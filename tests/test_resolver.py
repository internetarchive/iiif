import os

import unittest
from tests.base import IIIFTestCase
from iiify.resolver import purify_domain, collection, manifest_page
from iiify.app import app, cache

from tests.mocks.mock_metadata import log_requests, mock_urls

class TestResolver(IIIFTestCase):
    def setUp(self) -> None:
        cache.init_app(app, config={
                'CACHE_TYPE': 'NullCache',
                'CACHE_NO_NULL_WARNING': True})

    # Doesn't call any external URLs
    def test_purify(self):
        domain = purify_domain("https://example.org/iiif/")
        self.assertEqual(domain, "https://example.org/iiif/")
        domain = purify_domain("https://example.org/test/")
        self.assertEqual(domain, "https://example.org/test/iiif/")

    # Doesn't call any external URLs
    def test_collection(self):
        coll = collection(domain="https://example.org/", identifiers=["1", "2", "3"])
        self.assertIsInstance(coll, dict)
        self.assertEqual(coll["@id"], "https://example.org/collection.json")
        self.assertEqual(len(coll["collections"]), 3)
        self.assertEqual(coll["collections"][0]["@id"], "https://example.org/1/manifest.json")

    # Doesn't call any external URLs
    def test_manifest_page(self):
        mani = manifest_page(identifier="https://example.org/1", label="p1", width=100, height=100)
        self.assertEqual(mani["@id"], "https://example.org/1/canvas")
        self.assertEqual(mani['label'], 'p1')
        self.assertEqual(mani["images"][0]["@id"], "https://example.org/1/annotation")
        self.assertEqual(mani["images"][0]["resource"]["@id"], "https://example.org/1/full/full/0/default.jpg")
        self.assertEqual(mani["images"][0]["resource"]["height"], 100)


if __name__ == '__main__':
    unittest.main()
