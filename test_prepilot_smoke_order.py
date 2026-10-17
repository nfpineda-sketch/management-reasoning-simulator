"""Regressions from the deployed pre-pilot smoke encounter of 2026-10-11."""

from family_parser import parse_family_actions
from order_pipeline import open_turn


def action_types(parsed):
    return [a.get("type") for a in parsed.get("actions", []) if isinstance(a, dict)]


def test_monitoring_runs_without_a_false_not_understood_receipt():
    text = "Initiate continuous cardiac monitoring and pulse oximetry."
    parsed = parse_family_actions(text)
    assert "monitoring" in action_types(parsed)
    assert "clarification" not in action_types(parsed)
    turn = open_turn(text, parsed, submission_id="smoke-monitor", entry_point="free_text", minute=0, ledger=[])
    assert not [o for o in turn["orders"] if o.get("canonical") == "unrecognized"]


def test_bedside_assessment_words_are_reassessment_not_unknown_orders():
    parsed = parse_family_actions(
        "Assess airway, breathing, mental status, peripheral perfusion, and signs of shock."
    )
    kinds = action_types(parsed)
    assert kinds and set(kinds) == {"reassessment"}


def test_standalone_signs_of_shock_is_reassessment_not_clarification():
    for text in ("signs of shock", "shock signs", "signos de shock", "signos de choque"):
        parsed = parse_family_actions(text)
        kinds = action_types(parsed)
        assert kinds == ["reassessment"]
        assert "clarification" not in kinds


def test_preparing_pacing_does_not_start_pacing():
    parsed = parse_family_actions(
        "Prepare transcutaneous pacing pads and have pacing equipment ready if atropine is ineffective."
    )
    assert "transcutaneous_pacing" not in action_types(parsed)
    assert any(d.get("category") == "pacing_preparation" for d in parsed.get("future_details", []))


def test_serum_magnesium_is_a_diagnostic_request_not_magnesium_treatment():
    parsed = parse_family_actions("Obtain CBC, CMP, magnesium, troponin, and venous blood gas.")
    diagnostics = [a.get("diagnostic") for a in parsed.get("actions", []) if a.get("type") == "diagnostic"]
    assert {"basic_labs", "serum_magnesium", "troponin", "vbg"} <= set(diagnostics)
    assert "magnesium" not in action_types(parsed)


def test_atropin_with_chilean_ev_route_is_atropine_iv():
    parsed = parse_family_actions("Give atropin 1 mg EV.")
    actions = [a for a in parsed.get("actions", []) if a.get("type") == "atropine"]
    assert len(actions) == 1
    assert actions[0].get("route") == "IV"
    assert actions[0].get("dose_mg") == 1



def test_oxygen_saturation_reassessment_has_no_false_unrecognized_receipt():
    text = "Check oxygen saturation"
    parsed = parse_family_actions(text)
    assert action_types(parsed) == ["reassessment"]
    turn = open_turn(text, parsed, submission_id="smoke-spo2", entry_point="free_text", minute=0, ledger=[])
    assert not [o for o in turn["orders"] if o.get("canonical") == "unrecognized"]


def test_durable_pending_submission_skips_only_the_intermediate_render():
    import submission_guard

    session = {}
    submission_guard.log(session).append({
        "id": "smoke-fast-path",
        "form_id": "smoke-fast-path",
        "raw_text": "Reassess",
        "status": "received",
    })
    # The processing run emits no bedside. Once the entry is processed, the
    # result rerun renders the current bedside exactly once.
    assert submission_guard.pending(session)
    assert submission_guard.fast_path(session) is True
    session["submission_log"][0]["status"] = "processed"
    assert submission_guard.fast_path(session) is False
