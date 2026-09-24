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
           alternatives, evidence_required, exclusions, domains, on_asking=()):
    """One defined critical event.

    ``information_required`` is what has to be **in the record**: arrival
    observables, a study result, an executed action. ``on_asking`` is what the
    patient or the collateral source will say **if the resident asks** — each
    entry a (history topic, what it tells them) pair, where the topic is a key
    the case actually authors and ``case_assessment.verify`` checks that.

    Faculty decision of 2026-09-23: information available on asking is
    available, whether or not the learner asked. The patient is in front of
    them and can be asked; a resident who never asks has not been deprived of
    the information, they have omitted to obtain it. So an unasked history
    never excuses an event, and the omission is itself something the reports
    name and the score reflects.
    """
    return {"event_id": event_id, "kind": kind, "action": action, "trigger": trigger,
            "information_required": tuple(information_required), "window_min": window,
            "alternatives": tuple(alternatives), "evidence_required": evidence_required,
            "exclusions": tuple(exclusions), "domains": tuple(domains),
            "information_on_asking": tuple((topic, tells) for topic, tells in on_asking)}


# --- the antiplatelet omission, shared by every coronary case ----------------
def _aspirin_omission(window=(0, 30)):
    return _event(
        "acs_no_antiplatelet", "critical_omission",
        "No antiplatelet is given in a recognised acute coronary syndrome.",
        "The ECG is reported and the presentation is ischaemic, and no aspirin or P2Y12 "
        "inhibitor is executed within the window.",
        ["The 12-lead ECG result"], window,
        ["A P2Y12 inhibitor when aspirin is contraindicated or refused, stated as such",
         "withholding it with a stated contraindication such as active bleeding or allergy"],
        "An executed antiplatelet action, or its absence across every executed turn in the window.",
        ["The encounter closed before the ECG was reported",
         "the interpreter refused the order and the resident was never told what it could accept"],
        ["D3"],
        [("chief_complaint", "the ischaemic presentation in the patient's own words"),
         ("allergies", "whether aspirin can be given at all")])


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
                ["Arrival observables"], (0, 30),
                ["Continuous nebulised bronchodilator", "an intravenous bronchodilator stated as such"],
                "An executed bronchodilator action, or its absence across the window.",
                ["The encounter closed before any order could be executed"], ["D3"],
                [("medical_history", "that this is asthma and how severe it has been before"),
                 ("medications", "the reliever already used today")])]),

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
                ["Arrival observables"], (0, 30),
                ["Continuous nebulised bronchodilator", "an intravenous bronchodilator stated as such"],
                "An executed bronchodilator action, or its absence across the window.",
                ["The encounter closed before any order could be executed"], ["D3"],
                [("medical_history", "the asthma and the previous ventilated admission"),
                 ("medications", "the reliever already used today")]),
         _event("asthma_no_ventilatory_support", "critical_omission",
                "Ventilatory failure is left without any support or preparation for it.",
                "The blood gas or the recorded effort shows ventilatory failure and neither "
                "oxygen, non-invasive support, bag-mask nor intubation is executed or prepared.",
                ["The blood gas result or the recorded work of breathing"], (0, 60),
                ["Non-invasive support", "bag-mask ventilation", "intubation",
                 "stating a ceiling of treatment"],
                "The absence of any executed airway or ventilation action in the window.",
                ["The gas was never reported within the encounter",
                 "the resident's support order was refused by the interpreter"], ["D3", "D5"],
                [("medical_history", "the previous admission that required ventilation")])]),
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
                ["Arrival observables"], (0, 40),
                ["Packed red cells", "crystalloid stated as the bridge to blood",
                 "a stated ceiling of treatment"],
                "The absence of any executed blood or fluid action in the window.",
                ["The encounter closed before any order could be executed",
                 "vascular access failed in the engine and the resident addressed it"],
                ["D3"],
                [("bleeding", "the melena and how long it has been going on"),
                 ("medications", "the anti-inflammatory that caused it")]), *extra_events])}


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
            "A discharge disposition is executed after a hypoglycaemia this case attributes to "
            "a sulfonylurea, without any recorded plan for continued observation. It applies "
            "whether or not the learner asked what caused it: the agent is available on "
            "asking, and never asking is part of the omission rather than an excuse for it.",
            ["An executed discharge disposition"], (0, 180),
            ["Admission", "observation with a stated duration",
             "discharge with an explicitly arranged early review"],
            "An executed discharge disposition with no observation stated in the same encounter.",
            ["The encounter reached its horizon before any disposition was decided"],
            ["D5"],
            [("medications", "the glimepiride she kept taking while eating almost nothing"),
             ("onset", "the two days of poor intake that made it recur")])]))

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
            ["An executed dextrose action"], (0, 60),
            ["Thiamine before the dextrose", "thiamine in the same submission"],
            "An executed dextrose action with no executed thiamine action in the window.",
            ["The encounter closed before a second order could be executed"],
            ["D3"],
            [("medical_history", "the daily drinking"),
             ("oral_intake", "the week with almost nothing to eat")])]))


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
            ["An executed antagonist action", "the recorded response to it"], (0, 180),
            ["Admission", "observation with a stated duration", "an antagonist infusion"],
            "An executed discharge disposition with no observation stated.",
            ["The encounter reached its horizon before any disposition was decided"],
            ["D5"],
            [("exposure", "the long-acting agent she took"),
             ("medications", "what was on her list before this")])]))


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
                ["Arrival observables", "the chest radiograph where it was requested"], (0, 60),
                ["Any of the antibiotics the engine models, with a route",
                 "a stated ceiling of treatment"],
                "The absence of an executed antibiotic action in the window.",
                ["The encounter closed before any order could be executed",
                 "the interpreter refused the agent and never said what it accepts"],
                ["D3"],
                [("associated_symptoms", "the new cough and the days it has lasted"),
                 ("onset", "when the breathing changed")]), *extra_events])}


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
                ["The POCUS, angiogram or D-dimer where requested"], (0, 60),
                ["Anticoagulation of any modelled agent and route",
                 "withholding it with a stated bleeding contraindication",
                 "proceeding directly to reperfusion with a stated reason"],
                "The absence of an executed anticoagulation action in the window.",
                ["The encounter closed before the confirming study was reported"], ["D3"],
                [("risk_factors", "the immobility and the active cancer"),
                 ("medications", "whether an anticoagulant is already running")]),
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
            ["Arrival and subsequent observables"], (0, 180),
            ["Anticoagulation", "arranging a reperfusion-capable team without giving the drug",
             "thrombolysis after sustained hypotension is recorded"],
            "An executed thrombolysis action with the record showing no sustained hypotension.",
            ["The record shows sustained hypotension within the engine's own criterion"],
            ["D3"],
            [("medical_history", "the operation twelve days ago"),
             ("bleeding", "whether the surgical site has bled")])]))

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


# --- anaphylaxis -------------------------------------------------------------
# The family added 2026-09-23. What it declares is the same everywhere; what
# separates the two cases is the fifth domain, because one is a reaction that
# will come back and the other is a reaction that answers a third as well as it
# should.
def _anaphylaxis_no_epinephrine():
    return _event(
        "anaphylaxis_no_epinephrine", "critical_omission",
        "No adrenaline is given in a reaction that presents as anaphylaxis.",
        "The arrival record carries an acute reaction after an exposure with airway, "
        "breathing or circulatory involvement, and no adrenaline is executed by any "
        "route within the window.",
        ["Arrival observables", "the examination of the skin and the chest"], (0, 15),
        ["Adrenaline by any route, stated as such",
         "withholding it with a stated reason the record supports"],
        "An executed adrenaline action, or its absence across every executed turn in the window.",
        ["The encounter closed before the window opened",
         "the interpreter refused the order and the resident was never told what it could accept"],
        ["D1", "D3"],
        [("exposure", "what the patient was exposed to and when"),
         ("chief_complaint", "the reaction in the patient's or the family's own words")])


def _anaphylaxis_antihistamine_only():
    return _event(
        "anaphylaxis_antihistamine_only", "dangerous_action",
        "The reaction is treated with a steroid or a bronchodilator instead of adrenaline.",
        "A steroid or a bronchodilator is executed within the window and no adrenaline is, "
        "so the treatment given cannot act on the reaction.",
        ["Arrival observables"], (0, 20),
        ["The same drugs given after adrenaline, as adjuncts",
         "a bronchodilator for a wheeze in a patient who has already had adrenaline"],
        "An executed steroid or bronchodilator with no executed adrenaline action before it "
        "or within the window.",
        ["Adrenaline was executed first or in the same turn"],
        ["D3"],
        [("medical_history", "whether this patient has asthma, which a wheeze alone would not settle")])


_ANA_D1 = _d(
    "The reaction is in front of the resident on arrival: the skin, the airway and the "
    "pressure all carry it, and there is a priority to decide between treating it and "
    "investigating what caused it.",
    ["Names the reaction or the threat it represents within the window",
     "treats before pursuing confirmation"],
    ["Naming it as an allergic reaction without the word anaphylaxis",
     "acting first and naming it in the same turn"],
    (0, 15), examination=("General appearance",))

_ANA_D2 = _d(
    "The exposure, the timing and the medication list are all available for the asking, and "
    "the examination separates a warm shock from a cold one.",
    ["Obtains the exposure and its timing",
     "relates the skin, the chest and the peripheries to one explanation"],
    ["Reaching the explanation from the examination without naming the trigger",
     "using POCUS to exclude the congested alternatives"],
    (0, 30), studies=("pocus",), examination=("General appearance", "Respiratory"))

_ANA_D3 = _d(
    "Adrenaline is executable by the intramuscular route and as a diluted intravenous dose or "
    "an infusion; volume, oxygen and the adjuncts are all available.",
    ["Executes adrenaline with a dose and a route",
     "adds volume and oxygen to the reaction rather than instead of it"],
    ["An autoinjector strength stated as such",
     "the intravenous route with the dilution stated"],
    (0, 20), actions=("epinephrine_im", "fluid", "oxygen"))

_ANA_D4 = _d(
    "The intramuscular route takes minutes to act, and the engine runs a clock: what the "
    "first dose did, and when, is observable.",
    ["States a reassessment interval and what will be checked",
     "checks the pressure, the saturation and the airway after the dose"],
    ["Reassessing on the airway alone when that is the threat",
     "a shorter interval than stated"],
    (2, 60), actions=("reassessment",))


def _anaphylaxis(case_id, d5_opportunity, d5_expected, d5_alternatives, critical_events):
    return {case_id: {
        "domains": {"D1": _ANA_D1, "D2": _ANA_D2, "D3": _ANA_D3, "D4": _ANA_D4,
                    "D5": _d(d5_opportunity, d5_expected, d5_alternatives, (15, 180),
                             actions=("consult", "disposition"))},
        "information": ("Arrival observables and the monitor",
                        "the exposure, its timing and the medication list, on asking",
                        "the examination of the skin, the chest and the peripheries",
                        "laboratory, POCUS and chest radiograph"),
        "closure": "A disposition is decided, or the horizon of the encounter is reached.",
        "engine_limits": ("The engine does not perform a serum tryptase; the diagnosis is clinical here.",
                          "A referral to allergy is recorded, not its result."),
        "critical_events": critical_events,
    }}


CASES.update(_anaphylaxis(
    "anaphylaxis_29f",
    "The reaction settles, and the decision is what happens next: how long this patient is "
    "watched, and what they leave with.",
    ["Decides an observation period rather than a discharge on the response alone",
     "states what would bring the patient back and what they leave with"],
    ["Admission stated as the observation",
     "a discharge with the return criteria and the autoinjector stated"],
    [_anaphylaxis_no_epinephrine(), _anaphylaxis_antihistamine_only(),
     _event(
         "anaphylaxis_unsafe_discharge", "critical_omission",
         "The patient is discharged after the reaction settles without an observation period "
         "or stated return criteria.",
         "A discharge disposition is executed after the reaction settles, and the record "
         "carries neither an observation period nor the criteria for returning. It applies "
         "whether or not the learner asked how quickly it came on: the patient is in front "
         "of them and can be asked, and never asking is part of the omission rather than an "
         "excuse for it.",
         ["An executed discharge disposition", "the observables at the time of that decision"],
         (15, 180),
         ["An observation period stated with its length",
          "a discharge with the return criteria and the prescribed adrenaline stated",
          "handover to a service that will observe"],
         "An executed discharge action with no observation period or return criteria in any "
         "executed turn of the encounter.",
         ["The encounter reached its horizon before any disposition was decided"],
         ["D1", "D5"],
         [("onset", "how quickly the reaction came on, which is what a biphasic one repeats"),
          ("medical_history", "whether this has happened before")])]))

CASES.update(_anaphylaxis(
    "anaphylaxis_63m_betablocked",
    "The response to the adrenaline is smaller than it should be, and the decision is "
    "whether to repeat it or to ask what is blunting it.",
    ["Compares the observed response with the one they expected",
     "pursues the reason for the gap rather than only repeating the dose"],
    ["Glucagon with the beta blockade stated",
     "an adrenaline infusion with the inadequate response stated",
     "asking for help with the refractory reaction named"],
    [_anaphylaxis_no_epinephrine(), _anaphylaxis_antihistamine_only(),
     _event(
         "anaphylaxis_unexamined_refractory", "critical_omission",
         "Adrenaline is repeated without the reason for its inadequate response being pursued.",
         "Two or more adrenaline doses are executed, the observables show an inadequate "
         "response, and nothing in the record pursues why: no medication history is obtained, "
         "no glucagon is given, and no help is asked for. It applies whether or not the "
         "learner asked about the medications: the family is present and can be asked, and "
         "never asking is part of the omission rather than an excuse for it.",
         ["Two or more executed adrenaline actions", "the observables after each of them"],
         (10, 120),
         ["Glucagon", "an adrenaline infusion with the inadequate response stated",
          "a consultation with the refractory reaction named"],
         "Two or more executed adrenaline actions with no glucagon, no consultation and no "
         "recorded history of the medications in any executed turn of the window.",
         ["Only one adrenaline dose was executed",
          "the response recorded after the second dose was adequate"],
         ["D2", "D5"],
         [("medications", "the atenolol he took this morning"),
          ("medical_history", "the rhythm the beta blocker is for")])]))


# --- renal colic and obstructive pyelonephritis -------------------------------
# Two patients with the same complaint and the same dilatation on the study. The
# family is declared twice because what is being assessed genuinely differs: one
# is a decision not to admit, the other is a decision about who has to be
# involved for the treatment to work at all.
_COLIC_D2 = _d(
    "The urine, the temperature, the lactate and the renal study are all available, and "
    "together they separate a colic from an infected obstruction.",
    ["Requests the urine and the temperature", "relates them to the dilatation on the study"],
    ["Reaching the same separation from the examination and the urine without the lactate",
     "the renal study read alongside the urine rather than before it"],
    (0, 40), studies=("urinalysis", "temperature", "renal_ultrasound", "lactate"),
    examination=("Abdomen",))

CASES.update({
    "renal_colic_34m": {
        "domains": {
            "D1": _d(
                "Severe pain with preserved perfusion and a normal temperature: the priority is "
                "to relieve the pain and to establish that this is not the infected obstruction "
                "the same presentation can be.",
                ["Names the threat that has to be excluded, or excludes it",
                 "treats the pain within the window"],
                ["Treating the pain first and naming the exclusion in the same turn"],
                (0, 20), actions=("antipyretic", "opioid_analgesia")),
            "D2": _COLIC_D2,
            "D3": _d(
                "Analgesia is executable, and so is the antiemetic the vomiting calls for; the "
                "engine gives both and changes the pain score.",
                ["Executes an analgesic with a dose and a route",
                 "chooses an agent and a route the vomiting allows"],
                ["An opioid where the anti-inflammatory is contraindicated or refused",
                 "an anti-inflammatory stated as first line"],
                (0, 30), actions=("antipyretic", "opioid_analgesia")),
            "D4": _d(
                "Pain is a number this engine reports and changes: what the analgesia did, and "
                "when, is observable.",
                ["States what will be checked and when",
                 "checks the pain and the observables after the analgesia"],
                ["Reassessing the pain alone when the observables are normal"],
                (10, 90), actions=("reassessment",)),
            "D5": _d(
                "Nothing here requires admission, so the continuity decision is what this patient "
                "leaves with and what brings them back.",
                ["Decides the disposition on the findings rather than on the pain alone",
                 "states the follow-up and the reasons to return"],
                ["Admission with a stated reason such as intractable pain or a solitary kidney",
                 "a period of observation stated as such"],
                (20, 180), actions=("disposition", "consult")),
        },
        "information": ("Arrival observables and the monitor",
                        "the urinary symptoms, the exposure and the fluid intake, on asking",
                        "the examination of the abdomen and the renal angles",
                        "urine, laboratory, lactate and the renal ultrasound"),
        "closure": "A disposition is decided, or the horizon of the encounter is reached.",
        "engine_limits": ("The engine does not pass or remove a stone; the course inside the "
                          "encounter is the pain and the observables.",
                          "An outpatient urology appointment is recorded, not its result."),
        "critical_events": [
            _event(
                "colic_missed_infection", "critical_omission",
                "The patient is discharged without the urine or the temperature having been obtained.",
                "A discharge disposition is executed and neither a urinalysis nor a temperature "
                "appears anywhere in the record. It applies whether or not the learner asked "
                "about urinary symptoms: the patient is in front of them and can be asked, and "
                "never asking is part of the omission rather than an excuse for it.",
                ["An executed discharge disposition"], (0, 180),
                ["A urinalysis or a temperature obtained at any point before the discharge",
                 "admission or observation instead of discharge"],
                "An executed discharge action with no urinalysis and no temperature in any "
                "executed turn of the encounter.",
                ["The encounter reached its horizon before any disposition was decided"],
                ["D2", "D5"],
                [("urinary_symptoms", "the absence of burning, frequency and visible blood"),
                 ("exposure", "the absence of instrumentation or a recent admission")])],
    },
})

CASES.update({
    "obstructive_pyelonephritis_58f": {
        "domains": {
            "D1": _d(
                "Fever, tachycardia, delayed refill and a raised lactate on a dilated collecting "
                "system: the priority is the sepsis and its source, before the pain.",
                ["Names the sepsis and its urinary source within the window",
                 "acts on the circulation before completing the investigation"],
                ["Naming it as an infected obstruction without the word sepsis",
                 "acting first and naming it in the same turn"],
                (0, 20), actions=("fluid", "antibiotics")),
            "D2": _COLIC_D2,
            "D3": _d(
                "Cultures, antibiotics, volume and the urology referral are all executable, and "
                "the engine keeps the source behind the stone.",
                ["Takes cultures before or with the antibiotic and executes the antibiotic",
                 "resuscitates the circulation"],
                ["An antibiotic given before the cultures with the urgency stated",
                 "vasopressor support where volume has not restored the pressure"],
                (0, 60), actions=("antibiotics", "fluid", "diagnostic")),
            "D4": _d(
                "The engine runs a clock and answers to what is given: the pressure, the rate "
                "and the lactate all move, and the antibiotic takes an hour to do anything.",
                ["States a reassessment interval and what will be checked",
                 "checks the response to the volume and the antibiotic"],
                ["Reassessing the perfusion rather than the pressure alone",
                 "a shorter interval than stated"],
                (10, 120), actions=("reassessment",)),
            "D5": _d(
                "An antibiotic does not drain an obstructed kidney. The continuity decision is "
                "who decompresses it, when, and what is watched until they do.",
                ["Involves urology, or asks for decompression by name",
                 "states the level of care and what is watched while it is arranged"],
                ["Transfer to a centre with urology stated as the decompression pathway",
                 "a critical-care bed decided alongside the referral"],
                (15, 180), actions=("consult", "disposition")),
        },
        "information": ("Arrival observables and the monitor",
                        "the urinary symptoms, the diabetes and the previous stone, on asking",
                        "the examination of the abdomen and the renal angles",
                        "urine, cultures, laboratory, lactate and the renal ultrasound"),
        "closure": "A disposition is decided, or the horizon of the encounter is reached.",
        "engine_limits": ("The engine does not decompress a kidney; the referral is recorded, "
                          "never its result, so the course inside the encounter is what "
                          "treatment can and cannot do without it.",
                          "Culture identification and susceptibility are always pending here."),
        "critical_events": [
            _event(
                "pyelo_no_antibiotic", "critical_omission",
                "No antibiotic is given in a recognised infected obstruction.",
                "The urine and the temperature are in the record and no antibiotic is executed "
                "within the window.",
                ["Arrival observables", "the urinalysis or the temperature result"], (0, 60),
                ["An antibiotic withheld with a stated allergy and an alternative given"],
                "An executed antibiotic action, or its absence across every executed turn in "
                "the window.",
                ["The encounter closed before the window opened",
                 "the interpreter refused the order and the resident was never told what it could accept"],
                ["D3"],
                [("allergies", "whether the antibiotic can be given at all"),
                 ("urinary_symptoms", "the cloudy, strong-smelling urine and the burning")]),
            _event(
                "pyelo_no_source_control", "critical_omission",
                "Urology is not involved and no decompression is asked for in an infected, "
                "obstructed kidney with sepsis.",
                "The renal study reports the dilatation, the urine is infected, the observables "
                "carry the sepsis, and no urology consultation and no decompression appear in "
                "the record within the window. It applies whether or not the learner asked "
                "about the previous stone: the patient is in front of them and can be asked, "
                "and never asking is part of the omission rather than an excuse for it.",
                ["The renal ultrasound result", "the urinalysis result", "arrival observables"],
                (0, 90),
                ["Urology asked for by name", "a nephrostomy or a ureteric stent asked for",
                 "transfer to a centre with urology stated as the decompression pathway"],
                "An executed consultation with urology, or a request for decompression, or "
                "their absence across every executed turn in the window.",
                ["The encounter closed before the renal study was reported"],
                ["D3", "D5"],
                [("medical_history", "the stone on the same side three years ago"),
                 ("urinary_symptoms", "the burning and the cloudy urine")]),
            _event(
                "pyelo_unsafe_discharge", "critical_omission",
                "The patient is sent home or to an ambulatory pathway with the sepsis still "
                "recorded.",
                "A discharge disposition is executed while the record still carries fever, "
                "tachycardia or hypotension.",
                ["An executed discharge disposition", "the observables at the time of that decision"],
                (0, 180),
                ["Admission, a critical-care bed or transfer",
                 "a discharge after the observables have returned, with the follow-up stated"],
                "An executed discharge action with fever, tachycardia or hypotension in the "
                "observables recorded at that decision.",
                ["The encounter reached its horizon before any disposition was decided"],
                ["D1", "D5"],
                [("onset", "the two days of pain and the rigors this morning")])],
    },
})


# --- unstable bradycardia -----------------------------------------------------
# The monitor says the rate. It does not say what took it, and in both of these
# the treatment that works is the one the cause calls for. The shared omission
# is leaving a symptomatic bradycardia unsupported; what separates the cases is
# whether the answer is a drug or a wire.
def _bradycardia_no_support(window=(0, 20)):
    return _event(
        "bradycardia_no_support", "critical_omission",
        "A symptomatic bradycardia is left without any attempt to support the rate or the "
        "circulation.",
        "The arrival record carries a rate below 50 with hypotension or an altered mental "
        "state, and no atropine, pacing, chronotropic infusion or antidote is executed "
        "within the window.",
        ["Arrival observables and the monitor"], window,
        ["Atropine, pacing, a chronotropic infusion or the antidote the cause calls for",
         "an antidote given without atropine where the cause is already known"],
        "An executed rate-supporting or antidote action, or its absence across every "
        "executed turn in the window.",
        ["The encounter closed before the window opened",
         "the interpreter refused the order and the resident was never told what it could accept"],
        ["D1", "D3"],
        [("chief_complaint", "what happened before the collapse, in the family's own words"),
         ("medications", "what this patient takes and whether a dose changed")])


_BRADY_D1 = _d(
    "The rate, the pressure and the perfusion are all on arrival: the priority is to support "
    "the circulation while the cause is being established, not after it.",
    ["Names the instability within the window", "acts on it before completing the investigation"],
    ["Naming the threat without naming a cause", "acting first and naming it in the same turn"],
    (0, 15), actions=("atropine", "transcutaneous_pacing", "calcium", "glucagon"))

_BRADY_D4 = _d(
    "The engine answers to what is given and runs a clock: a dose that does nothing, and an "
    "antidote that fades, are both observable.",
    ["States a reassessment interval and what will be checked",
     "checks the rate, the pressure and the perfusion after each attempt"],
    ["Reassessing the rhythm as well as the rate", "a shorter interval than stated"],
    (5, 90), actions=("reassessment",))


def _bradycardia(case_id, d2, d3, d5, critical_events):
    return {case_id: {
        "domains": {"D1": _BRADY_D1, "D2": d2, "D3": d3, "D4": _BRADY_D4, "D5": d5},
        "information": ("Arrival observables, the monitor and the twelve-lead",
                        "the medication list and the course of the day, on asking",
                        "the examination of the pulse, the neck and the peripheries",
                        "laboratory including the potassium and the glucose, and POCUS"),
        "closure": "A disposition is decided, or the horizon of the encounter is reached.",
        "engine_limits": ("The engine does not place a transvenous wire; a referral is "
                          "recorded, not its result.",
                          "It does not run extracorporeal support or high-dose insulin "
                          "euglycaemic therapy; what it runs is what is listed as executable."),
        "critical_events": critical_events,
    }}


CASES.update(_bradycardia(
    "bradycardia_ccb_68m",
    _d("The glucose, the potassium and the medication list together separate a poisoning "
       "from a primary conduction problem, and the boxes came in with the daughter.",
       ["Obtains the medication history", "relates the glucose and the normal potassium to it"],
       ["Reaching the poisoning from the history alone",
        "the glucose noticed on the arrival observables rather than requested"],
       (0, 40), studies=("basic_labs", "poc_glucose", "ecg"), examination=("Cardiac",)),
    _d("Calcium and glucagon are both executable, and the engine prices them by the cause: "
       "one of them answers this blockade and the other barely does.",
       ["Executes the antidote the cause calls for, with a dose and a route",
        "does not stop at atropine once it has done nothing"],
       ["Both antidotes given in sequence with the uncertainty stated",
        "a chronotropic infusion alongside the antidote"],
       (0, 40), actions=("calcium", "glucagon", "atropine")),
    _d("The antidote fades and this engine does not run the definitive therapy: the "
       "continuity decision is who is involved and where this patient is watched.",
       ["Asks for help with the poisoning named",
        "decides the level of care and states what is watched as the antidote wears off"],
       ["Toxicology or the poisons centre named as the help",
        "a critical-care bed decided alongside the referral"],
       (15, 180), actions=("consult", "disposition")),
    [_bradycardia_no_support(),
     _event(
         "bradycardia_cause_unexamined", "critical_omission",
         "The rate is treated without the cause being pursued, in a patient whose poisoning "
         "is in the medication history.",
         "Atropine or pacing is executed, the response is inadequate, and nothing in the "
         "record pursues the cause: no medication history is obtained and no antidote is "
         "given within the window. It applies whether or not the learner asked about the "
         "medicines: the daughter is present with the boxes and can be asked, and never "
         "asking is part of the omission rather than an excuse for it.",
         ["An executed rate-supporting action", "the observables after it"], (5, 90),
         ["An antidote given", "a recorded medication history",
          "a toxicology consultation with the poisoning named"],
         "An executed atropine or pacing action with no antidote, no consultation and no "
         "recorded medication history in any executed turn of the window.",
         ["The encounter closed before any rate-supporting action was executed"],
         ["D2", "D5"],
         [("medications", "the verapamil and the dose that was doubled last week"),
          ("exposure", "that there is no other medicine in the house")])]))

CASES.update(_bradycardia(
    "bradycardia_avb3_78f",
    _d("The twelve-lead carries the dissociation, and the potassium, the glucose and the "
       "medication list are all available to exclude the causes that have an antidote.",
       ["Requests the twelve-lead and interprets the block",
        "excludes a drug or an electrolyte cause from the history and the laboratory"],
       ["Naming the block from the monitor and confirming it on the twelve-lead",
        "excluding the drug cause from the history without the laboratory"],
       (0, 40), studies=("ecg", "basic_labs"), examination=("Cardiac",)),
    _d("Atropine, pacing and a chronotropic infusion are all executable, and the pacer has "
       "a rate and an output that this patient's threshold answers separately.",
       ["Paces when the atropine does nothing",
        "sets an output and confirms capture rather than accepting the set rate"],
       ["A chronotropic infusion while the pacer is being set up",
        "pacing first with the atropine stated as unlikely to work"],
       (0, 45), actions=("atropine", "transcutaneous_pacing")),
    _d("Transcutaneous pacing is a bridge and this engine does not place a wire: the "
       "continuity decision is who does, and what holds the patient until then.",
       ["Arranges the definitive pacing or the service that provides it",
        "states what is watched while it is arranged"],
       ["Transfer stated as the pacing pathway",
        "a critical-care bed decided alongside the referral"],
       (15, 180), actions=("consult", "disposition")),
    [_bradycardia_no_support(),
     _event(
         "bradycardia_pacing_unconfirmed", "dangerous_action",
         "Pacing is started and capture is never confirmed.",
         "A transcutaneous pacing action is executed and no reassessment of the pulse, the "
         "pressure or the perfusion follows it within the window, so a monitor showing the "
         "set rate is treated as a circulation.",
         ["An executed transcutaneous pacing action"], (0, 30),
         ["A reassessment naming the pulse, the pressure or the perfusion after pacing",
          "the output raised after an explicit failure to capture"],
         "An executed pacing action with no reassessment action in the window that follows it.",
         ["The encounter closed before the window that follows the pacing"],
         ["D3", "D4"])]))


CASES.update(_bradycardia(
    "bradycardia_bb_54f",
    _d("The glucose, the potassium and the empty packet the partner brought together "
       "separate this poisoning from the one that looks identical on the monitor.",
       ["Obtains the medication history",
        "distinguishes it from the other drugs that slow a heart"],
       ["Reaching the poisoning from the packet alone",
        "the normal glucose used to exclude the calcium-channel blockade"],
       (0, 40), studies=("basic_labs", "poc_glucose", "ecg"), examination=("Cardiac",)),
    _d("Calcium and glucagon are both executable and the engine prices them by the cause: "
       "here the one that answers is not the one that answered the last case.",
       ["Executes the antidote this blockade answers to, with a dose and a route",
        "does not stop at atropine once it has done nothing"],
       ["Both antidotes in sequence with the uncertainty stated",
        "a chronotropic infusion alongside the antidote"],
       (0, 40), actions=("glucagon", "calcium", "atropine")),
    _d("The antidote fades and this engine does not run the definitive therapy: the "
       "continuity decision is who is involved and where this patient is watched.",
       ["Asks for help with the poisoning named",
        "decides the level of care and states what is watched as the antidote wears off"],
       ["Toxicology or the poisons centre named as the help",
        "a critical-care bed decided alongside the referral",
        "mental-health involvement stated for the intent"],
       (15, 180), actions=("consult", "disposition")),
    [_bradycardia_no_support(),
     _event(
         "bradycardia_cause_unexamined", "critical_omission",
         "The rate is treated without the cause being pursued, in a patient whose poisoning "
         "is in the medication history.",
         "Atropine or pacing is executed, the response is inadequate, and nothing in the "
         "record pursues the cause: no medication history is obtained and no antidote is "
         "given within the window. It applies whether or not the learner asked: the partner "
         "is present with the packet and can be asked, and never asking is part of the "
         "omission rather than an excuse for it.",
         ["An executed rate-supporting action", "the observables after it"], (5, 90),
         ["An antidote given", "a recorded medication history",
          "a toxicology consultation with the poisoning named"],
         "An executed atropine or pacing action with no antidote, no consultation and no "
         "recorded medication history in any executed turn of the window.",
         ["The encounter closed before any rate-supporting action was executed"],
         ["D2", "D5"],
         [("medications", "the empty propranolol pack and the full one that was there yesterday"),
          ("risk_factors", "the argument and the weeks she had been low")])]))

# The potassium case is declared apart from the other three because the window
# of its critical event does not start where theirs do. Faculty decision
# 2026-09-23: the calcium is given on the clinical suspicion, and the tracing is
# what raises it. A resident who waits for the laboratory has already waited.
CASES.update(_bradycardia(
    "bradycardia_hyperk_63m",
    _d("The tracing carries the severity before any number does: the complex widens as the "
       "rate falls. The missed dialysis and the potassium-retaining drug are there for the "
       "asking, and the laboratory confirms rather than reveals.",
       ["Reads the broad complex and the slow rate together",
        "obtains the dialysis history and requests the potassium"],
       ["Naming the hyperkalaemia from the tracing and the history before the result",
        "the venous gas used for the potassium rather than the panel"],
       (0, 30), studies=("ecg", "basic_labs", "vbg"), examination=("Cardiac",)),
    _d("Calcium, a nebulised beta agonist and dextrose are all executable, and the engine "
       "keeps them apart: one protects the membrane and the others move the potassium.",
       ["Executes calcium on the suspicion, before the result",
        "adds a shifting treatment rather than stopping at the calcium"],
       ["Calcium chloride instead of the gluconate, stated as such",
        "the shifting treatments started while the result is awaited"],
       (0, 30), actions=("calcium", "bronchodilator", "dextrose")),
    _d("Nothing given here removes any potassium, and this engine does not dialyse: the "
       "continuity decision is who does, and what holds this patient until then.",
       ["Arranges the treatment that removes the potassium, or the service that provides it",
        "states what is watched as the calcium and the shift wear off"],
       ["Nephrology or the dialysis unit named",
        "transfer stated as the pathway to dialysis",
        "a critical-care bed decided alongside the referral"],
       (15, 180), actions=("consult", "disposition")),
    [_bradycardia_no_support(),
     _event(
         "hyperk_calcium_awaited_the_laboratory", "critical_omission",
         "Calcium is not given on the clinical suspicion, and the encounter waits for the "
         "potassium result instead.",
         "The tracing carries a broad complex with a bradycardia, and no calcium is executed "
         "within the window. The window runs from the arrival tracing and not from the "
         "laboratory, because the treatment is given on the suspicion: a resident who waits "
         "for the number has already waited. It applies whether or not the learner asked "
         "about the dialysis: the patient is in front of them and can be asked, and never "
         "asking is part of the omission rather than an excuse for it.",
         ["Arrival observables and the monitor", "the arrival tracing"], (0, 20),
         ["Calcium by either salt", "calcium withheld with a stated reason the record supports"],
         "An executed calcium action, or its absence across every executed turn in the window.",
         ["The encounter closed before the window opened",
          "the interpreter refused the order and the resident was never told what it could accept"],
         ["D1", "D3"],
         [("medical_history", "the dialysis and the sessions that were missed"),
          ("medications", "the spironolactone started a month ago")]),
     _event(
         "hyperk_no_definitive_removal", "critical_omission",
         "The potassium is shifted and nobody is asked to remove it.",
         "Calcium or a shifting treatment is executed and no consultation and no disposition "
         "addresses removing the potassium within the window, so the encounter ends with a "
         "patient whose potassium is still in them.",
         ["An executed calcium or shifting action"], (15, 180),
         ["Nephrology or the dialysis unit involved",
          "transfer stated as the pathway to dialysis",
          "admission to a unit stated as being for dialysis"],
         "An executed calcium or shifting action with no consultation and no disposition "
         "naming the removal in any executed turn of the window.",
         ["The encounter reached its horizon before the window closed"],
         ["D5"],
         [("medical_history", "that he is on haemodialysis three times a week")])]))


# --- trauma -------------------------------------------------------------------
# Faculty decisions 2.1 to 2.4 of 2026-09-23. One mechanism per case, because a
# combined one makes it impossible to say which omission the patient answered
# for. What both declare is a sequence rather than a list of interventions.
_TRAUMA_D2 = _d(
    "The E-FAST reports all five windows and the pelvis is filmed; the examination and the "
    "history separate a source that can be compressed from one that cannot.",
    ["Looks for the source rather than only treating the shock",
     "relates the study and the examination to one explanation of where the blood is"],
    ["Reaching the source from the examination and the chest film",
     "the E-FAST read alongside the examination rather than instead of it"],
    (0, 40), studies=("efast", "pelvis_xray", "chest_xray"),
    examination=("General appearance", "Abdomen"))

_TRAUMA_D4 = _d(
    "The engine runs a clock and bleeds on it: what a measure stopped, and what it did not, "
    "is visible within minutes.",
    ["States a reassessment interval and what will be checked",
     "checks the pressure, the rate and the perfusion after each measure"],
    ["Reassessing the perfusion rather than the pressure alone",
     "a shorter interval than stated"],
    (2, 60), actions=("reassessment",))


def _trauma(case_id, d1, d3, d5, critical_events):
    return {case_id: {
        "domains": {"D1": d1, "D2": _TRAUMA_D2, "D3": d3, "D4": _TRAUMA_D4, "D5": d5},
        "information": ("Arrival observables and the monitor",
                        "the mechanism and the course since it, on asking",
                        "the examination of the wound, the chest, the abdomen and the pelvis",
                        "the E-FAST, the chest film, the pelvis film and the laboratory"),
        "closure": "A disposition is decided, or the horizon of the encounter is reached.",
        "engine_limits": ("The engine has no operating theatre; a referral is recorded, never "
                          "its result, so the encounter is about recognising that one is "
                          "needed and holding the patient until it is.",
                          "It does not perform a resuscitative thoracotomy or place an "
                          "endovascular balloon."),
        "critical_events": critical_events,
    }}


CASES.update(_trauma(
    "trauma_limb_hemorrhage_27m",
    _d("The bleeding is visible on arrival and it is compressible: the priority is to stop it "
       "before the airway, the breathing or the imaging, which is what the x of the algorithm "
       "means.",
       ["Controls the bleeding within the window",
        "does it before the other elements of the primary survey"],
       ["Direct pressure first with a tourniquet when it does not hold",
        "control applied while another member of the team begins the rest"],
       (0, 10), actions=("hemorrhage_control",)),
    _d("A tourniquet, direct pressure and packing are all executable; blood, tranexamic acid "
       "and warmed fluid are the resuscitation the loss calls for.",
       ["Executes a control measure naming the site",
        "replaces with blood rather than with crystalloid alone"],
       ["Packing where a tourniquet cannot be applied",
        "tranexamic acid early, stated as an adjunct and not a substitute"],
       (0, 30), actions=("hemorrhage_control", "blood", "tranexamic_acid")),
    _d("A controlled limb source still needs the wound managed and the volume accounted for: "
       "the continuity decision is who takes over and what they are told.",
       ["Arranges the definitive management of the wound",
        "states the blood given, the tourniquet time and what is watched"],
       ["Surgery or the trauma team named",
        "theatre stated as the destination with the tourniquet time handed over"],
       (10, 180), actions=("consult", "disposition")),
    [_event(
        "trauma_no_hemorrhage_control", "critical_omission",
        "Exsanguinating external bleeding is not controlled before the rest of the primary "
        "survey.",
        "The arrival record carries visible external bleeding with shock, and no tourniquet, "
        "direct pressure or packing is executed within the window, whatever else was done "
        "first. The window is ten minutes because that is what the x of the algorithm means.",
        ["Arrival observables", "the examination of the wound"], (0, 10),
        ["A tourniquet, direct pressure or packing",
         "control applied while another member of the team begins the rest"],
        "An executed hemorrhage-control action, or its absence across every executed turn in "
        "the window.",
        ["The encounter closed before the window opened",
         "the interpreter refused the order and the resident was never told what it could accept"],
        ["D1", "D3"],
        [("bleeding", "that it has not stopped and the dressing is soaked through"),
         ("chief_complaint", "the injury in the patient's own words")]),
     _event(
         "trauma_crystalloid_instead_of_blood", "dangerous_action",
         "A large volume of crystalloid is given to replace blood that is still being lost.",
         "More than two litres of crystalloid is executed and no blood is, in a patient whose "
         "record carries continuing haemorrhage.",
         ["Arrival observables", "the executed fluid volumes"], (0, 60),
         ["Blood given alongside or instead", "warmed fluid while blood is being prepared",
          "crystalloid stated as the bridge to blood"],
         "Executed crystalloid above two litres with no executed blood action in the window.",
         ["Blood was executed at any point in the window"],
         ["D3"])]))

CASES.update(_trauma(
    "trauma_hemothorax_41m",
    _d("Reduced air entry with dullness and shock: the priority is to drain the chest and to "
       "resuscitate at the same time, not one after the other.",
       ["Names the threat within the window", "drains and resuscitates together"],
       ["Naming it as a haemothorax without the word massive",
        "resuscitation begun while the drain is being prepared"],
       (0, 20), actions=("chest_decompression", "blood")),
    _d("A chest tube drains this collection and a needle does not; blood and tranexamic acid "
       "are the resuscitation. The engine keeps the chest filling after the drain.",
       ["Drains with a tube on the correct side",
        "replaces with blood rather than with crystalloid alone"],
       ["A needle first with the tube stated as following",
        "tranexamic acid early, stated as an adjunct"],
       (0, 30), actions=("chest_decompression", "blood", "tranexamic_acid")),
    # Faculty decision 2.4, in their own words: the massive haemothorax is not
    # defined by the drained volume but by the instability that persists, and
    # what it demands is that the resident looks again.
    _d("The chest has been drained and the patient is still unstable. The decision is whether "
       "another site is bleeding, and when there is nowhere else, that the treatment is a "
       "theatre this engine does not have.",
       ["Looks again for another site after the drain rather than only transfusing",
        "asks for surgery once the other sites are excluded"],
       ["The E-FAST or the pelvis film repeated after the drain",
        "surgery involved with the continuing output stated",
        "transfer stated as the pathway to theatre"],
       (10, 180), actions=("consult", "disposition", "diagnostic")),
    [_event(
        "trauma_undrained_hemothorax", "critical_omission",
        "A massive haemothorax with shock is not drained.",
        "The examination and the chest film carry a large collection with shock, and no chest "
        "tube is executed within the window.",
        ["Arrival observables", "the chest radiograph or the E-FAST result"], (0, 30),
        ["A chest tube on the correct side",
         "a needle first with the tube following in the same window"],
        "An executed chest-tube action, or its absence across every executed turn in the window.",
        ["The encounter closed before the window opened"],
        ["D1", "D3"],
        [("breathing", "that it began immediately and is worse lying flat"),
         ("chest_pain", "the left-sided pain that is worse with breathing")]),
     _event(
         "trauma_drained_and_never_looked_again", "critical_omission",
         "The chest is drained, the patient stays unstable, and no other site is looked for.",
         "A chest tube is executed, the observables afterwards still carry hypotension or "
         "delayed capillary refill, and no E-FAST, no pelvis film and no surgical consultation "
         "appears after the drain. The faculty's rule of 2026-09-23: a massive haemothorax is "
         "defined by the instability and not by the volume that came out, so a resident who "
         "transfuses and waits has stopped looking. It applies whether or not the learner "
         "asked about the mechanism: the patient is in front of them and can be asked, and "
         "never asking is part of the omission rather than an excuse for it.",
         ["An executed chest-tube action", "the observables recorded after it"], (10, 180),
         ["An E-FAST or a pelvis film requested after the drain",
          "surgery involved with the continuing instability stated",
          "theatre decided as the destination"],
         "An executed chest-tube action with persisting instability and no study and no "
         "surgical consultation in any executed turn after it.",
         ["The observables recorded after the drain no longer carry instability",
          "the encounter reached its horizon before the window closed"],
         ["D2", "D5"],
         [("exposure", "the seatbelt bruising across the chest and abdomen"),
          ("bleeding", "that no external source has been found")])]))
