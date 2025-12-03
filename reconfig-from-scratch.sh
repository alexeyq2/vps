#!/bin/bash -e

./down.sh

sudo rm -rf srv _work
cp -r srv-default srv
mkdir -p _work

./up.sh

echo "Теперь настройте все заново"
