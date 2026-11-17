#!/bin/sh
echo "Installing & Updating EPGImport..."
opkg update && opkg install enigma2-plugin-extensions-epgimport
echo "EPGImport ready!"
