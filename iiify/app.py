#!/usr/bin/env python
import hashlib
import os
import time
import requests
from flask import Flask, send_file, jsonify, abort, request, render_template, redirect, make_response
from flask_cors import CORS
from flask_caching import Cache
from iiif2 import iiif, web
from .resolver import ia_resolver, create_manifest, create_manifest3, scrape, \
    collection, purify_domain, cantaloupe_resolver, create_collection3, IsCollection, \
    create_annotations, create_vtt_stream
from .configs import options, cors, approot, cache_root, media_root, \
    cache_expr, version, image_server, cache_timeouts
from urllib.parse import quote
import re


app = Flask(__name__)
# disabling sorting of the output json
app.config['JSON_SORT_KEYS'] = False
app.config['CACHE_TYPE'] = "FileSystemCache" if os.environ.get("FLASK_CACHE_DISABLE", None) != "true" else "NullCache"
app.config['CACHE_DIR'] = "cache"
cors = CORS(app) if cors else None
cache = Cache(app)

ARCHIVE = 'https://archive.org'

# cache.init_app(app)


def cache_bust():
    return request.args.get("recache", "") in ["True", "true", "1"]

@app.route('/')
def mainentry():
  return redirect('/iiif/')


@app.route('/iiif/')
def index():
    """Lists all available book and image items on Archive.org"""
    q = request.args.get('q', '')
    cursor = request.args.get('cursor', '')
    fields = request.args.get('fields', '')
    sorts = request.args.get('sorts', '')
    r = scrape(q, cursor=cursor, fields=fields, sorts=sorts, restrict_to_iiif=True)
    return jsonify(r)


@app.route('/iiif/collection.json')
def catalog():
    q = request.args.get('q', '')
    cursor = request.args.get('cursor', '')
    fields = request.args.get('fields', '')
    sorts = request.args.get('sorts', '')
    domain = purify_domain(request.args.get('domain', request.url_root))
    identifiers = [
        i.get('identifier') for i in scrape(
            q, cursor=cursor, fields=fields, sorts=sorts, restrict_to_iiif=True
        ).get('items')
    ]
    return ldjsonify(collection(domain, identifiers))


@app.route('/iiif/cache')
def list_cache():
    """Lists all recently cached images"""
    return jsonify({'identifiers': [f for f in os.listdir(media_root)]})


@app.route('/iiif/demo')
def demo():
    domain = "http://dms-data.stanford.edu/data/manifests/Stanford/ege1"
    return render_template('reader.html', domain=domain)


@app.route('/iiif/documentation')
def documentation():
    return render_template('docs/index.html', version=version)

@app.route('/iiif/helper/<identifier>/')
def helper(identifier):
    validate_ia_identifier(identifier, page_suffix=False)

    metadata = requests.get('%s/metadata/%s' % (ARCHIVE, identifier)).json()

    # If the item doesn't exist, the endpoint 200s with an empty object
    if not metadata:
        abort(404, f"Identifier '{identifier}' not found")

    mediatype = metadata['metadata']['mediatype']

    if mediatype == "image":
        try:
            cantaloupe_id = cantaloupe_resolver(identifier)
            esc_cantaloupe_id = quote(cantaloupe_id)
            return render_template('helpers/image.html', identifier=identifier, cantaloupe_id=cantaloupe_id, esc_cantaloupe_id=esc_cantaloupe_id)
        except ValueError:
            abort(404)

    elif mediatype == "audio" or mediatype == "etree":
        return render_template('helpers/audio.html', identifier=identifier)
    elif mediatype == "movies":
        return render_template('helpers/movies.html', identifier=identifier)
    elif mediatype == "texts":
        return render_template('helpers/texts.html', identifier=identifier)
    elif mediatype == "collection":
        return render_template('helpers/collection.html', identifier=identifier)
    else:
        return render_template('helpers/unknown.html', identifier=identifier)


@app.route('/iiif/<identifier>')
def view(identifier):
    validate_ia_identifier(identifier, page_suffix=True)

    domain = purify_domain(request.args.get('domain', request.url_root))
    uri = '%s%s' % (domain, identifier)
    page = request.args.get('page', None)
    citation = request.args.get('citation', None)

    try:
        path, mediatype = ia_resolver(identifier)
    except ValueError:
        abort(404)
    if mediatype == 'image' or '$' in identifier:
        return render_template('viewer.html', domain=domain,
                               info=web.info(uri, path))
    return render_template('reader.html', domain=request.base_url, page=page, citation=citation)


@app.route('/iiif/3/<identifier>/collection.json')
@cache.cached(timeout=cache_timeouts["med"], forced_update=cache_bust)
def collection3JSON(identifier):
    validate_ia_identifier(identifier, page_suffix=False)
    domain = purify_domain(request.args.get('domain', request.url_root))

    try:
        collection = create_collection3(identifier, domain=domain)
        if not collection:
            abort(404)
            return

        return ldjsonify(collection)
    except Exception as excpt:
        print(excpt)
        raise excpt


@app.route('/iiif/3/<identifier>/<page>/collection.json')
@cache.cached(timeout=cache_timeouts["med"], forced_update=cache_bust)
def collection3page(identifier, page):
    validate_ia_identifier(identifier, page_suffix=False)
    domain = purify_domain(request.args.get('domain', request.url_root))

    try:
        collection = create_collection3(identifier, domain=domain, page=int(page))

        if not collection:
            abort(404)
            return

        return ldjsonify(collection)
    except Exception as excpt:
        print(excpt)
        raise excpt


@app.route('/iiif/<identifier>/collection.json')
@cache.cached(timeout=cache_timeouts["long"], forced_update=cache_bust)
def collectionJSON(identifier):
    validate_ia_identifier(identifier, page_suffix=False)
    return redirect(f'/iiif/3/{identifier}/collection.json', code=302)


@app.route('/iiif/<identifier>/<page>/collection.json')
@cache.cached(timeout=cache_timeouts["long"], forced_update=cache_bust)
def collectionPage(identifier, page):
    validate_ia_identifier(identifier, page_suffix=False)
    return redirect(f'/iiif/3/{identifier}/{page}/collection.json', code=302)


@app.route('/iiif/3/<identifier>/manifest.json')
@cache.cached(timeout=cache_timeouts["long"], forced_update=cache_bust)
def manifest3(identifier):
    validate_ia_identifier(identifier, page_suffix=False)

    domain = purify_domain(request.args.get('domain', request.url_root))
    page = None

    try:
        return ldjsonify(create_manifest3(identifier, domain=domain, page=page))
    except IsCollection:
        # raised when mediatype is a collection so we can redirect
        return redirect(f'/iiif/3/{identifier}/collection.json', code=302)
    except Exception as excpt:
        print('Exception occured in manifest3:')
        print(excpt)
        raise excpt
        # abort(404)

@app.route('/iiif/<int:version>/annotations/<identifier>/<fileName>/<int:canvas_no>.json')
@cache.cached(timeout=cache_timeouts["long"], forced_update=cache_bust)
def annnotations(version: str, identifier: str, fileName: str, canvas_no: int):
    validate_ia_identifier(identifier, page_suffix=False)
    domain = purify_domain(request.args.get('domain', request.url_root))
    return ldjsonify(create_annotations(version, identifier, fileName, canvas_no, domain=domain))

@app.route('/iiif/vtt/streaming/<identifier>.vtt')
@cache.cached(timeout=cache_timeouts["long"], forced_update=cache_bust)
def vtt_stream(identifier):
    validate_ia_identifier(identifier, page_suffix=False)
    response = make_response(create_vtt_stream(identifier))
    response.headers['Content-Type'] = 'text/vtt'
    return response

@app.route('/iiif/<identifier>/manifest.json')
@cache.cached(timeout=cache_timeouts["long"], forced_update=cache_bust)
def manifest(identifier):
    validate_ia_identifier(identifier, page_suffix=False)
    return redirect(f'/iiif/3/{identifier}/manifest.json', code=302)

@app.route('/iiif/2/<identifier>/manifest.json')
def manifest2(identifier):
    validate_ia_identifier(identifier, page_suffix=True)
    domain = purify_domain(request.args.get('domain', request.url_root))
    page = None
    if '$' in identifier:
        identifier, page = identifier.split('$')
        page = int(page)
    try:
        return ldjsonify(create_manifest(identifier, domain=domain, page=page, version='2/'))
    except Exception as excpt:
        print("Exception occurred in manifest2:")
        print(excpt)
        abort(404)


@app.route('/iiif/<identifier>/info.json')
def info(identifier):
    validate_ia_identifier(identifier, page_suffix=True)
    cantaloupe_id = cantaloupe_resolver(identifier)
    cantaloupe_url = f"{image_server}/2/{cantaloupe_id}/info.json"
    return redirect(cantaloupe_url, code=302)

@app.route('/iiif/3/<identifier>/info.json')
def info3(identifier):
    validate_ia_identifier(identifier, page_suffix=True)
    cantaloupe_id = cantaloupe_resolver(identifier)
    cantaloupe_url = f"{image_server}/3/{cantaloupe_id}/info.json"
    return redirect(cantaloupe_url, code=302)

@app.route('/iiif/2/<identifier>/info.json')
def info2(identifier):
    validate_ia_identifier(identifier, page_suffix=True)
    cantaloupe_id = cantaloupe_resolver(identifier)
    cantaloupe_url = f"{image_server}/2/{cantaloupe_id}/info.json"
    return redirect(cantaloupe_url, code=302)

@app.route('/iiif/<identifier>/<region>/<size>/<rotation>/<quality>.<fmt>')
def image_processor(identifier, region, size, rotation, quality, fmt):
    validate_ia_identifier(identifier, page_suffix=True)
    cantaloupe_id = cantaloupe_resolver(identifier)
    cantaloupe_url = f"{image_server}/2/{cantaloupe_id}/{region}/{size}/{rotation}/{quality}.{fmt}"
    return redirect(cantaloupe_url, code=302)


@app.after_request
def add_header(response):
    response.cache_control.max_age = cache_expr  # minutes
    return response


def ldjsonify(data):
    j = jsonify(data)
    j.mimetype = "application/ld+json"
    return j

def validate_ia_identifier(identifier: str, page_suffix: bool) -> None:
    if page_suffix:
        if not re.match(r'^[a-zA-Z0-9_.-]{1,100}(\$\d+)?$', identifier):
            abort(400, "Invalid identifier")
        return

    if not re.match(r'^[a-zA-Z0-9_.-]{1,100}$', identifier):
        abort(400, "Invalid identifier")
        return

if __name__ == '__main__':
    app.run(**options)
