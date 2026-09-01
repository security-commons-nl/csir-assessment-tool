# Bijdragen

Dit project hoort bij [security-commons-nl](https://github.com/security-commons-nl). De
organisatiebrede regels staan in
[CONTRIBUTING.md](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md) en het
[redactiestatuut](https://github.com/security-commons-nl/.github/blob/main/REDACTIESTATUUT.md).

## Wat helpt

- **Een tekst die afwijkt van jouw CSIR-exemplaar.** Meld de code van de control of maatregel en wat
  er bij jou staat. Tekstgetrouwheid is de kern van dit register; elke afwijking is een bug.
- **Een formule die in jouw Excel-versie anders uitpakt.** Noem de versie en het blad.
- **Een stap in de werkwijze die klemt.** De opzet is gegeneraliseerd; waar hij bij jou niet past,
  willen we dat weten.
- **De risicolaag.** Het register dekt bewust geen risicoanalyse. Heb je een werkbare manier om die
  eraan te koppelen, dan is dat de meest waardevolle bijdrage die er is.

Een [issue](../../issues/new/choose) of
[discussion](https://github.com/security-commons-nl/.github/discussions) is een volwaardige bijdrage.
"Maak maar een pull request" is nooit het antwoord.

## Voor wie een pull request doet

- Nederlands in documentatie en commitboodschappen.
- Eén onderwerp per commit, met de map als prefix.
- Geen persoonsnamen, organisatienamen of e-mailadressen in documentatie of in het werkboek
  (redactiestatuut A1 tot en met A3). Het werkboek is een sjabloon en blijft leeg.
- Wijzig je het werkboek, beschrijf dan in de PR wat er inhoudelijk verandert en tegen welke
  CSIR-versie je het hebt gecontroleerd.
- Wijzig je de site, draai dan `npm run build` en controleer `dist/index.html` in je browser.

## De pagina lokaal bouwen

```bash
npm install
npm run build
```

Dat schrijft `dist/index.html` met het werkboek ernaast. De pagina is self-contained: geen externe
fonts, geen externe scripts.
