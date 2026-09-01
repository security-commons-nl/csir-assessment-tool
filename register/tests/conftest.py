"""Gedeelde fixtures: de bron, de gebouwde pagina en de ingevulde doorloop."""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "register"))

import bouw as bouwer  # noqa: E402


@pytest.fixture(scope="session")
def bron() -> dict:
    return json.loads((ROOT / "csir.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def gebouwd(tmp_path_factory) -> pathlib.Path:
    """De pagina een keer bouwen per testsessie; alle tests lezen dezelfde uitvoer."""
    return bouwer.bouw(tmp_path_factory.mktemp("dist"))


@pytest.fixture(scope="session")
def html(gebouwd: pathlib.Path) -> str:
    return gebouwd.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def app_js() -> str:
    return (ROOT / "register" / "bron" / "app.js").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def doorloop() -> dict:
    pad = pathlib.Path(__file__).parent / "fixtures" / "doorloop-2026-09.json"
    return json.loads(pad.read_text(encoding="utf-8"))
