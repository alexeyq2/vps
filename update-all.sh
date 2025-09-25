#!/bin/bash -e
source dc.inc.sh

./down.sh

git pull

./update-3xui.sh
