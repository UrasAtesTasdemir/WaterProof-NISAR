"""'Flood map (validated rule)' on the Explore page and the numbers of the flood validation.

The map applies the PRIMARY rule of the flood validation (docs/FLOOD_VALIDATION_PROTOCOL.md, Deviation 3) to the whole
loaded window: existing preprocessing (3x3 mask-aware linear-power mean, dB) and `water_change.classify` with its
defaults (HH -16 dB, |dHH| >= 3 dB). The Compass logic is not touched. Validation numbers are read from the saved
outputs (data/flood_validation/), never typed in.
"""
import json
from pathlib import Path

import numpy as np
from rasterio.transform import Affine, array_bounds

from src import flood_validation as fv
from src.water_change import classify, pixel_area_km2

ROOT = Path(__file__).resolve().parents[1]
FV = ROOT / 'data/flood_validation'


def compute(cube, first, second):
    """Classes 0 invalid, 1 water both dates, 2 new open water, 3 water only first date, 4 no change to water."""
    pair = dict(hh_power=np.asarray(cube['hh_power'])[[first, second]], hv_power=np.asarray(cube['hv_power'])[[first, second]])
    prep = fv.preprocess(pair)
    t_hh = dict(fv.PRIMARY_CONFIG)['t_HH']; gate = dict(fv.PRIMARY_CONFIG)['min_change_db']
    classes, _ = classify(prep['HH'][0], prep['HH'][1], prep['valid'], t_hh, gate)
    valid = int(prep['valid'].sum())
    from rasterio.crs import CRS
    cell = pixel_area_km2(CRS.from_user_input(cube['crs']), Affine(*cube['transform']))
    new = int((classes == 2).sum())
    return dict(classes=classes, valid_pixels=valid, new_pixels=new, share_new=new / valid if valid else None,
                new_area_km2=new * cell)


def validation_numbers(root=ROOT):
    """Primary new-water F1 with 95 % intervals: Thailand test (stage b) and Gandak (stage c), from the saved outputs."""
    base = Path(root) / 'data/flood_validation'
    boot = json.loads((base / 'bootstrap_ab/results.json').read_text())
    b = boot['results']['b']['primary_rows']['new open water (during minus pre) | S1 primary']
    rows = json.loads((base / 'step2c/metrics.json').read_text())['rows']
    c = next(r for r in rows if r['threshold_set'].startswith('PRIMARY') and r['variant'] == 'HH' and r['outcome'].startswith('new'))
    return dict(thailand=(b['point']['F1'], *b['ci95']['F1']), gandak=(c['F1'], *c['ci95']['F1']))


# Okabe-Ito colours: distinct for common colour-vision deficiencies and readable on light and dark backgrounds.
AGREEMENT_COLORS = {1: '#0072B2', 2: '#E69F00', 3: '#CC79A7'}     # TP blue, FP orange, FN reddish purple


def agreement_colors():
    """0 excluded/invalid, 1 TP, 2 FP, 3 FN, 4 TN (neutral grey, darker in the dark theme)."""
    from src.theme import current_theme, palette
    dark = current_theme() == 'dark'
    return [palette()['nodata'], AGREEMENT_COLORS[1], AGREEMENT_COLORS[2], AGREEMENT_COLORS[3], '#5b6168' if dark else '#c9ccd1']


def legend_html(items):
    """Legend as HTML under a figure (readable on phones): items = [(colour, label), ...]."""
    import html
    from src.theme import tokens
    border = tokens()['muted']
    chips = ''.join(f'<span style="display:inline-flex;align-items:center;margin:0 1.1em .35em 0;white-space:nowrap">'
                    f'<span style="display:inline-block;width:1em;height:1em;margin-right:.4em;border:1px solid {border};'
                    f'background:{c}"></span>{html.escape(label)}</span>' for c, label in items)
    return f'<div style="display:flex;flex-wrap:wrap;font-size:.95rem;line-height:1.5">{chips}</div>'


def class_legend():
    from src.i18n import t
    from src.theme import palette
    colors = palette()['classes']
    return legend_html([(colors[i], t(f'fl.class.{i}')) for i in (2, 1, 3, 4, 0)])


def agreement_legend():
    from src.i18n import t
    colors = agreement_colors()
    return legend_html([(colors[i], t(f'fl.agree.{i}')) for i in (1, 2, 3, 4, 0)])


def figure(result, transform, crs):
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Patch
    from src.i18n import t
    from src.theme import palette
    from src.ui import new_figure
    colors = palette()['classes']
    west, south, east, north = array_bounds(*result['classes'].shape, Affine(*transform))
    fig, ax = new_figure(figsize=(7, 5))
    ax.imshow(result['classes'], extent=(west, east, south, north), cmap=ListedColormap(colors),
              norm=BoundaryNorm(np.arange(-.5, 5.5), 5), interpolation='nearest')
    ax.ticklabel_format(useOffset=False, style='plain'); ax.tick_params(labelsize=6)
    return fig                                   # legend: class_legend() as HTML under the image
