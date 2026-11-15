"""Offline Milestone 3 processing of the two cached real NISAR subsets."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
import numpy as np
import rasterio
from rasterio.transform import array_bounds

from src.water_change import (CLASS_NAMES, align_power, class_areas, classify,
                              mask_aware_mean, pixel_area_km2, power_to_db)

LIMITATIONS = [
    "Exploratory water candidates, not confirmed water or confirmed flooding.",
    "-16 dB and the optional 3 dB change gate are test settings, not universal or validated thresholds.",
    "Backscatter changes alone do not prove flooding. No ground truth or accuracy metrics are available.",
    "Wind, vegetation, soil moisture, geometry, radar shadow and smooth artificial surfaces can affect interpretation.",
    "A 3x3 linear-power boxcar reduces speckle but blurs boundaries; edge pixels have fewer valid neighbors.",
    "Areas are projected-grid pixel-count estimates within the common valid AOI, not geodesic surveyed extents.",
    "Threshold crossings below the change gate are assigned Other valid surface, not verified stable land.",
]


def load_cached(item, previous):
    date = item["start_time_utc"][:10]
    path = ROOT / "data" / "subsets" / f"nisar_hhhh_{date}.tif"
    sidecar = json.loads(path.with_suffix(".json").read_text())
    old = next(p for p in previous["observations"] if p["product_id"] == item["product_id"])
    for metadata in (sidecar, old):
        if (metadata["product_id"] != item["product_id"] or metadata["acquisition_utc"] != item["start_time_utc"]
                or metadata["layer"] != "HHHH" or metadata["hdf5_group"] != "/science/LSAR/GCOV/grids/frequencyA"):
            raise ValueError("Cached source metadata does not match the real NISAR manifest.")
    if item["product_type"] != "L2_GCOV" or "_L2_PR_GCOV_" not in item["product_id"]:
        raise ValueError("Manifest is not the expected NISAR GCOV product.")
    with rasterio.open(path) as ds:
        tags = ds.tags()
        if (tags.get("product_id") != item["product_id"] or tags.get("acquisition_utc") != item["start_time_utc"]
                or tags.get("source_layer") != "/science/LSAR/GCOV/grids/frequencyA/HHHH"
                or ds.descriptions != ("HHHH_gamma0_power", "HHHH_gamma0_dB")):
            raise ValueError("Cached raster tags or bands fail source verification.")
        power, cached_db = ds.read().astype(float)
        valid = (ds.read_masks(1) > 0) & np.isfinite(power) & (power > 0)
        expected_db = power_to_db(np.where(valid, power, np.nan))
        if not np.array_equal(valid, np.isfinite(cached_db)) or not np.allclose(
                expected_db[valid], cached_db[valid], atol=1e-5, rtol=0):
            raise ValueError("Cached dB band is inconsistent with 10*log10(positive linear power).")
        if not valid.any():
            raise ValueError("Cached raster has no positive valid power.")
        grid = {"crs": ds.crs, "transform": ds.transform, "shape": ds.shape}
        if (ds.crs.to_epsg() != sidecar["epsg"] or list(ds.shape) != sidecar["subset_shape"]
                or not np.allclose(list(ds.transform)[:6], sidecar["transform"], rtol=0, atol=1e-8)
                or int(valid.sum()) != sidecar["finite_positive_pixels"]
                or not np.isclose(power[valid].min(), sidecar["power_min"])
                or not np.isclose(power[valid].max(), sidecar["power_max"])):
            raise ValueError("Cached raster disagrees with the Milestone 2 metadata.")
    verification = {"product_id": item["product_id"], "date_utc": item["start_time_utc"],
                    "path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "provenance_verified_against": ["manifest", "Milestone 2 report", "JSON sidecar", "GeoTIFF tags"],
                    "db_max_absolute_error": float(np.max(np.abs(expected_db[valid] - cached_db[valid]))),
                    "valid_pixels": int(valid.sum()), "crs": str(grid["crs"]),
                    "shape": list(grid["shape"]), "resolution": list(ds.res),
                    "transform": list(grid["transform"])[:6]}
    return power, valid, grid, verification


def save_raster(path, arrays, descriptions, grid, tags, categorical=False):
    dtype = "uint8" if categorical else "float32"
    with rasterio.open(path, "w", driver="GTiff", width=grid["shape"][1], height=grid["shape"][0],
                       count=len(arrays), dtype=dtype, crs=grid["crs"], transform=grid["transform"],
                       nodata=0 if categorical else np.nan, compress="deflate") as ds:
        for index, (array, description) in enumerate(zip(arrays, descriptions), 1):
            ds.write(array.astype(dtype), index)
            ds.set_band_description(index, description)
        ds.update_tags(**tags)
    with rasterio.open(path) as ds:
        if ds.crs != grid["crs"] or ds.transform != grid["transform"]:
            raise ValueError("Output georeferencing read-back failed.")
        for index, array in enumerate(arrays, 1):
            if not np.array_equal(ds.read(index), array.astype(dtype), equal_nan=True):
                raise ValueError("Output raster values read-back failed.")


def draw_maps(out, before, after, delta, classes, grid, dates, settings):
    if grid["transform"].b or grid["transform"].d:
        raise ValueError("Map rendering requires a north-up reference grid.")
    west, south, east, north = array_bounds(*grid["shape"], grid["transform"])
    extent = (west, east, south, north)
    vmin, vmax = np.percentile(np.concatenate([before[np.isfinite(before)], after[np.isfinite(after)]]), [2, 98])
    if vmin == vmax:
        vmax = vmin + 1
    limit = max(1.0, float(np.percentile(np.abs(delta[np.isfinite(delta)]), 98)))
    gray = plt.get_cmap("gray").copy()
    diverging = plt.get_cmap("RdBu_r").copy()
    for cmap in (gray, diverging):
        cmap.set_bad("#d8e1e8")
    colors = ["#d8e1e8", "#2372a5", "#00bdb3", "#ed9e38", "#eeeeea"]
    class_cmap = ListedColormap(colors)
    class_norm = BoundaryNorm(np.arange(-0.5, 5.5), 5)
    panels = [("before_backscatter", before, f"Before: {dates[0]} | filtered HH", gray, vmin, vmax),
              ("after_backscatter", after, f"After: {dates[1]} | filtered HH", gray, vmin, vmax),
              ("backscatter_difference", delta, "Backscatter change: after - before", diverging, -limit, limit),
              ("water_change_classification", classes, "Exploratory water change candidates", class_cmap, None, None)]

    def panel(ax, entry):
        name, array, title, cmap, low, high = entry
        options = {"norm": class_norm} if name == "water_change_classification" else {"vmin": low, "vmax": high}
        image = ax.imshow(array, extent=extent, origin="upper", interpolation="nearest", cmap=cmap, **options)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("Easting (m)")
        ax.set_ylabel("Northing (m)")
        ax.ticklabel_format(style="plain", useOffset=False)
        if name == "water_change_classification":
            ax.legend(handles=[Patch(facecolor=colors[k], label=v) for k, v in CLASS_NAMES.items()],
                      loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=2, fontsize=7)
        else:
            ax.figure.colorbar(image, ax=ax, label="dB", shrink=0.8)

    gate = "disabled" if settings["min_abs_change_db"] is None else str(settings["min_abs_change_db"]) + " dB"
    footer = f"Exploratory threshold {settings['water_threshold_db']} dB | change gate {gate} | NOT confirmed flooding"
    for entry in panels:
        fig, ax = plt.subplots(figsize=(9, 5), layout="constrained")
        panel(ax, entry)
        fig.suptitle(footer, fontsize=9)
        fig.savefig(out / (entry[0] + ".png"), dpi=160)
        plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), layout="constrained")
    for ax, entry in zip(axes.flat, panels):
        panel(ax, entry)
    fig.suptitle("FloodPulse NISAR — " + footer, fontsize=11)
    fig.savefig(out / "water_change_overview.png", dpi=160)
    plt.close(fig)
    return {"backscatter_display_db": [float(vmin), float(vmax)],
            "difference_display_db": [-limit, limit],
            "display_rule": "Pooled 2nd–98th backscatter percentiles; symmetric 98th absolute delta percentile. Saved raster values are not clipped."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--water-threshold-db", type=float, default=-16)
    parser.add_argument("--min-change-db", type=float, default=3)
    parser.add_argument("--disable-change-threshold", action="store_true")
    parser.add_argument("--filter-size", type=int, default=3)
    parser.add_argument("--output-dir", default="data/water_change")
    args = parser.parse_args()
    out = (ROOT / args.output_dir).resolve()
    if not out.is_relative_to(ROOT):
        parser.error("Output directory must be inside the project.")
    out.mkdir(parents=True, exist_ok=True)
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "status": "started",
              "limitations": LIMITATIONS, "network_access_used": False, "inputs_modified": False}
    try:
        manifest = json.loads((ROOT / "data/nisar_manifest.json").read_text())
        previous = json.loads((ROOT / "data/nisar_visualization_report.json").read_text())
        items = sorted(manifest["observations"], key=lambda i: i["start_time_utc"])
        if len(items) != 2 or previous["status"] != "success":
            raise ValueError("Expected two successful real cached observations.")
        b, bv, grid, bmeta = load_cached(items[0], previous)
        a, av, agrid, ameta = load_cached(items[1], previous)
        a, av, corrected = align_power(a, av, agrid, grid)
        common = bv & av
        if not common.any():
            raise ValueError("No common valid pixels; change detection is undefined.")
        settings = {"water_threshold_db": args.water_threshold_db,
                    "min_abs_change_db": None if args.disable_change_threshold else args.min_change_db,
                    "water_rule": "filtered dB <= water threshold",
                    "change_rule": "cross water threshold AND abs(after_dB-before_dB) >= minimum; persistent water exempt",
                    "speckle_filter": {"method": "normalized mask-aware boxcar mean in linear power", "size_pixels": args.filter_size,
                                       "padding": "constant zero numerator and weights; renormalized", "invalid_center": "preserved as NaN",
                                       "support": "same common valid mask for both dates; no outside-AOI halo"}}
        bf = mask_aware_mean(b, common, args.filter_size)
        af = mask_aware_mean(a, common, args.filter_size)
        bdb, adb = power_to_db(bf), power_to_db(af)
        classes, delta = classify(bdb, adb, common, args.water_threshold_db, settings["min_abs_change_db"])
        areas = class_areas(classes, grid["crs"], grid["transform"])
        report.update(settings=settings, sources=[bmeta, ameta], aoi_wkt=manifest["aoi_wkt"],
                      alignment={"reference": "before", "after_reprojected": corrected,
                                 "resampling_if_needed": "nearest linear power + nearest validity mask",
                                 "input_valid_masks_equal_after_alignment": bool(np.array_equal(bv, av)),
                                 "common_valid_pixels": int(common.sum()), "common_mask_used_for_filter_and_classification": True,
                                 "before_valid_excluded_from_comparison": int((bv & ~common).sum()),
                                 "after_valid_excluded_from_comparison": int((av & ~common).sum())},
                      crs=str(grid["crs"]), transform=list(grid["transform"])[:6],
                      resolution_m=list(abs(v) for v in (grid["transform"].a, grid["transform"].e)),
                      pixel_area_km2=pixel_area_km2(grid["crs"], grid["transform"]),
                      classes=areas, expansion_km2=areas["2"]["area_km2"], recession_km2=areas["3"]["area_km2"])
        crossing = common & ((bdb <= args.water_threshold_db) != (adb <= args.water_threshold_db))
        report["threshold_crossings_rejected_by_change_gate"] = int((crossing & (classes == 4)).sum())
        tags = {"before_product": items[0]["product_id"], "after_product": items[1]["product_id"],
                "before_utc": items[0]["start_time_utc"], "after_utc": items[1]["start_time_utc"],
                "settings_json": json.dumps(settings), "interpretation": "Exploratory candidates only; not confirmed flooding"}
        save_raster(out / "filtered_radar_change.tif", [bf, af, bdb, adb, delta],
                    ["before_filtered_linear_power", "after_filtered_linear_power", "before_filtered_dB", "after_filtered_dB", "delta_dB_after_minus_before"], grid, tags)
        save_raster(out / "water_change_classes.tif", [classes], ["water_change_candidate_class"], grid,
                    {**tags, "class_codes_json": json.dumps(CLASS_NAMES)}, categorical=True)
        save_raster(out / "common_valid_mask.tif", [common], ["common_valid_1_unknown_0"], grid, tags, categorical=True)
        report["display"] = draw_maps(out, bdb, adb, delta, classes, grid,
                                      [i["start_time_utc"][:10] for i in items], settings)
        report.update(status="success", output_readback_verified=True,
                      outputs=sorted(p.name for p in out.iterdir() if p.suffix in (".tif", ".png")))
        summary = ("# Exploratory NISAR water change candidates\n\n"
                   f"Dates: {items[0]['start_time_utc']} → {items[1]['start_time_utc']}\n\n"
                   f"Possible expansion: **{report['expansion_km2']:.6f} km²**\n\n"
                   f"Possible recession: **{report['recession_km2']:.6f} km²**\n\n"
                   f"Common valid pixels: {int(common.sum())}; projected pixel area: {report['pixel_area_km2']} km².\n\n"
                   f"Exploratory water threshold: {args.water_threshold_db} dB; minimum absolute change: {settings['min_abs_change_db']}.\n\n"
                   + "\n".join("- " + s for s in LIMITATIONS) + "\n\n"
                   "Sources, identifiers, SHA-256 cache fingerprints, masks and full settings: results.json.\n\n"
                   "Method references: [SciPy convolve](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.convolve.html), "
                   "[Rasterio reprojection](https://rasterio.readthedocs.io/en/stable/topics/reproject.html), "
                   "[NASA SAR Handbook](https://earthdata.nasa.gov/s3fs-public/2025-04/SARHB_CH5_Content.pdf).\n")
        (out / "summary.md").write_text(summary)
        print(json.dumps({"status": report["status"], "expansion_km2": report["expansion_km2"],
                          "recession_km2": report["recession_km2"], "common_valid_pixels": int(common.sum()),
                          "alignment_corrected": corrected, "output_dir": str(out)}, indent=2))
        return 0
    except Exception as exc:
        report.update(status="error", error_type=type(exc).__name__, detail=str(exc))
        print(f"Water change processing failed: {exc}", file=sys.stderr)
        return 1
    finally:
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
