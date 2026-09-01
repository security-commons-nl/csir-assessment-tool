"""De rekenregels, los van de pagina.

Wat hier staat is de betekenis van het werkboek in Python. De browsertests leggen de pagina naast
deze uitkomsten; klopt het hier niet, dan klopt er niets.
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "register"))

import reken  # noqa: E402

TABEL = {"A": 4, "B": 3, "C": 2, "D": 1, "E": 1}
ERNST = [
    {"score": 1, "label": "Klein", "functiebox": "E", "niveau": 1},
    {"score": 2, "label": "Matig", "functiebox": "D", "niveau": 1},
    {"score": 3, "label": "Behoorlijk", "functiebox": "C", "niveau": 2},
    {"score": 4, "label": "Ernstig", "functiebox": "B", "niveau": 3},
    {"score": 5, "label": "Catastrofaal", "functiebox": "A", "niveau": 4},
]
CRITERIA = ("veiligheid", "maatschappij", "financieel", "cascade", "ecologie", "imago")

# De functies die de pagina onder dezelfde naam moet kennen. Helpers staan er bewust niet in: die
# mogen aan beide kanten anders heten zolang de uitkomst gelijk is.
SPIEGEL = ("rond_half_omhoog", "procent", "niveau_van_functiebox", "effectief_niveau",
           "klassificeer", "ouder", "geldt", "aanroepende_controls", "scope", "dashboard",
           "nieuw_dossier")


def scores(*waarden):
    return dict(zip(CRITERIA, waarden))


def instellingen(functiebox="", keten_actief=False, keten_boxen=()):
    return {
        "functiebox": functiebox,
        "keten": {
            "actief": keten_actief,
            "objecten": [{"naam": "", "functiebox": b} for b in keten_boxen],
        },
    }


def test_rond_half_omhoog():
    """Excel rondt 2,5 naar boven; Python round() rondt naar het even getal en zou 2 geven."""
    assert reken.rond_half_omhoog(2.5) == 3
    assert reken.rond_half_omhoog(3.5) == 4
    assert reken.rond_half_omhoog(2.49) == 2
    assert reken.rond_half_omhoog(1.0) == 1
    assert round(2.5) == 2  # de val waar deze functie omheen gaat


def test_functiebox_naar_niveau():
    for box, niveau in TABEL.items():
        assert reken.niveau_van_functiebox(box, TABEL) == {"niveau": niveau, "voorlopig": False}
    assert reken.niveau_van_functiebox("", TABEL) == {"niveau": 1, "voorlopig": True}
    assert reken.niveau_van_functiebox("Z", TABEL) == {"niveau": 1, "voorlopig": True}


def test_ketenregel():
    """Het bedienende object gaat omhoog naar het zwaarste object dat het aanstuurt."""
    assert reken.effectief_niveau(instellingen("B", True, ("A",)), TABEL)["effectief"] == 4
    assert reken.effectief_niveau(instellingen("B", False, ("A",)), TABEL)["effectief"] == 3
    assert reken.effectief_niveau(instellingen("B", True, ("", "")), TABEL)["effectief"] == 3
    leeg_met_keten = reken.effectief_niveau(instellingen("", True, ("C",)), TABEL)
    assert leeg_met_keten["effectief"] == 2
    assert leeg_met_keten["voorlopig"] is True
    assert leeg_met_keten["keten"] == 2


def test_classificatie_gemiddelde():
    uitkomst = reken.klassificeer(scores(2, 3, 1, 5, 2, 2), ERNST)
    assert uitkomst["som"] == 15
    assert uitkomst["gemiddelde"] == 3
    assert uitkomst["gemiddelde_functiebox"] == "C"
    assert uitkomst["gemiddelde_niveau"] == 2
    assert uitkomst["hoogste"] == 5
    assert uitkomst["hoogste_functiebox"] == "A"
    assert uitkomst["hoogste_niveau"] == 4


@pytest.mark.parametrize("waarden, gemiddelde, functiebox", [
    ((1, 1, 1, 1, 1, 1), 1, "E"),
    ((5, 5, 5, 5, 5, 5), 5, "A"),
    ((1, 1, 1, 1, 1, 2), 1, "E"),
    ((3, 3, 3, 3, 3, 4), 3, "C"),
    ((3, 3, 3, 3, 4, 4), 3, "C"),      # 20/6 = 3,33
    ((3, 3, 3, 4, 4, 4), 4, "B"),      # 21/6 = 3,5 en dat gaat omhoog
])
def test_classificatie_randen(waarden, gemiddelde, functiebox):
    uitkomst = reken.klassificeer(scores(*waarden), ERNST)
    assert uitkomst["gemiddelde"] == gemiddelde
    assert uitkomst["gemiddelde_functiebox"] == functiebox


def test_classificatie_incompleet():
    uitkomst = reken.klassificeer(scores(3, 3, 3, 3, 3, None), ERNST)
    assert uitkomst == {"compleet": False}


def test_ouder():
    assert reken.ouder("§2.5.1") == "§2.5"
    assert reken.ouder("§2.5") == "§2.5"
    assert reken.ouder("§2.10") == "§2.10"
    assert reken.ouder("§2.1.2") == "§2.1"


def test_aanroepende_controls_via_ouder():
    controls = [
        {"id": "A", "aangeroepen": ["§2.5"]},
        {"id": "B", "aangeroepen": ["§2.5.1"]},
        {"id": "C", "aangeroepen": []},
    ]
    for paragraaf in ("§2.5.1", "§2.5.2", "§2.5.3"):
        assert "A" in [c["id"] for c in reken.aanroepende_controls(paragraaf, controls)]
    assert [c["id"] for c in reken.aanroepende_controls("§2.5.2", controls)] == ["A"]
    assert sorted(c["id"] for c in reken.aanroepende_controls("§2.5.1", controls)) == ["A", "B"]


MINI_CONTROLS = [
    {"id": "VSP-1", "blad": "VSP", "aangeroepen": ["§2.2"]},
    {"id": "VSP-2", "blad": "VSP", "aangeroepen": ["§2.2"]},
]
MINI_MAATREGELEN = [
    {"code": "M1", "paragraaf": "§2.2", "niveaus": [1, 2]},
    {"code": "M2", "paragraaf": "§2.2", "niveaus": [4]},
    {"code": "M3", "paragraaf": "§2.9", "niveaus": [1, 2]},
]


def dossier_met(**vt):
    return {"controls": {sleutel: {"vt": waarde} for sleutel, waarde in vt.items()},
            "maatregelen": {}, "bijlagen": {}}


def test_scope_vier_uitkomsten():
    niet_op_niveau = reken.scope(MINI_MAATREGELEN[1], 2, MINI_CONTROLS, dossier_met())
    assert niet_op_niveau == "Niet op dit niveau"

    in_scope = dossier_met(**{"VSP-1": "Ja", "VSP-2": "Nee"})
    assert reken.scope(MINI_MAATREGELEN[0], 2, MINI_CONTROLS, in_scope) == "In scope"

    buiten = dossier_met(**{"VSP-1": "Nee", "VSP-2": "Nee"})
    assert reken.scope(MINI_MAATREGELEN[0], 2, MINI_CONTROLS, buiten) == "Buiten scope"

    half = dossier_met(**{"VSP-1": "Nee", "VSP-2": ""})
    assert reken.scope(MINI_MAATREGELEN[0], 2, MINI_CONTROLS, half) == "Nog te bepalen"

    # §2.9 wordt door geen enkele control aangeroepen: dan is er niets dat hem in of uit scope trekt.
    zonder = dossier_met(**{"VSP-1": "Ja", "VSP-2": "Ja"})
    assert reken.scope(MINI_MAATREGELEN[2], 2, MINI_CONTROLS, zonder) == "Nog te bepalen"


def test_scope_nvt_telt_niet_als_leeg():
    """N.v.t. is een gemaakte keuze, geen open vakje: de maatregel valt buiten scope."""
    dossier = dossier_met(**{"VSP-1": "N.v.t. (buiten scope)", "VSP-2": "Nee"})
    assert reken.scope(MINI_MAATREGELEN[0], 2, MINI_CONTROLS, dossier) == "Buiten scope"


def test_dashboard_nieuw_dossier(bron):
    dossier = reken.nieuw_dossier(bron)
    dossier["instellingen"]["functiebox"] = "C"        # niveau 2
    cijfers = reken.dashboard(bron, dossier)
    assert cijfers["niveau"] == 2
    assert cijfers["vsp"]["vt"] == 89
    assert cijfers["vse"]["vt"] == 38
    assert cijfers["maatregelen"]["vt"] == 198
    assert cijfers["totaal"]["vt"] == 325
    for sleutel in ("todo", "bezig", "klaar", "explain", "nvt"):
        assert cijfers["totaal"][sleutel] == 0
    assert cijfers["totaal"]["pct_impl"] == 0
    assert cijfers["controls"]["ja"] == 127
    assert cijfers["controls"]["leeg"] == 0
    assert cijfers["scope"]["in"] > 0
    op_niveau = sum(1 for m in bron["maatregelen"] if 2 in m["niveaus"])
    assert sum(cijfers["scope"].values()) == op_niveau


def test_dashboard_percentages():
    tellingen = {"todo": 2, "bezig": 0, "klaar": 4, "explain": 2, "nvt": 2}
    rij = reken._rij(10, tellingen)
    assert rij["pct_impl"] == pytest.approx(0.5)
    assert rij["pct_afgeh"] == pytest.approx(0.75)
    leeg = reken._rij(2, {"todo": 0, "bezig": 0, "klaar": 0, "explain": 0, "nvt": 2})
    assert leeg["pct_impl"] == 0 and leeg["pct_afgeh"] == 0


def test_dashboard_gelijk_aan_doorloop(bron, doorloop):
    """De ingevulde doorloop moet exact de vastgelegde tellers geven."""
    gevonden = reken.plat(reken.dashboard(bron, doorloop["dossier"]))
    for sleutel, verwacht in doorloop["verwacht"].items():
        assert sleutel in gevonden, f"teller {sleutel} bestaat niet meer"
        if isinstance(verwacht, float):
            assert gevonden[sleutel] == pytest.approx(verwacht), sleutel
        else:
            assert gevonden[sleutel] == verwacht, sleutel


def test_doorloop_raakt_elke_rekentak(bron, doorloop):
    """De fixture is alleen wat waard als hij ook echt door alle takken loopt."""
    dossier = doorloop["dossier"]
    cijfers = reken.dashboard(bron, dossier)
    assert cijfers["niveau"] == 3, "ketenregel moet het niveau boven de eigen functiebox tillen"
    assert cijfers["controls"]["nee"] >= 1
    assert cijfers["controls"]["nvt"] >= 1
    assert cijfers["controls"]["leeg"] >= 1
    assert cijfers["scope"]["in"] > 0 and cijfers["scope"]["buiten"] > 0
    for sleutel in ("todo", "bezig", "klaar", "explain", "nvt"):
        assert cijfers["totaal"][sleutel] > 0, f"geen enkele regel met status {sleutel}"
    buiten_niveau = [code for code, regel in dossier["maatregelen"].items()
                     if regel.get("status")
                     and 3 not in next(m["niveaus"] for m in bron["maatregelen"]
                                       if m["code"] == code)]
    assert buiten_niveau, "de fixture moet ook maatregelen buiten het niveau bevatten"


def test_reken_en_app_hebben_dezelfde_functies(app_js):
    """De pagina spiegelt dit bestand; anders lopen browser en referentie stil uit elkaar."""
    for naam in SPIEGEL:
        assert hasattr(reken, naam), f"reken.py mist {naam}"
        assert re.search(r"reken\." + naam + r"\s*=", app_js), f"app.js mist reken.{naam}"


def test_statuslijst_gelijk_aan_de_bron(bron):
    """De vertaaltabel status naar tellernaam moet de statussen van het werkboek gebruiken."""
    assert list(reken.STATUS_TELLER) == bron["keuzes"]["status"]
    assert list(reken.VAN_TOEPASSING) == bron["keuzes"]["van_toepassing"]
    assert list(reken.STATUSSEN) == bron["keuzes"]["status"]
