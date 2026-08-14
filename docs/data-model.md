# Datamodell

Se `app/models.py` för den körbara källan till sanning. Sammanfattning:

## Child
Ett registrerat barn.
| Fält | Typ | Anmärkning |
|---|---|---|
| id | int | |
| first_name, last_name | str | |
| group_class | str, valfri | fritidshemsgrupp/klass |
| birth_year | int, valfri | **endast födelseår**, inget personnummer |
| current_status | "in" \| "out" | materialiserad för snabb närvarolista |
| status_updated_at | datetime | |
| retrieval_pin_hash | str | hashad PIN för att hämta QR-koden igen |
| active | bool | false efter GDPR-radering |
| created_at, deleted_at | datetime | |

## GuardianContact
Vårdnadshavarkontakt kopplad till ett barn (`child_id`): namn, telefon,
e-post, relation, `primary_contact`.

## Card
Ett gårdskort: `child_id`, unik `token` (slumpad, `secrets.token_urlsafe`),
`created_at`, `revoked_at`, `active`. Endast ett aktivt kort per barn i
taget — ett nytt kort inaktiverar automatiskt det gamla.

## StaffUser
Personalkonto för adminvyn: `username`, `password_hash`, `role`
("staff"/"admin"), `active`, `last_login_at`.

## LogEntry
Den samlade audit-loggen. Se `docs/event-taxonomy.md` för alla
`event_type`-värden. Fält: `event_type`, `child_id` (valfri),
`staff_user_id` (valfri), `timestamp`, `source`
("gate-scanner"/"web-app"/"admin"/"system"), `context_json`, `note`.

## Medveten dataminimering

Inga personnummer, hemadresser eller foton lagras någonstans i schemat.
Se `docs/gdpr-and-retention.md`.

## Radering

`app/admin/services.py` innehåller den delade raderingslogiken:
- `erase_child_personal_data()` — skriver över ett barns personuppgifter
  och inaktiverar kortet. Används av både adminvyns "Radera
  personuppgifter"-knapp och den automatiska nattliga rensningen.
- `purge_children_who_turned_adult()` — hittar alla barn där
  `Child.is_adult(ADULT_AGE_YEARS)` är sant (beräknat från `birth_year`)
  och raderar deras uppgifter. Körs av `scripts/retention_cleanup.py`.
