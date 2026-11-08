import os
import unittest
from tests.base import IIIFTestCase

from iiify.resolver import safe_media_path
from iiify.configs import media_root


class TestSafeMediaPath(IIIFTestCase):
    """Regression tests for CodeQL py/path-injection #11 and #91.

    ``safe_media_path`` is the single source-side sanitizer for the tainted
    ``path`` used by ``ia_resolver`` at ``os.path.exists(path)`` and
    ``open(path, 'wb')``. These tests prove traversal is confined to
    ``media_root`` while legitimate identifiers still resolve correctly.
    """

    def setUp(self):
        self.media_base = os.path.realpath(media_root)

    # --- legitimate identifiers still resolve, inside media_root ---

    def test_plain_identifier_resolves_inside_media_root(self):
        path = safe_media_path("goody")
        self.assertEqual(path, os.path.join(self.media_base, "goody"))
        self.assertTrue(path.startswith(self.media_base + os.sep))

    def test_identifier_with_filepath_suffix_is_confined(self):
        # ia_resolver passes the full identifier (incl. $/: suffixes) through.
        path = safe_media_path("goody$cover.jpg")
        self.assertTrue(path.startswith(self.media_base + os.sep))

    def test_identifier_with_document_suffix_is_confined(self):
        path = safe_media_path("goody:doc")
        self.assertTrue(path.startswith(self.media_base + os.sep))

    def test_dots_in_filename_are_allowed(self):
        # A leading-dot or dotted filename is fine as long as it stays within root.
        path = safe_media_path("my.book.v2")
        self.assertEqual(path, os.path.join(self.media_base, "my.book.v2"))

    # --- traversal / absolute / null-byte payloads are rejected ---

    def test_relative_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            safe_media_path("../../etc/passwd")

    def test_deep_relative_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            safe_media_path("../" * 12 + "etc/passwd")

    def test_absolute_path_is_rejected(self):
        with self.assertRaises(ValueError):
            safe_media_path("/etc/passwd")

    def test_traversal_in_filepath_suffix_is_rejected(self):
        # A ``$filepath`` component laden with .. must not escape either.
        with self.assertRaises(ValueError):
            safe_media_path("goody$../../../../etc/passwd")

    def test_traversal_in_document_suffix_is_rejected(self):
        with self.assertRaises(ValueError):
            safe_media_path("goody:../../../../etc/passwd")

    def test_null_byte_is_rejected(self):
        with self.assertRaises(ValueError):
            safe_media_path("goody\x00.jpg")

    def test_empty_identifier_is_rejected(self):
        with self.assertRaises(ValueError):
            safe_media_path("")

    def test_media_root_itself_is_rejected(self):
        # A value that resolves to media_root exactly is not a valid resource.
        with self.assertRaises(ValueError):
            safe_media_path(".")


if __name__ == "__main__":
    unittest.main()
