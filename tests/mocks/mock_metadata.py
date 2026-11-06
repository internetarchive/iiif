import json
from functools import wraps
from unittest.mock import patch


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
    """Serve `fixture` for any requests.get whose URL contains `fragment`.

    Stack one per URL. Fragments are checked top to bottom and the first match
    wins. A URL with no match fails the test, so a live call can't slip through.
    """
    def decorate(test):
        # Decorators apply bottom-up, so insert at the front to keep reading order.
        if hasattr(test, "_mock_routes"):
            test._mock_routes.insert(0, (fragment, fixture))
            return test

        routes = [(fragment, fixture)]

        def fake_get(url, *args, **kwargs):
            for known_fragment, known_fixture in routes:
                if known_fragment in url:
                    return mockResponse(known_fixture)
            raise AssertionError(f"Unexpected request: {url}")

        @wraps(test)
        def wrapper(*args, **kwargs):
            with patch("requests.get", side_effect=fake_get):
                return test(*args, **kwargs)

        wrapper._mock_routes = routes
        return wrapper

    return decorate
