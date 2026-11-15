"""Evidence labels only. Never changes radar arrays, thresholds or saved measurements.

Case membership requires the evaluated products AND grid, not a nearby point or
a preset name. Even a matched case does not validate the 500 m Compass reading.
"""
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from rasterio.crs import CRS

ROOT = Path(__file__).resolve().parents[1]
LOUISIANA, CASE, LIVE = 'louisiana', 'case', 'live'


@lru_cache(maxsize=1)
def case_records():
    base = ROOT / 'data/flood_validation'
    return {s: json.loads((base / f'step2{s}/metrics.json').read_text()) for s in 'abc'}


def matched_case(cube, pair):
    """Exact saved evaluation grid/product pair; fail closed if metadata is unavailable."""
    try:
        ids = [cube['product_ids'][i] for i in pair]
        dates = [cube['dates'][i] for i in pair]
        for stage, record in case_records().items():
            n = record['nisar']
            if (ids == n['product_ids'] and dates == [x[:10] for x in n['times']]
                    and list(cube['hh_power'].shape[1:]) == n['grid_shape']
                    and CRS.from_user_input(cube['crs']) == CRS.from_user_input(n['crs'])
                    and np.allclose(list(cube['transform'])[:6], n['transform'], rtol=0, atol=1e-6)):
                return stage
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        pass
    return None


CONTROL_DATES = ['2026-09-06', '2026-09-18']   # saved pre-event negative control (data/flood_validation/step2d)


def is_control(cube, pair):
    """The saved Thailand pre-event control pair on the saved grid (compared with DSWx-S1 8 -> 19 Sep)."""
    try:
        return [cube['dates'][i] for i in pair] == CONTROL_DATES and thailand_context(cube)
    except (KeyError, IndexError, TypeError):
        return False


def scope_for(cube, pair):
    if cube.get('case') == 'louisiana':
        return LOUISIANA
    return CASE if (matched_case(cube, pair) or is_control(cube, pair)) else LIVE


def scope_text(scope, lang=None):
    from src.i18n import t
    return t('scope.' + scope, lang=lang)


def thailand_context(cube):
    """Only the saved Thailand grid and products warrant the Thailand control caution."""
    try:
        for record in (case_records()['a'], case_records()['b']):
            n = record['nisar']
            if (set(n['product_ids']).issubset(cube['product_ids'])
                    and list(cube['hh_power'].shape[1:]) == n['grid_shape']
                    and CRS.from_user_input(cube['crs']) == CRS.from_user_input(n['crs'])
                    and np.allclose(list(cube['transform'])[:6], n['transform'], rtol=0, atol=1e-6)):
                return True
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return False
