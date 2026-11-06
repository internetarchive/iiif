import json
from functools import wraps
from unittest.mock import patch

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


def mock_url(fragment, fixture):
    """Serve `fixture` for any HTTP request whose URL contains `fragment`.

    This covers requests.get and calls made through a requests.Session. Stack
    one per URL. Fragments are checked top to bottom and the first match wins.
    A URL with no match raises an error, so a live call can't slip through.
    """
    def decorate(test):
        # Decorators apply bottom-up, so insert at the front to keep reading order.
        if hasattr(test, "_mock_routes"):
            test._mock_routes.insert(0, (fragment, fixture))
            return test

        routes = [(fragment, fixture)]

        def fake_request(session, method, url, *args, **kwargs):
            for known_fragment, known_fixture in routes:
                if known_fragment in url:
                    return mockResponse(known_fixture)
            raise AssertionError(f"Unexpected request: {url}")

        @wraps(test)
        def wrapper(*args, **kwargs):
            with patch("requests.Session.request", fake_request):
                return test(*args, **kwargs)

        wrapper._mock_routes = routes
        return wrapper

    return decorate


def log_requests(test):
    """Print the URL of every HTTP request made while `test` runs.

    Use this to work out which fixtures a test needs. On its own, requests still
    go to the network. To use it with @mock_url, put it below the @mock_url lines:
    it then prints each request and @mock_url answers it. Placed above them, it
    prints nothing.
    """
    @wraps(test)
    def wrapper(*args, **kwargs):
        # Look this up per run so a @mock_url above this decorator still applies.
        next_request = requests.Session.request

        def logging_request(session, method, url, *args, **kwargs):
            full_url = requests.Request(method, url, params=kwargs.get("params")).prepare().url
            print(f"[{test.__name__}] {method.upper()} {full_url}")
            return next_request(session, method, url, *args, **kwargs)

        with patch("requests.Session.request", logging_request):
            return test(*args, **kwargs)

    return wrapper
