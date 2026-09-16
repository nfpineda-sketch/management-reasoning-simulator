"""Learner synthesis lifecycle in the actual Streamlit renderer, without API calls."""

import ast
from copy import deepcopy
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader
from streamlit.testing.v1 import AppTest

from management_trace_analysis import ManagementTraceAnalysisError, build_analysis_source
import management_trace_portal as portal
import management_trace_report as renderer
from test_management_trace_analysis import sample_payload, sample_report
from test_management_trace_report import report_example
from test_management_trace_store import cohort, current_report


PORTAL_SCRIPT = """
import streamlit as st
from management_trace_portal import render_management_trace_analysis
result = render_management_trace_analysis(
    st.session_state['source_payload'], api_key=st.session_state.get('test_api_key', ''),
    model='test-only-model', context=st.session_state.get('test_context'),
    case_label='Synthetic portal encounter',
    review_completed=st.session_state.get('test_review_completed', False),
    adaptation_plan=st.session_state.get('test_adaptation', {}),
)
st.session_state['test_rendered_report'] = result
"""


def make_app(source=None, *, context=None, attempt_id=None, completed=False):
    app = AppTest.from_string(PORTAL_SCRIPT, default_timeout=20)
    app.session_state["source_payload"] = source or sample_payload()
    app.session_state["test_api_key"] = "TEST_ONLY_NOT_A_REAL_KEY"
    app.session_state["test_review_completed"] = completed
    if context:
        app.session_state["test_context"] = context
    if attempt_id:
        app.session_state["_attempt_id"] = attempt_id
    return app


def displayed_text(app):
    return "\n".join(str(item.value) for kind in ("markdown", "caption", "info", "error", "subheader")
                     for item in app.get(kind))


def downloads(app):
    return [item for item in app.get("download_button") if item.proto.label == "Download Management Trace PDF"]


def cached_pdf(app):
    values = [value for key, value in app.session_state.to_dict().items()
              if key.startswith("_learner_trace_") and "_pdf_" in key]
    assert values and all(isinstance(value, bytes) for value in values)
    return values[-1]


def generation_spy(monkeypatch, *, fail_first=False):
    calls = []

    def generate(payload, **kwargs):
        calls.append(deepcopy(payload))
        if fail_first and len(calls) == 1:
            raise ManagementTraceAnalysisError("AI analysis is temporarily unavailable. Original evidence is preserved.")
        return sample_report(payload)

    monkeypatch.setattr(portal, "generate_management_trace_analysis", generate)
    return calls


def test_no_ai_request_before_lock_then_one_request_and_pdf_reused(monkeypatch):
    calls = generation_spy(monkeypatch)
    pdf_calls = []
    original_renderer = renderer.render_management_trace_pdf

    def render(*args, **kwargs):
        pdf_calls.append(kwargs)
        return original_renderer(*args, **kwargs)

    monkeypatch.setattr(renderer, "render_management_trace_pdf", render)
    source = sample_payload()
    source["reflection_locked"] = False
    app = make_app(source).run()
    assert not app.exception
    assert calls == [] and pdf_calls == [] and downloads(app) == []
    source["reflection_locked"] = True
    app.session_state["source_payload"] = source
    app.run()
    assert not app.exception
    assert len(calls) == len(pdf_calls) == 1
    assert len(downloads(app)) == 1
    assert "Your Management Trace" in displayed_text(app)
    first_pdf = cached_pdf(app)
    app.run()
    assert not app.exception
    assert len(calls) == len(pdf_calls) == 1
    assert cached_pdf(app) == first_pdf
    app.session_state["test_adaptation"] = {"cue": "Look again at breathing effort."}
    app.run()
    assert len(calls) == 1 and len(pdf_calls) == 2
    texts = ["\n".join(page.extract_text() for page in PdfReader(BytesIO(data)).pages)
             for key, data in app.session_state.to_dict().items() if "_pdf_" in key]
    assert any("Look again at breathing effort." in text for text in texts)


def test_provider_failure_has_explicit_retry_and_never_presents_a_template_as_ai(monkeypatch):
    calls = generation_spy(monkeypatch, fail_first=True)
    source = sample_payload()
    source["faculty_brief"] = {"recommendation": "PRIVATE_FACULTY_INFORMATION"}
    source["trace"][0]["state_before"]["hidden"] = {"diagnosis": "PRIVATE_CASE_INFORMATION"}
    app = make_app(source).run()
    assert not app.exception
    assert len(calls) == 1 and downloads(app) == []
    assert "temporarily unavailable" in displayed_text(app)
    app.run()
    assert not app.exception and len(calls) == 1
    retry = next(item for item in app.button if item.label == "Retry Management Trace analysis")
    retry.click().run()
    assert not app.exception and len(calls) == 2 and len(downloads(app)) == 1
    assert "PRIVATE_" not in displayed_text(app)
    text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(cached_pdf(app))).pages)
    assert "PRIVATE_" not in text


def test_analysis_and_pdf_survive_active_to_saved_review_without_another_ai_request(cohort, monkeypatch):
    accounts, store, users = cohort
    attempt_id, _, _ = current_report(cohort, completed=False)
    context = {"user": {"id": users["resident"]["id"], "role": "resident"},
               "token": users["resident"]["token"], "store": accounts}
    calls = generation_spy(monkeypatch)
    active = make_app(context=context, attempt_id=attempt_id).run()
    assert not active.exception and len(calls) == 1 and len(downloads(active)) == 1
    saved_report = store.get_latest(context["token"], attempt_id)
    assert saved_report is not None
    record = accounts.get_attempt(context["token"], attempt_id)
    accounts.save_attempt(context["token"], attempt_id, record["payload"], status="completed")
    saved = make_app(context=context, attempt_id=attempt_id, completed=True)
    saved.session_state["test_api_key"] = ""
    saved.run()
    assert not saved.exception and len(calls) == 1 and len(downloads(saved)) == 1
    text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(cached_pdf(saved))).pages)
    assert "REVIEW COMPLETE" in text
    assert saved.session_state["test_rendered_report"] == saved_report
    saved.run()
    assert not saved.exception and len(calls) == 1


def test_unauthorized_account_cannot_reuse_the_owner_pdf_cache(cohort, monkeypatch):
    accounts, store, users = cohort
    attempt_id, report, _ = current_report(cohort)
    store.save(users["resident"]["token"], attempt_id, report)
    context = {"user": {"id": users["resident"]["id"], "role": "resident"},
               "token": users["resident"]["token"], "store": accounts}
    calls = generation_spy(monkeypatch)
    app = make_app(context=context, attempt_id=attempt_id).run()
    assert not app.exception and len(downloads(app)) == 1 and calls == []
    context["token"] = users["other"]["token"]
    app.session_state["test_context"] = context
    app.run()
    assert not app.exception and downloads(app) == [] and calls == []
    assert "not available to your account" in displayed_text(app)


def test_long_study_and_xml_like_learner_text_remain_viewable_and_downloadable(monkeypatch):
    report, source = report_example()
    source["trace"][0]["reasoning"]["rationale"] = "Reevaluación & <literal>clínica</literal>. " * 120 + "END_OF_SOURCE_TEXT"
    from management_trace_analysis import source_fingerprint
    report["source_hash"] = source_fingerprint(source)
    monkeypatch.setattr(portal, "generate_management_trace_analysis", lambda *args, **kwargs: report)
    app = make_app(source).run()
    assert not app.exception and len(downloads(app)) == 1
    text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(cached_pdf(app))).pages)
    assert "END_OF_SOURCE_TEXT" in text
    assert "<literal>clínica</literal>" in text


def test_application_adapter_uses_frozen_locked_evidence_and_configured_model(monkeypatch):
    tree = ast.parse(Path(__file__).with_name("app.py").read_text())
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "_render_analyzed_management_trace")
    source = ast.unparse(node)
    script = """
import streamlit as st
ACCOUNT_CONTEXT = None
def _runtime_secret(key):
    return {'OPENAI_API_KEY':'TEST_KEY', 'MRS_TRACE_MODEL':'configured-trace-model'}.get(key, '')
""" + source + "\n_render_analyzed_management_trace()\n"
    calls = []

    def render(payload, **kwargs):
        calls.append((deepcopy(payload), kwargs))
        return None

    monkeypatch.setattr(portal, "render_management_trace_analysis", render)
    app = AppTest.from_string(script)
    source_payload = sample_payload()
    app.session_state["encounter_ended"] = True
    app.session_state["encounter_closed_trace"] = source_payload["trace"]
    app.session_state["precomparison_decision_review"] = source_payload["reflections"]
    app.session_state["review_prompts"] = source_payload["reflection_prompts"]
    app.session_state["management_trace"] = [{"incorrect_live_record": "DO_NOT_USE"}]
    app.session_state["decision_review"] = {"incorrect_later_reflection": "DO_NOT_USE"}
    app.session_state["expert_comparison_unlocked"] = False
    app.run()
    assert not app.exception and calls == []
    app.session_state["expert_comparison_unlocked"] = True
    app.run()
    assert not app.exception and len(calls) == 1
    payload, kwargs = calls[0]
    assert payload == {**source_payload, "encounter_events": []}
    assert kwargs["model"] == "configured-trace-model"
    assert kwargs["api_key"] == "TEST_KEY"


def test_portal_trends_keep_same_time_changes_and_missing_measurements(monkeypatch):
    source = build_analysis_source(sample_payload())
    source["timeline"][1]["state_before"]["observable"]["hr"] = None
    source["timeline"][1]["state_before"]["observable"]["sbp"] = 96
    frames = []

    class Container:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(portal.st, "columns", lambda count: [Container() for _ in range(count)])
    monkeypatch.setattr(portal.st, "caption", lambda *args, **kwargs: None)
    monkeypatch.setattr(portal.st, "line_chart", lambda frame, **kwargs: frames.append(frame.copy()))
    portal._trends(source)
    assert frames
    assert len(frames[0]) == 4
    assert list(frames[0]["Minute"]) == [0, 5, 5, 7]
    assert frames[0].iloc[1]["HR"] == 120
    assert frames[0].iloc[2]["HR"] != frames[0].iloc[2]["HR"]  # NaN preserves the missing sample.
    assert frames[0].iloc[1]["SBP"] == 98 and frames[0].iloc[2]["SBP"] == 96
