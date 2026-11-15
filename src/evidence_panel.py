"""Evidence & limitations page: checklist of saved evidence (no score)."""
import streamlit as st

from src.evidence import ROOT, PASS, WARN, UNKNOWN, louisiana_checklist, kerrville_checklist, summarize
from src.i18n import t, current_lang
from src.ui import markdown

CASES = {'louisiana': louisiana_checklist, 'kerrville': kerrville_checklist}


def render_checklist(items):
    """Headline, counts and one bordered line per evidence item."""
    lang = current_lang()
    summary = summarize(items, lang)
    counts = summary['counts']
    badge = {PASS: t('evp.badge.pass'), WARN: t('evp.badge.warn'), UNKNOWN: t('evp.badge.unknown')}
    with st.container(border=True):
        st.markdown(f"#### {summary['headline']}")
        st.write(t('evp.counts', ok=counts[PASS], warn=counts[WARN], unknown=counts[UNKNOWN]))
    for entry in items:
        with st.container(border=True):
            left, right = st.columns([1, 5])
            left.markdown(f"**{badge[entry['status']]}**")
            right.markdown(f"**{entry['title']}** — {entry['finding']}")
            right.caption(t('evp.rule_source', rule=entry['rule'], source=entry['source']))
    st.caption(t('evp.legend'))


def render_evidence():
    st.title(t('evp.title'))
    markdown(t('evp.intro'))
    st.warning(t('evp.warning'))
    case = st.selectbox(t('evp.case'), list(CASES), key='evidence_case', format_func=lambda c, lang=current_lang(): t(f'evp.case.{c}', lang=lang))
    try:
        items = CASES[case](lang=current_lang())
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        st.error(t('evp.error', error=type(exc).__name__))
        return
    render_checklist(items)
    if case == 'louisiana':
        st.caption(t('evp.baseline_note'))
        with st.expander(t('evp.figures')):
            for path, key in (('data/scientific_quality_check/threshold_sensitivity.png', 'evp.fig_threshold'),
                              ('data/reliability/darkening_sensitivity.png', 'evp.fig_offset')):
                if (ROOT / path).exists():
                    st.image(str(ROOT / path), caption=t(key))
                else:
                    st.info(t('evp.fig_missing', caption=t(key), path=path))
