FROM ghcr.io/mhsanaei/3x-ui:latest
# FROM ghcr.io/mhsanaei/3x-ui:2.5.6

# curl для скачки geodb-файлов (wget в контейнере оставляет зобми процессы <defunc> по неизвестным причинам)
# Midnight Commander (mc), чтобы проще находить файлы сертификатов - они будут в
# - /cert-staging/MYDOMAIN.crt
# - /cert-staging/MYDOMAIN.key
# а после отладки в 
# - /cert/MYDOMAIN.crt
# - /cert/MYDOMAIN.key
#
# зайти в контейнер:
# docker-compose exec 3x-ui sh
#    (или сразу - mc)
# docker-compose exec 3x-ui mc
#
RUN apk add --no-cache curl mc
COPY DockerEntrypoint2.sh update_geo.sh crontab.txt /app/
RUN chmod 755 /app/update_geo.sh /app/DockerEntrypoint2.sh

ENTRYPOINT [ "/app/DockerEntrypoint2.sh" ]
