"""Optional HH/HV exploration. All scientific arrays are local, never credentials."""
import html
from datetime import datetime

import folium
import streamlit as st
from rasterio.features import shapes
from rasterio.warp import transform_geom
from shapely.geometry import shape,mapping
from shapely.ops import unary_union

from src.i18n import t,num,integer,saved_text
from src.polarization import DIRECTORY,load_polarization,compare_polarizations
from src.theme import palette,themed_map_html
from src.time_series_map import continuous_display
from src.time_axis import mark_gaps,gap_caption
from src.ui import markdown,pyplot,new_figure,table
from src.water_change import pixel_area_km2
from scripts.process_polarization import draw_comparison,draw_change_relation

BANDS=['HH','HV','HH/HV power ratio (dB)']


def polarization_inputs():
    folder=next((DIRECTORY/n for n in ('six_date','two_date') if (DIRECTORY/n/'results.json').exists()),DIRECTORY/'two_date')
    names=('results.json','hh_db.tif','hv_db.tif','hh_hv_ratio_db.tif')
    signature=tuple((n,(folder/n).stat().st_mtime_ns,(folder/n).stat().st_size) for n in names)
    return str(folder),signature


@st.cache_data(max_entries=2,show_spinner=False)
def cached_pol_data(folder,signature):
    return load_polarization(folder)


def polarization_map(data,band,index,lang='en'):
    values=data[band][index];report=data['report'];date=report['observations'][index]['date']
    if band=='ratio_db':low,high=0.,15.;label=t('pol.ratio_label',lang=lang);palette_name='viridis'
    else:low,high=report['backscatter_scale_db'];label=t('pol.band_label',lang=lang,band=band);palette_name='gray'
    rgba,bounds=continuous_display(values,data['grid'],low,high,palette_name,max_pixels=640)
    m=folium.Map(location=[(bounds[0][0]+bounds[1][0])/2,(bounds[0][1]+bounds[1][1])/2],tiles='OpenStreetMap',control_scale=True)
    folium.raster_layers.ImageOverlay(rgba,bounds=bounds,name=date+' '+label,opacity=.85,origin='upper').add_to(m)
    common=data['common'];grid=data['grid']
    footprint=unary_union([shape(g) for g,v in shapes(common.astype('uint8'),mask=common,transform=grid['transform']) if v==1])
    folium.GeoJson(transform_geom(grid['crs'],'EPSG:4326',mapping(footprint)),name=t('pol.footprint',lang=lang),
        style_function=lambda f:dict(color='#00a892',weight=2,fillOpacity=0)).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m);m.fit_bounds(bounds)
    legend=f'''<div style="position:fixed;bottom:22px;left:10px;z-index:9999;background:white;padding:9px;border:1px solid #aaa;font:11px sans-serif;max-width:210px">
    <b>{html.escape(date+' · '+label)}</b><br>{html.escape(t('pol.legend_range',lang=lang,low=num(low,1,lang=lang),high=num(high,1,lang=lang)))}<br>
    {html.escape(t('pol.legend_dark' if band!='ratio_db' else 'pol.legend_ratio',lang=lang))}<br>
    {html.escape(t('pol.legend_nodata',lang=lang))}<br>{html.escape(t('pol.legend_note',lang=lang))}</div>'''
    m.get_root().html.add_child(folium.Element(legend));return m.get_root().render()


@st.cache_data(max_entries=8,show_spinner=False)
def cached_pol_map(folder,signature,band,index,lang):
    return polarization_map(cached_pol_data(folder,signature),band,index,lang)


def render_polarization():
    from src.i18n import current_lang
    lang=current_lang()
    st.title(t('pol.title'))
    st.warning(t('pol.warning'))
    st.caption(t('pol.caption'))
    try:
        folder,signature=polarization_inputs()
        with st.spinner(t('pol.spinner')):
            data=cached_pol_data(folder,signature)
    except (OSError,ValueError,KeyError,TypeError):
        st.error(t('pol.error'));return
    report=data['report'];rows=report['observations'];n=len(rows);dates=[o['date'] for o in rows]
    for key,default in (('pol_first',0),('pol_second',1)):
        if st.session_state.get(key,default) not in range(n):st.session_state[key]=default
    with st.sidebar:
        st.header(t('pol.sidebar'))
        first=st.selectbox(t('pol.first'),range(n),index=st.session_state.get('pol_first',0),format_func=lambda i:dates[i],key='pol_first')
        second=st.selectbox(t('pol.second'),range(n),index=st.session_state.get('pol_second',1),format_func=lambda i:dates[i],key='pol_second')
        selected=st.selectbox(t('pol.band'),BANDS,index=BANDS.index(st.session_state.get('pol_band','HV')),key='pol_band',
                              format_func=lambda b,lang=lang:t('pol.ratio_label',lang=lang) if b==BANDS[2] else b)
        st.caption(t('pol.sidebar_note'))
    band={'HH':'HH','HV':'HV','HH/HV power ratio (dB)':'ratio_db'}[selected]
    pair=compare_polarizations(data,first,second);stats=pair['statistics']
    cell=pixel_area_km2(data['grid']['crs'],data['grid']['transform'])
    for col,(key,value) in zip(st.columns(3),[('pol.m.area',f"{num(stats['pixels']*cell,4)} km²"),('pol.m.dhh',f"{num(stats['median_HH_delta_db'],3)} dB"),('pol.m.dhv',f"{num(stats['median_HV_delta_db'],3)} dB")]):
        col.metric(t(key),value)
    st.caption(t('pol.selected',n=n,first=rows[first]['acquisition_utc'],second=rows[second]['acquisition_utc'],area=num(report['common_valid_area_km2'],4)))
    if first==second:st.info(t('pol.identical'))
    st.subheader(t('pol.geo_title'))
    if band=='ratio_db':st.info(t('pol.ratio_info'))
    for col,index,role in zip(st.columns(2),(first,second),('selected','comparison')):
        with col:
            st.caption(t(f'pol.role.{role}')+f': {dates[index]} · '+(t('pol.ratio_label') if band=='ratio_db' else selected))
            st.iframe(themed_map_html(cached_pol_map(folder,signature,band,index,lang)),height=430,alt=t(f'pol.role.{role}')+' · Louisiana')
    st.caption(t('pol.maps_caption'))
    st.subheader(t('pol.change_title'))
    pyplot(draw_comparison(data,first,second))
    with st.expander(t('pol.relation')):
        pyplot(draw_change_relation(pair))
        correlation=t('pol.undefined') if stats['spatial_Pearson_r'] is None else num(stats['spatial_Pearson_r'],3)
        st.caption(t('pol.pearson',r=correlation,pixels=integer(stats['pixels']),diff=num(stats['median_delta_HH_minus_delta_HV_db'],3)))
        fig,ax=new_figure(figsize=(10,3));colors=palette()
        times=[datetime.fromisoformat(r['acquisition_utc'].replace('Z','+00:00')) for r in rows]
        for b in ('HH','HV'):
            ax.plot(times,[r[b+'_median_db'] for r in rows],'o',color=colors[b.lower()],label=t('pol.fig.median',band=b))
        mark_gaps(ax,times)
        ax.set_ylabel(t('pol.fig.ylabel'));ax.set_xlabel(t('pol.fig.xlabel'));ax.legend();ax.grid(alpha=.2)
        pyplot(fig);st.caption(gap_caption(times));table(rows)
        st.caption(t('pol.stats_caption'))
    with st.expander(t('pol.physics')):
        markdown(t('pol.physics_text'))
        st.code('HH: /science/LSAR/GCOV/grids/frequencyA/HHHH\nHV: /science/LSAR/GCOV/grids/frequencyA/HVHV\nPower units: 1 (linear gamma-0); display: 10*log10(power) dB')
        table([{'Acquisition UTC':o['acquisition_utc'],'Product ID':o['product_id']} for o in rows])
        st.markdown('[NASA polarimetry](https://science.nasa.gov/mission/nisar/polarimetry/) · [ASF GCOV product guide](https://nisar-docs.asf.alaska.edu/gcov/)')
