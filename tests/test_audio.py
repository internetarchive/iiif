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

    def test_multi_track_audio_gets_ranges(self):
        resp = self.test_app.get("/iiif/Weirdos_demo-1978/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(len(manifest["structures"]), 1, f"Expected a top level range to serve as the track list but got {len(manifest['items'])}")
        self.assertEqual(manifest["structures"][0]["label"]["none"][0], "Track List", f"Expected a top level range to be labeled 'Track List' but got {manifest["structures"][0]["label"]["none"][0]}")
        self.assertEqual(len(manifest["structures"][0]["items"]), 15, f"Expected 15 tracks but got {len(manifest["structures"][0]["items"])}")
    
    def test_single_track_audio_gets_no_ranges(self):
        resp = self.test_app.get("/iiif/2021-04-06/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertNotIn("structures", manifest, "Expected single file audio to have no structures or ranges.")
