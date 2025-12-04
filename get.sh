GREEN=$(tput setaf 2) # Set foreground color to red
NC=$(tput sgr0)    # Reset all attributes

cat << EOF 
$GREEN
        ╔═════════════════╗
        ║  VPS для всех   ║
        ╚═════════════════╝
$NC
Программа спросит пароль sudo для установки 
git, docker и настройки сети
EOF
# read -p "Нажмите Enter чтобы продолжить:"

sudo apt install -y git-core mc curl wget htop
git clone git@github.com:alexeyq2/vps.git
cd vps

./provision-docker.sh
./provision-syslog.sh
./provision-bbr.sh

echo OK
echo Далее настройте переменные по инструкциям в README.md
