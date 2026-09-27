"""The reasoning the Management Trace attributes to a resident is what they wrote.

DF-7 (critical, approved 2026-09-27). The EN/ES measurement of the rehearsal
corpus (docs/MEDICION_RECONOCIMIENTO_ORDENES.md) found that the extraction of
the four categories changed or misattributed the resident's words. Each test
here pins one class of that defect with sentences written for the test, not
taken from the corpus, so that the fix is a class and not a phrase (§57).
"""
import pytest

from family_parser import parse_family_actions
from test_curriculum_trajectories import load_engine


@pytest.fixture(scope="module")
def extract():
    return load_engine()["extract_explicit_reasoning"]


def _words(reasoning):
    return " ".join(value for key, value in reasoning.items()
                    if isinstance(value, str) and key != "slot_provenance")


# --- "im" is the intramuscular route, not "I'm" --------------------------------

@pytest.mark.parametrize("text", [
    "Pongo ceftriaxona 1 g im. Reevalúo en 10 minutos la fiebre.",
    "Give ketorolac 30 mg IM starting now, reassess pain in 30 minutes.",
    "Administro haloperidol 5 mg i.m. y reevalúo en 20 minutos la agitación.",
])
def test_the_intramuscular_route_is_never_rewritten_as_i_am(extract, text):
    assert "I'm" not in _words(extract(text))


def test_a_clause_opened_by_im_and_a_participle_is_still_the_pronoun(extract):
    reasoning = extract("Give diltiazem 10 mg IV. Im addressing the rate first, because it limits filling.")
    assert reasoning.get("management_priority") == "the rate"


# --- a word ending in "so" is not a connector ---------------------------------

@pytest.mark.parametrize("text, model", [
    ("Creo que es una sepsis con posible compromiso renal, porque el lactato es 4.",
     "una sepsis con posible compromiso renal"),
    ("I think this is sepsis and also dehydration, so I will give fluids.",
     "sepsis and also dehydration"),
    ("Creo que es un caso de hipoglicemia por exceso de insulina, así que doy glucosa.",
     "un caso de hipoglicemia por exceso de insulina"),
])
def test_a_word_ending_in_so_is_not_cut_as_a_connector(extract, text, model):
    assert extract(text).get("problem_representation") == model


# --- an order is never the working model ----------------------------------------

@pytest.mark.parametrize("text", [
    "Doy adrenalina 1 mg im.",
    "Adrenaline 1 mg IV now.",
    "Inicio noradrenalina a 0.1 mcg/kg/min y reevalúo PAM en 10 minutos.",
])
def test_an_order_alone_states_no_working_model(extract, text):
    reasoning = extract(text)
    assert "problem_representation" not in reasoning
    assert "rationale" not in reasoning


def test_a_model_stops_before_the_order_that_follows_it(extract):
    reasoning = extract("Creo que es anafilaxia, doy adrenalina 0.5 mg im y SF 1000 ml.")
    assert reasoning.get("problem_representation") == "anafilaxia"


@pytest.mark.parametrize("text, reason", [
    ("Consult surgery for laparotomy because this is a perforated viscus.", "a perforated viscus"),
    ("Llamo a cirugía para laparotomía porque es una víscera perforada.", "una víscera perforada"),
])
def test_the_reason_given_for_an_order_is_its_rationale_in_both_languages(extract, text, reason):
    reasoning = extract(text)
    assert (reasoning.get("problem_representation") or reasoning.get("rationale")) == reason


@pytest.mark.parametrize("text, model", [
    ("Anafilaxia con broncoespasmo, adrenalina 0.5 mg im, espero que ceda el broncoespasmo, "
     "reevalúo la saturación en 5 minutos", "Anafilaxia con broncoespasmo"),
    ("Anaphylaxis with bronchospasm, adrenaline 0.5 mg IM, I expect the wheeze to settle, "
     "recheck the saturation in 5 minutes", "Anaphylaxis with bronchospasm"),
])
def test_the_findings_written_before_the_order_are_the_model_without_the_order(extract, text, model):
    # Shorthand runs the finding, the order, the expectation and the
    # reassessment together; each keeps its own slot. The whole sentence,
    # order included, used to be recorded as the model.
    reasoning = extract(text)
    assert reasoning.get("problem_representation") == model
    assert reasoning.get("expected_effect") and reasoning.get("reassessment_target")


@pytest.mark.parametrize("text, model", [
    ("Given the hypotension I will give 500 mL of saline, the aim is to raise the MAP, "
     "recheck MAP in 15 minutes", "Given the hypotension"),
    ("Como está hipotenso le voy a pasar 500 ml de suero fisiológico, busco subir la PAM, "
     "reevalúo PAM en 15 minutos", "Como está hipotenso"),
    ("Dada la hipoxemia le voy a poner VNI, la idea es bajar el trabajo respiratorio, "
     "y reviso saturacion y FR en 10 minutos", "Dada la hipoxemia"),
])
def test_a_reason_before_a_declared_intention_ends_where_the_reader_starts_the_order(extract, text, model):
    assert extract(text).get("problem_representation") == model


def test_the_adrenal_crisis_is_still_a_finding_and_adrenaline_is_not(extract):
    assert extract("Paciente con crisis suprarrenal probable. Hidrocortisona 100 mg ev.").get(
        "problem_representation") == "Paciente con crisis suprarrenal probable"
    assert "problem_representation" not in extract("Adrenalina 0.5 mg im ahora.")


# --- the same statement makes the same kind of model in either language ----------

@pytest.mark.parametrize("english, spanish", [
    ("He is on a beta-blocker, which is why he does not respond. Give glucagon 1 mg IV.",
     "Está con betabloqueo, por eso no responde. Doy glucagón 1 mg ev."),
    ("He takes an SSRI and tramadol, so this is serotonin toxicity. Give cyproheptadine 12 mg PO.",
     "Toma un ISRS y tramadol, así que esto es toxicidad serotoninérgica. Doy ciproheptadina 12 mg vo."),
])
def test_a_consequence_keeps_its_stated_cause_in_both_languages(extract, english, spanish):
    en = extract(english).get("problem_representation") or ""
    es = extract(spanish).get("problem_representation") or ""
    assert "which is why" in en or "so this is" in en, en
    assert "por eso" in es or "así que" in es, es


@pytest.mark.parametrize("english, spanish", [
    ("The gas shows a normal PaCO2 with marked effort: this is exhaustion and impending ventilatory failure. "
     "Prepare for intubation.",
     "La gasometría muestra PaCO2 normal con esfuerzo marcado: es agotamiento y falla ventilatoria inminente. "
     "Preparo intubación."),
    ("Afebrile and the urinalysis shows no infection. Discharge home.",
     "Afebril y la orina no muestra infección. Lo doy de alta."),
])
def test_the_same_finding_makes_a_working_model_in_both_languages(extract, english, spanish):
    assert extract(english).get("problem_representation")
    assert extract(spanish).get("problem_representation")


@pytest.mark.parametrize("english, spanish", [
    ("I think this is a pneumothorax, because breath sounds are absent on the left and the trachea is shifted. "
     "Needle decompression now.",
     "Creo que es un neumotórax, porque no hay murmullo a izquierda y la tráquea está desviada. "
     "Descomprimo con aguja ahora."),
    # English "since" is also temporal ("hypotensive since arrival") and is not
    # read as a reason; "ya que" only is.
    ("I think it is hyperkalemia, because the T waves are peaked and he missed dialysis. Give calcium gluconate.",
     "Creo que es una hiperkalemia, ya que las T están picudas y no se dializó. Doy gluconato de calcio."),
])
def test_the_stated_reason_is_the_rationale_in_both_languages(extract, english, spanish):
    en, es = extract(english), extract(spanish)
    assert en.get("problem_representation") and es.get("problem_representation")
    assert en.get("rationale") and es.get("rationale"), (en, es)


# --- an expectation is what the resident expected, and only that ----------------

@pytest.mark.parametrize("text, effect", [
    ("Give 500 mL of saline to raise the MAP and I will recheck it in 15 minutes", "raise the MAP"),
    ("Pongo 500 ml de suero fisiológico para subir la PAM y reevalúo en 15 minutos", "subir la PAM"),
    ("Le doy furosemida 40 mg ev para bajar la congestión, espero que mejore la saturación y "
     "reevalúo la saturación en 30 minutos", "bajar la congestión"),
])
def test_a_purpose_ends_where_the_next_category_begins(extract, text, effect):
    assert extract(text).get("expected_effect") == effect


@pytest.mark.parametrize("text, effect", [
    ("Because of the poor perfusion I will give 500 mL of Ringer's lactate to raise the blood pressure, "
     "recheck the MAP in 15 minutes.", "raise the blood pressure"),
    ("Porque está mal perfundido le voy a pasar 500 ml de Ringer lactato para subir la presión, "
     "reevalúo la PAM en 15 minutos", "subir la presión"),
])
def test_the_order_inside_a_reason_does_not_take_the_expectation_with_it(extract, text, effect):
    # The English record lost the expectation to a rationale that still held
    # the order; the Spanish one kept it.
    reasoning = extract(text)
    assert reasoning.get("expected_effect") == effect
    assert "500" not in (reasoning.get("rationale") or "") + (reasoning.get("problem_representation") or "")


# --- the order layer: what a discharge sends the patient home with ----------------

def test_an_english_follow_up_named_by_its_service_is_kept_with_the_discharge():
    # As a list item after the discharge, the way "control urologico" is kept.
    # A follow-up attached by "with"/"con" to the discharge itself is lost in
    # both languages; that is recorded apart (docs/COLA_DECISIONES_AI_ADVISOR.md).
    parsed = parse_family_actions("Discharge her with analgesia, cardiology follow-up and return precautions "
                                  "for chest pain, dyspnea or syncope.")
    assert [a["type"] for a in parsed["actions"]] == ["disposition"]
    assert "cardiology follow-up" in parsed["recognized_future_actions"]
    assert "return precautions for chest pain, dyspnea or syncope" in parsed["recognized_future_actions"]


def test_spanish_warning_signs_keep_their_whole_list():
    parsed = parse_family_actions("La doy de alta con control en policlínico y signos de alarma: "
                                  "fiebre, vómitos o dolor.")
    assert any(item.startswith("signos de alarma") and "dolor" in item
               for item in parsed["recognized_future_actions"])
