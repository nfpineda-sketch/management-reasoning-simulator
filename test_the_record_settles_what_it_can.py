"""Three findings of the 2026-09-24 batch, reproduced offline and held in place.

(a) Encounter 7: ``opioid_no_ventilatory_support`` was proposed and confirmed
    although the resident had ventilated with a bag and mask and given
    naloxone inside the window -- and the model had written, in its own
    exclusion check, that the omission was not present.
(b) Encounter 8: an embolism was thrombolysed and never anticoagulated, and
    ``pe_no_anticoagulation`` was never proposed: the schema had room only for
    the events the model chose to name.
(c) "Not assessable" was never used, including in an encounter that closed at
    13 minutes without a destination.

Every encounter here is played through the production interpreter and engine
with the provider key withheld. Nothing opens a socket.
"""
import pytest

import rubric
import rubric_presentation
import rubric_screening
from account_store import AccountError
from faculty_analysis import source_fingerprint
from rubric_analysis import (LEGACY_PROMPT_VERSION, PROMPT_VERSION, SCHEMA_VERSION,
                             build_rubric_source, case_id_of, proposed_event_rows,
                             validate_rubric_proposal)
from rubric_store import build_review
from tools_rubric_runs import BY_ID, play, play_orders


REFLECTION = {"working_model_update": "x", "priority_trigger": "x",
              "alternative_action": "x", "expected_response_reassessment": "x"}


def _script(case_id, family, orders):
    return {"case_id": case_id, "family": family, "orders": orders,
            "reflection": REFLECTION, "plan": {"next_priority": "x"}, "intent": "test"}


def _domains(record, scores, opportunity=None):
    refs = sorted(build_rubric_source(record)["decision_events"][0:1] and
                  [row["evidence_ref"] for row in build_rubric_source(record)["decision_events"]
                   if row["evidence_ref"]])
    rows = []
    for domain in rubric.DOMAIN_IDS:
        value = scores.get(domain, 2)
        rows.append({
            "domain_id": domain, "score": value,
            "evidence_refs": [] if value == rubric.NOT_ASSESSABLE else refs[:1],
            "learner_evidence": [], "rationale": "Stated in the record.",
            "contrary_evidence": "None.", "limits": "None.",
            "opportunity": (opportunity or {}).get(
                domain, "no_opportunity" if value == rubric.NOT_ASSESSABLE else "observed"),
            "next_level_gap": "Targets were not set.",
        })
    return rows, refs


def proposal_1_1(record, *, occurred=(), scores=None, reasons=None):
    rows, refs = _domains(record, scores or {})
    events = build_rubric_source(record)["defined_critical_events"]
    body = {"domains": rows, "concerns_for_review": [], "assistance_recorded": [],
            "record_limits": []}
    if events:
        body["event_verdicts"] = {e["event_id"]: {
            "verdict": "occurred" if e["event_id"] in occurred else "did_not_occur",
            "evidence_refs": refs[:1],
            "trigger_evidence": (reasons or {}).get(e["event_id"], "The record shows it."),
            "exclusions_checked": "Checked."} for e in events}
    return validate_rubric_proposal({
        "schema_version": SCHEMA_VERSION, "prompt_version": PROMPT_VERSION,
        "rubric_version": rubric.VERSION, "coverage_version": "1.0",
        "source_hash": source_fingerprint(record), "attempt_id": record["id"],
        "attempt_revision": record["revision"], "generated_at": "2026-09-24T00:00:00+00:00",
        "model": "stub", "assistance_context": "unknown", "case_id": case_id_of(record),
        "proposal": body}, record)


def proposal_1_0(record, events, exclusions_checked):
    """The shape encounter 7 was proposed in, with its own sentence."""
    rows, refs = _domains(record, {})
    for row in rows:
        row.pop("opportunity")
        row.pop("next_level_gap")
    body = {"domains": rows, "concerns_for_review": [], "assistance_recorded": [],
            "record_limits": [],
            "critical_events": [{"event_id": event_id, "evidence_refs": refs[:1],
                                 "trigger_evidence": "The respiratory rate was depressed.",
                                 "exclusions_checked": exclusions_checked} for event_id in events]}
    return validate_rubric_proposal({
        "schema_version": SCHEMA_VERSION, "prompt_version": LEGACY_PROMPT_VERSION,
        "rubric_version": rubric.VERSION, "coverage_version": "1.0",
        "source_hash": source_fingerprint(record), "attempt_id": record["id"],
        "attempt_revision": record["revision"], "generated_at": "2026-09-24T00:00:00+00:00",
        "model": "stub", "assistance_context": "independent", "case_id": case_id_of(record),
        "proposal": body}, record)


ENCOUNTER_7_SENTENCE = (
    "Exclusion applies: the trigger condition (depressed RR) was present but support/reversal "
    "actions were executed within the window, so the critical omission is not present.")


@pytest.fixture(scope="module")
def ventilated_and_reversed():
    record, _ = play("opioid_67f")
    return record


# --- (a) the event proposed against its own words ---------------------------
def test_the_record_contradicts_the_opioid_omission_when_support_was_given(ventilated_and_reversed):
    screen = {row["event_id"]: row for row in
              rubric_screening.screen_events(ventilated_and_reversed, "opioid_67f")}
    row = screen["opioid_no_ventilatory_support"]
    assert row["status"] == "contradicted"
    text = " ".join(fact["en"] for fact in row["facts"])
    assert text == ("Executed inside the window 0-20 min: bag-mask ventilation at 0 min (D1); "
                    "naloxone at 5 min (D2).")
    assert row["refs"] == ["trace:0", "trace:1"]
    # The same facts in the reviewer's language.
    assert " ".join(f["es"] for f in row["facts"]) == (
        "Ejecutado dentro de la ventana 0-20 min: ventilación con bolsa-mascarilla a los 0 min (D1); "
        "naloxona a los 5 min (D2).")


def test_encounter_7_as_it_was_proposed_is_flagged_twice(ventilated_and_reversed):
    report = proposal_1_0(ventilated_and_reversed, ("opioid_no_ventilatory_support",),
                          ENCOUNTER_7_SENTENCE)
    result = rubric_screening.screening(ventilated_and_reversed, "opioid_67f")
    kinds = {(flag["kind"], flag.get("event_id")) for flag in
             rubric_screening.proposal_flags(report, result)}
    assert ("event_contradicted", "opioid_no_ventilatory_support") in kinds
    assert ("event_self_excluded", "opioid_no_ventilatory_support") in kinds


def test_confirming_an_event_the_record_contradicts_needs_a_written_reason(ventilated_and_reversed):
    """Nothing confirms that penalty silently any more, not even a reviewer in a hurry."""
    report = proposal_1_0(ventilated_and_reversed, ("opioid_no_ventilatory_support",),
                          ENCOUNTER_7_SENTENCE)
    screening = rubric_screening.screening(ventilated_and_reversed, "opioid_67f")
    decision = {"case_id": "opioid_67f", "scores": {d: 2 for d in rubric.DOMAIN_IDS},
                "reasons": {}, "justifications": {}, "status": "confirmed",
                "proposal": report, "screening": screening}
    with pytest.raises(AccountError, match="record contradicts"):
        build_review(events=[{"event_id": "opioid_no_ventilatory_support", "status": "confirmed",
                              "justification": ""},
                             {"event_id": "opioid_unsafe_discharge", "status": "dismissed",
                              "justification": "Observation was not stated but not asked here."}],
                     **decision)
    dismissed = build_review(events=[{"event_id": "opioid_no_ventilatory_support",
                                      "status": "dismissed", "justification": ""}], **decision)
    assert dismissed["totals"]["penalty"] == 0
    kept = build_review(events=[{"event_id": "opioid_no_ventilatory_support", "status": "confirmed",
                                 "justification": "Reviewed: the support was late in my reading."}],
                        **decision)
    assert kept["critical_events"][0]["record_contradicts"] is True
    assert kept["totals"]["penalty"] == rubric.CRITICAL_EVENT_PENALTY


def test_a_1_1_proposal_puts_the_same_reading_in_its_verdict(ventilated_and_reversed):
    """With a verdict for every event, the sentence of encounter 7 has a place to go."""
    report = proposal_1_1(ventilated_and_reversed, occurred=("opioid_unsafe_discharge",))
    assert [row["event_id"] for row in proposed_event_rows(report)] == ["opioid_unsafe_discharge"]
    result = rubric_screening.screening(ventilated_and_reversed, "opioid_67f")
    assert not [flag for flag in rubric_screening.proposal_flags(report, result)
                if flag.get("event_id") == "opioid_no_ventilatory_support"]


# --- (b) the event whose trigger was in the record and never proposed -------
@pytest.fixture(scope="module")
def recognised_never_anticoagulated():
    record, _ = play("pulmonary_embolism_61m")
    return record


def test_an_embolism_never_anticoagulated_has_its_trigger_met(recognised_never_anticoagulated):
    screen = {row["event_id"]: row for row in
              rubric_screening.screen_events(recognised_never_anticoagulated, "pulmonary_embolism_61m")}
    assert screen["pe_no_anticoagulation"]["status"] == "met"


def test_the_model_can_no_longer_skip_it_and_a_skip_is_flagged(recognised_never_anticoagulated):
    report = proposal_1_1(recognised_never_anticoagulated,
                          reasons={"pe_no_anticoagulation": "There is no recorded anticoagulation."})
    result = rubric_screening.screening(recognised_never_anticoagulated, "pulmonary_embolism_61m")
    flags = [flag for flag in rubric_screening.proposal_flags(report, result)
             if flag.get("event_id") == "pe_no_anticoagulation"]
    assert [flag["kind"] for flag in flags] == ["event_not_proposed"]
    assert flags[0]["model_verdict"] == "did_not_occur"
    assert "There is no recorded anticoagulation." in flags[0]["model_reason"]


def test_a_thrombolysed_embolism_is_left_to_the_reading_the_definition_needs():
    """Encounter 8's shape. Faculty decision 7 of 2026-09-25: a thrombolysis does not
    remove the anticoagulation decision. Here the thrombolysis was the last decision
    before the close, so no later decision could show a plan: the faculty reads it."""
    record, transcript = play_orders(_script("pulmonary_embolism_61m", "pulmonary_embolism", [
        "Creo que es un tromboembolismo pulmonar de alto riesgo con shock obstructivo, porque "
        "esta hipotenso, taquicardico e hipoxemico. Mi prioridad es reperfundir. Doy "
        "tenecteplase 50 mg ev. Espero que suba la presion y mejore la oxigenacion. "
        "Reevaluo en 10 minutos.",
    ]))
    screen = {row["event_id"]: row for row in
              rubric_screening.screen_events(record, "pulmonary_embolism_61m")}
    row = screen["pe_no_anticoagulation"]
    assert row["status"] == "reading", transcript
    text = " ".join(fact["en"] for fact in row["facts"])
    assert "thrombolysis" in text and "anticoagulation" in text
    assert "no later decision in which an anticoagulation plan could be observed" in text
    report = proposal_1_1(record)
    kinds = {flag["kind"] for flag in rubric_screening.proposal_flags(
        report, rubric_screening.screening(record, "pulmonary_embolism_61m"))
        if flag.get("event_id") == "pe_no_anticoagulation"}
    assert kinds == {"event_to_read"}


# --- (c) a window that never opened is not a zero ---------------------------
@pytest.fixture(scope="module")
def closed_at_thirteen():
    script = _script("pulmonary_embolism_61m", "pulmonary_embolism", [
        "Creo que es un tromboembolismo pulmonar, porque tiene disnea subita, taquicardia e "
        "hipoxemia. Mi prioridad es oxigenar y confirmar. Doy oxigeno por mascarilla a 15 L/min; "
        "pido POCUS. Espero que suba la saturacion. Reevaluo en 10 minutos.",
        "Pido angiotomografia de torax; pido dimero D",
        "Examino las extremidades",
    ])
    record, _ = play_orders(script)
    return record


def test_the_fifth_domain_had_no_window_when_the_encounter_closed_at_thirteen(closed_at_thirteen):
    rows = {row["domain_id"]: row for row in
            rubric_screening.screen_domains(closed_at_thirteen, "pulmonary_embolism_61m")}
    assert rubric_screening.facts(closed_at_thirteen, "pulmonary_embolism_61m")["closed_at"] == 13
    assert rows["D5"]["window_opened"] is False and rows["D5"]["suggestion"] == "no_opportunity"
    # The fourth domain's window had opened: the early closure is evidence there.
    assert rows["D4"]["window_opened"] is True and rows["D4"]["suggestion"] is None
    text = " ".join(fact["es"] for fact in rows["D5"]["facts"])
    assert "no evaluable" in text and "no un cero" in text
    # Support, never the criterion (faculty decision 8, 2026-09-25).
    assert "la ventana es un apoyo, no el criterio" in text


def test_scoring_a_domain_that_never_opened_is_flagged(closed_at_thirteen):
    report = proposal_1_1(closed_at_thirteen, scores={"D5": 1})
    result = rubric_screening.screening(closed_at_thirteen, "pulmonary_embolism_61m")
    flags = [flag for flag in rubric_screening.proposal_flags(report, result)
             if flag["kind"] == "domain_without_opportunity"]
    assert [(flag["domain_id"], flag["score"]) for flag in flags] == [("D5", 1)]
    # "Not assessable" on the same domain raises nothing.
    clean = proposal_1_1(closed_at_thirteen, scores={"D5": rubric.NOT_ASSESSABLE})
    assert not [flag for flag in rubric_screening.proposal_flags(clean, result)
                if flag["kind"] == "domain_without_opportunity"]


def test_the_reviewer_is_offered_the_record_reason_and_the_total_stays_partial(closed_at_thirteen):
    report = proposal_1_1(closed_at_thirteen, scores={"D5": 1})
    check = rubric_presentation.record_check(report, closed_at_thirteen, "es")
    assert check["domains"]["D5"]["suggestion"] == "no_opportunity"
    assert any("no evaluable" in fact for fact in check["domains"]["D5"]["facts"])
    assert [flag["label"] for flag in check["flags"] if flag["kind"] == "domain_without_opportunity"]
    review = build_review(case_id="pulmonary_embolism_61m",
                          scores={**{d: 2 for d in ("D1", "D2", "D3", "D4")},
                                  "D5": rubric.NOT_ASSESSABLE},
                          reasons={"D5": " ".join(check["domains"]["D5"]["facts"])},
                          events=[{"event_id": "pe_no_anticoagulation", "status": "dismissed",
                                   "justification": "Closed before the window ended."}],
                          justifications={"D5": "Window never opened."}, status="confirmed",
                          proposal=report)
    # Four domains carry a number and there is no comparable total: never a zero.
    assert review["totals"]["coverage"] == {"assessed": 4, "total": 5, "complete": False}
    assert review["totals"]["adjusted"] is None


# --- the documents say it too, without changing a number --------------------
def test_the_rubric_document_prints_the_disagreement(ventilated_and_reversed):
    from rubric_report import build_rubric_document
    report = proposal_1_0(ventilated_and_reversed, ("opioid_no_ventilatory_support",),
                          ENCOUNTER_7_SENTENCE)
    review = build_review(case_id="opioid_67f", scores={d: 2 for d in rubric.DOMAIN_IDS},
                          reasons={}, events=[], justifications={}, status="draft",
                          proposal=report)
    flow, assessment = build_rubric_document(review, report, ventilated_and_reversed, language="es")
    text = " ".join(getattr(item, "text", "") for item in flow)
    assert "LA PROPUESTA Y EL REGISTRO NO COINCIDEN" in text
    assert "El registro lo contradice" in text
    assert assessment["totals"]["penalty"] == 0


def test_every_pilot_script_screens_as_its_intent_says():
    """The thirteen scripts of the pilot, each written to provoke one event."""
    expected = {
        "gi_bleed_72f": ("gi_no_resuscitation", "met"),
        "hypoglycemia_54m_thiamine": ("hypo_no_thiamine", "met"),
        "pneumonia_83m": ("pneumonia_unexamined_altered_state", "met"),
        "pulmonary_embolism_61m": ("pe_no_anticoagulation", "met"),
        "hypoglycemia_76f": ("hypo_unsafe_discharge", "reading"),
        "opioid_67f": ("opioid_unsafe_discharge", "reading"),
        "pulmonary_edema_58m": ("edema_volume_loading", "reading"),
        "asthma_49m": ("asthma_no_ventilatory_support", "reading"),
        "opioid_35m": ("opioid_no_ventilatory_support", "contradicted"),
        "asthma_24f": ("asthma_no_bronchodilator", "contradicted"),
        "gi_bleed_57m": ("gi_no_resuscitation", "contradicted"),
    }
    for case_id, (event_id, status) in expected.items():
        assert case_id in BY_ID
        record, _ = play(case_id)
        screen = {row["event_id"]: row["status"] for row in
                  rubric_screening.screen_events(record, case_id)}
        assert screen[event_id] == status, (case_id, screen)


# --- faculty decision 7 of 2026-09-25: a thrombolysis does not remove the anticoagulation decision

def _lysis_trace(*entries):
    from family_parser import parse_family_actions
    trace = []
    for text, minute, executed in entries:
        parsed = parse_family_actions(text)
        trace.append({"execution_status": "executed", "decision_time_min": minute, "response_time_min": minute + 5,
                      "learner_input": text, "interpreted_action": parsed["actions"],
                      "action_summaries": [{"type": kind, "label": kind} for kind in executed],
                      "recognized_future_actions": parsed["recognized_future_actions"],
                      "future_details": parsed["future_details"]})
    return {"payload": {"session": {"management_trace": trace}}}


@pytest.mark.parametrize("entries, status, said", [
    ([("Doy tenecteplase 50 mg ev. Al terminar inicio heparina.", 10, ("thrombolysis",)),
      ("Reevaluo en 10 minutos", 20, ())], "reading", "a documented plan, execution pending"),
    ([("Doy tenecteplase 50 mg ev. Difiero la anticoagulacion por sangrado activo.", 10, ("thrombolysis",))],
     "reading", "An explicit reason to defer anticoagulation was stated"),
    ([("Doy tenecteplase 50 mg ev.", 10, ("thrombolysis",)), ("Reevaluo en 20 minutos", 25, ()),
      ("Lo hospitalizo en UCI", 45, ("disposition",))], "met", "an omission the record demonstrates"),
])
def test_a_plan_a_deferral_and_an_omission_are_told_apart(entries, status, said):
    row = {r["event_id"]: r for r in rubric_screening.screen_events(
        _lysis_trace(*entries), "pulmonary_embolism_61m")}["pe_no_anticoagulation"]
    assert row["status"] == status
    assert said in " ".join(fact["en"] for fact in row["facts"])


def test_no_universal_minute_decides_it():
    """The omission rests on later decisions without a plan, never on minutes elapsed."""
    early = _lysis_trace(("Doy tenecteplase 50 mg ev.", 10, ("thrombolysis",)), ("Reevaluo en 5 minutos", 12, ()))
    row = {r["event_id"]: r for r in rubric_screening.screen_events(early, "pulmonary_embolism_61m")}[
        "pe_no_anticoagulation"]
    assert row["status"] == "met"
