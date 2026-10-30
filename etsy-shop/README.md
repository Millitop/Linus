# Linnea Paper Co. – Etsy-planners

Sex färdiga PDF-produkter att sälja på Etsy, med säljbilder, annonstexter och Pinterest-material.

| Produkt | Sidor | Format | Förslag pris |
|---|---|---|---|
| Undated Daily & Weekly Planner | 13 | US Letter + A4 | $6.50 |
| Budget Planner | 16 | US Letter + A4 | $6.50 |
| Habit & Wellness Tracker | 13 | US Letter + A4 | $5.50 |
| Meal Planner & Grocery List | 12 | US Letter + A4 | $4.90 |
| 2027 Digital Planner (klickbara flikar) | 104 | iPad / GoodNotes | $11.90 |
| Life Planner Bundle (de 4 första) | 54 | 2 ZIP: Letter + A4 | $14.90 |

## Mappar

- `etsy-upload/<produkt>/files/` – filerna köparen får (ladda upp under "Digital files").
- `etsy-upload/<produkt>/images/` – annonsbilder 2700×2025 (ladda upp i ordning, 01 först).
- `listings/listings.json` – titel, 13 taggar, beskrivning och pris för varje annons.
- `listings/SHOP-SETUP.md` – steg-för-steg: starta butiken, avgifter, moms, AI-regler, Pinterest.
- `listings/PINTEREST-PINS.md` – text och board för varje pin.
- `marketing/<produkt>/pin-*.png` – Pinterest-pins 1000×1500.
- `showcase/` – visningssidan (Pinterest-stil). Fyll i `ETSY_SHOP_URL` och `PINTEREST_URL` när butiken finns.

## Bygga om

```bash
python3 scripts/undated_planner.py      # och budget_planner.py, habit_tracker.py, meal_planner.py, digital_planner_2027.py
python3 scripts/marketing.py            # gör om alla säljbilder och pins
```

Gemensam design (färger, typsnitt, hjälpfunktioner) finns i `brand.py`. Byt `SHOP_NAME` där om butiken ska heta något annat.

Typsnitt: DM Serif Display och Lato, båda under SIL Open Font License (fri kommersiell användning och inbäddning i PDF). Licenstexter finns i `fonts/`.
