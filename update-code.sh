#!/bin/bash -e
source dc.inc.sh

git pull
$DC build
