# Flood validation protocol (Thailand Prachin Buri, India Gandak)

**Status:** frozen protocol, written 2026-11-15 **before** any NISAR flood window was read or any metric computed.
**Freeze commit:** 181782456a49aa252885861754a67934c3431007 (2026-11-15) (local git commit containing this file, the reference scan, the reader and the class
mapping; this header line is filled in right after that commit and is the only edit made outside "Deviations"). Thresholds and rules
below are frozen from this point. Every later change is recorded in "Deviations" with the reason and the date, and is
made before the affected result is seen. Outputs: `data/flood_validation/` (new folder, sidecars with SHA-256).

Wording: these are **agreement numbers with independent water products**, not accuracy against ground truth and not
proof. Tier A claims are worded "consistent with", never "detects" or "accuracy".

What was already looked at before this draft (disclosed): two reference windows were read to test the reader
(Thailand DSWx-HLS 2026-09-02: all 253; DSWx-S1 2026-09-04: about 98 % code 255). No NISAR pixel of any flood date
has been read.

## 1. Cases, products and times (verified in the public ASF catalog, 2026-11-15)

| Case | NISAR group | Dates (UTC) |
|---|---|---|
| Thailand | GCOV DHDH 4005 P05023, track 004 D frame 081 | 2026-09-06 11:47:12, 09-18 11:47:12, 09-30 11:47:12, 10-12 11:47:12 |
| Thailand | GCOV DHDH 4005 P05023, track 011 A frame 009 | 2026-09-06 22:45:26, 09-18 22:45:26, 09-30 22:45:26, 10-12 22:45:26 |
| Gandak | GCOV DHDH 4005 P05023, track 026 A frame 015 | 2026-09-19 23:47:03, 10-01 23:47:03 (10-13 also exists; not used) |

Tracks 149 and 048 (2005 bandwidth) are never paired with 026 A.

**09-18 products (both Thailand tracks)** carry `_F_F_` where the others carry `_N_F_`. ASF naming convention
(nisar-docs.asf.alaska.edu/naming-conventions): the field after the CRID is "Accuracy/fidelity of orbit ephemeris and
radar pointing" with N = Near Real-Time, F = Forecast; the next field is coverage, F = Full. So the 09-18 products use a
**forecast orbit**. Its effect on geolocation is not documented there. Rule: 09-18 is **never** a calibration or test
scene. It is used only in the Tier A / Tier B negative control (09-06 → 09-18), and only after an empirical
co-registration check (section 6.4) passes; otherwise the negative control is reported as not run.

## 2. Areas of interest (fixed before any water result)

10 km × 10 km UTM squares (`src.live_engine.window_polygon`), saved in `data/flood_validation/aoi/`:

| AOI | Centre | Definition | Role |
|---|---|---|---|
| `thailand_prachinburi` | 14.0541 N, 101.3724 E | Mueang Prachin Buri on the Prachin Buri River (upper Bang Pakong); OSM river 0.19 km from centre | primary |
| `gandak_eo_image` | 26.71 N, 84.28 E | centre of the NASA Earth Observatory Gandak image (user-specified). OSM main Gandak channel (ways 44690664, 656598922, 656598926, 878061921, 878737697; Burhi/Chhoti Gandak excluded) crosses the window, 6.2 km inside, nearest point 26.70688 N 84.31629 E (4.04 km); therefore **not moved** | primary |
| `gandak_bagaha` | 27.0979 N, 84.0894 E | Bagaha (record gauge named in the article) | secondary, near the T45RTK north edge (~1.0 km margin), reported separately |

Distances: Thailand window ~40 km inside both NISAR footprints; Gandak primary window 33.8 km inside the T45RTK
bounding box and ~66 km inside the NISAR 026 A footprint. Neighbouring MGRS tiles (T45RTL, T44RQR) are **not** used to
fill gaps; gaps are reported.

## 3. Reference products and class codes

References: OPERA DSWx-HLS (`OPERA_L3_DSWX-HLS_V1`, tile T47PQR / T45RTK) and OPERA DSWx-S1 (`OPERA_L3_DSWX-S1_V1`),
WTR layer (band 1) only, read in small windows by `src/podaac_reader.py`.

### 3.1 DSWx-HLS WTR — JPL D-107395 Rev B (July 10, 2024), "OPERA DSWx-HLS VERSION 1.0.1", Section 4.1, Table 4-1, Layer 1, PDF page 16 (printed page 10). Verbatim:

> 0: Not water – an area with valid reflectance data that is not open water (class 1), partial surface water (class 2), snow/ice (class 252), cloud/cloud shadow (class 253), or ocean masked (class 254). Masking can result in "not water" (class 0) where land cover masking is applied.
> 1: Open water – an area that is entirely water and unobstructed to the sensor, including obstructions by vegetation, terrain, and buildings.
> 2: Partial surface water – an inundated area that is at least 20% and less than 100% open water. This may be referred to as "subpixel inundation" when referring to a pixel's area. Examples include wetlands, water bodies with emergent vegetation, and pixels bisected by coastlines.
> 252: Snow/ice – an area identified as snow/ice according to input HLS Fmask quality assurance (QA) data.
> 253: Cloud/cloud shadow and adjacent to cloud/cloud shadow– an area identified as cloud, cloud shadow, or adjacent to those features according to input HLS Fmask quality assurance (QA) data.
> 254: Ocean masked – an area identified as ocean using a shoreline database with an added margin
> 255: Fill value (no data).

**Version mismatch (stated limitation):** the spec (Section 1.4) says "The products generated by this version of the SAS
(SOFTWARE_VERSION) v1.0.1 are consistent with this document and are tagged as version (PRODUCT_VERSION) v1.0". The files
read carry PRODUCT_VERSION 1.1 and SOFTWARE_VERSION 1.0.2 (granule names `_v1.1`). The CMR collection (Version 1.0)
still links this document. No release notes for product v1.1 / SAS 1.0.2 were found (searches of PO.DAAC, Earthdata,
opera-sds-pcm releases, 2026-11-15; the PCM release list only names "v1.0.2 of DSWx-HLS SAS" without changes). The HLS
table is therefore **taken from the v1.0 specification**, and codes are verified empirically (section 3.3).

### 3.2 DSWx-S1 WTR — JPL D-108761 Rev A (July 25, 2024; cover reads "Initial Revision"), Section 4.1, Table 4-1, Layer 1, PDF page 16 (printed page 9). Verbatim:

> 0: Not water – an area with valid data that is not open water (class 1), inundated vegetation (class 3), height above nearest drainage masked (class 250), or layover/shadow masked (class 251). Masking can result in "not water" (class 0) where land cover masking is applied.
> 1: Open water – an area that is entirely water and unobstructed to the sensor, including obstructions by vegetation, terrain, and buildings.
> 3: Inundated vegetation – an area that is considered inundated, extracted from the high value in dual polarization ratio and the wetland class in land cover map.
> 250: Height Above Nearest Drainage (HAND) masked - an area where topographic height is higher than the HAND threshold.
> 251: Layover/shadow masked - an area identified as layover or shadow computed from the geometry of the digital elevation model and sensor. The area is directly copied from input burst RTC-S1 products.
> 255: Fill value (no data)

Internal inconsistency in the same table: the BWTR layer text refers to "HAND masked (class 252), layover or shadow
(class 253)" while WTR uses 250/251. Resolved **only from codes observed in the files** (section 3.3). Version: files
carry DSWX_PRODUCT_VERSION 1.0 (matches the spec's final release) but SOFTWARE_VERSION 1.2, while the spec (Section 1.4)
refers to DSWX-SAR v1.0. No release notes for software 1.2 were found; stated limitation. The files' embedded colormap
colours codes 2, 5–8 and 254, which the WTR table does not define.

### 3.3 Code mapping used (confirmed set = defined in the spec table AND observed in the files)

| Role | DSWx-HLS codes | DSWx-S1 codes |
|---|---|---|
| open water (main outcome) | 1 | 1 |
| not water | 0 | 0 |
| partial / inundated vegetation (secondary, separate) | 2 (partial surface water) | 3 (inundated vegetation) |
| invalid (removed from numerator AND denominator) | 252 snow/ice, 253 cloud/cloud shadow, 254 ocean masked, 255 fill | 250 HAND masked, 251 layover/shadow, 255 fill |
| **undefined** (excluded; never water, never not-water; counted and reported) | any other observed code | any other observed code (incl. 2, 5–8, 252–254 if they occur) |

A code is used in the primary analysis only if it is in this table **and** is observed in at least one window we read;
observed histograms are in section 9. HAND-masked (250) counts as invalid because the product makes no water decision
there.

### 3.4 Limitations stated by the product documentation (cited)

- DSWx-HLS, PO.DAAC collection notice (CMR `OPERA_L3_DSWX-HLS_V1`, "IMPORTANT NOTICE"): "Cloud dilation and cirrus cloud
  labeling may obscure valid water detection"; "Occasional erroneous snow/ice labels" (sediment-laden water);
  "Occasional unmasked clouds over ocean".
- DSWx-HLS spec, Table 4-1: "Masking can result in 'not water' (class 0) where land cover masking is applied"; Section
  5 (p. 26): terrain-shadow areas "have a higher chance of presenting dark reflectance similar to water, which may result
  in false positives"; Section 4.2.4: forest land-cover classes are used to mask "false water detections ... due to
  vegetation-related dark reflectance".
- DSWx-S1 spec, Table 4-1: same land-cover-masking sentence; inundated vegetation is defined only within "the wetland
  class in land cover map" (so flooded cropland outside mapped wetland is not class 3); layover/shadow and HAND masks
  remove areas from classification; CONF layer: water detection "is challenging or unfeasible due to factors like
  layover/shadow effects, no-data areas, and regions where water presence is hydrologically unrealistic".
- Both: classification uses a reference water layer / land cover ancillary inputs (S1 metadata:
  `INPUT_REFERENCE_WATER_SOURCE` = JRC Global Surface Water 1984–2021), so references are not independent of historical
  water maps.

## 4. Fixed thresholds and rules

- **Usable reference scene (Tier B):** valid fraction ≥ **0.70** inside the AOI (valid = open water + not water +
  partial/inundated codes; invalid and undefined codes excluded). Scenes below are kept in the tables and marked
  **unusable**, never dropped.
- **Reference per NISAR date:** for each product type separately (HLS, S1), the usable scene with the smallest |Δt| to
  the NISAR acquisition, within ±**72 h**. Duplicate granules of one acquisition: the latest processing time is used.
  If none qualifies, that comparison is "no usable reference".
- **Permanent / pre-existing water:** open-water share in the earliest usable pre-flood reference of each product type.
- **Reference new water:** open water in the during reference AND not water in the pre reference, on pixels valid in
  both.
- **Negative-control reference (Thailand 09-18), rule "closest valid scene by time":** among S1 2026-09-19T23:08,
  S1 2026-09-20T23:00 and HLS 2026-09-23T03:38, the usable scene (≥ 0.70) with the smallest |Δt| to each track's 09-18
  acquisition. |Δt| for 004 D: +35.4 h, +59.2 h, +111.9 h; for 011 A: +24.4 h, +48.2 h, +100.9 h. HLS 09-23 is outside
  the ±72 h window and only qualifies for this control (stated exception). If none is usable, the negative control
  is Tier A only.
- **NISAR preprocessing (existing, unchanged):** valid mask, 3×3 mask-aware linear-power mean (`water_change.mask_aware_mean`),
  dB; change classes from `water_change.classify` (water if dB ≤ threshold; new water = not water before, water after,
  |Δ| ≥ min change).
- **Frozen existing defaults (reported, never tuned):** HH water threshold −16 dB, minimum change 3 dB. No existing
  default exists for HV; the HV-only frozen-default row is "not applicable".
- **Calibration (only):** Thailand track 004 D, pre 2026-09-06, during 2026-09-30, against the during-date reference
  chosen by the rule above (HLS first if usable, else S1; both reported). Grid −25.0 … −10.0 dB in 0.5 dB steps;
  choose the HH threshold, and separately the HV threshold, that maximise F1 for open water presence (ties: the value
  closest to −16 dB, then the higher value). Minimum change stays 3 dB. HH+HV rule: water if HH ≤ t_HH AND HV ≤ t_HV.
  Values are written to `data/flood_validation/calibration.json` with its SHA-256 and are **frozen**; test code refuses
  to run if the file changed (enforced in tests).
- **Test scenes:** Thailand 011 A (09-06 → 09-30) and Gandak 026 A (09-19 → 10-01). No threshold may be changed after any
  test metric is seen.
- **Grid alignment:** categorical references are resampled to the NISAR grid by **nearest neighbour** (codes are never
  interpolated; existing NISAR preprocessing on its native grid is untouched). Because 30 m reference pixels are repeated
  on the finer NISAR grid, pixel counts overstate independent samples; stated limitation. Pixels invalid in either source
  are excluded.

## 5. Tier A (no external reference)

1. **Negative control:** before-before (Thailand 09-06 → 09-18, each track) vs before-during (09-06 → 09-30). Report the
   area classified as new water in each; expected: much less in the before-before pair. Worded "consistent with".
2. **Spatial consistency (rule fixed 2026-11-15, before computing it):**
   - DEM: Copernicus DEM GLO-30 (Copernicus_DSM_COG_10_<lat>_00_<lon>_00_DEM, public COG at the exact host
     `copernicus-dem-30m.s3.amazonaws.com`, no credentials), read by a small-window reader with the same safeguards as
     the PO.DAAC reader (HTTPS only, exact host, at most 6 redirects, byte caps, certifi; no token is ever sent).
     Tiles: Thailand N14 E101; Gandak primary and Bagaha N26/N27 E084 as the window requires.
   - Slope: computed on the DEM's own grid (central differences, x/y spacing in metres from the 1 arc-second posting at
     the tile latitude), in degrees, then sampled to the NISAR grid by nearest neighbour.
   - River distance: OpenStreetMap `waterway=river` lines (all, named or not) within the AOI + 5 km, fetched once from the
     Overpass API and saved as a dated snapshot; distance in metres from each NISAR pixel centre (UTM) to the nearest line.
   - Reported for NISAR new-water pixels vs all valid pixels (frozen-default and calibrated variants, HH-only, HV-only,
     HH+HV): median slope, median river distance, share within 1 km of a river, share on slope > 5°, and the two ratios
     (new-water share / all-valid share). Wording: "consistent with concentration near rivers" only if the 1 km ratio is
     > 1; "consistent with low terrain" only if the slope ratio is < 1 (or no valid pixel exceeds 5°, which is stated —
     both sites are mostly flat, so the slope test is weak there). No pass/fail score.
3. **Permanent-water stability:** pixels open water in the earliest usable pre-flood reference: share classified as
   water by NISAR on each date.
4. **Signs:** report HH and HV change directions separately for every class and reference category. Open water is
   expected to lower both; flooded vegetation can raise HH (double bounce). No single expected sign is assumed.

## 6. Tier B (reference-based), only on usable scenes

**Primary vs sensitivity reference (fixed 2026-11-15, before any NISAR metric):** Thailand **primary = DSWx-S1** (it
has usable pre AND during scenes, so new-water metrics are possible); **sensitivity = DSWx-HLS** (during-date water
presence only). Gandak primary: DSWx-S1 only (no usable HLS). Both are always reported side by side; the primary label
never changes after results.

Per case, per reference product (HLS-only and S1-only, run separately and compared; disagreements are results), per
date: confusion matrix (TP, FP, FN, TN, invalid), precision, recall, F1, IoU for (a) open water on the during date and
(b) new water (during minus pre). Variants: HH-only, HV-only, HH+HV; frozen defaults and calibrated thresholds; time
offsets printed next to every number. No combined score. Partial (HLS 2) / inundated vegetation (S1 3): separate
secondary rows, never merged with open water. Exploratory (separately labelled, not a validation result): HH increase
≥ 3 dB with HV not decreasing, against S1 class 3 / HLS class 2.

6.4 **Co-registration check for 09-18 (forecast orbit):** peak of the HH cross-correlation between 09-06 and 09-18
compared with 09-06 vs 09-30, on the AOI; passes if the 09-18 offset is ≤ 1 pixel.

## 7. Outputs
`data/flood_validation/`: AOIs, reference histograms, calibration.json, metrics (JSON + CSV), maps (before/during/change,
reference, agreement TP/FP/FN/TN/invalid), failure cases with hypotheses, sidecar.json (SHA-256 of every output).

## 8. Other published flood extents (checked 2026-11-15; not used to choose scenes)
Copernicus EMS rapid mapping activations list (title search): no activation for Thailand; for India the latest is
EMSR357 (2019); EMSR927 (26 Aug 2026) covers Rasuwa, Nepal, not Bihar. No UNOSAT product for either event found by
web search. None is used.

## 9. Observed reference code histograms

Generated from `data/flood_validation/reference/scan.json` (61 scene windows, 12,714,928 bytes read, 2026-11-15). Valid = open + not water + partial/inundated; usable = valid fraction ≥ 0.70. Histogram = every WTR code present in the AOI window (pixel counts).

### thailand_prachinburi

| Product | Acquired (UTC) | Sensor | Valid | Usable | Open water / valid | Partial or inundated / valid | Histogram (code: pixels) |
|---|---|---|---:|---|---:|---:|---|
| HLS | 2026-09-02 03:35 | S2B | 0.000 | **unusable** |  |  | 253: 115600 |
| HLS | 2026-09-09 03:42 | S2A | 0.125 | **unusable** | 0.023 | 0.345 | 0: 9106, 1: 336, 2: 4977, 252: 2061, 253: 99112, 255: 8 |
| HLS | 2026-09-12 03:35 | S2B | 0.000 | **unusable** |  |  | 255: 115600 |
| HLS | 2026-09-23 03:38 | L9 | 0.000 | **unusable** |  |  | 255: 115600 |
| HLS | 2026-09-29 03:42 | S2A | 0.349 | **unusable** | 0.577 | 0.065 | 0: 14458, 1: 23282, 2: 2613, 252: 10955, 253: 64292 |
| HLS | 2026-10-01 03:37 | L8 | 0.655 | **unusable** | 0.591 | 0.128 | 0: 21330, 1: 44701, 2: 9652, 252: 1817, 253: 37898, 255: 202 |
| HLS | 2026-10-02 03:31 | L9 | 0.934 | yes | 0.569 | 0.120 | 0: 33508, 1: 61413, 2: 12996, 253: 4023, 255: 3660 |
| HLS | 2026-10-02 03:35 | S2B | 0.842 | yes | 0.601 | 0.077 | 0: 31371, 1: 58477, 2: 7531, 252: 17510, 253: 711 |
| S1 | 2026-09-04 11:19 | S1C | 0.022 | **unusable** | 0.000 | 0.006 | 0: 2497, 3: 16, 255: 113087 |
| S1 | 2026-09-08 23:00 | S1C | 1.000 | yes | 0.020 | 0.011 | 0: 112063, 1: 2261, 3: 1276 |
| S1 | 2026-09-14 23:00 | S1D | 1.000 | yes | 0.024 | 0.015 | 0: 111148, 1: 2744, 3: 1708 |
| S1 | 2026-09-15 11:28 | S1D | 1.000 | yes | 0.023 | 0.019 | 0: 110773, 1: 2606, 3: 2221 |
| S1 | 2026-09-19 23:08 | S1D | 1.000 | yes | 0.030 | 0.019 | 0: 110040, 1: 3415, 3: 2144, 251: 1 |
| S1 | 2026-09-20 23:00 | S1C | 1.000 | yes | 0.024 | 0.017 | 0: 110825, 1: 2791, 3: 1984 |
| S1 | 2026-09-22 11:19 | S1D | 0.023 | **unusable** | 0.000 | 0.007 | 0: 2677, 3: 19, 255: 112904 |
| S1 | 2026-09-26 23:00 | S1D | 1.000 | yes | 0.113 | 0.027 | 0: 99421, 1: 13042, 3: 3137 |
| S1 | 2026-09-27 11:28 | S1D | 1.000 | yes | 0.113 | 0.021 | 0: 100140, 1: 13060, 3: 2400 |
| S1 | 2026-10-01 23:08 | S1D | 1.000 | yes | 0.339 | 0.014 | 0: 74859, 1: 39177, 3: 1562, 251: 2 |
| S1 | 2026-10-02 23:00 | S1C | 1.000 | yes | 0.333 | 0.027 | 0: 73974, 1: 38530, 3: 3096 |
| S1 | 2026-10-02 23:00 | S1C | 0.000 | **unusable** |  |  | 255: 115600 |
| S1 | 2026-10-04 11:19 | S1D | 0.025 | **unusable** | 0.002 | 0.007 | 0: 2854, 1: 7, 3: 21, 255: 112718 |

### gandak_eo_image

| Product | Acquired (UTC) | Sensor | Valid | Usable | Open water / valid | Partial or inundated / valid | Histogram (code: pixels) |
|---|---|---|---:|---|---:|---:|---|
| HLS | 2026-09-16 04:56 | S2B | 0.102 | **unusable** | 0.000 | 0.038 | 0: 11834, 1: 2, 2: 470, 252: 6785, 253: 102013 |
| HLS | 2026-09-18 04:54 | L9 | 0.675 | **unusable** | 0.074 | 0.107 | 0: 66939, 1: 6048, 2: 8748, 253: 39369 |
| HLS | 2026-09-19 04:48 | L8 | 0.042 | **unusable** | 0.229 | 0.098 | 0: 3460, 1: 1178, 2: 503, 253: 115963 |
| HLS | 2026-09-20 04:52 | S2A | 0.000 | **unusable** |  |  | 255: 121104 |
| HLS | 2026-09-21 04:57 | S2C | 0.217 | **unusable** | 0.002 | 0.137 | 0: 22639, 1: 45, 2: 3587, 252: 1980, 253: 92825, 255: 28 |
| HLS | 2026-09-27 04:48 | L9 | 0.084 | **unusable** | 0.065 | 0.225 | 0: 7203, 1: 660, 2: 2282, 253: 110446, 255: 513 |
| HLS | 2026-09-28 04:47 | S2C | 0.000 | **unusable** |  |  | 255: 121104 |
| HLS | 2026-10-01 04:57 | S2C | 0.077 | **unusable** | 0.045 | 0.443 | 0: 4779, 1: 423, 2: 4137, 252: 7841, 253: 103924 |
| HLS | 2026-10-03 04:46 | S2B | 0.000 | **unusable** |  |  | 255: 121104 |
| HLS | 2026-10-03 05:02 | S2A | 0.032 | **unusable** | 0.000 | 0.550 | 0: 1722, 2: 2104, 252: 6347, 253: 110931 |
| HLS | 2026-10-04 04:54 | L9 | 0.053 | **unusable** | 0.139 | 0.579 | 0: 1806, 1: 896, 2: 3722, 253: 114281, 255: 399 |
| HLS | 2026-10-05 04:48 | L8 | 0.019 | **unusable** | 0.439 | 0.159 | 0: 914, 1: 996, 2: 361, 253: 118833 |
| S1 | 2026-09-14 12:29 | S1D | 1.000 | yes | 0.066 | 0.008 | 0: 112097, 1: 8026, 3: 981 |
| S1 | 2026-09-17 00:19 | S1D | 1.000 | yes | 0.064 | 0.017 | 0: 111321, 1: 7740, 3: 2043 |
| S1 | 2026-09-21 12:20 | S1D | 0.000 | **unusable** |  |  | 255: 121104 |
| S1 | 2026-09-24 00:11 | S1D | 0.000 | **unusable** |  |  | 255: 121104 |
| S1 | 2026-09-26 12:29 | S1D | 1.000 | yes | 0.019 | 0.037 | 0: 114397, 1: 2251, 3: 4456 |
| S1 | 2026-09-29 00:19 | S1D | 1.000 | yes | 0.110 | 0.025 | 0: 104803, 1: 13295, 3: 3006 |
| S1 | 2026-10-03 12:20 | S1D | 0.000 | **unusable** |  |  | 255: 121104 |

### gandak_bagaha

| Product | Acquired (UTC) | Sensor | Valid | Usable | Open water / valid | Partial or inundated / valid | Histogram (code: pixels) |
|---|---|---|---:|---|---:|---:|---|
| HLS | 2026-09-16 04:56 | S2B | 0.123 | **unusable** | 0.000 | 0.045 | 0: 14293, 2: 678, 252: 7052, 253: 31723, 255: 68055 |
| HLS | 2026-09-18 04:54 | L9 | 0.000 | **unusable** | 0.375 | 0.175 | 0: 18, 1: 15, 2: 7, 253: 53706, 255: 68055 |
| HLS | 2026-09-19 04:48 | L8 | 0.000 | **unusable** |  |  | 255: 121801 |
| HLS | 2026-09-20 04:52 | S2A | 0.000 | **unusable** |  |  | 255: 121801 |
| HLS | 2026-09-21 04:57 | S2C | 0.183 | **unusable** | 0.053 | 0.262 | 0: 15268, 1: 1192, 2: 5856, 252: 4928, 253: 26502, 255: 68055 |
| HLS | 2026-09-27 04:48 | L9 | 0.000 | **unusable** |  |  | 255: 121801 |
| HLS | 2026-09-28 04:47 | S2C | 0.000 | **unusable** |  |  | 255: 121801 |
| HLS | 2026-10-01 04:57 | S2C | 0.002 | **unusable** | 0.030 | 0.333 | 0: 168, 1: 8, 2: 88, 252: 3984, 253: 49498, 255: 68055 |
| HLS | 2026-10-03 04:46 | S2B | 0.000 | **unusable** |  |  | 255: 121801 |
| HLS | 2026-10-03 05:02 | S2A | 0.096 | **unusable** | 0.054 | 0.426 | 0: 6081, 1: 635, 2: 4991, 252: 10691, 253: 31348, 255: 68055 |
| HLS | 2026-10-04 04:54 | L9 | 0.037 | **unusable** | 0.552 | 0.019 | 0: 1950, 1: 2506, 2: 84, 253: 49206, 255: 68055 |
| HLS | 2026-10-05 04:48 | L8 | 0.000 | **unusable** |  |  | 255: 121801 |
| S1 | 2026-09-14 12:29 | S1D | 0.441 | **unusable** | 0.219 | 0.014 | 0: 41212, 1: 11786, 3: 748, 255: 68055 |
| S1 | 2026-09-17 00:19 | S1D | 0.441 | **unusable** | 0.214 | 0.023 | 0: 41053, 1: 11482, 3: 1211, 255: 68055 |
| S1 | 2026-09-21 12:20 | S1D | 0.000 | **unusable** |  |  | 255: 121801 |
| S1 | 2026-09-24 00:11 | S1D | 0.000 | **unusable** |  |  | 255: 121801 |
| S1 | 2026-09-26 12:29 | S1D | 0.441 | **unusable** | 0.081 | 0.119 | 0: 42985, 1: 4352, 3: 6409, 255: 68055 |
| S1 | 2026-09-29 00:19 | S1D | 0.441 | **unusable** | 0.323 | 0.023 | 0: 35144, 1: 17365, 3: 1237, 255: 68055 |
| S1 | 2026-10-03 12:20 | S1D | 0.000 | **unusable** |  |  | 255: 121801 |

### Codes actually observed (resolves section 3.3)

- DSWx-HLS observed: 0, 1, 2, 252, 253, 255. Defined but not observed: 254 (ocean masked; not applicable inland).
- DSWx-S1 observed: 0, 1, 3, 251, 255. Defined but not observed: 250. **Codes 252/253 (named for HAND/layover in the spec's BWTR text) never occur in any S1 WTR window; 251 does.** The files therefore use the WTR-table codes (250/251); the BWTR sentence disagrees with the files and is not used.
- Colormap-only codes (S1: 2, 5–8, 254): **not observed** in any window. No undefined code was observed in any scene; the undefined-code rule stays in force.
- The 100 % cloud HLS window (2026-09-02) shows only 253; fill-only windows show only 255, as the spec states.

### Consequences fixed by the section 4 rules (stated before any NISAR result)

- **Gandak secondary (Bagaha):** every scene has 68,055 fill pixels (55.9 %) — the window extends beyond the actual T45RTK tile data; maximum valid fraction 0.441. **No usable reference; Bagaha is Tier A only.**
- **Gandak primary:** no DSWx-HLS scene is usable (all cloud-dominated, max valid 0.675 on 09-18). DSWx-S1 usable: 09-14 12:29, 09-17 00:19, 09-26 12:29, 09-29 00:19. Reference for NISAR 09-19 23:47: S1 09-17 00:19 (Δt −71.5 h); for NISAR 10-01 23:47: S1 09-29 00:19 (Δt −71.5 h). Both are just inside ±72 h. **Gandak Tier B is S1-only; the HLS-only sensitivity run is not possible.**
- **Thailand pre-flood references:** no DSWx-HLS pre-flood scene is usable; S1 usable from 09-08. Pre reference: S1 09-08 23:00 for both tracks (Δt +59.2 h for 004 D, +48.2 h for 011 A). **HLS new-water metrics are not possible (no usable HLS pre scene); HLS is used for during-date water presence only.**
- **Thailand during references (NISAR 09-30):** HLS: 10-02 03:31 L9 (Δt +39.7 h for 004 D, +28.8 h for 011 A; 10-01 L8 is unusable at 0.655). S1: 10-01 23:08 (Δt +35.4 h for 004 D, +24.4 h for 011 A; S1 09-27 11:28 is −72.3 h, outside the window).
- **Calibration reference** (rule: HLS first if usable): DSWx-HLS 2026-10-02 03:31 L9 against NISAR 004 D 09-30 (Δt +39.7 h); S1 10-01 23:08 also reported.
- **Negative-control reference** (rule: closest usable scene by time among S1 09-19, S1 09-20, HLS 09-23): **S1 2026-09-19 23:08** for both tracks (+35.4 h for 004 D, +24.4 h for 011 A; valid 1.000). HLS 09-23 is all fill.
- **Permanent / pre-existing water:** S1 2026-09-08: open water 0.020 and inundated vegetation 0.011 of the Thailand window; Gandak S1 09-14: open 0.066, 09-17: 0.064. No usable HLS pre-flood scene, so no HLS permanent-water share.

### Reference-only findings (no NISAR data involved)

- Thailand, S1 09-08 → 10-01: open water 0.020 → 0.339; new open water 0.323 of the window (37,365 pixels at 30 m). 09-08 → 10-02: 0.317. 09-08 → 09-19 (negative-control date): 0.012 new open water (open 0.030 on 09-19), so 09-19 is close to pre-flood in S1.
- Thailand, **HLS vs S1 disagree on 2026-10-02** (03:31 L9 vs 23:00 S1, 19.5 h apart, both valid on 0.934 of the window): open water 0.569 (HLS) vs 0.313 (S1); IoU of open water 0.549; pixel agreement 0.743. Partial surface water (HLS) 0.120 vs inundated vegetation (S1) 0.027. This disagreement is a result; neither product is preferred.
- Gandak primary, S1 ascending 09-17 → 09-29: open water 0.064 → 0.110; new open water 0.042. S1 descending 09-14 → 09-26: open water 0.066 → 0.019 (decrease). The two S1 geometries disagree on the direction of change between their dates; reported, not resolved.


## Deviations
1. 2026-11-15, before any NISAR result: `src/podaac_reader.py` range reads were changed to fetch and cache 64 KiB blocks
   (the uncached first scan took ~2 min per window); byte caps and host rules unchanged. The interrupted partial scan
   output (written by this run only) was deleted and the scan rerun in full.
2. 2026-11-15: PO.DAAC redirects to the CloudFront host `deotb6e7tfubr.cloudfront.net`, not S3; the owner approved this
   exact host (treated like S3: no token, signed query never stored).
3. **2026-11-15, after stage a (calibration, in-sample) and BEFORE any test result (stages b–e not run).**
   - *What happened:* the frozen calibration rule (section 4) optimised F1 for **open water presence on the flood date**
     against **DSWx-HLS 2026-10-02**, and the HH optimum landed on the **edge of the preset grid (−10.0 dB; F1 still rising:
     0.899 at −11.5, 0.917 at −10.0)**; HV −15.5 dB. Kept frozen exactly as computed; the grid is not widened and nothing is
     recalibrated (`data/flood_validation/calibration.json`, SHA-256 7a312b32400bfa47df10c45e1537f6ce55c2eed444f79c9f2ed207faadfd1b6e).
   - *Inconsistency, stated honestly:* the calibration objective (presence vs HLS) does not match the protocol's primary
     reference for Thailand (S1, fixed before results) nor the app's purpose (**new** water). In-sample, the calibrated HH
     threshold lowered new-water agreement against S1 from F1 0.69 (default) to 0.41, because −10 dB already labels many
     pre-flood paddy pixels as water. HLS marks 0.65 of valid pixels as open water vs 0.34 for S1, which pulled the
     threshold up.
   - *Decision (owner, before any test result):*
     - **Primary configuration for stages b–e = the untuned default** fixed before any data was seen: HH ≤ −16 dB with
       |ΔHH| ≥ 3 dB (`water_change.classify` defaults; `src.flood_validation.PRIMARY_CONFIG`). **Primary outcome = new open
       water against DSWx-S1.**
     - The frozen calibrated thresholds (HH −10.0, HV −15.5, HH+HV) are **secondary**, reported exactly as frozen.
     - HV-only and HH+HV have no untuned default: reported **only as secondary/exploratory** with the frozen calibrated
       values; no new HV threshold is chosen.
     - DSWx-HLS stays the sensitivity reference. No third configuration.
     - The inundated-vegetation rule (ΔHH ≥ 3 dB, ΔHV ≥ 0) is **exploratory and failed** in the calibration scene
       (F1 0.02 vs S1 new inundated vegetation); in stages b–e it is reported only as exploratory, never as a claim.
   - *Commit recording this deviation and the tests:* 67ff992a142488c1a5743119c3cd5357e28c26e1 (2026-11-15; this hash was filled in right after that commit)
4. **2026-11-15, after stage b, before stage c.** Added a **spatial block bootstrap 95 % interval** for precision, recall,
   F1 and IoU of the PRIMARY rows: confusion counts per 1 km × 1 km block (100 × 100 NISAR pixels at 10 m), blocks resampled
   with replacement (as many as the grid has), 1000 resamples, seed 20261115, 2.5/97.5 percentiles
   (`src.flood_validation.block_bootstrap`). It does **not** change any point estimate: stages a and b were recomputed from the
   cached windows and matched the saved TP/FP/FN/TN exactly (`data/flood_validation/bootstrap_ab/`). Stages c–e include it.
   Also added (descriptive, no threshold): where PRIMARY false positives/negatives concentrate, using the Copernicus DEM,
   one dated OpenStreetMap snapshot (rivers, land use) and the S1 flood edge (`data/flood_validation/context/`).

5. **2026-11-15, publication (no rule or result changed).** The commit hashes cited above (freeze commit `181782456a`,
   Deviation 3 `67ff992a14`) belong to the team's private development history. The public repository starts from a
   single release commit, so these hashes do not resolve there. The order of events (protocol committed before any NISAR
   flood window was read; deviations recorded before the affected results) is documented in this file.

## Run log (after the deviations above; no rule changed)
- Stage a (calibration, Thailand 004 D) and stage b (test, Thailand 011 A): see Deviation 3 and `data/flood_validation/step2a|b/`.
- Stage c (test, Gandak primary 026 A, S1 only): PRIMARY new open water F1 0.24 [0.17, 0.31] — **reported as a failure.**
  Hypotheses only (not tested): both S1 references are 71.5 h before their NISAR dates and water may have kept spreading
  after 09-29; little new water in the window (4 %); open water darkens weakly here (median ΔHH −2.3 dB vs −6.3 dB in
  Thailand); S1 new inundated vegetation brightens HH (median +1.0 dB). No other Gandak scene (10-13) or track (098 A)
  is added, by decision of the owner.
- Stage d (negative control, Thailand both tracks): co-registration check passed (|offset 09-06→09-18| 0.14 px for 004 D,
  0.06 px for 011 A; rule ≤ 1 px). Results in `data/flood_validation/step2d/`.
- Stage e (Bagaha, Tier A only): **not run (time).**

