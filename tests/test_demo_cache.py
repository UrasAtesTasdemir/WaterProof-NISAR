"""Shipped offline demo cache: lookup order, read-only use, offline presets, catalog snapshot, token safety, hashes.

Synthetic arrays exist ONLY inside these tests (FakeReader fixtures); the app never shows them.
The last tests check the real shipped data/demo_cache against its sidecar.
"""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src import demo_places
from src.live_engine import DEMO_CACHE_DIR, LiveError, cache_key, cache_lookup, run_live, window_polygon
from tests.test_live_engine import FakeReader, fixture_products, TOKEN

ROOT = Path(__file__).resolve().parents[1]
LAT, LON, KM = 29.91, -90.28, 5.0
NO_NET = dict(target='requests.sessions.Session.request', side_effect=AssertionError('Network disabled'))


def _files(directory):
    return {str(p.relative_to(directory)): (p.stat().st_mtime_ns, p.read_bytes()) for p in Path(directory).rglob('*') if p.is_file()}


def _fixture_demo(directory, products, reader):
    """A synthetic demo cache in `directory`, written the way scripts/prewarm_demo.py writes it."""
    from scripts.prewarm_demo import snapshot_products, write_sidecar
    directory = Path(directory)
    run_live(products, LAT, LON, KM, TOKEN, opener=reader.opener, subset=reader.subset, cache_dir=directory, demo_dir=None)
    (directory / 'catalog').mkdir(); (directory / 'places').mkdir()
    (directory / 'catalog/fixture.json').write_text(json.dumps(dict(
        place='fixture', snapshot_date='2026-11-15', count=len(products), products=snapshot_products(products))))
    bounds = window_polygon(LAT, LON, KM).bounds
    (directory / 'places/fixture.json').write_text(json.dumps(dict(
        place='fixture', lat=LAT, lon=LON, window_km=KM, status='cached', dates=[p['date'] for p in products],
        product_ids=[p['product_id'] for p in products], cache_keys=[cache_key(p['product_id'], bounds) for p in products],
        catalog_snapshot='catalog/fixture.json')))
    write_sidecar(directory)


class LookupOrderTests(unittest.TestCase):
    def test_demo_cache_then_live_cache_then_network(self):
        products = fixture_products(('20260621', '20260703', '20260715'))
        with tempfile.TemporaryDirectory() as demo, tempfile.TemporaryDirectory() as live:
            run_live(products[:1], LAT, LON, KM, TOKEN, opener=FakeReader().opener, subset=FakeReader().subset,
                     cache_dir=demo, demo_dir=None)                                   # date 1 shipped
            run_live(products[1:2], LAT, LON, KM, TOKEN, opener=FakeReader().opener, subset=FakeReader().subset,
                     cache_dir=live, demo_dir=None)                                   # date 2 in the local live cache
            key = lambda p: cache_key(p['product_id'], window_polygon(LAT, LON, KM).bounds)
            self.assertEqual(cache_lookup(key(products[0]), live, demo)[1], 'demo')
            self.assertEqual(cache_lookup(key(products[1]), live, demo)[1], 'cache')
            self.assertEqual(cache_lookup(key(products[2]), live, demo), (None, None))
            reader = FakeReader(); seen = []
            cube = run_live(products, LAT, LON, KM, TOKEN, opener=reader.opener, subset=reader.subset, cache_dir=live,
                            demo_dir=demo, progress=lambda i, n, p, how: seen.append(how))
            self.assertEqual(reader.calls, 1)                                         # only date 3 went to the "network"
            self.assertEqual(seen, ['cache', 'cache', 'read'])
            self.assertEqual(cube['dates_from_cache'], 2)

    def test_demo_cache_is_never_written_at_run_time(self):
        products = fixture_products(('20260621', '20260703'))
        with tempfile.TemporaryDirectory() as demo, tempfile.TemporaryDirectory() as live:
            run_live(products[:1], LAT, LON, KM, TOKEN, opener=FakeReader().opener, subset=FakeReader().subset,
                     cache_dir=demo, demo_dir=None)
            before = _files(demo)
            run_live(products, LAT, LON, KM, TOKEN, opener=FakeReader().opener, subset=FakeReader().subset,
                     cache_dir=live, demo_dir=demo)
            self.assertEqual(_files(demo), before)                                  # new date went to the live cache
            self.assertEqual(len([p for p in Path(live).iterdir() if p.is_dir()]), 1)


class OfflinePresetTests(unittest.TestCase):
    def test_demo_place_runs_offline_without_token(self):
        products = fixture_products(('20260621', '20260703', '20260715'))
        with tempfile.TemporaryDirectory() as demo:
            _fixture_demo(demo, products, FakeReader())
            self.assertEqual(demo_places.verify(demo), [])
            place = demo_places.places(demo)[0]
            self.assertEqual((place['key'], place['cached'], place['case']), ('fixture', True, 'demo'))
            with patch(**NO_NET), patch('src.nisar_data.open_frequency_a', side_effect=AssertionError('no reads')):
                cube = demo_places.demo_cube(place, demo)
            self.assertEqual(cube['source'], 'demo'); self.assertEqual(cube['bytes_read_this_run'], 0)
            self.assertEqual(cube['dates'], ['2026-06-21', '2026-07-03', '2026-07-15'])
            groups = demo_places.snapshot_groups(place)
            self.assertEqual(len(groups), 1); self.assertTrue(groups[0]['has_hh_hv'])

    def test_missing_window_is_reported_as_pending_not_filled(self):
        products = fixture_products(('20260621', '20260703'))
        with tempfile.TemporaryDirectory() as demo:
            _fixture_demo(demo, products, FakeReader())
            place = demo_places.places(demo)[0]
            first_key = place['manifest']['cache_keys'][0]
            for f in (Path(demo) / first_key).iterdir():
                f.unlink()
            (Path(demo) / first_key).rmdir()
            self.assertEqual(demo_places.missing_dates(place, demo), ['2026-06-21'])
            with self.assertRaises(LiveError) as caught:
                demo_places.demo_cube(place, demo)
            self.assertEqual(caught.exception.key, 'ex.demo.pending')
            self.assertTrue(demo_places.verify(demo))                               # sidecar notices the removal

    def test_tampered_entry_is_detected(self):
        products = fixture_products(('20260621', '20260703'))
        with tempfile.TemporaryDirectory() as demo:
            _fixture_demo(demo, products, FakeReader())
            meta = next(Path(demo).glob('*/meta.json'))
            meta.write_text(meta.read_text().replace('"layers"', '"layerz"'))
            self.assertEqual(demo_places.verify(demo), [str(meta.relative_to(demo))])


class SnapshotAndTokenTests(unittest.TestCase):
    def test_snapshot_urls_have_no_query_and_no_token(self):
        from scripts.prewarm_demo import plain_url, snapshot_products
        self.assertEqual(plain_url('https://h.example/a/b.h5?X-Amz-Signature=abc&token=x#f'), 'https://h.example/a/b.h5')
        products = fixture_products(('20260621',))
        products[0]['download_url'] += '?X-Amz-Credential=secret'
        self.assertNotIn('?', json.dumps(snapshot_products(products)))

    def test_token_never_in_keys_logs_or_files(self):
        import logging
        previous = logging.root.manager.disable                      # other tests may disable logging globally
        logging.disable(logging.NOTSET); self.addCleanup(logging.disable, previous)
        products = fixture_products(('20260621', '20260703'))
        out, err = io.StringIO(), io.StringIO()
        with tempfile.TemporaryDirectory() as demo, redirect_stdout(out), redirect_stderr(err), \
                self.assertLogs(level='DEBUG') as logs:
            logging.getLogger('demo-test').warning('start')
            _fixture_demo(demo, products, FakeReader())
            place = demo_places.places(demo)[0]
            demo_places.demo_cube(place, demo)
            for path in Path(demo).rglob('*'):
                self.assertNotIn(TOKEN[:12], path.name)
                if path.is_file():
                    self.assertNotIn(TOKEN.encode(), path.read_bytes())
                    self.assertNotIn(TOKEN[:12].encode(), path.read_bytes())
            for key in place['manifest']['cache_keys']:
                self.assertNotIn(TOKEN, key)
        for text in (out.getvalue(), err.getvalue(), '\n'.join(logs.output)):
            self.assertNotIn(TOKEN[:12], text)

    def test_catalog_snapshot_label_in_app(self):
        if not demo_places.places():
            self.skipTest('no shipped demo place yet')
        from streamlit.testing.v1 import AppTest
        from src.navigation import apptest_open
        key = demo_places.places()[0]['key']
        with patch(**NO_NET), patch('src.explore_panel.search_catalog', side_effect=AssertionError('no catalog')):
            app = apptest_open(AppTest.from_file(str(ROOT / 'app.py'), default_timeout=180).run(), 'Explore the world')
            app.selectbox(key='ex_preset').select(key).run()
            self.assertFalse(app.exception)
            self.assertTrue(any(e.label.startswith('Catalog snapshot from 20') for e in app.expander))
            self.assertTrue(any(c.value.startswith('Catalog snapshot from 20') for c in app.caption))


class ShippedDemoCacheTests(unittest.TestCase):
    def test_every_shipped_file_matches_its_sidecar_hash(self):
        if not (DEMO_CACHE_DIR / 'sidecar.json').exists():
            self.skipTest('data/demo_cache not pre-warmed yet')
        self.assertEqual(demo_places.verify(), [])
        sidecar = json.loads((DEMO_CACHE_DIR / 'sidecar.json').read_text())
        self.assertFalse(sidecar['credentials_stored'])
        # 25 MiB for the three surface-type places; raised to 40 MiB when the owner asked to ship the Thailand
        # flood-validation scene (3 x 10 km windows at 10 m, ~17 MiB) on 2026-11-15.
        self.assertLess(sidecar['total_bytes'], 40 * 1024 * 1024)

    def test_shipped_places_contain_no_credentials_or_signed_urls(self):
        for path in DEMO_CACHE_DIR.rglob('*.json'):
            text = path.read_text().lower()
            for marker in ('x-amz-signature', 'x-amz-credential', 'authorization', 'bearer ', 'token=', '?'):
                self.assertNotIn(marker, text, (path.name, marker))

    def test_demo_cache_is_tracked_and_live_cache_is_ignored(self):
        lines = [l.strip() for l in (ROOT / '.gitignore').read_text().splitlines()]
        self.assertIn('data/live_cache/', lines)
        self.assertFalse(any(l.startswith('data/demo_cache') or l in ('data/', 'data/*') for l in lines))

    def test_shipped_places_run_offline_end_to_end(self):
        places = [p for p in demo_places.places() if p['manifest'].get('status') == 'cached']
        if not places:
            self.skipTest('no pre-warmed demo place yet')
        from src.explore import analyze
        with patch(**NO_NET), patch('src.nisar_data.open_frequency_a', side_effect=AssertionError('no reads')):
            for place in places:
                cube = demo_places.demo_cube(place)
                self.assertEqual(len(cube['dates']), len(place['manifest']['dates']))
                try:
                    ctx = analyze(cube)          # whatever the data say, including inconclusive
                    self.assertTrue(ctx['reading']['key'])
                except ValueError:
                    pass                          # 'not enough common valid pixels' is a legitimate shown state


if __name__ == '__main__':
    unittest.main()
