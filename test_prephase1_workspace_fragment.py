from pathlib import Path


def _source():
    return Path("app.py").read_text(encoding="utf-8")


def test_active_encounter_is_one_named_fragment():
    source = _source()
    assert '@st.fragment(key="clinical-encounter")' in source
    assert "def _clinical_encounter_workspace():" in source
    assert source.rstrip().endswith("_clinical_encounter_workspace()")


def test_send_callback_relies_on_the_fragment_widgets_native_rerun():
    source = _source()
    start = source.index("def _capture_submission(form_id):")
    stop = source.index("# Historical source markers", start)
    block = source[start:stop]
    assert 'st.rerun("clinical-encounter")' not in block
    assert 'st.session_state["_encounter_fragment_rerun"] = True' in block


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
    fragment = source.index('@st.fragment(key="clinical-encounter")')
    assert helper < fragment
    start = source.index("if submitted and submission_text.strip():", fragment)
    snippet = source[start:start + 360]
    assert "_process_encounter_submission(submission_text, _guard_entry, submission_parsed)" in snippet


def test_send_result_rerun_stays_fragment_scoped():
    source = _source()
    start = source.index("def rerun_app():")
    stop = source.index("def _capture_submission", start)
    block = source[start:stop]
    assert 'pop("_encounter_fragment_rerun", False)' in block
    assert 'st.rerun(scope="fragment")' in block


def test_bedside_has_no_nested_streamlit_fragment():
    source = Path("resuscitation_room.py").read_text(encoding="utf-8")
    start = source.index("def render_room(")
    stop = source.index("def clear_room_fragment", start)
    block = source[start:stop]
    assert "st.fragment(" not in block
    assert "_room(" in block
