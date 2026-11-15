"""About page: framing, how pages fit together, data provenance, limits, glossary, AI use, license."""
import streamlit as st

from src.glossary import TERMS, label, definition
from src.i18n import t
from src.navigation import APP_NAME, go_to, page_label
from src.ui import markdown, table

PROVENANCE = (
    ('louisiana', 'data/subsets/, data/nisar_manifest.json'),
    ('six_date', 'data/time_series/, data/polarization_analysis/'),
    ('hv', 'data/hv/'),
    ('investigation', 'data/investigation_engine/'),
    ('robustness', 'data/robustness_v2/'),
    ('baseline', 'data/water_change/, data/scientific_quality_check/, data/reliability/'),
    ('references', 'data/validation/, data/pair_selection/, data/kerrville_feasibility/'),
    ('case_evaluation', 'data/flood_validation/'),
    ('benchmark', 'data/benchmark_validation/'),
)
LINKED_PAGES = ('Explore the world', 'Researcher workflow', 'NISAR study', 'Is this scene analyzable?',
                'Flood validation (Thailand, Gandak)', 'Benchmark Validation (Sentinel-1)')


def render_about():
    st.title(t('about.title', app=APP_NAME))
    st.markdown(f"#### {t('about.headline')}")
    markdown(t('about.framing'))
    st.info(t('scope.overview'))
    st.markdown(f"#### {t('about.pages')}")
    for key in LINKED_PAGES:
        c1, c2 = st.columns([1, 3])
        c1.button(page_label(key), key=f'about_go_{key}', on_click=go_to, args=(key,), use_container_width=True)
        c2.write(t(f'about.page.{key}'))
    st.markdown(f"#### {t('about.provenance')}")
    with st.expander(t('about.provenance_table')):
        table([{t('about.col.data'): t(f'about.prov.{key}.name'), t('about.col.folder'): folder, t('about.col.notes'): t(f'about.prov.{key}.notes')}
               for key, folder in PROVENANCE])
    st.caption(t('about.offline'))
    st.markdown(f"#### {t('about.glossary')}")
    with st.expander(t('about.glossary_open')):
        table([{t('about.col.term'): label(key), t('about.col.meaning'): definition(key)} for key in TERMS])
    st.markdown(f"#### {t('about.ai')}")
    st.markdown(t('about.ai_text'))
    st.markdown(f"#### {t('about.license')}")
    st.markdown(t('about.license_text'))
    st.caption(t('release.third_party'))
    from html import escape
    from src.theme import tokens
    st.markdown(f'<footer class="wp-attribution" style="text-align:center;font-size:.82rem;line-height:1.6;'
                f'margin-top:2rem;padding:.5rem 1rem;color:{tokens()["muted"]}">'
                f'{escape(t("release.attribution"))}</footer>', unsafe_allow_html=True)


def render_explore():
    st.title(t('explore.title'))
    markdown(t('explore.coming_soon'))
    st.button(t('explore.go_workflow'), key='explore_go_workflow', on_click=go_to, args=('Researcher workflow',))
