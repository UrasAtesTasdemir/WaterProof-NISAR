# Milestone 7 — Louisiana observation-pair selection

## Decision

NO-GO for a robust full-AOI independent before/after water-change validation with the six specified dates and inspected references. No suitable accepted pair is invented. The six catalog dates remain useful for an exploratory radar time series; only June21/July3 NISAR arrays are currently cached. No additional NISAR raster was read or HDF5 downloaded. The dashboard and scientific algorithm are unchanged.

Partial-area single-date water-presence agreement remains possible in principle (especially September1), but it must be restricted to the valid reference footprint and labelled reference-product agreement, not full-AOI accuracy, change validation or flood truth.

## Transparent criteria and ranking

Hold radar track/frame/direction, frequency-A HH, bandwidth and processing release consistent. Inspect the exact AOI pixel masks, never infer coverage from catalog footprint or tile cloud metadata. Separate the two individual valid masks from their spatial intersection. Use native projected 30m reference grids, with categorical nearest-neighbor alignment.

Conservative full-AOI guardrails retained from earlier work: absolute reference–NISAR gap ≤24 h for each date and ≥80% valid coverage both individually and jointly. These are analysis guardrails, NOT universal scientific standards. Smaller valid subareas can be studied, but do not validate the unobserved AOI. Timing needs particular care in this tidal/drainage setting. No threshold or result was optimized to increase water area.

Rank accepted change pairs first; among rejected exploratory candidates, prioritize both timing gaps ≤24 h, then larger joint support, smaller maximum time gap and shorter radar interval. Pairs with no reference-water cells on either date in their common area are not meaningful water-discrimination candidates and are excluded. At most three pairs are retained. These ranks are NOT validation scores.

| Exploratory rank | NISAR date pair | Reference acquisitions | Valid fraction separately | Joint valid AOI | Reference offsets | Result |
|---|---|---|---|---|---|
| 1 | 2026-07-15 / 2026-09-01 | 2026-07-15T16:31:31.043Z / 2026-09-01T16:31:55.343Z | 25.06% / 56.01% | 7.75% | +5.21 h / +5.21 h | Not accepted |
| 2 | 2026-08-20 / 2026-09-01 | 2026-08-21T16:45:31.558Z / 2026-09-01T16:31:55.343Z | 75.33% / 56.01% | 41.31% | +29.44 h / +5.21 h | Not accepted |
| 3 | 2026-07-15 / 2026-08-20 | 2026-07-15T16:31:31.043Z / 2026-08-21T16:45:31.558Z | 25.06% / 75.33% | 22.65% | +5.21 h / +29.44 h | Not accepted |

The best-timed July15/September1 pair has only 1,195 common valid 30m cells (7.75% AOI, approximately 1.0755 km²). Its reference-water counts are just 16 and 10; only one July15 common pixel is open water, the rest are partial-water class. This is sparse, spatially selected support for paired water discrimination. It cannot justify a robust AOI-wide change-validation claim.

August20/September1 has better common coverage (6,372 cells, 41.31%), but relies on August21 optical data ~29.44 hours after the first radar pass. It is a possible looser, explicitly asynchronous partial-area sensitivity study, not an accepted paired validation under the declared policy. The 24h cutoff is not a physical cliff: relaxing it would require independent justification of temporal stability, not merely a desire for a usable pair.

## Exact NISAR catalog observations

ASF search returned eleven GCOV provisional records over June21–September1; the six requested ascending track105/frame017 records are isolated here. Descending track156 acquisitions are not mixed into the series. The six products share A/B HH/HV, 4005/DHDH and P05023. Catalog footprints cover the original AOI, but later-date HHHH pixel validity has not been checked because no radar subset was downloaded in this milestone.

| UTC acquisition | Full product ID | Track/frame |
|---|---|---|
| 2026-06-21T11:19:06Z | `NISAR_L2_PR_GCOV_023_105_A_017_4005_DHDH_A_20260621T111906_20260621T111941_P05023_N_F_J_001` | 105/017 ascending |
| 2026-07-03T11:19:05Z | `NISAR_L2_PR_GCOV_024_105_A_017_4005_DHDH_A_20260703T111905_20260703T111940_P05023_N_F_J_001` | 105/017 ascending |
| 2026-07-15T11:19:05Z | `NISAR_L2_PR_GCOV_025_105_A_017_4005_DHDH_A_20260715T111905_20260715T111940_P05023_N_F_J_001` | 105/017 ascending |
| 2026-07-27T11:19:04Z | `NISAR_L2_PR_GCOV_026_105_A_017_4005_DHDH_A_20260727T111904_20260727T111939_P05023_N_F_J_001` | 105/017 ascending |
| 2026-08-20T11:19:03Z | `NISAR_L2_PR_GCOV_028_105_A_017_4005_DHDH_A_20260820T111903_20260820T111938_P05023_N_F_J_001` | 105/017 ascending |
| 2026-09-01T11:19:03Z | `NISAR_L2_PR_GCOV_029_105_A_017_4005_DHDH_A_20260901T111903_20260901T111937_P05023_N_F_J_001` | 105/017 ascending |

## Actual independent reference windows

NASA CMR exact-AOI queries used +/-1 calendar day around each target date (including the whole following day). All results stayed below page limits. A June21 DSWx-S1 record exists but is all NoData; the five later target windows returned no S1 products. This is a bounded search result, not proof no reference exists elsewhere or at larger time offsets. HLS sensing-time processing revisions were deduplicated by retaining the latest returned version. Prior identical AOI windows were reused; new windows were HTTPS range-read. All sampled reference grids are EPSG:32615 at 30m.

Valid S1 classes:0 nonwater,1 open water,3 inundated vegetation. Valid HLS classes:0 nonwater,1 open water,2 partial surface water. Cloud/shadow, snow/ice, HAND, layover/shadow, ocean and NoData are excluded. S1 vegetation water and HLS partial water do not mean the same scattering target as low-HH open-water candidates; future agreement must separate class definitions and mixed pixels.

| NISAR date | Full independent reference product ID | Reference UTC acquisition | Valid exact AOI | Offset |
|---|---|---|---:|---:|
| 2026-06-21 | `OPERA_L3_DSWx-S1_T15RYP_20260621T001010Z_20260827T184457Z_S1A_30_v1.0` | 2026-06-21T00:10:26.000Z | 0.00% | -11.14 h |
| 2026-06-21 | `OPERA_L3_DSWx-HLS_T15RYP_20260621T163131Z_20260722T172422Z_L9_30_v1.1` | 2026-06-21T16:31:31.238Z | 0.00% | +5.21 h |
| 2026-06-21 | `OPERA_L3_DSWx-HLS_T15RYP_20260622T163711Z_20260626T153321Z_S2A_30_v1.1` | 2026-06-22T16:45:33.397Z | 0.00% | +29.44 h |
| 2026-07-03 | `OPERA_L3_DSWx-HLS_T15RYP_20260703T163841Z_20260720T223436Z_S2C_30_v1.1` | 2026-07-03T16:55:11.907Z | 0.00% | +5.60 h |
| 2026-07-15 | `OPERA_L3_DSWx-HLS_T15RYP_20260715T163131Z_20260718T071454Z_L8_30_v1.1` | 2026-07-15T16:31:31.043Z | 25.06% | +5.21 h |
| 2026-07-27 | `OPERA_L3_DSWx-HLS_T15RYP_20260728T163839Z_20260730T031807Z_S2B_30_v1.1` | 2026-07-28T16:55:13.652Z | 27.76% | +29.60 h |
| 2026-08-20 | `OPERA_L3_DSWx-HLS_T15RYP_20260819T162831Z_20260821T041327Z_S2C_30_v1.1` | 2026-08-19T16:45:13.974Z | 0.51% | -18.56 h |
| 2026-08-20 | `OPERA_L3_DSWx-HLS_T15RYP_20260821T163701Z_20260823T033117Z_S2A_30_v1.1` | 2026-08-21T16:45:31.558Z | 75.33% | +29.44 h |
| 2026-09-01 | `OPERA_L3_DSWx-HLS_T15RYP_20260901T163155Z_20260903T021841Z_L8_30_v1.1` | 2026-09-01T16:31:55.343Z | 56.01% | +5.21 h |
| 2026-09-01 | `OPERA_L3_DSWx-HLS_T15RYP_20260901T163831Z_20260903T025711Z_S2C_30_v1.1` | 2026-09-01T16:55:10.886Z | 0.00% | +5.60 h |

June21 and July3 same-day optical windows remain fully cloud/shadow masked. July15 has 3,866 valid cells, including 8 open-water and 81 partial-water cells, but covers only 25.06% of the AOI. September1 Landsat8 has 8,639 valid cells (56.01%) and useful water/nonwater representation, while the same-day Sentinel2 window is entirely cloud/shadow. The August19 window has only 78 valid cells, all nonwater; it does not validate water detection despite its closer timestamp. The August21 window is 75.33% valid but later by 29.44h.

## Presence versus change

A single-date presence comparison can describe performance only over that date’s common valid footprint. For September1, a subsequent small NISAR HHHH subset could support a limited reference-product agreement test at native 30m resolution, with cloud-selection and mixed-pixel warnings. It does not validate June21/July3 or any other change map. Two valid reference dates are necessary for change evaluation, and the SAME geographic cells must be valid on both. None of the inspected pairs provides robust full-AOI temporally matched change support. No confusion matrix, F1, accuracy or confidence metric is computed here.

## Next action

Retain the six-date catalog series as exploratory. The single proposed next implementation step is to read a small September1 NISAR HHHH AOI subset and assess SINGLE-DATE water presence only in the clear Landsat reference footprint, without changing the production dashboard or claiming paired flood validation.

## Preservation and verification

32 existing regression tests passed. Reference class counts, nearest-grid joint masks, time offsets, six compatible radar IDs and all pre-existing file hashes were checked. Production code and all previous outputs are unchanged. New files are confined to data/pair_selection/. No large-area map was produced. assess.py reproduces the assessment from archived catalogs and small windows; its first run can fetch only missing reference windows.

Primary sources: [NASA DSWx-S1](https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-S1_V1), [NASA DSWx-HLS](https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-HLS_V1), [ASF NISAR Cookbook](https://asfopensarlab.github.io/NISAR_Cookbook/search-stream-nisar-asf-search/).
