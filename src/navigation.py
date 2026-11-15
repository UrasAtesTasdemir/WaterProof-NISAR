"""Page registry for NISAR Change Compass: six pages, Louisiana sub-views.

The sidebar lists the pages as buttons (session key 'workspace'); the
Louisiana case-study page has a second selector (key 'case_view') for its
analysis views. Internal keys of the original workspaces are kept so saved
behaviour and tests can address them by name. Displayed labels come from the
translation layer (keys 'page.<slug>' / 'view.<slug>').
"""

APP_NAME = 'WaterProof'

# internal key -> slug used for widget keys and translation keys
_PAGES = (
    ('Explore the world', 'explore'),
    ('Researcher workflow', 'workflow'),
    ('NISAR study', 'louisiana'),
    ('Is this scene analyzable?', 'visibility'),
    ('Flood validation (Thailand, Gandak)', 'flood'),
    ('Benchmark Validation (Sentinel-1)', 'benchmark'),
    ('About', 'about'),
)
_CASE_VIEWS = (
    ('Change dashboard', 'dashboard'),
    ('Geographic map (NISAR)', 'geographic'),
    ('HH time series (six dates)', 'time_series'),
    ('Polarization Analysis', 'polarization'),
    ('Investigation Explorer', 'investigation'),
    ('Change Compass', 'compass'),
    ('Evidence & limitations', 'evidence'),
    ('Scientific Diagnostics', 'diagnostics'),
)

PAGES = tuple(key for key, _ in _PAGES)
CASE_VIEWS = tuple(key for key, _ in _CASE_VIEWS)
SLUGS = {**dict(_PAGES), **dict(_CASE_VIEWS)}
NAV_KEYS = {key: f'nav_{slug}' for key, slug in _PAGES}
DEFAULT_PAGE = 'Explore the world'   # opens with the 'Start here' panel
DEFAULT_CASE_VIEW = 'Change dashboard'


def page_label(key, lang=None):
    """Displayed label for an internal key (unknown keys pass through)."""
    from src.i18n import t
    if key in PAGES:
        return t(f'page.{SLUGS[key]}', lang=lang)
    if key in CASE_VIEWS:
        return t(f'view.{SLUGS[key]}', lang=lang)
    return key


def go_to(key):
    """Callback for navigation buttons: open a page or a Louisiana view."""
    import streamlit as st
    if key in PAGES:
        st.session_state['workspace'] = key
        if key == 'NISAR study':
            st.session_state['case_view'] = DEFAULT_CASE_VIEW
    elif key in CASE_VIEWS:
        st.session_state['workspace'] = 'NISAR study'
        st.session_state['case_view'] = key
    else:
        raise ValueError(f'Unknown page: {key}')


def apptest_open(app, key):
    """Test helper: open a page or Louisiana view in a Streamlit AppTest via the sidebar buttons.

    'NISAR study' opens the original change dashboard."""
    if key in PAGES and key != 'NISAR study':
        app.button(key=NAV_KEYS[key]).click().run()
        return app
    view = DEFAULT_CASE_VIEW if key == 'NISAR study' else key
    if view not in CASE_VIEWS:
        raise ValueError(f'Unknown page: {key}')
    app.button(key=NAV_KEYS['NISAR study']).click().run()
    if view != DEFAULT_CASE_VIEW:
        app.selectbox(key='case_view').select(view).run()
    return app


# English display labels (kept for older callers and tests).
LABELS = {key: page_label(key, 'en') for key in PAGES + CASE_VIEWS}
