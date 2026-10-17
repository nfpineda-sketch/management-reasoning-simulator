from pathlib import Path


def test_durable_send_is_processed_before_encounter_rendering():
    source = Path("app.py").read_text(encoding="utf-8")

    helper = source.index("def _process_submission_before_render(")
    pending = source.index("_pre_render_guard_entry = next(iter(_submission_guard.pending(st.session_state)), None)")
    render = source.index("_in_room = not st.session_state.encounter_ended")

    assert helper < pending < render

    pre_render = source[pending:render]
    assert "_process_submission_before_render(" in pre_render
    assert "render_room(" not in pre_render
    assert "st.container(key=\"encounter-console\")" not in pre_render


def test_form_path_delegates_to_the_same_submission_processor():
    source = Path("app.py").read_text(encoding="utf-8")
    marker = "if submitted and submission_text.strip():"
    start = source.index(marker)
    block = source[start:start + 300]

    assert "_process_submission_before_render(submission_text, _guard_entry, submission_parsed)" in block


def test_processing_helper_reruns_only_after_recording_the_response():
    source = Path("app.py").read_text(encoding="utf-8")
    start = source.index("def _process_submission_before_render(")
    stop = source.index("_pre_render_guard_entry =", start)
    helper = source[start:stop]

    cursor = 'recorded_trace_event["state_after"]["encounter_event_count"]'
    assert cursor in helper
    assert "rerun_app()" in helper
    assert helper.rindex("rerun_app()") > helper.index(cursor)
