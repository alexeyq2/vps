#!/usr/bin/env python3

import random, time, os
from datetime import datetime

os.system('envsubst < cli.ini.template > /etc/letsencrypt/cli.ini')

print('certbot renew loop start', datetime.now())

time.sleep(random.randint(1, 7))  # не сразу после запуска контейнера стучаться на letsencrypt

seconds_in_hour = 60 * 60

# создать/обновить сертификат
# если не удалось - ждать несколько часов и пробовать снова, не выходя из скрипта, 
# чтобы контейнер не перезапускался часто и не долбил letsencrypt, иначе забанят.
# если такое случится, они пришлют письмо на email, указанный при создании сертификата с инструкцией как разблокировать
while os.system('certbot certonly'):
  some_hours = (1 + random.randint(0, 4)) * seconds_in_hour
  print('ERROR certbot certonly. Wait', some_hours // 60, 'minutes before retry')
  time.sleep(some_hours)
  print(datetime.now())
  

# раз в пару дней проверять обновление
while True:
  day_or_two = (24 + random.randint(0, 24)) * seconds_in_hour
  time.sleep(day_or_two)
  print(datetime.now())
  os.system('certbot renew')
