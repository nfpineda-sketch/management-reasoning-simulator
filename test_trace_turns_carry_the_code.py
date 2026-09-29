"""Every Management Trace turn names the code that answered it (TD-10, cycle 10).

The encounter records the commit it started with; a deployment can change before it ends, and
the turns after that were read and run by other code. Each turn now carries ``code_version``,
the same value the encounter's start records (``curriculum_runtime.code_version``).
"""
import curriculum_runtime
from test_doses_by_solution_and_by_weight import start, submit, widget


def test_an_order_and_an_examination_each_carry_the_code_that_answered_them(tmp_path, monkeypatch):
    monkeypatch.setenv("MRS_LANGUAGE", "en")
    at = start(tmp_path, monkeypatch, "hypoglycemia_28m", "R1-06", language="en")
    submit(at, "Check a capillary glucose now.")
    widget(at.radio, "Encounter").set_value("Examine").run()
    widget(at.selectbox, "Examine").set_value("General appearance").run()
    widget(at.button, "Examine patient").click().run()
    assert not at.exception
    trace = at.session_state["management_trace"]
    kinds = [entry.get("activity_kind", "decision") for entry in trace]
    assert "decision" in kinds and "examination" in kinds
    expected = curriculum_runtime.code_version()
    assert expected and all(entry["code_version"] == expected for entry in trace)
