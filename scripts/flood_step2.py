"""Flood validation Step 2, one stage at a time (protocol: docs/FLOOD_VALIDATION_PROTOCOL.md, freeze 181782456a).

  --stage a   Thailand 004 D calibration (09-06 -> 09-30); writes data/flood_validation/calibration.json (+ .sha256)
  --stage b   test: Thailand 011 A (09-06 -> 09-30). PRIMARY = untuned default HH -16 dB, |dHH| >= 3 dB, new open
              water vs DSWx-S1 (protocol Deviation 3); SECONDARY = frozen calibrated thresholds; HLS = sensitivity.
  --stage c   test: Gandak primary 026 A (09-19 -> 10-01), S1 only (no usable HLS); bootstrap CIs (Deviation 4)
  --stage d   negative control, Thailand both tracks: co-registration check of 09-18 first, then before-before vs before-during
  (later stages are added one at a time, each after the previous report)

NISAR windows are read with the existing live engine and byte-range reader (src.live_engine.run_live); the token comes
from the existing helper and is never printed or stored. Outputs only under data/flood_validation/step2<stage>/.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import numpy as np
from shapely.geometry import shape

from src import flood_validation as fv
from src.flood_classes import masks, OPEN, NOT_WATER, PARTIAL
from src.live_engine import search_catalog, group_products, run_live

FV = ROOT / 'data/flood_validation'
REF = FV / 'reference'
UTC = '%Y%m%dT%H%M%SZ'


def aoi(name):
    return shape(json.loads((FV / f'aoi/{name}.geojson').read_text())['features'][0]['geometry'])


def scan_row(site, product, acquired):
    scan = json.loads((REF / 'scan.json').read_text())
    return next(s for s in scan['scenes'] if (s['site'], s['product'], s['acquired_utc']) == (site, product, acquired))


def reference(site, product, acquired, grid):
    row = scan_row(site, product, acquired)
    codes = np.load(REF / row['file'])['wtr']
    aligned = fv.align_reference(codes, row['transform'], row['crs'], grid['shape'], grid['transform'], grid['crs'])
    return dict(codes=aligned, product=product, acquired=acquired, sensor=row['sensor'], granule=row['granule'],
                time=datetime.strptime(acquired, UTC).replace(tzinfo=timezone.utc))


def nisar(site, track, frame, direction, dates, token):
    region = aoi(site); c = region.centroid
    products, _ = search_catalog(c.y, c.x, datetime(2026, 9, 1).date(), datetime(2026, 10, 15).date())
    group = next(g for g in group_products(products) if (g['key']['track'], g['key']['frame'], g['key']['direction'],
                 g['key']['bandwidth'], g['key']['polarization']) == (track, frame, direction, '4005', 'DHDH'))
    chosen = [p for p in group['products'] if p['date'] in dates]
    if [p['date'] for p in chosen] != list(dates):
        raise SystemExit(f'NISAR dates not found: {dates}')
    started = time.monotonic()
    cube = run_live(chosen, c.y, c.x, 10.0, token, polygon=region)
    cube['read_seconds'] = round(time.monotonic() - started, 1)
    return cube


def hours(a, b):
    return round((a - b).total_seconds() / 3600, 1)


def figure(path, prep, before, after, refs, agreements, title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    v = prep['valid']
    for ax, arr, name, cmap, lim in ((axes[0, 0], prep['HH'][before], 'HH before (dB)', 'gray', (-25, 0)),
                                     (axes[0, 1], prep['HH'][after], 'HH during (dB)', 'gray', (-25, 0)),
                                     (axes[0, 2], prep['HH'][after] - prep['HH'][before], 'ΔHH (dB)', 'RdBu_r', (-8, 8)),
                                     (axes[0, 3], prep['HV'][after] - prep['HV'][before], 'ΔHV (dB)', 'RdBu_r', (-8, 8))):
        im = ax.imshow(np.where(v, arr, np.nan), cmap=cmap, vmin=lim[0], vmax=lim[1]); ax.set_title(name, fontsize=9)
        fig.colorbar(im, ax=ax, shrink=.7)
    role_cmap = ListedColormap(['#ffffff', '#1f5fbf', '#7fb3e6', '#bbbbbb'])
    for ax, (label, r) in zip(axes[1, :2], refs):
        m = masks(r['codes'], r['product'])
        roles = np.full(r['codes'].shape, 3); roles[m[NOT_WATER]] = 0; roles[m[OPEN]] = 1; roles[m[PARTIAL]] = 2
        ax.imshow(roles, cmap=role_cmap, vmin=0, vmax=3, interpolation='nearest')
        ax.set_title(f'{label}: white not water, blue open, light partial/inundated, grey invalid', fontsize=7)
    agree_cmap = ListedColormap(['#bbbbbb', '#1f5fbf', '#e0732c', '#8e44ad', '#ffffff'])
    for ax, (label, a) in zip(axes[1, 2:], agreements):
        ax.imshow(a, cmap=agree_cmap, vmin=0, vmax=4, interpolation='nearest')
        ax.set_title(f'{label}\nblue TP, orange FP, purple FN, white TN, grey invalid', fontsize=7)
    for ax in axes.flat:
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle(title, fontsize=10); fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def evaluate(prep, before, after, nisar_times, refs_presence, ref_new, thresholds, scope):
    """Metric rows for presence (during date) and new water, per variant and threshold set."""
    rows = []
    for set_name, (t_hh, t_hv) in thresholds.items():
        for variant in ('HH', 'HV', 'HH+HV'):
            if (variant != 'HH' and t_hv is None) or (variant != 'HV' and t_hh is None):
                rows.append(dict(scope=scope, threshold_set=set_name, variant=variant, outcome='all',
                                 note='not applicable (no frozen default for this channel)'))
                continue
            pred = fv.nisar_presence(prep, after, variant, t_hh, t_hv)
            for label, r in refs_presence:
                pos, neg, _ = fv.reference_presence(r['codes'], r['product'])
                rows.append(dict(scope=scope, threshold_set=set_name, variant=variant, outcome='open water presence (during)',
                                 reference=label, offset_hours=hours(r['time'], nisar_times[after]),
                                 t_HH=t_hh, t_HV=t_hv, **fv.confusion(pred, pos, neg, prep['valid'])))
            new = fv.nisar_new_water(prep, before, after, variant, t_hh, t_hv)
            if ref_new:
                label, pre, dur = ref_new
                pos, neg = fv.reference_new_water(pre['codes'], dur['codes'], dur['product'])
                rows.append(dict(scope=scope, threshold_set=set_name, variant=variant, outcome='new open water (during minus pre)',
                                 reference=label, offset_hours=f"pre {hours(pre['time'], nisar_times[before])}, "
                                 f"during {hours(dur['time'], nisar_times[after])}", t_HH=t_hh, t_HV=t_hv, min_change_db=fv.MIN_CHANGE,
                                 **fv.confusion(new, pos, neg, prep['valid'])))
    return rows


def write_outputs(out, report, rows):
    out.mkdir(parents=True, exist_ok=True)
    (out / 'metrics.json').write_text(json.dumps(dict(report, rows=rows), indent=1, default=str) + '\n')
    keys = ['scope', 'threshold_set', 'variant', 'outcome', 'reference', 'offset_hours', 't_HH', 't_HV', 'TP', 'FP', 'FN', 'TN',
            'invalid', 'precision', 'recall', 'F1', 'IoU', 'reference_positive_share', 'note']
    with (out / 'metrics.csv').open('w', newline='') as handle:
        w = csv.DictWriter(handle, keys, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    files = sorted(p for p in out.iterdir() if p.is_file() and p.name != 'sidecar.json')
    (out / 'sidecar.json').write_text(json.dumps(dict(
        outputs_sha256={p.name: fv.sha256(p) for p in files}, protocol_freeze_commit='181782456a49aa252885861754a67934c3431007',
        code_sha256={p: fv.sha256(ROOT / p) for p in ('scripts/flood_step2.py', 'src/flood_validation.py', 'src/flood_classes.py')}),
        indent=2) + '\n')


def stage_a(token):
    site = 'thailand_prachinburi'; out = FV / 'step2a'
    if (out / 'metrics.json').exists() or fv.CALIBRATION.exists():
        print('Stage a outputs exist; left unchanged.'); return 0
    cube = nisar(site, '004', '081', 'D', ('2026-09-06', '2026-09-30'), token)
    prep = fv.preprocess(cube)
    grid = dict(shape=prep['valid'].shape, transform=cube['transform'], crs=cube['crs'])
    times = [datetime.fromisoformat(t) for t in cube['times']]
    s1_pre = reference(site, 'S1', '20260908T230013Z', grid)
    s1_dur = reference(site, 'S1', '20261001T230839Z', grid)
    hls_dur = reference(site, 'HLS', '20261002T033141Z', grid)
    # calibration (protocol section 4): against HLS 10-02 (HLS first if usable); S1-optimal values reported, not used
    pos, neg, _ = fv.reference_presence(hls_dur['codes'], 'HLS')
    t_hh, table_hh = fv.calibrate(prep['HH'][1], pos, neg, prep['valid'])
    t_hv, table_hv = fv.calibrate(prep['HV'][1], pos, neg, prep['valid'])
    spos, sneg, _ = fv.reference_presence(s1_dur['codes'], 'S1')
    s_hh, _ = fv.calibrate(prep['HH'][1], spos, sneg, prep['valid'])
    s_hv, _ = fv.calibrate(prep['HV'][1], spos, sneg, prep['valid'])
    calibration = dict(created_utc=datetime.now(timezone.utc).isoformat(), protocol_freeze_commit='181782456a49aa252885861754a67934c3431007',
                       scene='Thailand NISAR 004 D 081, during 2026-09-30', reference=hls_dur['granule'],
                       reference_offset_hours=hours(hls_dur['time'], times[1]), grid_db=[float(fv.GRID[0]), float(fv.GRID[-1]), 0.5],
                       rule='max F1 open-water presence; ties: closest to -16 dB, then higher', frozen=dict(HH=t_hh, HV=t_hv),
                       min_change_db=fv.MIN_CHANGE, reported_not_used=dict(S1_optimal_HH=s_hh, S1_optimal_HV=s_hv,
                       S1_reference=s1_dur['granule']), f1_curve=dict(HH=[(r['threshold'], r['F1']) for r in table_hh],
                       HV=[(r['threshold'], r['F1']) for r in table_hv]))
    FV.mkdir(exist_ok=True)
    fv.CALIBRATION.write_text(json.dumps(calibration, indent=1) + '\n')
    fv.CALIBRATION.with_suffix('.sha256').write_text(f'{fv.sha256(fv.CALIBRATION)}  calibration.json\n')
    thresholds = {'frozen default (-16 dB HH, untuned)': (fv.DEFAULT_HH, None), 'calibrated (in-sample)': (t_hh, t_hv)}
    rows = evaluate(prep, 0, 1, times, [('S1 primary', s1_dur), ('HLS sensitivity', hls_dur)], ('S1 primary', s1_pre, s1_dur),
                    thresholds, 'calibration scene (in-sample)')
    m_pre, m_dur = masks(s1_pre['codes'], 'S1'), masks(s1_dur['codes'], 'S1')
    cats = {'S1 new open water': m_pre[NOT_WATER] & m_dur[OPEN], 'S1 persistent open water': m_pre[OPEN] & m_dur[OPEN],
            'S1 persistent not water': m_pre[NOT_WATER] & m_dur[NOT_WATER],
            'S1 new inundated vegetation': m_pre[NOT_WATER] & m_dur[PARTIAL],
            'HLS open water (during)': masks(hls_dur['codes'], 'HLS')[OPEN],
            'HLS partial surface water (during)': masks(hls_dur['codes'], 'HLS')[PARTIAL]}
    dirs = fv.directions(prep, 0, 1, cats)
    # exploratory, separately labelled: HH increase >= 3 dB with HV not decreasing vs S1 new inundated vegetation
    dhh = prep['HH'][1] - prep['HH'][0]; dhv = prep['HV'][1] - prep['HV'][0]
    explore = fv.confusion((dhh >= 3) & (dhv >= 0), m_pre[NOT_WATER] & m_dur[PARTIAL], m_pre[NOT_WATER] & m_dur[NOT_WATER], prep['valid'])
    secondary = {}
    for label, r in (('S1 inundated vegetation (during)', s1_dur), ('HLS partial surface water (during)', hls_dur)):
        part = masks(r['codes'], r['product'])[PARTIAL] & prep['valid']
        secondary[label] = dict(pixels=int(part.sum()), **{f'share classified water, {k}': float(fv.nisar_presence(prep, 1, v, *thr)[part].mean())
                                if part.any() and thr[0] is not None and (v == 'HH' or thr[1] is not None) else None
                                for k, (v, thr) in {'HH default': ('HH', (fv.DEFAULT_HH, None)), 'HH calibrated': ('HH', (t_hh, t_hv)),
                                                    'HV calibrated': ('HV', (t_hh, t_hv)), 'HH+HV calibrated': ('HH+HV', (t_hh, t_hv))}.items()})
    pos_s, neg_s, _ = fv.reference_presence(s1_dur['codes'], 'S1')
    pos_n, neg_n = fv.reference_new_water(s1_pre['codes'], s1_dur['codes'], 'S1')
    out.mkdir(parents=True, exist_ok=True)
    figure(out / 'maps.png', prep, 0, 1,
           [('S1 10-01 (primary)', s1_dur), ('HLS 10-02 L9 (sensitivity)', hls_dur)],
           [('Presence, calibrated HH vs S1', fv.agreement_map(fv.nisar_presence(prep, 1, 'HH', t_hh, t_hv), pos_s, neg_s, prep['valid'])),
            ('New water, calibrated HH vs S1', fv.agreement_map(fv.nisar_new_water(prep, 0, 1, 'HH', t_hh, t_hv), pos_n, neg_n, prep['valid']))],
           'Thailand 004 D, 2026-09-06 → 09-30 (calibration scene, in-sample). Agreement with independent water products, not accuracy.')
    report = dict(stage='a', created_utc=datetime.now(timezone.utc).isoformat(), nisar=dict(product_ids=cube['product_ids'],
                  times=cube['times'], bytes_read=cube['bytes_read_this_run'], read_seconds=cube['read_seconds'],
                  grid_shape=list(prep['valid'].shape), transform=cube['transform'], crs=cube['crs'],
                  valid_fraction=float(prep['valid'].mean())), calibration=dict(HH=t_hh, HV=t_hv, S1_optimal_HH=s_hh, S1_optimal_HV=s_hv),
                  references=dict(S1_pre=s1_pre['granule'], S1_during=s1_dur['granule'], HLS_during=hls_dur['granule']),
                  directions=dirs, exploratory_vegetated_flooding=dict(rule='dHH >= 3 dB and dHV >= 0 vs S1 new inundated vegetation (class 3)',
                  label='EXPLORATORY, not a validation result', **explore), secondary_partial=secondary)
    write_outputs(out, report, rows)
    return 0


def test_stage(stage, site, track, frame, direction, dates, s1_pre_id, s1_dur_id, hls_dur_id, token, title):
    """Test stages (b-e): primary untuned default first, frozen calibrated thresholds second; nothing is tuned here."""
    out = FV / f'step2{stage}'
    if (out / 'metrics.json').exists():
        print(f'Stage {stage} outputs exist; left unchanged.'); return 0
    t_hh_cal, t_hv_cal = fv.frozen_thresholds()                     # refuses if calibration.json changed
    primary = dict(fv.PRIMARY_CONFIG)
    cube = nisar(site, track, frame, direction, dates, token)
    prep = fv.preprocess(cube)
    grid = dict(shape=prep['valid'].shape, transform=cube['transform'], crs=cube['crs'])
    times = [datetime.fromisoformat(t) for t in cube['times']]
    s1_pre = reference(site, 'S1', s1_pre_id, grid); s1_dur = reference(site, 'S1', s1_dur_id, grid)
    hls_dur = reference(site, 'HLS', hls_dur_id, grid) if hls_dur_id else None
    presence_refs = [('S1 primary', s1_dur)] + ([('HLS sensitivity', hls_dur)] if hls_dur else [])
    thresholds = {'PRIMARY: untuned default (HH -16 dB, |dHH| >= 3 dB)': (primary['t_HH'], None),
                  'SECONDARY: frozen calibrated (HH -10.0, HV -15.5)': (t_hh_cal, t_hv_cal)}
    rows = evaluate(prep, 0, 1, times, presence_refs, ('S1 primary', s1_pre, s1_dur), thresholds, f'test scene ({title})')
    block = int(fv.BOOT_BLOCK_M / abs(cube['transform'][0]))          # Deviation 4: CIs for PRIMARY rows
    for r in rows:
        if r['threshold_set'].startswith('PRIMARY') and r['variant'] == 'HH' and 'TP' in r:
            if r['outcome'].startswith('new'):
                pred = fv.nisar_new_water(prep, 0, 1, 'HH', primary['t_HH'], None)
                pos, neg = fv.reference_new_water(s1_pre['codes'], s1_dur['codes'], 'S1')
            else:
                pred = fv.nisar_presence(prep, 1, 'HH', primary['t_HH'], None)
                ref = s1_dur if r['reference'].startswith('S1') else hls_dur
                pos, neg, _ = fv.reference_presence(ref['codes'], ref['product'])
            r['ci95'] = fv.block_bootstrap(pred, pos, neg, prep['valid'], block)
    for r in rows:
        if r['threshold_set'].startswith('SECONDARY') and r['variant'] != 'HH':
            r['note'] = (r.get('note', '') + ' secondary/exploratory (no untuned default for this variant)').strip()
    m_pre, m_dur = masks(s1_pre['codes'], 'S1'), masks(s1_dur['codes'], 'S1')
    cats = {'S1 new open water': m_pre[NOT_WATER] & m_dur[OPEN], 'S1 persistent open water': m_pre[OPEN] & m_dur[OPEN],
            'S1 persistent not water': m_pre[NOT_WATER] & m_dur[NOT_WATER],
            'S1 new inundated vegetation': m_pre[NOT_WATER] & m_dur[PARTIAL]}
    if hls_dur:
        hm = masks(hls_dur['codes'], 'HLS')
        cats.update({'HLS open water (during)': hm[OPEN], 'HLS partial surface water (during)': hm[PARTIAL]})
    dirs = fv.directions(prep, 0, 1, cats)
    dhh = prep['HH'][1] - prep['HH'][0]; dhv = prep['HV'][1] - prep['HV'][0]
    explore = fv.confusion((dhh >= 3) & (dhv >= 0), m_pre[NOT_WATER] & m_dur[PARTIAL], m_pre[NOT_WATER] & m_dur[NOT_WATER], prep['valid'])
    pos_s, neg_s, _ = fv.reference_presence(s1_dur['codes'], 'S1')
    pos_n, neg_n = fv.reference_new_water(s1_pre['codes'], s1_dur['codes'], 'S1')
    out.mkdir(parents=True, exist_ok=True)
    figure(out / 'maps.png', prep, 0, 1, [(f"S1 {s1_dur_id[:8]} (primary)", s1_dur)] +
           ([(f"HLS {hls_dur_id[:8]} (sensitivity)", hls_dur)] if hls_dur else [(f"S1 {s1_pre_id[:8]} (pre)", s1_pre)]),
           [('New water, PRIMARY default HH vs S1', fv.agreement_map(fv.nisar_new_water(prep, 0, 1, 'HH', primary['t_HH'], None), pos_n, neg_n, prep['valid'])),
            ('Presence, PRIMARY default HH vs S1', fv.agreement_map(fv.nisar_presence(prep, 1, 'HH', primary['t_HH'], None), pos_s, neg_s, prep['valid']))],
           f'{title}. Agreement with independent water products, not accuracy.')
    report = dict(stage=stage, created_utc=datetime.now(timezone.utc).isoformat(), primary_config=primary,
                  secondary_thresholds=dict(HH=t_hh_cal, HV=t_hv_cal), nisar=dict(product_ids=cube['product_ids'], times=cube['times'],
                  bytes_read=cube['bytes_read_this_run'], read_seconds=cube['read_seconds'], grid_shape=list(prep['valid'].shape),
                  transform=cube['transform'], crs=cube['crs'], valid_fraction=float(prep['valid'].mean())),
                  references=dict(S1_pre=s1_pre['granule'], S1_during=s1_dur['granule'], HLS_during=hls_dur['granule'] if hls_dur else None),
                  directions=dirs, exploratory_vegetated_flooding=dict(rule='dHH >= 3 dB and dHV >= 0 vs S1 new inundated vegetation',
                  label='EXPLORATORY; failed in the calibration scene (F1 0.02); not a claim', **explore))
    write_outputs(out, report, rows)
    return 0


def stage_b(token):
    return test_stage('b', 'thailand_prachinburi', '011', '009', 'A', ('2026-09-06', '2026-09-30'),
                      '20260908T230013Z', '20261001T230839Z', '20261002T033141Z', token, 'Thailand 011 A, 2026-09-06 -> 09-30 (test)')


def stage_c(token):
    return test_stage('c', 'gandak_eo_image', '026', '015', 'A', ('2026-09-19', '2026-10-01'),
                      '20260917T001912Z', '20260929T001912Z', None, token, 'Gandak primary 026 A, 2026-09-19 -> 10-01 (test, S1 only)')


def stage_d(token):
    """Negative control (protocol sections 1, 5.1, 6.4): co-registration check of 09-18 (forecast orbit) first; if it passes,
    PRIMARY new water for before-before (09-06 -> 09-18) vs before-during (09-06 -> 09-30), and against S1 09-08 -> 09-19."""
    site = 'thailand_prachinburi'; out = FV / 'step2d'
    if (out / 'metrics.json').exists():
        print('Stage d outputs exist; left unchanged.'); return 0
    primary = dict(fv.PRIMARY_CONFIG); results = {}; rows = []
    for track, frame, d in (('004', '081', 'D'), ('011', '009', 'A')):
        cube = nisar(site, track, frame, d, ('2026-09-06', '2026-09-18', '2026-09-30'), token)
        prep = fv.preprocess(cube)
        times = [datetime.fromisoformat(t) for t in cube['times']]
        grid = dict(shape=prep['valid'].shape, transform=cube['transform'], crs=cube['crs'])
        co18 = fv.coregistration_offset(prep['HH'][0], prep['HH'][1], prep['valid'])
        co30 = fv.coregistration_offset(prep['HH'][0], prep['HH'][2], prep['valid'])
        passed = co18['magnitude'] <= 1.0
        res = dict(product_ids=cube['product_ids'], bytes_read=cube['bytes_read_this_run'], read_seconds=cube['read_seconds'],
                   coregistration=dict(offset_09_18_px=co18, offset_09_30_px=co30, rule='pass if |offset(09-06, 09-18)| <= 1 px',
                                       passed=passed))
        if passed:
            new18 = fv.nisar_new_water(prep, 0, 1, 'HH', primary['t_HH'], None)
            new30 = fv.nisar_new_water(prep, 0, 2, 'HH', primary['t_HH'], None)
            v = prep['valid']; px_km2 = abs(cube['transform'][0] * cube['transform'][4]) / 1e6
            res['tier_A'] = dict(new_water_share_before_before=float(new18[v].mean()), new_water_share_before_during=float(new30[v].mean()),
                                 new_water_km2_before_before=float(new18.sum() * px_km2), new_water_km2_before_during=float(new30.sum() * px_km2))
            s1_pre = reference(site, 'S1', '20260908T230013Z', grid); s1_nc = reference(site, 'S1', '20260919T230839Z', grid)
            pos, neg = fv.reference_new_water(s1_pre['codes'], s1_nc['codes'], 'S1')
            m = fv.confusion(new18, pos, neg, v)
            m['ci95'] = fv.block_bootstrap(new18, pos, neg, v, int(fv.BOOT_BLOCK_M / abs(cube['transform'][0])))
            m['false_new_water_km2'] = m['FP'] * px_km2
            rows.append(dict(scope=f'negative control {track} {d}', threshold_set='PRIMARY: untuned default (HH -16 dB, |dHH| >= 3 dB)',
                             variant='HH', outcome='new open water, before-before (09-06 -> 09-18)', reference='S1 09-08 -> 09-19',
                             offset_hours=f"pre {hours(s1_pre['time'], times[0])}, second {hours(s1_nc['time'], times[1])}", t_HH=primary['t_HH'], **m))
            res['tier_B'] = dict(reference_new_water_share=m['reference_positive_share'], **{k: m[k] for k in ('TP', 'FP', 'FN', 'TN', 'precision', 'recall', 'F1', 'IoU', 'false_new_water_km2')})
            res['directions_before_before'] = fv.directions(prep, 0, 1, {'all valid': v, 'NISAR new water (before-before)': new18})
        results[f'{track} {d}'] = res
    report = dict(stage='d', created_utc=datetime.now(timezone.utc).isoformat(), primary_config=primary, tracks=results,
                  note='09-18 products use a forecast orbit (filename accuracy field F).')
    write_outputs(out, report, rows)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', required=True, choices=['a', 'b', 'c', 'd'])
    args = parser.parse_args(argv)
    from scripts.check_earthdata_access import available_token
    token = available_token()
    if not token:
        print('No Earthdata token available through the existing helper.'); return 2
    try:
        return {'a': stage_a, 'b': stage_b, 'c': stage_c, 'd': stage_d}[args.stage](token)
    finally:
        del token


if __name__ == '__main__':
    raise SystemExit(main())
