import language
import unexecuted_items


def test_pacing_preparation_trace_label_has_spanish_presentation():
    event = {
        "future_details": [{
            "text": "prepare transcutaneous pacing pads",
            "kind": "not_modelled",
            "category": "pacing_preparation",
        }]
    }
    [(written, english_label)] = unexecuted_items.trace_labels(event)
    assert written == "prepare transcutaneous pacing pads"
    assert english_label == "transcutaneous pacing preparation recorded; pacing not started"
    assert language.say(english_label, "es") == (
        "preparación para marcapasos transcutáneo registrada; estimulación no iniciada"
    )


def test_serum_magnesium_keeps_the_approved_spanish_label():
    assert language.say("Serum magnesium", "es") == "Magnesio sérico"
