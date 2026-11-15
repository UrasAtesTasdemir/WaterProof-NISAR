"""Milestone 2: real HH power subsets and diagnostic plots; no classification."""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))
logging.disable(logging.CRITICAL)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import Affine, array_bounds
from rasterio.warp import transform_bounds, transform_geom
from shapely import wkt
from shapely.geometry import mapping

from scripts.check_earthdata_access import available_token, AccessCheckError
from src.nisar_data import GROUP, RadarDataError, open_frequency_a

OUTPUT = ROOT / "data" / "subsets"
REPORT = ROOT / "data" / "nisar_visualization_report.json"


def positive_power_db(power):
    """Exclude invalid/nonpositive power before log10 (never clip to epsilon)."""
    valid = np.isfinite(power) & (power > 0)
    clean = np.where(valid, power, np.nan).astype("float32")
    db = np.full(clean.shape, np.nan, dtype="float32")
    db[valid] = 10 * np.log10(clean[valid])
    return clean, db


def read_subset(dataset, aoi, layer_name="HHHH"):
    """Read one explicit real power term; existing callers retain HH behavior."""
    if layer_name not in {"HHHH", "HVHV"}:
        raise RadarDataError("Only explicit HH or HV power terms are supported.")
    required = {layer_name, "xCoordinates", "yCoordinates", "projection"}
    if not required.issubset(dataset.variables):
        raise RadarDataError("Requested power term, coordinate or projection metadata is missing.")
    layer = dataset[layer_name]
    if layer.ndim != 2 or not np.issubdtype(layer.dtype, np.floating):
        raise RadarDataError("Requested layer is not a two-dimensional real power term.")
    if max(dataset.xCoordinates.size, dataset.yCoordinates.size) > 200_000:
        raise RadarDataError("Coordinate inspection exceeds the safety limit.")
    x = dataset.xCoordinates.values
    y = dataset.yCoordinates.values
    dx = float(dataset.xCoordinateSpacing.values)
    dy = float(dataset.yCoordinateSpacing.values)
    epsg = int(dataset.projection.attrs["epsg_code"])
    crs = rasterio.crs.CRS.from_epsg(epsg)
    if dx <= 0 or dy >= 0 or not np.allclose(np.diff(x), dx) or not np.allclose(np.diff(y), dy):
        raise RadarDataError("Expected a regular eastward, north-up radar grid.")
    bounds = transform_bounds("EPSG:4326", crs, *aoi.bounds, densify_pts=21)
    ix = np.flatnonzero((x + dx / 2 >= bounds[0]) & (x - dx / 2 <= bounds[2]))
    iy = np.flatnonzero((y + abs(dy) / 2 >= bounds[1]) & (y - abs(dy) / 2 <= bounds[3]))
    if not ix.size or not iy.size:
        raise RadarDataError("AOI does not intersect the product coordinate grid.")
    if ix.size * iy.size > 4_000_000:
        raise RadarDataError("Requested subset exceeds four million pixels.")
    xdim, ydim = dataset.xCoordinates.dims[0], dataset.yCoordinates.dims[0]
    # Backend indexing is lazy: only this small window is loaded, not layer.values.
    window = layer.isel({xdim: slice(ix[0], ix[-1] + 1),
                         ydim: slice(iy[0], iy[-1] + 1)}).transpose(ydim, xdim)
    print(f"  Metadata inspected: full grid {layer.shape}; loading window {window.shape}, EPSG:{epsg}", flush=True)
    power = window.load().values
    transform = Affine(dx, 0, float(x[ix[0]] - dx / 2),
                       0, dy, float(y[iy[0]] - dy / 2))
    projected_aoi = transform_geom("EPSG:4326", crs, mapping(aoi))
    inside = geometry_mask([projected_aoi], power.shape, transform, invert=True)
    inside_count = int(inside.sum())
    if not inside_count:
        raise RadarDataError("No pixel centers fall inside the AOI polygon.")
    clean, db = positive_power_db(np.where(inside, power, np.nan))
    count = int(np.isfinite(clean).sum())
    if not count:
        raise RadarDataError("AOI contains no finite positive requested radar power.")
    metadata = {
        "hdf5_group": GROUP, "layer": layer_name, "full_grid_shape": list(layer.shape),
        "subset_shape": list(clean.shape), "epsg": epsg,
        "pixel_spacing_m": [dx, dy], "transform": list(transform)[:6],
        "pixel_center_window": {"row_start": int(iy[0]), "row_stop_exclusive": int(iy[-1] + 1),
                                "column_start": int(ix[0]), "column_stop_exclusive": int(ix[-1] + 1)},
        "aoi_pixel_centers": inside_count, "finite_positive_pixels": count,
        "invalid_or_nonpositive_pixels_inside_aoi": inside_count - count,
        "power_min": float(np.nanmin(clean)), "power_max": float(np.nanmax(clean)),
        "db_min": float(np.nanmin(db)), "db_max": float(np.nanmax(db)),
        "power_units": str(layer.attrs.get("units", "1")),
        "db_formula": "10 * log10(power), finite positive values only",
        "aoi_mask_rule": "pixel center inside transformed AOI; outside and invalid values are NaN",
    }
    return clean, db, crs, transform, metadata


def save_geotiff(path, power, db, crs, transform, item):
    with rasterio.open(path, "w", driver="GTiff", height=power.shape[0],
                       width=power.shape[1], count=2, dtype="float32", crs=crs,
                       transform=transform, nodata=float("nan"), compress="deflate") as dst:
        dst.write(power, 1)
        dst.write(db, 2)
        dst.set_band_description(1, "HHHH_gamma0_power")
        dst.set_band_description(2, "HHHH_gamma0_dB")
        dst.update_tags(product_id=item["product_id"], acquisition_utc=item["start_time_utc"],
                        source_layer=GROUP + "/HHHH")
    # Read back the actual export and verify georeferencing and both bands.
    with rasterio.open(path) as check:
        if check.crs != crs or check.transform != transform or not all(
            np.array_equal(check.read(band), expected, equal_nan=True)
            for band, expected in ((1, power), (2, db))
        ):
            raise RadarDataError("GeoTIFF read-back verification failed.")


def main():
    report = {"started_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "started", "observations": [], "full_products_downloaded": False}
    try:
        manifest = json.loads((ROOT / "data" / "nisar_manifest.json").read_text())
        if len(manifest["observations"]) != 2:
            raise RadarDataError("Expected two manifest observations.")
        token = available_token()
        if not token:
            raise RadarDataError("No saved or environment Earthdata token is available.")
        aoi = wkt.loads(manifest["aoi_wkt"])
        report["aoi_wkt"] = manifest["aoi_wkt"]
        OUTPUT.mkdir(exist_ok=True)
        panels = []
        for item in manifest["observations"]:
            date = item["start_time_utc"][:10]
            print(f"Reading real NISAR HHHH: {date}", flush=True)
            with open_frequency_a(item, token) as (dataset, stats):
                power, db, crs, transform, metadata = read_subset(dataset, aoi)
            metadata.update({"product_id": item["product_id"],
                             "acquisition_utc": item["start_time_utc"],
                             "source_catalog_url": item["download_url"], **stats})
            path = OUTPUT / f"nisar_hhhh_{date}.tif"
            save_geotiff(path, power, db, crs, transform, item)
            metadata["geotiff"] = str(path.relative_to(ROOT))
            metadata["geotiff_readback_verified"] = True
            (path.with_suffix(".json")).write_text(json.dumps(metadata, indent=2) + "\n")
            report["observations"].append(metadata)
            panels.append((date, db, transform))
            print(f"  Verified {metadata['finite_positive_pixels']} positive pixels; {stats['range_bytes_read'] / 2**20:.1f} MiB read over HTTPS", flush=True)
        values = np.concatenate([db[np.isfinite(db)] for _, db, _ in panels])
        vmin, vmax = np.percentile(values, [2, 98]).tolist()
        if vmin == vmax:
            vmax = vmin + 1
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained", sharex=True, sharey=True)
        cmap = plt.get_cmap("gray").copy()
        cmap.set_bad("#d8e1e8")
        for ax, (date, db, transform) in zip(axes, panels):
            west, south, east, north = array_bounds(*db.shape, transform)
            im = ax.imshow(db, extent=(west, east, south, north), origin="upper",
                           cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")
            ax.set_title(date + " UTC — HH (HHHH)")
            ax.set_xlabel("Easting (m)")
            ax.ticklabel_format(style="plain", useOffset=False)
        axes[0].set_ylabel("Northing (m)")
        fig.suptitle("FloodPulse NISAR | Louisiana AOI | Real GCOV radar observations")
        fig.colorbar(im, ax=axes, label="Gamma-0 backscatter (dB)", shrink=0.8)
        image_path = ROOT / "data" / "nisar_hhhh_comparison.png"
        fig.savefig(image_path, dpi=170)
        plt.close(fig)
        report.update(status="success", image=str(image_path.relative_to(ROOT)),
                      color_scale_db=[vmin, vmax], color_scale_rule="Shared pooled 2nd–98th percentiles; display only, no classification",
                      completed_at_utc=datetime.now(timezone.utc).isoformat())
        print("Both real observations visualized; GeoTIFF exports verified.", flush=True)
        return 0
    except (RadarDataError, AccessCheckError) as exc:
        report.update(status="blocked", detail=str(exc))
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        report.update(status="error", error_type=type(exc).__name__)
        print(f"Pipeline stopped ({type(exc).__name__}); secret-bearing exception text suppressed.", file=sys.stderr)
        return 1
    finally:
        REPORT.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
