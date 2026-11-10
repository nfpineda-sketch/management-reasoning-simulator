"""Second live-shadow family (2026-11-10): the record of the cycle. Pure data.

What this cycle asked: whether a second, mechanistically distinct family can run in the real Phase-3 live
shadow -- real arrival, real actions, real timing, a region instead of a point, replay, visible failure and
no authority -- and the faculty decisions that preceded it. Every figure in ``MEASURED`` is recomputed by
``test_indirect_feedback_audit.py`` and ``test_opioid_live_shadow.py``.

Nothing here is a default, a calibration, a clinical value or a recommendation. The regions are
DEVELOPMENT_TEST_REGION; the witnesses exist to test with; the live shadow has no authority and is invisible
to the resident and to the score.

Numbering. The request numbers this cycle's packages P3-137 to P3-146. The previous cycle had used P3-137 to
P3-144 as its own labels for other packages (``management_generalization_record``). Neither is rewritten:
this cycle's code and tests carry an ``L`` (``p3l``), and the documents say which cycle a number belongs to.
"""

STATUS = "SECOND_FAMILY_LIVE_SHADOW_DEVELOPMENT_NO_AUTHORITY"
CYCLE = "second live family, 2026-11-10 (request packages P3-137 to P3-146; code label p3l)"
STARTING_HEAD = "39dee5229bbdd9123c95c84d06afa0d765a6f2a0"

# -- P3-137: the faculty decisions of 2026-11-10 -----------------------------------------------------------------

FACULTY_DECISIONS = {
    "FD-NEW-1": {
        "decision_file": "FD-P3-129",
        "quantity": "hypoventilation_oxygenation_transmission_fraction, respiratory quotient declared 0.8",
        "mathematical_development_region": (0.0, 0.060621),
        "active_causal_development_region": {"above": 0.0, "up_to": 0.060621},
        "why_two_regions": "a fraction of 0 is a negative control: it is representable and it expresses nothing "
                           "downstream of PaCO2, so it cannot show the chain ventilation -> PaCO2 -> oxygenation",
        "witnesses": {"LOW": 0.015, "CENTER_REFERENCE": 0.03, "HIGH": 0.06},
        "witnesses_are": "TEST_WITNESSES_ONLY",
        "center_reference_is_preferred": False,
        "a_committed_profile_adopts_one": False,
        "classification": "DEVELOPMENT_TEST_REGION",
        "confidence": 0.84,
    },
    "FD-NEW-2": {
        "decision_file": "FD-P3-129",
        "quantity": "pulmonary oedema decongestion_per_min",
        "region": (0.0025, 0.01),
        "classification": "DEVELOPMENT_TEST_REGION",
        "confidence": 0.82,
        "purpose": "to demonstrate simulation management causality",
        "is_not": ("a clinical calibration", "real-world dosing guidance", "a production value"),
    },
    "FD-NEW-3": {"decision_file": "FD-P3-130", "see": "ASTHMA_SUPERSESSION"},
    "FD-NEW-4": {
        "decision_file": "FD-P3-129",
        "rule": "the witnesses are not ordinary opioid or asthma adapter defaults; where a live shadow needs the "
                "parameter realized it runs a region-aware ensemble and never silently selects CENTER_REFERENCE",
        "resolves": "FD-P3-128 (b)",
    },
    "FD-NEW-5": {
        "decision_file": "FD-P3-129",
        "rule": "no live-arrival mapping is invented for ACS in this cycle",
        "acs_verdict_stands": "ACS_ARRIVAL_MAPPING_REQUIRES_NEW_SEMANTICS",
        "acs_offline": "CAUSALLY_READY",
    },
    "FD-NEW-6": {
        "decision_file": "FD-P3-129",
        "not_implemented_in_this_cycle": ("asthma bronchodilator writer", "embolism treatment mechanism", "NIV",
                                          "antiplatelet or anticoagulation physiology", "new common physiology"),
    },
    "FD-NEW-7": {
        "decision_file": "FD-P3-129",
        "rule": "the project instructions distinguish the HISTORICAL Phase-2 closure from the CURRENT certified "
                "common-core successor; the historical closure identity is neither replaced nor erased",
        "resolves": ("TD-131 (8)", "TD-132 (6)", "FD-P3-128 (f)"),
    },
}

#: The development milestone the decisions stand on. It is NOT live readiness.
MILESTONE = {
    "name": "MULTIFAMILY_MANAGEMENT_CAUSALITY_VALIDATED_FOR_DEVELOPMENT",
    "pathways": {
        "gi_bleed": {"mechanism": "V / volume loss", "status": "CAUSALLY_READY", "where": "live shadow"},
        "acs": {"mechanism": "P / reperfusion", "status": "CAUSALLY_READY", "where": "OFFLINE"},
        "opioid": {"mechanism": "central availability / ventilation", "status": "READY_WITH_REGION",
                   "where": "live shadow since this cycle"},
        "pulmonary_edema": {"mechanism": "L / decongestion", "status": "READY_WITH_REGION", "where": "OFFLINE"},
    },
    "implies_live_runtime_readiness": False,
    "implies_resident_readiness": False,
    "is_clinical_validation": False,
}

# -- P3-137A: the three P2S-3 probes ------------------------------------------------------------------------------

ASTHMA_SUPERSESSION = {
    "status": "SUPERSEDED_WHERE_THEY_CONFLICT_NOT_DELETED",
    "historical_freeze_records_modified": False,
    "what_changed": "PHASE2_AMENDMENT_1 certified that ventilation reaches oxygenation through PaCO2; a P2S-3 "
                    "condition that required saturation, and what reads it, to stay still while ventilation "
                    "moved is true only where the link expresses nothing",
    "probes": (
        {
            "probe": "untreated",
            "historical_purpose": "an untreated airway obstruction worsens through the mechanics and nothing "
                                  "else: efficiency down, ventilation down, PaCO2 up, pH down",
            "old_expectation": "only_mechanics_moves: RR, SpO2, G, L, D, lactate, HR, the delivery index, the "
                               "consciousness level and MAP identical to the same case without worsening, and "
                               "every state field but the mechanics identical",
            "conditions_superseded": ("spo2", "hr", "delivery_index", "states_identical_but_mechanics"),
            "why_the_certified_amendment_changes_it": "with a non-zero share the rising PaCO2 lowers the "
                                                      "saturation; the delivery index is proportional to it, "
                                                      "and the heart rate reads it through the certified "
                                                      "hypoxaemia term of the sympathetic drive, which is state",
            "new_causal_invariant": "mechanics -> ventilation -> PaCO2 -> oxygenation, in that direction and by "
                                    "no other path: RR, G, L, D, lactate, consciousness and MAP still identical; "
                                    "the saturation equals the certified equation applied to the PaCO2 exactly; "
                                    "the delivery index moves only in proportion to it; at a share of 0 the old "
                                    "condition holds in full",
            "historical_evidence_still_reproducible": "on the committed asthma profile, where the link is not "
                                                      "declared, the probe passes with every condition true",
        },
        {
            "probe": "relief",
            "historical_purpose": "a relief of the mechanics is representable through the common mechanics "
                                  "target: it raises ventilation and lowers PaCO2",
            "old_expectation": "rr_spo2_hr_unchanged: RR, SpO2 and HR identical with and without the relief",
            "conditions_superseded": ("rr_spo2_hr_unchanged",),
            "why_the_certified_amendment_changes_it": "the falling PaCO2 raises the saturation, and the heart "
                                                      "rate follows it; the RR is still unchanged",
            "new_causal_invariant": "relief raises W, lowers PaCO2 and leaves RR identical; the saturation is "
                                    "never lower than without relief, in any minute, and is higher once the "
                                    "relief has acted; nothing moves before it begins; the gain is 0 at a share "
                                    "of 0 and ordered by the share",
            "historical_evidence_still_reproducible": "on the committed asthma profile the probe passes",
        },
        {
            "probe": "heart_rate",
            "historical_purpose": "the asthma profile adds no gain of its own: the arrival heart-rate gap is "
                                  "carried forward, not patched",
            "old_expectation": "gains_untouched: every profile field equals the common reference profile except "
                               "the declared reference fields and the mechanics switch",
            "conditions_superseded": ("gains_untouched",),
            "why_the_certified_amendment_changes_it": "a profile that declares the link differs from the common "
                                                      "reference in the two link fields; neither is a gain",
            "new_causal_invariant": "a witness profile differs from the committed asthma profile in exactly the "
                                    "respiratory quotient and the transmission fraction, and the arrival "
                                    "heart-rate decomposition is unchanged by the link",
            "historical_evidence_still_reproducible": "on the committed asthma profile the probe passes",
        },
    ),
    "not_superseded": ("arrival", "writer_semantics", "oxygen", "direct_g", "collapse", "consciousness"),
    "refused_by_the_core": {"drive": "HYPOXEMIC_FEEDBACK_LOOP_DEFERRED: a hypoxaemic drive is not declarable "
                                     "together with the link"},
}

# -- P3-138: the indirect feedback loop of TD-130 (40) ------------------------------------------------------------

FEEDBACK_GRAPH = {
    "critical_delivery_index": 0.4,
    "edges": (
        {"id": "E01", "from": "SpO2", "to": "delivery", "sign": "+", "classes": ("ALWAYS_ACTIVE",),
         "source": "derived.relative_delivery: output x (Hb / Hb_a) x (SpO2 / SpO2_a); linear, same minute"},
        {"id": "E02", "from": "delivery", "to": "deficit", "sign": "-", "classes": ("THRESHOLDED",),
         "source": "derived.effective_oxygen_deficit: max(0, demand - reserve x delivery); 0 while the delivery "
                   "index is above demand / reserve (0.4 with the extraction reserve 2.5)"},
        {"id": "E03", "from": "deficit", "to": "acid burden", "sign": "+", "classes": ("DELAYED", "THRESHOLDED"),
         "source": "integration._acid_burden: dA = gain x deficit - A / tau, on the delivery of the START of the "
                   "minute; a leaky accumulator, one minute late"},
        {"id": "E04", "from": "acid burden", "to": "drive", "sign": "+", "classes": ("ALWAYS_ACTIVE",),
         "source": "derived.respiratory_drive: gain x burden"},
        {"id": "E05", "from": "drive", "to": "RR", "sign": "+", "classes": ("SATURATING", "CASE_DEPENDENT"),
         "source": "derived.rate_from_drive: intrinsic + S (1 - exp(-drive / S)), capped at rr_max, then times "
                   "the central availability the family writes"},
        {"id": "E06", "from": "RR", "to": "W", "sign": "+", "classes": ("ALWAYS_ACTIVE", "CASE_DEPENDENT"),
         "source": "derived.alveolar_ventilation: efficiency x RR / intrinsic / demand ratio"},
        {"id": "E07", "from": "W", "to": "PaCO2", "sign": "-", "classes": ("ALWAYS_ACTIVE",),
         "source": "derived.respiration: reference / W; undefined at W = 0 (the apnoea boundary is unresolved)"},
        {"id": "E08", "from": "PaCO2", "to": "SpO2", "sign": "-", "classes": ("ALWAYS_ACTIVE", "SATURATING"),
         "source": "derived.ventilated_oxygenation: PaO2 moved by -share x dPaCO2 / R through the dissociation "
                   "relation; nothing at a share of 0"},
        {"id": "E09", "from": "SpO2", "to": "hypoxaemic drive", "sign": "+", "classes": ("DISABLED",),
         "source": "CoreProfile: declaring the hypoxaemic drive with the link raises "
                   "HYPOXEMIC_FEEDBACK_LOOP_DEFERRED; the DIRECT loop cannot exist"},
        {"id": "E10", "from": "deficit", "to": "D", "sign": "+", "classes": ("DELAYED", "THRESHOLDED"),
         "source": "integration._oxygen_debt: an accumulator with no repayment while a deficit lasts; D feeds the "
                   "sympathetic drive and the lactate reading, not the respiration"},
        {"id": "E11", "from": "deficit", "to": "T", "sign": "+", "classes": ("DELAYED", "THRESHOLDED"),
         "source": "derived.tone_target (P2J-2): 1 + gain x deficit / demand; raises afterload, lowers output "
                   "and delivery: a POSITIVE branch that predates the link and shares its gate"},
        {"id": "E12", "from": "SpO2", "to": "sympathetic drive", "sign": "+", "classes": ("THRESHOLDED",),
         "source": "derived.sympathetic_target: the hypoxaemia term below its threshold, relative to arrival; it "
                   "ends in the heart-rate reading and feeds nothing back (the rate is not in the output)"},
    ),
    "respiratory_loop": ("E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08"),
    "respiratory_loop_sign": "NEGATIVE_FEEDBACK",
    "tone_branch": ("E01", "E02", "E11"),
    "tone_branch_sign": "POSITIVE_FEEDBACK",
    "loop_sign_when_active": "MIXED",
    "loop_sign_reading": "negative through ventilation, with a one-step multiplier of the acid accumulator "
                         "between 0 and 1 (monotone: no alternation, no divergence), plus a small positive "
                         "branch through tone whose one-step gain stays below 0.2; the monotone worsening seen "
                         "when the loop is active is driven by the family's own exogenous writer, not by the "
                         "loop",
    "when_it_can_close": "only while the effective deficit is above 0, that is while the delivery index is "
                         "below 0.4; every edge downstream of that gate is then active, one minute late",
}

FEEDBACK_VERDICT = {
    "verdict": "A_INDIRECT_FEEDBACK_SAFE_FOR_DEVELOPMENT_REGION",
    "closes": "TD-130 (40)",
    "stops_opioid_live_activation": False,
    "additional_region_restriction": None,
    "horizon_audited_min": 240,
    "rests_on": (
        "inside the region and up to 240 minutes the gate never opens in any of the four cases: the lowest "
        "delivery index is 0.773 against a critical 0.4, and every loop state is bit-identical to the negative "
        "control",
        "the smallest fraction that opens the gate within 240 minutes is 0.1209, twice the region's upper "
        "bound; within 60 minutes it is 0.80",
        "at the upper bound the gate does open in an untreated opioid course, but not before minute 346, and "
        "the loop is then monotone: no oscillation, no chatter",
        "forced active outside the region, the ventilatory branch is negative feedback and the tone branch a "
        "bounded positive one",
    ),
    "is_not": "not clinical validation; not a statement about a profile that declares other readers",
    "limit": "beyond the gate an untreated course keeps worsening without bound because no terminal transition "
             "is declared in these profiles: that is the family writer and the unset collapse layer, not the "
             "loop",
}

# -- P3-139: the opioid live-arrival mapping ----------------------------------------------------------------------

ARRIVAL_MAPPING = {
    "question": "can a live opioid encounter be mapped to the certified common-core state with existing semantics",
    "verdict": "OPIOID_LIVE_ARRIVAL_MAPPING_REUSES_EXISTING_SEMANTICS",
    "condition": "the live arrival must BE the authored case: every authored input the certified mapping reads "
                 "is compared with the live state before anything runs, and one difference refuses the run",
    "why_not_acs": "the engine authors six ACS variants and the adapter certifies one, so five live ACS arrivals "
                   "have no certified source at all; the engine authors two opioid variants and the adapter "
                   "certifies those two",
    "variants_authored_by_the_engine": ("opioid_35m", "opioid_67f"),
    "variants_certified_by_the_adapter": ("opioid_35m", "opioid_67f"),
    "sources": {
        "sbp": "DIRECT_FROM_LIVE_STATE", "dbp": "DIRECT_FROM_LIVE_STATE", "hr": "DIRECT_FROM_LIVE_STATE",
        "spo2": "DIRECT_FROM_LIVE_STATE", "respiratory_rate": "DIRECT_FROM_LIVE_STATE",
        "crt_s": "DIRECT_FROM_LIVE_STATE", "rhythm": "DIRECT_FROM_LIVE_STATE",
        "consciousness_level": "DIRECT_FROM_LIVE_STATE", "glucose": "DIRECT_FROM_LIVE_STATE",
        "lactate": "DIRECT_FROM_LIVE_STATE", "hb": "DIRECT_FROM_LIVE_STATE", "fio2": "DIRECT_FROM_LIVE_STATE",
        "k": "FIXED_AUTHORED_CASE_ANCHOR", "arrival_bicarbonate": "FIXED_AUTHORED_CASE_ANCHOR",
        "arrival_paco2": "FIXED_AUTHORED_CASE_ANCHOR",
        "V": "FIXED_AUTHORED_CASE_ANCHOR", "P": "FIXED_AUTHORED_CASE_ANCHOR", "T": "FIXED_AUTHORED_CASE_ANCHOR",
        "L": "FIXED_AUTHORED_CASE_ANCHOR", "G": "FIXED_AUTHORED_CASE_ANCHOR", "D": "FIXED_AUTHORED_CASE_ANCHOR",
        "intrinsic_respiratory_rate": "CERTIFIED_EXISTING_MAPPING",
        "arrival_central_availability": "CERTIFIED_EXISTING_MAPPING",
        "arrival_mechanics_efficiency": "CERTIFIED_EXISTING_MAPPING",
        "arrival_lactate_excess": "CERTIFIED_EXISTING_MAPPING",
        "intrinsic_sinus_rate": "CERTIFIED_EXISTING_MAPPING",
        "oxygen_action": "DIRECT_FROM_LIVE_STATE", "naloxone_action_and_minute": "DIRECT_FROM_LIVE_STATE",
        "wait_and_delay": "DIRECT_FROM_LIVE_STATE",
    },
    "identity_checked_live": {
        "the_case": ("sbp", "dbp", "hr", "rhythm", "spo2", "respiratory_rate", "crt_s", "mental_status",
                     "glucose_mg_dl", "lactate_mmol_l", "hb_g_dl", "potassium_mmol_l", "abg_paco2", "abg_hco3",
                     "abg_fio2_percent"),
        "the_arrival_as_shown": ("sbp", "dbp", "hr", "rhythm", "spo2", "respiratory_rate", "crt", "mental_status",
                                 "glucose_mg_dl"),
        "nothing_yet": "the clock at 0, no medication given, and every field of the engine's state for this "
                       "patient equal to a fresh initialization of the same case",
        "against_the_anchors": ("case_id", "lactate", "hb", "fio2"),
    },
    "notes": {
        "DIRECT_FROM_LIVE_STATE": "read on the live arrival and equal to the authored case, which the check proves "
                                  "for each encounter",
        "FIXED_AUTHORED_CASE_ANCHOR": "authored in the live state's own case (the blood gas, the potassium) or "
                                      "authored neutral (clear lungs, preserved perfusion)",
        "CERTIFIED_EXISTING_MAPPING": "P2U-1's frozen mapping of authored values: the latent arrival availability "
                                      "and efficiency are analytic in the authored RR, PaCO2 and bicarbonate at "
                                      "the carried intrinsic RR; the lactate excess and the intrinsic sinus rate "
                                      "follow the GI reference rule and stay declared synthetic_probe, which "
                                      "blocks a migration and not a shadow",
    },
    "missing_or_synthetic": {
        "REQUIRED_RUNTIME_INPUTS_MISSING": (),
        "REQUIRED_RUNTIME_INPUTS_SYNTHETIC_ONLY": (),
        "model_parameters_synthetic_only": {
            "opioid deepening rate": "0.005 per minute, a committed point with no span (SYNTHETIC_ONLY)",
            "naloxone recovery rate": "0.10 per minute, kinetics UNSET (SYNTHETIC_ONLY)",
            "respiratory quotient": "0.8, declared for this development analysis",
            "transmission fraction": "a DEVELOPMENT_TEST_REGION, run as an ensemble",
        },
        "bands_read_at_their_committed_point": {
            "intrinsic respiratory rate": "16 of the carried 12 / 16 / 20; the band is not explored live",
            "arrival lactate excess, intrinsic sinus rate": "the midpoint of a band built by an existing rule",
        },
        "carried_by_the_action_and_not_read": {"naloxone": ("dose_mg", "route")},
        "actions_with_no_core_contributor": ("naloxone_infusion", "bag_mask", "niv", "intubation",
                                             "opioid_analgesia", "a repeat naloxone dose"),
        "not_represented": ("the long-acting recurrence of opioid_67f", "withdrawal from an excess dose",
                            "any terminal transition"),
    },
}

# -- P3-140 and P3-141: the ensemble and the wiring ---------------------------------------------------------------

ENSEMBLE = {
    "witnesses": {"LOW": 0.015, "CENTER_REFERENCE": 0.03, "HIGH": 0.06},
    "negative_control": "the session's own run: the committed opioid profile, where the link is not declared, "
                        "state for state the run of a fraction of 0; it is not an ensemble witness",
    "each_witness_receives_the_same": ("arrival", "action sequence", "action timing", "exogenous writers",
                                       "execution primitive"),
    "witnesses_differ_only_in": "hypoventilation_oxygenation_transmission_fraction",
    "output": "each witness kept whole as its own trajectory, with its own replay artifact; a per-minute minimum "
              "and maximum beside the three values is a derived view",
    "averaged": False,
    "selected_witness": None,
    "fails_closed_on": "the core lineage: no witness opens unless the live core is a certified member",
    "authority": "none",
}

LIVE_WIRING = {
    "live_families": ("gi_bleed", "opioid"),
    "common_core_runtime_authority": False,
    "the_tuple_is_read_by": "the function that decides whether a shadow session opens, and nothing else",
    "adapter": "opioid/P3-141L",
    "action_mapping": {
        "oxygen": "the certified oxygen contributor, at the engine's minute, with the FiO2 the engine set",
        "stop oxygen": "the same contributor with the FiO2 the engine returned to",
        "naloxone": "the certified reversal, starting at the engine's minute + 1",
        "reassessment": "no physiology: skipped, never a gap",
        "a repeat naloxone dose": "declared gap: the reversal already began",
        "naloxone_infusion": "declared gap", "bag_mask": "declared gap", "niv": "declared gap",
        "intubation": "declared gap", "opioid_analgesia": "declared gap",
        "anything else": "declared gap: no core intervention for this order type",
    },
    "defects_found_and_corrected": (
        {"id": "L1", "what": "the reversal was mapped at the engine's own minute, so an order placed at minute m "
                             "changed the state of minute m, which the live run had already recorded: a late "
                             "order made the live run and its replay disagree from that minute",
         "fix": "the reversal starts at minute m + 1, where oxygen's effect already landed",
         "also_moves": "the previous cycle's offline naloxone figures by one minute; no verdict changes"},
        {"id": "L2", "what": "a second naloxone order built a second contributor with the same source and the "
                             "core refused the whole run",
         "fix": "one reversal begins once; a repeat dose is a declared gap"},
        {"id": "L3", "what": "an arrival the adapter refused left the session record empty with no reason in it",
         "fix": "the refusal is copied into the session's failures"},
        {"id": "L4", "what": "every difference from the engine was labelled an unexpected structural divergence "
                             "for a family that has no committed golden to say what is expected",
         "fix": "such a family's differences are NOT_COMPARABLE with the reason; the two safety readings stay "
                "loud"},
        {"id": "L5", "what": "a non-GI artifact named the GI adapter's version",
         "fix": "the family's versions name its own adapter; a GI artifact is unchanged"},
    ),
    "new_guard": "a run whose contributors would change a minute it already recorded stops and says so "
                 "(HistoryRewritten)",
    "independent_review": {
        "scope": "read-only, adversarial, on the candidate before it was committed: 1,000 fuzzed opioid and 500 "
                 "fuzzed GI encounters, 44 scripted GI scenarios against the previous modules, fault injection",
        "held": ("the authoritative state, ledger and entries are identical with the shadow on and off in "
                 "every encounter, and nothing raised into one",
                 "GI: the same record keys, minutes, classes, gaps and digests as before",
                 "live equals replay for the session run and every witness",
                 "no witness is preferred, averaged or carried by the registered adapter",
                 "the first changed shadow minute is always the order minute + 1"),
        "found_and_corrected": (
            {"id": "R1", "severity": "MEDIUM",
             "what": "the arrival identity read the engine's stored baseline and never the monitor or the "
                     "engine's treatment state: after a turn that takes zero minutes the page reopens the "
                     "session at minute 0, and an already-treated patient passed as the arrival, with the "
                     "action and its declared gap lost in the discarded session",
             "fix": "the identity now asks three things -- the case, the arrival as shown, and nothing given "
                    "yet (the engine's state equal to a fresh initialization, field by field) -- so that "
                    "session is refused, with the reason"},
            {"id": "R2", "severity": "LOW",
             "what": "a family that is supposed to have a golden and lost it would have gone quiet",
             "fix": "only a family declared without a golden is NOT_COMPARABLE; GI keeps the loud class"},
            {"id": "R3", "severity": "LOW",
             "what": "a comparison that raised left minutes recorded and the clock behind, and the history "
                     "guard then refused a run nothing had rewritten (fault injection only)",
             "fix": "the minutes and the clock move together; a failed comparison is recorded and the minute "
                    "stays, not compared"},
            {"id": "R4", "severity": "LOW",
             "what": "the opioid record named the Phase-2 default profile as its parameter snapshot",
             "fix": "a non-GI record names its own committed snapshot"},
            {"id": "R6", "severity": "LOW",
             "what": "with oxygen on every witness reaches the same states, so a replay check on state digests "
                     "could not tell one witness from another",
             "fix": "each recorded and replayed minute carries the digest of its readings too"},
            {"id": "R7", "severity": "LOW",
             "what": "the session record raised if the session run's mapping failed outright",
             "fix": "the record carries the failure instead"},
        ),
        "found_and_declared": (
            {"id": "R5", "what": "the lineage gate is at the live ensemble; a witness adapter opened directly, "
                                 "offline, is a test instrument and is not gated"},
            {"id": "R8", "what": "after a zero-minute first turn the page drops the session and opens a new one "
                                 "(a lifecycle that predates this cycle and is shared with GI); the opioid now "
                                 "refuses that session, GI still maps it"},
            {"id": "R9", "what": "two oxygen changes inside one engine minute would stop every run; no real "
                                 "order produces a zero-minute oxygen turn"},
            {"id": "R10", "what": "with the flag on an opioid turn costs about 100 ms at minute 99, four "
                                  "trajectories recomputed from arrival, against 2 ms with it off"},
        ),
    },
    "failure_policy": {
        "the_encounter": "never sees a shadow failure: the engine's turn is committed before the shadow observes "
                         "it, on copies",
        "a_refused_arrival": "no run, and the reason in the session record",
        "a_witness_that_cannot_run": "records why and stops at its last true minute; the others go on",
        "no_substitute": "a failed run is never replaced by another witness, by the committed run or by the "
                         "engine's values",
        "replay": "every run replays from its own artifact up to its last recorded minute",
        "where_it_is_visible": "the session record and the research trace; no screen shows it today",
    },
}

# -- P3-145: the readiness gates (read-only audit) ----------------------------------------------------------------

GATES = (
    {"gate": "runtime exposure", "status": "BLOCKED",
     "evidence": "the shadow opens only behind a process flag that a deployment secret cannot set; exposure "
                 "needs authority, whose gate names one family and one domain and has no approved snapshot",
     "blocker": "no faculty-approved snapshot; authority is GI pressure only by design"},
    {"gate": "UI exposure", "status": "BLOCKED",
     "evidence": "no screen, faculty or resident, renders a shadow record or a common-core reading",
     "blocker": "nothing is built; what a resident would see is not designed"},
    {"gate": "trace capture", "status": "PARTIAL",
     "evidence": "the session record and the research trace are complete and replay exactly from JSON; the "
                 "research artifact store accepts authority-experiment artifacts only",
     "blocker": "a live shadow trace is held in the session and never persisted"},
    {"gate": "scoring isolation", "status": "GREEN",
     "evidence": "the authoritative record, the ledger and the order fates are identical with the shadow on and "
                 "off, for GI and for the opioid series",
     "blocker": None},
    {"gate": "faculty review workflow", "status": "PARTIAL",
     "evidence": "decisions are recorded in the Decision File and the decision packs exist; six decisions of the "
                 "final pack are still open",
     "blocker": "no in-app review of a shadow trace or of a region"},
    {"gate": "case selection", "status": "NOT_YET_EVALUATED",
     "evidence": "the first pilot is frozen and untouched; no case is selected for a later one",
     "blocker": "a faculty selection, after review"},
    {"gate": "failure visibility", "status": "PARTIAL",
     "evidence": "every shadow failure, refused arrival and unsupported action is recorded and classified, and "
                 "none reaches the encounter",
     "blocker": "nothing surfaces a failure to an operator: no screen, log line or alert"},
    {"gate": "rollback", "status": "GREEN",
     "evidence": "unset the flag and the encounter is exactly the engine: no key, no session, no digest; the "
                 "family allowlist can only narrow",
     "blocker": None},
    {"gate": "resident-facing safety", "status": "BLOCKED",
     "evidence": "today nothing of the shadow reaches a resident, which is safe; an exposure would show a "
                 "physiology with no terminal transition, no consciousness mapping and unapproved regions",
     "blocker": "the unset collapse and consciousness layers and the development regions"},
)

READINESS = {
    "SIMULATION_ENGINE_READINESS": {
        "verdict": "SECOND_FAMILY_LIVE_SHADOW_VALIDATED_FOR_DEVELOPMENT",
        "holds": ("two mechanistically distinct families run in the live shadow with no authority",
                  "live, offline and replay agree state for state",
                  "the parameter is a region, kept as three trajectories",
                  "the indirect loop is audited and safe in the region"),
        "does_not_hold": ("ACS has no live arrival", "the regions are development regions",
                          "no terminal transition", "one case binds each region"),
    },
    "RESIDENT_PILOT_DEPLOYMENT_READINESS": {
        "verdict": "NOT_READY_FOR_RESIDENT_PILOT_REVIEW",
        "gates": {"GREEN": 2, "PARTIAL": 3, "BLOCKED": 3, "NOT_YET_EVALUATED": 1},
    },
}

#: Design only. The frozen first pilot is neither chosen nor modified here.
FUTURE_PILOT_RANKING = {
    "scale": "3 strongest, 0 weakest, per criterion; a ranking for a FUTURE non-frozen pilot after faculty review",
    "criteria": ("causal_completeness", "runtime_readiness", "parameter_uncertainty", "educational_discriminability",
                 "failure_visibility", "implementation_risk"),
    "families": {
        "gi_bleed": {"causal_completeness": 3, "runtime_readiness": 3, "parameter_uncertainty": 2,
                     "educational_discriminability": 2, "failure_visibility": 3, "implementation_risk": 3,
                     "why": "the only family with a golden, a live mapping from the state and an authority design"},
        "opioid": {"causal_completeness": 3, "runtime_readiness": 2, "parameter_uncertainty": 1,
                   "educational_discriminability": 3, "failure_visibility": 2, "implementation_risk": 2,
                   "why": "the sharpest teaching contrast (saturation against ventilation) and now live in "
                          "shadow; two synthetic rates, a development region and no dose"},
        "pulmonary_edema": {"causal_completeness": 2, "runtime_readiness": 1, "parameter_uncertainty": 1,
                            "educational_discriminability": 2, "failure_visibility": 1, "implementation_risk": 1,
                            "why": "complete offline on one case; one rate, no dose, RR does not read lung water"},
        "acs": {"causal_completeness": 2, "runtime_readiness": 0, "parameter_uncertainty": 1,
                "educational_discriminability": 2, "failure_visibility": 1, "implementation_risk": 0,
                "why": "complete offline; no live arrival and six authored variants against one certified case"},
    },
    "order": ("gi_bleed", "opioid", "pulmonary_edema", "acs"),
    "strongest_future_candidate": "gi_bleed",
    "strongest_candidate_with_a_distinct_teaching_contrast": "opioid",
    "is_a_selection": False,
}

# -- P3-146: the checkpoint ---------------------------------------------------------------------------------------

CHECKPOINT = {
    "engine_verdict": "A_SECOND_FAMILY_LIVE_SHADOW_VALIDATED",
    "pilot_verdict": "NOT_READY_FOR_RESIDENT_PILOT_REVIEW",
    "remaining_blockers": (
        "no faculty-approved snapshot, so no authority and no exposure",
        "no screen for a common-core reading, faculty or resident",
        "live shadow traces are not persisted",
        "no terminal transition and no consciousness mapping in the common core",
        "the two regions are development regions and two rates are synthetic points",
        "no case selected for a later pilot",
        "no operator-facing surface for a shadow failure",
    ),
    "next_shortest_package": "persist the live shadow trace in the faculty/research store and render it on a "
                             "faculty-only screen: it closes trace capture and failure visibility, needs no "
                             "physiology and no authority, and is what a faculty review of the regions would read",
    "not_claimed": ("clinical validation", "resident readiness", "a preferred transmission point",
                    "any change to the frozen first pilot"),
}

# <measured>
MEASURED = {'feedback': {'minimum_delivery_index': {'opioid_35m': 0.773263,
                                         'opioid_67f': 0.857586,
                                         'asthma_49m': 0.977593,
                                         'asthma_24f': 0.981448},
              'spo2_span_across_the_region': {'opioid_35m': {'60': 2.000001, '120': 5.066925, '240': 18.138952},
                                              'opioid_67f': {'60': 1.353353, '120': 3.401095, '240': 11.962757},
                                              'asthma_49m': {'60': 0.392768, '120': 0.847255, '240': 1.994181},
                                              'asthma_24f': {'60': 0.374016, '120': 0.778558, '240': 1.669647}},
              'first_fraction_that_opens_the_gate': {'opioid_35m': {'60': 0.802765, '120': 0.341475, '240': 0.120882},
                                                     'opioid_67f': {'60': None, '120': 0.446764, '240': 0.158154},
                                                     'asthma_49m': {'60': None, '120': None, '240': 0.598146},
                                                     'asthma_24f': {'60': None, '120': None, '240': 0.665171}},
              'gate_minute_at_the_upper_boundary': {'opioid_35m': 346,
                                                    'opioid_67f': 391,
                                                    'asthma_49m': None,
                                                    'asthma_24f': None},
              'forced_active': {'opioid_35m@1': {'gate_minute': 50,
                                                 'spo2_at_120': 16.271917,
                                                 'deficit_at_120': 0.528487},
                                'opioid_35m@0.5': {'gate_minute': 90,
                                                   'spo2_at_120': 23.277879,
                                                   'deficit_at_120': 0.303867}},
              'one_step': {'55': {'acid_multiplier': 0.815762, 'tone_branch_gain': 0.119828},
                           '60': {'acid_multiplier': 0.825046, 'tone_branch_gain': 0.11061},
                           '90': {'acid_multiplier': 0.869239, 'tone_branch_gain': 0.088665},
                           '120': {'acid_multiplier': 0.908068, 'tone_branch_gain': 0.065581}}},
 'live': {'LOW': {'untreated': {'minutes': 20,
                                'at_20': {'central_availability': 0.3392,
                                          'respiratory_rate': 5.4277,
                                          'paco2': 76.2759,
                                          'spo2': 79.8586}},
                  'oxygen': {'minutes': 20,
                             'at_20': {'central_availability': 0.3392,
                                       'respiratory_rate': 5.4277,
                                       'paco2': 76.2759,
                                       'spo2': 99.1977}},
                  'naloxone': {'minutes': 60,
                               'at_20': {'central_availability': 0.8896,
                                         'respiratory_rate': 14.2334,
                                         'paco2': 29.0866,
                                         'spo2': 80.7556},
                               'at_60': {'central_availability': 0.9516,
                                         'respiratory_rate': 15.2262,
                                         'paco2': 27.19,
                                         'spo2': 80.7907}},
                  'oxygen_and_naloxone': {'minutes': 60,
                                          'at_20': {'central_availability': 0.8896,
                                                    'respiratory_rate': 14.2334,
                                                    'paco2': 29.0866,
                                                    'spo2': 99.2123},
                                          'at_60': {'central_availability': 0.9516,
                                                    'respiratory_rate': 15.2262,
                                                    'paco2': 27.19,
                                                    'spo2': 99.2129}},
                  'delayed_naloxone': {'minutes': 60,
                                       'at_20': {'central_availability': 0.7559,
                                                 'respiratory_rate': 12.0948,
                                                 'paco2': 34.2297,
                                                 'spo2': 80.6601},
                                       'at_60': {'central_availability': 0.9501,
                                                 'respiratory_rate': 15.2009,
                                                 'paco2': 27.2352,
                                                 'spo2': 80.7898}},
                  'wait': {'minutes': 20,
                           'at_20': {'central_availability': 0.3392,
                                     'respiratory_rate': 5.4277,
                                     'paco2': 76.2759,
                                     'spo2': 79.8586}},
                  'respiratory_rate_area_1_60': {'naloxone': 835.6432, 'delayed_naloxone': 739.3521}},
          'CENTER_REFERENCE': {'untreated': {'minutes': 20,
                                             'at_20': {'central_availability': 0.3392,
                                                       'respiratory_rate': 5.4277,
                                                       'paco2': 76.2759,
                                                       'spo2': 79.7161}},
                               'oxygen': {'minutes': 20,
                                          'at_20': {'central_availability': 0.3392,
                                                    'respiratory_rate': 5.4277,
                                                    'paco2': 76.2759,
                                                    'spo2': 99.1954}},
                               'naloxone': {'minutes': 60,
                                            'at_20': {'central_availability': 0.8896,
                                                      'respiratory_rate': 14.2334,
                                                      'paco2': 29.0866,
                                                      'spo2': 81.4784},
                                            'at_60': {'central_availability': 0.9516,
                                                      'respiratory_rate': 15.2262,
                                                      'paco2': 27.19,
                                                      'spo2': 81.5454}},
                               'oxygen_and_naloxone': {'minutes': 60,
                                                       'at_20': {'central_availability': 0.8896,
                                                                 'respiratory_rate': 14.2334,
                                                                 'paco2': 29.0866,
                                                                 'spo2': 99.2244},
                                                       'at_60': {'central_availability': 0.9516,
                                                                 'respiratory_rate': 15.2262,
                                                                 'paco2': 27.19,
                                                                 'spo2': 99.2256}},
                               'delayed_naloxone': {'minutes': 60,
                                                    'at_20': {'central_availability': 0.7559,
                                                              'respiratory_rate': 12.0948,
                                                              'paco2': 34.2297,
                                                              'spo2': 81.2952},
                                                    'at_60': {'central_availability': 0.9501,
                                                              'respiratory_rate': 15.2009,
                                                              'paco2': 27.2352,
                                                              'spo2': 81.5438}},
                               'wait': {'minutes': 20,
                                        'at_20': {'central_availability': 0.3392,
                                                  'respiratory_rate': 5.4277,
                                                  'paco2': 76.2759,
                                                  'spo2': 79.7161}},
                               'respiratory_rate_area_1_60': {'naloxone': 835.6432, 'delayed_naloxone': 739.3521}},
          'HIGH': {'untreated': {'minutes': 20,
                                 'at_20': {'central_availability': 0.3392,
                                           'respiratory_rate': 5.4277,
                                           'paco2': 76.2759,
                                           'spo2': 79.4276}},
                   'oxygen': {'minutes': 20,
                              'at_20': {'central_availability': 0.3392,
                                        'respiratory_rate': 5.4277,
                                        'paco2': 76.2759,
                                        'spo2': 99.1908}},
                   'naloxone': {'minutes': 60,
                                'at_20': {'central_availability': 0.8896,
                                          'respiratory_rate': 14.2334,
                                          'paco2': 29.0866,
                                          'spo2': 82.8311},
                                'at_60': {'central_availability': 0.9516,
                                          'respiratory_rate': 15.2262,
                                          'paco2': 27.19,
                                          'spo2': 82.9536}},
                   'oxygen_and_naloxone': {'minutes': 60,
                                           'at_20': {'central_availability': 0.8896,
                                                     'respiratory_rate': 14.2334,
                                                     'paco2': 29.0866,
                                                     'spo2': 99.2479},
                                           'at_60': {'central_availability': 0.9516,
                                                     'respiratory_rate': 15.2262,
                                                     'paco2': 27.19,
                                                     'spo2': 99.25}},
                   'delayed_naloxone': {'minutes': 60,
                                        'at_20': {'central_availability': 0.7559,
                                                  'respiratory_rate': 12.0948,
                                                  'paco2': 34.2297,
                                                  'spo2': 82.4939},
                                        'at_60': {'central_availability': 0.9501,
                                                  'respiratory_rate': 15.2009,
                                                  'paco2': 27.2352,
                                                  'spo2': 82.9506}},
                   'wait': {'minutes': 20,
                            'at_20': {'central_availability': 0.3392,
                                      'respiratory_rate': 5.4277,
                                      'paco2': 76.2759,
                                      'spo2': 79.4276}},
                   'respiratory_rate_area_1_60': {'naloxone': 835.6432, 'delayed_naloxone': 739.3521}}}}
# </measured>


def all_records() -> dict:
    return {"status": STATUS, "cycle": CYCLE, "faculty_decisions": FACULTY_DECISIONS, "milestone": MILESTONE,
            "asthma_supersession": ASTHMA_SUPERSESSION, "feedback_graph": FEEDBACK_GRAPH,
            "feedback_verdict": FEEDBACK_VERDICT, "arrival_mapping": ARRIVAL_MAPPING, "ensemble": ENSEMBLE,
            "live_wiring": LIVE_WIRING, "gates": GATES, "readiness": READINESS,
            "future_pilot_ranking": FUTURE_PILOT_RANKING, "checkpoint": CHECKPOINT, "measured": MEASURED}
