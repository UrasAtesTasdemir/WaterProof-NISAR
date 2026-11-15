"""Small-window feasibility research only. Never modifies Louisiana or plots a new map."""
from pathlib import Path
from datetime import datetime
import json,csv,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
import numpy as np
from shapely import wkt
from shapely.geometry import shape
from rasterio.warp import transform_geom
import rasterio
import scripts.inspect_water_references as reader
from scripts.check_earthdata_access import available_token

def time(s):return datetime.fromisoformat(s.replace('Z','+00:00'))

def main():
 aoi=wkt.loads(json.loads((OUT/'aoi.json').read_text())['aoi_wkt'])
 target=shape(transform_geom('EPSG:4326','EPSG:32614',aoi.__geo_interface__))
 raw=json.loads((OUT/'nisar_catalog.json').read_text())['results']['features'];inventory=[]
 for f in sorted(raw,key=lambda f:f['properties']['startTime']):
  p=f['properties'];g=shape(transform_geom('EPSG:4326','EPSG:32614',f['geometry']));name=p['fileID'].split('_')
  inventory.append({'product_id':p['fileID'],'start_utc':p['startTime'],'stop_utc':p['stopTime'],'polarization_A':p['mainBandPolarization'],'polarization_B':p.get('sideBandPolarization'),'track':p['pathNumber'],'frame':p['frameNumber'],'direction':p['flightDirection'],'bandwidth':p['rangeBandwidth'],'configuration':name[8:11],'crid':p['crid'],'collection':p['collectionName'],'aoi_footprint_coverage_fraction':g.intersection(target).area/target.area,'catalog_url':p['url']})
 (OUT/'nisar_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
 entries=json.loads((OUT/'OPERA_L3_DSWX-HLS_V1.json').read_text())['response']['feed']['entry']
 # Inspect closest optical sensing time and a second nearest for each useful
 # July NISAR acquisition, plus low-cloud July9/20 alternatives. Not tuned to agreement.
 selected={}
 for n in inventory:
  if n['start_utc'][:10]>'2026-07-23':continue
  for e in sorted(entries,key=lambda e:abs((time(e['time_start'])-time(n['start_utc'])).total_seconds()))[:2]:selected[e['title']]=e
 for e in entries:
  if e['time_start'].startswith(('2026-07-09','2026-07-20')):selected[e['title']]=e
 reader.OUT=OUT;results=[]
 for e in selected.values():
  r=reader.inspect(e,available_token(),aoi)
  if r['status']=='aoi_inspected':
   r['valid_fraction']=r['usable_water_or_nonwater_pixels']/r['aoi_pixel_centers']
   with rasterio.open(ROOT/r['subset_path']) as src:r.update(crs=str(src.crs),resolution_m=list(src.res),bounds=list(src.bounds))
  r['time_difference_hours']={n['product_id']:(time(e['time_start'])-time(n['start_utc'])).total_seconds()/3600 for n in inventory}
  results.append(r);(OUT/'reference_windows.json').write_text(json.dumps(results,indent=2)+'\n')
  print(e['title'],r['status'],r.get('valid_fraction'),flush=True)
 print('NISAR inventory',[(n['start_utc'],n['track'],n['aoi_footprint_coverage_fraction']) for n in inventory])
if __name__=='__main__':main()
