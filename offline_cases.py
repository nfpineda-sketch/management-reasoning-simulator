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


def replay_record(require_offline=True):
    """A saved AI-generated encounter to play again, or None.

    ``MRS_REPLAY_CASE`` names a JSON record written by a paid run (it must hold
    the launched ``state``). In offline mode it is the only way an encounter
    starts, so replaying never pays for a generation, an image or a
    normalization. It is also used to serve a saved case to someone who may not
    start a paid one.
    """
    path = os.environ.get("MRS_REPLAY_CASE", "").strip()
    if not path or (require_offline and not offline_cases_enabled()):
        return None
    import json
    from pathlib import Path
    record = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    state = record.get("state") if isinstance(record, dict) else None
    if not isinstance(state, dict) or not isinstance(state.get("encounter_spec"), dict):
        raise ValueError("MRS_REPLAY_CASE must name a saved run that contains the launched encounter state.")
    return record


def paid_generation_allowed(role=None):
    """Who may start an encounter that pays a provider.

    Faculty decision B1, 2026-09-23: sharing the app's URL must not share the
    card. With ``MRS_PAID_GENERATION`` set to ``admin``, only an administrator
    starts a generated case and everyone else is served a saved, validated one.
    Offline mode still overrides everything.
    """
    if offline_cases_enabled():
        return False
    setting = str(os.environ.get("MRS_PAID_GENERATION", "")).strip().lower()
    if setting in {"admin", "administrator"}:
        return str(role or "").strip().lower() == "admin"
    if setting in {"none", "off", "0", "false", "no"}:
        return False
    return True


def launch_options(api_key, role=None):
    """Keyword arguments for ``generate_encounter`` and the key the scene may use."""
    if offline_cases_enabled():
        record = replay_record()
        if record is not None:
            return {"generation_mode": "replay", "replay": record, "api_key": ""}, ""
        return {"generation_mode": "authored", "api_key": ""}, ""
    if not paid_generation_allowed(role):
        # A saved, validated case instead of a paid generation.
        record = replay_record(require_offline=False)
        if record is not None:
            return {"generation_mode": "replay", "replay": record, "api_key": ""}, ""
        return {"generation_mode": "authored", "api_key": ""}, ""
    return {"api_key": api_key}, api_key


PROVIDER_SECRETS = frozenset({"OPENAI_API_KEY"})


def withhold(name, value):
    """In offline mode a provider key resolves to empty, wherever it is read."""
    if name in PROVIDER_SECRETS and offline_cases_enabled():
        return ""
    return value
