#!/bin/bash -e

CURRENT_USER=${SUDO_USER:-$(whoami)}
echo $CURRENT_USER, $SUDO_USER

if ! docker2 >/dev/null 2>&1; then
  echo NO
else
  echo YES
fi