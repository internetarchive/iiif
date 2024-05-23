import unittest
from flask.testing import FlaskClient
from iiify.app import app

class TestManifests(unittest.TestCase):

    def setUp(self) -> None:
        self.test_app = FlaskClient(app)

    def test_v2_image_manifest(self):
        resp = self.test_app.get("/iiif/2/rashodgson68/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(manifest['@id'], 'https://localhost/iiif/rashodgson68/manifest.json', 'V2 Manifest ID is using new infrastructure changed')
        self.assertEqual(manifest['@type'], "sc:Manifest", f"Unexpected type. Expected Manifest got {manifest['@type']}")
        self.assertEqual(len(manifest['sequences'][0]['canvases']),32,f"Expected 32 canvases but got: {len(manifest['sequences'][0]['canvases'])}")
        self.assertEqual(manifest['sequences'][0]['canvases'][0]['@id'],"https://iiif.archivelab.org/iiif/rashodgson68$0/canvas",f"v2 canvas id has changed")


    def test_v2_image_api(self):
        resp = self.test_app.get("/iiif/2/1991-12-compute-magazine/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(manifest['@id'], 'https://localhost/iiif/1991-12-compute-magazine/manifest.json', 'V2 Manifest ID is using new infrastructure changed')
        image = manifest['sequences'][0]['canvases'][0]['images'][0]['resource']
        self.assertEqual(image['@id'], "https://localhost/iiif/1991-12-compute-magazine$0/full/full/0/default.jpg", "Resource not using new image server")
        self.assertEqual(image['service']['@id'], 'https://localhost/iiif/1991-12-compute-magazine$0', "V2 service not using the new image server")


    def test_text_which_is_image(self):
        resp = self.test_app.get("/iiif/2/fbf_3chords_1_/manifest.json")

        self.assertEqual(resp.status_code, 200)