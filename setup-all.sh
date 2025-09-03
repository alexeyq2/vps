RELEASE=master

sudo apt install -y git-core mc curl wget htop
git clone git@github.com:alexeyq2/vps.git
cd vps
git checkout $RELEASE

./setup-docker.sh
./setup-syslog.sh
./setup-bbr.sh

echo OK
echo Now follow the instructions in README.md
