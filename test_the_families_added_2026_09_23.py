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


# --- the two bradycardia variants the faculty signed off on -----------------

def test_calcium_is_the_answer_to_one_blockade_and_glucagon_to_the_other(engine):
    """The same two drugs, the opposite sizes. That is the whole differential."""
    reason = (" Creo que es una intoxicacion. Espero que suba la frecuencia. "
              "Reevaluo frecuencia y presion en 5 minutos.")
    _, ccb = play(engine, "bradycardia", "bradycardia_ccb_68m", [
        "Doy gluconato de calcio 2 g EV." + reason])
    _, bb = play(engine, "bradycardia", "bradycardia_bb_54f", [
        "Doy gluconato de calcio 2 g EV." + reason])
    assert ccb[-1]["hr"] - ccb[0]["hr"] > bb[-1]["hr"] - bb[0]["hr"]

    _, ccb_g = play(engine, "bradycardia", "bradycardia_ccb_68m", [
        "Doy glucagon 5 mg EV." + reason])
    _, bb_g = play(engine, "bradycardia", "bradycardia_bb_54f", [
        "Doy glucagon 5 mg EV." + reason])
    assert bb_g[-1]["hr"] - bb_g[0]["hr"] > ccb_g[-1]["hr"] - ccb_g[0]["hr"]


def test_the_tracing_carries_the_severity_before_any_number_does(engine):
    """Faculty, 2026-09-23: the sicker the patient, the slower and the wider."""
    import bradycardia_toxicology as tox
    widths = [tox.qrs_ms(k) for k in (5.5, 6.2, 7.0, 7.6)]
    rates = [tox.potassium_rate_loss(k) for k in (5.5, 6.2, 7.0, 7.6)]
    assert widths == sorted(widths) and widths[0] < widths[-1]
    assert rates == sorted(rates) and rates[0] < rates[-1]
    _, seen = play(engine, "bradycardia", "bradycardia_hyperk_63m", [])
    assert seen[0]["qrs_ms"] >= 170, "the arrival tracing is already broad"
    assert seen[0]["hr"] < 45


def test_calcium_given_on_the_suspicion_narrows_the_complex(engine):
    reason = (" Sospecho hiperkalemia por el QRS ancho y la bradicardia. Espero que se "
              "angoste el QRS. Reevaluo frecuencia, QRS y presion en 5 minutos.")
    _, seen = play(engine, "bradycardia", "bradycardia_hyperk_63m", [
        "Doy gluconato de calcio 2 g EV." + reason])
    arrival, after = seen
    assert after["qrs_ms"] < arrival["qrs_ms"] - 50
    assert after["hr"] > arrival["hr"] + 20
    assert after["sbp"] > arrival["sbp"] + 10


def test_the_calcium_does_not_lower_the_potassium_and_says_so(engine):
    """It protects the membrane. The number in the record is unchanged."""
    reason = (" Sospecho hiperkalemia. Espero que se angoste el QRS. "
              "Reevaluo frecuencia y QRS en 5 minutos.")
    session, seen = play(engine, "bradycardia", "bradycardia_hyperk_63m", [
        "Doy gluconato de calcio 2 g EV." + reason,
        "Reevalua frecuencia, presion y conciencia en 30 minutos.",
        "Reevalua frecuencia, presion y conciencia en 30 minutos."])
    assert session["state"]["family_state"]["potassium"] == 7.6
    # And what it bought comes back, because nothing has removed any of it.
    assert seen[1]["qrs_ms"] < seen[-1]["qrs_ms"]


def test_a_nebulised_beta_agonist_moves_the_potassium_itself(engine):
    reason = (" Sospecho hiperkalemia. Espero bajar el potasio. "
              "Reevaluo frecuencia y QRS en 10 minutos.")
    session, _ = play(engine, "bradycardia", "bradycardia_hyperk_63m", [
        "Doy salbutamol 10 mg nebulizado." + reason,
        "Reevalua frecuencia, presion y conciencia en 30 minutos."])
    assert session["state"]["family_state"]["potassium"] < 7.6


def test_waiting_for_the_laboratory_changes_nothing(engine):
    """The window of the event runs from the tracing, and so does the case."""
    _, seen = play(engine, "bradycardia", "bradycardia_hyperk_63m", [
        "Pido un panel de laboratorio.",
        "Reevalua frecuencia, presion y conciencia en 20 minutos."])
    assert seen[-1]["hr"] == seen[0]["hr"]
    assert seen[-1]["qrs_ms"] == seen[0]["qrs_ms"]


def test_the_event_of_the_potassium_case_starts_at_the_tracing():
    from case_assessment_bank import CASES
    events = {e["event_id"]: e for e in CASES["bradycardia_hyperk_63m"]["critical_events"]}
    calcium = events["hyperk_calcium_awaited_the_laboratory"]
    assert calcium["window_min"] == (0, 20)
    assert "the arrival tracing" in calcium["information_required"]
    assert "laborator" in calcium["trigger"]


def test_the_ecg_draws_the_width_the_case_declares():
    import ecg12
    narrow = ecg12._parameters(38, "sinus", "baseline")
    broad = ecg12._parameters(38, "sinus", "baseline", qrs_s=.180)
    assert broad["qrs_s"] > narrow["qrs_s"]
    # And a width outside the readable range is refused rather than drawn.
    assert ecg12._qrs_override({"qrs_ms": 999}) is None
    assert ecg12._qrs_override({"qrs_ms": "wide"}) is None
    assert ecg12._qrs_override({"qrs_ms": 168}) == pytest.approx(.168)


@pytest.mark.parametrize("case_id", ["bradycardia_bb_54f", "bradycardia_hyperk_63m"])
def test_the_signed_variants_declare_what_they_offer(case_id):
    from case_assessment import verify
    assert verify(case_id) == []


# --- trauma: the x of xABCDE, and a haemothorax that is not a volume --------

TRAUMA_REASON = (" Creo que es un shock hemorragico. Espero que suba la presion. "
                 "Reevaluo presion, frecuencia y perfusion en 5 minutos.")


def test_the_minutes_before_the_tourniquet_are_paid_for_in_blood(engine):
    """Faculty decision 2.2: the x comes first, and the engine holds them to it."""
    _, early = play(engine, "trauma", "trauma_limb_hemorrhage_27m", [
        "Pongo un torniquete en el muslo." + TRAUMA_REASON,
        wait(10)])
    session, late = play(engine, "trauma", "trauma_limb_hemorrhage_27m", [
        wait(10),
        "Pongo un torniquete en el muslo." + TRAUMA_REASON])
    assert late[-1]["sbp"] < early[-1]["sbp"] - 30
    assert late[-1]["mental_status"] != "Alert"
    assert session["state"]["family_state"]["blood_lost_ml"] > 2000


def test_a_tourniquet_stops_it_and_does_not_raise_the_pressure_by_itself(engine):
    session, seen = play(engine, "trauma", "trauma_limb_hemorrhage_27m", [
        "Pongo un torniquete en el muslo." + TRAUMA_REASON, wait(15)])
    lost = session["state"]["family_state"]["blood_lost_ml"]
    assert lost == pytest.approx(700, abs=1), "seeded from the arrival deficit and then frozen"
    assert seen[-1]["sbp"] == seen[0]["sbp"], "stopping the loss is not replacing it"


def test_blood_replaces_what_was_lost_and_crystalloid_less_of_it(engine):
    """Two units carry what a litre of salt cannot, and the engine prices that.

    Compared once both have actually run in. A unit of packed cells takes time
    in this engine and a litre of crystalloid does not, so at twenty minutes the
    salt is ahead -- which is true, and is not what this test is about.
    """
    _, with_blood = play(engine, "trauma", "trauma_limb_hemorrhage_27m", [
        "Pongo un torniquete en el muslo." + TRAUMA_REASON,
        "Transfundo 2 unidades de globulos rojos." + TRAUMA_REASON, wait(60)])
    _, with_fluid = play(engine, "trauma", "trauma_limb_hemorrhage_27m", [
        "Pongo un torniquete en el muslo." + TRAUMA_REASON,
        "Paso 1000 cc de suero fisiologico EV." + TRAUMA_REASON, wait(60)])
    assert with_blood[-1]["sbp"] > with_fluid[-1]["sbp"]
    assert with_fluid[-1]["sbp"] > with_fluid[0]["sbp"], "and salt is not nothing"


def test_uncontrolled_bleeding_reaches_an_arrest_and_says_why(engine):
    generated = build_encounter(engine, "trauma", "trauma_limb_hemorrhage_27m")
    session = initialize(engine, deepcopy(generated["state"]))
    labels = []
    for order in (wait(15), wait(15)):
        _, result, _, _ = execute_turn(engine, order)
        labels.extend(str(s.get("label") or "") for s in result.get("action_summaries", []))
    assert any("arrest" in text.lower() for text in labels), labels
    assert any("no volume replaces a source that is still open" in text.lower()
               for text in labels), labels


def test_a_needle_does_not_drain_a_haemothorax(engine):
    session, _ = play(engine, "trauma", "trauma_hemothorax_41m", [
        "Hago descompresion con aguja del torax izquierdo." + TRAUMA_REASON])
    assert session["state"]["family_state"].get("thoracostomy_at") is None


def test_the_tube_drains_and_the_chest_keeps_filling(engine):
    """Faculty decision 2.4: it is the instability and not the volume."""
    session, seen = play(engine, "trauma", "trauma_hemothorax_41m", [
        "Instalo un tubo pleural izquierdo." + TRAUMA_REASON, wait(15)])
    f = session["state"]["family_state"]
    assert f["thoracostomy_at"] is not None
    assert f["thoracic_drained_ml"] > 1000
    assert seen[-1]["sbp"] < seen[0]["sbp"], "draining is not stopping"


def test_looking_again_only_counts_after_the_drain(engine):
    import trauma_hemorrhage
    before = {"thoracostomy_at": 20, "efast_at": 5, "pelvis_xray_at": None}
    after = {"thoracostomy_at": 20, "efast_at": 25, "pelvis_xray_at": None}
    never = {"thoracostomy_at": None, "efast_at": 25}
    assert not trauma_hemorrhage.searched_again(before)
    assert trauma_hemorrhage.searched_again(after)
    assert not trauma_hemorrhage.searched_again(never)


def test_the_theatre_is_indicated_by_the_sequence_and_not_by_a_volume():
    import trauma_hemorrhage
    unstable = {"sbp": 78, "crt": 4}
    stable = {"sbp": 118, "crt": 2}
    drained_and_searched = {"thoracostomy_at": 10, "efast_at": 20}
    assert trauma_hemorrhage.theatre_indicated(drained_and_searched, unstable)
    assert not trauma_hemorrhage.theatre_indicated(drained_and_searched, stable)
    assert not trauma_hemorrhage.theatre_indicated({"thoracostomy_at": 10}, unstable)
    assert not trauma_hemorrhage.theatre_indicated(
        {**drained_and_searched, "other_site_found": True}, unstable)


# --- the E-FAST the faculty wrote ------------------------------------------

def test_the_efast_has_the_five_windows_the_faculty_listed():
    import efast_report
    assert [name for name, _ in efast_report.SECTIONS] == [
        "Right upper quadrant", "Left upper quadrant", "Suprapubic", "Subxiphoid", "Lung"]
    # The suprapubic window is looked at twice, longitudinally and transversely.
    suprapubic = dict(efast_report.SECTIONS)["Suprapubic"]
    assert len(suprapubic) == 2


def test_every_window_is_reported_including_the_normal_ones():
    import efast_report
    result = efast_report.study(ruq_morison="Free fluid in the hepatorenal recess")
    assert efast_report.missing_windows(result) == []
    assert set(result) == set(efast_report.KEYS)


def test_the_report_says_which_windows_were_positive_and_interprets_nothing():
    import efast_report
    result = efast_report.study(ruq_morison="Free fluid in the hepatorenal recess",
                                pericardium="Pericardial fluid, circumferential")
    assert efast_report.free_fluid(result) == ["ruq_morison", "pericardium"]
    # And nothing in a normal study says "negative" or "no tamponade".
    for text in efast_report.NORMAL.values():
        lowered = text.lower()
        assert "negative" not in lowered and "tamponade" not in lowered
        assert "normal" not in lowered


def test_sliding_excludes_a_pneumothorax_and_its_absence_is_named():
    import efast_report
    assert efast_report.pneumothorax_windows(efast_report.study()) == []
    absent = efast_report.study(lung_sliding_left="Absent on the left")
    assert efast_report.pneumothorax_windows(absent) == ["lung_sliding_left"]


def test_the_cardiac_windows_come_first_in_penetrating_trauma():
    """Assessed, never enforced: the order is a decision, not a setting."""
    import efast_report
    assert efast_report.cardiac_first(["pericardium", "ruq_morison"])
    assert not efast_report.cardiac_first(["ruq_morison", "pericardium"])
    assert not efast_report.cardiac_first([]), "nobody looked is not a yes"


def test_a_window_outside_the_protocol_is_refused():
    import efast_report
    with pytest.raises(ValueError):
        efast_report.study(spleen="Free fluid")


@pytest.mark.parametrize("case_id", ["trauma_limb_hemorrhage_27m", "trauma_hemothorax_41m"])
def test_the_trauma_cases_declare_what_they_offer(case_id):
    from case_assessment import verify
    assert verify(case_id) == []
