import re
import requests
from urllib.parse import quote

import bleach
from bs4 import BeautifulSoup
from iiif_prezi3 import (
    Canvas, Annotation, AnnotationPage, CanvasRef, AnnotationBody,
    ServiceV3, Range, AccompanyingCanvas,
)

from .constants import ARCHIVE, IMG_SRV, URI_PRIFIX
from .utils import valid_filetype
from ..configs import LINKS


def sanitize_html(value):
    allowed_tags = ['a', 'b', 'br', 'i', 'img', 'p', 'small', 'span', 'sub', 'sup']
    allowed_attributes = {
        'a': ['href', 'rel'],
        'img': ['src', 'alt', 'title'],
        '*': []
    }
    cleaned = bleach.clean(
        value,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True,
        strip_comments=True
    )
    soup = BeautifulSoup(cleaned, 'html.parser')

    # If it's wrapped in a parent </p> just return the cleaned value in the parent
    top_level_elements = [el for el in soup.contents if not str(el).isspace()]
    if len(top_level_elements) == 1 and getattr(top_level_elements[0], 'name', None) == 'p':
        return cleaned

    # Otherwise, if there is allowed HTML present, take the cleaned thing and wrap in it a <p/> to ensure it's well formed
    contains_html = any(tag.name in allowed_tags for tag in soup.find_all())
    if contains_html:
        return f"<p>{cleaned}</p>"

    # Finally, just make sure no disallowed HTML is present
    return cleaned


def addMetadata(item, identifier, metadata, collection=False):
    item.homepage = [{"id": f"https://archive.org/details/{identifier}",
                         "type": "Text",
                         "label": {"en": ["Item Page on Internet Archive"]},
                         "format": "text/html"}]

    item.provider = [{"id": "https://archive.org",
                         "type": "Agent",
                         "label": {"en": ["The Internet Archive"]},
                      "homepage": [{"id": "https://archive.org",
                         "type": "Text",
                         "label": {"en": ["Internet Archive Homepage"]},
                         "format": "text/html"}],
                      "logo": [{
                          "id": "https://archive.org/images/glogo.png",
                          "type": "Image",
                          "format": "image/png",
                          "height": 79,
                          "width": 79
                            }],
                         }]

    if "licenseurl" in metadata:
        item.rights = metadata["licenseurl"].replace("https", "http", 1)

    if "description" in metadata:
        if not isinstance(metadata["description"], list):
            item.summary = [sanitize_html(metadata["description"])]
        else:
            item.summary = {"none": [sanitize_html(d) for d in metadata["description"]]}

    excluded_fields = [
        'avg_rating', 'backup_location', 'btih', 'description', 'downloads',
        'imagecount', 'indexflag', 'item_size', 'licenseurl', 'curation',
        'noindex', 'num_reviews', 'oai_updatedate', 'publicdate', 'publisher', 'reviewdate',
        'scanningcentre', 'stripped_tags', 'uploader'
    ]

    manifest_metadata = []

    for field in metadata:
        if field not in excluded_fields:
            if type(metadata[field]) != list:
                metadata_value = [str(metadata[field])]
            else:
                metadata_value = metadata[field]
            manifest_metadata.append(
                {"label": {"none": [field]}, "value": {"none": metadata_value}})

    item.metadata = manifest_metadata


def addSeeAlso(manifest, identifier, files):
    manifest.seeAlso = [
        {"id": f"{ARCHIVE}/metadata/{identifier}",
         "type": "Metadata",
         "label": {"en": ["Item Metadata"]},
         "format": "application/json"}
    ]

    for file in files:
        if file['format'] in LINKS and LINKS[file['format']]['field'] == 'seeAlso':
            seeAlso = LINKS[file['format']]
            manifest.seeAlso.append(
                {"id": f"{ARCHIVE}/download/{identifier}/{file['name']}",
                 "type": seeAlso['type'],
                 "label": {"en": [file["format"]]},
                 "format": seeAlso['format']
                 })


def addWaveform(identifier, slugged_id, filename, hard_code_size=True):
    """
        Create an IIIF AccompanyingCanvas representing a waveform image.

        This function generates an IIIF AccompanyingCanvas containing a waveform image,
        associated with an audio file. By default, the image dimensions are hardcoded,
        but if `hard_code_size` is False, the image's width and height will be retrieved
        dynamically from a IIIF image server.

        Parameters:
            identifier (str): The archive.org identifier for the resource (e.g. item ID).
            slugged_id (str): A slugified version of the identifier used in the canvas ID.
            filename (str): The filename of the waveform image (PNG).
            hard_code_size (bool): If True, sets the image size to 800x200; if False, fetches dimensions from IIIF image server.

        Returns:
            AccompanyingCanvas: An IIIF-compliant AccompanyingCanvas object representing the waveform image.
    """

    # This should be the Wave form
    accompanying_canvas = AccompanyingCanvas(
        id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/canvas/accompanying",
        label={"en": ["Waveform"]}
    )
    if hard_code_size:
        width = 800
        height = 200
        body = AnnotationBody(id=f"https://archive.org/download/{identifier}/{filename.replace(' ', '%20')}", type="Image", width=width, height=height)
        body.format = "image/jpeg"
    else:
        imgId = f"{identifier}/{filename}".replace('/', '%2f')
        imgURL = f"{IMG_SRV}/3/{imgId}".replace(' ', '%20')
        # Find the width and height from the image server
        body = AnnotationBody(id="http://example.com", type="Image")
        infoJson = body.set_hwd_from_iiif(imgURL)

        service = ServiceV3(id=infoJson['id'], profile=infoJson['profile'], type=infoJson['type'])
        body.service = [service]
        body.id = f'{infoJson["id"]}/full/max/0/default.jpg'
        body.format = "image/jpeg"

        width = infoJson['width']
        height = infoJson['height']

    annotation = Annotation(id=f"{accompanying_canvas.id}/anno", motivation='painting', body=body, target=accompanying_canvas.id)

    annotationPage = AnnotationPage(id=f"{accompanying_canvas.id}/annoPage")
    annotationPage.add_item(annotation)

    accompanying_canvas.add_item(annotationPage)
    accompanying_canvas.height = height
    accompanying_canvas.width = width

    return accompanying_canvas


def addRendering(manifest, identifier, files):
    manifest.rendering = []

    for file in files:
        if file['format'] in LINKS and LINKS[file['format']]['field'] == 'rendering':
            rendering = LINKS[file['format']]
            manifest.rendering.append(
                {"id": f"{ARCHIVE}/download/{identifier}/{file['name']}",
                 "type": rendering['type'],
                 "label": {"en": [file["format"]]},
                 "format": rendering['format']
                 })


def addThumbnails(manifest, identifier, files):
    """Creates thumbnails based on files.

    If the file appears to be a thumbnail (by format or name) attempt to create a IIIF thumbnail via Cantaloupe.
    If that fails or isn't possible, fall back to adding a static thumbnail.
    """
    thumbnail_files = []
    ia_thumb_files = []

    for file in files:
        name = file.get("name", "")
        file_format = file.get("format", "")

        if name == "__ia_thumb.jpg":
            ia_thumb_files.append(file)
        # ignore thumbnails in .thumbs as these are for video thumbnail navigation
        elif file_format in {"Thumbnail", "JPEG Thumb"} and f"{identifier}.thumbs" not in name:
            thumbnail_files.append(file)

    files_to_process = []

    if thumbnail_files:
        files_to_process = thumbnail_files

    elif ia_thumb_files:
        files_to_process = ia_thumb_files

    for file in files_to_process:
        name = file.get("name", "")
        encoded_name = quote(name.replace('/', '%2f'))
        # Forward solidus before thumbnail uri must always be %2f
        iiif_url = f"{IMG_SRV}/2/{identifier.strip()}%2f{encoded_name}"
        try:
            manifest.create_thumbnail_from_iiif(iiif_url)
        except requests.HTTPError:
            print(f"Failed to generate thumbnail from Cantaloupe: {iiif_url}")
            mimetype = "image/png" if name.endswith(".png") else "image/jpeg"
            static_url = f"{ARCHIVE}/download/{quote(identifier)}/{quote(name)}"
            manifest.add_thumbnail(static_url, format=mimetype)
    return


def addThumbnailNav(manifest, identifier, files):
    """Creates thumbnails navigation for Videos.

    If the file appears to be a thumbnail (by format or name) attempt to create a IIIF thumbnail via Cantaloupe.
    If that fails or isn't possible, fall back to adding a static thumbnail.
    """

    nav_thumbs = {}
    # Organise thumbs by original file as this is used for the canvas id.
    # This in case an item had two videos and different thumbnails for each
    for thumb in files:
        if ".thumbs" in thumb['name'] and thumb['format'] == "Thumbnail":
            if thumb['original'] not in nav_thumbs:
                nav_thumbs[thumb['original']] = []

            nav_thumbs[thumb['original']].append(thumb)

    if manifest.structures is None or not isinstance(manifest.structures, list):
        manifest.structures = []

    for original in nav_thumbs:
        normalised_id = original.rsplit(".", 1)[0]
        slugged_id = normalised_id.replace(" ", "-")

        thumb_nav_range = Range(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/thumbnails")
        thumb_nav_range.label = {"en": ["Thumbnail Navigation"]}
        thumb_nav_range.behavior = "thumbnail-nav"
        thumb_nav_range.items = []

        count = 0
        last = 0
        for thumb in nav_thumbs[original]:
            # Filename example: CSPAN3_20180217_164800_Poplar_Forest_Archaeology_000237.jpg
            # Pull out number at the end
            current = int(thumb['name'].rsplit("_", 1)[-1].split(".")[0])
            section = Range(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/thumbnails/{count}")
            section.items = [CanvasRef(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/canvas#t={last},{current}", type="Canvas")]
            section.thumbnail = [{
                "id": f"https://archive.org/download/{identifier}/{thumb['name'].replace(' ', '%20')}",
                "type": "Image",
                "format": "image/png",
                "height": 110,
                "width": 160
                }]

            thumb_nav_range.items.append(section)
            last = current
            count += 1

        manifest.structures.append(thumb_nav_range)


def addPartOfCollection(resource, collections, domain=None):
    # metadata["collections"] can be a list or str so we need to test what we have
    if isinstance(collections, list):
        parents = []
        for collection in collections:
            parents.append(
                {
                    "id": f"{domain}{collection}/collection.json",
                    "type": "Collection"
                }
            )
        resource.partOf = parents
    elif isinstance(collections, str):
        resource.partOf = [
            {
                "id": f"{domain}{collections}/collection.json",
                "type": "Collection"
            }
        ]


def sortDerivatives(metadata, includeVtt=False):
    """
        Sort the files into originals and derivatives, splitting the derivatives into buckets based on the original
    """
    originals = []
    derivatives = {}
    vttfiles = {}
    for f in metadata['files']:
        if f['source'] == 'derivative':
            if f['original'] in derivatives and not isinstance(f['original'], list):
                derivatives[f['original']][f['format']] = f
            else:
                derivatives[f['original']] = {f['format']: f}
        elif f['source'] == 'original':
            originals.append(f)

        if includeVtt and f['format'] == 'Web Video Text Tracks':
            # Example: cruz-test.en.vtt and 34C3_-_International_Image_Interoperability_Framework_IIIF_Kulturinstitutionen_schaffen_interop-SvH4fbjOT0A.autogenerated.vtt
            sourceFilename = re.sub(r'\.[a-zA-H-]*\.vtt', '', f['name'])
            if sourceFilename not in vttfiles:
                vttfiles[sourceFilename] = []

            vttfiles[sourceFilename].append(f)

    if includeVtt:
        return (originals, derivatives, vttfiles)
    else:
        return (originals, derivatives)


def singleImage(metadata, identifier, manifest, uri):
    fileName = ""
    for f in metadata['files']:
        if valid_filetype(f['name']) \
            and f['source'].lower() == 'original' \
            and 'thumb' not in f['name']:
            fileName = f['name']
            break

    if not fileName:
        # Original wasn't an image
        for f in metadata['files']:
            if '_jp2.zip' in f['name']:
                fileName = f"{f['name']}/{f['name'].replace('.zip','')}/{f['name'].replace('jp2.zip','0000.jp2')}"

    imgId = f"{identifier}/{fileName}".replace('/', '%2f')
    imgURL = f"{IMG_SRV}/3/{imgId}"

    manifest.make_canvas_from_iiif(url=imgURL,
                                    id=f"{URI_PRIFIX}/{identifier}/canvas",
                                    label="1",
                                    anno_page_id=f"{uri}/annotationPage/1",
                                    anno_id=f"{uri}/annotation/1")
