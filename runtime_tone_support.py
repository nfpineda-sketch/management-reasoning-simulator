"""P3-396 / P3-397 / P3-431 / P3-435: the common vasoconstrictor support of PHASE2_AMENDMENT_3, mapped for a DEVELOPMENT shadow run.

What this is. The common core gained one general state, the vasoconstrictor support (``aux.vasoconstrictor_support``), read
by the tone target through one bounded factor that is UNSET by default (``clinical_core.vascular_support``). This module is
the Phase-3 side of it and nothing more: it makes a development COPY of a family's shadow adapter that

- declares the reader with ONE witness of the development behavioural region (``with_tone_support``), and
- maps the encounter's norepinephrine orders -- a START, and after it every order that itself gives an absolute rate in
  mcg/min (an increase, a decrease, a restart) or stops the infusion -- to ONE writer of that state.

The mapping is the same for every family: it reads the orders and the witness, never the case, the family or the patient's
state, and it builds no pressure. What the orders do to the pressure is whatever the common core's tone, flow, preload and
pump make of them.

P3-431, the rate history (FD-TITRATE-01 to FD-TITRATE-13). The engine holds ONE absolute rate for the infusion and every
order of the kind replaces it; the mapping mirrors exactly that: the rate ordered at a time is the last valid order's, and
the encounter has ONE infusion and ONE writer, never two streams. An encounter with a single start still builds the core's
own writer, ``clinical_core.vascular_support.Norepinephrine``, exactly as before; any longer history builds
``NorepinephrineRateHistory``, which IS that writer (a subclass: the same constants, the same change, the same state, the
same grid) with the one thing the core's closed form lacks, a rate that changes: its contribution approaches the steady
support of the rate ordered, with the writer's own ONSET constant while it is below it and its own OFFSET constant while
it is above it. A start from nothing and a stop are that rule's two ends, and for them the arithmetic is the core's own,
bit for bit. Nothing here is new physiology: no constant, no reader, no equation of the core changes, and the core is
not edited.

P3-435, after the independent adversarial review. Within one minute the infusion carries ONE order, the last valid one;
an order replaced within its minute, a stop of nothing and a refused order are DECLARED gaps, and a declared order never
becomes a carried one when more orders arrive (the session's gaps only accumulate). The orders are read in the mirror's
own order, which is the engine's; orders that arrive against the clock are not sorted into place, they are refused.

What it is not.

- Not registered. ``runtime_shadow_families.ADAPTERS`` is untouched: no registered adapter declares the reader, so no
  encounter's own shadow run, no ensemble and no certified record changes.
- Not authority. ``runtime_authority.SUPPORTED_ACTIONS`` is untouched and the live grant names norepinephrine among what it
  does NOT grant: the GI pressure development authority still stops on the order, exactly as FR-F was certified
  (``HALTED_BY_UNSUPPORTED_ACTION``).
- Not a titration engine. Only rates a clinician ordered, in mcg/min: no pressure target, no protocol, no closed loop and
  no weight-based dose (an order in mcg/kg/min is refused, never converted). The order is read AS WRITTEN: one that gives
  no units is refused though the engine would complete it from the running infusion, because a bare number is not always
  a rate. An order the mapping cannot read fails CLOSED: it and every later order of the kind are DECLARED gaps, reported
  with their reason, and the run says it no longer mirrors the encounter's vasopressor. So does an order that names NO
  drug ("stop the infusion") while the norepinephrine runs: the engine applies it to whichever infusion is running and
  the mirror does not say to which, so the run cannot know what became of the norepinephrine. Nothing is dropped and
  nothing is guessed; what the run then keeps computing is the history it had mapped, which is no longer the encounter's.
- Not combined with the Amendment-2 consciousness witnesses: that interaction has not been reviewed, and it is refused.
- Not a calibration. A witness is a probe of a region whose every magnitude has a confidence below 0.80; nothing here
  reads the ratified development snapshot, and no constant of the writer is changed by an order.
- Not for residents. Nothing here is read by the page, the scoring or the first pilot.
"""
from __future__ import annotations

import copy
import dataclasses
import math
from typing import Any, Mapping, Sequence

from clinical_core import vascular_support as _vs
from clinical_core.integration import NOTHING, Contribution, register
from clinical_core.provenance import VasoconstrictionChange
from clinical_core.state import CoreInvariantError

import runtime_shadow as rs
import runtime_shadow_families as fam

MODULE_VERSION = "P3-431"
REVISION = "PHASE2_AMENDMENT_3"
STATUS = "DEVELOPMENT_SHADOW_ONLY"
#: The engine's own action type for the orders (``family_parser``), and the shapes of it this mapping reads.
ORDER_KIND = "norepinephrine"
#: The engine's action type for an order that names NO drug ("stop the infusion", "increase the infusion rate to ..."): the
#: engine applies it to whichever infusion is running, and the mirror hands it over as written, without saying to which.
ROLE_KIND = "infusion_adjustment"
#: The operation that opens the encounter's infusion: the run must have SEEN it start.
MAPPED_OPERATION = "start"
STOP_OPERATION = "stop"
#: The engine's whole vocabulary for an infusion (``family_engine``): each sets ONE absolute rate, or stops it.
MAPPED_OPERATIONS = ("start", "adjust", "continue", "stop")
MAPPED_UNITS = "mcg/min"
#: The writer of a rate history, by version: an artifact names it, and a rebuild under another version is refused.
WRITER_VERSION = "norepinephrine_rate_history/P3-431"
#: What a specification of a rate history must NAME to be rebuilt: none of them is filled in by a default.
SPEC_NAMES = ("changes", "orders", "rate_units", "writer_version")
#: The profile field the development copy declares; it exists only in PHASE2_AMENDMENT_3 and its registered successors.
PROFILE_FIELD = "vasoconstrictor_support_to_tone_gain"
NOT_GRANTED = ("runtime authority", "a registered adapter", "resident visibility", "scoring", "the first pilot",
               "a clinical dose-response", "an mmHg target", "automatic titration (a pressure target, a protocol, a closed loop)",
               "a weight-based dose", "any other vasopressor", "clinical validation")

#: What a CARRIED order did to the encounter's ONE infusion, read against the rate that ran just before it.
STARTED, INCREASED, DECREASED, STOPPED, RESTARTED = "STARTED", "INCREASED", "DECREASED", "STOPPED", "RESTARTED"
#: The same rate again, or a stop of an infusion already stopped: carried, and nothing changes (never counted twice).
IDEMPOTENT = "IDEMPOTENT_NO_CHANGE"
OUTCOMES = (STARTED, INCREASED, DECREASED, STOPPED, RESTARTED, IDEMPOTENT)
#: What an order that is NOT carried is, in the order log. Each is a DECLARED gap of the run, with its reason.
REFUSED = "REFUSED_FAIL_CLOSED"
REPLACED = "REPLACED_WITHIN_ITS_MINUTE"
NOTHING_TO_BUILD = "NOTHING_TO_BUILD"
NOT_CARRIED = (REFUSED, REPLACED, NOTHING_TO_BUILD)

#: Why an order is not carried. Each is a declared gap of the run. A gap never becomes a carried order afterwards: what a
#: reason depends on (the order itself, the orders before it, and whether a later order of its own minute exists) does not
#: change once it is true.
GAP_OPERATION = ("norepinephrine {operation} is not an operation this mapping reads (start, adjust, continue or stop, each "
                 "with one absolute rate): nothing is guessed")
GAP_TYPE = "an order mirrored as norepinephrine whose own action says it is {type}: the two disagree, and nothing is guessed"
GAP_NO_UNITS = ("a norepinephrine {operation} that gives no units is not mapped: the engine completes it from the running "
                "infusion, and this mapping reads only an order that says mcg/min itself (a bare number may be a pressure "
                "target, and is never read as a rate)")
GAP_UNITS = ("norepinephrine in {units} is not mapped: only a fixed rate in mcg/min (a weight-based dose is never converted: "
             "it needs a weight this mapping does not read)")
GAP_RATE = "a norepinephrine {operation} without a finite positive rate is not mapped"
GAP_TWO_RATES = "a norepinephrine {operation} that carries two different rates is not mapped: nothing is guessed"
GAP_RECEIPT = ("the engine's own receipt of this norepinephrine {operation} does not say what the order says ({what}): the two "
               "disagree, and nothing is guessed")
GAP_NOT_STARTED = ("norepinephrine {operation} before any start the run saw: an infusion the run never saw start is not "
                   "mapped")
GAP_CHRONOLOGY = ("a norepinephrine order without an identity or a whole minute, or orders that arrive against the clock: the "
                  "order of the encounter's infusion cannot be established, so none of its orders is mapped")
GAP_ROLE_NAMED = ("an order that names no drug (an infusion adjustment) arrived while the encounter's norepinephrine was running: "
                  "the engine applies it to whichever infusion is running and the mirror does not say to which, or to what rate, "
                  "so it may have changed or stopped the norepinephrine and nothing is guessed")
#: After an order the mapping refused, the infusion is CLOSED: the rate the engine runs is no longer known to the run.
GAP_AFTER_A_REFUSED_ORDER = ("norepinephrine {operation} after an order the run could not map is not mapped: the run keeps the "
                             "infusion history it had mapped and no longer mirrors the encounter's vasopressor")
GAP_NOT_MIRRORED = ("the encounter's first norepinephrine order was not mapped, so the run does not mirror its vasopressor and "
                    "maps no later order of the kind either")
GAP_REPLACED = ("norepinephrine {operation} was replaced within its own minute by a later order, before any modelled interval: "
                "nothing carries it")
GAP_NOTHING_TO_BUILD = ("a norepinephrine {operation} that leaves nothing running before any modelled interval carried the infusion: "
                        "nothing was running, so there is nothing to build")
NOT_MIRRORED = "The run does not mirror the encounter's vasopressor"
NO_LONGER_MIRRORED = "From this order on the run no longer mirrors the encounter's vasopressor"


class ToneSupportUnavailable(RuntimeError):
    """The common vasoconstrictor reader cannot be declared: the live core is not a certified member that carries it."""


def availability() -> str | None:
    """None when a development run may declare the reader, else why not. Fail closed on the core's lineage: the field
    exists only in PHASE2_AMENDMENT_3 and its registered successors, and only a CERTIFIED active core is run."""
    try:
        import runtime_shadow_evidence as evidence          # it imports the families module: resolved at call time
        if not evidence.core_lineage_ok():
            return evidence.core_lineage_reason() or "the common core lineage could not be evaluated"
        active = evidence.core_lineage_verdict().get("active_core")
    except Exception as error:
        return f"the common core lineage could not be evaluated: {type(error).__name__}"
    if not rs.core_is_or_descends_from(active, (REVISION,)):
        return f"the common vasoconstrictor reader exists only in {REVISION} and its registered successors; the live core is {active}"
    return None


def witness_values(name: str) -> dict:
    """The named witness of the development region, as plain data (the core validates the name and the bounds)."""
    return _vs.witness(name)


# -- the writer of a rate history ------------------------------------------------------------------------------------------

def _whole(minute) -> bool:
    return not isinstance(minute, bool) and isinstance(minute, int) and minute >= 0


def _number(value) -> float | None:
    """``value`` as a finite float, or None for anything that is not one (a bool, a word, a number too large to be one)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except (OverflowError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _ordered_rate(rate) -> float:
    number = _number(rate)
    if number is None or number < 0.0:
        raise CoreInvariantError("an ordered norepinephrine rate is a finite number at or above 0 (0 is a stop)")
    return number


def outcome_of(before: float, rate: float) -> str:
    """What an order to ``rate`` did to an infusion that ran at ``before`` (0 for a stopped one)."""
    if rate == before:
        return IDEMPOTENT
    if rate == 0.0:
        return STOPPED
    if before == 0.0:
        return RESTARTED
    return INCREASED if rate > before else DECREASED


def physical_history(orders: Sequence) -> tuple:
    """The rate the infusion RUNS at, minute by minute of change, from the orders it carries ``(order id, minute, rate ordered,
    outcome)``: one order a minute, in time, and a rate equal to the one already running changes nothing.
    ``((minute, rate), ...)``, strictly later minutes, each rate different from the last."""
    out = []
    for _order, minute, rate, _outcome in orders:
        if out and out[-1][1] == rate:
            continue
        out.append((minute, rate))
    return tuple(out)


def _approach(level: float, target: float, elapsed, onset: float, offset: float) -> float:
    """Where a contribution that was at ``level`` is after ``elapsed`` minutes of approaching ``target``: first order, with the
    writer's ONSET constant while it is below the target and its OFFSET constant while it is above it, and never past the
    target (the bound is held exactly, not left to the rounding). From nothing (level 0) and to nothing (target 0) these
    are, term for term, the two expressions of the core's own closed form."""
    if target > level:
        return min(target, level + (target - level) * -math.expm1(-elapsed / onset))
    if target < level:
        return max(target, target + (level - target) * math.exp(-elapsed / offset))
    return level


@register
@dataclasses.dataclass(frozen=True)
class NorepinephrineRateHistory(_vs.Norepinephrine):
    """The encounter's ONE norepinephrine infusion when it carries more than one order: the core's writer, with a rate that
    changes.

    It IS ``clinical_core.vascular_support.Norepinephrine`` (the same constants, the same ``VasoconstrictionChange``, the
    same common state, the same grid) and it writes the same ONE thing: the change of its own contribution to the support
    in a minute. ``start_minute`` and ``rate_mcg_min`` are the first rate the infusion ran at; ``changes`` are the later
    ones, ``(minute, rate)`` with 0 for a stop, each at a strictly later minute and different from the rate before it. The
    rate ordered at a time is the LAST of them at or before it: one rate, never a sum of several. The contribution
    approaches the steady support of that rate (rate over half-effect rate) from wherever it is, with the onset constant
    while it is below it and the offset constant while it is above it, so a change of rate never moves it in the minute of
    the order and a stop never erases it. An order at minute s first acts over (s, s + 1], like every intervention. What
    this says about the CONTRIBUTION is exactly that: it moves toward the rate ordered and never past it. It does not say
    the contribution falls the moment a lower rate is ordered: a decrease ordered while the contribution is still below
    the lower rate's steady support keeps rising toward it, more slowly and to a lower level than without the order.

    A closed form of the orders and of time only: it reads no pressure, tone, output, delivery, volume, pump or any other
    reading (the writer contract), so nothing here closes a loop or titrates. ``orders`` is the accounting, never read by
    the contribution: every order the infusion CARRIES, ``(order id, minute, rate ordered, outcome)``, one a minute, the
    first the order that started it, each outcome what that rate did to the rate before it; and the history above must be
    exactly what those orders make (a history that its orders do not explain, or an outcome they do not give, is refused).
    """

    type_name = "norepinephrine_rate_history"

    changes: tuple = ()
    orders: tuple = ()
    rate_units: str = MAPPED_UNITS
    writer_version: str = WRITER_VERSION

    def __post_init__(self):
        super().__post_init__()
        if self.stop_minute is not None:
            raise CoreInvariantError("a rate history holds a stop as a change to a rate of 0, never as a stop minute")
        if self.rate_units != MAPPED_UNITS:
            raise CoreInvariantError(f"a rate history is in {MAPPED_UNITS} and nothing else: {self.rate_units!r} is not read")
        if self.writer_version != WRITER_VERSION:
            raise CoreInvariantError(f"this is {WRITER_VERSION}; a history written by {self.writer_version!r} is not rebuilt by it")
        try:
            changes = tuple((minute, _ordered_rate(rate)) for minute, rate in self.changes)
            orders = tuple((order, minute, _ordered_rate(rate), outcome) for order, minute, rate, outcome in self.orders)
        except (TypeError, ValueError) as error:
            raise CoreInvariantError(f"a rate history is ((minute, rate), ...) with its orders ((id, minute, rate, outcome), ...): {error}")
        object.__setattr__(self, "changes", changes)
        object.__setattr__(self, "orders", orders)
        last_minute, last_rate = self.start_minute, float(self.rate_mcg_min)
        for minute, rate in changes:
            if not _whole(minute) or minute <= last_minute:
                raise CoreInvariantError("each change of the rate is at a whole minute after the one before it")
            if rate == last_rate:
                raise CoreInvariantError("a change of the rate changes it: the same rate again is not a change")
            if not rate / self.half_effect_rate_mcg_min < _vs.SUPPORT_LIMIT:
                raise CoreInvariantError(f"a norepinephrine rate of {_vs.SUPPORT_LIMIT:g} times its half-effect rate or more is not "
                                         "an order this writer represents")
            last_minute, last_rate = minute, rate
        if not orders or any(not isinstance(order, str) or not order or not _whole(minute) for order, minute, _rate, _outcome in orders):
            raise CoreInvariantError("a rate history names every order it carries, each by its own id and at a whole minute")
        if len({order for order, _minute, _rate, _outcome in orders}) != len(orders) or orders[0][0] != self.id:
            raise CoreInvariantError("each order is carried once, and the infusion has the id of the order that started it")
        if any(later[1] <= earlier[1] for earlier, later in zip(orders, orders[1:])):
            raise CoreInvariantError("the infusion carries one order a minute, in time: an order replaced within its minute is not carried")
        if orders[0][1:] != (self.start_minute, float(self.rate_mcg_min), STARTED):
            raise CoreInvariantError("the first order the infusion carries is the one that started it, at its first rate")
        if any(later[3] != outcome_of(earlier[2], later[2]) for earlier, later in zip(orders, orders[1:])):
            raise CoreInvariantError("each order's outcome is what its rate did to the rate before it: another one is refused")
        if physical_history(orders) != ((self.start_minute, float(self.rate_mcg_min)),) + changes:
            raise CoreInvariantError("the rate history is not what its orders make: a history its orders do not explain is refused")

    @classmethod
    def from_spec_data(cls, data: Mapping):
        """Rebuilt from a specification that NAMES its history, its orders, its units and its writer's version: a field that
        is missing is not filled in by a default, so an artifact cut short is refused and never read as something else."""
        missing = [name for name in SPEC_NAMES if name not in data]
        if missing:
            raise CoreInvariantError(f"a rate history is rebuilt only from a specification that names {', '.join(missing)}")
        return cls(**dict(data))

    @property
    def carried_order_ids(self) -> tuple:
        """Every mirrored order this ONE contributor answers for (``runtime_shadow_families.action_dispositions``)."""
        return tuple(order for order, _minute, _rate, _outcome in self.orders)

    def ordered_rate_over(self, minute: float) -> float:
        """The rate ordered for the interval that ends at ``minute``: the last one ordered BEFORE it (an order at minute s
        first acts over (s, s + 1]); 0 before the start and after a stop."""
        if minute <= self.start_minute:
            return 0.0
        rate = float(self.rate_mcg_min)
        for at, later in self.changes:
            if minute <= at:
                break
            rate = later
        return rate

    def support_at(self, minute: float) -> float:
        """Its own contribution to the common support at the end of ``minute``, on the writers' grid. Without a change of
        rate it is the core's own closed form, called as it is. With changes it is the same approach, segment by segment:
        each starts where the one before it ended (off the grid, as the core carries the value a stop decays from) and
        approaches its own rate's steady support, so an earlier minute never depends on a later order."""
        if not self.changes:
            return super().support_at(minute)
        if minute <= self.start_minute:
            return 0.0
        level, since, target = 0.0, self.start_minute, self.rate_mcg_min / self.half_effect_rate_mcg_min
        for at, rate in self.changes:
            if minute <= at:
                break
            level = _approach(level, target, at - since, self.onset_tau_min, self.offset_tau_min)
            since, target = at, rate / self.half_effect_rate_mcg_min
        return _vs.on_the_grid(_approach(level, target, minute - since, self.onset_tau_min, self.offset_tau_min))

    def contribute(self, state, minute, signals, anchors, profile) -> Contribution:
        amount = self.support_at(minute) - self.support_at(minute - 1)
        if amount == 0.0:
            return NOTHING
        rate = self.ordered_rate_over(minute)
        return Contribution(vasoconstriction=(VasoconstrictionChange(
            amount, self.source, minute,
            f"norepinephrine {rate:g} mcg/min approaching its steady support" if rate > 0.0
            else "norepinephrine stopped: its support decaying"),))


def ensure_registered() -> None:
    """Make BOTH writers this mapping builds rebuildable from their specification in the registry that is live NOW: the core's own
    ``Norepinephrine`` and the rate history. Each registers when its module is first imported, and a registry that is swapped at
    that moment does not keep it: a historical view of an earlier tree lists the core's older types only, and a replay that
    first imports the core's module UNDER such a view (a module-scoped view does this) leaves the core's own writer
    unregistered for the rest of the process, so that a later, ordinary run of this mapping could build a writer its own
    artifact cannot rebuild. The mapping therefore asks again each time it builds, and a replay may ask too. Registering the
    same class again is the core's own no-op; nothing of the core is edited."""
    register(_vs.Norepinephrine)
    register(NorepinephrineRateHistory)


# -- the orders ---------------------------------------------------------------------------------------------------------------

def order_disposition(action: Mapping | None, receipt: Mapping | None = None) -> tuple:
    """(the absolute rate the order sets in mcg/min, None) -- 0.0 for a stop -- when the order is one this mapping reads: a
    start, an adjustment or a continuation that itself says a finite positive rate in mcg/min, or a stop; (None, None) for a
    BARE continuation, one that gives no rate and no units and so keeps the rate ordered before it; (None, why) otherwise.

    The order is read AS WRITTEN (the action the mirror hands over is the parsed order, before the engine completes it): an
    order that gives no units is refused, though the engine would run it at the running infusion's units, because a bare
    number is not always a rate. When the engine's receipt of the order is there, it must say the same operation, units and
    rate; a disagreement is refused. It judges the order ALONE: whether the run saw the infusion start, and whether the
    core's writer represents the rate, are ``infusion_history``'s."""
    action = dict(action) if isinstance(action, Mapping) else {}
    receipt = dict(receipt) if isinstance(receipt, Mapping) else {}
    operation = action.get("operation")
    if not isinstance(operation, str) or operation not in MAPPED_OPERATIONS:
        return None, GAP_OPERATION.format(operation=repr(operation))
    if action.get("type") not in (None, ORDER_KIND):
        return None, GAP_TYPE.format(type=repr(action.get("type")))
    if receipt.get("operation") not in (None, operation):
        return None, GAP_RECEIPT.format(operation=operation, what="the operation")
    if operation == STOP_OPERATION:
        return 0.0, None
    units, rate = action.get("units"), _number(action.get("rate"))
    if receipt.get("units") not in (None, MAPPED_UNITS):
        return None, GAP_RECEIPT.format(operation=operation, what="the units")
    if operation == "continue" and units is None and action.get("rate") is None and action.get("rate_mcg_min") is None:
        return None, None
    if units is None:
        return None, GAP_NO_UNITS.format(operation=operation)
    if units != MAPPED_UNITS:
        return None, GAP_UNITS.format(units=repr(units))
    if rate is None or rate <= 0.0:
        return None, GAP_RATE.format(operation=operation)
    if action.get("rate_mcg_min") is not None and _number(action.get("rate_mcg_min")) != rate:
        return None, GAP_TWO_RATES.format(operation=operation)
    if receipt.get("rate") is not None and _number(receipt.get("rate")) != rate:
        return None, GAP_RECEIPT.format(operation=operation, what="the rate")
    return rate, None


def infusion_history(events: Sequence, witness: Mapping) -> tuple:
    """(physical, carried, declared) for the encounter's infusion orders, given in the engine's order.

    ONE infusion and ONE ordered rate: each order the mapping reads REPLACES the rate ordered before it (the engine's own
    rule). The run must have SEEN the infusion start: until a start is read nothing else is.

    - ``carried`` is ``((order id, minute, rate ordered, outcome), ...)``: the orders the infusion answers for, ONE a minute
      (the last valid order of each minute, the only one a modelled interval ever carries), from the first that leaves a
      rate running. Each has what it did to the rate that ran before it: STARTED, then INCREASED, DECREASED, STOPPED,
      RESTARTED or IDEMPOTENT_NO_CHANGE. ``physical`` is the rate history they make (``physical_history``).
    - ``declared`` is ``((order id, kind, what, why), ...)``, in the engine's order: every order that is NOT carried, each
      with its own reason. REFUSED_FAIL_CLOSED: the FIRST order the mapping cannot read -- an operation or units it does not
      know, no units, a rate that is not a finite positive number, a receipt that disagrees, an adjustment or a stop of an
      infusion the run never saw start, a rate the core's writer refuses, or an order that names no drug while the
      norepinephrine runs -- CLOSES the infusion: it and every later order of the kind are refused, and nothing after it is
      applied, because the rate the engine runs is no longer known to the run. REPLACED_WITHIN_ITS_MINUTE: a valid order that
      a later order of its own minute replaced (a valid one, or the one that closed the infusion) before any modelled
      interval. NOTHING_TO_BUILD: an order that leaves nothing running while nothing had ever run.

    A declared order never becomes a carried one when more orders arrive: each reason depends on the order, on those before
    it, and on whether a later order of its own minute exists."""
    ordered, opened, closed_at = 0.0, False, None
    valid, declared = [], {}
    for event in events:
        action = event.action if isinstance(event.action, Mapping) else {}
        operation = action.get("operation")
        if event.kind == ROLE_KIND:
            if closed_at is None and ordered > 0.0:       # as far as the run knows the norepinephrine is running: the order may be its own
                declared[event.order_id] = (ROLE_KIND, REFUSED, f"{GAP_ROLE_NAMED}. {NO_LONGER_MIRRORED}")
                closed_at = event.minute
            continue
        if closed_at is not None:
            declared[event.order_id] = (ORDER_KIND, REFUSED, GAP_AFTER_A_REFUSED_ORDER.format(operation=repr(operation)) if opened else GAP_NOT_MIRRORED)
            continue
        rate, why = order_disposition(event.action, event.receipt)
        if why is None and not opened and operation != MAPPED_OPERATION:
            why = GAP_NOT_STARTED.format(operation=repr(operation))
        if why is None and rate is None:                   # a bare continuation keeps the rate ordered before it, and the engine's receipt, when there, must say that rate
            rate, said = ordered, (event.receipt if isinstance(event.receipt, Mapping) else {}).get("rate")
            if said is not None and _number(said) != ordered:
                why = GAP_RECEIPT.format(operation=operation, what="the rate")
        if why is None and rate > 0.0:
            try:                                           # the core's own writer judges the rate: what it refuses is not an order this run represents
                _vs.Norepinephrine(event.order_id, event.minute, rate, half_effect_rate_mcg_min=float(witness["half_effect_rate_mcg_min"]),
                                   onset_tau_min=float(witness["onset_tau_min"]), offset_tau_min=float(witness["offset_tau_min"]))
            except Exception as error:
                why = f"the core's writer refuses this order: {error}"
        if why is not None:
            declared[event.order_id] = (ORDER_KIND, REFUSED, f"{why}. {NO_LONGER_MIRRORED if opened else NOT_MIRRORED}")
            closed_at = event.minute
            continue
        valid.append((event.order_id, event.minute, rate, operation))
        ordered, opened = rate, True
    carried = []
    for index, (order, minute, rate, operation) in enumerate(valid):
        replaced = (index + 1 < len(valid) and valid[index + 1][1] == minute) or closed_at == minute
        if rate == 0.0 and not carried:
            declared[order] = (ORDER_KIND, NOTHING_TO_BUILD, GAP_NOTHING_TO_BUILD.format(operation=operation))
        elif replaced:
            declared[order] = (ORDER_KIND, REPLACED, GAP_REPLACED.format(operation=operation))
        else:
            carried.append((order, minute, rate, outcome_of(carried[-1][2], rate) if carried else STARTED))
    in_order = tuple((event.order_id,) + declared[event.order_id] for event in events if event.order_id in declared)
    return physical_history(carried), tuple(carried), in_order


def _ours(mirrored: Sequence) -> tuple:
    """(the encounter's infusion orders in the engine's own order, ()) -- the mirror's order, an order id once: the orders of the
    kind and, among them, the ones that name no drug -- or (None, the orders of the kind) when that order cannot be
    established: one of them has no identity (a non-empty text id), or no whole minute, or is dated before one that came
    before it."""
    found, seen, broken, last = [], set(), False, 0
    for event in mirrored:
        if event.kind not in (ORDER_KIND, ROLE_KIND):
            continue
        if not isinstance(event.order_id, str) or not event.order_id:
            broken = True
            found.append(event)
            continue
        if event.order_id in seen:
            continue
        seen.add(event.order_id)
        found.append(event)
        if not _whole(event.minute) or event.minute < last:
            broken = True
        else:
            last = event.minute
    if broken:
        return None, tuple(event for event in found if event.kind == ORDER_KIND)
    return tuple(found), ()


def map_orders(mirrored: Sequence, built: Sequence, gaps: Sequence, witness: Mapping) -> tuple:
    """(contributors, gaps) with every norepinephrine order either carried by the encounter's ONE infusion or DECLARED with its own reason.

    ``built`` and ``gaps`` are what the own mapping of the run returned: it knows no vasopressor, so each order of the kind arrives as a gap.
    The orders are taken in the engine's own order (the mirror's), an order id counts once, and ``infusion_history`` reads them: one infusion,
    one ordered rate, each order replacing the one before it. A single carried order builds the core's own writer, as it always did; more
    of them build ``NorepinephrineRateHistory``, which names every order it carries. An order that is not carried -- refused, with every
    order after it (fail closed); replaced within its minute; a stop of nothing -- is a declared gap with its reason, and stays one. An
    order that names no drug closes the infusion when the norepinephrine may be the one it changed. A run that already carries a
    norepinephrine writer is refused outright: one writer of the kind, never two. Nothing else in ``built`` or ``gaps`` is touched."""
    ensure_registered()
    made = list(built)
    if any(isinstance(item, _vs.Norepinephrine) for item in made):
        raise ToneSupportUnavailable("the run already carries a norepinephrine writer: one writer of the kind, never two")
    events, unplaced = _ours(mirrored)
    kept = [dict(gap) for gap in gaps if gap.get("kind") != ORDER_KIND]
    if events is None:
        return tuple(made), kept + [{"order_id": event.order_id, "kind": ORDER_KIND, "why": f"{GAP_CHRONOLOGY}. {NOT_MIRRORED}"} for event in unplaced]
    physical, carried, declared = infusion_history(events, witness)
    if carried:
        (first, first_minute, first_rate, _first_outcome), constants = carried[0], {name: float(witness[name]) for name in ("half_effect_rate_mcg_min", "onset_tau_min", "offset_tau_min")}
        if len(carried) == 1:
            made.append(_vs.Norepinephrine(first, first_minute, first_rate, **constants))
        else:
            made.append(NorepinephrineRateHistory(first, first_minute, first_rate, changes=physical[1:], orders=carried, **constants))
    ours = [order for order, kind, _what, _why in declared if kind == ROLE_KIND]
    kept = [gap for gap in kept if not (gap.get("kind") == ROLE_KIND and gap.get("order_id") in ours)]
    kept.extend({"order_id": order, "kind": kind, "why": why} for order, kind, _what, why in declared)
    return tuple(made), kept


def order_log(mirrored: Sequence, witness: Mapping) -> list:
    """One row per infusion order of the encounter that concerns its norepinephrine, in the engine's order: what was ordered and
    what became of it -- carried by the ONE infusion, with what it did to it, or not carried, with why (refused, replaced
    within its minute, or a stop of nothing). For a record or a reader: it decides nothing, it reads ``infusion_history``."""
    events, unplaced = _ours(mirrored)
    if events is None:
        return [{"order_id": event.order_id, "minute": event.minute, "kind": ORDER_KIND, "outcome": REFUSED, "carried": False,
                 "why": f"{GAP_CHRONOLOGY}. {NOT_MIRRORED}"} for event in unplaced]
    _physical, carried, declared = infusion_history(events, witness)
    did = {order: (rate, outcome) for order, _minute, rate, outcome in carried}
    why_not = {order: (what, why) for order, _kind, what, why in declared}
    rows = []
    for event in events:
        if event.order_id not in did and event.order_id not in why_not:
            continue                                        # an order that names no drug while no norepinephrine ran: not this infusion's
        action = event.action if isinstance(event.action, Mapping) else {}
        row = {"order_id": event.order_id, "minute": event.minute, "kind": event.kind, "operation": action.get("operation"),
               "rate": action.get("rate"), "units": action.get("units")}
        if event.order_id in did:
            rate, outcome = did[event.order_id]
            row.update(outcome=outcome, carried=True, ordered_rate_mcg_min=rate, replaced_within_its_minute=False,
                       first_acts_over=[event.minute, event.minute + 1], why=None)
        else:
            what, why = why_not[event.order_id]
            row.update(outcome=what, carried=False, ordered_rate_mcg_min=None, replaced_within_its_minute=what == REPLACED, first_acts_over=None, why=why)
        rows.append(row)
    return rows


class ToneSupport:
    """What a development copy of an adapter gains (``with_tone_support``). Mixed in BEFORE the family's own adapter class,
    so the family's mapping runs first and unchanged, and this adds one declared profile field and one order mapping."""

    def region_witnesses(self) -> dict:
        """None: a tone-support run opens no ensemble. A family's region witnesses do not carry the reader, and a witness
        is never compared under another run's hemodynamics."""
        return {}

    def profile(self, point: str):
        why = availability()
        if why is not None:
            raise ToneSupportUnavailable(why)
        values = witness_values(self.tone_support_witness)
        return dataclasses.replace(super().profile(point), **{PROFILE_FIELD: float(values["tone_gain"])})

    def snapshot(self, point: str = fam.COMMITTED):
        from clinical_core import vascular_support as vs
        base = super().snapshot(point)
        name = self.tone_support_witness
        values = witness_values(name)
        said = ", ".join(f"{key} = {values[key]}" for key in sorted(values))
        return fam.ShadowParameterSnapshot(
            f"{base.id}+tone_support_{name.lower()}", base.family, base.point,
            tuple(base.provenance) + (
                f"clinical_core.vascular_support.WITNESSES[{name!r}] ({said}): {vs.STATUS} of {REVISION}, a development "
                "witness -- not a selection, not a calibration and not clinical truth",
                "the common vasoconstrictor reader is declared by THIS development run only: no registered adapter declares "
                "it, and the live authority does not grant norepinephrine"))

    def interventions(self, mirrored: Sequence, state: Mapping | None = None) -> tuple:
        built, gaps = super().interventions(mirrored, state)
        return map_orders(mirrored, built, gaps, witness_values(self.tone_support_witness))


def with_tone_support(adapter: Any, witness: str = "CENTER_REFERENCE") -> Any:
    """A development COPY of ``adapter`` (same family, same cases, same mapping) that also declares the common
    vasoconstrictor reader with the named witness and maps the encounter's norepinephrine orders to ONE writer. The adapter
    given is not modified, the copy is never registered, and it is refused for an adapter that already declares the reader.
    The copy's version says the witness and not the mapping's own version: an encounter with a single start is mapped
    exactly as it always was, and a rate history names its writer's version in its own specification."""
    if not isinstance(adapter, fam.RuntimeFamilyAdapter):
        raise TypeError("tone support is declared on a family's shadow adapter")
    if adapter.tone_support_witness is not None:
        raise ValueError("this adapter already declares the common vasoconstrictor reader")
    if adapter.amendment_2_witness is not None:
        # The Amendment-2 consciousness composite reads the pressure, which the support raises while delivery falls: the two together have not
        # been reviewed by the faculty, so the combination is not offered (the interaction is recorded as a core-level probe and a limitation).
        raise ValueError("tone support is not declared on an Amendment-2 consciousness witness: that interaction has not been reviewed")
    witness_values(witness)                                 # an unknown witness is refused here, by name
    base = type(adapter)
    # A class of its own for each copy: the layer keeps no mutable state of its own, not even a cache of these.
    cls = type(f"{base.__name__}WithToneSupport", (ToneSupport, base), {"__doc__": f"{base.__name__} as a development copy that declares {REVISION}'s reader."})
    made = copy.copy(adapter)
    made.__class__ = cls
    made.tone_support_witness = str(witness)
    made.version = f"{adapter.version}+tone_support/{witness}"
    made.maps = tuple(adapter.maps) + (ORDER_KIND,)
    return made


def summary() -> dict:
    """What this mapping is, as plain data for a record. What can be read from the code is read from it."""
    declaring = sorted(name for name, registered in fam.ADAPTERS.items() if registered.tone_support_witness is not None)
    return {"module_version": MODULE_VERSION, "revision": REVISION, "status": STATUS,
            "mapped": {"kind": ORDER_KIND, "opening_operation": MAPPED_OPERATION, "operations": list(MAPPED_OPERATIONS), "units": MAPPED_UNITS,
                       "read_as_written_never_as_the_engine_completed_it": True,
                       "contributor_of_a_single_carried_order": _vs.Norepinephrine.type_name,
                       "contributor_of_a_rate_history": NorepinephrineRateHistory.type_name, "writer_version": WRITER_VERSION,
                       "a_rate_history_is_rebuilt_only_from_a_specification_that_names": list(SPEC_NAMES)},
            "one_infusion_one_ordered_rate": True, "outcomes_of_a_carried_order": list(OUTCOMES), "what_an_order_not_carried_is": list(NOT_CARRIED),
            "refusal_closes_the_infusion": True, "a_declared_order_never_becomes_a_carried_one": True,
            "an_order_that_names_no_drug": {"kind": ROLE_KIND, "closes_the_infusion_while_the_norepinephrine_runs": True, "why": GAP_ROLE_NAMED},
            "declared_gaps": {"another_operation": GAP_OPERATION, "another_action_type": GAP_TYPE, "no_units": GAP_NO_UNITS, "other_units": GAP_UNITS,
                              "no_rate": GAP_RATE, "two_rates": GAP_TWO_RATES, "a_receipt_that_disagrees": GAP_RECEIPT, "never_seen_to_start": GAP_NOT_STARTED,
                              "no_identity_no_whole_minute_or_against_the_clock": GAP_CHRONOLOGY, "an_order_that_names_no_drug": GAP_ROLE_NAMED,
                              "any_order_after_a_refused_one": GAP_AFTER_A_REFUSED_ORDER, "any_order_after_an_unmapped_first": GAP_NOT_MIRRORED,
                              "replaced_within_its_minute": GAP_REPLACED, "a_stop_of_nothing": GAP_NOTHING_TO_BUILD},
            "refused_on_an_amendment_2_witness": True,
            "profile_field": PROFILE_FIELD, "witnesses": list(_vs.WITNESS_NAMES), "chosen_witness": None,
            "registered_adapters_declaring_it": declaring, "not_granted": list(NOT_GRANTED)}
