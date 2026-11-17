#!/bin/sh
echo "Restarting OSCam / NCam Emulator..."
killall -9 oscam ncam 2>/dev/null
sleep 2
/etc/init.d/softcam restart 2>/dev/null || /usr/bin/oscam -b 2>/dev/null
echo "Emulator restarted successfully!"