"""Real raster overlays: native-grid measurements, Web Mercator display only."""
from pathlib import Path
import json
import numpy as np
import rasterio
from rasterio.warp import reproject,transform_bounds,transform_geom
from rasterio.transform import Affine,array_bounds
from rasterio.enums import Resampling
from rasterio.features import shapes
from shapely.geometry import shape,mapping
from shapely.ops import unary_union
import folium
from src.water_change import pixel_area_km2

ROOT=Path(__file__).resolve().parents[1]
COLORS={1:(35,114,165),2:(0,189,163),3:(237,140,35)}
NAMES={1:'Persistent water candidate',2:'Candidate water expansion',3:'Candidate water recession'}


def visualization_grid(classes,crs,transform,max_pixels=768):
    """Categorical nearest reprojection, north-up EPSG:3857 for Leaflet."""
    bounds=transform_bounds(crs,'EPSG:3857',*array_bounds(*classes.shape,transform),densify_pts=21)
    left,bottom,right,top=bounds;resolution=max(right-left,top-bottom)/max_pixels
    width=int(np.ceil((right-left)/resolution));height=int(np.ceil((top-bottom)/resolution))
    target=Affine(resolution,0,left,0,-resolution,top)
    out=np.zeros((height,width),dtype='uint8')
    reproject(classes,out,src_transform=transform,src_crs=crs,src_nodata=0,
              dst_transform=target,dst_crs='EPSG:3857',dst_nodata=0,resampling=Resampling.nearest)
    west,south,east,north=transform_bounds('EPSG:3857','EPSG:4326',*array_bounds(height,width,target))
    return out,target,[[south,west],[north,east]]


def rgba_layer(classes,code):
    rgba=np.zeros((*classes.shape,4),dtype='uint8')
    rgba[classes==code]=(*COLORS[code],185)
    return rgba


def load_geographic(directory):
    directory=Path(directory)
    meta=json.loads((directory/'results.json').read_text())
    with rasterio.open(directory/'classes.tif') as src:
        classes=src.read(1);crs=src.crs;transform=src.transform
        if src.crs.to_epsg()!=32615 or src.res!=(10,10):raise ValueError('Unexpected native Louisiana grid.')
    cell=pixel_area_km2(crs,transform)
    for code in range(5):
        if int((classes==code).sum())!=meta['areas'][str(code)]['pixels']:raise ValueError('Stored counts differ from native raster.')
    if not np.isclose(int((classes!=0).sum())*cell,meta['valid_comparison_area_km2']):raise ValueError('Native area mismatch.')
    geometry=unary_union([shape(g) for g,value in shapes((classes!=0).astype('uint8'),mask=classes!=0,transform=transform) if value==1])
    footprint=transform_geom(crs,'EPSG:4326',mapping(geometry))
    display,display_transform,bounds=visualization_grid(classes,crs,transform)
    return meta,display,bounds,footprint


def build_map(meta,display,bounds,footprint):
    center=[(bounds[0][0]+bounds[1][0])/2,(bounds[0][1]+bounds[1][1])/2]
    m=folium.Map(location=center,tiles='OpenStreetMap',zoom_start=12,control_scale=True)
    for code in (2,3,1):
        folium.raster_layers.ImageOverlay(rgba_layer(display,code),bounds=bounds,
            name=NAMES[code],opacity=.8,origin='upper',show=True,interactive=False).add_to(m)
    folium.GeoJson(footprint,name='Actual valid processed footprint',
        style_function=lambda feature:{'color':'#12334a','weight':2,'fillOpacity':0},
        tooltip=f"Actual common valid footprint: {meta['valid_comparison_area_km2']:.4f} km²").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    folium.LatLngPopup().add_to(m)
    m.fit_bounds(bounds)
    legend='''<div style="position:fixed;bottom:24px;left:12px;z-index:9999;background:white;padding:12px;border:1px solid #aaa;border-radius:8px;font:12px sans-serif;max-width:245px">
    <b>Unvalidated candidate<br>surface-water changes</b><br>
    <span style="color:#00bda3">■</span> Expansion candidate<br>
    <span style="color:#ed8c23">■</span> Recession candidate<br>
    <span style="color:#2372a5">■</span> Persistent water candidate<br>
    ━ Actual valid processed boundary<br>21 June → 3 July 2026 · HH<br>
    Transparent: other surface / no data<br><small>Not confirmed flooding. Not benchmark accuracy.</small></div>'''
    m.get_root().html.add_child(folium.Element(legend))
    return m.get_root().render()
