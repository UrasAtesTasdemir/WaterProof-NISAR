# Focused scientific quality check — FloodPulse NISAR

Analysis UTC: 2026-11-14T08:26:05.438278+00:00

Original results and cached observations are preserved (SHA-256 verified). No NISAR download, threshold optimization or Streamlit work was performed.

## Threshold sensitivity

All runs use the same real observations, common mask, normalized 3×3 linear-power mean and minimum absolute change of 3 dB.

| Water threshold (dB) | Expansion candidate (km²) | Recession candidate (km²) |
|---|---:|---:|
| -14 | 0.1652 | 0.0072 |
| -16 | 0.0569 | 0.0005 |
| -18 | 0.0091 | 0.0000 |
| -20 | 0.0000 | 0.0000 |

[Chart](threshold_sensitivity.png), [spatial threshold comparison](threshold_spatial_comparison.png), [candidate location context](candidate_location_context.png).

## Where the baseline candidates occur

The largest connected groups lie along the east–west dark linear corridor around latitude 29.912°, longitudes −90.276° to −90.267°, with smaller groups along intersecting channels and other dark features. Component centroid coordinates and sizes are in expansion_component_centroids.geojson. This is a radar/context interpretation, not confirmed inundation.

Of 569 expansion candidate pixels: 416 touch mapped canal/ditch or stream/river geometry and 431 fall within 30 m (441 within 60 m). Excluding swamp/marsh polygons, the broader mapped water network contains/touches 512 candidates and has 533 within 30 m. Thus most candidates are associated with previously mapped water features, not demonstrated new flooding of dry land.

The broad all-hydrography union includes historical swamp polygons and overlaps 566 candidates; this number alone would exaggerate river/canal association. Feature types are separated in quality_diagnostics.json. NHD geometries were rasterized all_touched=True at 10 m; proximity is approximate and not a validation score. Source feature attributes include historical dates, not the 2026 observation water states.

Before-date filtered HH≤−16 dB dark pixels have 197 candidates within 30 m and 387 within 60 m. This diagnostic is derived from NISAR itself and is not independent evidence.

## Reliability checks

- Both raster grids, EPSG:32615 CRS, 10 m resolution, transforms and masks match. No invalid pixel is classified as water. NaN masks remain unchanged. The best tested integer structural offset is (0,0) within a ±2-pixel search. Subpixel coregistration is not validated.
- There are 140 eight-connected expansion groups, including 61 singleton pixels; 136 candidate pixels belong to groups of at most 3 pixels. These may reflect speckle, edge effects or real narrow features; none were removed.
- Six expansion candidates have incomplete 3×3 neighborhood support at the AOI edge. No nodata filling was found. Filtering without a halo can still affect boundaries.
- At the same −16/3 dB settings, unfiltered power yields 0.3432 km² expansion candidates versus 0.0569 km² after filtering. This is processing sensitivity, not an accuracy comparison. Only 334 expansion pixels are shared. Smoothing can suppress narrow channels and move threshold boundaries.
- Common-AOI median after-minus-before backscatter is −1.3888 dB. Widespread darkening can influence asymmetric expansion/recession counts. Hydrological/surface changes and radiometric or acquisition effects need separate checks; a calibration error has not been established. No scene-wide offset was removed.

## Independent reference investigation

NASA CMR queries searched OPERA_L3_DSWX-HLS_V1 over the exact AOI for ±3 days around each target date (full query parameters and responses retained in dswx_granules_*.json). Each returned five catalog records, including processing duplicates. The independent optical product is 30 m, so narrow 10 m radar channels are mixed pixels. Catalog tile cloud cover alone was not used to judge AOI coverage. Small B01_WTR AOI windows were actually range-read and saved.

| Optical acquisition | Match | AOI pixel centers | Usable water/nonwater | Cloud/cloud-shadow |
|---|---|---:|---:|---:|
| 2026-06-21T16:31:31.238Z | same day | 15424 | 0 | 15424 |
| 2026-06-22T16:45:33.397Z | nearby day | 15424 | 0 | 15424 |
| 2026-07-03T16:55:11.907Z | same day | 15424 | 0 | 15424 |
| 2026-06-30T16:45:15.359Z | nearby day | 15424 | 1342 | 14078 |

Both same-day AOI windows consist entirely of class 253 (cloud/cloud shadow). The June 22 nearby window is also fully cloudy; June 30 has only 1,342 usable of 15,424 AOI pixels and is not date matched to either NISAR image. No reliable paired optical reference was established from these inspected data. This does not prove no other reference exists. All candidates remain independently UNVALIDATED; no accuracy metrics are reported.

Historical USGS hydrography is useful spatial context only, never proof of flooding on June 21 or July 3. DSWx-HLS is itself a classified satellite product, not ground truth; even clear, same-day acquisitions would require attention to observation time, uncertainty and resolution.

## Demo decision and required improvements

Suitable for an explicitly exploratory water-change demo, not an operational flood claim. Before the UI: (1) add clear date/quality-checked independent reference coverage, or retain an explicit unvalidated state; (2) investigate scene-wide darkening and subpixel coregistration using defensible stable controls without arbitrary offset correction; (3) review singleton/channel-edge and filter-halo effects, preserving baseline outputs; (4) expose threshold sensitivity and separate historical water context from new flood claims. Do not choose a threshold to maximize mapped area.

## Reproduction and records

Run `.venv/bin/python -B scripts/quality_check_water.py` for cached-data diagnostics and `.venv/bin/python -B scripts/inspect_water_references.py` for bounded optical pixel inspection using locally protected Earthdata authentication. Public CMR and NHD responses are archived here; the latter script uses the archived CMR discovery records. Secret tokens and signed URLs are not saved. Original-file hashes and output checks are in quality_diagnostics.json and verification.json.

## Primary references

- [NASA PO.DAAC DSWx-HLS product](https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-HLS_V1)
- [NASA OPERA visualization guide: WTR codes](https://d2pn8kiwq2w21t.cloudfront.net/documents/DSWx_visualization_guide.pdf)
- [USGS NHD feature definitions](https://www.usgs.gov/ngp-standards-and-specifications/national-hydrography-dataset-nhd-data-dictionary-feature-domains)
- [USGS NHD service](https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer)
- [USGS 3DHP and historical NHD access](https://www.usgs.gov/national-hydrography/access-national-hydrography-products)
