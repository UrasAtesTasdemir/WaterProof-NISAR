# Milestone 6 — independent satellite validation attempt

## Outcome

The two cached Louisiana NISAR observations cannot currently be quantitatively validated as water-change detections with the inspected references. No confusion matrix, precision, recall, F1, IoU or expansion/recession agreement is reported. This is an unavailable validation, not a failed accuracy test. No dashboard change, regional switch or large product download occurred.

## Search and actual access

Exact Louisiana AOI: longitude −90.310020 to −90.250797, latitude 29.902604 to 29.924476. NASA CMR searches covered June 15 through July 9 inclusive, returning three S1 and sixteen HLS catalog records. June16 S1 is farther from both target dates and was not downloaded. Nearest June21 and June28 S1 subsets were range-read. HLS sensing times June30 through July6 were inspected (processing duplicates deduplicated by time). The earlier quality check already inspected June21/June22 HLS windows, both entirely cloud/shadow. No assumption was made that catalog intersection means valid coverage.

All inspected subsets are EPSG:32615, 30 m grids. Bounds: easting 759660–765480 m, northing 3311010–3313620 m. Original WGS84 AOI mask has 15,424 pixel centers; the NISAR common mask projected by nearest neighbor defines the comparison denominator. Coverage below is usable reference fraction, not accuracy.

| Reference acquisition UTC | Full product identifier | Relative time to closest NISAR | Valid common AOI coverage |
|---|---|---:|---:|
| 2026-06-21T00:10:26.000Z | `OPERA_L3_DSWx-S1_T15RYP_20260621T001010Z_20260827T184457Z_S1A_30_v1.0` | -11.14 h from 2026-06-21 | 0.00% |
| 2026-06-28T00:02:14.000Z | `OPERA_L3_DSWx-S1_T15RYP_20260628T000156Z_20260829T231643Z_S1A_30_v1.0` | -131.28 h from 2026-07-03 | 100.00% |
| 2026-06-30T16:45:15.359Z | `OPERA_L3_DSWx-HLS_T15RYP_20260630T162831Z_20260702T030402Z_S2C_30_v1.1` | -66.56 h from 2026-07-03 | 8.70% |
| 2026-07-03T16:55:11.907Z | `OPERA_L3_DSWx-HLS_T15RYP_20260703T163841Z_20260720T223436Z_S2C_30_v1.1` | +5.60 h from 2026-07-03 | 0.00% |
| 2026-07-05T16:45:14.784Z | `OPERA_L3_DSWx-HLS_T15RYP_20260705T162829Z_20260720T220732Z_S2B_30_v1.1` | +53.44 h from 2026-07-03 | 40.75% |
| 2026-07-05T16:55:28.766Z | `OPERA_L3_DSWx-HLS_T15RYP_20260705T164711Z_20260720T220641Z_S2A_30_v1.1` | +53.61 h from 2026-07-03 | 56.96% |
| 2026-07-06T16:37:41.215Z | `OPERA_L3_DSWx-HLS_T15RYP_20260706T163741Z_20260708T115045Z_L8_30_v1.1` | +77.31 h from 2026-07-03 | 0.00% |

June21 S1 has all 15,424 AOI centers in NoData class 255, despite successful HTTP 206 access and a catalog footprint intersecting the AOI. June28 S1 has 15,015 nonwater, 277 open-water and 132 inundated-vegetation centers, but precedes July3 by 131.28 hours. July3 HLS is entirely cloud/shadow. July5 optical coverage is partial and 53.4–53.6 hours later. July6 is all NoData. Catalog tile cloud percentage was not used as AOI cloud fraction.

Full product metadata, URLs, timing, masks and coverage are archived in the collection JSONs, reference_access.json, reference_inventory.csv and validation_results.json. Initial subset saving encountered a local relative-path reporting error after successful reads; cached windows were recovered, independently counted with the projected AOI mask and checked. Final inventories do not treat this as an access failure.

## Matching and evaluation policy

Both data types use a common projected CRS. Categorical reference alignment uses nearest-neighbor only, with NoData=255. S1 valid WTR codes: 0 nonwater, 1 open water, 3 inundated vegetation; HLS valid WTR codes: 0 nonwater, 1 open water, 2 partial surface water. HAND, layover/shadow, ocean, cloud/shadow, snow and NoData codes are excluded. Missing coverage is never nonwater.

A conservative policy was declared before metric computation: absolute time gap ≤24 hours and ≥80% common valid AOI coverage. It is an analysis guardrail, not a universal validation standard; tides, water dynamics and class meanings still need checking. No inspected product satisfies both conditions for either NISAR acquisition. Tests verify metric math on synthetic fixtures only; no synthetic metric is presented as a satellite result.

If usable matches become available, evaluation should stay on the native 30 m reference grid. Nearest-neighbor NISAR category sampling must be accompanied by mixed-pixel sensitivity and/or exclusion of ambiguous channel-edge cells; do not upsample a 30 m reference to claim nine independent 10 m samples. Open-water and inundated-vegetation agreement should be separated because low HH backscatter is not a universal vegetation-water detector.

An explicit reference-availability visualization is provided. Its gray agreement panel means NOT EVALUATED, not agreement or disagreement. No misleading cross-date error map was generated.

## Systematic darkening investigation

Original common-AOI median change: −1.3888 dB. For a 30 m diagnostic, filtered LINEAR NISAR power is area-averaged, then converted to dB; categorical reference masks are nearest-aligned. AOI pixel centers and essentially complete NISAR pixel support are required. Reference-stable-looking proxies use June28 S1 and July5 S2A-HLS; these are later/offset observations, not proof of stability on June21/July3.

| Diagnostic support | Native 30 m cells | Median NISAR change |
|---|---:|---:|
| all_common_30m | 15239 | -1.3446 dB |
| nonwater_in_both_later_references_proxy | 8106 | -1.4234 dB |
| open_water_in_both_later_references_proxy | 31 | -1.7296 dB |

Widespread darkening remains in reference-nonwater proxies, so it is not confined to detected water. It does not identify the cause. Same track105/frame017, bandwidth4005, HH-containing DHDH and processing CRID P05023 reduce obvious acquisition-configuration mismatch. Grids match; the previous ±2-pixel structural test peaks at zero offset, but subpixel error is unresolved. Calibration gain/angle metadata, water dynamics, vegetation/moisture and weather/tides were not independently resolved. A spatially uniform offset is not established sensor bias. No normalization is applied.

USGS site discovery in the exact AOI found 07380310, Bayou Verret Western Tie-in Sector Gate. A historical gage-height (00065) query for June20–July4 returned no series. Supporting hydrological state could therefore not be quantified; this is not evidence that levels were unchanged. Raw query/response and summary are saved. Historical NHD remains location context, not flood truth.

## Study-area decision

**A:** Keep Louisiana only as an explicitly unvalidated exploratory demo. The current dates do not support credible water-change agreement evaluation.

**B:** Only June21 and July3 NISAR observations are cached. There is no alternate date pair among existing processed observations. Other catalog scenes are not additional cached observations.

**C — one proposed alternative:** Guadalupe River near Kerrville, Texas, July 2026 flooding. The event is documented by the City of Kerrville and NOAA/NWS. Metadata-only candidate location: point −99.14°, 30.05°, independent-reference search box −99.18,30.01 to −99.10,30.09. These are recommendation checks only; the project AOI has not changed.

The ASF catalog returned six GCOV observations in July. A compatible ascending pair on track163/frame017, 4005/DHDH, P05023 is accessible. Two independent optical products also passed HTTP 206 byte-range access checks:

| Product | Acquisition UTC | Access verification |
|---|---|---|
| `NISAR_L2_PR_GCOV_025_163_A_017_4005_DHDH_A_20260719T115223_20260719T115257_P05023_N_F_J_001` | 2026-07-19T11:52:23Z | 8-byte HDF5 signature verified |
| `NISAR_L2_PR_GCOV_024_163_A_017_4005_DHDH_A_20260707T115223_20260707T115258_P05023_N_F_J_001` | 2026-07-07T11:52:23Z | 8-byte HDF5 signature verified |
| `OPERA_L3_DSWx-HLS_T14RMU_20260709T170835Z_20260712T112028Z_L8_30_v1.1` | 2026-07-09T17:08:35.773Z | HTTP 206 range access verified |
| `OPERA_L3_DSWx-HLS_T14RMU_20260720T171859Z_20260727T174922Z_S2B_30_v1.1` | 2026-07-20T17:35:25.611Z | HTTP 206 range access verified |

The July9 and July20 HLS catalog tiles report 0% cloud, but their AOI pixels were NOT inspected. The reference gaps are approximately +53 h and +30 h relative to this candidate NISAR pair, so the pair is NOT yet validation-ready under the conservative policy. Other nearby-day optical products exist but are cloudier at tile scale. No S1 reference was returned in the bounded July10–25 alternative query. Temporal compatibility, small-AOI reference coverage and flood timing must be checked before committing. Accessible files and an event do not prove usable validation. Only headers and eight-byte signatures were accessed for this proposed region; no raster subset there was read.

## Next single implementation step

With user approval, perform a small-pixel-window reference/temporal suitability check for the proposed Kerrville case before acquiring NISAR subsets or switching project settings. Do not build a large-area map.

## Tests

32 tests passed, including six new reference-validation tests: known confusion matrix, invalid masks, undefined metrics, categorical nearest resampling, temporal/coverage gate and the real no-score decision. Existing 26 tests still pass. Original outputs were verified unchanged by SHA-256. See tests.log and verification.json.

## Sources

- [NASA PO.DAAC DSWx-S1](https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-S1_V1)
- [Current NASA/JPL DSWx product specifications](https://www.jpl.nasa.gov/go/opera/products/dswx-product-suite/)
- [USGS station](https://waterdata.usgs.gov/monitoring-location/USGS-07380310/)
- [City of Kerrville: July2026 flood recovery](https://www.kerrvilletx.gov/2026-Flood-Recovery)
- [NOAA/NWS July2026 hydrologic report](https://www.weather.gov/media/ewx/Hydro/MonthlyReports/E-5%20EWX%202026-07.pdf)
