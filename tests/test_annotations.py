import os

import json
import shutil
import tempfile
import unittest
from unittest.mock import patch
from flask.testing import FlaskClient
from iiify.app import app, cache

class TestAnnotations(unittest.TestCase):

    def setUp(self) -> None:
        app.config['CACHE_TYPE'] = "NullCache"
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
        annotationList = annotations['items']
        self.assertEqual(annotations['type'], "AnnotationPage", "Unexpected type, expected AnnotationPage")
        self.assertEqual(len(annotationList), 6, "Unexpected number of annotations")

        ids = []
        first=True
        for anno in annotationList:
            self.assertTrue(anno['id'] not in ids,f"Duplicate ID: {anno['id']}")
            ids.append(anno['id'])
            self.assertEqual(anno['type'], "Annotation", "Expected type of Annotation")
            self.assertTrue("body" in anno and "target" in anno, f"Body or target missing from annotation {anno}")
            self.assertEqual(anno['body']['type'], "TextualBody", "Expected body to be a TextualBody")
            self.assertEqual(anno['body']['format'], "text/plain", "Expected format to be a text/plain")
            self.assertEqual(anno['target'].split('#')[0], "https://iiif.archive.org/iiif/journalofexpedit00ford$0/canvas")
            if first:
                self.assertEqual(anno['target'].split('#')[1],"xywh=592,1742,460,118")
                self.assertEqual(anno['body']['value'],"JOURNAL ")

            self.assertEqual(anno['motivation'], "supplementing", "Expected motivation of supplementing")
            first=False

    def test_review_annotations_on_manifest(self):
        resp = self.test_app.get(
            "/iiif/3/goodytwoshoes00newyiala/manifest.json?recache=true"
        )
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json
        self.assertEqual(len(manifest['annotations']), 1)
        self.assertEqual(manifest["annotations"][0]["type"], "AnnotationPage")


def reviewsFixture(**changes):
    with open("tests/fixtures/metadata/goodytwoshoes00newyiala.json") as handle:
        metadata = json.load(handle)
    metadata.update(changes)
    return metadata


def mockMetadata(metadata):
    """A requests.get stand-in serving `metadata`.

    Anything else raises, so an accidental live call fails loudly rather than
    quietly putting the network back under the test.
    """
    def mock_get(url, *args, **kwargs):
        if "/metadata/" in url:
            class MockResponse:
                status_code = 200

                def json(self):
                    return metadata

                def raise_for_status(self):
                    return

            return MockResponse()
        raise AssertionError(f"Unexpected request while building comments: {url}")

    return mock_get


class TestReviewAnnotations(unittest.TestCase):
    """Reviews are user-generated and arrive whenever a reader writes one, so the
    count of them is not a property of this code. Asserting the live number meant
    the suite went red on someone else's book review: it was bumped 37 -> 38 in
    66feca4 and the item was already on 41 the same day. The fixture is the real
    /metadata response for goodytwoshoes00newyiala reduced to its `reviews` array,
    which is the only key create_annotations_from_comments reads.
    """

    def setUp(self) -> None:
        # flask_caching binds a FileSystemCache in ./cache at import time, so setting
        # CACHE_TYPE here is too late. Without rebinding, a response cached from a
        # previous live run is replayed and the test passes without ever reaching
        # the fixture.
        self.cache_dir = tempfile.mkdtemp()
        cache.init_app(app, config={'CACHE_TYPE': 'FileSystemCache',
                                    'CACHE_DIR': self.cache_dir})
        self.test_app = FlaskClient(app)

    def tearDown(self) -> None:
        shutil.rmtree(self.cache_dir, ignore_errors=True)
        # Restore the application's own cache rather than leaving a NullCache
        # behind, which would silently disable caching for every later module.
        cache.init_app(app, config={'CACHE_TYPE': 'FileSystemCache',
                                    'CACHE_DIR': 'cache'})

    @patch("requests.get")
    def test_review_annotations(self, requestsGet):
        metadata = reviewsFixture()
        requestsGet.side_effect = mockMetadata(metadata)

        resp = self.test_app.get(
            "/iiif/3/annotations/goodytwoshoes00newyiala/comments.json"
        )
        annotations = resp.json
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(annotations['@context'], "http://iiif.io/api/presentation/3/context.json","Unexpected context")
        self.assertEqual(annotations['type'], "AnnotationPage", "Unexpected type, expected AnnotationPage")
        self.assertEqual(len(annotations['items']), 41, "Unexpected number of annotations")
        ids = []
        for anno in annotations['items']:
            self.assertEqual(anno['type'], "Annotation", "Expected type of Annotation")
            self.assertTrue("body" in anno and "target" in anno, f"Body or target missing from annotation {anno}")
            self.assertTrue(anno['id'] not in ids, f"Duplicate ID: {anno['id']}")
            ids.append(anno['id'])
            self.assertEqual(anno['body']['format'], "text/html", "Expected format to be a text/html")
            self.assertEqual(anno['motivation'], "commenting", "Expected motivation of commenting")

        # A count alone would still pass if every review rendered as the same empty
        # span, so pin the review -> annotation mapping to the fixture's content.
        first = metadata['reviews'][0]
        self.assertEqual(
            annotations['items'][0]['body']['value'],
            f"<span><p>{first['reviewtitle']}:</p><p>{first['reviewbody']}</p></span>")
        self.assertEqual(
            annotations['items'][0]['target'],
            "https://localhost/iiif/3/goodytwoshoes00newyiala/manifest.json")

    @patch("requests.get")
    def test_review_annotations_tracks_the_item(self, requestsGet):
        """The page follows the item's reviews rather than a number baked in here."""
        metadata = reviewsFixture()
        metadata['reviews'] = metadata['reviews'][:5]
        requestsGet.side_effect = mockMetadata(metadata)

        resp = self.test_app.get(
            "/iiif/3/annotations/goodytwoshoes00newyiala/comments.json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json['items']), 5)

    @patch("requests.get")
    def test_review_annotations_with_no_reviews(self, requestsGet):
        """An item nobody has reviewed is an empty page, not a crash."""
        requestsGet.side_effect = mockMetadata(reviewsFixture(reviews=[]))

        resp = self.test_app.get(
            "/iiif/3/annotations/goodytwoshoes00newyiala/comments.json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['items'], [])
