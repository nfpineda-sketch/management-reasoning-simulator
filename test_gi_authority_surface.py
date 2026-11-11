"""P3-193 to P3-196 and P3-198: the authority surface inventory, the experiment design, the failure contract, the UnresolvedBoundary audit and the
readiness checkpoint -- as a RECORD, with the parts that can be checked against the code checked by ``test_phase3_gi_authority_readiness``.

TEST-SIDE. Read-only: it enables no authority, registers no snapshot, terminates no encounter and writes no state. A statement here is one of
three kinds, and says which: ``VERIFIED`` (a test recomputes it from the code or from a live run), ``RECORDED`` (taken from a committed record or
document of an earlier cycle) or ``DESIGN`` (a proposal that nothing implements).
"""
from __future__ import annotations

import json
import os
import re
from typing import Mapping, Sequence

import test_gi_snapshot_analysis as an

READINESS_FILE = "docs/revision/PHASE3_GI_AUTHORITY_READINESS.json"
READINESS_VERSION = "P3-193"

LEGACY_AUTHORITY = "LEGACY_AUTHORITY"
SHADOW_AVAILABLE = "COMMON_CORE_SHADOW_AVAILABLE"
CERTIFIED_NOT_AUTHORIZED = "COMMON_CORE_CERTIFIED_BUT_NOT_AUTHORIZED"
MISSING = "MISSING_COMMON_CORE"
UNRESOLVED_BOUNDARY = "UNRESOLVED_BOUNDARY"
CLASSES = (LEGACY_AUTHORITY, SHADOW_AVAILABLE, CERTIFIED_NOT_AUTHORIZED, MISSING, UNRESOLVED_BOUNDARY)

#: P3-193. ``runtime_owner`` is LEGACY_AUTHORITY for every row, today: ``COMMON_CORE_RUNTIME_AUTHORITY`` is False and no authority gate can open.
#: ``common_class`` is the strongest status the common core has for the output. ``basis`` says whether a test or a document holds it.
INVENTORY = (
    {"output": "sbp / dbp / map", "resident_visible": True, "common_class": CERTIFIED_NOT_AUTHORIZED, "basis": "VERIFIED + RECORDED",
     "evidence": "the pressure core is part of the certified lineage; `gi_pressure_committed` is the ONE registered approval (DEVELOPMENT_AUTHORITY_EXPERIMENT_ONLY, "
                 "GI cases 57m/72f); a first experiment (3 authority minutes) and a 26-trajectory series ran on the PHASE2 CLOSURE core (digest 22b90a6f...), not on the active lineage member",
     "gap": "re-run the authority series on the active lineage member; the common SBP falls below the legacy engine's own minimum (50 / 58 mmHg) from minute 153 (57m) / 144 (72f) untreated; "
            "no clinical tolerance exists; the approved point is not clinically validated"},
    {"output": "heart rate (monitor rate)", "resident_visible": True, "common_class": SHADOW_AVAILABLE, "basis": "VERIFIED",
     "evidence": "the shadow computes `monitor_rate_bpm`; it is a certified-comparison `display` variable with tolerance TBD; never in an approved domain",
     "gap": "no approval, no snapshot; differences are expected-architectural (up to 17 bpm over the 14 required runs); 3 minutes of opposite direction in the crystalloid-only course"},
    {"output": "pulse present / rhythm", "resident_visible": True, "common_class": SHADOW_AVAILABLE, "basis": "VERIFIED",
     "evidence": "categorical equality: the pulse agrees at every one of 1930 compared minutes of the 14 required runs",
     "gap": "the terminal path of the same state is UNRESOLVED_BOUNDARY (below); the pulse flag itself is not an authority candidate"},
    {"output": "SpO2", "resident_visible": True, "common_class": SHADOW_AVAILABLE, "basis": "VERIFIED",
     "evidence": "equal at all 1930 compared minutes",
     "gap": "agreement is NOT evidence of validity: in GI the oxygenation chain is not exercised (both engines hold the authored value)"},
    {"output": "respiratory rate", "resident_visible": True, "common_class": SHADOW_AVAILABLE, "basis": "VERIFIED",
     "evidence": "a certified-comparison `display` variable; architecture-explained in GI (PHASE3_RUNTIME_INTEGRATION)",
     "gap": "after treatment the engines move it in opposite directions in the delayed-treatment and crystalloid-only courses (55 compared minutes)"},
    {"output": "lactate", "resident_visible": True, "common_class": SHADOW_AVAILABLE, "basis": "VERIFIED",
     "evidence": "a certified-comparison `display` variable; architecture-explained in GI",
     "gap": "after treatment the legacy lab falls and the common value does not (62 compared minutes of opposite direction)"},
    {"output": "haemoglobin", "resident_visible": True, "common_class": SHADOW_AVAILABLE, "basis": "VERIFIED",
     "evidence": "the legacy value falls with untreated haemorrhage (6.69 to 4.54 g/dL at minute 240) and the common value stays near 6.4: architecture-explained in GI (PHASE3_RUNTIME_INTEGRATION), although the comparison table calls the variable `exact`",
     "gap": "the `exact` status holds only for the certified comparison runs, not for the live GI course"},
    {"output": "capillary refill (CRT)", "resident_visible": True, "common_class": SHADOW_AVAILABLE, "basis": "RECORDED",
     "evidence": "deferred by the faculty out of the first domain: its divergence is only partly explained",
     "gap": "no approval"},
    {"output": "consciousness category (mental status)", "resident_visible": True, "common_class": CERTIFIED_NOT_AUTHORIZED, "basis": "VERIFIED",
     "evidence": "PHASE2_AMENDMENT_2 (certified) in the GI development shadow under the three witnesses and GI_DEVELOPMENT_SNAPSHOT_V1; the independent evaluator reproduces it bit for bit",
     "gap": "the legacy engine and the app READ this field (consumers below); 461 compared minutes are POTENTIAL_EDUCATIONAL_PROBLEM (legacy and common differ by two bands, or Alert against not Alert); "
            "the gate, the ownership contract and `commit` are written for numeric pressure fields; every magnitude is a development region"},
    {"output": "collapse state (soft collapse: none / impending / established)", "resident_visible": False, "common_class": SHADOW_AVAILABLE, "basis": "VERIFIED",
     "evidence": "the amendment's predicate is recorded beside the legacy engine in the terminal-boundary block of the trace",
     "gap": "the legacy engine has no collapse field (only an arrest flag): there is nothing to compare with and nothing to write"},
    {"output": "terminal state (arrest / terminalisation from the common core)", "resident_visible": True, "common_class": UNRESOLVED_BOUNDARY, "basis": "VERIFIED",
     "evidence": "the core raises UnresolvedBoundary at minute 349 untreated (effective output zero with a pulse and no declared terminal transition)",
     "gap": "no terminal rule is declared and none may be invented; a runtime terminal mapping is a separate faculty decision"},
    {"output": "respiratory support / work of breathing / extremities", "resident_visible": True, "common_class": MISSING, "basis": "VERIFIED",
     "evidence": "no variable of the certified comparison table carries them: they are legacy-only descriptors",
     "gap": "nothing common to compare with"},
    {"output": "glucose / potassium / FiO2 / delivered volumes", "resident_visible": True, "common_class": LEGACY_AUTHORITY, "basis": "VERIFIED",
     "evidence": "`exact` comparison variables that both engines hold from the same authored or delivered inputs: not outputs of a common law",
     "gap": "not authority candidates"},
)

#: P3-194A: the candidate domains, ranked by readiness (best first).
RANKING = (
    {"rank": 1, "domain": "pressure (sbp, dbp, map)", "readiness": "MACHINERY_READY",
     "why": "the only domain with an approved development snapshot, a gate, an atomic transaction, a store and a replay; nothing new to build",
     "needs": "re-validation on the active lineage member (cheap, no physiology)"},
    {"rank": 2, "domain": "consciousness category, ONLY together with pressure", "readiness": "DESIGN_NEEDS_EXTENSION",
     "why": "the category is a function of the same relative delivery and perfusion that drive the pressure: written alone it would show a resident a legacy pressure beside a common consciousness "
            "that came from a different course; the pair is the smallest coherent surface, and mirrors the rule that the three pressures are owned together",
     "needs": "a writer for a categorical field, a pairing rule, the snapshot binding, the audit of the consumers of mental status, the layer's ability to run the snapshot by id and digest"},
    {"rank": 3, "domain": "collapse state", "readiness": "RECORD_ONLY",
     "why": "no legacy field exists to write and none to compare: it stays in the artifact as a comparison-only value and is never written or shown",
     "needs": "nothing, as long as it stays record-only"},
    {"rank": 4, "domain": "terminal state / arrest", "readiness": "BLOCKED",
     "why": "UnresolvedBoundary: no terminal rule is declared, and the faculty has not authorised one",
     "needs": "a faculty decision on a runtime terminal mapping (not made, not invented here)"},
    {"rank": 5, "domain": "heart rate, respiratory rate, lactate, haemoglobin, CRT", "readiness": "NOT_YET",
     "why": "opposite-direction differences after treatment, partial explanations, or an explicit faculty deferral (CRT)",
     "needs": "faculty reading of the differences first"},
)

#: P3-193A: what the earlier pressure-authority experiment did and did not establish. ``RECORDED`` unless a test says otherwise.
PRIOR_PRESSURE_AUTHORITY = {
    "validated": ["pressure only: sbp and dbp written, map derived by the display", "development and faculty environments only",
                  "the two allowlisted GI cases", "one transaction per turn: capture, compute, validate, atomic commit or abort",
                  "hard-fail, visible to the faculty, with no engine switch inside an encounter (HARD_FAIL_VISIBLE_TO_FACULTY)",
                  "a first experiment of 3 authority minutes and a series of 26 eligible trajectories (64 authority minutes), replayed exactly"],
    "ran_on": "the PHASE2 CLOSURE core (digest 22b90a6f..., 141 sources): the active lineage member is now PHASE2_AMENDMENT_2 (a0af7d08..., 144 sources)",
    "not_established": ["consciousness, collapse or any other output", "clinical validity of any magnitude (0 of 58 calibration regions approved by the faculty)",
                        "that the pressure result still holds on the active lineage member: it must be re-run",
                        "a closed provenance note left open by the 26-trajectory series (P3-51 verdict B); its later status is not re-audited here"],
    "registry_today": ["gi_pressure_committed"],
}

#: P3-194: the design of a FUTURE experiment. Nothing here is implemented; nothing here may be switched on.
DESIGN = {
    "name": "GI_PRESSURE_PLUS_CONSCIOUSNESS_DEVELOPMENT_AUTHORITY_EXPERIMENT (DESIGN ONLY)",
    "scope": {"environments": ["development", "faculty"], "cases": ["gi_bleed_57m", "gi_bleed_72f"], "family": "gi_bleed",
              "pilot": "excluded", "resident": "excluded", "scoring": "legacy, unchanged",
              "window": "scripted scenarios of at most 240 simulated minutes (109 minutes before the boundary); the experiment ends there by its own script, the encounter is never terminated by the common core",
              "domain": ["sbp", "dbp", "map (derived by the display)", "mental_status (the legacy word of the common category)"],
              "record_only": ["collapse state"], "never_written": ["hr", "spo2", "respiratory_rate", "lactate", "haemoglobin", "crt", "rhythm", "pulse", "arrest"]},
    "stages": [
        "0. re-run the pressure authority series on the active lineage member (no physiology)",
        "1. technical readiness: a categorical writer with a pairing rule, the snapshot binding, the audit of the consumers of mental status, the layer able to run the snapshot by id and digest",
        "2. dry run: the full capture, compute and validate steps for the pair on the 14 scenarios, WITHOUT commit (this cycle's counterfactual harness is its first form)",
        "3. only with a written faculty grant: the first development commit, bounded as above",
    ],
    "transaction": ["capture the authoritative state (copy, nothing written)", "compute: the common candidate of the minute from the shadow, beside the legacy counterfactual",
                    "validate: the existing ten checks plus snapshot_bound, pair_complete, consumers_declared, window_open",
                    "commit ONCE, from one prepared mapping, to a copy the caller owns, with the gate re-evaluated at commit; or abort with a rollback artifact"],
    "no_mixed_trajectory": "the pair is written in one transaction or not at all; a minute is never half common, half legacy; after the first commit the encounter never returns to the legacy engine",
    "snapshot_binding": {"snapshot_id": an.SNAPSHOT_ID, "bound_by": ["snapshot_id", "identity_digest", "record_digest", "core lineage digest", "every value equal to the record"],
                         "no_implicit_defaults": "the Amendment-2 profile is built from the record, never from the names in `systemic_consciousness.WITNESSES`; a missing or different value refuses",
                         "registered_as_authority": False},
}

#: P3-195. Every row names the DETECTION (existing code or a required addition), what happens BEFORE the first authoritative commit and AFTER it.
FAILURE_CONTRACT = (
    {"failure": "lineage mismatch", "detects": "gate condition `phase2_digest` (`core_lineage_ok`), re-evaluated at commit", "exists": True,
     "before_first_commit": "the gate refuses: the encounter runs in legacy mode from its first minute; the refusal is recorded",
     "after_first_commit": "hard fail: the experiment HALTS (INVALID_FOR_CONTINUATION); no silent switch to legacy"},
    {"failure": "snapshot mismatch", "detects": "`approved_snapshot` / `snapshot_is_wellformed` for the pressure point (exists); the id + digest + value binding of GI_DEVELOPMENT_SNAPSHOT_V1 (REQUIRED ADDITION)",
     "exists": "partly",
     "before_first_commit": "refuse to open the site; legacy for the whole encounter", "after_first_commit": "hard fail and halt; a configuration change inside the encounter halts (CONFIGURATION_CHANGED)"},
    {"failure": "unsupported action", "detects": "`unsupported_among` over the turn's actions, BEFORE the candidate is looked up (exists)", "exists": True,
     "before_first_commit": "the encounter is ineligible: legacy throughout", "after_first_commit": "hard fail and halt (UNSUPPORTED_AUTHORITY_ACTION); the minute already committed is not rewritten"},
    {"failure": "unresolved boundary", "detects": "validation `no_unresolved_boundary` over the shadow session's failures (exists)", "exists": True,
     "before_first_commit": "abort the minute with a rollback artifact; legacy continues only if no commit ever happened",
     "after_first_commit": "hard fail and halt: NOT a terminal rule, an experiment stop; the encounter itself is not terminated by the common core"},
    {"failure": "common-core invariant failure", "detects": "validation `invariants_hold` and `no_core_failure` (exists)", "exists": True,
     "before_first_commit": "abort the minute, nothing written", "after_first_commit": "hard fail and halt"},
    {"failure": "replay mismatch", "detects": "validation `minute_reproducible` (replay digest equals the expected digest) (exists)", "exists": True,
     "before_first_commit": "abort the minute", "after_first_commit": "hard fail and halt; the artifact keeps both digests"},
    {"failure": "partial output failure", "detects": "`commit` builds ONE prepared mapping and raises AuthorityRefused on any failure, leaving the state exactly as captured (exists for the pressure fields; a categorical field is a REQUIRED ADDITION)",
     "exists": "partly", "before_first_commit": "nothing was written; abort", "after_first_commit": "the transaction is ABORTED, the prior commit stands, the experiment HALTS; a half-written pair cannot exist"},
    {"failure": "trace persistence failure", "detects": "the artifact store is mandatory for an experiment (absolute path outside the repository); a store failure is a stop condition (exists for the pressure experiment)",
     "exists": True, "before_first_commit": "the site does not open; legacy throughout", "after_first_commit": "hard fail and halt; the encounter is not continued with the other engine"},
)
FAILURE_RULES = ("authority fails CLOSED", "no silent fallback after the first authoritative commit", "before the first commit the legacy engine may continue, because authority never began",
                 "a halted experiment is for replay and analysis, never for continuation", "the common core never terminates an encounter")

BLOCKERS = (
    {"id": "B1", "kind": "faculty decision", "blocker": "an authority grant, and its approval of a snapshot FOR AUTHORITY: GI_DEVELOPMENT_SNAPSHOT_V1 is a development snapshot, the registry holds only the pressure point"},
    {"id": "B2", "kind": "faculty decision", "blocker": "ratification of GI_DEVELOPMENT_SNAPSHOT_V1 itself (selected here by rule, as the assignment authorises; the faculty has not seen it run)"},
    {"id": "B3", "kind": "technical", "blocker": "the gate (`AUTHORITY_DOMAIN`), the ownership contract and `commit` are pressure-specific; a categorical field and the pairing rule are not built"},
    {"id": "B4", "kind": "technical", "blocker": "the layer builds Amendment-2 witnesses from the NAMES in `systemic_consciousness.WITNESSES`; it cannot run a snapshot by id and digest (a layer change and its certification)"},
    {"id": "B5", "kind": "audit", "blocker": "the readers of `mental_status` (the legacy engine's order validation and the app's feedback, trace, image and PDF paths) are listed, not audited"},
    {"id": "B6", "kind": "faculty reading", "blocker": "the educational reading of the differences: 461 minutes of consciousness differing by two bands or Alert against not Alert, and opposite-direction responses of lactate and respiratory rate after treatment"},
    {"id": "B7", "kind": "technical", "blocker": "the pressure authority series ran on the closure core: re-run it on the active lineage member"},
    {"id": "B8", "kind": "boundary", "blocker": "UnresolvedBoundary from minute 349 untreated: bounded away by the scripted window; any unbounded or resident-facing use needs a terminal mapping decision"},
    {"id": "B9", "kind": "evidence", "blocker": "the common pressure falls below the legacy engine's own minimum (50 / 58 mmHg) from minute 153 (57m) / 144 (72f) untreated, and reads 20 mmHg or less from about minute 274: a window bound or an explicit faculty reading"},
    {"id": "B10", "kind": "faculty decision", "blocker": "what a resident would see, if anything, and the pilot: not granted, not designed here"},
)

READINESS_VERDICT = "GI_READY_FOR_DEVELOPMENT_AUTHORITY_EXPERIMENT_DESIGN_REVIEW"
READINESS_OPTIONS = ("GI_READY_FOR_DEVELOPMENT_AUTHORITY_EXPERIMENT_DESIGN_REVIEW", "GI_SNAPSHOT_READY_BUT_AUTHORITY_BLOCKED_BY_TERMINAL_BOUNDARY",
                     "GI_SNAPSHOT_NEEDS_MORE_CALIBRATION", "GI_AUTHORITY_ARCHITECTURE_NEEDS_REDESIGN")
BOUNDARY_OPTIONS = ("UNRESOLVEDBOUNDARY_NOT_REACHABLE_IN_PROPOSED_AUTHORITY_WINDOW", "AUTHORITY_WINDOW_CAN_BE_SAFELY_BOUNDED_BEFORE_BOUNDARY",
                    "TERMINAL_MAPPING_REQUIRED_BEFORE_AUTHORITY", "COMMON_CORE_BOUNDARY_REDESIGN_REQUIRED")
BOUNDARY_VERDICT = "AUTHORITY_WINDOW_CAN_BE_SAFELY_BOUNDED_BEFORE_BOUNDARY"
PROPOSED_WINDOW_MINUTES = 240

#: modules that are neither tests, regressions, tools nor the validation corpus: the ones whose reading of `mental_status` is a runtime consumer.
_EXCLUDED = re.compile(r"^(test_|regression_|tools_)")


def mental_status_consumers(root: str = ".") -> dict:
    """VERIFIED: the repository's runtime modules that mention ``mental_status``, with the count of lines (the validation corpus is never opened)."""
    out = {}
    for name in sorted(os.listdir(root)):
        if not name.endswith(".py") or _EXCLUDED.match(name):
            continue
        with open(os.path.join(root, name), encoding="utf-8") as handle:
            count = sum(1 for line in handle if "mental_status" in line)
        if count:
            out[name] = count
    return out


def boundary_audit(captures: Mapping) -> dict:
    """P3-196 from the live captures: where the boundary falls, what stops, what the legacy engine shows, and which scenarios reach it."""
    out = {"scenarios_reaching_it": [], "scenarios_not_reaching_it": [], "cases": {}}
    for (case, scenario), captured in sorted(captures.items()):
        reached = any(item["classification"] == "COMMON_BOUNDARY" for item in captured["failures"])
        out["scenarios_reaching_it" if reached else "scenarios_not_reaching_it"].append(
            {"case": case, "scenario": scenario, "minutes_played": captured["minutes_played"]})
    for case in an.CASES:
        captured = captures[(case, "untreated_long")]
        failure = next(item for item in captured["failures"] if item["where"] == "core")
        session = {row["minute"]: row for row in captured["session"]}
        snapshot_rows = captured["witnesses"]["CENTER_REFERENCE"]
        established = next(row["minute"] for row in snapshot_rows if row["collapse_state_index"] >= 2)
        unresponsive = next(row["minute"] for row in snapshot_rows if row["category_index"] >= 3)
        legacy = {row["minute"]: row for row in captured["legacy"]}
        legacy_sbp = [row["sbp"] for row in captured["legacy"] if row["sbp"] is not None]

        def first_below(level):
            return next((minute for minute, row in sorted(session.items()) if row["sbp"] is not None and row["sbp"] < level), None)
        out["cases"][case] = {
            "boundary_minute": failure["minute"], "exception": failure["exception"], "classification": failure["classification"],
            "message_start": failure["message"], "raised_in": "clinical_core/derived.py (effective output reached zero while a pulse is present)",
            "failing_runs": sorted(item["where"] for item in captured["failures"]), "last_recorded_minute_of_every_common_run": max(session),
            "outputs_undefined_from_the_boundary": "every common output of the session and of the three witnesses (the runs FAIL; their rows up to the last recorded minute are kept)",
            "snapshot_witness_unresponsive_at": unresponsive, "snapshot_witness_established_collapse_at": established,
            "boundary_after_established_collapse_minutes": failure["minute"] - established,
            "legacy_at_the_boundary": {key: legacy[max(legacy)].get(key) for key in ("sbp", "dbp", "hr", "mental_status", "pulse_present", "arrested")},
            "legacy_sbp_minimum": min(legacy_sbp),
            "common_sbp_first_below": {str(level): first_below(level) for level in (60, 40, 20, 10, 1)},
            "margin_to_the_proposed_window_minutes": failure["minute"] - PROPOSED_WINDOW_MINUTES,
        }
    out["proposed_window_minutes"] = PROPOSED_WINDOW_MINUTES
    out["verdict"] = BOUNDARY_VERDICT
    out["verdict_options"] = list(BOUNDARY_OPTIONS)
    out["reading"] = ("The boundary is a property of the UNTREATED course (the shared haemorrhage takes the effective output to zero at minute 349 in both cases) and is reached by no scripted "
                      "scenario of the matrix, by the late rescue (order at 215, played to 336) or by any treated course. In an UNBOUNDED window it is reachable, so the verdict is not A. "
                      "The window can be bounded by the experiment's own script, with 109 minutes of margin, and an authority transaction that meets it would abort on `no_unresolved_boundary` and halt visibly: "
                      "an experiment stop, not a terminal rule. A runtime terminal mapping stays required before any unbounded or resident-facing authority; none is invented here.")
    return out


def build_record(captures: Mapping) -> dict:
    return {
        "readiness_version": READINESS_VERSION, "snapshot_id": an.SNAPSHOT_ID,
        "authority": {"enabled": False, "common_core_runtime_authority": False, "granted_by_this_record": False},
        "inventory": list(INVENTORY), "classes": list(CLASSES), "mental_status_consumers": mental_status_consumers(),
        "prior_pressure_authority": PRIOR_PRESSURE_AUTHORITY, "candidate_domain_ranking": list(RANKING), "design": DESIGN,
        "failure_contract": {"rules": list(FAILURE_RULES), "rows": list(FAILURE_CONTRACT)},
        "boundary_audit": boundary_audit(captures), "blockers": list(BLOCKERS),
        "checkpoint": {"verdict": READINESS_VERDICT, "options": list(READINESS_OPTIONS),
                       "reading": "Ready for the faculty's REVIEW of the experiment's design. It is not an authority grant and not a readiness to activate: the blockers above stand."},
    }


def write_record(root: str, captures: Mapping) -> dict:
    record = build_record(captures)
    with open(os.path.join(root, READINESS_FILE), "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=1, sort_keys=True)
    return record
