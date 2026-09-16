"""An explicit local switch that starts encounters from authored cases.

Every launch path in the app calls AI case generation, so without it the only
way to exercise the encounter was to pay for a generation. The authored path
already existed and every menu challenge has an authored case, but only the test
suite could reach it.

Set ``MRS_OFFLINE_CASES=1`` to use it. Off by default, so production behaviour
is unchanged.

Offline has to mean offline everywhere, not only at launch. The key is read in
seven places during an encounter: the patient illustration and its retry, the
language normalization of every learner submission, history answers, and both
faculty analyses. A launch-only switch still issued image requests with a key
present. So the rule is enforced where the key is resolved: every resolver
passes its result through ``withhold``, and in offline mode a provider key
resolves to nothing, whichever path asks for it.
"""
import os


def offline_cases_enabled():
    return os.environ.get("MRS_OFFLINE_CASES", "").strip().lower() in {"1", "true", "yes", "on"}


def launch_options(api_key):
    """Keyword arguments for ``generate_encounter`` and the key the scene may use."""
    if offline_cases_enabled():
        return {"generation_mode": "authored", "api_key": ""}, ""
    return {"api_key": api_key}, api_key


PROVIDER_SECRETS = frozenset({"OPENAI_API_KEY"})


def withhold(name, value):
    """In offline mode a provider key resolves to empty, wherever it is read."""
    if name in PROVIDER_SECRETS and offline_cases_enabled():
        return ""
    return value
