## Installation
1. cp .env-default .env
2. edit .env file
  - VPS_DOMAIN, VPS_EMAIL
  - ACME_SERVER - choose staging server (for testing) or production server
3. cp -r srv-default srv
4. "srv" is where configs and data will live
5. sudo ./setup.sh
6. docker compose up [-d]
7. docker compose logs [-f]

## Update
    docker compose down
    git pull
    docker compose build
    docker compose up -d

## Folders
    srv - config files, database, uploaded files
        - keep this folder when update or reinstall
    srv-default - copy to "srv" and begin with it
    _work - working files. safe to remove

## Start from scratch (reinstall)
remove srv and _work, 
copy srv-default to srv and repeat installation steps (set up config files and permissions)


## Switch testing (staging) certificate to production

    docker compose stop
    sudo rm -rf srv/certbot
    docker compose start

docker compose logs -f certbot
    certbot_1      | certbot renew loop start [...]
    ...
    certbot_1      | Requesting a certificate for <VPS_DOMAIN>
    certbot_1      | Using the webroot path /nginx/www/http for all unmatched domains.
    certbot_1      | Waiting for verification...
    certbot_1      | Running deploy-hook command: /app/restart_certbot_containers.py
    certbot_1      | Hook 'deploy-hook' ran with output:
    certbot_1      |  Restarting containers with "certbot_restart" label
    certbot_1      |  Restart container vps_nginx_1
    certbot_1      |  Restart container vps_3x-ui_1
