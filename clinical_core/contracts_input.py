"""Offline input adapter: final Phase-1 Contracts v2 -> the shadow core's inputs (P2B-2).

It reads only Contracts v2 objects: ``OrderAction`` (what the engine was sent),
``FateReceipt`` (what the Phase-0 ledger says happened to each order), ``TurnTime``
(when) and ``EventInterruption`` (the logistic completions). It builds the interventions
``legacy_adapter`` builds from the engine's own run.

The ledger's identity is kept:
- each intervention's id is the order's ``order_id``;
- each binding keeps the ``submission_id`` the order was written in, also when a later
  turn carries the order forward.

Every order ends in exactly one ``OrderBinding``, with one of these dispositions:
- a core contributor;
- a stop;
- no physiology in the core;
- not acted on by the engine.

Anything else is refused with ``UnsupportedContract``. Nothing is dropped, and no future
or conditional order is read as given now.

Two quantities the engine decided are not carried by Contracts v2:
- the minute a queued timed bag starts;
- the FiO2 an oxygen device gives.

Both are rebuilt from the contract fields by the engine's own rules (``queued_start`` and
``OXYGEN_FIO2`` below). The golden comparison checks them against what the engine did.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from contracts_v2.events import EventInterruption
from contracts_v2.fates import FateReceipt
from contracts_v2.orders import OrderAction
from contracts_v2.timing import TurnTime

from .interventions import Oxygen, ProtonPumpInhibitor
from .legacy_adapter import Delivery, delivery_contributors
from .logistics import EndoscopicHemostasis


class ContractInputError(ValueError):
    """The contracts contradict each other (identity, timing); nothing is built from them."""


class UnsupportedContract(ContractInputError):
    """The contracts hold something the shadow core does not model. It is refused, never dropped."""


#: Ledger fates (order_ledger.FATES) under which the order did not act on the patient.
NOT_ACTED = frozenset({"RECORDED_NOT_MODELLED", "UNRECOGNIZED", "DUPLICATE_IGNORED", "TERMINAL_NOT_EXECUTABLE"})
#: Fates of an order that may still run later: never read as given now.
PENDING = frozenset({"HELD_CLARIFICATION", "HELD_REASONING", "SCHEDULED"})

#: Engine-facing fields each class may carry. Any other field is a meaning the core does not
#: follow (a rate, a condition, "after the result"...), and the order is refused.
FIELDS = {
    "fluid": frozenset({"type", "fluid_type", "volume_ml", "route", "administration_duration_min", "rate_ml_h",
                        "operation"}),
    "blood": frozenset({"type", "units", "administration_duration_min"}),
    "oxygen": frozenset({"type", "device", "flow_lpm"}),
    "ppi": frozenset({"type", "agent", "dose_mg", "route"}),
    "reassessment": frozenset({"type", "delay_min"}),
    "consult": frozenset({"type", "service"}),
    "diagnostic": frozenset({"type", "diagnostic"}),
}
NO_PHYSIOLOGY = frozenset({"reassessment", "consult", "diagnostic"})
CRYSTALLOIDS = frozenset({"normal saline", "lactated Ringer's"})
FLUID_ROUTES = frozenset({"IV", "IO"})

#: FiO2 by the engine's device names (family_engine._apply, oxygen branch). Nasal cannula
#: depends on the flow: min(.45, .21 + .04 x L/min).
OXYGEN_FIO2 = {"Room air": .21, "Simple mask": .50, "Non-rebreather mask": .85}
NASAL_CANNULA = ("Nasal cannula", .21, .04, .45)

#: Logistic completions the core models: event kind -> the logistic process's id in the core.
LOGISTIC_EVENTS = {"endoscopy": "gastroenterology_endoscopy"}
#: Event causes that are inputs to the legacy physiology. A shadow core that does not model
#: them cannot follow the case, so they are refused, not skipped.
EVENT_INPUT_CAUSES = frozenset({"LOGISTIC", "SCRIPTED_NATURAL_HISTORY"})

DISPOSITIONS = ("core_contributor", "core_stop", "no_physiology", "not_acted_by_engine")


@dataclass(frozen=True)
class OrderBinding:
    """What became of one order in the shadow core. It cites the ledger's fate; it owns none."""

    order_id: str
    submission_id: str
    action_class: str
    fate: str
    executed_at_min: int | None
    disposition: str
    source_key: str | None = None
    start_minute: float | None = None
    affects: tuple = ()

    def __post_init__(self):
        if self.disposition not in DISPOSITIONS:
            raise ContractInputError(f"unknown disposition {self.disposition!r}")

    def to_dict(self) -> dict:
        return {"order_id": self.order_id, "submission_id": self.submission_id, "class": self.action_class,
                "cited_fate": self.fate, "executed_at_min": self.executed_at_min, "disposition": self.disposition,
                "source_key": self.source_key, "start_minute": self.start_minute, "affects": list(self.affects)}


@dataclass(frozen=True)
class AdaptedInputs:
    contributors: tuple
    bindings: tuple
    events_not_consumed: tuple

    def binding(self, order_id: str) -> OrderBinding:
        return next(item for item in self.bindings if item.order_id == order_id)


def adapt(actions: Iterable[OrderAction], fates: Iterable[FateReceipt], times: Iterable[TurnTime] = (),
          events: Iterable[EventInterruption] = (), *, gi_bleed: Mapping, devices: Mapping) -> AdaptedInputs:
    """Contracts v2 of a run, in execution order, into the core's interventions and bindings.

    ``fates`` may hold the same order more than once (its receipt in each turn that
    touched it); the last one is the order's fate. ``gi_bleed`` is the engine's GI_BLEED
    table and ``devices`` its oxygen device names, both passed in by the legacy-facing
    caller so that this module reads no engine state.
    """
    actions, fates = tuple(actions), tuple(fates)
    for item in actions:
        if not isinstance(item, OrderAction):
            raise ContractInputError(f"not an OrderAction v2: {type(item).__name__}")
    for item in fates:
        if not isinstance(item, FateReceipt):
            raise ContractInputError(f"not a FateReceipt v2: {type(item).__name__}")
    by_id = _actions_by_id(actions)
    # An order carried forward appears again in the turn that ran it; its last place is where it ran.
    ran_at = {action.order_id: index for index, action in enumerate(actions)}
    final = _final_fates(fates)
    _check_times(tuple(times), final)
    for order_id in by_id:
        if order_id not in final:
            raise UnsupportedContract(f"order {order_id} has no FateReceipt: whether it ran is unknown")
    bindings, built, deliveries, stops = [], [], [], []
    sequence = list(by_id) + [order_id for order_id in final if order_id not in by_id]
    for position, order_id in enumerate(sequence):
        fate = final[order_id]
        action = by_id.get(order_id)
        if action is not None and (action.submission_id != fate.submission_id
                                   or action.action_class != fate.action_class):
            raise ContractInputError(f"order {order_id}: OrderAction and FateReceipt disagree on its identity")
        if fate.limitation is not None:
            raise UnsupportedContract(f"order {order_id} carries the limitation {fate.limitation!r}")
        if fate.fate in NOT_ACTED:
            bindings.append(_binding(fate, "not_acted_by_engine"))
            continue
        if fate.fate in PENDING:
            raise UnsupportedContract(f"order {order_id} is {fate.fate}: a future or conditional order is not "
                                      "read as given now")
        if fate.fate != "EXECUTED":
            raise UnsupportedContract(f"order {order_id} has fate {fate.fate!r}, which the shadow core does not follow")
        if action is None:
            raise UnsupportedContract(f"executed order {order_id} has no OrderAction: what ran is unknown")
        minute = _minute(fate)
        kind, fields = action.action_class, action.fields
        _check_fields(order_id, kind, fields)
        if kind in NO_PHYSIOLOGY:
            bindings.append(_binding(fate, "no_physiology"))
        elif kind == "oxygen":
            contributor = Oxygen(order_id, minute, _fio2(order_id, fields, devices))
            built.append(contributor)
            bindings.append(_binding(fate, "core_contributor", contributor.source.key, minute))
        elif kind == "ppi":
            contributor = ProtonPumpInhibitor(order_id, minute)
            built.append(contributor)
            bindings.append(_binding(fate, "core_contributor", contributor.source.key, minute))
        elif kind == "fluid" and fields.get("operation") == "stop":
            stops.append(((minute, ran_at[order_id]), order_id))
            bindings.append(_binding(fate, "core_stop"))
        else:
            _check_delivery(order_id, kind, fields)
            deliveries.append(Delivery((minute, ran_at[order_id]), kind, order_id, minute, dict(fields), minute))
            bindings.append(None)
    # The line and the queue follow the order in which the engine ran the orders, not the order
    # in which they were first written.
    deliveries.sort(key=lambda item: item.position)
    stops.sort()
    deliveries = queued_start(deliveries, stops)
    made = delivery_contributors(deliveries, stops, gi_bleed)
    by_order = {contributor.id: contributor for contributor in made}
    stopped = {}
    for contributor in made:
        if getattr(contributor, "stopped_by", None):
            stopped.setdefault(contributor.stopped_by, []).append(contributor.id)
    starts = {item.order_id: item.start for item in deliveries}
    result = []
    for position, order_id in enumerate(sequence):
        binding = bindings[position]
        if binding is None:
            contributor = by_order[order_id]
            binding = _binding(final[order_id], "core_contributor", contributor.source.key, starts[order_id])
        elif binding.disposition == "core_stop":
            binding = _binding(final[order_id], "core_stop", affects=tuple(stopped.get(order_id, ())))
        result.append(binding)
    logistics, not_consumed = logistics_from_events(events)
    return AdaptedInputs(tuple(built) + made + logistics, tuple(result), not_consumed)


def queued_start(deliveries, stops) -> list:
    """The engine's queue (family_engine._queue_delivery), rebuilt from the contracts.

    A timed bag of one kind starts when the earlier timed bags of that kind that are
    still running at its minute have finished. "Stop IV fluids" closes every running
    crystalloid at its minute, so it no longer delays a later bag. Untimed orders start at
    once and share their line (``delivery_contributors``).
    """
    placed = []
    for item in deliveries:
        duration = _duration(item.action)
        # As the legacy adapter reads the engine's receipt: a timed bag's start is a float
        # (the engine reports it), an untimed order starts at its whole minute.
        start = item.minute if duration is None else float(item.minute)
        if duration is not None:
            for earlier in placed:
                earlier_duration = _duration(earlier.action)
                if earlier.kind != item.kind or earlier_duration is None:
                    continue
                closed = item.kind == "fluid" and any(
                    earlier.position < position <= item.position for position, _ in stops)
                end = earlier.start + earlier_duration
                if not closed and end > item.minute:
                    start = max(start, end)
        placed.append(Delivery(item.position, item.kind, item.order_id, item.minute, item.action, start))
    return placed


def logistics_from_events(events: Iterable[EventInterruption]) -> tuple:
    """Logistic completions the core models, from EventInterruption v2. Other inputs are refused."""
    built, not_consumed, seen = [], [], set()
    for contract in events:
        if not isinstance(contract, EventInterruption):
            raise ContractInputError(f"not an EventInterruption v2: {type(contract).__name__}")
        if contract.interrupted:
            raise UnsupportedContract("an interrupted turn is not followed by the shadow core yet")
        for event in contract.events:
            kind, cause = event.payload.get("kind"), event.payload.get("cause_class")
            if cause in EVENT_INPUT_CAUSES:
                if cause != "LOGISTIC" or kind not in LOGISTIC_EVENTS:
                    raise UnsupportedContract(f"event {kind!r} ({cause}) changes the legacy patient and is not "
                                              "modelled by the shadow core")
                if kind in seen:
                    raise UnsupportedContract(f"logistic event {kind!r} completes twice")
                minute = event.minute
                if isinstance(minute, bool) or not isinstance(minute, int) or minute < 0:
                    raise ContractInputError(f"logistic event {kind!r} has no whole minute: {minute!r}")
                seen.add(kind)
                built.append(EndoscopicHemostasis(LOGISTIC_EVENTS[kind], minute))
            else:
                not_consumed.append({"kind": kind, "cause_class": cause, "minute": event.minute})
    return tuple(built), tuple(not_consumed)


def _actions_by_id(actions) -> dict:
    by_id = {}
    for action in actions:
        known = by_id.get(action.order_id)
        if known is None:
            by_id[action.order_id] = action
        elif (known.submission_id, known.action_class, known.fields) != (
                action.submission_id, action.action_class, action.fields):
            raise ContractInputError(f"order {action.order_id} is carried forward with a different identity or "
                                     "payload")
    return by_id


def _final_fates(fates) -> dict:
    """The last receipt of each order. A held order may run later; an order that ran stays as it ran."""
    final = {}
    for fate in fates:
        known = final.get(fate.order_id)
        if known is not None and (known.submission_id, known.action_class) != (fate.submission_id, fate.action_class):
            raise ContractInputError(f"order {fate.order_id} changes its submission or class between receipts")
        if known is not None and known.fate == "EXECUTED" and (fate.fate, fate.executed_at_min) != (
                known.fate, known.executed_at_min):
            raise ContractInputError(f"order {fate.order_id} ran at minute {known.executed_at_min} and is later "
                                     f"reported as {fate.fate} at {fate.executed_at_min}")
        final[fate.order_id] = fate
    return final


def _check_times(times, final) -> None:
    for turn in times:
        if not isinstance(turn, TurnTime):
            raise ContractInputError(f"not a TurnTime v2: {type(turn).__name__}")
        if turn.interrupted:
            raise UnsupportedContract("an interrupted turn is not followed by the shadow core yet")
        for timing in turn.order_timing:
            fate = final.get(timing.order_id)
            if fate is None:
                raise UnsupportedContract(f"TurnTime names order {timing.order_id}, which has no FateReceipt")
            if timing.executed_at_min is not None and fate.executed_at_min is not None \
                    and timing.executed_at_min != fate.executed_at_min:
                raise ContractInputError(f"order {timing.order_id}: TurnTime and FateReceipt disagree on when it ran")


def _minute(fate: FateReceipt) -> int:
    minute = fate.executed_at_min
    if isinstance(minute, bool) or not isinstance(minute, int) or minute < 0:
        raise ContractInputError(f"executed order {fate.order_id} has no whole executed_at_min: {minute!r}")
    return minute


def _check_fields(order_id, kind, fields) -> None:
    if kind not in FIELDS:
        raise UnsupportedContract(f"order {order_id}: class {kind!r} has no shadow-core equivalent yet")
    if fields.get("type") != kind:
        raise ContractInputError(f"order {order_id}: class {kind!r} but engine type {fields.get('type')!r}")
    extra = sorted(key for key, value in fields.items() if key not in FIELDS[kind] and value is not None)
    if extra:
        raise UnsupportedContract(f"order {order_id} ({kind}) carries {extra}, which the shadow core does not follow")


def _check_delivery(order_id, kind, fields) -> None:
    if kind == "fluid":
        if fields.get("operation") is not None:
            raise UnsupportedContract(f"order {order_id}: fluid operation {fields['operation']!r} is not followed")
        if fields.get("fluid_type") not in CRYSTALLOIDS:
            raise UnsupportedContract(f"order {order_id}: fluid {fields.get('fluid_type')!r} is not a crystalloid "
                                      "the shadow core follows")
        route = fields.get("route")
        if route is not None and str(route).upper() not in FLUID_ROUTES:
            raise UnsupportedContract(f"order {order_id}: crystalloid route {route!r} is not IV or IO")
        rate = fields.get("rate_ml_h")
        if rate is not None:
            duration = _duration(fields)
            if duration is None or abs(float(fields["volume_ml"]) / float(rate) * 60 - duration) > 1e-9:
                raise UnsupportedContract(f"order {order_id}: rate {rate!r} mL/h does not match its duration")


def _fio2(order_id, fields, devices: Mapping) -> float:
    raw = str(fields.get("device") or "").strip()
    device = devices.get(raw.lower(), raw if raw in set(devices.values()) else None)
    if device == NASAL_CANNULA[0]:
        flow = fields.get("flow_lpm")
        if flow is None:
            raise UnsupportedContract(f"order {order_id}: nasal cannula without a flow")
        _, base, per_lpm, cap = NASAL_CANNULA
        return min(cap, base + per_lpm * float(flow))
    if device not in OXYGEN_FIO2:
        raise UnsupportedContract(f"order {order_id}: oxygen device {raw!r} is not one the engine names")
    return OXYGEN_FIO2[device]


def _duration(fields: Mapping):
    value = fields.get("administration_duration_min")
    return None if value is None else float(value)


def _binding(fate: FateReceipt, disposition: str, source_key=None, start=None, affects=()) -> OrderBinding:
    return OrderBinding(fate.order_id, fate.submission_id, fate.action_class, fate.fate, fate.executed_at_min,
                        disposition, source_key, start, affects)
