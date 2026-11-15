# FloodPulse NISAR — Investigation region 2

**Investigation candidate only. NOT confirmed flooding, environmental damage, flood risk or calibrated confidence.**

Representative WGS84 point: -90.268822, 29.920885 (longitude, latitude).
Approximate native-grid area: 0.0030 km² (30 cells; EPSG:32615, 10 m pixel spacing).

## Why investigate

4/5 region-median intervals exceed both the 3 dB floor and their scene absolute-change 90th percentile; 30 same-interval/direction 4-connected cells. Rank then favors area and magnitude, not environmental risk.

Largest median HH interval: 2026-07-27 to 2026-08-20; HH +8.772 dB, HV +3.544 dB. Different channel responses do not identify a physical cause.

Longest run of observed same-direction ≥3dB departures after the seed event: 1 sampled dates. Sparse observations do not establish continuous persistence.

Median pixel-wise six-date range: HH 9.476 dB; HV 6.812 dB.

## Actual temporal observations

| Acquisition UTC | HH median dB | HV median dB | Valid cells |
|---|---:|---:|---:|
| 2026-06-21T11:19:06+00:00 | -2.2269 | -12.3866 | 30 |
| 2026-07-03T11:19:05+00:00 | -6.4537 | -16.1699 | 30 |
| 2026-07-15T11:19:05+00:00 | -1.9815 | -13.1167 | 30 |
| 2026-07-27T11:19:04+00:00 | -8.1978 | -15.7876 | 30 |
| 2026-08-20T11:19:03+00:00 | 1.8399 | -10.9047 | 30 |
| 2026-09-01T11:19:03+00:00 | -7.0171 | -14.8309 | 30 |

## Consecutive interval statistics

| Dates | Median pixel ΔHH dB | Median pixel ΔHV dB | Scene median ΔHH dB | Notable |
|---|---:|---:|---:|---|
| 2026-06-21 → 2026-07-03 | -1.6051 | -2.6658 | -1.3888 | False |
| 2026-07-03 → 2026-07-15 | 3.4263 | 2.6884 | 0.6656 | True |
| 2026-07-15 → 2026-07-27 | -4.9063 | -2.8437 | -0.8813 | True |
| 2026-07-27 → 2026-08-20 | 8.7716 | 3.5444 | -0.2906 | True |
| 2026-08-20 → 2026-09-01 | -7.4250 | -1.8468 | 1.0342 | True |

Medians of pixel differences need not equal differences of region medians. No scene median is subtracted.

## Sensitivity of this fixed footprint

| Linear filter side | Magnitude floor dB | Cells still screened in any interval | Original cells |
|---|---:|---:|---:|
| 1 | 2.5 | 8 | 30 |
| 1 | 3.0 | 8 | 30 |
| 1 | 3.5 | 8 | 30 |
| 3 | 2.5 | 30 | 30 |
| 3 | 3.0 | 30 | 30 |
| 3 | 3.5 | 30 | 30 |
| 5 | 2.5 | 22 | 30 |
| 5 | 3.0 | 22 | 30 |
| 5 | 3.5 | 21 | 30 |

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

Obtain an independent date-matched optical/water reference over this exact polygon for 2026-07-27–2026-08-20; if unavailable, document the gap and request local observations before attributing a cause.
