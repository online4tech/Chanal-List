#!/bin/sh
echo "=== [ DISK & FLASH STORAGE ] ==="
df -h
echo ""
echo "=== [ RAM MEMORY STATUS ] ==="
free -m
echo ""
echo "=== [ NETWORK PING TEST ] ==="
ping -c 3 8.8.8.8
