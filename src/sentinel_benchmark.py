"""Separate VV/VH benchmark adapter; never NISAR-specific accuracy."""
import numpy as np
import rasterio
from src.water_change import mask_aware_mean,power_to_db,classify
from src.reference_validation import agreement

def prepare_db(db,valid,units='dB'):
    if units!='dB':raise ValueError('Sen1Floods11 adapter requires documented dB input.')
    db=np.asarray(db,dtype=float)
    # Input already dB: convert to power ONLY to apply the existing linear mean.
    power=np.where(valid,10**(db/10),np.nan)
    return power_to_db(mask_aware_mean(power,valid,3))

def evaluation_mask(labels,radar_valid):
    return np.asarray(radar_valid,dtype=bool)&np.isin(labels,[0,1])

def load_chip(radar_path,label_path):
    with rasterio.open(radar_path) as r,rasterio.open(label_path) as l:
        if r.count!=2 or l.count!=1 or r.crs!=l.crs or r.shape!=l.shape or not r.transform.almost_equals(l.transform,precision=1e-12):raise ValueError('Bands or label alignment mismatch.')
        if r.descriptions!=('VV','VH'):raise ValueError('Unexpected radar band order.')
        db=r.read().astype(float);labels=l.read(1)
        if not np.isin(labels,[-1,0,1]).all():raise ValueError('Unexpected manual-label codes.')
        valid=np.all(np.isfinite(db)&(r.read_masks()>0),axis=0)
        metadata={'crs':str(r.crs),'shape':r.shape,'transform':list(r.transform)[:6],'radar_bands':r.descriptions,'radar_nodata':[str(x) for x in r.nodatavals],'label_nodata_metadata':str(l.nodata),'label_codes':[int(x) for x in np.unique(labels)],'units_source':'Official README: S1 GRD dB; bands also verified from actual TIFF descriptions','label_valid_pixels':int(np.isin(labels,[0,1]).sum()),'radar_valid_pixels':int(valid.sum())}
    return np.stack([prepare_db(b,valid) for b in db]),labels,evaluation_mask(labels,valid),metadata

def predict(db,threshold):
    # Reuse the static threshold rule via persistent candidates of identical
    # arguments; this is water PRESENCE, never a simulated change observation.
    classes,_=classify(db,db,np.isfinite(db),water_threshold=float(threshold),min_change=None)
    return classes==1

def otsu_threshold(db):
    x=db[np.isfinite(db)]
    if x.size==0:raise ValueError('No valid radar data for Otsu.')
    if x.min()==x.max():return float(x.min())
    hist,edges=np.histogram(x,bins=256);centers=(edges[:-1]+edges[1:])/2
    weights=np.cumsum(hist).astype(float);sums=np.cumsum(hist*centers);total=weights[-1]
    denom=weights*(total-weights);score=np.full(256,-np.inf)
    np.divide((sums[-1]*weights-sums*total)**2,denom,out=score,where=denom>0)
    return float(centers[np.argmax(score)])

def assert_no_leakage(train,test,official_train,official_test):
    if set(train)&set(test) or not set(train)<=set(official_train) or not set(test)<=set(official_test):raise ValueError('Train/test split leakage or membership error.')
