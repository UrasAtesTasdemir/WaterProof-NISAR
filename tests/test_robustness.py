"""Robustness checks: pure functions plus the saved data/robustness outputs."""
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
import unittest

import numpy as np

from src.robustness import (acquisition_gaps, iou, ring_mask, ring_comparison, leave_one_date_out, notable_on_footprint,
                            merged_seed_interval)
from src.time_axis import gaps_from_times, gap_caption

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/robustness_v2'
V1 = ROOT / 'data/robustness'
DATES = ['2026-06-21', '2026-07-03', '2026-07-15', '2026-07-27', '2026-08-20', '2026-09-01']


class PureFunctionTests(unittest.TestCase):
    def test_gap_detection_finds_the_24_day_gap(self):
        gaps = acquisition_gaps(DATES)
        self.assertEqual(gaps, [dict(start='2026-07-27', end='2026-08-20', days=24, missing_acquisitions=1)])
        times = [datetime.fromisoformat(d) for d in DATES]
        self.assertEqual(len(gaps_from_times(times)), 1)
        self.assertIn('24 days', gap_caption(times))

    def test_iou_and_ring_geometry(self):
        a = np.zeros((40, 40), bool); a[18:22, 18:22] = True
        self.assertEqual(iou(a, a), 1.0); self.assertEqual(iou(a, ~a), 0.0)
        ring = ring_mask(a, np.ones_like(a), inner=5, outer=15)
        self.assertFalse((ring & a).any())
        rr, cc = np.nonzero(ring)
        distance = np.hypot(np.clip(np.abs(rr - 19.5) - 1.5, 0, None), np.clip(np.abs(cc - 19.5) - 1.5, 0, None))
        self.assertTrue((distance > 4).all())
        excluded = np.zeros_like(a); excluded[:, :10] = True
        self.assertFalse((ring_mask(a, np.ones_like(a), exclude=excluded) & excluded).any())

    def test_ring_comparison_keeps_raw_values(self):
        hh = np.zeros((2, 30, 30)); hh[1] = -1.0; fp = np.zeros((30, 30), bool); fp[14:16, 14:16] = True
        hh[1][fp] = -5.0
        ring = ring_mask(fp, np.ones((30, 30), bool))
        row = ring_comparison(hh, hh.copy(), fp, ring, DATES[:2])[0]
        self.assertEqual(row['candidate_dHH_db'], -5.0); self.assertEqual(row['ring_dHH_db'], -1.0)
        self.assertEqual(row['candidate_minus_ring_dHH_db'], -4.0)

    def test_leave_one_date_out_on_a_synthetic_step(self):
        rng = np.random.default_rng(3)
        hh = rng.normal(-10, .3, (6, 60, 60)); hv = hh - 7
        fp = np.zeros((60, 60), bool); fp[20:30, 20:30] = True
        hh[3:, fp] += 6.0                        # step between date 2 and date 3, sustained afterwards
        rows = leave_one_date_out(hh, hv, np.ones((60, 60), bool), DATES, fp, 'increase', 2)
        still = {r['removed_date']: r['seed_event_still_notable'] for r in rows}
        self.assertTrue(all(still.values()))   # a sustained step stays notable in its merged interval after any removal
        self.assertTrue(all(r['best_iou_any_proposal'] > .5 for r in rows))
        self.assertEqual(rows[2]['seed_event_interval'], '2026-07-03 → 2026-07-27')   # removing the seed start merges backwards
        hh2 = rng.normal(-10, .3, (6, 60, 60)); hh2[3, fp] += 6.0   # one-date spike only
        rows2 = {r['removed_date']: r for r in leave_one_date_out(hh2, hh2 - 7, np.ones((60, 60), bool), DATES, fp, 'increase', 2)}
        self.assertFalse(rows2['2026-07-27']['seed_event_still_notable'])

    def test_merged_seed_interval(self):
        self.assertEqual(merged_seed_interval(6, 1, 0), (1, 2))      # unrelated date
        self.assertEqual(merged_seed_interval(6, 1, 1), (0, 2))      # seed start removed: merge with the earlier interval
        self.assertEqual(merged_seed_interval(6, 1, 2), (1, 3))      # seed end removed: merge with the later interval
        self.assertIsNone(merged_seed_interval(6, 0, 0))             # nothing before the seed start
        self.assertIsNone(merged_seed_interval(6, 4, 5))             # nothing after the seed end
        with self.assertRaises(ValueError):
            merged_seed_interval(6, 5, 0)

    def test_unrelated_same_direction_change_does_not_count(self):
        """Seed event 03 Jul → 15 Jul is a one-date spike on 15 Jul; an unrelated, sustained same-direction step happens
        27 Jul → 20 Aug. Removing 15 Jul must report the seed event as not notable even though the other interval is."""
        rng = np.random.default_rng(7)
        hh = rng.normal(-10, .3, (6, 60, 60)); fp = np.zeros((60, 60), bool); fp[20:30, 20:30] = True
        hh[2, fp] += 6.0                                  # spike on 15 Jul only (seed interval 1, increase)
        hh[4:, fp] += 6.0                                 # unrelated sustained increase from 20 Aug
        rows = {r['removed_date']: r for r in leave_one_date_out(hh, hh - 7, np.ones((60, 60), bool), DATES, fp, 'increase', 1)}
        dropped = rows['2026-07-15']
        self.assertEqual(dropped['seed_event_interval'], '2026-07-03 → 2026-07-27')
        self.assertFalse(dropped['seed_event_still_notable'])
        self.assertIn('2026-07-27 → 2026-08-20', dropped['other_same_direction_notable_intervals'])
        self.assertTrue(rows['2026-06-21']['seed_event_still_notable'])

    def test_edge_removal_is_not_testable(self):
        rng = np.random.default_rng(11)
        hh = rng.normal(-10, .3, (6, 60, 60)); fp = np.zeros((60, 60), bool); fp[20:30, 20:30] = True
        hh[1:, fp] -= 6.0                                 # seed interval 0, decrease, sustained
        rows = {r['removed_date']: r for r in leave_one_date_out(hh, hh - 7, np.ones((60, 60), bool), DATES, fp, 'decrease', 0)}
        self.assertIsNone(rows['2026-06-21']['seed_event_still_notable'])
        self.assertIsNone(rows['2026-06-21']['seed_event_interval'])
        self.assertIn('not testable', rows['2026-06-21']['seed_event_status'])
        self.assertTrue(rows['2026-07-03']['seed_event_still_notable'])   # merged 21 Jun → 15 Jul still carries it


class SavedRobustnessTests(unittest.TestCase):
    def setUp(self):
        self.report = json.loads((OUT / 'results.json').read_text())

    def test_outputs_and_sources_verify(self):
        sidecar = json.loads((OUT / 'sidecar.json').read_text())
        for name, digest in sidecar['outputs_sha256'].items():
            self.assertEqual(hashlib.sha256((OUT / name).read_bytes()).hexdigest(), digest, name)
        for name, digest in sidecar['sources_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest, name)
        self.assertFalse(self.report['network_access_used'])

    def test_default_variant_reproduces_saved_regions(self):
        self.assertEqual(self.report['default_variant_reproduces_saved_regions']['best_iou_per_candidate'], [1.0] * 5)
        rows = list(csv.DictReader((OUT / 'settings_sensitivity.csv').open()))
        self.assertEqual(len(rows), 27 * 5)
        defaults = [r for r in rows if r['is_default'] == 'True']
        self.assertEqual([int(r['top5_rank']) for r in defaults], [1, 2, 3, 4, 5])

    def test_summary_matches_tables_and_keeps_two_measures_separate(self):
        rows = list(csv.DictReader((OUT / 'settings_sensitivity.csv').open()))
        for s in self.report['summary']:
            mine = [r for r in rows if int(r['candidate']) == s['candidate']]
            self.assertEqual(s['variants_in_top5'], sum(r['top5_rank'] != '' for r in mine))
            self.assertEqual(s['variants_same_seed'], sum(r['same_seed_interval_and_direction'] == 'True' for r in mine))
            for key in ('variants_in_top5', 'variants_same_seed', 'iou_top5_range', 'screened_pixels_range'):
                self.assertIn(key, s)
            self.assertNotIn('score', ' '.join(s))
        first = self.report['summary'][0]
        self.assertEqual((first['variants_in_top5'], first['lodo_removals_still_notable']), (27, 5))
        self.assertEqual(first['lodo_dates_not_notable'], ['2026-07-15'])
        for s in self.report['summary']:
            self.assertEqual(s['lodo_removals_still_notable'] + len(s['lodo_dates_not_notable']) + len(s['lodo_dates_not_testable']), 6)

    def test_lodo_rows_follow_the_seed_event_interval(self):
        for cid, rows in self.report['leave_one_date_out'].items():
            seed = next(s for s in self.report['summary'] if s['candidate'] == int(cid))['seed']
            start, end = seed.split(' (')[0].split(' → ')
            for r in rows:
                if r['seed_event_interval'] is None:
                    self.assertIn(r['removed_date'], (self.report['dates'][0], self.report['dates'][-1]))
                    continue
                a, b = r['seed_event_interval'].split(' → ')
                self.assertTrue(a <= start and end <= b, (cid, r['removed_date']))
                self.assertNotIn(r['seed_event_interval'], r['other_same_direction_notable_intervals'])

    def test_version_one_is_kept_unchanged_and_superseded(self):
        self.assertEqual(self.report['version'], 2)
        sidecar = json.loads((V1 / 'sidecar.json').read_text())
        for name, digest in sidecar['outputs_sha256'].items():
            self.assertEqual(hashlib.sha256((V1 / name).read_bytes()).hexdigest(), digest, name)
        old = json.loads((V1 / 'results.json').read_text())
        self.assertEqual(old['summary'][0]['lodo_dates_where_change_survives'], 6)   # the overstated v1 value stays on record

    def test_ring_rows_are_raw_differences(self):
        for rows in self.report['ring_comparison'].values():
            for r in rows:
                self.assertAlmostEqual(r['candidate_minus_ring_dHH_db'], r['candidate_dHH_db'] - r['ring_dHH_db'], places=9)
                self.assertGreater(r['ring_pixels'], 100)

    def test_gap_reported(self):
        self.assertEqual(self.report['acquisition_gaps'][0]['days'], 24)


if __name__ == '__main__':
    unittest.main()
