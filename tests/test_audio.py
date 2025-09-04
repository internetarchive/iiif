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
            self.assertTrue("height" in accCanvas and accCanvas["height"] == 200)
            self.assertTrue("width" in accCanvas and accCanvas["width"] == 800)


        # Test mime types
        body = manifest["items"][0]["items"][0]["items"][0]["body"]["items"]

        for item in body:
            name = item['id']
            format = item['format']   
            if name.endswith(".mp3"):
                self.assertEqual(format, "audio/mpeg", f"Unexpected mimetype for {name}")
            elif name.endswith(".flac"):
                self.assertEqual(format, "audio/flac", f"Unexpected mimetype for {name}")
            elif name.endswith(".ogg"):
                self.assertEqual(format, "audio/ogg", f"Unexpected mimetype for {name}")
            elif name.endswith(".wav"):
                self.assertEqual(format, "audio/x-wav", f"Unexpected mimetype for {name}")

    def test_multi_track_audio_gets_ranges(self):
        resp = self.test_app.get("/iiif/Weirdos_demo-1978/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(len(manifest["structures"]), 1, f"Expected a top level range to serve as the track list but got {len(manifest['items'])}")
        self.assertEqual(manifest["structures"][0]["label"]["en"][0], "Track List", f"Expected a top level range to be labeled 'Track List' but got {manifest["structures"][0]["label"]["en"][0]}")
        self.assertEqual(len(manifest["structures"][0]["items"]), 15, f"Expected 15 tracks but got {len(manifest["structures"][0]["items"])}")
    
    def test_single_track_audio_gets_no_ranges(self):
        resp = self.test_app.get("/iiif/2021-04-06/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertNotIn("structures", manifest, "Expected single file audio to have no structures or ranges.")

