"""CRITICAL_CLINICAL_LANGUAGE_REGRESSIONS: the nine critical classes of DF-22.

The cycle 5 trace audit (docs/AUDITORIA_TRACE_CICLO5.md, C01-C09) found nine
kinds of sentence in which a first-line order was lost, inverted or held: the
encounter did not do what the resident wrote, and the Management Trace showed
the resident not doing it. Cycle 6 corrected them by class (faculty approval of
2026-09-28). This suite keeps each class corrected, cheaply:

- for every class, the audit's example, variants written for this correction
  and near-miss negatives, in English and in Spanish;
- what the reader reads (every order that must run now, none that must not,
  the plan it keeps);
- what the engine executes on the bank case the sentence is written for;
- through the real page, four critical scenarios (anaphylaxis, bradycardia,
  shock, oxygen) read back from the stored Management Trace.

INTERNAL DEVELOPMENT DATA: every sentence was written by the developer for the
correction or taken from the internal audit. None is external validation data,
and passing here says nothing about how often a resident's real sentence is
read correctly (that is what the validation pilot measures).
"""
import pytest

from family_parser import parse_family_actions
from test_curriculum_trajectories import load_engine

# (class, language, family, case, text, must run now, must not run now, plan kinds kept)
# An order that must run is (type, {key: value}); a forbidden one is a type.
POSITIVE = [
    # C01 · "X, if no response, Y": X now, Y is the plan.
    ("C01", "es", "bradycardia", "bradycardia_avb3_78f",
     "Atropina 1 mg ev, si no responde, marcapaso transcutáneo a 70 lpm con 60 mA.",
     [("atropine", {"dose_mg": 1.0, "route": "IV"})], ["transcutaneous_pacing"], ["conditional"]),
    ("C01", "en", "bradycardia", "bradycardia_avb3_78f",
     "Atropine 1 mg IV, if no response, transcutaneous pacing at 70 bpm with 60 mA.",
     [("atropine", {"dose_mg": 1.0, "route": "IV"})], ["transcutaneous_pacing"], ["conditional"]),
    ("C01", "es", "pneumonia", "pneumonia_83m",
     "Noradrenalina 0,1 mcg/kg/min, si persiste hipotenso, agregar vasopresina 0,03 U/min.",
     [("norepinephrine", {"rate": 0.1, "units": "mcg/kg/min"})], [], ["conditional"]),
    ("C01", "en", "pneumonia", "pneumonia_83m",
     "Norepinephrine 0.1 mcg/kg/min, if still hypotensive, add vasopressin 0.03 U/min.",
     [("norepinephrine", {"rate": 0.1, "units": "mcg/kg/min"})], [], ["conditional"]),
    ("C01", "es", "pneumonia", "pneumonia_83m",
     "Oxígeno por naricera a 2 L/min, si satura menos de 90%, mascarilla con reservorio a 15 L/min.",
     [("oxygen", {"device": "nasal cannula", "flow_lpm": 2.0})], [], ["conditional"]),
    ("C01", "en", "anaphylaxis", "anaphylaxis_29f",
     "Epinephrine 0.5 mg IM, if no response, repeat in 5 minutes.",
     [("epinephrine_im", {"dose_mg": 0.5})], [], ["repeat"]),
    ("C01", "es", "asthma", "asthma_24f",
     "Salbutamol 5 mg nbz, si persiste el broncoespasmo, repetir cada 20 minutos.",
     [("bronchodilator", {"agent": "albuterol", "dose_mg": 5.0})], [], ["repeat"]),
    # C02 · "Diagnosis or findings: order": the order runs.
    ("C02", "en", "anaphylaxis", "anaphylaxis_29f",
     "Anaphylaxis with stridor and facial swelling: epinephrine 0.5 mg IM in the thigh now, "
     "repeat in 5 minutes if no response.",
     [("epinephrine_im", {"dose_mg": 0.5, "route": "IM"})], [], ["repeat"]),
    ("C02", "en", "trauma", "trauma_hemothorax_41m",
     "Decreased breath sounds on the left with hypotension, I think it's a massive hemothorax: "
     "left chest tube now and reassess vitals in 5 minutes.",
     [("chest_decompression", {"side": "left", "device": "chest tube"}), ("reassessment", {"delay_min": 5.0})],
     [], []),
    ("C02", "en", "opioid", "opioid_35m",
     "RR 6 and pinpoint pupils, opioid toxidrome: bag-mask ventilate and give naloxone 2 mg intranasal.",
     [("bag_mask", {}), ("naloxone", {"dose_mg": 2.0, "route": "IN"})], [], []),
    ("C02", "es", "pulmonary_embolism", "pulmonary_embolism_61m",
     "TEP de alto riesgo con hipotensión: trombolisis con alteplasa 100 mg ev en 2 horas.",
     [("thrombolysis", {"agent": "alteplase", "dose_mg": 100.0, "administration_duration_min": 120.0})], [], []),
    ("C02", "es", "pneumonia", "pneumonia_83m", "Shock séptico: noradrenalina 0,1 mcg/kg/min.",
     [("norepinephrine", {"rate": 0.1})], [], []),
    ("C02", "en", "anaphylaxis", "anaphylaxis_29f", "Plan: epinephrine 0.5 mg IM.",
     [("epinephrine_im", {"dose_mg": 0.5})], [], []),
    ("C02", "es", "pneumonia", "pneumonia_83m", "Hipotensión persistente: noradrenalina 0,1 mcg/kg/min.",
     [("norepinephrine", {"rate": 0.1})], [], []),
    # C03 · "Now X and then repeat": X now, the repeat is X's plan.
    ("C03", "es", "asthma", "asthma_24f", "Ahora salbutamol 5 mg nbz y luego repetir cada 20 minutos por 3 veces.",
     [("bronchodilator", {"dose_mg": 5.0, "route": "nebulized"})], [], ["repeat"]),
    ("C03", "en", "asthma", "asthma_24f", "Now albuterol 5 mg nebulized and then repeat every 20 minutes three times.",
     [("bronchodilator", {"dose_mg": 5.0, "route": "nebulized"})], [], ["repeat"]),
    ("C03", "es", "anaphylaxis", "anaphylaxis_29f",
     "Primero adrenalina 0,5 mg IM y repetir en 5 minutos si no responde.",
     [("epinephrine_im", {"dose_mg": 0.5})], [], ["repeat"]),
    # C04 · "Stop A and switch to B <amount>": A stops, B starts.
    ("C04", "es", "gi_bleed", "gi_bleed_72f", "Suspende el SF y cambia a Ringer lactato 500 mL ev.",
     [("fluid", {"operation": "stop", "fluid_type": "normal saline"}),
      ("fluid", {"volume_ml": 500.0, "fluid_type": "lactated Ringer's"})], [], []),
    ("C04", "en", "gi_bleed", "gi_bleed_72f", "Stop the saline and switch to lactated Ringer's 500 mL IV.",
     [("fluid", {"operation": "stop", "fluid_type": "normal saline"}),
      ("fluid", {"volume_ml": 500.0, "fluid_type": "lactated Ringer's"})], [], []),
    # C05 · disposition + "on/with" treatment: both.
    ("C05", "en", "hypoglycemia", "hypoglycemia_76f",
     "She's on glimepiride, so no discharge tonight; admit to the ward on a D10 drip at 100 mL/h "
     "with hourly glucose checks.",
     [("disposition", {"destination": "ward"}), ("dextrose_infusion", {"rate_ml_h": 100.0})], [], []),
    ("C05", "es", "pneumonia", "pneumonia_83m", "Ingreso a UCI con noradrenalina 0,1 mcg/kg/min.",
     [("disposition", {"destination": "ICU"}), ("norepinephrine", {"rate": 0.1})], [], []),
    ("C05", "en", "pneumonia", "pneumonia_83m", "Admit to the ICU on norepinephrine 0.1 mcg/kg/min.",
     [("disposition", {"destination": "ICU"}), ("norepinephrine", {"rate": 0.1})], [], []),
    # C06 · Spanish first-person activation.
    ("C06", "es", "acs", "acs_54m_inferior", "Activo hemodinamia para angioplastia primaria y repito ECG en 10 minutos.",
     [("consult", {"service": "cath lab"})], ["diagnostic"], ["repeat"]),
    ("C06", "es", "acs", "acs_61m_posterior", "Activo código infarto.", [("consult", {"service": "cath lab"})], [], []),
    ("C06", "es", "acs", "acs_61m_posterior", "Activamos hemodinamia.", [("consult", {"service": "cath lab"})], [], []),
    ("C06", "en", "acs", "acs_61m_posterior", "Activate the cath lab for primary PCI.",
     [("consult", {"service": "cath lab"})], [], []),
    # C07 · "Because of <reason> I <verb> <order>".
    ("C07", "es", "trauma", "trauma_hemothorax_41m",
     "Por el hemotórax masivo izquierdo instalo tubo pleural izquierdo; espero que mejore la saturación y la PA, "
     "reevalúo en 5 minutos.",
     [("chest_decompression", {"side": "left"}), ("reassessment", {"delay_min": 5.0})], [], []),
    ("C07", "en", "trauma", "trauma_hemothorax_41m",
     "For the massive left hemothorax I place a left chest tube and reassess in 5 minutes.",
     [("chest_decompression", {"side": "left"}), ("reassessment", {"delay_min": 5.0})], [], []),
    ("C07", "es", "pneumonia", "pneumonia_83m", "Por la hipotensión inicio noradrenalina 0,1 mcg/kg/min.",
     [("norepinephrine", {"rate": 0.1})], [], []),
    ("C07", "en", "pneumonia", "pneumonia_83m", "Given the hypotension I start norepinephrine 0.1 mcg/kg/min.",
     [("norepinephrine", {"rate": 0.1})], [], []),
    # C08 · TXA with its duration inside an urgent bundle: everything runs.
    ("C08", "en", "trauma", "trauma_limb_hemorrhage_27m",
     "Tourniquet high on the right thigh now, two large-bore IVs, and TXA 1 g IV over 10 minutes.",
     [("hemorrhage_control", {"measure": "tourniquet"}),
      ("tranexamic_acid", {"dose_g": 1.0, "administration_duration_min": 10.0})], [], []),
    ("C08", "es", "trauma", "trauma_limb_hemorrhage_27m",
     "Torniquete en muslo derecho, 2 VVP gruesas, ácido tranexámico 1 g ev en 10 min.",
     [("hemorrhage_control", {"measure": "tourniquet"}),
      ("tranexamic_acid", {"dose_g": 1.0, "administration_duration_min": 10.0})], [], []),
    # C09 · a finding after the order is no second order.
    ("C09", "es", "pneumonia", "pneumonia_83m",
     "Súbele el oxígeno a mascarilla con reservorio a 15 litros, satura 86% con la naricera.",
     [("oxygen", {"device": "non-rebreather mask", "flow_lpm": 15.0})], [], []),
    ("C09", "en", "pneumonia", "pneumonia_83m", "Switch her to a non-rebreather at 15 L/min, sats 86% on the nasal cannula.",
     [("oxygen", {"device": "non-rebreather mask", "flow_lpm": 15.0})], [], []),
    ("C09", "es", "pneumonia", "pneumonia_83m", "Súbele el oxígeno a 6 L por naricera, satura 88%.",
     [("oxygen", {"device": "nasal cannula", "flow_lpm": 6.0})], [], []),
    ("C09", "en", "bradycardia", "bradycardia_avb3_78f", "Atropine 1 mg IV, HR 38.",
     [("atropine", {"dose_mg": 1.0})], [], []),
    # Class flaws the blind held-out checks found in the first corrections.
    ("C05", "en", "asthma", "asthma_24f", "Admit to the ICU on continuous albuterol 10 mg/h.",
     [("disposition", {"destination": "ICU"}), ("continuous_bronchodilator", {"rate_mg_h": 10.0})], [], []),
    ("C05", "es", "opioid", "opioid_67f", "Ingresa a intermedio con infusión de naloxona a 0,4 mg/h.",
     [("disposition", {"destination": "intermediate care"}), ("naloxone_infusion", {"rate_mg_h": 0.4})], [], []),
    ("C04", "en", "gi_bleed", "gi_bleed_72f", "Hold the saline and change to lactated Ringer's 500 mL over 30 min.",
     [("fluid", {"operation": "stop", "fluid_type": "normal saline"}),
      ("fluid", {"volume_ml": 500.0, "fluid_type": "lactated Ringer's"})], [], []),
    ("C04", "es", "gi_bleed", "gi_bleed_72f", "Cierra el SF y pon 1 litro de Ringer a pasar en 30 minutos.",
     [("fluid", {"operation": "stop", "fluid_type": "normal saline"}),
      ("fluid", {"volume_ml": 1000.0, "fluid_type": "lactated Ringer's"})], [], []),
    ("C01", "en", "asthma", "asthma_24f",
     "Magnesium sulfate 2 g IV over 20 minutes, if no improvement, we go to intubation.",
     [("magnesium", {"dose_mg": 2000.0})], ["intubation"], ["conditional"]),
    ("C02", "es", "acs", "acs_61m_posterior", "IAM posterior: aspirina 300 mg vo.",
     [("aspirin", {"dose_mg": 300.0})], [], []),
    # The line a fluid runs through is its route: the bolus was lost and a line
    # placed instead (found by the blind held-out check; exposed by C01).
    ("C01", "es", "gi_bleed", "gi_bleed_72f", "SF 500 mL por VVP en 15 minutos.",
     [("fluid", {"volume_ml": 500.0, "fluid_type": "normal saline"})], ["vascular_access"], []),
    ("C01", "en", "gi_bleed", "gi_bleed_72f", "Give 500 mL NS via the PIV over 15 minutes.",
     [("fluid", {"volume_ml": 500.0, "fluid_type": "normal saline"})], ["vascular_access"], []),
    ("C01", "es", "gi_bleed", "gi_bleed_72f",
     "Carga de SF 500 mL por la VVP, si no responde, noradrenalina 0,05 mcg/kg/min.",
     [("fluid", {"volume_ml": 500.0})], ["vascular_access", "norepinephrine"], ["conditional"]),
    # The resident's own order after the prehospital team's account still runs.
    ("C08", "es", "trauma", "trauma_limb_hemorrhage_27m",
     "El paramédico dejó 2 VVP y pongo torniquete alto en el muslo derecho.",
     [("hemorrhage_control", {"measure": "tourniquet"})], [], []),
    ("C08", "en", "trauma", "trauma_limb_hemorrhage_27m",
     "EMS started a line and I place a tourniquet high on the right thigh.",
     [("hemorrhage_control", {"measure": "tourniquet"})], [], []),
]

# (class, language, text, types that must not run now, plan kinds that must be kept)
NEGATIVE = [
    ("C01", "es", "Atropina 1 mg ev, si persiste la bradicardia.", ["atropine"], ["conditional"]),
    ("C01", "en", "If no response, transcutaneous pacing at 70 bpm with 60 mA.", ["transcutaneous_pacing"],
     ["conditional"]),
    ("C01", "es", "Si no responde, marcapaso transcutáneo a 70 lpm con 60 mA.", ["transcutaneous_pacing"],
     ["conditional"]),
    ("C01", "es", "Adrenalina 0,5 mg IM, si no responde, a los 5 minutos.", ["epinephrine_im"], ["conditional"]),
    # A head that is a condition, a time, an alternative or something awaited
    # keeps what follows from running now.
    ("C02", "en", "Plan B: intubate.", ["intubation"], []),
    ("C02", "en", "PRN: morphine 2 mg IV.", ["opioid_analgesia"], []),
    ("C02", "es", "SOS: morfina 2 mg ev.", ["opioid_analgesia"], []),
    ("C02", "es", "Refractario: vasopresina 0,04 U/min.", [], []),
    ("C02", "en", "No response: repeat epinephrine 0.5 mg IM.", ["repeat_order", "epinephrine_im"], []),
    ("C02", "es", "Una vez estable: TAC de abdomen.", ["diagnostic"], []),
    ("C02", "en", "Later: CT head.", ["diagnostic"], []),
    ("C02", "es", "Persiste: cardioversión 100 J.", ["cardioversion"], []),
    ("C02", "en", "Post-intubation: fentanyl 50 mcg/h.", ["sedation_infusion"], []),
    ("C02", "es", "Evitar: nitroglicerina.", ["nitroglycerin"], []),
    ("C02", "es", "Si no responde: adrenalina 0,5 mg IM.", ["epinephrine_im"], ["conditional"]),
    ("C02", "en", "If worse: intubate.", ["intubation"], ["conditional"]),
    ("C03", "es", "Repetir salbutamol cada 20 minutos por 3 veces.", ["bronchodilator"], ["repeat"]),
    ("C05", "en", "Discharge home with ibuprofen 400 mg every 8 hours.", ["analgesia", "antipyretic"],
     ["prescription"]),
    ("C05", "es", "Alta con paracetamol 1 g c/8 h por 5 días.", ["antipyretic"], ["prescription"]),
    ("C06", "es", "El cardiólogo ya activó hemodinamia.", ["consult"], []),
    ("C07", "es", "Por la disnea el paramédico inició oxígeno por naricera.", ["oxygen"], []),
    ("C07", "es", "Por el paso del tiempo empeora.", ["oxygen", "norepinephrine"], []),
    ("C07", "en", "I think we should start norepinephrine.", ["norepinephrine"], []),
    ("C09", "es", "Satura 86% con la naricera.", ["oxygen"], []),
    ("C09", "en", "Sats 86% on the nasal cannula.", ["oxygen"], []),
    # False executions the blind held-out checks found: tranexamic acid read in
    # someone else's history, a thought or a withholding once its duration was
    # accepted, and a threshold heading that is a condition.
    ("C08", "en", "Medic already gave TXA 1 g over 10 min en route.", ["tranexamic_acid"], []),
    ("C08", "en", "She got TXA 1 g IV in the ambulance.", ["tranexamic_acid"], []),
    ("C08", "es", "Estaba pensando en dar tranexámico 1 g ev en 10 min.", ["tranexamic_acid"], []),
    ("C08", "es", "Ya van más de 3 horas del trauma, así que no corresponde ácido tranexámico 1 g en 10 min.",
     ["tranexamic_acid"], []),
    ("C08", "es", "Recibió ácido tranexámico 1 g ev en el SAMU.", ["tranexamic_acid"], []),
    ("C02", "es", "Con HGT estables sobre 150: suspender SG 10% y dejar SG 5% a 70 mL/h.",
     ["dextrose_infusion", "fluid"], []),
    ("C02", "en", "MAP under 65: start norepinephrine 0.1 mcg/kg/min.", ["norepinephrine"], []),
    ("C05", "es", "Ingreso a sala con su esposa.", ["clarification"], []),
    # What the prehospital team did goes on past "and"/"y": the clause joined to
    # it is asked about, never run (C08; the first two found by the blind checks).
    ("C08", "en", "Medic already gave TXA 1 g over 10 min en route and put on a tourniquet.",
     ["hemorrhage_control", "tranexamic_acid"], []),
    ("C08", "es", "El paramédico ya dejó 2 VVP y pasó tranexámico 1 g en 10 minutos.",
     ["tranexamic_acid", "vascular_access"], []),
    ("C08", "en", "EMS started a line and placed a tourniquet on the right leg.", ["hemorrhage_control"], []),
    ("C08", "es", "En la ambulancia le pusieron una vía y colocaron torniquete en la pierna.",
     ["hemorrhage_control", "vascular_access"], []),
    # A result that may not be in yet is a condition, as a threshold is.
    ("C02", "es", "Con angioTAC positivo: enoxaparina 1 mg/kg c/12 h sc.", ["anticoagulation"], []),
    ("C02", "en", "With a positive CTA: enoxaparin 1 mg/kg SC every 12 hours.", ["anticoagulation"], []),
]

# Heads that are a reason stay one order: the colon is stepped over only after a label.
ONE_ORDER = [
    ("Oxygen: nasal cannula 2 L/min.", ("oxygen", {"device": "nasal cannula", "flow_lpm": 2.0})),
    ("Norepinephrine: 0.1 mcg/kg/min.", ("norepinephrine", {"rate": 0.1})),
    ("Epinefrina 1:1000 0,5 mg IM.", ("epinephrine_im", {"dose_mg": 0.5})),
]


def _matches(action, kind, fields):
    if action.get("type") != kind:
        return False
    return all(action.get(key) == value for key, value in fields.items())


def _ids(rows):
    return [f"{row[0]}-{row[1]}-{index}" for index, row in enumerate(rows)]


@pytest.mark.parametrize("cls, lang, family, case_id, text, run, forbidden, plans", POSITIVE, ids=_ids(POSITIVE))
def test_the_reader_reads_the_order_that_runs_now(cls, lang, family, case_id, text, run, forbidden, plans):
    parsed = parse_family_actions(text)
    actions = parsed["actions"]
    assert not any(action.get("type") == "clarification" for action in actions), actions
    for kind, fields in run:
        assert any(_matches(action, kind, fields) for action in actions), (kind, fields, actions)
    for kind in forbidden:
        assert not any(action.get("type") == kind for action in actions), (kind, actions)
    assert sorted({detail.get("kind") for detail in parsed["future_details"]}) == sorted(set(plans))


@pytest.mark.parametrize("cls, lang, text, forbidden, plans", NEGATIVE, ids=_ids(NEGATIVE))
def test_a_near_miss_runs_nothing_it_should_not(cls, lang, text, forbidden, plans):
    parsed = parse_family_actions(text)
    for kind in forbidden:
        assert not any(action.get("type") == kind for action in parsed["actions"]), (kind, parsed["actions"])
    kinds = {detail.get("kind") for detail in parsed["future_details"]}
    assert set(plans) <= kinds, parsed["future_details"]


# --- what the adversarial review of the cycle 6 diff found in the corrections themselves ----
# Each sentence reads as cycle 5 read it, or better: (text, what must be read now, what must not).
REVIEW = [
    # C04: a stop is not lent to a new order, and "para" is also "for".
    ("Hold NS, O2 4 L NC", [("fluid", {"operation": "stop"}), ("oxygen", {"device": "nasal cannula", "flow_lpm": 4.0})],
     []),
    ("Cierra el suero y oxígeno por naricera a 3 L/min",
     [("fluid", {"operation": "stop"}), ("oxygen", {"device": "nasal cannula"})], []),
    ("Hold the saline, furosemide 40 mg IV", [("fluid", {"operation": "stop"}), ("diuretic", {"dose_mg": 40.0})], []),
    ("Suspender SF, O2 4 L NC", [("oxygen", {"device": "nasal cannula"})], []),
    ("Suspender noradrenalina y dobutamina",
     [("norepinephrine", {"operation": "stop"}), ("dobutamine", {"operation": "stop"})], []),
    ("Turn off the maintenance fluids, she's wet, and switch to a nitro drip at 50 mcg/min",
     [("fluid", {"operation": "stop"})], ["clarification"]),
    ("Para los fluidos: Ringer lactato 500 mL ev", [], ["fluid"]),
    # C07: a question, a hedge, a habit or prose in the first person is no order.
    ("Should I give aspirin 300 mg PO?", [], ["aspirin"]),
    ("Normally we start norepinephrine 0.1 mcg/kg/min but not now", [], ["norepinephrine"]),
    ("Por qué no inicio noradrenalina 0,1 mcg/kg/min?", [], ["norepinephrine"]),
    ("Por lo general administro aspirina 300 mg vo", [], ["aspirin"]),
    ("I think we start norepinephrine 0.1 mcg/kg/min", [], ["norepinephrine"]),
    ("Epinephrine 0.5 mg IM now. We give it 5 minutes and then reassess.", [("epinephrine_im", {"dose_mg": 0.5})],
     ["clarification"]),
    # C08: the history test guards only what is read anywhere in the piece.
    ("Paracetamol 1 g ev ya que AINE contraindicado", [("antipyretic", {})], []),
    ("Aspirin 300 mg PO (not given by EMS)", [("aspirin", {"dose_mg": 300.0})], []),
    ("Epinephrine 0.5 mg IM given anaphylaxis", [("epinephrine_im", {})], ["clarification"]),
    ("Tourniquet high on the right thigh. IV TXA 1 g.", [("hemorrhage_control", {}), ("tranexamic_acid", {})], []),
    ("Urgent TXA 1 g IV", [("tranexamic_acid", {})], []),
    ("El ácido tranexámico 1 g ev", [("tranexamic_acid", {})], []),
    # The prehospital account: the team as the subject, told in the past; a comma
    # before "and" does not bypass it.
    ("Remove the EMS dressing and apply a tourniquet high on the right thigh", [("hemorrhage_control", {})],
     ["clarification"]),
    ("Aspirin given by EMS, give clopidogrel 600 mg PO and heparin 5000 units IV",
     [("p2y12", {}), ("anticoagulation", {})], ["clarification"]),
    ("Ask the medic what he gave and give naloxone 0.4 mg IV", [("naloxone", {"dose_mg": 0.4})], []),
    ("El paramedico ya dejo 2 VVP, y paso tranexamico 1 g en 10 minutos.", [], ["tranexamic_acid"]),
    ("Medic already gave TXA 1 g over 10 min en route, and put on a tourniquet.", [],
     ["hemorrhage_control", "tranexamic_acid"]),
    # C09: "RR" after an airway order is its rate, not a finding.
    ("Intubate, VC/AC, RR 10, PEEP 5, FiO2 100%", [("intubation", {"rate_per_min": 10.0, "peep_cmh2o": 5.0})], []),
    # C02: sedation or analgesia with a procedure is quoted back, not half run.
    ("Sedation with etomidate 8 mg IV before synchronized cardioversion 200 J", [], ["cardioversion"]),
    ("Analgesia with morphine 4 mg IV before the chest tube", [], ["chest_decompression"]),
    # C05: prepared is not started.
    ("Admit to the ICU with a norepinephrine infusion ready", [("disposition", {})], ["norepinephrine"]),
    # The activation of a service is never lent to the medicines after it (since
    # before cycle 6; C02 and C06 put it in front of more sentences).
    ("Activate the cath lab, aspirin 325 mg and ticagrelor 180 mg PO",
     [("consult", {"service": "cath lab"}), ("aspirin", {"dose_mg": 325.0}), ("p2y12", {"dose_mg": 180.0})], []),
    ("IAM posterior con supra ST en V7-V9: activar hemodinamia, heparina 5.000 U ev y ticagrelor 180 mg vo",
     [("consult", {"service": "cath lab"}), ("p2y12", {"dose_mg": 180.0})], []),
    # C01: the instruction after a condition is read up to the next condition.
    ("AAS 250 mg vo masticada, si reaparece el dolor, considerar activar hemodinamia", [("aspirin", {"dose_mg": 250.0})],
     []),
]


@pytest.mark.parametrize("text, run, forbidden", REVIEW)
def test_what_the_adversarial_review_found_reads_as_cycle_5_did_or_better(text, run, forbidden):
    actions = parse_family_actions(text)["actions"]
    for kind, fields in run:
        assert any(_matches(action, kind, fields) for action in actions), (kind, fields, actions)
    for kind in forbidden:
        assert not any(action.get("type") == kind for action in actions), (kind, actions)


def test_a_conditional_plan_that_names_tranexamic_acid_is_kept():
    for text in ("If it keeps oozing, run the second gram of TXA over 8 hours.",
                 "Si sigue sangrando, segundo gramo de ácido tranexámico en 8 horas."):
        parsed = parse_family_actions(text)
        assert not parsed["actions"] and [d["kind"] for d in parsed["future_details"]] == ["conditional"]


def test_a_chain_of_conditions_and_a_run_of_spaces_are_read_in_time():
    import time
    for text in ("atropina 1 mg ev, " + "si no, tcp, " * 12, "Por" + " " * 600 + "la hipotension."):
        start = time.perf_counter()
        parse_family_actions(text)
        assert time.perf_counter() - start < 2.0


def test_an_answer_in_the_first_person_is_not_taken_for_a_new_order():
    from family_parser import _opens_with_an_order
    assert not _opens_with_an_order("we start at 0.1 mcg/kg/min")
    assert _opens_with_an_order("start norepinephrine 0.1 mcg/kg/min")
    assert _opens_with_an_order("i will give naloxone 0.4 mg iv")


def test_the_duration_of_a_medicine_reads_in_spanish():
    import language
    assert language.say("Tranexamic acid 1 g IV administered over 10 min", "es").endswith("administrado en 10 min")


def test_the_question_about_a_clause_joined_to_the_prehospital_account_reads_in_spanish():
    import language
    message = parse_family_actions(
        "Medic already gave TXA 1 g over 10 min en route and put on a tourniquet.")["actions"][0]["message"]
    said = language.say(message, "es")
    assert said.startswith("«put on a tourniquet» está escrito junto a lo que hizo el equipo prehospitalario")
    assert "Si ahora es tu orden" in said and "quedan retenidas hasta entonces" in said


@pytest.mark.parametrize("text, expected", ONE_ORDER)
def test_a_colon_inside_one_order_is_not_a_label(text, expected):
    actions = parse_family_actions(text)["actions"]
    kind, fields = expected
    assert len(actions) == 1 and _matches(actions[0], kind, fields), actions


def test_a_repeat_after_the_order_is_that_order_s_plan():
    for text in ("Ahora salbutamol 5 mg nbz y luego repetir cada 20 minutos por 3 veces.",
                 "Salbutamol 5 mg nbz, si persiste el broncoespasmo, repetir cada 20 minutos.",
                 "Anaphylaxis with stridor and facial swelling: epinephrine 0.5 mg IM in the thigh now, "
                 "repeat in 5 minutes if no response."):
        [plan] = parse_family_actions(text)["future_details"]
        assert plan["kind"] == "repeat" and plan["of"], plan
    # A repeat that names its own study is not the repeat of the order before it.
    [plan] = parse_family_actions("Activo hemodinamia para angioplastia primaria y repito ECG en 10 minutos.")[
        "future_details"]
    assert plan["of"] is None and "ecg" in plan["text"]


PAIRS = [
    ("Atropina 1 mg ev, si no responde, marcapaso transcutáneo a 70 lpm con 60 mA.",
     "Atropine 1 mg IV, if no response, transcutaneous pacing at 70 bpm with 60 mA."),
    ("Noradrenalina 0,1 mcg/kg/min, si persiste hipotenso, agregar vasopresina 0,03 U/min.",
     "Norepinephrine 0.1 mcg/kg/min, if still hypotensive, add vasopressin 0.03 U/min."),
    ("Ahora salbutamol 5 mg nbz y luego repetir cada 20 minutos por 3 veces.",
     "Now albuterol 5 mg nebulized and then repeat every 20 minutes three times."),
    ("Suspende el SF y cambia a Ringer lactato 500 mL ev.",
     "Stop the saline and switch to lactated Ringer's 500 mL IV."),
    ("Ingreso a UCI con noradrenalina 0,1 mcg/kg/min.", "Admit to the ICU on norepinephrine 0.1 mcg/kg/min."),
    ("Activamos hemodinamia.", "Activate the cath lab for primary PCI."),
    ("Por la hipotensión inicio noradrenalina 0,1 mcg/kg/min.",
     "Given the hypotension I start norepinephrine 0.1 mcg/kg/min."),
    ("Torniquete en muslo derecho, 2 VVP gruesas, ácido tranexámico 1 g ev en 10 min.",
     "Tourniquet high on the right thigh now, two large-bore IVs, and TXA 1 g IV over 10 minutes."),
    ("Súbele el oxígeno a mascarilla con reservorio a 15 litros, satura 86% con la naricera.",
     "Switch her to a non-rebreather at 15 L/min, sats 86% on the nasal cannula."),
]


@pytest.mark.parametrize("spanish, english", PAIRS)
def test_the_two_languages_read_the_same_orders(spanish, english):
    types = [sorted(a["type"] for a in parse_family_actions(text)["actions"]) for text in (spanish, english)]
    assert types[0] == types[1], types
    plans = [sorted(d["kind"] for d in parse_family_actions(text)["future_details"]) for text in (spanish, english)]
    assert plans[0] == plans[1], plans


# --- executed by the engine on the case the sentence is written for ---------------------------

@pytest.fixture(scope="module")
def engine():
    return load_engine()


_STATES = {}


def _run(engine, family, case_id, text, setup=None):
    from copy import deepcopy
    from family_engine import execute_family_bundle
    from test_cognitive_encounters import encounter
    from test_curriculum_trajectories import initialize
    if case_id not in _STATES:
        _STATES[case_id] = encounter(engine, family, case_id)["state"]
    state = deepcopy(_STATES[case_id])
    initialize(engine, state)
    session = engine["st"].session_state
    if setup:
        assert execute_family_bundle(session.state, engine["clinical_interpreter"](setup))["executed"]
    return execute_family_bundle(session.state, engine["clinical_interpreter"](text))


SETUP = {"gi_bleed_72f": "SF 1000 mL ev en 60 minutos, reevalúo en 10 minutos"}


@pytest.mark.parametrize("cls, lang, family, case_id, text, run, forbidden, plans", POSITIVE, ids=_ids(POSITIVE))
def test_the_engine_runs_it(engine, cls, lang, family, case_id, text, run, forbidden, plans):
    result = _run(engine, family, case_id, text, SETUP.get(case_id))
    assert result["executed"], result.get("clarification")
    assert not result.get("clarification")
    ran = {summary.get("type") for summary in result.get("action_summaries") or []}
    for kind in forbidden:
        assert kind not in ran, (kind, ran)


def test_the_tranexamic_acid_duration_is_recorded_like_any_other_medicine_s(engine):
    result = _run(engine, "trauma", "trauma_limb_hemorrhage_27m",
                  "Tourniquet high on the right thigh now, two large-bore IVs, and TXA 1 g IV over 10 minutes.")
    labels = [summary.get("label") for summary in result["action_summaries"]]
    assert "Tranexamic acid 1 g IV administered over 10 min" in labels
    record = [m for m in engine["st"].session_state.state["treatments"]["administered_medications"]
              if m.get("agent") == "tranexamic acid"][-1]
    assert record["administration_duration_min"] == 10.0
    # As for every fixed-dose medicine written with its time, the stated
    # minutes pass when no reassessment is given; the drug's effect is the one
    # the engine already models, with or without the duration.
    # With the bleeding stopped first: an untreated limb haemorrhage now collapses at minute 6
    # and stops the turn there (Phase 0, 0F), which is not what this test is about.
    tourniquet = "Tourniquet high on the right thigh now."
    timed = _run(engine, "trauma", "trauma_limb_hemorrhage_27m", "TXA 1 g IV over 10 minutes.", setup=tourniquet)
    plain = _run(engine, "trauma", "trauma_limb_hemorrhage_27m", "TXA 1 g IV.", setup=tourniquet)
    assert timed["executed"] and plain["executed"]
    assert timed["elapsed_min"] == 10 and plain["elapsed_min"] < 10


def test_a_stop_written_with_a_duration_does_not_break_the_page(engine):
    # KeyError: 'volume_ml' reached the page; C04's stop verbs made it reachable.
    result = _run(engine, "gi_bleed", "gi_bleed_72f", "Suspender el SF en 30 minutos")
    assert result["executed"]


@pytest.mark.parametrize("family, case_id, text, kinds", [
    ("trauma", "trauma_limb_hemorrhage_27m", "Tourniquet high on the right thigh. IV TXA 1 g.",
     {"hemorrhage_control", "tranexamic_acid"}),
    ("anaphylaxis", "anaphylaxis_29f", "Epinephrine 0.5 mg IM now. We give it 5 minutes and then reassess.",
     {"epinephrine_im"}),
    ("acs", "acs_61m_posterior", "Activate the cath lab, aspirin 325 mg and ticagrelor 180 mg PO", {"aspirin", "p2y12"}),
])
def test_the_first_line_orders_the_review_found_held_run_in_the_engine(engine, family, case_id, text, kinds):
    result = _run(engine, family, case_id, text, SETUP.get(case_id))
    assert result["executed"] and not result.get("clarification"), result.get("clarification")
    ran = {summary.get("type") for summary in result.get("action_summaries") or []}
    assert kinds <= ran, ran


def test_the_order_is_not_quoted_as_the_working_model(engine):
    extract = engine["extract_explicit_reasoning"]
    for text, model in (
            ("Anaphylaxis with stridor and facial swelling: epinephrine 0.5 mg IM in the thigh now.",
             "Anaphylaxis with stridor and facial swelling"),
            ("TEP de alto riesgo con hipotensión: trombolisis con alteplasa 100 mg ev en 2 horas.",
             "TEP de alto riesgo con hipotensión")):
        assert extract(text).get("problem_representation") == model


# --- through the real page, read back from the stored Management Trace -----------------------

SCENARIOS = [
    # (name, language, family, case, challenge, order, what ran, what must not run, plan kinds)
    ("anaphylaxis", "es", "anaphylaxis", "anaphylaxis_29f", "R1-06",
     "Anafilaxia con estridor y edema facial: adrenalina 0,5 mg IM en el muslo ahora, repetir en 5 minutos "
     "si no responde.", "Epinephrine 0.5 mg IM administered", "transcutaneous", ["repeat"]),
    ("bradycardia", "en", "bradycardia", "bradycardia_avb3_78f", "R2-04",
     "Atropine 1 mg IV, if no response, transcutaneous pacing at 70 bpm with 60 mA.",
     "atropine 1 mg IV administered", "pacing", ["conditional"]),
    ("shock", "es", "pneumonia", "pneumonia_83m", "R1-05",
     "Ingreso a UCI con noradrenalina 0,1 mcg/kg/min.", "orepinephrine", None, []),
    ("oxygen", "en", "pneumonia", "pneumonia_83m", "R1-05",
     "Switch her to a non-rebreather at 15 L/min, sats 86% on the nasal cannula.",
     "Non-rebreather mask at 15 L/min", "Nasal cannula", []),
]


@pytest.mark.parametrize("name, lang, family, case_id, challenge, order, ran, not_ran, plans", SCENARIOS,
                         ids=[row[0] for row in SCENARIOS])
def test_the_stored_management_trace_records_what_was_written(tmp_path, monkeypatch, name, lang, family, case_id,
                                                              challenge, order, ran, not_ran, plans):
    import tools_order_reading
    import tools_tanda20
    # Through monkeypatch, so the offline mode ends with this test (C-2026-09-26-20).
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    script = {"number": 1, "case_id": case_id, "family": family, "category": "test", "challenge": challenge,
              "intent": "DF-22", "language": lang, "steps": [("order", order)], "resolve_until_clear": True,
              "reflection": {}, "plan": {}, "comparison": {"alignment": "-", "adjustment": "-"}}
    result = tools_tanda20.rehearse(script, tmp_path, seed=3000)
    assert result["stopped"] is None, result["stopped"]
    stored = tools_order_reading.stored_encounter(tmp_path / "rehearsal-01.sqlite3")
    assert stored["ai_calls_spent"] in (0, None)
    entries = [entry for entry in stored["trace"] if entry["input"].startswith(order[:25])]
    executed = [entry for entry in entries if entry["status"] == "executed"]
    assert executed, entries
    entry = executed[-1]
    assert any(ran in summary for summary in entry["summaries"]), entry["summaries"]
    if not_ran:
        assert not any(not_ran in summary for summary in entry["summaries"]), entry["summaries"]
    assert sorted({kind for kind, _ in entry["plans"]}) == sorted(set(plans)), entry["plans"]
    # The order is not the working model the trace quotes back.
    model = entry["slots"].get("problem_representation", "")
    assert "mg" not in model and "L/min" not in model, model
