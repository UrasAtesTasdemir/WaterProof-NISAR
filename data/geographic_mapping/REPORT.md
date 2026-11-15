# Milestone 9 — real Louisiana geographic mapping

## Data and footprint

The existing June 21 and July 3, 2026 frequency-A HHHH products were accessed
through the existing authenticated, TLS-verified range-read pipeline. Exact IDs
and acquisition timestamps are retained in each `results.json` and GeoTIFF tags.
The cached ASF catalog features match these IDs. Both projected catalog
footprints fully contain both requested squares, centered on the original AOI.
Pixel-center inclusion determines the actual processed boundary. No full HDF5
products were downloaded, and no synthetic observations were used.

| Window | Common valid area km² | Expansion candidate km² | Recession candidate km² | Native array | Processing seconds | Range-read MiB, before / after |
|---|---:|---:|---:|---|---:|---|
| 5 × 5 km | 25.0000 | 0.1056 | 0.0024 | 525 × 525 | 71.28 | 10.00 / 11.00 |
| 10 × 10 km | 100.0000 | 0.5062 | 0.0352 | 1049 × 1048 | 109.06 | 15.00 / 14.00 |

Array padding outside the polygon is invalid, not additional analyzed area.
The 10 km request lies approximately within 29.8674–29.9597° N and
90.3334–90.2274° W (a rotated projected square, not its geographic bounding box).
The valid footprint GeoJSON is authoritative for displayed analysis coverage.
The 10 km run followed a successful 5 km run with full coverage and small range
transfers. Saved files occupy approximately 4.13 and 16.40 MiB respectively.
No peak-memory measurement was made.

## Processing and outputs

Existing preprocessing/classification functions are reused: common finite
positive linear-power mask; 3×3 mask-aware linear mean; 10 log10 conversion;
water ≤ −16 dB; transition magnitude ≥3 dB; no singleton suppression or scene
offset correction. Both dates share EPSG:32615, 10 m pixels, affine transform,
shape and a common mask. Areas use native projected pixels, never degree areas
or display-pixel counts. Enlarged-window areas differ from the original AOI
because the processed geography is larger; its original 0.0569 / 0.0005 km²
results remain unchanged.

Each `5km/` and `10km/` directory contains two-band `radar_power.tif`, three-band
`filtered_backscatter.tif`, `classes.tif`, `common_valid.tif`, `results.json` and
`valid_footprint.geojson`. Standalone `map_5km.html` and `map_10km.html`, run logs,
test log and browser preview images are saved alongside this report.

New code: `scripts/process_geographic_area.py`, `src/geographic_map.py`,
`src/geographic_panel.py`, `tests/test_geographic_map.py`. `app.py` adds a separate
workspace; requirements add Folium 0.20.0 and its dependency lock entries.
The scientific algorithm and benchmark outputs are unchanged.

## Map and verification

The image overlays are categorical nearest-neighbor reprojections to EPSG:3857,
north-up, maximum 768 pixels per side (actual 768 × 765 and 768 × 764).
Their Leaflet bounds are transformed to latitude/longitude. Only candidate
classes are colored; other/invalid pixels are transparent. The projected native
valid-cell boundary is transformed separately to EPSG:4326. OSM and Leaflet
resources require an internet connection; scientific arrays and overlays are
local. HTML maps are only approximately 24 and 28 kB.

46 automated tests passed, including five new geographic tests: north/south and
east/west orientation, bounds, categorical/alpha preservation, true native
area/boundary consistency, reproduction of the saved classes from real cached
power, map contents, and Streamlit workspace regression. The existing 41 tests
include scientific processing and separate benchmark checks.

Actual browser checks on a fresh local server (127.0.0.1:8502) confirmed:

- Original workspace rendered its unchanged 0.0569 / 0.0005 km² defaults.
- Geographic workspace rendered OSM tiles, all three real overlay images and
  the valid footprint around Ama/Waggaman, the Mississippi and Lake Cataouatche.
- Each candidate layer was hidden and restored; overlay image count changed
  from three to two and back. Zoom changed the scale from 3 km to 1 km.
- Dragging panned the map pane by 70 px east and 30 px south.
- Coverage selection changed metrics to 25.0000 / 0.1056 / 0.0024 km², then
  returned to 100.0000 / 0.5062 / 0.0352 km².

An older process on port 8501 retained a stale three-argument processing module
and raised a TypeError. A freshly launched process loaded the current module and
worked; no scientific code change was needed. Restart old Streamlit processes
when reusing a server across milestones. No additional browser engine or wide
viewport was tested. Saved previews show the actual narrow browser viewport.

Before edits, SHA-256 hashes were recorded for 236 existing files in
`original_hashes.json`. Verification found no missing prior files and changes
only to the intended app and requirements files; README documentation was added
after that verification. All previous data, cached products and benchmark
results are preserved.

## Scientific limits

These are unvalidated candidates, not confirmed flooding. Water thresholds,
scene-wide darkening, speckle, mixed/narrow pixels and possible registration
error remain relevant. Wider coverage supplies no independent accuracy evidence.
OSM is geographic context, not date-matched flood validation. Display reduction
can hide isolated features; it never changes measured areas. A recommended next
step is spatial review of expanded-area candidates with independent dated
references before making any flood-extent claim.
