import os

import unittest
from unittest.mock import patch
from flask.testing import FlaskClient
from iiify.app import app
from iiify import search
import json
import requests

def mockResponse(fixture):
    class MockResponse:
        status_code = 200
        def json(self):
            with open(fixture, "r") as file:
                return json.load(file)

        def raise_for_status(self):
            return        

    return MockResponse()

class TestSearch(unittest.TestCase):

    def setUp(self) -> None:
        os.environ["FLASK_CACHE_DISABLE"] = "true"
        self.test_app = FlaskClient(app)

    def test_live(self):
        resp = self.test_app.get("/iiif/search/journalofexpedit00ford/?q=Brunswick")
        self.assertEqual(resp.status_code, 200)
        results = resp.json    

        self.assertEqual(len(results["resources"]),2, "Expected two results for Brunswick")

    @patch("requests.get")
    def test_fixture(self, searchPatch):
            # Define mock response for the specific URLs
            def mock_response(url, *args, **kwargs):
                if "fulltext/inside.php" in url:
                    return mockResponse("tests/fixtures/search/fulltext-search.json")
                elif "metadata" in url:
                    return mockResponse("tests/fixtures/metadata/journalofexpedit00ford.json")

            searchPatch.side_effect = mock_response    

            resp = self.test_app.get("/iiif/search/journalofexpedit00ford/?q=Brunswick")
            self.assertEqual(resp.status_code, 200)
            results = resp.json    

            self.assertEqual(len(results["resources"]),2, "Expected two results for Brunswick")

            result1 = results["resources"][0]
            self.assertEqual(result1["on"], "https://iiif.archive.org/iiif/journalofexpedit00ford$5/canvas#xywh=1338,2851,337,44", "Canvas id or bounding box is wrong")

    @patch("requests.get")
    def test_search_url(self,metadataPatch):
         # Define mock response for the specific URLs
        def mock_response(url, *args, **kwargs):
            return mockResponse("tests/fixtures/metadata/journalofexpedit00ford.json")

        metadataPatch.side_effect = mock_response
    
        self.assertEqual(search.buildSearchURL("journalofexpedit00ford", "query"), "https://ia601302.us.archive.org/fulltext/inside.php?item_id=journalofexpedit00ford&doc=journalofexpedit00ford&path=/31/items/journalofexpedit00ford&q=query", "Unexpected search query")

    @patch("requests.get")
    def multi_box(self, searchPatch):
        # Define mock response for the specific URLs
        def mock_response(url, *args, **kwargs):
            if "fulltext/inside.php" in url:
                return mockResponse("tests/fixtures/search/2_boxes.json")
            elif "metadata" in url:
                return mockResponse("tests/fixtures/metadata/journalofexpedit00ford.json")

        searchPatch.side_effect = mock_response    

        resp = self.test_app.get("/iiif/search/journalofexpedit00ford/?q=much")
        self.assertEqual(resp.status_code, 200)
        results = resp.json    

        self.assertEqual(len(results["resources"]),3, "Expected three results for 'much' fixture.")

        results = results["resources"]

        # Just a single results
        self.assertEqual(results[0]["resource"]["chars"], "much", "Unexpected search match")
        self.assertEqual(results[0]["on"], "https://iiif.archive.org/iiif/journalofexpedit00ford$6/canvas#xywh=271,682,154,41", "Canvas or box is incorrect")

        # Second result from search but should result in two annotations:
        self.assertEqual(results[1]["resource"]["chars"], "much", "Unexpected search match")
        self.assertEqual(results[1]["on"], "https://iiif.archive.org/iiif/journalofexpedit00ford$6/canvas#xywh=1479,1451,159,42", "Canvas or box is incorrect")

        self.assertEqual(results[2]["resource"]["chars"], "much", "Unexpected search match")
        self.assertEqual(results[2]["on"], "https://iiif.archive.org/iiif/journalofexpedit00ford$6/canvas#xywh=1336,1520,171,42", "Canvas or box is incorrect")

    @patch("requests.get")
    def multi_word(self, searchPatch):    
        # Define mock response for the specific URLs
        def mock_response(url, *args, **kwargs):
            if "fulltext/inside.php" in url:
                return mockResponse("tests/fixtures/search/multi_word.json")
            elif "metadata" in url:
                return mockResponse("tests/fixtures/metadata/journalofexpedit00ford.json")

        searchPatch.side_effect = mock_response    

        resp = self.test_app.get("/iiif/search/journalofexpedit00ford/?q=pleasure to observe")
        self.assertEqual(resp.status_code, 200)
        results = resp.json    

        self.assertEqual(len(results["resources"]),7, "Expected seven results for 'pleasure to observe' fixture")
        results = results["resources"]

        self.assertEqual(results[0]["resource"]["chars"], "to", "Unexpected search match")
        self.assertEqual(results[1]["resource"]["chars"], "pleasure", "Unexpected search match")
        self.assertEqual(results[2]["resource"]["chars"], "to", "Unexpected search match")
        self.assertEqual(results[3]["resource"]["chars"], "observe", "Unexpected search match")