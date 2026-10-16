import language


def test_pacing_preparation_trace_label_has_spanish_presentation():
    english = "transcutaneous pacing preparation recorded; pacing not started"
    assert language.say(english, "es") == (
        "preparación para marcapasos transcutáneo registrada; estimulación no iniciada"
    )


def test_serum_magnesium_keeps_the_approved_spanish_label():
    assert language.say("Serum magnesium", "es") == "Magnesio sérico"
