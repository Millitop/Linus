# Checklista för driftsättning på plats

Bocka av när en fysisk Raspberry Pi sätts upp vid en dörr. Fullständiga
installationssteg finns i [`deploy/raspi-setup.md`](../deploy/raspi-setup.md)
(välj headless- eller kiosk-profil där först).

## Grundläggande

- [ ] Pi:n startar och `gardskort-web.service` är `active (running)`
      (`systemctl status gardskort-web`)
- [ ] `http://<pi-ip>:5000/auth/login` svarar och personal kan logga in
- [ ] `.env` har ett unikt `SECRET_KEY` (inte standardvärdet från
      `.env.example`)

## Incheckning — QR

- [ ] USB-handskannern är inkopplad och `/gate` är öppen i en
      webbläsare med fokus i textfältet (antingen manuellt på valfri
      skärm, eller automatiskt via `gardskort-kiosk.service` om
      kiosk-profilen valdes — den kräver Desktop-OS, se
      `deploy/raspi-setup.md`)
- [ ] Självregistrera en testmedlem via `/join`, verifiera att QR-koden
      går att ladda ner och skanna
- [ ] Testskanning av testmedlemmens QR-kod ger korrekt in/ut-bekräftelse
      inom någon sekund
- [ ] (Om kamera-fallback används istället) `gardskort-scanner.service`
      är `active (running)` och känner igen en QR-kod i olika ljusförhållanden

## Incheckning — NFC-tagg (om det används)

Se [`deploy/nfc-tag-setup.md`](../deploy/nfc-tag-setup.md) för hur taggen skrivs.

- [ ] Taggen är monterad vid dörren och pekar mot `http://<pi-host>/gate/tap`
- [ ] En testtelefon utan tidigare cookie skickas till `/card/retrieve`
      vid första taggningen och kan identifiera sig med namn + PIN
- [ ] Efter identifiering: samma telefon kan taggas igen direkt och
      checkas in/ut utan att behöva ange PIN på nytt
      ("kom ihåg mig"-cookien fungerar)

## Statistik och administration

- [ ] Verifiera att `/admin/` (statistik) och `/admin/attendance`
      uppdateras direkt efter en testskanning/taggning
- [ ] Verifiera att en testmedlem går att hitta via
      `/admin/members/search`
- [ ] Testa periodväljaren på `/admin/` (7/30/90 dagar) och att
      `Exportera CSV` laddar ner en giltig fil

## Nätverk

- [ ] (Om lokal Wi-Fi-AP används) SSID `Fritidsgard-Kort` syns och en
      testtelefon kan ansluta och nå `/join`, `/card/retrieve` och
      `/gate/tap`
- [ ] `wpa_passphrase` i `hostapd.conf` är ändrad från standardvärdet

## Gallring och städning

- [ ] Verifiera att crontab/systemd-timer för
      `scripts/retention_cleanup.py` är installerad
      (`crontab -l` eller `systemctl list-timers`)
- [ ] Ta bort testmedlemmen igen efter verifiering
      (Radera personuppgifter-knappen)
