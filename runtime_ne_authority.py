"""P3-490 to P3-494: the LIVE manual NOREPINEPHRINE control under the development authority (FD-AUTHNE-01 to FD-AUTHNE-12).

Part of the Phase-3 layer (named in ``runtime_shadow.LAYER_SOURCES``). It adds NO physiology and edits NO source of ``clinical_core``: the path is the one the faculty ratified -- the order -> the encounter's ONE
rate history (``runtime_tone_support.NorepinephrineRateHistory``) -> the common vasoconstrictor support -> the common tone ``T`` -> the pressure -- and there is no direct drug -> mmHg path anywhere. What this
module adds is what makes it safe to run LIVE, under ``GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1`` (``runtime_ne_grant``):

* the AUTHORITY'S OWN contract of the order (``check``): read from the raw mirrored action, independently of the shadow mapping, and cross-checked against it. An explicit absolute rate in mcg/min, or a stop
  (which needs no rate), and nothing else: a rate without a unit, another unit, a weight-based dose, a rate on a stop, a bare continuation, an order that names no drug, an order the shadow could not carry, an
  order the two readings disagree about, or a chronology that cannot be established, is PERMANENT_FAIL_CLOSED (the session stops; there is no recovery of a malformed order and no fallback to the shadow, the
  earlier grant or a witness name);
* the tone binding (``runtime_tone_snapshot``) and the adapter that executes it (``bound_adapter``): the ratified values, read from the record, in the ONE profile field and in the writer the order builds;
* the consciousness overlay that carries the collapse boundary guard under the SAME hemodynamics as the pressure (``ToneConsciousnessOverlay``): the overlay is a comparison, it writes nothing and it is not
  visible to the resident; what it says of consciousness under tone is UNRESOLVED (``CONSCIOUSNESS_UNDER_TONE_UNRESOLVED``) and is used only as the guard it already is;
* what an artifact must carry to be replayed under this grant, and what makes it fail (``artifact_problems``, ``replay_overlay``).

Nothing here registers an approval, enables an authority or writes into an encounter: the site (``runtime_authority``) decides, and calls this module only when the NE grant travels with it.
"""
from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import runtime_authority_pair as pair
import runtime_ne_grant as grant_module
import runtime_pressure_snapshot as ps
import runtime_shadow_families as fam
import runtime_tone_snapshot as tn
import runtime_tone_support as ts

MODULE_VERSION = "P3-490/494"
ROOT = Path(__file__).resolve().parent
READER = "family_parser.py"

#: The class of action the NE grant carries, and the synthetic kind that names "an NE order the contract does not read" (never a class the engine produces: it exists only to be unsupported).
CARRIED_CLASSES = ("norepinephrine",)
NOT_CARRIED_KIND = "norepinephrine_order_not_carried"
ORDER_KIND, ROLE_KIND = ts.ORDER_KIND, ts.ROLE_KIND
STOP, START = "stop", "start"
#: What a benign declared gap of the shadow mapping is (the order is accounted for by a later order of its own minute, or it left nothing running): nothing else is accepted as a gap.
BENIGN_OUTCOMES = (ts.REPLACED, ts.NOTHING_TO_BUILD)
#: The label of what the consciousness overlay says under tone.
UNDER_TONE = "CONSCIOUSNESS_UNDER_TONE_UNRESOLVED"

# -- the problems (each has a name) ----------------------------------------------------------------------------------------------------------------------------------------------------------
NO_IDENTITY = "NE_ORDER_HAS_NO_IDENTITY_OR_NO_WHOLE_MINUTE"
CHRONOLOGY = "NE_ORDERS_ARRIVE_AGAINST_THE_CLOCK"
NOT_NE_TYPE = "NE_ORDER_OF_ANOTHER_ACTION_TYPE"
UNKNOWN_OPERATION = "NE_OPERATION_IS_NOT_START_ADJUST_CONTINUE_OR_STOP"
NO_UNITS = "NE_RATE_WITHOUT_UNITS"
WRONG_UNITS = "NE_RATE_IN_UNITS_OTHER_THAN_MCG_MIN"
BAD_RATE = "NE_RATE_IS_NOT_A_FINITE_POSITIVE_NUMBER"
TWO_RATES = "NE_ORDER_CARRIES_TWO_DIFFERENT_RATES"
STOP_WITH_RATE = "NE_STOP_CARRIES_A_RATE"
BARE_CONTINUATION = "NE_CONTINUATION_WITHOUT_AN_EXPLICIT_RATE"
RECEIPT_DISAGREES = "NE_RECEIPT_DISAGREES_WITH_THE_ORDER"
NOT_STARTED = "NE_ORDER_BEFORE_ANY_START"
ROLE_NAMED = "AN_ORDER_THAT_NAMES_NO_DRUG_WHILE_THE_INFUSION_IS_IN_PLAY"
RATE_BEYOND_THE_WRITER = "NE_RATE_BEYOND_WHAT_THE_COMMON_WRITER_REPRESENTS"
SHADOW_REFUSED = "THE_SHADOW_MAPPING_DID_NOT_CARRY_AN_ORDER_THE_CONTRACT_READS"
READINGS_DISAGREE = "THE_AUTHORITY_AND_THE_SHADOW_READ_THE_INFUSION_DIFFERENTLY"
UNEXPLAINED_GAP = "A_NE_GAP_THE_CONTRACT_DOES_NOT_ACCOUNT_FOR"
TOO_MANY_WRITERS = "THE_RUN_CARRIES_MORE_THAN_ONE_NE_WRITER"
NO_MIRROR = "THE_SESSION_HAS_NO_MIRROR_OF_THE_ORDERS_OR_NO_RECORD_OF_ITS_GAPS"
NOT_MIRRORED = "AN_EXECUTED_NE_ACTION_THE_AUTHORITY_CANNOT_FIND_IN_THE_MIRROR"
PROBLEMS = (NO_MIRROR, NOT_MIRRORED, RATE_BEYOND_THE_WRITER, NO_IDENTITY, CHRONOLOGY, NOT_NE_TYPE, UNKNOWN_OPERATION, NO_UNITS, WRONG_UNITS, BAD_RATE, TWO_RATES, STOP_WITH_RATE, BARE_CONTINUATION, RECEIPT_DISAGREES, NOT_STARTED, ROLE_NAMED,
            SHADOW_REFUSED, READINGS_DISAGREE, UNEXPLAINED_GAP, TOO_MANY_WRITERS)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=list)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except (OverflowError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _whole(minute: Any) -> bool:
    return not isinstance(minute, bool) and isinstance(minute, int) and minute >= 0


# ============================================================================================================================================
# the authority's own reading of the orders
# ============================================================================================================================================

def read_order(action: Mapping | None, receipt: Mapping | None = None) -> tuple:
    """``(semantic, rate, problem)`` for ONE raw norepinephrine action, read as written. ``semantic`` is "start", "adjust", "continue" or "stop"; ``rate`` is the explicit absolute rate in mcg/min (0.0 for a stop);
    ``problem`` is None when the order is one the contract reads. Independent of ``runtime_tone_support.order_disposition`` on purpose: the two readings are compared."""
    action = dict(action) if isinstance(action, Mapping) else {}
    receipt = dict(receipt) if isinstance(receipt, Mapping) else {}
    if action.get("type") != ORDER_KIND:
        return None, None, NOT_NE_TYPE
    operation = action.get("operation")
    if not isinstance(operation, str) or operation not in grant_module.ENGINE_OPERATIONS:
        return None, None, UNKNOWN_OPERATION
    if receipt.get("operation") not in (None, operation):
        return operation, None, RECEIPT_DISAGREES
    rate, units, said = _number(action.get("rate")), action.get("units"), action.get("rate_mcg_min")
    if operation == STOP:
        if action.get("rate") is not None or said is not None:
            return operation, None, STOP_WITH_RATE
        return operation, 0.0, None
    if units is None and action.get("rate") is None and said is None:
        return operation, None, BARE_CONTINUATION if operation == "continue" else NO_UNITS
    if units is None:
        return operation, None, NO_UNITS
    if units != grant_module.UNITS:
        return operation, None, WRONG_UNITS
    if rate is None or rate <= 0.0:
        return operation, None, BAD_RATE
    if said is not None and _number(said) != rate:
        return operation, None, TWO_RATES
    if receipt.get("units") not in (None, grant_module.UNITS) or (receipt.get("rate") is not None and _number(receipt.get("rate")) != rate):
        return operation, None, RECEIPT_DISAGREES
    return operation, rate, None


def _support_limit() -> float:
    """The core's own bound on the support a rate may ask for (a rate of this many times its half-effect rate or more is not an order the writer represents)."""
    from clinical_core import vascular_support as vs
    return float(vs.SUPPORT_LIMIT)


def label_of(before: float, rate: float, opened: bool) -> str:
    """The faculty's name for what an order did to the rate that ran before it."""
    if not opened:
        return "START"
    if rate == before:
        return "UNCHANGED"
    if rate == 0.0:
        return "STOP"
    if before == 0.0:
        return "RESTART"
    return "INCREASE" if rate > before else "DECREASE"


@dataclasses.dataclass(frozen=True)
class NeCheck:
    """What the authority concluded about the encounter's norepinephrine orders at one turn: the verdict, every problem by name, the orders as the authority read them and the rate history they make."""

    ok: bool
    problems: tuple
    orders: tuple
    history: tuple
    benign: tuple
    digest: str

    def summary(self) -> dict:
        return {"ok": self.ok, "problems": [dict(item) for item in self.problems], "orders": [dict(item) for item in self.orders], "rate_history": [list(item) for item in self.history],
                "benign_gaps": list(self.benign), "digest": self.digest}


def _kind_of(event: Any) -> str:
    """The class of a mirrored event, normalised the way the site normalises the classes of the turn (review A4): a kind spelt differently is still the class."""
    return str(getattr(event, "kind", "") or "").strip().lower()


def _ran_signature(action: Any) -> tuple | None:
    """``(operation, rate, units)`` of an executed norepinephrine action, or None when the action is not one (by its normalised type)."""
    if not isinstance(action, Mapping) or str(action.get("type") or "").strip().lower() != ORDER_KIND:
        return None
    return (action.get("operation"), action.get("rate"), action.get("units"))


def _events(mirrored: Sequence) -> list:
    seen, out = set(), []
    for event in list(mirrored or []):
        if _kind_of(event) not in (ORDER_KIND, ROLE_KIND):
            continue
        identity = getattr(event, "order_id", None)
        if isinstance(identity, str) and identity in seen:
            continue
        if isinstance(identity, str):
            seen.add(identity)
        out.append(event)
    return out


def check(mirrored: Sequence | None, tone_configuration: Any, gaps: Sequence | None = (), *, ran: Sequence | None = None) -> NeCheck:
    """The authority's verdict on the encounter's norepinephrine orders, from the mirrored actions alone (never raises: a failure to read is itself a problem).

    The orders are read in the mirror's order, once each. ``problems`` is empty only if EVERY order is one the contract reads, the first is a start, the chronology is whole, the shadow mapping carried exactly
    the infusion the authority read (the same rate history) and every gap the shadow declared for the kind is a benign one the authority accounts for."""
    problems: list = []
    rows: list = []
    history: list = []
    benign: list = []
    try:
        cfg = tn.checked(tone_configuration)
        if mirrored is None or gaps is None:
            problems.append({"order_id": None, "problem": NO_MIRROR})      # a session that does not say what it mirrored is not a clean contract
            mirrored, gaps = (), ()
        events = _events(mirrored)
        # what the engine EXECUTED this turn must be in the mirror: an executed norepinephrine action the authority cannot find is an infusion the run does not see
        wanted: dict = {}
        for action in list(ran or []):
            signature = _ran_signature(action)
            if signature is not None:
                wanted[signature] = wanted.get(signature, 0) + 1
        for signature, count in wanted.items():
            have = sum(1 for event in events if _kind_of(event) == ORDER_KIND and _ran_signature(getattr(event, "action", None)) == signature)
            if have < count:
                problems.append({"order_id": None, "problem": NOT_MIRRORED, "executed": list(signature)})
        ordered, opened, last_minute = 0.0, False, 0
        finals: dict = {}
        for event in events:
            identity, minute = getattr(event, "order_id", None), getattr(event, "minute", None)
            if _kind_of(event) == ROLE_KIND:
                problems.append({"order_id": identity, "problem": ROLE_NAMED})
                continue
            if not isinstance(identity, str) or not identity or not _whole(minute):
                problems.append({"order_id": identity, "problem": NO_IDENTITY})
                continue
            if minute < last_minute:
                problems.append({"order_id": identity, "problem": CHRONOLOGY})
                continue
            last_minute = minute
            operation, rate, problem = read_order(getattr(event, "action", None), getattr(event, "receipt", None))
            if problem is None and not opened and operation != START:
                problem = NOT_STARTED
            if problem is None and rate and rate / cfg.half_effect_rate_mcg_min >= _support_limit():
                problem = RATE_BEYOND_THE_WRITER
            if problem is not None:
                problems.append({"order_id": identity, "problem": problem, "operation": operation})
                continue
            if operation == "continue" and rate is None:
                problems.append({"order_id": identity, "problem": BARE_CONTINUATION})
                continue
            name = label_of(ordered, rate, opened)
            rows.append({"order_id": identity, "minute": minute, "operation": operation, "rate_mcg_min": rate, "semantic": name})
            finals[minute] = (identity, rate)
            ordered, opened = rate, True
        # the rate history the authority read: the last order of each minute, a rate equal to the one running changes nothing
        running = None
        for minute in sorted(finals):
            rate = finals[minute][1]
            if running is None and rate == 0.0:
                continue
            if rate != (0.0 if running is None else running):
                history.append((minute, rate))
            running = rate
        if not problems:
            shadow_events, unplaced = ts._ours(mirrored)
            if shadow_events is None:
                problems.append({"order_id": None, "problem": CHRONOLOGY})
            else:
                physical, carried, declared = ts.infusion_history(shadow_events, cfg.values())
                refused = [(order, what) for order, _kind, what, _why in declared if what not in BENIGN_OUTCOMES]
                if refused:
                    problems += [{"order_id": order, "problem": SHADOW_REFUSED, "shadow": what} for order, what in refused]
                elif tuple(physical) != tuple(history):
                    problems.append({"order_id": None, "problem": READINGS_DISAGREE, "authority": [list(item) for item in history], "shadow": [list(item) for item in physical]})
                benign = [order for order, _kind, what, _why in declared if what in BENIGN_OUTCOMES]
        problems += gap_problems(gaps, tuple(sorted(benign)))
    except Exception as error:                                   # a check that cannot be made is a failure of the contract, never a pass
        problems.append({"order_id": None, "problem": f"THE_CONTRACT_COULD_NOT_BE_CHECKED: {type(error).__name__}"})
    body = {"orders": rows, "history": [list(item) for item in history], "problems": problems, "benign": sorted(benign)}
    return NeCheck(not problems, tuple(problems), tuple(rows), tuple((minute, rate) for minute, rate in history), tuple(sorted(benign)), digest(body))


def gap_problems(gaps: Sequence, benign: Sequence) -> list:
    """Every norepinephrine-kind gap of the shadow session that the contract does NOT account for. A gap is accounted for only if it names an order the contract classified as benign (replaced within its minute, or
    a stop of nothing) and its reason is that benign reason; the cumulative list of the session is read every turn, so an unaccounted gap stays a problem for good."""
    found = []
    for gap in list(gaps or []):
        kind = dict(gap).get("kind")
        if kind != ORDER_KIND:
            continue
        why = str(dict(gap).get("why") or "")
        benign_why = ("norepinephrine" in why and ("was replaced within its own minute by a later order" in why or "leaves nothing running before any modelled interval" in why)
                      and "could not map" not in why and "not mapped" not in why)
        if str(dict(gap).get("order_id")) not in set(benign) or not benign_why:
            found.append({"order_id": dict(gap).get("order_id"), "problem": UNEXPLAINED_GAP, "why": why[:160]})
    return found


def carried_for(site_has_the_grant: bool) -> tuple:
    return CARRIED_CLASSES if site_has_the_grant else ()


# ============================================================================================================================================
# the adapter that executes the tone binding
# ============================================================================================================================================

class BoundToneSupport:
    """What a development adapter gains when it executes the RATIFIED tone configuration. Mixed in BEFORE the family's own adapter class: the family's mapping runs first and unchanged, and this adds the ONE profile
    field with the snapshot's gain and the order mapping with the snapshot's writer constants. The values are read from the verified configuration, never from a witness name."""

    tone_configuration: Any = None

    def region_witnesses(self) -> dict:
        return {}

    def profile(self, point: str):
        why = ts.availability()
        if why is not None:
            raise ts.ToneSupportUnavailable(why)
        return tn.apply_profile(super().profile(point), self.tone_configuration)

    def snapshot(self, point: str = fam.COMMITTED):
        cfg = tn.checked(self.tone_configuration)
        base = super().snapshot(point)
        said = ", ".join(f"{key} = {value}" for key, value in sorted(cfg.values().items()))
        return fam.ShadowParameterSnapshot(
            f"{base.id}+{cfg.runtime_snapshot_id}", base.family, base.point,
            tuple(base.provenance) + (
                f"runtime_tone_snapshot: {cfg.snapshot_id} (record {cfg.record_digest}, configuration {cfg.configuration_digest}) ({said}): the four values of the ratified development snapshot, read from the record",
                "a development configuration: not a clinical calibration, not a dose-response, not production, not resident-approved"))

    def interventions(self, mirrored: Sequence, state: Mapping | None = None) -> tuple:
        built, gaps = super().interventions(mirrored, state)
        return ts.map_orders(mirrored, built, gaps, tn.checked(self.tone_configuration).values())


def _with_bound_tone(adapter: Any, tone_configuration: Any) -> Any:
    """A COPY of ``adapter`` (same family, same cases, same mapping) that executes the verified tone configuration. The adapter given is not modified, and a copy is never registered."""
    cfg = tn.checked(tone_configuration)
    if not isinstance(adapter, fam.RuntimeFamilyAdapter) or adapter.tone_support_witness is not None:
        raise ValueError("the bound tone is declared once, on an adapter that does not already declare the reader")
    cls = type(f"{type(adapter).__name__}WithBoundTone", (BoundToneSupport, type(adapter)), {"__doc__": f"{type(adapter).__name__} executing {cfg.snapshot_id}."})
    made = copy.copy(adapter)
    made.__class__ = cls
    made.tone_configuration = cfg
    made.tone_support_witness = tn.WITNESS
    made.version = f"{adapter.version}+tone/{cfg.snapshot_id}"
    made.maps = tuple(adapter.maps) + (ORDER_KIND,)
    return made


def bound_adapter(pressure_configuration: Any, tone_configuration: Any) -> Any:
    """The GI adapter of the session: the ratified pressure configuration AND the ratified tone configuration, both re-checked."""
    return _with_bound_tone(fam.GiHaemorrhageAdapter.configured(pressure_configuration), tone_configuration)


def adapter_is_bound(adapter: Any, pressure_configuration: Any, tone_configuration: Any) -> bool:
    """This adapter executes exactly the two pinned configurations (every consumer re-derives it; nothing trusts the object)."""
    try:
        return (ps.configuration_is_pinned(pressure_configuration) and tn.configuration_is_pinned(tone_configuration) and isinstance(adapter, BoundToneSupport)
                and adapter.pressure_configuration == pressure_configuration and adapter.tone_configuration == tone_configuration and adapter.tone_support_witness == tn.WITNESS)
    except Exception:
        return False


# ============================================================================================================================================
# the consciousness overlay under the SAME hemodynamics (a comparison and a guard; never an authority)
# ============================================================================================================================================

class ToneConsciousnessOverlay(pair.ConsciousnessOverlay):
    """The V1-bound consciousness overlay, run on the SAME hemodynamics as the pressure the site commits -- which, under this grant, include the norepinephrine contributor. Without the contributor the overlay's
    pressure would differ from the session's and every minute would fail ``one_course``. What it says about consciousness under tone is UNRESOLVED (the faculty's open limitation); it is used only as the collapse
    boundary guard it already is, writes nothing, and is not visible to the resident."""

    def __init__(self, bound: Any, case_id: str, arrival_state: Mapping, tone_configuration: Any, *, time_limit: int = pair.TIME_LIMIT_MIN):
        super().__init__(bound, case_id, arrival_state, time_limit=time_limit)
        self.tone_configuration = tn.checked(tone_configuration)
        adapter = _with_bound_tone(pair.BoundSnapshotAdapter(bound), self.tone_configuration)
        self.runner = fam.ShadowPhysiologyRunner.open("gi_bleed", case_id, state=copy.deepcopy(dict(arrival_state)), adapter=adapter,
                                                      scenario_id=f"bound::{bound.snapshot_id}+{self.tone_configuration.runtime_snapshot_id}")
        self._anchors = pair._anchors_digest(self.runner)

    def overlay_summary(self) -> dict:
        out = super().overlay_summary()
        out["snapshot"] = {**dict(out.get("snapshot") or {}), "profile_digest": TONE_OVERLAY_PROFILE_DIGEST}
        out["tone_configuration"] = self.tone_configuration.summary()
        out["under_tone"] = UNDER_TONE
        out["boundary_is_a_guard_only_under_tone"] = True
        return out


def overlay_for(pressure_configuration: Any, tone_configuration: Any, case_id: str, arrival_state: Mapping) -> ToneConsciousnessOverlay:
    return ToneConsciousnessOverlay(pair.bind(pressure=pressure_configuration), case_id, arrival_state, tone_configuration)


def _tone_overlay_profile_digest() -> str:
    """The digest of the overlay's profile under the NE grant: version 2's pinned profile (the pair on the ratified pressure point) plus the ONE tone field. Derived here only to be compared with the literal below."""
    bound = pair.bind(pressure=ps.bind())
    return pair.profile_digest(tn.apply_profile(bound.profile, tn.bind()))


#: Written as a literal ON PURPOSE (a value read from the code that produces it would be a comparison of a thing with itself); the test re-derives it from the records.
TONE_OVERLAY_PROFILE_DIGEST = "ca3878729d07815fe6aa8071257b4d80a202b9d3281dd75f24ba8ab216a7df6e"


# ============================================================================================================================================
# what an artifact must carry, and how it is held to the records
# ============================================================================================================================================

def scenario_tone_problems(scenario: Any, cfg: Any, history: Sequence | None = None) -> list:
    """What the captured scenario says about the tone, held to the ratified configuration: the ONE profile field carries the snapshot's gain, the run has at most ONE norepinephrine writer, every norepinephrine
    contributor carries the snapshot's constants and the pinned writer version, and -- when the authority's own rate history is given -- the writer's history is exactly that history."""
    found: list = []
    try:
        from clinical_core import integration
        from clinical_core import vascular_support as vs
        cfg = tn.checked(cfg)
        _anchors, contributors, _minutes, profile = integration.scenario_from_dict(scenario)
        if getattr(profile, tn.PROFILE_FIELD, None) != cfg.tone_gain:
            found.append("the captured profile does not carry the ratified tone gain in the one field the support reads")
        writers = [item for item in contributors if isinstance(item, vs.Norepinephrine)]
        if len(writers) > 1:
            found.append(TOO_MANY_WRITERS)
        for writer in writers:
            if (writer.half_effect_rate_mcg_min, writer.onset_tau_min, writer.offset_tau_min) != (cfg.half_effect_rate_mcg_min, cfg.onset_tau_min, cfg.offset_tau_min):
                found.append("a norepinephrine writer of the captured scenario carries constants other than the ratified ones")
            if isinstance(writer, ts.NorepinephrineRateHistory) and writer.writer_version != grant_module.WRITER_VERSION:
                found.append("the rate history of the captured scenario was written by another writer version")
        if history is not None:
            if writers:
                writer = writers[0]
                made = ((int(writer.start_minute), float(writer.rate_mcg_min)),) + tuple((int(minute), float(rate)) for minute, rate in getattr(writer, "changes", ()))
                if made != tuple((int(minute), float(rate)) for minute, rate in history):
                    found.append("the writer's rate history is not the one the authority read from the orders")
            elif tuple(history):
                found.append("the authority read an infusion that the captured scenario does not carry")
    except Exception as error:
        found.append(f"the captured scenario cannot be held to the tone snapshot: {type(error).__name__}")
    return found


def contract_writer_problems(contract: Mapping, scenario: Any) -> list:
    """P3-494 (review A2): the orders the contract records are the orders the captured writer carries, and each recorded semantic is what its rate did to the rate before it (recomputed here, never read)."""
    found: list = []
    try:
        from clinical_core import integration
        from clinical_core import vascular_support as vs
        rows = [dict(row) for row in (contract.get("orders") or [])]
        before, opened = 0.0, False
        for row in rows:
            rate = _number(row.get("rate_mcg_min"))
            if rate is None or rate < 0.0:
                found.append(f"order {row.get('order_id')}: a recorded rate that is not a finite number at or above 0")
                break
            if row.get("semantic") != label_of(before, rate, opened):
                found.append(f"order {row.get('order_id')}: its recorded semantic is not what its rate did to the rate before it")
            before, opened = rate, True
        benign = set(contract.get("benign_gaps") or [])
        carried = [(row.get("order_id"), row.get("minute"), _number(row.get("rate_mcg_min"))) for row in rows if row.get("order_id") not in benign]
        _anchors, contributors, _minutes, _profile = integration.scenario_from_dict(scenario)
        writers = [item for item in contributors if isinstance(item, vs.Norepinephrine)]
        if writers:
            writer = writers[0]
            made = ([(order, minute, _number(rate)) for order, minute, rate, _outcome in writer.orders] if getattr(writer, "orders", None) else [(writer.id, writer.start_minute, _number(writer.rate_mcg_min))])
        else:
            made = []
        if carried != made:
            found.append("the orders the contract records are not the orders the captured writer carries")
    except Exception as error:
        found.append(f"the contract cannot be held to the captured writer: {type(error).__name__}")
    return found


def artifact_problems(body: Mapping) -> list:
    """What an artifact under the NE grant says that its own records contradict (re-derivable from the artifact alone). Called by ``runtime_authority.real_artifact_problems`` when the artifact names this grant;
    an artifact under any other grant that carries the NE block (or the tone), and one under this grant that does not, are problems too (the label of the grant decides, and the content must agree)."""
    problems: list = []
    body = dict(body or {})
    named = dict(body.get("grant") or {})
    is_ne = named.get("grant_id") == grant_module.GRANT_ID
    block = dict(body.get("norepinephrine_authority") or {})
    if (not is_ne) and block:
        return ["the artifact carries a norepinephrine authority block and does not name the norepinephrine grant"]
    if not is_ne:
        return []
    try:
        cfg = tn.bind()
    except tn.ToneBindingError as error:
        return [f"the tone snapshot cannot be established: {list(error.reasons)}"]
    if body.get("authority_label") != grant_module.ARTIFACT_LABEL:
        problems.append("the artifact does not carry the label the grant names")
    registered = grant_module.registered_grant(named.get("grant_id"), named.get("fingerprint"))
    if registered is None or canonical(named) != canonical(grant_module.summary(registered)):
        problems.append("the grant the artifact names is not the registered norepinephrine grant's summary")
    if not block or dict(block.get("tone_configuration") or {}) != cfg.summary():
        problems.append("the artifact does not carry the tone configuration of the ratified snapshot")
    if block.get("consciousness_under_tone") != UNDER_TONE or block.get("pump_dependence") != "COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED":
        problems.append("the artifact does not declare its open limitations")
    if block.get("resident_visible") is not False or block.get("scoring") is not False or block.get("authority_scope") != list(grant_module.DOMAIN):
        problems.append("the artifact claims a scope beyond the pressure domain, or resident visibility, or scoring")
    if dict(block.get("reader") or {}).get("git_blob") != grant_module.READER_GIT_BLOB:
        problems.append("the artifact does not name the order-safety successor of the reader")
    minutes = [dict(item) for item in (body.get("minutes") or [])]
    for record in minutes:
        contract = dict(record.get("norepinephrine_contract") or {})
        at = record.get("minute")
        if record.get("committed") and (not contract or contract.get("ok") is not True or contract.get("problems")):
            problems.append(f"minute {at} was committed without a clean norepinephrine contract")
        if contract and contract.get("digest") is not None:
            expected = digest({"orders": [dict(item) for item in contract.get("orders") or []], "history": [list(item) for item in contract.get("rate_history") or []],
                               "problems": [dict(item) for item in contract.get("problems") or []], "benign": sorted(contract.get("benign_gaps") or [])})
            if contract.get("digest") != expected:
                problems.append(f"minute {at}: the norepinephrine contract's digest does not recompute")
        scenario = dict(record.get("replay_input") or {}).get("scenario")
        if scenario and record.get("committed"):
            for item in scenario_tone_problems(scenario, cfg, [tuple(entry) for entry in contract.get("rate_history") or []] if contract else None):
                problems.append(f"minute {at}: {item}")
            if contract:
                problems.extend(f"minute {at}: {item}" for item in contract_writer_problems(contract, scenario))
    scenario = dict(body.get("replay_input") or {}).get("scenario")
    if scenario:
        for item in scenario_tone_problems(scenario, cfg):
            problems.append(f"the artifact's captured scenario: {item}")
    return problems


def reader_problems() -> list:
    """Why the LIVE reader is not the order-safety successor the grant pins (empty: it is). Read from the file, hashed here: a reader that changed again is a new succession and a new decision."""
    try:
        data = (ROOT / READER).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
        if blob != grant_module.READER_GIT_BLOB or hashlib.sha256(data).hexdigest() != grant_module.READER_SHA256:
            return ["the live reader is not the order-safety successor the grant pins"]
        return []
    except Exception as error:
        return [f"the live reader could not be read: {type(error).__name__}"]


def replay_overlay(artifact: Mapping) -> dict:
    """The overlay of an NE artifact, rebuilt FROM THE ARTIFACT ALONE: the generic replay with the profile digest of the tone-carrying overlay, plus the tone configuration and the scenario's tone values held to
    the ratified snapshot. Never raises."""
    out = pair.replay_overlay_artifact(artifact, ps.SNAPSHOT_ID, expected_profile_digest=TONE_OVERLAY_PROFILE_DIGEST)
    try:
        overlay = dict((artifact or {}).get("consciousness_overlay") or {})
        cfg = tn.bind()
        extra = []
        if dict(overlay.get("tone_configuration") or {}) != cfg.summary():
            extra.append("the overlay does not name the tone configuration of the ratified snapshot")
        scenario = dict(overlay.get("replay_input") or {}).get("scenario")
        extra += [f"the overlay's captured scenario: {item}" for item in scenario_tone_problems(scenario, cfg)] if scenario else ["the overlay carries no captured scenario"]
        if overlay.get("under_tone") != UNDER_TONE:
            extra.append("the overlay does not declare what it says of consciousness under tone")
        if extra:
            out = {**out, "reproduces": False, "mismatches": list(out.get("mismatches") or []) + extra}
    except Exception as error:
        out = {**out, "reproduces": False, "mismatches": list(out.get("mismatches") or []) + [f"{type(error).__name__}: {error}"]}
    return out


def summary_of(verdict: NeCheck | None, tone_configuration: Any, grant: Mapping) -> dict:
    """What the artifact says about the norepinephrine authority of the run (the block ``norepinephrine_authority``)."""
    return {"grant_id": dict(grant).get("grant_id"), "tone_configuration": tn.checked(tone_configuration).summary(), "writer_version": grant_module.WRITER_VERSION,
            "authority_scope": list(grant_module.DOMAIN), "resident_visible": False, "scoring": False, "consciousness_under_tone": UNDER_TONE,
            "pump_dependence": "COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED", "reader": {"git_blob": grant_module.READER_GIT_BLOB, "sha256": grant_module.READER_SHA256},
            "path": "order -> rate history -> vasoconstrictor support -> common T -> pressure", "no_drug_to_mmhg_equation": True,
            "last_contract": None if verdict is None else verdict.summary()}
