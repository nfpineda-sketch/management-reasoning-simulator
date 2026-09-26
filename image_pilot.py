"""The first real images of the bank: one mature family, three people, a few states (2026-09-26).

Faculty request of 2026-09-26: prove the circuit with a small batch before
anything larger, reviewing each batch before the next. Hypoglycemia is the
family with the most review behind it (its catalogue, its battery and the
faculty magnitudes of 2026-09-20).

Every state below is one the engine produces, found by playing the family's
battery on every configuration of its catalogue (``docs/IMAGENES_PACIENTE.md``):
across twelve configurations the family shows seven visible states, none with
a device. The mask state is the one exception, added to see a device appear and
be removed on a real photograph: it is what the engine shows after
"Oxígeno por mascarilla de reservorio a 15 L/min" is executed for the
54-year-old, who is obtunded by then. Nothing here changes a case.

The three people differ in sex, age band and skin tone, and each is compatible
with the case they stand for. None of them belongs to this family: the
selection may draw them for any family whose case they fit.
"""
from __future__ import annotations

PILOT_ID = "piloto-hipoglicemia-2026-09-26"
FAMILY = "hypoglycemia"

_BASE = {"work_of_breathing": "normal", "skin_color": "mild pallor", "mottling": False,
         "respiratory_support": "none"}

STATES = {
    # After dextrose, in every configuration and every battery script.
    "recovered": {**_BASE, "mental_status": "alert", "expression": "neutral", "diaphoresis": "absent"},
    # Arrival of the 54-year-old and the 76-year-old.
    "drowsy_mild_sweat": {**_BASE, "mental_status": "drowsy", "expression": "uncomfortable",
                          "diaphoresis": "mild"},
    # Arrival of the 28-year-old.
    "drowsy_marked_sweat": {**_BASE, "mental_status": "drowsy", "expression": "uncomfortable",
                            "diaphoresis": "marked"},
    # Untreated, a few minutes later (54-year-old and 76-year-old).
    "obtunded_mild_sweat": {**_BASE, "mental_status": "obtunded", "expression": "passive",
                            "diaphoresis": "mild"},
    # The same, with the non-rebreather mask the resident ordered.
    "obtunded_mild_sweat_mask": {**_BASE, "mental_status": "obtunded", "expression": "passive",
                                 "diaphoresis": "mild", "respiratory_support": "non-rebreather mask"},
}

# In order. The anchor of each person is made by the first job that needs it.
PLAN = (
    {"batch": 1, "identity": "V22", "case": "hypoglycemia_54m_thiamine", "state": "drowsy_mild_sweat"},
    {"batch": 2, "identity": "V22", "case": "hypoglycemia_54m_thiamine", "state": "obtunded_mild_sweat"},
    {"batch": 2, "identity": "V22", "case": "hypoglycemia_54m_thiamine", "state": "obtunded_mild_sweat_mask"},
    {"batch": 2, "identity": "V22", "case": "hypoglycemia_54m_thiamine", "state": "recovered"},
    # Reduced after batch 2 (the mask retry's tool error): the arrival of two more people, to see
    # identity and state on a darker skin tone, a woman and another age. Their recovery waits.
    {"batch": 3, "identity": "V18", "case": "hypoglycemia_28m", "state": "drowsy_marked_sweat"},
    {"batch": 3, "identity": "V11", "case": "hypoglycemia_76f", "state": "drowsy_mild_sweat"},
    {"batch": 4, "identity": "V18", "case": "hypoglycemia_28m", "state": "recovered"},
    {"batch": 4, "identity": "V11", "case": "hypoglycemia_76f", "state": "recovered"},
)


def items(batch=None):
    return [item for item in PLAN if batch is None or item["batch"] == batch]


def contract(item):
    return dict(STATES[item["state"]])
