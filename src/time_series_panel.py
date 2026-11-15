"""Optional offline scientific time-series workspace; no credential handling."""
from datetime import datetime

import numpy as np
import streamlit as st
from shapely import wkt

from src.i18n import t, num, integer, current_lang
from src.theme import palette, themed_map_html
from src.time_series import DIRECTORY, load_time_series, pair_difference, point_series
from src.time_series_map import build_time_map
from src.time_axis import mark_gaps, gap_caption
from src.ui import markdown, pyplot, new_figure, table
from src.water_change import pixel_area_km2

LAYERS = ['Selected observation', 'Comparison observation', 'Comparison − selected (dB)', 'Selected anomaly (dB)']


def file_signature():
    return tuple((p.name,p.stat().st_mtime_ns,p.stat().st_size) for p in (
        DIRECTORY/'hh_db.tif',DIRECTORY/'results.json',DIRECTORY/'common_footprint.geojson'))


@st.cache_data(max_entries=1, show_spinner=False)
def cached_time_data(signature):
    return load_time_series()


@st.cache_data(max_entries=8, show_spinner=False)
def cached_time_map(signature, first, second, layer, lon, lat, radius):
    data = cached_time_data(signature)
    point = point_series(data, lon, lat, radius)
    return build_time_map(data, first, second, layer, point)


def render_time_series():
    st.title(t('ts.title'))
    st.warning(t('ts.warning'))
    st.caption(t('ts.caption'))
    try:
        signature = file_signature()
        with st.spinner(t('ts.spinner')):
            data = cached_time_data(signature)
    except (OSError,ValueError,KeyError,TypeError):
        st.error(t('ts.error')); return
    report = data['report']; observations = report['observations']
    dates = [o['date'] for o in observations]
    with st.sidebar:
        st.header(t('ts.sidebar'))
        # Explicit current defaults keep the browser and server consistent when
        # these conditional widgets are recreated after another workspace.
        first = st.selectbox(t('ts.first'), range(6), index=st.session_state.get('ts_first',0), format_func=lambda i:dates[i], key='ts_first')
        second = st.selectbox(t('ts.second'), range(6), index=st.session_state.get('ts_second',1), format_func=lambda i:dates[i], key='ts_second')
        layer = st.selectbox(t('ts.layer'), LAYERS, index=LAYERS.index(st.session_state.get('ts_layer',LAYERS[0])), key='ts_layer',
                             format_func=lambda name, lang=current_lang(): t(f'ts.layer.{LAYERS.index(name)}', lang=lang))
        st.caption(t('ts.sidebar_note'))
    delta, pair_valid = pair_difference(data['db'], first, second)
    cell = pixel_area_km2(data['grid']['crs'],data['grid']['transform'])
    for col,(key,value) in zip(st.columns(3), [('ts.m.obs','6'),('ts.m.common',f"{num(report['common_valid_area_km2'],4)} km²"),
                                               ('ts.m.pair',f'{num(pair_valid.sum()*cell,4)} km²')]):
        col.metric(t(key),value)
    st.caption(t('ts.selected', first=observations[first]['acquisition_utc'], second=observations[second]['acquisition_utc']))
    if first == second: st.info(t('ts.identical'))
    st.subheader(t('ts.point_title'))
    center = wkt.loads(report['aoi_wkt']).centroid
    with st.form('time_point_form'):
        cols = st.columns(2)
        lon = cols[0].number_input(t('ts.lon'),min_value=-180.,max_value=180.,value=float(st.session_state.get('ts_lon',center.x)),step=.001,format='%.6f',key='ts_lon')
        lat = cols[1].number_input(t('ts.lat'),min_value=-90.,max_value=90.,value=float(st.session_state.get('ts_lat',center.y)),step=.001,format='%.6f',key='ts_lat')
        radius = st.selectbox(t('ts.neighborhood'), [0,1,2],index=st.session_state.get('ts_radius',0),format_func=lambda r,lang=current_lang():t('ts.pixels',lang=lang,n=2*r+1),key='ts_radius')
        st.form_submit_button(t('ts.apply'))
    try:
        point = point_series(data,lon,lat,radius)
    except ValueError as exc:
        st.error(str(exc)); return
    st.caption(t('ts.sampled', lon=f'{lon:.6f}', lat=f'{lat:.6f}', plon=f"{point['pixel_center_longitude']:.6f}",
                 plat=f"{point['pixel_center_latitude']:.6f}", row=point['row'], col=point['column']))
    st.iframe(themed_map_html(cached_time_map(signature,first,second,layer,lon,lat,radius)),height=580,alt=t('ts.map_alt'))
    st.caption(t('ts.map_caption'))
    st.subheader(t('ts.chart_title'))
    colors = palette()
    values = [r['HH backscatter (dB)'] if r['HH backscatter (dB)'] is not None else np.nan for r in point['rows']]
    times = [datetime.fromisoformat(r['Acquisition UTC'].replace('Z','+00:00')) for r in point['rows']]
    fig,ax = new_figure(figsize=(10,3.4))
    # Points, not interpolated curves: six irregular dates cannot resolve intervening events.
    ax.plot(times,values,'o',color=colors['hh'],label=t('ts.fig.median'))
    for idx,color,key in ((first,colors['first'],'ts.fig.selected'),(second,colors['second'],'ts.fig.comparison')):
        ax.axvline(times[idx],color=color,linestyle='--',alpha=.75,label=t(key))
    mark_gaps(ax, times)
    ax.set_ylabel(t('ts.fig.ylabel')); ax.set_xlabel(t('ts.fig.xlabel')); ax.grid(alpha=.2); ax.legend(fontsize=8)
    pyplot(fig); st.caption(gap_caption(times))
    available = sum(r['Status']=='valid' for r in point['rows'])
    st.caption(t('ts.available', available=available, missing=6-available))
    with st.expander(t('ts.point_table')):
        table(point['rows'])
    with st.expander(t('ts.method')):
        table([{k:v for k,v in o.items() if k!='source_verification'} for o in observations])
        st.caption(t('ts.method_caption'))
        markdown(t('ts.method_text'))
        st.markdown('[NASA polarimetry](https://science.nasa.gov/mission/nisar/polarimetry/) · [Official ASF Cookbook](https://asfopensarlab.github.io/NISAR_Cookbook/search-stream-nisar-asf-search/)')
