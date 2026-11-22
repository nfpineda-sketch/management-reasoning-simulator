"""P3-506 to P3-512 and P3-514: the DEVELOPMENT ENCOUNTER RUNNER, the management PATHS and the BUILDER of the management-trace review set (a tool, never imported by a page; it holds no test).

THE ENCOUNTER. ``DevelopmentEncounter`` is the GI encounter the page runs, without Streamlit: the frozen reader, the time words, the order ledger, the bundle rule and the engine (``pilot_acceptance.Encounter``,
the family branch of the page's own order path), with the REAL live development authority site opened on its arrival under the norepinephrine development grant, called exactly where the page calls it
(``site.minute`` after an executed turn, ``site.settle_provenance`` after settlement -- the calls of the certified ``test_phase3_ne_authority.Driver``). It builds no parallel simulator: every turn is the two
certified harnesses' own calls, in their order, and every pressure is the one the live authority committed.

THE PATHS. Ten management paths from the SAME arrival (A to J), each with what was expected of it BEFORE it ran (written here, and machine-checked by ``test_phase3_management_trace.py``), a scenario priority per
step and a proposed category (both AUTHORED, proposed for faculty review: they are not the resident's and not the faculty's). No path is labelled correct; no outcome is hard-coded; no penalty is added.

THE SET. ``build`` runs every path through the live authority, extracts each trace from the runtime events (``development_management_trace.extract``), and assembles the review set
``GI_MANAGEMENT_TRACE_V1_FACULTY_REVIEW``: per path the clinical start, the action sequence, the committed pressure trajectory, the faculty-readable trace and the boundary. The audit keeps the structured trace,
its digest, the authority artifact's digest, grant and snapshots, APART from the items. The set is a VERSIONED historical record (provenance, seal, index); ``write_all`` refuses to replace it with other bytes.
"""
from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import development_management_trace as mt
import faculty_management_review as fmr
import historical_records as hr

ROOT = Path(__file__).resolve().parent
SET_PATH = fmr.SET_PATH
GENERATED_ON = "2026-11-22"
DECISIONS = "FD-MTRACE-01 to FD-MTRACE-10"
REVIEW_MODULES = ("faculty_management_review.py", "faculty_management_review_ui.py")
CASE_ID = "gi_bleed_57m"
REASSESS = "Reassess in {n} minutes."
STEP_MIN = 15
VOL = "Give 1 litre of normal saline over 15 minutes. Transfuse 2 units of packed red cells. Reassess in 15 minutes."
NE = "Start norepinephrine at {rate} mcg/min. Reassess in 15 minutes."
UP, DOWN = "Increase norepinephrine to {rate} mcg/min. Reassess in 15 minutes.", "Decrease norepinephrine to {rate} mcg/min. Reassess in 15 minutes."
STOP = "Stop norepinephrine. Reassess in 15 minutes."

P_VOLUME = "Restore circulating volume and replace lost blood while the bleeding continues."
P_SUPPORT = "Support a perfusion pressure that is low again after volume and blood; the bleeding still needs definitive control."
#: A step of a path happens WHEN its condition holds at a decision point (the end of a turn), read from what the resident could see there (the committed pressure):
#: ``("at", m)`` at minute m; ``("hypotensive_from", m)`` at the first reading at or after minute m that is hypotensive (SBP below 90 or MAP below 65, the trace's own threshold);
#: ``("after", n)`` n minutes or more after the previous step; ``("hypotensive_after", n)`` / ``("not_hypotensive_after", n)`` n minutes or more after the previous step and only when the reading is / is not hypotensive.
#: Every other turn is a reassessment of 15 minutes (the last one ends at the horizon). A state-contingent step is what keeps the action consistent with the state it answers (P3-515: no state/action mismatch).
#: ``expected`` is the qualitative behaviour written BEFORE the certified run (P3-506); ``category`` the proposed management meaning (FD-MTRACE-02). All AUTHORED, all proposed for faculty review.
PATHS = {
    "A": {"short": "Volume + blood", "title": "early crystalloid and blood, then reassessment only", "category": "REASONABLE",
          "steps": [(("at", 0), VOL, P_VOLUME)],
          "expected": "the pressure rises after volume and blood, then erodes while the bleeding continues; it ends above the untreated course",
          "purpose": "Early crystalloid and blood, then reassessment only: is the pressure response, and its later erosion while the bleeding continues, coherent in direction and timing, and does the management "
                     "trace avoid any implication of control of the bleeding?"},
    "B": {"short": "Then norepinephrine", "title": "crystalloid and blood, hypotension again, then norepinephrine", "category": "REASONABLE",
          "steps": [(("at", 0), VOL, P_VOLUME), (("hypotensive_from", 15), NE.format(rate=5), P_SUPPORT)],
          "expected": "after volume and blood the pressure erodes until it is low again; the vasopressor then adds pressure above the volume-only course; the gain erodes while the bleeding continues",
          "purpose": "Volume and blood, then norepinephrine when the pressure is low again: is the added pressure support, and its erosion while the bleeding continues, coherent, and is the vasopressor shown as "
                     "temporary support rather than treatment of the bleeding?"},
    "C": {"short": "Norepinephrine first", "title": "norepinephrine first, crystalloid and blood later", "category": "TEMPORIZING",
          "steps": [(("at", 0), NE.format(rate=10), "Raise the pressure with a vasopressor before giving volume."), (("at", 30), VOL, P_VOLUME)],
          "expected": "the vasopressor raises the pressure early and the gain fades while no volume is given; volume and blood then raise it again; the gain erodes while the bleeding continues",
          "purpose": "Norepinephrine first, volume and blood later: are the early support, its fading while no volume is given, and the later response to volume and blood coherent in order and timing?"},
    "D": {"short": "Rate increased", "title": "initial resuscitation, norepinephrine, then a rate increase", "category": "REASONABLE",
          "steps": [(("at", 0), VOL, P_VOLUME), (("hypotensive_from", 15), NE.format(rate=2), P_SUPPORT),
                    (("hypotensive_after", 15), UP.format(rate=8), "Support a perfusion pressure that is low again on the vasopressor.")],
          "expected": "a low starting rate adds little; when the pressure is low again on it, the increase raises the pressure at the next reading; the bleeding continues",
          "purpose": "Resuscitation, norepinephrine, then a rate increase while the pressure is still low: does the pressure follow the increase and then erode while the bleeding continues, and is that read as "
                     "temporary support?"},
    "E": {"short": "Weaned and stopped", "title": "initial resuscitation, norepinephrine, improvement, then a rate decrease and a stop", "category": "REASONABLE",
          "steps": [(("at", 0), VOL, P_VOLUME), (("hypotensive_from", 15), NE.format(rate=10), P_SUPPORT),
                    (("not_hypotensive_after", 15), DOWN.format(rate=5), "Reduce the vasopressor as the pressure allows, watching for it to fall back."),
                    (("not_hypotensive_after", 15), STOP, "Stop the vasopressor, watching for the pressure to fall back.")],
          "expected": "the decrease and the stop take the vasopressor support away: the pressure falls back, and after the support has worn off it is the volume-only course",
          "purpose": "Resuscitation, norepinephrine, then a rate decrease and a stop after improvement: does the pressure fall back causally, and does the trace avoid reading the earlier improvement as recovery?"},
    "F": {"short": "Vasopressor alone", "title": "norepinephrine without volume or blood", "category": "INCOMPLETE",
          "steps": [(("at", 0), NE.format(rate=10), "Raise the pressure with a vasopressor alone.")],
          "expected": "the vasopressor raises the pressure early; without volume or blood it falls below the volume-only course and keeps falling; it stays above the untreated course",
          "purpose": "Norepinephrine without volume or blood: are the early rise and the later course coherent in direction and timing, and how does the trace read the early rise?"},
    "G": {"short": "Slow crystalloid", "title": "slow crystalloid alone", "category": "TEMPORIZING",
          "steps": [(("at", 0), "Give 1 litre of normal saline over 60 minutes. Reassess in 15 minutes.", "Give volume slowly.")],
          "expected": "the pressure falls slowly while the slow crystalloid does not keep up with the bleeding; it ends below the volume-and-blood course and not below the untreated course",
          "purpose": "Slow crystalloid alone: is the trajectory coherent with a measure that does not keep up with the bleeding?"},
    "H": {"short": "No treatment", "title": "no treatment for two hours", "category": "CLEARLY_NONBENEFICIAL",
          "steps": [],
          "expected": "the pressure falls throughout; the lowest reading is at the boundary",
          "purpose": "No treatment for two hours: is the course coherent in direction and timing?"},
    "I": {"short": "Escalation, no volume", "title": "norepinephrine escalated each time the pressure is low again, with no volume or blood", "category": "CLEARLY_NONBENEFICIAL",
          "steps": [(("at", 0), NE.format(rate=5), "Raise the pressure with a vasopressor alone."),
                    (("hypotensive_after", 15), UP.format(rate=10), "Raise the pressure by escalating the vasopressor, without volume or blood."),
                    (("hypotensive_after", 15), UP.format(rate=15), "Raise the pressure by escalating the vasopressor, without volume or blood."),
                    (("hypotensive_after", 15), UP.format(rate=20), "Raise the pressure by escalating the vasopressor, without volume or blood.")],
          "expected": "each increase adds little and for a short time; the pressure keeps falling while no volume is given and ends below the volume-only course",
          "purpose": "Norepinephrine escalated each time the pressure is low again, while no volume or blood is given: is the course coherent with each escalation in direction and timing?"},
    "J": {"short": "Stopped too early", "title": "norepinephrine stopped at the next reading after a transient rise", "category": "INCOMPLETE",
          "steps": [(("at", 0), VOL, P_VOLUME), (("hypotensive_from", 15), NE.format(rate=10), P_SUPPORT), (("after", 15), STOP, "Stop the vasopressor after a transient rise.")],
          "expected": "the vasopressor gives a transient rise; after the stop the pressure falls back to the volume-only course",
          "purpose": "Norepinephrine stopped at the next reading after a transient rise: does the pressure fall back causally, and is the transient rise read as temporary support?"},
}
PATH_IDS = tuple(PATHS)
MARKER = {"fluid": "saline", "blood": "red cells", "NE_START": "norepinephrine {rate}", "NE_RESTART": "norepinephrine {rate}", "NE_INCREASE": "norepinephrine up to {rate}",
          "NE_DECREASE": "norepinephrine down to {rate}", "NE_STOP": "norepinephrine stop", "ppi": "acid suppression", "consult": "consultation"}


# -- the environment of the live development authority (the norepinephrine development grant) -------------------------------------------------------------------------------------
def environment(store_dir: str | None = None) -> dict:
    """The authorized DEVELOPMENT configuration of the live GI pressure authority under the norepinephrine grant: the ratified pressure snapshot AND the tone snapshot (the selector never opens it alone)."""
    import runtime_authority as ra
    import runtime_authority_store as store
    import runtime_pressure_snapshot as ps
    import runtime_shadow as rs
    import runtime_tone_snapshot as tn
    return {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE, ra.SNAPSHOT_FLAG: ps.SNAPSHOT_ID, ra.TONE_FLAG: tn.SNAPSHOT_ID,
            store.STORE_FLAG: store_dir or tempfile.mkdtemp(prefix="mtrace-store-")}


class DevelopmentEncounter:
    """One GI encounter on the page's family order path with the REAL live development authority site, recording each turn as the Phase-0 trace records it."""

    def __init__(self, case_id: str = CASE_ID, env: Mapping[str, str] | None = None):
        import pilot_acceptance
        import runtime_authority as ra
        self.env = dict(env or environment())
        self.entries: list = []
        with self._scoped():
            self.enc = pilot_acceptance.Encounter(case_id)
            self.arrival = deepcopy(self.enc.state)
            self.site = ra.open_site(self.arrival, environ=self.env)

    @contextmanager
    def _scoped(self):
        """The development configuration in the process environment ONLY while this runner works: whatever was there before is put back on exit, so a runner never leaks the live-authority flags into
        what runs after it in the same process (a test file, a page test, another runner)."""
        import runtime_authority as ra
        names = set(ra.PILOT_FLAGS) | set(ra.PILOT_REQUIRED_ON) | set(self.env)
        saved = {name: os.environ.get(name) for name in names}
        try:
            for name in names:
                os.environ.pop(name, None)
            os.environ.update(self.env)
            yield
        finally:
            for name, value in saved.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

    @property
    def minute(self) -> int:
        return int(self.enc.state.get("sim_time", 0) or 0)

    @property
    def halted(self) -> bool:
        return bool(self.site is None or self.site.halted)

    def order(self, text: str) -> dict:
        """One order turn: the calls of ``pilot_acceptance.Encounter.order`` and of the certified authority ``Driver``, in their order. Returns the turn entry."""
        with self._scoped():
            return self._order(text)

    def _order(self, text: str) -> dict:
        import event_provenance
        import order_ledger
        import order_pipeline
        import time_semantics
        import trace_phase0
        from family_parser import parse_family_actions
        enc = self.enc
        submission = f"t{enc._turns}"
        enc._turns += 1
        minute = self.minute
        parsed = time_semantics.apply(text, parse_family_actions(text))
        parsed.setdefault("raw_text", text)
        turn = order_pipeline.open_turn(text, parsed, submission_id=submission, entry_point="free_text", minute=minute, ledger=enc.ledger)
        before = enc.shadow.capture(enc.state)
        result, split, run = enc._execute(parsed, text)
        enc.shadow.observe(before, enc.state, parsed, result, run, submission)
        if self.site is not None and result.get("executed"):
            prepared = self.site.minute(before, enc.state, enc.shadow, run, submission)
            if prepared is not None:
                enc.state = prepared
        order_pipeline.settle(turn, result=result, run_actions=run, split=split, minute_before=minute, minute_after=self.minute, terminal=bool(result.get("terminal_locked")))
        orders = order_ledger.snapshot(turn["orders"])
        events = event_provenance.attribute(deepcopy(result.get("events") or []), list(enc.ledger) + orders)
        order_pipeline.upsert(enc.ledger, turn["orders"])
        if self.site is not None and result.get("executed"):
            self.site.settle_provenance(submission, orders)
        entry = {"text": text, "decision_time_min": minute, "response_time_min": self.minute, "executed": bool(result.get("executed")), "terminal_locked": bool(result.get("terminal_locked")),
                 "clarification": result.get("clarification"), "orders": orders, "events": events, "observation_snapshot": trace_phase0.observation_snapshot(enc.state, result)}
        self.entries.append(entry)
        return entry

    def artifact(self) -> dict:
        return self.site.artifact() if self.site is not None else {}


def plan_digest(path_id: str) -> str:
    path = PATHS[path_id]
    return mt.digest({"path": path_id, "steps": [[list(when), text] for when, text, _ in path["steps"]], "step_min": STEP_MIN, "horizon_min": mt.HORIZON_MIN,
                      "hypotension": [mt.HYPOTENSION_SBP, mt.HYPOTENSION_MAP]})


def _holds(when: tuple, minute: int, last_step_minute: int | None, low: bool) -> bool:
    """Whether a step's condition holds at this decision point (``low``: the reading the resident sees now is hypotensive)."""
    kind, value = when
    if kind == "at":
        return minute == value
    if kind == "hypotensive_from":
        return minute >= value and low
    since = minute - (last_step_minute if last_step_minute is not None else 0)
    if kind == "after":
        return since >= value
    if kind == "hypotensive_after":
        return since >= value and low
    if kind == "not_hypotensive_after":
        return since >= value and not low
    raise ValueError(f"unknown condition {kind!r}")


def run_path(path_id: str, case_id: str = CASE_ID, env: Mapping[str, str] | None = None) -> dict:
    """Play ONE path through the live development authority to the boundary. Each step is given at the first decision point where its condition holds, read from the pressure the resident sees there (the one
    the live authority committed). Returns the encounter, its turns, the trace, the step priorities the path AUTHORED and the minute each step was given."""
    import runtime_authority as ra
    path = PATHS[path_id]
    run = DevelopmentEncounter(case_id, env)
    observable = run.arrival["observable"]
    arrival = {"sbp": int(observable["sbp"]), "dbp": int(observable["dbp"]), "map": ra.derived_map(observable["sbp"], observable["dbp"])}       # the MAP the page derives (the authority's own function)
    priorities, given, pending, last_step = {}, [], list(path["steps"]), None
    while run.minute < mt.HORIZON_MIN and not run.halted:
        minute = run.minute
        seen = dict(run.enc.state.get("observable") or {})
        reading = {"sbp": int(seen["sbp"]), "dbp": int(seen["dbp"]), "map": ra.derived_map(seen["sbp"], seen["dbp"])}
        text = None
        if pending and _holds(pending[0][0], minute, last_step, bool(mt.hypotensive(reading))):
            when, text, priority = pending.pop(0)
            priorities[len(run.entries) + 1] = priority
            given.append({"minute": minute, "when": list(when), "text": text})
            last_step = minute
        entry = run.order(text or REASSESS.format(n=min(STEP_MIN, mt.HORIZON_MIN - minute)))
        if entry["terminal_locked"] or any(mt.is_definitive_request(order) for order in entry["orders"]):
            break
    turns = [mt.turn_from_runner_entry(entry) for entry in run.entries]
    artifact = run.artifact()
    scenario = {"id": f"MT-{path_id}", "case_id": case_id, "plan_digest": plan_digest(path_id), "priorities": priorities, "category": path["category"]}
    trace = mt.extract(turns, artifact, arrival, scenario=scenario)
    return {"run": run, "entries": plain(run.entries), "turns": turns, "artifact": artifact, "trace": trace, "arrival": {**dict(observable), "map": arrival["map"]}, "given": given,
            "not_given": [list(step[0]) for step in pending]}


def retrace(played: Mapping, path_id: str, case_id: str = CASE_ID) -> dict:
    """The trace of a played path read AGAIN from its persisted inputs alone (its turns, its artifact, its arrival and the priorities its steps were given with): the extraction is a pure function of them."""
    priorities = {int(step["n"]): step["priority"]["scenario"]["value"] for step in played["trace"]["steps"] if step["priority"]["scenario"]["value"]}
    scenario = {"id": f"MT-{path_id}", "case_id": case_id, "plan_digest": plan_digest(path_id), "priorities": priorities, "category": PATHS[path_id]["category"]}
    arrival = {key: int(played["arrival"][key]) for key in ("sbp", "dbp", "map")}
    return {**dict(played), "trace": mt.extract(played["turns"], played["artifact"], arrival, scenario=scenario)}


def plain(value: Any) -> Any:
    """``value`` as plain JSON data (read-only mappings and tuples become dicts and lists); nothing else changes."""
    if isinstance(value, Mapping):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def portable(played: Mapping) -> dict:
    """A played path without its live objects (what a JSON file can hold): its entries, turns, artifact, trace, arrival and steps. ``build`` accepts it as it accepts a live one."""
    return {key: plain(value) for key, value in dict(played).items() if key != "run"}


# -- the review item --------------------------------------------------------------------------------------------------------------------------------------------------------------
def _rate_text(rate: Any) -> str:
    return f"{float(rate):g}"


def _result(entry_orders: list, advance: int) -> str:
    parts = []
    for order in entry_orders:
        if str(order.get("fate") or "").upper() != "EXECUTED":
            reason = str(order.get("reason") or "").strip()
            parts.append(reason or f"not carried out: {order.get('canonical') or order.get('span')}")
            continue
        kind = order.get("class")
        if kind == "reassessment":
            continue
        reason = str(order.get("reason") or "").strip()
        parts.append(reason if reason and reason != "executed" else str(order.get("canonical") or ""))
    if advance > 0:
        parts.append(f"{advance} min passed")
    return "; ".join(part for part in parts if part) or "—"


def _intervention(step: Mapping) -> bool:
    return any(row["class"] not in ("reassessment", "vascular_access") and row["fate"] == "EXECUTED" for row in step["action"]["orders"]["value"])


def _marker(step: Mapping) -> str:
    words = []
    for row in step["action"]["orders"]["value"]:
        if row["fate"] != "EXECUTED" or row["class"] in ("reassessment", "vascular_access"):
            continue
        key = row.get("operation") or row["class"]
        words.append(MARKER.get(key, row["class"]).format(rate=_rate_text(row.get("rate_mcg_min") or 0)))
    return f"{step['n']} · " + " + ".join(words)


def build_item(path_id: str, played: Mapping, case: Mapping) -> dict:
    """The review item of ONE path: what the reviewer sees, nothing else (no identifier, digest, grant, snapshot, parameter, heart rate or consciousness)."""
    path, trace = PATHS[path_id], played["trace"]
    arrival = played["arrival"]
    steps = trace["steps"]
    timeline = []
    for step, entry in zip(steps, played["entries"]):
        decision, response = step["decision_minute"]["value"], step["response_minute"]["value"]
        timeline.append({"n": step["n"], "minute": decision, "advance": response - decision, "action": step["action"]["text"]["value"], "result": _result(entry["orders"], response - decision),
                         "executed": bool(step["action"]["executed"]["value"]), "intervention": _intervention(step)})
    points = mt.trajectory(trace)
    common = [{"minute": point["minute"], "sbp": float(point["sbp"]), "dbp": float(point["dbp"]), "map": float(point["map"])} for point in points]
    markers = [{"minute": step["decision_minute"]["value"], "label": _marker(step)} for step in steps if _intervention(step)]
    boundary = dict(trace["boundary"])
    return {"scenario_id": f"MT-{path_id}", "short": path["short"], "title": f"57-year-old man with an upper gastrointestinal bleed: {path['title']}", "kind": fmr.KIND_CASE, "banner": fmr.CASE_BANNER,
            "note": fmr.CASE_NOTE, "context": case["context"], "baseline_facts": list(case["baseline_facts"]), "purpose": path["purpose"],
            "arrival": {"sbp": int(arrival["sbp"]), "dbp": int(arrival["dbp"]), "map": int(arrival["map"]), "spo2": int(arrival["spo2"]), "rr": int(arrival["respiratory_rate"])},
            "timeline": timeline, "common": common, "markers": markers, "trace": mt.render(trace),
            "boundary": {"minute": int(boundary["minute"]), "message": boundary["message"]}, "stopped": False, "required": True}


def case_context() -> dict:
    """The authored clinical context of the 57-year-old man, exactly as the reviewed titration set states it (it is the same authored case; nothing is rewritten)."""
    import faculty_titration_review as ftt
    loaded = ftt.load_set()
    item = loaded["items"]["TIT-1"]
    return {"context": item["context"], "baseline_facts": list(item["baseline_facts"])}


def _sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def generating_code() -> dict:
    """What generated the set, by content: the live common core, the live authority modules, the trace module and this builder. The review modules are left out (the loader holds the pin)."""
    from clinical_core import amendment_3 as a3
    modules = ("development_management_trace.py", "runtime_authority.py", "runtime_ne_authority.py", "runtime_ne_grant.py", "runtime_tone_snapshot.py", "runtime_pressure_snapshot.py", "runtime_shadow.py",
               "runtime_shadow_families.py", "family_engine.py", "family_parser.py", "pilot_acceptance.py")
    return {"clinical_core": a3.amended_core_digest_now(), **{name: _sha(ROOT / name) for name in modules}, "test_gi_management_trace_paths.py": _sha(Path(__file__).resolve()),
            "excluded_review_modules": list(REVIEW_MODULES)}


def build(played: Mapping[str, Mapping] | None = None) -> dict:
    """The review set: every path played through the live development authority, its trace extracted, its item assembled. Raises when an item or a trace does not hold."""
    played = dict(played or {path_id: run_path(path_id) for path_id in PATH_IDS})
    case = case_context()
    items, audit_paths = [], {}
    for path_id in PATH_IDS:
        trace, turns = played[path_id]["trace"], played[path_id]["turns"]
        problems = mt.trace_problems(trace, turns)
        if problems:
            raise ValueError(f"MT-{path_id}: the trace does not hold: {problems}")
        item = build_item(path_id, played[path_id], case)
        problems = fmr.item_problems(item)
        if problems:
            raise ValueError(f"MT-{path_id}: the item does not hold: {problems}")
        items.append(item)
        audit_paths[f"MT-{path_id}"] = {"trace": trace, "trace_digest": trace["trace_digest"], "plan_digest": plan_digest(path_id), "category_proposed": PATHS[path_id]["category"],
                                        "expected_before_the_run": PATHS[path_id]["expected"], "steps": [[list(when), text] for when, text, _ in PATHS[path_id]["steps"]],
                                        "given": played[path_id]["given"], "not_given": played[path_id]["not_given"], "authority": trace["authority"],
                                        # the persisted inputs of the trace (the turns as the runtime recorded them and the part of the authority artifact the extraction reads): a reader re-extracts the SAME
                                        # trace from this record alone, as a session that restarts from its persisted inputs would (P3-512, P3-515 #10)
                                        "persisted_inputs": {"turns": plain(turns), "artifact_view": mt.artifact_view(played[path_id]["artifact"]), "arrival": dict(trace["arrival"]["value"])}}
    audit = {"decision_reference": DECISIONS, "encounter": mt.encounter_definition(), "paths": audit_paths, "case_id": CASE_ID,
             "not_stored_with_the_items": ["heart rate, capillary refill and mental status come from the legacy engine and are not part of the items (FD-MTRACE-03, FD-MTRACE-06)",
                                           "no tone value, parameter, snapshot, grant or lineage reaches the items: they stay in this audit"],
             "no_physiology_change": True, "no_parameter_selected": True, "no_source_control": True, "pressures_from": "the live development authority (committed minutes of its artifact)"}
    body = {"record_type": fmr.SET_TYPE, "version": fmr.VERSION, "set_id": fmr.SET_ID, "statement": fmr.STATEMENT,
            "what_it_is": ("Ten management paths of ONE upper gastrointestinal hemorrhage case from the same arrival, played through the live development authority of the GI pressure with manual norepinephrine: "
                           "for each, the action sequence, the committed pressure trajectory, the management trace derived from the runtime events and the development boundary."),
            "order": [f"MT-{path_id}" for path_id in PATH_IDS], "items": items, "limitations": [dict(entry) for entry in fmr.LIMITATIONS], "audit": audit}
    body["provenance"] = hr.provenance(record_id=fmr.SET_ID, generating_code=generating_code(), generated_on=GENERATED_ON,
                                       source_data={"paths": {path_id: {"plan_digest": plan_digest(path_id), "trace_digest": played[path_id]["trace"]["trace_digest"],
                                                                        "artifact_digest": played[path_id]["artifact"].get("artifact_digest")} for path_id in PATH_IDS},
                                                    "encounter_definition_digest": mt.encounter_definition()["definition_digest"]},
                                       grant_id=played[PATH_IDS[0]]["trace"]["authority"]["grant_id"])
    return hr.seal(body)


def write_all(path: Path | None = None) -> dict:
    target = Path(path or SET_PATH)
    return {str(target): hr.write(target, build())}


def reproduce(played: Mapping[str, Mapping] | None = None) -> dict:
    """The CONTENT of the set, regenerated without provenance or seal: what a test compares with the stored set."""
    record = build(played)
    return {key: value for key, value in record.items() if key not in ("provenance", "record_digest")}


if __name__ == "__main__":
    print(json.dumps(write_all(), indent=2))
