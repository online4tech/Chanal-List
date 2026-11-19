#!/bin/sh
# Online4Tech Panel v8.1.1 — installer
# Run from the receiver via telnet / SSH (see README.txt for the one-liner).
# What it does:
#   1. Creates /usr/lib/enigma2/python/Plugins/Extensions/Online4Tech/
#   2. Downloads plugin.py (v8.1.1) from the Online4Tech GitHub repo into it
#   3. Restarts the Enigma2 GUI so the panel appears in the Plugins menu
# Safe to run again at any time (re-install / repair).

PLUGIN_DIR="/usr/lib/enigma2/python/Plugins/Extensions/Online4Tech"
PLUGIN_URL="https://raw.githubusercontent.com/online4tech/Chanal-List/main/plugin/plugin.py"

echo "Installing Online4Tech Panel v8.1.1 ..."

mkdir -p "$PLUGIN_DIR" || { echo "ERROR: cannot create $PLUGIN_DIR"; exit 1; }
cd "$PLUGIN_DIR" || exit 1

wget -q --no-check-certificate -O plugin.py "$PLUGIN_URL" || { echo "ERROR: download failed - check the internet connection"; exit 1; }
[ -s plugin.py ] || { echo "ERROR: downloaded plugin.py is empty"; exit 1; }

echo "Online4Tech Panel v8.1.1 installed successfully!"
echo "Restarting Enigma2 GUI ..."
sleep 2
killall -9 enigma2
