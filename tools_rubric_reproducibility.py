"""One frozen record, scored several times: the evaluator's variability, isolated.

Score reproducibility, 2026-09-24. Two runs of the same pilot script were
scored 13/15 and 9/15. Two things could differ between them: the encounter or
the evaluator. This separates them.

* **The encounter.** ``--check-encounter`` plays a script several times through
  the production interpreter and engine, with the provider key withheld, and
  compares the records byte for byte. It costs nothing. If they are identical,
  the same script cannot produce two different encounters, and a difference in
  scores comes from the evaluator (or from a different code or prompt version,
  which the saved proposals name).
* **The evaluator.** ``--times N`` asks the same question N times about one
  frozen record: the same record, rubric, prompt, schema and model, each a new
  request (nothing is cached or reused -- a proposal is kept only if it is bound
  to the same record fingerprint, and the provider requests are counted and
  capped at N). The summary gives, per domain, every score, the spread and the
  agreement; per defined event, every verdict; and the marks the record check
  raised on each proposal.

Nothing here declares stability unless every run agreed. Nothing here fixes a
score: the point is to measure the reading, not to steer it.

Faculty decision 11 of 2026-09-25 ("Reproducibilidad: medir primero, pero no
adaptar después el criterio para que pase") sets the order. First, whether the
two runs that scored 13/15 and 9/15 read the same record with the same rubric,
prompt and model (``--compare`` says so before anything else). Then identical
records read again, performances of different quality among them (``--case``
may be repeated), compared per domain, in total, in critical events and in
what was not assessable. A difference in the total is decomposed into the
domains and events that make it up, and until it is explained the score is not
used to compare residents; the tool explains how a difference is made up,
never what the score should have been. Five to ten requests are an initial
exploration, not a validation. Every request is written to a ledger of its
own, apart from the paid encounters, so that the spend stays visible
(``--spent``).

    python tools_rubric_reproducibility.py --check-encounter opioid_67f        # free
    python tools_rubric_reproducibility.py --case opioid_67f --times 5 --dry-run  # free
    python tools_rubric_reproducibility.py --case opioid_67f --times 5 --yes      # N paid requests
    python tools_rubric_reproducibility.py --case opioid_35m --case opioid_67f --times 5 --yes
    python tools_rubric_reproducibility.py --record saved.record.json --times 5 --yes
    python tools_rubric_reproducibility.py --compare run_a.json run_b.json          # free
    python tools_rubric_reproducibility.py --spent                                   # free
"""
import os
import sys

if __name__ == "__main__":
    # Playing the script never spends anything: the key is withheld from every
    # resolver while the record is built, and handed only to the evaluator.
    os.environ.setdefault("MRS_OFFLINE_CASES", "1")

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MAX_TIMES = 10
#: Requests in one invocation, across every record: an initial exploration.
EXPLORATION_LIMIT = 10
DEFAULT_OUT = "local-data/paid_runs/reproducibility"
EXPLORATION_NOTE = ("Exploration, not validation: {readings} reading(s) of {records} record(s). "
                    "Five to ten requests describe the evaluator's variability; they do not "
                    "establish that the score is stable.")
UNEXPLAINED = ("The total differed by {points} point(s) between readings of the same record. Until "
               "this difference is explained, the score is not used to compare residents.")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def frozen(case=None, record_path=None):
    """The record to evaluate: a pilot script played offline, or a saved record."""
    if record_path:
        return json.loads(Path(record_path).read_text(encoding="utf-8"))
    from tools_rubric_runs import BY_ID, play_orders
    if case not in BY_ID:
        raise SystemExit(f"Unknown script {case!r}. See tools_rubric_runs.py --list.")
    record, _ = play_orders(BY_ID[case])
    return record


def check_encounter(case, plays=3):
    """Play one script ``plays`` times; the encounter is deterministic if every record matches."""
    digests = [digest(frozen(case)) for _ in range(plays)]
    return {"case": case, "plays": plays, "identical": len(set(digests)) == 1, "digests": digests}


def _key():
    from tools_rubric_runs import _key as key
    return key()


# --- the ledger: evaluator requests, apart from the encounters ---------------------

def ledger_path(out=DEFAULT_OUT):
    """Where this tool writes its requests. Never the ledger of a batch's encounters."""
    path = Path(out)
    return (path if path.is_absolute() else ROOT / path) / "ledger.jsonl"


def _write_ledger(ledger, entry):
    if ledger is None:
        return
    ledger = Path(ledger)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def spent(ledger):
    """Provider requests on the ledger, counting a reading that never finished as spent."""
    ledger = Path(ledger)
    if not ledger.exists():
        return {"readings": 0, "requests": 0, "unfinished": 0}
    started, finished, requests = set(), set(), 0
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        key = (entry.get("batch"), entry.get("record_fingerprint"), entry.get("run"))
        if entry.get("event") == "started":
            started.add(key)
        elif entry.get("event") == "finished":
            finished.add(key)
            requests += int(entry.get("provider_requests") or 0)
    unfinished = len(started - finished)
    return {"readings": len(started), "requests": requests + unfinished, "unfinished": unfinished}


def evaluate(record, times, *, model="gpt-5-mini", client=None, api_key=None, ledger=None, batch=None):
    """``times`` independent proposals about one frozen record. Never more requests than that.

    With a ``ledger``, each reading is written before it starts and after it
    ends, with the provider requests it sent: the spend of these readings is
    kept apart from the paid encounters and visible on its own.
    """
    import httpx
    from faculty_analysis import source_fingerprint
    from rubric_analysis import PROMPT_VERSION, generate_rubric_proposal
    from rubric import VERSION

    if not isinstance(times, int) or not 1 <= times <= MAX_TIMES:
        raise ValueError(f"Choose between 1 and {MAX_TIMES} evaluations.")
    fingerprint = source_fingerprint(record)
    batch = batch or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sent = []
    original = httpx.Client.send

    def counted(self, request, *args, **kwargs):
        sent.append(str(request.url))
        if len(sent) > times:
            raise RuntimeError("More provider requests than evaluations were attempted; refused.")
        return original(self, request, *args, **kwargs)

    httpx.Client.send = counted
    reports, failures = [], []
    common = {"kind": "evaluator_reading", "purpose": "reproducibility", "paid_encounter": False,
              "batch": batch, "record_fingerprint": fingerprint, "record": record.get("id"),
              "model": model, "prompt_version": PROMPT_VERSION, "rubric_version": VERSION}
    try:
        for run in range(times):
            started = datetime.now(timezone.utc)
            before = len(sent)
            _write_ledger(ledger, {**common, "event": "started", "run": run + 1, "at": started.isoformat()})
            outcome = {"outcome": "ok"}
            try:
                report = generate_rubric_proposal(record, api_key=api_key if api_key is not None else _key(),
                                                  model=model, client=client)
            except Exception as error:  # a failed run is reported, never replaced
                failures.append({"run": run + 1, "error": f"{type(error).__name__}: {error}"})
                outcome = {"outcome": "failed", "error": type(error).__name__}
                continue
            finally:
                _write_ledger(ledger, {**common, "event": "finished", "run": run + 1, **outcome,
                                       "provider_requests": len(sent) - before,
                                       "at": datetime.now(timezone.utc).isoformat()})
            if report["source_hash"] != fingerprint:
                raise RuntimeError("A proposal is bound to another record; the comparison is void.")
            seconds = (datetime.now(timezone.utc) - started).total_seconds()
            reports.append({"run": run + 1, "seconds": round(seconds, 1), "report": report})
    finally:
        httpx.Client.send = original
    return {"fingerprint": fingerprint, "requests": len(sent), "reports": reports,
            "failures": failures}


def _proposed_total(proposal_report):
    """What the proposal adds up to if a faculty member accepted every value."""
    import rubric
    from rubric_analysis import proposed_event_rows
    scores = {row["domain_id"]: row["score"] for row in proposal_report["proposal"]["domains"]}
    events = [{"event_id": row["event_id"], "status": "confirmed"}
              for row in proposed_event_rows(proposal_report)]
    return rubric.score(scores, events)


def _not_assessable(report):
    import rubric
    return sum(1 for row in report["proposal"]["domains"] if row.get("score") == rubric.NOT_ASSESSABLE)


def explain_difference(report_a, report_b):
    """How a difference between two readings is made up. Never what it should have been.

    The total moves by the domains read differently and by the critical events
    one reading proposed and the other did not; a domain one reading scored and
    the other found not assessable changes what the total is a total of.
    """
    import rubric
    from rubric_analysis import event_verdicts
    total_a, total_b = _proposed_total(report_a), _proposed_total(report_b)
    domains = []
    for domain in rubric.DOMAIN_IDS:
        a, b = total_a["per_domain"][domain], total_b["per_domain"][domain]
        if a != b:
            numeric = isinstance(a, int) and isinstance(b, int)
            domains.append({"domain": domain, "a": a, "b": b, "points": (b - a) if numeric else None})
    verdicts_a, verdicts_b = event_verdicts(report_a), event_verdicts(report_b)
    events = [{"event_id": event_id, "a": (verdicts_a.get(event_id) or {}).get("verdict"),
               "b": (verdicts_b.get(event_id) or {}).get("verdict")}
              for event_id in sorted(set(verdicts_a) | set(verdicts_b))
              if (verdicts_a.get(event_id) or {}).get("verdict") != (verdicts_b.get(event_id) or {}).get("verdict")]
    comparable = total_a["adjusted"] is not None and total_b["adjusted"] is not None
    points = abs(total_b["adjusted"] - total_a["adjusted"]) if comparable else None
    return {"adjusted": [total_a["adjusted"], total_b["adjusted"]],
            "base": [total_a["base"], total_b["base"]],
            "penalty": [total_a["penalty"], total_b["penalty"]],
            "critical_events": [total_a["critical_events"], total_b["critical_events"]],
            "not_assessable": [_not_assessable(report_a), _not_assessable(report_b)],
            "points": points, "comparable": comparable, "domains": domains, "events": events,
            # Any difference, or a total that is not a total of the same domains,
            # is explained before the score compares anyone.
            "needs_explanation": bool(points) or not comparable and (
                total_a["coverage"]["assessed"] != total_b["coverage"]["assessed"] or bool(domains))}


def explanation_lines(difference):
    """The decomposition, said in a few lines."""
    lines = []
    if difference["points"]:
        lines.append(UNEXPLAINED.format(points=difference["points"]))
    elif not difference["comparable"] and difference["needs_explanation"]:
        lines.append("The readings did not assess the same domains, so their totals are not totals of the "
                     "same thing. Until this is explained, the score is not used to compare residents.")
    for row in difference["domains"]:
        lines.append(f"- {row['domain']}: {row['a']} and {row['b']}"
                     + (f" ({row['points']:+d})" if row["points"] is not None else
                        " (one reading scored it, the other found it not assessable)"))
    for row in difference["events"]:
        lines.append(f"- {row['event_id']}: {row['a']} and {row['b']}")
    if difference["penalty"][0] != difference["penalty"][1]:
        lines.append(f"- Penalty for critical events: {difference['penalty'][0]} and {difference['penalty'][1]}")
    return lines


def summarize(record, evaluation):
    """Per domain and per event, what every run said, and whether they agreed."""
    import rubric
    import rubric_screening
    from rubric_analysis import case_id_of, event_verdicts
    reports = [item["report"] for item in evaluation["reports"]]
    case_id = case_id_of(record)
    screening = rubric_screening.screening(record, case_id) if case_id else {"events": [], "domains": []}
    domains = {}
    for domain in rubric.DOMAIN_IDS:
        rows = [next(row for row in report["proposal"]["domains"] if row["domain_id"] == domain)
                for report in reports]
        scores = [row["score"] for row in rows]
        numeric = [score for score in scores if isinstance(score, int) and not isinstance(score, bool)]
        counts = Counter(str(score) for score in scores)
        modal, modal_count = counts.most_common(1)[0] if counts else ("", 0)
        domains[domain] = {
            "scores": scores,
            "opportunities": [row.get("opportunity") for row in rows],
            "not_assessable": sum(1 for score in scores if score == rubric.NOT_ASSESSABLE),
            "range": (max(numeric) - min(numeric)) if numeric else None,
            "modal": modal, "agreement": round(modal_count / len(scores), 2) if scores else None,
        }
    events = {}
    for report in reports:
        for event_id, verdict in event_verdicts(report).items():
            events.setdefault(event_id, []).append(verdict.get("verdict"))
    totals = []
    for report in reports:
        total = _proposed_total(report)
        totals.append({"base": total["base"], "penalty": total["penalty"],
                       "adjusted": total["adjusted"], "partial_subtotal": total["partial_subtotal"],
                       "assessed": total["coverage"]["assessed"],
                       "critical_events": total["critical_events"],
                       "not_assessable": _not_assessable(report)})
    marks = []
    for report in reports:
        flags = (rubric_screening.proposal_flags(report, screening)
                 + rubric_screening.anchor_flags(report, record))
        marks.append(dict(Counter(flag["kind"] for flag in flags)))
    agree = (all(len(set(map(str, row["scores"]))) <= 1 for row in domains.values())
             and all(len(set(values)) <= 1 for values in events.values()))
    varying = [domain for domain, row in domains.items() if len(set(map(str, row["scores"]))) > 1]
    adjusted = [total["adjusted"] for total in totals if total["adjusted"] is not None]
    # The two readings furthest apart, decomposed; readings that could not be
    # totalled are compared on what they assessed.
    difference = None
    if len(reports) > 1:
        order = sorted(range(len(reports)), key=lambda index: (
            totals[index]["adjusted"] is None, totals[index]["adjusted"] or 0))
        difference = explain_difference(reports[order[0]], reports[order[-1]])
        if not difference["needs_explanation"]:
            for index in order[1:]:
                candidate = explain_difference(reports[order[0]], reports[index])
                if candidate["needs_explanation"]:
                    difference = candidate
                    break
    return {
        "case_id": case_id, "record": record.get("id"), "fingerprint": evaluation["fingerprint"],
        "runs": len(reports), "failures": evaluation["failures"], "requests": evaluation["requests"],
        "model": sorted({report["model"] for report in reports}),
        "prompt_version": sorted({report["prompt_version"] for report in reports}),
        "rubric_version": sorted({report["rubric_version"] for report in reports}),
        "domains": domains, "events": events, "totals": totals, "marks": marks,
        # Stability is a claim about every run, and it is made only when every
        # run agreed. Two runs that agree are two runs, not a demonstration.
        "all_runs_agreed": bool(reports) and agree,
        "varying_domains": varying,
        "adjusted_range": (max(adjusted) - min(adjusted)) if len(adjusted) > 1 else None,
        "critical_events": [total["critical_events"] for total in totals],
        "not_assessable": [total["not_assessable"] for total in totals],
        "difference": difference,
        "exploration": EXPLORATION_NOTE.format(readings=len(reports), records=1),
    }


def as_markdown(summary):
    lines = [f"# Reproducibility · {summary['case_id']} · {summary['runs']} runs",
             "",
             f"Record fingerprint `{summary['fingerprint'][:16]}`, prompt "
             f"{', '.join(summary['prompt_version'])}, rubric {', '.join(summary['rubric_version'])}, "
             f"model {', '.join(summary['model'])}. Requests sent: {summary['requests']}.",
             "", "| Domain | Scores | Range | Agreement | Opportunity |", "|---|---|---|---|---|"]
    for domain, row in summary["domains"].items():
        lines.append(f"| {domain} | {', '.join(map(str, row['scores']))} | "
                     f"{'-' if row['range'] is None else row['range']} | {row['agreement']} | "
                     f"{', '.join(str(o) for o in row['opportunities'])} |")
    lines += ["", "| Event | Verdicts |", "|---|---|"]
    for event_id, verdicts in sorted(summary["events"].items()):
        lines.append(f"| {event_id} | {', '.join(map(str, verdicts))} |")
    lines += ["", "Totals if every proposed value were accepted: "
              + "; ".join(f"base {t['base']}, penalty {t['penalty']}, adjusted {t['adjusted']}"
                          if t["base"] is not None else f"partial {t['partial_subtotal']} "
                          f"({t['assessed']} domains)" for t in summary["totals"]), ""]
    lines.append("Domains not assessable per reading: " + ", ".join(map(str, summary.get("not_assessable", [])))
                 + ". Critical events proposed per reading: "
                 + ", ".join(map(str, summary.get("critical_events", []))) + ".")
    lines.append("")
    lines.append("All runs agreed." if summary["all_runs_agreed"] else
                 "The runs did not agree: " + (", ".join(summary["varying_domains"]) or "events")
                 + (f"; the adjusted total ranged over {summary['adjusted_range']} points."
                    if summary["adjusted_range"] is not None else "."))
    if summary.get("difference") and summary["difference"]["needs_explanation"]:
        lines += ["", *explanation_lines(summary["difference"])]
    if summary["failures"]:
        lines.append(f"{len(summary['failures'])} run(s) failed and were not replaced.")
    if summary.get("exploration"):
        lines += ["", summary["exploration"]]
    return "\n".join(lines) + "\n"


def _load_run(path):
    """A saved proposal as tools_rubric_runs writes it, or a bare envelope, with its record."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    report = data.get("report", data)
    record_path = path.with_name(path.name.replace(".json", ".record.json"))
    record = (json.loads(record_path.read_text(encoding="utf-8"))
              if record_path.exists() and record_path != path else None)
    return report, record


def _events_of(record):
    from rubric_analysis import build_rubric_source
    rows = []
    for row in build_rubric_source(record)["decision_events"]:
        rows.append({"ref": row.get("evidence_ref"), "minute": row.get("decision_time_min"),
                     "status": row.get("execution_status"),
                     "actions": canonical(row.get("executed_action_summaries")),
                     "before": canonical(row.get("state_before")),
                     "after": canonical(row.get("state_after"))})
    return rows


IDENTITY = (("record", "source_hash"), ("rubric", "rubric_version"), ("prompt", "prompt_version"),
            ("model", "model"), ("coverage", "coverage_version"))


def identity(report_a, report_b):
    """What two readings read, and with what: checked before any score is compared."""
    rows = {name: {"a": report_a.get(key), "b": report_b.get(key),
                   "same": report_a.get(key) == report_b.get(key)} for name, key in IDENTITY}
    differing = [name for name, row in rows.items() if not row["same"]]
    if not differing:
        conclusion = ("The same record, read with the same rubric, prompt and model: every difference "
                      "below is the evaluator's reading.")
    elif "record" in differing:
        conclusion = ("Not the same record: the encounters themselves differ, so a difference in score "
                      "is not the evaluator's alone. The first decision where they part is named below "
                      "when both records are available.")
    else:
        conclusion = ("The same record, but not the same " + ", ".join(differing) + ": a difference in "
                      "score cannot be attributed to the evaluator's reading alone.")
    return {"rows": rows, "differing": differing, "conclusion": conclusion}


def compare(report_a, report_b, record_a=None, record_b=None):
    """Two saved proposals: was it the same encounter, and where did the readings part?

    The same ``source_hash`` means the same frozen record was read twice, so every
    difference is the evaluator's -- provided the rubric, prompt and model were
    the same too, which is checked first. A different one means the encounters
    themselves differed, and the first decision where they did is named.
    """
    import rubric_screening
    from rubric_analysis import case_id_of, event_verdicts
    same_record = report_a.get("source_hash") == report_b.get("source_hash")
    domains = {}
    rows_a = {row["domain_id"]: row for row in report_a["proposal"]["domains"]}
    rows_b = {row["domain_id"]: row for row in report_b["proposal"]["domains"]}
    for domain in sorted(rows_a):
        a, b = rows_a[domain], rows_b.get(domain, {})
        domains[domain] = {"scores": [a.get("score"), b.get("score")],
                           "opportunities": [a.get("opportunity"), b.get("opportunity")],
                           "evidence": [sorted(a.get("evidence_refs") or []),
                                        sorted(b.get("evidence_refs") or [])],
                           "differs": a.get("score") != b.get("score")}
    verdicts_a, verdicts_b = event_verdicts(report_a), event_verdicts(report_b)
    events = {event_id: [(verdicts_a.get(event_id) or {}).get("verdict"),
                         (verdicts_b.get(event_id) or {}).get("verdict")]
              for event_id in sorted(set(verdicts_a) | set(verdicts_b))}
    result = {"same_record": same_record, "identity": identity(report_a, report_b),
              "versions": [[report_a.get("prompt_version"), report_a.get("rubric_version"),
                            report_a.get("model")],
                           [report_b.get("prompt_version"), report_b.get("rubric_version"),
                            report_b.get("model")]],
              "domains": domains, "events": events,
              "totals": [_proposed_total(report_a), _proposed_total(report_b)],
              "difference": explain_difference(report_a, report_b)}
    if record_a is not None and record_b is not None:
        first = None
        events_a, events_b = _events_of(record_a), _events_of(record_b)
        for index in range(max(len(events_a), len(events_b))):
            left = events_a[index] if index < len(events_a) else None
            right = events_b[index] if index < len(events_b) else None
            if left != right:
                first = {"index": index, "a": left, "b": right}
                break
        case_a, case_b = case_id_of(record_a), case_id_of(record_b)
        windows = [{row["domain_id"]: row["window_opened"] for row in
                    rubric_screening.screening(record, case)["domains"]}
                   for record, case in ((record_a, case_a), (record_b, case_b))]
        result.update({"decisions": [len(events_a), len(events_b)], "first_difference": first,
                       "windows_opened": windows})
    return result


def compare_markdown(result):
    """A comparison, identity first, as a faculty member reads it."""
    identity_rows = result["identity"]["rows"]
    short = lambda value: (str(value)[:16] if value is not None else "—")
    lines = ["# Two readings compared", "", "| | A | B | Same |", "|---|---|---|---|"]
    for name, row in identity_rows.items():
        lines.append(f"| {name.capitalize()} | {short(row['a'])} | {short(row['b'])} | "
                     f"{'yes' if row['same'] else 'no'} |")
    lines += ["", result["identity"]["conclusion"], "",
              "| Domain | A | B | Opportunity A | Opportunity B |", "|---|---|---|---|---|"]
    for domain, row in result["domains"].items():
        lines.append(f"| {domain} | {row['scores'][0]} | {row['scores'][1]} | "
                     f"{row['opportunities'][0]} | {row['opportunities'][1]} |")
    lines += ["", "| Event | A | B |", "|---|---|---|"]
    for event_id, (a, b) in result["events"].items():
        lines.append(f"| {event_id} | {a} | {b} |")
    difference = result["difference"]
    lines += ["", f"Totals if every proposed value were accepted: A adjusted {difference['adjusted'][0]} "
              f"(base {difference['base'][0]}, penalty {difference['penalty'][0]}); B adjusted "
              f"{difference['adjusted'][1]} (base {difference['base'][1]}, penalty {difference['penalty'][1]}).",
              f"Domains not assessable: A {difference['not_assessable'][0]}, B {difference['not_assessable'][1]}. "
              f"Critical events proposed: A {difference['critical_events'][0]}, B {difference['critical_events'][1]}."]
    if difference["needs_explanation"]:
        lines += ["", *explanation_lines(difference)]
    if result.get("first_difference"):
        lines += ["", f"The encounters part at decision {result['first_difference']['index']}."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--case", action="append", default=[],
                        help="a pilot script (tools_rubric_runs.py --list); may be repeated")
    parser.add_argument("--record", action="append", default=[], help="a saved record JSON; may be repeated")
    parser.add_argument("--check-encounter", metavar="CASE", help="free: play a script repeatedly")
    parser.add_argument("--compare", nargs=2, metavar=("RUN_A", "RUN_B"),
                        help="free: two saved proposals (with their .record.json beside them)")
    parser.add_argument("--json", action="store_true", help="with --compare: the comparison as JSON")
    parser.add_argument("--spent", action="store_true", help="free: the requests on this tool's ledger")
    parser.add_argument("--plays", type=int, default=3)
    parser.add_argument("--times", type=int, default=0, help=f"evaluations per record, 1-{MAX_TIMES}")
    parser.add_argument("--model", default="gpt-5-mini")
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true", help="required to send the paid requests")
    args = parser.parse_args(argv)

    if args.compare:
        (report_a, record_a), (report_b, record_b) = (_load_run(path) for path in args.compare)
        result = compare(report_a, report_b, record_a, record_b)
        print(json.dumps(result, indent=1, ensure_ascii=False, default=str) if args.json
              else compare_markdown(result))
        return 0
    if args.spent:
        ledger = ledger_path(args.out)
        print(json.dumps({"ledger": str(ledger), **spent(ledger)}, indent=1))
        return 0
    if args.check_encounter:
        result = check_encounter(args.check_encounter, args.plays)
        print(json.dumps(result, indent=1))
        return 0 if result["identical"] else 1
    if not (args.case or args.record) or not args.times:
        parser.print_help()
        return 2
    records = [frozen(case) for case in args.case] + [frozen(record_path=path) for path in args.record]
    total = args.times * len(records)
    if total > EXPLORATION_LIMIT:
        print(f"{total} requests asked for; one exploration sends at most {EXPLORATION_LIMIT}.", file=sys.stderr)
        return 2
    from faculty_analysis import source_fingerprint
    for record in records:
        print(f"record {record.get('id')} · fingerprint {source_fingerprint(record)[:16]} · "
              f"{args.times} evaluation(s) = {args.times} paid request(s) with {args.model}")
    ledger = ledger_path(args.out)
    print(f"{total} paid request(s) in all, written to {ledger}, apart from any encounter.")
    if args.dry_run:
        return 0
    if not args.yes:
        print("This sends paid requests. Re-run with --yes.", file=sys.stderr)
        return 2
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    readings = 0
    for record in records:
        evaluation = evaluate(record, args.times, model=args.model, ledger=ledger, batch=stamp)
        summary = summarize(record, evaluation)
        readings += summary["runs"]
        out = ledger.parent / f"{summary['case_id'] or 'record'}-{stamp}"
        out.mkdir(parents=True, exist_ok=False)
        (out / "record.json").write_text(json.dumps(record, indent=1, ensure_ascii=False, default=str),
                                         encoding="utf-8")
        for item in evaluation["reports"]:
            (out / f"run-{item['run']}.json").write_text(
                json.dumps(item, indent=1, ensure_ascii=False), encoding="utf-8")
        (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
        (out / "summary.md").write_text(as_markdown(summary), encoding="utf-8")
        print(as_markdown(summary))
        print("written:", out)
    print(EXPLORATION_NOTE.format(readings=readings, records=len(records)))
    print("Spent on this tool's ledger so far:", json.dumps(spent(ledger)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
