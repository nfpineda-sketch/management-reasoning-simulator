"""P3-210: the mental_status reader graph, re-derived, with the guard design for every executable reader.

TEST-SIDE. The inventory is REPRODUCED from the source by the P3-201 recorrido (``test_gi_preauthority_review.reader_audit``), not copied: 54 modules
with a syntactic use, 119 sites, 32 executable readers of the live observable. This module adds what P3-210 asks of each of the 32:

* its class in the eleven-class taxonomy of the assignment (``KINDS``);
* P3-210A: what a common-core word in its place could alter -- resident-visible behavior, scoring, scenario state, future available
  actions, AI output, termination;
* P3-210B: its guard type (``observable_view.GUARD_TYPES``) and the mechanism that makes it hold today.

Nothing here reads a consciousness value or runs an encounter. ``test_phase3_dormant_guards.py`` proves the mechanisms.
"""
from __future__ import annotations

import os
from typing import Mapping

import observable_view as view
import test_gi_preauthority_review as review

ROOT = os.path.dirname(os.path.abspath(__file__))

DISPLAY_ONLY, TEXT_GENERATION, CLINICAL_BRANCHING, SCORING, AI_PAYLOAD, FACULTY_PORTAL = (
    "DISPLAY_ONLY", "TEXT_GENERATION", "CLINICAL_BRANCHING", "SCORING", "AI_PAYLOAD", "FACULTY_PORTAL")
ACTION_AVAILABILITY, DISCHARGE, TERMINATION, PERSISTENCE, OTHER = (
    "ACTION_AVAILABILITY", "DISCHARGE", "TERMINATION", "PERSISTENCE", "OTHER")
KINDS = (DISPLAY_ONLY, TEXT_GENERATION, CLINICAL_BRANCHING, SCORING, AI_PAYLOAD, FACULTY_PORTAL, ACTION_AVAILABILITY, DISCHARGE, TERMINATION,
         PERSISTENCE, OTHER)

#: How the isolation holds TODAY for a reader.
ROUTED = "ROUTED_THROUGH_THE_VIEW_AND_FROZEN"
SNAPSHOT = "READS_THE_FROZEN_TRACE_WHICH_THE_ROUTED_SNAPSHOTS_KEEP_LEGACY"
LIVE_FIELD = "READS_THE_LIVE_FIELD_WHICH_NO_TRANSACTION_WRITES"
DEAD = "NO_CALLER"
MECHANISMS = (ROUTED, SNAPSHOT, LIVE_FIELD, DEAD)

CONSEQUENCE_FIELDS = ("resident_visible", "scoring", "scenario_state", "available_actions", "ai_output", "termination")


def _row(kind, guard, mechanism, resident=False, scoring=False, scenario=False, actions=False, ai=False, termination=False, why=""):
    return {"kind": kind, "guard": guard, "mechanism": mechanism, "why": why,
            "consequence": {"resident_visible": resident, "scoring": scoring, "scenario_state": scenario, "available_actions": actions,
                            "ai_output": ai, "termination": termination}}


#: The 32 executable readers. ``module::function`` is the id the audit and ``observable_view`` use.
READER_GUARDS = {
    # The three ENGINE readers cannot be routed in this phase: family_engine.py is a source of the Phase-2 calibration freeze (an edit moves the closure digests; found by
    # this cycle's full suite). They are held by the one thing that can hold them -- no transaction writes the live field, and the writer refuses to -- and they are
    # blockers for any mapping into it (``view.UNROUTED_CONSEQUENTIAL``).
    "family_engine.py::_validate": _row(
        ACTION_AVAILABILITY, view.LATER, LIVE_FIELD, resident=True, scenario=True, actions=True,
        why="oral glucose and oral carbohydrate are refused when the patient is not awake; the order's outcome would change. Frozen by the Phase-2 closure: not routed"),
    "family_engine.py::_order": _row(
        ACTION_AVAILABILITY, view.LATER, LIVE_FIELD, resident=True, scenario=True, actions=True,
        why="an oral antipyretic is withheld from a patient who is not Alert or Agitated, and the message says so. Frozen by the Phase-2 closure: not routed"),
    "family_engine.py::_discharge_alarm": _row(
        DISCHARGE, view.LATER, LIVE_FIELD, resident=True, scenario=True, termination=False,
        why="after a discharge a patient who is not awake is 'found ... at home' and brought back: the disposition's outcome (the encounter continues). "
            "Frozen by the Phase-2 closure: not routed"),
    "app.py::_clinical_encounter_workspace": _row(
        ACTION_AVAILABILITY, view.FREEZE, ROUTED, resident=True, actions=True,
        why="history-taking is unavailable while the word is unresponsive, obtunded or sedated and no collateral source exists"),
    "app.py::observable_state_changed": _row(
        CLINICAL_BRANCHING, view.FREEZE, ROUTED, resident=True, scenario=True,
        why="decides whether a turn adds a clinical-update card and event: a changed word adds one"),
    "app.py::learner_vitals_snapshot": _row(
        PERSISTENCE, view.FREEZE, ROUTED, resident=True, ai=True,
        why="freezes the learner-visible state into each update event, shown later and stored with the attempt"),
    "app.py::management_state_snapshot": _row(
        PERSISTENCE, view.FREEZE, ROUTED, resident=True, scoring=True, ai=True,
        why="the trace every AI analysis, faculty analysis and the retention of an AI suggestion is built from: the choke point of the indirect paths"),
    "app.py::_critical_adaptation_prompt": _row(
        CLINICAL_BRANCHING, view.FREEZE, SNAPSHOT, resident=True,
        why="selects an adaptive reflection prompt from the change of the word between two TRACE states"),
    "app.py::_expected_response_prompt": _row(
        CLINICAL_BRANCHING, view.FREEZE, SNAPSHOT, resident=True, why="as above"),
    "app.py::_reasoning_data_alignment_prompt": _row(
        CLINICAL_BRANCHING, view.FREEZE, SNAPSHOT, resident=True, why="as above"),
    "app.py::_trajectory_expert_model": _row(
        CLINICAL_BRANCHING, view.FREEZE, SNAPSHOT, resident=True, ai=True,
        why="the expert comparison reads the word of the frozen trace to decide 'impaired perfusion'"),
    "app.py::_trace_observable_delta": _row(TEXT_GENERATION, view.FREEZE, SNAPSHOT, resident=True, why="words what changed between two trace states"),
    "app.py::_trace_state_text": _row(TEXT_GENERATION, view.FREEZE, SNAPSHOT, resident=True, why="words a trace state"),
    "app.py::_trace_state_words": _row(TEXT_GENERATION, view.FREEZE, SNAPSHOT, resident=True, why="translates the words of a trace state"),
    "app.py::_perfusion_response_direction": _row(
        OTHER, view.NONE_NEEDED, DEAD, why="would classify a response as improve or worsen, but nothing calls it (dead code)"),
    "app.py::_vitals_cells": _row(
        DISPLAY_ONLY, view.LATER, LIVE_FIELD, resident=True, why="the vitals panel and the exported page show the word"),
    "app.py::format_clinical_update": _row(
        TEXT_GENERATION, view.LATER, LIVE_FIELD, resident=True, why="the clinical-update sentence"),
    "family_engine.py::current_findings": _row(
        TEXT_GENERATION, view.LATER, LIVE_FIELD, resident=True, why="the general appearance and neurological findings the resident reads"),
    "family_engine.py::clinical_update": _row(TEXT_GENERATION, view.LATER, LIVE_FIELD, resident=True, why="the clinical-update text"),
    "patient_appearance.py::appearance_summary": _row(
        TEXT_GENERATION, view.LATER, LIVE_FIELD, resident=True, why="the appearance summary the resident reads"),
    "patient_appearance.py::contract_brief": _row(
        CLINICAL_BRANCHING, view.LATER, LIVE_FIELD, resident=True,
        why="the brief of the image contract: what an image must show depends on the word (an image edit can be a paid call)"),
    "image_broker.py::edit_prompt": _row(
        TEXT_GENERATION, view.LATER, LIVE_FIELD, resident=True, why="the prompt of an image edit carries the word (can be a paid call)"),
    "image_consistency.py::photographic_targets": _row(
        CLINICAL_BRANCHING, view.LATER, LIVE_FIELD, resident=True, why="the photographic targets an image must meet depend on the word"),
    "visual_observations.py::visual_observations": _row(
        CLINICAL_BRANCHING, view.LATER, LIVE_FIELD, resident=True, why="the visual profile of the patient changes with the word"),
    "visual_observations.py::<module>": _row(
        CLINICAL_BRANCHING, view.LATER, LIVE_FIELD, resident=True, why="the module's table of visual descriptors keyed by the word"),
    "cognitive_review.py::<module>": _row(TEXT_GENERATION, view.FREEZE, SNAPSHOT, resident=True, why="names the observation in the cognitive review text, from the trace"),
    "trace_phase0.py::observation_snapshot": _row(
        PERSISTENCE, view.FREEZE, ROUTED, resident=True, ai=True,
        why="stores what the resident saw in EVERY Management-Trace event. P3-219 review (F4): the first audit called this row a snapshot of the routed readers; it "
            "is a reader of the live observable of its own (a dynamic key over a tuple), and it is now routed through the view"),
    "management_trace_portal.py::render_management_trace_analysis": _row(
        FACULTY_PORTAL, view.FREEZE, SNAPSHOT, ai=True, why="the faculty's trace view lists the field from the trace"),
    "management_trace_report.py::<module>": _row(FACULTY_PORTAL, view.FREEZE, SNAPSHOT, ai=True, why="the trace report lists the field from the trace"),
    "record_findings.py::<module>": _row(
        FACULTY_PORTAL, view.FREEZE, SNAPSHOT, scoring=True, ai=True,
        why="inert_observables reads every observed field of the TRACE, the word among them, and unsettled() HOLDS an AI suggestion that names a field "
            "which never changed: the faculty portal's retention rule (found by the P3-208 review)"),
    "faculty_analysis.py::<text>": _row(
        AI_PAYLOAD, view.FREEZE, SNAPSHOT, scoring=True, ai=True, why="the observable scalars of every trace state, the word included, enter the faculty analysis payload"),
    "management_trace_analysis.py::<text>": _row(
        AI_PAYLOAD, view.FREEZE, SNAPSHOT, scoring=True, ai=True, why="the same scalars enter the payload of the AI analysis of the management trace"),
}


def live_reader_ids(root: str = ROOT) -> list:
    """The executable readers of the live observable, REPRODUCED from the source by the P3-201 recorrido (not read from a record)."""
    audit = review.reader_audit(root)
    return sorted(f"{row['module']}::{row['function']}" for row in audit["rows"]
                  if row["where"] in review.LIVE and row["executable_read"])


def inventory(root: str = ROOT) -> dict:
    audit = review.reader_audit(root)
    return {"modules_with_a_syntactic_use": audit["modules_with_a_syntactic_use"], "modules_text_only": len(audit["modules_text_only"]),
            "sites": audit["sites"], "executable_readers": audit["executable_readers_of_the_live_observable"], "unclassified": audit["unclassified"]}


def by_kind(table: Mapping = READER_GUARDS) -> dict:
    out = {kind: [] for kind in KINDS}
    for reader, row in sorted(table.items()):
        out[row["kind"]].append(reader)
    return out


def consequences(table: Mapping = READER_GUARDS) -> dict:
    """P3-210A in one place: for each consequence, the readers a common-core word could alter, and how each is held today."""
    return {name: sorted(reader for reader, row in table.items() if row["consequence"][name]) for name in CONSEQUENCE_FIELDS}
