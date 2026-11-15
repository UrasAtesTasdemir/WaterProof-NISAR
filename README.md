# WaterProof

*NASA Space Apps Challenge 2026 — "Dancing with the SARs". MIT License.*

Radar change maps look convincing but are hard to trust. A pixel that got darker between two NISAR passes may be new
open water, but also a calmer or drier surface, harvested or flattened vegetation, a different viewing geometry or a
processing effect. **WaterProof** is a research tool that shows real NISAR L-band radar changes together with what they
are consistent with, what else could explain them, how fragile they are, and — where it exists — how they compare with
independent water products. It ends every investigation with an exportable note saying what to check next.

WaterProof does **not** confirm flooding, water or land-cover change, give an accuracy or confidence score, or identify
causes.

## Evidence scopes (how to read every result)

| Scope | Where | What the evidence supports |
|---|---|---|
| **A · Louisiana research exploration** | Louisiana (and the Kerrville availability case) | Real NISAR observations; exploratory radar-change candidates. No independent reference with matching timing and coverage exists, so the change findings are **not validated**. Robustness checks use the same observations and are not accuracy. |
| **B · Case-specific evaluation** | Thailand (Prachin Buri) and India (Gandak) | The candidate open-water threshold map was compared with independent OPERA DSWx water products for **specific dates, grids and settings**. Only those measured agreements are reported; they are **not** global accuracy and they do not validate the local Change Compass interpretation. |
| **C · Live / user-selected exploration** | Any other place, date pair or grid | Real NISAR observations when retrieved; **exploratory** unless that exact product pair and grid has a saved evaluation. Thailand/Gandak scores never transfer. |

The scope is decided in one place (`src/evidence_scope.py`) from the actual products, dates and grid — not from a preset
name or a nearby point — and the same label appears on screen and in exported notes.

## What the app contains

| Page | Contents |
|---|---|
| **Explore the world** (opens first) | Short "Start here" strip (select an example → observe the change → check uncertainty → investigate next), a textured 3D globe, presets, coordinates or place-name search, catalog search and small-window reads; before/after/change maps, HH/HV time series, the Compass reading with alternative explanations, a **candidate open-water change map (evaluated threshold method)** with its evidence scope, and a downloadable review note. |
| **Researcher workflow** | One Louisiana candidate at a time: map highlight, acquisition dates, HH/HV behaviour, why it was listed (ranking is not a risk score), settings robustness separately from date dependence, placebo check, main limitation, one concrete next investigation, review note. |
| **Louisiana case study** | Original change dashboard and analysis views (map, time series, HH/HV, investigation explorer, Change Compass, evidence checklist, diagnostics). |
| **Is this scene analyzable?** | Compatible pairs, shared coverage, timing and optical-reference usability for the cached cases. |
| **Reference comparisons (Thailand, Gandak)** | "Where the Method Works — and Where It Struggles", primary results with 95 % intervals, maps, the pre-event control, metric provenance (products, acquisition times, offsets, masks, evaluated pixels), deviations and limits. |
| **Appendix: Sentinel-1 benchmark** | Frozen Sen1Floods11 adaptation scores. **Different sensor; does not describe NISAR.** |
| **About** | Framing, evidence scopes, provenance, glossary, AI use, licence, data attribution. |

Languages: English and Turkish. Themes: light and dark.

## Scope A — cached Louisiana demonstration

Six NISAR L2 GCOV acquisitions (21 Jun – 1 Sep 2026, track 105 / frame 17, HH and HV) with one 24-day gap
(27 Jul → 20 Aug). Five investigation candidates were screened (heuristic ranking by area and magnitude, not risk).

| Candidate | Seed change | Pattern (both references) | Top 5 under 27 settings variants | Seed event still notable after single-date removal | Candidate − ring ΔHH |
|---|---|---|---:|---|---:|
| 1 | 3 Jul → 15 Jul, increase | More volume scattering or roughness (HV dark-level caution) | 27/27 | 5/6 (not without 15 Jul) | +5.55 dB |
| 2 | 15 Jul → 27 Jul, decrease | No clear pattern (30 pixels, below the 50-pixel minimum) | 5/27 | 4/6 | −3.65 dB |
| 3 | 21 Jun → 3 Jul, decrease | Smoother-surface pattern | 3/27 | 4/6 | −1.92 dB |
| 4 | 3 Jul → 15 Jul, increase | Reading depends on the reference | 5/27 | 4/6 | +1.32 dB |
| 5 | 3 Jul → 15 Jul, increase | HH-dominated brightening | 4/27 | 4/6 | +1.77 dB |

The scene-wide change for 21 Jun → 3 Jul (ΔHH −1.39 dB) is unexplained and not corrected. Placebo check (method fixed in
`docs/PLACEBO_METHOD.md`): candidates 1–5 are unusual in HH against random same-shape regions (exceedance fraction
0.002–0.006), candidates 4 and 5 are **not** unusual in HV (0.33, 0.54); candidates were selected for large change, so this
comparison is incomplete and says nothing about causes.

## Scope B — case-specific reference comparisons (Thailand, Gandak)

Protocol `docs/FLOOD_VALIDATION_PROTOCOL.md`, committed before any NISAR flood window was read (commit `181782456a` in the
private development history; this public repository starts from a single release commit);
later changes are dated deviations. Primary method: water candidate if HH ≤ −16 dB; new open-water candidate needs a
crossing from above the threshold and |ΔHH| ≥ 3 dB, after a 3×3 mask-aware linear-power filter (`water_change.classify`,
untuned defaults). Primary outcome: new open water against OPERA **DSWx-S1** (open water = WTR 1; partial/inundated
vegetation, clouds, masks and NoData excluded); DSWx-HLS is a sensitivity reference. 30 m references are resampled to the
10 m NISAR grid by nearest neighbour. Metrics pool the evaluated pixels of one scene; 95 % intervals are spatial block
bootstrap (1 km blocks, 1000 resamples).

| Scene | NISAR dates | DSWx-S1 dates (offset) | Evaluated | New open water F1 [95 %] |
|---|---|---|---|---|
| Thailand 004 D (calibration scene for secondary thresholds; primary rule untuned) | 6 → 30 Sep 2026 | 8 Sep → 1 Oct (+59.2 h / +35.4 h) | 97.7 km² | 0.69 [0.63, 0.74] |
| Thailand 011 A (test) | 6 → 30 Sep 2026 | 8 Sep → 1 Oct (+48.2 h / +24.4 h) | 97.7 km² | 0.78 [0.74, 0.81] |
| Gandak 026 A (test) | 19 Sep → 1 Oct 2026 | 17 Sep → 29 Sep (−71.5 h / −71.5 h) | 96.4 km² | **0.24 [0.17, 0.31]** |

- **Where it works and where it struggles.** Agreement is moderate in Thailand and low at Gandak. The two Thailand tracks
  view the **same 10 km area with the same references**: one location, not two independent successes. Gandak reasons
  (flooding under vegetation, weak darkening, references three days earlier) are hypotheses, not tested.
- **References are products, not field truth.** In Thailand DSWx-HLS and DSWx-S1 disagree (open water 57 % vs 31 %,
  IoU 0.55). The HLS class table comes from its v1.0 specification while the files are v1.1.
- **Pre-event control (Thailand, 6 → 18 Sep 2026, both before the flood).** The same rule still produced **3.14 km²
  (004 D) / 5.19 km² (011 A)** of new-water candidates, of which 2.82 / 4.88 km² are not new water in DSWx-S1
  (8 → 19 Sep). The 18 Sep forecast-orbit products passed the co-registration check (0.14 / 0.06 px). This limits
  interpretation: a darker pixel alone is not evidence of flooding; part of the disagreement may also be real pre-event
  water change or reference timing.
- The calibrated thresholds (HH −10 dB, on the edge of the search grid) are secondary and worse for new water; HV adds
  nothing under the "both below threshold" rule; an exploratory flooded-vegetation rule failed (F1 0.02 / 0.01 / 0.17).
  Bagaha (secondary Gandak window) was not run.

Outputs: `data/flood_validation/` (each folder has a SHA-256 sidecar). The Thailand 004 D scene ships in
`data/demo_cache/` and is the guided example: offline it reproduces 25.67 km² (6 → 30 Sep) and 3.14 km² (6 → 18 Sep).

## Scope C — live exploration

- **No credentials needed:** the cached Louisiana case, the shipped demo places (Thailand, Marmara Lake, Central Valley,
  Mekong Delta) and all saved comparisons; the public ASF catalog search (internet required).
- **Earthdata authentication needed:** reading new radar windows. Supply a token server-side (`EARTHDATA_TOKEN`
  environment variable, an owner-only `.secrets/earthdata_token` file, or Streamlit secrets) or paste your own token into
  the password field (kept in that browser session only). No token is shipped; tokens are never logged, cached, displayed
  or written to files.
- **What a read does:** up to 6 dates of one compatible acquisition group, HH and HV only, inside a 1–10 km square, through
  a TLS-verified byte-range reader restricted to approved NASA hosts. Windows are cached in `data/live_cache/` (git-ignored).
- New places get the exploratory scope unless their exact products and grid were evaluated.

## Exporting an investigation note

On Explore (any loaded result) or in the Researcher workflow, press **Download review note (Markdown)**. The note contains
the location, acquisition dates and product IDs, the evidence scope, the observed HH/HV change, the Compass reading and
alternatives, the most important uncertainty, open questions and the proposed next investigation — the same statements
shown on screen.

## Setup and tests

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
.venv/bin/python -m unittest discover -s tests
```

Regenerating saved outputs (each script refuses to overwrite without `--overwrite`): `scripts/process_robustness.py`,
`scripts/process_placebo.py`, `scripts/flood_reference_scan.py`, `scripts/flood_step2.py --stage a|b|c|d`,
`scripts/flood_bootstrap_context.py`, `scripts/flood_primary_maps.py`, `scripts/prewarm_demo.py`,
`scripts/add_thailand_demo.py`. Scripts that read NISAR or OPERA products need an Earthdata token
(see [EARTHDATA_ACCESS.md](EARTHDATA_ACCESS.md)).

## Public demo requirements (not deployed)

Entry point `app.py`, dependencies in `requirements.txt`, Python 3.12. The public demo works fully without secrets in
cached mode; do not add an Earthdata token to a public deployment unless you accept that visitors' reads use it. All files
are under GitHub's 100 MB limit (largest ≈16 MB). Basemap tiles, the place search and the catalog search need internet;
the globe texture, cached radar and saved results are local. Memory on hosted platforms has not been measured.

## Data provenance and attribution

- NISAR L2 GCOV radar products (provisional, CRID P05023): NASA Earthdata, ASF DAAC.
- OPERA DSWx-S1 / DSWx-HLS reference water products: NASA PO.DAAC; derived from ESA Copernicus Sentinel-1/-2 and
  USGS/NASA Landsat observations.
- Sentinel-1 benchmark appendix: Sen1Floods11 (Copernicus Sentinel-1); not a NASA source.
- Basemaps and place search: © OpenStreetMap contributors (Nominatim). Globe texture: Three.js example asset
  ([sources](assets/earth_globe/README.md)). Copernicus DEM GLO-30 was used for the Thailand error-context analysis.
- Product IDs, acquisition times and SHA-256 fingerprints are stored beside every output. Local file paths in saved test
  logs were masked before release; `data/masked_logs.json` lists the original and masked hashes.
- NASA does not endorse WaterProof.

## Limitations

- Three scenes in two regions; agreement varies by place and is not global accuracy. Thailand's two tracks are not
  independent. Pixel counts overstate independent samples.
- Louisiana findings have no independent validation; the scene-wide shift is uncorrected; the HV noise floor is not
  quantified; six dates with a 24-day gap can miss short events.
- Thresholds (−16 dB, 3 dB, Compass dead zone 1.5 dB) are exploratory; robustness and placebo checks reuse the same data.
- The 500 m Compass square can describe a different surface (e.g. a town) than the surrounding flood.
- NISAR products are provisional; DSWx references can disagree with each other.

## Known issues

- The date picker and number fields follow the browser's locale, even when the app language is English.
- On phones the map images are small; legends are HTML and stay readable.
- No real-user usability sessions have been run yet (protocol: [docs/usability_test.md](docs/usability_test.md)).

## AI use

As the competition requires, we disclose that we used AI tools in this project:

- **Claude Code (Anthropic)**
- **ChatGPT / Codex (OpenAI)**

They were used to write and refactor Python code and tests, inspect cached data and saved
reports, run checks, and draft documentation. All scientific numbers come from real NASA
data processed by the code in this repository; none were invented by an AI tool. The team
set the scope and requirements of each phase and is responsible for the claims made.

## License

[MIT](LICENSE).
