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

valid_filetypes = ['jpg', 'jpeg', 'png', 'gif', 'tif', 'jp2', 'pdf', 'tiff']
AUDIO_FORMATS = ['VBR MP3', '32Kbps MP3', '56Kbps MP3', '64Kbps MP3', '96Kbps MP3', '128Kbps MP3', 'MPEG-4 Audio', 'Flac', 'AIFF', 'Apple Lossless Audio', 'Ogg Vorbis', 'WAVE', '24bit Flac', 'Shorten']
VIDEO_FORMATS = ['MPEG4', 'h.264 HD', 'h.264 MPEG4', '512Kb MPEG4', 'HiRes MPEG4', 'MPEG2', 'h.264', 'Matroska', 'Ogg Video', 'Ogg Theora', 'WebM', 'Windows Media', 'Cinepack', 'QuickTime']
