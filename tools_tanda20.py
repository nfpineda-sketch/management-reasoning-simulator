"""The twenty-scenario batch: its plan, its offline rehearsal, and its runner.

Faculty specification of 2026-09-24. Three uses, and only one of them counts:

``--plan``
    The twenty scenarios, their trajectory, the challenge each is launched
    under, and what each case declares for the rubric.

``--rehearse``  (free, offline, and never evidence for the batch)
    Plays each script through the real page -- the same app.py a resident
    uses, driven by Streamlit's in-process test runner -- against a temporary
    database, with the provider key withheld and the case pinned. It exists to
    find what would stop a resident *before* a paid encounter is spent: an
    order the application does not read, a follow-up question that comes back
    twice, an order executed twice, a result that disappears, a close that
    fails. The account it creates is a rehearsal copy in a temporary file,
    never ``residente_prueba_r3`` in the real database, and nothing it writes
    is presented as part of the batch.

``--run``  (paid, and the only evidence)
    The batch itself: the development app, the real ``residente_prueba_r3``
    account, the real database. See ``docs/TANDA_20_ESCENARIOS.md`` for what it
    needs and why it could not run in the session that prepared it.
"""
import os
import sys

if __name__ == "__main__" and "--run" not in sys.argv:
    # The rehearsal must never reach a provider, whatever the environment has.
    os.environ["MRS_OFFLINE_CASES"] = "1"

import argparse
import json
import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

APP = str(ROOT / "app.py")
TEST_ACCOUNT = "residente_prueba_r3"


# --- the plan ------------------------------------------------------------------

def plan():
    """One row per scenario, with what its case declares for the rubric."""
    import case_assessment_bank as bank
    from curriculum import CHALLENGES
    from tanda20 import CATEGORIES, SCRIPTS
    rows = []
    for script in SCRIPTS:
        entry = bank.CASES.get(script["case_id"]) or {}
        events = [event.get("event_id") or event.get("id")
                  for event in entry.get("critical_events") or entry.get("events") or []]
        rows.append({"number": script["number"], "case_id": script["case_id"],
                     "family": script["family"], "category": script["category"],
                     "category_label": CATEGORIES[script["category"]],
                     "challenge": script["challenge"],
                     "challenge_title": CHALLENGES[script["challenge"]]["title"],
                     "intent": script["intent"], "steps": len(script["steps"]),
                     "declared_events": events})
    return rows


# --- the rehearsal ---------------------------------------------------------------

@contextmanager
def _environment(values):
    saved = {key: os.environ.get(key) for key in values}
    os.environ.update({key: str(value) for key, value in values.items()})
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _button(at, label):
    return next((item for item in at.button if item.label == label), None)


def _click(at, label):
    button = _button(at, label)
    if button is None:
        raise RehearsalStop(f"The page offers no {label!r} button.")
    button.click().run()


def _mode(at, mode):
    radio = next((item for item in at.radio if item.label == "Encounter"), None)
    if radio is None:
        raise RehearsalStop("The encounter controls are not on the page.")
    radio.set_value(mode).run()


class RehearsalStop(Exception):
    """The page could not go on: this is a finding, not a crash of the tool."""


def _events(at):
    return list(at.session_state["events"]) if "events" in at.session_state else []


def _pending(at):
    for key in ("pending_reasoning", "pending_action", "pending_bundle"):
        if key in at.session_state and at.session_state[key]:
            return key
    return None


def _step(at, step):
    """Perform one step on the page. Returns what the application said back."""
    kind = step[0]
    before = len(_events(at))
    trace_before = len(at.session_state["management_trace"]) if "management_trace" in at.session_state else 0
    if kind == "ask":
        _mode(at, "Talk")
        field = next((item for item in at.text_input
                      if item.label in ("Ask the patient", "Ask the available history source")), None)
        if field is None:
            raise RehearsalStop("There is nobody to ask: no history field on the page.")
        field.set_value(step[1])
        next(item for item in at.button if item.label == "Ask").click().run()
    elif kind == "examine":
        _mode(at, "Examine")
        select = next((item for item in at.selectbox if item.label == "Examine"), None)
        if select is None or step[1] not in select.options:
            raise RehearsalStop(f"The examination {step[1]!r} is not offered: "
                                f"{select.options if select else 'no selector'}.")
        select.set_value(step[1]).run()
        _click(at, "Examine patient")
    elif kind == "order":
        _mode(at, "Treat")
        box = next((item for item in at.text_area
                    if item.label == "Enter your clinical reasoning and/or actions"), None)
        if box is None:
            raise RehearsalStop("The order box is not on the page.")
        box.set_value(step[1])
        _click(at, "Submit")
    elif kind == "answer":
        # A natural-language answer to the follow-up question of a held order.
        _mode(at, "Treat")
        box = next((item for item in at.text_area
                    if item.label == "Enter your clinical reasoning and/or actions"), None)
        if box is None:
            raise RehearsalStop("The answer box is not on the page.")
        box.set_value(step[1])
        _click(at, "Submit")
    elif kind == "complete":
        answers = step[1]
        form = {item.label: item for item in at.text_area}
        for label, value in answers.items():
            if label == "delay":
                next(item for item in at.number_input).set_value(int(value))
                continue
            target = next((item for text, item in form.items() if text.startswith(label)), None)
            if target is None:
                raise RehearsalStop(f"The follow-up question {label!r} is not on the page.")
            target.set_value(value)
        _click(at, "Complete reasoning & execute held order")
    elif kind == "cancel":
        _click(at, "Cancel pending orders")
    elif kind == "recover":
        _click(at, "Save & return to dashboard")
        _click(at, "Resume encounter")
    else:
        raise ValueError(f"Unknown step {kind!r}.")
    if at.exception:
        raise RehearsalStop("The page raised: " + str(at.exception[0].value)[:500])
    said = [event for event in _events(at)[before:]
            if event.get("kind") not in ("you", "reasoning_completion")]
    trace_after = len(at.session_state["management_trace"]) if "management_trace" in at.session_state else 0
    return {"step": list(step), "said": [f"{e.get('kind')}: {str(e.get('text'))[:300]}" for e in said],
            "held": _pending(at), "new_trace_entries": trace_after - trace_before,
            "sim_time": (at.session_state["state"] or {}).get("sim_time")}


def _app_constant(name):
    """A literal the page defines, read from app.py so the labels cannot drift."""
    import ast
    tree = ast.parse(Path(APP).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)


FALLBACK_ANSWERS = {
    "What do you think is going on": "Mantengo la hipótesis de trabajo que ya expliqué.",
    "What do you expect": "Espero que mejore el parámetro que estoy tratando.",
    "What will you check": "Signos vitales y el hallazgo que motivó la orden.",
}
FALLBACK_ANSWERS_EN = {
    "What do you think is going on": "I keep the working hypothesis I already explained.",
    "What do you expect": "I expect the parameter I am treating to improve.",
    "What will you check": "Vital signs and the finding that prompted the order.",
}


def _resolve(at, held, language="es"):
    """An unanticipated hold, answered with the four questions or cancelled."""
    fallback = FALLBACK_ANSWERS_EN if language == "en" else FALLBACK_ANSWERS
    if held == "pending_reasoning":
        areas = [item for item in at.text_area if not item.disabled]
        for item in areas:
            for prefix, value in fallback.items():
                if item.label.startswith(prefix) and not str(item.value or "").strip():
                    item.set_value(value)
        try:
            _click(at, "Complete reasoning & execute held order")
        except RehearsalStop:
            _click(at, "Cancel pending orders")
            return {"step": ["auto-cancel", held], "said": [], "held": _pending(at),
                    "new_trace_entries": 0, "sim_time": (at.session_state["state"] or {}).get("sim_time")}
        return {"step": ["auto-complete", held], "said": [], "held": _pending(at),
                "new_trace_entries": None, "sim_time": (at.session_state["state"] or {}).get("sim_time")}
    _click(at, "Cancel pending orders")
    return {"step": ["auto-cancel", held], "said": [], "held": _pending(at),
            "new_trace_entries": 0, "sim_time": (at.session_state["state"] or {}).get("sim_time")}


def _review(at, script):
    """Close, reflect, compare and plan, the way the page asks for it."""
    REVIEW_RESPONSE_FIELDS = _app_constant("REVIEW_RESPONSE_FIELDS")
    ADAPTATION_PLAN_FIELDS = _app_constant("ADAPTATION_PLAN_FIELDS")
    _click(at, "Complete Encounter & Begin Review")
    if _button(at, "Finish now"):
        # No destination stands: the warning never blocks; the script says how
        # the encounter ends (faculty decision 9, 2026-09-25).
        kind = script.get("close", "clinical_close")
        next(item for item in at.radio if item.label == "How is this encounter ending?").set_value(kind).run()
        _click(at, "Finish now")
    for _ in range(40):
        areas = {item.label: item for item in at.text_area}
        for field, label in REVIEW_RESPONSE_FIELDS:
            if label in areas and not areas[label].value:
                areas[label].set_value(script["reflection"].get(field, "Sin respuesta."))
        if _button(at, "Next decision"):
            _click(at, "Next decision")
            continue
        break
    lock = _button(at, "Lock Decision Review & Reveal Expert Comparison")
    if lock is None or lock.disabled:
        at.run()
        lock = _button(at, "Lock Decision Review & Reveal Expert Comparison")
    if lock is None:
        raise RehearsalStop("The reflection could not be locked.")
    lock.click().run()
    for _ in range(40):
        areas = {item.label: item for item in at.text_area}
        for label, value in (("Where did your reasoning align with this model?", script["comparison"]["alignment"]),
                             ("What will you change or preserve next time?", script["comparison"]["adjustment"])):
            if label in areas and not areas[label].value:
                areas[label].set_value(value)
        if _button(at, "Next comparison"):
            _click(at, "Next comparison")
            continue
        break
    _click(at, "Continue to Adaptation Plan")
    areas = at.text_area
    for field, label in ADAPTATION_PLAN_FIELDS:
        target = next((item for item in areas if item.label.startswith(label)), None)
        if target is not None:
            target.set_value(script["plan"].get(field, "Sin respuesta."))
    _click(at, "Continue to Final Summary")
    return bool(at.session_state["review_completed"]) if "review_completed" in at.session_state else False


def _declare_synthetic(at):
    """The closing question: this run was an automated agent's (a test account may say so)."""
    box = next((item for item in at.checkbox if item.label.startswith(
        "This encounter was run by an automated agent")), None)
    if box is None:
        return False
    box.check()
    save = next((item for item in at.button if item.label == "Save my answer"), None)
    if save is None:
        return False
    save.click().run()
    return True


@contextmanager
def _pinned_seed(seed):
    """The encounter's random seed, fixed for a rehearsal that must be repeatable.

    A launch draws its seed with ``secrets.randbelow``, and a few things depend
    on it -- whether a patient vomits with morphine (analgesia), the noise of a
    rhythm strip. Two rehearsals compared decision by decision need the same
    seed; rehearsing with several seeds shows what a paid run may meet. Only
    seeds are drawn with ``randbelow``: tokens and passwords are not touched.
    """
    if seed is None:
        yield
        return
    import secrets
    real = secrets.randbelow
    secrets.randbelow = lambda bound: int(seed) % bound
    try:
        yield
    finally:
        secrets.randbelow = real


def rehearse(script, workdir, seed=None):
    """One script through the real page, offline. A finding is returned, never raised."""
    with _pinned_seed(seed):
        result = _rehearse(script, workdir)
    result["language"] = script.get("language", "es")
    if seed is not None:
        result["seed"] = seed
    return result


def _rehearse(script, workdir):
    from streamlit.testing.v1 import AppTest
    import curriculum_runtime
    from account_store import AccountStore, hash_password
    from resident_profile import ProfileStore
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{workdir / ('rehearsal-%02d.sqlite3' % script['number'])}"
    started = time.monotonic()
    result = {"number": script["number"], "case_id": script["case_id"],
              "category": script["category"], "steps": [], "stopped": None}
    with _environment({"MRS_AUTH_MODE": "accounts", "MRS_DATABASE_URL": url,
                       "MRS_ALLOW_LOCAL_SQLITE": "true", "MRS_OFFLINE_CASES": "1",
                       "MRS_DEFAULT_VARIANT": script["case_id"],
                       "MRS_SYNTHETIC_ACCOUNTS": TEST_ACCOUNT}):
        store = AccountStore(url, allow_sqlite=True)
        store.bootstrap_admin("ensayo_admin", hash_password("rehearsal-only-password"))
        admin = store.authenticate("ensayo_admin", "rehearsal-only-password")
        code = store.create_invite(admin, "resident", 3)
        token = store.register(TEST_ACCOUNT, "rehearsal-only-resident", code)
        # The one-time photograph agreement, declined, as a first sign-in would.
        ProfileStore(store).decline(token)
        real = curriculum_runtime.assign_challenge
        # A rehearsal pins the case here; the batch chooses it the way a
        # faculty member does, with a directive (encounter_directives,
        # docs/TANDA_20_ESCENARIOS.md section 3).
        curriculum_runtime.assign_challenge = lambda *args, **kwargs: {
            "challenge_id": script["challenge"], "reason": "rehearsal_pinned",
            "assignment_seed": 17, "competence_decision": "Not assessed automatically"}
        try:
            at = AppTest.from_file(APP, default_timeout=120)
            at.session_state["_account_token"] = token
            at.run()
            _click(at, "Begin Encounter")
            if at.exception:
                raise RehearsalStop("The launch raised: " + str(at.exception[0].value)[:500])
            drawn = ((at.session_state["state"] or {}).get("encounter_spec") or {}).get("variant_id")
            result["drawn_case"] = drawn
            if drawn != script["case_id"]:
                raise RehearsalStop(f"The launch drew {drawn!r}, not {script['case_id']!r}.")
            steps = list(script["steps"])
            for index, step in enumerate(steps):
                if step[0] in ("answer", "complete") and not _pending(at):
                    # The script expected a question that never came: sending the
                    # answer anyway would put a stray entry in the record.
                    result.setdefault("answers_not_needed", []).append(index)
                    continue
                outcome = _step(at, step)
                result["steps"].append(outcome)
                following = steps[index + 1][0] if index + 1 < len(steps) else None
                if outcome["held"] and following not in ("complete", "answer", "cancel"):
                    # Held and the script says nothing about it: a finding about
                    # the script (or the reader). Resolved so the rest of the
                    # rehearsal still means something.
                    result.setdefault("unanticipated_holds", []).append(
                        {"step": index, "kind": outcome["held"], "said": outcome["said"][-1:]})
                    result["steps"].append(_resolve(at, outcome["held"], script.get("language", "es")))
            if _pending(at):
                result["pending_at_close"] = _pending(at)
            result["sim_time_at_close"] = (at.session_state["state"] or {}).get("sim_time")
            result["review_completed"] = _review(at, script)
            result["synthetic_declared"] = _declare_synthetic(at)
            if at.exception:
                raise RehearsalStop("The review raised: " + str(at.exception[0].value)[:500])
        except RehearsalStop as stop:
            result["stopped"] = str(stop)
        except Exception as error:  # the tool's own failure, reported as such
            result["stopped"] = f"{type(error).__name__}: {error}"
        finally:
            curriculum_runtime.assign_challenge = real
        attempts = [a for a in store.list_attempts(admin) if a["username"] == TEST_ACCOUNT]
        if attempts:
            record = store.get_attempt(admin, attempts[0]["id"])
            session = (record.get("payload") or {}).get("session") or {}
            trace = session.get("management_trace") or []
            result.update({
                "attempt_status": record["status"],
                "trace_entries": len(trace),
                "decisions_executed": sum(1 for e in trace if e.get("execution_status") == "executed"),
                "not_executed": [e.get("learner_input", "")[:120] for e in trace
                                 if e.get("execution_status") in ("not_executed", "clarification_required")],
                "read_as_nothing": [e.get("learner_input", "")[:120] for e in trace if _read_as_nothing(e)],
            })
            import encounter_context
            context = encounter_context.EncounterContextStore(store).current(admin, attempts[0]["id"])
            result["execution_declared"] = (context.get("execution") or {}).get("value")
    result["seconds"] = round(time.monotonic() - started, 1)
    return result


_ONLY_A_REASSESSMENT = re.compile(r"\s*(?:reeval\w*\s+en|reassess\w*\s+in)\s+\d+\s+min\w*[^.]*\.?\s*",
                                  re.I)


def _read_as_nothing(entry):
    """A decision the page accepted and that did nothing: the order was not read.

    Scenario 7's discharge, "Lo doy de alta con analgesia, control urologico y
    regresar si tiene fiebre", ran as an executed decision with no action at all:
    the page said nothing, and neither "held" nor "not executed" noticed it
    (2026-09-25). A decision whose own words read as no order, and nothing kept as
    a plan, is named here so that a person reads it.
    """
    from family_parser import parse_family_actions
    if entry.get("execution_status") != "executed":
        return False
    text = str(entry.get("learner_input") or "").split("\n\nReasoning clarification:")[0]
    if _ONLY_A_REASSESSMENT.fullmatch(text):
        return False
    parsed = parse_family_actions(text)
    return not parsed["recognized_future_actions"] and not [
        action for action in parsed["actions"] if action.get("type") != "reassessment"]


def summary_markdown(results):
    english = any(r.get("language") == "en" for r in results)
    lines = ["# Ensayo offline de la tanda de 20 · no es evidencia de la tanda"
             + (" · órdenes en inglés" if english else ""), "",
             "Cada guion pasó por la página real (app.py) con Streamlit en proceso, una base "
             "temporal, sin clave y con el caso fijado. Sirve para encontrar lo que detendría "
             "a un residente antes de gastar un encuentro pagado.", "",
             "| # | Caso | Trayectoria | Pasos | Retenidas no previstas | Decisiones sin acción leída "
             "| Min. al cierre | Revisión | Estado | Detención |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['number']} | {r['case_id']} | {r['category']} | {len(r['steps'])} | "
                     f"{len(r.get('unanticipated_holds', []))} | {len(r.get('read_as_nothing', []))} | "
                     f"{r.get('sim_time_at_close', '')} | "
                     f"{'completa' if r.get('review_completed') else '-'} | "
                     f"{r.get('attempt_status', '')} | {r['stopped'] or ''} |")
    return "\n".join(lines) + "\n"


def _scripts(language):
    if language == "en":
        import tanda20_en as scripts
    else:
        import tanda20 as scripts
    return scripts.BY_NUMBER, scripts.SCRIPTS


def local_check(number, workdir, port=8599, language="es"):
    """The runner itself, in a real browser, against a local offline copy of the app.

    A temporary database with a faculty test account and a local copy of the
    resident account, a Streamlit server with no key, and one scenario played
    end to end without the paid steps. It proves the runner still fits the
    page before anything is spent; it is not evidence for the batch.
    """
    import subprocess
    import time as _time
    import urllib.request
    from account_store import AccountStore, hash_password
    from resident_profile import ProfileStore
    BY_NUMBER, _ = _scripts(language)
    import tanda20_runner
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    database = workdir / "accounts.sqlite3"
    if database.exists():
        database.unlink()
    url = f"sqlite:///{database}"
    store = AccountStore(url, allow_sqlite=True)
    store.bootstrap_admin("admin_local", hash_password("local-admin-password"))
    admin = store.authenticate("admin_local", "local-admin-password")
    faculty = store.register("faculty_agente_local", "local-faculty-password",
                             store.create_invite(admin, "faculty", None))
    resident = store.register(TEST_ACCOUNT, "local-resident-password",
                              store.create_invite(admin, "resident", 3))
    ProfileStore(store).decline(resident)
    # Since faculty decision 14 a faculty member directs only the residents an
    # administrator authorized them for: the local copy is set up as the real
    # app has to be.
    from encounter_directives import DirectiveStore
    DirectiveStore(store).grant(admin, store.get_user(faculty)["id"], store.get_user(resident)["id"],
                                "Local check of the batch runner")
    env = {**os.environ, "MRS_AUTH_MODE": "accounts", "MRS_DATABASE_URL": url,
           "MRS_ALLOW_LOCAL_SQLITE": "true", "MRS_OFFLINE_CASES": "1",
           "MRS_SYNTHETIC_ACCOUNTS": TEST_ACCOUNT, "NO_PROXY": "localhost,127.0.0.1",
           "no_proxy": "localhost,127.0.0.1"}
    env.pop("OPENAI_API_KEY", None)
    server = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", APP, "--server.port", str(port),
         "--server.headless", "true", "--browser.gatherUsageStats", "false"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(60):
            try:
                if opener.open(f"http://localhost:{port}/", timeout=2).status == 200:
                    break
            except OSError:
                _time.sleep(1)
        os.environ.update({"MRS_BATCH_RESIDENT_PASSWORD": "local-resident-password",
                           "MRS_BATCH_STAFF_USER": "faculty_agente_local",
                           "MRS_BATCH_STAFF_PASSWORD": "local-faculty-password",
                           "NO_PROXY": "localhost,127.0.0.1", "no_proxy": "localhost,127.0.0.1"})
        checks = tanda20_runner.preflight(base_url=f"http://localhost:{port}")
        entry = tanda20_runner.run_scenario(BY_NUMBER[number], base_url=f"http://localhost:{port}",
                                            out=workdir / "run", with_ai=False)
        entry["preflight"] = checks
        attempts = [a for a in store.list_attempts(admin) if a["username"] == TEST_ACCOUNT]
        if attempts:
            record = store.get_attempt(admin, attempts[0]["id"])
            session = (record.get("payload") or {}).get("session") or {}
            entry["stored"] = {"status": record["status"],
                               "case": ((session.get("state") or {}).get("encounter_spec") or {}).get("variant_id"),
                               "assignment": session.get("encounter_assignment", {}).get("reason")}
        return entry
    finally:
        server.terminate()
        server.wait(timeout=30)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--rehearse", nargs="?", const="all", metavar="N|all")
    parser.add_argument("--local-check", type=int, metavar="N",
                        help="free: the browser runner against a local offline copy of the app")
    parser.add_argument("--preflight", action="store_true",
                        help="free: sign in with both test accounts on the app and check what a paid run needs")
    parser.add_argument("--run", metavar="N[,M...]", help="PAID: scenarios through the development app")
    parser.add_argument("--base-url", help="the development app, for --run")
    parser.add_argument("--staff-documents", type=int, metavar="N",
                        help="the staff half only (brief, rubric proposal, documents B-D) of scenario N, "
                             "whose encounter is already completed; no encounter is started")
    parser.add_argument("--no-ai", action="store_true", help="--run without the paid documents")
    parser.add_argument("--out", default="local-data/tanda20/rehearsal")
    parser.add_argument("--language", choices=("es", "en"), default="es",
                        help="the Spanish scripts or their English version (tanda20_en), for "
                             "--rehearse, --local-check and --run")
    parser.add_argument("--seed", type=int, help="--rehearse with the encounter seed pinned")
    args = parser.parse_args(argv)
    if args.local_check:
        entry = local_check(args.local_check, ROOT / "local-data" / "tanda20" / "local-check",
                            language=args.language)
        print(json.dumps({k: v for k, v in entry.items() if k != "steps"}, indent=1, ensure_ascii=False))
        return 0 if not entry["stopped"] else 1
    if args.preflight:
        if not args.base_url:
            parser.error("--preflight needs --base-url (the development app).")
        import tanda20_runner
        checks = tanda20_runner.preflight(base_url=args.base_url)
        for row in checks:
            print(("ok     " if row["ok"] else "MISSING") + f" {row['check']}" + (f": {row['detail']}" if row["detail"] else ""))
        return 0 if checks and all(row["ok"] for row in checks) else 1
    if args.staff_documents:
        if not args.base_url:
            parser.error("--staff-documents needs --base-url (the development app).")
        import tanda20_runner
        BY_NUMBER, _ = _scripts(args.language)
        out = ROOT / "local-data" / "tanda20" / "batch"
        out.mkdir(parents=True, exist_ok=True)
        entry = tanda20_runner.finish_staff_documents(BY_NUMBER[args.staff_documents],
                                                      base_url=args.base_url, out=out)
        print(f"{args.staff_documents:>2} {entry['case_id']:<30} stopped={entry['stopped']} "
              f"documents={sorted(entry['documents'])}", flush=True)
        return 1 if entry["stopped"] else 0
    if args.run:
        if not args.base_url:
            parser.error("--run needs --base-url (the development app).")
        import tanda20_runner
        BY_NUMBER, _ = _scripts(args.language)
        # One ledger for both languages: the limit of paid encounters counts every
        # run, and an English run is not a second budget.
        out = ROOT / "local-data" / "tanda20" / "batch"
        out.mkdir(parents=True, exist_ok=True)
        for number in [int(n) for n in args.run.split(",")]:
            entry = tanda20_runner.run_scenario(BY_NUMBER[number], base_url=args.base_url, out=out,
                                                with_ai=not args.no_ai)
            print(f"{number:>2} {entry['case_id']:<30} stopped={entry['stopped']} "
                  f"documents={sorted(entry['documents'])}", flush=True)
            if entry["stopped"]:
                return 1
        return 0
    if args.plan or not args.rehearse:
        for row in plan():
            print(f"{row['number']:>2} {row['case_id']:<30} {row['category']:<13} {row['challenge']} "
                  f"events={','.join(row['declared_events'])}")
        return 0
    BY_NUMBER, SCRIPTS = _scripts(args.language)
    chosen = SCRIPTS if args.rehearse == "all" else [BY_NUMBER[int(n)] for n in args.rehearse.split(",")]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / args.out / stamp
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for script in chosen:
        result = rehearse(script, out / "db", seed=args.seed)
        results.append(result)
        print(f"{script['number']:>2} {script['case_id']:<30} stopped={result['stopped']} "
              f"holds={len(result.get('unanticipated_holds', []))} status={result.get('attempt_status')} "
              f"t={result.get('sim_time_at_close')} ({result['seconds']} s)", flush=True)
        (out / f"{script['number']:02d}-{script['case_id']}.json").write_text(
            json.dumps(result, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    (out / "summary.md").write_text(summary_markdown(results), encoding="utf-8")
    print("written:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
