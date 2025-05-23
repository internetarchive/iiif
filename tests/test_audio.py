import os

import unittest
import math
from flask.testing import FlaskClient
from iiify.app import app

class TestAudio(unittest.TestCase):

    def setUp(self) -> None:
        app.config['CACHE_TYPE'] = "NullCache"
        self.test_app = FlaskClient(app)

    def test_audio_no_derivatives(self):
        resp = self.test_app.get("/iiif/3/kaled_jalil/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(len(manifest['items']),114,f"Expected 114 canvases but got: {len(manifest['items'])}") 