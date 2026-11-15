"""Flood map layer on Explore, catalog-aware time wording, and the Flood validation page (no network)."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NO_NET = dict(target='requests.sessions.Session.request', side_effect=AssertionError('Network disabled'))


def _app():
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(ROOT / 'app.py'), default_timeout=180).run()


class FloodLayerTests(unittest.TestCase):
    def test_layer_is_the_primary_rule(self):
        from src import flood_layer, flood_validation as fv
        from src.water_change import classify
        rng = np.random.default_rng(2)
        hh = 10 ** (rng.uniform(-25, -5, (3, 40, 40)) / 10); hv = 10 ** (rng.uniform(-30, -10, (3, 40, 40)) / 10)
        cube = dict(hh_power=hh, hv_power=hv, crs='EPSG:32647', transform=[10, 0, 0, 0, -10, 0])
        r = flood_layer.compute(cube, 0, 2)
        prep = fv.preprocess(dict(hh_power=hh[[0, 2]], hv_power=hv[[0, 2]]))
        expected, _ = classify(prep['HH'][0], prep['HH'][1], prep['valid'], -16.0, 3.0)
        self.assertTrue(np.array_equal(r['classes'], expected))
        self.assertAlmostEqual(r['new_area_km2'], r['new_pixels'] * 1e-4)

    def test_validation_numbers_are_read_from_saved_outputs(self):
        from src.flood_layer import validation_numbers
        v = validation_numbers()
        self.assertEqual([round(x, 2) for x in v['thailand']], [0.78, 0.74, 0.81])
        self.assertEqual([round(x, 2) for x in v['gandak']], [0.24, 0.17, 0.31])


class TimeWordingTests(unittest.TestCase):
    def _ctx(self, catalog):
        from src.explore import louisiana_cube, analyze
        cube = louisiana_cube()
        cube = dict(cube, lat=29.910969, lon=-90.264745, catalog_dates=catalog)
        return analyze(cube, 3, 4, lang='en')                      # 2026-07-27 -> 2026-08-20 (24 days)

    def _time(self, ctx):
        return next(e['text'] for e in ctx['evidence'] if e['id'] == 'time')

    def test_real_gap_only_when_the_catalog_has_nothing_in_between(self):
        from src.explore import louisiana_cube
        inventory = louisiana_cube()['catalog_dates']
        self.assertEqual(len(inventory), 6)
        self.assertIn('spans the 24-day acquisition gap', self._time(self._ctx(inventory)))

    def test_intermediate_catalog_acquisition_is_reported_as_not_loaded(self):
        from src.explore import louisiana_cube
        ctx = self._ctx(louisiana_cube()['catalog_dates'] + ['2026-08-08'])
        text = self._time(ctx)
        self.assertNotIn('acquisition gap', text)
        self.assertIn('2026-08-08', text); self.assertIn('not loaded', text)
        self.assertEqual(ctx['pair_gaps'], [])
        self.assertTrue(any('2026-08-08' in q for q in ctx['open_questions']))

    def test_unknown_catalog_is_not_called_a_gap(self):
        text = self._time(self._ctx(None))
        self.assertNotIn('spans the', text); self.assertIn('catalog was not checked', text)


class FloodAppTests(unittest.TestCase):
    def test_explore_shows_candidate_map_with_scope_not_transferred_scores(self):
        with patch(**NO_NET), patch('src.explore_panel.search_catalog', side_effect=AssertionError('no catalog')):
            app = _app()
            self.assertFalse(app.exception)
            text = ' '.join(m.value for m in app.markdown)
            self.assertIn('Candidate open-water change — evaluated threshold method', text)
            self.assertIn('Candidate new open water in this window:', text)
            self.assertIn('Compass reading', text)                 # existing Compass result still shown
            self.assertNotIn('validated rule', text)
            captions = ' '.join(c.value for c in app.caption)
            self.assertIn('Case-specific evaluation', captions)    # Thailand 004 D 6 -> 30 Sep is a saved comparison
            self.assertIn('matches the saved Thailand 004 D', captions)
            self.assertTrue(any('Thailand control:' in w.value for w in app.warning))
            self.assertNotIn('F1 0.78', text); self.assertNotIn('F1 0.24', text)   # other scenes' scores never shown here
            app.button(key='lang_tr').click().run()
            self.assertFalse(app.exception)
            self.assertIn('Açık su değişimi adayları — değerlendirilmiş eşik yöntemi', ' '.join(m.value for m in app.markdown))

    def test_flood_validation_page_both_languages_and_themes(self):
        from src.navigation import apptest_open
        with patch(**NO_NET):
            app = apptest_open(_app(), 'Flood validation (Thailand, Gandak)')
            self.assertFalse(app.exception)
            self.assertEqual(app.title[0].value, 'Reference comparisons (Thailand, Gandak)')
            self.assertEqual(app.subheader[0].value, 'Where the Method Works — and Where It Struggles')
            text = ' '.join(m.value for m in app.markdown)
            for phrase in ('181782456a', 'not accuracy against ground truth', 'Co-registration', 'not run (time)', 'HV adds',
                           'F1 0.78 [0.74, 0.81]', 'F1 0.24 [0.17, 0.31]', 'Δt +48.2 h / +24.4 h', 'Δt -71.5 h / -71.5 h'):
                self.assertIn(phrase, text)
            captions = ' '.join(c.value for c in app.caption)
            self.assertIn('not two independent successes', captions); self.assertIn('Low agreement', captions)
            self.assertEqual(len(app.table[0].value), 8)
            app.button(key='theme_toggle').click().run(); self.assertFalse(app.exception)
            app.button(key='lang_tr').click().run(); self.assertFalse(app.exception)
            self.assertEqual(app.title[0].value, 'Referans karşılaştırmaları (Tayland, Gandak)')

    def test_typing_coordinates_switches_preset_to_custom(self):
        with patch(**NO_NET), patch('src.explore_panel.search_catalog', side_effect=AssertionError('no catalog')):
            app = _app()
            self.assertEqual(app.session_state['ex_preset'], 'thailand_prachinburi')
            app.number_input(key='ex_lat').set_value(14.2).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['ex_preset'], 'custom')
            self.assertEqual(app.selectbox(key='ex_preset').value, 'custom')

    def test_agreement_colours_are_colourblind_safe_and_legends_are_html(self):
        from src.flood_layer import AGREEMENT_COLORS
        self.assertEqual(AGREEMENT_COLORS, {1: '#0072B2', 2: '#E69F00', 3: '#CC79A7'})     # Okabe-Ito
        from src.navigation import apptest_open
        with patch(**NO_NET):
            app = apptest_open(_app(), 'Flood validation (Thailand, Gandak)')
            html = ' '.join(m.value for m in app.markdown)
            for label in ('TP: both new water', 'FP: NISAR only', 'FN: DSWx-S1 only', 'new open water'):
                self.assertIn(label, html)
            self.assertIn('#E69F00', html); self.assertIn('#CC79A7', html)
            self.assertTrue(any('UTM zone 44N' in c.value for c in app.caption))
            app.button(key='lang_tr').click().run()
            self.assertFalse(app.exception)
            self.assertIn('%3,1', ' '.join(m.value for m in app.markdown))          # Turkish percent order

    def test_strings_parity_and_wording(self):
        from src.locales import flood
        from src.i18n import PLACEHOLDER
        self.assertEqual(set(flood.EN), set(flood.TR))
        for k in flood.EN:
            self.assertEqual(set(PLACEHOLDER.findall(flood.EN[k])), set(PLACEHOLDER.findall(flood.TR[k])), k)
        text = ' '.join(flood.EN.values()).lower()
        for bad in ('accuracy of', 'accurate', 'proves', 'proven', 'ground truth shows'):
            self.assertNotIn(bad, text)
