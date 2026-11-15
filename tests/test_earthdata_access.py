"""Offline security tests only; these are not NASA data-access results."""

import io
import unittest
from unittest.mock import patch

from scripts.check_earthdata_access import AccessCheckError, open_product_range


class Response:
    def __init__(self, status, location=None):
        self.status_code = status
        self.headers = {"Location": location} if location else {}
        self.raw = io.BytesIO()
        self.closed = False

    def close(self):
        self.closed = True


class RedirectTests(unittest.TestCase):
    origin = "https://nisar.asf.earthdatacloud.nasa.gov/NISAR/example.h5"
    s3 = "https://sds-n-cumulus-prod-nisar-products.s3.us-west-2.amazonaws.com/example.h5?signature=private"

    @patch("scripts.check_earthdata_access.requests.get")
    def test_observed_nisar_cloudfront_redirect(self, get):
        cdn = "https://d1mv8zhcvry6x4.cloudfront.net/example.h5?Signature=private"
        get.side_effect = [Response(303, cdn), Response(206)]
        entry = {}
        result = open_product_range(self.origin, "test-secret", entry)
        self.assertEqual(result.status_code, 206)
        self.assertEqual(get.call_count, 2)
        request = get.call_args_list[1]
        self.assertEqual(request.args[0], cdn)
        self.assertNotIn("Authorization", request.kwargs["headers"])
        self.assertEqual(request.kwargs["headers"]["Range"], "bytes=0-7")
        self.assertNotIn("private", str(entry))
        self.assertNotIn("test-secret", str(entry))

    @patch("scripts.check_earthdata_access.requests.get")
    def test_other_cloudfront_distribution_is_blocked(self, get):
        get.return_value = Response(303, "https://other.cloudfront.net/example.h5")
        with self.assertRaisesRegex(AccessCheckError, "approved HTTPS"):
            open_product_range(self.origin, "test-secret", {})
        self.assertEqual(get.call_count, 1)

    @patch("scripts.check_earthdata_access.requests.get")
    def test_303_data_redirect_strips_token_keeps_range(self, get):
        redirect, final = Response(303, self.s3), Response(206)
        get.side_effect = [redirect, final]
        entry = {}
        result = open_product_range(self.origin, "test-secret", entry)
        self.assertIs(result, final)
        self.assertTrue(redirect.closed)
        initial, follow = get.call_args_list
        self.assertEqual(initial.kwargs["headers"]["Authorization"], "Bearer test-secret")
        self.assertNotIn("Authorization", follow.kwargs["headers"])
        self.assertEqual(follow.kwargs["headers"]["Range"], "bytes=0-7")
        self.assertTrue(follow.kwargs["stream"])
        self.assertFalse(follow.kwargs["allow_redirects"])
        self.assertNotIn("private", str(entry))
        self.assertNotIn("test-secret", str(entry))

    @patch("scripts.check_earthdata_access.requests.get")
    def test_login_redirect_is_not_followed(self, get):
        get.return_value = Response(303, "https://urs.earthdata.nasa.gov/oauth/authorize?code=private")
        with self.assertRaisesRegex(AccessCheckError, "Earthdata Login"):
            open_product_range(self.origin, "test-secret", {})
        self.assertEqual(get.call_count, 1)
        self.assertTrue(get.return_value.closed)

    @patch("scripts.check_earthdata_access.requests.get")
    def test_unapproved_or_insecure_redirects_are_not_requested(self, get):
        for target in ("https://example.com/file.h5", "http://nisar.asf.earthdatacloud.nasa.gov/file.h5"):
            with self.subTest(target=target):
                get.reset_mock()
                get.return_value = Response(303, target)
                with self.assertRaisesRegex(AccessCheckError, "approved HTTPS"):
                    open_product_range(self.origin, "test-secret", {})
                self.assertEqual(get.call_count, 1)

    @patch("scripts.check_earthdata_access.requests.get")
    def test_redirect_loop_is_bounded(self, get):
        get.side_effect = lambda *a, **k: Response(303, self.origin)
        with self.assertRaisesRegex(AccessCheckError, "limit"):
            open_product_range(self.origin, "test-secret", {})
        self.assertEqual(get.call_count, 6)

    @patch("scripts.check_earthdata_access.requests.get")
    def test_ignored_range_body_is_not_read(self, get):
        get.return_value = Response(200)
        result = open_product_range(self.origin, "test-secret", {})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.raw.tell(), 0)


if __name__ == "__main__":
    unittest.main()
