"""How the order reader treats the rehearsal corpus, Spanish against English.

Cycle 1 of the AI Advisor, quick win QW1 (faculty approval of 2026-09-27):
measure deterministically, on the existing rehearsal corpus only, how the
orders of a simulated encounter are read in English and in Spanish.

Each of the twenty rehearsal scripts (``tanda20`` and its English twin
``tanda20_en``) is played through the real page by
``tools_tanda20.rehearse`` -- Streamlit's in-process runner, a temporary
database, the provider key withheld and the encounter seed pinned -- and the
Management Trace the page stored is read back and compared, decision by
decision, between the two languages. No resident's encounter is read and no
model is called: the tool refuses to play if a provider key is visible, and
the report counts the model calls each stored encounter recorded.

What it can and cannot say. These scripts are the corpus the reader was tuned
on (docs/TANDA_20_ESCENARIOS.md, §2), and ``test_the_twenty_in_english.py``
keeps every order reading the same action types in both languages. The
result is therefore a baseline of the current behaviour on known text -- a
regression check with more detail than that test (doses, routes, holds, the
four categories, the reasoning the trace quotes, the trajectory) -- and not
an estimate of how often a real resident's order goes unread.

    python tools_order_reading.py --play es all --out DIR [--seed 3000]
    python tools_order_reading.py --play en all --out DIR [--seed 3000]
    python tools_order_reading.py --compare DIR
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REHEARSAL_ADMIN = ("ensayo_admin", "rehearsal-only-password")  # tools_tanda20._rehearse's own copy
SLOTS = ("problem_representation", "expected_effect", "reassessment_target", "management_priority",
         "contingency", "threshold")
CLARIFICATION_STATUSES = ("clarification_required", "not_executed")


# --- reading one stored encounter ---------------------------------------------------

def action_signature(action):
    """An action as the engine will execute it: its type and every parameter.

    The reader's actions carry only canonical values (types, agents, routes,
    destinations, numbers), so the same decision in either language has to
    produce the same signature.
    """
    items = []
    for key, value in sorted((action or {}).items()):
        if isinstance(value, float):
            value = round(value, 3)
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True, ensure_ascii=False)
        items.append((key, value))
    return tuple(items)


def _folded(text):
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def quoted_faithfully(slot_text, learner_input):
    """Whether a reasoning slot quotes what the learner wrote.

    Accents, case and punctuation aside, every word of a slot the trace
    records as ``stated`` should appear in the learner's own input.
    """
    words = _folded(slot_text).split()
    source = set(_folded(learner_input).split())
    return all(word in source for word in words)


def reads_as_an_order(text):
    """Whether a reasoning slot's text is itself an order the reader executes.

    A working model says what the learner thinks is going on; "inicio
    adrenalina en infusion a 0.1 mcg/kg/min" recorded there is an order put in
    the place of the reasoning.
    """
    from family_parser import parse_family_actions
    parsed = parse_family_actions(str(text or ""))
    return any(action.get("type") != "reassessment" for action in parsed["actions"])


def compact_entry(entry):
    """What the comparison needs from one Management Trace entry."""
    reasoning = entry.get("reasoning") or {}
    provenance = reasoning.get("slot_provenance") or {}
    gate = entry.get("reasoning_gate") or {}
    clarification = entry.get("clarification")
    return {
        "input": str(entry.get("learner_input") or ""),
        "status": entry.get("execution_status"),
        "mode": entry.get("interpretation_mode"),
        "minute": entry.get("decision_time_min"),
        "actions": sorted(action_signature(a) for a in entry.get("interpreted_action") or []
                          if isinstance(a, dict)),
        "future": sorted(str(item.get("type") if isinstance(item, dict) else item)
                         for item in entry.get("recognized_future_actions") or []),
        "future_details": sorted(f"{d.get('kind')}/{d.get('category')}"
                                 for d in entry.get("future_details") or [] if isinstance(d, dict)),
        "gate_required": gate.get("required"), "gate_status": gate.get("status"),
        "gate_missing": sorted(gate.get("missing") or []),
        "clarification": (json.dumps(clarification, ensure_ascii=False)[:300] if clarification else None),
        "slots": {slot: str(reasoning.get(slot)) for slot in SLOTS
                  if isinstance(reasoning.get(slot), str) and reasoning.get(slot).strip()},
        "provenance": {slot: provenance.get(slot) for slot in SLOTS if slot in provenance},
        "summaries": [str(s.get("label")) for s in entry.get("action_summaries") or [] if isinstance(s, dict)],
    }


def stored_encounter(database):
    """The rehearsal's stored attempt: its Management Trace and its model calls."""
    os.environ.setdefault("MRS_ALLOW_LOCAL_SQLITE", "true")
    from account_store import AccountStore
    store = AccountStore(f"sqlite:///{database}", allow_sqlite=True)
    admin = store.authenticate(*REHEARSAL_ADMIN)
    attempts = store.list_attempts(admin)
    if not attempts:
        return None
    record = store.get_attempt(admin, attempts[0]["id"])
    session = (record.get("payload") or {}).get("session") or {}
    ledger = session.get("ai_call_ledger")
    return {"status": record.get("status"),
            "trace": [compact_entry(e) for e in session.get("management_trace") or [] if isinstance(e, dict)],
            "ai_calls_spent": session.get("ai_calls_spent"),
            "ai_call_ledger_entries": len(ledger) if isinstance(ledger, (list, dict)) else ledger}


# --- playing -----------------------------------------------------------------------

def _numbers(spec):
    if spec == "all":
        return list(range(1, 21))
    chosen = []
    for part in spec.split(","):
        low, _, high = part.partition("-")
        chosen.extend(range(int(low), int(high or low) + 1))
    return chosen


def play(language, numbers, out, seed):
    if any(os.environ.get(name) for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")):
        raise SystemExit("A provider key is visible: this measurement must not be able to spend.")
    os.environ["MRS_OFFLINE_CASES"] = "1"
    import tools_tanda20
    by_number, _ = tools_tanda20._scripts(language)
    folder = Path(out) / language
    folder.mkdir(parents=True, exist_ok=True)
    for number in numbers:
        script = by_number[number]
        result = tools_tanda20.rehearse(script, folder / "db", seed=seed)
        stored = stored_encounter(folder / "db" / f"rehearsal-{number:02d}.sqlite3")
        (folder / f"{number:02d}.json").write_text(
            json.dumps({"result": result, "stored": stored}, indent=1, ensure_ascii=False, default=str),
            encoding="utf-8")
        print(f"{language} {number:>2} {script['case_id']:<30} stopped={result['stopped']} "
              f"holds={len(result.get('unanticipated_holds', []))} ({result['seconds']} s)", flush=True)


# --- comparing ----------------------------------------------------------------------

UNREAD = re.compile(r"not recognized|no se reconoci|could not read|no matching", re.I)


def _load(folder):
    return {int(path.stem): json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(Path(folder).glob("[0-9][0-9].json"))}


def language_counts(runs, scripts):
    """Per-language counts over every script played in that language."""
    counts = {"scripts": len(runs), "stopped": 0, "reviews_completed": 0, "order_steps": 0,
              "answer_steps": 0, "held_after_order": 0, "held_anticipated": 0,
              "unanticipated_holds": 0, "unread_messages": 0, "read_as_nothing": 0,
              "trace_entries": 0, "executed": 0, "not_executed": 0, "ai_mode_entries": 0,
              "gate_incomplete": 0, "slots_stated": 0, "slots_not_quoted": 0,
              "working_model_stated": 0, "working_model_is_an_order": 0, "ai_calls_spent": 0,
              "seconds": 0.0, "statuses": {}}
    examples = {"unread": [], "not_quoted": [], "unanticipated": [], "not_executed": [],
                "working_model_is_an_order": []}
    for number, run in runs.items():
        result, stored = run["result"], run.get("stored") or {}
        counts["seconds"] += float(result.get("seconds") or 0)
        counts["stopped"] += bool(result.get("stopped"))
        counts["reviews_completed"] += bool(result.get("review_completed"))
        steps = scripts[number]["steps"]
        played = [s for s in result.get("steps") or [] if s["step"][0] not in ("auto-complete", "auto-cancel")]
        for index, outcome in enumerate(played):
            kind = outcome["step"][0]
            if kind == "order":
                counts["order_steps"] += 1
                if outcome.get("held"):
                    counts["held_after_order"] += 1
                    position = next((i for i, s in enumerate(steps) if list(s) == outcome["step"]), None)
                    following = steps[position + 1][0] if position is not None and position + 1 < len(steps) else None
                    counts["held_anticipated"] += following in ("answer", "complete", "cancel")
            elif kind in ("answer", "complete"):
                counts["answer_steps"] += 1
            for said in outcome.get("said") or []:
                if UNREAD.search(said):
                    counts["unread_messages"] += 1
                    examples["unread"].append(f"#{number} {said[:220]}")
        counts["unanticipated_holds"] += len(result.get("unanticipated_holds") or [])
        examples["unanticipated"] += [f"#{number} step {h['step'] + 1}: {h.get('said')}"
                                      for h in result.get("unanticipated_holds") or []]
        counts["read_as_nothing"] += len(result.get("read_as_nothing") or [])
        counts["ai_calls_spent"] += int(stored.get("ai_calls_spent") or 0)
        for entry in stored.get("trace") or []:
            counts["trace_entries"] += 1
            counts["statuses"][entry["status"]] = counts["statuses"].get(entry["status"], 0) + 1
            counts["executed"] += entry["status"] == "executed"
            if entry["status"] in CLARIFICATION_STATUSES:
                counts["not_executed"] += 1
                examples["not_executed"].append(f"#{number} [{entry['status']}] {entry['input'][:160]}")
            counts["ai_mode_entries"] += entry["mode"] not in (None, "deterministic")
            counts["gate_incomplete"] += bool(entry["gate_required"]) and entry["gate_status"] != "complete"
            source = entry["input"]
            for slot, text in entry["slots"].items():
                if entry["provenance"].get(slot) != "stated":
                    continue
                counts["slots_stated"] += 1
                if not quoted_faithfully(text, source):
                    counts["slots_not_quoted"] += 1
                    examples["not_quoted"].append(f"#{number} {slot}: «{text[:120]}» ← «{source[:160]}»")
                if slot == "problem_representation":
                    counts["working_model_stated"] += 1
                    if reads_as_an_order(text):
                        counts["working_model_is_an_order"] += 1
                        examples["working_model_is_an_order"].append(
                            f"#{number} «{text[:120]}» ← «{source[:200]}»")
    counts["seconds"] = round(counts["seconds"], 1)
    return counts, examples


def paired_differences(spanish, english):
    """Decision by decision, where the two languages part."""
    rows = []
    for number in sorted(set(spanish) & set(english)):
        es = (spanish[number].get("stored") or {}).get("trace") or []
        en = (english[number].get("stored") or {}).get("trace") or []
        if len(es) != len(en):
            rows.append({"script": number, "decision": None, "what": "entries",
                         "es": len(es), "en": len(en)})
        for index, (a, b) in enumerate(zip(es, en)):
            for field in ("actions", "status", "minute", "future", "future_details", "gate_missing",
                          "provenance"):
                # Recognized future actions are kept in the learner's own words,
                # so the two languages can only be compared by how many there are.
                if field == "future" and len(a[field]) == len(b[field]):
                    continue
                if a[field] != b[field]:
                    rows.append({"script": number, "decision": index + 1, "what": field,
                                 "es": a[field], "en": b[field],
                                 "es_input": a["input"][:200], "en_input": b["input"][:200],
                                 "es_slots": a["slots"] if field == "provenance" else None,
                                 "en_slots": b["slots"] if field == "provenance" else None})
        es_close = spanish[number]["result"].get("sim_time_at_close")
        en_close = english[number]["result"].get("sim_time_at_close")
        if es_close != en_close:
            rows.append({"script": number, "decision": None, "what": "minute_at_close",
                         "es": es_close, "en": en_close})
    return rows


def compare(out):
    import tanda20
    import tanda20_en
    spanish, english = _load(Path(out) / "es"), _load(Path(out) / "en")
    report = {"es": language_counts(spanish, tanda20.BY_NUMBER),
              "en": language_counts(english, tanda20_en.BY_NUMBER),
              "paired_differences": paired_differences(spanish, english),
              "decisions_compared": sum(min(len((spanish[n].get("stored") or {}).get("trace") or []),
                                            len((english[n].get("stored") or {}).get("trace") or []))
                                        for n in set(spanish) & set(english))}
    (Path(out) / "comparison.json").write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str),
                                               encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--play", nargs=2, metavar=("es|en", "N|N-M|all"))
    parser.add_argument("--compare", metavar="DIR")
    parser.add_argument("--out", default="local-data/order-reading")
    parser.add_argument("--seed", type=int, default=3000)
    args = parser.parse_args(argv)
    if args.play:
        language, spec = args.play
        if language not in ("es", "en"):
            parser.error("--play takes es or en")
        play(language, _numbers(spec), args.out, args.seed)
        return 0
    if args.compare:
        report = compare(args.compare)
        print(json.dumps({key: report[key][0] if key in ("es", "en") else len(report[key])
                          if isinstance(report[key], list) else report[key] for key in report},
                         indent=1, ensure_ascii=False))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
