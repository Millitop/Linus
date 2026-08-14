# Arkitektur

```
┌───────────────────────────┐
│   Medlemmens telefon       │
│   (webbläsare, ingen app)  │
│   visar QR-kod              │
└──────────────┬─────────────┘
               │ (skärm visas för läsare)
               ▼
┌───────────────────────────────────────────┐
│  Raspberry Pi vid dörren                   │
│                                             │
│  USB-handskanner  ──►  /gate/scan (Flask)  │
│  (fallback: kamera)                        │
│                                             │
│  Flask-app (gunicorn)                      │
│   ├─ auth   (personalinloggning)           │
│   ├─ admin  (statistik, sök, logg)         │
│   ├─ card   (självregistrering /join,      │
│   │          QR-visning, PIN-hämtning,     │
│   │          grind-scan, kiosk-vy)         │
│   └─ sync   (tom stub, avstängd i v1)      │
│                                             │
│  SQLite (lokal fil, instance/gardskort.db) │
│                                             │
│  hostapd + dnsmasq (egen Wi-Fi, valfritt)  │
└───────────────────────────┬────────────────┘
                             │ (samma lokala nätverk)
                             ▼
                  Medlemmens telefon ansluter
                  till Pi:ns Wi-Fi för att
                  registrera sig/hämta sitt kort
```

## Komponenter

- **Flask-app** (`app/`) — server-renderade sidor (Jinja2), körs som en
  enda process med `gunicorn` på Pi:n. Ingen separat frontend-build.
- **SQLite** — en enda fil, ingen extern databasserver. Tillräckligt för
  en fritidsgårds skala (hundratals medlemmar, en dörr).
- **Grind-scanning** — en USB HID-handskanner är primärt gränssnitt: den
  beter sig som ett tangentbord och "skriver in" kortets token i ett
  fokuserat textfält på kiosk-sidan (`/gate`), som sedan skickas till
  `/gate/scan` via JavaScript (`fetch`). En valfri kamerabaserad
  fallback (`scanner/camera_scan.py`) finns för den som saknar
  handskanner.
- **NFC-tagg vid dörren** — alternativ till att visa QR: en passiv
  NFC-tagg pekar telefonens webbläsare mot `/gate/tap` (ingen app
  krävs, fungerar på iPhone och Android). Eftersom taggen är delad och
  inte vet vem som taggar identifieras personen via en cookie som sätts
  när de registrerar sig eller hämtar sitt kort. Se
  `deploy/nfc-tag-setup.md`.
- **Statistik istället för lista** — `app/admin/stats.py` innehåller
  bara aggregerande frågor mot loggen (`LogEntry`). Det finns ingen
  route som returnerar alla medlemmar; personal söker enskilda personer
  via `/admin/members/search`. Se `docs/gdpr-and-retention.md`.
- **Wi-Fi-accesspunkt** — Pi:n kan köra sin egen `hostapd`/`dnsmasq`-AP så
  att telefoner når webbappen (registrering, PIN-hämtning) utan beroende
  av annat nätverk. Detta är valfritt; Pi:n kan istället anslutas till
  ett befintligt nätverk.
- **`app/sync/base.py`** — ett medvetet tomt gränssnitt för en framtida
  molnsynk. Byggs inte i v1; se `SYNC_ENABLED` i konfigurationen.

## Varför ingen mobilapp?

En native-app hade krävt separat utveckling och distribution för iOS och
Android, plus att riktig NFC-korttappning (Host Card Emulation) bara
fungerar fritt på Android. En mobilanpassad webbsida med QR-kod fungerar
identiskt på alla telefoner, kräver ingen installation, och är enklare
att underhålla för ett litet team.
