"""The pilot freeze: which cases the first pilot runs, on what, and what each one cannot do.

Phase 0 (0J, 0K), pre-pilot measurement safety, 2026-10-06. The acceptance battery
(``pilot_acceptance``, ``test_phase0_acceptance_battery.py`` and
``test_phase0_acceptance_page.py``) runs every bank case through the scenarios of the Phase 0
request (A-K, terminal course, recovery, resume, replay, ledger, provenance, observation,
guards). What it found is declared here, once, and read by three things:

* the case selection: an excluded case is never drawn for a resident and never offered to a
  faculty member directing one (``cognitive_generator``, ``encounter_directives``);
* the analysis: a course event the simulator decides for a case never counts against the
  resident (``rubric_screening.may_support_negative_feedback``, rule D);
* the manifest: ``docs/revision/PILOT_FREEZE_MANIFEST.md`` is generated from this module
  (``tools_pilot_freeze.py``), so the document cannot drift from what the code enforces.

A case is EXCLUDED when an assessed management decision depends on a behaviour of the engine
that is broken and cannot be fixed safely within Phase 0, or when the Trace cannot tell that
limitation from the resident's doing. It is ACCEPTED WITH A DECLARED LIMITATION when the
limitation is real, is declared, and the guards keep it from being read as the resident's.
Nothing here is a clinical judgement: every limitation names what the engine does, and the
clinical questions it raises are the faculty's (docs/revision/PHASE_0_PILOT_SAFETY_REPORT.md).
"""
from __future__ import annotations

FREEZE_ID = "pilot-freeze-phase0-2026-10-06"
STATUSES = ("ACCEPT", "ACCEPT WITH DECLARED LIMITATION", "EXCLUDE")

#: Limitations that hold in every case of the bank, with how the record keeps each one from
#: being read as the resident's.
GLOBAL_LIMITATIONS = {
    "G-RESUSCITATION": {
        "text": "Resuscitation is not modelled: a cardiac arrest is the end of what can be assessed. The page "
                "says so in the agreed words, later orders are TERMINAL_NOT_EXECUTABLE, and every decision "
                "whose window reaches past the arrest is NOT ASSESSABLE (rule E).",
        "affects_assessed": True, "guard": "rule E (resuscitation_not_modelled)"},
    "G-LATER-ORDERS": {
        "text": "An order for a later time ('in 30 minutes') is recorded and neither run nor scheduled "
                "(RECORDED_NOT_MODELLED, unsupported_future_execution); the resident is told to write it "
                "again when it is due.",
        "affects_assessed": True, "guard": "rule A (the kinds the plan names, or a wildcard)"},
    "G-STEP-120": {
        "text": "One step moves the clock at most 120 minutes; a longer wait is refused and explained "
                "(pilot_time_step_limit), never shortened.",
        "affects_assessed": False, "guard": "the refusal is recorded with its fate"},
    "G-READER-V3": {
        "text": "The order reader is frozen at V3. What it does not read is UNRECOGNIZED, with a receipt, "
                "and never disappears; it counts as a wildcard for every assessed omission in its window.",
        "affects_assessed": True, "guard": "rule A (wildcard) and rule D (an order not carried out)"},
    "G-STATIC-OBSERVATIONS": {
        "text": "History, collateral and the examination regions and studies the engine does not model are "
                "the case's authored values, declared static (observation_consistency.declaration); a "
                "static result reported in a turn is a limitation of that turn (observable_static).",
        "affects_assessed": False, "guard": "observable_static in the turn's limitations"},
    "G-HARM-NOT-MODELLED": {
        "text": "Several excesses and errors have no modelled harm (audit 8 D/E): crystalloid beyond need "
                "where the family has no lung to load, furosemide in septic hypotension, midazolam in "
                "severe asthma, repeated IM adrenaline, D50 or aspirin, repeated nebulised albuterol. The "
                "order runs with its fate; the absence of a consequence is the engine's, not evidence.",
        "affects_assessed": False, "guard": "no declared critical event reads these consequences"},
    "G-INTERRUPTIONS": {
        "text": "A wait stops at a declared engine event, at a systolic below 70 that fell 20 or more for "
                "2 minutes, or at a saturation below 85 that fell 5 or more for 2 minutes (event_provenance).",
        "affects_assessed": False, "guard": "every event carries its cause class and preventability"},
}

#: Limitations of one case or family, declared by what the battery observed.
CASE_LIMITATIONS = {
    "C-SCRIPTED-AV-BLOCK": {
        "text": "The complete AV block at minute 45 of the inferior infarct is scripted "
                "(SCRIPTED_NATURAL_HISTORY, NOT_PREVENTABLE_IN_SIMULATOR): it comes whatever is done.",
        "affects_assessed": False, "guard": "rule D: a scripted event never counts against the resident"},
    "C-SCRIPTED-VF": {
        "text": "Ventricular fibrillation is scripted at minute 120 of occlusion and prevented by reperfusion "
                "before it. Whether the reperfusion decision came in time is read from the decision, never "
                "from the scripted minute.",
        "affects_assessed": False, "guard": "rule D: a scripted event never counts against the resident"},
    "C-BIPHASIC": {
        "text": "The biphasic reaction is scripted 75 minutes after the first one settles "
                "(NOT_PREVENTABLE_IN_SIMULATOR) and stops a wait when it comes.",
        "affects_assessed": False, "guard": "rule D"},
    "C-GLUCAGON-INFUSION": {
        "text": "A glucagon infusion is not read (UNRECOGNIZED). Glucagon boluses, repeated IM adrenaline and "
                "an adrenaline infusion are modelled and hold the patient.",
        "affects_assessed": False, "guard": "rule A (wildcard) and rule D"},
    "C-BRADYCARDIA-DEFINITIVE": {
        "text": "By design the definitive treatment is not run: high-dose insulin (calcium-channel blocker), "
                "a glucagon infusion (beta blocker), insulin and dialysis (potassium); dopamine, "
                "isoproterenol and vasopressin are not read. What is modelled as a bridge: repeated antidote "
                "boluses, an adrenaline infusion and transcutaneous pacing. Phase 0 reads the arrest from "
                "the rate the monitor shows, which an adrenaline infusion lifts as well.",
        "affects_assessed": False, "guard": "rule A and rule D for an order the simulator did not carry out"},
    "C-INFRANODAL-BLOCK": {
        "text": "Atropine does nothing for the infranodal block, by design; pacing and an adrenaline infusion "
                "are modelled.",
        "affects_assessed": False, "guard": "none needed: the behaviour is the case's teaching point"},
    "C-SOURCE-CONTROL": {
        "text": "The urology consult (source control) is recorded and has no modelled physiological effect: "
                "after the first fluid the pressure drifts back.",
        "affects_assessed": False, "guard": "pyelo_no_source_control reads the decision, not its effect"},
    "C-LIMB-ARREST-13": {
        "text": "Untreated, the arterial limb bleed reaches the engine's arrest threshold at about minute 13; "
                "Phase 0 made that arrest a true one (it was announced while a pulse was shown).",
        "affects_assessed": True, "guard": "rule E: trauma_crystalloid_instead_of_blood is not assessable "
                                           "past the arrest"},
    "C-NO-THEATRE": {
        "text": "The definitive control of the haemothorax, an operating theatre, is not modelled. After the "
                "drain the patient bleeds to a true arrest at about minute 60 whatever is done (drain at "
                "minute 0, repeated transfusion, search for another source, surgery called). The assessed "
                "management after drainage (look again, decide theatre) and the case's own endpoint depend "
                "on that course.",
        "affects_assessed": True, "guard": "provenance ENGINE_LIMITATION; the case is excluded"},
}

_A = "ACCEPT"
_L = "ACCEPT WITH DECLARED LIMITATION"
_X = "EXCLUDE"

#: Every bank case of the pilot, with its decision and the limitations it carries beyond the
#: global ones. ``engine_limited_events``: course events the simulator decides in this case
#: and that never count against the resident (rule D).
CASES = {
    "pneumonia_46f": {"status": _L, "limitations": ["G-HARM-NOT-MODELLED"]},
    "pneumonia_83m": {"status": _L, "limitations": ["G-HARM-NOT-MODELLED"]},
    "pulmonary_edema_58m": {"status": _A, "limitations": []},
    "pulmonary_edema_75f": {"status": _A, "limitations": []},
    "acs_54m_inferior": {"status": _L, "limitations": ["C-SCRIPTED-AV-BLOCK", "C-SCRIPTED-VF"]},
    "acs_66f_nonst": {"status": _A, "limitations": []},
    "acs_61m_posterior": {"status": _L, "limitations": ["C-SCRIPTED-VF"]},
    "acs_52m_de_winter": {"status": _L, "limitations": ["C-SCRIPTED-VF"]},
    "acs_48m_wellens": {"status": _A, "limitations": []},
    "acs_70f_left_main": {"status": _L, "limitations": ["C-SCRIPTED-VF"]},
    "pulmonary_embolism_33f": {"status": _A, "limitations": []},
    "pulmonary_embolism_61m": {"status": _A, "limitations": []},
    "asthma_24f": {"status": _L, "limitations": ["G-HARM-NOT-MODELLED"]},
    "asthma_49m": {"status": _L, "limitations": ["G-HARM-NOT-MODELLED"]},
    "gi_bleed_57m": {"status": _L, "limitations": ["G-HARM-NOT-MODELLED"]},
    "gi_bleed_72f": {"status": _L, "limitations": ["G-HARM-NOT-MODELLED"]},
    "hypoglycemia_28m": {"status": _A, "limitations": []},
    "hypoglycemia_76f": {"status": _A, "limitations": []},
    "hypoglycemia_54m_thiamine": {"status": _A, "limitations": []},
    "opioid_35m": {"status": _A, "limitations": []},
    "opioid_67f": {"status": _A, "limitations": []},
    "anaphylaxis_29f": {"status": _L, "limitations": ["C-BIPHASIC", "G-HARM-NOT-MODELLED"]},
    "anaphylaxis_63m_betablocked": {"status": _L, "limitations": ["C-GLUCAGON-INFUSION"]},
    "renal_colic_34m": {"status": _A, "limitations": []},
    "obstructive_pyelonephritis_58f": {"status": _L, "limitations": ["C-SOURCE-CONTROL"]},
    "bradycardia_ccb_68m": {"status": _L, "limitations": ["C-BRADYCARDIA-DEFINITIVE"]},
    "bradycardia_avb3_78f": {"status": _L, "limitations": ["C-INFRANODAL-BLOCK"]},
    "bradycardia_bb_54f": {"status": _L, "limitations": ["C-BRADYCARDIA-DEFINITIVE"]},
    "bradycardia_hyperk_63m": {"status": _L, "limitations": ["C-BRADYCARDIA-DEFINITIVE"]},
    "trauma_limb_hemorrhage_27m": {"status": _L, "limitations": ["C-LIMB-ARREST-13"]},
    "trauma_hemothorax_41m": {"status": _X, "limitations": ["C-NO-THEATRE"],
                              "engine_limited_events": ["cardiac_arrest"],
                              "why_excluded": "An assessed management decision depends on a course the engine "
                                              "cannot run: the theatre is not modelled and, since Phase 0 made the "
                                              "arrest a true one, the patient arrests at about minute 60 whatever "
                                              "is done, so trauma_drained_and_never_looked_again (window 10-180) "
                                              "is never assessable. This departs from the pre-pilot closure "
                                              "(C-2026-10-02-08: no case excluded, the theatre declared as a limit "
                                              "while the arrest was only announced): the faculty decides between "
                                              "keeping it excluded, accepting it with the arrest declared, or "
                                              "representing the theatre."},
}

#: The legacy PS001 challenges no resident is assigned (Phase 0, 0C).
EXCLUDED_LEGACY_CHALLENGES = ("R1-03", "R1-04", "R2-01")

#: What the deployment must hold for the freeze to be the one tested.
RUNTIME_FLAGS = {
    ".streamlit/config.toml [runner] fastReruns": "false (Phase 0, 0D: a second click never starts a "
                                                  "concurrent run)",
    "MRS_OFFLINE_CASES": "1 (bank cases; no provider call during the encounter)",
    "MRS_PAID_GENERATION": "off",
    "MRS_FREE_GENERATION": "unset (free generation stays in the administrator's sandbox)",
    "MRS_DEFAULT_VARIANT": "unset (a pinned variant would bypass the case selection)",
    "MRS_REPLAY_CASE": "unset (a replayed case is outside the accepted list)",
    "MRS_CODE_VERSION": "the deployed commit (every encounter and every turn records it)",
    "MRS_IMAGE_REQUIRE_REVIEW": "on",
}


def status(variant_id):
    return (CASES.get(variant_id) or {}).get("status")


def excluded(variant_id):
    """True for a bank case the pilot never gives a resident."""
    return status(variant_id) == _X


def excluded_variants():
    return sorted(variant for variant, case in CASES.items() if case["status"] == _X)


def accepted_variants():
    return sorted(variant for variant, case in CASES.items() if case["status"] != _X)


def engine_limited_event(case_id, kind):
    """A course event the simulator decides in this case: it never counts against the resident."""
    return kind in ((CASES.get(case_id) or {}).get("engine_limited_events") or ())


def declared_engine_limits(variant_id):
    """What the case itself declares the engine cannot show or treat (pre-pilot closure, C-2026-10-02-08).

    Frozen with each encounter (``evaluation_basis``) and shown where the faculty evaluates with
    "Never count these against the resident"; the freeze names them and does not restate them.
    """
    from case_assessment_bank import CASES as DECLARATIONS
    return list((DECLARATIONS.get(variant_id) or {}).get("engine_limits") or ())


def case_versions(variant_id):
    """The case as the freeze accepted it: the bank's text and the assessment declaration.

    ``declaration`` is the fingerprint ``evaluation_basis.freeze`` stores with every encounter at
    launch, so an encounter can be checked against the freeze; ``case`` covers the case's text
    (``clinical_cases``). A change to either after the freeze changes the manifest, and
    ``test_phase0_pilot_freeze.py`` fails until the manifest is written again.
    """
    import clinical_cases
    import evaluation_basis
    from case_assessment_bank import CASES as DECLARATIONS
    return {"case": evaluation_basis.fingerprint(clinical_cases.variant_by_id(variant_id))[:12],
            "declaration": evaluation_basis.fingerprint(DECLARATIONS[variant_id])[:12]}


def limitations(variant_id):
    """The case's declared limitations (its own first), each with its text and guard."""
    out = []
    for key in (CASES.get(variant_id) or {}).get("limitations") or []:
        spec = CASE_LIMITATIONS.get(key) or GLOBAL_LIMITATIONS.get(key)
        out.append({"id": key, **spec})
    return out


def versions():
    """The versions the freeze names; the commit is the deployment's (MRS_CODE_VERSION)."""
    import event_provenance
    import order_ledger
    import trace_phase0
    from clinical_cases import CASE_BANK_VERSION
    from cognitive_generator import GENERATOR_VERSION
    from curriculum_runtime import RUNTIME_VERSION, PAYLOAD_VERSION
    from family_engine import EXECUTION_VERSION, FAMILY_ENGINE_VERSION
    return {
        "freeze_id": FREEZE_ID,
        "engine": f"family engine v{FAMILY_ENGINE_VERSION}, execution {EXECUTION_VERSION}",
        "case_bank": CASE_BANK_VERSION,
        "case_generator": GENERATOR_VERSION,
        "runtime": RUNTIME_VERSION,
        "payload": PAYLOAD_VERSION,
        "reader": "frozen at V3 (validation/BASELINES.md, 3d942ee); not modified by Phase 0",
        "trace_schema": "management_trace_v1 + " + trace_phase0.SCHEMA,
        "ledger_schema": order_ledger.LEDGER_SCHEMA,
        "event_provenance_schema": event_provenance.SCHEMA,
    }
