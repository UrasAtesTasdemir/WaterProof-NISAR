"""Bounded real HVHV subsets; reuse HH cache and preserve every prior output."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import numpy as np
import rasterio
import xarray as xr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from rasterio.transform import array_bounds
from shapely import wkt
from scripts.check_earthdata_access import available_token,AccessCheckError
from scripts.visualize_nisar import read_subset
from scripts.detect_water_change import save_raster
from src.nisar_data import open_frequency_a,RadarDataError
from src.water_change import align_power,power_to_db,pixel_area_km2
from src.time_series import load_time_series
from src.polarization import DIRECTORY,GROUP,prepare_polarizations,compare_polarizations


def inspect_layers(ds):
    layers = {name:dict(shape=list(ds[name].shape),dtype=str(ds[name].dtype),units=str(ds[name].attrs.get('units','not specified')),
                        description=str(ds[name].attrs.get('long_name',ds[name].attrs.get('description',''))))
              for name in ds.data_vars if re.fullmatch('[HV]{4}',name)}
    if 'HVHV' not in layers or 'HHHH' not in layers:
        raise RadarDataError('Real product does not expose both HHHH and HVHV in frequencyA.')
    for name in ('HHHH','HVHV'):
        if layers[name]['units'] not in ('1','unitless','dimensionless') or len(layers[name]['shape'])!=2 or not np.issubdtype(ds[name].dtype,np.floating):
            raise RadarDataError('Polarization layer is not confirmed dimensionless real linear power.')
    return layers


def draw_comparison(data,first,second):
    """Six panels, common radar scale and common change scale; all native pixels."""
    pair = compare_polarizations(data,first,second); valid = pair['valid']
    low,high = data['report']['backscatter_scale_db']; limit = data['report']['change_scale_db'][1]
    west,south,east,north = array_bounds(*data['grid']['shape'],data['grid']['transform']); extent = west,east,south,north
    dates = [o['date'] for o in data['report']['observations']]
    fig,axes = plt.subplots(2,3,figsize=(14,6.7),layout='constrained')
    for row,band in enumerate(('HH','HV')):
        for col,(array,title,is_delta) in enumerate(((data[band][first],f'{band} · {dates[first]}',False),
                (data[band][second],f'{band} · {dates[second]}',False),(pair[band+'_delta'],f'Δ {band}: comparison − selected',True))):
            cm = plt.get_cmap('RdBu_r' if is_delta else 'gray').copy(); cm.set_bad('#d8e1e8')
            im = axes[row,col].imshow(np.where(valid,array,np.nan),extent=extent,origin='upper',interpolation='nearest',
                cmap=cm,vmin=-limit if is_delta else low,vmax=limit if is_delta else high)
            axes[row,col].set_title(title,fontsize=10);axes[row,col].tick_params(labelsize=7)
            axes[row,col].ticklabel_format(style='plain',useOffset=False)
            axes[row,col].set_xlabel('UTM easting (m)');axes[row,col].set_ylabel('UTM northing (m)')
            fig.colorbar(im,ax=axes[row,col],label='Δ dB' if is_delta else 'Gamma-0 (dB)',shrink=.7)
    fig.suptitle('Real NISAR HH/HV · matched valid mask · descriptive scattering, not flooded-vegetation classification',fontsize=11)
    return fig


def draw_change_relation(pair):
    fig,ax = plt.subplots(figsize=(6,4.4),layout='constrained')
    valid = pair['valid']; hh = pair['HH_delta'][valid]; hv = pair['HV_delta'][valid]
    image = ax.hexbin(hh,hv,gridsize=60,mincnt=1,bins='log',cmap='viridis')
    low = min(hh.min(),hv.min()); high = max(hh.max(),hv.max())
    ax.plot([low,high],[low,high],'--',color='#d17f22',label='Equal HH/HV change')
    ax.set_xlabel('Δ HH (dB)');ax.set_ylabel('Δ HV (dB)');ax.set_title('All common pixels · spatially dependent observations')
    ax.legend(fontsize=8);fig.colorbar(image,ax=ax,label='Pixel count (log scale)')
    return fig


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--dates',type=int,choices=(2,6),default=2);args=parser.parse_args()
    base = DIRECTORY;out = base/('two_date' if args.dates==2 else 'six_date');out.mkdir(parents=True,exist_ok=True)
    if (out/'results.json').exists():print('Completed polarization results exist; left unchanged.');return 0
    rawdir = base/'raw';rawdir.mkdir(exist_ok=True);stage = 'load verified HH cache';read_dates = [];start=time.monotonic()
    try:
        hh_data = load_time_series();manifest=json.loads((ROOT/'data/time_series/manifest.json').read_text())
        items=manifest['observations'][:args.dates];aoi=wkt.loads(manifest['aoi_wkt']);grid=hh_data['grid']
        with xr.open_dataset(ROOT/'data/time_series/hh_time_series.nc',engine='h5netcdf') as ds:
            if ds.HHHH_linear_power.attrs.get('units')!='1' or ds.attrs['source_layer']!=GROUP+'/HHHH':
                raise ValueError('Existing HH cube provenance/units mismatch.')
            hh_power=ds.HHHH_linear_power.isel(time=slice(0,args.dates)).values
        hv_list=[];sources=[];token=None
        for item in items:
            day=item['date'];stage=day;path=rawdir/f'hvhv_{day}.tif';sidecar=path.with_suffix('.json')
            if path.exists() and sidecar.exists():
                meta=json.loads(sidecar.read_text())
                if (meta['product_id']!=item['product_id'] or meta['layer']!='HVHV' or meta['hdf5_group']!=GROUP
                        or meta['sha256']!=hashlib.sha256(path.read_bytes()).hexdigest()):raise ValueError('HV source cache provenance mismatch.')
                with rasterio.open(path) as src:
                    if src.tags().get('source_layer')!=GROUP+'/HVHV':raise ValueError('HV cached raster layer tag mismatch.')
                    hv=src.read(1);cached_db=src.read(2);source_grid=dict(crs=src.crs,transform=src.transform,shape=src.shape)
                np.testing.assert_allclose(cached_db,power_to_db(hv),atol=5e-6,rtol=0,equal_nan=True)
                meta['range_bytes_read_this_run']=0
            else:
                token=token or available_token()
                if not token:raise RadarDataError('No protected local Earthdata credential is available.')
                print('Inspecting real frequencyA polarization metadata:',day,flush=True)
                with open_frequency_a(item,token) as (ds,transfer):
                    available=inspect_layers(ds)
                    hv,raw_db,crs,tr,meta=read_subset(ds,aoi,layer_name='HVHV')
                source_grid=dict(crs=crs,transform=tr,shape=hv.shape)
                tags=dict(source_layer=GROUP+'/HVHV',product_id=item['product_id'],acquisition_utc=item['start_time_utc'],power_units='1',db_formula='10*log10(positive linear power)')
                save_raster(path,[hv,raw_db],['HVHV_gamma0_power','HVHV_gamma0_dB'],source_grid,tags)
                meta.update(product_id=item['product_id'],acquisition_utc=item['start_time_utc'],available_layers=available,**transfer,
                    range_bytes_read_this_run=transfer['range_bytes_read'],sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                sidecar.write_text(json.dumps(meta,indent=2)+'\n')
            if source_grid['crs']!=grid['crs'] or source_grid['transform'].a!=10 or source_grid['transform'].e!=-10:
                raise ValueError('Unexpected HV CRS/resolution; review before processing.')
            hv,valid,corrected=align_power(hv,np.isfinite(hv)&(hv>0),source_grid,grid)
            meta['aligned_by_nearest']=corrected;hv_list.append(hv);sources.append(meta);read_dates.append(day)
            print('Verified real HVHV',day,int(valid.sum()),'positive valid pixels',flush=True)
        stage='joint scientific comparison';hv_power=np.stack(hv_list);data=prepare_polarizations(hh_power,hv_power)
        common=data['common'];count=int(common.sum())
        if count<.8*hh_data['common'].sum():raise ValueError('Joint HH/HV temporal coverage is below 80% of original common area; review required.')
        dates=[i['date'] for i in items];measurements=[]
        for idx,item in enumerate(items):
            row=dict(date=item['date'],acquisition_utc=item['start_time_utc'],product_id=item['product_id'],joint_valid_pixels=int(data['valid'][idx].sum()),statistics_pixels=count)
            for name in ('HH','HV','ratio_db'):
                values=data[name][idx][common];q=np.percentile(values,[25,50,75])
                row.update({name+'_p25_db':float(q[0]),name+'_median_db':float(q[1]),name+'_p75_db':float(q[2]),name+'_mean_db':float(values.mean()),name+'_std_db':float(values.std())})
            measurements.append(row)
        pooled=np.concatenate([data[b][:,common].ravel() for b in ('HH','HV')]);low,high=np.percentile(pooled,[2,98])
        pair=compare_polarizations(data,0,1);limit=max(1.,float(np.percentile(np.abs(np.concatenate([pair[b][common] for b in ('HH_delta','HV_delta')])),98)))
        report=dict(status='success',created_utc=datetime.now(timezone.utc).isoformat(),observations=measurements,sources=sources,
            source_layers={'HH':GROUP+'/HHHH','HV':GROUP+'/HVHV'},crs=str(grid['crs']),transform=list(grid['transform'])[:6],shape=list(grid['shape']),
            common_valid_pixels=count,common_valid_area_km2=count*pixel_area_km2(grid['crs'],grid['transform']),
            backscatter_scale_db=[float(low),float(high)],change_scale_db=[-limit,limit],before_after_statistics=pair['statistics'],
            settings={'filter':'3x3 mask-aware mean in linear power then 10*log10','mask':'joint HH/HV positive finite per-date mask; all-date joint mask for temporal statistics',
                      'ratio_definition':'filtered HH_power / filtered HV_power; dimensionless; ratio_dB=HH_dB-HV_dB',
                      'noise_floor_correction':'none; noise diagnostics deferred to Phase 4','classification':'none; original HH water algorithm unchanged'},
            range_bytes_read_this_run=sum(s['range_bytes_read_this_run'] for s in sources),full_hdf5_downloaded=False,elapsed_seconds=time.monotonic()-start)
        data.update(grid=grid,report=report)
        base_tags=dict(product_ids=json.dumps([i['product_id'] for i in items]),acquisitions_utc=json.dumps([i['start_time_utc'] for i in items]),
                       preprocessing='joint per-date HH/HV valid mask; 3x3 linear mean before dB',interpretation='Descriptive scattering only; not flood or flooded-vegetation classification')
        for name,layer in (('HH','HHHH'),('HV','HVHV'),('ratio_db',None)):
            filename={'HH':'hh_db.tif','HV':'hv_db.tif','ratio_db':'hh_hv_ratio_db.tif'}[name]
            source_label = GROUP+'/'+layer if layer else 'derived:HH_dB-HV_dB'
            save_raster(out/filename,data[name],dates,grid,dict(**base_tags,source_layer=source_label,units='dB'))
        save_raster(out/'hh_hv_ratio_linear.tif',data['ratio'],dates,grid,dict(**base_tags,units='1',definition='filtered HH power divided by filtered HV power'))
        save_raster(out/'joint_valid.tif',data['valid'],dates,grid,base_tags,categorical=True)
        save_raster(out/'common_valid.tif',[common],['all_dates_both_polarizations_valid'],grid,base_tags,categorical=True)
        save_raster(out/'before_after_delta_db.tif',[pair['HH_delta'],pair['HV_delta'],pair['ratio_delta_db']],['HH_comparison_minus_selected_dB','HV_comparison_minus_selected_dB','delta_HH_minus_delta_HV_dB'],grid,dict(**base_tags,units='dB',dates=dates[0]+' / '+dates[1]))
        # NetCDF cube retains both measured raw power and separately named filtered bands.
        tr=grid['transform'];h,w=grid['shape']
        cube=xr.Dataset({
            'HHHH_linear_power':(('time','y','x'),hh_power.astype('float32')),'HVHV_linear_power':(('time','y','x'),hv_power.astype('float32')),
            'HH_filtered_db':(('time','y','x'),data['HH'].astype('float32')),'HV_filtered_db':(('time','y','x'),data['HV'].astype('float32')),
            'HH_HV_power_ratio':(('time','y','x'),data['ratio'].astype('float32')),'HH_HV_ratio_db':(('time','y','x'),data['ratio_db'].astype('float32')),
            'joint_valid':(('time','y','x'),data['valid'].astype('uint8'))},
            coords={'time':[np.datetime64(i['start_time_utc'].replace('+00:00','').replace('Z',''),'ns') for i in items],
                    'x':tr.c+(np.arange(w)+.5)*tr.a,'y':tr.f+(np.arange(h)+.5)*tr.e},
            attrs={**base_tags,'crs':grid['crs'].to_wkt(),'GeoTransform':' '.join(map(str,tr.to_gdal())), 'HH_source_layer':GROUP+'/HHHH','HV_source_layer':GROUP+'/HVHV'})
        for k in cube.data_vars:cube[k].attrs['units']='dB' if k.endswith('_db') else '1'
        cube.to_netcdf(out/'hh_hv_cube.nc',engine='h5netcdf',encoding={k:{'zlib':True,'complevel':4} for k in cube.data_vars})
        with xr.open_dataset(out/'hh_hv_cube.nc',engine='h5netcdf') as check:np.testing.assert_allclose(check.HV_filtered_db.values,data['HV'].astype('float32'),equal_nan=True)
        fig=draw_comparison(data,0,1);fig.savefig(out/'hh_hv_before_after_change.png',dpi=140);plt.close(fig)
        fig=draw_change_relation(pair);fig.savefig(out/'hh_vs_hv_change.png',dpi=150);plt.close(fig)
        fig,ax=plt.subplots(figsize=(10,3.5),layout='constrained')
        times=[datetime.fromisoformat(i['start_time_utc']) for i in items]
        for b,color in (('HH','#007f83'),('HV','#a04c83')):
            ax.plot(times,[r[b+'_median_db'] for r in measurements],'o-',color=color,label=b+' spatial median')
        ax.set_ylabel('Filtered gamma-0 (dB)');ax.set_xlabel('Acquisition UTC; connecting lines are visual guides');ax.legend();ax.grid(alpha=.2)
        fig.savefig(out/'hh_hv_temporal_statistics.png',dpi=150);plt.close(fig)
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('SUCCESS:',args.dates,'real HH/HV dates;',report['common_valid_area_km2'],'km² common valid area',flush=True)
        return 0
    except Exception as exc:
        detail=str(exc) if isinstance(exc,(RadarDataError,AccessCheckError)) else 'Sensitive exception text suppressed; stage and error type recorded.'
        failure=dict(status='blocked',stage=stage,error_type=type(exc).__name__,detail=detail,real_HV_dates_read=read_dates)
        (out/'blocker.json').write_text(json.dumps(failure,indent=2)+'\n');print(json.dumps(failure),flush=True);return 2


if __name__=='__main__':raise SystemExit(main())
