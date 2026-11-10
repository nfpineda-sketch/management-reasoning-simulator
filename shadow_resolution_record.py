"""Registro del ciclo de resolucion de la sombra en vivo (2026-11-10): P3-156 a P3-166.

Datos puros: lo que el ciclo decidio, midio y dejo abierto. No importa nada y no ejecuta nada;
``test_shadow_resolution.py`` comprueba cada cifra contra el codigo.

Todo aqui es MEDICION DE DESARROLLO sobre un motor sin autoridad. Nada es verdad clinica, ninguna magnitud
esta aprobada por docentes, ningun testigo esta seleccionado y nada de esto lo ve un residente.
"""

CYCLE = "P3-156..P3-166"
STARTING_HEAD = "f1f6034"

FACULTY_DECISIONS = {
    "FD-151": "the active transmission region (0, 0.060621] is valid ONLY at the committed synthetic opioid "
              "deepening rate 0.005/min: CONDITIONAL_DEVELOPMENT_REGION, not robust to its uncertainty; no "
              "interval is invented from the exploratory probes 0.02 and 0.03",
    "FD-152": "search the repository's own evidence for a constraint on the deepening rate; derive a region "
              "only if the evidence constrains it with confidence >= 0.80, else return the exact faculty "
              "question",
    "FD-153": "mirror an order that is held and later really executes, at its REAL execution time; runtime "
              "synchronization only, no new treatment physiology",
    "FD-154": "no faculty observer inside the main application yet; the external report is enough this cycle",
    "FD-155": "terminal transition and consciousness: a READ-ONLY architecture audit first; no change to "
              "common physiology without a later explicit gate",
    "FD-156": "begin a faculty review of GI and opioid as CANDIDATE future cases; review readiness only, no "
              "resident pilot is launched or modified",
}

# -- P3-156 -------------------------------------------------------------------------------------------------------

PROVENANCE_STATUSES = ("FACULTY_DEFINED", "AUTHORED_CASE_CONSTRAINT", "CERTIFIED_BEHAVIORAL_CONSTRAINT",
                       "SYNTHETIC_REFERENCE", "EXPLORATORY_PROBE", "LEGACY_DERIVED", "UNKNOWN")

DEEPENING_RATE = {
    "parameter": "deepening_per_min",
    "provenance": (
        {"value": 0.005, "source": "clinical_core/opioid_migration.py DEEPENING_PER_MIN, under the heading "
                                   "'Synthetic, predeclared probe values (SYNTHETIC_ONLY)'",
         "status": "SYNTHETIC_REFERENCE", "constrains_the_rate": False,
         "note": "the one committed value; the live adapter's own provenance says 'a committed point, no span "
                 "is declared'"},
        {"value": "> 0 (direction only)", "source": "P2U-1 certification of the opioid migration: the "
                                                    "untreated patient worsens monotonically",
         "status": "CERTIFIED_BEHAVIORAL_CONSTRAINT", "constrains_the_rate": True,
         "note": "a sign, not a magnitude: it excludes zero and nothing else"},
        {"value": 0.02, "source": "clinical_core/opioid_migration.py RECURRENCE['deepening_per_min'] (the "
                                  "recurrence probe of the second variant)",
         "status": "EXPLORATORY_PROBE", "constrains_the_rate": False,
         "note": "written to exercise a mechanism, not as a bound; not evidence"},
        {"value": 0.03, "source": "clinical_core/opioid_migration.py SEVERE_DEEPENING_PER_MIN",
         "status": "EXPLORATORY_PROBE", "constrains_the_rate": False,
         "note": "written to exercise a mechanism, not as a bound; not evidence"},
        {"value": 0.5, "source": "test_clinical_core_opioid_migration.py, an invalid-input mutation",
         "status": "EXPLORATORY_PROBE", "constrains_the_rate": False,
         "note": "a negative control of the validator; never a patient"},
        {"value": "none", "source": "the authored case: 'later_observations': 'none authored (no "
                                    "post-naloxone truth)'",
         "status": "AUTHORED_CASE_CONSTRAINT", "constrains_the_rate": False,
         "note": "the case authors one arrival and no later observation: there is no time course to fit"},
        {"value": "unsupported patient arrests at minute 20", "source": "the legacy opioid rule",
         "status": "LEGACY_DERIVED", "constrains_the_rate": False,
         "note": "the legacy engine is never a calibration target; and the core has no arrest to place"},
        {"value": "none", "source": "the Decision File and the project documents",
         "status": "FACULTY_DEFINED", "constrains_the_rate": False,
         "note": "no faculty statement on the rate, an interval for it or a time course exists"},
        {"value": "f x ((1 - d)^-60 - 1) <= C", "source": "the development fixture: SpO2 at minute 60 not "
                                                         "below the development floor (P3-140)",
         "status": "CERTIFIED_BEHAVIORAL_CONSTRAINT", "constrains_the_rate": "JOINTLY_WITH_THE_FRACTION",
         "note": "one inequality over two unknowns: it bounds a combination, never the rate alone"},
    ),
    "identifiability": "NOT_IDENTIFIABLE_WITH_EXISTING_EVIDENCE",
    "why": "the only constraints on the rate are its sign and one inequality it shares with the transmission "
           "fraction; no authored time course, no faculty statement and no certified magnitude exists",
    "region": None,
    "region_confidence": 0.0,
    "required_confidence": 0.80,
    "verdict_confidence": 0.9,
    "uncertainty": "the repository was searched outside the validation corpus, which this stage does not "
                   "open; a constraint could only live there or outside the repository",
    "falsifier": "an authored later observation of the untreated patient (a value at a stated minute), or a "
                 "faculty statement of a time by which a stated deterioration must or must not have happened",
    "parameter_adoption": "STOPPED",
    "faculty_question": "For the development opioid patient left untreated on room air, by what minute "
                        "should ventilation have fallen to a stated fraction of its arrival value -- or, "
                        "equivalently, what is the earliest and the latest minute at which you would accept "
                        "the carbon dioxide having risen by a stated amount? One such pair bounds the rate; "
                        "without it the rate stays a single synthetic point.",
}

# -- P3-157 -------------------------------------------------------------------------------------------------------

JOINT = {
    "minutes": 60,
    "reparameterization": "the fixture depends on the two parameters only through f x ((1 - d)^-T - 1): "
                          "the central availability decays geometrically at rate d, the rise of carbon "
                          "dioxide at minute T is P0 x ((1 - d)^-T - 1), and the saturation at f = 0 does "
                          "not depend on d. It is neither f alone, nor d alone, nor the product f x d (the "
                          "product is only its first-order reading and it drifts by more than half across "
                          "the probed rates)",
    "P0": 69.0,
    "C": 0.02127038,
    "f_max_closed_form": "f_max(d) = C / ((1 - d)^-60 - 1)",
    "d_max_closed_form": "d_max(f) = 1 - (1 + C / f)^(-1/60)",
    "method": ("analytic bound", "fixed probes", "one-dimensional bisection on d per witness"),
    "rate_witnesses": (
        {"rate": 0.005, "status": "SYNTHETIC_REFERENCE", "justified": True, "f_max": 0.060621},
    ),
    "exploratory_rates_not_witnesses": (
        {"rate": 0.02, "status": "EXPLORATORY_PROBE", "f_max": 0.00901},
        {"rate": 0.03, "status": "EXPLORATORY_PROBE", "f_max": 0.004076},
    ),
    "transmission_witnesses": (
        {"name": "LOW", "f": 0.015, "d_max": 0.014608, "margin_over_committed_rate": 2.92},
        {"name": "CENTER_REFERENCE", "f": 0.03, "d_max": 0.008892, "margin_over_committed_rate": 1.78},
        {"name": "HIGH", "f": 0.06, "d_max": 0.005045, "margin_over_committed_rate": 1.009},
    ),
    "product_f_times_d_at_the_bound": {0.005: 0.0003031, 0.02: 0.0001802, 0.03: 0.0001223},
    "verdict": "CURRENT_REGION_VALID_ONLY_AT_COMMITTED_RATE",
    "joint_region": None,
    "why_no_joint_region": "a joint region needs justified bounds in BOTH dimensions and the rate has none "
                           "(P3-156); the closed form is the fixture's constraint, not a region of patients",
    "reading": "HIGH sits 0.9 % under the edge: any faster deepening than the committed one puts it outside. "
               "LOW tolerates almost three times the committed rate. The region is a statement about one "
               "rate.",
    "classification": "CONDITIONAL_DEVELOPMENT_REGION",
}

# -- P3-158 -------------------------------------------------------------------------------------------------------

HELD_ORDERS = {
    "old_behavior": "an order placed to run after a result was a declared gap when placed and was never "
                    "mirrored; when the engine ran it later the shadow run did not carry its effect, the "
                    "action was a NOT_MIRRORED row and the status was never COMPLETE",
    "events": ("ORDER_PLACED", "ORDER_HELD", "ORDER_RELEASED", "ORDER_EXECUTED", "ORDER_CANCELLED",
               "ORDER_TERMINAL_NOT_EXECUTABLE"),
    "event_semantics": {
        "ORDER_PLACED": "the engine accepted the order and held it: nothing ran",
        "ORDER_HELD": "it is in the engine's held list, waiting for a named result",
        "ORDER_RELEASED": "the engine ran the held order; alone, it means the run could not be mirrored (no "
                          "receipt reached the shadow, or its minute cannot be established) and says so",
        "ORDER_EXECUTED": "the minute it ran is established from the engine's own record: mirrored, once",
        "ORDER_CANCELLED": "reserved: the engine has no cancellation today, so no order reaches this state",
        "ORDER_TERMINAL_NOT_EXECUTABLE": "it is still held and the engine has stopped the patient",
    },
    "fixed_at": "the shared session layer that mirrors every family's orders; no adapter and no engine file "
                "changed",
    "execution_minute": "read from the engine's own record: the minute the awaited result came back when a "
                        "result left pending by an earlier turn released it inside the turn, else the end "
                        "of the turn in which the engine found it ready. Never the placement minute",
    "timing_rule": "placed at p, executed at e: the contributor starts by the layer's one rule, first "
                   "present in the state of minute e + 1",
    "exactly_once": "a held order is matched to the engine's receipt by kind, awaited result and placement "
                    "minute, oldest first, and is mirrored under one identity; observing the same turn again "
                    "adds nothing, and a receipt with no held order behind it is declared, not mirrored",
    "unsupported": "an executed held order the core cannot represent is mirrored as an action and declared "
                   "a gap: DECLARED_GAP with UNSUPPORTED_ACTION, never a faked effect",
    "not_executed": "an order the engine has not run is a HELD_NOT_EXECUTED row: nothing is missing from the "
                    "shadow run, so the status is not degraded by it",
    "unmatched_release": "a receipt for a held order the session was not holding, or one whose minute cannot "
                         "be established, is NOT mirrored and says so; its effect is never guessed",
    "unobserved_release": "the engine also releases held orders while clinical time passes in an information "
                          "activity (a question, an examination), which no shadow turn observes: such an "
                          "order leaves the held list with no receipt. It is NOT mirrored and NOT called "
                          "cancelled: it is a NOT_MIRRORED row, a declared gap and a status that is never "
                          "COMPLETE. Found by the independent review of this cycle",
    "engine_facts": ("the engine has no cancellation: a held order leaves its list only by running",
                     "an order held on a result the engine does not produce never runs",
                     "the engine's receipt names the placement minute and not the execution minute"),
    "measured": {"case": "opioid_35m", "placed": 0, "executed": 5, "first_shadow_minute": 6,
                 "chunkings_of_the_wait": 20, "all_equal_to_the_engine_stamp": True},
    "dispositions": 8,
}

# -- P3-159 -------------------------------------------------------------------------------------------------------

SESSION_RESIDUALS = {
    "generation": {
        "explicit_identifier_exists": True,
        "what": "the id of the attempt record the page starts every account-backed encounter from",
        "used": "the page hands it to the session; another attempt is another encounter whatever its "
                "patient looks like. The session keeps a digest of it, never the identifier",
        "closes": "a second attempt after a first that left no trace on the patient (a zero-time turn with "
                  "no fingerprint)",
        "residual": "an encounter that is not started from an attempt record has no generation; there the "
                    "three state rules decide and the same residual stays, declared",
        "no_heuristic_added": True,
    },
    "hidden_state": {
        "classification": "IRRELEVANT_TO_THE_CERTIFIED_MAPPING",
        "why": "the engine derives it from the state the rule already compares; the certified arrival "
               "mapping reads none of it; the case authors none of it",
        "action": "none: no authored value was added to make the equality stricter",
    },
    "trace_integrity": {
        "mechanism": "a SHA-256 digest over the canonical trace plus a self-consistency check of the trace "
                     "against its own replay artifacts",
        "protects": ("accidental corruption or truncation of a stored record",
                     "an edit that does not recompute the digest",
                     "a re-sealed edit that contradicts the trace's own replay artifacts (status, "
                     "witnesses, actions, minutes)",
                     "a record from another core lineage being replayed as if it were this one"),
        "does_not_protect": ("a writer who replaces the whole record with another self-consistent one: "
                             "there is no key, no signature and no external anchor",
                             "deletion of a record or of a whole attempt",
                             "who wrote a record, or when"),
        "cryptographic_infrastructure_added": False,
    },
}

# -- P3-160 -------------------------------------------------------------------------------------------------------

ARCHITECTURE_STATUSES = ("COMMON_CORE_EXISTS", "AUXILIARY_EXISTS", "LEGACY_ONLY", "SHADOW_ONLY", "DEFERRED",
                         "MISSING")

TERMINAL_CONSCIOUSNESS = {
    "read_only": True,
    "architecture": (
        {"concept": "consciousness level (0-3)", "status": "COMMON_CORE_EXISTS",
         "detail": "a derived reading: the authored arrival level as a floor, raised by pressure and "
                   "saturation ladders; capped while there is a pulse"},
        {"concept": "neurologic state N", "status": "COMMON_CORE_EXISTS",
         "detail": "a state field no live writer writes and no default reading reads"},
        {"concept": "neurologic impairment from hypercapnia, acidemia, hypoxemia, low delivery",
         "status": "DEFERRED",
         "detail": "the encephalopathy candidate is structurally complete, its magnitudes UNSET, and no live "
                   "path calls it"},
        {"concept": "drug-induced depression of consciousness", "status": "MISSING",
         "detail": "central availability drives ventilation only; nothing carries it to consciousness"},
        {"concept": "observed mental-status category", "status": "LEGACY_ONLY",
         "detail": "the resident's mental status is the legacy engine's; the core emits no category and the "
                   "mapping is pending faculty"},
        {"concept": "pulse present / rhythm", "status": "COMMON_CORE_EXISTS",
         "detail": "representable, and changed only by a scripted rhythm event or by the collapse rule"},
        {"concept": "circulatory collapse rule", "status": "DEFERRED",
         "detail": "the collapse candidate exists with both limits UNSET: off on every live path"},
        {"concept": "respiratory arrest / apnoea to loss of pulse", "status": "MISSING",
         "detail": "the boundary is declared unresolved in the core; no edge leads from apnoea or hypoxemia "
                   "to a terminal state"},
        {"concept": "arrest and terminal outcome", "status": "LEGACY_ONLY",
         "detail": "only the legacy engine arrests a patient and only it writes the resident's terminal "
                   "screen"},
        {"concept": "terminal signal in the shadow", "status": "SHADOW_ONLY",
         "detail": "the shadow stops because the legacy clock stops; the only signal is a "
                   "SAFETY_CRITICAL divergence on pulse and rhythm, and (since this cycle) a held order "
                   "marked not executable"},
        {"concept": "candidate diagnostics of both layers on a shadow minute", "status": "SHADOW_ONLY",
         "detail": "a diagnostic reader exists with no production caller"},
    ),
    "causal_edges_present": ("pressure -> consciousness ladder", "saturation -> consciousness ladder",
                             "scripted rhythm event -> pulse"),
    "causal_edges_missing": ("central depressant -> consciousness", "hypercapnia / acidemia -> consciousness",
                             "delivery debt -> consciousness", "apnoea / hypoxemia -> loss of pulse",
                             "collapse burden -> loss of pulse (rule off)",
                             "core state -> observed mental-status category"),
    "contradictions_possible_today": (
        {"what": "the legacy patient is arrested while the core run has a pulse, a pressure and a "
                 "consciousness level of its arrival",
         "measured": {"case": "opioid_35m", "untreated": True, "legacy_arrest_minute": 20,
                      "core_pulse_present": True, "core_sbp": 106.0, "core_spo2": 80.0,
                      "core_consciousness_level": 2}},
        {"what": "the legacy mental status changes while the core level stays at its arrival floor",
         "measured": {"case": "opioid_35m"}},
        {"what": "the two consciousness ladders disagree in GI (classified PARTIALLY_EXPLAINED)",
         "measured": {"case": "gi_bleed_57m"}},
    ),
    "visible_to_a_resident_today": False,
    "why_not_visible": "the core has no authority and nothing of it is rendered; every contradiction above "
                       "is between the legacy screen and an invisible run",
    "minimum_representation": ("one terminal state both engines agree on, with its cause",
                               "a consciousness reading with a causal source for every family that can "
                               "change it (pressure, oxygenation, ventilation, central depressant)",
                               "a faculty-approved mapping from that reading to the observed category",
                               "a rule for which engine decides the terminal transition while authority "
                               "is partial"),
    "verdict": "COMMON_CORE_EXTENSION_REQUIRED",
    "verdict_options": ("EXISTING_TERMINAL_CONSCIOUSNESS_ARCHITECTURE_SUFFICIENT",
                        "RUNTIME_MAPPING_ONLY_REQUIRED", "COMMON_CORE_EXTENSION_REQUIRED",
                        "REPRESENTATION_NEEDS_REDESIGN"),
    "why_not_mapping_only": "a mapping can only carry what the core computes, and the core computes no "
                            "respiratory arrest, no drug effect on consciousness and no category",
    "why_not_redesign": "the existing variables can represent the states (level, pulse, rhythm, N, a "
                        "collapse burden); what is missing is causal edges and their magnitudes, not the "
                        "representation",
    "implemented_this_cycle": False,
}

# -- P3-161 -------------------------------------------------------------------------------------------------------

BROWSER = {
    "infrastructure": "the repository's before/after browser tooling: isolated servers of the real page, no "
                      "network, no credentials, synthetic accounts, Chromium",
    "sides": {"off": "the working tree with no shadow flag", "on": "the same tree with the shadow flag and a "
                                                                   "trace store outside the tree"},
    "launch": "from the faculty sandbox with a synthetic administrator account (the curriculum does not "
              "assign these two families to a new synthetic resident); the encounter page is the same code",
    "encounters": ("gi_bleed_57m", "opioid_35m"),
    "checked": ("session creation", "action reflection", "trace persistence", "zero-time behavior",
                "failure isolation", "page text identical with the shadow on and off"),
    "resident_visible_widgets_created": False,
    "verdict": "BROWSER_PATH_SHADOW_VALIDATED",
    "limits": ("the comparison is the rendered text of the page at each step and a screenshot per step, not "
               "a pixel comparison",
               "two encounters of a few turns each; not a resident account, not the closing review",
               "run data stays outside the repository: the run is reproduced by its script, not by the "
               "suite"),
}

# -- P3-162 -------------------------------------------------------------------------------------------------------

FACULTY_REVIEW = {
    "tool": "the external observer's review package: an index in markdown and one report page per trace",
    "inside_the_main_application": False,
    "new_physiology": False,
    "per_trace": ("initial state", "action timeline", "expected causal first channel",
                  "observed first channel", "downstream sequence", "region witnesses", "failures",
                  "replay status", "unresolved synthetic parameters"),
    "first_effect_method": "the trace's own replay artifact with one contributor removed, compared channel "
                           "by channel through the layer's one from-artifact path",
    "questions_are": "faculty judgment only: causal order, plausibility of direction, what is missing, "
                     "candidate suitability; no implementation detail",
    "finding": "in the opioid run every channel downstream of the reversal responds in the same simulated "
               "minute; in GI the order is visible (volume and pressures first, then debt, then lactate)",
    "resident_access": False,
}

# -- P3-163 -------------------------------------------------------------------------------------------------------

CASE_SELECTION = {
    "is_a_selection": False,
    "criteria": ("mechanism clarity", "management discriminability", "runtime completeness",
                 "parameter uncertainty", "unsupported actions", "terminal-state risk",
                 "trace interpretability", "likely resident confusion", "faculty calibration burden"),
    "comparison": {
        "mechanism clarity": {"gi_bleed": "volume loss to perfusion, with a visible order of effects",
                              "opioid": "one mechanism, every downstream channel in the same minute",
                              "better": "gi_bleed"},
        "management discriminability": {"gi_bleed": "fluid, blood, oxygen, acid suppression and the stop of "
                                                    "the bleeding are each represented and distinguishable",
                                        "opioid": "reversal and oxygen are represented; assisted "
                                                  "ventilation is not",
                                        "better": "gi_bleed"},
        "runtime completeness": {"gi_bleed": "a committed golden; every divergence classified",
                                 "opioid": "no golden: every reading NOT_COMPARABLE, and a safety-critical "
                                           "divergence whenever the legacy patient arrests",
                                 "better": "gi_bleed"},
        "parameter uncertainty": {"gi_bleed": "a development default profile, no conditional region",
                                  "opioid": "an unidentifiable deepening rate, a conditional region, a "
                                            "synthetic recovery rate, a declared quotient",
                                  "better": "gi_bleed"},
        "unsupported actions": {"gi_bleed": "vascular access and consults carry no physiology",
                                "opioid": "assisted ventilation, airway and sedation are declared gaps: a "
                                          "central management is absent",
                                "better": "gi_bleed"},
        "terminal-state risk": {"gi_bleed": "no legacy arrest in two untreated hours of the tested variant",
                                "opioid": "the untreated legacy patient arrests at minute 20 and the core "
                                          "cannot follow",
                                "better": "gi_bleed"},
        "trace interpretability": {"gi_bleed": "one run, ordered downstream effects",
                                   "opioid": "one run and three witnesses, to be read as a span",
                                   "better": "gi_bleed"},
        "likely resident confusion": {"gi_bleed": "two consciousness ladders that can disagree",
                                      "opioid": "a monitor that would contradict the outcome at arrest, and "
                                                "a consciousness that does not move",
                                      "better": "gi_bleed"},
        "faculty calibration burden": {"gi_bleed": "the magnitudes of one profile",
                                       "opioid": "the rate, the region, the recovery, the quotient and the "
                                                 "terminal representation",
                                       "better": "gi_bleed"},
    },
    "ranking": ("gi_bleed", "opioid"),
    "blockers": {
        "gi_bleed": ("no faculty-approved parameter snapshot", "the consciousness mapping is not approved",
                     "no terminal representation in the core", "nothing resident-facing is designed"),
        "opioid": ("the deepening rate has no evidence and no interval",
                   "the transmission region is conditional on that rate",
                   "no terminal or consciousness representation: the untreated course ends in a legacy "
                   "arrest the core cannot represent",
                   "assisted ventilation is not represented",
                   "no faculty-approved parameter snapshot", "nothing resident-facing is designed"),
    },
    "faculty_decision_pending": True,
}

# -- P3-164 -------------------------------------------------------------------------------------------------------

ATTACKS = ("held order executes later", "held order cancelled", "duplicate release", "unsupported held action",
           "zero-time continuation", "stale session", "wrong-family trace", "trace mutation",
           "failed persistence", "replay mismatch", "synthetic parameter boundary", "shadow ON/OFF isolation")

CERTIFICATION = {
    "attacks": ATTACKS,
    "randomized": {"seeds": (11, 23, 47, 101, 257, 1009), "families": 2, "held_orders_in_the_pool": True},
    "equality_on_vs_off": ("legacy patient state", "scoring inputs", "order destination",
                           "resident-visible outputs"),
    "authority": False,
}

# -- P3-165 -------------------------------------------------------------------------------------------------------

GATES = (
    {"gate": "runtime exposure", "status": "BLOCKED", "before": "BLOCKED",
     "evidence": "unchanged: the shadow opens only behind a process flag and exposure needs authority, whose "
                 "gate has no approved snapshot",
     "blocker": "no faculty-approved snapshot; authority is GI pressure only by design"},
    {"gate": "UI exposure", "status": "BLOCKED", "before": "BLOCKED",
     "evidence": "the review package and the report are faculty development tools outside the application; "
                 "the page renders nothing of the shadow, with the shadow on and off, in a real browser",
     "blocker": "nothing resident-facing is built or designed; faculty development tooling does not make "
                "this green"},
    {"gate": "trace capture", "status": "GREEN", "before": "GREEN",
     "evidence": "as before, and now through the real page in a browser; a held order that runs later is in "
                 "the trace at its real minute",
     "blocker": None, "scope": "faculty and development environments; no deployed store is designed"},
    {"gate": "scoring isolation", "status": "GREEN", "before": "GREEN",
     "evidence": "the authoritative record, the ledger and the order fates are identical with the shadow on "
                 "and off under held orders and the randomized sequences",
     "blocker": None},
    {"gate": "faculty review workflow", "status": "PARTIAL", "before": "PARTIAL",
     "evidence": "a review package exists per trace with the questions that need faculty judgment",
     "blocker": "no faculty review has taken place and no decision is recorded; the tool stays outside the "
                "application by decision"},
    {"gate": "case selection", "status": "PARTIAL", "before": "NOT_YET_EVALUATED",
     "evidence": "an engineering comparison of GI and opioid on nine criteria, with a ranking and the exact "
                 "blockers of each",
     "blocker": "the selection is a faculty decision and none has been made; both candidates have blockers",
     "scope": "an engineering comparison for review; not a selection"},
    {"gate": "failure visibility", "status": "GREEN", "before": "GREEN",
     "evidence": "eight dispositions and no bare success; a held order is never missing from the timeline, "
                 "waiting or run",
     "blocker": None, "scope": "pull-based: a reader opens the store or the report"},
    {"gate": "rollback", "status": "GREEN", "before": "GREEN",
     "evidence": "unset the flag and the encounter is exactly the engine; unset the store and nothing is "
                 "written",
     "blocker": None},
    {"gate": "resident-facing safety", "status": "BLOCKED", "before": "BLOCKED",
     "evidence": "the terminal and consciousness audit shows a resident-facing core could contradict the "
                 "outcome today",
     "blocker": "no terminal or consciousness representation in the core; no approved snapshot; no "
                "resident-facing design or review"},
)

READINESS = {
    "SIMULATION_ENGINE_READINESS": {
        "verdict": "LIVE_SHADOW_SYNCHRONIZED_WITH_DEFERRED_ORDERS_FOR_DEVELOPMENT",
        "holds": ("two families in the live shadow, no authority, one arrival rule",
                  "an order held and executed later is mirrored once at its real minute",
                  "the page path is exercised in a browser with the shadow on and off",
                  "traces persist, verify and replay exactly"),
        "does_not_hold": ("no terminal transition and no consciousness mapping in the core",
                          "the opioid region is conditional on a rate with no evidence",
                          "no common-core physiology was added or changed", "ACS has no live arrival"),
    },
    "FACULTY_REVIEW_READINESS": {
        "verdict": "READY_FOR_FACULTY_CASE_REVIEW_OF_SHADOW_TRACES_IN_DEVELOPMENT",
        "holds": ("a review package per persisted trace", "expected and observed first channel per treatment",
                  "the questions that need faculty judgment, and only those",
                  "an engineering comparison of the two candidate cases"),
        "does_not_hold": ("no faculty has reviewed a trace", "the tool is outside the application",
                          "no decision is recorded by the tool"),
    },
    "RESIDENT_PILOT_REVIEW_READINESS": {
        "verdict": "NOT_READY_FOR_RESIDENT_PILOT_REVIEW",
        "gates": {"GREEN": 4, "PARTIAL": 2, "BLOCKED": 3, "NOT_YET_EVALUATED": 0},
        "moved_this_cycle": ("case selection",),
        "still_blocked": ("runtime exposure", "UI exposure", "resident-facing safety"),
        "exact_blockers": ("no terminal or consciousness representation in the common core",
                           "no faculty-approved parameter snapshot",
                           "the opioid deepening rate has no evidence",
                           "no faculty review of a trace and no case selected",
                           "nothing resident-facing is designed, built or reviewed"),
    },
}

# -- P3-166 -------------------------------------------------------------------------------------------------------

ROADMAP = {
    "next_explicit_faculty_decision_package": "terminal transition and consciousness in the common core",
    "why": "the audit's verdict is COMMON_CORE_EXTENSION_REQUIRED and it blocks resident-facing safety for "
           "both candidate cases",
    "next_step_is_another_physiology_family": False,
    "package_asks": (
        "whether to authorize a common-core extension for the terminal transition and consciousness at all",
        "which causal sources consciousness must have (pressure, oxygenation, ventilation, central "
        "depressant)",
        "the mapping from the core reading to the observed mental-status category",
        "what ends an encounter in the core, and which engine decides while authority is partial",
    ),
    "in_parallel_no_code": (
        "the faculty review of the persisted GI and opioid traces with the review package",
        "the deepening-rate question of this cycle",
        "the case selection between the two candidates",
    ),
    "after_that": ("an approved parameter snapshot", "authority beyond GI pressure",
                   "a resident-facing design and its review"),
    "is_a_selection": False,
}

NOT_CLAIMED = ("clinical validation", "resident readiness", "any change to common physiology",
               "a deepening-rate interval", "a joint region", "a selected witness", "a selected case",
               "an implemented terminal or consciousness mapping")
