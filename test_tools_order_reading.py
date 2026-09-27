"""The order-reading measurement compares what it should, and only that."""
import tools_order_reading as reading


def _entry(text, actions=(), status="executed", slots=None, provenance=None, future=()):
    return reading.compact_entry({
        "learner_input": text, "execution_status": status, "interpretation_mode": "deterministic",
        "decision_time_min": 5, "interpreted_action": list(actions),
        "recognized_future_actions": list(future), "future_details": [],
        "reasoning_gate": {"required": True, "status": "complete", "missing": []},
        "reasoning": {**(slots or {}), "slot_provenance": provenance or {}},
    })


def test_the_same_decision_has_the_same_signature_in_either_language():
    spanish = _entry("Doy adrenalina 0.5 mg im", [{"type": "epinephrine_im", "dose_mg": 0.5, "route": "IM"}])
    english = _entry("Give epinephrine 0.5 mg IM", [{"route": "IM", "dose_mg": 0.5000001, "type": "epinephrine_im"}])
    assert spanish["actions"] == english["actions"]


def test_a_slot_that_changes_the_learners_words_is_not_a_quotation():
    assert reading.quoted_faithfully("una anafilaxia por la picadura", "Creo que es una anafilaxia por la picadura.")
    assert not reading.quoted_faithfully("Doy adrenalina 0.5 mg I'm", "Doy adrenalina 0.5 mg im.")
    assert not reading.quoted_faithfully("un IAM inferior con posible compromi",
                                         "Creo que es un IAM inferior con posible compromiso del VD")


def test_an_order_in_the_place_of_the_working_model_is_named():
    assert reading.reads_as_an_order("inicio adrenalina en infusion a 0.1 mcg/kg/min")
    assert not reading.reads_as_an_order("una anafilaxia por la picadura")


def test_the_two_languages_are_compared_decision_by_decision():
    def run(entries, close=40):
        return {"result": {"sim_time_at_close": close}, "stored": {"trace": entries}}
    same = [{"type": "epinephrine_im", "dose_mg": 0.5, "route": "IM"}]
    spanish = {1: run([_entry("Doy adrenalina 0.5 mg im", same, future=["doy ondansetron 4 mg ev"],
                              slots={"problem_representation": "x"},
                              provenance={"problem_representation": "stated"})])}
    english = {1: run([_entry("Give epinephrine 0.5 mg IM", same, future=["give ondansetron 4 mg iv"],
                              slots={"problem_representation": "y"},
                              provenance={"problem_representation": "carried"})], close=45)}
    differences = reading.paired_differences(spanish, english)
    # Future actions are kept in each language's words: only their number is compared.
    assert {d["what"] for d in differences} == {"provenance", "minute_at_close"}
