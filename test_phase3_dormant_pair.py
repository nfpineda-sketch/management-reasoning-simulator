"""P3-212, P3-213 and P3-214: the disposition of an executed order with no common physiology, the dormant pair transaction, and the V1 binding in the
REAL layer. No authority anywhere in this file: every commit below is made on a COPY, through the test-only approval pattern of the P3-28 certification,
and the encounter's own state is never the target.
"""
import copy
import dataclasses
import json
import os
import tempfile
from pathlib import Path

import pytest

import observable_view as view
import pilot_acceptance as acceptance
import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_authority_store as store
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import test_gi_snapshot_binding as old_binding
from clinical_core import systemic_consciousness as sc

ROOT = Path(__file__).resolve().parent
CASE = "gi_bleed_57m"
TEST_ONLY_SNAPSHOT = {"id": "test_only_pair_point", "approved_by_faculty": True,
                      "decision": "TEST ONLY: exists inside one test session, approves nothing",
                      "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID, "parameters": {"test_only_placeholder": 1.0}}
STORE_DIR = tempfile.mkdtemp(prefix="phase3-pair-")
BEST = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: TEST_ONLY_SNAPSHOT["id"], ra.ENVIRONMENT_FLAG: "development",
        rs.FLAG: rs.MODE_SHADOW_COMPARE, store.STORE_FLAG: STORE_DIR}


@pytest.fixture
def approved(monkeypatch, tmp_path):
    monkeypatch.setitem(ra._APPROVED_SNAPSHOT_POINTS, TEST_ONLY_SNAPSHOT["id"], TEST_ONLY_SNAPSHOT)
    for name, value in BEST.items():
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)
    directory = tmp_path / "phase3_authority"
    monkeypatch.setenv(store.STORE_FLAG, str(directory))
    return {"environ": {**BEST, store.STORE_FLAG: str(directory)}}


@pytest.fixture(scope="module")
def gi_state():
    with ev.shadow(rs.MODE_OFF):
        return copy.deepcopy(acceptance.Encounter(CASE).state)


@pytest.fixture(scope="module")
def bound():
    return pair.bind(str(ROOT))


PRESSURES = {"sbp": 88, "dbp": 54}
GOOD = ra.digest_of({"sbp": 88.4, "dbp": 54.1, "map": 65.5})


def payload(minute=0, category=3, word=None, pulse=True, sbp=88, dbp=54):
    return pair.PairPayload(minute=minute, sbp=sbp, dbp=dbp, map=ra.derived_map(sbp, dbp), consciousness_category=category,
                            mental_status=word if word is not None else pair.WORD_OF.get(category), pulse_present=pulse)


def pressure_kwargs(**over):
    base = dict(invariants_hold=True, replay_digest=GOOD, expected_digest=GOOD, unsupported=(), legacy_arrest=False, failures=())
    base.update(over)
    return base


def pair_conditions(**over):
    base = dict(consciousness_ok={}, interval_ok=True, boundary_clear=True, window_open=True, one_course=True)
    base.update(over)
    return base


def transaction(state, bound, snapshot=TEST_ONLY_SNAPSHOT, **kw):
    tx = pair.PairAuthorityTransaction(minute=int(state["sim_time"]), case_id=CASE, snapshot=snapshot, bound=bound)
    tx.capture(state).compute(kw.pop("payload", payload(int(state["sim_time"]))), {"sbp": 90, "dbp": 55})
    return tx


# -- P3-212: EXECUTED_NO_COMMON_PHYSIOLOGY ------------------------------------------------------------------------------------------------------------

def test_the_disposition_vocabulary_separates_the_four_things_the_assignment_names():
    assert set(ra.ACTION_DISPOSITIONS) == {"SUPPORTED_MODELED", "STRUCTURAL_ONLY", "EXECUTED_NO_COMMON_PHYSIOLOGY", "HELD_NOT_EXECUTED",
                                           "TERMINAL_NOT_EXECUTABLE", "UNSUPPORTED_ACTION"}
    expected = {("vascular_access", None): ra.EXECUTED_NO_COMMON_PHYSIOLOGY, ("vascular_access", "EXECUTED"): ra.EXECUTED_NO_COMMON_PHYSIOLOGY,
                ("vascular_access", "DUPLICATE_IGNORED"): ra.EXECUTED_NO_COMMON_PHYSIOLOGY,
                ("vascular_access", "HELD_CLARIFICATION"): ra.HELD_NOT_EXECUTED, ("vascular_access", "HELD_REASONING"): ra.HELD_NOT_EXECUTED,
                ("vascular_access", "TERMINAL_NOT_EXECUTABLE"): ra.TERMINAL_NOT_EXECUTABLE,
                ("vascular_access", "RECORDED_NOT_MODELLED"): ra.UNSUPPORTED_ACTION, ("vascular_access", "UNRECOGNIZED"): ra.UNSUPPORTED_ACTION,
                ("fluid", "EXECUTED"): ra.SUPPORTED_MODELED, ("blood", None): ra.SUPPORTED_MODELED, ("consult", None): ra.STRUCTURAL_ONLY,
                ("reassessment", None): ra.STRUCTURAL_ONLY, ("intubation", "EXECUTED"): ra.UNSUPPORTED_ACTION, ("", None): ra.UNSUPPORTED_ACTION,
                ("untyped_action", None): ra.UNSUPPORTED_ACTION}
    for (kind, fate), disposition in expected.items():
        assert ra.disposition_of(kind, fate) == disposition, (kind, fate)
    assert ra.disposition_of("  VASCULAR_ACCESS ", "executed") == ra.EXECUTED_NO_COMMON_PHYSIOLOGY


def test_212a_the_disposition_is_an_explicit_allowlist_with_one_member_and_it_cannot_be_widened_by_a_rule():
    assert dict(ra.NO_COMMON_PHYSIOLOGY_ACTIONS).keys() == {"vascular_access"} and all(ra.NO_COMMON_PHYSIOLOGY_ACTIONS.values())
    with pytest.raises(TypeError):
        ra.NO_COMMON_PHYSIOLOGY_ACTIONS["intubation"] = "x"                          # read-only
    for kind in ("intubation", "anticoagulation", "aspirin", "norepinephrine", "dextrose", "oral_carbohydrate", "antipyretic", "disposition", "discharge",
                 "not_modelled", "unrecognized", "a_class_nobody_declared", "monitoring", "urinary_catheter"):
        assert ra.unsupported_among((kind,)) == (kind,), kind                         # nothing else stops being unsupported
        assert ra.disposition_of(kind, "EXECUTED") == ra.UNSUPPORTED_ACTION, kind
    assert ra.unsupported_among(("vascular_access", "fluid", "intubation")) == ("intubation",)


def test_212b_the_acknowledgement_is_recorded_exactly_once_with_no_contributor_and_no_physiological_mutation():
    rows = [{"order_id": "m001-t01-0-vascular_access", "type": "vascular_access"}, {"order_id": "m001-t01-0-vascular_access", "type": "vascular_access"},
            {"order_id": "m001-t01-1-fluid", "type": "fluid"}, {"order_id": "m001-t02-0-vascular_access", "class": "vascular_access", "fate": "HELD_REASONING"}]
    found = ra.executed_no_common_physiology(rows)
    assert [row["order_id"] for row in found] == ["m001-t01-0-vascular_access"]            # a repeated receipt is ONE event; a held order is not executed
    assert found[0]["contributor"] is None and found[0]["physiological_mutation"] is False and found[0]["disposition"] == ra.EXECUTED_NO_COMMON_PHYSIOLOGY
    assert ra.executed_no_common_physiology(None) == () and ra.executed_no_common_physiology([{"type": "fluid"}]) == ()


def _real_turn(text):
    seen = {}
    real = acceptance.Encounter._execute

    def execute(self, parsed, line):
        out = real(self, parsed, line)
        seen["run"] = out[2]
        return out
    acceptance.Encounter._execute = execute
    try:
        with ev.shadow(rs.MODE_SHADOW_COMPARE):
            encounter = acceptance.Encounter(CASE)
            entry = encounter.order(text)
    finally:
        acceptance.Encounter._execute = real
    return encounter, entry, seen["run"]


def test_212c_a_real_iv_line_turn_is_executed_by_the_engine_traced_once_and_does_not_make_the_turn_unsupported():
    encounter, entry, run = _real_turn("Place an IV line.")
    assert entry["executed"] is True and ra.action_kinds(run) == ("vascular_access",)               # real engine execution: it is in the turn's run list
    settled = [dict(item) for item in entry["orders"]]
    assert [(item["class"], ra.disposition_of(item["class"], item["fate"])) for item in settled] == [("vascular_access", ra.EXECUTED_NO_COMMON_PHYSIOLOGY)]
    assert ra.unsupported_among(ra.action_kinds(run)) == ()
    # the shadow still DECLARES the gap (nothing is hidden) and the authority acknowledges it instead of halting on it
    gaps = [gap.get("kind") for gap in encounter.shadow.gaps]
    assert gaps == ["vascular_access"] and ra.unsupported_among(gaps) == ()
    assert len(ra.executed_no_common_physiology(ra.action_fates(run))) == 1


def test_212d_the_iv_line_changes_no_common_physiology_the_common_course_is_identical_with_and_without_it():
    def course(orders):
        with ev.shadow(rs.MODE_SHADOW_COMPARE):
            encounter = acceptance.Encounter(CASE)
            for text in orders:
                encounter.order(text)
            encounter.wait_until(30, step=1)
            # every reading of every minute: the state DIGEST also carries the mirrored order ids (the IV order is mirrored as a declared gap), which are
            # bookkeeping and not physiology, so the physiology is compared reading by reading
            return [(item.minute, dict(item.derived)) for item in encounter.shadow.runner.results], encounter
    with_iv, encounter = course(["Place an IV line.", "Give 1 L of normal saline."])
    without, other = course(["Give 1 L of normal saline."])
    common = min(len(with_iv), len(without))
    assert common >= 20 and with_iv[:common] == without[:common]
    assert [row[0] for row in with_iv] == [row[0] for row in without]
    # the executed IV order produced no contributor for the common core
    assert all("vascular" not in str(gap.get("kind") or "") or gap.get("why") for gap in encounter.shadow.gaps)


def test_212e_a_unsupported_class_next_to_an_iv_line_still_halts_and_a_held_iv_line_does_not_count_as_executed():
    kinds = ra.action_kinds([{"type": "vascular_access"}, {"type": "intubation"}])
    assert ra.unsupported_among(kinds) == ("intubation",)
    assert ra.executed_no_common_physiology([{"order_id": "a", "type": "vascular_access", "fate": "HELD_CLARIFICATION"}]) == ()


# -- P3-213: the pair payload and the atomic transaction ------------------------------------------------------------------------------------------------

def test_the_payload_is_the_pair_and_nothing_else_and_it_is_complete_or_it_is_not_a_payload():
    good = payload(5, 3)
    assert pair.payload_problems(good) == [] and good.digest() == payload(5, 3).digest() and set(good.as_dict()) == {"minute"} | set(pair.PAIR_FIELDS)
    assert pair.PAIR_FIELDS == ("sbp", "dbp", "map", "consciousness_category", "mental_status", "pulse_present")
    assert not set(pair.PAIR_FIELDS) & {"hr", "spo2", "respiratory_rate", "crt", "rhythm", "lactate", "hemoglobin", "collapse_state"}
    bad = {"category 4": payload(5, 4, word="Alert"), "bool category": dataclasses.replace(good, consciousness_category=True),
           "word is not the category": payload(5, 3, word="Alert"), "map not the display mean": dataclasses.replace(good, map=1),
           "nan pressure": dataclasses.replace(good, sbp=float("nan")), "string pressure": dataclasses.replace(good, sbp="88"),
           "pulse not bool": dataclasses.replace(good, pulse_present=1), "not a payload": {"sbp": 88}}
    for label, item in bad.items():
        assert pair.payload_problems(item), label


def test_a_valid_pair_commits_into_a_copy_with_the_pressures_in_the_observable_and_the_consciousness_in_the_overlay_only(gi_state, approved, bound):
    state = copy.deepcopy(gi_state)
    before = ra.canonical(state)
    assert (state["observable"]["sbp"], state["observable"]["dbp"]) == (88, 54)                                       # the arrival's pressures
    tx = transaction(state, bound, payload=payload(int(state["sim_time"]), 3, sbp=91, dbp=57))                       # another pair: all three pressures move
    assert tx.validate(pressure=pressure_kwargs(), **pair_conditions()) is True and tx.state == pair.PAIR_VALIDATED
    prepared = tx.commit(state, environ=approved["environ"])
    assert tx.state == pair.PAIR_COMMITTED and tx.committed == pair.PAIR_FIELDS and ra.canonical(state) == before            # the target is untouched
    assert prepared is not state and prepared["observable"] is not state["observable"]
    assert (prepared["observable"]["sbp"], prepared["observable"]["dbp"], prepared["observable"]["map"]) == (91, 57, ra.derived_map(91, 57))
    assert prepared["observable"]["mental_status"] == state["observable"]["mental_status"]                          # the live word is NEVER written
    overlay = prepared[view.OVERLAY_KEY]
    assert view.overlay_problems(overlay) == [] and overlay["common"] == {"consciousness_category": 3, "mental_status": "Unresponsive", "pulse_present": True}
    assert overlay["mapped_into_live_field"] is False and overlay["legacy"] == {} and overlay["views"] == {} and overlay["minute"] == state["sim_time"]
    outside, observable_moved = pair.moved_fields(state, prepared)
    assert outside == {view.OVERLAY_KEY} and observable_moved == {"sbp", "dbp", "map"}
    # the site's own helper would have hidden the observable half: it returns the outside keys alone when there are any
    assert ra.AuthoritySite._moved(state, prepared) == {view.OVERLAY_KEY}
    # and no reader sees the common word: the frozen readers still read the legacy one
    assert all(view.mental_status_for(prepared, reader) == state["observable"]["mental_status"] for reader in view.ROUTED_READERS)
    record = tx.record()
    assert record["writes_the_live_mental_status"] is False and record["committed"] == list(pair.PAIR_FIELDS) and record["common_core_runtime_authority"] is False


def test_unresponsive_with_a_pulse_is_a_valid_common_state_and_the_legacy_live_field_is_not_where_it_goes(gi_state, approved, bound):
    """FD-P3-NEW-02: the common physiology may represent UNRESPONSIVE while the pulse is present. It is carried by the overlay, not by mental_status."""
    state = copy.deepcopy(gi_state)
    tx = transaction(state, bound, payload=payload(state["sim_time"], 3, pulse=True))
    assert tx.validate(pressure=pressure_kwargs(), **pair_conditions()) is True
    prepared = tx.commit(state, environ=approved["environ"])
    assert prepared[view.OVERLAY_KEY]["common"]["mental_status"] == "Unresponsive" and prepared[view.OVERLAY_KEY]["common"]["pulse_present"] is True
    assert prepared["observable"]["mental_status"] == "Alert" and prepared["observable"]["pulse_present"] is True
    assert view.common_consciousness(prepared)["mental_status"] == "Unresponsive"                                 # a diagnostic reader may see it; no resident does


@pytest.mark.parametrize("label,conditions", [
    ("interval minute failed", {"interval_ok": False}), ("collapse boundary reached", {"boundary_clear": False}), ("window closed", {"window_open": False}),
    ("not one course", {"one_course": False}),
])
def test_213a_a_failure_in_any_pair_condition_commits_nothing_and_leaves_no_pressure_only_path(gi_state, approved, bound, label, conditions):
    state = copy.deepcopy(gi_state)
    tx = transaction(state, bound)
    assert tx.validate(pressure=pressure_kwargs(), **pair_conditions(**conditions)) is False and tx.state == pair.PAIR_ABORTED
    with pytest.raises(ra.AuthorityRefused):
        tx.commit(state, environ=approved["environ"])
    # the pressure half passed on its own and is NOT left committable: the inner transaction was aborted with the pair
    assert tx._pressure.state == ra.ABORTED and tx._pressure.committed == ()
    with pytest.raises(ra.AuthorityRefused):
        tx._pressure.commit(state, environ=approved["environ"])
    assert tx.committed == () and ra.canonical(state) == ra.canonical(gi_state)


@pytest.mark.parametrize("label,kwargs", [
    ("replay mismatch", {"replay_digest": ra.digest_of({"other": 1})}), ("invariants fail", {"invariants_hold": False}), ("legacy arrest", {"legacy_arrest": True}),
    ("unsupported action", {"unsupported": ("intubation",)}), ("undeclared management", {"unsupported": None}),
])
def test_213a_a_failure_of_the_pressure_half_commits_no_consciousness_either(gi_state, approved, bound, label, kwargs):
    state = copy.deepcopy(gi_state)
    tx = transaction(state, bound)
    assert tx.validate(pressure=pressure_kwargs(**kwargs), **pair_conditions()) is False
    assert "pressure_half_validated" in tx.failures and tx.state == pair.PAIR_ABORTED
    with pytest.raises(ra.AuthorityRefused):
        tx.commit(state, environ=approved["environ"])
    assert view.OVERLAY_KEY not in state


@pytest.mark.parametrize("label,item", [
    ("category off the ladder", payload(0, 4, word="Alert")), ("word is not the category", payload(0, 3, word="Alert")),
    ("arrest in the pair", payload(0, 3, pulse=False)), ("bool category", None),
])
def test_213a_a_failure_of_the_consciousness_half_commits_no_pressure_either(gi_state, approved, bound, label, item):
    state = copy.deepcopy(gi_state)
    item = dataclasses.replace(payload(0, 3), consciousness_category=True) if item is None else item
    tx = transaction(state, bound, payload=item)
    assert tx.validate(pressure=pressure_kwargs(), **pair_conditions()) is False and tx.state == pair.PAIR_ABORTED
    assert tx._pressure.state == ra.ABORTED
    with pytest.raises(ra.AuthorityRefused):
        tx.commit(state, environ=approved["environ"])
    assert state["observable"]["sbp"] == gi_state["observable"]["sbp"]


def test_213a_a_hand_built_transaction_cannot_skip_validation_and_an_unbound_pair_never_commits(gi_state, approved, bound):
    state = copy.deepcopy(gi_state)
    tx = transaction(state, bound)
    with pytest.raises(ra.AuthorityRefused):
        tx.commit(state, environ=approved["environ"])                                  # never validated
    tx.state = pair.PAIR_VALIDATED                                                      # forced: the payload and the binding are still re-checked
    forged = pair.BoundSnapshot(*[getattr(bound, f.name) for f in dataclasses.fields(bound)][:9],
                                dataclasses.replace(bound.profile, amendment_2=sc.WITNESSES["LOW"]), pair.profile_digest(dataclasses.replace(bound.profile, amendment_2=sc.WITNESSES["LOW"])))
    tx.bound = forged
    with pytest.raises(ra.AuthorityRefused):
        tx.commit(state, environ=approved["environ"])
    tx2 = pair.PairAuthorityTransaction(minute=int(state["sim_time"]), case_id=CASE, snapshot=TEST_ONLY_SNAPSHOT, bound=None)
    tx2.capture(state).compute(payload(0), None)
    assert tx2.validate(pressure=pressure_kwargs(), **pair_conditions()) is False and "snapshot_is_v1" in tx2.failures


def test_213_the_pair_is_dormant_with_the_flag_off_nothing_commits_even_when_every_check_passes(gi_state, approved, bound):
    state = copy.deepcopy(gi_state)
    tx = pair.PairAuthorityTransaction(minute=int(state["sim_time"]), case_id=CASE, snapshot=TEST_ONLY_SNAPSHOT, bound=bound)
    tx.capture(state).compute(payload(0), None)
    assert tx.validate(pressure=pressure_kwargs(), **pair_conditions()) is True
    with pytest.raises(ra.AuthorityRefused) as refused:
        tx.commit(state, environ={})                                                    # no flag, no approval: the nine-condition gate refuses at commit
    assert "gate" in str(refused.value) and tx.state == pair.PAIR_ABORTED and view.OVERLAY_KEY not in state
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False and sorted(ra.APPROVED_POINT_DIGESTS) == ["gi_pressure_committed"] and ra.AUTHORITY_DOMAIN == ("sbp", "dbp", "map")


def test_213b_collapse_is_boundary_information_only_it_is_in_no_payload_no_overlay_and_no_write(gi_state, approved, bound):
    assert "collapse_state" not in pair.PAIR_FIELDS and "collapse" not in "".join(pair.OBSERVABLE_WRITES + pair.OVERLAY_WRITES)
    assert set(view.COMMON_FIELDS) == {"consciousness_category", "mental_status", "pulse_present"}
    state = copy.deepcopy(gi_state)
    tx = transaction(state, bound)
    tx.validate(pressure=pressure_kwargs(), **pair_conditions())
    prepared = tx.commit(state, environ=approved["environ"])
    assert not [key for key in json.dumps(prepared[view.OVERLAY_KEY]).split('"') if "collapse" in key]


def test_213_no_other_field_can_ride_along_the_prepared_mapping_changes_exactly_the_pair(gi_state, approved, bound):
    state = copy.deepcopy(gi_state)
    tx = transaction(state, bound)
    tx.validate(pressure=pressure_kwargs(), **pair_conditions())
    prepared = tx.commit(state, environ=approved["environ"])
    changed = {key for key in set(prepared) | set(state) if ra.canonical(prepared.get(key)) != ra.canonical(state.get(key))}
    assert changed == {"observable", view.OVERLAY_KEY}
    observable = {key for key in set(prepared["observable"]) | set(state["observable"])
                  if ra.canonical(prepared["observable"].get(key)) != ra.canonical(state["observable"].get(key))}
    assert observable <= {"sbp", "dbp", "map"}


# -- P3-214: the V1 binding in the real layer ---------------------------------------------------------------------------------------------------------

def test_the_binding_lives_in_the_layer_and_the_old_test_side_module_is_only_a_reexport_of_it():
    assert "runtime_authority_pair.py" in rs.LAYER_SOURCES
    for name in ("bind", "bound_is_v1", "verify_record", "verify_ratification", "BoundSnapshot", "SnapshotBindingError", "build_profile", "runner_is_bound",
                 "open_bound_runner", "BoundSnapshotAdapter", "lineage_is_v1", "live_lineage", "plain", "pressure_point_matches", "profile_digest",
                 "V1_VALUES_DIGEST", "V1_PROFILE_DIGEST", "V1_FULL_DIGEST", "V1_RATIFICATION_DIGEST", "REFUSALS"):
        assert getattr(old_binding, name) is getattr(pair, name), name


def test_214_the_binding_requires_every_identity_the_assignment_lists_and_builds_the_profile_only_from_the_record(bound):
    summary = bound.summary()
    assert (summary["snapshot_id"], summary["version"]) == ("GI_DEVELOPMENT_SNAPSHOT_V1", 1)
    for field, pinned in (("file_sha256", pair.V1_FILE_SHA256), ("record_digest", pair.V1_RECORD_DIGEST), ("identity_digest", pair.V1_IDENTITY_DIGEST),
                          ("profile_digest", pair.V1_PROFILE_DIGEST), ("core_digest", pair.V1_CORE_DIGEST), ("core_version", pair.V1_CORE_VERSION)):
        assert summary[field] == pinned and len(str(pinned)) > 8
    assert pair.digest(bound.value_map()) == pair.V1_VALUES_DIGEST and pair.profile_digest(bound.profile) == pair.V1_PROFILE_DIGEST
    record = json.loads((ROOT / pair.SNAPSHOT_FILE).read_text(encoding="utf-8"))
    assert pair.digest(record) == pair.V1_FULL_DIGEST and bound.profile.amendment_2.to_dict() == record["values"]
    source = (ROOT / "runtime_authority_pair.py").read_text(encoding="utf-8")
    build = source.split("def build_profile")[1].split("def bound_is_v1")[0]
    assert "WITNESSES" not in build.split('"""')[2] and "development_profile(" not in build.split('"""')[2]
    assert all(bound.profile_digest != pair.profile_digest(dataclasses.replace(bound.profile, amendment_2=witness)) for witness in sc.WITNESSES.values())


def _tampered(change):
    record = json.loads((ROOT / pair.SNAPSHOT_FILE).read_text(encoding="utf-8"))
    change(record)
    return record


TAMPER = {
    "wrong snapshot id": (lambda r: r.update(snapshot_id="GI_DEVELOPMENT_SNAPSHOT_V2"), pair.WRONG_SNAPSHOT_ID),
    "wrong version": (lambda r: r.update(version=2), pair.WRONG_VERSION),
    "modified parameter": (lambda r: r["values"].update(delivery_severe=0.51), pair.MODIFIED_PARAMETER),
    "modified parameter with recomputed digests": (lambda r: (r["values"].update(burden_clear_tau=9.0), r["immutability"].update(
        identity_digest=pair.digest(pair.identity_of(r)), record_digest=pair.digest({k: v for k, v in r.items() if k != "immutability"}))), pair.MODIFIED_PARAMETER),
    "wrong digest": (lambda r: r["immutability"].update(record_digest="0" * 64), pair.WRONG_DIGEST),
    "edited body": (lambda r: r.update(falsifiers=[]), pair.WRONG_DIGEST),
    "superseded_by set": (lambda r: r["immutability"].update(superseded_by="GI_DEVELOPMENT_SNAPSHOT_V2"), pair.WRONG_DIGEST),
    "wrong core lineage in the record": (lambda r: r["common_core_lineage"].update(digest="22b90a6f" + "0" * 56), pair.WRONG_CORE_LINEAGE),
    "partial snapshot": (lambda r: r["values"].pop("collapse_clear_tau"), pair.PARTIAL_SNAPSHOT),
    "extra parameter": (lambda r: r["values"].update(extra=1.0), pair.PARTIAL_SNAPSHOT),
    "a non-number": (lambda r: r["values"].update(delivery_normal="0.75"), pair.PARTIAL_SNAPSHOT),
    "LOW substituted": (lambda r: r.update(values=sc.WITNESSES["LOW"].to_dict()), pair.WITNESS_SUBSTITUTED),
    "HIGH substituted": (lambda r: r.update(values=sc.WITNESSES["HIGH"].to_dict()), pair.WITNESS_SUBSTITUTED),
    "CENTER_REFERENCE substituted": (lambda r: r.update(values=sc.WITNESSES["CENTER_REFERENCE"].to_dict()), pair.WITNESS_SUBSTITUTED),
    "registered as authority": (lambda r: r["authority"].update(registered_as_an_authority_artifact=True), pair.NOT_A_DEVELOPMENT_SNAPSHOT),
}


@pytest.mark.parametrize("label", sorted(TAMPER))
def test_214_every_forged_or_substituted_record_the_review_found_is_refused_by_the_layer(label):
    change, code = TAMPER[label]
    with pytest.raises(pair.SnapshotBindingError) as refused:
        pair.bind(str(ROOT), record=_tampered(change))
    assert code in refused.value.reasons, (label, refused.value.reasons)


def test_214_the_values_that_answer_differently_when_verified_and_when_built_cannot_change_the_profile():
    class Liar(float):
        def __new__(cls, real, told):
            self = super().__new__(cls, real)
            self._told = told
            return self

        def __float__(self):
            return self._told
    record = _tampered(lambda r: None)
    record["values"]["burden_rise_tau"] = Liar(record["values"]["burden_rise_tau"], 1.5)
    bound = pair.bind(str(ROOT), record=record)
    assert pair.bound_is_v1(bound) and bound.profile.amendment_2.burden_rise_tau == 1.964


def test_214_a_hand_built_binding_a_forged_ratification_and_an_offered_lineage_are_refused(monkeypatch, bound):
    low = sc.WITNESSES["LOW"].to_dict()
    profile = pair.build_profile(low)
    forged = pair.BoundSnapshot(pair.V1_ID, pair.V1_VERSION, tuple((n, float(low[n])) for n in sc.FIELDS), pair.V1_IDENTITY_DIGEST, pair.V1_RECORD_DIGEST,
                                pair.V1_FILE_SHA256, pair.V1_CORE_VERSION, pair.V1_CORE_DIGEST, pair.PRESSURE_POINT, profile, pair.profile_digest(profile))
    assert not pair.bound_is_v1(forged)
    with pytest.raises(pair.SnapshotBindingError):
        pair.BoundSnapshotAdapter(forged)
    with pytest.raises(pair.SnapshotBindingError):
        pair.PairDryEvaluator(forged, CASE, {"sim_time": 0})
    ratification = json.loads((ROOT / pair.RATIFICATION_FILE).read_text(encoding="utf-8"))
    for bad in ({**ratification, "faculty_decisions": {"FD-AUTH-01": "approved for authority"}}, {**ratification, "ratification_digest": "0" * 64},
                {"status": pair.RATIFIED, "snapshot_id": pair.V1_ID}):
        with pytest.raises(pair.SnapshotBindingError) as refused:
            pair.bind(str(ROOT), ratification=bad)
        assert refused.value.reasons == (pair.NOT_RATIFIED,)
    from clinical_core import amendment_2 as a2
    forged_lineage = {"version_id": pair.V1_CORE_VERSION, "digest": pair.V1_CORE_DIGEST, "bytes_digest": pair.V1_CORE_DIGEST, "certified": True}
    monkeypatch.setattr(a2, "amended_core_digest_now", lambda: "f" * 64)
    for lineage in (None, forged_lineage):
        with pytest.raises(pair.SnapshotBindingError) as refused:
            pair.bind(str(ROOT), lineage=lineage)
        assert refused.value.reasons == (pair.WRONG_CORE_LINEAGE,)


def test_214a_binding_promotes_nothing_to_an_authority_registry_and_registers_nothing(bound):
    before = (sorted(ra.APPROVED_SNAPSHOTS), sorted(ra._APPROVED_SNAPSHOT_POINTS), dict(ra.APPROVED_POINT_DIGESTS), sorted(sc.WITNESSES))
    pair.bind(str(ROOT))
    assert (sorted(ra.APPROVED_SNAPSHOTS), sorted(ra._APPROVED_SNAPSHOT_POINTS), dict(ra.APPROVED_POINT_DIGESTS), sorted(sc.WITNESSES)) == before
    assert before[0] == ["gi_pressure_committed"] and "GI_DEVELOPMENT_SNAPSHOT_V1" not in ra.APPROVED_SNAPSHOTS and "GI_DEVELOPMENT_SNAPSHOT_V1" not in ra._APPROVED_SNAPSHOT_POINTS
    ratification = json.loads((ROOT / pair.RATIFICATION_FILE).read_text(encoding="utf-8"))
    assert ratification["status"] == "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS" and ratification["authority"]["added_to_an_approved_authority_snapshot_registry"] is False
    assert os.environ.get(ra.AUTHORITY_FLAG) in (None, "") and rs.COMMON_CORE_RUNTIME_AUTHORITY is False
