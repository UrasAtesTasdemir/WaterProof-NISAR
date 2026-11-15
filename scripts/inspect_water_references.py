"""Inspect small optical-reference windows; no NISAR redownloads or accuracy claims."""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import ssl
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.disable(logging.CRITICAL)
import aiohttp
import certifi
import fsspec
from fsspec.asyn import sync
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import transform_bounds, transform_geom
from rasterio.windows import Window, from_bounds
import requests
from shapely.geometry import mapping
from shapely import wkt
from scripts.check_earthdata_access import available_token

OUT = ROOT / "data/scientific_quality_check"


def inspect(entry, token, aoi):
    result = {"product_id": entry["title"], "acquisition_utc": entry.get("time_start"),
              "tile_cloud_cover_percent": entry.get("cloud_cover"), "tile_cloud_cover_is_not_aoi_cloud_fraction": True}
    fs = None
    try:
        url = next(l["href"] for l in entry["links"] if l.get("href", "").startswith("https://archive.podaac.earthdata.nasa.gov/") and l["href"].endswith("_B01_WTR.tif"))
        result["public_catalog_url"] = url
        # requests strips Authorization on cross-host redirects. The signed URL
        # is used only in memory, never persisted or printed.
        with requests.get(url, headers={"Authorization": "Bearer " + token, "Range": "bytes=0-7", "Accept-Encoding": "identity"},
                          stream=True, allow_redirects=True, timeout=(15, 45)) as response:
            result["http_status"] = response.status_code
            if response.status_code != 206 or not response.headers.get("Content-Range", "").startswith("bytes 0-7/"):
                result["status"] = "reference_range_access_failed_no_body_read"
                return result
            size = int(response.headers["Content-Range"].split("/")[-1])
            final_url = response.url
        headers = {"Accept-Encoding": "identity"}
        if urlparse(final_url).hostname == "archive.podaac.earthdata.nasa.gov":
            headers["Authorization"] = "Bearer " + token
        fs = fsspec.filesystem("http", skip_instance_cache=True, allow_redirects=False, headers=headers,
                              ssl=ssl.create_default_context(cafile=certifi.where()),
                              client_kwargs={"timeout": aiohttp.ClientTimeout(total=60)})
        transfer = [0]

        def opener(path, mode="rb"):
            if not path.endswith("reference.tif"):
                raise FileNotFoundError("No ancillary files are exposed.")
            f = fs.open(final_url, "rb", size=size, block_size=65536,
                        cache_type="blockcache", cache_options={"maxblocks": 32})
            fetch = f.cache.fetcher

            def bounded(start, end):
                if transfer[0] + end - start > 16 * 2**20:
                    raise ValueError("Optical reference 16 MiB transfer budget reached.")
                data = fetch(start, end); transfer[0] += len(data)
                return data

            f.cache.fetcher = bounded
            return f

        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
            with rasterio.open("reference.tif", opener=opener) as src:
                bounds = transform_bounds("EPSG:4326", src.crs, *aoi.bounds, densify_pts=21)
                win = from_bounds(*bounds, src.transform)
                win = Window(int(np.floor(win.col_off)), int(np.floor(win.row_off)),
                             int(np.ceil(win.col_off + win.width) - np.floor(win.col_off)),
                             int(np.ceil(win.row_off + win.height) - np.floor(win.row_off)))
                if win.width * win.height > 100_000:
                    raise ValueError("Optical reference window too large.")
                values = src.read(1, window=win)
                transform = src.window_transform(win)
                mask = geometry_mask([transform_geom("EPSG:4326", src.crs, mapping(aoi))], values.shape, transform, invert=True)
                crs = src.crs
        counts = {str(int(v)): int(n) for v, n in zip(*np.unique(values[mask], return_counts=True))}
        path = OUT / (entry["title"] + "_aoi_WTR.tif")
        with rasterio.open(path, "w", driver="GTiff", width=values.shape[1], height=values.shape[0], count=1,
                           dtype=values.dtype, transform=transform, crs=crs, nodata=255, compress="deflate") as dst:
            dst.write(np.where(mask, values, 255), 1)
            dst.update_tags(source_product=entry["title"], source_url=url, interpretation="Independent optical product; reference suitability check only")
        result.update(status="aoi_inspected", aoi_class_counts=counts, aoi_pixel_centers=int(mask.sum()),
                      range_bytes_read=transfer[0], subset_path=str(path.relative_to(ROOT)),
                      usable_water_or_nonwater_pixels=int(np.isin(values[mask], [0, 1, 2]).sum()),
                      class_codes={"0": "not water", "1": "open water", "2": "partial surface water", "252": "snow/ice", "253": "cloud/cloud shadow", "254": "ocean masked", "255": "no data"})
    except Exception as exc:
        result.update(status="reference_inspection_error", error_type=type(exc).__name__)
    finally:
        if fs is not None and fs._session is not None:
            sync(fs.loop, fs._session.close)
    return result


def main():
    aoi = wkt.loads(json.loads((ROOT / "data/nisar_manifest.json").read_text())["aoi_wkt"])
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "collection": "OPERA_L3_DSWX-HLS_V1", "observations": [],
              "interpretation": "Independent optical water product, not ground truth. Cloud/shadow is unknown, not water or nonwater. Historical NHD is not dated flood evidence."}
    token = available_token()
    for date in ("2026-06-21", "2026-07-03"):
        data = json.loads((OUT / f"dswx_granules_{date}.json").read_text())
        entries = data["response"]["feed"]["entry"]
        same_day = [e for e in entries if e.get("time_start", "").startswith(date)]
        nearby = [e for e in entries if not e.get("time_start", "").startswith(date)]
        # Same-day first; inspect one nearby lowest-tile-cloud candidate as a
        # suitability check, never selecting a threshold by apparent agreement.
        selected = same_day + sorted(nearby, key=lambda e: float(e.get("cloud_cover", 100)))[:1]
        for entry in selected:
            result = inspect(entry, token, aoi) if token else {"status": "missing_local_token", "product_id": entry["title"]}
            result["nisar_target_date"] = date
            result["same_day"] = entry in same_day
            report["observations"].append(result)
            print(json.dumps(result), flush=True)
    (OUT / "independent_reference_check.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
