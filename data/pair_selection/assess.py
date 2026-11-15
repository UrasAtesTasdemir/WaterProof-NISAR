"""Read small reference windows and rank dates without changing the app."""
from pathlib import Path
from datetime import datetime
from itertools import combinations,product
import json,sys,hashlib,csv
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import transform_geom
from shapely import wkt
from shapely.geometry import mapping,shape
from src.reference_validation import align_categories
from scripts.check_earthdata_access import available_token
import scripts.inspect_water_references as reader
DATES=('2026-06-21','2026-07-03','2026-07-15','2026-07-27','2026-08-20','2026-09-01')
def dt(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
def main():
 aoi=wkt.loads(json.loads((ROOT/'data/nisar_manifest.json').read_text())['aoi_wkt']);reader.OUT=OUT
 features=json.loads((OUT/'nisar_catalog.json').read_text())['results']['features'];ns=[]
 projected=shape(transform_geom('EPSG:4326','EPSG:32615',mapping(aoi)))
 for f in features:
  p=f['properties']
  if p['startTime'][:10] not in DATES or p['pathNumber']!=105:continue
  g=shape(transform_geom('EPSG:4326','EPSG:32615',f['geometry']))
  ns.append({'date':p['startTime'][:10],'product_id':p['fileID'],'acquisition_utc':p['startTime'],'track':p['pathNumber'],'frame':p['frameNumber'],'direction':p['flightDirection'],'polarization':p['mainBandPolarization'],'bandwidth':p['rangeBandwidth'],'crid':p['crid'],'aoi_footprint_coverage_fraction':min(1,g.intersection(projected).area/projected.area),'url':p['url']})
 ns.sort(key=lambda x:x['date']);assert len(ns)==6
 (OUT/'nisar_inventory.json').write_text(json.dumps(ns,indent=2)+'\n')
 references=[];grids={};masks={};water_masks={};seen={}
 for n in ns:
  for collection in ('OPERA_L3_DSWX-S1_V1','OPERA_L3_DSWX-HLS_V1'):
   raw=json.loads((OUT/(collection+'_'+n['date']+'.json')).read_text());es=raw['response']['feed']['entry']
   assert len(es)<100
   # Do not double-count processing revisions of one sensing time.
   latest={}
   for e in sorted(es,key=lambda e:e['title']):latest[e['time_start']]=e
   for e in latest.values():
    key=e['title'];path=None
    if key not in seen:
     for folder in ('pair_selection','validation','scientific_quality_check'):
      candidate=ROOT/'data'/folder/(key+'_aoi_WTR.tif')
      if candidate.exists():path=candidate;break
     access='reused prior real AOI window'
     if path is None:
      result=reader.inspect(e,available_token(),aoi);access='small HTTPS AOI range read'
      if result['status']!='aoi_inspected':
       seen[key]={'product_id':key,'status':result['status'],'error_type':result.get('error_type')};references.append({**seen[key],'nisar_date':n['date'],'collection':collection});continue
      path=ROOT/result['subset_path']
     with rasterio.open(path) as ds:
      values=ds.read(1);inside=geometry_mask([transform_geom('EPSG:4326',ds.crs,mapping(aoi))],ds.shape,ds.transform,invert=True)
      kind='S1' if 'DSWX-S1' in collection else 'HLS'
      valid=inside&np.isin(values,[0,1,3] if kind=='S1' else [0,1,2]);counts={str(int(v)):int(c) for v,c in zip(*np.unique(values[inside],return_counts=True))}
      grids[key]={'crs':ds.crs,'transform':ds.transform,'shape':ds.shape};masks[key]=valid
      water_masks[key]=inside&np.isin(values,[1,3] if kind=='S1' else [1,2])
      seen[key]={'product_id':key,'status':'inspected','reference_utc':e['time_start'],'collection':collection,'subset_path':str(path.relative_to(ROOT)),'access':access,'crs':str(ds.crs),'resolution_m':list(ds.res),'aoi_pixel_centers':int(inside.sum()),'valid_pixels':int(valid.sum()),'valid_fraction':float(valid.sum()/inside.sum()),'class_counts':counts,'tile_cloud_cover_metadata':e.get('cloud_cover'),'validity_definition':'S1 codes0/1/3 or HLS0/1/2; all other codes excluded. Unknown is not nonwater.'}
     print(key,seen[key]['valid_fraction'],flush=True)
    if seen[key]['status']=='inspected':
     hours=(dt(seen[key]['reference_utc'])-dt(n['acquisition_utc'])).total_seconds()/3600
     references.append({**seen[key],'nisar_date':n['date'],'time_offset_hours':hours,'eligible_presence':abs(hours)<=24 and seen[key]['valid_fraction']>=.8})
    (OUT/'reference_inventory.json').write_text(json.dumps(references,indent=2)+'\n')
 pairs=[]
 for before,after in combinations(ns,2):
  if not all(before[k]==after[k] for k in ('track','frame','direction','polarization','bandwidth','crid')):continue
  options_b=[r for r in references if r.get('nisar_date')==before['date'] and r.get('status')=='inspected']
  options_a=[r for r in references if r.get('nisar_date')==after['date'] and r.get('status')=='inspected']
  for b,a in product(options_b,options_a):
   keyb,keya=b['product_id'],a['product_id'];mapped=align_categories(masks[keya].astype('uint8'),grids[keya],grids[keyb])==1
   denominator=b['aoi_pixel_centers'];overlap=int((masks[keyb]&mapped).sum())/denominator
   pair={'before':before,'after':after,'before_reference':b,'after_reference':a,'common_reference_valid_fraction':overlap,'presence_dates_eligible':int(b['eligible_presence'])+int(a['eligible_presence']),'max_abs_time_offset_hours':max(abs(b['time_offset_hours']),abs(a['time_offset_hours'])),'nisar_interval_days':(dt(after['acquisition_utc'])-dt(before['acquisition_utc'])).total_seconds()/86400}
   pair['eligible_change']=pair['presence_dates_eligible']==2 and overlap>=.8 and keyb!=keya
   pair['within24hours_both']=abs(b['time_offset_hours'])<=24 and abs(a['time_offset_hours'])<=24
   shared=masks[keyb]&mapped
   mapped_water=align_categories(water_masks[keya].astype('uint8'),grids[keya],grids[keyb])==1
   pair['reference_water_cells_in_common']=[int((shared&water_masks[keyb]).sum()),int((shared&mapped_water).sum())]
   # All-nonwater windows cannot test water discrimination meaningfully.
   if min(pair['reference_water_cells_in_common'])==0:continue
   pairs.append(pair)
 # Rank by predeclared policy, not agreement or candidate-water area: eligible
 # change first, then number of eligible dates, then shared support, then timing.
 score=lambda p:(-int(p['eligible_change']),-int(p['within24hours_both']),-p['common_reference_valid_fraction'],p['max_abs_time_offset_hours'],p['nisar_interval_days'])
 pairs.sort(key=score);ranked=[];date_pairs=set()
 for p in pairs:
  key=(p['before']['date'],p['after']['date'])
  if key in date_pairs:continue
  ranked.append(p);date_pairs.add(key)
  if len(ranked)==3:break
 original=json.loads((OUT/'preserved_hashes.json').read_text())
 for path,h in original.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
 report={'criteria':{'max_abs_reference_time_gap_hours':24,'min_each_and_common_valid_fraction':.8,'ranking':'Require compatible radar and nonzero reference-water support on both dates; rank change eligibility first, then both reference gaps <=24h, then larger common support, smaller max time gap, shorter NISAR interval. Rejected pairs remain rejected.','note':'Conservative full-AOI feasibility guardrails, not universal validation standards. Partial-area presence evaluation can still be useful but is not full-AOI or robust change validation. No agreement metrics used to rank.'},'ranked_at_most_three_pairs':ranked,'decision':'GO for prospective reference-product water classification agreement' if ranked and ranked[0]['eligible_change'] else 'NO-GO for paired independent validation','production_unchanged':True,'new_nisar_products_downloaded':False,'limitations':['Reference products are not ground truth; no flood event inferred.','30m reference pixels mix 10m canal/surface features.','S1 inundated vegetation and HLS partial water differ from open-water low-HH detection; class definitions must be separated.','Hours of timing difference can matter in tidal/drainage landscapes.','Only the original June21/July3 radar subsets are cached; later NISAR validity remains to be checked with small windows.']}
 (OUT/'pair_ranking.json').write_text(json.dumps(report,indent=2)+'\n')
 for p in ranked:print('RANK',p['before']['date'],p['after']['date'],p['presence_dates_eligible'],p['common_reference_valid_fraction'],p['max_abs_time_offset_hours'],p['eligible_change'])
 print(report['decision'])
if __name__=='__main__':main()
