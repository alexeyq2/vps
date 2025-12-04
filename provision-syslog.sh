#!/bin/bash -e

# уменьшить размер системных логов /var/log/journal - логи докера могут разрастись до гигабайт
grep "SystemMaxUse=100M" /etc/systemd/journald.conf >/dev/null || echo "SystemMaxUse=100M" >> /etc/systemd/journald.conf
systemctl restart systemd-journald

echo Syslog настроен OK
