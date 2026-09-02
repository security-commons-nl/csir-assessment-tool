# CSIR Assessment Tool

De Cybersecurity Implementatierichtlijn Objecten (CSIR) toegepast op één object met industriële
automatisering: een tunnel, gemaal, brug, sluis, verkeersinstallatie of vergelijkbaar areaal.

Drie stappen achter elkaar. Je **classificeert** het object langs zes gevolgcriteria; daaruit volgen de
functiebox en het weerstandsniveau. Je **bepaalt** welke van de 127 controls je van toepassing
verklaart en welke van de 268 maatregelen op dat niveau gelden. Je **werkt** ze uit tot een dossier met
status, bewijs, verantwoordelijke en onderbouwde afwijkingen. De eisteksten zijn woordelijk uit de CSIR
overgenomen, zodat je ze rechtstreeks in een vraagspecificatie of contract kunt gebruiken.

Het kan online in je browser of in Excel. De browserversie rekent lokaal: er is geen server, geen
account en geen telemetrie, en je dossier verlaat je eigen apparaat niet.

Status: prototype. Werkt en is te gebruiken; geen belofte over onderhoud.

## Voor wie

CISO's, ISO's, objectbeheerders en projectleiders bij publieke organisaties die objecten met
industriële automatisering (IA/PA/OT) beheren. Ook bruikbaar als eisenbron bij een aanbesteding of
een contract met een leverancier.

## Snel starten

1. Open de [CSIR Assessment Tool](https://security-commons-nl.github.io/csir-assessment-tool/) in je browser.
2. **Classificeren.** Scoor de zes gevolgcriteria van 1 tot 5 en onderbouw elke score. De functiebox
   (A–E) en het weerstandsniveau (1–4) rollen eruit. Bedient dit object andere objecten, dan gaat het
   niveau mee omhoog met het zwaarste object dat het aanstuurt.
3. **Bepalen.** Loop de 127 controls langs en verklaar per control *Van toepassing*. Ze staan
   voorgevuld op "Ja"; zet ze op Nee of N.v.t. waar het risico buiten de scope van de opdracht valt en
   onderbouw dat. Op het maatregelenblad zie je direct wat daarmee in scope komt.
4. **Uitwerken.** Houd per maatregel de status en het bewijs bij. Per paragraaf staan de handleidingen
   uit de [kennisbank](https://security-commons-nl.github.io/kennisbank/) erbij: de richtlijn zegt wat
   er moet gelden, die zeggen hoe je het inricht.
5. **Uitdraai.** Het laatste tabblad zet alles op een rij in de volgorde waarin het in het
   Cybersecurity Dossier hoort, met de afwijkingen apart. Sla je dossier op als bestand; het is een
   gewone JSON die je later weer inleest.

**Liever Excel?** Download [het werkboek](werkboek/csir-control-register.xlsx) en het
[classificatieformulier](werkboek/objectclassificatie.xlsx). Beide rekenen hetzelfde. Het werkboek is
een sjabloon: er staat geen object in, dus kopieer het per object.

De uitleg bij het werkboek staat op de [uitlegpagina](https://security-commons-nl.github.io/csir-assessment-tool/uitleg/):
de werkwijze stap voor stap en de verantwoording van elke kolom.

## Bijdragen

Zie de [CONTRIBUTING](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md) van
de organisatie: daar staat per project een formulier, ook zonder Git-ervaring. Een issue of
discussion is een volwaardige bijdrage.

## Licentie

EUPL-1.2, zie [LICENSE](LICENSE). Die licentie dekt wat in dit project zelf gemaakt is: de opzet van
het werkboek, de formules, het dashboard, de webversie en de documentatie.

**De eisteksten zelf vallen daar niet onder.** De controls en maatregelen zijn woordelijk overgenomen
uit de Cybersecurity Implementatierichtlijn Objecten, uitgegeven door Rijkswaterstaat en Het
Waterschapshuis. Het auteursrecht daarop ligt bij hen. Gebruik dit register zoals je de CSIR zelf zou
gebruiken.

## Wat erin zit

| Onderdeel | Inhoud |
|---|---|
| **Classificeren** | Zes gevolgcriteria (veiligheid, maatschappij, financieel, cascade, ecologie, imago), elk met vijf drempels; onderbouwing per criterium |
| **Niveau** | Functiebox, keten-analyse (CSIR §0.3), berekend weerstandsniveau |
| **Dashboard** | Live tellers: voortgang per onderdeel en per maatregelparagraaf, in en uit scope |
| **VSP Proceseisen** | 89 proces-controls, met de BIO-bron erbij |
| **VSE Systeemeisen** | 38 systeem-controls |
| **Maatregelen** | Alle 268 maatregelen met de niveaus N1–N4, de scope en de handleidingen per paragraaf |
| **Bijlagen** | CSR 1–24 plus A, B en C |
| **Uitdraai** | Het hele dossier op een rij, met de afwijkingen apart; afdrukbaar op A4 |

In cijfers: **127 controls** (89 + 38), **268 maatregelen** en **27 bijlagen**. Per weerstandsniveau
gelden 193, 198, 230 en 234 maatregelen; een maatregel kan op meerdere niveaus gelden.

## Hoe het rekent

- **Gevolgscores naar functiebox.** Het classificatieformulier neemt het afgeronde gemiddelde van de
  zes scores: 1=E, 2=D, 3=C, 4=B, 5=A. De browserversie toont daarnaast de strengste lezing (de
  hoogste score), omdat een gemiddelde een enkel zwaar gevolg kan wegmiddelen.
- **Functiebox naar niveau.** A=4, B=3, C=2, D=1, E=1. Dat niveau stuurt alle andere kolommen aan, dus
  één wijziging beweegt het hele register mee.
- **Ketenregel.** Bedient of beheert dit object andere objecten, dan gaat het niveau omhoog naar dat
  van het zwaarste bestuurde object. Dat is de regel uit §0.3 van de CSIR: het bedienende object gaat
  omhoog, niet het bediende.
- **Van toepassing naar scope.** De kolom *Aangeroepen §2* op de controlbladen koppelt een control aan
  een maatregelparagraaf. Staat minstens één aanroepende control op "Ja", dan komt die paragraaf in
  scope. De koppeling loopt ook via de bovenliggende paragraaf: §2.5 dekt §2.5.1 tot en met §2.5.3.
- **Twee percentages.** *% geïmplementeerd* telt alleen wat af is; *% afgehandeld* telt ook de
  onderbouwde afwijkingen mee, omdat comply-or-explain in de CSIR een geldige eindtoestand is.

De opmaak (kleuren in koppen en accenten) is vrij aan te passen aan de eigen huisstijl.

## Onder de motorkap

`csir.json` is de bron van de webversie: alle eisteksten, maatregelen, drempels en keuzelijsten, met
de sha256 van beide werkboeken erbij. Hij wordt gemaakt met `register/haal_bron.py` en een test
blokkeert als hij van de werkboeken afdrijft. De pagina zelf is één bestand met een
Content-Security-Policy die elke externe verbinding uitsluit; dat wordt in de tests nagerekend in
plaats van beloofd. Zie [register/LEESMIJ.md](register/LEESMIJ.md) voor bouwen, rekenen en testen.
