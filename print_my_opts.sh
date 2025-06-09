set -o allexport
source .env set
set +o allexport

echo == настройки
env | grep VPS
env | grep ACME

echo == сертификаты
echo /etc/letsencrypt/live/$VPS_DOMAIN/fullchain.pem
echo /etc/letsencrypt/live/$VPS_DOMAIN/privkey.pem
