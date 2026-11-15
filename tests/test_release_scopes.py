"""Final-release checks: evidence scopes, metric provenance, negative-control visibility, terminology, exports, attribution.

All numbers are compared with the saved outputs in data/flood_validation/ (never typed in as the source of truth).
"""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NO_NET = dict(target='requests.sessions.Session.request', side_effect=AssertionError('Network disabled'))
FV = ROOT / 'data/flood_validation'


def _app():
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(ROOT / 'app.py'), default_timeout=180).run()


def _thailand_cube():
    from src import demo_places
    place = next(p for p in demo_places.places() if p['key'] == 'thailand_prachinburi')
    with patch(**NO_NET), patch('src.nisar_data.open_frequency_a', side_effect=AssertionError('no read')):
        return demo_places.demo_cube(place)


class ScopeTests(unittest.TestCase):
    def test_scope_for_each_kind_of_selection(self):
        from src.evidence_scope import scope_for, matched_case, is_control, LOUISIANA, CASE, LIVE
        from src.explore import louisiana_cube
        self.assertEqual(scope_for(louisiana_cube(), (0, 5)), LOUISIANA)
        cube = _thailand_cube()                                   # dates 09-06, 09-18, 09-30 on the saved 004 D grid
        self.assertEqual((scope_for(cube, (0, 2)), matched_case(cube, (0, 2))), (CASE, 'a'))
        self.assertTrue(is_control(cube, (0, 1))); self.assertEqual(scope_for(cube, (0, 1)), CASE)
        self.assertEqual(scope_for(cube, (1, 2)), LIVE)           # never evaluated: stays exploratory

    def test_live_selection_stays_exploratory_and_fails_closed(self):
        from src.evidence_scope import scope_for, matched_case, LIVE
        cube = _thailand_cube()
        shifted = dict(cube, transform=list(cube['transform'][:2]) + [cube['transform'][2] + 10] + list(cube['transform'][3:6]))
        self.assertIsNone(matched_case(shifted, (0, 2)))           # same products, different grid: not the evaluated case
        self.assertEqual(scope_for(shifted, (0, 2)), LIVE)
        self.assertEqual(scope_for(dict(dates=['a', 'b']), (0, 1)), LIVE)   # missing metadata never upgrades the scope
        rng = np.random.default_rng(0)
        other = dict(source='live', dates=['2026-06-01', '2026-06-13'], product_ids=['x', 'y'], crs='EPSG:32647',
                     transform=[10, 0, 0, 0, -10, 0], hh_power=rng.random((2, 5, 5)), hv_power=rng.random((2, 5, 5)))
        self.assertEqual(scope_for(other, (0, 1)), LIVE)

    def test_scope_texts_distinguish_the_three_scopes_in_both_languages(self):
        from src.i18n import t
        en = {k: t('scope.' + k, lang='en') for k in ('louisiana', 'case', 'live')}
        tr = {k: t('scope.' + k, lang='tr') for k in ('louisiana', 'case', 'live')}
        self.assertIn('no independent validation', en['louisiana'])
        self.assertIn('independent water-product comparison', en['case']); self.assertIn('not to', en['case'])
        self.assertIn('Thailand/Gandak scores do not apply here', en['live'])
        self.assertIn('Tayland/Gandak puanları burada geçerli değildir', tr['live'])
        self.assertEqual(len(set(en.values())), 3); self.assertEqual(len(set(tr.values())), 3)


class ProvenanceTests(unittest.TestCase):
    def test_primary_rows_match_saved_metrics_with_dates_and_offsets(self):
        from src.evaluation_provenance import primary_evaluations
        rows = primary_evaluations()
        self.assertEqual(len(rows), 8)
        boot = json.loads((FV / 'bootstrap_ab/results.json').read_text())
        c = json.loads((FV / 'step2c/metrics.json').read_text())
        for r in rows:
            if r['stage'] in ('a', 'b'):
                saved = boot['results'][r['stage']]['primary_rows'][r['outcome'] + ' | ' + r['reference_type'] + ' ' +
                        ('primary' if r['reference_type'] == 'S1' else 'sensitivity')]['point']
            else:
                saved = next(x for x in c['rows'] if x['threshold_set'].startswith('PRIMARY') and x['variant'] == 'HH'
                             and x['outcome'] == r['outcome'])
            self.assertEqual(r['metrics']['F1'], saved['F1'])
            for ref in r['references']:
                self.assertIsNotNone(ref['acquired_utc'])          # acquisition time, never missing for primary rows
        new_b = next(r for r in rows if r['stage'] == 'b' and r['outcome'].startswith('new'))
        self.assertEqual([x['acquired_utc'][:19] for x in new_b['references']], ['2026-09-08T23:00:13', '2026-10-01T23:08:39'])
        self.assertEqual([round(x['offset_hours'], 1) for x in new_b['references']], [48.2, 24.4])
        new_c = next(r for r in rows if r['stage'] == 'c' and r['outcome'].startswith('new'))
        self.assertEqual([round(x['offset_hours'], 1) for x in new_c['references']], [-71.5, -71.5])
        self.assertEqual(round(new_b['metrics']['F1'], 2), 0.78); self.assertEqual(round(new_c['metrics']['F1'], 2), 0.24)

    def test_negative_control_numbers_are_the_saved_ones(self):
        from src.evaluation_provenance import negative_controls
        d = json.loads((FV / 'step2d/metrics.json').read_text())['tracks']
        for row in negative_controls():
            self.assertEqual(row['candidate_area_km2'], d[row['track']]['tier_A']['new_water_km2_before_before'])
            self.assertEqual(row['disagreement_area_km2'], d[row['track']]['tier_B']['false_new_water_km2'])
            self.assertTrue(row['coregistration']['passed'])


class AppTests(unittest.TestCase):
    def test_negative_control_warning_only_for_thailand(self):
        with patch(**NO_NET), patch('src.explore_panel.search_catalog', side_effect=AssertionError('no catalog')):
            app = _app()
            self.assertTrue(any('Thailand control:' in w.value for w in app.warning))
            self.assertIn('See the pre-event control evidence', [e.label for e in app.expander])
            app.selectbox(key='ex_preset').select('marmara_lake').run()
            self.assertFalse(app.exception)
            self.assertFalse(any('Thailand control:' in w.value for w in app.warning))
            self.assertTrue(any('Exploratory selection' in c.value for c in app.caption))

    def test_explore_review_note_carries_the_same_scope(self):
        from src.i18n import t
        with patch(**NO_NET), patch('src.explore_panel.search_catalog', side_effect=AssertionError('no catalog')):
            app = _app()
            note = next(m.value for m in app.markdown if m.value.startswith('# Review note · place'))
            self.assertIn(t('scope.case', lang='en'), note)
            self.assertTrue(any(t('scope.case', lang='en') == c.value for c in app.caption))
            app.selectbox(key='ex_preset').select('marmara_lake').run()
            note = next(m.value for m in app.markdown if m.value.startswith('# Review note · place'))
            self.assertIn(t('scope.live', lang='en'), note)

    def test_workflow_explains_selection_and_note_matches_screen(self):
        from src.i18n import t
        from src.navigation import apptest_open
        with patch(**NO_NET):
            app = apptest_open(_app(), 'Researcher workflow')
            self.assertFalse(app.exception)
            captions = ' '.join(c.value for c in app.caption)
            self.assertIn('Why it was listed:', captions)
            self.assertIn(t('release.rank_note', lang='en'), captions)
            self.assertIn(t('scope.louisiana', lang='en'), captions)
            note = next(m.value for m in app.markdown if m.value.startswith('# Review note'))
            self.assertIn(t('scope.louisiana', lang='en'), note)
            self.assertIn(t('release.rank_note', lang='en'), note)
            self.assertIn('2026-07-03', note); self.assertIn('2026-07-15', note)
            app.button(key='lang_tr').click().run()
            note = next(m.value for m in app.markdown if m.value.startswith('# İnceleme notu'))
            self.assertIn(t('scope.louisiana', lang='tr'), note)

    def test_about_page_ends_with_centered_nasa_data_attribution(self):
        from src.navigation import apptest_open
        with patch(**NO_NET):
            app = apptest_open(_app(), 'About')
            self.assertFalse(app.exception)
            last = app.main.markdown[-1].value
            self.assertIn('Satellite data used in this website were obtained through NASA data sources.', last)
            self.assertIn('text-align:center', last)
            self.assertTrue(any('not a NASA source' in c.value and 'does not endorse' in c.value for c in app.caption))
            app.button(key='lang_tr').click().run()
            self.assertIn('Bu web sitesinde kullanılan uydu verileri NASA kaynakları aracılığıyla elde edilmiştir.',
                          app.main.markdown[-1].value)
            app.button(key='theme_toggle').click().run()
            self.assertFalse(app.exception)
            self.assertIn('text-align:center', app.main.markdown[-1].value)


class TerminologyTests(unittest.TestCase):
    def test_no_overclaiming_terms_in_either_language(self):
        from src.locales import EN, TR
        for bad in ('validated rule', 'globally validated', 'proven flood', 'flood detection accuracy', 'confirmed by NASA',
                    'Nothing here has been checked', 'Flood map (validated'):
            self.assertFalse([k for k, v in EN.items() if bad.lower() in v.lower()], bad)
        for bad in ('doğrulanan kural', 'küresel olarak doğrulanmış', 'kanıtlanmış taşkın'):
            self.assertFalse([k for k, v in TR.items() if bad.lower() in v.lower()], bad)
        self.assertEqual(set(EN), set(TR))


if __name__ == '__main__':
    unittest.main()


class MaskedLogTests(unittest.TestCase):
    def test_no_local_home_path_in_tracked_data_and_registry_matches(self):
        import hashlib
        registry = json.loads((ROOT / 'data/masked_logs.json').read_text())['files']
        self.assertEqual(len(registry), 16)
        for name, entry in registry.items():
            content = (ROOT / name).read_bytes()
            self.assertEqual(hashlib.sha256(content).hexdigest(), entry['masked_sha256'], name)
            self.assertNotIn(b'/Users/', content, name)
        for path in (ROOT / 'data').rglob('*'):
            if path.is_file() and 'live_cache' not in path.parts and path.suffix in ('.log', '.json', '.md', '.txt', '.csv'):
                self.assertNotIn(str(Path.home()).encode(), path.read_bytes(), str(path))   # no literal path in this file
