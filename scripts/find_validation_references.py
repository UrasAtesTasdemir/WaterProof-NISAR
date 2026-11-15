"""Bounded reference discovery/pixel inspection without large downloads."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import requests
from shapely import wkt
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import transform_geom
from shapely.geometry import mapping
import numpy as np
import scripts.inspect_water_references as reader
from scripts.check_earthdata_access import available_token
OUT=ROOT/'data/validation'

def main():
 OUT.mkdir(exist_ok=True);reader.OUT=OUT
 aoi=wkt.loads(json.loads((ROOT/'data/nisar_manifest.json').read_text())['aoi_wkt'])
 results=[]
 for collection in ('OPERA_L3_DSWX-S1_V1','OPERA_L3_DSWX-HLS_V1'):
  path=OUT/(collection+'.json')
  if not path.exists():
   q={'short_name':collection,'provider':'POCLOUD','bounding_box':','.join(map(str,aoi.bounds)),'temporal':'2026-06-15T00:00:00Z,2026-07-10T00:00:00Z','page_size':200}
   r=requests.get('https://cmr.earthdata.nasa.gov/search/granules.json',params=q,timeout=40);r.raise_for_status()
   path.write_text(json.dumps({'query':q,'hits':r.headers.get('CMR-Hits'),'response':r.json()},indent=2))
  data=json.loads(path.read_text());entries=data['response']['feed']['entry']
  if len(entries)>=200:raise ValueError('Discovery truncated; refine search.')
  if 'S1' in collection:chosen=[e for e in entries if e['time_start'].startswith(('2026-06-21','2026-06-28'))]
  else:
   unique={}
   for e in sorted(entries,key=lambda x:x['title']):
    if '2026-06-30'<=e['time_start'][:10]<='2026-07-06':unique[e['time_start']]=e
   chosen=list(unique.values())
  for e in chosen:
   cached=OUT/(e['title']+'_aoi_WTR.tif')
   # Earlier valid window reads may exist even if report generation failed.
   if cached.exists():
    with rasterio.open(cached) as ds:
     values=ds.read(1);good=geometry_mask([transform_geom('EPSG:4326',ds.crs,mapping(aoi))],values.shape,ds.transform,invert=True)
     counts={str(int(v)):int(n) for v,n in zip(*np.unique(values[good],return_counts=True))}
     resolution=list(ds.res);bounds=list(ds.bounds);crs=str(ds.crs)
    item={'product_id':e['title'],'acquisition_utc':e['time_start'],'status':'aoi_inspected','subset_path':str(cached.relative_to(ROOT)),'aoi_class_counts':counts,'aoi_pixel_centers':int(good.sum()),'spatial_resolution_m':resolution,'projected_bounds':bounds,'crs':crs,'access':'small HTTPS range-read subset cached locally; full tile not downloaded'}
   else:item=reader.inspect(e,available_token(),aoi)
   item['collection']=collection
   if item['status']=='aoi_inspected':
    if 'S1' in collection:
     item['class_codes']={'0':'not water','1':'open water','3':'inundated vegetation','250':'HAND','251':'layover/shadow','254':'ocean','255':'no data'};valid=(0,1,3)
     with rasterio.open(ROOT/item['subset_path'],'r+') as ds:ds.update_tags(interpretation='Independent Sentinel-1 product; suitability check, not flood ground truth')
    else:valid=(0,1,2)
    item['valid_reference_pixels']=sum(item['aoi_class_counts'].get(str(c),0) for c in valid)
   results.append(item);print(json.dumps(item),flush=True)
   (OUT/'reference_access.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':main()
