"""Shared read-only case evidence; never placed as a score for an unrelated AOI."""
import streamlit as st
from src.i18n import t, num, integer, percent
from src.evaluation_provenance import primary_evaluations, negative_controls
from src.ui import table


def metric_provenance(stages=None):
    st.caption(t('release.metric_context'))
    st.caption(t('release.mask_policy'))
    for row in primary_evaluations():
        if stages and row['stage'] not in stages:
            continue
        label = t('fl.outcome.new' if row['outcome'].startswith('new') else 'fl.outcome.presence')
        st.markdown(f"**{t('fl.stage.' + row['stage'])} · {label} · {row['reference_type']}**")
        st.write(t('release.coverage', pixels=integer(row['evaluated_pixels']), area=num(row['evaluated_area_km2'], 4),
                   fraction=percent(row['evaluated_fraction_of_grid'], 2)))
        st.json(dict(nisar_product_ids=row['nisar']['product_ids'], nisar_acquisition_utc=row['nisar']['times'],
                     crs=row['nisar']['crs'], transform=row['nisar']['transform'], grid_shape=row['nisar']['grid_shape'],
                     raster_bounds_wgs84=row['bounds_wgs84'], counts=row['counts']))
        for ref in row['references']:
            st.code(ref['product_id'], language=None)
            st.write(ref.get('acquired_utc') or '—')
            st.caption(t('release.offset', hours=num(ref.get('offset_hours'), 2, sign=True)))
            st.json({k: v for k, v in ref.items() if k not in ('product_id', 'acquired_utc', 'offset_hours')})
        st.caption(t('release.source', path=', '.join(row['source_files'])))
    st.info(t('release.ref_caution'))


def comparison_panel():
    st.subheader(t('release.case_title'))
    rows = primary_evaluations()
    for col, stages, key in zip(st.columns(2), (('a', 'b'), ('c',)), ('thailand', 'gandak')):
        with col:
            st.markdown('**' + t('release.' + key) + '**')
            for row in rows:
                if row['stage'] not in stages or not row['outcome'].startswith('new'):
                    continue
                lo, hi = row['ci95']['F1']
                pre, dur = row['references']
                st.markdown(t('release.case_metric', scene=t('fl.stage.' + row['stage']), f1=num(row['metrics']['F1']),
                              lo=num(lo), hi=num(hi), n1=row['nisar']['times'][0][:10], n2=row['nisar']['times'][1][:10],
                              r1=(pre['acquired_utc'] or '—')[:10], r2=(dur['acquired_utc'] or '—')[:10],
                              o1=num(pre['offset_hours'], 1, sign=True), o2=num(dur['offset_hours'], 1, sign=True),
                              area=num(row['evaluated_area_km2'], 1)))
            st.caption(t('release.' + key + '_note'))
    st.info(t('release.case_caution'))
    with st.expander(t('release.provenance')):
        metric_provenance()


def negative_warning():
    a, b = negative_controls()
    return t('release.negative_short', a=num(a['candidate_area_km2'], 2), b=num(b['candidate_area_km2'], 2),
             da=num(a['disagreement_area_km2'], 2), db=num(b['disagreement_area_km2'], 2))


def negative_details():
    st.write(t('release.negative_method'))
    st.warning(t('release.negative_note'))
    for row in negative_controls():
        st.markdown('**Thailand ' + row['track'] + '**')
        st.write(t('release.coverage', pixels=integer(row['evaluated_pixels']), area=num(row['evaluated_area_km2'], 4),
                   fraction=percent(row['evaluated_fraction_of_grid'], 2)))
        st.json(row)
