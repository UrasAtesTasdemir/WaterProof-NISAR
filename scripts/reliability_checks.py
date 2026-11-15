"""Small offline reliability scenarios; never apply a scene correction by default."""
import csv
from datetime import datetime,timezone
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.warp import transform_geom
from scipy.ndimage import distance_transform_edt,label
from src.dashboard_data import prepare_data,calculate
from scripts.detect_water_change import save_raster
OUT=ROOT/'data/reliability'

def fingerprints():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('subsets','water_change','scientific_quality_check') for p in (ROOT/'data'/folder).rglob('*') if p.is_file()}

def main():
    OUT.mkdir(exist_ok=True); original=fingerprints();d=prepare_data()
    baseline=calculate(d,-16,3);filtered=calculate(d,-16,3,True)
    median=float(np.median(baseline['delta'][d['valid']]))
    rows=[]
    for fraction in (0,.5,1):
        addition=-fraction*median
        scenario={**d,'after':d['after']+addition}
        r=calculate(scenario,-16,3)
        rows.append({'fraction_of_measured_median_removed':fraction,'hypothetical_after_offset_db':addition,'expansion_km2':r['expansion'],'recession_km2':r['recession'],'baseline_expansion_pixels_still_candidates':int(((baseline['classes']==2)&(r['classes']==2)).sum())})
    with (OUT/'darkening_sensitivity.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    geometries=[]
    for layer in (6,9):
        j=json.loads((ROOT/f'data/scientific_quality_check/nhd_layer_{layer}.geojson').read_text())
        for feat in j['features']:
            props=feat['properties'];kind=int(props.get('ftype',props.get('FTYPE')))
            if kind in (336,460):geometries.append(transform_geom('EPSG:4326',d['grid']['crs'],feat['geometry']))
    hydro=rasterize([(g,1) for g in geometries],out_shape=d['valid'].shape,transform=d['grid']['transform'],all_touched=True).astype(bool)
    near=distance_transform_edt(~hydro,sampling=(10,10))<=30
    split={}
    for name,r in (('default',baseline),('optional_singleton_suppression',filtered)):
        split[name]={}
        for code,labelname in ((2,'expansion'),(3,'recession')):
            mask=r['classes']==code
            split[name][labelname]={'within_30m_pixels':int((mask&near).sum()),'beyond_30m_pixels':int((mask&~near).sum()),'within_30m_km2':int((mask&near).sum())*d['pixel_area'],'beyond_30m_km2':int((mask&~near).sum())*d['pixel_area']}
    suppressed=(baseline['classes']!=filtered['classes'])
    coords=[]
    rr,cc=np.nonzero(suppressed&(baseline['classes']==2))
    for row,col in zip(rr,cc):
        coords.append({'row':int(row),'column':int(col),'before_db':float(d['before'][row,col]),'after_db':float(d['after'][row,col]),'delta_db':float(baseline['delta'][row,col]),'within_30m_mapped_waterway':bool(near[row,col])})
    with (OUT/'isolated_expansion_pixels.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(coords[0]));writer.writeheader();writer.writerows(coords)
    tags={'settings':'water=-16dB, minimum_change=3dB; optional singleton suppression; 8-connectivity; separately for expansion/recession','interpretation':'Size prior only; not improved accuracy or dry-land confirmation'}
    save_raster(OUT/'classes_optional_singleton_filter.tif',[filtered['classes']],['optional_size_filtered_classes'],d['grid'],tags,categorical=True)
    save_raster(OUT/'suppressed_singleton_mask.tif',[suppressed],['suppressed_change_candidate_1'],d['grid'],tags,categorical=True)
    context=np.where(baseline['classes']==2,np.where(near,1,2),0)
    save_raster(OUT/'expansion_waterway_context.tif',[context],['0_not_expansion_1_near_waterway_2_farther'],d['grid'],{'interpretation':'Historical proximity only; no detections removed'},categorical=True)
    def areas(r):return {k:r[k] for k in ('expansion','recession','net','valid_area','suppressed_pixels')}
    report={'created_at_utc':datetime.now(timezone.utc).isoformat(),'default':areas(baseline),'optional_singleton_filter':areas(filtered),
            'measured_median_delta_db':median,'darkening_scenarios':rows,
            'darkening_interpretation':'Offsets are counterfactual sensitivity scenarios applied to the actual after dB values, not sensor calibration or evidence that environmental change is bias. The -1.39 dB median alone is smaller than the 3 dB gate; local variation is needed. No offset is applied to defaults or dashboard.',
            'singleton_interpretation':'One 10m grid pixel = 100m²; removing singletons may remove real small water features. Persistent and unknown classes are untouched; suppressed changes become other valid surface.',
            'isolated_expansion_pixels':len(coords),'isolated_expansion_near_waterway_pixels':sum(p['within_30m_mapped_waterway'] for p in coords),
            'waterway_context':split,'waterway_rule':'Historical NHD ftype336/460 rasterized all_touched on original grid; within 30m approximate raster distance. Not flood validation; near-water detections are not automatically removed.',
            'independent_validation':'Unavailable: inspected HLS windows cloudy; bounded DSWx-S1 catalog search finds June21 candidate but no July3 +/-1 day counterpart. A catalog hit is not pixel validation; no paired confirmation.',
            'sources':d['sources'],'settings':{'water_db':-16,'min_change_db':3,'linear_filter_size':3,'component_connectivity':8,'singleton_filter_default':False},'preserved_original_hashes':original}
    assert original==fingerprints()
    assert np.array_equal(baseline['classes']==0,filtered['classes']==0)
    (OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    fig,ax=plt.subplots(figsize=(8,4),layout='constrained')
    ax.plot([r['hypothetical_after_offset_db'] for r in rows],[r['expansion_km2'] for r in rows],marker='o',label='Expansion candidate')
    ax.plot([r['hypothetical_after_offset_db'] for r in rows],[r['recession_km2'] for r in rows],marker='o',label='Recession candidate')
    ax.set_xlabel('Hypothetical offset added to AFTER backscatter (dB)');ax.set_ylabel('Candidate area (km²)');ax.legend()
    ax.set_title('Counterfactual sensitivity only — NOT a calibration correction')
    fig.savefig(OUT/'darkening_sensitivity.png',dpi=160);plt.close(fig)
    print(json.dumps({k:report[k] for k in ('default','optional_singleton_filter','measured_median_delta_db','darkening_scenarios','waterway_context')},indent=2))

if __name__=='__main__':main()
