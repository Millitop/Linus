# Händelsetyper i loggen

Alla skrivs till samma `LogEntry`-tabell, skiljs åt av `event_type`.
Detta är också källdatan för statistik-dashboarden (`app/admin/stats.py`).

| event_type | Utlöses av | Refererar |
|---|---|---|
| `registration` | Ny medlem registrerar sig (`/join`) eller personal hjälper någon registrera sig, första kortet utfärdas | member_id, staff_user_id (null vid självregistrering) |
| `card_reissued` | Nytt kort utfärdas (t.ex. borttappat kort) | member_id, staff_user_id |
| `card_revoked` | Ett kort inaktiveras manuellt | member_id, staff_user_id |
| `card_retrieval` | Medlem hämtar sin QR-kod via PIN | member_id |
| `check_in` / `check_out` | Grind-skanning, togglas automatiskt utifrån aktuell status | member_id |
| `manual_check_in` / `manual_check_out` | Personal rättar status i adminvyn, eller nattlig auto-utcheckning | member_id, staff_user_id (null vid auto) |
| `scan_rejected` | Okänd/inaktiv token skannad, eller inaktiv medlem | staff_user_id=null |
| `member_updated` | Personal redigerar en medlems uppgifter i adminvyn | member_id, staff_user_id |
| `staff_login` / `staff_logout` | Personalens inloggning/utloggning | staff_user_id |
| `member_data_deleted` | GDPR-radering genomförd, manuellt eller automatiskt vid inaktivitet | member_id (historisk referens kvarstår) |

## Vad "logga in" betyder i det här systemet

Kravet "man ska kunna logga in på fritidsgården, för att föra statistik
och ha koll på hur många som är aktiva" täcks av: `registration`
(medlemmen skapar sitt konto/kort), `check_in`/`check_out` (den
faktiska in-/utloggningen vid dörren — detta är statistikens kärna),
samt `card_retrieval` för den som behöver hämta sitt kort igen. Att
skilja dem åt som separata `event_type` istället för en enda generisk
"login" gör loggen användbar för både beläggningsstatistik och
felsökning (t.ex. varför någons status verkar fel).

## Hantering av missade skanningar

- Nattlig auto-återställning (`scripts/retention_cleanup.py`,
  `auto_checkout_all()`) sätter alla kvarvarande "incheckade" till
  "utcheckade" vid en konfigurerbar tid.
- Personal kan rätta status manuellt i adminvyn (`manual_check_in/out`).
- Kiosk-skärmen visar tydlig bekräftelse (namn + in/ut ✓) i ~3 sekunder
  så personen kan se att skanningen gick åt rätt håll.
- `SCAN_DEBOUNCE_SECONDS` ignorerar en oavsiktlig dubbel-skanning av
  samma kort inom ett kort tidsfönster.
