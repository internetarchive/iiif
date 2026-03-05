import requests

from .base import BaseManifestBuilder
from .constants import IMG_SRV, URI_PRIFIX, valid_filetypes
from .helpers import singleImage


def checkMultiItem(metadata):
    # Maybe add call to book stack to see if that works first

    # Count the number of each original file
    file_types = {}
    for file in metadata['files']:
        if file['source'] == "original":
            if file['format'] not in file_types:
                file_types[file['format']] = 0

            file_types[file['format']] += 1

    # If there is multiple files of the same type then return the first format
    # Will have to see if there are objects with multiple images and formats
    for format in file_types:
        if file_types[format] > 1 and format.lower() in valid_filetypes:
            return (True, format)

    return (False, None)


class ImageManifestBuilder(BaseManifestBuilder):
    def build_canvases(self, manifest, metadata, identifier, domain, uri, page):
        (multiFile, format) = checkMultiItem(metadata)
        if multiFile:
            # Create multi file manifest
            pageCount = 0
            for file in metadata['files']:
                if file['source'] == "original" and file['format'] == format:
                    imgId = f"{identifier}/{file['name']}".replace('/', '%2f')
                    imgURL = f"{IMG_SRV}/3/{imgId}"
                    pageCount += 1
                    slugged_id = file['name'].replace(" ", "-")

                    try:
                        manifest.make_canvas_from_iiif(
                            url=imgURL,
                            id=f"{URI_PRIFIX}/{identifier}${pageCount}/canvas",
                            label=f"{file['name']}",
                            anno_page_id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/page",
                            anno_id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/annotation"
                        )
                    except requests.exceptions.HTTPError as error:
                        print(f'Failed to get {imgURL}')
                        manifest.make_canvas(label=f"Failed to load {file['name']} from Image Server",
                                             summary=f"Got {error}",
                                             id=f"{URI_PRIFIX}/{identifier}/canvas",
                                             height=1800, width=1200)
        else:
            singleImage(metadata, identifier, manifest, uri)
