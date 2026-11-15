"""Change Compass: rules, real cached pair, provenance and page behaviour."""
from src.navigation import apptest_open
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import rasterio

from src.change_compass import (DIRECTORY, LABELS, compass_label, compass_reading, alternatives_for, COMMON_ALTERNATIVES, region_summary, sector_shares, rectangle_mask,
                                lag_correlation, load_pair, region_options, pair_change, read_raw_hv, sha256)

ROOT = Path(__file__).resolve().parents[1]


def summary_for(h, v, n=500, spread=0.2):
    rng = np.random.default_rng(0)
    hh = h + spread * rng.standard_normal(n); hv = v + spread * rng.standard_normal(n)
    return region_summary(hh[None], hv[None], np.ones((1, n), bool))


class CompassRuleTests(unittest.TestCase):
    def test_each_rule_and_dead_zone(self):
        cases = {(-3, -1): 'smoother_surface', (-3, -0.2): 'hh_darkening', (3, 0): 'hh_brightening', (0, -3): 'volume_loss',
                 (0, 3): 'volume_gain', (3, 3): 'volume_gain', (-0.5, 0.4): 'inconclusive', (-3, 0.8): 'inconclusive'}
        for (h, v), key in cases.items():
            self.assertEqual(compass_label(summary_for(h, v))['key'], key, (h, v))
        self.assertEqual(compass_label(summary_for(-1.2, -0.5), dead_zone_db=1.5)['key'], 'inconclusive')
        self.assertEqual(compass_label(summary_for(-1.2, -0.6), dead_zone_db=1.0)['key'], 'smoother_surface')

    def test_inconclusive_guards(self):
        self.assertEqual(compass_label(summary_for(-4, -2, n=20))['key'], 'inconclusive')
        wide = summary_for(-1.6, 0.1, spread=5)
        self.assertEqual(compass_label(wide)['key'], 'inconclusive')
        self.assertIn('disagree', compass_label(wide)['reason'])
        with self.assertRaises(ValueError):
            compass_label(summary_for(-3, -1), dead_zone_db=0)
        self.assertEqual(compass_label({'pixels': 0})['key'], 'inconclusive')

    def test_reference_subtraction_changes_reading(self):
        s = summary_for(-1.7, -0.9)
        self.assertEqual(compass_label(s)['key'], 'smoother_surface')
        self.assertEqual(compass_label(s, reference=(-1.39, -0.72))['key'], 'inconclusive')

    def test_every_label_has_rule_physics_and_caution_without_overclaiming(self):
        for key, info in LABELS.items():
            for field in ('title', 'rule', 'physics', 'caution'):
                self.assertTrue(info[field])
            text = (info['title'] + info['caution']).lower()
            self.assertNotIn('confirmed flood', text.replace('not confirmed', ''))
        self.assertIn('consistent with', LABELS['smoother_surface']['title'])

    def test_sector_shares_sum_to_one_and_rectangle_bounds(self):
        hh = np.array([[-3, 3, 0, 0, 0.1, -3.]]); hv = np.array([[-1, 0, -3, 3, 0.1, 2.]])
        shares = sector_shares(hh, hv, np.ones(hh.shape, bool), 1.5)
        self.assertAlmostEqual(sum(shares.values()), 1.0)
        self.assertAlmostEqual(shares['inside dead zone'], 1 / 6)
        self.assertAlmostEqual(shares['mixed directions'], 0)
        mask = rectangle_mask((10, 20), (0, .5), (.5, 1))
        self.assertEqual(int(mask.sum()), 5 * 10)
        with self.assertRaises(ValueError):
            rectangle_mask((10, 20), (.5, .5), (0, 1))

    def test_lag_correlation_detects_structure_not_noise(self):
        rng = np.random.default_rng(1)
        noise = rng.standard_normal((200, 200)); valid = np.ones_like(noise, bool)
        self.assertLess(abs(lag_correlation(noise, valid, 5)[0]), 0.05)
        smooth = np.repeat(np.repeat(rng.standard_normal((20, 20)), 10, 0), 10, 1)
        self.assertGreater(lag_correlation(smooth, valid, 5)[0], 0.3)
        with self.assertRaises(ValueError):
            lag_correlation(noise, valid, 0)


class ReferenceRobustnessTests(unittest.TestCase):
    def test_label_flips_under_reference_change_become_reference_dependent(self):
        s = summary_for(-1.7, -0.9)                      # raw: both darker, just outside the dead zone
        reading = compass_reading(s, scene=(-1.39, -0.72))
        self.assertEqual(reading['raw']['key'], 'smoother_surface')
        self.assertEqual(reading['relative']['key'], 'inconclusive')
        self.assertEqual(reading['key'], 'reference_dependent')
        self.assertFalse(reading['agree'])
        h, v = reading['numbers']['relative']
        self.assertAlmostEqual(h, s['HH']['median'] + 1.39); self.assertAlmostEqual(v, s['HV']['median'] + 0.72)

    def test_agreeing_references_keep_the_pattern(self):
        reading = compass_reading(summary_for(-4.4, -2.75), scene=(-1.39, -0.72))
        self.assertTrue(reading['agree']); self.assertEqual(reading['key'], 'smoother_surface')

    def test_hv_near_zero_has_no_sign_flip(self):
        keys = {compass_label(summary_for(-3.65, v))['key'] for v in (-0.05, 0.0, 0.05, 0.3, -0.3)}
        self.assertEqual(keys, {'hh_darkening'})
        self.assertEqual(compass_label(summary_for(-3.65, -1.0))['key'], 'smoother_surface')

    def test_real_candidate_example_raw_and_scene_relative(self):
        data = load_pair(); options = region_options()
        s = region_summary(data['HH_delta'], data['HV_delta'], options['Baseline class · New water candidate (possible expansion)'])
        scene = (float(np.median(data['HH_delta'][data['valid']])), float(np.median(data['HV_delta'][data['valid']])))
        reading = compass_reading(s, scene)
        raw_h, raw_v = reading['numbers']['raw']; rel_h, rel_v = reading['numbers']['relative']
        self.assertAlmostEqual(raw_h, -3.65, places=2); self.assertAlmostEqual(raw_v, -0.54, places=2)
        self.assertAlmostEqual(rel_h, -2.26, places=2); self.assertAlmostEqual(rel_v, +0.18, places=2)
        self.assertEqual(reading['raw']['key'], 'hh_darkening')
        self.assertEqual(reading['relative']['key'], 'hh_darkening')

    def test_every_pattern_lists_alternatives_including_scene_wide_shift(self):
        for key in LABELS:
            if key == 'inconclusive':
                continue
            alts = alternatives_for(key)
            self.assertTrue(any('scene-wide' in a for a in alts), key)
            self.assertTrue(any('moisture' in a.lower() for a in alts), key)
            self.assertTrue(any('roughness' in a.lower() for a in alts), key)
        for info in LABELS.values():
            for word in (' is water', 'confirmed', 'flooded vegetation detected'):
                self.assertNotIn(word, info['title'].lower())


class CompassDataTests(unittest.TestCase):
    def test_cached_outputs_verify_and_match_earlier_polarization_output(self):
        data = load_pair()
        report = data['report']
        self.assertEqual(report['pair'], ['2026-06-21', '2026-07-03'])
        self.assertFalse(report['network_access_used'])
        self.assertEqual(int(data['valid'].sum()), 138779)
        with rasterio.open(ROOT / 'data/polarization_analysis/two_date/before_after_delta_db.tif') as src:
            earlier = src.read()[:2]
        np.testing.assert_allclose(data['HH_delta'], earlier[0], atol=1e-5, equal_nan=True)
        np.testing.assert_allclose(data['HV_delta'], earlier[1], atol=1e-5, equal_nan=True)
        self.assertAlmostEqual(np.median(data['HH_delta'][data['valid']]), -1.3888, places=3)
        self.assertAlmostEqual(np.median(data['HV_delta'][data['valid']]), -0.7204, places=3)
        sidecar = json.loads((DIRECTORY / 'pair_change_db.json').read_text())
        self.assertEqual(sidecar['output_sha256']['pair_change_db.tif'], sha256(DIRECTORY / 'pair_change_db.tif'))
        for source in sidecar['sources']:
            self.assertIn('_L2_PR_GCOV_', source['product_id'])
            self.assertEqual(source['HV']['sha256'], sha256(ROOT / source['HV']['path']))

    def test_recomputation_from_raw_windows_is_reproducible(self):
        from scripts.detect_water_change import load_cached
        manifest = json.loads((ROOT / 'data/nisar_manifest.json').read_text())
        previous = json.loads((ROOT / 'data/nisar_visualization_report.json').read_text())
        items = sorted(manifest['observations'], key=lambda p: p['start_time_utc'])
        hh, hv = [], []
        for item in items:
            power, valid, _, _ = load_cached(item, previous)
            hh.append(np.where(valid, power, np.nan)); hv.append(read_raw_hv(item['start_time_utc'][:10])[0])
        pair = pair_change(np.stack(hh), np.stack(hv))
        cached = load_pair()
        np.testing.assert_allclose(pair['HV_delta'], cached['HV_delta'], atol=1e-5, equal_nan=True)

    def test_tampered_output_is_rejected(self):
        import shutil, tempfile
        with tempfile.TemporaryDirectory() as tmp:
            for f in DIRECTORY.iterdir():
                shutil.copy(f, tmp)
            report = json.loads((Path(tmp) / 'hv_signal_assessment.json').read_text())
            report['output_sha256']['pair_change_db.tif'] = '0' * 64
            (Path(tmp) / 'hv_signal_assessment.json').write_text(json.dumps(report))
            with self.assertRaises(ValueError):
                load_pair(tmp)

    def test_real_region_readings(self):
        data = load_pair(); options = region_options()
        new = region_summary(data['HH_delta'], data['HV_delta'], options['Baseline class · New water candidate (possible expansion)'],
                             hv_db=data['HV_db'])
        self.assertEqual(new['pixels'], 569)
        self.assertTrue(new['hv_dark_level']['flag'])
        scene = (np.median(data['HH_delta'][data['valid']]), np.median(data['HV_delta'][data['valid']]))
        reading = compass_reading(new, scene)
        self.assertEqual(reading['key'], 'hh_darkening')
        whole = region_summary(data['HH_delta'], data['HV_delta'], data['valid'])
        self.assertEqual(compass_label(whole)['key'], 'inconclusive')

    def test_page_renders_offline_with_evidence_and_caution(self):
        from streamlit.testing.v1 import AppTest
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Network disabled')):
            app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
            apptest_open(app,'Change Compass')
            self.assertFalse(app.exception)
            self.assertEqual([m.value for m in app.metric], ['569', '0.0569 km²', '-3.65 dB', '-0.54 dB'])
            self.assertTrue(any('NOT validated' in w.value for w in app.warning))
            self.assertTrue(any('noise floor' in w.value for w in app.warning))
            self.assertTrue(any('Other explanations' in m.value for m in app.markdown))
            app.selectbox(key='compass_region').select('Investigation region 1').run()
            self.assertTrue(any(m.value.startswith('#### Reading depends on the reference') for m in app.markdown))
            self.assertTrue(any('different readings' in m.value for m in app.markdown))
            app.selectbox(key='compass_region').select('Whole common AOI').run()
            self.assertTrue(any(m.value.startswith('#### No clear pattern') for m in app.markdown))
            app.radio(key='compass_mode').set_value('Rectangle').run()
            self.assertFalse(app.exception)
            apptest_open(app,'NISAR study')
            self.assertEqual(app.metric[0].value, '0.0569 km²')


if __name__ == '__main__':
    unittest.main()
