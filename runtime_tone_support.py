"""P3-396 / P3-397: the common vasoconstrictor support of PHASE2_AMENDMENT_3, mapped for a DEVELOPMENT shadow run.

What this is. The common core gained one general state, the vasoconstrictor support (``aux.vasoconstrictor_support``), read
by the tone target through one bounded factor that is UNSET by default (``clinical_core.vascular_support``). This module is
the Phase-3 side of it and nothing more: it makes a development COPY of a family's shadow adapter that

- declares the reader with ONE witness of the development behavioural region (``with_tone_support``), and
- maps ONE order -- a norepinephrine START at a fixed rate in mcg/min -- to the core's first writer of that state.

The mapping is the same for every family: it reads the order and the witness, never the case, the family or the patient's
state, and it builds no pressure. What the order does to the pressure is whatever the common core's tone, flow, preload and
pump make of it.

What it is not.

- Not registered. ``runtime_shadow_families.ADAPTERS`` is untouched: no registered adapter declares the reader, so no
  encounter's own shadow run, no ensemble and no certified record changes.
- Not authority. ``runtime_authority.SUPPORTED_ACTIONS`` is untouched and the live grant names norepinephrine among what it
  does NOT grant: the GI pressure development authority still stops on the order, exactly as FR-F was certified
  (``HALTED_BY_UNSUPPORTED_ACTION``).
- Not a titration engine. Only the encounter's FIRST order of the kind can be built, and only when it is a start at a fixed
  rate in mcg/min; an adjustment, a stop, a weight-based dose and any later start are DECLARED gaps: reported with their
  reason, never dropped and never approximated.
- Not combined with the Amendment-2 consciousness witnesses: that interaction has not been reviewed, and it is refused.
- Not a calibration. A witness is a probe of a region whose every magnitude has a confidence below 0.80; none is chosen.
- Not for residents. Nothing here is read by the page, the scoring or the first pilot.
"""
from __future__ import annotations

import copy
import dataclasses
import math
from typing import Any, Mapping, Sequence

import runtime_shadow as rs
import runtime_shadow_families as fam

MODULE_VERSION = "P3-396"
REVISION = "PHASE2_AMENDMENT_3"
STATUS = "DEVELOPMENT_SHADOW_ONLY"
#: The engine's own action type for the order (``family_parser``), and the one shape of it this mapping builds.
ORDER_KIND = "norepinephrine"
MAPPED_OPERATION = "start"
MAPPED_UNITS = "mcg/min"
#: The profile field the development copy declares; it exists only in PHASE2_AMENDMENT_3 and its registered successors.
PROFILE_FIELD = "vasoconstrictor_support_to_tone_gain"
NOT_GRANTED = ("runtime authority", "a registered adapter", "resident visibility", "scoring", "the first pilot",
               "a clinical dose-response", "an mmHg target", "titration", "a weight-based dose", "any other vasopressor",
               "clinical validation")

#: Why an order of the kind is not mapped. Each is a declared gap of the run.
GAP_OPERATION = "norepinephrine {operation} has no core mapping: only a start at a fixed rate is mapped (no titration and no stop)"
GAP_UNITS = ("norepinephrine in {units} is not mapped: only a fixed rate in mcg/min (a weight-based dose needs a weight this "
             "mapping does not read)")
GAP_RATE = "a norepinephrine start without a finite positive rate is not mapped"
#: Only the encounter's FIRST order of the kind can be built. Whatever follows it is a titration, a stop or a restart, and none of them is mapped.
GAP_AFTER_THE_INFUSION = ("norepinephrine {operation} after the run's infusion started is not mapped (no titration, no stop, no restart): the run "
                          "keeps the infusion it mapped and, from this order on, no longer mirrors the encounter's vasopressor")
GAP_NOT_MIRRORED = ("the encounter's first norepinephrine order was not mapped, so the run does not mirror its vasopressor and maps no later order "
                    "of the kind either")
NOT_MIRRORED = " The run does not mirror the encounter's vasopressor."


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
    from clinical_core import vascular_support as vs
    return vs.witness(name)


def order_disposition(action: Mapping | None) -> tuple:
    """(rate in mcg/min, None) when the order is the ONE shape this mapping builds -- a start at a finite positive rate in mcg/min; (None, why)
    otherwise. It judges the order alone: whether it is the encounter's first, and whether the core's writer represents the rate, are
    ``map_orders``'s."""
    action = dict(action or {})
    operation, units, rate = action.get("operation"), action.get("units"), action.get("rate")
    if operation != MAPPED_OPERATION:
        return None, GAP_OPERATION.format(operation=repr(operation))
    if units != MAPPED_UNITS:
        return None, GAP_UNITS.format(units=repr(units))
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate <= 0.0:
        return None, GAP_RATE
    return float(rate), None


def map_orders(mirrored: Sequence, built: Sequence, gaps: Sequence, witness: Mapping) -> tuple:
    """(contributors, gaps) with every norepinephrine order either BUILT once or DECLARED with its own reason.

    ``built`` and ``gaps`` are what the family's own mapping returned: it knows no vasopressor, so each order of the kind arrives as a gap.
    ONLY the encounter's first order of the kind can become the core's writer, and only when it is a mappable start: every later one is a
    titration, a stop or a restart, none of which is mapped, so it stays a gap that says the run no longer mirrors the vasopressor; and when
    the first order itself is not mappable, no later one is built in its place (the run would carry an infusion the encounter started at
    another time, at another dose). Orders are taken in the engine's own order (minute, then position in the mirror), an order id counts once,
    and nothing else in ``built`` or ``gaps`` is touched."""
    from clinical_core import vascular_support as vs
    ours, seen = [], set()
    for position, event in enumerate(mirrored):
        if event.kind == ORDER_KIND and event.order_id not in seen:
            seen.add(event.order_id)
            ours.append((event.minute, position, event))
    ours = [event for _minute, _position, event in sorted(ours, key=lambda item: item[:2])]
    made = list(built)
    kept = [dict(gap) for gap in gaps if not (gap.get("kind") == ORDER_KIND and gap.get("order_id") in seen)]
    first_was_built = None
    for event in ours:
        if first_was_built is None:
            rate, why = order_disposition(event.action)
            if why is None:
                try:
                    made.append(vs.Norepinephrine(event.order_id, int(event.minute), rate,
                                                  half_effect_rate_mcg_min=float(witness["half_effect_rate_mcg_min"]),
                                                  onset_tau_min=float(witness["onset_tau_min"]),
                                                  offset_tau_min=float(witness["offset_tau_min"])))
                except Exception as error:               # an order the core's writer refuses (a rate past what it represents) is a declared gap too
                    why = f"the core's writer refuses this order: {error}"
            first_was_built = why is None
            if why is not None:
                kept.append({"order_id": event.order_id, "kind": ORDER_KIND, "why": why + NOT_MIRRORED})
        elif first_was_built:
            kept.append({"order_id": event.order_id, "kind": ORDER_KIND,
                         "why": GAP_AFTER_THE_INFUSION.format(operation=repr(dict(event.action or {}).get("operation")))})
        else:
            kept.append({"order_id": event.order_id, "kind": ORDER_KIND, "why": GAP_NOT_MIRRORED})
    return tuple(made), kept


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
    vasoconstrictor reader with the named witness and maps a norepinephrine start. The adapter given is not modified, the
    copy is never registered, and it is refused for an adapter that already declares the reader."""
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
    """What this mapping is, as plain data for a record."""
    from clinical_core import vascular_support as vs
    return {"module_version": MODULE_VERSION, "revision": REVISION, "status": STATUS,
            "mapped": {"kind": ORDER_KIND, "operation": MAPPED_OPERATION, "units": MAPPED_UNITS,
                       "contributor": vs.Norepinephrine.type_name},
            "declared_gaps": {"another_operation": GAP_OPERATION, "other_units": GAP_UNITS, "no_rate": GAP_RATE,
                              "any_order_after_the_first": GAP_AFTER_THE_INFUSION, "any_order_after_an_unmapped_first": GAP_NOT_MIRRORED},
            "only_the_first_order_of_the_kind_can_be_built": True, "refused_on_an_amendment_2_witness": True,
            "profile_field": PROFILE_FIELD, "witnesses": list(vs.WITNESS_NAMES), "chosen_witness": None,
            "registered_adapters_declaring_it": [], "not_granted": list(NOT_GRANTED)}
