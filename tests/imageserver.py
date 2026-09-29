"""Stub for the Cantaloupe image server.

Several manifest tests are not about thumbnails at all, but every manifest build
fetches an `info.json` from `cantaloupe.prod.archive.org` to size them. That makes
those tests fail whenever the image server is unwell — which is what happened on
2026-09-25, when Cantaloupe began timing out and took six tests down with it.

Wrap such a test in `@without_image_server` so it exercises the code it names and
not the availability of a separate service. Item metadata still comes from the live
API; only the image server is replaced.
"""
import functools
import requests
from unittest.mock import patch

def _canned_info(url):
    class MockResponse:
        status_code = 200
        def json(self):
            return {
                "@context": "http://iiif.io/api/image/2/context.json",
                "@id": url[:-len("/info.json")],
                "protocol": "http://iiif.io/api/image",
                "profile": ["http://iiif.io/api/image/2/level2.json"],
                "width": 320,
                "height": 240,
            }

        def raise_for_status(self):
            return

    return MockResponse()

def without_image_server(test):
    """Serve image-server `info.json` from a canned response; pass everything else through."""
    @functools.wraps(test)
    def wrapper(*args, **kwargs):
        live = requests.get

        def dispatch(url, *a, **kw):
            if url.endswith("info.json"):
                return _canned_info(url)
            return live(url, *a, **kw)

        with patch("requests.get", side_effect=dispatch):
            return test(*args, **kwargs)

    return wrapper
