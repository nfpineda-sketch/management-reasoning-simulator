"""P2I-2P: oxygen delivery and extraction, on synthetic probes and on the P2I-2R findings.

    python -m clinical_core.oxygen_probes [--out <directory outside the repository>]
    python -m clinical_core.oxygen_probes --write <document> --json <probes JSON>

Shadow, offline and read-only. It runs the core with synthetic profiles and contributors and
changes no default, band, registry, golden or rule. The extraction reserves here are
illustrations, never proposals: the physiological value is TBD and the canonical profile keeps
the neutral 1 (the pre-P2I-2P model). Collapse burdens are computed here, from each trajectory,
for two candidate signals with synthetic thresholds; the core's collapse rule stays off.

The delivery index is DO2 over the patient's normal resting DO2, the demand index VO2 demand
over normal resting VO2, and their ratio the supply-to-demand ratio (``derived.oxygen_balance``):
1 at normal extraction; between 1 / reserve and 1 extraction compensates; below 1 / reserve the
demand left unmet is the effective deficit, the only one D integrates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path

from . import calibration, decision_pack, faculty_constraints as fc, lactate_constraints, lactate_slice
from .bands import ARRIVAL, Demand, Drift
from .derived import DEFAULT_PROFILE, derive, effective_delivery, oxygen_balance
from .integration import run
from .state import Anchors

NEUTRAL = Anchors(**ARRIVAL)
MINUTES = 120
TIMES = (0, 15, 30, 60, 90, 120)
#: Illustrations only (normal extraction about a quarter, maximal about 0.5-0.75): not proposals.
SYNTHETIC_RESERVE = 2.5
SYNTHETIC_RESERVES = (2.0, 2.5, 3.0)
#: Synthetic collapse illustration: the existing output-based form, and an oxygen-deficit form.
SYNTHETIC_OUTPUT_THRESHOLD = 0.3
SYNTHETIC_BURDEN_LIMIT = 30.0
P2I2R_RESULTS = Path(__file__).resolve().parent.parent / "docs" / "revision" / "P2I2_lactate_constraints.json"

#: P2I-2P-6: name -> (what it represents, contributors). The neutral healthy arrival of the band probes.
PROBES = {
    "A normal": ("normal delivery, normal demand", ()),
    "B compensated low delivery": ("pump falls 30 % over 30 min, then holds", (Drift("pump", "P", 0, 30, -0.01),)),
    "C delivery crossing the critical region": ("pump falls steadily to 0.2 over 100 min",
                                                (Drift("pump", "P", 0, 100, -0.008),)),
    "D anaemia, output preserved": ("Hb falls 0.07 g/dL per min (13 to 4.6 g/dL)", (Drift("hb", "hb", 0, 120, -0.07),)),
    "E low output, Hb preserved": ("pump falls to 0.3 over 60 min, then holds", (Drift("pump", "P", 0, 60, -0.0117),)),
    "F low output and anaemia": ("pump to 0.6 and Hb to 7.8 g/dL over 40 min",
                                 (Drift("pump", "P", 0, 40, -0.01), Drift("hb", "hb", 0, 40, -0.13))),
    "G high demand, delivery preserved": ("demand x 1.5 throughout", (Demand("demand", 0, MINUTES, 1.5),)),
    "H resuscitation restores delivery": ("pump falls to 0.25 by 30 min, restored to 1.0 by 60 min",
                                          (Drift("fall", "P", 0, 30, -0.025), Drift("restore", "P", 30, 60, 0.025))),
    "I transfusion raises Hb and delivery": ("Hb falls to 4.6 g/dL by 30 min; +2 g/dL from 45 to 85 min",
                                             (Drift("bleed", "hb", 0, 30, -0.28), Drift("transfuse", "hb", 45, 85, 0.05))),
    "J severe sustained critical deficit": ("pump falls to 0.16 by 15 min and stays", (Drift("pump", "P", 0, 15, -0.056),)),
}


def _profile(reserve: float):
    return replace(DEFAULT_PROFILE, oxygen_extraction_reserve=reserve)


def _burdens(rows: list) -> dict:
    """Two candidate collapse signals, accumulated per minute from the trajectory (synthetic)."""
    output = deficit = 0.0
    reached = {"output": None, "oxygen_deficit": None}
    for row in rows:
        output += max(0.0, SYNTHETIC_OUTPUT_THRESHOLD - row["output_rel"]) / SYNTHETIC_OUTPUT_THRESHOLD
        deficit += row["effective_deficit"] / row["demand"]
        row["burden_output"], row["burden_oxygen_deficit"] = output, deficit
        for name, value in (("output", output), ("oxygen_deficit", deficit)):
            if reached[name] is None and value >= SYNTHETIC_BURDEN_LIMIT:
                reached[name] = row["minute"]
    return reached


def trajectory_rows(anchors: Anchors, contributors: tuple, reserve: float, minutes: int = MINUTES) -> tuple:
    """Every minute of a core run, read through the oxygen balance at ``reserve``."""
    profile = _profile(reserve)
    result = run(anchors, contributors, minutes, profile)
    rows = []
    for state in result.states:
        derived = derive(state, anchors, profile)
        delivery = effective_delivery(derived.delivery_rel, anchors)
        balance = oxygen_balance(delivery, state.aux.oxygen_demand, reserve)
        rows.append({"minute": state.minute, "output_rel": derived.output_rel, "hb": state.hb, "delivery": delivery,
                     "demand": balance.demand, "supply_ratio": balance.supply_ratio, "state": balance.state,
                     "required_extraction": balance.required_extraction, "effective_deficit": balance.effective_deficit,
                     "D": state.D, "lactate": derived.lactate, "sbp": derived.sbp})
    return rows, _burdens(rows)


def _direction(before: float, after: float) -> str:
    return "rises" if after > before + 1e-9 else "falls" if after < before - 1e-9 else "flat"


def probe(name: str, reserve: float) -> dict:
    what, contributors = PROBES[name]
    rows, reached = trajectory_rows(NEUTRAL, contributors, reserve)
    points = {str(minute): rows[minute] for minute in TIMES}
    lactate = [points[str(minute)]["lactate"] for minute in TIMES]
    first_critical = next((row["minute"] for row in rows if row["state"] == "CRITICAL"), None)
    return {"what": what, "reserve": reserve, "points": points,
            "lactate_direction": [_direction(a, b) for a, b in zip(lactate, lactate[1:])],
            "states_seen": sorted({row["state"] for row in rows}), "first_critical_minute": first_critical,
            "max_D": max(row["D"] for row in rows), "collapse_limit_reached": reached}


# P2I-2P-7: the P2I-2R findings, revisited -------------------------------------------------------

#: How a synthetic reserve meets the GI arrival band (P2I-2P-7). FIXED keeps each candidate's
#: arrival_delivery_ratio as a DO2 index over normal (reading C); RE_ANCHORED reads the band as it
#: was designed, in units of the minimum adequate (critical) delivery (reading B: "at or below
#: adequacy; 1 is a compensated arrival"), so the DO2 index over normal is ratio / reserve.
FIXED, RE_ANCHORED = "fixed band", "re-anchored band"


def _core_rows(case: str, candidate, scenario: str, reserve: float, reading: str = FIXED) -> list:
    """One engine-produced GI run at ``reserve``, read minute by minute through the oxygen balance."""
    ratio = calibration.case_values(case, candidate)["arrival_delivery_ratio"]
    # The band's reading is always stated for a reserve other than 1 (lactate_slice refuses otherwise).
    extra = None if reserve == 1.0 else {"arrival_delivery_ratio": ratio / reserve if reading == RE_ANCHORED else ratio}
    run_ = lactate_slice.slice_run(case, candidate, scenario, keep_states=True, case_extra=extra,
                                   profile_extra={"oxygen_extraction_reserve": reserve})
    anchors, profile = run_["anchors"], run_["profile"]
    controlled = lactate_constraints._controlled_at(run_["states"][-1])
    rows = []
    for state in run_["states"]:
        derived = derive(state, anchors, profile)
        delivery = effective_delivery(derived.delivery_rel, anchors)
        balance = oxygen_balance(delivery, state.aux.oxygen_demand, reserve)
        rows.append({"minute": state.minute, "output_rel": derived.output_rel, "hb_ratio": state.hb / anchors.hb,
                     "delivery": delivery, "demand": balance.demand, "state": balance.state,
                     "effective_deficit": balance.effective_deficit, "D": state.D, "lactate": derived.lactate,
                     "sbp": derived.sbp, "V": state.V, "arrival_ratio": anchors.arrival_delivery_ratio,
                     "bleeding": controlled is None or state.minute < controlled})
    return rows


def critical_declines(rows: list, settings: dict) -> list:
    """Finding 1's probe at any reserve: every window of active bleeding with an effective oxygen
    deficit at every minute (CRITICAL), at least ``sustained_min`` long, that holds a substantial
    sustained lactate decline (FD-LAC-06's reading, P2I-2R settings). With reserve 1 CRITICAL is
    delivery below demand, exactly P2I-2R's inadequate delivery. For each first decline: whether
    delivery improved across it, and whether the effective deficit fell across it and between
    every pair of consecutive reassessment points inside it (the recovering state of the FD-LAC-06
    faculty decision, read by direction only)."""
    trajectory = fc.Trajectory(*(tuple(row[name] for row in rows) for name in ("lactate", "D", "delivery", "demand")))
    found = []
    for first, last in fc.spans(trajectory, lambda minute: rows[minute]["bleeding"]
                                and rows[minute]["state"] == "CRITICAL"):
        if last - first < settings["sustained_min"]:
            continue
        declines = fc.sustained_declines(trajectory, first, last, settings)
        if declines:
            early, late = declines[0]
            points = fc.reassessments(early, late, settings)
            found.append({"window": [first, last], "first_decline": [early, late],
                          "delivery_improving": rows[late]["delivery"] > rows[early]["delivery"],
                          "deficit_falling": rows[late]["effective_deficit"] < rows[early]["effective_deficit"],
                          "deficit_falling_each_interval": all(
                              rows[b]["effective_deficit"] < rows[a]["effective_deficit"]
                              for a, b in zip(points, points[1:]))})
    return found


def frozen_survivors() -> list:
    """The 72 candidates of the P2I-2R results as committed (filter digest RESULTS_PENDING_REFILTER):
    read, not refiltered."""
    data = json.loads(P2I2R_RESULTS.read_text(encoding="utf-8"))
    if data["filter_digest"] != lactate_constraints.RESULTS_PENDING_REFILTER["filter_digest"]:
        raise AssertionError("the committed P2I-2R results are not the ones recorded as pending refilter")
    return list(data["faculty_constrained_region"])


def _same_dynamics(rows: list, reference: list) -> float:
    """The largest difference in D or lactate between two runs of the same candidate."""
    if len(rows) != len(reference):
        return math.inf
    return max(abs(row[name] - other[name]) for row, other in zip(rows, reference) for name in ("D", "lactate"))


def _outside_60_min_envelope(rows: list, case: str) -> bool:
    """Untreated lactate at 60 min outside the faculty's 60-min envelope for the case (FD-LAC-02 /
    FD-LAC-03, whose lower bound is the arrival lactate): the approved numbers are read, the rule
    is not run. Not FD-LAC-01, which forbids only a sustained decline in an inadequate window."""
    envelope = fc.ENVELOPES[case]
    if len(rows) <= envelope["minute"]:
        return False
    return not envelope["low"] <= rows[envelope["minute"]]["lactate"] <= envelope["high"]


def _below_arrival_at_end(rows: list) -> bool:
    """Untreated lactate below arrival at the run's end, bleeding never controlled (descriptive: no rule)."""
    return rows[-1]["lactate"] < rows[0]["lactate"] - 1e-9


def revisit(reserves=SYNTHETIC_RESERVES) -> dict:
    """The three P2I-2R findings, at today's canonical reserve 1 and at each synthetic reserve, with
    the arrival band FIXED and RE_ANCHORED. No FD-LAC filter runs: finding 1 reads only L3's
    critical windows over the admissible region, findings 2 and 3 read the committed survivors."""
    settings = fc.params()
    candidates = {candidate.key(): candidate for candidate in decision_pack.admissible()}
    survivors = frozen_survivors()
    variants = [("1", 1.0, FIXED)] + [(f"{reserve:g} {reading}", reserve, reading)
                                      for reserve in reserves for reading in (FIXED, RE_ANCHORED)]
    # Finding 1: sustained lactate declines in L3 while delivery is below demand but improving.
    canonical_rows = {(key, case): _core_rows(case, candidate, fc.DEFINITIVE, 1.0)
                      for key, candidate in candidates.items() for case in fc.CASES}
    canonical = {pair: critical_declines(rows, settings) for pair, rows in canonical_rows.items()}
    pairs = sorted(pair for pair, found in canonical.items() if any(item["delivery_improving"] for item in found))
    finding1 = {"instances": sum(item["delivery_improving"] for found in canonical.values() for item in found),
                "candidates": len({key for key, _ in pairs}), "candidate_cases": len(pairs), "by_variant": {}}
    for name, reserve, reading in variants:
        still = recovering = 0
        states: dict = {}
        largest = 0.0
        for key, case in pairs:
            rows = canonical_rows[(key, case)] if reserve == 1.0 else _core_rows(case, candidates[key], fc.DEFINITIVE,
                                                                                reserve, reading)
            largest = max(largest, _same_dynamics(rows, canonical_rows[(key, case)]))
            found = critical_declines(rows, settings)
            still += bool(found)
            recovering += bool(found) and all(item["delivery_improving"] and item["deficit_falling"]
                                              and item["deficit_falling_each_interval"] for item in found)
            for row in rows[:31]:
                states[row["state"]] = states.get(row["state"], 0) + 1
        finding1["by_variant"][name] = {"pairs_with_a_critical_sustained_decline": still,
                                        "all_of_them_recovering": recovering, "states_minutes_0_30": states,
                                        "largest_D_or_lactate_change_vs_canonical": largest}
    # Finding 2: untreated delivery index 10-39 % at 120 min (lowest survivor per case), and the
    # untreated lactate's direction over all survivors.
    finding2 = {}
    for case in fc.CASES:
        untreated = {key: _core_rows(case, candidates[key], fc.UNTREATED, 1.0) for key in survivors}
        lowest = min(survivors, key=lambda key: untreated[key][-1]["delivery"])
        finding2[case] = {"candidate": lowest,
                          "survivor_range_at_end": [min(rows[-1]["delivery"] for rows in untreated.values()),
                                                    max(rows[-1]["delivery"] for rows in untreated.values())],
                          "by_variant": {}}
        for name, reserve, reading in variants:
            runs = untreated if reserve == 1.0 else {key: _core_rows(case, candidates[key], fc.UNTREATED, reserve,
                                                                     reading) for key in survivors}
            rows = runs[lowest]
            reached = _burdens([dict(row) for row in rows])
            finding2[case]["by_variant"][name] = {
                "points": {str(minute): {item: rows[minute][item] for item in (
                    "output_rel", "hb_ratio", "delivery", "state", "effective_deficit", "D", "lactate", "sbp", "V")}
                    for minute in (0, 60, len(rows) - 1)},
                "arrival_ratio": rows[0]["arrival_ratio"], "collapse_limit_reached": reached,
                "survivors_outside_60_min_envelope": sum(_outside_60_min_envelope(item, case)
                                                         for item in runs.values()),
                "survivors_below_arrival_at_end": sum(map(_below_arrival_at_end, runs.values())),
                "largest_D_or_lactate_change_vs_canonical": max(_same_dynamics(runs[key], untreated[key])
                                                                for key in survivors)}
    # Finding 3: delivery index 1.1-2.2 after transfusion (L3), FIXED and RE_ANCHORED.
    finding3 = {}
    for case in fc.CASES:
        definitive = {key: canonical_rows[(key, case)] for key in survivors}
        by_ratio: dict = {}
        for rows in definitive.values():
            by_ratio.setdefault(f"{rows[0]['arrival_ratio']:g}", []).append(max(row["delivery"] for row in rows))
        highest = max(survivors, key=lambda key: max(row["delivery"] for row in definitive[key]))
        peak = max(definitive[highest], key=lambda row: row["delivery"])
        finding3[case] = {"max_delivery_by_arrival_ratio": {level: [min(values), max(values), len(values)]
                                                           for level, values in sorted(by_ratio.items())},
                          "highest": {"candidate": highest, **{item: peak[item] for item in (
                              "arrival_ratio", "minute", "delivery", "output_rel", "hb_ratio", "V")}},
                          "re_anchored_peak": {f"{reserve:g}": {"delivery": peak["delivery"] / reserve,
                                                                "state": oxygen_balance(peak["delivery"] / reserve,
                                                                                        peak["demand"], reserve).state}
                                               for reserve in reserves}}
    # P2I-2P-5: the synthetic collapse burdens over every admissible engine-produced run, at the
    # canonical reserve (the same D, lactate and critical deficit as any re-anchored reserve).
    collapse = {}
    for scenario in (fc.UNTREATED, fc.PARTIAL, fc.DEFINITIVE):
        for case in fc.CASES:
            runs = ([canonical_rows[(key, case)] for key in candidates] if scenario == fc.DEFINITIVE
                    else [_core_rows(case, candidate, scenario, 1.0) for candidate in candidates.values()])
            reached = [_burdens([dict(row) for row in rows]) for rows in runs]
            collapse[f"{scenario} {case}"] = {
                "runs": len(runs), "stopped_before_end": sum(len(rows) <= MINUTES for rows in runs),
                "critical_at_end": sum(rows[-1]["state"] == "CRITICAL" for rows in runs),
                **{f"reached_by_{name}": sum(item[name] is not None for item in reached)
                   for name in ("output", "oxygen_deficit")},
                **{f"earliest_by_{name}": min((item[name] for item in reached if item[name] is not None), default=None)
                   for name in ("output", "oxygen_deficit")}}
    return {"survivors": len(survivors), "variants": [name for name, _, _ in variants],
            "finding_1_recovering_subthreshold_delivery": finding1,
            "finding_2_untreated_low_delivery": finding2, "finding_3_post_transfusion_delivery": finding3,
            "collapse_interface": collapse}


# The report ----------------------------------------------------------------------------------------


#: P2I-2T (2026-10-27): this audit describes the shadow core before the shared blood state replaced
#: the GI module's independent V and Hb drifts. Its committed JSON and document stay as the historical
#: record they were accepted as (probes digest below) and are not regenerated: the command refuses to
#: produce new results, and only re-renders the committed JSON. None for an authorized re-audit.
HISTORICAL = {"probes_digest": "760627b365b161b166872b932b2bd5cf4fdba6b3507ad17a28215dfb2a8f1357",
              "since": "2026-10-27",
              "reason": "P2I-2T replaced the independent haemorrhage drifts with the shared blood state; this audit "
                        "is the record of the core before it"}


def probes_digest() -> str:
    text = json.dumps({"sources": lactate_slice.slice_sources(), "freeze": calibration.frozen_digest()}, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def report() -> dict:
    return {"probes_digest": probes_digest(), "canonical_reserve": DEFAULT_PROFILE.oxygen_extraction_reserve,
            "synthetic_reserve": SYNTHETIC_RESERVE, "synthetic_output_threshold": SYNTHETIC_OUTPUT_THRESHOLD,
            "synthetic_burden_limit": SYNTHETIC_BURDEN_LIMIT, "admissible_candidates": len(decision_pack.admissible()),
            "probes": {name: {f"{reserve:g}": probe(name, reserve) for reserve in (1.0, SYNTHETIC_RESERVE)}
                       for name in PROBES},
            "revisit": revisit()}


# Rendering ---------------------------------------------------------------------------------------

OPENING, CLOSING = "<!-- generado:oxigeno -->\n", "<!-- /generado:oxigeno -->"
STATES_ES = {"ADEQUATE": "adecuada", "COMPENSATED": "compensada", "CRITICAL": "crítica"}
DIRECTIONS_ES = {"rises": "↑", "falls": "↓", "flat": "="}
PROBES_ES = {"A normal": "A · normal",
             "B compensated low delivery": "B · entrega baja compensada",
             "C delivery crossing the critical region": "C · entrega que cruza la región crítica",
             "D anaemia, output preserved": "D · anemia con gasto conservado",
             "E low output, Hb preserved": "E · gasto bajo con Hb conservada",
             "F low output and anaemia": "F · gasto bajo y anemia",
             "G high demand, delivery preserved": "G · demanda alta con entrega conservada",
             "H resuscitation restores delivery": "H · la reanimación restituye la entrega",
             "I transfusion raises Hb and delivery": "I · la transfusión sube la Hb y la entrega",
             "J severe sustained critical deficit": "J · déficit crítico grave y sostenido"}
WHAT_ES = {"normal delivery, normal demand": "entrega y demanda normales",
           "pump falls 30 % over 30 min, then holds": "la bomba cae 30 % en 30 min y se mantiene",
           "pump falls steadily to 0.2 over 100 min": "la bomba cae de forma continua hasta 0,2 en 100 min",
           "Hb falls 0.07 g/dL per min (13 to 4.6 g/dL)": "la Hb baja 0,07 g/dL por min (de 13 a 4,6 g/dL)",
           "pump falls to 0.3 over 60 min, then holds": "la bomba cae a 0,3 en 60 min y se mantiene",
           "pump to 0.6 and Hb to 7.8 g/dL over 40 min": "bomba a 0,6 y Hb a 7,8 g/dL en 40 min",
           "demand x 1.5 throughout": "demanda × 1,5 todo el tiempo",
           "pump falls to 0.25 by 30 min, restored to 1.0 by 60 min":
               "la bomba cae a 0,25 hasta el min 30 y se restituye a 1,0 hasta el min 60",
           "Hb falls to 4.6 g/dL by 30 min; +2 g/dL from 45 to 85 min":
               "la Hb baja a 4,6 g/dL hasta el min 30; +2 g/dL entre los min 45 y 85",
           "pump falls to 0.16 by 15 min and stays": "la bomba cae a 0,16 hasta el min 15 y se mantiene"}
VARIANTS_ES = {"1": "1 (canónica)"}


def _decimal(text: str) -> str:
    return text.replace(".", ",")


def _variant_es(name: str) -> str:
    if name in VARIANTS_ES:
        return VARIANTS_ES[name]
    reserve, reading = name.split(" ", 1)
    return f"{_decimal(reserve)}, banda {'fija' if reading == FIXED else 're-anclada'}"


def _n(value, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, float) and math.isinf(value):
        return "∞"
    return lactate_slice._n(value, digits)


def _minute(value) -> str:
    return "—" if value is None else f"min {value}"


def _reached(reached: dict) -> str:
    return " / ".join(str(reached[name]) if reached[name] is not None else "no" for name in ("output", "oxygen_deficit"))


def render(data: dict) -> str:
    lines = []
    add = lines.append
    add(f"Generado desde las sondas `{data['probes_digest']}` (`python -m clinical_core.oxygen_probes`). Reserva canónica "
        f"{_n(data['canonical_reserve'], 0)} (neutra: el modelo previo); reserva ilustrativa "
        f"{_n(data['synthetic_reserve'], 1)}, sintética y no propuesta. Colapso: sólo un cálculo sobre cada trayectoria, "
        f"con un umbral de gasto sintético de {_n(data['synthetic_output_threshold'], 1)} y un límite de carga sintético "
        f"de {_n(data['synthetic_burden_limit'], 0)} minutos a severidad plena; la regla del núcleo sigue apagada. Los "
        "lactatos de las sondas A–J usan las cinéticas por defecto del perfil (TBD): importa su dirección, no su "
        "magnitud.\n")
    add("### 4.1 Sondas A–J\n")
    add("Índice de entrega (DO2 / DO2 normal en reposo), índice de demanda (VO2 demandado / VO2 normal en reposo), estado "
        "de oxigenación, extracción requerida (relativa a la normal), déficit efectivo (lo que D integra), D, lactato y las "
        "dos cargas de colapso sintéticas (gasto / déficit de O2).\n")
    for name, by_reserve in data["probes"].items():
        first = next(iter(by_reserve.values()))
        add(f"**{PROBES_ES[name]}** — {WHAT_ES[first['what']]}.\n")
        add("| Reserva | Min | Entrega | Demanda | Estado | Extracción req. | Déficit efectivo | D | Lactato | "
            "Carga gasto | Carga déficit |")
        add("|---|---|---|---|---|---|---|---|---|---|---|")
        for reserve, item in by_reserve.items():
            for minute in TIMES:
                point = item["points"][str(minute)]
                add(f"| {_decimal(reserve)} | {minute} | {_n(point['delivery'])} | {_n(point['demand'])} | "
                    f"{STATES_ES[point['state']]} | {_n(point['required_extraction'])} | "
                    f"{_n(point['effective_deficit'])} | {_n(point['D'], 1)} | {_n(point['lactate'])} | "
                    f"{_n(point['burden_output'], 1)} | {_n(point['burden_oxygen_deficit'], 1)} |")
        add("")
        add("| Reserva | Dirección del lactato (0→15→30→60→90→120) | Primer minuto crítico | D máximo | "
            "Límite de colapso sintético alcanzado (gasto / déficit) |")
        add("|---|---|---|---|---|")
        for reserve, item in by_reserve.items():
            critical = item["first_critical_minute"]
            add(f"| {_decimal(reserve)} | {' '.join(DIRECTIONS_ES[step] for step in item['lactate_direction'])} | "
                f"{critical if critical is not None else 'nunca'} | {_n(item['max_D'], 1)} | "
                f"{_reached(item['collapse_limit_reached'])} |")
        add("")
    revisit_ = data["revisit"]
    one = revisit_["finding_1_recovering_subthreshold_delivery"]
    add("### 4.2 Hallazgo 1: entrega bajo la demanda pero recuperándose (L3)\n")
    add(f"Con la reserva canónica, {one['instances']} descensos sostenidos del lactato en una ventana L3 con sangrado activo "
        f"y entrega bajo la demanda en cada minuto, con la entrega mejorando, en {one['candidates']} candidatos "
        f"({one['candidate_cases']} pares candidato–caso) de la región admisible; los pares se eligieron por esa mejora. "
        "Para cada variante: cuántos pares conservan un descenso sostenido dentro de un tramo **crítico** (déficit efectivo "
        "en cada minuto); cuántos están en recuperación en todos sus descensos (la entrega sube y el déficit efectivo baja "
        "entre los extremos y entre cada par de reevaluaciones de 15 min consecutivas); los estados de los minutos 0–30; y "
        "el cambio máximo de D o lactato frente a la corrida canónica.\n")
    add("| Reserva | Pares con descenso sostenido en tramo crítico | De ellos, en recuperación | Minutos 0–30 por estado | "
        "Cambio máx. de D o lactato |")
    add("|---|---|---|---|---|")
    for name, row in one["by_variant"].items():
        states = ", ".join(f"{STATES_ES[state]}: {count}" for state, count in sorted(row["states_minutes_0_30"].items()))
        add(f"| {_variant_es(name)} | {row['pairs_with_a_critical_sustained_decline']} de {one['candidate_cases']} | "
            f"{row['all_of_them_recovering']} | {states} | {_n(row['largest_D_or_lactate_change_vs_canonical'], 3)} |")
    add("")
    add("### 4.3 Hallazgo 2: entrega muy baja sin tratar (L1)\n")
    add(f"El sobreviviente de P2I-2R (los {revisit_['survivors']} comprometidos, sin refiltrar) con la menor entrega al "
        "final, en cada variante; y sobre todos los sobrevivientes, cuántos dejan el lactato sin tratar de los 60 min fuera "
        "de la envolvente docente de FD-LAC-02/03 (cuyo límite inferior es el lactato de llegada; se leen los números "
        "aprobados, no se ejecuta la regla) y cuántos terminan con el lactato bajo el de llegada (descriptivo).\n")
    add("| Caso | Variante | Relación de llegada | Min | Gasto rel. | Hb / Hb llegada | Entrega | Estado | Déficit | D | "
        "Lactato | PAS | V (mL) |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for case, item in revisit_["finding_2_untreated_low_delivery"].items():
        for name, row in item["by_variant"].items():
            for minute, point in sorted(row["points"].items(), key=lambda item: int(item[0])):
                add(f"| {case} | {_variant_es(name)} | {_n(row['arrival_ratio'])} | {minute} | {_n(point['output_rel'])} | "
                    f"{_n(point['hb_ratio'])} | {_n(point['delivery'])} | {STATES_ES[point['state']]} | "
                    f"{_n(point['effective_deficit'])} | {_n(point['D'], 1)} | {_n(point['lactate'])} | "
                    f"{_n(point['sbp'], 0)} | {_n(point['V'], 0)} |")
    add("")
    add("| Caso | Variante | Entrega al final, rango de los sobrevivientes | Límite de colapso sintético (gasto / déficit), "
        "el más bajo | Sobrevivientes fuera de la envolvente de 60 min | Sobrevivientes con lactato final bajo el de "
        "llegada | Cambio máx. de D o lactato |")
    add("|---|---|---|---|---|---|---|")
    for case, item in revisit_["finding_2_untreated_low_delivery"].items():
        for name, row in item["by_variant"].items():
            low, high = item["survivor_range_at_end"]
            scale = 1.0 if name.endswith(FIXED) or name == "1" else float(name.split()[0])
            add(f"| {case} | {_variant_es(name)} | {_n(low / scale)}–{_n(high / scale)} | "
                f"{_reached(row['collapse_limit_reached'])} | {row['survivors_outside_60_min_envelope']} de "
                f"{revisit_['survivors']} | {row['survivors_below_arrival_at_end']} de {revisit_['survivors']} | "
                f"{_n(row['largest_D_or_lactate_change_vs_canonical'], 3)} |")
    add("")
    add("### 4.4 Hallazgo 3: índice de entrega tras la transfusión (L3)\n")
    add("| Caso | Máximo del índice por relación de llegada (mín–máx, n) | El más alto: llegada, minuto, índice = gasto rel. × "
        "Hb rel. × relación, V | El mismo pico, banda re-anclada (índice sobre DO2 normal, estado) |")
    add("|---|---|---|---|")
    for case, item in revisit_["finding_3_post_transfusion_delivery"].items():
        levels = "; ".join(f"{_n(float(level))}: {_n(values[0])}"
                           + (f"–{_n(values[1])}" if _n(values[1]) != _n(values[0]) else "") + f" (n {values[2]})"
                           for level, values in item["max_delivery_by_arrival_ratio"].items())
        top = item["highest"]
        anchored = "; ".join(f"ρ {_decimal(reserve)}: {_n(peak['delivery'])} ({STATES_ES[peak['state']]})"
                             for reserve, peak in item["re_anchored_peak"].items())
        add(f"| {case} | {levels} | {_n(top['arrival_ratio'])}, min {top['minute']}: {_n(top['delivery'])} = "
            f"{_n(top['output_rel'])} × {_n(top['hb_ratio'])} × {_n(top['arrival_ratio'])}; V {_n(top['V'], 0)} mL | "
            f"{anchored} |")
    add("")
    add("### 4.5 Cargas de colapso sintéticas sobre la región admisible\n")
    add("Todas las corridas producidas por el motor (L1 sin tratar, L2 salino parcial, L3 manejo definitivo) con la reserva "
        "canónica, que da el mismo déficit crítico que cualquier reserva con la banda re-anclada. La carga sintética "
        "acumula y no se repaga.\n")
    add("| Escenario y caso | Corridas | Detenidas antes de 120 min | Críticas al final | Alcanzan el límite por gasto "
        "(más temprano) | Alcanzan el límite por déficit (más temprano) |")
    add("|---|---|---|---|---|---|")
    for name, row in revisit_["collapse_interface"].items():
        add(f"| {name} | {row['runs']} | {row['stopped_before_end']} | {row['critical_at_end']} | "
            f"{row['reached_by_output']} ({_minute(row['earliest_by_output'])}) | "
            f"{row['reached_by_oxygen_deficit']} ({_minute(row['earliest_by_oxygen_deficit'])}) |")
    add("")
    return "\n".join(lines)


def apply(document: str, block: str) -> str:
    start = document.index(OPENING) + len(OPENING)
    end = document.index(CLOSING)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--write", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)
    if args.write:
        data = json.loads(args.json.read_text(encoding="utf-8"))
        args.write.write_text(apply(args.write.read_text(encoding="utf-8"), render(data)), encoding="utf-8")
        return 0
    if HISTORICAL is not None:
        parser.error(f"a historical record since {HISTORICAL['since']} ({HISTORICAL['reason']}): its results are not "
                     "regenerated without authorization")
    text = json.dumps(report(), indent=1, sort_keys=True, default=str)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "oxygen_probes.json").write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
