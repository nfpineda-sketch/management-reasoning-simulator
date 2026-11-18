"""P3-386: the sealed checkpoint of the promotion of the ratified GI pressure snapshot to live development authority, and the proof that the documents, the debt, CLAUDE.md and the code say the same thing.

TEST-SIDE. The record is a STATIC, sealed JSON written once (``MRS_WRITE_PROMOTION_CHECKPOINT=1 python3 -m pytest test_phase3_pressure_promotion_checkpoint.py -k write``) and committed. These tests check that it
is sealed, that every fact in it that the code can also answer (the snapshot, the grant, the six coordinates before and after, the recorded equality with the human-reviewed ``CENTER_REFERENCE`` trajectories)
still equals what the code and the ratified records say, and that the documents agree. On purpose it does NOT embed the list of registered approvals or the digest of any earlier checkpoint: that is what chained
the older code-derived records to each other (see ``test_phase3_promotion_record_delta.py``), and this record must not become another link of that chain.
"""
import json
import os
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_pressure_grant as grants
import runtime_pressure_snapshot as ps
import runtime_shadow as rs
import runtime_shadow_families as rsf

ROOT = Path(__file__).resolve().parent
RECORD_PATH = ROOT / "docs" / "revision" / "PHASE3_GI_PRESSURE_PROMOTION_CHECKPOINT.json"
REGION = json.loads((ROOT / ps.REGION_FILE).read_text(encoding="utf-8"))
V1, V2 = "gi_pressure_committed", ps.SNAPSHOT_ID

#: The six coordinates, the previous live value (what the authority ran until this cycle) and the ratified one. The previous values are RE-DERIVED from the code below (the older adapter), not trusted.
PREVIOUS = {"bleed_rate_ml_eq_per_min": 2.5, "preload_scale_ml_eq": 833.3333333333334, "arrival_position": 0.5, "kernel_e": 0.125, "kernel_s": 0.6, "kernel_tau_min": 30.0}

#: What the page run recorded (``test_phase3_pressure_promotion.py::test_e1``): the SBP/DBP/MAP the page DISPLAYED at every committed minute of the four reviewed encounters.
EQUALITY = {
    "FR-B": {"case": "gi_bleed_57m", "rows": {5: [89, 54, 66], 10: [91, 56, 68], 30: [92, 57, 69]}},
    "FR-C": {"case": "gi_bleed_57m", "rows": {60: [71, 43, 52], 120: [54, 33, 40], 125: [56, 34, 41], 130: [59, 36, 44], 150: [64, 39, 47]}},
    "FR-E": {"case": "gi_bleed_72f", "rows": {60: [79, 50, 60], 120: [60, 38, 45], 125: [62, 39, 47], 130: [66, 42, 50], 160: [72, 46, 55]}},
    "FR-G": {"case": "gi_bleed_72f", "rows": {60: [85, 54, 64], 70: [81, 51, 61]}},
}

#: The adversarial review of the cycle (one, independent, read-only). Filled in when the review is done.
REVIEW = {
    "performed": "one independent, read-only, adversarial review of the uncommitted tree, against the attack list of the assignment",
    "high": 0, "medium": 3, "low": 5, "info": 1, "hard_invariants_broken": [],
    "every_finding_confirmed_by_an_own_probe_or_reading_before_acting": True,
    "findings_and_resolutions": [
        "MEDIUM 1 artifact verification bound the labels of the snapshot to the grant, not the values of the run: reproduced (a consistent relabel verified); repaired (every captured scenario must carry the six values of the snapshot its grant binds; the overlay replay is decided by the grant)",
        "MEDIUM 2 stale tests, one a collection error that my sweep did not cover: reproduced; four files adapted under the same rule (an exact set, nothing else)",
        "MEDIUM 3 the only session/site mix guard was incidental: confirmed; an explicit named PRESSURE_CONFIGURATION_MISMATCH check before the candidate is taken",
        "LOW 4 provenance inside the run named the committed default profile: reproduced; repaired",
        "LOW 5 the review environment requiring version 2 had no test (and the document named the wrong condition): confirmed; test added, document corrected",
        "LOW 6 the digests the grant pins were never compared at run time with the binding: confirmed; compared in the gate and in open_site (not in the grant module, which imports nothing of the repository on purpose)",
        "LOW 7 a bind failure was undiagnosable in the authority record: the reason now names it",
        "LOW 8 weakened or missing tests (b4 became membership; s11 not mirrored): b4 exact again; s11 mirrored",
        "INFO 9 duplicated literals, dry evaluator, CRLF checkouts, shadow session without the authority flag: equality test added; the rest declared"],
    "mutants_of_the_findings_killed": 8,
    "not_reproduced": ["the exact count of surviving mutants the reviewer reported (what was done: the eight mutants that matter are killed by new tests)"],
    "declared_not_changed": ["the dry evaluator still binds the older point", "no .gitattributes pins LF for the hash-pinned JSON (a CRLF checkout fails closed)", "unsigned artifacts: a determined forger of consistent values, minutes and digests is not refutable"]}


#: 2026-11-17 (declared adaptation, P3-388): the promotion's successor decision was taken on PHASE2_AMENDMENT_2, the active member that day. The checkpoint is a historical record and
#: is not regenerated: it keeps naming THAT member, which the lineage still registers and rebuilds, whatever member is active now.
PROMOTED_ON = next(member for member in rs.CORE_LINEAGE if member.version_id == "PHASE2_AMENDMENT_2")


def _digest(body):
    return ra.digest_of(body)


def build_record():
    cfg = ps.bind()
    older, promoted = rsf.GiHaemorrhageAdapter(), rsf.GiHaemorrhageAdapter.configured(cfg)
    coordinates = []
    for name, home in ps.EXECUTABLE_HOME.items():
        coordinates.append({"coordinate": name, "ratified": cfg.values()[name], "previous_live": PREVIOUS[name], "differs": cfg.values()[name] != PREVIOUS[name], "executable_home": home})
    body = {
        "record_type": "PHASE3_GI_PRESSURE_PROMOTION_CHECKPOINT", "version": "P3-375..386", "decided_on": "2026-11-16",
        "overall": {"verdict": "A", "name": "GI_PRESSURE_RATIFIED_SNAPSHOT_PROMOTED_TO_LIVE_DEVELOPMENT_AUTHORITY"},
        "statement": ("The live GI pressure DEVELOPMENT authority (sbp, dbp, derived map; gi_bleed_57m and gi_bleed_72f; development only; explicit grant) executes exactly GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1, "
                      "the CENTER_REFERENCE point ratified on 2026-11-16, instead of the older gi_pressure_committed. It is configuration only: no new physiology, no recalibration, no other point. It is not a clinical "
                      "validation, not production authority and not a resident deployment."),
        "successor_decision": {"verdict": "A", "name": "CONFIG_ONLY_PROMOTION_SUFFICIENT",
                               "why": "the six coordinates live in fields of objects the Phase 3 layer builds (profile, haemorrhage writer, crystalloid contributors); none is a constant of clinical_core/",
                               "predecessor": {"version_id": PROMOTED_ON.version_id, "digest": PROMOTED_ON.digest}, "successor": None, "clinical_core_changed": False},
        "snapshot": {"id": V2, "runtime_snapshot_id": ps.RUNTIME_SNAPSHOT_ID, "status": ps.STATUS, "values": cfg.values(), "c_rate_over_scale_per_min": cfg.c_rate_over_scale_per_min,
                     "configuration_digest": cfg.configuration_digest, "values_digest": cfg.values_digest, "record_digest": cfg.record_digest, "ratification_digest": cfg.ratification_digest,
                     "region_record_digest": cfg.region_record_digest, "human_record_digest": cfg.human_record_digest},
        "coordinates": coordinates, "coordinates_that_differ": sum(1 for item in coordinates if item["differs"]),
        "grant": {"id": grants.GRANT_ID_V2, "version": grants.GRANT_VERSION_V2, "fingerprint": grants.GRANT_FINGERPRINT_V2, "pressure_value_digest": grants.PRESSURE_VALUE_DIGEST_V2,
                  "configuration_digest": grants.CONFIGURATION_DIGEST_V2, "cases": list(grants.CASES), "domain": list(grants.GRANT_V2["domain"]), "environments": list(grants.GRANT_V2["environments"]),
                  "version_1": {"id": grants.GRANT_ID, "fingerprint": grants.GRANT_FINGERPRINT, "untouched": True, "still_registered": True},
                  "the_review_environment_requires": "version 2, in new sessions"},
        "binding": {"module": "runtime_pressure_snapshot.py", "in_the_layer_digest": True, "named_but_unbindable": "no corridor is opened and there is no fallback to the older point",
                    "refusals": list(ps.REFUSALS)},
        "replay": {"new_runs_identify": grants.GRANT_ID_V2, "older_artifacts_replay_under": grants.GRANT_ID, "nothing_rewritten": True,
                   "verification_hardening": "every snapshot identity an artifact declares must be the one its named grant binds"},
        "equality_with_center_reference": {"criterion": "the displayed pressures (whole mmHg, derived MAP) at every committed minute equal the human-reviewed CENTER_REFERENCE trajectory; the older authority is not the reference",
                                           "scenarios": {name: {"case": item["case"], "minutes": sorted(item["rows"]), "displayed_sbp_dbp_map": {str(minute): row for minute, row in sorted(item["rows"].items())}}
                                                         for name, item in EQUALITY.items()},
                                           "minutes_compared": sum(len(item["rows"]) for item in EQUALITY.values()), "all_equal": True},
        "nonregression": {"untreated_FR_A_FR_D": "still halts at the collapse boundary with the same committed minutes (60, 120, 180); the collapse is established earlier (183 under the promoted point, 207 under the older one)",
                          "FR_F_unsupported_norepinephrine": "still a correct stop; nothing implemented",
                          "effective_stop_reopen_abort_leaks": "the stop-page proofs are replayed under the promoted configuration",
                          "review_environment_single_process_isolation": "unchanged and proved with the promoted configuration"},
        "limitations": ["GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE stays a monitored limitation; the promotion did not touch it",
                        "FR-A and FR-D under the ratified configuration were machine-checked, not reviewed by a person (the blinded re-review covered FR-B, FR-C, FR-E and FR-G)",
                        "version 1 and the older point stay registered and runnable; retiring them from live activation is a pending faculty decision",
                        "the human re-review record is REPORTED_NOT_VERIFIED_AGAINST_PERSISTED_STORE (TD-152)",
                        "development only; one reviewer, four scenarios, two cases; not a clinical validation"],
        "pending_faculty_decisions": ["retire the older point and grant version 1 from live activation, or keep them runnable for replay", "decide a versioning scheme for the code-derived historical records before the declared delta accumulates"],
        "next_physiology_priority": "common vascular-tone / vasopressor pathway (FD-REVIEW-06); not implemented",
        "reported": {"adversarial_review": REVIEW},
        "confirmations": {"clinical_core_untouched": True, "common_core_runtime_authority_false": True, "no_new_calibration": True, "no_amendment_3_physiology": True, "no_norepinephrine": True,
                          "no_source_control": True, "no_consciousness_authority": True, "no_terminal_authority": True, "no_resident_deployment": True, "no_clinical_validation_claim": True,
                          "low_and_high_not_promoted": True, "monitored_limitation_not_fixed": True, "scoring_and_first_pilot_unchanged": True, "no_historical_record_rewritten": True},
    }
    return {**body, "record_digest": _digest(body)}


def _stored():
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


def test_write_the_record_only_when_asked():
    if os.environ.get("MRS_WRITE_PROMOTION_CHECKPOINT") == "1":
        RECORD_PATH.write_text(json.dumps(build_record(), indent=1, sort_keys=True), encoding="utf-8")
    assert RECORD_PATH.exists(), "the record is produced once and committed"


def test_c1_the_checkpoint_is_sealed_and_every_fact_the_code_can_answer_is_what_the_code_says():
    stored = _stored()
    assert stored["record_digest"] == _digest({key: value for key, value in stored.items() if key != "record_digest"}), "sealed"
    live = json.loads(json.dumps(build_record()))
    assert stored == live, "the committed checkpoint no longer matches the code and the ratified records: regenerate it deliberately"


def test_c2_the_recorded_equality_is_the_human_reviewed_center_reference_and_the_previous_values_are_the_older_adapters():
    for name, item in EQUALITY.items():
        reference = {int(point["minute"]): [int(point["sbp"]), int(point["dbp"]), int(point["map"])]
                     for point in REGION["candidate_trajectories"][name]["candidates"]["CENTER_REFERENCE"]["pressures"]}
        assert {minute: reference[minute] for minute in item["rows"]} == item["rows"], name
    older = rsf.GiHaemorrhageAdapter()
    profile = older.profile(rsf.COMMITTED)
    assert (profile.preload_curve_scale_ml, profile.arrival_preload_fraction) == (PREVIOUS["preload_scale_ml_eq"], PREVIOUS["arrival_position"])
    from clinical_core.modules.gi_haemorrhage import GIHaemorrhage
    assert [w.blood_loss_ml_per_min for w in older.writers("gi_bleed_57m", rsf.COMMITTED, None) if isinstance(w, GIHaemorrhage)] == [PREVIOUS["bleed_rate_ml_eq_per_min"]]


def test_c3_the_record_says_what_it_must_and_claims_nothing_it_may_not():
    record = _stored()
    assert record["overall"] == {"verdict": "A", "name": "GI_PRESSURE_RATIFIED_SNAPSHOT_PROMOTED_TO_LIVE_DEVELOPMENT_AUTHORITY"}
    assert record["successor_decision"]["verdict"] == "A" and record["successor_decision"]["successor"] is None and record["successor_decision"]["clinical_core_changed"] is False
    assert record["coordinates_that_differ"] == 5 and len(record["coordinates"]) == 6
    assert record["equality_with_center_reference"]["minutes_compared"] == 15 and record["equality_with_center_reference"]["all_equal"] is True
    assert record["grant"]["version_1"]["untouched"] is True and record["grant"]["fingerprint"] == grants.GRANT_FINGERPRINT_V2
    assert all(record["confirmations"].values()), "every confirmation is true"
    text = json.dumps(record).lower()
    for forbidden in ("clinically validated", "validated clinically", "production authority granted", "approved for residents"):
        assert forbidden not in text, forbidden
    assert "GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE" in json.dumps(record["limitations"])


def test_c4_the_decisions_the_debt_the_document_and_claude_md_say_the_same_thing():
    cola = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    for index in range(1, 8):
        assert f"| FD-PROMOTE-0{index} |" in cola
    for index in range(252, 257):
        assert f"| FD-P3-{index} |" in cola
    for text in ("GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1", "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2", "CONFIG_ONLY_PROMOTION_SUFFICIENT", "A · `CONFIG_ONLY_PROMOTION_SUFFICIENT`"):
        assert text in cola, text
    debt = (ROOT / "docs" / "REGISTRO_DEUDA_TECNICA.md").read_text(encoding="utf-8")
    assert "## TD-153" in debt and "retirar la V1 de la activación" in debt and "FR-A y FR-D con la configuración ratificada no pasaron por la re-revisión humana" in debt
    assert "`TD-153`" in debt.split("## TD-152")[1].split("## TD-153")[0], "TD-152 carries the dated note that points to TD-153"
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    for text in ("docs/PHASE3_GI_PRESSURE_PROMOTION.md", "FD-PROMOTE-01 a FD-PROMOTE-07", "FD-P3-252 a FD-P3-256", "`TD-153`", "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2", "runtime_pressure_snapshot.py"):
        assert text in claude, text
    doc = (ROOT / "docs" / "PHASE3_GI_PRESSURE_PROMOTION.md").read_text(encoding="utf-8")
    for text in ("8,970853509", "2697,136369656", "0,003326066", "0,213115961", "60,624", "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2", "8a91145dbfe899dffdc5de1ed28b116c61f4fa5b462a49979727ce8b05b3642f",
                 "70e6826cb2844bace6e3249058638340d00d80f84f8fdd2a5a2e752028db0641", "CONFIG_ONLY_PROMOTION_SUFFICIENT", "GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE", "FR-A", "FR-D"):
        assert text in doc, text
    for name, text in (("docs/PHASE3_GI_JOINT_REGION_RATIFICATION.md", "Nota fechada (2026-11-16, ciclo de promoción"), ("docs/PHASE3_FACULTY_REVIEW_ENVIRONMENT.md", "Actualización (2026-11-16, ciclo de promoción"),
                       ("docs/PHASE3_FACULTY_REREVIEW_INTERACTIVE.md", "Actualización (2026-11-16, ciclo de promoción")):
        assert text in (ROOT / name).read_text(encoding="utf-8"), name
    operator = (ROOT / "faculty_review_kit" / "02_preparacion_operador.md").read_text(encoding="utf-8")
    assert f"MRS_PHASE3_AUTHORITY_SNAPSHOT={V2}" in operator and "MRS_PHASE3_AUTHORITY_SNAPSHOT=gi_pressure_committed\n" not in operator
