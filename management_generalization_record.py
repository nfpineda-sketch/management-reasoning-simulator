"""P3-137 a P3-144: registro del ciclo de generalizacion de la causalidad de manejo.

Datos y nada mas: este modulo no importa la capa de sombra ni el nucleo. Cada cifra de ``MEASURED`` la recalcula
``test_management_generalization.py`` sobre el runtime integrado, asi que el registro no puede quedar viejo.

Todo aqui es MEDICION DE DESARROLLO. Las regiones son DEVELOPMENT_TEST_REGION: sirven para probar causalidad en un
simulador educativo. No son verdad clinica, ni dosis, ni recomendacion para pacientes reales, ni valores aprobados,
y ninguna se adopta como parametro del perfil comprometido.
"""

STATUS = "DEVELOPMENT_MEASUREMENT_NO_PARAMETER_ADOPTED"

#: El runtime sobre el que se midio todo: la Fase 3 con la enmienda certificada integrada.
RUNTIME = {
    "branch": "phase-3-runtime-integration",
    "core_version": "PHASE2_AMENDMENT_1",
    "core_digest": "10b45ce2967ea55afccb35291afb5bb1f7f1b01eb4a253e6a0736c02a5878635",
    "historical_closure_head": "d2cca46626ed5d45a792ec9456d46fb75fe87731",
    "historical_closure_digest": "22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a",
    "certified_candidate": "0b3c44396ddac13a0e0f1c000113d14825d61f67",
    "promotion_head": "0c230f88bbe4eac76b9b69524c2fc46b53a777be",
    "integration": {
        "method": "revert of the revert e1eb797 (601452c), then a no-fast-forward merge of the certified branch",
        "merge_head": "534aa506f6982ef4d27f2ff7f260df7329f53af0",
        "integrated_tree_equals_the_promotion_tree": True,
        "full_phase2_suite": "ALREADY_VALID_ON_EQUIVALENT_CODE",
    },
    "common_core_runtime_authority": False,
    "live_families": ["gi_bleed"],
}

# C3 -----------------------------------------------------------------------------------------------------------------

TRANSMISSION_REGION = {
    "quantity": "hypoventilation_oxygenation_transmission_fraction",
    "declared_R": 0.8,
    "identifies_only": "the ratio transmission_fraction / respiratory_quotient: with another R the same behaviour "
                       "is another fraction",
    "target": {"fixture": "opioid_35m", "minute": 60, "arm": "untreated", "spo2_low": 78.0, "spo2_high": 88.0,
               "classification": "DEVELOPMENT_TEST_REGION", "source": "faculty development decision (P3-117)"},
    "derivation": "the preimage of the target under the certified equation, found twice: by the formula "
                  "ODC^-1(base) - f * delta / R = ODC^-1(floor), and by bisection on the simulation itself",
    "bound_by": "opioid_35m",
    "common_region": (0.0, 0.060621),
    "the_ceiling_does_not_bind": True,
    "witnesses": {"LOW": 0.015, "CENTER_REFERENCE": 0.03, "HIGH": 0.06},
    "center_reference_is_preferred": False,
    "verdict": "RESPIRATORY_DEVELOPMENT_REGION_REPRODUCED",
}

# C4 -----------------------------------------------------------------------------------------------------------------

OPIOID = {
    "fixture": "opioid_35m",
    "arms": ["untreated", "oxygen", "naloxone", "oxygen_and_naloxone", "delayed_naloxone", "wait"],
    "causal_order": ["central_availability", "respiratory_rate", "ventilation", "paco2", "spo2"],
    "naloxone_writes_only": "central_availability",
    "oxygen_writes_only": "fio2",
    "reached_through_a_certified_reader": "sympathetic_drive",
    "onset_note": "derived readings are functions of the minute's state, so the chain is ordered by the graph and "
                  "starts in the minute of activation: no reading moves before it and none overtakes its cause",
    "oxygen_onset_note": "oxygen ordered at minute m changes the reading at m + 1 (the asymmetry TD-130 (39) declares)",
    "status": "READY_WITH_REGION",
    "verdict": "OPIOID_MANAGEMENT_CAUSALITY_READY",
}

# C5 -----------------------------------------------------------------------------------------------------------------

ASTHMA = {
    "cases": ["asthma_49m", "asthma_24f"],
    "region_used": (0.0, 0.060621),
    "asthma_specific_retuning": False,
    #: Las sondas PROPIAS de la etapa P2S-3, vueltas a correr con el enlace declarado en cada testigo.
    "probes_unchanged": ["arrival", "writer_semantics", "oxygen", "direct_g", "collapse", "consciousness"],
    "probe_conditions_that_change_with_the_link": {
        "untreated": ["delivery_index", "hr", "spo2", "states_identical_but_mechanics"],
        "relief": ["rr_spo2_hr_unchanged"],
        "drive": "REFUSED",
        "heart_rate": ["gains_untouched"],
    },
    "why_they_change": {
        "untreated": "P2S-3 states that ONLY the mechanics move. With the link declared the SpO2 follows the PaCO2, "
                     "and through it the delivery and (by the certified acute-deficit reader) the heart rate: that "
                     "is what the link is, and P2T-5 certified it at full transmission",
        "relief": "a structural relief of the mechanics now reaches the SpO2, upwards: the end-to-end chain",
        "heart_rate": "the condition compares every profile field with the common profile; the witness declares "
                      "two fields, the quotient and the fraction, and nothing else",
        "drive": "the probe declares a hypoxaemic drive, and P2T-5's invariant refuses it together with the link "
                 "(HYPOXEMIC_FEEDBACK_LOOP_DEFERRED): a certified refusal, not a failure",
    },
    "ventilation_chain_bit_identical": True,
    "verdict": "RESPIRATORY_TRANSMISSION_GENERALIZES",
    "verdict_caveat": "the same region, with no narrowing: asthma never binds it. Read strictly, three P2S-3 probe "
                      "conditions are no longer true once ANY non-zero transmission is declared; they are the "
                      "pre-link statement the link replaces, and they change in the declared direction",
}

# C6 -----------------------------------------------------------------------------------------------------------------

EDUCATIONAL_CONTRAST = {
    "fixture": "opioid_35m", "witness": "CENTER_REFERENCE",
    "arms": {"untreated": "no action", "oxygen": "oxygen support from minute 10",
             "naloxone": "central-drive reversal at minute 20"},
    "channels": ["respiratory_rate", "ventilation", "paco2", "spo2", "delivery_rel"],
    "distinguishing_channels": ["respiratory_rate", "ventilation", "paco2"],
    "not_distinguishing_alone": ["spo2", "delivery_rel"],
    "statement": "oxygen support raises the saturation and the delivery while the rate keeps falling and the PaCO2 "
                 "keeps rising; the reversal raises the rate and the ventilation, lowers the PaCO2 and raises the "
                 "saturation downstream. At every reading after both, oxygen shows MORE saturation with WORSE "
                 "ventilation, so the saturation alone does not tell the two apart",
    "is_a_recommendation_for_real_patients": False,
}

# C7 -----------------------------------------------------------------------------------------------------------------

DECONGESTION_DECISION = {
    "quantity": "PulmonaryEdema decongestion rate, EdemaCongestion.decongestion_per_min (lung water removed per "
                "simulated minute once a decongestive treatment has begun)",
    "region": (0.0025, 0.01),
    "witnesses": {"LOW": 0.0025, "CENTER_REFERENCE": 0.005, "HIGH": 0.01},
    "classification": "DEVELOPMENT_TEST_REGION",
    "confidence": 0.82,
    "rationale": "the interval is the family's own lung-water rate span, declared in P2P-1 before any run "
                 "(edema_migration.PROGRESSION, a factor of two either side of its middle), and its middle is the "
                 "only decongestion rate the repository states (edema_migration.DECONGESTION, SYNTHETIC_ONLY). The "
                 "region is wanted to TEST CAUSALITY, and every verdict of the generic contract -- direction, "
                 "temporality, specificity, dose ordering, reversibility, cost of delay -- is the same at its three "
                 "witnesses and at rates 2.5 times lower and 2 times higher, so the conclusion does not depend on "
                 "where in the region the truth lies. The arrival floor (L_rev = 0) bounds the effect at any rate",
    "evidence": ["edema_migration.PROGRESSION = (0.0025, 0.005, 0.01)", "edema_migration.DECONGESTION per_min = 0.005",
                 "edema_migration.decongestion(): back to arrival and never beyond, V and P unchanged (certified)",
                 "the case authors that an improvement is expected after treatment, and no value after arrival",
                 "test_p3_141i: the same contract verdicts from 0.001 to 0.02 per minute"],
    "uncertainty": "no post-arrival value is authored (INSUFFICIENT_AUTHORED_TRUTH), so the real time course of the "
                   "recovery is unknown and its magnitude is NOT claimed; one case only; the family writer has one "
                   "rate, so two therapies are not distinguished and a second order adds nothing; the respiratory "
                   "rate does not read lung water in this profile; venodilation, afterload and diuresis of volume "
                   "are not represented",
    "falsifier": "an authored observation after treatment (a saturation or a congestion finding at a stated time) "
                 "that implies a rate outside the interval; an authored statement that treatment should not return "
                 "to the arrival congestion, or should improve beyond it (L_rev other than 0); or any witness "
                 "breaking an item of the generic contract",
    "is_clinical_truth": False,
    "is_a_dose": False,
    "adopted_in_the_committed_profile": False,
}

EDEMA = {
    "fixture": "pulmonary_edema_58m",
    "path": ["decongestive order (diuretic, nitroglycerin, nitroglycerin_bolus)",
             "DecongestiveTreatment(id, begins_at_minute): a signal, writes nothing",
             "EdemaCongestion hears it: stops progressing, removes lung water at its rate, never below arrival",
             "L (state)", "G (state, the common L -> G coupling)", "SpO2 and delivery (derived, common)"],
    "exposure": "PulmonaryEdemaAdapter.development(witness): a separate offline adapter. The registered adapter is "
                "built with no rate and keeps the decongestive orders as declared gaps, so nothing changes by default",
    "common_core_changed": False,
    "arms": ["untreated", "oxygen", "decongestion", "oxygen_and_decongestion", "delayed_decongestion", "wait"],
    "decongestion_writes_only": "L",
    "oxygen_touches_lung_water": False,
    "respiratory_rate_follows": False,
    "status": "READY_WITH_REGION",
    "verdict": "PULMONARY_EDEMA_MANAGEMENT_CAUSALITY_READY",
}

#: Defecto encontrado y corregido al medir C7 y C9.
OXYGEN_SILENT_DROP = {
    "found": "the oedema, embolism and asthma adapters listed oxygen in ``maps`` and inherited a base method that "
             "built no contributor: an oxygen order was neither applied nor declared as a gap",
    "consequence": "FD-P3-100 said oxygen was mapped and causally correct in those three families; through the "
                   "Phase-3 adapter path it had no effect at all",
    "fix": "the base adapter builds the Oxygen it declares, and declares -- never drops -- any other kind it lists "
           "and cannot build",
    "scope": "offline shadow adapters only (none of the three is live); no committed profile and no core file changed",
}

# C8 -----------------------------------------------------------------------------------------------------------------

ACS = {
    "audited": ["clinical_core.legacy_adapter.anchors_from_legacy", "clinical_core.legacy_adapter.FAMILY_CASE_PARAMETER_RULES",
                "clinical_core.acs_reference.anchors", "clinical_core.migration_authority.canonical_arrival",
                "the ACS family adapter's anchors()", "the GI family adapter's anchors()"],
    "finding": "the only certified mapping from a live encounter state to arrival anchors refuses every family but "
               "GI: FAMILY_CASE_PARAMETER_RULES holds no rule for ACS (P2D-8). The ACS reference returns the "
               "arrival of ONE authored case and does not read the encounter",
    "case_parameters_with_no_live_rule": ["arrival_delivery_ratio", "arrival_lactate_excess", "arrival_oxygen_debt",
                                          "intrinsic_sinus_rate", "pump_reserve"],
    "what_closing_it_needs": "a rule that derives those five case parameters from the live state of an ACS "
                             "encounter, for every ACS variant the engine authors: new clinical semantics. For the "
                             "single declared case alone, a guarded identity (use the reference only when the live "
                             "arrival equals the authored one) would need no new clinical semantics, but it is a "
                             "new mapping rule: a methodological decision, not taken here",
    "offline_management_chain": "CAUSALLY_READY",
    "live_shadow": False,
    "authority_changed": False,
    "verdict": "ACS_ARRIVAL_MAPPING_REQUIRES_NEW_SEMANTICS",
}

# C9 -----------------------------------------------------------------------------------------------------------------

CONTRACT = ("DIRECTION", "TEMPORALITY", "CAUSAL_SPECIFICITY", "MAGNITUDE_PLAUSIBILITY", "DOSE_ORDERING",
            "REVERSIBILITY", "TIME_WITHOUT_ACTION", "CROSS_FAMILY_CONSISTENCY", "SAFETY")

READINESS = {
    "gi_bleed": {"mechanism": "volume / haemorrhage", "defining_intervention": "transfusion (also fluid, source control)",
                 "primary_state_channel": "V", "status": "CAUSALLY_READY", "complete_pathway": True,
                 "not_applicable": ["REVERSIBILITY"], "live_shadow": True, "depends_on_a_development_region": False},
    "acs": {"mechanism": "pump / reperfusion", "defining_intervention": "reperfusion, on the engine's own clock",
            "primary_state_channel": "P", "status": "CAUSALLY_READY", "complete_pathway": True,
            "not_applicable": ["DOSE_ORDERING", "REVERSIBILITY"], "live_shadow": False,
            "depends_on_a_development_region": False,
            "note": "complete offline; not in the live list (C8: no certified live arrival mapping)"},
    "opioid": {"mechanism": "central drive / ventilation", "defining_intervention": "naloxone",
               "primary_state_channel": "central_availability", "status": "READY_WITH_REGION",
               "complete_pathway": True, "not_applicable": [], "live_shadow": False,
               "depends_on_a_development_region": True,
               "note": "the last link (PaCO2 -> SpO2) exists only with the transmission declared; the committed "
                       "profile keeps it off, and the witnesses are declared in tests, not in the adapter"},
    "pulmonary_edema": {"mechanism": "congestion / decongestion", "defining_intervention": "decongestive treatment",
                        "primary_state_channel": "L", "status": "READY_WITH_REGION", "complete_pathway": True,
                        "not_applicable": [], "live_shadow": False, "depends_on_a_development_region": True,
                        "note": "through the development adapter only; the registered adapter keeps the gap"},
    "asthma": {"mechanism": "mechanics", "defining_intervention": "bronchodilator",
               "primary_state_channel": "mechanics_efficiency", "status": "MISSING_TREATMENT_WRITER",
               "complete_pathway": False, "not_applicable": [], "live_shadow": False,
               "depends_on_a_development_region": False,
               "note": "BRONCHODILATOR_WRITER_DEFERRED in the core. A structural relief of the mechanics already "
                       "reaches ventilation and, with the transmission declared, oxygenation: the mechanism is "
                       "there, the treatment writer and its clinical semantics are not"},
    "pulmonary_embolism": {"mechanism": "obstruction", "defining_intervention": "anticoagulation / thrombolysis",
                           "primary_state_channel": "P", "status": "MISSING_COMMON_MECHANISM",
                           "complete_pathway": False, "not_applicable": [], "live_shadow": False,
                           "depends_on_a_development_region": False,
                           "note": "the family writer takes no treatment parameter: a mechanism is missing, not a mapping"},
}

# C10 ----------------------------------------------------------------------------------------------------------------

CHECKPOINT = {
    "threshold": 4,
    "counting_rule": "a family counts when its DEFINING management intervention has an end-to-end causal chain "
                     "(treatment -> primary state channel -> downstream observable -> temporality -> dose ordering "
                     "or cost of delay) that passes the generic contract; two families that share a primary state "
                     "channel count once",
    "complete_pathways": ["gi_bleed", "acs", "opioid", "pulmonary_edema"],
    "complete_pathway_count": 4,
    "incomplete": {"asthma": "MISSING_TREATMENT_WRITER", "pulmonary_embolism": "MISSING_COMMON_MECHANISM"},
    "pathways_that_depend_on_a_development_region": ["opioid", "pulmonary_edema"],
    "live_shadow_families": ["gi_bleed"],
    "verdict": "A_MULTIFAMILY_MANAGEMENT_CAUSALITY_VALIDATED_FOR_DEVELOPMENT",
    "what_the_verdict_is": "SIMULATION readiness for development: four mechanistically distinct management "
                           "pathways are causally complete in the certified shadow core, offline",
    "is_resident_deployment_readiness": False,
    "is_clinical_validation": False,
}

#: C10-1: el camino mas corto y seguro hacia una REVISION de preparacion para piloto con residentes. Solo diseno.
PILOT_READINESS_REVIEW_PATH = {
    "is_design_only": True,
    "modifies_the_frozen_first_pilot": False,
    "simulation_readiness": "reached for development (CHECKPOINT): the physiology answers management causally in "
                            "four distinct mechanisms, in shadow, with no authority",
    "resident_deployment_readiness": "NOT reached and not claimed: every gate below is open",
    "remaining_gates": [
        {"gate": "runtime exposure", "open": "the common core has no runtime authority and only GI runs live in "
                                             "shadow; opioid and oedema run offline, behind development regions"},
        {"gate": "UI exposure", "open": "nothing the common core computes is shown to a resident; what would be "
                                        "shown, and how it differs from the engine's reading, is undecided"},
        {"gate": "trace capture", "open": "the shadow record exists and is joined to the ledger for GI; the same "
                                          "capture is not exercised live for any other family"},
        {"gate": "scoring isolation", "open": "scoring reads the engine only, and must provably keep doing so"},
        {"gate": "faculty review", "open": "two development regions carry two of the four pathways; neither has a "
                                           "faculty-approved value or region, and R is still a synthetic reference"},
        {"gate": "case selection", "open": "one or two authored cases per family; no selection rule for a second pilot"},
        {"gate": "failure visibility", "open": "a shadow failure is recorded and never reaches the encounter; what "
                                               "a resident-facing failure looks like is undesigned"},
        {"gate": "rollback", "open": "the flag turns the shadow off; a rollback of an authoritative core is undesigned"},
        {"gate": "resident-facing safeguards", "open": "none designed: no resident sees the common core today"},
    ],
    "shortest_safe_next_step": "a faculty decision on the two development regions (adopt as a declared region, "
                               "replace, or keep as test-only), because every later gate depends on which "
                               "physiology is the one being exposed",
}

#: C10: lo que sigue, ordenado. El paquete mas corto primero.
ROADMAP = [
    {"package": "faculty decision on the two development regions", "why": "two of the four pathways stand on them",
     "architecture_cost": "none", "risk": "low"},
    {"package": "declare the transmission witnesses in the opioid and asthma adapters as named development "
                "snapshots", "why": "today they are declared in tests; the adapter path cannot run them by name",
     "architecture_cost": "small, Phase-3 layer only", "risk": "low"},
    {"package": "asthma bronchodilator writer", "why": "a fifth distinct mechanism; the relief already propagates "
                                                        "end to end, only the writer's clinical semantics are missing",
     "architecture_cost": "one family writer, no common physiology", "risk": "medium (a clinical semantics decision)"},
    {"package": "ACS live arrival mapping", "why": "a second live shadow family",
     "architecture_cost": "a certified case-parameter rule", "risk": "medium (methodological)"},
    {"package": "embolism treatment mechanism", "why": "the sixth family",
     "architecture_cost": "new common physiology", "risk": "high; not authorized"},
]

DEVELOPMENT_TEST_DECISIONS = [
    {"quantity": "hypoventilation_oxygenation_transmission_fraction, with respiratory_quotient = 0.8",
     "region": (0.0, 0.060621), "witnesses": {"LOW": 0.015, "CENTER_REFERENCE": 0.03, "HIGH": 0.06},
     "classification": "DEVELOPMENT_TEST_REGION", "confidence": 0.84,
     "rationale": "it is the exact preimage, under the certified equation, of the faculty development target "
                  "(untreated SpO2 at minute 60 in [78, 88] % on opioid_35m), derived twice and not chosen; inside "
                  "it the ventilatory correction moves the oxygenation visibly, and asthma shifts by less than one "
                  "point with its ventilation bit-identical",
     "uncertainty": "only f / R is identified and R is a synthetic reference; one case binds the bound and the "
                    "ceiling does not bind; f = 0 is in the region but expresses nothing; three P2S-3 probe "
                    "conditions are superseded by any non-zero transmission",
     "falsifier": "a faculty target that the preimage does not contain; a certified asthma invariant other than "
                  "the pre-link ones failing inside the region; or the indirect loop waking below the bound",
     "is_clinical_truth": False},
    {"quantity": "PulmonaryEdema decongestion rate, EdemaCongestion.decongestion_per_min",
     "region": DECONGESTION_DECISION["region"], "witnesses": DECONGESTION_DECISION["witnesses"],
     "classification": "DEVELOPMENT_TEST_REGION", "confidence": DECONGESTION_DECISION["confidence"],
     "rationale": DECONGESTION_DECISION["rationale"], "uncertainty": DECONGESTION_DECISION["uncertainty"],
     "falsifier": DECONGESTION_DECISION["falsifier"], "is_clinical_truth": False},
]

# <measured>
MEASURED = {'region': {'opioid_35m': {'spo2_60_at_f0': 80.0,
                           'delta_paco2_60': 24.210373,
                           'f_upper_by_formula': 0.060621,
                           'f_upper_by_bisection': 0.060621,
                           'spo2_60_at_f1': 25.249192,
                           'spo2_60_at_witnesses': {'LOW': 79.525102,
                                                    'CENTER_REFERENCE': 79.037289,
                                                    'HIGH': 78.021602}},
            'opioid_67f': {'spo2_60_at_f0': 84.0,
                           'delta_paco2_60': 21.403373,
                           'f_upper_by_formula': 0.233153,
                           'f_upper_by_bisection': 0.233153,
                           'spo2_60_at_f1': 37.216489,
                           'spo2_60_at_witnesses': {'LOW': 83.677136,
                                                    'CENTER_REFERENCE': 83.346507,
                                                    'HIGH': 82.661181}},
            'asthma_49m': {'spo2_60_at_f0': 89.0,
                           'delta_paco2_60': 10.065786,
                           'f_upper_by_formula': 1.119209,
                           'f_upper_by_bisection': None,
                           'spo2_60_at_f1': 79.651141,
                           'spo2_60_at_witnesses': {'LOW': 88.904395,
                                                    'CENTER_REFERENCE': 88.807759,
                                                    'HIGH': 88.611342}},
            'asthma_24f': {'spo2_60_at_f0': 90.0,
                           'delta_paco2_60': 10.779447,
                           'f_upper_by_formula': 1.201341,
                           'f_upper_by_bisection': None,
                           'spo2_60_at_f1': 80.883438,
                           'spo2_60_at_witnesses': {'LOW': 89.909042,
                                                    'CENTER_REFERENCE': 89.817048,
                                                    'HIGH': 89.629903}}},
 'opioid': {'LOW': {'untreated': {'respiratory_rate': 3.821, 'ventilation': 0.369, 'paco2': 108.336, 'spo2': 79.222},
                    'oxygen': {'respiratory_rate': 3.821, 'ventilation': 0.369, 'paco2': 108.336, 'spo2': 85.176},
                    'naloxone': {'respiratory_rate': 15.234, 'ventilation': 1.472, 'paco2': 27.176, 'spo2': 80.791},
                    'oxygen_and_naloxone': {'respiratory_rate': 15.234,
                                            'ventilation': 1.472,
                                            'paco2': 27.176,
                                            'spo2': 86.233},
                    'delayed_naloxone': {'respiratory_rate': 14.851,
                                         'ventilation': 1.435,
                                         'paco2': 27.877,
                                         'spo2': 80.778},
                    'wait': {'respiratory_rate': 3.821, 'ventilation': 0.369, 'paco2': 108.336, 'spo2': 79.222},
                    'respiratory_rate_area': {'naloxone': 1096.975,
                                              'delayed_naloxone': 678.544,
                                              'untreated': 433.531}},
            'CENTER_REFERENCE': {'untreated': {'respiratory_rate': 3.821,
                                               'ventilation': 0.369,
                                               'paco2': 108.336,
                                               'spo2': 78.409},
                                 'oxygen': {'respiratory_rate': 3.821,
                                            'ventilation': 0.369,
                                            'paco2': 108.336,
                                            'spo2': 84.629},
                                 'naloxone': {'respiratory_rate': 15.234,
                                              'ventilation': 1.472,
                                              'paco2': 27.176,
                                              'spo2': 81.546},
                                 'oxygen_and_naloxone': {'respiratory_rate': 15.234,
                                                         'ventilation': 1.472,
                                                         'paco2': 27.176,
                                                         'spo2': 86.741},
                                 'delayed_naloxone': {'respiratory_rate': 14.851,
                                                      'ventilation': 1.435,
                                                      'paco2': 27.877,
                                                      'spo2': 81.521},
                                 'wait': {'respiratory_rate': 3.821,
                                          'ventilation': 0.369,
                                          'paco2': 108.336,
                                          'spo2': 78.409},
                                 'respiratory_rate_area': {'naloxone': 1096.975,
                                                           'delayed_naloxone': 678.544,
                                                           'untreated': 433.531}},
            'HIGH': {'untreated': {'respiratory_rate': 3.821, 'ventilation': 0.369, 'paco2': 108.336, 'spo2': 76.674},
                     'oxygen': {'respiratory_rate': 3.821, 'ventilation': 0.369, 'paco2': 108.336, 'spo2': 83.461},
                     'naloxone': {'respiratory_rate': 15.234, 'ventilation': 1.472, 'paco2': 27.176, 'spo2': 82.954},
                     'oxygen_and_naloxone': {'respiratory_rate': 15.234,
                                             'ventilation': 1.472,
                                             'paco2': 27.176,
                                             'spo2': 87.691},
                     'delayed_naloxone': {'respiratory_rate': 14.851,
                                          'ventilation': 1.435,
                                          'paco2': 27.877,
                                          'spo2': 82.909},
                     'wait': {'respiratory_rate': 3.821, 'ventilation': 0.369, 'paco2': 108.336, 'spo2': 76.674},
                     'respiratory_rate_area': {'naloxone': 1096.975,
                                               'delayed_naloxone': 678.544,
                                               'untreated': 433.531}}},
 'asthma': {'asthma_49m': {'LOW': {'spo2_shift_60': -0.0956, 'spo2_shift_120': -0.2025, 'spo2_min': 88.7975},
                           'CENTER_REFERENCE': {'spo2_shift_60': -0.1922,
                                                'spo2_shift_120': -0.4096,
                                                'spo2_min': 88.5904},
                           'HIGH': {'spo2_shift_60': -0.3887, 'spo2_shift_120': -0.8382, 'spo2_min': 88.1618}},
            'asthma_24f': {'LOW': {'spo2_shift_60': -0.091, 'spo2_shift_120': -0.1859, 'spo2_min': 89.8141},
                           'CENTER_REFERENCE': {'spo2_shift_60': -0.183,
                                                'spo2_shift_120': -0.3762,
                                                'spo2_min': 89.6238},
                           'HIGH': {'spo2_shift_60': -0.3701, 'spo2_shift_120': -0.7702, 'spo2_min': 89.2298}}},
 'contrast': {'untreated': {'5': {'respiratory_rate': 5.851,
                                  'ventilation': 0.565,
                                  'paco2': 70.751,
                                  'spo2': 79.932,
                                  'delivery_rel': 0.999},
                            '15': {'respiratory_rate': 5.565,
                                   'ventilation': 0.538,
                                   'paco2': 74.388,
                                   'spo2': 79.79,
                                   'delivery_rel': 0.997},
                            '25': {'respiratory_rate': 5.293,
                                   'ventilation': 0.511,
                                   'paco2': 78.212,
                                   'spo2': 79.64,
                                   'delivery_rel': 0.995},
                            '30': {'respiratory_rate': 5.162,
                                   'ventilation': 0.499,
                                   'paco2': 80.197,
                                   'spo2': 79.561,
                                   'delivery_rel': 0.995},
                            '45': {'respiratory_rate': 4.788,
                                   'ventilation': 0.463,
                                   'paco2': 86.459,
                                   'spo2': 79.311,
                                   'delivery_rel': 0.991},
                            '60': {'respiratory_rate': 4.442,
                                   'ventilation': 0.429,
                                   'paco2': 93.21,
                                   'spo2': 79.037,
                                   'delivery_rel': 0.988},
                            '90': {'respiratory_rate': 3.821,
                                   'ventilation': 0.369,
                                   'paco2': 108.336,
                                   'spo2': 78.409,
                                   'delivery_rel': 0.98}},
              'oxygen': {'5': {'respiratory_rate': 5.851,
                               'ventilation': 0.565,
                               'paco2': 70.751,
                               'spo2': 79.932,
                               'delivery_rel': 0.999},
                         '15': {'respiratory_rate': 5.565,
                                'ventilation': 0.538,
                                'paco2': 74.388,
                                'spo2': 85.559,
                                'delivery_rel': 1.069},
                         '25': {'respiratory_rate': 5.293,
                                'ventilation': 0.511,
                                'paco2': 78.212,
                                'spo2': 85.458,
                                'delivery_rel': 1.068},
                         '30': {'respiratory_rate': 5.162,
                                'ventilation': 0.499,
                                'paco2': 80.197,
                                'spo2': 85.405,
                                'delivery_rel': 1.068},
                         '45': {'respiratory_rate': 4.788,
                                'ventilation': 0.463,
                                'paco2': 86.459,
                                'spo2': 85.236,
                                'delivery_rel': 1.065},
                         '60': {'respiratory_rate': 4.442,
                                'ventilation': 0.429,
                                'paco2': 93.21,
                                'spo2': 85.052,
                                'delivery_rel': 1.063},
                         '90': {'respiratory_rate': 3.821,
                                'ventilation': 0.369,
                                'paco2': 108.336,
                                'spo2': 84.629,
                                'delivery_rel': 1.058}},
              'naloxone': {'5': {'respiratory_rate': 5.851,
                                 'ventilation': 0.565,
                                 'paco2': 70.751,
                                 'spo2': 79.932,
                                 'delivery_rel': 0.999},
                           '15': {'respiratory_rate': 5.565,
                                  'ventilation': 0.538,
                                  'paco2': 74.388,
                                  'spo2': 79.79,
                                  'delivery_rel': 0.997},
                           '25': {'respiratory_rate': 9.604,
                                  'ventilation': 0.928,
                                  'paco2': 43.106,
                                  'spo2': 80.974,
                                  'delivery_rel': 1.012},
                           '30': {'respiratory_rate': 12.003,
                                  'ventilation': 1.16,
                                  'paco2': 34.492,
                                  'spo2': 81.286,
                                  'delivery_rel': 1.016},
                           '45': {'respiratory_rate': 14.625,
                                  'ventilation': 1.413,
                                  'paco2': 28.307,
                                  'spo2': 81.506,
                                  'delivery_rel': 1.019},
                           '60': {'respiratory_rate': 15.122,
                                  'ventilation': 1.461,
                                  'paco2': 27.377,
                                  'spo2': 81.539,
                                  'delivery_rel': 1.019},
                           '90': {'respiratory_rate': 15.234,
                                  'ventilation': 1.472,
                                  'paco2': 27.176,
                                  'spo2': 81.546,
                                  'delivery_rel': 1.019}}},
 'edema': {'LOW': {'rate_per_min': 0.0025,
                   'back_to_arrival_at_minute': 79,
                   'spo2_at_180': {'untreated': 77.8276,
                                   'oxygen': 82.1548,
                                   'decongestion': 81.0,
                                   'oxygen_and_decongestion': 86.7,
                                   'delayed_decongestion': 80.6736,
                                   'wait': 77.8276},
                   'lung_water_at_180': {'untreated': 0.6345,
                                         'oxygen': 0.6345,
                                         'decongestion': 0.0,
                                         'oxygen_and_decongestion': 0.0,
                                         'delayed_decongestion': 0.0653,
                                         'wait': 0.6345},
                   'spo2_area': {'untreated': 14257.5395,
                                 'decongestion': 14553.6095,
                                 'delayed_decongestion': 14396.62}},
           'CENTER_REFERENCE': {'rate_per_min': 0.005,
                                'back_to_arrival_at_minute': 55,
                                'spo2_at_180': {'untreated': 77.8276,
                                                'oxygen': 82.1548,
                                                'decongestion': 81.0,
                                                'oxygen_and_decongestion': 86.7,
                                                'delayed_decongestion': 81.0,
                                                'wait': 77.8276},
                                'lung_water_at_180': {'untreated': 0.6345,
                                                      'oxygen': 0.6345,
                                                      'decongestion': 0.0,
                                                      'oxygen_and_decongestion': 0.0,
                                                      'delayed_decongestion': 0.0,
                                                      'wait': 0.6345},
                                'spo2_area': {'untreated': 14257.5395,
                                              'decongestion': 14561.1829,
                                              'delayed_decongestion': 14434.3592}},
           'HIGH': {'rate_per_min': 0.01,
                    'back_to_arrival_at_minute': 43,
                    'spo2_at_180': {'untreated': 77.8276,
                                    'oxygen': 82.1548,
                                    'decongestion': 81.0,
                                    'oxygen_and_decongestion': 86.7,
                                    'delayed_decongestion': 81.0,
                                    'wait': 77.8276},
                    'lung_water_at_180': {'untreated': 0.6345,
                                          'oxygen': 0.6345,
                                          'decongestion': 0.0,
                                          'oxygen_and_decongestion': 0.0,
                                          'delayed_decongestion': 0.0,
                                          'wait': 0.6345},
                    'spo2_area': {'untreated': 14257.5395,
                                  'decongestion': 14565.369,
                                  'delayed_decongestion': 14460.5562}}},
 'contract': {'gi_bleed': {'DIRECTION': True,
                           'TEMPORALITY': True,
                           'CAUSAL_SPECIFICITY': True,
                           'MAGNITUDE_PLAUSIBILITY': True,
                           'DOSE_ORDERING': True,
                           'REVERSIBILITY': None,
                           'TIME_WITHOUT_ACTION': True,
                           'SAFETY': True},
              'acs': {'DIRECTION': True,
                      'TEMPORALITY': True,
                      'CAUSAL_SPECIFICITY': True,
                      'MAGNITUDE_PLAUSIBILITY': True,
                      'DOSE_ORDERING': None,
                      'REVERSIBILITY': None,
                      'TIME_WITHOUT_ACTION': True,
                      'SAFETY': True},
              'opioid': {'DIRECTION': True,
                         'TEMPORALITY': True,
                         'CAUSAL_SPECIFICITY': True,
                         'MAGNITUDE_PLAUSIBILITY': True,
                         'DOSE_ORDERING': True,
                         'REVERSIBILITY': True,
                         'TIME_WITHOUT_ACTION': True,
                         'SAFETY': True},
              'pulmonary_edema': {'DIRECTION': True,
                                  'TEMPORALITY': True,
                                  'CAUSAL_SPECIFICITY': True,
                                  'MAGNITUDE_PLAUSIBILITY': True,
                                  'DOSE_ORDERING': True,
                                  'REVERSIBILITY': True,
                                  'TIME_WITHOUT_ACTION': True,
                                  'SAFETY': True}},
 'moved_state_channels': {'gi_bleed': ['D', 'V', 'sympathetic_drive'],
                          'acs': ['D', 'L', 'P', 'T', 'sympathetic_drive'],
                          'opioid': ['central_availability', 'sympathetic_drive'],
                          'pulmonary_edema': ['G', 'L', 'sympathetic_drive']}}
# </measured>


def all_records() -> dict:
    return {name: value for name, value in globals().items() if name.isupper()}
