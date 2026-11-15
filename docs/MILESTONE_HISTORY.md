# FloodPulse NISAR

NASA Space Apps Challenge 2026 — Dancing with the SARs.

## Milestone 1

Simple local setup and real NASA ASF public metadata discovery only. No HDF5
download, flood detection, or advanced interface is implemented.

The project environment uses Python 3.12.0 on Apple Silicon macOS because
Python 3.11 was not available locally. System Python settings were not changed.

## PyCharm

Open this folder as a project. In Settings → Project → Python Interpreter,
select an existing local interpreter: `<project folder>/.venv/bin/python`.

From the project terminal:

```sh
.venv/bin/python scripts/verify_environment.py
.venv/bin/python scripts/search_nisar.py
# Optional minimal placeholder:
.venv/bin/python -m streamlit run app.py
```

Install dependencies in a new environment with `python -m pip install -r requirements.txt`.
`requirements-lock.txt` records the versions installed during verification.

## Data discovery

Reference: [official ASF NISAR Cookbook](https://asfopensarlab.github.io/NISAR_Cookbook/search-stream-nisar-asf-search/).
Naming and polarization definitions: [ASF GCOV guide](https://nisar-docs.asf.alaska.edu/gcov/).

The search uses the requested Louisiana polygon, UTC dates 2026-06-21 and
2026-07-03, NISAR GCOV, production configuration PR, PROVISIONAL maturity,
ascending passes, and frequency-A HH. Matching pairs must have identical
track, frame, instrument, bandwidth mode, polarization mode, and source mode.
The latest release identifier is retained per acquisition as in the Cookbook.
HH is checked in returned `mainBandPolarization` metadata and filename codes,
rather than an API polarization filter: the latter returned zero for these
HH+HV acquisitions during verification. The same processing release is required
for the selected pair.

Public search metadata does not require Earthdata credentials. No passwords or
tokens belong in chat or version control. Catalog URLs are reported as returned;
authenticated HDF5 access and actual HHHH arrays are not checked in this milestone.

Outputs are saved under `data/`: environment versions, raw public search results,
a search report, and (only when a compatible pair is found) `nisar_manifest.json`.
An empty search is not proof that the mission has no such observations; it means
the requested records were not returned by that search at that time.

## Verified result

Both requested observations were found in the live ASF catalog. See
[the result report](data/nisar_results.md) for full product IDs, UTC timestamps,
HTTPS download URLs, and S3 URIs. The selected pair is saved in
`data/nisar_manifest.json`: track 105, frame 017, bandwidth 4005,
polarization DHDH (frequency-A HH/HV), processing release P05023.

All ten dependency imports and `pip check` passed. The final search exited
successfully with one catalog record on each requested date. No HDF5 was
downloaded. Milestone 1 ends here; further work requires the user's instruction.

## Milestone 2 — completed

Both real frequency-A HHHH Louisiana subsets were read using authenticated
HTTPS byte ranges, converted to dB and visualized with one shared scale.
Run `.venv/bin/python -B scripts/visualize_nisar.py` with a valid saved token to
repeat. See [Earthdata access and verified results](EARTHDATA_ACCESS.md).

Outputs: [comparison image](data/nisar_hhhh_comparison.png),
[processing report](data/nisar_visualization_report.json), and georeferenced
power/dB GeoTIFFs with JSON sidecars under `data/subsets/`. GeoTIFF read-back,
matching grids and inverse dB conversion passed on the real subsets.
No full products were downloaded, and no flood classification is implemented.

## Milestone 3 — exploratory water change candidates

This stage runs entirely offline on the real cached June 21 and July 3, 2026
GCOV HHHH subsets. Source identifiers, GeoTIFF tags, sidecars and the Milestone 2
report are cross-checked; input dB bands are verified against positive linear
power. SHA-256 fingerprints record the current source files. No new satellite
products are downloaded and no source files are changed.

```sh
.venv/bin/python -B scripts/detect_water_change.py
.venv/bin/python -B -m unittest discover -s tests -v
```

Adjust settings explicitly, using separate output folders to retain the baseline:

```sh
.venv/bin/python -B scripts/detect_water_change.py --water-threshold-db -17 --min-change-db 2 --filter-size 3 --output-dir data/water_change_alternative
.venv/bin/python -B scripts/detect_water_change.py --disable-change-threshold --output-dir data/water_change_without_gate
```

Default processing uses the intersection of both valid positive-power masks,
a normalized 3×3 boxcar mean in **linear power**, then `10*log10(power)` and
`delta_dB = after_dB - before_dB`. Invalid centers stay NaN. Invalid neighbors
and pixels outside the AOI do not contribute; the window is renormalized at
edges, with no outside-AOI halo. This simple speckle smoothing can blur narrow
water features. The odd filter width is adjustable from 1 to 9 pixels.

The **−16 dB threshold is exploratory**, not a validated universal threshold.
Water candidates have filtered backscatter ≤ the chosen threshold. The optional
absolute change gate defaults to ≥3 dB and applies only to transitions, not
persistent candidates. Rejected transitions remain “Other valid surface”; that
class does not assert verified stable land. Output codes are:

| Code | Meaning |
| --- | --- |
| 0 | Unknown / no data (including outside AOI) |
| 1 | Persistent water candidate |
| 2 | New water candidate / possible expansion |
| 3 | Receded water candidate |
| 4 | Other valid surface |

Both real grids match at EPSG:32615, 10 m resolution; no reprojection was needed.
If grids differ, the after power and its mask are resampled separately with
nearest-neighbor onto the before grid, then intersected. Areas use the affine
pixel determinant and projected CRS linear units converted to metres; geographic
degree-based area calculations are rejected. These are projected-grid estimates.

Outputs in `data/water_change/` include individual before/after/difference/class
PNGs, `water_change_overview.png`, `filtered_radar_change.tif` (bands: filtered
before power, filtered after power, before dB, after dB, delta dB),
`water_change_classes.tif`, `common_valid_mask.tif`, `results.json`, `summary.md`
and the real-output `verification.json`. All raster outputs retain georeferencing;
dates, source IDs and settings are stored in GeoTIFF tags and results metadata.
Display limits clip only PNG colors, never saved radar values.

Baseline estimates: 569 expansion-candidate pixels (**0.0569 km²**),
5 recession-candidate pixels (**0.0005 km²**) across 138,779 common valid pixels.
There are also 158 persistent-water candidates, 138,047 other valid pixels and
10,024 unknown/outside-AOI cells in the rectangular output. A further 1,421
threshold crossings fail the 3 dB gate and remain class 4.

Twelve new unit tests cover conversion, invalid values, class transitions,
optional gates, identical images, mask-aware filtering, alignment and projected
area calculations; all passed alongside seven existing security tests. Synthetic
arrays occur only in unit tests. Real-output checks passed for dB conversion,
delta, classes, masks, projected areas, georeferencing and unchanged source hashes.

**These are not confirmed flood detections.** Backscatter alone cannot establish
flooding; independent reference data and threshold assessment are still needed.
Wind, vegetation, soil moisture, shadow and smooth artificial surfaces can affect
interpretation. No accuracy percentages or validation metrics are claimed.
See [results and limitations](data/water_change/summary.md), including primary
method references. No Streamlit UI was developed. Work stops after Milestone 3.

## Milestone 4 — interactive local application

Start from this project folder in PyCharm's Terminal (using the existing `.venv`):

```sh
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

Open http://127.0.0.1:8501 . In a PyCharm Run Configuration, select module
`streamlit`, parameters `run app.py --server.address 127.0.0.1`, project working
directory, and interpreter `.venv/bin/python`. Stop with Ctrl+C in the terminal.

The dashboard verifies the cached source fingerprints, reuses existing mask-aware
filtering/classification/area functions, and makes no NASA data requests. Only
public radar arrays and metadata are cached in memory; credentials are never
loaded or cached. File size/modification signatures invalidate the data cache.
Neither slider changes nor app startup write to the original scientific outputs.

Features: four radar/change maps, four area metrics, an adjustable −22 to −12 dB
water threshold (0.5 dB steps), 0–8 dB minimum absolute change (0.5 dB steps),
recalculated threshold sensitivity, provenance, baseline quality context and
expandable methodology. A zero minimum removes the magnitude gate. The fixed
preprocessing is the existing 3×3 normalized linear-power mean. Shared map color
limits are display-only. Candidate classes are not confirmed water or flooding.

Validation: 22 tests passed (19 previous + 3 dashboard tests). Streamlit AppTest
checked −16, −14, −18 and −20 dB against the actual saved quality-check results;
minimum-change values 0 and 8 dB were also tested. Default metrics exactly match
Milestone 3: 0.0569 km² expansion, 0.0005 recession, 0.0564 net change and
13.8779 km² valid area. Missing inputs produce a recovery message; invalid
thresholds are rejected. A network-blocked app test passed, with original input
and processing-file hashes unchanged. The live server health endpoint returned
HTTP 200. Real browser interactions were checked at −16, −14 and −18 dB, plus
the sensitivity tab; narrow and 1440-pixel-wide layouts were visually inspected.
This is not exhaustive cross-device testing. See `data/dashboard_tests.log`,
`data/dashboard_verification.json` and `data/dashboard_preview.jpg`.

Scientific limitations remain unchanged: no usable independent date-matched
water validation, exploratory thresholds, sensitivity to filtering and isolated
pixels, widespread radar darkening, and unresolved subpixel registration.
Streamlit work stops at Milestone 4; no deployment or presentation is included.

## Milestone 5 — optional reliability controls

Default results remain unchanged. The sidebar now offers **Suppress single-pixel
change candidates (optional)**, OFF by default. It suppresses only one-pixel
8-connected expansion/recession components separately; the map, areas and
sensitivity curves use the same setting. Persistent/unknown pixels and radar
values are unchanged. Suppressed candidates are not verified dry land, and small
real features may be lost. The open scientific interpretation panel states the
remaining limitations. No scene-wide bias correction is applied.

Offline darkening scenarios, singleton diagnostics, historical-waterway splits,
a bounded independent Sentinel-1 reference catalog search, optional GeoTIFFs and
26-test verification are saved separately in [data/reliability/REPORT.md](data/reliability/REPORT.md).
These support an exploratory presentation, not confirmed flooding or accuracy
claims. To repeat scenarios: `.venv/bin/python -B scripts/reliability_checks.py`.
Milestone 5 ends here; no presentation or deployment tasks were performed.

## Milestone 8 — separate Sentinel-1 benchmark

The optional **Workspace → Benchmark Validation (Sentinel-1)** page reports a
small official Sen1Floods11 hand-labeled test subset, separated from all NISAR
area metrics. It does **not** establish NISAR HH accuracy or verified flood extent.
See [data/benchmark_validation/REPORT.md](data/benchmark_validation/REPORT.md)
for the deterministic 12-train/12-test chip protocol, frozen train-only VV/VH
threshold selection, actual held-out results, baseline, all 12 real scene panels,
failure cases and 41-test verification. The main NISAR processing is unchanged.

## Milestone 9 — real geographic overlays

Choose **Workspace → Geographic map (NISAR)** for the cached 5 × 5 or 10 × 10 km
Louisiana windows. Both catalog footprints cover these requests. Actual common
valid coverage is 25 and 100 km² respectively, measured on the native 10 m
EPSG:32615 grid. The boundary follows valid raster cells, including gaps if any.
Candidate classes use the existing 3×3 linear-power filter, −16 dB threshold and
3 dB change gate, with singleton suppression OFF. Map settings are fixed and
explicit; the original NISAR workspace retains its interactive thresholds.

The optional map has OpenStreetMap, zoom/pan, three transparent candidate layers,
layer controls, a legend and the real processed boundary. Display rasters use
nearest-neighbor reprojection to Web Mercator and at most 768 pixels per side.
Native pixels determine all measurements; small features can disappear in the
display. These are **unvalidated candidate surface-water changes**, not a flood
map. Sentinel-1 benchmark scores do not apply to these NISAR overlays.

Launch with `.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1`.
An already running server from an older milestone may need restarting to reload
Python modules. A fresh instance was verified at http://127.0.0.1:8502.
Opening the dashboard uses local cached radar outputs; OSM tiles and Leaflet
libraries require internet access. Only metadata/rendered map HTML is cached,
never credentials.

Outputs and verification: [data/geographic_mapping/REPORT.md](data/geographic_mapping/REPORT.md).
The separate window retrieval script is `scripts/process_geographic_area.py`
(`--size-km 5` or `--size-km 10`); it requires locally available Earthdata
authentication and makes bounded HDF5 range reads, not whole-product downloads.
There is no need to rerun it to use the map. Existing data and benchmark results
are preserved. Milestone 9 stops before further science, presentation or deployment.

## Six-date HH time series — phases 0–2

**Workspace → HH time series (six dates)** adds the real June21, July3, July15,
July27, August20 and September1 2026 observations over the original Louisiana
AOI. All six share ascending track105/frame017, 4005/DHDH, P05023 and processing
version R05.02.3. The verified common footprint is **13.8779 km²**, 138,779
positive valid pixels on the same 10 m EPSG:32615 grid; no reprojection was needed.
The larger existing two-date maps and the benchmark workspace remain separate.

Select two dates and a geographic layer (either HH observation, signed difference,
or exploratory temporal anomaly). Enter longitude/latitude, choose a 1×1/3×3/5×5
neighborhood and press **Apply point**. The sampled native pixel center is marked
and reported; the graph/table give actual acquisition times, filtered HH dB,
valid counts, missing values and product IDs. Graph points are not interpolated
across the irregular observation gaps. Same-date comparisons return zero.
OSM/Leaflet resources need internet; app interactions never access Earthdata.

Processing reuses the existing mask-aware 3×3 mean in **linear** HH power before
10 log10 conversion. Per-date and all-six-date valid masks are retained. No scene
median normalization is applied. The anomaly is a signed dB deviation from the
per-pixel temporal median, **not a z-score or probability**. Fewer than four finite
observations remain unknown, constant histories have zero deviation, and the
median resists an isolated extreme date. Six dates do not establish a climatology
or confirm flooding. See [scientific methodology](data/time_series/METHODOLOGY.md).

New outputs in `data/time_series/` include a georeferenced NetCDF cube, per-date
HH dB GeoTIFF bands, common-valid cube/mask, consecutive and first-date differences,
temporal median, dB anomaly bands, statistics, real-data overview figures and
provenance. The first two cached observations were reused; four new small windows
required about 34 MiB of total range reads. The full phase-1 run took 142 seconds.
No whole HDF5 products were downloaded or original outputs overwritten.

Run locally with `.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.fileWatcherType poll`.
The increment was verified on `http://127.0.0.1:8503`. Reprocessing is unnecessary;
`scripts/process_time_series.py` leaves a completed time-series result unchanged.
Run regression checks with `.venv/bin/python -B -m unittest discover -s tests -v`.
The pre-change Git checkpoint is tagged **pre-timeseries-phase0**. HV retrieval
and new radiometric/noise diagnostics await explicit approval; phases 3–4 have
not been performed. See [execution report](data/time_series/REPORT.md).

## Phase 3 — optional real HH/HV polarization analysis

Choose **Workspace → Polarization Analysis** for six real frequency-A HHHH/HVHV
observations on the original Louisiana AOI. Both polarizations and all dates
share the same verified 10 m EPSG:32615 grid and **13.8779 km²** common valid area.
HH raw data was reused; HV required only small HTTPS ranges (~48 MiB total),
not whole HDF5 products. Existing HH, geographic and benchmark results remain
unchanged; Git checkpoint **pre-polarization-phase3** protects the working baseline.

The new section includes HH/HV/derived-ratio selection, actual-date comparison,
side-by-side geographic maps, HH/HV before/after/change panels, a change hexbin,
temporal statistics and source metadata. All interaction is local; OSM/Leaflet
need internet. Use `.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.fileWatcherType poll`.
The tested Phase3 server is `http://127.0.0.1:8504`.

Both bands use matched positive-finite masks, the existing 3×3 linear-power mean,
then 10 log10. The linear ratio is HH power / HV power; its dB value is HH_dB−HV_dB.
It is not a ratio of dB numbers, flood probability or vegetation classification.
Original-pair median changes are −1.3888 dB HH and −0.7204 dB HV; the difference
does not establish a physical cause, sensor bias or flooding. No new classifier,
noise correction, normalization or threshold was introduced.

Outputs, exact source IDs, methodology and test details are separate in
[data/polarization_analysis/REPORT.md](data/polarization_analysis/REPORT.md).
Processing script: `scripts/process_polarization.py --dates 2` or `--dates 6`;
completed outputs are left unchanged, so no rerun is needed. The full regression
suite passes 62 tests. **Phase 4 remains pending; only Phase 3 was performed.**

## Phase 4 — optional scientific diagnostics

**Workspace → Scientific Diagnostics** adds cached HH/HV temporal distributions,
all15 date-pair change distributions, robust spatial summaries, selected
quiet-looking reference regions, a baseline-versus-alternative comparison,
threshold/filter sensitivity and actual quality/texture limitations. The main
application and original measurements are unchanged. Baseline Git tag:
**pre-scientific-diagnostics-phase4**.

The original pair still gives0.0569 km² expansion candidates and0.0005 km² recession.
One retrospective diagnostic divides ΔdB by the maximum of four held-out-date
scaled MAD and a declared1 dB floor;|score|≥3 retains0.0448/0.0003 km². This is
not a probability,3σ test, new deployed classifier or evidence of improved
accuracy. The floor makes the alternative at least as restrictive as3 dB.
No scene median is subtracted and no benchmark test labels were used for tuning.

Real GCOV quality windows for June21/July3 show medians of approximately4.745
numberOfLooks and valid-subsample mask code1 throughout the AOI. Noise-equivalent
HH/HV metadata are described as DN², so no unverified comparison to calibrated
gamma-0, HV noise-floor estimate or SNR is made. Both products report no applied
noise correction. Two raw HV patches pass declared conditional ENL screening
(provisional moment proxies≈3.9–4.0); these are not pure thermal-noise estimates.
Speckle/texture and environmental temporal variation remain distinct uncertainties.

The3 dB gate remains an exploratory magnitude rule. Twelve threshold/filter
settings show substantial candidate-area sensitivity; fewer candidates or setting
agreement do not validate flooding. Independent NISAR validation is unavailable.
See [full scientific report](data/scientific_diagnostics/REPORT.md) for actual
numbers, selection rules, caveats and source documentation. Seventy-one regression
tests pass, preserving previous data and dashboard workspaces.

To reproduce only new diagnostics, run `scripts/inspect_radar_quality.py` with
local Earthdata authentication, then `scripts/run_scientific_diagnostics.py`.
Existing completed outputs are left unchanged; the app needs no NASA credentials
or science recomputation. Processing flags are separately recorded in
`data/scientific_diagnostics/processing_flags.json`. Run the dashboard with the
existing Streamlit command; the tested Phase4 server is `http://127.0.0.1:8505`.
**Phase 4 stops here.** Presentation is defensible as exploratory research, not
confirmed flood extent, NISAR accuracy or calibrated uncertainty.

## Phase 5 — Change Investigation Engine

**Workspace → Investigation Explorer** helps researchers choose where and when
to investigate real radar changes. It adds five numbered geographic candidates,
list selection, region-specific six-date HH/HV charts, exact dates/provenance,
an explainable reason for selection, setting sensitivity, uncertainties and a
suggested independent follow-up. The Markdown download exports that evidence
for the selected region. Existing analysis workspaces and results remain intact.

The frozen heuristic screens same-interval/direction four-connected HH changes:
at least3 dB, strictly above the scene absolute-change90th percentile, at least
25 native cells. It ranks notable-interval count, then area, then magnitude;
overlapping/nearby proposals are suppressed. These are descriptive priorities,
not flood/risk/confidence scores or verified wetlands. HV is contextual because
its calibrated noise floor remains unresolved. No scene median is subtracted,
benchmark labels used for tuning, or new scientific dataset downloaded.

The six-date13.8779 km² footprint produced268 eligible event-components and five
selected regions of0.0074,0.0030,0.0464,0.0158 and0.0130 km². The first two have
four notable intervals out of five; this is not a count of independent events.
One anomalous date can generate both a rise and a fall. Nine filter/magnitude
variants expose substantial setting dependence, which is shown rather than
turned into confidence. Region4 touches the cached boundary and is flagged as
clipped. Unselected areas are not verified stable.

Run `.venv/bin/python -B scripts/build_investigations.py` to create only the new
cached outputs; a completed run exits without overwriting them. The app itself
performs no NASA access or engine recomputation. Existing Folium maps and the
linear-power filtering functions are reused; no dependencies were added.
The pre-change Git tag is **pre-investigation-phase5**. Tests: **81 passing**.
The tested local server is `http://127.0.0.1:8506`; use the existing Streamlit
launch command with `--server.fileWatcherType poll` and restart old processes
when changing modules between phases.

See [investigation report](data/investigation_engine/REPORT.md) and the five
`region_*_investigation.md` reports under `data/investigation_engine/`.
This is an exploratory wetland-research workflow; independent references are
needed before attributing flooding, damage or ecological change. **Stop after
Phase5; deployment, rebranding and presentation tasks have not been started.**
