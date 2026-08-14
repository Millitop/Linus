# Gårdskort

Ett digitalt "gårdskort"-system för fritidshem: barn/ungdomar visar en
QR-kod på sin egen telefon för att checka in/ut vid skolgården, istället
för ett fysiskt NFC-kort. Alla registreringar och in-/utcheckningar
loggas lokalt på en Raspberry Pi som står vid grinden.

Varför QR och inte riktig NFC-tappning? iPhone tillåter inte
tredjepartsappar att emulera NFC-kort (Host Card Emulation finns bara
fritt på Android), så en QR-kod som visas på skärmen fungerar lika bra
på alla telefoner utan att någon behöver installera en app.

## Funktioner

- **Registrering** — personal registrerar ett barn och en
  vårdnadshavarkontakt, systemet genererar ett unikt gårdskort (QR-kod).
- **Elevadmin** — se, sök och redigera alla elevers uppgifter
  (namn, grupp, födelseår, vårdnadshavare), samt lägga till/ta bort.
- **Hämta kort igen** — barnet/vårdnadshavaren kan hämta sin QR-kod igen
  med namn + PIN-kod, t.ex. via Pi:ns egna Wi-Fi.
- **Grind-skanning** — en USB-handskanner (eller valfritt en kamera) vid
  grinden läser QR-koden och togglar in/ut-status, med tydlig bekräftelse
  på skärmen.
- **Live-närvaro & logg** — personal ser vilka barn som är incheckade just
  nu, samt en fullständig, exporterbar audit-logg över alla händelser.
- **GDPR-medvetet** — minimal datainsamling, lokal lagring (ingen
  molnberoende), rättighet att radera ett barns personuppgifter,
  **automatisk radering när ett barn fyller 18 år**, samt konfigurerbar
  gallring av loggar.

## Snabbstart (utveckling)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python scripts/init_db.py
python scripts/create_staff_user.py admin --role admin
flask --app wsgi run --debug
```

Besök `http://localhost:5000/`. Personalinloggning på `/auth/login`,
grindens scan-vy på `/gate`, hämta-kort-sidan på `/card/retrieve`.

Simulera en grindskanning utan hårdvara:

```bash
curl -X POST http://localhost:5000/gate/scan -d "token=<kortets token>"
```

## Tester

```bash
pytest
```

## Driftsättning på Raspberry Pi

Se [`deploy/raspi-setup.md`](deploy/raspi-setup.md) för fullständiga
installationssteg (hårdvara, autostart via systemd, lokal Wi-Fi-
accesspunkt) och [`docs/pi-hardware-checklist.md`](docs/pi-hardware-checklist.md)
för en checklista att bocka av på plats.

## Mer dokumentation

- [`docs/architecture.md`](docs/architecture.md) — översikt av systemet
- [`docs/data-model.md`](docs/data-model.md) — datamodell
- [`docs/event-taxonomy.md`](docs/event-taxonomy.md) — alla loggade händelsetyper
- [`docs/gdpr-and-retention.md`](docs/gdpr-and-retention.md) — dataskydd och gallring

## Avgränsning (v1)

Byggt: allt ovan. Inte byggt (medvetet bortvalt för v1): SMS/e-post till
vårdnadshavare, riktig NFC-tappning, synk mellan flera grindar/Pi:er
(endast ett tomt gränssnitt `app/sync/base.py` finns förberett),
etikettskrivare, flerspråkigt UI.
