#!/bin/bash -e
source dc.inc.sh

$DC down
$DC pull
$DC build
$DC up -d --remove-orphans
