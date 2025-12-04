RELEASE=feature/rusreadme

set -e  # остановиться при ошибке

GREEN=$(tput setaf 2) # Set foreground color to red
NC=$(tput sgr0)    # Reset all attributes

cat << EOF 
$GREE
* VPS со своим HTTPS для VLESS
* (вариант steal-from-yourself)
*
+ URL подписки для программ-клиентов (subscription URL)
+ файлообменник с веб-мордой
+ автоматическое обновление geoip и geoip_RU файлов

Подготовка машины:
* Установка git, docker, утилит, настройка сети
* Скачивание кода проекта

$NC
EOF


if ! sudo --version >/dev/null; then
    [ $EUID != 0 ] && echo "Не установлен sudo и не root доступ, установка невозможна" && exit 1 
    # мы - root без sudo
    # все равно поставим sudo, далее скрипт должен его использовать - он может быть запущен и не от root

    echo "Устанавливаем sudo..."
    apt update
    apt install -yq sudo
else
    sudo apt -q update
fi

sudo apt install -yq git-core curl wget htop mc vim nano apt-transport-https ca-certificates

## Логи
# уменьшить размер системных логов - логи докера могут разрастись до гигабайт в /var/log/journal
grep "SystemMaxUse=100M" /etc/systemd/journald.conf >/dev/null || echo "SystemMaxUse=100M" | sudo tee -a /etc/systemd/journald.conf
sudo systemctl restart systemd-journald
echo Syslog настроен OK

## BBR

CHANGED=false

add_if_missing() {
    grep -q "^[[:space:]]*$1[[:space:]]*=" "/etc/sysctl.conf" 2>/dev/null || {
        echo "$1" >> "/etc/sysctl.conf"
        echo "Добавлено: $1"
        return 0
    }
    return 1
}

add_if_missing "net.core.default_qdisc=fq" && CHANGED=true
add_if_missing "net.ipv4.tcp_congestion_control=bbr" && CHANGED=true

$CHANGED && sudo sysctl -p >/dev/null 2>&1

echo "Текущие настройки TCP:"
sysctl net.ipv4.tcp_congestion_control net.core.default_qdisc


## DOCKER COMPOSE v2
install_docker_compose_v2() {    
    if docker compose --version &> /dev/null ;then
        echo Docker уже установлен, отлично! OK
        return 0
    fi

    # Add Docker's official GPG key:
    apt-get update
    apt-get install -y ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update

    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    systemctl enable docker
    systemctl start docker

    CURRENT_USER=${SUDO_USER:-$(whoami)}
    usermod -aG docker $CURRENT_USER
    newgrp docker

    # Проверка docker compose
    if docker compose --version &> /dev/null; then
        echo "Docker Compose установлен. OK"
    else
        echo "Ошибка. docker compose --version не запускается. Проверьте установку."
        return 1
    fi

    # Проверка Docker (ваш существующий код)
    if docker run ubuntu echo hello-world &> /dev/null ;then
        echo "Docker работает отлично! OK"
    else
        echo "Docker не смог запустить контейнер. Проверьте установку." 
        echo "Перезайдите в систему или выполните: newgrp docker"
        return 1
    fi
}

install_docker_compose_v2 || exit 1

## Код проекта
VPS_DIR=vps-vless

if [ -d $VPS_DIR ] ;then
    echo "$GREEN Папка $VPS_DIR уже есть, обновляем код... $NC"
    echo "$GREEN Если не получится - удалите папку $VPS_DIR и запустите скрипт снова $NC"

    cd $VPS_DIR
    git fetch
    git checkout $RELEASE
    git pull
    cd ..
else
    echo "Скачиваем код проекта..."
    git clone https://github.com/alexeyq2/vps.git $VPS_DIR
    cd $VPS_DIR
    git checkout $RELEASE
fi

cat << EOF
$GREEN
Далее: 
 * переходите в папку $VPS_DIR
 * настройте переменные по инструкциям в README.md
 * настройте ACME_SERVER на получение реального сертификата
 * если не работает - переключите на получение тестового и решайте
 * настраивайте свой VPN в панели 3X-UI
 * подключаете клиента по QR-коду или ссылке vless://...
