#!/bin/bash -e

NOFILE=524282
# NOFILE=65535

sudo mkdir -p /etc/systemd/system/docker.service.d

cat <<EOF | sudo tee /etc/systemd/system/docker.service.d/limits-no-file.conf >/dev/null
[Service]
LimitNOFILE=$NOFILE
EOF

sudo systemctl daemon-reload
sudo systemctl restart docker

sudo prlimit --nofile --output RESOURCE,SOFT,HARD --pid $(pgrep dockerd) | grep "NOFILE\s*$NOFILE" > /dev/null || \
    (echo "Ошибка: Лимиты не применились" && exit 1)

echo "${GREEN}Лимиты для Docker - OK${NC}"
