# WaterProof navigation globe assets

- Three.js **0.170.0**, `three.module.js` and `examples/jsm/controls/OrbitControls.js`:
  https://cdn.jsdelivr.net/npm/three@0.170.0/ — official published Three.js package.
  MIT license included in THREE-LICENSE.txt.
- Historical Earth texture, 2048-pixel example asset:
  https://threejs.org/examples/textures/planets/earth_atmos_2048.jpg
  Downloaded 2026-11-15. Stored locally as earth.jpg (512,606 bytes).
- index.html: WaterProof's small Streamlit bridge and globe presentation.

This is a static visualization texture. It is not date-matched reference data,
a radar observation, a flood map or an analysis output. All NISAR measurements
continue to use the existing processing pipeline. A direct NASA Blue Marble
texture request timed out; the displayed asset came from the official Three.js
example URL above, not from a successful NASA download.

Geometry uses Three.js equirectangular SphereGeometry conventions: longitude zero
is +X, north is +Y, longitude −90 is +Z. Clicks use a ray/sphere intersection and
inverse atan2/asin conversion. Preset hits are restricted to the visible hemisphere.
No automatic rotation; no live data download; all rendering assets are local.
