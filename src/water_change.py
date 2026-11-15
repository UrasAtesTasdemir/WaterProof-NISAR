"""Exploratory radar water candidates, not confirmed water or flooding."""

import numpy as np
from scipy.ndimage import convolve
from rasterio.enums import Resampling
from rasterio.warp import reproject

CLASS_NAMES = {0: "Unknown / no data", 1: "Persistent water candidate",
               2: "New water candidate (possible expansion)",
               3: "Receded water candidate", 4: "Other valid surface"}


def suppress_single_pixel_changes(classes):
    """Optional 8-connected singleton suppression, separately for classes 2/3.

    Do not remove persistent water or unknowns. Suppressed candidates become
    class 4 (other valid surface), never evidence of non-water. Real narrow
    features may be lost: this is a visualization/size prior, not validation.
    """
    from scipy.ndimage import label
    result = np.asarray(classes).copy()
    suppressed = np.zeros(result.shape, dtype=bool)
    for code in (2, 3):
        components, _ = label(result == code, structure=np.ones((3, 3)))
        counts = np.bincount(components.ravel())
        small = (components > 0) & (counts[components] == 1)
        suppressed |= small
    result[suppressed] = 4
    return result, suppressed


def power_to_db(power):
    power = np.asarray(power, dtype=np.float64)
    valid = np.isfinite(power) & (power > 0)
    db = np.full(power.shape, np.nan)
    db[valid] = 10 * np.log10(power[valid])
    return db


def mask_aware_mean(power, valid, size=3):
    """Normalized boxcar mean of valid LINEAR power; retain invalid centers.

    No zero-padding bias: both numerator and valid-neighbor count use constant
    zero padding. AOI edges use fewer neighbors; this is not a Lee filter.
    """
    if not isinstance(size, int) or size < 1 or size % 2 != 1 or size > 9:
        raise ValueError("Filter size must be an odd integer between 1 and 9.")
    power = np.asarray(power, dtype=np.float64)
    valid = np.asarray(valid, dtype=bool)
    if power.shape != valid.shape or power.ndim != 2:
        raise ValueError("Power and mask must be matching 2D arrays.")
    valid = valid & np.isfinite(power) & (power > 0)
    kernel = np.ones((size, size), dtype=np.float64)
    total = convolve(np.where(valid, power, 0), kernel, mode="constant", cval=0)
    count = convolve(valid.astype(float), kernel, mode="constant", cval=0)
    result = np.full(power.shape, np.nan)
    np.divide(total, count, out=result, where=valid & (count > 0))
    return result


def align_power(power, valid, source_grid, reference_grid):
    """Align after to before using nearest samples and a separate validity mask.

    No interpolation of dB; no filling gaps. Nearest is chosen to preserve
    observed linear power values. Reprojection may still alter spatial support.
    """
    matching = (source_grid["crs"] == reference_grid["crs"]
                and source_grid["shape"] == reference_grid["shape"]
                and source_grid["transform"].almost_equals(reference_grid["transform"], precision=1e-8))
    if matching:
        return np.where(valid, power, np.nan).astype(float), valid.copy(), False
    destination = np.full(reference_grid["shape"], np.nan)
    destination_mask = np.zeros(reference_grid["shape"], dtype="uint8")
    options = dict(src_transform=source_grid["transform"], src_crs=source_grid["crs"],
                   dst_transform=reference_grid["transform"], dst_crs=reference_grid["crs"],
                   resampling=Resampling.nearest)
    reproject(np.where(valid, power, np.nan).astype(float), destination,
              src_nodata=np.nan, dst_nodata=np.nan, **options)
    reproject(valid.astype("uint8"), destination_mask, src_nodata=0, dst_nodata=0, **options)
    valid_out = (destination_mask == 1) & np.isfinite(destination) & (destination > 0)
    return np.where(valid_out, destination, np.nan), valid_out, True


def classify(before_db, after_db, valid, water_threshold=-16.0, min_change=3.0):
    """Cross-threshold transitions must also pass the optional absolute gate.

    Rejected transitions remain class 4, not persistent water. Unknown is class
    0 even if a filter could estimate a value from surrounding valid pixels.
    """
    if not np.isfinite(water_threshold):
        raise ValueError("Water threshold must be finite.")
    if min_change is not None and (not np.isfinite(min_change) or min_change < 0):
        raise ValueError("Minimum change must be nonnegative or disabled.")
    before_db, after_db = np.asarray(before_db), np.asarray(after_db)
    valid = np.asarray(valid, dtype=bool)
    if before_db.shape != after_db.shape or valid.shape != before_db.shape:
        raise ValueError("Classification arrays and mask must have equal shapes.")
    valid = valid & np.isfinite(before_db) & np.isfinite(after_db)
    delta = np.where(valid, after_db - before_db, np.nan)
    before_water = before_db <= water_threshold
    after_water = after_db <= water_threshold
    gate = np.ones(valid.shape, dtype=bool) if min_change is None else np.abs(delta) >= min_change
    classes = np.zeros(valid.shape, dtype="uint8")
    classes[valid] = 4
    classes[valid & before_water & after_water] = 1
    classes[valid & ~before_water & after_water & gate] = 2
    classes[valid & before_water & ~after_water & gate] = 3
    return classes, delta


def pixel_area_km2(crs, transform):
    if crs is None or not crs.is_projected:
        raise ValueError("Area requires a projected CRS, never geographic degrees.")
    _, meters_per_unit = crs.linear_units_factor
    area = abs(transform.a * transform.e - transform.b * transform.d) * meters_per_unit**2 / 1e6
    if not np.isfinite(area) or area <= 0:
        raise ValueError("Raster pixel area must be positive and finite.")
    return float(area)


def class_areas(classes, crs, transform):
    pixel_area = pixel_area_km2(crs, transform)
    return {str(code): {"name": name, "pixels": int(np.count_nonzero(classes == code)),
                        "area_km2": int(np.count_nonzero(classes == code)) * pixel_area}
            for code, name in CLASS_NAMES.items()}
