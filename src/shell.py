"""App shell used by every page: theme CSS, sidebar page list, team dialog, header strip."""
import streamlit as st

from src.i18n import LANGS, DEFAULT_LANG, LANG_NAMES, t
from src.navigation import APP_NAME, PAGES, CASE_VIEWS, NAV_KEYS, DEFAULT_PAGE, DEFAULT_CASE_VIEW, page_label, go_to
from src.theme import THEMES, DEFAULT_THEME, css, apply_matplotlib

CREATORS = ('Uras Ateş Taşdemir', 'Ali Semih Salum')


def init_state():
    """Language and theme from the URL on first load, then from session state."""
    params = st.query_params
    if 'lang' not in st.session_state:
        st.session_state['lang'] = params.get('lang') if params.get('lang') in LANGS else DEFAULT_LANG
    if 'theme' not in st.session_state:
        st.session_state['theme'] = params.get('theme') if params.get('theme') in THEMES else DEFAULT_THEME
    st.session_state.setdefault('workspace', DEFAULT_PAGE)
    # Preserve Explore coordinates when its widgets are temporarily absent on another page.
    for key in ('ex_lat','ex_lon','ex_window','ex_dates','ex_preset'):
        if key in st.session_state:
            st.session_state[key]=st.session_state[key]


# Widgets whose displayed option labels depend on the language. Streamlit identifies a selectbox choice by its
# label, so before the rerun the current values are stored again as Python values; otherwise the browser's
# old-language label would come back as a raw string after the switch.
LANGUAGE_DEPENDENT_WIDGETS = ('case_view', 'wf_candidate', 'wf_pair', 'compass_mode', 'compass_region', 'evidence_case',
                              'ts_layer', 'ts_radius', 'pol_band', 'diag_quantity', 'investigation_region')


def set_lang(lang):
    for key in LANGUAGE_DEPENDENT_WIDGETS:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]
    st.session_state['lang'] = lang
    st.query_params['lang'] = lang


def toggle_theme():
    theme = 'dark' if st.session_state.get('theme') == 'light' else 'light'
    st.session_state['theme'] = theme
    st.query_params['theme'] = theme


def show_creators():
    @st.dialog(t('team.heading'))
    def creators():
        for name in CREATORS:
            st.markdown(f'**{name}**')
    creators()


def header_strip():
    """Top-right controls: English / Turkish flags and the light/dark switch."""
    lang = st.session_state['lang']; theme = st.session_state['theme']
    with st.container(horizontal=True, vertical_alignment='center', key='cc_header'):
        st.markdown(f'<div class="wp-brand" aria-label="{APP_NAME}">{APP_NAME}</div>',unsafe_allow_html=True)
        with st.container(horizontal=True, horizontal_alignment='right', key='cc_topbar'):
            for code in LANGS:
                st.button(LANG_NAMES[code], key=f'lang_{code}', type='primary' if lang == code else 'secondary',
                          on_click=set_lang, args=(code,))
            st.button(t('shell.switch_theme'), key='theme_toggle', on_click=toggle_theme,
                      icon=':material/dark_mode:' if theme == 'light' else ':material/light_mode:')


def sidebar():
    """Vertical page list (active page highlighted), Louisiana views, team button at the bottom."""
    workspace = st.session_state['workspace']
    with st.sidebar:
        st.markdown(f'<div class="wp-brand wp-sidebar-brand">{APP_NAME}</div>',unsafe_allow_html=True)
        with st.container(key='cc_nav'):
            for key in PAGES:
                st.button(page_label(key), key=NAV_KEYS[key], type='primary' if key == workspace else 'secondary',
                          on_click=go_to, args=(key,), use_container_width=True)
        target = workspace
        if workspace == 'NISAR study':
            st.session_state.setdefault('case_view', DEFAULT_CASE_VIEW)
            target = st.selectbox(t('shell.louisiana_view'), CASE_VIEWS, format_func=lambda key, lang=st.session_state['lang']: page_label(key, lang), key='case_view')
        with st.container(key='cc_team'):
            if st.button(t('team.button'), key='team_button', icon=':material/group:', use_container_width=True):
                show_creators()
    return target


def render_shell():
    """Call once per run, right after st.set_page_config. Returns the page or Louisiana view key to render."""
    init_state()
    apply_matplotlib()
    st.markdown(css(), unsafe_allow_html=True)
    header_strip()
    return sidebar()
