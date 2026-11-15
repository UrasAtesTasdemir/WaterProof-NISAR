# Change Compass — method and interpretation table

**Status: literature-based interpretation, not validated for this site.**
The Compass turns a region's median change in HH and HV backscatter into a
*hypothesis* label. It does not classify land cover, water or flooding.

## Inputs (real, cached, offline)

| Item | Source |
|---|---|
| HH power, 21 June & 3 July 2026 | `data/subsets/nisar_hhhh_*.tif` (verified by the existing `load_cached`) |
| HV power, same products | `data/polarization_analysis/raw/hvhv_*.tif` (bounded range reads from an earlier phase; SHA-256 sidecars checked) |
| Pair change written for the app | `data/hv/pair_change_db.tif`, `pair_filtered_db.tif`, sidecar `pair_change_db.json` |
| Gate analysis | `data/hv/hv_signal_assessment.json`, `data/hv/change_histograms.png` |

Products: `NISAR_L2_PR_GCOV_023_105_A_017_4005_DHDH_A_20260621T111906_…` and
`NISAR_L2_PR_GCOV_024_105_A_017_4005_DHDH_A_20260703T111905_…` (full IDs in the sidecar).

Preprocessing reuses `src.polarization.prepare_polarizations` → `src.water_change.mask_aware_mean`
/ `power_to_db`: joint per-date HH/HV positive-finite mask, 3×3 mask-aware mean in
linear power, then `10·log10`. Change = after dB − before dB. The result agrees with
the earlier `data/polarization_analysis/two_date/before_after_delta_db.tif` to < 1e-6 dB.

Regenerate (offline): `python scripts/process_hv_compass.py --overwrite` (only rewrites `data/hv/`).

## Gate: does HV carry usable signal? (computed before the UI was built)

| Indicator (whole common AOI, 138,779 px) | ΔHH | ΔHV |
|---|---:|---:|
| Median | −1.39 dB | −0.72 dB |
| IQR | −2.43 … −0.41 dB | −1.64 … +0.18 dB |
| Lag-5 px (50 m) spatial autocorrelation | 0.30 / 0.28 | 0.18 / 0.18 |
| Lag-20 px (200 m) spatial autocorrelation | 0.17 / 0.17 | 0.08 / 0.10 |
| Pearson r (ΔHH, ΔHV) | 0.35 | |

Reading: HV change is spatially structured beyond the 3×3 filter support and
partly shared with HH, so it is **usable with caution at scene scale**. A smooth
large-scale pattern (incidence angle, calibration) could also produce some of the
autocorrelation.

**Dark-pixel limitation.** New-water candidate pixels have median filtered HV of
−21.9 / −22.3 dB, close to the scene's 1st percentile (−22.5 / −22.6 dB). Their HV
barely changes (−0.54 dB) while HH drops 3.65 dB. A stable lower bound like this is
consistent with, but does not prove, a noise floor. The noise floor itself is
**not available**: the GCOV noise-equivalent layers are documented in linear DN²
and no verified conversion to gamma-0 was established (see
`data/scientific_diagnostics/REPORT.md`). The Compass therefore flags any region
whose median HV is at or below the scene's 5th percentile on either date.

## Pattern rules (applied to region medians, in this order)

τ = dead zone (default 1.5 dB, user-adjustable). The default exceeds the unexplained
scene-wide median HH change (−1.39 dB); it is not a calibrated noise level.

| # | Condition | Pattern |
|---|---|---|
| 1 | fewer than 50 valid pixels | No clear pattern (inconclusive) |
| 2 | max(\|ΔHH\|, \|ΔHV\|) < τ | No clear pattern (dead zone) |
| 3 | p25 < 0 < p75 for both ΔHH and ΔHV | No clear pattern (pixels disagree) |
| 4 | ΔHH ≤ −τ and ΔHV ≤ −τ/2 | Pattern consistent with a smoother surface (HH and HV both darker) |
| 5 | ΔHH ≤ −τ and \|ΔHV\| < τ/2 | HH darker, HV roughly unchanged |
| 6 | ΔHH ≥ +τ and ΔHV < +τ | Pattern consistent with HH-dominated brightening |
| 7 | ΔHV ≤ −τ and ΔHH > −τ | Pattern consistent with reduced volume scattering |
| 8 | ΔHV ≥ +τ | Pattern consistent with more volume scattering or roughness |
| 9 | anything else | No clear pattern (mixed directions) |

**Two references, always.** Every region is evaluated on its raw medians and on its
medians minus the scene-wide median (ΔHH −1.39 dB, ΔHV −0.72 dB). If the two
patterns differ, the result is **"Reading depends on the reference"** and both readings
are shown with their numbers. Subtracting the scene median is a comparison, not a correction.

**Change from the first version (hardening phase).** The first version used "ΔHV ≤ 0"
for the open-water pattern. A region with ΔHH = −3.65 dB then switched between
"open water" and "inconclusive" when ΔHV crossed zero by a few hundredths of a dB.
Rule 5 now reports "HH darker, HV roughly unchanged" for small HV changes (|ΔHV| < τ/2),
and rule 4 requires a clear HV decrease. Pattern titles describe the radar change, not a cause.

Every pattern is shown with a list of alternative explanations that the pair cannot
rule out: moisture, roughness (including wind on water), vegetation change,
processing or scene-wide shift, and geometry/registration/mixed pixels, plus
pattern-specific items. For "HH darker, HV roughly unchanged", that includes HV sitting near the noise floor.

## Literature basis (general tendencies, not site validation)

- Smooth open water acts as a specular reflector, lowering both co- and cross-pol
  backscatter (e.g. NASA SAR Handbook, Flores-Anderson et al., 2019, flood-mapping chapters).
- At L-band, water beneath emergent vegetation can strengthen HH through
  trunk–water double bounce (Richards, Woodgate & Skidmore, 1987; Hess, Melack &
  Simonett, 1990).
- HV is dominated by volume scattering and tracks canopy volume/biomass, so HV loss
  with little HH change is commonly associated with vegetation loss (e.g. Le Toan et
  al., 1992; NISAR Science Users' Handbook).

Every one of these patterns has competing explanations (soil moisture, wind,
roughness, geometry, provisional calibration, a scene-wide offset, mixed pixels).
That is why each label carries its numbers and a caution line, and why
"inconclusive" is a first-class answer.

## Results on the saved Louisiana regions (τ = 1.5 dB)

| Region | Pixels | Raw ΔHH / ΔHV (dB) | Scene-relative ΔHH / ΔHV (dB) | Raw pattern | Relative pattern | Result |
|---|---:|---|---|---|---|---|
| Whole common AOI | 138,779 | −1.39 / −0.72 | 0.00 / 0.00 | No clear pattern | No clear pattern | No clear pattern |
| New water candidates (baseline −16 dB / 3 dB) | 569 | −3.65 / −0.54 | −2.26 / +0.18 | HH darker, HV roughly unchanged | same | HH darker, HV roughly unchanged (HV dark-level flag) |
| Investigation region 1 | 74 | −1.95 / −0.32 | −0.56 / +0.40 | HH darker, HV roughly unchanged | No clear pattern | **Reading depends on the reference** |
| Investigation regions 3, 4, 5 | 464 / 158 / 130 | −4.40 / −2.75 … | | Smoother-surface pattern | same | Smoother-surface pattern |
| Persistent / receded candidates, region 2 | 158 / 5 / 30 | | | No clear pattern | No clear pattern | No clear pattern (n < 50 for two) |

These are descriptive patterns to guide further investigation, not findings.
