"""The debt register cites every correction that names a debt in its title (cycle 10, C10-00).

A correction whose title says "TD-31: ..." resolved (part of) TD-31, so a row of TD-31 in
docs/REGISTRO_DEUDA_TECNICA.md has to say so, with the correction's id. Without this, the
register kept TD-31 open after C-2026-09-29-13 had closed it.
"""
import re
from pathlib import Path

from corrections_registry import CORRECTIONS

REGISTER = Path(__file__).with_name("docs") / "REGISTRO_DEUDA_TECNICA.md"


def _rows():
    return [line for line in REGISTER.read_text(encoding="utf-8").splitlines() if line.startswith("|")]


def _rows_of(debt, rows):
    first_cell = re.compile(r"^\|[^|]*\b%s\b" % re.escape(debt))
    return [row for row in rows if first_cell.search(row)]


def test_every_correction_named_after_a_debt_is_cited_by_that_debt():
    rows = _rows()
    missing = []
    for correction in CORRECTIONS:
        for debt in sorted(set(re.findall(r"\bTD-\d+\b", correction["title"]))):
            if not any(correction["id"] in row for row in _rows_of(debt, rows)):
                missing.append((debt, correction["id"]))
    assert missing == []


def test_the_check_would_have_caught_the_stale_row():
    stale = ["| TD-31 | Motor | **Resto de TD-31:** sin cambio |",
             "| TD-31 (primera mitad) | La adrenalina IM sin dosis | C-2026-09-28-21 |"]
    assert not any("C-2026-09-29-13" in row for row in _rows_of("TD-31", stale))
    assert any("C-2026-09-29-13" in row for row in _rows_of("TD-31", _rows()))
