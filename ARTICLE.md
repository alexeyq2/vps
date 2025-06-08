# алиасы в баше делать чтобы поменьше писать
#
# $ cat ~/.bashrc | tail -n 5
# alias dco="docker container"
# alias run="NN=622 bash -c -i 'dco start $NN && dco logs $NN -f -n 0 || dco stop $NN -s 9'"
# alias dcomp="docker compose"
# alias dcompre="dcomp down && dcomp build && dcomp up"


3X-UI 

поменять порт
и URI path

сетрификаты
/etc/letsencrypt/live/<VPS_DOMAIN>/fullchain.pem
/etc/letsencrypt/live/<VPS_DOMAIN>/privkey.pem

inbound vless
client - flow
dest 127.0.0.1:10443
SNI <VPS_DOMAIN>
get new cert button

sharry.conf
    auth {

      # The secret for this server that is used to sign the authenicator
      # tokens. You can use base64 or hex strings (prefix with b64: and
      # hex:, respectively)
      server-secret = "hex:0102caffee9884451242"

chown 10001 srv/sharry/h2_data srv/sharry/files

логи nginx будут показывать IP-адрес контейнера 3x-ui, а не пользователя. можно не отключать логирование ради удобства расследования инцидентов.
- а вот и нет! для plain http есть адрес и для ошибок тоже. надо скрывать!

===
после установки и запуска
docker compose logs certbot
открыть http://<VPS_SERVER>:80
будет страница-перенаправялка на https.