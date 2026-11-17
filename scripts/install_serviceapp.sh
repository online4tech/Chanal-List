#!/bin/sh
echo "Installing ServiceApp + Exteplayer3 + GstPlayer..."
opkg update
opkg install ffmpeg exteplayer3 gstplayer enigma2-plugin-systemplugins-serviceapp
echo "ServiceApp & Players installed successfully!"
