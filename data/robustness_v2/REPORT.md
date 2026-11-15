# Robustness checks (version 2) for the five Louisiana investigation candidates

Offline, from cached real NISAR GCOV data (six dates, HH and HV). Script: `scripts/process_robustness.py`. Screening and ranking reuse `src/investigation.py` unchanged. **Robustness is not validation**: the same observations select and test the candidates.

**What changed from version 1 (`data/robustness/`, kept unchanged):** the leave-one-date-out check now looks only at the interval that contains the original seed event (merged across the removed date when needed). Version 1 counted a same-direction notable change in any remaining interval.

Acquisition gap: 2026-07-27 → 2026-08-20 is 24 days (1 acquisition missing).

| Candidate | Seed change | (a) top 5 in variants | (b) same seed in variants | Date removals: seed event still notable | not notable | not testable | Candidate − ring ΔHH at seed (dB) |
|---|---|---:|---:|---:|---|---|---:|
| 1 | 2026-07-03 → 2026-07-15 (increase) | 27/27 | 27/27 | 5/6 | 2026-07-15 | – | +5.55 |
| 2 | 2026-07-15 → 2026-07-27 (decrease) | 5/27 | 9/27 | 4/6 | 2026-07-15, 2026-07-27 | – | -3.65 |
| 3 | 2026-06-21 → 2026-07-03 (decrease) | 3/27 | 11/27 | 4/6 | 2026-07-03 | 2026-06-21 | -1.92 |
| 4 | 2026-07-03 → 2026-07-15 (increase) | 5/27 | 9/27 | 4/6 | 2026-07-03, 2026-07-15 | – | +1.32 |
| 5 | 2026-07-03 → 2026-07-15 (increase) | 4/27 | 9/27 | 4/6 | 2026-07-03, 2026-07-15 | – | +1.77 |

## Leave one date out: interval that carries the seed event

| Candidate | Removed date | Seed-event interval | Days | Median ΔHH (dB) | Status | Other same-direction notable intervals (not counted) |
|---|---|---|---:|---:|---|---|
| 1 | 2026-06-21 | 2026-07-03 → 2026-07-15 | 12 | +5.97 | still notable in the seed direction | 2026-07-27 → 2026-08-20 |
| 1 | 2026-07-03 | 2026-06-21 → 2026-07-15 | 24 | +4.30 | still notable in the seed direction | 2026-07-27 → 2026-08-20 |
| 1 | 2026-07-15 | 2026-07-03 → 2026-07-27 | 24 | +1.53 | not notable in the seed direction | 2026-07-27 → 2026-08-20 |
| 1 | 2026-07-27 | 2026-07-03 → 2026-07-15 | 12 | +5.97 | still notable in the seed direction | – |
| 1 | 2026-08-20 | 2026-07-03 → 2026-07-15 | 12 | +5.97 | still notable in the seed direction | – |
| 1 | 2026-09-01 | 2026-07-03 → 2026-07-15 | 12 | +5.97 | still notable in the seed direction | 2026-07-27 → 2026-08-20 |
| 2 | 2026-06-21 | 2026-07-15 → 2026-07-27 | 12 | -4.91 | still notable in the seed direction | 2026-08-20 → 2026-09-01 |
| 2 | 2026-07-03 | 2026-07-15 → 2026-07-27 | 12 | -4.91 | still notable in the seed direction | 2026-08-20 → 2026-09-01 |
| 2 | 2026-07-15 | 2026-07-03 → 2026-07-27 | 24 | -0.99 | not notable in the seed direction | 2026-08-20 → 2026-09-01 |
| 2 | 2026-07-27 | 2026-07-15 → 2026-08-20 | 36 | +2.15 | not notable in the seed direction | 2026-08-20 → 2026-09-01 |
| 2 | 2026-08-20 | 2026-07-15 → 2026-07-27 | 12 | -4.91 | still notable in the seed direction | – |
| 2 | 2026-09-01 | 2026-07-15 → 2026-07-27 | 12 | -4.91 | still notable in the seed direction | – |
| 3 | 2026-06-21 | – | – | – | not testable: the seed event is not observable without this date | 2026-07-15 → 2026-07-27 |
| 3 | 2026-07-03 | 2026-06-21 → 2026-07-15 | 24 | -1.47 | not notable in the seed direction | 2026-07-15 → 2026-07-27 |
| 3 | 2026-07-15 | 2026-06-21 → 2026-07-03 | 12 | -4.40 | still notable in the seed direction | – |
| 3 | 2026-07-27 | 2026-06-21 → 2026-07-03 | 12 | -4.40 | still notable in the seed direction | 2026-07-15 → 2026-08-20 |
| 3 | 2026-08-20 | 2026-06-21 → 2026-07-03 | 12 | -4.40 | still notable in the seed direction | 2026-07-15 → 2026-07-27 |
| 3 | 2026-09-01 | 2026-06-21 → 2026-07-03 | 12 | -4.40 | still notable in the seed direction | 2026-07-15 → 2026-07-27 |
| 4 | 2026-06-21 | 2026-07-03 → 2026-07-15 | 12 | +3.49 | still notable in the seed direction | – |
| 4 | 2026-07-03 | 2026-06-21 → 2026-07-15 | 24 | -0.95 | not notable in the seed direction | – |
| 4 | 2026-07-15 | 2026-07-03 → 2026-07-27 | 24 | -1.04 | not notable in the seed direction | – |
| 4 | 2026-07-27 | 2026-07-03 → 2026-07-15 | 12 | +3.49 | still notable in the seed direction | – |
| 4 | 2026-08-20 | 2026-07-03 → 2026-07-15 | 12 | +3.49 | still notable in the seed direction | – |
| 4 | 2026-09-01 | 2026-07-03 → 2026-07-15 | 12 | +3.49 | still notable in the seed direction | – |
| 5 | 2026-06-21 | 2026-07-03 → 2026-07-15 | 12 | +3.68 | still notable in the seed direction | – |
| 5 | 2026-07-03 | 2026-06-21 → 2026-07-15 | 24 | -0.89 | not notable in the seed direction | – |
| 5 | 2026-07-15 | 2026-07-03 → 2026-07-27 | 24 | -1.17 | not notable in the seed direction | – |
| 5 | 2026-07-27 | 2026-07-03 → 2026-07-15 | 12 | +3.68 | still notable in the seed direction | – |
| 5 | 2026-08-20 | 2026-07-03 → 2026-07-15 | 12 | +3.68 | still notable in the seed direction | – |
| 5 | 2026-09-01 | 2026-07-03 → 2026-07-15 | 12 | +3.68 | still notable in the seed direction | – |

## Method

- **screening**: src.investigation.event_components / describe_proposals / rank_regions, unchanged
- **area_and_rank**: (a) pixels of the fixed footprint still screened; top-5 rank and pixels of the best-overlapping selected region (IoU >= 0.5)
- **similarity**: (b) best IoU with any selected region and with any eligible proposal; same seed interval and direction
- **leave_one_date_out**: default settings on the existing filtered cube with one date removed; only the interval that contains the original seed event (merged across the removed date when needed) is checked with the existing notable-interval rule (|median ΔHH| >= 3 dB and > scene 90th percentile) in the seed direction. Same-direction changes in other intervals are listed separately and do not count. If the removed date is the first or last date and an endpoint of the seed interval, the event is not testable.
- **ring**: pixels 50-150 m from the candidate, inside the common mask, excluding all candidates; medians of raw pixel-wise change. A comparison, not a correction.

## Limitations

- Same observations select and test the candidates; robustness is not validation.
- Settings variants are sensitivity checks; no variant is preferred or tuned.
- Removing a date changes interval lengths (12 → 24 or 36 days); a change that is still notable can be a longer-term difference.
- The ring may contain different land cover from the candidate; a contrast does not identify a cause.

Files: `results.json`, `settings_sensitivity.csv`, `leave_one_date_out.csv`, `ring_comparison.csv`, `sidecar.json` (SHA-256 of sources and outputs).
