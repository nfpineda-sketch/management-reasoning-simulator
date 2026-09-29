"""A local smoke test of the formative pilot's path (post-V3, 2026-09-29).

It never touches a configured database or real data: it makes its own SQLite file
in a temporary directory -- or, for the backup drill (tools_backup_drill.py), writes
into an empty throwaway database it is handed and refuses one that holds accounts --
its own accounts (no real names), and plays encounters
through the real application (Streamlit's AppTest) as a resident and as a faculty
member. Every attempt to build an AI provider client is recorded and refused, so
the report says whether anything would call a provider without an explicit request.

Two configurations are measured, both with a provider key present:

* ``pilot`` -- ``MRS_OFFLINE_CASES=1``: authored cases, the key withheld everywhere.
* ``default`` -- the application's defaults with the key present.

    python3 tools_pilot_smoke.py [--out report.json]

It deploys nothing, invites nobody and starts no real session.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = str(ROOT / "app.py")
FAKE_KEY = "sk-smoke-test-not-a-key"
ORDERS = {
    "en": ("My working model is that reduced preload contributes to poor perfusion. My priority is to improve "
           "perfusion. Give 500 mL normal saline IV. I expect improved blood pressure and capillary refill. "
           "Reassess blood pressure, heart rate, mental status, and perfusion in 5 minutes."),
    "es": ("Mi modelo de trabajo es que una precarga reducida contribuye a la mala perfusión. Mi prioridad es "
           "mejorar la perfusión. Administrar 500 mL de suero fisiológico EV. Espero que mejoren la presión "
           "arterial y el llene capilar. Reevaluar presión arterial, frecuencia cardiaca, estado mental y "
           "perfusión en 5 minutos."),
}
REVIEW_FIELDS = ("working_model_update", "priority_trigger", "alternative_action", "expected_response_reassessment")
PLAN_FIELDS = ("cue", "threshold", "next_priority", "alternative_action", "expected_effect", "reassessment_plan")
CALLS: list[dict] = []


class _RefusedProvider:
    """Stands in for ``openai.OpenAI``: records who asked, then refuses."""

    def __init__(self, *args, **kwargs):
        frames = [f for f in traceback.extract_stack()[:-1]
                  if str(ROOT) in f.filename and "tools_pilot_smoke" not in f.filename]
        where = [f"{Path(f.filename).name}:{f.name}" for f in frames[-3:]]
        CALLS.append({"step": _STEP[0], "where": where})
        raise RuntimeError("An AI provider client was refused by the pilot smoke test.")


_STEP = ["setup"]


def _refuse_providers():
    import openai
    openai.OpenAI = _RefusedProvider
    for module in list(sys.modules.values()):
        if getattr(module, "OpenAI", None) is not None and module is not openai:
            try:
                module.OpenAI = _RefusedProvider
            except (AttributeError, TypeError):
                pass


def _environment(configuration, url):
    for name in ("MRS_OFFLINE_CASES", "MRS_PAID_GENERATION", "MRS_FREE_GENERATION", "MRS_REPLAY_CASE",
                 "MRS_AI_LANGUAGE_INTERPRETATION"):
        os.environ.pop(name, None)
    os.environ.update({"MRS_AUTH_MODE": "accounts", "MRS_DATABASE_URL": url,
                       "MRS_ALLOW_LOCAL_SQLITE": "true", "OPENAI_API_KEY": FAKE_KEY})
    if configuration == "pilot":
        os.environ["MRS_OFFLINE_CASES"] = "1"


def _accounts(store):
    from account_store import hash_password
    from resident_profile import ProfileStore
    password = "smoke-test-password-" + os.urandom(6).hex()
    store.bootstrap_admin("smoke_admin", hash_password(password))
    admin = store.authenticate("smoke_admin", password)
    people = {"admin": admin}
    for username, role, year in (("smoke_faculty", "faculty", None), ("smoke_resident_en", "resident", 1),
                                 ("smoke_resident_es", "resident", 1)):
        code = store.create_invite(admin, role, year)
        people[username] = store.register(username, password, code)
        if role == "resident":
            ProfileStore(store).decline(people[username])
    return people


def _open(token, timeout):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=timeout)
    at.session_state["_account_token"] = token
    at.run()
    return at


def _click(at, label):
    import report_language
    names = {label, report_language.t(label, "es")}
    button = next((b for b in at.button if b.label in names), None)
    if button is None or button.disabled:
        return False
    button.click().run()
    return True


def _texts(at):
    return " ".join(str(item.value) for kind in ("markdown", "caption", "info", "warning", "error", "subheader")
                    for item in getattr(at, kind))


def _play(store, token, language, timeout):
    """One encounter through the real room, as a resident writes it."""
    at = _open(token, timeout)
    steps = {"opened": not at.exception, "orders_language": language, "screen_language": "en"}
    chooser = next((w for w in at.selectbox if w.key == "presentation_language"), None)
    steps["language_options"] = list(chooser.options) if chooser is not None else []
    steps["begin"] = _click(at, "Begin Encounter") and not at.exception
    state = at.session_state["state"] if "state" in at.session_state else {}
    case = ((state.get("encounter_spec") or {}).get("clinical_case") or {}).get("id") or state.get("case_id")
    if at.text_area:
        at.text_area[0].set_value(ORDERS[language])
        steps["submitted"] = _click(at, "Submit") and not at.exception
    steps["trace_rows"] = len(at.session_state["management_trace"]) if "management_trace" in at.session_state else 0
    steps["buttons_after_submit"] = [(b.label, bool(b.disabled)) for b in at.button][:12]
    steps["messages_after_submit"] = _texts(at)[-600:]
    steps["closed"] = _click(at, "Complete Encounter & Begin Review") and not at.exception
    _click(at, "Finish now")
    steps["ended"] = bool(at.session_state["encounter_ended"]) if "encounter_ended" in at.session_state else False
    steps["focus_hidden_at_close"] = ("after a faculty member reviews it" in _texts(at)
                                     and not any(e.label == "Learning focus for this encounter" for e in at.expander))
    attempt_id = at.session_state["_attempt_id"] if "_attempt_id" in at.session_state else None
    steps["exceptions"] = [str(e.value)[:200] for e in at.exception]
    if attempt_id and steps["ended"]:
        steps["review_completed"] = _complete_review(store, token, attempt_id)
    return at, case, attempt_id, steps


def _complete_review(store, token, attempt_id):
    """The resident's written review, saved through the store as the room saves it.

    The same shortcut the full-app test takes (test_curriculum_app): the review's
    content is the resident's writing; the store's save is the path the room uses.
    """
    from copy import deepcopy
    record = store.get_attempt(token, attempt_id)
    payload = deepcopy(record["payload"])
    session = payload["session"]
    prompts = session.get("review_prompts") or []
    if not prompts:
        return "no review prompts"
    session["decision_review"] = {p["review_id"]: {f: "I will compare the observed perfusion response."
                                                   for f in REVIEW_FIELDS} for p in prompts}
    session["precomparison_decision_review"] = deepcopy(session["decision_review"])
    session["expert_comparison_responses"] = {p["review_id"]: {"alignment": "Perfusion remains a concern.",
                                                               "adjustment": "Reassess the response."}
                                              for p in prompts}
    session["adaptation_plan"] = {f: "Reassess perfusion in context." for f in PLAN_FIELDS}
    session["review_completed"] = True
    session["expert_comparison_unlocked"] = True
    store.save_attempt(token, attempt_id, payload, "completed", record["revision"])
    return store.get_attempt(token, attempt_id)["status"]


def _spanish_screens(token, timeout):
    """The resident's pages rendered in Spanish, without clicks.

    AppTest cannot click once the screens are in Spanish (it looks a translated
    radio's stored value up among its translated options); the Spanish screens
    themselves are covered by test_screens_speak_the_readers_language.py.
    """
    from streamlit.testing.v1 import AppTest
    found = {}
    for view in ("Clinical encounters", "My encounters", "My progress", "My portfolio"):
        at = AppTest.from_file(APP, default_timeout=timeout)
        at.session_state["_account_token"] = token
        at.session_state["presentation_language"] = "Español"
        at.session_state["_resident_dashboard_view"] = view
        at.run()
        found[view] = [str(e.value)[:200] for e in at.exception] or "ok"
    return found


def _record_facts(store, token, attempt_id):
    record = store.get_attempt(token, attempt_id)
    session = (record.get("payload") or {}).get("session") or {}
    encounter = session.get("encounter") or record.get("encounter") or {}
    basis = encounter.get("evaluation_basis") or {}
    assignment = encounter.get("assignment") or {}
    return {"status": record.get("status"), "trace_rows": len(session.get("management_trace") or []),
            "code_version": basis.get("code_version") or assignment.get("code_version"),
            "basis_versions": basis.get("versions"), "case": basis.get("case_id"),
            "language": session.get("encounter_language") or session.get("presentation_language")}


def _permissions(store, people, attempt_id):
    from account_store import AccountError
    from rubric_store import RubricStore
    import rubric
    found = {}
    try:
        seen = store.get_attempt(people["smoke_resident_es"], attempt_id)
        found["another_resident_reads_the_record"] = "ALLOWED" if seen is not None else "refused (not found)"
    except AccountError:
        found["another_resident_reads_the_record"] = "refused"
    listed = {row["id"] for row in store.list_attempts(people["smoke_resident_es"])}
    found["another_resident_lists_the_record"] = "ALLOWED" if attempt_id in listed else "refused"
    try:
        RubricStore(store).save_review(people["smoke_resident_en"], attempt_id,
                                       scores={d: 3 for d in rubric.DOMAIN_IDS}, status="confirmed")
        found["resident_confirms_their_own_rubric"] = "ALLOWED"
    except AccountError:
        found["resident_confirms_their_own_rubric"] = "refused"
    try:
        store.create_invite(people["smoke_faculty"], "resident", 1)
        found["faculty_creates_an_invitation"] = "ALLOWED"
    except AccountError:
        found["faculty_creates_an_invitation"] = "refused"
    found["faculty_reads_the_record"] = "allowed" if store.get_attempt(people["smoke_faculty"], attempt_id) else "none"
    try:
        store.create_invite(people["smoke_resident_en"], "faculty", None)
        found["resident_creates_a_faculty_invitation"] = "ALLOWED"
    except AccountError:
        found["resident_creates_a_faculty_invitation"] = "refused"
    return found


def empty_database(url):
    """Whether ``url`` holds no account yet: the only kind of database this tool writes into."""
    from account_store import AccountStore
    store = AccountStore(url, allow_sqlite=str(url).startswith("sqlite:"))
    with store._transaction() as connection:
        return store._execute(connection, "SELECT COUNT(*) AS n FROM mrs_users").fetchone()["n"] == 0


def run(configuration, timeout=120, url=None):
    """Play the pilot's path. ``url``: an empty, throwaway database to leave the rows in (the backup drill).

    Without it, a temporary SQLite file is made and deleted, as before.
    """
    from account_store import AccountStore
    CALLS.clear()
    with tempfile.TemporaryDirectory(prefix="mrs-smoke-") as directory:
        if url is None:
            url = f"sqlite:///{Path(directory) / 'smoke.sqlite3'}"
        elif not empty_database(url):
            raise SystemExit("That database already holds accounts; this tool writes only into an empty, "
                             "throwaway one.")
        _environment(configuration, url)
        _refuse_providers()
        store = AccountStore(url, allow_sqlite=url.startswith("sqlite:"))
        people = _accounts(store)
        report = {"configuration": configuration, "encounters": {}}
        for language, username in (("en", "smoke_resident_en"), ("es", "smoke_resident_es")):
            _STEP[0] = f"resident {language}: play"
            at, case, attempt_id, steps = _play(store, people[username], language, timeout)
            entry = {"case": case, "attempt": bool(attempt_id), "steps": steps}
            if attempt_id:
                entry["record"] = _record_facts(store, people[username], attempt_id)
                _STEP[0] = f"resident {language}: pages"
                for view in ("My encounters", "My progress", "My portfolio"):
                    page = _open(people[username], timeout)
                    try:
                        page.session_state["_resident_dashboard_view"] = view
                        page.run()
                        entry.setdefault("pages", {})[view] = [str(e.value)[:200] for e in page.exception] or "ok"
                    except Exception as exc:  # noqa: BLE001 -- the report says what failed
                        entry.setdefault("pages", {})[view] = f"not driven: {exc}"
            report["encounters"][language] = entry
        _STEP[0] = "resident: Spanish screens"
        report["spanish_screens"] = _spanish_screens(people["smoke_resident_es"], timeout)
        first = next((e for e in report["encounters"].values() if e.get("attempt")), None)
        if first is not None:
            attempt_id = store.list_attempts(people["smoke_resident_en"])[0]["id"]
            _STEP[0] = "faculty: dashboard"
            faculty = _open(people["smoke_faculty"], timeout)
            report["faculty_dashboard"] = [str(e.value)[:200] for e in faculty.exception] or "ok"
            _STEP[0] = "faculty: confirm rubric"
            from rubric_store import RubricStore
            import rubric
            import resident_pages
            try:
                RubricStore(store).save_review(people["smoke_faculty"], attempt_id,
                                               scores={d: 2 for d in rubric.DOMAIN_IDS}, status="confirmed")
                report["rubric_confirmed"] = True
            except Exception as exc:  # noqa: BLE001 -- the report says what failed
                report["rubric_confirmed"] = f"failed: {exc}"
            user = store.get_user(people["smoke_resident_en"])
            context = {"store": store, "token": people["smoke_resident_en"], "user": user}
            report["focus_visible_after_review"] = resident_pages.learning_focus_visible(context, attempt_id)
            _STEP[0] = "resident: documents in Spanish"
            import portfolio
            import prose_translation
            record = store.get_attempt(people["smoke_resident_en"], attempt_id)
            page = prose_translation.for_page(context, f"portfolio:{attempt_id}:es")
            try:
                found = portfolio.documents(context, record, user, language="es", translate=page)
                report["documents_es"] = sorted(found) if isinstance(found, dict) else len(found or [])
            except Exception as exc:  # noqa: BLE001
                report["documents_es"] = f"failed: {exc}"
            report["permissions"] = _permissions(store, people, attempt_id)
        report["provider_attempts"] = list(CALLS)
        return report


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", help="write the JSON report here as well")
    parser.add_argument("--configuration", choices=("pilot", "default", "both"), default="both")
    args = parser.parse_args(argv)
    commit = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                                cwd=ROOT).stdout.strip())
    import family_engine
    import glucose_rescue
    import re
    version = re.search(r'^SIMULATOR_VERSION = "([^"]+)"', Path(APP).read_text(encoding="utf-8"), re.M)
    result = {"commit": commit, "uncommitted_changes": dirty, "simulator_version": version and version.group(1),
              "family_engine": family_engine.FAMILY_ENGINE_VERSION, "glucose_rescue": glucose_rescue.VERSION,
              "runs": []}
    for configuration in (("pilot", "default") if args.configuration == "both" else (args.configuration,)):
        result["runs"].append(run(configuration))
    text = json.dumps(result, indent=1, ensure_ascii=False, default=str)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
