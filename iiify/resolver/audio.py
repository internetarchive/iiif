from iiif_prezi3 import Canvas, Annotation, AnnotationPage, AnnotationBody, Choice, CanvasRef

from .base import BaseManifestBuilder
from .constants import AUDIO_FORMATS, URI_PRIFIX
from .helpers import sortDerivatives, addWaveform
from .utils import to_mimetype


class AudioManifestBuilder(BaseManifestBuilder):
    def build_canvases(self, manifest, metadata, identifier, domain, uri, page):
        (originals, derivatives) = sortDerivatives(metadata)

        # Make behavior "auto-advance if more than one original"
        if sum(f['format'] in AUDIO_FORMATS for f in originals) > 1:
            manifest.behavior = "auto-advance"

        # create the canvases for each original
        total_audio_files = len([f for f in originals if f['format'] in AUDIO_FORMATS])
        if total_audio_files > 1:
            top_range = manifest.make_range(
                id=f"{URI_PRIFIX}/{identifier}/range/1",
                label={"en": ["Track List"]}
            )

        for file in [f for f in originals if f['format'] in AUDIO_FORMATS]:
            normalised_id = file['name'].rsplit(".", 1)[0]
            slugged_id = normalised_id.replace(" ", "-")
            c_id = f"{URI_PRIFIX}/{identifier}/{slugged_id}/canvas"
            c = Canvas(id=c_id, label=normalised_id, duration=float(file['length']))

            # if multiple files, also add a range
            if total_audio_files > 1:
                track = top_range.make_range(
                    id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/range",
                    label=file.get('title', normalised_id)
                )
                track.add_item(
                    CanvasRef(
                        id=c_id,
                        type="Canvas"
                    )
                )

            # create intermediary objects
            ap = AnnotationPage(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/page")
            anno = Annotation(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/annotation", motivation="painting", target=c.id)

            # create body based on whether there are derivatives or not:
            if file['name'] in derivatives:
                body = Choice(items=[])
                # add the choices in order per https://github.com/ArchiveLabs/iiif.archivelab.org/issues/77#issuecomment-1499672734
                for format in AUDIO_FORMATS:
                    if format in derivatives[file['name']]:
                        r = AnnotationBody(id=f"https://archive.org/download/{identifier}/{derivatives[file['name']][format]['name'].replace(' ', '%20')}",
                                         type='Sound',
                                         format=to_mimetype(derivatives[file['name']][format]['name'], format),
                                         label={"none": [format]},
                                         duration=float(file['length']))
                        body.items.append(r)
                    elif file['format'] == format:
                        r = AnnotationBody(
                            id=f"https://archive.org/download/{identifier}/{file['name'].replace(' ', '%20')}",
                            type='Sound',
                            format=to_mimetype(file['name'], format),
                            label={"none": [format]},
                            duration=float(file['length']))
                        body.items.append(r)

                if "Spectrogram" in derivatives[file['name']]:
                    c.seeAlso = [{
                        "id": f"https://archive.org/download/{identifier}/{normalised_id.replace(' ', '%20')}_spectrogram.png",
                        "type": "Image",
                        "label": {"en": ["Spectrogram"]},
                        "format": "image/png"
                    }]

                if "PNG" in derivatives[file['name']]:
                    # This should be the Wave form
                    c.accompanyingCanvas = addWaveform(identifier, slugged_id, derivatives[file['name']]["PNG"]["name"])
            else:
                # todo: deal with instances where there are no derivatives for whatever reason
                body = AnnotationBody(
                            id=f"https://archive.org/download/{identifier}/{file['name'].replace(' ', '%20')}",
                            type='Sound',
                            format=to_mimetype(file['name'], file['format']),
                            label={"none": [file['format']]},
                            duration=float(file['length']))

            anno.body = body
            ap.add_item(anno)
            c.add_item(ap)
            manifest.add_item(c)
