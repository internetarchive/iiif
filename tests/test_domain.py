import shutil
import tempfile
import unittest
from unittest.mock import patch

from flask.testing import FlaskClient
from iiify.app import app, cache, requested_domain

IDENTIFIER = "DontBeaS1947"
MANIFEST = f"/iiif/3/{IDENTIFIER}/manifest.json"
CANONICAL = f"https://iiif.archive.org/iiif/{IDENTIFIER}/manifest.json"

def fakeManifest(identifier, domain=None, page=None):
    """Stands in for create_manifest3, so these tests exercise routing and caching
    only - which domain reaches the builder, and what ends up under which key."""
    return {"id": f"{domain}{identifier}/manifest.json"}

def cachedViews():
    """Every cached route, derived from the url map so new ones are covered
    without anyone having to remember to add them here."""
    for rule in app.url_map.iter_rules():
        view = app.view_functions[rule.endpoint]
        if hasattr(view, 'uncached'):  # flask_caching marks its decorated views
            yield rule, view

class TestRequestedDomain(unittest.TestCase):

    def setUp(self) -> None:
        # flask_caching binds a FileSystemCache in ./cache at import time, so setting
        # CACHE_TYPE would be too late. Rebind at a throwaway directory instead, or
        # these tests read and overwrite the application's real cache.
        self.cache_dir = tempfile.mkdtemp()
        cache.init_app(app, config={'CACHE_TYPE': 'FileSystemCache',
                                    'CACHE_DIR': self.cache_dir})
        self.test_app = FlaskClient(app)

    def tearDown(self) -> None:
        shutil.rmtree(self.cache_dir, ignore_errors=True)
        # Leave the binding pointing somewhere that exists: the module-global cache
        # outlives this class, and later test modules would otherwise write into a
        # directory we just deleted.
        cache.init_app(app, config={'CACHE_TYPE': 'NullCache'})

    def assertNotPoisoned(self, attacker, host="iiif.archive.org"):
        """An attacker request must not change what the next plain caller is served.

        Asserts the victim was served *from cache* as well: without that, this
        passes with caching switched off entirely and proves nothing.
        """
        with patch("iiify.app.create_manifest3", side_effect=fakeManifest) as builder:
            self.test_app.get(attacker[0], headers={"Host": attacker[1]})
            builder.reset_mock()
            victim = self.test_app.get(MANIFEST, headers={"Host": host})
            self.assertEqual(victim.json['id'], CANONICAL,
                             f"cache poisoned by {attacker!r}")
            self.assertEqual(builder.call_count, 0,
                             "victim was rebuilt, so this never exercised the cache")

    def primeCache(self, host="iiif.archive.org"):
        with patch("iiify.app.create_manifest3", side_effect=fakeManifest):
            self.test_app.get(MANIFEST, headers={"Host": host})

    def test_unlisted_domain_is_ignored(self):
        with patch("iiify.app.create_manifest3", side_effect=fakeManifest):
            resp = self.test_app.get(f"{MANIFEST}?domain=https://evil.example/",
                                     headers={"Host": "iiif.archive.org"})
        self.assertEqual(resp.json['id'], CANONICAL)

    def test_allowed_domain_is_honoured(self):
        with patch("iiify.app.create_manifest3", side_effect=fakeManifest):
            resp = self.test_app.get(f"{MANIFEST}?domain=https://iiif.archive.org/",
                                     headers={"Host": "somewhere.example"})
        self.assertEqual(resp.json['id'], CANONICAL)

    def test_unlisted_domain_cannot_poison(self):
        self.primeCache()
        self.assertNotPoisoned((f"{MANIFEST}?domain=https://evil.example/", "iiif.archive.org"))

    def test_allowed_alternate_domain_cannot_poison(self):
        """An allowlisted domain is a legitimate answer for the caller who asked for
        it, and still must not become the answer everyone else gets."""
        self.primeCache()
        self.assertNotPoisoned(
            (f"{MANIFEST}?domain=https://iiif.archivelab.org/", "iiif.archive.org"))

    def test_host_header_cannot_poison(self):
        """The Host header reaches the body through request.url_root and is not in
        the default cache key - the same defect on a different input."""
        self.primeCache()
        self.assertNotPoisoned((MANIFEST, "evil.example"))

    def test_recache_cannot_poison(self):
        """?recache= is an amplifier, not the vector: it only removes the need to
        win the race after an entry expires."""
        self.primeCache()
        self.assertNotPoisoned(
            (f"{MANIFEST}?domain=https://evil.example/&recache=1", "iiif.archive.org"))

    def test_allowed_domain_is_rebuilt_not_echoed(self):
        """Validating the hostname while emitting the caller's whole string lets
        scheme, port, userinfo and path through - and a backslash past urlparse."""
        for hostile in (r"https://evil.example\@iiif.archive.org/",
                        "https://iiif.archive.org:1337/junk/",
                        "https://iiif.archive.org/../../evil/",
                        "https://user:pw@iiif.archive.org/x/",
                        "ftp://iiif.archive.org/",
                        "//iiif.archive.org/",
                        "https://IIIF.ARCHIVE.ORG/",
                        "https://iiif.archive.org./"):
            with self.subTest(domain=hostile):
                with app.test_request_context(f"{MANIFEST}?domain={hostile}",
                                              headers={"Host": "iiif.archive.org"}):
                    self.assertEqual(requested_domain(), "https://iiif.archive.org/iiif/")

    def test_every_cached_route_keys_on_the_domain_it_renders(self):
        """The structural guard. A cached response that varies on something the key
        ignores is this whole bug, so assert the two move together - for every
        cached route, including ones added after this was written."""
        variants = [("plain", "", "iiif.archive.org"),
                    ("alt-domain", "?domain=https://iiif.archivelab.org/", "iiif.archive.org"),
                    ("alt-host", "", "somewhere.example")]
        for rule, view in cachedViews():
            path = rule.build({arg: (1 if arg in ('page', 'canvas_no', 'version')
                                     else 'anIdentifier')
                               for arg in rule.arguments}, append_unknown=False)[1]
            keys, domains = {}, {}
            for label, query, host in variants:
                with app.test_request_context(path + query, headers={"Host": host}):
                    keys[label] = view.make_cache_key(use_request=True)
                    domains[label] = requested_domain()
            for other in ("alt-domain", "alt-host"):
                if domains["plain"] != domains[other]:
                    self.assertNotEqual(
                        keys["plain"], keys[other],
                        f"{rule}: body differs ({domains['plain']} vs {domains[other]}) "
                        f"but both cache under {keys['plain']}")

if __name__ == '__main__':
    unittest.main()
