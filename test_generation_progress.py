"""Progress must describe real stages without exposing a case or an exception."""
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

import generation_progress
from generation_progress import STAGE_LABELS, encounter_preparation


class RecordingStatus:
    def __init__(self):
        self.messages = []
        self.updates = []

    def write(self, text):
        self.messages.append(text)

    def update(self, **kwargs):
        self.updates.append(kwargs)


def test_progress_reports_stages_elapsed_and_completion_without_repeating(monkeypatch):
    status = RecordingStatus()
    times = iter([100, 100, 132, 132, 164, 165])
    monkeypatch.setattr(generation_progress, "monotonic", lambda: next(times))
    with encounter_preparation(SimpleNamespace(status=lambda *args, **kwargs: status)) as progress:
        for stage in ("author", "validation", "validation", "correction", "review", "complete"):
            progress(stage)
    assert status.messages[1:] == [
        "Creating your patient · 0s elapsed",
        "Checking the clinical scenario · 32s elapsed",
        "Refining the clinical scenario · 32s elapsed",
        "Reviewing clinical consistency · 64s elapsed",
        "Your encounter is ready · 65s elapsed",
    ]
    assert status.updates[-1]["state"] == "complete"


def test_failed_preparation_never_displays_raw_detail_or_claims_ready():
    status = RecordingStatus()
    secret_detail = "private diagnosis and provider payload"
    with pytest.raises(ValueError, match=secret_detail):
        with encounter_preparation(SimpleNamespace(status=lambda *args, **kwargs: status)) as progress:
            progress("author")
            progress(secret_detail)
            progress({"unexpected": secret_detail})
            progress("correction")
            raise ValueError(secret_detail)
    assert secret_detail not in str(status.messages) + str(status.updates)
    assert status.updates[-1]["state"] == "error"
    assert not any(update["state"] == "complete" for update in status.updates)


def test_real_streamlit_status_displays_preparation_stages():
    def page():
        import streamlit as st
        from generation_progress import encounter_preparation
        with encounter_preparation(st) as progress:
            progress("author")
            progress("validation")
            progress("correction")
            progress("review")
            progress("complete")

    app = AppTest.from_function(page).run()
    assert not app.exception
    text = "\n".join(item.value for item in app.markdown)
    assert all(label in text for label in STAGE_LABELS.values())
    assert app.get("status")[0].label == "Your encounter is ready"


def test_page_title_and_all_visible_captions_share_release_version(monkeypatch):
    from test_problem_launch import open_shared
    app = open_shared(monkeypatch)
    captions = [item.value for item in app.caption if "Clinical encounter v" in item.value]
    assert captions
    assert all(item.endswith("v0.24.4") for item in captions)
    # AppTest does not expose page config; evaluate its real expression using
    # the same assignment that produces persisted simulator metadata.
    import ast
    from pathlib import Path
    tree = ast.parse(Path(__file__).with_name("app.py").read_text())
    version = next(node for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "SIMULATOR_VERSION"
                           for target in node.targets))
    config = next(node.value for node in tree.body if isinstance(node, ast.Expr)
                  and isinstance(node.value, ast.Call)
                  and isinstance(node.value.func, ast.Attribute)
                  and node.value.func.attr == "set_page_config")
    namespace = {}
    exec(compile(ast.Module(body=[version], type_ignores=[]), "version", "exec"), namespace)
    title = next(keyword.value for keyword in config.keywords if keyword.arg == "page_title")
    value = eval(compile(ast.Expression(title), "page_title", "eval"), namespace)
    assert value.endswith("v0.24.4")
