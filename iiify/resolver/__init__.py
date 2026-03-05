import json
import math
import os
import re
import requests
import xml.etree.ElementTree as ET
from datetime import timedelta
from urllib.parse import quote

from iiif_prezi3 import (
    config, Collection, Manifest, Canvas, Annotation, AnnotationPage,
    CollectionRef, ManifestRef, AnnotationPageRef, AnnotationPageRefExtended,
    AnnotationBody, ServiceV3, Choice, TextualBody,
)

from .constants import (
    SCRAPE_API, ADVANCED_SEARCH, IMG_CTX, PRZ_CTX, ARCHIVE, IMG_SRV,
    METADATA_FIELDS, bookdata, bookreader, URI_PRIFIX,
    MAX_SCRAPE_LIMIT, MAX_API_LIMIT,
    valid_filetypes, AUDIO_FORMATS, VIDEO_FORMATS,
)
from .utils import (
    MaxLimitException, purify_domain, scrape, search, to_mimetype,
    coerce_list, valid_filetype, ia_resolver, infojson, cantaloupe_resolver,
)
from .helpers import (
    sanitize_html, addMetadata, addSeeAlso, addWaveform, addRendering,
    addThumbnails, addThumbnailNav, addPartOfCollection, sortDerivatives, singleImage,
)
from .texts import TextsManifestBuilder, create_canvas_from_br
from .image import ImageManifestBuilder, checkMultiItem
from .audio import AudioManifestBuilder
from .video import VideoManifestBuilder

from ..configs import options, cors, approot, cache_root, media_root, apiurl, LINKS


class IsCollection(Exception):
    # Used for when we need to raise to the route handler from inside the manifest function
    pass

_BUILDERS = {
    'texts':  TextsManifestBuilder,
    'image':  ImageManifestBuilder,
    'audio':  AudioManifestBuilder,
    'etree':  AudioManifestBuilder,
    'movies': VideoManifestBuilder,
}


def create_manifest3(identifier, domain=None, page=None):
    # Get item metadata
    metadata = requests.get('%s/metadata/%s' % (ARCHIVE, identifier)).json()

    mediatype = metadata['metadata']['mediatype']

    if mediatype == 'collection':
        raise IsCollection

    builder_class = _BUILDERS.get(mediatype)
    if not builder_class:
        print(f'Unknown mediatype "{mediatype}"')
        raise ValueError(f'Unknown mediatype: {mediatype}')

    return builder_class().build(identifier, domain, page, metadata=metadata)


def create_collection3(identifier, domain, page=1, rows=MAX_API_LIMIT):
    # Get item metadata
    metadata = requests.get('%s/metadata/%s' % (ARCHIVE, identifier)).json()

    # Used to build up URIs for the manifest
    uri = f"{domain}{identifier}/collection.json"

    config.configs['helpers.auto_fields.AutoLang'].auto_lang = "none"
    collection = Collection(id=uri, label=metadata["metadata"]["title"])

    addMetadata(collection, identifier, metadata['metadata'], collection=True)
    addPartOfCollection(collection, metadata.get('metadata').get('collection', []), domain)

    asURL = f'{ADVANCED_SEARCH}?q=collection%3A{identifier}&fl[]=identifier&fl[]=mediatype&fl[]=title&fl[]=description&sort[]=&sort[]=&sort[]=&rows={rows}&page={page}&output=json&save=yes'
    itemsSearch = requests.get(asURL).json()
    total = itemsSearch['response']['numFound']
    # There is a max of 10,000 items that can be retrieved from the advanced search
    if total > MAX_SCRAPE_LIMIT:
        total = MAX_SCRAPE_LIMIT

    if len(itemsSearch['response']['docs']) == 0:
        return None

    pages = math.ceil(total / rows)
    for item in itemsSearch['response']['docs']:
        if item['mediatype'] == 'collection':
            child = CollectionRef(id=f"{domain}{item['identifier']}/collection.json", type="Collection", label=item['title'])
        else:
            child = ManifestRef(id=f"{domain}{item['identifier']}/manifest.json", type="Manifest", label=item['title'])

        if "description" in item:
            child.summary = {"none": [item['description']]}

        collection.add_item(child)
    page += 1
    if page <= pages:
        child = CollectionRef(id=f"{domain}{identifier}/{page}/collection.json", type="Collection", label={"en": [f"Page {page} of {pages}"]})
        collection.add_item(child)

    return json.loads(collection.jsonld())


def create_annotations(version: int, identifier: str, fileName: str, canvas_no: int, domain: str | None = None):
    annotationPage = AnnotationPage(
        id=f"{domain}{version}/annotations/{identifier}/{quote(fileName, safe='()')}/{canvas_no}.json"
    )
    annotationPage.items = []
    index = canvas_no - 1
    url = f"{ARCHIVE}/download/{identifier}/{fileName}"
    try:
        # Fetch the remote XML file
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the XML content
        djfu = ET.fromstring(response.content)
        page = djfu.findall(f".//OBJECT[{canvas_no}]")[0]
        words = page.findall(".//WORD")
        count = 1
        for word in words:
            # <WORD coords="444,1353,635,1294" x-confidence="10">[David </WORD>
            # <WORD coords="lx,by,rx,ty" x-confidence="10">[David </WORD>
            # x = lx
            # y = ty
            # w = rx - lx
            # h = by - ty
            (left_x, bottom_y, right_x, top_y) = word.attrib['coords'].split(',')
            x = left_x
            y = top_y
            width = int(right_x) - int(left_x)
            height = int(bottom_y) - int(top_y)
            annotationPage.items.append({
                "id": f"https://iiif.archive.org/iiif/{identifier}/canvas/{index}/anno/{count}",
                "type": "Annotation",
                "motivation": "supplementing",
                "body": {
                    "type": "TextualBody",
                    "format": "text/plain",
                    "value": word.text
                },
                "target": f"https://iiif.archive.org/iiif/{identifier}${index}/canvas#xywh={x},{y},{width},{height}"
            })
            count += 1

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the XML file: {e}")
        raise ValueError("Failed to retrieve {url}")
    except ET.ParseError as e:
        print(f"Error parsing the XML content: {e}")
        raise ValueError("Failed to process {url}")

    return json.loads(annotationPage.jsonld())


def create_annotations_from_comments(identifier, domain=None):
    annotation_page = AnnotationPage(
        id=f"{domain}3/annotations/{identifier}/comments.json"
    )
    metadata = requests.get('%s/metadata/%s' % (ARCHIVE, identifier)).json()
    i = 0
    for comment in metadata.get('reviews', []):
        anno_body = TextualBody(
            type="TextualBody",
            language="none",
            format="text/html",
            value=f"<span><p>{comment.get('reviewtitle')}:</p><p>{comment.get('reviewbody')}</p></span>"
        )
        anno = Annotation(
            id=f"{domain}3/annotations/{identifier}/comments/{i}",
            motivation="commenting",
            body=anno_body,
            target=f"{domain}3/{identifier}/manifest.json"
        )
        annotation_page.add_item(anno)
        i += 1
    return json.loads(annotation_page.jsonld())


def _formatTimeVTT(time):
    hours, remainder = divmod(time.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}.{int(time.microseconds / 1000):03}"


def _timeToDelta(time):
    """
    Convert SRT formated times to timedelta
    """
    milliseconds = int(time.split(",")[1])
    timeStr = time.split(",")[0]
    hour = int(timeStr.split(":")[0])
    minute = int(timeStr.split(":")[1])
    second = int(timeStr.split(":")[2])
    return timedelta(hours=hour, minutes=minute, seconds=second, milliseconds=milliseconds)


def create_vtt_stream(identifier):
    """
    This method will read a SRT file using the following URL:
    https://archive.org/download/CSPAN3_20180217_164800_Poplar_Forest_Archaeology/CSPAN3_20180217_164800_Poplar_Forest_Archaeology.cc5.srt?t=0/360
    and convert it to vtt. The streaming text above takes seconds as a parameter.
    """

    metadata = requests.get('%s/metadata/%s' % (ARCHIVE, identifier)).json()
    filename = ""
    duration = 0.0
    for file in metadata['files']:
        if file['name'].endswith('.mpg') and file['source'] == 'original':
            duration = float(file['length'])
        # There seems to be multiple srt files but unclear how they are different
        if file['name'].endswith('.srt'):
            filename = file['name']

    # Initialize the vtt content with the WEBVTT header
    vtt_content = ["WEBVTT\n"]

    segments = math.floor(duration / 60)
    for i in range(segments):
        start = i * 60
        if i == segments - 1:
            end = int(duration)
        else:
            end = (i + 1) * 60

        response = requests.get(f"https://archive.org/download/{identifier}/{filename}?t={start}/{end}")

        if response.status_code == 200:
            # Get the content of the SRT file as a string
            srt_content = response.text
            # Split the srt file by lines
            lines = srt_content.splitlines()
            for line in lines:
                # Convert time format: 00:00:00,000 -> 00:00:00.000
                if "-->" in line:
                    splitline = line.split("-->")
                    starttime = _timeToDelta(splitline[0].strip()) + timedelta(seconds=start)
                    endtime = _timeToDelta(splitline[1].strip()) + timedelta(seconds=start)
                    line = f"{_formatTimeVTT(starttime)} --> {_formatTimeVTT(endtime)}"

                vtt_content.append(line)

            vtt_content.append("")

    # Join the list into a single string
    return "\n".join(vtt_content)


def collection(domain, identifiers, label='Custom Archive.org IIIF Collection'):
    cs = {
        '@context': PRZ_CTX,
        '@id': "%scollection.json" % domain,
        '@type': 'sc:Collection',
        'label': label,
        'collections': []
    }
    for i in identifiers:
        cs['collections'].append({
            '@id': '%s%s/manifest.json' % (domain, i),
            '@type': 'sc:Manifest',
            'label': label,
            'description': label
        })
    return cs


def manifest_page(identifier, label='', page='', width='', height='', metadata=None, canvasId=""):
    if not canvasId:
        canvasId = f"{identifier}/canvas"

    metadata = metadata or {}
    return {
        '@id': canvasId,
        '@type': 'sc:Canvas',
        '@context': PRZ_CTX,
        'description': metadata.get('description', ''),
        'label': label or 'p. ' + str(page),
        'width': width,
        'height': height,
        'images': [{
            '@type': 'oa:Annotation',
            '@context': IMG_CTX,
            '@id': '%s/annotation' % identifier,
            'on': '%s/annotation' % identifier,
            'motivation': "sc:painting",
            'resource': {
                '@id': '%s/full/full/0/default.jpg' % identifier,
                '@type': 'dctypes:Image',
                'width': width,
                'height': height,
                'format': 'image/jpeg',
                'service': {
                    '@context': IMG_CTX,
                    '@id': identifier,
                    'profile': 'https://iiif.io/api/image/2/profiles/level2.json',
                }
            }
        }]
    }


def create_manifest(identifier, domain=None, page=None):
    path = os.path.join(media_root, identifier)
    resp = requests.get('%s/metadata/%s' % (ARCHIVE, identifier)).json()
    metadata = resp.get("metadata", {})

    manifest = {
        '@context': PRZ_CTX,
        '@id': '%s2/%s/manifest.json' % (domain, identifier),
        '@type': 'sc:Manifest',
        'description': metadata.get('description', ''),
        'logo': 'https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcReMN4l9cgu_qb1OwflFeyfHcjp8aUfVNSJ9ynk2IfuHwW1I4mDSw',
            'sequences': [
                {
                    '@id': '%s%s/canvas/default' % (domain, identifier),
                    '@type': 'sc:Sequence',
                    '@context': IMG_CTX,
                    'label': 'default',
                    'canvases': []
                }
            ],
        'viewingHint': 'paged',
        'attribution': "The Internet Archive",
        'seeAlso': '%s/metadata/%s' % (ARCHIVE, identifier)
    }

    mediatype = metadata.get("mediatype")

    if 'title' in metadata:
        manifest['label'] = metadata['title']
    if 'identifier-access' in metadata:
        manifest['related'] = metadata['identifier-access']
    if 'description' in metadata:
        manifest['description'] = coerce_list(metadata['description'])

    manifest['metadata'] = [{"label": field, "value": coerce_list(metadata[field])}
                            for field in METADATA_FIELDS if metadata.get(field)]

    if page and mediatype is None:
        mediatype = 'image'

    if "$" not in identifier:
        filepath = None
    else:
        identifier, filepath = identifier.split("$", 1)
        filepath = filepath.replace("$", os.sep)

    if mediatype.lower() == 'image' or (
        filepath and mediatype.lower() != 'texts'
    ):
        info = infojson(identifier, metadata=resp)
        manifest['sequences'][0]['canvases'].append(
            manifest_page(
                identifier=info['@id'],
                label=metadata['title'],
                width=info['width'],
                height=info['height'],
                metadata=metadata,
                canvasId=f"https://iiif.archivelab.org/iiif/{identifier}/canvas"
            )
        )

    elif mediatype.lower() == 'texts':
        subPrefix = resp['dir']
        server = resp.get('server', ARCHIVE)

        # XXX Use https://api.archivelab.org/books/:id/metadata API

        r = requests.get(bookdata % server, params={
            'server': server,
            'itemPath': subPrefix,
            'itemId': identifier
        })
        if r.status_code != 200:
            # If the bookdata failed then treat as a single image
            info = infojson(identifier, metadata=resp)
            manifest['sequences'][0]['canvases'].append(
                manifest_page(
                    identifier=info['@id'],
                    label=metadata['title'],
                    width=info['width'],
                    height=info['height'],
                    metadata=metadata,
                    canvasId=f"https://iiif.archivelab.org/iiif/{identifier}/canvas"
                )
            )
        else:
            data = r.json()

            manifest.update({
                'label': data['title'],
                'thumbnail': {
                    '@id': data['previewImage']
                },
            })

            if page:
                manifest['sequences'][0]['canvases'].append(
                    manifest_page(
                        identifier=f"{IMG_SRV}/2/{cantaloupe_resolver(f'{identifier}${page}', metadata=resp)}",
                        label=data['pageNums'][page],
                        width=data['pageWidths'][page],
                        height=data['pageHeights'][page],
                        canvasId=f"https://iiif.archivelab.org/iiif/{identifier}${page}/canvas"
                    )
                )
                return manifest

            for page in range(0, len(data.get('leafNums', []))):
                manifest['sequences'][0]['canvases'].append(
                    manifest_page(
                        identifier=f"{IMG_SRV}/2/{cantaloupe_resolver(f'{identifier}${page}', metadata=resp)}",
                        label=data['pageNums'][page],
                        width=data['pageWidths'][page],
                        height=data['pageHeights'][page],
                        canvasId=f"https://iiif.archivelab.org/iiif/{identifier}${page}/canvas"
                    )
                )
    return manifest
