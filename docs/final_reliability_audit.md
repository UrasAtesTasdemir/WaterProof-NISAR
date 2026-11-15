# Final reliability audit — 2026-11-15

Checkpoint before edits: `2466af6`. Existing navigation order and Explore feature retained.
Baseline: 175 unittest tests run, 174 passed, 1 optional real-network test skipped;
no failures. No new NASA download was used for this audit.

## Reproduced before editing

- Default `np.allclose` accepted a 30 m northing displacement at UTM coordinates.
- Outside-window point produced a 2,500-pixel centre neighborhood instead of stopping.
- Controlled stationary-power arrays with changing masks produced window medians
  16.7877686 and 0 dB despite no physical temporal change.
- A 500 m place on 10×20 m cells was 1,000 m tall.
- Catalog state checked location only; date changes did not invalidate it. Loaded
  cubes checked location but not window/products. Confirmed by state-path inspection,
  then covered by actual Streamlit AppTest control changes.
- Louisiana already identified itself as cached, but exposed controls which did not
  affect that fixed demo. This was misleading control scope, not fabricated data.

## Fixes and defined limits

`grid_validation.py` checks semantic CRS equality, dimensions, north-up orientation,
spacing, affine coefficients and representative pixel centres. All coordinate
comparisons use rtol=0, atol=1e-6 m; no resampling is performed. Geographic,
non-metre and rotated live grids are rejected explicitly. The existing determinant
area calculation already handled rectangular pixels correctly; no area-algorithm
change was necessary. Ring distance now uses physical x/y spacing in Explore.
Legacy Louisiana investigation/robustness algorithms and their saved outputs remain intact.

Catalog identity includes point/dates/filters. Analysis identity includes products,
point/window, bands, filter, interpretation settings and processing/mask versions.
Results carry their identity, and late responses are only accepted for the active
request. Raw subset cache reuse is preserved. Fixed demo controls are disabled;
Custom uses live mode. No async worker was introduced.

Primary Explore comparisons and temporal medians use all-date common positive-finite
HH/HV coverage. Per-date coverage/statistics are separately labeled. A centre pixel
must be common valid, with at least 50 common neighborhood pixels. This declared
minimum is not a scientific validation rule. Unsupported coverage yields a warning
and no interpretation/export. Requested and sampled centre coordinates are both
reported. Points are never moved to another location. Physical neighborhoods handle
10×10 and 10×20 m cells; the original 3×3 linear-power filter remains in pixel units.

The existing globe is retained and labeled approximate. A Folium map plus a small
local Streamlit click bridge refines coordinates and updates the same analysis
request. Requested bounds and loaded common-valid footprint are distinct layers.
No new dependency is required. Globe, basemap and remote requests need internet;
the fixed cached scientific demo needs no Earthdata authentication.

## Verification

Fourteen new focused tests passed, including displacement, pixel centres, orientation,
CRS, rectangular units, variable/empty coverage, outside/NoData points, real cached
six-date provenance, request identities, late responses, map geometry and actual
AppTest date/window/product control changes. Live reader alignment also tested with
mocked byte-range data. Synthetic arrays are confined to test fixtures.

Full suite: 189 tests run; 188 passed, 1 optional real-network test skipped; no failures.
Final rerun after all code changes: 189 run, 188 passed, 1 optional network test skipped, 0 failures.

The app was launched on loopback port 8510; HTTP root and health endpoints returned
200. This is server verification, not browser interaction verification. Browser
control tools are unavailable for this turn. No actual globe click, precise Folium
click, browser catalog interaction, theme/language click, export download or narrow
viewport was tested in this audit. AppTest verifies server-side controls and existing
pages; it cannot establish frontend component behavior or real-user usability.
Before submission manually exercise the precise-map click bridge, date/window/product
invalidation and export coordinates at desktop/narrow sizes. Real NASA network test
was deliberately skipped; the previous live verification report is preserved.

No tracked `.secrets`, `.env`, `.netrc` or `.streamlit/secrets.toml` paths were found.
Existing token-exclusion tests remain in regression suite. Tokens were not read or
printed for this audit. This is not a new forensic scan of all Git history.

Scientific limitations persist: provisional products, sparse time samples, unknown
HV noise floor, unexplained scene variation and no independent matched validation.
Software regression success does not establish NISAR accuracy or confirmed flooding.

Preservation: 403 scientific/navigation files match their pre-edit SHA-256 values.
The only other captured file, macOS `data/.DS_Store`, changed independently during
the session; it is excluded from the scientific preservation manifest. It was not edited
or restored by this audit. The original navigation registry remains identical.
