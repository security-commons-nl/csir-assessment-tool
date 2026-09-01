# Waar de inhoud vandaan komt

Een register dat eisen uit een norm overneemt, is alleen bruikbaar als navolgbaar is wat brontekst is
en wat eigen invulling. Deze pagina legt dat per kolom vast.

## Bron

De inhoud komt uit de **Cybersecurity Implementatierichtlijn Objecten (CSIR), versie 3.0**, uitgegeven
door Rijkswaterstaat en Het Waterschapshuis. Daarnaast bestaat een gestripte variant voor
aanbestedingen, waarin het hoofdstuk met de controls ontbreekt.

Die twee zijn voor het maatregelenhoofdstuk **identiek**: dezelfde 268 maatregelen, dezelfde teksten,
dezelfde paragraafnummers en dezelfde niveaumarkeringen, plus dezelfde bijlagen CSR 1–24 en A, B en C.
Alle §2- en CSR-verwijzingen in dit register gelden dus in beide varianten. Alleen de controlnummers
bestaan uitsluitend in de volledige versie.

## Wat letterlijk is overgenomen

| Onderdeel | Aantal |
|---|---|
| Maatregelteksten | 268 |
| Control-eisen (kolom C op VSP en VSE) | 127 |
| Niveaumarkeringen N1–N4 | 268 × 4 |
| Paragraafnummers en BIO-bronnummers | alle |
| Groepskoppen van de fysieke-toegangsparagrafen | 65 |
| Bijlagenummering CSR 1–24 plus A, B en C | 27 |
| Functiebox-tabel en het ketenregel-citaat | — |

Elke tekst is met twee onafhankelijke extractiemethodes tegen de bron gelegd: één op basis van
tekstcoördinaten, één op basis van vaste kolomposities. De niveaumarkeringen zijn op coördinaten
uitgelezen, omdat de tabellen in de bron over pagina's heen verspringen; de uitkomsten zijn steekproefsgewijs
visueel geverifieerd tegen de opgemaakte pagina's.

## Wat eruit is afgeleid

- **Thema** — de paragraaftitels, herschreven tot korte labels.
- **Aangeroepen §2** en **Bijlage (CSR)** — de verwijzingen die in de controltekst zelf staan,
  uitgelicht in een eigen kolom zodat je erop kunt filteren.
- **Groep** buiten de fysieke-toegangsparagrafen — spelling geharmoniseerd.
- **Type** op het bijlagenblad — "richtlijn" volgt uit de bron; bij twee bijlagen is "template" een
  eigen inschatting.
- Drie bijlagetitels zijn ingekort of uitgeschreven.

## Wat eigen invulling is

De hele werkwijzelaag is van dit register en staat niet in de CSIR: de kolommen *Van toepassing*,
*Status*, *Invulling / bewijs*, *Verantwoordelijke* en *Comply-or-explain*, de berekende kolommen
*Geldt (dit object)* en *In scope? (auto)*, het complete dashboard met alle tellers, de nummering in
kolom A, en de kolom *Korte omschrijving* op de controlbladen. Die laatste is een navigatiehulp en
draagt dat ook als kop: **niet normatief**. Neem hem nooit over in een contract; gebruik kolom C.

## Bewuste afwijkingen van de letterlijke tekst

| Wat | Waarom |
|---|---|
| `Tme23` → `TMe23` | Typefout in de bron, in beide varianten |
| Tweede `MM1` → `MP1` | De bron gebruikt `MM1` twee keer; de tweede staat in de groep "Procedures en Organisatie" en wordt gevolgd door MP2, MP3 en MP4 |
| `LM11` blijft `LM11` | Ook een bronafwijking van het patroon, maar ongemoeid gelaten omdat de code nergens botst |
| Eén maatregel noemt "CO3" waar CO4 logisch zou zijn | Letterlijk overgenomen |
| Twee maatregelen hebben identieke tekst op niveau 1 en 2 | Letterlijk overgenomen; ze zijn in de bron werkelijk gelijk |
| Eén control verwijst naar "paragraaf 2.42" | Letterlijk overgenomen; de gecorrigeerde verwijzing §2.4.2 staat in de kolom *Aangeroepen §2* |
| Eén control eindigt met de ingevulde objectnaam | De bron heeft daar de placeholder "Lijst Objecten: xx – cybersecurity weerstandsniveau xx"; die xx-en zijn vervangen door de ingestelde waarden |

De bron is op één punt intern inconsistent: de functiebox-tabel in de inleiding laat de waarde bij **E**
leeg, terwijl de tabel bij het maatregelenhoofdstuk E=1 geeft. Het register volgt het
maatregelenhoofdstuk.

## Grenzen van dit register

Het register dekt het strategische deel van een CSIR-implementatie: classificatie, weerstandsniveau,
de bijbehorende maatregelenset en de verantwoording daarover. Het dekt het risicodeel **niet**.

Wie de CSIR op een **bestaand** object toepast, werkt risicogestuurd: per maatregel die niet voldoet
een kans en een impact bepalen, daaruit een risicowaarde, en per risico een formele acceptatie of een
mitigerende maatregel met kosten en doorlooptijd. Daar heeft dit werkboek geen kolommen voor. Het
verschil zit in de meetlat: dit register meet voortgang richting volledige implementatie, terwijl een
risicogestuurde aanpak meet of het restrisico aanvaardbaar is. Voor nieuwbouw en algehele renovatie is
de eerste meetlat de juiste; voor bestaande objecten de tweede.

Ook niet aanwezig: een gap-analyse met de tussenwaarden "voldoet deels" en "informatie ontbreekt",
ruimte voor objectspecifieke maatregelen buiten de CSIR, en velden voor prioritering, planning en
herijkingsdatum.
