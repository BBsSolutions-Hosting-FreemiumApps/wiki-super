# Studiebijbel-wiki (studieb-wiki)

Wiki van personen, steden, landen, plaatsen en volken uit de **Elohim YHWH Studiebijbel** (v9).
Een naam aanklikken geeft een pop-up met wie of wat het is, met de verzen als bron. Er is een
pagina per naam, een leesweergave met klikbare namen, zoeken op naam, zoeken in de hele tekst
en zoeken op versverwijzing (bijv. "Genesis 10:8").

- Live: https://studieb.bbss.pro
- Preview: https://studieb-wiki.ecodorpgezocht.workers.dev (alleen test, `noindex`)
- Cloudflare: Worker `studieb-wiki` + KV-namespace `studieb-wiki-data` (id 82097222907c44a4a0d5db8dbb453eef), Free-plan
- studiebot.bbss.pro, de Worker `studiebot` en `/workspace/elohim/botbible` zijn niet aangeraakt.

## Bronnen (alleen gelezen)
- `/workspace/elohim/kennis-v9/studiebijbel-v9.txt` (hoofdtekst)
- `/workspace/elohim/kennis-v9/studynotes-v9.txt` (1494 aantekeningen)
- RTF- en zipbestanden zijn niet geopend. Hashes vóór en na staan in `build/*-sha-start.txt` (ongewijzigd).

## Hoe gebouwd
1. `build/parse.py`: splitst de tekst in 25.296 verzen (volgorde van de studiebijbel, ook samengevoegde verzen met `|`),
   301 kopjes `(#)`, 48 koningsprofielen (`[{Koning-…}] nn/nn`) en de aantekeningen. Annotaties als
   `[{13e generatie Adam}]`, `[{‘Beltesassar’}]` en `[{Koning-Juda}]` worden apart bewaard. Redactieregels
   (Tijdbeslag, Conversatie, NTB#, hashtags, verwijzingen) gaan niet mee in de verstekst.
2. `build/entities.py`: zoekt namen (hoofdletterwoorden die in de tekst bijna nooit met een kleine letter staan,
   plus het romeinse nummer van de studiebijbel, zoals Seba I / Seba II). Het type komt uit de tekst zelf:
   - persoon: "X verwekte", "verwekte X", "X zei/sprak/stierf…", "de profeet X", "X de zoon van Y", annotaties;
   - stad: "de stad X", "de muren/poorten/bewoners van X";
   - land: "het land X", "land van X";
   - plaats: "de berg/rivier/woestijn… X", of alleen "naar/uit/in/te X" (dan staat er "niet zeker");
   - volk/groep: groepsnamen als "de Jebusiet", "de Filistijnen".
   Spellingvarianten worden samengevoegd via een sleutel zonder streepjes en accenten (Ab-ra-ham = Abraham,
   Dâni'êl = Dani-el, Yiś·rā·’êl = Isra-el). Namen met een ander nummer blijven aparte personen.
3. `build/build_data.py`: maakt per naam: korte omschrijving, feiten met vers en citaat (vader, zoon/dochter van,
   rol, aantekening, markering), koningsprofiel, kinderen, koningen van een plaats, kopjes, aantekeningen,
   namen die vaak in hetzelfde vers staan, en alle verzen. Uitvoer in `data/` (93 JSON-bestanden, ca. 6,4 MB).
4. `site/` (index.html, app.js, style.css) wordt door `build/make_worker.js` in `worker/worker.js` gezet.
   De data staat in KV onder `w1/<bestand>`.

## Aantallen (v9, 12-11-2026)
1803 namen: 1144 personen, 63 steden, 40 landen, 323 plaatsen/gebieden, 233 volken/groepen.

## Wat niet is meegenomen / beperkingen
- Geen kennis van buitenaf, geen AI-teksten. "Doel in het leven" staat er alleen als de tekst een rol noemt
  (profeet, koning, priester…) of als er een profiel in de studiebijbel staat.
- Godsnamen en titels (Elohim, YHWH, Adonai, Theos, Kyrios…) en afgodennamen zijn uitgesloten.
- Namen die maar zelden en zonder duidelijke aanwijzing voorkomen (ca. 1900 kandidaten) zijn weggelaten.
- Personen met dezelfde naam die de studiebijbel niet nummert, staan samen op één pagina (bijv. Saul, Asa,
  Josafat). Als de tekst verschillende ouders noemt, ziet de bezoeker een waarschuwing.
- Het type is automatisch afgeleid en kan fout zijn (bijv. Eden als stad). Bij twijfel staat er een melding.
- Meerwoordige namen met spaties (bijv. "Rode Zee") zijn niet als één naam herkend.
- Boeken die in v9 nog niet volledig zijn (o.a. Psalmen, Jesaja, Deuteronomium) hebben ook minder verzen in de wiki.

## Opnieuw bouwen en uitrollen
```
cd /workspace/elohim/studieb-wiki/build
python3 parse.py && python3 entities.py && python3 build_data.py
node make_worker.js && node make_deploy.js
node local-server.mjs            # lokaal testen op http://localhost:8787
python3 browsertest.py [URL]     # browsertest (desktop + mobiel)
```
Uitrollen gaat via de Cloudflare-connector (`execute`) met `deploy/kv-*.js` (data naar KV, bulk) en
`deploy/worker.js` (Worker + workers.dev). Er staan geen sleutels of tokens in deze map.

Domein: Custom Domain `studieb.bbss.pro` is gekoppeld aan Worker `studieb-wiki` (zone bbss.pro, 12-11-2026).
`studiebot.bbss.pro` is niet gewijzigd.

In de openbare voettekst staan de copyrightregels uit de kop van studiebijbel-v9.txt, zonder het
persoonlijke e-mailadres van Jan Smit; naam, LinkedIn en de twee site-URL's blijven staan.

## Copyright
© 12-02-2023 Jan Smit, © “Elohim YHWH Bijbel” (elohim-yhwh-bijbel.nl), © “Zo heb je de Bijbel nog nooit gelezen”
(zohebjedebijbelnognooitgelezen.nl). De regels uit de kop van studiebijbel-v9.txt staan onderaan elke pagina.
