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
        return path


# --- the three sessions ------------------------------------------------------------

def sign_in(page, base_url, username, password):
    page.page.goto(base_url, wait_until="networkidle")
    page.settle()
    page.fill("Username", username)
    page.fill("Password", password)
    page.click("Sign in")
    try:
        page.wait_for_text("Sign out")
    except RunStop:
        raise RunStop(f"{username} could not sign in.") from None


def direct(page, script, resident):
    """Staff: the resident's next case is this scenario's, and why."""
    page.open("Resident activity and recorded evidence")
    page.open("Direct a resident's next encounter")
    page.select("Challenge", script["challenge"] + " · ")
    page.select("Resident", resident)
    page.select("Case", script["case_id"])
    page.fill("Why this case", f"Tanda sintética 2026-09-24 · escenario {script['number']} · "
                              f"{script['category']}")
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


def resident_document(page, folder, script):
    """Document A: the analysed Management Trace, generated on first view (paid)."""
    page.wait_for_text("Download Management Trace PDF")
    return str(page.download("Download Management Trace PDF", folder,
                             f"{script['number']:02d}-A-management_trace.pdf"))


def open_latest_encounter(page, resident):
    """Staff: select the resident's newest completed encounter in the listing."""
    page.open("Resident activity and recorded evidence")
    box = page._labelled("stSelectbox", "Encounter record")
    if not box.count():
        raise RunStop("The staff listing offers no encounter record.")
    combo = box.first.locator('input[role="combobox"]')
    combo.click()
    options = [text for text in page.page.get_by_role("option").all_inner_texts()
               if text.startswith(resident + " · ") and " · completed · " in text]
    if not options:
        raise RunStop(f"No completed encounter of {resident} is listed.")
    latest = max(options, key=lambda text: text.rsplit(" · ", 1)[-1])
    page.page.get_by_role("option", name=latest, exact=True).first.click()
    page.settle()
    return latest


def staff_documents(page, folder, script, resident):
    """Staff: the AI brief and the AI rubric proposal (paid, once), and documents B-D."""
    chosen = open_latest_encounter(page, resident)
    # Generated once. A "new" button means it already exists: not paid for twice.
    if page.has_button("Generate AI faculty brief"):
        page.click("Generate AI faculty brief")
    page.open("Management reasoning rubric - pilot 1.0")
    if page.has_button("Generate an AI proposal"):
        page.click("Generate an AI proposal")
    saved = {"encounter": chosen}
    for label, name in (("Download 2-page faculty brief (PDF)", "C-brief_compact.pdf"),
                        ("Download full faculty analysis (PDF)", "B-brief_full.pdf"),
                        ("Download rubric assessment (PDF)", "D-rubric.pdf")):
        try:
            saved[name] = str(page.download(label, folder, f"{script['number']:02d}-{name}"))
        except RunStop as missing:
            saved[name] = f"missing: {missing}"
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
    resident_user = os.environ.get("MRS_BATCH_RESIDENT_USER", "residente_prueba_r3")
    resident_password = os.environ.get("MRS_BATCH_RESIDENT_PASSWORD", "")
    staff_user = os.environ.get("MRS_BATCH_STAFF_USER", "")
    staff_password = os.environ.get("MRS_BATCH_STAFF_PASSWORD", "")
    if not (resident_password and staff_user and staff_password):
        raise SystemExit("MRS_BATCH_RESIDENT_PASSWORD, MRS_BATCH_STAFF_USER and "
                         "MRS_BATCH_STAFF_PASSWORD are required, as environment variables.")
    if with_ai and spent(out) >= AUTHORISED_PAID_ENCOUNTERS:
        raise SystemExit(f"{AUTHORISED_PAID_ENCOUNTERS} paid encounters are already on the ledger. "
                         "No new paid encounter is started.")
    folder = Path(out) / f"{script['number']:02d}-{script['case_id']}"
    folder.mkdir(parents=True, exist_ok=True)
    entry = {"number": script["number"], "case_id": script["case_id"],
             "category": script["category"], "started_at": datetime.now(timezone.utc).isoformat(),
             "code_version_local": code_version(), "base_url": base_url,
             "paid_encounter": bool(with_ai), "steps": [], "stopped": None, "documents": {}}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=BROWSER, headless=headless)
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
                entry["documents"]["A-management_trace.pdf"] = resident_document(resident, folder, script)
                staff.page.reload()
                staff.settle()
                entry["documents"].update(staff_documents(staff, folder, script, resident_user))
        except Exception as stop:  # a finding about the page, or the tool's own failure
            entry["stopped"] = f"{type(stop).__name__}: {stop}"[:1000]
            try:
                (folder / "stopped.png").write_bytes(
                    (resident if "resident" in locals() else staff).page.screenshot(full_page=True))
            except Exception:
                pass
        finally:
            browser.close()
    entry["finished_at"] = datetime.now(timezone.utc).isoformat()
    record(out, entry)
    return entry
