"""P3-203, P3-205 and P3-209: the pair's design, the collapse-boundary guard, the checkpoint, and the two records of the cycle.

TEST-SIDE. A statement here is ``VERIFIED`` (a test recomputes it), ``MEASURED`` (taken from a live run recorded in this cycle) or ``DESIGN`` (a
proposal nothing in the runtime layer implements). Nothing here enables authority or registers a snapshot for authority.
"""
from __future__ import annotations

import json
import os
from typing import Mapping, Sequence

import runtime_authority as authority
import runtime_shadow as rs
import test_gi_pair_dry_run as dry
import test_gi_preauthority_review as review
import test_gi_snapshot_analysis as an
import test_gi_snapshot_binding as binding

ROOT = os.path.dirname(os.path.abspath(__file__))
REVIEW_FILE = "docs/revision/PHASE3_GI_PREAUTHORITY_REVIEW.json"
DRY_RUN_FILE = "docs/revision/PHASE3_GI_PAIR_DRY_RUN.json"
#: The commit whose tree is the closure-core side of the pressure comparison (the last series before the first amendment was integrated).
CLOSURE_SERIES_COMMIT = "e0c9ae5"

#: P3-203 (DESIGN). The pair, and what stays out of it.
PAIR_DESIGN = {
    "pressure_domain": {"written": ["sbp", "dbp"], "derived_by_the_display": ["map"], "source": "the pressure point of the bound run, shaped like the legacy display",
                        "approval_today": "gi_pressure_committed (development experiment only)"},
    "consciousness_domain": {"written": ["mental_status"], "value": "the legacy word of the common observable category",
                             "mapping": {str(level): word for level, word in sorted(dry.WORD_OF.items())},
                             "source": "PHASE2_AMENDMENT_2 composite (F, established collapse) under GI_DEVELOPMENT_SNAPSHOT_V1, read from the SAME run as the pressures",
                             "approval_today": "none: the snapshot is ratified for development experiments, not approved for authority",
                             "open_point": "the legacy engine writes 'Unresponsive' only at an arrest; the snapshot reads it WITH a pulse from minute 158 untreated. "
                                           "Whether that word may carry both meanings is a faculty decision."},
    "not_authoritative": {"collapse_state": "recorded and compared, never written, never shown", "terminal_state": "no terminal rule exists and none is invented"},
    "never_written": list(dry.NEVER_WRITTEN),
    "atomicity": ["the pair is validated as ONE transaction: every check in CHECKS must pass or nothing would be written",
                  "the four fields would be written from ONE prepared mapping (the existing commit rule), so pressure-common with consciousness-legacy cannot exist after a commit",
                  "the two halves must be the same physical course: every reading that does not depend on the ten magnitudes is equal in the pressure run and in the bound run, minute by minute",
                  "after the first refusal the experiment is halted for the encounter: no later minute is evaluated as a commit"],
    "can_the_architecture_guarantee_it": "YES in the dry transaction (verified on every would-commit minute of the series). NOT YET in the layer: "
                                         "AUTHORITY_DOMAIN, the ownership contract and AuthorityTransaction.commit accept numeric pressure fields only.",
}

#: P3-205 (DESIGN, with the detection VERIFIED in the dry transaction).
GUARD_DESIGN = {
    "rule": "if the bound common-core run reads ESTABLISHED circulatory collapse at any minute a transaction would cover, the transaction aborts and the experiment hard-stops "
            "BEFORE that minute is committed",
    "means": "EXPERIMENT NOT VALID BEYOND THIS PHYSIOLOGICAL BOUNDARY",
    "does_not_mean": ["the patient died", "a terminal clinical threshold", "a resident-facing outcome", "a rule that ends an encounter"],
    "resident_text": "none: the stop is an experiment event on the faculty surface, never mapped to terminal text",
    "detected_in": "compute: the bound run's collapse predicate is part of the candidate, so it is known before validate ends",
    "precommit": True,
    "covers": "every minute since the last cleared one up to the minute that would be committed (a turn can span many minutes: an infusion advances the engine's clock in one turn)",
    "fail_closed": "a minute the bound run cannot show (a failed or unreproduced run) is not a cleared minute",
    "window": "authority_window_end = min(the predefined time limit, the first established-collapse minute); both are checks of the same transaction",
    "after_the_stop": "no fallback to the legacy engine as authority once a commit has happened: the encounter is INVALID_FOR_CONTINUATION; if nothing was ever committed, authority never began",
    "impending_collapse": "not a stop: only ESTABLISHED is the boundary (FD-AUTH-06)",
}

#: P3-204 (VERIFIED by the tamper tests).
BINDING_CONTRACT = {
    "bound_by": ["snapshot_id", "version", "the file's SHA-256", "identity digest", "record digest", "the digest of the ten values", "common-core lineage (declared, live, and the core's own bytes)",
                 "the ratification record"],
    "profile": "the committed default profile (verified to be the point gi_pressure_committed pins) plus amendment_2 built ONLY from the record's ten values",
    "never_read": ["systemic_consciousness.WITNESSES", "systemic_consciousness.development_profile()", "a witness name"],
    "refusals": list(binding.REFUSALS),
    "every_minute": "the run in hand is re-checked against the bound snapshot (adapter, profile, profile digest, the ten values)",
    "where_it_lives": "TEST-SIDE. The layer still builds its witnesses by name; an authority experiment needs this rule inside the layer, certified.",
}

CHECKPOINT_OPTIONS = ("GI_PRESSURE_CONSCIOUSNESS_READY_FOR_DEVELOPMENT_AUTHORITY_EXPERIMENT", "PRESSURE_READY_BUT_CONSCIOUSNESS_NOT_READY",
                      "SNAPSHOT_READY_BUT_AUTHORITY_TRANSACTION_NOT_READY", "FURTHER_PHYSIOLOGY_OR_ARCHITECTURE_REQUIRED")
CHECKPOINT = "PRESSURE_READY_BUT_CONSCIOUSNESS_NOT_READY"
CHECKPOINT_READING = ("Pressure: the development-authority series is identical on the active core (every value written and every digest that names no version). "
                      "Consciousness: every divergence from the legacy engine is mechanistically coherent, the snapshot binds exactly and the dry pair transaction "
                      "behaves; but the faculty has not yet answered the review of the divergence, the readers of the word have downstream effects whose guards do "
                      "not exist, and the pair's commit path and the snapshot binding exist only test-side. None of this is an authority grant.")
BLOCKERS = (
    {"id": "C1", "kind": "faculty review", "blocker": "FD-AUTH-04: the faculty's answers to the consciousness review table (nine representative episodes) are pending; the assistant does not answer them"},
    {"id": "C2", "kind": "guards", "blocker": "FD-AUTH-05: consciousness authority HAS downstream side effects; seven of the eight guards do not exist (history-taking availability, resident-visible text and display, "
                                              "image contract and prompt, trace and event persistence, AI and faculty analysis payloads, reflection prompts, and the legacy comparison captured before the commit)"},
    {"id": "C3", "kind": "technical", "blocker": "the pair's commit path does not exist in the layer: AUTHORITY_DOMAIN, the ownership contract and commit are numeric-pressure only; it must be built DORMANT and certified, as the pressure path was"},
    {"id": "C4", "kind": "technical", "blocker": "the snapshot binding is test-side: the layer builds witnesses by name and cannot run GI_DEVELOPMENT_SNAPSHOT_V1 by id and digest"},
    {"id": "C5", "kind": "faculty decision", "blocker": "the word 'Unresponsive' with a pulse: the legacy engine writes it only at an arrest; the snapshot reads it from minute 158 untreated"},
    {"id": "C6", "kind": "faculty or engineering decision", "blocker": "'Place an IV line.' is the class vascular_access, outside SUPPORTED_ACTIONS: the commonest GI order hard-stops the experiment"},
    {"id": "C7", "kind": "design", "blocker": "one turn is one transaction and an infusion advances the engine's clock inside ONE turn (four units: 120 minutes): a recovery ordered at minute 158 ends at 278, past the window, "
                                             "and every intermediate minute is covered by one boundary check instead of being committed minute by minute"},
    {"id": "C8", "kind": "faculty decision", "blocker": "an authority grant and an approval of a snapshot FOR AUTHORITY: the registry holds only gi_pressure_committed, and stays that way"},
)
NEXT_PACKAGE = ("1. The faculty answers the consciousness review table (C1) and the two word and action questions (C5, C6). "
                "2. With those answers: design and build DORMANT, in the layer, the guards of the readers (C2), the pair commit path (C3) and the snapshot binding (C4), with their own "
                "mutants and ONE integrated certification of the layer; decide the turn granularity for infusions (C7). "
                "3. Re-run this dry series through the layer's own dormant path. Only then could a faculty decision (C8) authorize the development experiment. "
                "Independently and already possible: the pressure-only development experiment on the active core.")


def series_fingerprint(dump: Mapping) -> dict:
    """What must be identical between two cores, per scenario and per minute: outcomes, written pressures and the version-free digests."""
    out = {}
    for row in dump["rows"]:
        minutes = [[item.get("minute"), item.get("outcome"), item.get("candidate_digest"), item.get("written_digest"), item.get("replay_digest"),
                    item.get("state_digest"), item.get("common_pressures")] for item in (row["artifact"] or {}).get("minutes") or []]
        out[f"{row['case']}/{row['scenario']}"] = {"halted": row["halted"], "committed": row["committed"], "minutes": minutes}
    return out


def dry_run_matrix(runs: Mapping[str, Mapping]) -> dict:
    """The two-case management matrix: for each run the would-commit window and the abort, and whether the two cases agree."""
    rows = {}
    for key, run in sorted(runs.items()):
        summary = run["summary"]
        rows[key] = {name: summary[name] for name in ("minutes_evaluated", "would_commit_minutes", "first_would_commit", "last_would_commit", "first_would_abort",
                                                      "abort_checks", "abort_stage", "authority_had_begun_at_abort", "halted_minutes")}
        rows[key]["orders"] = [[order["minute"], order["clock_after"], order["text"]] for order in run["orders"]]
    scenarios = sorted({key.split("/")[1] for key in rows})
    agree = {scenario: all(rows[f"{dry.CASES[0]}/{scenario}"][name] == rows[f"{dry.CASES[1]}/{scenario}"][name]
                           for name in ("first_would_commit", "last_would_commit", "first_would_abort", "abort_checks"))
             for scenario in scenarios}
    return {"rows": rows, "the_two_cases_agree": agree}


def build_dry_run_record(runs: Mapping[str, Mapping]) -> dict:
    bound = binding.bind()
    return {"dry_run_version": dry.DRY_RUN_VERSION, "what_it_is": "A legacy-authoritative encounter with the pair transaction run DRY beside it. Nothing is committed; commit is never called.",
            "snapshot": bound.summary(), "time_limit_min": dry.TIME_LIMIT_MIN, "checks": list(dry.CHECKS), "pair_domain": list(dry.PAIR_DOMAIN),
            "required_scenarios": list(dry.REQUIRED_SCENARIOS), "extra_scenarios": list(dry.EXTRA_SCENARIOS), "cases": list(dry.CASES),
            "verdict_states": [dry.WOULD_COMMIT, dry.WOULD_ABORT, dry.HALTED],
            "matrix": dry_run_matrix(runs), "runs": {key: runs[key] for key in sorted(runs)},
            "authority": {"common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY, "approved_authority_snapshots": sorted(authority.APPROVED_SNAPSHOTS),
                          "commit_called": False}}


def build_review_record(counterfactual: Mapping, sensitivity: Mapping, snapshot: Mapping, closure_dump: Mapping, active_dump: Mapping,
                        adversarial: Sequence[Mapping] = ()) -> dict:
    found = review.episodes(counterfactual, sensitivity, snapshot["values"])
    audit = review.reader_audit(ROOT)
    directions = {}
    for item in found:
        entry = directions.setdefault(item["direction"], {"episodes": 0, "compared_minutes": 0})
        entry["episodes"] += 1
        entry["compared_minutes"] += item["compared_minutes"]
    comparison = review.compare_pressure_series(closure_dump, active_dump)
    return {
        "review_version": review.REVIEW_VERSION, "snapshot_id": binding.V1_ID,
        "authority": {"enabled": False, "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY,
                      "approved_authority_snapshots": sorted(authority.APPROVED_SNAPSHOTS), "granted_by_this_record": False},
        "consciousness_review": {
            "source": "the POTENTIAL_EDUCATIONAL_PROBLEM minutes of docs/revision/PHASE3_GI_AUTHORITY_COUNTERFACTUAL.json (14 required runs)",
            "episodes": found, "episode_count": len(found), "compared_minutes": sum(item["compared_minutes"] for item in found),
            "by_direction": directions,
            "coherence": {"coherent": sum(1 for item in found if item["coherence"]["verdict"] == review.COHERENT),
                          "contradictions": [f"{item['case']}/{item['scenario']}:{item['start']}" for item in found if item["coherence"]["verdict"] != review.COHERENT]},
            "opposite_direction": review.opposite_direction_explanation(counterfactual, sensitivity, snapshot["values"]),
            "faculty_questions": list(review.FACULTY_QUESTIONS), "faculty_table": review.faculty_table(found),
            "physiology_modified": False,
        },
        "reader_audit": audit,
        "pressure_recertification": {"harness": "test_runtime_authority_series._play_the_battery_with_authority (the existing development harness), both cases",
                                     "closure_tree_commit": CLOSURE_SERIES_COMMIT, "comparison": comparison,
                                     "closure_fingerprint": series_fingerprint(closure_dump), "retuned": False},
        "pair_design": PAIR_DESIGN, "binding_contract": BINDING_CONTRACT, "collapse_boundary_guard": GUARD_DESIGN,
        "adversarial_review": list(adversarial), "adversarial_review_status": "DONE" if adversarial else "PENDING",
        "checkpoint": {"verdict": CHECKPOINT, "options": list(CHECKPOINT_OPTIONS), "reading": CHECKPOINT_READING, "blockers": list(BLOCKERS), "next_package": NEXT_PACKAGE,
                       "provisional": not adversarial},
    }


def write(root: str, review_record: Mapping, dry_record: Mapping) -> None:
    with open(os.path.join(root, REVIEW_FILE), "w", encoding="utf-8") as handle:
        json.dump(review_record, handle, indent=1, sort_keys=True)
    with open(os.path.join(root, DRY_RUN_FILE), "w", encoding="utf-8") as handle:
        json.dump(dry_record, handle, sort_keys=True, separators=(",", ":"))
