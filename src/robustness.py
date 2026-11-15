"""Robustness checks for investigation candidates (pure functions, no I/O).

Reuses the existing screening/ranking functions in ``src.investigation``
unchanged. Nothing here corrects data: the ring comparison is shown next to
the raw change, never instead of it.
"""
from datetime import datetime

import numpy as np
from scipy.ndimage import distance_transform_edt

from src.investigation import event_components, describe_proposals, rank_regions

RING_INNER_PX = 5    # 50 m: excludes the immediate edge, which shares mixed pixels with the candidate
RING_OUTER_PX = 15   # 150 m
GAP_DAYS = 13        # NISAR repeat is 12 days; a longer interval means a missing acquisition


def acquisition_gaps(dates, nominal_days=12):
    """Intervals longer than the nominal repeat (e.g. 27 Jul → 20 Aug = 24 days)."""
    times = [datetime.fromisoformat(d[:10]) for d in dates]
    gaps = []
    for a, b, da, db in zip(times, times[1:], dates, dates[1:]):
        days = (b - a).days
        if days > nominal_days:
            gaps.append(dict(start=da[:10], end=db[:10], days=days, missing_acquisitions=round(days / nominal_days) - 1))
    return gaps


def iou(a, b):
    a = np.asarray(a, bool); b = np.asarray(b, bool)
    union = np.count_nonzero(a | b)
    return 0.0 if union == 0 else np.count_nonzero(a & b) / union


def indices_mask(indices, shape):
    mask = np.zeros(shape, bool); mask.ravel()[indices] = True
    return mask


def screen(hh, hv, common, floor_db=3.0, percentile=90.0, minimum_pixels=25):
    """Run the existing screening + description + ranking on a cube."""
    proposals, scene, eligible = event_components(hh, common, floor_db, percentile, minimum_pixels)
    proposals = describe_proposals(proposals, hh, hv, scene)
    return proposals, scene, eligible, rank_regions(proposals)


def match_candidate(footprint, proposals, selected, shape):
    """Best-overlapping proposal (any) and best-overlapping selected top-5 region."""
    best_any = max(((iou(footprint, indices_mask(p['indices'], shape)), p) for p in proposals),
                   key=lambda t: t[0], default=(0.0, None))
    best_sel = max(((iou(footprint, indices_mask(p['indices'], shape)), rank, p) for rank, p in enumerate(selected, 1)),
                   key=lambda t: t[0], default=(0.0, None, None))
    return best_any, best_sel


def footprint_interval_medians(hh, footprint):
    """Median of pixel-wise consecutive HH differences on a fixed footprint."""
    values = hh[:, footprint]
    return np.median(np.diff(values, axis=0), axis=1)


def notable_on_footprint(hh, footprint, scene):
    """Existing notable-interval rule applied to a fixed footprint."""
    delta = footprint_interval_medians(hh, footprint)
    return [dict(delta_db=float(x), notable=bool(abs(x) >= s['magnitude_floor_db'] and abs(x) > s['absolute_change_percentile_db']))
            for x, s in zip(delta, scene)]


def merged_seed_interval(n_dates, seed_interval, drop):
    """Original date indices (a, b) of the interval that contains the seed event after removing ``drop``.

    The seed event lies between dates ``seed_interval`` and ``seed_interval + 1``. After a removal it is
    carried by the interval from the last kept date at or before the seed start to the first kept date at
    or after the seed end. Returns None when no kept date exists on one side (the event is then not
    observable in the reduced series).
    """
    if not 0 <= seed_interval < n_dates - 1 or not 0 <= drop < n_dates:
        raise ValueError('Seed interval or removed date outside the series.')
    before = [i for i in range(seed_interval + 1) if i != drop]
    after = [i for i in range(seed_interval + 1, n_dates) if i != drop]
    return (before[-1], after[0]) if before and after else None


def leave_one_date_out(hh, hv, common, dates, footprint, seed_direction, seed_interval, floor_db=3.0, percentile=90.0):
    """For each removed date: is the seed event still a notable seed-direction change in the (possibly merged)
    interval that contains it, and is the candidate re-detected by screening? One row per removed date.

    Only the interval carrying the original seed event counts. Same-direction changes in other intervals are
    reported separately and never count as the seed event being kept.
    """
    rows = []
    sign = 1 if seed_direction in ('increase', 1) else -1
    for drop in range(len(dates)):
        keep = [i for i in range(len(dates)) if i != drop]
        sub_hh, sub_hv = hh[keep], hv[keep]
        proposals, scene, eligible, selected = screen(sub_hh, sub_hv, common, floor_db, percentile)
        intervals = notable_on_footprint(sub_hh, footprint, scene)
        listed = [dict(start=dates[keep[i]], end=dates[keep[i + 1]], **r) for i, r in enumerate(intervals)]
        merged = merged_seed_interval(len(dates), seed_interval, drop)
        carrier = None
        if merged is not None:
            carrier = keep.index(merged[0])          # consecutive in the reduced series by construction
            if keep[carrier + 1] != merged[1]:
                raise ValueError('Merged seed interval is not consecutive in the reduced series.')
        seed_row = listed[carrier] if carrier is not None else None
        still = None if seed_row is None else bool(seed_row['notable'] and np.sign(seed_row['delta_db']) == sign)
        others = [r for i, r in enumerate(listed) if i != carrier and r['notable'] and np.sign(r['delta_db']) == sign]
        (any_iou, _), (sel_iou, sel_rank, _) = match_candidate(footprint, proposals, selected, footprint.shape)
        rows.append(dict(removed_date=dates[drop], notable_intervals=sum(r['notable'] for r in intervals),
                         seed_event_interval=f"{seed_row['start']} → {seed_row['end']}" if seed_row else None,
                         seed_event_interval_days=(datetime.fromisoformat(seed_row['end'][:10]) -
                                                   datetime.fromisoformat(seed_row['start'][:10])).days if seed_row else None,
                         seed_event_delta_db=float(seed_row['delta_db']) if seed_row else None,
                         seed_event_still_notable=still,
                         seed_event_status=('not testable: the seed event is not observable without this date' if still is None
                                            else 'still notable in the seed direction' if still else 'not notable in the seed direction'),
                         other_same_direction_notable_intervals=[f"{r['start']} → {r['end']}" for r in others],
                         footprint_fraction_screened=float(eligible[footprint].mean()),
                         best_iou_any_proposal=float(any_iou), best_iou_top5=float(sel_iou),
                         top5_rank=sel_rank if sel_iou >= 0.5 else None, intervals=listed))
    return rows


def ring_mask(footprint, common, exclude=None, inner=RING_INNER_PX, outer=RING_OUTER_PX):
    """Pixels between ``inner`` and ``outer`` pixels from the footprint, inside the common mask."""
    distance = distance_transform_edt(~np.asarray(footprint, bool))
    ring = (distance > inner) & (distance <= outer) & np.asarray(common, bool)
    if exclude is not None:
        ring &= ~np.asarray(exclude, bool)
    return ring


def ring_comparison(hh, hv, footprint, ring, dates):
    """Per consecutive interval: candidate vs surrounding-ring median change (both raw)."""
    rows = []
    for i in range(len(dates) - 1):
        dh = hh[i + 1] - hh[i]; dv = hv[i + 1] - hv[i]
        c_h, r_h = float(np.median(dh[footprint])), float(np.median(dh[ring]))
        c_v, r_v = float(np.median(dv[footprint])), float(np.median(dv[ring]))
        rows.append(dict(start=dates[i], end=dates[i + 1], candidate_dHH_db=c_h, ring_dHH_db=r_h, candidate_minus_ring_dHH_db=c_h - r_h,
                         candidate_dHV_db=c_v, ring_dHV_db=r_v, candidate_minus_ring_dHV_db=c_v - r_v,
                         ring_pixels=int(ring.sum()), candidate_pixels=int(footprint.sum())))
    return rows
