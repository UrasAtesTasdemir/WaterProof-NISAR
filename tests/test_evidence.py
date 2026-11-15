"""Evidence & limitations checklist reads saved evidence and never claims validation."""
import csv
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from src.evidence import (PASS, WARN, UNKNOWN, SOURCES, louisiana_checklist, kerrville_checklist, summarize, item)
from src.navigation import apptest_open

ROOT = Path(__file__).resolve().parents[1]


class EvidenceTests(unittest.TestCase):
    def test_louisiana_items_match_saved_reports(self):
        items = {i['key']: i for i in louisiana_checklist()}
        rel = json.loads((ROOT / SOURCES['reliability']).read_text())
        self.assertAlmostEqual(items['offset']['evidence']['median_delta_db'], rel['measured_median_delta_db'])
        self.assertIn('-1.39 dB', items['offset']['finding'])
        self.assertIn('62 of 569', items['offset']['finding'])
        self.assertEqual(items['offset']['status'], WARN)
        rows = list(csv.DictReader((ROOT / SOURCES['threshold_csv']).open()))
        self.assertEqual(items['threshold']['evidence']['expansion_km2_by_threshold'][-14.0], float(rows[0]['expansion_km2']))
        self.assertEqual(items['threshold']['status'], WARN)
        self.assertIn('61 of 569', items['singletons']['finding'])
        self.assertIn('431 of 569', items['waterways']['finding'])
        self.assertEqual(items['reference']['status'], UNKNOWN)
        self.assertIn('0% valid', items['reference']['finding'])
        self.assertEqual(items['registration']['status'], PASS)
        self.assertEqual(items['quality_mask']['status'], PASS)
        self.assertEqual(items['cross_pol']['status'], WARN)
        for entry in items.values():
            self.assertTrue(entry['rule']); self.assertTrue((ROOT / entry['source']).exists())

    def test_summary_never_claims_validation(self):
        for items in (louisiana_checklist(), kerrville_checklist()):
            text = summarize(items)['headline'].lower()
            self.assertIn('not', text)
            self.assertNotIn('accuracy', text)
            for entry in items:
                self.assertNotIn('%', entry['title'])
        s = summarize([item('reference', 'x', PASS, 'f', {}, 's')])
        self.assertIn('still not validation', s['headline'])

    def test_kerrville_reports_not_available_and_real_timing(self):
        items = {i['key']: i for i in kerrville_checklist()}
        for key in ('offset', 'threshold', 'singletons', 'waterways'):
            self.assertEqual(items[key]['status'], UNKNOWN)
            self.assertIn('Not available', items[key]['finding'])
        self.assertIn('39.6 h', items['timing']['finding'])
        self.assertIn('before the gauge peak', items['reference']['finding'])
        self.assertIn('0.007% valid', items['reference']['finding'])

    def test_missing_hv_report_becomes_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            for key, rel in SOURCES.items():
                if key == 'hv':
                    continue
                target = Path(tmp) / rel; target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / rel, target)
            items = {i['key']: i for i in louisiana_checklist(tmp)}
            self.assertEqual(items['cross_pol']['status'], UNKNOWN)
            self.assertIn('Not available', items['cross_pol']['finding'])
        with self.assertRaises(ValueError):
            item('x', 'x', 'great', '', {}, '')

    def test_page_renders_offline_for_both_cases(self):
        from streamlit.testing.v1 import AppTest
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Network disabled')):
            app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=40).run()
            apptest_open(app,'Evidence & limitations')
            self.assertFalse(app.exception)
            self.assertTrue(any('not validation' in w.value for w in app.warning))
            self.assertTrue(any('5 caution' in m.value for m in app.markdown))
            self.assertFalse(any('PASS' in m.value or 'passed' in m.value.lower() for m in app.markdown))
            self.assertEqual(len(app.metric), 0)
            app.selectbox(key='evidence_case').select(app.selectbox(key='evidence_case').options[1]).run()
            self.assertFalse(app.exception)
            self.assertTrue(any('Not available' in m.value for m in app.markdown))


if __name__ == '__main__':
    unittest.main()
