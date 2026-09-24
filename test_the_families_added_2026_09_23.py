"""Three families added on 2026-09-23, and what each of them is built to teach.

Anaphylaxis, ureteric colic with its infected counterpart, and the unstable
bradycardia. Each was asked for by the faculty; each entered under the same
contract as the eight before them -- five declared domains, a critical event
with a clinical window, and no discrepancy between what the declaration promises
and what the case carries.

What is pinned here is not that the code runs. It is the clinical claim each
family makes, because that is what would be lost silently if a coefficient
moved: the route of the adrenaline being visible, the antibiotic that cannot
reach an obstructed kidney, and the atropine that does nothing to a block below
the node.
"""
from copy import deepcopy

import pytest

from test_cognitive_encounters import encounter as build_encounter
from test_curriculum_trajectories import execute_turn, initialize, load_engine


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def play(engine, family, case_id, orders):
    """Play a scripted encounter and return the observables after each turn."""
    generated = build_encounter(engine, family, case_id)
    session = initialize(engine, deepcopy(generated["state"]))
    seen = [deepcopy(session["state"]["observable"])]
    for order in orders:
        execute_turn(engine, order)
        seen.append(deepcopy(session["state"]["observable"]))
    return session, seen


REASON = (" Creo que esto es lo que esta pasando. Espero que mejore. "
          "Reevaluo presion, frecuencia y conciencia en {n} minutos.")


def wait(minutes):
    return f"Reevalua presion, frecuencia y conciencia en {minutes} minutos."


# --- anaphylaxis ------------------------------------------------------------

def test_the_intramuscular_route_is_visible_in_the_numbers(engine):
    """Two minutes after the dose, nothing has happened yet. That is the case."""
    _, seen = play(engine, "anaphylaxis", "anaphylaxis_29f", [
        "Doy adrenalina 0.5 mg IM en el muslo." + REASON.format(n=2),
        wait(3), wait(10)])
    arrival, at_two, at_five, at_fifteen = seen
    assert at_two["sbp"] <= arrival["sbp"] + 2, "the depot has not been absorbed yet"
    assert at_five["sbp"] > at_two["sbp"], "by five minutes it is working"
    assert at_fifteen["sbp"] > at_five["sbp"] + 8, "and it keeps working"


def test_a_steroid_does_not_treat_the_reaction(engine):
    _, seen = play(engine, "anaphylaxis", "anaphylaxis_29f", [
        "Doy hidrocortisona 200 mg EV." + REASON.format(n=10), wait(10)])
    assert seen[-1]["sbp"] < seen[0]["sbp"], "the reaction continues"


def test_an_untreated_reaction_reaches_an_arrest_and_says_so(engine):
    """The event is drained into the turn that surfaces it, so it is read there."""
    generated = build_encounter(engine, "anaphylaxis", "anaphylaxis_29f")
    session = initialize(engine, deepcopy(generated["state"]))
    labels = []
    for order in (wait(15), wait(15)):
        _, result, _, _ = execute_turn(engine, order)
        labels.extend(str(s.get("label") or "") for s in result.get("action_summaries", []))
    assert any("arrest" in text.lower() for text in labels), labels
    assert any("adrenaline was the treatment" in text.lower() for text in labels), labels


def test_a_blocked_receptor_answers_a_third_as_well(engine):
    """The same order, the same dose, a smaller response. And the reason is askable."""
    _, plain = play(engine, "anaphylaxis", "anaphylaxis_29f", [
        "Doy adrenalina 0.5 mg IM." + REASON.format(n=10)])
    _, blocked = play(engine, "anaphylaxis", "anaphylaxis_63m_betablocked", [
        "Doy adrenalina 0.5 mg IM." + REASON.format(n=10)])
    gained = plain[-1]["sbp"] - plain[0]["sbp"]
    blunted = blocked[-1]["sbp"] - blocked[0]["sbp"]
    assert blunted < gained, (blunted, gained)


def test_glucagon_restores_what_the_blockade_took(engine):
    _, without = play(engine, "anaphylaxis", "anaphylaxis_63m_betablocked", [
        "Doy adrenalina 0.5 mg IM." + REASON.format(n=10), wait(15)])
    _, with_glucagon = play(engine, "anaphylaxis", "anaphylaxis_63m_betablocked", [
        "Doy adrenalina 0.5 mg IM." + REASON.format(n=10),
        "Doy glucagon 5 mg EV." + REASON.format(n=15)])
    assert with_glucagon[-1]["sbp"] > without[-1]["sbp"]


def test_the_blocked_patient_never_mounts_the_tachycardia(engine):
    """The rate that does not rise is itself the finding."""
    _, seen = play(engine, "anaphylaxis", "anaphylaxis_63m_betablocked", [wait(10)])
    assert seen[0]["hr"] < 80
    assert seen[-1]["hr"] < 80


# --- renal colic and its infected counterpart -------------------------------

def test_both_flank_pain_cases_show_the_same_dilatation(engine):
    """The study does not decide which patient this is."""
    import clinical_cases
    colic, pyelo = (clinical_cases.variant_by_id(name) for name in
                    ("renal_colic_34m", "obstructive_pyelonephritis_58f"))
    for case in (colic, pyelo):
        report = case["investigations"]["renal_ultrasound"]["result"]["report"]
        assert "dilatation" in report and "calculus" in report
    assert colic["observable"]["temperature_c"] < 37.5
    assert pyelo["observable"]["temperature_c"] > 38.5


def test_an_antibiotic_alone_does_not_turn_an_obstructed_kidney(engine):
    """A referral is recorded, never its result. So treatment slows the course."""
    reason = (" Creo que es una pielonefritis obstructiva. Espero que mejore la perfusion. "
              "Reevaluo presion y frecuencia en 60 minutos.")
    _, seen = play(engine, "renal_colic", "obstructive_pyelonephritis_58f", [
        "Doy ceftriaxona 2 g EV." + reason, wait(60), wait(60)])
    assert seen[-1]["sbp"] < seen[0]["sbp"], "the pressure keeps falling"
    assert seen[-1]["hr"] > seen[0]["hr"]


def test_volume_buys_pressure_and_then_gives_it_back(engine):
    reason = (" Creo que es una sepsis de foco urinario. Espero que suba la presion. "
              "Reevaluo presion y frecuencia en 15 minutos.")
    _, seen = play(engine, "renal_colic", "obstructive_pyelonephritis_58f", [
        "Paso 1000 cc de suero fisiologico EV." + reason, wait(90)])
    arrival, after_fluid, later = seen
    assert after_fluid["sbp"] > arrival["sbp"], "volume works"
    assert later["sbp"] < after_fluid["sbp"], "and it is not the treatment"


def test_the_uncomplicated_colic_does_not_deteriorate_on_its_own(engine):
    _, seen = play(engine, "renal_colic", "renal_colic_34m", [wait(30), wait(60)])
    assert seen[-1]["sbp"] == seen[0]["sbp"]
    assert seen[-1]["hr"] == seen[0]["hr"]


def test_the_analgesia_changes_the_pain_and_nothing_else(engine):
    reason = (" Creo que es un colico renal. Espero que ceda el dolor. "
              "Reevaluo dolor y signos vitales en 20 minutos.")
    _, seen = play(engine, "renal_colic", "renal_colic_34m", [
        "Doy ketorolaco 30 mg EV." + reason])
    assert seen[-1]["pain_score"] < seen[0]["pain_score"]
    assert seen[-1]["sbp"] == seen[0]["sbp"]


def test_urology_is_reachable_by_name_and_by_what_it_is_asked_to_do():
    from family_parser import parse_family_actions
    for text in ("Llamo a urologia.", "Consult urology for decompression.",
                 "Pido nefrostomia percutanea.", "Solicito un cateter doble J."):
        actions = parse_family_actions(text)["actions"]
        assert actions == [{"type": "consult", "service": "urology"}], text


# --- unstable bradycardia ---------------------------------------------------

def test_no_dose_of_atropine_lifts_a_block_below_the_node(engine):
    reason = (" Creo que es una bradicardia sintomatica. Espero que suba la frecuencia. "
              "Reevaluo frecuencia y presion en 5 minutos.")
    _, seen = play(engine, "bradycardia", "bradycardia_avb3_78f", [
        "Doy atropina 1 mg EV." + reason,
        "Doy atropina 1 mg EV otra vez." + reason])
    assert seen[-1]["hr"] == seen[0]["hr"] == 32


def test_atropine_does_not_lift_a_calcium_channel_blockade_either(engine):
    reason = (" Creo que es una bradicardia sintomatica. Espero que suba la frecuencia. "
              "Reevaluo frecuencia y presion en 5 minutos.")
    _, seen = play(engine, "bradycardia", "bradycardia_ccb_68m", [
        "Doy atropina 1 mg EV." + reason])
    assert seen[-1]["hr"] == seen[0]["hr"] == 38


def test_calcium_answers_the_blockade_and_does_not_last(engine):
    reason = (" Creo que es una intoxicacion por bloqueador de calcio. Espero que suba la "
              "frecuencia y la presion. Reevaluo frecuencia y presion en 5 minutos.")
    _, seen = play(engine, "bradycardia", "bradycardia_ccb_68m", [
        "Doy gluconato de calcio 2 g EV." + reason, wait(30)])
    arrival, after_calcium, later = seen
    assert after_calcium["hr"] > arrival["hr"] + 15
    assert after_calcium["sbp"] > arrival["sbp"] + 30
    assert later["hr"] < after_calcium["hr"], "the antidote is not definitive"


def test_calcium_does_nothing_to_a_block(engine):
    reason = (" Creo que es un bloqueo completo. Espero que suba la frecuencia. "
              "Reevaluo frecuencia y presion en 5 minutos.")
    _, seen = play(engine, "bradycardia", "bradycardia_avb3_78f", [
        "Doy gluconato de calcio 2 g EV." + reason])
    assert seen[-1]["hr"] == seen[0]["hr"]


def test_a_set_rate_is_not_a_circulation_until_it_captures(engine):
    reason = (" Creo que es un bloqueo completo sintomatico. Espero capturar y que suba la "
              "presion. Reevaluo pulso, presion y frecuencia en 5 minutos.")
    session, seen = play(engine, "bradycardia", "bradycardia_avb3_78f", [
        "Inicio marcapasos transcutaneo a 70 por minuto con 50 mA." + reason,
        "Subo el marcapasos a 90 mA." + reason])
    arrival, uncaptured, captured = seen
    assert uncaptured["hr"] == arrival["hr"], "spikes without capture are not a rate"
    assert "without capture" in uncaptured["rhythm"]
    assert captured["hr"] == 70
    assert "capture confirmed" in captured["rhythm"]
    assert captured["sbp"] > arrival["sbp"] + 25


def test_the_glucose_is_the_clue_and_it_is_only_in_one_of_them():
    import clinical_cases
    ccb = clinical_cases.variant_by_id("bradycardia_ccb_68m")
    block = clinical_cases.variant_by_id("bradycardia_avb3_78f")
    assert ccb["observable"]["glucose_mg_dl"] > 180
    assert 70 <= block["observable"]["glucose_mg_dl"] <= 140
    # And neither of them has a potassium that would explain the rate.
    for case in (ccb, block):
        potassium = case["investigations"]["basic_labs"]["result"]["potassium_mmol_l"]
        assert potassium < 5.5


# --- the contract every family enters under ---------------------------------

@pytest.mark.parametrize("case_id", [
    "anaphylaxis_29f", "anaphylaxis_63m_betablocked",
    "renal_colic_34m", "obstructive_pyelonephritis_58f",
    "bradycardia_ccb_68m", "bradycardia_avb3_78f",
])
def test_each_new_case_declares_what_it_offers_without_discrepancy(case_id):
    from case_assessment import verify
    assert verify(case_id) == []


@pytest.mark.parametrize("family", ["anaphylaxis", "renal_colic", "bradycardia"])
def test_each_new_family_hangs_from_a_decision_challenge(family):
    from cognitive_catalog import BIAS_CHALLENGES
    assert [key for key, item in BIAS_CHALLENGES.items() if family in item["families"]]
