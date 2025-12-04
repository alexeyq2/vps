RELEASE=feature/rusreadme

GREEN=$(tput setaf 2) # Set foreground color to red
NC=$(tput sgr0)    # Reset all attributes

cat << EOF 
$GREEN
        ╔═════════════════╗
        ║  VPS для всех   ║
        ╚═════════════════╝
$NC
Будут выполнены:
Установка git, скачивание кода проекта, установка docker, настройка сети.
Скрипт спросит пароль sudo.
EOF

read -p "Нажмите Enter чтобы продолжить:"


sudo apt install -y git-core mc curl wget htop
git clone git@github.com:alexeyq2/vps.git
cd vps
git checkout $RELEASE

sudo ./provision-docker.sh
sudo ./provision-syslog.sh
sudo ./provision-bbr.sh

echo OK
echo Далее настройте переменные по инструкциям в README.md
