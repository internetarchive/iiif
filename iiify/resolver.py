#!/usr/bin/env python

import os
import requests
from .configs import options, cors, approot, cache_root, media_root, apiurl, LINKS
from iiif_prezi3 import Manifest, config, Annotation, AnnotationPage,AnnotationPageRef, Canvas, Manifest, ResourceItem, ServiceItem, Choice, Collection, ManifestRef, CollectionRef
from urllib.parse import urlparse, parse_qs, quote
import json
import math
import re
import xml.etree.ElementTree as ET
from datetime import timedelta

SCRAPE_API = 'https://archive.org/services/search/v1/scrape'
ADVANCED_SEARCH = 'https://archive.org/advancedsearch.php'
IMG_CTX = 'http://iiif.io/api/image/2/context.json'
PRZ_CTX = 'http://iiif.io/api/presentation/2/context.json'
ARCHIVE = 'https://archive.org'
IMG_SRV = 'https://iiif.archive.org/image/iiif'
METADATA_FIELDS = ("title", "volume", "publisher", "subject", "date", "contributor", "creator")
bookdata = 'https://%s/BookReader/BookReaderJSON.php'
bookreader = "https://%s/BookReader/BookReaderImages.php"
URI_PRIFIX = "https://iiif.archive.org/iiif"
MAX_SCRAPE_LIMIT = 10_000
MAX_API_LIMIT = 1_000

class MaxLimitException(Exception):
    pass

valid_filetypes = ['jpg', 'jpeg', 'png', 'gif', 'tif', 'jp2', 'pdf', 'tiff']
AUDIO_FORMATS = ['VBR MP3', '32Kbps MP3', '56Kbps MP3', '64Kbps MP3', '96Kbps MP3', '128Kbps MP3', 'MPEG-4 Audio', 'Flac', 'AIFF', 'Apple Lossless Audio', 'Ogg Vorbis', 'WAVE', '24bit Flac', 'Shorten']
VIDEO_FORMATS = ['MPEG4', 'h.264 HD', 'h.264 MPEG4', '512Kb MPEG4', 'HiRes MPEG4', 'MPEG2', 'h.264', 'Matroska', 'Ogg Video', 'Ogg Theora', 'WebM', 'Windows Media', 'Cinepack','QuickTime']

class IsCollection(Exception):
    # Used for when we need to raise to the route handler from inside the manifest function
    pass

def purify_domain(domain):
    domain = re.sub(r'^http:\/\/', "https://", domain)
    return domain if domain.endswith('/iiif/') else domain + 'iiif/'


def scrape(query, fields="", sorts="", count=100, cursor="", restrict_to_iiif=False, security=True):
    """
    params:
        query: the query (using the same query Lucene-like queries supported by Internet Archive Advanced Search.
        fields: Metadata fields to return, comma delimited
        sorts: Fields to sort on, comma delimited (if identifier is specified, it must be last)
        count: Number of results to return (minimum of 100)
        cursor: A cursor, if any (otherwise, search starts at the beginning)
        restrict_to_iiif: restrict query to supported IIIF collections?
        security: enforce API page limit
    """
    if restrict_to_iiif or not query:
        _query = "(mediatype:(texts) OR mediatype:(image))"
        query = f"{_query} AND {query}" if query else _query

    if int(count) > MAX_API_LIMIT and security:
        raise MaxLimitException(f"Limit may not exceed {MAX_API_LIMIT}.")

    fields = fields or 'identifier,title'

    params = {
        'q': query
    }
    if sorts:
        params['sorts'] = sorts
    if fields:
        params['fields'] = fields
    if count:
        params['count'] = count
    if cursor:
        params['cursor'] = cursor

    r = requests.get(SCRAPE_API, params=params)
    return r.json()

def search(query, page=1, limit=100, security=True, sort=None, fields=None):
    if not query:
        raise ValueError("GET query parameters 'q' required")

    if int(limit) > MAX_API_LIMIT and security:
        raise MaxLimitException(f"Limit may not exceed {MAX_API_LIMIT}.")

    return requests.get(
        ADVANCED_SEARCH,
        params={'q': query,
                'sort[]': sort or ['date asc', 'createdate'],
                'rows': limit,
                'page': page,
                'fl[]': fields or 'identifier,title',
                'output': 'json',
            }).json()

def checkMultiItem(metadata):
    # Maybe add call to book stack to see if that works first

    # Count the number of each original file
    file_types = {}
    for file in metadata['files']:
        if file['source'] == "original":
            if file['format'] not in file_types:
                file_types[file['format']] = 0

            file_types[file['format']] += 1
    #print (file_types)

    # If there is multiple files of the same type then return the first format
    # Will have to see if there are objects with multiple images and formats
    for format in file_types:
        if file_types[format] > 1 and format.lower() in valid_filetypes:
            return (True, format)

    return (False, None)

def to_mimetype(format):
    formats = {
        "VBR MP3": "audio/mp3",
        "32Kbps MP3": "audio/mp3",
        "56Kbps MP3": "audio/mp3",
        "64Kbps MP3": "audio/mp3",
        "96Kbps MP3": "audio/mp3",
        "128Kbps MP3": "audio/mp3",
        "Flac": "audio/flac",
        "Ogg Vorbis": "audio/ogg",
        "Ogg Video": "video/ogg",
        "WAVE": "audio/wav",
        "MPEG4": "video/mp4",
        "24bit Flac": "audio/flac",
        'Shorten': "audio/shn",
        "MPEG2": "video/mpeg",
        "512Kb MPEG4": "video/mpeg",
        "HiRes MPEG4": "video/mpeg",
        "h.264 MPEG4": "video/mpeg",
        "h.264": "video/mpeg",
        "h.264 HD": "video/mp4",
        "Matroska": "video/x-matroska",
        "Cinepack": "video/x-msvideo",
        "AIFF": "audio/aiff",
        "Apple Lossless Audio": "audio/x-m4a",
        "MPEG-4 Audio": "audio/mp4"
    }
    return formats.get(format, "application/octet-stream")

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

def create_collection3(identifier, domain, page=1, rows=MAX_API_LIMIT):
    # Get item metadata
    metadata = requests.get('%s/metadata/%s' % (ARCHIVE, identifier)).json()

    # Used to build up URIs for the manifest
    uri = f"{domain}{identifier}/collection.json"

    config.configs['helpers.auto_fields.AutoLang'].auto_lang = "none"
    collection = Collection(id=uri, label=metadata["metadata"]["title"])

    addMetadata(collection, identifier, metadata['metadata'], collection=True)

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
        child = None
        if item['mediatype'] == 'collection':
            child = CollectionRef(id=f"{domain}{item['identifier']}/collection.json", type="Collection", label=item['title'])
        else:
            child = ManifestRef(id=f"{domain}{item['identifier']}/manifest.json", type="Manifest", label=item['title'])

        if "description" in item:
            child.summary = {"none": [item['description']]}

        collection.add_item(child)
    page += 1
    if page <= pages:
        child = CollectionRef(id=f"{domain}{identifier}/{page}/collection.json", type="Collection", label={ "en": [f"Page {page} of {pages}"]})
        collection.add_item(child)

    return json.loads(collection.jsonld())

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
        '@id': '%s2/%s/manifest.json' % (domain,identifier),
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
                canvasId= f"https://iiif.archivelab.org/iiif/{identifier}/canvas"
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
                    identifier= info['@id'],
                    label=metadata['title'],
                    width=info['width'],
                    height=info['height'],
                    metadata=metadata,
                    canvasId= f"https://iiif.archivelab.org/iiif/{identifier}/canvas"
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
                        identifier = f"{IMG_SRV}/2/{cantaloupe_resolver(f"{identifier}${page}", metadata=resp)}",
                        label=data['pageNums'][page],
                        width=data['pageWidths'][page],
                        height=data['pageHeights'][page],
                        canvasId= f"https://iiif.archivelab.org/iiif/{identifier}${page}/canvas"
                    )
                )
                return manifest

            for page in range(0, len(data.get('leafNums', []))):
                manifest['sequences'][0]['canvases'].append(
                    manifest_page(
                        identifier = f"{IMG_SRV}/2/{cantaloupe_resolver(f"{identifier}${page}", metadata=resp)}",
                        label=data['pageNums'][page],
                        width=data['pageWidths'][page],
                        height=data['pageHeights'][page],
                        canvasId= f"https://iiif.archivelab.org/iiif/{identifier}${page}/canvas"
                    )
                )
    return manifest

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

    imgId = f"{identifier}/{fileName}".replace('/','%2f')
    imgURL = f"{IMG_SRV}/3/{imgId}"

    manifest.make_canvas_from_iiif(url=imgURL,
                                    id=f"{URI_PRIFIX}/{identifier}/canvas",
                                    label="1",
                                    anno_page_id=f"{uri}/annotationPage/1",
                                    anno_id=f"{uri}/annotation/1")

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
        if type(metadata["description"]) != list:
            item.summary = {"none": [metadata["description"]]}
        else:
            item.summary = {"none": metadata["description"]}

    excluded_fields = [
        'avg_rating', 'backup_location', 'btih', 'description', 'downloads',
        'imagecount', 'indexflag', 'item_size', 'licenseurl', 'curation',
        'noindex', 'num_reviews', 'oai_updatedate', 'publicdate', 'publisher',  'reviewdate',
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

    # Type format from IA Metadata -> Type description in IIIF
    SEEALSO_TYPES = {
        "Abbyy GZ": "OCR Data",
        "Abbyy XML": "OCR Data",
        "Djvu XML": "OCR Data",
        "Scandata": "OCR Data",
        "Archive BitTorrent": "Torrent",
        "Metadata": "Metadata",
    }

    for file in files:
        if file['format'] in LINKS and LINKS[file['format']]['field'] == 'seeAlso':
            seeAlso = LINKS[file['format']]
            manifest.seeAlso.append(
                {"id": f"{ARCHIVE}/download/{identifier}/{file['name']}",
                 "type": seeAlso['type'],
                 "label": {"en": [file["format"]]},
                 "format": seeAlso['format']
                 })


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
    for file in files:
        if file['format'] == "Thumbnail" or file['format'] == "JPEG Thumb" or file['name'] == "__ia_thumb.jpg":
            thumbnail_uri = quote(
                file.get('name').split('/')[-1].replace('/','%2f')
            )
            # Forward solidus before thumbnail uri must always be %2f
            manifest.create_thumbnail_from_iiif(
                f"{IMG_SRV}/2/{identifier.strip()}%2f{thumbnail_uri}"
            )
    return manifest

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

def create_manifest3(identifier, domain=None, page=None):
    # Get item metadata
    metadata = requests.get('%s/metadata/%s' % (ARCHIVE, identifier)).json()

    mediatype = metadata['metadata']['mediatype']

    # Used to build up URIs for the manifest
    uri = f"{domain}{identifier}"

    config.configs['helpers.auto_fields.AutoLang'].auto_lang = "none"

    manifest = Manifest(id=f"{uri}/manifest.json", label=metadata["metadata"]["title"])

    addMetadata(manifest, identifier, metadata['metadata'])
    addSeeAlso(manifest, identifier, metadata['files'])
    addRendering(manifest, identifier, metadata['files'])
    manifest = addThumbnails(manifest, identifier, metadata['files'])

    if mediatype == 'texts':
        # Get bookreader metadata (mostly for filenames and height / width of image)
        # subprefix can be different from the identifier use the scandata filename to find the correct prefix
        # if not present fall back to identifier
        subprefix = identifier
        djvuFile = ""
        for fileMd in metadata['files']:
            if fileMd['name'].endswith('_scandata.xml'):
                subprefix = fileMd['name'].replace('_scandata.xml', '')
            if fileMd['format'] == 'Djvu XML':
                djvuFile = fileMd['name']

        bookReaderURL = f"https://{metadata.get('server')}/BookReader/BookReaderJSIA.php?id={identifier}&itemPath={metadata.get('dir')}&server={metadata.get('server')}&format=jsonp&subPrefix={subprefix}"

        bookreader = requests.get(bookReaderURL).json()
        if 'error' in bookreader:
            # Image stack not found. Maybe a single image
            singleImage(metadata, identifier, manifest, uri)
        else:
            pageCount = 0
            # In json: /29/items/goody/goody_jp2.zip convert to goody/good_jp2.zip
            zipFile = '/'.join(bookreader['data']['brOptions']['zip'].split('/')[-2:])

            for pageSpread in bookreader['data']['brOptions']['data']:
                for page in pageSpread:
                    fileUrl = urlparse(page['uri'])
                    fileName = parse_qs(fileUrl.query).get('file')[0]
                    imgId = f"{zipFile}/{fileName}"
                    imgURL = f"{IMG_SRV}/3/{quote(imgId, safe='()')}"

                    canvas = Canvas(id=f"{URI_PRIFIX}/{identifier}${pageCount}/canvas", label=f"{page['leafNum']}")

                    body = ResourceItem(id=f"{imgURL}/full/max/0/default.jpg", type="Image")
                    body.format = "image/jpeg"
                    body.service = [ServiceItem(id=imgURL, profile="level2", type="ImageService3")]

                    annotation = Annotation(id=f"{uri}/annotation/{pageCount}", motivation='painting', body=body, target=canvas.id)

                    annotationPage = AnnotationPage(id=f"{uri}/annotationPage/{pageCount}")
                    annotationPage.add_item(annotation)

                    canvas.add_item(annotationPage)
                    canvas.set_hwd(page['height'], page['width'])

                    manifest.add_item(canvas)
                    # Create canvas from IIIF image service. Note this is very slow:
                    #canvas = manifest.make_canvas_from_iiif(url=imgURL,
                    #                            id=f"https://iiif.archivelab.org/iiif/{identifier}${pageCount}/canvas",
                    #                            label=f"{page['leafNum']}")
                    pageCount += 1


            # Setting logic for paging behavior and starting canvases
            # Start with paged (default) or individual behaviors
            try:
                if bookreader['data']['brOptions']['defaults'] == "mode/1up":
                    manifest.behavior = "individuals"
            except:
                manifest.behavior = "paged"

            # Then set left-to-right or right-to-left if present
            try:
                if bookreader['data']['brOptions']['pageProgression'] == "lr":
                    viewingDirection = "left-to-right"
                elif bookreader['data']['brOptions']['pageProgression'] == "rl":
                    viewingDirection = "right-to-left"
                if viewingDirection:
                    manifest.viewingDirection = viewingDirection
            except:
                pass

        # Add annotations if djvu file is present
        if djvuFile:
            count = 1
            for canvas in manifest.items:
                if 'annotations' in canvas:
                    annotations = canvas.annotations
                else:
                    annotations = []

                annotations.append(
                    AnnotationPageRef(id=f"{domain}3/annotations/{identifier}/{quote(djvuFile, safe='()')}/{count}.json", type="AnnotationPage")
                )
                canvas.annotations = annotations
                count += 1
    elif mediatype == 'image':
        (multiFile, format) = checkMultiItem(metadata)
        if multiFile:
            # Create multi file manifest
            pageCount = 0
            for file in metadata['files']:
                if file['source'] == "original" and file['format'] == format:
                    imgId = f"{identifier}/{file['name']}".replace('/','%2f')
                    imgURL = f"{IMG_SRV}/3/{imgId}"
                    pageCount += 1

                    try:
                        manifest.make_canvas_from_iiif(url=imgURL,
                                                    id=f"{URI_PRIFIX}/{identifier}${pageCount}/canvas",
                                                    label=f"{file['name']}",
                                                    anno_page_id=f"{uri}/annotationPage/1",
                                                    anno_id=f"{uri}/annotation/1")
                    except requests.exceptions.HTTPError as error:
                        print (f'Failed to get {imgURL}')
                        manifest.make_canvas(label=f"Failed to load {file['name']} from Image Server",
                                             summary=f"Got {error}",
                                            id=f"{URI_PRIFIX}/{identifier}/canvas",
                                            height=1800, width=1200)
        else:
            singleImage(metadata, identifier, manifest, uri)
    elif mediatype == 'audio' or mediatype == 'etree':
        # sort the files into originals and derivatives, splitting the derivatives into buckets based on the original
        (originals, derivatives) = sortDerivatives(metadata)

        # Make behavior "auto-advance if more than one original"
        if sum(f['format'] in AUDIO_FORMATS for f in originals) > 1:
            manifest.behavior = "auto-advance"

        # create the canvases for each original
        for file in [f for f in originals if f['format'] in AUDIO_FORMATS]:
            normalised_id = file['name'].rsplit(".", 1)[0]
            slugged_id = normalised_id.replace(" ", "-")
            c_id = f"{URI_PRIFIX}/{identifier}/{slugged_id}/canvas"
            c = Canvas(id=c_id, label=normalised_id, duration=float(file['length']))

            # create intermediary objects
            ap = AnnotationPage(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/page")
            anno = Annotation(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/annotation", motivation="painting", target=c.id)

            # create body based on whether there are derivatives or not:
            if file['name'] in derivatives:
                body = Choice(items=[])
                # add the choices in order per https://github.com/ArchiveLabs/iiif.archivelab.org/issues/77#issuecomment-1499672734
                for format in AUDIO_FORMATS:
                    if format in derivatives[file['name']]:
                        r = ResourceItem(id=f"https://archive.org/download/{identifier}/{derivatives[file['name']][format]['name'].replace(' ', '%20')}",
                                         type='Sound',
                                         format=to_mimetype(format),
                                         label={"none": [format]},
                                         duration=float(file['length']))
                        body.items.append(r)
                    elif file['format'] == format:
                        r = ResourceItem(
                            id=f"https://archive.org/download/{identifier}/{file['name'].replace(' ', '%20')}",
                            type='Sound',
                            format=to_mimetype(format),
                            label={"none": [format]},
                            duration=float(file['length']))
                        body.items.append(r)
            else:
                # todo: deal with instances where there are no derivatives for whatever reason
                body = ResourceItem(
                            id=f"https://archive.org/download/{identifier}/{file['name'].replace(' ', '%20')}",
                            type='Sound',
                            format=to_mimetype(file['format']),
                            label={"none": [file['format']]},
                            duration=float(file['length']))

            anno.body = body
            ap.add_item(anno)
            c.add_item(ap)
            manifest.add_item(c)

    elif mediatype == "movies":
        (originals, derivatives, vttfiles) = sortDerivatives(metadata, includeVtt=True)
        # Make behavior "auto-advance if more than one original"
        if sum(f['format'] in VIDEO_FORMATS for f in originals) > 1:
            manifest.behavior = "auto-advance"

        if 'access-restricted-item' in metadata['metadata'] and metadata['metadata']['access-restricted-item']:
            # this is a news item so has to be treated differently
            # https://ia801803.us.archive.org/29/items/CSPAN3_20180217_164800_Poplar_Forest_Archaeology/CSPAN3_20180217_164800_Poplar_Forest_Archaeology.mp4?start=0&end=360&ignore=x.mp4&cnt=0
            mp4File = None
            duration = 0.0
            filedata = None
            for file in metadata['files']:
                if file['name'].endswith('.mp4'):
                    mp4File = file['name']
                    duration = float(file['length'])
                    filedata = file

            # create the canvases for each original
            for file in [f for f in originals if f['format'] in VIDEO_FORMATS]:
                normalised_id = file['name'].rsplit(".", 1)[0]
                slugged_id = normalised_id.replace(" ", "-")
                c_id = f"{URI_PRIFIX}/{identifier}/{slugged_id}/canvas"
                c = Canvas(id=c_id, label=normalised_id, duration=duration, height=int(filedata['height']), width=int(filedata['width']))        

                ap = AnnotationPage(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/page")

                vttAPId = f"{URI_PRIFIX}/{identifier}/{slugged_id}/vtt"
                vtAnno = c.make_annotation(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/annotation/vtt/streamed", 
                                                    motivation="supplementing", 
                                                    target=c.id, 
                                                    anno_page_id=vttAPId,
                                                    body={"id": f"{domain}vtt/streaming/{identifier}.vtt",
                                                            "type": "Text",
                                                            "format": "text/vtt",
                                                            })

                segments = math.floor(duration / 60)
                for i in range(segments):
                    start = i * 60
                    if i == segments - 1:
                        end = int(duration)
                    else:
                        end = (i + 1) * 60

                    #print (f"Start: {start} End: {end}, Duration: {float(end) - float(start)} full duration: {duration}")
                    anno = Annotation(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/annotation/{i}", motivation="painting", target=f"{c.id}#t={start},{end}")
                    streamurl = f"https://{metadata['server']}{metadata['dir']}/{mp4File}?start={start}&end={end}&ignore=x.mp4&cnt=0"        
                    body = ResourceItem(id=streamurl,
                                        type='Video',
                                        format="video/mp4",
                                        label={"en": [f"Part {i + 1} of {segments}"]},
                                        duration=end - start, 
                                        height=int(filedata['height']),
                                        width=int(filedata['width']),                      
                                    )

                    anno.body = body
                    ap.add_item(anno)
                
                c.add_item(ap)
                manifest.add_item(c)
        else:
            # create the canvases for each original
            for file in [f for f in originals if f['format'] in VIDEO_FORMATS]:
                normalised_id = file['name'].rsplit(".", 1)[0]
                slugged_id = normalised_id.replace(" ", "-")
                c_id = f"{URI_PRIFIX}/{identifier}/{slugged_id}/canvas"
                c = Canvas(id=c_id, label=normalised_id, duration=float(file['length']), height=int(file['height']), width=int(file['width']))

                # Add vtt if present
                if vttfiles and normalised_id in vttfiles:
                    vttAPId = f"{URI_PRIFIX}/{identifier}/{slugged_id}/vtt"

                    vttNo = 1
                    for vttFile in vttfiles[normalised_id]:
                        vtAnno = c.make_annotation(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/annotation/vtt/{vttNo}", 
                                                motivation="supplementing", 
                                                target=c.id, 
                                                anno_page_id=vttAPId,
                                                body={"id": f"{domain}resource/{identifier}/{vttFile['name']}",
                                                        "type": "Text",
                                                        "format": "text/vtt",
                                                        })
                        # add label and language
                        if vttFile['name'].endswith("autogenerated.vtt"):
                            vtAnno.body.label = { 'en': ['autogenerated']}
                        else:
                            # Assume language
                            splitName = vttFile['name'].split(".")
                            lang = splitName[-2]
                            vtAnno.body.add_label(lang, language="none")
                            vtAnno.body.language = lang

                        vttNo += 1

                # create intermediary objects
                ap = AnnotationPage(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/page")
                anno = Annotation(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/annotation", motivation="painting", target=c.id)

                # create body based on whether there are derivatives or not:
                if file['name'] in derivatives:
                    body = Choice(items=[])
                    # add the choices in order per https://github.com/ArchiveLabs/iiif.archivelab.org/issues/77#issuecomment-1499672734
                    for format in VIDEO_FORMATS:
                        if format in derivatives[file['name']]:
                            r = ResourceItem(id=f"https://archive.org/download/{identifier}/{derivatives[file['name']][format]['name'].replace(' ', '%20')}",
                                            type='Video',
                                            format=to_mimetype(format),
                                            label={"none": [format]},
                                            duration=float(file['length']), 
                                            height=int(file['height']),
                                            width=int(file['width']),                      
                            )
                            body.items.append(r)
                        elif file['format'] == format:
                            r = ResourceItem(
                                id=f"https://archive.org/download/{identifier}/{file['name'].replace(' ', '%20')}",
                                type='Video',
                                format=to_mimetype(format),
                                label={"none": [format]},
                                duration=float(file['length']),
                                height=int(file['height']),
                                width=int(file['width']))
                            body.items.append(r)
                else:
                    # todo: deal with instances where there are no derivatives for whatever reason
                    pass

                anno.body = body
                ap.add_item(anno)
                c.add_item(ap)
                manifest.add_item(c)
    elif mediatype == "collection":
        raise IsCollection
    else:
        print (f'Unknown mediatype "{mediatype}"')

    return json.loads(manifest.jsonld())

def create_annotations(version: int, identifier: str, fileName: str, canvas_no: int, domain: str | None = None):
    annotationPage = AnnotationPage(id=f"{domain}{version}/annotations/{identifier}/{quote(fileName, safe='()')}/{canvas_no}.json")
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
                    starttime = timeToDelta(splitline[0].strip()) + timedelta(seconds=start)
                    endtime = timeToDelta(splitline[1].strip()) + timedelta(seconds=start)
                    line = f"{formatTimeVTT(starttime)} --> {formatTimeVTT(endtime)}"

                vtt_content.append(line)

            vtt_content.append("")

    # Join the list into a single string
    return "\n".join(vtt_content)

def formatTimeVTT(time):
    hours, remainder = divmod(time.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}.{int(time.microseconds / 1000):03}"

def timeToDelta(time):
    """
    Convert SRT formated times to timedelta
    """
    milliseconds = int(time.split(",")[1])
    timeStr = time.split(",")[0]
    hour = int(timeStr.split(":")[0])
    minute = int(timeStr.split(":")[1])
    second = int(timeStr.split(":")[2])
    return timedelta(hours=hour, minutes=minute, seconds=second, milliseconds=milliseconds)

def coerce_list(value):
    if isinstance(value, list):
        return ". ".join(value)
    return value


def valid_filetype(filename):
    f = filename.lower()
    return any(f.endswith('.%s' % ext) for ext in valid_filetypes)

def ia_resolver(identifier):
    """Resolves a iiif identifier to the resource's path on disk.

    Resolver returns the path of resource on the iiif server (as
    opposed to a remote storage host, like Internet Archive) and first
    fetches it, if it doesn't exist on disk..
    """
    path = os.path.join(media_root, identifier)

    leaf = None
    if "$" not in identifier:
        filepath = None
    else:
        identifier, filepath = identifier.split("$", 1)
        filepath = filepath.replace("$", os.sep)
        if os.sep not in filepath:
            leaf = filepath

    identifier, document = identifier.split(":", 1) if ":" in identifier else (identifier, None)

    metadata = requests.get('%s/metadata/%s' % (ARCHIVE, identifier)).json()
    if 'dir' not in metadata:
        raise ValueError("No such valid Archive.org item identifier: %s" \
                        % identifier)
    mediatype = metadata['metadata']['mediatype']
    files = metadata['files']
    collections = metadata['metadata']['collection']
    collections = [collections] if isinstance(collections, str) else collections

    # If item in restricted collection, raise permission error
    for i in collections:
        metadata_url = '%s/metadata/%s' % (ARCHIVE, i)
        c = requests.get(metadata_url).json().get('metadata', {})
        if c.get('access-restricted', False):
            # check for preview, e.g. etable of contents (which can be public?)
            # ...
            raise ValueError("This resource has restricted access")

    if not os.path.exists(path):
        r = None

        if mediatype.lower() == 'image' or (
            filepath and mediatype.lower() != 'texts'
        ):
            if filepath:
                itempath = os.path.join(identifier, filepath)
            else:
                f = next(f for f in files if valid_filetype(f['name']) \
                         and f['source'].lower() == 'original' \
                         and 'thumb' not in f['name'] )
                itempath = os.path.join(identifier, f['name'])
            url = '%s/download/%s' % (ARCHIVE, itempath)
            r = requests.get(url, stream=True, allow_redirects=True)

        elif mediatype.lower() == 'texts' and leaf:
            identifierpath = "/".join([identifier, document]) if document else identifier
            url = '%s/download/%s/page/leaf%s' % (ARCHIVE, identifierpath, leaf)
            r = requests.get(url)
        if r:
            with open(path, 'wb') as rc:
                rc.writelines(r.iter_content(chunk_size=1024))

    return path, mediatype

def infojson(identifier, version="2", metadata=None):
    """
     This will only work when identifier is a single image or if it uses the $ to identify the sub image. 

     Parameters:
     identifier (str): IA object identifier 
     version (str): IIIF Version number. Defaults to 2
     metadata (dict): if you have already got the response from ARCHIVE/metadata/identifier then you can
                      pass this as a parameter 
    """
    imgSrv = f"{IMG_SRV}/{version}/{cantaloupe_resolver(identifier, metadata)}/info.json"

    info_resp = requests.get(imgSrv)
    return info_resp.json()


def cantaloupe_resolver(identifier, metadata=None):
    """Resolves an existing Image Service identifier to what it should be with the new Cantaloupe setup"""
    leaf = None
    if "$" in identifier:
        identifier, leaf = identifier.split("$", 1)

    if not metadata:
        response = requests.get('%s/metadata/%s' % (ARCHIVE, identifier))
        # Raise exception if getting the metadata failed
        response.raise_for_status()
        metadata = response.json()

    if 'dir' not in metadata:
        print (f"Metadata contains:")
        print (metadata)
        raise ValueError("No such valid Archive.org item identifier: %s" \
                        % identifier)

    mediatype = metadata['metadata']['mediatype'].lower()
    files = metadata['files']
    if mediatype == "image":
        # single image file - find the filename

        filename = None
        for f in files:
            if valid_filetype(f['name']) \
                 and f['source'].lower() == 'original' \
                 and 'thumb' not in f['name']:

                filename = f['name'].replace(" ", "%20")

        if filename:
            return f"{identifier}%2f{filename}"

    elif mediatype == "texts" and leaf:
        # book - find the jp2 zip and assume the filename?
        # TODO: use one of the BookReader (or other) APIs to be 100% certain here
        filename = None
        fileIdentifier = ""
        extension = ".jp2"

        # First try the identifier then _jp2.zip
        for f in files:
            if f['name'].lower() == f'{identifier.lower()}_jp2.zip':
                filename = f['name']
                fileIdentifier = filename[:-1 * len('_jp2.zip')]

        # next look for any _jp2.zip that has a different name to the identifier
        if not filename:
            for f in files:
                if f['name'].endswith('_jp2.zip'):
                    filename = f['name']
                    fileIdentifier = filename[:-1 * len('_jp2.zip')]
        # Prefer zip files but if not return tar
        if not filename:
            for f in files:
                if f['name'].endswith('_jp2.tar'):
                    filename = f['name']
                    fileIdentifier = filename[:-1 * len('_jp2.tar')]

        # if no jp2s look for tiffs
        if not filename:
            for f in files:
                if f['name'].endswith('_tif.zip'):
                    filename = f['name']
                    fileIdentifier = filename[:-1 * len('_tif.zip')]
                    extension = ".tif"

        if filename:
            dirpath = filename[:-4]
            filepath = f"{fileIdentifier}_{leaf.zfill(4)}{extension}"
            return f"{identifier}%2f{filename}%2f{dirpath}%2f{filepath}"

