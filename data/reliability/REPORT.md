# Milestone 5 — scientific reliability improvements

Original results and cached observations are preserved, verified by SHA-256.
The default water threshold (-16 dB), change gate (3 dB) and linear 3×3 filter
are unchanged. No new NISAR data were downloaded.

## Optional connected-component filtering

Default expansion/recession: **0.0569 / 0.0005 km²**.
Optional singleton suppression: **0.0508 / 0.0002 km²**.
The toggle is OFF by default. It suppresses 61 isolated expansion pixels and
3 isolated recession pixels, separately labeled with 8-connectivity. Only change
candidates are affected; persistent water and unknown classes are preserved.
Suppressed pixels become other valid surface, not confirmed dry land. The common
valid comparison area remains 13.8779 km². The SAR arrays themselves are unchanged.

Each grid pixel is 100 m², and a singleton may be noise OR a real small feature.
The filter is a transparent size prior for exploration, not improved accuracy.
All 61 singleton expansion pixels are recorded in isolated_expansion_pixels.csv
with row/column, both backscatter values, change and historical-waterway context.
Statistics are in singleton_statistics.json. No near-water rule removes pixels.

## Scene-wide darkening: counterfactual sensitivity only

The common valid-AOI median after-minus-before change is -1.3887816 dB.
We hold both classification thresholds fixed and hypothetically brighten AFTER
by zero, half, or all of the opposite median. These scenarios operate on the
actual arrays; no scenario raster is passed off as an observation.

| Hypothetical AFTER addition | Expansion (km²) | Recession (km²) |
|---|---:|---:|
| -0.0000 dB | 0.0569 | 0.0005 |
| 0.6944 dB | 0.0192 | 0.0007 |
| 1.3888 dB | 0.0062 | 0.0015 |

The strong response means scene-level darkening could contribute to candidate
counts in combination with local changes. A uniform -1.39 dB shift alone cannot
meet the default 3 dB change gate. This does not establish sensor bias: wind,
vegetation, moisture and real hydrological change can produce broad differences.
There are no independently verified stable controls. No calibration correction
is scientifically justified yet, and none is applied in the app or defaults.
See darkening_sensitivity.csv and darkening_sensitivity.png.

## Historical waterway context (not validation)

At baseline, 431/569 expansion pixels are within 30 m of mapped NHD canals/streams
(0.0431 km²); 138 are farther (0.0138 km²). The optional singleton filter leaves
394 nearby pixels (0.0394 km²) and 114 farther pixels (0.0114 km²).
Historical geometry is rasterized all_touched at 10 m, so distance is approximate.
Real flooding can occur near rivers: proximity is reported, never an exclusion.
Full expansion and recession splits are in results.json; the baseline context
raster has 1=near waterway, 2=farther expansion candidate, 0=not expansion.
Broad historical swamp polygons are excluded from this canal/stream definition.

## Bounded independent reference investigation

Existing date-matched optical DSWx-HLS AOI windows remain fully cloud/shadow
masked. Two additional public CMR queries tested independent Sentinel-1-derived
OPERA_L3_DSWX-S1_V1 within +/-1 day around each target date over the exact AOI.
One June 21 acquisition was returned (00:10 UTC, about 11 hours before NISAR);
no counterpart was returned for July 3 +/-1 day. No paired reference is therefore
available from this bounded search. The June catalog hit was NOT downloaded or
pixel-validated; it does not establish water or flood truth. Other archives or
wider windows were not exhaustively searched. No accuracy score is claimed.
Query parameters, results and timestamps are in reference_search.json and the
raw dswx_s1_*.json files.

Sources: [NASA DSWx-S1 product](https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-S1_V1),
[NASA DSWx suite](https://www.jpl.nasa.gov/go/opera/products/dswx-product-suite/).

## Dashboard and tests

The optional singleton toggle recomputes metrics, class map and the threshold
sensitivity curve consistently. An always-open scientific interpretation panel
explains dark radar ambiguity, threshold sensitivity, scene-wide darkening and
missing independent validation. No scene-offset toggle or correction is added.

26 tests passed, including four new reliability tests: singleton connectivity, class/mask preservation, real-data counts, and toggle/reversion with sensitivity consistency. Existing threshold, missing-input and network-blocked app tests also passed. The live server returned HTTP 200. This milestone used AppTest for the new toggle; no new browser-toggle interaction is claimed.

Suitable for final presentation as an **exploratory radar water-change demo**,
with all limitations visible. Not suitable for confirmed flood mapping or an
accuracy claim. Independent reference pairing, scene-level radiometric/surface
change assessment and subpixel registration remain unresolved.

Run `.venv/bin/python -B scripts/reliability_checks.py` to repeat the offline
scenario analysis. Run `.venv/bin/python -B -m unittest discover -s tests -v`
for the full automated suite. Original scientific outputs are never overwritten.
