"""What the patient's breathing looks like, recomputed from what is driving it.

Faculty decision 9 of 2026-09-21, from the full bank review. The proportional
scale reached only the pneumonia, so a thrombolysed pulmonary embolism whose
rate fell from 32 to 29 and whose saturation rose to 95 still reported the words
the case had been written with. The decision was that no evolving clinical
descriptor may stay anchored to the authoring text, and that the determinants
belong to each pathophysiology rather than to one generic variable.

Three things are kept apart, as the decision asks:

  * **the respiratory load**, which is what each family's own physiology is
    doing to the lung, the circulation or the airway;
  * **the visible effort**, which is what this module reports;
  * **ventilatory efficacy**, which the rate, the gases and the mechanics carry.

They come apart at the end: a patient whose load stays high for long enough
tires, and the effort that can be seen falls while the load does not. That
trajectory is reported as exhaustion, never as a lower rung of the same ladder.
"""

LEVELS = ("Normal", "Mildly increased", "Moderately increased", "Markedly increased", "Severe")
# The words the decision asked for: fatigue or ineffective breathing, never a
# lower rung of the same ladder, which would read as improvement.
EXHAUSTED = "Exhausted: shallow and ineffective effort"
# The word the case was authored with, mapped onto the scale.
INDEX = {"normal": 0, "mildly increased": 1, "increased": 2, "moderately increased": 2,
         "markedly increased": 3, "severe": 4}

# Levels of visible effort per unit of that family's load. The pneumonia keeps
# the value faculty set on 2026-09-21; the others are stated here for the first
# time and are deliberately coarser, because their load moves further.
LEVELS_PER_UNIT = {
    "pneumonia": 6.0, "pulmonary_edema": 3.0, "asthma": 3.0,
    "pulmonary_embolism": 4.0, "gi_bleed": 3.0, "acs": 3.0, "hypoglycemia": 3.0,
}
EXHAUSTION_LOAD = 1.25      # the load a patient cannot carry indefinitely
EXHAUSTION_MIN = 25         # minutes of carrying it before the effort falls


def load_index(baseline_word):
    return INDEX.get(str(baseline_word or "").lower(), 2)


def count_minute(f, supported):
    """One minute of the load the patient is carrying, for the exhaustion clock."""
    load = float(f.get("respiratory_load") or 1.0)
    if supported or load < EXHAUSTION_LOAD:
        f["high_load_min"] = 0
    else:
        f["high_load_min"] = int(f.get("high_load_min", 0)) + 1


def exhausted(f, supported):
    return not supported and int(f.get("high_load_min", 0)) >= EXHAUSTION_MIN


def describe(family, baseline_word, load, f=None, supported=False):
    """The effort to report, from this family's load and the authored word."""
    if f is not None and exhausted(f, supported):
        return EXHAUSTED
    index = load_index(baseline_word)
    per_unit = LEVELS_PER_UNIT.get(family, 3.0)
    position = int(max(0, min(len(LEVELS) - 1, round(index + (load - 1) * per_unit))))
    # While the patient is where the case left them, the case's own wording stands.
    return str(baseline_word) if position == index else LEVELS[position]
