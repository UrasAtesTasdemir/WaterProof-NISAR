# FloodPulse NISAR — six-date HH exploration

## Scope and protected baseline

This increment adds phases 0–2 only. HV feasibility and new radiometric/noise
diagnostics (phases 3–4) require a separate approval. The existing two-date
classifier, geographic map, Sentinel-1 benchmark, data and scientific results
remain available and unchanged. No second study region or flood accuracy claim
is introduced.

A standard Git repository and the tag `pre-timeseries-phase0` protect the
pre-change project (commit `59c8bb4a90a0cfa4090d9ca1395be013c4e27d69`). The checkpoint
contains source, tests and cached public scientific outputs; credentials, the
virtual environment and caches are excluded. System Git is blocked by an
unaccepted Xcode license, so Dulwich was installed in the existing venv only and
used to create the commit/tag. It is a checkpoint tool, not an application
dependency; no system-wide configuration or license was changed. The initial
46 tests passed. SHA-256 fingerprints of previous data are stored separately in
`preserved_hashes.json`. After system Git is available, the tag can be inspected
with `git show pre-timeseries-phase0`; recovery should be done in a separate
checkout rather than overwriting newer scientific files.

## What the signal represents

NISAR is a NASA–ISRO synthetic aperture radar mission. Its L-band radar uses
roughly 24 cm wavelength, useful for observing vegetation and surface dynamics.
Radar supplies measurements through cloud and without daylight. Backscatter
depends on roughness, moisture, vegetation and viewing geometry; it is not a
direct water-depth measurement. See the official [mission overview](https://science.nasa.gov/mission/nisar/mission-overview/)
and [NISAR user guide](https://nisar-docs.asf.alaska.edu/nisar-intro/).

HH is horizontally transmitted and horizontally received radar; HV is horizontal
transmit and vertical receive. Cross-polarized scattering can provide additional
structural information, but neither polarization uniquely identifies inundation.
This increment processes **HHHH only**, the GCOV HH power term; it does not read
HVHV or mix HH/HV. HV feasibility remains pending. See NASA's
[polarimetry explanation](https://science.nasa.gov/mission/nisar/polarimetry/).

## Source compatibility and preprocessing

The original small Louisiana AOI is retained for a lightweight six-date series;
the existing 5/10 km two-date geographic products are preserved separately.
The six previously researched product IDs are matched against a new public ASF
catalog response. Filename configuration, track/frame, ascending direction,
bandwidth, frequency-A HH, provisional collection, CRID and processing version
are checked, together with projected catalog footprint coverage. Pixel validity
is checked from actual arrays, not inferred from footprint coverage.

June21/July3 power is reused from the verified original GeoTIFFs. Only missing
dates require authenticated HTTPS HDF5 ranges through the existing pipeline:
approved redirects, TLS verification, bounded 16 MiB cache and 256 MiB transfer
limit per product. Secrets and signed URLs are never saved or cached. The
[official ASF Cookbook](https://asfopensarlab.github.io/NISAR_Cookbook/search-stream-nisar-asf-search/)
describes lazy access, spatial subsetting and time-series loading.

All observations are placed on the first date's 10 m EPSG:32615 grid. If needed,
the existing nearest-neighbor power/mask alignment function is reused and the
correction is recorded; actual CRS, transforms, shape and north-up orientation
are tested. Finite positive linear power determines per-date validity. An
existing 3×3 normalized mean is applied to **linear power**, with each date's
valid mask; invalid centers remain invalid. Only then is `10*log10(power)` used.
Near boundaries or gaps there are fewer contributing neighbors. Per-date mask
filtering is explicit, and differs from a hypothetical filter restricted to the
six-date intersection. Saved per-date masks preserve that distinction.

## Temporal products and interpretation

`hh_db.tif` retains individual-date valid coverage. `common_hh_db.tif` and the
`HH_common_db` NetCDF variable retain pixels valid on **all six dates**. The cube
also stores raw linear power, per-date filtered dB, individual/common validity,
actual UTC acquisition times, coordinates, CRS/affine metadata, median and
exploratory residuals. Comparison statistics use the fixed six-date common
footprint, avoiding apparent shifts caused by changing spatial support.

Per-date mean, median, standard deviation and 5/25/75/95 percentiles describe
spatial backscatter distributions; they are not independent-pixel uncertainties.
Consecutive differences and differences from the first date are in dB. Selected
UI pairs use the intersection of those two dates' finite data. Date order and
the subtraction direction are explicit; irregular time gaps are not disguised
as a uniform cadence.

The exploratory anomaly score is simply **date dB minus that pixel's temporal
median, in dB**. It is not a z-score, probability, return period or flood score.
The median is robust to one extreme date; no division by zero or estimated
variance occurs. A minimum of four finite observations is a declared exploratory
guardrail; insufficient histories remain NaN and zero variation gives zero
deviation. The saved common cube has six observations wherever valid. Six dates
over one season cannot establish a climatology, event baseline, trend significance
or calibrated anomaly likelihood. Temporal gaps can miss short-lived changes.

Scene-wide darkening is displayed as an observation, not assumed sensor bias.
No scene median is subtracted and no radiometric correction is applied. Wind,
tidal/drainage conditions, soil moisture, vegetation, speckle, mixed pixels,
registration and provisional processing remain plausible influences.

## Geographic exploration and limits

The time-series view reuses Folium and the existing Web Mercator display-grid
helper. Coordinate inputs provide a reliable point-selection alternative to
an iframe click callback. The selected native pixel center is reported and
marked on the map. A 1×1, 3×3 or 5×5 neighborhood reports median **filtered dB**,
finite sample counts and explicit missing values for each date; support can vary
with missing data. Plot points use actual acquisition times; missing dates are
not filled or interpolated. The 3×3 speckle filter precedes any neighborhood
summary, so even a 1×1 plot is not an unfiltered point measurement.

Map resampling and percentile color scales are display-only. Native georeferenced
arrays and projected pixel dimensions determine measurements. OSM is context,
not an independent contemporaneous water reference. Suitable paired independent
validation remains unavailable. Sentinel-1 Sen1Floods11 metrics remain confined
to that adapter; they do not establish NISAR HH accuracy. Backscatter changes
alone are not confirmed surface water or flooding. This system helps researchers
inspect persistence, timing, spatial context and competing explanations before
requesting independent validation.
