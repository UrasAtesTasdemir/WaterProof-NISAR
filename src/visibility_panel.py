"""'Is this scene analyzable?' page — cached catalog results only."""
from datetime import timedelta

import matplotlib.dates as mdates
import streamlit as st

from src.i18n import t, num, integer, percent, current_lang, saved_text
from src.theme import palette
from src.time_axis import mark_gaps
from src.ui import markdown, pyplot, new_figure, table
from src.visibility import USABLE_FRACTION, louisiana, kerrville, case_summary

REASONS = {'usable': 'usable', 'mostly cloud / cloud shadow': 'cloud', 'mostly no data (outside swath / not observed)': 'nodata',
           'too few valid cells': 'few'}


def case_name(case):
    return t(f"vis.case.{case['key']}")


def availability_figure(cases):
    """Per case: NISAR footprint coverage vs optical valid fraction, same 0–100% axis."""
    colors = palette(); lang = current_lang()
    fig, axes = new_figure(len(cases), 1, figsize=(10, 2.9 * len(cases)))
    axes = [axes] if len(cases) == 1 else axes
    for ax, case in zip(axes, cases):
        obs = case['observations']; refs = case['references']
        ax.axhspan(USABLE_FRACTION * 100, 100, color=colors['usable_band'], zorder=0)
        ax.scatter([o['time'] for o in obs], [100 * o['coverage'] for o in obs], marker='D', s=46, color=colors['nisar'],
                   label=t('vis.fig.nisar'), zorder=3)
        for usable, color, key in ((True, colors['optical_ok'], 'vis.fig.usable'), (False, colors['optical_bad'], 'vis.fig.not_usable')):
            chosen = [r for r in refs if r['usable'] == usable]
            ax.scatter([r['time'] for r in chosen], [100 * r['valid_fraction'] for r in chosen], marker='o', s=40, zorder=3,
                       color=color, label=t('vis.fig.reference', text=t(key), count=len(chosen)))
        mark_gaps(ax, [o['time'] for o in obs])
        if case['event']['time'] is not None:
            ax.axvline(case['event']['time'], color=colors['event'], ls='--', lw=1.2, label=t('vis.fig.peak'))
        times = [o['time'] for o in obs] + [r['time'] for r in refs]
        ax.set_xlim(min(times) - timedelta(days=2), max(times) + timedelta(days=2))
        ax.set_ylim(-5, 108); ax.set_ylabel(t('vis.fig.ylabel'))
        ax.set_title(t('vis.fig.title', name=case_name(case), usable=percent(USABLE_FRACTION)), fontsize=10, loc='left')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b' if lang == 'en' else '%d.%m')); ax.grid(alpha=.2)
        ax.legend(fontsize=7, loc='center left', bbox_to_anchor=(1.0, .5), frameon=False)
    fig.suptitle(t('vis.fig.suptitle'), fontsize=11)
    return fig


def fmt_hours(h):
    return t('common.na') if h is None else f"{num(h, 1, sign=True)} h"


def render_case(case):
    summary = case_summary(case)
    cols = st.columns(4)
    cols[0].metric(t('vis.m.acquisitions'), summary['nisar_acquisitions'])
    cols[1].metric(t('vis.m.pairs'), summary['compatible_pairs'])
    cols[2].metric(t('vis.m.full'), summary['full_coverage_pairs'])
    cols[3].metric(t('vis.m.optical', usable=percent(USABLE_FRACTION)),
                   t('vis.m.optical_value', usable=summary['optical_usable'], inspected=summary['optical_inspected']))
    event = case['event']
    note_values = dict(event.get('note_values', {}))
    if 'warning' in note_values:
        note_values['warning'] = saved_text(note_values['warning'])
    st.caption(t(event['note_key'], **note_values) if 'note_key' in event else event['note'])
    if summary['first_post_event_hours'] is not None:
        st.warning(t('vis.first_after', hours=num(summary['first_post_event_hours'], 1)))
    with st.expander(t('vis.pairs_title')):
        span = {True: t('common.yes'), False: t('common.no'), None: t('vis.no_event')}
        table([{t('vis.col.track'): p['track'], t('vis.col.frame'): p['frame'], t('vis.col.direction'): p['direction'],
                t('vis.col.before'): p['before'].strftime('%Y-%m-%d %H:%M'), t('vis.col.after'): p['after'].strftime('%Y-%m-%d %H:%M'),
                t('vis.col.interval'): p['interval_days'], t('vis.col.coverage'): percent(p['coverage'], 1),
                t('vis.col.method'): t('vis.method.intersection') if p['coverage_method'] == 'geometric intersection' else t('vis.method.upper'),
                t('vis.col.spans'): span[p['spans_event']]} for p in case['pairs']])
    with st.expander(t('vis.refs_title')):
        table([{t('vis.col.collection'): r['collection'], t('vis.col.acquired'): r['time'].strftime('%Y-%m-%d %H:%M'),
                t('vis.col.valid'): percent(r['valid_fraction'], 1),
                t('vis.col.cloud'): t('common.na') if r['tile_cloud_percent'] is None else percent(r['tile_cloud_percent'] / 100, 0),
                t('vis.col.cells'): t('vis.cells', cloud=integer(r['cloud_shadow_cells']), cells=integer(r['cells'])),
                t('vis.col.status'): t(f"vis.reason.{REASONS.get(r['reason'], 'few')}") if r['reason'] in REASONS else r['reason'],
                t('vis.col.hours'): fmt_hours(r['hours_from_event'])} for r in case['references']])
        st.caption(t('vis.refs_caption', decision=saved_text(case['decision']), sources=', '.join(f'`{s}`' for s in case['sources'])))


def render_visibility():
    st.title(t('vis.title'))
    st.caption(t('vis.cached_only'))
    markdown(t('vis.intro'))
    st.info(t('vis.info'))
    try:
        cases = [louisiana(), kerrville()]
    except (OSError, ValueError, KeyError) as exc:
        st.error(t('vis.error', error=type(exc).__name__))
        return
    pyplot(availability_figure(cases))
    st.caption(t('vis.fig_caption'))
    tabs = st.tabs([case_name(c) for c in cases])
    for tab, case in zip(tabs, cases):
        with tab:
            render_case(case)
    with st.expander(t('vis.kerrville_checklist')):
        from src.evidence import kerrville_checklist
        from src.evidence_panel import render_checklist
        render_checklist(kerrville_checklist(lang=current_lang()))
    with st.expander(t('vis.meaning')):
        markdown(t('vis.meaning_text', usable=percent(USABLE_FRACTION)))
