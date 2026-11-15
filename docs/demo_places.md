# Offline demo places

Shipped in `data/demo_cache/` (tracked; written by `scripts/prewarm_demo.py` from `data/demo_places/places.json`).

## Selection criterion (recorded before any radar window was read)

- **Different surface types**, so that "any place on Earth" is shown with data from contrasting surfaces, not claimed.
- Places were chosen by the project owner on 2026-11-15 from a list of suggestions (agriculture, forest, delta/wetland,
  mountain/glacier) after a **public catalog check only** (no token, no radar values): each had at least one compatible
  HH+HV group with 7–9 acquisitions between 1 Jun and 30 Sep 2026. Marmara Lake was the owner's own addition, conditional
  on data being available (it was: 4 HH+HV groups).
- Places were **not** chosen for expected or striking results. Thresholds are not tuned per place.

| Key | Place | Point (lat, lon) | Surface type | Why (one line, neutral) |
|---|---|---|---|---|
| `marmara_lake` | Marmara Lake, Manisa, Türkiye | 38.62, 28.03 | shallow lake basin / wetland | Chosen by the team as a lake/wetland surface type. |
| `central_valley` | Central Valley, California, USA | 36.60, −120.10 | irrigated agriculture | Agriculture surface type. |
| `mekong_delta` | Mekong Delta, Vietnam | 10.00, 105.80 | river delta / rice paddies | Delta surface type. |

The one-line reasons were written by Claude from the surface-type criterion; the owner did not give separate reasons. Please
check them.

## Fixed date rule

Date range 1 Jun – 30 Sep 2026. Group: the largest compatible HH+HV group returned by `src.live_engine.group_products`
(ties: catalog order). Dates: its first 6 acquisitions. Window: 5 km square centred on the point (existing caps and
safety limits of the live engine).

| Key | Track / frame / direction | Dates |
|---|---|---|
| `marmara_lake` | 129 / 021 / ascending | 2026-06-23, 07-05, 07-17, 08-10, 08-22, 09-03 |
| `central_valley` | 034 / 020 / ascending | 2026-06-04, 06-16, 06-28, 07-10, 07-22, 08-15 |
| `mekong_delta` | 047 / 083 / descending | 2026-06-17, 06-29, 07-11, 07-23, 08-16, 08-28 |

Product IDs, cache keys and the dated catalog snapshot of each place are in `data/demo_cache/places/<key>.json` and
`data/demo_cache/catalog/<key>.json`.

## Results (as computed, default first-to-last pair, 500 m square)

All three read **"No clear pattern (inconclusive)"**: Marmara Lake ΔHH +0.41 dB / ΔHV +0.49 dB; Central Valley −1.21 / −1.12 dB;
Mekong Delta +0.12 / +0.08 dB. Other pairs are one click away in the app.

## Thailand flood-validation scene (added 2026-11-15, owner's request)
`thailand_prachinburi` (14.0541 N, 101.3724 E, 10 km window; track 004 D; 2026-09-06, 09-18, 09-30) is not chosen by the
surface-type rule above: it is the flood-validation scene (docs/FLOOD_VALIDATION_PROTOCOL.md), shipped so the flood map
and the negative control work offline. Its three windows were copied unchanged from the validated live cache
(`scripts/add_thailand_demo.py`); it is the first preset and the "Start here" guided example.

