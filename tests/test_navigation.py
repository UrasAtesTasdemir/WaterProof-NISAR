"""Six-page sidebar navigation; legacy workspaces reachable as Louisiana views."""
from pathlib import Path
import unittest
from unittest.mock import patch

from src.navigation import apptest_open

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ('NISAR study', 'Geographic map (NISAR)', 'HH time series (six dates)', 'Polarization Analysis',
          'Scientific Diagnostics', 'Investigation Explorer', 'Benchmark Validation (Sentinel-1)')


class NavigationTests(unittest.TestCase):
    def test_six_pages_and_legacy_views(self):
        from src.navigation import PAGES, CASE_VIEWS, DEFAULT_PAGE, APP_NAME, page_label
        self.assertEqual(PAGES, ('Explore the world', 'Researcher workflow', 'NISAR study', 'Is this scene analyzable?',
                                 'Flood validation (Thailand, Gandak)', 'Benchmark Validation (Sentinel-1)', 'About'))
        for key in LEGACY:
            self.assertIn(key, PAGES + CASE_VIEWS)
        self.assertEqual(DEFAULT_PAGE, 'Explore the world')
        self.assertTrue(page_label('Benchmark Validation (Sentinel-1)').startswith('Appendix'))
        self.assertEqual(page_label('NISAR study'), 'Louisiana wetland radar-change case study')
        self.assertIn('cached cases', page_label('Is this scene analyzable?'))
        self.assertNotIn('Flood', APP_NAME)
        self.assertNotIn('Confidence', PAGES + CASE_VIEWS)

    def test_apptest_helper_rejects_unknown_pages(self):
        from src.navigation import apptest_open
        with self.assertRaises(ValueError):
            apptest_open(None, 'Overview')

    def test_landing_page_and_about_entry_points(self):
        from streamlit.testing.v1 import AppTest
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Network disabled')):
            app = AppTest.from_file(str(ROOT/'app.py'), default_timeout=60).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['workspace'], 'Explore the world')  # landing page with 'Start here'
            self.assertEqual(app.title[0].value, 'Explore the world')
            self.assertTrue(app.session_state['start_open'])
            apptest_open(app, 'About')
            self.assertFalse(app.exception)
            text = ' '.join(m.value for m in app.markdown)
            for phrase in ('Claude Code', 'ChatGPT / Codex', 'MIT License', 'hard to trust'):
                self.assertIn(phrase, text)
            app.button(key='about_go_NISAR study').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['workspace'], 'NISAR study')
            self.assertEqual(app.selectbox(key='case_view').value, 'Change dashboard')
            self.assertEqual(app.metric[0].value, '0.0569 km²')
            for view in ('Change Compass', 'Evidence & limitations', 'Geographic map (NISAR)'):
                apptest_open(app, view)
                self.assertFalse(app.exception, view)
            apptest_open(app, 'Is this scene analyzable?')
            self.assertFalse(app.exception)
            self.assertEqual(app.title[0].value, 'Is this scene analyzable?')

    def test_case_map_uses_current_classes_and_actual_footprint(self):
        from src.dashboard_data import prepare_data, calculate
        from src.case_map import classes_map_html, valid_footprint
        data = prepare_data()
        result = calculate(data, -16, 3)
        html = classes_map_html(result['classes'], data['valid'], data['grid'], result['valid_area'])
        for text in ('Candidate water expansion', 'imageOverlay', 'Actual valid processed footprint', '13.8779 km²'):
            self.assertIn(text, html)
        footprint = valid_footprint(data['valid'], data['grid'])
        self.assertEqual(footprint['type'], 'Polygon')
        with self.assertRaises(ValueError):
            valid_footprint(np.zeros((3, 3), bool), data['grid'])
        with self.assertRaises(ValueError):
            classes_map_html(result['classes'][:-1], data['valid'], data['grid'], 1.0)


if __name__ == '__main__':
    unittest.main()
