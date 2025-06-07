#!/usr/bin/env python3

import random, time, os
from datetime import datetime

os.system('envsubst < cli.ini.template > /etc/letsencrypt/cli.ini')

print('certbot renew loop start', datetime.now())

 # создать/обновить сертификат
if os.system('certbot certonly'): 
  print('certbot certonly failed')
  exit(2)

# раз в пару дней проверять обновление
while True:
  seconds_in_hour = 60 * 60
  day_or_two = (24 + random.randint(0, 24)) * seconds_in_hour
  time.sleep(day_or_two)
  print(datetime.now())
  os.system('certbot renew')
