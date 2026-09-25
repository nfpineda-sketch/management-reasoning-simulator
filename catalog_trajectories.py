"""Run a case on the real engine with structured actions, and fingerprint what happens.

No provider, no reader and no Streamlit page: the state a launch produces and
the orders in the shape the engine receives them after the reader has done its
work. What this demonstrates is what the engine does with an order. It never
demonstrates that free text reaches that order -- the reader has checks of its
own (``test_hypoglycemia_reader``) -- and it never makes a trajectory
clinically right: a run that reproduces today's behaviour only shows that the
behaviour did not change.
"""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
_INITIAL_STATE = None
# What a launch writes once and never changes during an encounter. It is
# fingerprinted with the launch, not with every step.
FROZEN_KEYS = ("encounter_spec", "encounter_facts")


def initial_state():
    """The application's own starting state, read from app.py without running it."""
    global _INITIAL_STATE
    if _INITIAL_STATE is None:
        tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                    getattr(target, "id", None) == "INITIAL_STATE" for target in node.targets):
                _INITIAL_STATE = ast.literal_eval(node.value)
                break
        else:
            raise RuntimeError("app.py no longer defines INITIAL_STATE as a literal.")
    return deepcopy(_INITIAL_STATE)


def challenge_for(family):
    """The first catalogue challenge whose cases include this family."""
    from cognitive_catalog import BIAS_CHALLENGES
    return next(key for key, item in BIAS_CHALLENGES.items() if family in item["families"])


def launch(variant_id, family, *, seed=17, allow_review_candidates=False):
    """The launched state of one case, exactly as an authored launch builds it."""
    from encounter_generator import generate_encounter
    options = {"allow_review_candidates": True} if allow_review_candidates else {}
    return generate_encounter(challenge_for(family), initial_state(), seed=seed, family_id=family,
                              variant_id=variant_id, generation_mode="authored", **options)["state"]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_default)


def _default(value):
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(f"Not serialisable: {type(value).__name__}")


def digest(value, length=16):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()[:length]


def moving_state(state):
    return {key: value for key, value in state.items() if key not in FROZEN_KEYS}


def run(state, script):
    """Execute every turn in order; a turn is a list of structured actions.

    Returns one row per turn: what the engine answered and the whole state it
    left, both deep copies. A refused turn is recorded as refused -- that is
    behaviour too.
    """
    from family_engine import execute_family_bundle
    rows = []
    for turn in script:
        result = execute_family_bundle(state, {"actions": deepcopy(list(turn))})
        rows.append({"turn": deepcopy(list(turn)), "result": deepcopy(result),
                     "state": deepcopy(moving_state(state))})
    return rows


def readable(row):
    """A few fields a person can read beside a fingerprint."""
    o = row["state"].get("observable", {})
    f = row["state"].get("family_state", {})
    result = row["result"]
    return {"executed": bool(result.get("executed")),
            "clarification": result.get("clarification"),
            "sim_time": row["state"].get("sim_time"),
            "glucose_engine": None if f.get("glucose") is None else round(float(f["glucose"]), 2),
            "mental_status": o.get("mental_status"),
            "labels": [s.get("label") for s in result.get("action_summaries", []) or []]}
