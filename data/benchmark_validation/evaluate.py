"""Reproducible bounded manual-label benchmark. Calibration sees train only."""
import json,sys,os,csv,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT));os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
import numpy as np
from src.sentinel_benchmark import load_chip,predict,otsu_threshold,assert_no_leakage
from src.reference_validation import agreement

def main():
 m=json.loads((P/'sample_manifest.json').read_text());train=[r for r in m['records'] if r['split']=='train'];test=[r for r in m['records'] if r['split']=='test']
 official={s:[r[0] for r in csv.reader((P/f'flood_{s}_data.csv').read_text().splitlines())] for s in ('train','test')}
 assert_no_leakage([r['radar'] for r in train],[r['radar'] for r in test],official['train'],official['test'])
 loaded=[]
 for r in train:
  db,labels,valid,meta=load_chip(P/'raw'/r['radar'],P/'raw'/r['label']);loaded.append((r,db,labels,valid,meta))
 scores=[]
 for band in (0,1):
  for threshold in np.arange(-30,-7.99,.5):
   scene_scores=[]
   for _,db,labels,valid,_ in loaded:
    result=agreement(predict(db[band],threshold),labels==1,valid);scene_scores.append(result['F1'] or 0.)
   scores.append({'band_index':band,'band':['VV','VH'][band],'threshold_db':float(threshold),'training_macro_F1':float(np.mean(scene_scores))})
 best=max(scores,key=lambda r:r['training_macro_F1'])
 config={**best,'input_units':'dB','filter':'3x3 mask-aware linear-power mean; radar-valid support only, never label-valid support','objective':'Mean per-chip training F1, undefined F1 counted as0; ties choose first VV then most-negative threshold. Grid -30..-8dB step0.5. No NISAR -16dB reuse.','calibration_split':'official train subset','evaluation_split':'official test subset','baseline':'Per-image 256-bin Otsu on same selected band after same filtering, histogram uses radar validity only, never test annotations.'}
 # Freeze before reading any test raster/annotation for evaluation.
 (P/'calibration.json').write_text(json.dumps(config,indent=2)+'\n');(P/'training_grid.json').write_text(json.dumps(scores,indent=2)+'\n')
 print('TRAIN-ONLY CONFIG',config,flush=True)
 rows=[];ps=[];bs=[];ys=[];scene_arrays=[]
 for r in test:
  db,labels,valid,meta=load_chip(P/'raw'/r['radar'],P/'raw'/r['label']);b=best['band_index'];pred=predict(db[b],best['threshold_db']);ot=otsu_threshold(db[b]);base=predict(db[b],ot)
  score=agreement(pred,labels==1,valid);baseline=agreement(base,labels==1,valid)
  rows.append({'scene_id':r['scene_id'],'group':r['group'],'split':'official test','metrics':score,'baseline':baseline,'otsu_threshold_db':ot,'metadata':meta})
  ps.append(pred[valid]);bs.append(base[valid]);ys.append(labels[valid]==1);scene_arrays.append((r,db[b],labels,valid,pred,score))
 micro=agreement(np.concatenate(ps),np.concatenate(ys),np.ones(sum(len(y) for y in ys),bool));baseline_micro=agreement(np.concatenate(bs),np.concatenate(ys),np.ones(sum(len(y) for y in ys),bool))
 # All sampled test scenes get a panel, including the worst. No success-only selection.
 (P/'figures').mkdir(exist_ok=True)
 for r,db,labels,valid,pred,score in scene_arrays:
  truth=np.where(valid,labels,-1);prediction=np.where(valid,pred.astype(int),-1)
  errors=np.zeros(labels.shape,int);errors[valid&~pred&(labels==0)]=1;errors[valid&pred&(labels==1)]=2;errors[valid&pred&(labels==0)]=3;errors[valid&~pred&(labels==1)]=4
  fig,axes=plt.subplots(1,4,figsize=(14,4),layout='constrained')
  vmin,vmax=np.percentile(db[np.isfinite(db)],[2,98]);im=axes[0].imshow(db,cmap='gray',vmin=vmin,vmax=vmax);fig.colorbar(im,ax=axes[0],shrink=.6,label='dB')
  axes[0].set_title('A · Real '+best['band']+' (3x3 filtered)')
  for ax,array,title in ((axes[1],truth,'B · Manual water annotation'),(axes[2],prediction,'C · Train-calibrated prediction')):
   ax.imshow(array,cmap=ListedColormap(['#cccccc','#fafafa','#1973b9']),norm=BoundaryNorm([-1.5,-.5,.5,1.5],3));ax.set_title(title)
  axes[3].imshow(errors,cmap=ListedColormap(['#ccc','#fafafa','#1973b9','#e68a20','#c52b50']),vmin=0,vmax=4);axes[3].set_title('D · Agreement / disagreement')
  for ax in axes:ax.set_xticks([]);ax.set_yticks([])
  fig.suptitle(f"{r['scene_id']} | official held-out test | F1 {score['F1'] if score['F1'] is not None else 'undefined'}",fontsize=10)
  fig.supxlabel('Gray: ignored · white: true nonwater · blue: true water · orange: false positive · red: missed water. Sentinel-1 benchmark ONLY; not NISAR accuracy.',fontsize=8)
  fig.savefig(P/'figures'/(r['scene_id']+'.png'),dpi=130);plt.close(fig)
 report={'status':'success','dataset':'Sen1Floods11 v1.1 hand labels','sampling':m['selection'],'train_scenes':len(train),'test_scenes':len(test),'groups':m['groups'],'calibration':config,'test_micro_metrics':micro,'baseline_micro_metrics':baseline_micro,'test_scene_metrics':rows,'test_macro_F1':float(np.mean([r['metrics']['F1'] or 0 for r in rows])),'worst_scene':min(rows,key=lambda r:r['metrics']['F1'] or 0)['scene_id'],'test_valid_pixels':micro['valid_pixels'],'interpretation':'Small selected official test-chip subset; not full benchmark, event-independent holdout, NISAR accuracy, or confirmed flood extent. Hand labels include surface water; zero is nonwater, -1 ignored. Both bands read, training chooses band/threshold; test frozen and no selective removal. Training/test chips can share event geography under official split.','download_bytes':sum(p.stat().st_size for p in (P/'raw').glob('*.tif'))}
 (P/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('train_scenes','test_scenes','test_valid_pixels','test_micro_metrics','baseline_micro_metrics','worst_scene','download_bytes')},indent=2))
if __name__=='__main__':main()
