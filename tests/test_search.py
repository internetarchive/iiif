import unittest
from flask.testing import FlaskClient
from iiify.app import app, cache
from iiify import search
import requests
from tests.mocks.mock_metadata import log_requests, mock_url

journal_metadata = mock_url("metadata", "tests/fixtures/metadata/journalofexpedit00ford.json")

class TestSearch(unittest.TestCase):

    def setUp(self) -> None:
        cache.init_app(app, config={'CACHE_TYPE': 'NullCache'})
        self.test_app = FlaskClient(app)

    @journal_metadata
    @mock_url("fulltext/inside.php","tests/fixtures/search/fulltext-search.json")
    def test_basic(self):
        resp = self.test_app.get("/iiif/search/journalofexpedit00ford/?q=Brunswick")
        self.assertEqual(resp.status_code, 200)
        results = resp.json    

        self.assertEqual(len(results["resources"]),2, "Expected two results for Brunswick")

    @journal_metadata
    @mock_url("info.json", "tests/fixtures/info/journalofexpedit00ford__ia_thumb.jpg.info.json")
    @mock_url("BookReaderJSIA.php", "tests/fixtures/bookreader/journalofexpedit00ford.json")
    def test_search_in_manifest(self):    
        resp = self.test_app.get("/iiif/3/journalofexpedit00ford/manifest.json")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json    

        self.assertTrue("service" in manifest, "Failed to find search service in manifest")
        self.assertEqual(len(manifest['service']), 1, "Expected a single search service")
        service = manifest['service'][0]
        self.assertEqual(service['@id'], "https://localhost/iiif/search/journalofexpedit00ford")
        self.assertEqual(service['@type'], "SearchService1")
        self.assertEqual(service['profile'], "http://iiif.io/api/search/1/search")


    @mock_url("fulltext/inside.php", "tests/fixtures/search/fulltext-search.json")
    @journal_metadata
    def test_fixture(self):
        resp = self.test_app.get("/iiif/search/journalofexpedit00ford/?q=Brunswick")
        self.assertEqual(resp.status_code, 200)
        results = resp.json    

        self.assertEqual(len(results["resources"]),2, "Expected two results for Brunswick")

        result1 = results["resources"][0]
        self.assertEqual(result1["on"], "https://iiif.archive.org/iiif/journalofexpedit00ford$5/canvas#xywh=1338,2851,337,44", "Canvas id or bounding box is wrong")

    @journal_metadata
    def test_search_url(self):
        self.assertEqual(search.build_search_url("journalofexpedit00ford", "query"), "https://ia601302.us.archive.org/fulltext/inside.php?item_id=journalofexpedit00ford&doc=journalofexpedit00ford&path=/31/items/journalofexpedit00ford&q=query", "Unexpected search query")

    @mock_url("fulltext/inside.php", "tests/fixtures/search/2_boxes.json")
    @journal_metadata
    def test_multi_box(self):
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

    @mock_url("fulltext/inside.php", "tests/fixtures/search/multi_word.json")
    @journal_metadata
    def test_multi_word(self):
        resp = self.test_app.get("/iiif/search/journalofexpedit00ford/?q=pleasure to observe")
        self.assertEqual(resp.status_code, 200)
        results = resp.json    

        self.assertEqual(len(results["resources"]),7, "Expected seven results for 'pleasure to observe' fixture")
        results = results["resources"]

        self.assertEqual(results[0]["resource"]["chars"], "to", "Unexpected search match")
        self.assertEqual(results[1]["resource"]["chars"], "pleasure", "Unexpected search match")
        self.assertEqual(results[2]["resource"]["chars"], "to", "Unexpected search match")
        self.assertEqual(results[3]["resource"]["chars"], "observe", "Unexpected search match")

    # Although the metadata fixture doesn't match the item searched for
    # below it shouldn't matter for this test
    @mock_url("fulltext/inside.php", "tests/fixtures/search/missmatch.json")
    @journal_metadata
    def test_search_missing_r(self):
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


    @journal_metadata
    @mock_url("fulltext/inside.php","tests/fixtures/search/fulltext-search.json")
    def test_matching_characters_not_empty(self):
        resp = self.test_app.get("/iiif/search/journalofexpedit00ford/?q=Brunswick")
        results = resp.json
        for result in results["resources"]:
            self.assertTrue(isinstance(result, dict))
            self.assertEqual(result["resource"]["chars"], "Brunswick")

    @mock_url("metadata", "tests/fixtures/metadata/gray-diary.json")
    @mock_url("fulltext/inside.php", "tests/fixtures/search/Houston.json")
    def test_real_gray_diary_item(self):
        """Test that doc parameter matches the original filename minus extension"""
        result = search.build_search_url('gray-diary', 'Houston')

        self.assertIn('item_id=gray-diary', result)
        self.assertIn('doc=GrayDiary', result)
        self.assertIn('q=Houston', result)

        response = requests.get(result)
        self.assertEqual(response.status_code, 200)
