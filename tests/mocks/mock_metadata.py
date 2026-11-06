import json
from functools import wraps
from unittest.mock import patch

import requests


# A part of a URL that identifies it, and the fixture to serve for it. Parts are
# matched against the URL as @log_requests prints it, so spaces appear as %20.
KNOWN_URLS = {
    # Metadata
    "/metadata/journalofexpedit00ford": "tests/fixtures/metadata/journalofexpedit00ford.json",
    "/metadata/gray-diary": "tests/fixtures/metadata/gray-diary.json",
    "/metadata/mrr_401": "tests/fixtures/metadata/mrr_401.json",
    "/metadata/goodytwoshoes00newyiala": "tests/fixtures/metadata/goodytwoshoes00newyiala.json",

    # Image info
    "journalofexpedit00ford%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/journalofexpedit00ford__ia_thumb.jpg.info.json",
    "goodytwoshoes00newyiala%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/goodytwoshoes00newyiala__ia_thumb.jpg.info.json",

    # BookReader
    "BookReaderJSIA.php?id=journalofexpedit00ford": "tests/fixtures/bookreader/journalofexpedit00ford.json",
    "BookReaderJSIA.php?id=goodytwoshoes00newyiala": "tests/fixtures/bookreader/goodytwoshoes.json",

    # Full text search, identified by the search term
    "journalofexpedit00ford&q=Brunswick": "tests/fixtures/search/fulltext-search.json",
    "journalofexpedit00ford&q=much": "tests/fixtures/search/2_boxes.json",
    "journalofexpedit00ford&q=pleasure%20to%20observe": "tests/fixtures/search/multi_word.json",
    "mrr_401&q=top": "tests/fixtures/search/missmatch.json",
    "gray-diary&q=Houston": "tests/fixtures/search/Houston.json",

    # Files:
    "journalofexpedit00ford_djvu.xml": "tests/fixtures/files/journalofexpedit00ford_djvu.xml"
}


def mockResponse(fixture):
    class MockResponse:
        status_code = 200

        @property
        def content(self):
            with open(fixture, "rb") as file:
                return file.read()

        @property
        def text(self):
            return self.content.decode("utf-8")

        def json(self):
            with open(fixture, "r") as file:
                return json.load(file)

        def raise_for_status(self):
            return

    return MockResponse()


def prepared_url(method, url, kwargs):
    return requests.Request(method, url, params=kwargs.get("params")).prepare().url


def find_fixture(url):
    matches = [part for part in KNOWN_URLS if part in url]
    if not matches:
        raise RuntimeError(f"URL not found in registry please add a fixture for: {url}")
    if len(matches) > 1:
        raise RuntimeError(
            f"{url} matches more than one KNOWN_URLS entry: {matches}. "
            "Make those URL parts more specific."
        )
    return KNOWN_URLS[matches[0]]


def mock_urls(test):
    """Answer every HTTP request made while `test` runs from KNOWN_URLS.

    This covers requests.get and calls made through a requests.Session. A URL
    that doesn't match exactly one entry raises a RuntimeError that fails the test.
    """
    @wraps(test)
    def wrapper(*args, **kwargs):
        errors = []

        def fake_request(session, method, url, *args, **kwargs):
            try:
                return mockResponse(find_fixture(prepared_url(method, url, kwargs)))
            except RuntimeError as error:
                errors.append(error)
                raise

        with patch("requests.Session.request", fake_request):
            try:
                return test(*args, **kwargs)
            finally:
                # Flask turns the exception into a 500, and resolver.py has bare
                # excepts that could hide it completely, so raise it again here.
                if errors:
                    raise errors[0]

    return wrapper


def log_requests(test):
    """Print the URL of every HTTP request made while `test` runs.

    Use this to work out which fixtures a test needs. On its own, requests still
    go to the network. To use it with @mock_urls, put it below @mock_urls: it then
    prints each request and @mock_urls answers it. Placed above, it prints nothing.
    """
    @wraps(test)
    def wrapper(*args, **kwargs):
        # Look this up per run so a @mock_urls above this decorator still applies.
        next_request = requests.Session.request

        def logging_request(session, method, url, *args, **kwargs):
            print(f"[{test.__name__}] {method.upper()} {prepared_url(method, url, kwargs)}")
            return next_request(session, method, url, *args, **kwargs)

        with patch("requests.Session.request", logging_request):
            return test(*args, **kwargs)

    return wrapper
