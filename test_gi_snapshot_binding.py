"""P3-199 and P3-204: the ratification record of ``GI_DEVELOPMENT_SNAPSHOT_V1``, and (since P3-214) a RE-EXPORT of the binding that now lives in the layer.

The exact binding to the ratified snapshot -- its pinned identities, the hardened refusals the independent review of P3-208 forced, ``bound_is_v1``, the
adapter and the run check -- moved into ``runtime_authority_pair`` (the Phase-3 layer, dormant). Every name below that is not defined here IS the layer's
object, so every test that used this module's binding now exercises the layer's code and nothing else.

What stays here is test-side tooling only: the ratification record's builder and its faculty decisions. Nothing here registers, approves or enables
anything: the authority registry (``runtime_authority.APPROVED_SNAPSHOTS``) is untouched.
"""
from __future__ import annotations

import json
import os

import runtime_authority as authority
import runtime_shadow as rs
import test_gi_snapshot_analysis as an
from runtime_authority_pair import (BoundSnapshot, BoundSnapshotAdapter, IS_NOT, MODIFIED_PARAMETER, NOT_A_DEVELOPMENT_SNAPSHOT, NOT_RATIFIED,  # noqa: F401
                                    PARTIAL_SNAPSHOT, PRESSURE_POINT, PRESSURE_POINT_MISMATCH, RATIFICATION_FILE, RATIFIED, REFUSALS, SNAPSHOT_FILE,
                                    SnapshotBindingError, V1_CORE_DIGEST, V1_CORE_VERSION, V1_FILE_SHA256, V1_FULL_DIGEST, V1_ID, V1_IDENTITY_DIGEST,
                                    V1_PROFILE_DIGEST, V1_RATIFICATION_DIGEST, V1_RECORD_DIGEST, V1_VALUES_DIGEST, V1_VERSION, WITNESS_SUBSTITUTED,
                                    WRONG_CORE_LINEAGE, WRONG_DIGEST, WRONG_SNAPSHOT_ID, WRONG_VERSION, bind, bound_is_v1, build_profile, identity_of,
                                    lineage_is_v1, live_lineage, open_bound_runner, plain, pressure_point_matches, profile_digest, runner_is_bound,
                                    verify_ratification, verify_record)

ROOT = os.path.dirname(os.path.abspath(__file__))
RATIFIED_ON = "2026-11-11"

# -- P3-199: the ratification record ---------------------------------------------------------------------------------------------------------

FACULTY_DECISIONS = {
    "FD-AUTH-01": "Ratify GI_DEVELOPMENT_SNAPSHOT_V1 for DEVELOPMENT EXPERIMENTS. Status RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS. Not a clinical calibration, a "
                  "production profile, a resident profile or an authority-approved snapshot. Preserve LOW, V1 and HIGH as sensitivity witnesses; do not replace "
                  "the underlying development region with V1.",
    "FD-AUTH-02": ["it satisfies the predeclared H1-H7 criteria", "it is interior to every approved parameter region", "it maximizes the minimum boundary margin",
                   "no legacy output was used in the selection rule",
                   "CENTER_REFERENCE was not automatically selected and in fact violates one region-bound criterion",
                   "causal ordering is stable across both GI cases", "recovery semantics satisfy FD-P3-176"],
    "FD-AUTH-03": "No authority yet: COMMON_CORE_RUNTIME_AUTHORITY stays False and no common-core output writes into the real encounter.",
}
REOPENING_RULE = "Snapshot selection is not reopened unless a cycle finds a new structural contradiction (FD-AUTH-02)."


def build_ratification(root: str = ROOT) -> dict:
    """The ratification of version 1, built from the committed record (which stays untouched) and from the registry as it is today."""
    with open(os.path.join(root, SNAPSHOT_FILE), "rb") as handle:
        raw = handle.read()
    record = json.loads(raw.decode("utf-8"))
    reasons = verify_record(record, raw=raw)
    if reasons:
        raise SnapshotBindingError(reasons)
    profile = build_profile(record["values"])
    kept = record["witnesses_preserved_for_ongoing_sensitivity_checks"]
    body = {
        "record_type": "GI_DEVELOPMENT_SNAPSHOT_RATIFICATION", "snapshot_id": V1_ID, "version": V1_VERSION, "status": RATIFIED,
        "ratified_for": "DEVELOPMENT EXPERIMENTS", "ratified_on": RATIFIED_ON, "is_not": list(IS_NOT),
        "faculty_decisions": FACULTY_DECISIONS, "reopening_rule": REOPENING_RULE,
        "snapshot_file": SNAPSHOT_FILE, "snapshot_file_sha256": V1_FILE_SHA256, "identity_digest": V1_IDENTITY_DIGEST, "record_digest": V1_RECORD_DIGEST,
        "values": record["values"], "amendment": record["amendment"],
        "common_core_lineage": {"version_id": V1_CORE_VERSION, "digest": V1_CORE_DIGEST},
        "selection_criteria": record["selection"]["criteria"], "selection_rule": record["selection"]["rule"],
        "boundary_margins": record["margins_to_the_region_bounds"], "min_margin": record["min_margin"], "region_bounds": record["region_bounds"],
        "sensitivity_witnesses": {"LOW": kept["LOW"], "V1": V1_ID, "HIGH": kept["HIGH"],
                                  "region_not_replaced_by_the_point": True,
                                  "note": "LOW and HIGH are the core's own witnesses, unchanged. CENTER_REFERENCE stays a test witness of the layer and "
                                          "is not the snapshot. The sweep of the full region stays the sensitivity check.",
                                  "event_times_not_bounded_by_the_witnesses_minutes": kept["event_times_not_bounded_by_the_witnesses_minutes"]},
        "uncertainty": record["uncertainty"], "falsifiers": record["falsifiers"],
        "binding": {"bound_profile_digest": profile_digest(profile), "pressure_point": PRESSURE_POINT,
                    "pressure_point_digest": authority.APPROVED_POINT_DIGESTS[PRESSURE_POINT],
                    "profile_built_from": "the committed default profile plus amendment_2 built only from the record's ten values"},
        "authority": {"added_to_an_approved_authority_snapshot_registry": False,
                      "approved_authority_snapshots_today": sorted(authority.APPROVED_SNAPSHOTS),
                      "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY},
    }
    return {**body, "ratification_digest": an.digest(body)}


def write_ratification(root: str = ROOT) -> dict:
    ratification = build_ratification(root)
    with open(os.path.join(root, RATIFICATION_FILE), "w", encoding="utf-8") as handle:
        json.dump(ratification, handle, indent=1, sort_keys=True)
    return ratification
