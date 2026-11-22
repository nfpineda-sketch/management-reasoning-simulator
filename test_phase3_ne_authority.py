"""P3-489 to P3-499: the LIVE manual NOREPINEPHRINE control under the development authority (``GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1``, FD-AUTHNE-01 to FD-AUTHNE-12).

TEST-SIDE, headless: a REAL GI encounter and a REAL authority site (the real registered pressure and tone snapshots and the real grant), driven the way the page drives it (an order turn and clinical time), with
the stores in a temporary directory. What is defended, in order:

* A  the grant (data only, pinned, never edited; the earlier grants are what they were);
* B  the tone binding (read from the ratified record, never recomputed; LOW and HIGH are never read);
* C  the selector and the gate (nothing opens unless the tone AND the ratified pressure snapshot are named; nothing falls back);
* D  the authority's own order contract (independent of the shadow mapping, and compared with it);
* E  the live pressure equals the certified trajectories (FR-F, TIT-1..TIT-5) minute by minute;
* F  the fail-closed matrix (a malformed or unsupported order stops the session for good);
* G  the artifact and its replay (a renamed or mislabelled artifact fails; the older artifacts verify as before);
* H  non-regression (without norepinephrine nothing moves), the effective stop, isolation (what the resident sees and what is scored does not change) and the families that are not granted.
"""
import copy
import json
import os
import tempfile
from copy import deepcopy
from types import SimpleNamespace

import pytest

import faculty_titration_review as titration
import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_authority_session as se
import runtime_authority_store as store
import runtime_ne_authority as ne
import runtime_ne_grant as ng
import runtime_pressure_grant as pg
import runtime_pressure_snapshot as ps
import runtime_shadow as rs
import runtime_tone_snapshot as tn
import runtime_tone_support as ts

pytestmark = pytest.mark.ordinary_configuration

STORE_DIR = tempfile.mkdtemp(prefix="phase3-ne-authority-")
BASE = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE, store.STORE_FLAG: STORE_DIR}
V3_ENV = {**BASE, ra.SNAPSHOT_FLAG: ps.SNAPSHOT_ID}
NE_ENV = {**V3_ENV, ra.TONE_FLAG: tn.SNAPSHOT_ID}
CASE = "gi_bleed_57m"
START5 = "Start norepinephrine at 5 mcg/min."
START10 = "Start norepinephrine at 10 mcg/min."
STOP = "Stop norepinephrine."


@pytest.fixture(autouse=True)
def _environment(monkeypatch):
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)
    for name, value in NE_ENV.items():
        monkeypatch.setenv(name, value)
    yield


class Driver:
    """A real GI encounter and a REAL authority site, imitating the page: an order turn reaches the site only when something ran (the page does not call the hook for a question it asks), and clinical time
    outside an order turn reaches it on its own route."""

    def __init__(self, case=CASE, env=NE_ENV):
        import pilot_acceptance
        self.env = {**dict(env), store.STORE_FLAG: tempfile.mkdtemp(prefix="phase3-ne-driver-")}      # one store per driver: two runs of one case are two experiments of one identity
        self._sync_environment()
        self.enc = pilot_acceptance.Encounter(case)
        self.arrival = deepcopy(self.enc.state)
        self.site = ra.open_site(self.arrival, environ=self.env)

    def _sync_environment(self):
        """The shadow session reads the process environment, the site reads the environment it was opened with: they must say the same thing (a run under the earlier grant names no tone snapshot)."""
        for name in (ra.TONE_FLAG, ra.SNAPSHOT_FLAG):
            if name in self.env:
                os.environ[name] = self.env[name]
            else:
                os.environ.pop(name, None)

    @property
    def state(self):
        return self.enc.state

    def order(self, text):
        self._sync_environment()
        import order_ledger
        import order_pipeline
        import time_semantics
        from family_parser import parse_family_actions
        enc = self.enc
        submission = f"t{enc._turns}"
        enc._turns += 1
        minute = int(enc.state.get("sim_time", 0) or 0)
        parsed = time_semantics.apply(text, parse_family_actions(text))
        parsed.setdefault("raw_text", text)
        turn = order_pipeline.open_turn(text, parsed, submission_id=submission, entry_point="free_text", minute=minute, ledger=enc.ledger)
        before = enc.shadow.capture(enc.state)
        result, split, run = enc._execute(parsed, text)
        enc.shadow.observe(before, enc.state, parsed, result, run, submission)
        prepared = None
        if self.site is not None and result.get("executed"):
            prepared = self.site.minute(before, enc.state, enc.shadow, run, submission)
            if prepared is not None:
                enc.state = prepared
        order_pipeline.settle(turn, result=result, run_actions=run, split=split, minute_before=minute, minute_after=int(enc.state.get("sim_time", 0) or 0), terminal=bool(result.get("terminal_locked")))
        orders = order_ledger.snapshot(turn["orders"])
        order_pipeline.upsert(enc.ledger, turn["orders"])
        if self.site is not None and result.get("executed"):
            self.site.settle_provenance(submission, orders)
        return prepared

    def ask(self, minutes=1):
        self._sync_environment()
        from family_engine import advance_clinical_time
        enc = self.enc
        before = enc.shadow.capture(enc.state)
        result = advance_clinical_time(enc.state, minutes, label="question")
        enc.shadow.observe_time(before, enc.state, result)
        prepared = self.site.minute(before, enc.state, enc.shadow, None, None, ra.CLINICAL_TIME)
        if prepared is not None:
            enc.state = prepared
        return prepared

    def committed(self):
        return {r["minute"]: r["written_candidate"] for r in self.site.records if r.get("committed")}

    def run_plan(self, plan, until=32):
        """``plan``: ``{minute: order text}``. One clinical minute at a time, so that every minute is committed and can be compared."""
        clock = int(self.state["sim_time"])
        while clock < until and not self.site.halted:
            if clock in plan:
                self.order(plan[clock])
            else:
                self.ask(1)
            clock = int(self.state["sim_time"])
        return self


def _order_text(op, rate):
    if op in ("START", "RESTART"):
        return f"{'Start' if op == 'START' else 'Restart'} norepinephrine at {rate:g} mcg/min."
    if op == "INCREASE":
        return f"Increase norepinephrine to {rate:g} mcg/min."
    if op == "DECREASE":
        return f"Decrease norepinephrine to {rate:g} mcg/min."
    return STOP


def _plan(scenario):
    return {minute: _order_text(op, rate) for minute, op, rate in titration.RATE_PLAN[scenario]}


# ============================================================================================================================================
# A. the grant
# ============================================================================================================================================

def test_a1_the_grant_is_registered_pinned_and_valid():
    assert ng.GRANT_ID == "GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1" and ng.GRANT_VERSION == 1
    assert ng.GRANT["fingerprint"] == ng.GRANT_FINGERPRINT == "d79637c47343b82f0fbb4cb54cc89f5c3027d596d1e4fe086642e50580a45fb7" == ng.fingerprint_of(ng.GRANT)
    assert ng.grant_problems(ng.GRANT) == [] and ng.registered_grant(ng.GRANT_ID, ng.GRANT_FINGERPRINT) is ng.GRANT and ng.registered_grant(ng.GRANT_ID, "0" * 64) is None
    with pytest.raises(TypeError):
        ng.GRANT["status"] = "REVOKED"
    assert ng.lineage_of(ng.GRANT) == {"version_id": "PHASE2_AMENDMENT_3", "digest": "867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c"}


def test_a2_the_earlier_grants_are_what_they_were_and_the_new_one_replaces_none_of_them():
    assert pg.GRANT["fingerprint"] == "3c29c2b9eb070ea1728bea2b17fd4484ff42c5105070c9402b17e73b29c3c136"
    assert pg.GRANT_V2["fingerprint"] == "8a91145dbfe899dffdc5de1ed28b116c61f4fa5b462a49979727ce8b05b3642f"
    assert pg.GRANT_V3["fingerprint"] == pg.GRANT_FINGERPRINT_V3 == pg.fingerprint_of(pg.GRANT_V3)
    assert [item["grant_id"] for item in pg.REGISTERED_GRANTS] == [pg.GRANT_ID, pg.GRANT_ID_V2, pg.GRANT_ID_V3] and pg.LIVE_GRANT_ID == pg.GRANT_ID_V3
    assert "norepinephrine" in pg.GRANT_V3["not_granted"], "version 3 still says norepinephrine is not granted: it is the grant of every run that names no tone snapshot"
    assert ng.GRANT["extends"]["mutates_the_earlier_grant"] is False and ng.GRANT["extends"]["supersedes_the_earlier_grant"] is False and ng.GRANT["extends"]["grant_id"] == pg.GRANT_ID_V3
    assert ng.GRANT_ID not in {item["grant_id"] for item in pg.REGISTERED_GRANTS} and pg.registered_grant(ng.GRANT_ID) is None


def test_a3_the_grant_binds_every_dimension_by_literals_typed_again():
    body = ng.GRANT
    assert (body["pressure_snapshot"]["id"], body["pressure_snapshot"]["configuration_digest"], body["pressure_snapshot"]["value_digest"]) == (
        "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1", ps.CONFIGURATION_DIGEST, pg.PRESSURE_VALUE_DIGEST_V2)
    assert (body["tone_snapshot"]["id"], body["tone_snapshot"]["configuration_digest"], body["tone_snapshot"]["values_digest"], body["tone_snapshot"]["record_digest"],
            body["tone_snapshot"]["record_file_sha256"], body["tone_snapshot"]["ratification_digest"], body["tone_snapshot"]["human_record_digest"]) == (
        tn.SNAPSHOT_ID, tn.CONFIGURATION_DIGEST, tn.VALUES_DIGEST, tn.RECORD_DIGEST, tn.RECORD_FILE_SHA256, tn.RATIFICATION_DIGEST, tn.HUMAN_RECORD_DIGEST)
    assert body["tone_snapshot"]["selector_flag"] == ra.TONE_FLAG == "MRS_PHASE3_AUTHORITY_TONE_SNAPSHOT" and body["tone_snapshot"]["profile_field"] == ts.PROFILE_FIELD
    assert (body["writer"]["version"], tuple(body["writer"]["types"])) == (ts.WRITER_VERSION, ("norepinephrine", "norepinephrine_rate_history")) and body["writer"]["constants_changed"] is False
    assert (body["domain"], body["cases"], body["environments"], body["window"]["max_minute"], body["family"]) == (("sbp", "dbp", "map"), ("gi_bleed_57m", "gi_bleed_72f"), ("development",), 240, "gi_bleed")
    assert tuple(body["excluded_domains"]) == pg.EXCLUDED_DOMAINS and body["authority_mode"] == "PRESSURE_ONLY"
    contract = body["order_contract"]
    assert tuple(contract["supported_semantics"]) == ("START", "INCREASE", "DECREASE", "STOP", "RESTART") and contract["units"] == "mcg/min" and contract["a_stop_needs_no_rate"] is True
    assert {"mcg/kg/min", "target-based titration", "relative dose arithmetic", "a rate without a unit", "a restart without an explicit rate", "automatic control", "another vasopressor"} <= set(contract["unsupported_and_failed_closed"])
    assert {"pump-limited families", "pulmonary edema authority", "consciousness authority", "terminal semantics", "a weight-based dose", "any other vasopressor", "resident deployment", "scoring",
            "a resident-visible tone variable", "clinical validation"} <= set(body["not_granted"])
    import reader_succession as succession
    assert (body["order_contract"]["reader_successor"]["git_blob"], body["order_contract"]["reader_successor"]["sha256"]) == (succession.SUCCESSOR_GIT_BLOB, succession.SUCCESSOR_SHA256)
    assert ne.reader_problems() == [], "the live reader is the order-safety successor the grant pins"


@pytest.mark.parametrize("path, value", [
    (("status",), "REVOKED"), (("authority_mode",), "ALL_DOMAINS"), (("domain",), ("sbp", "dbp", "map", "pulse")), (("cases",), ("gi_bleed_57m", "pe_70m")), (("environments",), ("development", "production")),
    (("window", "max_minute"), 1000), (("pressure_snapshot", "configuration_digest"), "0" * 64), (("tone_snapshot", "configuration_digest"), "0" * 64), (("tone_snapshot", "witness"), "HIGH"),
    (("core_lineage", "digest"), "0" * 64), (("writer", "version"), "norepinephrine_rate_history/P3-999"), (("writer", "constants_changed"), True),
    (("order_contract", "units"), "mcg/kg/min"), (("order_contract", "reader_successor", "git_blob"), "0" * 40), (("order_contract", "a_stop_needs_no_rate"), False),
    (("failure_policy", "a_norepinephrine_order_the_contract_does_not_read"), "RECOVER"), (("failure_policy", "silent_fallback_to_the_legacy_engine"), True),
    (("consciousness_overlay", "authority"), True), (("consciousness_overlay", "resident_visible"), True), (("collapse_boundary", "fails_closed"), False),
    (("extends", "mutates_the_earlier_grant"), True), (("kind",), "FACULTY_GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT")])
def test_a4_a_grant_that_drifted_in_any_dimension_is_refused(path, value):
    body = ng._plain(ng.GRANT)
    node = body
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    found = ng.grant_problems(body)
    assert found, f"editing {path} was not caught"
    assert ng.FINGERPRINT_MISMATCH in found or ng.FINGERPRINT_NOT_PINNED in found


def test_a5_a_claim_no_faculty_decision_made_is_refused_and_a_dimension_the_run_does_not_name_is_a_refusal():
    body = ng._plain(ng.GRANT)
    body["purpose_note"] = "CLINICALLY_VALIDATED"
    assert ng.FORBIDDEN_CLAIM in ng.grant_problems(body)
    full = dict(case_id=CASE, environment="development", snapshot_id=ng.PRESSURE_SNAPSHOT_ID, tone_snapshot_id=ng.TONE_SNAPSHOT_ID, family="gi_bleed", domain=ng.DOMAIN, lineage=ng.lineage_of(ng.GRANT))
    assert ng.permits(**full) == (True, [])
    for name in ("case_id", "environment", "snapshot_id", "tone_snapshot_id", "family", "lineage"):
        ok, why = ng.permits(**{**full, name: None})
        assert not ok and name in why[0]
    assert not ng.permits(**{**full, "domain": ("sbp", "dbp", "map", "hr")})[0] and not ng.permits(**{**full, "case_id": "asthma_30m"})[0]
    assert not ng.permits(**{**full, "snapshot_id": pg.PRESSURE_SNAPSHOT_ID})[0], "the older pressure point is not a snapshot this grant runs on"
    assert not ng.permits(**{**full, "environment": "production"})[0] and not ng.permits(**{**full, "tone_snapshot_id": "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V2"})[0]


# ============================================================================================================================================
# B. the tone binding
# ============================================================================================================================================

def test_b1_the_tone_snapshot_binds_to_the_ratified_record_and_is_the_cores_center_reference():
    cfg = tn.bind()
    assert tn.configuration_is_pinned(cfg) and cfg.configuration_digest == tn.CONFIGURATION_DIGEST == ng.TONE_CONFIGURATION_DIGEST
    assert cfg.values() == {"tone_gain": 0.6, "half_effect_rate_mcg_min": 10.0, "onset_tau_min": 1.5, "offset_tau_min": 2.5}
    from clinical_core import vascular_support as vs
    assert {name: vs.witness("CENTER_REFERENCE")[name] for name in tn.BINDING} == dict(tn.BINDING)
    record = json.load(open(os.path.join(tn.ROOT, tn.RECORD_FILE)))
    assert record["binding"] == dict(tn.BINDING) and record["witnesses_test_only"]["LOW"] == record["witnesses_test_only"]["HIGH"] == "TEST_WITNESS_ONLY"
    assert record["live_configuration"]["bound"] is False, "the sealed record is never rewritten: that it is bound now is said by the grant and the checkpoint, not by an edit of the record"


def test_b2_low_and_high_are_never_read(monkeypatch):
    from clinical_core import vascular_support as vs
    asked = []
    real = vs.witness
    monkeypatch.setattr(vs, "witness", lambda name: (asked.append(name), real(name))[1])
    tn.bind()
    d = Driver()
    d.run_plan(_plan("TIT-1"), until=14)
    assert set(asked) <= {"CENTER_REFERENCE"}, asked


@pytest.mark.parametrize("name, mutate, code", [
    ("gain", lambda r: r["binding"].__setitem__("tone_gain", 0.61), tn.MODIFIED_PARAMETER),
    ("half_effect", lambda r: r["binding"].__setitem__("half_effect_rate_mcg_min", 11.0), tn.MODIFIED_PARAMETER),
    ("onset", lambda r: r["binding"].__setitem__("onset_tau_min", 1.4), tn.MODIFIED_PARAMETER),
    ("offset", lambda r: r["binding"].__setitem__("offset_tau_min", 2.6), tn.MODIFIED_PARAMETER),
    ("low_as_number", lambda r: r["witnesses_test_only"].__setitem__("LOW", {"tone_gain": 0.3}), tn.WITNESS_SUBSTITUTED),
    ("high_as_number", lambda r: r["witnesses_test_only"].__setitem__("HIGH", {"tone_gain": 0.9}), tn.WITNESS_SUBSTITUTED),
    ("status", lambda r: r.__setitem__("status", "DRAFT"), tn.WRONG_STATUS),
    ("id", lambda r: r.__setitem__("snapshot_id", "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V2"), tn.WRONG_SNAPSHOT_ID),
    ("witness", lambda r: r.__setitem__("selected_witness", "HIGH"), tn.WRONG_SNAPSHOT_ID),
    ("core", lambda r: r["binding_source"].__setitem__("core_digest", "0" * 64), tn.CORE_MISMATCH),
    ("recomputed", lambda r: r["binding_source"].__setitem__("copied_not_recomputed", False), tn.MODIFIED_PARAMETER),
    ("optimized", lambda r: r["binding_source"].__setitem__("optimized", True), tn.MODIFIED_PARAMETER),
    ("profile_field", lambda r: r.__setitem__("profile_field", "something_else"), tn.MODIFIED_PARAMETER),
    ("human", lambda r: r["reviewed_with"]["human_record"].__setitem__("record_digest", "0" * 64), tn.HUMAN_RECORD_MISMATCH),
    ("extra_binding_key", lambda r: r["binding"].__setitem__("pump_coupling", 0.5), tn.NOT_A_RECORD),
    ("record_digest", lambda r: r.__setitem__("record_digest", "0" * 64), tn.WRONG_DIGEST),
])
def test_b3_a_record_that_differs_from_the_ratified_one_in_anything_is_refused_by_its_own_code(name, mutate, code):
    record = json.load(open(os.path.join(tn.ROOT, tn.RECORD_FILE)))
    mutate(record)
    with pytest.raises(tn.ToneBindingError) as refusal:
        tn.bind(record=record)
    assert code in refusal.value.reasons, (name, refusal.value.reasons)
    assert code in tn.verify_record(record), "the verification names it, not only the digest"


def test_b3b_the_bytes_offered_must_be_the_bytes_of_the_record_offered_and_the_ratification_must_be_the_pinned_one():
    path = os.path.join(tn.ROOT, tn.RECORD_FILE)
    raw = open(path, "rb").read()
    record = json.loads(raw.decode("utf-8"))
    assert tn.bind(record=record, raw=raw).configuration_digest == tn.CONFIGURATION_DIGEST
    with pytest.raises(tn.ToneBindingError) as refusal:
        tn.bind(record=record, raw=raw + b" ")
    assert tn.WRONG_DIGEST in refusal.value.reasons
    ratification = json.load(open(os.path.join(tn.ROOT, tn.RATIFICATION_FILE)))
    ratification["status"] = "DRAFT"
    with pytest.raises(tn.ToneBindingError) as refusal2:
        tn.bind(ratification=ratification)
    assert tn.NOT_RATIFIED in refusal2.value.reasons


def test_b6_the_binding_must_equal_the_cores_own_center_reference_and_nothing_else_is_asked(monkeypatch):
    from clinical_core import vascular_support as vs
    real = vs.witness
    monkeypatch.setattr(vs, "witness", lambda name: {**real(name), "tone_gain": 0.61})
    with pytest.raises(tn.ToneBindingError) as refusal:
        tn.bind()
    assert tn.NOT_THE_CORE_WITNESS in refusal.value.reasons


def test_b4_the_selector_is_exact_and_an_unknown_id_is_a_refusal_never_a_default():
    assert tn.configuration_for({}) is None and not tn.named({}) and tn.configuration_for({tn.TONE_SNAPSHOT_FLAG: "  "}) is None
    assert tn.configuration_for({tn.TONE_SNAPSHOT_FLAG: f" {tn.SNAPSHOT_ID} "}).configuration_digest == tn.CONFIGURATION_DIGEST
    for other in ("COMMON_TONE_DEVELOPMENT_SNAPSHOT_V2", "common_tone_development_snapshot_v1", "CENTER_REFERENCE", "LOW", "HIGH", "1"):
        with pytest.raises(tn.ToneBindingError) as refusal:
            tn.configuration_for({tn.TONE_SNAPSHOT_FLAG: other})
        assert refusal.value.reasons == (tn.UNKNOWN_TONE_SNAPSHOT,)


def test_b5_a_configuration_built_by_hand_or_edited_afterwards_is_not_trusted():
    import dataclasses
    cfg = tn.bind()
    assert not tn.configuration_is_pinned(dataclasses.replace(cfg, tone_gain=0.7)) and not tn.configuration_is_pinned(SimpleNamespace(**dataclasses.asdict(cfg))) and not tn.configuration_is_pinned(None)
    forged = copy.copy(cfg)
    object.__setattr__(forged, "half_effect_rate_mcg_min", 12.0)
    assert not tn.configuration_is_pinned(forged)
    with pytest.raises(tn.ToneBindingError):
        tn.apply_profile(object(), forged)
    with pytest.raises(tn.ToneBindingError):
        ne.bound_adapter(ps.bind(), forged)


# ============================================================================================================================================
# C. the selector and the gate
# ============================================================================================================================================

def test_c1_the_ratified_pressure_and_tone_snapshots_open_a_site_under_the_norepinephrine_grant():
    d = Driver()
    assert d.site is not None and d.site.grant["grant_id"] == ng.GRANT_ID and d.site.grant["fingerprint"] == ng.GRANT_FINGERPRINT
    assert d.site.tone_configuration == tn.bind() and d.site._carried() == ("norepinephrine",) and d.site.snapshot_id == ps.SNAPSHOT_ID
    gate = ra.gate(deepcopy(d.arrival), environ=NE_ENV, unsupported=())
    assert gate.granted and gate.conditions["explicit_development_grant"] and len(gate.conditions) == 10


def test_c2_without_the_tone_selector_the_earlier_grant_runs_and_norepinephrine_still_halts_it():
    d = Driver(env=V3_ENV)
    assert d.site is not None and d.site.grant["grant_id"] == pg.GRANT_ID_V3 and d.site.tone_configuration is None and d.site._carried() == ()
    d.ask(2)
    d.order(START10)
    assert d.site.halted and d.site.halt_reason.startswith("UNSUPPORTED_AUTHORITY_ACTION") and "norepinephrine" in d.site.halt_reason


@pytest.mark.parametrize("name, env", [
    ("older_pressure_point", {**NE_ENV, ra.SNAPSHOT_FLAG: "gi_pressure_committed"}),
    ("v2_historical_name", {**NE_ENV, ra.SNAPSHOT_FLAG: "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1", "MRS_PHASE3_HISTORICAL_RECONSTRUCTION": pg.GRANT_ID_V2}),
    ("unknown_tone_id", {**NE_ENV, ra.TONE_FLAG: "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V2"}),
    ("a_witness_name", {**NE_ENV, ra.TONE_FLAG: "CENTER_REFERENCE"}),
    ("production", {**NE_ENV, ra.ENVIRONMENT_FLAG: "production"}),
    ("no_authority_flag", {key: value for key, value in NE_ENV.items() if key != ra.AUTHORITY_FLAG}),
    ("no_store", {key: value for key, value in NE_ENV.items() if key != store.STORE_FLAG}),
    ("no_shadow", {key: value for key, value in NE_ENV.items() if key != rs.FLAG}),
])
def test_c3_every_configuration_the_grant_does_not_authorize_opens_nothing(name, env):
    import pilot_acceptance
    arrival = deepcopy(pilot_acceptance.Encounter(CASE).state)
    assert ra.open_site(arrival, environ=env) is None, name
    assert ra.open_site(arrival, environ={**NE_ENV, store.STORE_FLAG: tempfile.mkdtemp()}) is not None, "and the same arrival does open under the full configuration"


def test_c4_a_tone_selector_named_in_a_secret_is_not_honoured(monkeypatch):
    monkeypatch.setattr(rs, "_named_in_secrets", lambda name: name == ra.TONE_FLAG)
    gate = ra.gate(deepcopy(Driver(env=V3_ENV).arrival), environ=NE_ENV, unsupported=())
    assert not gate.granted and not gate.conditions["authority_flag"] and any("Streamlit secrets" in reason for reason in gate.reasons)


def test_c5_the_live_reader_must_be_the_order_safety_successor_or_the_grant_opens_nothing(monkeypatch):
    monkeypatch.setattr(ng, "READER_GIT_BLOB", "0" * 40)
    ok, why = ra._norepinephrine_permission(NE_ENV, case_id=CASE, snapshot_id=ps.SNAPSHOT_ID, family="gi_bleed", domain=ng.DOMAIN, lineage=ng.lineage_of(ng.GRANT), reconstruction=None)
    assert not ok and any("reader" in reason.lower() for reason in why)


def test_c6_only_the_two_gi_cases_and_only_gi_open_a_site():
    assert Driver("gi_bleed_72f").site is not None
    for case in ("pe_70m", "acs_70f_left_main"):
        try:
            assert Driver(case).site is None, case
        except KeyError:
            pytest.skip(f"no such case {case}")


# ============================================================================================================================================
# D. the authority's own order contract
# ============================================================================================================================================

def _event(order_id, minute, operation, rate=None, units=None, *, kind="norepinephrine", receipt=None, type_=None):
    action = {"type": type_ or kind, "rate": rate, "units": units, "operation": operation}
    return SimpleNamespace(order_id=order_id, minute=minute, kind=kind, action=action, receipt=receipt or {}, ledger_order_id=order_id, submission_id="s")


@pytest.mark.parametrize("action, expected", [
    (dict(type="norepinephrine", operation="start", rate=10.0, units="mcg/min"), ("start", 10.0, None)),
    (dict(type="norepinephrine", operation="adjust", rate=15.0, units="mcg/min"), ("adjust", 15.0, None)),
    (dict(type="norepinephrine", operation="continue", rate=12.0, units="mcg/min"), ("continue", 12.0, None)),
    (dict(type="norepinephrine", operation="stop", rate=None, units=None), ("stop", 0.0, None)),
    (dict(type="norepinephrine", operation="continue", rate=None, units=None), ("continue", None, ne.BARE_CONTINUATION)),
    (dict(type="norepinephrine", operation="start", rate=0.1, units="mcg/kg/min"), ("start", None, ne.WRONG_UNITS)),
    (dict(type="norepinephrine", operation="start", rate=10.0, units="mg/h"), ("start", None, ne.WRONG_UNITS)),
    (dict(type="norepinephrine", operation="start", rate=10.0, units=None), ("start", None, ne.NO_UNITS)),
    (dict(type="norepinephrine", operation="adjust", rate=None, units=None), ("adjust", None, ne.NO_UNITS)),
    (dict(type="norepinephrine", operation="start", rate=None, units="mcg/min"), ("start", None, ne.BAD_RATE)),
    (dict(type="norepinephrine", operation="start", rate=0.0, units="mcg/min"), ("start", None, ne.BAD_RATE)),
    (dict(type="norepinephrine", operation="start", rate=-3.0, units="mcg/min"), ("start", None, ne.BAD_RATE)),
    (dict(type="norepinephrine", operation="start", rate=float("nan"), units="mcg/min"), ("start", None, ne.BAD_RATE)),
    (dict(type="norepinephrine", operation="start", rate=float("inf"), units="mcg/min"), ("start", None, ne.BAD_RATE)),
    (dict(type="norepinephrine", operation="start", rate=True, units="mcg/min"), ("start", None, ne.BAD_RATE)),
    (dict(type="norepinephrine", operation="start", rate="10", units="mcg/min"), ("start", None, ne.BAD_RATE)),
    (dict(type="norepinephrine", operation="stop", rate=5.0, units="mcg/min"), ("stop", None, ne.STOP_WITH_RATE)),
    (dict(type="norepinephrine", operation="titrate", rate=5.0, units="mcg/min"), (None, None, ne.UNKNOWN_OPERATION)),
    (dict(type="norepinephrine", operation=None, rate=5.0, units="mcg/min"), (None, None, ne.UNKNOWN_OPERATION)),
    (dict(type="dobutamine", operation="start", rate=5.0, units="mcg/min"), (None, None, ne.NOT_NE_TYPE)),
    (dict(type="infusion_adjustment", operation="stop"), (None, None, ne.NOT_NE_TYPE)),
    (dict(type="norepinephrine", operation="start", rate=10.0, units="mcg/min", rate_mcg_min=12.0), ("start", None, ne.TWO_RATES)),
])
def test_d1_the_authority_reads_one_raw_order_as_the_contract_says(action, expected):
    assert ne.read_order(action) == expected


def test_d2_a_receipt_that_disagrees_with_the_order_is_a_refusal():
    action = dict(type="norepinephrine", operation="start", rate=10.0, units="mcg/min")
    assert ne.read_order(action, {"operation": "start", "rate": 10.0, "units": "mcg/min"}) == ("start", 10.0, None)
    for receipt in ({"operation": "stop"}, {"rate": 12.0}, {"units": "mcg/kg/min"}):
        assert ne.read_order(action, receipt)[2] == ne.RECEIPT_DISAGREES


def test_d3_the_whole_history_is_read_and_compared_with_the_shadow_mapping():
    cfg = tn.bind()
    seq = [_event("a", 2, "start", 5.0, "mcg/min"), _event("b", 10, "adjust", 10.0, "mcg/min"), _event("c", 18, "adjust", 4.0, "mcg/min"), _event("d", 25, "stop")]
    verdict = ne.check(seq, cfg)
    assert verdict.ok and verdict.problems == () and verdict.history == ((2, 5.0), (10, 10.0), (18, 4.0), (25, 0.0))
    assert [row["semantic"] for row in verdict.orders] == ["START", "INCREASE", "DECREASE", "STOP"]
    shadow = ts.infusion_history(ts._ours(seq)[0], cfg.values())[0]
    assert tuple(shadow) == verdict.history, "the two readings agree, and they are two implementations"
    restart = ne.check(seq + [_event("e", 30, "start", 10.0, "mcg/min")], cfg)
    assert restart.ok and restart.orders[-1]["semantic"] == "RESTART"
    assert ne.check([], cfg).ok and ne.check([], cfg).history == ()


@pytest.mark.parametrize("name, seq, problem", [
    ("kg", [_event("a", 2, "start", 0.1, "mcg/kg/min")], ne.WRONG_UNITS),
    ("no_unit", [_event("a", 2, "start", 10.0, None)], ne.NO_UNITS),
    ("before_start", [_event("a", 2, "adjust", 10.0, "mcg/min")], ne.NOT_STARTED),
    ("stop_first", [_event("a", 2, "stop")], ne.NOT_STARTED),
    ("bare_continue", [_event("a", 2, "start", 5.0, "mcg/min"), _event("b", 4, "continue")], ne.BARE_CONTINUATION),
    ("role_named", [_event("a", 2, "start", 5.0, "mcg/min"), _event("b", 4, "stop", kind="infusion_adjustment", type_="infusion_adjustment")], ne.ROLE_NAMED),
    ("no_identity", [_event("", 2, "start", 5.0, "mcg/min")], ne.NO_IDENTITY),
    ("no_whole_minute", [_event("a", 2.5, "start", 5.0, "mcg/min")], ne.NO_IDENTITY),
    ("against_the_clock", [_event("a", 5, "start", 5.0, "mcg/min"), _event("b", 3, "adjust", 6.0, "mcg/min")], ne.CHRONOLOGY),
    ("a_rate_beyond_the_writer", [_event("a", 2, "start", 1.0e6, "mcg/min")], ne.RATE_BEYOND_THE_WRITER),
])
def test_d4_every_order_the_contract_does_not_read_is_a_named_problem(name, seq, problem):
    verdict = ne.check(seq, tn.bind())
    assert not verdict.ok and problem in {item["problem"] for item in verdict.problems}, (name, verdict.problems)


def test_d5_if_the_shadow_mapping_and_the_authority_read_the_infusion_differently_that_is_a_problem(monkeypatch):
    cfg = tn.bind()
    seq = [_event("a", 2, "start", 5.0, "mcg/min"), _event("b", 10, "adjust", 10.0, "mcg/min")]
    assert ne.check(seq, cfg).ok
    real = ts.infusion_history

    def shifted(events, witness):
        physical, carried, declared = real(events, witness)
        return tuple((minute + 1, rate) for minute, rate in physical), carried, declared
    monkeypatch.setattr(ts, "infusion_history", shifted)
    verdict = ne.check(seq, cfg)
    assert not verdict.ok and ne.READINGS_DISAGREE in {item["problem"] for item in verdict.problems}


def test_d6_a_gap_the_contract_does_not_account_for_stays_a_problem_for_good():
    cfg = tn.bind()
    seq = [_event("a", 2, "start", 5.0, "mcg/min")]
    verdict = ne.check(seq, cfg, gaps=[{"order_id": "zz", "kind": "norepinephrine", "why": "no core intervention for this order type yet"}])
    assert not verdict.ok and ne.UNEXPLAINED_GAP in {item["problem"] for item in verdict.problems}
    assert ne.check(seq, cfg, gaps=[{"order_id": "a", "kind": "dobutamine", "why": "x"}]).ok, "another kind of gap is the site's own business"
    same_minute = [_event("a", 2, "start", 5.0, "mcg/min"), _event("b", 2, "adjust", 8.0, "mcg/min")]
    declared = ts.infusion_history(ts._ours(same_minute)[0], cfg.values())[2]
    assert [what for _order, _kind, what, _why in declared] == [ts.REPLACED], "an order a later order of its own minute replaced is benign"
    gaps = [{"order_id": order, "kind": kind, "why": why} for order, kind, _what, why in declared]
    assert ne.check(same_minute, cfg, gaps=gaps).ok and ne.check(same_minute, cfg, gaps=gaps).benign == ("a",)


# ============================================================================================================================================
# E. the live pressure equals the certified trajectories
# ============================================================================================================================================

@pytest.fixture(scope="module")
def tit_items():
    data = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "revision", "PHASE3_NOREPINEPHRINE_TITRATION_V1_REVIEW_SET.json")))
    return {item["scenario_id"]: item for item in data["items"]}


@pytest.mark.parametrize("scenario", ["TIT-1", "TIT-2", "TIT-3", "TIT-4", "TIT-5"])
def test_e1_the_live_titration_equals_the_certified_trajectory_minute_by_minute(scenario, tit_items):
    d = Driver().run_plan(_plan(scenario))
    assert not d.site.halted, d.site.halt_reason
    got = d.committed()
    want = {row["minute"]: (row["sbp"], row["dbp"], row["map"]) for row in tit_items[scenario]["common"]}
    assert sorted(got) == list(range(1, 33))
    assert [m for m in range(1, 33) if (got[m]["sbp"], got[m]["dbp"], got[m]["map"]) != want[m]] == [], scenario
    assert d.site.grant["grant_id"] == ng.GRANT_ID and d.site.ne_verdict.ok


def test_e2_the_live_start_equals_the_human_reviewed_frf_center_reference():
    record = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "revision", "PHASE3_FRF_TONE_V1_CANDIDATE.json")))
    series = record["witnesses"]["CENTER_REFERENCE"]
    d = Driver().run_plan({2: START10})
    assert not d.site.halted
    got = d.committed()
    wrong = []
    for row in series["per_minute"]:
        minute = row["minute"]
        if not 1 <= minute <= 32:
            continue
        sbp, dbp = int(round(row["sbp"])), int(round(row["dbp"]))
        if (got[minute]["sbp"], got[minute]["dbp"], got[minute]["map"]) != (sbp, dbp, ra.derived_map(sbp, dbp)):
            wrong.append(minute)
    assert wrong == [], "the live series is the certified FR-F series under the pressure-equality and rounding contract of the authority"
    assert {row["minute"]: (row["sbp"], row["dbp"], row["map"]) for row in series["displayed_pressure"]} == {m: (got[m]["sbp"], got[m]["dbp"], got[m]["map"]) for m in (2, 7, 17, 32)}


def test_e3_the_old_frf_artifact_is_preserved_and_still_reads_as_unsupported():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "revision", "PHASE3_FRF_TONE_V1_CANDIDATE.json")
    record = json.load(open(path))
    assert record["order_not_mapped"] is not None or record.get("the_certified_run_is_untouched") is not None
    d = Driver(env=V3_ENV)
    d.ask(2)
    d.order(START10)
    assert d.site.halted and "norepinephrine" in d.site.halt_reason, "the certified FR-F outcome under the pressure grant is unchanged"


def test_e4_both_gi_cases_satisfy_the_same_contract():
    for case in ("gi_bleed_57m", "gi_bleed_72f"):
        d = Driver(case).run_plan({2: START5, 10: _order_text("INCREASE", 10.0), 18: STOP}, until=30)
        assert not d.site.halted, (case, d.site.halt_reason)
        assert d.site.grant["grant_id"] == ng.GRANT_ID and sorted(d.committed()) == list(range(1, 31)) and d.site.ne_verdict.history == ((2, 5.0), (10, 10.0), (18, 0.0))


def test_e5_norepinephrine_raises_the_pressure_only_through_the_common_path_and_stopping_decays_it():
    without = Driver().run_plan({}, until=24).committed()
    with_ne = Driver().run_plan({2: START10, 10: STOP}, until=24).committed()
    assert [m for m in range(1, 3) if with_ne[m] != without[m]] == [], "nothing differs before the order acts"
    assert with_ne[8]["map"] > without[8]["map"] and with_ne[9]["sbp"] > without[9]["sbp"]
    assert with_ne[24]["map"] >= without[24]["map"], "after a stop the effect has decayed toward the untreated trajectory but not instantly"
    assert with_ne[11]["map"] > without[11]["map"], "a stop never erases the contribution in the minute of the order"


# ============================================================================================================================================
# F. the fail-closed matrix
# ============================================================================================================================================

def _stopped(d):
    return d.site.halted and d.site.halt_reason.startswith("UNSUPPORTED_AUTHORITY_ACTION")


@pytest.mark.parametrize("name, plan, expected_reason, expected_problem", [
    ("weight_based", {2: "Start norepinephrine at 0.1 mcg/kg/min."}, "norepinephrine_order_not_carried", ne.WRONG_UNITS),
    ("bare_continuation", {2: START5, 5: "Continue norepinephrine."}, "norepinephrine_order_not_carried", ne.BARE_CONTINUATION),
    ("names_no_drug", {2: START5, 5: "Stop the infusion."}, "infusion_adjustment", None),
    ("another_vasopressor", {2: "Start dobutamine at 5 mcg/min."}, "dobutamine", None),
])
def test_f1_a_malformed_or_unsupported_order_stops_the_session_by_name(name, plan, expected_reason, expected_problem):
    d = Driver().run_plan(plan, until=12)
    assert _stopped(d), (name, d.site.halt_reason)
    assert expected_reason in d.site.halt_reason
    if expected_problem is not None:
        assert expected_problem in {item["problem"] for item in d.site.ne_verdict.problems}
    assert d.site.records[-1]["outcome"] == ra.ABORTED and d.site.records[-1]["committed"] == []


def test_f2_the_stop_is_permanent_nothing_recovers_the_session_and_nothing_falls_back():
    d = Driver().run_plan({2: START5, 5: "Start norepinephrine at 0.1 mcg/kg/min."}, until=12)
    assert _stopped(d)
    committed = list(d.site.minutes_committed)
    for text in (STOP, START5, "Stop norepinephrine."):
        d.order(text)
        d.ask(3)
    assert d.site.halted and list(d.site.minutes_committed) == committed, "a later valid order recovers nothing"
    art = d.site.artifact()
    assert art["experiment_outcome"] == "INVALID_FOR_CONTINUATION" and art["post_commit_policy"]["silent_fallback_to_the_legacy_engine"] is False
    record = se.session_record_of(art)
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["continuation_allowed"] is False and record["legacy_fallback_allowed"] is False


def test_f3_a_failure_before_the_first_commit_leaves_the_legacy_encounter_unchanged():
    d = Driver()
    before = deepcopy(d.state)
    d.order("Start norepinephrine at 0.1 mcg/kg/min.")
    assert _stopped(d) and not d.site.minutes_committed
    art = d.site.artifact()
    assert art["experiment_outcome"] == "EXPERIMENT_HALTED" and se.session_record_of(art)["lifecycle"] == se.PRECOMMIT_ABORT
    assert {k: v for k, v in d.state["observable"].items() if k in ("sbp", "dbp", "map")} != {}, "the legacy engine keeps owning the pressure"
    assert before["observable"]["sbp"] is not None


def test_f4_a_question_or_an_order_the_reader_does_not_execute_never_reaches_the_authority():
    for text in ("Titrate norepinephrine to MAP 65.", "Increase norepinephrine by 2 mcg/min.", "Start norepinephrine 10."):
        d = Driver().run_plan({2: START5}, until=4)
        committed = list(d.site.minutes_committed)
        history = d.site.ne_verdict.history
        d.order(text)
        d.ask(3)
        assert not d.site.halted, (text, d.site.halt_reason)
        assert d.site.ne_verdict.history == history == ((2, 5.0),), "a target, a relative change or a rate without a unit is a question: nothing is executed and the infusion is what it was"
        assert len(d.site.minutes_committed) == len(committed) + 1, "the question changed nothing and the three minutes of clinical time are ONE committed turn"


def test_f5_a_start_then_an_adjustment_in_the_same_minute_is_benign_and_equals_the_later_order():
    d = Driver()
    d.ask(2)
    d.order(START5)
    d.order(_order_text("INCREASE", 10.0))
    d.ask(8)
    assert not d.site.halted, d.site.halt_reason
    assert d.site.ne_verdict.ok


@pytest.mark.parametrize("plan", [{2: START5, 5: "Stop norepinephrine.", 9: "Restart norepinephrine at 8 mcg/min."}, {2: START5, 6: "Continue norepinephrine at 5 mcg/min."},
                                  {2: START5, 6: "Increase norepinephrine to 8 mcg/min.", 9: "Decrease norepinephrine to 3 mcg/min.", 12: "Stop norepinephrine."}])
def test_f6_every_ratified_semantic_runs_without_stopping(plan):
    d = Driver().run_plan(plan, until=16)
    assert not d.site.halted, d.site.halt_reason
    assert d.site.ne_verdict.ok and d.site.ne_verdict.problems == ()


def test_f7_a_tone_selector_that_does_not_bind_runs_nothing_and_falls_back_to_nothing(monkeypatch):
    monkeypatch.setenv(ra.TONE_FLAG, "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V2")
    d = Driver(env={**NE_ENV, ra.TONE_FLAG: "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V2"})
    assert d.site is None and d.enc.shadow.runner is None
    assert [item.exception for item in d.enc.shadow.failures] == [rs.TONE_SNAPSHOT_NOT_BOUND]
    monkeypatch.setenv(ra.TONE_FLAG, tn.SNAPSHOT_ID)
    monkeypatch.setenv(ra.SNAPSHOT_FLAG, "gi_pressure_committed")
    d2 = Driver(env={**NE_ENV, ra.SNAPSHOT_FLAG: "gi_pressure_committed"})
    assert d2.site is None and [item.exception for item in d2.enc.shadow.failures if item.exception == rs.TONE_SNAPSHOT_NOT_BOUND], "a tone on another hemodynamics was never reviewed"


def test_f8_the_session_must_have_run_the_ratified_tone_configuration_or_the_minute_is_refused(monkeypatch):
    d = Driver()
    d.ask(2)
    adapter = d.enc.shadow.runner.adapter
    forged = copy.copy(adapter.tone_configuration)
    object.__setattr__(forged, "tone_gain", 0.9)
    monkeypatch.setattr(adapter, "tone_configuration", forged)
    d.ask(1)
    assert d.site.halted and d.site.halt_reason.startswith(ra.PRESSURE_CONFIGURATION_MISMATCH)


# ============================================================================================================================================
# G. the artifact and its replay
# ============================================================================================================================================

def _reseal(artifact):
    body = {key: value for key, value in artifact.items() if key != "artifact_digest"}
    return {**body, "artifact_digest": ra.digest_of(body)}


@pytest.fixture(scope="module")
def sequence_artifact():
    with pytest.MonkeyPatch.context() as patch:
        for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
            patch.delenv(name, raising=False)
        for name, value in NE_ENV.items():
            patch.setenv(name, value)
        d = Driver().run_plan(_plan("TIT-4"), until=30)
        assert not d.site.halted, d.site.halt_reason
        return json.loads(ra.canonical(d.site.artifact()))


def test_g1_the_artifact_names_its_grant_verifies_and_replays_from_itself_alone(sequence_artifact):
    art = sequence_artifact
    assert art["grant"] == ng.summary(ng.GRANT) and art["authority_label"] == ra.REAL_PRESSURE_LABEL and art["authority_mode"] == "PRESSURE_ONLY"
    block = art["norepinephrine_authority"]
    assert block["tone_configuration"] == tn.bind().summary() and block["resident_visible"] is False and block["scoring"] is False and block["authority_scope"] == ["sbp", "dbp", "map"]
    assert block["consciousness_under_tone"] == ne.UNDER_TONE and block["pump_dependence"] == "COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED" and block["writer_version"] == ts.WRITER_VERSION
    assert all(record["norepinephrine_contract"]["ok"] and record["grant_id"] == ng.GRANT_ID and record["grant_fingerprint"] == ng.GRANT_FINGERPRINT for record in art["minutes"] if record.get("committed"))
    verdict = ra.verify_artifact(art)
    assert verdict["complete"] and verdict["grant_is_the_registered_one"] and verdict["real_claims_problems"] == [] and verdict["claims_are_honest"]
    replay = ra.replay_site_artifact(art)
    assert replay["reproduces"] and replay["covers_every_committed_minute"] and replay["overlay_replay"]["reproduces"] and replay["real_claims_problems"] == []
    assert replay["overlay_replay"]["snapshot_matches"] and replay["overlay_replay"]["boundary_matches"] and replay["overlay_replay"]["rows_compared"] > 0
    overlay = art["consciousness_overlay"]
    assert overlay["authority"] is False and overlay["resident_visible"] is False and overlay["writes_mental_status"] is False and overlay["under_tone"] == ne.UNDER_TONE
    assert overlay["snapshot"]["profile_digest"] == ne.TONE_OVERLAY_PROFILE_DIGEST == ne._tone_overlay_profile_digest()


def _mutate(artifact, edit):
    art = json.loads(json.dumps(artifact))
    edit(art)
    return _reseal(art)


def _scenario_of(art):
    return art["replay_input"]["scenario"]


MUTANTS = {
    "renamed_to_the_earlier_grant": lambda a: a.update(grant={**pg.summary(pg.GRANT_V3)}),
    "grant_fingerprint_forged": lambda a: a["grant"].update(fingerprint="0" * 64),
    "norepinephrine_block_removed": lambda a: a.pop("norepinephrine_authority"),
    "tone_configuration_forged": lambda a: a["norepinephrine_authority"]["tone_configuration"].update(configuration_digest="0" * 64),
    "limitations_not_declared": lambda a: a["norepinephrine_authority"].update(consciousness_under_tone="RESOLVED"),
    "resident_visible_claim": lambda a: a["norepinephrine_authority"].update(resident_visible=True),
    "scoring_claim": lambda a: a["norepinephrine_authority"].update(scoring=True),
    "scope_widened": lambda a: a["norepinephrine_authority"].update(authority_scope=["sbp", "dbp", "map", "pulse"]),
    "reader_not_named": lambda a: a["norepinephrine_authority"]["reader"].update(git_blob="0" * 40),
    "snapshot_id_changed": lambda a: a.update(snapshot_id="gi_pressure_committed"),
    "captured_tone_gain_changed": lambda a: _scenario_of(a)["profile"].update(vasoconstrictor_support_to_tone_gain=0.9),
    "contract_not_clean_on_a_committed_minute": lambda a: next(m for m in a["minutes"] if m.get("committed"))["norepinephrine_contract"].update(ok=False),
    "contract_digest_forged": lambda a: next(m for m in a["minutes"] if m.get("committed"))["norepinephrine_contract"].update(digest="0" * 64),
    "contract_history_rewritten": lambda a: next(m for m in a["minutes"] if m.get("committed") and m["norepinephrine_contract"]["rate_history"])["norepinephrine_contract"].update(
        rate_history=[[2, 9.0]]),
    "overlay_without_the_tone": lambda a: a["consciousness_overlay"].pop("tone_configuration"),
    "overlay_claims_authority": lambda a: a["consciousness_overlay"].update(authority=True),
}


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_g2_a_renamed_forged_or_mislabelled_artifact_fails_even_when_its_digest_is_recomputed(sequence_artifact, name):
    art = _mutate(sequence_artifact, MUTANTS[name])
    verdict = ra.verify_artifact(art)
    replay = ra.replay_site_artifact(art)
    assert not verdict["complete"] or not replay["reproduces"], f"{name}: the mutated artifact still passes"


def test_g3_the_earlier_artifacts_verify_and_replay_exactly_as_before_and_cannot_wear_the_new_block(sequence_artifact):
    d = Driver(env=V3_ENV).run_plan({}, until=6)
    art = json.loads(ra.canonical(d.site.artifact()))
    assert art["grant"]["grant_id"] == pg.GRANT_ID_V3 and "norepinephrine_authority" not in art and "tone_configuration" not in json.dumps(art["consciousness_overlay"])
    assert ra.verify_artifact(art)["complete"] and ra.replay_site_artifact(art)["reproduces"]
    wearing = _mutate(art, lambda a: a.update(norepinephrine_authority=copy.deepcopy(sequence_artifact["norepinephrine_authority"])))
    assert not ra.verify_artifact(wearing)["complete"]
    assert ne.artifact_problems(art) == []


def test_g4_a_replay_in_a_swapped_registry_still_rebuilds_the_writers_it_names(sequence_artifact):
    import runtime_tone_support
    runtime_tone_support.ensure_registered()
    assert ra.replay_site_artifact(sequence_artifact)["reproduces"]


# ============================================================================================================================================
# H. non-regression, the effective stop, isolation, and what is not granted
# ============================================================================================================================================

MANAGEMENT = {0: "Give 1 litre of normal saline over 15 minutes.", 16: "Transfuse 1 unit of packed red blood cells.", 30: "Start pantoprazole 80 mg IV."}


def test_h1_without_norepinephrine_nothing_moves_the_series_is_the_earlier_authoritys_to_the_last_digit():
    under_ne = Driver().run_plan(MANAGEMENT, until=40)
    under_v3 = Driver(env=V3_ENV).run_plan(MANAGEMENT, until=40)
    assert not under_ne.site.halted and not under_v3.site.halted, (under_ne.site.halt_reason, under_v3.site.halt_reason)
    assert under_ne.committed() == under_v3.committed() and len(under_ne.committed()) >= 3 and max(under_ne.committed()) >= 40, "the three management orders commit at the minutes they end"
    assert [r.get("moved_fields") for r in under_ne.site.records if r.get("committed")] == [r.get("moved_fields") for r in under_v3.site.records if r.get("committed")]
    assert under_ne.site.ne_verdict.ok and under_ne.site.ne_verdict.history == ()


def test_h2_both_gi_cases_without_norepinephrine_equal_the_earlier_authority():
    for case in ("gi_bleed_57m", "gi_bleed_72f"):
        assert Driver(case).run_plan({}, until=20).committed() == Driver(case, env=V3_ENV).run_plan({}, until=20).committed()


def test_h3_only_the_pressure_domain_is_written_and_nothing_the_resident_sees_or_is_scored_on_gains_a_tone_variable():
    d = Driver().run_plan({2: START10, 12: STOP}, until=30)
    assert not d.site.halted
    for record in d.site.records:
        if record.get("committed"):
            assert set(record["moved_fields"]) <= {"sbp", "dbp", "map"}, record["moved_fields"]
    plain = Driver().run_plan({}, until=30)
    assert set(d.state["observable"]) == set(plain.state["observable"]) and set(d.state) - {ra.PROVENANCE_ANCHOR_KEY} == set(plain.state) - {ra.PROVENANCE_ANCHOR_KEY}, "no key is added to the encounter by the tone"
    named = [key for key in set(d.state["observable"]) | set(d.state) if any(word in str(key).lower() for word in ("tone", "vasoconstrict", "rate_history", "vasopressor_support"))]
    assert named == [], named
    for name in ("mental_status", "hr", "spo2"):
        assert d.state["observable"].get(name) == plain.state["observable"].get(name), f"{name} is the legacy engine's, whatever the tone"


def test_h4_the_legacy_mental_status_is_never_written_by_the_authority_under_tone():
    d = Driver().run_plan({2: START10}, until=30)
    for record in d.site.records:
        assert "mental_status" not in set(record.get("moved_fields") or ()), record.get("moved_fields")
        overlay = dict(record.get("consciousness_overlay") or {})
        assert "writes_mental_status" not in overlay or overlay["writes_mental_status"] is False
    assert d.site.overlay.violations == []
    assert dict(d.site.artifact()["consciousness_overlay"])["written_into_the_encounter"] is False


def test_h5_the_effective_stop_and_a_reopened_session_hold_after_a_norepinephrine_failure():
    d = Driver().run_plan({2: START5, 6: "Start norepinephrine at 0.1 mcg/kg/min."}, until=12)
    assert _stopped(d)
    session_store = {ra.SITE_KEY: d.site, ra.ARTIFACT_KEY: d.site.artifact()}
    d.site._session_store = session_store
    guard = se.continuation_guard(session_store, d.state, environ=NE_ENV)
    assert guard["allowed"] is False and guard["lifecycle"] == se.INVALID_FOR_CONTINUATION
    reopened = {ra.ARTIFACT_KEY: d.site.artifact()}
    assert se.continuation_guard(reopened, d.state, environ=NE_ENV)["allowed"] is False, "a session reopened from the artifact alone is still stopped"
    assert se.replay_session_record(d.site.artifact())["reproduces"] is True


def test_h6_the_families_that_are_not_granted_open_no_site_and_the_tone_flag_changes_nothing_for_them():
    from clinical_core import legacy_adapter
    for case in ("pe_70m", "acs_70f_left_main", "asthma_30m", "opioid_45m", "pulmonary_edema_68m"):
        try:
            d = Driver(case)
        except Exception:
            continue
        assert d.site is None, case
        runner = getattr(d.enc.shadow, "runner", None)
        assert runner is None or not isinstance(runner.adapter, ne.BoundToneSupport), case
    assert legacy_adapter is not None


def test_h7_the_pulmonary_edema_negative_control_and_the_pe_probe_remain_development_probes_only():
    record = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "revision", "NEGATIVE_CONTROL_HYPERTENSIVE_PULMONARY_EDEMA_NOREPI_V1.json")))
    assert "NEGATIVE_CONTROL" in json.dumps(record)
    assert "pulmonary edema authority" in ng.GRANT["not_granted"] and "pump-limited families" in ng.GRANT["not_granted"]
    assert ts.summary()["registered_adapters_declaring_it"] == [], "no registered adapter declares the reader: the shadow's development copy stays a development copy"
    assert [name for name, adapter in __import__("runtime_shadow_families").ADAPTERS.items() if adapter.tone_support_witness is not None] == []


def test_h8_the_new_selector_is_documented_nowhere_a_resident_or_the_pilot_can_reach(monkeypatch):
    import glob
    page = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"), encoding="utf-8").read()
    assert ra.TONE_FLAG not in page and "norepinephrine_authority" not in page and "runtime_ne_authority" not in page, "the page names neither the selector nor the module: it orchestrates and decides nothing"
    for name in ra.PILOT_FLAGS:
        monkeypatch.setenv(name, "1")
        break
    gate = ra.gate(deepcopy(Driver(env=V3_ENV).arrival), environ={**NE_ENV, ra.PILOT_FLAGS[0]: "1"}, unsupported=())
    assert not gate.granted or not gate.conditions["no_pilot"] is False
    assert glob.glob("runtime_ne_*.py") == ["runtime_ne_authority.py", "runtime_ne_grant.py"] or sorted(glob.glob("runtime_ne_*.py")) == ["runtime_ne_authority.py", "runtime_ne_grant.py"]


def test_h9_the_tone_selector_is_part_of_the_configuration_an_experiment_opened_on():
    me = SimpleNamespace(environ=None, snapshot_id=ps.SNAPSHOT_ID, environment="development", tone_configuration=tn.bind())
    assert ra._configuration_changed(me, NE_ENV) is False
    assert ra._configuration_changed(me, V3_ENV) is True, "a session under the norepinephrine grant whose tone selector disappears is a configuration change"
    assert ra._configuration_changed(me, {**NE_ENV, ra.TONE_FLAG: "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V2"}) is True
    older = SimpleNamespace(environ=None, snapshot_id=ps.SNAPSHOT_ID, environment="development", tone_configuration=None)
    assert ra._configuration_changed(older, V3_ENV) is False and ra._configuration_changed(older, NE_ENV) is True, "a session under the earlier grant whose environment gains a tone selector is a change too"


def test_h10_a_stored_session_claim_holds_only_while_the_tone_selector_is_what_it_was():
    d = Driver().run_plan({2: START5}, until=6)
    record = se.session_record_of(d.site.artifact())
    assert record["grant_id"] == ng.GRANT_ID and se._configuration_holds(record, NE_ENV)
    assert not se._configuration_holds(record, V3_ENV) and not se._configuration_holds(record, {**NE_ENV, ra.TONE_FLAG: "x"})
    earlier = Driver(env=V3_ENV).run_plan({}, until=4)
    record3 = se.session_record_of(earlier.site.artifact())
    assert record3["grant_id"] == pg.GRANT_ID_V3 and se._configuration_holds(record3, V3_ENV) and not se._configuration_holds(record3, NE_ENV)


def test_g5_a_fresh_process_verifies_and_replays_the_artifact_from_the_file_alone(sequence_artifact, tmp_path):
    import subprocess
    import sys
    path = tmp_path / "ne_artifact.json"
    path.write_text(json.dumps(sequence_artifact), encoding="utf-8")
    code = ("import json, sys; import runtime_authority as ra; a = json.load(open(sys.argv[1]));"
            " r = ra.replay_site_artifact(a); v = ra.verify_artifact(a); print(r['reproduces'], v['complete'], r['overlay_replay']['reproduces'])")
    done = subprocess.run([sys.executable, "-c", code, str(path)], cwd=os.path.dirname(os.path.abspath(__file__)), capture_output=True, text=True, timeout=600,
                          env={key: value for key, value in os.environ.items() if not key.startswith("MRS_")})
    assert done.stdout.split() == ["True", "True", "True"], (done.stdout, done.stderr[-400:])


@pytest.mark.parametrize("scenario", ["FR-A", "FR-B", "FR-C", "FR-D", "FR-E", "FR-G"])
def test_h11_the_first_reviews_scenarios_without_norepinephrine_are_the_same_under_both_grants(scenario):
    data = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "revision", "PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json")))
    item = next(entry for entry in data["items"] if entry["scenario_id"] == scenario)

    def run(env):
        d = Driver(item["case_id"], env=env)
        for kind, text in item["script"]:
            if d.site.halted:
                break
            d.order(text) if kind == "order" else d.ask(2)
        return d
    under_ne, under_v3 = run(NE_ENV), run(V3_ENV)
    assert under_ne.site.grant["grant_id"] == ng.GRANT_ID and under_v3.site.grant["grant_id"] == pg.GRANT_ID_V3
    assert under_ne.committed() == under_v3.committed() and under_ne.committed(), scenario
    assert (under_ne.site.halted, under_ne.site.halt_reason) == (under_v3.site.halted, under_v3.site.halt_reason), "the same stop, for the same reason, at the same time"
    assert [r.get("outcome") for r in under_ne.site.records] == [r.get("outcome") for r in under_v3.site.records]


@pytest.mark.parametrize("text, history, benign", [
    ("Start norepinephrine at 5 mcg/min. Then increase norepinephrine to 10 mcg/min.", ((2, 10.0),), 1),
    ("Start norepinephrine at 5 mcg/min and stop norepinephrine.", (), 2),
])
def test_f9_two_norepinephrine_actions_in_one_turn_are_one_minute_and_the_later_one_is_what_runs(text, history, benign):
    d = Driver()
    d.ask(2)
    d.order(text)
    d.ask(5)
    assert not d.site.halted, d.site.halt_reason
    assert d.site.ne_verdict.ok and d.site.ne_verdict.history == history and len(d.site.ne_verdict.benign) == benign


def test_c5b_a_live_reader_that_is_not_the_successor_the_grant_pins_opens_nothing(monkeypatch, tmp_path):
    reader = os.path.join(os.path.dirname(os.path.abspath(__file__)), "family_parser.py")
    (tmp_path / "family_parser.py").write_bytes(open(reader, "rb").read() + b"\n# a later edit of the reader\n")
    assert ne.reader_problems() == []
    monkeypatch.setattr(ne, "ROOT", tmp_path)
    assert ne.reader_problems() != [], "the grant is intact; it is the LIVE reader that is not the pinned successor"
    ok, why = ra._norepinephrine_permission(NE_ENV, case_id=CASE, snapshot_id=ps.SNAPSHOT_ID, family="gi_bleed", domain=ng.DOMAIN, lineage=ng.lineage_of(ng.GRANT), reconstruction=None)
    assert not ok and any(ng.READER_WRONG in reason for reason in why)
    import pilot_acceptance
    assert ra.open_site(deepcopy(pilot_acceptance.Encounter(CASE).state), environ={**NE_ENV, store.STORE_FLAG: tempfile.mkdtemp()}) is None


def test_c1b_the_gate_refuses_what_the_norepinephrine_grant_refuses_even_if_the_earlier_grant_would_not(monkeypatch):
    import pilot_acceptance
    arrival = deepcopy(pilot_acceptance.Encounter(CASE).state)
    env = {**NE_ENV, store.STORE_FLAG: tempfile.mkdtemp()}
    assert ra.gate(arrival, environ=env, unsupported=()).granted
    monkeypatch.setattr(ne, "reader_problems", lambda: ["the reader changed"])
    verdict = ra.gate(arrival, environ=env, unsupported=())
    assert not verdict.granted and not verdict.conditions["explicit_development_grant"] and any("reader" in reason.lower() for reason in verdict.reasons)
    assert ra.open_site(arrival, environ=env) is None, "and the earlier grant, which would have permitted this run, is NOT consulted for an environment that names the tone snapshot"


def test_c7_the_faculty_review_environment_runs_the_pressure_authority_alone():
    import runtime_faculty_review as review
    base = {review.FLAG: "on", ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: ps.SNAPSHOT_ID, ra.ENVIRONMENT_FLAG: "development"}
    assert review.environment_conditions(base)["snapshot"] is True
    assert review.environment_conditions({**base, ra.TONE_FLAG: tn.SNAPSHOT_ID})["snapshot"] is False, "a process that names the tone snapshot is not a review configuration"


def test_d7_a_norepinephrine_order_the_shadow_mapping_refuses_is_a_problem_even_if_the_authority_read_it_fine(monkeypatch):
    cfg = tn.bind()
    seq = [_event("a", 2, "start", 5.0, "mcg/min")]
    assert ne.check(seq, cfg).ok
    real = ts.infusion_history

    def refusing(events, witness):
        physical, carried, declared = real(events, witness)
        return physical, carried, tuple(declared) + (("a", "norepinephrine", ts.REFUSED, "the mapping could not carry it"),)
    monkeypatch.setattr(ts, "infusion_history", refusing)
    verdict = ne.check(seq, cfg)
    assert not verdict.ok and ne.SHADOW_REFUSED in {item["problem"] for item in verdict.problems}


def test_d8_a_contract_that_cannot_be_checked_is_a_failure_never_a_pass():
    verdict = ne.check([_event("a", 2, "start", 5.0, "mcg/min")], SimpleNamespace(not_a="tone configuration"))
    assert not verdict.ok and verdict.problems[0]["problem"].startswith("THE_CONTRACT_COULD_NOT_BE_CHECKED")
    assert not ne.check([_event("a", 2, "start", 5.0, "mcg/min")], None).ok


def _writers(scenario):
    return [item for item in scenario["contributors"] if str(item.get("type", "")).startswith("norepinephrine")]


def test_g6_the_captured_scenario_is_held_to_the_ratified_values_the_one_writer_and_the_history_the_authority_read(sequence_artifact):
    cfg = tn.bind()
    scenario = sequence_artifact["replay_input"]["scenario"]
    history = [tuple(item) for item in sequence_artifact["minutes"][-1]["norepinephrine_contract"]["rate_history"]]
    assert ne.scenario_tone_problems(scenario, cfg, history) == [] and history == [(2, 5.0), (10, 10.0), (18, 4.0), (25, 0.0)]

    def edited(edit):
        copy_ = json.loads(json.dumps(scenario))
        edit(copy_)
        return copy_
    for name, edit, args in [
        ("constants", lambda s: _writers(s)[0].update(onset_tau_min=2.0), (history,)),
        ("half_effect", lambda s: _writers(s)[0].update(half_effect_rate_mcg_min=12.0), (history,)),
        ("offset", lambda s: _writers(s)[0].update(offset_tau_min=3.0), (history,)),
        ("tone_gain", lambda s: s["profile"].update(vasoconstrictor_support_to_tone_gain=0.9), (history,)),
        ("tone_gain_absent", lambda s: s["profile"].update(vasoconstrictor_support_to_tone_gain=None), (history,)),
        ("writer_version", lambda s: _writers(s)[0].update(writer_version="norepinephrine_rate_history/P3-999"), (history,)),
        ("two_writers", lambda s: s["contributors"].append({**_writers(s)[0], "id": "a_second_infusion"}), (history,)),
        ("no_writer_but_an_infusion_was_read", lambda s: s.update(contributors=[c for c in s["contributors"] if not str(c.get("type", "")).startswith("norepinephrine")]), (history,)),
        ("history_rewritten", lambda s: None, ([(2, 9.0)],)),
    ]:
        found = ne.scenario_tone_problems(edited(edit), cfg, *args)
        assert found, f"{name}: the captured scenario was not held to the snapshot"
    assert ne.scenario_tone_problems("not a scenario", cfg) != [] and ne.scenario_tone_problems(scenario, SimpleNamespace(x=1)) != []
    assert ne.scenario_tone_problems(edited(lambda s: s.update(contributors=[c for c in s["contributors"] if not str(c.get("type", "")).startswith("norepinephrine")])), cfg, []) == []


def test_g7_a_minute_whose_own_captured_scenario_carries_other_tone_values_fails_even_if_the_artifacts_does_not(sequence_artifact):
    def edit(art):
        committed = [m for m in art["minutes"] if m.get("committed")]
        committed[-1]["replay_input"]["scenario"]["profile"]["vasoconstrictor_support_to_tone_gain"] = 0.9
    art = _mutate(sequence_artifact, edit)
    assert any("minute" in item for item in ne.artifact_problems(art)), ne.artifact_problems(art)[:3]
    assert not ra.verify_artifact(art)["complete"]


# ============================================================================================================================================
# the findings of the independent adversarial review (P3-500): each reproduced first, then repaired, then defended here
# ============================================================================================================================================

def _recontract(contract):
    contract["digest"] = ne.digest({"orders": contract["orders"], "history": contract["rate_history"], "problems": contract["problems"], "benign": sorted(contract["benign_gaps"])})


def _first_contract(art):
    return next(m for m in art["minutes"] if m.get("committed") and m["norepinephrine_contract"]["orders"])["norepinephrine_contract"]


def _last_contract(art):
    return [m for m in art["minutes"] if m.get("committed") and m["norepinephrine_contract"]["orders"]][-1]["norepinephrine_contract"]


def test_g8_a_norepinephrine_run_relabelled_as_the_earlier_grant_with_an_honest_overlay_spliced_in_fails_review_a1(sequence_artifact):
    honest = json.loads(ra.canonical(Driver(env=V3_ENV).run_plan({}, until=30).site.artifact()))
    assert ra._tone_content_problems(honest) == [] and ra.verify_artifact(honest)["complete"]

    def forge(a):
        a["grant"] = pg.summary(pg.GRANT_V3)
        a.pop("norepinephrine_authority")
        a["consciousness_overlay"] = copy.deepcopy(honest["consciousness_overlay"])
        for record in a["minutes"]:
            record.pop("norepinephrine_contract", None)
            record["grant_id"], record["grant_fingerprint"] = pg.GRANT_ID_V3, pg.GRANT_FINGERPRINT_V3
    forged = _mutate(sequence_artifact, forge)
    problems = ra.real_artifact_problems(forged)
    assert any("does not stand under the norepinephrine grant" in item for item in problems), problems[:4]
    assert not ra.verify_artifact(forged)["complete"]
    assert not ra.replay_site_artifact(forged)["reproduces"], "the replay says so too: the forged artifact still carries the writer and the lifted pressure"


def test_g9_the_contract_rows_are_the_writers_orders_and_the_semantics_are_recomputed_review_a2(sequence_artifact):
    assert ne.contract_writer_problems(_last_contract(sequence_artifact), sequence_artifact["replay_input"]["scenario"]) == []

    def rewrite_rate(a):
        contract = _last_contract(a)
        contract["orders"][1]["rate_mcg_min"] = 9.0
        _recontract(contract)

    def drop_an_order(a):
        contract = _last_contract(a)
        contract["orders"] = contract["orders"][:-1]
        _recontract(contract)

    def relabel(a):
        contract = _last_contract(a)
        contract["orders"][1]["semantic"] = "DECREASE"
        _recontract(contract)
    for edit in (rewrite_rate, drop_an_order, relabel):
        art = _mutate(sequence_artifact, edit)
        assert any("minute" in item for item in ne.artifact_problems(art)) and not ra.verify_artifact(art)["complete"], edit.__name__


def test_g10_the_carried_class_is_modelled_not_unsupported_in_the_artifacts_dispositions_review_a3(sequence_artifact):
    rows = [row for record in sequence_artifact["minutes"] for row in (record.get("action_dispositions") or []) if row["class"] == "norepinephrine"]
    assert rows and {row["disposition"] for row in rows} == {ra.SUPPORTED_MODELED}
    assert ra.disposition_of("norepinephrine", "EXECUTED") == ra.UNSUPPORTED_ACTION and ra.disposition_of("norepinephrine", "EXECUTED", ("norepinephrine",)) == ra.SUPPORTED_MODELED
    assert ra.disposition_of("norepinephrine", "HELD_REASONING", ("norepinephrine",)) == ra.HELD_NOT_EXECUTED, "a fate that says the order did not act still wins"


def test_d9_the_contract_reads_the_class_as_the_site_does_and_never_passes_what_it_cannot_see_review_a4():
    cfg = tn.bind()
    odd = _event("a", 2, "start", 0.1, "mcg/kg/min", kind="Norepinephrine", type_="Norepinephrine")
    assert not ne.check([odd], cfg).ok, "a kind spelt differently is still the class, and it is not an order the contract reads"
    assert not ne.check([_event("a", 2, "start", 5.0, "mcg/min", kind=" NOREPINEPHRINE ")], cfg).ok, "and the shadow mapping, which reads the exact kind, would not carry it: the two readings differ"
    assert ne.NO_MIRROR in {item["problem"] for item in ne.check(None, cfg).problems} and ne.NO_MIRROR in {item["problem"] for item in ne.check([], cfg, None).problems}
    executed = [{"type": "norepinephrine", "operation": "start", "rate": 5.0, "units": "mcg/min"}]
    assert ne.NOT_MIRRORED in {item["problem"] for item in ne.check([], cfg, ran=executed).problems}, "an executed infusion the mirror does not hold is an infusion the run does not see"
    assert ne.check([_event("a", 2, "start", 5.0, "mcg/min")], cfg, ran=executed).ok
    assert ne.check([_event("a", 2, "start", 5.0, "mcg/min")], cfg, ran=[{"type": "fluid"}]).ok
    d = Driver()
    assert not d.site._norepinephrine_verdict(SimpleNamespace(), []).ok, "a session that has no mirror is not a clean contract"


def test_g11_verifying_an_earlier_artifact_registers_nothing_new_in_the_core_review_a5(tmp_path):
    import subprocess
    import sys
    art = json.loads(ra.canonical(Driver(env=V3_ENV).run_plan({}, until=6).site.artifact()))
    path = tmp_path / "v3.json"
    path.write_text(json.dumps(art), encoding="utf-8")
    code = ("import json, sys; import runtime_authority as ra; a = json.load(open(sys.argv[1])); v = ra.verify_artifact(a); r = ra.replay_site_artifact(a);"
            " print(v['complete'], r['reproduces'], 'runtime_ne_authority' in sys.modules, 'runtime_tone_support' in sys.modules)")
    done = subprocess.run([sys.executable, "-c", code, str(path)], cwd=os.path.dirname(os.path.abspath(__file__)), capture_output=True, text=True, timeout=600,
                          env={key: value for key, value in os.environ.items() if not key.startswith("MRS_")})
    assert done.stdout.split() == ["True", "True", "False", "False"], (done.stdout, done.stderr[-300:])


def test_g12_the_artifact_carries_the_label_the_grant_names_review_a6(sequence_artifact):
    assert sequence_artifact["authority_label"] == ng.ARTIFACT_LABEL == ng.GRANT["replay_identity"]["artifact_label"] == ra.REAL_PRESSURE_LABEL
    art = _mutate(sequence_artifact, lambda a: a.update(authority_label="SOMETHING_ELSE"))
    assert not ra.verify_artifact(art)["complete"]
    # the grant's own re-derivation says so by itself (the generic label handling is not what protects this)
    assert ne.artifact_problems(sequence_artifact) == [], "an honest artifact has no problem of its own"
    assert "the artifact does not carry the label the grant names" in ne.artifact_problems(art)
    renamed = _mutate(sequence_artifact, lambda a: a.update(authority_label="REAL_DEVELOPMENT_PRESSURE_AUTHORITY_V2"))
    assert "the artifact does not carry the label the grant names" in ne.artifact_problems(renamed)
