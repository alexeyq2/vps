RELEASE=feature/rusreadme

GREEN=$(tput setaf 2) # Set foreground color to red
NC=$(tput sgr0)    # Reset all attributes

cat << EOF 
$GREEN
        ╔═════════════════╗
        ║  VPS для всех   ║
        ╚═════════════════╝
$NC
Установка git, docker, кода проекта, настройка сети.
EOF

sleep 1

which sudo >/dev/null
WHICH_SUDO=$?

set -e  # остановиться при ошибке

if [ $WHICH_SUDO != 0 ]; then
    [ $EUID != 0 ] && echo "Не установлен sudo и не root доступ, установка невозможна" && exit 1 
    echo "Устанавливаем sudo..."
    apt update
    apt install -y sudo
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

echo OK
echo Далее настройте переменные по инструкциям в README.md
