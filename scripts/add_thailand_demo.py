"""Ship the Thailand flood-validation scene (track 004 D; 2026-09-06, 09-18, 09-30; 10 km window) as an offline demo place.

Copies the three already-read windows from data/live_cache into data/demo_cache unchanged (same cache keys and format:
window.npz float32 + meta.json, SHA-256 checked on read), saves a dated public catalog snapshot (no credentials), writes
the place manifest and refreshes data/demo_cache/sidecar.json. No NISAR network read and no token.
Dates and window are those of the flood validation (docs/FLOOD_VALIDATION_PROTOCOL.md), not the demo selection rule.
"""
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))

from src.live_engine import (CACHE_DIR, DEMO_CACHE_DIR, PROCESSING_VERSION, cache_get, cache_key, group_products, search_catalog,
                             window_polygon)
from scripts.prewarm_demo import snapshot_products, write_sidecar

KEY, LAT, LON, KM = 'thailand_prachinburi', 14.0541, 101.3724, 10.0
DATES = ('2026-09-06', '2026-09-18', '2026-09-30')


def main():
    out = Path(DEMO_CACHE_DIR)
    if (out / 'places' / f'{KEY}.json').exists():
        print('Thailand demo place exists; left unchanged.'); return 0
    products, truncated = search_catalog(LAT, LON, date(2026, 9, 1), date(2026, 10, 15))
    group = next(g for g in group_products(products) if (g['key']['track'], g['key']['frame'], g['key']['direction'],
                 g['key']['bandwidth'], g['key']['polarization']) == ('004', '081', 'D', '4005', 'DHDH'))
    chosen = [p for p in group['products'] if p['date'] in DATES]
    assert [p['date'] for p in chosen] == list(DATES), [p['date'] for p in chosen]
    bounds = window_polygon(LAT, LON, KM).bounds
    keys = [cache_key(p['product_id'], bounds) for p in chosen]
    for k in keys:
        if cache_get(k, CACHE_DIR) is None:
            raise SystemExit(f'live cache entry {k} missing or failed its SHA-256 check')
        shutil.copytree(Path(CACHE_DIR) / k, out / k, dirs_exist_ok=False)
        if cache_get(k, out) is None:
            raise SystemExit(f'copied entry {k} failed its SHA-256 check')
    (out / 'catalog' / f'{KEY}.json').write_text(json.dumps(dict(
        place=KEY, lat=LAT, lon=LON, start='2026-09-01', end='2026-10-15', snapshot_date=date.today().isoformat(),
        snapshot_utc=datetime.now(timezone.utc).isoformat(), truncated=truncated, count=len(products),
        products=snapshot_products(products)), indent=2) + '\n')
    (out / 'places' / f'{KEY}.json').write_text(json.dumps(dict(
        place=KEY, lat=LAT, lon=LON, window_km=KM, surface='river floodplain: rice paddies, town, aquaculture',
        group=group['key'], dates=list(DATES), product_ids=[p['product_id'] for p in chosen], cache_keys=keys,
        selection_rule='Flood-validation scene (docs/FLOOD_VALIDATION_PROTOCOL.md): AOI thailand_prachinburi, track 004 D, '
                       'pre 2026-09-06, pre 2026-09-18 (forecast orbit; negative control), during 2026-09-30.',
        catalog_snapshot=f'catalog/{KEY}.json', processing_version=PROCESSING_VERSION, status='cached',
        source='copied unchanged from data/live_cache (windows read on 2026-11-15 for the flood validation)',
        prewarmed_utc=datetime.now(timezone.utc).isoformat()), indent=2) + '\n')
    sidecar = write_sidecar(out)
    print(f'demo cache: {len(sidecar["outputs_sha256"])} files, {sidecar["total_bytes"] / 1048576:.1f} MiB')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
