"""Live NISAR window engine for the "Explore the world" page.

For a user-chosen point and date range: search the public ASF catalog (no
credentials), group compatible GCOV acquisitions, and read ONLY a small square
window of HH and HV power around the point through the existing authenticated,
TLS-verified, host-restricted HTTP byte-range code (src.nisar_data.open_frequency_a
plus scripts.visualize_nisar.read_subset). Nothing here downloads a full product.

Safety rules:
- Strict validation of latitude, longitude, dates and window size; hard caps on
  dates per run, bytes per product (256 MiB in open_frequency_a) and bytes per run.
- The Earthdata token is only ever a function argument. It is never stored,
  logged, cached, hashed or put into an exception message: errors raised here
  carry fixed text plus the exception type name only.
- The disk cache (data/live_cache/, git-ignored, size-capped) holds radar
  arrays and non-sensitive metadata keyed by product ID + window bounds +
  processing version. Signed URLs and credentials are never written.
"""
from collections import defaultdict
from datetime import date, datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
from urllib.parse import unquote, urlparse

import numpy as np
from src.grid_validation import assert_same_grid, metric_grid

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / 'data/live_cache'
DEMO_CACHE_DIR = ROOT / 'data/demo_cache'    # shipped, tracked, read-only at run time (scripts/prewarm_demo.py writes it)
PROCESSING_VERSION = 'live-window-v1'
DEFAULT_WINDOW_KM = 5.0
MIN_WINDOW_KM = 1.0
MAX_WINDOW_KM = 10.0
MAX_DATES = 6
MAX_RUN_BYTES = 768 * 1024 * 1024          # per live run (per product the reader already stops at 256 MiB)
CACHE_LIMIT_BYTES = 512 * 1024 * 1024
MAX_DATE_SPAN_DAYS = 400
EARLIEST_DATE = date(2025, 7, 1)            # no NISAR science products exist before this
COMPATIBILITY = ('instrument', 'track', 'direction', 'frame', 'bandwidth', 'polarization', 'source', 'crid')
NAME = re.compile(
    r"^NISAR_(?P<instrument>[LS])2_PR_GCOV_(?P<cycle>\d{3})_"
    r"(?P<track>\d{3})_(?P<direction>[AD])_(?P<frame>\d{3})_"
    r"(?P<bandwidth>\d{4})_(?P<polarization>[A-Z]{4})_(?P<source>[AM])_"
    r"(?P<start>\d{8}T\d{6})_(?P<end>\d{8}T\d{6})_"
    r"(?P<crid>[PX]\d{5})_(?P<accuracy>[PMNF])_(?P<coverage>[FP])_"
    r"(?P<location>[A-Z])_(?P<counter>\d{3})\.h5$")
# Dual-pol modes whose frequency A carries both HH and HV (HHHH and HVHV power terms).
HH_HV_MODES = ('DHDH', 'QPQP', 'DHQP', 'QPDH')


class LiveError(Exception):
    """Fixed, non-sensitive message for the user (a translation key plus values). Never contains a token or a signed URL."""

    def __init__(self, key, **values):
        self.key = key; self.values = values
        super().__init__(key)

    def text(self, lang=None):
        from src.i18n import t
        return t(self.key, lang=lang, **self.values)

    def __str__(self):
        return self.text('en')


# ---------------------------------------------------------------- validation
def validate_point(lat, lon):
    try:
        lat = float(lat); lon = float(lon)
    except (TypeError, ValueError):
        raise LiveError('live.err.numbers') from None
    if not (math.isfinite(lat) and math.isfinite(lon)):
        raise LiveError('live.err.finite')
    if not -90 <= lat <= 90:
        raise LiveError('live.err.lat')
    if not -180 <= lon <= 180:
        raise LiveError('live.err.lon')
    if abs(lat) > 84:
        raise LiveError('live.err.polar')
    return lat, lon


def validate_dates(start, end, today=None):
    try:
        start = start if isinstance(start, date) else date.fromisoformat(str(start))
        end = end if isinstance(end, date) else date.fromisoformat(str(end))
    except ValueError:
        raise LiveError('live.err.date_format') from None
    today = today or datetime.now(timezone.utc).date()
    if end < start:
        raise LiveError('live.err.date_order')
    if start < EARLIEST_DATE:
        raise LiveError('live.err.date_early')
    if start > today:
        raise LiveError('live.err.date_future')
    if (end - start).days > MAX_DATE_SPAN_DAYS:
        raise LiveError('live.err.date_span', days=MAX_DATE_SPAN_DAYS)
    return start, end


def validate_window(km):
    try:
        km = float(km)
    except (TypeError, ValueError):
        raise LiveError('live.err.window_number') from None
    if not math.isfinite(km) or not MIN_WINDOW_KM <= km <= MAX_WINDOW_KM:
        raise LiveError('live.err.window_range', low=f'{MIN_WINDOW_KM:g}', high=f'{MAX_WINDOW_KM:g}')
    return km


def utm_epsg(lat, lon):
    zone = min(60, int((lon + 180) // 6) + 1)
    return (32600 if lat >= 0 else 32700) + zone


def window_polygon(lat, lon, km):
    """Square of side `km` centred on the point, built in the local UTM zone, returned in EPSG:4326."""
    from rasterio.warp import transform, transform_geom
    from shapely.geometry import box, mapping, shape
    lat, lon = validate_point(lat, lon); km = validate_window(km)
    crs = f'EPSG:{utm_epsg(lat, lon)}'
    (x,), (y,) = transform('EPSG:4326', crs, [lon], [lat])
    half = km * 500.0
    square = box(x - half, y - half, x + half, y + half).segmentize(half / 10)
    return shape(transform_geom(crs, 'EPSG:4326', mapping(square)))


# ---------------------------------------------------------------- catalog
def parse_product(url):
    filename = unquote(Path(urlparse(url).path).name)
    match = NAME.fullmatch(filename)
    if not match:
        return None
    fields = match.groupdict()
    start = datetime.strptime(fields['start'], '%Y%m%dT%H%M%S').replace(tzinfo=timezone.utc)
    return dict(product_id=filename.removesuffix('.h5'), start_time_utc=start.isoformat(), date=start.date().isoformat(),
                download_url=url, filename_fields=fields,
                group={k: fields[k] for k in COMPATIBILITY}, has_hh_hv=fields['polarization'] in HH_HV_MODES)


def search_catalog(lat, lon, start, end, search=None, max_results=250):
    """Public ASF catalog search (no credentials) for GCOV products whose footprint contains the point."""
    lat, lon = validate_point(lat, lon); start, end = validate_dates(start, end)
    if search is None:
        import asf_search as asf
        def search(**options):
            return asf.search(opts=asf.ASFSearchOptions(**options))
    try:
        results = search(dataset=['NISAR'], processingLevel=['GCOV'], intersectsWith=f'POINT({lon:.6f} {lat:.6f})',
                         start=f'{start.isoformat()}T00:00:00Z', end=f'{end.isoformat()}T23:59:59Z', maxResults=max_results)
    except Exception as exc:  # noqa: BLE001 - network/catalog failures become a fixed message
        raise LiveError('live.err.catalog', error=type(exc).__name__) from None
    products = {}
    for record in results:
        try:
            urls = record.find_urls(extension='.h5', pattern=r'^(?!.*QA_STATS).*', directAccess=False)
        except Exception:  # noqa: BLE001
            urls = []
        for url in urls:
            product = parse_product(url)
            if product:
                products[product['product_id']] = product
    truncated = len(results) >= max_results
    return sorted(products.values(), key=lambda p: p['start_time_utc']), truncated


def group_products(products):
    """Compatible acquisitions: same instrument, track, direction, frame, bandwidth, polarization mode, source and release."""
    groups = defaultdict(list)
    for p in products:
        groups[tuple(p['group'][k] for k in COMPATIBILITY)].append(p)
    out = []
    for key, items in groups.items():
        items = sorted(items, key=lambda p: p['start_time_utc'])
        # one product per acquisition date (latest counter wins)
        by_date = {}
        for p in items:
            by_date[p['date']] = p
        items = [by_date[d] for d in sorted(by_date)]
        out.append(dict(key=dict(zip(COMPATIBILITY, key)), products=items, dates=[p['date'] for p in items],
                        has_hh_hv=all(p['has_hh_hv'] for p in items)))
    return sorted(out, key=lambda g: (not g['has_hh_hv'], -len(g['products'])))


# ---------------------------------------------------------------- disk cache
def cache_key(product_id, bounds, version=PROCESSING_VERSION):
    """Key from product ID, rounded window bounds and processing version only (never credentials)."""
    text = '|'.join([str(product_id), ','.join(f'{b:.6f}' for b in bounds), version])
    return hashlib.sha256(text.encode()).hexdigest()


def cache_get(key, directory=CACHE_DIR):
    directory = Path(directory) / key
    try:
        meta = json.loads((directory / 'meta.json').read_text())
        with np.load(directory / 'window.npz') as arrays:
            if hashlib.sha256((directory / 'window.npz').read_bytes()).hexdigest() != meta['sha256']:
                return None
            return dict(hh=arrays['hh'].astype(float), hv=arrays['hv'].astype(float), meta=meta)
    except (OSError, KeyError, ValueError):
        return None


def cache_lookup(key, cache_dir=CACHE_DIR, demo_dir=DEMO_CACHE_DIR):
    """Shipped demo cache first (read-only), then the local live cache. Returns (entry or None, 'demo'|'cache'|None)."""
    if demo_dir is not None:
        entry = cache_get(key, demo_dir)
        if entry is not None:
            return entry, 'demo'
    entry = cache_get(key, cache_dir)
    return (entry, 'cache') if entry is not None else (None, None)


def cache_put(key, hh, hv, meta, directory=CACHE_DIR, limit=CACHE_LIMIT_BYTES):
    root = Path(directory); target = root / key
    target.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(target / 'window.npz', hh=np.asarray(hh, np.float32), hv=np.asarray(hv, np.float32))
    meta = dict(meta, sha256=hashlib.sha256((target / 'window.npz').read_bytes()).hexdigest(),
                cached_utc=datetime.now(timezone.utc).isoformat(), processing_version=PROCESSING_VERSION)
    (target / 'meta.json').write_text(json.dumps(meta, indent=2) + '\n')
    _enforce_limit(root, limit, keep=key)
    return meta


def _enforce_limit(root, limit, keep=None):
    entries = []
    for entry in Path(root).iterdir():
        if entry.is_dir():
            size = sum(f.stat().st_size for f in entry.iterdir() if f.is_file())
            entries.append((entry.stat().st_mtime, size, entry))
    total = sum(e[1] for e in entries)
    for _, size, entry in sorted(entries):
        if total <= limit:
            break
        if entry.name == keep:
            continue
        for f in entry.iterdir():
            f.unlink()
        entry.rmdir(); total -= size


# ---------------------------------------------------------------- window reads
def _clean(text, token):
    return text.replace(token, '[redacted]') if token else text


def read_window(product, polygon, token, opener=None, subset=None):
    """HH and HV power of one product inside `polygon` (EPSG:4326), plus grid and transfer statistics."""
    if opener is None:
        from src.nisar_data import open_frequency_a as opener
    if subset is None:
        from scripts.visualize_nisar import read_subset as subset
    if not token:
        raise LiveError('live.err.token')
    try:
        with opener(product, token) as (dataset, stats):
            hh, _, crs, transform, meta_hh = subset(dataset, polygon, layer_name='HHHH')
            hv, _, crs_hv, transform_hv, meta_hv = subset(dataset, polygon, layer_name='HVHV')
            try:
                assert_same_grid(dict(crs=crs,transform=transform,shape=hh.shape),
                                 dict(crs=crs_hv,transform=transform_hv,shape=hv.shape))
            except ValueError:
                raise LiveError('live.err.hhhv_grid')
            bytes_read = int(stats['range_bytes_read'])
    except LiveError:
        raise
    except Exception as exc:  # noqa: BLE001 - only the type name and a fixed sentence leave this function
        message = _clean(str(getattr(exc, 'args', [''])[0]) if exc.args else '', token)
        known = type(exc).__name__ in ('RadarDataError', 'AccessCheckError')
        raise LiveError('live.err.read', product=product['product_id'], error=type(exc).__name__,
                        detail=f': {message}' if known and message else '') from None
    return dict(hh=hh, hv=hv, crs=str(crs), transform=list(transform)[:6], bytes=bytes_read,
                shape=list(hh.shape), meta=dict(HH=meta_hh, HV=meta_hv))


def run_live(products, lat, lon, km, token, progress=None, opener=None, subset=None, cache_dir=CACHE_DIR,
             max_run_bytes=MAX_RUN_BYTES, polygon=None, demo_dir=DEMO_CACHE_DIR):
    """Read (or reuse from cache) HH/HV windows for up to MAX_DATES products of one compatible group.

    Lookup order per date: shipped demo cache (read-only), local live cache, then the network."""
    lat, lon = validate_point(lat, lon); km = validate_window(km)
    if not products:
        raise LiveError('live.err.none')
    if len(products) > MAX_DATES:
        raise LiveError('live.err.too_many', max=MAX_DATES)
    if len({tuple(p['group'][k] for k in COMPATIBILITY) for p in products}) != 1:
        raise LiveError('live.err.mixed')
    if not all(p['has_hh_hv'] for p in products):
        raise LiveError('live.err.no_hv')
    polygon = polygon if polygon is not None else window_polygon(lat, lon, km)
    bounds = polygon.bounds
    started = time.monotonic(); total_bytes = 0; windows = []; from_cache = 0
    for index, product in enumerate(sorted(products, key=lambda p: p['start_time_utc'])):
        key = cache_key(product['product_id'], bounds)
        cached, _where = cache_lookup(key, cache_dir, demo_dir)
        if progress:
            progress(index, len(products), product, 'cache' if cached else 'read')
        if cached is not None:
            from_cache += 1
        else:
            if total_bytes >= max_run_bytes:
                raise LiveError('live.err.budget')
            window = read_window(product, polygon, token, opener, subset)
            total_bytes += window['bytes']
            if total_bytes > max_run_bytes:
                raise LiveError('live.err.budget')
            meta = dict(product_id=product['product_id'], date=product['date'], start_time_utc=product['start_time_utc'],
                        bounds_wgs84=list(bounds), crs=window['crs'], transform=window['transform'], shape=window['shape'],
                        range_bytes_read=window['bytes'], group=product['group'], layers=['HHHH', 'HVHV'],
                        hdf5_group='/science/LSAR/GCOV/grids/frequencyA', full_product_downloaded=False)
            meta = cache_put(key, window['hh'], window['hv'], meta, cache_dir)
            cached = dict(hh=window['hh'].astype(float), hv=window['hv'].astype(float), meta=meta)
        windows.append(cached)
    first = windows[0]['meta']
    try:
        metric_grid(first['crs'],first['transform'],first['shape'])
        for w in windows[1:]:
            assert_same_grid(first,w['meta'])
    except ValueError:
        raise LiveError('live.err.grid') from None
    return dict(source='live', lat=lat, lon=lon, window_km=km,
                dates=[w['meta']['date'] for w in windows],
                times=[w['meta']['start_time_utc'] for w in windows],
                product_ids=[w['meta']['product_id'] for w in windows],
                hh_power=np.stack([w['hh'] for w in windows]), hv_power=np.stack([w['hv'] for w in windows]),
                crs=first['crs'], transform=first['transform'], bytes_read_this_run=total_bytes,
                dates_from_cache=from_cache,
                elapsed_seconds=round(time.monotonic() - started, 1))


def token_status():
    """Where a server-side token would come from, without reading or returning it."""
    try:
        from scripts.check_earthdata_access import TOKEN_VARIABLES, SECRET
    except ImportError:
        return None
    if any(os.environ.get(name, '').strip() for name in TOKEN_VARIABLES):
        return 'environment'
    if SECRET.is_file():
        return 'local file'
    try:
        import streamlit as st
        if any(k in st.secrets for k in ('EARTHDATA_TOKEN',)):
            return 'secrets'
    except Exception:  # noqa: BLE001 - no secrets file configured
        pass
    return None


def server_token():
    """The server-side token (environment, local owner-only file, or Streamlit secrets); never shown or stored."""
    try:
        from scripts.check_earthdata_access import available_token
        token = available_token()
    except (ImportError, ValueError, OSError):
        token = None
    if token:
        return token
    try:
        import streamlit as st
        value = st.secrets.get('EARTHDATA_TOKEN')
        return str(value).strip() or None if value else None
    except Exception:  # noqa: BLE001
        return None
