"""The paid run of the twenty-scenario batch, through the real app, in a browser.

Only this counts as the batch (faculty specification of 2026-09-24, section 4):
the development app, the real ``residente_prueba_r3`` account, the persistent
database, every step through the page a person uses. It never writes to the
database itself and never confirms an evaluation.

Per scenario:

1. **Staff** (a faculty test account, never a real faculty member's): directs
   the resident's next encounter to the scenario's case, with its reason.
2. **Resident** (``residente_prueba_r3``): signs in, begins the encounter,
   plays the script -- asking, examining, ordering, answering the follow-up
   questions -- closes, reflects, plans, declares the run a synthetic test, and
   generates the analysed Management Trace (paid).
3. **Staff**: opens the encounter, generates the AI faculty brief and the AI
   rubric proposal (paid), and downloads the four documents to prove they can
   be retrieved. Every evaluation is left pending.
4. **Ledger**: one line per attempt, with what it cost in encounters; a new
   paid encounter is refused once the authorised total is reached.

Credentials come from the environment and are never printed or stored:
``MRS_BATCH_RESIDENT_PASSWORD`` (and ``MRS_BATCH_RESIDENT_USER``, default
``residente_prueba_r3``), ``MRS_BATCH_STAFF_USER`` and ``MRS_BATCH_STAFF_PASSWORD``.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUTHORISED_PAID_ENCOUNTERS = 40
BROWSER = os.environ.get("MRS_BATCH_BROWSER", "/opt/pw-browsers/chromium")
# The batch cannot run from a cloud session whose proxy refuses WebSocket
# upgrades: a Streamlit page needs one (/_stcore/stream). It runs from a machine
# with direct access -- a computer or a Codespace -- where Playwright's own
# Chromium is used when the cloud image's path does not exist.


def launch(playwright, headless=True):
    """Chromium: the configured one, or Playwright's own (``playwright install chromium``)."""
    if Path(BROWSER).exists():
        return playwright.chromium.launch(executable_path=BROWSER, headless=headless)
    return playwright.chromium.launch(headless=headless)


class RunStop(Exception):
    """The page did not let the run go on: recorded as a finding."""


class Page:
    """A Streamlit page, driven the way a person drives it."""

    def __init__(self, page, *, timeout=120):
        self.page = page
        self.timeout = timeout

    # -- waiting ------------------------------------------------------------
    def settle(self, quiet=0.8):
        """Wait until Streamlit has finished re-running the script.

        The app element carries the script's state (``data-test-script-state``,
        what Streamlit's own end-to-end tests wait on); a rerun can start a
        moment after a click, so the state has to stay "notRunning" for a while.
        """
        deadline = time.monotonic() + self.timeout
        calm_since = None
        while time.monotonic() < deadline:
            state = self.page.evaluate(
                "() => { const app = document.querySelector('[data-testid=\"stApp\"]');"
                " return app ? app.getAttribute('data-test-script-state') : null; }")
            if state == "notRunning":
                if calm_since is None:
                    calm_since = time.monotonic()
                elif time.monotonic() - calm_since >= quiet:
                    return
            else:
                calm_since = None
            time.sleep(0.15)
        raise RunStop("The page kept running for longer than the timeout.")

    def wait_for_text(self, text):
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if text in self.text():
                self.settle()
                return
            time.sleep(0.25)
        raise RunStop(f"{text!r} never appeared on the page.")

    # -- widgets ------------------------------------------------------------
    def button(self, label):
        return self.page.get_by_role("button", name=label, exact=True)

    def has_button(self, label):
        return self.button(label).count() > 0

    def click(self, label):
        target = self.button(label)
        if not target.count():
            raise RunStop(f"The page offers no {label!r} button.")
        target.first.click()
        self.settle()

    def _commit(self, field, text):
        # Streamlit sends a text field's value when the field loses focus.
        field.fill(str(text))
        field.press("Tab")
        self.settle()

    def fill(self, label, text):
        field = self.page.get_by_label(label, exact=True)
        if not field.count():
            raise RunStop(f"There is no field {label!r} on the page.")
        self._commit(field.first, text)

    def fill_starting(self, prefix, text):
        field = self.page.locator(f'textarea[aria-label^="{prefix}"], input[aria-label^="{prefix}"]')
        if not field.count():
            raise RunStop(f"There is no field starting {prefix!r} on the page.")
        self._commit(field.first, text)

    def _labelled(self, testid, label):
        """The widget whose own label reads exactly ``label``."""
        exact = re.compile(r"^\s*" + re.escape(label) + r"\s*$")
        return self.page.locator(f'[data-testid="{testid}"]').filter(
            has=self.page.locator('[data-testid="stWidgetLabel"]').filter(has_text=exact))

    def radio(self, label, option):
        group = self._labelled("stRadio", label)
        if not group.count():
            raise RunStop(f"There is no choice {label!r} on the page.")
        group.first.get_by_text(option, exact=True).click()
        self.settle()

    def select(self, label, option):
        box = self._labelled("stSelectbox", label)
        if not box.count():
            raise RunStop(f"There is no selector {label!r} on the page.")
        # A react-aria combobox in this Streamlit: typing filters the list.
        combo = box.first.locator('input[role="combobox"]')
        combo.click()
        combo.fill(option)
        choice = self.page.get_by_role("option", name=option, exact=True)
        if not choice.count():
            choice = self.page.get_by_role("option").filter(has_text=option)
        if not choice.count():
            raise RunStop(f"{option!r} is not offered in {label!r}.")
        choice.first.click()
        self.settle()

    def offers(self, label, option):
        """Whether a selector offers ``option``, asked without choosing anything.

        The same filtering ``select`` uses -- type, and see what the list shows
        -- then the list is closed with the choice untouched.
        """
        box = self._labelled("stSelectbox", label)
        if not box.count():
            raise RunStop(f"There is no selector {label!r} on the page.")
        combo = box.first.locator('input[role="combobox"]')
        combo.click()
        # A click focuses the field; the arrow opens the list. Typing the value
        # already chosen would not open it at all.
        combo.press("ArrowDown")
        options = self.page.get_by_role("option")
        try:
            options.first.wait_for(timeout=5_000)
        except Exception:
            pass  # an empty selector opens no list
        offered = any(text.strip() == option for text in options.all_inner_texts())
        if not offered and options.count():
            # A long list is filtered, as ``select`` does.
            combo.fill(option)
            offered = any(text.strip() == option for text in options.all_inner_texts())
        combo.press("Escape")
        self.settle()
        return offered

    def check(self, label):
        self.page.get_by_text(label, exact=True).first.click()

    def open(self, expander):
        summary = self.page.locator('[data-testid="stExpander"] summary').filter(has_text=expander)
        if not summary.count():
            raise RunStop(f"There is no section {expander!r} on the page.")
        if summary.first.get_attribute("aria-expanded") != "true":
            summary.first.click()
            self.settle()

    def text(self):
        return self.page.locator("body").inner_text()

    def download(self, label, folder, name):
        target = self.button(label)
        if not target.count():
            target = self.page.locator('[data-testid="stDownloadButton"]').filter(has_text=label)
        if not target.count():
            raise RunStop(f"There is no download {label!r} on the page.")
        with self.page.expect_download(timeout=self.timeout * 1000) as info:
            target.first.click()
        path = Path(folder) / name
        info.value.save_as(path)
        # A download button reruns the script: the next widget exists only after it.
        self.settle()
        return path


# --- the three sessions ------------------------------------------------------------

def sign_in(page, base_url, username, password):
    page.page.goto(base_url, wait_until="networkidle")
    page.settle()
    if not page.page.get_by_label("Username", exact=True).count():
        # Streamlit Community Cloud sends every visit through its own sign-in at
        # share.streamlit.io first. A public app passes straight through; a
        # private one asks for a Streamlit account the runner does not have.
        where = page.page.url
        if "share.streamlit.io" in where or "streamlit.io/-/auth" in where:
            raise RunStop("Streamlit asks for its own sign-in before showing the app (" + where.split("?")[0]
                          + "): the app is private on Streamlit Community Cloud. Make it viewable by anyone "
                            "with the link for the batch -- the simulator still requires its own accounts.")
        raise RunStop(f"The simulator's sign-in form is not on the page at {where.split('?')[0]}.")
    page.fill("Username", username)
    page.fill("Password", password)
    page.click("Sign in")
    try:
        page.wait_for_text("Sign out")
    except RunStop:
        raise RunStop(f"{username} could not sign in.") from None


# On a person's own computer the passwords may live in this file instead of the
# environment: local-data/ is never committed, and nothing here prints them.
CREDENTIALS_FILE = ROOT / "local-data" / "tanda20" / "credentials.env"
# The only names read, from the environment or the file. A fixed list, not a
# resolver of any name: nothing here can read a provider key.
BATCH_CREDENTIALS = ("MRS_BATCH_RESIDENT_USER", "MRS_BATCH_RESIDENT_PASSWORD",
                     "MRS_BATCH_STAFF_USER", "MRS_BATCH_STAFF_PASSWORD")


def _stored_credentials(path=None):
    """The batch's NAME=value lines from the local credentials file, if there is one."""
    path = Path(path or CREDENTIALS_FILE)
    values = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() in BATCH_CREDENTIALS:
                values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def credentials():
    """The two test accounts: the environment first, then the local file; never printed."""
    stored = _stored_credentials()
    found = {key: os.environ.get(key, "") or stored.get(key, "") for key in BATCH_CREDENTIALS}
    resident_user = found["MRS_BATCH_RESIDENT_USER"] or "residente_prueba_r3"
    resident_password = found["MRS_BATCH_RESIDENT_PASSWORD"]
    staff_user = found["MRS_BATCH_STAFF_USER"]
    staff_password = found["MRS_BATCH_STAFF_PASSWORD"]
    if not (resident_password and staff_user and staff_password):
        where = (CREDENTIALS_FILE.relative_to(ROOT) if CREDENTIALS_FILE.is_relative_to(ROOT)
                 else CREDENTIALS_FILE)
        raise SystemExit("MRS_BATCH_RESIDENT_PASSWORD, MRS_BATCH_STAFF_USER and "
                         "MRS_BATCH_STAFF_PASSWORD are required, as environment variables or "
                         f"as NAME=value lines in {where}.")
    return resident_user, resident_password, staff_user, staff_password


NOT_IN_SCOPE = "No resident has been assigned to you for choosing cases"
# The caption of case direction since faculty decision 14 (commit 38c45c6).
SCOPED_CAPTION = "the resident is not told that the case was chosen"


def preflight(*, base_url, headless=True):
    """Free: what a paid run needs, checked on the real app before anything is spent.

    Signs in as the faculty test account and as the resident, and only reads:
    no encounter is started, no directive is saved and nothing is generated
    (signing in opens a session, as any sign-in does). Each check says what is
    missing and who can fix it. Whether the app lets the resident declare a
    synthetic run (MRS_SYNTHETIC_ACCOUNTS) can only be seen at the end of an
    encounter, so it is not checked here.
    """
    from playwright.sync_api import sync_playwright
    resident_user, resident_password, staff_user, staff_password = credentials()
    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": "" if ok else detail})
        return bool(ok)

    with sync_playwright() as playwright:
        browser = launch(playwright, headless)
        try:
            staff = Page(browser.new_context().new_page())
            try:
                sign_in(staff, base_url, staff_user, staff_password)
            except RunStop as stop:
                check("staff_sign_in", False, f"{stop} The faculty test account must exist in this app, "
                                              "with the password in MRS_BATCH_STAFF_PASSWORD.")
                return checks
            check("staff_sign_in", True)
            sidebar = staff.page.locator('[data-testid="stSidebar"]').inner_text()
            check("staff_is_faculty", re.search(r"^\s*Faculty\s*$", sidebar, re.M),
                  "The batch directs cases and generates the AI drafts with a faculty test account, "
                  "never with an administrator's or a real faculty member's.")
            try:
                staff.open("Resident activity and recorded evidence")
                staff.open("Direct a resident's next encounter")
            except RunStop:
                check("case_direction", False, "This app does not offer case direction: it does not run "
                                               "the branch clinical-encounter-v0.13.")
                return checks
            check("case_direction", True)
            text = staff.text()
            check("scoped_direction", SCOPED_CAPTION in text,
                  "This app runs a version older than faculty decision 14 (commit 38c45c6): deploy the "
                  "branch's latest commit to it.")
            if NOT_IN_SCOPE in text:
                check("staff_authorized_for_resident", False,
                      f"An administrator of this app must authorize {staff_user} for {resident_user}: "
                      "Resident activity and recorded evidence -> Who may choose a resident's cases.")
            else:
                check("staff_authorized_for_resident", staff.offers("Resident", resident_user),
                      f"{resident_user} is not among the residents this account may direct: the account "
                      "is not in this app's database, or it is not authorized for it.")
            resident = Page(browser.new_context().new_page())
            try:
                sign_in(resident, base_url, resident_user, resident_password)
            except RunStop as stop:
                check("resident_sign_in", False, f"{stop} The resident test account must exist in this app, "
                                                 "with the password in MRS_BATCH_RESIDENT_PASSWORD.")
                return checks
            check("resident_sign_in", True)
            if resident.has_button("Resume encounter"):
                check("resident_ready", False, "The account has an active encounter: finish or abandon it in "
                                               "the app before the batch starts.")
            else:
                check("resident_ready", resident.has_button("Begin Encounter"),
                      "The page offers neither Begin nor Resume: the one-time account setup is probably "
                      "pending. Sign in once as the resident and complete it.")
        finally:
            browser.close()
    return checks


def direct(page, script, resident):
    """Staff: the resident's next case is this scenario's, and why."""
    page.open("Resident activity and recorded evidence")
    page.open("Direct a resident's next encounter")
    if "No resident has been assigned to you for choosing cases" in page.text():
        raise RunStop(f"The staff account is not authorized to choose {resident}'s cases. An "
                      "administrator authorizes it under «Who may choose a resident's cases».")
    page.select("Challenge", script["challenge"] + " · ")
    page.select("Resident", resident)
    page.select("Case", script["case_id"])
    page.fill("Why this case", f"Tanda sintética 2026-09-24 · escenario {script['number']} · "
                              f"{script['category']}"
                              + (" · órdenes en inglés" if script.get("language") == "en" else ""))
    page.click("Save directive")
    if "Saved. The resident's next encounter will use this case." not in page.text():
        raise RunStop("The directive was not saved.")


def pending(page):
    return page.has_button("Cancel pending orders")


def step(page, action):
    kind = action[0]
    if kind == "ask":
        page.radio("Encounter", "Talk")
        field = page.page.locator('input[aria-label="Ask the patient"], '
                                  'input[aria-label="Ask the available history source"]')
        if not field.count():
            raise RunStop("There is nobody to ask on the page.")
        field.first.fill(action[1])
        page.click("Ask")
    elif kind == "examine":
        page.radio("Encounter", "Examine")
        page.select("Examine", action[1])
        page.click("Examine patient")
    elif kind in ("order", "answer"):
        page.radio("Encounter", "Treat")
        page.fill("Enter your clinical reasoning and/or actions", action[1])
        page.click("Submit")
    elif kind == "complete":
        for label, value in action[1].items():
            if label == "delay":
                page.page.get_by_label("I will check in… minutes").first.fill(str(value))
            else:
                page.fill_starting(label, value)
        page.click("Complete reasoning & execute held order")
    elif kind == "cancel":
        page.click("Cancel pending orders")
    elif kind == "recover":
        page.click("Save & return to dashboard")
        page.click("Resume encounter")
    else:
        raise ValueError(kind)


def play(page, script, log):
    """Resident: the encounter, the reflection, the declaration and document A."""
    if page.has_button("Resume encounter"):
        # Another scenario's encounter is still open. Resuming it would play
        # this script on the wrong patient; abandoning it could lose paid work.
        raise RunStop("This account already has an active encounter. Finish or abandon it in "
                      "the app before starting the next scenario.")
    page.click("Begin Encounter")
    steps = list(script["steps"])
    for index, action in enumerate(steps):
        if action[0] in ("answer", "complete") and not pending(page):
            log.append({"step": index, "note": "the follow-up question never came; answer not sent"})
            continue
        step(page, action)
        following = steps[index + 1][0] if index + 1 < len(steps) else None
        if pending(page) and following not in ("answer", "complete", "cancel"):
            # A question the script did not expect: a finding, stated and
            # stopped, never answered with invented words in the real batch.
            raise RunStop(f"Step {index} was held and the script has no answer for it.")
        log.append({"step": index, "kind": action[0], "ok": True})
    page.click("Complete Encounter & Begin Review")
    if page.has_button("Finish now"):
        # No destination stands: the page warns without blocking and asks how the
        # encounter ends (faculty decision 9). The script says; nothing is invented.
        import encounter_close
        kind = script.get("close", "clinical_close")
        page.radio("How is this encounter ending?", encounter_close.LABELS[kind])
        page.click("Finish now")
        log.append({"note": f"closed without a destination, declared as {kind}"})
    from tools_tanda20 import _app_constant
    for _ in range(40):
        for field, label in _app_constant("REVIEW_RESPONSE_FIELDS"):
            locator = page.page.get_by_label(label, exact=True)
            if locator.count() and not locator.first.input_value():
                page._commit(locator.first, script["reflection"][field])
        if page.has_button("Next decision"):
            page.click("Next decision")
            continue
        break
    page.click("Lock Decision Review & Reveal Expert Comparison")
    for _ in range(40):
        for field, label in _app_constant("EXPERT_COMPARISON_FIELDS"):
            locator = page.page.get_by_label(label, exact=True)
            if locator.count() and not locator.first.input_value():
                page._commit(locator.first, script["comparison"][field])
        if page.has_button("Next comparison"):
            page.click("Next comparison")
            continue
        break
    page.click("Continue to Adaptation Plan")
    for field, label in _app_constant("ADAPTATION_PLAN_FIELDS"):
        # Some fields arrive drafted from the reflection, and once the plan is
        # complete the review closes itself: follow the page, do not assume it.
        box = page.page.locator(f'textarea[aria-label^="{label}"]')
        if box.count():
            page._commit(box.first, script["plan"][field])
    if page.has_button("Continue to Final Summary"):
        page.click("Continue to Final Summary")
    page.check("This encounter was run by an automated agent (synthetic test)")
    page.click("Save my answer")
    if "Saved. You can change it at any time" not in page.text():
        raise RunStop("The synthetic-run declaration was not saved.")


# The alert boxes after the "Your Management Trace" heading: what the page said
# about the analysis, and nothing from the rest of the review.
TRACE_ALERTS = """() => {
  const heading = [...document.querySelectorAll('h1,h2,h3')]
    .find(h => h.textContent.trim() === 'Your Management Trace');
  if (!heading) return [];
  return [...document.querySelectorAll('[data-testid="stAlert"]')]
    .filter(a => heading.compareDocumentPosition(a) & Node.DOCUMENT_POSITION_FOLLOWING)
    .map(a => a.innerText.trim())
    .filter(t => t && !t.startsWith('Your analysis was not available'));
}"""


def resident_document(page, folder, script):
    """Document A: the analysed Management Trace, generated on first view (paid).

    The analysis can outlast the page's usual wait, and a first attempt the
    provider fails leaves a retry button: it is pressed once, never more.
    """
    usual, page.timeout = page.timeout, max(page.timeout, GENERATION_TIMEOUT)
    try:
        attempts_failed = 0
        reasons = []  # what the page said about each failed attempt
        deadline = time.monotonic() + GENERATION_TIMEOUT
        while time.monotonic() < deadline:
            page.settle()
            if "Download Management Trace PDF" in page.text():
                return str(page.download("Download Management Trace PDF", folder,
                                         f"{script['number']:02d}-A-management_trace.pdf"))
            # A failed attempt says why in an error box in the run that made it;
            # the retry button only appears on the next run.
            errors = page.page.evaluate(TRACE_ALERTS)
            fresh = [text for text in errors if text and text not in reasons]
            reasons.extend(fresh)
            if page.has_button("Retry Management Trace analysis") or fresh:
                attempts_failed += 1
                if attempts_failed >= 2:
                    raise RunStop("The Management Trace analysis failed twice (one retry): "
                                  + (" | ".join(reasons) or "the page gave no reason"))
                if not page.has_button("Retry Management Trace analysis"):
                    # Streamlit's own rerun shortcut: same session, and the button appears.
                    page.page.locator("body").press("r")
                    page.settle()
                page.click("Retry Management Trace analysis")
                continue
            time.sleep(2)
        raise RunStop("'Download Management Trace PDF' never appeared on the page.")
    finally:
        page.timeout = usual


def reopen_latest_review(page):
    """Resident: open the newest completed review from the dashboard."""
    page.open("Previous completed reviews")
    dates = re.findall(r"Encounter review · (\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC)", page.text())
    buttons = page.button("Open review")
    if not dates or buttons.count() != len(dates):
        raise RunStop("The dashboard offers no completed review to open.")
    newest = max(range(len(dates)), key=lambda i: dates[i])
    buttons.nth(newest).click()
    page.settle()
    return dates[newest]


def open_latest_encounter(page, resident):
    """Staff: select the resident's newest completed encounter in the listing."""
    page.open("Resident activity and recorded evidence")
    box = page._labelled("stSelectbox", "Encounter record")
    if not box.count():
        raise RunStop("The staff listing offers no encounter record.")
    combo = box.first.locator('input[role="combobox"]')
    combo.click()
    # A click focuses the field; the arrow opens the list (as in ``offers``).
    combo.press("ArrowDown")
    try:
        page.page.get_by_role("option").first.wait_for(timeout=5_000)
    except Exception:
        pass  # no list: reported below as no completed encounter
    options = [text for text in page.page.get_by_role("option").all_inner_texts()
               if text.startswith(resident + " · ") and " · completed · " in text]
    if not options:
        raise RunStop(f"No completed encounter of {resident} is listed.")
    latest = max(options, key=lambda text: text.rsplit(" · ", 1)[-1])
    page.page.get_by_role("option", name=latest, exact=True).first.click()
    page.settle()
    return latest


GENERATION_TIMEOUT = 600  # seconds: a brief or a rubric proposal outlasts the page's usual wait


def staff_documents(page, folder, script, resident):
    """Staff: the AI brief and the AI rubric proposal (paid, once), and documents B-D."""
    usual, page.timeout = page.timeout, max(page.timeout, GENERATION_TIMEOUT)
    try:
        return _staff_documents(page, folder, script, resident)
    finally:
        page.timeout = usual


def _staff_documents(page, folder, script, resident):
    chosen = open_latest_encounter(page, resident)
    if f" · {script['challenge']} · " not in chosen:
        raise RunStop(f"The newest completed encounter ({chosen}) is not under this scenario's "
                      f"challenge {script['challenge']}: nothing is generated for it.")
    # Generated once. A "new" button means it already exists: not paid for twice.
    if page.has_button("Generate AI faculty brief"):
        page.click("Generate AI faculty brief")
    page.open("Management reasoning rubric - pilot 1.0")
    if page.has_button("Generate an AI proposal"):
        page.click("Generate an AI proposal")
    failure = page.page.locator('[data-testid="stException"]')
    if failure.count():
        # The app's own error hides every download below it: a finding, not
        # three "missing" documents on an otherwise clean line.
        raise RunStop("The faculty view of the encounter shows an application error: "
                      + " | ".join(failure.first.inner_text().splitlines()[:6]))
    saved = {"encounter": chosen}
    # The full analysis sits in a folded section of the brief.
    for label, name, section in (
            ("Download 2-page faculty brief (PDF)", "C-brief_compact.pdf", None),
            ("Download full faculty analysis (PDF)", "B-brief_full.pdf",
             "Read the analysis and debriefing questions"),
            ("Download rubric assessment (PDF)", "D-rubric.pdf", None)):
        try:
            if section:
                page.open(section)
            saved[name] = str(page.download(label, folder, f"{script['number']:02d}-{name}"))
        except Exception as missing:  # one document missing does not hide the others
            saved[name] = f"missing: {type(missing).__name__}: {str(missing).splitlines()[0][:300]}"
    return saved


# --- the ledger ------------------------------------------------------------------

def ledger_path(out):
    return Path(out) / "ledger.jsonl"


def spent(out):
    path = ledger_path(out)
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines()
               if line.strip() and json.loads(line).get("paid_encounter"))


def record(out, entry):
    with ledger_path(out).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def code_version():
    try:
        return subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], capture_output=True,
                              text=True, cwd=ROOT, timeout=5).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def run_scenario(script, *, base_url, out, with_ai=True, headless=True):
    """One scenario end to end. Returns the ledger entry; never raises for a finding."""
    from playwright.sync_api import sync_playwright
    resident_user, resident_password, staff_user, staff_password = credentials()
    if with_ai and spent(out) >= AUTHORISED_PAID_ENCOUNTERS:
        raise SystemExit(f"{AUTHORISED_PAID_ENCOUNTERS} paid encounters are already on the ledger. "
                         "No new paid encounter is started.")
    language = script.get("language", "es")
    folder = Path(out) / (f"{script['number']:02d}-{script['case_id']}" + ("-en" if language == "en" else ""))
    folder.mkdir(parents=True, exist_ok=True)
    entry = {"number": script["number"], "case_id": script["case_id"], "language": language,
             "category": script["category"], "started_at": datetime.now(timezone.utc).isoformat(),
             "code_version_local": code_version(), "base_url": base_url,
             "paid_encounter": bool(with_ai), "steps": [], "stopped": None, "documents": {}}
    with sync_playwright() as playwright:
        browser = launch(playwright, headless)
        try:
            staff = Page(browser.new_context(accept_downloads=True).new_page())
            sign_in(staff, base_url, staff_user, staff_password)
            direct(staff, script, resident_user)
            resident = Page(browser.new_context(accept_downloads=True).new_page())
            sign_in(resident, base_url, resident_user, resident_password)
            play(resident, script, entry["steps"])
            # The completed view replaces the review once every field is in.
            entry["review_completed"] = "Your Management Trace" in resident.text()
            if with_ai:
                try:
                    entry["documents"]["A-management_trace.pdf"] = resident_document(resident, folder, script)
                except RunStop as refused:
                    # The encounter is saved; the staff half does not depend on
                    # document A, which --resident-document can obtain later.
                    entry["documents"]["A-management_trace.pdf"] = f"missing: {refused}"
                # A reload opens a new Streamlit session, signed out: sign in again.
                failing = staff
                sign_in(staff, base_url, staff_user, staff_password)
                entry["documents"].update(staff_documents(staff, folder, script, resident_user))
        except Exception as stop:  # a finding about the page, or the tool's own failure
            entry["stopped"] = f"{type(stop).__name__}: {stop}"[:1000]
            try:
                shown = locals().get("failing") or (resident if "resident" in locals() else staff)
                (folder / "stopped.png").write_bytes(shown.page.screenshot(full_page=True))
            except Exception:
                pass
        finally:
            browser.close()
    entry["finished_at"] = datetime.now(timezone.utc).isoformat()
    record(out, entry)
    return entry


def finish_staff_documents(script, *, base_url, out, headless=True):
    """The staff half of a scenario whose encounter is already completed.

    For a run that stopped after the resident's encounter was saved: the
    encounter is not played again and no new encounter is started, so it is
    recorded as not paid. The brief and the rubric proposal are generated only
    if the encounter does not have them yet.
    """
    from playwright.sync_api import sync_playwright
    resident_user, _, staff_user, staff_password = credentials()
    language = script.get("language", "es")
    folder = Path(out) / (f"{script['number']:02d}-{script['case_id']}" + ("-en" if language == "en" else ""))
    folder.mkdir(parents=True, exist_ok=True)
    entry = {"number": script["number"], "case_id": script["case_id"], "language": language,
             "category": script["category"], "started_at": datetime.now(timezone.utc).isoformat(),
             "code_version_local": code_version(), "base_url": base_url, "paid_encounter": False,
             "staff_documents_only": True, "steps": [], "stopped": None, "documents": {}}
    with sync_playwright() as playwright:
        browser = launch(playwright, headless)
        try:
            staff = Page(browser.new_context(accept_downloads=True).new_page())
            sign_in(staff, base_url, staff_user, staff_password)
            entry["documents"].update(staff_documents(staff, folder, script, resident_user))
        except Exception as stop:
            entry["stopped"] = f"{type(stop).__name__}: {stop}"[:1000]
            try:
                (folder / "stopped-staff.png").write_bytes(staff.page.screenshot(full_page=True))
            except Exception:
                pass
        finally:
            browser.close()
    entry["finished_at"] = datetime.now(timezone.utc).isoformat()
    record(out, entry)
    return entry


def finish_resident_document(script, *, base_url, out, headless=True):
    """Document A of a scenario whose encounter is already completed.

    The resident reopens the newest completed review from the dashboard, where
    the Management Trace analysis is attempted again. No encounter is started,
    so it is recorded as not paid.
    """
    from playwright.sync_api import sync_playwright
    resident_user, resident_password, _, _ = credentials()
    language = script.get("language", "es")
    folder = Path(out) / (f"{script['number']:02d}-{script['case_id']}" + ("-en" if language == "en" else ""))
    folder.mkdir(parents=True, exist_ok=True)
    entry = {"number": script["number"], "case_id": script["case_id"], "language": language,
             "category": script["category"], "started_at": datetime.now(timezone.utc).isoformat(),
             "code_version_local": code_version(), "base_url": base_url, "paid_encounter": False,
             "resident_document_only": True, "steps": [], "stopped": None, "documents": {}}
    with sync_playwright() as playwright:
        browser = launch(playwright, headless)
        try:
            resident = Page(browser.new_context(accept_downloads=True).new_page())
            sign_in(resident, base_url, resident_user, resident_password)
            entry["documents"]["reopened_review"] = reopen_latest_review(resident)
            entry["documents"]["A-management_trace.pdf"] = resident_document(resident, folder, script)
        except Exception as stop:
            entry["stopped"] = f"{type(stop).__name__}: {stop}"[:1000]
            try:
                (folder / "stopped-resident.png").write_bytes(resident.page.screenshot(full_page=True))
            except Exception:
                pass
        finally:
            browser.close()
    entry["finished_at"] = datetime.now(timezone.utc).isoformat()
    record(out, entry)
    return entry
