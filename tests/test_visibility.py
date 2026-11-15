"""'Is this scene analyzable?' reads cached inventories faithfully."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest.mock import patch

from src.visibility import compatible_pairs, reference_rows, louisiana, kerrville, case_summary, USABLE_FRACTION
from src.navigation import apptest_open

ROOT = Path(__file__).resolve().parents[1]


def obs(day, track=1, coverage=1.0, frame=1):
    return dict(product_id=f'P{day}{track}', time=datetime(2026, 7, day, tzinfo=timezone.utc), track=track, frame=frame,
                direction='ASCENDING', mode='40+5', coverage=coverage)


class VisibilityTests(unittest.TestCase):
    def test_pairs_require_same_geometry_and_use_min_coverage(self):
        pairs = compatible_pairs([obs(1), obs(13, coverage=.5), obs(2, track=2), obs(25)])
        self.assertEqual(len(pairs), 3)
        self.assertTrue(all(p['track'] == 1 for p in pairs))
        self.assertEqual(pairs[0]['coverage'], .5)
        self.assertEqual(len(compatible_pairs([obs(1), obs(13), obs(25)], max_days=12.5)), 2)

    def test_reference_reasons(self):
        rows = reference_rows([
            dict(product_id='OPERA_L3_DSWx-HLS_a', t='2026-07-01T00:00:00Z', valid_fraction=.9, class_counts={'0': 9, '253': 1}, aoi_pixel_centers=10),
            dict(product_id='OPERA_L3_DSWx-HLS_b', t='2026-07-02T00:00:00Z', valid_fraction=0, class_counts={'253': 10}, aoi_pixel_centers=10),
            dict(product_id='OPERA_L3_DSWx-S1_c', t='2026-07-03T00:00:00Z', valid_fraction=0, class_counts={'255': 10}, aoi_pixel_centers=10)], 't')
        self.assertEqual([r['reason'] for r in rows], ['usable', 'mostly cloud / cloud shadow', 'mostly no data (outside swath / not observed)'])
        self.assertEqual(rows[2]['collection'], 'DSWx-S1')

    def test_louisiana_from_cache(self):
        case = louisiana(); s = case_summary(case)
        self.assertEqual(s['nisar_acquisitions'], 6)
        self.assertEqual(s['compatible_pairs'], 15)
        self.assertEqual(s['twelve_day_pairs'], 4)
        self.assertEqual(s['optical_inspected'], 10)
        self.assertEqual(s['optical_usable'], 0)
        self.assertFalse(case['event']['documented'])
        self.assertIsNone(s['first_post_event_hours'])
        saved = json.loads((ROOT / 'data/pair_selection/reference_inventory.json').read_text())
        self.assertEqual(sorted(r['valid_fraction'] for r in case['references']), sorted(r['valid_fraction'] for r in saved))
        self.assertTrue(all(p['spans_event'] is None for p in case['pairs']))

    def test_kerrville_from_cache(self):
        case = kerrville(); s = case_summary(case)
        self.assertEqual(s['nisar_acquisitions'], 7)
        self.assertEqual(s['twelve_day_pairs'], 3)
        self.assertAlmostEqual(s['first_post_event_hours'], 39.61, places=1)
        self.assertEqual(s['optical_usable'], 1)
        usable = [r for r in case['references'] if r['usable']]
        self.assertTrue(all(r['hours_from_event'] < 0 for r in usable))  # only usable optical window predates the peak
        self.assertEqual(min(p['coverage'] for p in case['consecutive']), min(
            p['nominal_common_aoi_coverage_fraction'] for p in json.loads((ROOT / 'data/kerrville_feasibility/feasibility.json').read_text())['compatible_12day_pairs']))
        self.assertGreaterEqual(USABLE_FRACTION, .8)

    def test_page_renders_offline(self):
        from streamlit.testing.v1 import AppTest
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Network disabled')):
            app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
            apptest_open(app,'Is this scene analyzable?')
            self.assertFalse(app.exception)
            self.assertEqual((app.metric[0].label, app.metric[0].value), ('NISAR acquisitions (cached search)', '6'))
            self.assertEqual(app.metric[4].value, '7')
            self.assertEqual(app.metric[3].value, '0 of 10')
            self.assertEqual(app.metric[7].value, '1 of 12')
            self.assertTrue(any('39.6 h' in w.value for w in app.warning))
            self.assertTrue(any('Nothing on this page queries NASA live' in i.value for i in app.info))


if __name__ == '__main__':
    unittest.main()
