"""Phase 2 shadow core, P2G: the faculty calibration decision pack.

Decision support only: the pack reads P2F's admissible region, never selects or approves a
value, never changes a canonical default and never lets a CANDIDATE pass the migration gate.
"""
import hashlib
import json
from dataclasses import replace

import pytest

from clinical_core import calibration, decision_pack, gi_reference, migration
from clinical_core.derived import DEFAULT_PROFILE, CoreProfile
from clinical_core.migration import MigrationBlocked, check_migration_gate, gate_dry_run, migration_gate
from clinical_core.shadow import GOLDEN
from clinical_core.state import CASE_PARAMETERS

MIDDLE = decision_pack.MIDDLE


@pytest.fixture(scope="module")
def quick_pack():
    golden = hashlib.sha256(GOLDEN.read_bytes()).hexdigest()
    pack = decision_pack.report(quick=True)
    assert hashlib.sha256(GOLDEN.read_bytes()).hexdigest() == golden
    return pack


# The admissible region is P2F's, not a new one ---------------------------------------------------

def test_the_admissible_region_is_the_p2f_design_less_its_163_rejections():
    design = calibration.gi_candidates()
    rejected = [candidate for candidate in design if decision_pack.p2f_rejection(candidate)]
    assert len(design) == 1217 and len(rejected) == 163 and len(decision_pack.admissible()) == 1054


@pytest.mark.parametrize("candidate, rejected", [
    (MIDDLE, False),
    (replace(MIDDLE, preload="upper"), False),
    (replace(MIDDLE, profile={**MIDDLE.profile, "debt_clearance_tau_min": 30.0}, debt="midpoint"), False),
    (replace(MIDDLE, debt="upper", delivery="lower"), False),
    (replace(MIDDLE, profile={**MIDDLE.profile, "debt_clearance_tau_min": 30.0}, debt="upper",
             delivery="lower"), True),
    (replace(MIDDLE, preload="lower"), True),
])
def test_the_written_rejection_matches_the_frozen_acceptance(candidate, rejected):
    assert (decision_pack.p2f_rejection(candidate) is not None) is rejected
    assert (not calibration.gi_physiology(candidate)["valid"]) is rejected


# Decision support, never a choice ---------------------------------------------------------------

def test_the_pack_selects_ranks_and_approves_nothing(quick_pack):
    text = json.dumps(quick_pack, default=str).lower()
    for word in ("faculty_approved", "\"best", "\"selected", "\"recommended", "\"preferred", "\"rank"):
        assert word not in text
    assert DEFAULT_PROFILE == CoreProfile()
    assert DEFAULT_PROFILE.collapse_output_threshold is None and quick_pack["collapse"]["canonical_threshold"] is None
    assert quick_pack["freeze_digest"] == calibration.frozen_digest()


def test_low_middle_and_high_are_admissible_positions(quick_pack):
    for case in decision_pack.CASES:
        representatives = quick_pack["lactate"][case]["representatives"]
        assert representatives["middle"]["candidate"] == MIDDLE.key()
        for item in representatives.values():
            assert decision_pack.p2f_rejection(decision_pack._candidate(item["candidate"])) is None
        envelope = quick_pack["lactate"][case]["envelopes"]["untreated_120"][60]
        assert envelope["min"] <= representatives["middle"]["trajectories"]["untreated_120"][60] <= envelope["max"]


def test_heart_rate_is_intrinsic_plus_sympathetic_and_nothing_else(quick_pack):
    for case in decision_pack.CASES:
        for scenario in quick_pack["hr"][case]["scenarios"].values():
            for points in scenario["decomposition"].values():
                for point in points.values():
                    assert point["beta_factor"] == 1.0
                    assert abs(point["other_chronotropic_bpm"]) < 1e-9
                    assert point["hr"] >= point["intrinsic_bpm"] - 1e-9


def test_every_effect_row_says_whether_the_frozen_rules_admit_it(quick_pack):
    statuses = {decision_pack.ADMISSIBLE, decision_pack.REJECTED, decision_pack.NOT_ASSESSED,
                decision_pack.SENSITIVITY}
    for table in ("lactate", "hr", "rr"):
        for case in decision_pack.CASES:
            for rows in quick_pack[table][case]["effects"].values():
                assert rows and {row["status"] for row in rows} <= statuses
    rows = quick_pack["bp"]["gi_bleed_57m"]["effects"]["sbp"]
    assert {row["status"] for row in rows if row["factor"].startswith("bleeding source")} == {
        decision_pack.SENSITIVITY}
    assert {row["status"] for row in rows if row["factor"] == "preload_fraction" and row["level"] == "lower"} == {
        decision_pack.REJECTED}


def test_the_collapse_support_is_synthetic_and_canonical_gi_keeps_collapse_off(quick_pack):
    collapse = quick_pack["collapse"]
    assert collapse["terminal_rhythm_by_policy"] == {"pea": "pea", "asystole": "asystole"}
    assert collapse["patterns"]["transient moderate low flow (0.25 for 10 min)"]["arrest_minute"] is None
    assert collapse["patterns"]["profound low flow (0.1)"]["arrest_minute"] is not None
    repayment = collapse["repayment"]
    assert repayment["none"]["26 min at 0.15, 30 min recovered, 15 min at 0.15"]["arrest_minute"] is not None
    assert repayment["30"]["26 min at 0.15, 30 min recovered, 15 min at 0.15"]["arrest_minute"] is None


def test_pl2_fails_only_on_its_second_clause_and_reproduces_p2f(quick_pack):
    rows = quick_pack["pl2"]["rows"]
    assert all(row["clause_1_holds"] for row in rows)
    failing = {(row["arrival_preload_fraction"], round(row["preload_curve_scale_ml"]))
               for row in rows if row["in_registry_band"] and not row["clause_2_holds"]}
    assert failing == {(0.3, 600), (0.3, 833)}


def test_the_reachability_bound_would_exclude_exactly_the_hr1_rejections(quick_pack):
    reachability = quick_pack["reachability"]
    assert reachability["excluded_design_points"] == 162 and reachability["all_rejected_by_p2f"]


def test_the_preload_edge_empties_under_the_case_bleed_too(quick_pack):
    row = next(row for row in quick_pack["preload_edge"]["rows"]
               if row["preload_fraction"] == 0.2 and round(row["preload_curve_scale_ml"]) == 833)
    assert row["probe 8 mL/min"] is not None and row["case source 2.5 mL/min"] is not None
    assert row["probe 4 mL/min"] is None


@pytest.mark.parametrize("path, changes", [
    ("clinical_core/derived.py", True), ("clinical_core/integration.py", True),
    ("clinical_core/decision_pack.py", True), ("clinical_core/decision_pack_markdown.py", False)])
def test_the_pack_digest_covers_the_model_and_not_the_renderer(monkeypatch, path, changes):
    assert path in decision_pack.pack_sources() or path in decision_pack.PACK_DIGEST_EXCLUDED
    before = decision_pack.pack_digest()
    original = calibration._source_bytes
    monkeypatch.setattr(calibration, "_source_bytes",
                        lambda name: original(name) + (b"\n# changed\n" if name == path else b""))
    assert (decision_pack.pack_digest() != before) is changes


# P2G-14: nothing is approved, nothing migrates ---------------------------------------------------

def test_no_core_module_but_the_gate_and_its_vocabulary_writes_a_migratable_source():
    """The gate trusts the declared source; inside the core only the gate's own vocabulary names one.

    Nothing in the shadow core can label a CANDIDATE value as case truth or as an approved
    default. A caller outside the core still could: that limit is decision FD-41.
    """
    from pathlib import Path
    package = Path(decision_pack.__file__).resolve().parent
    writers = {path.relative_to(package).as_posix() for path in package.rglob("*.py")
               if any(label in path.read_text(encoding="utf-8") for label in migration.MIGRATABLE_SOURCES)}
    assert writers == {"state.py", "derived.py", "migration.py"}


def test_nothing_is_faculty_approved_and_no_family_default_is_recorded():
    assert sum(entry.status == calibration.FACULTY_APPROVED for entry in calibration.REGISTRY.values()) == 0
    assert migration.APPROVED_FAMILY_DEFAULTS == {}


@pytest.mark.parametrize("case", gi_reference.GI_CASES)
def test_gi_still_fails_the_gate_however_its_candidates_are_declared(case):
    assert gate_dry_run(case)["passes_gate"] is False
    values = decision_pack.calibration.case_values(case, MIDDLE)
    anchors = gi_reference.candidate_anchors(case, {**values, "beta_blockade": 0.0, "pump_reserve": 1.0})
    with pytest.raises(MigrationBlocked):
        check_migration_gate("gi_bleed", anchors)
    rows = migration_gate("gi_bleed", anchors)
    assert all(not row["migratable"] for name, row in rows.items() if name in CASE_PARAMETERS)
    # A CANDIDATE band value claimed as an approved family default is refused: none is recorded.
    claimed = {name: (entry.midpoint, "approved_family_default")
               for name, entry in calibration.REGISTRY.items() if name.startswith("gi_")}
    family = {name[len("gi_"):]: value for name, value in claimed.items()}
    rows = migration_gate("gi_bleed", anchors, family)
    assert not any(rows[name]["migratable"] for name in family)
    # The registry's status words are not provenance sources.
    with pytest.raises(MigrationBlocked):
        migration_gate("gi_bleed", anchors, {"volume_loss_ml_per_min": (2.5, calibration.CANDIDATE)})


# The faculty document --------------------------------------------------------------------------


def _document():
    from pathlib import Path
    root = Path(__file__).resolve().parent / "docs" / "revision"
    return ((root / "P2G_DECISIONES_DOCENTES_CALIBRACION_GI.md").read_text(encoding="utf-8"),
            json.loads((root / "P2G_decision_pack.json").read_text(encoding="utf-8")))


def _rows(document: str, first_cell: str) -> list[list[str]]:
    return [[cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in document.splitlines() if line.startswith("| " + first_cell)]


def test_the_faculty_document_is_generated_from_the_current_code_and_freeze():
    from clinical_core import decision_pack_markdown
    document, pack = _document()
    assert pack["pack_digest"] == decision_pack.pack_digest(), "the pack is stale: regenerate it"
    assert pack["freeze_digest"] == calibration.frozen_digest() and not pack["quick"]
    assert pack["pack_digest"] in document and pack["freeze_digest"] in document
    assert decision_pack_markdown.apply(document, decision_pack_markdown.render(pack)) == document, (
        "the document's tables differ from the pack: run decision_pack_markdown --write")


def test_the_master_table_leaves_every_decision_open_and_covers_every_gate_blocker():
    document, _ = _document()
    rows = _rows(document, "FD-")
    ids = [row[0] for row in rows]
    assert ids == [f"FD-{number:02d}" for number in range(1, len(rows) + 1)]
    assert all(len(row) == 10 and row[8] == "" and row[9] == "ABIERTA" for row in rows)
    assert f"**Decisiones abiertas: {len(rows)}.**" in document
    table = "\n".join("|".join(row) for row in rows)
    for case in gi_reference.GI_CASES:
        for name in gate_dry_run(case)["blockers"]:
            assert f"`{name}`" in table, name
    assert "FACULTY_APPROVED" not in table


def test_every_registry_parameter_is_in_the_master_table_or_listed_out_of_scope_with_a_reason():
    document, _ = _document()
    table = "\n".join("|".join(row) for row in _rows(document, "FD-"))
    start = document.index("**Parámetros del registro fuera de esta tabla")
    outside = document[start:document.index("\n## ", start)]
    for name in calibration.REGISTRY:
        assert (f"`{name}`" in table) != (f"`{name}`" in outside), name
    for bullet in outside.split("\n- ")[1:]:
        assert bullet.startswith("`") and ": " in bullet, bullet


def test_the_a9_worksheet_lists_every_variable_with_its_type_and_no_tolerance():
    from clinical_core import a9
    document, _ = _document()
    rows = [row for row in _rows(document, "") if len(row) == 7 and row[0] in "ABCD" and row[0]]
    assert {row[1].strip("`") for row in rows} == set(a9.A9)
    for row in rows:
        variable = a9.A9[row[1].strip("`")]
        assert (row[2] == "sí") is variable.resident_visible and row[6] == "PENDIENTE"
        assert (row[0] == "D") is (not variable.resident_visible)


def test_the_family_default_table_uses_exact_names_and_allowed_categories():
    document, _ = _document()
    categories = ("SAFE_FAMILY_DEFAULT_CANDIDATE", "CASE_SPECIFIC_PREFERRED", "FACULTY_DECISION_REQUIRED")
    rows = [row for row in _rows(document, "`") if len(row) == 7]
    names = {row[0].split("`")[1] for row in rows}
    assert names == {"beta_blockade", "pump_reserve", *migration.FAMILY_GATES["gi_bleed"].family_parameters}
    assert all(row[6].startswith(categories) for row in rows)
    beta = next(row for row in rows if row[0].startswith("`beta_blockade`"))
    assert beta[6] == "FACULTY_DECISION_REQUIRED"
