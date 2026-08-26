#!/usr/bin/env bash
set -e

NEW_PORT=51022
CONFIG_FILE="/etc/ssh/sshd_config"

# 1. Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run this script with sudo or as root." >&2
    exit 1
fi

echo "==> Reassigning SSHD port to ${NEW_PORT} via ${CONFIG_FILE}..."

# 2. Update or insert the Port directive in sshd_config
if grep -qE "^#?Port [0-9]+" "$CONFIG_FILE"; then
    # Replace existing Port line (whether commented out or active)
    sed -i -E "s/^#?Port [0-9]+/Port ${NEW_PORT}/" "$CONFIG_FILE"
else
    # Append Port directive if it doesn't exist
    echo "Port ${NEW_PORT}" >> "$CONFIG_FILE"
fi

# 3. Handle UFW Firewall if active
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    echo "==> Firewall (UFW) detected. Allowing traffic on port ${NEW_PORT}..."
    ufw allow ${NEW_PORT}/tcp comment 'SSH Custom Port'
    ufw reload
fi

# 4. Trigger the Ubuntu 24.04 systemd generator and restart the socket
systemctl daemon-reload
systemctl restart ssh.socket

# 5. Verify the new port is listening
echo "==> Verifying listening status..."
if ss -tlnp | grep -q ":${NEW_PORT} "; then
    echo "SSH is now listening on port ${NEW_PORT} using the native config!"
    echo "Do NOT close this window. Test connection in a new terminal tab first."
else
    echo "ERROR: Port verification failed. Check 'systemctl status ssh.socket'"
fi
