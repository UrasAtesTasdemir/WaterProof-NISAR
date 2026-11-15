"""Evaluate reference suitability and stable-looking proxies without forced metrics."""
from datetime import datetime
import json,os,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.warp import reproject,transform_geom
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.transform import array_bounds
from shapely import wkt
from shapely.geometry import mapping
from src.dashboard_data import prepare_data
from src.reference_validation import align_categories,reference_valid,eligibility
OUT=ROOT/'data/validation'

def main():
 d=prepare_data();items=d['manifest']['observations'];refs=json.loads((OUT/'reference_access.json').read_text())
 # Preserve originals and their recorded fingerprints; all new data are isolated.
 original=json.loads((ROOT/'data/reliability/results.json').read_text())['preserved_original_hashes']
 for path,digest in original.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
 aoi=wkt.loads(d['manifest']['aoi_wkt']);inventory=[];loaded={}
 for ref in refs:
  if ref['status']!='aoi_inspected':continue
  with rasterio.open(ROOT/ref['subset_path']) as src:
   values=src.read(1);grid={'crs':src.crs,'transform':src.transform,'shape':src.shape}
   inside=geometry_mask([mapping(aoi)],src.shape,src.transform,invert=True) if src.crs.to_epsg()==4326 else None
   # Both reference and NISAR are projected; use original common mask projected
   # nearest to reference grid to define comparable AOI support.
   support=np.zeros(src.shape,dtype='uint8')
   reproject(d['valid'].astype('uint8'),support,src_transform=d['grid']['transform'],src_crs=d['grid']['crs'],dst_transform=src.transform,dst_crs=src.crs,resampling=Resampling.nearest)
  kind='S1' if 'DSWX-S1' in ref['collection'] else 'HLS'
  valid=reference_valid(values,kind)&(support==1);area=int((support==1).sum())
  fraction=int(valid.sum())/area if area else 0
  gaps={i['start_time_utc'][:10]:(datetime.fromisoformat(ref['acquisition_utc'].replace('Z','+00:00'))-datetime.fromisoformat(i['start_time_utc'])).total_seconds()/3600 for i in items}
  eligible={day:eligibility(hours,fraction) for day,hours in gaps.items()}
  record={**ref,'time_offset_hours_from_nisar':gaps,'common_reference_grid_aoi_pixels':area,'common_valid_pixels':int(valid.sum()),'valid_coverage_fraction':fraction,'common_valid_area_km2':int(valid.sum())*.0009,'eligible_by_date':eligible}
  inventory.append(record);loaded[ref['product_id']]=(values,grid)
 # Analyze stable-looking proxy areas from two independently classified reference
 # dates bracketing AFTER, not stable ground truth on NISAR dates.
 s1=next(r for r in inventory if 'DSWX-S1' in r['collection'] and r['acquisition_utc'].startswith('2026-06-28'))
 hls=next(r for r in inventory if r['acquisition_utc'].startswith('2026-07-05T16:55'))
 sv,grid=loaded[s1['product_id']];hv,hgrid=loaded[hls['product_id']]
 hv=align_categories(hv,hgrid,grid)
 def aggregate(db):
  power=np.where(d['valid'],10**(db/10),np.nan)
  dst=np.full(grid['shape'],np.nan)
  reproject(power,dst,src_transform=d['grid']['transform'],src_crs=d['grid']['crs'],src_nodata=np.nan,dst_transform=grid['transform'],dst_crs=grid['crs'],dst_nodata=np.nan,resampling=Resampling.average)
  return 10*np.log10(dst)
 b,a=aggregate(d['before']),aggregate(d['after']);delta=a-b
 inside=geometry_mask([transform_geom('EPSG:4326',grid['crs'],mapping(aoi))],grid['shape'],grid['transform'],invert=True)
 support=np.zeros(grid['shape'],dtype='float64')
 reproject(d['valid'].astype(float),support,src_transform=d['grid']['transform'],src_crs=d['grid']['crs'],dst_transform=grid['transform'],dst_crs=grid['crs'],resampling=Resampling.average)
 both=np.isfinite(b)&np.isfinite(a)&inside&(support>=.999)
 stable_land=both&(sv==0)&(hv==0)
 stable_open=both&(sv==1)&(hv==1)
 stats={}
 for name,mask in [('all_common_30m',both),('nonwater_in_both_later_references_proxy',stable_land),('open_water_in_both_later_references_proxy',stable_open)]:
  stats[name]={'pixels':int(mask.sum()),'median_delta_db':float(np.median(delta[mask])) if mask.any() else None,'p10_delta_db':float(np.percentile(delta[mask],10)) if mask.any() else None,'p90_delta_db':float(np.percentile(delta[mask],90)) if mask.any() else None}
 report={'reference_inventory':inventory,'eligibility_policy':'Exploratory conservative policy declared before metrics: <=24 hour absolute time offset AND >=80% common valid AOI coverage. Not a universal standard. Assess tides, mixed pixels and class definitions even when eligible.',
 'quantitative_validation_possible':any(any(x['eligible_by_date'].values()) for x in inventory),'agreement_metrics':None,'expansion_recession_agreement':None,
 'reason':'No inspected reference satisfies timing AND coverage requirements for either NISAR date. Do not compute misleading scores.',
 'darkening':{'original_10m_median_db':float(np.median((d['after']-d['before'])[d['valid']])),'reference_proxy_stats':stats,'proxy_reference_ids':[s1['product_id'],hls['product_id']],
 'limitations':'Nonwater/open-water agreement across June28 and July5 is only stable-looking proxy support, not proof of stability on June21/July3. Can reflect vegetation/moisture/wind, tidal hydrology, radiometry or registration. No cause separated or correction applied.',
 'radiometric_check':'Same NISAR track105 frame017 bandwidth4005 polarizationDHDH and processing CRID P05023 in cached manifest. Same grid; prior +/-2 pixel gradient test best at zero shift. Calibration gains/incidence angles/meteorology/tides not independently measured; subpixel residuals not excluded.'},
 'area_decision':{'A':'Current June21/July3 pair cannot be credibly validated as surface-water change with inspected references. Keep as explicitly unvalidated demo only.',
 'B':'Only two NISAR observations are cached; no alternate date pair exists among cached observations. Catalog dates beyond these are not processed observations.',
 'C':'Recommend metadata-vetted Guadalupe River near Kerrville, Texas, July2026 flood as one alternative pending approval; no new region processed or large datasets downloaded.'},'source_files_unchanged':True}
 assert not report['quantitative_validation_possible'], 'Suitable reference unexpectedly found: implement comparison before reporting blocked.'
 (OUT/'validation_results.json').write_text(json.dumps(report,indent=2)+'\n')
 # Show availability, never a deceptive cross-date disagreement map.
 fig,axes=plt.subplots(1,3,figsize=(15,4.5),layout='constrained')
 panels=[(np.where(d['valid'],d['before']<=-16,np.nan),d['grid'],'NISAR water candidates: June21, -16 dB'),
         (np.where(np.isin(sv,[0,1,3]),sv,np.nan),grid,'Independent S1 water classes: June28'),
         (np.full(grid['shape'],np.nan),grid,'Agreement: NOT EVALUATED\nNo compatible reference on June21/July3')]
 for ax,(array,g,title) in zip(axes,panels):
  west,south,east,north=array_bounds(*g['shape'],g['transform']);cmap=plt.get_cmap('Blues').copy();cmap.set_bad('#dddddd')
  ax.imshow(array,extent=(west,east,south,north),cmap=cmap,vmin=0,vmax=3 if 'classes' in title else 1,origin='upper',interpolation='nearest')
  ax.set_title(title,fontsize=9);ax.set_xlabel('Easting (m)');ax.ticklabel_format(useOffset=False,style='plain');ax.tick_params(labelsize=7)
 fig.suptitle('Reference availability only — different dates; no flood accuracy or temporal agreement inferred',fontsize=10)
 fig.savefig(OUT/'reference_availability.png',dpi=160);plt.close(fig)
 print(json.dumps({'quantitative_validation_possible':report['quantitative_validation_possible'],'darkening':report['darkening']},indent=2))
if __name__=='__main__':main()
