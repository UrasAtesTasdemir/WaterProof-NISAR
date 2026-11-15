"""Phase 1: bounded real HHHH reads; new outputs only, no old-result writes."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import asf_search as asf
import numpy as np
import rasterio
import xarray as xr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely import wkt
from shapely.geometry import shape, mapping
from rasterio.features import shapes
from rasterio.warp import transform_geom
from shapely.ops import unary_union

from scripts.check_earthdata_access import available_token, AccessCheckError
from scripts.visualize_nisar import read_subset, save_geotiff
from scripts.detect_water_change import load_cached, save_raster
from scripts.search_nisar import parse_product, COMPATIBILITY
from src.nisar_data import open_frequency_a, RadarDataError
from src.water_change import align_power, mask_aware_mean, power_to_db, pixel_area_km2
from src.time_series import DIRECTORY, DATES, temporal_summary


def verify_catalog(catalog, inventory, aoi):
    """Match researched IDs to real catalog properties, filename and footprint."""
    selected = []
    reference = None
    projected_aoi = shape(transform_geom('EPSG:4326', 'EPSG:32615', mapping(aoi)))
    for day in DATES:
        researched = next(r for r in inventory if r['date'] == day)
        found = [f for f in catalog['features'] if f['properties']['fileID'] == researched['product_id']]
        if len(found) != 1:
            raise ValueError('A researched product is missing or ambiguous in ASF.')
        feature = found[0]; props = feature['properties']
        item = parse_product(props['url'], day)
        if item is None or item['product_id'] != researched['product_id']:
            raise ValueError('Catalog URL does not match a researched GCOV HH acquisition.')
        fields = item['filename_fields']
        key = tuple(fields[k] for k in COMPATIBILITY)
        if reference is not None and reference != key:
            raise ValueError('Track/frame or acquisition/processing configuration differs.')
        reference = key
        if (props['pathNumber'] != int(fields['track']) or props['frameNumber'] != int(fields['frame'])
                or props['collectionName'] != 'NISAR_L2_GCOV_PROVISIONAL_V1'
                or 'HH' not in props['mainBandPolarization'] or props['flightDirection'] != 'ASCENDING'
                or props['productionConfiguration'] != 'PR' or props['crid'] != fields['crid']):
            raise ValueError('Catalog properties disagree with the compatible filename.')
        footprint = shape(transform_geom('EPSG:4326', 'EPSG:32615', feature['geometry']))
        fraction = projected_aoi.intersection(footprint).area / projected_aoi.area
        if fraction < .999:
            raise ValueError('AOI is not fully covered by a selected catalog footprint.')
        item.update(date=day, catalog_coverage_fraction=min(1., fraction), catalog_metadata={k:props.get(k) for k in (
            'startTime','stopTime','pathNumber','frameNumber','mainBandPolarization','sideBandPolarization',
            'rangeBandwidth','productionConfiguration','crid','pgeVersion','collectionName')})
        selected.append(item)
    if len({json.dumps(r['catalog_metadata']['rangeBandwidth']) for r in selected}) != 1 or len({r['catalog_metadata']['pgeVersion'] for r in selected}) != 1:
        raise ValueError('Processing version or bandwidth differs; scientific review required.')
    return selected


def draw_outputs(db, common, median, anomalies, grid, out):
    pooled = db[:, common]; low, high = np.percentile(pooled, [2, 98])
    if high <= low: high = low + 1
    from rasterio.transform import array_bounds
    west, south, east, north = array_bounds(*grid['shape'], grid['transform'])
    extent = west, east, south, north
    cmap = plt.get_cmap('gray').copy(); cmap.set_bad('#d8e1e8')
    fig, axes = plt.subplots(2, 3, figsize=(14, 7), layout='constrained')
    for ax, day, values in zip(axes.flat, DATES, db):
        im = ax.imshow(np.where(common, values, np.nan), extent=extent, origin='upper', cmap=cmap, vmin=low, vmax=high)
        ax.set_title(day + ' · HH'); ax.ticklabel_format(useOffset=False, style='plain'); ax.tick_params(labelsize=7)
        ax.set_xlabel('UTM easting (m)'); ax.set_ylabel('UTM northing (m)')
    fig.colorbar(im, ax=axes, label='Filtered gamma-0 (dB)', shrink=.65)
    fig.suptitle('Real NISAR HH · six-date common valid footprint · exploratory, not flood confirmation')
    fig.savefig(out/'six_date_backscatter.png', dpi=140); plt.close(fig)
    for filename, values, title, palette, vmin, vmax in (
        ('temporal_median.png', median, 'Six-date temporal median', 'gray', low, high),
        ('last_date_anomaly.png', anomalies[-1], '1 September minus per-pixel temporal median · exploratory', 'RdBu_r', -6, 6)):
        fig, ax = plt.subplots(figsize=(9, 4.5), layout='constrained')
        cm = plt.get_cmap(palette).copy(); cm.set_bad('#d8e1e8')
        im = ax.imshow(values, extent=extent, origin='upper', cmap=cm, vmin=vmin, vmax=vmax)
        ax.set_title(title); ax.set_xlabel('UTM easting (m)'); ax.set_ylabel('UTM northing (m)')
        ax.ticklabel_format(useOffset=False, style='plain'); fig.colorbar(im, ax=ax, label='dB')
        fig.savefig(out/filename, dpi=140); plt.close(fig)
    return [float(low), float(high)]


def main():
    out = DIRECTORY; out.mkdir(exist_ok=True)
    if (out/'results.json').exists():
        print('Completed time-series output already exists; left unchanged.'); return 0
    stage = 'catalog'; started = time.monotonic(); records = []
    try:
        manifest = json.loads((ROOT/'data/nisar_manifest.json').read_text())
        aoi = wkt.loads(manifest['aoi_wkt'])
        inventory = json.loads((ROOT/'data/pair_selection/nisar_inventory.json').read_text())
        catalog_path = out/'catalog.geojson'
        if catalog_path.exists():
            catalog = json.loads(catalog_path.read_text())
        else:
            options = asf.ASFSearchOptions(dataset=['NISAR'], processingLevel=['GCOV'], productionConfiguration=['PR'],
                dataMaturity='PROVISIONAL', intersectsWith=manifest['aoi_wkt'], start='2026-06-21T00:00:00Z',
                end='2026-09-02T00:00:00Z', maxResults=200)
            results = asf.search(opts=options)
            if len(results) >= 200: raise ValueError('Catalog search truncated.')
            catalog = results.geojson(); catalog_path.write_text(json.dumps(catalog, indent=2)+'\n')
        items = verify_catalog(catalog, inventory, aoi)
        (out/'manifest.json').write_text(json.dumps({'aoi_wkt':manifest['aoi_wkt'], 'observations':items, 'compatibility_fields':COMPATIBILITY},indent=2)+'\n')
        powers = []; source_meta = []; grid = None
        token = None
        for item in items:
            stage = item['date']; day = item['date']
            if day in DATES[:2]:
                old = next(r for r in manifest['observations'] if r['start_time_utc'][:10] == day)
                if old['product_id'] != item['product_id']: raise ValueError('Existing cache is a different product.')
                previous = json.loads((ROOT/'data/nisar_visualization_report.json').read_text())
                power, valid, source_grid, metadata = load_cached(old, previous)
                metadata.update(reused_existing_cache=True, range_bytes_read_this_run=0)
            else:
                path = out/f'hhhh_{day}.tif'; sidecar = path.with_suffix('.json')
                if path.exists() and sidecar.exists():
                    metadata = json.loads(sidecar.read_text())
                    if metadata['product_id'] != item['product_id'] or metadata['layer'] != 'HHHH' or hashlib.sha256(path.read_bytes()).hexdigest() != metadata['sha256']:
                        raise ValueError('New subset cache failed provenance/hash verification.')
                    with rasterio.open(path) as src:
                        power = src.read(1); source_grid = dict(crs=src.crs, transform=src.transform, shape=src.shape)
                    metadata['range_bytes_read_this_run'] = 0
                else:
                    token = token or available_token()
                    if not token: raise RadarDataError('No protected local Earthdata credential is available.')
                    print('Reading only the real HHHH window:', day, flush=True)
                    with open_frequency_a(item, token) as (ds, stats):
                        power, raw_db, crs, tr, metadata = read_subset(ds, aoi)
                        if metadata['power_units'] not in ('1', 'unitless', 'dimensionless'):
                            raise RadarDataError('HHHH units are not confirmed linear dimensionless power.')
                    source_grid = dict(crs=crs, transform=tr, shape=power.shape)
                    save_geotiff(path, power, raw_db, crs, tr, item)
                    metadata.update(product_id=item['product_id'], acquisition_utc=item['start_time_utc'], **stats,
                                    range_bytes_read_this_run=stats['range_bytes_read'], reused_existing_cache=False,
                                    path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                    sidecar.write_text(json.dumps(metadata,indent=2)+'\n')
                valid = np.isfinite(power) & (power > 0)
            if source_grid['crs'].to_epsg() != 32615 or abs(source_grid['transform'].a) != 10 or source_grid['transform'].e != -10:
                raise ValueError('Unexpected CRS or resolution; review before alignment.')
            if grid is None: grid = source_grid
            power, valid, corrected = align_power(power, valid, source_grid, grid)
            metadata['aligned_by_nearest'] = corrected
            powers.append(power); source_meta.append(metadata); records.append(day)
            print('Verified', day, int(valid.sum()), 'valid pixels', flush=True)
        stage = 'common cube'
        powers = np.stack(powers); per_date_valid = np.isfinite(powers) & (powers > 0)
        common = per_date_valid.all(axis=0)
        inside = source_meta[0]['valid_pixels']
        if common.sum() < .8*inside: raise ValueError('Less than 80% of the original valid AOI is common to six dates; review coverage.')
        db = np.stack([power_to_db(mask_aware_mean(p, v, 3)) for p, v in zip(powers, per_date_valid)])
        common_cube = np.where(common, db, np.nan)
        median, anomaly, counts = temporal_summary(common_cube)
        delta = np.diff(common_cube, axis=0)
        tags = dict(source_layer='/science/LSAR/GCOV/grids/frequencyA/HHHH', polarization='HH',
            source_ids=json.dumps([o['product_id'] for o in items]), acquisition_utc=json.dumps([o['start_time_utc'] for o in items]),
            processing='3x3 mask-aware linear-power mean per-date mask, then 10*log10; no scene normalization',
            interpretation='Exploratory HH radar dynamics; not confirmed water or flooding')
        for filename, arrays, descriptions, categorical in (
            ('hh_db.tif',db,DATES,False), ('common_hh_db.tif',common_cube,DATES,False),
            ('common_valid.tif',[common],['all_six_dates_valid'],True),
            ('delta_consecutive_db.tif',delta,[f'{a}_minus_{b}' for b,a in zip(DATES,DATES[1:])],False),
            ('delta_from_first_db.tif',common_cube-common_cube[0],DATES,False),
            ('temporal_median_db.tif',[median],['six_date_temporal_median_dB'],False),
            ('anomaly_db.tif',anomaly,DATES,False)):
            save_raster(out/filename, arrays, descriptions, grid, tags, categorical=categorical)
        tr = grid['transform']; h,w = grid['shape']
        times = np.array([np.datetime64(o['start_time_utc'].replace('+00:00','').replace('Z',''),'ns') for o in items])
        cube = xr.Dataset({
            'HHHH_linear_power':(('time','y','x'),powers.astype('float32')),
            'HH_filtered_db':(('time','y','x'),db.astype('float32')),
            'HH_common_db':(('time','y','x'),common_cube.astype('float32')),
            'valid_observation':(('time','y','x'),per_date_valid.astype('uint8')),
            'common_valid':(('y','x'),common.astype('uint8')),
            'temporal_median_db':(('y','x'),median.astype('float32')),
            'exploratory_anomaly_db':(('time','y','x'),anomaly.astype('float32'))},
            coords={'time':times,'y':tr.f+(np.arange(h)+.5)*tr.e,'x':tr.c+(np.arange(w)+.5)*tr.a},
            attrs={**tags,'crs':grid['crs'].to_wkt(),'GeoTransform':' '.join(map(str,tr.to_gdal())), 'anomaly_definition':'HH_common_db minus per-pixel six-date temporal median; dB, NOT z-scores/probabilities'})
        for name in ('HH_filtered_db','HH_common_db','temporal_median_db','exploratory_anomaly_db'):cube[name].attrs['units']='dB'
        cube['HHHH_linear_power'].attrs['units']='1'
        cube.to_netcdf(out/'hh_time_series.nc',engine='h5netcdf',encoding={k:{'zlib':True,'complevel':4} for k in cube.data_vars})
        with xr.open_dataset(out/'hh_time_series.nc',engine='h5netcdf') as check:
            np.testing.assert_allclose(check.HH_common_db.values,common_cube.astype('float32'),equal_nan=True)
            np.testing.assert_array_equal(check.time.values,times)
        stats = []
        for item, values, valid in zip(items, db, per_date_valid):
            sample = values[common]; quantiles = np.percentile(sample,[5,25,50,75,95])
            stats.append(dict(date=item['date'],acquisition_utc=item['start_time_utc'],product_id=item['product_id'],
                valid_pixels=int(valid.sum()),common_pixels=int(common.sum()),mean_db=float(sample.mean()),std_db=float(sample.std()),
                **{f'p{p}_db':float(v) for p,v in zip((5,25,50,75,95),quantiles)}))
        footprint = unary_union([shape(g) for g,v in shapes(common.astype('uint8'), mask=common, transform=tr) if v==1])
        (out/'common_footprint.geojson').write_text(json.dumps(transform_geom(grid['crs'],'EPSG:4326',mapping(footprint)))+'\n')
        scale = draw_outputs(db,common,median,anomaly,grid,out)
        report = dict(status='success',created_utc=datetime.now(timezone.utc).isoformat(),observations=[dict(**r,source_verification=s) for r,s in zip(stats,source_meta)],
            aoi_wkt=manifest['aoi_wkt'],crs=str(grid['crs']),transform=list(tr)[:6],shape=list(grid['shape']),
            common_valid_pixels=int(common.sum()),common_valid_area_km2=int(common.sum())*pixel_area_km2(grid['crs'],tr),
            common_fraction_of_original_valid=float(common.sum()/inside),display_scale_db=scale,source_layer=tags['source_layer'],
            filter_size=3,filter_mask='per-date finite positive power; invalid centers remain invalid; comparisons use common masks',
            anomaly_definition='signed dB deviation from per-pixel six-date temporal median; not normalized, not probability',
            consecutive_intervals_days=[int((times[i]-times[i-1])/np.timedelta64(1,'D')+.5) for i in range(1,6)],
            full_hdf5_downloaded=False,elapsed_seconds=time.monotonic()-started)
        (out/'scene_statistics.json').write_text(json.dumps(stats,indent=2)+'\n')
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('SUCCESS: six real dates;',report['common_valid_area_km2'],'km² common valid area',flush=True)
        return 0
    except Exception as exc:
        # No URL-bearing exception text/traceback: signed redirects and secrets stay in memory.
        detail = str(exc) if isinstance(exc,(RadarDataError,AccessCheckError)) else 'See stage and error type; sensitive exception details suppressed.'
        failure=dict(status='blocked',stage=stage,error_type=type(exc).__name__,detail=detail,successfully_read_dates=records)
        (out/'access_blocker.json').write_text(json.dumps(failure,indent=2)+'\n')
        print(json.dumps(failure),flush=True); return 2


if __name__ == '__main__':
    raise SystemExit(main())
