#!/usr/bin/env python3
"""De rekenregels van het register, los van de pagina.

Dit is de referentie: `register/bron/app.js` bevat dezelfde functies onder dezelfde namen in het
object `reken`, en de browsertests vergelijken de uitkomst op het scherm met de uitkomst hier. Loopt
de pagina weg van dit bestand, dan valt dat om.

De regels zijn woordelijk de formules uit het werkboek. Waar Excel iets doet wat je niet zou
verzinnen (het afgeronde gemiddelde bij de classificatie, een paragraaf die door geen enkele control
wordt aangeroepen en daardoor "Nog te bepalen" blijft), volgt dit bestand Excel. Een rekenregel
veranderen is een besluit van de opsteller van het werkboek, niet van de bouwer.

Alleen standaardbibliotheek.
"""
from __future__ import annotations

import math

VAN_TOEPASSING = ("Ja", "Nee", "N.v.t. (buiten scope)")
STATUSSEN = ("Nog te doen", "In uitvoering", "Geïmplementeerd", "Explain (afwijking)", "N.v.t.")

# De sleutels waaronder het dashboard zijn tellers aflevert; de pagina gebruikt dezelfde namen in
# data-teller, zodat de browsertest ze een op een kan vergelijken.
TELLERS = ("vt", "todo", "bezig", "klaar", "explain", "nvt", "pct_impl", "pct_afgeh")

STATUS_TELLER = {
    "Nog te doen": "todo",
    "In uitvoering": "bezig",
    "Geïmplementeerd": "klaar",
    "Explain (afwijking)": "explain",
    "N.v.t.": "nvt",
}


def rond_half_omhoog(getal: float) -> int:
    """Afronden zoals Excel ROUND: 2,5 wordt 3.

    Python rondt met round() naar het even getal (round(2.5) is 2) en dat wijkt af van het werkboek.
    JavaScript doet Math.round(2.5) wel goed maar Math.round(-2.5) niet; met floor(x + 0.5) doen
    beide kanten hetzelfde. Negatieve scores komen hier niet voor, maar de regel blijft zo eenduidig.
    """
    return math.floor(getal + 0.5)


def procent(deel: float) -> str:
    """Een verhouding als heel percentage, met dezelfde afronding als de rest.

    Ook hier telt de val: 1 van de 8 is 12,5 procent, en dat moet aan beide kanten 13 worden.
    Met round() zou Python 12 tonen en de browser 13, en dan lijkt de pagina te rekenen terwijl er
    alleen verschillend wordt afgerond.
    """
    return f"{rond_half_omhoog(deel * 100)}%"


def niveau_van_functiebox(functiebox: str, tabel: dict[str, int]) -> dict:
    """Functiebox A t/m E naar weerstandsniveau.

    Zolang er geen functiebox is gekozen rekent het werkboek met niveau 1, maar het zegt er ook bij
    dat dat een voorlopige waarde is en geen vastgesteld niveau. Dat onderscheid houden we vast.
    """
    if functiebox in tabel:
        return {"niveau": tabel[functiebox], "voorlopig": False}
    return {"niveau": 1, "voorlopig": True}


def effectief_niveau(instellingen: dict, tabel: dict[str, int]) -> dict:
    """Het niveau waarop dit object wordt afgerekend, inclusief de ketenregel (CSIR §0.3).

    Bedient of beheert dit object andere objecten, dan gaat dit object omhoog naar het niveau van het
    zwaarste object dat het aanstuurt. Het bedienende object gaat omhoog, niet het bediende.
    """
    eigen = niveau_van_functiebox(instellingen.get("functiebox", ""), tabel)
    keten_niveau = 0
    keten = instellingen.get("keten") or {}
    if keten.get("actief"):
        for object_ in keten.get("objecten") or []:
            box = (object_ or {}).get("functiebox", "")
            if box in tabel:
                keten_niveau = max(keten_niveau, tabel[box])
    return {
        "eigen": eigen["niveau"],
        "keten": keten_niveau,
        "effectief": max(eigen["niveau"], keten_niveau),
        "voorlopig": eigen["voorlopig"],
    }


def klassificeer(scores: dict, ernst: list[dict]) -> dict:
    """De zes gevolgscores naar een functiebox.

    Het formulier neemt het afgeronde gemiddelde. Dat is een keuze met een prijs: een 5 op cascade
    tussen vijf enen zakt weg naar box D. Daarom rekenen we de strengste lezing (de hoogste score)
    ernaast uit en toont de pagina die erbij; welke van de twee de richtlijn bedoelt is een vraag aan
    de opsteller.
    """
    per_score = {rij["score"]: rij for rij in ernst}
    waarden = [scores.get(sleutel) for sleutel in scores]
    if not waarden or any(w is None for w in waarden):
        return {"compleet": False}

    som = sum(waarden)
    gemiddelde = rond_half_omhoog(som / len(waarden))
    hoogste = max(waarden)
    return {
        "compleet": True,
        "som": som,
        "gemiddelde": gemiddelde,
        "hoogste": hoogste,
        "gemiddelde_label": per_score[gemiddelde]["label"],
        "gemiddelde_functiebox": per_score[gemiddelde]["functiebox"],
        "gemiddelde_niveau": per_score[gemiddelde]["niveau"],
        "hoogste_label": per_score[hoogste]["label"],
        "hoogste_functiebox": per_score[hoogste]["functiebox"],
        "hoogste_niveau": per_score[hoogste]["niveau"],
    }


def ouder(paragraaf: str) -> str:
    """§2.5.1 hoort bij §2.5; §2.2 is zijn eigen ouder. Letterlijk hulpkolom Q van het werkboek."""
    if paragraaf.count(".") >= 2:
        eerste = paragraaf.index(".")
        tweede = paragraaf.index(".", eerste + 1)
        return paragraaf[:tweede]
    return paragraaf


def geldt(maatregel: dict, niveau: int) -> bool:
    """Geldt deze maatregel op dit weerstandsniveau?"""
    return niveau in maatregel["niveaus"]


def aanroepende_controls(paragraaf: str, controls: list[dict]) -> list[dict]:
    """De controls die deze maatregelparagraaf aanroepen, rechtstreeks of via de bovenliggende.

    Een control die §2.5 aanroept, raakt daarmee §2.5.1, §2.5.2 en §2.5.3. Het werkboek telt de
    directe en de bovenliggende treffers apart op; voor de uitkomst telt alleen of er nul of meer
    dan nul zijn, dus een lijst zonder dubbelingen geeft hetzelfde antwoord.
    """
    boven = ouder(paragraaf)
    return [c for c in controls
            if paragraaf in c["aangeroepen"] or boven in c["aangeroepen"]]


def van_toepassing(dossier: dict, soort: str, sleutel: str) -> str:
    """De van-toepassing-waarde uit het dossier; ontbreekt de regel, dan is hij leeg."""
    return ((dossier.get(soort) or {}).get(sleutel) or {}).get("vt", "") or ""


def status_van(dossier: dict, soort: str, sleutel: str) -> str:
    """De status uit het dossier; ontbreekt de regel, dan is hij leeg."""
    return ((dossier.get(soort) or {}).get(sleutel) or {}).get("status", "") or ""


def scope(maatregel: dict, niveau: int, controls: list[dict], dossier: dict) -> str:
    """Staat deze maatregel in scope voor dit object?

    Vier uitkomsten, in deze volgorde:
      - geldt hij niet op dit niveau, dan is hij "Niet op dit niveau" en verder niet interessant;
      - is minstens een aanroepende control van toepassing verklaard, dan "In scope";
      - zijn er aanroepende controls en is er geen enkele meer leeg, dan "Buiten scope";
      - anders "Nog te bepalen".
    Een paragraaf die door geen enkele control wordt aangeroepen blijft dus "Nog te bepalen". Dat is
    Excel-gedrag: zonder aanroep is er niets dat de maatregel in of uit scope trekt.
    """
    if not geldt(maatregel, niveau):
        return "Niet op dit niveau"
    betrokken = aanroepende_controls(maatregel["paragraaf"], controls)
    ja = sum(1 for c in betrokken if van_toepassing(dossier, "controls", c["id"]) == "Ja")
    leeg = sum(1 for c in betrokken if not van_toepassing(dossier, "controls", c["id"]))
    if ja > 0:
        return "In scope"
    if betrokken and leeg == 0:
        return "Buiten scope"
    return "Nog te bepalen"


def _rij(vt: int, tellingen: dict[str, int]) -> dict:
    """Een dashboardrij: de tellingen plus de twee percentages.

    Het werkboek rekent percentages over wat van toepassing is minus wat op N.v.t. staat: een regel
    die niet van toepassing is, mag de teller niet omlaag trekken. En er zijn er twee, omdat
    comply-or-explain in de CSIR een geldige eindtoestand is: geimplementeerd telt altijd mee,
    afgehandeld telt de onderbouwde afwijkingen erbij.
    """
    noemer = vt - tellingen["nvt"]
    rij = {"vt": vt}
    rij.update(tellingen)
    rij["pct_impl"] = 0.0 if noemer <= 0 else tellingen["klaar"] / noemer
    rij["pct_afgeh"] = 0.0 if noemer <= 0 else (tellingen["klaar"] + tellingen["explain"]) / noemer
    return rij


def _leeg() -> dict[str, int]:
    return {"todo": 0, "bezig": 0, "klaar": 0, "explain": 0, "nvt": 0}


def dashboard(bron: dict, dossier: dict) -> dict:
    """Alle tellers van het dashboard, met dezelfde namen als de pagina gebruikt."""
    niveau = effectief_niveau(dossier.get("instellingen") or {}, bron["functiebox_niveau"])["effectief"]
    controls = bron["controls"]
    uit: dict[str, object] = {"niveau": niveau}

    som_vt = 0
    som_tellingen = _leeg()

    for blad in ("VSP", "VSE"):
        rijen = [c for c in controls if c["blad"] == blad]
        tellingen = _leeg()
        vt = 0
        for control in rijen:
            if van_toepassing(dossier, "controls", control["id"]) != "Ja":
                continue
            vt += 1
            sleutel = STATUS_TELLER.get(status_van(dossier, "controls", control["id"]))
            if sleutel:
                tellingen[sleutel] += 1
        uit[blad.lower()] = _rij(vt, tellingen)
        som_vt += vt
        for sleutel in som_tellingen:
            som_tellingen[sleutel] += tellingen[sleutel]

    op_niveau = [m for m in bron["maatregelen"] if geldt(m, niveau)]
    tellingen = _leeg()
    for maatregel in op_niveau:
        sleutel = STATUS_TELLER.get(status_van(dossier, "maatregelen", maatregel["code"]))
        if sleutel:
            tellingen[sleutel] += 1
    uit["maatregelen"] = _rij(len(op_niveau), tellingen)
    som_vt += len(op_niveau)
    for sleutel in som_tellingen:
        som_tellingen[sleutel] += tellingen[sleutel]

    uit["totaal"] = _rij(som_vt, som_tellingen)

    uit["controls"] = {
        "ja": sum(1 for c in controls if van_toepassing(dossier, "controls", c["id"]) == "Ja"),
        "nee": sum(1 for c in controls if van_toepassing(dossier, "controls", c["id"]) == "Nee"),
        "nvt": sum(1 for c in controls
                   if van_toepassing(dossier, "controls", c["id"]) == "N.v.t. (buiten scope)"),
        "leeg": sum(1 for c in controls if not van_toepassing(dossier, "controls", c["id"])),
    }

    scopes = [scope(m, niveau, controls, dossier) for m in bron["maatregelen"]]
    uit["scope"] = {
        "in": scopes.count("In scope"),
        "buiten": scopes.count("Buiten scope"),
        "nog": scopes.count("Nog te bepalen"),
    }

    per_paragraaf = {}
    for paragraaf in bron["paragrafen"]:
        rijen = [m for m in bron["maatregelen"]
                 if m["paragraaf"] == paragraaf["id"] and geldt(m, niveau)]
        klaar = sum(1 for m in rijen
                    if status_van(dossier, "maatregelen", m["code"]) == "Geïmplementeerd")
        per_paragraaf[paragraaf["id"]] = {
            "op_niveau": len(rijen),
            "geimpl": klaar,
            "pct": None if not rijen else klaar / len(rijen),
        }
    uit["paragraaf"] = per_paragraaf
    return uit


def plat(waarden: dict, voorvoegsel: str = "") -> dict[str, object]:
    """Het dashboard als platte sleutels ('vsp.klaar', 'paragraaf.§2.2.pct'), zoals data-teller."""
    uit: dict[str, object] = {}
    for sleutel, waarde in waarden.items():
        pad = f"{voorvoegsel}{sleutel}"
        if isinstance(waarde, dict):
            uit.update(plat(waarde, f"{pad}."))
        else:
            uit[pad] = waarde
    return uit


def nieuw_dossier(bron: dict) -> dict:
    """Een leeg dossier met alle controls voorgevuld op 'Ja', zoals het werkboek ze aanlevert."""
    return {
        "formaat": "csir-dossier",
        "versie": 1,
        "bron_versie": bron["versie"],
        "object": {sleutel: "" for sleutel in
                   ("naam", "organisatie", "proces", "locatie", "hoofdtaak", "situatie",
                    "ingevuld_door", "team", "datum",
                    # De terugverwijzing naar procescheck: welk dossier en welk proces dit object
                    # draagt. Los gekoppeld, want de ene tool hoort niet stuk te gaan van de andere.
                    "procescheck_dossier", "procescheck_proces")},
        "classificatie": {
            "scores": {c["id"]: None for c in bron["classificatie"]["criteria"]},
            "onderbouwing": {c["id"]: "" for c in bron["classificatie"]["criteria"]},
            "opmerkingen": "",
        },
        "instellingen": {
            "functiebox": "",
            "functiebox_bron": "",
            "keten": {"actief": False,
                      "objecten": [{"naam": "", "functiebox": ""} for _ in range(3)],
                      "bevestigd_door": "", "datum": ""},
        },
        "controls": {c["id"]: {"vt": "Ja", "status": "", "bewijs": "",
                               "verantwoordelijke": "", "opmerking": ""} for c in bron["controls"]},
        "maatregelen": {},
        "bijlagen": {},
    }
