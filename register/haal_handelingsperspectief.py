#!/usr/bin/env python3
"""Haalt de koppeling barriere naar handleiding op uit de kennisbank.

De kennisbank is de bron: daar staat in de frontmatter van elk item bij welke barrieres het hoort en
met welke rol. `kennisbank/tools/build.py` exporteert dat naar `handelingsperspectief.json`. Dit
script kopieert die export hierheen, met een sha256 erbij zodat een verlopen kopie opvalt.

Waarom kopieren en niet lezen? De site van dit register wordt gebouwd zonder de kennisbank ernaast,
en een pagina die stilletjes zonder handreiking bouwt is erger dan een build die stukloopt. De kopie
staat in git, dus een verschil is zichtbaar in de review in plaats van pas op de site.

Gebruik:
    python register/haal_handelingsperspectief.py            (kopieren)
    python register/haal_handelingsperspectief.py --check    (alleen melden of de kopie klopt)

Alleen standaardbibliotheek; geen pip nodig.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

HIER = pathlib.Path(__file__).resolve().parent
REPO = HIER.parent
DOEL = HIER / "handelingsperspectief.json"
# Lokaal staat de kennisbank ernaast in de werkmap; in CI wordt hij binnen de workspace uitgecheckt
# als _kennisbank, want een checkout buiten $GITHUB_WORKSPACE wordt geweigerd.
KANDIDATEN = (
    REPO.parent / "kennisbank" / "handelingsperspectief.json",
    REPO / "_kennisbank" / "handelingsperspectief.json",
)

TOELICHTING = (
    "Kopie van de kennisbank-export: waar staat de handleiding bij een barriere. De CSIR zegt wat er "
    "moet gelden, dit zegt hoe je het inricht. Wat hier niet staat is geen omissie maar een "
    "openstaande schrijfopdracht in de kennisbank."
)


def bronbestand() -> pathlib.Path:
    for pad in KANDIDATEN:
        if pad.is_file():
            return pad
    plekken = "\n".join(f"  {p}" for p in KANDIDATEN)
    sys.exit(f"kennisbank-export niet gevonden. Gezocht op:\n{plekken}\n"
             "Zet de kennisbank-repo naast deze repo, of check hem uit als _kennisbank.")


def vingerafdruk(export: dict) -> str:
    """Sha256 over de inhoud, niet over de bytes.

    Git zet regeleindes op Windows om naar CRLF; hashen over de ruwe bytes zou de controle op de ene
    machine laten slagen en op de andere niet, terwijl er inhoudelijk niets verschilt.
    """
    kern = {"handleidingen": export["handleidingen"],
            "zonder_handleiding": export["zonder_handleiding"]}
    return hashlib.sha256(
        json.dumps(kern, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def bouw() -> dict:
    export = json.loads(bronbestand().read_text(encoding="utf-8"))
    for sleutel in ("handleidingen", "zonder_handleiding"):
        if sleutel not in export:
            sys.exit(f"kennisbank-export mist '{sleutel}'; is het formaat gewijzigd?")
    return {
        "versie": "gekopieerd uit de kennisbank door register/haal_handelingsperspectief.py; "
                  "wijzig de frontmatter van het kennisbankitem, niet dit bestand",
        "toelichting": TOELICHTING,
        "bron": {
            "kennisbank": "https://security-commons-nl.github.io/kennisbank/",
            "repo": "security-commons-nl/kennisbank",
            "bestand": "handelingsperspectief.json",
            "sha256": vingerafdruk(export),
        },
        "handleidingen": export["handleidingen"],
        "zonder_handleiding": export["zonder_handleiding"],
    }


def main(argv: list[str]) -> int:
    nieuw = bouw()
    if "--check" in argv:
        if not DOEL.is_file():
            print(f"{DOEL.name} ontbreekt; draai dit script zonder --check.")
            return 1
        oud = json.loads(DOEL.read_text(encoding="utf-8"))
        if oud.get("bron", {}).get("sha256") == nieuw["bron"]["sha256"]:
            print(f"{DOEL.name} loopt gelijk met de kennisbank "
                  f"({len(nieuw['handleidingen'])} handleidingen).")
            return 0
        print(f"{DOEL.name} loopt achter op de kennisbank.\n"
              f"  kopie:      {oud.get('bron', {}).get('sha256', '(geen)')[:16]}\n"
              f"  kennisbank: {nieuw['bron']['sha256'][:16]}\n"
              "Draai 'python register/haal_handelingsperspectief.py' om hem bij te werken.")
        return 1
    DOEL.write_bytes((json.dumps(nieuw, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print(f"{DOEL}: {len(nieuw['handleidingen'])} handleidingen, "
          f"{len(nieuw['zonder_handleiding'])} barrieres zonder.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
