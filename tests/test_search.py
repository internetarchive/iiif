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
        app.config['CACHE_TYPE'] = "NullCache"
        self.test_app = FlaskClient(app)

    def test_live(self):
        resp = self.test_app.get("/iiif/search/journalofexpedit00ford/?q=Brunswick")
        self.assertEqual(resp.status_code, 200)
        results = resp.json    

        self.assertEqual(len(results["resources"]),2, "Expected two results for Brunswick")

    def test_search_in_manifest(self):    
        resp = self.test_app.get("/iiif/3/journalofexpedit00ford/manifest.json?recache=true")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json    

        self.assertTrue("service" in manifest, "Failed to find search service in manifest")
        self.assertEqual(len(manifest['service']), 1, "Expected a single search service")
        service = manifest['service'][0]
        self.assertEqual(service['@id'], "https://localhost/iiif/search/journalofexpedit00ford")
        self.assertEqual(service['@type'], "SearchService1")
        self.assertEqual(service['profile'], "http://iiif.io/api/search/1/search")


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

    @patch("requests.get")
    def multi_box(self, searchPatch):
        # Define mock response for the specific URLs
        def mock_response(url, *args, **kwargs):
            if "fulltext/inside.php" in url:
                return mockResponse("tests/fixtures/search/missmatch.json")
            elif "metadata" in url:
                # Although this doesn't match the item used in the 
                # search above it shouldn't matter for this test
                return mockResponse("tests/fixtures/metadata/journalofexpedit00ford.json")

        searchPatch.side_effect = mock_response    

        resp = self.test_app.get("/iiif/search/mrr_401/?q=top")
        self.assertEqual(resp.status_code, 200)
        results = resp.json        

        # this doesn't have the r field in the box:
        anno5 = results["resources"][4]
        self.assertEqual(anno5['on'], "https://iiif.archive.org/iiif/mrr_401$78/canvas#xywh=3650,2284,1044,67")
        anno1 = results["resources"][0]
        # First anno should use the IA_FTS_MATCH
        self.assertEqual(anno1["resource"]["chars"], "TOP")
        # The rest should use the query 
        for anno in results["resources"][1:]:
            self.assertEqual(anno["resource"]["chars"], "top")


    def test_matching_characters_not_empty(self):
        resp = self.test_app.get("/iiif/search/journalofexpedit00ford/?q=Brunswick")
        results = resp.json
        for result in results["resources"]:
            self.assertTrue(isinstance(result, dict))
            self.assertEqual(result["resource"]["chars"], "Brunswick")    