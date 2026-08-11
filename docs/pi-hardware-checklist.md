# Checklista för driftsättning på plats

Bocka av när en fysisk Raspberry Pi sätts upp vid en grind. Fullständiga
installationssteg finns i [`deploy/raspi-setup.md`](../deploy/raspi-setup.md).

- [ ] Pi:n startar och `gardskort-web.service` är `active (running)`
      (`systemctl status gardskort-web`)
- [ ] `http://<pi-ip>:5000/auth/login` svarar och personal kan logga in
- [ ] USB-handskannern är inkopplad, `/gate` visar kiosk-vyn
- [ ] Testskanning av ett testkorts QR-kod ger korrekt in/ut-bekräftelse
      på skärmen inom någon sekund
- [ ] (Om kamera-fallback används istället) `gardskort-scanner.service`
      är `active (running)` och känner igen en QR-kod i olika ljusförhållanden
- [ ] (Om lokal Wi-Fi-AP används) SSID `Fritidshem-Kort` syns och en
      testtelefon kan ansluta och nå `/card/retrieve`
- [ ] Registrera ett testbarn, verifiera att QR-koden går att ladda ner
      och skanna
- [ ] Verifiera att `/admin/attendance` uppdateras direkt efter en
      testskanning
- [ ] Verifiera att crontab/systemd-timer för
      `scripts/retention_cleanup.py` är installerad
      (`crontab -l` eller `systemctl list-timers`)
- [ ] `.env` har ett unikt `SECRET_KEY` (inte standardvärdet från
      `.env.example`) och `wpa_passphrase` i `hostapd.conf` är ändrad
- [ ] Ta bort testbarnet igen efter verifiering
      (Radera personuppgifter-knappen)
