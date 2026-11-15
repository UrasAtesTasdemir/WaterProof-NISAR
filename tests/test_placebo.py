"""Placebo (null) check: placement rules, minimum placements, reproducibility, formula, UI and review note.

Small synthetic grids below are test fixtures only; the app shows only data/placebo computed from real data.
"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from src import placebo
from src.placebo import (exceedance_fraction, null_placements, placebo_for_candidate, shape_offsets, load_results,
                         note_line, for_candidate)

ROOT = Path(__file__).resolve().parents[1]
NO_NET = dict(target='requests.sessions.Session.request', side_effect=AssertionError('Network disabled'))


def _grid(shape=(80, 120), seed=1):
    rng = np.random.default_rng(seed)
    hh = rng.normal(-15, 1, (3,) + shape); hv = rng.normal(-22, 1, (3,) + shape)
    common = np.ones(shape, bool); common[:, :6] = False                       # an invalid strip
    labels = np.zeros(shape, np.int32)
    labels[30:34, 40:46] = 1; labels[34, 40:43] = 1                            # irregular footprint (27 px)
    labels[60:63, 90:95] = 2
    hh[1:, labels == 1] += 4                                                   # candidate 1 brightens in interval 0
    return hh, hv, common, labels


class PlacementTests(unittest.TestCase):
    def test_shape_preserved_valid_no_overlap_ring_and_spacing(self):
        hh, hv, common, labels = _grid()
        footprint = labels == 1; candidates = labels > 0
        rows, cols, _ = shape_offsets(footprint)
        kept = list(null_placements(footprint, common, candidates, seed=7, draws=400))
        self.assertGreater(len(kept), 20)
        for top, left, mask, ring in kept:
            r, c, _ = shape_offsets(mask)
            self.assertTrue(np.array_equal(np.sort(r * 1000 + c), np.sort(rows * 1000 + cols)))   # same shape
            self.assertEqual(int(mask.sum()), int(footprint.sum()))
            self.assertTrue(common[mask].all())
            self.assertFalse(candidates[mask].any())
            self.assertFalse((ring & candidates).any())
            self.assertGreaterEqual(int(ring.sum()), placebo.MIN_RING_PIXELS)
        positions = np.array([(k[0], k[1]) for k in kept])
        d = np.sqrt(((positions[:, None] - positions[None]) ** 2).sum(-1)) + np.eye(len(positions)) * 1e9
        self.assertGreaterEqual(d.min(), placebo.MIN_SPACING_PX)

    def test_minimum_placements_rule_reports_no_number(self):
        hh, hv, common, labels = _grid()
        small = np.zeros_like(common); small[25:45, 35:55] = True                 # almost no room
        result = placebo_for_candidate(hh, hv, small, labels, 1, 0, ['a', 'b', 'c'], [1, 2], draws=300)
        self.assertEqual(result['status'], 'not enough valid placements')
        self.assertLess(result['placements'], placebo.MIN_PLACEMENTS)
        for band in ('HH', 'HV'):
            self.assertNotIn('exceedance_fraction', result[band]); self.assertNotIn('null_median_db', result[band])
        self.assertIn('not enough valid placements', note_line(result))

    def test_reproducible_with_fixed_seed(self):
        hh, hv, common, labels = _grid()
        a = placebo_for_candidate(hh, hv, common, labels, 1, 0, ['a', 'b', 'c'], [1, 2], draws=600, min_placements=10)
        b = placebo_for_candidate(hh, hv, common, labels, 1, 0, ['a', 'b', 'c'], [1, 2], draws=600, min_placements=10)
        self.assertEqual(json.dumps(a), json.dumps(b))
        self.assertEqual(a['seed'], placebo.BASE_SEED + 1)
        c = placebo_for_candidate(hh, hv, common, labels, 1, 0, ['a', 'b', 'c'], [1, 2], draws=600, min_placements=10, seed=5)
        self.assertNotEqual(a['positions'], c['positions'])

    def test_exceedance_formula(self):
        self.assertAlmostEqual(exceedance_fraction([0.1, -0.5, 2.0, -3.0], 1.0), (2 + 1) / (4 + 1))
        self.assertAlmostEqual(exceedance_fraction([0.1, 0.2], -5.0), 1 / 3)            # none as extreme -> 1/(n+1), never 0
        self.assertAlmostEqual(exceedance_fraction([1.0, -1.0], 1.0), 1.0)              # ties count, absolute values


class SavedOutputTests(unittest.TestCase):
    def test_saved_outputs_verified_and_reproducible(self):
        saved = load_results()
        self.assertIsNotNone(saved, 'data/placebo missing or changed')
        self.assertEqual([c['candidate'] for c in saved['candidates']], [1, 2, 3, 4, 5])  # all five reported
        self.assertIsNone(saved['multiple_comparison_correction'])
        self.assertTrue(all(c['matches_saved_ring_comparison'] for c in saved['candidates']))
        from scripts.process_placebo import compute
        _, rows = compute()
        self.assertEqual(json.dumps(rows), json.dumps(saved['candidates']))           # bit-for-bit with the fixed seed

    def test_missing_outputs_show_not_available(self):
        with tempfile.TemporaryDirectory() as empty:
            self.assertIsNone(load_results(empty))
        self.assertIsNone(for_candidate(None, 1))
        self.assertIn('not available', note_line(None)); self.assertIn('kullanılamıyor', note_line(None, 'tr'))

    def test_wording_is_descriptive(self):
        from src.locales import placebo as strings
        from src.i18n import PLACEHOLDER
        self.assertEqual(set(strings.EN), set(strings.TR))
        for key in strings.EN:
            self.assertEqual(set(PLACEHOLDER.findall(strings.EN[key])), set(PLACEHOLDER.findall(strings.TR[key])), key)
        text = ' '.join(strings.EN.values()).lower()
        self.assertNotIn('p-value', text); self.assertNotIn('statistically significant', text)
        self.assertIn('not a significance test', text); self.assertIn('selected because they changed a lot', text)


class PlaceboUITests(unittest.TestCase):
    def _workflow(self):
        from streamlit.testing.v1 import AppTest
        from src.navigation import apptest_open
        return apptest_open(AppTest.from_file(str(ROOT / 'app.py'), default_timeout=120).run(), 'Researcher workflow')

    def test_expander_and_review_note_line(self):
        with patch(**NO_NET):
            app = self._workflow()
            self.assertFalse(app.exception)
            exp = next(e for e in app.expander if e.label == 'Placebo check')
            texts = ' '.join(m.value for m in exp.markdown) + ' '.join(c.value for c in exp.caption)
            self.assertIn('It does not tell us why', texts)
            self.assertIn('exceedance fraction', texts); self.assertIn('Not a significance test', texts)
            note = next(m.value for m in app.markdown if m.value.startswith('# Review note'))
            self.assertIn('- Placebo check (seed interval 2026-07-03 → 2026-07-15', note)
            app.button(key='lang_tr').click().run()
            self.assertFalse(app.exception)
            note = next(m.value for m in app.markdown if m.value.startswith('# İnceleme notu'))
            self.assertIn('- Plasebo kontrolü (tohum aralığı', note); self.assertRegex(note, r'aşım oranı HH 0,\d{4}')

    def test_missing_outputs_do_not_break_the_page(self):
        with patch(**NO_NET), patch('src.placebo.cached_results', return_value=None):
            app = self._workflow()
            self.assertFalse(app.exception)
            exp = next(e for e in app.expander if e.label == 'Placebo check')
            self.assertTrue(any('Placebo check not available' in i.value for i in exp.info))
            note = next(m.value for m in app.markdown if m.value.startswith('# Review note'))
            self.assertIn('- Placebo check: not available', note)


if __name__ == '__main__':
    unittest.main()
