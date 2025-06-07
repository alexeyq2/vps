## Installation
1. cp .env-default .env
2. edit .env file
  - VPS_DOMAIN, VPS_EMAIL
  - ACME_SERVER - choose staging server (for testing) or production server
3. cp -r srv-default srv
4. change srv/sharry/opt/sharry.conf, server-secret parameter to something else
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
