"""Exploratory reliability statistics; never a replacement water classifier."""
from pathlib import Path
import warnings
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'data/scientific_diagnostics'
MAD_NORMAL=1.482602218505602


def robust_statistics(values):
    values=np.asarray(values,dtype=float);values=values[np.isfinite(values)]
    if not values.size:return dict(count=0,median=None,mad=None,scaled_mad=None,iqr=None,p05=None,p25=None,p75=None,p95=None)
    q=np.percentile(values,[5,25,50,75,95]);mad=float(np.median(np.abs(values-q[2])))
    return dict(count=int(values.size),median=float(q[2]),mad=mad,scaled_mad=MAD_NORMAL*mad,iqr=float(q[3]-q[1]),
                p05=float(q[0]),p25=float(q[1]),p75=float(q[3]),p95=float(q[4]))


def temporal_scaled_change(db,first=0,second=1,floor_db=1.,cutoff=3.):
    """ΔdB / max(1.4826*MAD(other dates),1dB). Four finite reference dates needed.

    Leave BOTH comparison dates out. This reflects local temporal variation,
    including environment, not just measurement noise. The 1 dB regularizer and
    |score|>=3 cutoff are declared exploratory choices, NOT estimated error or
    significance levels. No scene offset is removed. Floor implies a >=3dB
    effective gate at defaults, so smaller candidate sets do not prove accuracy.
    """
    db=np.asarray(db,dtype=float)
    if db.ndim!=3 or first==second or first not in range(len(db)) or second not in range(len(db)):
        raise ValueError('Expected distinct comparison dates in a time/y/x cube.')
    if not np.isfinite([floor_db,cutoff]).all() or floor_db<=0 or cutoff<=0:raise ValueError('Positive finite diagnostic settings required.')
    db=np.where(np.isfinite(db),db,np.nan)
    reference=np.where(np.isfinite(db),db,np.nan)[[i for i in range(len(db)) if i not in (first,second)]]
    count=np.isfinite(reference).sum(axis=0)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        center=np.nanmedian(reference,axis=0);mad=np.nanmedian(np.abs(reference-center),axis=0)
    scale=np.maximum(MAD_NORMAL*mad,floor_db)
    valid=(count>=4)&np.isfinite(db[first])&np.isfinite(db[second])&np.isfinite(scale)
    score=np.full(db.shape[1:],np.nan);np.divide(db[second]-db[first],scale,out=score,where=valid)
    return dict(score=score,scale_db=np.where(valid,scale,np.nan),reference_count=count,valid=valid,
                gate=valid&(np.abs(score)>=cutoff))


def local_texture(power,looks=None,filtered=False):
    """Conservative conditional ENL moment estimate only on stationary raw patches.

    Qualification: >=400 positive cells, all cells valid; relative plane trend
    <=0.1, quadrant mean contrast<=0.15, |lag1 correlation|<=0.2, and local
    numberOfLooks IQR/median<=0.1. Passing is only provisional homogeneity support,
    not proof of independent samples or a thermal noise estimate. Filtered data
    are never used to estimate ENL. Otherwise report texture only and ENL=None.
    """
    p=np.asarray(power,dtype=float)
    if p.ndim!=2:raise ValueError('Texture requires a 2D power patch.')
    valid=np.isfinite(p)&(p>0);v=p[valid]
    if v.size<2:return dict(count=int(v.size),cv=None,relative_plane_trend=None,quadrant_contrast=None,lag1_max_abs=None,enl=None,qualified=False)
    mean=float(v.mean());variance=float(v.var(ddof=1));cv=float(np.sqrt(variance)/mean)
    yy,xx=np.indices(p.shape);design=np.column_stack((np.ones(v.size),xx[valid],yy[valid]))
    coef=np.linalg.lstsq(design,v,rcond=None)[0]
    trend=float((abs(coef[1])*(p.shape[1]-1)+abs(coef[2])*(p.shape[0]-1))/mean)
    halves=[block[np.isfinite(block)&(block>0)] for row in np.array_split(p,2,axis=0) for block in np.array_split(row,2,axis=1)]
    means=[float(b.mean()) for b in halves if b.size];contrast=(max(means)-min(means))/mean
    correlations=[]
    for a,b in ((p[:,:-1],p[:,1:]),(p[:-1,:],p[1:,:])):
        m=np.isfinite(a)&(a>0)&np.isfinite(b)&(b>0)
        if m.sum()>2 and np.std(a[m])>0 and np.std(b[m])>0:correlations.append(float(np.corrcoef(a[m],b[m])[0,1]))
    lag=max(map(abs,correlations)) if correlations else None
    looks_cv=None
    if looks is not None:
        l=np.asarray(looks)[valid];l=l[np.isfinite(l)&(l>0)]
        if l.size==v.size:looks_cv=float((np.percentile(l,75)-np.percentile(l,25))/np.median(l))
    qualified=bool(not filtered and v.size>=400 and valid.all() and trend<=.1 and contrast<=.15 and lag is not None and lag<=.2 and looks_cv is not None and looks_cv<=.1 and variance>0)
    return dict(count=int(v.size),mean_linear=mean,variance_linear=variance,cv=cv,relative_plane_trend=trend,
                quadrant_contrast=float(contrast),lag1_max_abs=lag,looks_relative_iqr=looks_cv,qualified=qualified,
                enl=float(mean**2/variance) if qualified else None)


def select_stable_tiles(hh,hv,common,far_from_water,size=21,maximum=3):
    """Prespecified later-four-date selection; June21/July3 changes are not ranked.

    Whole 210m tiles, >=90% farther than100m from mapped waterways, median
    reference HH>-12 and HV>-20dB, reference tile-median temporal IQR<=1.5dB.
    Rank spatial IQR of the four-date temporal median (HH+HV); keep separated
    centers>=300m. These are selected quiet-looking patches, not stable truth.
    """
    candidates=[]
    for row in range(0,common.shape[0]-size+1,size):
        for col in range(0,common.shape[1]-size+1,size):
            sl=np.s_[row:row+size,col:col+size]
            if not common[sl].all() or np.mean(far_from_water[sl])<.9:continue
            h=hh[2:,row:row+size,col:col+size];v=hv[2:,row:row+size,col:col+size]
            hm=np.median(h,axis=(1,2));vm=np.median(v,axis=(1,2))
            if np.median(hm)<=-12 or np.median(vm)<=-20 or np.ptp(np.percentile(hm,[25,75]))>1.5 or np.ptp(np.percentile(vm,[25,75]))>1.5:continue
            score=float(np.ptp(np.percentile(np.median(h,axis=0),[25,75]))+np.ptp(np.percentile(np.median(v,axis=0),[25,75])))
            candidates.append(dict(row=row,column=col,size=size,selection_score_iqr_db=score))
    selected=[]
    for candidate in sorted(candidates,key=lambda x:(x['selection_score_iqr_db'],x['row'],x['column'])):
        if all(np.hypot(candidate['row']-s['row'],candidate['column']-s['column'])>=30 for s in selected):selected.append(candidate)
        if len(selected)==maximum:break
    return selected,len(candidates)
