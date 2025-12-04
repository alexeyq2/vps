set -o allexport
source .env set
set +o allexport

echo == настройки
env | grep VPS_
env | grep ACME_
env | grep SUBSCRIPTION_

echo == сертификаты
echo /etc/letsencrypt/live/$VPS_DOMAIN/fullchain.pem
echo /etc/letsencrypt/live/$VPS_DOMAIN/privkey.pem
