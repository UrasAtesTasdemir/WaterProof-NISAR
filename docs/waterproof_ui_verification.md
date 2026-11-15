# WaterProof branding and globe verification — 2026-11-15

## Scope

- WaterProof is now the product name in the shared shell, sidebar, browser title,
  About and benchmark text, generated report headings/disclaimers and README.
- #67C8F5 brand text is larger and semibold on #12334A for contrast in both themes.
  Browser DOM inspection confirmed rgb(103, 200, 245); mobile branding and controls
  did not overlap at 390×844.
- The standalone Limits/Sınırlar blocks in About and flood-validation pages were
  removed. The evidence page label is now Evidence review/Kanıt incelemesi.
  Individual candidate uncertainties, processing safeguards, report warnings and
  scientific calculations remain intact.
- The globe is a local Three.js textured sphere with manual OrbitControls,
  preset markers, ray-cast surface selection and scoped plain-text hover labels.
  It adds no Python dependencies. Renderer/library and static texture sources
  are documented under assets/earth_globe/README.md.

## Actual browser verification

Local app: http://localhost:8520 (loopback-only server).

Checked desktop and 390×844 mobile layouts; EN/TR switching; light/dark switching;
keyboard focus; About section removal; WaterProof in the Researcher workflow;
3D texture rendering; zoom-in/out buttons; keyboard rotation; mouse-drag rotation;
surface click updating coordinate fields and selecting Custom place. The captured
surface selection changed the point to 15.76047, 109.80380. No NASA live read was
started. A fresh-server navigation round-trip preserved 14.05410, 101.37240.

Dedicated mouse-hover sweeps over all preset markers were not automated. The
previous generic `{name}` tooltip was removed, and the new tooltip uses textContent
with a name or actual coordinates; its plain-text fallback is covered by tests.
A desktop screenshot is saved as docs/waterproof_preview.jpg.

The pre-existing module watcher retained some old modules. Final browser checks
used a freshly started server with fileWatcherType=none; restart an existing app
process to load all current Python modules.

## Tests and scientific preservation

Baseline: 253 tests run, 252 passed, 1 optional live-network test skipped.
Four new tests cover branding/contrast, both-language/theme About rendering,
real report provenance and globe assets/label behavior. The historical-export
comparison now permits only the product heading to differ; the entire report body
still compares exactly with its original saved file. Ten investigation tests passed.

Final full suite: 257 tests run in 308.822 seconds; 256 passed, 1 optional live-network test skipped, 0 failures.

SHA-256 verification: all 569 pre-existing data files (excluding macOS .DS_Store)
remain identical. No observations, benchmark results, scientific outputs or
historical reports were overwritten. This visual redesign establishes no new
scientific accuracy, confidence score or validation finding.
