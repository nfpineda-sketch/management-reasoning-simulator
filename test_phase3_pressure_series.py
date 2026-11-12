"""P3-241, P3-242, P3-243, P3-245, P3-246 and P3-247: the FIRST REAL GI DEVELOPMENT PRESSURE AUTHORITY experiment, on the real page, both GI cases.

TEST-SIDE. Nothing is injected: the page runs with the authorized development configuration (the authority, snapshot and environment flags, the shadow in compare mode,
an artifact store), the REAL registered pressure approval ``gi_pressure_committed`` and the REAL explicit grant ``GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1``. Thirteen
management scenarios are played on each GI case through Streamlit's ``AppTest``, once with the pressure authority ON and once with it OFF (the shadow only), and the two are
compared at every step. The claims:

* the committed SBP/DBP/MAP are the COMMON authority's (equal to the recorded written candidate, different from the legacy value the OFF run shows wherever the two differ);
* nothing else of the resident's world moves: every non-pressure observable, the buttons, the order ledger, the events and (after closing) the whole session are equal modulo
  the pressure values themselves; ``mental_status`` is the legacy engine's at every step;
* the V1 consciousness overlay runs beside it and is recorded (legacy word, common category, F, relative delivery, collapse state) but written nowhere;
* the collapse boundary and the window stop the experiment BEFORE a minute beyond them is committed;
* every artifact verifies, replays (pressure, overlay, boundary, halt reason) and says it is a REAL development pressure artifact.

``MRS_WRITE_PRESSURE_SERIES=1`` regenerates ``docs/revision/PHASE3_PRESSURE_AUTHORITY_SERIES.json`` once, by the person who changes the experiment.
"""
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_pressure_grant as grants
import runtime_shadow as rs
import test_phase3_pair_page as page

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_PRESSURE_AUTHORITY_SERIES.json"
VERSION = "P3-242"
CASES = page.CASES
PRESSURE_KEYS = ("sbp", "dbp", "map")
IV, Q, E = ("order", "Place an IV line."), ("question", None), ("examination", None)
WAIT60, WAIT20 = ("order", "Reassess in 60 minutes."), ("order", "Reassess in 20 minutes.")
LITRE15 = ("order", "Give 1 litre of normal saline over 15 minutes.")
BLOOD2 = ("order", "Transfuse 2 units of packed red cells.")

SCENARIOS = {
    "untreated": (WAIT60,) * 5,
    "early_treatment": (IV, LITRE15, BLOOD2, WAIT20),
    "delayed_treatment": (WAIT60, WAIT60, IV, LITRE15, BLOOD2, WAIT20),
    "fluid_only": (IV, ("order", "Give 500 mL normal saline over 5 minutes."), ("order", "Give 500 mL normal saline over 5 minutes."), WAIT20),
    "blood_only": (IV, BLOOD2, WAIT20),
    "severe_deterioration": (WAIT60, WAIT60, WAIT60, ("order", "Give 1 litre of normal saline over 15 minutes."), WAIT20),
    "recovery": (WAIT60, WAIT60, IV, LITRE15, BLOOD2, ("order", "Reassess in 30 minutes.")),
    "late_rescue": (WAIT60, WAIT60, WAIT60, IV, ("order", "Give 1 litre of normal saline over 10 minutes."), BLOOD2, ("order", "Reassess in 15 minutes.")),
    "iv_line": (IV, Q, IV),
    "unsupported_action": (Q, ("order", page.UNSUPPORTED), Q),
    "long_infusion": (IV, ("order", "Give 1 litre of normal saline over 60 minutes. Reassess in 60 minutes."), ("order", "Reassess in 10 minutes.")),
    "question_time": (Q, Q, Q),
    "exam_time": (E, E, E),
}
CLOSED = ("early_treatment", "iv_line")                         # also CLOSED, to compare the termination, the disposition and the whole session


def _drive(at, step):
    kind, text = step
    if kind == "order":
        page._order(at, text)
    elif kind == "question":
        page._ask(at, text) if text else page._ask(at)
    else:
        page._examine(at)


def _snap(at, label):
    state = at.session_state["state"]
    site = at.session_state.get(ra.SITE_KEY)
    return {"label": label, "minute": page._minute(at), "observable": deepcopy(dict(state.get("observable") or {})), "screen": page._screen(at), "buttons": [b.label for b in at.button],
            "observed": page._observed(at), "overlay_key_in_state": any("overlay" in str(key).lower() for key in state),
            "committed": None if site is None else list(site.minutes_committed), "halted": None if site is None else bool(site.halted),
            "halt_reason": None if site is None else str(site.halt_reason), "records": None if site is None else len(site.records)}


def _play(case, steps, *, authority, directory, close=False):
    monkeypatch = pytest.MonkeyPatch()
    try:
        at = page._open(monkeypatch, case, shadow=True, dry=False, authority=directory if authority else None)
        trail = [_snap(at, "arrival")]
        for position, step in enumerate(steps):
            if authority and ra.continuation_guard(at.session_state, at.session_state["state"])["allowed"] is False:
                # ADAPTED in P3-253 (FD-STOP-02/03): once the experiment is INVALID_FOR_CONTINUATION after a real commit the session is STOPPED. The step is OFFERED to the page and the
                # page cannot take it (no control is drawn); it is recorded as BLOCKED, with the encounter exactly as the stop left it. The OFF leg (the legacy engine) runs on, as it always did.
                before = json.dumps(at.session_state["state"], sort_keys=True, default=str)
                with pytest.raises(StopIteration):
                    _drive(at, step)
                assert json.dumps(at.session_state["state"], sort_keys=True, default=str) == before, "a blocked step moved the encounter"
                trail.append({**_snap(at, f"{position}:{step[0]}"), "blocked": True})
                continue
            _drive(at, step)
            trail.append(_snap(at, f"{position}:{step[0]}"))
        if close:
            next(b for b in at.button if b.label == "Complete Encounter & Begin Review").click().run()
            assert not at.exception, [str(item.value)[:300] for item in at.exception]
            finish = [b for b in at.button if b.label == "Finish now"]
            if finish:
                finish[0].click().run()
                assert not at.exception, [str(item.value)[:300] for item in at.exception]
            trail.append(_snap(at, "closed"))
        site = at.session_state.get(ra.SITE_KEY)
        return {"at": at, "trail": trail, "site": site, "artifact": None if site is None else site.artifact(), "status": ra.authority_status(at.session_state)}
    finally:
        monkeypatch.undo()


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    """Every (case, scenario), authority ON and OFF. Module-scoped: each is a real page played once."""
    out = {}
    for case in CASES:
        for name, steps in SCENARIOS.items():
            directory = str(tmp_path_factory.mktemp("authority_store"))
            out[(case, name)] = {"on": _play(case, steps, authority=True, directory=directory, close=name in CLOSED),
                                 "off": _play(case, steps, authority=False, directory=directory, close=name in CLOSED)}
    return out


def _normalize(text: str) -> str:
    """The screen with the pressure values masked: the claim is that nothing but the pressures differs."""
    text = re.sub(r"\b\d{2,3}/\d{2,3}\b", "<BP>", str(text))
    return re.sub(r"MAP \d+", "MAP <MAP>", text)


def _without_pressures(value):
    if isinstance(value, dict):
        return {key: _without_pressures(item) for key, item in value.items() if key not in PRESSURE_KEYS}
    if isinstance(value, (list, tuple)):
        return [_without_pressures(item) for item in value]
    return _normalize(value) if isinstance(value, str) else value


def _each(runs):
    for (case, name), pair_ in runs.items():
        yield case, name, pair_["on"], pair_["off"]


# -- P3-241: the first real commit on the real page --------------------------------------------------------------------------------------------------------------

def test_p1_the_grant_and_the_real_snapshot_open_a_real_authority_site_on_both_cases(runs):
    for case, name, on, off in _each(runs):
        site = on["site"]
        assert site is not None and site.grant is not None and dict(site.grant)["grant_id"] == grants.GRANT_ID, (case, name)
        assert site.snapshot_id == "gi_pressure_committed" and site.case_id == case and tuple(site.domain) == ("sbp", "dbp", "map")
        assert off["site"] is None, "the OFF run has no authority site: it is the legacy pressure baseline"
        assert on["artifact"]["authority_label"] == ra.REAL_PRESSURE_LABEL and ra.artifact_class(on["artifact"]) == ra.REAL_PRESSURE_LABEL


def test_p2_the_first_real_commit_is_the_common_authority_s_and_differs_from_the_legacy_pressure(runs):
    """P3-241A: equality with the legacy value would prove nothing. At every committed step the pressure the page holds is the recorded COMMON candidate (shaped as the legacy
    engine shows it), and across the series there are minutes where it differs from the legacy pressure the OFF page shows at the same step."""
    differing = 0
    for case, name, on, off in _each(runs):
        records = {record["minute"]: record for record in on["site"].records if record.get("committed")}
        for left, right in zip(on["trail"], off["trail"]):
            if left["label"] in ("arrival", "closed") or left.get("blocked") or left["minute"] not in records or left["committed"] is None or left["minute"] not in left["committed"]:
                continue
            record = records[left["minute"]]
            written = record["written_candidate"]
            assert (left["observable"]["sbp"], left["observable"]["dbp"]) == (written["sbp"], written["dbp"]), (case, name, left["label"], "the page does not hold what the site committed")
            assert record["written_candidate"] != record["legacy_counterfactual"] or record["common_candidate"] == record["legacy_counterfactual"]
            assert (right["observable"]["sbp"], right["observable"]["dbp"]) == (record["legacy_counterfactual"]["sbp"], record["legacy_counterfactual"]["dbp"]), (
                case, name, right["label"], "the OFF page must show the legacy pressure the site recorded as its counterfactual")
            if (left["observable"]["sbp"], left["observable"]["dbp"]) != (right["observable"]["sbp"], right["observable"]["dbp"]):
                differing += 1
    assert differing >= 20, differing


def test_p3_without_the_grant_a_flagged_run_has_no_authority_and_the_pressure_is_the_legacy_engine_s(tmp_path_factory, monkeypatch):
    """The grant is what authorizes: every flag set, the real registered snapshot, and NO grant in the registry -> no site, and the page shows the legacy pressure."""
    directory = str(tmp_path_factory.mktemp("no_grant"))
    monkeypatch.setattr(grants, "REGISTERED_GRANTS", ())
    monkeypatch.setattr(grants, "permits", lambda **kwargs: (False, [grants.UNKNOWN_GRANT]))
    played = _play(CASES[0], (Q, IV), authority=True, directory=directory)
    assert played["site"] is None and played["artifact"] is None
    baseline = _play(CASES[0], (Q, IV), authority=False, directory=directory)
    assert [row["observable"] for row in played["trail"]] == [row["observable"] for row in baseline["trail"]]


# -- P3-242: the management series --------------------------------------------------------------------------------------------------------------------------

def test_p4_every_scenario_ran_and_every_committed_minute_is_the_common_pressure_domain_only(runs):
    assert len(runs) == len(CASES) * len(SCENARIOS) == 26
    for case, name, on, off in _each(runs):
        for record in on["site"].records:
            if record.get("committed"):
                assert sorted(record["committed"]) == ["dbp", "map", "sbp"] or sorted(record["committed"]) == ["dbp", "sbp"] or set(record["committed"]) <= {"sbp", "dbp", "map"}, record["committed"]
                assert set(record["moved_fields"]) <= {"sbp", "dbp", "map"}, (case, name, record["minute"], record["moved_fields"])
                assert record["authority_mode"] == "PRESSURE_ONLY" and record["grant_id"] == grants.GRANT_ID and record["grant_fingerprint"] == grants.GRANT_FINGERPRINT


def test_p5_the_pressure_is_authoritative_at_every_step_after_a_commit_even_when_the_clock_does_not_move(runs):
    """After a real commit at minute m, a turn that does not move the clock (an IV line, a duplicate order) must NOT hand the pressure back to the legacy engine: it is
    re-asserted, unchanged (found by the first real page run and repaired). The pressure never changes between two steps that share a minute."""
    reasserted = 0
    for case, name, on, off in _each(runs):
        for left, right in zip(on["trail"][1:], on["trail"][2:]):
            if left["minute"] == right["minute"] and left["committed"] and right["committed"] and right["minute"] in right["committed"] and not right["halted"]:
                assert (left["observable"]["sbp"], left["observable"]["dbp"]) == (right["observable"]["sbp"], right["observable"]["dbp"]), (case, name, right["label"])
        reasserted += sum(1 for item in on["site"].no_advance_turns if item.get("pressure_reasserted"))
    assert reasserted >= 2, reasserted


def test_p6_no_advance_turns_before_any_commit_and_unsupported_actions_behave_as_certified(runs):
    for case in CASES:
        iv = runs[(case, "iv_line")]["on"]
        assert iv["site"].minutes_committed, "the question committed minute 2 and the IV line did not halt the experiment"
        assert not iv["site"].halted, iv["site"].halt_reason
        bad = runs[(case, "unsupported_action")]["on"]
        assert bad["site"].halted and ra.UNSUPPORTED_AUTHORITY_ACTION in bad["site"].halt_reason and bad["site"].minutes_committed, "an unsupported action after a commit invalidates"
        assert bad["artifact"]["invalid_for_continuation"] == ra.INVALID_FOR_CONTINUATION and bad["artifact"]["mixed_trajectory"] is True


def test_p7_granularity_a_long_infusion_is_one_validated_interval_with_every_internal_minute_in_the_overlay(runs):
    for case in CASES:
        on = runs[(case, "long_infusion")]["on"]
        site = on["site"]
        assert not site.halted, site.halt_reason
        turn = max(site.records, key=lambda record: record["minute"] - (record["consciousness_overlay"] or {}).get("from_minute", 0))
        overlay = turn["consciousness_overlay"]
        assert overlay["clear"] and overlay["minute"] - overlay["from_minute"] + 1 >= 60, "the 60-minute infusion was read minute by minute by the overlay"
        assert [row["minute"] for row in overlay["rows"]] == list(range(overlay["from_minute"], overlay["minute"] + 1))
        assert all(row["shown"] and row["reproduced"] for row in overlay["rows"])
        assert site.minutes_committed.count(overlay["minute"]) == 1, "one final interval commit, not one per minute"


# -- P3-243: the consciousness overlay beside the authority -------------------------------------------------------------------------------------------------

def test_p8_the_overlay_records_the_common_consciousness_and_writes_it_nowhere(runs):
    for case, name, on, off in _each(runs):
        artifact = on["artifact"]
        overlay = artifact["consciousness_overlay"]
        assert overlay["label"] == grants.OVERLAY_LABEL == "FACULTY_ACCEPTED_FOR_DEVELOPMENT_COMPARISON" and overlay["role"] == "CANDIDATE_OVERLAY_NONAUTHORITATIVE"
        assert overlay["authority"] is False and overlay["resident_visible"] is False and overlay["writes_mental_status"] is False and overlay["written_into_the_encounter"] is False
        assert overlay["snapshot"]["snapshot_id"] == "GI_DEVELOPMENT_SNAPSHOT_V1" and overlay["snapshot_is_the_pinned_version_1"] is True and overlay["violations"] == []
        rows = [row for turn in overlay["turns"] for row in turn["rows"]]
        assert rows and all({"category", "mental_status", "F", "relative_delivery", "collapse_state"} <= set(row) for row in rows if row["shown"])
        assert all(turn.get("legacy_mental_status") for turn in overlay["turns"]), "the legacy word is recorded beside the common category"
        for left, right in zip(on["trail"], off["trail"]):
            assert left["overlay_key_in_state"] is False
            if left.get("blocked"):
                continue            # ADAPTED in P3-253: the stopped leg is not run any further (its mental_status is the one the stop left: see p17)
            assert left["observable"].get("mental_status") == right["observable"].get("mental_status"), (case, name, left["label"], "mental_status is the legacy engine's")
        text = ra.canonical(artifact)
        assert "AUTHORITY" not in json.dumps(overlay.get("label")) and "RESIDENT_VISIBLE" not in text


# -- P3-245: the collapse boundary and the window ------------------------------------------------------------------------------------------------------------

def test_p9_the_untreated_course_stops_before_the_boundary_and_names_the_last_commit_the_first_rejection_and_the_common_state(runs):
    for case in CASES:
        on = runs[(case, "untreated")]["on"]
        site, artifact = on["site"], on["artifact"]
        assert site.halted and site.halt_reason.startswith(ra.COLLAPSE_BOUNDARY_REACHED), site.halt_reason
        boundary = artifact["collapse_boundary"]
        assert boundary["last_authoritative_commit_minute"] == max(site.minutes_committed) and boundary["last_authoritative_commit_minute"] < 207
        failed = next(record for record in site.records if record["outcome"] == ra.ABORTED)
        assert boundary["first_rejected_minute"] == failed["minute"] and failed["minute"] > 207 and not failed["committed"]
        assert failed["collapse_boundary"]["first_established_minute"] == 207
        common = boundary["common_state_at_rejection"]
        assert common and common["rows"][-1]["collapse_state"] in (0, 1, 2) and "F" in common["rows"][-1]
        assert not any(word in on["trail"][-1]["screen"] for word in ("ESTABLISHED", "COLLAPSE_BOUNDARY", "INVALID_FOR_CONTINUATION")), "no experiment word, no terminal word on the page"
        assert on["trail"][-1]["observable"].get("pulse_present", True) is not False, "the experiment stop invented no terminal state"


def test_p10_the_window_is_the_predefined_limit_and_no_rescue_scenario_commits_past_it(runs):
    for case, name, on, off in _each(runs):
        assert all(minute <= grants.WINDOW_MINUTES for minute in on["site"].minutes_committed), (case, name)


# -- P3-246: artifacts and replay ---------------------------------------------------------------------------------------------------------------------------

def test_p11_every_real_artifact_verifies_is_labelled_real_and_replays_from_itself_alone(runs):
    for case, name, on, off in _each(runs):
        artifact = on["artifact"]
        verdict = ra.verify_artifact(artifact)
        assert verdict["complete"] and verdict["digest_matches"] and verdict["claims_are_honest"] and verdict["artifact_class"] == ra.REAL_PRESSURE_LABEL, (case, name, verdict)
        replay = ra.replay_site_artifact(artifact)
        assert replay["reproduces"] and replay["overlay_replay"]["reproduces"] and replay["halt_reason_replay"]["reproduces"], (case, name, replay["overlay_replay"], replay["halt_reason_replay"])
        assert replay["covers_every_committed_minute"] and replay["overlay_replay"]["rows_compared"] > 0
        assert artifact["grant"]["fingerprint"] == grants.GRANT_FINGERPRINT and artifact["authority_mode"] == "PRESSURE_ONLY"
        assert artifact["excluded_domains"] == list(grants.EXCLUDED_DOMAINS)


def test_p12_the_real_artifact_is_not_a_dormant_evaluation_nor_a_historical_pressure_artifact(runs):
    import runtime_pair_site as site_module
    for case, name, on, off in _each(runs):
        artifact = on["artifact"]
        assert artifact["artifact"] == "phase3_authority_experiment" and artifact["artifact"] != site_module.ARTIFACT_TYPE
        assert "DORMANT" not in json.dumps({key: artifact[key] for key in ("authority_label", "authority_mode")})
        historical = {key: value for key, value in artifact.items() if key not in ra.REAL_ARTIFACT_FIELDS and key != "artifact_digest"}
        # ADAPTED in P3-248 (review M5): an artifact is classified by its CONTENT as well as its label, so the historical shape has to lack the real content of its minutes too
        assert ra.artifact_class({**historical, "artifact_digest": "x"}) == ra.INCONSISTENT_ARTIFACT, "real minutes under no label are inconsistent, never historical"
        bare = {**historical, "minutes": [{key: value for key, value in dict(record).items() if key not in ra.REAL_MINUTE_CONTENT_KEYS} for record in artifact["minutes"]]}
        bare.pop("no_advance_turns", None)
        assert ra.artifact_class({**bare, "artifact_digest": "x"}) == ra.HISTORICAL_PRESSURE_LABEL, "without the label, the grant and the overlay (and the real content of its minutes) it is the historical shape"
        assert ra.artifact_class({"artifact": site_module.ARTIFACT_TYPE, "label": site_module.LABEL}) == ra.DORMANT_LABEL


# -- P3-247: isolation, OFF versus ON -----------------------------------------------------------------------------------------------------------------------

def test_p13_off_versus_on_differ_only_in_the_pressure_values(runs):
    """At every step of every scenario: same minute, same buttons, same events, same order ledger, same observable but the three pressure fields, and a resident-visible
    text equal once the pressure values are masked."""
    for case, name, on, off in _each(runs):
        assert [row["label"] for row in on["trail"]] == [row["label"] for row in off["trail"]]
        for left, right in zip(on["trail"], off["trail"]):
            where = f"{case}/{name}/{left['label']}"
            if left.get("blocked"):
                continue            # ADAPTED in P3-253: the stopped leg offers no controls and does not move; the isolation claim is about every step the leg RAN (blocked steps: p17)
            # ADAPTED in P3-253: from the step in which the experiment halts after a real commit the ON page is the STOPPED page (the failing turn ran, then the page drew the stop): no
            # controls and the operational notice. Everything else of that step is still compared; the controls and the text are compared on every step before it.
            stopped_page = bool(left["halted"] and left["committed"])
            assert left["minute"] == right["minute"], where
            if not stopped_page:
                assert left["buttons"] == right["buttons"], where
            assert _without_pressures(left["observed"]["events"]) == _without_pressures(right["observed"]["events"]), where
            assert left["observed"]["ledger"] == right["observed"]["ledger"], where
            assert _without_pressures(left["observable"]) == _without_pressures(right["observable"]), (where, "a non-pressure observable differs")
            if not stopped_page:
                assert _normalize(left["screen"]) == _normalize(right["screen"]), (where, "the visible text differs beyond the pressure values")


def test_p17_a_stopped_scenario_ends_at_the_stop_every_later_step_is_blocked_and_nothing_moves(runs):
    """ADAPTED/ADDED in P3-253 to P3-261 (FD-STOP-02/03/07). The scenarios in which the experiment halts after a real commit (an unsupported action; the untreated course at the collapse
    boundary) are STOPPED sessions: every step after the halt is blocked -- no control is drawn, the encounter is exactly as the stop left it, the legacy engine does not run it on, no
    minute is committed again -- and no step before the halt is blocked. Scenarios that never halt are never blocked."""
    stopped = 0
    for case, name, on, off in _each(runs):
        trail = on["trail"]
        halted_at = next((index for index, row in enumerate(trail) if row["halted"] and row["committed"]), None)
        blocked = [index for index, row in enumerate(trail) if row.get("blocked")]
        if halted_at is None:
            assert not blocked, (case, name, "a session that never halted was blocked")
            continue
        stopped += 1
        assert blocked == list(range(blocked[0], len(trail))) if blocked else True, (case, name, "blocked steps are exactly the ones after the stop")
        assert all(index > halted_at for index in blocked), (case, name, "the failing step itself ran (declared limit); only the steps AFTER it are blocked")
        held = trail[halted_at]
        assert "Send" not in held["buttons"] and "Examine patient" not in held["buttons"] and "Ask" not in held["buttons"], (case, name, "the stopped page draws no control")
        assert "DEVELOPMENT AUTHORITY EXPERIMENT HALTED" in held["screen"], (case, name, "the stopped page says so, operationally")
        for index in blocked:
            assert trail[index]["observable"] == held["observable"] and trail[index]["minute"] == held["minute"] and trail[index]["observed"] == held["observed"], (case, name, index)
            assert trail[index]["committed"] == held["committed"] and trail[index]["records"] == held["records"], (case, name, index, "nothing was committed or recorded again")
        assert on["status"]["halted"] is True
    assert stopped >= 4, stopped


def test_p14_after_the_encounter_is_closed_the_whole_session_is_equal_modulo_the_pressures_scoring_included(runs):
    import test_phase3_site_page as pages
    compared = 0
    for case, name, on, off in _each(runs):
        if name not in CLOSED:
            continue
        whole_on, whole_off = pages._whole(on["at"]), pages._whole(off["at"])
        assert whole_on.keys() == whole_off.keys(), (case, name)
        different = sorted(key for key in whole_on if _without_pressures(whole_on[key]) != _without_pressures(whole_off[key]))
        assert not different, (case, name, different)
        compared += 1
    assert compared == len(CASES) * len(CLOSED)


def test_p15_the_first_pilot_and_production_never_see_the_grant(monkeypatch):
    import runtime_authority_store as store
    for name in ra.PILOT_REQUIRED_ON:
        monkeypatch.setenv(name, "1")
    state = {"engine_family": "gi_bleed", "case_id": "x", "sim_time": 0, "observable": {}}
    for environ in ({ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: "gi_pressure_committed", ra.ENVIRONMENT_FLAG: "production", store.STORE_FLAG: "x", rs.FLAG: rs.MODE_SHADOW_COMPARE},
                    {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: "gi_pressure_committed", ra.ENVIRONMENT_FLAG: "development", ra.PILOT_FLAGS[0]: "1"}):
        assert ra.open_site(state, environ=environ) is None and not ra.gate(state, environ=environ, unsupported=()).granted
    assert grants.GRANT["authority_mode"] == "PRESSURE_ONLY"


# -- the record --------------------------------------------------------------------------------------------------------------------------------------------

def _row(case, name, on, off):
    site, artifact = on["site"], on["artifact"]
    overlay_rows = [row for turn in artifact["consciousness_overlay"]["turns"] for row in turn["rows"] if row["shown"]]
    established = [row["minute"] for row in overlay_rows if row["collapse_state"] == 2]
    replay = ra.replay_site_artifact(artifact)
    return {"case": case, "scenario": name, "steps": len(SCENARIOS[name]), "committed_minutes": list(site.minutes_committed),
            "last_authoritative_commit": max(site.minutes_committed) if site.minutes_committed else None, "state": artifact["experiment_state"],
            "halted": bool(site.halted), "halt_kind": site.halt_reason.split(":", 1)[0] if site.halted else "",
            "first_rejected_minute": artifact["collapse_boundary"]["first_rejected_minute"], "reasserted_turns": sum(1 for item in site.no_advance_turns if item.get("pressure_reasserted")),
            "pressure_steps_on_off": [[row["minute"], [left["observable"].get("sbp"), left["observable"].get("dbp")], [right["observable"].get("sbp"), right["observable"].get("dbp")]]
                                      for row, left, right in zip(on["trail"], on["trail"], off["trail"])],
            "overlay": {"rows": len(overlay_rows), "words": sorted({row["mental_status"] for row in overlay_rows}), "max_F": round(max((row["F"] for row in overlay_rows), default=0.0), 4),
                        "first_established_minute": established[0] if established else None, "legacy_words": sorted({str(turn["legacy_mental_status"]) for turn in artifact["consciousness_overlay"]["turns"]})},
            "artifact_class": ra.artifact_class(artifact), "verified": bool(ra.verify_artifact(artifact)["complete"]), "replay_reproduces": bool(replay["reproduces"]),
            "overlay_replay_reproduces": bool(replay["overlay_replay"]["reproduces"]), "halt_replay": replay["halt_reason_replay"]["kind"],
            # ADDED in P3-253: only the rows of STOPPED sessions carry it (the other rows are what they were, bit for bit)
            **({"blocked_steps": [index for index, step in enumerate(on["trail"]) if step.get("blocked")]} if any(step.get("blocked") for step in on["trail"]) else {})}


def build_record(runs) -> dict:
    rows = [_row(case, name, on, off) for case, name, on, off in _each(runs)]
    body = {"record_type": "PHASE3_PRESSURE_AUTHORITY_SERIES", "version": VERSION, "decided_on": "2026-11-12",
            "what_it_is": "the first REAL GI development pressure authority experiment on the real page: 13 scenarios x 2 cases, authority ON versus OFF",
            "grant": grants.summary(), "runs": rows,
            "summary": {"runs": len(rows), "committed_minutes": sum(len(row["committed_minutes"]) for row in rows), "states": dict(Counter(row["state"] for row in rows)),
                        "halt_kinds": dict(Counter(row["halt_kind"] for row in rows if row["halted"])), "all_verified": all(row["verified"] for row in rows),
                        "all_replay": all(row["replay_reproduces"] and row["overlay_replay_reproduces"] for row in rows)},
            "authority": {"common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY, "approved_authority_snapshots": sorted(ra.APPROVED_SNAPSHOTS),
                          "consciousness_authority": False, "mental_status_written": False}}
    return {**body, "record_digest": ra.digest_of(body)}


def test_p16_the_series_record_is_what_the_real_page_produced(runs):
    live = json.loads(json.dumps(build_record(runs)))
    if os.environ.get("MRS_WRITE_PRESSURE_SERIES") == "1":
        RECORD_PATH.write_text(json.dumps(live, indent=1, sort_keys=True), encoding="utf-8")
    assert RECORD_PATH.exists(), "the record is produced once and committed"
    assert json.loads(RECORD_PATH.read_text(encoding="utf-8")) == live, "the committed series no longer matches the real page: regenerate it deliberately"
