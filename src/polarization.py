"""HH/HV descriptive comparisons. No water/vegetation classifier or correction."""
import json
from pathlib import Path

import numpy as np
import rasterio
from src.water_change import mask_aware_mean, power_to_db, pixel_area_km2

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT/'data/polarization_analysis'
GROUP = '/science/LSAR/GCOV/grids/frequencyA'


def prepare_polarizations(hh_power, hv_power, filter_size=3):
    """Matched per-date masks and identical linear-power filtering for both bands."""
    hh = np.asarray(hh_power, dtype=float); hv = np.asarray(hv_power, dtype=float)
    if hh.shape != hv.shape or hh.ndim != 3:
        raise ValueError('HH/HV power must share time/y/x shape.')
    valid = np.isfinite(hh) & (hh>0) & np.isfinite(hv) & (hv>0)
    hh_filtered = np.stack([mask_aware_mean(p,v,filter_size) for p,v in zip(hh,valid)])
    hv_filtered = np.stack([mask_aware_mean(p,v,filter_size) for p,v in zip(hv,valid)])
    hh_db = power_to_db(hh_filtered); hv_db = power_to_db(hv_filtered)
    # Dimensionless LINEAR POWER ratio; its dB value is HH_dB - HV_dB.
    ratio = np.full(hh.shape,np.nan)
    np.divide(hh_filtered,hv_filtered,out=ratio,where=valid)
    ratio_db = hh_db-hv_db
    return dict(HH=hh_db,HV=hv_db,ratio=ratio,ratio_db=ratio_db,valid=valid,common=valid.all(axis=0))


def compare_polarizations(data, first, second):
    n = len(data['HH'])
    if first not in range(n) or second not in range(n):
        raise ValueError('Date index outside the polarization observations.')
    valid = data['valid'][first] & data['valid'][second]
    hh_delta = np.where(valid,data['HH'][second]-data['HH'][first],np.nan)
    hv_delta = np.where(valid,data['HV'][second]-data['HV'][first],np.nan)
    hh = hh_delta[valid]; hv = hv_delta[valid]
    if not hh.size: raise ValueError('No common HH/HV pair pixels.')
    corr = float(np.corrcoef(hh,hv)[0,1]) if np.std(hh)>1e-10 and np.std(hv)>1e-10 else None
    return dict(valid=valid,HH_delta=hh_delta,HV_delta=hv_delta,ratio_delta_db=hh_delta-hv_delta,
        statistics=dict(pixels=int(valid.sum()),median_HH_delta_db=float(np.median(hh)),median_HV_delta_db=float(np.median(hv)),
            median_delta_HH_minus_delta_HV_db=float(np.median(hh-hv)),spatial_Pearson_r=corr))


def load_polarization(directory=None):
    """Verify local layer provenance, grid, masks and ratio identity before UI use."""
    if directory is None:
        directory = next((DIRECTORY/name for name in ('six_date','two_date') if (DIRECTORY/name/'results.json').exists()),DIRECTORY/'two_date')
    directory = Path(directory); report = json.loads((directory/'results.json').read_text())
    if report['status'] != 'success' or len(report['observations']) not in (2,6):
        raise ValueError('Expected a completed two/six-date polarization output.')
    dates = tuple(o['date'] for o in report['observations']); arrays = {}; grid = None
    for band,layer in (('HH','HHHH'),('HV','HVHV'),('ratio_db',None)):
        filename = {'HH':'hh_db.tif','HV':'hv_db.tif','ratio_db':'hh_hv_ratio_db.tif'}[band]
        with rasterio.open(directory/filename) as src:
            current = dict(crs=src.crs,transform=src.transform,shape=src.shape)
            expected_source = GROUP+'/'+layer if layer else 'derived:HH_dB-HV_dB'
            if (src.descriptions != dates or src.tags().get('source_layer') != expected_source
                    or src.tags().get('units') != 'dB' or src.count != len(dates)):
                raise ValueError('Polarization/date/units provenance mismatch.')
            if grid is not None and grid != current: raise ValueError('Polarization grids differ.')
            grid = current; arrays[band] = src.read().astype(float)
    if (grid['crs'].to_epsg()!=32615 or not grid['transform'].almost_equals(rasterio.Affine(*report['transform']),precision=1e-8)
            or list(grid['shape'])!=report['shape']): raise ValueError('Unexpected Louisiana polarization grid.')
    valid = np.isfinite(arrays['HH']) & np.isfinite(arrays['HV'])
    if not np.array_equal(valid,np.isfinite(arrays['HH'])) or not np.array_equal(valid,np.isfinite(arrays['HV'])):
        raise ValueError('HH/HV masks are inconsistent.')
    if not np.array_equal(valid,np.isfinite(arrays['ratio_db'])) or not np.allclose((arrays['HH']-arrays['HV'])[valid],arrays['ratio_db'][valid],atol=5e-6,rtol=0):
        raise ValueError('Power-ratio dB identity failed.')
    common = valid.all(axis=0)
    if int(common.sum()) != report['common_valid_pixels'] or not np.isclose(common.sum()*pixel_area_km2(grid['crs'],grid['transform']),report['common_valid_area_km2']):
        raise ValueError('Common projected area mismatch.')
    return dict(**arrays,valid=valid,common=common,grid=grid,report=report,directory=directory)
