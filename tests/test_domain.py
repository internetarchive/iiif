import shutil
import tempfile
import unittest
from unittest.mock import patch

from flask.testing import FlaskClient
from iiify.app import app, cache

IDENTIFIER = "DontBeaS1947"
MANIFEST = f"/iiif/3/{IDENTIFIER}/manifest.json"

def fakeManifest(identifier, domain=None, page=None):
    """Stands in for create_manifest3 so these tests exercise routing and caching
    only - what domain reaches the builder, and what ends up cached."""
    return {"id": f"{domain}{identifier}/manifest.json"}

class TestRequestedDomain(unittest.TestCase):

    def setUp(self) -> None:
        # flask_caching binds a FileSystemCache in ./cache at import time, so point it
        # at a throwaway directory rather than the application's real cache.
        self.cache_dir = tempfile.mkdtemp()
        cache.init_app(app, config={'CACHE_TYPE': 'FileSystemCache',
                                    'CACHE_DIR': self.cache_dir})
        self.test_app = FlaskClient(app)

    def tearDown(self) -> None:
        shutil.rmtree(self.cache_dir, ignore_errors=True)

    @patch("iiify.app.create_manifest3", side_effect=fakeManifest)
    def test_unlisted_domain_is_ignored(self, _manifest):
        resp = self.test_app.get(f"{MANIFEST}?domain=https://evil.example/")
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("evil.example", resp.text)
        self.assertIn("localhost", resp.json['id'], "Expected a fallback to the request host")

    @patch("iiify.app.create_manifest3", side_effect=fakeManifest)
    def test_allowed_domain_is_honoured(self, _manifest):
        resp = self.test_app.get(f"{MANIFEST}?domain=https://iiif.archive.org/")
        self.assertEqual(resp.json['id'],
                         f"https://iiif.archive.org/iiif/{IDENTIFIER}/manifest.json")

    @patch("iiify.app.create_manifest3", side_effect=fakeManifest)
    def test_domain_cannot_poison_the_cached_response(self, _manifest):
        """The regression this guards.

        Flask-Caching keys on the path, not the query string. Before the fix, one
        anonymous request carrying a hostile ?domain= stored a response under the key
        that plain requests read, for as long as the entry lived.
        """
        self.test_app.get(f"{MANIFEST}?domain=https://evil.example/")
        victim = self.test_app.get(MANIFEST)
        self.assertNotIn("evil.example", victim.text,
                         "A cached response was poisoned by an earlier request's ?domain=")

    @patch("iiify.app.create_manifest3", side_effect=fakeManifest)
    def test_recache_cannot_poison_the_cached_response(self, _manifest):
        """?recache= is an amplifier, not the vector - it only removes the need to
        win the race after an entry expires. Both paths must be closed."""
        self.test_app.get(MANIFEST)
        self.test_app.get(f"{MANIFEST}?domain=https://evil.example/&recache=1")
        victim = self.test_app.get(MANIFEST)
        self.assertNotIn("evil.example", victim.text)

    @patch("iiify.app.create_manifest3", side_effect=fakeManifest)
    def test_schemeless_domain_is_ignored(self, _manifest):
        resp = self.test_app.get(f"{MANIFEST}?domain=evil.example")
        self.assertNotIn("evil.example", resp.text)

if __name__ == '__main__':
    unittest.main()
