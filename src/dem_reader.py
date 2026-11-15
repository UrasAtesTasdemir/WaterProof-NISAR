"""Small-window reader for the public Copernicus DEM GLO-30 COGs (flood validation Tier A, protocol section 5).

Same safeguards as src/podaac_reader.py, but no credentials exist at all: HTTPS only, the exact host DEM_HOST, manual
redirects (at most MAX_REDIRECTS, every hop must be DEM_HOST), a range-readable TIFF check, per-window/total byte caps,
certifi TLS. No Authorization header is ever sent.
"""
from urllib.parse import urlsplit, urljoin

import certifi
import numpy as np

from src.podaac_reader import (ByteBudget, ReferenceAccessError, RangeFile, safe_url, MAX_REDIRECTS, PER_WINDOW_CAP,
                               TIFF_MAGIC)

DEM_HOST = 'copernicus-dem-30m.s3.amazonaws.com'


class DemAccessError(ReferenceAccessError):
    pass


def check_url(url):
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.port not in (None, 443) or parts.username or parts.password
            or (parts.hostname or '').lower() != DEM_HOST):
        raise DemAccessError(f'Rejected URL (DEM allowlist is https://{DEM_HOST} only): {safe_url(url)}')


def tile_url(lat, lon):
    ns = f"{'N' if lat >= 0 else 'S'}{abs(int(np.floor(lat))):02d}"
    ew = f"{'E' if lon >= 0 else 'W'}{abs(int(np.floor(lon))):03d}"
    name = f'Copernicus_DSM_COG_10_{ns}_00_{ew}_00_DEM'
    return f'https://{DEM_HOST}/{name}/{name}.tif'


def resolve(url, session=None, log=None, budget=None):
    import requests
    session = session or requests.Session(); log = log if log is not None else []
    for _ in range(MAX_REDIRECTS + 1):
        check_url(url)
        headers = {'Range': 'bytes=0-15', 'Accept-Encoding': 'identity'}       # never an Authorization header
        try:
            response = session.get(url, headers=headers, allow_redirects=False, stream=True, timeout=(15, 60),
                                   verify=certifi.where())
        except Exception as exc:  # noqa: BLE001
            raise DemAccessError(f'Request to {safe_url(url)} failed ({type(exc).__name__}).') from None
        log.append(dict(host=urlsplit(url).hostname, path=urlsplit(url).path, status=response.status_code))
        try:
            if response.status_code in (301, 302, 303, 307, 308):
                if not response.headers.get('Location'):
                    raise DemAccessError('Redirect without a Location header.')
                url = urljoin(url, response.headers['Location']); continue
            if response.status_code != 206 or not response.headers.get('Content-Range', '').startswith('bytes 0-15/'):
                raise DemAccessError(f'{safe_url(url)} is not range-readable (HTTP {response.status_code}); refusing to download it whole.')
            head = response.raw.read(16)
            if budget is not None:
                budget.charge(len(head))
            if head[:4] not in TIFF_MAGIC:
                raise DemAccessError(f'{safe_url(url)} is not a GeoTIFF.')
            return url, int(response.headers['Content-Range'].split('/')[-1])
        finally:
            response.close()
    raise DemAccessError(f'Redirect limit ({MAX_REDIRECTS}) reached.')


class DemRangeFile(RangeFile):
    def __init__(self, url, size, budget, session):          # same block cache and caps, DEM host only
        check_url(url)
        self.url, self.size, self.budget, self.session, self.pos, self.blocks = url, size, budget, session, 0, {}


def read_dem_window(lat, lon, polygon_wgs84, budget, session=None, log=None, margin_deg=0.01, per_window_cap=PER_WINDOW_CAP):
    """DEM heights (m) for the polygon bounds plus a small margin, with its grid. One 1x1 degree tile only."""
    import requests
    import rasterio
    from rasterio.windows import from_bounds
    session = session or requests.Session()
    url = tile_url(lat, lon)
    w = budget.window(per_window_cap)
    final, size = resolve(url, session, log, w)
    name = url.rsplit('/', 1)[-1]

    def opener(path, mode='rb'):
        if not path.endswith(name):
            raise FileNotFoundError(path)
        return DemRangeFile(final, size, w, session)

    west, south, east, north = polygon_wgs84.bounds
    try:
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', CPL_DEBUG='OFF'), rasterio.open(name, opener=opener) as src:
            if src.block_shapes[0][0] == 1:
                raise DemAccessError(f'{safe_url(url)} is not tiled; refusing to read it.')
            window = from_bounds(west - margin_deg, south - margin_deg, east + margin_deg, north + margin_deg,
                                 transform=src.transform).round_offsets().round_lengths()
            data = src.read(1, window=window, boundless=True, fill_value=np.nan).astype(float)
            out = dict(height=data, crs=str(src.crs), transform=list(src.window_transform(window))[:6], nodata=src.nodata)
    except ReferenceAccessError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise DemAccessError(f'DEM window read from {safe_url(url)} failed ({type(exc).__name__}).') from None
    if out['nodata'] is not None:
        out['height'][out['height'] == out['nodata']] = np.nan
    return dict(out, bytes_read=w.read, source=safe_url(url))


def slope_degrees(height, transform):
    """Slope on the DEM's own geographic grid: central differences with metre spacing at each row's latitude."""
    a, _, c, _, e, f = transform
    rows = np.arange(height.shape[0])
    lat = np.radians(f + (rows + 0.5) * e)
    dy = abs(e) * 111_320.0
    dx = np.abs(a) * 111_320.0 * np.cos(lat)
    gy, gx = np.gradient(height)
    slope = np.degrees(np.arctan(np.hypot(gx / dx[:, None], gy / dy)))
    return slope
