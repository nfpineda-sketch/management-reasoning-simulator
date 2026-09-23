"""Measure what a model adds to the deterministic cue reader, and what it costs.

The patterns in ``reasoning_cues`` were measured on 2026-09-23 against fifteen
entries and what a reader would mark by hand in each: 28 of 30 findings, none
invented, the link judged the same way in 13 of 15. The two differences were a
link written across a sentence boundary.

One uncertainty remains and only a real request can settle it: does a model
catch what the patterns missed **without inventing what nobody wrote**? That is
what this measures, and nothing else. It sends one request per entry, against
frozen text, with no encounter, no physiology and no clock — so a run here can
never change a patient or a score.

The scope is hard-capped. ``--limit`` is required, every request is counted, and
the counter refuses the request after the cap. Nothing runs without ``--yes``.

    python tools_cue_recognition_runs.py --dry-run            # free, no request
    python tools_cue_recognition_runs.py --limit 6 --yes      # SIX paid requests
"""
import os
import sys

os.environ.setdefault("MRS_OFFLINE_CASES", "1")

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import reasoning_cues


#: (entry, findings a reader would mark, whether the link is expressed).
#: The first six are the informative ones: two where the patterns missed a
#: finding or a link, and four controls where inventing would be the failure.
CORPUS = [
    # --- where the patterns and a reader disagreed ---
    ("Paciente taquicardico, mal perfundido, frio y sudoroso. Impresiona shock cardiogenico.",
     ["taquicardico", "mal perfundido", "frio", "sudoroso"], True),
    ("PA 80/50, FC 130, sat 88%. Creo que es sepsis de foco urinario porque tiene orina turbia.",
     ["PA 80/50", "FC 130", "sat 88%", "orina turbia"], True),
    # --- controls: inventing here is the failure that matters ---
    ("Dar suero.", [], False),
    ("Creo que está en shock.", [], False),
    ("Espero que mejore la hipotension. Reevaluo la presion en 10 minutos.", [], False),
    ("Furosemida 40 mg EV. Reviso diuresis en 30 minutos.", [], False),
    # --- the rest of the corpus, for a fuller picture ---
    ("Está hipotenso y confuso; me preocupa que esté en shock.", ["hipotenso", "confuso"], True),
    ("La presión mejoró, pero sigue confuso.", ["presion", "confuso"], False),
    ("Tiene crepitantes bibasales e ingurgitacion yugular, lo que sugiere congestion.",
     ["crepitantes", "ingurgitacion yugular"], True),
    ("Sibilancias difusas con uso de musculatura accesoria. Crisis asmatica grave.",
     ["sibilancias", "uso de musculatura accesoria"], False),
    ("Dolor toracico opresivo con supradesnivel del ST en cara inferior.",
     ["dolor toracico", "supradesnivel"], False),
    ("HGT 35, comprometido de conciencia. Debe ser hipoglicemia.",
     ["HGT 35", "comprometido de conciencia"], False),
    ("Sin fiebre, sin crepitantes. No impresiona neumonia.", ["fiebre", "crepitantes"], False),
    ("The patient is hypotensive and confused, concerning for shock.",
     ["hypotensive", "confused"], True),
    ("Still tachycardic and the lactate is 4, so I suspect ongoing hypoperfusion.",
     ["tachycardic", "lactate is 4"], True),
]


def _key():
    import tomllib
    secrets = ROOT / ".streamlit" / "secrets.toml"
    if secrets.exists():
        return str(tomllib.loads(secrets.read_text(encoding="utf-8"))
                   .get("OPENAI_API_KEY", "")).strip()
    return ""


def _matches(finding, expected):
    a = reasoning_cues.key(finding)
    return any(a in reasoning_cues.key(want) or reasoning_cues.key(want) in a
               for want in expected)


def compare(entry, expected, linked_expected, rows, label):
    """What this reader caught, missed and invented on one entry."""
    caught = [row["finding"] for row in rows if _matches(row["finding"], expected)]
    invented = [row["finding"] for row in rows if not _matches(row["finding"], expected)]
    missed = [want for want in expected
              if not any(_matches(row["finding"], [want]) for row in rows)]
    return {"reader": label, "caught": caught, "missed": missed, "invented": invented,
            "linked": any(row.get("linked") for row in rows),
            "link_expected": linked_expected}


def run(limit, *, paid, model="gpt-5-mini", only=None):
    """``only`` re-reads named entries instead of the first ``limit`` of them."""
    entries = ([row for row in CORPUS if row[0] in set(only)][:limit] if only
               else CORPUS[:limit])
    sent = []
    original = None
    if paid:
        import httpx
        original = httpx.Client.send

        def counted(self, request, *args, **kwargs):
            if len(sent) >= limit:
                raise RuntimeError(
                    f"Request {len(sent) + 1} exceeds the authorised limit of {limit}; "
                    "it was refused.")
            sent.append(str(request.url))
            return original(self, request, *args, **kwargs)

        httpx.Client.send = counted

    started = datetime.now(timezone.utc)
    rows = []
    try:
        for entry, expected, linked_expected in entries:
            pattern_rows = reasoning_cues.cues(entry)
            record = {"entry": entry,
                      "reference": expected,
                      "pattern": compare(entry, expected, linked_expected,
                                         pattern_rows, "patterns")}
            if paid:
                from reasoning_recognition import ReasoningRecognitionError, recognize
                try:
                    found = recognize(entry, (), cues=True, api_key=_key(), model=model)
                    record["model"] = compare(entry, expected, linked_expected,
                                              list(found.cues), "model")
                    record["model"]["refused_by_the_check"] = found.cues_rejected
                except ReasoningRecognitionError as exc:
                    record["model"] = {"reader": "model", "error": str(exc)}
            rows.append(record)
    finally:
        if original is not None:
            import httpx
            httpx.Client.send = original

    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    return {"entries": len(entries), "requests": len(sent),
            "seconds": round(elapsed, 1), "model": model if paid else None,
            "rows": rows}


def summarise(result):
    lines = [f"entries {result['entries']} · requests {result['requests']} "
             f"· {result['seconds']}s"]
    for name in ("pattern", "model"):
        caught = missed = invented = 0
        links = 0
        seen = 0
        for row in result["rows"]:
            reader = row.get(name)
            if not reader or "error" in reader:
                continue
            seen += 1
            caught += len(reader["caught"])
            missed += len(reader["missed"])
            invented += len(reader["invented"])
            links += int(reader["linked"] == reader["link_expected"])
        if seen:
            lines.append(f"{name:8s} caught {caught} · missed {missed} "
                         f"· invented {invented} · link as a reader {links}/{seen}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int,
                        help="the maximum number of paid requests; required with --yes")
    parser.add_argument("--dry-run", action="store_true",
                        help="the deterministic reading only; no request is sent")
    parser.add_argument("--yes", action="store_true",
                        help="confirm that paid requests may be sent")
    parser.add_argument("--model", default="gpt-5-mini")
    parser.add_argument("--out", default="")
    parser.add_argument("--rerun", default="",
                        help="a previous --out file; re-reads only the entries that failed")
    args = parser.parse_args(argv)

    if not args.dry_run and not args.yes:
        parser.error("this sends paid requests; pass --dry-run, or --limit N --yes")
    if args.yes and not args.limit:
        parser.error("--yes needs --limit N, so the scope is a number and not a promise")

    limit = args.limit or len(CORPUS)
    only = None
    if args.rerun:
        previous = json.loads(Path(args.rerun).read_text(encoding="utf-8"))
        only = [row["entry"] for row in previous["rows"]
                if "error" in (row.get("model") or {})]
        print(f"re-reading {len(only)} entries that failed before")
    result = run(limit, paid=bool(args.yes), model=args.model, only=only)
    print(summarise(result))
    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
