"""'Flood validation (Thailand, Gandak)' page: protocol summary, PRIMARY-rule maps, tables with 95 % intervals,
negative control, deviations and limits. Everything shown is read from data/flood_validation/ (no recomputation).
Wording: agreement with independent water products, never accuracy against ground truth."""
import json
from pathlib import Path

import numpy as np
import streamlit as st
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from rasterio.transform import Affine, array_bounds

from src.i18n import t, num, percent, current_lang
from src.theme import palette
from src.ui import markdown, pyplot, new_figure, table

ROOT = Path(__file__).resolve().parents[1]
FV = ROOT / 'data/flood_validation'
FREEZE, DEV3 = '181782456a', '67ff992a14'


@st.cache_data(show_spinner=False)
def _load(signature):
    boot = json.loads((FV / 'bootstrap_ab/results.json').read_text())
    c = json.loads((FV / 'step2c/metrics.json').read_text())
    d = json.loads((FV / 'step2d/metrics.json').read_text())
    meta = json.loads((FV / 'primary_maps/meta.json').read_text())
    maps = {s: dict(np.load(FV / f'primary_maps/stage_{s}.npz')) for s in meta['stages']}
    return boot, c, d, meta, maps


def _signature():
    files = [FV / p for p in ('bootstrap_ab/results.json', 'step2c/metrics.json', 'step2d/metrics.json', 'primary_maps/meta.json')]
    return tuple((str(f), f.stat().st_mtime_ns) for f in files)


def maps_figure(stage_maps, transform):
    from src.flood_layer import agreement_colors
    colors = palette(); classes = colors['classes']
    agree = agreement_colors()
    west, south, east, north = array_bounds(*stage_maps['classes'].shape, Affine(*transform))
    extent = (west, east, south, north)
    fig, axes = new_figure(1, 2, figsize=(12, 4.6))
    axes[0].imshow(stage_maps['classes'], extent=extent, cmap=ListedColormap(classes), norm=BoundaryNorm(np.arange(-.5, 5.5), 5),
                   interpolation='nearest')
    axes[1].imshow(stage_maps['agreement'], extent=extent, cmap=ListedColormap(agree), norm=BoundaryNorm(np.arange(-.5, 5.5), 5),
                   interpolation='nearest')
    for ax in axes:
        ax.ticklabel_format(useOffset=False, style='plain'); ax.tick_params(labelsize=6)
    return fig


def _ci(point, ci):
    sep = '; ' if current_lang() == 'tr' else ', '      # Turkish decimal commas would make '0,74, 0,81' ambiguous
    return f"{num(point, 2)} [{num(ci[0], 2)}{sep}{num(ci[1], 2)}]" if ci else num(point, 2)


def result_rows(boot, c):
    rows = []
    for stage in ('a', 'b'):
        for key, row in boot['results'][stage]['primary_rows'].items():
            outcome, reference = key.split(' | ')
            p, ci = row['point'], row['ci95']
            rows.append({t('fl.col.scene'): t(f'fl.stage.{stage}'),
                         t('fl.col.outcome'): t('fl.outcome.new' if outcome.startswith('new') else 'fl.outcome.presence'),
                         t('fl.col.reference'): reference.replace(' primary', '').replace(' sensitivity', ''),
                         t('fl.col.precision'): _ci(p['precision'], ci['precision']), t('fl.col.recall'): _ci(p['recall'], ci['recall']),
                         t('fl.col.f1'): _ci(p['F1'], ci['F1']), t('fl.col.iou'): _ci(p['IoU'], ci['IoU'])})
    for r in c['rows']:
        if r['threshold_set'].startswith('PRIMARY') and r['variant'] == 'HH' and 'TP' in r:
            ci = r['ci95']
            rows.append({t('fl.col.scene'): t('fl.stage.c'),
                         t('fl.col.outcome'): t('fl.outcome.new' if r['outcome'].startswith('new') else 'fl.outcome.presence'),
                         t('fl.col.reference'): f"S1 ({r['offset_hours']} h)",
                         t('fl.col.precision'): _ci(r['precision'], ci['precision']), t('fl.col.recall'): _ci(r['recall'], ci['recall']),
                         t('fl.col.f1'): _ci(r['F1'], ci['F1']), t('fl.col.iou'): _ci(r['IoU'], ci['IoU'])})
    return rows


def render_flood():
    st.title(t('fl.title'))
    markdown(t('fl.intro'))
    try:
        boot, c, d, meta, maps = _load(_signature())
    except (OSError, KeyError, ValueError) as exc:
        st.info(t('fl.missing', error=type(exc).__name__)); return
    from src.evaluation_panel import comparison_panel, negative_warning, negative_details
    comparison_panel()
    with st.expander(t('fl.protocol.title')):
        markdown(t('fl.protocol.items', freeze=FREEZE))
    st.subheader(t('fl.table.title'))
    table(result_rows(boot, c))
    st.subheader(t('fl.maps.title'))
    st.caption(t('fl.maps.caption'))
    from src.flood_layer import class_legend, agreement_legend
    for stage, info in meta['stages'].items():
        st.markdown(f"**{t(f'fl.stage.{stage}')}**")
        if stage in ('a', 'b'):
            st.warning(negative_warning())
        pyplot(maps_figure(maps[stage], info['transform']))
        left, right = st.columns(2)
        left.markdown(class_legend(), unsafe_allow_html=True)
        right.markdown(agreement_legend(), unsafe_allow_html=True)
        if stage == 'c':
            st.caption(t('fl.gandak_rotation'))
    st.subheader(t('fl.neg.title'))
    tr = d['tracks']; a, b = tr['004 D'], tr['011 A']
    pct = lambda x: percent(x, 1)
    st.markdown(t('fl.neg.text', o1=num(a['coregistration']['offset_09_18_px']['magnitude'], 2),
                  o2=num(b['coregistration']['offset_09_18_px']['magnitude'], 2),
                  bb1=pct(a['tier_A']['new_water_share_before_before']), bb2=pct(b['tier_A']['new_water_share_before_before']),
                  bd1=pct(a['tier_A']['new_water_share_before_during']), bd2=pct(b['tier_A']['new_water_share_before_during']),
                  ref=pct(a['tier_B']['reference_new_water_share']), fp1=num(a['tier_B']['false_new_water_km2'], 1),
                  fp2=num(b['tier_B']['false_new_water_km2'], 1)))
    with st.expander(t('release.negative_details')):
        negative_details()
    with st.expander(t('release.secondary')):
        st.write(t('release.secondary_note'))
        markdown(t('fl.secondary.text'))
        from src.evidence_scope import case_records
        for stage, record in case_records().items():
            st.markdown('**' + t('fl.stage.' + stage) + '**')
            table([{k: (str(v) if k == 'offset_hours' else v) for k, v in r.items() if k != 'ci95'}
                   for r in record['rows'] if r['threshold_set'].startswith(('SECONDARY', 'calibrated'))])
            st.json(record['exploratory_vegetated_flooding'])
        st.caption(t('release.metric_context'))
        st.caption(t('release.mask_policy'))
    with st.expander(t('fl.deviations.title')):
        markdown(t('fl.deviations.text', dev3=DEV3))
