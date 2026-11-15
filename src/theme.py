"""Light and dark themes from one set of colour tokens.

Streamlit applies one configured theme to every visitor, so the per-visitor
switch is done here: CSS custom properties for the page and widgets, matplotlib
rc parameters and a chart palette for figures, and tile/legend swaps for
Leaflet maps. Text tokens are checked against WCAG AA in tests.
"""
import base64
from pathlib import Path

THEMES = ('light', 'dark')
DEFAULT_THEME = 'light'
ROOT = Path(__file__).resolve().parents[1]

TOKENS = {
    'light': dict(bg='#f5f8fb', surface='#ffffff', surface2='#eaf1f6', text='#12334a', heading='#0d2638', muted='#4a6276',
                  border='#c4d3de', primary='#00706b', on_primary='#ffffff', link='#005f86',
                  warn_bg='#fff4d6', warn_text='#5c3d00', info_bg='#e3f0fb', info_text='#0b3c5d',
                  error_bg='#fde6e6', error_text='#7a1414', ok_bg='#e2f5ec', ok_text='#0d4a2f',
                  tip_bg='#12334a', tip_text='#ffffff', focus='#d17f22'),
    'dark': dict(bg='#0f1a22', surface='#172631', surface2='#1f3240', text='#e4edf3', heading='#f4f8fb', muted='#a9bccb',
                 border='#355063', primary='#3cc6bd', on_primary='#062221', link='#8fd3ff',
                 warn_bg='#3a2e10', warn_text='#ffe3a3', info_bg='#10314a', info_text='#d3e9fb',
                 error_bg='#45191b', error_text='#ffd3d3', ok_bg='#123828', ok_text='#c9f2dc',
                 tip_bg='#e4edf3', tip_text='#0f1a22', focus='#f2a65a'),
}

# Chart colours per theme. Lines/markers must reach 3:1 against the figure background (WCAG 1.4.11).
PALETTE = {
    'light': dict(hh='#007f83', hv='#a04c83', first='#12334a', second='#b9650f', expansion='#00857a', recession='#b9650f',
                  event='#9b2226', gap_fill='#f2d7a6', gap_text='#7a4f00', nisar='#12334a', optical_ok='#1f7f74',
                  optical_bad='#c4472b', usable_band='#e2f2ee', reference_line='#6b7c8a', median='#b9650f',
                  nodata='#d8e1e8', classes=['#d8e1e8', '#2372a5', '#00a596', '#bf6c1a', '#eeeee8'], footprint='#00a892'),
    'dark': dict(hh='#45c4c8', hv='#e08fc6', first='#cfe3f2', second='#f2a65a', expansion='#3fd1c2', recession='#f2a65a',
                 event='#ff8080', gap_fill='#5a4520', gap_text='#ffd48a', nisar='#cfe3f2', optical_ok='#4cc9b0',
                 optical_bad='#ff8a6a', usable_band='#173a33', reference_line='#9fb2c1', median='#f2a65a',
                 nodata='#2b3a46', classes=['#2b3a46', '#5aa8e0', '#2fd6c4', '#f5a94a', '#5d6a74'], footprint='#3fd1c2'),
}
CLASS_KEYS = ('unknown', 'persistent', 'new', 'receded', 'other')


def current_theme():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx(suppress_warning=True) is None:
            return DEFAULT_THEME
        import streamlit as st
        theme = st.session_state.get('theme', DEFAULT_THEME)
    except Exception:  # noqa: BLE001
        return DEFAULT_THEME
    return theme if theme in THEMES else DEFAULT_THEME


def tokens(theme=None):
    return TOKENS[theme or current_theme()]


def palette(theme=None):
    return PALETTE[theme or current_theme()]


def _luminance(hex_color):
    rgb = [int(hex_color.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4 for c in rgb]
    return .2126 * lin[0] + .7152 * lin[1] + .0722 * lin[2]


def contrast(a, b):
    """WCAG contrast ratio between two hex colours."""
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + .05) / (lb + .05)


def mpl_rc(theme=None):
    k = tokens(theme)
    return {'figure.facecolor': k['bg'], 'axes.facecolor': k['surface'], 'savefig.facecolor': k['bg'],
            'axes.edgecolor': k['border'], 'axes.labelcolor': k['text'], 'axes.titlecolor': k['heading'],
            'text.color': k['text'], 'xtick.color': k['muted'], 'ytick.color': k['muted'],
            'xtick.labelcolor': k['text'], 'ytick.labelcolor': k['text'], 'grid.color': k['muted'],
            'legend.facecolor': k['surface'], 'legend.edgecolor': k['border'], 'legend.labelcolor': k['text']}


def apply_matplotlib(theme=None):
    import matplotlib
    matplotlib.rcParams.update(mpl_rc(theme))


def _flag(name):
    data = (ROOT / 'assets/flags' / f'{name}.svg').read_bytes()
    return 'data:image/svg+xml;base64,' + base64.b64encode(data).decode()


def css(theme=None):
    """CSS for the whole app: custom properties plus overrides of Streamlit's own surfaces."""
    k = tokens(theme)
    props = ';'.join(f'--cc-{name.replace("_", "-")}:{value}' for name, value in k.items())
    try:
        flags = {name: _flag(name) for name in ('en', 'tr')}
    except OSError:
        flags = {'en': '', 'tr': ''}
    return f'''<style>
:root{{{props}}}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stHeader"],[data-testid="stBottom"]>div{{background:var(--cc-bg)!important;color:var(--cc-text)!important}}
[data-testid="stSidebar"],[data-testid="stSidebarContent"]{{background:var(--cc-surface2)!important;color:var(--cc-text)!important}}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6{{color:var(--cc-heading)!important;letter-spacing:-.02em}}
[data-testid="stMarkdownContainer"],[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li,
[data-testid="stText"],[data-testid="stWidgetLabel"],[data-testid="stWidgetLabel"] p,.stApp label{{color:var(--cc-text)!important}}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{{color:var(--cc-muted)!important}}
.stApp a{{color:var(--cc-link)!important}}
.stApp code{{background:var(--cc-surface2)!important;color:var(--cc-text)!important}}
[data-testid="stCode"] pre,[data-testid="stCode"] code{{background:var(--cc-surface2)!important;color:var(--cc-text)!important}}
[data-testid="stJson"]{{background:var(--cc-surface)!important;border-radius:8px}}
[data-testid="stJson"] span{{color:var(--cc-text)!important}}
[data-testid="stMetric"]{{background:var(--cc-surface);border:1px solid var(--cc-border);border-radius:14px;padding:14px}}
[data-testid="stMetricValue"],[data-testid="stMetricValue"] *,[data-testid="stMetricLabel"],[data-testid="stMetricLabel"] *{{color:var(--cc-text)!important}}
[data-testid="stExpander"] details{{background:var(--cc-surface)!important;border-color:var(--cc-border)!important}}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary *{{color:var(--cc-text)!important}}
[data-testid="stVerticalBlockBorderWrapper"],[data-testid="stVerticalBlock"][style*="border"]{{border-color:var(--cc-border)!important}}
[data-baseweb="select"]>div,[data-baseweb="input"],[data-baseweb="input"] input,[data-baseweb="base-input"],
[data-testid="stNumberInputContainer"],.stNumberInput input,.stTextInput input,.stApp textarea{{background:var(--cc-surface)!important;color:var(--cc-text)!important;border-color:var(--cc-border)!important}}
[data-baseweb="select"] *{{color:var(--cc-text)!important}}
[data-testid="stDateInput"] div[data-baseweb],[data-testid="stDateInput"] input{{background:var(--cc-surface)!important;color:var(--cc-text)!important}}
[data-baseweb="calendar"],[data-baseweb="calendar"] div{{background:var(--cc-surface)!important;color:var(--cc-text)!important}}
[data-testid="stNumberInputStepDown"],[data-testid="stNumberInputStepUp"]{{background:var(--cc-surface2)!important;color:var(--cc-text)!important}}
[data-baseweb="popover"] ul,[data-baseweb="menu"],[role="listbox"]{{background:var(--cc-surface)!important}}
[role="option"],[role="option"] *{{color:var(--cc-text)!important}}
[role="option"]:hover,[role="option"][aria-selected="true"]{{background:var(--cc-surface2)!important}}
[data-testid^="stBaseButton-secondary"],[data-testid="stBaseButton-tertiary"]{{background:var(--cc-surface)!important;color:var(--cc-text)!important;border-color:var(--cc-border)!important}}
[data-testid^="stBaseButton-secondary"] *{{color:var(--cc-text)!important}}
[data-testid="stBaseButton-primary"]{{background:var(--cc-primary)!important;border-color:var(--cc-primary)!important}}
[data-testid="stBaseButton-primary"],[data-testid="stBaseButton-primary"] *{{color:var(--cc-on-primary)!important}}
.stApp button[data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] p,
.stApp button[data-testid="stBaseButton-primary"] span{{color:var(--cc-on-primary)!important}}
.stApp button[data-testid^="stBaseButton-secondary"] [data-testid="stMarkdownContainer"] p{{color:var(--cc-text)!important}}
[data-testid="stTooltipContent"],[data-baseweb="tooltip"],[data-baseweb="tooltip"] div{{background:var(--cc-tip-bg)!important;color:var(--cc-tip-text)!important}}
[data-testid="stTooltipContent"] *,[data-baseweb="tooltip"] *{{color:var(--cc-tip-text)!important}}
.stApp button:focus-visible,.cc-term:focus-visible{{outline:3px solid var(--cc-focus)!important;outline-offset:2px}}
[data-testid="stAlertContainer"]{{border:1px solid var(--cc-border)}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]){{background:var(--cc-warn-bg)!important}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) *{{color:var(--cc-warn-text)!important}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]){{background:var(--cc-info-bg)!important}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) *{{color:var(--cc-info-text)!important}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]){{background:var(--cc-error-bg)!important}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) *{{color:var(--cc-error-text)!important}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]){{background:var(--cc-ok-bg)!important}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) *{{color:var(--cc-ok-text)!important}}
[data-baseweb="tab"],[data-baseweb="tab"] *{{color:var(--cc-muted)!important;background:transparent!important}}
[data-baseweb="tab"][aria-selected="true"],[data-baseweb="tab"][aria-selected="true"] *{{color:var(--cc-primary)!important}}
[data-baseweb="tab-highlight"]{{background:var(--cc-primary)!important}}
[data-baseweb="tab-border"]{{background:var(--cc-border)!important}}
[data-testid="stTable"] table,[data-testid="stTable"] th,[data-testid="stTable"] td{{color:var(--cc-text)!important;border-color:var(--cc-border)!important}}
[data-testid="stTable"] table{{background:var(--cc-surface)!important}}
[data-testid="stTable"] th{{background:var(--cc-surface2)!important}}
[data-testid="stSliderTickBar"] *,[data-testid="stSliderThumbValue"]{{color:var(--cc-text)!important}}
[role="dialog"]{{background:var(--cc-surface)!important;color:var(--cc-text)!important}}
[role="dialog"] *{{color:var(--cc-text)}}
[data-testid="stSpinner"] *{{color:var(--cc-text)!important}}
hr{{border-color:var(--cc-border)!important}}
/* The soft-blue brand sits on a dark plaque for readable contrast in either theme. */
.wp-brand{{color:#67C8F5!important;background:#12334a;border-radius:10px;padding:6px 12px;
font-size:1.65rem;font-weight:600;letter-spacing:.035em;line-height:1.3;white-space:nowrap;width:fit-content}}
.st-key-cc_header{{align-items:center;gap:1rem!important;justify-content:space-between}}
.st-key-cc_header>.stElementContainer{{flex:0 0 auto!important}}
.st-key-cc_header>.st-key-cc_topbar{{flex:0 0 auto!important;margin-left:auto}}
.wp-sidebar-brand{{font-size:1.45rem;margin-bottom:.6rem}}
@media(max-width:600px){{.wp-brand{{font-size:1.3rem;padding:5px 8px}}.st-key-cc_header{{flex-wrap:wrap!important;gap:.5rem!important}}}}
/* Sidebar navigation: page buttons as a vertical list; the active page is highlighted. */
[data-testid="stSidebar"] .st-key-cc_nav button{{justify-content:flex-start;text-align:left}}
[data-testid="stSidebar"] .st-key-cc_nav [data-testid="stBaseButton-primary"]{{box-shadow:inset 4px 0 0 var(--cc-focus)}}
/* Team button pinned to the bottom of the sidebar, whatever pages add to the sidebar later. */
[data-testid="stSidebarUserContent"]{{min-height:calc(100vh - 5rem);display:flex;flex-direction:column}}
[data-testid="stSidebarUserContent"]>div{{flex:1 1 auto;display:flex;flex-direction:column}}
[data-testid="stSidebarUserContent"]>div>[data-testid="stVerticalBlock"]{{flex:1 1 auto}}
.st-key-cc_team,[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"]>div:has(>.st-key-cc_team){{order:99;margin-top:auto!important;padding-top:1rem}}
/* Header strip: flag buttons and theme switch, top right. Labels stay in the DOM for screen readers. */
.st-key-cc_topbar{{gap:.4rem!important}}
.st-key-lang_en button,.st-key-lang_tr button{{width:44px;min-height:30px;height:30px;padding:0!important;background-size:cover!important;
  background-position:center!important;border:2px solid var(--cc-border)!important;border-radius:6px}}
.st-key-lang_en button{{background-image:url("{flags['en']}")!important}}
.st-key-lang_tr button{{background-image:url("{flags['tr']}")!important}}
.st-key-lang_en button[data-testid="stBaseButton-primary"],.st-key-lang_tr button[data-testid="stBaseButton-primary"]{{border:3px solid var(--cc-focus)!important;box-shadow:0 0 0 2px var(--cc-bg)}}
.st-key-lang_en button p,.st-key-lang_tr button p,.st-key-theme_toggle button p{{position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}}
.st-key-theme_toggle button{{min-height:30px;height:30px;width:40px;padding:0!important}}
/* Compact only the researcher workflow; leave every other workspace unchanged. */
[data-testid="stMainBlockContainer"]:has(.st-key-wf_candidate){{padding-top:3.75rem!important}}
[data-testid="stMainBlockContainer"]:has(.st-key-wf_candidate) h1{{font-size:2rem;padding-top:0}}
[data-testid="stMainBlockContainer"]:has(.st-key-wf_candidate) .st-key-cc_topbar{{margin-bottom:-.5rem}}
/* Glossary terms: dotted underline; definition shown on hover, keyboard focus or tap. */
.cc-term{{position:relative;border-bottom:1px dotted currentColor;cursor:help;outline:none}}
.cc-term .cc-tip{{display:none;visibility:hidden;opacity:0;position:absolute;left:0;top:calc(100% + 6px);z-index:1000;width:max-content;max-width:min(280px,70vw);
  background:var(--cc-tip-bg);color:var(--cc-tip-text)!important;padding:8px 10px;border-radius:8px;font-size:.82rem;line-height:1.35;
  font-weight:400;box-shadow:0 4px 14px rgba(0,0,0,.25);transition:opacity .12s;pointer-events:none;white-space:normal}}
.cc-term:hover .cc-tip,.cc-term:focus .cc-tip,.cc-term:focus-within .cc-tip{{display:block;visibility:visible;opacity:1}}
</style>'''


def themed_map_html(html, theme=None, lang=None):
    """Theme map legends and language while preserving the OpenStreetMap basemap."""
    k = tokens(theme)
    html = html.replace('background:white', f"background:{k['surface']};color:{k['text']}")
    from src.i18n import current_lang, map_replacements
    for english, translated in map_replacements(lang or current_lang()):
        html = html.replace(english, translated)
    return html
