"""P3-393 / P3-397 / P3-398: the analysis harness of the common vascular tone pathway (PHASE2_AMENDMENT_3).

A harness beside the tests, not a runtime module: the Phase-3 isolation guards admit the shadow layer only in the wiring points
and in test code, and nothing the encounter runs imports this file. It builds two VERSIONED records under the historical-record
contract of P3-388 (``historical_records``):

- ``docs/revision/PHASE3_FRF_TONE_V1_CANDIDATE.json``: the FR-F script run in the SHADOW with its norepinephrine order mapped to
  the common vasoconstrictor support, once per witness of the development region and once with the order left unmapped. A
  CANDIDATE for a later human review: it carries no verdict and predeclares none. The certified FR-F run (the live authority
  stops on the order) is untouched and still what the live authority does.
- ``docs/revision/PHASE3_COMMON_TONE_PROBES.json``: the edge-case matrix (the direction predicted BEFORE the run, beside what
  the core did) and the same order in every registered family, through each family's own committed mapping.

Development probes only. No magnitude here is approved, no witness is chosen, nothing is a clinical dose-response, and no
probe is evidence about a patient.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import historical_records as hr

ROOT = Path(__file__).resolve().parent
CANDIDATE_PATH = ROOT / "docs" / "revision" / "PHASE3_FRF_TONE_V1_CANDIDATE.json"
PROBES_PATH = ROOT / "docs" / "revision" / "PHASE3_COMMON_TONE_PROBES.json"
CANDIDATE_VERSION = "FR-F_TONE_V1_CANDIDATE"
PROBES_VERSION = "COMMON_TONE_PROBES_V1"
GENERATED_ON = "2026-11-17"
DECISIONS = "FD-TONE-01 to FD-TONE-12"
WITNESSES = ("LOW", "CENTER_REFERENCE", "HIGH")
NOT_MAPPED = "ORDER_NOT_MAPPED"                 # the same run with the order left as the declared gap it was before
STATEMENT = ("Synthetic development cases run in the shadow. Development probes of a behavioural region: not a clinical validation, "
             "not a calibration, not a dose-response, not runtime authority and not visible to a resident. No witness is chosen.")
#: What decides what these records say (P3-388: a regeneration is compared only under the same generating code). The candidate is captured through the REAL
#: legacy encounter, so any application module can change it -- the parser, the engine, the mirror, the grant the record names: all of them are in the fingerprint,
#: as one digest of every non-test module at the root, beside the common core's own digest and this harness.
GENERATING_PARTS = ("clinical_core", "application_modules", "application_module_count", "test_tone_pathway_analysis.py")

# -- FR-F ------------------------------------------------------------------------------------------------------------------------------
FRF_ID, FRF_CASE, FRF_FAMILY = "FR-F", "gi_bleed_57m", "gi_bleed"
FRF_ORDER = "Start norepinephrine at 10 mcg/min."
#: The certified FR-F run: two minutes of history, then the order with the page's implicit five-minute reassessment, where the live
#: authority stopped. Here the order is followed by two reassessments the certified run never reached, so a response can be read.
FRF_TURNS = ("Reassess in 2 minutes.", f"{FRF_ORDER} Reassess in 5 minutes.", "Reassess in 10 minutes.", "Reassess in 15 minutes.")
FRF_ORDER_MINUTE = 2
FRF_REASSESSMENTS = (7, 17, 32)
FRF_SCRIPT_NOTE = ("the certified run's two-minute history question is two minutes of clinical time here (a reassessment): a question carries no "
                   "physiology, so the common core sees the same thing; the two later reassessments are new, because the certified run stopped at the order")

# -- the probes ------------------------------------------------------------------------------------------------------------------------
PROBE_ORDER_MINUTE = 5
PROBE_MINUTES = 30
PROBE_RATE = 10.0
#: Which edge of the matrix each registered family's first authored case stands for.
FAMILY_ROLE = {"gi_bleed": "hemorrhagic_low_volume", "acs": "cardiogenic_pump_limited", "pulmonary_edema": "pulmonary_congestion",
               "pulmonary_embolism": "obstructive", "asthma": "normal_hemodynamics", "opioid": "normal_hemodynamics"}

UP, DOWN, NONE, TOWARD_ARRIVAL = "UP", "DOWN", "NONE", "TOWARD_ARRIVAL"
#: P3-393: what the physiology the core has should do in each case -- written here BEFORE any run, and compared with the run in the
#: record. ``missing`` is what a clinician would also expect and the core does not represent: a declared limitation, not a prediction.
PREDICTIONS = {
    "hemorrhagic_low_volume": {
        "pressure": UP, "flow": DOWN, "bounded": True, "class": "PRESSURE_SUPPORT_AT_A_FLOW_COST",
        "why": "tone multiplies the flow there is, so pressure rises while the bleed goes on; the afterload lowers output, so delivery falls and "
               "the debt accrues faster; no volume is added, so the pressure keeps falling with the bleed",
        "missing": ("venous return recruited by venoconstriction (the support does not raise preload)",
                    "pressure-dependent bleeding (a higher pressure does not bleed faster here)")},
    "cardiogenic_pump_limited": {
        "pressure": UP, "flow": DOWN, "bounded": True, "class": "PRESSURE_SUPPORT_AT_A_FLOW_COST",
        "why": "the same factor on a smaller flow: fewer mmHg than with a preserved pump, and output falls through the afterload",
        "missing": ("a pump-dependent afterload sensitivity (a failing ventricle loses more output per unit of afterload; the sensitivity is one "
                    "number for every pump)", "coronary perfusion pressure acting on the pump", "the drug's inotropy")},
    "pulmonary_congestion": {
        "pressure": UP, "flow": DOWN, "bounded": True, "class": "HARM_OR_NON_BENEFIT",
        "why": "a patient who is not hypotensive gains pressure they do not need and loses flow",
        "missing": ("afterload-driven lung water (lung water is not read from tone)",
                    "the factor is on the patient's own arrival pressure, so the same order buys MORE mmHg at a higher arrival pressure")},
    "obstructive": {
        "pressure": UP, "flow": DOWN, "bounded": True, "class": "PRESSURE_SUPPORT_AT_A_FLOW_COST",
        "why": "as with any reduced forward flow: the factor is the tone's, the flow sets what it multiplies",
        "missing": ("right-ventricular coronary perfusion",)},
    "normal_hemodynamics": {
        "pressure": UP, "flow": DOWN, "bounded": True, "class": "HARM_OR_NON_BENEFIT",
        "why": "pressure above the patient's own arrival and less flow: no benefit",
        "missing": ()},
    "distributive_like_low_tone": {
        "pressure": UP, "flow": TOWARD_ARRIVAL, "bounded": True, "class": "RESTORES_TOWARD_ARRIVAL",
        "why": "a burden lowers the tone target and the support raises it: the two factors multiply, so pressure and flow both move back toward "
               "arrival and flow stays at or above it",
        "missing": ("no authored distributive case exists: the vasodilatory reader is SYNTHETIC_ONLY and the burden here is a scripted probe",)},
    "no_pulse": {
        "pressure": NONE, "flow": NONE, "bounded": True, "class": "NO_EFFECT",
        "why": "hard no-pulse semantics: without a pulse there is no pressure, output or delivery whatever the tone",
        "missing": ()},
    "empty_preload_no_flow": {
        "pressure": NONE, "flow": NONE, "bounded": True, "class": "NO_EFFECT",
        "why": "pressure is output x tone: with no forward flow no tone makes a pressure",
        "missing": ()},
    "already_high_tone": {
        "pressure": UP, "flow": DOWN, "bounded": True, "class": "DIMINISHING_RETURNS",
        "why": "the support saturates: each further mcg/min adds less tone, the tone never reaches 1 + k, and delivery falls further",
        "missing": ("ischaemia from excessive vasoconstriction beyond the loss of flow",
                    "a patient who ARRIVES vasoconstricted is not nearer the ceiling: arrival is the scale (tone 1), so only the exogenous support saturates")},
}


# -- shared -------------------------------------------------------------------------------------------------------------------------

def _r(value, places: int = 9):
    return None if value is None else round(float(value), places)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def application_modules() -> dict:
    """Every non-test module at the root of the repository, by content: what an encounter, its mirror and the shadow layer execute."""
    return {path.name: _sha(path) for path in sorted(ROOT.glob("*.py")) if not path.name.startswith("test_") and path.name != "conftest.py"}


def generating_code() -> dict:
    """What generated these records, by content: the live common core, every application module and this harness."""
    from clinical_core import amendment_3 as a3
    modules = application_modules()
    return {"clinical_core": a3.amended_core_digest_now(), "application_modules": hr.digest_of(modules), "application_module_count": len(modules),
            "test_tone_pathway_analysis.py": _sha(ROOT / "test_tone_pathway_analysis.py")}


def order_event(minute: int, *, rate=PROBE_RATE, units="mcg/min", operation="start", order_id: str | None = None):
    """A norepinephrine order as the engine's mirror hands it to a shadow adapter (a development probe: no encounter ran it)."""
    import runtime_shadow as rs
    action = {"type": "norepinephrine", "rate": rate, "units": units, "operation": operation}
    return rs.MirroredAction(order_id or f"probe-m{int(minute):03d}-norepinephrine", int(minute), "norepinephrine", action, {}, 0.21)


def row_of(state, reading) -> dict:
    d = reading.to_dict()
    return {"minute": int(state.minute), "support": _r(state.aux.vasoconstrictor_support), "T": _r(state.T), "V": _r(state.V), "P": _r(state.P),
            "hb": _r(state.hb), "L": _r(state.L), "D": _r(state.D), "output_rel": _r(d["output_rel"]), "pressure_rel": _r(d["pressure_rel"]),
            "delivery_rel": _r(d["delivery_rel"]), "sbp": _r(d["sbp"]), "dbp": _r(d["dbp"]), "map": _r(d["map"]), "pulse_present": d["pulse_present"]}


def displayed(row: dict) -> dict:
    """The pressure a page would show at a minute: whole mmHg, MAP by the screen's convention on the displayed values."""
    sbp, dbp = round(row["sbp"]), round(row["dbp"])
    return {"minute": row["minute"], "sbp": int(sbp), "dbp": int(dbp), "map": int(round((sbp + 2 * dbp) / 3))}


def shadow_run(family: str, case_id: str, witness: str | None, mirrored, minutes, *, base=None, state=None, mapping_state=None, scenario_id=None) -> dict:
    """One shadow run through the REAL adapter and runner: the family's mapping (``base``, or the registered adapter), with the common
    vasoconstrictor reader declared when a witness is named. ``minutes`` is the sequence of turns the run is advanced through."""
    import runtime_shadow as rs
    import runtime_shadow_families as fam
    import runtime_tone_support as ts
    from clinical_core import integration
    adapter = base if base is not None else fam.adapter_for(family)
    if witness is not None:
        adapter = ts.with_tone_support(adapter, witness)
    runner = fam.ShadowPhysiologyRunner.open(family, case_id, state=state, adapter=adapter, scenario_id=scenario_id)
    runner.mirror(list(mirrored))
    turns = [int(minute) for minute in ((minutes,) if isinstance(minutes, int) else minutes)]
    advanced = [bool(runner.advance(minute, state=mapping_state)) for minute in turns]
    last = runner.minutes_done
    trajectory = integration.run(runner.anchors, runner.contributors(), last, runner.profile)
    readings = trajectory.derived()
    replay = fam.replay_from_runner(runner)
    return {"adapter": adapter, "runner": runner, "trajectory": trajectory,
            "rows": [row_of(state, readings[index]) for index, state in enumerate(trajectory.states)],
            "advanced": advanced, "minutes_done": last,
            "same_states_as_the_runner": tuple(rs._digest_of(item) for item in trajectory.states[1:]) == tuple(runner.digests()),
            "replay_equal": [item["state_digest"] for item in replay["results"][1:]] == list(runner.digests()),
            "gaps": [dict(gap) for gap in runner.gaps],
            "failures": [{"where": item.where, "exception": item.exception} for item in runner.failures],
            "dispositions": fam.action_dispositions(adapter, runner.mirrored, runner.mapping_state),
            "snapshot_id": runner.snapshot_.id, "adapter_version": adapter.version,
            "profile_gain": runner.profile.vasoconstrictor_support_to_tone_gain}


def untouched(reference: list, rows: list) -> dict:
    """The state the support must not move, minute by minute against the same run without it."""
    return {name: all(a[name] == b[name] for a, b in zip(reference, rows)) for name in ("V", "P", "hb", "L")}


def first_difference(reference: list, rows: list, name: str):
    return next((b["minute"] for a, b in zip(reference, rows) if a[name] != b[name]), None)


def causal_facts(reference: list, rows: list, order_minute: int, gain: float) -> dict:
    """What the order caused and when, read from the run and the same run without the mapping."""
    supported = [row for row in rows if (row["support"] or 0.0) > 0.0]
    peak = max(rows, key=lambda row: row["T"])
    return {"order_minute": order_minute,
            "first_minute_with_support": supported[0]["minute"] if supported else None,
            "first_minute_tone_differs": first_difference(reference, rows, "T"),
            "first_minute_pressure_differs": first_difference(reference, rows, "pressure_rel"),
            "identical_through_the_minute_after_the_order": all(a["pressure_rel"] == b["pressure_rel"] and a["T"] == b["T"]
                                                                for a, b in zip(reference[:order_minute + 2], rows[:order_minute + 2])),
            "untouched_state": untouched(reference, rows),
            "largest_tone": peak["T"], "tone_ceiling": _r(1.0 + gain), "tone_below_its_ceiling": peak["T"] < 1.0 + gain,
            "pressure_never_below_the_unmapped_run": all(b["pressure_rel"] >= a["pressure_rel"] for a, b in zip(reference, rows)),
            "output_never_above_the_unmapped_run": all(b["output_rel"] <= a["output_rel"] for a, b in zip(reference, rows)),
            "delivery_never_above_the_unmapped_run": all(b["delivery_rel"] <= a["delivery_rel"] for a, b in zip(reference, rows)),
            "debt_never_below_the_unmapped_run": all(b["D"] >= a["D"] for a, b in zip(reference, rows))}


def observed(reference: list, rows: list, minute: int) -> dict:
    a, b = reference[minute], rows[minute]
    return {"minute": minute, "map_without": a["map"], "map_with": b["map"], "map_gain_mmhg": _r(b["map"] - a["map"], 6),
            "pressure_ratio": _r(b["pressure_rel"] / a["pressure_rel"], 6) if a["pressure_rel"] else None,
            "output_ratio": _r(b["output_rel"] / a["output_rel"], 6) if a["output_rel"] else None,
            "delivery_ratio": _r(b["delivery_rel"] / a["delivery_rel"], 6) if a["delivery_rel"] else None}


def direction(before, after, tolerance: float = 1e-9) -> str:
    if before is None or after is None:
        return NONE
    return UP if after > before + tolerance else DOWN if after < before - tolerance else NONE


# -- P3-397: the FR-F candidate ---------------------------------------------------------------------------------------------------------

def capture_frf() -> dict:
    """The FR-F script through the REAL legacy encounter with the shadow mirror on: the arrival the shadow maps and the orders the engine
    executed, exactly as its mirror hands them over. The legacy engine's own pressure is not read: it has a vasopressor rule of its own."""
    import pilot_acceptance as acceptance
    import runtime_shadow as rs
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(FRF_CASE)
        arrival = deepcopy(encounter.state)
        turns = []
        for text in FRF_TURNS:
            entry = encounter.order(text)
            turns.append({"text": text, "from_minute": int(entry["decision_time_min"]), "to_minute": int(entry["response_time_min"]),
                          "executed": bool(entry["executed"])})
        runner = encounter.shadow.runner
        return {"arrival": arrival, "mirrored": tuple(runner.mirrored), "mapping_state": deepcopy(runner.mapping_state), "turns": turns}


def frf_base_adapter():
    """The GI mapping on the ratified pressure snapshot the live development authority runs (pressure only): the hemodynamics a later
    review would be looking at. A development adapter, never registered."""
    import runtime_pressure_snapshot as ps
    import runtime_shadow_families as fam
    return fam.GiHaemorrhageAdapter.configured(ps.configuration_for({ps.SNAPSHOT_FLAG: ps.SNAPSHOT_ID}))


def frf_runs(captured: dict | None = None) -> dict:
    captured = captured or capture_frf()
    turns = (FRF_ORDER_MINUTE,) + FRF_REASSESSMENTS
    return {name: shadow_run(FRF_FAMILY, FRF_CASE, None if name == NOT_MAPPED else name, captured["mirrored"], turns, base=frf_base_adapter(),
                             state=captured["arrival"], mapping_state=captured["mapping_state"], scenario_id=f"{CANDIDATE_VERSION}::{name}")
            for name in (NOT_MAPPED,) + WITNESSES}


def _frf_checks(run: dict, reference: dict, order_minute: int) -> dict:
    """The four things the migration had to show, each read from the run. A check is a fact about the run, never a clinical verdict."""
    facts = causal_facts(reference["rows"], run["rows"], order_minute, run["profile_gain"])
    order = next(item for item in run["dispositions"] if item["kind"] == "norepinephrine")
    reassessed = [run["rows"][minute] for minute in FRF_REASSESSMENTS]
    return {
        "order_accepted": order["disposition"] == "BUILT" and order["effective_minute"] == order_minute + 1 and not run["gaps"] and not run["failures"],
        "tone_changes": facts["first_minute_tone_differs"] is not None and facts["largest_tone"] > 1.0,
        "response_begins_causally": (facts["first_minute_with_support"] == order_minute + 1 and facts["first_minute_tone_differs"] == order_minute + 2
                                     and facts["first_minute_pressure_differs"] == order_minute + 2
                                     and facts["identical_through_the_minute_after_the_order"]),
        "reassessment_possible": all(run["advanced"]) and run["minutes_done"] == FRF_REASSESSMENTS[-1]
                                 and all(row["pulse_present"] and row["sbp"] is not None for row in reassessed),
        "no_volume_and_no_pump_created": all(facts["untouched_state"].values()),
        "bounded_by_its_own_form": facts["tone_below_its_ceiling"],
        "replays_exactly": run["replay_equal"] and run["same_states_as_the_runner"],
        "facts": facts}


def build_candidate(runs: dict | None = None, captured: dict | None = None) -> dict:
    import runtime_pressure_grant as grants
    import runtime_pressure_snapshot as ps
    import runtime_tone_support as ts
    from clinical_core import vascular_support as vs
    captured = captured or capture_frf()
    runs = runs or frf_runs(captured)
    reference = runs[NOT_MAPPED]
    order = next(event for event in captured["mirrored"] if event.kind == "norepinephrine")
    order_minute = int(order.minute)
    witnesses = {}
    for name in WITNESSES:
        run = runs[name]
        witnesses[name] = {
            "witness": vs.witness(name), "adapter_version": run["adapter_version"], "parameter_snapshot": run["snapshot_id"],
            "checks": _frf_checks(run, reference, order_minute),
            "displayed_pressure": [displayed(run["rows"][minute]) for minute in (order_minute,) + FRF_REASSESSMENTS],
            "caused_at_each_reassessment": [observed(reference["rows"], run["rows"], minute) for minute in FRF_REASSESSMENTS],
            "per_minute": run["rows"]}
    body = {
        "record_type": "FRF_TONE_DEVELOPMENT_CANDIDATE", "version": CANDIDATE_VERSION, "status": "CANDIDATE_FOR_LATER_HUMAN_REVIEW",
        "evidence_class": "MODEL_ANALYSIS", "statement": STATEMENT, "decision_reference": DECISIONS,
        "faculty_verdict": None, "predeclared_verdict": None, "chosen_witness": None,
        "what_it_is": "FR-F with its norepinephrine order mapped in the SHADOW to the common vasoconstrictor support of PHASE2_AMENDMENT_3, on the ratified GI "
                      "pressure snapshot, once per witness of the development region. What a later human review would look at; it decides nothing.",
        "scenario": {"scenario_id": FRF_ID, "case_id": FRF_CASE, "family": FRF_FAMILY, "order": FRF_ORDER, "order_minute": order_minute,
                     "turns": captured["turns"], "reassessment_minutes": list(FRF_REASSESSMENTS), "script_note": FRF_SCRIPT_NOTE,
                     "order_as_mirrored": {key: order.action.get(key) for key in ("type", "rate", "units", "operation")}},
        "hemodynamics": {"pressure_snapshot": ps.SNAPSHOT_ID, "note": "the snapshot the live development authority runs; it is read, never changed"},
        "mapping": ts.summary(),
        "order_not_mapped": {"what": "the same run with the order left as the declared gap it was before this stage: what the bleed does to the pressure "
                                     "with no vasopressor in the core",
                             "adapter_version": reference["adapter_version"], "parameter_snapshot": reference["snapshot_id"], "gaps": reference["gaps"],
                             "displayed_pressure": [displayed(reference["rows"][minute]) for minute in (order_minute,) + FRF_REASSESSMENTS],
                             "per_minute": reference["rows"]},
        "witnesses": witnesses,
        "not_shown": {"heart_rate_and_capillary_refill": "not part of the candidate: the common core's are not authoritative, and the legacy engine's were "
                                                         "computed under its own vasopressor rule, which this pathway does not use",
                      "comparator": "none: the legacy engine's pressure under norepinephrine is a fixed bonus in mmHg, the form this pathway forbids"},
        "the_certified_run_is_untouched": {
            "what": "FR-F as certified: the live GI pressure development authority stops on the order (HALTED_BY_UNSUPPORTED_ACTION)",
            "still_true_of_the_live_authority": "norepinephrine is not a supported authority action and the live grant names it as not granted",
            "live_grant": grants.LIVE_GRANT_ID,
            "preserved_records": ["docs/revision/PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json", "docs/revision/PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json"]},
        "for_the_later_review": "how this is put before a human reviewer (which witness or witnesses, blinded or not, with which questions) is a faculty "
                                "decision that is pending; no review set and no screen were built",
        "limitations": [
            "the three witnesses are probes of a region whose every magnitude has a confidence below 0.80: none is a calibration",
            "the support adds no volume and recruits no venous return: in a bleeding patient the pressure it buys keeps falling with the bleed",
            "output and delivery never rise with tone here: the afterload is the only path from tone to flow",
            "only the encounter's first norepinephrine order is mapped, and only as a start at a fixed rate in mcg/min; an adjustment, a stop, a weight-based dose "
            "and any later start are declared gaps",
            "the consciousness reading is taken from the pressure: with the support it reads better while delivery is lower (see the probes record)",
            "shadow only: nothing here is authoritative, shown to a resident or scored",
        ],
    }
    body["provenance"] = hr.provenance(record_id=CANDIDATE_VERSION, generating_code=generating_code(), generated_on=GENERATED_ON,
                                       source_snapshot_id=ps.SNAPSHOT_ID, grant_id=None,
                                       source_data={"turns": captured["turns"], "order": dict(body["scenario"]["order_as_mirrored"]),
                                                    "witnesses": {name: vs.witness(name) for name in WITNESSES}})
    return hr.seal(body)


# -- P3-398: the same order in every registered family ------------------------------------------------------------------------------

def family_probe(family: str, case_id: str) -> dict:
    events = (order_event(PROBE_ORDER_MINUTE),)
    reference = shadow_run(family, case_id, None, events, PROBE_MINUTES, scenario_id=f"{PROBES_VERSION}::{family}::{NOT_MAPPED}")
    out = {"family": family, "case_id": case_id, "role": FAMILY_ROLE[family], "order_minute": PROBE_ORDER_MINUTE,
           "mapping": "the family's own registered (committed) shadow mapping, plus the declared reader: the SAME order mapping in every family",
           "without_the_mapping": {"gaps": reference["gaps"], "at_the_order": reference["rows"][PROBE_ORDER_MINUTE], "at_the_end": reference["rows"][PROBE_MINUTES]},
           "witnesses": {}}
    for name in WITNESSES:
        run = shadow_run(family, case_id, name, events, PROBE_MINUTES, scenario_id=f"{PROBES_VERSION}::{family}::{name}")
        facts = causal_facts(reference["rows"], run["rows"], PROBE_ORDER_MINUTE, run["profile_gain"])
        out["witnesses"][name] = {
            "built": [item["disposition"] for item in run["dispositions"] if item["kind"] == "norepinephrine"] == ["BUILT"],
            "gaps": run["gaps"], "failures": run["failures"], "replays_exactly": run["replay_equal"] and run["same_states_as_the_runner"],
            "facts": facts, "observed": [observed(reference["rows"], run["rows"], minute) for minute in (PROBE_ORDER_MINUTE + 2, PROBE_ORDER_MINUTE + 5, PROBE_MINUTES)]}
    return out


def family_probes() -> dict:
    import runtime_shadow_families as fam
    return {family: family_probe(family, adapter.cases[0]) for family, adapter in fam.ADAPTERS.items()}


# -- P3-393: the states no authored case supplies (the common core alone) -----------------------------------------------------------

def _gi_core(case: str = "gi_bleed_72f"):
    from clinical_core import blood_anchors as ba
    anchors, profile, values = ba.setup(case)
    return anchors, profile, ba.contributors(case, "untreated", values)


def _infusion(name: str, start: int, rate: float = PROBE_RATE):
    from clinical_core import vascular_support as vs
    point = vs.witness(name)
    return vs.Norepinephrine("probe-norepinephrine", start, rate, half_effect_rate_mcg_min=point["half_effect_rate_mcg_min"],
                             onset_tau_min=point["onset_tau_min"], offset_tau_min=point["offset_tau_min"])


def _declared(profile, name: str):
    from clinical_core import vascular_support as vs
    return dataclasses.replace(profile, vasoconstrictor_support_to_tone_gain=vs.witness(name)["tone_gain"])


def core_volume_dependence(name: str = "CENTER_REFERENCE") -> dict:
    """The same order given early and late in an untreated bleed: the factor on the pressure is the tone's, the mmHg are the flow's."""
    from clinical_core import integration as ig
    anchors, profile, items = _gi_core()
    declared = _declared(profile, name)
    out = []
    for start in (5, 60, 110):
        end = start + 15
        plain = ig.run(anchors, items, end, profile)
        infused = ig.run(anchors, items + (_infusion(name, start),), end, declared)
        a, b = plain.derived()[end], infused.derived()[end]
        out.append({"order_minute": start, "read_at": end, "V_before": _r(plain.states[start].V), "output_rel_without": _r(a.output_rel),
                    "map_without": _r(a.map), "map_with": _r(b.map), "map_gain_mmhg": _r(b.map - a.map, 6), "pressure_ratio": _r(b.pressure_rel / a.pressure_rel, 6),
                    "volume_identical": plain.states[end].V == infused.states[end].V})
    return {"witness": name, "case": "gi_bleed_72f, untreated", "orders": out,
            "fewer_mmhg_as_the_volume_falls": all(x["map_gain_mmhg"] > y["map_gain_mmhg"] > 0.0 for x, y in zip(out, out[1:]))}


def core_static_dependence(name: str = "CENTER_REFERENCE") -> dict:
    """One tone, applied to arrival states that differ only in volume or pump: what the same tone buys in each."""
    from clinical_core import derived as dv
    from clinical_core import vascular_support as vs
    anchors, profile, _items = _gi_core()
    declared = _declared(profile, name)
    arrival = dv.arrival_state(anchors, declared)
    filling = dv.arrival_filling(anchors, declared)
    tone = vs.tone_factor(1.0, vs.witness(name)["tone_gain"])
    states = {"replete": arrival, "volume_depleted": dataclasses.replace(arrival, V=-0.4 * filling),
              "very_volume_depleted": dataclasses.replace(arrival, V=-0.8 * filling), "failing_pump": dataclasses.replace(arrival, P=0.5),
              "depleted_and_failing_pump": dataclasses.replace(arrival, V=-0.4 * filling, P=0.5)}
    rows = {}
    for label, state in states.items():
        plain, raised = dv.derive(dataclasses.replace(state, T=1.0), anchors, declared), dv.derive(dataclasses.replace(state, T=tone), anchors, declared)
        rows[label] = {"map_at_arrival_tone": _r(plain.map), "map_at_raised_tone": _r(raised.map), "map_gain_mmhg": _r(raised.map - plain.map, 6),
                       "pressure_ratio": _r(raised.pressure_rel / plain.pressure_rel, 9), "output_ratio": _r(raised.output_rel / plain.output_rel, 9)}
    ratios = [row["output_ratio"] for row in rows.values()]
    return {"witness": name, "tone": _r(tone), "states": rows,
            "the_output_cost_of_tone_is_the_same_fraction_in_every_state": max(ratios) - min(ratios) < 1e-9}


def core_no_flow(name: str = "CENTER_REFERENCE") -> dict:
    from clinical_core import derived as dv
    from clinical_core import integration as ig
    from clinical_core.state import RhythmState
    anchors, profile, items = _gi_core()
    declared = _declared(profile, name)
    state = ig.run(anchors, items + (_infusion(name, 10),), 30, declared).states[30]
    pulseless = []
    for label, rhythm in (("asystole", RhythmState.asystole()), ("pulseless_electrical_activity", RhythmState.pea(90.0))):
        for tone in (state.T, 2.5):
            d = dv.derive(dataclasses.replace(state, R=rhythm, T=tone, terminal_since=state.minute), anchors, declared)
            pulseless.append({"rhythm": label, "tone": _r(tone), "support": _r(state.aux.vasoconstrictor_support), "pulse_present": d.pulse_present,
                              "sbp": d.sbp, "map": d.map, "output_rel": d.output_rel, "pressure_rel": d.pressure_rel, "delivery_rel": d.delivery_rel})
    empty = dataclasses.replace(state, V=-dv.arrival_filling(anchors, declared) - 50.0)
    no_preload = []
    for tone in (1.0, state.T, 2.5):
        output, pressure, _spo2, delivery = dv._perfusion(dataclasses.replace(empty, T=tone), anchors, declared)
        no_preload.append({"tone": _r(tone), "output_rel": output, "pressure_rel": pressure, "delivery_rel": delivery})
    return {"witness": name, "no_pulse": pulseless, "empty_preload": no_preload,
            "no_pulse_has_no_circulation": all(item["pulse_present"] is False and item["sbp"] is None and item["map"] is None and item["output_rel"] == 0.0
                                               and item["pressure_rel"] == 0.0 and item["delivery_rel"] == 0.0 for item in pulseless),
            "no_flow_has_no_pressure": all(item["output_rel"] == 0.0 and item["pressure_rel"] == 0.0 and item["delivery_rel"] == 0.0 for item in no_preload)}


def core_saturation(name: str = "CENTER_REFERENCE") -> dict:
    """Already-high tone: more of the drug adds less, the tone never reaches its ceiling, and a gain that could reach the guard is refused."""
    from clinical_core import integration as ig
    from clinical_core.state import Channel, CoreInvariantError
    anchors, profile, items = _gi_core()
    declared = _declared(profile, name)
    gain = declared.vasoconstrictor_support_to_tone_gain
    plain = ig.run(anchors, items, 40, profile)
    rows = []
    from clinical_core import vascular_support as vs
    half = vs.witness(name)["half_effect_rate_mcg_min"]
    largest = (vs.SUPPORT_LIMIT - 1.0) * half                       # the largest rate the writer represents: past it the order is refused, never run
    try:
        _infusion(name, 10, vs.SUPPORT_LIMIT * half)
        over_the_limit_refused = False
    except CoreInvariantError:
        over_the_limit_refused = True
    for rate in (5.0, 10.0, 20.0, 40.0, 80.0, largest):
        run = ig.run(anchors, items + (_infusion(name, 10, rate),), 40, declared)
        d = run.derived()[40]
        rows.append({"rate_mcg_min": rate, "support": _r(run.states[40].aux.vasoconstrictor_support, 6), "T": _r(run.states[40].T),
                     "map": _r(d.map), "output_rel": _r(d.output_rel), "delivery_rel": _r(d.delivery_rel), "D": _r(run.states[40].D)})
    # Per unit of rate, not per doubling: a saturating (Emax) effect is symmetric in the logarithm of the rate around its half-effect rate, so two doublings
    # that straddle it add the same tone. What saturation means is that each further mcg/min adds less.
    per_unit = [(b["T"] - a["T"]) / (b["rate_mcg_min"] - a["rate_mcg_min"]) for a, b in zip(rows, rows[1:5])]
    upper = ig.CHANNEL_BOUNDS[Channel.T][1]
    refused = {}
    for tried in (upper - 1.0, upper, 10.0):
        try:
            ig.run(anchors, items, 1, dataclasses.replace(profile, vasoconstrictor_support_to_tone_gain=tried))
            refused[str(tried)] = False
        except CoreInvariantError:
            refused[str(tried)] = True
    return {"witness": name, "tone_ceiling": _r(1.0 + gain), "tone_guard_upper": upper, "without": {"map": _r(plain.derived()[40].map), "D": _r(plain.states[40].D)},
            "by_rate": rows, "each_further_unit_of_rate_adds_less_tone": all(x > y > 0.0 for x, y in zip(per_unit, per_unit[1:])),
            "tone_never_reaches_its_ceiling": all(row["T"] < 1.0 + gain for row in rows),
            "delivery_falls_as_the_rate_rises": all(x["delivery_rel"] > y["delivery_rel"] for x, y in zip(rows, rows[1:5])),
            "debt_rises_with_the_rate": all(x["D"] < y["D"] for x, y in zip(rows, rows[1:5])),
            "a_gain_that_could_reach_the_guard_is_refused_before_execution": refused,
            "largest_rate_the_writer_represents_mcg_min": largest, "a_rate_past_it_is_refused_at_the_order": over_the_limit_refused}


def core_distributive(name: str = "CENTER_REFERENCE") -> dict:
    """A scripted vasodilatory burden (SYNTHETIC_ONLY, P2W-1) lowers the tone; the support then raises it: two independent factors of one target."""
    from clinical_core import distributive_tone as dt
    from clinical_core import integration as ig
    anchors = dt.probe_anchors()
    profile = dt.reader(dt.base_profile())
    declared = _declared(profile, name)
    burden = (dt.SyntheticVasodilation("probe-burden", dt.BURDEN_STEP, 0, 4),)          # +0.25 a minute over (0, 4]: a burden of 1
    plain = ig.run(anchors, burden, 40, declared)
    infused = ig.run(anchors, burden + (_infusion(name, 10),), 40, declared)
    a, b = plain.derived(), infused.derived()
    row = lambda run, d, minute: {"minute": minute, "burden": _r(run.states[minute].aux.vasodilatory_burden), "support": _r(run.states[minute].aux.vasoconstrictor_support, 6),
                                  "T": _r(run.states[minute].T), "map": _r(d[minute].map), "pressure_rel": _r(d[minute].pressure_rel),
                                  "output_rel": _r(d[minute].output_rel), "delivery_rel": _r(d[minute].delivery_rel)}
    return {"witness": name, "probe": "SYNTHETIC_ONLY: clinical_core.distributive_tone probe anchors and scripted burden; no authored case and no family adapter",
            "arrival": row(plain, a, 0), "low_tone_before_the_order": row(plain, a, 10), "low_tone_without_support": row(plain, a, 40), "low_tone_with_support": row(infused, b, 40),
            "tone_is_the_product_of_both_factors": abs(infused.states[40].T / plain.states[40].T - (1.0 + declared.vasoconstrictor_support_to_tone_gain
                                                                                                    * infused.states[39].aux.vasoconstrictor_support
                                                                                                    / (1.0 + infused.states[39].aux.vasoconstrictor_support))) < 1e-9,
            "pressure_moves_toward_arrival": a[40].pressure_rel < b[40].pressure_rel <= 1.0 + 1e-9 or a[40].pressure_rel < b[40].pressure_rel,
            "flow_moves_toward_arrival_and_stays_at_or_above_it": a[40].output_rel > b[40].output_rel >= 1.0}


def core_stopped_infusion(name: str = "LOW") -> dict:
    """An infusion that is stopped, and two that overlap: the state is EXACTLY the sum of what its writers hold at every minute, and exactly 0 once they
    have decayed (adversarial review, finding 1: before the writers' grid a residue of either sign was left, and a negative one refused the run)."""
    from clinical_core import integration as ig
    from clinical_core import vascular_support as vs
    anchors, profile, items = _gi_core()
    declared = _declared(profile, name)
    point = vs.witness(name)
    make = lambda identity, start, rate, stop: vs.Norepinephrine(identity, start, rate, half_effect_rate_mcg_min=point["half_effect_rate_mcg_min"],
                                                                 onset_tau_min=point["onset_tau_min"], offset_tau_min=point["offset_tau_min"], stop_minute=stop)
    cases = {"one_stopped": (make("a", 0, 3.0, 5),), "two_overlapping_and_stopped": (make("a", 0, 10.0, 12), make("b", 4, 2.5, 30))}
    out = {}
    for label, writers in cases.items():
        run = ig.run(anchors, items + writers, 240, declared)
        held = [run.states[minute].aux.vasoconstrictor_support for minute in range(1, 241)]
        out[label] = {"minutes": 240, "ran_to_the_end": True, "peak_support": _r(max(held)),
                      "state_is_exactly_the_sum_of_its_writers_every_minute": all(held[minute - 1] == sum(w.support_at(minute) for w in writers) for minute in range(1, 241)),
                      "first_minute_at_exactly_zero_after_the_last_stop": next(minute for minute in range(max(w.stop_minute for w in writers), 241) if held[minute - 1] == 0.0),
                      "never_negative": min(held) >= 0.0, "tone_back_at_arrival_at_the_end": run.states[240].T == 1.0}
    return {"witness": name, "resolution": vs.SUPPORT_QUANTUM, "cases": out}


def core_consciousness_reading(name: str = "CENTER_REFERENCE") -> dict:
    """What the consciousness readings do under the support. They are taken from the PRESSURE: the direct pressure ladder of the committed profiles, and --
    where it is declared -- the soft-collapse conjunction of PHASE2_AMENDMENT_2, min(perfusion failure, delivery failure). The support raises the pressure
    while delivery falls, so both read BETTER with it. Shown, not judged: it is a limitation for the faculty, and the reason the development mapping
    refuses an Amendment-2 witness."""
    from clinical_core import integration as ig
    from clinical_core import systemic_consciousness as sc
    anchors, profile, items = _gi_core()
    declared = _declared(profile, name)
    plain = ig.run(anchors, items, 150, profile)
    infused = ig.run(anchors, items + (_infusion(name, 10),), 150, declared)
    a, b = plain.derived(), infused.derived()
    differs = [minute for minute in range(151) if a[minute].consciousness_level != b[minute].consciousness_level and a[minute].pulse_present and b[minute].pulse_present]
    ladder = {"minutes_the_level_differs": len(differs), "first": None}
    if differs:
        m = differs[0]
        ladder["first"] = {"minute": m, "level_without": a[m].consciousness_level, "level_with": b[m].consciousness_level,
                           "delivery_rel_without": _r(a[m].delivery_rel), "delivery_rel_with": _r(b[m].delivery_rel), "map_without": _r(a[m].map), "map_with": _r(b[m].map)}
    ladder["the_level_is_never_worse_with_support_while_both_have_a_pulse"] = all(b[m].consciousness_level <= a[m].consciousness_level for m in differs)
    ladder["delivery_is_lower_with_support_wherever_the_level_is_better"] = all(b[m].delivery_rel < a[m].delivery_rel for m in differs)

    def collapse(run, used):
        readings = run.derived()
        states = []
        for minute in range(1, len(run.states)):
            states.append(sc.readout(run.states[minute], anchors, used, readings[minute].pressure_rel, readings[minute].delivery_rel)["collapse"]["state"])
        first = lambda wanted: next((minute + 1 for minute, state in enumerate(states) if state == wanted), None)
        last = readings[len(run.states) - 1]
        return {"first_impending": first(sc.IMPENDING), "first_established": first(sc.ESTABLISHED), "delivery_rel_at_the_end": _r(last.delivery_rel), "map_at_the_end": _r(last.map)}

    with_a2 = dataclasses.replace(profile, amendment_2=sc.development_profile("CENTER_REFERENCE"))
    with_both = _declared(with_a2, name)
    rows = {"without_support": collapse(ig.run(anchors, items, 230, with_a2), with_a2)}
    for rate in (10.0, 40.0):
        rows[f"support_{rate:g}_mcg_min_from_minute_30"] = collapse(ig.run(anchors, items + (_infusion(name, 30, rate),), 230, with_both), with_both)
    return {"witness": name, "case": "gi_bleed_72f, untreated",
            "direct_pressure_ladder": ladder,
            "amendment_2_soft_collapse": {"consciousness_witness": "CENTER_REFERENCE", "read_until": 230, "runs": rows,
                                          "the_support_delays_or_removes_the_collapse_predicate_while_delivery_is_lower": all(
                                              (row["first_established"] is None or row["first_established"] > rows["without_support"]["first_established"])
                                              and row["delivery_rel_at_the_end"] < rows["without_support"]["delivery_rel_at_the_end"]
                                              for label, row in rows.items() if label != "without_support")},
            "not_offered_by_the_development_mapping": "runtime_tone_support.with_tone_support refuses an Amendment-2 witness adapter: this interaction has not been reviewed"}


def _matrix_row(case: str, pressure_seen: str, flow_seen: str, bounded_seen: bool, evidence: dict) -> dict:
    predicted = PREDICTIONS[case]
    return {"case": case,
            "predicted": {"pressure": predicted["pressure"], "flow": predicted["flow"], "bounded": predicted["bounded"], "class": predicted["class"], "why": predicted["why"]},
            "observed": {"pressure": pressure_seen, "flow": flow_seen, "bounded": bounded_seen},
            "as_predicted": (pressure_seen, flow_seen, bounded_seen) == (predicted["pressure"], predicted["flow"], predicted["bounded"]),
            "not_represented": list(predicted["missing"]), "evidence": evidence}


def edge_matrix(families: dict, core: dict, name: str = "CENTER_REFERENCE") -> list:
    """P3-393: one row per case. The family rows read the family probes; the others read the core-level probes."""
    rows = []
    for family, probe in families.items():
        seen = probe["witnesses"][name]
        late = seen["observed"][-1]
        rows.append({**_matrix_row(probe["role"], direction(late["map_without"], late["map_with"]), direction(1.0, late["output_ratio"]), seen["facts"]["tone_below_its_ceiling"],
                                   {"probe": f"family:{family}", "case_id": probe["case_id"], "at_minute": late["minute"], "map_gain_mmhg": late["map_gain_mmhg"],
                                    "pressure_ratio": late["pressure_ratio"], "output_ratio": late["output_ratio"], "delivery_ratio": late["delivery_ratio"]}),
                     "family": family})
    d = core["distributive"]
    rows.append(_matrix_row("distributive_like_low_tone", direction(d["low_tone_without_support"]["pressure_rel"], d["low_tone_with_support"]["pressure_rel"]),
                            TOWARD_ARRIVAL if d["flow_moves_toward_arrival_and_stays_at_or_above_it"] else direction(d["low_tone_without_support"]["output_rel"], d["low_tone_with_support"]["output_rel"]),
                            d["low_tone_with_support"]["T"] < core["saturation"]["tone_ceiling"], {"probe": "core:distributive", **{key: d[key] for key in ("low_tone_without_support", "low_tone_with_support")}}))
    n = core["no_flow"]
    rows.append(_matrix_row("no_pulse", NONE if n["no_pulse_has_no_circulation"] else UP, NONE if n["no_pulse_has_no_circulation"] else UP, True, {"probe": "core:no_flow.no_pulse"}))
    rows.append(_matrix_row("empty_preload_no_flow", NONE if n["no_flow_has_no_pressure"] else UP, NONE if n["no_flow_has_no_pressure"] else UP, True, {"probe": "core:no_flow.empty_preload"}))
    s = core["saturation"]
    rows.append(_matrix_row("already_high_tone", direction(s["by_rate"][1]["map"], s["by_rate"][4]["map"]), direction(s["by_rate"][1]["output_rel"], s["by_rate"][4]["output_rel"]),
                            s["tone_never_reaches_its_ceiling"] and s["each_further_unit_of_rate_adds_less_tone"], {"probe": "core:saturation", "tone_at_10": s["by_rate"][1]["T"], "tone_at_80": s["by_rate"][4]["T"],
                                                                                                         "tone_at_the_largest_rate": s["by_rate"][5]["T"], "tone_ceiling": s["tone_ceiling"]}))
    return rows


def build_probes(families: dict | None = None) -> dict:
    import runtime_shadow_families as fam
    import runtime_tone_support as ts
    from clinical_core import vascular_support as vs
    families = families or family_probes()
    core = {"volume_dependence": core_volume_dependence(), "static_dependence": core_static_dependence(), "no_flow": core_no_flow(),
            "saturation": core_saturation(), "distributive": core_distributive(), "stopped_infusion": core_stopped_infusion(),
            "consciousness_reading": core_consciousness_reading()}
    matrix = edge_matrix(families, core)
    relative = sorted(probe["witnesses"]["CENTER_REFERENCE"]["observed"][-1]["pressure_ratio"] for probe in families.values())
    gains = sorted(probe["witnesses"]["CENTER_REFERENCE"]["observed"][-1]["map_gain_mmhg"] for probe in families.values())
    body = {
        "record_type": "COMMON_TONE_DEVELOPMENT_PROBES", "version": PROBES_VERSION, "status": "DEVELOPMENT_PROBES", "evidence_class": "MODEL_ANALYSIS",
        "statement": STATEMENT, "decision_reference": DECISIONS, "chosen_witness": None,
        "order": {"kind": ts.ORDER_KIND, "operation": ts.MAPPED_OPERATION, "rate": PROBE_RATE, "units": ts.MAPPED_UNITS, "minute": PROBE_ORDER_MINUTE, "read_until": PROBE_MINUTES},
        "region": {name: {"bounds": list(spec["bounds"]), "unit": spec["unit"], "confidence": spec["confidence"], "evidence": spec["evidence"], "assumption": spec["assumption"],
                          "uncertainty": spec["uncertainty"], "falsifier": spec["falsifier"]} for name, spec in vs.REGION.items()},
        "witnesses": {name: vs.witness(name) for name in WITNESSES},
        "no_narrow_region": "every confidence is below 0.80, so no narrow region is adopted and no point is chosen (FD-TONE-06)",
        "edge_case_matrix": matrix,
        "family_probes": families,
        "core_probes": core,
        "across_families": {
            "registered_families": sorted(fam.ADAPTERS), "one_order_mapping": "runtime_tone_support.map_orders: it reads the order and the witness, never the family or the case",
            "built_in_every_family": all(seen["built"] for probe in families.values() for seen in probe["witnesses"].values()),
            "no_family_run_failed": not any(seen["failures"] or seen["gaps"] for probe in families.values() for seen in probe["witnesses"].values()),
            "every_run_replays_exactly": all(seen["replays_exactly"] for probe in families.values() for seen in probe["witnesses"].values()),
            "volume_pump_haemoglobin_and_lung_water_untouched_everywhere": all(all(seen["facts"]["untouched_state"].values()) for probe in families.values() for seen in probe["witnesses"].values()),
            "pressure_ratio_center_reference": {"lowest": relative[0], "highest": relative[-1]},
            "map_gain_mmhg_center_reference": {"lowest": gains[0], "highest": gains[-1]},
            "no_universal_mmhg_gain": gains[-1] - gains[0] > 1.0,
        },
        "limitations": sorted({text for spec in PREDICTIONS.values() for text in spec["missing"]} | {
            "output and delivery never rise with tone: the afterload is the only path from tone to flow, and its sensitivity is one number for every pump and volume",
            "a patient who arrives already on a vasopressor cannot be represented: arrival is the scale (tone 1, support 0)",
            "only norepinephrine writes the support, and only the encounter's first order of the kind -- a start at a fixed rate in mcg/min -- is mapped",
            "the consciousness readings are taken from the pressure, so with support they read BETTER while output and delivery are lower: the direct pressure "
            "ladder, and the Amendment-2 soft-collapse conjunction, which the support can keep from establishing (the development mapping refuses that combination)",
        }),
    }
    body["provenance"] = hr.provenance(record_id=PROBES_VERSION, generating_code=generating_code(), generated_on=GENERATED_ON,
                                       source_data={"order": body["order"], "witnesses": body["witnesses"], "families": {family: probe["case_id"] for family, probe in families.items()},
                                                    "predictions": {case: {key: spec[key] for key in ("pressure", "flow", "bounded", "class")} for case, spec in PREDICTIONS.items()}})
    return hr.seal(body)


# -- writing (deliberate, never a side effect of a test) ---------------------------------------------------------------------------

def text_of(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_all() -> dict:
    """Generate both records and write them. ``historical_records.write`` refuses to replace an existing record with other content: a new
    representation is a successor record with its own name, never a regeneration in place."""
    made = {CANDIDATE_PATH: build_candidate(), PROBES_PATH: build_probes()}
    return {str(path.relative_to(ROOT)): hr.write(path, record) for path, record in made.items()}
