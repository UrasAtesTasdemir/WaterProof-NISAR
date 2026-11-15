"""Researcher workflow page: one candidate, one date pair, one evidence list.

First view: location and dates, the six-date HH/HV pattern, a two-sentence
observation with the most important uncertainty, and the review-note download.
Robustness tables, pair details and the full evidence list are in collapsed
sections below (hidden, not removed).
"""
from datetime import datetime
from itertools import combinations

import streamlit as st

from src.change_compass import DEFAULT_DEAD_ZONE_DB
from src.compass_panel import render_reading, location_figure
from src.i18n import t, num, integer, current_lang, saved_text
from src.theme import palette, themed_map_html
from src.time_axis import mark_gaps, gap_caption
from src.ui import markdown, caption, pyplot, new_figure, table
from src.workflow import (load_inputs, build_context, review_note, default_pair, observation, status_text, scope_text,
                          PAIR, BASELINE, CONTEXT, CONSISTENT, CAUTION, NEUTRAL, UNKNOWN,
                          robustness_summary, investigation_action)
from src.workflow_map import workflow_map, waterway_context, context_sentence, NHD

ICON = {CONSISTENT: '🟢', CAUTION: '🟠', NEUTRAL: '⚪', UNKNOWN: '❔'}


@st.cache_resource(show_spinner=False)
def cached_inputs():
    return load_inputs()


@st.cache_data(max_entries=20, show_spinner=False)
def cached_workflow_map(candidate_id, first, second, lang, nhd_signature):
    inputs = cached_inputs()
    ctx = build_context(inputs, candidate_id, first, second, lang=lang)
    report = inputs['investigations']
    water = waterway_context(ctx['candidate'], report['common_footprint'], ctx['grid']['crs'])
    return workflow_map(report, ctx, water), context_sentence(water, lang)


def _reset_pair():
    """Selecting a new candidate resets the date pair to that candidate's seed change."""
    regions = cached_inputs()['investigations']['regions']
    region = next(r for r in regions if r['id'] == st.session_state['wf_candidate'])
    st.session_state['wf_pair'] = default_pair(region)


def pattern_figure(ctx):
    rows = ctx['candidate']['temporal_statistics']; colors = palette()
    times = [datetime.fromisoformat(r['acquisition_utc'].replace('Z', '+00:00')) for r in rows]
    fig, ax = new_figure(figsize=(10, 3.4))
    for band in ('HH', 'HV'):
        med = [r[band + '_median_db'] for r in rows]
        ax.errorbar(times, med, yerr=[[r[band + '_median_db'] - r[band + '_p25_db'] for r in rows],
                                      [r[band + '_p75_db'] - r[band + '_median_db'] for r in rows]],
                    fmt='o', color=colors[band.lower()], capsize=3, label=t('wfp.fig.median', band=band))
    for index, color, key in ((ctx['first'], colors['first'], 'wfp.fig.first'), (ctx['second'], colors['second'], 'wfp.fig.second')):
        ax.axvline(times[index], color=color, ls='--', alpha=.8, label=t(key))
    mark_gaps(ax, times)
    ax.set_ylabel(t('wfp.fig.ylabel')); ax.set_xlabel(t('wfp.fig.xlabel'))
    ax.grid(alpha=.2); ax.legend(fontsize=7, ncol=3, loc='upper left', bbox_to_anchor=(0, -.22), frameon=False)
    return fig, times


def evidence_table(ctx, scope):
    table([{'': ICON[e['status']], t('wfp.col.topic'): e['topic'], t('wfp.col.status'): status_text(e['status'], ctx['lang']),
            t('wfp.col.observation'): e['text'], t('wfp.col.rule'): e['rule']}
           for e in ctx['evidence'] if e['scope'] == scope])


def placebo_figure(result):
    """Null distributions (HH, HV) with the candidate's value marked; theme-aware."""
    colors = palette()
    fig, axes = new_figure(1, 2, figsize=(10, 3.0))
    for ax, band in zip(axes, ('HH', 'HV')):
        b = result[band]
        ax.hist(b['null_values_db'], bins=40, color=colors[band.lower()], alpha=.75, label=t('pl.fig.band_null', band=band))
        ax.axvline(b['candidate_minus_ring_db'], color=colors['second'], lw=2, label=t('pl.fig.candidate', id=result['candidate']))
        for q in ('null_p05_db', 'null_p95_db'):
            ax.axvline(b[q], color=colors['first'], ls=':', lw=1)
        ax.set_xlabel(t('pl.fig.xlabel', band=band), fontsize=8); ax.set_ylabel(t('pl.fig.ylabel'), fontsize=8)
        ax.tick_params(labelsize=7); ax.legend(fontsize=7, frameon=False); ax.grid(alpha=.2)
    return fig


def render_placebo(ctx):
    """Expander 'Placebo check' for the selected candidate (saved data/placebo outputs; 'not available' otherwise)."""
    from src.placebo import count_at_least
    result = ctx.get('placebo')
    with st.expander(t('pl.title')):
        st.markdown(f"**{t('pl.caption')}**")
        if not result:
            st.info(t('pl.not_available')); return
        markdown(t('pl.intro'))
        st.caption(t('pl.interval', d1=result['interval'][0], d2=result['interval'][1], n=integer(result['placements']),
                     draws=integer(result['draws_attempted']), seed=result['seed']))
        if result['status'] != 'computed':
            st.warning(t('pl.not_enough', n=result['placements'], minimum=result['min_placements']))
        else:
            for band in ('HH', 'HV'):
                b = result[band]
                st.markdown(t('pl.line', band=band, value=num(b['candidate_minus_ring_db'], 2, True), median=num(b['null_median_db'], 2, True),
                              p05=num(b['null_p05_db'], 2, True), p95=num(b['null_p95_db'], 2, True),
                              count=integer(count_at_least(result, band)), n=integer(result['placements']),
                              fraction=num(b['exceedance_fraction'], 4)))
            pyplot(placebo_figure(result))
        st.caption(t('pl.limits'))


def render_workflow():
    lang = current_lang()
    st.title(t('wfp.title'))
    markdown(t('ux.purpose'))
    from src.evidence_scope import scope_text as evidence_scope_text, LOUISIANA   # not workflow.scope_text (evidence-table scopes)
    st.caption(evidence_scope_text(LOUISIANA))
    try:
        with st.spinner(t('wfp.spinner')):
            inputs = cached_inputs()
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        st.error(t('wfp.error', error=type(exc).__name__))
        return
    regions = inputs['investigations']['regions']
    dates = [o['date'] for o in inputs['data']['report']['observations']]
    ids = [r['id'] for r in regions]
    if not ids:
        st.info(t('inv.none')); return
    st.session_state.setdefault('wf_candidate', ids[0])
    st.session_state.setdefault('wf_pair', default_pair(regions[0]))
    with st.container(border=True):
        left, mid = st.columns(2)
        candidate_id = left.selectbox(
            t('wfp.candidate'), ids, key='wf_candidate', on_change=_reset_pair,
            format_func=lambda i, lang=lang: next(t('wfp.candidate_option', lang=lang, id=r['id'], area=num(r['area_km2'], 4, lang=lang),
                                                    d1=dates[r['seed_interval']], d2=dates[r['seed_interval'] + 1],
                                                    direction=t(f"wfp.direction.{r['seed_direction']}", lang=lang))
                                       for r in regions if r['id'] == i))
        pairs = list(combinations(range(len(dates)), 2))
        first, second = mid.selectbox(
            t('wfp.pair'), pairs, key='wf_pair',
            format_func=lambda p, lang=lang: t('wfp.pair_option', lang=lang, d1=dates[p[0]], d2=dates[p[1]],
                                    days=(datetime.fromisoformat(dates[p[1]]) - datetime.fromisoformat(dates[p[0]])).days))
    try:
        ctx = build_context(inputs, candidate_id, first, second, st.session_state.get('wf_dead_zone', DEFAULT_DEAD_ZONE_DB), lang=lang)
    except ValueError as exc:
        st.info(t('wfp.cannot', error=exc))
        return
    r = ctx['candidate']; s = ctx['summary']; d1, d2 = ctx['dates'][first], ctx['dates'][second]

    # ---- First view: location, observation, uncertainty, next action --------------------------
    st.caption(t('ux.location', id=r['id'], area=num(r['area_km2'], 4), pixels=integer(s.get('pixels', 0)),
                 lon=f"{r['representative_longitude']:.5f}", lat=f"{r['representative_latitude']:.5f}"))
    st.caption(t('release.why_listed', reason=saved_text(r['selection_reason'], lang)) + ' ' + t('release.rank_note'))
    try:
        nhd_signature = (NHD.stat().st_mtime_ns, NHD.stat().st_size) if NHD.exists() else None
        map_html, geographic_context = cached_workflow_map(candidate_id, first, second, lang, nhd_signature)
        st.iframe(themed_map_html(map_html), height=390, alt=t('ux.map_alt'))
        st.caption(geographic_context)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        st.warning(t('ux.map_error', error=type(exc).__name__))
    with st.container(border=True):
        st.markdown(f"**{t('wfp.observation')}**")
        st.markdown(observation(ctx))
        st.markdown(f"**{t('ux.action_title')}**")
        question, action = investigation_action(ctx)
        st.write(question)
        st.write(action)
        st.caption(t('ux.action_scope'))
        note = review_note(ctx)
        st.download_button(t('wfp.download'), note, file_name=f"review_candidate{r['id']}_{d1}_{d2}_{lang}.md",
                           mime='text/markdown', key='wf_download', help=t('wfp.download_help'))
    st.subheader(t('ux.robustness'))
    for line in robustness_summary(ctx):
        st.write(line)
    render_placebo(ctx)
    st.subheader(t('wfp.pattern'))
    fig, times = pattern_figure(ctx); pyplot(fig)
    st.caption(gap_caption(times))
    caption(t('wfp.pattern_caption'))
    with st.expander(t('ux.advanced')):
        st.number_input(t('wfp.dead_zone'), .5, 4., DEFAULT_DEAD_ZONE_DB, .25, key='wf_dead_zone',
                        help=t('wfp.dead_zone_help'))
        st.caption(t('ux.advanced_note'))
    with st.expander(t('wfp.where')):
        st.caption(t('ux.map_note', area=num(inputs['investigations']['common_valid_area_km2'], 4)))
        pyplot(location_figure(ctx['HH_delta'], ctx['footprint_mask'] & ctx['pair_valid'], ctx['grid'], f'{d2} − {d1}'))

    # ---- Details (collapsed) -------------------------------------------------------------
    with st.expander(t('wfp.intervals')):
        table([{t('wfp.col.interval'): f"{x['selected_date']} → {x['comparison_date']}",
                t('wfp.col.region_dhh'): round(x['median_HH_delta_db'], 2), t('wfp.col.region_dhv'): round(x['median_HV_delta_db'], 2),
                t('wfp.col.scene_dhh'): round(x['scene_median_HH_delta_db'], 2), t('wfp.col.notable'): x['region_notable']}
               for x in r['notable_intervals']])
    rs = ctx['robustness']['summary']
    with st.expander(scope_text(BASELINE, lang)):
        st.info(t('wfp.baseline_info', seed=rs['seed']))
        a, b, c = st.columns(3)
        with a:
            st.markdown(t('wfp.a_title'))
            st.metric(t('wfp.a_metric'), f"{rs['variants_in_top5']}/{rs['settings_variants']}")
            st.caption(t('wfp.a_caption', r0=rs['rank_range'][0], r1=rs['rank_range'][1], p0=rs['screened_pixels_range'][0],
                         p1=rs['screened_pixels_range'][1], pixels=r['pixels']))
        with b:
            st.markdown(t('wfp.b_title'))
            st.metric(t('wfp.b_metric'), f"{rs['variants_same_seed']}/{rs['settings_variants']}")
            st.caption(t('wfp.b_caption', i0=num(rs['iou_top5_range'][0]), i1=num(rs['iou_top5_range'][1])))
        with c:
            markdown(t('wfp.lodo_title'))
            st.metric(t('wfp.lodo_metric'), f"{rs['lodo_removals_still_notable']}/{rs['lodo_removals']}")
            untestable = t('wfp.lodo_untestable', dates=', '.join(rs['lodo_dates_not_testable'])) if rs['lodo_dates_not_testable'] else ''
            st.caption(t('wfp.lodo_caption', dates=', '.join(rs['lodo_dates_not_notable']) or t('common.none'), untestable=untestable))
        table([{t('wfp.col.removed'): x['removed_date'], t('wfp.col.carrier'): x['seed_event_interval'] or '–',
                t('wfp.col.median_dhh'): None if x['seed_event_delta_db'] is None else round(x['seed_event_delta_db'], 2),
                t('wfp.col.status'): t(f"wfp.lodo_status.{x['seed_event_status']}"),
                t('wfp.col.others'): ', '.join(x['other_same_direction_notable_intervals']) or '–',
                t('wfp.col.best_iou'): round(x['best_iou_top5'], 2), t('wfp.col.rank'): x['top5_rank']} for x in ctx['robustness']['lodo']])
        st.markdown(f"**{t('wfp.variants')}**")
        table(ctx['robustness']['variants'], height=320)
        st.markdown(t('wfp.baseline_evidence'))
        evidence_table(ctx, BASELINE)

    with st.expander(scope_text(PAIR, lang)):
        st.info(t('wfp.pair_info', d1=d1, d2=d2))
        ring = ctx['ring']
        markdown(t('wfp.ring_title', d1=d1, d2=d2))
        table([{t('wfp.col.quantity'): 'ΔHH (dB)', t('wfp.col.candidate'): round(ring['candidate_dHH_db'], 2), t('wfp.col.ring'): round(ring['ring_dHH_db'], 2),
                t('wfp.col.diff'): round(ring['candidate_minus_ring_dHH_db'], 2), t('wfp.col.scene'): round(ctx['scene'][0], 2)},
               {t('wfp.col.quantity'): 'ΔHV (dB)', t('wfp.col.candidate'): round(ring['candidate_dHV_db'], 2), t('wfp.col.ring'): round(ring['ring_dHV_db'], 2),
                t('wfp.col.diff'): round(ring['candidate_minus_ring_dHV_db'], 2), t('wfp.col.scene'): round(ctx['scene'][1], 2)}])
        st.caption(t('wfp.ring_caption'))
        st.markdown(f"**{t('wfp.consistent')}**")
        render_reading(ctx['reading'])
        dark = s.get('hv_dark_level')
        if dark and dark['flag']:
            st.warning(t('wfp.hv_dark'))
        st.caption(t('wfp.saved_note', text=saved_text(r['possible_interpretations'], lang)))
        st.markdown(t('wfp.pair_evidence'))
        evidence_table(ctx, PAIR)

    with st.expander(t('wfp.questions_section')):
        st.markdown(f"**{scope_text(CONTEXT, lang)}**")
        evidence_table(ctx, CONTEXT)
        st.caption(t('wfp.statuses'))
        st.markdown(t('wfp.open_questions') + '\n' + '\n'.join(f'{i}. {q}' for i, q in enumerate(ctx['open_questions'], 1)))
        st.markdown(f"**{t('wfp.preview')}**")
        st.markdown(note)
