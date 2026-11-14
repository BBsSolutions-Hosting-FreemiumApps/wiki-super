# RTF-updates voor wiki-super

Deze procedure gebruikt de RTF rechtstreeks. De bronlezer komt uit de gecontroleerde converter van `wiki-normaal`, commit `4ed4fe2`. `build/parse.py` maakt de leesweergave; `build/update_rtf.py` behoudt bestaande naamkeys en versadressen. De bestanden van `wiki-normaal` zijn niet nodig bij een volgende update.

## Volgende RTF verwerken

1. Maak een nieuwe werkbranch vanaf de laatste goedgekeurde versie van **wiki-super**. De eerste update staat op `update-rtf-2026-11-14`, gebaseerd op `main` (`3d781dc`).
2. Upload/vervang `sources/studiebijbel-2026.rtf`.
3. Voer onderstaande commando's uit. Kies een nieuwe uitvoermap **buiten** de repository; bestaande uitvoermappen worden geweigerd.

```bash
python3 -m unittest discover -s tests -v
python3 build/update_rtf.py --source sources/studiebijbel-2026.rtf --baseline . --output /tmp/wiki-super-update
python3 build/verify_update.py --source sources/studiebijbel-2026.rtf --baseline . --site /tmp/wiki-super-update --report /tmp/wiki-super-update/reports/verification.json
node build/make_worker.js /tmp/wiki-super-update
node build/local-server.mjs /tmp/wiki-super-update 8787
```

Open `http://localhost:8787`. Kies een vers en **Vergelijk vorige versie**. **Oorspronkelijke RTF** toont de volledige bron met opmaak, ook de annotaties die de leesweergave weglaat. De bronkleuren zijn uitschakelbaar.

Met Playwright 1.62.1 en Chromium geïnstalleerd:

```bash
WIKI_RELEASE=/tmp/wiki-super-update node tests/browser-update.cjs http://localhost:8787 /tmp/wiki-super-update/reports/browser.json
python3 build/update_rtf.py --source sources/studiebijbel-2026.rtf --baseline /tmp/wiki-super-update --output /tmp/wiki-super-repeat
python3 build/check_repeat.py /tmp/wiki-super-update /tmp/wiki-super-repeat
```

De browsercontrole voor deze migratie kent het oorspronkelijke aantal 25.296 als grens voor nieuw toegevoegde IDs. Die controle is migratiespecifiek; de converter en broncontrole zijn herbruikbaar.

## Wat behouden blijft

- Alle bestaande naamkeys, typen, spellingvarianten, nummeronderscheidingen en relatiegegevens.
- Alle bestaande vers-IDs en hun boek/hoofdstuk/vers. Nieuw gevonden verzen krijgen alleen hogere IDs; een afzonderlijke leesvolgorde houdt de Bijbeltekst op de juiste plaats.
- De 1.494 losse studienotities. Een nieuwe RTF bevat niet automatisch een nieuwe versie van die afzonderlijke notities.
- Bestaande feiten en hun citaat. Een letterlijk teruggevonden citaat kan naar een nauwkeuriger vers worden verwezen; een onbevestigd citaat blijft expliciet gemarkeerd als afkomstig uit de eerdere wiki.
- Een herstelarchief en SHA-256 manifest van alle basisdata vóór iedere conversie.

De complete RTF wordt afzonderlijk in bronregels met stijlen bewaard. Dat is de controlebron voor tekst die volgens de bestaande leesregels niet in de gewone verstekst verschijnt. De leesweergave gebruikt de bestaande wiki-opmaak; de bronweergave behoudt de RTF-opmaak.

De converter herclassificeert namen niet. De bestaande wiki heeft bijvoorbeeld een samengestelde Eden-pagina en de oude classificatie ‘stad’. De RTF-update lost zulke redactionele identiteitvragen niet automatisch op. Naam `mj` is als bestaand record behouden, maar heeft geen actuele tekstvermeldingen.

## Handmatige GitHub Action

Workflow `.github/workflows/rtf-update.yml` bouwt een controlepakket op een werkbranch. De workflow publiceert en pusht niets. Het pakket bevat data, de Worker, een herstelkopie en controleverslagen. GitHub kan vereisen dat de workflow op de standaardbranch bekend is voordat de knop **Run workflow** verschijnt. De lokale commando's werken al zonder die registratie.

## Cloudflare-preview en productie

De nieuwe preview krijgt een eigen Worker **`studieb-wiki-rtf-preview`** en een eigen KV-namespace **`studieb-wiki-rtf-preview-data`**. Bind de namespace als `DATA` aan de Worker. Gebruik geen productiedomein voor de preview.

`node build/make_worker.js UITVOERMAP` maakt `worker/worker.mjs` en `worker/release.json`. Het manifest bevat de unieke prefix en de hashes van **alle** datafiles. Upload elke JSON-file onder `PREFIX + bestandsnaam`, controleer de hashes en upload pas daarna de Worker. Het manifest voorkomt dat een oude KV-cache of een gedeeltelijke upload data van verschillende versies mengt. De Worker geeft de actieve prefix terug via `/version.json`; workers.dev is `noindex`.

Na beoordeling van de concrete preview kan de goedgekeurde release op de live Worker worden gezet. Bewaar eerst de bestaande Worker-code en KV-bindingen. Upload de volledige nieuwe release onder haar eigen prefix; wissel daarna de Worker. Terugzetten kan met de opgeslagen vorige Worker en binding. De oorspronkelijke `w1/`-sleutels worden daarvoor niet verwijderd.

Gebruik de oude `deploy/*.js` niet voor RTF-updates: die zijn een historisch v9-pakket met vaste productiedoelen. De nieuwe release wordt samengesteld met `build/make_worker.js`.

## Voorbeeldopdracht

> Werk wiki-super bij met de bijgevoegde RTF. Gebruik de laatst goedgekeurde updatebranch als basis en bevestig die branch. Voer build/update_rtf.py en alle passende controles uit, behoud bestaande naamkeys en versadressen, toon de wijzigingen in een aparte Cloudflare-preview en geef een controleverslag. Publiceer pas na beoordeling van die preview.

## Preview publiceren via GitHub Actions

Maak in GitHub bij Settings → Secrets and variables → Actions één repositorysecret met de naam `CLOUDFLARE_API_TOKEN`. Plak uitsluitend de Cloudflare-tokenwaarde in het beveiligde secretveld. Het token heeft binnen het juiste account Workers Scripts: Edit, Workers KV Storage: Edit en Account Settings: Read nodig.

Workflow **Cloudflare RTF preview** start op de eerste push van de updatebranch en kan daarna opnieuw worden uitgevoerd. Hij controleert de volledige RTF en bestaande identiteiten, vindt het account via de bekende bestaande KV-namespace, schrijft alleen naar de afzonderlijke preview-namespace en Worker, en controleert alle 341 publiek opgeleverde datafiles op hun SHA-256. De productie-Worker wordt alleen gelezen om te bevestigen dat die niet veranderde. Het concrete preview-adres verschijnt in het workflowoverzicht en `deployment.json`.

De Composio-koppeling was in deze sessie actief, maar stuurde de beperkte API-token als `X-Auth-Key`; Cloudflare gaf daarvoor fout 6103. De Actions-workflow gebruikt het juiste `Authorization: Bearer`-formaat. Er is geen Global API key nodig.
