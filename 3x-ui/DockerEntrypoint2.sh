#!/bin/sh

# настроить и запустить crond на периодичный запуск обновления geo-файлов
/usr/bin/crontab /app/crontab.txt
/usr/sbin/crond

# при старте контейнера сразу обновить geo-файлы (в фоне)
# - nohup - отсоединить дочерний процесс от stdin/stdout и сигналов текущего процесса
# - & в конце - запустить в фоне
# - конструкция 2>&1 значит перенаправить stderr (поток 2) в stdout (поток 1)
nohup /app/update_geo.sh > /app/update_geo/update_geo.log 2>&1 &

# передача управления стандартному контейнеру 3X-UI
exec /app/DockerEntrypoint.sh
