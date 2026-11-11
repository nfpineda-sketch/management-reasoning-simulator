"""P3-200, P3-201 and P3-202: the consciousness-divergence review, the audit of the readers of ``mental_status`` and the comparison of the
pressure-authority series between the closure core and the active core.

TEST-SIDE and read-only. Nothing here changes physiology, enables authority or writes a patient state. Three parts:

* ``episodes`` (P3-200): the 461 ``POTENTIAL_EDUCATIONAL_PROBLEM`` minutes of the counterfactual record, decomposed into contiguous episodes, each
  with what the legacy engine showed, what the snapshot would have shown, the mechanism's own quantities, a direction and a coherence verdict.
  The legacy engine is never taken as correct because it is the legacy engine.
* ``scan_readers`` and ``READER_TABLE`` (P3-201): every syntactic use of ``mental_status`` in the repository's runtime modules, found by AST, and
  the classification of every function that holds one. A MENTION is told apart from an EXECUTABLE READ, and a read of the live observable from a
  read of the authored arrival.
* ``compare_pressure_series`` (P3-202): the artifacts the EXISTING development harness produces on two trees, field by field.
"""
from __future__ import annotations

import ast
import os
import re
from typing import Any, Mapping, Sequence

import test_gi_snapshot_analysis as an

ROOT = os.path.dirname(os.path.abspath(__file__))
REVIEW_VERSION = "P3-200"

# ============================================================================================================================================
# P3-200: consciousness divergence
# ============================================================================================================================================

COMMON_MORE, LEGACY_MORE, CROSSING, TRANSIENT = "COMMON_MORE_IMPAIRED", "LEGACY_MORE_IMPAIRED", "CROSSING", "TRANSIENT"
COHERENT, CONTRADICTION = "MECHANISTICALLY_COHERENT_DIFFERENCE", "STRUCTURAL_CONTRADICTION"
#: An episode of at most this many compared minutes is TRANSIENT whatever its sign (a single sampled minute at an order, typically).
TRANSIENT_MAX_MINUTES = 2
WORD = {0: "Alert", 1: "Drowsy", 2: "Obtunded", 3: "Unresponsive"}
#: The legacy engine's own consciousness ladder for a patient who arrives Alert (``family_engine._PRESSURE_LEVELS``): ABSOLUTE systolic pressure.
LEGACY_SBP_DROWSY, LEGACY_SBP_OBTUNDED = 80.0, 65.0


def _index(minutes: Sequence[int]) -> dict:
    return {minute: i for i, minute in enumerate(minutes)}


def _mechanism(values: Mapping[str, float], physical: Mapping[str, Sequence]) -> dict:
    """The snapshot's own quantities per minute over a recorded physical course (the independent evaluator; exact, proved elsewhere)."""
    rows = an.evaluate(values, physical)
    by_minute = {}
    for row, delivery, perfusion in zip(rows, physical["relative_delivery"], physical["relative_perfusion"]):
        by_minute[row["minute"]] = {"F": row["F"], "collapse_burden": row["collapse_burden"], "category": row["category"],
                                    "collapse_state": row["collapse_state"], "relative_delivery": delivery, "relative_perfusion": perfusion,
                                    "target": an._ramp(delivery, values["delivery_normal"], values["delivery_severe"])}
    return by_minute


def _coherence(minutes: Sequence[int], common: Sequence[int], mechanism: Mapping[int, Mapping], first_order: int | None) -> dict:
    """Does the common category follow its declared causes inside the episode? Three checks, each a count of violations (all zero is coherent).

    1. the category shown is the category of the composite the mechanism holds (F, or established collapse) at that minute;
    2. F moves toward its target and never away from it (it rises only while the delivery signal is above it, falls only while below);
    3. upstream first: relative delivery does not rise before any order was given."""
    wrong_category = away_from_target = delivery_rose_untreated = 0
    span = range(minutes[0], minutes[-1] + 1)
    for minute, shown in zip(minutes, common):
        held = mechanism.get(minute)
        if held is None or shown != held["category"]:
            wrong_category += 1
    for minute in span:
        now, nxt = mechanism.get(minute), mechanism.get(minute + 1)
        if now is None or nxt is None:
            continue
        step, gap = nxt["F"] - now["F"], now["target"] - now["F"]
        if step * gap < -1e-15:
            away_from_target += 1
        if (first_order is None or minute + 1 <= first_order) and nxt["relative_delivery"] > now["relative_delivery"] + 1e-12:
            delivery_rose_untreated += 1
    violations = {"category_is_not_the_composite": wrong_category, "f_moves_away_from_its_target": away_from_target,
                  "delivery_rises_before_any_order": delivery_rose_untreated}
    return {"violations": violations, "verdict": COHERENT if not any(violations.values()) else CONTRADICTION}


def episodes(counterfactual: Mapping, sensitivity: Mapping, values: Mapping[str, float], runs: str = "required_runs") -> list:
    """Every contiguous ``POTENTIAL_EDUCATIONAL_PROBLEM`` episode of consciousness in the counterfactual record, fully described."""
    out = []
    for key in sorted(counterfactual[runs]):
        run = counterfactual[runs][key]
        case, scenario = key.split("/")
        domain = run["domains"]["consciousness_category"]
        minutes, position = run["minutes"], _index(run["minutes"])
        mechanism = _mechanism(values, an.course_of_record(sensitivity["physical"])[case][scenario]["physical"])
        pressures = run["domains"]["sbp"]
        for start, end in domain["flagged_windows"]["POTENTIAL_EDUCATIONAL_PROBLEM"]:
            inside = [minute for minute in minutes if start <= minute <= end]
            legacy = [domain["legacy"][position[minute]] for minute in inside]
            common = [domain["candidate"][position[minute]] for minute in inside]
            signs = {(-1 if a > b else 1 if b > a else 0) for a, b in zip(legacy, common)} - {0}
            if len(inside) <= TRANSIENT_MAX_MINUTES:
                direction = TRANSIENT
            elif signs == {1}:
                direction = COMMON_MORE
            elif signs == {-1}:
                direction = LEGACY_MORE
            else:
                direction = CROSSING
            first_order = run["first_order_minute"]

            def at(minute: int) -> dict:
                held = mechanism[minute]
                return {"minute": minute, "legacy": WORD[domain["legacy"][position[minute]]], "common": WORD[domain["candidate"][position[minute]]],
                        "relative_delivery": round(held["relative_delivery"], 4), "relative_perfusion": round(held["relative_perfusion"], 4),
                        "F": round(held["F"], 4), "collapse_burden": round(held["collapse_burden"], 4), "collapse_state": held["collapse_state"],
                        "legacy_sbp": pressures["legacy"][position[minute]], "common_sbp": pressures["candidate"][position[minute]]}
            out.append({
                "case": case, "scenario": scenario, "start": start, "end": end, "compared_minutes": len(inside), "span_minutes": end - start + 1,
                "actions_before": ("none: untreated so far" if first_order is None or first_order > start
                                   else f"first order at minute {first_order} ({scenario})"),
                "first_order_minute": first_order, "at_start": at(inside[0]), "at_end": at(inside[-1]),
                "legacy_categories": sorted({WORD[value] for value in legacy}), "common_categories": sorted({WORD[value] for value in common}),
                "max_band_gap": max(abs(a - b) for a, b in zip(legacy, common)), "direction": direction,
                "coherence": _coherence(inside, common, mechanism, first_order),
            })
    return out


def run_coherence(counterfactual: Mapping, sensitivity: Mapping, values: Mapping[str, float], runs: str = "required_runs") -> dict:
    """The same three checks over EVERY compared minute of every run, not only inside the divergence episodes: a structural contradiction at a
    minute where the two words happen to agree is still one (the independent review of P3-208 planted one there and no episode saw it)."""
    per_run, compared = {}, 0
    for key in sorted(counterfactual[runs]):
        run = counterfactual[runs][key]
        case, scenario = key.split("/")
        mechanism = _mechanism(values, an.course_of_record(sensitivity["physical"])[case][scenario]["physical"])
        minutes = list(run["minutes"])
        compared += len(minutes)
        per_run[key] = _coherence(minutes, list(run["domains"]["consciousness_category"]["candidate"]), mechanism, run["first_order_minute"])
    contradictions = sorted(key for key, found in per_run.items() if found["verdict"] != COHERENT)
    return {"runs": len(per_run), "compared_minutes": compared, "contradictions": contradictions,
            "violations": {name: sum(found["violations"][name] for found in per_run.values())
                           for name in ("category_is_not_the_composite", "f_moves_away_from_its_target", "delivery_rises_before_any_order")},
            "verdict": COHERENT if not contradictions else CONTRADICTION}


def opposite_direction_explanation(counterfactual: Mapping, sensitivity: Mapping, values: Mapping[str, float]) -> dict:
    """Why the two GI cases diverge from the legacy engine in OPPOSITE directions at the onset of impairment, from the untreated runs alone.

    The legacy ladder reads ABSOLUTE systolic pressure (drowsy below 80 mmHg); the common core reads delivery RELATIVE to each patient's own
    arrival. A patient who arrives lower crosses the absolute threshold sooner; both cross the relative one at the same minute."""
    out = {"legacy_threshold_sbp_drowsy": LEGACY_SBP_DROWSY, "cases": {}}
    course = an.course_of_record(sensitivity["physical"])
    for case in an.CASES:
        run = counterfactual["required_runs"][f"{case}/untreated"]
        minutes = run["minutes"]
        legacy, common = run["domains"]["consciousness_category"]["legacy"], run["domains"]["consciousness_category"]["candidate"]
        sbp = run["domains"]["sbp"]["legacy"]
        first_legacy = next(i for i, value in enumerate(legacy) if value >= 1)
        first_common = next(i for i, value in enumerate(common) if value >= 1)
        mechanism = _mechanism(values, course[case]["untreated"]["physical"])
        out["cases"][case] = {
            "legacy_arrival_sbp": sbp[0],
            "legacy_first_drowsy_minute": minutes[first_legacy], "legacy_sbp_at_that_minute": sbp[first_legacy],
            "legacy_sbp_one_minute_before": sbp[first_legacy - 1],
            "common_first_somnolent_minute": minutes[first_common],
            "relative_delivery_at_that_minute": round(mechanism[minutes[first_common]]["relative_delivery"], 6),
            "F_at_that_minute": round(mechanism[minutes[first_common]]["F"], 6),
            "direction_at_onset": LEGACY_MORE if minutes[first_legacy] < minutes[first_common] else COMMON_MORE if minutes[first_common] < minutes[first_legacy] else "SAME_MINUTE",
        }
    a, b = (out["cases"][case] for case in an.CASES)
    out["explained_by"] = ("ABSOLUTE_PAS_LEGACY_THRESHOLD_VERSUS_RELATIVE_TO_ARRIVAL_SEMANTICS"
                           if (a["legacy_sbp_at_that_minute"] < LEGACY_SBP_DROWSY <= a["legacy_sbp_one_minute_before"]
                               and b["legacy_sbp_at_that_minute"] < LEGACY_SBP_DROWSY <= b["legacy_sbp_one_minute_before"]
                               and a["common_first_somnolent_minute"] == b["common_first_somnolent_minute"]
                               and abs(a["relative_delivery_at_that_minute"] - b["relative_delivery_at_that_minute"]) < 1e-3
                               and a["legacy_arrival_sbp"] != b["legacy_arrival_sbp"]) else "NOT_EXPLAINED")
    return out


#: P3-200D: the questions the faculty answers for each representative episode. They are NOT answered here: they are clinical-educational judgement.
FACULTY_QUESTIONS = ("Would this state be defensible to show a resident?", "Is impairment too early or too late?",
                     "Is recovery too early or too late?", "Does the category communicate the physiologic severity appropriately?")


def faculty_table(found: Sequence[Mapping], limit: int = 9) -> list:
    """The highest-impact episodes, one per distinct pattern (case, direction, words), ranked by compared minutes times the band gap."""
    ranked = sorted(found, key=lambda item: -(item["compared_minutes"] * item["max_band_gap"]))
    chosen, seen = [], set()
    for item in ranked:
        pattern = (item["case"], item["direction"], tuple(item["legacy_categories"]), tuple(item["common_categories"]),
                   item["first_order_minute"] is None or item["first_order_minute"] > item["start"])
        if pattern in seen:
            continue
        seen.add(pattern)
        chosen.append({"case": item["case"], "scenario": item["scenario"], "minutes": [item["start"], item["end"]],
                       "compared_minutes": item["compared_minutes"], "direction": item["direction"], "max_band_gap": item["max_band_gap"],
                       "legacy_shows": item["legacy_categories"], "snapshot_would_show": item["common_categories"],
                       "actions_before": item["actions_before"],
                       "mechanism_at_start": {key: item["at_start"][key] for key in ("relative_delivery", "F", "collapse_burden", "legacy_sbp", "common_sbp")},
                       "mechanism_at_end": {key: item["at_end"][key] for key in ("relative_delivery", "F", "collapse_burden", "legacy_sbp", "common_sbp")},
                       "coherence": item["coherence"]["verdict"], "faculty_answers": {question: None for question in FACULTY_QUESTIONS}})
        if len(chosen) == limit:
            break
    return chosen


# ============================================================================================================================================
# P3-201: readers of mental_status
# ============================================================================================================================================

KEY = "mental_status"
SKIP_DIRS = {"validation", ".git", "__pycache__", ".claude", "node_modules"}
_NOT_RUNTIME = re.compile(r"^(test_|regression_|tools_)")
DISPLAY, TEXT, BRANCHING, SCORING, TERMINATION, ELIGIBILITY, PERSISTENCE, TEST_DOC = (
    "A_DISPLAY_ONLY", "B_TEXT_GENERATION", "C_CLINICAL_BRANCHING", "D_SCORING", "E_TERMINATION", "F_ORDER_ACTION_ELIGIBILITY",
    "G_PERSISTENCE_SERIALIZATION", "H_TEST_DOC_ONLY")
WRITER, MENTION = "WRITER_NOT_A_READER", "MENTION_NOT_AN_EXECUTABLE_READ"
#: Where a function runs, relative to a GI family encounter under a future pair authority.
GI_TURN, GI_PAGE, GI_AFTER, ARRIVAL, OTHER_FAMILY, OTHER_ENGINE, OFFLINE, COMPARISON = (
    "GI_ENCOUNTER_TURN", "GI_ENCOUNTER_PAGE", "GI_AFTER_THE_ENCOUNTER", "ARRIVAL_ONLY_AUTHORED_BASELINE", "OTHER_FAMILY_OF_THE_LEGACY_ENGINE",
    "OTHER_ENGINE_NOT_THE_FAMILY_ENGINE", "OFFLINE_AUTHORING_RECORD_OR_REPORT", "SHADOW_COMPARISON_ONLY")
LIVE = (GI_TURN, GI_PAGE, GI_AFTER)


def runtime_files(root: str = ROOT) -> list:
    """Every runtime module of the repository (tests, regressions, tools and the validation corpus are not opened)."""
    found = []
    for base, dirs, names in os.walk(root):
        dirs[:] = sorted(name for name in dirs if name not in SKIP_DIRS)
        for name in sorted(names):
            if name.endswith(".py") and not _NOT_RUNTIME.match(name):
                found.append(os.path.join(base, name))
    return found


def scan_readers(root: str = ROOT) -> dict:
    """``{module: {function: [role, ...]}}`` for every syntactic use of the key, and the modules that only mention it in text.

    Roles: READ (``.get(key)``, ``[key]`` loaded, attribute loaded), WRITE (stored, a dict literal's key, a keyword argument), FIELD_LIST (the key
    inside a tuple, list or set of field names), KEY_COMPARE, PARAM, OTHER. A FIELD_LIST is counted as a read: the fields named are read by a loop.

    What this scan CANNOT see is ``SCAN_LIMITS`` below. It finds the literal key; a function that receives the whole observable and walks it
    never names the key and is invisible here. The roles are therefore information, and the CLASS in ``READER_TABLE`` (a reading of the code by
    hand) decides whether a site is an executable reader."""
    sites, text_only = {}, []
    for path in runtime_files(root):
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        if KEY not in source:
            continue
        module = os.path.relpath(path, root)
        tree = ast.parse(source)
        parent = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}

        def owner(node) -> str:
            names = []
            while node in parent:
                node = parent[node]
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.append(node.name)
            return ".".join(reversed(names)) or "<module>"
        found = {}
        for node in ast.walk(tree):
            role = None
            if isinstance(node, ast.Constant) and node.value == KEY:
                above = parent.get(node)
                if isinstance(above, ast.Call) and isinstance(above.func, ast.Attribute) and above.args and above.args[0] is node:
                    role = "WRITE" if above.func.attr == "setdefault" else "READ" if above.func.attr in ("get", "pop") else "OTHER"
                elif isinstance(above, ast.Subscript):
                    role = "WRITE" if isinstance(above.ctx, (ast.Store, ast.Del)) else "READ"
                elif isinstance(above, ast.Dict):
                    role = "WRITE" if node in above.keys else "OTHER"
                elif isinstance(above, (ast.Tuple, ast.List, ast.Set)):
                    role = "FIELD_LIST"
                elif isinstance(above, ast.Compare):
                    role = "KEY_COMPARE"
                else:
                    role = "OTHER"
            elif isinstance(node, ast.keyword) and node.arg == KEY:
                role = "WRITE"
            elif isinstance(node, ast.Attribute) and node.attr == KEY:
                role = "READ" if isinstance(node.ctx, ast.Load) else "WRITE"
            elif isinstance(node, ast.arg) and node.arg == KEY:
                role = "PARAM"
            if role is not None:
                found.setdefault(owner(node), []).append(role)
        if found:
            sites[module] = {name: sorted(roles) for name, roles in sorted(found.items())}
        else:
            text_only.append(module)
    return {"sites": sites, "text_only": sorted(text_only)}


#: What a scan for the literal key cannot see (the independent review of P3-208 showed each with a synthetic module). The audit is an inventory
#: of the sites that NAME the key plus the consumers found by hand; it is not a proof that no other code reads the word.
SCAN_LIMITS = (
    "the key held in a variable or built at run time (an f-string, a .split() of a field string)",
    "a loop over every item of the observable (.items(), ** unpacking, a comparison of the whole observable)",
    "getattr with the key, or a helper that receives the key: found, but as role OTHER",
    "a consumer of a value DERIVED from the word (it never names the key): listed by hand in INDIRECT_CONSUMERS",
)
#: Consumers of a value derived from the word. They do not name the key, so no scan finds them: each is verified to import its source.
INDIRECT_CONSUMERS = {
    "record_findings.py": ("faculty_portal.py", "faculty_report.py", "management_trace_report.py"),
}


def _row(kind, where, consequence, guard=None):
    return {"class": kind, "where": where, "consequence": consequence, "guard": guard}


#: The classification, by module and function. ``*`` is the module's default for a function not listed. A row says what the function does WITH the
#: value and where it runs; ``guard`` is what a future pair authority needs, or None when nothing more than the existing rules is needed.
READER_TABLE = {
    "family_engine.py": {
        "_surface": _row(WRITER, GI_TURN, "the engine RE-WRITES mental_status at every surface from its own ladder (its family state and the authored baseline); "
                         "its reads here are of the baseline, never of the live observable (checked by AST: ``surface_reads``), so a value written by an "
                         "authority never feeds the engine's physiology. It is overwritten by the next turn that ADVANCES the clock: a zero-minute turn "
                         "(a consult) leaves the written word in the state, in the entry and in its observation snapshot"),
        "_arrival_anchors": _row(BRANCHING, ARRIVAL, "reads the AUTHORED arrival level to anchor the engine's thresholds, once"),
        "_pe_attributable": _row(BRANCHING, OTHER_FAMILY, "pulmonary embolism: reads the authored baseline"),
        "_validate": _row(ELIGIBILITY, GI_TURN, "reads the LIVE observable: oral dextrose and oral carbohydrate are refused when the patient is not alert",
                          "both order classes are outside SUPPORTED_ACTIONS: the turn halts the experiment; the order's own outcome in that turn was already decided by the written word"),
        "_order": _row(ELIGIBILITY, GI_TURN, "reads the LIVE observable: an oral antipyretic is withheld when the patient is not Alert or Agitated (and says so in text)",
                       "antipyretic is outside SUPPORTED_ACTIONS: the turn halts the experiment"),
        "_discharge_alarm": _row(TERMINATION, GI_TURN, "reads the LIVE observable after a discharge: a patient who is not awake is 'found ... at home' and brought back (the disposition's outcome)",
                                 "disposition and discharge are outside SUPPORTED_ACTIONS: the turn halts the experiment"),
        "current_findings": _row(TEXT, GI_TURN, "reads the LIVE observable into the examination text the resident reads (general appearance, neurological)",
                                 "resident-visible text: not exposed in any cycle without an explicit decision (FD-AUTH-08)"),
        "clinical_update": _row(TEXT, GI_TURN, "reads the LIVE observable into the clinical update text", "resident-visible text (FD-AUTH-08)"),
    },
    "app.py": {
        "<module>": _row(MENTION, OTHER_ENGINE, "the initial state of the non-family encounters"),
        "build_ps002_state": _row(WRITER, OTHER_ENGINE, "builds another encounter's state"),
        "learner_vitals_snapshot": _row(PERSISTENCE, GI_PAGE, "freezes the learner-visible state, the word included, into each clinical-update event (shown later, stored with the attempt)",
                                        "an experiment's encounter must stay out of resident records"),
        "management_state_snapshot": _row(PERSISTENCE, GI_PAGE, "stores the state before and after each decision in the management trace",
                                          "an experiment's trace must stay out of the resident trace and of any analysis that scores"),
        "observable_state_changed": _row(BRANCHING, GI_PAGE, "decides whether a turn adds a clinical-update card and event: a changed word adds one",
                                         "resident-visible flow (FD-AUTH-08)"),
        "_trace_state_text": _row(TEXT, GI_AFTER, "words the state in the trace review"),
        "_trace_state_words": _row(TEXT, GI_AFTER, "translates the state's words in the trace review"),
        "_trace_observable_delta": _row(TEXT, GI_AFTER, "words what changed between two states in the trace review"),
        "_perfusion_response_direction": _row(TEST_DOC, GI_AFTER, "would classify a response as improve or worsen, but no call site exists in app.py (dead code)"),
        "_expected_response_prompt": _row(BRANCHING, GI_AFTER, "selects and words an adaptive reflection prompt from the change of the word between two states",
                                          "the reflection a resident answers depends on it: an observation OPPORTUNITY changes (not a score by itself)"),
        "_critical_adaptation_prompt": _row(BRANCHING, GI_AFTER, "selects and words an adaptive reflection prompt", "as above"),
        "_reasoning_data_alignment_prompt": _row(BRANCHING, GI_AFTER, "selects and words an adaptive reflection prompt", "as above"),
        "_trajectory_expert_model": _row(BRANCHING, GI_AFTER, "an expert-comparison text reads the word to decide 'impaired perfusion' (written for the sepsis encounters; reach in GI not verified)",
                                         "resident-visible feedback"),
        "_vitals_cells": _row(DISPLAY, GI_PAGE, "the vitals panel and the exported page show the word", "resident-visible display (FD-AUTH-08)"),
        "format_clinical_update": _row(TEXT, GI_PAGE, "the clinical update sentence", "resident-visible text (FD-AUTH-08)"),
        "_clinical_encounter_workspace": _row(ELIGIBILITY, GI_PAGE, "history-taking is unavailable while the word is unresponsive, obtunded or sedated and no collateral source exists",
                                              "an AVAILABLE ACTION changes with the word: the snapshot reads Obtunded from minute 131 and Unresponsive from 158 untreated, where the legacy engine reads Drowsy"),
    },
    "management_trace_analysis.py": {"*": _row(SCORING, GI_AFTER, "the observable scalars of every trace state, the word included, enter the payload of the AI analysis of the management trace",
                                               "INDIRECT scoring evidence: no AI analysis or rubric may run on an authority-experiment encounter, or it must be labelled as one")},
    "faculty_analysis.py": {"*": _row(SCORING, GI_AFTER, "the same observable scalars enter the faculty analysis payload", "as above")},
    "management_trace_portal.py": {"*": _row(DISPLAY, GI_AFTER, "the faculty's trace view lists the field")},
    "management_trace_report.py": {"*": _row(DISPLAY, GI_AFTER, "the trace report lists the field")},
    "cognitive_review.py": {"*": _row(TEXT, GI_AFTER, "names the observation in the cognitive review text")},
    "record_findings.py": {"*": _row(SCORING, GI_AFTER, "``inert_observables`` reads every observed field of the trace, the word among them (label 'alertness'), and "
                                     "``unsettled`` HOLDS an AI suggestion that names a field which never changed: with the legacy word constant the faculty "
                                     "portal shows 'Requires faculty review', with a word that moves the same suggestion is shown as proposed. Consumers: "
                                     "faculty_portal.py, faculty_report.py, management_trace_report.py",
                                     "INDIRECT scoring evidence on the faculty's evaluation surface: no AI analysis on an authority-experiment encounter, or the "
                                     "hold computed on the legacy word; scoring stays legacy")},
    "trace_phase0.py": {"*": _row(PERSISTENCE, GI_AFTER, "the trace schema lists the field")},
    "visual_observations.py": {"*": _row(BRANCHING, GI_PAGE, "the visual profile of the patient changes with the word (obtunded, unresponsive, sedated)",
                                         "resident-visible description and image contract")},
    "patient_appearance.py": {"*": _row(TEXT, GI_PAGE, "the appearance brief and summary carry the word", "resident-visible description and image contract")},
    "image_consistency.py": {"*": _row(BRANCHING, GI_PAGE, "the photographic targets an image must meet depend on the word", "image selection: resident-visible"),
                             "<module>": _row(MENTION, OFFLINE, "a field list")},
    "image_broker.py": {"*": _row(TEXT, GI_PAGE, "the prompt of an image edit carries the word", "an image edit can be a PAID call: image generation must be off in an experiment")},
    "image_bank_portal.py": {"*": _row(DISPLAY, OFFLINE, "the faculty's image bank view")},
    "image_bank.py": {"*": _row(MENTION, OFFLINE, "a constant")},
    "image_pilot.py": {"*": _row(MENTION, OFFLINE, "authored image-pilot states")},
    "pilot_acceptance.py": {"*": _row(TEST_DOC, OFFLINE, "the acceptance battery's own severity reading of a state (a harness, not the runtime)")},
    "asthma_complications.py": {"*": _row(BRANCHING, OTHER_FAMILY, "asthma: exhaustion and intubation timing read the word")},
    "hypoglycemia_battery.py": {"*": _row(TEST_DOC, OFFLINE, "a battery's timeline")},
    "hypoglycemia_catalog.py": {"*": _row(TEST_DOC, OFFLINE, "catalogue contract checks")},
    "catalog_trajectories.py": {"*": _row(TEST_DOC, OFFLINE, "a catalogue reader")},
    "clinical_cases.py": {"*": _row(WRITER, OFFLINE, "authors a case's observable")},
    "clinical_physiology.py": {"*": _row(BRANCHING, OTHER_ENGINE, "the coupled physiology of the non-family encounters reads and writes its own word")},
    "coupled_encounter.py": {"*": _row(BRANCHING, OTHER_ENGINE, "the coupled encounter of the non-family engine")},
    "generated_case.py": {"*": _row(PERSISTENCE, OTHER_ENGINE, "the generated-case engine (not integrated)")},
    "generated_case_capabilities.py": {"*": _row(MENTION, OTHER_ENGINE, "the generated-case engine (not integrated)")},
    "generated_case_schema.py": {"*": _row(TEST_DOC, OTHER_ENGINE, "schema validation of generated cases (not integrated)")},
    "generated_engine.py": {"*": _row(BRANCHING, OTHER_ENGINE, "the generated-case engine (not integrated)")},
    "generated_engine_diagnostics.py": {"*": _row(MENTION, OTHER_ENGINE, "the generated-case engine (not integrated)")},
    "generated_pe.py": {"*": _row(BRANCHING, OTHER_ENGINE, "the generated-case engine (not integrated)")},
    "generated_glucose.py": {"*": _row(WRITER, OTHER_ENGINE, "the generated-case engine's own function of that name (not integrated)")},
    "generated_opioid.py": {"*": _row(WRITER, OTHER_ENGINE, "the generated-case engine's own function of that name (not integrated)")},
    "generated_case_coverage.py": {"*": _row(MENTION, OTHER_ENGINE, "other keys that contain the name (procedural sedation fields)")},
    "case_authoring.py": {"*": _row(MENTION, OFFLINE, "other keys that contain the name (procedural sedation fields)")},
    "runtime_shadow_families.py": {"*": _row(WRITER, OTHER_FAMILY, "the opioid adapter's arrival identity (shadow layer, another family)")},
    "second_live_family_record.py": {"*": _row(MENTION, OFFLINE, "a committed record's field list")},
    "clinical_core/legacy_adapter.py": {
        "snapshot": _row(PERSISTENCE, COMPARISON, "the shadow's per-minute copy of what the legacy engine shows, for comparison only",
                         "under a pair authority the legacy counterfactual must be captured BEFORE the commit, as it is for the pressures"),
        "anchors_from_legacy": _row(BRANCHING, ARRIVAL, "the common core's arrival anchor of the consciousness level, read once when the shadow opens")},
    "clinical_core/comparison.py": {"*": _row(TEST_DOC, COMPARISON, "the certified comparison table")},
}
#: Every other module under ``clinical_core/`` that names the key is a Phase-2 migration, reference, audit or report module: authored arrival
#: values and committed records, read offline. None runs in a GI encounter turn.
CORE_OFFLINE = _row(TEST_DOC, OFFLINE, "a Phase-2 migration, reference, audit or report module: authored arrivals and committed records")


def classify(module: str, function: str) -> dict | None:
    table = READER_TABLE.get(module)
    if table is None:
        return dict(CORE_OFFLINE) if module.startswith("clinical_core/") else None
    return dict(table.get(function) or table.get("*") or {}) or None


def reader_audit(root: str = ROOT) -> dict:
    """The whole P3-201 record: every site with its class, the executable readers of the LIVE observable, their consequences and the verdict."""
    scan = scan_readers(root)
    rows, unclassified = [], []
    for module, functions in scan["sites"].items():
        for function, roles in functions.items():
            found = classify(module, function)
            if found is None:
                unclassified.append(f"{module}::{function}")
                continue
            # The CLASS decides (a reading of the code by hand); the roles are what the scan saw. A site classed A-H is an executable reader
            # whatever role the scan gave it: a key passed to a helper, or a module-level table keyed by the field, reads it too.
            rows.append({"module": module, "function": function, "roles": roles,
                         "executable_read": found["class"] not in (WRITER, MENTION), **found})
    for module in scan["text_only"]:
        found = classify(module, "*")
        if found is None:
            unclassified.append(f"{module}::<text>")
        else:
            rows.append({"module": module, "function": "<text>", "roles": ["TEXT_ONLY"],
                         "executable_read": found["class"] in (SCORING,), **found})
    live = [row for row in rows if row["where"] in LIVE and row["executable_read"]]
    by_class = {}
    for row in live:
        by_class.setdefault(row["class"], []).append(f"{row['module']}::{row['function']}")
    effects = {
        "scenario_flow": sorted(f"{r['module']}::{r['function']}" for r in live if r["class"] in (BRANCHING, TERMINATION)),
        "scoring": sorted(f"{r['module']}::{r['function']}" for r in live if r["class"] == SCORING),
        "available_actions": sorted(f"{r['module']}::{r['function']}" for r in live if r["class"] == ELIGIBILITY),
        "termination": sorted(f"{r['module']}::{r['function']}" for r in live if r["class"] == TERMINATION),
        "resident_visible_text": sorted(f"{r['module']}::{r['function']}" for r in live if r["class"] in (TEXT, DISPLAY)),
        "persistence": sorted(f"{r['module']}::{r['function']}" for r in live if r["class"] == PERSISTENCE),
    }
    indirect = indirect_consumers(root)
    effects["scoring"] = sorted(set(effects["scoring"]) | {f"{consumer}::<consumer of {source}>" for source, found in indirect.items()
                                                           for consumer in found["verified"]})
    surface = surface_reads(root)
    isolated = (not any(effects[name] for name in ("scenario_flow", "scoring", "available_actions", "termination"))
                and not surface["reads_the_live_word"])
    return {"modules_with_a_syntactic_use": len(scan["sites"]), "modules_text_only": scan["text_only"], "sites": len(rows),
            "executable_readers_of_the_live_observable": len(live), "live_readers_by_class": {key: sorted(value) for key, value in sorted(by_class.items())},
            "downstream_effects": effects, "unclassified": unclassified, "rows": rows,
            "indirect_consumers": indirect, "scan_limits": list(SCAN_LIMITS),
            # DERIVED, not asserted: the receivers of every read of the key in the engine's surface function, by AST. A test also plays the
            # encounter twice (the word forced before each turn, and not) and compares the engine's whole state.
            "surface_reads_of_the_key": surface, "legacy_physiology_reads_the_live_word": surface["reads_the_live_word"],
            "verdict": "CONSCIOUSNESS_AUTHORITY_ISOLATED" if isolated else "CONSCIOUSNESS_AUTHORITY_HAS_DOWNSTREAM_SIDE_EFFECTS",
            "required_guards": REQUIRED_GUARDS}


#: The receivers a read of the key may have inside the engine's surface function: the authored baseline of the family state.
BASELINE_RECEIVERS = ("base",)


def surface_reads(root: str = ROOT, source: str | None = None) -> dict:
    """Every read of the key inside ``family_engine._surface``, with the expression it is read FROM. The engine's physiology does not read the
    live word exactly when every receiver is the authored baseline; anything else (``state``, ``o``, an observable) makes it a reader."""
    if source is None:
        with open(os.path.join(root, "family_engine.py"), encoding="utf-8") as handle:
            source = handle.read()
    tree = ast.parse(source)
    function = next((node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_surface"), None)
    receivers = []
    for node in ast.walk(function) if function is not None else ():
        target = None
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("get", "pop") and node.args
                and isinstance(node.args[0], ast.Constant) and node.args[0].value == KEY):
            target = node.func.value
        elif (isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load) and isinstance(node.slice, ast.Constant)
              and node.slice.value == KEY):
            target = node.value
        elif isinstance(node, ast.Attribute) and node.attr == KEY and isinstance(node.ctx, ast.Load):
            target = node.value
        if target is not None:
            receivers.append(ast.unparse(target))
    foreign = sorted({name for name in receivers if name not in BASELINE_RECEIVERS})
    return {"function_found": function is not None, "receivers": sorted(receivers), "not_the_baseline": foreign,
            "reads_the_live_word": function is None or bool(foreign)}


def indirect_consumers(root: str = ROOT) -> dict:
    """For each source of a derived value, the consumers listed by hand and which of them really import that source (by AST)."""
    out = {}
    for source, consumers in INDIRECT_CONSUMERS.items():
        wanted, verified, missing = source[:-3], [], []
        for consumer in consumers:
            try:
                with open(os.path.join(root, consumer), encoding="utf-8") as handle:
                    tree = ast.parse(handle.read())
            except (OSError, SyntaxError):
                missing.append(consumer)
                continue
            imports = any((isinstance(node, ast.Import) and any(alias.name == wanted for alias in node.names))
                          or (isinstance(node, ast.ImportFrom) and node.module == wanted) for node in ast.walk(tree))
            (verified if imports else missing).append(consumer)
        out[source] = {"verified": sorted(verified), "not_found_or_not_importing": sorted(missing)}
    return out


REQUIRED_GUARDS = (
    {"surface": "order and action eligibility in the legacy engine (oral dextrose, oral carbohydrate, oral antipyretic) and the disposition outcome",
     "guard": "already refused: these classes are outside SUPPORTED_ACTIONS, so the turn hard-stops the experiment. To declare: the order's own outcome in the halting turn was decided with the written word.",
     "exists": True},
    {"surface": "history-taking availability on the encounter page (cannot_speak)",
     "guard": "NEW: run the experiment through the scripted harness only (no page), or obtain an explicit faculty acceptance that the available actions follow the common word",
     "exists": False},
    {"surface": "resident-visible text and display (examination findings, clinical update text and cards, vitals panel, visual description)",
     "guard": "NEW: a development-only surface; nothing resident-facing (FD-AUTH-08). These are the intended effect of an authority, so the decision is an exposure decision, not a defect",
     "exists": False},
    {"surface": "image contract and image edit prompt", "guard": "NEW: image generation off in the experiment environment (an edit can be a paid call)", "exists": False},
    {"surface": "management trace and event snapshots (persistence)", "guard": "NEW: an experiment's encounter is marked and kept out of resident records", "exists": False},
    {"surface": "AI and faculty analysis payloads (indirect scoring evidence)",
     "guard": "NEW: no AI analysis and no rubric on an authority-experiment encounter, or a mandatory label; scoring stays legacy", "exists": False},
    {"surface": "the hold of an AI suggestion on the faculty's evaluation surface (record_findings.inert_observables -> faculty portal and reports)",
     "guard": "NEW: found by the independent review of P3-208. The same rule as above, or the hold computed on the legacy word: with a word that moves, a "
              "suggestion the portal holds today ('Requires faculty review') would be shown as proposed", "exists": False},
    {"surface": "adaptive reflection prompts and expert comparison", "guard": "NEW: not shown for an experiment's encounter (no resident), or declared", "exists": False},
    {"surface": "the shadow's own legacy comparison (legacy_adapter.snapshot)", "guard": "NEW in the pair: capture the legacy word BEFORE the commit, as the pressures are", "exists": False},
)


# ============================================================================================================================================
# P3-208: where the layer's authority site is called, read from the source (the independent review found a route it does not cover)
# ============================================================================================================================================

def _function(tree: ast.AST, name: str):
    return next((node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name), None)


def _names_in(node: ast.AST | None) -> set:
    if node is None:
        return set()
    return ({item.attr for item in ast.walk(node) if isinstance(item, ast.Attribute)}
            | {item.id for item in ast.walk(node) if isinstance(item, ast.Name)})


def site_coverage(root: str = ROOT) -> dict:
    """Two facts about the EXISTING pressure authority site, by AST, with no authority enabled:

    1. the engine's clock also moves OUTSIDE an order turn (``app.spend_clinical_time``: a history question, an examination). That route calls the
       shadow (``observe_time``) and never the authority site, and the site has no rule that notices a turn it did not see;
    2. the site reads the shadow's failures of the turn's LAST minute only.

    Neither was exercised by the development series (it plays orders through ``pilot_acceptance.Encounter.order``), so the recertification of
    P3-202 says nothing about them. Both are declared, not changed: the layer is not edited in this cycle."""
    with open(os.path.join(root, "app.py"), encoding="utf-8") as handle:
        app = ast.parse(handle.read())
    with open(os.path.join(root, "runtime_authority.py"), encoding="utf-8") as handle:
        authority_source = handle.read()
    spend = _function(app, "spend_clinical_time")
    spend_names = _names_in(spend)
    callers = sum(1 for node in ast.walk(app) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "spend_clinical_time")
    site_calls = sum(1 for node in ast.walk(app) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                     and node.func.id == "_runtime_authority_site")
    minute = _function(ast.parse(authority_source), "_minute")
    minute_source = ast.unparse(minute) if minute is not None else ""
    return {
        "time_outside_an_order_turn": {
            "route": "app.spend_clinical_time", "callers_in_app": callers, "calls_the_shadow": "observe_time" in spend_names,
            "calls_the_authority_site": "_runtime_authority_site" in spend_names or "site_for" in spend_names,
            "authority_site_call_sites_in_app": site_calls, "the_site_names_the_route": "observe_time" in authority_source,
            "consequence": "with an authority active, a minute that passes on this route keeps the legacy engine's own pressures while the order turns "
                           "carry the common ones: a mixed trajectory the site would not record. The development harness never takes this route.",
            "in_the_dry_transaction": "refused: turn_has_a_transaction_site, and turn_was_observed for any turn the transaction did not see",
            "evidence": "the source, by AST. NOT executed with an authority: this cycle forbids an actual authority, so the consequence is a reading "
                        "of the code and not a measured trajectory"},
        "failures_read_by_the_site": {
            "rule_in_the_site": "_as_int(item.minute) == minute" in minute_source,
            "consequence": "a shadow failure recorded at an intermediate minute of a multi-minute turn would not refuse that turn's commit. Reached "
                           "only by injection so far: in the layer's own paths a failed advance records no later minute.",
            "in_the_dry_transaction": "stricter: every failure the session recorded since the last turn refuses"},
    }


# ============================================================================================================================================
# P3-202: the pressure-authority series on two cores
# ============================================================================================================================================

#: The fields that MAY differ between the closure core and the active core, and why. Anything else that differs is a blocker.
EXPLAINED_DIFFERENCES = {
    "experiment_id": "the identity of the attempt (process-local)",
    "artifact_digest": "the digest of an artifact that carries the fields below",
    "input_digest": "the digest of a replay input that now names the core version and carries two new profile fields",
    "transaction_digest": "takes the input digest",
    "phase3_versions.core_digest": "the active lineage member is named (absent in the closure tree)",
    "phase3_versions.core_version": "the active lineage member is named",
    "phase3_versions.closure_guard_digest": "the closure guard was extended by the two amendments",
    "phase3_versions.phase3_layer_digest": "the Phase-3 layer moved since the closure-core series",
    "replay_input.versions.core_digest": "as above", "replay_input.versions.core_version": "as above",
    "replay_input.versions.closure_guard_digest": "as above", "replay_input.versions.phase3_layer_digest": "as above",
    "replay_input.scenario.profile.amendment_2": "Amendment 2's profile field, OFF (None) in the committed profile",
    "replay_input.scenario.profile.hypoventilation_oxygenation_transmission_fraction": "Amendment 1's profile field, OFF (None) in the committed profile",
    "rollback.phase3_layer_digest": "as above",
}
#: What must be IDENTICAL for the recertification: the physiology written and every digest that does not include a version.
MUST_MATCH = ("common_candidate", "common_pressures", "written_candidate", "legacy_counterfactual", "candidate_digest", "replay_digest", "written_digest",
              "state_digest", "precommit_observable_digest", "outcome", "committed", "moved_fields", "validation_failures", "action_kinds",
              "settled_action_classes", "unsupported_actions", "failure_reason", "minute", "divergence_classes", "action_lineage")


#: The must-match fields the site writes only for a minute that COMMITTED (an aborted minute has no written state and no settlement).
COMMIT_ONLY = ("common_pressures", "state_digest", "moved_fields", "settled_action_classes", "action_lineage")


def _differences(left: Any, right: Any, path: tuple, sink: dict) -> None:
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        for key in sorted(set(left) | set(right)):
            _differences(left.get(key, "<absent>"), right.get(key, "<absent>"), path + (str(key),), sink)
    elif isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        for a, b in zip(left, right):
            _differences(a, b, path, sink)
    elif left != right:
        sink[".".join(path)] = sink.get(".".join(path), 0) + 1


def compare_pressure_series(closure: Mapping, active: Mapping) -> dict:
    """The two dumps of ``test_runtime_authority_series._play_the_battery_with_authority`` (both cases), compared scenario by scenario."""
    a = {(row["case"], row["scenario"]): row for row in closure["rows"]}
    b = {(row["case"], row["scenario"]): row for row in active["rows"]}
    top, fields, minutes_compared, must_match_failures = {}, {}, 0, []
    for key in sorted(set(a) | set(b)):
        left, right = a.get(key), b.get(key)
        if left is None or right is None:
            top.setdefault("scenario_missing", []).append(list(key))
            continue
        for name in ("halted", "halt_reason", "committed", "minutes", "digest_verified", "kinds", "settled_classes"):
            if left[name] != right[name]:
                top.setdefault(name, []).append(list(key))
        _differences({k: v for k, v in left["artifact"].items() if k != "minutes"}, {k: v for k, v in right["artifact"].items() if k != "minutes"}, (), fields)
        ours, theirs = list(left["artifact"]["minutes"]), list(right["artifact"]["minutes"])
        if len(ours) != len(theirs) or [item.get("minute") for item in ours] != [item.get("minute") for item in theirs]:
            top.setdefault("minute_records_differ_in_number_or_order", []).append(list(key))   # zip() below would silently drop the rest
        for one, two in zip(ours, theirs):
            minutes_compared += 1
            _differences(one, two, (), fields)
            for name in MUST_MATCH:
                # An absent field compares equal to itself, so absence is checked: a field must be on both sides, and may be missing from
                # both only where the site writes none (a minute that did not commit has no state it wrote)
                required = name not in COMMIT_ONLY or one.get("outcome") == "COMMITTED" or two.get("outcome") == "COMMITTED"
                if (name in one) != (name in two) or (required and name not in one):
                    must_match_failures.append([list(key), one.get("minute"), f"{name}: ABSENT"])
                elif one.get(name) != two.get(name):
                    must_match_failures.append([list(key), one.get("minute"), name])
    unexplained = sorted(name for name in fields if name not in EXPLAINED_DIFFERENCES)
    if not a or not b or not minutes_compared:
        top.setdefault("nothing_was_compared", []).append([len(a), len(b), minutes_compared])       # an empty series recertifies nothing

    def totals(dump):
        rows = dump["rows"]
        return {"scenarios": len(rows), "completed": sum(1 for r in rows if r["site"] and not r["halted"]), "halted": sum(1 for r in rows if r["halted"]),
                "committed_minutes": sum(r["committed"] or 0 for r in rows), "all_digests_verified": all(r["digest_verified"] for r in rows if r["site"]),
                "replay_covers_every_committed_minute": all((r["replay"] or {}).get("covers_every_committed_minute") for r in rows if r["site"] and not r["halted"]),
                "mixed_trajectory_declared_when_halted_after_a_commit": all(r["artifact"]["mixed_trajectory"] is True
                                                                            for r in rows if r["halted"] and r["committed"])}
    verdict = ("GI_PRESSURE_AUTHORITY_RECERTIFIED_ON_ACTIVE_CORE" if not top and not unexplained and not must_match_failures
               and totals(closure) == totals(active) else "BLOCKED")
    return {"closure": {**{k: closure["meta"][k] for k in ("layer", "authority_module", "phase2_digest", "approved", "failure_policy", "domain", "cases")},
                        "lineage": closure["meta"]["lineage"], **totals(closure)},
            "active": {**{k: active["meta"][k] for k in ("layer", "authority_module", "phase2_digest", "approved", "failure_policy", "domain", "cases")},
                       "lineage": active["meta"]["lineage"], **totals(active)},
            "scenarios_compared": len(set(a) & set(b)), "minute_records_compared": minutes_compared,
            "top_level_differences": top, "differing_fields": {name: {"count": count, "why": EXPLAINED_DIFFERENCES.get(name, "UNEXPLAINED")}
                                                               for name, count in sorted(fields.items())},
            "unexplained_differences": unexplained, "must_match_failures": must_match_failures, "must_match_fields": list(MUST_MATCH),
            "verdict": verdict}
