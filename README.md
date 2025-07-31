# VPS for masses

- 3X-UI web panel for X-Ray
- autoupdate X-Ray geodat files for routing
- your own website with Let's Encrypt SSL certificate for VLESS
- preinstalled web-based file share

## Provision fresh VPS (Ubuntu 24.04 LTS)
1. `./setup-docker.sh`  # install docker and docker compose
2. `./setup-syslog.sh`  # reduce systemlog size (default is too much and eats disk space)
3. `./optimize.sh`      # set up better TCP packets processig (BBR)

## Installation
1. `cp .env-default .env` # file with your domain name
2. edit .env file, variables:
  - VPS_DOMAIN - your domain
  - VPS_EMAIL  - your email (optional, for Let's Encrypt)
  - ACME_SERVER - choose Let's Encrypt testing server or production server
3. `cp -r srv-default srv`  # "srv" is where configs and data files will live
4. `sudo ./setup.sh`

## Start, Stop, Logs

* `./up.sh`   # docker compose up [-d]
* `./down.sh` # docker compose down
* `./log.sh` # docker compose logs [-f]

## Switch testing certificate to production

If everything runs and your website opens and has testing SSL cert, you want real certificate. 

1. Uncomment production ACME_SERVER in .env file
2. Run `./update.sh`

Check that certbot has got new cert

3. `docker compose logs -f certbot`

Output should lool like below:

    certbot_1      | certbot renew loop start
    ...
    certbot_1      | Requesting a certificate for <VPS_DOMAIN>
    certbot_1      | Using the webroot path /nginx/www/http for all unmatched domains.
    certbot_1      | Waiting for verification...
    certbot_1      | Running deploy-hook command: /app/restart_certbot_containers.py
    certbot_1      | Hook 'deploy-hook' ran with output:
    certbot_1      |  Restarting containers with "certbot_restart" label
    certbot_1      |  Restart container vps_3x-ui_1

## Update

update everything

`git pull && ./update.sh`

update 3X-UI and nginx only

`./update.sh`


## Reinstall

- `./down.sh`
- `./reinstall.sh`
- `./up.sh`

Basically, copy srv-default to srv and repeat installation steps (set up config files and permissions)


## Important folders and files

    srv - config files, database, uploaded files
        - keep this folder when update or reinstall
    srv-default - copy to "srv" and begin with it
    _work - working files. safe to remove
    .env - here you set up your domain name

