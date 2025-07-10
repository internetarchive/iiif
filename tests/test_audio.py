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


    def test_spectrogram_waveforms(self):
        resp = self.test_app.get("/iiif/3/hhfbc-cyl26/manifest.json?recache=True")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json        

        for canvas in manifest['items']:
            self.assertTrue('seeAlso' in canvas)
            spectrogram = canvas['seeAlso'][0]
            self.assertEqual(spectrogram["format"], "image/png")
            self.assertEqual(spectrogram["label"]["en"][0], "Spectrogram")

            self.assertTrue('accompanyingCanvas' in canvas)
            accCanvas = canvas['accompanyingCanvas']
            self.assertEqual(accCanvas["type"], "Canvas")
            self.assertEqual(accCanvas["label"]["en"][0], "Waveform")
            self.assertTrue("height" in accCanvas)
            self.assertTrue("width" in accCanvas)