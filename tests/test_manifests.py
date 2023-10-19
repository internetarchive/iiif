import unittest
from flask.testing import FlaskClient
from iiify.app import app

class TestManifests(unittest.TestCase):

    def setUp(self) -> None:
        self.test_app = FlaskClient(app)


    def test_no_version(self):
        resp = self.test_app.get("/iiif/rashodgson68/manifest.json")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.location, '/iiif/3/rashodgson68/manifest.json')

    def test_ident(self):
        resp = self.test_app.get("/iiif/3/img-8664_202009/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json
        self.assertEqual(manifest['id'], 'http://localhost/iiif/3/img-8664_202009/manifest.json', 'Unexpected identifier')

    def test_v3_image_manifest(self):
        resp = self.test_app.get("/iiif/3/rashodgson68/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(manifest['type'], "Manifest", f"Unexpected type. Expected Manifest go {manifest['type']}")
        self.assertEqual(len(manifest['items']),32,f"Expected 32 canvases but got: {len(manifest['items'])}")

    def test_v3_single_image_manifest(self):
        resp = self.test_app.get("/iiif/3/img-8664_202009/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(manifest['type'], "Manifest", f"Unexpected type. Expected Manifest go {manifest['type']}")
        self.assertEqual(len(manifest['items']),1,f"Expected 1 canvas but got: {len(manifest['items'])}")

    def test_v3_single_text_manifest(self):
        resp = self.test_app.get("/iiif/3/fbf_3chords_1_/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(manifest['type'], "Manifest", f"Unexpected type. Expected Manifest go {manifest['type']}")
        self.assertEqual(len(manifest['items']),1,f"Expected 1 canvas but got: {len(manifest['items'])}")


    def test_v3_vermont_Life_Magazine(self):
        resp = self.test_app.get("/iiif/3/rbmsbk_ap2-v4_2001_V55N4/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(len(manifest['items']),116,f"Expected 116 canvas but got: {len(manifest['items'])}")

    def test_v3_single_video_manifest(self):
        resp = self.test_app.get("/iiif/3/youtube-7w8F2Xi3vFw/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(len(manifest['items']),1,f"Expected 1 canvas but got: {len(manifest['items'])}")

    #logic to cover etree mediatype github issue #123
    def test_v3_etree_mediatype(self):
        resp = self.test_app.get("/iiif/3/gd72-04-14.aud.vernon.23662.sbeok.shnf/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(len(manifest['items']),36,f"Expected 36 canvases but got: {len(manifest['items'])}")
        self.assertEqual(manifest['items'][0]['items'][0]['items'][0]['body']['items'][0]['type'],"Sound",f"Expected 'Sound' but got: {manifest['items'][0]['items'][0]['items'][0]['body']['items'][0]['type']}")


    def test_v3_64Kbps_MP3(self):
        resp = self.test_app.get("/iiif/3/TvQuran.com__Alafasi/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json
        self.assertEqual(len(manifest['items']),114,f"Expected 114 canvases but got: {len(manifest['items'])}")
        self.assertEqual("64Kbps MP3".lower() in resp.text.lower(), True, f"Expected the string '64Kbps MP3'")


    def test_v3_128Kbps_MP3(self):
        resp = self.test_app.get("/iiif/3/alice_in_wonderland_librivox/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json
        self.assertEqual(len(manifest['items']),12,f"Expected 12 canvases but got: {len(manifest['items'])}")
        self.assertEqual("128kbps mp3".lower() in resp.text.lower(), True, f"Expected the string '128kbps mp3'")

    def test_v3_h264_MPEG4_OGG_Theora(self):
        resp = self.test_app.get("/iiif/3/taboca_201002_03/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json
        self.assertEqual(len(manifest['items']),251,f"Expected 251 canvases but got: {len(manifest['items'])}")
        self.assertEqual("h.264 MPEG4".lower() in resp.text.lower(), True, f"Expected the string 'h.264 MPEG4'")
        self.assertEqual("OGG Theora".lower() in resp.text.lower(), True, f"Expected the string 'OGG Theora'")

    def test_v3_aiff(self):
        resp = self.test_app.get("/iiif/3/PDextend_AIFF/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json
        self.assertEqual(len(manifest['items']),38,f"Expected 38 canvases but got: {len(manifest['items'])}")
        self.assertEqual("AIFF".lower() in resp.text.lower(), True, f"Expected the string 'AIFF'")

    def test_provider_logo(self):
        resp = self.test_app.get("/iiif/3/rashodgson68/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json
        self.assertEqual(manifest['provider'][0]['homepage'][0]['id'] == "https://archive.org", True, f"Expected 'https://archive.org' but got {manifest['provider'][0]['id']}")
        self.assertEqual(manifest['provider'][0]['logo'][0]['id'] == "https://archive.org/images/glogo.png", True, f"Expected logo URI but got {manifest['provider'][0]['logo'][0]['id']}")

    def test_page_behavior(self):
        resp = self.test_app.get("/iiif/3/rbmsbk_ap2-v4_2001_V55N4/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json
        self.assertEqual(len(manifest['items']),116,f"Expected 116 canvas but got: {len(manifest['items'])}")
        self.assertEqual(manifest['viewingDirection'],"left-to-right",f"Expected 'left-to-right' canvas but got: {manifest['viewingDirection']}")
        self.assertEqual(manifest['behavior'][0],"paged",f"Expected 'paged' but got: {manifest['behavior'][0]}")

    def test_page_behavior_r_to_l(self):
        resp = self.test_app.get("/iiif/3/nybc314063/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json
        self.assertEqual(len(manifest['items']),544,f"Expected 544 canvas but got: {len(manifest['items'])}")
        self.assertEqual(manifest['viewingDirection'],"right-to-left",f"Expected 'right-to-left' canvas but got: {manifest['viewingDirection']}")
        self.assertEqual(manifest['behavior'][0],"paged",f"Expected 'paged' but got: {manifest['behavior'][0]}")



''' to test:
kaled_jalil (no derivatives)
Dokku_obrash (geo-restricted?)
m4a filetypes (No length to files?)
'''

if __name__ == '__main__':
    unittest.main()