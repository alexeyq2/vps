#!/bin/bash

echo Check SSL certificate

[ ! -f /etc/letsencrypt/live/$VPS_DOMAIN/fullchain.pem ] && \
    echo "No certificate. Disable SSL" && \
    rm /etc/nginx/conf.d/ssl_server*.conf || \
    true
