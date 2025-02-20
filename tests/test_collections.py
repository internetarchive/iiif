import os

import unittest
from flask.testing import FlaskClient
from iiify.app import app
class TestCollections(unittest.TestCase):

    def setUp(self) -> None:
        os.environ["FLASK_ENV"] = "testing"
        self.test_app = FlaskClient(app)

    def test_v3_collection(self):
        resp = self.test_app.get("/iiif/3/frankbford/collection.json")
        self.assertEqual(resp.status_code, 200)
        collection = resp.json

        self.assertEqual(collection['type'], "Collection", f"Unexpected type. Expected collection got {collection['type']}")
        self.assertEqual(len(collection['items']),1001,f"Expected 1001 items but got: {len(collection['items'])}")
        self.assertEqual(collection['items'][-1]['type'],'Collection',"Expected last item to be a collection pointing to the next set of results")

    def test_v3_collection_pages(self):
        resp = self.test_app.get("/iiif/3/frankbford/2/collection.json")
        self.assertEqual(resp.status_code, 200)

    def test_collections_proxy(self):
        resp = self.test_app.get("/iiif/frankbford/collection.json")
        print(resp.status_code)
        self.assertEqual(resp.status_code, 200)

    def test_v3_collection_pages_proxy(self):
        resp = self.test_app.get("/iiif/frankbford/2/collection.json")
        self.assertEqual(resp.status_code, 200)

def test_v3_collection_detection(self):
        resp = self.test_app.get("/iiif/frankbford/manifest.json")
        self.assertEqual(resp.status_code, 302)

if __name__ == '__main__':
    unittest.main()