"""Phase B: app shell, languages, themes, glossary tooltips and the team dialog."""
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from src.i18n import STRINGS, PLACEHOLDER, t, num, integer, percent
from src.glossary import TERMS, UNSURE, md, term
from src.navigation import PAGES, CASE_VIEWS, NAV_KEYS, apptest_open
from src.theme import TOKENS, PALETTE, contrast, css, themed_map_html

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TERMS = ('sar', 'nisar', 'lband', 'backscatter', 'db', 'hh', 'hv', 'polarization', 'gcov', 'speckle', 'threshold',
                  'change_map', 'candidate', 'compass', 'ring', 'lodo', 'scene_change', 'noise_floor', 'acquisition',
                  'track_frame', 'footprint', 'valid_pixel', 'reference', 'hypothesis')


class TranslationTableTests(unittest.TestCase):
    def test_same_keys_no_empty_values_same_placeholders(self):
        en, tr = STRINGS['en'], STRINGS['tr']
        self.assertEqual(set(en), set(tr))
        self.assertGreater(len(en), 700)
        for key in en:
            self.assertTrue(en[key].strip(), key); self.assertTrue(tr[key].strip(), key)
            self.assertEqual(set(PLACEHOLDER.findall(en[key])), set(PLACEHOLDER.findall(tr[key])), key)
            for text in (en[key], tr[key]):
                for marker in re.findall(r'\[\[(\w+)', text):
                    self.assertIn(marker, TERMS, key)

    def test_turkish_wording_keeps_the_hedging(self):
        affirmative_tr = ('teyit edildi', 'doğrulandı', 'kanıtlandı', 'kesinlikle su', 'taşkın var')
        for key, text in STRINGS['tr'].items():
            low = text.lower()
            for phrase in affirmative_tr:
                self.assertNotIn(phrase, low, key)
        for key, text in STRINGS['en'].items():
            for sentence in re.split(r'(?<=[.!?])\s', text):
                if re.search(r'\bconfirmed (flood|water)', sentence):
                    self.assertRegex(sentence, r'\b(not|NOT|no|No)\b', key)   # only ever negated
        # Hedged pattern names stay hedged in Turkish.
        self.assertIn('tutarlı', t('compass.smoother_surface.title', lang='tr'))
        self.assertIn('consistent with', t('compass.smoother_surface.title', lang='en'))

    def test_turkish_numbers_use_decimal_comma(self):
        self.assertEqual(num(-3.6512, 2, sign=True, lang='tr'), '-3,65')
        self.assertEqual(num(13877.9, 1, lang='tr'), '13.877,9')
        self.assertEqual(num(13877.9, 1, lang='en'), '13,877.9')
        self.assertEqual(integer(138779, lang='tr'), '138.779')
        self.assertEqual(percent(.482, 1, lang='tr'), '%48,2')
        self.assertEqual(percent(.482, 1, lang='en'), '48.2%')


class GlossaryTests(unittest.TestCase):
    def test_required_terms_in_both_languages_and_short(self):
        for key in REQUIRED_TERMS:
            self.assertIn(key, TERMS)
        for key, entry in TERMS.items():
            for lang in ('en', 'tr'):
                label, text = entry[lang]
                self.assertTrue(label and text, (key, lang))
                self.assertLessEqual(len(re.findall(r'[.!?](\s|$)', text)), 2, (key, lang))
                self.assertLessEqual(len(text), 200, (key, lang))
        self.assertTrue(set(UNSURE) <= set(TERMS))

    def test_tooltip_markup_is_keyboard_and_screen_reader_accessible(self):
        html = term('hh', lang='en')
        self.assertIn('tabindex="0"', html); self.assertIn('role="tooltip"', html); self.assertIn('aria-label=', html)
        self.assertIn('cc-term', md('Look at [[hv|this HV]] change', lang='tr'))
        self.assertIn('Yatay', md('[[hv]]', lang='tr'))

    def test_review_file_lists_every_definition(self):
        text = (ROOT / 'docs/glossary_review.md').read_text()
        for entry in TERMS.values():
            for lang in ('en', 'tr'):
                self.assertIn(entry[lang][1], text)


class ThemeTests(unittest.TestCase):
    def test_text_tokens_meet_wcag_aa(self):
        for name, k in TOKENS.items():
            for fg, bg in (('text', 'bg'), ('text', 'surface'), ('text', 'surface2'), ('heading', 'bg'), ('muted', 'bg'),
                           ('muted', 'surface'), ('muted', 'surface2'), ('link', 'bg'), ('link', 'surface'), ('on_primary', 'primary'),
                           ('warn_text', 'warn_bg'), ('info_text', 'info_bg'), ('error_text', 'error_bg'), ('ok_text', 'ok_bg'),
                           ('tip_text', 'tip_bg')):
                self.assertGreaterEqual(contrast(k[fg], k[bg]), 4.5, (name, fg, bg))

    def test_chart_and_class_colours_are_visible_on_both_backgrounds(self):
        for name, colours in PALETTE.items():
            bg = TOKENS[name]['surface']
            for key in ('hh', 'hv', 'first', 'second', 'expansion', 'recession', 'event', 'nisar', 'optical_ok', 'optical_bad'):
                self.assertGreaterEqual(contrast(colours[key], bg), 3.0, (name, key))
            for index in (1, 2, 3):   # persistent, new, receded water candidate classes
                self.assertGreaterEqual(contrast(colours['classes'][index], bg), 3.0, (name, index))

    def test_css_and_maps_follow_the_theme(self):
        self.assertIn(TOKENS['dark']['bg'], css('dark')); self.assertIn(TOKENS['light']['bg'], css('light'))
        html = '<script>L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png")</script><div style="background:white">x</div>'
        dark = themed_map_html(html, 'dark', 'en')
        self.assertIn('tile.openstreetmap.org', dark); self.assertNotIn('background:white', dark)
        self.assertNotIn('cartocdn', dark)
        self.assertIn(TOKENS['dark']['surface'], dark)
        self.assertIn('tile.openstreetmap.org', themed_map_html(html, 'light', 'en'))


def _app():
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(ROOT / 'app.py'), default_timeout=90).run()


class ShellAppTests(unittest.TestCase):
    def test_language_switch_translates_page_note_and_navigation(self):
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Network disabled')):
            app = apptest_open(_app(), 'Researcher workflow')
            self.assertFalse(app.exception)
            self.assertEqual(app.title[0].value, 'Researcher workflow')
            self.assertEqual(app.button(key='lang_en').proto.type, 'primary')
            app.button(key='lang_tr').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['lang'], 'tr')
            self.assertEqual(app.title[0].value, 'Araştırmacı iş akışı')
            self.assertEqual(app.button(key='lang_tr').proto.type, 'primary')
            self.assertEqual(app.button(key=NAV_KEYS['About']).label, 'Hakkında')
            note = next(m.value for m in app.markdown if m.value.startswith('# İnceleme notu'))
            self.assertIn('doğrulanmamıştır', note)
            self.assertRegex(note, r'[+-]\d+,\d\d dB')
            self.assertTrue(any('En önemli belirsizlik' in m.value for m in app.markdown))
            app.button(key='lang_en').click().run()
            self.assertEqual(app.title[0].value, 'Researcher workflow')

    def test_language_switch_keeps_selections(self):
        """Streamlit identifies a selectbox choice by its label; switching language must not lose or corrupt it."""
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Network disabled')):
            app = apptest_open(_app(), 'Researcher workflow')
            app.selectbox(key='wf_candidate').select(3).run()
            app.selectbox(key='wf_pair').select((3, 4)).run()
            for lang in ('tr', 'en', 'tr'):
                app.button(key=f'lang_{lang}').click().run()
                self.assertFalse(app.exception, lang)
                self.assertEqual(app.selectbox(key='wf_candidate').value, 3)
                self.assertEqual(app.selectbox(key='wf_pair').value, (3, 4))
            apptest_open(app, 'Investigation Explorer')
            app.selectbox(key='investigation_region').select(2).run()
            app.button(key='lang_en').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.selectbox(key='investigation_region').value, 2)
            self.assertEqual(app.selectbox(key='case_view').value, 'Investigation Explorer')

    def test_theme_switch_rerenders_without_recomputing_data(self):
        import src.workflow_panel as panel
        panel.cached_inputs.clear()
        calls = []
        real = panel.load_inputs
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Network disabled')), \
             patch.object(panel, 'load_inputs', side_effect=lambda: calls.append(1) or real()):
            app = apptest_open(_app(), 'Researcher workflow')    # the page that loads the heavy inputs
            self.assertEqual(app.session_state['theme'], 'light')
            app.button(key='theme_toggle').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['theme'], 'dark')
            self.assertTrue(any(TOKENS['dark']['bg'] in m.value for m in app.markdown))
            app.button(key='lang_tr').click().run(); app.button(key='theme_toggle').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['theme'], 'light')
            self.assertEqual(len(calls), 1)   # heavy inputs loaded once; language/theme changes only re-render

    def test_team_dialog_shows_exactly_the_two_creators(self):
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Network disabled')):
            for lang, heading in (('en', 'Creators'), ('tr', 'Oluşturucular')):
                app = _app()
                app.button(key=f'lang_{lang}').click().run()
                app.button(key='team_button').click().run()
                self.assertFalse(app.exception)
                self.assertEqual(t('team.heading', lang=lang), heading)
                names = [m.value for m in app.markdown if m.value in ('**Uras Ateş Taşdemir**', '**Ali Semih Salum**')]
                self.assertEqual(names, ['**Uras Ateş Taşdemir**', '**Ali Semih Salum**'])
                dialog_text = ' '.join(m.value for m in app.markdown)
                self.assertNotIn('@', dialog_text.split('Uras Ateş Taşdemir')[-1][:200])

    def test_every_page_and_view_renders_in_both_languages_and_themes(self):
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Network disabled')):
            app = _app()
            for lang in ('en', 'tr'):
                app.button(key=f'lang_{lang}').click().run()
                for theme in ('light', 'dark'):
                    if app.session_state['theme'] != theme:
                        app.button(key='theme_toggle').click().run()
                    for key in PAGES + CASE_VIEWS:
                        apptest_open(app, key)
                        self.assertFalse(app.exception, (lang, theme, key, app.exception))
                        self.assertTrue(app.title, (lang, theme, key))
                        if key in PAGES:
                            self.assertEqual(app.button(key=NAV_KEYS[key]).proto.type, 'primary', (lang, key))
            self.assertIn('Dünyayı keşfet', [b.label for b in app.button])


if __name__ == '__main__':
    unittest.main()
