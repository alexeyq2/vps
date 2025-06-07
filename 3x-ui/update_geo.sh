#!/bin/ash -e
# можно и -ex
<<DOC
флаги запуска скрипта для ash/bash

-e: останавливать по ошибке если выполненная команда вернула не 0.
    хорошо для надежности, но накладывает определенный стиль,
    т.к. некоторые команды ожидаемо что-то не находят, например grep.
    в таких случаях можно писать $(command || true)

-ex: отладка, печатать выполняемую строчку

== разработка на Kububtu, сразу под Alpine/ash, есть отличия от bash

1. в контейнере запускать скрипт из смонтированной в /app текущей папки
   для краткости добавить в ~/.bashrc

alias dco="docker container"

   перезапустить терминал (или в нем же запустить новый bash)

dco create -v .:/app alpine /app/update_geo.sh
622...84fec

2. запустить, смотреть лог и остановить по Ctrl-C

NN=622 bash -c -i 'dco start $NN && dco logs $NN -f -n 0 || dco stop $NN -s 9'
 
  конструкция (cmd1 && cmd2 || cmd3) выполнит cmd3 после прерывания cmd2.
  
  cmd1 - запустит контейнер в фоне
  cmd2 - будет выдавать логи до прерывания по Ctrl-C и вернет ошибку
  cmd3 - остановит контейнер без мучений (SIGKILL=9)

  bash -i нужно чтобы считался .bashrc
  -c чтобы запускался дочерний процесс, в котором есть переменная NN

  полезные команды
dco ps, dco run, dco -ti exec, dco prune (!) docker system prune (!)

== можно сидеть прямо в контейнере

dco run -v .:/app alpine sh -c 'while :; do echo here; sleep 60; done'
# посмотреть ID контейнера и зайти в него
dco ps
622...84fec
dco exec -ti 622 sh
  / # внутри
app/update_geo.sh
 
DOC

# случайная задержка ~1min, хорошо для периодичных задач cron
delay=$((RANDOM % 60 + 10))  # ого! в shell есть генератор случайный чисел [0...65535]
echo $(date)
echo Start geofiles update in $delay seconds
sleep $delay

### настройки скрипта и подготовка

WORKDIR=/app/geo
APPDIR=/app/bin

# есть curl?
which curl || apk --no-cache add curl

mkdir -p $WORKDIR # -p не вызовет ошибки есть папка уже есть
mkdir -p $APPDIR
cd $WORKDIR

# глобальные переменные - это нормально!
nDownloads="0"

get_url_info() {
  # HTTP HEAD, следовать по всем редиректам (location) и взять размер последнего (tail -1)
  echo "$(curl --silent --head --location $1 | grep content-length | tail -1)"
}

need_download() {
  url=$1
  file=$2

  [ ! -f $file.info ] && echo "$file has been not downloaded yet" && return 0

  info="$(get_url_info $url)"
  prev=$(cat $file.info)  # cat - конструкция $(<file.info) не работает в ash

  # красивый одностроковый "bashism" вместо громоздкого if/else/then
  [ "$info" = "$prev" ] && echo "" || echo "$file changed"
}

download()
{
  url=$1
  file=$2

  if [ "$(need_download $url $file)" != "" ]; then
    echo $file $url
    curl -L -s $url >$file
    echo "$(get_url_info $url)" > $file.info
    nDownloads=$((nDownloads + 1)) # shell понимает арифметику в $((в двойных скобках)) 
  else
    echo "$file is up-to-date"
  fi
}

restart_xray() {
  XRAY_PID=$(pgrep xray-linux || true) # или true чтобы не упало по ошибке если pgrep не нашел
  if [ "$XRAY_PID" != "" ]; then
    echo Restart xray pid=$XRAY_PID && kill $(pgrep xray-linux)
  else
    echo No xray is running, skip restart
  fi
}

update_geo() {
  download https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat \
    geoip.dat
  download https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat \
    geosite.dat
  download https://github.com/runetfreedom/russia-v2ray-rules-dat/releases/latest/download/geoip.dat \
    geoip_RU.dat
  download https://github.com/runetfreedom/russia-v2ray-rules-dat/releases/latest/download/geosite.dat \
    geosite_RU.dat

  if [ "$nDownloads" != "0" ]; then
    echo Geofiles are different, update
    mv -f geo*.dat $APPDIR
    restart_xray
  fi
}

### Поехали!

start_sec=$(date +%s)
update_geo

### суперфича скриптов - "here-doc"
<<USE_IN_ROUTES

in 3x-ui no spaces (!), comma-delimited
in nekoray - line by line

в 3x-ui вставлять без пробелов (!), через запятую
в nekoray - каждая запись в новой строке

3X-UI:

== IP ==
geoip:ru,ext:geoip_RU.dat:ru

== Domain ==
geosite:category-gov-ru,ext:geosite_RU.dat:category-gov-ru,regexp:.*\.ru$,regexp:.*\.xn--p1ai$

Nekoray:

== IP ==
geoip:ru
ext:geoip_RU.dat:ru

== Domain ==
geosite:category-gov-ru,
ext:geosite_RU.dat:category-gov-ru,
regexp:.*\.ru$,
regexp:.*\.xn--p1ai$  
       ^ домены .рф ^

USE_IN_ROUTES
# закончен HERE-doc, продолжается скрипт. важно после метки USE_IN_ROUTES не оставить пробел!

echo Geofiles update OK in $(($(date +%s) - start_sec)) sec
