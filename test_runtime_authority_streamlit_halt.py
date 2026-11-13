"""P3-54: the authority hard failure, driven through the application's own Streamlit wiring.

P3-50 left this as a declared MEDIUM: the real hard fail of P3-47 ran through the production SEQUENCE
(``site.minute`` inside the turn, ``settle_provenance`` after ``order_pipeline.settle``) but not through
``app.py``'s own wiring, and the existing surface tests inject a site built outside the app. Here nothing
is injected: the app opens its own site through ``_runtime_authority_site``, the resident types into the
app's own text area, and the halt happens because of what they typed.
"""
import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_store as store
import runtime_shadow as rs

APP = str(Path(__file__).resolve().parent / "app.py")
CASE = "gi_bleed_57m"
#: The only challenge whose families include ``gi_bleed``, so the app can offer this variant at all.
CHALLENGE = "R2-05"
SNAP = "gi_pressure_committed"
STORE_DIR = tempfile.mkdtemp(prefix="phase3-authority-streamlit-")
#: The repository's own vasopressor script for this family: a management class the common mapping has no
#: writer for, which faculty decision C makes a hard failure. Nothing synthetic.
UNSUPPORTED = "Start norepinephrine at 10 mcg/min."
#: The page's reasoning gate holds any treatment order until these four are answered. P3-54 found that
#: an unsupported order NEVER reaches the authority minute while the gate holds it -- the clock does not
#: move and no authority minute exists -- so the gate has to be passed for the halt to be real.
FOUR_FIELDS = ("What do you think is going on?", "What are you going to do?",
               "What do you expect to happen, or what are you trying to clarify?",
               "What will you check, and when?")
ANSWERS = ("Ongoing haemorrhagic shock despite crystalloid and blood.",
           None,  # the page fills this one from the held order and disables it
           "A higher perfusion pressure while the bleeding source is controlled.",
           "Blood pressure, heart rate and capillary refill in 15 minutes.")


@pytest.fixture(autouse=True)
def _pinned_store(monkeypatch):
    """No authority test may write into an ambient faculty store (P3-28 review, guarded by S23).

    Pinned for EVERY test in this file, not only the ones that open an encounter, so a machine that
    exports ``MRS_PHASE3_AUTHORITY_STORE`` cannot receive a record from the repository's own suite.
    """
    monkeypatch.setenv(store.STORE_FLAG, STORE_DIR)


@pytest.fixture
def app_on_the_authorized_case(monkeypatch):
    """The app, on the allowlisted GI case, with the authorized development authority configuration."""
    for name, value in ((ra.AUTHORITY_FLAG, ra.MODE_LIMITED_COMMON_AUTHORITY),
                        (ra.SNAPSHOT_FLAG, SNAP),
                        (ra.ENVIRONMENT_FLAG, "development"),
                        (rs.FLAG, rs.MODE_SHADOW_COMPARE),
                        (store.STORE_FLAG, STORE_DIR),
                        ("MRS_OFFLINE_CASES", "1"),
                        ("MRS_DEFAULT_CHALLENGE", CHALLENGE),
                        ("MRS_DEFAULT_VARIANT", CASE)):
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=600)
    at.secrets["APP_PASSWORD"] = "test-only-not-a-real-credential"
    at.session_state["_shared_access_granted"] = True
    at.run()
    begin = [button for button in at.button if "Begin" in button.label or "Comenzar" in button.label]
    assert begin, "the app must offer the encounter"
    begin[0].click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    assert str(at.session_state["state"].get("engine_family") or "") == "gi_bleed"
    return at


def _submit(at, text):
    next(r for r in at.radio if r.label == "Encounter").set_value("Treat").run()
    next(a for a in at.text_area
         if a.label == "Enter your clinical reasoning and/or actions").set_value(text)
    next(b for b in at.button if b.label == "Send").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    return at


def _answer_the_reasoning_gate(at):
    """The page's own four fields and its own button: the order runs only once they are answered."""
    assert at.session_state["pending_reasoning"], "the gate must be holding the order"
    for label, answer in zip(FOUR_FIELDS, ANSWERS):
        if answer is None:
            continue
        next(item for item in at.text_area if item.label == label).set_value(answer)
    next(b for b in at.button
         if b.label == "Complete reasoning & execute held order").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    # P3-271 (declared adaptation): the held order is consumed by the turn that runs it. When the authority REFUSES that turn the encounter is untouched by it, so the hold is still there: it may remain
    # only if the authority site halted (any other leftover hold is still a failure of the gate).
    site = at.session_state.get("phase3_authority_site")
    assert not at.session_state["pending_reasoning"] or (site is not None and site.halted), "the gate released the order"
    return at


def _submit_treatment(at, text):
    """One treatment turn as a resident really gives it: the order, then the gate's four answers."""
    _submit(at, text)
    return _answer_the_reasoning_gate(at)


def _site(at):
    return at.session_state.get(ra.SITE_KEY)


def _screen(at):
    return "\n".join(str(item.value) for item in at.markdown)


# -- P3-54-1: the app opens its own site and commits through its own wiring ---------------------------

def test_the_app_opens_its_own_authority_site(app_on_the_authorized_case):
    """``_runtime_authority_site`` is called from the submission path, so the site appears with the
    first turn the resident sends -- nothing is injected into the session."""
    at = app_on_the_authorized_case
    assert _site(at) is None, "no site exists before the resident sends anything"
    _submit(at, "Reassess in 30 minutes.")
    site = _site(at)
    assert site is not None, "the authorized development configuration must open a site in the app"
    assert site.case_id in ra.AUTHORITY_CASES and site.family == ra.AUTHORITY_FAMILY
    assert dict(site.eligibility or {}).get("classification") in ra.ELIGIBLE_CLASSES


def test_the_streamlit_path_commits_and_then_halts_on_the_unsupported_action(app_on_the_authorized_case):
    at = app_on_the_authorized_case
    _submit(at, "Reassess in 30 minutes.")
    site = _site(at)
    committed = list(site.minutes_committed)
    assert committed, "a clean turn commits an authority minute through the app's own wiring"
    before = len(site.records)
    legacy_vitals = dict(at.session_state["state"]["observable"])

    _submit_treatment(at, UNSUPPORTED)
    assert site.halted, "the unsupported action must halt the experiment"
    assert ra.UNSUPPORTED_AUTHORITY_ACTION in str(site.halt_reason or ""), site.halt_reason
    assert list(site.minutes_committed) == committed, "the failing minute commits nothing"
    assert len(site.records) > before, "the failure is recorded, not swallowed"
    failing = [item for item in site.artifact()["minutes"] if item.get("outcome") != ra.COMMITTED]
    assert failing and all(not item.get("committed") for item in failing), failing
    assert site.artifact()["mixed_trajectory"] is True, "a commit before the halt is declared"

    # ADAPTED in P3-253 (FD-STOP-02/03, the effective stop): after a REAL commit followed by an authority failure the experimental session is STOPPED. Before, "the legacy engine ran on"
    # (declared, advisory); now no order box is drawn, nothing re-commits and the legacy engine does NOT run the encounter on. What the test protects (no silent fallback, no commit after the halt) holds.
    import json as _json
    stopped_state = _json.dumps(at.session_state["state"], sort_keys=True, default=str)
    with pytest.raises(StopIteration):
        _submit(at, "Reassess in 15 minutes.")
    assert list(site.minutes_committed) == committed, "no authority commit after the halt"
    assert _json.dumps(at.session_state["state"], sort_keys=True, default=str) == stopped_state, "the legacy engine did not run on: the session is stopped"
    assert ra.authority_status(at.session_state)["experiment_state"] == ra.EXPERIMENT_HALTED


def test_the_resident_screen_says_nothing_of_the_experiment(app_on_the_authorized_case):
    at = app_on_the_authorized_case
    _submit(at, "Reassess in 30 minutes.")
    _submit_treatment(at, UNSUPPORTED)
    assert _site(at).halted
    screen = _screen(at)
    for forbidden in (ra.INVALID_FOR_CONTINUATION, ra.UNSUPPORTED_AUTHORITY_ACTION, SNAP,
                      "authority", "Authority", "experiment_state", "artifact_id"):
        assert forbidden not in screen, forbidden


# -- P3-54-1: the faculty surface shows it ------------------------------------------------------------

def test_the_faculty_surface_shows_the_halt_of_the_streamlit_encounter(app_on_the_authorized_case,
                                                                      monkeypatch):
    at = app_on_the_authorized_case
    _submit(at, "Reassess in 30 minutes.")
    _submit_treatment(at, UNSUPPORTED)
    site = _site(at)
    assert site.halted

    import app

    class _Recorder:
        def __init__(self, session_state):
            self.session_state = session_state
            self.drawn = []

        class _Block:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def expander(self, label, expanded=False):
            self.drawn.append(("expander", label, expanded))
            return self._Block()

        def json(self, payload):
            self.drawn.append(("json", payload))

        def error(self, text):
            self.drawn.append(("error", str(text)))

        def caption(self, text):
            self.drawn.append(("caption", str(text)))

        def __getattr__(self, name):
            raise AssertionError(f"the faculty surface used st.{name}, which this test does not allow")

    recorder = _Recorder({ra.SITE_KEY: site, ra.ARTIFACT_KEY: site.artifact()})
    monkeypatch.setattr(app, "st", recorder)
    app._render_authority_experiment()
    assert [item for item in recorder.drawn if item[0] == "error"], "a halt is an error, not a caption"
    payload = [item[1] for item in recorder.drawn if item[0] == "json"][0]
    assert payload["experiment_state"] == ra.EXPERIMENT_HALTED
    assert payload["mixed_trajectory"] is True
    assert ra.UNSUPPORTED_AUTHORITY_ACTION in str(payload["failure_reason"])
    assert payload["authority_minutes"] == list(site.minutes_committed)


# -- P3-54-2: the artifact of the halted Streamlit encounter persists and replays --------------------

def test_the_halted_streamlit_artifact_persists_and_replays_exactly(app_on_the_authorized_case):
    at = app_on_the_authorized_case
    _submit(at, "Reassess in 30 minutes.")
    _submit_treatment(at, UNSUPPORTED)
    site = _site(at)
    artifact = at.session_state[ra.ARTIFACT_KEY]
    # ADAPTED in P3-248: the authorized case runs on the REAL registered point under the grant, so its artifact carries the real fields too (what only a run under the grant carries)
    assert artifact["halted"] and sorted(artifact) == sorted(ra.ARTIFACT_FIELDS + ra.REAL_ARTIFACT_FIELDS)
    identifier = dict(site.stored).get("artifact_id")
    assert identifier, site.stored
    checked = store.verify(identifier)
    assert checked.get("verified"), checked

    replay = ra.replay_site_artifact(artifact)
    assert replay["eligibility_present"] and replay["eligibility_consistent"], replay["eligibility_reasons"]
    assert replay["verdict"] == "every committed minute reproduces", replay["verdict"]
    committed = [row for row in replay["minutes"] if row["outcome"] == ra.COMMITTED]
    assert committed
    for row in committed:
        assert row["candidate_matches"] and row["transaction_matches"], row["minute"]
        assert row["pressures_match"] and row["written_matches"], row["minute"]
        assert row["provenance_settled"] and row["provenance_consistent"], row["minute"]
        assert row["lineage_valid"] and not row["lineage_violations"], row["minute"]
    # The provenance of the Streamlit path is the canonical one: real order ids, real settled fates.
    for item in artifact["minutes"]:
        for link in item.get("action_lineage") or []:
            row = dict(link)
            assert str(row["order_id"]).strip(), row
            assert row["link"] == ra.LINK_VALID, row
