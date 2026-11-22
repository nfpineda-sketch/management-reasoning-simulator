"""P3-510 and P3-512 (page level): the management trace is derived from the REAL page's runtime events -- the page's own Management Trace (``management_trace_v1``) and the live authority's artifact -- on the GI
encounter under the norepinephrine development grant, with the page's reasoning gate answered by the (simulated) resident.

What it proves: the trace extracted from the page carries the resident's reasoning EXACTLY as the page recorded it (and nothing else under that provenance), the action text as the resident typed it, every pressure
transition bound to a committed authority minute, and the same pressures the headless development runner produces for the same orders (the runner IS the page's order path).
"""
from pathlib import Path

import pytest

import development_management_trace as mt
import runtime_authority as ra
import runtime_pressure_snapshot as ps
import runtime_tone_snapshot as tn
import test_gi_management_trace_paths as tp
import test_phase3_pair_page as pair_page

pytestmark = pytest.mark.ordinary_configuration
CASE = "gi_bleed_57m"
#: The first order carries an expectation in the resident's own words: the page then COMPOSES a priority from it and marks it as composed (the case of P3-515 M1).
ORDERS = (tp.VOL + " I expect the blood pressure and perfusion to improve.", "Start norepinephrine at 5 mcg/min. Reassess in 15 minutes.")


def _open(monkeypatch, tmp_path):
    """The real page on the GI case under the norepinephrine development grant (the ratified pressure snapshot AND the tone snapshot)."""
    pair_page._clean(monkeypatch, CASE, shadow=True, dry=False, authority=str(tmp_path / "store"))
    monkeypatch.setenv(ra.SNAPSHOT_FLAG, ps.SNAPSHOT_ID)
    monkeypatch.setenv(ra.TONE_FLAG, tn.SNAPSHOT_ID)
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(pair_page.APP, default_timeout=600)
    at.secrets["APP_PASSWORD"] = "test-only-not-a-real-credential"
    at.session_state["_shared_access_granted"] = True
    at.run()
    begin = [button for button in at.button if "Begin" in button.label or "Comenzar" in button.label]
    assert begin, "the app must offer the encounter"
    begin[0].click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    return at


@pytest.fixture(scope="module")
def page_run(tmp_path_factory):
    import runtime_pressure_grant as grants
    with pytest.MonkeyPatch.context() as monkeypatch:
        # ORDINARY configuration (the module's marker reaches function scope only; this module-scoped run must declare it itself): the suite's session-wide historical reconstruction is
        # not this encounter's
        monkeypatch.delenv(grants.HISTORICAL_RECONSTRUCTION_FLAG, raising=False)
        at = _open(monkeypatch, tmp_path_factory.mktemp("mtrace-page"))
        for text in ORDERS:
            pair_page._order(at, text)
        site = at.session_state[ra.SITE_KEY] if ra.SITE_KEY in at.session_state else None      # (AppTest's session state has no .get)
        events = [dict(event) for event in at.session_state["management_trace"]]
        observable = dict(at.session_state["state"].get("observable") or {})
        yield {"at": at, "site": site, "events": events, "artifact": site.artifact() if site is not None else {}, "observable": observable}


def test_m1_the_trace_extracted_from_the_page_keeps_the_resident_s_reasoning_exactly_and_invents_none(page_run):
    assert page_run["site"] is not None and not page_run["site"].halted, getattr(page_run["site"], "halt_reason", None)
    turns = [mt.turn_from_page_event(event) for event in page_run["events"]]
    arrival = {"sbp": 88, "dbp": 54, "map": 65}
    trace = mt.extract(turns, page_run["artifact"], arrival)
    assert mt.trace_problems(trace, turns) == []
    expressed = [turn for turn in turns if turn["executed"]]
    assert expressed, "the page executed the two orders"
    composed_seen = 0
    for step, turn in zip(trace["steps"], turns):
        assert step["action"]["text"] == {"value": turn["text"], "provenance": mt.RESIDENT_EXPRESSED, "source": mt.PAGE}
        record = dict(turn["reasoning"])
        composed = set(record.get("derived_slots") or ()) | {key for key, value in dict(record.get("slot_provenance") or {}).items() if value == "composed"}
        for part, keys in (("priority", ("management_priority",)), ("expected", ("expected_effect",)), ("reassessment", ("reassessment_target", "reassessment_plan"))):
            key = next((key for key in keys if str(record.get(key) or "").strip()), None)
            resident = step[part]["resident"]
            if key is None:
                assert resident["value"] == mt.NOT_EXPRESSED
            elif key in composed:
                # P3-515 M1 on the REAL page: the page composes a priority from the gate's other answers and marks it; it is never shown as the resident's
                composed_seen += 1
                assert resident["value"] == mt.NOT_EXPRESSED and resident["note"] == mt.COMPOSED_NOTE
                assert str(record[key]).strip() not in " ".join(line["text"] for block in mt.render(trace) for line in block["lines"])
            else:
                assert resident["value"] == str(record[key]).strip()
                if dict(record.get("slot_provenance") or {}).get(key) == "completed":
                    assert resident["as"] == "completed in the follow-up", "the gate's answers are the resident's, labelled as given in the follow-up"
    assert composed_seen, "the page composed a priority from the gate's answers (the case M1 was about)"
    appended = [event for event in page_run["events"] if "Guided reasoning completion:" in str(event.get("learner_input") or "")]
    assert appended, "the page appended its guided-completion transcript to an entry"
    for event in appended:
        turn = mt.turn_from_page_event(event)
        assert "Guided reasoning completion" not in turn["text"] and turn["text"] == str(event["learner_input"]).split("\n\nGuided reasoning completion: ")[0], \
            "the action is the resident's own entry, not the transcript the application formatted after the gate"
    assert any(step["expected"]["resident"]["value"] != mt.NOT_EXPRESSED for step in trace["steps"]), "the gate's answer about the expected effect is the resident's, read from the page"


def test_m2_every_pressure_of_the_page_trace_is_a_committed_live_authority_minute_under_the_norepinephrine_grant(page_run):
    turns = [mt.turn_from_page_event(event) for event in page_run["events"]]
    trace = mt.extract(turns, page_run["artifact"], {"sbp": 88, "dbp": 54, "map": 65})
    assert trace["authority"]["grant_id"] == "GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1" and trace["authority"]["tone_snapshot_id"] == tn.SNAPSHOT_ID
    committed = mt.authority_points(page_run["artifact"])
    for point in mt.trajectory(trace)[1:]:
        assert committed[point["minute"]]["pressure"] == {key: point[key] for key in ("sbp", "dbp", "map")}
    last = mt.trajectory(trace)[-1]
    assert (int(page_run["observable"]["sbp"]), int(page_run["observable"]["dbp"])) == (last["sbp"], last["dbp"]), "what the resident sees is the last committed authority minute"


def test_m3_the_headless_development_runner_gives_the_page_s_pressures_for_the_same_orders(page_run):
    run = tp.DevelopmentEncounter(CASE)
    for text in ORDERS:
        run.order(text)
    headless = mt.authority_points(run.artifact())
    page = mt.authority_points(page_run["artifact"])
    assert {minute: point["pressure"] for minute, point in headless.items()} == {minute: point["pressure"] for minute, point in page.items()}
