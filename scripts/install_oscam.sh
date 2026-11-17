#!/bin/sh
echo "Installing latest OSCam-icam Emulator..."
wget -q "--no-check-certificate" https://raw.githubusercontent.com/biko-73/OsCam_emu/main/installer.sh -O - | /bin/sh
