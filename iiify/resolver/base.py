import json
import requests
from iiif_prezi3 import config, Manifest, AnnotationPageRef, AnnotationPageRefExtended

from .constants import ARCHIVE
from .helpers import addMetadata, addSeeAlso, addRendering, addThumbnails, addPartOfCollection


class BaseManifestBuilder:
    def build(self, identifier, domain, page=None, metadata=None):
        if metadata is None:
            metadata = requests.get(f'{ARCHIVE}/metadata/{identifier}').json()

        uri = f"{domain}{identifier}"

        config.configs['helpers.auto_fields.AutoLang'].auto_lang = "none"

        manifest = Manifest(id=f"{uri}/manifest.json", label=metadata["metadata"]["title"])
        if 'reviews' in metadata:
            reviews_as_annotations = AnnotationPageRef(__root__=AnnotationPageRefExtended(
                id=f"{domain.replace('iiif/', 'iiif/3/annotations/')}{identifier}/comments.json",
                type="AnnotationPage",
            ))
            manifest.annotations = [reviews_as_annotations]

        addMetadata(manifest, identifier, metadata['metadata'])
        addSeeAlso(manifest, identifier, metadata['files'])
        addRendering(manifest, identifier, metadata['files'])
        addThumbnails(manifest, identifier, metadata['files'])
        addPartOfCollection(manifest, metadata.get('metadata').get('collection', []), domain)

        self.build_canvases(manifest, metadata, identifier, domain, uri, page)
        return json.loads(manifest.jsonld())

    def build_canvases(self, manifest, metadata, identifier, domain, uri, page):
        raise NotImplementedError
