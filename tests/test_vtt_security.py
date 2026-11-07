import unittest
from tests.base import IIIFTestCase
from unittest.mock import patch

from flask.testing import FlaskClient
from iiify.app import app, cache

# A caption payload an attacker could plant in a remote .srt on archive.org.
XSS_PAYLOAD = "<script>alert('xss')</script>"


def mockJsonResponse(payload, text="", status_code=200):
    class MockResponse:
        def __init__(self):
            self.status_code = status_code
            self.text = text

        def json(self):
            return payload

        def raise_for_status(self):
            return

    return MockResponse()


def mockVttStream(identifier, srt_text):
    """requests.get stand-in: serves a /metadata response with one .mpg original
    (so there is a duration) and one .srt, and returns `srt_text` for the download.
    """
    metadata = {
        "files": [
            {"name": f"{identifier}.mpg", "source": "original", "length": "70.0"},
            {"name": f"{identifier}.srt", "source": "original"},
        ]
    }

    def mock_get(url, *args, **kwargs):
        if "/metadata/" in url:
            return mockJsonResponse(metadata)
        if "/download/" in url and url.split("?")[0].endswith(".srt"):
            return mockJsonResponse(None, text=srt_text)
        raise AssertionError(f"Unexpected request: {url}")

    return mock_get


class TestVttSecurity(IIIFTestCase):

    def setUp(self) -> None:
        cache.init_app(app, config={
                'CACHE_TYPE': 'NullCache',
                'CACHE_NO_NULL_WARNING': True})
        self.test_app = FlaskClient(app)

    @patch("requests.get")
    def test_vtt_stream_sets_nosniff_and_vtt_content_type(self, requestsGet):
        srt = "1\n00:00:01,000 --> 00:00:02,000\n%s\n" % XSS_PAYLOAD
        requestsGet.side_effect = mockVttStream("xss-item", srt)

        resp = self.test_app.get("/iiif/vtt/streaming/xss-item.vtt")

        self.assertEqual(resp.status_code, 200)
        # nosniff forbids the browser from re-interpreting the response as HTML.
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff",
                         "Expected X-Content-Type-Options: nosniff on the VTT response")
        # The content type is pinned to text/vtt with an explicit charset, so the
        # body is never served in an executable (text/html) context.
        self.assertEqual(resp.headers.get("Content-Type"), "text/vtt; charset=utf-8",
                         "Expected an explicit text/vtt; charset=utf-8 content type")
        self.assertNotIn("text/html", resp.headers.get("Content-Type", ""))
        # The payload still appears as inert VTT text (we neutralise via headers,
        # not by silently dropping the caption), but can no longer execute.
        self.assertIn(XSS_PAYLOAD, resp.text)

    @patch("requests.get")
    def test_valid_vtt_still_produced(self, requestsGet):
        srt = "1\n00:00:01,000 --> 00:00:02,000\nHELLO WORLD\n"
        requestsGet.side_effect = mockVttStream("good-item", srt)

        resp = self.test_app.get("/iiif/vtt/streaming/good-item.vtt")

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.text.startswith("WEBVTT"),
                        "Expected a well-formed WEBVTT body")
        self.assertIn("HELLO WORLD", resp.text)
        # Converted SRT comma timestamps to VTT dot timestamps.
        self.assertIn("00:00:01.000 --> 00:00:02.000", resp.text)


if __name__ == '__main__':
    unittest.main()
