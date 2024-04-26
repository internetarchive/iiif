import unittest
from flask.testing import FlaskClient
from iiify.app import app

class TestVideo(unittest.TestCase):

    def setUp(self) -> None:
        self.test_app = FlaskClient(app)

    def test_v3_single_video_manifest(self):
        resp = self.test_app.get("/iiif/3/youtube-7w8F2Xi3vFw/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(len(manifest['items']),1,f"Expected 1 canvas but got: {len(manifest['items'])}")   

    def test_v3_h264_MPEG4_OGG_Theora(self):
        resp = self.test_app.get("/iiif/3/taboca_201002_03/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json
        self.assertEqual(len(manifest['items']),251,f"Expected 251 canvases but got: {len(manifest['items'])}")
        self.assertEqual("h.264 MPEG4".lower() in resp.text.lower(), True, f"Expected the string 'h.264 MPEG4'")
        self.assertEqual("OGG Theora".lower() in resp.text.lower(), True, f"Expected the string 'OGG Theora'")

if __name__ == '__main__':
    unittest.main()