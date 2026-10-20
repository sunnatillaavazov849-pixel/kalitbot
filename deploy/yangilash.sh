#!/usr/bin/env bash
# Saytni GitHub'dagi oxirgi versiyaga yangilaydi:  sudo bash /opt/sunat/deploy/yangilash.sh
set -euo pipefail
APP=/opt/sunat
cd "$APP"
/usr/local/bin/sunat-backup || true
sudo -u sunat git pull -q
sudo -u sunat "$APP/venv/bin/pip" install -q -r requirements.txt
sudo -u sunat "$APP/venv/bin/python" manage.py migrate --noinput
sudo -u sunat "$APP/venv/bin/python" manage.py collectstatic --noinput -v 0
systemctl restart sunat
echo "Yangilandi."
