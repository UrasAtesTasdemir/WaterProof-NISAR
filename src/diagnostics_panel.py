"""Small cached diagnostic workspace; production processing is never invoked."""
from datetime import datetime
import json

import numpy as np
import streamlit as st

from src.i18n import t,num,integer,current_lang
from src.scientific_diagnostics import DIRECTORY
from src.theme import palette,tokens
from src.time_axis import mark_gaps,gap_caption
from src.ui import markdown,pyplot,new_figure,table

QUANTITIES=['expansion_km2','recession_km2']


def diagnostics_signature():
    names=('results.json','quality_metadata.json','processing_flags.json')
    return tuple((n,(DIRECTORY/n).stat().st_mtime_ns,(DIRECTORY/n).stat().st_size) for n in names)


@st.cache_data(max_entries=1,show_spinner=False)
def cached_diagnostics(signature):
    result=json.loads((DIRECTORY/'results.json').read_text())
    quality=json.loads((DIRECTORY/'quality_metadata.json').read_text())
    flags=json.loads((DIRECTORY/'processing_flags.json').read_text())
    if result['status']!='success' or len(result['observations'])!=6 or quality['status']!='success':raise ValueError('Incomplete real-data diagnostics.')
    if result['source_layers']['HH']!='/science/LSAR/GCOV/grids/frequencyA/HHHH' or result['source_layers']['HV']!='/science/LSAR/GCOV/grids/frequencyA/HVHV':raise ValueError('Unexpected diagnostic source layers.')
    return result,quality,flags


def render_diagnostics():
    st.title(t('diag.title'))
    st.warning(t('diag.warning'))
    try:
        with st.spinner(t('diag.spinner')):
            result,quality,flags=cached_diagnostics(diagnostics_signature())
    except (OSError,ValueError,KeyError,TypeError):
        st.error(t('diag.error'));return
    pairs=[(p['selected'],p['comparison']) for p in result['pairwise_distributions'] if p['band']=='HH']
    colors=palette()
    with st.sidebar:
        st.header(t('diag.sidebar'))
        bands=['HH','HV'];band=st.selectbox(t('diag.band'),bands,index=bands.index(st.session_state.get('diag_band','HH')),key='diag_band')
        index=st.selectbox(t('diag.interval'),range(len(pairs)),index=st.session_state.get('diag_pair',0),format_func=lambda i:' → '.join(pairs[i]),key='diag_pair')
        st.caption(t('diag.sidebar_note'))
    chosen=next(p for p in result['pairwise_distributions'] if p['band']==band and (p['selected'],p['comparison'])==pairs[index])
    for col,(key,value) in zip(st.columns(3),[('diag.m.median',f"{num(chosen['median'],3)} dB"),('diag.m.mad',f"{num(chosen['scaled_mad'],3)} dB"),('diag.m.area',f"{num(result['common_valid_area_km2'],4)} km²")]):col.metric(t(key),value)
    st.caption(t('diag.chosen',band=band,comparison=chosen['comparison'],selected=chosen['selected'],count=integer(chosen['count'])))
    distributions,methods,sensitivity,noise=st.tabs([t('diag.tab.dist'),t('diag.tab.methods'),t('diag.tab.sens'),t('diag.tab.noise')])
    with distributions:
        fig,ax=new_figure(figsize=(10,3.5))
        for b in ('HH','HV'):
            rows=[r for r in result['temporal_distributions'] if r['band']==b]
            times=[datetime.fromisoformat(o['acquisition_utc'].replace('Z','+00:00')) for o in result['observations']]
            ax.errorbar(times,[r['median'] for r in rows],yerr=[[r['median']-r['p25'] for r in rows],[r['p75']-r['median'] for r in rows]],fmt='o',color=colors[b.lower()],label=t('diag.fig.median',band=b))
        mark_gaps(ax,times)
        ax.set_ylabel(t('diag.fig.ylabel'));ax.set_xlabel(t('diag.fig.xlabel'));ax.legend();ax.grid(alpha=.2)
        pyplot(fig);st.caption(gap_caption(times))
        fig,ax=new_figure(figsize=(10,3))
        h=chosen['histogram'];ax.stairs(h['counts'],h['edges'],color=colors[band.lower()])
        ax.axvline(-3,color=colors['reference_line'],linestyle='--');ax.axvline(3,color=colors['reference_line'],linestyle='--');ax.axvline(chosen['median'],color=colors['median'])
        ax.set_xlabel(t('diag.fig.hist_x',band=band,comparison=chosen['comparison'],selected=chosen['selected']));ax.set_ylabel(t('diag.fig.hist_y'))
        pyplot(fig)
        st.caption(t('diag.tails',below=h['below'],above=h['above']))
        with st.expander(t('diag.pairwise_table')):
            table([{k:v for k,v in p.items() if k!='histogram'} for p in result['pairwise_distributions']])
        region_rows=[{t('diag.col.region'):r['id'],t('diag.col.hh'):r['HH_first_pair_change']['median'],t('diag.col.hv'):r['HV_first_pair_change']['median'],t('diag.col.row'):r['row'],t('diag.col.column'):r['column']} for r in result['candidate_stable_regions']]
        st.subheader(t('diag.quiet'))
        table(region_rows)
        st.caption(t('diag.quiet_caption'))
    with methods:
        c=result['comparison']
        st.markdown(t('diag.fixed'))
        rows=[{t('diag.col.gate'):t('diag.gate.fixed'),t('diag.col.expansion'):c['baseline_expansion_km2'],t('diag.col.recession'):c['baseline_recession_km2']},
              {t('diag.col.gate'):t('diag.gate.scaled'),t('diag.col.expansion'):c['alternative_expansion_km2'],t('diag.col.recession'):c['alternative_recession_km2']}]
        table(rows)
        fig,ax=new_figure(figsize=(9,3));x=np.arange(2)
        ax.bar(x-.16,[c['baseline_expansion_km2'],c['alternative_expansion_km2']],.32,label=t('diag.fig.expansion'),color=colors['expansion'])
        ax.bar(x+.16,[c['baseline_recession_km2'],c['alternative_recession_km2']],.32,label=t('diag.fig.recession'),color=colors['recession'])
        ax.set_xticks(x,[t('diag.fig.fixed'),t('diag.fig.scaled')]);ax.set_ylabel(t('diag.fig.km2'));ax.legend();pyplot(fig)
        st.code('S = (after_dB − before_dB) / max(1.4826 × MAD(other four dates), 1 dB)\nDiagnostic gate: |S| ≥ 3; all four reference dates must be finite')
        st.markdown(t('diag.reference_scale'))
        st.caption(t('diag.retrospective'))
        st.info(t('diag.effective',median=num(c['effective_gate_db']['median'],3),p95=num(c['effective_gate_db']['p95'],3)))
    with sensitivity:
        quantity=st.selectbox(t('diag.quantity'),QUANTITIES,index=QUANTITIES.index(st.session_state.get('diag_quantity',QUANTITIES[0])),key='diag_quantity',
                              format_func=lambda q,lang=current_lang():t(f'diag.q.{q}',lang=lang))
        fig,ax=new_figure(figsize=(9,3.4))
        for size in (1,3,5):
            rows=sorted([r for r in result['sensitivity'] if r['filter_size']==size],key=lambda r:r['water_threshold_db'])
            ax.plot([r['water_threshold_db'] for r in rows],[r[quantity] for r in rows],'o-',label=t('diag.fig.filter',size=size))
        ax.set_xlabel(t('diag.fig.threshold'));ax.set_ylabel(t('diag.fig.area'));ax.legend();pyplot(fig)
        with st.expander(t('diag.sens_table')):
            table(result['sensitivity'])
        st.caption(t('diag.sens_caption'))
        stability=result['stability']
        st.write(t('diag.stability',any=num(stability['expansion_in_any_km2'],4),all=num(stability['expansion_in_all_km2'],4)))
        baseline_pixels=int(round(result['comparison']['baseline_expansion_km2']/(result['common_valid_area_km2']/result['common_valid_pixels'])))
        st.write(t('diag.waterways',near=stability['baseline_expansion_within_30m_waterway_pixels'],total=baseline_pixels))
        families=DIRECTORY/'stability_families.json'
        if families.exists():
            with st.expander(t('diag.families')):
                table(json.loads(families.read_text())['families'])
                st.caption(t('diag.families_caption'))
    with noise:
        st.subheader(t('diag.metadata'))
        table([{t('diag.col.date'):e['date'],t('diag.col.looks_med'):e['layers']['numberOfLooks'].get('median'),t('diag.col.looks_min'):e['layers']['numberOfLooks'].get('min'),
                t('diag.col.looks_max'):e['layers']['numberOfLooks'].get('max'),t('diag.col.codes'):str(e['layers']['mask'].get('observed_common_codes'))} for e in quality['observations']])
        st.caption(t('diag.looks_caption'))
        texture_rows=[dict(Region=x['region'],Band=x['band'],Date=x['date'],CV_raw=x['raw'].get('cv'),CV_filtered=x['filtered_cv'],Lag1=x['raw'].get('lag1_max_abs'),Conditional_ENL=x['raw'].get('enl')) for x in result['local_texture'] if x['date'] in ('2026-06-21','2026-07-03')]
        with st.expander(t('diag.texture_table')):
            table(texture_rows)
        markdown(t('diag.texture'))
        markdown(t('diag.hv_floor'))
        markdown(t('diag.limits'))
        with st.expander(t('diag.flags')):
            st.json({'processing_flags':flags,'quality_scope':'Only June21/July3 quality metadata inspected; six dates used for cached radar statistics.','original_pipeline_unchanged':True})
        st.markdown('[Official GCOV guide](https://nisar-docs.asf.alaska.edu/gcov/) · [MAD definition](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.median_abs_deviation.html)')
