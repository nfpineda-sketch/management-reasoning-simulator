"""The examination says the state the engine is in (B-5, IG-4; faculty, 2026-10-07 and 2026-10-08).

A-2: the pulmonary oedema of a patient who is exhausted reads as exhaustion, never as an effort
that still compensates. A-6, A-6a, A-6b, A-7-49m and A-8a: the 49m keeps the severity he arrived
with while his obstruction has not improved, read on the engine's state at each examination,
never on the order that ran, the intubation alone or the induction drug; the 24f is unchanged.
A-9 to A-11: during assisted ventilation the opioid patient's rate is the ventilation's, and the
three sentences write «{n}/min». TD-84: the English examination of the two opioid cases says
their small reactive pupils, as the Spanish already did. Only the words change: these tests also
hold the vital signs and the course to what the engine did before.
"""
import pytest

import case_text
import language
import pilot_acceptance as acceptance
import work_of_breathing
from family_engine import (_airway_relaxation, advance_clinical_time, current_findings,
                           examination_finding)

A2_EXHAUSTED = ("Bilateral inspiratory crackles; respiratory effort is now shallow and ineffective, consistent with "
                "exhaustion.")
A2_INCREASED = "Bilateral inspiratory crackles with increased respiratory effort."
A3_REDUCED = "Bilateral crackles remain, with reduced respiratory effort."
A6 = "Reduced bilateral air entry with prolonged expiration and wheeze."
A5 = "Improved air entry with residual expiratory wheeze."
A6A = ("Severe effort with very poor bilateral air entry and only faint wheeze. He cannot complete a reliable "
       "peak-flow maneuver.")
A6B = "Endotracheal tube in place: air entry remains very poor bilaterally, with only faint wheeze."
A7 = "Breath sounds absent over the right hemithorax, which is hyper-resonant; wheeze on the other side."
A7_49M = ("Breath sounds absent over the right hemithorax, which is hyper-resonant; air entry on the left remains "
          "very poor, with only faint wheeze.")
A8A = ("Breath sounds returning on the right after decompression; air entry remains very poor bilaterally, with "
       "only faint wheeze.")
A8_IMPROVED = "Breath sounds returning on the right after decompression; improved air entry with residual expiratory wheeze."
A8_A6 = ("Breath sounds returning on the right after decompression; reduced bilateral air entry with prolonged "
         "expiration and wheeze.")

OXYGEN = "Give oxygen by non-rebreather mask at 15 L/min. Reassess in 10 minutes."
NIV = "Start BiPAP with IPAP 12 and EPAP 6 and FiO2 60%. Reassess in 10 minutes."
ETOMIDATE = ("Give etomidate 20 mg IV and rocuronium 100 mg IV and intubate VC/AC FiO2 100% PEEP 0 Vt 450 mL rate 12 "
             "flow 80 L/min. Reassess in 5 minutes.")
KETAMINE = ("Give ketamine 100 mg IV and intubate VC/AC FiO2 100% PEEP 0 Vt 450 mL rate 12 flow 80 L/min. "
            "Reassess in 5 minutes.")
HIGH_PRESSURE = ("Give etomidate 20 mg IV and rocuronium 100 mg IV and intubate VC/AC FiO2 100% PEEP 5 Vt 750 mL "
                 "rate 30. Reassess in 10 minutes.")
DECOMPRESS = "Perform needle decompression of the right chest. Reassess in 5 minutes."
BRONCHODILATOR = "Give albuterol 5 mg nebulized and ipratropium 0.5 mg nebulized. Reassess in 15 minutes."


def _respiratory(variant, orders):
    encounter = acceptance.Encounter(variant)
    seen = []
    for order in orders:
        entry = encounter.order(order)
        assert entry["executed"], (order, entry["clarification"])
        assert not encounter.arrested, order
        seen.append(examination_finding(encounter.state, "Respiratory"))
    return seen


# --- A-2 ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("variant", ["pulmonary_edema_58m", "pulmonary_edema_75f"])
def test_the_exhausted_oedema_reads_as_exhaustion_and_never_as_increased_effort(variant):
    encounter = acceptance.Encounter(variant)
    exhausted = 0
    for _ in range(140):
        advance_clinical_time(encounter.state, 1)
        if not encounter.state["observable"].get("pulse_present", True):
            break
        respiratory = current_findings(encounter.state)["Respiratory"]
        if encounter.state["observable"]["work_of_breathing"] == work_of_breathing.EXHAUSTED:
            exhausted += 1
            assert respiratory == A2_EXHAUSTED, encounter.state["sim_time"]
        else:
            assert respiratory in (A2_INCREASED, A3_REDUCED), encounter.state["sim_time"]
    assert exhausted, "the untreated oedema reaches exhaustion within the window"


# --- A-6 and its edge states ---------------------------------------------------------------------------

def test_the_49m_keeps_its_arrival_examination_while_breathing_on_his_own_and_not_improved():
    encounter = acceptance.Encounter("asthma_49m")
    assert examination_finding(encounter.state, "Respiratory") == A6A  # arrival
    assert _respiratory("asthma_49m", [OXYGEN]) == [A6A]
    assert _respiratory("asthma_49m", [NIV]) == [A6A]  # NIV counts as breathing on his own


def test_the_intubated_49m_reads_a6b_by_his_state_not_by_the_intubation_or_the_drug():
    assert _respiratory("asthma_49m", [ETOMIDATE]) == [A6B]
    # Ketamine lowers the engine's obstruction: the examination says that improved state (A-6), not A-6b.
    assert _respiratory("asthma_49m", [KETAMINE]) == [A6]


def test_the_49m_pneumothorax_decompression_and_real_improvement():
    seen = _respiratory("asthma_49m", [HIGH_PRESSURE, "Reassess in 15 minutes.", DECOMPRESS, BRONCHODILATOR])
    assert seen == [A6B, A7_49M, A8A, A8_IMPROVED]


def test_the_24f_reads_as_before():
    assert _respiratory("asthma_24f", [OXYGEN]) == [A6]
    assert _respiratory("asthma_24f", [ETOMIDATE]) == [A6]
    assert _respiratory("asthma_24f", [HIGH_PRESSURE, "Reassess in 15 minutes.", DECOMPRESS, BRONCHODILATOR]) == [
        A6, A7, A8_A6, A8_IMPROVED]
    assert _respiratory("asthma_24f", [BRONCHODILATOR]) == [A5]


def test_the_examination_follows_the_obstruction_index_against_its_arrival_value():
    encounter = acceptance.Encounter("asthma_49m")
    encounter.order(BRONCHODILATOR)
    f = encounter.state["family_state"]
    assert f["obstruction"] - f["bronchodilation"] - _airway_relaxation(f) < 1.0
    assert examination_finding(encounter.state, "Respiratory") == A5


# --- A-9 to A-11 -------------------------------------------------------------------------------------

@pytest.mark.parametrize("variant", ["opioid_35m", "opioid_67f"])
def test_the_opioid_rate_says_whose_it_is(variant):
    arrival = acceptance.Encounter(variant)
    arrival.order("Reassess in 2 minutes.")
    shallow = current_findings(arrival.state)["Respiratory"]
    assert shallow.startswith("Respiratory rate ") and shallow.endswith("/min; breaths remain shallow.")
    assert " /min" not in shallow
    assisted = acceptance.Encounter(variant)
    assisted.order("Start bag-mask ventilation. Reassess in 5 minutes.")
    assert current_findings(assisted.state)["Respiratory"] == (
        f"Respiratory rate {assisted.state['observable']['respiratory_rate']}/min, provided by the assisted "
        "ventilation currently in progress.")
    reversed_ = acceptance.Encounter(variant)
    reversed_.order("Give naloxone 0.4 mg IV. Reassess in 10 minutes.")
    deeper = current_findings(reversed_.state)["Respiratory"]
    assert deeper == (f"Respiratory rate {reversed_.state['observable']['respiratory_rate']}/min; spontaneous breaths "
                      "have greater depth."), deeper


# --- TD-84 -------------------------------------------------------------------------------------------

@pytest.fixture
def approved_narrative():
    language.set_narrative({})
    case_text._INSTALLED.clear()
    case_text.install(None, now=0)
    yield
    language.set_narrative({})
    case_text._INSTALLED.clear()


@pytest.mark.parametrize("variant, rest_en, spanish", [
    ("opioid_35m", "Brief bilateral withdrawal to firm stimulation.",
     "Pupilas pequeñas y reactivas, y retiro bilateral breve ante un estímulo firme."),
    ("opioid_67f", "Briefly withdrawing both arms to a firm stimulus.",
     "Pupilas pequeñas y reactivas, retira brevemente ambos brazos ante un estímulo firme."),
])
def test_the_opioid_pupils_read_the_same_in_english_and_spanish(variant, rest_en, spanish, approved_narrative):
    encounter = acceptance.Encounter(variant)
    english = examination_finding(encounter.state, "Neurological")
    assert english.endswith(" Pupils are small and reactive. " + rest_en), english
    assert language.examination(english, "es", case=variant).endswith(" " + spanish)
    # After naloxone the engine models no change of the pupils: the case's own finding stands.
    encounter.order("Give naloxone 0.4 mg IV. Reassess in 10 minutes.")
    assert "Pupils are small and reactive." in examination_finding(encounter.state, "Neurological")


@pytest.mark.parametrize("variant", ["hypoglycemia_28m", "hypoglycemia_76f", "hypoglycemia_54m_thiamine"])
def test_other_pupils_read_as_before(variant, approved_narrative):
    english = examination_finding(acceptance.Encounter(variant).state, "Neurological")
    assert english.endswith(" Pupils are equal and reactive.")
    assert language.examination(english, "es", case=variant).endswith(" Pupilas isocóricas y reactivas.")
