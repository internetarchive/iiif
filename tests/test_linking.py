import os

import unittest
from flask.testing import FlaskClient
from iiify.app import app

class TestLinking(unittest.TestCase):

    def setUp(self) -> None:
        app.config['CACHE_TYPE'] = "NullCache"
        self.test_app = FlaskClient(app)

    def convertListToHash(self, items):
        map = {}
        for item in items:
            map[item['label']['en'][0]] = item
        return map    

    def checkLink(self, map, field, name, value):        
        self.assertTrue(name in map, f"Expected to find {name} in {field}")

        self.assertEqual(map[name]['id'], value, f"Expected {value} in {map[name]}")

    def test_v3_image_links(self):
        resp = self.test_app.get("/iiif/3/journalofexpedit00ford/manifest.json?recache=true")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json    

        self.assertTrue('rendering' in manifest, "Expected rendering in Manifest")
        renderingMap = self.convertListToHash(manifest['rendering'])
        # Animated GIF - rendering
        self.checkLink(renderingMap, "rendering", "Animated GIF", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford.gif")
        # Text PDF - rendering
        self.checkLink(renderingMap, "rendering", "Text PDF", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford.pdf")
        # Abbyy GZ - rendering
        self.checkLink(renderingMap, "rendering", "Abbyy GZ", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_abbyy.gz")
        # Archive BitTorrent - rendering
        self.checkLink(renderingMap, "rendering", "Archive BitTorrent", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_archive.torrent")
        # Grayscale PDF - rendering
        self.checkLink(renderingMap, "rendering", "Grayscale PDF", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_bw.pdf")
        # chOCR - rendering
        self.checkLink(renderingMap, "rendering", "chOCR", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_chocr.html.gz")
        # DjVuTXT - rendering
        self.checkLink(renderingMap, "rendering", "DjVuTXT", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_djvu.txt")
        # Djvu XML - rendering
        self.checkLink(renderingMap, "rendering", "Djvu XML", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_djvu.xml")
        # hOCR - rendering
        self.checkLink(renderingMap, "rendering", "hOCR", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_hocr.html")
        # Single Page Processed JP2 ZIP - rendering
        self.checkLink(renderingMap, "rendering", "Single Page Processed JP2 ZIP", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_jp2.zip")
        # OCR Search Text - rendering
        self.checkLink(renderingMap, "rendering", "OCR Search Text", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_hocr_searchtext.txt.gz")
        # Single Page Original JP2 Tar - rendering
        self.checkLink(renderingMap, "rendering", "Single Page Original JP2 Tar", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_orig_jp2.tar")
        # DjVu - rendering
        self.checkLink(renderingMap, "rendering", "DjVu", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford.djvu")

        self.assertTrue('seeAlso' in manifest, "Expected seeAlso in Manifest")
        seeAlsoMap = self.convertListToHash(manifest['seeAlso'])
        # Cloth Cover Detection Log - seeAlso
        self.checkLink(seeAlsoMap, "seeAlso", "Cloth Cover Detection Log", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_cloth_detection.log")
        # Dublin Core - seeAlso
        self.checkLink(seeAlsoMap, "seeAlso", "Dublin Core", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_dc.xml")
        # OCR Page Index - seeAlso
        self.checkLink(seeAlsoMap, "seeAlso", "OCR Page Index", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_hocr_pageindex.json.gz")
        # MARC - seeAlso
        self.checkLink(seeAlsoMap, "seeAlso", "MARC", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_marc.xml")
        # MARC Binary - seeAlso
        self.checkLink(seeAlsoMap, "seeAlso", "MARC Binary", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_meta.mrc")
        # MARC Source - seeAlso
        self.checkLink(seeAlsoMap, "seeAlso", "MARC Source", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_metasource.xml")
        # Page Numbers JSON - seeAlso
        self.checkLink(seeAlsoMap, "seeAlso", "Page Numbers JSON", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_page_numbers.json")
        # Scandata - seeAlso
        self.checkLink(seeAlsoMap, "seeAlso", "Scandata", "https://archive.org/download/journalofexpedit00ford/journalofexpedit00ford_scandata.xml")

    def test_v3_video_links(self):
        resp = self.test_app.get("/iiif/3/DuckandC1951/manifest.json?recache=true")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json    

        self.assertTrue('rendering' in manifest, "Expected rendering in Manifest")
        renderingMap = self.convertListToHash(manifest['rendering'])
        seeAlsoMap = self.convertListToHash(manifest['seeAlso'])
        self.assertTrue("Unknown" not in renderingMap and "Unknown" not in seeAlsoMap, "Found Unknown in rendering or seeAlso where it shouldn't be.")

        # SubRip - rendering
        self.checkLink(renderingMap, "rendering", "SubRip", "https://archive.org/download/DuckandC1951/DuckandC1951.asr.srt")
		# Web Video Text Tracks - rendering
        self.checkLink(renderingMap, "rendering", "Web Video Text Tracks", "https://archive.org/download/DuckandC1951/DuckandC1951.asr.vtt")
		# Archive BitTorrent - rendering
        self.checkLink(renderingMap, "rendering", "Archive BitTorrent", "https://archive.org/download/DuckandC1951/DuckandC1951_archive.torrent")
		# Intermediate ASR JSON - rendering
        self.checkLink(renderingMap, "rendering", "Intermediate ASR JSON", "https://archive.org/download/DuckandC1951/DuckandC1951_intermediate_asr.json")
        # Whisper ASR JSON
        self.checkLink(renderingMap, "rendering", "Whisper ASR JSON", "https://archive.org/download/DuckandC1951/DuckandC1951_whisper_asr.json")

		# Storj Upload Log - seeAlso
        self.checkLink(seeAlsoMap, "seeAlso", "Storj Upload Log", "https://archive.org/download/DuckandC1951/DuckandC1951.storj-store.log")
		# Storj Upload Trigger - seeAlso
        self.checkLink(seeAlsoMap, "seeAlso", "Storj Upload Trigger", "https://archive.org/download/DuckandC1951/DuckandC1951.storj-store.trigger")

		# Thumbnail - thumbnail
        # 19 thumbs
        self.assertEqual(len(manifest['thumbnail']), 1, f"Expected 1 thumbnails: {manifest['thumbnail']}")