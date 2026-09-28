"""The reader classes of cycle 8: TD-29, TD-30, TD-31, TD-32 and KD-05.

Each class was fixed as a class and measured with the A–J standard: an independent set for
development, a blind held-out set measured once, post-hoc changes labelled, negative controls,
an adversarial review and a comparison with the frozen V2 reader over every text the repository
holds (docs/MEDICION_RECONOCIMIENTO_ORDENES.md, cycle 8).

- TD-29: "when", "cuando", "once", "en cuanto", "apenas" (with the subjunctive), "una vez que",
  "tan pronto como" make an order a plan when they name the patient's value or course.
- TD-30: orders written without a verb or with "take": consults as nouns, the endoscopy asked
  for (a call to gastroenterology in this simulator), cultures with their count, large-bore lines.
- TD-31: intramuscular adrenaline without a dose is asked its dose in milligrams, never a rate.
- TD-32: "2 U. GR", the protocol stood down, platelets on a count, the crossmatch's state, the
  time of each unit.
- KD-05: "OK to discharge" and "ok para alta" are a discharge.
"""
import pytest

import language
import unexecuted_items
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine


def read(text):
    return parse_family_actions(text)["actions"]


def kinds(text):
    return [action["type"] for action in read(text)]


def kept(text):
    return [(detail["kind"], detail.get("category")) for detail in parse_family_actions(text)["future_details"]]


# --- TD-29: a condition on the patient, said with "when" as with "if" ---------------------------

@pytest.mark.parametrize("text", [
    "When BP drops, give NS 500 mL", "Cuando baje la PA, bolo SF 500 mL", "Once the BP drops below 90, give 500 mL NS",
    "When glucose is below 70, give D50 50 mL", "Give NS 500 mL when BP drops",
    "Bolus 500 mL LR whenever her systolic drops below 90", "Apenas la HGT baje de 70, pasar 60 mL de glucosa al 30% ev",
    "Cuando la saturación baje de 90%, subir O2 a reservorio 15 L", "Cuando empeore, intubar",
    "Once stable, transfer to the ward", "Cuando esté estable, trasladar a sala", "Transfundir 2 U GR cuando Hb < 7",
    "Paracetamol 1 g EV cuando la temperatura sea mayor a 38.5", "When she wakes up, give oral glucose",
    # A condition written without a comma runs on into its order (post hoc, blind set).
    "when hgb drops below 7 transfuse 1 unit PRBC", "whenever she gets drowsy or pCO2 >45 -> call ICU",
    "if hgb drops below 7 transfuse 1 unit PRBC",
    # A result with the value it must reach (post hoc, blind set).
    "when lactate comes back >4 give 30 ml/kg LR", "IC a cardio en cuanto salga la troponina positiva",
])
def test_a_condition_on_the_patient_keeps_the_order_as_a_plan(text):
    assert not read(text), read(text)
    assert kept(text) == [("conditional", None)]


@pytest.mark.parametrize("text, now", [
    ("Start O2 2 L NC and when SBP < 90 give NS 500 mL", "oxygen"),
    ("Ceftriaxone 2 g IV now, and when MAP falls below 65 give LR 1 L", "antibiotics"),
    ("Atropina 1 mg ev, cuando la FC baje de 40, marcapaso transcutáneo", "atropine"),
    ("Monitor BP; when MAP < 65 start norepinephrine 0.1 mcg/kg/min", "reassessment"),
    ("Instalar 2 VVP gruesas y una vez que la Hb baje de 7, transfundir 1 U de GR", "vascular_access"),
])
def test_the_order_before_the_condition_runs_and_the_one_after_it_is_the_plan(text, now):
    assert kinds(text) == [now]
    assert kept(text) == [("conditional", None)]


@pytest.mark.parametrize("text, now", [
    ("Cuando puedas, pasa 1 L de SF", "fluid"), ("Give ceftriaxone 2 g IV as soon as possible", "antibiotics"),
    ("When I examined him his BP was 80/50, give 1 L NS", "fluid"),
    ("Once intubated, start propofol 20 mcg/kg/min", "sedation_infusion"),
    ("Once IV access is in, give ceftriaxone 2 g IV", "antibiotics"),
    ("Apenas puedas, ponle O2 por naricera a 2 L/min", "oxygen"),
    # "Apenas" before what the patient does is "barely".
    ("Apenas mejora la PA con volumen, iniciar noradrenalina 0.1 mcg/kg/min", "norepinephrine"),
    ("Ceftriaxona 2 g ev lo antes posible", "antibiotics"),
])
def test_what_the_team_can_do_a_story_and_the_same_turn_order_now(text, now):
    assert kinds(text) == [now]
    assert not kept(text)


def test_something_awaited_with_no_value_to_reach_is_asked_about_as_before():
    assert [a["message"][:40] for a in read("When blood arrives, transfuse 2 units PRBC")] == [
        "Specify whether to transfuse these units"]


@pytest.mark.parametrize("text", ["Give it once more", "En cuanto a la glicemia, controlar HGT"])
def test_once_as_one_time_and_en_cuanto_a_are_not_conditions(text):
    assert ("conditional", None) not in kept(text)


def test_once_as_one_time_leaves_the_condition_to_its_own_if():
    text = "Give fluids once and reassess if BP drops"
    assert kinds(text) == ["fluid"]
    assert [detail["text"] for detail in parse_family_actions(text)["future_details"]] == ["reassess if bp drops"]


@pytest.mark.parametrize("text", [
    "Once MAP is above 65: stop the bolus and run NS at 100 mL/h",
    "Don't take the tourniquet down; if bleeding continues, place a second one proximal to the first.",
    "Si persiste hipotensa pese al volumen, agregar vancomicina 25 mg/kg ev",
    "Once his fingerstick glucose drops below 70, push 50 mL of D50 IV",
])
def test_what_a_condition_leads_to_is_kept_even_when_the_reader_cannot_run_it(text):
    assert ("conditional", None) in kept(text)
    assert not [a for a in read(text) if a["type"] not in {"clarification"}]


@pytest.mark.parametrize("text", ["Check if she is pregnant", "Evaluar si requiere intubación",
                                  "Preguntar si tiene alergias", "Decidir si trombolizo"])
def test_if_after_a_verb_of_finding_out_is_whether(text):
    assert not kept(text)


def test_a_condition_that_qualifies_one_clause_does_not_make_the_sentence_a_plan():
    text = "PA 76/46 FC 140, sangrado arterial muslo - pasar 2 UGR ahora, O neg si no hay tipificada"
    assert ("conditional", None) not in kept(text)


@pytest.mark.parametrize("text", ["Lo doy de alta. Regresar si tiene fiebre.", "Discharge home. Return if fever."])
def test_return_advice_in_a_sentence_of_its_own_is_advice(text):
    assert kinds(text) == ["disposition"]
    assert kept(text) == [("advice", None)]


# --- TD-30: orders without a verb that were lost -------------------------------------------------

@pytest.mark.parametrize("text, service", [
    ("Surgery consult", "surgery"), ("Consult surgery", "surgery"), ("Interconsulta a cirugía", "surgery"),
    ("Llamar a cirugía", "surgery"), ("Cardiology consult", "cardiology"), ("cards consult", "cardiology"),
    ("gen surg consult", "surgery"), ("GI consult re urgent EGD", "gastroenterology"),
    ("IC a urología ahora para desobstrucción", "urology"), ("IC uro", "urology"), ("IC cardio", "cardiology"),
    ("Hemorrhage control: surgery consult", "surgery"), ("Control de hemorragia: interconsulta a cirugía", "surgery"),
    # A surgical subspecialty is asked which specialist, as before.
    ("Vascular surgery consult", None), ("IC cx vascular", None), ("Consult neurosurgery", None),
])
def test_a_consult_written_as_a_noun_is_the_consult(text, service):
    assert read(text) == [{"type": "consult", "service": service}]


@pytest.mark.parametrize("text", [
    "Endoscopía urgente", "EDA urgente", "Urgent upper endoscopy", "Solicitar endoscopía", "Solicito EDA urgente",
    "Endoscopía urgente para control de hemorragia", "urgent scope", "GI scope now", "endoscopía alta ya",
])
def test_an_endoscopy_asked_for_is_the_call_to_gastroenterology(text):
    assert read(text) == [{"type": "consult", "service": "gastroenterology"}]
    assert "hemorrhage_control" not in kinds(text)


@pytest.mark.parametrize("text", [
    "Surgery already saw him in the trauma bay", "La interconsulta a cirugía ya fue respondida", "EDA de ayer normal",
    "Scope done, ulcer clipped", "scope", "Cardiology consult pending", "IC descompensada",
    "Blood cultures pending", "Blood cultures were already drawn in triage", "Hemocultivos y lactato ya tomados",
    "Hemocultivos x2 y urocultivo ya tomados", "Ya tiene 2 VVP gruesas instaladas", "He has 2 large-bore IVs in place",
])
def test_what_has_happened_or_is_pending_orders_nothing(text):
    assert not read(text), read(text)


@pytest.mark.parametrize("text, expected", [
    ("Take blood cultures x2 from two separate sites", ["blood_cultures"]),
    ("Hemocultivos x2", ["blood_cultures"]),
    ("Blood cultures x2, then ceftriaxone 2 g IV and azithromycin 500 mg IV", ["blood_cultures", "ceftriaxone", "azithromycin"]),
    ("Hemocultivos x2 y luego ceftriaxona 2 g ev", ["blood_cultures", "ceftriaxone"]),
    ("Blood cultures and lactate already drawn, give ceftriaxone 2 g IV", ["ceftriaxone"]),
])
def test_cultures_with_their_count_are_asked_for_beside_the_antibiotic(text, expected):
    assert [a.get("diagnostic") or a.get("agent") for a in read(text)] == expected


def test_a_blood_gas_asks_which_one():
    assert [a["message"] for a in read("Take a blood gas")] == ["Specify arterial (ABG) or venous (VBG) blood gases."]


@pytest.mark.parametrize("text", ["2 large-bore IVs (16G)", "2 large-bore IVs", "2 large-bore IVs or IO", "Two 18G IVs",
                                  "Large-bore IV access x2", "2 IVs", "2 VVP gruesas"])
def test_a_line_named_by_its_count_or_bore_is_the_line(text):
    assert read(text) == [{"type": "vascular_access", "operation": "start"}]


@pytest.mark.parametrize("text", ["IV", "Ceftriaxone 2 g IV"])
def test_a_bare_iv_is_still_a_route(text):
    assert "vascular_access" not in kinds(text)


@pytest.mark.parametrize("text", ["RL 500 ml ev", "Pasar RL 500 ml", "bolo de RL 1000 ml", "Mientras tanto RL 500 ml"])
def test_rl_before_a_volume_is_lactated_ringer(text):
    assert [(a["type"], a["fluid_type"]) for a in read(text)] == [("fluid", "lactated Ringer's")]


# --- TD-31: intramuscular adrenaline without a dose ----------------------------------------------

@pytest.mark.parametrize("text", [
    "Epinephrine IM now", "Adrenalina IM ya", "Epi 1:1000 IM stat", "Epi IM stat", "Adrenalina 1 mg/mL IM",
    "IM epi stat", "Administrar adrenalina intramuscular en vasto lateral", "Give IM epi, anterolateral thigh",
    "Epinephrine IM x1, she is barely moving air",
])
def test_an_intramuscular_adrenaline_without_a_dose_is_the_im_order_still_to_be_dosed(text):
    assert read(text) == [{"type": "epinephrine_im", "dose_mg": None, "route": "IM"}]


@pytest.mark.parametrize("text, expected", [
    ("Epinephrine 0.5 mg IM now", {"type": "epinephrine_im", "dose_mg": 0.5, "route": "IM"}),
    ("epi 300 mcg IM x1", {"type": "epinephrine_im", "dose_mg": 0.3, "route": "IM"}),
    ("Start an epinephrine drip", {"type": "epinephrine", "rate": None, "units": None, "operation": "start"}),
    ("epi gtt pls", {"type": "epinephrine", "rate": None, "units": None, "operation": "start"}),
])
def test_a_dosed_im_order_and_an_infusion_read_as_before(text, expected):
    assert read(text) == [expected]


# --- TD-32: what was left of the blood products --------------------------------------------------

@pytest.mark.parametrize("text", ["2 U. GR", "2 U. de GR O neg", "2 U. PRBCs", "transfuse 2 U. PRBC"])
def test_the_point_of_u_is_not_a_full_stop(text):
    assert read(text) == [{"type": "blood", "units": 2.0}]


@pytest.mark.parametrize("text", ["Deactivate MTP", "Stand down the MTP, bleeding is controlled", "Desactivar PTM",
                                  "Suspender PTM, sangrado controlado", "Stop MTP"])
def test_the_protocol_stood_down_is_recorded_and_gives_nothing(text):
    assert not read(text)
    assert kept(text) == [("not_modelled", "massive_transfusion_stop")]
    lines, _ = unexecuted_items.messages(parse_family_actions(text))
    assert lines[0].startswith("Massive transfusion protocol stood down and recorded as your decision")
    assert language.say(lines[0], "es").startswith("Desactivación del protocolo de transfusión masiva registrada")


@pytest.mark.parametrize("text", ["Platelets if count < 50", "Plaquetas si recuento < 50", "plts if < 50k",
                                  "Plaq 1 U c/10 kg si recuento < 50 mil",
                                  "Transfundir plaquetas si el recuento está bajo 50.000"])
def test_platelets_on_a_count_are_a_plan(text):
    assert not read(text)
    assert kept(text) == [("conditional", None)]


@pytest.mark.parametrize("text", ["Type and cross pending", "Pruebas cruzadas en curso",
                                  "T&C already sent, blood bank processing"])
def test_the_state_of_a_crossmatch_is_not_a_new_one(text):
    assert not read(text)


def test_a_crossmatch_asked_for_is_still_one():
    assert read("Type and cross 2 units") == [{"type": "diagnostic", "diagnostic": "crossmatch"}]


@pytest.mark.parametrize("text, minutes", [
    ("Transfundir 2 U GR en 2 horas c/u", 240.0), ("Transfuse 2 U PRBC over 2 h each", 240.0),
    ("2u PRBC over 2h each", 240.0), ("Transfundir 2 U GR, pasar en 2 hrs c/u", 240.0),
    ("Transfundir 2 U GR en 2 h", 120.0), ("Transfundir 2 U GR en 2 horas", 120.0),
])
def test_each_unit_s_time_adds_up(text, minutes):
    assert read(text) == [{"type": "blood", "units": 2.0, "administration_duration_min": minutes}]


# --- KD-05: the discharge said as a clearance ----------------------------------------------------

@pytest.mark.parametrize("text", [
    "OK to discharge home", "Pt OK for discharge, GP follow-up in 48 h", "He's ok to go home",
    "OK for d/c home, PCP f/u in 1 week", "OK para alta", "OK para alta a domicilio, control en CESFAM en 48 h",
    "La paciente está OK para irse a la casa", "Ok alta con indicaciones y signos de alarma",
    "Ok para dar de alta, control con su médico tratante en 1 semana", "Ok para la casa con control con su médico en APS",
    "Glucose 110, OK to discharge home with a snack",
])
def test_ok_to_discharge_is_a_discharge(text):
    assert kinds(text) == ["disposition"]
    assert read(text)[0]["destination"] == "home"


@pytest.mark.parametrize("text", ["He's not OK for discharge yet", "Is she ok to go home?", "Todavía no está OK para alta",
                                  "¿Está OK para alta la paciente?", "Exámenes OK, reevaluar antes del alta"])
def test_a_denied_or_asked_clearance_is_no_discharge(text):
    assert "disposition" not in kinds(text)


@pytest.mark.parametrize("text", [
    "OK to discharge with an EpiPen prescription and allergy clinic follow-up",
    "Discharge home with an EpiPen prescription and allergy clinic follow-up",
    "OK to dc home w/ epipen x2 rx + allergy f/u",
])
def test_a_discharge_with_its_prescription_keeps_the_discharge(text):
    assert kinds(text) == ["disposition"]
    assert ("prescription", "adrenaline_autoinjector") in kept(text)


@pytest.mark.parametrize("text", ["Alta, paracetamol 1 g c/8 h", "Alta a domicilio, prednisona 40 mg c/24 h por 5 días",
                                  "Lo doy de alta con ondansetrón 4 mg c/8 h"])
def test_what_goes_home_with_the_patient_is_a_prescription(text):
    assert kinds(text) == ["disposition"]
    assert [kind for kind, _ in kept(text)] == ["prescription"]


def test_an_admission_s_medicines_are_not_prescriptions():
    assert ("prescription", "other") not in kept("Hospitalizar en sala, ceftriaxona 2 g c/24 h")


# --- the room ------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine():
    return load_engine()


def test_the_room_asks_an_undosed_im_adrenaline_its_dose_in_milligrams(engine):
    state = encounter(engine, "anaphylaxis", "anaphylaxis_29f")["state"]
    result = execute_family_bundle(state, parse_family_actions("Adrenalina IM ya"))
    assert not result["executed"]
    assert result["clarification"].startswith("Specify an intramuscular epinephrine dose")
    assert "mcg/min" not in result["clarification"]


def test_a_plan_on_the_patient_runs_nothing_in_the_room(engine):
    state = encounter(engine, "gi_bleed", "gi_bleed_57m")["state"]
    before = state["sim_time"]
    parsed = parse_family_actions("Cuando la Hb baje de 7, transfundir 2 U GR")
    result = execute_family_bundle(state, parsed)
    assert not result["executed"] and state["sim_time"] == before
    assert [detail["kind"] for detail in parsed["future_details"]] == ["conditional"]


# --- post hoc: what the adversarial review of cycle 8 found -----------------------------------------
# Each was a regression of this cycle against the V2 reader, or a miss inside its own classes. The
# reading asked for is V2's where V2 was right, and the class's where it was not.

@pytest.mark.parametrize("text, now", [
    ("Presyncope when BP drops below 90 on standing, epinephrine 0.5 mg IM now", "epinephrine_im"),
    ("Mareada cuando la PA baja a 80/50, SF 500 ml ev en bolo", "fluid"),
    ("Paciente que cuando se sienta la PA cae a 80/50, SF 500 ml ev", "fluid"),
    ("Symptomatic when glucose drops below 60, D50 25 g IV", "dextrose"),
    ("Give D50 50 mL IV now as he gets confused when his glucose drops", "dextrose"),
    ("When she talks her sats drop to 88%, increase O2 to 4 L NC", "oxygen"),
    ("When I lay her flat she desaturates to 84%, sit her upright and give furosemide 40 mg IV", "diuretic"),
    ("When he stands up his HR increases to 140, give 1 L NS bolus", "fluid"),
    ("When she got to the ED she desaturated to 82%, start NRB at 15 L", "oxygen"),
    ("Cuando lo trasladaron a box empeoró la PA, SF 500 ml ev", "fluid"),
    ("Cuando se le retira el O2 la saturación baja a 85%, mantener O2 por naricera 3 L/min", "oxygen"),
    ("Once again BP low, NS 500 mL bolus", "fluid"),
    ("Give epi 0.5 mg IM once more as BP remains low", "epinephrine_im"),
])
def test_a_when_in_what_the_resident_saw_is_no_condition(text, now):
    assert now in kinds(text)
    assert ("conditional", None) not in kept(text)


@pytest.mark.parametrize("text, now", [
    ("NS 500 mL bolus now then repeat when SBP < 90", "fluid"),
    ("Salbutamol 5 mg NBZ ahora, cuando la sat baje de 92% repetir", "bronchodilator"),
    ("Epinephrine 0.5 mg IM now then again in 5 min when BP still low", "epinephrine_im"),
])
def test_the_order_now_runs_and_its_repeat_on_a_condition_is_the_plan(text, now):
    assert kinds(text) == [now]
    assert kept(text) == [("conditional", None)]


@pytest.mark.parametrize("text", [
    "D50 50 mL IV when FSBG < 60", "Paracetamol 1 g ev cuando T° > 38,5", "Transfuse 1 unit PRBC when Hct < 21",
    "Discharge home when afebrile x 24 h", "Alta cuando esté asintomático y tolere VO",
    "Alta una vez que complete 6 horas de observación", "Intubate when she tires", "Intubar cuando se agote",
    "Intubate once she becomes drowsy", "Once hemostasis achieved, stand down MTP",
    "Cuando se controle el sangrado, desactivar PTM", "ok para alta cuando tolere VO", "OK for d/c home once afebrile",
])
def test_a_condition_the_class_missed_is_a_plan(text):
    assert not read(text), read(text)
    assert kept(text) == [("conditional", None)]


def test_the_account_of_the_ambulance_stays_one_plan():
    text = "En el SAMU le dieron atropina 0,5 mg ev, si no respondía iban a iniciar dopamina"
    assert not read(text)
    assert kept(text) == [("conditional", None)]


@pytest.mark.parametrize("text, expected", [
    ("Hemocultivos tomados y ceftriaxona 2 g ev", ["antibiotics"]),
    ("Blood cultures drawn then give ceftriaxone 2 g IV", ["antibiotics"]),
    ("Blood cultures pending - start ceftriaxone 2 g IV", ["antibiotics"]),
    ("Hemocultivos y urocultivo tomados antes del antibiótico: ceftriaxona 2 g ev", ["antibiotics"]),
    ("Hb y pruebas cruzadas pendientes y transfundir 2 U GR O neg ahora", ["blood"]),
    ("Lactate pending so give 30 mL/kg LR", ["fluid"]),
])
def test_a_study_s_state_takes_nothing_after_it(text, expected):
    assert kinds(text) == expected


def test_a_urine_culture_is_asked_for_beside_the_rest():
    actions = read("Hemocultivos x2, urocultivo y ceftriaxona 2 g ev")
    assert [action.get("diagnostic") or action["type"] for action in actions] == [
        "blood_cultures", "urine_culture", "antibiotics"]


@pytest.mark.parametrize("text", [
    "OK to d/c IV fluids", "Ok to dc O2", "OK to d/c the epi drip", "OK to dc norepi", "ok to dc tele",
    "OK to dc home after 4 h observation", "Ok to discharge, but first observe 4 hours", "ok para alta mañana",
    "OK for discharge tomorrow AM", "OK to discharge: no", "OK to dc home - not yet", "Ok para alta dosis de salbutamol",
    "Per surgery, OK to discharge", "OK to discharge from ortho standpoint",
])
def test_a_clearance_that_is_not_a_discharge_now(text):
    assert "disposition" not in kinds(text)


@pytest.mark.parametrize("text", [
    "Epi 0.5 mg IM given by EMS", "Epi 0.3 mg IM 20 min ago", "Epi 0.3 mg IM x1 at home", "Epi 0.5 mg IM ya administrada",
    "Epi IM at 14:05", "Epi IM x1 at school", "Epi 0.3 IM prehospital", "Epi IM q5-15 min PRN",
])
def test_an_earlier_or_someone_else_s_epi_is_never_given(text):
    assert not {"epinephrine_im", "epinephrine"} & set(kinds(text))


@pytest.mark.parametrize("text, given", [
    ("Epi 8/10 pain, give morphine 4 mg IV", "opioid_analgesia"),
    ("EPI 1ria vs pielonefritis, ceftriaxona 2 g ev", "antibiotics"),
])
def test_epi_before_a_score_or_a_diagnosis_is_not_adrenaline(text, given):
    assert kinds(text) == [given]


@pytest.mark.parametrize("text, service", [
    ("Consult urology for decompression since she is already septic", "urology"),
    ("Consult ICU for refractory shock already on norepi 0.3 mcg/kg/min", "ICU"),
    ("Llamar nuevamente a cirugía que ya lo vio", "surgery"),
])
def test_a_consult_asked_for_is_one_whatever_else_is_already_so(text, service):
    assert read(text) == [{"type": "consult", "service": service}]


@pytest.mark.parametrize("text", [
    "Surgery consult not needed at this time", "Surgery consult declined by patient", "Surgery consult deferred",
    "Surgery consult tomorrow", "GI consult in AM", "Surgery consult?", "Surgery consult saw pt",
    "Surgery consult appreciated", "Surgery consult - no operative intervention",
    "IC a cirugía: sin indicación quirúrgica por ahora", "IC a cirugía pendiente", "Nutrition consult",
])
def test_a_consult_written_with_its_state_is_not_asked_for(text):
    assert "consult" not in kinds(text)


@pytest.mark.parametrize("text", ["Discharge home with allergy referral", "Alta con interconsulta a inmunología",
                                  "Discharge home with pulmonology referral in 2 weeks"])
def test_a_referral_after_a_discharge_is_the_patient_s_plan(text):
    assert kinds(text) == ["disposition"]
    assert ("advice", None) in kept(text)


@pytest.mark.parametrize("text, given", [
    ("IC con FE preservada descompensada: furosemida 40 mg ev", ["diuretic"]),
    ("Social work consult, ceftriaxone 2 g IV", ["antibiotics"]),
])
def test_heart_failure_and_a_non_clinical_consult_hold_nothing(text, given):
    assert kinds(text) == given


def test_blood_cultures_written_cx_are_not_surgery():
    assert read("Consult ID re blood cx") == [{"type": "consult", "service": None}]


@pytest.mark.parametrize("text", ["Antecedentes: cirrosis, EDA por várices hace 1 año",
                                  "PMH: cirrhosis, EGD for banding last year", "EDA por gastro: ligadura de várices"])
def test_an_endoscopy_done_calls_no_one(text):
    assert "consult" not in kinds(text)


@pytest.mark.parametrize("text", [
    "Furosemida 40 mg ev con control de diuresis en 2 h", "SF 500 ml ev en bolo con control de PA en 1 h",
    "Salbutamol 5 mg NBZ con control de PEF en 1 h", "Noradrenalina 0,1 mcg/kg/min ev con control de PAM en 1 h",
])
def test_when_the_patient_is_checked_is_not_how_long_the_order_runs(text):
    actions = read(text)
    assert len(actions) == 1 and "administration_duration_min" not in actions[0], actions


@pytest.mark.parametrize("text", ["Transfuse PRBC 2 U. Platelets if count < 50.",
                                  "Transfundir GR 2 U. Plaquetas si recuento < 50 mil."])
def test_a_point_after_the_count_of_named_red_cells_ends_the_sentence(text):
    assert read(text) == [{"type": "blood", "units": 2.0}]
    assert kept(text) == [("conditional", None)]


@pytest.mark.parametrize("text", ["Stop MTP?", "Can we stop MTP now?", "We should stop MTP soon",
                                  "Once we stop MTP, recheck labs", "Cuando termine el PTM, controlar calcio iónico"])
def test_a_stand_down_asked_or_as_a_time_is_not_recorded(text):
    assert ("not_modelled", "massive_transfusion_stop") not in kept(text)


@pytest.mark.parametrize("text", ["Type and cross 4 units to be ready for the OR", "Type and cross 2 units awaiting OR",
                                  "Type and cross 4 units sent stat"])
def test_a_crossmatch_with_its_purpose_is_asked_for(text):
    assert read(text) == [{"type": "diagnostic", "diagnostic": "crossmatch"}]


def test_a_dose_given_before_the_patient_leaves_is_no_prescription():
    assert ("prescription", "other") not in kept("Alta a domicilio, salbutamol 4 puff ahora antes de irse")
    assert ("prescription", "other") not in kept("Discharge home tomorrow, tonight ceftriaxone 1 g IV q24h")


def test_a_consult_and_a_repeated_check_are_not_advice():
    assert kept("Consultar cirugía si persiste el sangrado") == [("conditional", None)]
    assert ("advice", None) not in kept("Volver a controlar creatinina si oliguria")


def test_the_autoinjector_goes_home_and_one_given_now_is_given():
    assert kinds("Ok para alta con adrenalina autoinyectable") == ["disposition"]
    assert ("prescription", "adrenaline_autoinjector") in kept("Ok para alta con adrenalina autoinyectable")
    assert kinds("Adrenalina autoinyectable 0,3 mg IM ahora") == ["epinephrine_im"]


def test_units_run_one_after_another_longer_than_the_simulator_runs_are_asked(engine):
    state = encounter(engine, "gi_bleed", "gi_bleed_57m")["state"]
    result = execute_family_bundle(state, parse_family_actions("2 U GR en 2 horas c/u"))
    assert not result["executed"]
    assert result["clarification"].startswith(
        "2 units over 4 h in all: this simulator runs a transfusion over at most 120 min")
    assert language.say(result["clarification"], "es").startswith("2 unidades en 4 h en total")


def test_a_volume_over_hours_is_asked_as_a_fluid_rate_is(engine):
    state = encounter(engine, "gi_bleed", "gi_bleed_57m")["state"]
    result = execute_family_bundle(state, parse_family_actions("SF 1000 ml ev durante 8 h"))
    assert result["clarification"].startswith("1000 mL over 8 h:")
    assert language.say(result["clarification"], "es").startswith("1000 mL en 8 h:")


def test_a_urine_culture_is_recorded_with_no_result(engine):
    state = encounter(engine, "renal_colic", "obstructive_pyelonephritis_58f")["state"]
    result = execute_family_bundle(state, parse_family_actions("Hemocultivos x2, urocultivo y ceftriaxona 2 g ev"))
    assert result["executed"]
    labels = [str(summary.get("label") or "") for summary in result["action_summaries"]]
    assert any(label.startswith("Study requested; not modelled in this version of the simulator: Urine culture")
               for label in labels), labels
    assert language.say("Urine culture", "es") == "Urocultivo"
