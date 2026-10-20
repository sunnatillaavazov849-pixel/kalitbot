#!/usr/bin/env bash
# Sunat.cc Plaginlar saytini toza Ubuntu (22.04 / 24.04) serverga o'rnatadi.
#
#   curl -fsSL https://raw.githubusercontent.com/sunnatillaavazov849-pixel/kalitbot/claude/practical-hawking-kbsu0h/deploy/ornatish.sh -o ornatish.sh
#   sudo bash ornatish.sh sunat.cc
#
# Natija: https://<domen> (HTTPS avtomatik), admin panel: https://<domen>/boshqaruv/
set -euo pipefail

DOMAIN="${1:-}"
REPO="https://github.com/sunnatillaavazov849-pixel/kalitbot.git"
BRANCH="${BRANCH:-claude/practical-hawking-kbsu0h}"
APP=/opt/sunat
DATA=/var/lib/sunat
USER_NAME=sunat

if [[ $EUID -ne 0 ]]; then echo "sudo bilan ishga tushiring: sudo bash ornatish.sh sunat.cc"; exit 1; fi
if [[ -z "$DOMAIN" ]]; then echo "Domenni yozing: sudo bash ornatish.sh sunat.cc"; exit 1; fi

echo "== 1/7 Kerakli dasturlar"
apt-get update -q
apt-get install -y -q python3 python3-venv python3-pip git sqlite3 curl debian-keyring debian-archive-keyring apt-transport-https gnupg
if ! command -v caddy >/dev/null; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -q && apt-get install -y -q caddy
fi

echo "== 2/7 Foydalanuvchi va kod"
id "$USER_NAME" >/dev/null 2>&1 || useradd --system --home "$APP" --shell /usr/sbin/nologin "$USER_NAME"
if [[ -d "$APP/.git" ]]; then git -C "$APP" pull -q; else git clone -q -b "$BRANCH" "$REPO" "$APP"; fi
mkdir -p "$DATA"
python3 -m venv "$APP/venv"
"$APP/venv/bin/pip" install -q --upgrade pip
"$APP/venv/bin/pip" install -q -r "$APP/requirements.txt"

echo "== 3/7 Sozlamalar (.env)"
if [[ ! -f "$APP/.env" ]]; then
  read -rp "Tez-Tez maxfiy kaliti (TezTezAdmin.bas dagi LIC_SECRET): " LIC
  read -rp "Karta raqami (masalan 8600 1234 5678 9012): " CARD
  read -rp "Karta egasi (masalan SUNAT A.): " OWNER
  KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
  cat > "$APP/.env" <<ENV
SECRET_KEY=$KEY
DEBUG=0
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
SITE_URL=https://$DOMAIN
DATA_DIR=$DATA
LIC_SECRET=$LIC
CARD_NUMBER=$CARD
CARD_OWNER=$OWNER
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
ADMIN_EMAILS=
ENV
  chmod 600 "$APP/.env"
fi
chown -R "$USER_NAME:$USER_NAME" "$APP" "$DATA"

echo "== 4/7 Baza va statik fayllar"
cd "$APP"
sudo -u "$USER_NAME" "$APP/venv/bin/python" manage.py migrate --noinput
sudo -u "$USER_NAME" "$APP/venv/bin/python" manage.py collectstatic --noinput -v 0
sudo -u "$USER_NAME" "$APP/venv/bin/python" manage.py shell -c "
from django.contrib.sites.models import Site
Site.objects.update_or_create(id=1, defaults={'domain': '$DOMAIN', 'name': 'Sunat.cc'})"

echo "== 5/7 Sayt xizmati (gunicorn)"
cp "$APP/deploy/sunat.service" /etc/systemd/system/sunat.service
systemctl daemon-reload
systemctl enable --now sunat
systemctl restart sunat

echo "== 6/7 HTTPS (Caddy)"
sed "s/__DOMAIN__/$DOMAIN/g" "$APP/deploy/Caddyfile" > /etc/caddy/Caddyfile
systemctl enable --now caddy
systemctl reload caddy

echo "== 7/7 Har kunlik zaxira nusxa (03:30)"
cp "$APP/deploy/backup.sh" /usr/local/bin/sunat-backup
chmod +x /usr/local/bin/sunat-backup
echo "30 3 * * * root /usr/local/bin/sunat-backup" > /etc/cron.d/sunat-backup

echo
echo "Admin akkaunt yaratamiz (login, email - bo'sh qoldirsa bo'ladi, parol):"
sudo -u "$USER_NAME" "$APP/venv/bin/python" manage.py createsuperuser
echo
echo "Tayyor: https://$DOMAIN   Admin panel: https://$DOMAIN/boshqaruv/"
echo "Sozlamalarni o'zgartirish: sudo nano $APP/.env  so'ng  sudo systemctl restart sunat"
