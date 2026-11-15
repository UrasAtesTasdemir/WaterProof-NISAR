# FloodPulse NISAR — Investigation region 5

**Investigation candidate only. NOT confirmed flooding, environmental damage, flood risk or calibrated confidence.**

Representative WGS84 point: -90.262286, 29.921380 (longitude, latitude).
Approximate native-grid area: 0.0130 km² (130 cells; EPSG:32615, 10 m pixel spacing).

## Why investigate

3/5 region-median intervals exceed both the 3 dB floor and their scene absolute-change 90th percentile; 130 same-interval/direction 4-connected cells. Rank then favors area and magnitude, not environmental risk.

Largest median HH interval: 2026-07-15 to 2026-07-27; HH -4.982 dB, HV -1.262 dB. Different channel responses do not identify a physical cause.

Longest run of observed same-direction ≥3dB departures after the seed event: 1 sampled dates. Sparse observations do not establish continuous persistence.

Median pixel-wise six-date range: HH 6.731 dB; HV 3.315 dB.

## Actual temporal observations

| Acquisition UTC | HH median dB | HV median dB | Valid cells |
|---|---:|---:|---:|
| 2026-06-21T11:19:06+00:00 | -8.5042 | -17.7540 | 130 |
| 2026-07-03T11:19:05+00:00 | -13.2841 | -20.0155 | 130 |
| 2026-07-15T11:19:05+00:00 | -9.2649 | -19.0159 | 130 |
| 2026-07-27T11:19:04+00:00 | -14.5530 | -20.2221 | 130 |
| 2026-08-20T11:19:03+00:00 | -14.8673 | -20.8881 | 130 |
| 2026-09-01T11:19:03+00:00 | -13.8992 | -20.6861 | 130 |

## Consecutive interval statistics

| Dates | Median pixel ΔHH dB | Median pixel ΔHV dB | Scene median ΔHH dB | Notable |
|---|---:|---:|---:|---|
| 2026-06-21 → 2026-07-03 | -4.7747 | -2.0804 | -1.3888 | True |
| 2026-07-03 → 2026-07-15 | 3.6824 | 0.7331 | 0.6656 | True |
| 2026-07-15 → 2026-07-27 | -4.9822 | -1.2619 | -0.8813 | True |
| 2026-07-27 → 2026-08-20 | -0.2603 | -0.7056 | -0.2906 | False |
| 2026-08-20 → 2026-09-01 | 0.6736 | 0.1741 | 1.0342 | False |

Medians of pixel differences need not equal differences of region medians. No scene median is subtracted.

## Sensitivity of this fixed footprint

| Linear filter side | Magnitude floor dB | Cells still screened in any interval | Original cells |
|---|---:|---:|---:|
| 1 | 2.5 | 53 | 130 |
| 1 | 3.0 | 53 | 130 |
| 1 | 3.5 | 53 | 130 |
| 3 | 2.5 | 130 | 130 |
| 3 | 3.0 | 130 | 130 |
| 3 | 3.5 | 122 | 130 |
| 5 | 2.5 | 125 | 130 |
| 5 | 3.0 | 123 | 130 |
| 5 | 3.5 | 120 | 130 |

Retention is setting sensitivity, not confidence; candidates are not reranked to maximize a result.

## Criteria and provenance

```json
{
  "magnitude_floor_db": 3.0,
  "scene_percentile": 90.0,
  "minimum_pixels": 25,
  "connectivity": 4,
  "maximum_regions": 5,
  "minimum_centroid_separation_m": 100.0,
  "linear_filter_size": 3
}
```

Ranking: recurrence count descending; area descending; maximum absolute region-median HH change descending; deterministic date/location tie-break. Overlap or centers within100 m are suppressed; no merging/dilation is applied.

HH source: /science/LSAR/GCOV/grids/frequencyA/HHHH
HV source: /science/LSAR/GCOV/grids/frequencyA/HVHV
Matched finite-positive all-six-date mask; 3×3 normalized linear-power mean before 10 log10; dB data are not converted twice.

- 2026-06-21T11:19:06+00:00: `NISAR_L2_PR_GCOV_023_105_A_017_4005_DHDH_A_20260621T111906_20260621T111941_P05023_N_F_J_001`
- 2026-07-03T11:19:05+00:00: `NISAR_L2_PR_GCOV_024_105_A_017_4005_DHDH_A_20260703T111905_20260703T111940_P05023_N_F_J_001`
- 2026-07-15T11:19:05+00:00: `NISAR_L2_PR_GCOV_025_105_A_017_4005_DHDH_A_20260715T111905_20260715T111940_P05023_N_F_J_001`
- 2026-07-27T11:19:04+00:00: `NISAR_L2_PR_GCOV_026_105_A_017_4005_DHDH_A_20260727T111904_20260727T111939_P05023_N_F_J_001`
- 2026-08-20T11:19:03+00:00: `NISAR_L2_PR_GCOV_028_105_A_017_4005_DHDH_A_20260820T111903_20260820T111938_P05023_N_F_J_001`
- 2026-09-01T11:19:03+00:00: `NISAR_L2_PR_GCOV_029_105_A_017_4005_DHDH_A_20260901T111903_20260901T111937_P05023_N_F_J_001`

## Interpretations, uncertainty and next step

Changing surface/canopy moisture, vegetation structure, open-water roughness/wind, drainage/tides, geometry, processing or residual speckle are competing hypotheses; none is established.

- Investigation candidates only; NOT confirmed floods, risk predictions or environmental damage assessments.
- Ranking is a descriptive heuristic, not confidence, probability, accuracy or ecological importance.
- The same observations select and describe candidates; extreme values and percentile-tail selection are not independent validation.
- Six irregular dates cannot establish continuous persistence or capture every short-lived event.
- Notable adjacent intervals are not independent recurring events; one anomalous date can create both a rise and a fall.
- Screening favors abrupt localized changes and can miss gradual, scene-wide or smaller-footprint changes; an unselected area is not verified stable.
- HH drives spatial screening. HV is descriptive; its calibrated noise floor remains unresolved because available noise metadata are DN^2.
- Speckle, smoothing, mixed pixels, moisture, vegetation, wind, drainage/tides, registration and provisional processing can influence scattering.
- Phase4 found strong threshold/filter sensitivity and regional darkening differences; no scene-median normalization is applied.
- Finite-positive common masks cover all six dates; detailed GCOV quality windows were inspected only for the original pair.
- Sentinel-1 benchmark scores do not establish NISAR HH/HV accuracy. Independent date-matched validation remains unavailable.

Obtain an independent date-matched optical/water reference over this exact polygon for 2026-07-15–2026-07-27; if unavailable, document the gap and request local observations before attributing a cause.
