"""Pre-warm the shipped, offline demo cache (data/demo_cache/) for the places in data/demo_places/places.json.

For each place: one public catalog search (no credentials) saved as a dated snapshot, then the existing live
engine (src.live_engine.run_live -> existing authenticated, host-restricted byte-range reader) reads only the
small HH/HV window for up to `max_dates` dates of one compatible group. Entries use exactly the live-cache key
and format (window.npz + meta.json: radar arrays and non-sensitive metadata only).

Never stores, prints or logs credentials or signed URLs. Existing entries are reused, never overwritten.
Writes ONLY under data/demo_cache/. A sidecar (data/demo_cache/sidecar.json) lists the SHA-256 of every file.

Run:  .venv/bin/python scripts/prewarm_demo.py            (all places)
      .venv/bin/python scripts/prewarm_demo.py --place marmara_lake
"""
import argparse
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))

from src.live_engine import (DEMO_CACHE_DIR, LiveError, search_catalog, group_products, run_live, window_polygon,
                             cache_key, PROCESSING_VERSION)

CONFIG = ROOT / 'data/demo_places/places.json'
SIDECAR = 'sidecar.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def plain_url(url):
    """Public product URL without query string or fragment (no signatures can survive)."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))


def snapshot_products(products):
    return [dict(product_id=p['product_id'], start_time_utc=p['start_time_utc'], date=p['date'],
                 download_url=plain_url(p['download_url']), filename_fields=p['filename_fields'], group=p['group'],
                 has_hh_hv=p['has_hh_hv']) for p in products]


def choose(groups, max_dates):
    """Fixed selection rule (documented in places.json and docs/demo_places.md): first (largest) HH+HV group,
    its first `max_dates` dates. Never depends on radar values."""
    usable = [g for g in groups if g['has_hh_hv'] and len(g['products']) >= 2]
    if not usable:
        return None
    return usable[0], usable[0]['products'][:max_dates]


def write_sidecar(directory):
    directory = Path(directory)
    files = sorted(p for p in directory.rglob('*') if p.is_file() and p.name != SIDECAR)
    sidecar = dict(description='Sidecar for data/demo_cache (shipped offline demo windows and catalog snapshots).',
                   processing_version=PROCESSING_VERSION, created_utc=datetime.now(timezone.utc).isoformat(),
                   outputs_sha256={str(p.relative_to(directory)): sha(p) for p in files},
                   total_bytes=sum(p.stat().st_size for p in files), credentials_stored=False)
    (directory / SIDECAR).write_text(json.dumps(sidecar, indent=2) + '\n')
    return sidecar


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--place', action='append', help='only this place key (repeatable)')
    parser.add_argument('--catalog-only', action='store_true', help='save catalog snapshots only (no token needed)')
    args = parser.parse_args(argv)
    config = json.loads(CONFIG.read_text())
    places = [p for p in config['places'] if not args.place or p['key'] in args.place]
    start, end = (date.fromisoformat(d) for d in config['date_range'])
    km = float(config['window_km']); max_dates = int(config['max_dates'])
    token = None
    if not args.catalog_only:
        from scripts.check_earthdata_access import available_token
        token = available_token()
        if not token:
            print('No Earthdata token available through the existing helper; catalog snapshots only.')
    out = Path(DEMO_CACHE_DIR); (out / 'catalog').mkdir(parents=True, exist_ok=True); (out / 'places').mkdir(exist_ok=True)
    status = 0
    for place in places:
        key = place['key']; lat, lon = place['lat'], place['lon']
        print(f'[{key}] catalog search ({lat}, {lon}, {start} to {end})', flush=True)
        try:
            products, truncated = search_catalog(lat, lon, start, end)
        except LiveError as exc:
            print(f'[{key}] catalog search failed: {exc}'); status = 1; continue
        groups = group_products(products)
        snapshot = dict(place=key, lat=lat, lon=lon, start=start.isoformat(), end=end.isoformat(),
                        snapshot_date=date.today().isoformat(), snapshot_utc=datetime.now(timezone.utc).isoformat(),
                        truncated=truncated, count=len(products), products=snapshot_products(products))
        (out / 'catalog' / f'{key}.json').write_text(json.dumps(snapshot, indent=2) + '\n')
        chosen = choose(groups, max_dates)
        if not chosen:
            print(f'[{key}] no compatible HH+HV group; nothing to read.'); status = 1; continue
        group, selected = chosen
        bounds = window_polygon(lat, lon, km).bounds
        manifest = dict(place=key, lat=lat, lon=lon, window_km=km, surface=place.get('surface'),
                        group=group['key'], dates=[p['date'] for p in selected],
                        product_ids=[p['product_id'] for p in selected],
                        cache_keys=[cache_key(p['product_id'], bounds) for p in selected],
                        selection_rule=config['selection_rule'], catalog_snapshot=f'catalog/{key}.json',
                        processing_version=PROCESSING_VERSION)
        if token:
            started = time.monotonic()
            def progress(i, total, product, how):
                print(f'[{key}]   {i + 1}/{total} {product["date"]}: {how} ({time.monotonic() - started:.0f} s)', flush=True)
            try:
                cube = run_live(selected, lat, lon, km, token, progress=progress, cache_dir=out, demo_dir=None)
            except LiveError as exc:
                print(f'[{key}] window read failed: {exc}'); status = 1
            else:
                manifest.update(status='cached', read_seconds=round(time.monotonic() - started, 1),
                                range_bytes_read=cube['bytes_read_this_run'], dates_reused=cube['dates_from_cache'],
                                prewarmed_utc=datetime.now(timezone.utc).isoformat())
        else:
            manifest.update(status='pending token run')
        (out / 'places' / f'{key}.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(f'[{key}] {manifest["status"]}: {", ".join(manifest["dates"])}', flush=True)
    del token
    sidecar = write_sidecar(out)
    print(f'data/demo_cache: {len(sidecar["outputs_sha256"])} files, {sidecar["total_bytes"] / 1048576:.1f} MiB')
    return status


if __name__ == '__main__':
    raise SystemExit(main())
