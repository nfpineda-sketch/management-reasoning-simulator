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

    python tools_rubric_reproducibility.py --check-encounter opioid_67f        # free
    python tools_rubric_reproducibility.py --case opioid_67f --times 5 --dry-run  # free
    python tools_rubric_reproducibility.py --case opioid_67f --times 5 --yes      # N paid requests
    python tools_rubric_reproducibility.py --record saved.record.json --times 5 --yes
    python tools_rubric_reproducibility.py --compare run_a.json run_b.json          # free
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


def evaluate(record, times, *, model="gpt-5-mini", client=None, api_key=None):
    """``times`` independent proposals about one frozen record. Never more requests than that."""
    import httpx
    from faculty_analysis import source_fingerprint
    from rubric_analysis import generate_rubric_proposal

    if not isinstance(times, int) or not 1 <= times <= MAX_TIMES:
        raise ValueError(f"Choose between 1 and {MAX_TIMES} evaluations.")
    fingerprint = source_fingerprint(record)
    sent = []
    original = httpx.Client.send

    def counted(self, request, *args, **kwargs):
        sent.append(str(request.url))
        if len(sent) > times:
            raise RuntimeError("More provider requests than evaluations were attempted; refused.")
        return original(self, request, *args, **kwargs)

    httpx.Client.send = counted
    reports, failures = [], []
    try:
        for run in range(times):
            started = datetime.now(timezone.utc)
            try:
                report = generate_rubric_proposal(record, api_key=api_key if api_key is not None else _key(),
                                                  model=model, client=client)
            except Exception as error:  # a failed run is reported, never replaced
                failures.append({"run": run + 1, "error": f"{type(error).__name__}: {error}"})
                continue
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
                       "assessed": total["coverage"]["assessed"]})
    marks = []
    for report in reports:
        flags = (rubric_screening.proposal_flags(report, screening)
                 + rubric_screening.anchor_flags(report, record))
        marks.append(dict(Counter(flag["kind"] for flag in flags)))
    agree = (all(len(set(map(str, row["scores"]))) <= 1 for row in domains.values())
             and all(len(set(values)) <= 1 for values in events.values()))
    varying = [domain for domain, row in domains.items() if len(set(map(str, row["scores"]))) > 1]
    adjusted = [total["adjusted"] for total in totals if total["adjusted"] is not None]
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
    lines.append("All runs agreed." if summary["all_runs_agreed"] else
                 "The runs did not agree: " + (", ".join(summary["varying_domains"]) or "events")
                 + (f"; the adjusted total ranged over {summary['adjusted_range']} points."
                    if summary["adjusted_range"] is not None else "."))
    if summary["failures"]:
        lines.append(f"{len(summary['failures'])} run(s) failed and were not replaced.")
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


def compare(report_a, report_b, record_a=None, record_b=None):
    """Two saved proposals: was it the same encounter, and where did the readings part?

    The same ``source_hash`` means the same frozen record was read twice, so every
    difference is the evaluator's. A different one means the encounters
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
    result = {"same_record": same_record,
              "versions": [[report_a.get("prompt_version"), report_a.get("rubric_version"),
                            report_a.get("model")],
                           [report_b.get("prompt_version"), report_b.get("rubric_version"),
                            report_b.get("model")]],
              "domains": domains, "events": events,
              "totals": [_proposed_total(report_a), _proposed_total(report_b)]}
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--case", help="a pilot script (tools_rubric_runs.py --list)")
    source.add_argument("--record", help="a saved record JSON")
    parser.add_argument("--check-encounter", metavar="CASE", help="free: play a script repeatedly")
    parser.add_argument("--compare", nargs=2, metavar=("RUN_A", "RUN_B"),
                        help="free: two saved proposals (with their .record.json beside them)")
    parser.add_argument("--plays", type=int, default=3)
    parser.add_argument("--times", type=int, default=0, help=f"evaluations, 1-{MAX_TIMES}")
    parser.add_argument("--model", default="gpt-5-mini")
    parser.add_argument("--out", default="local-data/paid_runs/reproducibility")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true", help="required to send the paid requests")
    args = parser.parse_args(argv)

    if args.compare:
        (report_a, record_a), (report_b, record_b) = (_load_run(path) for path in args.compare)
        print(json.dumps(compare(report_a, report_b, record_a, record_b), indent=1,
                         ensure_ascii=False, default=str))
        return 0
    if args.check_encounter:
        result = check_encounter(args.check_encounter, args.plays)
        print(json.dumps(result, indent=1))
        return 0 if result["identical"] else 1
    if not (args.case or args.record) or not args.times:
        parser.print_help()
        return 2
    record = frozen(args.case, args.record)
    from faculty_analysis import source_fingerprint
    print(f"record {record.get('id')} · fingerprint {source_fingerprint(record)[:16]} · "
          f"{args.times} evaluation(s) = {args.times} paid request(s) with {args.model}")
    if args.dry_run:
        return 0
    if not args.yes:
        print("This sends paid requests. Re-run with --yes.", file=sys.stderr)
        return 2
    evaluation = evaluate(record, args.times, model=args.model)
    summary = summarize(record, evaluation)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / args.out / f"{summary['case_id'] or 'record'}-{stamp}"
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
