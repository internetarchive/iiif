import math

from iiif_prezi3 import Canvas, Annotation, AnnotationPage, AnnotationBody, Choice

from .base import BaseManifestBuilder
from .constants import VIDEO_FORMATS, URI_PRIFIX
from .helpers import sortDerivatives, addThumbnailNav
from .utils import to_mimetype


class VideoManifestBuilder(BaseManifestBuilder):
    def build_canvases(self, manifest, metadata, identifier, domain, uri, page):
        (originals, derivatives, vttfiles) = sortDerivatives(metadata, includeVtt=True)

        # Make behavior "auto-advance if more than one original"
        if sum(f['format'] in VIDEO_FORMATS for f in originals) > 1:
            manifest.behavior = "auto-advance"

        addThumbnailNav(manifest, identifier, metadata["files"])

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

                    anno = Annotation(id=f"{URI_PRIFIX}/{identifier}/{slugged_id}/annotation/{i}", motivation="painting", target=f"{c.id}#t={start},{end}")
                    streamurl = f"https://{metadata['server']}{metadata['dir']}/{mp4File}?start={start}&end={end}&ignore=x.mp4&cnt=0"
                    body = AnnotationBody(id=streamurl,
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
                            vtAnno.body.label = {'en': ['autogenerated']}
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
                            r = AnnotationBody(id=f"https://archive.org/download/{identifier}/{derivatives[file['name']][format]['name'].replace(' ', '%20')}",
                                            type='Video',
                                            format=to_mimetype(derivatives[file['name']][format]['name'], format),
                                            label={"none": [format]},
                                            duration=float(file['length']),
                                            height=int(file['height']),
                                            width=int(file['width']),
                            )
                            body.items.append(r)
                        elif file['format'] == format:
                            r = AnnotationBody(
                                id=f"https://archive.org/download/{identifier}/{file['name'].replace(' ', '%20')}",
                                type='Video',
                                format=to_mimetype(file['name'], format),
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
