"""The arrest and return events say what happened, in both languages (B-5, IG-3; faculty, 2026-10-07/08).

K-18 and K-E5: the anaphylaxis arrest after a dose names adrenaline that did not keep the reaction
under control, and its label is true with or without a dose; K-21 stays the truly untreated
sentence. K-E6: the bradycardia arrest is a circulatory arrest from profound bradycardia. K-E16: the
saturation is written «84%». TD-85: the two sentences the room writes at the bradycardia arrest and
at the anaphylactic reaction's return read, in Spanish, in the approved event terminology. Only
the words change: trigger, minute, cause, preventability and severity are the engine's as before.
"""
import pytest

import anaphylaxis_reaction
import bradycardia_toxicology
import event_provenance
import language
import pilot_acceptance as acceptance


def _events(encounter):
    return [event for entry in encounter.entries for event in entry["events"]]


def _labels(encounter):
    return [str(s.get("label") or "") for entry in encounter.entries for s in entry["action_summaries"]]


def test_the_anaphylaxis_arrest_label_is_true_with_and_without_a_dose():
    label = "circulatory arrest from anaphylaxis without effective adrenaline"
    assert event_provenance.FLAG_EVENTS["arrested"]["label"] == label
    assert language.say(label, "es") == "paro circulatorio por anafilaxia sin adrenalina eficaz"
    untreated = acceptance.Encounter("anaphylaxis_29f").wait_until(60)
    dosed = acceptance.Encounter("anaphylaxis_63m_betablocked")
    dosed.order("Give epinephrine 0.5 mg IM. Reassess in 15 minutes.")
    dosed.wait_until(120, step=15)
    for encounter, sentence in ((untreated, anaphylaxis_reaction.ARREST_TEXT),
                                (dosed, anaphylaxis_reaction.ARREST_AFTER_DOSE_TEXT)):
        arrests = [event for event in _events(encounter) if event["flag"] == "arrested"]
        assert encounter.arrested and len(arrests) == 1
        assert arrests[0]["label"] == label and arrests[0]["cause_class"] == "NATURAL_DISEASE"
        assert arrests[0]["preventability"] == "PREVENTABLE" and arrests[0]["severity"] == "terminal"
        assert sentence in _labels(encounter)
    # K-21 stays the sentence of the anaphylaxis that was really untreated.
    assert anaphylaxis_reaction.ARREST_AFTER_DOSE_TEXT not in _labels(untreated)
    assert anaphylaxis_reaction.ARREST_TEXT not in _labels(dosed)


def test_the_arrest_after_a_dose_says_the_adrenaline_did_not_keep_the_reaction_under_control():
    assert anaphylaxis_reaction.ARREST_AFTER_DOSE_TEXT == (
        "Circulatory arrest after twenty-five minutes without effective adrenaline: the adrenaline given earlier "
        "did not keep the reaction under control. Nothing else that was given acts on the reaction.")
    assert language.say(anaphylaxis_reaction.ARREST_AFTER_DOSE_TEXT, "es") == (
        "Paro circulatorio tras veinticinco minutos sin adrenalina eficaz: la adrenalina administrada antes no logró "
        "mantener la reacción bajo control. Nada más de lo administrado actúa sobre la reacción.")
    for word in ("worn off", "come back", "untreated"):
        assert word not in anaphylaxis_reaction.ARREST_AFTER_DOSE_TEXT


@pytest.mark.parametrize("variant", ["bradycardia_ccb_68m", "bradycardia_avb3_78f",
                                     "bradycardia_bb_54f", "bradycardia_hyperk_63m"])
def test_the_bradycardia_arrest_is_named_in_the_approved_terminology(variant):
    label = "circulatory arrest from profound bradycardia"
    assert event_provenance.FLAG_EVENTS["bradycardia_arrest"]["label"] == label
    untreated = acceptance.Encounter(variant).wait_until(180)
    arrests = [event for event in _events(untreated) if event["flag"] == "bradycardia_arrest"]
    assert untreated.arrested and len(arrests) == 1 and arrests[0]["label"] == label
    assert arrests[0]["preventability"] == "PREVENTABLE" and arrests[0]["severity"] == "terminal"
    assert language.say(label, "es") == "paro circulatorio por bradicardia profunda"
    # TD-85 (a): the sentence the room writes at the arrest, in the same terminology in Spanish.
    assert bradycardia_toxicology.ARREST_TEXT in _labels(untreated)
    assert language.say(bradycardia_toxicology.ARREST_TEXT, "es") == "Paro circulatorio por bradicardia profunda."


def test_the_reaction_that_returns_is_said_in_the_approved_terminology():
    treated = acceptance.Encounter("anaphylaxis_29f")
    # Settled by two doses, the reaction returns 75 minutes later (the case declares it biphasic).
    treated.order("Give epinephrine 0.5 mg IM. Give 1 liter of normal saline IV. Reassess in 15 minutes.")
    treated.order("Give epinephrine 0.5 mg IM. Reassess in 15 minutes.")
    treated.wait_until(120, step=30)
    returns = [event for event in _events(treated) if event["flag"] == "biphasic_at"]
    assert len(returns) == 1 and returns[0]["label"] == "the anaphylactic reaction returns"
    assert returns[0]["preventability"] == "NOT_PREVENTABLE_IN_SIMULATOR"
    assert language.say(returns[0]["label"], "es") == "la reacción anafiláctica vuelve"
    # TD-85 (b).
    assert anaphylaxis_reaction.BIPHASIC_TEXT in _labels(treated)
    assert language.say(anaphylaxis_reaction.BIPHASIC_TEXT, "es") == "La reacción anafiláctica vuelve."


def test_the_saturation_event_writes_its_percentage_as_the_room_does():
    watch = event_provenance.Watch({"observable": {"sbp": 120, "spo2": 95, "pulse_present": True}})
    found = []
    for minute in range(1, 4):
        found += watch.step({"sim_time": minute, "observable": {"sbp": 120, "spo2": 84, "pulse_present": True}})
    assert [event["label"] for event in found] == ["saturation 84% and falling"]
    assert language.say("saturation 84% and falling", "es") == "saturación de 84 % y en descenso"
    # An encounter recorded before 2026-10-08 still reads in Spanish.
    assert language.say("saturation 84 % and falling", "es") == "saturación de 84 % y en descenso"


def test_the_labels_recorded_before_2026_10_08_still_read_in_spanish():
    for english, spanish in (
            ("circulatory arrest from untreated anaphylaxis", "paro circulatorio por anafilaxia no tratada"),
            ("loss of circulation from the falling rate", "pérdida de la circulación por la frecuencia que cae")):
        assert language.say(english, "es") == spanish
