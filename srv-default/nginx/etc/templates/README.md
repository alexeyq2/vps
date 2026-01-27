### основной конфиг переопределен и всегда перегенерируется

будет /etc/conf.d/default.conf, а не /etc/nginx.conf, 
см. command в сервисе nginx в compose.yml

default.conf импортирует `все ssl_server*.conf`

### srv/nginx/templates

содержит первичную настройку:
- http сервер на 80 порту для хостинга .well-known папки для certbot 
  (получение и обновление сертификата)
- https сервер на 443 порту для хостинга файлообменника
  он же - собственный сайт-донор сертификата для XRay VLESS-Reality

при каждом старте *.template файлы в этой папке будут обработаны envsubst 
и помещены в /etc/nginx/conf.d/ контейнера.
это фича официального nginx-образа (https://hub.docker.com/_/nginx)
