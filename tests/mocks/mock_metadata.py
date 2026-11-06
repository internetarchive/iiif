import json
from functools import wraps
from unittest.mock import patch

import requests


# A part of a URL that identifies it, and the fixture to serve for it. Parts are
# matched against the URL as @log_requests prints it, so spaces appear as %20.
KNOWN_URLS = {
    # Search
    "/metadata/journalofexpedit00ford": "tests/fixtures/metadata/journalofexpedit00ford.json",
    "/metadata/gray-diary": "tests/fixtures/metadata/gray-diary.json",
    "/metadata/mrr_401": "tests/fixtures/metadata/mrr_401.json",
    # Annotations 
    "/metadata/goodytwoshoes00newyiala": "tests/fixtures/metadata/goodytwoshoes00newyiala.json",
    # Audio
    "/metadata/kaled_jalil": "tests/fixtures/metadata/kaled_jalil.json",
    "/metadata/hhfbc-cyl26": "tests/fixtures/metadata/hhfbc-cyl26.json",
    "/metadata/Weirdos_demo-1978": "tests/fixtures/metadata/Weirdos_demo-1978.json",
    "/metadata/2021-04-06": "tests/fixtures/metadata/2021-04-06.json",
    # Cantaloupe resolver
    "/metadata/img-8664_202009": "tests/fixtures/metadata/img-8664_202009.json",
    "/metadata/wg35-2-388": "tests/fixtures/metadata/wg35-2-388.json",
    "/metadata/pennsylvaniavege14penn": "tests/fixtures/metadata/pennsylvaniavege14penn.json",
    "/metadata/mobot31753002307400": "tests/fixtures/metadata/mobot31753002307400.json",
    "/metadata/opencontext-10-1998fig2tr52late-wall-west-face": "tests/fixtures/metadata/opencontext-10-1998fig2tr52late-wall-west-face.json",
    "/metadata/v52n2gullv52ngold": "tests/fixtures/metadata/v52n2gullv52ngold.json",
    "/metadata/erzhlungen00kleigoog": "tests/fixtures/metadata/erzhlungen00kleigoog.json",
    "/metadata/1994harlequinducksurreicrich": "tests/fixtures/metadata/1994harlequinducksurreicrich.json",
    "/metadata/CAT31108226": "tests/fixtures/metadata/CAT31108226.json",
    "/metadata/CAT31151811": "tests/fixtures/metadata/CAT31151811.json",
    "/metadata/opencontext-22-e-2-203-4-1-p-3jpg": "tests/fixtures/metadata/opencontext-22-e-2-203-4-1-p-3jpg.json",
    "/metadata/footmouthdisease00reyn": "tests/fixtures/metadata/footmouthdisease00reyn.json",
    "/metadata/drug-use-and-abuse-collection-of-pamphlets": "tests/fixtures/metadata/drug-use-and-abuse-collection-of-pamphlets.json",
    "/metadata/engflowergarden00robirich": "tests/fixtures/metadata/engflowergarden00robirich.json",
    # Collections
    "/metadata/frankbford": "tests/fixtures/metadata/frankbford.json",
    "/metadata/university_pittsburgh": "tests/fixtures/metadata/university_pittsburgh.json",
    "/metadata/terminal-escape-collection": "tests/fixtures/metadata/terminal-escape-collection.json",
    "/metadata/usgs_tx": "tests/fixtures/metadata/usgs_tx.json",
    # images
    "/metadata/jewishinterpreta00morg": "tests/fixtures/metadata/jewishinterpreta00morg.json",
    "/metadata/Codex-Cuara": "tests/fixtures/metadata/Codex-Cuara.json",
    # Links
    "/metadata/DuckandC1951": "tests/fixtures/metadata/DuckandC1951.json",

    # Image info
    "journalofexpedit00ford%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/journalofexpedit00ford__ia_thumb.jpg.info.json",
    "goodytwoshoes00newyiala%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/goodytwoshoes00newyiala__ia_thumb.jpg.info.json",
    "2/hhfbc-cyl26%2FFlandersFairbanks_thumb.jpg/info.json":"tests/fixtures/info/hhfbc-cyl26FlandersFairbanks_thumb.jpg.info.json",
    "2/Weirdos_demo-1978%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/Weirdos_demo-1978__ia_thumb.jpg.info.json",
    "2021-04-06%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/2021-04-06__ia_thumb.jpg.info.json",
    "Codex-Cuara%2F00000031.tif/info.json": "tests/fixtures/info/Codex-Cuara00000031.tif.info.json",
    "Codex-Cuara%2F00000036.tif/info.json": "tests/fixtures/info/Codex-Cuara00000036.tif.info.json",
    "Codex-Cuara%2F00000038.tif/info.json": "tests/fixtures/info/Codex-Cuara00000038.tif.info.json",
    "Codex-Cuara%2F00000039.tif/info.json": "tests/fixtures/info/Codex-Cuara00000039.tif.info.json",
    "Codex-Cuara%2F00000040.tif/info.json": "tests/fixtures/info/Codex-Cuara00000040.tif.info.json",
    "Codex-Cuara%2F00000043.tif/info.json": "tests/fixtures/info/Codex-Cuara00000043.tif.info.json",
    "Codex-Cuara%2F00000045.tif/info.json": "tests/fixtures/info/Codex-Cuara00000045.tif.info.json",
    "Codex-Cuara%2F00000047.tif/info.json": "tests/fixtures/info/Codex-Cuara00000047.tif.info.json",
    "Codex-Cuara%2F00000050.tif/info.json": "tests/fixtures/info/Codex-Cuara00000050.tif.info.json",
    "Codex-Cuara%2F00000051.tif/info.json": "tests/fixtures/info/Codex-Cuara00000051.tif.info.json",
    "Codex-Cuara%2F00000053.tif/info.json": "tests/fixtures/info/Codex-Cuara00000053.tif.info.json",
    "Codex-Cuara%2F00000054.tif/info.json": "tests/fixtures/info/Codex-Cuara00000054.tif.info.json",
    "Codex-Cuara%2FCuara,%20Co%CC%81dice%20leaf%201r.tif/info.json": "tests/fixtures/info/Codex-CuaraCuara,%20Co%CC%81dice%20leaf%201r.tif.info.json",
    "Codex-Cuara%2FCuara,%20Co%CC%81dice%20leaf10r.tif/info.json": "tests/fixtures/info/Codex-CuaraCuara,%20Co%CC%81dice%20leaf10r.tif.info.json",
    "Codex-Cuara%2FCuara,%20Co%CC%81dice%20leaf1v.tif/info.json": "tests/fixtures/info/Codex-CuaraCuara,%20Co%CC%81dice%20leaf1v.tif.info.json",
    "Codex-Cuara%2FCuara,%20Co%CC%81dice%20leaf7r.tif/info.json": "tests/fixtures/info/Codex-CuaraCuara,%20Co%CC%81dice%20leaf7r.tif.info.json",
    "Codex-Cuara%2FCuara,%20Co%CC%81dice%20leaf8r.tif/info.json": "tests/fixtures/info/Codex-CuaraCuara,%20Co%CC%81dice%20leaf8r.tif.info.json",
    "Codex-Cuara%2FCuara,%20Co%CC%81dice%20leaf9r.tif/info.json": "tests/fixtures/info/Codex-CuaraCuara,%20Co%CC%81dice%20leaf9r.tif.info.json",
    "DuckandC1951%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/DuckandC1951__ia_thumb.jpg.info.json",

    # BookReader
    "BookReaderJSIA.php?id=journalofexpedit00ford": "tests/fixtures/bookreader/journalofexpedit00ford.json",
    "BookReaderJSIA.php?id=goodytwoshoes00newyiala": "tests/fixtures/bookreader/goodytwoshoes.json",

    # Full text search, identified by the search term
    "journalofexpedit00ford&q=Brunswick": "tests/fixtures/search/fulltext-search.json",
    "journalofexpedit00ford&q=much": "tests/fixtures/search/2_boxes.json",
    "journalofexpedit00ford&q=pleasure%20to%20observe": "tests/fixtures/search/multi_word.json",
    "mrr_401&q=top": "tests/fixtures/search/missmatch.json",
    "gray-diary&q=Houston": "tests/fixtures/search/Houston.json",

    # Advanced search for building collections:
    "advancedsearch.php?q=collection%3Afrankbford":"tests/fixtures/advanced/frankbford.json",
    "advancedsearch.php?q=collection%3Auniversity_pittsburgh": "tests/fixtures/advanced/university_pittsburgh.json",
    "advancedsearch.php?q=collection%3Aterminal-escape-collection": "tests/fixtures/advanced/terminal-escape-collection.json",
    "advancedsearch.php?q=collection%3Ausgs_tx":"tests/fixtures/advanced/usgs_tx.json",

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
