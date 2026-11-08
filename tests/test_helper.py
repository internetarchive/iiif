import os
os.environ["FLASK_CACHE_DISABLE"] = "true"

from tests.base import IIIFTestCase
from flask.testing import FlaskClient
from iiify.app import app, cache

from tests.mocks.mock_metadata import log_requests, mock_urls

class TestHelper(IIIFTestCase):

    def setUp(self) -> None:
        cache.init_app(app, config={
                'CACHE_TYPE': 'NullCache',
                'CACHE_NO_NULL_WARNING': True})
        self.test_app = FlaskClient(app)

    @mock_urls
    def test_single_image(self):
        resp = self.test_app.get("/iiif/helper/img-8664_202009/")
        self.assertEqual(resp.status_code, 200)

        self.assertIn('<a href="https://projectmirador.org/embed/?iiif-content=https://iiif.archive.org/iiif/img-8664_202009/manifest.json">', resp.text, "Couldn't find Mirador link in helper page.")

    @mock_urls
    def test_collection(self):
        resp = self.test_app.get("/iiif/helper/frankbford/")
        self.assertEqual(resp.status_code, 200)

        self.assertIn('<a href="https://projectmirador.org/embed/?iiif-content=https://iiif.archive.org/iiif/frankbford/collection.json">', resp.text, "Couldn't find Mirador link in helper page.")