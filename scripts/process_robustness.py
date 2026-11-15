"""Robustness checks for the five Louisiana investigation candidates (version 2).

Offline: reads only cached real data (six-date HH/HV polarization outputs and
the saved investigation regions). Writes ONLY to data/robustness_v2/. The
version-1 folder data/robustness/ is kept unchanged for the record; its
leave-one-date-out column counted a same-direction notable change in ANY
remaining interval. Version 2 checks only the (possibly merged) interval that
contains the original seed event. Exits unchanged if results exist (use
--overwrite to regenerate this script's own folder).
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import numpy as np
import rasterio
import xarray as xr

from src.polarization import load_polarization
from src.water_change import mask_aware_mean, power_to_db
from src.investigation import DEFAULTS
from src.robustness import (acquisition_gaps, iou, indices_mask, screen, match_candidate, leave_one_date_out,
                            ring_mask, ring_comparison, notable_on_footprint, RING_INNER_PX, RING_OUTER_PX)

OUT = ROOT / 'data/robustness_v2'
VERSION = 2
FILTERS = (1, 3, 5)
FLOORS = (2.5, 3.0, 3.5)
PERCENTILES = (85.0, 90.0, 95.0)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(path, rows):
    with open(path, 'w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def markdown_report(report):
    """Human-readable summary built only from the results dictionary."""
    lines = ['# Robustness checks (version 2) for the five Louisiana investigation candidates', '',
             'Offline, from cached real NISAR GCOV data (six dates, HH and HV). Script: `scripts/process_robustness.py`. '
             'Screening and ranking reuse `src/investigation.py` unchanged. **Robustness is not validation**: the same '
             'observations select and test the candidates.', '',
             '**What changed from version 1 (`data/robustness/`, kept unchanged):** the leave-one-date-out check now looks only '
             'at the interval that contains the original seed event (merged across the removed date when needed). Version 1 '
             'counted a same-direction notable change in any remaining interval.', '']
    for g in report['acquisition_gaps']:
        lines.append(f"Acquisition gap: {g['start']} → {g['end']} is {g['days']} days ({g['missing_acquisitions']} acquisition missing).")
    lines += ['', '| Candidate | Seed change | (a) top 5 in variants | (b) same seed in variants | Date removals: seed event still notable | not notable | not testable | Candidate − ring ΔHH at seed (dB) |',
              '|---|---|---:|---:|---:|---|---|---:|']
    for s in report['summary']:
        ring = s['ring_seed_interval']
        lines.append(f"| {s['candidate']} | {s['seed']} | {s['variants_in_top5']}/{s['settings_variants']} | "
                     f"{s['variants_same_seed']}/{s['settings_variants']} | {s['lodo_removals_still_notable']}/{s['lodo_removals']} | "
                     f"{', '.join(s['lodo_dates_not_notable']) or '–'} | {', '.join(s['lodo_dates_not_testable']) or '–'} | "
                     f"{ring['candidate_minus_ring_dHH_db']:+.2f} |")
    lines += ['', '## Leave one date out: interval that carries the seed event', '',
              '| Candidate | Removed date | Seed-event interval | Days | Median ΔHH (dB) | Status | Other same-direction notable intervals (not counted) |',
              '|---|---|---|---:|---:|---|---|']
    for c, rows in report['leave_one_date_out'].items():
        for r in rows:
            delta = f"{r['seed_event_delta_db']:+.2f}" if r['seed_event_delta_db'] is not None else '–'
            lines.append(f"| {c} | {r['removed_date']} | {r['seed_event_interval'] or '–'} | {r['seed_event_interval_days'] or '–'} | "
                         f"{delta} | {r['seed_event_status']} | {', '.join(r['other_same_direction_notable_intervals']) or '–'} |")
    lines += ['', '## Method', ''] + [f"- **{k}**: {v}" for k, v in report['method'].items() if isinstance(v, str)]
    lines += ['', '## Limitations', ''] + [f'- {x}' for x in report['limitations']]
    lines += ['', 'Files: `results.json`, `settings_sensitivity.csv`, `leave_one_date_out.csv`, `ring_comparison.csv`, '
              '`sidecar.json` (SHA-256 of sources and outputs).', '']
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--overwrite', action='store_true', help='Rewrite data/robustness_v2 only.')
    args = parser.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'results.json').exists() and not args.overwrite:
        print('data/robustness_v2 results already exist; left unchanged (use --overwrite).'); return 0
    start = time.monotonic()
    data = load_polarization(ROOT / 'data/polarization_analysis/six_date')  # existing verified loader
    common = data['common']; grid = data['grid']; shape = common.shape
    dates = [o['date'] for o in data['report']['observations']]
    report_inv = json.loads((ROOT / 'data/investigation_engine/results.json').read_text())
    with rasterio.open(ROOT / 'data/investigation_engine/region_labels.tif') as src:
        labels = src.read(1)
        if src.transform != grid['transform'] or src.crs != grid['crs']:
            raise ValueError('Investigation labels are not on the polarization grid.')
    candidates = []
    for region in report_inv['regions']:
        footprint = labels == region['id']
        if int(footprint.sum()) != region['pixels']:
            raise ValueError('Saved region pixels differ from the label raster.')
        candidates.append((region, footprint))
    all_candidates = np.isin(labels, [r['id'] for r, _ in candidates])

    with xr.open_dataset(ROOT / 'data/polarization_analysis/six_date/hh_hv_cube.nc', engine='h5netcdf') as ds:
        raw_hh = ds.HHHH_linear_power.values.astype(float); raw_hv = ds.HVHV_linear_power.values.astype(float)

    # (1) Settings sensitivity: rerun the unchanged screening/ranking for 27 variants.
    settings_rows = []
    default_check = None
    for size in FILTERS:
        hh = np.stack([power_to_db(mask_aware_mean(p, common, size)) for p in raw_hh])
        hv = np.stack([power_to_db(mask_aware_mean(p, common, size)) for p in raw_hv])
        for floor in FLOORS:
            for pct in PERCENTILES:
                proposals, scene, eligible, selected = screen(hh, hv, common, floor, pct, DEFAULTS['minimum_pixels'])
                if (size, floor, pct) == (3, 3.0, 90.0):
                    default_check = [max(iou(fp, indices_mask(p['indices'], shape)) for p in selected) if selected else 0.0
                                     for _, fp in candidates]
                for region, fp in candidates:
                    (any_iou, any_p), (sel_iou, sel_rank, sel_p) = match_candidate(fp, proposals, selected, shape)
                    matched = sel_p if sel_iou >= 0.5 else None
                    settings_rows.append(dict(
                        candidate=region['id'], filter_size=size, magnitude_floor_db=floor, scene_percentile=pct,
                        is_default=(size, floor, pct) == (3, 3.0, 90.0),
                        # (a) area / ranking change
                        footprint_pixels_screened=int(eligible[fp].sum()), original_pixels=region['pixels'],
                        top5_rank=sel_rank if matched else None,
                        matched_region_pixels=int(matched['pixels']) if matched else None,
                        # (b) similarity
                        best_iou_top5=round(float(sel_iou), 4), best_iou_any_proposal=round(float(any_iou), 4),
                        same_seed_interval_and_direction=bool(any_p is not None and any_iou >= 0.5 and
                            any_p['seed_interval'] == region['seed_interval'] and
                            ('increase' if any_p['seed_direction'] > 0 else 'decrease') == region['seed_direction'])))
    # (2) Leave-one-date-out on the default (existing) filtered cube.
    lodo = {}
    for region, fp in candidates:
        lodo[region['id']] = leave_one_date_out(data['HH'], data['HV'], common, dates, fp, region['seed_direction'], region['seed_interval'])
    # (3) Surrounding-ring comparison (raw change kept; no correction applied).
    rings = {}
    for region, fp in candidates:
        ring = ring_mask(fp, common, exclude=all_candidates)
        rings[region['id']] = ring_comparison(data['HH'], data['HV'], fp, ring, dates)
    scene_intervals = [dict(start=dates[i], end=dates[i + 1],
                            scene_dHH_db=float(np.median((data['HH'][i + 1] - data['HH'][i])[common])),
                            scene_dHV_db=float(np.median((data['HV'][i + 1] - data['HV'][i])[common]))) for i in range(len(dates) - 1)]

    summary = []
    for region, fp in candidates:
        rows = [r for r in settings_rows if r['candidate'] == region['id']]
        ranks = [r['top5_rank'] for r in rows]
        lodo_rows = lodo[region['id']]
        summary.append(dict(
            candidate=region['id'], area_km2=region['area_km2'], seed=f"{dates[region['seed_interval']]} → {dates[region['seed_interval'] + 1]} ({region['seed_direction']})",
            settings_variants=len(rows), variants_in_top5=sum(r is not None for r in ranks),
            rank_range=[min((r for r in ranks if r), default=None), max((r for r in ranks if r), default=None)],
            screened_pixels_range=[min(r['footprint_pixels_screened'] for r in rows), max(r['footprint_pixels_screened'] for r in rows)],
            iou_top5_range=[min(r['best_iou_top5'] for r in rows), max(r['best_iou_top5'] for r in rows)],
            variants_same_seed=sum(r['same_seed_interval_and_direction'] for r in rows),
            lodo_removals=len(lodo_rows),
            lodo_removals_still_notable=sum(r['seed_event_still_notable'] is True for r in lodo_rows),
            lodo_dates_not_notable=[r['removed_date'] for r in lodo_rows if r['seed_event_still_notable'] is False],
            lodo_dates_not_testable=[r['removed_date'] for r in lodo_rows if r['seed_event_still_notable'] is None],
            ring_seed_interval=rings[region['id']][region['seed_interval']]))
    files = dict(settings='settings_sensitivity.csv', lodo='leave_one_date_out.csv', ring='ring_comparison.csv')
    write_csv(OUT / files['settings'], settings_rows)
    write_csv(OUT / files['lodo'], [dict(candidate=c, **{k: (' | '.join(v) if isinstance(v, list) else v) for k, v in r.items() if k != 'intervals'}) for c, rows in lodo.items() for r in rows])
    write_csv(OUT / files['ring'], [dict(candidate=c, **r) for c, rows in rings.items() for r in rows])
    sources = {str(p.relative_to(ROOT)): sha(p) for p in (
        ROOT / 'data/polarization_analysis/six_date/hh_db.tif', ROOT / 'data/polarization_analysis/six_date/hv_db.tif',
        ROOT / 'data/polarization_analysis/six_date/hh_hv_cube.nc', ROOT / 'data/polarization_analysis/six_date/results.json',
        ROOT / 'data/investigation_engine/results.json', ROOT / 'data/investigation_engine/region_labels.tif')}
    report = dict(
        status='success', version=VERSION, supersedes='data/robustness (version 1)', created_utc=datetime.now(timezone.utc).isoformat(), network_access_used=False,
        dates=dates, product_ids=[o['product_id'] for o in data['report']['observations']],
        acquisition_gaps=acquisition_gaps(dates),
        method=dict(
            screening='src.investigation.event_components / describe_proposals / rank_regions, unchanged',
            settings_grid=dict(filter_size=FILTERS, magnitude_floor_db=FLOORS, scene_percentile=PERCENTILES,
                               default=dict(filter_size=3, magnitude_floor_db=3.0, scene_percentile=90.0),
                               filtering='3x3 (or 1/5) mask-aware linear-power mean on the all-date common mask, then dB'),
            area_and_rank='(a) pixels of the fixed footprint still screened; top-5 rank and pixels of the best-overlapping selected region (IoU >= 0.5)',
            similarity='(b) best IoU with any selected region and with any eligible proposal; same seed interval and direction',
            leave_one_date_out='default settings on the existing filtered cube with one date removed; only the interval that contains '
                               'the original seed event (merged across the removed date when needed) is checked with the existing '
                               'notable-interval rule (|median ΔHH| >= 3 dB and > scene 90th percentile) in the seed direction. '
                               'Same-direction changes in other intervals are listed separately and do not count. If the removed '
                               'date is the first or last date and an endpoint of the seed interval, the event is not testable.',
            ring=f'pixels {RING_INNER_PX * 10}-{RING_OUTER_PX * 10} m from the candidate, inside the common mask, excluding all candidates; '
                 'medians of raw pixel-wise change. A comparison, not a correction.'),
        default_variant_reproduces_saved_regions=dict(best_iou_per_candidate=default_check,
            note='Default variant recomputed from raw power with the all-date common mask; the saved regions used per-date masks.'),
        scene_intervals=scene_intervals, summary=summary, leave_one_date_out=lodo, ring_comparison=rings,
        files=files, source_sha256=sources, version_1_lodo_rule='counted any remaining interval (superseded)', elapsed_seconds=round(time.monotonic() - start, 1),
        limitations=['Same observations select and test the candidates; robustness is not validation.',
                     'Settings variants are sensitivity checks; no variant is preferred or tuned.',
                     'Removing a date changes interval lengths (12 → 24 or 36 days); a change that is still notable can be a longer-term difference.',
                     'The ring may contain different land cover from the candidate; a contrast does not identify a cause.'])
    (OUT / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    (OUT / 'REPORT.md').write_text(markdown_report(report))
    sidecar = dict(description='Sidecar for data/robustness_v2 outputs (version 2 of the robustness checks)', sources_sha256=sources,
                   outputs_sha256={name: sha(OUT / name) for name in [*files.values(), 'results.json', 'REPORT.md']})
    (OUT / 'sidecar.json').write_text(json.dumps(sidecar, indent=2) + '\n')
    print(json.dumps(dict(default_check=default_check, gaps=report['acquisition_gaps'], summary=summary), indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
