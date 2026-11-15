# Phase 5 — Change Investigation Engine

## Protected version and scope

Recoverable Git checkpoint `7b34b787233bc152b08d854691f227180adb11f5`, tag
`pre-investigation-phase5`, preserves the working Phase4 application. Dulwich in
the existing venv was reused for the standard Git checkpoint; secrets, venv and
caches were excluded. Baseline:71 passing tests. All364 previous scientific data
files are protected by SHA-256 fingerprints in `preserved_hashes.json`.

No NASA or other scientific datasets were downloaded. The engine reads the
existing six-date matched HH/HV cube and Phase4 diagnostic summaries only.
The actual common six-date footprint is138,779 finite-positive pixels,
**13.8779 km²**, on the existing10 m EPSG:32615 grid. This is the original small
Louisiana study area, not the larger two-date geographic map. Existing water-change
algorithms, default measurements, HH/HV outputs and benchmark results are unchanged.

## Prespecified, explainable selection

The following rules were declared before examining the region results:

1. Use the five consecutive acquisition intervals on the common six-date mask.
   The cached data already use the existing3×3 normalized linear-power mean
   followed by10 log10. No second logarithm or scene-median subtraction is used.
2. A seed pixel must have absolute HH change **≥3 dB AND strictly above the
   scene's90th percentile of absolute HH change for that interval**. Strictly
   above is intentional: a spatially uniform scene shift has no localized tail.
3. Split increases/decreases, and label four-connected components separately
   within each interval. Keep at least25 native cells (0.0025 km²). No dilation,
   gap filling or grouping opposite-sign/different-date pixels is performed.
4. On each fixed proposal footprint, calculate all six HH/HV spatial medians and
   IQRs, median pixel temporal ranges, five median pixel-wise interval changes,
   and the count of intervals whose regional median passes the same magnitude
   and scene-tail criteria. Report sampled post-seed departures as a separate
   descriptive persistence feature.
5. Rank lexicographically: notable-interval count descending, area descending,
   maximum absolute regional-median HH interval change descending, then fixed
   date/location tie-breaks. There is no weighted/calibrated score. Greedily keep
   up to five proposals with no selected-pixel overlap and native centroids
   at least100 m apart. Do not merge footprints or force five results.

HH drives screening because the calibrated HV floor remains unresolved. HV
patterns and HH/HV differences are reported as observations, not used to assert
a specific process or enhance a confidence score. Scene medians/quantiles and
the Phase4 original-pair temporal-scaled gate are context only. That diagnostic
gate's overlap is reported separately and does not drive the ranking.

The percentile rule deliberately selects an AOI-relative tail; it is not a false
alarm probability or evidence of statistical significance. Consecutive intervals
have unequal12/24-day gaps. Four notable intervals need not be four independent
events: one unusual acquisition can create both a rise and a fall. Ranking
favors temporal variability and spatial support, not ecological importance.

## Actual selected regions

The rules generated **268 eligible event-components**, including overlapping
proposals from different dates. The redundancy rule selected **five** footprints.
Their combined native area is0.0856 km², a radar-investigation footprint total,
not water extent or environmental damage area.

| Order | Representative longitude | Latitude | Native area km² | Notable intervals | Largest absolute median HH interval change dB |
|---|---:|---:|---:|---:|---:|
| 1 | −90.264745 | 29.910969 | 0.0074 | 4/5 | 5.966 |
| 2 | −90.268822 | 29.920885 | 0.0030 | 4/5 | 8.772 |
| 3 | −90.263313 | 29.917884 | 0.0464 | 3/5 | 4.404 |
| 4 | −90.260718 | 29.923783 | 0.0158 | 3/5 | 4.732 |
| 5 | −90.262286 | 29.921380 | 0.0130 | 3/5 | 4.982 |

The first two rank ahead of the larger third footprint because interval count
is the first declared criterion. Region1 then precedes region2 because74 cells
exceed30 cells; region2's larger peak change does not reverse that rule.

Region1's largest notable interval is July3→July15: median pixel HH change
**+5.966 dB**, HV **+4.055 dB**. Its HH spatial medians over six dates are
−13.852,−15.473,−8.528,−12.588,−8.119,−14.964 dB, showing sampled alternating
behavior rather than evidence of continuously persistent water. Median pixel
six-date ranges are7.795 dB HH and5.288 dB HV. The longest sampled same-direction
≥3 dB departure run after its seed event is one observed date.

Region2's largest notable interval is July27→August20: HH **+8.772 dB**, HV
**+3.544 dB**. The other candidates' largest HH intervals are June21→July3
(region3/4) and July15→July27 (region5). Full actual timestamps, signed HH/HV
changes, spatial IQRs and product IDs are retained for every region.

Representative points lie inside each actual polygon; they are not necessarily
polygon centroids. Areas come from native projected cell counts, not degrees.
Region4 touches the processed boundary, so its observed area is clipped and
does not establish the full physical feature extent. This warning appears in
its explanation/export. Other selected footprints do not touch that boundary.
An initial strict geographic containment test exposed tiny long-edge reprojection
chords; native edges were densified at10 m before transforming to WGS84. Selected
cells, statistics, areas and ranking were unchanged by this geometry correction.

## Setting sensitivity and uncertainty

Nine declared scenarios combine1/3/5-pixel linear filters with2.5/3/3.5 dB
magnitude floors. Each recomputes its scene percentile and applies the same
connectivity/size rule. Retention counts refer to cells of the fixed selected
footprint that remain part of eligible connected regions in any interval;
they do not imply recovery of exactly the same polygon. Candidates are not
reranked or discarded to optimize a visually successful outcome.

| Region | Original cells | Minimum–maximum retained across nine settings |
|---|---:|---:|
| 1 | 74 | 53–74 |
| 2 | 30 | 8–30 |
| 3 | 464 | 0–464 |
| 4 | 158 | 7–158 |
| 5 | 130 | 53–130 |

Region3 is particularly dependent on preprocessing under this screening rule;
its unfiltered variants retain zero cells. This is not hidden by the ranking.
Setting retention is **not calibrated confidence or independent validation**.
Smoothing changes spatial support and the scene percentile, so retention need
not vary monotonically. The Phase4 strong sensitivity and unresolved scattering
causes remain applicable. A heuristic minimum component size does not establish
statistical independence for overlapping filtered radar cells.

Candidates are not automatically verified wetlands. No independent wetland or
land-cover mask was introduced; artificial targets or mixed land cover are also
possible. OSM provides geographic context, not date-matched scientific validation.
Moisture, canopy/vegetation structure, roughness/wind, drainage/tides, geometry,
registration, provisional processing and residual speckle are competing causes.
The HH/HV contrast cannot establish flooding, damage or ecological degradation.

The engine can miss gradual cumulative changes, spatially uniform changes and
smaller footprints. Unselected locations are not verified stable. Sparse dates
do not establish continuous conditions between passes. Quality windows were
inspected for only the original pair, and available noise metadata describe DN²
without a verified gamma-0 conversion. No new confidence, risk, accuracy or
noise-floor estimate is produced. Sentinel-1 benchmark scores remain separate.

Each report suggests obtaining an independent date-matched optical/water
reference over the exact polygon around its largest notable interval. If none
exists, document the reference gap and obtain local observations before making
a causal interpretation. No reference download or validation claim was made.

## Investigator workflow and exports

The optional **Investigation Explorer** workspace provides five numbered polygons,
a representative-point marker for each, actual processed boundary, zoom/pan,
layer visibility and context popups. Select a numbered region **from the list**
to update its highlight, metrics, HH/HV time chart, dates, selection explanation,
setting sensitivity and next scientific step. Map clicks provide context rather
than pretending to update the backend selection. The initial view fits candidates;
zoom out to inspect the full processed footprint.

Charts use actual acquisition times and spatial median/IQR on the same cells,
without interpolating missing time. Every selected cell has all six valid
observations; invalid cells are excluded before screening. IQR bars are spatial
spread, not confidence intervals. Original water areas are not mixed with
investigation-region areas or the Sentinel-1 benchmark.

The Markdown download contains the selected coordinates/area, real observed
statistics/dates, full product provenance, selection/ranking rules, sensitivity,
interpretations, limitations and a suggested next step. Separate Markdown files
for all five regions are retained. The actual browser download for region3 was
saved normally to Downloads, compared byte-for-byte with its local report and
copied here as `browser_download_region_3.md`; it matched the selected region.
No PDF, new dependency or credential cache was added.

## Files and verification

Modified existing files: `app.py` and README only. New source:
`src/investigation.py`, `src/investigation_panel.py`,
`scripts/build_investigations.py`, `tests/test_investigation.py`.
Outputs are confined to this directory, apart from the requested browser export:
`results.json`, `regions.geojson`, `region_labels.tif`, five Markdown reports,
fingerprints, run/test logs, actual download copy and browser previews.

**81 tests passed** (71 existing+10 new). They check deterministic ranking,
overlap/spacing suppression, same-sign four-connectivity, identical/uniform/
small/invalid inputs producing no fabricated regions, real cached recomputation,
native areas, geographic containment/representative points, boundary clipping,
HH/HV temporal values/ranges, exports, numbered map HTML, list selection,
no-candidate/missing-file messages, original workspaces and prior data hashes.
Synthetic values are restricted to unit fixtures. Actual browser checks cover
region1→region3 metric/plot updates, five real map markers, layer visibility,
zoom and the verified Markdown download; other interactions are recorded in
`verification.json`. No claim is made about other browser engines/devices.

Existing algorithms and defaults remain intact, including0.0569/0.0005 km²
original water-change candidate areas and all benchmark values. App loading
uses cached summaries/HTML, never credentials or NASA data access. OSM/Leaflet
assets require internet. Computation/startup peak memory was not benchmarked.

**Ready for a final exploratory researcher-workflow demonstration**, with the
above limitations visible. Independent environmental interpretation remains
unvalidated. Phase5 stops here: no deployment, rebranding or presentation assets.
