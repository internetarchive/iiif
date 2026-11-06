import os

import unittest
from flask.testing import FlaskClient
from iiify.app import app, cache
from tests.mocks.mock_metadata import log_requests, mock_urls

class TestBasic(unittest.TestCase):

    def setUp(self) -> None:
        cache.init_app(app, config={'CACHE_TYPE': 'NullCache'})
        self.test_app = FlaskClient(app)

    def test_documentation(self):
        resp = self.test_app.get("/iiif/documentation")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text[:15], "<!doctype html>")


if __name__ == '__main__':
    unittest.main()
