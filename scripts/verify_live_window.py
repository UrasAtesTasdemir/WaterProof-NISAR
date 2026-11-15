"""Gate check for the live engine: re-read the six cached Louisiana HH/HV windows live and compare.

Uses src.live_engine.run_live (existing authenticated, host-restricted byte-range reader) on the same
area of interest and dates as data/polarization_analysis/six_date/hh_hv_cube.nc, with a fresh, separate
cache directory so the timing reflects real network reads. Writes ONLY data/live_verification/
(report.json + sidecar.json). The token is read by the existing helper and is never printed or saved.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import numpy as np
import xarray as xr
from shapely import wkt

from scripts.check_earthdata_access import available_token
from src.live_engine import parse_product, run_live, LiveError

OUT = ROOT / 'data/live_verification'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    if (OUT / 'report.json').exists() and not args.overwrite:
        print('data/live_verification exists; left unchanged (use --overwrite).'); return 0
    token = available_token()
    if not token:
        print('No Earthdata token available; live verification skipped.'); return 2
    manifest = json.loads((ROOT / 'data/time_series/manifest.json').read_text())
    aoi = wkt.loads(manifest['aoi_wkt'])
    products = [parse_product(o['download_url']) for o in manifest['observations']]
    if any(p is None for p in products):
        print('A cached product URL does not match the NISAR filename pattern.'); return 1
    cube_path = ROOT / 'data/polarization_analysis/six_date/hh_hv_cube.nc'
    with xr.open_dataset(cube_path, engine='h5netcdf') as ds:
        cached_hh = ds.HHHH_linear_power.values.astype(float); cached_hv = ds.HVHV_linear_power.values.astype(float)
    centre = aoi.centroid
    steps = []
    def progress(i, total, product, how):
        steps.append(dict(index=i, date=product['date'], source=how, t=round(time.monotonic() - started, 1)))
        print(f'  {i + 1}/{total} {product["date"]}: {how}', flush=True)
    with tempfile.TemporaryDirectory() as cache:
        started = time.monotonic()
        try:
            cube = run_live(products, centre.y, centre.x, 5, token, progress=progress, cache_dir=cache, polygon=aoi)
        except LiveError as exc:
            print('Live read failed:', exc); return 1
        first_seconds = round(time.monotonic() - started, 1)
        started = time.monotonic(); steps_first = list(steps); steps.clear()
        repeat = run_live(products, centre.y, centre.x, 5, None, progress=progress, cache_dir=cache, polygon=aoi)
        repeat_seconds = round(time.monotonic() - started, 1)
    del token
    comparison = {}
    for band, live, saved in (('HH', cube['hh_power'], cached_hh), ('HV', cube['hv_power'], cached_hv)):
        same_shape = live.shape == saved.shape
        finite_live, finite_saved = np.isfinite(live), np.isfinite(saved)
        both = finite_live & finite_saved if same_shape else None
        comparison[band] = dict(
            live_shape=list(live.shape), cached_shape=list(saved.shape), same_shape=same_shape,
            same_valid_mask=bool(same_shape and np.array_equal(finite_live, finite_saved)),
            max_abs_difference=float(np.max(np.abs(live[both] - saved[both]))) if same_shape and both.any() else None,
            max_relative_difference=float(np.max(np.abs(live[both] - saved[both]) / np.abs(saved[both]))) if same_shape and both.any() else None,
            allclose_rtol_1e_6=bool(same_shape and np.allclose(live[both], saved[both], rtol=1e-6, atol=0)))
    report = dict(status='success', created_utc=datetime.now(timezone.utc).isoformat(),
                  purpose='Live engine reproduces the cached Louisiana six-date HH/HV windows',
                  product_ids=cube['product_ids'], dates=cube['dates'], area_of_interest_wkt=manifest['aoi_wkt'],
                  live_read=dict(elapsed_seconds=first_seconds, range_bytes_read=cube['bytes_read_this_run'],
                                 mib_read=round(cube['bytes_read_this_run'] / 1048576, 1), steps=steps_first,
                                 seconds_per_date=round(first_seconds / len(products), 1)),
                  repeat_from_cache=dict(elapsed_seconds=repeat_seconds, network_bytes=repeat['bytes_read_this_run'],
                                         dates_from_cache=repeat['dates_from_cache'], token_used=False),
                  comparison=comparison, full_product_downloaded=False,
                  credentials_stored=False, cached_source_sha256=sha(cube_path))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (OUT / 'sidecar.json').write_text(json.dumps(dict(description='Sidecar for data/live_verification',
        outputs_sha256={'report.json': sha(OUT / 'report.json')}, sources_sha256={str(cube_path.relative_to(ROOT)): sha(cube_path)}), indent=2) + '\n')
    print(json.dumps(dict(live=report['live_read'], repeat=report['repeat_from_cache'], comparison=comparison), indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
