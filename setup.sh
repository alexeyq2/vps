#!/bin/bash -e

# sharry process runs as ordinary user with id=10001 in container
chown 10001 srv/sharry/h2_data srv/sharry/files

# limit size of logs (docker logs may grow) /var/log/journal
grep "SystemMaxUse=100M" /etc/systemd/journald.conf >/dev/null || echo "SystemMaxUse=100M" >> /etc/systemd/journald.conf
systemctl restart systemd-journald

echo OK
