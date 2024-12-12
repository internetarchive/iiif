import os

import unittest
from flask.testing import FlaskClient
from iiify.app import app

class TestAnnotations(unittest.TestCase):

    def setUp(self) -> None:
        os.environ["FLASK_CACHE_DISABLE"] = "true"
        self.test_app = FlaskClient(app)

    def test_v3_manifest_has_annotations(self):
        resp = self.test_app.get("/iiif/3/journalofexpedit00ford/manifest.json?recache=true")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json    

        count = 1
        for canvas in manifest['items']:
            self.assertTrue('annotations' in canvas, f"Expected annotations in canvas {canvas['id']}")
            annotations_url = f"https://localhost/iiif/3/annotations/journalofexpedit00ford/journalofexpedit00ford_djvu.xml/{count}.json"
            found=False
            for anno in canvas['annotations']:
                if anno['id'] == annotations_url:
                    found=True
                self.assertFalse('items' in anno, "As a referenced AnnotationPage it shouldn't contain items.")     
                self.assertTrue('type' in anno and anno['type'] == "AnnotationPage",f"Expected annotation page to have a type {anno}")

            self.assertTrue(found, f"Expected to find {annotations_url} in {canvas['annotations']}")   
            count += 1

    def test_v3_annotations(self):
        resp = self.test_app.get("/iiif/3/annotations/journalofexpedit00ford/journalofexpedit00ford_djvu.xml/1.json?recache=true")
        self.assertEqual(resp.status_code, 200)
        annotations = resp.json   

        self.assertEqual(annotations['id'], "https://localhost/iiif/3/annotations/journalofexpedit00ford/journalofexpedit00ford_djvu.xml/1.json", "Unexpected id")
        self.assertEqual(annotations['@context'], "http://iiif.io/api/presentation/3/context.json", "Unexpected context")
        self.assertEqual(annotations['type'], "AnnotationPage", "Unexpected type, expected AnnotationPage")
        annotationList = annotations['items']
        self.assertEqual(len(annotationList), 6, "Unexpected number of annotations")

        ids = []
        first=True
        for anno in annotationList:
            self.assertTrue(anno['id'] not in ids,"Duplicate ID: {anno['id']}")
            ids.append(anno['id'])
            self.assertEqual(anno['type'], "Annotation", "Expected type of Annotation")
            self.assertTrue("body" in anno and "target" in anno, "Body or target missing from annotation {anno}")
            self.assertEqual(anno['body']['type'], "TextualBody", "Expected body to be a TextualBody")
            self.assertEqual(anno['body']['format'], "text/plain", "Expected format to be a text/plain")
            self.assertEqual(anno['target'].split('#')[0], "https://iiif.archive.org/iiif/journalofexpedit00ford$0/canvas")
            if first:
                self.assertEqual(anno['target'].split('#')[1],"xywh=592,1742,460,118")
                self.assertEqual(anno['body']['value'],"JOURNAL ")

            self.assertEqual(anno['motivation'], "supplementing", "Expected motivation of supplementing")
            first=False

            