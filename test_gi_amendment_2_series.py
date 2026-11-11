"""P3-175 / P3-176 / P3-178: the GI consciousness and collapse LIVE-SHADOW SERIES (analysis; read-only; development only).

It is TEST-SIDE tooling (its name starts with ``test_``, like the repository's other test harnesses): it plays encounters through
the shadow and reads the store and the observer, which no module outside the declared shadow layer may do. It has no test of its own.

It plays real GI encounters through the Phase-3 live shadow (``pilot_acceptance.Encounter`` with the shadow flag on), so the
legacy engine remains the only authority and decides every minute; the session's own run (committed profile, PHASE2_AMENDMENT_2
OFF) and the three development witnesses of the amendment (LOW, CENTER_REFERENCE, HIGH) are read from the live ensemble, each
kept as its own trajectory. Nothing here selects, averages or prefers a witness, writes to an encounter, reaches the resident or
the score, or tunes a magnitude: it MEASURES, and every magnitude it reports is a development behavioural region's point.

Scenarios (the same rules on both supported GI cases, no per-case value):

  untreated                 no order after arrival, to a fixed horizon or to the first core boundary;
  early_treatment           access, crystalloid and red cells at minute 10;
  delayed_treatment         the same bundle at minute 120;
  fluid_focused             crystalloid only (1 L at minute 10, 1 L more at minute 40);
  blood_focused             red cells only (2 units at minute 10);
  severe_deterioration      crystalloid only (1 L), given when the CENTER_REFERENCE witness first reads OBTUNDED;
  recovery_after_severe     crystalloid and red cells, given when the CENTER_REFERENCE witness first reads UNRESPONSIVE.

The two adaptive rules are applied identically to both cases; they read a witness only to decide WHEN a development series
gives an order, never to change what the shadow computes.
"""
from __future__ import annotations

import os
from typing import Any, Mapping, Sequence

import pilot_acceptance as acceptance
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
from clinical_core import legacy_adapter
from clinical_core import systemic_consciousness as sc

SERIES_VERSION = "P3-175"
CASES = ("gi_bleed_57m", "gi_bleed_72f")
WITNESSES = tuple(fam.GI_AMENDMENT_2_WITNESS_NAMES)
ACCESS = "Place an IV line."
SALINE = "Give 1 L of normal saline."
BLOOD = "Transfuse 2 units of packed red blood cells."
BLOOD_MORE = "Transfuse 4 units of packed red blood cells."
#: The longest a series runs, and the cases' own horizon: the core's existing boundary (output reaching zero with a pulse and no
#: declared terminal rule) ends a witness's run, and the series records where and why. It is reported, never worked around.
HORIZON = 240
SCENARIOS = ("untreated", "early_treatment", "delayed_treatment", "fluid_focused", "blood_focused", "severe_deterioration",
             "recovery_after_severe")
CATEGORIES = tuple(sc.CATEGORIES)
#: The legacy engine's mental-state words, by the level the core's ladder gives them (``legacy_adapter.LEVEL_OF``).
LEGACY_LEVEL = dict(legacy_adapter.LEVEL_OF)


def _plan(scenario: str) -> dict:
    """The fixed schedule of a scenario: minute -> orders, and the length of the series. No case value is read."""
    if scenario == "untreated":
        return {"at": {}, "horizon": HORIZON}
    if scenario == "early_treatment":
        return {"at": {10: (ACCESS, SALINE, BLOOD)}, "horizon": 120}
    if scenario == "delayed_treatment":
        return {"at": {120: (ACCESS, SALINE, BLOOD)}, "horizon": 200}
    if scenario == "fluid_focused":
        return {"at": {10: (ACCESS, SALINE), 40: (SALINE,)}, "horizon": 120}
    if scenario == "blood_focused":
        return {"at": {10: (ACCESS, BLOOD)}, "horizon": 120}
    if scenario == "severe_deterioration":
        return {"at": {}, "horizon": HORIZON, "trigger": (2, (ACCESS, SALINE))}
    if scenario == "recovery_after_severe":
        return {"at": {}, "horizon": HORIZON, "trigger": (3, (ACCESS, SALINE, BLOOD_MORE)), "after": 45}
    raise ValueError(f"unknown scenario {scenario!r}: {list(SCENARIOS)}")


def _legacy_sample(encounter) -> dict:
    observable = dict(encounter.state.get("observable") or {})
    mental = observable.get("mental_status")
    return {"minute": int(encounter.minute), "mental_status": mental, "legacy_level": LEGACY_LEVEL.get(str(mental)),
            "sbp": observable.get("sbp"), "dbp": observable.get("dbp"), "hr": observable.get("hr"),
            "spo2": observable.get("spo2"), "pulse_present": observable.get("pulse_present"),
            "arrested": bool(encounter.arrested)}


def _level_of(session, witness: str) -> int | None:
    """The witness's observable category at its last recorded minute (None before it has one)."""
    runner = session.ensemble.runners[witness] if session.ensemble is not None else None
    if runner is None or not runner.results:
        return None
    return runner.results[-1].derived.get("consciousness_level")


def run_scenario(case: str, scenario: str, *, store_directory: str | None = None, horizon: int | None = None,
                 trigger_witness: str = "CENTER_REFERENCE") -> dict:
    """One real encounter, one scenario: the legacy truth per minute, every witness's channels, the orders and the ending.

    ``horizon`` lengthens a series (the boundary audit of P3-178 runs the untreated course until something ends it).
    ``trigger_witness`` names the witness whose reading decides WHEN an adaptive scenario treats (P3-181: each witness is
    treated at its OWN first UNRESPONSIVE minute, so that each enters its recovery substantially impaired)."""
    plan = _plan(scenario)
    if trigger_witness not in WITNESSES:
        raise ValueError(f"unknown witness {trigger_witness!r}")
    if horizon is not None:
        plan = {**plan, "horizon": int(horizon)}
    orders, legacy, triggered = [], [], None
    previous_store = os.environ.get("MRS_SHADOW_TRACE_STORE")
    from runtime_shadow_store import STORE_FLAG
    if store_directory is not None:
        os.environ[STORE_FLAG] = store_directory
    try:
        with ev.shadow(rs.MODE_SHADOW_COMPARE):
            encounter = acceptance.Encounter(case)
            session = encounter.shadow
            legacy.append(_legacy_sample(encounter))
            stop_after, fired = None, set()
            while int(encounter.minute) < plan["horizon"]:
                due = []
                for minute in sorted(plan["at"]):
                    if minute <= int(encounter.minute) and minute not in fired:
                        fired.add(minute)
                        due.extend(plan["at"][minute])
                trigger = plan.get("trigger")
                if triggered is None and trigger is not None:
                    level = _level_of(session, trigger_witness)
                    if level is not None and level >= trigger[0]:
                        triggered, due = int(encounter.minute), list(trigger[1])
                        stop_after = triggered + plan["after"] if plan.get("after") else None
                if due:
                    # One turn, one text: the legacy engine runs the bundle's orders from the same minute (an infusion then
                    # takes its own minutes on the clock), and the shadow mirrors each at that minute.
                    started, text = int(encounter.minute), " ".join(due)
                    entry = encounter.order(text)
                    orders.append({"minute": started, "text": text, "parts": list(due), "executed": bool(entry["executed"]),
                                   "clock_after": int(encounter.minute)})
                    legacy.append(_legacy_sample(encounter))
                if encounter.arrested or session is None or session.runner is None:
                    break
                if stop_after is not None and int(encounter.minute) >= stop_after:
                    break
                before = int(encounter.minute)
                encounter.wait_until(before + 1, step=1)
                legacy.append(_legacy_sample(encounter))
                if int(encounter.minute) == before:                       # the clock did not move: nothing more to read
                    break
                if any(item.classification == rs.BOUNDARY for item in session.failures):
                    break
            ensemble = session.ensemble
            rows = {name: fam.run_channels(runner) for name, runner in ensemble.runners.items()} if ensemble else {}
            own = fam.run_channels(session.runner) if session.runner is not None else []
            failures = [{"minute": item.minute, "where": item.where, "exception": item.exception,
                         "classification": item.classification, "message": item.message[:160]}
                        for item in session.failures]
            profile_of = {name: runner.profile.amendment_2 for name, runner in (ensemble.runners.items() if ensemble else [])}
            return {"case": case, "scenario": scenario, "orders": orders, "legacy": legacy, "session_rows": own,
                    "witness_rows": rows, "failures": failures, "profile": profile_of, "triggered_at": triggered,
                    "trigger_witness": trigger_witness if plan.get("trigger") else None,
                    "encounter_minute": int(encounter.minute), "legacy_arrested": bool(encounter.arrested),
                    "session": session, "encounter": encounter}
    finally:
        if store_directory is not None:
            if previous_store is None:
                os.environ.pop(STORE_FLAG, None)
            else:
                os.environ[STORE_FLAG] = previous_store


# -- what a witness's trajectory says -------------------------------------------------------------------------------

def _first(rows: Sequence, predicate) -> int | None:
    return next((row["minute"] for row in rows if predicate(row["channels"])), None)


def _channel(row: Mapping, name: str):
    return row["channels"].get(name)


def causal_order(rows: Sequence, profile) -> dict:
    """The first minute of each link of the required chain, read from one witness's own channels.

    hemorrhage (volume below arrival) -> delivery below the signal's bound -> F > 0 -> the observable category rises ->
    only then the soft collapse (needs perfusion AND delivery failing, for minutes). Perfusion is reported beside it.
    """
    if not rows:
        return {}
    v0 = rows[0]["channels"]["V"]
    first = {
        "volume_below_arrival": _first(rows, lambda c: c["V"] < v0 * 0.995),
        "delivery_below_normal_bound": _first(rows, lambda c: (c.get("relative_delivery") is not None
                                                               and c["relative_delivery"] < profile.delivery_normal)),
        "perfusion_below_normal_bound": _first(rows, lambda c: (c.get("relative_perfusion") is not None
                                                                and c["relative_perfusion"] < profile.perfusion_normal)),
        "f_above_zero": _first(rows, lambda c: (c.get("systemic_encephalopathy_burden") or 0.0) > 0.01),
        "somnolent": _first(rows, lambda c: (c.get("category_index") or 0) >= 1),
        "obtunded": _first(rows, lambda c: (c.get("category_index") or 0) >= 2),
        "unresponsive": _first(rows, lambda c: (c.get("category_index") or 0) >= 3),
        "collapse_impending": _first(rows, lambda c: (c.get("collapse_state_index") or 0) >= 1),
        "collapse_established": _first(rows, lambda c: (c.get("collapse_state_index") or 0) >= 2),
        "pulse_absent": _first(rows, lambda c: c.get("pulse_present") is False),
    }
    chain = ("volume_below_arrival", "delivery_below_normal_bound", "f_above_zero", "somnolent")
    seen = [first[name] for name in chain]
    first["chain_in_order"] = None if None in seen else all(a <= b for a, b in zip(seen, seen[1:]))
    # the collapse needs BOTH channels failing: at the minute it first appears, the minute before already had both failing
    collapse = first["collapse_impending"]
    if collapse is None:
        first["collapse_needs_both_failures"] = None
    else:
        before = [row for row in rows if row["minute"] < collapse]
        prior = before[-1]["channels"] if before else rows[0]["channels"]
        now = next(row for row in rows if row["minute"] == collapse)["channels"]
        both = lambda c: (c.get("relative_perfusion") is not None and c.get("relative_delivery") is not None
                          and sc.perfusion_failure(c["relative_perfusion"], profile) > 0.0
                          and sc.delivery_failure(c["relative_delivery"], profile) > 0.0)
        first["collapse_needs_both_failures"] = bool(both(prior) or both(now))
    first["category_never_skips_up"] = all(
        (b["channels"].get("category_index") or 0) - (a["channels"].get("category_index") or 0) <= 1
        for a, b in zip(rows, rows[1:]) if "category_index" in a["channels"] and "category_index" in b["channels"])
    return first


def category_sequence(rows: Sequence) -> list:
    """(first_minute, category_index) each time the observable category changes."""
    out, last = [], None
    for row in rows:
        index = row["channels"].get("category_index")
        if index is not None and index != last:
            out.append((row["minute"], int(index)))
            last = index
    return out


def recovery(rows: Sequence, profile, treatment_minute: int | None) -> dict:
    """The faculty's recovery reading (2026-11-11), measured on one witness's own channels.

    "Meaningful recovery in about 3 to 5 simulated minutes" means: starting from an impairment of about 0.80, the observable
    level crosses below 0.50 in about 3 to 5 minutes WHEN the upstream physiology has recovered enough. It does not ask for
    normalisation below 0.25 in that interval. So the measure is taken from the minute the upstream physiology has recovered
    (relative delivery back above its normal bound: the signal that feeds F is zero), not from the order: a transfusion takes
    minutes to restore delivery, and that is upstream time, not F time. F then falls by the first-order law of its own clearing
    constant, so the 0.80 -> 0.50 time of a witness is ``burden_clear_tau * ln(0.8 / 0.5)``, and what the live series adds is the
    check that the observed crossing follows that law from wherever F stood when the upstream recovered.
    """
    import math
    if not rows or treatment_minute is None:
        return {"applicable": False, "why": "no treatment was given"}
    f = lambda row: row["channels"].get("systemic_encephalopathy_burden")
    after = [row for row in rows if row["minute"] >= treatment_minute and f(row) is not None]
    if not after or f(after[0]) < 0.50:
        return {"applicable": False, "why": "F stood below 0.50 when the treatment was given: nothing impaired to recover from",
                "f_at_treatment": None if not after else f(after[0])}
    tau = profile.burden_clear_tau
    upstream = next((row for row in after if (row["channels"].get("relative_delivery") or 0.0) >= profile.delivery_normal), None)
    below = next((row["minute"] for row in after if f(row) < 0.50), None)
    descent = next((row["minute"] for row in after
                    if (row["channels"].get("category_index") or 0) < (after[0]["channels"].get("category_index") or 0)), None)
    out = {"applicable": True, "treatment_minute": treatment_minute, "f_at_treatment": f(after[0]),
           "category_at_treatment": after[0]["channels"].get("category_index"),
           "burden_clear_tau": tau, "from_0_80_to_below_0_50_minutes_by_the_law": tau * math.log(0.8 / 0.5),
           "upstream_recovered_at": None if upstream is None else upstream["minute"],
           "f_at_upstream_recovery": None if upstream is None else f(upstream),
           "below_0_50_at": below, "first_category_descent_at": descent,
           "minutes_treatment_to_first_descent": None if descent is None else descent - treatment_minute,
           "minutes_treatment_to_below_0_50": None if below is None else below - treatment_minute,
           "category_at_end": after[-1]["channels"].get("category_index"), "f_at_end": f(after[-1])}
    if upstream is not None:
        start_f = f(upstream)
        out["minutes_upstream_to_below_0_50"] = (None if below is None else max(0, below - upstream["minute"]))
        out["minutes_upstream_to_below_0_50_by_the_law"] = (0.0 if start_f <= 0.50 else tau * math.log(start_f / 0.50))
    return out


# -- legacy beside the mechanistic shadow (P3-176): a comparison, never a calibration -------------------------------------

def legacy_comparison(run: Mapping, witness: str) -> dict:
    """The legacy engine's own mental-state ladder beside one witness, minute by minute, and where they differ.

    The legacy engine carries its own authored timing; this does NOT tune the amendment to reproduce it. It reports the first
    impairment of each, the category sequences, whether each is reversible after treatment, and any contradiction.
    """
    rows = run["witness_rows"].get(witness, [])
    legacy = {sample["minute"]: sample for sample in run["legacy"]}
    shadow = {row["minute"]: row["channels"].get("category_index") for row in rows}
    first_legacy = next((m for m, s in sorted(legacy.items()) if (s["legacy_level"] or 0) >= 1), None)
    first_shadow = next((m for m, level in sorted(shadow.items()) if (level or 0) >= 1), None)
    legacy_sequence, last = [], None
    for minute, sample in sorted(legacy.items()):
        if sample["legacy_level"] is not None and sample["legacy_level"] != last:
            legacy_sequence.append((minute, int(sample["legacy_level"])))
            last = sample["legacy_level"]
    common = sorted(set(shadow) & set(legacy))
    differing = [minute for minute in common if shadow[minute] is not None and legacy[minute]["legacy_level"] is not None
                 and shadow[minute] != legacy[minute]["legacy_level"]]
    contradictions = []
    for minute in common:
        sample, level = legacy[minute], shadow[minute]
        if level is None or sample["legacy_level"] is None:
            continue
        if sample.get("arrested") or sample.get("pulse_present") is False:
            contradictions.append({"minute": minute, "kind": "legacy_arrested_or_pulseless",
                                   "shadow_category": int(level), "legacy_level": sample["legacy_level"]})
    return {"first_impairment": {"legacy": first_legacy, "shadow": first_shadow},
            "legacy_sequence": legacy_sequence, "shadow_sequence": category_sequence(rows),
            "minutes_compared": len(common), "minutes_that_differ": len(differing),
            "shadow_above_legacy": sum(1 for m in differing if shadow[m] > legacy[m]["legacy_level"]),
            "shadow_below_legacy": sum(1 for m in differing if shadow[m] < legacy[m]["legacy_level"]),
            "contradictions": contradictions[:12], "contradiction_minutes": len(contradictions)}


def treatment_minute(run: Mapping) -> int | None:
    """The minute the first ORDER THAT TREATS was given (crystalloid or red cells), or None."""
    for order in run["orders"]:
        if order["executed"] and any(part in (SALINE, BLOOD, BLOOD_MORE) for part in order["parts"]):
            return int(order["minute"])
    return None


def summarise(run: Mapping) -> dict:
    """Everything a reader needs of one run, per witness, without choosing between them."""
    treatment = treatment_minute(run)
    witnesses = {}
    for name in WITNESSES:
        rows = run["witness_rows"].get(name, [])
        profile = run["profile"].get(name)
        failed = [item for item in run["failures"] if item["where"].startswith(f"ensemble:{name}:")]
        witnesses[name] = {
            "minutes": len(rows),
            "order": causal_order(rows, profile) if rows and profile is not None else {},
            "category_sequence": category_sequence(rows),
            "f_peak": max((row["channels"].get("systemic_encephalopathy_burden") or 0.0 for row in rows), default=None),
            "recovery": recovery(rows, profile, treatment) if rows and profile is not None else {"applicable": False},
            "legacy": legacy_comparison(run, name),
            "failures": failed,
        }
    return {"case": run["case"], "scenario": run["scenario"], "treatment_minute": treatment, "orders": run["orders"],
            "triggered_at": run["triggered_at"], "minutes_played": run["encounter_minute"],
            "legacy_arrested": run["legacy_arrested"], "witnesses": witnesses,
            "session_failures": [item for item in run["failures"] if not item["where"].startswith("ensemble:")]}


# -- P3-177: the faculty-only review bundle -------------------------------------------------------------------------------

#: The representative trajectories of the bundle: (case, scenario). Both supported cases, the untreated course, the transient
#: effect of crystalloid alone, a delayed treatment, and the recovery after a severe deterioration. Faculty only; no resident.
BUNDLE = (("gi_bleed_72f", "untreated"), ("gi_bleed_57m", "severe_deterioration"), ("gi_bleed_72f", "delayed_treatment"),
          ("gi_bleed_57m", "recovery_after_severe"))


def write_faculty_bundle(destination: str, *, selections: Sequence = BUNDLE) -> dict:
    """Play the selected trajectories, build each encounter's trace as the store holds it, then write the observer's review
    package (index.md and one page per trace) to ``destination``, an absolute path outside the repository.

    Each page shows the action timeline, the channels (V, pressure, delivery, perfusion, F, collapse burden, category), the
    three witnesses apart (and the session's own committed run beside them), the replay status, the terminal boundary with the
    Amendment-2 state of each witness, and the faculty questions. The legacy mental-state ladder of each run is written to
    ``legacy_beside_shadow.md`` beside it, as a COMPARISON only. Run data: never committed, never shown to a resident."""
    import json
    import runtime_shadow_observer as observer
    import runtime_shadow_store as store
    from pathlib import Path
    target = Path(destination)
    if not target.is_absolute():
        return {"written": False, "why": "the bundle path must be absolute"}
    runs, traces = [], []
    for case, scenario in selections:
        run = run_scenario(case, scenario)
        runs.append((run, summarise(run)))
        # the trace as the store would hold it at the last turn (one per encounter: persisting every one-minute turn of a long
        # series would write hundreds of megabytes of run data for nothing)
        traces.append(json.loads(json.dumps(store.trace_of(run["session"]), default=str)))
    written = observer.write_review_package(traces, target)
    if not written.get("written"):
        return written
    lines = ["# Legacy mental-state ladder BESIDE the Amendment-2 shadow — a comparison, never a calibration", "",
             "The legacy engine keeps its own authored timing and decides the encounter. Nothing here tunes the amendment to "
             "reproduce it. Faculty only.", ""]
    for _run, summary in runs:
        lines += [f"## {summary['case']} · {summary['scenario']}", "",
                  "| witness | first impairment: legacy / shadow | legacy sequence | shadow sequence | minutes that differ | "
                  "shadow above / below legacy |", "|---|---|---|---|---|---|"]
        for name, item in summary["witnesses"].items():
            legacy = item["legacy"]
            lines.append(f"| {name} | {legacy['first_impairment']['legacy']} / {legacy['first_impairment']['shadow']} | "
                         f"{legacy['legacy_sequence']} | {legacy['shadow_sequence']} | {legacy['minutes_that_differ']} of "
                         f"{legacy['minutes_compared']} | {legacy['shadow_above_legacy']} / {legacy['shadow_below_legacy']} |")
        lines.append("")
    (target / "legacy_beside_shadow.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (target / "summaries.json").write_text(json.dumps([summary for _run, summary in runs], default=str, indent=1),
                                           encoding="utf-8")
    return {**written, "files": written["files"] + ["legacy_beside_shadow.md", "summaries.json"]}


# -- P3-181 to P3-183: the exact recovery timeline, and what the fall law does on a COMPLETE trajectory ------------------

def f_target(row: Mapping, profile) -> float | None:
    """The signal F relaxes toward at this minute's state: the delivery-failure ramp of the witness (0 at or above its normal
    bound of relative delivery, 1 at or below its severe bound). It is the F TARGET of the next minute."""
    delivery = row["channels"].get("relative_delivery")
    return None if delivery is None else sc.delivery_failure(delivery, profile)


def impairment_of(row: Mapping) -> float | None:
    """The observable impairment the category is cut from: max(F, an established collapse), over the arrival's own floor
    (0 in both supported GI cases, which arrive ALERT)."""
    burden = row["channels"].get("systemic_encephalopathy_burden")
    if burden is None:
        return None
    return max(float(burden), 1.0 if (row["channels"].get("collapse_state_index") or 0) >= 2 else 0.0)


def recovery_timeline(rows: Sequence, profile, order_minute: int, *, before: int = 3, after: int = 40) -> list:
    """Minute by minute around a treatment: the upstream coordinates, the F target, F, the impairment and the category."""
    out = []
    for row in rows:
        if not order_minute - before <= row["minute"] <= order_minute + after:
            continue
        channels = row["channels"]
        out.append({"minute": row["minute"], "V": channels.get("V"), "relative_perfusion": channels.get("relative_perfusion"),
                    "relative_delivery": channels.get("relative_delivery"), "f_target": f_target(row, profile),
                    "F": channels.get("systemic_encephalopathy_burden"), "impairment": impairment_of(row),
                    "category": channels.get("category_index")})
    return out


def recovery_events(rows: Sequence, profile, order_minute: int) -> dict:
    """The exact ordering of the recovery events of one witness after one treatment (P3-181).

    T_ORDER                  the minute the engine received the order;
    T_EFFECT                 the first minute whose state carries the treatment (the volume channel turns upward);
    T_SIGNAL_BEGINS_TO_FALL  the first minute the F target is below the previous minute's (delivery turned upward and the
                             target is below 1: under the severe bound a rising delivery does not move the target yet);
    T_TARGET_BELOW_F         the first minute the target is below F: the relaxation law starts CLEARING F here;
    T_RECOVERY_REGION_ENTRY  the first minute relative delivery is at or above the witness's normal bound: the target is 0
                             (the design's own "once the signal is gone");
    T_F_PEAK                 the minute of the highest F from the order on;
    T_F_BELOW_0_80 / 0_50    the first minute after the peak that F reads below 0.80 / 0.50;
    T_CATEGORY_IMPROVES      the first minute the observable category is below the one held at the order.
    """
    by = {row["minute"]: row for row in rows}
    after = [row for row in rows if row["minute"] >= order_minute]
    if not after or order_minute not in by:
        return {}
    f = lambda row: row["channels"].get("systemic_encephalopathy_burden")
    v = lambda row: row["channels"].get("V")
    first = lambda items, test: next((row["minute"] for row in items if test(row)), None)
    effect = next((b["minute"] for a, b in zip(after, after[1:]) if v(b) > v(a)), None)
    falls = next((b["minute"] for a, b in zip(after, after[1:])
                  if f_target(b, profile) is not None and f_target(a, profile) is not None
                  and f_target(b, profile) < f_target(a, profile)), None)
    clears = first(after, lambda row: f_target(row, profile) is not None and f_target(row, profile) < f(row))
    entry = first(after, lambda row: (row["channels"].get("relative_delivery") or 0.0) >= profile.delivery_normal)
    peak_row = max(after, key=lambda row: (f(row), -row["minute"]))
    later = [row for row in after if row["minute"] > peak_row["minute"]]
    below_80 = first(later, lambda row: f(row) < 0.80) if f(peak_row) >= 0.80 else None
    below_50 = first(later, lambda row: f(row) < 0.50) if f(peak_row) >= 0.50 else None
    category = by[order_minute]["channels"].get("category_index")
    improves = first(after, lambda row: (row["channels"].get("category_index") or 0) < (category or 0))
    normal = first(after, lambda row: (row["channels"].get("category_index") or 0) == 0) if category else None
    at = lambda minute, read: None if minute is None or minute not in by else read(by[minute])
    return {
        "T_ORDER": order_minute, "T_EFFECT": effect, "T_SIGNAL_BEGINS_TO_FALL": falls, "T_TARGET_BELOW_F": clears,
        "T_RECOVERY_REGION_ENTRY": entry, "T_F_PEAK": peak_row["minute"], "T_F_BELOW_0_80": below_80,
        "T_F_BELOW_0_50": below_50, "T_CATEGORY_IMPROVES": improves, "T_CATEGORY_NORMAL": normal,
        "F_at_order": f(by[order_minute]), "F_peak": f(peak_row), "F_at_entry": at(entry, f),
        "target_at_order": f_target(by[order_minute], profile),
        "relative_delivery_at_order": by[order_minute]["channels"].get("relative_delivery"),
        "category_at_order": category, "category_at_entry": at(entry, lambda row: row["channels"].get("category_index")),
        "minutes_entry_to_below_0_50": None if entry is None or below_50 is None else below_50 - entry,
        "minutes_below_0_80_to_below_0_50": None if below_80 is None or below_50 is None else below_50 - below_80,
        "minutes_order_to_entry": None if entry is None else entry - order_minute,
        "share_of_the_0_80_to_0_50_descent_done_before_entry": (
            None if entry is None or at(entry, f) is None or f(peak_row) < 0.80
            else max(0.0, min(1.0, (0.80 - at(entry, f)) / 0.30))),
    }


def f_course(deliveries: Sequence, profile, start: float, *, clear_tau: float | None = None, law: str = "certified") -> list:
    """F recomputed OFFLINE from a recorded series of relative delivery: what a different fall constant, or a different
    clearing rule, WOULD read on the very same upstream trajectory. Exact, because F feeds nothing back: the physical state
    of a run is identical with and without the amendment (the certified non-interference), so its delivery series is too.

    ``law``: ``certified`` is the amendment's own relaxation (toward the graded target, the rise constant above it and the
    clear constant below); ``gated`` is the WHAT-IF in which F is held while the target is positive and clears only inside
    the recovery region (target 0). Nothing here is installed anywhere: it is analysis, and the certified law is the control.
    """
    from clinical_core import encephalopathy as en
    tau = profile.burden_clear_tau if clear_tau is None else float(clear_tau)
    memory = en.EncephalopathyProfile(burden_rise_tau=profile.burden_rise_tau, burden_clear_tau=tau)
    out, burden = [float(start)], float(start)
    for delivery in list(deliveries)[:-1]:
        target = sc.delivery_failure(delivery, profile)
        if law == "gated" and 0.0 < target < burden:
            pass                                                      # held: the upstream is not in the recovery region yet
        else:
            burden = en.burden_after(burden, target, 1.0, memory)
        out.append(burden)
    return out


def recovery_order_checks(rows: Sequence, profile, order_minute: int) -> dict:
    """P3-184: the order a recovery must keep, read from one witness's own channels. Upstream first (the volume turns, then
    delivery, then the F target), F downstream (F does not fall before its target is below it, and still RISES at the minute
    the treatment takes effect), no instant normalisation (the category gives back one band at a time), and no direct
    treatment -> consciousness edge (F at each minute is exactly the certified relaxation of the previous F toward the
    previous minute's target: nothing else moves it)."""
    events = recovery_events(rows, profile, order_minute)
    after = [row for row in rows if row["minute"] >= order_minute]
    f = lambda row: row["channels"].get("systemic_encephalopathy_burden")
    first_fall = next((b["minute"] for a, b in zip(after, after[1:]) if f(b) < f(a)), None)
    recomputed = f_course([row["channels"].get("relative_delivery") for row in rows], profile, f(rows[0]))
    steps = [(b["channels"].get("category_index") or 0) - (a["channels"].get("category_index") or 0)
             for a, b in zip(after, after[1:])]
    return {
        "upstream_first": (events.get("T_EFFECT") is not None and events.get("T_SIGNAL_BEGINS_TO_FALL") is not None
                           and events["T_ORDER"] < events["T_EFFECT"] <= events["T_SIGNAL_BEGINS_TO_FALL"]),
        "f_falls_only_after_its_target_is_below_it": (first_fall is None or (events.get("T_TARGET_BELOW_F") is not None
                                                                              and first_fall > events["T_TARGET_BELOW_F"])),
        "f_does_not_fall_at_the_minute_the_treatment_takes_effect": (
            events.get("T_EFFECT") is None or first_fall is None or first_fall > events["T_EFFECT"]),
        "category_gives_back_one_band_at_a_time": all(step >= -1 for step in steps),
        "f_is_only_the_relaxation_toward_the_delivery_target": max(
            abs(a - f(row)) for a, row in zip(recomputed, rows)) == 0.0,
        "first_f_fall": first_fall,
    }
