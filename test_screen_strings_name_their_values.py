"""A screen string's value is never named like the translator's own argument (2026-09-29).

``screen_language.t(text, **values)`` fills a string's named values after
translating it. A value named ``text`` collides with its first argument: since
cycle 8 the faculty page raised "t() got multiple values for argument 'text'" on
any objective with a TDFC YES row (its observable component and what stays
outside the encounter). The pilot smoke test found it (tools_pilot_smoke.py).
"""
import re
from pathlib import Path

import language
import screen_language

ROOT = Path(__file__).resolve().parent
_CALL = re.compile(r"""\b_?t\(\s*(["'])(?:(?!\1).)*\{text\}""")


def test_no_screen_string_names_a_value_text():
    for path in ROOT.glob("*.py"):
        if path.name.startswith("test_"):
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            assert not _CALL.search(line), f"{path.name}:{number}"


def test_the_opportunity_lines_read_in_both_languages():
    for code, component, outside in (("en", "Component this encounter can show: A", "Outside this encounter: B"),
                                     ("es", "Componente que este encuentro puede mostrar: A",
                                      "Fuera de este encuentro: B")):
        with language.presenting(code):
            assert screen_language.t("Component this encounter can show: {component}", component="A") == component
            assert screen_language.t("Outside this encounter: {outside}", outside="B") == outside
