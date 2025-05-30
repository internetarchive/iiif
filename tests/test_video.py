import os

import unittest
import math
from flask.testing import FlaskClient
from iiify.app import app

class TestVideo(unittest.TestCase):

    def setUp(self) -> None:
        app.config['CACHE_TYPE'] = "NullCache"
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

    def test_vtt_autogenerated(self):
        resp = self.test_app.get("/iiif/3/youtube-SvH4fbjOT0A/manifest.json?recache=true")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        self.assertEqual(len(manifest['items']),1,f"Expected 1 canvas but got: {len(manifest['items'])}")
        self.assertTrue('annotations' in manifest['items'][0], "Expected annotations in manifest")
        self.assertTrue(isinstance(manifest['items'][0]['annotations'], list), "Expected annotations to be a list")
        self.assertEqual(len(manifest['items'][0]['annotations']), 1, "Expected 1 item in annotations")
        annotationPage = manifest['items'][0]['annotations'][0]
        self.assertEqual(annotationPage['type'], 'AnnotationPage', "Expected annotations to contain annotation page")

        self.assertTrue('items' in annotationPage and isinstance(annotationPage['items'],list) and len(annotationPage['items']) == 1, f"Expected annotation page to contain a list of items which contains 1 item. Found {annotationPage['items']}")
        annotation = annotationPage['items'][0]
        self.assertEqual(annotation['type'], 'Annotation', "Expected annotationPage to contain annotations")
        self.assertEqual(annotation['motivation'], 'supplementing', "Expected annotation to have the supplementing annotation")
        self.assertTrue('body' in annotation, "Expected annotation to have a body")
        body = annotation['body']
        self.assertEqual(body['type'],'Text', "Expected body to have a type text")
        self.assertEqual(body['format'],'text/vtt', "Expected body to have a type text")
        self.assertEqual(body['label']['en'][0], "autogenerated", "Expected VTT file to have the label autogenerated")
        self.assertFalse("language" in body, "We don't know the language for this item so there shouldn't be a language specified")
        self.assertEqual(body['id'], "https://localhost/iiif/resource/youtube-SvH4fbjOT0A/34C3_-_International_Image_Interoperability_Framework_IIIF_Kulturinstitutionen_schaffen_interop-SvH4fbjOT0A.autogenerated.vtt","Unexpected URL for the VTT file")

    def test_vtt_multilingual(self):
        resp = self.test_app.get("/iiif/3/cruz-test/manifest.json?recache=true")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        canvas = manifest['items'][0]
        self.assertTrue('annotations' in canvas, 'Expected annotations in Canvas')
        self.assertEqual(len(canvas['annotations']), 1, 'Expected one AnnotationPage')
        annotations = canvas['annotations'][0]['items']
        self.assertEqual(len(annotations), 104, 'Expected all 104 langues')

        # Check welsh
        for item in annotations:
            self.assertTrue('language' in item['body'], f"All vtt files should have a language: {item}")
            if item['body']['language'] == 'cy':
                self.assertEqual(item['body']['id'], 'https://localhost/iiif/resource/cruz-test/cruz-test.cy.vtt', 'Unexpected link for the Welsh vtt file')

    def test_newsitem(self):
        resp = self.test_app.get("/iiif/3/CSPAN3_20180217_164800_Poplar_Forest_Archaeology/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json

        canvas = manifest['items'][0]
        annoPages = canvas['items'][0]
        annotations = annoPages['items']
        self.assertEqual(len(annotations), math.floor(780.89 / 60), 'Expected the video to contain the 13min video split into 1 minute segments')

        # Check vtt file
        self.assertTrue('annotations' in canvas, "Expected canvas to have annotations")
        vttFile = canvas['annotations'][0]['items'][0]['body']['id']
        self.assertTrue(vttFile.endswith("/iiif/vtt/streaming/CSPAN3_20180217_164800_Poplar_Forest_Archaeology.vtt"),f"Expected vttFile to be located at /iiif/vtt/streaming/CSPAN3_20180217_164800_Poplar_Forest_Archaeology.vtt but found it at {vttFile}")

        resp = self.test_app.get("/iiif/vtt/streaming/CSPAN3_20180217_164800_Poplar_Forest_Archaeology.vtt")
        checkLine=False
        for line in resp.text.split("\n"):
            if checkLine:
                self.assertEqual("00:01:02.000 --> 00:01:03.000", line, "Expected the timecode to be over a minute as its the second video")
                break    
            if line.startswith("28"):
                checkLine=True
        # 28
        # 00:01:02.000 -> 00:01:02.000
        # I AM THE DIRECTOR OF ARCHAEOLOGY



if __name__ == '__main__':
    unittest.main()