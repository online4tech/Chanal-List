#!/bin/sh
echo "Updating SoftCam.Key from Online Server..."
mkdir -p /etc/tuxbox/config /usr/keys
wget -q --no-check-certificate -O /usr/keys/SoftCam.Key "https://raw.githubusercontent.com/MOHAMED19OS/SoftCam_Emu/main/SoftCam.Key"
cp -f /usr/keys/SoftCam.Key /etc/tuxbox/config/SoftCam.Key 2>/dev/null
echo "SoftCam.Key updated successfully in /usr/keys and /etc/tuxbox/config!"
