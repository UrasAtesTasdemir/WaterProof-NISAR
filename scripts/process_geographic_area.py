"""Real 5/10 km Louisiana windows; preserves all earlier results."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from shapely import wkt
from shapely.geometry import shape,box,mapping
from rasterio.warp import transform_geom
from src.nisar_data import open_frequency_a
from scripts.check_earthdata_access import available_token
from scripts.visualize_nisar import read_subset
from scripts.detect_water_change import save_raster
from src.water_change import mask_aware_mean,power_to_db,classify,class_areas

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--size-km',type=int,choices=[5,10],default=5);args=parser.parse_args()
 out=ROOT/'data/geographic_mapping'/f'{args.size_km}km';out.mkdir(parents=True,exist_ok=True)
 m=json.loads((ROOT/'data/nisar_manifest.json').read_text());old=wkt.loads(m['aoi_wkt'])
 projected=shape(transform_geom('EPSG:4326','EPSG:32615',mapping(old)));cx,cy=projected.centroid.coords[0];half=args.size_km*500
 requested=box(cx-half,cy-half,cx+half,cy+half)
 footprints=[]
 for date in ('2026-06-21','2026-07-03'):
  j=json.loads((ROOT/f'data/nisar_search_{date}.geojson').read_text())
  footprints.append(shape(transform_geom('EPSG:4326','EPSG:32615',j['features'][0]['geometry'])))
 overlap=footprints[0].intersection(footprints[1]);fraction=requested.intersection(overlap).area/requested.area
 if fraction<.999:raise ValueError('Requested rectangle not fully covered by both catalog footprints; reduce size.')
 aoi=shape(transform_geom('EPSG:32615','EPSG:4326',mapping(requested)))
 start=time.monotonic();loaded=[];metadata=[]
 for item in m['observations']:
  print('Opening real HHHH',item['start_time_utc'],flush=True)
  with open_frequency_a(item,available_token()) as (ds,stats):power,db,crs,tr,info=read_subset(ds,aoi)
  grid={'crs':crs,'transform':tr,'shape':power.shape}
  if loaded and grid!=loaded[0][1]:raise ValueError('Expanded radar grids differ.')
  loaded.append((power,grid));metadata.append({**info,**stats,'product_id':item['product_id'],'acquisition_utc':item['start_time_utc']})
  print('Read MiB',stats['range_bytes_read']/2**20,flush=True)
 b,a=loaded[0][0],loaded[1][0];common=np.isfinite(b)&(b>0)&np.isfinite(a)&(a>0)
 if not common.any():raise ValueError('No common valid pixels.')
 grid=loaded[0][1];bf=mask_aware_mean(b,common,3);af=mask_aware_mean(a,common,3);bdb,adb=power_to_db(bf),power_to_db(af)
 classes,delta=classify(bdb,adb,common,-16,3);areas=class_areas(classes,crs,tr)
 tags={'source_before':m['observations'][0]['product_id'],'source_after':m['observations'][1]['product_id'],'dates':'2026-06-21 / 2026-07-03','polarization':'frequencyA HH / HHHH','settings':'linear 3x3 mask-aware mean, water<=-16dB, absolute delta>=3dB; no singleton suppression','interpretation':'Unvalidated candidate surface-water changes'}
 save_raster(out/'radar_power.tif',[b,a],['before_linear_HHHH','after_linear_HHHH'],grid,tags)
 save_raster(out/'filtered_backscatter.tif',[bdb,adb,delta],['before_dB','after_dB','after_minus_before_dB'],grid,tags)
 save_raster(out/'classes.tif',[classes],['candidate_water_classes_0_unknown_1_persistent_2_expansion_3_recession_4_other'],grid,tags,categorical=True)
 save_raster(out/'common_valid.tif',[common],['common_valid_mask'],grid,tags,categorical=True)
 info={'status':'success','requested_size_km':args.size_km,'requested_projected_bounds':list(requested.bounds),'requested_aoi_geojson':mapping(aoi),'requested_area_km2':requested.area/1e6,'catalog_overlap_coverage_fraction':min(1,fraction),'crs':str(crs),'resolution_m':[10,10],'transform':list(tr)[:6],'shape':list(b.shape),'observations':metadata,'settings':tags,'areas':areas,'valid_comparison_area_km2':int(common.sum())*.0001,'elapsed_seconds':time.monotonic()-start,'full_HDF5_downloaded':False}
 (out/'results.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps({k:info[k] for k in ('requested_size_km','shape','valid_comparison_area_km2','elapsed_seconds')},indent=2))
if __name__=='__main__':main()
