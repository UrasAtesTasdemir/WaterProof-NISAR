"""Change Compass page: HH-vs-HV change vector for a chosen region."""
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from rasterio.transform import array_bounds

from src.change_compass import (DIRECTORY, DEFAULT_DEAD_ZONE_DB, MIN_PIXELS, LABELS, load_pair, region_options,
                                region_summary, compass_reading, sector_shares, rectangle_mask, percent_ranges,
                                label_text, reason_text, sector_label)
from src.i18n import t, num, integer, percent, saved_text, current_lang
from src.glossary import strip
from src.theme import palette, tokens, current_theme
from src.ui import markdown, caption, pyplot, new_figure, table
from src.water_change import pixel_area_km2

LIMIT = 8.0
KEY_COLORS = {'light': {'smoother_surface': '#2372a5', 'hh_darkening': '#3f76a0', 'hh_brightening': '#2f7a2d',
                        'volume_loss': '#a35a24', 'volume_gain': '#7d4f9b', 'inconclusive': '#5f6b78', 'reference_dependent': '#9a7a0c'},
              'dark': {'smoother_surface': '#6ab4ea', 'hh_darkening': '#8fbde0', 'hh_brightening': '#7fd17c',
                       'volume_loss': '#f0a46a', 'volume_gain': '#c99ae8', 'inconclusive': '#b8c4cf', 'reference_dependent': '#f2d36b'}}


def _tau(value):
    return num(value, 2).rstrip('0').rstrip(',.')


def render_reading(reading):
    """Pattern card: both references, their numbers, and the evidence-limits list."""
    key = reading['key']
    with st.container(border=True):
        st.markdown(f"#### {label_text(key)}")
        st.caption(label_text(key, 'physics'))
        rows = []
        for name, part in ((t('compass.card.raw'), 'raw'), (t('compass.card.relative'), 'relative')):
            numbers = reading['numbers'].get(part)
            rows.append({t('compass.col.reference'): name,
                         'ΔHH (dB)': t('common.na') if numbers is None else num(numbers[0], 2, sign=True),
                         'ΔHV (dB)': t('common.na') if numbers is None else num(numbers[1], 2, sign=True),
                         t('compass.col.pattern'): label_text(reading[part]['key']), t('compass.col.why'): reason_text(reading[part])})
        table(rows)
        if not reading['agree']:
            markdown(t('compass.card.disagree', dhh=num(reading['scene'][0], 2, sign=True), dhv=num(reading['scene'][1], 2, sign=True)))
        if reading['alternatives']:
            keys = reading.get('alternative_keys') or []
            items = [t(k) for k in keys] if len(keys) == len(reading['alternatives']) else reading['alternatives']
            st.markdown(t('compass.card.alternatives') + '\n' + '\n'.join(f'- {a}' for a in items))
        st.caption(t('compass.card.caution', caution=label_text(key, 'caution')))


@st.cache_data(max_entries=2, show_spinner=False)
def cached_inputs(signature):
    data = load_pair()
    return data, region_options()


def input_signature():
    names = ('hv_signal_assessment.json', 'pair_change_db.tif', 'pair_filtered_db.tif')
    return tuple((n, (DIRECTORY/n).stat().st_mtime_ns, (DIRECTORY/n).stat().st_size) for n in names)


def compass_figure(hh, hv, summary, scene, dead_zone, reference=(0.0, 0.0), label_key='inconclusive'):
    """Pixel cloud, dead zone, median vector with IQR, scene-median reference."""
    k = tokens(); colors = palette(); theme = current_theme()
    fig, ax = new_figure(figsize=(6.2, 5.6))
    h = np.clip(hh - reference[0], -LIMIT, LIMIT); v = np.clip(hv - reference[1], -LIMIT, LIMIT)
    if h.size > 2000:
        image = ax.hexbin(h, v, gridsize=70, extent=(-LIMIT, LIMIT, -LIMIT, LIMIT), mincnt=1, bins='log',
                          cmap='Greys' if theme == 'light' else 'Greys_r')
        fig.colorbar(image, ax=ax, shrink=.75, label=t('compass.fig.pixels_log'))
    else:
        ax.scatter(h, v, s=6, color=k['muted'], alpha=.55, linewidths=0, label=t('compass.fig.region_pixels'))
    tau = dead_zone
    ax.add_patch(Rectangle((-tau, -tau), 2*tau, 2*tau, facecolor='#f4d35e', alpha=.25, edgecolor='#c9a227', lw=1,
                           label=t('compass.fig.dead_zone', tau=_tau(tau))))
    ax.axhline(0, color=colors['reference_line'], lw=.7); ax.axvline(0, color=colors['reference_line'], lw=.7)
    corners = {(-1, -1): t('compass.fig.corner_smooth'), (1, -1): t('compass.fig.corner_hh'),
               (-1, 1): t('compass.fig.corner_volume'), (1, 1): t('compass.fig.corner_volume')}
    for (sx, sy), text in corners.items():
        ax.text(sx*(LIMIT-.3), sy*(LIMIT-.3), text, ha='right' if sx > 0 else 'left', va='top' if sy > 0 else 'bottom',
                fontsize=7, color=k['muted'])
    ax.text(0, -(LIMIT-.3), t('compass.fig.bottom'), ha='center', va='bottom', fontsize=7, color=k['muted'])
    sh, sv = scene[0]-reference[0], scene[1]-reference[1]
    if abs(sh) > 1e-9 or abs(sv) > 1e-9:
        ax.annotate('', xy=(sh, sv), xytext=(0, 0), arrowprops=dict(arrowstyle='->', color=colors['reference_line'], lw=1.6, ls='--'))
        ax.plot([], [], color=colors['reference_line'], ls='--', label=t('compass.fig.scene', h=num(sh, 2, sign=True), v=num(sv, 2, sign=True)))
    if summary.get('pixels', 0):
        mh = summary['HH']['median']-reference[0]; mv = summary['HV']['median']-reference[1]
        color = KEY_COLORS[theme][label_key]
        ax.annotate('', xy=(mh, mv), xytext=(0, 0), arrowprops=dict(arrowstyle='-|>', color=color, lw=2.6))
        ax.errorbar([mh], [mv], xerr=[[mh-(summary['HH']['p25']-reference[0])], [(summary['HH']['p75']-reference[0])-mh]],
                    yerr=[[mv-(summary['HV']['p25']-reference[1])], [(summary['HV']['p75']-reference[1])-mv]],
                    fmt='o', color=color, capsize=4, label=t('compass.fig.median', h=num(mh, 2, sign=True), v=num(mv, 2, sign=True)))
    ax.set_xlim(-LIMIT, LIMIT); ax.set_ylim(-LIMIT, LIMIT); ax.set_aspect('equal')
    suffix = t('compass.fig.minus_scene') if any(reference) else ''
    ax.set_xlabel(t('compass.fig.xlabel', suffix=suffix)); ax.set_ylabel(t('compass.fig.ylabel', suffix=suffix))
    ax.legend(fontsize=7, loc='upper left', bbox_to_anchor=(0, -.12), ncol=1, frameon=False)
    return fig


def location_figure(hh_delta, mask, grid, pair_text='3 July − 21 June'):
    fig, ax = new_figure(figsize=(6.2, 3.2))
    west, south, east, north = array_bounds(*hh_delta.shape, grid['transform'])
    cmap = plt.get_cmap('RdBu_r').copy(); cmap.set_bad(palette()['nodata'])
    image = ax.imshow(hh_delta, extent=(west, east, south, north), cmap=cmap, vmin=-5, vmax=5, interpolation='nearest')
    overlay = np.where(mask, 1.0, np.nan)
    ax.imshow(overlay, extent=(west, east, south, north), cmap='autumn', alpha=.55, interpolation='nearest')
    ax.contour(mask.astype(float), levels=[.5], colors='#f2a900', linewidths=1.2, origin='upper',
               extent=(west, east, south, north))
    ax.set_title(t('compass.loc.title', pair=pair_text), fontsize=9)
    ax.ticklabel_format(useOffset=False, style='plain'); ax.tick_params(labelsize=7)
    ax.set_xlabel(t('compass.loc.xlabel'), fontsize=8)
    fig.colorbar(image, ax=ax, shrink=.8, label='ΔHH (dB)')
    return fig


def render_compass():
    st.title(t('compass.title'))
    markdown(t('compass.intro'))
    st.warning(t('compass.warning'))
    try:
        with st.spinner(t('compass.spinner')):
            data, options = cached_inputs(input_signature())
    except (OSError, ValueError, KeyError) as exc:
        st.error(t('compass.error', error=type(exc).__name__))
        return
    report = data['report']; valid = data['valid']; grid = data['grid']
    st.caption(t('compass.context', first=report['pair'][0], second=report['pair'][1], pixels=integer(valid.sum())))
    left, right = st.columns([1, 1])
    modes = ['Saved region', 'Rectangle']
    with left:
        mode = st.radio(t('compass.region'), modes, horizontal=True, key='compass_mode',
                        format_func=lambda m, lang=current_lang(): t('compass.mode.saved' if m == 'Saved region' else 'compass.mode.rectangle', lang=lang))
        if mode == 'Saved region':
            names = ['Whole common AOI', *options]
            choice = st.selectbox(t('compass.saved_region'), names,
                                  index=names.index('Baseline class · New water candidate (possible expansion)'), key='compass_region',
                                  format_func=lambda n, lang=current_lang(): t('compass.whole_aoi', lang=lang) if n == 'Whole common AOI' else n)
            mask = valid if choice == 'Whole common AOI' else options[choice]
            if choice.startswith('Baseline class'):
                st.caption(t('compass.baseline_note'))
            elif choice.startswith('Investigation region'):
                st.caption(t('compass.investigation_note'))
        else:
            cols = st.slider(t('compass.cols'), 0, 100, (60, 80), key='compass_cols')
            rows = st.slider(t('compass.rows'), 0, 100, (30, 70), key='compass_rows')
            try:
                row_range, col_range = percent_ranges(rows, cols)
                mask = rectangle_mask(valid.shape, row_range, col_range)
            except ValueError as exc:
                st.info(t('compass.bad_rectangle', error=exc))
                return
            if row_range != (rows[0]/100, rows[1]/100) or col_range != (cols[0]/100, cols[1]/100):
                st.caption(t('compass.widened'))
    with right:
        dead_zone = st.slider(t('compass.dead_zone'), .5, 4., DEFAULT_DEAD_ZONE_DB, .25, key='compass_dead_zone',
                              help=t('compass.dead_zone_help'))
    cell = pixel_area_km2(grid['crs'], grid['transform'])
    summary = region_summary(data['HH_delta'], data['HV_delta'], mask, cell, hv_db=data['HV_db'])
    scene = (float(np.median(data['HH_delta'][valid])), float(np.median(data['HV_delta'][valid])))
    reference = (0.0, 0.0)  # the plot shows raw change; the scene-wide median is drawn as a reference arrow
    reading = compass_reading(summary, scene, dead_zone, MIN_PIXELS)
    render_reading(reading)
    if summary['pixels']:
        m = st.columns(4)
        m[0].metric(t('compass.metric.pixels'), integer(summary['pixels']))
        m[1].metric(t('compass.metric.area'), f"{num(summary['area_km2'], 4)} km²")
        m[2].metric(t('compass.metric.dhh'), f"{num(summary['HH']['median'], 2, sign=True)} dB")
        m[3].metric(t('compass.metric.dhv'), f"{num(summary['HV']['median'], 2, sign=True)} dB")
        st.caption(t('compass.iqr', hh_lo=num(summary['HH']['p25'], 2, sign=True), hh_hi=num(summary['HH']['p75'], 2, sign=True),
                     hv_lo=num(summary['HV']['p25'], 2, sign=True), hv_hi=num(summary['HV']['p75'], 2, sign=True),
                     shh=num(scene[0], 2, sign=True), shv=num(scene[1], 2, sign=True)))
        dark = summary['hv_dark_level']
        if dark['flag']:
            d0, d1 = dark['dates']
            st.warning(strip(t('compass.hv_dark', d0=num(d0['region_median_db'], 1), d1=num(d1['region_median_db'], 1), pct=dark['percentile'],
                               s0=num(d0['scene_percentile_db'], 1), s1=num(d1['scene_percentile_db'], 1))))
        else:
            caption(t('compass.hv_neutral', pct=dark['percentile']))
    else:
        st.info(t('compass.no_pixels'))
    plot_col, map_col = st.columns([1.05, 1])
    with plot_col:
        region = mask & valid
        pyplot(compass_figure(data['HH_delta'][region], data['HV_delta'][region], summary, scene, dead_zone, reference, reading['raw']['key']))
    with map_col:
        pyplot(location_figure(data['HH_delta'], mask & valid, grid, f"{report['pair'][1]} − {report['pair'][0]}"))
        if summary['pixels']:
            shares = sector_shares(data['HH_delta'] - reference[0], data['HV_delta'] - reference[1], mask, dead_zone)
            with st.expander(t('compass.spread_title').replace('**', '')):
                table([{t('compass.col.share'): percent(v, 1), t('compass.col.sector'): sector_label(k)} for k, v in shares.items()])
                st.caption(t('compass.spread_note'))
    with st.expander(t('compass.hv_gate')):
        verdict_hv = report['verdict']
        st.markdown(t('compass.hv_assessment', verdict=verdict_hv['hv_scene_scale']))
        for line in verdict_hv['evidence']:
            st.markdown(f'- {saved_text(line)}')
        st.warning(saved_text(verdict_hv['dark_pixel_warning']))
        st.caption(t('compass.noise_floor_prefix') + saved_text(report['indicators']['noise_floor']))
        st.image(str(DIRECTORY/'change_histograms.png'), caption=t('compass.hist_caption'))
    with st.expander(t('compass.method')):
        table([{t('compass.col.label'): label_text(k), t('compass.col.rule'): label_text(k, 'rule'),
                t('compass.col.physics'): label_text(k, 'physics')} for k in LABELS if k != 'reference_dependent'])
        st.markdown(t('compass.method_text', minimum=MIN_PIXELS))
