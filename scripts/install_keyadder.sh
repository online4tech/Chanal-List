#!/bin/sh
echo "Installing KeyAdder Plugin..."
wget -q "--no-check-certificate" https://raw.githubusercontent.com/fairbird/KeyAdder/main/installer.sh -O - | /bin/sh
