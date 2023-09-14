#!/usr/bin/env bash

export

envsubst '$NOMAD_HOST_ADDR_cantaloupe' < nginx-vhost.conf > /etc/nginx/conf.d/nginx.conf

envsubst '$NOMAD_HOST_ADDR_cantaloupe' < settings.cfg > iiify/configs/settings.cfg

# Call the regular start.sh for the uwsgi container..

/start.sh
