# NFC-tagg vid dörren

Ett alternativ till att visa QR-koden för en läsare: medlemmen plippar
sin egen telefon mot en passiv NFC-tagg vid dörren. Fungerar utan app
på både iPhone och Android — telefonen läser taggens URL och öppnar den
i webbläsaren automatiskt, samma sak som att skanna en QR-kod fast med
en beröring.

## Hur det fungerar

- Taggen bär bara en URL: `http://<pi-host eller ip>/gate/tap`.
  Den vet inget om vem som taggar — det är samma fysiska tagg för alla.
- Identiteten kommer istället från en cookie i telefonens webbläsare,
  satt automatiskt första gången personen registrerar sig (`/join`)
  eller hämtar sitt kort (`/card/retrieve`). Se `docs/architecture.md`
  och `app/card/routes.py::gate_tap` för detaljer.
- Saknar telefonen cookien (ny telefon, rensad webbläsare) skickas
  personen först till `/card/retrieve` för att identifiera sig en gång
  med namn + PIN — därefter kommer den telefonen ihåg dem.
- **Kräver att telefonen är ansluten till samma nätverk som Pi:n**
  (dess egna Wi-Fi-AP eller gårdens nät) i taggningsögonblicket, av
  samma skäl som gäller registrering och PIN-hämtning idag.

## Hårdvara

- Tomma skrivbara NFC-taggar, t.ex. NTAG213-klistermärken eller -kort
  (några kronor styck, beställs från valfri elektronikbutik).
- En NFC-aktiverad Android-telefon (för att skriva en enstaka tagg) —
  eller en USB NFC-läsare/skrivare (t.ex. ACR122U) om många taggar ska
  skrivas på en gång.

## Skriva taggen

### Med en Android-telefon (enklast för en tagg)

1. Installera en gratisapp för NFC-skrivning, t.ex. "NFC Tools" från
   Google Play.
2. I appen: Skriv → Lägg till post → URL/URI.
3. Ange `http://<pi-host eller ip>/gate/tap` (byt ut mot Pi:ns faktiska
   adress eller mDNS-namn, t.ex. `http://gardskort.local/gate/tap` om
   du satt upp det).
4. Håll telefonen mot den tomma taggen och bekräfta skrivningen.
5. Testa: lägg telefonen mot taggen igen (utanför appen) — webbläsaren
   ska öppna sidan automatiskt.

### Med en USB NFC-skrivare (för flera taggar/en fast installation)

Använd valfri NDEF-skrivarmjukvara som följer med läsaren (t.ex.
NXP TagWriter eller motsvarande) och skriv samma URL som ovan som en
NDEF URI-post.

## Montering

Sätt taggen vid dörren i normal räckviddshöjd (10 cm för de flesta
telefoner). En liten skylt ("Plippa här") hjälper. Taggen är passiv —
den behöver ingen ström eller kabeldragning.

## Felsökning

- **Inget händer vid tapp** — kontrollera att telefonens NFC är
  påslaget (Android: Inställningar → Anslutna enheter → NFC. iPhone:
  NFC-läsning är alltid på från iOS 14 och kräver ingen inställning).
- **Öppnar fel sida / gammal adress** — skriv om taggen, gamla
  skrivningar skrivs över helt.
- **"Identifiera dig"-sidan visas varje gång** — telefonens webbläsare
  tappar cookien om den körs i privat/inkognitoläge, eller om
  webbläsarens cookies rensas manuellt. Be personen hämta sitt kort en
  gång till via `/card/retrieve` i sin vanliga webbläsare.
