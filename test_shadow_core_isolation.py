"""Phase 2 shadow core: the core can never change what a resident sees.

- No module the application runs imports ``clinical_core``.
- ``clinical_core`` imports nothing that touches the session, the Trace, receipts,
  persistence or the page; only its legacy adapter reads the family engine, and only
  through copies. Its Contracts v2 adapters import ``contracts_v2``; the runtime, which also
  imports ``contracts_v2``, still never reaches ``clinical_core``.
- A legacy run is identical with and without the shadow run after it, and nothing the
  shadow is given is changed.
"""
import ast
from copy import deepcopy
from pathlib import Path

import pytest

import family_engine
from clinical_core import AUTHORITATIVE_ENGINE, SHADOW_ONLY
from clinical_core.legacy_adapter import (anchors_from_legacy, bank_case, contributors_from_legacy, run_legacy,
                                          snapshot)
from clinical_core.shadow import SCENARIOS, main, run_shadow
from clinical_core.state import digest

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "clinical_core"
#: What each core file may import besides the standard library and the package itself.
LEGACY_READERS = {"legacy_adapter.py": {"family_engine", "family_parser", "cognitive_catalog", "cognitive_generator"},
                  "shadow.py": {"family_engine"},
                  "contracts_input.py": {"contracts_v2"},
                  "contracts_output.py": {"contracts_v2"},
                  "contracts_legacy.py": {"contracts_v2", "pilot_acceptance"},
                  "contracts_shadow.py": {"family_engine"},
                  # P2F-2: reads the GI cases' repository truth, read-only and offline.
                  "gi_reference.py": {"clinical_cases"},
                  # P2N-2: the ACS reference reads acs_70f_left_main's repository truth, read-only and offline.
                  "acs_reference.py": {"clinical_cases"},
                  # P2P-1: the edema reference reads pulmonary_edema_58m's repository truth, read-only and offline.
                  "edema_reference.py": {"clinical_cases"},
                  # P2Q-2: the embolism reference reads the two PE cases' repository truth, read-only and offline.
                  "embolism_reference.py": {"clinical_cases"},
                  # P2S-2: the mechanics analysis reads nine cases' authored RR and blood gas, as diagnostics only,
                  # read-only and offline.
                  "respiratory_mechanics.py": {"clinical_cases"},
                  # P2S-3: the asthma reference reads asthma_49m's and asthma_24f's repository truth, read-only and offline.
                  "asthma_reference.py": {"clinical_cases"},
                  # P2T-1: the distress analysis reads the four respiratory families' authored work of breathing, as
                  # ordering evidence only, read-only and offline.
                  "respiratory_distress.py": {"clinical_cases"},
                  # P2T-3: the asthma distress migration reads the cross-family cases' authored respiratory evidence, RR,
                  # HR and blood gas, as region constraints only, read-only and offline.
                  "asthma_distress_migration.py": {"clinical_cases"},
                  # P2T-5: the oxygenation link analysis reads every variant's authored PaO2 / SpO2 pair, as a coherence
                  # check of the standard dissociation relation only (nothing fitted), read-only and offline.
                  "oxygenation_link.py": {"clinical_cases"},
                  # P2U-1: the opioid reference and its analysis read the two opioid cases' authored truth, read-only
                  # and offline, as every family mapping does.
                  "opioid_reference.py": {"clinical_cases"},
                  "opioid_migration.py": {"clinical_cases"},
                  # P2H-0: the migration authority reads repository case truth itself, read-only.
                  "migration_authority.py": {"clinical_cases"}}
#: The live runtime: the page, the engine, the reader, the submission guard and the order path.
RUNTIME_ROOTS = ("app", "family_engine", "family_parser", "submission_guard", "order_pipeline")
STDLIB = {"__future__", "argparse", "ast", "copy", "dataclasses", "enum", "functools", "hashlib", "inspect",
          "itertools", "json", "math", "pathlib", "typing"}
#: Standard-library modules one offline analysis file may use besides STDLIB.
ANALYSIS_ONLY = {
    # P2I-2AI: the offline analysis CLI parallelizes its run (--workers); nothing the application runs imports it.
    "arrival_severity.py": {"multiprocessing"},
    # P2J-4: the offline baroreflex analysis takes medians and a Pearson correlation of its own readings; nothing the
    # application runs imports it.
    "baroreflex.py": {"statistics"},
    # P2K-1: the offline RR audit lists the files that name W (re) and evaluates the RR function on a bare W holder
    # (types.SimpleNamespace); nothing the application runs imports it.
    "rr_audit.py": {"re", "types"},
    # P2K-5: the offline monotonicity closure proves its rule with exact rationals (fractions.Fraction); nothing the
    # application runs imports it.
    "respiratory_monotonicity.py": {"fractions"},
    # P2P-2: the offline D8 probe runs the P2P-1 derived.py (proven by the reversal) beside the live one as its own
    # module (types.ModuleType, registered in sys.modules for its dataclasses); nothing the application runs imports it.
    "respiratory_drive.py": {"sys", "types"},
    # P2S-2: the offline non-regression runs the P2Q-2 derived.py (proven by the reversal) beside the live one, as P2P-2's
    # D8 does; nothing the application runs imports it.
    "respiratory_mechanics.py": {"sys", "types"},
    # P2T-1: the offline non-regression runs the P2S-3 derived.py (proven by the reversal) beside the live one, as P2S-2's
    # does; nothing the application runs imports it.
    "respiratory_distress.py": {"sys", "types"},
    # P2V-1: the offline S10 probe runs the P2U-1 derived.py (proven by the reversal) beside the live one, as P2T-1's
    # non-regression does; nothing the application runs imports it.
    "systemic_stress.py": {"sys", "types"},
    # P2W-1: the same, for the distributive-tone analysis (its reversal proof and its view of the closed packages'
    # trees read module objects and the interpreter's path readers; the shadow core imports neither).
    "distributive_tone.py": {"sys", "types"},
    # P2X-1: the same, for the declared-property closure (its own view of the P2W-1 tree, installed locally so the
    # record can be produced outside a test, reads module objects and the interpreter's path readers).
    "tone_domain.py": {"sys", "types"},
    # P2X-1A's closure guard installs the same local view for the predecessor's own analysis.
    "closure_guard.py": {"sys", "types"}}


def _imports(path):
    names = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names.add((node.module or "").split(".")[0])
    return names


#: Phase 3, P3-1 (faculty authorization of 2026-11-07): the live encounter may run the closed common core
#: beside the legacy engine. ``runtime_shadow`` is the one declared bridge that crosses from the runtime to
#: the core. The ban below still holds for every other runtime module, and what the ban used to guarantee --
#: that the core cannot touch the encounter -- is now guaranteed by what the bridge cannot do: it holds no
#: authority, its flag is off unless a process sets it, and test_runtime_shadow_plumbing.py (R1-R17) shows
#: the authoritative record is byte-identical with it on and off.
SHADOW_BRIDGE = "runtime_shadow"
#: Phase 3, P3-19 (faculty authorization of 2026-11-07): the production authority call site is wired in, so
#: ``runtime_authority`` is a SECOND declared crossing -- ``app.py`` imports it, and it reaches the core to
#: evaluate the gate and to read the case. The invariant is reformulated, not weakened: the crossing is the
#: DECLARED LAYER (``LAYER_SOURCES``, pinned below), cutting that layer restores the Phase-2 isolation
#: exactly as before, and what the authority site may do is bounded by a gate no configuration can open.
DECLARED_CROSSINGS = frozenset({"runtime_shadow", "runtime_authority"})
#: The declared Phase-3 shadow layer, by exact name and from ONE declaration (``LAYER_SOURCES``): a new
#: module is not exempt because of its prefix, and the layer the artifacts' digest covers is the same layer
#: this ban exempts. ``runtime_shadow_evidence`` (P3-11) is the faculty/research harness: it reads the
#: layer and the acceptance battery, and no runtime module may read IT.
SHADOW_LAYER = frozenset(Path(name).stem for name in __import__("runtime_shadow").LAYER_SOURCES)
assert SHADOW_LAYER == {"runtime_shadow", "runtime_shadow_families", "runtime_shadow_evidence",
                        "runtime_authority", "runtime_authority_store"}, SHADOW_LAYER
assert DECLARED_CROSSINGS <= SHADOW_LAYER
HARNESS = "runtime_shadow_evidence"


def test_no_runtime_module_but_the_declared_shadow_bridge_imports_the_core():
    for path in ROOT.rglob("*.py"):
        relative = path.relative_to(ROOT)
        if relative.parts[0] in {"clinical_core", ".venv", ".claude"} or path.name.startswith("test_"):
            continue
        if path.stem in SHADOW_LAYER:
            continue
        assert "clinical_core" not in _imports(path), relative


def test_cutting_the_shadow_bridge_restores_the_phase2_isolation_exactly():
    """The bridge is the only crossing, it carries no authority, and only two modules use it."""
    import runtime_shadow
    assert "clinical_core" not in _reachable(RUNTIME_ROOTS, without=set(DECLARED_CROSSINGS)), \
        "the runtime reaches the core by a path that is not one of the declared crossings"
    assert runtime_shadow.COMMON_CORE_RUNTIME_AUTHORITY is False
    assert runtime_shadow.mode({}) == runtime_shadow.MODE_OFF
    users = sorted(path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*.py")
                   if path.relative_to(ROOT).parts[0] not in {".venv", ".claude"}
                   and not path.name.startswith("test_") and path.stem not in SHADOW_LAYER
                   and SHADOW_BRIDGE in _imports(path))
    assert users == ["app.py", "pilot_acceptance.py"], users
    # The second declared crossing has exactly ONE importer, and it is the orchestration helper in app.py.
    authority_users = sorted(path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*.py")
                             if path.relative_to(ROOT).parts[0] not in {".venv", ".claude"}
                             and not path.name.startswith("test_") and path.stem not in SHADOW_LAYER
                             and "runtime_authority" in _imports(path))
    assert authority_users == ["app.py"], authority_users
    import runtime_authority
    assert sorted(runtime_authority.APPROVED_SNAPSHOTS) == ["gi_pressure_committed"], \
        "the second crossing carries one development-only approval and nothing else"
    assert runtime_authority.site_for({}, {}) is None and runtime_authority.unreachable_because()
    # The layer itself is named, not matched by prefix: a future runtime_shadow_x.py is not exempt
    # unless the one declaration names it, and every declared source must exist on disk.
    globbed = {path.stem for path in ROOT.glob("runtime_shadow*.py")}
    assert not globbed - SHADOW_LAYER, sorted(globbed - SHADOW_LAYER)
    missing = sorted(stem for stem in SHADOW_LAYER if not (ROOT / f"{stem}.py").exists())
    assert missing == [], missing
    # The evidence harness is one-directional: the declared layer may read it (P3-15 reads the GI battery to
    # decide eligibility), and nothing outside that one declaration reads it, at module or at function level.
    harness_readers = sorted(path.name for path in ROOT.rglob("*.py")
                             if path.relative_to(ROOT).parts[0] not in {".venv", ".claude"}
                             and not path.name.startswith("test_") and path.stem not in SHADOW_LAYER
                             and HARNESS in _imports(path))
    assert harness_readers == [], harness_readers


def test_the_core_imports_only_what_a_shadow_needs():
    for path in PACKAGE.rglob("*.py"):
        imported = _imports(path) - STDLIB - {""}
        allowed = LEGACY_READERS.get(path.name, set()) | ANALYSIS_ONLY.get(path.name, set())
        assert imported <= allowed, (path.relative_to(ROOT), imported - allowed)
    assert SHADOW_ONLY is True and AUTHORITATIVE_ENGINE == "family_engine"


def _reachable(roots, without=()):
    """Every repository module the roots import, directly or not, at any depth or place.

    ``without`` cuts named modules out of the graph: it is how the one declared Phase-3 bridge is removed
    to show that the Phase-2 isolation holds exactly as it did without it.
    """
    modules = {path.stem: [path] for path in ROOT.glob("*.py")}
    modules.update({path.name: list(path.rglob("*.py")) for path in ROOT.iterdir()
                    if path.is_dir() and (path / "__init__.py").exists()})
    seen, pending = set(), list(roots)
    while pending:
        name = pending.pop()
        if name in seen or name not in modules or name in set(without):
            continue
        seen.add(name)
        for path in modules[name]:
            pending.extend(_imports(path) & set(modules))
    return seen


def test_contracts_v2_feeds_the_core_but_the_runtime_never_reaches_the_core():
    reached = _reachable(RUNTIME_ROOTS)
    assert {"app", "family_engine", "contracts_v2"} <= reached, "the runtime observes Contracts v2 in shadow"
    # Since P3-1 the runtime reaches the core through the declared crossings and nothing else; the test
    # above cuts them and shows this assertion holds exactly as it did in Phase 2.
    assert "clinical_core" not in _reachable(RUNTIME_ROOTS, without=set(DECLARED_CROSSINGS))
    # Cutting only the shadow bridge is no longer enough, and saying which module still crosses is the
    # honest form of the claim: it is the authority site, and it is the one app.py orchestrates.
    assert "clinical_core" in _reachable(RUNTIME_ROOTS, without={SHADOW_BRIDGE})
    assert "contracts_v2" in _imports(PACKAGE / "contracts_input.py")
    for path in (ROOT / "contracts_v2").rglob("*.py"):
        assert "clinical_core" not in _imports(path), path.name


def test_the_legacy_run_is_the_same_with_and_without_the_shadow():
    orders, minutes = SCENARIOS["definitive_management"]["orders"], SCENARIOS["definitive_management"]["minutes"]
    alone = run_legacy("gi_bleed_57m", orders, minutes)
    shadowed = run_shadow("gi_bleed_57m", "definitive_management")
    assert digest(list(alone.snapshots)) == digest(list(shadowed.legacy.snapshots))
    assert digest(_plain(alone.final_state)) == digest(_plain(shadowed.legacy.final_state))


def test_nothing_the_shadow_is_given_is_changed():
    state = bank_case("gi_bleed_72f")
    before = deepcopy(state)
    legacy = run_legacy("gi_bleed_72f", SCENARIOS["saline_then_blood"]["orders"], 40, state=state)
    assert state == before, "run_legacy works on its own copy of the encounter state"
    frozen = deepcopy(legacy)
    anchors_from_legacy(legacy.arrival)
    contributors_from_legacy(legacy)
    snapshot(legacy.final_state)
    assert legacy == frozen


def test_the_family_engine_s_tables_are_untouched_by_a_shadow_run():
    tables = {name: deepcopy(getattr(family_engine, name)) for name in ("GI_BLEED", "TRANSFUSION", "EDEMA")}
    run_shadow("gi_bleed_57m", "aggressive_volume")
    assert all(getattr(family_engine, name) == table for name, table in tables.items())


def test_the_comparison_writes_nothing_it_is_not_asked_to(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    golden = PACKAGE / "golden" / "gi_bleed_shadow.json"
    stamp = golden.stat().st_mtime_ns
    assert main([]) == 0
    assert list(tmp_path.iterdir()) == [] and golden.stat().st_mtime_ns == stamp
    assert "mismatching" in capsys.readouterr().out


def _plain(value):
    """The encounter state as JSON-serializable data, for a digest."""
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_plain(item) for item in value)
    if isinstance(value, float) and value != value:
        pytest.fail("NaN in the encounter state")
    return value
