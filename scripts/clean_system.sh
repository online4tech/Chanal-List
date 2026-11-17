#!/bin/sh
echo "Cleaning temporary files and freeing RAM..."
rm -rf /tmp/*.ipk /tmp/*.tar.gz /tmp/*.zip
sync && echo 3 > /proc/sys/vm/drop_caches
free -m
echo "System cleanup completed!"