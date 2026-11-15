# Milestone 8 — Sen1Floods11 independent manual-label benchmark

## Scope and reproducible sample

Official source: https://github.com/cloudtostreet/Sen1Floods11 . Data: public GCS sen1floods11/v1.1, HandLabeled/S1Hand and LabelHand only. Official train/valid/test/Bolivia CSVs and repository documentation are archived here. **12 training chips and 12 held-out official test chips** were selected across Ghana, India, Mekong, Nigeria, Pakistan and Paraguay. The validation split and Bolivia holdout were not used. No weak labels, JRC masks or automatic reference masks are used as manual truth.

The six alphabetically first shared event groups and SHA-256 filename ranking with a fixed seed select two chips per group per split. The rule and sample_manifest.json were fixed before opening labels or looking at results. This is a small reproducible sample, not the whole benchmark or a geographic-event holdout. Official chip splits share events, so results do not establish transfer to unseen flood events. Downloads total 39714432 bytes (~37.9 MiB), not the whole ~14GB dataset.

## Actual units, nodata and alignment

All downloaded radar TIFFs have actual descriptions VV then VH, Float32 and NaN nodata. The official README defines the values as dB; TIFF unit fields are empty, so metadata alone does not self-describe units. Negative dB values are valid, never interpreted as invalid power. Manual labels are Int16 with observed codes -1/0/1; their TIFF nodata attribute is absent, so explicit -1 exclusion is essential. All chips are 512x512 EPSG:4326 at nominal 10m posting. No area measurements in degrees are made.

Raster and label transforms differ only in floating-point coefficients (~1e-18 degrees). They share shape/CRS and are checked within 1e-12 absolute affine tolerance; no geometric resampling was performed. Larger mismatches fail. Actual per-file inspection is saved in actual_raster_inspection.json.

Input dB is NOT logged again. For the existing 3x3 mask-aware mean only, it is mapped to linear power, filtered using radar-valid support and converted back to dB. Label validity NEVER determines filter support or Otsu histograms. Evaluation uses the intersection of radar-valid pixels and manual label0/1. The same support/preprocessing is used by both methods.

## Train-only calibration and baseline

Calibration compared VV and VH thresholds from -30 through -8dB in 0.5dB steps using ONLY the 12 training chips. Objective: mean per-chip training F1 (undefined F1 contributes0), fixed tie rule. Selected **VH <= -20.5 dB**. No reuse of the NISAR HH -16dB threshold. calibration.json was frozen before test evaluation. Full training grid is archived.

FloodPulse’s existing classification rule supplies static water candidates through the separate Sentinel-1 adapter. The original NISAR processing module is unchanged. Baseline: per-image unsupervised 256-bin Otsu threshold on the SAME selected VH band and SAME 3x3 filtered radar. It uses test radar histograms but no test annotations, does not learn parameters from test labels, and differs from the global train-calibrated cutoff. No settings were adjusted after seeing test outcomes.

## Held-out manual-label results

All 12 selected test chips were retained, including poor/no-water cases. Total valid labeled radar pixels: **2,406,776**. Micro metrics pool these pixels; spatial pixels are correlated and are not millions of independent scenes.

| Method | Precision | Recall | F1 | IoU |
|---|---:|---:|---:|---:|
| Train-calibrated VH cutoff | 0.600487 | 0.751487 | 0.667554 | 0.500999 |
| Per-image Otsu baseline | 0.259756 | 0.741865 | 0.384785 | 0.238225 |

Adapted confusion matrix, rows manual [nonwater,water], columns predicted [nonwater,water]: `[[1976949, 143271], [71213, 215343]]`.

Macro per-test-chip F1: **0.372119**. This is much lower than micro F1 because scene/class support is imbalanced. Undefined scores (e.g. no positive reference labels) stay null in scene results; no confidence interval or accuracy percentage is invented.

## Real visual comparisons and failure cases

Four-panel PNGs were generated for ALL 12 test chips in figures/: A real VH backscatter after declared filter, B manual water mask, C prediction, D true nonwater/true water/false-positive/false-negative/ignore map. No synthetic scene is shown. Examples:

- [Ghana_313799](figures/Ghana_313799.png): strong missed-water failure, recall ~0.075 and F1 ~0.139.
- [India_44475](figures/India_44475.png): no labeled water, but false detections; recall is undefined and F1 is0.
- [Nigeria_812045](figures/Nigeria_812045.png): stronger example, F1 ~0.919; this was not selected instead of the failures.
- [Mekong_254910](figures/Mekong_254910.png): severe false-positive behavior, F1 ~0.012.

One global radar intensity threshold is not a universally reliable water detector. Different surface roughness, vegetation, geometry and dark nonwater can affect the signal. The figures alone cannot attribute the precise physical cause. The 3x3 filter can blur boundaries; manual annotations also have interpretation limits. Results have not been tuned to improve these failures.

## Streamlit integration and preservation

A separate optional Workspace → Benchmark Validation (Sentinel-1) page is available only after successful evaluation. It displays these metrics without NISAR candidate-area cards. It states prominently that this is a Sentinel-1 adaptation, not NISAR HH accuracy, and that surface-water presence is not verified flood extent. The NISAR workspace remains default and its original area/threshold behavior is unchanged. The app loads only saved benchmark outputs; it does not download benchmark or NASA data.

41 automated tests passed: units/no double logarithm, manual invalid masks, confusion counts, split leakage, missing data, train-only grid consistency, actual micro-count aggregation, Otsu without labels, optional UI separation/reversion, and all prior NISAR/dashboard tests. Live server health returned HTTP200. The new page was tested with Streamlit AppTest; no new actual browser-interaction test is claimed.

All previous scientific outputs and pipeline source hashes were checked unchanged. The prior app entry point is backed up as app_before.py.txt; its only intentional integration change is the optional separate workspace. No NISAR-specific validation metric has been created.

## Reproduce

1. `.venv/bin/python -B data/benchmark_validation/download_sample.py` (reuses existing bounded downloads).
2. `.venv/bin/python -B data/benchmark_validation/evaluate.py` (repeats the fixed train-only protocol; do not tune on test failures).
3. `.venv/bin/python -B -m unittest discover -s tests -v`.
4. `.venv/bin/python -m streamlit run app.py` → select the separate benchmark workspace.

Next: retain this frozen held-out result and discuss the observed failures and transfer limits before any new model/threshold experiment. Further experiments require a new preregistered protocol or untouched validation data; do not optimize against this test sample.
