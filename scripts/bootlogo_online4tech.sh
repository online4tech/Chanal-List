#!/bin/sh
echo "Downloading Online4Tech Full HD Bootlogo..."
wget -q --no-check-certificate -O /tmp/o4t_boot.jpg "https://raw.githubusercontent.com/online4tech/Chanal-List/main/assets/bootlogo_online4tech.jpg"

if [ ! -s /tmp/o4t_boot.jpg ]; then
    echo "Error: Failed to download bootlogo image from GitHub!"
    exit 1
fi

echo "Converting JPG to Enigma2 MVI format..."
if ! command -v ffmpeg >/dev/null 2>&1; then
    opkg update && opkg install ffmpeg
fi

# Method 1: Modern FFmpeg (MPEG2 Video I-frame for Enigma2 .mvi)
ffmpeg -y -i /tmp/o4t_boot.jpg -r 25 -f mpeg2video -q:v 2 -s 1920x1080 /tmp/bootlogo.mvi >/dev/null 2>&1

# Method 2: Fallback if 1920x1080 fails on older boxes (1280x720)
if [ ! -s /tmp/bootlogo.mvi ]; then
    ffmpeg -y -i /tmp/o4t_boot.jpg -r 25 -f mpeg2video -q:v 2 -s 1280x720 /tmp/bootlogo.mvi >/dev/null 2>&1
fi

if [ -s /tmp/bootlogo.mvi ]; then
    [ -f /usr/share/bootlogo.mvi ] && [ ! -f /usr/share/bootlogo.mvi.bak ] && cp /usr/share/bootlogo.mvi /usr/share/bootlogo.mvi.bak
    
    cp -f /tmp/bootlogo.mvi /usr/share/bootlogo.mvi 2>/dev/null
    cp -f /tmp/bootlogo.mvi /usr/share/backdrop.mvi 2>/dev/null
    [ -d /boot ] && mount -o remount,rw /boot 2>/dev/null && cp -f /tmp/bootlogo.mvi /boot/bootlogo.mvi 2>/dev/null
    
    wget -q --no-check-certificate -O /usr/lib/enigma2/python/Plugins/Extensions/Online4Tech/icon.png "https://raw.githubusercontent.com/online4tech/Chanal-List/main/assets/icon_online4tech.png"
    wget -q --no-check-certificate -O /usr/share/enigma2/picon_default.png "https://raw.githubusercontent.com/online4tech/Chanal-List/main/assets/picon_default.png"
    
    rm -f /tmp/o4t_boot.jpg /tmp/bootlogo.mvi
    echo "SUCCESS! Online4Tech Bootlogo, Icon & Default Picon installed!"
    echo "Press Blue Button (Reboot Box) to see your new Bootlogo."
else
    echo "FFmpeg Details:"
    ffmpeg -y -i /tmp/o4t_boot.jpg -r 25 -f mpeg2video -q:v 2 -s 1920x1080 /tmp/bootlogo.mvi
    rm -f /tmp/o4t_boot.jpg
fi
