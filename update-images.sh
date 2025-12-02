#!/bin/bash -e
source dc.inc.sh

# явно скачать новый certbot, чтобы на его базе скомпилировать свой certbot, рестартующий nginx и xray
# - certbot не качается docker compose pull потому что он компилируется
docker pull certbot/certbot:latest
# скачать новые образы остальных сервисов
docker compose pull

