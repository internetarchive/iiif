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
    # manifests
    "/metadata/rashodgson68": "tests/fixtures/metadata/rashodgson68.json",
    "/metadata/fbf_3chords_1_": "tests/fixtures/metadata/fbf_3chords_1_.json",
    "/metadata/rbmsbk_ap2-v4_2001_V55N4": "tests/fixtures/metadata/rbmsbk_ap2-v4_2001_V55N4.json",
    "/metadata/gd72-04-14.aud.vernon.23662.sbeok.shnf": "tests/fixtures/metadata/gd72-04-14.aud.vernon.23662.sbeok.shnf.json",
    "/metadata/TvQuran.com__Alafasi": "tests/fixtures/metadata/TvQuran.com__Alafasi.json",
    "/metadata/alice_in_wonderland_librivox": "tests/fixtures/metadata/alice_in_wonderland_librivox.json",
    "/metadata/julian-damian-marley-with-the-uprising-band-shoreline-81697": "tests/fixtures/metadata/julian-damian-marley-with-the-uprising-band-shoreline-81697.json",
    "/metadata/nybc314063": "tests/fixtures/metadata/nybc314063.json",
    "/metadata/0-._20211206": "tests/fixtures/metadata/0-._20211206.json",
    "/metadata/mareful": "tests/fixtures/metadata/mareful.json",
    "/metadata/balagzone_gmail": "tests/fixtures/metadata/balagzone_gmail.json",
    "/metadata/annualreport00carn_14": "tests/fixtures/metadata/annualreport00carn_14.json",
    "/metadata/arkivkopia.se-lms-G70-48.3": "tests/fixtures/metadata/arkivkopia.se-lms-G70-48.3.json",
    "/metadata/st-anthony-relics-01": "tests/fixtures/metadata/st-anthony-relics-01.json",
    "/metadata/steamboat-willie-16mm-film-scan-4k-lossless": "tests/fixtures/metadata/steamboat-willie-16mm-film-scan-4k-lossless.json",
    "/metadata/cc4ia-Polar_Plunge_Promo_-_2018": "tests/fixtures/metadata/cc4ia-Polar_Plunge_Promo_-_2018.json",
    "/metadata/beowulf_te_librivox": "tests/fixtures/metadata/beowulf_te_librivox.json",
    "/metadata/78_der-er-maske-en-lille-pige-der-drommer-om-dig-skuespiller-edgar": "tests/fixtures/metadata/78_der-er-maske-en-lille-pige-der-drommer-om-dig-skuespiller-edgar.json",
    "/metadata/captain-n-the-game-master-season-2-mkv": "tests/fixtures/metadata/captain-n-the-game-master-season-2-mkv.json",
    "/metadata/DONAHUEARTSPECIAL": "tests/fixtures/metadata/DONAHUEARTSPECIAL.json",
    "/metadata/Waste-Management_Taster-Too-demo-2009": "tests/fixtures/metadata/Waste-Management_Taster-Too-demo-2009.json",
    "/metadata/bub_gb_3Kt5kiw9KYcC": "tests/fixtures/metadata/bub_gb_3Kt5kiw9KYcC.json",
    # Manifest v2 tests
    "/metadata/1991-12-compute-magazine": "tests/fixtures/metadata/1991-12-compute-magazine.json",
    "/metadata/opencontext-41-nippur-excavation-units": "tests/fixtures/metadata/opencontext-41-nippur-excavation-units.json",

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
    "img-8664_202009%2FIMG_8664_thumb.jpg/info.json": "tests/fixtures/info/img-8664_202009IMG_8664_thumb.jpg.info.json",
    "/3/img-8664_202009%2FIMG_8664.jpg/info.json": "tests/fixtures/info/3_img-8664_202009IMG_8664.jpg.info.json",
    "/2/img-8664_202009%2FIMG_8664.jpg/info.json": "tests/fixtures/info/2_img-8664_202009IMG_8664.jpg.info.json",
    "rashodgson68%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/rashodgson68__ia_thumb.jpg.info.json",
    "fbf_3chords_1_%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/fbf_3chords_1___ia_thumb.jpg.info.json",
    "rbmsbk_ap2-v4_2001_V55N4%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/rbmsbk_ap2-v4_2001_V55N4__ia_thumb.jpg.info.json",
    "gd72-04-14.aud.vernon.23662.sbeok.shnf%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/gd72-04-14.aud.vernon.23662.sbeok.shnf__ia_thumb.jpg.info.json",
    "TvQuran.com__Alafasi%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/TvQuran.com__Alafasi__ia_thumb.jpg.info.json",
    "alice_in_wonderland_librivox%2FAlice_in_Wonderland_thumb.jpg/info.json": "tests/fixtures/info/alice_in_wonderland_librivoxAlice_in_Wonderland_thumb.jpg.info.json",
    "nybc314063%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/nybc314063__ia_thumb.jpg.info.json",
    "0-._20211206%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/0-._20211206__ia_thumb.jpg.info.json",
    "mareful%2Fmaariful-quran-cover1_thumb.jpg/info.json": "tests/fixtures/info/marefulmaariful-quran-cover1_thumb.jpg.info.json",
    "balagzone_gmail%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/balagzone_gmail__ia_thumb.jpg.info.json",
    "annualreport00carn_14%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/annualreport00carn_14__ia_thumb.jpg.info.json",
    "arkivkopia.se-lms-G70-48.3%2Foriginal_lms2_4c4d535f4737302d34383a33.index.1.tiff_thumb.jpg/info.json": "tests/fixtures/info/arkivkopia.se-lms-G70-48.3original_lms2_4c4d535f4737302d34383a33.index.1.tiff_thumb.jpg.info.json",
    "arkivkopia.se-lms-G70-48.3%2Foriginal_lms2_4c4d535f4737302d34383a33.index.2.tiff_thumb.jpg/info.json": "tests/fixtures/info/arkivkopia.se-lms-G70-48.3original_lms2_4c4d535f4737302d34383a33.index.2.tiff_thumb.jpg.info.json",
    "arkivkopia.se-lms-G70-48.3%2Foriginal_lms2_4c4d535f4737302d34383a33.index.3.tiff_thumb.jpg/info.json": "tests/fixtures/info/arkivkopia.se-lms-G70-48.3original_lms2_4c4d535f4737302d34383a33.index.3.tiff_thumb.jpg.info.json",
    "arkivkopia.se-lms-G70-48.3%2Foriginal_lms2_4c4d535f4737302d34383a33.index.1.tiff.jpg/info.json": "tests/fixtures/info/arkivkopia.se-lms-G70-48.3original_lms2_4c4d535f4737302d34383a33.index.1.tiff.jpg.info.json",
    "arkivkopia.se-lms-G70-48.3%2Foriginal_lms2_4c4d535f4737302d34383a33.index.2.tiff.jpg/info.json": "tests/fixtures/info/arkivkopia.se-lms-G70-48.3original_lms2_4c4d535f4737302d34383a33.index.2.tiff.jpg.info.json",
    "arkivkopia.se-lms-G70-48.3%2Foriginal_lms2_4c4d535f4737302d34383a33.index.3.tiff.jpg/info.json": "tests/fixtures/info/arkivkopia.se-lms-G70-48.3original_lms2_4c4d535f4737302d34383a33.index.3.tiff.jpg.info.json",
    "st-anthony-relics-01%2FAuronzo-ComuneCortina_thumb.jpg/info.json": "tests/fixtures/info/st-anthony-relics-01Auronzo-ComuneCortina_thumb.jpg.info.json",
    "st-anthony-relics-01%2FCadore-Becher_1998_thumb.jpg/info.json": "tests/fixtures/info/st-anthony-relics-01Cadore-Becher_1998_thumb.jpg.info.json",
    "st-anthony-relics-01%2FStAnthony-Relics_01_thumb.jpg/info.json": "tests/fixtures/info/st-anthony-relics-01StAnthony-Relics_01_thumb.jpg.info.json",
    "st-anthony-relics-01%2FStAnthony-Relics_02_thumb.jpg/info.json": "tests/fixtures/info/st-anthony-relics-01StAnthony-Relics_02_thumb.jpg.info.json",
    "st-anthony-relics-01%2FStAnthony-Relics_03_thumb.jpg/info.json": "tests/fixtures/info/st-anthony-relics-01StAnthony-Relics_03_thumb.jpg.info.json",
    "steamboat-willie-16mm-film-scan-4k-lossless%2FSteamboat%20Willie%20%5B16mm%20Film%20Scan%5D_ProRes%20%283400x2550%29.01_thumb.jpg/info.json": "tests/fixtures/info/steamboat-willie-16mm-film-scan-4k-losslessSteamboat%20Willie%20%5B16mm%20Film%20Scan%5D_ProRes%20%283400x2550%29.01_thumb.jpg.info.json",
    "cc4ia-Polar_Plunge_Promo_-_2018%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/cc4ia-Polar_Plunge_Promo_-_2018__ia_thumb.jpg.info.json",
    "beowulf_te_librivox%2Fbeowulf_1310_thumb.jpg/info.json": "tests/fixtures/info/beowulf_te_librivoxbeowulf_1310_thumb.jpg.info.json",
    "78_der-er-maske-en-lille-pige-der-drommer-om-dig-skuespiller-edgar%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/78_der-er-maske-en-lille-pige-der-drommer-om-dig-skuespiller-edgar__ia_thumb.jpg.info.json",
    "captain-n-the-game-master-season-2-mkv%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/captain-n-the-game-master-season-2-mkv__ia_thumb.jpg.info.json",
    "DONAHUEARTSPECIAL%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/DONAHUEARTSPECIAL__ia_thumb.jpg.info.json",
    "Waste-Management_Taster-Too-demo-2009%2Fwaste%20management%20cover_thumb.jpg/info.json": "tests/fixtures/info/Waste-Management_Taster-Too-demo-2009waste%20management%20cover_thumb.jpg.info.json",
    "Waste-Management_Taster-Too-demo-2009%2Fwaste%20management%20img2_thumb.jpg/info.json": "tests/fixtures/info/Waste-Management_Taster-Too-demo-2009waste%20management%20img2_thumb.jpg.info.json",
    "Waste-Management_Taster-Too-demo-2009%2Fwaste%20management%20img_thumb.jpg/info.json": "tests/fixtures/info/Waste-Management_Taster-Too-demo-2009waste%20management%20img_thumb.jpg.info.json",
    "Waste-Management_Taster-Too-demo-2009%2Fwaste%20management%20inside_thumb.jpg/info.json": "tests/fixtures/info/Waste-Management_Taster-Too-demo-2009waste%20management%20inside_thumb.jpg.info.json",
    "Waste-Management_Taster-Too-demo-2009%2Fwaste%20management%20outside_thumb.jpg/info.json": "tests/fixtures/info/Waste-Management_Taster-Too-demo-2009waste%20management%20outside_thumb.jpg.info.json",
    "bub_gb_3Kt5kiw9KYcC%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/bub_gb_3Kt5kiw9KYcC__ia_thumb.jpg.info.json",
    "opencontext-41-nippur-excavation-units%2F41-nippur-excavation-units.jpg/info.json": "tests/fixtures/info/opencontext-41-nippur-excavation-units41-nippur-excavation-units.jpg.info.json",

    # BookReader
    "BookReaderJSIA.php?id=journalofexpedit00ford": "tests/fixtures/bookreader/journalofexpedit00ford.json",
    "BookReaderJSIA.php?id=goodytwoshoes00newyiala": "tests/fixtures/bookreader/goodytwoshoes.json",
    "BookReaderJSIA.php?id=rashodgson68": "tests/fixtures/bookreader/rashodgson68.json",
    "BookReaderJSIA.php?id=fbf_3chords_1_": "tests/fixtures/fbf_3chords_1_.json",
    "BookReaderJSIA.php?id=rbmsbk_ap2-v4_2001_V55N4": "tests/fixtures/rbmsbk_ap2-v4_2001_V55N4.json",
    "BookReaderJSIA.php?id=nybc314063": "tests/fixtures/bookreader/nybc314063.json",
    "BookReaderJSIA.php?id=0-._20211206": "tests/fixtures/bookreader/0-._20211206.json",
    "BookReaderJSIA.php?id=mareful": "tests/fixtures/bookreader/mareful.json",
    "BookReaderJSIA.php?id=balagzone_gmail": "tests/fixtures/bookreader/balagzone.json",
    "BookReaderJSIA.php?id=annualreport00carn_14": "tests/fixtures/bookreader/annualreport00carn_14.json",
    "BookReaderJSIA.php?id=st-anthony-relics-01": "tests/fixtures/bookreader/st-anthony-relics-01.json",
    
    # v2 book reader
    "BookReaderJSON.php?itemId=rashodgson68": "tests/fixtures/bookreader/v2_rashodgson68.json",
    "BookReaderJSON.php?itemId=1991-12-compute-magazine": "tests/fixtures/bookreader/v2_1991-12-compute-magazine.json",
    "BookReaderJSON.php?itemId=fbf_3chords_1_": "tests/fixtures/bookreader/v2_fbf_3chords_1_.json",
    "BookReaderJSON.php?itemId=bub_gb_3Kt5kiw9KYcC": "tests/fixtures/bookreader/bub_gb_3Kt5kiw9KYcC.json",
    
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
