# Installera på Raspberry Pi

Checklista för att sätta upp gårdskort-systemet på en fysisk Raspberry Pi.
Se `docs/pi-hardware-checklist.md` för en kortare drifts-checklista att
bocka av på plats.

## Välj profil först

Det finns två sätt att driftsätta, beroende på om Pi:n ska ha en egen
skärm vid dörren eller inte:

- **Headless (rekommenderas som standard)** — Raspberry Pi OS **Lite**,
  ingen skärm kopplad till Pi:n. Bekräftelse sker på besökarens *egen*
  telefon: antingen genom att gårdskortets QR-kod skannas av en
  USB-handskanner (ingen skärm behövs för det), eller genom att
  besökaren själv taggar en NFC-tagg och ser bekräftelsen i sin egen
  webbläsare (se `deploy/nfc-tag-setup.md`). Enklast att sätta upp och
  underhålla.
- **Med kiosk-skärm** — Raspberry Pi OS **med skrivbord** (inte Lite),
  eftersom `gardskort-kiosk.service` kräver ett grafiskt skal och en
  webbläsare. Ger en dedikerad skärm vid dörren som visar en stor
  bekräftelse när någon skannar/taggar, utöver det som redan visas på
  besökarens egen telefon.

Steg 1–4 nedan är gemensamma; steg 2 och `gardskort-kiosk.service` i
steg 4 skiljer sig åt beroende på vald profil.

## 1. Hårdvara

- Raspberry Pi 4 (4 GB) eller Pi 5
- USB-SSD rekommenderas som boot-disk istället för SD-kort (SQLite
  skriver ofta; SD-kort slits ut snabbare)
- USB-handskanner (streckkod/QR), t.ex. en billig 1D/2D USB HID-skanner
  — **eller** NFC-taggar vid dörren (se `deploy/nfc-tag-setup.md`),
  eller båda
- (Endast kiosk-profilen) skärm/HDMI-monitor eller litet pekskärm
- (Valfritt, endast om ingen handskanner finns) USB-webbkamera eller Pi
  Camera Module

## 2. OS

1. Flasha **Raspberry Pi OS Lite (64-bit)** för headless-profilen, eller
   **Raspberry Pi OS med skrivbord (64-bit)** om ni vill ha en
   kiosk-skärm vid dörren, med Raspberry Pi Imager.
2. Sätt lokal (sv_SE.UTF-8) och tidszon Europe/Stockholm under
   avancerade inställningar. Aktivera SSH så resten av installationen
   kan göras på distans.
3. `sudo apt update && sudo apt install -y python3-venv git`

## 3. Applikationen

Snabbaste vägen — `deploy/install.sh` gör steg 3–4 automatiskt:

```bash
git clone https://github.com/Millitop/Linus.git linus
cd linus
./deploy/install.sh                     # headless (standard)
./deploy/install.sh --with-kiosk        # + kiosk-skärm (kräver Desktop-OS)
./deploy/install.sh --with-camera-scanner  # + kamera-fallback istället för USB-skanner
```

Skriptet skapar `.env` från `.env.example` (kom ihåg att sätta ett
eget `SECRET_KEY`!), skapar venv, installerar beroenden, initierar
databasen och installerar/startar systemd-tjänsterna.

Skapa en personalanvändare efteråt:

```bash
.venv/bin/python scripts/create_staff_user.py admin --role admin
```

Testa lokalt innan systemd-tjänsten startas om ni vill felsöka:
`flask --app wsgi run --host 0.0.0.0` och besök `http://<pi-ip>:5000/`.

### Manuell installation (om ni inte vill använda install.sh)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # redigera SECRET_KEY, SITE_NAME osv.
python scripts/init_db.py
python scripts/create_staff_user.py admin --role admin
```

## 4. Automatisk start (systemd)

Redan gjort av `install.sh` ovan. Manuellt:

```bash
sudo cp deploy/systemd/gardskort-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gardskort-web.service
```

`gardskort-kiosk.service` **kräver Raspberry Pi OS med skrivbord**
(chromium + ett grafiskt skal) — installera bara den om ni valde
kiosk-profilen i steg 2. Kontrollera webbläsarens sökväg innan ni
startar tjänsten, den skiljer sig mellan OS-versioner:

```bash
which chromium || which chromium-browser
# redigera ExecStart i gardskort-kiosk.service om sökvägen inte stämmer
```

`gardskort-scanner.service` (kamera-fallback) behövs **endast** om
ingen USB-handskanner finns.

## 5. Lokal Wi-Fi-accesspunkt (valfritt men rekommenderat)

Ger telefoner ett sätt att nå webbappen (registrering/PIN-hämtning,
och NFC-taggning vid dörren) utan beroende av annat nätverk:

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

## 6. NFC-tagg vid dörren (valfritt)

Se `deploy/nfc-tag-setup.md` för hur man skriver och monterar en
NFC-tagg som pekar mot `/gate/tap`.

## 7. Nattlig gallring/auto-utcheckning

`install.sh` sätter inte upp detta automatiskt än — lägg till manuellt:

```bash
crontab -e
# lägg till:
0 3 * * * /home/pi/linus/.venv/bin/python /home/pi/linus/scripts/retention_cleanup.py
```
