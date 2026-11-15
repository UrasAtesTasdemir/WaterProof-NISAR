"""Optional geographic view of already processed NISAR windows."""
import streamlit as st

from src.geographic_map import ROOT,load_geographic,build_map
from src.i18n import t,num
from src.theme import themed_map_html


@st.cache_data(max_entries=2,show_spinner=False)
def cached_geographic(directory,signature):
    meta,display,bounds,footprint=load_geographic(directory)
    return meta,build_map(meta,display,bounds,footprint)


def render_geographic():
    st.title(t('geo.title'))
    st.warning(t('geo.warning'))
    st.caption(t('geo.caption'))
    base=ROOT/'data/geographic_mapping'
    options=[name for name in ('5km','10km') if (base/name/'results.json').exists()]
    if not options:
        st.error(t('geo.none'));return
    name=st.sidebar.selectbox(t('geo.coverage'),options,index=len(options)-1,key='map_coverage')
    directory=base/name
    try:
        signature=tuple((f.name,f.stat().st_mtime_ns,f.stat().st_size) for f in (directory/'classes.tif',directory/'results.json'))
        with st.spinner(t('geo.spinner')):
            meta,html=cached_geographic(str(directory),signature)
    except (OSError,ValueError,KeyError) as exc:
        st.error(t('geo.error',error=type(exc).__name__));return
    for col,(key,value) in zip(st.columns(3),[('geo.m.expansion',meta['areas']['2']['area_km2']),('geo.m.recession',meta['areas']['3']['area_km2']),('geo.m.valid',meta['valid_comparison_area_km2'])]):
        col.metric(t(key),f'{num(value,4)} km²')
    st.caption(t('geo.requested',size=meta['requested_size_km']))
    st.iframe(themed_map_html(html),height=650,alt=t('geo.alt'))
    st.caption(t('geo.howto'))
    st.info(t('geo.internet'))
    with st.expander(t('geo.provenance')):
        st.json({'native_crs':meta['crs'],'resolution_m':meta['resolution_m'],'raster_shape':meta['shape'],'product_ids':[o['product_id'] for o in meta['observations']],'processing_seconds':meta['elapsed_seconds'],'full_HDF5_downloaded':False})
