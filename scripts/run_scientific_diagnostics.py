"""Small reproducible offline Phase4 study. No production algorithm writes."""
import json
import os
from pathlib import Path
import sys
from itertools import combinations

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import numpy as np
import rasterio
import xarray as xr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from rasterio.features import rasterize
from rasterio.warp import transform_geom
from rasterio.transform import xy,array_bounds
from scipy.ndimage import distance_transform_edt
from src.polarization import load_polarization
from src.scientific_diagnostics import DIRECTORY,robust_statistics,temporal_scaled_change,local_texture,select_stable_tiles
from src.water_change import classify,mask_aware_mean,power_to_db,pixel_area_km2
from scripts.detect_water_change import save_raster


def histogram(values,edges):
    v=np.asarray(values);v=v[np.isfinite(v)];return dict(edges=edges.tolist(),counts=np.histogram(v,edges)[0].tolist(),below=int((v<edges[0]).sum()),above=int((v>edges[-1]).sum()))


def main():
    out=DIRECTORY;out.mkdir(exist_ok=True)
    if (out/'results.json').exists():print('Completed diagnostics left unchanged.');return 0
    data=load_polarization();report=data['report'];grid=data['grid'];common=data['common'];cell=pixel_area_km2(grid['crs'],grid['transform'])
    if len(data['HH'])!=6:raise ValueError('Six real dates required for reference-scaled diagnostics.')
    dates=[o['date'] for o in report['observations']]
    with xr.open_dataset(data['directory']/'hh_hv_cube.nc',engine='h5netcdf') as ds:
        raw={'HH':ds.HHHH_linear_power.values,'HV':ds.HVHV_linear_power.values}
    temporal=[];pairs=[]
    for band in ('HH','HV'):
        for i,date in enumerate(dates):temporal.append(dict(band=band,date=date,**robust_statistics(data[band][i][common]),histogram=histogram(data[band][i][common],np.linspace(-35,10,91))))
        for first,second in combinations(range(6),2):
            delta=data[band][second]-data[band][first]
            pairs.append(dict(band=band,selected=dates[first],comparison=dates[second],**robust_statistics(delta[common]),histogram=histogram(delta[common],np.linspace(-15,15,121))))
    geometries=[]
    for layer in (6,9):
        for feature in json.loads((ROOT/f'data/scientific_quality_check/nhd_layer_{layer}.geojson').read_text())['features']:
            p=feature['properties'];kind=int(p.get('ftype',p.get('FTYPE',0)))
            if kind in (336,460):geometries.append(transform_geom('EPSG:4326',grid['crs'],feature['geometry']))
    if not geometries:raise ValueError('Cached historical waterway geometry missing; do not invent stable-land context.')
    mapped=rasterize([(g,1) for g in geometries],out_shape=grid['shape'],transform=grid['transform'],all_touched=True).astype(bool)
    distance=distance_transform_edt(~mapped,sampling=(10,10));far=distance>100
    stable,pool=select_stable_tiles(data['HH'],data['HV'],common,far)
    region_mask=np.full(grid['shape'],np.nan,dtype='float32');regions=[];texture=[]
    for index,tile in enumerate(stable,1):
        row,col,size=tile['row'],tile['column'],tile['size'];sl=np.s_[row:row+size,col:col+size]
        region_mask[sl]=index;cx,cy=xy(grid['transform'],row+size//2,col+size//2)
        region=dict(id=index,**tile,center_easting_m=cx,center_northing_m=cy,statistics=[])
        for band in ('HH','HV'):
            region[band+'_first_pair_change']=robust_statistics((data[band][1]-data[band][0])[sl])
            for i,date in enumerate(dates):
                region['statistics'].append(dict(band=band,date=date,**robust_statistics(data[band][i][sl])))
                looks=None
                q=out/f'numberOfLooks_{date}.tif'
                if q.exists():
                    with rasterio.open(q) as src:looks=src.read(1)[sl]
                raw_texture=local_texture(raw[band][i][sl],looks=looks)
                filtered_power=10**(data[band][i][sl]/10)
                filtered_texture=local_texture(filtered_power,filtered=True)
                texture.append(dict(region=index,band=band,date=date,raw=raw_texture,filtered_cv=filtered_texture['cv'],enl_interpretation='Conditional spatial moment estimate only if qualified; never pure sensor/thermal noise.'))
        regions.append(region)
    baseline,delta=classify(data['HH'][0],data['HH'][1],common,-16,3)
    crosses,_=classify(data['HH'][0],data['HH'][1],common,-16,None)
    scaled=temporal_scaled_change(data['HH']);hv_scaled=temporal_scaled_change(data['HV'])
    alt_exp=(crosses==2)&scaled['gate'];alt_rec=(crosses==3)&scaled['gate']
    def area(mask):return int(np.count_nonzero(mask))*cell
    baseline_exp=baseline==2;baseline_rec=baseline==3
    comparison=dict(baseline_expansion_km2=area(baseline_exp),baseline_recession_km2=area(baseline_rec),
        alternative_expansion_km2=area(alt_exp),alternative_recession_km2=area(alt_rec),comparison_area_km2=area(common&scaled['valid']),
        baseline_expansion_also_alternative_pixels=int((baseline_exp&alt_exp).sum()),baseline_recession_also_alternative_pixels=int((baseline_rec&alt_rec).sum()),
        baseline_change_pixels_without_four_reference_observations=int(((baseline_exp|baseline_rec)&~scaled['valid']).sum()),
        effective_gate_db=robust_statistics(3*scaled['scale_db'][common]),score=robust_statistics(scaled['score'][common]),
        HH_score_gate_pixels=int((scaled['gate']&common).sum()),HV_score_gate_pixels=int((hv_scaled['gate']&common).sum()))
    sensitivity=[];exp_count=np.zeros(grid['shape'],dtype='uint8');rec_count=np.zeros_like(exp_count)
    for size in (1,3,5):
        db=np.stack([power_to_db(mask_aware_mean(p,common,size)) for p in raw['HH'][:2]])
        for threshold in (-14,-16,-18,-20):
            classes,_=classify(db[0],db[1],common,threshold,3)
            exp=classes==2;rec=classes==3;exp_count+=exp;rec_count+=rec
            union=(exp|baseline_exp).sum()
            sensitivity.append(dict(filter_size=size,water_threshold_db=threshold,min_change_db=3,expansion_pixels=int(exp.sum()),recession_pixels=int(rec.sum()),
                expansion_km2=area(exp),recession_km2=area(rec),baseline_expansion_Jaccard=float((exp&baseline_exp).sum()/union) if union else None))
    stability=dict(scenarios=len(sensitivity),expansion_in_any_km2=area(exp_count>0),expansion_in_all_km2=area(exp_count==len(sensitivity)),
        recession_in_any_km2=area(rec_count>0),recession_in_all_km2=area(rec_count==len(sensitivity)),
        baseline_expansion_in_all_pixels=int((baseline_exp&(exp_count==len(sensitivity))).sum()),
        baseline_expansion_within_30m_waterway_pixels=int((baseline_exp&(distance<=30)).sum()),
        any_expansion_within_30m_waterway_pixels=int(((exp_count>0)&(distance<=30)).sum()))
    tags=dict(source_layer='NISAR frequencyA HHHH/HVHV',units='diagnostic only',source_ids=json.dumps([o['product_id'] for o in report['observations']]),interpretation='Exploratory reliability study; no production classification replaced')
    save_raster(out/'temporal_scaled_change.tif',[scaled['score'],hv_scaled['score'],scaled['scale_db']],['HH_dimensionless_score','HV_dimensionless_score','HH_reference_scale_dB'],grid,tags)
    with rasterio.open(out/'temporal_scaled_change.tif','r+') as dst:
        for index,unit in enumerate(('1','1','dB'),1):dst.set_band_unit(index,unit)
        dst.update_tags(units='Bands 1/2: dimensionless; band 3: dB',source_layers=json.dumps(report['source_layers']))
    save_raster(out/'sensitivity_counts.tif',[np.where(common,exp_count,np.nan),np.where(common,rec_count,np.nan)],['expansion_candidate_count_0_to_12','recession_candidate_count_0_to_12'],grid,tags)
    save_raster(out/'candidate_stable_regions.tif',[region_mask],['selected_quiet_looking_reference_regions'],grid,tags)
    baseline_change=baseline_exp|baseline_rec;alt_change=alt_exp|alt_rec
    support=np.where(common,np.where(baseline_change&alt_change,2,np.where(baseline_change,3,1)),0).astype('uint8')
    save_raster(out/'baseline_alternative_overlap.tif',[support],['0_unknown_1_neither_2_both_3_baseline_only'],grid,tags,categorical=True)
    result=dict(status='success',observations=[{'date':o['date'],'acquisition_utc':o['acquisition_utc'],'product_id':o['product_id']} for o in report['observations']],
        source_layers=report['source_layers'],crs=str(grid['crs']),transform=list(grid['transform'])[:6],shape=list(grid['shape']),
        common_valid_pixels=int(common.sum()),common_valid_area_km2=area(common),temporal_distributions=temporal,pairwise_distributions=pairs,
        candidate_stable_region_pool=pool,candidate_stable_regions=regions,local_texture=texture,comparison=comparison,sensitivity=sensitivity,stability=stability,
        alternative_settings={'formula':'delta_dB / max(1.4826022185*MAD(other four dates),1 dB)','reference_dates':dates[2:],'floor_db':1,'cutoff_dimensionless':3,'minimum_finite_reference_dates':4,
          'interpretation':'Descriptive background-temporal-scaled change; not probability or significance; floor guarantees effective gate>=3dB, hence subsets do not imply improved accuracy.'},
        baseline_settings={'water_threshold_db':-16,'minimum_absolute_change_db':3,'linear_filter_size':3,'production_algorithm_modified':False},
        independent_validation='Unavailable; no NISAR water/flood accuracy claim.',scene_normalization_applied=False,benchmark_used_for_tuning=False)
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    # Standalone figures from actual calculated summaries and spatial outputs.
    fig,ax=plt.subplots(figsize=(10,4),layout='constrained')
    for band,color in (('HH','#007f83'),('HV','#a04c83')):
        rows=[r for r in temporal if r['band']==band]
        ax.errorbar(dates,[r['median'] for r in rows],yerr=[[r['median']-r['p25'] for r in rows],[r['p75']-r['median'] for r in rows]],fmt='o',color=color,label=band+' spatial median/IQR')
    ax.legend();ax.set_ylabel('Filtered gamma-0 (dB)');ax.set_xlabel('Acquisition date (UTC; not equal time steps)');fig.savefig(out/'temporal_distributions.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    for band,color in (('HH','#007f83'),('HV','#a04c83')):
        row=next(r for r in pairs if r['band']==band and r['selected']==dates[0] and r['comparison']==dates[1]);h=row['histogram'];edges=np.array(h['edges'])
        ax.stairs(h['counts'],edges,label=f"{band}: median {row['median']:.3f} dB",color=color)
    ax.axvline(-3,color='gray',linestyle='--');ax.axvline(3,color='gray',linestyle='--');ax.legend();ax.set_xlabel('July3 minus June21 (dB)');ax.set_ylabel('Pixels per bin');fig.savefig(out/'original_pair_histograms.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    for size in (1,3,5):
        rows=sorted([r for r in sensitivity if r['filter_size']==size],key=lambda r:r['water_threshold_db'])
        ax.plot([r['water_threshold_db'] for r in rows],[r['expansion_km2'] for r in rows],'o-',label=f'{size}×{size} linear mean')
    ax.legend();ax.set_xlabel('Exploratory HH water threshold (dB)');ax.set_ylabel('Expansion candidate km²');fig.savefig(out/'sensitivity.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
    west,south,east,north=array_bounds(*grid['shape'],grid['transform'])
    for ax,array,title in zip(axes,[np.where(common,exp_count,np.nan),np.where(common,scaled['score'],np.nan)],['Expansion occurrence across 12 settings','Exploratory temporal-scaled HH change']):
        im=ax.imshow(array,extent=(west,east,south,north),origin='upper',cmap='viridis' if 'occurrence' in title else 'RdBu_r');ax.set_title(title);fig.colorbar(im,ax=ax,shrink=.7)
        ax.ticklabel_format(style='plain',useOffset=False)
    fig.savefig(out/'spatial_stability.png',dpi=150);plt.close(fig)
    print(json.dumps({'comparison':comparison,'stable_regions':len(regions),'qualified_ENL_estimates':sum(t['raw']['qualified'] for t in texture),'stability':stability},indent=2))


def save_stability_families():
    """Supplement broad-range counts with two prespecified, interpretable families."""
    out=DIRECTORY;path=out/'stability_families.json'
    if path.exists():return
    data=load_polarization();common=data['common'];grid=data['grid'];cell=pixel_area_km2(grid['crs'],grid['transform'])
    with xr.open_dataset(data['directory']/'hh_hv_cube.nc',engine='h5netcdf') as ds:power=ds.HHHH_linear_power.values[:2]
    masks={}
    for size in (1,3,5):
        db=[power_to_db(mask_aware_mean(p,common,size)) for p in power]
        for threshold in (-14,-16,-18):
            classes,_=classify(*db,common,threshold,3);masks[size,threshold]=(classes==2,classes==3)
    families=[];rasters=[]
    for name,settings in [('filter_sizes_at_minus16',[(s,-16) for s in (1,3,5)]),('thresholds_at_filter3',[(3,t) for t in (-14,-16,-18)])]:
        exp=np.logical_and.reduce([masks[k][0] for k in settings]);rec=np.logical_and.reduce([masks[k][1] for k in settings])
        families.append(dict(name=name,settings=settings,expansion_pixels=int(exp.sum()),recession_pixels=int(rec.sum()),expansion_km2=int(exp.sum())*cell,recession_km2=int(rec.sum())*cell))
        rasters.append(np.where(common,exp,np.nan))
    save_raster(out/'consistency_families.tif',rasters,['expansion_in_all_filter_sizes_at_minus16','expansion_in_all_minus14_minus16_minus18_at_filter3'],grid,{'interpretation':'Setting stability only; NOT validation or confidence'})
    path.write_text(json.dumps({'families':families,'interpretation':'Within-family consistency is sensitivity support, not independently confirmed water. All twelve settings also include minus20 and have an empty intersection.'},indent=2)+'\n')


if __name__=='__main__':
    main();save_stability_families()
