# Händelsetyper i loggen

Alla skrivs till samma `LogEntry`-tabell, skiljs åt av `event_type`:

| event_type | Utlöses av | Refererar |
|---|---|---|
| `registration` | Personal registrerar ett nytt barn, första kortet utfärdas | child_id, staff_user_id |
| `card_reissued` | Nytt kort utfärdas (t.ex. borttappat kort) | child_id, staff_user_id |
| `card_revoked` | Ett kort inaktiveras manuellt | child_id, staff_user_id |
| `card_retrieval` | Barn/vårdnadshavare hämtar sin QR-kod via PIN | child_id |
| `check_in` / `check_out` | Grind-skanning, togglas automatiskt utifrån aktuell status | child_id |
| `manual_check_in` / `manual_check_out` | Personal rättar status i adminvyn, eller nattlig auto-utcheckning | child_id, staff_user_id (null vid auto) |
| `scan_rejected` | Okänd/inaktiv token skannad, eller tomt/inaktivt barn | staff_user_id=null |
| `staff_login` / `staff_logout` | Personalens inloggning/utloggning | staff_user_id |
| `child_data_deleted` | GDPR-radering genomförd | child_id (historisk referens kvarstår) |

## Varför "inloggning" i kravet motsvarar flera olika händelser

Ursprungskravet "inloggning och registrering ska loggas" täcks av:
`registration` (nytt kort utfärdas), `card_retrieval` (barnet "loggar in"
för att se sitt kort), samt `check_in`/`check_out` (den faktiska
in-/utloggningen på skolgården). Att skilja dem åt som separata
`event_type` istället för en enda generisk "login" gör loggen
användbar för både säkerhet (vilka barn är på plats nu) och
administration (vem registrerade vad och när).

## Hantering av missade skanningar

- Nattlig auto-återställning (`scripts/retention_cleanup.py`,
  `auto_checkout_all()`) sätter alla kvarvarande "incheckade" till
  "utcheckade" vid en konfigurerbar tid.
- Personal kan rätta status manuellt i adminvyn (`manual_check_in/out`).
- Kiosk-skärmen visar tydlig bekräftelse (namn + in/ut ✓) i ~3 sekunder
  så barnet kan se att skanningen gick åt rätt håll.
- `SCAN_DEBOUNCE_SECONDS` ignorerar en oavsiktlig dubbel-skanning av
  samma kort inom ett kort tidsfönster.
