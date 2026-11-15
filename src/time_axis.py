"""Shared helper: make acquisition gaps visible on every time-axis plot."""
from datetime import datetime, timedelta

NOMINAL_REPEAT_DAYS = 12


def gaps_from_times(times, nominal_days=NOMINAL_REPEAT_DAYS):
    """(start, end, days) for consecutive acquisitions further apart than the nominal repeat."""
    ordered = sorted(times)
    return [(a, b, (b - a).total_seconds() / 86400) for a, b in zip(ordered, ordered[1:])
            if (b - a) > timedelta(days=nominal_days + 1)]


def mark_gaps(ax, times, nominal_days=NOMINAL_REPEAT_DAYS):
    """Shade and label intervals with a missing acquisition (e.g. 27 Jul → 20 Aug = 24 days).

    Returns the gaps so callers can mention them in captions."""
    from src.i18n import t
    from src.theme import palette
    colors = palette()
    gaps = gaps_from_times(times, nominal_days)
    for index, (a, b, days) in enumerate(gaps):
        ax.axvspan(a, b, color=colors['gap_fill'], alpha=.6, zorder=0,
                   label=t('time.gap_label', days=f'{days:.0f}') if index == 0 else None)
        ax.annotate(t('time.gap_short', days=f'{days:.0f}'), xy=(a + (b - a) / 2, 1), xycoords=('data', 'axes fraction'),
                    ha='center', va='top', fontsize=7, color=colors['gap_text'])
    return gaps


def gap_caption(times, lang=None):
    from src.i18n import t, current_lang
    lang = lang or current_lang()
    gaps = gaps_from_times(times)
    if not gaps:
        return t('time.no_gap', lang=lang)
    pattern = '%d %b' if lang == 'en' else '%d.%m'
    items = '; '.join(t('time.gap_item', lang=lang, start=f'{a:{pattern}}', end=f'{b:{pattern}}', days=f'{d:.0f}') for a, b, d in gaps)
    return t('time.gap_caption', lang=lang, items=items)


def as_datetimes(values):
    return [v if isinstance(v, datetime) else datetime.fromisoformat(str(v).replace('Z', '+00:00')) for v in values]
