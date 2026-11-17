"""P3-378 to P3-383 (FD-PROMOTE-01 to FD-PROMOTE-07): the live GI pressure DEVELOPMENT authority runs the ratified ``GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1``.

TEST-SIDE. What this file proves, and what it does not:

* the binding (``runtime_pressure_snapshot``) accepts exactly the committed, ratified, pinned snapshot and refuses every change of it by name -- a changed rate, a changed kernel, a LOW or HIGH test witness in its
  place, a rate that is not ``c x scale``, a changed id/status/digest, a region or ratification record that is not the pinned one -- with mutation controls that re-seal the record, so the refusal is the
  binding's own and not a side effect of a broken digest;
* the grant (version 2) binds that snapshot, its configuration digest, the certified lineage, both GI cases, pressure only, development only, and version 1 is untouched and still registered;
* an environment that names the promoted snapshot and does not bind runs NOTHING: no session, no fallback to the older point;
* on the REAL page (Streamlit ``AppTest``), the displayed pressures at every committed minute of the faculty-reviewed FR-B, FR-C, FR-E and FR-G encounters EQUAL the human-reviewed ``CENTER_REFERENCE`` trajectory,
  under the existing whole-mmHg display contract. That is the criterion. The older authority's trajectory is NOT the reference and is never compared to;
* the artifact of a promoted run names grant version 2 and the promoted snapshot, verifies, and replays from itself alone; an artifact of the older point still verifies and replays under ITS grant, and no
  artifact is rewritten.

What it does not do: it does not recalibrate anything, it does not touch ``LOW`` or ``HIGH``, it does not "fix" the monitored limitation ``GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE``, and it says nothing about clinical truth.
The stop, reopen and pre-commit-abort behaviour under the promoted configuration is ``test_phase3_pressure_promotion_stop.py`` (the same page proofs as ``test_phase3_stop_page.py``).
"""
import copy
import json
import tempfile
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_pressure_grant as grants
import runtime_pressure_snapshot as ps
import runtime_shadow as rs
import runtime_shadow_families as rsf
import test_gi_frg_crystalloid_analysis as fa
import test_phase3_pair_page as page
import test_phase3_pressure_grant as v1_grant_tests

ROOT = Path(__file__).resolve().parent
V1 = "gi_pressure_committed"
V2 = ps.SNAPSHOT_ID
RECORD_PATH = ROOT / ps.RECORD_FILE
REGION_PATH = ROOT / ps.REGION_FILE
RECORD = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
REGION = json.loads(REGION_PATH.read_text(encoding="utf-8"))
#: The ratified CENTER_REFERENCE binding as the assignment states it, typed here independently of the code AND of the record: three copies must agree.
RATIFIED = {"bleed_rate_ml_eq_per_min": 8.970853509, "c_rate_over_scale_per_min": 0.003326066, "preload_scale_ml_eq": 2697.136369656, "arrival_position": 0.5,
            "kernel_e": 0.213115961, "kernel_s": 0.835, "kernel_tau_min": 60.624}
REVIEWED = ("FR-B", "FR-C", "FR-E", "FR-G")


def _sealed(record, **changes):
    """A copy of the committed record with ``changes`` applied and its own digest re-sealed: only the binding's content checks can refuse it."""
    body = copy.deepcopy(record)
    for path, value in changes.items():
        node = body
        keys = path.split("/")
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = value
    body["record_digest"] = ps._whole_record_digest(body)
    return body


def _refusal(record, **kwargs):
    raw = json.dumps(record, sort_keys=True).encode("utf-8")
    with pytest.raises(ps.PressureBindingError) as refused:
        ps.bind(record=record, raw=raw, **kwargs)
    return set(refused.value.reasons)


# -- P3-378/380: the binding ---------------------------------------------------------------------------------------------------------------------------------

def test_b1_the_binding_is_the_ratified_center_reference_three_times_over():
    cfg = ps.bind()
    assert ps.configuration_is_pinned(cfg) and cfg.snapshot_id == V2 and cfg.configuration_digest == ps.CONFIGURATION_DIGEST == grants.CONFIGURATION_DIGEST_V2
    in_code = {"bleed_rate_ml_eq_per_min": cfg.bleed_rate_ml_eq_per_min, "c_rate_over_scale_per_min": cfg.c_rate_over_scale_per_min, "preload_scale_ml_eq": cfg.preload_scale_ml_eq,
               "arrival_position": cfg.arrival_position, "kernel_e": cfg.kernel_e, "kernel_s": cfg.kernel_s, "kernel_tau_min": cfg.kernel_tau_min}
    centre = REGION["witnesses"]["CENTER_REFERENCE"]["binding"]
    in_record = RECORD["binding"]
    assert in_record == centre, "the snapshot record copied the region's CENTER_REFERENCE binding (copied, not recomputed)"
    from_the_record = {"bleed_rate_ml_eq_per_min": in_record["bleed_rate_ml_eq_per_min"], "c_rate_over_scale_per_min": in_record["c_rate_over_scale_per_min"],
                       "preload_scale_ml_eq": in_record["preload_scale_ml_eq"], "arrival_position": in_record["arrival_position"], "kernel_e": in_record["crystalloid_kernel"]["e"],
                       "kernel_s": in_record["crystalloid_kernel"]["s"], "kernel_tau_min": in_record["crystalloid_kernel"]["tau_min"]}
    assert in_code == RATIFIED == from_the_record
    assert abs(cfg.bleed_rate_ml_eq_per_min - cfg.c_rate_over_scale_per_min * cfg.preload_scale_ml_eq) <= 1e-5 * cfg.bleed_rate_ml_eq_per_min, "the rate is c x scale, never a rate on its own"
    assert RECORD["status"] == "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS" and RECORD["selected_witness"] == "CENTER_REFERENCE"


def test_b2_the_binding_refuses_every_change_of_the_snapshot_by_name_even_when_the_record_is_resealed():
    bound = RECORD["binding"]
    cases = {
        "the rate alone": (_sealed(RECORD, **{"binding/bleed_rate_ml_eq_per_min": bound["bleed_rate_ml_eq_per_min"] * 1.2}), {ps.MODIFIED_PARAMETER, ps.RATE_WITHOUT_SCALE}),
        "the scale alone": (_sealed(RECORD, **{"binding/preload_scale_ml_eq": bound["preload_scale_ml_eq"] * 1.1}), {ps.MODIFIED_PARAMETER, ps.RATE_WITHOUT_SCALE}),
        "the kernel without the snapshot's identity": (_sealed(RECORD, **{"binding/crystalloid_kernel/e": 0.30}), {ps.MODIFIED_PARAMETER}),
        "the kernel time constant": (_sealed(RECORD, **{"binding/crystalloid_kernel/tau_min": 30.0}), {ps.MODIFIED_PARAMETER}),
        "the arrival position": (_sealed(RECORD, **{"binding/arrival_position": 0.6}), {ps.MODIFIED_PARAMETER}),
        "another snapshot id": (_sealed(RECORD, snapshot_id="GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V2"), {ps.WRONG_SNAPSHOT_ID}),
        "another witness selected": (_sealed(RECORD, selected_witness="LOW"), {ps.WRONG_SNAPSHOT_ID}),
        "another status": (_sealed(RECORD, status="PROPOSED"), {ps.WRONG_STATUS}),
        "a binding with a missing member": (_sealed(RECORD, **{"binding/crystalloid_kernel": {"e": 0.213115961}}), {ps.NOT_A_RECORD}),
        "a non-numeric member": (_sealed(RECORD, **{"binding/arrival_position": "0.5"}), {ps.NOT_A_RECORD}),
    }
    for label, (record, expected) in cases.items():
        assert expected <= _refusal(record), label
    # the LOW and HIGH test witnesses, each in the place of the ratified point: refused as a witness (and as a modified parameter)
    for name in ("LOW", "HIGH"):
        witness = RECORD["witnesses_test_only"][name]["binding"]
        reasons = _refusal(_sealed(RECORD, binding=copy.deepcopy(witness)))
        assert ps.WITNESS_SUBSTITUTED in reasons and ps.MODIFIED_PARAMETER in reasons, (name, reasons)


def test_b3_a_forged_digest_a_different_byte_stream_a_foreign_region_or_ratification_and_an_unreadable_root_are_refused(tmp_path):
    forged = copy.deepcopy(RECORD)
    forged["record_digest"] = "0" * 64
    assert ps.WRONG_DIGEST in _refusal(forged)
    other_bytes = json.dumps(RECORD, sort_keys=True).encode("utf-8") + b" "
    with pytest.raises(ps.PressureBindingError) as refused:
        ps.bind(record=copy.deepcopy(RECORD), raw=other_bytes)
    assert ps.WRONG_DIGEST in refused.value.reasons
    foreign_region = copy.deepcopy(REGION)
    foreign_region["witnesses"]["CENTER_REFERENCE"]["binding"]["bleed_rate_ml_eq_per_min"] = 7.0
    assert ps.REGION_MISMATCH in _refusal(RECORD, region=foreign_region)
    with pytest.raises(ps.PressureBindingError) as refused:
        ps.bind(root=str(tmp_path))                                                    # no record under this root
    assert list(refused.value.reasons) == [ps.UNREADABLE]
    root = tmp_path / "copy"
    for name in (ps.RECORD_FILE, ps.RATIFICATION_FILE, ps.REGION_FILE):
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes((ROOT / name).read_bytes())
    assert ps.configuration_is_pinned(ps.bind(root=str(root))), "a faithful copy of the three records binds"
    (root / ps.RATIFICATION_FILE).write_bytes((ROOT / ps.RATIFICATION_FILE).read_bytes() + b"\n")
    with pytest.raises(ps.PressureBindingError) as refused:
        ps.bind(root=str(root))
    assert ps.NOT_RATIFIED in refused.value.reasons, "one byte of difference in the ratification record is not THE ratification"
    (root / ps.RATIFICATION_FILE).write_bytes((ROOT / ps.RATIFICATION_FILE).read_bytes())
    (root / ps.REGION_FILE).write_bytes((ROOT / ps.REGION_FILE).read_bytes() + b"\n")
    with pytest.raises(ps.PressureBindingError) as refused:
        ps.bind(root=str(root))
    assert ps.REGION_MISMATCH in refused.value.reasons, "one byte of difference in the region record is not THE region record"


def test_b4_a_hand_built_or_altered_configuration_is_never_trusted_by_a_consumer():
    import dataclasses
    cfg = ps.bind()
    for change in ({"bleed_rate_ml_eq_per_min": 9.0}, {"preload_scale_ml_eq": 2000.0}, {"kernel_e": 0.5}, {"kernel_tau_min": 10.0}, {"arrival_position": 0.4}, {"configuration_digest": "0" * 64}):
        assert not ps.configuration_is_pinned(dataclasses.replace(cfg, **change)), change
    assert not ps.configuration_is_pinned(None) and not ps.configuration_is_pinned(dict(dataclasses.asdict(cfg)))
    forced = dataclasses.replace(cfg)
    object.__setattr__(forced, "kernel_s", 0.5)                                        # Python lets a determined caller force a frozen field: no consumer trusts the object
    assert not ps.configuration_is_pinned(forced)
    with pytest.raises(ps.PressureBindingError):
        ps.apply_profile(rsf._bundle_profile("committed"), forced)
    with pytest.raises(ps.PressureBindingError):
        rsf.GiHaemorrhageAdapter.configured(forced)


def test_b5_only_the_exact_snapshot_id_asks_for_the_binding_and_a_named_snapshot_that_does_not_bind_has_no_fallback(monkeypatch):
    for environ in ({}, {ps.SNAPSHOT_FLAG: ""}, {ps.SNAPSHOT_FLAG: V1}, {ps.SNAPSHOT_FLAG: "gi_joint_pressure_development_snapshot_v1"}, {ps.SNAPSHOT_FLAG: V2.lower()}, {ps.SNAPSHOT_FLAG: V2 + "x"}):
        assert ps.requested(environ) is False and ps.configuration_for(environ) is None, environ
    assert ps.requested({ps.SNAPSHOT_FLAG: f"  {V2}  "}) is True and ps.configuration_is_pinned(ps.configuration_for({ps.SNAPSHOT_FLAG: V2}))
    monkeypatch.setattr(ps, "RECORD_FILE", "docs/revision/does_not_exist.json")
    with pytest.raises(ps.PressureBindingError):
        ps.configuration_for({ps.SNAPSHOT_FLAG: V2})                                   # named and unbindable: it raises -- it does not return the older point or None


def test_b6_applying_the_configuration_changes_exactly_the_six_magnitudes_and_nothing_else():
    cfg = ps.bind()
    older = rsf.GiHaemorrhageAdapter()
    promoted = rsf.GiHaemorrhageAdapter.configured(cfg)
    point = rsf.COMMITTED
    before, after = older.profile(point), promoted.profile(point)
    import dataclasses
    changed = {field.name for field in dataclasses.fields(before) if getattr(before, field.name) != getattr(after, field.name)}
    # The older live configuration already ran the arrival position 0.5 and the profile's other magnitudes: of the six coordinates, FIVE differ (the scale here, the rate and the kernel below).
    assert changed == {"preload_curve_scale_ml"}, changed
    assert (before.preload_curve_scale_ml, before.arrival_preload_fraction) == (833.3333333333334, 0.5), "the older live point, as the V1 registry records it"
    assert after.preload_curve_scale_ml == RATIFIED["preload_scale_ml_eq"] and after.arrival_preload_fraction == RATIFIED["arrival_position"]
    state = None
    w_before, w_after = older.writers("gi_bleed_57m", point, state), promoted.writers("gi_bleed_57m", point, state)
    assert len(w_before) == len(w_after)
    from clinical_core.modules.gi_haemorrhage import GIHaemorrhage
    for left, right in zip(w_before, w_after):
        if isinstance(left, GIHaemorrhage):
            assert left.blood_loss_ml_per_min == 2.5 and right.blood_loss_ml_per_min == RATIFIED["bleed_rate_ml_eq_per_min"]
            assert dataclasses.replace(right, blood_loss_ml_per_min=left.blood_loss_ml_per_min) == left, "only the rate of the haemorrhage changed"
        else:
            assert left == right
    from clinical_core.interventions.fluids import Crystalloid
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = pilot_acceptance.Encounter("gi_bleed_57m")
        encounter.order("Give 1 litre of normal saline over 15 minutes. Transfuse 1 unit of packed red blood cells. Start a proton pump inhibitor.")
    mirrored = list(encounter.shadow.runner.mirrored)
    assert {"fluid", "blood"} <= {event.kind for event in mirrored}, [event.kind for event in mirrored]
    c_before, _ = older.interventions(mirrored, None)
    c_after, _ = promoted.interventions(mirrored, None)
    assert len(c_before) == len(c_after) and any(isinstance(item, Crystalloid) for item in c_before)
    for left, right in zip(c_before, c_after):
        if isinstance(left, Crystalloid):
            assert (left.effective_ml_per_ml, left.transient_share, left.leak_tau_min) == (0.125, 0.6, 30.0), "the older live kernel"
            assert (right.effective_ml_per_ml, right.transient_share, right.leak_tau_min) == (RATIFIED["kernel_e"], RATIFIED["kernel_s"], RATIFIED["kernel_tau_min"])
            assert dataclasses.replace(right, effective_ml_per_ml=left.effective_ml_per_ml, transient_share=left.transient_share, leak_tau_min=left.leak_tau_min) == left
        else:
            assert left == right, "red cells, oxygen, the PPI and endoscopy are untouched"


def test_b7_the_session_opens_with_the_promoted_adapter_or_opens_nothing_and_never_the_older_point(monkeypatch):
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    environ = {rs.FLAG: rs.MODE_SHADOW_COMPARE, ps.SNAPSHOT_FLAG: V2}
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = pilot_acceptance.Encounter("gi_bleed_57m")
        arrival = copy.deepcopy(encounter.state)
    session = rs.ShadowSession.start(arrival, environ=environ)
    assert session is not None and session.runner is not None and not [f for f in session.failures if f.exception == rs.PRESSURE_SNAPSHOT_NOT_BOUND]
    assert session.runner.adapter.pressure_configuration is not None and session.runner.adapter.pressure_configuration.snapshot_id == V2
    older = rs.ShadowSession.start(arrival, environ={rs.FLAG: rs.MODE_SHADOW_COMPARE, ps.SNAPSHOT_FLAG: V1})
    assert older is not None and older.runner.adapter.pressure_configuration is None, "naming the older point still runs the older point, unchanged"
    monkeypatch.setattr(ps, "RECORD_FILE", "docs/revision/does_not_exist.json")
    refused = rs.ShadowSession.start(arrival, environ=environ)
    assert refused is not None and refused.runner is None and refused.ensemble is None, "named and unbindable: no runner"
    assert [f.exception for f in refused.failures if f.exception == rs.PRESSURE_SNAPSHOT_NOT_BOUND], [f.exception for f in refused.failures]


# -- P3-379: the grant ---------------------------------------------------------------------------------------------------------------------------------------

def test_g1_grant_version_2_binds_the_snapshot_the_configuration_the_lineage_the_cases_the_domain_and_the_environment():
    grant = grants.GRANT_V2
    assert grant["grant_id"] == "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2" and grant["grant_version"] == 2 and grant["kind"] == "FACULTY_GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT"
    assert grant["status"] == "ACTIVE_FOR_DEVELOPMENT_EXPERIMENT" and grant["authority_mode"] == "PRESSURE_ONLY" and grant["purpose"] == "DEVELOPMENT_AUTHORITY_EXPERIMENT_ONLY"
    assert grant["fingerprint"] == grants.GRANT_FINGERPRINT_V2 == grants.fingerprint_of(grant)
    assert grant["pressure_snapshot"]["id"] == V2 and grant["pressure_snapshot"]["value_digest"] == ra.APPROVED_POINT_DIGESTS[V2] == grants.PRESSURE_VALUE_DIGEST_V2
    assert grant["pressure_snapshot"].get("configuration_digest") == ps.CONFIGURATION_DIGEST
    assert tuple(grant["cases"]) == ("gi_bleed_57m", "gi_bleed_72f") and grant["family"] == "gi_bleed" and tuple(grant["environments"]) == ("development",) and tuple(grant["domain"]) == ("sbp", "dbp", "map")
    assert grant["core_lineage"]["version_id"] == rs.CORE_LINEAGE[-1].version_id and grant["core_lineage"]["digest"] == rs.CORE_LINEAGE[-1].digest, "no successor core: the lineage is the certified one"
    assert grant["window"]["max_minute"] == 240 and grant["failure_policy"] == grants.GRANT["failure_policy"], "the effective-stop semantics are the version-1 ones, unchanged"
    assert grant["collapse_boundary"] == grants.GRANT["collapse_boundary"] and list(grant["excluded_domains"]) == list(grants.EXCLUDED_DOMAINS)
    assert grant["issued_on"] == "2026-11-16" and "FD-PROMOTE" in grant["decision_reference"]


def test_g2_version_1_is_untouched_both_are_registered_and_each_snapshot_belongs_to_exactly_one_grant():
    assert grants.GRANT_FINGERPRINT == v1_grant_tests.PINNED_FINGERPRINT and grants.GRANT["grant_id"] == "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1" and grants.GRANT["pressure_snapshot"]["id"] == V1
    assert grants.REGISTERED_GRANTS == (grants.GRANT, grants.GRANT_V2) and grants.REAL_SNAPSHOT_IDS == (V1, V2)
    assert grants.grant_for_snapshot(V1) is grants.GRANT and grants.grant_for_snapshot(V2) is grants.GRANT_V2 and grants.grant_for_snapshot("nothing") is None
    assert grants.registered_grant(grants.GRANT_ID_V2, grants.GRANT_FINGERPRINT_V2) is grants.GRANT_V2 and grants.registered_grant(grants.GRANT_ID_V2, grants.GRANT_FINGERPRINT) is None


def test_g3_each_grant_is_judged_against_its_own_snapshot_and_a_cross_version_pairing_is_refused():
    common = dict(case_id="gi_bleed_57m", environment="development", family="gi_bleed", lineage=rs.CORE_LINEAGE[-1])
    lineage = {"version_id": rs.CORE_LINEAGE[-1].version_id, "digest": rs.CORE_LINEAGE[-1].digest}
    ok_2 = grants.grant_problems(grants.GRANT_V2, snapshot_id=V2, **{**common, "lineage": lineage})
    ok_1 = grants.grant_problems(grants.GRANT, snapshot_id=V1, **{**common, "lineage": lineage})
    assert ok_2 == [] and ok_1 == [], (ok_2, ok_1)
    assert grants.grant_problems(grants.GRANT_V2, snapshot_id=V1, **{**common, "lineage": lineage}), "version 2 does not permit the older snapshot"
    assert grants.grant_problems(grants.GRANT, snapshot_id=V2, **{**common, "lineage": lineage}), "version 1 does not permit the ratified snapshot"
    tampered = {**dict(grants.GRANT_V2), "pressure_snapshot": {**dict(grants.GRANT_V2["pressure_snapshot"]), "configuration_digest": "0" * 64}}
    assert grants.grant_problems(tampered, snapshot_id=V2, **{**common, "lineage": lineage}), "a grant that names another configuration is not the registered one (its fingerprint no longer matches)"
    for field, value in (("cases", ("gi_bleed_57m", "gi_bleed_72f", "acs_stemi_60m")), ("environments", ("development", "production")), ("domain", ("sbp", "dbp", "map", "mental_status"))):
        altered = {**dict(grants.GRANT_V2), field: value}
        assert grants.grant_problems(altered, snapshot_id=V2, **{**common, "lineage": lineage}), field


def test_g4_the_registry_holds_the_promoted_point_complete_with_its_rate_and_kernel_and_it_permits_only_what_the_grant_permits():
    entry = ra.APPROVED_SNAPSHOTS[V2]
    assert ra.snapshot_is_wellformed(entry) == (True, ()) and ra.approved_values_match(V2, entry)
    assert entry["parameters"]["preload_curve_scale_ml"] == RATIFIED["preload_scale_ml_eq"] and entry["parameters"]["arrival_preload_fraction"] == RATIFIED["arrival_position"]
    scenario = entry["scenario_parameters"]
    assert scenario["bleed_rate_ml_eq_per_min"] == RATIFIED["bleed_rate_ml_eq_per_min"] and (scenario["crystalloid_effective_ml_per_ml"], scenario["crystalloid_transient_share"], scenario["crystalloid_leak_tau_min"]) == (
        RATIFIED["kernel_e"], RATIFIED["kernel_s"], RATIFIED["kernel_tau_min"])
    assert ra.approved_snapshot(V2, environment="development", family="gi_bleed", case_id="gi_bleed_57m", domain=("sbp", "dbp", "map")) is not None
    for outside in (dict(environment="production"), dict(environment="staging"), dict(family="acs"), dict(case_id="acs_stemi_60m"), dict(domain=("sbp", "dbp", "map", "mental_status")), dict(domain=("hr",))):
        context = dict(environment="development", family="gi_bleed", case_id="gi_bleed_57m", domain=("sbp", "dbp", "map")) | outside
        assert ra.approved_snapshot(V2, **context) is None, outside
    assert "LOW" not in json.dumps(sorted(ra.APPROVED_SNAPSHOTS)) and "HIGH" not in json.dumps(sorted(ra.APPROVED_SNAPSHOTS)), "no test witness is registered"


def test_g5_the_gate_grants_the_promoted_snapshot_only_with_its_own_grant_and_never_through_a_changed_value(monkeypatch):
    import runtime_authority_store as store
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        state = copy.deepcopy(pilot_acceptance.Encounter("gi_bleed_57m").state)
    directory = tempfile.mkdtemp(prefix="promotion-gate-")
    real = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: V2, ra.ENVIRONMENT_FLAG: "development", store.STORE_FLAG: directory}
    decision = ra.gate(state, environ=real, unsupported=())
    assert decision.granted and decision.snapshot_id == V2 and decision.conditions["explicit_development_grant"] and decision.conditions["approved_snapshot"], decision.reasons
    for wrong in ({ra.ENVIRONMENT_FLAG: "production"}, {ra.SNAPSHOT_FLAG: "GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1_LOW"}, {ra.SNAPSHOT_FLAG: ""}, {ra.AUTHORITY_FLAG: ra.MODE_SHADOW_COMPARE}):
        assert not ra.gate(state, environ={**real, **wrong}, unsupported=()).granted, wrong
    # an approval that is present while its grant is not: the gate refuses (a snapshot with no grant is never enough)
    monkeypatch.setattr(grants, "REGISTERED_GRANTS", (grants.GRANT,))
    assert not ra.gate(state, environ=real, unsupported=()).granted, "the promoted snapshot without its version-2 grant is refused"


# -- P3-382: equality with the human-reviewed CENTER_REFERENCE trajectories, on the real page -----------------------------------------------------------------

def _candidate(scenario):
    return {int(point["minute"]): (int(point["sbp"]), int(point["dbp"]), int(point["map"]))
            for point in REGION["candidate_trajectories"][scenario]["candidates"]["CENTER_REFERENCE"]["pressures"]}


def _run_on_the_page(scenario, snapshot_id):
    """The faculty-reviewed encounter of ``scenario`` played through the real page, in the authorized development configuration of ``snapshot_id``."""
    item = fa.reviewed_item(scenario)
    case, _orders = fa.reviewed_orders(scenario)
    directory = tempfile.mkdtemp(prefix="promotion-page-")
    patch = pytest.MonkeyPatch()
    try:
        patch.setattr(page, "AUTHORITY_SNAPSHOT_ID", snapshot_id)
        at = page._open(patch, case, shadow=True, dry=False, authority=directory)
        seen = {}

        def read():
            state = at.session_state["state"]
            observable = state["observable"]
            seen[int(round(float(state["sim_time"])))] = (observable.get("sbp"), observable.get("dbp"), observable.get("map"))
        read()
        for kind, text in item["script"]:
            if kind == "order":
                page._order(at, text)
            elif kind == "question":
                page._ask(at)
            else:
                page._examine(at)
            read()
        site = at.session_state.get(ra.SITE_KEY)
        return {"scenario": scenario, "case": case, "seen": seen, "site": site, "artifact": None if site is None else site.artifact(), "at": at, "directory": directory}
    finally:
        patch.undo()


@pytest.fixture(scope="module")
def promoted_runs():
    return {scenario: _run_on_the_page(scenario, V2) for scenario in REVIEWED}


@pytest.fixture(scope="module")
def older_run():
    return _run_on_the_page("FR-B", V1)


@pytest.mark.parametrize("scenario", REVIEWED)
def test_e1_the_live_authority_reproduces_the_human_reviewed_center_reference_pressures_at_every_committed_minute(promoted_runs, scenario):
    run = promoted_runs[scenario]
    site, seen = run["site"], run["seen"]
    candidate = _candidate(scenario)
    assert site is not None and site.snapshot_id == V2 and site.grant["grant_id"] == grants.GRANT_ID_V2 and site.minutes_committed, "the page ran the promoted authority"
    committed = sorted(site.minutes_committed)
    assert set(committed) <= set(candidate), (scenario, committed, sorted(candidate))
    for minute in committed:
        assert minute in seen, (scenario, minute, "the displayed state at every committed minute was read")
        assert seen[minute][:2] == candidate[minute][:2], (scenario, minute, "SBP/DBP displayed", seen[minute], "CENTER_REFERENCE", candidate[minute])
        if seen[minute][2] is not None:
            assert seen[minute][2] == candidate[minute][2], (scenario, minute, "MAP (derived) displayed", seen[minute], candidate[minute])
    assert set(candidate) <= set(committed) or not REGION["candidate_trajectories"][scenario]["candidates"]["CENTER_REFERENCE"]["complete_to_the_last_committed_minute"], (scenario, sorted(candidate), committed)
    expected_stop = REGION["candidate_trajectories"][scenario]["candidates"]["CENTER_REFERENCE"]["experiment_would_stop"]
    assert bool(site.halted) == bool(expected_stop), (scenario, site.halted, site.halt_reason, expected_stop)


def test_e2_no_run_was_compared_with_or_fell_back_to_the_older_authority(promoted_runs):
    for scenario, run in promoted_runs.items():
        artifact = run["artifact"]
        assert artifact["snapshot_id"] == V2 and artifact["grant"]["grant_id"] == grants.GRANT_ID_V2 and artifact["grant"]["fingerprint"] == grants.GRANT_FINGERPRINT_V2, scenario
        assert all(record["grant_id"] == grants.GRANT_ID_V2 and record["grant_fingerprint"] == grants.GRANT_FINGERPRINT_V2 and record["snapshot_id"] == V2 for record in artifact["minutes"]), scenario
        assert artifact["phase3_versions"]["parameter_snapshot"] == ps.RUNTIME_SNAPSHOT_ID, (scenario, "the shadow layer reports the promoted point and nothing else")
        assert V1 not in ra.canonical(artifact), (scenario, "no trace of the older approved id in a promoted run's artifact")
        # adversarial review, finding 4: the provenance INSIDE the run names the promoted snapshot too -- the captured input of the artifact and of every minute that carries one (never the committed default
        # profile's label), and the overlay names the pressure snapshot it was bound to
        assert artifact["replay_input"]["versions"]["parameter_snapshot"] == ps.RUNTIME_SNAPSHOT_ID, scenario
        assert all(record["replay_input"]["versions"]["parameter_snapshot"] == ps.RUNTIME_SNAPSHOT_ID for record in artifact["minutes"] if record.get("replay_input")), scenario
        assert artifact["consciousness_overlay"]["replay_input"]["versions"]["parameter_snapshot"].endswith("+" + ps.RUNTIME_SNAPSHOT_ID), scenario


# -- P3-381: artifacts and replay ----------------------------------------------------------------------------------------------------------------------------

def test_r1_a_promoted_artifact_verifies_is_labelled_real_names_version_2_and_replays_from_itself_alone(promoted_runs):
    for scenario, run in promoted_runs.items():
        artifact = run["artifact"]
        verdict = ra.verify_artifact(artifact)
        assert verdict["complete"] and verdict["digest_matches"] and verdict["claims_are_honest"] and verdict["grant_is_the_registered_one"] and verdict["artifact_class"] == ra.REAL_PRESSURE_LABEL, (scenario, verdict)
        replay = ra.replay_site_artifact(artifact)
        assert replay["reproduces"] and replay["overlay_replay"]["reproduces"] and replay["halt_reason_replay"]["reproduces"] and replay["covers_every_committed_minute"], (scenario, replay)
        assert artifact["authority_mode"] == "PRESSURE_ONLY" and artifact["excluded_domains"] == list(grants.EXCLUDED_DOMAINS)


def test_r2_an_artifact_of_the_older_point_still_verifies_and_replays_under_its_own_grant_and_is_not_rewritten(older_run):
    artifact = older_run["artifact"]
    assert artifact["snapshot_id"] == V1 and artifact["grant"]["grant_id"] == grants.GRANT_ID and artifact["grant"]["fingerprint"] == grants.GRANT_FINGERPRINT == v1_grant_tests.PINNED_FINGERPRINT
    verdict = ra.verify_artifact(artifact)
    assert verdict["complete"] and verdict["grant_is_the_registered_one"], verdict
    replay = ra.replay_site_artifact(artifact)
    assert replay["reproduces"] and replay["overlay_replay"]["reproduces"], replay
    assert artifact["phase3_versions"]["parameter_snapshot"] == rs.PARAMETER_SNAPSHOT_ID, "the older run reports the committed default profile, exactly as before"
    frozen = ra.canonical(artifact)
    ra.verify_artifact(artifact)
    ra.replay_site_artifact(artifact)
    assert ra.canonical(artifact) == frozen, "verifying and replaying read the artifact; they never write it"


def test_r3_an_artifact_cannot_be_read_under_the_other_grant_even_when_it_is_resealed(promoted_runs):
    promoted = json.loads(ra.canonical(promoted_runs["FR-B"]["artifact"]))                 # plain data: a mutation control must not touch the run's own artifact

    def resealed(body):
        body = {key: value for key, value in body.items() if key != "artifact_digest"}
        return {**body, "artifact_digest": ra.digest_of(body)}
    older_grant = json.loads(ra.canonical(grants.GRANT))
    swapped = copy.deepcopy(promoted)
    swapped["grant"] = {**dict(swapped["grant"]), "grant_id": older_grant["grant_id"], "fingerprint": older_grant["fingerprint"]}
    for record in swapped["minutes"]:
        record["grant_id"], record["grant_fingerprint"] = older_grant["grant_id"], older_grant["fingerprint"]
    verdict = ra.verify_artifact(resealed(swapped))
    assert not verdict["complete"], "a version-2 run presented as a version-1 run does not verify"
    mixed = copy.deepcopy(promoted)
    mixed["snapshot_id"] = V1
    assert not ra.verify_artifact(resealed(mixed))["complete"], "the promoted grant with the older snapshot id does not verify"
    bare = copy.deepcopy(promoted)
    bare["grant"] = {**dict(bare["grant"]), "fingerprint": "0" * 64}
    assert not ra.verify_artifact(resealed(bare))["grant_is_the_registered_one"], "a fingerprint that is not a registered one is not a registered grant"


def test_r4_the_ratified_records_are_exactly_the_pinned_bytes_so_the_promotion_rewrote_none_of_them():
    """The promotion ADDS configuration and records; it edits none of the records it stands on. Their file hashes and digests are pinned in the binding, so a rewrite of any of them (here: the snapshot record,
    its ratification and the region record; the human re-review record by its digest) cannot go unnoticed -- the binding would refuse, and this test names the pin."""
    import hashlib
    assert hashlib.sha256(RECORD_PATH.read_bytes()).hexdigest() == ps.RECORD_FILE_SHA256 and RECORD["record_digest"] == ps.RECORD_DIGEST
    assert hashlib.sha256(REGION_PATH.read_bytes()).hexdigest() == ps.REGION_FILE_SHA256 and REGION["record_digest"] == ps.REGION_DIGEST
    ratification = ROOT / ps.RATIFICATION_FILE
    assert hashlib.sha256(ratification.read_bytes()).hexdigest() == ps.RATIFICATION_FILE_SHA256 and json.loads(ratification.read_text(encoding="utf-8"))["record_digest"] == ps.RATIFICATION_DIGEST
    human = json.loads((ROOT / "docs" / "revision" / "PHASE3_HUMAN_FACULTY_REREVIEW.json").read_text(encoding="utf-8"))
    assert human["record_digest"] == ps.HUMAN_RECORD_DIGEST


# -- the adversarial review: values, not only labels; one run, one configuration ---------------------------------------------------------------------------------------

def _plain(value):
    return json.loads(ra.canonical(value))


def _relabelled(artifact, grant, snapshot_id):
    """A genuine artifact with every LABEL of the snapshot and the grant consistently replaced and its digest re-sealed (the values it carried stay what they were)."""
    body = _plain(artifact)
    body["snapshot_id"] = snapshot_id
    body["snapshot"]["id"] = snapshot_id
    body["grant"] = _plain(grants.summary(grant))
    for record in body["minutes"]:
        record["grant_id"], record["grant_fingerprint"] = grant["grant_id"], grant["fingerprint"]
        if "snapshot_id" in record:
            record["snapshot_id"] = snapshot_id
    body.pop("artifact_digest", None)
    return {**body, "artifact_digest": ra.digest_of(body)}


def test_r5_an_artifact_relabelled_consistently_as_the_other_version_does_not_verify_because_the_values_it_carried_are_not_that_snapshots(promoted_runs, older_run):
    forged_as_v2 = _relabelled(older_run["artifact"], grants.GRANT_V2, V2)
    forged_as_v1 = _relabelled(promoted_runs["FR-B"]["artifact"], grants.GRANT, V1)
    for label, forged in (("older run presented as promoted", forged_as_v2), ("promoted run presented as older", forged_as_v1)):
        verdict = ra.verify_artifact(forged)
        assert verdict["digest_matches"] and not verdict["complete"], label
        assert any("does not carry the values of the snapshot its grant binds" in problem for problem in verdict["real_claims_problems"]), (label, verdict["real_claims_problems"])
    import runtime_authority_pair as pair
    replay = pair.replay_overlay_artifact(forged_as_v1, V1)
    assert not replay["reproduces"] and replay["mismatches"], "the overlay of a promoted run cannot be replayed as the older version's"


def test_r6_the_helper_holds_each_snapshot_to_its_own_six_values_and_a_test_only_id_to_none(promoted_runs, older_run):
    import runtime_authority_pair as pair
    older_scenario, promoted_scenario = older_run["artifact"]["replay_input"]["scenario"], promoted_runs["FR-B"]["artifact"]["replay_input"]["scenario"]
    assert pair.snapshot_values(V1) == pair.OLDER_POINT and dict(pair.snapshot_values(V2)) == ps.bind().values() and pair.snapshot_values("a test-only point") is None
    assert pair.scenario_has_the_values(older_scenario, pair.OLDER_POINT) and not pair.scenario_has_the_values(older_scenario, pair.snapshot_values(V2))
    assert pair.scenario_has_the_values(promoted_scenario, pair.snapshot_values(V2)) and not pair.scenario_has_the_values(promoted_scenario, pair.OLDER_POINT)
    assert pair.scenario_has_the_values(None, pair.OLDER_POINT) is False, "no scenario is not a scenario that carries the values"
    for change in ({"bleed_rate_ml_eq_per_min": 9.0}, {"preload_scale_ml_eq": 2000.0}, {"kernel_e": 0.5}, {"kernel_s": 0.9}, {"kernel_tau_min": 10.0}, {"arrival_position": 0.4}):
        assert not pair.scenario_has_the_values(promoted_scenario, {**pair.snapshot_values(V2), **change}), change


def test_r7_the_overlay_of_a_promoted_run_is_replayable_only_when_it_names_the_pinned_configuration_and_its_scenario_is_at_it(promoted_runs, older_run):
    import runtime_authority_pair as pair
    artifact = _plain(promoted_runs["FR-B"]["artifact"])
    assert pair.replay_overlay_artifact(artifact, V2)["reproduces"] is True
    tampered = copy.deepcopy(artifact)
    tampered["consciousness_overlay"]["snapshot"]["pressure_configuration"]["values"]["bleed_rate_ml_eq_per_min"] = 2.5
    replay = pair.replay_overlay_artifact(tampered, V2)
    assert replay["snapshot_matches"] is False and replay["reproduces"] is False, "a summary that names another configuration is not the pinned one"
    cfg = ps.bind()
    assert pair.scenario_is_at_the_configuration(promoted_runs["FR-B"]["artifact"]["consciousness_overlay"]["replay_input"]["scenario"], cfg) is True
    assert pair.scenario_is_at_the_configuration(older_run["artifact"]["replay_input"]["scenario"], cfg) is False, "a scenario of the older point is not at the promoted configuration"
    assert pair.scenario_is_at_the_configuration(promoted_runs["FR-B"]["artifact"]["replay_input"]["scenario"], object()) is False, "an object that is not the pinned configuration is refused"


def _encounter_under(monkeypatch, snapshot_id, directory, case="gi_bleed_57m"):
    """A real encounter whose shadow session ran under ``snapshot_id``, with the arrival state and the actions of its first turn."""
    import pilot_acceptance
    import runtime_authority_store as store
    import runtime_shadow_evidence as ev
    environ = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: snapshot_id, ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE, store.STORE_FLAG: str(directory)}
    for name, value in environ.items():
        monkeypatch.setenv(name, value)
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        for name, value in environ.items():
            monkeypatch.setenv(name, value)
        encounter = pilot_acceptance.Encounter(case)
        arrival = copy.deepcopy(encounter.state)
        encounter.order("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.")
    return encounter, arrival, [dict(order) for order in encounter.entries[-1]["orders"]]


@pytest.mark.parametrize("session_runs,site_names", ((V1, V2), (V2, V1)))
def test_m1_a_session_that_ran_one_configuration_under_a_site_that_names_the_other_commits_nothing_and_says_why(monkeypatch, tmp_path, session_runs, site_names):
    import runtime_authority_session as se
    encounter, arrival, ran = _encounter_under(monkeypatch, session_runs, tmp_path / "store")
    environ = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: site_names, ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE, "MRS_PHASE3_AUTHORITY_STORE": str(tmp_path / "store")}
    site = ra.open_site(arrival, environ=environ)
    assert site is not None and site.snapshot_id == site_names
    assert site._configuration_mismatch(encounter.shadow), "the check is its own and it names the mix"
    site.minute(arrival, copy.deepcopy(encounter.state), encounter.shadow, ran, "t0")
    assert site.halted and not site.minutes_committed and site.halt_reason.startswith(ra.PRESSURE_CONFIGURATION_MISMATCH), site.halt_reason
    assert se.stop_class_of(site.halt_reason) == se.STOP_CONFIGURATION


def test_m2_the_run_is_refused_when_the_configuration_the_binding_would_run_is_not_the_one_the_grant_pins(monkeypatch, tmp_path):
    import pilot_acceptance
    import runtime_authority_store as store
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        state = copy.deepcopy(pilot_acceptance.Encounter("gi_bleed_57m").state)
    environ = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: V2, ra.ENVIRONMENT_FLAG: "development", store.STORE_FLAG: str(tmp_path / "store"), rs.FLAG: rs.MODE_SHADOW_COMPARE}
    assert ra.gate(state, environ=environ, unsupported=()).granted and ra.open_site(state, environ=environ) is not None and ra.binding_agrees_with_the_grant(grants.GRANT_V2)
    monkeypatch.setattr(ps, "CONFIGURATION_DIGEST", "0" * 64)                         # an in-place edit of the binding (its pins and its values together)
    decision = ra.gate(state, environ=environ, unsupported=())
    assert not decision.granted and not decision.conditions["explicit_development_grant"] and any(grants.CONFIGURATION_MISMATCH in reason for reason in decision.reasons), decision.reasons
    assert ra.open_site(state, environ=environ) is None, "no site opens on a binding the grant does not pin"
    assert not ra.binding_agrees_with_the_grant(grants.GRANT_V2) and ra.binding_agrees_with_the_grant(grants.GRANT), "the older grant does not depend on the binding"


def test_m3_when_the_session_could_not_bind_the_authority_record_says_so_and_still_commits_nothing(monkeypatch, tmp_path):
    encounter, arrival, ran = _encounter_under(monkeypatch, V1, tmp_path / "store")
    monkeypatch.setattr(ps, "RECORD_FILE", "docs/revision/does_not_exist.json")      # from here on, naming the promoted snapshot cannot bind
    for name, value in ((ra.SNAPSHOT_FLAG, V2), ):
        monkeypatch.setenv(name, value)
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        monkeypatch.setenv(ra.SNAPSHOT_FLAG, V2)
        unbound = pilot_acceptance.Encounter("gi_bleed_57m")
        unbound.order("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.")
    assert unbound.shadow.runner is None, "no corridor was opened"
    environ = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: V2, ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE, "MRS_PHASE3_AUTHORITY_STORE": str(tmp_path / "store")}
    site = ra.open_site(arrival, environ=environ)
    assert site is not None
    site.minute(arrival, copy.deepcopy(unbound.state), unbound.shadow, [dict(order) for order in unbound.entries[-1]["orders"]], "t0")
    assert site.halted and not site.minutes_committed
    assert ra.NO_COMMON_CANDIDATE in site.halt_reason and rs.PRESSURE_SNAPSHOT_NOT_BOUND in site.halt_reason, site.halt_reason
    assert "2.5" not in site.halt_reason and "833" not in site.halt_reason, "no older value is reported as if it had run"


def test_m4_the_names_the_binding_and_the_gate_use_are_the_same_strings():
    """Adversarial review, finding 9: the flag name and the runtime snapshot id are typed in more than one module; if they drifted, the session would silently run the older point."""
    import runtime_shadow_families as fam
    assert ps.SNAPSHOT_FLAG == ra.SNAPSHOT_FLAG and ps.SNAPSHOT_ID == grants.PRESSURE_SNAPSHOT_ID_V2 == ra.JOINT_PRESSURE_SNAPSHOT["id"]
    assert ps.RUNTIME_SNAPSHOT_ID == ra.JOINT_PRESSURE_SNAPSHOT["runtime_parameter_snapshot_id"] == rs.runtime_snapshot_for(V2)
    assert fam.GiHaemorrhageAdapter.configured(ps.bind()).snapshot().id == ps.RUNTIME_SNAPSHOT_ID
    assert rs.runtime_snapshot_for(V1) == rs.PARAMETER_SNAPSHOT_ID != ps.RUNTIME_SNAPSHOT_ID
