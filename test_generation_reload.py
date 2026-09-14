"""A hot update must not mix old author callbacks with new exception classes."""
import subprocess
import sys
from pathlib import Path


def run_isolated(source):
    result = subprocess.run(
        [sys.executable, "-c", source],
        cwd=Path(__file__).resolve().parent,
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_hot_update_refreshes_callback_and_exception_aliases():
    # A separate interpreter models the old cached release without invalidating
    # class references intentionally imported by other collected test modules.
    run_isolated('''
import importlib
import generated_case
import generated_case_schema
import generated_case_errors
import encounter_generator
import curriculum_runtime
from generation_reload import refresh_generation_modules

old_error = generated_case.GeneratedCaseError
def old_author(challenge_id, base_state, api_key="", model="", seed=None, client=None, review_model=None):
    raise AssertionError("The old author must not run after a hot update")
generated_case.generate_ai_encounter = old_author
generated_case.GENERATOR_VERSION = "0.17.1"
encounter_generator.GENERATOR_VERSION = "0.17.0"
curriculum_runtime.RUNTIME_VERSION = "0.17.1"

assert refresh_generation_modules("0.17.2") is True
# This is the guard used by app.py after the author stack has been refreshed.
if curriculum_runtime.RUNTIME_VERSION != "0.17.2":
    importlib.reload(curriculum_runtime)
assert curriculum_runtime.generate_encounter is encounter_generator.generate_encounter
assert generated_case.GeneratedCaseError is generated_case_schema.GeneratedCaseError
assert generated_case_errors.GeneratedCaseError is generated_case_schema.GeneratedCaseError
assert generated_case.GeneratedCaseError is not old_error

from test_generated_case import AuthorClient, novel_payload
stages = []
encounter = curriculum_runtime.generate_encounter(
    "R1-04", {"sim_time": 0}, client=AuthorClient(novel_payload()), progress=stages.append,
)
assert stages == ["author", "validation", "review", "complete"]
assert encounter["state"]["engine_family"] == "generated"
try:
    raise generated_case_errors.generation_error("REVIEW", "REVIEW")
except generated_case.GeneratedCaseError:
    pass
else:
    raise AssertionError("The UI error boundary must catch the current error class")
assert refresh_generation_modules("0.17.2") is False
''')


def test_fresh_process_and_matching_release_do_not_reload():
    run_isolated('''
import sys
from generation_reload import refresh_generation_modules
assert "generated_case" not in sys.modules
assert refresh_generation_modules("0.17.2") is False
assert "generated_case" not in sys.modules
import generated_case
import encounter_generator
author = generated_case.generate_ai_encounter
error = generated_case.GeneratedCaseError
assert refresh_generation_modules("0.17.2") is False
assert generated_case.generate_ai_encounter is author
assert generated_case.GeneratedCaseError is error
''')
