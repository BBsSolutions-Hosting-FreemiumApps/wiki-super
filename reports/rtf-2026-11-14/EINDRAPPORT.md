# Wiki-super — RTF 2026 controleverslag

Werkbranch: `update-rtf-2026-11-14`, gebaseerd op `main` commit `3d781dc54ac8ffe74456eb07a93abd1452feecb9`.

Dezelfde aangeleverde RTF als bij wiki-normaal is verwerkt. SHA-256: `4cf082bd418517b301240735b4ede690b09f2372e13ca5c1e4aac59b48935392`. De converter werkt voortaan rechtstreeks vanuit deze RTF en de bestaande wiki-super-data; wiki-normaal hoeft niet tegelijk aanwezig te zijn.

## Resultaat

| Controle | Uitkomst |
| --- | ---: |
| Bijbelboeken | 66 |
| Bestaande naamkeys behouden | 1,803 |
| Bestaande versadressen behouden | 25,296 |
| Huidige versrecords | 28,721 |
| Toegevoegde afzonderlijke versrecords | 3,425 |
| Bijgewerkte bestaande versteksten | 1,616 |
| Losse studienotities ongewijzigd behouden | 1,494 |
| RTF-bronregels vergeleken, tekst én stijl | 217,428 |
| Bestaande feiten met citaten behouden | 978 |
| Citaten bij nauwkeuriger vers geplaatst | 14 |
| Historische citaten zichtbaar gemarkeerd | 9 |
| Regressietests | 25 geslaagd |
| Browsercontroles | 14 geslaagd |
| Bestanden identiek bij herhaalde conversie | 341 |

De 3.425 toevoegingen zijn vooral verzen die voorheen in grotere tekstgedeelten zaten of waarvan de koppen niet afzonderlijk werden herkend. Dit aantal betekent niet dat er 3.425 nieuwe Bijbelverzen zijn geschreven. De bestaande 25.296 IDs en hun referenties vormen nog steeds de vaste basis; nieuwe IDs worden alleen toegevoegd. Een expliciete leesvolgorde plaatst alles op de juiste plek.

Twee lege dubbele records, IDs 10428 en 14501, blijven als bestaande URL bestaan en zijn herkenbaar als oude lege records. Eén verplaatst Nehemia-vers is via exact dezelfde tekst teruggevonden. De exacte wijzigingen staan in [changes.json](changes.json).

## Wat de bezoeker kan bekijken

- **Vergelijk vorige versie** bij een vers: oude en huidige leestekst naast elkaar.
- **Oorspronkelijke RTF**: volledige bronregels met kleuren, lettertype, grootte en overige karakteropmaak, inclusief regels die de bestaande leesregels uitsluiten.
- **Bronkleuren uit/aan** in de bronweergave.
- Alle bestaande namenpagina's, popups, losse notities en zoekfuncties.

De gewone leesweergave blijft de bestaande wiki-super-opmaak gebruiken. De volledige originele RTF-opmaak staat in de bronweergave; het zijn bewust verschillende weergaven van dezelfde bron.

## Redactionele aandachtspunten

De bestaande typen en identiteiten zijn behouden. Een samengestelde naam zoals **Eden** is hier nog de bestaande gecombineerde pagina met type ‘stad’; die is niet gelijkgesteld aan een naam-ID van wiki-normaal. Automatisch opnieuw classificeren zou verschillende personen of plaatsen kunnen samenvoegen.

Negen bestaande feitcitaten zijn niet volledig letterlijk in één nieuw vers bevestigd. Ze zijn behouden, op de site gemarkeerd als citaat uit de eerdere wiki, en apart geïnventariseerd in changes.json: Jezus, Boaz, Jesua, Nebukadnessar, Joel, Salmon, Artachsasta, Jakobus III en Judas. Hun beweringen zijn niet door nieuwe AI-teksten vervangen.

De oude naamkey `mj` blijft bestaan, maar heeft geen actuele verstekstvermeldingen. De 1.494 losse studienotities zijn uit de vorige wiki behouden; de aangeleverde hoofdtekst is geen nieuwe afzonderlijke notitie-uitgave.

## Bewijs en herstel

- [Onafhankelijke controle](verification.json)
- [Browsercontrole](browser.json) en [preview-afbeelding](preview.png)
- [Herhaalcontrole](idempotence.json)
- [Testlog](unit-tests.txt)
- [SHA-256 van oorspronkelijke basisdata](baseline-manifest.json)
- [Herstelarchief met oorspronkelijke data](baseline-data.tar.gz)
- [Nieuwe bron en toekomstige updateprocedure](../../docs/RTF-UPDATES.md)

De browsercontrole omvat alle 66 boeken, bestaande naam-IDs, notities, nummeronderscheidingen, oorspronkelijke bronregels over een chunkgrens en aan het einde van de bron, bronkleuren, vergelijking, zoeken, desktop en mobiel. Alle 341 datafiles zijn via de lokale Worker op SHA-256 gecontroleerd. Er waren geen JavaScript- of resourcefouten. De broncontrole vergelijkt alle 217.428 regels met alle karakterstijlen. De herhaalcontrole gaf 0 veranderde bestanden, 0 nieuwe verzen en 0 gewijzigde bestaande versteksten.

## Publicatie

De publicatie is voorbereid voor de afzonderlijke Worker **studieb-wiki-rtf-preview** en KV-namespace **studieb-wiki-rtf-preview-data**. De nieuwe releaseprefix is `rtf-c13e0a4e9df20358184a/`.

De Composio-verbinding werd actief, maar de eerste API-aanroep mislukte doordat de beperkte API-token als X-Auth-Key werd verstuurd (Cloudflare 6103). De rechtstreekse API is vanuit deze uitvoeromgeving door de netwerkproxy geblokkeerd. Daarom is een aparte GitHub Actions-workflow toegevoegd die het juiste Bearer-formaat gebruikt. Daarvoor moet de gebruiker één repositorysecret **CLOUDFLARE_API_TOKEN** in het beveiligde GitHub-scherm invullen.

**De preview is bij het opstellen van dit verslag nog niet op Cloudflare gepubliceerd.** De bestaande productie-Worker en productiedata zijn niet gewijzigd. Het concrete preview-adres verschijnt na een geslaagde workflow in het Actions-overzicht en `deployment.json`. Daarna kan de gebruiker de preview beoordelen voordat productie wordt bijgewerkt.
