"""P3-231: the REAL page, both GI cases, authority OFF, the dormant pair-authority SITE ON versus OFF.

TEST-SIDE. ``test_phase3_pair_page.py`` (P3-217) already proved invisibility for the main script. This file extends the matrix to what the dormant SITE adds and what
that script did not play: a held order released during information activities, a held order released inside an order turn, a recovery (a bolus, then blood, then a
reassessment), a long untreated deterioration, and the closing of the encounter (the termination and the disposition). For every step the resident-visible text,
the buttons, the engine's state, the events and the order ledger are compared with the evaluation OFF and ON; after the closing, the WHOLE session state (every key
but the layer's own) is compared, which is where a score, a ledger, the management trace, a termination or a disposition would live.

Nothing is enabled and nothing is injected: no authority flag, no approved snapshot, no grant. The dormant vocabulary never reaches the page.
"""
import json
import re
from copy import deepcopy

import pytest

import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_pair_site as site_module
import runtime_shadow as rs
import test_phase3_pair_page as page
from test_shadow_resolution import GI, HELD

CASES = page.CASES
BLOOD, FLUID = HELD[GI]["blood"][0], HELD[GI]["fluid"][0]
#: Vocabulary of the dormant site that must never reach a resident (added to the P3-217 list).
DORMANT_WORDS = page.FORBIDDEN_ON_THE_PAGE + ("DORMANT_AUTHORITY_EVALUATION", "INVALID_FOR_CONTINUATION", "DORMANT_NOT_ARMED", "arming", "GRANT_REGISTRY", "GI_PAIR_AUTHORITY",
                                              "faculty_approval", "pair_dormant", "TEST_ONLY_FAKE_GRANT", "request_commit")

SCRIPTS = {
    "held_release_by_activity": (("order", BLOOD), ("question", None), ("examination", None), ("question", "How long has the pain been going on?")),
    "held_release_by_order": (("order", FLUID), ("order", "Give 500 mL normal saline over 12 minutes."), ("order", "Reassess in 10 minutes.")),
    "recovery": (("order", "Place an IV line."), ("order", "Give 500 mL normal saline over 5 minutes."), ("order", "Transfuse 2 units of packed red cells."),
                 ("order", "Reassess in 20 minutes.")),
    "long_untreated_deterioration": (("order", "Reassess in 60 minutes."),) * 5,
}
CLOSED = ("held_release_by_activity", "recovery")                  # the encounters that are also CLOSED, to compare the termination and the disposition
#: Keys of the page's session that belong to the layer under test, or that are volatile by construction (a clock, a thread, a random nonce).
LAYER_KEYS = {pair.DRY_KEY, pair.DRY_ARTIFACT_KEY, pair.DRY_REFUSAL_KEY, "phase3_shadow", "phase3_shadow_store", ra.SITE_KEY, ra.ARTIFACT_KEY, ra.HALTED_KEY}


def _drive(at, step):
    kind, text = step
    if kind == "order":
        page._order(at, text)
    elif kind == "question":
        page._ask(at, text) if text else page._ask(at)
    else:
        page._examine(at)


#: What differs between ANY two runs of the same script, flags or no flags: the random seed of the encounter and the hash taken over it, the random id and the
#: wall-clock stamps of a submission, and the per-run suffix of a widget key. Masked, and nothing else.
_RANDOM_PER_RUN = {"seed", "content_sha256", "form_id", "started_at", "finished_at"}


def _mask(value, parent=None):
    if isinstance(value, dict):
        return {key: ("<per-run>" if key in _RANDOM_PER_RUN or key in page._PER_RUN or (key == "id" and parent in ("submission", "submission_log")) else _mask(item, key))
                for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_mask(item, parent) for item in value]
    return value


def _whole(at):
    """Every key of the page's session but the layer's own, as plain masked JSON."""
    out = {}
    for key in sorted(list(at.session_state)):
        if key in LAYER_KEYS or str(key).startswith("phase3_") or str(key).startswith("_scene") or key in ("_submission_nonce", "rng_counter"):
            continue
        try:
            out[re.sub(r"_[0-9a-f]{16}$", "_<widget>", str(key))] = _mask(json.loads(json.dumps(at.session_state[key], default=str)), key)
        except Exception:
            out[key] = "<unreadable>"
    return out


def _play(monkeypatch, case, steps, *, dry, close):
    at = page._open(monkeypatch, case, shadow=dry, dry=dry)
    trail = [("arrival", page._screen(at), page._observed(at), [b.label for b in at.button])]
    for position, step in enumerate(steps):
        _drive(at, step)
        trail.append((f"{position}:{step[0]}", page._screen(at), page._observed(at), [b.label for b in at.button]))
    if close:
        next(b for b in at.button if b.label == "Complete Encounter & Begin Review").click().run()
        assert not at.exception, [str(item.value)[:300] for item in at.exception]
        # the page asks once whether to continue or finish (the encounter is closed only by "Finish now")
        finish = [b for b in at.button if b.label == "Finish now"]
        if finish:
            finish[0].click().run()
            assert not at.exception, [str(item.value)[:300] for item in at.exception]
        trail.append(("closed", page._screen(at), page._observed(at), [b.label for b in at.button]))
    return at, trail


@pytest.fixture(scope="module", params=sorted(SCRIPTS))
def played(request):
    """One script, both cases, both settings. Module-scoped: each is a real page played once."""
    monkeypatch = pytest.MonkeyPatch()
    try:
        out = {}
        for case in CASES:
            off = _play(monkeypatch, case, SCRIPTS[request.param], dry=False, close=request.param in CLOSED)
            on = _play(monkeypatch, case, SCRIPTS[request.param], dry=True, close=request.param in CLOSED)
            out[case] = {"off": off, "on": on}
        yield {"script": request.param, "cases": out}
    finally:
        monkeypatch.undo()


def test_q1_the_resident_page_is_identical_step_by_step_with_the_dormant_site_on_in_both_cases(played):
    """Text, buttons, the engine's observable, events and order ledger: not one character differs at any step."""
    for case, runs in played["cases"].items():
        (_, off), (_, on) = runs["off"], runs["on"]
        assert [row[0] for row in off] == [row[0] for row in on]
        for left, right in zip(off, on):
            assert left[1] == right[1], f"{played['script']}/{case}/{left[0]}: the visible text differs"
            assert left[2] == right[2], f"{played['script']}/{case}/{left[0]}: the engine's own state differs"
            assert left[3] == right[3], f"{played['script']}/{case}/{left[0]}: the buttons differ"


def test_q2_no_word_of_the_dormant_site_is_ever_on_the_page_and_the_flags_off_page_holds_no_layer_state(played):
    for case, runs in played["cases"].items():
        (at_off, _), (at_on, on) = runs["off"], runs["on"]
        for label, screen, _, buttons in on:
            for word in DORMANT_WORDS:
                assert word not in screen and not [b for b in buttons if word in b], (played["script"], case, label, word)
        for key in LAYER_KEYS:
            assert at_off.session_state.get(key) is None, (played["script"], case, key)
        assert "development_authority_view" not in at_on.session_state["state"]


def test_q3_the_whole_session_is_identical_after_the_encounter_is_closed_termination_disposition_trace_ledger_and_review(played):
    """Every key of the page's session but the layer's own, compared after the closing (and, for the scripts that are not closed, at their end)."""
    for case, runs in played["cases"].items():
        (at_off, _), (at_on, _) = runs["off"], runs["on"]
        whole_off, whole_on = _whole(at_off), _whole(at_on)
        assert whole_off.keys() == whole_on.keys()
        different = sorted(key for key in whole_off if whole_off[key] != whole_on[key])
        assert not different, (played["script"], case, different)
        if played["script"] in CLOSED:
            assert whole_on["encounter_ended"] and whole_on["encounter_closed_trace"] and whole_on["review_stage"] == whole_off["review_stage"]


def test_q4_the_dormant_site_evaluated_every_route_and_its_states_say_what_the_script_did(played):
    for case, runs in played["cases"].items():
        at_on = runs["on"][0]
        held = at_on.session_state[pair.DRY_KEY]
        site = held[1]
        assert isinstance(site, site_module.DormantPairSite) and site.violations == [] and held[0] is at_on.session_state["phase3_shadow"]
        assert site.arming({})["armed"] is False and site.commit_requests == [] and site.artifact()["committed_authority"] is False
        verdicts = [record["verdict"] for record in site.records]
        script = played["script"]
        if script in ("held_release_by_activity",):
            assert set(site.records[i]["route"] for i in range(len(site.records))) == {ra.ORDER_TURN, ra.CLINICAL_TIME}, (case, script)
        if script == "long_untreated_deterioration":
            # the window or the collapse boundary ends the experiment; authority had begun, so the state says INVALID_FOR_CONTINUATION (never a fallback)
            assert site.halt is not None and set(site.halt["failed_checks"]) & {"window_open", "collapse_boundary_not_reached"}, (case, site.halt)
            assert site.state == site_module.INVALID_FOR_CONTINUATION and site.continuation()["legacy_may_continue_silently"] is False
        else:
            assert pair.WOULD_ABORT not in verdicts, (case, script, [r["failed_checks"] for r in site.records])
            assert site.state in (site_module.WOULD_COMMIT, site_module.NOT_STARTED) and site.halt is None
        artifact = site.artifact()
        assert site_module.verify_artifact(artifact)["verified"] is True
        if script != "long_untreated_deterioration":
            replay = site_module.replay_artifact(artifact)
            assert replay["reproduces"] is True, (case, script, replay["mismatches"][:2])


def test_q5_the_held_order_is_not_applied_at_its_placement_and_the_release_minute_is_inside_a_validated_interval(played):
    if not played["script"].startswith("held_release"):
        pytest.skip("only the held-order scripts")
    for case, runs in played["cases"].items():
        at_on = runs["on"][0]
        shadow, site = at_on.session_state["phase3_shadow"], at_on.session_state[pair.DRY_KEY][1]
        entry = shadow.held[0]
        assert entry["state"] == rs.ORDER_EXECUTED and entry["placed_minute"] < entry["executed_minute"]
        released = [record for record in site.records if entry["executed_minute"] in [row["minute"] for row in record["interval"]]]
        assert released and all(record["verdict"] == pair.WOULD_COMMIT for record in released)
        # the shadow mirrored the held order exactly ONCE, at the minute the engine ran it, never at its placement
        mine = [item for item in shadow.mirrored if item.order_id == entry["shadow_order_id"]]
        assert [(item.minute) for item in mine] == [entry["executed_minute"]] and entry["executed_minute"] > entry["placed_minute"]
