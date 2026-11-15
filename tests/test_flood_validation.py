"""PO.DAAC reference reader safety and DSWx class mapping (no network: a fake HTTP session)."""
import io
from contextlib import redirect_stdout, redirect_stderr
import unittest

import numpy as np

from src import podaac_reader as pr
from src.flood_classes import CODES, OPEN, NOT_WATER, PARTIAL, INVALID, UNDEFINED, masks, role_map, summarize

TOKEN = 'TEST-EDL-TOKEN-never-leak-91c2'
ARCHIVE = 'https://archive.podaac.earthdata.nasa.gov/podaac-ops-cumulus-protected/OPERA_L3_DSWX-HLS_V1/x_B01_WTR.tif'
CDN = 'https://deotb6e7tfubr.cloudfront.net/s3-abc/bucket/x_B01_WTR.tif?Signature=SECRETSIG&Key-Pair-Id=K1'
S3 = 'https://podaac-ops-cumulus-protected.s3.us-west-2.amazonaws.com/x.tif?X-Amz-Signature=SECRETSIG'


class FakeResponse:
    def __init__(self, status, headers=None, body=b'II*\x00' + b'\x00' * 12, url=''):
        self.status_code = status; self.headers = headers or {}; self.raw = io.BytesIO(body); self.content = body; self.url = url

    def close(self):
        pass


class FakeSession:
    """Scripted responses keyed by URL; records every request (url, headers)."""
    def __init__(self, script):
        self.script = script; self.requests = []

    def get(self, url, headers=None, **kwargs):
        self.requests.append((url, dict(headers or {})))
        response = self.script.get(url)
        if response is None:
            raise AssertionError(f'unexpected request to {url}')
        return response() if callable(response) else response


def ok_206(size=1000):
    return FakeResponse(206, {'Content-Range': f'bytes 0-15/{size}', 'Accept-Ranges': 'bytes'})


def redirect(to, status=303):
    return FakeResponse(status, {'Location': to})


class HostTests(unittest.TestCase):
    def test_allowed_hosts(self):
        self.assertEqual(pr.classify_host(ARCHIVE), 'archive')
        self.assertEqual(pr.classify_host('https://urs.earthdata.nasa.gov/oauth/authorize?x=1'), 'urs')
        self.assertEqual(pr.classify_host(S3), 's3')
        self.assertEqual(pr.classify_host(CDN), 'cdn')

    def test_rejected_urls(self):
        for url in ('http://archive.podaac.earthdata.nasa.gov/x.tif',                    # not https
                    'https://archive.podaac.earthdata.nasa.gov.evil.example/x.tif',      # look-alike
                    'https://evil.example/archive.podaac.earthdata.nasa.gov/x.tif',
                    'https://other.cloudfront.net/x.tif',                                # other CDN host
                    'https://bucket.s3.amazonaws.com.evil.example/x.tif',
                    'https://s3.us-west-2.amazonaws.com/bucket/x.tif',                    # not the exact pattern
                    'https://user:pw@archive.podaac.earthdata.nasa.gov/x.tif',           # user-info
                    'https://archive.podaac.earthdata.nasa.gov:8443/x.tif',              # port
                    'ftp://archive.podaac.earthdata.nasa.gov/x.tif'):
            with self.assertRaises(pr.ReferenceAccessError, msg=url):
                pr.classify_host(url)


class RedirectTests(unittest.TestCase):
    def test_token_only_to_archive_never_to_cdn_or_s3(self):
        for target in (CDN, S3):
            session = FakeSession({ARCHIVE: redirect(target), target: ok_206()})
            log = []
            url, size = pr.resolve(ARCHIVE, TOKEN, session, log)
            self.assertEqual((url, size), (target, 1000))
            (u1, h1), (u2, h2) = session.requests
            self.assertEqual(h1.get('Authorization'), 'Bearer ' + TOKEN)
            self.assertNotIn('Authorization', h2)
            self.assertNotIn(TOKEN, repr(h2))
            text = repr(log)
            self.assertNotIn('SECRETSIG', text); self.assertNotIn(TOKEN, text)
            self.assertEqual([e['token_sent'] for e in log], [True, False])

    def test_urs_gets_token_only_after_a_real_login_redirect(self):
        urs = 'https://urs.earthdata.nasa.gov/oauth/authorize?client_id=x'
        session = FakeSession({ARCHIVE: redirect(urs, 302), urs: redirect(CDN, 302), CDN: ok_206()})
        pr.resolve(ARCHIVE, TOKEN, session, [])
        self.assertIn('Authorization', session.requests[1][1])
        direct = FakeSession({urs: ok_206()})
        pr.resolve(urs, TOKEN, direct, [])                       # starting at URS is not a login redirect
        self.assertNotIn('Authorization', direct.requests[0][1])

    def test_redirect_to_unlisted_host_is_rejected_before_any_request(self):
        evil = 'https://evil.example/steal?x=1'
        session = FakeSession({ARCHIVE: redirect(evil)})
        with self.assertRaises(pr.ReferenceAccessError) as caught:
            pr.resolve(ARCHIVE, TOKEN, session, [])
        self.assertEqual(len(session.requests), 1)              # evil host never contacted
        self.assertNotIn(TOKEN, str(caught.exception))
        http = FakeSession({ARCHIVE: redirect('http://deotb6e7tfubr.cloudfront.net/x.tif')})
        with self.assertRaises(pr.ReferenceAccessError):
            pr.resolve(ARCHIVE, TOKEN, http, [])

    def test_redirect_limit_is_six(self):
        chain = [f'https://archive.podaac.earthdata.nasa.gov/hop{i}.tif' for i in range(8)]
        script = {chain[i]: redirect(chain[i + 1]) for i in range(7)}
        script[chain[6]] = ok_206()
        pr.resolve(chain[0], TOKEN, FakeSession(dict(script)), [])          # 6 redirects: allowed
        script[chain[6]] = redirect(chain[7]); script[chain[7]] = ok_206()
        with self.assertRaises(pr.ReferenceAccessError) as caught:
            pr.resolve(chain[0], TOKEN, FakeSession(script), [])            # 7th redirect: refused
        self.assertIn('Redirect limit', str(caught.exception))

    def test_not_range_readable_or_not_tiff_fails_loudly(self):
        whole = FakeSession({ARCHIVE: redirect(CDN), CDN: FakeResponse(200, {'Accept-Ranges': 'none'})})
        with self.assertRaises(pr.ReferenceAccessError) as caught:
            pr.resolve(ARCHIVE, TOKEN, whole, [])
        self.assertIn('not range-readable', str(caught.exception)); self.assertNotIn('SECRETSIG', str(caught.exception))
        html = FakeSession({ARCHIVE: redirect(CDN), CDN: FakeResponse(206, {'Content-Range': 'bytes 0-15/99'}, b'<html>' + b' ' * 10)})
        with self.assertRaises(pr.ReferenceAccessError):
            pr.resolve(ARCHIVE, TOKEN, html, [])

    def test_errors_and_output_never_contain_token_or_signature(self):
        class Boom:
            def get(self, url, **kw):
                raise ConnectionError(f'failed {url} with Bearer {TOKEN}')
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err), self.assertRaises(pr.ReferenceAccessError) as caught:
            pr.resolve(ARCHIVE, TOKEN, Boom(), [])
        for text in (str(caught.exception), out.getvalue(), err.getvalue()):
            self.assertNotIn(TOKEN, text); self.assertNotIn('SECRETSIG', text)
        self.assertEqual(pr.safe_url(CDN), 'https://deotb6e7tfubr.cloudfront.net/s3-abc/bucket/x_B01_WTR.tif')


class ByteCapTests(unittest.TestCase):
    def test_per_window_and_total_caps(self):
        budget = pr.ByteBudget(total=1000)
        w = budget.window(cap=600)
        w.charge(500)
        with self.assertRaises(pr.ReferenceAccessError):
            w.charge(200)                                         # window cap
        w2 = budget.window(cap=600)
        with self.assertRaises(pr.ReferenceAccessError):
            w2.charge(600)                                        # total cap (500 + 600 > 1000)
        self.assertEqual(budget.total, 500)

    def test_range_file_reads_without_token_and_refuses_huge_reads(self):
        session = FakeSession({CDN: FakeResponse(206, {}, b'abcdefgh')})
        budget = pr.ByteBudget().window(cap=pr.BLOCK)
        f = pr.RangeFile(CDN, 10_000_000, budget, session)
        self.assertEqual(f.read(8), b'abcdefgh')
        self.assertNotIn('Authorization', session.requests[0][1])
        self.assertEqual(session.requests[0][1]['Range'], f'bytes=0-{pr.BLOCK - 1}')   # one cached block
        self.assertEqual(budget.read, pr.BLOCK)
        f.seek(2); self.assertEqual(f.read(3), b'cde'); self.assertEqual(len(session.requests), 1)  # served from cache
        with self.assertRaises(pr.ReferenceAccessError):
            f.read(pr.MAX_REQUEST + 1)                           # never a whole-file read
        with self.assertRaises(pr.ReferenceAccessError):
            pr.RangeFile(ARCHIVE, 10, budget, session)            # range reads never go to the token host


class ClassMappingTests(unittest.TestCase):
    def test_hls_table(self):
        codes = np.array([0, 1, 2, 252, 253, 254, 255, 3, 250])
        self.assertEqual(list(role_map(codes, 'HLS')),
                         [NOT_WATER, OPEN, PARTIAL, INVALID, INVALID, INVALID, INVALID, UNDEFINED, UNDEFINED])

    def test_s1_table(self):
        codes = np.array([0, 1, 3, 250, 251, 255, 2, 5, 6, 7, 8, 252, 253, 254])
        self.assertEqual(list(role_map(codes, 'S1')),
                         [NOT_WATER, OPEN, PARTIAL, INVALID, INVALID, INVALID] + [UNDEFINED] * 8)

    def test_tables_are_not_assumed_equal(self):
        self.assertNotEqual(CODES['HLS'], CODES['S1'])
        self.assertEqual(role_map(np.array([2]), 'S1')[0], UNDEFINED)     # HLS partial code is undefined in S1
        self.assertEqual(role_map(np.array([3]), 'HLS')[0], UNDEFINED)    # S1 inundated code is undefined in HLS

    def test_invalid_and_undefined_never_water_or_not_water(self):
        codes = np.array([1, 1, 0, 0, 253, 255, 7])
        s = summarize(codes, 'HLS')
        self.assertAlmostEqual(s['valid_fraction'], 4 / 7)
        self.assertAlmostEqual(s['open_water_share_of_valid'], 0.5)
        self.assertEqual(s['undefined_codes'], [7])
        m = masks(codes, 'HLS')
        self.assertFalse((m[OPEN] & (m[INVALID] | m[UNDEFINED])).any())
        self.assertFalse((m[NOT_WATER] & (m[INVALID] | m[UNDEFINED])).any())

    def test_usable_threshold(self):
        self.assertTrue(summarize(np.array([0] * 7 + [255] * 3), 'S1')['usable'])
        self.assertFalse(summarize(np.array([0] * 6 + [255] * 4), 'S1')['usable'])


if __name__ == '__main__':
    unittest.main()


class DemReaderTests(unittest.TestCase):
    def test_host_allowlist(self):
        from src import dem_reader as dr
        dr.check_url(dr.tile_url(14.05, 101.37))
        self.assertTrue(dr.tile_url(14.05, 101.37).endswith('Copernicus_DSM_COG_10_N14_00_E101_00_DEM.tif'))
        self.assertTrue(dr.tile_url(26.7, 84.28).endswith('N26_00_E084_00_DEM.tif'))
        for url in ('http://copernicus-dem-30m.s3.amazonaws.com/x.tif', 'https://copernicus-dem-30m.s3.amazonaws.com.evil.example/x.tif',
                    'https://copernicus-dem-90m.s3.amazonaws.com/x.tif', 'https://evil.example/x.tif',
                    'https://u:p@copernicus-dem-30m.s3.amazonaws.com/x.tif', 'https://copernicus-dem-30m.s3.amazonaws.com:444/x.tif'):
            with self.assertRaises(dr.DemAccessError, msg=url):
                dr.check_url(url)

    def test_no_auth_header_redirect_rules_and_limit(self):
        from src import dem_reader as dr
        url = dr.tile_url(14.05, 101.37)
        session = FakeSession({url: ok_206()})
        dr.resolve(url, session, [])
        self.assertNotIn('Authorization', session.requests[0][1])
        bad = FakeSession({url: redirect('https://evil.example/x.tif')})
        with self.assertRaises(dr.DemAccessError):
            dr.resolve(url, bad, [])
        self.assertEqual(len(bad.requests), 1)
        hops = [f'https://copernicus-dem-30m.s3.amazonaws.com/h{i}.tif' for i in range(8)]
        script = {hops[i]: redirect(hops[i + 1]) for i in range(7)}; script[hops[7]] = ok_206()
        with self.assertRaises(dr.DemAccessError):
            dr.resolve(hops[0], FakeSession(script), [])
        with self.assertRaises(dr.DemAccessError):
            dr.DemRangeFile('https://evil.example/x.tif', 10, pr.ByteBudget().window(), session)

    def test_slope_of_a_plane(self):
        from src import dem_reader as dr
        a = 1 / 3600; transform = (a, 0, 101.0, 0, -a, 15.0)
        rows, cols = np.mgrid[0:50, 0:50]
        dy = a * 111_320.0
        height = rows * dy * np.tan(np.radians(10))           # 10 degree slope towards south
        slope = dr.slope_degrees(height, transform)
        self.assertAlmostEqual(float(np.median(slope)), 10.0, delta=0.05)
        self.assertAlmostEqual(float(np.median(dr.slope_degrees(np.zeros((20, 20)), transform))), 0.0)


class MetricTests(unittest.TestCase):
    def test_grid_alignment_nearest_keeps_codes_and_marks_outside_invalid(self):
        from src.flood_validation import align_reference
        codes = np.array([[0, 1], [2, 253]], np.uint8)                       # 30 m reference pixels
        src_t = (30.0, 0.0, 1000.0, 0.0, -30.0, 2000.0)
        dst_t = (10.0, 0.0, 1000.0, 0.0, -10.0, 2000.0)                      # 10 m NISAR grid, extends 1 pixel beyond
        out = align_reference(codes, src_t, 'EPSG:32647', (7, 7), dst_t, 'EPSG:32647')
        self.assertTrue(set(np.unique(out)) <= {0, 1, 2, 253, 255})          # codes never interpolated
        self.assertTrue((out[:3, :3] == 0).all() and (out[:3, 3:6] == 1).all())
        self.assertTrue((out[3:6, :3] == 2).all() and (out[3:6, 3:6] == 253).all())
        self.assertTrue((out[6, :] == 255).all() and (out[:, 6] == 255).all())  # outside the reference -> invalid

    def test_confusion_counts_and_exclusions(self):
        from src.flood_validation import confusion, agreement_map
        pred = np.array([1, 1, 0, 0, 1, 0, 1], bool)
        pos = np.array([1, 0, 1, 0, 0, 0, 1], bool)
        neg = np.array([0, 1, 0, 1, 0, 0, 0], bool)                           # index 4, 5: neither (e.g. partial)
        valid = np.array([1, 1, 1, 1, 1, 1, 0], bool)                         # index 6: NISAR invalid
        m = confusion(pred, pos, neg, valid)
        self.assertEqual((m['TP'], m['FP'], m['FN'], m['TN'], m['invalid']), (1, 1, 1, 1, 3))
        self.assertAlmostEqual(m['precision'], 0.5); self.assertAlmostEqual(m['recall'], 0.5)
        self.assertAlmostEqual(m['F1'], 0.5); self.assertAlmostEqual(m['IoU'], 1 / 3)
        self.assertEqual(list(agreement_map(pred, pos, neg, valid)), [1, 2, 3, 4, 0, 0, 0])
        empty = confusion(np.zeros(3, bool), np.zeros(3, bool), np.ones(3, bool), np.ones(3, bool))
        self.assertIsNone(empty['precision']); self.assertIsNone(empty['F1'])

    def test_reference_new_water_excludes_partial_and_invalid(self):
        from src.flood_validation import reference_new_water
        pre = np.array([0, 0, 1, 0, 3, 255, 0])
        dur = np.array([1, 0, 1, 3, 1, 1, 251])
        pos, neg = reference_new_water(pre, dur, 'S1')
        self.assertEqual(list(pos), [True, False, False, False, False, False, False])
        self.assertEqual(list(neg), [False, True, True, False, False, False, False])

    def test_nisar_new_water_is_the_existing_classify(self):
        from src.flood_validation import nisar_new_water
        from src.water_change import classify
        rng = np.random.default_rng(3)
        prep = dict(HH=rng.uniform(-25, -5, (2, 30, 30)), HV=rng.uniform(-30, -10, (2, 30, 30)), valid=rng.random((30, 30)) > .1)
        classes, _ = classify(prep['HH'][0], prep['HH'][1], prep['valid'], -16.0, 3.0)
        self.assertTrue(np.array_equal(nisar_new_water(prep, 0, 1, 'HH', -16.0, None), classes == 2))

    def test_frozen_calibration_cannot_be_changed(self):
        import json, tempfile
        from pathlib import Path
        from src.flood_validation import frozen_thresholds, sha256, CALIBRATION
        self.assertEqual(frozen_thresholds(), (-10.0, -15.5))                 # the real frozen file
        self.assertEqual(sha256(CALIBRATION), '7a312b32400bfa47df10c45e1537f6ce55c2eed444f79c9f2ed207faadfd1b6e')
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'calibration.json'
            path.write_text(json.dumps(dict(frozen=dict(HH=-10.0, HV=-15.5))))
            path.with_suffix('.sha256').write_text(sha256(path) + '  calibration.json\n')
            self.assertEqual(frozen_thresholds(path), (-10.0, -15.5))
            path.write_text(json.dumps(dict(frozen=dict(HH=-12.0, HV=-15.5))))  # a test scene "retunes" it
            with self.assertRaises(ValueError):
                frozen_thresholds(path)

    def test_primary_configuration_is_the_untuned_default(self):
        import inspect
        from src import flood_validation as fv
        from src.water_change import classify
        self.assertEqual(dict(fv.PRIMARY_CONFIG), dict(variant='HH', t_HH=-16.0, min_change_db=3.0,
                                                       outcome='new open water', reference='S1'))
        defaults = inspect.signature(classify).parameters
        self.assertEqual(defaults['water_threshold'].default, dict(fv.PRIMARY_CONFIG)['t_HH'])
        self.assertEqual(defaults['min_change'].default, dict(fv.PRIMARY_CONFIG)['min_change_db'])
        self.assertEqual((fv.DEFAULT_HH, fv.MIN_CHANGE), (-16.0, 3.0))
        self.assertIsInstance(fv.PRIMARY_CONFIG, tuple)                       # immutable


class BootstrapTests(unittest.TestCase):
    def test_block_bootstrap_reproducible_and_brackets_estimate(self):
        from src.flood_validation import block_bootstrap, confusion
        rng = np.random.default_rng(0)
        truth = rng.random((200, 200)) < 0.3
        pred = truth ^ (rng.random((200, 200)) < 0.1)
        valid = np.ones((200, 200), bool)
        a = block_bootstrap(pred, truth, ~truth, valid, 20, n=200, seed=5)
        b = block_bootstrap(pred, truth, ~truth, valid, 20, n=200, seed=5)
        self.assertEqual(a, b)
        self.assertEqual(a['blocks'], 100)
        point = confusion(pred, truth, ~truth, valid)
        for k in ('precision', 'recall', 'F1', 'IoU'):
            self.assertLessEqual(a[k][0], point[k]); self.assertGreaterEqual(a[k][1], point[k])
        self.assertNotEqual(block_bootstrap(pred, truth, ~truth, valid, 20, n=200, seed=6), a)


class CoregistrationTests(unittest.TestCase):
    def test_detects_known_shift(self):
        from src.flood_validation import coregistration_offset
        rng = np.random.default_rng(1)
        base = rng.normal(-15, 3, (200, 200))
        from scipy.ndimage import gaussian_filter
        base = gaussian_filter(base, 2)
        shifted = np.roll(base, (3, -2), axis=(0, 1))
        valid = np.ones_like(base, bool)
        o = coregistration_offset(base, shifted, valid)
        self.assertAlmostEqual(o['row'], 3, delta=0.2); self.assertAlmostEqual(o['col'], -2, delta=0.2)
        self.assertLess(coregistration_offset(base, base, valid)['magnitude'], 0.1)
