"""Presentation-only geographic context. Uses cached NHD; never queries a service."""
import json
from pathlib import Path

import numpy as np
from rasterio.warp import transform_geom
from shapely.geometry import shape, mapping

from src.i18n import t, num
from src.investigation_panel import investigation_map
from src.time_series_map import continuous_display

NHD = Path(__file__).resolve().parents[1] / 'data/scientific_quality_check/nhd_layer_6.geojson'


def waterway_context(region, footprint, crs, path=NHD):
    """Distance to the *cached* stream/canal subset, in projected metres.

    Not a comprehensive inventory: absence from this subset is not absence of water.
    NHD ftypes 336 (canal/ditch) and 460 (stream/river), as in the saved quality check.
    """
    result = dict(features={'type': 'FeatureCollection', 'features': []}, distance_m=None,
                  source=str(Path(path).name), available=False)
    try:
        data = json.loads(Path(path).read_text())
        if data.get('exceededTransferLimit'):
            return result
        from rasterio.crs import CRS
        projected = CRS.from_user_input(crs)
        if not projected.is_projected or projected.linear_units != 'metre':
            raise ValueError('Geographic context requires a projected metre CRS.')
        candidate = shape(transform_geom('EPSG:4326', projected, region['geometry']))
        aoi = shape(footprint)
        distances = []
        for feature in data['features']:
            props = feature.get('properties', {})
            if int(props.get('ftype', props.get('FTYPE', 0))) not in (336, 460) or not feature.get('geometry'):
                continue
            geometry = shape(feature['geometry'])
            if not geometry.is_valid or geometry.is_empty:
                continue
            distances.append(candidate.distance(shape(transform_geom('EPSG:4326', projected, feature['geometry']))))
            clipped = geometry.intersection(aoi)
            if not clipped.is_empty:
                result['features']['features'].append(dict(type='Feature', geometry=mapping(clipped), properties={}))
        result['available'] = bool(distances)
        result['distance_m'] = min(distances) if distances else None
    except (OSError, ValueError, KeyError, TypeError):
        return result
    return result


def context_sentence(context, lang):
    if context['distance_m'] is None:
        return t('ux.context_missing', lang=lang)
    return t('ux.context_distance', lang=lang, distance=num(context['distance_m'], 0, lang=lang))


def workflow_map(report, ctx, water):
    values = np.where(ctx['pair_valid'], ctx['HH_delta'], np.nan)
    rgba, bounds = continuous_display(values, ctx['grid'], -6., 6., 'RdBu_r', max_pixels=768)
    title = f"ΔHH · {ctx['dates'][ctx['first']]} → {ctx['dates'][ctx['second']]} · dB"
    # Keep the existing investigation map, candidate geometries and common footprint.
    return investigation_map(report, ctx['candidate']['id'], ctx['lang'],
                             change_overlay=(rgba, bounds, title), waterways=water['features'], focus_selected=True)
