"""Read every OPERA DSWx reference WTR window for the flood-validation AOIs and record code histograms.

No NISAR data and no metric. Writes ONLY data/flood_validation/reference/ (window arrays .npz, scan.json, sidecar.json).
Reader: src/podaac_reader.py (allowlisted hosts, manual redirects, byte caps; token only to the PO.DAAC archive host).
The token comes from the existing helper and is never printed or stored. Signed URLs are never stored.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import numpy as np
import requests
from shapely.geometry import shape

from src.flood_classes import summarize, VALID_FRACTION_MIN
from src.podaac_reader import ByteBudget, ReferenceAccessError, read_window

OUT = ROOT / 'data/flood_validation/reference'
CMR = 'https://cmr.earthdata.nasa.gov/search/granules.json'
UA = {'User-Agent': 'NISAR-Change-Compass/1.0 (educational demo)'}
SITES = {
    'thailand_prachinburi': dict(tile='T47PQR', start='2026-09-01T00:00:00Z', end='2026-10-06T00:00:00Z'),
    'gandak_eo_image': dict(tile='T45RTK', start='2026-09-14T00:00:00Z', end='2026-10-06T00:00:00Z'),
    'gandak_bagaha': dict(tile='T45RTK', start='2026-09-14T00:00:00Z', end='2026-10-06T00:00:00Z'),
}
PRODUCTS = {'HLS': 'OPERA_L3_DSWX-HLS_V1', 'S1': 'OPERA_L3_DSWX-S1_V1'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def granules(short_name, aoi, start, end, tile):
    c = aoi.centroid
    r = requests.get(CMR, params={'short_name': short_name, 'point': f'{c.x},{c.y}', 'temporal': f'{start},{end}',
                                  'page_size': 200}, headers=UA, timeout=60)
    r.raise_for_status()
    out = {}
    for e in r.json()['feed']['entry']:
        title = e['title']
        if f'_{tile}_' not in title:
            continue
        url = next((l['href'] for l in e.get('links', []) if l['href'].startswith('https://archive.podaac')
                    and l['href'].endswith('_B01_WTR.tif')), None)
        parts = title.split('_')
        acq, produced = parts[4], parts[5]          # ..._<tile>_<acquisition>_<production>_<sensor>_30_v...
        if url and (acq not in out or produced > out[acq]['produced']):
            out[acq] = dict(title=title, url=url, acquired=acq, produced=produced, sensor=parts[6],
                            version=parts[-1])
    return [out[k] for k in sorted(out)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    if (OUT / 'scan.json').exists() and not args.overwrite:
        print('data/flood_validation/reference exists; left unchanged (use --overwrite).'); return 0
    from scripts.check_earthdata_access import available_token
    token = available_token()
    if not token:
        print('No Earthdata token available through the existing helper.'); return 2
    budget = ByteBudget(); rows = []; session = requests.Session()
    for site, cfg in SITES.items():
        aoi = shape(json.loads((ROOT / f'data/flood_validation/aoi/{site}.geojson').read_text())['features'][0]['geometry'])
        (OUT / site).mkdir(parents=True, exist_ok=True)
        for kind, short in PRODUCTS.items():
            for g in granules(short, aoi, cfg['start'], cfg['end'], cfg['tile']):
                row = dict(site=site, product=kind, tile=cfg['tile'], granule=g['title'], acquired_utc=g['acquired'],
                           produced_utc=g['produced'], sensor=g['sensor'], version=g['version'])
                try:
                    w = read_window(g['url'], token, aoi, budget, session=session)
                except ReferenceAccessError as exc:
                    row.update(status='read failed', error=str(exc)); rows.append(row); print(site, kind, g['acquired'], 'FAILED'); continue
                name = f"{kind}_{g['acquired']}.npz"
                np.savez_compressed(OUT / site / name, wtr=w['array'])
                row.update(status='read', file=f'{site}/{name}', bytes_read=w['bytes_read'], crs=w['crs'],
                           transform=w['transform'], window_outside_file=w['outside_file'],
                           file_product_version=w['tags'].get('PRODUCT_VERSION') or w['tags'].get('DSWX_PRODUCT_VERSION'),
                           file_software_version=w['tags'].get('SOFTWARE_VERSION'),
                           **summarize(w['array'], kind))
                rows.append(row)
                print(site, kind, g['acquired'], g['sensor'], f"valid {row['valid_fraction']:.3f}", row['usable'],
                      'hist', row['histogram'], flush=True)
    del token
    report = dict(created_utc=datetime.now(timezone.utc).isoformat(), purpose='Reference code histograms and valid '
                  'fractions before any metric (docs/FLOOD_VALIDATION_PROTOCOL.md section 9)',
                  valid_fraction_min=VALID_FRACTION_MIN, total_bytes_read=budget.total, scenes=rows,
                  credentials_stored=False, signed_urls_stored=False)
    (OUT / 'scan.json').write_text(json.dumps(report, indent=1) + '\n')
    files = sorted(p for p in OUT.rglob('*') if p.is_file() and p.name != 'sidecar.json')
    (OUT / 'sidecar.json').write_text(json.dumps(dict(outputs_sha256={str(p.relative_to(OUT)): sha(p) for p in files},
        code_sha256={p: sha(ROOT / p) for p in ('scripts/flood_reference_scan.py', 'src/podaac_reader.py', 'src/flood_classes.py')}),
        indent=2) + '\n')
    print(f'total bytes read: {budget.total}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
