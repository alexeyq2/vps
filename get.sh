RELEASE=feature/rusreadme

set -e  # остановиться при ошибке

GREEN=$(tput setaf 2) # Set foreground color to red
NC=$(tput sgr0)    # Reset all attributes

cat << EOF 
$GREEN
          ╔═════════════════╗
          ║  VPS для всех   ║
          ╚═════════════════╝
Установка git, docker, кода проекта, настройка сети.

$NC
EOF


if ! sudo -v; then
    [ $EUID != 0 ] && echo "Не установлен sudo и не root доступ, установка невозможна" && exit 1 
    echo "Устанавливаем sudo..."
    apt update
    apt install -yq sudo
else
    sudo apt update
fi

sudo apt install -y git-core mc curl wget htop
git clone https://github.com/alexeyq2/vps.git
cd vps
git checkout $RELEASE

sudo ./provision-syslog.sh
sudo ./provision-bbr.sh
sudo ./provision-docker.sh

cat <EOF
$GREEN
Далее: 
 * попробуйте команду - должна работать: docker compose -v
     - если нет, перезайдите в систему или выполните: newgrp docker
 * настройте переменные по инструкциям в README.md
 $NC
EOF
