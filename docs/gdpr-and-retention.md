# GDPR och gallring

Systemet hanterar personuppgifter om ungdomar, vilket kräver extra
försiktighet enligt GDPR.

## Dataminimering

- Inga personnummer, hemadresser, födelsedatum eller foton lagras.
- Ingen vårdnadshavarkontakt krävs — medlemmar registrerar sig själva.
  `EmergencyContact` finns som ett helt valfritt fält, inte en
  förutsättning för att gå med.
- Ingen bläddringsbar lista över registrerade medlemmar finns i
  adminvyn (se "Ingen medlemslista" nedan) — statistiken är aggregerad,
  inte namn-för-namn.

## Lokal lagring istället för moln

All data lagras i en lokal SQLite-fil på Raspberry Pi:n. Ingen
molntjänst används i v1 (`SYNC_ENABLED=false` som standard) — detta
minskar både attackyta och antalet parter som har tillgång till
medlemmarnas uppgifter.

## Ingen medlemslista

Adminvyns startsida (`/admin/`) visar bara aggregerad statistik (antal
aktiva just nu, besök över tid, populära tider, unika besökare) — det
finns medvetet ingen sida som listar alla registrerade medlemmar.
Personal som behöver hitta en specifik person (t.ex. vid borttappat
kort) använder `/admin/members/search`, som kräver en sökterm och
visar ingenting i vila.

## Åtkomstkontroll

- Adminvyn (`/admin/*`) kräver personalinloggning (`Flask-Login`).
- Den PIN-baserade kortåterhämtningen (`/card/retrieve`) och
  självregistreringen (`/join`) är hastighetsbegränsade
  (`Flask-Limiter`) för att försvåra missbruk/gissningsattacker.
- Lösenord hashas (`werkzeug.security`), aldrig i klartext.

## Gallring

- `LOG_RETENTION_DAYS` (standard 365 dagar) styr hur länge loggposter
  sparas. `scripts/retention_cleanup.py` körs nattligen (via cron/systemd
  timer) och raderar äldre poster. Sätt till `0` för att stänga av
  automatisk gallring om verksamheten har andra krav.
- `INACTIVE_MONTHS_BEFORE_ERASURE` (standard 12) styr när en medlems
  personuppgifter automatiskt raderas — se "Automatisk radering vid
  inaktivitet" nedan.

## Rätt till radering (manuell)

Adminvyn (`/admin/members/<id>`) har en "Radera personuppgifter"-knapp
per medlem som anropar `erase_member_personal_data()`
(`app/admin/services.py`). Den funktionen:
- inaktiverar och tar bort kortets token-koppling (kortet slutar fungera),
- tar bort eventuell kontaktperson helt,
- skriver över medlemmens namn/telefon/PIN-hash med platshållarvärden,
- behåller `LogEntry`-raderna (med `member_id` kvar) av kontinuitetsskäl
  för statistiken — historiken över besök en viss dag ändras inte
  retroaktivt, men går inte längre att koppla till ett namn i UI:t.

Detta är en medveten avvägning mellan "rätt att bli glömd" och
verksamhetens behov av pålitlig statistik. Om fullständig radering av
loggrader krävs (t.ex. efter `LOG_RETENTION_DAYS`), sköts det av
gallringsjobbet nedan.

## Automatisk radering vid inaktivitet

En fritidsgård för äldre ungdomar har inte en fast årskull som slutar
vid en viss ålder (till skillnad från ett fritidshem) — så en
åldersbaserad raderingsgräns passar inte här. Istället raderas en
medlems personuppgifter automatiskt när de varit inaktiva (ingen
in-/utcheckning) i `INACTIVE_MONTHS_BEFORE_ERASURE` månader (standard
12). `scripts/retention_cleanup.py` kör nattligen
`purge_inactive_members()` (`app/admin/services.py`), som använder
**samma** `erase_member_personal_data()`-funktion som den manuella
raderingsknappen — alltså identisk radering, bara automatiskt triggad
utifrån `Member.last_activity_at()` istället för ålder.

Sätt `INACTIVE_MONTHS_BEFORE_ERASURE=0` för att stänga av denna
automatik helt.
