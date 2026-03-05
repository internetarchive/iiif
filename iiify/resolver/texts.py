import math
import requests
from urllib.parse import urlparse, parse_qs, quote

from iiif_prezi3 import (
    Canvas, Annotation, AnnotationPage, AnnotationPageRef, AnnotationPageRefExtended,
    AnnotationBody, ServiceV3,
)

from .base import BaseManifestBuilder
from .constants import ARCHIVE, IMG_SRV, URI_PRIFIX
from .helpers import singleImage


def create_canvas_from_br(br_page, zipFile, identifier, pageCount, uri):
    """Create a canvas from Book Reader JSON.
        e.g {
            "width": 1976,
            "height": 2500,
            "uri": "https://ia800309.us.archive.org/BookReader/BookReaderImages.php?zip=/14/items/bub_gb_3Kt5kiw9KYcC/bub_gb_3Kt5kiw9KYcC_jp2.zip&file=bub_gb_3Kt5kiw9KYcC_jp2/bub_gb_3Kt5kiw9KYcC_0000.jp2&id=bub_gb_3Kt5kiw9KYcC",
            "leafNum": 0,
            "pageType": "Normal",
            "pageSide": "R"
        }
    """

    fileUrl = urlparse(br_page['uri'])
    fileName = parse_qs(fileUrl.query).get('file')[0]
    imgId = f"{zipFile}/{fileName}"
    imgURL = f"{IMG_SRV}/3/{quote(imgId, safe='()')}"

    canvas = Canvas(id=f"{URI_PRIFIX}/{identifier}${pageCount}/canvas", label=f"{br_page['leafNum']}")

    body = AnnotationBody(id=f"{imgURL}/full/max/0/default.jpg", type="Image")
    body.format = "image/jpeg"
    body.service = [ServiceV3(id=imgURL, profile="level2", type="ImageService3")]

    annotation = Annotation(id=f"{uri}/annotation/{pageCount}", motivation='painting', body=body, target=canvas.id)

    annotationPage = AnnotationPage(id=f"{uri}/annotationPage/{pageCount}")
    annotationPage.add_item(annotation)

    canvas.add_item(annotationPage)
    canvas.set_hwd(br_page['height'], br_page['width'])

    return canvas


class TextsManifestBuilder(BaseManifestBuilder):
    def build_canvases(self, manifest, metadata, identifier, domain, uri, page):
        subprefix = identifier
        djvuFile = ""
        for fileMd in metadata['files']:
            if fileMd['name'].endswith('_scandata.xml'):
                subprefix = fileMd['name'].replace('_scandata.xml', '')
            if fileMd['format'] == 'Djvu XML':
                djvuFile = fileMd['name']

        bookReaderURL = f"https://{metadata.get('server')}/BookReader/BookReaderJSIA.php?id={identifier}&itemPath={metadata.get('dir')}&server={metadata.get('server')}&format=jsonp&subPrefix={subprefix}"

        bookreader_data = requests.get(bookReaderURL).json()
        if 'error' in bookreader_data:
            # Image stack not found. Maybe a single image
            singleImage(metadata, identifier, manifest, uri)
        else:
            pageCount = 0
            # In json: /29/items/goody/goody_jp2.zip convert to goody/good_jp2.zip
            zipFile = '/'.join(bookreader_data['data']['brOptions']['zip'].split('/')[-2:])

            # Single page of a manifest requested
            if page:
                # Book reader supplies pages in spread form
                # e.g. opening, page1 + page2, page3 + page4, end page
                # this removes the first page divides by 2 to find the spread
                # then adds one back to get the index.
                spread = math.floor((page - 1) / 2) + 1
                canvas = create_canvas_from_br(
                    bookreader_data['data']['brOptions']['data'][spread][(page + 1) % 2],
                    zipFile, identifier, pageCount, uri
                )
                manifest.add_item(canvas)
            else:
                for pageSpread in bookreader_data['data']['brOptions']['data']:
                    for pg in pageSpread:
                        canvas = create_canvas_from_br(pg, zipFile, identifier, pageCount, uri)
                        manifest.add_item(canvas)
                        pageCount += 1

            # Setting logic for paging behavior and starting canvases
            # Start with paged (default) or individual behaviors
            try:
                if bookreader_data['data']['brOptions']['defaults'] == "mode/1up":
                    manifest.behavior = "individuals"
            except:
                manifest.behavior = "paged"

            # Then set left-to-right or right-to-left if present
            try:
                viewingDirection = None
                if bookreader_data['data']['brOptions']['pageProgression'] == "lr":
                    viewingDirection = "left-to-right"
                elif bookreader_data['data']['brOptions']['pageProgression'] == "rl":
                    viewingDirection = "right-to-left"
                if viewingDirection:
                    manifest.viewingDirection = viewingDirection
            except:
                pass

        # Add annotations if djvu file is present
        if djvuFile:
            # Add search service
            service = {
                "@context": "http://iiif.io/api/search/1/context.json",
                "@id": f"{domain}search/{identifier}",
                "@type": "SearchService1",
                "profile": "http://iiif.io/api/search/1/search"
            }
            if manifest.service:
                manifest.service.append(service)
            else:
                manifest.service = [service]

            count = 1
            for canvas in manifest.items:
                if 'annotations' in canvas:
                    annotations = canvas.annotations
                else:
                    annotations = []

                annotations.append(
                    AnnotationPageRef(__root__=AnnotationPageRefExtended(
                        id=f"{domain}3/annotations/{identifier}/{quote(djvuFile, safe='()')}/{count}.json",
                        type="AnnotationPage"
                    ))
                )
                canvas.annotations = annotations

                count += 1
