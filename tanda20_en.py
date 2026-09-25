"""The twenty scripts of tanda20.py, with everything the resident types in English.

Requested on 2026-09-25 ("si puedes correlos con las indicaciones en inglés
también"). The steps, their order, the examination areas and the follow-up
questions answered are the Spanish scripts' own; only what the resident writes
is English -- orders, questions, answers, reflection and plan -- written the
way an English-speaking resident writes them, with the usual abbreviations
(IV, PO, IM, SC, neb, NS, NRB). The drugs and doses are the same, so the two
languages can be compared decision by decision: the same inputs should make
the same encounter, and where they do not, the reader is what has to explain
why. Like the Spanish scripts, these are rehearsed offline through the real
page (``tools_tanda20.py --rehearse all --language en``); they are not a batch
and not a person's performance.
"""
from copy import deepcopy

import tanda20

COMPARISON = {"alignment": "I matched the initial priority.",
              "adjustment": "I would state earlier the threshold for changing the plan."}

_EN = {
    1: {
        "steps": [
            ("examine", "Breathing"),
            ("order", "I think this is a severe asthma exacerbation, because she speaks in short phrases, "
                      "RR 34 and SpO2 90%. My priority is bronchodilation and oxygen now. Give albuterol 5 mg "
                      "nebulized + ipratropium 0.5 mg neb; O2 by face mask at 6 L/min. I expect the work of "
                      "breathing to ease and the saturation to rise above 94%. Reassess in 15 min RR and "
                      "saturation."),
            ("order", "Better: RR 23 and less effort. My priority is to sustain the bronchodilation and shorten "
                      "the attack. Repeat albuterol 5 mg neb; give hydrocortisone 200 mg IV; order a VBG. I "
                      "expect the RR to keep falling. Reassess in 20 minutes RR and saturation."),
            ("examine", "Breathing"),
            ("order", "Still better: RR 20, mild effort and SpO2 99%. My priority is to complete the first hour "
                      "of bronchodilation. Repeat albuterol 5 mg neb. I expect the effort to settle. Reassess "
                      "in 20 minutes RR and work of breathing."),
            ("examine", "Breathing"),
            ("order", "Good but incomplete response: RR 20, mild effort and SpO2 99%. My priority is a "
                      "destination with monitoring. Admit her to the ward to continue albuterol every 4 hours "
                      "and steroids. I expect the effort to keep settling. Reassess in 30 minutes RR and work "
                      "of breathing."),
            ("order", "On reassessment she relapses: RR 27 with moderate effort as the albuterol wears off. My "
                      "priority is not to leave her without bronchodilation while she goes up to the ward. "
                      "Start continuous albuterol nebulization 10 mg/h. I expect the RR to come back below "
                      "22. Reassess in 15 minutes RR and work of breathing."),
        ],
        "reflection": {
            "working_model_update": "The severity was in her effort and her speech, not only in the saturation.",
            "priority_trigger": "A silent chest or drowsiness would have made me escalate to ventilatory support.",
            "alternative_action": "I could have started continuous nebulization earlier instead of separate doses.",
            "expected_response_reassessment": "I expected less effort; I reassessed RR and work of breathing, and "
                                              "when she relapsed as the albuterol wore off I switched to "
                                              "continuous nebulization.",
        },
        "plan": {"cue": "Broken speech", "threshold": "SpO2 < 92% after the second neb",
                 "next_priority": "Escalate to ventilatory support if there is no response",
                 "alternative_action": "Continuous nebulization", "expected_effect": "Less effort within 15 min",
                 "reassessment_plan": "RR, saturation and speech every 15 min"},
    },
    2: {
        "steps": [
            ("order", "Check a fingerstick glucose"),
            ("order", "I think this is symptomatic hypoglycemia, because he is drowsy and confused with a low "
                      "glucose. My priority is to correct it now. Place a peripheral IV; give dextrose 25 g IV. "
                      "I expect him to wake up and the glucose to rise. Reassess in 10 minutes mental status "
                      "and glucose."),
            ("ask", "Do you use insulin or any medication for your sugar? Have you eaten today?"),
            ("order", "Check a fingerstick glucose"),
            ("order", "He woke up and the glucose is normal. My priority is to keep it from falling again. Give "
                      "him an oral snack and keep him under observation for 2 hours with serial fingerstick "
                      "glucose. I expect a glucose above 100. Reassess in 30 minutes fingerstick glucose and "
                      "mental status."),
        ],
        "reflection": {
            "working_model_update": "The confusion was hypoglycemia until proven otherwise.",
            "priority_trigger": "A new drop in glucose would have made me start a dextrose infusion.",
            "alternative_action": "Glucagon if I had not had IV access.",
            "expected_response_reassessment": "I expected recovery within minutes; I measured glucose and "
                                              "mental status.",
        },
        "plan": {"cue": "Fingerstick glucose", "threshold": "< 70 mg/dL", "next_priority": "Identify the cause",
                 "alternative_action": "10% dextrose infusion", "expected_effect": "Stable glucose",
                 "reassessment_plan": "Glucose every 30 min for 2 hours"},
    },
    3: {
        "steps": [
            ("order", "Get a 12-lead ECG"),
            ("order", "I think this is an inferior STEMI with possible RV involvement, because there is inferior "
                      "ST elevation, HR 58 and BP 100/64. My priority is reperfusion without dropping the "
                      "preload. Give aspirin 300 mg PO and clopidogrel 600 mg PO; get a right-sided ECG. I "
                      "expect to document the RV involvement without the pressure falling. Reassess in 10 "
                      "minutes BP and HR."),
            ("ask", "Do you have any allergies or recent bleeding? Do you take blood thinners?"),
            ("order", "Consult the cath lab for primary PCI because this is a STEMI. I expect them to accept "
                      "within 90 minutes. Reassess in 10 minutes pain, BP and HR."),
            ("order", "Still stable, SBP above 95. My priority is to reach the cath lab monitored. Transfer him "
                      "to the cath lab on a monitor. I expect the pressure not to drop during the transfer. "
                      "Reassess in 15 minutes BP and rhythm."),
        ],
        "reflection": {
            "working_model_update": "The 'dyspeptic' pain with bradycardia was an inferior MI.",
            "priority_trigger": "A drop in pressure would have made me give volume and avoid nitrates.",
            "alternative_action": "Heparin in the same order set if the cath lab was delayed.",
            "expected_response_reassessment": "I watched BP and HR while the cath lab was activated.",
        },
        "plan": {"cue": "Inferior ST elevation", "threshold": "SBP < 90", "next_priority": "Reperfusion",
                 "alternative_action": "Thrombolysis if there is no cath lab", "expected_effect": "No hypotension",
                 "reassessment_plan": "BP and HR every 5-10 min"},
    },
    4: {
        "steps": [
            ("ask", "Have you had black stools or vomited blood? Do you take any medication?"),
            ("order", "I think this is an upper GI bleed with hypoperfusion, because he has melena, BP 88/54, "
                      "HR 124 and a capillary refill of 5 s. My priority is to replace volume and get blood. "
                      "Place 2 large-bore IVs; give NS 500 mL IV bolus; order hemoglobin, basic labs and "
                      "lactate. I expect the BP to rise and the perfusion to improve. Reassess in 10 min BP, "
                      "HR and capillary refill."),
            ("order", "Still hypotensive. My priority is oxygen delivery. Transfuse 2 units of packed red cells; "
                      "give omeprazole 80 mg IV. I expect an SBP above 90 and HR below 110. Reassess in 15 "
                      "minutes BP, HR and capillary refill."),
            ("order", "Consult gastroenterology for an urgent endoscopy"),
            ("complete", {"What do you expect": "That they do the endoscopy in the next few hours and control "
                                                "the bleeding.",
                          "What will you check": "BP, HR and any new melena or hematemesis",
                          "delay": 30}),
            ("examine", "Peripheral perfusion"),
            ("order", "Better perfused, SBP above 95. My priority is hemostasis in a monitored setting. Admit "
                      "him to intermediate care. I expect no rebleeding before the endoscopy. Reassess in 30 "
                      "minutes BP, HR and hemoglobin."),
        ],
        "reflection": {
            "working_model_update": "The first hemoglobin did not show the real loss.",
            "priority_trigger": "A new drop in BP would have made me activate massive transfusion.",
            "alternative_action": "Transfuse before the crystalloid.",
            "expected_response_reassessment": "I measured BP, HR and capillary refill after each intervention.",
        },
        "plan": {"cue": "Capillary refill", "threshold": "SBP < 90 after 2 units", "next_priority": "Endoscopy",
                 "alternative_action": "Massive transfusion", "expected_effect": "Perfusion restored",
                 "reassessment_plan": "BP/HR every 15 min"},
    },
    5: {
        "steps": [
            ("ask", "How long have you had the cough and fever? Are you bringing up sputum?"),
            ("ask", "Any allergies to antibiotics? Any previous illnesses?"),
            ("examine", "Breathing"),
            ("examine", "Peripheral perfusion"),
            ("order", "Order a chest x-ray, blood cultures, lactate and basic labs"),
            ("order", "Reassess in 15 minutes"),
            ("order", "I think this is pneumonia with sepsis and hypoperfusion, because she has a fever of 39.1, "
                      "RR 30, SpO2 89% and a capillary refill of 4 s. My priority is antibiotics and oxygen. "
                      "Give ceftriaxone 2 g IV and azithromycin 500 mg IV; O2 by nasal cannula 4 L/min; NS "
                      "1000 mL IV. I expect the perfusion to improve and the saturation to rise. Reassess in "
                      "20 minutes perfusion and saturation."),
            ("order", "Perfusion somewhat better, BP 99/62 and refill 3.4 s, but SpO2 92% with RR 32 and more "
                      "effort. My priority is better oxygenation and completing the volume. Put her on a "
                      "non-rebreather mask at 10 L/min; give NS 500 mL IV. I expect a saturation above 94% and "
                      "an SBP above 100. Reassess in 20 minutes saturation, RR and BP."),
            ("order", "SpO2 99% on the non-rebreather, BP 103/64 and refill 3 s, but still RR 32 with marked "
                      "effort. My priority is a monitored destination because of the work of breathing. Admit "
                      "her to intermediate care. I expect the effort to settle with the antibiotics over the "
                      "next hours. Reassess in 30 minutes RR, saturation and BP."),
        ],
        "reflection": {
            "working_model_update": "The hypoperfusion called for antibiotics before completing the workup.",
            "priority_trigger": "A slow capillary refill with fever should have triggered the antibiotics at once.",
            "alternative_action": "Antibiotics and volume in the first order set.",
            "expected_response_reassessment": "I reassessed perfusion and saturation after the treatment, and "
                                              "increased the oxygen and the volume when the response was partial.",
        },
        "plan": {"cue": "Hypoperfusion with fever", "threshold": "Refill > 3 s",
                 "next_priority": "Antibiotics within the first hour",
                 "alternative_action": "Vasopressor if there is no response to volume",
                 "expected_effect": "Better perfusion", "reassessment_plan": "Repeat lactate"},
    },
    6: {
        "steps": [
            ("order", "I think this is opioid-induced respiratory depression, because RR 6 and SpO2 80%. My "
                      "priority is oxygenation. Give O2 by non-rebreather mask at 15 L/min. I expect the "
                      "saturation to rise. Reassess in 5 minutes saturation and RR."),
            ("ask", "What did he take? How long ago? Did he take anything else?"),
            ("order", "Still a low RR. My priority is reversal without withdrawal. Give naloxone 0.04 mg IV. I "
                      "expect the RR to rise. Reassess in 3 minutes."),
            ("answer", "I will count the respiratory rate and look at the saturation."),
            ("order", "Give naloxone 0.1 mg IV, reassess in 3 minutes RR"),
            ("complete", {"What do you expect": "The RR to rise without him waking up agitated"}),
            ("order", "Give naloxone 0.4 mg IV. I expect an RR above 12. Reassess in 5 minutes RR and level of "
                      "consciousness."),
            ("examine", "General appearance"),
            ("order", "Breathing well and awake. My priority is to watch for renarcotization. Admit him to "
                      "intermediate care with monitoring. I expect him not to become depressed again. Reassess "
                      "in 30 minutes RR and level of consciousness."),
        ],
        "reflection": {
            "working_model_update": "It was an opioid overdose of uncertain duration.",
            "priority_trigger": "An RR below 10 would have made me ventilate with a bag.",
            "alternative_action": "Bag-mask ventilation before titrating.",
            "expected_response_reassessment": "I counted the RR after each dose.",
        },
        "plan": {"cue": "RR", "threshold": "< 10/min", "next_priority": "Ventilation before the antagonist",
                 "alternative_action": "Naloxone infusion", "expected_effect": "RR > 12",
                 "reassessment_plan": "RR and consciousness every 15 min"},
    },
    7: {
        "steps": [
            ("ask", "How did the pain start? Do you have a fever or pain when you pass urine?"),
            ("order", "Order a renal ultrasound"),
            ("order", "I think this is right renal colic, because the pain comes in waves and he cannot keep "
                      "still. My priority is analgesia. Give ketorolac 30 mg IV. I expect the pain to drop below "
                      "4/10. Reassess in 20 minutes pain."),
            ("order", "Order a urinalysis and a temperature"),
            ("order", "Reassess in 20 minutes"),
            ("order", "Still in severe pain despite the ketorolac. My priority is analgesia. Give morphine 4 mg "
                      "IV. I expect the pain to drop below 4/10. Reassess in 20 minutes pain."),
            ("order", "Down to moderate pain, not yet controlled. Repeat morphine 4 mg IV. I expect mild pain. "
                      "Reassess in 20 minutes pain."),
            ("order", "Mild pain with the second dose. My priority is that he tolerates oral intake before he "
                      "leaves, and morphine can cause nausea and vomiting. Give ondansetron 4 mg IV. I expect "
                      "him to keep fluids down without vomiting. Reassess in 30 minutes pain and oral "
                      "tolerance."),
            ("order", "Back to moderate pain. My priority is baseline analgesia before discharge. Give "
                      "metamizole 1 g IV. I expect sustained mild pain. Reassess in 20 minutes pain."),
            ("order", "Mild pain, afebrile and the urinalysis shows no infection. My priority is a safe "
                      "discharge. Discharge him with analgesia, urology follow-up and return precautions for "
                      "fever, vomiting or uncontrolled pain. I expect him to pass the stone. Reassess in 15 "
                      "minutes the pain before he leaves."),
        ],
        "reflection": {
            "working_model_update": "Colic without fever or infection allowed a discharge.",
            "priority_trigger": "Fever or a urinary infection would have made me admit him.",
            "alternative_action": "Analgesia before the imaging.",
            "expected_response_reassessment": "I reassessed the pain after each analgesic, added morphine when the "
                                              "NSAID was not enough and excluded infection before the discharge.",
        },
        "plan": {"cue": "Fever", "threshold": "T > 38", "next_priority": "Exclude an obstructive infection",
                 "alternative_action": "Opioid if the NSAID fails", "expected_effect": "Pain < 4/10",
                 "reassessment_plan": "Pain every 20 min"},
    },
    8: {
        "steps": [
            ("order", "I think this is acute pulmonary edema, because BP 218/116, RR 38 and SpO2 81%. My "
                      "priority is oxygenation. Give O2 by non-rebreather mask at 15 L/min. I expect the "
                      "saturation to rise. Reassess in 10 minutes."),
            ("complete", {"What will you check": "Saturation, RR and work of breathing"}),
            ("order", "Order a chest x-ray and POCUS"),
            ("order", "Still SpO2 88%, RR 39 and severe effort. My priority is ventilatory support and lowering "
                      "the afterload. Start NIV CPAP 8 with FiO2 60%; nitroglycerin 50 mcg/min IV. I expect the "
                      "RR to fall and the saturation to rise. Reassess in 10 minutes RR, saturation and BP."),
            ("order", "Give furosemide 40 mg IV"),
            ("answer", "I expect more urine output and less congestion. Reassess in 20 minutes urine output and "
                       "saturation."),
            ("examine", "Breathing"),
            ("order", "Better: SpO2 99% on CPAP and RR 21 without effort, but the BP is still 177/98. My "
                      "priority is to keep lowering the afterload in a monitored setting. Increase the "
                      "nitroglycerin to 100 mcg/min and admit him to the CCU. I expect a BP below 160 and the "
                      "congestion to keep improving. Reassess in 30 minutes saturation and BP."),
        ],
        "reflection": {
            "working_model_update": "It was afterload-driven edema; oxygen alone was not enough.",
            "priority_trigger": "A saturation that did not rise should have taken me to NIV earlier.",
            "alternative_action": "NIV and nitroglycerin from the first order set.",
            "expected_response_reassessment": "I followed RR, saturation and BP.",
        },
        "plan": {"cue": "SpO2 below 90 on oxygen", "threshold": "No response in 10 min", "next_priority": "NIV",
                 "alternative_action": "Intubation if it fails", "expected_effect": "Less effort",
                 "reassessment_plan": "RR and SpO2 every 10 min"},
    },
    9: {
        "steps": [
            ("ask", "What was the pain like? How long did each episode last?"),
            ("order", "Get an ECG and a troponin"),
            ("order", "I think this may be atypical pain without active ischemia, because he is pain-free now. "
                      "My priority is to observe without treating yet. Order a repeat troponin. I expect it to "
                      "be negative. Reassess in 30 minutes pain."),
            ("order", "Reviewing the ECG there are deep T-wave inversions in V2-V3: this is a Wellens pattern. "
                      "My priority is to treat it as an acute coronary syndrome and NOT to provoke exertion. Give "
                      "aspirin 300 mg PO; heparin 5000 units IV. I expect the pain not to come back. Reassess in "
                      "15 minutes pain and ECG."),
            ("order", "Consult cardiology for early coronary angiography"),
            ("answer", "I expect them to do it today. I will watch the pain and the ECG every 15 minutes."),
            ("order", "Pain-free and stable. My priority is angiography without delay. Admit him to the CCU. I "
                      "expect the artery not to occlude before then. Reassess in 30 minutes pain and ECG."),
        ],
        "reflection": {
            "working_model_update": "The Wellens ECG turns a pain that settled into a critical stenosis.",
            "priority_trigger": "The deep T-wave inversions should have changed the plan before I thought of a "
                                "stress test.",
            "alternative_action": "Read the ECG before deciding on the workup.",
            "expected_response_reassessment": "I watched the pain and serial ECGs.",
        },
        "plan": {"cue": "T-wave inversions in V2-V3", "threshold": "Any new pain",
                 "next_priority": "Coronary angiography", "alternative_action": "Full anticoagulation",
                 "expected_effect": "No recurrence", "reassessment_plan": "Serial ECG and troponin"},
    },
    10: {
        "steps": [
            ("order", "Check a fingerstick glucose"),
            ("order", "I think this is hypoglycemia, because she is obtunded with a low glucose. My priority is "
                      "to correct it. Place a PIV; give dextrose 25 g IV. I expect her to wake up. Reassess in "
                      "10 minutes mental status and glucose."),
            ("order", "Check a fingerstick glucose"),
            ("order", "She woke up with a glucose of 131. I think it was hypoglycemia from eating little. My "
                      "priority is a safe discharge. Give her an oral snack and discharge her if she tolerates "
                      "it. I expect it not to drop again. Reassess in 30 minutes fingerstick glucose."),
            ("ask", "What medications do you take for your diabetes?"),
            ("order", "She takes glimepiride: it can fall again for hours, so she cannot go home. My priority is "
                      "to prevent a recurrence. Start a dextrose 10% infusion at 100 mL/h and admit her to the "
                      "ward for observation with hourly glucose checks. I expect a glucose above 100. Reassess "
                      "in 30 minutes fingerstick glucose."),
        ],
        "reflection": {
            "working_model_update": "It was not only poor intake: the sulfonylurea explains the recurrence.",
            "priority_trigger": "Knowing her glucose-lowering drug should have come before any discharge plan.",
            "alternative_action": "Octreotide if it recurs despite the glucose.",
            "expected_response_reassessment": "Hourly glucose under observation.",
        },
        "plan": {"cue": "Glucose-lowering medication", "threshold": "Sulfonylurea",
                 "next_priority": "Prolonged observation", "alternative_action": "Octreotide",
                 "expected_effect": "No recurrence", "reassessment_plan": "Glucose every hour"},
    },
    11: {
        "steps": [
            ("order", "I think this is an asthma exacerbation, because he is wheezing. My priority is "
                      "bronchodilation. Give albuterol 5 mg neb + ipratropium 0.5 mg neb. I expect the "
                      "obstruction to ease. Reassess in 20 minutes."),
            ("answer", "I will look at the saturation and the wheeze."),
            ("order", "Order an ABG"),
            ("order", "Reassess in 10 minutes"),
            ("order", "The gas shows a PaCO2 of 45 with RR 23 and marked effort, and he arrived tired with a "
                      "quieter wheeze: a normal PaCO2 in an attack like this is exhaustion, impending "
                      "ventilatory failure. My priority is ventilatory support. Start NIV BiPAP 12/5 with FiO2 "
                      "40%; give hydrocortisone 200 mg IV. I expect the PaCO2 to fall and the effort to settle. "
                      "Reassess in 15 minutes mental status and gases."),
            ("order", "Consult the ICU"),
            ("complete", {"What do you expect": "That they take him for monitored ventilatory support",
                          "What will you check": "Mental status, RR and saturation", "delay": 15}),
            ("order", "Still RR 28 and severe effort despite the NIV. My priority is not to be late to the "
                      "airway. I prepare for intubation and admit him to the ICU. I expect the ICU to intubate "
                      "him if he keeps tiring. Reassess in 15 minutes mental status and RR."),
        ],
        "reflection": {
            "working_model_update": "The tiredness and the quieter chest were exhaustion, not improvement.",
            "priority_trigger": "A tired asthmatic with a quieter wheeze should have triggered a gas and support "
                                "from the start.",
            "alternative_action": "Prepare the intubation in parallel.",
            "expected_response_reassessment": "Repeat gases and mental status.",
        },
        "plan": {"cue": "Drowsiness", "threshold": "Normal or high PaCO2", "next_priority": "Ventilatory support",
                 "alternative_action": "Intubation", "expected_effect": "Less CO2",
                 "reassessment_plan": "Gases in 30 min"},
    },
    12: {
        "steps": [
            ("order", "I think this is an allergic reaction, because she has a rash and facial swelling. My "
                      "priority is to control the allergy. Give chlorphenamine 10 mg IV and hydrocortisone 200 "
                      "mg IV. I expect the rash to settle. Reassess in 10 minutes."),
            ("answer", "I will see whether the rash and the swelling settle."),
            ("examine", "Breathing"),
            ("order", "Still hypotensive with stridor: this is anaphylaxis. My priority is epinephrine. Give "
                      "epinephrine 0.5 mg IM; NS 1000 mL IV bolus; O2 by face mask 10 L/min. I expect the BP to "
                      "rise and the stridor to settle. Reassess in 5 minutes BP and stridor."),
            ("order", "Partial improvement. Give epinephrine 0.5 mg IM. Reassess in 5 minutes BP and stridor."),
            ("answer", "I expect the pressure to finish rising and the stridor to go away."),
            ("order", "Reassess in 15 minutes BP, RR and stridor"),
            ("order", "Stable: BP 135/74, RR 21 with mild effort and no stridor. My priority is to watch for a "
                      "biphasic reaction. Keep her in observation for 6 hours and prescribe an epinephrine "
                      "auto-injector at discharge. I expect no recurrence. Reassess in 30 minutes BP and "
                      "airway."),
        ],
        "reflection": {
            "working_model_update": "Hypotension and stridor after an exposure are anaphylaxis: epinephrine first.",
            "priority_trigger": "The hypotension should have taken me to epinephrine in the first order set.",
            "alternative_action": "IM epinephrine before antihistamines.",
            "expected_response_reassessment": "BP and stridor every 5 min.",
        },
        "plan": {"cue": "Hypotension after an exposure", "threshold": "SBP < 90", "next_priority": "IM epinephrine",
                 "alternative_action": "Epinephrine infusion", "expected_effect": "BP restored",
                 "reassessment_plan": "BP every 5 min"},
    },
    13: {
        "steps": [
            ("order", "I think this is opioid-induced respiratory depression, because RR 8 and SpO2 84%. My "
                      "priority is ventilation. Bag-mask ventilate with 100% O2. I expect a saturation above "
                      "94%. Reassess in 5 minutes saturation and RR."),
            ("order", "My priority is reversal. Give naloxone 0.4 mg IV. I expect an RR above 12. Reassess in 5 "
                      "minutes RR."),
            ("examine", "General appearance"),
            ("order", "She woke up and is breathing well. My priority is to free up the bed. Send her home with "
                      "her husband. I expect it not to happen again. Reassess in 15 minutes."),
            ("answer", "I will check that she stays awake before she leaves."),
        ],
        "reflection": {
            "working_model_update": "I reversed without knowing which opioid it was.",
            "priority_trigger": "An RR falling again would have made me repeat the naloxone.",
            "alternative_action": "Ask about the drug and its formulation before the disposition.",
            "expected_response_reassessment": "I told her to come back if it happened again.",
        },
        "plan": {"cue": "Opioid formulation", "threshold": "Extended release", "next_priority": "Observation",
                 "alternative_action": "Naloxone infusion", "expected_effect": "No renarcotization",
                 "reassessment_plan": "RR every 30 min for hours"},
    },
    14: {
        "steps": [
            ("order", "I think this is hypovolemic shock, because he is hypotensive and tachycardic. My priority "
                      "is volume. Give NS 1000 mL IV bolus. I expect the BP to rise. Reassess in 15 minutes BP."),
            ("order", "Order a CT pulmonary angiogram and a D-dimer"),
            ("order", "Still hypotensive. My priority is more volume. Give NS 1000 mL IV. I expect an SBP above "
                      "90. Reassess in 15 minutes BP and HR."),
            ("order", "Order a POCUS"),
            ("order", "The RV is dilated; I will wait for the CT before deciding. My priority is confirmation. "
                      "Give O2 by nasal cannula 3 L/min. I expect the saturation to rise. Reassess in 20 "
                      "minutes."),
            ("answer", "I will look at the saturation."),
            ("order", "Admit him to the ICU"),
            ("answer", "I expect them to stabilize him there. Reassess the BP in 10 minutes."),
        ],
        "reflection": {
            "working_model_update": "It was not hypovolemia: the dilated RV was obstructive shock.",
            "priority_trigger": "The POCUS should have changed the plan towards anticoagulation and reperfusion.",
            "alternative_action": "Anticoagulate and consider thrombolysis for sustained hypotension.",
            "expected_response_reassessment": "BP after each bolus.",
        },
        "plan": {"cue": "Dilated RV", "threshold": "Sustained hypotension", "next_priority": "Reperfusion",
                 "alternative_action": "Thrombolysis", "expected_effect": "Stable BP",
                 "reassessment_plan": "BP every 10 min"},
    },
    15: {
        "steps": [
            ("ask", "Have you noticed black stools? What medications do you take?"),
            ("order", "I think this is chronic anemia, because she reports days of tiredness. My priority is the "
                      "workup. Order a hemoglobin and basic labs. I expect a low hemoglobin. Reassess in 20 "
                      "minutes."),
            ("order", "Give omeprazole 40 mg IV"),
            ("answer", "I expect to protect the mucosa. I will check the hemoglobin in 30 minutes."),
            ("order", "Consult gastroenterology"),
            ("complete", {"What do you expect": "That they schedule an endoscopy",
                          "What will you check": "A repeat hemoglobin", "delay": 30}),
            ("order", "Admit her to the ward"),
            ("answer", "I expect them to work her up. I will check the hemoglobin tomorrow."),
        ],
        "reflection": {
            "working_model_update": "It was active bleeding with hypoperfusion, not chronic anemia.",
            "priority_trigger": "The slow capillary refill should have made me resuscitate.",
            "alternative_action": "Volume and early transfusion.",
            "expected_response_reassessment": "A repeat hemoglobin.",
        },
        "plan": {"cue": "Capillary refill", "threshold": "> 3 s", "next_priority": "Resuscitation",
                 "alternative_action": "Transfusion", "expected_effect": "Better perfusion",
                 "reassessment_plan": "BP/HR every 15 min"},
    },
    16: {
        "steps": [
            ("order", "I think this is symptomatic bradycardia, because HR 38 and BP 74/44. My priority is to "
                      "raise the rate. Give atropine 1 mg IV. I expect an HR above 50. Reassess in 5 minutes HR "
                      "and BP."),
            ("order", "Give atropine 1 mg IV. Reassess in 5 minutes."),
            ("answer", "I expect the HR to rise. I will look at the HR and BP."),
            ("order", "Order basic labs and an ECG"),
            ("order", "Still HR 35 and BP 71/42. My priority is the pressure. Give NS 500 mL IV. I expect an SBP "
                      "above 90. Reassess in 10 minutes BP and HR."),
            ("order", "Consult cardiology for a pacemaker"),
            ("complete", {"What do you expect": "That they place a pacemaker",
                          "What will you check": "HR and BP", "delay": 10}),
        ],
        "reflection": {
            "working_model_update": "The refractory bradycardia had a toxic cause that I did not look for.",
            "priority_trigger": "The lack of response to atropine should have made me ask about medications.",
            "alternative_action": "Calcium and glucagon; transcutaneous pacing.",
            "expected_response_reassessment": "HR and BP after each intervention.",
        },
        "plan": {"cue": "Atropine without a response", "threshold": "Two doses",
                 "next_priority": "Look for the cause", "alternative_action": "Antidote",
                 "expected_effect": "HR > 50", "reassessment_plan": "HR and BP every 5 min"},
    },
    17: {
        "steps": [
            ("order", "I think he is dehydrated, because the note says he is eating little. My priority is "
                      "hydration. Give NS 1000 mL IV. I expect him to wake up. Reassess in 30 minutes."),
            ("answer", "I will see whether he wakes up."),
            ("order", "Give NS 1000 mL IV. Reassess in 30 minutes."),
            ("answer", "I expect him to rehydrate. I will see whether he wakes up."),
            ("order", "Order basic labs"),
            ("order", "Admit him to the ward for hydration"),
            ("answer", "I expect him to rehydrate on the ward. I will check his hydration tomorrow."),
        ],
        "reflection": {
            "working_model_update": "I followed the note's hypothesis without testing it.",
            "priority_trigger": "The fever and the low saturation should have made me think of an infection.",
            "alternative_action": "Glucose, a chest x-ray and antibiotics.",
            "expected_response_reassessment": "I expected him to wake up with volume.",
        },
        "plan": {"cue": "New drowsiness", "threshold": "Any change in consciousness",
                 "next_priority": "Look for the cause", "alternative_action": "Early antibiotics",
                 "expected_effect": "Better consciousness",
                 "reassessment_plan": "Consciousness and perfusion every 15 min"},
    },
    18: {
        "steps": [
            ("order", "I think this is anxiety, because she is tachycardic and nervous. My priority is to calm "
                      "her down. Give lorazepam 1 mg PO. I expect the HR to come down. Reassess in 30 minutes."),
            ("order", "Order a stress test"),
            ("order", "Get an ECG"),
            ("order", "Discharge her with outpatient follow-up"),
            ("answer", "It is anxiety. I expect her to calm down at home. I will review the symptoms at the "
                       "clinic follow-up in one week."),
        ],
        "reflection": {
            "working_model_update": "I labelled a pressing pain with dyspnea as anxiety.",
            "priority_trigger": "The ECG should have come first.",
            "alternative_action": "An ECG within 10 minutes and aspirin.",
            "expected_response_reassessment": "I expected her to calm down.",
        },
        "plan": {"cue": "Pressing chest pain", "threshold": "Any ECG change", "next_priority": "Early ECG",
                 "alternative_action": "Aspirin", "expected_effect": "Ischemia treated",
                 "reassessment_plan": "Serial ECG and troponin"},
    },
    19: {
        "steps": [
            ("order", "I think this is anaphylaxis from the sting, because he has wheeze, a rash and BP 76/42. My "
                      "priority is epinephrine. Give epinephrine 0.5 mg IM; NS 1000 mL IV; O2 by face mask 10 "
                      "L/min. I expect the BP to rise. Reassess in 5 minutes BP and wheeze."),
            ("order", "Give epinephrine 0.5 mg IM. Reassess in 5 minutes BP."),
            ("answer", "I expect the pressure to rise this time."),
            ("ask", "What medications do you take? Do you take anything for blood pressure or the heart?"),
            ("order", "He takes a beta-blocker, which is why he is not responding. My priority is to get around "
                      "the blockade. Give glucagon 1 mg IV; start an epinephrine infusion at 0.1 mcg/kg/min. I "
                      "expect the BP to rise. Reassess in 10 minutes BP and HR."),
            ("order", "Admit him to the ICU"),
            ("answer", "I expect him to stay stable on the infusion. Reassess in 15 minutes BP."),
        ],
        "reflection": {
            "working_model_update": "The lack of response had a cause: the beta-blocker.",
            "priority_trigger": "Two doses without a response made me look for the cause.",
            "alternative_action": "An epinephrine infusion before the glucagon.",
            "expected_response_reassessment": "BP and HR every 5 min.",
        },
        "plan": {"cue": "Epinephrine without a response", "threshold": "Two doses",
                 "next_priority": "Look for beta-blockade", "alternative_action": "Glucagon",
                 "expected_effect": "BP restored", "reassessment_plan": "BP every 5 min"},
    },
    20: {
        "steps": [
            ("ask", "Have you had recent surgery, travel or pain in one leg?"),
            ("order", "I think this is a pulmonary embolism, because she has sudden dyspnea, pleuritic pain, HR "
                      "124 and SpO2 90%. My priority is to anticoagulate without waiting for the imaging. Give "
                      "enoxaparin 60 mg SC; O2 by nasal cannula 3 L/min; order a CT pulmonary angiogram. I "
                      "expect the saturation to rise and no deterioration. Reassess in 20 minutes saturation "
                      "and HR."),
            ("recover",),
            ("examine", "Peripheral perfusion"),
            ("order", "Order a troponin"),
            ("order", "Reassess in 20 minutes HR and saturation"),
            ("order", "Troponin 31 over 19 and a dilated RV on the CT angiogram, with HR 125, RR 30 and SpO2 93% "
                      "but BP 108/69: intermediate-high risk PE, no shock. My priority is a monitored "
                      "destination. Admit her to intermediate care on anticoagulation. I expect her to stay "
                      "stable. Reassess in 30 minutes saturation and BP."),
        ],
        "reflection": {
            "working_model_update": "With a high clinical probability I anticoagulated before the imaging.",
            "priority_trigger": "Hypotension would have made me consider thrombolysis.",
            "alternative_action": "Wait for the CT angiogram if the suspicion were low.",
            "expected_response_reassessment": "Saturation and BP.",
        },
        "plan": {"cue": "Hypotension", "threshold": "SBP < 90", "next_priority": "Reperfusion if in shock",
                 "alternative_action": "Unfractionated heparin", "expected_effect": "Stable",
                 "reassessment_plan": "SpO2 and BP every 30 min"},
    },
}


def _shape(step):
    """What a step is, apart from its words: its kind, the area examined, the questions answered."""
    kind = step[0]
    if kind == "examine":
        return kind, step[1]
    if kind == "complete":
        return kind, tuple(sorted(step[1]))
    return (kind,)


def english(script):
    """A Spanish script with the resident's words in English, and nothing else changed."""
    words = _EN[script["number"]]
    if [_shape(step) for step in words["steps"]] != [_shape(step) for step in script["steps"]]:
        raise ValueError(f"The English script {script['number']} does not have the Spanish script's steps.")
    for key in ("reflection", "plan"):
        if set(words[key]) != set(script[key]):
            raise ValueError(f"The English script {script['number']} does not answer the same {key} fields.")
    return {**deepcopy(script), "steps": list(words["steps"]), "reflection": dict(words["reflection"]),
            "plan": dict(words["plan"]), "comparison": dict(words.get("comparison", COMPARISON)),
            "language": "en"}


SCRIPTS = [english(script) for script in tanda20.SCRIPTS]
BY_NUMBER = {script["number"]: script for script in SCRIPTS}
