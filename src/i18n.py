"""Translation layer: one function `t(key)` for all user-facing text, EN and TR.

Strings live in src/locales/<module>.py as side-by-side EN / TR dictionaries and are
merged here. English is the default and the fallback. Numbers go through `num`,
`integer` and `percent`, which use a decimal comma (and Turkish percent order) for TR.
Pure modules pass `lang=` explicitly; Streamlit pages use the session language.
"""
import re

LANGS = ('en', 'tr')
DEFAULT_LANG = 'en'
LANG_NAMES = {'en': 'English', 'tr': 'Türkçe'}


def _load():
    from src.locales import EN, TR
    return {'en': EN, 'tr': TR}


STRINGS = _load()
PLACEHOLDER = re.compile(r'{(\w+)(?:[:!][^}]*)?}')


def current_lang():
    """Session language inside a Streamlit run; English elsewhere (tests, scripts)."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx(suppress_warning=True) is None:
            return DEFAULT_LANG
        import streamlit as st
        lang = st.session_state.get('lang', DEFAULT_LANG)
    except Exception:  # noqa: BLE001 - no Streamlit context: fall back to English
        return DEFAULT_LANG
    return lang if lang in LANGS else DEFAULT_LANG


def t(key, lang=None, **values):
    lang = lang or current_lang()
    text = STRINGS.get(lang, {}).get(key) or STRINGS[DEFAULT_LANG].get(key)
    if text is None:
        raise KeyError(f'Missing translation key: {key}')
    return text.format(**values) if values else text


def has(key):
    return key in STRINGS[DEFAULT_LANG]


def _swap(text):
    return text.replace(',', '\u0000').replace('.', ',').replace('\u0000', '.')


def num(value, digits=2, sign=False, lang=None):
    """Formatted number: 1,234.56 (EN) or 1.234,56 (TR). None → '–'."""
    if value is None:
        return '–'
    text = f"{value:{'+' if sign else ''},.{digits}f}"
    return _swap(text) if (lang or current_lang()) == 'tr' else text


def integer(value, lang=None):
    if value is None:
        return '–'
    text = f'{int(value):,}'
    return _swap(text) if (lang or current_lang()) == 'tr' else text


def percent(fraction, digits=0, lang=None):
    """0.482 → '48%' (EN) or '%48' (TR)."""
    if fraction is None:
        return '–'
    body = num(100 * fraction, digits, lang=lang)
    return f'%{body}' if (lang or current_lang()) == 'tr' else f'{body}%'


def saved_text(text, lang=None):
    """Text read from saved English reports is shown as is, labelled in TR."""
    if (lang or current_lang()) == 'tr' and text:
        return f"{text} {t('common.saved_english', lang='tr')}"
    return text


def map_replacements(lang):
    """(English, translated) pairs applied to Leaflet legend/tooltip HTML from the map builders."""
    if lang != 'tr':
        return []
    from src.locales import MAP_PAIRS_TR
    return MAP_PAIRS_TR
