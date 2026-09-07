#!/usr/bin/env python3
"""Bouwt de CSIR Assessment Tool: een zelfstandig HTML-bestand uit csir.json en de bestanden in bron/.

Daarnaast bouwt het de downloadpagina van het werkboek (dist/werkboek/index.html): een kleine pagina
zonder script, met de twee werkboeken ernaast. Die staat er los van de tool, zodat je iemand een
adres kunt geven waar alleen het Excel-bestand staat.

Geen bundler, geen dependencies, geen externe verwijzingen. De bron wordt als JSON in dezelfde
scripttag gezet als de app, zodat er precies een script en een stylesheet is en het
Content-Security-Policy hun sha256-hash kan vastleggen: default-src 'none' voor de rest. Zo is de
offlinebelofte controleerbaar in plaats van beloofd.

Aanroep:
    python register/bouw.py                 # schrijft register/dist/index.html
    python register/bouw.py <doelmap>

Alleen standaardbibliotheek.
"""
from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import re
import shutil
import sys

HIER = pathlib.Path(__file__).resolve().parent
REPO = HIER.parent
BRON = HIER / "bron"

# De volgorde waarin handleidingen bij een paragraaf komen te staan: eerst waar je begint, dan de
# verdieping, dan het alternatief. Wie de lijst leest moet bovenaan kunnen instappen.
ROLVOLGORDE = {"fundering": 0, "verdieping": 1, "alternatief": 2}


def sha256_csp(inhoud: str) -> str:
    """De hashvorm die het Content-Security-Policy verwacht."""
    return "sha256-" + base64.b64encode(hashlib.sha256(inhoud.encode("utf-8")).digest()).decode()


def vingerafdruk(bron: dict) -> str:
    """Sha256 over de inhoud van de bron; zie register/haal_bron.py voor het waarom."""
    kern = {sleutel: bron[sleutel] for sleutel in
            ("controls", "maatregelen", "bijlagen", "classificatie", "functiebox_niveau")}
    ruw = json.dumps(kern, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(ruw.encode("utf-8")).hexdigest()


def handreiking() -> dict[str, dict]:
    """Per maatregelparagraaf de handleidingen uit de kennisbank, klein gehouden voor in de pagina.

    De CSIR zegt wat er moet gelden, de kennisbank zegt hoe je het inricht. Die handleidingen bestaan
    al; ze stonden alleen een paar klikken verderop. Alleen titel, rol en url gaan mee: de rest van
    de export is hier niet nodig en maakt het bestand groter dan de belofte "werkt offline" verdient.
    Staat er niets, dan gaat de reden mee, want een leeg vakje is geen uitnodiging.
    """
    koppeling = json.loads((HIER / "paragrafen-barrieres.json").read_text(encoding="utf-8"))
    export_pad = HIER / "handelingsperspectief.json"
    if not export_pad.is_file():
        sys.exit("register/handelingsperspectief.json ontbreekt. Draai eerst "
                 "'python register/haal_handelingsperspectief.py'. Zonder die kopie zou de pagina "
                 "stil zonder handreiking bouwen, en dat is erger dan een build die stukloopt.")
    export = json.loads(export_pad.read_text(encoding="utf-8"))

    per_barriere: dict[str, list[dict]] = {}
    for item in export["handleidingen"]:
        per_barriere.setdefault(item["barriere"], []).append(
            {"titel": item["titel"], "rol": item["rol"], "url": item["url"]})

    uit: dict[str, dict] = {}
    for regel in koppeling["regels"]:
        gevonden: dict[str, dict] = {}
        for barriere in regel["barrieres"]:
            for handleiding in per_barriere.get(barriere, []):
                gevonden[handleiding["url"]] = handleiding
        lijst = sorted(gevonden.values(),
                       key=lambda h: (ROLVOLGORDE.get(h["rol"], 9), h["titel"]))
        uit[regel["paragraaf"]] = {
            "barrieres": regel["barrieres"],
            "reden": regel["reden"],
            "handleidingen": lijst,
        }
    return uit


def bouw(doel: pathlib.Path) -> pathlib.Path:
    data = json.loads((REPO / "csir.json").read_text(encoding="utf-8"))
    data["vingerafdruk"] = vingerafdruk(data)
    data["handreiking"] = handreiking()

    ontbreekt = [p["id"] for p in data["paragrafen"] if p["id"] not in data["handreiking"]]
    if ontbreekt:
        sys.exit("paragrafen-barrieres.json mist een regel voor: " + ", ".join(ontbreekt) +
                 ". Elke paragraaf staat erin, ook als de lijst leeg is; stilte is nooit een "
                 "vergissing.")

    css = (BRON / "app.css").read_text(encoding="utf-8").strip()
    js = (BRON / "app.js").read_text(encoding="utf-8").strip()
    sjabloon = (BRON / "index.html").read_text(encoding="utf-8")

    # </script> in de data zou de scripttag vroegtijdig sluiten; JSON mag die slash escapen.
    json_bron = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    script = "window.__BRON__ = " + json_bron + ";\n" + js

    html = (sjabloon
            .replace("__CSS__", css)
            .replace("__SCRIPT__", script)
            .replace("__SCRIPT_HASH__", sha256_csp(script).removeprefix("sha256-"))
            .replace("__STYLE_HASH__", sha256_csp(css).removeprefix("sha256-")))

    for rest in ("__CSS__", "__SCRIPT__", "__SCRIPT_HASH__", "__STYLE_HASH__"):
        assert rest not in html, f"placeholder {rest} niet ingevuld"

    doel.mkdir(parents=True, exist_ok=True)
    uit = doel / "index.html"
    uit.write_bytes(html.encode("utf-8"))
    return uit


WERKBOEKEN = {
    "csir-control-register.xlsx": "werkboek_sha256",
    "objectclassificatie.xlsx": "classificatie_sha256",
}


def leesbare_grootte(bytes_: int) -> str:
    """Zoals een browser het toont: kB met een komma, want de pagina is Nederlands."""
    return f"{bytes_ / 1024:.0f} kB".replace(".", ",")


def bouw_werkboekpagina(doel: pathlib.Path) -> pathlib.Path:
    """Schrijft doel/werkboek/index.html met de twee werkboeken ernaast.

    De versie, de vingerafdrukken en de aantallen komen uit csir.json en niet uit de hand: dat bestand
    wordt door haal_bron.py uit de werkboeken zelf gehaald en --check blokkeert als het afdrijft. Zo
    kan de pagina niet stilletjes een oude sha256 blijven tonen.

    De werkboeken worden hier ook naartoe gekopieerd. In de Pages-build heeft de documentatiebuild dat
    al gedaan; deze kopie maakt het bouwscript los daarvan bruikbaar en houdt de downloadlink waar.
    """
    data = json.loads((REPO / "csir.json").read_text(encoding="utf-8"))
    bron = data["bron"]

    map_werkboek = doel / "werkboek"
    map_werkboek.mkdir(parents=True, exist_ok=True)
    for naam in WERKBOEKEN:
        shutil.copyfile(REPO / "werkboek" / naam, map_werkboek / naam)

    css = (BRON / "werkboek.css").read_text(encoding="utf-8").strip()
    html = (BRON / "werkboek.html").read_text(encoding="utf-8")

    vervangingen = {
        "__CSS__": css,
        "__STYLE_HASH__": sha256_csp(css).removeprefix("sha256-"),
        "__WERKBOEK_GROOTTE__": leesbare_grootte((map_werkboek / "csir-control-register.xlsx").stat().st_size),
        "__CLASSIFICATIE_GROOTTE__": leesbare_grootte((map_werkboek / "objectclassificatie.xlsx").stat().st_size),
        "__WERKBOEK_VERSIE__": bron["werkboek_versie"],
        "__WERKBOEK_SHA256__": bron["werkboek_sha256"],
        "__CLASSIFICATIE_SHA256__": bron["classificatie_sha256"],
        "__AANTAL_CONTROLS__": str(len(data["controls"])),
        "__AANTAL_MAATREGELEN__": str(len(data["maatregelen"])),
        "__AANTAL_BIJLAGEN__": str(len(data["bijlagen"])),
        "__AUTEURSRECHT__": bron["auteursrecht"],
    }
    for plaatshouder, waarde in vervangingen.items():
        html = html.replace(plaatshouder, waarde)

    achtergebleven = re.findall(r"__[A-Z_]+__", html)
    assert not achtergebleven, f"placeholder niet ingevuld: {', '.join(sorted(set(achtergebleven)))}"

    uit = map_werkboek / "index.html"
    uit.write_bytes(html.encode("utf-8"))
    return uit


if __name__ == "__main__":
    doelmap = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HIER / "dist"
    bestand = bouw(doelmap)
    kb = bestand.stat().st_size / 1024
    print(f"{bestand}: {kb:.0f} kB, zelfstandig en offline")
    print(f"{bouw_werkboekpagina(doelmap)}: de werkboeken met hun vingerafdruk ernaast")
