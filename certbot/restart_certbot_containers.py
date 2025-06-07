#!/usr/bin/env python3

import docker

def restart_certbot_containers():
  print('Restarting containers with "certbot_restart" label')
  client = docker.from_env()
  n = 0
  for c in client.containers.list():
    if 'certbot_restart' in c.labels:
      print(f'Restart container {c.name}')
      c.restart()
      n += 1
  
  if n == 0:
    print(f'No containers has been restarted. Is it OK?')

restart_certbot_containers()
