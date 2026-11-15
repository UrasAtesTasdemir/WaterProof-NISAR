"""Small-window reader for OPERA DSWx GeoTIFFs at PO.DAAC (reference water products for flood validation).

Separate from the NISAR reader (src/nisar_data.py, scripts/check_earthdata_access.py), which is unchanged.
Safeguards (agreed 2026-11-15):
- Redirects are followed manually (at most MAX_REDIRECTS). The Earthdata token is sent ONLY to the exact host
  archive.podaac.earthdata.nasa.gov, and to urs.earthdata.nasa.gov only when a login redirect actually points there.
  It is never sent to S3 or the CDN. S3 is allowed only by an exact pattern: https://<bucket>.s3.<region>.amazonaws.com;
  the PO.DAAC CloudFront CDN only as the exact host CDN_HOST (approved by the owner on 2026-11-15; PO.DAAC answers 303
  to it). Both are treated alike: no token, signed query never logged or stored.
  Every other scheme, host, port or user-info is rejected before any request.
- Presigned S3 URLs (signatures in the query) are never logged, stored or put in exceptions; diagnostics carry
  host + path only (`safe_url`).
- Before any window is read the file must answer a Range request with 206 + Content-Range and start with a TIFF
  header, and rasterio must report it as tiled. Otherwise ReferenceAccessError; whole-file downloads never happen.
- Per-window and total byte caps (ByteBudget) are enforced on every range request; bytes read are reported.
"""
from contextlib import contextmanager
import io
import re
from urllib.parse import urlsplit, urljoin

import certifi
import numpy as np

ARCHIVE_HOST = 'archive.podaac.earthdata.nasa.gov'
URS_HOST = 'urs.earthdata.nasa.gov'
CDN_HOST = 'deotb6e7tfubr.cloudfront.net'
S3_HOST = re.compile(r'^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]\.s3\.[a-z]{2}(-gov)?-[a-z]+-\d\.amazonaws\.com$')
MAX_REDIRECTS = 6
PER_WINDOW_CAP = 8 * 1024 * 1024
TOTAL_CAP = 256 * 1024 * 1024
MAX_REQUEST = 4 * 1024 * 1024
BLOCK = 64 * 1024                 # range-request granularity (cached per window)
TIFF_MAGIC = (b'II*\x00', b'MM\x00*', b'II+\x00', b'MM\x00+')


class ReferenceAccessError(Exception):
    """Fixed, non-sensitive message (never a token or a signed query)."""


def safe_url(url):
    parts = urlsplit(url)
    return f'{parts.scheme}://{parts.hostname or ""}{parts.path}'


def classify_host(url):
    """'archive' | 'urs' | 's3'; raises for anything else (http, other domains, ports, user-info)."""
    parts = urlsplit(url)
    host = (parts.hostname or '').lower()
    if parts.scheme != 'https' or parts.port not in (None, 443) or parts.username or parts.password:
        raise ReferenceAccessError(f'Rejected non-HTTPS or unusual URL: {safe_url(url)}')
    if host == ARCHIVE_HOST:
        return 'archive'
    if host == URS_HOST:
        return 'urs'
    if S3_HOST.fullmatch(host):
        return 's3'
    if host == CDN_HOST:
        return 'cdn'
    raise ReferenceAccessError(f'Rejected host not on the PO.DAAC allowlist: {host or "(none)"}')


class ByteBudget:
    def __init__(self, total=TOTAL_CAP):
        self.total_cap = total; self.total = 0

    def window(self, cap=PER_WINDOW_CAP):
        return _WindowBudget(self, cap)


class _WindowBudget:
    def __init__(self, parent, cap):
        self.parent = parent; self.cap = cap; self.read = 0

    def charge(self, n):
        if self.read + n > self.cap:
            raise ReferenceAccessError(f'Per-window byte cap reached ({self.cap} bytes); nothing more is read.')
        if self.parent.total + n > self.parent.total_cap:
            raise ReferenceAccessError(f'Total byte cap reached ({self.parent.total_cap} bytes); nothing more is read.')
        self.read += n; self.parent.total += n


def resolve(url, token, session=None, log=None, budget=None):
    """Follow redirects manually to a range-readable TIFF. Returns (final_url, size). The final URL stays in memory."""
    import requests
    session = session or requests.Session()
    log = log if log is not None else []
    came_from_redirect = False
    for hop in range(MAX_REDIRECTS + 1):
        kind = classify_host(url)
        headers = {'Range': 'bytes=0-15', 'Accept-Encoding': 'identity'}
        if token and (kind == 'archive' or (kind == 'urs' and came_from_redirect)):
            headers['Authorization'] = 'Bearer ' + token
        try:
            response = session.get(url, headers=headers, allow_redirects=False, stream=True, timeout=(15, 60),
                                   verify=certifi.where())
        except Exception as exc:  # noqa: BLE001
            raise ReferenceAccessError(f'Request to {safe_url(url)} failed ({type(exc).__name__}).') from None
        log.append(dict(host=urlsplit(url).hostname, path=urlsplit(url).path, status=response.status_code,
                        token_sent='Authorization' in headers))
        try:
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get('Location')
                if not location:
                    raise ReferenceAccessError('Redirect without a Location header.')
                url = urljoin(url, location); came_from_redirect = True
                continue
            if response.status_code != 206 or not response.headers.get('Content-Range', '').startswith('bytes 0-15/'):
                raise ReferenceAccessError(f'{safe_url(url)} is not range-readable (HTTP {response.status_code}, '
                                           f'Accept-Ranges={response.headers.get("Accept-Ranges")}); refusing to download it whole.')
            head = response.raw.read(16)
            if budget is not None:
                budget.charge(len(head))
            if head[:4] not in TIFF_MAGIC:
                raise ReferenceAccessError(f'{safe_url(url)} is not a GeoTIFF.')
            size = int(response.headers['Content-Range'].split('/')[-1])
            return url, size
        finally:
            response.close()
    raise ReferenceAccessError(f'Redirect limit ({MAX_REDIRECTS}) reached.')


class RangeFile(io.RawIOBase):
    """Read-only file object over HTTPS Range requests (no credentials), charged to a window budget."""
    def __init__(self, url, size, budget, session):
        if classify_host(url) not in ('s3', 'cdn'):
            raise ReferenceAccessError('Range reads only from the signed S3 or CDN location (no credentials).')
        self.url, self.size, self.budget, self.session, self.pos = url, size, budget, session, 0
        self.blocks = {}                                         # in-memory block cache (this window only)

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = {0: offset, 1: self.pos + offset, 2: self.size + offset}[whence]
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = max(0, min(n, self.size - self.pos))
        if n == 0:
            return b''
        if n > MAX_REQUEST:
            raise ReferenceAccessError(f'Single read of {n} bytes refused (max {MAX_REQUEST}); whole-file reads are disabled.')
        first, last = self.pos // BLOCK, (self.pos + n - 1) // BLOCK
        data = b''.join(self._block(i) for i in range(first, last + 1))
        start = self.pos - first * BLOCK
        out = data[start:start + n]
        self.pos += len(out)
        return out

    def _block(self, index):
        """One BLOCK-sized range, fetched once and kept in memory; charged to the window budget."""
        if index in self.blocks:
            return self.blocks[index]
        start = index * BLOCK; end = min(self.size, start + BLOCK) - 1
        self.budget.charge(end - start + 1)
        try:
            response = self.session.get(self.url, headers={'Range': f'bytes={start}-{end}', 'Accept-Encoding': 'identity'},
                                        allow_redirects=False, timeout=(15, 60), verify=certifi.where())
        except Exception as exc:  # noqa: BLE001
            raise ReferenceAccessError(f'Range read from {safe_url(self.url)} failed ({type(exc).__name__}).') from None
        if response.status_code != 206:
            raise ReferenceAccessError(f'Range read from {safe_url(self.url)} returned HTTP {response.status_code}.')
        self.blocks[index] = response.content[:end - start + 1]
        return self.blocks[index]

    def readinto(self, buffer):
        data = self.read(len(buffer)); buffer[:len(data)] = data
        return len(data)


def read_window(url, token, polygon_wgs84, budget, session=None, log=None, per_window_cap=PER_WINDOW_CAP):
    """WTR (band 1) inside the polygon's bounds, plus grid, file metadata and bytes read. Never the whole file."""
    import requests
    import rasterio
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds
    session = session or requests.Session()
    window_budget = budget.window(per_window_cap)
    final_url, size = resolve(url, token, session, log, window_budget)
    name = '/vsipythonfilelike/' + urlsplit(url).path.rsplit('/', 1)[-1]

    def opener(path, mode='rb'):
        if not path.endswith(name.rsplit('/', 1)[-1]):
            raise FileNotFoundError(path)
        return RangeFile(final_url, size, window_budget, session)

    try:
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', CPL_DEBUG='OFF'), \
                rasterio.open(name.rsplit('/', 1)[-1], opener=opener) as src:
            if not src.profile.get('tiled') and src.block_shapes[0][0] == 1:
                raise ReferenceAccessError(f'{safe_url(url)} is not tiled; refusing to read it.')
            bounds = transform_bounds('EPSG:4326', src.crs, *polygon_wgs84.bounds, densify_pts=21)
            window = from_bounds(*bounds, transform=src.transform).round_offsets().round_lengths()
            data = src.read(1, window=window, boundless=True, fill_value=src.nodata if src.nodata is not None else 255)
            meta = dict(crs=str(src.crs), transform=list(src.window_transform(window))[:6], nodata=src.nodata,
                        tags=src.tags(), band_tags=src.tags(1), description=src.descriptions[0],
                        colormap=_colormap(src), block_shape=list(src.block_shapes[0]), tiled=bool(src.profile.get('tiled')),
                        file_size=size, window=[int(window.row_off), int(window.col_off), int(window.height), int(window.width)],
                        outside_file=bool(window.row_off < 0 or window.col_off < 0 or window.row_off + window.height > src.height
                                          or window.col_off + window.width > src.width))
    except ReferenceAccessError:
        raise
    except Exception as exc:  # noqa: BLE001 - no URL query or token can leave this function
        raise ReferenceAccessError(f'Window read from {safe_url(url)} failed ({type(exc).__name__}).') from None
    return dict(array=np.asarray(data), bytes_read=window_budget.read, source=safe_url(url), **meta)


def _colormap(src):
    try:
        return {int(k): list(v) for k, v in src.colormap(1).items()}
    except ValueError:
        return None
