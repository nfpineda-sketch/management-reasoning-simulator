"""Phase 2 shadow core, P2I-2Q: haemodynamic plausibility before the lactate refilter (read-only).

The probes audit V -> effective preload -> output -> pressure -> oxygen delivery -> critical deficit
-> collapse. They change nothing canonical; these tests pin what they claim about the current form.
"""
import ast
import json
from pathlib import Path

import pytest

from clinical_core import decision_pack, hemodynamic_probes as hp, lactate_slice
from clinical_core.bands import Drift
from clinical_core.derived import DEFAULT_PROFILE, OXYGEN_CRITICAL
from clinical_core.integration import run

ROOT = Path(__file__).resolve().parent
DOCUMENT = ROOT / "docs" / "revision" / "P2I2Q_PLAUSIBILIDAD_HEMODINAMICA.md"
DATA = ROOT / "docs" / "revision" / "P2I2Q_hemodynamic_probes.json"


@pytest.mark.parametrize("position", [0.35, 0.45, 0.7])
def test_output_reaches_zero_exactly_at_the_zero_flow_distance(position):
    distance = hp.zero_flow_distance(position)
    assert hp._synthetic(position, 1.0, distance - 1.0)["output_rel"] > 0.0
    assert hp._synthetic(position, 1.0, distance + 1.0)["no_output"]


@pytest.mark.parametrize("position", [0.35, 0.7])
@pytest.mark.parametrize("pump", [1.0, 0.7])
def test_the_current_form_is_continuous_monotone_and_saturating(position, pump):
    losses = list(range(0, int(hp.zero_flow_distance(position)) - 5, 5))
    outputs = [hp._synthetic(position, pump, loss)["output_rel"] for loss in losses]
    steps = [before - after for before, after in zip(outputs, outputs[1:])]
    assert all(step > 0.0 for step in steps)                         # monotone: every loss lowers output
    assert max(steps) < 0.05                                          # no jump: 5 mL-eq never moves it 5 %
    assert all(later >= earlier - 1e-12 for earlier, later in zip(steps, steps[1:]))   # saturating


def test_responsiveness_is_state_dependent_and_a_weaker_pump_tolerates_less_loss_only_in_absolute_terms():
    low, high = (1.0 - hp._synthetic(position, 1.0, 100.0)["output_rel"] for position in (0.35, 0.7))
    assert low > 3 * high
    for coupling in hp.COUPLINGS:
        normal, weak = (hp.loss_to(0.35, pump, 1.0 / hp.RESERVE, pump_preload_coupling=coupling) for pump in (1.0, 0.7))
        assert weak < normal                                          # reaches the critical boundary sooner
    # As reported: relative to its own output a weaker pump is not less tolerant (c = 1 flattens its curve),
    # and P never moves the zero-flow point.
    own = [hp.loss_to(0.35, pump, 0.5, relative=True, pump_preload_coupling=1.0) for pump in (1.0, 0.7)]
    assert own[1] >= own[0]
    for pump in (1.0, 0.7):
        assert hp._synthetic(0.35, pump, hp.zero_flow_distance(0.35) + 1.0)["no_output"]


def test_the_audit_decomposes_output_and_counts_the_bleed():
    rows = hp.gi_rows(hp.CASES[0], hp.representative(), hp.UNTREATED)
    for row in rows:
        assert row["output_rel"] == pytest.approx(row["P"] * row["rhythm_factor"] * row["preload_rel"] * row["afterload"])
        assert row["lost_ml"] == pytest.approx(2.5 * row["minute"])
        assert row["filling_ml"] == pytest.approx(hp.zero_flow_distance(0.35) + row["V"])


def test_the_re_anchored_reading_keeps_the_canonical_debt_and_lactate():
    candidate = hp.representative()
    for case in hp.CASES:
        rows = hp.gi_rows(case, candidate, hp.UNTREATED)
        canonical = lactate_slice.slice_run(case, candidate, hp.UNTREATED)
        assert max(abs(row["D"] - value) for row, value in zip(rows, canonical["D"])) < 1e-9
        assert max(abs(row["lactate"] - value) for row, value in zip(rows, canonical["lactate"])) < 1e-9


def test_the_representative_is_an_admissible_member_of_the_committed_p2i2r_region():
    data = json.loads((ROOT / "docs" / "revision" / "P2I2_lactate_constraints.json").read_text(encoding="utf-8"))
    assert hp.REPRESENTATIVE_KEY in data["faculty_constrained_region"]
    assert hp.representative() in decision_pack.admissible()


def test_the_output_burden_is_the_cores_own_minute_by_minute():
    """With the core's collapse rule declared (a limit it never reaches), the probe's output burden
    is the core's aux.collapse_burden at every minute: same timing, same repayment."""
    anchors = hp.positioned(0.7)
    profile = hp._profile(collapse_output_threshold=hp.COLLAPSE["threshold"], collapse_burden_limit=1e9,
                          collapse_repayment_tau_min=hp.COLLAPSE["repayment_tau_min"],
                          collapse_burden_per_minute=hp.COLLAPSE["per_minute"])
    contributors = (Drift("fall", "P", 0, 40, -0.02), Drift("restore", "P", 40, 60, 0.03))
    result = run(anchors, contributors, 120, profile)
    rows = [hp._row(state, anchors, profile, hp.RESERVE, 0.0) for state in result.states]
    track = hp.burden_track(rows, "output")["track"]
    core = [state.aux.collapse_burden for state in result.states]
    assert max(core) > 1.0 and core[-1] < max(core)
    assert track == pytest.approx(core, abs=1e-12)


def test_the_collapse_signals_behave_as_reported():
    anaemia = hp.COLLAPSE_SCENARIOS["severe anaemia, output preserved: Hb 13 to 3 g/dL"]()
    assert anaemia[-1]["state"] == OXYGEN_CRITICAL and anaemia[-1]["output_rel"] == pytest.approx(1.0)
    assert hp.burden_track(anaemia, "output")["peak"] == 0.0 < hp.burden_track(anaemia, "oxygen_deficit")["peak"]
    recovery = hp.COLLAPSE_SCENARIOS["recovery: pump to 0.25 by 30 min, restored by 60"]()
    for signal in hp.SIGNALS:
        track = hp.burden_track(recovery, signal)
        assert (track["end"] < track["peak"] or track["peak"] == 0.0) and not any(track["reached"].values())
    # A stable patient held at the GI arrival (critical fraction 0.15, no bleeding): the raw deficit
    # signal still reaches a registry limit, the profound one never moves.
    held = hp.COLLAPSE_SCENARIOS["GI 57m held at arrival, no bleeding"]()
    assert {round(row["output_rel"], 9) for row in held} == {1.0}
    assert hp.burden_track(held, "oxygen_deficit")["reached"]["15"] is not None
    assert hp.burden_track(held, "profound_oxygen_deficit")["peak"] == 0.0


def test_the_pressure_relation_has_an_implicit_tone_and_a_knee():
    for item in hp.pressure_form().values():
        assert item["implied_resistance"]["0.5"] > 1.4 and item["slope_ratio"] > 2.5
    vasoconstricted = hp.pressure_as_perfusion()[-1]
    assert vasoconstricted["state"] == OXYGEN_CRITICAL and vasoconstricted["consciousness"] == 0


def test_the_probes_run_no_fd_lac_rule_and_change_nothing_canonical():
    tree = ast.parse(Path(hp.__file__).read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names}
    assert not imported & {"faculty_constraints", "lactate_constraints", "oxygen_probes"}
    assert DEFAULT_PROFILE.oxygen_extraction_reserve == 1.0
    assert DEFAULT_PROFILE.preload_curve_scale_ml == pytest.approx(300.0 / 0.36)


def test_the_probe_document_is_the_historical_record_before_p2i2t():
    """P2I-2T: the committed probes are the accepted record of the core before the shared blood
    state; they are stale by construction, labelled so, and never silently regenerated."""
    data = json.loads(DATA.read_text(encoding="utf-8"))
    document = DOCUMENT.read_text(encoding="utf-8")
    assert data["probes_digest"] == hp.HISTORICAL["probes_digest"] != hp.probes_digest()
    assert data["probes_digest"] in document and "REGISTRO HISTÓRICO, anterior a P2I-2T" in document
    assert hp.apply(document, hp.render(data)) == document, (
        "the document differs from the committed probes: run python -m clinical_core.hemodynamic_probes --write")
    with pytest.raises(SystemExit):
        hp.main(["--out", str(DATA.parent / "never-written")])
    assert not (DATA.parent / "never-written").exists()