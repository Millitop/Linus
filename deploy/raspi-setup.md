# Installera på Raspberry Pi

Checklista för att sätta upp gårdskort-systemet på en fysisk Raspberry Pi.
Se `docs/pi-hardware-checklist.md` för en kortare drifts-checklista att
bocka av på plats.

## 1. Hårdvara

- Raspberry Pi 4 (4 GB) eller Pi 5
- USB-SSD rekommenderas som boot-disk istället för SD-kort (SQLite
  skriver ofta; SD-kort slits ut snabbare)
- USB-handskanner (streckkod/QR), t.ex. en billig 1D/2D USB HID-skanner
- (Valfritt) skärm/HDMI-monitor eller litet pekskärm för
  bekräftelse-vyn vid grinden
- (Valfritt, endast om ingen handskanner finns) USB-webbkamera eller Pi
  Camera Module

## 2. OS

1. Flasha Raspberry Pi OS Lite (64-bit) med Raspberry Pi Imager.
2. Sätt lokal (sv_SE.UTF-8) och tidszon Europe/Stockholm under
   avancerade inställningar.
3. `sudo apt update && sudo apt install -y python3-venv git`

## 3. Applikationen

```bash
git clone https://github.com/Millitop/Linus.git linus
cd linus
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # redigera SECRET_KEY, SITE_NAME osv.
python scripts/init_db.py
python scripts/create_staff_user.py admin --role admin
```

Testa lokalt: `flask --app wsgi run --host 0.0.0.0` och besök
`http://<pi-ip>:5000/`.

## 4. Automatisk start (systemd)

```bash
sudo cp deploy/systemd/gardskort-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gardskort-web.service
```

Lägg även till `gardskort-kiosk.service` om Pi:n har en egen skärm som
ska visa scan-vyn automatiskt (`/gate`), och/eller
`gardskort-scanner.service` **endast** om ingen USB-handskanner finns.

## 5. Lokal Wi-Fi-accesspunkt (valfritt men rekommenderat)

Ger telefoner ett sätt att nå webbappen (registrering/PIN-hämtning) utan
beroende av skolans nätverk:

```bash
sudo apt install -y hostapd dnsmasq
sudo cp deploy/hostapd/hostapd.conf /etc/hostapd/hostapd.conf
sudo cp deploy/hostapd/dnsmasq.conf /etc/dnsmasq.d/gardskort.conf
# redigera wpa_passphrase i hostapd.conf till något unikt
sudo systemctl enable --now hostapd dnsmasq
```

Om fritidsgården redan har ett fungerande Wi-Fi kan detta steg hoppas
över -- koppla då Pi:n till det nätverket istället (`raspi-config` →
System Options → Wireless LAN).

## 6. Nattlig gallring/auto-utcheckning

```bash
crontab -e
# lägg till:
0 3 * * * /home/pi/linus/.venv/bin/python /home/pi/linus/scripts/retention_cleanup.py
```
