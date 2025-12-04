# VPS для всех

- Веб-панель 3X-UI для X-Ray
- Автообновление geo.dat файлов для маршрутизации X-Ray
- Свой сайт с SSL от Let's Encrypt для VLESS
- Файлообменник c веб-мордой

## Установка на чистый VPS (Ubuntu 24.04 LTS)
 
Установить git, docker, скачать код проекта

`curl -sL https://raw.githubusercontent.com/alexeyq2/vps/refs/heads/master/install.sh | bash`

## Настройка
1. Создайте файл  `.env` из шаблона

    `cp .env-default .env` 

2. отредактируйте `.env`, переменные:
  - `VPS_DOMAIN` - свой домен
  - `VPS_EMAIL`  - свой email (необязательно, для Let's Encrypt)
  - `ACME_SERVER` - тестовый или боевой сервер Let's Encrypt
  - `SUBSCRIPTION_URL` - уникальный путь (секретный) для подписок (subscription) VPN-клиентов. Поменяйте на что-нибудь свое, чтобы не палиться.

3. Создайте папку `srv` — тут хранятся конфиги VPN, сертификат и содержимое веб-сайта.

   `cp -r srv-default/ srv/`

### Важные папки и файлы

    srv - файлы конфигурации, база данных, файлообменник.
        - сохраняйте эту папку при обновлении или переустановке
    srv-default - скопируйте в "srv" и начинайте с неё
    _work - рабочие файлы. можно удалять
    .env - здесь вы настраиваете VPS под свой домен

### Запуск, остановка, логи

* `./up.sh`   # docker compose up [-d]
* `./down.sh` # docker compose down
* `./log.sh`  # docker compose logs [-f]

### Проверить, что certbot получил сертификат:

 `./logs.sh -f certbot`

Ожидаемый вывод:

```
certbot-1      | Successfully received certificate.
certbot-1      | Certificate is saved at: /etc/letsencrypt/live/VPS_DOMAIN/fullchain.pem
certbot-1      | Key is saved at:         /etc/letsencrypt/live/VPS_DOMAIN/privkey.pem
certbot-1      | This certificate expires on YYYY-MM-SS.
certbot-1      | These files will be updated when the certificate renews.
certbot-1      | NEXT STEPS:
```

### Cоздайте Inbound в 3X-UI:

Входящее HTTPS-соединение попадает на 3X-UI, это он сидит на внешнем интерфейсе. Nginx слушает только на внутреннем `localhost:10443`. 3X-UI перенаправляет внешний порт 443 на внутренний nginx.

    браузер -> VPS_DOMAIN:443 
        -> 3x-ui vless inbound:443
            -> nginx docker container:10443 


Параметры Inbound в 3X-UI (остальные можно не трогать):

    Protocol: vless
    Port: 443
    Security - выбрать вкладку Reality
        Target: 127.0.0.1:10443
        SNI: VPS_DOMAIN
        Public Key/Private Key - нажмите кнопку "Get New Cert"

С таким Inbound будет работать `https://VPS_DOMAIN` .

### Настройка панели 3X-UI

`http://VPS_IP_ADDRESS:2053` admin:admin

1. сменить порт с 2053 на что-то побольше 10000
2. включить HTTPS - указать сертификат и ключ к нему

   `print-my-opts.sh` напечатает путь к сертификату, как его указывать в панели
   
3. сменить пароль админа

### Переключение с тестового сертификата на боевой

Если всё работает и сайт открывается с тестовым SSL, можно получить реальный сертификат:

1. Раскомментируйте production ACME_SERVER в файле `.env`
2. Запустите `./delete-certificate.sh`
3. Выведется лог получения сертификата


### Окончательная настройка VPN

* Донастроить Inbound, если хочется. Выключить встроенный Subscription service.
* Создать клиента и указать `flow: xtlx-rprx-vision`. Это и есть **VLESS-Reality**.
* Нажать иконку QR-кода и импортировать подключение в vpn-клиент.
* ВНИМАНИЕ! Лучше заходить на панель по IP-адресу, а не по имени домена, чтобы QR и ключи для адреса создавались.

### Настройка подписки

Когда есть несколько серверов и они периодически "переезжают" и переконфигурятся, программы-клиенты умеют обновлять ключи из специального URL, который называется подписка (subscription).

Специальный `https://$YOURDOMAIN/$SUBSCRIPTION_URL` показывает содержимое файла `srv/nginx/www/subscription/ss.base64`. Меняя этот файл мы обновляем всех клиентов. Подробности в subscriptions/README.txt

Subscription - полезная фича.

## Пароль к FileBrowser

Пишется в лог при первом старте. Нужно удалить все данные filebrowser и он создаст новый пароль и напишет в лог. Следующая команда сделает это и выведет пароль:

`./delete-filebrowser-data.sh`
    
    filebrowser-1  | User 'admin' initialized with randomly generated password: zbKQSdn9VJPM6kAV

## Обновление

Обновить всё: 

`./update.sh`

Обновить certbot, 3x-ui и nginx:

```
./down.sh
./update-images.sh
./up.sh
```

Обновить только код этого проекта:

```
./down.sh
./update-code-and-build.sh
./up.sh
```

## Реконфигурация с нуля

Удалите `srv` и `_work`, скопируйте `srv-default` в `srv` и повторите настройку. Следующий скрипт все сбросит как было (кроме  `.env` - его вы, скорее всего, хотите оставить):

`./reconfig-from-scratch.sh`

# Вроде всё
Настройка, собственно, VPN VLESS в панели 3X-UI с картинками будет позже. Впрочем, таких гайдов много. Данный проект призван:
- автоматизировать получение/обновление сертификатов для режима VLESS-Reality "сертификат берем у себя"
- обновлять geo-файлы, чтобы **трафик до России заворачивать назад через российский прокси, снижая шансы обнаружения VPN**.
- поднять ненапряжное файлохранилище, чтобы можно было дать прямую ссылку на файлы и скачать без регистрации. 10-20гигов на бесплатные облака не загрузить.

### А нет, еще можно...
Отключить на сервере ping, перевесить sshd c 22 порта на повыше, прикрутить бесплатную graphana и мониторить загрузку VPS. И что-то еще было с UDP... 


ОК, пока пойдет.

### Правильный вариант небольшого группового VPN:
- два сервера за границей (один может сломаться) 
- один в России (для заворачивания трафика назад и доступа к госуслугам из-за рубежа)
- URL с подпиской, в которой оба заграничных VPS

◼
