# CSIR-Control-Register

Excel-werkboek om de Cybersecurity Implementatierichtlijn Objecten (CSIR) praktisch toe te passen en bij te
houden voor een object, bijvoorbeeld: een tunnel, gemaal, brug, sluis of verkeersinstallatie.

Je stelt op één blad het object en de functiebox in. Daaruit volgt het weerstandsniveau, en daarmee
beweegt de rest van het werkboek mee: welke van de 268 maatregelen op dat niveau gelden, welke van de
127 controls je van toepassing verklaart, en hoe ver je bent. De eisteksten zijn woordelijk uit de
CSIR overgenomen, zodat je ze rechtstreeks in een vraagspecificatie of contract kunt gebruiken.

Status: prototype. Werkt en is te gebruiken; geen belofte over onderhoud.

## Voor wie

CISO's, ISO's, objectbeheerders en projectleiders bij publieke organisaties die objecten met
industriële automatisering (IA/PA/OT) beheren. Ook bruikbaar als eisenbron bij een aanbesteding of
een contract met een leverancier.

## Snel starten

1. Download [het werkboek](werkboek/csir-control-register.xlsx) en open het in Excel.
2. Blad **Instellingen**: vul de objectnaam in en kies de functiebox (A–E). Het weerstandsniveau
   rolt eruit. Laat je de functiebox leeg, dan waarschuwt het werkboek daarover.
3. Blad **VSP Proceseisen** en **VSE Systeemeisen**: loop de 127 controls langs en verklaar per
   control *Van toepassing*. Ze staan voorgevuld op "Ja"; zet ze op Nee of N.v.t. waar het risico
   buiten de scope van de opdracht valt en onderbouw dat.
4. Blad **Maatregelen**: kolom *Geldt (dit object)* toont wat op jouw niveau geldt; de rest staat
   grijs. Houd per regel de status en het bewijs bij.
5. Blad **Dashboard**: de tellers werken live mee.

Het werkboek is een sjabloon: er staat geen object in. Kopieer het per object.

## Bijdragen

Zie de [CONTRIBUTING](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md) van
de organisatie: daar staat per project een formulier, ook zonder Git-ervaring. Een issue of
discussion is een volwaardige bijdrage.

## Licentie

EUPL-1.2, zie [LICENSE](LICENSE). Die licentie dekt wat in dit project zelf gemaakt is: de opzet van
het werkboek, de formules, het dashboard en de documentatie.

**De eisteksten zelf vallen daar niet onder.** De controls en maatregelen zijn woordelijk overgenomen
uit de Cybersecurity Implementatierichtlijn Objecten, uitgegeven door Rijkswaterstaat en Het
Waterschapshuis. Het auteursrecht daarop ligt bij hen. Gebruik het werkboek zoals je de CSIR zelf zou
gebruiken.

## Wat er in het werkboek zit

| Blad | Inhoud |
|---|---|
| **Instellingen** | Object, functiebox, keten-analyse, berekend weerstandsniveau, versiebeheer |
| **Toelichting** | Uitleg, gebruiksinstructie, legenda |
| **Dashboard** | Live tellers: voortgang per blad en per paragraaf, in en uit scope |
| **VSP Proceseisen** | 89 proces-controls, met de BIO-bron erbij |
| **VSE Systeemeisen** | 38 systeem-controls |
| **Maatregelen** | Alle 268 maatregelen met de niveaukolommen N1–N4 |
| **Bijlagen** | CSR 1–24 plus A, B en C |

In cijfers: **127 controls** (89 + 38), **268 maatregelen** en **27 bijlagen**. Per weerstandsniveau
gelden 193, 198, 230 en 234 maatregelen; een maatregel kan op meerdere niveaus gelden.

## Hoe het rekent

- **Functiebox naar niveau.** A=4, B=3, C=2, D=1, E=1. Het berekende niveau stuurt via `CHOOSE` alle
  formules aan, dus één wijziging op Instellingen beweegt het hele werkboek mee.
- **Ketenregel.** Bedient of beheert dit object andere objecten, dan gaat het niveau omhoog naar dat
  van het zwaarste bestuurde object. Dat is de regel uit §0.3 van de CSIR: het bedienende object gaat
  omhoog, niet het bediende.
- **Van toepassing naar scope.** De kolom *Aangeroepen §2* op de controlbladen koppelt een control aan
  een maatregelparagraaf. Staat minstens één aanroepende control op "Ja", dan komt die paragraaf op
  het maatregelenblad in scope.
- **Twee percentages.** *% geïmplementeerd* telt alleen wat af is; *% afgehandeld* telt ook de
  onderbouwde afwijkingen mee, omdat comply-or-explain in de CSIR een geldige eindtoestand is.

De opmaak (kleuren in koppen en accenten) is vrij aan te passen aan de eigen huisstijl.
