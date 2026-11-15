"""Pure functions for the preregistered flood validation (docs/FLOOD_VALIDATION_PROTOCOL.md, freeze 181782456a).

Agreement with independent water products only; never accuracy against ground truth. Reuses the existing
preprocessing (water_change.mask_aware_mean / power_to_db) and change classes (water_change.classify).
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from rasterio.enums import Resampling
from rasterio.transform import Affine
from rasterio.warp import reproject

from src.flood_classes import masks, OPEN, NOT_WATER, PARTIAL
from src.water_change import mask_aware_mean, power_to_db, classify

GRID = np.round(np.arange(-25.0, -9.99, 0.5), 2)
DEFAULT_HH, MIN_CHANGE = -16.0, 3.0
# Primary configuration for stages b-e (protocol Deviation 3): the untuned default, fixed before any data was seen.
PRIMARY_CONFIG = (('variant', 'HH'), ('t_HH', -16.0), ('min_change_db', 3.0), ('outcome', 'new open water'), ('reference', 'S1'))
ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / 'data/flood_validation/calibration.json'


def preprocess(cube):
    """dB after the existing 3x3 mask-aware linear-power mean; common valid mask over all dates and both channels."""
    hh, hv = np.asarray(cube['hh_power'], float), np.asarray(cube['hv_power'], float)
    valid = ((np.isfinite(hh) & (hh > 0)) & (np.isfinite(hv) & (hv > 0))).all(axis=0)
    out = dict(valid=valid)
    for name, stack in (('HH', hh), ('HV', hv)):
        out[name] = np.stack([power_to_db(mask_aware_mean(p, valid, 3)) for p in stack])
    out['valid'] = valid & np.isfinite(out['HH']).all(axis=0) & np.isfinite(out['HV']).all(axis=0)
    return out


def align_reference(codes, src_transform, src_crs, dst_shape, dst_transform, dst_crs):
    """Categorical reference codes on the NISAR grid by nearest neighbour; outside the reference window -> 255."""
    out = np.full(dst_shape, 255, dtype=np.uint8)
    reproject(np.asarray(codes, np.uint8), out, src_transform=Affine(*src_transform), src_crs=src_crs,
              dst_transform=Affine(*dst_transform), dst_crs=dst_crs, resampling=Resampling.nearest,
              src_nodata=None, dst_nodata=255, init_dest_nodata=False)
    return out


def confusion(pred, positive, negative, valid):
    """Counts and metrics. Pixels that are neither positive nor negative in the reference, or invalid in NISAR, are 'invalid'."""
    pred = np.asarray(pred, bool); valid = np.asarray(valid, bool)
    pos = np.asarray(positive, bool) & valid; neg = np.asarray(negative, bool) & valid & ~pos
    tp = int((pred & pos).sum()); fp = int((pred & neg).sum()); fn = int((~pred & pos).sum()); tn = int((~pred & neg).sum())
    invalid = int(pred.size - tp - fp - fn - tn)
    div = lambda a, b: float(a) / b if b else None
    precision, recall = div(tp, tp + fp), div(tp, tp + fn)
    f1 = div(2 * tp, 2 * tp + fp + fn)
    return dict(TP=tp, FP=fp, FN=fn, TN=tn, invalid=invalid, precision=precision, recall=recall, F1=f1,
                IoU=div(tp, tp + fp + fn), reference_positive_share=div(tp + fn, tp + fp + fn + tn))


def agreement_map(pred, positive, negative, valid):
    """0 invalid, 1 TP, 2 FP, 3 FN, 4 TN."""
    pred = np.asarray(pred, bool); valid = np.asarray(valid, bool)
    pos = np.asarray(positive, bool) & valid; neg = np.asarray(negative, bool) & valid & ~pos
    out = np.zeros(pred.shape, np.uint8)
    out[pred & pos] = 1; out[pred & neg] = 2; out[~pred & pos] = 3; out[~pred & neg] = 4
    return out


def reference_presence(codes, product):
    """Main outcome: open water (positive) vs not water (negative); partial/inundated, invalid, undefined excluded."""
    m = masks(codes, product)
    return m[OPEN], m[NOT_WATER], m[PARTIAL]


def reference_new_water(pre, during, product):
    """Positive: not water before AND open water during. Negative: both dates open/not water, not positive.
    Partial/inundated on either date, invalid and undefined are excluded."""
    a, b = masks(pre, product), masks(during, product)
    clean = (a[OPEN] | a[NOT_WATER]) & (b[OPEN] | b[NOT_WATER])
    pos = clean & a[NOT_WATER] & b[OPEN]
    return pos, clean & ~pos


def water(db, threshold):
    return np.asarray(db) <= threshold


def nisar_presence(prep, index, variant, t_hh, t_hv):
    hh, hv = prep['HH'][index], prep['HV'][index]
    if variant == 'HH':
        return water(hh, t_hh)
    if variant == 'HV':
        return water(hv, t_hv)
    return water(hh, t_hh) & water(hv, t_hv)


def nisar_new_water(prep, before, after, variant, t_hh, t_hv, min_change=MIN_CHANGE):
    """Existing water_change.classify (class 2 = new water). HH+HV: water = both channels below their thresholds,
    gate on |dHH| >= min_change (the existing classify gate, applied to HH)."""
    valid = prep['valid']
    if variant in ('HH', 'HV'):
        band, t = (prep['HH'], t_hh) if variant == 'HH' else (prep['HV'], t_hv)
        classes, _ = classify(band[before], band[after], valid, t, min_change)
        return classes == 2
    wb = water(prep['HH'][before], t_hh) & water(prep['HV'][before], t_hv)
    wa = water(prep['HH'][after], t_hh) & water(prep['HV'][after], t_hv)
    gate = np.abs(prep['HH'][after] - prep['HH'][before]) >= min_change
    return valid & ~wb & wa & gate


def calibrate(db, positive, negative, valid, grid=GRID, prefer=DEFAULT_HH):
    """Threshold maximising F1 (ties: closest to `prefer`, then the higher value). Returns (threshold, table)."""
    table = []
    for t in grid:
        m = confusion(water(db, t), positive, negative, valid)
        table.append(dict(threshold=float(t), **m))
    best = max(table, key=lambda r: ((r['F1'] if r['F1'] is not None else -1), -abs(r['threshold'] - prefer), r['threshold']))
    return best['threshold'], table


def directions(prep, before, after, categories):
    """Median dHH/dHV and share of decreases per reference category (no single expected sign)."""
    dhh = prep['HH'][after] - prep['HH'][before]; dhv = prep['HV'][after] - prep['HV'][before]
    out = {}
    for name, mask in categories.items():
        m = np.asarray(mask, bool) & prep['valid']
        n = int(m.sum())
        out[name] = dict(pixels=n) if not n else dict(
            pixels=n, median_dHH_db=float(np.median(dhh[m])), median_dHV_db=float(np.median(dhv[m])),
            share_dHH_negative=float((dhh[m] < 0).mean()), share_dHV_negative=float((dhv[m] < 0).mean()),
            share_dHH_up_3db=float((dhh[m] >= 3).mean()))
    return out


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen_thresholds(path=CALIBRATION, expected_sha=None):
    """Calibrated thresholds; refuses if the file's SHA-256 differs from the frozen value (test data cannot change them)."""
    path = Path(path)
    record = json.loads(path.read_text())
    expected = expected_sha or path.with_suffix('.sha256').read_text().split()[0]
    if sha256(path) != expected:
        raise ValueError('calibration.json changed after it was frozen; refusing to evaluate.')
    return record['frozen']['HH'], record['frozen']['HV']


BOOT_SEED, BOOT_N, BOOT_BLOCK_M = 20261115, 1000, 1000.0   # protocol Deviation 4


def block_bootstrap(pred, positive, negative, valid, block_px, n=BOOT_N, seed=BOOT_SEED):
    """Spatial block bootstrap: confusion counts per block (block_px x block_px pixels), blocks resampled with replacement
    (as many blocks as the grid has), metrics recomputed; 2.5/97.5 percentiles. Point estimates are not changed."""
    pred = np.asarray(pred, bool); valid = np.asarray(valid, bool)
    pos = np.asarray(positive, bool) & valid; neg = np.asarray(negative, bool) & valid & ~pos
    h, w = pred.shape
    counts = []
    for r in range(0, h, block_px):
        for c in range(0, w, block_px):
            sl = (slice(r, r + block_px), slice(c, c + block_px))
            p, ps, ng = pred[sl], pos[sl], neg[sl]
            counts.append(((p & ps).sum(), (p & ng).sum(), (~p & ps).sum(), (~p & ng).sum()))
    counts = np.array(counts, dtype=float)
    rng = np.random.default_rng(seed)
    draws = counts[rng.integers(0, len(counts), (n, len(counts)))].sum(axis=1)      # (n, 4): TP FP FN TN
    tp, fp, fn = draws[:, 0], draws[:, 1], draws[:, 2]
    with np.errstate(invalid='ignore', divide='ignore'):
        stats = dict(precision=tp / (tp + fp), recall=tp / (tp + fn), F1=2 * tp / (2 * tp + fp + fn), IoU=tp / (tp + fp + fn))
    out = dict(blocks=len(counts), block_px=block_px, resamples=n, seed=seed)
    for k, v in stats.items():
        v = v[np.isfinite(v)]
        out[k] = [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if v.size else None
    return out


def coregistration_offset(a, b, valid, max_shift=8):
    """Integer (row, col) shift of b relative to a from the peak of the FFT cross-correlation of the demeaned dB images
    over the common valid area, plus a parabolic sub-pixel refinement. Used for the 09-18 forecast-orbit check."""
    a = np.where(valid, a - np.nanmean(a[valid]), 0.0); b = np.where(valid, b - np.nanmean(b[valid]), 0.0)
    fa, fb = np.fft.rfft2(a), np.fft.rfft2(b)
    xc = np.fft.irfft2(fa.conj() * fb, s=a.shape)
    xc = np.fft.fftshift(xc)
    cy, cx = a.shape[0] // 2, a.shape[1] // 2
    win = xc[cy - max_shift:cy + max_shift + 1, cx - max_shift:cx + max_shift + 1]
    r, c = np.unravel_index(np.argmax(win), win.shape)
    def sub(m, i):
        if 0 < i < len(m) - 1:
            d = m[i - 1] - 2 * m[i] + m[i + 1]
            return 0.5 * (m[i - 1] - m[i + 1]) / d if d else 0.0
        return 0.0
    dr = r - max_shift + sub(win[:, c], r); dc = c - max_shift + sub(win[r, :], c)
    peak = float(win[r, c]); norm = float(np.sqrt((a * a).sum() * (b * b).sum()))
    return dict(row=float(dr), col=float(dc), magnitude=float(np.hypot(dr, dc)), peak_correlation=peak / norm if norm else None)
