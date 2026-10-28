"""Phase 2 shadow core, P2I-2AA: the crystalloid tau edge and the lactate-readiness semantics.

These tests pin that the faculty constraints, P2I-2Z's robust criterion and the closed records are unchanged, that
the tau extension is the faculty's (F0 0.20, Finf 0.05 and 0.10, tau 120 to 240 in steps of 30, nothing above 240)
frozen before evaluation, that the oxygen adequacy for lactate is effective_oxygen_deficit == 0 (never a return to
normal DO2), that the future lactate space keeps rates 2.5, 5 and 6, that the L3 modifiers stay fixed provisional
values without an invented range, that the source space cannot be consumed while readiness is not READY, and that no
lactate filter, legacy trajectory, SBP or MAP enters.
"""
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from clinical_core import blood_constraints as bc
from clinical_core import blood_fluid_calibration as fc
from clinical_core import blood_fluid_readiness as fr
from clinical_core import blood_fluid_tau_closure as tc
from clinical_core import decision_pack, lactate_slice
from clinical_core.derived import OXYGEN_ADEQUATE, OXYGEN_COMPENSATED, OXYGEN_CRITICAL, oxygen_balance

ROOT = Path(__file__).resolve().parent
#: The P2I-2AA freeze: design, limit, stop rule, practical-identifiability rule, adequacy, rates, L3 status, readiness
#: criteria, draft status, policy and every clinical_core source but the downstream reports, committed before any new
#: outcome was evaluated.
FROZEN_DIGEST = "263efababa2cee8110d682bc2f4a22d6218bce642cef6c3d3444a6de45dfdf16"
P2I2VR_CONSTRAINTS_SHA = "2d139733ed529a03f9c58cd4aa5eb70c8812bb25ba0737f90172546b4e2a65a8"
P2I2Z_MODULE_SHA = "40b93a69c8b70190e7d92a056f0987b81a30ee32331629d18132f0aa534a15cf"


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_the_faculty_constraints_and_the_closed_records_are_unchanged():
    assert _sha("clinical_core/blood_constraints.py") == P2I2VR_CONSTRAINTS_SHA
    assert _sha("clinical_core/blood_fluid_readiness.py") == P2I2Z_MODULE_SHA
    assert tc.record_p2i2z()["freeze_digest"] == tc.P2I2Z_DIGEST
    assert bc.DECISIONS["FD-BLD-04"]["envelope"] == (0.15, 0.30)
    assert bc.DECISIONS["FD-BLD-05"]["envelopes"] == {30: (0.15, 0.25), 60: (0.10, 0.20), 120: (0.05, 0.15)}
    assert bc.DECISIONS["FD-BLD-06"]["envelopes"] == {1000: (0.2, 0.5), 2000: (0.4, 0.8)}


def test_the_tau_closure_is_frozen():
    sources = fc.freeze_sources()
    assert {"clinical_core/blood_fluid_tau_closure.py", "clinical_core/blood_fluid_readiness.py",
            "clinical_core/blood_constraints.py", "clinical_core/interventions/fluids.py"} <= set(sources)
    assert not set(lactate_slice.DOWNSTREAM_REPORTS) & set(sources)
    assert tc.freeze_digest() == FROZEN_DIGEST, "a source, the design, a rule or the policy changed after the freeze"


def test_the_tau_design_is_the_faculty_s_and_stops_at_240():
    points = tc.design()
    assert len(points) == 10
    assert {p["F0"] for p in points} == {0.20} and {p["Finf"] for p in points} == {0.05, 0.10}
    assert sorted({p["tau"] for p in points}) == [120.0, 150.0, 180.0, 210.0, 240.0]
    assert tc.NEW_TAU == (150.0, 180.0, 210.0, 240.0) and tc.TAU_CAP == 240.0
    assert max(tc.GRIDS["tau"]) == 240.0 and tc.GRIDS["tau"] == (15.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0,
                                                                  240.0)
    assert all(p["status"] == fr.ACTIVE for p in points)
    assert tc.LIMIT == {"F0": 0.2, "Finf": 0.2, "tau": 240.0}
    assert fr.calibration_status(tc.LIMIT["F0"], tc.LIMIT["Finf"]) == fr.REFERENCE_ONLY


def test_the_boundary_and_practical_rules_never_identify_an_open_edge():
    classified = {f"0.2|{f:g}|{t:g}": {"robust": True} for f in (0.05, 0.1) for t in tc.TAU}
    open_edge = tc.tau_boundary(classified)
    assert open_edge["status"] == tc.OPEN_AT_CAP and open_edge["stop"] == tc.STOP
    edges = tc.region_edges(sorted(classified))
    assert edges["tau"]["upper_side"] == "OPEN" and edges["tau"]["identified"] is False
    closed = tc.tau_boundary({k: v for k, v in classified.items() if not k.endswith(("|210", "|240"))})
    assert closed["status"] == tc.CLOSED and closed["highest_surviving"] == 180.0
    assert closed["first_without_survivor"] == 210.0 and closed["interior_boundary"]


def test_oxygen_adequacy_is_no_deficit_never_normal_delivery():
    assert tc.ADEQUATE_STATES == (OXYGEN_ADEQUATE, OXYGEN_COMPENSATED)
    compensated = oxygen_balance(0.6, 1.0, 2.5)          # below normal DO2, met by extraction
    assert compensated.state == OXYGEN_COMPENSATED and tc.oxygen_adequate(compensated.effective_deficit)
    critical = oxygen_balance(0.3, 1.0, 2.5)
    assert critical.state == OXYGEN_CRITICAL and not tc.oxygen_adequate(critical.effective_deficit)
    assert tc.adequacy_consistency()["agree"]
    assert "effective_oxygen_deficit == 0" in tc.ADEQUACY_RULE and "does not require a return to normal" in \
        tc.ADEQUACY_RULE


def test_the_lactate_rates_keep_2_5_and_the_l3_modifiers_stay_fixed():
    assert tc.LACTATE_RATES == (2.5, 5.0, 6.0)
    audit = tc.l3_audit()
    for name, item in audit.items():
        assert item["committed_range"] is False and item["sensitivity_design"] is None, name
        assert item["status"] == ["FIXED_PROVISIONAL_FOR_PRIMARY_LACTATE_ANALYSIS", "FACULTY_DECISION_PENDING"]
    assert audit["gi_fraction_with_ppi"]["value"] == 0.8 and audit["gi_fraction_after_hemostasis"]["value"] == 0.1


def test_the_blood_key_checks_cover_the_explored_region_only():
    assert len(tc.rate25_keys()) == 36 and {k[1] for k in tc.rate25_keys()} == {2.5}
    keys = tc.explored_keys()
    assert len(keys) == 288 and {k[1] for k in keys} == {2.5, 5.0, 6.0}
    assert len(tc._old_crystalloids("P2I-2V-R")) == 27 and len(tc._old_crystalloids("P2I-2Y")) == 18


def test_the_structural_checks_support_the_factorized_design():
    summary = tc.structural_summary(tc.structural_checks())
    assert summary["rho_cancels_in_deficit_and_adequacy"]
    assert summary["delivery_level_never_reaches_haemodynamics"] and summary["delivery_level_moves_the_deficit"]


def test_the_source_space_cannot_be_consumed_unless_ready():
    draft = {"readiness": {"verdict": tc.NOT_READY}, "source_space": {"status": tc.DRAFT_STATUS}}
    with pytest.raises(ValueError, match="NOT EXECUTABLE"):
        tc.certified_input(draft)
    mixed = {"readiness": {"verdict": tc.READY}, "source_space": {"status": tc.DRAFT_STATUS}}
    with pytest.raises(ValueError):
        tc.certified_input(mixed)


def test_no_lactate_filter_legacy_pressure_or_probe_enters():
    tree = ast.parse((ROOT / "clinical_core" / "blood_fluid_tau_closure.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported |= {alias.name for alias in node.names} | {(node.module or "").split(".")[-1]}
        elif isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[-1] for alias in node.names}
    assert not imported & {"lactate_constraints", "faculty_constraints", "legacy_adapter", "family_engine",
                           "lactate_slice", "haemorrhage_probes", "hemodynamic_probes", "oxygen_probes", "decision_pack"}
    source = (ROOT / "clinical_core" / "blood_fluid_tau_closure.py").read_text(encoding="utf-8")
    assert '"sbp"' not in source and '"map"' not in source and "1054" not in source


def test_the_module_loads_no_family_engine_or_lactate_filter():
    code = ("import sys; import clinical_core.blood_fluid_tau_closure; "
            "print('family_engine' in sys.modules, 'clinical_core.faculty_constraints' in sys.modules, "
            "'clinical_core.lactate_constraints' in sys.modules)")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
    assert out.stdout.split() == ["False", "False", "False"]


def test_the_report_stays_downstream():
    assert "clinical_core/blood_fluid_tau_closure_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/blood_fluid_tau_closure.py", "clinical_core/blood_fluid_tau_closure_report.py"} <= set(
        decision_pack.PACK_DIGEST_EXCLUDED)
    assert "clinical_core/blood_fluid_tau_closure.py" in lactate_slice.slice_sources()


# After the freeze commit: the analysis's record --------------------------------------------------------------------

RESULT = ROOT / "docs" / "revision" / "P2I2AA_blood_fluid_tau_closure.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2I2AA_CIERRE_TAU_Y_SEMANTICA_LACTATO.md"


def _plain(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


@pytest.fixture(scope="module")
def result():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_the_record_carries_the_frozen_digest_and_design(result):
    assert result["freeze_digest"] == FROZEN_DIGEST and result["revision"] == "P2I-2AA"
    assert result["record"] == {"P2I-2Z": tc.P2I2Z_DIGEST, "P2I-2Y": fr.P2I2Y_DIGEST}
    assert result["design"] == _plain(tc.design()) and result["policy"] == tc.POLICY
    assert result["contradictions"] == [] and result["adequacy"]["rule"] == tc.ADEQUACY_RULE


def test_tau_120_reproduces_p2i2z_and_the_classification_is_recomputed(result):
    p2i2z, keys = tc.record_p2i2z(), fr.blood_keys(fr.record_p2i2y())
    assert tc.reproduces_p2i2z(result["evaluated"], p2i2z) == []
    assert result["classified"] == _plain(fr.classify(result["evaluated"], keys))
    assert result["region"] == tc.region(result["classified"], p2i2z)
    assert result["edges"] == _plain(tc.region_edges(result["region"]))
    assert result["boundary"] == _plain(tc.tau_boundary(result["classified"]))
    assert all(fr.calibration_status(*(float(v) for v in k.split("|")[:2])) == fr.ACTIVE for k in result["region"])


def test_fd_bld_04_and_05_are_recomputed_live_on_the_bag_alone(result):
    entries = {**result["evaluated"], tc._key(tc.LIMIT): result["limit"]}
    for key, entry in entries.items():
        f0, finf, tau = (float(v) for v in key.split("|"))
        for case in bc.CASES:
            row = bc.retained(case, fc.bag(f0, finf, tau))
            assert {n: bc.passes(n, case, row) for n in ("FD-BLD-04", "FD-BLD-05")} == entry["verdicts"][case], key


def test_fd_bld_06_is_recomputed_live_at_the_smallest_margins(result):
    from clinical_core import blood_rate_boundary as rb
    rows = rb.Rows()
    for point in tc.design():
        if not point["new"]:
            continue
        key = tc._key(point)
        fd06 = result["evaluated"][key]["fd06"]
        low = min(fd06, key=lambda b: min(fd06[b][c]["reading"]["1000"]["peak"] for c in bc.CASES))
        high = max(fd06, key=lambda b: max(fd06[b][c]["reading"]["2000"]["peak"] for c in bc.CASES))
        for label in {low, high}:
            values = fc._crystalloid_values(point, tuple(float(v) for v in label.split("|")))
            for case in bc.CASES:
                assert rows.verdict(case, "FD-BLD-06", values) is fd06[label][case]["pass"], (key, label, case)


def test_tau_stays_open_at_240_bounded_beyond_and_readiness_names_that_blocker(result):
    b = result["boundary"]
    assert b["status"] == tc.OPEN_AT_CAP and b["highest_surviving"] == 240.0 and b["stop"] == tc.STOP
    assert b["per_finf"]["0.1"]["highest"] == 150.0 and b["per_finf"]["0.1"]["first_failing"] == 180.0
    assert result["practical"]["classification"] == tc.BOUNDED_BEYOND
    assert result["practical"]["limit"]["verdicts"]["FD-BLD-05"] is False
    assert result["practical"] == _plain(tc.practical(result["evaluated"], result["limit"],
                                                      fr.blood_keys(fr.record_p2i2y()), tc.record_p2i2z(), b))
    assert result["readiness"]["verdict"] == tc.NOT_READY
    assert result["readiness"]["blockers"] == [tc.CRYSTALLOID_CRITERION]
    edges = result["edges"]["tau"]
    assert edges["upper_side"] == "OPEN" and edges["identified"] is False


def test_readiness_and_the_source_space_are_recomputed_from_the_record(result):
    p2i2z, p2i2y = tc.record_p2i2z(), fr.record_p2i2y()
    checks_z = fr.structural_checks()
    summary_z = fr.structural_summary(checks_z)
    assert _plain(summary_z) == result["structural"]["p2i2z_summary"]
    ready = tc.readiness(p2i2z, p2i2y, result["region"], result["edges"], result["boundary"], result["practical"],
                         result["rate25_compatibility"], result["completeness"], result["adequacy"]["grid"],
                         result["structural"]["summary"], checks_z, summary_z)
    assert _plain(ready) == result["readiness"]
    space = tc.source_space(p2i2y, result["region"], result["completeness"], result["structural"]["summary"],
                            summary_z, False, result["rate25_compatibility"])
    assert _plain(space) == result["source_space"] and space["status"] == tc.DRAFT_STATUS
    with pytest.raises(ValueError, match="NOT EXECUTABLE"):
        tc.certified_input(result)


def test_the_substitution_witnesses_and_rate_2_5_compatibility_hold_live(result):
    from clinical_core import blood_rate_boundary as rb
    rows = rb.Rows()
    complete = result["completeness"]
    assert complete["keys"] == 288 and complete["without_witness"] == []
    for label in sorted(complete["witness"])[::96]:         # three keys, one per stretch of the explored set
        effective, leak, transient = complete["witness"][label]
        values = {fc.EFFECTIVE: effective, fc.LEAK: leak, fc.TRANSIENT: transient,
                  **dict(zip(fc.PROBE_KEYS, (float(v) for v in label.split("|"))))}
        assert all(rows.verdict(case, "FD-BLD-06", values) is True for case in bc.CASES), label
    assert not any(result["rate25_compatibility"].values())
    assert sorted(result["rate25_compatibility"]) == sorted(result["region"])


def test_nothing_is_approved_selected_or_lactate_filtered(result):
    from clinical_core import calibration, migration_authority
    assert sum(entry.status == calibration.FACULTY_APPROVED for entry in calibration.REGISTRY.values()) == 0
    assert migration_authority.APPROVED_FAMILY_DEFAULTS == () and migration_authority.TRUSTED_CASE_MAPPINGS == ()
    import re
    text = json.dumps(result)
    # The adequacy rule names FD-LAC as the future reader; no FD-LAC constraint (FD-LAC-01..06) is ever evaluated.
    assert "selected" not in text and "best" not in text and not re.search(r"FD-LAC-\d", text)
    assert result["rates"]["lactate"] == [2.5, 5.0, 6.0]
    assert all(item["committed_range"] is False for item in result["l3"].values())


def test_the_document_blocks_are_generated(result):
    from clinical_core import blood_fluid_tau_closure_report as report
    document = DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        assert report.apply(document, name, render(result)) == document, name
    assert "1054" in document and "fisiología actual" in document and "TAU_REMAINS_OPEN_AT_240" in document
    assert "DRAFT — NOT EXECUTABLE UNTIL BLOOD/FLUID READINESS = READY" in document
