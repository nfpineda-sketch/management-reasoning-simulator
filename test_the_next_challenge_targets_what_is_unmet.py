"""Choosing the next challenge from what the resident has never met.

Faculty request of 2026-09-23. Two properties hold it in place:

**It reads coverage, never scores.** What it looks at is which defined
critical events the resident's past cases could have presented -- which safety
situations they have never been placed in. Not how they did. An instrument
that chose the next case from its own marks would steer the learner by its own
output, and this rubric is a pilot that awards nothing.

**It breaks ties and never overrides.** The curriculum rule decides what is
eligible and where the gap is; targeting only orders the candidates that rule
was already picking between at random.
"""
import pytest

import challenge_targeting
from curriculum import CHALLENGES, assign_challenge


def attempt(challenge_id, *, status="completed", sandbox=False, updated="1"):
    return {"challenge_id": challenge_id, "status": status, "is_sandbox": sandbox,
            "updated_at": updated, "payload": {}}


# --- what counts as met -----------------------------------------------------

def test_a_challenge_offers_the_events_of_the_cases_behind_it():
    events = challenge_targeting.events_of(CHALLENGES["R1-06"])
    assert "hypo_unsafe_discharge" in events
    assert "opioid_unsafe_discharge" in events
    assert "acs_no_antiplatelet" not in events


def test_a_challenge_with_no_case_family_offers_none():
    assert challenge_targeting.events_of({"families": []}) == set()
    assert challenge_targeting.events_of({}) == set()


def test_completing_a_challenge_marks_its_situations_met():
    seen = challenge_targeting.seen_events([attempt("R1-06")], CHALLENGES)
    assert "hypo_unsafe_discharge" in seen
    assert "pneumonia_no_antibiotic" not in seen


@pytest.mark.parametrize("item", [
    attempt("R1-06", status="active"),
    attempt("R1-06", status="abandoned"),
    attempt("R1-06", sandbox=True),
])
def test_an_encounter_that_never_counted_marks_nothing(item):
    assert challenge_targeting.seen_events([item], CHALLENGES) == set()


def test_what_is_unmet_shrinks_as_situations_are_met():
    before = challenge_targeting.unmet([], CHALLENGES)
    after = challenge_targeting.unmet([attempt("R1-06")], CHALLENGES)
    # Nine since the anaphylaxis family joined this challenge on 2026-09-23;
    # eight since hypo_no_thiamine stopped being a critical event on
    # 2026-09-25 (coverage 1.1). The number is here so a family leaving a
    # challenge is noticed; the property is that completing it takes every one
    # of them to met.
    assert before["R1-06"] == 8 and after["R1-06"] == 0
    # R1-07 shares hypoglycaemia with R1-06, so it loses what they share.
    assert after["R1-07"] < before["R1-07"]
    # A challenge with nothing in common is untouched.
    assert after["R1-05"] == before["R1-05"]


# --- how it is used ---------------------------------------------------------

def test_it_prefers_the_candidate_that_offers_most_that_is_new():
    done = [attempt("R1-06")]
    targeted = assign_challenge(1, done, 7, challenge_targeting.unmet(done, CHALLENGES))
    assert targeted["challenge_id"] == "R1-05"
    assert targeted["targeting"] == "unmet_situations"


def test_without_it_the_assignment_is_exactly_what_it_was():
    done = [attempt("R1-06")]
    assert assign_challenge(1, done, 7) == assign_challenge(1, done, 7, None)
    assert assign_challenge(1, done, 7)["targeting"] == "none"


def test_it_never_chooses_outside_what_the_curriculum_offered():
    for seed in range(12):
        for year in (1, 2, 3):
            done = [attempt("R1-06"), attempt("R1-05", updated="2")]
            plain = assign_challenge(year, done, seed)
            aimed = assign_challenge(year, done, seed,
                                     challenge_targeting.unmet(done, CHALLENGES))
            # The curriculum's own rule still decides the reason and the pool.
            assert aimed["reason"] == plain["reason"]
            from curriculum import eligible_challenges
            assert aimed["challenge_id"] in eligible_challenges(year)


def test_a_year_one_resident_is_never_aimed_at_a_later_year():
    done = [attempt("R1-06")]
    from curriculum import eligible_challenges
    for seed in range(20):
        aimed = assign_challenge(1, done, seed, challenge_targeting.unmet(done, CHALLENGES))
        assert aimed["challenge_id"] in eligible_challenges(1)


def test_when_everything_has_been_met_the_random_pick_returns():
    done = [attempt(key, updated=str(index)) for index, key in enumerate(CHALLENGES)]
    aimed = assign_challenge(3, done, 5, challenge_targeting.unmet(done, CHALLENGES))
    plain = assign_challenge(3, done, 5)
    assert aimed["challenge_id"] == plain["challenge_id"]
    assert aimed["targeting"] == "none"


def test_a_tie_among_all_candidates_changes_nothing():
    done = [attempt("R1-06")]
    flat = {key: 3 for key in CHALLENGES}
    assert (assign_challenge(1, done, 7, flat)["challenge_id"]
            == assign_challenge(1, done, 7)["challenge_id"])


def test_nothing_here_reads_a_score():
    """The property, stated where it can be checked: coverage only."""
    import ast
    from pathlib import Path
    source = Path(challenge_targeting.__file__).read_text(encoding="utf-8")
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    assert "rubric" not in names and "rubric_store" not in names
    assert "rubric_progress" not in names and "progress_store" not in names


def test_a_score_attached_to_an_encounter_changes_nothing():
    # The behavioural half of the same property: two identical histories, one
    # of them carrying marks, and the targeting is the same.
    plain = [attempt("R1-06")]
    marked = [{**attempt("R1-06"), "rubric": {"scores": {"D1": 0}, "adjusted": 0}}]
    assert (challenge_targeting.unmet(plain, CHALLENGES)
            == challenge_targeting.unmet(marked, CHALLENGES))


def test_the_curriculum_still_knows_nothing_about_the_rubric():
    import ast
    from pathlib import Path
    source = Path("curriculum.py").read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        module = getattr(node, "module", None) if isinstance(node, ast.ImportFrom) else None
        assert not (module or "").startswith(("rubric", "case_assessment"))


def test_the_explanation_says_what_it_offers_without_saying_how_anyone_did():
    done = [attempt("R1-06")]
    line = challenge_targeting.explain(done, CHALLENGES, "R1-05")
    assert "4 safety situation(s)" in line
    assert "remain unmet" in line
    for word in ("score", "Score", "low", "weak", "poor"):
        assert word not in line
