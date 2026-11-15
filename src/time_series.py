"""Small real HH time series. Residuals are dB deviations, never probabilities."""
import json
import warnings
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine, rowcol, xy
from rasterio.warp import transform

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'data/time_series'
DATES = ('2026-06-21', '2026-07-03', '2026-07-15', '2026-07-27', '2026-08-20', '2026-09-01')


def temporal_summary(db, min_observations=4):
    """Robust temporal median and signed dB residual, with insufficient data masked.

    No variance division, z-score, bias correction or probability calibration.
    The median resists a single extreme date; zero temporal variation gives zero.
    Four finite dates is a declared exploration guardrail, not a validation rule.
    """
    db = np.asarray(db, dtype=float)
    if db.ndim != 3 or not 2 <= min_observations <= db.shape[0]:
        raise ValueError('Expected a time/y/x cube and a feasible minimum count.')
    clean = np.where(np.isfinite(db), db, np.nan)
    counts = np.isfinite(clean).sum(axis=0)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        median = np.nanmedian(clean, axis=0)
    median[counts < min_observations] = np.nan
    return median, clean - median, counts


def load_time_series(directory=DIRECTORY):
    """Validate locally saved observations and georeferencing; no network/secrets."""
    directory = Path(directory)
    report = json.loads((directory / 'results.json').read_text())
    if report['status'] != 'success' or tuple(o['date'] for o in report['observations']) != DATES:
        raise ValueError('Six verified dates are required.')
    with rasterio.open(directory / 'hh_db.tif') as src:
        if src.count != 6 or src.crs.to_epsg() != 32615 or src.res != (10, 10):
            raise ValueError('Unexpected Louisiana HH time-series grid.')
        db = src.read().astype(float)
        if src.descriptions != DATES or src.tags().get('source_layer') != '/science/LSAR/GCOV/grids/frequencyA/HHHH':
            raise ValueError('HH dates or polarization provenance mismatch.')
        grid = dict(crs=src.crs, transform=src.transform, shape=src.shape)
    if list(grid['shape']) != report['shape'] or not np.allclose(list(grid['transform'])[:6], report['transform'], atol=1e-8, rtol=0):
        raise ValueError('Grid disagrees with processing report.')
    common = np.isfinite(db).all(axis=0)
    if int(common.sum()) != report['common_valid_pixels']:
        raise ValueError('Common validity disagrees with processing report.')
    return dict(db=db, common=common, grid=grid, report=report)


def pair_difference(db, first, second):
    if first not in range(db.shape[0]) or second not in range(db.shape[0]):
        raise ValueError('Date index outside the saved cube.')
    valid = np.isfinite(db[first]) & np.isfinite(db[second])
    return np.where(valid, db[second] - db[first], np.nan), valid


def point_series(data, longitude, latitude, radius=0):
    """Median filtered dB in a native-grid neighborhood; never fill missing dates."""
    if not np.isfinite([longitude, latitude]).all() or not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        raise ValueError('Coordinates must be finite WGS84 longitude/latitude.')
    if radius not in (0, 1, 2):
        raise ValueError('Neighborhood radius must be 0, 1 or 2 pixels.')
    grid = data['grid']
    east, north = transform('EPSG:4326', grid['crs'], [longitude], [latitude])
    row, col = rowcol(grid['transform'], east[0], north[0])
    h, w = grid['shape']
    if not 0 <= row < h or not 0 <= col < w:
        raise ValueError('Selected point is outside the cached raster. Choose a point inside the outlined AOI.')
    window = data['db'][:, max(0, row-radius):min(h, row+radius+1), max(0, col-radius):min(w, col+radius+1)]
    center_x, center_y = xy(grid['transform'], row, col)
    lon, lat = transform(grid['crs'], 'EPSG:4326', [center_x], [center_y])
    rows = []
    for item, values in zip(data['report']['observations'], window):
        valid = values[np.isfinite(values)]
        rows.append({'Acquisition UTC': item['acquisition_utc'], 'HH backscatter (dB)': float(np.median(valid)) if valid.size else None,
                     'Valid neighborhood pixels': int(valid.size), 'Available neighborhood pixels': int(values.size),
                     'Status': 'valid' if valid.size else 'missing / no data', 'Product ID': item['product_id']})
    return dict(rows=rows, row=int(row), column=int(col), pixel_center_longitude=lon[0], pixel_center_latitude=lat[0],
                requested_longitude=float(longitude), requested_latitude=float(latitude), radius_pixels=radius)
