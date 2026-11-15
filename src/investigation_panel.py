"""Optional investigator workflow over cached descriptive region summaries."""
from datetime import datetime
import html
import json

import folium
import streamlit as st

from src.i18n import t,num,current_lang,saved_text
from src.investigation import DIRECTORY,load_investigations,markdown_report
from src.theme import palette,themed_map_html
from src.time_axis import mark_gaps,gap_caption
from src.ui import markdown,pyplot,new_figure,table


def investigation_signature():
    files=[DIRECTORY/'results.json',DIRECTORY/'regions.geojson']
    if files[0].exists():
        from src.investigation import ROOT
        source=json.loads(files[0].read_text())
        files += [ROOT/name for name in source['source_fingerprints']]
    return tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in files)


@st.cache_data(max_entries=1,show_spinner=False)
def cached_investigations(signature):
    return load_investigations()


def investigation_map(report,selected_id,lang='en', *, change_overlay=None, waterways=None, focus_selected=False):
    from shapely.geometry import shape
    footprint=shape(report['common_footprint']);west,south,east,north=footprint.bounds
    m=folium.Map(location=[(south+north)/2,(west+east)/2],tiles='OpenStreetMap',control_scale=True)
    if change_overlay is not None:
        rgba,bounds,title=change_overlay
        folium.raster_layers.ImageOverlay(rgba,bounds=bounds,name=title,opacity=.55,origin='upper').add_to(m)
    if waterways and waterways['features']:
        folium.GeoJson(waterways,name=t('ux.waterways',lang=lang),
            style_function=lambda f:dict(color='#297cce',weight=2,opacity=.85),
            tooltip=t('ux.waterway_tip',lang=lang)).add_to(m)
    folium.GeoJson(report['common_footprint'],name=t('inv.map.footprint',lang=lang),
        style_function=lambda f:dict(color='#12334a',weight=2,fillOpacity=0),
        tooltip=t('inv.map.footprint_tip',lang=lang,area=num(report['common_valid_area_km2'],4,lang=lang))).add_to(m)
    group=folium.FeatureGroup(name=t('inv.map.group',lang=lang),show=True)
    for r in report['regions']:
        color='#d17f22' if r['id']==selected_id else '#007f83'
        label=t('inv.map.label',lang=lang,id=r['id'],area=num(r['area_km2'],4,lang=lang),count=r['recurrence_count'])
        folium.GeoJson(r['geometry'],name=t('inv.region',lang=lang,id=r['id']),style_function=lambda f,c=color:dict(color=c,weight=3,fillColor=c,fillOpacity=.35),
                       tooltip=label,popup=folium.Popup(html.escape(label)+'<br>'+html.escape(t('inv.map.popup',lang=lang)),max_width=260)).add_to(group)
        icon=folium.DivIcon(html=f'<div style="background:{color};color:white;border:2px solid white;border-radius:50%;width:27px;height:27px;text-align:center;line-height:24px;font:bold 14px sans-serif">{r["id"]}</div>',icon_size=(29,29),icon_anchor=(14,14))
        folium.Marker([r['representative_latitude'],r['representative_longitude']],icon=icon,tooltip=label).add_to(group)
    group.add_to(m);folium.LayerControl(collapsed=focus_selected).add_to(m)
    # Start close enough to inspect small regions; the full real processed
    # boundary remains available by zooming out and in the layer control.
    if report['regions']:
        from shapely.ops import unary_union
        west,south,east,north=unary_union([shape(r['geometry']) for r in report['regions']]).bounds
    if focus_selected:
        r=next(r for r in report['regions'] if r['id']==selected_id)
        west,south,east,north=shape(r['geometry']).bounds
        west-=.0025; east+=.0025; south-=.002; north+=.002
        folium.LatLngPopup().add_to(m)
    m.fit_bounds([[south,west],[north,east]])
    legend=f'''<div style="position:fixed;bottom:22px;left:10px;z-index:9999;background:white;padding:10px;border:1px solid #aaa;border-radius:8px;font:12px sans-serif;max-width:240px">
    {t('ux.map_legend' if focus_selected else 'inv.map.legend',lang=lang)}</div>'''
    m.get_root().html.add_child(folium.Element(legend));return m.get_root().render()


@st.cache_data(max_entries=10,show_spinner=False)
def cached_investigation_map(signature,selected_id,lang):
    return investigation_map(cached_investigations(signature),selected_id,lang)


def render_investigation():
    lang=current_lang()
    st.title(t('inv.title'))
    st.warning(t('inv.warning'))
    st.caption(t('inv.caption'))
    try:
        signature=investigation_signature()
        with st.spinner(t('inv.spinner')):
            report=cached_investigations(signature)
    except (OSError,ValueError,KeyError,TypeError):
        st.error(t('inv.error'));return
    regions=report['regions']
    if not regions:
        st.info(t('inv.none'))
        st.json(report['settings']);return
    choices=[r['id'] for r in regions];previous=st.session_state.get('investigation_region',choices[0])
    if previous not in choices:st.session_state['investigation_region']=choices[0];previous=choices[0]
    selected=st.sidebar.selectbox(t('inv.select'),choices,index=choices.index(previous),format_func=lambda i,lang=lang:t('inv.region',lang=lang,id=i),key='investigation_region')
    r=next(r for r in regions if r['id']==selected)
    st.sidebar.caption(t('inv.select_note'))
    for col,(key,value) in zip(st.columns(3),[('inv.m.area',f"{num(r['area_km2'],4)} km²"),('inv.m.notable',f"{r['recurrence_count']}/5"),('inv.m.common',f"{num(report['common_valid_area_km2'],4)} km²")]):col.metric(t(key),value)
    st.caption(t('inv.point',id=r['id'],lon=f"{r['representative_longitude']:.6f}",lat=f"{r['representative_latitude']:.6f}",pixels=r['pixels']))
    st.iframe(themed_map_html(cached_investigation_map(signature,selected,lang)),height=530,alt=t('inv.map.alt'))
    st.caption(t('inv.map_caption',area=num(report['common_valid_area_km2'],4)))
    st.subheader(t('inv.why',id=r['id']))
    st.write(saved_text(r['selection_reason']));st.write(saved_text(r['observed_HH_HV_pattern']))
    st.caption(t('inv.ranges',hh=num(r['HH_median_pixel_temporal_range_db'],3),hv=num(r['HV_median_pixel_temporal_range_db'],3)))
    st.info(t('inv.adjacent'))
    st.subheader(t('inv.chart_title'))
    fig,ax=new_figure(figsize=(10,3.5));colors=palette()
    times=[datetime.fromisoformat(x['acquisition_utc'].replace('Z','+00:00')) for x in r['temporal_statistics']]
    for band in ('HH','HV'):
        rows=r['temporal_statistics'];med=[x[band+'_median_db'] for x in rows]
        ax.errorbar(times,med,yerr=[[x[band+'_median_db']-x[band+'_p25_db'] for x in rows],[x[band+'_p75_db']-x[band+'_median_db'] for x in rows]],fmt='o',color=colors[band.lower()],label=t('inv.fig.median',band=band))
    mark_gaps(ax,times)
    ax.set_ylabel(t('inv.fig.ylabel'));ax.set_xlabel(t('inv.fig.xlabel'));ax.legend();ax.grid(alpha=.2)
    pyplot(fig);st.caption(gap_caption(times))
    st.caption(t('inv.chart_caption'))
    with st.expander(t('inv.stats_table')):
        table(r['temporal_statistics'])
    with st.expander(t('inv.dates')):
        table(r['notable_intervals'])
        st.caption(t('inv.dates_caption'))
        table(r['post_seed_departures'])
        st.write(t('inv.longest',n=r['longest_run_of_observed_shifted_dates']))
    with st.expander(t('inv.sensitivity')):
        table(r['sensitivity'])
        counts=[s['retained_pixels'] for s in r['sensitivity']]
        st.write(t('inv.retained',low=min(counts),high=max(counts),pixels=r['pixels']))
        st.caption(t('inv.variants'))
        st.write(saved_text(r['possible_interpretations']))
        st.write(t('inv.next')+saved_text(r['suggested_next_step']))
        st.caption(t('inv.phase4',support=r['original_pair_temporal_scaled_gate_support_pixels'],pixels=r['pixels']))
    with st.expander(t('inv.rules')):
        st.json(report['settings']);st.write(saved_text(report['ranking_rule']))
        markdown(t('inv.rules_text'))
        for limit in report['limitations']:st.write('• '+saved_text(limit))
        st.json(report['source_layers'])
    export=markdown_report(r,report)
    st.download_button(t('inv.download'),data=export,file_name=f"change_compass_region_{r['id']}_investigation.md",mime='text/markdown',key='investigation_export')
    st.caption(t('inv.export_caption'))
