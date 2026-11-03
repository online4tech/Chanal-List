#!/bin/sh
# Online4Tech - install the published Enigma2 channel files
set -eu

BASE_URL="https://raw.githubusercontent.com/online4tech/Enigma2-Chanal-List-BYRomeh/main"
ARCHIVE_URL="$BASE_URL/channels_backup_openATV_Enigma2-Chanal-List-BYRomeh.tar.gz"
TARGET="/etc/enigma2"
WORK="/tmp/online4tech-channels-install"
ARCHIVE="$WORK/channels.tar.gz"
EXTRACT="$WORK/extracted"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$TARGET/online4tech-backup-$STAMP"

command -v wget >/dev/null 2>&1 || { echo "ERROR: wget is required"; exit 1; }
command -v tar >/dev/null 2>&1 || { echo "ERROR: tar is required"; exit 1; }
[ -d "$TARGET" ] || { echo "ERROR: $TARGET was not found"; exit 1; }

rm -rf "$WORK"
mkdir -p "$EXTRACT"
echo "Downloading Online4Tech channel package..."
wget -q -O "$ARCHIVE" "$ARCHIVE_URL" || { echo "ERROR: download failed"; exit 1; }
tar -xzf "$ARCHIVE" -C "$EXTRACT" || { echo "ERROR: archive extraction failed"; exit 1; }

# Match only channel bouquets and satellite/cable/terrestrial data files.
find "$EXTRACT" -type f \( \
  -name "bouquets.tv" -o -name "bouquets.radio" -o \
  -name "userbouquet.*.tv" -o -name "userbouquet.*.radio" -o \
  -name "satellites.xml" -o -name "cables.xml" -o \
  -name "terrestrial.xml" -o -name "atsc.xml" \
\) -print > "$WORK/file-list.txt"

[ -s "$WORK/file-list.txt" ] || { echo "ERROR: no channel files found in the package"; exit 1; }

mkdir -p "$BACKUP"
while IFS= read -r file; do
  name="${file##*/}"
  [ -f "$TARGET/$name" ] && cp "$TARGET/$name" "$BACKUP/$name"
done < "$WORK/file-list.txt"

COUNT=0
while IFS= read -r file; do
  name="${file##*/}"
  cp "$file" "$TARGET/$name"
  COUNT=$((COUNT + 1))
done < "$WORK/file-list.txt"

sync
rm -rf "$WORK"
echo "Done: installed $COUNT channel files."
echo "Previous matching files backup: $BACKUP"
echo "Restart the Enigma2 GUI from the receiver menu to reload the channel list."
