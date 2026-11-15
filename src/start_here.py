"""'Start here' panel at the top of the Explore page (the app's opening page).

Open on the first visit; the visitor can hide it and show it again (session key 'start_open').
"Take the guided example" opens the shipped Thailand flood case (Prachin Buri, 6 -> 30 Sep 2026, offline) with the
flood-validation pair preselected (see src/explore_panel.py).
"""
import streamlit as st

from src.i18n import t
from src.ui import markdown

OPEN_KEY = 'start_open'


def _set_open(value):
    st.session_state[OPEN_KEY] = value


def take_guided_example():
    """Button callback: guided preset, its example pair, introduction folded away."""
    from src.explore_panel import guided_preset, guided_pair_key
    item = guided_preset()
    st.session_state['ex_pending'] = (item['lat'], item['lon'], item['key'])
    st.session_state.pop(guided_pair_key(item['key']), None)   # the pair selector falls back to the example pair
    st.session_state['workspace'] = 'Explore the world'
    st.session_state[OPEN_KEY] = False


def render_start_here():
    st.session_state.setdefault(OPEN_KEY, True)
    if not st.session_state[OPEN_KEY]:
        st.button(t('start.show'), key='start_show', on_click=_set_open, args=(True,))
        return
    with st.container(border=True, key='start_here'):
        st.subheader(t('start.title'))
        st.write(t('release.first_line'))
        for col, step in zip(st.columns(4), range(1, 5)):
            with col:
                markdown(t(f'start.step{step}'))
        left, right = st.columns([1, 1])
        left.button(t('start.guided'), key='start_guided', type='primary', on_click=take_guided_example,
                    help=t('start.guided_help'), width='stretch')
        from src.navigation import go_to
        right.button(t('release.open_workflow'), key='start_research', on_click=go_to, args=('Researcher workflow',), width='stretch')
        st.caption(t('scope.overview'))
        with st.expander(t('release.details')):
            for block in ('problem', 'do', 'not'):
                st.markdown(f"**{t(f'start.{block}_title')}**")
                markdown(t(f'start.{block}'))
            st.button(t('start.hide'), key='start_hide', on_click=_set_open, args=(False,))
