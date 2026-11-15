"""Regression tests for the hardening-phase defects (one or more per defect)."""
from datetime import datetime, timezone
from pathlib import Path
import unittest

from shapely.geometry import box

from src.change_compass import percent_ranges, rectangle_mask
from src.navigation import apptest_open

ROOT = Path(__file__).resolve().parents[1]


class RectangleBoundsTests(unittest.TestCase):
    """Defect 1: equal slider ends near 100 produced an upper bound of 1.01."""

    def test_equal_ends_at_100_stay_inside_unit_range(self):
        rows, cols = percent_ranges((100, 100), (100, 100))
        self.assertEqual(rows, (0.99, 1.0)); self.assertEqual(cols, (0.99, 1.0))
        self.assertTrue(rectangle_mask((257, 579), rows, cols).any())

    def test_equal_ends_at_zero_and_reversed_ends(self):
        self.assertEqual(percent_ranges((0, 0), (40, 20))[0], (0.0, 0.01))
        self.assertEqual(percent_ranges((0, 0), (40, 20))[1], (0.2, 0.4))

    def test_out_of_range_raises_value_error(self):
        with self.assertRaises(ValueError):
            percent_ranges((0, 101), (0, 50))

    def test_page_shows_no_traceback_for_degenerate_rectangle(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
        apptest_open(app,'Change Compass')
        app.radio(key='compass_mode').set_value('Rectangle').run()
        for value in ((100, 100), (0, 0), (57, 57)):
            app.slider(key='compass_cols').set_value(value).run()
            self.assertFalse(app.exception, value)
        app.slider(key='compass_rows').set_value((100, 100)).run()
        self.assertFalse(app.exception)
        self.assertTrue(any('widened' in c.value for c in app.caption))


class SharedCoverageTests(unittest.TestCase):
    """Defect 2: shared coverage must be a footprint intersection, not min()."""

    def obs(self, footprint, coverage):
        return dict(footprint_in_aoi=footprint, aoi_area=4.0, coverage=coverage)

    def test_disjoint_halves_share_nothing(self):
        from src.visibility import shared_coverage
        left, right = self.obs(box(0, 0, 1, 2), .5), self.obs(box(1, 0, 2, 2), .5)
        value, method = shared_coverage(left, right)
        self.assertEqual(value, 0.0)
        self.assertEqual(method, 'geometric intersection')

    def test_missing_footprint_is_labelled_upper_bound(self):
        from src.visibility import shared_coverage
        value, method = shared_coverage(self.obs(None, .5), self.obs(box(0, 0, 2, 2), 1.0))
        self.assertEqual(value, .5)
        self.assertIn('upper bound', method)

    def test_real_cases_use_geometry_and_match_stored_single_date_coverage(self):
        from src.visibility import louisiana, kerrville
        for case in (louisiana(), kerrville()):
            for o in case['observations']:
                self.assertIsNotNone(o['footprint_in_aoi'])
                self.assertAlmostEqual(min(1, o['footprint_in_aoi'].area / o['aoi_area']), o['coverage'], places=9)
            self.assertTrue(all(p['coverage_method'] == 'geometric intersection' for p in case['pairs']))
        track142 = [p for p in kerrville()['pairs'] if p['track'] == 142][0]
        self.assertAlmostEqual(track142['coverage'], 0.4821, places=3)


class WordingTests(unittest.TestCase):
    """Defects 3 and 4: stale HV text and score-like 'Confidence' naming."""

    def test_time_series_method_text_is_current(self):
        # The method text moved into the translation layer (both languages are checked).
        from src.i18n import t
        for lang in ('en', 'tr'):
            text = (ROOT / 'src/time_series_panel.py').read_text() + t('ts.method_text', lang=lang)
            self.assertNotIn('HV analysis is pending', text)
            self.assertIn('HVHV', text)

    def test_no_confidence_page_or_score_wording(self):
        from src.navigation import PAGES, LABELS
        self.assertNotIn('Confidence', PAGES)
        self.assertFalse(any('confidence' in label.lower() for label in LABELS.values()))
        for name in ('src/evidence.py', 'src/evidence_panel.py', 'src/locales/evidence.py'):
            text = (ROOT / name).read_text().lower()
            self.assertNotIn('reliability indicator', text)
            self.assertNotIn('confidence score:', text)

    def test_license_is_mit(self):
        self.assertTrue((ROOT / 'LICENSE').read_text().startswith('MIT License'))


if __name__ == '__main__':
    unittest.main()
