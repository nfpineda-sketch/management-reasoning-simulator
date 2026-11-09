"""P3-53: the authority record links every consumed action to the order that authorized it.

P3-51 left ONE blocker: a provenance note nobody could explain, which P3-50 guessed came from a split
bundle or an order opened in an earlier turn. P3-52 measured the two GI acceptance batteries inside
``order_pipeline.settle`` -- the one place the repository itself pairs an action with its order -- and
refuted that guess:

* 170 of 170 consumed actions carry ``_order_id``, the key ``order_pipeline._order_by_action`` resolves
  orders by, so the direct link is total;
* 0 of 170 reach back to an order opened in an earlier submission;
* 2 of 170 resolve to an order whose class and creation minute disagree with the action's, and both are
  the ``reload_resume`` scenario of ``pilot_acceptance``: a fresh ``Encounter`` opens its shadow at
  minute 0 and then has its state AND its ledger replaced by a copy of another encounter's minute 15,
  without restoring the turn counter. Its first turn is called ``t0`` again, its action takes
  ``_order_id = "t0:0"``, and ``open_turn`` reuses the INHERITED ``t0:0`` instead of opening its own.

So ``order_id`` is canonical within one encounter's ledger and not across encounters. The link is
therefore resolved by identity and then CHECKED, never trusted blind, and each check is a named thing
the record can be wrong about.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_store as store
import runtime_shadow as rs

ROOT = Path(__file__).resolve().parent
CASE = "gi_bleed_57m"
SNAP = "gi_pressure_committed"
STORE_DIR = tempfile.mkdtemp(prefix="phase3-authority-lineage-")

#: What P3-41 measured BEFORE any provenance work, and what P3-46 pinned: the lineage may not move it.
P341_TRAJECTORY = (
    {"minute": 30, "written": {"sbp": 80, "dbp": 49, "map": 59}},
    {"minute": 45, "written": {"sbp": 101, "dbp": 62, "map": 75}},
    {"minute": 60, "written": {"sbp": 112, "dbp": 68, "map": 83}},
)


def _environ(**extra):
    out = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: SNAP,
           ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE,
           store.STORE_FLAG: STORE_DIR}
    out.update(extra)
    return out


@pytest.fixture(autouse=True)
def _pinned_store(monkeypatch):
    monkeypatch.setenv(store.STORE_FLAG, STORE_DIR)


def _run(monkeypatch, *, experiment_id, orders_hook=None, script=None):
    """One real development authority encounter, in ``app.py``'s own sequence."""
    import pilot_acceptance as acceptance
    for name, value in _environ().items():
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)
    encounter = acceptance.Encounter(CASE)
    site = ra.open_site(encounter.state, environ=dict(os.environ), experiment_id=experiment_id)
    assert site is not None
    real_observe = type(encounter.shadow).observe
    real_order = type(encounter).order
    submissions, turns = [], []

    def hooked_observe(self, before, state, parsed, result, run, submission_id):
        real_observe(self, before, state, parsed, result, run, submission_id)
        submissions.append(submission_id)
        # Exactly what ``app.py`` hands the minute, tags included.
        turns.append({"submission": submission_id,
                      "ran": [{"order_id": a.get("_order_id"), "type": a.get("type"),
                               "written_at_min": a.get("_written_at_min")}
                              for a in list(run or []) if isinstance(a, dict)]})
        prepared = site.minute(before, state, self, run, submission_id)
        if prepared is not None:
            state.clear()
            state.update(prepared)

    def hooked_order(self, text):
        before = len(submissions)
        entry = real_order(self, text)
        if len(submissions) > before:
            orders = [dict(order) for order in (entry.get("orders") or [])]
            if orders_hook is not None:
                orders = orders_hook(orders)
            turns[-1]["orders"] = [dict(o) for o in orders]
            site.settle_provenance(submissions[-1], orders)
        return entry

    type(encounter.shadow).observe = hooked_observe
    type(encounter).order = hooked_order
    try:
        scripts = acceptance.scripts(CASE)
        for text in (script or ["Reassess in 30 minutes.",
                                scripts["correct"] + " Reassess in 15 minutes."]):
            encounter.order(text.format(**scripts) if "{" in text else text)
        encounter.wait_until(60)
    finally:
        type(encounter.shadow).observe = real_observe
        type(encounter).order = real_order
    return site, encounter, turns


@pytest.fixture(scope="module")
def _done():
    with pytest.MonkeyPatch.context() as patch:
        site, encounter, turns = _run(patch, experiment_id="p353-shared")
        yield site, encounter, turns, site.artifact()


def _identity(order_id, kind, written=None):
    return {"order_id": order_id, "type": kind, "fate": "", "source_submission": "",
            "action_written_at_min": written}


def _order(order_id, kind, *, submission, fate="EXECUTED", written=0, executed=0):
    return {"order_id": order_id, "submission_id": submission, "class": kind, "fate": fate,
            "reason": "", "executed_at_min": executed, "written_at_min": written}


# -- L1: an order opened and run in the same turn ----------------------------------------------------

def test_l1_same_turn_order_and_action_are_linked(_done):
    _site, _encounter, _turns, artifact = _done
    treated = [item for item in artifact["minutes"] if "fluid" in (item.get("action_kinds") or [])]
    assert treated, "the treatment bundle must be in the artifact"
    for item in treated:
        rows = [dict(row) for row in (item.get("action_lineage") or [])]
        assert rows, "the minute carries its lineage"
        for row in rows:
            assert row["link"] == ra.LINK_VALID, row
            assert row["origin"] == ra.ORIGIN_THIS_TURN, row
            assert str(row["order_id"]).startswith(f"{item['submission_id']}:"), row
            assert row["source_submission"] == item["submission_id"], row
            assert row["activation_submission"] == item["submission_id"], row


# -- L2: an order opened in an earlier turn, run later -----------------------------------------------

def test_l2_a_prior_turn_order_links_and_declares_its_origin():
    """``open_turn`` reuses a held order by its id, so the order keeps the submission that opened it.

    The two GI batteries never exercise it (P3-52: 0 of 170), so this is asserted on the linker itself,
    with the shape the repository would produce: the order's own ``submission_id`` is the earlier turn.
    """
    rows = ra.action_lineage([_identity("t0:2", "fluid", written=0)],
                             [_order("t0:2", "fluid", submission="t0", written=0, executed=30)],
                             "t3")
    assert len(rows) == 1
    row = rows[0]
    assert row["link"] == ra.LINK_VALID, row
    assert row["origin"] == ra.ORIGIN_EARLIER, row
    assert row["source_submission"] == "t0" and row["activation_submission"] == "t3"
    assert row["order_written_at_min"] == 0 and row["activated_at_min"] == 30


# -- L3: a bundle the pipeline split -----------------------------------------------------------------

def test_l3_a_split_bundle_links_every_action_it_ran():
    """P3-52 measured the real shape: 6 orders, 5 run actions, the sixth a plan the engine never ran."""
    import pilot_acceptance as acceptance
    with pytest.MonkeyPatch.context() as patch:
        _site, _encounter, turns = _run(
            patch, experiment_id="p353-l3",
            # The battery's own ``H_unexpected_reasonable``: a reasonable order the engine does not
            # model, written beside the correct bundle. P3-52 measured 6 orders and 5 run actions.
            script=[acceptance.UNMODELLED_ORDER + " {correct} Reassess in 15 minutes."])
    split = [turn for turn in turns if turn.get("orders")
             and len(turn["orders"]) > len(turn["ran"])]
    assert split, ("the correct course opens a plan order the engine never runs; "
                   f"turns: {[(t['submission'], len(t['ran']), len(t.get('orders') or [])) for t in turns]}")
    for turn in split:
        rows = ra.action_lineage(
            [_identity(a["order_id"], a["type"], a["written_at_min"]) for a in turn["ran"]],
            [{key: order.get(key) for key in ra.SETTLED_ORDER_FIELDS + ("written_at_min",)}
             for order in turn["orders"]], turn["submission"])
        assert len(rows) == len(turn["ran"]), "one row per CONSUMED action, never per order"
        assert all(row["link"] == ra.LINK_VALID for row in rows), rows
        unconsumed = {str(o["order_id"]) for o in turn["orders"]} - {str(r["order_id"]) for r in rows}
        assert unconsumed, "the order no action ran is simply not consumed; it is not a violation"


# -- L4: one order to several actions ----------------------------------------------------------------

def test_l4_the_runtime_maps_one_order_to_one_action(_done):
    """No ``group`` or expansion key is ever written at order level, and the measurement agrees.

    If the repository ever expanded one order into several action components, the linker would emit one
    row per component and every row would carry the same canonical order id; that is asserted on the
    linker, while the runtime's current one-to-one mapping is asserted on the real turns.
    """
    _site, _encounter, turns, _artifact = _done
    for turn in turns:
        ids = [str(a["order_id"]) for a in turn["ran"]]
        assert len(ids) == len(set(ids)), f"one action per order in {turn['submission']}: {ids}"
    expanded = ra.action_lineage([_identity("t0:0", "fluid", 0), _identity("t0:0", "fluid", 0)],
                                 [_order("t0:0", "fluid", submission="t0")], "t0")
    assert len(expanded) == 2 and {row["order_id"] for row in expanded} == {"t0:0"}
    assert all(row["link"] == ra.LINK_VALID for row in expanded)


# -- L5: the stored fate is the ledger's fate --------------------------------------------------------

def test_l5_the_stored_fate_is_the_one_the_ledger_settled(_done):
    _site, _encounter, turns, artifact = _done
    settled = {str(o["order_id"]): str(o.get("fate") or "")
               for turn in turns for o in (turn.get("orders") or [])}
    assert settled, "the encounter settled orders"
    seen = 0
    for item in artifact["minutes"]:
        for row in [dict(r) for r in (item.get("action_lineage") or [])]:
            assert str(row["fate"]) == settled[str(row["order_id"])], row
            seen += 1
    assert seen, "at least one linked action"


# -- L6: an order that did not act cannot be the source of a treatment -------------------------------

def test_l6_a_fate_that_did_not_act_cannot_be_an_executed_source(monkeypatch):
    rows = ra.action_lineage([_identity("t1:0", "fluid", 0)],
                             [_order("t1:0", "fluid", submission="t1", fate="SCHEDULED")], "t1")
    assert rows[0]["link"] == ra.LINEAGE_FATE_DID_NOT_ACT, rows
    assert ra.lineage_violations(rows), "a violation, not a note"

    def forge(orders):
        out = []
        for order in orders:
            item = dict(order)
            if str(item.get("class")) in ("fluid", "blood", "ppi"):
                item["fate"] = "SCHEDULED"
            out.append(item)
        return out

    site, _encounter, _turns = _run(monkeypatch, experiment_id="p353-l6", orders_hook=forge)
    artifact = site.artifact()
    assert artifact["halted"], "a treatment whose order did not act halts the experiment"
    assert ra.PROVENANCE_CONTRADICTION in str(artifact["halt_reason"])
    committed = [item for item in artifact["minutes"] if item.get("outcome") == ra.COMMITTED]
    assert committed, "the minutes committed before the contradiction are preserved as they happened"


# -- L7: an activation may not precede the order that authorized it ----------------------------------

def test_l7_activation_cannot_precede_the_source_order():
    rows = ra.action_lineage([_identity("t2:0", "fluid", 45)],
                             [_order("t2:0", "fluid", submission="t2", written=45, executed=30)], "t2")
    assert rows[0]["link"] == ra.LINEAGE_WRITTEN_AFTER_ACTIVATION, rows


# -- the collision P3-52 reproduced ------------------------------------------------------------------

def test_the_inherited_ledger_collision_is_named_and_not_excused():
    """``reload_resume``'s shape: ``t0:0`` resolves to the ORIGINAL encounter's fluid order."""
    rows = ra.action_lineage([_identity("t0:0", "reassessment", 15)],
                             [_order("t0:0", "fluid", submission="t0", written=0, executed=15)], "t0")
    assert rows[0]["link"] == ra.LINEAGE_CLASS_DISAGREES, rows
    # Same class, but the order was opened in a minute this action never wrote in.
    same = ra.action_lineage([_identity("t0:0", "fluid", 15)],
                             [_order("t0:0", "fluid", submission="t0", written=0, executed=15)], "t0")
    assert same[0]["link"] == ra.LINEAGE_NOT_THE_ORDER_THIS_ACTION_OPENED, same


def test_an_action_without_an_identity_is_a_violation():
    rows = ra.action_lineage([_identity("", "fluid", 0)], [_order("t0:0", "fluid", submission="t0")], "t0")
    assert rows[0]["link"] == ra.NO_CANONICAL_SOURCE_ORDER, rows
    absent = ra.action_lineage([_identity("t9:9", "fluid", 0)], [], "t9")
    assert absent[0]["link"] == ra.LINEAGE_ABSENT, absent


# -- L8: the replay verifies the lineage from the artifact alone -------------------------------------

def test_l8_the_replay_verifies_the_lineage_from_the_artifact(_done):
    _site, _encounter, _turns, artifact = _done
    out = ra.replay_site_artifact(artifact)
    assert out["lineage_valid_minutes"] == len(artifact["minutes"])
    assert out["lineage_links"] == [ra.LINK_VALID]
    for row in out["minutes"]:
        assert row["lineage_valid"] and not row["lineage_violations"], row["minute"]
    forged = json.loads(json.dumps(artifact, default=str))
    for item in forged["minutes"]:
        for row in item.get("action_lineage") or []:
            row["link"] = ra.LINEAGE_CLASS_DISAGREES
        for row in item.get("action_fates") or []:
            row["link"] = ra.LINEAGE_CLASS_DISAGREES
    replayed = ra.replay_site_artifact(forged)
    assert replayed["lineage_valid_minutes"] == 0
    assert all(not row["provenance_consistent"] for row in replayed["minutes"])


# -- L9: the physiology did not move -----------------------------------------------------------------

def test_l9_the_pressure_trajectory_is_the_one_measured_before_any_provenance_work(_done):
    _site, _encounter, _turns, artifact = _done
    committed = [item for item in artifact["minutes"] if item.get("outcome") == ra.COMMITTED]
    assert len(committed) == len(P341_TRAJECTORY)
    for item, expected in zip(committed, P341_TRAJECTORY):
        assert item["minute"] == expected["minute"], item
        assert dict(item["written_candidate"]) == expected["written"], item


# -- L11, L12, L13: nothing else moved ---------------------------------------------------------------

def test_l11_no_scoring_surface_is_reachable_from_the_lineage(_done):
    _site, _encounter, _turns, artifact = _done
    body = json.dumps(artifact, default=str).lower()
    for forbidden in ("rubric", "radar", "penalt", "competenc", "global_score", "dimension",
                      " assessment", "d1_", "d5_"):
        assert forbidden not in body, forbidden
    assert sorted(artifact) == sorted(ra.ARTIFACT_FIELDS)


def test_l12_the_pilot_is_still_refused(monkeypatch):
    import pilot_acceptance as acceptance
    for name, value in _environ().items():
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS:
        monkeypatch.setenv(name, "1")
    encounter = acceptance.Encounter(CASE)
    assert ra.open_site(encounter.state, environ=dict(os.environ), experiment_id="p353-pilot") is None


def test_l13_the_phase_two_digest_did_not_move():
    assert rs.PHASE2_DIGEST == "22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a"
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
