"""Security regression tests for create_annotations.

Covers two CodeQL findings in iiify/resolver.py:create_annotations:
  * #13 py/xpath-injection (CRITICAL) — canvas_no interpolated into an
    ElementPath query.
  * #9  py/xml-bomb (HIGH) — remote XML parsed without entity-expansion guard.

All inputs are crafted LOCALLY and fed directly to the code under test. No
request is ever made to archive.org or any external service: requests.get is
mocked so the XML payload never leaves this process.
"""

import unittest
from tests.base import IIIFTestCase
from unittest.mock import patch

from iiify import resolver


class _FakeResponse:
    """Minimal stand-in for a requests.Response wrapping canned XML bytes."""

    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        return None


def _mock_get(content: bytes):
    """Return a patcher for resolver.requests.get yielding `content`."""
    return patch.object(
        resolver.requests, "get", return_value=_FakeResponse(content)
    )


# A tiny, well-formed DjVu-style document with a single OBJECT/WORD so the
# normal (non-malicious) path can be exercised end to end.
BENIGN_XML = (
    b"<?xml version='1.0'?>"
    b"<DjVuXML><BODY>"
    b"<OBJECT><WORD coords='10,40,30,20'>hello</WORD></OBJECT>"
    b"</BODY></DjVuXML>"
)

# Classic "billion laughs" internal-entity-expansion bomb.
BILLION_LAUGHS = (
    b"<?xml version='1.0'?>"
    b"<!DOCTYPE lolz ["
    b" <!ENTITY lol 'lol'>"
    b" <!ENTITY lol1 '&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;'>"
    b" <!ENTITY lol2 '&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;'>"
    b" <!ENTITY lol3 '&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;'>"
    b"]>"
    b"<lolz>&lol3;</lolz>"
)

# External-entity (XXE) payload attempting to read a local file.
XXE_PAYLOAD = (
    b"<?xml version='1.0'?>"
    b"<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>"
    b"<foo><OBJECT>&xxe;</OBJECT></foo>"
)


class TestXPathInjection(IIIFTestCase):
    """CodeQL #13 — canvas_no must be a positive integer."""

    def test_non_integer_canvas_no_rejected(self):
        # An ElementPath-injection attempt must be rejected before any fetch.
        with _mock_get(BENIGN_XML) as mocked_get:
            with self.assertRaises(ValueError):
                resolver.create_annotations(
                    3, "ident", "file.xml", "1]|//OBJECT", domain="https://x/"
                )
            mocked_get.assert_not_called()

    def test_zero_and_negative_canvas_no_rejected(self):
        for bad in (0, -1, "-5"):
            with self.subTest(canvas_no=bad):
                with _mock_get(BENIGN_XML):
                    with self.assertRaises(ValueError):
                        resolver.create_annotations(
                            3, "ident", "file.xml", bad, domain="https://x/"
                        )

    def test_valid_canvas_no_builds_annotations(self):
        # The fix must not break the normal path: a valid canvas_no over
        # benign XML yields one annotation from the single WORD.
        with _mock_get(BENIGN_XML):
            result = resolver.create_annotations(
                3, "ident", "file.xml", 1, domain="https://x/"
            )
        self.assertEqual(result["type"], "AnnotationPage")
        self.assertEqual(len(result["items"]), 1)
        # coords='10,40,30,20' -> x=10, y=20, w=20, h=20
        self.assertEqual(result["items"][0]["body"]["value"], "hello")
        self.assertTrue(result["items"][0]["target"].endswith("xywh=10,20,20,20"))


class TestXmlBomb(IIIFTestCase):
    """CodeQL #9 — hardened parser refuses entity expansion / external refs."""

    def test_billion_laughs_refused(self):
        with _mock_get(BILLION_LAUGHS):
            with self.assertRaises(ValueError):
                resolver.create_annotations(
                    3, "ident", "file.xml", 1, domain="https://x/"
                )

    def test_external_entity_refused(self):
        with _mock_get(XXE_PAYLOAD):
            with self.assertRaises(ValueError):
                resolver.create_annotations(
                    3, "ident", "file.xml", 1, domain="https://x/"
                )

    def test_defused_parser_does_not_expand_entities(self):
        # Prove it at the parser level too: defused_fromstring raises rather
        # than expanding, so no memory blow-up occurs.
        from defusedxml.common import DefusedXmlException

        with self.assertRaises(DefusedXmlException):
            resolver.defused_fromstring(BILLION_LAUGHS)


if __name__ == "__main__":
    unittest.main()
