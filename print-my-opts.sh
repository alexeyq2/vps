set -o allexport
source .env set
set +o allexport

echo == настройки
env | grep VPS_
env | grep ACME_
env | grep SUBSCRIPTION_

echo == сертификаты
echo srv/certbot/etc/letsencrypt/live/$VPS_DOMAIN/fullchain.pem
echo srv/certbot/etc/letsencrypt/live/$VPS_DOMAIN/privkey.pem
