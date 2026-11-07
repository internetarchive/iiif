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
    # Video tests
    "/metadata/youtube-7w8F2Xi3vFw": "tests/fixtures/metadata/youtube-7w8F2Xi3vFw.json",
    "/metadata/taboca_201002_03": "tests/fixtures/metadata/taboca_201002_03.json",
    "/metadata/youtube-SvH4fbjOT0A": "tests/fixtures/metadata/youtube-SvH4fbjOT0A.json",
    "/metadata/cruz-test": "tests/fixtures/metadata/cruz-test.json",
    "/metadata/CSPAN3_20180217_164800_Poplar_Forest_Archaeology": "tests/fixtures/metadata/CSPAN3_20180217_164800_Poplar_Forest_Archaeology.json",
    "/metadata/coitx-Inside_the_Movies_-_Shang-Chi_and_the_Legend_of_the_Ten_Rings": "tests/fixtures/metadata/coitx-Inside_the_Movies_-_Shang-Chi_and_the_Legend_of_the_Ten_Rings.json",
    "/metadata/2025-highland-house-walkthrough-ma": "tests/fixtures/metadata/2025-highland-house-walkthrough-ma.json",
    "/metadata/DontBeaS1947": "tests/fixtures/metadata/DontBeaS1947.json",

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
    "/3/img-8664_202009%2FIMG_8664.jpg/info.json": "tests/fixtures/info/3/img-8664_202009IMG_8664.jpg.info.json",
    "/2/img-8664_202009%2FIMG_8664.jpg/info.json": "tests/fixtures/info/2/img-8664_202009IMG_8664.jpg.info.json",
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
    "2/youtube-7w8F2Xi3vFw%2F34C3_-_International_Image_Interoperability_Framework_IIIF_Kulturinstitutionen_schaffen_interop-7w8F2Xi3vFw_thumb.jpg/info.json": "tests/fixtures/info/2/youtube-7w8F2Xi3vFw34C3_-_International_Image_Interoperability_Framework_IIIF_Kulturinstitutionen_schaffen_interop-7w8F2Xi3vFw_thumb.jpg.info.json",
    "3/youtube-7w8F2Xi3vFw%2F34C3_-_International_Image_Interoperability_Framework_IIIF_Kulturinstitutionen_schaffen_interop-7w8F2Xi3vFw.jpg/info.json": "tests/fixtures/info/3/youtube-7w8F2Xi3vFw34C3_-_International_Image_Interoperability_Framework_IIIF_Kulturinstitutionen_schaffen_interop-7w8F2Xi3vFw.jpg.info.json",
    "3/taboca_201002_03%2F0c53341f060875c7d387c62203170d51.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030c53341f060875c7d387c62203170d51.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F0c53341f060875c7d387c62203170d51.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030c53341f060875c7d387c62203170d51.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F0c53341f060875c7d387c62203170d51.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030c53341f060875c7d387c62203170d51.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F0c53341f060875c7d387c62203170d51.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030c53341f060875c7d387c62203170d51.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F0c53341f060875c7d387c62203170d51.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030c53341f060875c7d387c62203170d51.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F0c53341f060875c7d387c62203170d51.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030c53341f060875c7d387c62203170d51.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F0ce75d623fb5b81bfbd5f01718c051e0.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030ce75d623fb5b81bfbd5f01718c051e0.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F0ce75d623fb5b81bfbd5f01718c051e0.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030ce75d623fb5b81bfbd5f01718c051e0.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F0ce75d623fb5b81bfbd5f01718c051e0.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030ce75d623fb5b81bfbd5f01718c051e0.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F0ce75d623fb5b81bfbd5f01718c051e0.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030ce75d623fb5b81bfbd5f01718c051e0.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F0ce75d623fb5b81bfbd5f01718c051e0.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030ce75d623fb5b81bfbd5f01718c051e0.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F0ce75d623fb5b81bfbd5f01718c051e0.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030ce75d623fb5b81bfbd5f01718c051e0.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F0e2903eadb796e8ca0bb685518f2ba42.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030e2903eadb796e8ca0bb685518f2ba42.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F0e2903eadb796e8ca0bb685518f2ba42.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030e2903eadb796e8ca0bb685518f2ba42.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F0e2903eadb796e8ca0bb685518f2ba42.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030e2903eadb796e8ca0bb685518f2ba42.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F0e2903eadb796e8ca0bb685518f2ba42.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030e2903eadb796e8ca0bb685518f2ba42.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F0e2903eadb796e8ca0bb685518f2ba42.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030e2903eadb796e8ca0bb685518f2ba42.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F0e2903eadb796e8ca0bb685518f2ba42.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_030e2903eadb796e8ca0bb685518f2ba42.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F14a399004d05fb55da286ed73c16daf0.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0314a399004d05fb55da286ed73c16daf0.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F14a399004d05fb55da286ed73c16daf0.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0314a399004d05fb55da286ed73c16daf0.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F14a399004d05fb55da286ed73c16daf0.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0314a399004d05fb55da286ed73c16daf0.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F14a399004d05fb55da286ed73c16daf0.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0314a399004d05fb55da286ed73c16daf0.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F14a399004d05fb55da286ed73c16daf0.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0314a399004d05fb55da286ed73c16daf0.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F14a399004d05fb55da286ed73c16daf0.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0314a399004d05fb55da286ed73c16daf0.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F163dcbee497895da0d093134890be2ca.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03163dcbee497895da0d093134890be2ca.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F163dcbee497895da0d093134890be2ca.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03163dcbee497895da0d093134890be2ca.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F163dcbee497895da0d093134890be2ca.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03163dcbee497895da0d093134890be2ca.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F163dcbee497895da0d093134890be2ca.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03163dcbee497895da0d093134890be2ca.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F163dcbee497895da0d093134890be2ca.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03163dcbee497895da0d093134890be2ca.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F163dcbee497895da0d093134890be2ca.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03163dcbee497895da0d093134890be2ca.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F1789a4309751369b2fca2a84e90425ac.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_031789a4309751369b2fca2a84e90425ac.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F1789a4309751369b2fca2a84e90425ac.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_031789a4309751369b2fca2a84e90425ac.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F1789a4309751369b2fca2a84e90425ac.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_031789a4309751369b2fca2a84e90425ac.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F1789a4309751369b2fca2a84e90425ac.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_031789a4309751369b2fca2a84e90425ac.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F1789a4309751369b2fca2a84e90425ac.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_031789a4309751369b2fca2a84e90425ac.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F1789a4309751369b2fca2a84e90425ac.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_031789a4309751369b2fca2a84e90425ac.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F197eadf007384ccac65db98615c9a683.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03197eadf007384ccac65db98615c9a683.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F197eadf007384ccac65db98615c9a683.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03197eadf007384ccac65db98615c9a683.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F197eadf007384ccac65db98615c9a683.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03197eadf007384ccac65db98615c9a683.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F197eadf007384ccac65db98615c9a683.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03197eadf007384ccac65db98615c9a683.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F197eadf007384ccac65db98615c9a683.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03197eadf007384ccac65db98615c9a683.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F197eadf007384ccac65db98615c9a683.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03197eadf007384ccac65db98615c9a683.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F22f57fc74656ced9b96f2af5fe52f506.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0322f57fc74656ced9b96f2af5fe52f506.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F22f57fc74656ced9b96f2af5fe52f506.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0322f57fc74656ced9b96f2af5fe52f506.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F22f57fc74656ced9b96f2af5fe52f506.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0322f57fc74656ced9b96f2af5fe52f506.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F22f57fc74656ced9b96f2af5fe52f506.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0322f57fc74656ced9b96f2af5fe52f506.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F22f57fc74656ced9b96f2af5fe52f506.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0322f57fc74656ced9b96f2af5fe52f506.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F22f57fc74656ced9b96f2af5fe52f506.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0322f57fc74656ced9b96f2af5fe52f506.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F2364806606ac51cd64b3c918f482ef78.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_032364806606ac51cd64b3c918f482ef78.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F2364806606ac51cd64b3c918f482ef78.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_032364806606ac51cd64b3c918f482ef78.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F2364806606ac51cd64b3c918f482ef78.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_032364806606ac51cd64b3c918f482ef78.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F2364806606ac51cd64b3c918f482ef78.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_032364806606ac51cd64b3c918f482ef78.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F2364806606ac51cd64b3c918f482ef78.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_032364806606ac51cd64b3c918f482ef78.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F2364806606ac51cd64b3c918f482ef78.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_032364806606ac51cd64b3c918f482ef78.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F26889bbe281b6f12747521f01764e564.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0326889bbe281b6f12747521f01764e564.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F26889bbe281b6f12747521f01764e564.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0326889bbe281b6f12747521f01764e564.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F26889bbe281b6f12747521f01764e564.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0326889bbe281b6f12747521f01764e564.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F26889bbe281b6f12747521f01764e564.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0326889bbe281b6f12747521f01764e564.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F26889bbe281b6f12747521f01764e564.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0326889bbe281b6f12747521f01764e564.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F26889bbe281b6f12747521f01764e564.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0326889bbe281b6f12747521f01764e564.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F33c8795783668c0ce9932240769caad5.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0333c8795783668c0ce9932240769caad5.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F33c8795783668c0ce9932240769caad5.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0333c8795783668c0ce9932240769caad5.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F33c8795783668c0ce9932240769caad5.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0333c8795783668c0ce9932240769caad5.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F33c8795783668c0ce9932240769caad5.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0333c8795783668c0ce9932240769caad5.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F33c8795783668c0ce9932240769caad5.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0333c8795783668c0ce9932240769caad5.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F33c8795783668c0ce9932240769caad5.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0333c8795783668c0ce9932240769caad5.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F34a2acb0ace173f44704613fbba2597c.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0334a2acb0ace173f44704613fbba2597c.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F34a2acb0ace173f44704613fbba2597c.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0334a2acb0ace173f44704613fbba2597c.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F34a2acb0ace173f44704613fbba2597c.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0334a2acb0ace173f44704613fbba2597c.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F34a2acb0ace173f44704613fbba2597c.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0334a2acb0ace173f44704613fbba2597c.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F34a2acb0ace173f44704613fbba2597c.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0334a2acb0ace173f44704613fbba2597c.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F34a2acb0ace173f44704613fbba2597c.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0334a2acb0ace173f44704613fbba2597c.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F36eb20e409cc7e22f87043f8348eb787.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0336eb20e409cc7e22f87043f8348eb787.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F36eb20e409cc7e22f87043f8348eb787.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0336eb20e409cc7e22f87043f8348eb787.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F36eb20e409cc7e22f87043f8348eb787.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0336eb20e409cc7e22f87043f8348eb787.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F36eb20e409cc7e22f87043f8348eb787.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0336eb20e409cc7e22f87043f8348eb787.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F36eb20e409cc7e22f87043f8348eb787.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0336eb20e409cc7e22f87043f8348eb787.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F36eb20e409cc7e22f87043f8348eb787.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0336eb20e409cc7e22f87043f8348eb787.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F406c14c0f3090f85aa8d2fe4c9bb30e5.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03406c14c0f3090f85aa8d2fe4c9bb30e5.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F406c14c0f3090f85aa8d2fe4c9bb30e5.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03406c14c0f3090f85aa8d2fe4c9bb30e5.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F406c14c0f3090f85aa8d2fe4c9bb30e5.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03406c14c0f3090f85aa8d2fe4c9bb30e5.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F406c14c0f3090f85aa8d2fe4c9bb30e5.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03406c14c0f3090f85aa8d2fe4c9bb30e5.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F406c14c0f3090f85aa8d2fe4c9bb30e5.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03406c14c0f3090f85aa8d2fe4c9bb30e5.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F406c14c0f3090f85aa8d2fe4c9bb30e5.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03406c14c0f3090f85aa8d2fe4c9bb30e5.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F40f063d458f2dac0f959cdaf8df72a75.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0340f063d458f2dac0f959cdaf8df72a75.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F40f063d458f2dac0f959cdaf8df72a75.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0340f063d458f2dac0f959cdaf8df72a75.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F40f063d458f2dac0f959cdaf8df72a75.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0340f063d458f2dac0f959cdaf8df72a75.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F40f063d458f2dac0f959cdaf8df72a75.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0340f063d458f2dac0f959cdaf8df72a75.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F40f063d458f2dac0f959cdaf8df72a75.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0340f063d458f2dac0f959cdaf8df72a75.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F40f063d458f2dac0f959cdaf8df72a75.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0340f063d458f2dac0f959cdaf8df72a75.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F53981a1c888f8af9febbf63974bdca45.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0353981a1c888f8af9febbf63974bdca45.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F53981a1c888f8af9febbf63974bdca45.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0353981a1c888f8af9febbf63974bdca45.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F53981a1c888f8af9febbf63974bdca45.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0353981a1c888f8af9febbf63974bdca45.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F53981a1c888f8af9febbf63974bdca45.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0353981a1c888f8af9febbf63974bdca45.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F53981a1c888f8af9febbf63974bdca45.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0353981a1c888f8af9febbf63974bdca45.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F53981a1c888f8af9febbf63974bdca45.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0353981a1c888f8af9febbf63974bdca45.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F549b36149d78f1b2e455cf2109174be4.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03549b36149d78f1b2e455cf2109174be4.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F549b36149d78f1b2e455cf2109174be4.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03549b36149d78f1b2e455cf2109174be4.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F549b36149d78f1b2e455cf2109174be4.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03549b36149d78f1b2e455cf2109174be4.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F549b36149d78f1b2e455cf2109174be4.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03549b36149d78f1b2e455cf2109174be4.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F549b36149d78f1b2e455cf2109174be4.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03549b36149d78f1b2e455cf2109174be4.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F549b36149d78f1b2e455cf2109174be4.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03549b36149d78f1b2e455cf2109174be4.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F63c331b35b2c1c337e7fab37e1b5cc04.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0363c331b35b2c1c337e7fab37e1b5cc04.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F63c331b35b2c1c337e7fab37e1b5cc04.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0363c331b35b2c1c337e7fab37e1b5cc04.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F63c331b35b2c1c337e7fab37e1b5cc04.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0363c331b35b2c1c337e7fab37e1b5cc04.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F63c331b35b2c1c337e7fab37e1b5cc04.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0363c331b35b2c1c337e7fab37e1b5cc04.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F63c331b35b2c1c337e7fab37e1b5cc04.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0363c331b35b2c1c337e7fab37e1b5cc04.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F63c331b35b2c1c337e7fab37e1b5cc04.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0363c331b35b2c1c337e7fab37e1b5cc04.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F6b9a182c4e6d0a67e67e2fc2cda0a8e3.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_036b9a182c4e6d0a67e67e2fc2cda0a8e3.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F6b9a182c4e6d0a67e67e2fc2cda0a8e3.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_036b9a182c4e6d0a67e67e2fc2cda0a8e3.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F6b9a182c4e6d0a67e67e2fc2cda0a8e3.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_036b9a182c4e6d0a67e67e2fc2cda0a8e3.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F6b9a182c4e6d0a67e67e2fc2cda0a8e3.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_036b9a182c4e6d0a67e67e2fc2cda0a8e3.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F6b9a182c4e6d0a67e67e2fc2cda0a8e3.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_036b9a182c4e6d0a67e67e2fc2cda0a8e3.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F6b9a182c4e6d0a67e67e2fc2cda0a8e3.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_036b9a182c4e6d0a67e67e2fc2cda0a8e3.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F84133d0fa0364ab83df65881d2695233.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0384133d0fa0364ab83df65881d2695233.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F84133d0fa0364ab83df65881d2695233.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0384133d0fa0364ab83df65881d2695233.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F84133d0fa0364ab83df65881d2695233.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0384133d0fa0364ab83df65881d2695233.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F84133d0fa0364ab83df65881d2695233.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0384133d0fa0364ab83df65881d2695233.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F84133d0fa0364ab83df65881d2695233.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0384133d0fa0364ab83df65881d2695233.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F84133d0fa0364ab83df65881d2695233.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0384133d0fa0364ab83df65881d2695233.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F86bd2576d60d1fbe32ff4e0b357e0d52.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0386bd2576d60d1fbe32ff4e0b357e0d52.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F86bd2576d60d1fbe32ff4e0b357e0d52.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0386bd2576d60d1fbe32ff4e0b357e0d52.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F86bd2576d60d1fbe32ff4e0b357e0d52.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0386bd2576d60d1fbe32ff4e0b357e0d52.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F86bd2576d60d1fbe32ff4e0b357e0d52.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0386bd2576d60d1fbe32ff4e0b357e0d52.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F86bd2576d60d1fbe32ff4e0b357e0d52.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0386bd2576d60d1fbe32ff4e0b357e0d52.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F86bd2576d60d1fbe32ff4e0b357e0d52.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0386bd2576d60d1fbe32ff4e0b357e0d52.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F8d8250d8521693e1b317e917926badf1.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_038d8250d8521693e1b317e917926badf1.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F8d8250d8521693e1b317e917926badf1.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_038d8250d8521693e1b317e917926badf1.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F8d8250d8521693e1b317e917926badf1.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_038d8250d8521693e1b317e917926badf1.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F8d8250d8521693e1b317e917926badf1.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_038d8250d8521693e1b317e917926badf1.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F8d8250d8521693e1b317e917926badf1.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_038d8250d8521693e1b317e917926badf1.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F8d8250d8521693e1b317e917926badf1.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_038d8250d8521693e1b317e917926badf1.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F9090020d16b100345c57747b3434bab3.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039090020d16b100345c57747b3434bab3.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F9090020d16b100345c57747b3434bab3.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039090020d16b100345c57747b3434bab3.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F9090020d16b100345c57747b3434bab3.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039090020d16b100345c57747b3434bab3.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F9090020d16b100345c57747b3434bab3.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039090020d16b100345c57747b3434bab3.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F9090020d16b100345c57747b3434bab3.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039090020d16b100345c57747b3434bab3.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F9090020d16b100345c57747b3434bab3.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039090020d16b100345c57747b3434bab3.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F90c447c45086c8c88c03625fcf120a69.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0390c447c45086c8c88c03625fcf120a69.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F90c447c45086c8c88c03625fcf120a69.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0390c447c45086c8c88c03625fcf120a69.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F90c447c45086c8c88c03625fcf120a69.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0390c447c45086c8c88c03625fcf120a69.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F90c447c45086c8c88c03625fcf120a69.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0390c447c45086c8c88c03625fcf120a69.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F90c447c45086c8c88c03625fcf120a69.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0390c447c45086c8c88c03625fcf120a69.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F90c447c45086c8c88c03625fcf120a69.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_0390c447c45086c8c88c03625fcf120a69.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F981cbaea0ade5ff3b0dd8050b1b78a82.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03981cbaea0ade5ff3b0dd8050b1b78a82.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F981cbaea0ade5ff3b0dd8050b1b78a82.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03981cbaea0ade5ff3b0dd8050b1b78a82.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F981cbaea0ade5ff3b0dd8050b1b78a82.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03981cbaea0ade5ff3b0dd8050b1b78a82.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F981cbaea0ade5ff3b0dd8050b1b78a82.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03981cbaea0ade5ff3b0dd8050b1b78a82.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F981cbaea0ade5ff3b0dd8050b1b78a82.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03981cbaea0ade5ff3b0dd8050b1b78a82.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F981cbaea0ade5ff3b0dd8050b1b78a82.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03981cbaea0ade5ff3b0dd8050b1b78a82.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F9c58481a7a3a043c377eaceb1064f082.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039c58481a7a3a043c377eaceb1064f082.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F9c58481a7a3a043c377eaceb1064f082.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039c58481a7a3a043c377eaceb1064f082.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F9c58481a7a3a043c377eaceb1064f082.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039c58481a7a3a043c377eaceb1064f082.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F9c58481a7a3a043c377eaceb1064f082.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039c58481a7a3a043c377eaceb1064f082.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F9c58481a7a3a043c377eaceb1064f082.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039c58481a7a3a043c377eaceb1064f082.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F9c58481a7a3a043c377eaceb1064f082.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039c58481a7a3a043c377eaceb1064f082.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2F9e882679e96f8ee807474fbf5844f6cc.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039e882679e96f8ee807474fbf5844f6cc.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2F9e882679e96f8ee807474fbf5844f6cc.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039e882679e96f8ee807474fbf5844f6cc.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2F9e882679e96f8ee807474fbf5844f6cc.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039e882679e96f8ee807474fbf5844f6cc.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2F9e882679e96f8ee807474fbf5844f6cc.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039e882679e96f8ee807474fbf5844f6cc.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2F9e882679e96f8ee807474fbf5844f6cc.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039e882679e96f8ee807474fbf5844f6cc.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2F9e882679e96f8ee807474fbf5844f6cc.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_039e882679e96f8ee807474fbf5844f6cc.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Faf378a1f53c7a5c44306730da89f0e31.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03af378a1f53c7a5c44306730da89f0e31.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Faf378a1f53c7a5c44306730da89f0e31.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03af378a1f53c7a5c44306730da89f0e31.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Faf378a1f53c7a5c44306730da89f0e31.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03af378a1f53c7a5c44306730da89f0e31.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Faf378a1f53c7a5c44306730da89f0e31.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03af378a1f53c7a5c44306730da89f0e31.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Faf378a1f53c7a5c44306730da89f0e31.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03af378a1f53c7a5c44306730da89f0e31.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Faf378a1f53c7a5c44306730da89f0e31.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03af378a1f53c7a5c44306730da89f0e31.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Faf5f9dfaccf0f7dd92383304f4a7f008.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03af5f9dfaccf0f7dd92383304f4a7f008.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Faf5f9dfaccf0f7dd92383304f4a7f008.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03af5f9dfaccf0f7dd92383304f4a7f008.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Faf5f9dfaccf0f7dd92383304f4a7f008.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03af5f9dfaccf0f7dd92383304f4a7f008.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Faf5f9dfaccf0f7dd92383304f4a7f008.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03af5f9dfaccf0f7dd92383304f4a7f008.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Faf5f9dfaccf0f7dd92383304f4a7f008.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03af5f9dfaccf0f7dd92383304f4a7f008.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Faf5f9dfaccf0f7dd92383304f4a7f008.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03af5f9dfaccf0f7dd92383304f4a7f008.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Fb5d13764fa9d4c25af3a456a6f994f1a.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03b5d13764fa9d4c25af3a456a6f994f1a.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Fb5d13764fa9d4c25af3a456a6f994f1a.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03b5d13764fa9d4c25af3a456a6f994f1a.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Fb5d13764fa9d4c25af3a456a6f994f1a.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03b5d13764fa9d4c25af3a456a6f994f1a.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Fb5d13764fa9d4c25af3a456a6f994f1a.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03b5d13764fa9d4c25af3a456a6f994f1a.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Fb5d13764fa9d4c25af3a456a6f994f1a.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03b5d13764fa9d4c25af3a456a6f994f1a.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Fb5d13764fa9d4c25af3a456a6f994f1a.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03b5d13764fa9d4c25af3a456a6f994f1a.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Fbbc6433224ceb8807bd0c58079e81f87.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bbc6433224ceb8807bd0c58079e81f87.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Fbbc6433224ceb8807bd0c58079e81f87.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bbc6433224ceb8807bd0c58079e81f87.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Fbbc6433224ceb8807bd0c58079e81f87.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bbc6433224ceb8807bd0c58079e81f87.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Fbbc6433224ceb8807bd0c58079e81f87.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bbc6433224ceb8807bd0c58079e81f87.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Fbbc6433224ceb8807bd0c58079e81f87.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bbc6433224ceb8807bd0c58079e81f87.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Fbbc6433224ceb8807bd0c58079e81f87.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bbc6433224ceb8807bd0c58079e81f87.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Fbbeba1a08be2565d7d22a0f565c4f50f.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bbeba1a08be2565d7d22a0f565c4f50f.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Fbbeba1a08be2565d7d22a0f565c4f50f.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bbeba1a08be2565d7d22a0f565c4f50f.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Fbbeba1a08be2565d7d22a0f565c4f50f.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bbeba1a08be2565d7d22a0f565c4f50f.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Fbbeba1a08be2565d7d22a0f565c4f50f.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bbeba1a08be2565d7d22a0f565c4f50f.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Fbbeba1a08be2565d7d22a0f565c4f50f.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bbeba1a08be2565d7d22a0f565c4f50f.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Fbbeba1a08be2565d7d22a0f565c4f50f.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bbeba1a08be2565d7d22a0f565c4f50f.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Fbdc96880801118cef0c21eb16cc00b8b.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bdc96880801118cef0c21eb16cc00b8b.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Fbdc96880801118cef0c21eb16cc00b8b.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bdc96880801118cef0c21eb16cc00b8b.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Fbdc96880801118cef0c21eb16cc00b8b.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bdc96880801118cef0c21eb16cc00b8b.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Fbdc96880801118cef0c21eb16cc00b8b.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bdc96880801118cef0c21eb16cc00b8b.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Fbdc96880801118cef0c21eb16cc00b8b.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bdc96880801118cef0c21eb16cc00b8b.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Fbdc96880801118cef0c21eb16cc00b8b.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03bdc96880801118cef0c21eb16cc00b8b.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Fc480531ae73ea60d73fbe1e2f3b85264.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03c480531ae73ea60d73fbe1e2f3b85264.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Fc480531ae73ea60d73fbe1e2f3b85264.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03c480531ae73ea60d73fbe1e2f3b85264.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Fc480531ae73ea60d73fbe1e2f3b85264.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03c480531ae73ea60d73fbe1e2f3b85264.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Fc480531ae73ea60d73fbe1e2f3b85264.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03c480531ae73ea60d73fbe1e2f3b85264.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Fc480531ae73ea60d73fbe1e2f3b85264.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03c480531ae73ea60d73fbe1e2f3b85264.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Fc480531ae73ea60d73fbe1e2f3b85264.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03c480531ae73ea60d73fbe1e2f3b85264.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Fc8a17e98b8925756d207969039e06e18.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03c8a17e98b8925756d207969039e06e18.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Fc8a17e98b8925756d207969039e06e18.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03c8a17e98b8925756d207969039e06e18.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Fc8a17e98b8925756d207969039e06e18.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03c8a17e98b8925756d207969039e06e18.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Fc8a17e98b8925756d207969039e06e18.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03c8a17e98b8925756d207969039e06e18.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Fc8a17e98b8925756d207969039e06e18.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03c8a17e98b8925756d207969039e06e18.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Fc8a17e98b8925756d207969039e06e18.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03c8a17e98b8925756d207969039e06e18.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Fd4bfd4a8982121cbbca405cb6ccf5cd9.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03d4bfd4a8982121cbbca405cb6ccf5cd9.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Fd4bfd4a8982121cbbca405cb6ccf5cd9.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03d4bfd4a8982121cbbca405cb6ccf5cd9.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Fd4bfd4a8982121cbbca405cb6ccf5cd9.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03d4bfd4a8982121cbbca405cb6ccf5cd9.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Fd4bfd4a8982121cbbca405cb6ccf5cd9.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03d4bfd4a8982121cbbca405cb6ccf5cd9.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Fd4bfd4a8982121cbbca405cb6ccf5cd9.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03d4bfd4a8982121cbbca405cb6ccf5cd9.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Fd4bfd4a8982121cbbca405cb6ccf5cd9.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03d4bfd4a8982121cbbca405cb6ccf5cd9.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Fdb48458d2a637ad80753c83ed0bab28a.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03db48458d2a637ad80753c83ed0bab28a.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Fdb48458d2a637ad80753c83ed0bab28a.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03db48458d2a637ad80753c83ed0bab28a.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Fdb48458d2a637ad80753c83ed0bab28a.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03db48458d2a637ad80753c83ed0bab28a.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Fdb48458d2a637ad80753c83ed0bab28a.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03db48458d2a637ad80753c83ed0bab28a.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Fdb48458d2a637ad80753c83ed0bab28a.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03db48458d2a637ad80753c83ed0bab28a.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Fdb48458d2a637ad80753c83ed0bab28a.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03db48458d2a637ad80753c83ed0bab28a.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Fdc19b74f8a15fc5669db4c16947aa996.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03dc19b74f8a15fc5669db4c16947aa996.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Fdc19b74f8a15fc5669db4c16947aa996.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03dc19b74f8a15fc5669db4c16947aa996.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Fdc19b74f8a15fc5669db4c16947aa996.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03dc19b74f8a15fc5669db4c16947aa996.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Fdc19b74f8a15fc5669db4c16947aa996.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03dc19b74f8a15fc5669db4c16947aa996.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Fdc19b74f8a15fc5669db4c16947aa996.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03dc19b74f8a15fc5669db4c16947aa996.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Fdc19b74f8a15fc5669db4c16947aa996.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03dc19b74f8a15fc5669db4c16947aa996.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Fec040f288d898a683b5eebb8920ac430.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03ec040f288d898a683b5eebb8920ac430.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Fec040f288d898a683b5eebb8920ac430.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03ec040f288d898a683b5eebb8920ac430.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Fec040f288d898a683b5eebb8920ac430.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03ec040f288d898a683b5eebb8920ac430.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Fec040f288d898a683b5eebb8920ac430.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03ec040f288d898a683b5eebb8920ac430.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Fec040f288d898a683b5eebb8920ac430.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03ec040f288d898a683b5eebb8920ac430.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Fec040f288d898a683b5eebb8920ac430.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03ec040f288d898a683b5eebb8920ac430.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Ff894390b9647ae7fc794030596432074.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03f894390b9647ae7fc794030596432074.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Ff894390b9647ae7fc794030596432074.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03f894390b9647ae7fc794030596432074.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Ff894390b9647ae7fc794030596432074.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03f894390b9647ae7fc794030596432074.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Ff894390b9647ae7fc794030596432074.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03f894390b9647ae7fc794030596432074.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Ff894390b9647ae7fc794030596432074.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03f894390b9647ae7fc794030596432074.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Ff894390b9647ae7fc794030596432074.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03f894390b9647ae7fc794030596432074.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Ffc876267ef840bd0fcca256f6a8bf5e0.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03fc876267ef840bd0fcca256f6a8bf5e0.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Ffc876267ef840bd0fcca256f6a8bf5e0.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03fc876267ef840bd0fcca256f6a8bf5e0.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Ffc876267ef840bd0fcca256f6a8bf5e0.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03fc876267ef840bd0fcca256f6a8bf5e0.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Ffc876267ef840bd0fcca256f6a8bf5e0.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03fc876267ef840bd0fcca256f6a8bf5e0.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Ffc876267ef840bd0fcca256f6a8bf5e0.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03fc876267ef840bd0fcca256f6a8bf5e0.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Ffc876267ef840bd0fcca256f6a8bf5e0.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03fc876267ef840bd0fcca256f6a8bf5e0.mts-jpgbw-360.JPG.info.json",
    "3/taboca_201002_03%2Fff8361e29c43da4b3cfc47b12c3ebe08.mts-jpg-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03ff8361e29c43da4b3cfc47b12c3ebe08.mts-jpg-108.JPG.info.json",
    "3/taboca_201002_03%2Fff8361e29c43da4b3cfc47b12c3ebe08.mts-jpg-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03ff8361e29c43da4b3cfc47b12c3ebe08.mts-jpg-272.JPG.info.json",
    "3/taboca_201002_03%2Fff8361e29c43da4b3cfc47b12c3ebe08.mts-jpg-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03ff8361e29c43da4b3cfc47b12c3ebe08.mts-jpg-360.JPG.info.json",
    "3/taboca_201002_03%2Fff8361e29c43da4b3cfc47b12c3ebe08.mts-jpgbw-108.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03ff8361e29c43da4b3cfc47b12c3ebe08.mts-jpgbw-108.JPG.info.json",
    "3/taboca_201002_03%2Fff8361e29c43da4b3cfc47b12c3ebe08.mts-jpgbw-272.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03ff8361e29c43da4b3cfc47b12c3ebe08.mts-jpgbw-272.JPG.info.json",
    "3/taboca_201002_03%2Fff8361e29c43da4b3cfc47b12c3ebe08.mts-jpgbw-360.JPG/info.json": "tests/fixtures/info/3/taboca_201002_03ff8361e29c43da4b3cfc47b12c3ebe08.mts-jpgbw-360.JPG.info.json",
    "2/youtube-SvH4fbjOT0A%2F34C3_-_International_Image_Interoperability_Framework_IIIF_Kulturinstitutionen_schaffen_interop-SvH4fbjOT0A_thumb.jpg/info.json": "tests/fixtures/info/2/youtube-SvH4fbjOT0A34C3_-_International_Image_Interoperability_Framework_IIIF_Kulturinstitutionen_schaffen_interop-SvH4fbjOT0A_thumb.jpg.info.json",
    "3/youtube-SvH4fbjOT0A%2F34C3_-_International_Image_Interoperability_Framework_IIIF_Kulturinstitutionen_schaffen_interop-SvH4fbjOT0A.jpg/info.json": "tests/fixtures/info/3/youtube-SvH4fbjOT0A34C3_-_International_Image_Interoperability_Framework_IIIF_Kulturinstitutionen_schaffen_interop-SvH4fbjOT0A.jpg.info.json",
    "2/cruz-test%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/2/cruz-test__ia_thumb.jpg.info.json",
    "2/CSPAN3_20180217_164800_Poplar_Forest_Archaeology%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/2/CSPAN3_20180217_164800_Poplar_Forest_Archaeology__ia_thumb.jpg.info.json",
    "2/coitx-Inside_the_Movies_-_Shang-Chi_and_the_Legend_of_the_Ten_Rings%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/2/coitx-Inside_the_Movies_-_Shang-Chi_and_the_Legend_of_the_Ten_Rings__ia_thumb.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_212924454.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_212924454.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213000000.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213000000.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213011321.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213011321.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213040003.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213040003.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213049113.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213049113.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213105589.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213105589.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213117170.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213117170.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213132964.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213132964.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213203031.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213203031.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213505466.MP.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213505466.MP.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213519152.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213519152.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213531256.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213531256.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213547882.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213547882.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213617951.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213617951.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213644096.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213644096.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213656686.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213656686.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250830_213808651.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250830_213808651.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250831_170454806.MP.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250831_170454806.MP.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250831_170503726.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250831_170503726.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250831_170522953.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250831_170522953.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250831_170548817.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250831_170548817.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250831_170602518.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250831_170602518.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250831_170619231.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250831_170619231.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250831_171703452.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250831_171703452.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250831_171709871.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250831_171709871.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250831_190512696.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250831_190512696.jpg.info.json",
    "3/2025-highland-house-walkthrough-ma%2FPXL_20250831_190518116.jpg/info.json": "tests/fixtures/info/3/2025-highland-house-walkthrough-maPXL_20250831_190518116.jpg.info.json",
    "2/DontBeaS1947%2F__ia_thumb.jpg/info.json": "tests/fixtures/info/2/DontBeaS1947__ia_thumb.jpg.info.json",

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
    "BookReaderJSIA.php?id=bub_gb_3Kt5kiw9KYcC": "tests/fixtures/bookreader/bub_gb_3Kt5kiw9KYcC.json",

    # v2 book reader
    "BookReaderJSON.php?itemId=rashodgson68": "tests/fixtures/bookreader/v2_rashodgson68.json",
    "BookReaderJSON.php?itemId=1991-12-compute-magazine": "tests/fixtures/bookreader/v2_1991-12-compute-magazine.json",
    "BookReaderJSON.php?itemId=fbf_3chords_1_": "tests/fixtures/bookreader/v2_fbf_3chords_1_.json",
    "BookReaderJSON.php?itemId=bub_gb_3Kt5kiw9KYcC": "tests/fixtures/bookreader/v2_bub_gb_3Kt5kiw9KYcC.json",
    
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
    "journalofexpedit00ford_djvu.xml": "tests/fixtures/files/journalofexpedit00ford_djvu.xml",
    "CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=0/60": "tests/fixtures/files/0-60_CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt",
    "CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=60/120": "tests/fixtures/files/60-120_CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt",
    "CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=120/180": "tests/fixtures/files/120-180_CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt",
    "CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=180/240": "tests/fixtures/files/180-240_CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt",
    "CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=240/300": "tests/fixtures/files/240-300_CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt",
    "CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=300/360": "tests/fixtures/files/300-360_CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt",
    "CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=360/420": "tests/fixtures/files/360-420_CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt",
    "CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=420/480": "tests/fixtures/files/420-480_CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt",
    "CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=480/540": "tests/fixtures/files/480-540_CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt",
    "CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=540/600": "tests/fixtures/files/540-600_CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt",
    "CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=600/660": "tests/fixtures/files/600-660_CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt",
    "CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=660/720": "tests/fixtures/files/660-720_CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt",
    "CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=720/780": "tests/fixtures/files/720-780_CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt"
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
