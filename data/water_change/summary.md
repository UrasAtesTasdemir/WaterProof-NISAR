# Exploratory NISAR water change candidates

Dates: 2026-06-21T11:19:06+00:00 → 2026-07-03T11:19:05+00:00

Possible expansion: **0.056900 km²**

Possible recession: **0.000500 km²**

Common valid pixels: 138779; projected pixel area: 0.0001 km².

Exploratory water threshold: -16 dB; minimum absolute change: 3.

- Exploratory water candidates, not confirmed water or confirmed flooding.
- -16 dB and the optional 3 dB change gate are test settings, not universal or validated thresholds.
- Backscatter changes alone do not prove flooding. No ground truth or accuracy metrics are available.
- Wind, vegetation, soil moisture, geometry, radar shadow and smooth artificial surfaces can affect interpretation.
- A 3x3 linear-power boxcar reduces speckle but blurs boundaries; edge pixels have fewer valid neighbors.
- Areas are projected-grid pixel-count estimates within the common valid AOI, not geodesic surveyed extents.
- Threshold crossings below the change gate are assigned Other valid surface, not verified stable land.

Sources, identifiers, SHA-256 cache fingerprints, masks and full settings: results.json.

Method references: [SciPy convolve](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.convolve.html), [Rasterio reprojection](https://rasterio.readthedocs.io/en/stable/topics/reproject.html), [NASA SAR Handbook](https://earthdata.nasa.gov/s3fs-public/2025-04/SARHB_CH5_Content.pdf).
