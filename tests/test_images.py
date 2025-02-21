import os

import unittest
from flask.testing import FlaskClient
from iiify.app import app

class TestImages(unittest.TestCase):

    def setUp(self) -> None:
        os.environ["FLASK_CACHE_DISABLE"] = "true"
        self.test_app = FlaskClient(app)

    def test_v3_resolving(self):
        resp = self.test_app.get("/iiif/3/jewishinterpreta00morg$267/info.json")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual("https://iiif.archive.org/image/iiif/3/jewishinterpreta00morg%2fjewishinterpreta00morg_jp2.zip%2fjewishinterpreta00morg_jp2%2fjewishinterpreta00morg_0267.jp2/info.json", resp.location, "Expected to be redirected to full JSON URl.")

    def test_v2_resolving(self):
        resp = self.test_app.get("/iiif/2/jewishinterpreta00morg$267/info.json")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual("https://iiif.archive.org/image/iiif/2/jewishinterpreta00morg%2fjewishinterpreta00morg_jp2.zip%2fjewishinterpreta00morg_jp2%2fjewishinterpreta00morg_0267.jp2/info.json", resp.location, "Expected to be redirected to full JSON URl.")



