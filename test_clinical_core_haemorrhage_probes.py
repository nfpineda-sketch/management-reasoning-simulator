"""Phase 2 shadow core, P2I-2S: haemorrhage / preload scale calibration constraints (read-only).

V stays an internal effective-preload coordinate; these tests pin what the probes report about the
haemorrhage, transfusion and crystalloid mappings and about the scale / position grid.

Since P2I-2T the committed probes are the historical record of the core before the shared blood
state: what they recorded about the old drifts is checked on the committed JSON, and the current
core's opposite behaviour in test_clinical_core_shared_haemorrhage.py.
"""
import ast
import json
import math
from pathlib import Path

import pytest

from clinical_core import haemorrhage_probes as hz, hemodynamic_probes as hp
from clinical_core.derived import DEFAULT_PROFILE, OXYGEN_CRITICAL

ROOT = Path(__file__).resolve().parent
DOCUMENT = ROOT / "docs" / "revision" / "P2I2S_ESCALA_HEMORRAGIA_PRECARGA.md"
DATA = ROOT / "docs" / "revision" / "P2I2S_haemorrhage_probes.json"


def _recorded():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_the_audit_recorded_two_independent_drifts_before_p2i2t():
    """The record: the pre-P2I-2T bleed moved V and Hb by two fixed literals sharing only the fraction."""
    for case in hz.CASES:
        bleed = _recorded()["audit"][case]["bleed"]
        assert (bleed["v_ml_eq_per_min"], bleed["hb_g_dl_per_min"]) == (2.5, 0.009)
        assert bleed["hb_per_v"] == pytest.approx(0.009 / 2.5)
        assert (bleed["fraction_with_ppi"], bleed["fraction_after_haemostasis"]) == (0.8, 0.1)
        assert bleed["v_loss"] == pytest.approx(300.0) and bleed["hb_fall"] == pytest.approx(1.08)
    # Those literals are references only now: the module has no Hb rate of its own.
    assert hz.LEGACY_HB_PER_MIN == 0.009 and not hasattr(hz._inputs()["bleed"], "hb_loss_g_dl_per_min")


@pytest.mark.parametrize("mixing", hz.MIXING_VOLUMES)
def test_the_discussion_analogue_reproduces_both_drifts_from_one_bleed(mixing):
    implied = hz.implied_bleed(6.7, 1.08, 300.0, mixing)
    blood, share = implied["blood_loss_ml"], implied["refilled_share"]
    assert (1.0 - share) * blood == pytest.approx(300.0)
    assert 6.7 * (mixing - blood) / (mixing - 300.0) == pytest.approx(6.7 - 1.08)
    assert implied["blood_loss_over_v_loss"] > 2.0


def test_the_audit_recorded_a_crystalloid_dilution_that_did_not_reverse():
    for case in hz.CASES:
        saline = _recorded()["audit"][case]["saline_2l"]
        assert saline["dilution_independent_of_leak"] is True and saline["hb_fall"] == pytest.approx(1.2)
        assert saline["v_retained_ml_eq"] < saline["v_peak_in_run_ml_eq"] < saline["v_gross_gain_ml_eq"]


def test_the_grid_is_ordered_and_its_regions_follow_their_criteria():
    rows = hz.grid()
    for scale in hz.SCALES:
        halves = [row["minutes_to_output"]["0.5"] for row in rows if row["scale"] == scale]
        assert halves == sorted(halves)
    for position in hz.POSITIONS:
        halves = [row["minutes_to_output"]["0.5"] for row in rows if row["position"] == position]
        assert halves == sorted(halves)
    rate = hz._inputs()["bleed"].blood_loss_ml_per_min
    for row in rows:
        small = row["points"]["small"]["output_rel"]
        sensitive = (small < hz.CLEARLY_TOO_SENSITIVE["output_below"]
                     or row["zero_flow_ml"] <= rate * hz.ANCHORS[hz.CLEARLY_TOO_SENSITIVE["zero_flow_before"]])
        insensitive = (not sensitive and row["points"][hz.CLEARLY_TOO_INSENSITIVE["anchor"]]["output_rel"]
                       > hz.CLEARLY_TOO_INSENSITIVE["output_above"])
        assert (row["region"] == "too sensitive by the probe's criterion") is sensitive
        assert (row["region"] == "too insensitive by the probe's criterion") is insensitive
        assert row["bleed_over_scale_per_min"] == pytest.approx(rate / row["scale"])


def test_the_response_requirements_on_the_recorded_trajectories():
    data = _recorded()["trajectories"]
    for scale in hz.TRAJECTORY_SCALES:
        normal, under = (data[f"{name}; {scale:g}"] for name in ("normal preload (0.70)", "underfilled (0.35)"))
        assert (normal["first_half_output"] or 10**6) > under["first_half_output"]           # requirement 5
        # Requirement 6 holds in absolute terms only (as reported): the weaker pump reaches the
        # critical boundary sooner; relative to its own output it is not less tolerant.
        weak = data[f"depressed pump (0.35, P to 0.7 by 10 min); {scale:g}"]
        assert weak["first_critical"] < under["first_critical"]


def test_the_response_requirements_still_hold_on_the_current_core():
    """Requirements 5 and 6 on today's core (with refill, P2I-2T): a run that never reaches the
    threshold within the window counts as later than any that does."""
    data = hz.trajectories()

    def at(value):
        return math.inf if value is None else value
    for scale in hz.TRAJECTORY_SCALES:
        normal, under = (data[f"{name}; {scale:g}"] for name in ("normal preload (0.70)", "underfilled (0.35)"))
        weak = data[f"depressed pump (0.35, P to 0.7 by 10 min); {scale:g}"]
        assert at(normal["first_half_output"]) >= at(under["first_half_output"])                 # requirement 5
        assert at(weak["first_critical"]) <= at(under["first_critical"])                       # requirement 6
        if under["first_half_output"] is not None:
            assert at(normal["first_half_output"]) > under["first_half_output"]
    canonical = hz.TRAJECTORY_SCALES[0]
    assert data[f"underfilled (0.35); {canonical:g}"]["first_half_output"] is not None, "the check is not vacuous"


def test_the_audit_recorded_lambda_as_a_unit_convention_for_v():
    """Recorded before P2I-2T. Since then V = kappa x the circulating-volume deviation, and the
    gauge is kappa together with lambda (test_clinical_core_shared_haemorrhage.py): scaling only the
    V inputs also changes the circulating volume and so Hb."""
    gauge = _recorded()["gauge"]
    assert gauge["largest_change_when_doubled"] == 0.0
    assert gauge["bleed_over_scale_per_min"] == pytest.approx(0.003)
    assert gauge["unit_over_scale"] == pytest.approx(0.36)
    # At a fixed distance to zero flow the loss response barely moves with lambda; the transfusion
    # response does (it reads the curvature).
    fixed = _recorded()["fixed_zero_flow"]
    halves = [item["minutes_to_half_output"] for item in fixed.values()]
    units = [item["output_after_two_units"] for item in fixed.values()]
    assert max(halves) - min(halves) < 10.0 and max(units) - min(units) > 0.5


def test_one_bleed_drives_both_in_the_prototype():
    no_refill = hz.coherent_prototype(hz.CASES[0], 2.5, None, 4000.0)
    assert {round(row["hb"], 9) for row in no_refill} == {6.7}            # whole blood lost: no dilution
    refill = hz.coherent_prototype(hz.CASES[0], 8.0, 60.0, 4000.0)
    assert refill[240]["hb"] < refill[120]["hb"] and refill[240]["V"] > refill[120]["V"]   # lag after the bleed stops


def test_transfusion_raises_both_and_its_output_effect_falls_with_scale_and_volume():
    data = hz.transfusion()
    for case in hz.CASES:
        outputs = {}
        for scale in hz.TRAJECTORY_SCALES:
            for volume in hz.UNIT_VOLUMES:
                item = data[f"{case}; 2 U; {scale:g}; {volume:g}"]
                assert item["after"]["hb"] > item["before"]["hb"] and item["after"]["do2"] > item["before"]["do2"]
                outputs[(scale, volume)] = item["after"]["output_rel"]
        for volume in hz.UNIT_VOLUMES:
            ordered = [outputs[(scale, volume)] for scale in sorted(hz.TRAJECTORY_SCALES)]
            assert ordered == sorted(ordered, reverse=True)
        for scale in hz.TRAJECTORY_SCALES:
            ordered = [outputs[(scale, volume)] for volume in sorted(hz.UNIT_VOLUMES)]
            assert ordered == sorted(ordered)


def test_the_probes_run_no_fd_lac_rule_and_change_nothing_canonical():
    tree = ast.parse(Path(hz.__file__).read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names}
    assert not imported & {"faculty_constraints", "lactate_constraints", "oxygen_probes"}
    assert DEFAULT_PROFILE.preload_curve_scale_ml == pytest.approx(300.0 / 0.36)
    assert DEFAULT_PROFILE.oxygen_extraction_reserve == 1.0


def test_the_probe_document_is_the_historical_record_before_p2i2t():
    """P2I-2T: the committed probes are the accepted record of the core before the shared blood
    state; they are stale by construction, labelled so, and never silently regenerated."""
    data = json.loads(DATA.read_text(encoding="utf-8"))
    document = DOCUMENT.read_text(encoding="utf-8")
    assert data["probes_digest"] == hz.HISTORICAL["probes_digest"] != hz.probes_digest()
    assert data["probes_digest"] in document and "REGISTRO HISTÓRICO, anterior a P2I-2T" in document
    assert hz.apply(document, hz.render(data)) == document, (
        "the document differs from the committed probes: run python -m clinical_core.haemorrhage_probes --write")
    with pytest.raises(SystemExit):
        hz.main(["--out", str(DATA.parent / "never-written")])
    assert not (DATA.parent / "never-written").exists()
