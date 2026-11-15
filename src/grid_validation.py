"""Strict north-up, projected metre grids; no implicit resampling or alignment."""
import numpy as np
from rasterio.crs import CRS
from rasterio.transform import Affine

# A micrometre permits serialization roundoff, far below a SAR pixel.
COORD_ATOL_M = 1e-6


def metric_grid(crs, transform, shape):
    crs = CRS.from_user_input(crs)
    transform = Affine(*list(transform)[:6])
    if not crs.is_projected or crs.linear_units_factor[1] != 1:
        raise ValueError('A projected metre CRS is required.')
    if (len(shape) != 2 or any(int(n) != n or n <= 0 for n in shape)
            or not np.isfinite(tuple(transform)[:6]).all() or transform.a <= 0 or transform.e >= 0
            or transform.b != 0 or transform.d != 0):
        raise ValueError('Only finite, north-up, unrotated metre grids are supported.')
    return crs, transform, tuple(shape)


def assert_same_grid(reference, other):
    """Validate CRS, size, spacing, affine and corner/centre pixel centres."""
    c1, a, shape1 = metric_grid(reference['crs'], reference['transform'], reference['shape'])
    c2, b, shape2 = metric_grid(other['crs'], other['transform'], other['shape'])
    if c1 != c2 or shape1 != shape2 or not np.allclose(tuple(a)[:6], tuple(b)[:6], rtol=0, atol=COORD_ATOL_M):
        raise ValueError('Raster grids differ; explicit alignment is required.')
    height, width = shape1
    for col, row in ((.5,.5), (width-.5,height-.5), (width/2,height/2)):
        if not np.allclose(a*(col,row), b*(col,row), rtol=0, atol=COORD_ATOL_M):
            raise ValueError('Pixel centres differ.')


def metric_ring(footprint, valid, transform, crs, inner_m=50, outer_m=150):
    from scipy.ndimage import distance_transform_edt
    _, tr, _ = metric_grid(crs, transform, footprint.shape)
    if not 0 <= inner_m < outer_m:
        raise ValueError('Invalid metric ring radii.')
    distance = distance_transform_edt(~np.asarray(footprint,bool), sampling=(abs(tr.e),tr.a))
    return (distance > inner_m) & (distance <= outer_m) & valid
