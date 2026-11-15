"""WaterProof: cached research examples plus optional authenticated live exploration.

Seven pages (src/navigation.py) inside one shell (src/shell.py: sidebar page list,
team dialog, language flags and theme switch). The Louisiana case-study
dashboard below is the original application, unchanged in behaviour; its other
analysis views are selected with the sidebar 'Louisiana view' selector.
All text goes through src/i18n.py (English / Turkish)."""
import os
from importlib import import_module
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
import numpy as np
from rasterio.transform import array_bounds
import streamlit as st
from src.dashboard_data import input_signature,prepare_data,calculate,sensitivity
from src.navigation import APP_NAME,go_to
from src.shell import render_shell
from src.i18n import t,num,integer
from src.theme import palette,themed_map_html
from src.ui import markdown,pyplot,new_figure,table

st.set_page_config(page_title=APP_NAME,page_icon='🧭',layout='wide')
target=render_shell()
RENDERERS={'Explore the world':('src.explore_panel','render_explore'),
           'Researcher workflow':('src.workflow_panel','render_workflow'),
           'Is this scene analyzable?':('src.visibility_panel','render_visibility'),
           'Flood validation (Thailand, Gandak)':('src.flood_panel','render_flood'),
           'Benchmark Validation (Sentinel-1)':('src.benchmark_panel','render_benchmark'),
           'About':('src.about_panel','render_about'),
           # Louisiana case-study views (selected with 'case_view')
           'Change Compass':('src.compass_panel','render_compass'),
           'Evidence & limitations':('src.evidence_panel','render_evidence'),
           'Investigation Explorer':('src.investigation_panel','render_investigation'),
           'Scientific Diagnostics':('src.diagnostics_panel','render_diagnostics'),
           'Polarization Analysis':('src.polarization_panel','render_polarization'),
           'HH time series (six dates)':('src.time_series_panel','render_time_series'),
           'Geographic map (NISAR)':('src.geographic_panel','render_geographic')}
if target in RENDERERS:
    module,function=RENDERERS[target]
    getattr(import_module(module),function)()
    st.stop()
st.caption(t('common.challenge'))
st.title(t('dash.title'))
markdown(t('dash.intro',app=APP_NAME))
st.button(t('dash.open_workflow'),key='case_go_workflow',on_click=go_to,args=('Researcher workflow',))
st.warning(t('dash.warning'))

@st.cache_data(show_spinner=False,max_entries=2)
def cached_data(signature):
    return prepare_data()

try:
    with st.spinner(t('dash.spinner')):
        data=cached_data(input_signature())
except (FileNotFoundError,ValueError,KeyError,StopIteration,OSError,TypeError) as exc:
    st.error(t('dash.error',error=type(exc).__name__))
    st.stop()
with st.sidebar:
    st.header(t('dash.explore'))
    st.caption(t('dash.two_obs'))
    threshold=st.slider(t('dash.threshold'),-22.,-12.,-16.,.5,key='water_threshold',help=t('dash.threshold_help'))
    minimum=st.slider(t('dash.minimum'),0.,8.,3.,.5,key='minimum_change',help=t('dash.minimum_help'))
    remove_singletons=st.toggle(t('dash.singletons'),value=False,key='remove_singletons',help=t('dash.singletons_help'))
    st.caption(t('dash.fixed'))
    st.info(t('dash.sensitivity_info'))
    st.caption(t('dash.grid_note'))
try:
    result=calculate(data,threshold,minimum,remove_singletons)
except ValueError as exc:
    st.error(str(exc));st.stop()
st.caption(t('dash.dates'))
for col,key in zip(st.columns(4),('expansion','recession','net','valid_area')):
    col.metric(t(f'dash.metric.{key}'),f"{num(result[key],4)} km²")
st.caption(t('dash.settings',threshold=num(threshold,1).rstrip('0').rstrip(',.'),minimum=num(minimum,1).rstrip('0').rstrip(',.'),pixels=integer(data["valid"].sum())))
if remove_singletons:
    st.info(t('dash.filter_on',count=result["suppressed_pixels"]))
with st.expander(t('dash.interpretation')):
    median_change=float(np.median(result['delta'][data['valid']]))
    markdown(t('dash.interpretation_text',median=num(median_change,2)))
geo_tab,map_tab,sensitivity_tab,source_tab=st.tabs([t('dash.tab.geo'),t('dash.tab.radar'),t('dash.tab.sensitivity'),t('dash.tab.source')])
colors=palette()['classes']

def radar_plot(array,kind):
    fig,ax=new_figure(figsize=(7,3.7))
    west,south,east,north=array_bounds(*array.shape,data['grid']['transform'])
    cmap=plt.get_cmap('RdBu_r' if kind=='difference' else 'gray').copy();cmap.set_bad(colors[0])
    if kind=='classes':
        opts=dict(cmap=ListedColormap(colors),norm=BoundaryNorm(np.arange(-.5,5.5),5))
    elif kind=='difference':
        limit=max(1.,float(np.percentile(np.abs(result['delta'][data['valid']]),98)))
        opts=dict(cmap=cmap,vmin=-limit,vmax=limit)
    else:
        lo,hi=np.percentile(np.concatenate([data['before'][data['valid']],data['after'][data['valid']]]),[2,98])
        opts=dict(cmap=cmap,vmin=lo,vmax=max(hi,lo+.01))
    im=ax.imshow(array,extent=(west,east,south,north),origin='upper',interpolation='nearest',**opts)
    ax.set_xlabel(t('dash.easting'),fontsize=8);ax.set_ylabel(t('dash.northing'),fontsize=8)
    ax.ticklabel_format(useOffset=False,style='plain');ax.tick_params(labelsize=7)
    if kind!='classes':fig.colorbar(im,ax=ax,shrink=.8,label='Δ dB' if kind=='difference' else t('dash.gamma0'))
    return fig

@st.cache_data(max_entries=8,show_spinner=False)
def cached_case_map(signature,threshold,minimum,remove_singletons,classes):
    from src.case_map import classes_map_html
    return classes_map_html(classes,data['valid'],data['grid'],int(data['valid'].sum())*data['pixel_area'])

with geo_tab:
    try:
        st.iframe(themed_map_html(cached_case_map(input_signature(),threshold,minimum,remove_singletons,result['classes'])),height=560)
        st.caption(t('dash.geo_caption'))
    except (ValueError,OSError) as exc:
        st.info(t('dash.geo_missing',error=type(exc).__name__))
with map_tab:
    entries=[('before','radar',data['before']),('after','radar',data['after']),('difference','difference',result['delta']),('classes','classes',result['classes'])]
    for start in (0,2):
        for col,(key,kind,array) in zip(st.columns(2),entries[start:start+2]):
            with col:
                st.subheader(t(f'dash.panel.{key}'));st.caption(t(f'dash.panel.{key}_caption'))
                pyplot(radar_plot(array,kind))
    st.caption(t('dash.legend'))
    st.caption(t('dash.scale'))
with sensitivity_tab:
    st.subheader(t('dash.sens_title'))
    st.write(t('dash.sens_text'))
    rows=sensitivity(data,minimum,remove_singletons)
    fig,ax=new_figure(figsize=(10,3.6));line_colors=palette()
    for field,key,color in [('Expansion (km²)','dash.sens.expansion',line_colors['expansion']),('Recession (km²)','dash.sens.recession',line_colors['recession'])]:
        ax.plot([r['Threshold (dB)'] for r in rows],[r[field] for r in rows],marker='.',label=t(key),color=color)
    ax.axvline(threshold,color=line_colors['first'],linestyle='--',label=t('dash.sens.selected'))
    ax.set_xlabel(t('dash.sens.xlabel'));ax.set_ylabel(t('dash.sens.ylabel'));ax.legend()
    pyplot(fig)
    with st.expander(t('dash.sens_table')):
        table(rows)
    st.caption(t('dash.sens_caption'))
with source_tab:
    st.subheader(t('dash.source_title'))
    with st.expander(t('dash.source_table')):
        table([{'Acquisition (UTC)':s['date_utc'],'Product ID':s['product_id'],'Polarization':t('dash.source.pol'),'Product':'NISAR L2 GCOV Provisional','Local source':s['path']} for s in data['sources']])
        st.code(data['manifest']['aoi_wkt'],language=None)
    st.write(t('dash.aoi'))
    st.caption(t('dash.checked'))
    if data['quality']:
        q=data['quality'];near=q['historical_hydrography_proximity']['explicit_canal_ditch_or_stream_river']['expansion_within_30m_pixels']
        count=next(r['expansion_pixels'] for r in q['threshold_sensitivity'] if r['water_threshold_db']==-16)
        st.info(t('dash.quality',near=near,count=count))
    else:st.info(t('dash.quality_missing'))
    st.markdown(t('dash.links'))
    for item in data['manifest']['observations']:
        st.markdown(t('dash.product_link',date=item['start_time_utc'][:10],url=item['download_url']))
with st.expander(t('dash.method')):
    markdown(t('dash.method_text'))
st.caption(t('dash.footer',app=APP_NAME))
