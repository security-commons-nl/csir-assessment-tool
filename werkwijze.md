# Zo gebruik je het register

Het register maakt de vervolgstappen ná de objectclassificatie concreet en toetsbaar: van *"wat
schrijft de CSIR voor"* naar *"wat gaan wij voor dít object doen, op welk niveau, en waarom"*.

## De vijf stappen

1. **Classificeren.** Het object heeft een functiebox (A–E) uit de objectclassificatie. Die bepaalt
   het weerstandsniveau: A=4, B=3, C=2, D=1, E=1. Vul beide in op blad Instellingen. Heb je die
   classificatie nog niet gedaan, begin dan bij het classificatieformulier (zie hieronder); in de
   [webversie](https://security-commons-nl.github.io/csir-control-register/) is dat het eerste
   tabblad en stroomt de uitkomst vanzelf door.
2. **Baseline vaststellen.** Loop de controls op VSP en VSE langs en verklaar ze van toepassing.
   Uitgangspunt is dat de volledige set geldt; wijk je af, dan doe je dat risicogestuurd en leg je
   dat vast.
3. **Maatregelen selecteren.** Op het maatregelenblad toont de kolom *Geldt (dit object)* wat op het
   gekozen niveau geldt. *In scope? (auto)* combineert dat met je van-toepassing-keuzes.
4. **Verantwoorden.** Houd per regel de status bij en leg bewijs vast. Afwijkingen krijgen status
   *Explain (afwijking)* met een onderbouwing.
5. **Vastleggen.** De complete invulling en alle afwijkingen horen in het Cybersecurity Dossier /
   Beveiligingsplan (bijlage B), met een jaarlijkse toetsing volgens de PDCA-cyclus.

Stap 1 tot en met 3 en stap 5 zijn constant. Alleen de vertaalslag naar contracteisen hangt ervan af
of je het werk uitbesteedt.

## De classificatie ervoor

De functiebox komt niet uit dit register maar uit de objectclassificatie, en die is een stap op zich.
Je beoordeelt het potentiële gevolg als het object faalt, uitvalt of niet beschikbaar is, langs zes
criteria: veiligheid van medewerker en publiek, maatschappelijke gevolgen, financiële en
herstelschade, cascade- en dominoeffecten, ecologische schade, en imago- en politieke schade. Elk
criterium scoor je van 1 (klein) tot 5 (catastrofaal), met per stap een concrete drempel: minder dan
duizend of meer dan vijfhonderdduizend getroffen personen, minder dan vijf ton of meer dan vijfhonderd
miljoen euro schade, interne commotie of langdurig geen college.

Het formulier neemt daarvan het **afgeronde gemiddelde** en vertaalt dat naar de functiebox: 1=E, 2=D,
3=C, 4=B, 5=A. Dat gemiddelde heeft een prijs die je moet kennen: een enkel zwaar gevolg middelt weg.
Een 5 op cascade tussen vijf enen komt uit op box D, terwijl datzelfde cascade-effect in de praktijk
de reden is dat het object ertoe doet. De webversie zet daarom de strengste lezing ernaast, de hoogste
score, zodat je ziet wat het verschil is voordat je hem vaststelt. Het formulier blijft leidend; wijk
je ervan af, onderbouw dat dan bij de opmerkingen.

**De onderbouwing is het product, niet het cijfer.** Wat je later moet kunnen uitleggen aan een
bestuurder, een auditor of een leverancier is waarom een gevolg zwaar of licht is ingeschat, niet
welk getal eruit rolde. Vul daarom per criterium de onderbouwing in, ook als de score vanzelfsprekend
lijkt.

## De ketenregel

De CSIR stelt in §0.3: *"Elke keten is zo sterk als de zwakste schakel. Indien de bediening of het
beheer van object A wordt gedaan vanuit een initieel lager geclassificeerd object B, wordt de
classificatie van dat object B verhoogd tot het cybersecurity weerstandsniveau van object A."*

Het **bedienende** object gaat dus omhoog. Vul op Instellingen daarom de objecten in die vánuit dit
object worden bediend of beheerd; het zwaarste daarvan bepaalt de ophoging. Wordt dit object juist
zelf vanuit een ander object bediend, dan moet dát andere object omhoog — niet dit object. Een
centrale bediening zit dus minimaal op het niveau van het zwaarste object dat zij aanstuurt.

## Selectie op het maatregelenblad

Het blad toont alle 268 maatregelen. Wat op het gekozen niveau geldt staat in *Geldt (dit object)* op
"Ja"; de overige regels staan grijs. Zo blijft de selectie zichtbaar meebewegen met het niveau zonder
dat er iets verdwijnt.

Wil je alleen de geldende set zien, filter die kolom dan op "Ja". **Let op:** Excel past een bestaand
filter niet vanzelf opnieuw toe. Na elke niveauwijziging moet je het filter herhalen, anders blijven
rijen ten onrechte verborgen.

## Wat er onder de motorkap gebeurt

- **Namen.** `Object`, `Functiebox` en `Niveau` zijn workbook-brede namen die naar Instellingen
  wijzen. Alle titels en formules gebruiken ze, dus het werkboek is object- en niveau-onafhankelijk.
- **Niveauselectie.** Overal `CHOOSE(Niveau; N1; N2; N3; N4)`. Bij niveau 3 pakt elke formule
  automatisch kolom N3.
- **Scope-logica.** Vier verborgen hulpkolommen tellen per maatregel hoeveel controls die paragraaf
  aanroepen, hoeveel daarvan op "Ja" staan en hoeveel er nog leeg zijn. Daaruit volgt *In scope*,
  *Buiten scope*, *Nog te bepalen* of *Niet op dit niveau*. De koppeling loopt ook via de
  bovenliggende paragraaf: een control die §2.5 aanroept dekt §2.5.1, §2.5.2 en §2.5.3.
- **Celbeveiliging.** Instellingen is beveiligd zonder wachtwoord; alleen de invoervelden zijn
  bewerkbaar en het berekende niveau is vergrendeld. Ontgrendelen kan via *Controleren → Blad
  ontgrendelen*. De overige bladen zijn vrij.
- **Lege functiebox.** Zolang die leeg is toont het niveauveld een waarschuwing en waarschuwen ook de
  koppen van Dashboard, VSP, VSE en Maatregelen. De onderliggende waarde is dan 1, zodat de formules
  blijven werken, maar dat is een voorlopige waarde en geen vastgesteld niveau.

## De CSIR in een contract

De eisen horen bindend in het contract; de gestripte CSIR-variant voor aanbestedingen gaat mee als
aangeroepen bijlage; het Cybersecurity Dossier is een op te leveren product.

**In de vraagspecificatie:**

- De van-toepassing-verklaarde controls, vertaald naar proces- en systeemtechnische eisen.
- Per eis de verwijzing uit de kolommen *Aangeroepen §2* en *Bijlage (CSR)*.
- Het vereiste weerstandsniveau expliciet benoemd; niveau 1 is de ondergrens.
- Comply-or-explain: afwijkingen onderbouwd en vastgelegd als non-compliancy (bijlage C).
- Auditrecht (control 15.1.2.6) en een verwerkersovereenkomst als de leverancier persoonsgegevens
  verwerkt (15.1.1.3 en 18.1.4).
- Medewerking aan risicogestuurd (pen)testen en aan de PDCA-cyclus (5.1.1.1).
- Einde-contractbepaling: objectinformatie overdragen én resterende data vernietigen (8.3.2.2,
  CSR 1, CSR 23).
- Maximale hardening door de leverancier van randapparatuur en datanetwerk (6.2.1.2).

**Als op te leveren product:** het Cybersecurity Dossier / Beveiligingsplan (bijlage B), en waar van
toepassing een Recovery Plan (CSR 15), een CMDB (CSR 16), back-upmanagement (CSR 18) en een
continuïteitsplan energievoorziening (CSR 12).

**Let op bij de gestripte variant.** Daarin ontbreekt het hoofdstuk met de controls. De
controlnummers (5.1.1.1, 15.1.2.6 en zo verder) zijn daar dus niet terug te vinden. De §2- en
CSR-verwijzingen zijn wél rechtstreeks bruikbaar. Dat is precies waarom de controls als eisen in de
vraagspecificatie moeten landen.

## Onderhoud

Register-versie, opsteller en datum staan in het metadatablok op Instellingen. Voor een nieuw object
kopieer je het bestand en pas je alleen dat blad aan. Verschijnt er een nieuwe CSIR-versie, controleer
dan of controls, maatregelen of niveaus zijn gewijzigd.
