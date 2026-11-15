"""PRIMARY-rule maps for the Flood validation page (stages a, b, c), from the cached NISAR windows (no network read).

Writes only data/flood_validation/primary_maps/: per stage an .npz with uint8 `classes` (water_change.classify with the
untuned default HH -16 dB, |dHH| >= 3 dB) and uint8 `agreement` (new open water vs DSWx-S1: 0 excluded/invalid, 1 TP,
2 FP, 3 FN, 4 TN), plus meta.json and sidecar.json. Counts are checked against the saved stage outputs.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import numpy as np

from src import flood_validation as fv
from src.water_change import classify
from scripts.flood_step2 import nisar, reference

FV = ROOT / 'data/flood_validation'
OUT = FV / 'primary_maps'
STAGES = {
    'a': ('thailand_prachinburi', '004', '081', 'D', ('2026-09-06', '2026-09-30'), '20260908T230013Z', '20261001T230839Z'),
    'b': ('thailand_prachinburi', '011', '009', 'A', ('2026-09-06', '2026-09-30'), '20260908T230013Z', '20261001T230839Z'),
    'c': ('gandak_eo_image', '026', '015', 'A', ('2026-09-19', '2026-10-01'), '20260917T001912Z', '20260929T001912Z'),
}


def main():
    if (OUT / 'meta.json').exists():
        print('primary_maps exists; left unchanged.'); return 0
    OUT.mkdir(parents=True, exist_ok=True)
    meta = dict(created_utc=datetime.now(timezone.utc).isoformat(), rule=dict(fv.PRIMARY_CONFIG), stages={})
    for stage, (site, track, frame, d, dates, pre_id, dur_id) in STAGES.items():
        with patch('src.nisar_data.open_frequency_a', side_effect=AssertionError('no NISAR network read here')):
            cube = nisar(site, track, frame, d, dates, None)
        prep = fv.preprocess(cube)
        grid = dict(shape=prep['valid'].shape, transform=cube['transform'], crs=cube['crs'])
        classes, _ = classify(prep['HH'][0], prep['HH'][1], prep['valid'], fv.DEFAULT_HH, fv.MIN_CHANGE)
        pre = reference(site, 'S1', pre_id, grid); dur = reference(site, 'S1', dur_id, grid)
        pos, neg = fv.reference_new_water(pre['codes'], dur['codes'], 'S1')
        agreement = fv.agreement_map(classes == 2, pos, neg, prep['valid'])
        saved = next(r for r in json.loads((FV / f'step2{stage}/metrics.json').read_text())['rows']
                     if r.get('variant') == 'HH' and r['outcome'].startswith('new') and 'TP' in r
                     and ('PRIMARY' in r['threshold_set'] or 'default' in r['threshold_set']))
        counts = {k: int((agreement == v).sum()) for k, v in (('TP', 1), ('FP', 2), ('FN', 3), ('TN', 4))}
        if any(counts[k] != saved[k] for k in counts):
            raise SystemExit(f'stage {stage}: map counts differ from the saved metrics')
        np.savez_compressed(OUT / f'stage_{stage}.npz', classes=classes.astype(np.uint8), agreement=agreement)
        meta['stages'][stage] = dict(site=site, track=f'{track} {d}', dates=list(dates), transform=cube['transform'], crs=cube['crs'],
                                     references=[pre['granule'], dur['granule']], counts_match_saved_metrics=True, **counts)
    (OUT / 'meta.json').write_text(json.dumps(meta, indent=1) + '\n')
    files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != 'sidecar.json')
    (OUT / 'sidecar.json').write_text(json.dumps(dict(outputs_sha256={p.name: fv.sha256(p) for p in files},
        code_sha256={p: fv.sha256(ROOT / p) for p in ('scripts/flood_primary_maps.py', 'src/flood_validation.py')}), indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
