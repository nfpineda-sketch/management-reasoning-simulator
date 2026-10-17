from pathlib import Path


def _source():
    return Path("app.py").read_text(encoding="utf-8")


def test_active_encounter_is_one_named_fragment():
    source = _source()
    assert '@_encounter_fragment(key="clinical-encounter")' in source
    assert "def _encounter_fragment(*, key):" in source
    assert "return st.fragment(key=key)" in source
    assert "def _clinical_encounter_workspace():" in source
    assert source.rstrip().endswith("_clinical_encounter_workspace()")


def test_fragment_decorator_is_safe_with_missing_or_partial_fake_st():
    source = _source()
    start = source.index("def _encounter_fragment(*, key):")
    stop = source.index("def rerun_app():", start)
    block = source[start:stop]
    assert 'streamlit_obj = globals().get("st")' in block
    assert 'getattr(streamlit_obj, "fragment", None)' in block
    assert "if not callable(fragment):" in block
    assert "return lambda func: func" in block
    assert "return fragment(key=key)" in block


def test_send_callback_only_captures_and_relies_on_native_fragment_rerun():
    source = _source()
    start = source.index("def _capture_submission(form_id):")
    stop = source.index("# Historical source markers", start)
    block = source[start:stop]
    code_lines = [line.strip() for line in block.splitlines() if not line.strip().startswith("#")]
    assert not any(line.startswith("st.rerun(") for line in code_lines)
    assert "_encounter_fragment_rerun" not in block
    assert "submission_guard.capture(st.session_state, form_id)" in block


def test_fragment_repeats_write_ahead_before_any_encounter_render():
    source = _source()
    start = source.index("def _clinical_encounter_workspace():")
    render = source.index("_in_room = not st.session_state.encounter_ended", start)
    prefix = source[start:render]
    assert "_submission_guard.recover(" in prefix
    assert "_submission_guard.write_ahead(" in prefix
    assert "_process_encounter_submission(" in prefix
    assert prefix.index("_submission_guard.write_ahead(") < prefix.index("_process_encounter_submission(")


def test_submission_processing_is_extracted_from_the_render_tree():
    source = _source()
    helper = source.index("def _process_encounter_submission(")
    fragment = source.index('@_encounter_fragment(key="clinical-encounter")')
    assert helper < fragment
    start = source.index("if submitted and submission_text.strip():", fragment)
    snippet = source[start:start + 360]
    assert "_process_encounter_submission(submission_text, _guard_entry, submission_parsed)" in snippet


def test_ordinary_send_finishes_and_renders_in_the_same_fragment_run():
    source = _source()
    start = source.index("def _process_encounter_submission(")
    stop = source.index('@st.fragment(key="clinical-encounter")', start)
    helper = source[start:stop]
    cursor = 'recorded_trace_event["state_after"]["encounter_event_count"]'
    assert cursor in helper
    ordinary = helper[helper.index(cursor):]
    assert "_guard.finish(st.session_state)" in ordinary
    assert "save_session(ACCOUNT_CONTEXT)" in ordinary
    assert "return" in ordinary
    assert ordinary.index("return") < ordinary.rindex("rerun_app()")


def test_bedside_has_no_nested_streamlit_fragment():
    source = Path("resuscitation_room.py").read_text(encoding="utf-8")
    start = source.index("def render_room(")
    stop = source.index("def clear_room_fragment", start)
    block = source[start:stop]
    assert "st.fragment(" not in block
    assert "_room(" in block
