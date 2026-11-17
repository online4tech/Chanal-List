#!/bin/sh
echo "Downloading Online4Tech Full HD Bootlogo..."
wget -q --no-check-certificate -O /tmp/o4t_boot.jpg "https://raw.githubusercontent.com/online4tech/Chanal-List/main/assets/bootlogo_online4tech.jpg"

if [ ! -s /tmp/o4t_boot.jpg ]; then
    echo "Error: Failed to download bootlogo image from GitHub!"
    exit 1
fi

echo "Converting JPG to Enigma2 MVI format..."
if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg -y -i /tmp/o4t_boot.jpg -r 25 -b:v 20000k -s 1920x1080 /tmp/bootlogo.mvi >/dev/null 2>&1
else
    echo "Error: ffmpeg not found on this image! Installing ffmpeg..."
    opkg update && opkg install ffmpeg
    ffmpeg -y -i /tmp/o4t_boot.jpg -r 25 -b:v 20000k -s 1920x1080 /tmp/bootlogo.mvi >/dev/null 2>&1
fi

if [ -s /tmp/bootlogo.mvi ]; then
    # Backup original bootlogo once
    [ -f /usr/share/bootlogo.mvi ] && [ ! -f /usr/share/bootlogo.mvi.bak ] && cp /usr/share/bootlogo.mvi /usr/share/bootlogo.mvi.bak
    
    # Copy new Online4Tech bootlogo to standard Enigma2 paths
    cp -f /tmp/bootlogo.mvi /usr/share/bootlogo.mvi 2>/dev/null
    cp -f /tmp/bootlogo.mvi /usr/share/backdrop.mvi 2>/dev/null
    [ -d /boot ] && mount -o remount,rw /boot 2>/dev/null && cp -f /tmp/bootlogo.mvi /boot/bootlogo.mvi 2>/dev/null
    
    # Also update plugin icon & default picon
    wget -q --no-check-certificate -O /usr/lib/enigma2/python/Plugins/Extensions/Online4Tech/icon.png "https://raw.githubusercontent.com/online4tech/Chanal-List/main/assets/icon_online4tech.png"
    wget -q --no-check-certificate -O /usr/share/enigma2/picon_default.png "https://raw.githubusercontent.com/online4tech/Chanal-List/main/assets/picon_default.png"
    
    rm -f /tmp/o4t_boot.jpg /tmp/bootlogo.mvi
    echo "Online4Tech Bootlogo, Plugin Icon & Default Picon installed successfully!"
    echo "Please Reboot Receiver (Blue Button) to see the new Bootlogo."
else
    echo "Error: Failed to convert image to bootlogo.mvi"
fi
