#!/bin/bash -e
source dc.inc.sh

$DC down

$DC pull
docker pull certbot/certbot:latest
docker pull ghcr.io/mhsanaei/3x-ui:latest

$DC build
$DC up -d --remove-orphans
