"""Live-shadow observability cycle (2026-11-10): the record of the cycle. Pure data.

What this cycle asked: that the live shadow of the two live families be FACULTY-OBSERVABLE, PERSISTENT and
FAILURE-VISIBLE, with one shared rule for when a state may be mapped as an arrival -- and that nothing of it
reach a resident, a score or the engine. Every figure in ``MEASURED`` is recomputed by
``test_shadow_observability.py`` and ``test_shadow_sensitivity.py``.

Nothing here is a default, a calibration, a clinical value or a recommendation. No common-core physiology
changed in this cycle. The witnesses exist to test with; the shadow has no authority.

Numbering. The request numbers this cycle's packages P3-147 to P3-155, continuing after P3-146 (faculty
decision FD-NEW-5: no historical package is renumbered). This cycle's code and tests carry ``p3o``.
"""

STATUS = "LIVE_SHADOW_OBSERVABILITY_DEVELOPMENT_NO_AUTHORITY"
CYCLE = "live shadow observability, 2026-11-10 (request packages P3-147 to P3-155; code label p3o)"
STARTING_HEAD = "1e1859439943dc214b156892fa6a6df4ebcecd4c"

# -- the faculty and architect decisions that opened the cycle ---------------------------------------------------

FACULTY_DECISIONS = {
    "FD-NEW-1": {"row": "FD-P3-139",
                 "decision": "the opioid exact-arrival identity check is a LIVE_SHADOW_ELIGIBILITY_GUARD, not new "
                             "clinical mapping semantics; any mismatch rejects shadow initialization; opioid "
                             "remains a live family",
                 "implemented_as": "the adapter's identity check documents the classification and delegates the "
                                   "shared part to the one eligibility rule"},
    "FD-NEW-2": {"row": "FD-P3-140",
                 "decision": "an arrival mapping is valid only before any positive time advancement, any executed "
                             "intervention and any state mutation that means the patient is no longer at the "
                             "authored arrival; a zero-minute turn does not create a new arrival; a treated "
                             "patient is never remapped as an arrival; for every live family, GI included",
                 "implemented_as": "one shared invariant, ARRIVAL_ELIGIBLE, in the session layer"},
    "FD-NEW-3": {"row": "FD-P3-141",
                 "decision": "correct the one-minute timing offset of the offline development oedema adapter with "
                             "the timing semantics of the corrected live opioid path; no common physiology change",
                 "implemented_as": "the decongestive treatment begins the minute after its order"},
    "FD-NEW-4": {"row": "FD-P3-142",
                 "decision": "the arrival bands and the opioid deepening and recovery rates are NOT added to the "
                             "region ensemble automatically; a bounded sensitivity audit first; a parameter is "
                             "promoted only if its uncertainty can materially change a verdict",
                 "implemented_as": "the audit below; the ensemble's dimensionality is unchanged"},
    "FD-NEW-5": {"row": "FD-P3-143",
                 "decision": "continue with P3-147 onward; historical packages are not renumbered",
                 "implemented_as": "this numbering"},
}

# -- P3-147: the shared session lifecycle -------------------------------------------------------------------------

LIFECYCLE = {
    "package": "P3-147",
    "invariant": "ARRIVAL_ELIGIBLE",
    "conditions": ("clock_at_arrival", "engine_state_is_a_fresh_arrival", "monitor_is_the_authored_arrival",
                   "nothing_administered", "nothing_on_the_diagnostic_record"),
    "not_only_elapsed_minutes": "the engine's state is compared field by field with the same case initialized "
                                "afresh, the monitor with the authored case, and the administration and "
                                "diagnostic records must be empty; the clock is one condition of five",
    "old_bug": {
        "where": "the session's own rule for 'is this still my encounter', shared by every live family",
        "rule_before": "another encounter if the clock is at zero and this session has already seen a turn",
        "defect": "a turn that takes no time leaves the clock at zero, so the page dropped the session and "
                  "opened a new one on the already-treated patient as if it were the arrival; the action of "
                  "that turn and its declared gap were lost from the mirror",
        "zero_minute_orders": {"gi_bleed": ("Place an IV line.", "Consult gastroenterology.",
                                             "Give midazolam 2 mg IV."),
                               "opioid": ("Give midazolam 2 mg IV.", "Place an IV line.")},
        "reproduced_for": ("gi_bleed", "opioid"),
    },
    "rule_now": {
        "kept": "the same case, a clock that has not gone backwards, and not an untouched arrival seen after "
                "this session's encounter left its own",
        "another_encounter": "an untouched arrival once the session's encounter has left its arrival",
        "refused": "a session asked to open on a state that is not an untouched authored arrival opens with no "
                   "run and one recorded failure that names every difference: the encounter is legacy-only",
        "where_fixed": "the shared session layer, once; no family carries its own lifecycle rule",
    },
    "negative_controls": ("patient already treated", "time-advanced patient", "altered arrival vitals",
                          "prior shadow state reopened as a fresh arrival", "incompatible family",
                          "unsupported variant"),
    "families": ("gi_bleed", "opioid"),
    "opioid_identity_classification": "LIVE_SHADOW_ELIGIBILITY_GUARD",
    "residual": "a turn that takes no time AND leaves no trace on the patient (a diagnostic order with no "
                "result yet) does not mark the encounter as having left its arrival; a second attempt at the "
                "same case straight after it, without the page's explicit reset, is read as the same session. "
                "The physiology of both is the same arrival. What can mix is a non-physiological mirrored row; "
                "and, only where a harness reuses order identities across attempts, an action of the second "
                "attempt can be taken for one already mirrored and left out (the page's order identities are "
                "unique, so this is not expected there)",
    "not_compared": "the eligibility rule has no authored reference for the engine's hidden state or for "
                    "top-level keys the arrival does not have; a synthetic state altered only there is read "
                    "as an arrival (no real turn produced one in the review's 962 attempts)",
    "verdict": "SHARED_LIVE_SHADOW_LIFECYCLE_VALIDATED",
}

# -- P3-148: the shadow research trace store ----------------------------------------------------------------------

TRACE_STORE = {
    "package": "P3-148",
    "name": "SHADOW_RESEARCH_TRACE_STORE",
    "is_not": "the authority artifact store: neither store accepts the other's records",
    "on_when": "a faculty or development process environment names an absolute directory outside the "
               "repository; unset, nothing is written, read or created; a deployment secret cannot name one",
    "provenance_labels": ("NONAUTHORITATIVE_SHADOW", "DEVELOPMENT_ONLY"),
    "content": ("family", "case identity", "lineage version and digest", "arrival fingerprint",
                "arrival eligibility", "witness identity", "witness parameter value", "action sequence",
                "order minutes", "effective minutes", "per-minute state digest and channels",
                "replay artifact of every run", "observable readings", "failure state", "structured status",
                "trace digest"),
    "runs": {"gi_bleed": ("SESSION_RUN",),
             "opioid": ("SESSION_RUN", "LOW", "CENTER_REFERENCE", "HIGH")},
    "witnesses_are": "three whole trajectories kept apart; none selected, preferred or averaged",
    "selected_witness": None,
    "records": "immutable and create-only: one per state of a session; the same inputs are the same record, "
               "and the same inputs with different recorded content is a refused collision; a record is "
               "written whole or not at all, only ever directly inside the store's directory, under a name no "
               "field of the trace can steer",
    "attempts": "every record names the record its own session stored before it; that chain, not the arrival "
                "fingerprint, tells two attempts at a case apart",
    "identity_carries_no_participant": True,
    "self_consistency": ("every run is the run its name says and ran the value its witness declares",
                         "every run is as long as its record says, and a short run is marked failed",
                         "the recorded status is what the recorded content adds up to",
                         "the actions are the ones the session run was given",
                         "the labels and the expected witnesses are the family's own"),
    "failed_witness": "kept at its last valid minute with its failure; nothing is made up after it, and its "
                      "replay stops where it stopped",
    "integrity": "a content digest plus the self-consistency checks above: together they catch an accidental "
                 "change and an edit that was re-sealed but no longer tells one story. A forgery rebuilt to be "
                 "consistent in every part is beyond them; no signature is claimed",
    "not_cross_checked": ("turns",),
    "verdict": "SHADOW_TRACE_PERSISTENCE_VALIDATED",
}

# -- P3-149: the faculty-only observer ----------------------------------------------------------------------------

OBSERVER = {
    "package": "P3-149",
    "surface": "a read-only report built from a persisted trace by a faculty or development tool, outside the "
               "encounter page; the frozen first pilot and the page are not modified",
    "why_not_a_page": "the page may not render the shadow at all (a standing guard), and no resident-facing "
                      "module may read the store or the observer",
    "shows": ("family and case", "lineage", "arrival eligibility", "action timeline with effective minutes",
              "every run kept apart", "key channels over time", "failure status", "replay status"),
    "opioid_channels": ("central_availability", "respiratory_rate", "ventilation", "paco2", "spo2",
                        "delivery_rel"),
    "witness_label": "DEVELOPMENT TEST WITNESS",
    "center_reference_is_the_answer": False,
    "envelope": "a derived summary (minimum to maximum of the witnesses), drawn behind the trajectories and "
                "labelled as not a trajectory",
    "read_only": ("issues no order", "alters no state", "selects no authority", "changes no score",
                  "chooses no witness", "writes nothing back to the store"),
    "verdict": "FACULTY_ONLY_SHADOW_OBSERVER_VALIDATED",
}

# -- P3-150: failure visibility -----------------------------------------------------------------------------------

FAILURE_VISIBILITY = {
    "package": "P3-150",
    "codes": ("ARRIVAL_REJECTED", "UNSUPPORTED_ACTION", "WITNESS_FAILED", "REPLAY_MISMATCH", "LINEAGE_REJECTED",
              "TRACE_PERSISTENCE_FAILED", "INTERNAL_SHADOW_ERROR"),
    "states": ("COMPLETE", "COMPLETE_WITH_UNSUPPORTED_ACTIONS", "PARTIAL", "FAILED", "REJECTED"),
    "no_bare_success": "there is no state named success; COMPLETE means every run reached the encounter's "
                       "minute and nothing was reported, and every other state names what is missing",
    "visible_to": ("the trace record", "the faculty observer", "the replay"),
    "not_visible_to": ("the resident", "the score", "the engine"),
    "no_silent_drop": "every action the session MIRRORED has exactly one disposition; a supported action that "
                      "produced neither a contributor nor a declared gap is reported as an internal error. "
                      "Two further rows keep the timeline whole: a contributor built from the engine's own "
                      "state, and an order the session never mirrored",
    "dispositions": ("BUILT", "SKIPPED_NO_PHYSIOLOGY", "DECLARED_GAP", "APPLIED_AS_A_STOP", "UNACCOUNTED",
                     "FROM_ENGINE_STATE", "NOT_MIRRORED", "HELD_NOT_EXECUTED"),
    "mirrored_dispositions": ("BUILT", "SKIPPED_NO_PHYSIOLOGY", "DECLARED_GAP", "APPLIED_AS_A_STOP",
                              "UNACCOUNTED"),
    "held_orders": "as this cycle left it: an order the engine holds until a result arrives was not mirrored, "
                   "and when the engine executed it later the shadow run did NOT carry its effect; it was a "
                   "NOT_MIRRORED row and the status was never COMPLETE. SUPERSEDED by the next cycle (P3-158, "
                   "the resolution record): a held order is now mirrored once, at the minute the engine really "
                   "executes it, and one the engine has not run is a HELD_NOT_EXECUTED row",
    "oxygen_regression": "the earlier defect (oxygen listed as mapped and dropped by three offline adapters) is "
                         "regression-tested through the dispositions of every adapter",
    "residual": "visibility is pull-based (a reader opens the store or the report); a store that cannot be "
                "written at all is recorded in the session and reported by the tool, and nowhere else",
    "verdict": "SHADOW_FAILURE_VISIBILITY_VALIDATED",
}

# -- P3-151: the synthetic-parameter sensitivity audit ------------------------------------------------------------

MATERIALITY = ("causal direction", "temporal ordering", "READY verdict", "boundary", "region intersection",
               "live-versus-offline equivalence")
SENSITIVITY_VERDICTS = ("ENSEMBLE_REQUIRED", "SENSITIVITY_NON_MATERIAL_FOR_CURRENT_VERDICT",
                        "SYNTHETIC_ONLY_NO_DEFENSIBLE_REGION")

SENSITIVITY = {
    "package": "P3-151",
    "method": "read-only and computational: the six-arm opioid series at the three transmission witnesses, "
              "offline, with one synthetic parameter moved at a time on a development adapter; the registered "
              "adapter, the committed profile and the core are not touched",
    "ranges_used": "only values the repository already holds; none is invented",
    "parameters": {
        "arrival_bands": {
            "values": ("lower", "midpoint", "upper"),
            "source": "the declared points of the certified opioid reference mapping (no value selected there)",
            "interval_is_defensible": True,
            "finding": "the untreated chain and the derived region bound are the same at the three points to "
                       "floating-point roundoff (the point cancels in the composition); every verdict is the "
                       "same at the three points; only the treated magnitudes move",
            "verdict": "SENSITIVITY_NON_MATERIAL_FOR_CURRENT_VERDICT",
        },
        "opioid_recovery_rate": {
            "values": (0.10, 0.5, 0.9),
            "source": "the committed point and two structural probes of the certified opioid tests; the "
                      "repository declares no interval for it",
            "interval_is_defensible": False,
            "finding": "at the values the repository holds every verdict is unchanged and the region bound does "
                       "not read it; no claim is made between or beyond those values",
            "verdict": "SYNTHETIC_ONLY_NO_DEFENSIBLE_REGION",
        },
        "opioid_deepening_rate": {
            "values": (0.005, 0.02, 0.03),
            "source": "the committed point, the recurrence probe and the structural collapse-direction probe; "
                      "the adapter's own provenance says no span is declared",
            "interval_is_defensible": False,
            "finding": "the transmission region's upper bound is CONDITIONAL on this rate: it is inversely "
                       "proportional to the untreated carbon-dioxide rise the rate produces, and at the two "
                       "probe values every witness lies outside the bound and oxygen's specificity and "
                       "direction no longer hold at the upper witnesses; the direction and the timing of the "
                       "reversal hold at every value",
            "material_at_repository_probe_values": True,
            "verdict": "SYNTHETIC_ONLY_NO_DEFENSIBLE_REGION",
            "open_question": "FD-NEW-4 promotes a parameter whose uncertainty can change a boundary, and also "
                             "forbids inventing a range; this rate is material at the probe values and has no "
                             "declared interval. It is NOT promoted. Either the faculty declares an interval "
                             "(then it is ENSEMBLE_REQUIRED and the region is re-derived jointly) or the "
                             "region is read as valid at the committed rate only",
        },
    },
    "ensemble_dimensionality_changed": False,
    "region_statement": "the transmission region (0, 0.060621] is the region AT the committed deepening rate",
    "verdict": "SENSITIVITY_AUDITED_NO_PARAMETER_PROMOTED_ONE_DECISION_OPEN",
}

# -- P3-152: the oedema timing correction -------------------------------------------------------------------------

EDEMA_TIMING = {
    "package": "P3-152",
    "where": "the offline development oedema adapter only; the registered adapter still declares the gap",
    "before": "the decongestive treatment began at the order's own minute (floored at 1)",
    "after": "it begins the minute after its order: an order the engine executed at minute m is first present "
             "in the state of minute m + 1, as oxygen and the live opioid reversal already are",
    "magnitude_region_changed": False,
    "common_physiology_changed": False,
    "first_effect_minute": {"before": 30, "after": 31, "order_minute": 30},
    "back_to_arrival_minute": {"before": {"LOW": 79, "CENTER_REFERENCE": 55, "HIGH": 43},
                               "after": {"LOW": 81, "CENTER_REFERENCE": 57, "HIGH": 44}},
    "why_not_exactly_one_minute": "one more minute of untreated progression before the treatment begins adds "
                                  "lung water that the slower rates take a further minute to remove",
    "contract_verdicts_changed": False,
    "verdict": "PULMONARY_EDEMA_TIMING_CORRECTED_NO_VERDICT_CHANGE",
}

# -- P3-153: the integrated adversarial certification -------------------------------------------------------------

CERTIFICATION = {
    "package": "P3-153",
    "covers": ("GI live shadow", "opioid live shadow", "trace persistence", "replay", "session lifecycle",
               "failure visibility", "faculty observer isolation", "oedema offline timing"),
    "attacks": ("repeated initialization", "zero-minute turns", "duplicate actions", "unsupported actions",
                "action at the exact boundary", "replay after failure", "wrong-family trace", "stale lineage",
                "missing witness", "mutated arrival"),
    "randomized": "bounded and seeded: fixed seeds, a fixed pool of real order texts, a fixed number of "
                  "sequences per family; the same seeds give the same sequences",
    "isolation": ("legacy state identical with the shadow on and off", "scoring inputs identical",
                  "order destination identical", "resident-visible outputs identical",
                  "the common core has no runtime authority"),
    "also_with_the_store_on": True,
    "mutants": {"run": 35, "detected": 35},
    "independent_review": {
        "when": "on the uncommitted candidate, before the final certification; read-only",
        "held": ("isolation over 1,200 seeded sequences played off, on and on with the store (3,600 "
                 "encounters): authoritative record, state, fates, minute and arrest identical in all",
                 "lifecycle over 500 seeds and 962 attempts through one page helper without a reset: no "
                 "session mapped on a touched state, none kept across attempts after leaving arrival",
                 "the eligibility rule never raised on 790 malformed states",
                 "replay deterministic across three processes; the effective minute equal to the first "
                 "differing state minute in 32 of 32 cases",
                 "store boundaries, observer read-only and escaping, the oedema change being the begin minute "
                 "only, and no loosened adapted test"),
        "findings": {"MEDIUM": 5, "LOW": 12, "INFO": 2},
        "fixed": ("R1", "R2", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11", "R12", "R13", "R16", "R17",
                  "R19"),
        "fixed_in_part_and_declared": ("R3", "R14"),
        "declared": ("R15", "R18"),
    },
}

# -- P3-154: the nine gates, read again ---------------------------------------------------------------------------

GATES = (
    {"gate": "runtime exposure", "status": "BLOCKED", "before": "BLOCKED",
     "evidence": "unchanged: the shadow opens only behind a process flag a deployment secret cannot set, and "
                 "exposure needs authority, whose gate has no approved snapshot",
     "blocker": "no faculty-approved snapshot; authority is GI pressure only by design"},
    {"gate": "UI exposure", "status": "BLOCKED", "before": "BLOCKED",
     "evidence": "a faculty-only report now exists and it is not a resident screen: nothing a resident sees "
                 "renders a shadow record or a common-core reading, and a guard forbids the page to",
     "blocker": "nothing resident-facing is built or designed; a faculty observer does not make this green"},
    {"gate": "trace capture", "status": "GREEN", "before": "PARTIAL",
     "evidence": "a live shadow trace is persisted turn by turn in its own store, reloaded and replayed exactly "
                 "for GI and for the opioid's session run and three witnesses; a failed witness stays failed",
     "blocker": None,
     "scope": "faculty and development environments; a durable store for a deployed pilot is not designed"},
    {"gate": "scoring isolation", "status": "GREEN", "before": "GREEN",
     "evidence": "the authoritative record, the ledger and the order fates are identical with the shadow on and "
                 "off, with and without the store, for GI and for the opioid, under the randomized sequences",
     "blocker": None},
    {"gate": "faculty review workflow", "status": "PARTIAL", "before": "PARTIAL",
     "evidence": "a faculty reader can now open a persisted trace and see each witness apart, the actions with "
                 "their effective minutes, the failures and the replay",
     "blocker": "the report is a tool outside the app; it records no faculty decision; the open decisions of "
                "the earlier packs and this cycle's deepening-rate question stay open"},
    {"gate": "case selection", "status": "NOT_YET_EVALUATED", "before": "NOT_YET_EVALUATED",
     "evidence": "the first pilot is frozen and untouched; no case is selected for a later one",
     "blocker": "a faculty selection, after review"},
    {"gate": "failure visibility", "status": "GREEN", "before": "PARTIAL",
     "evidence": "every trace carries a structured status with seven distinct codes and no bare success; the "
                 "report and the listing show it; no executed action is dropped without a disposition",
     "blocker": None,
     "scope": "pull-based: a reader opens the store or the report; nothing alerts"},
    {"gate": "rollback", "status": "GREEN", "before": "GREEN",
     "evidence": "unset the flag and the encounter is exactly the engine; unset the store and nothing is "
                 "written; the family allowlist can only narrow",
     "blocker": None},
    {"gate": "resident-facing safety", "status": "BLOCKED", "before": "BLOCKED",
     "evidence": "nothing of the shadow reaches a resident, which is safe today; an exposure would show a "
                 "physiology with no terminal transition, no consciousness mapping and unapproved regions",
     "blocker": "the unset collapse and consciousness layers and the development regions"},
)

READINESS = {
    "SIMULATION_ENGINE_READINESS": {
        "verdict": "LIVE_SHADOW_OBSERVABLE_PERSISTENT_AND_REPLAYABLE_FOR_DEVELOPMENT",
        "holds": ("two families run in the live shadow with no authority and one shared arrival rule",
                  "a live trace persists, reloads and replays state for state, witness by witness",
                  "every failure is coded and no executed action disappears",
                  "the offline oedema adapter uses the layer's one timing rule"),
        "does_not_hold": ("no common-core physiology was added or changed", "ACS has no live arrival",
                          "the regions are development regions and the opioid region is conditional on a "
                          "synthetic rate with no declared interval",
                          "no terminal transition and no consciousness mapping"),
    },
    "FACULTY_REVIEW_READINESS": {
        "verdict": "READY_FOR_FACULTY_REVIEW_OF_SHADOW_TRACES_IN_DEVELOPMENT",
        "holds": ("a read-only report of any persisted trace", "LOW, CENTER_REFERENCE and HIGH shown apart",
                  "actions with order and effective minutes", "failures and replay shown on the same page"),
        "does_not_hold": ("it is a development tool, not a screen of the app",
                          "it captures no faculty decision", "no access control beyond who can run the tool"),
    },
    "RESIDENT_PILOT_DEPLOYMENT_READINESS": {
        "verdict": "NOT_READY_FOR_RESIDENT_PILOT_REVIEW",
        "gates": {"GREEN": 4, "PARTIAL": 1, "BLOCKED": 3, "NOT_YET_EVALUATED": 1},
        "moved_this_cycle": ("trace capture", "failure visibility"),
        "still_blocked": ("runtime exposure", "UI exposure", "resident-facing safety"),
    },
}

# -- P3-155: the roadmap ------------------------------------------------------------------------------------------

ROADMAP = {
    "package": "P3-155",
    "scale": "3 highest, 0 lowest, per criterion; architecture_cost and risk are costs (3 is the most costly)",
    "criteria": ("pilot_criticality", "architecture_cost", "educational_value", "risk"),
    "rank_rule": "pilot_criticality first (highest first), then architecture_cost + risk (lowest first), then "
                 "educational_value (highest first); the rank is not the path: the path below respects what "
                 "each blocker depends on",
    "blockers": (
        {"blocker": "open faculty decisions on what is now reviewable: the two development regions, the "
                    "synthetic rates (the deepening-rate interval above all) and the earlier packs",
         "pilot_criticality": 3, "architecture_cost": 0, "educational_value": 2, "risk": 0,
         "needs": "a faculty review session over persisted traces; no code"},
        {"blocker": "no resident-facing design for a common-core reading",
         "pilot_criticality": 3, "architecture_cost": 2, "educational_value": 3, "risk": 2,
         "needs": "a design decision after authority is decided; not before"},
        {"blocker": "no faculty-approved snapshot, so no authority and no runtime exposure",
         "pilot_criticality": 3, "architecture_cost": 1, "educational_value": 1, "risk": 3,
         "needs": "a faculty approval that depends on the two rows above"},
        {"blocker": "no terminal transition and no consciousness mapping in the common core",
         "pilot_criticality": 3, "architecture_cost": 3, "educational_value": 2, "risk": 3,
         "needs": "a common-core amendment, which this cycle was not authorized to make"},
        {"blocker": "no case selected for a later pilot",
         "pilot_criticality": 2, "architecture_cost": 0, "educational_value": 2, "risk": 0,
         "needs": "a faculty selection, informed by the review session"},
        {"blocker": "the faculty report is a tool outside the app and the store is a development directory",
         "pilot_criticality": 1, "architecture_cost": 2, "educational_value": 1, "risk": 1,
         "needs": "only if the faculty asks for an in-app review or a deployed store"},
        {"blocker": "ACS has no live arrival mapping",
         "pilot_criticality": 1, "architecture_cost": 2, "educational_value": 2, "risk": 2,
         "needs": "authored arrival semantics for six variants; not authorized, not on the critical path"},
        {"blocker": "more physiology families (asthma treatment, embolism)",
         "pilot_criticality": 0, "architecture_cost": 3, "educational_value": 2, "risk": 2,
         "needs": "new physiology; not on the critical path and not the assumed next step"},
    ),
    "shortest_critical_path": (
        "a faculty review of persisted GI and opioid traces with the report, to decide the regions and the "
        "synthetic rates (including whether the deepening rate gets an interval)",
        "a faculty decision on whether to authorize the terminal-transition and consciousness work in the "
        "common core, which is what resident-facing safety waits on",
        "only then the approved snapshot, authority and a resident-facing design",
    ),
    "next_step_is_another_physiology_family": False,
    "is_a_selection": False,
}

CHECKPOINT = {
    "engine_verdict": "LIVE_SHADOW_OBSERVABILITY_VALIDATED_FOR_DEVELOPMENT",
    "faculty_review_verdict": "READY_FOR_FACULTY_REVIEW_OF_SHADOW_TRACES_IN_DEVELOPMENT",
    "pilot_verdict": "NOT_READY_FOR_RESIDENT_PILOT_REVIEW",
    "not_claimed": ("clinical validation", "resident readiness", "a preferred transmission point",
                    "any change to the frozen first pilot", "any change to common physiology",
                    "any authority for the common core"),
}

# <measured>
MEASURED = {'sensitivity': {'configs': {'committed': {'region': {'spo2_60_at_f0': 80.0,
                                                      'delta_paco2_60': 24.210373,
                                                      'f_upper': 0.060621},
                                           'witnesses_inside_the_bound': ['LOW', 'CENTER_REFERENCE', 'HIGH'],
                                           'contract': {'DIRECTION': True,
                                                        'TEMPORALITY': True,
                                                        'CAUSAL_SPECIFICITY': True,
                                                        'MAGNITUDE_PLAUSIBILITY': True,
                                                        'DOSE_ORDERING': True,
                                                        'REVERSIBILITY': True,
                                                        'TIME_WITHOUT_ACTION': True,
                                                        'SAFETY': True},
                                           'endpoints': {'LOW': {'untreated_spo2': 79.221876,
                                                                 'reversal_spo2': 80.790915,
                                                                 'untreated_paco2': 108.335757},
                                                         'CENTER_REFERENCE': {'untreated_spo2': 78.409118,
                                                                              'reversal_spo2': 81.545898,
                                                                              'untreated_paco2': 108.335757},
                                                         'HIGH': {'untreated_spo2': 76.674013,
                                                                  'reversal_spo2': 82.954442,
                                                                  'untreated_paco2': 108.335757}},
                                           'verdicts_that_differ_from_committed': {'LOW': [],
                                                                                   'CENTER_REFERENCE': [],
                                                                                   'HIGH': []},
                                           'material': []},
                             'arrival_lower': {'region': {'spo2_60_at_f0': 80.0,
                                                          'delta_paco2_60': 24.210373,
                                                          'f_upper': 0.060621},
                                               'witnesses_inside_the_bound': ['LOW', 'CENTER_REFERENCE', 'HIGH'],
                                               'contract': {'DIRECTION': True,
                                                            'TEMPORALITY': True,
                                                            'CAUSAL_SPECIFICITY': True,
                                                            'MAGNITUDE_PLAUSIBILITY': True,
                                                            'DOSE_ORDERING': True,
                                                            'REVERSIBILITY': True,
                                                            'TIME_WITHOUT_ACTION': True,
                                                            'SAFETY': True},
                                               'endpoints': {'LOW': {'untreated_spo2': 79.221876,
                                                                     'reversal_spo2': 80.622747,
                                                                     'untreated_paco2': 108.335757},
                                                             'CENTER_REFERENCE': {'untreated_spo2': 78.409118,
                                                                                  'reversal_spo2': 81.223224,
                                                                                  'untreated_paco2': 108.335757},
                                                             'HIGH': {'untreated_spo2': 76.674013,
                                                                      'reversal_spo2': 82.360462,
                                                                      'untreated_paco2': 108.335757}},
                                               'verdicts_that_differ_from_committed': {'LOW': [],
                                                                                       'CENTER_REFERENCE': [],
                                                                                       'HIGH': []},
                                               'material': []},
                             'arrival_upper': {'region': {'spo2_60_at_f0': 80.0,
                                                          'delta_paco2_60': 24.210373,
                                                          'f_upper': 0.060621},
                                               'witnesses_inside_the_bound': ['LOW', 'CENTER_REFERENCE', 'HIGH'],
                                               'contract': {'DIRECTION': True,
                                                            'TEMPORALITY': True,
                                                            'CAUSAL_SPECIFICITY': True,
                                                            'MAGNITUDE_PLAUSIBILITY': True,
                                                            'DOSE_ORDERING': True,
                                                            'REVERSIBILITY': True,
                                                            'TIME_WITHOUT_ACTION': True,
                                                            'SAFETY': True},
                                               'endpoints': {'LOW': {'untreated_spo2': 79.221876,
                                                                     'reversal_spo2': 80.891014,
                                                                     'untreated_paco2': 108.335757},
                                                             'CENTER_REFERENCE': {'untreated_spo2': 78.409118,
                                                                                  'reversal_spo2': 81.736419,
                                                                                  'untreated_paco2': 108.335757},
                                                             'HIGH': {'untreated_spo2': 76.674013,
                                                                      'reversal_spo2': 83.29954,
                                                                      'untreated_paco2': 108.335757}},
                                               'verdicts_that_differ_from_committed': {'LOW': [],
                                                                                       'CENTER_REFERENCE': [],
                                                                                       'HIGH': []},
                                               'material': []},
                             'recovery_0.5': {'region': {'spo2_60_at_f0': 80.0,
                                                         'delta_paco2_60': 24.210373,
                                                         'f_upper': 0.060621},
                                              'witnesses_inside_the_bound': ['LOW', 'CENTER_REFERENCE', 'HIGH'],
                                              'contract': {'DIRECTION': True,
                                                           'TEMPORALITY': True,
                                                           'CAUSAL_SPECIFICITY': True,
                                                           'MAGNITUDE_PLAUSIBILITY': True,
                                                           'DOSE_ORDERING': True,
                                                           'REVERSIBILITY': True,
                                                           'TIME_WITHOUT_ACTION': True,
                                                           'SAFETY': True},
                                              'endpoints': {'LOW': {'untreated_spo2': 79.221876,
                                                                    'reversal_spo2': 80.810162,
                                                                    'untreated_paco2': 108.335757},
                                                            'CENTER_REFERENCE': {'untreated_spo2': 78.409118,
                                                                                 'reversal_spo2': 81.582621,
                                                                                 'untreated_paco2': 108.335757},
                                                            'HIGH': {'untreated_spo2': 76.674013,
                                                                     'reversal_spo2': 83.021285,
                                                                     'untreated_paco2': 108.335757}},
                                              'verdicts_that_differ_from_committed': {'LOW': [],
                                                                                      'CENTER_REFERENCE': [],
                                                                                      'HIGH': []},
                                              'material': []},
                             'recovery_0.9': {'region': {'spo2_60_at_f0': 80.0,
                                                         'delta_paco2_60': 24.210373,
                                                         'f_upper': 0.060621},
                                              'witnesses_inside_the_bound': ['LOW', 'CENTER_REFERENCE', 'HIGH'],
                                              'contract': {'DIRECTION': True,
                                                           'TEMPORALITY': True,
                                                           'CAUSAL_SPECIFICITY': True,
                                                           'MAGNITUDE_PLAUSIBILITY': True,
                                                           'DOSE_ORDERING': True,
                                                           'REVERSIBILITY': True,
                                                           'TIME_WITHOUT_ACTION': True,
                                                           'SAFETY': True},
                                              'endpoints': {'LOW': {'untreated_spo2': 79.221876,
                                                                    'reversal_spo2': 80.812284,
                                                                    'untreated_paco2': 108.335757},
                                                            'CENTER_REFERENCE': {'untreated_spo2': 78.409118,
                                                                                 'reversal_spo2': 81.586667,
                                                                                 'untreated_paco2': 108.335757},
                                                            'HIGH': {'untreated_spo2': 76.674013,
                                                                     'reversal_spo2': 83.02864,
                                                                     'untreated_paco2': 108.335757}},
                                              'verdicts_that_differ_from_committed': {'LOW': [],
                                                                                      'CENTER_REFERENCE': [],
                                                                                      'HIGH': []},
                                              'material': []},
                             'deepening_0.02': {'region': {'spo2_60_at_f0': 80.0,
                                                           'delta_paco2_60': 162.89135,
                                                           'f_upper': 0.00901},
                                                'witnesses_inside_the_bound': [],
                                                'contract': {'DIRECTION': True,
                                                             'TEMPORALITY': True,
                                                             'CAUSAL_SPECIFICITY': True,
                                                             'MAGNITUDE_PLAUSIBILITY': True,
                                                             'DOSE_ORDERING': True,
                                                             'REVERSIBILITY': True,
                                                             'TIME_WITHOUT_ACTION': True,
                                                             'SAFETY': True},
                                                'endpoints': {'LOW': {'untreated_spo2': 71.570973,
                                                                      'reversal_spo2': 80.719141,
                                                                      'untreated_paco2': 425.110937},
                                                              'CENTER_REFERENCE': {'untreated_spo2': 59.435117,
                                                                                   'reversal_spo2': 81.408578,
                                                                                   'untreated_paco2': 425.110937},
                                                              'HIGH': {'untreated_spo2': 26.160615,
                                                                       'reversal_spo2': 82.703126,
                                                                       'untreated_paco2': 422.604796}},
                                                'verdicts_that_differ_from_committed': {'LOW': [],
                                                                                        'CENTER_REFERENCE': [],
                                                                                        'HIGH': ['oxygen_leaves_ventilation']},
                                                'material': ['causal direction', 'region intersection']},
                             'deepening_0.03': {'region': {'spo2_60_at_f0': 80.0,
                                                           'delta_paco2_60': 360.086682,
                                                           'f_upper': 0.004076},
                                                'witnesses_inside_the_bound': [],
                                                'contract': {'DIRECTION': True,
                                                             'TEMPORALITY': True,
                                                             'CAUSAL_SPECIFICITY': True,
                                                             'MAGNITUDE_PLAUSIBILITY': True,
                                                             'DOSE_ORDERING': True,
                                                             'REVERSIBILITY': True,
                                                             'TIME_WITHOUT_ACTION': True,
                                                             'SAFETY': True},
                                                'endpoints': {'LOW': {'untreated_spo2': 46.669125,
                                                                      'reversal_spo2': 80.671088,
                                                                      'untreated_paco2': 1070.022739},
                                                              'CENTER_REFERENCE': {'untreated_spo2': 10.040296,
                                                                                   'reversal_spo2': 81.316311,
                                                                                   'untreated_paco2': 977.231108},
                                                              'HIGH': {'untreated_spo2': 0.0,
                                                                       'reversal_spo2': 82.533046,
                                                                       'untreated_paco2': 776.520249}},
                                                'verdicts_that_differ_from_committed': {'LOW': [],
                                                                                        'CENTER_REFERENCE': ['oxygen_leaves_ventilation'],
                                                                                        'HIGH': ['oxygen_leaves_ventilation',
                                                                                                 'oxygen_raises_saturation',
                                                                                                 'saturation_reached_its_floor']},
                                                'material': ['causal direction', 'boundary', 'region intersection']}},
                 'committed_verdicts': {'LOW': {'untreated_downhill': True,
                                                'reversal_direction': True,
                                                'reversal_first_effect_minute': 21,
                                                'no_effect_before_activation': True,
                                                'oxygen_raises_saturation': True,
                                                'oxygen_leaves_ventilation': True,
                                                'early_beats_late': True,
                                                'waiting_is_not_a_treatment': True,
                                                'replays': True,
                                                'no_run_failed': True,
                                                'saturation_reached_its_floor': False},
                                        'CENTER_REFERENCE': {'untreated_downhill': True,
                                                             'reversal_direction': True,
                                                             'reversal_first_effect_minute': 21,
                                                             'no_effect_before_activation': True,
                                                             'oxygen_raises_saturation': True,
                                                             'oxygen_leaves_ventilation': True,
                                                             'early_beats_late': True,
                                                             'waiting_is_not_a_treatment': True,
                                                             'replays': True,
                                                             'no_run_failed': True,
                                                             'saturation_reached_its_floor': False},
                                        'HIGH': {'untreated_downhill': True,
                                                 'reversal_direction': True,
                                                 'reversal_first_effect_minute': 21,
                                                 'no_effect_before_activation': True,
                                                 'oxygen_raises_saturation': True,
                                                 'oxygen_leaves_ventilation': True,
                                                 'early_beats_late': True,
                                                 'waiting_is_not_a_treatment': True,
                                                 'replays': True,
                                                 'no_run_failed': True,
                                                 'saturation_reached_its_floor': False}},
                 'bound_elasticity_to_the_deepening_rate': -1.160926}}
# </measured>


def all_records() -> dict:
    return {"status": STATUS, "cycle": CYCLE, "faculty_decisions": FACULTY_DECISIONS, "lifecycle": LIFECYCLE,
            "trace_store": TRACE_STORE, "observer": OBSERVER, "failure_visibility": FAILURE_VISIBILITY,
            "materiality": MATERIALITY, "sensitivity": SENSITIVITY, "edema_timing": EDEMA_TIMING,
            "certification": CERTIFICATION, "gates": GATES, "readiness": READINESS, "roadmap": ROADMAP,
            "checkpoint": CHECKPOINT, "measured": MEASURED}
