"""Offline adapters; scientific algorithms remain in water_change."""
import json
from pathlib import Path
import numpy as np
from scripts.detect_water_change import load_cached
from src.water_change import align_power, mask_aware_mean, power_to_db, classify, pixel_area_km2, suppress_single_pixel_changes
ROOT = Path(__file__).resolve().parents[1]

def input_signature():
    files = [ROOT/'data'/s for s in ('nisar_manifest.json','nisar_visualization_report.json','water_change/results.json')]
    for day in ('2026-06-21','2026-07-03'):
        files.extend(ROOT/'data/subsets'/f'nisar_hhhh_{day}.{ext}' for ext in ('tif','json'))
    quality=ROOT/'data/scientific_quality_check/quality_diagnostics.json'
    if quality.exists(): files.append(quality)
    return tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in files)

def prepare_data():
    manifest=json.loads((ROOT/'data/nisar_manifest.json').read_text())
    previous=json.loads((ROOT/'data/nisar_visualization_report.json').read_text())
    baseline=json.loads((ROOT/'data/water_change/results.json').read_text())
    items=sorted(manifest['observations'],key=lambda p:p['start_time_utc'])
    if [i['start_time_utc'][:10] for i in items]!=['2026-06-21','2026-07-03']:
        raise ValueError('Expected acquisition dates are missing.')
    b,bv,grid,bm=load_cached(items[0],previous)
    a,av,ag,am=load_cached(items[1],previous)
    for source in (bm,am):
        expected=next(s for s in baseline['sources'] if s['product_id']==source['product_id'])
        if source['sha256']!=expected['sha256']: raise ValueError('Cached source fingerprint changed.')
    a,av,corrected=align_power(a,av,ag,grid)
    common=bv&av
    if not common.any(): raise ValueError('No valid comparison pixels.')
    quality=ROOT/'data/scientific_quality_check/quality_diagnostics.json'
    return dict(before=power_to_db(mask_aware_mean(b,common,3)),after=power_to_db(mask_aware_mean(a,common,3)),valid=common,
                grid=grid,pixel_area=pixel_area_km2(grid['crs'],grid['transform']),manifest=manifest,sources=[bm,am],baseline=baseline,
                quality=json.loads(quality.read_text()) if quality.exists() else None)

def calculate(data,threshold,minimum,remove_singletons=False):
    if not np.isfinite(threshold) or not -22<=threshold<=-12: raise ValueError('Water threshold must be between -22 and -12 dB.')
    if not np.isfinite(minimum) or not 0<=minimum<=8: raise ValueError('Minimum change must be between 0 and 8 dB.')
    classes,delta=classify(data['before'],data['after'],data['valid'],threshold,minimum)
    suppressed = np.zeros(classes.shape, dtype=bool)
    if remove_singletons:
        classes,suppressed=suppress_single_pixel_changes(classes)
    expansion=int((classes==2).sum())*data['pixel_area']
    recession=int((classes==3).sum())*data['pixel_area']
    return dict(classes=classes,delta=delta,expansion=expansion,recession=recession,net=expansion-recession,valid_area=int(data['valid'].sum())*data['pixel_area'],suppressed_pixels=int(suppressed.sum()))

def sensitivity(data,minimum,remove_singletons=False):
    return [{'Threshold (dB)':float(t),'Expansion (km²)':r['expansion'],'Recession (km²)':r['recession']}
            for t in np.arange(-22,-11.99,.5) for r in [calculate(data,float(t),minimum,remove_singletons)]]
