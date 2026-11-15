"""Focused scientific diagnostics; original NISAR data/results remain untouched."""

from datetime import datetime, timezone
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import array_bounds
from rasterio.warp import transform_geom, transform as project_points
from scipy.ndimage import convolve, distance_transform_edt, label, sobel, binary_erosion
from scripts.detect_water_change import load_cached, save_raster
from src.water_change import classify, mask_aware_mean, power_to_db, pixel_area_km2

OUT = ROOT / "data/scientific_quality_check"


def fingerprint():
    paths = list((ROOT / "data/water_change").rglob("*")) + list((ROOT / "data/subsets").rglob("*"))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def main():
    OUT.mkdir(exist_ok=True)
    originals = fingerprint()
    manifest = json.loads((ROOT / "data/nisar_manifest.json").read_text())
    previous = json.loads((ROOT / "data/nisar_visualization_report.json").read_text())
    items = sorted(manifest["observations"], key=lambda x: x["start_time_utc"])
    b, bv, grid, bm = load_cached(items[0], previous)
    a, av, ag, am = load_cached(items[1], previous)
    assert grid == ag, "QC expects the already aligned Milestone 3 caches"
    common = bv & av
    bf, af = mask_aware_mean(b, common, 3), mask_aware_mean(a, common, 3)
    bdb, adb = power_to_db(bf), power_to_db(af)
    raw_bdb, raw_adb = power_to_db(b), power_to_db(a)
    cell = pixel_area_km2(grid["crs"], grid["transform"])
    rows, maps = [], {}
    for threshold in (-14, -16, -18, -20):
        classes, delta = classify(bdb, adb, common, threshold, 3)
        row = {"water_threshold_db": threshold, "min_abs_change_db": 3,
               "filter_size": 3, "expansion_pixels": int((classes == 2).sum()),
               "recession_pixels": int((classes == 3).sum()),
               "expansion_km2": round(float((classes == 2).sum() * cell), 6),
               "recession_km2": round(float((classes == 3).sum() * cell), 6)}
        rows.append(row)
        maps[threshold] = classes
        save_raster(OUT / f"classes_threshold_{abs(threshold)}db.tif", [classes],
                    ["exploratory_water_change_classes"], grid,
                    {"threshold_db": str(threshold), "min_change_db": "3", "filter_size": "3",
                     "before_product": items[0]["product_id"], "after_product": items[1]["product_id"],
                     "interpretation": "Exploratory candidates, not confirmed flooding"}, categorical=True)
    with (OUT / "threshold_sensitivity.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    base = maps[-16]
    with rasterio.open(ROOT / "data/water_change/water_change_classes.tif") as ds:
        assert np.array_equal(ds.read(1), base), "Baseline must reproduce original classification"
    expansion = base == 2
    dy, dx = abs(grid["transform"].e), abs(grid["transform"].a)
    dark = common & (bdb <= -16)
    distance_dark = distance_transform_edt(~dark, sampling=(dy, dx))
    components, n = label(expansion, structure=np.ones((3, 3)))
    sizes = np.bincount(components.ravel())[1:]
    support = convolve(common.astype(int), np.ones((3, 3), int), mode="constant", cval=0)
    raw_classes, _ = classify(raw_bdb, raw_adb, common, -16, 3)
    raw_expansion = raw_classes == 2
    union = int((raw_expansion | expansion).sum())
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "sources": [bm, am], "settings_held_fixed": {"linear_power_filter": "3x3 mask-aware boxcar", "minimum_absolute_change_db": 3, "valid_pixels": int(common.sum())},
              "threshold_sensitivity": rows,
              "invalid_and_alignment": {"crs": str(grid["crs"]), "same_grid": True, "same_input_valid_masks": bool(np.array_equal(bv, av)),
                                        "invalid_classified_as_water": int(np.isin(base[~common], [1, 2, 3]).sum()),
                                        "expansion_with_incomplete_3x3_support": int((expansion & (support < 9)).sum()),
                                        "nan_masks_preserved": bool(np.array_equal(np.isfinite(bdb), common) and np.array_equal(np.isfinite(adb), common))},
              "existing_dark_radar_proximity": {"definition": "Before-date filtered HH <= -16 dB; not an independent water reference", "before_dark_pixels": int(dark.sum()),
                                                "expansion_within_30m_pixels": int((expansion & (distance_dark <= 30)).sum()),
                                                "expansion_within_60m_pixels": int((expansion & (distance_dark <= 60)).sum())},
              "connected_components": {"connectivity": 8, "component_count": n, "singleton_components": int((sizes == 1).sum()),
                                       "pixels_in_components_of_1_to_3_pixels": int(sizes[sizes <= 3].sum()), "largest_component_pixels": int(sizes.max()) if n else 0,
                                       "interpretation": "Small clusters may be noise or real narrow features; no clusters were removed."},
              "filter_diagnostic": {"raw_unfiltered_expansion_km2": float(raw_expansion.sum() * cell),
                                    "filtered_expansion_km2": float(expansion.sum() * cell),
                                    "shared_expansion_pixels": int((raw_expansion & expansion).sum()),
                                    "expansion_Jaccard_raw_vs_filtered": int((raw_expansion & expansion).sum()) / union if union else None,
                                    "interpretation": "Processing sensitivity, not an accuracy or validation score; no filter settings optimized."},
              "delta_distribution_db": {str(q): float(np.percentile(delta[common], q)) for q in (5, 25, 50, 75, 95)}}
    # Assess whether a small integer translation improves structural similarity.
    # This is an image-registration diagnostic, not independent water validation.
    def gradient(image):
        fill = np.where(common, image, 0)
        return np.hypot(sobel(fill, axis=0), sobel(fill, axis=1))
    gb, ga = gradient(bdb), gradient(adb)
    interior = binary_erosion(common, structure=np.ones((5, 5)), border_value=0)
    scores = []
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            br = slice(max(0, dr), min(b.shape[0], b.shape[0] + dr))
            ar = slice(max(0, -dr), min(b.shape[0], b.shape[0] - dr))
            bc = slice(max(0, dc), min(b.shape[1], b.shape[1] + dc))
            ac = slice(max(0, -dc), min(b.shape[1], b.shape[1] - dc))
            m = interior[br, bc] & interior[ar, ac]
            score = float(np.corrcoef(gb[br, bc][m], ga[ar, ac][m])[0, 1])
            scores.append({"row_shift": dr, "column_shift": dc, "gradient_correlation": score})
    report["integer_registration_diagnostic"] = {"best": max(scores, key=lambda s: s["gradient_correlation"]), "scores": scores,
                                                  "limitation": "Tests only integer shifts within +/-2 pixels; cannot rule out subpixel misregistration."}
    shapes, feature_counts = [], {}
    nonwetland_shapes, canal_stream_shapes, wetland_shapes = [], [], []
    for layer in (6, 9, 12):
        path = OUT / f"nhd_layer_{layer}.geojson"
        if path.exists():
            data = json.loads(path.read_text())
            assert "features" in data and not data.get("exceededTransferLimit"), "Hydrography query failed or truncated"
            feature_counts[str(layer)] = len(data["features"])
            for feature in data["features"]:
                if not feature.get("geometry"):
                    continue
                geom = transform_geom("EPSG:4326", grid["crs"], feature["geometry"])
                properties = feature["properties"]
                kind = int(properties.get("ftype", properties.get("FTYPE")))
                shapes.append(geom)
                (wetland_shapes if kind == 466 else nonwetland_shapes).append(geom)
                if kind in (336, 460):
                    canal_stream_shapes.append(geom)
    hydro = rasterize([(g, 1) for g in shapes], out_shape=b.shape, transform=grid["transform"], all_touched=True).astype(bool) if shapes else np.zeros(b.shape, bool)
    if shapes:
        hd = distance_transform_edt(~hydro, sampling=(dy, dx))
        report["historical_hydrography_proximity"] = {"source": "USGS NHD large-scale flowlines/areas/waterbodies", "feature_counts": feature_counts,
                                                     "rasterization": "all_touched=True on 10m NISAR grid; distances quantized to raster cells",
                                                     "expansion_inside_or_touching_hydro_pixels": int((expansion & hydro).sum()),
                                                     "expansion_within_30m_pixels": int((expansion & (hd <= 30)).sum()),
                                                     "expansion_within_60m_pixels": int((expansion & (hd <= 60)).sum()),
                                                     "not_date_matched": True, "not_flood_validation": True}
        for name, geometries in (("network_excluding_swamp_marsh", nonwetland_shapes),
                                 ("explicit_canal_ditch_or_stream_river", canal_stream_shapes),
                                 ("swamp_marsh_only", wetland_shapes)):
            feature_mask = rasterize([(g, 1) for g in geometries], out_shape=b.shape, transform=grid["transform"], all_touched=True).astype(bool)
            distance = distance_transform_edt(~feature_mask, sampling=(dy, dx))
            report["historical_hydrography_proximity"][name] = {
                "mapped_pixels_in_common_aoi": int((feature_mask & common).sum()),
                "expansion_inside_or_touching_pixels": int((expansion & feature_mask).sum()),
                "expansion_within_30m_pixels": int((expansion & (distance <= 30)).sum()),
                "expansion_within_60m_pixels": int((expansion & (distance <= 60)).sum())}
        report["historical_hydrography_proximity"]["caution"] = "All-hydrography union includes broad historical swamp/marsh polygons; use the separate canal/stream statistics when discussing river/ditch proximity."
        # Draw the water network without broad swamp polygons obscuring radar.
        hydro = rasterize([(g, 1) for g in nonwetland_shapes], out_shape=b.shape, transform=grid["transform"], all_touched=True).astype(bool)
    # Export real detections' component centroids and sizes for manual review.
    features = []
    for k in np.argsort(sizes)[::-1]:
        rr, cc = np.nonzero(components == k + 1)
        x, y = grid["transform"] * (float(cc.mean()) + .5, float(rr.mean()) + .5)
        lon, lat = project_points(grid["crs"], "EPSG:4326", [x], [y])
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon[0], lat[0]]},
                         "properties": {"component_id": int(k + 1), "pixels": int(sizes[k]), "area_km2": float(sizes[k] * cell)}})
    (OUT / "expansion_component_centroids.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features}, indent=2))
    xs = np.arange(4)
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    ax.bar(xs - .18, [r["expansion_km2"] for r in rows], .36, label="Expansion candidate")
    ax.bar(xs + .18, [r["recession_km2"] for r in rows], .36, label="Recession candidate")
    ax.set_xticks(xs, [str(r["water_threshold_db"]) for r in rows]); ax.set_xlabel("Exploratory water threshold (dB)")
    ax.set_ylabel("Candidate area (km²)"); ax.legend()
    ax.set_title("Threshold sensitivity | 3x3 linear filter, |change| >= 3 dB")
    fig.savefig(OUT / "threshold_sensitivity.png", dpi=160); plt.close(fig)
    west, south, east, north = array_bounds(*b.shape, grid["transform"])
    extent = (west, east, south, north)
    fig, axes = plt.subplots(2, 2, figsize=(13, 7), layout="constrained", sharex=True, sharey=True)
    for ax, row in zip(axes.flat, rows):
        ax.imshow(bdb, cmap="gray", vmin=-20, vmax=0, extent=extent, origin="upper")
        rgba = np.zeros((*b.shape, 4))
        rgba[maps[row["water_threshold_db"]] == 2] = (0, .95, .8, 1)
        rgba[maps[row["water_threshold_db"]] == 3] = (1, .5, 0, 1)
        ax.imshow(rgba, extent=extent, origin="upper", interpolation="nearest")
        ax.set_title(f"{row['water_threshold_db']} dB | expansion {row['expansion_km2']:.4f}, recession {row['recession_km2']:.4f} km²", fontsize=9)
        ax.set_xlabel("Easting (m)"); ax.set_ylabel("Northing (m)"); ax.ticklabel_format(useOffset=False, style="plain")
    fig.suptitle("Cyan: expansion candidate | Orange: recession candidate | Background: BEFORE radar, same scale\nExploratory sensitivity only; not confirmed flooding", fontsize=10)
    fig.savefig(OUT / "threshold_spatial_comparison.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(12, 5), layout="constrained")
    ax.imshow(bdb, cmap="gray", vmin=-20, vmax=0, extent=extent, origin="upper")
    yy, xx = np.nonzero(hydro & common)
    ax.scatter(west + (xx + .5) * dx, north - (yy + .5) * dy, s=.5, c="#54b9ff", alpha=.35, label="Historical NHD network (swamp polygons excluded; context only)")
    yy, xx = np.nonzero(expansion)
    ax.scatter(west + (xx + .5) * dx, north - (yy + .5) * dy, s=6, c="#ff6044", label="-16 dB expansion candidates (markers enlarged)")
    ax.set_xlim(west, east); ax.set_ylim(south, north); ax.set_aspect("equal")
    ax.ticklabel_format(useOffset=False, style="plain"); ax.set_xlabel("Easting (m)"); ax.set_ylabel("Northing (m)")
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.2), fontsize=8)
    ax.set_title("Candidate locations vs historical hydrography and BEFORE radar | Not validation")
    fig.savefig(OUT / "candidate_location_context.png", dpi=160); plt.close(fig)
    assert fingerprint() == originals, "Original files changed during quality check"
    report["original_files_unchanged_sha256"] = originals
    report["independent_validation_status"] = "unvalidated; hydrography is historical context and DSWx catalog/pixel checks are recorded separately"
    (OUT / "quality_diagnostics.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ('sources', 'original_files_unchanged_sha256', 'integer_registration_diagnostic')}, indent=2))


if __name__ == "__main__":
    main()
