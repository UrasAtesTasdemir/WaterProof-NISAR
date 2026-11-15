"""Geographic (Leaflet) view of the CURRENT Louisiana dashboard classes.

Reuses the existing display helpers in ``src.geographic_map``. Areas are never
computed from the display raster; the dashboard metrics stay native-grid.
"""
import numpy as np
from rasterio.features import shapes
from rasterio.warp import transform_geom
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

from src.geographic_map import visualization_grid, build_map


def valid_footprint(valid, grid):
    """Actual common-valid footprint polygon in EPSG:4326 (GeoJSON mapping)."""
    valid = np.asarray(valid, dtype=bool)
    if not valid.any():
        raise ValueError('No valid pixels for a footprint.')
    geometry = unary_union([shape(g) for g, v in shapes(valid.astype('uint8'), mask=valid,
                                                         transform=grid['transform']) if v == 1])
    return transform_geom(grid['crs'], 'EPSG:4326', mapping(geometry))


def classes_map_html(classes, valid, grid, valid_area_km2):
    """Leaflet HTML for the slider-driven classes (0 unknown, 1-3 candidates, 4 other)."""
    classes = np.asarray(classes, dtype='uint8')
    if classes.shape != np.shape(valid):
        raise ValueError('Classes do not match the radar grid.')
    display, _, bounds = visualization_grid(classes, grid['crs'], grid['transform'])
    return build_map({'valid_comparison_area_km2': float(valid_area_km2)}, display, bounds,
                     valid_footprint(valid, grid))
