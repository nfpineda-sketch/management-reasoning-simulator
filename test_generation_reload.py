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

assert refresh_generation_modules("0.24.4") is True
# This is the guard used by app.py after the author stack has been refreshed.
if curriculum_runtime.RUNTIME_VERSION != "0.24.4":
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
assert refresh_generation_modules("0.24.4") is False
''')


def test_fresh_process_and_matching_release_do_not_reload():
    run_isolated('''
import sys
from generation_reload import refresh_generation_modules
assert "generated_case" not in sys.modules
assert refresh_generation_modules("0.24.4") is False
assert "generated_case" not in sys.modules
import generated_case
import encounter_generator
author = generated_case.generate_ai_encounter
error = generated_case.GeneratedCaseError
assert refresh_generation_modules("0.24.4") is False
assert generated_case.generate_ai_encounter is author
assert generated_case.GeneratedCaseError is error
''')


def test_hot_visual_update_refreshes_jobs_errors_and_preparation_together():
    run_isolated('''
import ast
from pathlib import Path
import scene_errors
import scene_jobs
import scene_preparation
import scene_pipeline
import image_consistency
import patient_appearance
import clinical_scene
import resuscitation_room
import generation_reload

old_jobs = scene_jobs.SceneJobs
old_error = scene_errors.SceneImageError
old_lock = generation_reload._LOCK
# Simulate the cached v0.17.2 bootstrap, which did not expose visual refresh.
del generation_reload.RELOAD_VERSION
del generation_reload.refresh_visual_modules
patient_appearance.APPEARANCE_VERSION = 3
scene_pipeline.SCENE_PIPELINE_VERSION = 1
clinical_scene.SCENE_RENDER_VERSION = 7
resuscitation_room.ROOM_RENDER_VERSION = 6

# Execute the actual app bootstrap; do not recreate its dependency list here.
tree = ast.parse(Path("app.py").read_text())
nodes = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "require_shared_password":
        break
    nodes.append(node)
exec(compile(ast.Module(body=nodes, type_ignores=[]), "app-bootstrap", "exec"), {})

assert scene_jobs.SceneJobs is not old_jobs
assert scene_errors.SceneImageError is not old_error
assert scene_jobs.SceneImageError is scene_errors.SceneImageError
assert scene_preparation.SceneJobs is scene_jobs.SceneJobs
assert scene_preparation.screened_scene is scene_pipeline.screened_scene
assert scene_pipeline.inspect_image is image_consistency.inspect_image
assert patient_appearance.APPEARANCE_VERSION == 4
assert scene_pipeline.SCENE_PIPELINE_VERSION == 10
assert clinical_scene.SCENE_RENDER_VERSION == 12
assert resuscitation_room.ROOM_RENDER_VERSION == 8
assert generation_reload._LOCK is old_lock
''')


def test_simultaneous_visual_refreshes_share_one_dependency_pass():
    run_isolated('''
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import generation_reload
import patient_appearance
import scene_jobs
import scene_errors
import scene_preparation

patient_appearance.APPEARANCE_VERSION = 3
entered, release, second_started = Event(), Event(), Event()
original_reload = generation_reload.importlib.reload
reloads = []

def controlled_reload(module):
    reloads.append(module.__name__)
    if len(reloads) == 1:
        entered.set()
        assert release.wait(5)
    return original_reload(module)
generation_reload.importlib.reload = controlled_reload

def second_refresh():
    second_started.set()
    return generation_reload.refresh_visual_modules()

with ThreadPoolExecutor(max_workers=2) as pool:
    first = pool.submit(generation_reload.refresh_visual_modules)
    assert entered.wait(5)
    second = pool.submit(second_refresh)
    assert second_started.wait(5)
    release.set()
    assert first.result(10) is True
    assert second.result(10) is False

assert reloads.count("scene_errors") == 1
assert reloads.count("scene_jobs") == 1
assert scene_jobs.SceneImageError is scene_errors.SceneImageError
assert scene_preparation.SceneJobs is scene_jobs.SceneJobs
''')


def test_current_generator_with_old_executor_is_reloaded_and_executes_native_orders():
    run_isolated("""
import generated_case, encounter_generator, generated_engine, family_engine
from generation_reload import refresh_generation_modules
assert generated_case.GENERATOR_VERSION == '0.24.4'
assert encounter_generator.GENERATOR_VERSION == '0.24.4'
def old_executor(*args):
    raise AssertionError('An outdated executor was reached')
generated_engine.execute_generated_bundle=old_executor
family_engine.execute_family_bundle=old_executor
del generated_engine.EXECUTION_VERSION
del family_engine.EXECUTION_VERSION
assert refresh_generation_modules('0.24.4') is True
from test_generated_case import AuthorClient, clean_base
from family_parser import parse_family_actions
s=generated_case.generate_ai_encounter('R1-05',clean_base(),client=AuthorClient(),seed=5)['state']
r=family_engine.execute_family_bundle(s,parse_family_actions('start oxygen 4 L/min nasal cannula, give 1000 cc NS and reassess in 10 minutes'))
assert r['executed'],r
assert s['coupled_state']['treatments']['oxygen_flow_lpm']==4
assert s['family_state']['fluid_delivered_ml']>0
assert refresh_generation_modules('0.24.4') is False
""")
