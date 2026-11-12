"""P3-222: the ONE per-minute validation primitive of the Phase-3 authority layer.

A turn of the encounter can move the clock by many simulated minutes (an infusion, a wait, a long history). The experiment commits the engine's END state
once (``VALIDATED_ATOMIC_INTERVAL``, FD-AUTH-16), but only if EVERY minute of the interval passed the same validation, and the first minute that fails makes
every later minute of the interval ineligible: a clean final state can never override a failed intermediate one.

Before this module the pair evaluator validated every minute of an interval and the pressure-only site validated only the minute it committed: the review's finding R2.
Both now call the functions here for EVERY INTERMEDIATE minute, so there is exactly one place where an intermediate minute is judged, and the two modes differ in one
thing only: whether the consciousness half is judged. The END minute (the one a commit would write) keeps its own transaction inside each site -- the very same
``AuthorityTransaction.validate`` this module calls per minute -- plus the checks that only the end state has (the legacy comparison, the provenance).

* ``PRESSURE_ONLY``: the pressure transaction's own validation, for the pressure domain. It never reads a consciousness candidate; handing it one is an error,
  so the consciousness can never become authoritative through the pressure-only site.
* ``PAIR_PRESSURE_CONSCIOUSNESS``: the same pressure validation, plus the consciousness candidate (on the ladder, the core's own reading, pulse present) and the
  one-course check between the pressure run and the bound run.

This module computes no physiology, writes no state and commits nothing. It reads the shadow session and the bound runner's results and returns evidence.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from clinical_core import legacy_adapter

import runtime_authority as ra
import runtime_shadow_families as fam

MODULE_VERSION = "P3-222"

PRESSURE_ONLY = "PRESSURE_ONLY"
PAIR_PRESSURE_CONSCIOUSNESS = "PAIR_PRESSURE_CONSCIOUSNESS"
MODES = (PRESSURE_ONLY, PAIR_PRESSURE_CONSCIOUSNESS)

#: The names a failed minute carries. The pressure ones are IDENTICAL in both modes: that is what "the pair's pressure half is the pressure-only site's" means.
PRESSURE_CANDIDATE_PRESENT = "pressure_candidate_present"
CONSCIOUSNESS_CANDIDATE_PRESENT = "consciousness_candidate_present"
PULSE_PRESENT = "pulse_present"
PAIR_IS_ONE_COURSE = "pair_is_one_course"

#: The core's own consciousness ladder: the levels the legacy adapter maps its words from.
LADDER = frozenset(legacy_adapter.LEVEL_OF.values())
#: The readings of one common state that do NOT depend on the Amendment-2 magnitudes: equal in the pressure run and in the bound run, or the pair is not one course.
SHARED_READINGS = tuple(name for name in fam.TRACE_READINGS if name != "consciousness_level")


class ModeError(ValueError):
    """A caller asked a mode to do what it may not: a pressure-only validation was handed a consciousness candidate, or the mode is unknown."""


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def judges_consciousness(mode: str) -> bool:
    if mode not in MODES:
        raise ModeError(f"unknown validation mode {mode!r}")
    return mode == PAIR_PRESSURE_CONSCIOUSNESS


def replay_table(replay_input: Mapping | None) -> dict | None:
    """The pressures of EVERY minute of the artifact's replay, computed ONCE: ``{minute: pressure_point}``. ``None`` when there is no artifact to replay.

    The first result of a minute wins, which is what the site's single-minute replay has always returned."""
    if not replay_input:
        return None
    replayed = fam.replay_shadow_encounter(json.loads(ra.canonical(replay_input)))
    table: dict = {}
    for item in replayed["results"]:
        table.setdefault(_as_int(item["minute"]), ra.pressure_point(item["derived"]))
    return table


def pressure_failures(index: int, *, case_id: str, snapshot: Mapping | None, pressure: Mapping | None, replayed: Mapping | None,
                      failures_at: Sequence, unsupported: Sequence[str], legacy_arrest: bool) -> list:
    """The pressure half of ONE minute: the pressure transaction's own validation (candidate present and finite, reproducible from the immutable artifact,
    no failure recorded at THIS minute, a supported management, no legacy arrest, the approved snapshot). Returns the names that failed; empty = valid.

    The legacy comparison is a record, not a safety check, and an intermediate minute has none."""
    if pressure is None or any(value is None for value in pressure.values()):
        return [PRESSURE_CANDIDATE_PRESENT]
    step = ra.AuthorityTransaction(minute=index, case_id=case_id, snapshot=snapshot)
    step.capture({"sim_time": index}).compute(ra.shaped_like_legacy(pressure, {}), None)
    ok = step.validate(invariants_hold=not failures_at, replay_digest=ra.digest_of(replayed) if replayed is not None else "", expected_digest=ra.digest_of(pressure),
                       unsupported=tuple(unsupported), legacy_arrest=bool(legacy_arrest), failures=list(failures_at))
    return [] if ok else [f"pressure:{name}" for name in step.failures]


def consciousness_failures(index: int, *, channels: Mapping | None, bound_derived: Mapping | None, session_derived: Mapping | None) -> list:
    """The consciousness half of ONE minute (pair mode only): the candidate is on the ladder and is the core's own reading, the pulse is present, and the bound
    run and the pressure run are one course at the readings that do not depend on the Amendment-2 magnitudes."""
    failed = []
    if (channels is None or type(channels.get("category_index")) is not int or channels.get("category_index") not in LADDER
            or channels.get("consciousness_level") != channels.get("category_index")):          # an exact int: ``True`` and ``0.0`` hash like the rungs 1 and 0
        failed.append(CONSCIOUSNESS_CANDIDATE_PRESENT)
    elif channels.get("pulse_present") is not True:
        failed.append(PULSE_PRESENT)
    if bound_derived is None or session_derived is None or any(bound_derived.get(name) != session_derived.get(name) for name in SHARED_READINGS):
        failed.append(PAIR_IS_ONE_COURSE)
    return failed


def validate_interval(minutes: Sequence[int], *, mode: str, case_id: str, snapshot: Mapping | None, session: Any, unsupported: Sequence[str], legacy_arrest: bool,
                      table: Mapping | None, bound_results: Sequence | None = None, channel_rows: Mapping | None = None) -> dict:
    """EVERY minute of ``minutes``, with the same checks, and the interval's verdict.

    ``rows`` is ``[{minute, ok, failed}]`` in the order given. ``first_failed_minute`` is the first row that failed; every later minute is in
    ``ineligible_after``: it may not become authoritative whatever its own row says. ``ok`` is True only when every row is.
    ``bound_results`` and ``channel_rows`` belong to the pair mode; the pressure-only mode refuses them (FD-AUTH-16)."""
    with_consciousness = judges_consciousness(mode)
    if not with_consciousness and (bound_results is not None or channel_rows is not None):
        raise ModeError("the pressure-only validation reads no consciousness candidate: it was handed one")
    theirs = {_as_int(item.minute): item for item in list(getattr(session, "minutes", []) or [])}
    failures_all = list(getattr(session, "failures", []) or [])
    mine = {_as_int(item.minute): dict(item.derived) for item in (bound_results or ())}
    rows = []
    for index in minutes:
        entry = theirs.get(index)
        derived = None if entry is None else dict(entry.derived)
        pressure = None if derived is None else ra.pressure_point(derived)
        failed = pressure_failures(index, case_id=case_id, snapshot=snapshot, pressure=pressure, replayed=None if table is None else table.get(index),
                                   failures_at=[item for item in failures_all if _as_int(item.minute) == index], unsupported=unsupported,
                                   legacy_arrest=legacy_arrest)
        if with_consciousness:
            row = (channel_rows or {}).get(index)
            channels = None if row is None or "channels_unavailable" in row else row["channels"]
            failed.extend(consciousness_failures(index, channels=channels, bound_derived=mine.get(index), session_derived=derived))
        rows.append({"minute": index, "ok": not failed, "failed": failed})
    first = next((row for row in rows if not row["ok"]), None)
    return {"mode": mode, "rows": rows, "ok": first is None, "first_failed_minute": None if first is None else first["minute"],
            "failed": None if first is None else list(first["failed"]),
            "ineligible_after": [] if first is None else [row["minute"] for row in rows if row["minute"] > first["minute"]],
            "interval_minutes": [rows[0]["minute"], rows[-1]["minute"]] if rows else []}
