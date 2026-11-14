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
| Regressietests | 26 geslaagd |
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

**De aparte preview is gepubliceerd:** [https://studieb-wiki-rtf-preview.ecodorpgezocht.workers.dev](https://studieb-wiki-rtf-preview.ecodorpgezocht.workers.dev). De [GitHub Actions-workflow](https://github.com/BBsSolutions-Hosting-FreemiumApps/wiki-super/actions/runs/43610676948) is succesvol afgerond. Het [publicatiebewijs](deployment.json) bevat de namespace, de releaseprefix en de controle-uitkomsten.

Alle **341 opgeslagen databestanden** zijn via de Cloudflare-API op SHA-256 gecontroleerd. De productie-Worker is vóór en na de preview-publicatie op alle modulebytes vergeleken; die broncode is ongewijzigd. De laatste publicatie hergebruikte de volledige bestaande previewrelease en deed 0 nieuwe KV-schrijfacties.

**Beperking:** Cloudflare geeft de Python HTTP-testclient fout 1010; de cloudbrowser kon geen toegang tot de pagina krijgen. Daarom staat de openbare browsercontrole als **geblokkeerd**, niet als geslaagd. De 14 browsercontroles en de HTTP-controle van alle 341 bestanden zijn lokaal op dezelfde release geslaagd; alle opgeslagen Cloudflare-data is bovendien onafhankelijk via de API bevestigd. De gebruiker kan de online preview openen en per vers **Vergelijk vorige versie** kiezen. Productie is nog niet naar deze update omgezet.

## Versrecords per boek

Dit zijn technische records, inclusief herhaalde en parallelle bronverwijzingen; de aantallen zijn geen nieuwe canonieke versnummering.

| Boek | Vorige versie | Huidige versie | Toegevoegd | Bestaande tekst bijgewerkt |
| --- | ---: | ---: | ---: | ---: |
| Genesis | 1479 | 1542 | 63 | 123 |
| Exodus | 1147 | 1216 | 69 | 55 |
| Leviticus | 851 | 859 | 8 | 3 |
| Numeri | 1244 | 1286 | 42 | 25 |
| Deuteronomium | 160 | 959 | 799 | 38 |
| Jozua | 583 | 661 | 78 | 31 |
| Richteren | 593 | 620 | 27 | 3 |
| Ruth | 85 | 85 | 0 | 0 |
| 1 Samu-el | 799 | 812 | 13 | 7 |
| 2 Samu-el | 684 | 697 | 13 | 22 |
| 1 Koningen | 799 | 820 | 21 | 42 |
| 2 Koningen | 696 | 731 | 35 | 34 |
| 1 Kronieken | 657 | 725 | 68 | 37 |
| 2 Kronieken | 785 | 826 | 41 | 56 |
| Ezra | 251 | 284 | 33 | 10 |
| Nehemia | 373 | 414 | 41 | 10 |
| Esther | 167 | 167 | 0 | 0 |
| Job | 215 | 1071 | 856 | 25 |
| Psalm | 199 | 203 | 4 | 5 |
| Spreuken | 874 | 915 | 41 | 23 |
| Prediker | 214 | 222 | 8 | 50 |
| Hooglied | 112 | 117 | 5 | 15 |
| Jesaja | 1251 | 1291 | 40 | 20 |
| Jeremia | 1331 | 1367 | 36 | 24 |
| Klaagliederen | 154 | 154 | 0 | 0 |
| Ezechi-el | 1272 | 1286 | 14 | 9 |
| Dani-el | 268 | 357 | 89 | 11 |
| Hosea | 197 | 197 | 0 | 8 |
| Jo-el | 73 | 73 | 0 | 8 |
| Amos | 146 | 146 | 0 | 7 |
| Obadja | 21 | 21 | 0 | 0 |
| Jona | 48 | 48 | 0 | 1 |
| Micha | 107 | 108 | 1 | 3 |
| Nahum | 47 | 47 | 0 | 0 |
| Habakuk | 56 | 56 | 0 | 2 |
| Sefanja | 53 | 53 | 0 | 0 |
| Haggaï | 38 | 38 | 0 | 0 |
| Zacharia | 207 | 211 | 4 | 2 |
| Maleachi | 54 | 55 | 1 | 1 |
| Mattheus | 917 | 1077 | 160 | 244 |
| Markus | 509 | 684 | 175 | 143 |
| Lukas | 1025 | 1156 | 131 | 191 |
| Johannes | 737 | 886 | 149 | 183 |
| Handelingen | 725 | 1006 | 281 | 105 |
| Romeinen | 433 | 434 | 1 | 1 |
| 1 Korinthie-ers | 433 | 437 | 4 | 2 |
| 2 Korinthie-ers | 254 | 255 | 1 | 1 |
| Galaten | 149 | 149 | 0 | 0 |
| Efezie-ers | 155 | 155 | 0 | 0 |
| Filippie-ers | 104 | 104 | 0 | 0 |
| Kolossers | 94 | 95 | 1 | 1 |
| 1 Thessalonikers | 88 | 89 | 1 | 1 |
| 2 Thessalonikers | 47 | 47 | 0 | 0 |
| 1 Timotheus | 113 | 113 | 0 | 10 |
| 2 Timotheus | 82 | 83 | 1 | 1 |
| Titus | 46 | 46 | 0 | 0 |
| Filémon | 25 | 25 | 0 | 0 |
| Hebree-en | 300 | 303 | 3 | 2 |
| Jakobus | 107 | 108 | 1 | 3 |
| 1 Petrus | 104 | 105 | 1 | 1 |
| 2 Petrus | 61 | 61 | 0 | 1 |
| 1 Johannes | 105 | 105 | 0 | 0 |
| 2 Johannes | 13 | 13 | 0 | 0 |
| 3 Johannes | 15 | 15 | 0 | 0 |
| Judas | 25 | 25 | 0 | 0 |
| Openbaring | 340 | 405 | 65 | 16 |
