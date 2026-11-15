"""Streamlit widget tests on actual cached NISAR data, without network access."""
import csv
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from src.dashboard_data import prepare_data,calculate
from src.navigation import apptest_open
ROOT=Path(__file__).resolve().parents[1]

class DashboardTests(unittest.TestCase):
    def test_real_widget_metrics_update_without_network_or_output_changes(self):
        paths=[p for folder in ('data/subsets','data/water_change','data/scientific_quality_check') for p in (ROOT/folder).rglob('*') if p.is_file()]
        before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        expected={float(r['water_threshold_db']):r for r in csv.DictReader((ROOT/'data/scientific_quality_check/threshold_sensitivity.csv').open())}
        with patch('requests.sessions.Session.request',side_effect=AssertionError('Network disabled for dashboard test')):
            app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run();apptest_open(app,'NISAR study')  # Explore (with "Start here") is the landing page
            self.assertFalse(app.exception)
            self.assertEqual(len(app.slider),2)
            self.assertEqual(len(app.metric),4)
            for threshold in (-16.,-14.,-18.,-20.):
                app.slider(key='water_threshold').set_value(threshold).run()
                self.assertFalse(app.exception)
                metrics={m.label:m.value for m in app.metric}
                self.assertEqual(metrics['Candidate expansion'],f"{float(expected[threshold]['expansion_km2']):.4f} km²")
                self.assertEqual(metrics['Candidate recession'],f"{float(expected[threshold]['recession_km2']):.4f} km²")
                self.assertEqual(metrics['Valid comparison area'],'13.8779 km²')
            app.slider(key='water_threshold').set_value(-16.).run()
            original=app.metric[0].value
            app.slider(key='minimum_change').set_value(0.).run()
            calculated=calculate(prepare_data(),-16,0)
            self.assertEqual(app.metric[0].value,f"{calculated['expansion']:.4f} km²")
            self.assertNotEqual(app.metric[0].value,original)
            app.slider(key='minimum_change').set_value(8.).run()
            self.assertFalse(app.exception)
            calculated=calculate(prepare_data(),-16,8)
            self.assertEqual(app.metric[0].value,f"{calculated['expansion']:.4f} km²")
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

    def test_missing_files_show_recovery_message(self):
        with patch('src.dashboard_data.input_signature',side_effect=FileNotFoundError('test fixture')):
            app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run();apptest_open(app,'NISAR study')  # Explore (with "Start here") is the landing page
            self.assertFalse(app.exception)
            self.assertTrue(app.error)
            self.assertIn('No download was attempted',app.error[0].value)

    def test_invalid_thresholds_rejected(self):
        for water,minimum in ((-30,3),(-16,-1),(-16,9),(float('nan'),3)):
            with self.assertRaises(ValueError):calculate({},water,minimum)

if __name__=='__main__':unittest.main()
