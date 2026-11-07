"""P2X-3: the Phase-2 closure record, checked against the repository it describes.

The record (``docs/revision/P2X3_phase2_closure.json``) is the authoritative closure artifact and the
document ``docs/PHASE2_CLOSURE.md`` reads from it. Nothing here approves a clinical value: every field
these tests accept is recomputed from the live repository, so a record that drifts fails, and a record
that claims more than the repository holds fails too.

``problems`` is the executable closure check. ``test_a_mutated_record_is_rejected`` mutates the record
to show each class of claim can actually fail: no criterion here passes by construction.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from clinical_core import calibration, closure_guard as cg, decision_pack, lactate_slice, state, tone_domain

ROOT = Path(__file__).resolve().parent
RECORD = ROOT / "docs" / "revision" / "P2X3_phase2_closure.json"
DOCUMENT = ROOT / "docs" / "PHASE2_CLOSURE.md"
#: The four declarations the closure artifact may carry only if the repository backs each one.
DECLARATIONS = ("PHASE 2 CLOSED", "SHADOW PHYSIOLOGY ONLY", "NO RESIDENT-VISIBLE RUNTIME CHANGE",
                "PHASE 3 NOT STARTED")
#: What P2X-3 is allowed to touch: its own record, the documents, and this test.
CLOSURE_PATHS = ("docs/", "test_phase2_closure.py")


def _record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _sources() -> dict[str, str]:
    package = ROOT / "clinical_core"
    paths = sorted(path.relative_to(ROOT).as_posix() for path in package.rglob("*.py")
                   if "__pycache__" not in path.parts and path.is_file() and not path.name.startswith("."))
    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}


def _digest(sources: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(sources, sort_keys=True).encode("utf-8")).hexdigest()


def _git(*arguments: str) -> list[str]:
    result = subprocess.run(("git", *arguments), cwd=ROOT, capture_output=True, text=True, check=True)
    return [line for line in result.stdout.splitlines() if line.strip()]


def _closure_commit() -> str | None:
    """The commit that added the closure record, or None while P2X-3 is still uncommitted.

    The record describes the repository AT THAT COMMIT. Two of its claims are repository-wide -- what
    P2X-3 touched, and which application modules import the shadow package -- so they are read from that
    tree and not from whatever a later stage has in the working tree. Phase 3 (P3-1), authorized after
    this closure, puts one declared bridge module on the runtime side on purpose; reading these claims
    from the working tree would make the closure record of a finished stage fail because a later,
    separately authorized stage exists. The claims themselves are unchanged and still recomputed.
    """
    found = _git("log", "--diff-filter=A", "--format=%H", "--",
                 "docs/revision/P2X3_phase2_closure.json")
    return found[0] if found else None


def _touched() -> set[str]:
    """Every path P2X-3 adds or changes, in its own commit or, before it exists, in the working tree."""
    head = _record()["final_executable_head"]
    closure = _closure_commit()
    if closure is None:
        committed = _git("diff", "--name-only", f"{head}..HEAD")
        working = [line[3:].strip().strip('"') for line in _git("status", "--porcelain")]
        return {path for path in (*committed, *working) if path}
    return {path for path in _git("diff", "--name-only", f"{head}..{closure}") if path}


def _root_modules() -> list[tuple[str, str]]:
    """``(name, source)`` for every non-test root module, as of the closure commit when it exists."""
    closure = _closure_commit()
    if closure is None:
        return [(path.name, path.read_text(encoding="utf-8")) for path in sorted(ROOT.glob("*.py"))
                if not path.name.startswith("test_")]
    names = sorted(name for name in _git("ls-tree", "--name-only", closure)
                   if name.endswith(".py") and not name.startswith("test_"))
    import subprocess
    return [(name, subprocess.run(("git", "show", f"{closure}:{name}"), cwd=ROOT, capture_output=True,
                                  text=True, check=True).stdout) for name in names]


def _imports_the_shadow_package() -> list[str]:
    """Application modules that import the shadow package. ``clinical_core_defaults`` is not it."""
    offenders = []
    for name, source in _root_modules():
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import clinical_core ", "import clinical_core.", "from clinical_core ",
                                    "from clinical_core.")) or stripped in ("import clinical_core",):
                offenders.append(name)
                break
    return offenders


def problems(record: dict) -> list[str]:
    """Every closure claim that the repository does not back. Empty means the record holds."""
    found: list[str] = []
    sources = _sources()
    if record.get("branch") != "phase-2-clinical-core-shadow":
        found.append("the record names another branch")
    if record.get("sources") != sources:
        found.append("the source map is stale")
    if record.get("phase2_digest") != _digest(sources):
        found.append("the Phase-2 digest does not recompute")
    if record.get("clinical_core_modules") != len(sources):
        found.append("the module count is wrong")

    families = record.get("families", {})
    present = sorted(path.stem for path in (ROOT / "clinical_core" / "modules").glob("*.py")
                     if path.stem not in ("__init__", "rhythm_events"))
    if sorted(families) != present:
        found.append(f"the family inventory is not the migrated set {present}")
    for name, entry in families.items():
        for key in ("module", "migration"):
            if not (ROOT / entry[key]).is_file():
                found.append(f"{name}: {entry[key]} does not exist")
        for test in entry["tests"]:
            if not (ROOT / test).is_file():
                found.append(f"{name}: {test} does not exist")
        if not entry.get("mechanism") or not entry.get("packages"):
            found.append(f"{name}: no mechanism or no package is named")

    common = record.get("common_physiology", {})
    if common.get("channels") != [channel.name for channel in state.Channel]:
        found.append("the channel inventory is not the core's")
    for path in common.get("executable_core", ()):
        if not (ROOT / path).is_file():
            found.append(f"the executable core names {path}, which does not exist")

    registry = calibration.REGISTRY
    statuses: dict[str, int] = {}
    for entry in registry.values():
        statuses[entry.status] = statuses.get(entry.status, 0) + 1
    parameters = record.get("parameters", {})
    if parameters.get("registered") != len(registry) or parameters.get("by_status") != statuses:
        found.append("the parameter inventory does not recompute")
    if parameters.get("faculty_approved") != statuses.get("FACULTY_APPROVED", 0):
        found.append("the approved-parameter count is wrong")
    if statuses.get("FACULTY_APPROVED", 0):
        found.append("a clinical magnitude is approved: closing Phase 2 must not need one")

    debt = {name: dict(entries) for name, entries in record.get("debt", {}).items()}
    if debt != {name: dict(entries) for name, entries in cg.DEBT.items()}:
        found.append("the debt inventory is not the classified one")
    identifiers = [name for entries in debt.values() for name in entries]
    if len(identifiers) != len(set(identifiers)):
        found.append("a debt is classified twice")
    if set(identifiers) != set(cg.REQUIRED_DEBT) or sorted(record.get("debt_required", ())) != sorted(cg.REQUIRED_DEBT):
        found.append("the classified debt is not the debt closure requires")
    blockers = {name: list(probes) for name, probes in cg.CLOSURE_BLOCKERS.items()}
    if {name: list(probes) for name, probes in record.get("closure_blockers_now_covered", {}).items()} != blockers:
        found.append("the closure blockers are not the ones the guard covers")
    if set(blockers) & set(identifiers):
        found.append("an active closure blocker is classified as nonblocking debt")

    if sorted(record.get("supersession", ())) != sorted(cg.HISTORY):
        found.append("the supersession history is not the guard's")

    digests = {"calibration": calibration.frozen_digest(), "closure_guard_P2X1A": cg.freeze_digest(),
               "tone_domain_on_the_live_tree": tone_domain.freeze_digest(),
               "lactate_slice": lactate_slice.slice_digest(), "decision_pack": decision_pack.pack_digest()}
    if record.get("freeze_digests") != digests:
        found.append("a freeze digest does not recompute")

    guard = json.loads((ROOT / "docs" / "revision" / "P2X1A_closure_guard.json").read_text(encoding="utf-8"))
    readiness = record.get("readiness", {})
    if readiness.get("P2X-1A") != guard["readiness"]["verdict"]:
        found.append("the recorded P2X-1A verdict is not the one its record carries")
    if readiness.get("P2X-1A") != "PHASE2_DECLARED_PROPERTIES_CLOSED":
        found.append("P2X-1A did not close the declared properties")
    if readiness.get("P2X-2") != "PHASE2_READY_FOR_FINAL_FREEZE":
        found.append("the exit audit did not return READY")
    if readiness.get("probes") != len(guard["probes"]) or readiness.get("criteria") != len(
            guard["readiness"]["criteria"]):
        found.append("the probe or criterion count is wrong")

    offenders = _imports_the_shadow_package()
    if record.get("isolation", {}).get("app_modules_importing_the_shadow_package") != offenders:
        found.append("the isolation claim does not recompute")
    runtime = record.get("runtime_status", {})
    if offenders and not runtime.get("integrated_at_runtime"):
        found.append(f"the shadow package is imported by {offenders}")
    if runtime.get("source_of_truth") != "family_engine.py" or not (ROOT / "family_engine.py").is_file():
        found.append("the runtime source of truth is not the legacy engine")
    if runtime.get("integrated_at_runtime") or runtime.get("resident_visible_change") or runtime.get(
            "phase_3_started"):
        found.append("the record claims runtime integration, a resident-visible change or Phase 3")

    touched = _touched()
    outside = sorted(path for path in touched
                     if not path.startswith(CLOSURE_PATHS[0]) and path not in CLOSURE_PATHS[1:])
    if outside:
        found.append(f"P2X-3 touches more than documentation and its test: {outside}")
    if "docs/revision/P2X3_phase2_closure.json" not in touched:
        found.append("the closure record is neither committed by this package nor in the working tree")

    declarations = record.get("declarations", {})
    if sorted(declarations) != sorted(DECLARATIONS) or not all(declarations.values()):
        found.append("the four closure declarations are not all stated")
    return found


def test_the_closure_record_holds_against_the_repository():
    assert problems(_record()) == []


def test_a_mutated_record_is_rejected():
    """Each class of claim must be able to fail: no criterion passes by construction."""
    mutations = {
        "digest": lambda record: record.update(phase2_digest="0" * 64),
        "source map": lambda record: record["sources"].pop(next(iter(record["sources"]))),
        "module count": lambda record: record.update(clinical_core_modules=1),
        "family": lambda record: record["families"].pop("opioid"),
        "family file": lambda record: record["families"]["asthma"].update(module="clinical_core/modules/none.py"),
        "channel": lambda record: record["common_physiology"]["channels"].append("Z"),
        "parameters": lambda record: record["parameters"].update(registered=0),
        "approved parameter": lambda record: record["parameters"].update(faculty_approved=1),
        "debt": lambda record: record["debt"]["FUTURE_RESEARCH_DEBT"].pop("PLASMA_LEAK"),
        "required debt": lambda record: record["debt_required"].pop(),
        "blocker as debt": lambda record: record["debt"]["ACCEPTABLE_PHASE2_DEBT"].update(
            P2X1_R_F1_CONDITIONAL_T_OWNERSHIP="TD-127"),
        "supersession": lambda record: record["supersession"].pop(),
        "freeze digest": lambda record: record["freeze_digests"].update(calibration="0" * 64),
        "verdict": lambda record: record["readiness"].update({"P2X-1A": "PHASE2_DECLARED_PROPERTIES_NOT_CLOSED"}),
        "exit verdict": lambda record: record["readiness"].update({"P2X-2": "PHASE2_NOT_READY_FOR_FINAL_FREEZE"}),
        "isolation": lambda record: record["isolation"].update(
            app_modules_importing_the_shadow_package=["streamlit_app.py"]),
        "runtime": lambda record: record["runtime_status"].update(integrated_at_runtime=True),
        "resident": lambda record: record["runtime_status"].update(resident_visible_change=True),
        "phase 3": lambda record: record["runtime_status"].update(phase_3_started=True),
        "declaration": lambda record: record["declarations"].update({"PHASE 2 CLOSED": False}),
        "branch": lambda record: record.update(branch="main"),
    }
    for name, mutate in mutations.items():
        record = _record()
        mutate(record)
        assert problems(record), f"a record with a broken {name} was accepted"


def test_the_executable_core_is_what_the_integration_step_loads():
    """The shadow core that runs is five modules; everything else in the package is analysis or presentation."""
    code = ("import sys, clinical_core.integration;"
            "print('\\n'.join(sorted(m for m in sys.modules if m.startswith('clinical_core'))))")
    loaded = subprocess.run((sys.executable, "-c", code), cwd=ROOT, capture_output=True, text=True, check=True)
    modules = {name.replace("clinical_core.", "").replace("clinical_core", "__init__") + ".py"
               for name in loaded.stdout.split()}
    recorded = {Path(path).name for path in _record()["common_physiology"]["executable_core"]}
    assert modules == recorded, (modules, recorded)


def test_the_document_reads_from_the_record():
    record = _record()
    document = DOCUMENT.read_text(encoding="utf-8")
    assert record["phase2_digest"] in document and record["final_executable_head"][:10] in document
    assert record["branch"] in document
    for declaration in DECLARATIONS:
        assert declaration in document, declaration
    for name in record["families"]:
        assert name in document, name
    for identifier in record["debt_required"]:
        assert identifier in document, identifier


def test_the_closure_document_states_what_the_closure_does_not_include():
    """The three limits in the document's own words: a closure record that drops one of them fails here."""
    document = DOCUMENT.read_text(encoding="utf-8")
    for sentence in ("PHASE 3 NOT STARTED", "no se integra en tiempo de ejecución",
                     "no cambia lo que ve el residente", "la Fase 3 no está iniciada"):
        assert sentence in document, sentence
