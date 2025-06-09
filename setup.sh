#!/bin/bash -e

# limit size of logs (docker logs may grow) /var/log/journal
grep "SystemMaxUse=100M" /etc/systemd/journald.conf >/dev/null || echo "SystemMaxUse=100M" >> /etc/systemd/journald.conf
systemctl restart systemd-journald

echo OK
