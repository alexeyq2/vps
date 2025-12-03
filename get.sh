echo -e "\033[32m  == VPS для масс == \033[0m"
echo -e "Программа спросит пароль sudo"
echo "- для установки git, docker и настройки сети"
echo "Нажмите Enter чтобы продолжить..."

sudo apt install -y git-core mc curl wget htop
git clone git@github.com:alexeyq2/vps.git
cd vps

./provision-docker.sh
./provision-syslog.sh
./provision-bbr.sh

echo OK
echo Далее настройте переменные по инструкциям в README.md
