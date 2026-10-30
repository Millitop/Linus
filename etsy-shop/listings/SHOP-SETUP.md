# Linnea Paper Co. – kom igång på Etsy och Pinterest

En kort, praktisk guide. Färdiga titlar, taggar, beskrivningar och pin-texter finns i `listings.json` i samma mapp. Siffror om avgifter och regler stämde i oktober 2026 enligt källorna längst ner. **Kontrollera alltid aktuella värden hos Etsy innan du räknar på dem.**

---

## 1. Skapa Etsy-butiken

1. Gå till **etsy.com/sell** och logga in eller skapa ett konto.
2. **Shop preferences:** språk *English*, land *Sverige*, valuta **USD**. De flesta köpare finns i USA och Storbritannien, och Etsy visar automatiskt priset i köparens valuta.
3. **Butiksnamn:** `LinneaPaperCo` (namnet får inte innehålla mellanslag, men visningsnamnet kan vara "Linnea Paper Co.").
4. Lägg upp minst en listning (se avsnitt 3). Etsy kräver det innan butiken kan öppnas.
5. **Betalning:** välj Etsy Payments och ange ditt svenska bankkonto (IBAN) och personuppgifter. Etsy kan behöva verifiera din identitet.
6. **Fakturering:** lägg in ett kort för Etsys avgifter.
7. **Säkerhet:** aktivera tvåstegsverifiering, som Etsy kräver.
8. **Butiksprofil:** logga, banner, en kort "About"-text (vem du är och den lugna, minimalistiska stilen) samt **Shop policies**. Skriv in att digitala filer inte går att returnera, men att du hjälper till om något är fel med filen.

## 2. Butikssektioner (Shop sections)

Shop Manager → Listings → *Sections*. Förslag:

- **Printable Planners** – undated planner
- **Budget & Finance**
- **Habit & Wellness**
- **Meal Planning**
- **Digital Planners (iPad)** – 2027 digital planner
- **Bundles & Savings** – life planner bundle

## 3. Ladda upp en digital listning

1. Shop Manager → **Listings → Add a listing**.
2. **Foton/video:** upp till 10 bilder och 1 video. Lägg den bästa mockupen först. Visa gärna "What's included", en bild med storlekar (Letter + A4) och några exempelsidor. För paketet: en bild som visar att det är "värt 23,40 USD".
3. **Titel, beskrivning och taggar:** kopiera från `listings.json`. Du har 13 taggar à max 20 tecken. Taggarna i filen är redan anpassade till det.
4. **Item details:**
   - *Who made it?* → **I did**
   - *What is it?* → **A finished product**
   - *When was it made?* → **Made to order** eller **2020–2026**
   - **Type: Digital** (viktigt – då skickas inget fysiskt)
5. **Kategori + attribut:** till exempel *Paper & Party Supplies → Paper → Calendars & Planners* (välj den kategori Etsy föreslår och som passar bäst). Fyll i **alla attribut** (format, färg, tillfälle osv.). Attributen fungerar som sökfilter och tar inte upp någon av dina 13 taggar.
6. **Filer:** max **5 filer per listning, max 20 MB per fil**.
   - Enskilda planers: 2 PDF:er (Letter + A4).
   - Paketet har 8 PDF:er, vilket är för många. Lägg dem i **4 ZIP-filer** (en per planer med Letter och A4) eller i **2 ZIP-filer** (alla Letter och alla A4). Varje ZIP får vara högst 20 MB.
   - Den digitala 2027-planern: 1 PDF. Om den blir större än 20 MB, komprimera bilderna i PDF:en.
7. **Pris och antal:** se avsnitt 4. Sätt *Quantity* till exempelvis 999 (det förnyas automatiskt).
8. **Material** (frivilligt fält): finns i `materials` i JSON-filen.
9. **Kreativitet/AI-uppgift** (se avsnitt 6).
10. Klicka **Publish**. Varje publicering kostar 0,20 USD.

## 4. Prissättning

Förslag på lanseringspriser:

| Produkt | Pris |
|---|---|
| Undated Daily & Weekly Planner | 6,50 USD |
| Budget Planner | 6,50 USD |
| Habit & Wellness Tracker | 5,50 USD |
| Meal Planner & Grocery List | 4,90 USD |
| 2027 Digital Planner (iPad) | 11,90 USD |
| Life Planner Bundle (1–4) | 14,90 USD (värt 23,40, ca 36 % rabatt) |

**Tips:**
- Utskrivbara planers säljer ofta för 2–12 USD. Hyperlänkade GoodNotes-planers säljer för 10–25 USD.
- Lansera på en rimlig nivå. Höj priset (till exempel den digitala planern till 14–16 USD) när du har fått omdömen.
- Använd Etsys egna **Sales and discounts** (till exempel 20–30 % under Black Friday och nyår) i stället för att blåsa upp grundpriset.
- Paketet höjer ordervärdet. Länka till det i beskrivningen av varje enskild produkt.
- Rätt tid är **nu**. Nyårsplanering pågår från november till januari, och daterade 2027-planers säljer bäst före januari.

## 5. Etsys avgifter (ungefärliga – kontrollera aktuella värden)

- **Listningsavgift:** 0,20 USD per listning. Den förnyas var 4:e månad och efter varje försäljning.
- **Transaktionsavgift:** 6,5 % av försäljningspriset.
- **Betalningshantering:** för USA ca 3 % + 0,25 USD. Satsen beror på **säljarens bankland**, så kolla den svenska satsen i Etsys avgiftstabell (ofta ca 4 % + en fast avgift).
- **Offsite Ads:** 12–15 % på försäljningar som kommer via Etsys annonser utanför Etsy. Det är frivilligt för butiker som säljer under 10 000 USD per år.
- **Moms på avgifterna:** Etsy lägger svensk moms (25 %) på sina avgifter. Om du registrerar ett VAT-nummer hos Etsy slipper du det, men då redovisar du momsen själv.
- **Valutaväxling:** om butiksvalutan (USD) skiljer sig från bankvalutan (SEK) tillkommer en avgift på cirka 2,5 %.
- **Tumregel:** räkna med att ungefär 10–15 % av priset försvinner i avgifter (mer vid Offsite Ads). På en försäljning för 6,50 USD får du kvar ungefär 5,40–5,70 USD.

## 6. Etsys Creativity Standards och AI – vad som gäller oss

- Etsy delar in alla varor i **Made by**, **Designed by**, **Handpicked by** och **Sourced by**. Digitala nedladdningar som bygger på **säljarens egen design** räknas som **"Designed by a seller"**.
- **Allt ska vara säljarens egen design.** Sedan juni 2025 räcker det enligt rapporter inte längre att sälja färdiga mallar (t.ex. Canva-mallar) rakt av. Våra planers är egna layouter, och så ska det vara.
- **AI:** att skapa med hjälp av AI utifrån egna instruktioner (prompts) är tillåtet, men det **måste redovisas**. När du skapar listningen svarar du på frågan om hur varan är gjord. Ange att den är designad av dig och, om det stämmer, att **generativ AI eller digitala verktyg** har använts. Skriv gärna också en rad om det i beskrivningen. Beskrivningarna innehåller redan raden *"Designed by Linnea Paper Co. … created by the shop using digital design tools."* Om AI-verktyg har använts för layout, text eller bilder, lägg till till exempel: *"Created with the help of AI tools based on my own designs and direction."*
- Mockup-bilderna ska visa den **riktiga produkten**, inget som inte ingår i köpet.
- Kopiera aldrig andras design, varumärken eller typsnitt som kräver kommersiell licens. Kontrollera att typsnitten i `fonts/` får användas kommersiellt i PDF:er.
- Etsy har skärpt kontrollen av digitala varor och tar ibland bort listningar automatiskt. Spara skisser och arbetsfiler så att du kan visa din egen designprocess vid en eventuell överklagan.

## 7. Skatt och moms (Sverige)

- **Moms på digitala varor till EU-konsumenter:** Etsy tar normalt ut och betalar in momsen för digitala nedladdningar till köpare i EU (och i bland annat Storbritannien). Du ska då inte lägga på moms själv. Kontrollera ändå vad som gäller för din situation.
- **Inkomsten är skattepliktig.** Om det blir en regelbunden verksamhet med vinstsyfte behöver du **registrera enskild firma** (verksamt.se och Skatteverket) och eventuellt **F-skatt och momsregistrering**. Momsregistrering krävs normalt inte om omsättningen understiger 120 000 kr per år (kontrollera aktuell gräns).
- Spara Etsys månadsfakturor och utbetalningsrapporter för bokföring och deklaration.
- **Rådgör med Skatteverket** (eller en redovisningskonsult) innan du drar igång på riktigt. Regler för moms på digitala tjänster, OSS och omvänd skattskyldighet för Etsys avgifter kan vara krångliga.

## 8. Pinterest – gratis trafik till butiken

**Skapa konto**
1. Gå till **business.pinterest.com** och skapa ett **gratis företagskonto** (Business), eller konvertera ett privat konto under Inställningar → Kontohantering.
2. Profilnamn: *Linnea Paper Co. | Minimalist Planners & Printables*. Lägg till logga och en kort beskrivning med nyckelord.

**Göra anspråk på (claim) butiken eller webbplatsen**
- Inställningar → **Claimed accounts** → **Etsy** → *Claim* och logga in på Etsy. Då kopplas dina pins till butiken och du får statistik. Pinterests alternativ har ändrats över tid, så om Etsy-valet saknas: gör anspråk på en egen domän (Settings → Claim → Website, via HTML-tagg eller DNS-post) om du skaffar en egen webbplats senare.
- Aktivera även **Rich Pins** om möjligheten finns.

**Tavlor (boards)** – en tavla per produktkategori. Använd namnen i `listings.json` → `pinterest.board`:
- Minimalist Printable Planners
- Budget Planner & Money Printables
- Habit Tracker & Wellness Printables
- Meal Planning & Kitchen Printables
- Digital Planners for iPad & GoodNotes
- Life Binder & Home Organization Printables
- och en bred tavla: *New Year Planning & Goal Setting*

Ge varje tavla en beskrivning med naturliga nyckelord.

**Pinningsschema**
- **3–5 pins per dag** i början, jämnt fördelade över dagen (använd Pinterests inbyggda schemaläggning). Öka gradvis till 5–10 pins per dag.
- Satsa på **"fresh pins"**: nya bilder för samma produkt (ny mockup, ny bakgrund, ny rubrik) i stället för att pinna samma bild om och om igen. Gör 5–10 olika pin-bilder per produkt och sprid ut dem över flera veckor.
- Format: **stående 2:3 (1000 × 1500 px)**, med tydlig textrubrik på bilden (t.ex. "Printable Budget Planner – Letter & A4").
- Använd `pin_title`, `pin_description` och hashtaggarna från `listings.json`. Variera texten lite mellan pins.
- Pinterest är en sökmotor med lång framförhållning. Pinna nyårs- och budgetinnehåll **nu**, inte i januari.

**Länka pins till Etsy**
- Klistra in **direktlänken till listningen** (t.ex. `https://www.etsy.com/listing/123456789/...`) i fältet *Destination link* på varje pin. Länka inte till butiksstartsidan.
- Ta bort onödiga spårningsparametrar från länken, men behåll listnings-ID:t.
- Du kan också skapa pins direkt från Etsy-listningen via **Share → Pinterest** och sedan ersätta bilden med din egen pin-design.
- Följ upp i Pinterest Analytics och Etsy Stats (trafikkälla "Pinterest") varje månad, och gör fler pins i samma stil som de som fungerar.

---

## Källor

- Etsy – How to Manage Your Digital Listings (5 filer, 20 MB): https://help.etsy.com/hc/en-us/articles/115015628347-How-to-Add-Files-to-a-Digital-Listing
- Etsy – How to Use Tags to Get Found in Search (13 taggar, 20 tecken): https://help.etsy.com/hc/articles/360000336307
- Etsy – How VAT Works on Digital Items: https://help.etsy.com/hc/articles/115015587567
- Etsy – Creativity Standards / House Rules: https://www.etsy.com/legal/creativity och https://www.etsy.com/new-guidelines
- TechCrunch – Etsy's new seller policy on generative AI (2024): https://techcrunch.com/2024/07/09/etsy-new-seller-policy-2024-generative-ai
- Modern Retail – Etsy's labeling policy: https://www.modernretail.co/technology/sellers-are-cautiously-optimistic-about-etsys-new-labeling-policy/
- Listadum – Etsy's Creativity Standards 2026: https://www.listadum.com/blog/etsy-creativity-standards
- Rankhero – Etsy policy changes (juni 2025): https://blog.rankhero.com/2025/06/20/etsy-policy-changes/
- Craftybase – The complete guide to Etsy fees: https://craftybase.com/blog/the-complete-guide-to-etsy-fees
- Checkoutpage – Etsy fees 2026: https://checkoutpage.com/blog/etsy-fees
- Craftybase – Etsy charging VAT on seller fees: https://craftybase.com/blog/etsy-charging-vat-for-seller-fees-from-midyear
- Outfy – Etsy character limits 2026: https://www.outfy.com/blog/etsy-character-limit/
- Listingview – Etsy SEO guide 2026: https://listingview.io/blogs/etsy-seo-guide
- Sellertoolshq – How to sell planners on Etsy: https://sellertoolshq.com/guides/how-to-sell-planners-on-etsy/
- Promptless Press – Selling digital planners on Etsy: https://www.promptlesspress.com/blog-sell-digital-planners-etsy
- Growing Your Craft – Pinterest marketing for Etsy sellers (2026): https://www.growingyourcraft.com/blog/pinterest-marketing-strategies-for-etsy-sellers
- Craftybase – Pinterest for Etsy sellers: https://craftybase.com/blog/pinterest-for-etsy-seller-handmade
- Printify – Pinterest–Etsy traffic playbook: https://printify.com/knowledge-hub/pinterest-etsy-traffic-playbook/
- Skatteverket: https://www.skatteverket.se och Verksamt (starta företag): https://www.verksamt.se
