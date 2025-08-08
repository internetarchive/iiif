import os

import unittest
from flask.testing import FlaskClient
from iiify.app import app

class TestImages(unittest.TestCase):

    def setUp(self) -> None:
        app.config['CACHE_TYPE'] = "NullCache"
        self.test_app = FlaskClient(app)

    def test_v3_resolving(self):
        resp = self.test_app.get("/iiif/3/jewishinterpreta00morg$267/info.json")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual("https://iiif.archive.org/image/iiif/3/jewishinterpreta00morg%2fjewishinterpreta00morg_jp2.zip%2fjewishinterpreta00morg_jp2%2fjewishinterpreta00morg_0267.jp2/info.json", resp.location, "Expected to be redirected to full JSON URl.")

    def test_v2_resolving(self):
        resp = self.test_app.get("/iiif/2/jewishinterpreta00morg$267/info.json")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual("https://iiif.archive.org/image/iiif/2/jewishinterpreta00morg%2fjewishinterpreta00morg_jp2.zip%2fjewishinterpreta00morg_jp2%2fjewishinterpreta00morg_0267.jp2/info.json", resp.location, "Expected to be redirected to full JSON URl.")

    def test_annotation_id_is_not_annotationpage_id(self):
        resp = self.test_app.get("/iiif/3/Codex-Cuara/manifest.json?recache=true")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json
        anno_page_ids = []
        annotation_ids = []
        for canvas in manifest['items']:
            for anno_page in canvas['items']:
                anno_page_ids.append(anno_page.get('id'))
                for annotation in anno_page['items']:
                    annotation_ids.append(annotation.get('id'))
        
        self.assertEqual(len(anno_page_ids), len(set(anno_page_ids)),
                        "Some annotation page ids are duplicated")
        self.assertEqual(len(annotation_ids), len(set(annotation_ids)),
                        "Some annotation ids are duplicated")
        overlap = set(anno_page_ids) & set(annotation_ids)
        self.assertFalse(overlap, f"Some annotation ids are reused as annotation page ids: {overlap}")

        
