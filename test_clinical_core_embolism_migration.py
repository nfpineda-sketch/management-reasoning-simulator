"""P2Q-2: pulmonary_embolism_61m / _33f migrated in shadow with family writers on the closed common core.

The PE family writes the obstruction on the unsided P, the embolic gas exchange on G directly, and owns L with zero
generation; V is the underfilled LV's arrival position, never the plethoric IVC. These tests pin the writers and their
refusals, the case mapping, the no-double-count proof, the L authority under the fluid stress, direct G without the L_rev
credit, the common oxygen response, the P2P-2 drive on the PE course, D / lactate, collapse, the secondary case, the
verdict rule, the proof against the P2P-2 tree and the freeze.
"""
import hashlib
import json

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import embolism_migration as em
from clinical_core import embolism_reference as mr
from clinical_core import respiratory_drive as rd
from clinical_core import respiratory_mechanics as mc
from clinical_core import asthma_migration as sm
from clinical_core.integration import from_spec, step
from clinical_core.modules.pulmonary_edema import EdemaCongestion
from clinical_core.modules.pulmonary_embolism import EmbolicGasExchange, EmbolicLungWater, ObstructiveForwardFlow
from clinical_core.provenance import ProvenanceError
from clinical_core.state import Channel, CoreInvariantError, RhythmState

#: The P2Q-2 freeze: the cases and their mapping, the writers, the predeclared spans, probes and verdict rule, the proof
#: and every clinical_core source but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "6eabb72188b5aa9e8b6c0c17f9234fbf1ce5413cc01841a58a33ca79da797e6e"

#: P2S-2 changed the core (the common respiratory mechanics candidate, off by default) and two tuple files, proven against
#: the P2Q-2 files (respiratory_mechanics.proved): this package's guards read the tree as P2Q-2 left it (mc.chain,
#: mc.p2q2_sources); its record is unchanged and reproduced with P2S-2's new anchor input, at its reference 1, left out.
#: P2S-3 added files (the asthma family, its mapping and analysis) and two tuple entries, proven against the
#: P2S-2 files (asthma_migration.proved): this package's guards read the tree as P2S-2 left it (sm.chain,
#: sm.p2s2_sources).
_LIVE_SOURCES_P2S3 = bf.freeze_sources


def _LIVE_SOURCES_P2S2() -> dict:
    return sm.p2s2_sources(_LIVE_SOURCES_P2S3())


@pytest.fixture(autouse=True, scope="module")
def _p2q2_tree():
    with pytest.MonkeyPatch.context() as patch:
        mc.chain(patch)
        sm.chain(patch)
        patch.setattr(bf, "freeze_sources", lambda: mc.p2q2_sources(_LIVE_SOURCES_P2S2()))
        yield


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert all(relative in sources for relative in em.OWN) and em.REPORT not in sources
    assert set(em.TUPLES_ADDED["DOWNSTREAM_REPORTS"]) <= set(lactate_slice.DOWNSTREAM_REPORTS)
    assert set(em.TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    # The case mapping and the family writers stay in the P2G pack digest; the analysis and its report leave it.
    assert not {em.OWN[0], em.OWN[1]} & set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert em.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_no_common_file_changed_and_the_tuples_differ_only_by_p2q2_entries():
    assert set(em.REVERSAL) == set(em.CORE_AT_P2P2) == {"clinical_core/lactate_slice.py",
                                                        "clinical_core/decision_pack.py"}
    assert all(em.proofs().values())
    for relative, sha in em.CORE_AT_P2P2.items():
        assert hashlib.sha256(em.p2p2_bytes(relative)).hexdigest() == sha
    common = em.common_untouched()
    assert all(common.values()) and len(common) >= 100
    assert {"clinical_core/derived.py", "clinical_core/integration.py", "clinical_core/state.py",
            "clinical_core/collapse.py", "clinical_core/respiratory_drive.py"} <= set(common)
    proof = em.upstream_unchanged()
    assert proof["p2p2_freeze_digest"] and proof["p2p2_record"]


@pytest.mark.parametrize("old, new", [
    ('"clinical_core/embolism_migration_report.py")', '"clinical_core/embolism_migration_report.py", "x.py")'),
    ('"clinical_core/respiratory_drive_report.py",\n', '"clinical_core/respiratory_drive_reports.py",\n'),
])
def test_the_proof_notices_any_other_change(old, new):
    live = em._live("clinical_core/lactate_slice.py")
    assert live.count(old) == 1 and not em.proved("clinical_core/lactate_slice.py", live.replace(old, new))


def test_closed_packages_read_the_p2p2_tree():
    with pytest.MonkeyPatch.context() as patch:
        em.chain(patch)
        assert "embolism" not in rd._live("clinical_core/lactate_slice.py")
        assert "embolism" not in rd._live("clinical_core/decision_pack.py")
        assert all(rd.proofs().values())
    assert "embolism_migration_report" in rd._live("clinical_core/lactate_slice.py")


def test_the_p2p2_sources_leave_out_the_p2q2_files():
    sources = em.p2p2_sources(bf.freeze_sources())
    assert not set(em.OWN) & set(sources)
    for relative, sha in em.CORE_AT_P2P2.items():
        assert sources[relative] == sha


# The family writers ------------------------------------------------------------------------------------------------------------

def _start(case=mr.CASE):
    a, p = mr.anchors(case), em.profile()
    return dv.arrival_state(a, p), a, p


@pytest.mark.parametrize("build", [
    lambda: ObstructiveForwardFlow("x", -0.001, 0.5), lambda: ObstructiveForwardFlow("x", 0.001, 0.0),
    lambda: ObstructiveForwardFlow("x", 0.001, 1.01), lambda: ObstructiveForwardFlow("x", float("inf"), 0.5),
    lambda: ObstructiveForwardFlow("x", True, 0.5), lambda: EmbolicGasExchange("x", -0.01),
    lambda: EmbolicGasExchange("x", float("nan")), lambda: EmbolicLungWater("x", -0.01),
])
def test_the_writers_refuse_impossible_values(build):
    with pytest.raises(CoreInvariantError):
        build()


def test_the_obstruction_writes_p_only_and_stops_at_its_floor():
    s, a, p = _start()
    writer = ObstructiveForwardFlow("pe-obstruction", 0.1, 0.5)
    contribution = writer.contribute(s, 1, (), a, p)
    assert [(d.channel, d.amount) for d in contribution.deltas] == [(Channel.P, -0.1)]
    near = s.evolve(P=0.55)
    assert [d.amount for d in writer.contribute(near, 1, (), a, p).deltas] == pytest.approx([-0.05])
    assert writer.contribute(s.evolve(P=0.5), 1, (), a, p).deltas == ()
    assert ObstructiveForwardFlow("z", 0.0, 0.5).contribute(s, 1, (), a, p).deltas == ()


def test_no_writer_acts_without_a_pulse():
    s, a, p = _start()
    pulseless = s.evolve(R=RhythmState.asystole(), terminal_since=s.minute)
    for writer in (ObstructiveForwardFlow("o", 0.01, 0.5), EmbolicGasExchange("g", 0.01), EmbolicLungWater("l", 0.01)):
        assert writer.contribute(pulseless, 1, (), a, p).deltas == ()


def test_the_gas_writer_writes_g_and_the_owner_writes_l_only_when_authored():
    s, a, p = _start()
    assert [(d.channel, d.amount) for d in EmbolicGasExchange("g", 0.02).contribute(s, 1, (), a, p).deltas] == \
        [(Channel.G, 0.02)]
    assert EmbolicLungWater("l").contribute(s, 1, (), a, p).deltas == ()
    assert [(d.channel, d.amount) for d in EmbolicLungWater("l", 0.01).contribute(s, 1, (), a, p).deltas] == \
        [(Channel.L, 0.01)]


def test_the_authority_is_declared_on_the_owner_only_and_replays():
    assert EmbolicLungWater.lung_water_authority is True
    assert ObstructiveForwardFlow.lung_water_authority is False and EmbolicGasExchange.lung_water_authority is False
    for writer in em.writers():
        assert from_spec(writer.to_spec()) == writer


def test_a_second_owner_of_lung_water_is_refused():
    s, a, p = _start()
    with pytest.raises(ProvenanceError):
        step(s, (em.owner(), EdemaCongestion("edema-congestion", 0.005)), a, p)


def test_writer_semantics_from_the_source():
    out = em.writer_semantics()
    assert out["pass"], out
    assert out["classes"]["ObstructiveForwardFlow"]["writes"] == ["P"] and not out["writes_v"]


# The case mapping --------------------------------------------------------------------------------------------------------------

def test_truth_is_read_from_the_bank():
    for case in mr.CASES:
        bank = mr.bank_case(case)
        t = mr.truth(case)
        assert t["sbp"] == bank["observable"]["sbp"] and t["pocus_ivc"] == bank["investigations"]["pocus"]["result"]["ivc"]
        assert t["abg_paco2"] == bank["investigations"]["abg"]["result"]["paco2_mm_hg"]
    assert em.case()["available"]


def test_the_lv_band_runs_from_the_gi_floor_to_neutral_and_only_for_the_underfilled_lv():
    # Review H1: the GI bands also read a collapsing IVC, so only the scale's floor is borrowed; an underfilled LV is
    # never above the neutral position.
    band = mr.preload_band(mr.CASE)
    assert (band.lower, band.midpoint, band.upper) == pytest.approx((0.2, 0.35, 0.5))
    assert band.lower == min(b[0] for b in mr.gi_reference.PRELOAD_BANDS.values())
    assert mr.NEUTRAL_PRELOAD_POSITION == dv.DEFAULT_PROFILE.arrival_preload_fraction == band.upper
    assert band.classification == mr.FAMILY_CANDIDATE and "not transferred" in band.rule
    assert mr.preload_band(mr.SECONDARY) is None and mr.anchors(mr.SECONDARY).preload_fraction is None
    assert mr.anchors().preload_fraction == pytest.approx(0.35) and mr.anchors().declared["preload_fraction"] == \
        "synthetic_probe"


def test_the_ivc_and_the_jvp_never_reach_v(monkeypatch):
    real = mr.truth

    def changed(case=mr.CASE):
        t = dict(real(case))
        t["pocus_ivc"], t["cardiac_exam"], t["pocus_rv"] = "0.9 cm; complete collapse", "Flat neck veins.", "Normal"
        return t
    before = mr.anchors()
    monkeypatch.setattr(mr, "truth", changed)
    assert mr.anchors().preload_fraction == before.preload_fraction

    def normal_lv(case=mr.CASE):
        t = dict(real(case))
        t["pocus_lv"] = "Normal size and contraction"
        return t
    monkeypatch.setattr(mr, "truth", normal_lv)
    assert mr.anchors().preload_fraction is None


@pytest.mark.parametrize("item, text", [
    ("pocus_lungs", "Diffuse bilateral B-lines"),
    ("pocus_lungs", "No B-lines anteriorly; bilateral posterior B-lines"),        # review H3
    ("chest_xray", "No focal consolidation; bilateral interstitial pulmonary edema."),
    ("respiratory_exam", "Marked effort; widespread bilateral crackles."),
    ("chest_xray", "No pneumothorax but perihilar congestion."),
])
def test_authored_edema_would_not_get_a_zero_owner_silently(monkeypatch, item, text):
    real = mr.truth

    def edema(case=mr.CASE):
        t = dict(real(case))
        t[item] = text
        return t
    assert mr.lung_water_generation(mr.CASE) == 0.0 and mr.lung_water_generation(mr.SECONDARY) == 0.0
    monkeypatch.setattr(mr, "truth", edema)
    assert mr.authored_pulmonary_edema(mr.CASE)
    with pytest.raises(ValueError):
        mr.lung_water_generation(mr.CASE)


def test_the_two_cases_author_no_edema_on_every_l_text():
    for case in mr.CASES:
        assert not mr.authored_pulmonary_edema(case)
        assert all(mr.truth(case)[item] for item in mr.L_EVIDENCE)


@pytest.mark.parametrize("case", mr.CASES)
def test_the_arrival_is_exact_where_the_core_models_it(case):
    out = em.arrival(case)
    assert out["pass"], out
    assert out["channels_at_arrival"] == {"V": 0.0, "P": 1.0, "L": 0.0, "G": 0.0, "D": out["channels_at_arrival"]["D"],
                                          "T": 1.0}


def test_the_arrival_position_never_changes_the_arrival():
    assert em.arrival_position_invariance()["pass"]


# The migration's probes --------------------------------------------------------------------------------------------------------

def test_the_obstruction_runs_through_the_common_core():
    out = em.obstruction_course()
    assert out["pass"], out


def test_no_double_count():
    out = em.no_double_count(em.untreated(), em.arrival_position_invariance())
    assert out["pass"], out


def test_the_owner_closes_the_false_edema():
    out = em.lung_water_owner()
    assert out["pass"], out
    # P2Q-1's conflict, reproduced without the owner on the rejected plethoric-IVC mapping.
    assert out["counterfactual_rejected_ivc_no_owner"]["common_writes"] > 0
    assert out["counterfactual_rejected_ivc_no_owner"]["L_max"] > 0.0


def test_the_fluid_stress_makes_no_false_l():
    out = em.fluid_stress()
    assert out["pass"], out
    assert set(out["points"]) == {"lower", "midpoint", "upper"}


def test_direct_g_gets_no_lung_water_credit():
    out = em.direct_g()
    assert out["pass"], out


def test_oxygen_is_the_common_response():
    out = em.oxygen()
    assert out["pass"], out


def test_the_p2p2_drive_accepts_the_pe_hypoxaemia_structurally():
    out = em.respiratory_drive()
    assert out["pass"], out
    assert not out["parameter_status"]["chosen_from_pe"]


def test_central_depression_still_dominates():
    assert em.central_depression()["pass"]


def test_d_and_lactate_stay_common():
    out = em.d_lactate(em.untreated())
    assert out["pass"], out


def test_a_d_read_from_the_lactate_would_be_caught(monkeypatch):
    # Review H2: the arrival D is rebuilt from a truth whose lactate is doubled, so a D derived from it would differ.
    real = mr.bands

    def lactate_debt(case=mr.CASE, t=None):
        out = dict(real(case, t))
        t = mr.truth(case) if t is None else t
        band = out.get("arrival_oxygen_debt")
        if band is not None:
            out["arrival_oxygen_debt"] = mr.Band(band.name, band.lower, band.upper, 10.0 * t["lactate_mmol_l"],
                                                 band.classification, band.rule)
        return out
    untreated = em.untreated()
    monkeypatch.setattr(mr, "bands", lactate_debt)
    assert not em.d_lactate(untreated)["pass"]


def test_retuned_common_gains_would_be_caught(monkeypatch):
    # Review H2: the gains are compared with the ACS package's point itself (pinned by hash), not this package's wrapper.
    untreated = em.untreated()
    real = mr.common_profile
    monkeypatch.setattr(mr, "common_profile", lambda **changes: real(**{"deficit_to_tone_gain": 2.0, **changes}))
    assert not em.tone(untreated)["gains_untouched"] and not em.heart_rate(untreated)["gains_untouched"]
    monkeypatch.setattr(mr, "common_profile", lambda **changes: real(**{"debt_clearance_tau_min": 999.0, **changes}))
    assert not em.d_lactate(untreated)["kinetics_untouched"]


def test_collapse_accepts_the_outputs_structurally():
    out = em.collapse()
    assert out["pass"], out
    assert not out["active"] and not out["thresholds_selected"]


def test_the_secondary_case_shows_hypoxaemia_without_hypotension():
    out = em.secondary()
    assert out["pass"], out


# The verdict rule ---------------------------------------------------------------------------------------------------------------

def _passing() -> dict:
    ok = {"pass": True}
    return {"case": {"available": True}, "arrival": ok, "secondary": {"arrival": ok}, "writer": ok, "obstruction": ok,
            "no_double_count": ok, "lung_water_owner": ok, "fluid_stress": ok, "direct_g": ok, "oxygen": ok,
            "respiratory_drive": ok, "central_depression": ok, "d_lactate": ok, "collapse": ok, "non_regression": ok,
            "tone": ok, "heart_rate": ok,
            "proof": {"proofs": {"x": True}, "common_untouched": {"x": True}, "p2p2_freeze_digest": True,
                      "p2p2_record": True}}


#: Which found item each criterion reads (its index in VERDICT_CRITERIA).
_DECIDES = [(0, ("case",)), (0, ("arrival",)), (0, ("secondary", "arrival")), (1, ("writer",)), (1, ("obstruction",)),
            (2, ("no_double_count",)), (3, ("lung_water_owner",)), (4, ("fluid_stress",)), (5, ("direct_g",)),
            (6, ("oxygen",)), (7, ("respiratory_drive",)), (7, ("central_depression",)), (8, ("d_lactate",)),
            (9, ("collapse",)), (10, ("non_regression",)), (10, ("tone",)), (10, ("heart_rate",))]


def test_the_verdict_is_ready_only_when_every_criterion_holds():
    assert em.verdict(_passing())["verdict"] == em.READY


@pytest.mark.parametrize("index, path", _DECIDES)
def test_every_criterion_decides_the_verdict(index, path):
    found = json.loads(json.dumps(_passing()))
    target = found
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = {"pass": False, "available": False}
    out = em.verdict(found)
    assert not out["ready"] and out["blocker"] == em.VERDICT_CRITERIA[index]


@pytest.mark.parametrize("key, value", [("p2p2_freeze_digest", False), ("p2p2_record", False),
                                        ("proofs", {"x": False}), ("common_untouched", {"x": False})])
def test_the_proof_decides_the_verdict(key, value):
    found = _passing()
    found["proof"][key] = value
    assert em.verdict(found)["blocker"] == em.VERDICT_CRITERIA[-1]


# The frozen record and the document ------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def record():
    if not em.RECORD.exists():
        pytest.skip("the P2Q-2 record is written by the evaluation run, after the freeze")
    return json.loads(em.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert record == mc.without_new_anchor_key(em.go._plain(json.loads(json.dumps(em.run(), sort_keys=True,
                                                                                  default=str))))
    assert record["verdict"]["verdict"] == em.READY


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import embolism_migration_report as report
    text = em.DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        opening, closing = report.MARKERS[name]
        assert text.count(opening) == 1 and text.count(closing) == 1
        assert text.split(opening)[1].split(closing)[0].strip("\n") == render(record).strip("\n")
