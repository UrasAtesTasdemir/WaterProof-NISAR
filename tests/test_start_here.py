"""'Start here' opening panel, guided example and an all-pages render sweep (EN/TR, light/dark). No network."""
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
NO_NET = dict(target='requests.sessions.Session.request', side_effect=AssertionError('Network disabled'))


def _app(timeout=120):
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(ROOT / 'app.py'), default_timeout=timeout).run()


class StartHereTests(unittest.TestCase):
    def test_first_visit_opens_start_here_on_explore(self):
        with patch(**NO_NET):
            app = _app()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['workspace'], 'Explore the world')
            self.assertTrue(app.session_state['start_open'])
            self.assertEqual(app.subheader[0].value, 'Start here')
            text = ' '.join(m.value for m in app.markdown)
            for phrase in ('1. Select an example', '2. Observe the change', '3. Check uncertainty', '4. Investigate next',
                           'The problem', 'What this tool does NOT claim', 'Thailand and Gandak have case-specific comparisons'):
                self.assertIn(phrase, text)
            self.assertNotIn('Nothing here has been checked', text)
            self.assertTrue(any('New locations do not inherit those results' in c.value for c in app.caption))
            self.assertEqual(app.button(key='start_research').label, 'Investigate a Louisiana candidate')
            self.assertEqual(app.button(key='start_guided').label, 'Take the guided example')
            self.assertEqual(app.button(key='start_guided').proto.type, 'primary')

    def test_collapse_and_expand(self):
        with patch(**NO_NET):
            app = _app()
            app.button(key='start_hide').click().run()
            self.assertFalse(app.exception)
            self.assertFalse(app.session_state['start_open'])
            self.assertFalse(any(s.value == 'Start here' for s in app.subheader))
            self.assertEqual(app.button(key='start_show').label, 'Show “Start here”')
            app.button(key='start_show').click().run()
            self.assertTrue(app.session_state['start_open'])
            self.assertTrue(any(s.value == 'Start here' for s in app.subheader))

    def test_guided_example_is_the_offline_thailand_flood_case(self):
        with patch(**NO_NET), patch('src.nisar_data.open_frequency_a', side_effect=AssertionError('no live read')):
            app = _app()
            self.assertEqual(app.selectbox(key='ex_preset').options[0], 'Guided example: Thailand flood, Prachin Buri (cached, works offline)')
            # change the pair and the place first, then take the guided example
            app.selectbox(key='ex_pair_guided_thailand_prachinburi').select((0, 1)).run()
            app.selectbox(key='ex_preset').select('louisiana').run()
            app.button(key='start_guided').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['ex_preset'], 'thailand_prachinburi')
            self.assertFalse(app.session_state['start_open'])
            pair = app.selectbox(key='ex_pair_guided_thailand_prachinburi')
            self.assertEqual(pair.value, (0, 2))
            self.assertEqual(pair.format_func(pair.value), '2026-09-06 → 2026-09-30')
            captions = ' '.join(c.value for c in app.caption)
            self.assertIn('Example pair: 6 → 30 Sep 2026, the saved Thailand 004 D comparison', captions)
            text = ' '.join(m.value for m in app.markdown)
            self.assertIn('Candidate new open water in this window: 25.7% of valid pixels (25.67 km²)', text)   # = saved stage d
            self.assertIn('Dates and window are those of the reference-comparison protocol', text)
            app.selectbox(key='ex_pair_guided_thailand_prachinburi').select((0, 1)).run()        # negative control
            self.assertFalse(app.exception)
            self.assertIn('(3.14 km²), 2026-09-06 → 2026-09-18', ' '.join(m.value for m in app.markdown))

    def test_louisiana_candidate_1_keeps_its_seed_pair_and_limits(self):
        from src.explore import GUIDED_EXAMPLE_PAIR
        with patch(**NO_NET):
            app = _app()
            app.selectbox(key='ex_preset').select('louisiana_c1').run()
            self.assertFalse(app.exception)
            pair = app.selectbox(key='ex_pair_guided_louisiana_c1')
            self.assertEqual(pair.value, (1, 2))
            self.assertEqual(pair.format_func(pair.value), f'{GUIDED_EXAMPLE_PAIR[0]} → {GUIDED_EXAMPLE_PAIR[1]}')
            self.assertIn(f'{GUIDED_EXAMPLE_PAIR[0][:4]}-06-21 → 2026-09-01', pair.options)  # first-to-last stays one click away
            captions = ' '.join(c.value for c in app.caption)
            self.assertIn('Example pair: the saved screening flagged this interval for candidate 1', captions)
            self.assertIn('including first-to-last, are one click away', captions)
            text = ' '.join(m.value for m in app.markdown)
            self.assertIn('Candidate 1’s own limits', text)
            self.assertIn('not notable when 2026-07-15 is removed', text)      # seed change depends on 15 Jul
            self.assertIn('74 pixels', text)                                      # small region
            self.assertIn('HV may be near the noise floor', text)                 # HV dark-level caution
            self.assertIn('diluted', text)                                        # 500 m square vs footprint, both shown
            # the inconclusive first-to-last comparison is still reachable and shown as computed
            app.selectbox(key='ex_pair_guided_louisiana_c1').select((0, 5)).run()
            self.assertFalse(app.exception)
            self.assertTrue(any('Compass reading' in m.value for m in app.markdown))

    def test_turkish_start_here(self):
        with patch(**NO_NET):
            app = _app()
            app.button(key='lang_tr').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.subheader[0].value, 'Buradan başlayın')
            self.assertEqual(app.button(key='start_guided').label, 'Rehberli örneği açın')
            self.assertTrue(any('Örnek çift' in c.value for c in app.caption))

    def test_start_strings_have_identical_keys_and_placeholders(self):
        from src.locales import start
        from src.i18n import PLACEHOLDER
        self.assertEqual(set(start.EN), set(start.TR))
        for key in start.EN:
            self.assertEqual(set(PLACEHOLDER.findall(start.EN[key])), set(PLACEHOLDER.findall(start.TR[key])), key)
        for forbidden in ('confirmed flood', 'accuracy of', 'validated'):
            self.assertFalse(any(forbidden in v.lower() for v in start.EN.values()), forbidden)


class AllPagesRenderTests(unittest.TestCase):
    def test_every_page_and_view_renders_in_both_languages_and_themes(self):
        from src.navigation import PAGES, CASE_VIEWS, apptest_open
        with patch(**NO_NET), patch('src.explore_panel.search_catalog', side_effect=AssertionError('no catalog')):
            for lang in ('en', 'tr'):
                for theme in ('light', 'dark'):
                    app = _app(180)
                    if lang == 'tr':
                        app.button(key='lang_tr').click().run()
                    if theme == 'dark':
                        app.button(key='theme_toggle').click().run()
                    self.assertEqual(app.session_state['theme'], theme)
                    for key in PAGES + CASE_VIEWS:
                        apptest_open(app, key)
                        self.assertFalse(app.exception, (lang, theme, key, [e.value for e in app.exception][:1]))


if __name__ == '__main__':
    unittest.main()
