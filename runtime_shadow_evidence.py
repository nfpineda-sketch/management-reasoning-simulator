"""P3-11: the GI acceptance battery as live-shadow evidence, read off the real battery.

Read-only with respect to the encounter, as P3-1 and P3-4 are: the legacy engine stays the only runtime
authority (``runtime_shadow.COMMON_CORE_RUNTIME_AUTHORITY`` is False) and nothing here writes a patient
state, a ledger, a score or a trace. What it adds is evidence instead of a promise:

- it plays the repository's own acceptance battery (``pilot_acceptance.battery``), once with the shadow off
  and once in ``shadow_compare``, and compares the authoritative record of each scenario byte for byte. No
  scenario is invented here: the battery's categories and scripts are the ones Phase 0 froze;
- per scenario it reads the live minute digests, replays the scenario's own serialized artifact through
  ``runtime_shadow_families.replay_shadow_encounter`` -- the same primitive the live path uses -- and reports
  whether the two agree digest by digest, not observable by observable;
- it classifies every GI action class the battery exercises as FULLY_MIRRORED, STRUCTURAL_ONLY or
  UNSUPPORTED, so a treatment the core cannot represent is named instead of showing up later as physiology;
- it reports comparability by domain, and every divergence by its declared class. No numeric tolerance is
  defined here, and none is needed: the baseline is the committed golden.

Nothing in this module selects or approves a clinical magnitude: the snapshot is whatever the adapter's own
policy gives (for GI, the committed default profile, which reads no band).
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from functools import lru_cache
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Mapping, Sequence

import runtime_shadow as rs
import runtime_shadow_families as fam

MODULE_VERSION = "P3-11"

#: How a GI action class is represented in the shadow.
FULLY_MIRRORED = "FULLY_MIRRORED"
#: The engine ran it, the core has no physiology for it and Phase 2 declares it non-physiological.
STRUCTURAL_ONLY = "STRUCTURAL_ONLY"
#: The engine ran it, it changes management, and the common mapping has no writer for it.
UNSUPPORTED = "UNSUPPORTED"

#: Comparability of a domain in one minute (P3-11-6).
COMPARABLE = "COMPARABLE"
PARTIALLY_COMPARABLE = "PARTIALLY_COMPARABLE"
NOT_COMPARABLE = "NOT_COMPARABLE"

#: The safety-critical conditions of P3-11-8. A scenario fails if any of them is true.
SAFETY_CONDITIONS = ("authoritative_record_differs", "order_fates_differ", "persistence_differs",
                     "minute_alignment_differs", "action_duplicated", "replay_differs_from_live",
                     "shadow_failure_reached_the_encounter", "phase2_digest_changed")


def gi_variants() -> tuple:
    """The GI cases of the acceptance battery, as the repository lists them."""
    import pilot_acceptance as acceptance
    return tuple(name for name in acceptance.variants() if acceptance.family_of(name) == "gi_bleed")


@contextmanager
def shadow(mode: str | None):
    """Run the block with the shadow flag set to ``mode``, or absent when it is None."""
    names = (rs.FLAG, rs.FAMILIES_FLAG)
    kept = {name: os.environ.get(name) for name in names}
    try:
        for name in names:
            os.environ.pop(name, None)
        if mode is not None:
            os.environ[rs.FLAG] = mode
        yield
    finally:
        for name, value in kept.items():
            os.environ.pop(name, None)
            if value is not None:
                os.environ[name] = value


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _phase2_sources() -> tuple:
    """The frozen sources with their size and mtime: the cheap fingerprint the digest cache keys on."""
    root = Path(__file__).resolve().parent
    package = root / "clinical_core"
    return tuple(sorted((path.relative_to(root).as_posix(), path.stat().st_size,
                         path.stat().st_mtime_ns)
                        for path in package.rglob("*.py")
                        if "__pycache__" not in path.parts and path.is_file()
                        and not path.name.startswith(".")))


@lru_cache(maxsize=8)
def _phase2_digest_for(fingerprint: tuple) -> str:
    root = Path(__file__).resolve().parent
    sources = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
               for name, _size, _mtime in fingerprint}
    return hashlib.sha256(json.dumps(sources, sort_keys=True).encode("utf-8")).hexdigest()


def phase2_digest_now() -> str:
    """The Phase-2 closure digest as the repository stands, RECOMPUTED over the 141 frozen sources.

    Reading ``runtime_shadow.PHASE2_DIGEST`` here would compare a constant with itself, so the safety
    condition that watches the freeze would be true by construction and could never fire.

    P3-17: the result used to be cached for the life of the process, so a change in ``clinical_core``
    after the first call could not fire the condition either. The cache is keyed on the sources' names,
    sizes and modification times, so it is still one hash per unchanged tree and a changed tree is a
    different key.
    """
    return _phase2_digest_for(_phase2_sources())


def authoritative(encounter) -> dict:
    """Everything authoritative one encounter produced: what the resident sees and what scoring reads."""
    state = encounter.state
    return {"entries": encounter.entries, "ledger": encounter.ledger,
            "observable": state.get("observable"), "hidden": state.get("hidden"),
            "family_state": state.get("family_state"), "sim_time": state.get("sim_time"),
            "keys": sorted(state)}


def fates(encounter) -> list:
    return [(order.get("class"), order.get("fate")) for entry in encounter.entries
            for order in entry.get("orders") or []]


def _play_battery(variant: str, mode: str | None) -> tuple:
    """The battery of one case, with the shadow in ``mode``; returns (categories, [(label, encounter)]).

    The battery is the repository's own, played once. Its cached result is cleared by ``collecting`` so a
    cached dictionary can never be read as a fresh run.
    """
    import pilot_acceptance as acceptance
    collected: list = []
    with shadow(mode), acceptance.collecting(
            lambda label, encounter, turns: collected.append((label, encounter, turns))):
        started = time.perf_counter()
        categories = acceptance.battery(variant)
        elapsed = time.perf_counter() - started
    return dict(categories), collected, elapsed


#: A variable neither architecture moved across the compared minutes: comparing it says nothing, so it is
#: reported as not exercised instead of counting as a domain that agrees.
NOT_EXERCISED = "NOT_EXERCISED"


def _moved(values) -> bool:
    """Whether a series actually changed. One value, or none, is not movement."""
    seen = {repr(value) for value in values if value is not None}
    return len(seen) > 1


def _domains(session) -> dict:
    """Comparability by domain over the minutes a legacy truth existed, and what each domain exercised.

    A domain used to read COMPARABLE as long as no variable of it was NOT_COMPARABLE -- which a scenario
    that never moved the domain also satisfies, so the field said nothing. A variable now counts only when
    one of the two sides moved it across the compared minutes; a domain nobody exercised says so.
    """
    from clinical_core import comparison
    compared = [item for item in session.minutes if item.compared_against_legacy]
    names = {variable.name for variable in comparison.VARIABLES
             if variable.kind not in ("core_only", "legacy_only")}
    out: dict = {}
    for domain in fam.DOMAINS:
        belongs = sorted(name for name in names if fam.DOMAIN_OF.get(name) == domain)
        if not belongs:
            out[domain] = {"comparability": NOT_COMPARABLE, "variables": [], "classes": {},
                           "why": "no variable of the certified comparison table belongs to this domain"}
            continue
        statuses: dict = {name: set() for name in belongs}
        legacy_series: dict = {name: [] for name in belongs}
        core_series: dict = {name: [] for name in belongs}
        # The core's own series runs over EVERY shadow minute, not only the compared ones: a scenario with
        # a single turn has one comparison and still moves the patient between the arrival and that turn.
        for minute in session.minutes:
            for name in belongs:
                if name in (minute.derived or {}):
                    core_series[name].append((minute.derived or {}).get(name))
        for minute in compared:
            seen = {record.variable: record for record in minute.divergences}
            for name in belongs:
                record = seen.get(name)
                statuses[name].add(record.status if record is not None else "AGREES")
                if record is not None:
                    legacy_series[name].append(record.legacy)
                elif name in (minute.derived or {}):
                    # It agreed, so the legacy value is the core's value for that minute.
                    legacy_series[name].append((minute.derived or {}).get(name))
        exercised = {name for name in belongs
                     if _moved(legacy_series[name]) or _moved(core_series[name])}
        incomparable = {name for name, values in statuses.items() if values == {rs.NOT_COMPARABLE}}
        if not compared:
            comparability = NOT_COMPARABLE
        elif not exercised:
            comparability = NOT_EXERCISED
        elif not (incomparable & exercised):
            comparability = COMPARABLE
        elif incomparable >= exercised:
            comparability = NOT_COMPARABLE
        else:
            comparability = PARTIALLY_COMPARABLE
        classes: dict = {}
        for values in statuses.values():
            for status in values:
                if status != "AGREES":
                    classes[status] = classes.get(status, 0) + 1
        out[domain] = {"comparability": comparability, "variables": belongs, "classes": classes,
                       "exercised": sorted(exercised),
                       "not_exercised": sorted(set(belongs) - exercised),
                       "agreeing": sorted(name for name, values in statuses.items()
                                          if values == {"AGREES"})}
    return out


def _coverage(encounter, session) -> dict:
    """Every action class the engine executed in this scenario, and how the shadow represents it."""
    from clinical_core import legacy_adapter
    mapped = set(fam.ADAPTERS["gi_bleed"].maps)
    mirrored = {event.kind for event in session.mirrored} if session is not None else set()
    refused = {}
    for gap in (session.gaps if session is not None else []):
        if gap.get("kind"):
            refused[str(gap["kind"])] = str(gap.get("why") or "")
    haemostasis = session is not None and session.endoscopy_at is not None
    procedures = [action for entry in encounter.entries for action in entry.get("action_summaries") or []
                  if str(action.get("type") or "") == "procedure"]
    endoscopies = [action for action in procedures
                   if "endoscop" in str(action.get("label") or action.get("name") or "").lower()]
    out: dict = {}
    for entry in encounter.entries:
        for action in entry.get("action_summaries") or []:
            kind = str(action.get("type") or "")
            if not kind:
                # An action the engine reports without a type cannot be mapped, mirrored or replayed, so
                # dropping it silently was the one way an unrepresented action could pass unnoticed.
                out["untyped_action"] = {"status": UNSUPPORTED,
                                         "why": "the engine reported an action with no type: it cannot "
                                                "be mapped to a core contributor"}
                continue
            if kind == "procedure":
                # The engine reports the endoscopy as a procedure receipt and the core receives it through
                # ``family_state.endoscopy_at``. The reading is tied to THAT receipt: a second kind of
                # procedure -- an embolisation, say -- is not mirrored by a haemostasis that happened to
                # occur, and must read as a gap instead.
                mirrored_here = (haemostasis and len(endoscopies) == len(procedures)
                                 and len(procedures) >= 1)
                out[kind] = ({"status": FULLY_MIRRORED,
                              "why": f"endoscopic haemostasis at minute {session.endoscopy_at}, through "
                                     f"family_state"} if mirrored_here else
                             {"status": UNSUPPORTED,
                              "why": "a procedure the GI mapping does not represent: only the endoscopic "
                                     "haemostasis reaches the core, through family_state"})
            elif kind in refused:
                # P3-17: this used to be tested AFTER "mapped and mirrored", and ``mirrored`` is the set
                # of classes mirrored anywhere in the session, so one order of a class that fell through
                # read as fully mirrored because another order of the same class had not. A declared gap
                # now wins over a sibling that happened to be mirrored.
                out[kind] = {"status": UNSUPPORTED, "why": refused[kind]}
            elif kind in mapped and kind in mirrored:
                out[kind] = {"status": FULLY_MIRRORED, "why": "mapped to a certified core contributor"}
            elif kind in legacy_adapter.NOT_PHYSIOLOGICAL:
                out.setdefault(kind, {"status": STRUCTURAL_ONLY,
                                      "why": "Phase 2 declares this order class non-physiological"})
            elif kind in mapped:
                out.setdefault(kind, {"status": STRUCTURAL_ONLY,
                                      "why": "mapped, but no event of this kind was mirrored in this run"})
            else:
                out.setdefault(kind, {"status": UNSUPPORTED,
                                      "why": "the GI mapping has no writer for this order type"})
    if session is not None and session.endoscopy_at is not None:
        out["endoscopy"] = {"status": FULLY_MIRRORED,
                            "why": f"haemostasis at minute {session.endoscopy_at}, read from family_state"}
    return out


#: The display variables a region position is read for: the key ``legacy_against_region`` uses, the name
#: of the envelope series, and the name the certified comparison table gives the same reading.
POSITION_VARIABLES = (("sbp", "sbp", "sbp"), ("dbp", "dbp", "dbp"), ("map", "map", "map"),
                      ("hr", "pulse_rate_bpm", "hr"), ("spo2", "spo2", "spo2"),
                      ("respiratory_rate", "respiratory_rate", "respiratory_rate"),
                      ("crt", "crt_s", "crt_s"))


def _legacy_at(session, minute: int, result) -> tuple:
    """The legacy display values of one compared minute, as the comparison itself saw them.

    A variable that MISMATCHED carries its legacy value in its divergence record. A variable that AGREED
    has no record, and agreeing means the legacy value equals the core's structural witness after the
    display projection; the structural witness is used for it and the reading is marked ``by_agreement``,
    because a value that already equals the structural witness cannot fall outside a band containing it.
    """
    records = {record.variable: record for item in session.minutes if item.minute == minute
               for record in item.divergences}
    legacy, agreed = {}, set()
    for legacy_key, envelope_name, record_name in POSITION_VARIABLES:
        record = records.get(record_name) or records.get(legacy_key)
        if record is not None:
            if record.status != fam.NOT_COMPARABLE and record.legacy is not None:
                legacy[legacy_key] = record.legacy
            continue
        band = (result.envelope.get(envelope_name) or {}).get(minute)
        if band and band[2] is not None:
            legacy[legacy_key] = band[2]
            agreed.add(legacy_key)
    return legacy, agreed


def region_evidence(session, encounter) -> dict:
    """The named region witnesses of this scenario, and where the legacy engine sits at EVERY minute
    a legacy truth existed.

    The witnesses are P3-11-5's: the committed point plus the lower and upper corner of the declared
    calibration region. Outside the region does not mean the core is right -- the legacy engine is not
    clinical ground truth and no magnitude in the region is approved.
    """
    from clinical_core import legacy_adapter
    compared = sorted(session.runner.compared) if session is not None and session.runner is not None else []
    minute = compared[-1] if compared else 0
    if session is None or session.runner is None or minute < 1:
        return {"status": "NOT_RUN", "why": "no shadow run or no compared minute"}
    # The ensemble takes ONE state: the adapter reads the arrival from it and the mapping reads the
    # haemostasis minute from its ``family_state``. The live arrival carries no endoscopy yet, so the
    # minute the engine performed it is injected here -- the same two facts the live run used, no more.
    arrival = dict(session.arrival or {})
    arrival["family_state"] = {**(arrival.get("family_state") or {}),
                               "endoscopy_at": session.endoscopy_at}
    result = fam.ensemble(session.family, session.case_id, minute, points=fam.POINTS,
                          mirrored=session.mirrored, state=arrival)
    try:
        legacy = legacy_adapter.snapshot(encounter.state)
    except Exception as error:  # the harness reports it; it never raises into a run
        return {"status": "NOT_RUN", "why": f"the legacy snapshot could not be read: {error}"}
    positions, counts, agreements = {}, {}, {}
    for compared_minute in compared:
        values, agreed = _legacy_at(session, compared_minute, result)
        reading = fam.legacy_against_region(values, result, compared_minute)
        for name, item in reading.items():
            if name in agreed:
                item["by_agreement"] = True
                agreements[name] = agreements.get(name, 0) + 1
            counts.setdefault(name, {})
            counts[name][item["status"]] = counts[name].get(item["status"], 0) + 1
        positions[compared_minute] = reading
    position = positions.get(minute, {})
    widths: dict = {}
    for name, rows in result.envelope.items():
        band = rows.get(minute)
        if band:
            low, high, structural = band
            widths[name] = {"lower": low, "upper": high, "structural": structural,
                            "width": high - low}
    if not widths:
        # An empty envelope is never reported as a comparison: the witnesses did not run.
        return {"status": "NOT_RUN", "minute": minute,
                "why": "no witness produced a band at this minute",
                "failures": [vars(item) for point, runner in result.runs.items()
                             for item in runner.failures]}
    return {"status": "RUN", "minute": minute, "minutes": compared, "points": list(result.points),
            "snapshots": [item["id"] for item in result.to_dict()["snapshots"]],
            "legacy_against_region": position, "positions": positions, "counts": counts,
            "by_agreement": agreements, "widths": widths}


def scenario_evidence(label: str, variant: str, turns: Sequence, off, on) -> dict:
    """Everything P3-11-3 asks of one acceptance scenario, with the shadow on and off side by side."""
    session = getattr(on, "shadow", None)
    if session is not None:
        # The encounter cannot know which acceptance scenario it is: the harness names it here, before the
        # artifact is read, so the replay input carries the scenario id P3-11-11 asks for.
        session.scenario_id = label
        if session.runner is not None:
            session.runner.scenario_id = label
    live = list(session.digests()) if session is not None else []
    replayed = [item["state_digest"] for item in session.replay()["minutes"]] if session is not None else []
    record = session.record() if session is not None else {}
    captured = record.get("replay_input")
    divergences = [vars(item) for minute in (session.minutes if session is not None else [])
                   for item in minute.divergences]
    unexpected = [item for item in divergences
                  if item["status"] in (rs.UNEXPECTED, rs.SAFETY_CRITICAL)]
    off_authority, on_authority = authoritative(off), authoritative(on)
    mirrored_ids = [event.order_id for event in (session.mirrored if session is not None else [])]
    checks = {
        "authoritative_record_differs": _digest(off_authority) != _digest(on_authority),
        "order_fates_differ": fates(off) != fates(on),
        "persistence_differs": _digest({key: off_authority[key] for key in
                                        ("observable", "hidden", "family_state", "keys")})
                               != _digest({key: on_authority[key] for key in
                                           ("observable", "hidden", "family_state", "keys")}),
        "minute_alignment_differs": bool(off.state.get("sim_time") != on.state.get("sim_time")
                                         or (live and len(live) != int(on.state.get("sim_time") or 0))),
        "action_duplicated": len(mirrored_ids) != len(set(mirrored_ids)),
        "replay_differs_from_live": bool(live) and live != replayed,
        "shadow_failure_reached_the_encounter": _digest(off_authority) != _digest(on_authority)
                                                and bool(session is not None and session.failures),
        "phase2_digest_changed": phase2_digest_now() != rs.PHASE2_DIGEST,
    }
    return {
        "scenario": label,
        "case": variant,
        "shadow_case_id": None if session is None else session.case_id,
        "turns": list(turns),
        "arrival_digest": _digest(on.arrival),
        "authoritative_digest": _digest(on_authority),
        "fates": fates(on),
        "legacy_final": {"minute": on.state.get("sim_time"), "arrested": on.arrested,
                         "observable_digest": _digest(on.state.get("observable"))},
        "mirrored": [{"order_id": event.order_id, "minute": event.minute, "kind": event.kind,
                      "ledger_order_id": event.ledger_order_id, "submission_id": event.submission_id}
                     for event in (session.mirrored if session is not None else [])],
        "coverage": _coverage(on, session),
        "snapshot": (captured or {}).get("snapshot"),
        "live_digests": live,
        "replay_digests": replayed,
        "live_equals_replay": bool(live) and live == replayed,
        "final_digest": live[-1] if live else None,
        "minutes": len(live),
        "compared_minutes": record.get("compared_minutes", []),
        "domains": _domains(session) if session is not None else {},
        "region": region_evidence(session, on),
        "divergence_classes": _counted([item["status"] for item in divergences]),
        "unexpected": unexpected,
        "partially_explained": [item for item in divergences
                                if item["status"] == rs.PARTIALLY_EXPLAINED],
        "boundaries": [item for item in divergences if item["status"] == rs.BOUNDARY],
        "failures": [vars(item) for item in (session.failures if session is not None else [])],
        "gaps": list(session.gaps) if session is not None else [],
        "replay_digest": record.get("replay_digest"),
        "replay_input": captured,
        "artifact_sizes": (fam.artifact_sizes(session.runner)
                           if session is not None and session.runner is not None else {}),
        "safety": checks,
        "safe": not any(checks.values()),
    }


def _counted(values: Sequence) -> dict:
    out: dict = {}
    for value in values:
        out[str(value)] = out.get(str(value), 0) + 1
    return out


def battery_evidence(variant: str) -> dict:
    """The whole acceptance battery of one GI case, played off and on, scenario by scenario."""
    off_categories, off_runs, off_elapsed = _play_battery(variant, None)
    on_categories, on_runs, on_elapsed = _play_battery(variant, rs.MODE_SHADOW_COMPARE)
    paired, mismatched = [], []
    by_label: dict = {}
    for label, encounter, turns in off_runs:
        by_label.setdefault(label, []).append((encounter, turns))
    used: dict = {}
    for label, encounter, turns in on_runs:
        index = used.get(label, 0)
        used[label] = index + 1
        candidates = by_label.get(label) or []
        if index >= len(candidates):
            mismatched.append({"scenario": label, "why": "the shadow run played a scenario the off run "
                                                         "did not: the battery is not deterministic"})
            continue
        off_encounter, off_turns = candidates[index]
        if list(off_turns) != list(turns):
            mismatched.append({"scenario": label, "why": "the two runs played different orders"})
            continue
        paired.append(scenario_evidence(label, variant, turns, off_encounter, encounter))
    return {
        "case": variant,
        "categories_off": off_categories,
        "categories_on": on_categories,
        "categories_identical": off_categories == on_categories,
        "failed_categories": sorted(name for name, result in on_categories.items() if not result["ok"]),
        "scenarios": paired,
        "unpaired": mismatched,
        "timing": {"legacy_s": round(off_elapsed, 3), "legacy_and_shadow_s": round(on_elapsed, 3),
                   "ratio": round(on_elapsed / off_elapsed, 3) if off_elapsed else None},
        "versions": rs.versions(),
    }


def gi_evidence() -> dict:
    """The full GI acceptance-battery evidence: both cases, every scenario, with the readiness verdict."""
    cases = [battery_evidence(variant) for variant in gi_variants()]
    scenarios = [scenario for case in cases for scenario in case["scenarios"]]
    coverage: dict = {}
    for scenario in scenarios:
        for kind, how in scenario["coverage"].items():
            coverage.setdefault(kind, {"status": how["status"], "why": how["why"], "scenarios": []})
            coverage[kind]["scenarios"].append(scenario["scenario"])
            if how["status"] == UNSUPPORTED:  # the worst reading of a class wins
                coverage[kind].update({"status": UNSUPPORTED, "why": how["why"]})
    unsupported = sorted(kind for kind, how in coverage.items() if how["status"] == UNSUPPORTED)
    unexpected = [item for scenario in scenarios for item in scenario["unexpected"]]
    # The golden declares some differences in only some of its scenarios. That is not an explanation of
    # THIS scenario, so the class is reported with its count, the scenarios that declare it and what those
    # scenarios ordered -- and it blocks readiness until a reader has looked at it. The case that forced
    # the rule is ``consciousness_level``: the golden declares it in 1 of its 20 scenarios, so letting it
    # pass as "partially explained" would silence the one reading whose disagreement must be loud.
    conditions = rs.golden_conditions("gi_bleed")
    partially: dict = {}
    for scenario in scenarios:
        for item in scenario.get("partially_explained") or []:
            name = item["variable"]
            entry = partially.setdefault(name, {"minutes": 0, "scenarios": set(),
                                                **conditions.get(name, {})})
            entry["minutes"] += 1
            entry["scenarios"].add(scenario["scenario"])
    for entry in partially.values():
        entry["scenarios"] = sorted(entry["scenarios"])
    region: dict = {}
    agreements: dict = {}
    minutes_compared = 0
    for scenario in scenarios:
        minutes_compared += len(scenario["region"].get("minutes") or [])
        for name, statuses in (scenario["region"].get("counts") or {}).items():
            region.setdefault(name, {})
            for status, count in statuses.items():
                region[name][status] = region[name].get(status, 0) + count
        for name, count in (scenario["region"].get("by_agreement") or {}).items():
            agreements[name] = agreements.get(name, 0) + count
    unsafe = [scenario["scenario"] for scenario in scenarios if not scenario["safe"]]
    not_replayed = [scenario["scenario"] for scenario in scenarios if not scenario["live_equals_replay"]]
    blockers = []
    if unsafe:
        blockers.append(f"SAFETY_CONDITION_TRIPPED in {sorted(set(unsafe))}")
    if not_replayed:
        blockers.append(f"LIVE_DIFFERS_FROM_REPLAY in {sorted(set(not_replayed))}")
    if unexpected:
        blockers.append(f"UNEXPECTED_STRUCTURAL_DIVERGENCE on "
                        f"{sorted({item['variable'] for item in unexpected})}")
    if unsupported:
        blockers.append(f"TREATMENT_GAP on {unsupported}")
    if partially:
        blockers.append("PARTIALLY_EXPLAINED_DIVERGENCE_REQUIRES_A_READING on "
                        f"{sorted(partially)}: the golden declares each of these in some of its scenarios "
                        "and not in others, so it does not explain this one")
    if any(not case["categories_identical"] for case in cases):
        blockers.append("THE_BATTERY_DECIDED_DIFFERENTLY_WITH_THE_SHADOW_ON")
    if phase2_digest_now() != rs.PHASE2_DIGEST:
        blockers.append("PHASE2_DIGEST_CHANGED")
    return {
        "cases": cases,
        "scenarios_played": len(scenarios),
        "coverage": coverage,
        "unsupported": unsupported,
        "unexpected": unexpected,
        "partially_explained": partially,
        "golden_conditions": conditions,
        "unsafe_scenarios": sorted(set(unsafe)),
        "legacy_against_region": region,
        "within_by_agreement": agreements,
        "compared_minutes": minutes_compared,
        "region_notes": fam.region_notes(),
        "live_equals_replay": not not_replayed,
        "blockers": blockers,
        "readiness": ("GI_FULL_LIVE_SHADOW_EVIDENCE_READY" if not blockers
                      else "GI_FULL_LIVE_SHADOW_EVIDENCE_NOT_READY"),
        "versions": rs.versions(),
    }


def scenario_matrix(evidence: Mapping | None = None) -> list:
    """The P3-11-19 matrix: one row per scenario, with nothing summarized away."""
    data = evidence if evidence is not None else gi_evidence()
    rows = []
    for case in data["cases"]:
        for scenario in case["scenarios"]:
            rows.append({
                "scenario": scenario["scenario"],
                "case": scenario["case"],
                "actions": sorted(scenario["coverage"]),
                "snapshots": [(scenario["snapshot"] or {}).get("id")],
                "live_equals_replay": scenario["live_equals_replay"],
                "authority_unchanged": not scenario["safety"]["authoritative_record_differs"],
                "comparable_domains": sorted(name for name, item in scenario["domains"].items()
                                             if item["comparability"] == COMPARABLE),
                "partially_comparable": sorted(name for name, item in scenario["domains"].items()
                                               if item["comparability"] == PARTIALLY_COMPARABLE),
                "divergence_classes": scenario["divergence_classes"],
                "boundaries": len(scenario["boundaries"]),
                "shadow_failures": [item["classification"] for item in scenario["failures"]],
                "gaps": sorted({str(gap.get("kind")) for gap in scenario["gaps"]}),
                "unexpected": len(scenario["unexpected"]),
                "replay_artifact_valid": bool(scenario["replay_digest"]) and scenario["live_equals_replay"],
            })
    return rows


def replay_from_json(scenario: Mapping) -> dict:
    """Rebuild a scenario's shadow trajectory from its serialized artifact alone (P3-11-12).

    The artifact goes through ``json.dumps``/``json.loads`` first, so nothing in memory can help it.
    """
    payload = json.loads(json.dumps(scenario["replay_input"], default=str)) \
        if "replay_input" in scenario else None
    if payload is None:
        return {"ok": False, "why": "the scenario carries no replay artifact"}
    replayed = fam.replay_shadow_encounter(payload)
    digests = [item["state_digest"] for item in replayed["results"]][1:]
    return {"ok": digests == list(scenario["live_digests"]), "digests": digests,
            "final_digest": replayed["final_digest"], "minutes": replayed["minutes"]}


def artifact_totals(evidence: Mapping | None = None) -> dict:
    """What a full battery of shadow evidence costs to keep (P3-11-18). Faculty and research only."""
    data = evidence if evidence is not None else gi_evidence()
    minimal = verbose = replay = 0
    scenarios = 0
    for case in data["cases"]:
        for scenario in case["scenarios"]:
            scenarios += 1
            sizes = scenario.get("artifact_sizes") or {}
            replay += int(sizes.get("replay_input_bytes") or 0)
            minimal += int(sizes.get("minimal_trace_bytes") or 0)
            verbose += int(sizes.get("verbose_trace_bytes") or 0)
    return {"scenarios": scenarios, "replay_input_bytes": replay,
            "minimal_trace_bytes": minimal, "verbose_trace_bytes": verbose,
            "retention_default": "minimal trace plus the replay input: the verbose trace is reproducible "
                                 "from the input, so keeping it is a convenience, not a record"}
