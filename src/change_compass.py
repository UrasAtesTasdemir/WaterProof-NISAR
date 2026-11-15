"""Change Compass logic: HH-vs-HV change vectors mapped to HYPOTHESIS labels.

Nothing here classifies land cover. The mapping from a change direction to a
label is a documented, literature-based interpretation of typical L-band
scattering tendencies; it is NOT validated for these scenes. Every label is
returned together with its numeric evidence and a caution line.

Preprocessing is the existing pipeline (``src.polarization``, which itself
uses ``src.water_change.mask_aware_mean`` / ``power_to_db``): joint HH/HV
positive-finite masks, 3x3 mask-aware mean in linear power, then dB.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

from src.polarization import prepare_polarizations, compare_polarizations

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'data/hv'
PAIR_DATES = ('2026-06-21', '2026-07-03')
RAW_HV = ROOT / 'data/polarization_analysis/raw'
GROUP = '/science/LSAR/GCOV/grids/frequencyA'
DEFAULT_DEAD_ZONE_DB = 1.5
MIN_PIXELS = 50

# Ordered rule table. Titles describe a PATTERN in the radar change, not a
# cause. Literature basis is general L-band scattering behaviour, not a
# validation for this site (see docs/CHANGE_COMPASS_METHOD.md).
COMMON_ALTERNATIVES = (
    'Soil or canopy moisture change (wetting raises, drying lowers backscatter)',
    'Surface roughness change, including wind on open water',
    'Vegetation growth, harvest, senescence or lodging',
    'Processing or scene-wide shift: provisional calibration, or the unexplained scene-wide median change',
    'Viewing geometry, sub-pixel misregistration and mixed 10 m pixels',
)
LABELS = {
    'smoother_surface': dict(
        title='Pattern consistent with a smoother surface (HH and HV both darker)',
        rule='median ΔHH ≤ −τ and median ΔHV ≤ −τ/2',
        physics='A smoother surface, such as calm open water, reflects energy away from the sensor and can lower '
                'both co-pol (HH) and cross-pol (HV) returns.',
        alternatives=('Drying soil or canopy', 'Calmer wind over existing water', 'Loss of vegetation volume'),
        caution='Not evidence of water or flooding on its own.'),
    'hh_darkening': dict(
        title='HH darker, HV roughly unchanged',
        rule='median ΔHH ≤ −τ and |median ΔHV| < τ/2',
        physics='HH lost energy but HV did not change much. Smoothing of a surface that was already dark in HV, '
                'or a change that affects mainly the co-pol channel, can produce this.',
        alternatives=('HV close to the noise floor, so it cannot fall further', 'Drying soil (stronger effect on HH)',
                      'Calmer water surface where HV was already very low'),
        caution='When HV is very dark the HV change carries little information; see the HV dark-level flag.'),
    'hh_brightening': dict(
        title='Pattern consistent with HH-dominated brightening',
        rule='median ΔHH ≥ +τ and median ΔHV < +τ',
        physics='At L-band, water under emergent vegetation or near structures can add a double-bounce return '
                'that brightens HH much more than HV.',
        alternatives=('Wetter soil', 'Row or structure orientation relative to the radar', 'Rougher surface'),
        caution='Not evidence of flooded vegetation on its own.'),
    'volume_loss': dict(
        title='Pattern consistent with reduced volume scattering (HV darker, HH steady)',
        rule='median ΔHV ≤ −τ and median ΔHH > −τ',
        physics='HV is dominated by volume scattering in vegetation canopies; a clear HV drop with little HH '
                'change is typical of reduced canopy volume (e.g. harvest, defoliation, clearing).',
        alternatives=('Canopy drying', 'Wind-driven canopy motion', 'HV noise in dark areas'),
        caution='No land-cover change is established.'),
    'volume_gain': dict(
        title='Pattern consistent with more volume scattering or roughness (HV brighter)',
        rule='median ΔHV ≥ +τ',
        physics='Rising HV (often with HH) is typical of more volume scattering or rougher / wetter surfaces.',
        alternatives=('Vegetation growth', 'Wetting', 'Roughening by tillage or wind'),
        caution='Several different processes produce this pattern; it does not identify one cause.'),
    'inconclusive': dict(
        title='No clear pattern (inconclusive)',
        rule='too few pixels, inside the ±τ dead zone, pixels disagree, or mixed directions',
        physics='The change vector is too small, too spread, or points in a direction without a single '
                'common physical reading.',
        alternatives=(),
        caution='Inconclusive is a valid answer: the radar pair alone does not support a pattern here.'),
    'reference_dependent': dict(
        title='Reading depends on the reference',
        rule='raw-median and scene-median-relative readings differ',
        physics='The pattern changes when the unexplained scene-wide median change is removed, so it may be '
                'driven by that scene-wide shift rather than by something local to the region.',
        alternatives=('Scene-wide shift from calibration, moisture or wind', 'Local change of a size similar to the shift'),
        caution='Neither reading should be used on its own; both are shown with their numbers.'),
}


def alternatives_for(key):
    """Label-specific alternatives first, then the shared evidence-limits list."""
    specific = list(LABELS[key]['alternatives'])
    return specific + [a for a in COMMON_ALTERNATIVES if a not in specific]


def alternative_keys(key):
    """Translation keys matching ``alternatives_for(key)`` one to one."""
    specific = [f'compass.{key}.alt{i}' for i in range(len(LABELS[key]['alternatives']))]
    common = [f'compass.common.alt{i}' for i, a in enumerate(COMMON_ALTERNATIVES) if a not in LABELS[key]['alternatives']]
    return specific + common


def label_text(key, field='title', lang=None):
    """Translated title / rule / physics / caution of a pattern label."""
    from src.i18n import t
    return t(f'compass.{key}.{field}', lang=lang)


def reason_text(part, lang=None):
    """Translated reason of a raw or relative reading (numbers in the language's format)."""
    from src.i18n import t, num
    values = dict(part.get('values', {}))
    for name in ('h', 'v'):
        if name in values:
            values[name] = num(values[name], 2, sign=True, lang=lang)
    if 'tau' in values:
        values['tau'] = num(values['tau'], 2, lang=lang).rstrip('0').rstrip(',.')
    if 'rule_of' in values:
        values['rule'] = label_text(values.pop('rule_of'), 'rule', lang)
    return t(part['reason_key'], lang=lang, **values) if 'reason_key' in part else part['reason']


def sector_label(name, lang=None):
    """Translate a sector name returned by ``sector_shares``."""
    from src.i18n import t
    if name == 'inside dead zone':
        return t('compass.sector.dead', lang=lang)
    if name == 'mixed directions':
        return t('compass.sector.mixed', lang=lang)
    key = next((k for k, info in LABELS.items() if info['title'] == name), None)
    return label_text(key, 'title', lang) if key else name


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_raw_hv(date, directory=RAW_HV):
    """Verified cached HVHV power window (real bounded read made in an earlier phase)."""
    path = Path(directory) / f'hvhv_{date}.tif'
    meta = json.loads(path.with_suffix('.json').read_text())
    if meta['layer'] != 'HVHV' or meta['hdf5_group'] != GROUP or meta['sha256'] != sha256(path):
        raise ValueError(f'HV cache provenance mismatch for {date}.')
    with rasterio.open(path) as src:
        if src.tags().get('source_layer') != GROUP + '/HVHV' or src.descriptions[0] != 'HVHV_gamma0_power':
            raise ValueError(f'HV raster tag mismatch for {date}.')
        power = src.read(1).astype(float)
        grid = dict(crs=src.crs, transform=src.transform, shape=src.shape)
    return power, grid, meta


def pair_change(hh_power, hv_power):
    """Existing preprocessing for one before/after pair; inputs are (2, y, x) linear power."""
    data = prepare_polarizations(hh_power, hv_power)
    pair = compare_polarizations(data, 0, 1)
    return dict(HH_delta=pair['HH_delta'], HV_delta=pair['HV_delta'], valid=pair['valid'],
                HH_db=data['HH'], HV_db=data['HV'], statistics=pair['statistics'])


def lag_correlation(delta, valid, lag):
    """Pearson r between pixels `lag` cells apart (columns, rows) on the valid support."""
    if lag < 1:
        raise ValueError('Lag must be at least one pixel.')
    a = np.where(valid, delta, np.nan)
    out = []
    for x, y in ((a[:, :-lag], a[:, lag:]), (a[:-lag, :], a[lag:, :])):
        ok = np.isfinite(x) & np.isfinite(y)
        if ok.sum() < 3 or np.std(x[ok]) < 1e-12 or np.std(y[ok]) < 1e-12:
            out.append(None)
        else:
            out.append(float(np.corrcoef(x[ok], y[ok])[0, 1]))
    return out


def distribution(values):
    values = np.asarray(values, dtype=float)
    q = np.percentile(values, [5, 25, 50, 75, 95])
    return dict(p5=float(q[0]), p25=float(q[1]), median=float(q[2]), p75=float(q[3]), p95=float(q[4]),
                mean=float(values.mean()), std=float(values.std()))


def region_summary(hh_delta, hv_delta, mask, pixel_area_km2=1e-4, hv_db=None, floor_percentile=5):
    """Numbers behind a Compass reading for one region (mask is boolean, same grid).

    ``hv_db`` (2, y, x) filtered HV dB for the two dates enables the HV
    dark-level flag: region median HV at or below the scene's
    ``floor_percentile`` on either date. This is a proxy, not a noise floor.
    """
    valid = np.isfinite(hh_delta) & np.isfinite(hv_delta)
    region = np.asarray(mask, dtype=bool) & valid
    n = int(region.sum())
    summary = dict(pixels=n, area_km2=n * pixel_area_km2)
    if n == 0:
        return summary
    summary['HH'] = distribution(hh_delta[region])
    summary['HV'] = distribution(hv_delta[region])
    if hv_db is not None:
        levels = []
        for index in (0, 1):
            scene = float(np.percentile(hv_db[index][valid], floor_percentile))
            local = float(np.median(hv_db[index][region]))
            levels.append(dict(region_median_db=local, scene_percentile_db=scene))
        summary['hv_dark_level'] = dict(percentile=floor_percentile, dates=levels,
                                        flag=any(l['region_median_db'] <= l['scene_percentile_db'] for l in levels))
    return summary


def compass_label(summary, dead_zone_db=DEFAULT_DEAD_ZONE_DB, min_pixels=MIN_PIXELS, reference=(0.0, 0.0)):
    """Deterministic label from a region summary. ``reference`` is subtracted
    from the medians (e.g. the scene-wide median vector) for a relative reading."""
    if not np.isfinite(dead_zone_db) or dead_zone_db <= 0:
        raise ValueError('Dead zone must be a positive number of dB.')
    if summary.get('pixels', 0) < min_pixels:
        return dict(key='inconclusive', reason=f"only {summary.get('pixels', 0)} valid pixels (< {min_pixels})",
                    reason_key='compass.reason.pixels', values=dict(pixels=summary.get('pixels', 0), minimum=min_pixels))
    h = summary['HH']['median'] - reference[0]
    v = summary['HV']['median'] - reference[1]
    tau = dead_zone_db
    straddle = lambda d, ref: d['p25'] - ref < 0 < d['p75'] - ref
    if max(abs(h), abs(v)) < tau:
        return dict(key='inconclusive', reason=f'median change vector ({h:+.2f}, {v:+.2f}) dB is inside the ±{tau:g} dB dead zone',
                    reason_key='compass.reason.dead_zone', values=dict(h=h, v=v, tau=tau))
    if straddle(summary['HH'], reference[0]) and straddle(summary['HV'], reference[1]):
        return dict(key='inconclusive', reason='the middle 50% of pixels disagree in direction on both HH and HV',
                    reason_key='compass.reason.disagree', values={})
    if h <= -tau and v <= -tau / 2:
        key = 'smoother_surface'
    elif h <= -tau and abs(v) < tau / 2:
        key = 'hh_darkening'
    elif h >= tau and v < tau:
        key = 'hh_brightening'
    elif v <= -tau and h > -tau:
        key = 'volume_loss'
    elif v >= tau:
        key = 'volume_gain'
    else:
        return dict(key='inconclusive', reason=f'mixed directions ({h:+.2f} dB HH, {v:+.2f} dB HV) without a single reading',
                    reason_key='compass.reason.mixed', values=dict(h=h, v=v))
    return dict(key=key, reason=f'median ΔHH {h:+.2f} dB, median ΔHV {v:+.2f} dB; rule: {LABELS[key]["rule"]}',
                reason_key='compass.reason.rule', values=dict(h=h, v=v, rule_of=key))


def sector_shares(hh_delta, hv_delta, mask, dead_zone_db=DEFAULT_DEAD_ZONE_DB):
    """Where the pixel cloud falls under the same direction rules (a spread view, not a per-pixel classification)."""
    valid = np.isfinite(hh_delta) & np.isfinite(hv_delta) & np.asarray(mask, dtype=bool)
    h = hh_delta[valid]; v = hv_delta[valid]; t = dead_zone_db
    if not h.size:
        return {}
    dead = np.maximum(np.abs(h), np.abs(v)) < t
    keys = np.full(h.shape, 'mixed directions', dtype=object)
    keys[dead] = 'inside dead zone'
    rules = (('smoother_surface', (h <= -t) & (v <= -t / 2)), ('hh_darkening', (h <= -t) & (np.abs(v) < t / 2)),
             ('hh_brightening', (h >= t) & (v < t)), ('volume_loss', (v <= -t) & (h > -t)), ('volume_gain', v >= t))
    assigned = dead.copy()
    for key, condition in rules:
        hit = condition & ~assigned
        keys[hit] = LABELS[key]['title']; assigned |= hit
    n = float(h.size)
    order = ['inside dead zone'] + [LABELS[k]['title'] for k, _ in rules] + ['mixed directions']
    return {name: float((keys == name).sum()) / n for name in order}


def compass_reading(summary, scene, dead_zone_db=DEFAULT_DEAD_ZONE_DB, min_pixels=MIN_PIXELS):
    """Evaluate the region under BOTH references and report whether they agree.

    ``scene`` is the scene-wide median (ΔHH, ΔHV). The raw reading uses the
    region medians as measured; the relative reading subtracts ``scene``.
    No automatic correction is implied: both are shown.
    """
    raw = compass_label(summary, dead_zone_db, min_pixels)
    relative = compass_label(summary, dead_zone_db, min_pixels, reference=tuple(scene))
    key = raw['key'] if raw['key'] == relative['key'] else 'reference_dependent'
    numbers = {}
    if summary.get('pixels', 0):
        numbers = dict(raw=(summary['HH']['median'], summary['HV']['median']),
                       relative=(summary['HH']['median'] - scene[0], summary['HV']['median'] - scene[1]))
    shown = raw['key'] if key != 'reference_dependent' else key
    return dict(key=key, agree=key != 'reference_dependent', raw=raw, relative=relative, numbers=numbers,
                scene=tuple(scene), dead_zone_db=dead_zone_db, alternatives=alternatives_for(shown),
                alternative_keys=alternative_keys(shown))


def rectangle_mask(shape, rows, columns):
    """Boolean mask from fractional (start, stop) row and column ranges in [0, 1]."""
    (r0, r1), (c0, c1) = rows, columns
    if not (0 <= r0 < r1 <= 1 and 0 <= c0 < c1 <= 1):
        raise ValueError('Rectangle ranges must satisfy 0 <= start < stop <= 1.')
    mask = np.zeros(shape, dtype=bool)
    h, w = shape
    mask[int(np.floor(r0 * h)):int(np.ceil(r1 * h)), int(np.floor(c0 * w)):int(np.ceil(c1 * w))] = True
    return mask


def percent_ranges(rows, columns, minimum_width=1):
    """Turn slider percent ranges (0–100) into valid fractional ranges.

    Equal or reversed ends are widened to ``minimum_width`` percent while
    staying inside 0–100 (e.g. (100, 100) -> (99, 100)). Raises ValueError for
    values outside 0–100 so the caller can show a friendly message.
    """
    out = []
    for start, stop in (rows, columns):
        start, stop = sorted((float(start), float(stop)))
        if not (0 <= start <= 100 and 0 <= stop <= 100):
            raise ValueError('Rectangle percentages must lie between 0 and 100.')
        if stop - start < minimum_width:
            stop = min(100.0, start + minimum_width)
            start = stop - minimum_width
        out.append((start / 100, stop / 100))
    return tuple(out)


def load_pair(directory=DIRECTORY):
    """Verified cached June21→July3 compass inputs written by scripts/process_hv_compass.py."""
    directory = Path(directory)
    report = json.loads((directory / 'hv_signal_assessment.json').read_text())
    if report.get('status') != 'success':
        raise ValueError('HV compass outputs are incomplete.')
    for name, expected in report['output_sha256'].items():
        if sha256(directory / name) != expected:
            raise ValueError(f'{name} changed since it was written.')
    with rasterio.open(directory / 'pair_change_db.tif') as src:
        if src.descriptions != ('HH_after_minus_before_dB', 'HV_after_minus_before_dB'):
            raise ValueError('Unexpected change bands.')
        hh_delta, hv_delta = src.read().astype(float)
        grid = dict(crs=src.crs, transform=src.transform, shape=src.shape)
    with rasterio.open(directory / 'pair_filtered_db.tif') as src:
        bands = src.read().astype(float)
    return dict(HH_delta=hh_delta, HV_delta=hv_delta, HH_db=bands[:2], HV_db=bands[2:], grid=grid, report=report,
                valid=np.isfinite(hh_delta) & np.isfinite(hv_delta))


def region_options(root=ROOT):
    """Real saved masks on the Louisiana grid: baseline classes and investigation regions."""
    options = {}
    with rasterio.open(root / 'data/water_change/water_change_classes.tif') as src:
        classes = src.read(1)
    names = {1: 'Persistent water candidate', 2: 'New water candidate (possible expansion)',
             3: 'Receded water candidate', 4: 'Other valid surface'}
    for code, name in names.items():
        options[f'Baseline class · {name}'] = classes == code
    path = root / 'data/investigation_engine/region_labels.tif'
    if path.exists():
        with rasterio.open(path) as src:
            labels = src.read(1)
        for rid in sorted(int(x) for x in np.unique(labels[np.isfinite(labels)]) if x > 0):
            options[f'Investigation region {rid}'] = labels == rid
    return options
