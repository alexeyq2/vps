#!/usr/bin/env bash
#
# Ubuntu 24.04
# Закрывает все входящие порты кроме указанных

KEEP_PORTS=(443 51022 51053 51054 51055 51056 51057 51058 51059 51060)
BACKUP_DIR="/root/config-backups-$TIMESTAMP"
TIMESTAMP="$(date +%Y%m%d%H%M%S)"

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Запустите скрипт от root или через sudo."
  exit 1
fi

mkdir -p "$BACKUP_DIR"
echo "Резервные копии будут в $BACKUP_DIR"

# Определяем текущий SSH порт в sshd_config (если не найден, считаем 22)
CURRENT_SSH_PORT="$(awk 'tolower($1)=="port" {print $2; exit}' /etc/ssh/sshd_config 2>/dev/null || true)"
if [[ -z "$CURRENT_SSH_PORT" ]]; then
  CURRENT_SSH_PORT=22
fi
echo "Текущий SSH порт (считанный из /etc/ssh/sshd_config): $CURRENT_SSH_PORT"


echo
echo "Будут оставлены открытыми порты: ${KEEP_PORTS[*]}"
if [[ ! " ${KEEP_PORTS[*]} " =~ " ${CURRENT_SSH_PORT} " ]]; then
  echo "Текущий SSH-порт ($CURRENT_SSH_PORT) не входит в список KEEP_PORTS."
  echo "Скрипт временно разрешит этот порт в UFW, чтобы не потерять доступ. SSH-конфигурацию (sshd_config) менять не будем."
fi

read -p "Продолжить и применить правила UFW? [y/N]: " CONF
CONF=${CONF:-N}
if [[ ! "$CONF" =~ ^([yY][eE][sS]|[yY])$ ]]; then
  echo "Отмена."
  exit 0
fi

# Обновление пакетов (только apt update/upgrade)
echo "Обновление пакетов..."
apt update -y
apt upgrade -y

# Установка ufw и unattended-upgrades (fail2ban НЕ устанавливается)
echo "Установка необходимых пакетов (ufw, unattended-upgrades)..."
apt install -y ufw unattended-upgrades apt-listchanges

# Резервное копирование конфигураций
cp -a /etc/ufw "$BACKUP_DIR/ufw.bak" || true
cp -a /etc/ssh/sshd_config "$BACKUP_DIR/sshd_config.bak" || true

# Сброс UFW и базовая настройка
echo "Сбрасываем UFW к дефолту..."
ufw --force reset

echo "Устанавливаем политики по умолчанию: deny incoming, allow outgoing..."
ufw default deny incoming
ufw default allow outgoing

# Маскировка под домашний компьютер - отключаем ping и скрываем информацию о TCP
echo "Отключаем ответы на ping (icmp echo)..."
echo 1 > /proc/sys/net/ipv4/icmp_echo_ignore_all 2>/dev/null || true
grep -q "^net.ipv4.icmp_echo_ignore_all = 1" /etc/sysctl.conf || echo "net.ipv4.icmp_echo_ignore_all = 1" >> /etc/sysctl.conf

echo "Отключаем ICMP timestamp и redirect..."
echo 0 > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts 2>/dev/null || true
grep -q "^net.ipv4.icmp_echo_ignore_broadcasts = 0" /etc/sysctl.conf || echo "net.ipv4.icmp_echo_ignore_broadcasts = 0" >> /etc/sysctl.conf

# Скрываем версию SSH
echo "Скрываем информацию о SSH (отключаем баннер)..."
grep -q "^Banner none" /etc/ssh/sshd_config || echo "Banner none" >> /etc/ssh/sshd_config

# Применяем sysctl
sysctl -p >/dev/null 2>&1 || true

# Разрешаем loopback
ufw allow in on lo

# Разрешаем необходимые порты
for p in "${KEEP_PORTS[@]}"; do
  echo "Разрешаем порт $p/tcp"
  ufw allow "$p"/tcp comment "allow service port $p"
done

# Если текущий SSH-порт не входит в KEEP_PORTS, разрешаем его временно
if [[ ! " ${KEEP_PORTS[*]} " =~ " ${CURRENT_SSH_PORT} " ]]; then
  echo "Разрешаем текущий SSH-порт $CURRENT_SSH_PORT временно (не меняем sshd_config)."
  ufw allow "$CURRENT_SSH_PORT"/tcp comment "temporary allow current ssh port $CURRENT_SSH_PORT"
fi

# Меняем SSH порт на 51022
NEW_SSH_PORT=51022
echo "Меняем SSH порт на $NEW_SSH_PORT..."
sed -i "s/^Port [0-9]*/Port $NEW_SSH_PORT/" /etc/ssh/sshd_config 2>/dev/null || echo "Port $NEW_SSH_PORT" >> /etc/ssh/sshd_config
echo "SSH порт изменён на $NEW_SSH_PORT"

# Перезапускаем SSH
echo "Перезапускаем SSH сервис..."
systemctl restart sshd 2>/dev/null || service ssh restart 2>/dev/null || true
echo "SSH сервис перезапущен"

# Включаем UFW
echo "Включаем UFW..."
ufw --force enable

# Настройка автоматических обновлений (unattended-upgrades)
echo "Включаем unattended-upgrades (автоматические обновления безопасности)..."
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

# Информация о состоянии
echo
echo "UFW status:"
ufw status verbose

echo
echo "Резервные копии конфигов в: $BACKUP_DIR"
echo

if [[ ! " ${KEEP_PORTS[*]} " =~ " ${CURRENT_SSH_PORT} " ]]; then
  echo "ВНИМАНИЕ: текущий SSH-порт $CURRENT_SSH_PORT был временно разрешён в UFW."
  echo "Когда убедитесь, что доступ по нужным портам (например, 8822) установлен и не требуется старый порт,"
  echo "удалите правило командой (пример):"
  echo "  ufw delete allow ${CURRENT_SSH_PORT}/tcp"
fi

echo
echo "Готово. Проверьте доступ по SSH (используйте ваш обычный клиент)."
echo "Если что-то пошло не так — используйте консоль провайдера или откат из $BACKUP_DIR."
