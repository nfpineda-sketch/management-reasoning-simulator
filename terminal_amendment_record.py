"""Registro del ciclo de sincronizacion final y de diseno de la Enmienda 2 (2026-11-10): P3-167 a P3-171 y
A2-001 a A2-010.

Datos puros: lo que el ciclo decidio, midio y dejo abierto. No importa nada y no ejecuta nada. Las pruebas
(``test_shadow_synchronization.py`` y ``test_terminal_amendment_design.py``) comprueban cada afirmacion contra
el codigo.

Todo aqui es DESARROLLO sobre un motor sin autoridad. Nada es verdad clinica, ningun umbral esta aprobado por
docentes y nada de esto lo ve un residente.
"""

CYCLE = "P3-167..P3-171 + A2-001..A2-010"
STARTING_HEAD = "cb0b2c8"

# -- P3-167 y P3-168 ------------------------------------------------------------------------------------------------

SYNCHRONIZATION = {
    "engine_path": {
        "function": "family_engine.advance_clinical_time",
        "what": "the one engine function that lets clinical time pass outside an order turn; inside its "
                "minute loop, when a pending result comes back, it runs every held order waiting for it and "
                "returns the receipt among its action summaries",
        "page_helper": "app.spend_clinical_time",
        "page_callers": 3,
        "callers": ("a history question (two call sites)", "a physical examination"),
        "result_review_advances_time": False,
        "result_review": "reading a result that is already back costs no engine time and calls no engine "
                         "function: there is no release path there to observe",
    },
    "semantics": "HELD -> EXECUTED is read from the engine's own receipt of the interval; the activity's "
                 "content (the question, the answer, the examined region) is never passed to the session",
    "timing": "the minute the awaited result came back, from the engine's record; first present in the "
              "shadow state of that minute + 1 -- the rule already certified for a release inside an order "
              "turn, and the same run digest as that release",
    "exactly_once": "one identity per released order; the same activity observed again adds nothing",
    "unsupported": "an executed held order the core cannot represent is a declared gap, never a faked effect",
    "isolation": ("the engine file is unchanged", "the order, the ledger and the scoring inputs are unchanged",
                  "the page renders nothing new", "the observer copies what it reads and executes nothing",
                  "a failure of the observer is recorded in the observer"),
    "negative_controls": ("remains HELD", "becomes TERMINAL_NOT_EXECUTABLE", "duplicate observation",
                          "multiple identical studies", "release during different information activities",
                          "unsupported executed action"),
    "randomized": {"seeds": (11, 23, 47, 101, 257, 1009), "families": 2,
                   "mix": ("ordinary execution", "delayed execution in an order turn",
                           "delayed execution in an information activity", "duplicate observation",
                           "unsupported actions")},
    "verdict": "LIVE_SHADOW_EXECUTION_SYNCHRONIZATION_COMPLETE",
    "covers": ("every engine path the page uses to let time pass: the order turn and the information "
               "activity", "GI and opioid"),
    "does_not_cover": ("an interval advanced without the page helper is still declared NOT_MIRRORED, not "
                       "mirrored", "the execution minute is read from the engine's record because its "
                       "receipt does not carry it", "a real browser run of an information activity is "
                       "reported separately"),
}

FACULTY_DECISIONS = {
    "FD-NEW-A": "the opioid deepening rate stays one SYNTHETIC_REFERENCE point (0.005/min); no interval; the "
                "transmission region stays CONDITIONAL_DEVELOPMENT_REGION on it; no calibration this cycle",
    "FD-NEW-B": "the shadow may observe orders the engine executes during an information activity -- the "
                "execution event only, at its real time; nothing is inferred from the activity",
    "FD-NEW-C": "GI is the preferred FUTURE case for a pilot-readiness review; ranking GI, opioid; the frozen "
                "first pilot is not modified",
    "FD-NEW-D": "a FORMAL common-core amendment design package for terminal state and consciousness; "
                "implementation only where mechanism and region are defensible at confidence >= 0.80; "
                "otherwise stop and return the faculty question",
    "FD-NEW-E": "consciousness stays distinct from terminal outcome; no direct shortcut rule where an "
                "intermediate mechanism should carry the effect",
    "FD-NEW-F": "terminality is structured physiological predicates owned by the common core; the runtime "
                "owns encounter termination and the resident-visible category",
}

# -- P3-169 ---------------------------------------------------------------------------------------------------------

CASE_REVIEW = {
    "preferred_future_case": "gi_bleed",
    "ranking": ("gi_bleed", "opioid"),
    "decided_by": "faculty (FD-NEW-C)",
    "first_pilot_modified": False,
    "is_a_deployment": False,
    "comparison": {
        "causal completeness": {
            "gi_bleed": "volume, haemoglobin, output, pressure, delivery, debt, lactate and rate are one "
                        "executed chain with a visible order of effects",
            "opioid": "ventilation, carbon dioxide and pH are executed; oxygenation follows only in the "
                      "conditional witness runs; nothing reaches consciousness or a terminal state"},
        "live runtime readiness": {
            "gi_bleed": "a committed golden; every divergence classified; execution synchronization complete",
            "opioid": "no golden (every reading NOT_COMPARABLE); synchronization complete; the terminal "
                      "boundary is LEGACY_TERMINAL_CORE_ACTIVE whenever the untreated course ends"},
        "unsupported-action surface": {
            "gi_bleed": "vascular access and consults carry no physiology",
            "opioid": "assisted ventilation, airway and sedation are declared gaps"},
        "parameter uncertainty": {
            "gi_bleed": "one development default profile; no conditional region",
            "opioid": "a deepening rate with no evidence, a region conditional on it, a synthetic recovery "
                      "rate and a declared quotient"},
        "terminal/consciousness dependency": {
            "gi_bleed": "the legacy engine has NO arrest rule for GI, so no terminal contradiction exists "
                        "today; what remains is the consciousness reading (an adopted legacy ladder)",
            "opioid": "the untreated legacy course ends in an arrest at minute 20 that the core cannot "
                      "represent, and the core's consciousness does not move"},
        "trace interpretability": {
            "gi_bleed": "one run, effects in a visible order",
            "opioid": "one run and three witnesses read as a span; every effect in the same minute"},
        "faculty calibration burden": {
            "gi_bleed": "the profile's magnitudes and the consciousness mapping",
            "opioid": "all of GI's, plus the rate, the region, the recovery, respiratory failure and whether "
                      "the drug depresses consciousness directly"},
    },
    "better_in_every_criterion": "gi_bleed",
}

# -- A2-001 ---------------------------------------------------------------------------------------------------------

LINEAGE = {
    "historical_closure": {"name": "PHASE2_CLOSURE",
                           "digest": "22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a",
                           "changed": False},
    "parent": {"name": "PHASE2_AMENDMENT_1",
               "digest": "10b45ce2967ea55afccb35291afb5bb1f7f1b01eb4a253e6a0736c02a5878635",
               "certified_candidate": "0b3c44396ddac13a0e0f1c000113d14825d61f67",
               "branch_head": "0c230f88bbe4eac76b9b69524c2fc46b53a777be", "changed": False},
    "workspace": {"branch": "phase-2-amendment-2-terminal-consciousness",
                  "created_from": "0c230f88bbe4eac76b9b69524c2fc46b53a777be",
                  "commits_on_it": 0, "common_core_changed": False,
                  "status": "WORKSPACE_ONLY_NO_CANDIDATE"},
    "active_core_on_the_phase3_branch": "PHASE2_AMENDMENT_1",
    "successor_requirements": ("a declared reversal that reconstructs the parent byte for byte",
                               "the lineage entry and its record", "the root contracts",
                               "the gate's negative controls", "an adversarial review",
                               "a full certification before promotion"),
}

# -- A2-002 ---------------------------------------------------------------------------------------------------------

EDGE_STATUSES = ("IMPLEMENTED_COMMON_CORE", "IMPLEMENTED_LEGACY", "IMPLEMENTED_RUNTIME", "DEFERRED", "MISSING",
                 "DOCUMENTATION_ONLY")

GRAPH = (
    {"edge": "blood flows -> V, Hb", "status": "IMPLEMENTED_COMMON_CORE"},
    {"edge": "V, P, T, rhythm -> output", "status": "IMPLEMENTED_COMMON_CORE"},
    {"edge": "output x T -> pressure", "status": "IMPLEMENTED_COMMON_CORE"},
    {"edge": "FiO2 -> SpO2", "status": "IMPLEMENTED_COMMON_CORE"},
    {"edge": "output, Hb, SpO2 -> delivery (DO2)", "status": "IMPLEMENTED_COMMON_CORE"},
    {"edge": "delivery -> effective deficit -> debt D", "status": "IMPLEMENTED_COMMON_CORE"},
    {"edge": "D -> lactate", "status": "IMPLEMENTED_COMMON_CORE"},
    {"edge": "D, pressure, SpO2 -> sympathetic drive -> heart rate", "status": "IMPLEMENTED_COMMON_CORE"},
    {"edge": "central availability -> RR -> W -> PaCO2 -> pH", "status": "IMPLEMENTED_COMMON_CORE",
     "scope": "profiles with the acid-base physiology on (opioid); not GI"},
    {"edge": "PaCO2 -> SpO2", "status": "IMPLEMENTED_COMMON_CORE",
     "scope": "only where a profile declares the transmission fraction: the witness runs, not the committed "
              "opioid profile"},
    {"edge": "SBP ladder -> consciousness level", "status": "IMPLEMENTED_COMMON_CORE",
     "note": "adopted from the legacy engine; a direct rule, not a mechanism"},
    {"edge": "SpO2 ladder -> consciousness level", "status": "IMPLEMENTED_COMMON_CORE",
     "note": "adopted from the legacy engine; a direct rule, not a mechanism"},
    {"edge": "no pulse -> consciousness level 3, RR 0", "status": "IMPLEMENTED_COMMON_CORE"},
    {"edge": "scripted rhythm event -> rhythm, pulse, terminal_since", "status": "IMPLEMENTED_COMMON_CORE"},
    {"edge": "output below a threshold -> collapse burden -> pulseless rhythm", "status": "DEFERRED",
     "note": "the rule is in the core and off: both limits are None"},
    {"edge": "MAP / deficit -> collapse signal -> burden -> terminal", "status": "DEFERRED",
     "note": "the collapse candidate layer: every mapping and time constant unset"},
    {"edge": "N -> neurologic impairment", "status": "DEFERRED",
     "note": "the encephalopathy candidate reads N; nothing writes N and nothing live calls the candidate"},
    {"edge": "MAP, deficit, SpO2, pH, PaCO2, glucose -> acute brain stress -> impairment", "status": "DEFERRED",
     "note": "the encephalopathy candidate: every signal unmapped, both time constants unset"},
    {"edge": "impairment -> observed mental-status category", "status": "MISSING"},
    {"edge": "central depressant -> consciousness", "status": "MISSING"},
    {"edge": "PaCO2 -> sympathetic drive", "status": "MISSING"},
    {"edge": "absent ventilation -> loss of pulse", "status": "MISSING",
     "note": "reachable only indirectly, through SpO2 and delivery, where the transmission fraction is "
             "declared and a collapse rule is on; neither holds on a committed profile"},
    {"edge": "respiratory failure as a state or predicate", "status": "MISSING"},
    {"edge": "family rule -> arrest / fibrillation minute", "status": "IMPLEMENTED_LEGACY",
     "note": "opioid: 20 unsupported failing minutes; GI: no arrest rule"},
    {"edge": "family state -> mental status shown", "status": "IMPLEMENTED_LEGACY"},
    {"edge": "arrest -> encounter locked, terminal screen", "status": "IMPLEMENTED_LEGACY"},
    {"edge": "legacy terminal record + core pulse -> terminal boundary of the trace", "status": "IMPLEMENTED_RUNTIME",
     "note": "added this cycle, outside the core, with no threshold"},
    {"edge": "pharmacologic depression as a modifier of impairment", "status": "DOCUMENTATION_ONLY"},
)

# -- A2-003 ---------------------------------------------------------------------------------------------------------

CONTRIBUTOR_VERDICTS = ("STRUCTURALLY_JUSTIFIED", "DEFERRED", "DUPLICATIVE", "NEW_MECHANISM_REQUIRED")

CONSCIOUSNESS = {
    "contributors": {
        "A primary neurologic state N": {
            "verdict": "STRUCTURALLY_JUSTIFIED", "structure": "the candidate reads N as primary impairment",
            "magnitude": "NOT_IDENTIFIABLE: no family writes N, so there is nothing to identify"},
        "B central depressant state": {
            "verdict": "NEW_MECHANISM_REQUIRED",
            "structure": "central availability drives ventilation only; whether the drug depresses "
                         "consciousness by the same state, by another, or only through carbon dioxide and "
                         "hypoxaemia is a clinical decision the repository does not hold",
            "magnitude": "NOT_IDENTIFIABLE"},
        "C oxygen-delivery debt / systemic hypoxic burden": {
            "verdict": "STRUCTURALLY_JUSTIFIED",
            "structure": "the candidate reads the acute deficit, MAP and SpO2 as signals of one stress",
            "magnitude": "NOT_IDENTIFIABLE: every signal is unmapped; no faculty value, no authored course"},
        "D hypercapnic burden": {
            "verdict": "STRUCTURALLY_JUSTIFIED",
            "structure": "the candidate reads pH and PaCO2 where the profile computes them; DEFERRED for a "
                         "profile without the acid-base physiology (GI)",
            "magnitude": "NOT_IDENTIFIABLE"},
        "E circulatory collapse": {
            "verdict": "STRUCTURALLY_JUSTIFIED",
            "structure": "already executed: no pulse forces the top level; what is deferred is the rule "
                         "that takes the pulse away",
            "magnitude": "none needed for the edge itself"},
    },
    "existing ladder": {
        "verdict": "DUPLICATIVE",
        "why": "SBP and SpO2 reach consciousness directly AND are inputs of delivery, deficit and the "
               "candidate's signals: adding the composite beside the ladder would count pressure and "
               "saturation twice. The composite must REPLACE the ladder, not join it",
        "values": {"pressure_levels": ((80.0, 1), (65.0, 2)), "oxygen_levels": ((87.0, 1), (80.0, 2))},
        "provenance": "LEGACY_DERIVED (adopted from the legacy engine's ladders)"},
    "double_counting": ("MAP and SBP are the same pressure_rel: one pressure signal, not two",
                        "SpO2 enters delivery, hence the deficit, and is also a signal of its own: the "
                        "candidate takes the MAXIMUM of its signals, which does not add them",
                        "lactate and debt are downstream of the deficit: neither may be a further input",
                        "sympathetic drive already reads debt, pressure and SpO2: it is not an input of "
                        "consciousness"),
    "structure_identifiable": True,
    "magnitudes_identifiable": False,
    "category_mapping": "MISSING: pending faculty",
}

# -- A2-004 y A2-005 ------------------------------------------------------------------------------------------------

RESPIRATORY_FAILURE = {
    "existing": ("expressed respiratory rate and ventilation fall with central availability, toward zero",
                 "PaCO2 rises without bound as ventilation falls and is undefined at exactly zero",
                 "availability is bounded to [0, 1] with no positive floor, and the opioid writer's loss is "
                 "proportional, so it never reaches zero",
                 "the only ventilatory floor in the core is a split bound of the non-acid-base rate formula",
                 "the apnoea boundary of the oxygenation link is declared unresolved"),
    "absent": ("a respiratory-failure predicate or typed state", "a dwell or burden for time in failure",
               "any edge from absent ventilation to the rhythm", "an authored case constraint"),
    "semantic_principle": "a ventilation/drive-based predicate, never SpO2 alone",
    "verdict": "NEW_COMMON_STATE_REQUIRED",
    "why": "the instantaneous variables suffice to SAY ventilation is low, but arrest is time in failure and "
           "its consequence: that needs a state the core does not have, and both the level that counts as "
           "failure and the dwell are thresholds nobody has set. Without a threshold the only exact "
           "predicate is a rate of zero, which the committed writer never reaches",
    "threshold_chosen": False,
}

CIRCULATORY_COLLAPSE = {
    "existing": ("a typed pulseless state (rhythm, pulse_present, terminal_since) with its invariant",
                 "a core rule from low output through a burden to a pulseless rhythm, off by default",
                 "a candidate layer from MAP and deficit through a burden to a terminal event, all unset",
                 "the burden's own memory slot in the core state",
                 "a stop of the run, by exception, when output reaches zero with a pulse and no rule"),
    "auxiliary_only": ("the collapse burden memory",),
    "deferred": ("both limits of the core rule", "every mapping and time constant of the candidate layer",
                 "the terminal rhythm phenotype", "return of circulation"),
    "verdict": "EXISTING_VARIABLES_SUFFICIENT_STRUCTURE",
    "open_structural_choice": "two overlapping structures exist (output-based in the core, MAP/deficit-based "
                              "in the candidate layer): which one is the rule is not decided",
    "threshold_chosen": False,
}

# -- A2-006 ---------------------------------------------------------------------------------------------------------

BOUNDARY = {
    "common_core": ("the physiological state", "structured predicates: circulatory arrest, respiratory "
                    "failure, severe consciousness impairment", "a continuous consciousness impairment with "
                    "its contributors", "never the encounter, the screen or the category"),
    "runtime": ("whether a predicate ends the encounter", "which engine decides while authority is partial",
                "the mapping from impairment to the resident-visible category",
                "the terminal encounter behaviour"),
    "legacy_and_shadow": ("the legacy engine keeps deciding termination and the visible mental status",
                          "the shadow records, per trace, where the two engines stand on terminality",
                          "nothing of the core is shown"),
    "invariant": "a trace can no longer hold a terminal legacy patient beside an active core run without "
                 "saying so: the terminal boundary names the state and the reason, and verification "
                 "recomputes it",
    "implemented": "IMPLEMENTED_RUNTIME, outside the common core, threshold-free",
    "verification_sees": ("the state, the reason or a predicate edited apart from the boundary's two sides",
                          "the core side edited apart from the run's last minute",
                          "a legacy arrest erased when the run itself recorded the pulse divergence"),
    "verification_does_not_see": ("a legacy record rewritten whole and consistently, such as another minute",
                                  "the boundary removed from the trace",
                                  "an edit of the last minute's own channels: only the replay sees that",
                                  "a legacy reading gone stale after an interval nobody observed"),
    "states": ("TERMINAL_AGREEMENT", "LEGACY_TERMINAL_CORE_ACTIVE", "CORE_TERMINAL_LEGACY_ACTIVE", "BOTH_ACTIVE",
               "TERMINAL_NOT_COMPARABLE"),
    "for_a_future_authoritative_runtime": "the same reading must be a precondition of authority: an "
                                          "authoritative minute with a boundary other than agreement or "
                                          "both-active must halt, as the authority transaction already halts "
                                          "on its other failures. Designed; not built (no authority exists)",
}

# -- A2-007 ---------------------------------------------------------------------------------------------------------

EVIDENCE_CLASSES = ("FACULTY_DEFINED", "AUTHORED_CASE", "CERTIFIED_BEHAVIORAL", "SYNTHETIC", "LEGACY_DERIVED",
                    "EXPLORATORY", "NONE")

IDENTIFIABILITY = {
    "evidence": (
        {"magnitude": "consciousness ladder: SBP 80 / 65, SpO2 87 / 80", "evidence": "LEGACY_DERIVED",
         "usable_as_a_threshold": False},
        {"magnitude": "encephalopathy signal mappings (MAP, deficit, SpO2, pH, PaCO2, glucose)",
         "evidence": "NONE", "usable_as_a_threshold": False},
        {"magnitude": "encephalopathy burden time constants", "evidence": "NONE", "usable_as_a_threshold": False},
        {"magnitude": "impairment -> category cut points", "evidence": "NONE", "usable_as_a_threshold": False},
        {"magnitude": "collapse output threshold 0.2 / 0.3 / 0.4", "evidence": "SYNTHETIC",
         "note": "a CANDIDATE registry range with no stated source; the GI cases cannot identify it",
         "usable_as_a_threshold": False},
        {"magnitude": "collapse burden limit 5 / 15 / 30", "evidence": "SYNTHETIC",
         "note": "a CANDIDATE registry range with no stated source", "usable_as_a_threshold": False},
        {"magnitude": "collapse rule test values (0.4, 10)", "evidence": "EXPLORATORY",
         "usable_as_a_threshold": False},
        {"magnitude": "legacy opioid arrest: 20 minutes at rate <= 6, SpO2 <= 80 or suppression >= 0.85",
         "evidence": "LEGACY_DERIVED", "usable_as_a_threshold": False},
        {"magnitude": "respiratory-failure level and dwell", "evidence": "NONE", "usable_as_a_threshold": False},
        {"magnitude": "authored arrival consciousness level per case", "evidence": "AUTHORED_CASE",
         "note": "a floor at arrival; not a threshold of anything", "usable_as_a_threshold": False},
        {"magnitude": "no pulse => top consciousness level", "evidence": "CERTIFIED_BEHAVIORAL",
         "note": "an invariant of the certified core, not a magnitude", "usable_as_a_threshold": False},
    ),
    "development_regions": (),
    "why_no_region": "no mechanism with a magnitude is both accepted and supported by evidence of a broad "
                     "region at confidence >= 0.80: the only ranges in the repository are unsourced "
                     "candidates, and the only numbers that produce the expected outcome are the legacy's",
    "faculty_questions": (
        "Consciousness. Do you accept replacing the adopted pressure and saturation ladder by one composite "
        "impairment (the worst of perfusion pressure, oxygen-delivery deficit, hypoxaemia, acidaemia / "
        "hypercapnia and hypoglycaemia, plus the primary neurologic state)? If so, for each signal: at what "
        "value does impairment begin and at what value is it complete, and how fast does it build and clear?",
        "Category. At what impairment is the patient Drowsy, Obtunded and Unresponsive?",
        "Central depressant. Does an opioid depress consciousness directly, as a state of its own, or is its "
        "effect on consciousness carried only by carbon dioxide retention and hypoxaemia?",
        "Circulatory collapse. Which is the rule -- sustained low output, or sustained low perfusion pressure "
        "and delivery deficit? For the one you choose: the level, the time it must be sustained, and the "
        "rhythm the patient is found in.",
        "Respiratory failure. What ventilation (as a fraction of arrival, or a rate) counts as failure, for "
        "how long before it is an arrest, and does a respiratory arrest take the pulse only through "
        "hypoxaemia or by a rule of its own?",
        "Termination. While the common core has no authority, the legacy engine ends the encounter. When the "
        "core has it, which predicates end an encounter, and which only change what is shown?",
    ),
}

# -- A2-008 a A2-010 ------------------------------------------------------------------------------------------------

DESIGN = {
    "objective": "remove the measured contradiction: the legacy encounter terminal while the common-core "
                 "run is physiologically active with its arrival consciousness",
    "output_contract": ("consciousness impairment: a continuous value and the contributor that sets it",
                        "circulatory-collapse predicate", "respiratory-failure predicate",
                        "severe-consciousness-impairment predicate",
                        "each predicate tri-valued in effect: true, false, or not determined because the "
                        "rule that would settle it is not declared"),
    "required_now": (
        {"component": "consciousness as the candidate composite, REPLACING the adopted ladder",
         "blocked_on": "the signal mappings, the time constants and the faculty's acceptance of the replacement"},
        {"component": "one circulatory-collapse rule that can take the pulse",
         "blocked_on": "the choice between the two existing structures, its level and its dwell"},
        {"component": "the structured predicates as a common-core output",
         "blocked_on": "the two components above: with nothing declared they would only repeat the pulse"},
        {"component": "the terminal boundary as an explicit state of every trace",
         "blocked_on": None, "done": "this cycle, in the runtime layer"},
    ),
    "optional_later": ("a respiratory-failure state with its dwell (opioid only)",
                       "a direct central-depressant path to consciousness (opioid only)",
                       "writers of the primary neurologic state N", "return of circulation",
                       "adoption of the transmission fraction, which the opioid chain to hypoxaemia needs"),
    "not_justified": ("a single terminal scalar", "any threshold taken from the legacy engine",
                      "keeping SpO2 -> unconscious or SBP -> unconscious as the authoritative path",
                      "an arrest defined by SpO2 alone", "a consciousness or arrest value chosen because it "
                      "reproduces the legacy outcome", "a resident-visible change"),
    "implementation": {
        "common_core": "INTENTIONALLY_STOPPED",
        "why": "every component that would change the certified core depends on a threshold nobody has set "
               "or on a faculty decision that changes its shape; a predicate contract with nothing declared "
               "would add no information and would cost a full successor certification",
        "outside_the_core": "the terminal boundary of the trace: threshold-free, non-authoritative, "
                            "recomputed by verification, shown in the faculty review package",
    },
    "verdict": "AMENDMENT_2_BLOCKED_ON_FACULTY_THRESHOLDS",
    "verdict_options": ("AMENDMENT_2_STRUCTURAL_CANDIDATE_READY_FOR_FULL_CERTIFICATION",
                        "AMENDMENT_2_BLOCKED_ON_FACULTY_THRESHOLDS", "AMENDMENT_2_REQUIRES_NEW_COMMON_MECHANISM",
                        "EXISTING_ARCHITECTURE_SUFFICIENT_NO_AMENDMENT_NEEDED"),
    "why_this_verdict": "for the preferred case (GI) and for the terminal contradiction itself, the "
                        "structures already exist in the core and its candidate layers and only their "
                        "magnitudes and one structural choice are missing. A new common mechanism is needed "
                        "only for the opioid-specific parts (a respiratory-failure state, a direct depressant "
                        "path), which the design places later and which are themselves faculty questions",
    "certified": False,
    "full_certification_required": False,
    "full_certification_run": False,
}

# -- P3-170 y P3-171 ------------------------------------------------------------------------------------------------

PILOT_IMPACT = {
    "gates_reassessed": ("resident-facing safety", "case selection", "trace capture"),
    "gates": {
        "resident-facing safety": {"before": "BLOCKED", "status": "BLOCKED",
                                   "why": "the amendment is blocked on faculty thresholds; the contradiction "
                                          "is now explicit in every trace, not removed"},
        "case selection": {"before": "PARTIAL", "status": "GREEN",
                           "why": "the faculty named GI the preferred future case",
                           "scope": "a preference for a future readiness review; no case is deployed"},
        "trace capture": {"before": "GREEN", "status": "GREEN",
                          "why": "execution synchronization is complete on every path the page uses"},
    },
    "gi_bleed": {"verdict": "NOT_READY_FOR_RESIDENT_PILOT_REVIEW",
                 "terminal_contradiction_today": False,
                 "remaining": ("consciousness is an adopted legacy ladder, and it disagrees with the legacy "
                               "reading in part", "no collapse rule: a GI patient cannot become pulseless in "
                               "the core", "no approved parameter snapshot", "nothing resident-facing")},
    "opioid": {"verdict": "NOT_READY_FOR_RESIDENT_PILOT_REVIEW",
               "terminal_contradiction_today": True,
               "remaining": ("the legacy arrest the core cannot represent", "consciousness does not move",
                             "the deepening rate has no evidence", "assisted ventilation is not represented",
                             "no approved parameter snapshot", "nothing resident-facing")},
    "needs_faculty_not_code": ("every threshold question of the amendment", "the parameter snapshot",
                               "the review of persisted traces"),
    "needs_code_after_faculty": ("the amendment itself, as a certified successor",
                                 "authority beyond GI pressure", "a resident-facing design"),
    "readiness": "NOT_READY_FOR_RESIDENT_PILOT_REVIEW",
}

ROADMAP = {
    "target": "READY_FOR_RESIDENT_PILOT_REVIEW (not deployment)",
    "case": "gi_bleed",
    "next_critical_package": "the faculty answers to the consciousness, category and circulatory-collapse "
                             "questions, for GI",
    "critical_path": (
        "faculty answers the three GI questions (consciousness composite, category, collapse rule)",
        "Amendment 2 for GI only: the composite replacing the ladder and one collapse rule, as a certified "
        "successor of Amendment 1",
        "faculty review of persisted GI traces and an approved GI parameter snapshot",
        "authority for GI beyond pressure, behind the existing gate, with the terminal boundary as a "
        "precondition",
        "a resident-facing design for GI and its review",
    ),
    "off_the_critical_path": ("the opioid deepening rate", "respiratory failure and the depressant path",
                              "any other physiology family"),
    "next_step_is_another_physiology_family": False,
}

NOT_CLAIMED = ("clinical validation", "resident readiness", "any change to common physiology",
               "a certified Amendment 2", "any consciousness, arrest or collapse threshold",
               "a deepening-rate interval", "a deployed case")
