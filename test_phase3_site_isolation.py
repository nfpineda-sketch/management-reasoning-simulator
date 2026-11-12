"""P3-234: the executable-reader audit re-run with the dormant SITE in the tree, and the proof that the dormant evaluation changes no consumer of the live word.

TEST-SIDE. FD-AUTH-12 and FD-AUTH-13: the legacy ``mental_status`` stays the resident-authoritative live field; the common word lives only in an isolated candidate
payload (and, in a future commit, an overlay the readers ignore); the three engine readers frozen by the Phase-2 closure and the other consequential readers of the live
field are NOT routed and stay named blockers for any later direct authority over the word.

* the audit is the live AST scan, not a record: the numbers below are reproduced from the source;
* the new layer modules (the shared validator and the site) are mechanisms, not readers: they name no field of the live word and no function of theirs reads it;
* the dormant evaluation never writes the state the readers read: byte-identical before and after (a deterministic reader of an identical state returns an
  identical answer, which is why scoring, branching, the AI payloads, the faculty's retention of a suggestion, action availability, the discharge, the termination and
  the resident's text cannot change; the real page is compared in ``test_phase3_site_page.py``).
"""
import ast
from collections import Counter
from copy import deepcopy
from pathlib import Path

import observable_view as view
import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_pair_site as site_module
import test_gi_preauthority_review as review
import test_gi_reader_guards as guards
from test_phase3_clock_routes import bound  # noqa: F401 (fixture)
from test_phase3_pair_site import _feed, infusion  # noqa: F401 (fixture)

ROOT = Path(__file__).resolve().parent
NEW_LAYER_MODULES = ("runtime_minute_validation.py", "runtime_pair_site.py")


def test_k1_the_executable_reader_audit_is_reproduced_from_the_source_with_the_dormant_site_in_the_tree():
    audit = review.reader_audit(str(ROOT))
    rows = [row for row in audit["rows"] if row["module"] not in review.MECHANISM_MODULES]
    live = sorted(f"{row['module']}::{row['function']}" for row in rows if row["where"] in review.LIVE and row["executable_read"])
    assert audit["unclassified"] == [] and len(live) == 32 and live == guards.live_reader_ids(str(ROOT)) == sorted(guards.READER_GUARDS)
    by_mechanism = Counter(row["mechanism"] for row in guards.READER_GUARDS.values())
    assert by_mechanism[guards.ROUTED] == 5 and by_mechanism[guards.LIVE_FIELD] == 13, by_mechanism
    assert sum(by_mechanism.values()) == 32 and len(view.ROUTED_READERS) == 5
    # nothing new reads the word: neither new module is among the 119 sites
    assert not [row for row in audit["rows"] if row["module"] in NEW_LAYER_MODULES]
    for module in NEW_LAYER_MODULES:
        tree = ast.parse((ROOT / module).read_text(encoding="utf-8"))
        assert not [node for node in ast.walk(tree) if isinstance(node, ast.Constant) and node.value == "mental_status"], module


def test_k2_the_seven_consequential_readers_and_the_three_frozen_engine_readers_are_still_named_blockers_and_nothing_routes_them():
    assert len(view.UNROUTED_CONSEQUENTIAL) == 7 and len(view.FROZEN_BY_THE_PHASE2_CLOSURE) == 3
    assert view.FROZEN_BY_THE_PHASE2_CLOSURE <= set(view.UNROUTED_CONSEQUENTIAL) and not set(view.UNROUTED_CONSEQUENTIAL) & set(view.ROUTED_READERS)
    assert dict(view.COMMON_VIEW_READERS) == {} or not view.COMMON_VIEW_READERS            # no reader reads the common word in this cycle
    for reader in view.UNROUTED_CONSEQUENTIAL:
        row = guards.READER_GUARDS.get(reader)
        assert row is None or (row["mechanism"] == guards.LIVE_FIELD and row["guard"] == view.LATER), reader
    assert "observable_view" not in (ROOT / "family_engine.py").read_text(encoding="utf-8")      # the engine is untouched, as the closure requires


def test_k3_the_dormant_evaluation_leaves_the_state_the_readers_read_byte_identical_and_writes_no_overlay(infusion):
    state = deepcopy(infusion["after"])
    before = ra.digest_of(state)
    record = infusion["site"].minute(infusion["before"], state, infusion["session"], infusion["ran"], "inf-1", ra.ORDER_TURN)
    assert record["verdict"] == pair.WOULD_COMMIT and ra.digest_of(state) == before and view.OVERLAY_KEY not in state
    assert state["observable"]["mental_status"] == infusion["after"]["observable"]["mental_status"]
    # every routed reader, asked of the state after the dormant evaluation, answers the live word
    for reader in view.ROUTED_READERS:
        assert view.mental_status_for(state, reader) == state["observable"]["mental_status"]
    # the candidate word exists ONLY inside the candidate payload of the record and the artifact, never in a field a reader reads
    candidate = record["would_write"]["mental_status"]
    assert candidate in view.WORDS
    for key, value in state["observable"].items():
        assert value != candidate or key == "mental_status", key


def test_k4_the_candidate_word_may_differ_from_the_live_word_and_the_artifact_says_so_without_changing_the_live_one(infusion):
    """FD-AUTH-12: a common ``Unresponsive`` WITH a pulse is a valid candidate while the legacy word stays what the engine says."""
    _feed(infusion)
    turn = infusion["site"].artifact()["turns"][-1]
    assert turn["legacy"]["mental_status"] == infusion["after"]["observable"]["mental_status"]
    assert turn["common"]["mental_status"] in view.WORDS and turn["would_write"]["mental_status"] == turn["common"]["mental_status"]
    assert infusion["encounter"].state["observable"]["mental_status"] == turn["legacy"]["mental_status"]


def test_k5_scoring_and_the_resident_facing_modules_never_name_the_site_the_word_or_the_artifact():
    for name in ("app.py", "pilot_acceptance.py", "order_pipeline.py", "management_trace_store.py", "rubric_store.py", "progress_store.py"):
        path = ROOT / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for token in ("runtime_pair_site", "DormantPairSite", "DORMANT_AUTHORITY_EVALUATION", "phase3_pair_authority_dormant", "pair_dormant", "request_commit"):
            assert token not in text, (name, token)
    assert site_module.ARTIFACT_TYPE not in (ROOT / "runtime_authority_store.py").read_text(encoding="utf-8")
