"""Pulmonary congestion inside a generated case (faculty decision 2026-09-20).

Seventh and thinnest mechanism, and deliberately so. The shared core already
models congestion: it has ``pulmonary_congestion`` as a driver, volume worsens it,
and oxygen, noninvasive ventilation, nitroglycerin and furosemide are native
actions the core answers to. Building a second congestion model on top would
double count, which is the lesson the dextrose ampoule taught: the monitor read
230 for a patient at 130.

So this mechanism adds only what the core has no answer for, and says so:

- the intravenous nitroglycerin **bolus**, which the bank invented for this
  teaching and which no native action covers;
- the declaration itself, which authorises the bolus and states the case's intent.

Everything else, including the fall in pressure of a nitroglycerin infusion, the
recruitment of noninvasive ventilation and the harm of volume, stays with the
shared core.
"""
from family_engine import EDEMA

MECHANISM_ACTIONS = frozenset({"nitroglycerin_bolus"})

# The bolus is a reserve that decays; its pressure effect enters as a delta.
SBP_PER_MCG = .012              # 2000 mcg gives about 24 mmHg at the peak
SBP_FLOOR = -30.0
CONGESTION_RELIEF_PER_MCG = .00004   # ...and it unloads the lung while it lasts
SPO2_PER_RELIEF = 14.0
RR_PER_RELIEF = 16.0


def spec(state):
    case = state.get("encounter_spec", {}).get("clinical_case", {})
    return case.get("engine", {}).get("pulmonary_congestion")


def step(state):
    """Decay the bolus reserve. The core owns everything else."""
    if spec(state) is None:
        return None
    import math
    f = state["family_state"]
    pool = float(f.get("nitro_bolus_pool") or 0)
    if pool:
        pool *= math.exp(-1 / EDEMA["nitro_bolus_tau_min"])
        f["nitro_bolus_pool"] = 0.0 if pool < 1 else pool
        f.setdefault("congestion_relieved", 0.0)
        f["congestion_relieved"] = min(1.0, f["congestion_relieved"] + pool * CONGESTION_RELIEF_PER_MCG)
    return None


def generated_effects(state):
    """(sbp, dbp, spo2, respiratory_rate) from the bolus and what it unloaded."""
    if spec(state) is None:
        return (0.0,) * 4
    f = state["family_state"]
    pool = float(f.get("nitro_bolus_pool") or 0)
    relieved = float(f.get("congestion_relieved") or 0)
    sbp = max(SBP_FLOOR, -SBP_PER_MCG * pool)
    return sbp, sbp * .48, SPO2_PER_RELIEF * relieved, -RR_PER_RELIEF * relieved
