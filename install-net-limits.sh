#!/bin/bash -e

cat <<EOF | sudo tee /etc/sysctl.d/99-bbr.conf >/dev/null
# BBR TCP congestion control
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# TCP buffer sizes for fast data transfer
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# Incoming packet queue
net.core.netdev_max_backlog = 10000

# Maximum number of open files
fs.file-max = 100000
EOF

# Apply the settings
sudo sysctl --system >/dev/null

echo -e "${GREEN}Current TCP settings:${NC}"
sysctl net.ipv4.tcp_congestion_control net.core.default_qdisc \
    fs.file-max \
    net.core.rmem_max net.core.wmem_max \
    net.ipv4.tcp_rmem net.ipv4.tcp_wmem \
    net.core.netdev_max_backlog

echo "${GREEN}Настройки TCP - OK${NC}"
