"""Placebo (null) check: candidate-minus-ring contrast vs the same footprint shape at random valid positions.

Method fixed in docs/PLACEBO_METHOD.md before any result was computed. Reuses src.robustness.ring_mask and
ring_comparison unchanged. Descriptive only: an exceedance fraction, never a p-value or a significance claim.
"""
import json
from pathlib import Path

import numpy as np

from src.robustness import ring_mask, ring_comparison

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/placebo'
DRAWS = 2000
BASE_SEED = 20261115
MIN_PLACEMENTS = 200
MIN_RING_PIXELS = 20        # same minimum ring size as src.explore.MIN_RING_PIXELS
MIN_SPACING_PX = 10         # 100 m between kept placements (simplification for spatial autocorrelation)
VERSION = 'placebo-v1'


def shape_offsets(footprint):
    """Pixel offsets of a footprint relative to its bounding-box corner, and the box size."""
    rows, cols = np.nonzero(footprint)
    r0, c0 = rows.min(), cols.min()
    return rows - r0, cols - c0, (int(rows.max() - r0 + 1), int(cols.max() - c0 + 1))


def place(offsets, top, left, shape):
    rows, cols, _ = offsets
    mask = np.zeros(shape, bool); mask[rows + top, cols + left] = True
    return mask


def contrast(hh, hv, footprint, ring, interval, dates):
    """Footprint minus ring median change (HH, HV) over one interval, via the existing ring_comparison."""
    i = interval
    row = ring_comparison(hh[[i, i + 1]], hv[[i, i + 1]], footprint, ring, [dates[i], dates[i + 1]])[0]
    return row['candidate_minus_ring_dHH_db'], row['candidate_minus_ring_dHV_db'], row


def exceedance_fraction(null, value):
    """(#{|null| >= |value|} + 1) / (n + 1). Descriptive; not a p-value."""
    null = np.asarray(null, float)
    return float((np.count_nonzero(np.abs(null) >= abs(value)) + 1) / (null.size + 1))


def null_placements(footprint, common, candidates, seed, draws=DRAWS, min_ring=MIN_RING_PIXELS, spacing=MIN_SPACING_PX):
    """Random placements of the footprint's exact shape that satisfy the fixed rules. Yields (top, left, mask, ring)."""
    offsets = shape_offsets(footprint); height, width = offsets[2]; shape = common.shape
    rng = np.random.default_rng(seed)
    tops = rng.integers(0, shape[0] - height + 1, draws); lefts = rng.integers(0, shape[1] - width + 1, draws)
    kept = []
    for top, left in zip(tops, lefts):
        if any((top - a) ** 2 + (left - b) ** 2 < spacing ** 2 for a, b in kept):
            continue
        mask = place(offsets, top, left, shape)
        if not common[mask].all() or candidates[mask].any():
            continue
        ring = ring_mask(mask, common, exclude=candidates)
        if int(ring.sum()) < min_ring:
            continue
        kept.append((top, left))
        yield int(top), int(left), mask, ring


def placebo_for_candidate(hh, hv, common, labels, candidate_id, interval, dates, candidate_ids, draws=DRAWS,
                          seed=None, min_placements=MIN_PLACEMENTS):
    seed = BASE_SEED + candidate_id if seed is None else seed
    candidates = np.isin(labels, candidate_ids)
    footprint = labels == candidate_id
    ring = ring_mask(footprint, common, exclude=candidates)
    real_hh, real_hv, row = contrast(hh, hv, footprint, ring, interval, dates)
    null_hh, null_hv, positions = [], [], []
    for top, left, mask, pring in null_placements(footprint, common, candidates, seed, draws):
        a, b, _ = contrast(hh, hv, mask, pring, interval, dates)
        null_hh.append(a); null_hv.append(b); positions.append([top, left])
    result = dict(candidate=candidate_id, interval=[dates[interval], dates[interval + 1]], seed=seed, draws_attempted=draws,
                  placements=len(null_hh), min_placements=min_placements, candidate_pixels=int(footprint.sum()),
                  candidate_ring_pixels=int(ring.sum()), positions=positions)
    enough = len(null_hh) >= min_placements
    result['status'] = 'computed' if enough else 'not enough valid placements'
    for band, value, null in (('HH', real_hh, null_hh), ('HV', real_hv, null_hv)):
        entry = dict(candidate_minus_ring_db=float(value))
        if enough:
            entry.update(null_median_db=float(np.median(null)), null_p05_db=float(np.percentile(null, 5)),
                         null_p95_db=float(np.percentile(null, 95)), exceedance_fraction=exceedance_fraction(null, value),
                         null_values_db=[float(v) for v in null])
        result[band] = entry
    return result


def load_results(directory=OUTPUT):
    """Saved placebo results, verified against their sidecar; None when not available."""
    import hashlib
    directory = Path(directory)
    try:
        sidecar = json.loads((directory / 'sidecar.json').read_text())
        for name, digest in sidecar['outputs_sha256'].items():
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
                return None
        return json.loads((directory / 'results.json').read_text())
    except (OSError, KeyError, ValueError):
        return None


def for_candidate(results, candidate_id):
    if not results:
        return None
    return next((c for c in results['candidates'] if c['candidate'] == candidate_id), None)


_CACHE = {}


def cached_results(directory=OUTPUT):
    """load_results, re-read only when results.json or sidecar.json change on disk."""
    directory = Path(directory)
    try:
        stamp = tuple((directory / n).stat().st_mtime_ns for n in ('results.json', 'sidecar.json'))
    except OSError:
        return None
    key = str(directory)
    if _CACHE.get(key, (None,))[0] != stamp:
        _CACHE[key] = (stamp, load_results(directory))
    return _CACHE[key][1]


def note_line(result, lang='en'):
    """One review-note line (or a 'not available' line) for a candidate's placebo result."""
    from src.i18n import t, num
    if not result:
        return t('pl.note_missing', lang=lang)
    if result['status'] != 'computed':
        return t('pl.note_not_enough', lang=lang, n=result['placements'], minimum=result['min_placements'])
    return t('pl.note', lang=lang, d1=result['interval'][0], d2=result['interval'][1], n=result['placements'],
             seed=result['seed'], hh=num(result['HH']['exceedance_fraction'], 4, lang=lang),
             hv=num(result['HV']['exceedance_fraction'], 4, lang=lang))


def count_at_least(result, band):
    """Number of placements at least as extreme as the candidate (recovered from the saved null values)."""
    b = result[band]
    return int(np.count_nonzero(np.abs(np.asarray(b['null_values_db'])) >= abs(b['candidate_minus_ring_db'])))
