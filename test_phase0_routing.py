"""Phase 0 (0C): a pilot resident is never given the legacy PS001 engine.

Pre-pilot measurement safety, 2026-10-06. The pilot documents say the legacy engine is not
used ("motor antiguo, inaccesible"; "PS001/PS002 no se usan"); the clinical engine audit
found it assigned all the same (§1.1): once a year-1 resident had seen the three year-1
varied cases, the automatic assignment gave R1-03 or R1-04, which run on PS001. These
tests follow the real assignment and the real launch, without monkeypatching either.
"""
import pytest

import curriculum
from encounter_generator import generate_encounter
from test_curriculum_trajectories import load_engine


def _completed(keys):
    return [{"challenge_id": key, "status": "completed", "is_sandbox": False,
             "updated_at": f"2026-09-{index + 1:02d}T12:00:00Z", "payload": {}}
            for index, key in enumerate(keys)]


@pytest.mark.parametrize("year", [1, 2, 3])
def test_the_automatic_assignment_never_launches_the_legacy_engine(year):
    engine = load_engine()
    histories = [[], _completed(curriculum.assignable_challenges(year)),
                 _completed(curriculum.assignable_challenges(year) * 3)]
    for history in histories:
        for seed in range(25):
            assignment = curriculum.assign_challenge(year, history, seed)
            assert assignment["challenge_id"] not in curriculum.LEGACY_ENGINE_CHALLENGES
            encounter = generate_encounter(assignment["challenge_id"], engine["INITIAL_STATE"], seed=seed,
                                           generation_mode="authored", api_key="")
            state = encounter["state"]
            assert state.get("engine_family"), "a resident encounter runs on the family engine"
            assert state.get("case_id") != "PS001"
            assert (state.get("encounter_spec") or {}).get("clinical_case", {}).get("id") != "PS001"


def test_the_legacy_challenges_are_kept_for_faculty_and_migration():
    # Not deleted: the faculty sandbox still offers them and they still launch PS001.
    engine = load_engine()
    for key in sorted(curriculum.LEGACY_ENGINE_CHALLENGES):
        assert key in curriculum.CHALLENGES
        encounter = generate_encounter(key, engine["INITIAL_STATE"], seed=17, generation_mode="authored",
                                       api_key="")
        assert not encounter["state"].get("engine_family")


def test_a_directive_cannot_reach_a_legacy_challenge():
    from encounter_directives import case_options
    for key in curriculum.LEGACY_ENGINE_CHALLENGES:
        assert case_options(key) == []
