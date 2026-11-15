"""Analysis behind the "Explore the world" page, for a cached case or a live window.

Input is a "cube": linear HH and HV power for up to six dates of one compatible
acquisition group on one grid, plus the chosen point. Everything else reuses the
existing code unchanged: src.polarization (valid mask, 3x3 linear-power filter,
dB, pair change), src.change_compass (region summary, raw and scene-relative
Compass readings), src.robustness (ring comparison, acquisition gaps) and the
evidence/review-note wording of the researcher workflow. No new science.

The "place" is a 500 m x 500 m square centred on the chosen point; the "scene" is
the whole window. Both are descriptive regions, not detections.
"""
from datetime import datetime
import json
from pathlib import Path

import numpy as np
from rasterio.crs import CRS
from rasterio.transform import Affine, rowcol
from rasterio.warp import transform as warp_transform

from src.change_compass import region_summary, compass_reading, MIN_PIXELS, DEFAULT_DEAD_ZONE_DB, label_text, reason_text
from src.i18n import t, num, integer
from src.polarization import prepare_polarizations, compare_polarizations
from src.robustness import ring_mask, ring_comparison, acquisition_gaps
from src.water_change import pixel_area_km2
from src.grid_validation import metric_grid, metric_ring
from src.workflow import CONSISTENT, CAUTION, NEUTRAL, UNKNOWN, PAIR, BASELINE, CONTEXT, status_text, scope_text

ROOT = Path(__file__).resolve().parents[1]
PLACE_SIZE_M = 500.0
MIN_RING_PIXELS = 20

# Preset places. Louisiana (and the guided example inside its window) has cached radar windows; Kerrville has
# cached catalog results only. Shipped demo places (data/demo_cache) are added by src.explore_panel.presets().
# The guided example's point is candidate 1's representative point (read from the saved investigation results).
GUIDED_EXAMPLE_PAIR = ('2026-07-03', '2026-07-15')   # saved candidate-1 seed interval (data/robustness_v2 summary)
PRESETS = (
    dict(key='louisiana_c1', lat=29.910969, lon=-90.264745, cached=True, case='louisiana', candidate=1,
         example_pair=GUIDED_EXAMPLE_PAIR, example_caption='ex.example_caption'),
    dict(key='louisiana', lat=29.913540, lon=-90.280409, cached=True, case='louisiana'),
    dict(key='kerrville', lat=30.0474, lon=-99.1403, cached=False),
)


def louisiana_cube(root=ROOT):
    """Cached six-date Louisiana HH/HV power windows (verified loaders), as an Explore cube."""
    import xarray as xr
    from src.polarization import load_polarization
    from shapely import wkt
    directory = Path(root) / 'data/polarization_analysis/six_date'
    data = load_polarization(directory)
    report = data['report']
    with xr.open_dataset(directory / 'hh_hv_cube.nc', engine='h5netcdf') as ds:
        hh = ds.HHHH_linear_power.values.astype(float); hv = ds.HVHV_linear_power.values.astype(float)
    if hh.shape[0] != len(report['observations']) or hh.shape[1:] != tuple(data['grid']['shape']):
        raise ValueError('Cached Louisiana cube does not match its report.')
    aoi = wkt.loads(json.loads((Path(root) / 'data/nisar_manifest.json').read_text())['aoi_wkt'])
    center = aoi.centroid
    inventory = Path(root) / 'data/pair_selection/nisar_inventory.json'
    catalog_dates = sorted({o['date'] for o in json.loads(inventory.read_text())}) if inventory.exists() else None
    return dict(source='cache', case='louisiana', lat=center.y, lon=center.x, window_km=None, catalog_dates=catalog_dates,
                dates=[o['date'] for o in report['observations']], times=[o['acquisition_utc'] for o in report['observations']],
                product_ids=[o['product_id'] for o in report['observations']], hh_power=hh, hv_power=hv,
                crs=str(data['grid']['crs']), transform=list(data['grid']['transform'])[:6], bytes_read_this_run=0)


def place_mask(shape, transform, crs, lat, lon, size_m=PLACE_SIZE_M):
    """Square of `size_m` centred on the point's pixel (clipped to the window). Returns (mask, inside)."""
    _, transform, shape = metric_grid(crs,transform,shape)
    if not np.isfinite([lat,lon,size_m]).all() or size_m <= 0:
        raise ValueError('Invalid point or physical neighborhood size.')
    (x,), (y,) = warp_transform('EPSG:4326', crs, [lon], [lat])
    row, col = rowcol(transform, x, y)
    if not (0 <= row < shape[0] and 0 <= col < shape[1]):
        raise ValueError('Selected coordinate is outside the loaded window; choose another coordinate.')
    # Physical pixel-centre distances, independently for rectangular x/y spacing.
    xc = transform.c + (np.arange(shape[1])+.5)*transform.a
    yc = transform.f + (np.arange(shape[0])+.5)*transform.e
    center_x, center_y = transform*(col+.5,row+.5)
    mask = (((yc-center_y >= -size_m/2) & (yc-center_y < size_m/2))[:,None] &
            ((xc-center_x >= -size_m/2) & (xc-center_x < size_m/2))[None,:])
    return mask, True


def analyze(cube, first=None, second=None, dead_zone_db=DEFAULT_DEAD_ZONE_DB, lang='en'):
    T = lambda key, **v: t(key, lang=lang, **v)
    n = lambda x, d=2, sign=False: num(x, d, sign, lang=lang)
    dates = list(cube['dates']); count = len(dates)
    if count < 2:
        raise ValueError(T('ex.err.two_dates'))
    first = 0 if first is None else first; second = count - 1 if second is None else second
    if not (0 <= first < second < count):
        raise ValueError(T('wf.err.pair'))
    data = prepare_polarizations(cube['hh_power'], cube['hv_power'])
    crs = CRS.from_user_input(cube['crs']); transform = Affine(*cube['transform'])
    cell = pixel_area_km2(crs, transform)
    metric_grid(crs,transform,data['HH'].shape[1:])
    common = data['common']
    place, inside = place_mask(common.shape, transform, crs, cube['lat'], cube['lon'])
    (point_x,), (point_y,) = warp_transform('EPSG:4326',crs,[cube['lon']],[cube['lat']])
    pr,pc = rowcol(transform,point_x,point_y)
    if not common[pr,pc]:
        raise ValueError(T('ex.err.point_nodata'))
    if int((common & place).sum()) < MIN_PIXELS:
        raise ValueError(T('ex.err.common',minimum=MIN_PIXELS))
    sample_x,sample_y=transform*(pc+.5,pr+.5)
    (sample_lon,),(sample_lat,)=warp_transform(crs,'EPSG:4326',[sample_x],[sample_y])
    # Preserve individual coverage separately; every primary comparison uses one footprint.
    native_valid = data['valid'].copy()
    data['valid'] = np.broadcast_to(common,data['valid'].shape).copy()
    pair = compare_polarizations(data, first, second)
    summary = region_summary(pair['HH_delta'], pair['HV_delta'], place & pair['valid'], cell, hv_db=np.where(common,data['HV'][[first, second]],np.nan))
    scene = (pair['statistics']['median_HH_delta_db'], pair['statistics']['median_HV_delta_db'])
    reading = compass_reading(summary, scene, dead_zone_db, MIN_PIXELS)
    ring = metric_ring(place, common, transform, crs)
    ring_row = None
    if int((ring & pair['valid']).sum()) >= MIN_RING_PIXELS and int((place & pair['valid']).sum()):
        ring_row = ring_comparison(data['HH'][[first, second]], data['HV'][[first, second]], place & pair['valid'],
                                   ring & pair['valid'], [dates[first], dates[second]])[0]
    series = []
    for i, d in enumerate(dates):
        v = common; pv = common & place; native = native_valid[i]
        series.append(dict(date=d, time=cube['times'][i], window_pixels=int(v.sum()), valid_pixels_this_date=int(native.sum()),
                           valid_area_this_date_km2=float(native.sum()*cell),
                           place_valid_pixels_this_date=int((native & place).sum()),
                           HH_per_date_coverage_median_db=float(np.median(data['HH'][i][native])) if native.any() else None,
                           HV_per_date_coverage_median_db=float(np.median(data['HV'][i][native])) if native.any() else None,
                           HH_window_median_db=float(np.median(data['HH'][i][v])) if v.any() else None,
                           HV_window_median_db=float(np.median(data['HV'][i][v])) if v.any() else None,
                           HH_place_median_db=float(np.median(data['HH'][i][pv])) if pv.any() else None,
                           HV_place_median_db=float(np.median(data['HV'][i][pv])) if pv.any() else None))
    gaps = [g for g in acquisition_gaps(dates)]
    loaded_gaps = [g for g in gaps if dates[first] <= g['start'] and g['end'] <= dates[second]]
    # A loaded gap is an acquisition gap only if the catalog has nothing in between; otherwise dates were not loaded.
    catalog = cube.get('catalog_dates')
    between = sorted({d for d in (catalog or []) if dates[first] < d < dates[second] and d not in dates})
    gap_status = 'none' if not loaded_gaps else 'unchecked' if catalog is None else 'not_loaded' if between else 'gap'
    pair_gaps = loaded_gaps if gap_status == 'gap' else []
    days = (datetime.fromisoformat(dates[second]) - datetime.fromisoformat(dates[first])).days
    tau = n(dead_zone_db).rstrip('0').rstrip(',.')

    evidence = []
    def add(ident, status, text, rule, scope=PAIR, topic=None):
        evidence.append(dict(id=ident, topic=topic or T(f'wf.topic.{ident}'), status=status, text=text, rule=rule, scope=scope))
    if reading['key'] == 'inconclusive':
        add('pattern', CAUTION, T('wf.ev.pattern_none', reason=reason_text(reading['raw'], lang)), T('wf.rule.pattern_none'))
    elif not reading['agree']:
        add('pattern', CAUTION, T('wf.ev.pattern_differ', raw=label_text(reading['raw']['key'], lang=lang),
                                  relative=label_text(reading['relative']['key'], lang=lang)), T('wf.rule.pattern'))
    else:
        add('pattern', CONSISTENT, T('wf.ev.pattern_agree', title=label_text(reading['key'], lang=lang)), T('wf.rule.pattern'))
    if ring_row is None:
        add('ring', UNKNOWN, T('ex.ev.ring_none'), T('wf.rule.ring', tau=tau))
    else:
        contrast = ring_row['candidate_minus_ring_dHH_db']
        add('ring', CONSISTENT if abs(contrast) >= dead_zone_db else CAUTION,
            T('wf.ev.ring', cand=n(ring_row['candidate_dHH_db'], 2, True), ring=n(ring_row['ring_dHH_db'], 2, True),
              diff=n(contrast, 2, True), diff_hv=n(ring_row['candidate_minus_ring_dHV_db'], 2, True)), T('wf.rule.ring', tau=tau))
    dark = summary.get('hv_dark_level', {})
    add('hv', CAUTION if dark.get('flag') else NEUTRAL,
        T('wf.ev.hv_dark' if dark.get('flag') else 'wf.ev.hv_neutral') + ' ' + T('wf.noise_floor_note'), T('wf.rule.hv'))
    if gap_status == 'gap':
        time_text = T('wf.ev.time_gap', days=days, gap=pair_gaps[0]['days'], start=pair_gaps[0]['start'], end=pair_gaps[0]['end'])
    elif gap_status == 'not_loaded':
        time_text = T('fl.time.unloaded', days=days, count=len(between), dates=', '.join(between))
    elif gap_status == 'unchecked':
        time_text = T('fl.time.unchecked', days=days)
    else:
        time_text = T('wf.ev.time', days=days) + (T('wf.ev.time_long') if days > 12 else '')
    add('time', CAUTION if loaded_gaps or days > 12 else CONSISTENT, time_text, T('wf.rule.time'))
    if summary.get('pixels', 0) < MIN_PIXELS:
        add('region_size', CAUTION, T('wf.ev.region_size', pixels=summary.get('pixels', 0), minimum=MIN_PIXELS), T('wf.rule.region_size'))
    if not inside:
        add('outside', CAUTION, T('ex.ev.outside'), T('ex.rule.outside'), topic=T('ex.topic.outside'))
    add('robustness', UNKNOWN, T('ex.ev.robustness'), T('ex.rule.robustness'), BASELINE, topic=T('ex.topic.robustness'))
    add('selection', NEUTRAL, T('ex.ev.selection'), T('ex.rule.selection'), CONTEXT, topic=T('ex.topic.selection'))
    from src.evidence_scope import scope_for, scope_text
    evidence_scope = scope_for(cube, (first, second))
    add('reference', UNKNOWN, scope_text(evidence_scope, lang), T('ex.rule.reference'), CONTEXT)

    questions = [T('wf.q.reference')]
    if not reading['agree']:
        questions.append(T('wf.q.scene'))
    if dark.get('flag'):
        questions.append(T('wf.q.hv'))
    if pair_gaps:
        questions.append(T('ex.q.gap', days=pair_gaps[0]['days']))
    elif gap_status == 'not_loaded':
        questions.append(T('fl.q.unloaded', dates=', '.join(between)))
    questions.append(T('ex.q.robustness'))
    questions.append(T('wf.q.alternatives'))
    order = ('pattern', 'ring', 'region_size', 'outside', 'hv', 'time')
    cautions = {e['id']: e for e in evidence if e['status'] == CAUTION}
    key_item = next((cautions[i] for i in order if i in cautions), next(e for e in evidence if e['id'] == 'reference'))
    return dict(cube=cube, lang=lang, dates=dates, first=first, second=second, interval_days=days, gaps=gaps, pair_gaps=pair_gaps,
                gap_status=gap_status, catalog_between=between, evidence_scope=evidence_scope,
                data=data, pair=pair, place=place, place_inside=inside, ring=ring_row, summary=summary, scene=scene,
                reading=reading, series=series, evidence=evidence, open_questions=questions, key_uncertainty=key_item,
                dead_zone_db=dead_zone_db, crs=crs, transform=transform, cell_km2=cell,
                common=common,common_pixels=int(common.sum()),common_area_km2=float(common.sum()*cell),
                sampled_row=int(pr),sampled_col=int(pc),sampled_lat=sample_lat,sampled_lon=sample_lon,
                place_common_pixels=int((common & place).sum()),place_common_area_km2=float((common & place).sum()*cell))


def observation(ctx):
    lang = ctx['lang']; s = ctx['summary']; d1, d2 = ctx['dates'][ctx['first']], ctx['dates'][ctx['second']]
    if s.get('pixels'):
        first = t('ex.obs.first', lang=lang, d1=d1, d2=d2, dhh=num(s['HH']['median'], 2, True, lang=lang),
                  dhv=num(s['HV']['median'], 2, True, lang=lang), pattern=label_text(ctx['reading']['key'], lang=lang))
    else:
        first = t('wf.obs.no_pixels', lang=lang, d1=d1, d2=d2)
    text = ctx['key_uncertainty']['text'].rstrip('.')
    return first + ' ' + t('wf.obs.second', lang=lang, text=text[0].lower() + text[1:] if lang == 'en' else text)


def review_note(ctx):
    """Markdown note built only from the context (no new claims), in the context's language."""
    lang = ctx['lang']; cube = ctx['cube']
    T = lambda key, **v: t(key, lang=lang, **v)
    n = lambda x, d=2, sign=False: num(x, d, sign, lang=lang)
    s = ctx['summary']; rd = ctx['reading']; d1, d2 = ctx['dates'][ctx['first']], ctx['dates'][ctx['second']]
    def table(scope):
        rows = [e for e in ctx['evidence'] if e['scope'] == scope]
        return ([T('wf.note.table_head'), '|---|---|---|---|'] +
                [f"| {e['topic']} | {status_text(e['status'], lang)} | {e['text']} | {e['rule']} |" for e in rows] + ['']) if rows else []
    source = T('ex.note.source_cache') if cube['source'] == 'cache' else T('ex.note.source_live', bytes=integer(cube.get('bytes_read_this_run', 0), lang))
    from src.evidence_scope import scope_text as evidence_text
    lines = [T('ex.note.title', lat=f"{cube['lat']:.5f}", lon=f"{cube['lon']:.5f}"), '', T('wf.note.disclaimer'), '',
             evidence_text(ctx['evidence_scope'], lang), '',
             T('wf.note.observation'), '', observation(ctx), '',
             T('ex.note.place'), '', T('ex.common',pixels=integer(ctx['common_pixels'],lang=lang),area=n(ctx['common_area_km2'],4)), '',
             T('ex.note.point', lat=f"{cube['lat']:.6f}", lon=f"{cube['lon']:.6f}"),
             T('ex.sampled',lat=f"{ctx['sampled_lat']:.6f}",lon=f"{ctx['sampled_lon']:.6f}",row=ctx['sampled_row'],col=ctx['sampled_col']),
             T('ex.note.window', window=(n(cube['window_km'], 1) + ' km') if cube.get('window_km') else T('ex.note.cached_aoi'),
               size=int(PLACE_SIZE_M)),
             T('ex.note.grid', crs=str(ctx['crs']), pixel=n(abs(ctx['transform'].a), 0)), f'- {source}', '',
             T('wf.note.dates'), '',
             T('wf.note.pair', d1=d1, d2=d2, days=ctx['interval_days']) +
             (T('wf.note.spans_gap', days=ctx['pair_gaps'][0]['days']) if ctx['pair_gaps'] else ''),
             T('wf.note.products')] + [f'  - `{p}`' for p in cube['product_ids']] + ['',
             f"## {scope_text(PAIR, lang)}", '', T('wf.note.qv_head'), '|---|---:|', T('wf.note.valid_pixels', pixels=s.get('pixels', 0))]
    if s.get('pixels'):
        lines += [T('wf.note.median_dhh', v=n(s['HH']['median'], 2, True)), T('wf.note.median_dhv', v=n(s['HV']['median'], 2, True)),
                  T('wf.note.iqr_dhh', lo=n(s['HH']['p25'], 2, True), hi=n(s['HH']['p75'], 2, True)),
                  T('wf.note.iqr_dhv', lo=n(s['HV']['p25'], 2, True), hi=n(s['HV']['p75'], 2, True))]
    lines += [T('wf.note.scene', hh=n(ctx['scene'][0], 2, True), hv=n(ctx['scene'][1], 2, True))]
    if ctx['ring']:
        lines += [T('wf.note.ring', hh=n(ctx['ring']['ring_dHH_db'], 2, True), hv=n(ctx['ring']['ring_dHV_db'], 2, True)),
                  T('wf.note.ring_diff', hh=n(ctx['ring']['candidate_minus_ring_dHH_db'], 2, True), hv=n(ctx['ring']['candidate_minus_ring_dHV_db'], 2, True))]
    lines += ['', T('wf.note.pattern_head'), '',
              T('wf.note.raw', title=label_text(rd['raw']['key'], lang=lang), reason=reason_text(rd['raw'], lang)),
              T('wf.note.relative', title=label_text(rd['relative']['key'], lang=lang), reason=reason_text(rd['relative'], lang)),
              T('wf.note.result', title=label_text(rd['key'], lang=lang), tau=n(ctx['dead_zone_db']).rstrip('0').rstrip(',.')), '',
              T('wf.note.alternatives')] + [f'- {t(k, lang=lang)}' for k in rd['alternative_keys']] + ['']
    lines += table(PAIR)
    lines += [f"## {T('ex.note.not_computed')}", ''] + table(BASELINE)
    lines += [f"## {scope_text(CONTEXT, lang)}", ''] + table(CONTEXT)
    lines += [T('ex.note.series_head'), '', T('ex.note.series_cols'), '|---|---:|---:|---:|---:|']
    for r in ctx['series']:
        lines.append(f"| {r['date']} | {n(r['HH_place_median_db'])} | {n(r['HV_place_median_db'])} | "
                     f"{n(r['HH_window_median_db'])} | {n(r['HV_window_median_db'])} |")
    lines += ['', T('wf.note.questions'), ''] + [f'{i}. {q}' for i, q in enumerate(ctx['open_questions'], 1)] + ['',
              T('ex.note.method'), '']
    return '\n'.join(lines)
