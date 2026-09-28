"""The validation corpus, phase 1: from the physicians' Word documents to a report (DF-6).

Faculty decisions of 2026-09-27, cycle 3 (§22, §44–§48, §68–§74). Every step is
deterministic and calls no model; the engine receives only what the physician
wrote, one paragraph at a time, through the same page a resident uses
(``tools_tanda20.rehearse``: Streamlit's in-process runner, a temporary
database, no provider key, the seed pinned). Nothing here contacts anyone or
sends anything: the documents come and go through the faculty (§97).

    python tools_validation_corpus.py templates --out DIR [--language es|en|both] [--case C01 ...]
    python tools_validation_corpus.py templates --pilot PILOT.json --out DIR
    python tools_validation_corpus.py split --pilot PILOT.json --returned DIR --baseline SHA --corpus DIR
    python tools_validation_corpus.py ingest --corpus DIR --subset development|sealed --out OUT
    python tools_validation_corpus.py run --out OUT [--seed 3000]
    python tools_validation_corpus.py adjudicate --out OUT [--second annotation_B.csv]
    python tools_validation_corpus.py report --out OUT [--second annotation_B.csv]

``split`` draws development and sealed once every document is back, from the
files' bytes and never their text (§18, §41), and lays out the corpus folder
with its ``manifest.json``; ``ingest`` writes ``entries.json``, the blind
``annotation.csv`` and ``annotation_second.csv``, the fifth of each document a
second clinician annotates (VC-2); ``run``
writes ``engine_output.json``; ``adjudicate`` puts annotation and engine side
by side in ``adjudication.csv``, keeping whatever a reviewer already wrote;
``report`` writes ``report.json`` and ``report.md``.

The sealed subset (§45, §73): its corpus and its output folder must lie
outside this repository, and for it the command line prints aggregates only
-- the entries, the engine's reading of them and the traceability table stay
in the output folder, which is the faculty's.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import validation_corpus as vc  # noqa: E402

NEUTRAL = "Validation corpus reading run; this review is not part of the corpus."


# --- templates -------------------------------------------------------------------------

def templates(out, languages=("es", "en"), cases=None, participant=""):
    """The blank documents for the chosen cases, and what each one was made from."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for code in cases or sorted(vc.PILOT_CASES):
        for language in languages:
            data, source = vc.template(language, code, participant=participant)
            name = vc.file_name(participant, code, language)
            (out / name).write_bytes(data)
            made.append({"file": name, "case": code, "language": language, "participant": participant or None,
                         "template_version": f"{vc.TEMPLATE_VERSION}-{language.upper()}",
                         "sha256": hashlib.sha256(data).hexdigest(), "case_text": source})
    (out / "templates.json").write_text(json.dumps({
        "corpus_version": vc.CORPUS_VERSION, "template_version": vc.TEMPLATE_VERSION,
        "note": ("The case codes stand for bank cases (validation_corpus.PILOT_CASES); the documents never "
                 "name them. Spanish case text comes from case_text/es: confirm its faculty approval "
                 "before any document is sent."),
        "documents": made}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return made


def pilot_documents(pilot_path, out):
    """Every document the pilot assigns, one folder per physician, and a list of what each was made from.

    The list goes next to the pilot manifest (``documents.json``); the physicians'
    folders hold only what is sent.
    """
    pilot_path = Path(pilot_path)
    pilot = json.loads(pilot_path.read_text(encoding="utf-8"))
    made = []
    for row in pilot["assignment"]:
        data, source = vc.template(row["language"], row["case"], participant=row["participant"], cases=pilot["cases"])
        folder = Path(out) / row["participant"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / row["file"]).write_bytes(data)
        made.append({**row, "template_version": f"{vc.TEMPLATE_VERSION}-{row['language'].upper()}",
                     "sha256": hashlib.sha256(data).hexdigest(), "case_text": source})
    (pilot_path.parent / "documents.json").write_text(json.dumps({
        "pilot_id": pilot["pilot_id"], "template_version": vc.TEMPLATE_VERSION, "documents": made},
        indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return made


# --- the development/sealed draw ---------------------------------------------------------

def split(pilot_path, returned, baseline, corpus, collected_on):
    """Draw the subsets for the returned documents and lay out the corpus folder.

    Only file names and the SHA-256 of their bytes are read. The corpus folder
    must be outside this repository, because half of it is sealed; the draw is
    written to ``split.json`` and is never drawn again over different files.
    """
    import shutil
    pilot = json.loads(Path(pilot_path).read_text(encoding="utf-8"))
    # One language per corpus (§37 of cycle 7): the pilot declares it, and the
    # corpus manifest carries it and its own version.
    language = vc.corpus_language(pilot)
    returned = Path(returned)
    received = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(returned.glob("*.docx")) if not path.name.startswith("~$")}
    if not received:
        raise SystemExit(f"No returned .docx in {returned}.")
    corpus = vc.check_outside(corpus, "sealed")
    drawn = vc.draw_split(pilot, received, baseline)
    record = corpus / "split.json"
    if record.exists() and json.loads(record.read_text(encoding="utf-8"))["seed"] != drawn["seed"]:
        raise SystemExit(f"{record} already holds a draw over other files: the split is drawn once. "
                         "A late document joins its physician's subset (validation/pilot_v1/SPLIT_PROCEDURE.md).")
    for subset in vc.SUBSETS:
        (corpus / subset).mkdir(parents=True, exist_ok=True)
    for item in drawn["documents"]:
        shutil.copyfile(returned / item["file"], corpus / item["subset"] / item["file"])
    _write_json(record, {**drawn, "drawn_on": date.today().isoformat()})
    manifest = {"corpus_version": vc.CORPUS_VERSIONS[language], "language": language, "pilot_id": pilot["pilot_id"],
                "baseline_commit": drawn["baseline_commit"], "cases": pilot["cases"],
                "documents": [{"file": item["file"], "participant": item["participant"], "case": item["case"],
                               "language": item["language"], "collected_on": collected_on,
                               "subset": item["subset"], "sha256": item["sha256"]}
                              for item in drawn["documents"]],
                "retired_entries": []}
    _write_json(corpus / "manifest.json", manifest)
    return drawn


# --- the engine --------------------------------------------------------------------------

def engine_version():
    """The code that read the entries: commit, whether it had local changes, and the app's version."""
    def git(*args):
        found = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
        return found.stdout.strip() if found.returncode == 0 else None
    import tools_tanda20
    return {"commit": git("rev-parse", "HEAD"),
            "uncommitted_changes": bool(git("status", "--porcelain", "--untracked-files=no")),
            "simulator_version": tools_tanda20._app_constant("SIMULATOR_VERSION")}


def challenge_for(case_id):
    """A Decision Challenge that launches this case's family: the first by identifier.

    The reader does not depend on the challenge; the page needs one to open.
    """
    from clinical_cases import FAMILIES
    from curriculum import CHALLENGES
    family = next(name for name, definition in FAMILIES.items()
                  if any(case["id"] == case_id for case in definition.get("variants", [])))
    return family, next(key for key in sorted(CHALLENGES) if family in (CHALLENGES[key].get("families") or ()))


def outcomes(result, entries):
    """What the page said and held for each entry, from the rehearsal's steps.

    A held order is resolved by the rehearsal itself: an order held for its
    reasoning is completed with the rehearsal's neutral answers (recorded as
    completed, never as stated), and an order held for a clarification is
    cancelled -- nobody is there to answer.
    """
    steps = result.get("steps") or []
    orders = [index for index, step in enumerate(steps) if step["step"][0] == "order"]
    found = {}
    for position, entry in enumerate(entries):
        if position >= len(orders):
            found[entry["entry_id"]] = {"played": False}
            continue
        index = orders[position]
        step = steps[index]
        resolution = []
        for later in steps[index + 1:]:
            if later["step"][0] not in ("auto-complete", "auto-cancel"):
                break
            resolution.append(later["step"][0])
        found[entry["entry_id"]] = {"played": True, "held": step.get("held"), "said": step.get("said") or [],
                                    "resolution": resolution or None}
    return found


def play(corpus, out, seed=3000):
    """Every document of the subset through the real page, one encounter each."""
    if {"OPENAI_API_KEY", "ANTHROPIC_API_KEY"} & set(os.environ):
        raise SystemExit("A provider key is set: the validation reading must not be able to spend.")
    os.environ["MRS_OFFLINE_CASES"] = "1"
    import tools_order_reading
    import tools_tanda20
    workdir = Path(out) / "db"
    # Each run starts from empty rehearsal databases: an earlier run's account
    # would otherwise already be registered.
    for stale in workdir.glob("rehearsal-*.sqlite3*"):
        stale.unlink()
    records, documents = {}, []
    for number, document in enumerate(corpus["documents"], start=1):
        entries = [entry for _, entry in vc.entries_of({"documents": [document]})]
        family, challenge = challenge_for(document["bank_case"])
        script = {"number": number, "case_id": document["bank_case"], "family": family,
                  "category": "validation", "challenge": challenge, "intent": "validation corpus reading",
                  "language": document["language"], "steps": [("order", entry["text"]) for entry in entries],
                  "resolve_until_clear": True,
                  "reflection": {}, "plan": {}, "comparison": {"alignment": NEUTRAL, "adjustment": NEUTRAL}}
        result = tools_tanda20.rehearse(script, workdir, seed=seed)
        stored = tools_order_reading.stored_encounter(workdir / f"rehearsal-{number:02d}.sqlite3") or {}
        matched, unmatched = vc.align(entries, stored.get("trace") or [])
        said = outcomes(result, entries)
        for entry in entries:
            records[entry["entry_id"]] = {**said[entry["entry_id"]], "trace": matched[entry["entry_id"]]}
        documents.append({"file": document["file"], "bank_case": document["bank_case"], "challenge": challenge,
                          "stopped": result.get("stopped"), "seconds": result.get("seconds"),
                          "ai_calls_spent": stored.get("ai_calls_spent"),
                          "unmatched_trace_entries": len(unmatched)})
        # A page's error can quote what was typed: for the sealed subset only
        # the fact that it stopped leaves the output folder.
        stop = result.get("stopped")
        print(f"{document['file']}: {len(entries)} entries, {result.get('seconds')} s"
              + ((", stopped" if corpus["subset"] == "sealed" else f", stopped: {stop}") if stop else ""),
              flush=True)
    return {"corpus_version": corpus["corpus_version"], "subset": corpus["subset"],
            "engine": engine_version(), "seed": seed, "run_on": date.today().isoformat(),
            "documents": documents, "entries": records}


# --- files ---------------------------------------------------------------------------------

def _load(out, name):
    path = Path(out) / name
    if not path.exists():
        raise SystemExit(f"{path} does not exist yet: run the step that writes it first.")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def adjudicate(out, second=None):
    corpus, engine = _load(out, "entries.json"), _load(out, "engine_output.json")
    annotations = vc.read_csv(Path(out) / "annotation.csv")
    second_rows = vc.read_csv(second) if second else None
    rows = vc.adjudication_rows(corpus, engine["entries"], annotations, second_rows)
    disagreements = vc.agreement(annotations, second_rows)["disagreements"] if second_rows else {}
    path = Path(out) / "adjudication.csv"
    if path.exists():
        # A reviewer's work is kept when the sheet is made again.
        kept = {row["entry_id"]: row for row in vc.read_csv(path)}
        for row in rows:
            for column in vc.REVIEW_COLUMNS:
                if kept.get(row["entry_id"], {}).get(column):
                    row[column] = kept[row["entry_id"]][column]
    for row in rows:
        annotation_row = vc.annotation_of(row)
        review = vc.review_of(row) if annotation_row is not None else None
        if review is not None:
            view = vc.engine_view(engine["entries"].get(row["entry_id"]) or {})
            faithful = all(item["faithful"] for item in vc.fidelity(view, row["text"]))
            proposed, loci = vc.propose(annotation_row, view, review, faithful=faithful,
                                        disagreement=row["entry_id"] in disagreements)
            row["proposed_classification"] = proposed
            row["locus"] = row.get("locus") or "; ".join(loci)
    vc.write_csv(path, vc.ANNOTATION_COLUMNS + vc.ENGINE_COLUMNS + vc.REVIEW_COLUMNS, rows)
    return path


def _provenance(corpus, engine, rows):
    return {"corpus_version": corpus["corpus_version"], "subset": corpus["subset"],
            "subset_version": corpus["subset_version"], "source_type": corpus["source_type"],
            "template_versions": sorted({str(d.get("template_version")) for d in corpus["documents"]}),
            "annotation_versions": sorted({row.get("annotation_version") or "?" for row in rows}),
            "languages": sorted({d["language"] for d in corpus["documents"]}),
            "cases": sorted({d["case"] for d in corpus["documents"]}),
            "collection_dates": sorted({d["collected_on"] for d in corpus["documents"]}),
            "engine": engine["engine"], "seed": engine["seed"], "run_on": engine["run_on"],
            # Which baseline read the entries and which list of known defects its
            # errors are tagged against (faculty, 2026-09-28, §51): None for both
            # when the engine was not a registered baseline.
            **vc.baseline_of(engine["engine"]),
            "documents": len(corpus["documents"]), "retired_entries": len(corpus.get("retired_entries") or [])}


_TITLES = (("order_recognition_rate", "ORDER RECOGNITION RATE"),
           ("complete_interpretation_rate", "COMPLETE INTERPRETATION RATE"),
           ("partial_interpretation_rate", "PARTIAL INTERPRETATION RATE"),
           ("incorrect_execution_rate", "INCORRECT EXECUTION RATE"),
           ("unnecessary_clarification_rate", "UNNECESSARY CLARIFICATION RATE"),
           ("unnecessary_clarification_rate_orders_only", "  (orders only, without history/examination entries)"),
           ("trace_fidelity_rate", "TRACE FIDELITY RATE"),
           ("multi_order_success_rate", "MULTI-ORDER SUCCESS RATE"),
           ("reassessment_capture_rate", "REASSESSMENT CAPTURE RATE"),
           ("rationale_capture_rate", "RATIONALE CAPTURE RATE"),
           ("expectation_capture_rate", "EXPECTATION CAPTURE RATE"),
           ("contingency_capture_rate", "CONTINGENCY CAPTURE RATE"))


def markdown(report):
    lines = [f"# {report['provenance']['corpus_version']} · {report['provenance']['subset_version']}", "",
             "Deterministic reading of physicians' free text by the real page; no model was called. "
             "Counts, not inferences: a pilot's numbers do not carry intervals or tests.", "",
             "## Provenance", "", "```json", json.dumps(report["provenance"], indent=1, ensure_ascii=False), "```", ""]
    for language, values in sorted(report["metrics"].items()):
        lines += [f"## {'All languages' if language == 'all' else language.upper()}", "",
                  f"Entries {values['entries']} · not annotated {values['not_annotated']} · "
                  f"no clinical content {values['no_clinical_content']} · not adjudicated {values['not_adjudicated']} · "
                  f"adjudicated {values['adjudicated_entries']} · intended items {values['intended_items']} · "
                  f"reasoning-gate holds {values['reasoning_gate_holds']} · information-only entries "
                  f"{values['information_only_entries']}", "", "| Measure | n / N | Rate | Spurious |", "|---|---|---|---|"]
        for key, title in _TITLES:
            value = values[key]
            rate = "—" if value["rate"] is None else f"{value['rate']:.1%}"
            lines.append(f"| {title} | {value['n']} / {value['of']} | {rate} | {value.get('spurious', '')} |")
        lines += ["", "Classes: " + " · ".join(f"{name} {count}" for name, count in values["classes"].items()), ""]
    lines += [f"Proposals the reviewer changed: {report['overridden_proposals']}", ""]
    if report.get("traceability"):
        lines += ["## Traceability of every entry not classified CORRECT", "",
                  "| Case | Free text | Reference intent | Engine interpretation | Execution | Management Trace | "
                  "Classification | Locus | Impact | Known defect |", "|---|---|---|---|---|---|---|---|---|---|"]
        for row in report["traceability"]:
            cells = [row["case"], row["free_text"], row["reference_intent"], row["engine_interpretation"],
                     row["execution"], row["management_trace"], row["classification"], row["locus"],
                     row.get("impact") or "", row.get("known_defect") or ""]
            lines.append("| " + " | ".join(str(cell).replace("|", "/").replace("\n", " ") for cell in cells) + " |")
    return "\n".join(lines) + "\n"


def report(out, second=None):
    corpus, engine = _load(out, "entries.json"), _load(out, "engine_output.json")
    rows = vc.read_csv(Path(out) / "adjudication.csv")
    measured = vc.metrics(corpus, engine["entries"], rows, vc.read_csv(second) if second else None)
    result = {"provenance": _provenance(corpus, engine, rows), **measured}
    if second:
        result["annotation_agreement"] = {key: value for key, value in vc.agreement(rows, vc.read_csv(second)).items()
                                          if key != "disagreements"}
    _write_json(Path(out) / "report.json", result)
    (Path(out) / "report.md").write_text(markdown(result), encoding="utf-8")
    return result


def aggregates(result):
    """What may leave the output folder of a sealed run: numbers, never entries."""
    return {"provenance": result["provenance"], "metrics": result["metrics"],
            "overridden_proposals": result["overridden_proposals"],
            **({"annotation_agreement": result["annotation_agreement"]} if "annotation_agreement" in result else {})}


# --- command line ----------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("templates", help="write the blank Word documents")
    make.add_argument("--out", required=True)
    make.add_argument("--language", choices=("es", "en", "both"), default="both")
    make.add_argument("--case", action="append", help="a case code such as C01; all pilot cases if omitted")
    make.add_argument("--participant", default="", help="a participant code such as EM01 (optional)")
    make.add_argument("--pilot", help="a pilot manifest: every assigned document, one folder per physician")
    draw = commands.add_parser("split", help="draw development and sealed for the returned documents")
    draw.add_argument("--pilot", required=True, help="validation/pilot_v1/manifests/pilot_manifest.json")
    draw.add_argument("--returned", required=True, help="the folder with every returned .docx, unopened")
    draw.add_argument("--baseline", required=True, help="the pilot baseline commit (full SHA)")
    draw.add_argument("--corpus", required=True, help="the corpus folder to lay out, outside this repository")
    draw.add_argument("--collected-on", required=True, help="the date the last document came back, YYYY-MM-DD")
    take = commands.add_parser("ingest", help="read the returned documents of one subset")
    take.add_argument("--corpus", required=True, help="the corpus folder: manifest.json, development/, sealed/")
    take.add_argument("--subset", required=True, choices=sorted(vc.SUBSETS))
    take.add_argument("--out", required=True)
    for name, text in (("run", "read every entry through the real page"),
                       ("adjudicate", "put annotation and engine side by side"),
                       ("report", "measure and write the report")):
        command = commands.add_parser(name, help=text)
        command.add_argument("--out", required=True)
        if name == "run":
            command.add_argument("--seed", type=int, default=3000)
        else:
            command.add_argument("--second", help="a second, blind annotation of some entries")
    args = parser.parse_args(argv)

    if args.command == "templates" and args.pilot:
        for item in pilot_documents(args.pilot, args.out):
            print(f"{item['participant']}/{item['file']}  {item['sha256'][:12]}  {item['case_text']}")
        return 0
    if args.command == "templates":
        languages = ("es", "en") if args.language == "both" else (args.language,)
        for item in templates(args.out, languages, args.case, args.participant):
            print(f"{item['file']}  {item['sha256'][:12]}  {item['case_text']}")
        return 0
    if args.command == "split":
        drawn = split(args.pilot, args.returned, args.baseline, args.corpus, args.collected_on)
        print(json.dumps({"seed": drawn["seed"], "pairs": drawn["pairs"], "missing": drawn["missing"],
                          "documents": len(drawn["documents"])}, indent=1))
        return 0
    if args.command == "ingest":
        out = vc.check_outside(args.out, args.subset)
        out.mkdir(parents=True, exist_ok=True)
        corpus = vc.ingest(args.corpus, args.subset)
        _write_json(out / "entries.json", corpus)
        rows = vc.annotation_rows(corpus)
        vc.write_csv(out / "annotation.csv", vc.ANNOTATION_COLUMNS, rows)
        # The second clinician's blind sheet: a fixed fifth of each document (VC-2).
        second = set(vc.double_annotation_sample(corpus))
        vc.write_csv(out / "annotation_second.csv", vc.ANNOTATION_COLUMNS,
                     [row for row in rows if row["entry_id"] in second])
        warnings = [w for d in corpus["documents"] for w in d["warnings"]]
        print(f"{len(corpus['documents'])} documents, "
              f"{sum(1 for _ in vc.entries_of(corpus))} entries, {len(warnings)} warnings.")
        if args.subset != "sealed":
            for warning in warnings:
                print("  " + warning)
        return 0
    corpus = _load(args.out, "entries.json")
    vc.check_outside(args.out, corpus["subset"])
    sealed = corpus["subset"] == "sealed"
    if args.command == "run":
        engine = play(corpus, args.out, args.seed)
        _write_json(Path(args.out) / "engine_output.json", engine)
        print(json.dumps({"engine": engine["engine"], "documents": len(engine["documents"]),
                          "stopped": sum(1 for d in engine["documents"] if d["stopped"]),
                          "ai_calls_spent": sum(int(d["ai_calls_spent"] or 0) for d in engine["documents"])}, indent=1))
        return 0
    if args.command == "adjudicate":
        print(adjudicate(args.out, args.second))
        return 0
    result = report(args.out, args.second)
    print(json.dumps(aggregates(result) if sealed else {key: result[key] for key in ("provenance", "metrics")},
                     indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
