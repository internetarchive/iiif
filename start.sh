#!/usr/bin/env bash

cp nginx-vhost.conf /etc/nginx/conf.d/nginx.conf

# Call the regular start.sh for the uwsgi container..

/start.sh
