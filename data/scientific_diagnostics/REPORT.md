# Phase 4 — scientific reliability and radar noise diagnostics

## Protection and scope

Recoverable Git checkpoint: `24880228d4b6b7a06495fb5d681a43f9be55e824`, tag
`pre-scientific-diagnostics-phase4`. The pre-change application passed 62 tests.
SHA-256 fingerprints protect all 336 previous data files, including HH/HV cubes,
geographic maps, original classification and Sentinel-1 benchmark results.
No production classifier, default measurement, scene normalization, benchmark,
region or model was changed. All new results are separate in this directory.

## Real data and darkening

The six verified frequency-A HH/HV observations (June21, July3, July15, July27,
August20, September1 2026) retain their actual IDs/timestamps in `results.json`.
All analyses use the existing 10 m EPSG:32615 grid and the fixed 138,779-pixel,
13.8779 km² positive-finite common footprint. No SAR power was downloaded again.
Distributions are based on existing matched 3×3 linear-power preprocessing.

| Date | HH spatial median dB | HV spatial median dB |
|---|---:|---:|
| June21 | −5.6422 | −13.3707 |
| July3 | −6.9871 | −14.1466 |
| July15 | −6.4289 | −14.0404 |
| July27 | −7.0949 | −14.3963 |
| August20 | −7.3766 | −14.6086 |
| September1 | −6.3289 | −14.2439 |

All 15 date pairs for both bands (30 distributions) include median, MAD,
normal-scaled MAD, IQR, 5/25/75/95 percentiles and histograms. Histograms retain
out-of-range tail counts; robust summaries include all valid pixels. For July3
minus June21, HH median change is −1.3888 dB, scaled spatial MAD 1.4960 dB,
IQR 2.0227 dB; HV values are −0.7204, 1.3514 and 1.8236 dB respectively.
These are spatial distributions, not independent-sample noise uncertainties.
Difference of scene medians is not generally median pixel-wise change.

Candidate quiet-looking land patches were selected without ranking June21/July3
changes: nonoverlapping 21×21-pixel tiles, all common valid, at least 90% of cells
farther than100 m from historical mapped waterways; reference-four-date median
HH>−12 and HV>−20 dB; reference tile-median temporal IQR≤1.5 dB in both channels.
Among 89 eligible tiles, the three lowest combined spatial IQRs of reference
temporal-median images were retained, with centers separated by at least300 m.
Reference dates were July15, July27, August20 and September1 only.

| Region (native row/column) | HH median original-pair Δ dB | HV median Δ dB |
|---|---:|---:|
| 168/315 | −2.2129 | −1.3231 |
| 210/315 | −2.5720 | −1.1558 |
| 21/63 | −0.8665 | −0.0846 |

This selected sample is not a set of verified invariant calibration targets.
Widespread but spatially different darkening, differing HH/HV responses and the
nonmonotonic six-date medians are compatible with environmental/geometry/noise
or processing influences; they do not uniquely identify a cause. Moisture,
vegetation, wind, tides/drainage, registration and provisional radiometry remain
possible contributors. No constant sensor-bias explanation is established and
no scene median is subtracted.

## Actual quality metadata and HV floor limits

Small `numberOfLooks` and `mask` windows were read for the original pair using
the existing bounded HTTPS pipeline. An optional read-only inspection callback
uses that same transfer budget to inspect GCOV calibration metadata. No full
HDF5 was downloaded. Each product is approximately6.6 GB; reads were only ranges.

Median numberOfLooks is 4.7450118 and 4.7451606; June21 AOI range is
3.7277–5.9625. This variable describes the adaptive averaging ensemble, **not
equivalent independent looks or an ENL estimate**. Both observed masks are
code1 for every common pixel. The HDF5 description identifies0 as a partially
focused/invalid averaging ensemble and255 as outside acquisition extent. These
checks do not require changing the original positive-finite masks. Quality
windows were inspected only for these two dates; later-four-date quality flags
were not independently assessed in this bounded study.

Noise-equivalent HH/HV datasets are present on a 347×353 coarse projected grid,
but their actual description is **linear DN²**, despite the generic unit `1`.
The science arrays are calibrated gamma-0. A verified DN²-to-gamma-0/RTC conversion
was not established, so no floor, HV SNR, noise fraction or uncertainty percentage
is inferred or fabricated. Both products report `noiseCorrectionApplied=False`.
That flag alone does not quantify additive bias or explain the observed darkening.

The first metadata serialization attempt encountered a non-native JSON value;
the serializer was fixed and metadata inspection retried, reusing the already
saved quality windows. The initial error log/blocker file is retained as an
attempt record; `quality_metadata.json` and `processing_flags.json` show the final
successful checks. Successful retry/flag reads are recorded per product. No
credentials, signed URLs or secret-bearing exceptions were printed or saved.

## Speckle, texture and conditional ENL

Raw local linear-power CV across the selected three patches and six dates ranges
approximately0.426–0.540; after the existing 3×3 mean it is0.178–0.242. Smoothing
reduces spatial variation but also mixes real boundaries; this is not proof of
better accuracy. Spatial texture, temporal environmental variation and additive
noise are not the same quantity and are not separated by this experiment.

ENL moment estimates μ²/s² are withheld unless a raw patch has ≥400 fully valid
samples, relative planar trend≤0.10, quadrant-mean contrast≤0.15, absolute lag1
correlation≤0.20, positive variance and local looks IQR/median≤0.10. These are
prespecified screening rules, not formal homogeneity tests or calibrated
significance levels. No filtered patch is used for ENL. Without inspected looks
metadata, later dates do not qualify automatically.

Only two HV patches on July3 pass this screening: region2 conditional ENL4.0090
and region3 ENL3.9008. Their raw CVs are0.4994/0.5063. These are **provisional spatial
moment proxies under the homogeneity assumption**, not verified sensor noise,
thermal-noise floors, confidence bounds or exact effective looks. Residual
heterogeneity, higher-lag correlation and selection effects can bias them. No HH
patch in the inspected original pair qualified. They cannot calibrate a universal
3 dB change threshold.

## Baseline versus ONE diagnostic alternative

The original cross-water-threshold classifier remains unchanged. Fixed settings:
HH≤−16 dB, 3×3 normalized linear-power mean, absolute change≥3 dB. A 3 dB power
change is approximately a factor of2; this physical magnitude does **not** imply
statistical significance or establish an optimal flood threshold.

The one alternative is a **retrospective reference-temporal-scaled log-ratio**:

`S = ΔdB / max(1.4826022185 × MAD(other four dates), 1 dB)`

Both June21 and July3 are excluded from the scale reference. Four finite reference
dates are required; missing histories remain unknown and zero spread uses the
floor. The fixed diagnostic cutoff is|S|≥3, combined with the **same existing**
water-threshold crossings solely for candidate-area comparison. The score and
new support masks are diagnostics, not a deployed/new water classifier.

The scale includes real environmental variation, not just measurement error.
The 1 dB floor and cutoff3 were declared before results and never tuned against
benchmark labels. Normal-scaling MAD does not make the score normally distributed;
it is **not 3σ, probability, p-value or calibrated confidence**. Four references
are sparse and later real water/environmental changes can inflate the scale and
suppress genuine transitions. It is not a real-time detection method.

| Gate (original pair) | Expansion candidate km² | Recession candidate km² |
|---|---:|---:|
| Production fixed3 dB | 0.0569 | 0.0005 |
| Diagnostic temporal-scaled|S|≥3 | 0.0448 | 0.0003 |

The diagnostic retains448/569 baseline expansion pixels and3/5 recession pixels;
no reference-support pixels are missing. Median effective gate is3.000 dB,
75th spatial percentile3.545 dB and95th5.680 dB. The floor guarantees an effective
gate≥3 dB; fewer candidates are therefore expected by construction and **cannot
be claimed as improved accuracy**. HH/HV score support is reported separately,
without using HV to classify flooded vegetation.

## Sensitivity and spatial stability

Twelve prespecified combinations vary water threshold (−14/−16/−18/−20 dB) and
linear-power filter side (1/3/5), while holding the original3 dB gate fixed.

| Linear filter | −14 dB expansion/recession km² | −16 dB | −18 dB | −20 dB |
|---|---|---|---|---|
| 1×1 | 0.6701 / 0.0920 | 0.3432 / 0.0533 | 0.1299 / 0.0237 | 0.0288 / 0.0047 |
| 3×3 | 0.1652 / 0.0072 | **0.0569 / 0.0005** | 0.0091 / 0 | 0 / 0 |
| 5×5 | 0.0485 / 0.0014 | 0.0141 / 0 | 0.0011 / 0 | 0 / 0 |

This large sensitivity is a main reliability concern. Expansion appears in at
least one scenario over0.8152 km², but no pixel appears in all twelve; the empty
intersection is partly guaranteed by strict−20 dB smoothed scenarios having
zero detections, and is not proof that every baseline candidate is false.

The separate, declared families provide more interpretable consistency checks:
63 expansion pixels (0.0063 km²) remain candidates across all1/3/5 filter sizes
at−16 dB;29 (0.0029 km²) remain across−14/−16/−18 at3×3. These are setting-stability
patterns, not validation. There is no recession intersection in either family.
Historical geometry places431/569 original expansion pixels within30 m of mapped
waterways, reproducing earlier context. Near-water candidates are not removed;
real changes can occur there, and historical geometry cannot verify the dates.

## Implementation, tests and presentation decision

Modified preexisting code: `app.py` adds a lazily loaded optional workspace;
`src/nisar_data.py` adds the optional bounded read-only metadata callback with
old behavior as default; README documents the study. New files:
`src/scientific_diagnostics.py`, `src/diagnostics_panel.py`,
`scripts/inspect_radar_quality.py`, `scripts/run_scientific_diagnostics.py`,
`tests/test_scientific_diagnostics.py`, and this separate output directory.
Original classifier, processing outputs and benchmark values are unchanged.

**71 tests passed** (62 existing +9 new). Checks cover robust missing-value and
outlier behavior; leave-pair-out/floor/invalid histories; conditional ENL rejection;
real source/CRS/unit/mask/area consistency; all pair histograms; baseline recovery;
alternative support; quality units/flags; prior file hashes; widget changes,
missing-file recovery, workspace return and old HH/HV/time-series/map/benchmark
functionality. Synthetic values are confined to unit fixtures. Browser checks
and final preservation fingerprints are recorded in `verification.json`.

The small **Scientific Diagnostics** workspace uses cached summaries only,
with HH/HV/date-pair distributions, change histograms, the fixed baseline versus
alternative comparison, threshold/filter sensitivity and actual quality/texture
limits. It does not trigger NASA access or recompute production outputs.

**Ready for a final exploratory scientific presentation**, provided claims remain
surface-scattering exploration and unvalidated water-change candidates. **Not
ready for confirmed flood mapping, validated NISAR accuracy, or noise-calibrated
probabilities.** No further major feature, classifier, region, benchmark or phase
was implemented. Independent validation remains the missing evidence.

Sources: [GCOV product guide](https://nisar-docs.asf.alaska.edu/gcov/),
[MAD definition](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.median_abs_deviation.html).
