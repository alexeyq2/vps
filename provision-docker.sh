#!/bin/bash -e

docker compose --version > /dev/null 2>&1

if [ $? == 0 ] ;then
  echo Docker уже установлен, отлично!
  exit 0
fi

read -p "Установить docker? [yes/no]: " answer
[ "$answer" == "${answer#[Yy]}" ] && exit 0


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

usermod -aG docker $USER

echo Docker установлен успешно.
echo Перезайдите в систему чтобы изменения вступили в силу.
