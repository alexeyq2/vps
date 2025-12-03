# VPS для всех

- Веб-панель 3X-UI для X-Ray
- Автообновление geo.dat файлов для маршрутизации X-Ray
- Ваш сайт с SSL от Let's Encrypt для VLESS
- Предустановленный файлообменник c веб-мордой

## Установка на чистый VPS (Ubuntu 24.04 LTS)
 
Установить git, docker, скачать код проекта
`./get.sh`  # 

## Настройка
1. `cp .env-default .env` # файл с вашим доменом
2. отредактируйте `.env`, переменные:
  - VPS_DOMAIN - ваш домен
  - VPS_EMAIL  - ваш email (необязательно, для Let's Encrypt)
  - ACME_SERVER - выберите тестовый или боевой сервер Let's Encrypt
  - SUBSCRIPTION_URL - уникальный путь (секретный) для подписок(subscription) файла VPN-клиентов. Поменяйте на что-нибудь свое, чтобы не палиться.
3. `cp -r srv-default srv`  # "srv" — тут хранятся конфиги и данные.

## Важные папки и файлы

    srv - файлы конфигурации, база данных, файлообменник.
        - сохраняйте эту папку при обновлении или переустановке
    srv-default - скопируйте в "srv" и начинайте с неё
    _work - рабочие файлы. можно удалять
    .env - здесь вы настраиваете "VPS для масс" под себя

## Запуск, остановка, логи

* `./up.sh`   # docker compose up [-d]
* `./down.sh` # docker compose down
* `./log.sh`  # docker compose logs [-f]

## Переключение с тестового сертификата на боевой

Если всё работает и сайт открывается с тестовым SSL, можно получить реальный сертификат:

1. Раскомментируйте production ACME_SERVER в файле `.env`
2. остановите certbot
. удалите файлы
. запустите сертбот

Проверьте, что certbot получил сертификат:

3. `docker compose logs -f certbot`

Ожидаемый вывод:

    certbot_1      | certbot renew loop start
    ...
    certbot_1      | Requesting a certificate for <VPS_DOMAIN>
    certbot_1      | Using the webroot path /nginx/www/http for all unmatched domains.
    certbot_1      | Waiting for verification...
    certbot_1      | Running deploy-hook command: /app/restart_certbot_containers.py
    certbot_1      | Hook 'deploy-hook' ran with output:
    certbot_1      |  Restarting containers with "certbot_restart" label
    certbot_1      |  Restart container vps_3x-ui_1

## Обновление

Обновить всё:

`./update.sh`

Обновить certbot, 3x-ui и nginx:

```
./down.sh
./update-images.sh
./up.sh
```

Обновить этот проект:

```
./down.sh
./update-code-and-build.sh
./up.sh
```


## Реконфигурация с нуля

Удалите `srv` и `_work`, скопируйте `srv-default` в `srv` и повторите шаги установки. Следующий скрипт это делает:


`./reconfig.sh`



