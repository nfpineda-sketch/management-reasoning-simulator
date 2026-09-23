"""Rubric coverage and critical events, declared per bank case.

Written against each case's own data: the studies named here are in its
investigations, the actions are ones the engine executes, and the examination
regions are ones the case authors. ``case_assessment.verify`` checks that, so a
declaration cannot drift into promising an opportunity the case does not offer.

Windows are clinical, not arbitrary: they state when the opportunity is open,
which is what separates an omission from a lack of opportunity.
"""


def _d(opportunity, expected, alternatives, window, **requires):
    return {"opportunity": opportunity, "expected": tuple(expected),
            "alternatives": tuple(alternatives), "window_min": window,
            "requires": {k: tuple(v) for k, v in requires.items()}}


def _event(event_id, kind, action, trigger, information_required, window,
           alternatives, evidence_required, exclusions, domains):
    return {"event_id": event_id, "kind": kind, "action": action, "trigger": trigger,
            "information_required": tuple(information_required), "window_min": window,
            "alternatives": tuple(alternatives), "evidence_required": evidence_required,
            "exclusions": tuple(exclusions), "domains": tuple(domains)}


# --- the antiplatelet omission, shared by every coronary case ----------------
def _aspirin_omission(window=(0, 30)):
    return _event(
        "acs_no_antiplatelet", "critical_omission",
        "No antiplatelet is given in a recognised acute coronary syndrome.",
        "The ECG is reported and the presentation is ischaemic, and no aspirin or P2Y12 "
        "inhibitor is executed within the window.",
        ["The 12-lead ECG result", "the presenting history"], window,
        ["A P2Y12 inhibitor when aspirin is contraindicated or refused, stated as such",
         "withholding it with a stated contraindication such as active bleeding or allergy"],
        "An executed antiplatelet action, or its absence across every executed turn in the window.",
        ["The encounter closed before the ECG was reported",
         "the interpreter refused the order and the resident was never told what it could accept"],
        ["D3"])


def _stress_test_event():
    return _event(
        "acs_provocation_test", "dangerous_action",
        "A provocation or stress test is ordered in an unstable coronary syndrome.",
        "A stress test is ordered while the presentation is an acute coronary syndrome.",
        ["The 12-lead ECG result", "the troponin result when it was requested"], (0, 180),
        ["Angiography, invasive assessment or specialist consultation",
         "scheduled outpatient testing stated as after this episode, not now"],
        "An executed or ordered stress test action in the record.",
        ["The order was considered in writing but never submitted as an order"],
        ["D3"])


_ACS_D1 = _d(
    "The arrival ECG carries the ischaemic pattern of this case; there is a priority to "
    "decide between opening the artery, treating, and investigating further.",
    ["Names the ischaemic pattern or the threat it represents within the window",
     "acts on it before pursuing unrelated investigation"],
    ["Naming the threat without the eponym", "acting first and naming it in the same turn"],
    (0, 20), studies=("ecg",))

_ACS_D2 = _d(
    "A 12-lead ECG, a troponin and a history that distinguishes this pattern from the "
    "others in the family are all available.",
    ["Requests the ECG and interprets it", "relates the troponin to the ECG and the symptoms"],
    ["Interpreting the ECG without requesting the troponin when the pattern is already an "
     "occlusion equivalent", "using POCUS as the second line of evidence"],
    (0, 30), studies=("ecg", "troponin", "pocus"))

_ACS_D4 = _d(
    "The engine runs a clock and responds to what is given: an antiplatelet, a nitrate or "
    "an opioid changes observables that can be checked.",
    ["States a reassessment interval", "checks the response to what was executed"],
    ["Reassessing with the ECG rather than the vitals", "a shorter interval than stated"],
    (10, 90), actions=("reassessment",))


def _acs(d3_opportunity, d3_expected, d3_alternatives, d5_opportunity, d5_expected,
         d5_alternatives, critical_events, d3_actions=("aspirin", "consult")):
    return {
        "domains": {
            "D1": _ACS_D1, "D2": _ACS_D2,
            "D3": _d(d3_opportunity, d3_expected, d3_alternatives, (0, 40), actions=d3_actions),
            "D4": _ACS_D4,
            "D5": _d(d5_opportunity, d5_expected, d5_alternatives, (15, 180),
                     actions=("consult", "disposition")),
        },
        "information": ("Arrival observables and the monitor", "the patient's own history",
                        "the 12-lead ECG and, where the case carries them, additional leads",
                        "laboratory, troponin, POCUS and chest radiograph"),
        "closure": "A disposition is decided, or the horizon of the encounter is reached.",
        "engine_limits": ("The engine does not perform angiography; a referral is recorded, "
                          "not its result.",
                          "Serial troponin requires a new sample and the encounter may close first."),
        "critical_events": critical_events,
    }


_REPERFUSION_D5 = (
    "The pattern is an occlusion: the decision is whether the artery is opened now and by "
    "whom, and what happens while that is arranged.",
    ["Arranges reperfusion or the specialist assessment that decides it",
     "states what is watched while it is arranged"],
    ["Thrombolysis with a stated reason when timely intervention is not available",
     "transfer stated as the reperfusion pathway"])

CASES = {
    "acs_54m_inferior": _acs(
        "An inferior ST-elevation infarction: antiplatelet therapy and the reperfusion "
        "pathway, with the preload caution an inferior territory carries.",
        ["Gives an antiplatelet", "arranges reperfusion or the consultation that decides it"],
        ["A P2Y12 inhibitor when aspirin is contraindicated",
         "withholding a nitrate, which in this territory is a defensible choice"],
        *_REPERFUSION_D5,
        (_aspirin_omission(), _stress_test_event())),

    "acs_66f_nonst": _acs(
        "Ischaemia without ST elevation: antiplatelet therapy and a monitored specialist "
        "assessment rather than immediate angiography.",
        ["Gives an antiplatelet", "arranges monitored specialist assessment"],
        ["Anticoagulation added to the antiplatelet",
         "stating that immediate angiography is not required here"],
        "Without ST elevation the decision is the level of monitoring and who assesses next, "
        "not an immediate cath lab activation.",
        ["Defines a monitored destination", "states what would change the urgency"],
        ["Escalating to immediate invasive assessment with a stated reason such as refractory pain"],
        (_aspirin_omission(), _stress_test_event())),

    "acs_61m_posterior": _acs(
        "An occlusion the standard 12-lead shows only as a mirror image: the antiplatelet "
        "and the reperfusion pathway, once posterior leads confirm it.",
        ["Gives an antiplatelet", "arranges reperfusion once the posterior pattern is recognised"],
        ["Acting on the mirror-image pattern without recording posterior leads, stated as such"],
        *_REPERFUSION_D5,
        (_aspirin_omission(), _stress_test_event())),

    "acs_52m_de_winter": _acs(
        "A proximal anterior occlusion whose pattern precedes ST elevation: the artery is "
        "opened now, not after waiting for the elevation.",
        ["Gives an antiplatelet", "arranges reperfusion without waiting for ST elevation"],
        ["Stating the equivalence explicitly and escalating on that basis"],
        *_REPERFUSION_D5,
        (_aspirin_omission(), _stress_test_event())),

    "acs_48m_wellens": _acs(
        "A critical stenosis that is transiently reperfused: the antiplatelet and scheduled "
        "angiography, and never a provocation test.",
        ["Gives an antiplatelet", "arranges inpatient or scheduled angiography"],
        ["Admitting for monitoring with angiography stated as the plan"],
        "The patient feels well and the troponin is not raised. The decision is what happens "
        "next for a lesion that is not currently occluding, and what must not be done.",
        ["Keeps the patient for definitive assessment rather than discharging",
         "states that provocation testing is unsafe here"],
        ["Admitting without naming the test that must be avoided"],
        (_aspirin_omission(), _stress_test_event())),

    "acs_70f_left_main": _acs(
        "A proximal lesion behind a diffuse pattern, in a patient who is already "
        "hypoperfused: the antiplatelet, the invasive pathway, and support meanwhile.",
        ["Gives an antiplatelet", "arranges immediate invasive assessment",
         "addresses the hypoperfusion"],
        ["Oxygen and cautious volume before the invasive pathway is confirmed"],
        *_REPERFUSION_D5,
        (_aspirin_omission(), _stress_test_event())),
}


# --- the families whose threat is respiratory, circulatory or metabolic ------
def _family(d1, d2, d3, d4, d5, information, closure, limits, critical_events):
    return {"domains": {"D1": d1, "D2": d2, "D3": d3, "D4": d4, "D5": d5},
            "information": tuple(information), "closure": closure,
            "engine_limits": tuple(limits), "critical_events": tuple(critical_events)}


_REASSESS = ("reassessment",)

CASES.update({
    "asthma_24f": _family(
        _d("Severe airflow obstruction is present at arrival and the work of breathing is "
           "visible on the monitor.",
           ["Names the obstruction and its severity", "treats before completing the investigation"],
           ["Naming severity by the effort and speech rather than by a peak flow"],
           (0, 15)),
        _d("The history, the chest examination and the blood gas distinguish a severe "
           "exacerbation from ventilatory failure.",
           ["Examines the breathing or the chest", "relates the gas or the effort to the severity"],
           ["Using the examination alone when the gas has not returned"],
           (0, 30), studies=("abg", "vbg"), examination=("Respiratory",)),
        _d("Bronchodilator, corticosteroid and oxygen are all executable, and the engine "
           "responds to each.",
           ["Gives a bronchodilator", "gives a corticosteroid"],
           ["Continuous nebulisation instead of repeated doses",
            "magnesium added to the bronchodilator"],
           (0, 30), actions=("bronchodilator", "steroid", "oxygen")),
        _d("The engine moves the work of breathing and the saturation in response to treatment.",
           ["States a reassessment interval", "checks the work of breathing or the saturation"],
           ["Reassessing by the gas rather than the effort"], (10, 60), actions=_REASSESS),
        _d("The response decides whether treatment continues, escalates, or the patient is "
           "observed and discharged.",
           ["Decides on the basis of the response", "states the next step and its destination"],
           ["Continuing the same treatment with a stated reason and a further check"],
           (15, 180), actions=("disposition", "consult")),
        ["Arrival observables and the monitor", "the patient's history", "chest examination",
         "arterial and venous blood gases, chest radiograph, laboratory"],
        "A disposition is decided, or the encounter reaches its horizon.",
        ["Peak flow is not a study the engine reports.",
         "The engine does not model an inhaler technique."],
        [_event("asthma_no_bronchodilator", "critical_omission",
                "No bronchodilator is given in an asthma exacerbation.",
                "The presentation is an asthma exacerbation with increased work of breathing and "
                "no bronchodilator is executed in the window.",
                ["Arrival observables", "the presenting history"], (0, 30),
                ["Continuous nebulised bronchodilator", "an intravenous bronchodilator stated as such"],
                "An executed bronchodilator action, or its absence across the window.",
                ["The encounter closed before any order could be executed"], ["D3"])]),

    "asthma_49m": _family(
        _d("Fatigue and a rising carbon dioxide are present at arrival: this is ventilatory "
           "failure, not only obstruction.",
           ["Names the ventilatory failure or the fatigue", "acts with that urgency"],
           ["Naming exhaustion or a silent chest rather than the gas"],
           (0, 15)),
        _d("The gas shows hypercapnia and the examination shows the effort that precedes arrest.",
           ["Requests or reads the blood gas", "examines the breathing"],
           ["Acting on the clinical picture and stating that the gas will confirm it"],
           (0, 30), studies=("abg", "vbg"), examination=("Respiratory",)),
        _d("Bronchodilator and steroid continue while ventilatory support is the decision "
           "the case turns on.",
           ["Gives a bronchodilator", "addresses the ventilation with support or its preparation"],
           ["Non-invasive support before intubation", "intubation with stated preparation"],
           (0, 40), actions=("bronchodilator", "steroid", "niv", "intubation", "oxygen")),
        _d("The engine responds to support and to obstruction treatment separately.",
           ["States a reassessment interval", "checks the effort, the gas or the saturation"],
           ["A shorter interval than stated when the patient is deteriorating"],
           (5, 60), actions=_REASSESS),
        _d("Whether support is escalated, maintained or withdrawn is decided on what the "
           "reassessment shows.",
           ["Decides escalation or continuation on the observed response",
            "states the destination and what is still pending"],
           ["Maintaining support with a stated reason and a further check"],
           (10, 180), actions=("disposition", "consult", "ventilator_adjustment")),
        ["Arrival observables and the monitor", "the patient's history", "chest examination",
         "blood gases, chest radiograph, laboratory"],
        "A disposition is decided, or the encounter reaches its horizon.",
        ["Peak flow is not reported.",
         "The engine models ventilation settings but not a bronchoscopy or a chest CT."],
        [_event("asthma_no_bronchodilator", "critical_omission",
                "No bronchodilator is given in an asthma exacerbation.",
                "The presentation is an asthma exacerbation and no bronchodilator is executed "
                "in the window.",
                ["Arrival observables", "the presenting history"], (0, 30),
                ["Continuous nebulised bronchodilator", "an intravenous bronchodilator stated as such"],
                "An executed bronchodilator action, or its absence across the window.",
                ["The encounter closed before any order could be executed"], ["D3"]),
         _event("asthma_no_ventilatory_support", "critical_omission",
                "Ventilatory failure is left without any support or preparation for it.",
                "The blood gas or the recorded effort shows ventilatory failure and neither "
                "oxygen, non-invasive support, bag-mask nor intubation is executed or prepared.",
                ["The blood gas result or the recorded work of breathing"], (0, 60),
                ["Non-invasive support", "bag-mask ventilation", "intubation",
                 "stating a ceiling of treatment"],
                "The absence of any executed airway or ventilation action in the window.",
                ["The gas was never reported within the encounter",
                 "the resident's support order was refused by the interpreter"], ["D3", "D5"])]),
})


def _bleed(case_id, d1_text, d1_expected, d1_alternatives, extra_events=()):
    return {case_id: _family(
        _d(d1_text, d1_expected, d1_alternatives, (0, 20)),
        _d("The haemoglobin, the perfusion and the history of the bleeding are all obtainable, "
           "and the first haemoglobin does not yet show the whole loss.",
           ["Requests the haemoglobin or the laboratory", "relates the perfusion to the bleeding"],
           ["Acting on the perfusion before the haemoglobin returns, stated as such"],
           (0, 30), studies=("hemoglobin", "basic_labs", "lactate")),
        _d("Transfusion, a proton pump inhibitor and the consultation that arranges haemostasis "
           "are all executable.",
           ["Restores circulating volume or oxygen-carrying capacity",
            "arranges the haemostasis pathway"],
           ["Crystalloid first with blood stated as next",
            "an octreotide infusion where variceal bleeding is suspected"],
           (0, 40), actions=("blood", "ppi", "fluid", "consult", "octreotide")),
        _d("The engine moves the pressure, the perfusion and the haemoglobin in response to "
           "what is given.",
           ["States a reassessment interval", "checks the perfusion or the pressure after volume"],
           ["Reassessing by the haemoglobin when a repeat sample was sent"],
           (10, 60), actions=_REASSESS),
        _d("Continued bleeding, a stabilising response, or neither decides what follows and where.",
           ["Decides continuation or escalation on the observed response",
            "states the destination and what is pending"],
           ["Keeping the patient for observation with a stated threshold to escalate"],
           (15, 180), actions=("disposition", "consult")),
        ["Arrival observables and the monitor", "the patient's history",
         "haemoglobin, laboratory, lactate, blood gases, POCUS"],
        "A disposition is decided, or the encounter reaches its horizon.",
        ["The engine does not perform endoscopy; the referral is recorded, not its result.",
         "A repeat haemoglobin requires a new sample and the encounter may close first."],
        [_event("gi_no_resuscitation", "critical_omission",
                "Haemorrhagic hypoperfusion is left without volume or blood.",
                "The arrival observables show hypoperfusion from bleeding and neither blood nor "
                "fluid is executed in the window.",
                ["Arrival observables", "the presenting history of bleeding"], (0, 40),
                ["Packed red cells", "crystalloid stated as the bridge to blood",
                 "a stated ceiling of treatment"],
                "The absence of any executed blood or fluid action in the window.",
                ["The encounter closed before any order could be executed",
                 "vascular access failed in the engine and the resident addressed it"],
                ["D3"]), *extra_events])}


CASES.update(_bleed(
    "gi_bleed_57m",
    "Bleeding with hypoperfusion is visible in the arrival observables; volume and "
    "haemostasis compete for first place with investigation.",
    ["Names the bleeding and the hypoperfusion", "resuscitates before completing the workup"],
    ["Naming shock by the perfusion rather than by a pressure threshold"]))

CASES.update(_bleed(
    "gi_bleed_72f",
    "The pain is limited and the arrival picture is anaemia and hypoperfusion: the threat "
    "has to be recognised without a dramatic complaint.",
    ["Names the clinically important bleeding despite the quiet presentation",
     "acts on the perfusion rather than on the symptom"],
    ["Naming the anaemia and its consequence rather than the bleeding itself"]))


def _hypo(case_id, d1_text, d3_text, d3_expected, d3_alternatives, d3_actions, d5_text,
          d5_expected, d5_alternatives, extra_events=()):
    return {case_id: _family(
        _d(d1_text, ["Names the hypoglycaemia or the neuroglycopenia", "treats it first"],
           ["Naming the altered state and the glucose together"], (0, 15),
           studies=("poc_glucose",)),
        _d("A bedside glucose, the history of the exposure and the neurological examination "
           "are all available.",
           ["Requests or reads the bedside glucose", "relates the mental state to the glucose"],
           ["Treating on the history and confirming with the glucose in the same turn"],
           (0, 20), studies=("poc_glucose", "basic_labs"), examination=("Neurological",)),
        _d(d3_text, d3_expected, d3_alternatives, (0, 30), actions=d3_actions),
        _d("The engine raises the glucose and the mental state in response, and lets them fall "
           "again where the case carries that risk.",
           ["States a reassessment interval", "rechecks the glucose or the mental state"],
           ["Rechecking the mental state rather than the number"], (5, 60),
           actions=_REASSESS, studies=("poc_glucose",)),
        _d(d5_text, d5_expected, d5_alternatives, (15, 180), actions=("disposition", "consult")),
        ["Arrival observables and the monitor", "the patient's or the witness's history",
         "bedside glucose, laboratory, neurological examination"],
        "A disposition is decided, or the encounter reaches its horizon.",
        ["The engine does not model a continuous glucose monitor.",
         "An oral route is refused while the patient is not fully alert, by design."],
        [_event("hypo_no_glucose", "critical_omission",
                "Neuroglycopenia is left uncorrected.",
                "The bedside glucose is low and the patient is not alert, and no dextrose, "
                "glucagon or oral carbohydrate is executed in the window.",
                ["The bedside glucose result", "the recorded mental status"], (0, 30),
                ["Intravenous dextrose", "glucagon when there is no vascular access",
                 "oral carbohydrate once the patient is alert enough to swallow"],
                "The absence of any executed glucose-raising action in the window.",
                ["Vascular access failed in the engine and the resident addressed it",
                 "the encounter closed before the glucose was reported"], ["D3"]), *extra_events])}


CASES.update(_hypo(
    "hypoglycemia_28m",
    "The glucose is low enough to explain the altered state and the correction is time-critical.",
    "Intravenous dextrose is executable, and vascular access may have to be established first.",
    ["Gives dextrose", "secures the route it needs"],
    ["Glucagon when access is not available", "oral carbohydrate once the patient is alert"],
    ("dextrose", "vascular_access", "glucagon", "oral_carbohydrate"),
    "Once the glucose and the consciousness recover, the decision is whether this patient can "
    "safely leave and what would bring them back.",
    ["Decides the destination on the recovery observed", "states what is still pending"],
    ["Keeping the patient for a stated period before deciding"]))

CASES.update(_hypo(
    "hypoglycemia_76f",
    "The glucose is low and the agent that caused it is long-acting: correction is urgent and "
    "the recurrence is the reason the encounter continues.",
    "Dextrose corrects it; the recurrence risk is what the rest of the management addresses.",
    ["Gives dextrose", "plans for the recurrence the agent carries"],
    ["A dextrose infusion rather than repeated boluses", "octreotide stated for a sulfonylurea"],
    ("dextrose", "dextrose_infusion", "vascular_access", "octreotide", "oral_carbohydrate"),
    "A sulfonylurea patient who recovers is not a patient who can leave: the decision is "
    "observation and its length.",
    ["Arranges continued observation rather than discharge",
     "states what is watched and for how long"],
    ["Admission stated as the observation"],
    [_event("hypo_unsafe_discharge", "critical_omission",
            "A patient whose hypoglycaemia was caused by a long-acting agent is discharged "
            "without observation.",
            "A discharge disposition is executed after a sulfonylurea-associated hypoglycaemia, "
            "without any recorded plan for continued observation.",
            ["The history of the causative agent", "the recorded recurrence risk"], (0, 180),
            ["Admission", "observation with a stated duration",
             "discharge with an explicitly arranged early review"],
            "An executed discharge disposition with no observation stated in the same encounter.",
            ["The encounter reached its horizon before any disposition was decided"],
            ["D5"])]))

CASES.update(_hypo(
    "hypoglycemia_54m_thiamine",
    "The glucose is low and this patient is thiamine-depleted: correcting one threat without "
    "the other creates a second.",
    "Dextrose and thiamine are both executable, and the order in which they are given is the "
    "point of the case.",
    ["Gives dextrose", "gives thiamine"],
    ["Thiamine first", "both in the same submission"],
    ("dextrose", "thiamine", "vascular_access"),
    "The decision is continued treatment of the deficiency and where that happens, not only "
    "the glucose.",
    ["Decides the destination with the deficiency in it", "states what continues"],
    ["Admission stated as the continuation"],
    [_event("hypo_no_thiamine", "critical_omission",
            "Glucose is given to a thiamine-depleted patient and no thiamine is given.",
            "Dextrose is executed in a patient the case declares thiamine-depleted and no "
            "thiamine is executed within the window.",
            ["The history of chronic alcohol use or malnutrition"], (0, 60),
            ["Thiamine before the dextrose", "thiamine in the same submission"],
            "An executed dextrose action with no executed thiamine action in the window.",
            ["The encounter closed before a second order could be executed"],
            ["D3"])]))


def _opioid(case_id, d1_text, d5_text, d5_expected, d5_alternatives, extra_events=()):
    return {case_id: _family(
        _d(d1_text, ["Names the ventilatory depression", "supports the ventilation first"],
           ["Naming the toxidrome and acting on the breathing in the same turn"], (0, 10)),
        _d("The respiratory rate, the effort, the pupils and the blood gas separate an opioid "
           "effect from another cause of the altered state.",
           ["Reads the respiratory rate and the effort", "considers the gas or the glucose"],
           ["Treating first and confirming with the response to the antagonist"],
           (0, 30), studies=("abg", "vbg", "poc_glucose"), examination=("Neurological",)),
        _d("Bag-mask ventilation, oxygen and an opioid antagonist are all executable, and the "
           "engine separates supporting the breathing from reversing the drug.",
           ["Supports the ventilation", "gives an antagonist or states why it is withheld"],
           ["Ventilating and titrating the antagonist to the breathing, not to wakefulness",
            "supporting without an antagonist when the airway is already secured"],
           (0, 30), actions=("bag_mask", "oxygen", "naloxone", "naloxone_infusion", "intubation")),
        _d("The engine moves the respiratory rate and the mental state in response, and lets "
           "them fall again where the exposure is long-acting.",
           ["States a reassessment interval", "rechecks the breathing and the mental state"],
           ["Rechecking the saturation alone when the rate is the variable that matters"],
           (5, 60), actions=_REASSESS),
        _d(d5_text, d5_expected, d5_alternatives, (15, 180), actions=("disposition", "consult")),
        ["Arrival observables and the monitor", "the witness's history",
         "blood gases, bedside glucose, neurological examination"],
        "A disposition is decided, or the encounter reaches its horizon.",
        ["The engine does not model a urine toxicology screen.",
         "Pupil size is described in the examination, not measured."],
        [_event("opioid_no_ventilatory_support", "critical_omission",
                "Ventilatory depression is left without support or reversal.",
                "The recorded respiratory rate is depressed and neither oxygen, bag-mask "
                "ventilation, an antagonist nor intubation is executed in the window.",
                ["Arrival observables, including the respiratory rate"], (0, 20),
                ["Bag-mask ventilation", "an opioid antagonist", "intubation",
                 "oxygen stated as the bridge while the antagonist is drawn up"],
                "The absence of any executed airway, oxygen or antagonist action in the window.",
                ["The encounter closed before any order could be executed"], ["D1", "D3"]),
         *extra_events])}


CASES.update(_opioid(
    "opioid_35m",
    "The respiratory rate at arrival is the threat, and it is the breathing rather than the "
    "diagnosis that has to be addressed first.",
    "Whether the patient can leave depends on what the exposure was and how long its effect "
    "outlasts the antagonist.",
    ["Decides the destination on the observed response and the exposure",
     "states what is watched"],
    ["Observation with a stated duration"]))

CASES.update(_opioid(
    "opioid_67f",
    "The ventilation is depressed and the agent is long-acting: the first correction will not "
    "be the last.",
    "An antagonist that is shorter than the opioid makes observation the decision, not the "
    "response to the first dose.",
    ["Arranges observation for recurrence rather than discharging on the first response",
     "states the duration or what would bring the depression back"],
    ["An antagonist infusion stated as the reason observation continues", "admission"],
    [_event("opioid_unsafe_discharge", "critical_omission",
            "A patient exposed to a long-acting opioid is discharged on the response to a "
            "short-acting antagonist.",
            "A discharge disposition is executed after an antagonist was given for a "
            "long-acting exposure, with no observation stated in the encounter.",
            ["The history of the exposure", "the recorded response to the antagonist"], (0, 180),
            ["Admission", "observation with a stated duration", "an antagonist infusion"],
            "An executed discharge disposition with no observation stated.",
            ["The encounter reached its horizon before any disposition was decided"],
            ["D5"])]))


def _pneumonia(case_id, d1_text, d1_expected, d2_text, d2_expected, extra_events=()):
    return {case_id: _family(
        _d(d1_text, d1_expected, ["Naming the hypoperfusion rather than a sepsis label"], (0, 20)),
        _d(d2_text, d2_expected,
           ["Acting on the radiograph before the laboratory returns"],
           (0, 40), studies=("chest_xray", "basic_labs", "lactate", "pocus", "abg"),
           examination=("Respiratory",)),
        _d("Antibiotics, oxygen and fluid are all executable and the engine responds to each.",
           ["Gives an antibiotic", "addresses the oxygenation", "addresses the perfusion"],
           ["Fluid withheld with a stated reason such as congestion",
            "oxygen titrated rather than given at a fixed flow"],
           (0, 60), actions=("antibiotics", "oxygen", "fluid")),
        _d("The engine moves the saturation, the perfusion and the lactate in response.",
           ["States a reassessment interval", "checks the oxygenation or the perfusion"],
           ["Rechecking the lactate when a repeat sample was sent"], (15, 90), actions=_REASSESS),
        _d("The response to the first hour decides the level of care and what continues.",
           ["Decides the destination on the observed response", "states what is pending"],
           ["Escalating the level of care with a stated threshold"],
           (20, 180), actions=("disposition", "consult")),
        ["Arrival observables and the monitor", "the patient's or an informant's history",
         "chest radiograph, laboratory, lactate, blood gases, POCUS, cultures"],
        "A disposition is decided, or the encounter reaches its horizon.",
        ["Culture results are pending within the encounter, by design.",
         "The engine does not model a chest CT."],
        [_event("pneumonia_no_antibiotic", "critical_omission",
                "No antibiotic is given in a pneumonia with hypoperfusion.",
                "The presentation is a pneumonia with impaired perfusion and no antibiotic is "
                "executed in the window.",
                ["Arrival observables", "the presenting history",
                 "the chest radiograph where it was requested"], (0, 60),
                ["Any of the antibiotics the engine models, with a route",
                 "a stated ceiling of treatment"],
                "The absence of an executed antibiotic action in the window.",
                ["The encounter closed before any order could be executed",
                 "the interpreter refused the agent and never said what it accepts"],
                ["D3"]), *extra_events])}


CASES.update(_pneumonia(
    "pneumonia_46f",
    "Hypoxaemia and impaired perfusion are both present at arrival and both need a decision "
    "about what comes first.",
    ["Names the hypoxaemia or the hypoperfusion", "treats before the imaging returns"],
    "The radiograph, the laboratory, the lactate and the chest examination are all available.",
    ["Requests the radiograph or the laboratory", "relates the findings to the physiology"]))

CASES.update(_pneumonia(
    "pneumonia_83m",
    "The arrival complaint is nonspecific and the altered state is the finding that has to be "
    "recognised as a threat rather than as age.",
    ["Names the altered state as something to explain", "does not attribute it to age alone"],
    "The new confusion has to be investigated alongside the infection; glucose, gases and "
    "imaging are all available.",
    ["Investigates the altered state as well as the infection",
     "relates the findings to the physiology"],
    [_event("pneumonia_unexamined_altered_state", "critical_omission",
            "A new altered mental state is never investigated.",
            "The patient arrives with an altered mental state and no glucose, neurological "
            "examination or imaging of the head is obtained in the window.",
            ["Arrival observables, including the mental status"], (0, 60),
            ["A bedside glucose", "a neurological examination",
             "stating that the infection explains it and checking the glucose anyway"],
            "The absence of any executed glucose, neurological examination or head imaging.",
            ["The encounter closed before a second order could be executed"],
            ["D2"])]))


def _edema(case_id, d1_text, d3_text, d3_expected, d3_alternatives, d5_text, extra_events=()):
    return {case_id: _family(
        _d(d1_text, ["Names the respiratory failure and its cardiac cause",
                     "supports the breathing before completing the investigation"],
           ["Naming the congestion and acting on the breathing in the same turn"], (0, 15)),
        _d("POCUS, the chest radiograph, the blood gas and the examination separate congestion "
           "from the other causes of this presentation.",
           ["Requests POCUS or the radiograph", "relates the findings to the physiology"],
           ["Acting on the examination and confirming with POCUS in the same turn"],
           (0, 30), studies=("pocus", "chest_xray", "abg", "basic_labs"),
           examination=("Respiratory", "Cardiac")),
        _d(d3_text, d3_expected, d3_alternatives, (0, 40),
           actions=("niv", "nitroglycerin", "diuretic", "oxygen")),
        _d("The engine moves the pressure, the saturation and the work of breathing in "
           "response, and a nitrate has to be watched against the pressure it lowers.",
           ["States a reassessment interval", "checks the pressure as well as the breathing"],
           ["A shorter interval while a nitrate is running"], (5, 60), actions=_REASSESS),
        _d(d5_text, ["Decides continuation or escalation on the observed response",
                     "states the destination and what is watched"],
           ["Maintaining the support with a stated reason and a further check"],
           (15, 180), actions=("disposition", "consult", "infusion_adjustment")),
        ["Arrival observables and the monitor", "the patient's history",
         "POCUS, chest radiograph, blood gases, laboratory, troponin"],
        "A disposition is decided, or the encounter reaches its horizon.",
        ["The engine reports a nitrate as an infusion rate, not as a titration protocol.",
         "Urine output is reported only where the case measures it."],
        [_event("edema_no_ventilatory_support", "critical_omission",
                "Respiratory failure from congestion is left without oxygen or ventilatory support.",
                "The arrival observables show hypoxaemia with increased work of breathing and "
                "no oxygen, non-invasive support or intubation is executed in the window.",
                ["Arrival observables"], (0, 30),
                ["Non-invasive support", "oxygen at a stated device and flow", "intubation"],
                "The absence of any executed oxygen or ventilation action in the window.",
                ["The encounter closed before any order could be executed"], ["D1", "D3"]),
         _event("edema_volume_loading", "dangerous_action",
                "A fluid bolus is given in acute cardiogenic pulmonary oedema.",
                "A crystalloid bolus is executed while the record shows congestion and no cause "
                "of hypovolaemia has been established.",
                ["Arrival observables", "the POCUS or radiograph where it was requested"],
                (0, 180),
                ["A small stated challenge with an explicit hypovolaemic rationale and a "
                 "reassessment attached", "withholding fluid"],
                "An executed fluid action with a recorded congested state.",
                ["The case established a hypovolaemic contributor before the bolus"],
                ["D3"]), *extra_events])}


CASES.update(_edema(
    "pulmonary_edema_58m",
    "The pressure is high and the breathing is failing: both the loading and the ventilation "
    "need a decision in the first minutes.",
    "Non-invasive support, a nitrate and a diuretic are all executable, and in a hypertensive "
    "oedema the loading is what the nitrate addresses.",
    ["Supports the breathing", "reduces the cardiac loading"],
    ["A diuretic stated as secondary to the nitrate", "oxygen first while support is set up"],
    "The pressure and the breathing after the first intervention decide whether support "
    "continues, escalates or can be reduced."))

CASES.update(_edema(
    "pulmonary_edema_75f",
    "Respiratory distress with congestion, in a patient whose renal function and pressure "
    "limit what can be given.",
    "Support, a nitrate and a diuretic are executable, and this patient's pressure and renal "
    "function constrain the choice.",
    ["Supports the breathing", "addresses the congestion within the pressure available"],
    ["Withholding the nitrate with a stated pressure reason",
     "a diuretic with the renal function stated"],
    "The response, the pressure and the renal function decide what continues and where."))


def _embolism(case_id, d1_text, d1_expected, d3_text, d3_expected, d3_alternatives,
              d5_text, d5_expected, extra_events=()):
    return {case_id: _family(
        _d(d1_text, d1_expected,
           ["Naming the hypoxaemia and the tachycardia rather than the diagnosis"], (0, 20)),
        _d("The POCUS, the CT pulmonary angiogram, the D-dimer with its age-adjusted limit, "
           "the blood gas and the calf examination are all available, and the case's own "
           "alternative explanation has to be addressed rather than assumed.",
           ["Obtains objective evidence rather than accepting the offered explanation",
            "examines or investigates for the source"],
           ["POCUS as the first objective evidence when the patient cannot be moved",
            "treating on clinical grounds with the confirmation stated as pending"],
           (0, 45), studies=("pocus", "ctpa", "d_dimer", "abg", "troponin"),
           examination=("Extremities", "Respiratory")),
        _d(d3_text, d3_expected, d3_alternatives, (0, 60),
           actions=("anticoagulation", "oxygen", "consult", "thrombolysis", "fluid")),
        _d("The engine moves the saturation, the rate and the pressure in response, and the "
           "right ventricle is where deterioration shows first.",
           ["States a reassessment interval", "checks the oxygenation and the haemodynamics"],
           ["Reassessing by POCUS rather than by the vitals"], (10, 90), actions=_REASSESS),
        _d(d5_text, d5_expected,
           ["Keeping the patient monitored with a stated threshold to escalate"],
           (20, 180), actions=("disposition", "consult")),
        ["Arrival observables and the monitor", "the patient's history",
         "POCUS, CT pulmonary angiogram, D-dimer, blood gases, troponin, radiograph",
         "the examination of the legs, which the case authors"],
        "A disposition is decided, or the encounter reaches its horizon.",
        ["The engine records a reperfusion referral, not its result.",
         "The CT angiogram takes twenty minutes of simulated time and the encounter may close first."],
        [_event("pe_no_anticoagulation", "critical_omission",
                "No anticoagulation is given or stated as withheld in a recognised embolism.",
                "Objective or clinical evidence of embolism is recorded and no anticoagulation "
                "is executed in the window, with no contraindication stated.",
                ["The POCUS, angiogram or D-dimer where requested", "the presenting history"],
                (0, 60),
                ["Anticoagulation of any modelled agent and route",
                 "withholding it with a stated bleeding contraindication",
                 "proceeding directly to reperfusion with a stated reason"],
                "The absence of an executed anticoagulation action in the window.",
                ["The encounter closed before the confirming study was reported"], ["D3"]),
         *extra_events])}


CASES.update(_embolism(
    "pulmonary_embolism_33f",
    "Sudden breathlessness with tachycardia and hypoxaemia, in a patient who offers anxiety "
    "as the explanation: the threat has to be recognised against that anchor.",
    ["Names the hypoxaemia and the tachycardia as a threat",
     "does not accept the offered explanation without objective evidence"],
    "Anticoagulation, oxygen and the specialist pathway are executable; without sustained "
    "hypotension, thrombolysis is not the treatment this patient needs.",
    ["Anticoagulates or states why it is withheld", "addresses the oxygenation"],
    ["Awaiting the confirming study with anticoagulation stated as pending it",
     "oxygen titrated rather than given at a fixed flow"],
    "The haemodynamics decide the level of care and whether reperfusion enters the plan at all.",
    ["Decides the destination on the observed haemodynamics",
     "states what would change the plan"],
    [_event("pe_unindicated_thrombolysis", "dangerous_action",
            "Systemic thrombolysis is given without sustained hypotension, in a patient with a "
            "recent operation.",
            "A thrombolytic is executed while the record shows no sustained hypotension and the "
            "history carries a recent surgical site.",
            ["Arrival and subsequent observables", "the surgical history"], (0, 180),
            ["Anticoagulation", "arranging a reperfusion-capable team without giving the drug",
             "thrombolysis after sustained hypotension is recorded"],
            "An executed thrombolysis action with the record showing no sustained hypotension.",
            ["The record shows sustained hypotension within the engine's own criterion"],
            ["D3"])]))

CASES.update(_embolism(
    "pulmonary_embolism_61m",
    "Obstructive shock: the pressure, the rate and the perfusion all demand action before the "
    "confirming study returns.",
    ["Names the shock and its obstructive cause", "acts before the angiogram returns"],
    "Anticoagulation, oxygen, the reperfusion-capable team and, in sustained hypotension, "
    "thrombolysis are all executable.",
    ["Anticoagulates or states why it is withheld",
     "involves a reperfusion-capable team rapidly"],
    ["Thrombolysis with the sustained hypotension stated",
     "cautious volume with a stated limit"],
    "Transport, the level of care and who performs the reperfusion are the continuity "
    "decisions, and they depend on the pressure.",
    ["Decides transport and level of care on the observed haemodynamics",
     "states what is pending and who is responsible"]))
