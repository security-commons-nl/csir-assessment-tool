"""De gebouwde pagina: zit alles erin, en zit er niets in wat er niet hoort.

De belofte van deze pagina is dat hij offline werkt en dat de tekst die van de richtlijn is. Allebei
is hier controleerbaar gemaakt in plaats van beloofd: de CSP-hashes worden nagerekend op de inhoud,
en er mag geen enkele verwijzing naar buiten in staan behalve gewone links naar de commons.
"""
from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "register"))

import bouw as bouwer  # noqa: E402

TOEGESTANE_LINKS = ("https://security-commons-nl.github.io/", "https://github.com/security-commons-nl/")
CSP = ("default-src 'none'; script-src 'sha256-{script}'; style-src 'sha256-{stijl}'; "
       "img-src data:; form-action 'none'; base-uri 'none'")


def in_pagina(tekst: str, html: str) -> bool:
    """Staat deze tekst in de pagina, zoals het bouwscript hem daar zet?

    De bron gaat als JSON de scripttag in: regeleindes en aanhalingstekens worden geescaped, en
    '</' wordt '<\\/' zodat de scripttag niet vroegtijdig sluit.
    """
    geschreven = json.dumps(tekst, ensure_ascii=False)[1:-1].replace("</", "<\\/")
    return geschreven in html


def test_alle_eisen_en_maatregelen_staan_in_de_pagina(bron, html):
    for control in bron["controls"]:
        assert in_pagina(control["eis"], html), control["id"]
    for maatregel in bron["maatregelen"]:
        assert in_pagina(maatregel["tekst"], html), maatregel["code"]
    for bijlage in bron["bijlagen"]:
        assert in_pagina(bijlage["titel"], html), bijlage["id"]
    for criterium in bron["classificatie"]["criteria"]:
        for drempel in criterium["drempels"].values():
            assert in_pagina(drempel, html), criterium["id"]


def test_geen_enkele_externe_verwijzing(html):
    """Alles wat de pagina zou kunnen ophalen staat uit; alleen gewone links naar de commons blijven."""
    for patroon in ("src=", "@import", "url(", "fetch(", "XMLHttpRequest", "<iframe", "<link rel=\"stylesheet\""):
        assert patroon not in html, f"pagina bevat {patroon}"
    for adres in re.findall(r"https?://[^\"'<>\s)]+", html):
        assert adres.startswith(TOEGESTANE_LINKS), adres


def test_csp_sluit_alles_af_en_klopt_met_de_inhoud(html):
    script = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
    stijl = re.search(r"<style>(.*?)</style>", html, re.S).group(1)

    def hash_van(inhoud: str) -> str:
        return base64.b64encode(hashlib.sha256(inhoud.encode("utf-8")).digest()).decode()

    verwacht = CSP.format(script=hash_van(script), stijl=hash_van(stijl))
    gevonden = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', html).group(1)
    assert gevonden == verwacht


def test_precies_een_script_en_een_stylesheet(html):
    assert html.count("<script") == 1
    assert html.count("<style") == 1
    assert " style=" not in html, "inline stijlen kunnen niet onder deze CSP"


def test_de_app_bevat_geen_eigen_kopie_van_de_bron(bron, app_js):
    """De app kent geen enkele eis, code of maatregel uit zichzelf; alles komt uit de bron."""
    for maatregel in bron["maatregelen"]:
        assert not re.search(r"\b" + re.escape(maatregel["code"]) + r"\b", app_js), maatregel["code"]
    for control in bron["controls"]:
        assert control["id"] not in app_js, control["id"]
        assert control["eis"][:30] not in app_js, control["id"]
    for maatregel in bron["maatregelen"]:
        assert maatregel["tekst"][:30] not in app_js, maatregel["code"]
    assert "Rijkswaterstaat" not in app_js
    assert "Waterschapshuis" not in app_js


def test_statuslijst_in_de_app_komt_uit_de_bron(bron, app_js):
    """De app vertaalt statussen naar tellernamen; die statussen moeten van het werkboek zijn."""
    blok = re.search(r"var STATUS_TELLER = \{(.*?)\};", app_js, re.S).group(1)
    genoemd = re.findall(r"'([^']+)':", blok)
    assert genoemd == bron["keuzes"]["status"]


def test_pagina_werkt_zonder_javascript_uitleg(html, bron):
    noscript = re.search(r"<noscript>(.*?)</noscript>", html, re.S).group(1)
    assert "JavaScript" in noscript
    assert "csir.json" in noscript


def test_bouw_is_herhaalbaar(tmp_path):
    eerste = bouwer.bouw(tmp_path / "een").read_bytes()
    tweede = bouwer.bouw(tmp_path / "twee").read_bytes()
    assert eerste == tweede


def test_kruimelpad_wijst_terug_naar_de_hoofdpagina(html):
    kruimel = re.search(r'<nav class="kruimel".*?</nav>', html, re.S).group(0)
    assert 'href="https://security-commons-nl.github.io/"' in kruimel
    assert "Security Commons NL" in kruimel


def test_voetregel_bron_licentie_verbetering(bron, html):
    voet = re.search(r"<footer>(.*?)</footer>", html, re.S).group(1)
    assert "github.com/security-commons-nl/csir-control-register" in voet
    assert "EUPL-1.2" in voet
    assert "verbetering voorstellen" in voet
    assert in_pagina(bron["bron"]["auteursrecht"], html)


def test_handreiking_staat_erin(bron, html):
    """Per paragraaf de handleidingen, en waar er geen zijn de reden waarom niet."""
    koppeling = json.loads(
        (ROOT / "register" / "paragrafen-barrieres.json").read_text(encoding="utf-8"))
    export = json.loads(
        (ROOT / "register" / "handelingsperspectief.json").read_text(encoding="utf-8"))
    per_barriere = {}
    for item in export["handleidingen"]:
        per_barriere.setdefault(item["barriere"], []).append(item)

    met_handleiding = 0
    for regel in koppeling["regels"]:
        urls = {h["url"] for b in regel["barrieres"] for h in per_barriere.get(b, [])}
        assert in_pagina(regel["reden"], html), regel["paragraaf"]
        if urls:
            met_handleiding += 1
            for url in urls:
                assert url in html, f"{regel['paragraaf']}: {url}"
    assert met_handleiding >= 8, "de koppeling levert nauwelijks handleidingen op"


def test_vingerafdruk_in_de_pagina(bron, html):
    kern = {sleutel: bron[sleutel] for sleutel in
            ("controls", "maatregelen", "bijlagen", "classificatie", "functiebox_niveau")}
    ruw = json.dumps(kern, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    verwacht = hashlib.sha256(ruw.encode("utf-8")).hexdigest()
    assert f'"vingerafdruk":"{verwacht}"' in html


def test_pagina_is_niet_onnodig_groot(gebouwd: pathlib.Path):
    """Boven een megabyte is er iets dubbel opgenomen; de belofte 'sla hem op' moet waar blijven."""
    assert gebouwd.stat().st_size < 800 * 1024
