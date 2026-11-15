"""Two tiny GCOV quality windows and bounded calibration metadata inspection."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import h5py
import numpy as np
import rasterio
from scripts.check_earthdata_access import available_token,AccessCheckError
from scripts.detect_water_change import save_raster
from src.nisar_data import open_frequency_a,RadarDataError,GROUP

OUT=ROOT/'data/scientific_diagnostics'


def json_value(value):
    if isinstance(value,bytes):return value.decode('utf-8',errors='replace')
    if isinstance(value,np.ndarray):return json_value(value.tolist())
    if isinstance(value,dict):return {str(k):json_value(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [json_value(v) for v in value]
    if isinstance(value,np.generic):return json_value(value.item())
    if value is None or isinstance(value,(str,int,float,bool)):return value
    return str(value)


def metadata_probe(remote,report):
    """Only names/attributes under GCOV metadata; never load radar/noise arrays."""
    report['noise_calibration_inventory']=[]
    with h5py.File(remote,'r') as h5:
        prefix='/science/LSAR/GCOV/metadata'
        if prefix not in h5:
            report['gcov_metadata_group_available']=False;return
        report['gcov_metadata_group_available']=True
        visited=[0]
        def visitor(name,obj):
            visited[0]+=1
            if visited[0]>4000:raise RadarDataError('Metadata inventory exceeds the bounded inspection limit.')
            if any(word in name.lower() for word in ('noise','nesz','calibration')):
                entry={'path':prefix+'/'+name,'kind':'dataset' if isinstance(obj,h5py.Dataset) else 'group'}
                if isinstance(obj,h5py.Dataset):entry.update(shape=list(obj.shape),dtype=str(obj.dtype))
                entry['attributes']={k:json_value(v) for k,v in obj.attrs.items() if k in ('description','long_name','units','_FillValue','valid_min','valid_max')}
                report['noise_calibration_inventory'].append(entry)
        h5[prefix].visititems(visitor)
        report['metadata_objects_inspected']=visited[0]


def main():
    OUT.mkdir(exist_ok=True);out=OUT/'quality_metadata.json'
    if out.exists():print('Existing quality inspection left unchanged.');return 0
    results=[]
    try:
        manifest=json.loads((ROOT/'data/time_series/manifest.json').read_text())
        hhmeta=json.loads((ROOT/'data/subsets/nisar_hhhh_2026-06-21.json').read_text())
        win=hhmeta['pixel_center_window'];r0,r1=win['row_start'],win['row_stop_exclusive'];c0,c1=win['column_start'],win['column_stop_exclusive']
        with rasterio.open(ROOT/'data/time_series/common_valid.tif') as src:
            common=src.read(1).astype(bool);grid=dict(crs=src.crs,transform=src.transform,shape=src.shape)
        token=available_token()
        if not token:raise RadarDataError('No local protected Earthdata credential is available for quality inspection.')
        for item in manifest['observations'][:2]:
            day=item['date'];entry={'product_id':item['product_id'],'acquisition_utc':item['start_time_utc'],'date':day,'layers':{}}
            print('Inspecting bounded GCOV quality metadata:',day,flush=True)
            with open_frequency_a(item,token,inspect_file=lambda remote:metadata_probe(remote,entry)) as (ds,stats):
                entry['available_frequencyA_variables']=list(ds.variables)
                x=ds.xCoordinates.values[c0:c1];y=ds.yCoordinates.values[r0:r1]
                expected_x=grid['transform'].c+(np.arange(common.shape[1])+.5)*grid['transform'].a
                expected_y=grid['transform'].f+(np.arange(common.shape[0])+.5)*grid['transform'].e
                if not np.allclose(x,expected_x,atol=1e-7,rtol=0) or not np.allclose(y,expected_y,atol=1e-7,rtol=0):
                    raise RadarDataError('Quality-grid coordinates disagree with cached HH/HV window.')
                for name in ('numberOfLooks','mask'):
                    if name not in ds.variables:entry['layers'][name]={'available':False};continue
                    layer=ds[name];meta={'available':True,'path':GROUP+'/'+name,'shape':list(layer.shape),'dtype':str(layer.dtype),
                        'attributes':{k:json_value(v) for k,v in layer.attrs.items()},
                        'encoding_fill_value':json_value(layer.encoding.get('_FillValue'))}
                    if layer.ndim!=2:raise RadarDataError('Quality layer is not a two-dimensional grid.')
                    xdim=ds.xCoordinates.dims[0];ydim=ds.yCoordinates.dims[0]
                    cached=OUT/f'{name}_{day}.tif'
                    if cached.exists():
                        with rasterio.open(cached) as src:
                            if src.tags().get('product_id')!=item['product_id'] or src.transform!=grid['transform']:raise RadarDataError('Cached quality provenance mismatch.')
                            values=src.read(1)
                    else:
                        values=layer.isel({ydim:slice(r0,r1),xdim:slice(c0,c1)}).transpose(ydim,xdim).load().values
                    sample=values[common];finite=sample[np.isfinite(sample)]
                    meta['window_shape']=list(values.shape);meta['common_finite_count']=int(finite.size)
                    if finite.size:
                        meta['min']=float(finite.min());meta['median']=float(np.median(finite));meta['max']=float(finite.max())
                        if name=='mask':
                            codes,counts=np.unique(finite,return_counts=True);meta['observed_common_codes']={str(int(c)):int(n) for c,n in zip(codes,counts)}
                    if not cached.exists():
                        save_raster(cached,[np.where(common,values,np.nan)],[name],grid,
                            {'source_layer':GROUP+'/'+name,'product_id':item['product_id'],'acquisition_utc':item['start_time_utc'],'interpretation':'Quality diagnostic only; no production mask or measurements changed'})
                    entry['layers'][name]=meta
                entry.update(stats)
            results.append(entry);print('Quality layers inspected:',day,flush=True)
        out.write_text(json.dumps({'status':'success','observations':results,'full_hdf5_downloaded':False,
            'noise_floor_assessment':'Metadata inventory only. No noise-equivalent backscatter was mapped/calibrated onto gamma-0 AOI; no HV noise-floor or SNR value is inferred.','production_masks_changed':False},indent=2,default=json_value)+'\n')
        return 0
    except Exception as exc:
        detail=str(exc) if isinstance(exc,(RadarDataError,AccessCheckError)) else 'Sensitive exception text suppressed.'
        (OUT/'quality_access_blocker.json').write_text(json.dumps({'status':'blocked','error_type':type(exc).__name__,'detail':detail,'completed_dates':[e['date'] for e in results]},indent=2)+'\n')
        print('Quality access stopped:',type(exc).__name__,detail,flush=True);return 2


def read_processing_flags():
    """Reproducible bounded scalar read; leave an existing successful file intact."""
    out=OUT/'processing_flags.json'
    if out.exists():return
    records=[]
    for item in json.loads((ROOT/'data/time_series/manifest.json').read_text())['observations'][:2]:
        record={'product_id':item['product_id'],'date':item['date']}
        def inspect(remote):
            with h5py.File(remote,'r') as h5:
                path='/science/LSAR/GCOV/metadata/processingInformation/parameters/noiseCorrectionApplied'
                record['noiseCorrectionApplied']=json_value(h5[path][()]) if path in h5 else None
        with open_frequency_a(item,available_token(),inspect_file=inspect) as (ds,stats):record.update(stats)
        records.append(record)
    out.write_text(json.dumps({'status':'success','observations':records},indent=2,default=json_value)+'\n')


if __name__=='__main__':
    code=main()
    if code==0:
        try:read_processing_flags()
        except Exception as exc:
            print('Processing flag inspection stopped:',type(exc).__name__,'; sensitive details suppressed.');code=2
    raise SystemExit(code)
