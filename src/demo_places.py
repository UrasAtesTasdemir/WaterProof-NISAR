"""Shipped offline demo places (data/demo_cache/, written by scripts/prewarm_demo.py).

Read-only at run time. Each place has a manifest (places/<key>.json: point, window, product IDs, cache keys),
a dated catalog snapshot (catalog/<key>.json) and live-cache-format window entries (<cache key>/window.npz +
meta.json). data/demo_cache/sidecar.json lists the SHA-256 of every file. No credentials, no signed URLs.
"""
import hashlib
import json
from pathlib import Path

from src.live_engine import DEMO_CACHE_DIR, LiveError, cache_get, group_products, run_live

SIDECAR = 'sidecar.json'


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(directory=DEMO_CACHE_DIR):
    """List of files whose SHA-256 differs from the sidecar (or that are missing / unlisted)."""
    directory = Path(directory)
    sidecar = json.loads((directory / SIDECAR).read_text())
    listed = sidecar['outputs_sha256']
    problems = [name for name, digest in listed.items() if not (directory / name).is_file() or _sha(directory / name) != digest]
    present = {str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file() and p.name != SIDECAR}
    return problems + sorted(present - set(listed))


def places(directory=DEMO_CACHE_DIR):
    """Demo places with a manifest and a catalog snapshot, as Explore presets (cached=True, case='demo')."""
    directory = Path(directory); out = []
    for path in sorted((directory / 'places').glob('*.json')):
        try:
            manifest = json.loads(path.read_text())
            snapshot = json.loads((directory / manifest['catalog_snapshot']).read_text())
        except (OSError, KeyError, ValueError):
            continue
        out.append(dict(key=manifest['place'], lat=manifest['lat'], lon=manifest['lon'], cached=True, case='demo',
                        manifest=manifest, snapshot=snapshot))
    return out


def snapshot_groups(place):
    return group_products(place['snapshot']['products'])


def missing_dates(place, directory=DEMO_CACHE_DIR):
    m = place['manifest']
    return [d for d, key in zip(m['dates'], m['cache_keys']) if cache_get(key, directory) is None]


def demo_cube(place, directory=DEMO_CACHE_DIR):
    """The place's cube from the shipped cache only (no token, no network). Raises LiveError if a date is missing."""
    m = place['manifest']
    if m.get('status') != 'cached' or missing_dates(place, directory):
        raise LiveError('ex.demo.pending')
    wanted = set(m['product_ids'])
    products = [p for p in place['snapshot']['products'] if p['product_id'] in wanted]
    if len(products) != len(wanted):
        raise LiveError('ex.demo.pending')
    def offline(*_args, **_kwargs):
        raise LiveError('ex.demo.pending')
    cube = run_live(products, m['lat'], m['lon'], m['window_km'], None, demo_dir=directory, cache_dir=directory,
                    opener=offline)
    group = next((g for g in group_products(place['snapshot']['products'])
                  if all(g['key'].get(k) == v for k, v in m.get('group', {}).items())), None)
    return dict(cube, source='demo', bytes_read_this_run=0, catalog_dates=group['dates'] if group else None)
