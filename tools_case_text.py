"""The Spanish narrative of the bank cases, kept as data beside the English (faculty, 2026-09-26).

    python3 tools_case_text.py extract     # write or refresh case_text/es/<family>.json
    python3 tools_case_text.py check       # what is missing, stale or inconsistent

The faculty asked (2026-09-26) that whatever the app stores can be read in
English or Spanish, and that the narrative of the 31 bank cases be translated
and used only after their review. This file keeps that narrative as data:

* each family has ``case_text/es/<family>.json``, mapping variant -> a JSON
  pointer into the variant -> ``{"en": ..., "es": ...}``;
* the English is copied, not referenced: when a case's English changes, its
  translation shows as stale and is not used, rather than silently saying
  something the case no longer says;
* what is covered is what the resident reads of the case: the presentation,
  who gives the history, the history answers, the examination and the prose
  of the study reports. Numbers, doses and units are written as the English
  writes them (decision 16); a drug's name takes its Spanish generic spelling
  in the narrative (ibuprofeno, apixabán), a choice listed for the faculty's
  review in docs/TRADUCCION_CASOS.md.

Nothing here reaches a screen or a document until the faculty approves the
case's translation (``case_text``). ``extract`` never overwrites a Spanish
text: it adds new passages, and marks a passage whose English changed.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "case_text" / "es"
FIELDS = ("presentation", "history_source", "history", "examination", "investigations")
#: Leaves with no letters at all: numbers and symbols. A single word is a word
#: to translate ("Wife", "Daughter"), however short.
_NO_WORDS = re.compile(r"^[^A-Za-z]*$")


def _leaves(value, path):
    if isinstance(value, dict):
        for key, inner in value.items():
            yield from _leaves(inner, f"{path}/{key}")
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            yield from _leaves(inner, f"{path}/{index}")
    elif isinstance(value, str) and value.strip() and not _NO_WORDS.match(value.strip()):
        yield path, value


def passages(variant):
    """Every passage of the case the resident reads, by JSON pointer."""
    found = {}
    for field in FIELDS:
        if field in variant:
            for path, text in _leaves(variant[field], f"/{field}"):
                if field == "investigations" and "/result/" not in path + "/":
                    continue
                found[path] = text
    return found


def _families():
    from clinical_cases import FAMILIES
    return FAMILIES


def load(family):
    path = TARGET / f"{family}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def extract():
    TARGET.mkdir(parents=True, exist_ok=True)
    for family, spec in _families().items():
        current = load(family)
        out = {}
        for variant in spec["variants"]:
            kept = current.get(variant["id"], {})
            rows = {}
            for path, english in passages(variant).items():
                old = kept.get(path) or {}
                rows[path] = {"en": english, "es": old.get("es", "")}
                if old.get("en") and old["en"] != english:
                    # The case says something else now: the old Spanish is kept for
                    # the translator to see, and is not used until redone.
                    rows[path]["stale_es"] = old.get("es", "")
                    rows[path]["es"] = ""
            out[variant["id"]] = rows
        (TARGET / f"{family}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{family:20s} {len(out)} variants, {sum(len(r) for r in out.values())} passages")


def problems():
    """Missing, stale and inconsistent translations, as (family, variant, path, problem)."""
    found, spanish_of = [], {}
    for family, spec in _families().items():
        stored = load(family)
        for variant in spec["variants"]:
            rows = stored.get(variant["id"], {})
            for path, english in passages(variant).items():
                row = rows.get(path)
                if not row or not row.get("es"):
                    found.append((family, variant["id"], path, "missing"))
                elif row.get("en") != english:
                    found.append((family, variant["id"], path, "stale"))
                else:
                    spanish_of.setdefault(english, set()).add(row["es"])
    for english, versions in spanish_of.items():
        if len(versions) > 1:
            found.append(("*", "*", english[:80], f"{len(versions)} different translations"))
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("extract", "check"))
    args = parser.parse_args(argv)
    if args.command == "extract":
        extract()
        return 0
    rows = problems()
    counts = {}
    for row in rows:
        counts[row[3].split()[0] if row[0] != "*" else "inconsistent"] = counts.get(
            row[3].split()[0] if row[0] != "*" else "inconsistent", 0) + 1
    print(counts or "complete")
    for row in rows[:40]:
        print(" ", *row)
    return 1 if rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
