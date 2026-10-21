"""The only bridge between the family engine and the shadow core. Read-only.

It runs the family engine exactly as the encounter page does -- the frozen reader parses
the order, ``execute_family_bundle`` executes it, ``advance_clinical_time`` lets time pass
-- one minute at a time, on its own state, and records what the engine shows. Then it
reads the *same relevant inputs* (the case's arrival, the parsed orders with the start
minutes the engine reported, the FiO2 the engine set, the minute the engine performed
the endoscopy) and builds the core's anchors, module and interventions from them.

Nothing here writes to the family engine, its module constants, ``st.session_state``,
the Management Trace, receipts, events, observations or persistence. Every function
works on deep copies of the state it is given.

When Phase 1's ``OrderAction`` v2 is final, ``interventions_from_orders`` is the single
function to replace: it is where a legacy parsed action becomes a core intervention.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping

from .derived import LEGACY_ML_PER_CIRCULATION_UNIT
from .interventions import Crystalloid, Oxygen, PackedRedCells, ProtonPumpInhibitor
from .interventions.timing import delivered_by
from .logistics import EndoscopicHemostasis
from .modules import GIHaemorrhage
from .state import Anchors, RhythmCode, RhythmState

#: The family engine's mental-status ladder (family_engine._LEVEL_OF).
LEVEL_OF = {"Alert": 0, "Drowsy": 1, "Obtunded": 2, "Unresponsive": 3}
SUPPORTED_FAMILIES = frozenset({"gi_bleed"})
#: Parsed action types that carry no physiology in the core: they are recorded, not dropped.
NOT_PHYSIOLOGICAL = frozenset({"reassessment", "consult", "diagnostic"})

#: Literals of family_engine._minute that are not in a constant table there. Copied, with
#: their place, so a change in the engine shows up as a golden-trajectory difference.
LEGACY_LITERALS = {
    "gi_bleeding_circulation_per_min": (0.003, "family_engine._minute: circulation += (.003 + ...) * bleeding"),
    "gi_bleeding_hemoglobin_per_min": (0.009, "family_engine._minute: hemoglobin -= (.009 + ...) * bleeding"),
    "blood_circulation_per_unit": (0.36, "family_engine._minute: circulation -= gain + blood * .36"),
    "blood_hemoglobin_per_unit": (0.85, "family_engine._minute: hemoglobin += blood * .85"),
    "untimed_fluid_ml_per_min": (50.0, "family_engine._minute: min(50, pending_fluid_ml)"),
    "untimed_blood_units_per_min": (1 / 30, "family_engine._minute: min(1 / 30, pending_blood_units)"),
}


class UnsupportedScenario(ValueError):
    """The scenario holds something the shadow core does not model. It is refused, never dropped."""


def _engine():
    import family_engine
    return family_engine


def bank_case(variant_id: str, family: str = "gi_bleed", seed: int = 1) -> dict:
    """A bank encounter as the faculty sandbox creates it (authored mode, fixed seed)."""
    from cognitive_catalog import BIAS_CHALLENGES
    from cognitive_generator import generate_cognitive_encounter
    challenge = next(key for key, entry in BIAS_CHALLENGES.items() if family in entry["families"])
    return generate_cognitive_encounter(challenge, {"sim_time": 0, "hidden": {}, "treatments": {}}, family_id=family,
                                        variant_id=variant_id, seed=seed, generation_mode="authored")["state"]


def _initialized(state: Mapping) -> dict:
    copy = deepcopy(dict(state))
    _engine()._initialize(copy)
    return copy


def _authored_potassium(state: Mapping) -> float | None:
    labs = _engine()._case(state).get("investigations", {}).get("basic_labs", {}).get("result", {})
    value = labs.get("potassium_mmol_l")
    return None if value is None else float(value)


def _lactate_lab(state: Mapping) -> float:
    """The lactate the family engine would report now, computed by its own code on a copy."""
    copy = deepcopy(dict(state))
    return float(_engine()._diagnostic(copy, "lactate", 0)["result"]["lactate_mmol_l"])


def snapshot(state: Mapping) -> dict:
    """What the family engine shows and holds at this minute, for comparison only."""
    source = state if state.get("family_state", {}).get("version") else _initialized(state)
    f, o = source["family_state"], source.get("observable", {})
    return {
        "minute": int(source.get("sim_time", 0)),
        "sbp": o.get("sbp"), "dbp": o.get("dbp"), "map": o.get("map"), "hr": o.get("hr"), "spo2": o.get("spo2"),
        "respiratory_rate": o.get("respiratory_rate"), "crt": o.get("crt"), "mental_status": o.get("mental_status"),
        "rhythm": o.get("rhythm"), "pulse_present": o.get("pulse_present", True),
        "circulation": float(f["circulation"]), "hemoglobin": float(f["hemoglobin"]), "glucose": float(f["glucose"]),
        "fluid_delivered_ml": float(f["fluid_delivered_ml"]), "blood_delivered_units": float(f["blood_delivered_units"]),
        "oxygen_fio2": float(f["oxygen_fio2"]), "endoscopy_at": f.get("endoscopy_at"),
        "hemostasis_relief": float(f.get("hemostasis_relief", 0.0)),
        "transfusion_overload_units": float(f.get("transfusion_overload_units", 0.0)),
        "lactate_lab": _lactate_lab(source), "potassium_lab": _authored_potassium(source),
    }


@dataclass(frozen=True)
class LegacyOrder:
    minute: int
    text: str
    actions: tuple
    summaries: tuple
    fio2_after: float


@dataclass(frozen=True)
class LegacyRun:
    variant_id: str
    arrival: dict
    snapshots: tuple
    orders: tuple
    final_state: dict


def run_legacy(variant_id: str, orders: Mapping[int, str], minutes: int, *, state: Mapping | None = None) -> LegacyRun:
    """Run the family engine one minute at a time; an order is executed at its minute.

    Each order is sent with "Reassess in 1 minute." so the turn advances exactly one
    minute; the run fails closed if the engine advanced any other amount, interrupted the
    turn, or refused the order.
    """
    from family_parser import parse_family_actions
    engine = _engine()
    for minute, text in orders.items():
        # An order the loop would never reach must not vanish from the comparison.
        if isinstance(minute, bool) or not isinstance(minute, int) or not 0 <= minute < minutes:
            raise UnsupportedScenario(f"order minute {minute!r} is not a whole minute in [0, {minutes})")
        if not isinstance(text, str) or not text.strip():
            raise UnsupportedScenario(f"the order at minute {minute} has no text")
    current = deepcopy(dict(state)) if state is not None else bank_case(variant_id)
    if current.get("engine_family") not in SUPPORTED_FAMILIES:
        raise UnsupportedScenario(f"family {current.get('engine_family')!r} is not in the shadow core yet")
    arrival = deepcopy(current)
    snapshots, executed = [snapshot(current)], []
    for minute in range(minutes):
        text = orders.get(minute)
        if text:
            parsed = parse_family_actions(f"{text} Reassess in 1 minute.")
            result = engine.execute_family_bundle(current, parsed)
            if not result.get("executed") or result.get("elapsed_min") != 1 or result.get("interrupted"):
                raise UnsupportedScenario(f"the family engine did not run {text!r} as one plain minute: {result}")
            executed.append(LegacyOrder(minute, text, tuple(deepcopy(parsed["actions"])),
                                        tuple(deepcopy(result["action_summaries"])),
                                        float(current["family_state"]["oxygen_fio2"])))
        else:
            engine.advance_clinical_time(current, 1)
        if int(current["sim_time"]) != minute + 1:
            raise UnsupportedScenario("the family engine's clock did not advance one minute")
        snapshots.append(snapshot(current))
    return LegacyRun(variant_id, arrival, tuple(snapshots), tuple(executed), deepcopy(current))


def anchors_from_legacy(state: Mapping) -> Anchors:
    source = _initialized(state)
    f = source["family_state"]
    base = f["baseline"]
    if not str(base.get("rhythm", "")).lower().startswith("sinus"):
        raise UnsupportedScenario("only a sinus arrival rhythm is anchored so far")
    potassium = _authored_potassium(source)
    if potassium is None:
        raise UnsupportedScenario("the case authors no potassium to anchor C12")
    mental = str(base.get("mental_status", "Alert"))
    if mental not in LEVEL_OF:
        raise UnsupportedScenario(f"arrival mental status {mental!r} is not on the engine's ladder")
    return Anchors(case_id=str(engine_case_id(source)), sbp=float(base["sbp"]), dbp=float(base["dbp"]),
                   hr=float(base["hr"]), spo2=float(base["spo2"]), respiratory_rate=float(base["respiratory_rate"]),
                   crt_s=float(base.get("crt") or 2), lactate=float(f["lactate"]), hb=float(f["hemoglobin"]),
                   glucose=float(f["glucose"]), k=potassium, fio2=float(f["oxygen_fio2"]),
                   rhythm=RhythmState(RhythmCode.SINUS, float(base["hr"]), 1.0, True),
                   consciousness_level=LEVEL_OF[mental])


def engine_case_id(state: Mapping) -> str:
    return _engine()._case_id(state)


def haemorrhage_from_legacy(state: Mapping) -> GIHaemorrhage:
    engine = _engine()
    if _initialized(state)["family_state"].get("anticoagulant_exposure"):
        raise UnsupportedScenario("anticoagulant exposure is not modelled in the shadow haemorrhage module")
    return GIHaemorrhage(
        "gi_haemorrhage",
        volume_loss_ml_per_min=LEGACY_LITERALS["gi_bleeding_circulation_per_min"][0] * LEGACY_ML_PER_CIRCULATION_UNIT,
        hb_loss_g_dl_per_min=LEGACY_LITERALS["gi_bleeding_hemoglobin_per_min"][0],
        fraction_with_ppi=float(engine.GI_BLEED["bleeding_with_ppi"]),
        fraction_after_hemostasis=float(engine.GI_BLEED["bleeding_after_hemostasis"]))


def _order_id(order: LegacyOrder, index: int, action: Mapping) -> str:
    return f"m{order.minute:03d}-{index}-{action['type']}"


DELIVERED = ("fluid", "blood")


def _summaries(order: LegacyOrder, kind: str) -> list:
    """The engine appends one summary per action, in action order: pair them by position."""
    actions = [action for action in order.actions if action["type"] == kind]
    summaries = [summary for summary in order.summaries if summary.get("type") == kind]
    if len(actions) != len(summaries):
        raise UnsupportedScenario(f"{len(actions)} {kind} actions but {len(summaries)} {kind} receipts at minute "
                                  f"{order.minute}")
    return summaries


@dataclass(frozen=True)
class _Delivery:
    position: tuple
    kind: str
    order_id: str
    minute: int
    action: Mapping
    start: float


def interventions_from_orders(orders, engine_gi_bleed: Mapping) -> tuple:
    """Each executed legacy action becomes one core intervention, or the scenario is refused.

    Delivery follows what the engine did: a timed bag starts where the engine's receipt
    says (a second bag queues behind the first); untimed volume of one kind shares one
    line at the default rate; "stop IV fluids" closes every crystalloid given before it.
    An order held until a result arrives is released later by the engine; that release
    is not followed yet, so such a scenario is refused.
    """
    built, deliveries, stops = [], [], []
    for order in orders:
        if any(summary.get("type") == "deferred" for summary in order.summaries) or \
                any(action.get("after_result") for action in order.actions):
            raise UnsupportedScenario(f"an order held until a result (minute {order.minute}) is not followed yet")
        receipts = {kind: iter(_summaries(order, kind)) for kind in DELIVERED}
        for index, action in enumerate(order.actions):
            kind, order_id = action["type"], _order_id(order, index, action)
            if kind in DELIVERED:
                receipt = next(receipts[kind])
                operation = action.get("operation")
                if kind == "fluid" and operation == "stop":
                    stops.append(((order.minute, index), order_id))
                    continue
                if operation is not None:
                    raise UnsupportedScenario(f"{kind} operation {operation!r} has no shadow-core equivalent yet")
                begins = receipt.get("delivery_starts_at_min")
                deliveries.append(_Delivery((order.minute, index), kind, order_id, order.minute, action,
                                            order.minute if begins is None else float(begins)))
            elif kind == "oxygen":
                built.append(Oxygen(order_id, order.minute, order.fio2_after))
            elif kind == "ppi":
                built.append(ProtonPumpInhibitor(order_id, order.minute))
            elif kind in NOT_PHYSIOLOGICAL:
                continue
            else:
                raise UnsupportedScenario(f"order type {kind!r} has no shadow-core intervention yet")
    made = []
    for item in deliveries:
        stop = next(((position, order_id) for position, order_id in stops if position > item.position), None)
        stop_minute, stopped_by = (stop[0][0], stop[1]) if stop and item.kind == "fluid" else (None, None)
        ahead = 0.0
        if _duration(item.action) is None:
            for earlier, contributor in made:
                closed = any(earlier.position < position <= item.position for position, _ in stops) and earlier.kind == "fluid"
                if earlier.kind == item.kind and _duration(earlier.action) is None and not closed:
                    ahead += contributor_amount(contributor) - delivered_by(item.minute, **contributor.delivery())
        contributor = _build(item, engine_gi_bleed, stop_minute, stopped_by, ahead)
        made.append((item, contributor))
    return tuple(built + [contributor for _, contributor in made])


def contributor_amount(contributor) -> float:
    return contributor.volume_ml if isinstance(contributor, Crystalloid) else contributor.units


def _build(item: _Delivery, engine_gi_bleed: Mapping, stop_minute, stopped_by, ahead):
    if item.kind == "fluid":
        return Crystalloid(
            item.order_id, item.start, float(item.action["volume_ml"]), _duration(item.action),
            untimed_rate_ml_per_min=LEGACY_LITERALS["untimed_fluid_ml_per_min"][0],
            effective_ml_per_ml=float(engine_gi_bleed["crystalloid_per_ml"]) * LEGACY_ML_PER_CIRCULATION_UNIT,
            transient_share=float(engine_gi_bleed["crystalloid_transient"]),
            leak_tau_min=float(engine_gi_bleed["crystalloid_leak_tau_min"]),
            hb_dilution_g_dl_per_ml=float(engine_gi_bleed["hemodilution_g_dl_per_ml"]),
            stop_minute=stop_minute, stopped_by=stopped_by, queued_ahead_ml=ahead)
    return PackedRedCells(
        item.order_id, item.start, float(item.action["units"]), _duration(item.action),
        untimed_units_per_min=LEGACY_LITERALS["untimed_blood_units_per_min"][0],
        volume_ml_per_unit=LEGACY_LITERALS["blood_circulation_per_unit"][0] * LEGACY_ML_PER_CIRCULATION_UNIT,
        hb_g_dl_per_unit=LEGACY_LITERALS["blood_hemoglobin_per_unit"][0], queued_ahead_units=ahead)


def _duration(action: Mapping):
    value = action.get("administration_duration_min")
    return None if value is None else float(value)


def contributors_from_legacy(legacy: LegacyRun) -> tuple:
    """Module, interventions and the logistic completion the family engine decided."""
    engine = _engine()
    contributors = [haemorrhage_from_legacy(legacy.arrival)]
    contributors.extend(interventions_from_orders(legacy.orders, engine.GI_BLEED))
    endoscopy = legacy.final_state["family_state"].get("endoscopy_at")
    if endoscopy is not None:
        contributors.append(EndoscopicHemostasis("gastroenterology_endoscopy", int(endoscopy)))
    return tuple(contributors)
