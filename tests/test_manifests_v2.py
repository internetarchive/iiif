import os

import unittest
from flask.testing import FlaskClient
from iiify.app import app

class TestManifests(unittest.TestCase):

    def setUp(self) -> None:
        app.config['CACHE_TYPE'] = "NullCache"
        self.test_app = FlaskClient(app)

    def test_v2_image_manifest(self):
        resp = self.test_app.get("/iiif/2/rashodgson68/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(manifest['@id'], 'https://localhost/iiif/2/rashodgson68/manifest.json', 'V2 Manifest ID is using new infrastructure changed')
        self.assertEqual(manifest['@type'], "sc:Manifest", f"Unexpected type. Expected Manifest got {manifest['@type']}")
        self.assertEqual(len(manifest['sequences'][0]['canvases']),32,f"Expected 32 canvases but got: {len(manifest['sequences'][0]['canvases'])}")
        self.assertEqual(manifest['sequences'][0]['canvases'][0]['@id'],"https://iiif.archivelab.org/iiif/rashodgson68$0/canvas",f"v2 canvas id has changed")


    def test_v2_image_api(self):
        resp = self.test_app.get("/iiif/2/1991-12-compute-magazine/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(manifest['@id'], 'https://localhost/iiif/2/1991-12-compute-magazine/manifest.json', 'V2 Manifest ID is using new infrastructure changed')
        image = manifest['sequences'][0]['canvases'][0]['images'][0]['resource']
        self.assertEqual(image['@id'], "https://iiif.archive.org/image/iiif/2/1991-12-compute-magazine%2fCompute_Issue_136_1991_Dec_jp2.zip%2fCompute_Issue_136_1991_Dec_jp2%2fCompute_Issue_136_1991_Dec_0000.jp2/full/full/0/default.jpg", "Resource not using new image server")
        self.assertEqual(image['service']['@id'], 'https://iiif.archive.org/image/iiif/2/1991-12-compute-magazine%2fCompute_Issue_136_1991_Dec_jp2.zip%2fCompute_Issue_136_1991_Dec_jp2%2fCompute_Issue_136_1991_Dec_0000.jp2', "V2 service not using the new image server")

    def test_v2_single_image(self):
        resp = self.test_app.get("/iiif/2/img-8664_202009/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(manifest['@id'], 'https://localhost/iiif/2/img-8664_202009/manifest.json', 'V2 Manifest ID is using new infrastructure changed')
        canvas = manifest['sequences'][0]['canvases'][0]
        self.assertEqual(canvas['@id'], 'https://iiif.archivelab.org/iiif/img-8664_202009/canvas', 'Expected canvas id to be the same')
        image = canvas['images'][0]['resource']
        self.assertEqual(image['@id'], "https://iiif.archive.org/image/iiif/2/img-8664_202009%2FIMG_8664.jpg/full/full/0/default.jpg", "Resource not using new image server")
        self.assertEqual(image['service']['@id'], 'https://iiif.archive.org/image/iiif/2/img-8664_202009%2FIMG_8664.jpg', "V2 service not using the new image server")

    def test_v2_single_text_manifest(self):
        resp = self.test_app.get("/iiif/2/fbf_3chords_1_/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(manifest['@id'], 'https://localhost/iiif/2/fbf_3chords_1_/manifest.json', 'V2 Manifest ID is using new infrastructure changed')
        canvas = manifest['sequences'][0]['canvases'][0]
        self.assertEqual(canvas['@id'], 'https://iiif.archivelab.org/iiif/fbf_3chords_1_$0/canvas', 'Expected canvas id to be the same')
        image = canvas['images'][0]['resource']
        self.assertEqual(image['@id'], "https://iiif.archive.org/image/iiif/2/fbf_3chords_1_%2f3chords(1)_jp2.zip%2f3chords(1)_jp2%2f3chords(1)_0000.jp2/full/full/0/default.jpg", "Resource not using new image server")
        self.assertEqual(image['service']['@id'], 'https://iiif.archive.org/image/iiif/2/fbf_3chords_1_%2f3chords(1)_jp2.zip%2f3chords(1)_jp2%2f3chords(1)_0000.jp2', "V2 service not using the new image server")


    def test_text_which_is_image(self):
        resp = self.test_app.get("/iiif/2/fbf_3chords_1_/manifest.json")

        self.assertEqual(resp.status_code, 200)

    def test_brokenv2(self):
        resp = self.test_app.get("/iiif/2/opencontext-41-nippur-excavation-units/manifest.json")

        self.assertEqual(resp.status_code, 200)    
        manifest = resp.json
        imgSrv = manifest['sequences'][0]['canvases'][0]['images'][0]['resource']['service']

        # Check using the correct url 
        # "https://iiif.archive.org/image/iiif/2
        self.assertTrue(imgSrv['@id'].startswith("https://iiif.archive.org/image/iiif/2"),"Expected v2 image service to use cantaloupe")

