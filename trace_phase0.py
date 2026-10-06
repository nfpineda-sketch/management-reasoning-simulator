"""The Phase 0 fields of a Management Trace turn: observation, limitations, versions (0H).

Pre-pilot measurement safety, 2026-10-06. Each executed turn of the family engine already
records its submission, every order with its fate (``orders``), the time words applied
(``time_semantics``), every event of the course with its provenance (``events``) and the
event that stopped a wait (``interrupted``). These three complete the minimum the analysis
needs so that it never reads an engine limitation as the resident's omission:

* ``observation_snapshot`` -- what the resident could see at the end of the turn, whether the
  patient was in arrest, and which of the results reported this turn are the case's authored,
  static values rather than the engine's;
* ``limitations`` -- each place where the simulator, not the resident, decided what happened:
  ``unrecognized_order``, ``recorded_not_modelled``, ``unsupported_future_execution``,
  ``observable_static``, ``scripted_event``, ``resuscitation_not_modelled``,
  ``engine_inconsistency`` (and ``pilot_time_step_limit`` for a wait longer than one step);
* ``versions`` -- the code, the schemas and the case the turn ran on.

The v1 fields are unchanged; these are added beside them (``trace_extensions``).
"""
from __future__ import annotations

from copy import deepcopy

LIMITATION_KINDS = ("unrecognized_order", "recorded_not_modelled", "unsupported_future_execution",
                    "observable_static", "scripted_event", "resuscitation_not_modelled", "engine_inconsistency",
                    "pilot_time_step_limit")
SCHEMA = "phase0_trace_v1"

_VISIBLE = ("sbp", "dbp", "map", "hr", "spo2", "respiratory_rate", "rhythm", "pulse_present", "mental_status",
            "work_of_breathing", "crt", "temperature_c", "glucose_mg_dl", "respiratory_support")


def observation_snapshot(state, result=None):
    import observation_consistency
    o = (state or {}).get("observable") or {}
    minute = observation_consistency.arrest_minute(state)
    reported = [s.get("diagnostic_type") for s in (result or {}).get("action_summaries") or []
                if isinstance(s, dict) and s.get("diagnostic_type")]
    static = observation_consistency.declaration(state)["studies"]["static"]
    return {
        "minute": int((state or {}).get("sim_time", 0) or 0),
        "visible": {key: deepcopy(o.get(key)) for key in _VISIBLE if key in o},
        "arrest": {"minute": minute} if minute is not None else None,
        "static_results_reported": [study for study in reported if study in static],
        "inconsistencies": observation_consistency.check(state),
    }


def limitations(*, orders, events, observation, terminal_locked=False):
    """Where the simulator, not the resident, decided what happened in this turn."""
    found = []
    for order in orders or []:
        fate = order.get("fate")
        base = {"order_id": order.get("order_id"), "span": order.get("span") or order.get("canonical")}
        if order.get("limitation") == "unsupported_future_execution":
            found.append({"kind": "unsupported_future_execution", **base})
        elif order.get("limitation") == "pilot_time_step_limit":
            found.append({"kind": "pilot_time_step_limit", **base})
        elif fate == "UNRECOGNIZED":
            found.append({"kind": "unrecognized_order", **base})
        elif fate == "RECORDED_NOT_MODELLED":
            found.append({"kind": "recorded_not_modelled", **base})
    for event in events or []:
        if event.get("cause_class") == "SCRIPTED_NATURAL_HISTORY":
            found.append({"kind": "scripted_event", "event": event.get("kind"), "minute": event.get("minute"),
                          "preventability": event.get("preventability")})
        if event.get("terminal"):
            found.append({"kind": "resuscitation_not_modelled", "event": event.get("kind"),
                          "minute": event.get("minute")})
    arrest = (observation or {}).get("arrest")
    if terminal_locked and arrest and not any(item["kind"] == "resuscitation_not_modelled" for item in found):
        found.append({"kind": "resuscitation_not_modelled", "event": "cardiac_arrest", "minute": arrest["minute"]})
    for study in (observation or {}).get("static_results_reported") or []:
        found.append({"kind": "observable_static", "study": study})
    for broken in (observation or {}).get("inconsistencies") or []:
        found.append({"kind": "engine_inconsistency", "detail": broken})
    return found


def versions(state):
    import event_provenance
    import order_ledger
    from curriculum_runtime import code_version
    try:
        from clinical_cases import CASE_BANK_VERSION
    except Exception:  # pragma: no cover - an installation without the bank
        CASE_BANK_VERSION = None
    return {
        "code_version": code_version(),
        "trace_schema": "management_trace_v1",
        "phase0_schema": SCHEMA,
        "ledger_schema": order_ledger.LEDGER_SCHEMA,
        "event_provenance_schema": event_provenance.SCHEMA,
        "engine_family": (state or {}).get("engine_family"),
        "case_id": (state or {}).get("case_id"),
        "variant_id": ((state or {}).get("encounter_spec") or {}).get("variant_id") or (state or {}).get("variant_id"),
        "case_bank_version": CASE_BANK_VERSION,
    }
