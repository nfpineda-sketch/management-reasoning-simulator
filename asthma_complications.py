"""Barotrauma and the timing of intubation in severe asthma (faculty, 2026-09-19).

Faculty statement: the patient must not be intubated too early, nor too late; it
is a difficult balance. And the ventilated asthmatic is the patient in whom a
pneumothorax appears, which is the diagnosis that competes with dynamic
hyperinflation when the pressure falls.

Pneumothorax here is barotrauma, not chance: sustained plateau pressure above the
limit accumulates until the lung tears. It then behaves as a tension
pneumothorax, so the pressure falls, the saturation falls and the peak pressure
jumps, while examination and POCUS lose sliding on that side. Needle
decompression or a chest tube resolves it.

Timing is judged at the moment of intubation, from the patient the resident had
in front of them. Intubating someone who is still alert, oxygenating and
improving is premature: spontaneous ventilation is lost and the physiology
becomes the ventilator's. Leaving an exhausted, obtunded, hypoxaemic patient
unintubated is late: the price is paid after intubation, as hypotension and
lactate.

Teaching magnitudes pending faculty review.
"""
import math

# Barotrauma
PLATEAU_SAFE_CMH2O = 30.0
BAROTRAUMA_PER_CMH2O_MIN = .1     # exposure gained per cmH2O above the limit, per minute
BAROTRAUMA_THRESHOLD = 10.0       # 10 minutes at a plateau of 40 tears the lung
TENSION_SBP_DROP = 35.0
TENSION_SPO2_DROP = 12.0
TENSION_PEAK_RISE = 15.0
DECOMPRESSION_RECOVERY_TAU_MIN = 2.0

# Timing of intubation
PREMATURE_SPO2 = 92
PREMATURE_OBSTRUCTION = .85       # residual obstruction already coming down
PREMATURE_SBP_COST = 12.0         # positive pressure without a reason to be there
LATE_MENTAL = {"Drowsy", "Obtunded", "Unresponsive"}
LATE_EFFORT = {"Markedly increased", "Severe"}
LATE_SPO2 = 90
LATE_EXPOSURE_MIN = 15.0          # minutes of exhaustion before intubation that count as late
EXHAUSTION_RECOVERY_PER_MIN = .5  # relief buys the clock back, slowly
FATIGUE_ONSET_MIN = 20.0          # sustained maximal effort starts to fail
FATIGUE_DRIFT_PER_MIN = .0015     # ...and the obstruction then worsens faster
LATE_SBP_DROP = 25.0              # post-intubation hypotension of the exhausted patient
LATE_LACTATE = 2.0
POST_INTUBATION_TAU_MIN = 20.0


def track_exhaustion(f, observable):
    """Count the minutes of failing effort, and let that failure feed back.

    Maximal work with poor oxygenation is what tires the patient; relief buys the
    clock back. Past ``FATIGUE_ONSET_MIN`` the obstruction itself worsens faster,
    which is how an untreated patient reaches drowsiness instead of plateauing.
    """
    if f.get("invasive"):
        return 0.0
    exhausted = (str(observable.get("mental_status")) in LATE_MENTAL
                 or (float(observable.get("spo2", 100)) < LATE_SPO2
                     and str(observable.get("work_of_breathing")) in LATE_EFFORT))
    minutes = f.get("exhausted_min", 0.0) + (1.0 if exhausted else -EXHAUSTION_RECOVERY_PER_MIN)
    f["exhausted_min"] = max(0.0, minutes)
    return FATIGUE_DRIFT_PER_MIN if f["exhausted_min"] >= FATIGUE_ONSET_MIN else 0.0


def intubation_timing(f, observable, obstruction):
    """Classify the moment of intubation: 'premature', 'late' or 'within window'."""
    if f.get("exhausted_min", 0.0) >= LATE_EXPOSURE_MIN:
        return "late"
    if (str(observable.get("mental_status")) == "Alert"
            and float(observable.get("spo2", 0)) >= PREMATURE_SPO2
            and obstruction < PREMATURE_OBSTRUCTION):
        return "premature"
    return "within window"


def apply_intubation_timing(f, timing):
    """Record the judgement and its physiological price."""
    f["intubation_timing"] = timing
    f["intubation_penalty_at"] = f["elapsed"]
    if timing == "premature":
        f["intubation_sbp_penalty"] = PREMATURE_SBP_COST
    elif timing == "late":
        f["intubation_sbp_penalty"] = LATE_SBP_DROP
        f["lactate"] = f.get("lactate", 1.5) + LATE_LACTATE
    else:
        f["intubation_sbp_penalty"] = 0.0


def timing_note(timing):
    if timing == "premature":
        return ("Intubation was performed while the patient was still alert, oxygenating and responding to treatment: "
                "spontaneous ventilation is lost and the airway pressures now govern the circulation.")
    if timing == "late":
        return ("Intubation followed a prolonged period of exhaustion and hypoxaemia: the patient is acidotic and "
                "hypotensive after induction, and needs volume and slower ventilation rather than more pressure.")
    return "Intubation was performed while the patient was failing but still perfusing."


def step(f, mechanics):
    """Accumulate barotrauma and declare the pneumothorax when the lung tears.

    Returns the event text when it happens, and None otherwise.
    """
    if f.get("pneumothorax_at") is not None or mechanics is None:
        return None
    excess = float(mechanics["plateau_cmh2o"]) - PLATEAU_SAFE_CMH2O
    if excess <= 0:
        return None
    f["barotrauma_exposure"] = f.get("barotrauma_exposure", 0.0) + excess * BAROTRAUMA_PER_CMH2O_MIN
    if f["barotrauma_exposure"] < BAROTRAUMA_THRESHOLD:
        return None
    f["pneumothorax_at"] = f["elapsed"]
    f["pneumothorax_side"] = "right"
    return ("Sudden deterioration on the ventilator: the blood pressure and the saturation fall while the peak airway "
            "pressure rises. Breath sounds are absent on the right and the right chest is hyper-resonant. "
            "Sustained plateau pressures above 30 cmH2O have torn the lung: this is a tension pneumothorax, not "
            "dynamic hyperinflation.")


def tension_fraction(f):
    """How much of the tension is still present: 1.0 untreated, 0 after decompression."""
    if f.get("pneumothorax_at") is None:
        return 0.0
    treated = f.get("pneumothorax_decompressed_at")
    if treated is None:
        return 1.0
    return math.exp(-(f["elapsed"] - treated) / DECOMPRESSION_RECOVERY_TAU_MIN)


def intubation_penalty(f):
    """The fading price of intubating outside the window."""
    penalty = f.get("intubation_sbp_penalty", 0.0)
    if not penalty:
        return 0.0
    since = f["elapsed"] - f.get("intubation_penalty_at", f["elapsed"])
    return penalty * math.exp(-since / POST_INTUBATION_TAU_MIN)
