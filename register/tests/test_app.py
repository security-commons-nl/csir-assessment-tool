"""De keten in een echte browser: klikken, rekenen, opslaan, terugladen, afdrukken.

Deze tests bewijzen wat een unit-test niet kan: dat de pagina werkt zoals iemand hem gebruikt, en
dat wat er op het scherm staat exact gelijk is aan register/reken.py. Loopt de app weg van de
referentie, dan valt dat hier om.

Overslaan als Playwright of de browser ontbreekt; CI installeert beide.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HIER = pathlib.Path(__file__).resolve().parent
ROOT = HIER.parent.parent
sys.path.insert(0, str(ROOT / "register"))

import bouw as bouwer  # noqa: E402
import reken  # noqa: E402

sync_api = pytest.importorskip("playwright.sync_api", reason="playwright niet beschikbaar")


@pytest.fixture(scope="module")
def bestand(tmp_path_factory) -> str:
    return bouwer.bouw(tmp_path_factory.mktemp("dist")).as_uri()


@pytest.fixture(scope="module")
def data() -> dict:
    return json.loads((ROOT / "csir.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as pw:
        try:
            gestart = pw.chromium.launch()
        except Exception as fout:                       # geen browser geinstalleerd
            pytest.skip(f"chromium niet beschikbaar: {fout}")
        yield gestart
        gestart.close()


@pytest.fixture
def pagina(browser, bestand):
    context = browser.new_context()
    blad = context.new_page()
    fouten: list[str] = []
    blad.on("pageerror", lambda e: fouten.append(str(e)))
    blad.on("console", lambda m: fouten.append(m.text) if m.type == "error" else None)
    blad.goto(bestand)
    yield blad
    assert not fouten, f"fouten in de browser: {fouten}"
    context.close()


def naar(blad, tab: str) -> None:
    blad.click(f"#tab-{tab}")


def zet_scores(blad, waarden) -> None:
    naar(blad, "classificatie")
    for criterium, score in zip(
            ("veiligheid", "maatschappij", "financieel", "cascade", "ecologie", "imago"), waarden):
        blad.select_option(f'[data-criterium="{criterium}"]', str(score))


def tellers(blad) -> dict[str, str]:
    return blad.evaluate(
        "() => Object.fromEntries(Array.from(document.querySelectorAll('[data-teller]'))"
        ".map(e => [e.getAttribute('data-teller'), e.textContent]))")


def verwacht_tekst(sleutel: str, waarde) -> str:
    if waarde is None:
        return "—"
    if sleutel.endswith(("pct", "pct_impl", "pct_afgeh")):
        return reken.procent(waarde)
    return str(waarde)


# ---------------------------------------------------------------- de schermen

def test_startscherm_toont_classificatie_en_tabs(pagina):
    assert pagina.is_visible("#scherm-classificatie")
    assert pagina.locator('[role="tab"]').count() == 8
    assert "niveau 1 (voorlopig)" in pagina.text_content("#dossier-status")


def test_classificatie_rekent_en_neemt_over(pagina):
    zet_scores(pagina, (2, 3, 1, 5, 2, 2))
    assert pagina.text_content("#klas-som") == "15"
    assert "3" in pagina.text_content("#klas-gemiddelde")
    assert pagina.text_content("#klas-functiebox") == "C"
    assert pagina.text_content("#klas-niveau") == "2"
    assert pagina.text_content("#klas-hoogste-functiebox") == "A"
    assert pagina.text_content("#klas-hoogste-niveau") == "4"

    pagina.click("#knop-classificatie-overnemen")
    assert pagina.is_visible("#scherm-instellingen")
    assert pagina.input_value("#obj-functiebox") == "C"
    assert pagina.text_content("#niveau-effectief") == "2"
    assert not pagina.is_visible("#waarschuwing-functiebox")
    assert "Overgenomen uit de classificatie" in pagina.text_content("#functiebox-herkomst")


def test_classificatie_incompleet_toont_geen_functiebox(pagina):
    naar(pagina, "classificatie")
    for criterium in ("veiligheid", "maatschappij", "financieel", "cascade", "ecologie"):
        pagina.select_option(f'[data-criterium="{criterium}"]', "3")
    assert pagina.text_content("#klas-functiebox") == "nog niet compleet"
    assert pagina.is_disabled("#knop-classificatie-overnemen")


def test_instellingen_functiebox_en_keten(pagina):
    naar(pagina, "instellingen")
    pagina.select_option("#obj-functiebox", "B")
    assert pagina.text_content("#niveau-effectief") == "3"

    pagina.select_option("#keten-actief", "ja")
    pagina.select_option('[data-keten-fb="1"]', "A")
    assert pagina.text_content("#niveau-keten") == "4"
    assert pagina.text_content("#niveau-effectief") == "4"
    assert pagina.text_content('[data-keten-niveau="1"]') == "4"

    pagina.select_option("#keten-actief", "nee")
    assert pagina.text_content("#niveau-effectief") == "3"


def test_lege_functiebox_waarschuwt(pagina):
    naar(pagina, "instellingen")
    assert pagina.is_visible("#waarschuwing-functiebox")
    assert pagina.text_content("#niveau-effectief") == "1"
    naar(pagina, "dashboard")
    assert pagina.is_visible("#waarschuwing-dashboard")


def test_maatregelenfilter_volgt_het_niveau(pagina, data):
    naar(pagina, "instellingen")
    pagina.select_option("#obj-functiebox", "C")
    naar(pagina, "maatregelen")
    assert pagina.text_content("#teller-maatregelen") == "198 van 268 zichtbaar"

    naar(pagina, "instellingen")
    pagina.select_option("#obj-functiebox", "A")
    naar(pagina, "maatregelen")
    assert pagina.text_content("#teller-maatregelen") == "234 van 268 zichtbaar"

    pagina.uncheck("#filter-geldt")
    assert pagina.text_content("#teller-maatregelen") == "268 van 268 zichtbaar"


def test_control_op_nee_zet_paragraaf_buiten_scope(pagina, data):
    """Een paragraaf met precies een aanroepende control laat de vier scope-uitkomsten zien."""
    keuze = None
    for paragraaf in data["paragrafen"]:
        betrokken = reken.aanroepende_controls(paragraaf["id"], data["controls"])
        if len(betrokken) != 1:
            continue
        maatregelen = [m for m in data["maatregelen"]
                       if m["paragraaf"] == paragraaf["id"] and 2 in m["niveaus"]]
        if maatregelen:
            keuze = (betrokken[0], maatregelen[0])
            break
    assert keuze, "geen paragraaf met precies een aanroepende control gevonden"
    control, maatregel = keuze

    naar(pagina, "instellingen")
    pagina.select_option("#obj-functiebox", "C")            # niveau 2
    blad = "vsp" if control["blad"] == "VSP" else "vse"
    cel = f'tr[data-maatregel="{maatregel["code"]}"] td.scope'

    naar(pagina, blad)
    pagina.select_option(f'tr[data-control="{control["id"]}"] select.vt', "Nee")
    naar(pagina, "maatregelen")
    assert pagina.text_content(cel).strip() == "Buiten scope"

    naar(pagina, blad)
    pagina.select_option(f'tr[data-control="{control["id"]}"] select.vt', "Ja")
    naar(pagina, "maatregelen")
    assert pagina.text_content(cel).strip() == "In scope"

    naar(pagina, blad)
    pagina.select_option(f'tr[data-control="{control["id"]}"] select.vt', "")
    naar(pagina, "maatregelen")
    assert pagina.text_content(cel).strip() == "Nog te bepalen"


# ---------------------------------------------------------------- het dossier

def test_dashboard_gelijk_aan_referentie(pagina, data, doorloop, tmp_path):
    pad = tmp_path / "doorloop.json"
    pad.write_text(json.dumps(doorloop["dossier"], ensure_ascii=False), encoding="utf-8")
    pagina.set_input_files("#bestand-laden", str(pad))
    pagina.wait_for_function(
        "() => document.querySelector('#dossier-status').textContent.includes('Gemaal Voorbeeld')")

    verwacht = reken.plat(reken.dashboard(data, doorloop["dossier"]))
    gevonden = tellers(pagina)
    for sleutel, waarde in verwacht.items():
        if sleutel == "niveau":
            continue
        assert sleutel in gevonden, f"teller {sleutel} staat niet op het scherm"
        assert gevonden[sleutel] == verwacht_tekst(sleutel, waarde), sleutel


def test_browser_geeft_dezelfde_uitslag_als_excel(pagina, doorloop, tmp_path):
    """De tellers op het scherm tegen wat in Excel is afgelezen."""
    if not doorloop.get("bevestigd_in_excel"):
        pytest.skip("de doorloop is nog niet in Excel afgelezen; zie fixtures/doorloop-2026-09.json")
    pad = tmp_path / "doorloop.json"
    pad.write_text(json.dumps(doorloop["dossier"], ensure_ascii=False), encoding="utf-8")
    pagina.set_input_files("#bestand-laden", str(pad))
    pagina.wait_for_function(
        "() => document.querySelector('#dossier-status').textContent.includes('Gemaal Voorbeeld')")
    gevonden = tellers(pagina)
    for sleutel, waarde in doorloop["verwacht"].items():
        if sleutel == "niveau":
            continue
        assert gevonden[sleutel] == verwacht_tekst(sleutel, waarde), sleutel


def test_opslaan_geeft_een_dossierbestand(pagina, tmp_path):
    naar(pagina, "classificatie")
    pagina.fill("#obj-naam", "Tunnel Voorbeeld")
    pagina.fill("#obj-organisatie", "Gemeente Voorbeeld")
    pagina.fill("#obj-situatie", "Tunnel met eigen bediening.")

    with pagina.expect_download() as bezig:
        pagina.click("#knop-opslaan")
    download = bezig.value
    assert re.match(r"^csir-dossier-.+-\d{4}-\d{2}-\d{2}\.json$", download.suggested_filename), \
        download.suggested_filename

    doel = tmp_path / "opgeslagen.json"
    download.save_as(str(doel))
    dossier = json.loads(doel.read_text(encoding="utf-8"))
    assert dossier["formaat"] == "csir-dossier"
    assert dossier["versie"] == 1
    assert dossier["object"]["naam"] == "Tunnel Voorbeeld"
    assert dossier["object"]["organisatie"] == "Gemeente Voorbeeld"
    assert dossier["object"]["situatie"] == "Tunnel met eigen bediening."


def test_laden_herstelt_de_stand(pagina, tmp_path):
    naar(pagina, "classificatie")
    pagina.fill("#obj-naam", "Sluis Voorbeeld")
    naar(pagina, "instellingen")
    pagina.select_option("#obj-functiebox", "B")

    with pagina.expect_download() as bezig:
        pagina.click("#knop-opslaan")
    doel = tmp_path / "dossier.json"
    bezig.value.save_as(str(doel))

    pagina.once("dialog", lambda d: d.accept())
    pagina.click("#knop-wissen")
    assert pagina.input_value("#obj-functiebox") == ""

    pagina.set_input_files("#bestand-laden", str(doel))
    pagina.wait_for_function(
        "() => document.querySelector('#obj-functiebox').value === 'B'")
    naar(pagina, "classificatie")
    assert pagina.input_value("#obj-naam") == "Sluis Voorbeeld"
    naar(pagina, "instellingen")
    assert pagina.text_content("#niveau-effectief") == "3"


def test_laden_weigert_verkeerd_bestand(pagina, tmp_path):
    naar(pagina, "classificatie")
    pagina.fill("#obj-naam", "Gemaal Blijft")
    rommel = tmp_path / "rommel.json"
    rommel.write_text('{"iets": "anders"}', encoding="utf-8")
    pagina.set_input_files("#bestand-laden", str(rommel))
    pagina.wait_for_function(
        "() => document.querySelector('#dossier-status').textContent.includes('geen dossier')")
    assert pagina.input_value("#obj-naam") == "Gemaal Blijft"


def test_laden_meldt_andere_bronversie(pagina, doorloop, tmp_path):
    afwijkend = json.loads(json.dumps(doorloop["dossier"]))
    afwijkend["bron_sha256"] = "0" * 64
    afwijkend["bron_versie"] = "2020-01"
    pad = tmp_path / "oud.json"
    pad.write_text(json.dumps(afwijkend, ensure_ascii=False), encoding="utf-8")
    pagina.set_input_files("#bestand-laden", str(pad))
    pagina.wait_for_function(
        "() => document.querySelector('#dossier-status').textContent.includes('bronversie')")
    naar(pagina, "classificatie")
    assert pagina.input_value("#obj-naam") == "Gemaal Voorbeeld"


def test_herladen_bewaart(pagina):
    naar(pagina, "classificatie")
    pagina.fill("#obj-naam", "Brug Voorbeeld")
    naar(pagina, "instellingen")
    pagina.select_option("#obj-functiebox", "D")
    pagina.reload()
    naar(pagina, "classificatie")
    assert pagina.input_value("#obj-naam") == "Brug Voorbeeld"
    naar(pagina, "instellingen")
    assert pagina.input_value("#obj-functiebox") == "D"


def test_wissen_leegt_de_opslag(pagina):
    naar(pagina, "classificatie")
    pagina.fill("#obj-naam", "Weg Voorbeeld")
    pagina.once("dialog", lambda d: d.accept())
    pagina.click("#knop-wissen")
    assert pagina.input_value("#obj-naam") == ""
    assert pagina.evaluate("() => window.localStorage.getItem('csir-dossier')") is None


def test_wissen_kan_worden_afgebroken(pagina):
    naar(pagina, "classificatie")
    pagina.fill("#obj-naam", "Niet wissen")
    pagina.once("dialog", lambda d: d.dismiss())
    pagina.click("#knop-wissen")
    assert pagina.input_value("#obj-naam") == "Niet wissen"


# ---------------------------------------------------------------- de uitdraai

def test_uitdraai_bevat_afwijkingen(pagina, data):
    naar(pagina, "classificatie")
    pagina.fill("#obj-naam", "Gemaal Afwijking")
    naar(pagina, "instellingen")
    pagina.select_option("#obj-functiebox", "A")

    control = data["controls"][0]
    naar(pagina, "vsp")
    pagina.select_option(f'tr[data-control="{control["id"]}"] select.status',
                         "Explain (afwijking)")
    pagina.fill(f'tr[data-control="{control["id"]}"] input.opmerking',
                "Leverancier levert dit pas bij de volgende release.")

    maatregel = next(m for m in data["maatregelen"] if 4 in m["niveaus"])
    naar(pagina, "maatregelen")
    pagina.select_option(f'tr[data-maatregel="{maatregel["code"]}"] select.status',
                         "Explain (afwijking)")
    pagina.fill(f'tr[data-maatregel="{maatregel["code"]}"] input.opmerking',
                "Bewust niet ingevoerd, risico geaccepteerd.")

    naar(pagina, "uitdraai")
    tekst = pagina.text_content("#uitdraai-inhoud")
    assert "Gemaal Afwijking" in tekst
    assert "Afwijkingen" in pagina.text_content("#scherm-uitdraai")
    assert control["id"] in tekst
    assert maatregel["code"] in tekst
    assert "Leverancier levert dit pas bij de volgende release." in tekst
    assert "Bewust niet ingevoerd, risico geaccepteerd." in tekst


def test_uitdraai_toont_classificatie_en_keten(pagina):
    zet_scores(pagina, (3, 4, 2, 5, 1, 3))
    pagina.fill("#obj-naam", "Gemaal Keten")
    pagina.click("#knop-classificatie-overnemen")
    pagina.select_option("#keten-actief", "ja")
    pagina.select_option('[data-keten-fb="1"]', "A")
    pagina.fill('[data-keten-naam="1"]', "Centrale post")

    naar(pagina, "uitdraai")
    tekst = pagina.text_content("#uitdraai-inhoud")
    assert "Centrale post" in tekst
    assert "Effectief weerstandsniveau" in tekst
    assert "Strengste lezing" in tekst


def test_afdrukken_toont_uitdraai(pagina):
    naar(pagina, "maatregelen")
    pagina.emulate_media(media="print")
    assert pagina.is_visible("#scherm-uitdraai")
    assert not pagina.is_visible("#scherm-maatregelen")
    assert not pagina.is_visible("#tab-maatregelen")
    pagina.emulate_media(media="screen")


# ---------------------------------------------------------------- handreiking

def test_handreiking_zichtbaar_bij_paragraaf(pagina):
    naar(pagina, "maatregelen")
    pagina.uncheck("#filter-geldt")
    links = pagina.eval_on_selector_all(
        '[data-handreiking="§2.2"] a', "els => els.map(e => e.href)")
    assert links, "§2.2 hoort handleidingen uit de kennisbank te tonen"
    assert all(u.startswith("https://security-commons-nl.github.io/kennisbank/") for u in links)
    assert "Nog geen handleiding" in pagina.text_content('[data-handreiking="§2.4.2"]')


def test_sjabloon_eis_vult_object_en_niveau_in(pagina, data):
    """De twee VSE-eisen met een plaatshouder tonen de objectnaam en het actuele niveau."""
    sjabloon = next(c for c in data["controls"] if c["sjabloon"])
    naar(pagina, "classificatie")
    pagina.fill("#obj-naam", "Sluis Sjabloon")
    naar(pagina, "instellingen")
    pagina.select_option("#obj-functiebox", "B")           # niveau 3
    naar(pagina, "vse")
    tekst = pagina.text_content(f'[data-eis="{sjabloon["id"]}"]')
    assert "Sluis Sjabloon" in tekst
    assert "{object}" not in tekst and "{niveau}" not in tekst
    assert tekst.rstrip().endswith("3")
