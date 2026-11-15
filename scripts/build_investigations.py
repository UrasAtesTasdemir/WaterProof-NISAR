"""Offline real HH/HV investigation regions. Existing outputs are read-only."""
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import numpy as np
import rasterio
import xarray as xr
from shapely.geometry import mapping,shape
from shapely.ops import unary_union
from rasterio.features import shapes
from rasterio.warp import transform_geom
from src.polarization import load_polarization
from src.water_change import mask_aware_mean,power_to_db
from src.investigation import DIRECTORY,DEFAULTS,LIMITATIONS,event_components,describe_proposals,rank_regions,region_record,markdown_report


def main():
    out=DIRECTORY;out.mkdir(exist_ok=True)
    if (out/'results.json').exists():print('Completed investigation outputs left unchanged.');return
    data=load_polarization();common=data['common'];grid=data['grid']
    if len(data['HH'])!=6:raise ValueError('Six real HH/HV observations required.')
    proposals,scene,eligible=event_components(data['HH'],common)
    proposals=describe_proposals(proposals,data['HH'],data['HV'],scene)
    selected=rank_regions(proposals)
    with xr.open_dataset(data['directory']/'hh_hv_cube.nc',engine='h5netcdf') as ds:raw=ds.HHHH_linear_power.values
    scenario_masks=[]
    for size in (1,3,5):
        db=np.stack([power_to_db(mask_aware_mean(p,common,size)) for p in raw])
        for floor in (2.5,3.,3.5):
            _,_,mask=event_components(db,common,floor_db=floor)
            scenario_masks.append((size,floor,mask))
    diagnostics=json.loads((ROOT/'data/scientific_diagnostics/results.json').read_text())
    if diagnostics['common_valid_pixels']!=int(common.sum()):raise ValueError('Diagnostic support differs from the investigation grid.')
    with rasterio.open(ROOT/'data/scientific_diagnostics/temporal_scaled_change.tif') as src:
        if src.transform!=grid['transform'] or src.crs!=grid['crs']:raise ValueError('Diagnostic raster grid mismatch.')
        score=src.read(1)
    regions=[];labels=np.zeros(common.shape,dtype='uint8')
    for rank,p in enumerate(selected,1):
        sensitivity=[dict(filter_size=size,magnitude_floor_db=floor,retained_pixels=int(mask.ravel()[p['indices']].sum())) for size,floor,mask in scenario_masks]
        record=region_record(p,rank,data,scene,sensitivity,{'score_gate':np.isfinite(score)&(np.abs(score)>=3)})
        regions.append(record);labels.ravel()[p['indices']]=rank
    footprint=unary_union([shape(g) for g,value in shapes(common.astype('uint8'),mask=common,transform=grid['transform']) if value==1])
    observed=data['report']['observations']
    report=dict(status='success' if regions else 'no_candidates',settings=DEFAULTS,
        observations=[{k:o[k] for k in ('date','acquisition_utc','product_id')} for o in observed],source_layers=data['report']['source_layers'],
        crs=str(grid['crs']),transform=list(grid['transform'])[:6],shape=list(grid['shape']),common_valid_pixels=int(common.sum()),
        common_valid_area_km2=data['report']['common_valid_area_km2'],common_footprint=transform_geom(grid['crs'],'EPSG:4326',mapping(footprint.segmentize(10))),
        eligible_proposals=len(proposals),regions=regions,scene_interval_context=scene,limitations=LIMITATIONS,
        ranking_rule='Descending recurrence count, pixel area, maximum absolute regional median HH change; date/location ties. Greedy non-overlap and >=100m centroid separation. No weighted or calibrated score.',
        no_normalization=True,benchmark_used_for_tuning=False,new_datasets_downloaded=False,
        diagnostics_context={'original_pair_HH_median_delta_db':next(p['median'] for p in diagnostics['pairwise_distributions'] if p['band']=='HH' and p['selected']==observed[0]['date'] and p['comparison']==observed[1]['date']),
            'original_pair_HV_median_delta_db':next(p['median'] for p in diagnostics['pairwise_distributions'] if p['band']=='HV' and p['selected']==observed[0]['date'] and p['comparison']==observed[1]['date']),
            'original_pair_baseline_expansion_km2':diagnostics['comparison']['baseline_expansion_km2'],
            'description':'Existing Phase4 scene distributions, strong setting sensitivity and unresolved HV calibrated noise floor remain relevant; diagnostic gate overlap is not validation.'},
        source_fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (data['directory']/'hh_db.tif',data['directory']/'hv_db.tif',data['directory']/'hh_hv_cube.nc',ROOT/'data/scientific_diagnostics/results.json')})
    from scripts.detect_water_change import save_raster
    save_raster(out/'region_labels.tif',[np.where(common,labels,np.nan)],['0_no_selected_region_1_to_5_heuristic_order'],grid,
        {'source_layers':json.dumps(report['source_layers']),'interpretation':'Investigation regions only; numbers are heuristic order, NOT risk/confidence'},categorical=False)
    geojson={'type':'FeatureCollection','features':[{'type':'Feature','geometry':r['geometry'],'properties':{'region_id':r['id'],'area_km2':r['area_km2'],'recurrence_intervals':r['recurrence_count'],'interpretation':'Unvalidated radar-change investigation candidate'}} for r in regions]}
    (out/'regions.geojson').write_text(json.dumps(geojson,indent=2)+'\n')
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    for r in regions:(out/f"region_{r['id']}_investigation.md").write_text(markdown_report(r,report))
    print(json.dumps({'regions':len(regions),'proposals':len(proposals),'summary':[{'id':r['id'],'area_km2':r['area_km2'],'recurrence':r['recurrence_count'],'max_median_HH_change_db':r['maximum_absolute_median_HH_change_db'],'coordinates':[r['representative_longitude'],r['representative_latitude']]} for r in regions]},indent=2))


if __name__=='__main__':main()
