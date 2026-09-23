"""The history the resident took, and the case the encounter was played on.

Two failures found on 2026-09-23, both of them silent, and both of them about
something the record held that nothing read.

**The history was invisible.** Asking a question is not an order -- it costs no
simulated time and changes no observable -- so it lives in the encounter's
events and not in the Management Trace. Nothing that built an analysis looked
there. A model asked to judge a discharge reported "no explicit medication
history in the encounter": true of what it had been shown, false of the
encounter.

**The authored case was invisible too.** ``case_id_of`` read only the field the
export writes, and a saved session has no such field -- the app stores its
session fields and nothing else. So every real encounter looked like a case
with no declaration: no declared opportunities, and no defined critical events.
Every test that exercised the layer set the export-shaped field by hand, so the
suite was green while the production path was inert.

The faculty's rule, recorded the same day: the patient is present and answers,
so information available on asking was available. A resident who never asked
was not deprived of it; they omitted to obtain it.
"""
import pytest

import history_review
from case_assessment import ASKING_RULE, events as defined_events, verify
from faculty_analysis import case_id_of


def record(events, case_id="hypoglycemia_76f"):
    return {"payload": {"session": {
        "encounter": {"authored_case_id": case_id}, "events": list(events)}}}


def asked(question, answer="An answer.", minute=0):
    return [{"kind": "you", "time": minute, "text": question},
            {"kind": "patient_history", "time": minute, "text": answer}]


# --- the authored case ----------------------------------------------------

def app_shaped_payload():
    """A payload built the way curriculum_runtime saves one, field for field.

    No environment is touched. Setting MRS_OFFLINE_CASES here would withhold
    the provider key for every test that runs after this one in the same
    process, which is how this fixture first broke fifteen unrelated tests.
    """
    from copy import deepcopy
    import curriculum_runtime
    from test_cognitive_encounters import encounter
    from test_curriculum_trajectories import initialize, load_engine
    engine = load_engine()
    generated = encounter(engine, "asthma", "asthma_24f")
    session = initialize(engine, deepcopy(generated["state"]))
    return {"schema_version": curriculum_runtime.PAYLOAD_VERSION,
            "session": {key: session[key] for key in curriculum_runtime.SESSION_FIELDS
                        if key in session}}


def test_the_case_is_found_in_the_payload_the_app_actually_saves():
    # The regression: this returned "" and the rubric lost its whole
    # declaration layer, silently, for every real encounter.
    assert case_id_of({"payload": app_shaped_payload()}) == "asthma_24f"


def test_a_real_encounter_therefore_has_its_defined_critical_events():
    case_id = case_id_of({"payload": app_shaped_payload()})
    assert [event["event_id"] for event in defined_events(case_id)] == [
        "asthma_no_bronchodilator"]


def test_the_export_shaped_field_still_wins_when_it_is_there():
    payload = app_shaped_payload()
    payload["session"]["encounter"] = {"authored_case_id": "pneumonia_83m"}
    assert case_id_of({"payload": payload}) == "pneumonia_83m"


def test_the_frozen_state_is_preferred_to_the_live_one():
    payload = app_shaped_payload()
    payload["session"]["encounter_closed_state"] = {
        "encounter_spec": {"clinical_case": {"id": "opioid_35m"}}}
    assert case_id_of({"payload": payload}) == "opioid_35m"


@pytest.mark.parametrize("payload", [
    {}, {"session": {}}, {"session": {"state": {}}}, {"session": {"state": None}},
    {"session": {"encounter": "not a mapping"}},
    {"session": {"state": {"encounter_spec": {"clinical_case": {}}}}},
])
def test_a_record_without_an_authored_case_says_so_rather_than_guessing(payload):
    assert case_id_of({"payload": payload}) == ""


# --- what was asked -------------------------------------------------------

def test_a_question_and_its_answer_are_read_back_together():
    result = history_review.obtained(record(asked("What medications do you take?",
                                                  "I take glimepiride.", 5)))
    assert result == [{"minute": 5, "asked": "What medications do you take?",
                       "answered": "I take glimepiride."}]


def test_an_examination_is_not_a_question():
    # "Examine: Breathing" is recorded with the same kind as a question, and
    # it belongs to the trace rather than to the history.
    events = [{"kind": "you", "time": 0, "text": "Examine: Breathing"},
              {"kind": "examination", "time": 0, "text": "Respiratory rate 18/min."}]
    assert history_review.obtained(record(events)) == []


def test_an_unanswered_question_is_not_counted_as_a_history():
    assert history_review.obtained(record([{"kind": "you", "time": 0, "text": "Hello?"}])) == []


@pytest.mark.parametrize("question, topic", [
    ("What medications do you take?", "medications"),
    ("¿Qué medicamentos toma?", "medications"),
    ("¿Qué remedios está tomando?", "medications"),
    ("Any allergies?", "allergies"),
    ("¿Tiene alergias?", "allergies"),
    ("When did this start?", "onset"),
    ("¿Hace cuánto empezó?", "onset"),
    ("¿Qué le pasó?", "chief_complaint"),
    ("Do you smoke?", "risk_factors"),
    ("¿Ha comido algo hoy?", "oral_intake"),
    ("¿Ha tenido deposiciones negras?", "bleeding"),
    ("Ask about medications", "medications"),
])
def test_the_question_reaches_the_topic_in_either_language(question, topic):
    assert topic in history_review.topics_named(history_review.obtained(record(asked(question))))


def test_nothing_asked_names_no_topic():
    assert history_review.topics_named([]) == set()


def test_the_topics_nobody_asked_about_are_listed():
    summary = history_review.review(record(asked("¿Qué medicamentos toma?")), "hypoglycemia_76f")
    assert summary["asked_anything"] is True
    assert "medications" in summary["named"]
    assert "Medications" not in [row["label"] for row in summary["not_named"]]
    assert "Allergies" in [row["label"] for row in summary["not_named"]]


def test_an_encounter_with_no_questions_at_all_leaves_every_topic_unasked():
    summary = history_review.review(record([]), "hypoglycemia_76f")
    assert summary["asked_anything"] is False
    assert summary["named"] == []
    assert len(summary["not_named"]) == len(summary["offered"]) > 0


def test_a_generated_case_offers_no_declared_topics_and_does_not_fail():
    summary = history_review.review(record(asked("What medications?"), "not-a-case-id"),
                                    "not-a-case-id")
    assert summary["offered"] == [] and summary["not_named"] == []


def test_the_frozen_events_are_preferred_to_the_live_ones():
    item = record(asked("¿Qué medicamentos toma?"))
    item["payload"]["session"]["encounter_closed_events"] = asked("¿Tiene alergias?")
    assert history_review.obtained(item)[0]["asked"] == "¿Tiene alergias?"


# --- what an event depends on ---------------------------------------------

def test_an_unasked_topic_an_event_turns_on_is_reported_with_what_it_would_tell():
    rows = history_review.unasked_for_events(record([]), "hypoglycemia_76f")
    assert {row["event_id"] for row in rows} == {"hypo_unsafe_discharge"}
    medications = next(row for row in rows if row["topic"] == "medications")
    assert "glimepiride" in medications["tells_them"]


def test_asking_about_it_removes_it():
    rows = history_review.unasked_for_events(
        record(asked("¿Qué medicamentos toma?") + asked("¿Hace cuánto empezó?")),
        "hypoglycemia_76f")
    assert rows == []


# --- the rule the declarations now carry ----------------------------------

def test_the_unsafe_discharge_no_longer_needs_the_resident_to_have_asked():
    event = next(e for e in defined_events("hypoglycemia_76f")
                 if e["event_id"] == "hypo_unsafe_discharge")
    # The history moved out of what the record must contain...
    assert not any("history" in item.lower() for item in event["information_required"])
    # ...and into what the case answers if asked.
    assert dict(event["information_on_asking"])["medications"]
    assert "whether or not the learner asked" in event["trigger"]


def test_every_promised_topic_is_one_its_case_authors():
    # verify() checks it; this states the property the check exists for.
    from case_assessment import matrix
    assert [row["case_id"] for row in matrix() if row["problems"]] == []


def test_a_topic_the_case_does_not_author_is_a_defect_in_the_declaration():
    from case_assessment import _verify_event
    problems = _verify_event(
        {"id": "x"},
        {"event_id": "e", "kind": "critical_omission", "action": "a", "trigger": "t",
         "information_required": ("Arrival observables",), "window_min": (0, 10),
         "alternatives": ("b",), "evidence_required": "c", "exclusions": ("d",),
         "domains": ("D1",), "information_on_asking": (("nonexistent_topic", "something"),)},
        set(), set(), {"medications"})
    assert any("does not author" in problem for problem in problems)


def test_the_rule_is_stated_once_and_travels_with_the_request():
    from rubric_analysis import build_rubric_source, _INSTRUCTIONS
    assert "on asking is available whether or not the learner asked" in ASKING_RULE
    assert "never excuses" in ASKING_RULE
    assert "NEVER excuses an event" in _INSTRUCTIONS


# --- what the documents say -----------------------------------------------

def text_of(blob):
    from io import BytesIO
    from pypdf import PdfReader
    return " ".join(" ".join(page.extract_text() or ""
                             for page in PdfReader(BytesIO(blob)).pages).split())


def learner_document(events, case_id="hypoglycemia_76f"):
    from management_trace_report import render_management_trace_pdf
    from test_management_trace_report import report_example
    report, payload = report_example()
    payload.setdefault("session", {})["events"] = list(events)
    payload["session"].setdefault("encounter", {})["authored_case_id"] = case_id
    return text_of(render_management_trace_pdf(report, payload, case_label="c",
                                               learner_label="l"))


def test_the_learner_sees_what_they_asked_and_what_they_did_not():
    words = learner_document(asked("¿Qué medicamentos toma?", "Tomo glimepirida."))
    assert "The history you took" in words
    assert "¿Qué medicamentos toma?" in words and "Tomo glimepirida." in words
    assert "AVAILABLE AND NOT ASKED ABOUT" in words
    assert "Allergies" in words
    assert "it was not obtained" in words


def test_the_learner_who_asked_nothing_is_told_so_plainly():
    words = learner_document([])
    assert "No question was asked" in words
    assert "Medications" in words


def test_a_topic_that_was_asked_about_is_not_listed_as_unasked():
    words = learner_document(asked("¿Qué medicamentos toma?"))
    unasked = words.split("AVAILABLE AND NOT ASKED ABOUT")[1].split(".")[0]
    assert "Medications" not in unasked
    assert "Allergies" in unasked


def brief(events, *, compact, case_id="hypoglycemia_76f"):
    from faculty_report import render_faculty_brief_pdf
    from test_faculty_report import brief_example
    report, record = brief_example()
    record["payload"].setdefault("session", {})["events"] = list(events)
    record["payload"]["session"].setdefault("encounter", {})["authored_case_id"] = case_id
    return text_of(render_faculty_brief_pdf(report, record, compact=compact))


def test_both_briefs_report_the_history_and_the_gap():
    for compact in (True, False):
        words = brief(asked("¿Qué medicamentos toma?", "Tomo glimepirida."), compact=compact)
        assert "HISTORY OBTAINED" in words, compact
        assert "¿Qué medicamentos toma?" in words, compact
        assert "Available and not asked about" in words, compact
        assert "not a limitation of the record" in words, compact


def test_the_full_brief_carries_the_answers_the_compact_only_counts():
    assert "Tomo glimepirida." in brief(
        asked("¿Qué medicamentos toma?", "Tomo glimepirida."), compact=False)
    assert "question(s) asked" in brief(
        asked("¿Qué medicamentos toma?", "Tomo glimepirida."), compact=True)


def test_an_encounter_with_no_authored_case_and_no_questions_adds_no_section():
    assert "HISTORY OBTAINED" not in brief([], compact=True, case_id="")


# --- what the model is sent -----------------------------------------------

def test_the_analysis_source_carries_the_history_and_the_rule():
    from faculty_analysis import HISTORY_AVAILABILITY, build_analysis_source
    from test_faculty_report import brief_example
    _, item = brief_example()
    item["is_sandbox"] = False
    item["payload"].setdefault("session", {})["events"] = asked(
        "¿Qué medicamentos toma?", "Tomo glimepirida.")
    item["payload"]["session"].setdefault("encounter", {})["authored_case_id"] = "hypoglycemia_76f"
    source = build_analysis_source(item)
    assert source["history_obtained"] == [
        {"minute": 0, "asked": "¿Qué medicamentos toma?", "answered": "Tomo glimepirida."}]
    assert "Allergies" in source["unasked_history_topics"]
    assert "Medications" not in source["unasked_history_topics"]
    assert source["history_availability"] == HISTORY_AVAILABILITY
    assert "an omission of the learner's, not information the record lacked" in HISTORY_AVAILABILITY


def test_the_rubric_source_carries_what_asking_would_have_told_them():
    from rubric_analysis import build_rubric_source
    from test_faculty_report import brief_example
    _, item = brief_example()
    item["is_sandbox"] = False
    item["payload"].setdefault("session", {})["events"] = []
    item["payload"]["session"].setdefault("encounter", {})["authored_case_id"] = "hypoglycemia_76f"
    source = build_rubric_source(item)
    event = next(row for row in source["defined_critical_events"]
                 if row["event_id"] == "hypo_unsafe_discharge")
    offered = {row["history_topic"]: row["tells_them"]
               for row in event["information_available_on_asking"]}
    assert "glimepiride" in offered["medications"]
    assert "never asking is part of the omission" in event["trigger"]
    assert source["information_on_asking_rule"] == ASKING_RULE


# --- what reading a label is allowed to cost ------------------------------

def test_reading_a_topic_label_does_not_import_the_whole_bedside():
    """The deadlock of 2026-09-23, pinned as the property that prevents it.

    ``history_review`` first reached the labels through ``clinical_scene``,
    which imports Streamlit and PIL. A faculty PDF and a rubric declaration
    then imported Streamlit to learn that ``medications`` is called
    "Medications" -- and when one thread imported it while a Streamlit script
    thread already held its import lock, the run stopped for two hours.

    The labels live in ``history_topics``, a leaf with no imports at all.
    """
    import subprocess
    import sys
    from pathlib import Path
    script = ("import sys; import history_review, history_topics;"
              "print(int('streamlit' in sys.modules), int('PIL' in sys.modules),"
              "      len(history_topics.HISTORY_TOPIC_LABELS))")
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                            cwd=str(Path(__file__).parent), timeout=120)
    assert result.returncode == 0, result.stderr
    streamlit, pillow, labels = result.stdout.split()
    assert streamlit == "0" and pillow == "0"
    assert int(labels) == 15


def test_the_bedside_still_offers_the_same_labels_it_always_did():
    import clinical_scene
    import history_topics
    assert clinical_scene.HISTORY_TOPIC_LABELS is history_topics.HISTORY_TOPIC_LABELS
