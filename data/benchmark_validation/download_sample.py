"""Deterministic small official sample, selected without labels or metrics."""
from pathlib import Path
import csv,json,hashlib,requests
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def main():
 splits={s:list(csv.reader((P/f'flood_{s}_data.csv').read_text().splitlines())) for s in ('train','valid','test')}
 sets={s:{r[0] for r in rows} for s,rows in splits.items()}
 assert not sets['train']&sets['test'] and not sets['valid']&sets['test']
 groups=sorted(set(x.split('_')[0] for x in sets['train'])&set(x.split('_')[0] for x in sets['test']))[:6]
 records=[]
 for split in ('train','test'):
  for group in groups:
   selected=sorted([r for r in splits[split] if r[0].startswith(group+'_')],key=lambda r:hashlib.sha256(('FloodPulse-Sen1Floods11-v1:'+r[0]).encode()).hexdigest())[:2]
   for radar,label in selected:
    records.append({'split':split,'group':group,'scene_id':radar.removesuffix('_S1Hand.tif'),'radar':radar,'label':label})
 manifest={'source':'https://github.com/cloudtostreet/Sen1Floods11','bucket':'https://storage.googleapis.com/sen1floods11/v1.1/','units':'dB','band_order':['VV','VH'],'labels':{'-1':'ignore','0':'not water','1':'water'},'selection':'First six alphabetic event groups shared by official train/test, two chips per group per split by SHA256(FloodPulse-Sen1Floods11-v1:filename). Fixed before opening labels.','groups':groups,'records':records}
 (P/'sample_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (P/'raw').mkdir(exist_ok=True)
 for i,r in enumerate(records):
  for field,folder in (('radar','S1Hand'),('label','LabelHand')):
   path=P/'raw'/r[field];url=manifest['bucket']+'data/flood_events/HandLabeled/'+folder+'/'+r[field]
   if not path.exists():
    response=requests.get(url,timeout=45);response.raise_for_status()
    if len(response.content)>4*1024*1024:raise ValueError('Unexpectedly large chip')
    path.write_bytes(response.content)
   r[field+'_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
  (P/'sample_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(i+1,r['split'],r['scene_id'],flush=True)
if __name__=='__main__':main()
