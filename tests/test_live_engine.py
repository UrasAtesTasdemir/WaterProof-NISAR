"""Live window engine and 'Explore the world' page, with a MOCKED range reader (no network).

The small arrays and product names below are test fixtures for the engine's plumbing only; they never
reach the app. One optional real-network test runs only when NISAR_LIVE_TEST=1 and a token exist.
"""
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from datetime import date, timedelta
import io
import json
import logging
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from rasterio.transform import Affine

from src.live_engine import (LiveError, validate_point, validate_dates, validate_window, window_polygon, parse_product,
                             group_products, search_catalog, cache_key, cache_get, cache_put, run_live, MAX_DATES, utm_epsg)

ROOT = Path(__file__).resolve().parents[1]
TOKEN = 'TEST-TOKEN-do-not-leak-7f3a9c'
TODAY = date(2026, 11, 15)


def fixture_url(day, track='105', frame='017', mode='DHDH', crid='P05023'):
    return ('https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_BETA_V1/'
            f'NISAR_L2_PR_GCOV_023_{track}_A_{frame}_4005_{mode}_A_{day}T111906_{day}T111941_{crid}_N_F_J_001/'
            f'NISAR_L2_PR_GCOV_023_{track}_A_{frame}_4005_{mode}_A_{day}T111906_{day}T111941_{crid}_N_F_J_001.h5')


def fixture_products(days=('20260621', '20260703', '20260715'), **kw):
    return [parse_product(fixture_url(d, **kw)) for d in days]


class FakeReader:
    """Mocked opener + subset: returns small deterministic power windows and counts reads."""
    def __init__(self, shape=(40, 40), fail_with=None, bytes_per_read=1000):
        self.calls = 0; self.shape = shape; self.fail_with = fail_with; self.bytes = bytes_per_read; self.tokens = []

    @contextmanager
    def opener(self, product, token):
        self.calls += 1; self.tokens.append(token)
        if self.fail_with:
            raise self.fail_with
        yield dict(product=product), {'range_bytes_read': self.bytes}

    def subset(self, dataset, polygon, layer_name='HHHH'):
        seed = int(dataset['product']['date'].replace('-', '')) % 97 + (0 if layer_name == 'HHHH' else 50)
        power = np.random.default_rng(seed).uniform(0.01, 0.2, self.shape)
        transform = Affine(10, 0, 750000, 0, -10, 3315000)
        return power, 10 * np.log10(power), 'EPSG:32615', transform, dict(layer=layer_name)


class ValidationTests(unittest.TestCase):
    def test_point_dates_window_validation(self):
        self.assertEqual(validate_point('29.9', -90.28), (29.9, -90.28))
        for lat, lon in ((91, 0), (-91, 0), (0, 181), (0, -181), (float('nan'), 0), ('north', 0), (85, 0)):
            with self.assertRaises(LiveError):
                validate_point(lat, lon)
        self.assertEqual(validate_dates('2026-06-01', '2026-09-30', today=TODAY), (date(2026, 6, 1), date(2026, 9, 30)))
        for start, end in (('2026-09-30', '2026-06-01'), ('2024-01-01', '2024-02-01'), ('2026-12-01', '2026-12-30'),
                           ('2025-08-01', '2026-11-01'), ('not-a-date', '2026-01-01')):
            with self.assertRaises(LiveError):
                validate_dates(start, end, today=TODAY)
        for km in (0.5, 10.5, float('inf'), 'big'):
            with self.assertRaises(LiveError):
                validate_window(km)

    def test_window_is_a_square_of_the_requested_size(self):
        from rasterio.warp import transform_geom
        from shapely.geometry import mapping, shape
        for lat, lon, km in ((29.91, -90.28, 5), (-33.9, 151.2, 10), (60.1, 24.9, 1)):
            polygon = window_polygon(lat, lon, km)
            projected = shape(transform_geom('EPSG:4326', f'EPSG:{utm_epsg(lat, lon)}', mapping(polygon)))
            self.assertAlmostEqual(projected.area / 1e6, km * km, delta=km * km * 0.01)
            self.assertTrue(polygon.contains(__import__('shapely').geometry.Point(lon, lat)))
        with self.assertRaises(LiveError):
            window_polygon(29.9, -90.3, 25)


class CatalogTests(unittest.TestCase):
    def test_parse_and_group_compatible_acquisitions(self):
        products = fixture_products() + fixture_products(('20260627',), track='042') + fixture_products(('20260621',), mode='SHNA')
        self.assertTrue(all(products))
        groups = group_products(products)
        self.assertEqual(groups[0]['dates'], ['2026-06-21', '2026-07-03', '2026-07-15'])
        self.assertTrue(groups[0]['has_hh_hv'])
        self.assertEqual({g['key']['track'] for g in groups}, {'105', '042'})
        self.assertFalse(next(g for g in groups if g['key']['polarization'] == 'SHNA')['has_hh_hv'])
        self.assertIsNone(parse_product('https://example.org/not_a_nisar_file.h5'))

    def test_search_uses_the_point_and_reports_failures_without_details(self):
        class Record:
            def __init__(self, url): self.url = url
            def find_urls(self, **kw): return [self.url, self.url.replace('.h5', '_QA_STATS.h5')]
        seen = {}
        def search(**options):
            seen.update(options); return [Record(fixture_url('20260703')), Record(fixture_url('20260621'))]
        products, truncated = search_catalog(29.9, -90.28, '2026-06-01', '2026-07-31', search=search)
        self.assertEqual([p['date'] for p in products], ['2026-06-21', '2026-07-03'])
        self.assertFalse(truncated)
        self.assertEqual(seen['intersectsWith'], 'POINT(-90.280000 29.900000)')
        self.assertNotIn('token', json.dumps(seen, default=str).lower())
        def broken(**options):
            raise ConnectionError('boom http://secret-url')
        with self.assertRaises(LiveError) as ctx:
            search_catalog(29.9, -90.28, '2026-06-01', '2026-07-31', search=broken)
        self.assertNotIn('secret-url', ctx.exception.text())


class CacheAndRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.cache = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_cache_miss_then_hit_and_offline_repeat_without_token(self):
        reader = FakeReader(); products = fixture_products()
        cube = run_live(products, 29.91, -90.28, 5, TOKEN, opener=reader.opener, subset=reader.subset, cache_dir=self.cache)
        self.assertEqual(reader.calls, 3); self.assertEqual(cube['bytes_read_this_run'], 3000)
        self.assertEqual(cube['hh_power'].shape, (3, 40, 40)); self.assertEqual(cube['dates_from_cache'], 0)
        repeat = run_live(products, 29.91, -90.28, 5, None, opener=reader.opener, subset=reader.subset, cache_dir=self.cache)
        self.assertEqual(reader.calls, 3)                       # no new reads: offline repeat from the cache
        self.assertEqual(repeat['bytes_read_this_run'], 0); self.assertEqual(repeat['dates_from_cache'], 3)
        np.testing.assert_allclose(repeat['hh_power'], cube['hh_power'], rtol=1e-6)   # float32 storage
        with self.assertRaises(LiveError) as ctx:                # a different window is a cache miss and needs a token
            run_live(products, 29.95, -90.28, 5, None, opener=reader.opener, subset=reader.subset, cache_dir=self.cache)
        self.assertEqual(ctx.exception.key, 'live.err.token')

    def test_caps_and_compatibility(self):
        reader = FakeReader()
        many = fixture_products(tuple(f'202607{d:02d}' for d in range(1, MAX_DATES + 2)))
        for products, key in ((many, 'live.err.too_many'), ([], 'live.err.none'),
                              (fixture_products() + fixture_products(('20260627',), track='042'), 'live.err.mixed'),
                              (fixture_products(mode='SHNA'), 'live.err.no_hv')):
            with self.assertRaises(LiveError) as ctx:
                run_live(products, 29.91, -90.28, 5, TOKEN, opener=reader.opener, subset=reader.subset, cache_dir=self.cache)
            self.assertEqual(ctx.exception.key, key)
        big = FakeReader(bytes_per_read=600 * 1024 * 1024)
        with self.assertRaises(LiveError) as ctx:
            run_live(fixture_products(), 29.91, -90.28, 5, TOKEN, opener=big.opener, subset=big.subset, cache_dir=self.cache)
        self.assertEqual(ctx.exception.key, 'live.err.budget')
        self.assertLessEqual(big.calls, 2)
        with self.assertRaises(LiveError):
            run_live(fixture_products(), 29.91, -90.28, 25, TOKEN, opener=reader.opener, subset=reader.subset, cache_dir=self.cache)

    def test_cache_is_size_capped_and_tamper_checked(self):
        meta = dict(product_id='x')
        for i in range(4):
            cache_put(f'k{i}', np.ones((200, 200)), np.ones((200, 200)), meta, self.cache, limit=1)
        self.assertEqual([p.name for p in self.cache.iterdir()], ['k3'])
        (self.cache / 'k3' / 'window.npz').write_bytes(b'tampered')
        self.assertIsNone(cache_get('k3', self.cache))

    def test_token_never_reaches_cache_logs_or_errors(self):
        reader = FakeReader(); out = io.StringIO(); log = io.StringIO()
        handler = logging.StreamHandler(log); logging.getLogger().addHandler(handler); logging.getLogger().setLevel(logging.DEBUG)
        try:
            with redirect_stdout(out), redirect_stderr(out):
                run_live(fixture_products(), 29.91, -90.28, 5, TOKEN, opener=reader.opener, subset=reader.subset, cache_dir=self.cache)
                failing = FakeReader(fail_with=RuntimeError(f'Authorization: Bearer {TOKEN} rejected'))
                with self.assertRaises(LiveError) as ctx:
                    run_live(fixture_products(('20260801',)), 29.91, -90.28, 5, TOKEN, opener=failing.opener, subset=failing.subset,
                             cache_dir=self.cache)
        finally:
            logging.getLogger().removeHandler(handler)
        self.assertNotIn(TOKEN, ctx.exception.text()); self.assertNotIn(TOKEN, str(ctx.exception)); self.assertNotIn(TOKEN, repr(ctx.exception))
        self.assertIsNone(ctx.exception.__cause__)
        self.assertNotIn(TOKEN, out.getvalue()); self.assertNotIn(TOKEN, log.getvalue())
        for path in self.cache.rglob('*'):
            if path.is_file():
                self.assertNotIn(TOKEN.encode(), path.read_bytes(), path)
        key = cache_key('PRODUCT', (1.0, 2.0, 3.0, 4.0))
        self.assertNotIn('token', cache_key.__code__.co_varnames)
        self.assertEqual(key, cache_key('PRODUCT', (1.0, 2.0, 3.0, 4.0)))     # the same with any token: tokens are not inputs

    def test_streamlit_caches_never_take_a_token(self):
        pattern = re.compile(r'@st\.cache_(?:data|resource)[^\n]*\n\s*def \w+\(([^)]*)\)')
        for name in ('src/explore_panel.py', 'src/live_engine.py', 'src/explore.py'):
            for params in pattern.findall((ROOT / name).read_text()):
                for param in [p.strip().split('=')[0] for p in params.split(',') if p.strip()]:
                    self.assertFalse('token' in param.lower() and not param.startswith('_'), (name, param))


class ExplorePageTests(unittest.TestCase):
    def _app(self):
        from streamlit.testing.v1 import AppTest
        from src.navigation import apptest_open
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=90).run()
        return apptest_open(app, 'Explore the world')

    def test_cached_louisiana_case_runs_end_to_end(self):
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Network disabled')):
            app = self._app()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['ex_preset'], 'thailand_prachinburi')   # guided example is the first view
            app.selectbox(key='ex_preset').select('louisiana_c1').run()
            self.assertFalse(app.exception)
            text = ' '.join(m.value for m in app.markdown)
            self.assertIn('Compass reading', text); self.assertIn('Most important uncertainty', text)
            self.assertTrue(any(m.value.startswith('# Review note · place') for m in app.markdown))
            self.assertTrue(app.get('download_button'))
            self.assertTrue(any('24 days' in c.value for c in app.caption))
            self.assertTrue(any('Other explanations' in m.value for m in app.markdown))
            app.button(key='lang_tr').click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any(m.value.startswith('# İnceleme notu · yer') for m in app.markdown))

    def test_no_data_state_and_pasted_token_is_never_displayed(self):
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Network disabled')), \
             patch('src.explore_panel.server_token', return_value=None), \
             patch('src.explore_panel.search_catalog', return_value=([], False)):
            app = self._app()
            app.selectbox(key='ex_preset').select('custom').run()
            app.number_input(key='ex_lat').set_value(10.5).run(); app.number_input(key='ex_lon').set_value(20.5).run()
            self.assertFalse(app.exception)
            app.text_input(key='ex_token_input').input(TOKEN).run()
            app.button(key='ex_catalog_search').click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any('No NISAR GCOV product covers this point' in w.value for w in app.warning))
            for element in list(app.markdown) + list(app.caption) + list(app.info) + list(app.warning) + list(app.error) + list(app.success):
                self.assertNotIn(TOKEN, element.value)
            self.assertNotIn(TOKEN, str({k: v for k, v in app.session_state._state._state.filtered_state.items() if k != 'ex_token_input'}))

    def test_invalid_place_shows_message_not_traceback(self):
        with patch('requests.sessions.Session.request', side_effect=AssertionError('Network disabled')):
            app = self._app()
            app.number_input(key='ex_lat').set_value(88.0).run()
            self.assertFalse(app.exception)
            self.assertTrue(any('±84°' in e.value for e in app.error))


@unittest.skipUnless(os.environ.get('NISAR_LIVE_TEST') == '1', 'real-network test: set NISAR_LIVE_TEST=1 (needs an Earthdata token)')
class RealNetworkTests(unittest.TestCase):
    def test_catalog_and_one_live_window(self):
        from scripts.check_earthdata_access import available_token
        token = available_token()
        if not token:
            self.skipTest('No Earthdata token available.')
        products, _ = search_catalog(29.9135, -90.2804, '2026-06-20', '2026-07-05')
        group = group_products(products)[0]
        with tempfile.TemporaryDirectory() as cache:
            cube = run_live(group['products'][:2], 29.9135, -90.2804, 1, token, cache_dir=cache)
        self.assertEqual(cube['hh_power'].shape[0], 2)


if __name__ == '__main__':
    unittest.main()
