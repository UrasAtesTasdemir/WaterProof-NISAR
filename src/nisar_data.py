"""Bounded, lazy HTTPS HDF5 access following the ASF NISAR Cookbook."""

from contextlib import contextmanager
from urllib.parse import urlparse
import ssl

import aiohttp
import certifi
import fsspec
from fsspec.asyn import sync
import xarray as xr

from scripts.check_earthdata_access import open_product_range, PRODUCT_HOST

GROUP = "/science/LSAR/GCOV/grids/frequencyA"
MAX_TRANSFER = 256 * 1024 * 1024


class RadarDataError(Exception):
    """A non-sensitive pipeline diagnostic."""


@contextmanager
def open_frequency_a(observation, token, *, inspect_file=None):
    entry = {}
    with open_product_range(observation["download_url"], token, entry) as response:
        if response.status_code != 206:
            raise RadarDataError(f"Product range access returned HTTP {response.status_code}.")
        content_range = response.headers.get("Content-Range", "")
        if not content_range.startswith("bytes 0-7/"):
            raise RadarDataError("Product did not return the requested byte range.")
        size = int(content_range.split("/")[-1])
        if response.raw.read(8) != b"\x89HDF\r\n\x1a\n":
            raise RadarDataError("Remote product is not an HDF5 file.")
        # This signed URL stays only in memory, never in output metadata.
        url = response.url
    headers = {"Accept-Encoding": "identity"}
    if urlparse(url).hostname == PRODUCT_HOST:
        headers["Authorization"] = "Bearer " + token
    fs = fsspec.filesystem(
        "http", headers=headers, allow_redirects=False, skip_instance_cache=True,
        ssl=ssl.create_default_context(cafile=certifi.where()),
        client_kwargs={"timeout": aiohttp.ClientTimeout(total=90)},
    )
    stats = {"remote_product_bytes": size, "range_bytes_read": 8,
             "cache_limit_bytes": 16 * 1024 * 1024}
    try:
        with fs.open(url, "rb", size=size, block_size=1024 * 1024,
                     cache_type="blockcache", cache_options={"maxblocks": 16}) as remote:
            fetch = remote.cache.fetcher

            def bounded_fetch(start, end):
                if end - start > 1024 * 1024 or stats["range_bytes_read"] + end - start > MAX_TRANSFER:
                    raise RadarDataError("Per-product 256 MiB transfer limit reached; full downloads are disabled.")
                data = fetch(start, end)
                stats["range_bytes_read"] += len(data)
                return data

            remote.cache.fetcher = bounded_fetch
            # Optional bounded read-only metadata inspection, on the same file
            # and transfer budget. Existing radar callers keep their behavior.
            if inspect_file is not None:
                inspect_file(remote)
            # chunks=None uses lazy backend indexing, without a Dask dependency.
            # Only .isel(...).load() on the small window loads radar arrays.
            with xr.open_dataset(remote, engine="h5netcdf", group=GROUP,
                                 phony_dims="access", chunks=None,
                                 decode_timedelta=False) as dataset:
                yield dataset, stats
    finally:
        if fs._session is not None:
            sync(fs.loop, fs._session.close)
