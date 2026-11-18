"""P3-401: the checkpoint of the common vascular tone pathway, and what it stands on.

``docs/revision/PHASE3_COMMON_TONE_CHECKPOINT.json`` is a VERSIONED record (P3-388). It is written ONCE, deliberately (``write``), from two things:

- what the code and the committed records say NOW (recomputed here, never typed): the lineage, the grants, the mapping, the candidate and the probes;
- ``EVIDENCE``: what cannot be recomputed from the tree -- the independent adversarial review and the certification run on the candidate -- typed below
  by whoever certifies, with the figures of that run.

The tests check the committed record against the live code wherever the live code can answer, and check that the verdict is one the facts allow. They
do not regenerate the record: the typed evidence is part of it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import historical_records as hr
import test_tone_pathway_analysis as ta

ROOT = Path(__file__).resolve().parent
PATH = ROOT / "docs" / "revision" / "PHASE3_COMMON_TONE_CHECKPOINT.json"
VERSION = "COMMON_TONE_CHECKPOINT_V1"
GENERATED_ON = "2026-11-17"
VERDICTS = {
    "A": "COMMON_VASCULAR_TONE_PATHWAY_READY_FOR_HUMAN_DEVELOPMENT_REVIEW",
    "B": "TONE_ARCHITECTURE_DEFINED_BUT_IMPLEMENTATION_REQUIRES_FACULTY_DECISION",
    "C": "NOREPINEPHRINE_WRITER_BLOCKED_BY_ORDER_SEMANTICS",
    "D": "COMMON_TONE_REQUIRES_BROADER_CORE_REDESIGN",
    "E": "MULTIFAMILY_PROBES_REVEALED_NONGENERAL_BEHAVIOR",
}
SEQUENCE = (
    ("P3-387", "V1/V2 activation audit", "a superseded grant opens no new session by ordinary configuration; only a declared historical reconstruction names it"),
    ("P3-388", "historical record versioning", "contract, index and the first VERSIONED records"),
    ("P3-389", "existing tone audit", "B: PARTIAL_TONE_PHYSIOLOGY_EXISTS_BUT_NEEDS_SUCCESSOR"),
    ("P3-390", "minimum state", "aux.vasoconstrictor_support, a general state; None while its reader is UNSET"),
    ("P3-391", "coupling", "tone target = C(s) x B(b) x K(u); pressure and afterload read T as before"),
    ("P3-392", "norepinephrine writer", "a fixed-rate infusion with first-order onset and offset; reads its order and time only"),
    ("P3-393", "edge-case matrix", "ten cases, predicted before the run"),
    ("P3-394", "development region", "broad bounds, every confidence below 0.80, three witnesses, none chosen"),
    ("P3-395", "successor decision", "C: PHASE2 AMENDMENT 3 -- COMMON VASCULAR TONE"),
    ("P3-396", "implementation", "the amendment (off by default) and the development mapping in the shadow"),
    ("P3-397", "FR-F development migration", "a versioned candidate with no verdict"),
    ("P3-398", "multifamily probes", "one mapping in the six registered families"),
    ("P3-399", "adversarial review", "one independent read-only review"),
    ("P3-400", "certification", "full suite and regressions on a frozen fingerprint"),
    ("P3-401", "checkpoint", "this record"),
)

#: Typed by whoever certifies (see the module docstring). ``None`` until the candidate has been reviewed and certified: the record cannot be written before.
EVIDENCE: dict | None = None


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def facts() -> dict:
    """What the tree says now, recomputed."""
    import runtime_authority as ra
    import runtime_pressure_grant as grants
    import runtime_pressure_snapshot as ps
    import runtime_shadow as rs
    import runtime_shadow_families as fam
    import runtime_tone_support as ts
    from clinical_core import amendment_3 as a3
    from clinical_core import derived as dv
    candidate, probes = ta.load(ta.CANDIDATE_PATH), ta.load(ta.PROBES_PATH)
    checks = ("order_accepted", "tone_changes", "response_begins_causally", "reassessment_possible", "no_volume_and_no_pump_created",
              "bounded_by_its_own_form", "replays_exactly")
    return {
        "core": {"amendment": a3.REVISION, "digest": a3.amended_core_digest_now(), "sources": len(a3.live_core_sources()),
                 "registered_as_the_last_lineage_member": (rs.CORE_LINEAGE[-1].version_id, rs.CORE_LINEAGE[-1].digest) == (a3.REVISION, a3.amended_core_digest_now()),
                 "off_by_default": dv.DEFAULT_PROFILE.vasoconstrictor_support_to_tone_gain is None,
                 "predecessors_rebuilt_from_the_live_tree": {"PHASE2_AMENDMENT_2": a3.amendment_2_verifies(), "PHASE2_AMENDMENT_1": a3.amendment_1_verifies(),
                                                             "PHASE2_CLOSURE": a3.historical_closure_verifies()},
                 "predecessor_digests": {"PHASE2_AMENDMENT_2": rs.CORE_LINEAGE[2].digest, "PHASE2_AMENDMENT_1": rs.CORE_LINEAGE[1].digest, "PHASE2_CLOSURE": rs.PHASE2_DIGEST}},
        "grants": {"live": grants.LIVE_GRANT_ID, "live_fingerprint": grants.GRANT_FINGERPRINT_V3,
                   "superseded": {name: dict(entry)["by"] for name, entry in grants.SUPERSEDED.items()},
                   "older_fingerprints_unchanged": {grants.GRANT_ID: grants.GRANT_FINGERPRINT, grants.GRANT_ID_V2: grants.GRANT_FINGERPRINT_V2},
                   "live_grant_is_a_lineage_rebind_only": dict(grants.GRANT_V3["lineage_rebind"])["kind"] == "LINEAGE_REBIND_ONLY",
                   "norepinephrine_not_granted": "norepinephrine" in grants.GRANT_V3["not_granted"]},
        "authority": {"common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY, "norepinephrine_is_a_supported_authority_action": ts.ORDER_KIND in ra.SUPPORTED_ACTIONS,
                      "authority_domain": list(ra.AUTHORITY_DOMAIN), "authority_cases": list(ra.AUTHORITY_CASES),
                      "registered_adapters_declaring_the_reader": sorted(name for name, adapter in fam.ADAPTERS.items() if adapter.tone_support_witness is not None)},
        "gi_pressure_snapshot": {"id": ps.SNAPSHOT_ID, "record_file_sha256": _sha(ROOT / ps.RECORD_FILE), "configuration_digest": ps.CONFIGURATION_DIGEST,
                                 "record_is_byte_for_byte_the_one_pinned_before_this_cycle": _sha(ROOT / ps.RECORD_FILE)
                                 == hr.load_index()["records"][Path(ps.RECORD_FILE).name]["file_sha256"],
                                 "gi_mapping_still_maps": list(fam.ADAPTERS["gi_bleed"].maps),
                                 "configuration_is_the_one_both_grants_pin": ps.CONFIGURATION_DIGEST == grants.CONFIGURATION_DIGEST_V2
                                 == dict(grants.GRANT_V3["pressure_snapshot"])["configuration_digest"] == dict(grants.GRANT_V2["pressure_snapshot"])["configuration_digest"]},
        "mapping": ts.summary(),
        "candidate": {"record": str(ta.CANDIDATE_PATH.relative_to(ROOT)), "record_digest": candidate["record_digest"], "version": candidate["version"],
                      "faculty_verdict": candidate["faculty_verdict"], "chosen_witness": candidate["chosen_witness"],
                      "every_check_true_in_every_witness": all(entry["checks"][name] is True for entry in candidate["witnesses"].values() for name in checks)},
        "probes": {"record": str(ta.PROBES_PATH.relative_to(ROOT)), "record_digest": probes["record_digest"], "version": probes["version"],
                   "matrix_cases": len(probes["edge_case_matrix"]), "matrix_as_predicted": sum(1 for row in probes["edge_case_matrix"] if row["as_predicted"]),
                   "across_families": {key: value for key, value in probes["across_families"].items() if isinstance(value, bool)},
                   "families": probes["across_families"]["registered_families"]},
    }


def verdict_allowed(found: dict, evidence: dict) -> str:
    """The one verdict the facts and the evidence allow. A needs everything; the others name what failed."""
    probes, candidate = found["probes"], found["candidate"]
    general = probes["matrix_as_predicted"] == probes["matrix_cases"] and all(probes["across_families"].values())
    if not general:
        return "E"
    if not candidate["every_check_true_in_every_witness"]:
        return "C"
    review = evidence["adversarial_review"]
    certified = evidence["certification"]
    green = certified["failures"] == 0 and certified["errors"] == 0 and certified["tests"] > 0 and certified["regressions_failed"] == 0 and certified["regressions_passed"] > 0
    if review["unresolved_blocking_findings"] or not green or not found["core"]["off_by_default"]:
        return "B"
    return "A"


def build(evidence: dict | None = None) -> dict:
    evidence = EVIDENCE if evidence is None else evidence
    if evidence is None:
        raise RuntimeError("the checkpoint is written after the adversarial review and the certification of the candidate: EVIDENCE is not filled in")
    import runtime_pressure_grant as grants
    found = facts()
    letter = verdict_allowed(found, evidence)
    not_granted = tuple(grants.GRANT_V3["not_granted"])
    body = {
        "record_type": "COMMON_VASCULAR_TONE_CHECKPOINT", "version": VERSION, "evidence_class": "MODEL_ANALYSIS", "decision_reference": ta.DECISIONS,
        "statement": ta.STATEMENT,
        "verdict": letter, "verdict_name": VERDICTS[letter], "verdicts": dict(VERDICTS),
        "why_not_the_others": {
            "B": "no implementation step waits on a faculty decision: the two the audit raised (the amendment and the grant re-ligation) were decided on 2026-11-17 (FD-TONE-10 to FD-TONE-12)",
            "C": "the engine's order carries what the writer needs (a start, a rate, mcg/min); the shapes that are not mapped are declared gaps, and FR-F needs none of them",
            "D": "the pathway is a declared, reversible insertion on the certified core: one memory, one profile field, one change record, one contributor",
            "E": "the same order runs through one mapping in every registered family and the ten-case matrix came out as predicted",
        } if letter == "A" else {},
        "sequence": [{"id": identity, "what": what, "outcome": outcome} for identity, what, outcome in SEQUENCE],
        "facts": found,
        "adversarial_review": evidence["adversarial_review"],
        "certification": evidence["certification"],
        "confirmations": {
            "gi_pressure_snapshot_unchanged": found["gi_pressure_snapshot"]["record_is_byte_for_byte_the_one_pinned_before_this_cycle"],
            "no_gi_recalibration": found["gi_pressure_snapshot"]["configuration_is_the_one_both_grants_pin"],
            "no_source_control": found["gi_pressure_snapshot"]["gi_mapping_still_maps"] == ["fluid", "blood", "oxygen", "ppi"] and "source control" in not_granted,
            "no_consciousness_authority_expansion": "mental_status" not in found["authority"]["authority_domain"] and "consciousness authority" in not_granted,
            "no_terminal_authority_expansion": "terminal semantics" in not_granted and dict(grants.GRANT_V3["collapse_boundary"])["is_a_terminal_state"] is False,
            "no_resident_deployment": (found["authority"]["common_core_runtime_authority"] is False and not found["authority"]["registered_adapters_declaring_the_reader"]
                                       and "resident deployment" in not_granted),
            "no_clinical_validation_claim": "clinical validation" in not_granted and "not a clinical validation" in ta.STATEMENT,
            "live_authority_still_stops_on_norepinephrine": found["authority"]["norepinephrine_is_a_supported_authority_action"] is False and "norepinephrine" in not_granted,
        },
        "next_human_action": "A faculty member decides how the FR-F candidate is put before a human reviewer (which witness or witnesses, blinded or not, with which questions) and "
                             "whether a pump-dependent afterload sensitivity is needed before any educational use of a vasopressor. Nothing else is to be done until then.",
        "open_faculty_decisions": [
            "how FR-F_TONE_V1_CANDIDATE is reviewed by a human (no review set and no screen were built)",
            "whether the output cost of tone must depend on the pump (today one sensitivity for every pump and volume)",
            "whether the support should recruit venous return or carry any inotropic effect",
            "whether a patient who arrives vasoconstricted or already on a vasopressor has to be representable",
            "whether an authored distributive case is wanted (the vasodilatory reader is SYNTHETIC_ONLY)",
            "whether stopping and titrating the infusion must be mapped before a human review",
            "the human re-review of FR-A and FR-D under the ratified pressure snapshot (desirable, not blocking: FD-TONE-08)",
        ],
        "limitations": ta.load(ta.PROBES_PATH)["limitations"],
    }
    body["provenance"] = hr.provenance(record_id=VERSION, generated_on=GENERATED_ON, source_snapshot_id=found["gi_pressure_snapshot"]["id"], grant_id=found["grants"]["live"],
                                       generating_code={"clinical_core": found["core"]["digest"], "test_tone_pathway_checkpoint.py": _sha(Path(__file__).resolve())},
                                       source_data={"evidence": evidence, "candidate": found["candidate"]["record_digest"], "probes": found["probes"]["record_digest"]})
    return hr.seal(body)


def write() -> str:
    return hr.write(PATH, build())


# -- the tests -------------------------------------------------------------------------------------------------------------------------

#: Typed from the commit this cycle started on (caa0b0f): the ratified GI pressure snapshot's record, by content, and the configuration the live authority runs. Neither is
#: recomputed here: a test that compared the file with a pin taken from the same working tree would say nothing.
GI_SNAPSHOT_RECORD_SHA256 = "dc5da76ea764759552d6107fd05584257903e16bb04cefe139486a0b343c922e"
GI_CONFIGURATION_DIGEST = "70e6826cb2844bace6e3249058638340d00d80f84f8fdd2a5a2e752028db0641"


def test_the_gi_pressure_snapshot_is_byte_for_byte_the_one_ratified_before_this_cycle():
    """It does not wait for the checkpoint: the snapshot is frozen whatever the verdict (FD-TONE-07)."""
    import runtime_pressure_grant as grants
    import runtime_pressure_snapshot as ps
    assert _sha(ROOT / ps.RECORD_FILE) == GI_SNAPSHOT_RECORD_SHA256 and ps.CONFIGURATION_DIGEST == GI_CONFIGURATION_DIGEST
    assert hr.load_index()["records"][Path(ps.RECORD_FILE).name] == {"class": hr.LEGACY_UNVERSIONED, "file_sha256": GI_SNAPSHOT_RECORD_SHA256}
    assert grants.CONFIGURATION_DIGEST_V2 == GI_CONFIGURATION_DIGEST == dict(grants.GRANT_V3["pressure_snapshot"])["configuration_digest"]


@pytest.fixture(scope="module")
def checkpoint():
    if EVIDENCE is None and not PATH.exists():
        pytest.skip("the checkpoint is written after the candidate is reviewed and certified: there is nothing to check yet")
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_the_checkpoint_is_a_sealed_versioned_record_with_exactly_one_verdict(checkpoint):
    assert hr.record_problems(checkpoint) == [] and checkpoint["version"] == VERSION and checkpoint["provenance"]["record_id"] == VERSION
    assert hr.load_index()["records"][PATH.name] == {"class": hr.VERSIONED, "file_sha256": hr.file_sha256(PATH), "record_id": VERSION,
                                                    "record_digest": checkpoint["record_digest"]}
    assert checkpoint["verdicts"] == VERDICTS and checkpoint["verdict"] in VERDICTS and checkpoint["verdict_name"] == VERDICTS[checkpoint["verdict"]]
    assert [item["id"] for item in checkpoint["sequence"]] == [f"P3-{number}" for number in range(387, 402)]
    assert "not a clinical validation" in checkpoint["statement"]


def test_what_the_checkpoint_says_of_the_tree_is_what_the_tree_says(checkpoint):
    found = facts()
    for section in ("grants", "authority", "gi_pressure_snapshot", "mapping", "candidate", "probes"):
        assert checkpoint["facts"][section] == json.loads(json.dumps(found[section])), section
    core = checkpoint["facts"]["core"]
    assert core == json.loads(json.dumps(found["core"]))
    assert core["off_by_default"] is True and core["registered_as_the_last_lineage_member"] is True
    assert all(value is True for item in core["predecessors_rebuilt_from_the_live_tree"].values() for key, value in item.items() if key != "touched")


def test_the_verdict_is_the_one_the_facts_and_the_typed_evidence_allow(checkpoint):
    evidence = {"adversarial_review": checkpoint["adversarial_review"], "certification": checkpoint["certification"]}
    assert EVIDENCE == evidence, "the typed evidence in this file is the evidence the record was written with"
    assert checkpoint["verdict"] == verdict_allowed(facts(), evidence)
    certified = checkpoint["certification"]
    assert certified["tests"] > 0 and certified["fingerprint"] and certified["stage"] == "CANDIDATE_UNDER_THE_CERTIFICATION_PREVIEW"
    review = checkpoint["adversarial_review"]
    assert review["reviews"] == 1 and isinstance(review["findings"], list) and all(item["disposition"] for item in review["findings"])
    if checkpoint["verdict"] == "A":
        assert certified["failures"] == 0 and certified["errors"] == 0 and certified["regressions_failed"] == 0 and review["unresolved_blocking_findings"] == []
        assert set(checkpoint["why_not_the_others"]) == {"B", "C", "D", "E"}


def test_the_confirmations_are_true_of_the_live_code(checkpoint):
    import runtime_authority as ra
    import runtime_pressure_grant as grants
    import runtime_shadow as rs
    assert set(checkpoint["confirmations"].values()) == {True}
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False and "norepinephrine" not in ra.SUPPORTED_ACTIONS
    assert tuple(ra.AUTHORITY_DOMAIN) == ("sbp", "dbp", "map") and tuple(ra.AUTHORITY_CASES) == ("gi_bleed_57m", "gi_bleed_72f")
    assert grants.GRANT_V3["pressure_snapshot"] == grants.GRANT_V2["pressure_snapshot"] and grants.GRANT_V3["cases"] == grants.GRANT_V2["cases"]
    assert checkpoint["facts"]["candidate"]["faculty_verdict"] is None and checkpoint["facts"]["candidate"]["chosen_witness"] is None
    assert "decides how the FR-F candidate is put before a human reviewer" in checkpoint["next_human_action"]
    assert len(checkpoint["open_faculty_decisions"]) >= 5 and checkpoint["limitations"]
