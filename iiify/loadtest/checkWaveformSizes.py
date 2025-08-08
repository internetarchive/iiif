import requests
from iiify import resolver

def getAudioItems():
    """
        Used to find audio items that have a waveform to check their size. 
        It uses the advanced search to find items and then uses the image api
        to find the width and height and check it against the expected size of 800,200
    """
    item_count = 0
    waveform_item_count = 0
    waveform_file_count = 0
    for page in range(5):
        audio = resolver.search("-collection:(stream_only) AND mediatype:(audio)".replace(":", "%3A"), page=page)
        for item in audio["response"]["docs"]:
            item_count += 1
            identifier = item["identifier"]
            metadata = requests.get(f"https://archive.org/metadata/{item["identifier"]}").json()
            # sort the files into originals and derivatives, splitting the derivatives into buckets based on the original
            (originals, derivatives) = resolver.sortDerivatives(metadata)
            hasWaveform=False
            for file in [f for f in originals if f['format'] in resolver.AUDIO_FORMATS]:
                if file['name'] in derivatives and "PNG" in derivatives[file['name']]:   
                    waveform_file_count += 1
                    filename = derivatives[file['name']]["PNG"]["name"]
                    imgId = f"{identifier}/{filename}".replace("/", "%2f")
                    imgUrl = f"{resolver.IMG_SRV}/3/{imgId}/info.json"
                    try:
                        infojson = requests.get(imgUrl).json()
                        if infojson['width'] == 800 and infojson['height'] == 200:
                            print (f"EXPECTED {identifier} waveform: {filename}")
                        else:    
                            print (f"DIFFERENT {identifier} waveform: {filename} different size: {infojson['width']}, {infojson['height']} from {imgUrl}")
                    except Exception as error:
                        print (f"Failed to get {imgUrl}")    
                        print (error)

                    hasWaveform=True
            if hasWaveform:
                waveform_item_count += 1        

    print (f"Number of items checked: {item_count}")
    print (f"Number of waveforms {waveform_file_count} from {waveform_item_count} items")

if __name__ == "__main__":
    """
        Run this as:
            python -m iiify.loadtest.checkWaveformSizes   
    """
    getAudioItems()