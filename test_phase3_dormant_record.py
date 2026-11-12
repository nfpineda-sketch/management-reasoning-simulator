"""P3-220: the record of the dormant-plumbing cycle (P3-210 to P3-220), rebuilt from the source and compared with the committed JSON.

TEST-SIDE. Everything in ``build_record`` that can be derived is derived (the reader inventory from the AST scan, the clock writers from the source, the
constants from the layer); what cannot be derived -- the findings of the independent review, the five readiness statuses, the verdict, the blockers -- is written
here ONCE, as data, so that a change of any of them is a visible diff of this file and of the record. Nothing here enables an authority.
"""
import json
from collections import Counter
from pathlib import Path

import observable_view as view
import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_shadow as rs
import test_gi_reader_guards as guards
import test_phase3_clock_routes as clock

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_DORMANT_PAIR_AUTHORITY.json"
SERIES_PATH = ROOT / "docs" / "revision" / "PHASE3_PAIR_DRY_SERIES.json"
BASE_HEAD = "50f387b"

#: The independent review of P3-219 (read-only; each finding was CONFIRMED with the reviewer's own probe before it was corrected).
REVIEW = (
    {"id": "F1", "severity": "HIGH", "where": "runtime_authority.settle_provenance", "finding": "a turn that did not advance the clock was never settled against the ledger",
     "consequence": "'Place an IV line. Also give <a class the mapping cannot represent>' kept the experiment going (the unmodelled order appears only in the settled ledger)",
     "correction": "settle_provenance judges the no-advance turn with the rule the dry evaluator uses (unsupported_in_settlement)", "tests": ["test_f1_*", "test_f7_*"]},
    {"id": "F2", "severity": "MEDIUM", "where": "runtime_authority._minute", "finding": "a capture that failed (before=None) let a multi-minute turn commit a pressure that ignored the treatment; "
     "a gap with no kind was dropped", "correction": "every failure not yet judged refuses the turn; a kind-less gap is 'untyped_gap', unsupported", "tests": ["test_f2_*"]},
    {"id": "F3", "severity": "MEDIUM", "where": "runtime_authority._minute and PairDryEvaluator._no_advance_turn",
     "finding": "a failure stamped at the turn's start, or recorded during a no-advance turn, was never judged",
     "correction": "a high-water mark over the shadow's failures (failures_judged) replaces the minute window, and the no-advance turn reads it", "tests": ["test_f3_*", "test_s8_*", "test_s9_*"]},
    {"id": "F4", "severity": "MEDIUM", "where": "trace_phase0.observation_snapshot", "finding": "an unrouted consequential reader of the live word that the audit had labelled a snapshot of routed readers",
     "consequence": "persists the word into every Management-Trace event; harmless today, false assurance the day the image readers are routed",
     "correction": "routed through observable_view and classified ROUTED (5 routed readers now)", "tests": ["test_f4_*", "test_phase3_dormant_guards.py"]},
    {"id": "F5", "severity": "LOW", "where": "PairAuthorityTransaction.validate", "finding": "a refused pair could be re-validated and committed",
     "correction": "ABORTED and COMMITTED are terminal", "tests": ["test_f5_*"], "declared_limit": "in-process code can still reach the private inner pressure transaction; the base AuthorityTransaction has the same property"},
    {"id": "F6", "severity": "LOW", "where": "observable_view / payload_problems", "finding": "a malformed overlay made the view raise; a float category was accepted as a rung",
     "correction": "exact-int check; overlay_of never raises", "tests": ["test_f6_*"]},
    {"id": "F7", "severity": "LOW", "where": "PairDryEvaluator.settle", "finding": "the dry settlement compared the raw class", "correction": "the shared normalised rule", "tests": ["test_f7_*"]},
    {"id": "F8", "severity": "LOW", "where": "runtime_authority_pair", "finding": "the evaluator did not compare its case with the session's; a stale artifact survived into the next encounter; "
     "the dry replay was quadratic", "correction": "case equality in case_eligible; the stale artifact is dropped when a new session is seen; ONE replay per turn", "tests": ["test_f8_*"]},
)

#: The five statuses of P3-220, kept apart on purpose.
READINESS = {
    "PRESSURE_TECHNICAL_READINESS": {
        "status": "READY_FOR_A_DEVELOPMENT_EXPERIMENT",
        "scope": "the scripted harness AND the real page, on BOTH routes by which the clock moves (order turn, clinical time outside an order turn); the IV line no longer halts; "
                 "every failure not yet judged refuses a turn; the settled ledger of a no-advance turn is judged",
        "limits": ["development only: the approval is the development approval of the pressure point, not a runtime approval",
                   "the real pressure site validates the END minute's candidate and replay plus every failure since the last judged turn; the per-minute candidate and replay "
                   "check of every minute of a multi-minute turn exists only in the pair's evaluator"]},
    "CONSCIOUSNESS_TECHNICAL_READINESS": {
        "status": "OVERLAY_ISOLATION_PROVEN_LIVE_FIELD_MAPPING_BLOCKED",
        "scope": "the common word lives only in an explicit overlay; all 32 executable readers are accounted for (5 routed and frozen to legacy, 13 read frozen traces the routed "
                 "snapshots keep legacy, 13 read the live field which no transaction writes -- among them the 3 engine readers and the 4 image/visual ones that are consequential --, "
                 "1 has no caller); no reader consumes the common word",
        "limits": ["mapping the common word into the live legacy field is refused by the writer while seven consequential readers remain unrouted: four image/visual ones and the three "
                   "ENGINE readers (order eligibility, discharge), which cannot be routed in this phase because family_engine.py is a source of the Phase-2 calibration freeze",
                   "a differential proof over engine, page, AI payload and faculty retention, not a proof of absence: the scan cannot see dynamic access (declared in the audit)"]},
    "CONSCIOUSNESS_FACULTY_READINESS": {
        "status": "NOT_READY",
        "scope": "FD-P3-NEW-01: the 15 consciousness divergence episodes remain MECHANISTICALLY_COHERENT_DIFFERENCE and the faculty table is unanswered; FD-P3-NEW-02 allows the "
                 "common physiology to represent UNRESPONSIVE with a pulse but does NOT authorize mapping it into the legacy live mental_status",
        "limits": ["no consciousness authority until the faculty reviews the table (FD-P3-187 C1 and C5 stay open)"]},
    "PAIR_TRANSACTION_READINESS": {
        "status": "TRANSACTION_AND_DRY_EVALUATION_READY_RUNTIME_SITE_NOT_BUILT",
        "scope": "one payload (sbp, dbp, MAP, category), all or nothing, gate re-evaluated at commit, bound to the exact ratified V1, validated at every minute of a turn "
                 "(VALIDATED_ATOMIC_INTERVAL), collapse boundary and 240-minute window, written only into a copy and only into the overlay",
        "limits": ["there is no pair AUTHORITY SITE: nothing composes the evaluator, the transaction, the artifact, the halt and the persistence for a pair at runtime",
                   "the pair's commit has been exercised on copies with a test-only approval; it has never run inside an encounter, and may not"]},
    "PAGE_RUNTIME_READINESS": {
        "status": "DRY_ONLY_PAGE_PROVEN_UNCHANGED",
        "scope": "with every flag off the page holds no pair state; with the shadow and the dry evaluation on the resident-visible page, the engine's state, the event stream, the "
                 "order ledger and the Management Trace are identical turn by turn on both GI cases; the ONE hook sees every clock advance",
        "limits": ["no pair authority on the page", "the dry evaluation costs one replay of the run per turn when its flag is on, and nothing when it is off"]},
}
VERDICT = "C"
VERDICTS = {"A": "TECHNICAL_INFRASTRUCTURE_READY_FOR_FACULTY_AUTHORITY_DECISION", "B": "PRESSURE_PATH_READY_CONSCIOUSNESS_STILL_TECHNICALLY_BLOCKED",
            "C": "PAIR_TRANSACTION_OR_RUNTIME_STILL_BLOCKED", "D": "AUTHORITY_ARCHITECTURE_NEEDS_REDESIGN"}
BLOCKERS = (
    {"id": "R1", "kind": "BUILD (no faculty decision needed to build it; one is needed to enable it)",
     "blocker": "the pair authority site: the orchestration that composes the dry evaluator's checks, PairAuthorityTransaction.commit, the artifact, the provenance, the halt and the store, "
                "with its page tests under a test-only approval"},
    {"id": "R2", "kind": "BUILD", "blocker": "the per-minute candidate and replay validation of the pressure-only site, if that site is to be used for a multi-minute turn without the pair"},
    {"id": "R3", "kind": "BUILD, only if the faculty ever asks for the legacy field to carry the common word",
     "blocker": "routing of the seven consequential live-field readers before any mapping into the live field: the four image/visual ones (image_broker.edit_prompt, "
                "image_consistency.photographic_targets, patient_appearance.contract_brief, visual_observations.visual_observations) and the three engine ones "
                "(family_engine._validate, _order, _discharge_alarm), which need the Phase-2 calibration-freeze amendment procedure because family_engine.py is one of its sources"},
    {"id": "F1", "kind": "FACULTY", "blocker": "the consciousness divergence table (nine representative episodes, FD-P3-187 C1) and the 'Unresponsive with a pulse' reading (C5)"},
    {"id": "F2", "kind": "FACULTY", "blocker": "the grant of any authority and the approval of a snapshot FOR authority: not requested in this cycle (FD-P3-NEW-07)"},
)


def _series_summary():
    if not SERIES_PATH.exists():
        return None
    series = json.loads(SERIES_PATH.read_text(encoding="utf-8"))
    return {"record_digest": series["record_digest"], "runs": len(series["runs"]), "authority_granted": series["authority_granted"], "granularity": series["granularity"]}


def build_record():
    mechanisms = Counter(row["mechanism"] for row in guards.READER_GUARDS.values())
    inventory = guards.inventory(str(ROOT))
    body = {
        "record_type": "PHASE3_DORMANT_PAIR_AUTHORITY", "version": "P3-210..P3-220", "base_head": BASE_HEAD,
        "authority": {"granted": False, "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY,
                      "approved_authority_snapshots": sorted(ra.APPROVED_SNAPSHOTS), "v1_status": pair.RATIFIED, "v1_in_the_authority_registry": pair.V1_ID in ra.APPROVED_SNAPSHOTS},
        "readers": {"inventory": {key: inventory[key] for key in ("modules_with_a_syntactic_use", "modules_text_only", "sites", "executable_readers", "unclassified")},
                    "by_mechanism": dict(sorted(mechanisms.items())), "routed": sorted(view.ROUTED_READERS), "unrouted_consequential": sorted(view.UNROUTED_CONSEQUENTIAL),
                    "common_view_readers": sorted(view.COMMON_VIEW_READERS),
                    "table": {reader: {"kind": row["kind"], "guard": row["guard"], "mechanism": row["mechanism"], "consequence": row["consequence"]}
                              for reader, row in sorted(guards.READER_GUARDS.items())}},
        "dispositions": {"vocabulary": list(ra.ACTION_DISPOSITIONS), "no_common_physiology_allowlist": sorted(ra.NO_COMMON_PHYSIOLOGY_ACTIONS),
                         "unsupported_classes_still_halt": ["intubation", "vasopressor", "disposition", "anything not declared"]},
        "clock": {"writers_of_sim_time": sorted(f"{name}::{function}" for name, function in clock._writers_of_the_clock()), "routes": list(ra.KNOWN_ROUTES),
                  "granularity": pair.GRANULARITY, "rejected": pair.PER_MINUTE_TRANSACTION, "time_limit_min": pair.TIME_LIMIT_MIN,
                  "no_advance_ok_classes": sorted(ra.NO_ADVANCE_OK)},
        "pair": {"payload_fields": list(pair.PAIR_FIELDS), "observable_writes": list(pair.OBSERVABLE_WRITES), "overlay_writes": list(pair.OVERLAY_WRITES),
                 "never_written": list(pair.NEVER_WRITTEN), "pair_checks": list(pair.PAIR_CHECKS), "dry_checks": list(pair.CHECKS)},
        "binding": {"snapshot": pair.V1_ID, "version": pair.V1_VERSION, "file_sha256": pair.V1_FILE_SHA256, "profile_digest": pair.V1_PROFILE_DIGEST,
                    "refusals": list(pair.REFUSALS)},
        "series": _series_summary(),
        "review": list(REVIEW), "readiness": READINESS, "verdict": VERDICT, "verdict_name": VERDICTS[VERDICT], "blockers": list(BLOCKERS),
        "confirmations": {"authority_enabled": False, "v1_promoted_to_authority": False, "common_state_written_into_an_encounter": False, "common_consciousness_exposed_to_residents": False,
                          "scoring_changed": False, "first_pilot_changed": False, "terminal_rule_invented": False, "legacy_curve_fitting": False, "physiology_retuned": False,
                          "clinical_validation_claimed": False, "clinical_core_bytes_changed": False},
    }
    return {**body, "record_digest": ra.digest_of(body)}


def write_record():
    record = build_record()
    RECORD_PATH.write_text(json.dumps(record, indent=1, sort_keys=True), encoding="utf-8")
    return record


def test_the_dormant_record_is_what_the_source_says_today():
    assert RECORD_PATH.exists(), "write it once with write_record()"
    stored = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    live = build_record()
    assert stored["record_digest"] == live["record_digest"], "the committed record no longer matches the source: regenerate it deliberately"
    assert stored["authority"] == {"granted": False, "common_core_runtime_authority": False, "approved_authority_snapshots": ["gi_pressure_committed"],
                                   "v1_status": "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS", "v1_in_the_authority_registry": False}


def test_the_record_keeps_its_five_statuses_apart_and_returns_one_verdict():
    live = build_record()
    assert list(live["readiness"]) == ["PRESSURE_TECHNICAL_READINESS", "CONSCIOUSNESS_TECHNICAL_READINESS", "CONSCIOUSNESS_FACULTY_READINESS", "PAIR_TRANSACTION_READINESS",
                                      "PAGE_RUNTIME_READINESS"]
    assert live["verdict"] == "C" and live["verdict_name"] == "PAIR_TRANSACTION_OR_RUNTIME_STILL_BLOCKED"
    assert all(value is False for value in live["confirmations"].values())
    assert {item["id"] for item in live["review"]} == {f"F{n}" for n in range(1, 9)}
    assert live["readers"]["by_mechanism"][guards.ROUTED] == len(view.ROUTED_READERS) == 5 and live["readers"]["common_view_readers"] == []
