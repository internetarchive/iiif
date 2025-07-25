import os

import unittest
from flask.testing import FlaskClient
from iiify.app import app
class TestCollections(unittest.TestCase):

    def setUp(self) -> None:
        app.config['CACHE_TYPE'] = "NullCache"
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
        self.assertEqual(resp.status_code, 200)

    def test_v3_collection_pages_proxy(self):
        resp = self.test_app.get("/iiif/frankbford/2/collection.json")
        self.assertEqual(resp.status_code, 200)

    def test_part_of(self):
        resp = self.test_app.get("/iiif/university_pittsburgh/collection.json")
        self.assertEqual(resp.status_code, 200)
        collection = resp.json
        self.assertEqual(len(collection['partOf']), 1, f"Expected 1 parent collection but got: {len(collection['partOf'])}")

    def test_sanitized_summary(self):
        resp = self.test_app.get("/iiif/terminal-escape-collection/collection.json")
        self.assertEqual(resp.status_code, 200)
        collection = resp.json
        self.assertEqual(
            collection['summary']['none'][0],
            """<p>TERMINAL ESCAPE. DAILY CASSETTE RIPS SINCE 2009. \"The wizard\" has been ripping and posting tapes daily on his <a href=\"https://terminalescape.blogspot.com/\" rel=\"noreferrer\">https://terminalescape.blogspot.com</a>&nbsp;blog since 2009. This massive collection covers DIY and underground releases from punk, hardcore, and all related and unrelated genre. There are both demos from contemporary bands and rare tapes, bootlegs, compilations, etc from his own personal collection, which is extensive due to his long-standing participation in undergound tape-trading scenes.<br>\n<br>\nPreviously all these tapes were uploaded to a variety of temporary upload sites and many of the older download links have gone dead (out of nearly 5000 posts since 2009, nearly 1500 are lost). This collection at the Internet Archive seeks to preserve these tape rips in a permanent home, alongside the wizard's commentary and reviews that accompanied each post.&nbsp;</p>""",
            f"Expected summary to be sanitized but got: {collection['summary']['none'][0]}"
        )
        

if __name__ == '__main__':
    unittest.main()