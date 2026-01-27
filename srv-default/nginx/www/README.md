
### nginx/www/http

- самое важное - папка http://myserver/.well-known/ на порту 80 для certbot
- статический контент на порту 80 - html-перенаправлялка на 443 

### nginx/www/ssl

- статический контент https://myserver
- или дополнительного ssl-сайта на 9090
  (настраивается в srv/nginx/etc/templates)
