#!/usr/bin/env bash
# Har kunlik zaxira: baza + fayllar (cheklar, plaginlar, rasmlar). 14 kunlik nusxa saqlanadi.
set -euo pipefail
DATA=/var/lib/sunat
OUT=/var/backups/sunat
STAMP=$(date +%Y-%m-%d)
mkdir -p "$OUT"
sqlite3 "$DATA/sayt.db" ".backup '$OUT/sayt-$STAMP.db'"
tar -czf "$OUT/fayllar-$STAMP.tar.gz" -C "$DATA" media private
cp /opt/sunat/.env "$OUT/env-$STAMP"
chmod 600 "$OUT/env-$STAMP"
find "$OUT" -type f -mtime +14 -delete
