# Phases 0–2 — six real Louisiana HH observations

## Protection and existing features

Inspected the existing pipeline, scientific/validation reports, tests, cached
subsets, Streamlit workspaces and real geographic products before edits. The
two-date classifier, optional singleton control, Folium map, scientific context
and separate Sen1Floods11 benchmark already existed and were retained.
The pre-change Git commit is `59c8bb4a90a0cfa4090d9ca1395be013c4e27d69`, tagged
`pre-timeseries-phase0`; 287 files were checkpointed, excluding secrets, venv,
caches and local Streamlit configuration. System Git could not run because of
the Xcode license; Dulwich in the existing venv created a standard local Git
repository without changing system settings. Baseline: 46 tests passed.

## Actual source products

All are L2 PR GCOV provisional, ascending track105/frame017, frequency-A HH,
4005/DHDH, P05023, processing R05.02.3. New ASF search and filename/catalog checks
confirm acquisition compatibility and complete catalog AOI footprint coverage.
Real arrays confirm full common positive valid coverage, not just catalog overlap.

| UTC acquisition | Exact product ID | Access this run |
|---|---|---|
| 2026-06-21T11:19:06Z | NISAR_L2_PR_GCOV_023_105_A_017_4005_DHDH_A_20260621T111906_20260621T111941_P05023_N_F_J_001 | Existing verified cache |
| 2026-07-03T11:19:05Z | NISAR_L2_PR_GCOV_024_105_A_017_4005_DHDH_A_20260703T111905_20260703T111940_P05023_N_F_J_001 | Existing verified cache |
| 2026-07-15T11:19:05Z | NISAR_L2_PR_GCOV_025_105_A_017_4005_DHDH_A_20260715T111905_20260715T111940_P05023_N_F_J_001 | 9 MiB range reads |
| 2026-07-27T11:19:04Z | NISAR_L2_PR_GCOV_026_105_A_017_4005_DHDH_A_20260727T111904_20260727T111939_P05023_N_F_J_001 | 8 MiB range reads |
| 2026-08-20T11:19:03Z | NISAR_L2_PR_GCOV_028_105_A_017_4005_DHDH_A_20260820T111903_20260820T111938_P05023_N_F_J_001 | 9 MiB range reads |
| 2026-09-01T11:19:03Z | NISAR_L2_PR_GCOV_029_105_A_017_4005_DHDH_A_20260901T111903_20260901T111937_P05023_N_F_J_001 | 8 MiB range reads |

The original Louisiana AOI remains −90.310020 to −90.250797° longitude and
29.902604 to 29.924476° latitude. Each window is 257 × 579 including masked
padding. All six use exactly the same north-up affine transform, EPSG:32615 and
10 m pixels: **138,779 common valid pixels / 13.8779 km²**. No alignment correction
was necessary. Phase1 took 142.2 s including range access, processing and output.
No peak memory was measured; only small windows were loaded and no full HDF5
product was downloaded. Transfer totals are actual bytes plus eight-byte header
checks, rounded to MiB above.

## Products and features

New source: `scripts/process_time_series.py`, `src/time_series.py`,
`src/time_series_map.py`, `src/time_series_panel.py`, `tests/test_time_series.py`.
Existing source changed: `app.py` (optional workspace branch) and `README.md`.
The scientific classifier and production dependencies were unchanged. Dulwich
is only a local checkpoint tool, not an application requirement.

The new directory contains catalog/manifest and four small real source GeoTIFFs,
`hh_time_series.nc`, `hh_db.tif`, `common_hh_db.tif`, `common_valid.tif`,
`delta_consecutive_db.tif`, `delta_from_first_db.tif`, `temporal_median_db.tif`,
`anomaly_db.tif`, `common_footprint.geojson`, `scene_statistics.json`, `results.json`,
overview figures, test/run logs and preservation fingerprints. Nothing under a
previous results directory was recomputed or overwritten. Full source IDs and
settings accompany the outputs; credentials and signed URLs do not.

New UI: two observation selectors; selected/comparison HH, difference and anomaly
geographic layers; WGS84 coordinate entry with 1/3/5-pixel neighborhood side;
sampled pixel center marker; six-date time graph; valid/missing sample counts;
full acquisition/product metadata; scene distributions and methodology. The
existing geographic projection helper and Folium are reused. All UI science is
local/offline; internet is required only for OSM/Leaflet assets.

## Verification and interpretation

Phase1 passed five new scientific tests before UI development. The complete
suite then passed **54 tests** (46 previous + 8 new), covering real-source
compatibility, dB units/conversion, common masks, missing/constant/outlier temporal
histories, coordinate orientation, point-to-native-pixel sampling, difference
sign and identical dates, display transparency, all six date selectors,
neighborhood data, out-of-extent recovery, missing files and old workspace
regression. Synthetic data appears only in unit fixtures. A failed early
out-of-coverage test used a polygon outside the projection's domain; its fixture
was corrected to a nearby out-of-coverage polygon. No observation or processing
result was fabricated or adjusted to make tests pass.

Browser checks and final SHA-256 preservation results are recorded in
`verification.json` after completion. The original two-date expansion/recession
defaults remain 0.0569 / 0.0005 km². Benchmark results remain Sentinel-1-only.

Actual browser checks rendered the real HH map, difference and anomaly layers;
changed comparison June21/September1 to July15/September1; sampled longitude
−90.290000°, latitude 29.915000° at native row114/column196; and verified the
3×3 neighborhood graph/table against the local calculation (nine finite samples
on each of six dates). The six displayed dB values were −4.4726, −8.3915, −7.0141,
−6.2040, −7.9197 and −2.9390. Raster visibility toggled correctly and zoom changed
the scale from 500 m to 300 m. The earlier geographic and benchmark pages still
rendered. Date controls, map labels and sampled coordinates were also checked
after leaving and returning to the time-series workspace.

That round trip exposed a browser-default/server-state mismatch in recreated
conditional widgets. Explicit defaults now reflect their current session values;
regression assertions check both widget values and browser-protocol defaults.
The final 54-test suite passed again after this fix. macOS FSEvents file watching
was unavailable in this execution context, so the local server was restarted with
`--server.fileWatcherType poll`; no system settings or project configuration were
changed. The final application is healthy on 127.0.0.1:8503.

SHA-256 checks confirm **all 254 previous data files are unchanged**, including
the benchmark. Of the checkpointed files only `app.py` and `README.md` changed;
new code/results are separate additions. The checkpoint and prior results remain
recoverable. Preview images and `browser_point_check.json` preserve the actual
browser sampling evidence. No browser test is claimed for other engines/devices.

Anomalies are signed deviations from each pixel's six-date median **in dB**, not
z-scores or probabilities; zero variance is harmless and fewer than four finite
samples are excluded. Six sparse dates do not establish a climatology or resolve
short-lived inundation. The source gaps are approximately 12/12/12/24/12 days.
Scene medians change, but this increment does not establish sensor bias, subtract
offsets, attribute causes, inspect HV, or perform phase3/4 diagnostics.

Independent paired change validation remains unavailable. Speckle, neighborhood
smoothing, mixed pixels, vegetation, wind, moisture, tides/drainage, registration
and provisional radiometry limit interpretation. This is a surface-dynamics
exploration workflow, not verified water/flood detection or NISAR accuracy.
See `METHODOLOGY.md` for definitions and official NASA/ASF sources.

**Stop:** phases 0–2 only. The single next action is user approval to begin the
small HV feasibility check and subsequent noise/radiometric diagnostics.
