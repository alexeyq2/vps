RELEASE=master

sudo apt install -y git-core mc curl wget htop
git clone git@github.com:alexeyq2/vps.git
cd vps
git checkout $RELEASE

./provision-docker.sh
./provision-syslog.sh
./provision-bbr.sh

echo OK
echo Далее настройте переменные по инструкциям в README.md
