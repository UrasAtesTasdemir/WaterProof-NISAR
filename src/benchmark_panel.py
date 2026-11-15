"""Separate optional Sentinel-1 benchmark page, never beside NISAR areas."""
from pathlib import Path
import json

import streamlit as st

from src.i18n import t, integer, num
from src.ui import table

ROOT = Path(__file__).resolve().parents[1]


def render_benchmark():
    st.title(t('bm.title'))
    st.caption(t('bm.caption'))
    st.subheader(t('bm.subheader'))
    st.warning(t('bm.warning'))
    path = ROOT/'data/benchmark_validation/results.json'
    try:
        result = json.loads(path.read_text())
        if result['status'] != 'success':
            raise ValueError('Evaluation incomplete')
        adapted = result['test_micro_metrics']; baseline = result['baseline_micro_metrics']
    except (OSError, ValueError, KeyError):
        st.error(t('bm.error')); return
    st.write(t('bm.summary', test=result['test_scenes'], groups=len(result['groups']), pixels=integer(result['test_valid_pixels']),
               train=result['train_scenes']))
    st.caption(t('bm.subset'))
    table([{t('bm.col.method'): name, **{k: values[k] for k in ('precision', 'recall', 'F1', 'IoU')}}
           for name, values in [(t('bm.method.calibrated'), adapted), (t('bm.method.otsu'), baseline)]])
    st.caption(t('bm.micro', macro=num(result['test_macro_F1'], 3)))
    c = result['calibration']
    st.write(t('bm.frozen', band=c['band'], threshold=c['threshold_db']))
    with st.expander(t('bm.matrix')):
        matrix = adapted['matrix_rows_reference_nonwater_water_columns_prediction_nonwater_water']
        table([{t('bm.col.manual'): t('bm.not_water'), t('bm.col.pred_not'): matrix[0][0], t('bm.col.pred_water'): matrix[0][1]},
               {t('bm.col.manual'): t('bm.water'), t('bm.col.pred_not'): matrix[1][0], t('bm.col.pred_water'): matrix[1][1]}])
        table([{t('bm.col.scene'): r['scene_id'], **{k: r['metrics'][k] for k in ('precision', 'recall', 'F1', 'IoU', 'valid_pixels')}}
               for r in result['test_scene_metrics']])
        st.caption(t('bm.undefined'))
    st.subheader(t('bm.scenes'))
    ids = [r['scene_id'] for r in result['test_scene_metrics']]
    selected = st.selectbox(t('bm.scene'), ids, index=ids.index(result['worst_scene']), key='benchmark_scene')
    image = ROOT/'data/benchmark_validation/figures'/f'{selected}.png'
    if image.exists():
        st.image(str(image))
    else:
        st.info(t('bm.figure_missing'))
    st.info(t('bm.limits'))
    st.markdown(t('bm.link'))
