# Arkitektur

```
┌───────────────────────────┐
│   Barnets telefon          │
│   (webbläsare, ingen app)  │
│   visar QR-kod              │
└──────────────┬─────────────┘
               │ (skärm visas för läsare)
               ▼
┌───────────────────────────────────────────┐
│  Raspberry Pi vid grinden                  │
│                                             │
│  USB-handskanner  ──►  /gate/scan (Flask)  │
│  (fallback: kamera)                        │
│                                             │
│  Flask-app (gunicorn)                      │
│   ├─ auth   (personalinloggning)           │
│   ├─ admin  (registrering, logg, närvaro)  │
│   ├─ card   (QR-visning, PIN-hämtning,     │
│   │          grind-scan, kiosk-vy)         │
│   └─ sync   (tom stub, avstängd i v1)      │
│                                             │
│  SQLite (lokal fil, instance/gardskort.db) │
│                                             │
│  hostapd + dnsmasq (egen Wi-Fi, valfritt)  │
└───────────────────────────┬────────────────┘
                             │ (samma lokala nätverk)
                             ▼
                  Personalens/barnets telefon
                  ansluter till Pi:ns Wi-Fi för
                  registrering/PIN-hämtning
```

## Komponenter

- **Flask-app** (`app/`) — server-renderade sidor (Jinja2), körs som en
  enda process med `gunicorn` på Pi:n. Ingen separat frontend-build.
- **SQLite** — en enda fil, ingen extern databasserver. Tillräckligt för
  ett fritidshems skala (tiotals barn, en grind).
- **Grind-scanning** — i v1 är en USB HID-handskanner primärt
  gränssnitt: den beter sig som ett tangentbord och "skriver in" kortets
  token i ett fokuserat textfält på kiosk-sidan (`/gate`), som sedan
  skickas till `/gate/scan` via JavaScript (`fetch`). En valfri
  kamerabaserad fallback (`scanner/camera_scan.py`) finns för den som
  saknar handskanner.
- **Wi-Fi-accesspunkt** — Pi:n kan köra sin egen `hostapd`/`dnsmasq`-AP så
  att telefoner når webbappen (registrering, PIN-hämtning) utan beroende
  av skolans nätverk. Detta är valfritt; Pi:n kan istället anslutas till
  ett befintligt nätverk.
- **`app/sync/base.py`** — ett medvetet tomt gränssnitt för en framtida
  molnsynk. Byggs inte i v1; se `SYNC_ENABLED` i konfigurationen.

## Varför ingen mobilapp?

En native-app hade krävt separat utveckling och distribution för iOS och
Android, plus att riktig NFC-korttappning (Host Card Emulation) bara
fungerar fritt på Android. En mobilanpassad webbsida med QR-kod fungerar
identiskt på alla telefoner, kräver ingen installation, och är enklare
att underhålla för ett litet fritidshems-team.
