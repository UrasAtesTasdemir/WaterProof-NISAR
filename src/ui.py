"""Small rendering helpers shared by every page (language and theme aware)."""
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import FuncFormatter
import pandas as pd
import streamlit as st

from src.glossary import md as glossary_md
from src.i18n import current_lang, num, t
from src.theme import apply_matplotlib


def markdown(text, **kwargs):
    """Markdown with glossary tooltips ([[key]] markers)."""
    st.markdown(glossary_md(text), unsafe_allow_html=True, **kwargs)


def caption(text):
    st.caption(glossary_md(text), unsafe_allow_html=True)


def _decimal_comma(axis):
    formatter = axis.get_major_formatter()
    if isinstance(formatter, (DateFormatter, FuncFormatter)) or type(formatter).__module__.startswith('matplotlib.dates'):
        return
    def fmt(value, position, base=formatter):
        return base(value, position).replace('.', ',').replace('−', '−')
    axis.set_major_formatter(FuncFormatter(fmt))


def pyplot(fig):
    """Show a matplotlib figure (decimal comma on numeric axes in Turkish), then free it."""
    if current_lang() == 'tr':
        fig.canvas.draw()
        for ax in fig.axes:
            for axis in (ax.xaxis, ax.yaxis):
                _decimal_comma(axis)
    st.pyplot(fig)
    plt.close(fig)


def new_figure(*args, **kwargs):
    """plt.subplots with the current theme's colours applied first."""
    apply_matplotlib()
    kwargs.setdefault('layout', 'constrained')
    return plt.subplots(*args, **kwargs)


def _cell(value, lang):
    if isinstance(value, bool) or value is None:
        return {True: t('common.yes', lang=lang), False: t('common.no', lang=lang), None: '–'}[value]
    if isinstance(value, float):
        digits = 0 if value.is_integer() and abs(value) >= 100 else 3 if abs(value) < 10 else 2
        return num(value, digits, lang=lang)
    if isinstance(value, int):
        return value
    if isinstance(value, (list, tuple, dict)):
        return str(value)
    return value


def table(rows, height=None):
    """Theme-following HTML table (st.dataframe draws on a canvas that CSS cannot recolour).

    English shows raw values; Turkish localizes numbers, booleans and known column names."""
    from src.locales import COLUMNS_TR
    lang = current_lang()
    frame = pd.DataFrame(list(rows))
    if lang == 'tr':
        frame = frame.rename(columns=lambda c: COLUMNS_TR.get(c, c))
        frame = frame.map(lambda v: _cell(v, lang))
    else:
        frame = frame.map(lambda v: str(v) if isinstance(v, (list, tuple, dict)) else v)
    kwargs = dict(hide_index=True)
    if height:
        kwargs['height'] = height
    st.table(frame, **kwargs)
