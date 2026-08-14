# GDPR och gallring

Systemet hanterar personuppgifter om barn (minderåriga), vilket kräver
extra försiktighet enligt GDPR och svensk dataskyddspraxis för skolor.

## Dataminimering

- Inga personnummer, hemadresser eller foton lagras.
- `birth_year` (endast år) är valfritt och räcker för eventuell
  åldersrelaterad logik — fullständigt födelsedatum lagras inte.
- Vårdnadshavarkontakt begränsas till namn, telefon, e-post och relation.

## Lokal lagring istället för moln

All data lagras i en lokal SQLite-fil på Raspberry Pi:n. Ingen
molntjänst används i v1 (`SYNC_ENABLED=false` som standard) — detta
minskar både attackyta och antalet parter som har tillgång till
barnens uppgifter.

## Åtkomstkontroll

- Adminvyn (`/admin/*`) kräver personalinloggning (`Flask-Login`).
- Barnets PIN-baserade kortåterhämtning (`/card/retrieve`) är
  hastighetsbegränsad (`Flask-Limiter`) för att försvåra gissningsattacker.
- Lösenord hashas (`werkzeug.security`), aldrig i klartext.

## Gallring

- `LOG_RETENTION_DAYS` (standard 365 dagar) styr hur länge loggposter
  sparas. `scripts/retention_cleanup.py` körs nattligen (via cron/systemd
  timer) och raderar äldre poster. Sätt till `0` för att stänga av
  automatisk gallring om verksamheten har andra krav.
- `ADULT_AGE_YEARS` (standard 18) styr när ett barns personuppgifter
  automatiskt raderas — se "Automatisk radering vid 18 års ålder" nedan.

## Rätt till radering (manuell)

Adminvyn (`/admin/children/<id>`) har en "Radera personuppgifter"-knapp
per barn som anropar `erase_child_personal_data()`
(`app/admin/services.py`). Den funktionen:
- inaktiverar och tar bort kortets token-koppling (kortet slutar fungera),
- tar bort vårdnadshavarkontakter helt,
- skriver över barnets namn/grupp/födelseår/PIN-hash med platshållarvärden,
- behåller `LogEntry`-raderna (med `child_id` kvar) av säkerhetsskäl —
  historiken över vilka som varit på skolgården en viss dag ändras inte
  retroaktivt, men går inte längre att koppla till ett namn i UI:t.

Detta är en medveten avvägning mellan "rätt att bli glömd" och
verksamhetens behov av en pålitlig närvarohistorik. Om fullständig
radering av loggrader krävs (t.ex. efter `LOG_RETENTION_DAYS`), sköts det
av gallringsjobbet nedan.

## Automatisk radering vid 18 års ålder

Fritidshemmet vänder sig till barn, inte vuxna — så personuppgifter för
någon som fyllt `ADULT_AGE_YEARS` (standard 18) år ska inte ligga kvar.
`scripts/retention_cleanup.py` kör därför nattligen
`purge_children_who_turned_adult()` (`app/admin/services.py`), som
använder **samma** `erase_child_personal_data()`-funktion som den
manuella raderingsknappen — alltså identisk radering, bara automatiskt
triggad.

Eftersom endast `birth_year` lagras (inget fullständigt födelsedatum,
se dataminimering ovan) kan systemet inte veta exakt vilken dag någon
fyller 18. Åldern räknas konservativt: från och med den 1 januari det år
personen fyller `ADULT_AGE_YEARS` räknas hen som vuxen, vilket kan vara
några månader innan den faktiska födelsedagen. Det är en medveten,
integritetsvänlig avvägning — hellre radera något för tidigt än att
personuppgifter om en snart vuxen person ligger kvar för länge. Sätt
`ADULT_AGE_YEARS=0` för att stänga av denna automatik helt.
