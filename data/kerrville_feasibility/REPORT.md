# Kerrville data feasibility — NO-GO for validated flood extent

## Research AOI and scope

Exact WGS84 box: −99.18 to −99.10 longitude, 30.01 to 30.09 latitude, centered on Kerrville/Guadalupe and nearby waterways. All research is separate here; Louisiana inputs, pipeline, dashboard and scientific outputs are unchanged. No geographic map or classification for Texas was generated. No full NISAR HDF5 was downloaded.

ASF GCOV production search: July1 00:00 through August16 00:00 UTC (includes August15). No query reached its result limit. Seven real provisional products were returned. All have frequency-A HH/HV, frequency-B HH/HV, bandwidth4005/DHDH, sourceA, release P05023. Footprint coverage is the catalog geometry intersection with the AOI in EPSG:32614, not a guarantee of valid raster pixels.

| Acquisition start UTC | Full product ID | Track/frame, direction | Nominal AOI footprint coverage |
|---|---|---|---:|
| 2026-07-06T01:26:49Z | `NISAR_L2_PR_GCOV_024_142_D_073_4005_DHDH_A_20260706T012649_20260706T012723_P05023_N_F_J_001` | 142/73 DESCENDING | 48.21% |
| 2026-07-07T11:52:23Z | `NISAR_L2_PR_GCOV_024_163_A_017_4005_DHDH_A_20260707T115223_20260707T115258_P05023_N_F_J_001` | 163/17 ASCENDING | 100.00% |
| 2026-07-11T01:18:29Z | `NISAR_L2_PR_GCOV_025_041_D_073_4005_DHDH_A_20260711T011829_20260711T011903_P05023_N_F_J_001` | 41/73 DESCENDING | 100.00% |
| 2026-07-18T01:26:48Z | `NISAR_L2_PR_GCOV_025_142_D_073_4005_DHDH_A_20260718T012648_20260718T012723_P05023_N_F_J_001` | 142/73 DESCENDING | 48.23% |
| 2026-07-19T11:52:23Z | `NISAR_L2_PR_GCOV_025_163_A_017_4005_DHDH_A_20260719T115223_20260719T115257_P05023_N_F_J_001` | 163/17 ASCENDING | 100.00% |
| 2026-07-23T01:18:28Z | `NISAR_L2_PR_GCOV_026_041_D_073_4005_DHDH_A_20260723T011828_20260723T011903_P05023_N_F_J_001` | 41/73 DESCENDING | 100.00% |
| 2026-08-12T11:52:21Z | `NISAR_L2_PR_GCOV_027_163_A_017_4005_DHDH_A_20260812T115221_20260812T115256_P05023_N_F_J_001` | 163/17 ASCENDING | 100.00% |

## Timing relative to the event

USGS 08166200 returned an actual stage time series. Within the July14–22 query, the maximum is 30.06 ft on July16 09:50 UTC (provisional P). The earliest subsequent NISAR pass is July18 01:26 UTC, 39.61 hours later; the nearest gauge sample is 4.41 ft, only 1.8 minutes from that pass. July19 NISAR is 74.04 hours after the peak with 2.81 ft at the nearest sample. Stage is local-gauge elevation, not water depth over the floodplain. One station cannot establish flood extent or rule out residual inundation.

There is no NISAR observation on July16 or July17 in this exact-AOI search. The post-event passes are better interpreted as possible recession/post-event surface observations; they do not measure the event maximum. August12 is a longer-term surface state.

Compatible pre/post 12-day pairs: July6/18 (track142/frame73, partial AOI), July7/19 (track163/frame17, nominal full AOI), July11/23 (track41/frame73, nominal full AOI). They cannot be combined across tracks as if identical viewing geometry. No scientifically suitable validated flood pair was identified. July6/18 is the earliest technical pair, but only about half of the AOI is covered; July7/19 has better footprint coverage but later recession timing. Neither is recommended as a validated inundation case.

## Independent reference availability

Exact-AOI CMR searches over July1–August15 returned **zero DSWx-S1 records** and **32 DSWx-HLS records**. Twelve targeted HLS small windows were actually range-read: two nearest sensing-time products around each useful July NISAR date, plus low-tile-cloud July9/20 alternatives. Other late July/August products were not exhaustively sampled; even a clear late reference cannot reconstruct the missed flood peak. Full collection metadata and exact query parameters are saved here.

All sampled references are 30 m categorical WTR products. Cloud/shadow, snow/ice, ocean and fill are excluded; valid classes are0,1,2. Fractions below use pixel centers inside the exact projected AOI, not tile-wide cloud metadata. Every inspected reference has a timing difference to each NISAR acquisition in reference_timing.csv.

| Actual reference acquisition UTC | Full product ID | Valid AOI fraction |
|---|---|---:|
| 2026-07-05T17:35:24.553Z | `OPERA_L3_DSWx-HLS_T14RMU_20260705T171851Z_20260720T220535Z_S2C_30_v1.1` | 0.000% |
| 2026-07-07T17:25:28.998Z | `OPERA_L3_DSWx-HLS_T14RMU_20260707T170849Z_20260721T174817Z_S2B_30_v1.1` | 36.469% |
| 2026-07-07T17:35:40.515Z | `OPERA_L3_DSWx-HLS_T14RMU_20260707T172721Z_20260709T144548Z_S2A_30_v1.1` | 0.000% |
| 2026-07-10T17:35:24.232Z | `OPERA_L3_DSWx-HLS_T14RMU_20260710T171859Z_20260713T102327Z_S2B_30_v1.1` | 0.000% |
| 2026-07-10T17:02:31.671Z | `OPERA_L3_DSWx-HLS_T14RMU_20260710T170231Z_20260713T123101Z_L9_30_v1.1` | 0.000% |
| 2026-07-17T17:25:30.744Z | `OPERA_L3_DSWx-HLS_T14RMU_20260717T170849Z_20260719T041454Z_S2B_30_v1.1` | 0.000% |
| 2026-07-17T17:08:49.312Z | `OPERA_L3_DSWx-HLS_T14RMU_20260717T170849Z_20260719T015906Z_L9_30_v1.1` | 0.000% |
| 2026-07-18T17:02:28.103Z | `OPERA_L3_DSWx-HLS_T14RMU_20260718T170228Z_20260720T045221Z_L8_30_v1.1` | 0.000% |
| 2026-07-20T17:35:25.611Z | `OPERA_L3_DSWx-HLS_T14RMU_20260720T171859Z_20260727T174922Z_S2B_30_v1.1` | 0.000% |
| 2026-07-24T17:15:05.611Z | `OPERA_L3_DSWx-HLS_T14RMU_20260724T171505Z_20260726T022312Z_L9_30_v1.1` | 0.000% |
| 2026-07-24T17:25:48.402Z | `OPERA_L3_DSWx-HLS_T14RMU_20260724T171721Z_20260728T004601Z_S2A_30_v1.1` | 0.007% |
| 2026-07-09T17:08:35.773Z | `OPERA_L3_DSWx-HLS_T14RMU_20260709T170835Z_20260712T112028Z_L8_30_v1.1` | 99.974% |

July7 S2B offers partial valid pre-event coverage (~36.47%). July9 Landsat8 is nearly complete (~99.97%) but is ~53 h after July7 NISAR or ~80 h after July6. July17 windows are entirely cloud/shadow; July18 and July20 are entirely NoData in the AOI. In particular, the July20 catalog tile reports 0% cloud but provides no AOI data: a clear tile attribute is not usable local coverage. July24 sampled coverage is also effectively unusable. There is no verified useful pre/post reference pair for the NISAR event timing. No agreement, flood area or accuracy was computed.

## Decision

**NO-GO for a scientifically validated flood-extent demonstration using this AOI/date inventory.** Kerrville has a documented flood and a gauge, so event timing is clearer than Louisiana. However, NISAR misses the measured peak and post-event independent references fail local coverage checks. It is not scientifically preferable for the intended validated demonstration. It might support an explicitly unvalidated recession or longer-term change study, which is a different objective.

No region switch is recommended on the present evidence. Preserve the Louisiana demo with its scientific warnings. Any new case search should require concurrent valid radar and independent-reference windows, rather than selecting a documented event first and assuming usable imagery.

## Checks and records

All historical Louisiana scientific-file hashes match. Catalog footprints were measured in projected metres. Each reference class count sums to its AOI pixel count, and timing offsets are computed from acquisition timestamps (not processing timestamps). Source datasets retain their full IDs, URLs, product versions and UTC times. The two small NISAR HHHH checks, if complete, are in nisar_small_window_checks.json; these measure raster validity and may differ from approximate catalog footprint coverage.

Sources: [USGS gauge query](https://waterservices.usgs.gov/nwis/iv/?format=json&sites=08166200&startDT=2026-07-14&endDT=2026-07-22&parameterCd=00065), [City of Kerrville event documentation](https://www.kerrvilletx.gov/2026-Flood-Recovery), [NASA DSWx product](https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-HLS_V1).

## Completed small NISAR HHHH access checks

- 2026-07-06T01:26:49Z: frequencyA/HHHH inspected, 50.219% positive valid pixel centers in the sampled AOI window; 14,680,072 HTTPS bytes read.
- 2026-07-18T01:26:48Z: frequencyA/HHHH inspected, 50.278% positive valid pixel centers in the sampled AOI window; 15,728,648 HTTPS bytes read.

Both sampled rasters use EPSG:32614 at 10 m. Their roughly 50% valid raster coverage is distinct from the approximate 48.2% catalog footprint intersection; neither is full-AOI evidence. No full HDF5 or new map was saved.
