"""Placebo (null) check for the five saved Louisiana candidates -> data/placebo/ (NEW folder; never overwrites).

Method: docs/PLACEBO_METHOD.md (fixed before results). Offline: uses only saved local data.
Outputs: results.json, summary.csv, sidecar.json (SHA-256 of every output, seed, parameters, code version, sources).
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
import rasterio

from src import placebo
from src.polarization import load_polarization

SOURCES = ('data/polarization_analysis/six_date/hh_hv_cube.nc', 'data/polarization_analysis/six_date/results.json',
           'data/investigation_engine/region_labels.tif', 'data/investigation_engine/results.json',
           'data/robustness_v2/results.json')
CODE = ('src/placebo.py', 'scripts/process_placebo.py', 'src/robustness.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compute(root=ROOT, draws=placebo.DRAWS):
    data = load_polarization(Path(root) / 'data/polarization_analysis/six_date')
    dates = [o['date'] for o in data['report']['observations']]
    with rasterio.open(Path(root) / 'data/investigation_engine/region_labels.tif') as src:
        labels = src.read(1)
    regions = json.loads((Path(root) / 'data/investigation_engine/results.json').read_text())['regions']
    ids = [r['id'] for r in regions]
    saved = {s['candidate']: s['ring_seed_interval'] for s in json.loads((Path(root) / 'data/robustness_v2/results.json').read_text())['summary']}
    rows = []
    for region in regions:
        result = placebo.placebo_for_candidate(data['HH'], data['HV'], data['common'], labels, region['id'],
                                               region['seed_interval'], dates, ids, draws=draws)
        ref = saved.get(region['id'])
        if ref:
            result['matches_saved_ring_comparison'] = bool(
                abs(ref['candidate_minus_ring_dHH_db'] - result['HH']['candidate_minus_ring_db']) < 1e-4 and
                abs(ref['candidate_minus_ring_dHV_db'] - result['HV']['candidate_minus_ring_db']) < 1e-4)
        result['seed_direction'] = region['seed_direction']
        rows.append(result)
    return dates, rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    out = placebo.OUTPUT
    if (out / 'results.json').exists() and not args.overwrite:
        print('data/placebo exists; left unchanged (use --overwrite).'); return 0
    started = time.monotonic()
    dates, rows = compute()
    report = dict(status='success', version=placebo.VERSION, created_utc=datetime.now(timezone.utc).isoformat(),
                  network_access_used=False, method_document='docs/PLACEBO_METHOD.md', dates=dates,
                  parameters=dict(draws=placebo.DRAWS, base_seed=placebo.BASE_SEED, seed_rule='base_seed + candidate id',
                                  min_placements=placebo.MIN_PLACEMENTS, min_ring_pixels=placebo.MIN_RING_PIXELS,
                                  min_spacing_px=placebo.MIN_SPACING_PX, pixel_size_m=10,
                                  ring='src.robustness.ring_mask: 50-150 m, common mask, all saved candidates excluded',
                                  statistic='candidate (or placement) median change minus ring median change, seed interval, raw',
                                  exceedance_fraction='(count(|null| >= |candidate|) + 1) / (placements + 1)'),
                  multiple_comparison_correction=None,
                  limitations=['Descriptive comparison, not a significance test and not evidence of a physical cause.',
                               'Candidates were selected for large change in this interval; random regions were not, so the '
                               'comparison is incomplete and a candidate looking unusual is expected.',
                               'Nearby placements are not independent (spatial autocorrelation); the 100 m minimum spacing is a '
                               'simplification.',
                               'No multiple-comparison correction across the five candidates or two channels.',
                               'No independent reference; nothing confirms water, flooding or land-cover change.'],
                  optional_other_intervals='skipped (see docs/PLACEBO_METHOD.md)',
                  candidates=rows, elapsed_seconds=round(time.monotonic() - started, 1))
    out.mkdir(parents=True, exist_ok=True)
    (out / 'results.json').write_text(json.dumps(report, indent=1) + '\n')
    with (out / 'summary.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['candidate', 'interval', 'status', 'placements', 'draws', 'seed', 'band', 'candidate_minus_ring_db',
                         'null_median_db', 'null_p05_db', 'null_p95_db', 'exceedance_fraction'])
        for r in rows:
            for band in ('HH', 'HV'):
                b = r[band]
                writer.writerow([r['candidate'], ' -> '.join(r['interval']), r['status'], r['placements'], r['draws_attempted'],
                                 r['seed'], band, f"{b['candidate_minus_ring_db']:.4f}"] +
                                [f"{b[k]:.4f}" if k in b else '' for k in ('null_median_db', 'null_p05_db', 'null_p95_db',
                                                                          'exceedance_fraction')])
    sidecar = dict(description='Sidecar for data/placebo (placebo / null check, docs/PLACEBO_METHOD.md)',
                   outputs_sha256={name: sha(out / name) for name in ('results.json', 'summary.csv')},
                   seed=dict(base_seed=placebo.BASE_SEED, rule='base_seed + candidate id'), parameters=report['parameters'],
                   code_version=dict(version=placebo.VERSION, **{p: sha(ROOT / p) for p in CODE}),
                   sources_sha256={p: sha(ROOT / p) for p in SOURCES})
    (out / 'sidecar.json').write_text(json.dumps(sidecar, indent=2) + '\n')
    for r in rows:
        print(r['candidate'], r['status'], r['placements'],
              {band: {k: round(v, 4) for k, v in r[band].items() if k != 'null_values_db'} for band in ('HH', 'HV')},
              'matches saved ring:', r.get('matches_saved_ring_comparison'))
    print(f"elapsed {report['elapsed_seconds']} s")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
