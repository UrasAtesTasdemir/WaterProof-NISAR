"""Researcher workflow: one candidate / pair / evidence list, and the review note."""
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

from src.workflow import (load_inputs, build_context, review_note, default_pair, load_robustness, CAUTION, UNKNOWN, NEUTRAL,
                          CONSISTENT, SCOPE_TEXT, PAIR, BASELINE)

ROOT = Path(__file__).resolve().parents[1]
INPUTS = None


def inputs():
    global INPUTS
    if INPUTS is None:
        INPUTS = load_inputs()
    return INPUTS


class WorkflowContextTests(unittest.TestCase):
    def test_live_ring_matches_saved_robustness_for_seed_pair(self):
        saved = json.loads((ROOT / 'data/robustness_v2/results.json').read_text())
        for region in inputs()['investigations']['regions']:
            first, second = default_pair(region)
            ctx = build_context(inputs(), region['id'], first, second)
            row = saved['ring_comparison'][str(region['id'])][first]
            self.assertAlmostEqual(ctx['ring']['candidate_dHH_db'], row['candidate_dHH_db'], places=6)
            self.assertAlmostEqual(ctx['ring']['ring_dHH_db'], row['ring_dHH_db'], places=6)

    def test_candidate_four_shows_its_weaknesses(self):
        region = inputs()['investigations']['regions'][3]
        ctx = build_context(inputs(), 4, *default_pair(region))
        self.assertEqual(ctx['reading']['key'], 'reference_dependent')
        topics = {e['topic']: e for e in ctx['evidence']}
        self.assertEqual(topics['Leave one date out']['status'], CAUTION)
        self.assertIn('2026-07-03', topics['Leave one date out']['text'])
        self.assertEqual(topics['Footprint edge']['status'], CAUTION)
        self.assertEqual(topics['Independent reference']['status'], UNKNOWN)
        self.assertTrue(any('single-date anomaly' in q for q in ctx['open_questions']))

    def test_hv_signal_level_is_never_positive(self):
        for region in inputs()['investigations']['regions']:
            for first, second in ((0, 1), (1, 2), *[default_pair(region)]):
                ctx = build_context(inputs(), region['id'], first, second)
                hv = next(e for e in ctx['evidence'] if e['topic'] == 'HV signal level')
                self.assertIn(hv['status'], (CAUTION, NEUTRAL))
                self.assertNotEqual(hv['status'], CONSISTENT)
                if hv['status'] == NEUTRAL:
                    self.assertIn('noise floor not quantified', hv['text'])
                self.assertIn('DN²', hv['text'])

    def test_saved_baseline_and_recomputed_pair_are_separated(self):
        region = inputs()['investigations']['regions'][0]
        a = build_context(inputs(), 1, *default_pair(region)); b = build_context(inputs(), 1, 3, 4)
        base = lambda c: [e for e in c['evidence'] if e['scope'] == BASELINE]
        self.assertEqual(base(a), base(b))   # saved baseline does not depend on the selected pair
        self.assertEqual({e['topic'] for e in base(a)}, {'Settings: area and ranking (a)', 'Settings: similarity (b)', 'Leave one date out'})
        note = review_note(b)
        i_pair, i_base = note.index('## ' + SCOPE_TEXT[PAIR]), note.index('## ' + SCOPE_TEXT[BASELINE])
        self.assertLess(note.index('Median ΔHH (raw)'), i_base)
        self.assertGreater(note.index('Leave one date out'), i_base)
        self.assertGreater(i_base, i_pair)
        for word in ('survive', 'passed'):
            self.assertNotIn(word, note.lower())

    def test_pair_across_gap_is_flagged_and_bad_pairs_rejected(self):
        ctx = build_context(inputs(), 1, 3, 4)
        self.assertEqual(ctx['interval_days'], 24)
        self.assertEqual(ctx['gaps'][0]['days'], 24)
        self.assertTrue(any('24-day acquisition gap' in q for q in ctx['open_questions']))
        for bad in ((2, 2), (4, 1), (0, 6)):
            with self.assertRaises(ValueError):
                build_context(inputs(), 1, *bad)
        with self.assertRaises(ValueError):
            build_context(inputs(), 9, 0, 1)

    def test_review_note_contains_only_context_numbers_and_no_claims(self):
        region = inputs()['investigations']['regions'][0]
        ctx = build_context(inputs(), 1, *default_pair(region))
        note = review_note(ctx)
        for text in (f"{ctx['summary']['HH']['median']:+.2f} dB", f"{ctx['ring']['candidate_minus_ring_dHH_db']:+.2f}",
                     '2026-07-03 → 2026-07-15', 'Open questions', 'Alternative explanations', '(a) Area and ranking',
                     '(b) Similarity', 'Leave one date out', ctx['product_ids'][0]):
            self.assertIn(text, note)
        lowered = note.lower()
        self.assertNotRegex(lowered, r'(?<!not )confirmed (flood|water)')
        self.assertNotRegex(lowered, r'\b(accuracy|validated) (of|is)\b')
        self.assertNotIn('is water', lowered)
        self.assertIn('not validated', lowered)
        for q in ctx['open_questions']:
            self.assertIn(q, note)

    def test_tampered_robustness_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for f in (ROOT / 'data/robustness_v2').iterdir():
                shutil.copy(f, tmp)
            (Path(tmp) / 'ring_comparison.csv').write_text('tampered\n')
            with self.assertRaises(ValueError):
                load_robustness(tmp)


class WorkflowPageTests(unittest.TestCase):
    def test_page_keeps_candidate_pair_and_note_in_sync(self):
        from streamlit.testing.v1 import AppTest
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Network disabled')):
            from src.navigation import apptest_open
            app = apptest_open(AppTest.from_file(str(ROOT / 'app.py'), default_timeout=90).run(), 'Researcher workflow')
            self.assertFalse(app.exception)
            self.assertEqual(app.selectbox(key='wf_candidate').value, 1)
            self.assertEqual(app.selectbox(key='wf_pair').value, (1, 2))   # candidate 1 seed: 3 Jul → 15 Jul
            app.selectbox(key='wf_candidate').select(4).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.selectbox(key='wf_pair').value, (1, 2))
            self.assertTrue(any(m.value.startswith('#### Reading depends on the reference') for m in app.markdown))
            app.selectbox(key='wf_candidate').select(3).run()
            self.assertEqual(app.selectbox(key='wf_pair').value, (0, 1))   # reset to candidate 3 seed
            app.selectbox(key='wf_pair').select((3, 4)).run()
            self.assertFalse(app.exception)
            self.assertTrue(any('24 days' in c.value for c in app.caption))
            notes = [m.value for m in app.markdown if m.value.startswith('# Review note')]
            self.assertTrue(notes and 'candidate 3' in notes[0] and '2026-07-27 → 2026-08-20' in notes[0])
            self.assertTrue(any('Statuses describe single checks' in c.value for c in app.caption))


if __name__ == '__main__':
    unittest.main()
