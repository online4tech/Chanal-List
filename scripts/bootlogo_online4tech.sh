#!/bin/sh
echo "Downloading Online4Tech Full HD Assets..."
wget -q --no-check-certificate -O /tmp/o4t_boot.jpg "https://raw.githubusercontent.com/online4tech/Chanal-List/main/assets/bootlogo_online4tech.jpg"
wget -q --no-check-certificate -O /usr/lib/enigma2/python/Plugins/Extensions/Online4Tech/icon.png "https://raw.githubusercontent.com/online4tech/Chanal-List/main/assets/icon_online4tech.png"
wget -q --no-check-certificate -O /usr/share/enigma2/picon_default.png "https://raw.githubusercontent.com/online4tech/Chanal-List/main/assets/picon_default.png"

if [ ! -s /tmp/o4t_boot.jpg ]; then
    echo "Error: bootlogo_online4tech.jpg not found in assets folder on GitHub!"
    exit 1
fi

echo "Converting JPG to bootlogo.mvi..."
ffmpeg -y -i /tmp/o4t_boot.jpg -r 25 -f mpeg2video -q:v 2 -s 1920x1080 /tmp/bootlogo.mvi >/dev/null 2>&1

if [ ! -s /tmp/bootlogo.mvi ] && command -v gst-launch-1.0 >/dev/null 2>&1; then
    gst-launch-1.0 filesrc location=/tmp/o4t_boot.jpg ! jpegdec ! videoconvert ! videoscale ! video/x-raw,width=1920,height=1080 ! avenc_mpeg2video bitrate=20000000 ! filesink location=/tmp/bootlogo.mvi >/dev/null 2>&1
fi

if [ -s /tmp/bootlogo.mvi ]; then
    [ -f /usr/share/bootlogo.mvi ] && [ ! -f /usr/share/bootlogo.mvi.bak ] && cp /usr/share/bootlogo.mvi /usr/share/bootlogo.mvi.bak
    cp -f /tmp/bootlogo.mvi /usr/share/bootlogo.mvi 2>/dev/null
    cp -f /tmp/bootlogo.mvi /usr/share/backdrop.mvi 2>/dev/null
    [ -d /boot ] && mount -o remount,rw /boot 2>/dev/null && cp -f /tmp/bootlogo.mvi /boot/bootlogo.mvi 2>/dev/null
    rm -f /tmp/o4t_boot.jpg /tmp/bootlogo.mvi
    echo "SUCCESS! Online4Tech Bootlogo, Icon & Picon installed!"
else
    echo "Note: Icon & Picon updated! For Bootlogo, please upload pre-converted bootlogo.mvi to assets/"
    rm -f /tmp/o4t_boot.jpg
fi
