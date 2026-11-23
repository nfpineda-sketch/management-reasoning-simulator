"""P3-536 to P3-539 (FD-FINALPILOT-01 to 04): the classification of a turn that did not move the clock after a committed minute, the PROOF of a clarification no-op, the
held order in the shared settlement rule, and the artifact's own re-derivation of every no-op -- at the unit and the site level (headless; the real page is
``test_gi_final_pilot_page.py``).

TEST-SIDE. Sites open through the test-only approval of the P3-28 certification (exactly as ``test_phase3_review_findings`` does); nothing here enables an authority.

What is pinned:
* every no-time-advance turn is exactly one of STRUCTURAL_ONLY, CLARIFICATION_NOOP, CERTIFIED_SAME_MINUTE_MUTATION, UNSAFE_MUTATION and UNKNOWN; only CLARIFICATION_NOOP is
  preserved, and it is decided from a proof of state equivalence, never from the text;
* a proven no-op is recorded on the SAME committed minute: nothing committed, no sample added, no time fabricated, the pressure is the committed one;
* a changed patient state, a changed protected field, an order that acted, a pressure that is not the committed one, a new shadow failure, a shadow that advanced, or a
  missing origin each keep failing closed (MINUTE_ALREADY_COMMITTED), classified UNSAFE_MUTATION or UNKNOWN;
* a HELD order of a class the mapping cannot represent does not halt a turn (it acted on nothing); an allowlisted class held, or an unsupported class that acted, still does;
* the artifact re-derives each no-op on its own, and a tampered one is named.
"""
import tempfile
from copy import deepcopy

import pytest

import pilot_acceptance as acceptance
import runtime_authority as ra
import runtime_authority_store as store
import runtime_authority_turn as rat
import runtime_shadow as rs
import runtime_shadow_evidence as ev

CASE = "gi_bleed_57m"
TEST_ONLY_SNAPSHOT = {"id": "test_only_final_pilot_point", "approved_by_faculty": True, "decision": "TEST ONLY: exists inside one test session, approves nothing",
                      "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID, "parameters": {"test_only_placeholder": 1.0}}
STORE_DIR = tempfile.mkdtemp(prefix="phase3-final-pilot-")
BEST = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: TEST_ONLY_SNAPSHOT["id"], ra.ENVIRONMENT_FLAG: "development",
        rs.FLAG: rs.MODE_SHADOW_COMPARE, store.STORE_FLAG: STORE_DIR}
VOLUME = "Give 1 litre of normal saline over 15 minutes. Reassess in 15 minutes."
INCOMPLETE = "Give normal saline."


@pytest.fixture
def approved(monkeypatch, tmp_path):
    monkeypatch.setitem(ra._APPROVED_SNAPSHOT_POINTS, TEST_ONLY_SNAPSHOT["id"], TEST_ONLY_SNAPSHOT)
    for name, value in BEST.items():
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)
    directory = tmp_path / "phase3_authority"
    monkeypatch.setenv(store.STORE_FLAG, str(directory))
    return {**BEST, store.STORE_FLAG: str(directory)}


# -- A: the classification, pure ----------------------------------------------------------------------------------------------------------------------------

FULL = {name: True for name in ra.NOOP_PROOF_FIELDS}


def test_a1_every_no_time_advance_turn_is_exactly_one_class_and_only_a_complete_proof_is_a_noop():
    assert ra.NONADVANCING_CLASSES == ("STRUCTURAL_ONLY", "CLARIFICATION_NOOP", "CERTIFIED_SAME_MINUTE_MUTATION", "UNSAFE_MUTATION", "UNKNOWN")
    assert ra.classify_nonadvancing(FULL) == ra.CLARIFICATION_NOOP
    assert ra.classify_nonadvancing(FULL, ("reassessment",)) == ra.STRUCTURAL_ONLY
    assert ra.classify_nonadvancing(FULL, ("consult", "reassessment")) == ra.STRUCTURAL_ONLY
    assert ra.classify_nonadvancing(FULL, ("vascular_access",)) == ra.CERTIFIED_SAME_MINUTE_MUTATION
    assert ra.classify_nonadvancing(FULL, ("fluid",)) == ra.UNSAFE_MUTATION, "an action that ran is a mutation, whatever the proof says"
    assert ra.classify_nonadvancing(FULL, ("diagnostic",)) == ra.CLARIFICATION_NOOP, "a test the engine recorded without changing anything is proven by the proof"
    assert ra.classify_nonadvancing({**FULL, "patient_state_unchanged": False}, ("diagnostic",)) == ra.UNSAFE_MUTATION
    assert ra.classify_nonadvancing(FULL, ("diagnostic", "fluid")) == ra.UNSAFE_MUTATION
    for name in ("patient_state_unchanged", "protected_fields_unchanged", "no_settled_order_acted"):
        assert ra.classify_nonadvancing({**FULL, name: False}) == ra.UNSAFE_MUTATION, name
    for name in set(ra.NOOP_PROOF_FIELDS) - {"patient_state_unchanged", "protected_fields_unchanged", "no_settled_order_acted"}:
        assert ra.classify_nonadvancing({**FULL, name: False}) == ra.UNKNOWN_NONADVANCING, name
    assert ra.classify_nonadvancing({}) == ra.UNKNOWN_NONADVANCING
    assert ra.classify_nonadvancing({**FULL, "patient_state_unchanged": None, "protected_fields_unchanged": None, "turn_origin_given": False}) == ra.UNKNOWN_NONADVANCING, \
        "facts that could not be established are unknown, not evidence of a mutation"
    assert ra.classify_nonadvancing({**FULL, "patient_state_unchanged": "yes"}) == ra.UNKNOWN_NONADVANCING, "only True proves; a truthy value does not"


def test_a2_a_held_order_acts_on_nothing_in_the_shared_settlement_rule_and_what_acted_or_an_allowlisted_held_class_still_does():
    assert ra.unsupported_in_settlement([{"class": "clarification", "fate": "HELD_CLARIFICATION"}]) == ()
    assert ra.unsupported_in_settlement([{"class": "tranexamic_acid", "fate": "HELD_REASONING"}, {"class": "fluid", "fate": "EXECUTED"}]) == ()
    assert ra.unsupported_in_settlement([{"class": "clarification", "fate": "EXECUTED"}]) == ("clarification",)
    assert ra.unsupported_in_settlement([{"class": "intubation", "fate": "EXECUTED"}, {"class": "clarification", "fate": "HELD_CLARIFICATION"}]) == ("intubation",)
    assert ra.unsupported_in_settlement([{"class": "Vascular_Access", "fate": "HELD_CLARIFICATION"}]) == ("vascular_access",), "the allowlisted class held is still a contradiction"
    assert ra.unsupported_in_settlement([{"class": "clarification", "fate": "RECORDED_NOT_MODELLED"}]) == ("clarification",)
    # P3-552 (review finding 1): what the reader did not recognize did nothing; a stated plan the engine records is not a management act; decision C stays for the rest
    assert ra.unsupported_in_settlement([{"class": "unrecognized", "fate": "UNRECOGNIZED"}, {"class": "unread_words", "fate": "UNRECOGNIZED"}]) == ()
    assert ra.unsupported_in_settlement([{"class": "plan", "fate": "RECORDED_NOT_MODELLED"}]) == ()
    assert ra.unsupported_in_settlement([{"class": "not_modelled", "fate": "RECORDED_NOT_MODELLED"}]) == ("not_modelled",), "decision C: a recorded, unmodelled medication"
    assert ra.unsupported_in_settlement([{"class": "gastric_tube", "fate": "EXECUTED"}]) == ("gastric_tube",)
    assert ra.order_did_not_act({"class": "diagnostic", "fate": "RECORDED_NOT_MODELLED"}) and not ra.order_did_not_act({"class": "norepinephrine", "fate": "RECORDED_NOT_MODELLED"})
    assert not ra.order_did_not_act({"class": "fluid", "fate": "SCHEDULED"}) and not ra.order_did_not_act({"class": "fluid", "fate": "EXECUTED"})


# -- B: the site --------------------------------------------------------------------------------------------------------------------------------------------

def _capture(encounter):
    real, seen = acceptance.Encounter._execute, {}

    def execute(self, parsed, line):
        out = real(self, parsed, line)
        seen["run"] = out[2]
        return out
    return real, seen, execute


def _turn(encounter, text):
    real, seen, execute = _capture(encounter)
    acceptance.Encounter._execute = execute
    try:
        origin_state = deepcopy(encounter.state)
        before = encounter.shadow.capture(encounter.state)
        entry = encounter.order(text)
    finally:
        acceptance.Encounter._execute = real
    orders = [dict(item) for item in entry["orders"]]
    return {"before": before, "after": deepcopy(encounter.state), "ran": seen.get("run", []), "orders": orders, "origin_state": origin_state,
            "sid": str((orders[0] if orders else {}).get("submission_id") or "")}


def _origin(origin_state, after, *, rng=(3, 3), last=("a", "a")):
    return {"originals": {"state": origin_state, "last_executed_action": last[0], "rng_counter": rng[0]},
            "current": {"state": after, "last_executed_action": last[1], "rng_counter": rng[1]}}


@pytest.fixture
def committed(approved):
    """An encounter whose first turn committed minute 15, and the site that committed it."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        site = ra.open_site(deepcopy(encounter.state), environ=approved)
        assert site is not None
        first = _turn(encounter, VOLUME)
        prepared = site.minute(first["before"], first["after"], encounter.shadow, first["ran"], first["sid"], ra.ORDER_TURN, settled=first["orders"])
        assert prepared is not None and site.minutes_committed == (15,) and not site.halted, site.halt_reason
        encounter.state = deepcopy(prepared)
        yield {"encounter": encounter, "site": site}


def _clarify(world, text=INCOMPLETE):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        return _turn(world["encounter"], text)


def _judge(world, turn, **kw):
    site = world["site"]
    origin = kw.pop("origin", _origin(turn["origin_state"], turn["after"]))
    after = kw.pop("after", turn["after"])
    settled = kw.pop("settled", turn["orders"])
    return site.minute(turn["before"], deepcopy(after), world["encounter"].shadow, turn["ran"], turn["sid"], ra.ORDER_TURN, settled=settled, origin=origin)


def test_b1_a_proven_clarification_noop_stays_on_the_same_committed_minute_and_the_artifact_rederives_it(committed):
    turn = _clarify(committed)
    assert turn["ran"] == [] and turn["after"]["sim_time"] == 15 and [o["fate"] for o in turn["orders"]] == ["HELD_CLARIFICATION"]
    site = committed["site"]
    records, committed_before = len(site.records), site.minutes_committed
    assert _judge(committed, turn) is None
    assert not site.halted and site.minutes_committed == committed_before and len(site.records) == records, "nothing committed, no sample added"
    noop = site.no_advance_turns[-1]
    assert noop["outcome"] == ra.NONADVANCING_CLARIFICATION_NOOP and noop["nonadvancing_class"] == ra.CLARIFICATION_NOOP and noop["attached_to_committed_minute"] == 15
    assert noop["proof"] == {name: True for name in ra.NOOP_PROOF_FIELDS} and noop["action_kinds"] == [] and [o["fate"] for o in noop["held_orders"]] == ["HELD_CLARIFICATION"]
    assert noop["pressure_digest"] == noop["committed_pressure_digest"]
    assert site.last_nonadvancing["class"] == ra.CLARIFICATION_NOOP
    report = site.settle_provenance(turn["sid"], turn["orders"])
    assert not report["halted"] and not site.halted
    assert ra.clarification_noop_problems(site.artifact()) == []
    # the experiment goes on: the next complete order commits the next minute, once
    nxt = _clarify(committed, VOLUME)
    assert _judge(committed, nxt) is not None and site.minutes_committed == (15, 30) and not site.halted


def test_b2_two_consecutive_clarifications_are_two_noops_on_the_same_minute(committed):
    for text in (INCOMPLETE, "Titrate norepinephrine to MAP 65."):
        turn = _clarify(committed, text)
        assert _judge(committed, turn) is None and not committed["site"].halted, committed["site"].halt_reason
    assert [q["outcome"] for q in committed["site"].no_advance_turns] == [ra.NONADVANCING_CLARIFICATION_NOOP] * 2
    assert committed["site"].minutes_committed == (15,)


def _refused(world, expected_class):
    site = world["site"]
    assert site.halted and site.halt_reason.startswith(ra.MINUTE_ALREADY_COMMITTED), (site.halt_reason, site.last_nonadvancing, [q.get("outcome") for q in site.no_advance_turns])
    assert site.records[-1]["nonadvancing"]["class"] == expected_class, site.records[-1].get("nonadvancing")
    assert not any(q.get("outcome") == ra.NONADVANCING_CLARIFICATION_NOOP for q in site.no_advance_turns)


def test_b3_without_the_turn_origin_the_proof_cannot_be_made_and_the_turn_fails_closed_unknown(committed):
    turn = _clarify(committed)
    assert _judge(committed, turn, origin=None) is None
    _refused(committed, ra.UNKNOWN_NONADVANCING)


def test_b4_a_patient_state_that_changed_is_an_unsafe_mutation(committed):
    turn = _clarify(committed)
    after = deepcopy(turn["after"])
    after["family_state"] = {**dict(after.get("family_state") or {}), "norepinephrine": 7.0}
    assert _judge(committed, turn, after=after, origin=_origin(turn["origin_state"], after)) is None
    _refused(committed, ra.UNSAFE_MUTATION)


def test_b5_a_protected_field_that_changed_is_an_unsafe_mutation(committed):
    turn = _clarify(committed)
    assert _judge(committed, turn, origin=_origin(turn["origin_state"], turn["after"], rng=(3, 4))) is None
    _refused(committed, ra.UNSAFE_MUTATION)


def test_b6_a_settled_order_that_acted_is_an_unsafe_mutation(committed):
    turn = _clarify(committed)
    acted = [{**order, "fate": "EXECUTED"} for order in turn["orders"]]
    assert _judge(committed, turn, settled=acted) is None
    _refused(committed, ra.UNSAFE_MUTATION)


def test_b7_a_new_shadow_failure_is_unknown(committed):
    turn = _clarify(committed)
    committed["encounter"].shadow.failures.append(rs.ShadowFailure(15, "observe", "RuntimeError", "injected during the clarification", rs.UNEXPECTED))
    assert _judge(committed, turn) is None
    _refused(committed, ra.UNKNOWN_NONADVANCING)


def test_b8_a_shadow_that_advanced_is_unknown(committed, monkeypatch):
    turn = _clarify(committed)
    real = rs.ShadowSession.minutes
    monkeypatch.setattr(rs.ShadowSession, "minutes", property(lambda self: list(real.fget(self)) + list(real.fget(self))[-1:]))     # one more sample than was judged
    assert _judge(committed, turn) is None
    _refused(committed, ra.UNKNOWN_NONADVANCING)


def test_b9_a_pressure_that_is_not_the_committed_one_is_not_a_noop(committed):
    turn = _clarify(committed)
    after = deepcopy(turn["after"])
    after["observable"] = {**dict(after["observable"]), "sbp": int(after["observable"]["sbp"]) + 9}
    origin = _origin(after, after)                      # even an origin that agrees with it cannot carry a pressure the minute did not commit
    assert _judge(committed, turn, after=after, origin=origin) is None
    _refused(committed, ra.UNKNOWN_NONADVANCING)
    assert committed["site"].records[-1]["nonadvancing"]["proof"]["pressure_is_the_committed_one"] is False


def test_b10_a_ledger_that_acted_after_the_noop_was_recorded_is_a_provenance_contradiction(committed):
    turn = _clarify(committed)
    assert _judge(committed, turn) is None and not committed["site"].halted
    report = committed["site"].settle_provenance(turn["sid"], [{**order, "fate": "EXECUTED"} for order in turn["orders"]])
    assert report["halted"] and committed["site"].halted and ra.PROVENANCE_CONTRADICTION in committed["site"].halt_reason


def test_b11_the_artifact_names_every_tampered_noop(committed):
    turn = _clarify(committed)
    assert _judge(committed, turn) is None
    artifact = committed["site"].artifact()
    assert ra.clarification_noop_problems(artifact) == []

    def tampered(change):
        body = deepcopy(artifact)
        change(body["no_advance_turns"][-1])
        return ra.clarification_noop_problems(body)
    assert tampered(lambda q: q["proof"].update(patient_state_unchanged=False))
    assert tampered(lambda q: q.update(action_kinds=["fluid"]))
    assert tampered(lambda q: q["held_orders"].append({"order_id": "x", "class": "fluid", "fate": "EXECUTED"}))
    assert tampered(lambda q: q.update(minute=999, attached_to_committed_minute=999))
    assert tampered(lambda q: q.update(pressure_digest="0" * 64))
    assert tampered(lambda q: q.update(nonadvancing_class=ra.UNSAFE_MUTATION))


def test_b12_the_turn_origin_is_read_from_the_open_transactional_turn_only():
    class Site:
        grant, halted, minutes_committed, records, no_advance_turns = {"grant_id": "x"}, False, (15,), [], []
    store_ = {"state": {"sim_time": 15}, "last_executed_action": None, "rng_counter": 2, ra.SITE_KEY: Site()}
    assert ra.turn_origin(store_) is None, "no open turn: no origin, so no proof"
    turn = rat.AuthorityTurn(store_, store_[ra.SITE_KEY])
    with turn:
        origin = ra.turn_origin(store_)
        assert origin["originals"]["state"] is turn.originals["state"] and origin["current"]["state"] is store_["state"]
        assert origin["originals"]["state"] is not origin["current"]["state"], "the working copy is not the original"
        assert set(origin["originals"]) == set(origin["current"]) == set(ra.NOOP_PROTECTED_FIELDS)


def test_b13_a_turn_judged_twice_never_commits_the_same_minute_twice(committed):
    """A duplicate request: the same time-advancing turn handed to the site again after its minute committed. It carries an action, so it is never a no-op: it fails closed."""
    turn = _clarify(committed, VOLUME)
    assert _judge(committed, turn) is not None and committed["site"].minutes_committed == (15, 30)
    again = dict(turn)
    again["before"] = dict(turn["after"])                              # the clock already stands at the committed minute
    assert committed["site"].minute(again["before"], deepcopy(turn["after"]), committed["encounter"].shadow, turn["ran"], turn["sid"], ra.ORDER_TURN,
                                    settled=turn["orders"], origin=_origin(turn["after"], turn["after"])) is None
    _refused(committed, ra.UNSAFE_MUTATION)
    assert committed["site"].minutes_committed == (15, 30), "no minute committed twice, no sample duplicated"


def test_b14_an_order_the_reader_did_not_recognize_is_a_noop(committed):
    turn = _clarify(committed, "Keep NPO.")
    assert [o["fate"] for o in turn["orders"]] == ["UNRECOGNIZED"] and turn["ran"] == []
    assert _judge(committed, turn) is None and not committed["site"].halted, committed["site"].halt_reason
    assert committed["site"].no_advance_turns[-1]["outcome"] == ra.NONADVANCING_CLARIFICATION_NOOP
    # the settlement after the judgement reads the SAME rule the proof used: an unrecognized order did not act, so the settled noop is not halted after the fact
    report = committed["site"].settle_provenance(turn["sid"], turn["orders"])
    assert not report["halted"] and not committed["site"].halted, committed["site"].halt_reason


def test_b15_a_recorded_unmodelled_medication_is_decision_c_and_is_never_called_a_mutation(committed):
    turn = _clarify(committed, "Give ondansetron 4 mg IV.")
    assert [(o["class"], o["fate"]) for o in turn["orders"]] == [("not_modelled", "RECORDED_NOT_MODELLED")]
    assert _judge(committed, turn) is None
    site = committed["site"]
    assert site.halted and site.halt_reason.startswith(ra.UNSUPPORTED_AUTHORITY_ACTION) and "not_modelled" in site.halt_reason, site.halt_reason
    assert site.records[-1]["nonadvancing"]["class"] == ra.UNKNOWN_NONADVANCING


def test_b16_a_noop_carries_the_state_digests_and_a_tampered_digest_is_named(committed):
    turn = _clarify(committed)
    assert _judge(committed, turn) is None
    artifact = committed["site"].artifact()
    digests = artifact["no_advance_turns"][-1]["state_digests"]
    assert set(digests) == {"origin_state", "turn_state", "judged_state", "origin_protected", "turn_protected"}
    assert digests["origin_state"] == digests["turn_state"] == digests["judged_state"]
    body = deepcopy(artifact)
    body["no_advance_turns"][-1]["state_digests"]["turn_state"] = "0" * 64
    assert ra.clarification_noop_problems(body)
    body = deepcopy(artifact)
    body["no_advance_turns"][-1]["state_digests"] = {}
    assert ra.clarification_noop_problems(body)


# -- P3-541: a broad sweep of real-world phrasings through the frozen reader and the pilot's two readings ------------------------------------------------------

import gi_pilot as gp  # noqa: E402

DEFINITIVE_REQUESTS = ("GI consult.", "Consult GI.", "Call gastroenterology.", "Urgent EGD.", "Arrange an urgent endoscopy.", "Scope him now.", "Get IR for embolization.",
                       "Embolize the bleeding vessel.", "Surgical consult.", "Call the surgeons.", "Take him to theatre.", "Control the bleeding.", "Achieve hemostasis.",
                       "Haemostasis now.", "Band the varices.", "He needs TIPS.", "Source control now.", "Page the GI fellow.", "Upper endoscopy please.",
                       "Notify gastroenterology for an urgent scope.", "Get the GI team to scope him.", "Call IR.", "He needs an OGD.", "Book theatre for laparotomy.")
NOT_REQUESTS = ("Hold off on GI for now.", "What is the GI plan?", "Is GI aware?", "Do not consult gastroenterology yet.", "GI has been informed by the ED.",
                "Plan: resuscitate first, endoscopy once stable.", "Check CBC with bands.", "Give 1 L normal saline over 15 minutes, GI bleed protocol.", "If he rebleeds, call GI.",
                "Consult ICU.", "Upper GI bleed, likely ulcer.", "Transfuse 2 units of packed red cells over 30 minutes given ongoing GI bleeding.")


@pytest.mark.parametrize("text, is_request", [(text, True) for text in DEFINITIVE_REQUESTS] + [(text, False) for text in NOT_REQUESTS])
def test_b17_the_pilot_reads_a_request_for_definitive_control_from_the_actions_or_the_orders_and_not_from_a_negation_question_or_diagnosis(text, is_request):
    """Each phrasing goes through the frozen reader and the engine of a fresh arrival; the pilot's barrier is the structural reading of the actions OR the reading of the
    orders and words (``gi_pilot_ui.barrier``). Every request is found (a structural consultation, or the orders' own words); nothing that is not a request is."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        turn = _turn(acceptance.Encounter(CASE), text)
    found = bool(gp.definitive_actions(turn["ran"]) or gp.definitive_intent(turn["orders"], text))
    assert found is is_request, (text, [(order.get("class"), order.get("fate")) for order in turn["orders"]])


def test_b18_the_final_fail_safe_table_names_only_known_exits_and_keeps_the_ratified_table_unchanged():
    """FAIL_SAFE is the table as ratified (it is pinned by the stored scope record); FAIL_SAFE_FINAL is the table as the pilot runs after this cycle."""
    assert len(gp.FAIL_SAFE) == 15 and len(gp.FAIL_SAFE_FINAL) == 18
    for situation, behaviour, exit_kind in gp.FAIL_SAFE_FINAL:
        assert situation and behaviour and (exit_kind is None or exit_kind in gp.EXITS), situation
    text = " ".join(f"{situation} {behaviour}" for situation, behaviour, _ in gp.FAIL_SAFE_FINAL)
    for needle in ("PROVEN clarification no-op", "fails closed", "development boundary", "never resumed", "decision C"):
        assert needle in text, needle
