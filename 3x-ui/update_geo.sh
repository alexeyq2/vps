#!/bin/bash -e
# можно и -ex
<<DOC
флаги запуска скрипта bash

-e: останавливать по ошибке если выполненная команда вернула не 0.
    хорошо для надежности, но накладывает определенный стиль,
    т.к. некоторые команды ожидаемо что-то не находят, например grep.
    в таких случаях можно писать $(command || true)

-ex: отладка, печатать выполняемую строчку
DOC

echo "START $(date)"

# случайная задержка ~1min, хорошо для периодичных задач cron
delay=$((RANDOM % 60 + 10))  # в shell есть генератор случайный чисел [0...65535]
[ "$1" != "now" ] && echo "Begin geofiles update in $delay seconds" && sleep $delay

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


get_file_size() {
  file=$1
  [ -f $file ] && stat -c %s $file || echo "0"
}

get_url_size() {
  # HTTP HEAD, следовать по всем редиректам (location) и взять размер последнего (tail -1)
  # будет строка вида
  # Content-Length: 12345\r
  # далее awk '{print $2}' возьмет 2й столбец
  # далее tr -cd 0-9 - удалит \r, который может быть в конце (оставит только числа)
  url=$1
  length="$(curl --silent --head --location $url | grep -i content-length | tail -1 | awk '{print $2}' | tr -cd 0-9)"
  echo $length
}

need_download() {
  url=$1
  file=$APPDIR/$2

  [ ! -f $file ] && echo "$file has been not downloaded yet" && return 0

  latest="$(get_url_size $url)"
  existing=$(get_file_size $file)

  # одностроковый "bashism" заменяет if/else/then
  [ "$latest" = "$existing" ] && echo "" || echo "$file size has been changed, '$latest' != '$existing'"
}

download()
{
  url=$1
  file=$2

  if [ "$(need_download $url $file)" != "" ]; then
    echo $file $url
    curl -L -s $url >$file
    if [ "$(get_file_size $file)" -eq 0 ]; then
      echo "Error download $url"
      return 1
    fi
    nDownloads=$((nDownloads + 1)) # shell понимает арифметику в $((в двойных скобках)) 
  else
    echo "$file is up-to-date"
  fi
}

restart_xray() {
  XRAY_PID=$(pgrep xray-linux || true) # или true чтобы не упало по ошибке если pgrep не нашел (скрипт работает с параметром -e)
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
    cp -f geo*.dat $APPDIR
    restart_xray
  fi
}

### Поехали!

start_sec=$(date +%s)
update_geo

### суперфича скриптов - "here-doc"
<<HOW_TO_USE_IN_ROUTES

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

HOW_TO_USE_IN_ROUTES
# закончен HERE-doc, продолжается скрипт. важно после метки HOW_TO_USE_IN_ROUTES не оставить пробел!

echo Geofiles update OK in $(($(date +%s) - start_sec)) sec
