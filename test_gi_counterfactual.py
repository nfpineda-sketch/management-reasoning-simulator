"""P3-197: the shadow-vs-proposed-authority counterfactual harness. TEST-SIDE ANALYSIS; it only reads.

A legacy-AUTHORITATIVE encounter ran with the shadow beside it (the shadow only observes, as it always does). Per minute, for each candidate
authority domain, this compares what the legacy engine SHOWED with what the selected common-core snapshot WOULD have authored. Nothing is
committed to the encounter: ``COMMON_CORE_RUNTIME_AUTHORITY`` stays False, the authority gate is never opened, and the legacy values below are
the ones the resident would have seen.

Classification of a difference (declared here, BEFORE the series was read; it uses structure and never a numeric clinical tolerance, which the
project has not defined and the assistant does not invent):

* ``MATCH``                       the two values are equal (at the display's own precision).
* ``STRUCTURAL_CONTRADICTION``    the two engines disagree on a structural fact: the pulse, or the DIRECTION a quantity moved (one engine moved it up
                                  where the other moved it down), read since the arrival before the first order and since the first order's start
                                  after it -- so a deterioration is judged against the arrival and a treatment response against the moment of the order.
* ``POTENTIAL_EDUCATIONAL_PROBLEM`` a categorical difference a resident would SEE as a different patient: the consciousness word differs by two or
                                  more bands, or one side reads Alert and the other does not.
* ``EXPECTED_MECHANISTIC_DIFFERENCE`` every other difference between two architectures that move the quantity the same way: a timing or a magnitude
                                  difference whose declared source is the engines' different laws.
* ``UNRESOLVED``                  no comparable value (one side undefined, or the legacy engine has no counterpart, as for the collapse state).

A large difference is NOT a failure and is never tuned away (FD-GI-03).
"""
from __future__ import annotations

from typing import Mapping, Sequence

import test_gi_snapshot_analysis as an

MATCH, STRUCTURAL, EDUCATIONAL, EXPECTED, UNRESOLVED = ("MATCH", "STRUCTURAL_CONTRADICTION", "POTENTIAL_EDUCATIONAL_PROBLEM",
                                                         "EXPECTED_MECHANISTIC_DIFFERENCE", "UNRESOLVED")
CODE = {MATCH: "M", STRUCTURAL: "S", EDUCATIONAL: "P", EXPECTED: "E", UNRESOLVED: "U"}
CLASS_OF = {value: key for key, value in CODE.items()}
VALID, NOT_COMPARABLE = "VALID", "NOT_COMPARABLE"
#: The comparison uses the display's own precision (``clinical_core.comparison`` rounds the core to the integer or tenth the legacy shows).
#: The repository's own numerical-noise bound for an exact comparison (``clinical_core.comparison.FLOAT_NOISE``); it is not a clinical tolerance.
FLOAT_NOISE = 1e-9
INTEGER_DISPLAY = ("sbp", "dbp", "map", "hr", "spo2", "respiratory_rate")
TENTH_DISPLAY = ("crt", "lactate")

#: domain -> (kind, legacy key, candidate key, source of the candidate, the legacy source). Every key is one that a recorded capture carries.
DOMAINS = {
    "sbp": ("numeric", "sbp", "sbp", "common core: output x tone pressure coordinate of the shared blood volume (V, P, T)",
            "legacy family engine: display linear in its circulation, with a floor"),
    "dbp": ("numeric", "dbp", "dbp", "common core: the same pressure coordinate", "legacy family engine: display linear in its circulation, with a floor"),
    "map": ("numeric", "map", "map", "common core: derived from its own pressures (the display derives the mean from the two it shows)",
            "legacy family engine / display: (sbp + 2 dbp) / 3 of the legacy pressures"),
    "hr": ("numeric", "hr", "monitor_rate_bpm", "common core: monitor rate from the sympathetic drive of the debt and the pressure",
           "legacy family engine: rate linear in its circulation, minus the hemostasis relief"),
    "spo2": ("numeric", "spo2", "spo2", "common core: the oxygenation chain (FiO2, lung and gas-exchange state)", "legacy family engine: authored base with oxygen terms"),
    "respiratory_rate": ("numeric", "respiratory_rate", "respiratory_rate", "common core: respiratory drive of the acid burden and the demand",
                         "legacy family engine: rate from circulation and state"),
    "lactate": ("numeric", "lactate_lab", "lactate", "common core: lactate of the oxygen-delivery debt (D)", "legacy: the lab the engine would report now"),
    "hb": ("numeric", "hemoglobin", "hb", "common core: arrival value and dilution by delivered volume (exact by construction)",
           "legacy family engine: arrival value and dilution by delivered volume"),
    "crt": ("numeric", "crt", "crt_s", "common core: capillary refill from the pump and tone state", "legacy family engine: linear in its circulation"),
    "consciousness_category": ("ordinal", "legacy_level", "category_index", "common core: PHASE2_AMENDMENT_2 composite (F, collapse) under the selected snapshot",
                               "legacy family engine: mental-status ladder on its own pressure and oxygen terms"),
    "pulse_present": ("pulse", "pulse_present", "pulse_present", "common core: rhythm and pulse state", "legacy family engine: pulse flag"),
    "collapse_state": ("collapse", None, "collapse_state_index", "common core: PHASE2_AMENDMENT_2 collapse predicate under the selected snapshot",
                       "legacy family engine: no collapse field (only the arrest flag)"),
}


def _round_candidate(domain: str, value):
    if value is None:
        return None
    if domain in INTEGER_DISPLAY:
        return int(round(value))
    if domain in TENTH_DISPLAY:
        return round(float(value), 1)
    return float(value) if domain == "hb" else value


def _sign(value: float, reference: float) -> int:
    difference = value - reference
    return 0 if abs(difference) <= 1e-9 else (1 if difference > 0 else -1)


def by_minute(rows: Sequence[Mapping]) -> dict:
    return {row["minute"]: row for row in rows}


def aligned_minutes(captured: Mapping) -> list:
    legacy, session = by_minute(captured["legacy"]), by_minute(captured["session"])
    return sorted(set(legacy) & set(session))


def values_at(captured: Mapping, minute: int, domain: str, witness: str = "CENTER_REFERENCE"):
    """(legacy value, candidate value) of a domain at a minute: the legacy engine's own sample and the shadow's reading, never anything written."""
    kind, legacy_key, candidate_key, _, _ = DOMAINS[domain]
    legacy, session = by_minute(captured["legacy"])[minute], by_minute(captured["session"])[minute]
    if kind in ("ordinal", "collapse"):
        row = by_minute(captured["witnesses"][witness]).get(minute)
        candidate = None if row is None else row[candidate_key]
    else:
        candidate = session.get(candidate_key)
    left = None if legacy_key is None else legacy.get(legacy_key)
    if domain == "map" and left is None and legacy.get("sbp") is not None and legacy.get("dbp") is not None:
        left = int(round((legacy["sbp"] + 2.0 * legacy["dbp"]) / 3.0))
    if domain == "map" and candidate is None and session.get("sbp") is not None and session.get("dbp") is not None:
        candidate = (session["sbp"] + 2.0 * session["dbp"]) / 3.0
    if kind == "collapse":
        left = None
    return left, _round_candidate(domain, candidate)


def classify_minute(domain: str, legacy, candidate, *, legacy_arrival, candidate_arrival, legacy_pulse=True) -> str:
    kind = DOMAINS[domain][0]
    if kind == "collapse":
        # the legacy engine has no collapse state: an absent state is the only thing it can be compared with
        return MATCH if candidate == 0 and legacy_pulse else UNRESOLVED
    if legacy is None or candidate is None:
        return UNRESOLVED
    if kind == "pulse":
        return MATCH if bool(legacy) == bool(candidate) else STRUCTURAL
    if legacy == candidate or (domain == "hb" and abs(legacy - candidate) <= FLOAT_NOISE):
        return MATCH
    moved_legacy, moved_candidate = _sign(legacy, legacy_arrival), _sign(candidate, candidate_arrival)
    if moved_legacy * moved_candidate == -1:
        return STRUCTURAL
    if kind == "ordinal":
        if abs(candidate - legacy) >= 2 or (legacy == 0) != (candidate == 0):
            return EDUCATIONAL
    return EXPECTED


def classify_columns(domain: str, minutes: Sequence[int], left: Sequence, right: Sequence, first_order: int | None,
                     pulses: Sequence[bool]) -> str:
    """The class code of every aligned minute of one domain, from its two columns alone (so a stored record can be re-derived)."""
    before_order = [i for i, minute in enumerate(minutes) if first_order is None or minute <= first_order]
    arrival = next((i for i in range(len(minutes)) if left[i] is not None and right[i] is not None), 0)
    reference_after = before_order[-1] if before_order else arrival
    codes = []
    for index, minute in enumerate(minutes):
        reference = arrival if first_order is None or minute <= first_order else reference_after
        codes.append(CODE[classify_minute(domain, left[index], right[index], legacy_arrival=left[reference],
                                          candidate_arrival=right[reference], legacy_pulse=bool(pulses[index]))])
    return "".join(codes)


def windows_of(minutes: Sequence[int], codes: str, wanted: str) -> list:
    """The contiguous runs of aligned minutes whose class code is in ``wanted``, as [first minute, last minute]."""
    out, start, last = [], None, None
    for minute, code in zip(minutes, codes):
        if code in wanted:
            start = minute if start is None else start
            last = minute
        elif start is not None:
            out.append([start, last])
            start = None
    if start is not None:
        out.append([start, last])
    return out


def compare_run(captured: Mapping, witness: str = "CENTER_REFERENCE") -> dict:
    """Per minute, per candidate domain: the legacy value, the common candidate (the snapshot), the difference, its class and the validity."""
    minutes = aligned_minutes(captured)
    legacy_rows = by_minute(captured["legacy"])
    pulses = [bool(legacy_rows[minute].get("pulse_present", True)) for minute in minutes]
    first_order = captured["orders"][0]["minute"] if captured["orders"] else None
    out = {"case": captured["case"], "scenario": captured["scenario"], "first_order_minute": first_order, "minutes": minutes,
           "legacy_pulse": pulses, "domains": {}}
    for domain, (kind, _, _, candidate_source, legacy_source) in DOMAINS.items():
        left, right = [], []
        for minute in minutes:
            a, b = values_at(captured, minute, domain, witness)
            left.append(a)
            right.append(b)
        codes = classify_columns(domain, minutes, left, right, first_order, pulses)
        differences = [None if None in (a, b) or kind in ("pulse", "collapse") else round(b - a, 4) for a, b in zip(left, right)]
        numeric = [abs(d) for d in differences if d is not None]
        peak = max(range(len(differences)), key=lambda i: abs(differences[i]) if differences[i] is not None else -1.0) if numeric else None
        out["domains"][domain] = {
            "kind": kind, "candidate_source": candidate_source, "legacy_source": legacy_source,
            "legacy": left, "candidate": right, "class_codes": codes,
            "validity": [VALID if a is not None and b is not None else NOT_COMPARABLE for a, b in zip(left, right)].count(VALID),
            "counts": {CLASS_OF[code]: codes.count(code) for code in sorted(set(codes))},
            "mean_abs_difference": round(sum(numeric) / len(numeric), 4) if numeric else None,
            "max_abs_difference": round(max(numeric), 4) if numeric else None,
            "max_difference_minute": None if peak is None else minutes[peak],
            "first_difference_minute": next((m for m, c in zip(minutes, codes) if c != "M"), None),
            "flagged_windows": {"STRUCTURAL_CONTRADICTION": windows_of(minutes, codes, "S"),
                                "POTENTIAL_EDUCATIONAL_PROBLEM": windows_of(minutes, codes, "P"),
                                "UNRESOLVED": windows_of(minutes, codes, "U")},
        }
    return out


def summarise(runs: Sequence[Mapping]) -> dict:
    """Per domain: how many compared minutes fall in each class, over every run, and where each non-trivial class occurs."""
    totals: dict = {}
    where: dict = {}
    for run in runs:
        for domain, item in run["domains"].items():
            counts = totals.setdefault(domain, {})
            for label, count in item["counts"].items():
                counts[label] = counts.get(label, 0) + count
                if label in (STRUCTURAL, EDUCATIONAL, UNRESOLVED):
                    where.setdefault(domain, {}).setdefault(label, []).append(f"{run['case']}/{run['scenario']}")
    return {"minutes_by_class": totals,
            "runs_with_a_flagged_class": {domain: {label: sorted(set(items)) for label, items in found.items()} for domain, found in where.items()}}


COUNTERFACTUAL_FILE = "docs/revision/PHASE3_GI_AUTHORITY_COUNTERFACTUAL.json"
CLASS_DEFINITIONS = {
    MATCH: "the two values are equal at the display's own precision (hemoglobin: within the repository's float-noise bound)",
    STRUCTURAL: "the engines disagree on the pulse, or on the DIRECTION a quantity moved (since the arrival, or since the first order's start after it)",
    EDUCATIONAL: "the consciousness word differs by two or more bands, or one side reads Alert and the other does not",
    EXPECTED: "any other difference between two architectures that move the quantity the same way",
    UNRESOLVED: "no comparable value (one side undefined, or the legacy engine has no counterpart)",
}


def _compact(run: Mapping) -> dict:
    """A run for the record. The columns are kept at full precision, so every class code can be RE-DERIVED from them."""
    return {key: value for key, value in run.items()}


def build_record(captures: Mapping) -> dict:
    """The P3-197 record: every required run (two cases x seven scenarios) and the two extras, compared minute by minute."""
    import runtime_authority as authority
    import runtime_shadow as runtime
    required, extra = {}, {}
    for (case, scenario), captured in sorted(captures.items()):
        target = required if scenario in an.SCENARIOS else extra
        target[f"{case}/{scenario}"] = _compact(compare_run(captured))
    gate = authority.gate({}, environ={}, unsupported=())
    snapshot = __import__("json").load(open(an.SNAPSHOT_FILE, encoding="utf-8"))
    return {
        "counterfactual_version": "P3-197", "snapshot_id": an.SNAPSHOT_ID,
        "snapshot_record_digest": snapshot["immutability"]["record_digest"],
        "what_it_is": "A legacy-authoritative encounter with the shadow beside it. The common values are what the selected snapshot WOULD have authored; "
                      "none is committed to the encounter, and the legacy engine's values are the ones the resident would have seen.",
        "non_interference": {"common_core_runtime_authority": runtime.COMMON_CORE_RUNTIME_AUTHORITY, "authority_gate_granted_without_flags": gate.granted,
                             "gate_refusal_reasons_count": len(gate.reasons)},
        "class_definitions": CLASS_DEFINITIONS, "class_codes": CODE,
        "domains": {domain: {"kind": spec[0], "legacy_key": spec[1], "candidate_key": spec[2], "candidate_source": spec[3], "legacy_source": spec[4]}
                    for domain, spec in DOMAINS.items()},
        "required_runs": required, "extra_runs": extra,
        "summary_required": summarise([captured for captured in required.values()]),
        "summary_extra": summarise([captured for captured in extra.values()]),
    }


def write_record(root: str, captures: Mapping) -> dict:
    import json
    import os
    record = build_record(captures)
    with open(os.path.join(root, COUNTERFACTUAL_FILE), "w", encoding="utf-8") as handle:
        json.dump(record, handle, sort_keys=True, separators=(",", ":"))
    return record
