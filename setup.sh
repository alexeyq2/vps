#!/bin/bash

# sharry process runs as ordinary user with id=10001 in container
chown 10001 srv/sharry/h2_data srv/sharry/files

echo OK
