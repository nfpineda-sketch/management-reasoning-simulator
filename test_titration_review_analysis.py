"""P3-438 to P3-440: the BUILDER and SOURCE AUDIT of the norepinephrine titration review set (a tool, never imported by a page; it holds no test).

WHAT IT DOES. It assembles the review set ``NOREPINEPHRINE_TITRATION_V1_FACULTY_REVIEW`` from a source that is ALREADY certified, and proves, scenario by scenario, that what it assembled IS what that source holds:

* every trajectory is the ``per_minute`` series of a GI-hemorrhage probe of the certified titration probes record ``PHASE3_NOREPINEPHRINE_TITRATION_PROBES.json`` (witness CENTER_REFERENCE), taken UNCHANGED:
  nothing is recomputed, tuned or substituted to make a scenario;
* the same series is REGENERATED with the certified harness call (``test_tone_titration_analysis.gi_probe``: the real interpreter, the real engine, the mirror, the registered shadow mapping and the declared reader)
  and must be EQUAL to the stored one, together with the orders the mirror handed over and the rate history written by hand in the harness;
* the rate history each scenario shows (the changes, their minutes and rates) is the one the faculty decision names (FD-TITREV-04) and the one the probe's orders spell out.

It sets NO parameter, tunes nothing, substitutes no witness and adds no physiology. It stores NO other setting of the response (no LOW, no HIGH: FD-TITREV-06), no tone state, no rate history of the writer and no
heart rate or capillary refill. The set is a VERSIONED historical record (provenance, seal, index); ``write_all`` refuses to replace it with other bytes. The review modules are left out of the generating code on purpose:
the one that loads the set holds its digest pin, and a pin cannot be part of what it pins.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import clinical_cases as cc
import faculty_titration_review as ftt
import historical_records as hr
import test_tone_review_analysis as trb
import test_tone_titration_analysis as tta

ROOT = Path(__file__).resolve().parent
SET_PATH = ftt.SET_PATH
GENERATED_ON = "2026-11-19"
DECISIONS = "FD-TITREV-01 to FD-TITREV-13 (the review); FD-TITRATE-01 to FD-TITRATE-13 (the semantics it reviews)"
REVIEW_MODULES = ("faculty_titration_review.py", "faculty_titration_review_ui.py")
CASE_ID = "gi_bleed_57m"
#: The certified probe each scenario is, by the name the titration probes record gives it. TIT-1 is B (5 -> 10), TIT-2 is C (10 -> 4), TIT-3 is D (10 -> stop), TIT-4 is E (5 -> 10 -> 4 -> stop) and TIT-5 is the
#: restart probe (10 -> stop -> 10): every one of them is a script of the certified harness, so no new code and no new physiology make any of them.
PROBES = {"TIT-1": "B_START_INCREASE", "TIT-2": "C_START_DECREASE", "TIT-3": "D_START_STOP", "TIT-4": "E_START_INCREASE_DECREASE_STOP", "TIT-5": "F_START_STOP_RESTART"}
#: What the mirror's outcome of an order is called in the review (the faculty's own words, FD-TITREV-04).
OPERATION_OF_OUTCOME = {"STARTED": "START", "INCREASED": "INCREASE", "DECREASED": "DECREASE", "STOPPED": "STOP", "RESTARTED": "RESTART"}
SHORT = {"TIT-1": "Increase", "TIT-2": "Decrease", "TIT-3": "Stop", "TIT-4": "Sequence", "TIT-5": "Restart"}
#: Written when the scenarios were chosen, before the trajectories were looked at: the minutes of the table next to the chart. Every change and the last minute are in them; two minutes after each change the
#: response can first be seen, and the minutes between are enough to follow the shape without drawing the whole series.
TABLE_MINUTES = {"TIT-1": [0, 2, 4, 10, 12, 14, 18, 25, 32], "TIT-2": [0, 2, 4, 10, 12, 14, 18, 25, 32], "TIT-3": [0, 2, 4, 10, 12, 14, 18, 25, 32], "TIT-4": [0, 2, 4, 10, 12, 18, 20, 25, 27, 32],
                 "TIT-5": [0, 2, 4, 10, 12, 18, 20, 25, 32]}
TITLE_LEAD = "57-year-old man with an upper gastrointestinal bleed"
TITLES = {"TIT-1": f"{TITLE_LEAD}: norepinephrine increased from 5 to 10 mcg/min", "TIT-2": f"{TITLE_LEAD}: norepinephrine reduced from 10 to 4 mcg/min", "TIT-3": f"{TITLE_LEAD}: norepinephrine started and then stopped",
          "TIT-4": f"{TITLE_LEAD}: norepinephrine increased, reduced and then stopped", "TIT-5": f"{TITLE_LEAD}: norepinephrine stopped and later restarted"}
INTERVENTIONS = {
    "TIT-1": "Norepinephrine 5 mcg/min started at minute 2, increased to 10 mcg/min at minute 10 and kept at that rate to the end.",
    "TIT-2": "Norepinephrine 10 mcg/min started at minute 2, reduced to 4 mcg/min at minute 10 and kept at that rate to the end.",
    "TIT-3": "Norepinephrine 10 mcg/min started at minute 2 and stopped at minute 10; it is not given again.",
    "TIT-4": ("Norepinephrine 5 mcg/min started at minute 2, increased to 10 mcg/min at minute 10, reduced to 4 mcg/min at minute 18 and stopped at minute 25; it is not given again."),
    "TIT-5": "Norepinephrine 10 mcg/min started at minute 2, stopped at minute 10 and restarted at 10 mcg/min at minute 18, then kept at that rate to the end.",
}
TAIL = " Nothing else is given or changed; the underlying problem is left untreated."
UNREPRESENTED = ("heart rate and capillary refill are not recomputed for these trajectories and are not stored with them",
                 "the tone state, the support of the infusion, the rate history of the writer, flow, oxygen delivery, oxygen debt, consciousness and collapse state are model state: they are not stored with the items and never drawn",
                 "no other setting of the response (LOW, HIGH) is stored or shown (FD-TITREV-06)")


# -- the generating code and the source -------------------------------------------------------------------------------------------------------------------------------
def _sha(path: Path) -> str:
    return tta.ta._sha(path)


def generating_code() -> dict:
    """What generated the set, by content: the live common core, the certified harness that produced the source, and this builder. Not every application module: the set copies a stored certified series and a test
    regenerates it with the certified call, so what the set depends on is the source and the two harnesses (the review modules are left out because the loader holds the pin)."""
    from clinical_core import amendment_3 as a3
    return {"clinical_core": a3.amended_core_digest_now(), "test_tone_titration_analysis.py": _sha(ROOT / "test_tone_titration_analysis.py"), "test_titration_review_analysis.py": _sha(Path(__file__).resolve()),
            "test_tone_review_analysis.py": _sha(ROOT / "test_tone_review_analysis.py"), "excluded_review_modules": list(REVIEW_MODULES)}


def source() -> dict:
    """The stored certified record, with its file digest and seal."""
    record = json.loads(tta.PROBES_PATH.read_text(encoding="utf-8"))
    return {"path": str(tta.PROBES_PATH.relative_to(ROOT)), "record": record, "file_sha256": _sha(tta.PROBES_PATH), "record_digest": record["record_digest"], "record_id": record["provenance"]["record_id"]}


def _points(rows: list) -> list:
    """The pressure points the page draws: the stored displayed series, unchanged."""
    return [{"minute": int(row["minute"]), "sbp": int(row["sbp"]), "dbp": int(row["dbp"]), "map": int(row["map"])} for row in rows]


def _plan_of(orders: list) -> list:
    """The changes of the rate the mirror handed over, as the review names them: ``(minute, operation, rate after the change)``."""
    return [(int(order["minute"]), OPERATION_OF_OUTCOME[order["outcome"]], 0.0 if OPERATION_OF_OUTCOME[order["outcome"]] == "STOP" else float(order["rate"])) for order in orders]


def _changes(plan: tuple) -> list:
    return [{"n": number, "minute": minute, "operation": operation, "rate_mcg_min": float(rate)} for number, (minute, operation, rate) in enumerate(plan, 1)]


def _rows(changes: list, end: int) -> list:
    """The table of what was done: one row per change of the rate, in the faculty's words, with the rate that runs after it."""
    rows = []
    for index, change in enumerate(changes):
        last = index + 1 == len(changes)
        until = end if last else changes[index + 1]["minute"]
        span = f"to minute {until}" if last else f"until minute {until}"
        rate = ftt.rate_text(change["rate_mcg_min"])
        result = f"Infusion off {span}" if change["operation"] == "STOP" else f"Infusion running at {rate} mcg/min {span}"
        rows.append({"n": change["n"], "minute": change["minute"], "advance": until - change["minute"], "action": ftt.change_text(change), "result": result, "executed": True, "intervention": True})
    return rows


# -- one scenario ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
def scenario(scenario_id: str, src: dict, case: dict, regenerate: bool = True) -> dict:
    """One scenario: the stored series unchanged, with the audit that it IS the certified one (regenerated with the certified call and equal, the orders and the rate history equal the plan)."""
    name = PROBES[scenario_id]
    stored = src["record"]["gi_probes"]["probes"][name]
    plan = ftt.RATE_PLAN[scenario_id]
    common = _points(stored["per_minute"])
    arrival = trb._arrival(case)
    history = tuple(tuple(step) for step in tta.GI_HISTORIES[name])
    expected_history = tuple((minute, float(rate)) for minute, _, rate in plan)
    reads = {row["minute"]: row["displayed"] for row in stored["at_the_reads"]}
    audit = {"source_record": src["path"], "source_record_id": src["record_id"], "source_record_digest": src["record_digest"], "source_file_sha256": src["file_sha256"],
             "taken_from": f"gi_probes.probes[{name}].per_minute, minutes {common[0]['minute']} to {common[-1]['minute']}, unchanged (nothing recomputed to make the scenario)", "probe": name,
             "recomputed_to_check": bool(regenerate), "rate_history_equals_the_faculty_plan": tuple((minute, float(rate)) for minute, rate in history) == expected_history,
             "orders_of_the_probe_equal_the_plan": _plan_of(stored["orders"]) == [(minute, operation, float(rate)) for minute, operation, rate in plan],
             "every_order_was_built": stored["dispositions"] == ["BUILT"] * len(plan) and not stored["gaps"] and not stored["failures"], "the_stored_probe_replays_exactly": bool(stored["replays_exactly"]),
             "the_unmapped_run_is_the_no_order_run": bool(stored["unmapped_run_is_the_no_order_run"]),
             "the_displayed_pressure_at_the_reads_is_the_series": all({key: point[key] for key in ("minute", "sbp", "dbp", "map")} == {**reads[point["minute"]]} for point in common if point["minute"] in reads),
             "the_map_is_the_displayed_rule": all(round((point["sbp"] + 2 * point["dbp"]) / 3) == point["map"] for point in common),
             "first_point_is_the_authored_arrival": (common[0]["sbp"], common[0]["dbp"], common[0]["map"]) == (arrival["sbp"], arrival["dbp"], arrival["map"]),
             "case_id": CASE_ID, "witness": tta.WITNESS}
    if regenerate:
        again = tta.gi_probe(name)
        audit.update({"regenerated_series_equals_the_stored_one": again["per_minute"] == stored["per_minute"], "regenerated_orders_equal_the_stored_ones": again["orders"] == stored["orders"],
                      "regenerated_rate_history_equals_the_stored_one": again["rate_history_as_written"] == stored["rate_history_as_written"], "regenerated_script_equals_the_stored_one": again["script"] == stored["script"]})
    changes = _changes(plan)
    item = {"scenario_id": scenario_id, "short": SHORT[scenario_id], "title": TITLES[scenario_id], "kind": ftt.KIND_CASE, "banner": ftt.CASE_BANNER, "note": ftt.CASE_NOTE,
            "context": f"{case['presentation']} Authored diagnosis: {case['faculty']['diagnosis']}.", "baseline_facts": trb._facts("FR-F", case), "purpose": ftt.QUESTIONS[scenario_id], "arrival": arrival,
            "intervention": INTERVENTIONS[scenario_id] + TAIL, "timeline": _rows(changes, common[-1]["minute"]), "rate_changes": changes, "common": common, "table_minutes": TABLE_MINUTES[scenario_id],
            "stopped": False, "required": True}
    return {"item": item, "audit": audit}


# -- the set --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def build(src: dict | None = None, *, regenerate: bool = True) -> dict:
    src = src or source()
    case = cc.variant_by_id(CASE_ID)
    made = {scenario_id: scenario(scenario_id, src, case, regenerate) for scenario_id in ftt.SCENARIOS}
    items = [made[scenario_id]["item"] for scenario_id in ftt.SCENARIOS]
    problems = [problem for item in items for problem in ftt.item_problems(item)]
    if problems:
        raise ValueError(f"the assembled scenarios do not hold: {problems}")
    failed = {scenario_id: [key for key, value in dict(made[scenario_id]["audit"]).items() if value is False and key != "recomputed_to_check"] for scenario_id in made}
    if any(failed.values()):
        raise ValueError(f"a scenario is not equal to its certified source: {failed}")
    audit = {"witness": tta.WITNESS, "decision_reference": DECISIONS, "sources": {scenario_id: made[scenario_id]["audit"] for scenario_id in ftt.SCENARIOS},
             "selection": {"required": list(ftt.SCENARIOS), "excluded": [], "reason": ("all five deterministic trajectories are already certified: B, C, D, E and the restart probe of the titration probes record; "
                                                                                       "the restart needed no new code and no new physiology"),
                           "not_included": [{"scenario": "START-only", "reason": "it has already undergone human faculty review (FD-TITREV-05)"}]},
             "not_stored_with_the_items": list(UNREPRESENTED), "no_physiology_change": True, "no_parameter_selected": True, "no_witness_substituted": True}
    body = {"record_type": ftt.SET_TYPE, "version": ftt.VERSION, "set_id": ftt.SET_ID, "statement": ftt.STATEMENT,
            "what_it_is": ("Five review scenarios of explicit norepinephrine rate changes in mcg/min in ONE upper gastrointestinal hemorrhage case -- an increase, a decrease, a stop, a sequence of changes and a restart -- with "
                           "the trajectories of the CENTER_REFERENCE setting taken unchanged from the certified titration probes. No comparator, no earlier trajectory, no other setting and no other set are part of the items."),
            "order": list(ftt.SCENARIOS), "items": items, "limitations": [dict(entry) for entry in ftt.LIMITATIONS], "audit": audit}
    body["provenance"] = hr.provenance(record_id=ftt.SET_ID, generating_code=generating_code(), generated_on=GENERATED_ON,
                                       source_data={"source": {"record_digest": src["record_digest"], "file_sha256": src["file_sha256"]}, "scenarios": list(ftt.SCENARIOS), "probes": PROBES,
                                                    "witness": tta.WITNESS, "plan": {key: [list(step) for step in value] for key, value in ftt.RATE_PLAN.items()}})
    return hr.seal(body)


def write_all(path: Path | None = None) -> dict:
    """Write the set. ``historical_records.write`` refuses to replace an existing record with other content: a new representation is a successor record with its own name, never a regeneration in place."""
    target = Path(path or SET_PATH)
    return {str(target): hr.write(target, build())}


def reproduce(src: dict | None = None) -> dict:
    """The CONTENT of the set, regenerated and returned without provenance or seal: what a test compares with the stored set whatever code generated its provenance."""
    record = build(src)
    return {key: value for key, value in record.items() if key not in ("provenance", "record_digest")}


if __name__ == "__main__":
    print(json.dumps(write_all(), indent=2))
