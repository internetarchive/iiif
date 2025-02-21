import os
os.environ["FLASK_CACHE_DISABLE"] = "true"

import unittest
from flask.testing import FlaskClient
from iiify.app import app

class TestHelper(unittest.TestCase):

    def setUp(self) -> None:
        self.test_app = FlaskClient(app)

    def test_single_image(self):
        resp = self.test_app.get("/iiif/helper/img-8664_202009/")
        self.assertEqual(resp.status_code, 200)

        self.assertIn('<a href="https://projectmirador.org/embed/?iiif-content=https://iiif.archive.org/iiif/img-8664_202009/manifest.json">Mirador</a>', resp.text, "Couldn't find Mirador link in helper page.")

    def test_collection(self):
        resp = self.test_app.get("/iiif/helper/frankbford/")
        self.assertEqual(resp.status_code, 200)

        self.assertIn('<a href="https://projectmirador.org/embed/?iiif-content=https://iiif.archive.org/iiif/frankbford/collection.json">Mirador</a>', resp.text, "Couldn't find Mirador link in helper page.")