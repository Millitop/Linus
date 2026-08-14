#!/usr/bin/env bash
# Automates the manual setup steps in deploy/raspi-setup.md: venv,
# dependencies, first-run database init, and installing/starting the
# systemd service(s). Run from the repo root on the Raspberry Pi
# itself, as the user that should own the service (matches
# deploy/systemd/*.service's User=pi -- edit those unit files first if
# you use a different username).
#
# Usage:
#   ./deploy/install.sh                       # headless (web + USB scanner)
#   ./deploy/install.sh --with-kiosk          # + kiosk screen (needs Desktop OS, see raspi-setup.md)
#   ./deploy/install.sh --with-camera-scanner # + camera-based scanner fallback
set -euo pipefail

cd "$(dirname "$0")/.."

WITH_KIOSK=false
WITH_CAMERA_SCANNER=false
for arg in "$@"; do
  case "$arg" in
    --with-kiosk) WITH_KIOSK=true ;;
    --with-camera-scanner) WITH_CAMERA_SCANNER=true ;;
    *)
      echo "Okänd flagga: $arg" >&2
      exit 1
      ;;
  esac
done

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Skapade .env från .env.example -- kom ihåg att sätta ett eget SECRET_KEY innan drift!" >&2
fi

echo "Skapar Python-miljö och installerar beroenden..."
python3 -m venv .venv
.venv/bin/pip install --upgrade pip >/dev/null
.venv/bin/pip install -r requirements.txt

if [ "$WITH_CAMERA_SCANNER" = true ]; then
  echo "Installerar kamera-fallbackens extra beroenden..."
  .venv/bin/pip install opencv-python-headless pyzbar requests
fi

echo "Initierar databasen (skapar tabeller om de inte redan finns)..."
.venv/bin/python scripts/init_db.py

echo "Installerar systemd-tjänster..."
sudo cp deploy/systemd/gardskort-web.service /etc/systemd/system/

if [ "$WITH_KIOSK" = true ]; then
  if ! command -v chromium >/dev/null 2>&1 && ! command -v chromium-browser >/dev/null 2>&1; then
    echo "VARNING: hittar varken 'chromium' eller 'chromium-browser'." >&2
    echo "gardskort-kiosk.service kräver Raspberry Pi OS MED skrivbord, inte Lite." >&2
    echo "Se deploy/raspi-setup.md. Installerar tjänsten ändå, men den startar inte förrän det är löst." >&2
  fi
  sudo cp deploy/systemd/gardskort-kiosk.service /etc/systemd/system/
fi

if [ "$WITH_CAMERA_SCANNER" = true ]; then
  sudo cp deploy/systemd/gardskort-scanner.service /etc/systemd/system/
fi

sudo systemctl daemon-reload
sudo systemctl enable --now gardskort-web.service

if [ "$WITH_KIOSK" = true ]; then
  sudo systemctl enable --now gardskort-kiosk.service
fi
if [ "$WITH_CAMERA_SCANNER" = true ]; then
  sudo systemctl enable --now gardskort-scanner.service
fi

echo
echo "Klart. Skapa en personalanvändare med:"
echo "  .venv/bin/python scripts/create_staff_user.py <användarnamn> --role admin"
echo
echo "Glöm inte den nattliga gallringen (steg 7 i deploy/raspi-setup.md) och"
echo "den lokala Wi-Fi-accesspunkten (steg 5) om ni vill ha dem."
