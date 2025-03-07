import requests
from .resolver import ARCHIVE, URI_PRIFIX
import json
import re

def iiif_search(identifier, query):
    response = requests.get(f"{ARCHIVE}/metadata/{identifier}")
    response.raise_for_status() 

    metadata = response.json()

    url = f"https://{metadata['server']}/fulltext/inside.php?item_id={identifier}&doc={identifier}&path={metadata['dir']}&q={query}"
    print (f"Search URL:\n{url}")
    response = requests.get(url)
    response.raise_for_status() 
    ia_response = response.json()

    searchResponse = {
        "@context":"http://iiif.io/api/presentation/2/context.json",
        "@id": f"{URI_PRIFIX}/search/{identifier}?q={query}",
        "@type":"sc:AnnotationList",

        "resources": [
        ]
    }

    # "b": 1090, "t": 700, "r": 2024, "l": 192, 
    count = 1
    for match in ia_response['matches']:
        paragraph = match['par'][0]
        x = int(paragraph['l'])
        y = int (paragraph['t'])
        width = int(paragraph['r']) - x
        height = int(paragraph['b']) - y
        # Only show the match rather than the full matching paragraph 
        match = re.search(r"<IA_FTS_MATCH>(.*?)</IA_FTS_MATCH>", match['text'])

        searchResponse['resources'].append({
            "@id": f"{URI_PRIFIX}/{identifier}/annotation/anno{count}",
            "@type": "oa:Annotation",
            "motivation": "sc:painting",
            "resource": {
                "@type": "cnt:ContentAsText",
                "chars": match.group(1)
            },
            "on": f"{URI_PRIFIX}/{identifier}${int(paragraph['page']) - 1}/canvas#xywh={x},{y},{width},{height}",
            "within": {
                "@id": f"{URI_PRIFIX}/{identifier}/manifest.json",
                "type": "sc:Manifest"
            }
        })
        count += 1

    return searchResponse