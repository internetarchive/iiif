#!/usr/bin/env bash

cd /app/ifffy;
uwsgi --uid 65534 --gid 65534 --ini uwsgi.ini -s /tmp/uwsgi.sock &
chmod 777 /tmp/uwsgi.sock;
