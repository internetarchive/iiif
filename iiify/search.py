import requests
from .resolver import ARCHIVE, URI_PRIFIX
from bs4 import BeautifulSoup

def build_search_url(identifier, query):
    response = requests.get(f"{ARCHIVE}/metadata/{identifier}")
    response.raise_for_status()
    metadata = response.json()
    # doc = metadata['files'][0]['name'].split('.')[0]
    doc = [file['name'].split('_')[0] for file in metadata["files"] if '_djvu.xml' in file['name']][0]
    return f"https://{metadata['server']}/fulltext/inside.php?item_id={identifier}&doc={doc}&path={metadata['dir']}&q={query}"

def iiif_search(identifier, query):
    url = build_search_url(identifier, query)
    response = requests.get(url)
    response.raise_for_status() 
    ia_response = response.json()

    searchResponse = {
        "@context":"http://iiif.io/api/presentation/2/context.json",
        "@id": f"{URI_PRIFIX}/search/{identifier}?q={query}",
        "@type": "sc:AnnotationList",

        "resources": [
        ]
    }

    # "b": 1090, "t": 700, "r": 2024, "l": 192, 
    count = 1
    for match in ia_response['matches']:
        paragraph = match['par'][0]
       
        # Only show the match rather than the full matching paragraph 
        text = ""
        largeResults = True
        if len(match['text']) < 10000:
            largeResults = False
            soup = BeautifulSoup(match['text'], 'html.parser')
            match = [tag.text for tag in soup.find_all('ia_fts_match')]
            if len(match) != len(paragraph['boxes']):
                for i in range(len(paragraph['boxes']) - len(match)):
                    match.append(query)
        else:
            text = query    

        matchNo = 0

        for box in paragraph['boxes']:
            x = int(box['l'])
            y = int(box['t'])
            # If r is missing then use the paragraph
            if 'r' in box:
                right = int(box['r'])
            else:
                right = paragraph['r'] 

            width = right - x
            height = int(box['b']) - y
            page = int(paragraph['page'])  - 1
            if "leaf0_missing" in ia_response and ia_response['leaf0_missing'] == False:
                page = int(paragraph['page'])

            searchResponse['resources'].append({
                "@id": f"{URI_PRIFIX}/{identifier}/annotation/anno{count}",
                "@type": "oa:Annotation",
                "motivation": "sc:painting",
                "resource": {
                    "@type": "cnt:ContentAsText",
                    "chars": text if largeResults else match[matchNo] 
                },
                "on": f"{URI_PRIFIX}/{identifier}${page}/canvas#xywh={x},{y},{width},{height}",
                "within": {
                    "@id": f"{URI_PRIFIX}/{identifier}/manifest.json",
                    "type": "sc:Manifest"
                }
            })
            matchNo += 1
            count += 1

    return searchResponse
