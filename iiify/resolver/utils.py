import os
import re
import mimetypes
import requests

from .constants import (
    SCRAPE_API, ADVANCED_SEARCH, ARCHIVE, IMG_SRV,
    MAX_API_LIMIT, valid_filetypes,
)
from ..configs import media_root


class MaxLimitException(Exception):
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


def to_mimetype(filename, format):
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
    mime, encoding = mimetypes.guess_type(filename)
    if mime is None:
        return formats.get(format, "application/octet-stream")
    else:
        return mime


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
        print(f"Metadata contains:")
        print(metadata)
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
