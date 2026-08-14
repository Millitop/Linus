# Datamodell

Se `app/models.py` för den körbara källan till sanning. Sammanfattning:

## Member
En registrerad medlem (självregistrerad eller personal-hjälpt).
| Fält | Typ | Anmärkning |
|---|---|---|
| id | int | |
| first_name, last_name | str | |
| phone | str, valfri | |
| current_status | "in" \| "out" | materialiserad för snabb närvarolista |
| status_updated_at | datetime | |
| retrieval_pin_hash | str | hashad PIN för att hämta QR-koden igen |
| active | bool | false efter GDPR-radering |
| created_at, deleted_at | datetime | |

## EmergencyContact
Helt valfri kontaktperson kopplad till en medlem (`member_id`): namn,
telefon, e-post, relation. Ingen vårdnadshavare krävs för registrering
— medlemmar är äldre ungdomar som registrerar sig själva.

## Card
Ett gårdskort: `member_id`, unik `token` (slumpad, `secrets.token_urlsafe`),
`created_at`, `revoked_at`, `active`. Endast ett aktivt kort per medlem i
taget — ett nytt kort inaktiverar automatiskt det gamla.

## StaffUser
Personalkonto för adminvyn: `username`, `password_hash`, `role`
("staff"/"admin"), `active`, `last_login_at`.

## LogEntry
Den samlade audit-loggen — även källan för statistik-dashboarden
(`app/admin/stats.py`). Se `docs/event-taxonomy.md` för alla
`event_type`-värden. Fält: `event_type`, `member_id` (valfri),
`staff_user_id` (valfri), `timestamp`, `source`
("gate-scanner"/"web-app"/"admin"/"system"), `context_json`, `note`.

## Medveten dataminimering

Inga personnummer, hemadresser eller foton lagras någonstans i schemat.
Se `docs/gdpr-and-retention.md`.

## Radering

`app/admin/services.py` innehåller den delade raderingslogiken:
- `erase_member_personal_data()` — skriver över en medlems
  personuppgifter och inaktiverar kortet. Används av både adminvyns
  "Radera personuppgifter"-knapp och den automatiska nattliga rensningen.
- `purge_inactive_members()` — hittar alla medlemmar vars senaste
  in-/utcheckning (`Member.last_activity_at()`) är äldre än
  `INACTIVE_MONTHS_BEFORE_ERASURE` månader och raderar deras uppgifter.
  Körs av `scripts/retention_cleanup.py`.

## Statistik, inte en bläddringsbar lista

Det finns medvetet ingen adminsida som listar alla registrerade
medlemmar (se `docs/gdpr-and-retention.md`). `app/admin/stats.py`
innehåller bara aggregerande frågor (antal aktiva, besök per dag,
populära tider, unika besökare) — inga enskilda namn. Personal som
behöver hitta en specifik person (t.ex. borttappat kort) söker på namn
via `/admin/members/search`, som visar högst 50 träffar och ingenting
i vila.
