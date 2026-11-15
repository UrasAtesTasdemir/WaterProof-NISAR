# Robustness checks for the five Louisiana investigation candidates

Offline, from cached real NISAR GCOV data (six dates, HH and HV). Script: `scripts/process_robustness.py`. Screening and ranking reuse `src/investigation.py` unchanged. **Robustness is not validation**: the same observations select and test the candidates.

Acquisition gap: 2026-07-27 → 2026-08-20 is 24 days (one 12-day acquisition missing).

The default settings (3×3 filter, 3 dB floor, 90th percentile) reproduce all five saved regions exactly (IoU 1.0 each).

## Summary per candidate

| Candidate | Seed change | (a) top-5 in variants | (a) rank range | (a) footprint pixels still screened | (b) IoU with top-5 match | (b) same seed in variants | Date removals where change survives | Candidate − ring ΔHH at seed (dB) |
|---|---|---:|---|---|---|---:|---|---:|
| 1 | 2026-07-03 → 2026-07-15 (increase) | 27/27 | 1–2 | 53–74 | 0.52–1.00 | 27/27 | 6/6 | +5.97 vs ring +0.42 → +5.55 |
| 2 | 2026-07-15 → 2026-07-27 (decrease) | 5/27 | 2–3 | 7–30 | 0.00–1.00 | 9/27 | 6/6 | -4.91 vs ring -1.26 → -3.65 |
| 3 | 2026-06-21 → 2026-07-03 (decrease) | 3/27 | 3–4 | 0–464 | 0.00–1.00 | 11/27 | 6/6 | -4.40 vs ring -2.48 → -1.92 |
| 4 | 2026-07-03 → 2026-07-15 (increase) | 5/27 | 4–5 | 0–158 | 0.00–1.00 | 9/27 | 4/6 (not when removing 2026-07-03, 2026-07-15) | +3.49 vs ring +2.18 → +1.32 |
| 5 | 2026-07-03 → 2026-07-15 (increase) | 4/27 | 5–5 | 0–130 | 0.00–1.00 | 9/27 | 4/6 (not when removing 2026-07-03, 2026-07-15) | +3.68 vs ring +1.91 → +1.77 |

(a) = how much area/ranking changes with settings; (b) = whether the candidate stays similar. They are reported separately and never combined.

## Method

- **screening**: src.investigation.event_components / describe_proposals / rank_regions, unchanged
- **area_and_rank**: (a) pixels of the fixed footprint still screened; top-5 rank and pixels of the best-overlapping selected region (IoU >= 0.5)
- **similarity**: (b) best IoU with any selected region and with any eligible proposal; same seed interval and direction
- **leave_one_date_out**: default settings on the existing filtered cube with one date removed; the fixed footprint is checked with the existing notable-interval rule (|median ΔHH| >= 3 dB and > scene 90th percentile) in the seed direction
- **ring**: pixels 50-150 m from the candidate, inside the common mask, excluding all candidates; medians of raw pixel-wise change. A comparison, not a correction.

## Limitations

- Same observations select and test the candidates; robustness is not validation.
- Settings variants are sensitivity checks; no variant is preferred or tuned.
- Removing a date changes interval lengths (12 → 24 or 36 days); a surviving change can be a longer-term difference.
- The ring may contain different land cover from the candidate; a contrast does not identify a cause.

Files: `results.json` (all tables), `settings_sensitivity.csv`, `leave_one_date_out.csv`, `ring_comparison.csv`, `sidecar.json` (SHA-256 of sources and outputs).
