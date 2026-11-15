"""'Explore the world' page: a 3D globe, a place and a date range, cached cases and live NISAR windows.

Modes:
- cached demo + catalog search (always): preset places with cached windows run end to end offline;
  the public ASF catalog can be searched for any place without credentials.
- live window reading: only when a server-side Earthdata token exists or the visitor pastes one
  (kept in this session's memory only). Reads only a small HH/HV window per date.
"""
from datetime import date, datetime
import json

import numpy as np
import streamlit as st
from matplotlib.patches import Rectangle
from rasterio.transform import array_bounds

from src.compass_panel import render_reading, compass_figure
from src.explore import PRESETS, PLACE_SIZE_M, GUIDED_EXAMPLE_PAIR, louisiana_cube, analyze, observation, review_note
from src.start_here import render_start_here
from src import demo_places
from src.i18n import t, num, integer, percent, current_lang
from src.live_engine import (LiveError, DEFAULT_WINDOW_KM, MIN_WINDOW_KM, MAX_WINDOW_KM, MAX_DATES, MAX_RUN_BYTES,
                             validate_point, validate_dates, search_catalog, group_products, run_live, window_polygon,
                             cache_key, cache_get, server_token, token_status)
from src.precise_selection import precise_selection
from src.explore_requests import catalog_request, analysis_request, accept_result, current_result
from src.theme import current_theme, palette, tokens
from src.time_axis import mark_gaps, gap_caption
from src.ui import markdown, caption, pyplot, new_figure, table
from src.workflow import status_text, scope_text, PAIR, BASELINE, CONTEXT, CONSISTENT, CAUTION, NEUTRAL, UNKNOWN

ICON = {CONSISTENT: '🟢', CAUTION: '🟠', NEUTRAL: '⚪', UNKNOWN: '❔'}
DEFAULT_DATES = (date(2026, 6, 1), date(2026, 9, 30))
SECONDS_PER_DATE = {5: 60, 10: 120}   # HH+HV per new date; measured 45.5 s/date for the Louisiana window (data/live_verification)


@st.cache_resource(show_spinner=False)
def _louisiana():
    return louisiana_cube()


GUIDED_PAIR_KEY = 'ex_pair_guided'          # pair selector of the preset that has an example pair
GUIDED_KEY = 'thailand_prachinburi'         # first preset and "Start here" guided example (shipped demo cache)
DEMO_EXAMPLES = {GUIDED_KEY: dict(example_pair=('2026-09-06', '2026-09-30'), example_caption='fl.example_caption',
                                  info_key='fl.demo.info')}


@st.cache_data(show_spinner=False)
def _candidate_point(candidate_id):
    """Representative point of a saved Louisiana candidate (data/investigation_engine/results.json)."""
    from src.explore import ROOT
    regions = json.loads((ROOT / 'data/investigation_engine/results.json').read_text())['regions']
    region = next(r for r in regions if r['id'] == candidate_id)
    return round(region['representative_latitude'], 6), round(region['representative_longitude'], 6)


def guided_pair_key(preset_key):
    return f'{GUIDED_PAIR_KEY}_{preset_key}'


def guided_preset():
    """The Thailand flood demo when it ships; otherwise Louisiana candidate 1."""
    items = presets()
    return next((p for p in items if p['key'] == GUIDED_KEY), next(p for p in items if p['key'] == 'louisiana_c1'))


def presets():
    """Preset places; Kerrville's point is the centroid of its cached area of interest when available; the guided
    example uses candidate 1's saved representative point."""
    from src.explore import ROOT
    items = []
    for p in PRESETS:
        item = dict(p)
        if p.get('candidate'):
            try:
                item['lat'], item['lon'] = _candidate_point(p['candidate'])
            except (OSError, KeyError, ValueError, StopIteration):
                pass
        if p['key'] == 'kerrville':
            try:
                from shapely import wkt
                aoi = wkt.loads(json.loads((ROOT / 'data/kerrville_feasibility/aoi.json').read_text())['aoi_wkt'])
                item.update(lat=aoi.centroid.y, lon=aoi.centroid.x)
            except (OSError, KeyError, ValueError):
                pass
        items.append(item)
    demos = [dict(p, **DEMO_EXAMPLES.get(p['key'], {})) for p in _demo_places()]
    first = [p for p in demos if p['key'] == GUIDED_KEY]
    return first + items + [p for p in demos if p['key'] != GUIDED_KEY]


@st.cache_data(show_spinner=False)
def _demo_places():
    """Shipped offline demo places (data/demo_cache); each needs a translated name."""
    from src.i18n import STRINGS
    return [p for p in demo_places.places() if f"ex.preset.{p['key']}" in STRINGS['en']]


@st.cache_resource(show_spinner=False)
def _demo_cube(key):
    place = next(p for p in _demo_places() if p['key'] == key)
    return demo_places.demo_cube(place)


def groups_table(groups):
    table([{t('ex.col.group'): i + 1, t('ex.col.track'): g['key']['track'], t('ex.col.frame'): g['key']['frame'],
            t('ex.col.direction'): t('ex.dir.' + g['key']['direction']), t('ex.col.mode'): g['key']['polarization'],
            t('ex.col.release'): g['key']['crid'], t('ex.col.hhhv'): g['has_hh_hv'], t('ex.col.count'): len(g['dates']),
            t('ex.col.dates'): ', '.join(g['dates'])} for i, g in enumerate(groups)])


def demo_section(place):
    """Point, reason, dates, window, product IDs and the dated catalog snapshot of a shipped demo place."""
    m = place['manifest']; snap = place['snapshot']
    with st.container(border=True, key='ex_demo_info'):
        st.markdown(f"**{t('ex.demo.title')}**")
        markdown(t(place.get('info_key', 'ex.demo.info'), name=t(f"ex.preset.{place['key']}").split(' (')[0], lat=f"{m['lat']:.4f}", lon=f"{m['lon']:.4f}",
                   window=num(m['window_km'], 0), count=len(m['dates']), dates=', '.join(m['dates']),
                   why=t(f"ex.demo.why.{place['key']}")))
        with st.expander(t('ex.demo.products')):
            table([{t('ex.col.date'): d, t('ex.col.product'): pid} for d, pid in zip(m['dates'], m['product_ids'])])
        with st.expander(t('ex.demo.snapshot', date=snap['snapshot_date'])):
            st.caption(t('ex.demo.snapshot_caption', date=snap['snapshot_date'], count=snap['count']))
            groups_table(demo_places.snapshot_groups(place))


def _apply_pending():
    """Coordinates chosen by a click, the preset list or the place search are applied before the inputs are drawn."""
    pending = st.session_state.pop('ex_pending', None)
    if pending:
        st.session_state['ex_lat'] = round(float(pending[0]), 5)
        st.session_state['ex_lon'] = round(float(pending[1]), 5)
        if len(pending) > 2:
            st.session_state['ex_preset'] = pending[2]
            item = next((p for p in presets() if p['key'] == pending[2]), None)
            if item and item.get('manifest'):                 # a shipped demo place: show its real window size
                st.session_state['ex_window'] = float(item['manifest']['window_km'])
        st.session_state.pop('ex_catalog', None); st.session_state.pop('ex_cube', None)


def _on_preset():
    key = st.session_state.get('ex_preset')
    item = next((p for p in presets() if p['key'] == key), None)
    if item:
        st.session_state['ex_pending'] = (item['lat'], item['lon'], key)


def _on_coords():
    """Typed coordinates: the preset box follows the point (another preset if it matches one, otherwise 'Custom place')."""
    lat, lon = st.session_state.get('ex_lat'), st.session_state.get('ex_lon')
    match = next((p['key'] for p in presets() if lat is not None and lon is not None
                  and abs(lat - p['lat']) < 5e-5 and abs(lon - p['lon']) < 5e-5), 'custom')
    st.session_state['ex_preset'] = match


def _geocode(query):
    """Free OpenStreetMap Nominatim search (only the typed place name is sent). Returns a list or raises LiveError."""
    import requests
    query = (query or '').strip()
    if not 2 <= len(query) <= 120:
        raise LiveError('ex.geo.length')
    try:
        response = requests.get('https://nominatim.openstreetmap.org/search', params=dict(q=query, format='json', limit=5),
                                headers={'User-Agent': 'NISAR-Change-Compass/1.0 (NASA Space Apps educational demo)'}, timeout=10)
        response.raise_for_status()
        rows = response.json()
    except Exception as exc:  # noqa: BLE001
        raise LiveError('ex.geo.failed', error=type(exc).__name__) from None
    return [dict(name=r.get('display_name', '')[:140], lat=float(r['lat']), lon=float(r['lon'])) for r in rows if 'lat' in r]


def cached_preset():
    """The selected preset when it has cached radar windows and the point still matches it; otherwise None."""
    key = st.session_state.get('ex_preset', GUIDED_KEY)
    item = next((p for p in presets() if p['key'] == key and p.get('cached')), None)
    if not item:
        return None
    lat, lon = st.session_state.get('ex_lat', item['lat']), st.session_state.get('ex_lon', item['lon'])
    return item if abs(lat - item['lat']) < 5e-5 and abs(lon - item['lon']) < 5e-5 else None


def fixed_demo():
    return cached_preset() is not None


def place_controls():
    lang = current_lang()
    options = [p['key'] for p in presets()] + ['custom']
    st.selectbox(t('ex.preset'), options, key='ex_preset', on_change=_on_preset,
                 format_func=lambda k, lang=lang: t(f'ex.preset.{k}', lang=lang))
    with st.form('ex_search_form', border=False):
        query = st.text_input(t('ex.geo.label'), key='ex_query', placeholder=t('ex.geo.placeholder'))
        searched = st.form_submit_button(t('ex.geo.button'))
    if searched:
        try:
            st.session_state['ex_geo_results'] = _geocode(query)
        except LiveError as exc:
            st.session_state['ex_geo_results'] = []; st.warning(exc.text())
    results = st.session_state.get('ex_geo_results')
    if results:
        choice = st.selectbox(t('ex.geo.results'), range(len(results)), format_func=lambda i: results[i]['name'], key='ex_geo_choice')
        if st.button(t('ex.geo.use'), key='ex_geo_use'):
            st.session_state['ex_pending'] = (results[choice]['lat'], results[choice]['lon'], 'custom'); st.rerun()
    elif results == [] and searched:
        st.info(t('ex.geo.none'))
    c1, c2 = st.columns(2)
    c1.number_input(t('ex.lat'), -90.0, 90.0, step=0.01, format='%.5f', key='ex_lat', on_change=_on_coords)
    c2.number_input(t('ex.lon'), -180.0, 180.0, step=0.01, format='%.5f', key='ex_lon', on_change=_on_coords)
    fixed=fixed_demo()
    st.date_input(t('ex.dates'), key='ex_dates', min_value=date(2025, 7, 1), max_value=date.today(),disabled=fixed)
    st.slider(t('ex.window'), MIN_WINDOW_KM, MAX_WINDOW_KM, step=1.0, key='ex_window', help=t('ex.window_help'), disabled=fixed)


def live_mode():
    """(token or None, mode text key). The token is never displayed, logged or cached."""
    token = server_token()
    if token:
        return token, 'ex.mode.server'
    pasted = st.session_state.get('ex_token_input', '').strip()
    if pasted:
        return pasted, 'ex.mode.pasted'
    return None, 'ex.mode.demo'


def catalog_section(lat, lon, dates, window_km):
    st.subheader(t('ex.catalog.title'))
    caption(t('ex.catalog.intro'))
    request_id=catalog_request(lat,lon,dates)
    st.session_state['ex_catalog_active']=request_id
    if st.button(t('ex.catalog.button'), key='ex_catalog_search', type='primary'):
        try:
            start, end = validate_dates(*dates)
            with st.spinner(t('ex.catalog.spinner')):
                products, truncated = search_catalog(lat, lon, start, end)
            accept_result(st.session_state,'ex_catalog',request_id,dict(lat=lat, lon=lon, start=start.isoformat(), end=end.isoformat(),
                                                  groups=group_products(products), truncated=truncated, count=len(products)))
        except LiveError as exc:
            st.error(exc.text()); return None
    catalog=current_result(st.session_state,'ex_catalog',request_id)
    if not catalog:
        if st.session_state.get('ex_catalog'): st.info(t('ex.outdated'))
        return None
    if not catalog['groups']:
        st.warning(t('ex.catalog.none', start=catalog['start'], end=catalog['end'])); return None
    if catalog['truncated']:
        st.warning(t('ex.catalog.truncated'))
    st.success(t('ex.catalog.found', count=catalog['count'], groups=len(catalog['groups'])))
    groups_table(catalog['groups'])
    lang = current_lang()
    index = st.selectbox(t('ex.group'), range(len(catalog['groups'])), key='ex_group_'+request_id,
                         format_func=lambda i, lang=lang: t('ex.group_option', lang=lang, n=i + 1, track=catalog['groups'][i]['key']['track'],
                                                            frame=catalog['groups'][i]['key']['frame'], count=len(catalog['groups'][i]['dates'])))
    group = catalog['groups'][index]
    if not group['has_hh_hv']:
        st.warning(t('ex.group_no_hv')); return None
    chosen = st.multiselect(t('ex.choose_dates', max=MAX_DATES), group['dates'], default=group['dates'][-MAX_DATES:],
                            max_selections=MAX_DATES, key=f'ex_dates_pick_{request_id}_{index}')
    if len(chosen) < 2:
        st.info(t('ex.need_two')); return None
    products = [p for p in group['products'] if p['date'] in chosen]
    bounds = window_polygon(lat, lon, window_km).bounds
    cached = sum(cache_get(cache_key(p['product_id'], bounds)) is not None for p in products)
    per_date = SECONDS_PER_DATE[5] if window_km <= 5 else SECONDS_PER_DATE[10]
    minutes = max(1, round((len(products) - cached) * per_date / 60))
    st.info(t('ex.plan', dates=', '.join(p['date'] for p in products), window=num(window_km, 0), cached=cached,
              to_read=len(products) - cached, minutes=minutes, cap=integer(MAX_RUN_BYTES // (1024 * 1024))))
    return products, cached, group['dates']


def run_section(products, cached, catalog_dates, lat, lon, window_km):
    request_id=analysis_request(products,lat,lon,window_km)
    st.session_state['ex_cube_active']=request_id
    token, mode = live_mode()
    to_read = len(products) - cached
    if to_read and not token:
        st.warning(t('ex.need_token')); return
    if st.session_state.get('ex_running'):
        st.warning(t('ex.running')); return
    label = t('ex.run') if to_read else t('ex.load_cached')
    if not st.button(label, key='ex_run', type='primary'):
        return
    st.caption(t('ex.cancel_hint'))
    bar = st.progress(0.0, text=t('ex.progress_start'))
    def progress(i, total, product, how):
        bar.progress(i / total, text=t('ex.progress_' + how, n=i + 1, total=total, date=product['date']))
    st.session_state['ex_running'] = True
    try:
        cube = run_live(products, lat, lon, window_km, token, progress=progress)
        cube['catalog_dates'] = list(catalog_dates)
        bar.progress(1.0, text=t('ex.progress_done', seconds=num(cube['elapsed_seconds'], 0),
                                 mib=num(cube['bytes_read_this_run'] / 1048576, 1)))
        accept_result(st.session_state,'ex_cube',request_id,cube)
    except LiveError as exc:
        bar.empty(); st.error(exc.text())
    finally:
        st.session_state['ex_running'] = False


def maps_figure(ctx):
    data = ctx['data']; first, second = ctx['first'], ctx['second']; colors = palette()
    west, south, east, north = array_bounds(*data['HH'].shape[1:], ctx['transform'])
    extent = (west, east, south, north)
    fig, axes = new_figure(1, 3, figsize=(12, 3.6))
    stack = np.concatenate([data['HH'][first][data['valid'][first]], data['HH'][second][data['valid'][second]]])
    lo, hi = np.percentile(stack, [2, 98]) if stack.size else (-25, 0)
    import matplotlib.pyplot as plt
    gray = plt.get_cmap('gray').copy(); gray.set_bad(colors['nodata'])
    for ax, index, key in ((axes[0], first, 'ex.map.before'), (axes[1], second, 'ex.map.after')):
        image = ax.imshow(np.where(ctx['common'], data['HH'][index], np.nan), extent=extent, cmap=gray, vmin=lo, vmax=hi,
                          interpolation='nearest')
        ax.set_title(t(key, date=ctx['dates'][index]), fontsize=9)
    fig.colorbar(image, ax=axes[:2], shrink=.8, label=t('ex.map.hh_db'))
    delta = ctx['pair']['HH_delta']
    limit = max(1.0, float(np.nanpercentile(np.abs(delta), 98))) if np.isfinite(delta).any() else 5
    rdbu = plt.get_cmap('RdBu_r').copy(); rdbu.set_bad(colors['nodata'])
    image = axes[2].imshow(delta, extent=extent, cmap=rdbu, vmin=-limit, vmax=limit, interpolation='nearest')
    axes[2].set_title(t('ex.map.change', d1=ctx['dates'][first], d2=ctx['dates'][second]), fontsize=9)
    fig.colorbar(image, ax=axes[2], shrink=.8, label='ΔHH (dB)')
    rows = np.flatnonzero(ctx['place'].any(axis=1)); cols = np.flatnonzero(ctx['place'].any(axis=0))
    tr = ctx['transform']
    x0, y0 = tr * (cols[0], rows[-1] + 1); x1, y1 = tr * (cols[-1] + 1, rows[0])
    for ax in axes:
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor=colors['second'], lw=1.6))
        ax.ticklabel_format(useOffset=False, style='plain'); ax.tick_params(labelsize=6)
    return fig


def series_figure(ctx):
    colors = palette()
    times = [datetime.fromisoformat(str(r['time']).replace('Z', '+00:00')) for r in ctx['series']]
    fig, ax = new_figure(figsize=(10, 3.4))
    for band in ('HH', 'HV'):
        ax.plot(times, [r[f'{band}_place_median_db'] if r[f'{band}_place_median_db'] is not None else np.nan for r in ctx['series']],
                'o', color=colors[band.lower()], label=t('ex.fig.place', band=band))
        ax.plot(times, [r[f'{band}_window_median_db'] if r[f'{band}_window_median_db'] is not None else np.nan for r in ctx['series']],
                'o', mfc='none', color=colors[band.lower()], label=t('ex.fig.window', band=band))
    for index, color, key in ((ctx['first'], colors['first'], 'wfp.fig.first'), (ctx['second'], colors['second'], 'wfp.fig.second')):
        ax.axvline(times[index], color=color, ls='--', alpha=.8, label=t(key))
    mark_gaps(ax, times)
    ax.set_ylabel(t('wfp.fig.ylabel')); ax.set_xlabel(t('wfp.fig.xlabel')); ax.grid(alpha=.2)
    ax.legend(fontsize=7, ncol=3, loc='upper left', bbox_to_anchor=(0, -.22), frameon=False)
    return fig, times


def evidence_table(ctx, scope):
    table([{'': ICON[e['status']], t('wfp.col.topic'): e['topic'], t('wfp.col.status'): status_text(e['status'], ctx['lang']),
            t('wfp.col.observation'): e['text'], t('wfp.col.rule'): e['rule']} for e in ctx['evidence'] if e['scope'] == scope])


def candidate_card(candidate_id, pair, square_pixels):
    """The saved researcher-workflow reading and limits for a Louisiana candidate, next to the Explore square."""
    from src.workflow import build_context, observation as wf_observation
    from src.workflow_panel import cached_inputs
    lang = current_lang()
    try:
        ctx = build_context(cached_inputs(), candidate_id, *pair, lang=lang)
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        st.info(t('ex.c1.unavailable', error=type(exc).__name__)); return
    region = ctx['candidate']; d1, d2 = ctx['dates'][pair[0]], ctx['dates'][pair[1]]
    with st.container(border=True, key='ex_candidate_card'):
        st.markdown(f"**{t('ex.c1.title')}**")
        markdown(t('ex.c1.scale', square=integer(square_pixels), pixels=integer(region['pixels'])))
        st.markdown(t('ex.c1.reading', d1=d1, d2=d2, observation=wf_observation(ctx)))
        st.markdown(t('ex.c1.limits'))
        limits = [e['text'] for e in ctx['evidence'] if e['id'] in ('lodo', 'hv') and e['status'] == CAUTION]
        limits.append(t('ex.c1.size', pixels=integer(region['pixels']), area=num(region['area_km2'], 4)))
        st.markdown('\n'.join(f'- {line}' for line in limits))
        st.button(t('ex.c1.open'), key='ex_open_candidate', on_click=_open_candidate, args=(candidate_id, pair))
        return ctx


def _open_candidate(candidate_id, pair):
    from src.navigation import go_to
    st.session_state['wf_candidate'] = candidate_id; st.session_state['wf_pair'] = tuple(pair)
    go_to('Researcher workflow')


def flood_section(cube, pair):
    """Unchanged threshold map; evidence scope is checked for the exact selection."""
    from src import flood_layer
    from src.evidence_scope import matched_case, scope_for, scope_text, thailand_context, is_control
    from src.evaluation_panel import metric_provenance, negative_warning, negative_details
    from src.navigation import go_to
    lang = current_lang(); dates = cube['dates']
    with st.container(border=True, key='ex_flood_map'):
        st.markdown(f"**{t('fl.layer.title')}**")
        st.caption(scope_text(scope_for(cube, pair)))
        markdown(t('fl.layer.intro'))
        try:
            result = flood_layer.compute(cube, *pair)
        except (ValueError, KeyError) as exc:
            st.info(t('fl.layer.error', error=type(exc).__name__)); return
        st.markdown(t('fl.layer.share', share=percent(result['share_new'] or 0, 1), area=num(result['new_area_km2'], 2),
                      d1=dates[pair[0]], d2=dates[pair[1]]))
        pyplot(flood_layer.figure(result, cube['transform'], cube['crs']))
        st.markdown(flood_layer.class_legend(), unsafe_allow_html=True)
        try:
            stage = matched_case(cube, pair)
            if is_control(cube, pair):
                st.caption(t('release.control_selected'))
            if stage:
                st.caption(t('release.selected_evaluation', stage=t('fl.stage.' + stage)))
                with st.expander(t('release.provenance')):
                    metric_provenance((stage,))
            if thailand_context(cube):
                st.warning(negative_warning())
                with st.expander(t('release.negative_details')):
                    negative_details()
        except (OSError, KeyError, ValueError, StopIteration) as exc:
            st.caption(t('fl.missing', error=type(exc).__name__))
        st.button(t('release.open_cases'), key='ex_open_cases', on_click=go_to, args=('Flood validation (Thailand, Gandak)',))


def render_results(cube, preset=None):
    lang = current_lang()
    dates = cube['dates']
    st.subheader(t('ex.results', source=t('ex.source.' + cube['source'])))
    c1, c2 = st.columns(2)
    pairs = [(a, b) for a in range(len(dates)) for b in range(a + 1, len(dates))]
    example = (preset or {}).get('example_pair')
    guided = bool(example) and all(d in dates for d in example)
    if guided:
        key = guided_pair_key(preset['key']); default = (dates.index(example[0]), dates.index(example[1]))
    else:
        key = f"ex_pair_{cube['source']}_{'-'.join(dates)}"; default = (0, len(dates) - 1)
    pair = c1.selectbox(t('wfp.pair'), pairs, index=pairs.index(default), key=key,
                        format_func=lambda p: f'{dates[p[0]]} → {dates[p[1]]}')
    if guided:
        caption(t(preset['example_caption']))
    try:
        ctx = analyze(cube, *pair, lang=lang)
    except ValueError as exc:
        st.info(t('wfp.cannot', error=exc)); return
    st.caption(t('ex.common',pixels=integer(ctx['common_pixels']),area=num(ctx['common_area_km2'],4)))
    st.caption(t('ex.coverage_note'))
    st.caption(t('ex.sampled',lat=f"{ctx['sampled_lat']:.6f}",lon=f"{ctx['sampled_lon']:.6f}",row=ctx['sampled_row'],col=ctx['sampled_col']))
    c2.metric(t('ex.place_pixels', size=int(PLACE_SIZE_M)), integer(ctx['summary'].get('pixels', 0)))
    if guided and preset.get('candidate'):
        candidate_card(preset['candidate'], pair, ctx['summary'].get('pixels', 0))
    with st.container(border=True):
        st.markdown(f"**{t('wfp.observation')}**")
        st.markdown(observation(ctx))
        note = review_note(ctx)
        st.download_button(t('wfp.download'), note, mime='text/markdown', key='ex_download',
                           file_name=f"review_{cube['lat']:.3f}_{cube['lon']:.3f}_{dates[pair[0]]}_{dates[pair[1]]}_{lang}.md",
                           help=t('wfp.download_help'))
    st.markdown(f"**{t('ex.maps')}**")
    pyplot(maps_figure(ctx))
    caption(t('ex.maps_caption', size=int(PLACE_SIZE_M)))
    st.markdown(f"**{t('ex.series')}**")
    fig, times = series_figure(ctx); pyplot(fig)
    st.caption(gap_caption(times))
    if ctx.get('catalog_between') and not ctx.get('pair_gaps'):
        st.caption(t('fl.time.caption_unloaded', dates=', '.join(ctx['catalog_between'])))
    with st.expander(t('ex.coverage')):
        table(ctx['series'])
    st.markdown(f"**{t('wfp.consistent')}**")
    render_reading(ctx['reading'])
    flood_section(cube, pair)
    with st.expander(t('ex.compass_plot')):
        region = ctx['place'] & ctx['pair']['valid']
        pyplot(compass_figure(ctx['pair']['HH_delta'][region], ctx['pair']['HV_delta'][region], ctx['summary'], ctx['scene'],
                              ctx['dead_zone_db'], (0.0, 0.0), ctx['reading']['raw']['key']))
    with st.expander(t('ex.evidence')):
        for scope, title in ((PAIR, scope_text(PAIR, lang)), (BASELINE, t('ex.note.not_computed')), (CONTEXT, scope_text(CONTEXT, lang))):
            st.markdown(f'**{title}**'); evidence_table(ctx, scope)
        st.caption(t('wfp.statuses'))
        st.markdown(t('wfp.open_questions') + '\n' + '\n'.join(f'{i}. {q}' for i, q in enumerate(ctx['open_questions'], 1)))
    with st.expander(t('ex.provenance')):
        table([{t('ex.col.date'): d, t('ex.col.product'): p} for d, p in zip(cube['dates'], cube['product_ids'])])
        st.caption(t('ex.provenance_caption', crs=str(ctx['crs']), bytes=integer(cube.get('bytes_read_this_run', 0))))
    with st.expander(t('wfp.preview')):
        st.markdown(note)


def render_explore():
    st.title(t('ex.title'))
    render_start_here()
    st.warning(t('ex.warning'))
    first_place = guided_preset()   # first visit: the guided example (cached, offline)
    st.session_state.setdefault('ex_preset', first_place['key'])
    st.session_state.setdefault('ex_lat', round(first_place['lat'], 5)); st.session_state.setdefault('ex_lon', round(first_place['lon'], 5))
    st.session_state.setdefault('ex_dates', DEFAULT_DATES)
    st.session_state.setdefault('ex_window', float(first_place.get('manifest', {}).get('window_km', DEFAULT_WINDOW_KM)))
    _apply_pending()
    fixed = cached_preset()
    st.caption(t('ex.live_mode') if not fixed else t('ex.fixed_mode_demo') if fixed.get('case') == 'demo' else t('ex.fixed_mode'))
    token, mode = live_mode()
    left, right = st.columns([1.25, 1])
    with left:
        try:
            from src.earth_globe import render_earth_globe
            picked=render_earth_globe(st.session_state['ex_lat'],st.session_state['ex_lon'],
                         [dict(lat=p['lat'],lon=p['lon'],name=t(f"ex.preset.{p['key']}")) for p in presets()])
            if picked and st.session_state.get('ex_last_pick') != (picked['lat'], picked['lon']):
                st.session_state['ex_last_pick'] = (picked['lat'], picked['lon'])
                st.session_state['ex_pending'] = (picked['lat'], picked['lon'], next(
                    (p['key'] for p in presets() if (round(p['lat'], 4), round(p['lon'], 4)) ==
                     (round(picked['lat'], 4), round(picked['lon'], 4))), 'custom'))
                st.rerun()
        except Exception as exc:  # noqa: BLE001 - the page must work without the globe
            st.info(t('ex.globe_failed', error=type(exc).__name__))
        caption(t('globe.precision'))
    with right:
        place_controls()
    lat, lon = st.session_state['ex_lat'], st.session_state['ex_lon']
    dates = st.session_state['ex_dates']; window_km = float(st.session_state['ex_window'])
    try:
        lat, lon = validate_point(lat, lon)
    except LiveError as exc:
        st.error(exc.text()); return
    if not (isinstance(dates, (tuple, list)) and len(dates) == 2):
        st.info(t('ex.dates_pick_two')); return
    with st.expander(t('ex.mode.title') + ' · ' + t(mode), expanded=False):
        markdown(t(mode + '_text'))
        if mode == 'ex.mode.demo' or mode == 'ex.mode.pasted':
            st.text_input(t('ex.token_label'), type='password', key='ex_token_input', help=t('ex.token_help'))
    preset = st.session_state.get('ex_preset')
    cached = cached_preset()
    if cached and cached.get('case') == 'louisiana':
        st.success(t('ex.cached_case'))
        try:
            with st.spinner(t('wfp.spinner')):
                cube = _louisiana()
        except (OSError, ValueError, KeyError) as exc:
            st.error(t('ex.cache_error', error=type(exc).__name__)); return
        if cached.get('candidate'):
            cube = dict(cube, lat=cached['lat'], lon=cached['lon'])
        render_results(cube, cached); return
    if cached and cached.get('case') == 'demo':
        demo_section(cached)
        try:
            with st.spinner(t('wfp.spinner')):
                cube = _demo_cube(cached['key'])
        except LiveError as exc:
            st.info(exc.text()); return
        render_results(cube, cached); return
    if preset == 'kerrville':
        st.info(t('ex.kerrville_note'))
    plan = catalog_section(lat, lon, dates, window_km)
    request_id=analysis_request(plan[0],lat,lon,window_km) if plan else None
    st.session_state['ex_cube_active']=request_id
    cube=current_result(st.session_state,'ex_cube',request_id) if request_id else None
    precise_selection(lat,lon,window_km,cube)
    if plan:
        run_section(*plan, lat, lon, window_km)
        cube=current_result(st.session_state,'ex_cube',request_id)
    if cube:
        render_results(cube)
    elif st.session_state.get('ex_cube'):
        st.info(t('ex.outdated'))
    elif not plan:
        st.caption(t('ex.not_available'))
