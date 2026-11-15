# Phase 3 — real NISAR HH/HV polarization analysis

## Protected baseline and scope

Recoverable standard Git checkpoint: commit
`3fabbe09ae36e2f7c5641602381bc81a7749f3aa`, tag `pre-polarization-phase3`.
It contains the working six-date HH application, public cached results and tests,
excluding secrets, venv, caches and local Streamlit configuration. Dulwich in
the existing venv was reused because system Git remains blocked by the Xcode
license. Baseline: 54 tests passed. SHA-256 fingerprints protect 288 preexisting
data files, including all HH time-series and benchmark results.

This increment performs Phase 3 only. No scene normalization, radiometric/noise
diagnostic study, new classifier, quality-mask interpretation, or Phase 4 work
is performed. The existing HH water-change algorithm and default areas remain
unchanged.

## Actual data availability and coverage

Both `/science/LSAR/GCOV/grids/frequencyA/HHHH` and
`/science/LSAR/GCOV/grids/frequencyA/HVHV` were inspected in each of six real
products. They are float32 2-D covariance intensity terms with units `1` and
descriptions identifying the corresponding geocoded covariance term. The
inspected frequency-A covariance terms were HHHH and HVHV; no synthetic or
renamed HH layer was substituted for HV. The [official GCOV guide](https://nisar-docs.asf.alaska.edu/gcov/)
identifies these diagonal terms as real-valued gamma-0 radar intensities.

Catalog/filename compatibility was rechecked against the preserved real ASF
search: ascending track105/frame017, 4005/DHDH, P05023, processing R05.02.3,
frequency-A HH/HV, complete coverage of the original Louisiana AOI. Exact IDs,
UTC acquisitions, filename/catalog fields and actual HDF5 layer metadata are in
`source_inventory.json`. Each small native window has 257 × 579 cells including
masked padding; each band/date has **138,779 positive valid pixels**. All twelve
HH/HV images overlap on the **13.8779 km²** common AOI at 10 m in EPSG:32615.
Transforms, dimensions and north-up coordinates match exactly; no alignment
reprojection was needed.

June21/July3 HV was processed and passed five new scientific tests first. Because
both reads worked, the optional remaining four HV dates were then processed.
HH raw power came from the existing verified six-date cache; it was not downloaded.
The first run read approximately 16 MiB over HTTPS in 82.30 s; the six-date run
reused those two HV windows and read another 32 MiB in 133.96 s. Total new access
was approximately **48 MiB**, with bounded range reads and no whole HDF5 downloads.
Secrets/signed URLs stayed in memory and are absent from outputs.
The recorded timers end at the scientific-summary stage, before final raster,
NetCDF and figure exports; they are not complete dashboard start-up benchmarks.

## Processing and physically defined comparisons

Per-date validity is the intersection of finite positive HH and HV linear power.
Both bands use the same existing 3×3 normalized mask-aware linear-power mean,
then `10*log10(power)`. Invalid centers remain invalid; edges use fewer valid
neighbors. Fixed all-date joint support is used for temporal spatial summaries;
selected-date comparisons use their joint HH/HV pair mask. New HH comparison
copies agree with the existing HH dB cache within float32 export precision. Old
HH outputs are not rewritten.

The dimensionless power ratio is **filtered HH power / filtered HV power**.
Its dB representation is `10 log10(HH/HV) = HH_dB − HV_dB`, not a ratio of dB
numbers or an amplitude ratio. Its provenance tag explicitly marks it as derived,
rather than inventing a new HDF5 dataset path. Change in ratio dB equals ΔHH−ΔHV.
Weak HV can make this ratio unstable; no noise-floor cutoff or correction has
been introduced.

| Acquisition UTC | HH spatial median dB | HV spatial median dB | Median pixel HH/HV ratio dB |
|---|---:|---:|---:|
| 2026-06-21 11:19:06 | −5.6422 | −13.3707 | 7.6596 |
| 2026-07-03 11:19:05 | −6.9871 | −14.1466 | 6.9462 |
| 2026-07-15 11:19:05 | −6.4289 | −14.0404 | 7.3683 |
| 2026-07-27 11:19:04 | −7.0949 | −14.3963 | 6.8390 |
| 2026-08-20 11:19:03 | −7.3766 | −14.6086 | 6.8630 |
| 2026-09-01 11:19:03 | −6.3289 | −14.2439 | 7.3313 |

For **July3 minus June21**, median pixel-wise ΔHH is **−1.3888 dB**, ΔHV is
**−0.7204 dB**, and median ΔHH−ΔHV is **−0.7085 dB**. Spatial Pearson r between
the two change fields is **0.3507**, descriptive association rather than accuracy.
All 138,779 pair-valid pixels are included in the change hexbin; no successful
examples are selected. Spatial dependence prevents interpreting pixel counts as
independent sample sizes. Difference of spatial medians is not generally the
median of pixel-wise differences.

Observed HV is generally weaker than HH on the common footprint. Both channels
darken in the original pair, but their magnitudes and spatial patterns differ.
The polarization contrast alone does not isolate a cause or demonstrate that
darkening is sensor bias. Smooth water, structure, canopy scattering, roughness,
wind/moisture, geometry and mixed pixels can influence different channels. These
are competing interpretations; no vegetation or water type was independently
identified here. See [NASA polarimetry](https://science.nasa.gov/mission/nisar/polarimetry/).

## Files and optional dashboard

Modified: `scripts/visualize_nisar.py` gains an explicit optional power-layer
argument, default HHHH unchanged; `app.py` adds an optional workspace; README
documents Phase3. No dependency or scientific classification code changed.
New: `scripts/process_polarization.py`, `src/polarization.py`,
`src/polarization_panel.py`, `tests/test_polarization.py`.

Outputs stay under `data/polarization_analysis/`. `raw/` contains six small HV
power/dB GeoTIFFs with source metadata/fingerprints. `two_date/` and `six_date/`
retain separate verified comparisons, georeferenced HH/HV dB, linear/dB ratios,
joint masks, change bands and an HH/HV NetCDF cube. Figures include HH/HV
before/after/change panels, HH-versus-HV change hexbin and temporal statistics.
Original outputs are preserved. A completed processing run exits without
overwriting its existing results.

**Workspace → Polarization Analysis** offers HH, HV and derived ratio maps,
two actual-date selectors, side-by-side geographic observations, six-panel
polarization comparisons, change relation, temporal spatial summaries, source
paths/IDs and physical limitations. The existing Folium display helper and
scientific filtering functions are reused. Maps use common display scales,
native projected measurements, transparent NoData and the actual all-date
joint-valid footprint. Only visualization is nearest-resampled (≤640 pixels per
side). No NASA access/credential handling occurs during UI interactions.

## Tests and remaining limitations

**62 tests passed**: 54 existing plus eight polarization tests. They cover explicit
layer selection, real HDF metadata, linear/dB units, ratio identities, NoData,
matched masks/grids, native area, change direction, identical dates, all band
choices, date controls, missing-file recovery, workspace return/defaults, existing
time-series/benchmark/map functionality and SHA-256 preservation of old data.
Synthetic values are restricted to unit-test fixtures.

Actual browser checks and final preservation details are recorded in
`verification.json`, with real preview screenshots. Tests on other browser engines
or devices are not claimed. Matplotlib emitted existing API deprecation warnings,
but the suite passed; these warnings did not change scientific results.

The browser rendered both real geographic HV observations and all six HH/HV
before/after/change panels. HH, HV and derived-ratio controls were exercised;
June21/September1 changed the displayed medians to −0.915 / −0.722 dB, matching
the native calculation. Selecting June21 twice gave 0.000 / 0.000 dB and an
undefined-correlation explanation. The selected raster overlay was hidden and
restored (image count one → zero → one). Navigation through the existing HH
time-series and benchmark pages returned with consistent polarization controls.
The original June21/July3 HV view was restored for the saved previews. All 288
preexisting data files retained their SHA-256 fingerprints; only the documented
app, subset-reader and README files changed among checkpointed files.

Independent NISAR water/flood validation remains unavailable. Six sparse dates
do not capture every event; speckle, filtering, cross-polarized noise sensitivity,
registration, temporal environmental variation and provisional radiometry remain
limitations. **Increasing HH or changing HH/HV does not classify flooded
vegetation.** No confidence or accuracy score is produced; benchmark scores
remain Sentinel-1-specific. No noise, offset correction or automatic scene
normalization is justified by these descriptive comparisons.

**Stop after Phase 3. Phase 4 has not been started.**
