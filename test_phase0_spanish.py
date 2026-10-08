"""Phase 0 closure (F0-11): the room's new sentences in Spanish, whole, with the resident's words as written.

Pre-pilot measurement safety, closure pass of 2026-10-06. The pilot runs in Spanish as well as
in English (the resident chooses, and the language stays fixed during the encounter), so every
sentence Phase 0 added to the room is said in Spanish: the order ledger's receipts, a partly
carried-out order, the look at the bedside, a wait an event cut short, the arrest, the limit of
one step, a submission stopped part way, an order written after an answer. Each is said whole,
before the word rules can say it by halves, and the resident's own words quoted in it are kept
exactly as written («Stop the infusion», never «Stop infusión de the»). English is unchanged.
Fates, codes and other fields the room does not show are not translated. The wording awaits the
faculty's signature (``docs/revision/F0_11_FRASES_ES.md``), as R-4's did.
"""
import pytest

import anaphylaxis_reaction
import language
import observation_consistency
import order_ledger
import order_pipeline
import submission_guard
import time_semantics
import tools_engine_spanish
from family_parser import parse_family_actions


def _turn(text, entry_point="free_text"):
    parsed = time_semantics.apply(text, parse_family_actions(text)) if entry_point == "free_text" else {"actions": []}
    return order_pipeline.open_turn(text, parsed, submission_id="s", entry_point=entry_point, minute=0)


def _receipt(text, entry_point="free_text"):
    return next(order["receipt"] for order in _turn(text, entry_point)["orders"] if order.get("receipt"))


CASES = {
    "unrecognized": (
        lambda: _receipt("Zyvox IV."),
        "No se entendió: «Zyvox IV». No se administró ni se hizo nada por ello. Escríbelo de nuevo con otras "
        "palabras si aún lo quieres."),
    "unrecognized_quoted_words_kept": (
        lambda: order_ledger.unrecognized_receipt("Stop the infusion"),
        "No se entendió: «Stop the infusion». No se administró ni se hizo nada por ello. Escríbelo de nuevo con "
        "otras palabras si aún lo quieres."),
    "recorded_not_modelled": (
        lambda: ('Recorded as your decision, not given: "Stop the infusion". This simulator does not model a '
                 "response to it in this case, so nothing changed."),
        "Registrado como tu decisión, no administrado: «Stop the infusion». Este simulador no modela una "
        "respuesta a ello en este caso, así que nada cambió."),
    "immediate_reassessment": (
        lambda: time_semantics.update_lead({"reassess_delay": 0, "elapsed_min": 2},
                                           time_semantics.apply("Reassess now.", parse_family_actions("Reassess now.")),
                                           []) + "BP 100/60 mmHg.",
        "Al reevaluar en la cabecera, 2 minutos después, PA 100/60 mmHg."),
    "immediate_look_after_an_order": (
        lambda: time_semantics.immediate_lead(["Normal saline 1000 mL"], 1) + "BP 100/60 mmHg.",
        "Suero fisiológico 1000 mL. Al reevaluar en la cabecera, 1 minuto después de la orden, PA 100/60 mmHg."),
    "interrupted_wait": (
        lambda: time_semantics.update_lead(
            {"interrupted": {"after_min": 7, "requested_until_min": 15, "minute": 7,
                             "label": "systolic pressure 62 mmHg and falling"}}, {}, ["Normal saline 1000 mL"])
        + "BP 62/30 mmHg.",
        "Administrado: Suero fisiológico 1000 mL. La espera se interrumpió tras 7 min de los 15 que pediste, en el "
        "minuto 7: presión sistólica de 62 mmHg y en descenso. Ahora, PA 62/30 mmHg."),
    "terminal_arrest": (
        lambda: observation_consistency.arrest_message(12),
        "Se produjo un paro cardíaco en el minuto 12. El manejo de la reanimación no está modelado en este piloto. "
        "El manejo posterior no es evaluable."),
    "order_after_the_arrest": (
        lambda: ('Not executed: "Give 1 L LR". The patient is in cardiac arrest; resuscitation management is not '
                 "modelled in this pilot."),
        "No se ejecutó: «Give 1 L LR». El paciente está en paro cardíaco; el manejo de la reanimación no está "
        "modelado en este piloto."),
    "pulseless_update": (
        lambda: time_semantics.interrupted_lead({"after_min": 3, "requested_until_min": 3, "minute": 3,
                                                 "label": "cardiac arrest, pulse lost"})
        + "No pulse: Ventricular fibrillation on the monitor; no blood pressure; not breathing; unresponsive.",
        "La espera se interrumpió tras 3 min, en el minuto 3: paro cardíaco, sin pulso. Ahora, sin pulso: "
        "Fibrilación ventricular en el monitor; sin presión arterial; sin respiración; sin respuesta."),
    "future_order_not_scheduled": (
        lambda: next(plan["receipt"] for plan in time_semantics.apply(
            "Give aspirin 300 mg in 30 minutes.", parse_family_actions("Give aspirin 300 mg in 30 minutes."))
            .get("ledger_plans") or [] if plan.get("receipt")),
        "No se hizo ahora: «Give aspirin 300 mg in 30 minutes». En este piloto, una orden para más tarde no se "
        "ejecuta: no se administró nada ni se programó nada. Escríbela de nuevo cuando quieras que se haga."),
    "submission_interrupted": (
        lambda: submission_guard.interrupted_message({"raw_text": "Give the normal saline", "rolled_back": True}),
        "Tu orden «Give the normal saline» se interrumpió mientras se procesaba, y no se aplicó nada de ella. Nada "
        "se repetirá automáticamente: revisa el estado del paciente y envíala de nuevo si todavía es necesaria."),
    "submission_interrupted_part_applied": (
        lambda: submission_guard.interrupted_message({"raw_text": "Give 1 L LR"}),
        "Tu orden «Give 1 L LR» se interrumpió mientras se procesaba, y es posible que una parte de ella se haya "
        "aplicado. Nada se repetirá automáticamente: revisa el estado del paciente y envíala de nuevo si todavía es "
        "necesaria."),
    "partial_bundle_not_carried_out": (
        lambda: order_pipeline.held_message(
            {"run": [{"type": "aspirin"}], "held": [({"type": "norepinephrine"}, "refused", "question")],
             "question": None, "no_pending": True}, lambda parsed: ["aspirin 300 mg PO"]
            if parsed["actions"][0]["type"] == "aspirin" else ["norepinephrine"]),
        "**PARTE DE ESTA ORDEN NO SE EJECUTÓ**\n\nEjecutado ahora: **aspirin 300 mg PO**.\nNo ejecutado: "
        "**norepinephrine**. No se ha administrado nada de ello; escríbelo de nuevo como una orden nueva si aún lo "
        "quieres."),
    "partial_bundle_held": (
        lambda: order_pipeline.held_message(
            {"run": [{"type": "aspirin"}], "held": [({"type": "fluid"}, "missing", "question")], "question": None},
            lambda parsed: ["aspirin 300 mg PO"] if parsed["actions"][0]["type"] == "aspirin" else ["normal saline"]),
        "**PARTE DE ESTA ORDEN ESTÁ RETENIDA — SE NECESITA UNA ACLARACIÓN**\n\nEjecutado ahora: **aspirin 300 mg "
        "PO**.\nRetenido hasta que respondas: **suero fisiológico**. No se ha administrado nada de ello."),
    "order_after_an_answer": (
        lambda: _receipt("1000 mL, and give ceftriaxone 2 g IV.", "clarification_answer"),
        "No se ejecutó: «ceftriaxone 2 g IV» se escribió en la respuesta a la pregunta anterior, que solo completa "
        "la orden retenida. Escríbelo de nuevo como una orden nueva si aún lo quieres."),
    "order_read_next_after_an_answer": (
        lambda: ('Also in your answer: "give 500 mL LR". The answer completes the held order only; this order is '
                 "read next, as an order of its own, with its own receipt."),
        "También en tu respuesta: «give 500 mL LR». La respuesta solo completa la orden retenida; esta orden se lee "
        "a continuación, como una orden propia, con su propio recibo."),
    "limit_of_one_step": (
        lambda: ("Specify a reassessment interval from 0 to 120 minutes. The simulator moves the clock at most 120 "
                 "minutes in one step (a limit of this pilot): write a wait or a reassessment of 120 minutes or "
                 "less, and wait again afterwards if you need more time."),
        "Indica un intervalo de reevaluación de 0 a 120 minutos. El simulador avanza el reloj como máximo 120 "
        "minutos de una vez (un límite de este piloto): escribe una espera o una reevaluación de 120 minutos o "
        "menos, y vuelve a esperar después si necesitas más tiempo."),
    "anaphylaxis_arrest_after_a_dose": (
        lambda: anaphylaxis_reaction.ARREST_AFTER_DOSE_TEXT,
        # K-18 (faculty, 2026-10-07; B-5, IG-3).
        "Paro circulatorio tras veinticinco minutos sin adrenalina eficaz: la adrenalina administrada antes no logró "
        "mantener la reacción bajo control. Nada más de lo administrado actúa sobre la reacción."),
    "default_flow": (
        lambda: next(f"{order['canonical']}: {order['default_applied']}."  # as ``settle`` writes it
                     for order in _turn("Start oxygen by non-rebreather mask.")["orders"]
                     if order.get("default_applied")),
        "Oxígeno por mascarilla con reservorio a 15 L/min: no se escribió un flujo; se usó el flujo habitual de la "
        "mascarilla con reservorio, 15 L/min."),
}


@pytest.mark.parametrize("name", list(CASES))
def test_each_new_sentence_is_said_whole_in_spanish_and_unchanged_in_english(name):
    english, spanish = CASES[name][0](), CASES[name][1]
    assert language.say(english, "en") == english
    said = language.say(english, "es")
    assert said == spanish, said
    assert tools_engine_spanish.residue(said.replace("**", " ")) == [] or name.startswith("partial_bundle"), said


def test_the_resident_s_quoted_words_are_never_translated():
    for words in ("Stop the infusion", "Give the normal saline and repeat the ECG", "Dale suero fisiológico"):
        said = language.say(order_ledger.unrecognized_receipt(words), "es")
        assert f"«{words}»" in said, said


def test_the_arrest_examination_is_said_whole():
    said = language.examination(observation_consistency.arrest_examination("Respiratory"), "es")
    assert said == ("Sin respuesta, sin respiración, sin pulso central: el paciente está en paro cardíaco. "
                    "La reanimación no está modelada en este piloto.")


def test_fates_and_codes_are_not_translated():
    turn = _turn("Zyvox IV.")
    [order] = turn["orders"]
    assert order["fate"] == "UNRECOGNIZED" and order["class"] == "unrecognized"
    assert order["receipt"].startswith('Not understood: "Zyvox IV"')  # stored in English; said in Spanish


def test_the_room_says_each_receipt_through_the_reading_language():
    """The receipts reach the room as entries the page says in the encounter's language.

    The Spanish room is not clicked through here: the page's test client cannot select a radio
    whose options are translated (the readiness report renders the Spanish screens apart, for
    the same reason). What the page does is read from its source: the kinds it says through
    ``language.say``, and the kind the ledger's receipts are entered with.
    """
    import ast
    from pathlib import Path
    tree = ast.parse((Path(__file__).resolve().parent / "app.py").read_text(encoding="utf-8"))
    translated = next(
        {element.value for element in node.value.args[0].elts}
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "_TRANSLATED_EVENTS" for t in node.targets))
    assert {"prototype", "clinical_update", "clarification"} <= translated
    entered = []
    order_pipeline.ledger_record({}, _turn("Zyvox IV."), lambda kind, text: entered.append((kind, text)))
    assert entered == [("prototype", order_ledger.unrecognized_receipt("Zyvox IV"))]
    assert language.say(entered[0][1], "es").startswith("No se entendió: «Zyvox IV».")
