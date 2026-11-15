# Placebo (null) check for the five Louisiana candidates: method

Written and fixed on 2026-11-15 **before** any placebo result was computed. Code: `src/placebo.py` (pure functions),
`scripts/process_placebo.py` (writes `data/placebo/`). Nothing here changes the saved candidates, the screening or any
saved output.

## Question

How unusual is a candidate's contrast with its surroundings, compared with random regions of the same size and shape in
the same interval? **It does not tell us why.** This is a descriptive comparison, not a significance test, and not
evidence of a physical cause.

## Inputs (all existing, unchanged)

- Filtered HH/HV cube and all-date common valid mask: `src.polarization.load_polarization('data/polarization_analysis/six_date')`
  (3x3 mask-aware linear-power mean, then dB).
- Candidate footprints: `data/investigation_engine/region_labels.tif` (ids 1-5) and their seed intervals
  (`data/investigation_engine/results.json`, `seed_interval`).
- Ring: `src.robustness.ring_mask(footprint, common, exclude=<all saved candidates>)`: pixels 50-150 m from the footprint,
  inside the common mask, excluding every saved candidate. Exactly the ring used in `data/robustness_v2`.
- Statistic: `src.robustness.ring_comparison` on the candidate's seed interval: **candidate median change minus ring median
  change**, in HH and, separately, in HV. Raw, no correction.

## Null distribution

For each candidate, separately:

1. Take the candidate's exact footprint shape (its pixel pattern, not rotated or rescaled).
2. Draw **2000** random placements (top-left offsets uniform over the grid) with a fixed random generator
   (`numpy.random.default_rng(20261115 + candidate id)`).
3. Keep a placement only if:
   - every footprint pixel lies inside the common valid mask (same valid-pixel count as the real candidate, whose
     footprint is fully valid);
   - it does not overlap any of the five saved candidates;
   - its ring has at least **20** valid pixels (the minimum ring size the app already uses, `src.explore.MIN_RING_PIXELS`);
   - its offset is at least **10 pixels (100 m)** from every previously kept placement (minimum spacing).
4. For each kept placement compute the same statistic (placement minus its own ring, HH and HV, same interval).

If fewer than **200** placements are kept, the result is reported as **"not enough valid placements"** and no number is given.

## Reported per candidate

- the candidate's value (HH and HV);
- number of draws attempted, placements kept, seed;
- null median, 5th and 95th percentiles;
- **empirical exceedance fraction** = (number of placements with |value| >= |candidate value| + 1) / (placements + 1).
  This is an exceedance fraction, never a p-value, and nothing is called "significant".

All five candidates are reported, whatever the outcome. **No multiple-comparison correction is applied.**

## Known limits (shown wherever the result is shown)

- **Selection bias:** the candidates were *selected* because they changed a lot in this interval; random regions were not.
  A candidate looking unusual against random regions is therefore expected and is an incomplete comparison.
- **Spatial autocorrelation:** neighbouring regions are not independent. The 100 m minimum spacing is a simplification;
  rings of nearby placements can still overlap.
- Same grid, same interval, same footprint shape only; it says nothing about other intervals, places or causes.
- No independent reference exists for this area and these dates; nothing here confirms water, flooding or land-cover change.

## Not done

The optional "apply the unchanged screening to the other intervals" comparison was **skipped**: it would add a second,
differently selected population and complicate the story without answering the question above.
