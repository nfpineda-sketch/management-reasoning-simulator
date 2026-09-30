"""TD1, F1, C1 and C3, declared case by case from the faculty's TDFC decisions (cycle 8).

Each row is the one ``tdfc_review.final_states`` derives from the cycle 5 draft
(docs/tdfc/BORRADOR_TDFC.md) and the faculty's answers:

* TDFC-1 to 6 and 8, approved conceptually "según las recomendaciones actuales"
  on 2026-09-28 (cycle 7 instruction, §28), their implementation deferred to
  cycle 8. A row one of them settles says which (``decision_group``).
* The draft's clear rows, kept under the same approval (``decision_group``
  "clear"). The residual doubts the draft listed about some of them are in
  docs/tdfc/TDFC_TABLA_FINAL.md, for the faculty to look at.

A YES row says why the case really offers the objective, which component of the
EPA it lets the faculty observe, what the Management Trace might show, and what
stays outside the encounter: an opportunity YES is never the full EPA observed
(§30, §92). A NO row says why not: not evaluable, never a failure. The expected
evidence guides and is not a whitelist.

acs_54m_inferior's rows waited for DF-20. The faculty closed it on 2026-09-29 with no
change to the case (cycle 9): a physiologic right-ventricular involvement can coexist with
a qualitative emergency POCUS that is normal or non-diagnostic, so its opportunities rest on
the physiology, the monitor and the ECG, never on the ultrasound. Its rows are the ones the
approved decisions already derived (TD1, F1 and C1 YES, C3 NO), released by that closure.
C4 is NO for the whole observation environment (case_assessment_bank.C4_DECLARATIONS).
Nothing here changes a case, an event, a domain or a score, and an encounter
started before keeps the declaration it was frozen with.
"""
from __future__ import annotations

_BASIS = ("Cycle 7 instruction §28 (2026-09-28): TDFC-1 to 6 and 8 approved conceptually as recommended "
          "in docs/tdfc/TDFC_DECISIONS_FOR_NICOLAS.md; written in cycle 8.")


def _review(group, released=None):
    reviewed = {"by": "Nicolás Pineda", "on": "2026-09-28", "source": "faculty_decision",
                "decision_group": group, "version": "TDFC-REVIEW-1", "basis": _BASIS}
    if released:
        reviewed["released"] = released
    return reviewed


# What released acs_54m_inferior's rows: the closing of DF-20 (cycle 9).
_DF20_CLOSED = {"by": "Nicolás Pineda", "on": "2026-09-29", "decision": "DF-20 closed, no change to the case",
                "basis": ("Cycle 9 instruction §16, §17, §46 and §47 (2026-09-29): physiologic right-ventricular "
                          "involvement can coexist with a qualitative emergency POCUS that is normal or "
                          "non-diagnostic; the rows the approved TDFC decisions derived are applied, and the "
                          "opportunities do not rest on the POCUS.")}


# What stays outside any encounter of this simulator, objective by objective (objectives.py
# limitations and the TDFC decisions). A row may add what its own case leaves out.
OUTSIDE = {
    "TD1": "Real help activation, teamwork and hands-on basic life support; the real clinical context.",
    "F1": ("Assisting a real resuscitation team; procedural skills such as vascular or intraosseous access; "
           "cardiac arrest and paediatrics; the real clinical context."),
    "C1": "Real team leadership; the full breadth of critical illness; procedural skills; the real clinical context.",
    "C3": ("Intubation in a normal or anticipated difficult airway, post-intubation care and ventilator adjustment "
           "(adjustable only in asthma), manual ventilation and laryngoscopy; paediatrics and the real clinical "
           "context."),
}


def _yes(objective, group, rationale, component, evidence, also_outside=None, released=None):
    outside = OUTSIDE[objective] + (" " + also_outside if also_outside else "")
    return {"opportunity": "yes", "rationale": rationale, "observable_component": component,
            "expected_evidence": tuple(evidence), "outside_the_encounter": outside,
            "reviewed": _review(group, released)}


def _no(group, reason, released=None):
    return {"opportunity": "no", "reason": reason, "reviewed": _review(group, released)}


# --- the decided rows' shared wording -------------------------------------------------------
_TDFC1 = ("Haemodynamically stable: without physiological instability, what TD1 observes cannot show. "
          "Recognising the ECG pattern that needs immediate reperfusion is observed by the case's rubric (D1) and "
          "belongs to C5, which is not enabled (TDFC-1).")
_TDFC3 = ("With correct management there is no second, critical phase by design: first-line treatment stabilises "
          "the hypoxaemia. The decisions the case puts first are others; 'respiratory failure by definition' is a "
          "category, not an opportunity (TDFC-3).")
_TDFC4 = ("Scope: the Royal College places the resuscitation of major trauma in C2, which stays disabled (DF-4). "
          "Counting it under C1 would observe C2's content under another name (TDFC-4).")
_TDFC6_NO = "F1 already observes the oxygen order (TDFC-6)."
_HYPO_OUTSIDE = "Oxygenation and ventilation, pressure support and critical arrhythmias, which these cases do not have."
_HYPO_F1 = ("Prioritising and starting the correction of a reversible cause of impaired consciousness, by a route "
            "that delivers, and assessing the response in glucose and consciousness")
_TDFC6_OUTSIDE = "Intubation itself, in a normal or an anatomically difficult airway."

DECLARATIONS = {
    # Released by the closing of DF-20 (cycle 9). The right-ventricular involvement is the case's
    # physiology, read from the monitor, the ECG and the response to preload; no row rests on the POCUS.
    "acs_54m_inferior": {
        "TD1": _yes("TD1", "clear",
                    "Borderline perfusion (SBP 100 with HR 58, cold extremities, capillary refill 3 s, marked "
                    "diaphoresis) in an inferior infarct whose pressure depends on right-ventricular preload; the "
                    "engine brings a complete AV block at about 45 min of occlusion, before the artery can be opened.",
                    "Recognising the incipient hypoperfusion and the bradyarrhythmia, and starting support and "
                    "monitoring.",
                    ("names the borderline perfusion and the preload-dependent right ventricle", "monitors",
                     "names the complete block as unstable and acts on it", "sets when to reassess"),
                    released=_DF20_CLOSED),
        "F1": _yes("F1", "clear",
                   "The pressure depends on preload: a nitrate lowers it sharply and volume restores it "
                   "(docs/AUDITORIA_ACS_54M_INFERIOR.md), and the complete block is a critical arrhythmia to manage. "
                   "The opportunity rests on the physiology, the monitor and the ECG, not on the bedside ultrasound.",
                   "Prioritising prudent volume over the nitrate and treating the block, assessing the response.",
                   ("withholds the nitrate because of the preload dependence", "gives a bounded bolus and reassesses "
                    "the pressure", "atropine and, if it fails, pacing with output and capture confirmed"),
                   released=_DF20_CLOSED),
        "C1": _yes("C1", "TDFC-5",
                   "Not in shock on arrival. By design the complete block and the right-ventricular drift lower the "
                   "pressure while reperfusion is awaited (HR 42 around minute 50), even with immediate activation: "
                   "the artery opens 90 min after the cath lab is activated. It does not depend on showing the right "
                   "ventricle on ultrasound.",
                   "Integrating rhythm, right-ventricular preload and the pending reperfusion, and revising the plan "
                   "by the response.",
                   ("relates the fall in pressure to the block and the right ventricle",
                    "adjusts volume, atropine or pacing", "keeps the reperfusion and says what it watches until the "
                    "cath lab"),
                   released=_DF20_CLOSED),
        "C3": _no("clear", "SpO2 96 % and clear lungs: an inferior infarct with right-ventricular involvement barely "
                           "congests in the engine, and there is no oxygen or ventilation decision.",
                  released=_DF20_CLOSED),
    },
    "acs_66f_nonst": {
        "TD1": _no("TDFC-1", _TDFC1),
        "F1": _no("clear", "Normotensive, well perfused and not hypoxaemic: antiplatelet treatment and a monitored "
                           "assessment are not resuscitation."),
        "C1": _no("clear", "No shock, respiratory failure or sepsis: a non-occlusive acute coronary syndrome with a "
                           "deferrable angiography, which is C5 content (not enabled)."),
        "C3": _no("clear", "SpO2 95 % with mild effort: oxygen is not a decision of the case."),
    },
    "acs_61m_posterior": {
        "TD1": _no("TDFC-1", _TDFC1),
        "F1": _no("clear", "Needs no resuscitation; with the artery closed the engine adds little congestion in this "
                           "territory (2 to 3 points of SpO2 by minute 90)."),
        "C1": _no("clear", "No critical resuscitation: the case teaches recognising the occlusion (C5)."),
        "C3": _no("clear", "SpO2 96 %, no respiratory effort."),
    },
    "acs_52m_de_winter": {
        "TD1": _no("TDFC-1", _TDFC1),
        "F1": _no("clear", "Needs no resuscitation on arrival. The general model congests the lung while reperfusion "
                           "is awaited (SpO2 below 90 % only after minute 80), which neither the case nor its "
                           "declaration supports; left out in TDFC-5."),
        "C1": _no("clear", "No shock or respiratory failure; the model's late congestion does not make a critical "
                           "resuscitation."),
        "C3": _no("clear", "SpO2 95 % on arrival; the late hypoxaemia stays out for the reason given for F1."),
    },
    "acs_48m_wellens": {
        "TD1": _no("clear", "Pain-free, normal signs and an open artery: no instability to recognise. The decision is a "
                            "scheduled angiography and not provoking ischaemia; ventricular fibrillation appears only "
                            "after a stress test, which is an error."),
        "F1": _no("clear", "Nothing to resuscitate."),
        "C1": _no("clear", "No critical condition."),
        "C3": _no("clear", "No respiratory compromise."),
    },
    "acs_70f_left_main": {
        "TD1": _yes("TD1", "clear",
                    "Hypoperfusion (cold, capillary refill 3 s, lactate 3.1, SBP 104 with HR 112) and congestion in a "
                    "proximal lesion: cardiogenic pre-shock.",
                    "Recognising cardiogenic pre-shock and starting support and monitoring while reperfusion is arranged.",
                    ("names the hypoperfusion and its ischaemic origin", "monitors and orders support",
                     "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "The declaration expects the hypoperfusion addressed and accepts oxygen and cautious volume; the "
                   "engine answers volume poorly in this profile.",
                   "Prioritising cautious haemodynamic support and assessing the response.",
                   ("limits or withholds volume because of the congestion, or gives a bounded bolus",
                    "considers support", "compares pressure, perfusion and breathing after each measure")),
        "C1": _yes("C1", "clear",
                   "Evolving cardiogenic shock: with every minute of occlusion the engine lowers the SBP (about 9 mmHg "
                   "at 90 min) and congests the lung, even with immediate activation.",
                   "Integrating support, congestion and reperfusion, and revising the plan by the response.",
                   ("relates hypoperfusion and congestion to the left main lesion",
                    "adjusts volume, oxygen or NIV and support", "keeps the invasive urgency and says what it watches")),
        "C3": _yes("C3", "TDFC-5",
                   "Arrives with SpO2 94 % and crackles; by design the congestion progresses with the artery closed "
                   "(SpO2 90 % at minute 60, below it from minute 80, work of breathing 'Exhausted') while the "
                   "reperfusion is awaited, and NIV relieves it in the engine. The declaration names oxygen.",
                   "Deciding oxygen or NIV for a congestion that progresses in an evolving cardiogenic shock, and "
                   "reassessing SpO2, respiratory rate, effort and pressure.",
                   ("names the congestion (crackles, the film, the falling SpO2)",
                    "orders oxygen to a target or NIV", "reassesses SpO2, respiratory rate and pressure")),
    },
    "anaphylaxis_29f": {
        "TD1": _yes("TD1", "clear",
                    "Shock (84/46) with stridor, wheeze and SpO2 91 % minutes after an exposure; without epinephrine "
                    "the engine takes her to arrest in about 25 min.",
                    "Recognising anaphylaxis with airway and circulatory compromise and starting treatment.",
                    ("names the reaction and its severity", "orders IM epinephrine with its dose before anything else",
                     "sets the reassessment to the IM route's timing")),
        "F1": _yes("F1", "clear",
                   "Epinephrine, volume and oxygen are the declared initial interventions (D3); the engine shows the "
                   "IM dose's effect at about 4 min.",
                   "Prioritising IM epinephrine and adding volume and oxygen, assessing the response in time.",
                   ("epinephrine 0.5 mg IM", "volume and oxygen beside it, not instead of it",
                    "reassesses pressure, SpO2 and stridor after the dose")),
        "C1": _yes("C1", "clear",
                   "Shock with a compromised airway: it may need another dose or an infusion, and the engine brings a "
                   "biphasic reaction 75 min after stabilisation.",
                   "Integrating the response to epinephrine, the airway and volume, and recognising the return.",
                   ("compares the response with the one expected", "escalates to an infusion if it falls short",
                    "decides the observation and recognises and treats the return")),
        "C3": _yes("C3", "clear",
                   "An upper airway threat (stridor, lip angioedema) the engine charges in SpO2 and only epinephrine "
                   "relieves; the declaration names the airway (D1, D4) and oxygen (D3), and preparing the airway can "
                   "be executed. No complete obstruction or difficult intubation is modelled.",
                   "Anticipating a difficult airway, giving oxygen and reassessing the airway after epinephrine.",
                   ("names the stridor as a threat", "orders oxygen", "prepares the airway or calls for help",
                    "reassesses the stridor after the dose"),
                   also_outside="A complete obstruction and a difficult intubation are not modelled."),
    },
    "anaphylaxis_63m_betablocked": {
        "TD1": _yes("TD1", "clear",
                    "Shock (76/42) with no compensatory tachycardia, drowsiness and SpO2 89 % after a sting.",
                    "Recognising anaphylactic shock with an inappropriately normal heart rate and starting treatment.",
                    ("names the shock and the reaction", "orders epinephrine with dose and route", "reassesses")),
        "F1": _yes("F1", "clear",
                   "Epinephrine, volume and oxygen can be executed and are declared; the engine answers a third of the "
                   "usual because of the beta-blockade.",
                   "Prioritising epinephrine and volume, and assessing a response that falls short.",
                   ("IM epinephrine, volume and oxygen", "compares pressure and heart rate after the dose")),
        "C1": _yes("C1", "clear",
                   "Refractory anaphylaxis: epinephrine yields a third, and the case's lever is the history (atenolol) "
                   "and glucagon. It forces a revision of the working model.",
                   "Integrating the lack of response, looking for its cause and changing strategy.",
                   ("compares what was expected with what was observed", "identifies the beta-blockade",
                    "gives glucagon or starts an infusion", "calls for help naming the refractoriness")),
        "C3": _no("TDFC-6", "The hypoxaemia follows the reaction: once it is controlled, SpO2 reaches 99 %. The "
                            "lever is pharmacological and oxygen is given either way. " + _TDFC6_NO),
    },
    "asthma_24f": {
        "TD1": _yes("TD1", "clear",
                    "Severe respiratory distress (RR 34, SpO2 90 %, PEF 35 %, speaking in phrases).",
                    "Recognising the severity of the obstruction and starting treatment and reassessment.",
                    ("names the severe obstruction by the effort or the PEF", "treats before completing the work-up",
                     "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Bronchodilator, corticosteroid and oxygen can be executed and are declared; the engine moves the "
                   "effort and SpO2 with each.",
                   "Prioritising bronchodilation, corticosteroid and oxygen, and assessing the response.",
                   ("repeated or continuous bronchodilator", "corticosteroid", "oxygen",
                    "reassesses effort and SpO2")),
        "C1": _no("TDFC-3", _TDFC3 + " In this case: bronchodilator and corticosteroid improve her; the decision is "
                                     "to escalate by the response."),
        "C3": _no("TDFC-6", "The bronchodilator corrects the hypoxaemia (SpO2 99 % with 3 L/min at 20 min), which "
                            "does not evolve by design. " + _TDFC6_NO),
    },
    "asthma_49m": {
        "TD1": _yes("TD1", "clear",
                    "Ventilatory failure: drowsy, very poor air entry, pH 7.30 and PaCO2 51.",
                    "Recognising fatigue and hypercapnia as the threat and starting support.",
                    ("names the ventilatory failure, not only the obstruction", "acts with that urgency",
                     "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Bronchodilator, corticosteroid and ventilatory support are declared (D3); the engine answers the "
                   "obstruction and the support separately.",
                   "Prioritising ventilatory support without leaving the obstruction's treatment, and assessing the "
                   "response.",
                   ("bronchodilator and corticosteroid", "NIV or preparation for intubation",
                    "reassesses effort, gases and SpO2")),
        "C1": _yes("C1", "clear",
                   "Ventilatory failure: deciding NIV or intubation in time (the engine rates it premature, timely or "
                   "late), setting the ventilator and managing post-intubation hypotension and barotrauma.",
                   "Integrating support, ventilation and complications, and revising the plan by the response.",
                   ("relates gases and consciousness to the decision to intubate",
                    "adjusts the ventilator for auto-PEEP or hypotension", "reassesses")),
        "C3": _yes("C3", "clear",
                   "Ventilatory support is the decision the case turns on (D3) and has its own critical event; it is "
                   "the only family in the bank whose ventilator can be adjusted after intubation.",
                   "Deciding NIV or intubation in time, setting ventilation for air trapping and reassessing.",
                   ("names fatigue and hypercapnia", "prepares volume and induction (ketamine)",
                    "intubates in time or justifies NIV", "low rate and long expiration; checks plateau and pressure")),
    },
    "bradycardia_ccb_68m": {
        "TD1": _yes("TD1", "clear",
                    "Unstable bradycardia: HR 38, SBP 74, cold and capillary refill 4 s after a collapse.",
                    "Recognising bradycardia with shock and starting support while the cause is sought.",
                    ("names the instability", "acts before completing the work-up", "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Atropine, calcium and glucagon can be executed; the engine answers according to the cause.",
                   "Prioritising rhythm support and the antidote, and assessing the response.",
                   ("atropine and, when it fails, calcium with dose and route",
                    "reassesses heart rate, pressure and perfusion after each attempt")),
        "C1": _yes("C1", "clear",
                   "Sustained toxic shock: the right antidote works and fades, and the engine offers no definitive "
                   "therapy; it forces reassessing, repeating and calling for help.",
                   "Integrating antidote, support and its fading, and deciding the continuity.",
                   ("recognises that atropine is not enough", "gives the cause's antidote",
                    "repeats it or adds support", "calls toxicology or the ICU")),
        "C3": _no("clear", "SpO2 96 %, normal breathing."),
    },
    "bradycardia_avb3_78f": {
        "TD1": _yes("TD1", "clear",
                    "Unstable bradyarrhythmia: HR 32, SBP 78, drowsy and with syncope.",
                    "Recognising the block with hypoperfusion and starting rhythm support.",
                    ("names the block as unstable", "acts", "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Atropine (which fails in an infranodal block) and transcutaneous pacing with output and a capture "
                   "threshold (70 mA).",
                   "Prioritising electrical rhythm support and assessing the response.",
                   ("atropine or pacing first", "rate and output", "confirms capture with pulse and pressure")),
        "C1": _yes("C1", "clear",
                   "Shock from the block: revising the plan when atropine fails, confirming mechanical capture (a "
                   "critical event) and arranging a definitive pacemaker.",
                   "Integrating the lack of response, the capture and the continuity.",
                   ("leaves atropine after it fails", "confirms capture with pulse and pressure and adjusts the output",
                    "asks for a definitive pacemaker and says what it watches")),
        "C3": _no("clear", "SpO2 95 % and RR 20; drowsy with no airway compromise."),
    },
    "bradycardia_bb_54f": {
        "TD1": _yes("TD1", "clear",
                    "Bradycardia with shock (HR 40, SBP 80, cold) after a propranolol ingestion; the examination "
                    "describes her drowsy.",
                    "Recognising bradycardia with shock and starting support.",
                    ("names the instability", "acts", "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Glucagon, calcium and atropine can be executed; the engine answers according to the cause.",
                   "Prioritising this cause's antidote and assessing the response.",
                   ("glucagon with dose and route", "reassesses heart rate, pressure and perfusion")),
        "C1": _yes("C1", "clear",
                   "Beta-blocker shock: the antidote is not the previous case's, it fades and help is needed; the "
                   "suicidal intent enters the continuity.",
                   "Integrating antidote, support and continuity.",
                   ("tells this poisoning apart", "gives glucagon, repeats it or adds support",
                    "calls toxicology, the ICU and mental health")),
        "C3": _no("clear", "SpO2 97 %, slow but regular breathing, no hypercapnia (PaCO2 40)."),
    },
    "bradycardia_hyperk_63m": {
        "TD1": _yes("TD1", "clear",
                    "HR 38 with a 180 ms QRS and SBP 84: the tracing gives the severity before the potassium does.",
                    "Recognising a wide-QRS bradycardia as the threat and starting treatment on suspicion.",
                    ("names the wide QRS and the bradycardia", "acts before the result", "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Calcium on suspicion before the laboratory (a critical event), plus measures that shift the "
                   "potassium.",
                   "Prioritising calcium and the shift, and assessing the response.",
                   ("calcium with dose and route", "nebulised salbutamol or glucose",
                    "reassesses heart rate, QRS and pressure")),
        "C1": _yes("C1", "clear",
                   "Calcium, shift and removal in sequence: the potassium keeps rising, the calcium fades and the "
                   "engine does not dialyse.",
                   "Integrating protection, shift and removal, and deciding the continuity.",
                   ("repeats calcium if the QRS widens again", "adds the shift",
                    "asks for dialysis or nephrology and says what it watches")),
        "C3": _no("clear", "SpO2 96 %, clear lungs."),
    },
    "gi_bleed_57m": {
        "TD1": _yes("TD1", "clear",
                    "Haemorrhagic shock (88/54, HR 124, capillary refill 5 s) with melaena.",
                    "Recognising haemorrhagic shock and resuscitating before completing the work-up.",
                    ("names the bleeding and the hypoperfusion", "starts replacement", "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Blood, volume, a proton pump inhibitor and the consult can be executed; the engine yields less "
                   "with crystalloid than with blood.",
                   "Prioritising replacement with blood and assessing the response.",
                   ("transfuses", "crystalloid only as a bridge", "reassesses pressure and perfusion after the volume")),
        "C1": _yes("C1", "clear",
                   "Sustained resuscitation: the bleeding continues until the endoscopy, which the engine performs "
                   "only with SBP >= 90 and Hb >= 7, or with blood running.",
                   "Integrating replacement, haemostasis and reassessment.",
                   ("relates the response to the active bleeding", "adjusts the replacement",
                    "asks for endoscopy and defines the destination and what it watches")),
        "C3": _no("clear", "SpO2 97 %, no respiratory effort."),
    },
    "gi_bleed_72f": {
        "TD1": _yes("TD1", "clear",
                    "Hypoperfusion with a quiet presentation (98/62, HR 112, capillary refill 4 s, cold); D1 asks for "
                    "recognising it without a dramatic symptom.",
                    "Recognising hypoperfusion from bleeding despite an unremarkable complaint.",
                    ("names the relevant bleeding and its consequence", "acts on the perfusion",
                     "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "The same interventions and the same model as gi_bleed_57m.",
                   "Prioritising replacement with blood and assessing the response.",
                   ("transfuses", "crystalloid only as a bridge", "reassesses pressure and perfusion")),
        "C1": _yes("C1", "clear",
                   "Compensated shock with Hb 6.4 and the same endoscopy conditioned on resuscitation as in "
                   "gi_bleed_57m.",
                   "Integrating replacement, haemostasis and reassessment.",
                   ("relates the response to the bleeding", "adjusts the replacement",
                    "asks for endoscopy and defines the destination")),
        "C3": _no("clear", "SpO2 96 %, no respiratory effort."),
    },
    "hypoglycemia_28m": {
        "TD1": _yes("TD1", "clear",
                    "Impaired consciousness with a glucose of 34 mg/dL; after 20 min below 40 mg/dL the engine produces "
                    "a seizure.",
                    "Recognising the reversible cause of impaired consciousness and correcting it first.",
                    ("asks for a capillary glucose", "names the neuroglycopenia", "gives glucose",
                     "sets the control")),
        "F1": _yes("F1", "TDFC-2",
                   "A clinically significant situation, not a category: neuroglycopenia the engine turns into a "
                   "seizure after 20 min below 40 mg/dL. It presents as a possible stroke, so prioritising the glucose "
                   "over the work-up is a real decision (TDFC-2). The weakest of the three: the response is simple.",
                   _HYPO_F1 + ".",
                   ("IV glucose with its dose before the imaging", "a glucose and consciousness control at a set time"),
                   also_outside=_HYPO_OUTSIDE),
        "C1": _no("clear", "One correction resolves the threat: no shock, respiratory failure or sepsis, and no "
                           "recurrence in the design."),
        "C3": _no("clear", "Airway and breathing preserved (SpO2 98 %)."),
    },
    "hypoglycemia_76f": {
        "TD1": _yes("TD1", "clear",
                    "Obtunded (opens her eyes only to firm stimulus) with a glucose of 38 mg/dL.",
                    "Recognising the reversible cause of impaired consciousness and correcting it first.",
                    ("asks for a capillary glucose", "names the neuroglycopenia", "gives glucose",
                     "sets the control")),
        "F1": _yes("F1", "TDFC-2",
                   "Neuroglycopenia from a sulfonylurea: the resuscitation is the glucose, and the engine makes the "
                   "hypoglycaemia recur, so assessing the response is a real decision (TDFC-2).",
                   _HYPO_F1 + ", including recognising the recurrence.",
                   ("IV glucose", "serial controls", "a glucose infusion or octreotide when it recurs"),
                   also_outside=_HYPO_OUTSIDE),
        "C1": _no("clear", "The recurrence (infusion, octreotide, observation) is surveillance and continuity, which "
                           "R1-06 looks for; hypoglycaemia is not a C1 condition."),
        "C3": _no("clear", "SpO2 97 % and RR 18. The engine refuses the oral route while she is not alert, but the "
                           "airway is not a decision of the case."),
    },
    "hypoglycemia_54m_thiamine": {
        "TD1": _yes("TD1", "clear",
                    "Drowsy with a glucose of 32 mg/dL, nystagmus and an unsteady gait.",
                    "Recognising the reversible cause of impaired consciousness and correcting it first.",
                    ("asks for a capillary glucose", "names the neuroglycopenia", "gives glucose",
                     "sets the control")),
        "F1": _yes("F1", "TDFC-2",
                   "The line he arrives with is not in the vein: the bolus barely raises the glucose and the delivery "
                   "has to be checked (D4). It is the assessment of the response F1 asks for (TDFC-2).",
                   _HYPO_F1 + ", including recognising a line that does not deliver and restoring one that does.",
                   ("IV glucose and a glucose control", "recognises the failed line",
                    "places another line (or glucagon, knowing it mobilises little)", "thiamine as a second aim"),
                   also_outside=_HYPO_OUTSIDE),
        "C1": _no("clear", "The failed line and the thiamine are a second step of the same problem, not a critical "
                           "resuscitation."),
        "C3": _no("clear", "Airway and breathing preserved."),
    },
    "opioid_35m": {
        "TD1": _yes("TD1", "clear",
                    "RR 6, SpO2 80 %, PaCO2 69 and obtunded; if nobody ventilates, the engine produces a respiratory "
                    "arrest at 20 min.",
                    "Recognising the ventilatory depression and supporting ventilation first.",
                    ("names the hypoventilation, not only the SpO2", "ventilates or reverses",
                     "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Bag-mask, oxygen and naloxone can be executed; the engine separates ventilating from reversing.",
                   "Prioritising ventilation and naloxone, and assessing the response.",
                   ("bag-mask", "naloxone with dose and route, titrated to the respiratory rate",
                    "reassesses respiratory rate and SpO2")),
        "C1": _yes("C1", "clear",
                   "Hypercapnic respiratory failure: a third of the tablet is still absorbed and naloxone lasts about "
                   "27 min, so re-sedation forces reassessment and revision.",
                   "Integrating ventilation, titration and recurrence, and deciding the observation.",
                   ("titrates naloxone to ventilation, not to consciousness", "reassesses when the effect wears off",
                    "repeats it or starts an infusion", "decides the observation")),
        "C3": _yes("C3", "clear",
                   "Bag-mask ventilation while reversing is the central decision (a critical event); intubation can "
                   "be executed if it does not reverse.",
                   "Deciding ventilatory support and reassessing ventilation.",
                   ("orders assisted ventilation before or with naloxone", "reassesses respiratory rate, SpO2 or gases",
                    "justifies not intubating if it reverses")),
    },
    "opioid_67f": {
        "TD1": _yes("TD1", "clear",
                    "RR 8, SpO2 84 %, PaCO2 61 and obtunded.",
                    "Recognising the ventilatory depression and supporting ventilation first.",
                    ("names the hypoventilation", "ventilates or reverses", "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Bag-mask, oxygen and naloxone can be executed; the engine separates ventilating from reversing.",
                   "Prioritising ventilation and naloxone, and assessing the response.",
                   ("bag-mask", "naloxone titrated to the respiratory rate", "reassesses respiratory rate and SpO2")),
        "C1": _yes("C1", "clear",
                   "The long-acting opioid outlasts naloxone: boluses are not enough and the engine makes the infusion "
                   "the treatment (D1: 'the first correction will not be the last').",
                   "Integrating the recurrence into the plan: infusion and observation.",
                   ("recognises the re-sedation", "starts an infusion with its dose", "reassesses",
                    "does not discharge on the first response")),
        "C3": _yes("C3", "clear",
                   "Ventilating while reversing is the central decision (a critical event); intubation can be executed.",
                   "Deciding ventilatory support and reassessing ventilation.",
                   ("assisted ventilation before or with naloxone", "reassesses respiratory rate, SpO2 or gases")),
    },
    "pneumonia_46f": {
        "TD1": _yes("TD1", "clear",
                    "Septic shock with hypoxaemia (SBP 92, capillary refill 4 s, lactate 3.8, SpO2 89 %).",
                    "Recognising hypoxaemia and hypoperfusion and treating before the imaging.",
                    ("names both threats", "starts oxygen and volume", "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Antibiotic, oxygen and volume are declared; the engine answers each.",
                   "Prioritising oxygen, volume and antibiotic, and assessing the response.",
                   ("oxygen", "a volume bolus", "antibiotic with its dose", "reassesses SpO2, pressure and perfusion")),
        "C1": _yes("C1", "clear",
                   "Severe sepsis: lung and circulation worsen until the antibiotic acts (60 min); volume, "
                   "vasopressor and reassessment.",
                   "Integrating volume, vasopressor, oxygen and antibiotic, and revising by the response.",
                   ("relates the response to volume with the decision on a vasopressor",
                    "reassesses lactate or perfusion", "defines the level of care")),
        "C3": _yes("C3", "TDFC-6",
                   "Hypoxaemic failure whose need changes by design: lung and circulation worsen until the antibiotic "
                   "acts (work of breathing 'Markedly increased' between minutes 60 and 80), so the oxygen has to be "
                   "retitrated or escalated (TDFC-6).",
                   "Choosing the oxygen device, flow and target in a hypoxaemic failure that worsens until the "
                   "antibiotic acts; reassessing and deciding whether to escalate to high flow or NIV.",
                   ("oxygen with device, flow and target", "reassesses SpO2 and effort",
                    "escalates or justifies not escalating"),
                   also_outside=_TDFC6_OUTSIDE),
    },
    "pneumonia_83m": {
        "TD1": _yes("TD1", "clear",
                    "Hypoperfusion (96/60, capillary refill 4 s, lactate 3.1), new drowsiness and SpO2 91 %; D1 asks "
                    "for not attributing it to age.",
                    "Recognising the impaired consciousness and the hypoperfusion as a threat and starting support.",
                    ("names the altered state as something to explain", "starts volume and oxygen",
                     "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Antibiotic, oxygen and volume are declared; the engine answers each.",
                   "Prioritising volume, oxygen and antibiotic, and assessing the response.",
                   ("a volume bolus", "oxygen", "antibiotic",
                    "reassesses pressure, perfusion, SpO2 and consciousness")),
        "C1": _yes("C1", "clear",
                   "Sepsis with encephalopathy: resuscitating and investigating the impaired consciousness in "
                   "parallel (a critical event).",
                   "Integrating resuscitation with the work-up of the altered state, and revising the working model.",
                   ("asks for a glucose or a neurological examination",
                    "relates the response to volume with consciousness", "adjusts and defines the destination")),
        "C3": _yes("C3", "TDFC-6",
                   "As in pneumonia_46f, the need changes by design until the antibiotic acts (TDFC-6). The weakest "
                   "of the three YES: SpO2 92-94 % with 3 L/min.",
                   "Choosing the oxygen device, flow and target in a hypoxaemic failure that worsens until the "
                   "antibiotic acts; reassessing and deciding whether to escalate.",
                   ("oxygen to a target", "reassesses SpO2, effort and consciousness",
                    "escalates or justifies not escalating"),
                   also_outside=_TDFC6_OUTSIDE),
    },
    "pulmonary_edema_58m": {
        "TD1": _yes("TD1", "clear",
                    "Respiratory failure (SpO2 81 %, RR 38, respiratory acidosis) with SBP 218.",
                    "Recognising respiratory failure of cardiac cause and supporting breathing first.",
                    ("names the failure and its cause", "starts support before completing the work-up",
                     "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "NIV, nitrate and diuretic are definitive actions; loading volume is a critical event.",
                   "Prioritising NIV and nitrate, and assessing the response.",
                   ("NIV with EPAP and FiO2", "nitrate with its dose", "reassesses SpO2, respiratory rate and pressure")),
        "C1": _yes("C1", "clear",
                   "Respiratory failure with a hypertensive emergency: NIV and nitrate while watching the pressure, and "
                   "deciding to continue, escalate or reduce.",
                   "Integrating support and offloading, and revising by the response.",
                   ("adjusts EPAP or nitrate to the response", "watches the pressure with the nitrate",
                    "decides to continue, escalate or reduce")),
        "C3": _yes("C3", "clear",
                   "NIV is a definitive action and the engine models it in detail (EPAP, recruitment, effect on "
                   "pressure); it has its own critical event (edema_no_ventilatory_support).",
                   "Deciding and titrating NIV, and reassessing.",
                   ("NIV with mode, EPAP and FiO2", "reassesses SpO2, respiratory rate and pressure",
                    "adjusts or escalates")),
    },
    "pulmonary_edema_75f": {
        "TD1": _yes("TD1", "clear",
                    "SpO2 84 %, RR 32 and marked effort.",
                    "Recognising respiratory failure of cardiac cause and supporting breathing first.",
                    ("names the failure and its cause", "starts support", "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "NIV, diuretic and nitrate are declared; loading volume is a critical event.",
                   "Prioritising NIV and offloading, and assessing the response.",
                   ("NIV with EPAP and FiO2", "nitrate or diuretic with its dose",
                    "reassesses SpO2, respiratory rate and pressure")),
        "C1": _yes("C1", "clear",
                   "Respiratory failure in a patient whose pressure and kidney function limit the nitrate and the "
                   "diuretic.",
                   "Integrating support, offloading and the limits the pressure and the kidney set.",
                   ("adjusts nitrate or diuretic to the pressure and the kidney function", "reassesses",
                    "defines the destination")),
        "C3": _yes("C3", "clear",
                   "NIV is a definitive action and is modelled in detail; it has its own critical event "
                   "(edema_no_ventilatory_support).",
                   "Deciding and titrating NIV, and reassessing.",
                   ("NIV with mode, EPAP and FiO2", "reassesses SpO2, respiratory rate and pressure")),
    },
    "pulmonary_embolism_33f": {
        "TD1": _yes("TD1", "clear",
                    "Tachycardia 124, SpO2 90 % and RR 30 in a patient who offers anxiety as the explanation; D1 asks "
                    "for recognising the threat against that anchor.",
                    "Recognising hypoxaemia and tachycardia as a threat and starting support.",
                    ("names hypoxaemia and tachycardia as a threat", "orders oxygen and monitoring",
                     "does not accept anxiety without evidence")),
        "F1": _yes("F1", "clear",
                   "Oxygen is a definitive action and D3 expects the oxygenation addressed; F1 includes the initial "
                   "oxygenation plan.",
                   "Prioritising oxygenation and monitoring, and assessing the response.",
                   ("oxygen to a target", "reassesses SpO2, heart rate and pressure")),
        "C1": _no("TDFC-3", _TDFC3 + " In this case: stable for 80 min with oxygen and heparin; the decisions are to "
                                     "anticoagulate and not to thrombolyse (a critical event)."),
        "C3": _no("TDFC-6", "Oxygen corrects the hypoxaemia, which does not evolve (SpO2 93 % with 3 L/min, "
                            "stable). " + _TDFC6_NO),
    },
    "pulmonary_embolism_61m": {
        "TD1": _yes("TD1", "clear",
                    "Obstructive shock (86/54, capillary refill 5 s, lactate 4.8) with SpO2 88 %.",
                    "Recognising obstructive shock and acting before the CT angiography.",
                    ("names the shock and its obstructive cause", "starts support", "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Oxygen is declared; the engine punishes rapid volume (the dilated right ventricle lowers the "
                   "output) and tolerates slow, bounded volume.",
                   "Prioritising oxygenation and pressure support that does not overload the right ventricle.",
                   ("oxygen", "slow, bounded volume or a vasopressor", "reassesses pressure and perfusion")),
        "C1": _yes("C1", "clear",
                   "Obstructive shock: deciding reperfusion without waiting for the CT angiography (20 min), limiting "
                   "volume, anticoagulating and deciding the transfer by the pressure.",
                   "Integrating reperfusion, support and transfer, and revising by the pressure.",
                   ("recognises obstructive shock attributable to the PE, or sustained hypotension (SBP < 90 mmHg for 15 "
                    "consecutive minutes)", "decides thrombolysis or the reperfusion team",
                    "adjusts the support and defines the transfer")),
        "C3": _yes("C3", "TDFC-6",
                   "An obstructive shock with marked effort: avoiding, deferring or preparing intubation is a real "
                   "decision about a physiologically difficult airway, and the engine charges positive pressure "
                   "while the obstruction lasts (TDFC-6).",
                   "Titrating oxygen in an obstructive shock and deciding to avoid, defer or prepare intubation, "
                   "naming the haemodynamic risk.",
                   ("high-flow oxygen", "reassesses",
                    "if intubation is considered, names the haemodynamic risk and prepares for it"),
                   also_outside=_TDFC6_OUTSIDE),
    },
    "renal_colic_34m": {
        "TD1": _no("clear", "Preserved perfusion and afebrile; by design the engine invents no deterioration. Severe "
                            "pain is not instability."),
        "F1": _no("clear", "Nothing to resuscitate: the intervention is the analgesia."),
        "C1": _no("clear", "No critical condition."),
        "C3": _no("clear", "SpO2 98 %."),
    },
    "obstructive_pyelonephritis_58f": {
        "TD1": _yes("TD1", "clear",
                    "Sepsis with hypoperfusion (94/54, capillary refill 4 s, lactate 4.2) and slowness.",
                    "Recognising the sepsis and its urinary source and acting on the circulation first.",
                    ("names the sepsis and the source", "starts volume and antibiotic", "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Volume, cultures and antibiotic are the declared initial actions (D1, D3).",
                   "Prioritising volume, cultures and antibiotic, and assessing the response.",
                   ("a volume bolus", "cultures and antibiotic", "reassesses pressure, perfusion and lactate")),
        "C1": _yes("C1", "clear",
                   "Sepsis with an obstructed source: the antibiotic slows the course but does not reverse it without "
                   "decompression; volume, vasopressor and urology (a critical event).",
                   "Integrating resuscitation, source control and continuity.",
                   ("recognises that the antibiotic is not enough", "a vasopressor if volume falls short",
                    "asks for urology or decompression and defines the destination")),
        "C3": _no("clear", "SpO2 95 % and RR 24, no respiratory effort."),
    },
    "trauma_limb_hemorrhage_27m": {
        "TD1": _yes("TD1", "clear",
                    "Haemorrhagic shock with visible external bleeding.",
                    "Recognising exsanguinating haemorrhage and controlling it first.",
                    ("controls the haemorrhage within 10 min", "names the shock", "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Haemorrhage control before everything (the x of xABCDE), blood and tranexamic acid.",
                   "Prioritising control and replacement with blood, and assessing the response.",
                   ("tourniquet or pressure, with the site", "blood before crystalloid",
                    "reassesses pressure and perfusion")),
        "C1": _no("TDFC-4", _TDFC4),
        "C3": _no("clear", "SpO2 97 % and an intact airway. The engine charges intubating before controlling the "
                           "haemorrhage, but that is trauma sequence, not airway management."),
    },
    "trauma_hemothorax_41m": {
        "TD1": _yes("TD1", "clear",
                    "Shock (88/50) with respiratory distress (SpO2 91 %, RR 28) and left-sided dullness.",
                    "Recognising the haemothorax with shock and acting.",
                    ("names the threat", "drains and resuscitates at once", "sets the reassessment")),
        "F1": _yes("F1", "clear",
                   "Drainage and resuscitation at once (D1), blood and tranexamic acid.",
                   "Prioritising the chest tube and blood, and assessing the response.",
                   ("a chest tube on the correct side", "blood",
                    "reassesses pressure and perfusion after the drainage")),
        "C1": _no("TDFC-4", _TDFC4),
        "C3": _no("clear", "The chest tube, a procedure, resolves the hypoxaemia (SpO2 91 %); neither the case nor its "
                           "declaration makes oxygen or ventilation a decision."),
    },
}


# --- DC9 (faculty, 2026-09-29): the nine hypoglycaemia compositions ------------------------------
# Each composition awaiting review gets its origin's TD1, F1, C1 and C3 rows as a traceable initial
# PROPOSAL, pending the faculty's review. A proposal is not a declaration: it never enters a case's
# ``objectives``, so an encounter of a composition keeps the transition (DF-12) it has today, and
# DECLARATIONS -- the approved reference -- is not touched. A composition whose proposal is pending is
# not exposed to residents: it opens only in the faculty sandbox, for review (curriculum_runtime).
COMPOSITION_PROPOSAL_STATUS = "PENDING FACULTY REVIEW (DC9)"
COMPOSITION_PROPOSAL_BASIS = ("Faculty instruction of 2026-09-29 (post-V3, DC9): the origin case's declarations are the "
                              "initial proposal for each composition, marked pending until reviewed; compositions with "
                              "unreviewed declarations are not exposed.")


def composition_proposals():
    """{composition id: {objective: the origin's row, marked as a pending proposal}}."""
    from copy import deepcopy
    import hypoglycemia_catalog
    proposals = {}
    for configuration in hypoglycemia_catalog.review_candidates():
        origin = configuration["derived_from"]
        proposals[configuration["id"]] = {
            objective: {**deepcopy(row), "status": COMPOSITION_PROPOSAL_STATUS, "reviewed": None,
                        "proposal": {"proposed_from": origin, "origin_review": deepcopy(row["reviewed"]),
                                     "basis": COMPOSITION_PROPOSAL_BASIS}}
            for objective, row in DECLARATIONS[origin].items()}
    return proposals


def composition_exposable(case_id):
    """Whether a composition may be offered to residents: never while a proposal of it is pending."""
    rows = composition_proposals().get(case_id)
    return rows is None or all(row.get("status") != COMPOSITION_PROPOSAL_STATUS for row in rows.values())
