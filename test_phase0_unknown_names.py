"""Phase 0 closure: an order whose name no vocabulary knows is never gone.

Pre-pilot measurement safety, closure pass of 2026-10-06. Written the way an order is written --
a name alone in a list or a sentence of names, with a dose, a route or a schedule and no verb,
after "Necesitamos", where the order's own name goes after an order verb, or after the problem
it treats ("Sepsis, ceftriaxone.") -- a name no vocabulary of the simulator knew vanished: the
reader returned nothing and the ledger saw nothing ("Zyvox.", "- Plasmaféresis", "Zyvox IV"),
and a known name in the same sentence went with it ("Zyvox and ceftriaxone."). The ledger now
accounts for it as not understood, after the reader and without changing it (Reader V3 stays
frozen). A note stays a note: a diagnosis, a finding, a state, a label, the history, a result,
a negation, a question, reasoning, a report of what others did. A false alarm only asks the
resident to write the order again: it runs nothing and counts for nothing. Where the words could
as well be a note, a description or a stray verb ("Sepsis: zyvox.", "Give ceftriaxone with
zyvox.", "Suctioning."), nothing is said to the resident, and the words are kept with the turn
so that no omission is read against them (TD-69).

The names below are in none of the simulator's vocabularies (checked by the first test).
"""
import pytest

import order_ledger
import order_pipeline
import pilot_acceptance as acceptance
import rubric_screening as screening
import time_semantics
from family_parser import parse_family_actions
from test_phase0_guards import FLUID, _entry, _order, _record, _row

NOVEL = ("zyvox", "dravolimab", "quentrazol", "fexoprazina", "tygacil", "plasmapheresis", "plasmaferesis", "ecmo",
         "bronchoscopy", "thoracotomy", "toracotomia", "hemodialysis", "hemodialisis")


def _flags(text):
    parsed = time_semantics.apply(text, parse_family_actions(text))
    order_pipeline.apply_safe_defaults(parsed, text)
    found = order_ledger.coverage(text, parsed)
    return [item["text"] for item in found["unaccounted"] + found["held"]], parsed


def _turn(text):
    parsed = time_semantics.apply(text, parse_family_actions(text))
    return order_pipeline.open_turn(text, parsed, submission_id="s", entry_point="free_text", minute=0)


def test_the_names_used_here_are_in_no_vocabulary():
    for name in NOVEL:
        assert not [entry["key"] for entry in order_ledger.lexicon() if entry["pattern"].search(name)], name
        assert order_ledger._word_kind(name) == "name", name


@pytest.mark.parametrize("text, missed", [
    # Alone, in a list, or in a sentence of names.
    ("Zyvox.", "Zyvox"),
    ("- Zyvox", "Zyvox"),
    ("Plan:\n- Dravolimab\n- Plasmapheresis", "Plasmapheresis"),
    ("1. Quentrazol\n2. Ceftriaxone 2 g IV", "Quentrazol"),
    ("ECMO.", "ECMO"),
    ("Bronchoscopy.", "Bronchoscopy"),
    ("Hemodialysis.", "Hemodialysis"),
    ("Plasmaféresis.", "Plasmaféresis"),
    # With "now", "urgente", a need or a wish.
    ("Zyvox now.", "Zyvox now"),
    ("Urgent plasmapheresis.", "Urgent plasmapheresis"),
    ("VA-ECMO now.", "VA-ECMO now"),
    ("Thoracotomy now.", "Thoracotomy now"),
    ("We need zyvox.", "zyvox"),
    ("Zyvox ahora.", "Zyvox ahora"),
    ("Plasmaféresis urgente.", "Plasmaféresis urgente"),
    ("Toracotomía ahora.", "Toracotomía ahora"),
    ("Hemodiálisis de urgencia.", "Hemodiálisis de urgencia"),
    ("Necesitamos zyvox.", "zyvox"),
    ("Quiero fexoprazina.", "fexoprazina"),
    # With a route or a schedule and no verb.
    ("Zyvox IV.", "Zyvox IV"),
    ("Zyvox EV.", "Zyvox EV"),
    ("Tygacil q12h.", "Tygacil q12h"),
    ("Zyvox cada 12 horas.", "Zyvox cada 12 horas"),
    # Where the order's own name goes, after an order verb.
    ("Give zyvox in 100 mL saline.", "zyvox"),
    ("Pasar zyvox en 100 mL de suero fisiológico.", "zyvox"),
    # After the problem it treats.
    ("Sepsis, zyvox.", "zyvox"),
    ("Due to sepsis, zyvox.", "zyvox"),
    ("Creo que es sepsis, zyvox.", "zyvox"),
    # A word that names a diagnosis as well as an order, alone ("Taponamiento.": wound packing
    # in the limb bleed, or a tamponade): said as not understood, never taken for a note.
    ("Taponamiento.", "Taponamiento"),
])
def test_an_order_no_vocabulary_names_is_not_understood_never_gone(text, missed):
    flagged, _ = _flags(text)
    assert missed in flagged, flagged


def test_an_order_the_reader_read_is_not_also_said_not_understood():
    """«Hacer taponamiento» ran as haemorrhage control and was also said "not understood"."""
    turn = _turn("Hacer taponamiento.")
    assert [(order["class"], order["span"]) for order in turn["orders"]] == [
        ("hemorrhage_control", "Hacer taponamiento")]


@pytest.mark.parametrize("text, missed", [
    ("Zyvox and ceftriaxone.", ["ceftriaxone", "Zyvox"]),
    ("Zyvox with ceftriaxone.", ["ceftriaxone", "Zyvox"]),
    ("Aspirin, zyvox, ECG.", ["Aspirin", "zyvox"]),
    ("Aspirina, zyvox, ECG.", ["Aspirina", "zyvox"]),
    # The same shape with a known name had vanished too.
    ("Sepsis, ceftriaxone.", ["ceftriaxone"]),
    ("Due to sepsis, ceftriaxone.", ["ceftriaxone"]),
    ("Creo que es sepsis, ceftriaxona.", ["ceftriaxona"]),
    ("Shock séptico, ceftriaxona y zyvox.", ["ceftriaxona", "zyvox"]),
])
def test_a_known_name_beside_an_unknown_one_is_not_lost_with_it(text, missed):
    flagged, _ = _flags(text)
    assert sorted(flagged) == sorted(missed), flagged


@pytest.mark.parametrize("text", [
    "Give zyvox 600 mg IV.", "Zyvox 600 mg IV.", "Start zyvox.", "Dravolimab 200 mg IV over 30 minutes.",
    "Iniciar zyvox 600 mg EV.", "Tigeciclina 100 mg EV cada 12 horas.", "Dar zyvox y ceftriaxona.",
])
def test_a_name_the_reader_already_asks_about_is_the_reader_s_order_not_a_second_one(text):
    flagged, parsed = _flags(text)
    assert flagged == [] and any(action.get("type") == "clarification" for action in parsed["actions"]), parsed


@pytest.mark.parametrize("text", [
    # Diagnoses, findings and states.
    "Sepsis.", "Septic shock.", "Neumonía.", "Estable.", "Improving.", "Febrile, hypotensive, tachycardic.",
    "Víscera perforada.", "ICC descompensada.", "Extremidades: frías.", "Diaforesis: marcada.",
    "Debito urinario 15 mL/h.", "The IV is patent.", "PEF 85% after nebs.",
    # Reasoning and intentions that are not orders.
    "Tratar la infección.", "Prioridad: llenar antes de apretar.", "I think zyvox would cover it.",
    "Espero que el zyvox ayude.", "Creo que es ansiedad, porque está taquicárdica y nerviosa.",
    # History, reports, results, allergies, negations and questions.
    "Medicamentos habituales: metformina.", "On zyvox at home.", "Zyvox was given by EMS.",
    "Received zyvox in the ambulance.", "Ya recibió zyvox.", "Lleva 2 U de GR.", "Cardiología sugiere alta.",
    "Pruebas cruzadas en curso.", "β-hCG negativa.", "Alergia a zyvox.", "Allergic to penicillin, ceftriaxone.",
    "No zyvox.", "Zyvox?", "Zyvox pending.",
    # A verb the order-verb pattern does not take is not the name of an order.
    "Repito morfina 4 mg ev.", "Ventila con ambu.", "Nebulizar salbutamol 5 mg.", "Remove the humeral IO.",
    "Indica ibuprofeno 600 mg VO.",
])
def test_a_note_a_report_or_reasoning_is_not_made_an_order(text):
    flagged, _ = _flags(text)
    assert flagged == [], flagged


def test_a_flagged_name_runs_nothing_and_is_said_not_understood():
    turn = _turn("Zyvox IV.")
    [order] = turn["orders"]
    assert (order["class"], order["fate"], order["span"]) == ("unrecognized", "UNRECOGNIZED", "Zyvox IV")
    assert order["modelled_effect"] is False and order["executed_at_min"] is None
    assert order["receipt"].startswith('Not understood: "Zyvox IV". Nothing was given or done for it.')
    assert order_pipeline.check(turn) == []


def test_the_course_is_the_one_it_would_be_without_the_unknown_order():
    plain = acceptance.Encounter("pneumonia_46f")
    plain.order("Reassess in 10 minutes.")
    named = acceptance.Encounter("pneumonia_46f")
    entry = named.order("Zyvox IV. Plasmapheresis now. Reassess in 10 minutes.")
    assert sorted((order["class"], order["fate"], order["span"]) for order in entry["orders"]) == [
        ("reassessment", "EXECUTED", "Reassess in 10 minutes"),
        ("unrecognized", "UNRECOGNIZED", "Plasmapheresis now"),
        ("unrecognized", "UNRECOGNIZED", "Zyvox IV")]
    assert named.minute == plain.minute == 10
    assert named.state["observable"] == plain.state["observable"]
    assert named.state["family_state"] == plain.state["family_state"]


def test_a_flagged_name_is_never_read_as_an_omission():
    """Rule A (0I): an order the simulator did not understand takes the omission it may be away."""
    unread = [order for order in _turn("Necesitamos zyvox.")["orders"] if order["fate"] == "UNRECOGNIZED"]
    assert [order["span"] for order in unread] == ["zyvox"]
    record = _record(_entry(0, summaries=[FLUID], orders=[_order("s:0", "fluid", "EXECUTED", 0, 0, "1 L LR")] + [
        _order(order["order_id"], order["class"], order["fate"], 0, span=order["span"]) for order in unread]),
        _entry(70, response=70))
    row = _row(record, "pneumonia_46f", "pneumonia_no_antibiotic")
    assert row["status"] == "reading", row
    assert "not understood by the simulator's reader" in " ".join(fact["en"] for fact in row["facts"])
    assert screening.may_support_negative_feedback(
        {"preventability": "PREVENTABLE", "minute": 30},
        withheld=[{"status": "UNRECOGNIZED", "minute": 0}]) is False


def _silent_guard(turn):
    silent = [order for order in turn["orders"] if order["class"] == "unread_words"]
    record = _record(_entry(0, summaries=[FLUID], orders=[_order("s:0", "fluid", "EXECUTED", 0, 0, "1 L LR")] + [
        _order(order["order_id"], order["class"], order["fate"], 0, span=order["span"]) for order in silent]),
        _entry(70, response=70))
    return silent, _row(record, "pneumonia_46f", "pneumonia_no_antibiotic")["status"]


@pytest.mark.parametrize("text, kept", [
    # Shapes where a known name is not taken for an order either: a label, a condition, a bare
    # number. Nothing is said to the resident; the words are kept with the turn.
    ("Sepsis: zyvox.", "Sepsis: zyvox"),
    ("If hypotensive, zyvox.", "zyvox"),
    ("Zyvox 600.", "Zyvox 600"),
])
def test_names_where_a_note_could_also_be_are_kept_silently_and_guard_the_omission(text, kept):
    turn = _turn(text)
    silent, status = _silent_guard(turn)
    assert [order["span"] for order in silent] == [kept]
    assert silent[0]["fate"] == "UNRECOGNIZED" and silent[0]["receipt"] is None
    assert order_pipeline.receipt_lines(turn) == [] and order_pipeline.check(turn) == []
    assert status == "reading"


@pytest.mark.parametrize("text, kept", [
    # After a known name the reader read, joined with "with" or "con": a second drug, or a word
    # that describes the first ("with caution"). The known order runs as read (TD-69 a).
    ("Give ceftriaxone with zyvox.", "zyvox"),
    ("Ceftriaxone 2 g IV with zyvox.", "zyvox"),
    ("Ceftriaxona 2 g EV con zyvox.", "zyvox"),
    # A procedure or a drug spelt like a verb or a participle, alone (TD-69 b).
    ("Suctioning.", "Suctioning"),
    ("- Proning", "Proning"),
    ("1. Splinting", "Splinting"),
    ("Lavado.", "Lavado"),
    ("Entablillado.", "Entablillado"),
    ("Suboxone.", "Suboxone"),
    ("Activase.", "Activase"),
])
def test_names_the_coverage_cannot_call_an_order_are_kept_silently_and_guard_the_omission(text, kept):
    turn = _turn(text)
    silent, status = _silent_guard(turn)
    assert [order["span"] for order in silent] == [kept]
    assert silent[0]["fate"] == "UNRECOGNIZED" and silent[0]["receipt"] is None
    assert not [order for order in turn["orders"] if order["class"] == "unrecognized"], turn["orders"]
    assert status == "reading"


@pytest.mark.parametrize("text", [
    "Improving.", "Stable.", "Previously.", "Sedated.", "Troponin elevated, ECG with ST depression.",
    "Quiero frenar la agregación.", "Presión y el llenado capilar.", "Give ceftriaxone with metronidazole.",
])
def test_a_note_a_state_or_a_known_name_is_not_kept_as_unread_words(text):
    assert not [order for order in _turn(text)["orders"] if order["class"] == "unread_words"]
