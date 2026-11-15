"""Existing Folium map framework with a minimal Streamlit click bridge."""
from pathlib import Path
import json
import folium
from branca.element import MacroElement, Template
from src.live_engine import window_polygon
from src.i18n import t
from src.theme import themed_map_html


def selection_map(lat,lon,km,lang='en',footprint=None):
    m=folium.Map(location=[lat,lon],tiles='OpenStreetMap',zoom_start=13,control_scale=True)
    polygon=window_polygon(lat,lon,km)
    folium.GeoJson(polygon.__geo_interface__,name=f'{km:g} km × {km:g} km',
                   style_function=lambda f:dict(color='#d17f22',weight=2,fillOpacity=0)).add_to(m)
    folium.Marker([lat,lon],tooltip=f'{lat:.5f}, {lon:.5f}').add_to(m)
    if footprint:
        folium.GeoJson(footprint,name=t('ex.actual_footprint',lang=lang),
                       style_function=lambda f:dict(color='#007f83',weight=2,fillOpacity=.08)).add_to(m)
    event=MacroElement()
    event._template=Template('''{% macro script(this,kwargs) %}
    {{this._parent.get_name()}}.on('click',function(e){
      window.parent.postMessage({type:'nisar:point',lat:e.latlng.lat,lon:e.latlng.lng},'*');
    });{% endmacro %}''')
    event.add_to(m);folium.LayerControl().add_to(m)
    west,south,east,north=polygon.bounds;m.fit_bounds([[south,west],[north,east]])
    return m.get_root().render()


def common_footprint(cube):
    import numpy as np
    from rasterio.features import shapes
    from rasterio.transform import Affine
    from rasterio.warp import transform_geom
    from shapely.geometry import shape,mapping
    from shapely.ops import unary_union
    mask=(np.isfinite(cube['hh_power']) & (cube['hh_power']>0) &
          np.isfinite(cube['hv_power']) & (cube['hv_power']>0)).all(axis=0)
    geometries=[shape(g) for g,v in shapes(mask.astype('uint8'),mask=mask,transform=Affine(*cube['transform'])) if v==1]
    if not geometries:return None
    return transform_geom(cube['crs'],'EPSG:4326',mapping(unary_union(geometries)))


def precise_selection(lat,lon,km,cube=None):
    import streamlit as st
    from streamlit.components.v1 import declare_component
    from src.i18n import current_lang
    st.caption(t('ex.globe_approx'));st.caption(t('ex.precise'))
    component=declare_component('nisar_precise_map',path=str(Path(__file__).resolve().parents[1]/'assets/precise_map'))
    html=themed_map_html(selection_map(lat,lon,km,current_lang(),common_footprint(cube) if cube else None))
    picked=component(html=html,key='ex_precise_map',default=None)
    if picked and picked != st.session_state.get('ex_last_precise'):
        st.session_state['ex_last_precise']=picked
        st.session_state['ex_pending']=(picked['lat'],picked['lon'],'custom')
        st.rerun()
