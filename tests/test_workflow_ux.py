"""Presentation integration using real cached candidates; no new scientific pipeline."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from rasterio.warp import transform_geom
from shapely.geometry import shape, Point

from src.workflow import load_inputs, build_context, default_pair, review_note, investigation_action, robustness_summary
from src.workflow_map import waterway_context, workflow_map, context_sentence

ROOT = Path(__file__).resolve().parents[1]


class WorkflowUXTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = load_inputs()

    def test_candidate_actions_and_exports_follow_selected_pair_both_languages(self):
        for r in self.inputs['investigations']['regions']:
            for lang in ('en', 'tr'):
                for pair in (default_pair(r), (3, 4)):
                    ctx = build_context(self.inputs, r['id'], *pair, lang=lang)
                    question, action = investigation_action(ctx)
                    note = review_note(ctx)
                    for text in (question, action, *robustness_summary(ctx)):
                        self.assertIn(text, note)
                    for date in (ctx['dates'][pair[0]], ctx['dates'][pair[1]]):
                        self.assertIn(date, question); self.assertIn(date, action)
                    self.assertIn(f"{r['representative_longitude']:.5f}", action)
                    self.assertIn('unverified' if lang == 'en' else 'teyit edilmedi', action)

    def test_summary_preserves_actual_robustness_and_temporary_event_caveat(self):
        ctx = build_context(self.inputs, 1, 1, 2)
        lines = robustness_summary(ctx)
        self.assertIn('27/27', lines[0]); self.assertIn('5/6', lines[1])
        self.assertIn('2026-07-15', lines[1]); self.assertIn('temporary event', lines[2])
        self.assertIn('insufficient', lines[3])
        other = robustness_summary(build_context(self.inputs, 3, 0, 1))
        self.assertIn('Sensitive', other[0]); self.assertIn('3/27', other[0])

    def test_geographic_context_distance_is_projected_and_missing_is_not_absence(self):
        report = self.inputs['investigations']; ctx = build_context(self.inputs, 1, 1, 2)
        water = waterway_context(ctx['candidate'], report['common_footprint'], ctx['grid']['crs'])
        self.assertTrue(water['available']); self.assertGreaterEqual(water['distance_m'], 0)
        self.assertIn('Historical', context_sentence(water, 'en'))
        for f in water['features']['features']:
            self.assertTrue(shape(report['common_footprint']).buffer(1e-10).covers(shape(f['geometry'])))
        with tempfile.TemporaryDirectory() as tmp:
            missing = waterway_context(ctx['candidate'], report['common_footprint'], ctx['grid']['crs'], Path(tmp)/'missing')
            self.assertIsNone(missing['distance_m'])
            self.assertIn('no claim', context_sentence(missing, 'en'))
        # Independent metric-space check using a real candidate and a synthetic reference only in this unit test.
        from shapely.geometry import mapping, LineString
        projected = shape(transform_geom('EPSG:4326', ctx['grid']['crs'], ctx['candidate']['geometry']))
        x0,y0,x1,y1 = projected.bounds
        line = LineString([(x1+100,y0-100),(x1+100,y1+100)])
        geom = transform_geom(ctx['grid']['crs'], 'EPSG:4326', mapping(line))
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'sample.json'
            p.write_text(json.dumps({'features':[dict(geometry=geom,properties={'ftype':460})]}))
            actual = waterway_context(ctx['candidate'], report['common_footprint'], ctx['grid']['crs'],p)
            self.assertAlmostEqual(actual['distance_m'],100,places=4)

    def test_map_uses_real_geometry_dates_bounds_and_nodata(self):
        from src.time_series_map import continuous_display
        report = self.inputs['investigations']
        for ident, pair in ((1,(1,2)), (3,(0,1))):
            ctx = build_context(self.inputs,ident,*pair)
            water = waterway_context(ctx['candidate'],report['common_footprint'],ctx['grid']['crs'])
            text = workflow_map(report,ctx,water)
            for date in (ctx['dates'][pair[0]], ctx['dates'][pair[1]]):
                self.assertIn(date,text)
            self.assertIn('openstreetmap',text); self.assertIn('L.imageOverlay',text)
            self.assertIn('L.control.layers',text); self.assertIn('USGS NHD',text)
            point = Point(ctx['candidate']['representative_longitude'],ctx['candidate']['representative_latitude'])
            self.assertTrue(shape(ctx['candidate']['geometry']).covers(point))
            values = np.where(ctx['pair_valid'],ctx['HH_delta'],np.nan)
            rgba,bounds = continuous_display(values,ctx['grid'],-6,6,'RdBu_r')
            self.assertTrue((rgba[...,3]==0).any())
            self.assertLess(bounds[0][0],point.y); self.assertGreater(bounds[1][0],point.y)
            self.assertLess(bounds[0][1],point.x); self.assertGreater(bounds[1][1],point.x)

    def test_advanced_tau_remains_effective_and_shell_help_is_removed_only_here(self):
        from streamlit.testing.v1 import AppTest
        from src.navigation import apptest_open
        app = apptest_open(AppTest.from_file(str(ROOT/'app.py'), default_timeout=90).run(), 'Researcher workflow')
        self.assertFalse(app.exception)
        self.assertTrue(any('Advanced settings' in e.label for e in app.expander))
        for key in ('lang_en','lang_tr','theme_toggle'):
            self.assertFalse(app.button(key=key).proto.help)
        app.number_input(key='wf_dead_zone').set_value(4.).run()
        self.assertFalse(app.exception)
        self.assertTrue(any('τ = 4 dB' in m.value for m in app.markdown))
        app.selectbox(key='wf_candidate').select(3).run()
        self.assertEqual(app.selectbox(key='wf_pair').value,(0,1))
        self.assertTrue(any('candidate 3' in m.value for m in app.markdown))


if __name__ == '__main__':
    unittest.main()
