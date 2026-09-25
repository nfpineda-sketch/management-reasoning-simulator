"""Which encounters need their documents regenerated, a new analysis, or a new run.

Faculty decisions of 2026-09-25, closing paragraph: the batch is not repeated
automatically. Once the decisions are applied, each encounter is classified:

* **re-run** -- its clinical trajectory changes: what was executed and with
  what, when, the patient's state after each decision, how and when it closed.
  The same inputs no longer produce the same encounter, and only a new run
  shows what happens now.
* **new analysis** -- the same trajectory, but what an analysis reads from the
  saved record changed: the rubric proposal, the faculty brief or the learner's
  Management Trace analysis would be sent something different by the current
  code (an order now read as indicated rather than unrecognised, a record check
  that now reads a deferral, how the encounter closed...). The saved analyses
  were made from the older reading.
* **documents only** -- the same trajectory and the same readings; only how the
  documents say it changed. They are regenerated from the saved data, at no
  cost and with no new request.

The comparison that decides a re-run needs the same inputs played twice:
``--compare BEFORE AFTER`` takes the saved records and their replay (for the
twenty scripts, the rehearsal before the decisions and the rehearsal after).
The comparison that decides a new analysis reads the *saved* record twice, with
the code that produced it (the revision the record names, or ``--since``) and
with the current code: a re-analysis is made on the saved record, never on a
replay.

``--reread RECORD`` is the triage for an encounter that cannot be replayed here
(a resident's, or one whose inputs cannot be played again): each recorded
decision is re-read by the current reader, and a decision it would now execute
differently is named as a re-run candidate. It is a re-reading, not a replay,
and says so; the faculty decides.

Nothing here writes to a database, sends a request or changes a record.

    python tools_reclassify.py --compare before/db after/db
    python tools_reclassify.py --reread saved.record.json --since 5c2d1c6
    python tools_reclassify.py --database "$MRS_DATABASE_URL" --account <username> --since <revision>
"""
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("MRS_OFFLINE_CASES", "1")

import argparse
import json
import sqlite3
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RERUN, REANALYSE, DOCUMENTS = "rerun", "reanalyse", "documents"
LABELS = {RERUN: "re-run: the clinical trajectory changes",
          REANALYSE: "new analysis: what an analysis reads changed",
          DOCUMENTS: "documents only: regenerate from the saved data"}
LABELS_ES = {RERUN: "volver a ejecutar: cambia la trayectoria clínica",
             REANALYSE: "nuevo análisis: cambia lo que lee un análisis",
             DOCUMENTS: "sólo regenerar documentos desde los datos guardados"}

# How an order is said, not what was done: labels, the arithmetic shown beside
# a dose, whether a rate was written or the simulator's.
PRESENTATION = frozenset({"label", "pathway_note", "dose_basis", "rate_basis", "weight_kg",
                          "weight_source"})
VITALS = ("hr", "sbp", "dbp", "spo2", "respiratory_rate", "mental_status", "rhythm",
          "pulse_present", "work_of_breathing", "crt", "extremities")
# Identity and time of a particular run: two runs of the same inputs differ here
# and nowhere that matters.
VOLATILE = frozenset({"id", "attempt_id", "record_id", "source_hash", "generated_at", "created_at",
                      "updated_at", "code_version", "revision", "attempt_revision", "assignment_seed",
                      "runtime_version", "saved_at", "exported_at",
                      # A rhythm strip's noise and its identifier are drawn per run.
                      "seed", "recording_id"})
EMPTY = (None, False, "", [], {})
# What every encounter's analysis is sent alike: the instructions and the
# definitions that are not about this record. A change there (a new prompt
# version) is the same for every encounter, and is reported apart; it makes a
# saved analysis older, not wrong about this record.
COMMON = frozenset({"record_screening_rule", "information_on_asking_rule", "domain_separation", "rubric",
                    "rubric_version", "schema_version", "objective_rubric", "engine_limitations",
                    "coverage_version"})


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


# --- records ---------------------------------------------------------------------

def _from_sqlite(path):
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute("""SELECT a.*, u.username FROM mrs_attempts a
            JOIN mrs_users u ON u.id = a.user_id ORDER BY a.created_at""").fetchall()
    finally:
        connection.close()
    from account_store import AccountStore
    return [AccountStore._attempt(row) for row in rows]


def records_from_database(url, usernames=()):
    """Completed encounters read from the application's database, read-only.

    For encounters that live only there -- the ten-encounter batch of
    2026-09-23 among them. Nothing is written: one SELECT, through the same
    store the application uses, optionally limited to some accounts.
    """
    from account_store import AccountStore
    store = AccountStore(url, allow_sqlite=url.startswith("sqlite"))
    with store._transaction() as connection:
        rows = store._execute(connection, """SELECT a.*, u.username FROM mrs_attempts a
            JOIN mrs_users u ON u.id = a.user_id WHERE a.status = 'completed'
            ORDER BY a.created_at""").fetchall()
    wanted = set(usernames or ())
    return [AccountStore._attempt(row) for row in rows if not wanted or row["username"] in wanted]


def records_from(path):
    """Saved records: a rehearsal's databases, a database, or record JSON files."""
    path = Path(path)
    if path.is_dir():
        found = []
        for child in sorted(path.iterdir()):
            if child.suffix in (".sqlite3", ".sqlite", ".db") or child.name.endswith(".record.json"):
                found += records_from(child)
        return found
    if path.suffix in (".sqlite3", ".sqlite", ".db"):
        return _from_sqlite(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return [data.get("record", data)] if isinstance(data, dict) else list(data)


def case_of(record):
    from faculty_analysis import case_id_of
    return case_id_of(record) or (record.get("encounter") or {}).get("case_label") or record.get("id")


def code_version_of(record):
    return ((record.get("encounter") or {}).get("assignment") or {}).get("code_version")


def _session(record):
    return ((record.get("payload") or {}).get("session")) or {}


# --- the clinical trajectory --------------------------------------------------------

def _action(summary):
    return _stable({key: value for key, value in (summary or {}).items() if key not in PRESENTATION})


def trajectory(record):
    """What was done, when, the state after it, and how it closed."""
    session = _session(record)
    trace = session.get("encounter_closed_trace") or session.get("management_trace") or []
    entries = []
    for entry in trace:
        observable = (entry.get("state_after") or {}).get("observable") or {}
        entries.append({
            "status": entry.get("execution_status"),
            "minute": entry.get("decision_time_min"),
            "response": entry.get("response_time_min"),
            "actions": [_action(summary) for summary in entry.get("action_summaries") or []],
            "after": {key: observable.get(key) for key in VITALS},
        })
    state = session.get("state") or {}
    return {"entries": entries, "closed_at": session.get("encounter_closed_time_min"),
            "disposition": state.get("disposition")}


def _actions_differ(before, after):
    """Whether two decisions executed different things; and the details only one records.

    Actions are matched by type, in order. A parameter both record and that
    differs is a different execution; a parameter only one of them records --
    a rate the newer code now writes down beside the label that always said
    it -- is a detail, reported and not counted.
    """
    remaining = list(after)
    unmatched, details = [], []
    for action in before:
        match = next((item for item in remaining if item.get("type") == action.get("type")), None)
        if match is None:
            unmatched.append(action)
            continue
        remaining.remove(match)
        common = set(action) & set(match)
        if any(action[key] != match[key] for key in common):
            unmatched.append(action)
            remaining.append({**match, "_differs": True})
            continue
        details += [key for key in set(action) ^ set(match)]
    changed = bool(unmatched) or any(True for _ in remaining)
    return changed, unmatched, [{k: v for k, v in item.items() if k != "_differs"} for item in remaining], sorted(set(details))


def trajectory_differences(before, after, limit=6, details=None):
    """Where two trajectories part, said in a few lines."""
    lines = []
    if len(before["entries"]) != len(after["entries"]):
        lines.append(f"{len(before['entries'])} decisions before, {len(after['entries'])} after")
    for index, (a, b) in enumerate(zip(before["entries"], after["entries"])):
        for key in ("status", "minute", "response", "actions", "after"):
            if key == "actions":
                changed, gone, new, noted = _actions_differ(a["actions"], b["actions"])
                if noted and details is not None:
                    details.append(f"decision {index + 1}: now also records {', '.join(noted)}")
                if changed:
                    lines.append(f"decision {index + 1}: executed {_short(gone)} before, {_short(new)} after")
                    break
                continue
            if a[key] != b[key]:
                if key == "after":
                    changed = {k: (a["after"][k], b["after"][k]) for k in VITALS if a["after"][k] != b["after"][k]}
                    lines.append(f"decision {index + 1}: state after differs {changed}")
                else:
                    lines.append(f"decision {index + 1}: {key} {a[key]} before, {b[key]} after")
                break
        if len(lines) >= limit:
            break
    for key in ("closed_at", "disposition"):
        if before[key] != after[key]:
            lines.append(f"{key.replace('_', ' ')}: {before[key]} before, {after[key]} after")
    return lines[:limit + 2]


def _short(actions):
    kinds = []
    for value in actions:
        kind = value.get("type", "?")
        detail = value.get("destination") or value.get("agent") or value.get("diagnostic_type") or ""
        kinds.append(kind + (f" ({detail})" if detail else ""))
    return "[" + ", ".join(kinds) + "]" if kinds else "nothing"


def interaction_differences(before, after, limit=6):
    """What the resident was asked, when the course itself is the same.

    A question the page no longer asks (a follow-up now accepted as the
    reassessment of a discharge, a plan shared by an antipyretic) is not a
    change in the patient's course; it is reported, and decides nothing.
    """
    lines = []
    trace_a = _session(before).get("encounter_closed_trace") or _session(before).get("management_trace") or []
    trace_b = _session(after).get("encounter_closed_trace") or _session(after).get("management_trace") or []
    for index, (a, b) in enumerate(zip(trace_a, trace_b)):
        gate_a, gate_b = a.get("reasoning_gate") or {}, b.get("reasoning_gate") or {}
        asked_a, asked_b = gate_a.get("asked_for") or [], gate_b.get("asked_for") or []
        if (gate_a.get("status"), asked_a) != (gate_b.get("status"), asked_b):
            lines.append(f"decision {index + 1}: asked for {asked_a or 'nothing'} ({gate_a.get('status')}) "
                         f"before, {asked_b or 'nothing'} ({gate_b.get('status')}) after")
        if len(lines) >= limit:
            break
    return lines


# --- what the analyses read ---------------------------------------------------------

_SNIPPET = r'''
import json, sys
paths = sys.argv[1:]
results = {}
for path in paths:
    record = json.load(open(path, encoding="utf-8"))
    out = {}
    def attempt(name, build):
        try:
            out[name] = build()
        except Exception as error:
            out[name] = {"unavailable": type(error).__name__ + ": " + str(error)[:200]}
    def rubric():
        import encounter_context
        from rubric_analysis import build_rubric_source
        return build_rubric_source(record, "unknown", encounter_context.not_reported())
    def brief():
        import encounter_context
        from faculty_analysis import build_analysis_source
        return build_analysis_source(record, "unknown", encounter_context.not_reported())
    def trace():
        from management_trace_store import analysis_payload_from_session
        from management_trace_analysis import build_analysis_source
        return build_analysis_source(analysis_payload_from_session(record["payload"]["session"]))
    attempt("rubric proposal", rubric)
    attempt("faculty brief", brief)
    attempt("Management Trace analysis", trace)
    results[path] = out
print(json.dumps(results, default=str, sort_keys=True))
'''


def _stable(value):
    if isinstance(value, dict):
        return {key: _stable(item) for key, item in value.items() if key not in VOLATILE}
    if isinstance(value, list):
        return [_stable(item) for item in value]
    return value


@contextmanager
def code_at(revision):
    """A checkout of ``revision`` beside this one, removed afterwards; None is this code."""
    if revision is None:
        yield ROOT
        return
    folder = Path(tempfile.mkdtemp(prefix="reclassify-"))
    checkout = folder / "code"
    subprocess.run(["git", "worktree", "add", "--detach", str(checkout), revision], cwd=ROOT,
                   check=True, capture_output=True, text=True)
    try:
        yield checkout
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(checkout)], cwd=ROOT,
                       capture_output=True, text=True)
        subprocess.run(["rm", "-rf", str(folder)], capture_output=True)


def readings(records, revision=None):
    """What the three analyses read from each record, under ``revision`` (None: this code)."""
    with tempfile.TemporaryDirectory() as scratch, code_at(revision) as code:
        paths = []
        for index, record in enumerate(records):
            path = Path(scratch) / f"record-{index}.json"
            path.write_text(canonical(record), encoding="utf-8")
            paths.append(str(path))
        env = {key: value for key, value in os.environ.items() if key != "OPENAI_API_KEY"}
        env.update({"MRS_OFFLINE_CASES": "1", "PYTHONPATH": str(code), "PYTHONDONTWRITEBYTECODE": "1"})
        done = subprocess.run([sys.executable, "-c", _SNIPPET, *paths], cwd=str(code), env=env,
                              capture_output=True, text=True, timeout=900)
        if done.returncode != 0:
            raise RuntimeError(f"Reading the records at {revision or 'this code'} failed: "
                               + done.stderr[-2000:])
        result = json.loads(done.stdout.strip().splitlines()[-1])
        return [{name: _stable(value) for name, value in result[path].items()} for path in paths]


def common_differences(a, b):
    """The shared instructions and definitions that changed between two readings."""
    a = a if isinstance(a, dict) else {}
    b = b if isinstance(b, dict) else {}
    return sorted(key for key in COMMON if (key in a or key in b) and a.get(key) != b.get(key))


def differences(a, b, path="", limit=8):
    """The first places two readings differ about this record, as paths."""
    found = []
    if isinstance(a, dict) and isinstance(b, dict) and not path:
        a = {key: value for key, value in a.items() if key not in COMMON}
        b = {key: value for key, value in b.items() if key not in COMMON}

    def walk(x, y, where):
        if len(found) >= limit:
            return
        if isinstance(x, dict) and isinstance(y, dict):
            for key in sorted(set(x) | set(y)):
                # A field the other code does not have, holding nothing, says
                # nothing new: the newer code records an empty list of
                # indications where the older one had no list at all.
                if key not in x:
                    if y[key] not in EMPTY:
                        found.append(f"{where}/{key}: added {_brief(y[key])}")
                elif key not in y:
                    if x[key] not in EMPTY:
                        found.append(f"{where}/{key}: removed {_brief(x[key])}")
                else:
                    walk(x[key], y[key], f"{where}/{key}")
                if len(found) >= limit:
                    return
        elif isinstance(x, list) and isinstance(y, list):
            if len(x) != len(y):
                found.append(f"{where}: {len(x)} items before, {len(y)} after")
                return
            for index, (p, q) in enumerate(zip(x, y)):
                walk(p, q, f"{where}[{index}]")
        elif x != y:
            found.append(f"{where}: {_brief(x)} -> {_brief(y)}")

    walk(a, b, path)
    return found


def _brief(value):
    text = canonical(value)
    return text if len(text) <= 90 else text[:87] + "..."


# --- the decision ---------------------------------------------------------------------

def classify(before, after=None, *, old_reading=None, new_reading=None):
    """One encounter's class, and why."""
    result = {"case": case_of(before), "record": before.get("id"),
              "code_version": code_version_of(before)}
    if after is not None:
        details = []
        moved = trajectory_differences(trajectory(before), trajectory(after), details=details)
        result["trajectory"] = moved
        result["details"] = details
        result["interaction"] = interaction_differences(before, after)
        if moved:
            result["class"] = RERUN
            return result
    changed, common = {}, {}
    if old_reading is not None and new_reading is not None:
        for name in sorted(set(old_reading) | set(new_reading)):
            found = differences(old_reading.get(name), new_reading.get(name))
            if found:
                changed[name] = found
            shared = common_differences(old_reading.get(name), new_reading.get(name))
            if shared:
                common[name] = shared
    result["analyses"] = changed
    result["instructions"] = common
    result["class"] = REANALYSE if changed else DOCUMENTS
    return result


def reread(record):
    """Triage without a replay: the decisions the current reader would execute differently."""
    from family_parser import parse_family_actions
    flagged = []
    trace = _session(record).get("encounter_closed_trace") or _session(record).get("management_trace") or []
    for index, entry in enumerate(trace):
        text = str(entry.get("learner_input") or "").split("\n\nReasoning clarification")[0]
        if not text.strip() or entry.get("execution_status") in ("information",):
            continue
        recorded = sorted(str((action or {}).get("type")) for action in entry.get("interpreted_action") or []
                          if isinstance(action, dict))
        parsed = parse_family_actions(text)
        now = sorted(str(action.get("type")) for action in parsed.get("actions") or [])
        if recorded != now:
            flagged.append({"decision": index + 1, "minute": entry.get("decision_time_min"),
                            "input": text[:160], "recorded": recorded, "now": now,
                            "status": entry.get("execution_status")})
    return flagged


def pair(before, after):
    """Match records of the same inputs by case, in order."""
    remaining = list(after)
    pairs = []
    for record in before:
        case = case_of(record)
        match = next((item for item in remaining if case_of(item) == case), None)
        if match is not None:
            remaining.remove(match)
        pairs.append((record, match))
    return pairs


def as_markdown(rows, language="es"):
    labels = LABELS_ES if language == "es" else LABELS
    lines = ["| # | Caso | Clase | Trayectoria | Lo que un análisis leería distinto en este registro | "
             "Preguntas al residente |", "|---|---|---|---|---|---|"]
    for number, row in enumerate(rows, 1):
        lines.append("| {n} | {case} | {cls} | {traj} | {analyses} | {asked} |".format(
            n=number, case=row["case"], cls=labels[row["class"]],
            traj="; ".join(row.get("trajectory") or []) or "igual",
            analyses=("; ".join(f"{name}: {', '.join(found[:3])}" for name, found in row.get("analyses", {}).items())
                      or ("—" if row["class"] == RERUN else "nada")),
            asked="; ".join(row.get("interaction") or []) or "igual"))
    counts = {cls: sum(row["class"] == cls for row in rows) for cls in (RERUN, REANALYSE, DOCUMENTS)}
    lines += ["", f"Volver a ejecutar: {counts[RERUN]} · Nuevo análisis: {counts[REANALYSE]} · "
                  f"Sólo documentos: {counts[DOCUMENTS]}"]
    shared = sorted({f"{name}: {', '.join(keys)}" for row in rows for name, keys in row.get("instructions", {}).items()})
    if shared:
        lines += ["", "Instrucciones o definiciones comunes a todos los encuentros que cambiaron (una versión "
                      "nueva del prompt; hacen más antiguo un análisis guardado, no lo hacen erróneo sobre su "
                      "registro): " + "; ".join(shared) + "."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"),
                        help="saved records and the replay of the same inputs")
    parser.add_argument("--reread", metavar="RECORDS", help="saved records, re-read without a replay")
    parser.add_argument("--database", metavar="URL",
                        help="with --reread: read the completed encounters from this database instead "
                             "(read-only; the application's MRS_DATABASE_URL)")
    parser.add_argument("--account", action="append", default=[],
                        help="with --database: only this account's encounters; may be repeated")
    parser.add_argument("--since", help="the revision that produced the saved records "
                                        "(default: the one each record names)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not (args.compare or args.reread or args.database):
        parser.print_help()
        return 2
    if args.database:
        args.reread = args.reread or args.database
        before = records_from_database(args.database, args.account)
    else:
        before = records_from(args.compare[0] if args.compare else args.reread)
    after = records_from(args.compare[1]) if args.compare else []
    pairs = pair(before, after) if args.compare else [(record, None) for record in before]
    # The saved records read by the code that produced them and by this code.
    by_revision = {}
    for record, _ in pairs:
        by_revision.setdefault(args.since or code_version_of(record), []).append(record)
    old, new = {}, {}
    for revision, group in by_revision.items():
        if revision is None:
            continue
        for record, reading in zip(group, readings(group, revision)):
            old[id(record)] = reading
    for record, reading in zip([record for record, _ in pairs], readings([record for record, _ in pairs])):
        new[id(record)] = reading
    rows = []
    for record, replay in pairs:
        row = classify(record, replay, old_reading=old.get(id(record)), new_reading=new.get(id(record)))
        if args.reread:
            row["reread"] = reread(record)
            if row["reread"] and row["class"] != RERUN:
                row["rerun_candidate"] = True
        if old.get(id(record)) is None:
            row["note"] = "No revision named: what the analyses read could not be compared."
        rows.append(row)
    print(json.dumps(rows, indent=1, ensure_ascii=False, default=str) if args.json else as_markdown(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
