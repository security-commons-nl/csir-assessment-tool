# register/ — de CSIR Assessment Tool in de browser

Eén zelfstandig HTML-bestand: alle eisteksten, maatregelen, drempels en rekenregels zitten erin. Geen
server, geen account, geen telemetrie, geen enkele externe verwijzing. Wie hem offline wil draaien,
slaat de pagina op met Ctrl+S.

**Live:** https://security-commons-nl.github.io/csir-assessment-tool/

De tool heeft drie stappen achter elkaar, met één dossier eronder:

| Stap | Vraag | Waar het vandaan komt |
|---|---|---|
| Classificeren | Hoe erg is het als dit object faalt? | `werkboek/objectclassificatie.xlsx` |
| Bepalen | Wat geldt er dan? | `werkboek/csir-control-register.xlsx` |
| Uitwerken | Hoe vul ik dat in? | het werkboek plus de handleidingen uit de kennisbank |

## Bouwen

```bash
python register/haal_bron.py                      # werkboeken -> csir.json
python register/haal_handelingsperspectief.py     # kennisbank -> register/handelingsperspectief.json
python register/bouw.py                           # -> register/dist/index.html
python register/bouw.py site                      # of naar een andere map
```

Het bouwscript zet `csir.json` en `bron/app.js` in één scripttag en `bron/app.css` in één style-tag,
en berekent daarna de sha256 van allebei voor het Content-Security-Policy in `bron/index.html`. Het
resultaat is:

```
default-src 'none'; script-src 'sha256-...'; style-src 'sha256-...'; img-src data:;
form-action 'none'; base-uri 'none'
```

Alles wat de pagina zou kunnen ophalen of versturen staat daarmee uit, en niet alleen in een belofte.
Een test rekent de hashes na op de inhoud, dus de regel kan niet stilletjes verlopen. Bijeffect:
`fetch` en inline `style`-attributen werken niet meer; kleur en zichtbaarheid gaan daarom via classes
en het `hidden`-attribuut.

## Waar de inhoud vandaan komt

`csir.json` is de bron van de pagina. Hij wordt gemaakt uit de twee werkboeken en staat in git, zodat
elke wijziging in de review zichtbaar is. **De werkboeken zijn vanaf nu een export, geen bron:** wie
een eistekst corrigeert, doet dat in het werkboek en draait `haal_bron.py` opnieuw, of corrigeert
`csir.json` en werkt het werkboek bij. `haal_bron.py --check` en `tests/test_bron.py` blokkeren als de
twee uit elkaar lopen. Verdwijnt het Excel-werkboek ooit, dan vervalt alleen die controle.

Twee control-eisen op VSE zijn in het werkboek een formule: de richtlijntekst met de objectnaam en het
weerstandsniveau erin. Die staan in `csir.json` met de plaatshouders `{object}` en `{niveau}` open; de
pagina vult ze in, precies zoals Excel dat doet.

De app bevat geen eigen lijst met eisen, codes, statussen of drempels. Alles komt uit
`window.__BRON__`. Een test controleert dat: geen maatregelcode, geen control-id en geen eistekst mag
in `app.js` staan.

## Rekenen

`reken.py` is de referentie-implementatie; `bron/app.js` heeft dezelfde functies onder dezelfde namen
in het object `reken`. De browsertests vergelijken wat op het scherm staat met wat `reken.py`
uitrekent, dus de twee kunnen niet stil uit elkaar lopen. Dat is ook de reden dat er in JavaScript
namen met liggende streepjes staan.

De regels zijn woordelijk die van het werkboek, ook waar je iets anders zou verzinnen:

- **Classificatie.** Het formulier neemt het *afgeronde gemiddelde* van de zes gevolgscores. Een 5 op
  cascade tussen vijf enen zakt daarmee weg naar box D. De pagina toont de strengste lezing (de
  hoogste score) ernaast; welke van de twee de richtlijn bedoelt is een open vraag aan de opsteller.
- **Afronden.** Excel `ROUND(2,5;0)` is 3. Python `round(2.5)` is 2 en JavaScript `Math.round(-2.5)`
  is -2; daarom staat overal `floor(x + 0,5)`, ook in de percentages (1 van de 8 is 13 procent, niet 12).
- **Ketenregel (§0.3).** Het bedienende object gaat omhoog naar het niveau van het zwaarste object dat
  het aanstuurt, niet andersom.
- **Scope.** Roept een van toepassing verklaarde control de paragraaf aan, dan staat de maatregel in
  scope; de koppeling loopt ook via de bovenliggende paragraaf (§2.5 dekt §2.5.1 tot en met §2.5.3).
  Een paragraaf die door geen enkele control wordt aangeroepen blijft "Nog te bepalen".

Een rekenregel wijzigen is een besluit van de opsteller van het werkboek, niet van de bouwer.

## Het dossier

Eén dossier per browser, in `localStorage`. Opslaan is een download (`csir-dossier-<object>-<datum>.json`),
laden is een bestandskeuze; er gaat niets naar een server. In het dossier staat de vingerafdruk van de
bron waarmee het is gemaakt, zodat de pagina meldt wanneer een oud dossier tegen een nieuwere bron
wordt geopend. Het tabblad **Uitdraai** zet alles op een rij in de volgorde waarin het in het
Cybersecurity Dossier (bijlage B) hoort, met de afwijkingen apart voor bijlage C.

## Handreiking uit de kennisbank

Per maatregelparagraaf staan de handleidingen uit de kennisbank erbij: de CSIR zegt wat er moet
gelden, de kennisbank zegt hoe je het inricht. De koppeling staat in `paragrafen-barrieres.json` en
loopt via de barrieres van de aanvalspaden. Waar er geen handleiding is, staat de reden erbij met een
uitnodiging om er een te schrijven; een leeg vakje is geen omissie maar een schrijfopdracht.

De koppeling ligt bewust op paragraaf-niveau. De CSIR verwijst in kolom "BIO-bron" naar de
ISO 27001:2013-nummering, terwijl de normverankering van de commons BIO 2.0 (ISO 27002:2022) gebruikt.
Zonder crosswalk tussen die twee sluit een koppeling per control niet aan; dat is een volgende ronde.

## Tests

```bash
python -m pytest register/tests/ -v
```

- `test_bron.py` (17): csir.json tegen de twee werkboeken. Aantallen (89 + 38 controls, 268
  maatregelen, 27 bijlagen, 15 paragrafen), de niveauverdeling 193/198/230/234, elke eistekst,
  maatregeltekst, drempel en niveaumarkering woordelijk, unieke sleutels, bestaande verwijzingen, de
  sha256 van beide werkboeken en de auteursrechtregel.
- `test_reken.py` (22): de rekenregels, inclusief de afrondval, de ketenregel, de vier
  scope-uitkomsten en de vergelijking met de ingevulde doorloop.
- `test_bouw.py` (13): de gebouwde pagina. Alles staat erin, er is precies één script en één
  stylesheet, de CSP-hashes kloppen met de inhoud, er is geen externe verwijzing, de bouw is
  herhaalbaar, en er staat een kruimelpad en een voetregel (statuut B10).
- `test_app.py` (21): de app in Chromium. Classificeren, overnemen, de ketenregel, filteren, een
  control op Nee die een paragraaf uit scope haalt, opslaan, laden, wissen, herladen, de uitdraai en
  de afdrukweergave. De browsertests slaan zichzelf over als Playwright of Chromium ontbreekt;
  installeren doe je met `pip install playwright && python -m playwright install chromium`.

De doorloop in `tests/fixtures/doorloop-2026-09.json` is de gedeelde referentie. Zolang
`bevestigd_in_excel` onwaar is, komen de verwachte tellers uit `reken.py` zelf. Zodra dezelfde invoer
in het Excel-werkboek is gedaan en het Dashboard-blad is afgelezen, gaan die afgelezen waarden erin en
vergelijkt `test_browser_geeft_dezelfde_uitslag_als_excel` de pagina met Excel in plaats van met de
eigen referentie. Dat is de enige stap die een mens met Excel vereist.
