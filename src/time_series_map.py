"""Continuous HH maps on the existing geographic display grid."""
import html
import json

import folium
import numpy as np
from matplotlib import colormaps
from rasterio.enums import Resampling
from rasterio.warp import reproject

from src.geographic_map import visualization_grid
from src.time_series import DIRECTORY, pair_difference


def continuous_display(values, grid, vmin, vmax, cmap='gray', max_pixels=768):
    """Nearest observed dB for display only; preserve NaN alpha and north-up order."""
    if not np.isfinite([vmin, vmax]).all() or vmax <= vmin:
        raise ValueError('Display scale must be finite and increasing.')
    mask, tr, bounds = visualization_grid(np.isfinite(values).astype('uint8'), grid['crs'], grid['transform'], max_pixels)
    display = np.full(mask.shape, np.nan, dtype='float32')
    reproject(np.asarray(values, dtype='float32'), display, src_transform=grid['transform'], src_crs=grid['crs'],
              src_nodata=np.nan, dst_transform=tr, dst_crs='EPSG:3857', dst_nodata=np.nan, resampling=Resampling.nearest)
    display[mask == 0] = np.nan
    finite = np.isfinite(display)
    scaled = np.where(finite, np.clip((display-vmin)/(vmax-vmin), 0, 1), 0)
    rgba = (colormaps[cmap](scaled)*255).astype('uint8'); rgba[...,3] = np.where(finite, 205, 0)
    return rgba, bounds


def build_time_map(data, first, second, layer, point=None):
    report = data['report']; observations = report['observations']; db = data['db']; grid = data['grid']
    first_date = observations[first]['date']; second_date = observations[second]['date']
    delta, valid = pair_difference(db, first, second)
    if layer == 'Selected observation':
        values = db[first]; low, high = report['display_scale_db']; cmap = 'gray'; title = first_date+' HH'
    elif layer == 'Comparison observation':
        values = db[second]; low, high = report['display_scale_db']; cmap = 'gray'; title = second_date+' HH'
    elif layer == 'Comparison − selected (dB)':
        values = delta; low, high = -6., 6.; cmap = 'RdBu_r'; title = second_date+' minus '+first_date
    elif layer == 'Selected anomaly (dB)':
        from src.time_series import temporal_summary
        _, anomalies, _ = temporal_summary(np.where(data['common'], db, np.nan))
        values = anomalies[first]; low, high = -6., 6.; cmap = 'RdBu_r'; title = first_date+' minus temporal median'
    else:
        raise ValueError('Unknown map layer.')
    rgba, bounds = continuous_display(values, grid, low, high, cmap)
    m = folium.Map(location=[sum(x[0] for x in bounds)/2, sum(x[1] for x in bounds)/2],
                   tiles='OpenStreetMap', zoom_start=13, control_scale=True)
    folium.raster_layers.ImageOverlay(rgba, bounds=bounds, name=title, opacity=.85, origin='upper').add_to(m)
    footprint = json.loads((DIRECTORY/'common_footprint.geojson').read_text())
    folium.GeoJson(footprint, name='Six-date common valid footprint',
                   style_function=lambda f:dict(color='#00a892',weight=2,fillOpacity=0),
                   tooltip=f"Six-date common area: {report['common_valid_area_km2']:.4f} km²").add_to(m)
    if point:
        folium.Marker([point['pixel_center_latitude'],point['pixel_center_longitude']],
            tooltip=f"Sampled pixel center: row {point['row']}, column {point['column']}",
            icon=folium.Icon(color='red',icon='info-sign')).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m); folium.LatLngPopup().add_to(m); m.fit_bounds(bounds)
    gradient = 'linear-gradient(to right,#000,#fff)' if cmap == 'gray' else 'linear-gradient(to right,#053061,#fff,#67001f)'
    legend = f'''<div style="position:fixed;bottom:22px;left:12px;z-index:9999;background:white;padding:10px;border:1px solid #aaa;border-radius:8px;font:12px sans-serif;max-width:260px">
    <b>{html.escape(title)}</b><br>HH / HHHH · 10 m native grid<br>
    <div style="background:{gradient};height:12px;margin:6px 0"></div>{low:.1f} → {high:.1f} dB (display clipping only)<br>
    Transparent = NoData · Green = common footprint<br>Exploratory radar dynamics; not confirmed flooding.<br>Not a NISAR accuracy score.</div>'''
    m.get_root().html.add_child(folium.Element(legend))
    return m.get_root().render()
