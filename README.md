# iiif.archive.org

The Internet Archive's official IIIF 3.0 Image & Presentation API

## Background

This service replaces the iiif.archivelab.org unofficial labs API.

## Technical Details

The service uses a manifest/API service written in python3 flask and makes image processing calls to cantaloupe in both iiif 3.0 and 2.0 format.

## Installation & Setup
```
git clone https://github.com/internetarchive/iiif.git
cd iiif
pip install .
python app.py
```
Navigate to http://127.0.0.1:8080/iiif

You can also run the app using Docker, either with the Flask development server:
```
docker build -t iiify .
docker run -d --rm --name iiify -p 8080:8080 iiify
```
or with an image using nginx and uwsgi:
```
docker build -t iiify-uwsgi -f Dockerfile-uwsgi .
docker run -d --rm --name iiify -p 8080:8080 iiify-uwsgi
```

Navigate to http://127.0.0.1:8080/iiif

## Testing

Unit tests are in the `tests` folder and can be run with:
```
python -m unittest discover -s tests
```

Retrieve large.jpg as 800px wide JPEG
* http://127.0.0.1:8080/iiif/large.jpg/full/800,/0/default.jpg 

Crop into large.jpg and return 800px wide JPEG
* http://127.0.0.1:8080/iiif/large.jpg/full/800,/0/default.jpg 

Mirror large.jpg horizontally and return 800px wide JPEG
* http://127.0.0.1:8080/iiif/large.jpg/full/800,/!0/default.jpg 
