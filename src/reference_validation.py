"""Conservative reference agreement utilities; never ground-truth accuracy."""
import numpy as np
from rasterio.warp import reproject
from rasterio.enums import Resampling

def align_categories(values,source_grid,target_grid):
    result=np.full(target_grid['shape'],255,dtype='uint8')
    reproject(values.astype('uint8'),result,src_transform=source_grid['transform'],src_crs=source_grid['crs'],src_nodata=255,
              dst_transform=target_grid['transform'],dst_crs=target_grid['crs'],dst_nodata=255,resampling=Resampling.nearest)
    return result

def reference_valid(values,kind):
    return np.isin(values,(0,1,3) if kind=='S1' else (0,1,2))

def eligibility(time_hours,valid_fraction):
    # A conservative analysis policy, not a universal validation standard.
    return abs(time_hours)<=24 and valid_fraction>=.8

def agreement(predicted,reference,valid):
    valid=np.asarray(valid,dtype=bool)
    if not valid.any():raise ValueError('No common valid reference area.')
    p=np.asarray(predicted,dtype=bool)[valid];r=np.asarray(reference,dtype=bool)[valid]
    tp=int((p&r).sum());tn=int((~p&~r).sum());fp=int((p&~r).sum());fn=int((~p&r).sum())
    ratio=lambda a,b: a/b if b else None
    return {'label':'Agreement with selected reference product, NOT ground-truth flood accuracy',
            'matrix_rows_reference_nonwater_water_columns_prediction_nonwater_water':[[tn,fp],[fn,tp]],
            'precision':ratio(tp,tp+fp),'recall':ratio(tp,tp+fn),'F1':ratio(2*tp,2*tp+fp+fn),'IoU':ratio(tp,tp+fp+fn),'valid_pixels':int(valid.sum())}
