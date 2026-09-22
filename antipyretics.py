"""Paracetamol, the NSAIDs and the fever they do or do not bring down.

Faculty decision 14 of 2026-09-21, from the full bank review. None of these
drugs existed, and the pneumonia's fever answered nothing by design. The
decision asked for the ordinary ward drugs, with the route changing the onset,
with a reduction that is gradual and variable rather than a normal temperature
by return of post, and with the precautions of an NSAID actually checked.

Comfort is not cure: the fever comes back while the infection is unresolved, and
nothing here treats the infection.
"""

# (maximum temperature fall in °C, maximum pain relief in points, IV onset).
AGENTS = {
    "paracetamol": {"max_drop_c": 1.1, "max_relief": 2.0, "onset_min": 20, "nsaid": False,
                    "reference_mg": 1000, "max_mg": 4000},
    "ibuprofen": {"max_drop_c": 1.2, "max_relief": 2.5, "onset_min": 25, "nsaid": True,
                  "reference_mg": 600, "max_mg": 2400},
    "ketorolac": {"max_drop_c": .6, "max_relief": 3.0, "onset_min": 20, "nsaid": True,
                  "reference_mg": 30, "max_mg": 120},
    "metamizole": {"max_drop_c": 1.2, "max_relief": 2.5, "onset_min": 20, "nsaid": False,
                   "reference_mg": 1000, "max_mg": 4000},
}
ORAL_EXTRA_ONSET_MIN = 20     # the route changes when it works, not whether
DURATION_MIN = 240            # and the effect fades over about four hours
NO_FEVER_BELOW_C = 37.5       # an antipyretic does not make anybody cold

# What an NSAID has to be checked against before it is given.
CREATININE_CAUTION = 1.5
PERFUSION_CAUTION_BURDEN = .15    # a circulation that is not perfusing a kidney
# Every reason is a full clause, so any combination of them reads as a sentence.
NSAID_CAUTION = ("{agent} is an NSAID and this patient {reason}. The analgesia is real and so is "
                 "the risk; the decision is whether this is the drug for this patient.")
DUPLICATE_NSAID = ("{agent} on top of {other}: two NSAIDs are one class. The second adds the risks "
                   "and very little of the effect.")


def _share(dose_mg, agent):
    spec = AGENTS[agent]
    return min(1.0, float(dose_mg or 0) / spec["reference_mg"])


def record_dose(state, agent, dose_mg, route):
    """Remember the dose, and return the caution it deserves, or None."""
    f = state["family_state"]
    given = f.setdefault("antipyretic_doses", [])
    spec = AGENTS.get(agent)
    if spec is None:
        return None
    onset = spec["onset_min"] + (ORAL_EXTRA_ONSET_MIN if route == "PO" else 0)
    given.append({"agent": agent, "mg": float(dose_mg or 0), "route": route,
                  "at": f["elapsed"], "onset": onset, "share": _share(dose_mg, agent)})
    if not spec["nsaid"]:
        return None
    other = next((d["agent"] for d in given[:-1] if AGENTS[d["agent"]]["nsaid"] and d["agent"] != agent), None)
    if other:
        return DUPLICATE_NSAID.format(agent=agent, other=other)
    creatinine = float((state.get("encounter_spec", {}).get("clinical_case", {})
                        .get("investigations", {}).get("basic_labs", {})
                        .get("result", {}) or {}).get("creatinine_mg_dl") or 1.0)
    burden = max(0.0, float(f.get("circulation", 1.0)) - 1.0)
    reasons = []
    if creatinine >= CREATININE_CAUTION:
        reasons.append(f"has a creatinine of {creatinine:g} mg/dL")
    if burden >= PERFUSION_CAUTION_BURDEN:
        reasons.append("is not perfusing well")
    if state.get("engine_family") == "gi_bleed":
        reasons.append("is bleeding from the gut")
    if not reasons:
        return None
    return NSAID_CAUTION.format(agent=agent, reason=" and ".join(reasons))


def total_mg(f, agent):
    return sum(d["mg"] for d in f.get("antipyretic_doses", ()) if d["agent"] == agent)


def _active(f):
    drop = relief = 0.0
    for dose in f.get("antipyretic_doses", ()):
        spec = AGENTS[dose["agent"]]
        since = f["elapsed"] - dose["at"] - dose["onset"]
        if since < 0:
            continue
        # Straight in over the onset, then fading over the duration.
        fade = max(0.0, 1 - since / DURATION_MIN)
        drop += spec["max_drop_c"] * dose["share"] * fade
        relief += spec["max_relief"] * dose["share"] * fade
    return drop, relief


def temperature(f, baseline_c):
    """The temperature now: fever comes down, normal temperature does not."""
    drop, _ = _active(f)
    if baseline_c <= NO_FEVER_BELOW_C:
        return baseline_c
    return round(max(NO_FEVER_BELOW_C, baseline_c - min(drop, baseline_c - NO_FEVER_BELOW_C)), 1)


def relief(f):
    return _active(f)[1]
