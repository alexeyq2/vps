#!/bin/bash

# Скрипт установки Docker и Docker Compose V2 для Ubuntu 24.04
# Требует запуска с правами root

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка на запуск от root
if [[ $EUID != 0 ]]; then
    print_error "Этот скрипт должен быть запущен с правами root"
    echo "Используйте: sudo $0"
    exit 1
fi

print_info "Начинаем установку Docker и Docker Compose V2"

# Проверка установленного Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
    print_info "Docker уже установлен: версия $DOCKER_VERSION"
else
    print_info "Установка Docker..."
    
    # Добавление GPG ключа Docker
    print_info "Добавление GPG ключа Docker..."
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    # Добавление репозитория Docker
    print_info "Добавление репозитория Docker..."
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
        https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Обновление пакетов после добавления репозитория
    apt-get update -qq

    # Установка Docker CE
    print_info "Установка Docker CE..."
    apt-get install -y -qq \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin

    # Настройка Docker для запуска без sudo
    print_info "Настройка Docker для запуска без sudo..."
    if getent group docker > /dev/null; then
        print_info "Группа docker уже существует"
    else
        groupadd docker
    fi
    
    # Добавление текущего пользователя в группу docker
    CURRENT_USER=${SUDO_USER:-$(whoami)}
    usermod -aG docker "$CURRENT_USER"
    
    print_info "Пользователь $CURRENT_USER добавлен в группу docker"
    print_warn "Необходимо перелогиниться или выполнить 'newgrp docker' для применения изменений"
fi

# Проверка установленного Docker Compose V2
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_VERSION=$(docker compose version | awk '{print $4}')
    print_info "Docker Compose V2 уже установлен: версия $DOCKER_COMPOSE_VERSION"
else
    print_info "Установка Docker Compose Plugin (V2)..."
    
    # Установка docker-compose-plugin
    apt-get install -y -qq docker-compose-plugin
    
    # Создание символической ссылки для совместимости (опционально)
    if [[ ! -f /usr/local/bin/docker-compose ]] && [[ -f /usr/libexec/docker/cli-plugins/docker-compose ]]; then
        ln -sf /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
        print_info "Создана символическая ссылка /usr/local/bin/docker-compose"
    fi
fi

# Проверка установки
print_info "\nПроверка установки..."

# Проверка Docker
if command -v docker &> /dev/null; then
    docker --version
    print_info "✓ Docker установлен успешно"
else
    print_error "✗ Docker не установлен"
    exit 1
fi

# Проверка Docker Compose
if docker compose version &> /dev/null; then
    docker compose version
    print_info "✓ Docker Compose V2 установлен успешно"
elif command -v docker-compose &> /dev/null; then
    docker-compose version
    print_info "✓ Docker Compose установлен успешно"
else
    print_error "✗ Docker Compose не установлен"
    exit 1
fi

# Проверка Docker Buildx
if docker buildx version &> /dev/null; then
    print_info "✓ Docker Buildx установлен"
else
    print_warn "⚠ Docker Buildx не найден"
fi

# Проверка состояния сервиса Docker
print_info "\nПроверка состояния сервиса Docker..."
if systemctl is-active --quiet docker; then
    print_info "✓ Docker сервис запущен"
else
    print_info "Запуск Docker сервиса..."
    systemctl start docker
    systemctl enable docker
    print_info "✓ Docker сервис запущен и добавлен в автозагрузку"
fi

# Информация для пользователя
print_info "\n================================================"
print_info "Установка завершена успешно!"
print_info "================================================"
echo ""
print_info "Для использования Docker без sudo необходимо:"
print_info "1. Выйти из системы и зайти снова"
print_info "2. ИЛИ выполнить команду: newgrp docker"
echo ""
print_info "Проверьте установку командами:"
print_info "  docker --version"
print_info "  docker compose version"
print_info "  docker run hello-world"
echo ""
print_info "Основные команды Docker Compose V2:"
print_info "  docker compose up -d      # Запуск сервисов"
print_info "  docker compose down       # Остановка сервисов"
print_info "  docker compose ps         # Просмотр статуса"
print_info "  docker compose logs       # Просмотр логов"
echo ""

print_info "Готово!"