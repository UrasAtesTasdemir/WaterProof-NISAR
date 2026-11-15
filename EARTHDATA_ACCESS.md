# Milestone 2: Earthdata access blocker

The existing Python 3.12 environment and both URLs in `data/nisar_manifest.json`
were checked. Authentication is now available through the protected local token.
Both products passed authenticated HDF5 range-access checks, and both real HHHH
AOI subsets have been read and visualized. Browser login is not automatically
available to Python.

## One local authentication action

Follow the [official ASF NISAR Cookbook](https://asfopensarlab.github.io/NISAR_Cookbook/search-stream-nisar-asf-search/):
sign into [Earthdata Profile](https://urs.earthdata.nasa.gov/profile), then use
**Generate Token** to obtain a Bearer Token. Do not send it in chat.

In PyCharm's **Terminal**, with this project as the working folder, run:

```sh
.venv/bin/python -B scripts/check_earthdata_access.py --prompt --save-token
```

Enter the token only at the hidden prompt. It is never a command argument,
printed output, source-code value, or report field. `--save-token` explicitly
chooses local storage for the next run: `.secrets/earthdata_token`, ignored by
Git, directory permissions 0700 and file permissions 0600. Omit `--save-token`
to keep the token in memory for this check only. A verified stored token can
later be read by the agent without sending it in chat. Do not share `.secrets`.

The helper also supports an existing EARTHDATA_TOKEN, NASA_EARTHDATA_TOKEN or
EARTHDATA_BEARER_TOKEN environment variable. It does not use a username/password
or change your system authentication settings.

The check requests **only bytes 0–7** of each product and requires HTTP 206 and
the HDF5 file signature. It follows at most six HTTPS data requests to approved
NISAR, NISAR-product S3, or the exact NISAR CloudFront distribution
`d1mv8zhcvry6x4.cloudfront.net` observed in the official endpoint's HTTPS redirect,
sending the Bearer token only to the original
NISAR host. Redirects to Earthdata Login are reported separately; HTTP 303 alone
does not prove that a token is invalid. Signed redirect URL parameters are never
logged. It never reads an entire product. It saves a non-sensitive report to
`data/earthdata_access_check.json`. An HTTP failure is reported by status code;
exception text is suppressed to protect secrets. A successful access check is
not verification of the HHHH layer or the radar values.

## Completed Milestone 2

Run `.venv/bin/python -B scripts/visualize_nisar.py` to repeat the real-data
subset workflow with a valid saved or environment token. Only public catalog
URLs go into outputs; signed CloudFront URLs stay in memory. The HTTPS client
verifies TLS using certifi; certificate verification is never disabled.

Outputs: `data/nisar_hhhh_comparison.png`, two two-band GeoTIFFs in `data/subsets/`
(band 1 gamma-0 power, band 2 dB), JSON sidecars and
`data/nisar_visualization_report.json`. Outside-AOI pixels are NaN. Each actual
subset is 257 rows by 579 columns at 10 m in EPSG:32615; both grids match and
each contains 138,779 finite positive AOI pixels. GeoTIFFs were read back and
verified, and the inverse dB conversion was checked against saved power values.

Only indexed windows are loaded from lazy xarray/h5netcdf arrays over fsspec
HTTPS byte ranges. Cache is limited to 16 MiB; transfer has a 256 MiB safety
limit per product. The successful processing run fetched 8,388,616 bytes per
product including its signature check, rather than each approximately 6.6 GB
HDF5 product. Earlier authentication/metadata inspection requests were additional
small requests and are not included in that processing-run count.

The shared display scale uses the pooled 2nd and 98th percentiles; it does not
alter saved radar values. Light blue outside-AOI areas are nodata. This is a
diagnostic visualization, not flood classification. No Streamlit changes were
made. Milestone 2 is complete; further milestones require the user's instruction.
