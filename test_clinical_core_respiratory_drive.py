"""P2P-2: the common respiratory-drive composition (structural, uncalibrated).

The core's RR (P2K-2's path) becomes availability x the RR of the excitatory drive (acid + hypoxaemic), the hypoxaemic
drive read from the current absolute SpO2 through an UNSET mapping, the availability 1 by default. These tests pin the
profile's inputs and their refusals, the absolute signal, the composition's exact P2K-2 default, probes D1-D10, the
diagnostics, the boundaries, the proof against the P2P-1 core and the freeze.
"""
import copy
import json
import hashlib
import math
from dataclasses import replace

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import edema_migration as pe
from clinical_core import edema_reference as er
from clinical_core import respiratory_drive as rd
from clinical_core import embolism_migration as em
from clinical_core import respiratory_mechanics as mc
from clinical_core import asthma_migration as sm
from clinical_core import respiratory_distress as dm
from clinical_core import distress_closure as xm
from clinical_core import asthma_distress_migration as tm
from clinical_core import oxygenation_link as om
from clinical_core import opioid_migration as un
from clinical_core import systemic_stress as ss
from clinical_core import distributive_tone as dt
from clinical_core import closure_guard as cg
from clinical_core import amendment_2 as a2
from clinical_core import tone_domain as x1
from clinical_core.state import CoreInvariantError

#: The P2P-2 freeze: the core insertions (by the proof), the audit, the semantics, the synthetic values, probes D1-D10,
#: the diagnostics, the readiness rule and every clinical_core source but the downstream reports, committed before the
#: evaluation run.
FROZEN_DIGEST = "5e705336b733be87c4bf1cc16fd8fdb664a11050aa9bed32ea82b539afe5f449"

#: P2Q-2 added files (the PE family, its mapping and analysis) and two tuple entries, proven against the P2P-2 files
#: (embolism_migration.proved): this package's guards read the tree as P2P-2 left it (em.chain, em.p2p2_sources);
#: the record is unchanged.
#: P2S-2 changed the core (the common respiratory mechanics candidate, off by default) and two tuple files,
#: proven against the P2Q-2 files (respiratory_mechanics.proved): this package's guards read the tree as
#: P2Q-2 left it (mc.chain, mc.p2q2_sources).
#: P2S-3 added files (the asthma family, its mapping and analysis) and two tuple entries, proven against the
#: P2S-2 files (asthma_migration.proved): this package's guards read the tree as P2S-2 left it (sm.chain,
#: sm.p2s2_sources).
#: P2T-1 changed four common files (the respiratory distress input and its two UNSET readers), proven against
#: the P2S-3 files (respiratory_distress.proved): this package's guards read the tree as P2S-3 left it
#: (dm.chain, dm.p2s3_sources).
#: P2T-1A changed two common files (the M1 guard and the L1 sum) and two tuple files, proven against the
#: P2T-1 files (distress_closure.proved): this package's guards read the tree as P2T-1 left it
#: (xm.chain, xm.p2t1_sources).
#: P2T-3 added files (the asthma distress migration) and two tuple entries, proven against the P2T-1A files
#: (asthma_distress_migration.proved): this package's guards read the tree as P2T-1A left it (tm.chain,
#: tm.p2t1a_sources).
#: P2T-5 changed the core (the hypoventilation -> oxygenation link, off by default: one UNSET profile field) and
#: two tuple files, proven against the P2T-3 files (oxygenation_link.proved): this package's guards read the
#: tree as P2T-3 left it (om.chain, om.p2t3_sources).
#: P2W-1 changed the core (the common vasodilatory burden: one auxiliary field, one arrival anchor, one
#: provenance record and one UNSET profile reader of the tone target, the burden 0 by default) and two tuple
#: files, proven against the P2V-1 files (distributive_tone.proved): this package's guards read the tree as
#: P2V-1 left it (dt.chain, dt.p2v1_sources).
#: P2V-1 changed the core (the common systemic stress: one auxiliary field, one arrival anchor, one provenance
#: record and one UNSET profile reader, the stress 0 by default) and two tuple files, proven against the P2U-1
#: files (systemic_stress.proved): this package's guards read the tree as P2U-1 left it (ss.chain,
#: ss.p2u1_sources).
#: P2U-1 changed the core (the common central respiratory drive availability: one auxiliary field, one arrival
#: anchor and one provenance record, all at their reference 1 by default) and two tuple files, proven against the
#: P2T-5 files (opioid_migration.proved): this package's guards read the tree as P2T-5 left it (un.chain,
#: un.p2t5_sources).
_LIVE_SOURCES_P2X1A = bf.freeze_sources


def _LIVE_SOURCES_P2X1() -> dict:
    return cg.p2x1_sources(_LIVE_SOURCES_P2X1A())


def _LIVE_SOURCES_P2W1() -> dict:
    return x1.p2w1_sources(_LIVE_SOURCES_P2X1())


def _LIVE_SOURCES_P2V1() -> dict:
    return dt.p2v1_sources(_LIVE_SOURCES_P2W1())


def _LIVE_SOURCES_P2U1() -> dict:
    return ss.p2u1_sources(_LIVE_SOURCES_P2V1())


def _LIVE_SOURCES_P2T5() -> dict:
    return un.p2t5_sources(_LIVE_SOURCES_P2U1())


def _LIVE_SOURCES_P2T3() -> dict:
    return om.p2t3_sources(_LIVE_SOURCES_P2T5())


def _LIVE_SOURCES_P2T1A() -> dict:
    return tm.p2t1a_sources(_LIVE_SOURCES_P2T3())


def _LIVE_SOURCES_P2T1() -> dict:
    return xm.p2t1_sources(_LIVE_SOURCES_P2T1A())


def _LIVE_SOURCES_P2S3() -> dict:
    return dm.p2s3_sources(_LIVE_SOURCES_P2T1())


def _LIVE_SOURCES_P2S2() -> dict:
    return sm.p2s2_sources(_LIVE_SOURCES_P2S3())


def _LIVE_SOURCES_P2Q2() -> dict:
    return mc.p2q2_sources(_LIVE_SOURCES_P2S2())


@pytest.fixture(autouse=True, scope="module")
def _p2p2_tree():
    with pytest.MonkeyPatch.context() as patch:
        em.chain(patch)
        mc.chain(patch)
        sm.chain(patch)
        dm.chain(patch)
        xm.chain(patch, historical=False)
        tm.chain(patch)
        om.chain(patch)
        un.chain(patch)
        ss.chain(patch)
        dt.chain(patch)
        x1.chain(patch)
        cg.chain(patch)
        a2.chain(patch)
        patch.setattr(bf, "freeze_sources", lambda: em.p2p2_sources(_LIVE_SOURCES_P2Q2()))
        yield


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert all(relative in sources for relative in rd.OWN) and rd.REPORT not in sources
    assert set(rd.TUPLES_ADDED["DOWNSTREAM_REPORTS"]) <= set(lactate_slice.DOWNSTREAM_REPORTS)
    assert set(rd.TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert rd.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_the_live_core_is_the_p2p1_core_plus_the_declared_insertions():
    assert set(rd.REVERSAL) == set(rd.CORE_AT_P2P1) == {"clinical_core/derived.py", "clinical_core/lactate_slice.py",
                                                        "clinical_core/decision_pack.py"}
    assert all(rd.proofs().values())
    for relative, sha in rd.CORE_AT_P2P1.items():
        assert hashlib.sha256(rd.p2p1_bytes(relative)).hexdigest() == sha
    assert all(rd.common_untouched().values()) and len(rd.COMMON_AT_P2P1) >= 20
    proof = rd.upstream_unchanged()
    assert proof["p2p1_freeze_digest"] and proof["p2p1_record"] and all(proof["p2p1_common_untouched"].values())


@pytest.mark.parametrize("old, new", [
    ("    return availability * excitatory_rr\n", "    return availability * excitatory_rr + 0.0\n"),
    ("    central_drive_availability: float = 1.0\n", "    central_drive_availability: float = 0.9\n"),
    ('    return {"authored_rr"', '    return {"authored_rr_"'),
])
def test_the_proof_notices_any_other_change(old, new):
    live = rd._live("clinical_core/derived.py")
    assert live.count(old) == 1 and not rd.proved("clinical_core/derived.py", live.replace(old, new))


def test_closed_packages_read_the_p2p1_core():
    with pytest.MonkeyPatch.context() as patch:
        rd.chain(patch)
        text = pe._live("clinical_core/derived.py")
        assert "central_drive_availability" not in text and "hypoxaemic_drive_mapping" not in text
        assert all(pe.common_untouched().values())


# P2P-2-2 / 3 / 4: the profile's inputs ----------------------------------------------------------------------------------------

def test_defaults_are_unset_and_neutral():
    p = dv.DEFAULT_PROFILE
    assert p.hypoxaemic_drive_mapping is None and p.hypoxaemic_to_drive_gain is None
    assert p.central_drive_availability == 1.0
    for name in ("hypoxaemic_drive_mapping", "hypoxaemic_to_drive_gain", "central_drive_availability"):
        status, note = dv.PARAMETERS[name]
        assert status == dv.PROVISIONAL and ("UNSET" in note or "STRUCTURAL_INPUT" in note)


@pytest.mark.parametrize("changes, message", [
    ({"hypoxaemic_drive_mapping": rd.SYNTHETIC_MAPPING}, "together"),
    ({"hypoxaemic_to_drive_gain": 5.0}, "together"),
    ({"hypoxaemic_drive_mapping": ((100.0, 0.0),), "hypoxaemic_to_drive_gain": 5.0}, "two finite"),
    ({"hypoxaemic_drive_mapping": ((100.0, 0.0), (50.0, math.nan)), "hypoxaemic_to_drive_gain": 5.0}, "two finite"),
    ({"hypoxaemic_drive_mapping": ((100.0, 0.0), (50.0, 1.5)), "hypoxaemic_to_drive_gain": 5.0}, "0 to 1"),
    ({"hypoxaemic_drive_mapping": ((50.0, 0.0), (100.0, 1.0)), "hypoxaemic_to_drive_gain": 5.0}, "strictly"),
    ({"hypoxaemic_drive_mapping": ((100.0, 0.5), (50.0, 0.2)), "hypoxaemic_to_drive_gain": 5.0}, "never decreases"),
    ({"central_drive_availability": 1.2}, "between 0"),
])
def test_the_profile_refuses_a_half_or_incoherent_composition(changes, message):
    with pytest.raises(CoreInvariantError, match=message):
        replace(rd.base_profile(), **changes)


def test_the_composition_needs_the_p2k2_physiology():
    with pytest.raises(CoreInvariantError, match="P2K-2"):
        replace(dv.DEFAULT_PROFILE, central_drive_availability=0.5)
    with pytest.raises(CoreInvariantError, match="P2K-2"):
        replace(dv.DEFAULT_PROFILE, hypoxaemic_drive_mapping=rd.SYNTHETIC_MAPPING, hypoxaemic_to_drive_gain=5.0)


def test_the_hypoxaemic_signal_interpolates_and_holds_the_end_values():
    p = rd.hypoxaemic(rd.base_profile(), 10.0, ((95.0, 0.0), (85.0, 0.5), (75.0, 1.0)))
    assert dv.hypoxaemic_drive_signal(99.0, p) == 0.0 and dv.hypoxaemic_drive_signal(95.0, p) == 0.0
    assert dv.hypoxaemic_drive_signal(90.0, p) == pytest.approx(0.25)
    assert dv.hypoxaemic_drive_signal(80.0, p) == pytest.approx(0.75)
    assert dv.hypoxaemic_drive_signal(60.0, p) == 1.0
    assert dv.hypoxaemic_drive(80.0, p) == pytest.approx(7.5)
    assert dv.hypoxaemic_drive(80.0, rd.base_profile()) == 0.0
    values = [dv.hypoxaemic_drive(x, p) for x in range(100, 59, -1)]
    assert all(b >= a for a, b in zip(values, values[1:]))


def test_the_hypoxaemic_drive_is_absolute():
    out = rd.absolute_check()
    assert out["pass"] and out["arrival_81_drive"] > 0.0 and out["same_paco2"]
    assert not any(out["reads_arrival"].values())


# The exact default and probes D1-D10 --------------------------------------------------------------------------------------------

def test_default_composition_is_p2k2_bit_for_bit_at_arrival():
    old = rd.p2p1_core()
    for anchors, profile in ((er.anchors(), pe.profile()), (rd.go.ar.anchors(), rd.go.gas_profile(rd.go.ar.common_profile()))):
        state = dv.arrival_state(anchors, profile)
        op = rd._old_profile(old, profile)
        assert dv.respiration(state, anchors, profile) .__dict__ == old.respiration(state, anchors, op).__dict__
        assert dv.derive(state, anchors, profile).to_dict() == old.derive(state, anchors, op).to_dict()
        c = dv.respiratory_drive_composition(state, anchors, profile)
        assert c.availability == 1.0 and c.hypoxaemic_drive == 0.0 and c.spo2 is None
        assert c.expressed_rr == c.excitatory_rr == dv.rate_from_drive(c.acid_drive, c.baseline_rr, profile)


@pytest.fixture(scope="module")
def probes():
    return rd.structural_probes()


@pytest.mark.parametrize("name", sorted(rd.PROBES))
def test_every_structural_probe_passes(probes, name):
    assert probes["pass"][name], (name, probes[name])


def test_depression_lowers_the_intrinsic_share_and_bounds_any_drive(probes):
    for name in ("D6", "D7"):
        d = probes[name]
        assert d["full_availability_rr"] > rd.PROBE_INTRINSIC > d["depressed_rr"]
        assert d["depressed_rr_any_drive"] <= d["bound_rr"] <= rd.PROBE_INTRINSIC
    assert probes["D9"]["at_zero"] == 0.0 and probes["D9"]["intrinsic_rr_unchanged"]
    assert probes["D10"]["derived_fields_differing"] == ["respiratory_rate"]
    # Central hypoventilation raises PaCO2 and lowers pH (the anchor stays P2K-2's, adversarial review H1).
    assert probes["D10"]["depression_raises_paco2_lowers_ph"]


def test_d8_compares_every_family_course(probes):
    families = {r["family"] for r in probes["D8"]["rows"]}
    assert families == {"gi", "acs", "pulmonary_edema", "metabolic_acidosis_probe"}
    assert probes["D8"]["compared"] >= 20


def test_the_arrival_paco2_anchor_is_p2k2s_and_exact_with_the_defaults():
    old = rd.p2p1_core()
    for anchors, profile in ((er.anchors(), pe.profile()), (rd.go.NEUTRAL, rd.base_profile())):
        op = rd._old_profile(old, profile)
        assert dv.arrival_alveolar_ventilation(anchors, profile) == old.arrival_alveolar_ventilation(anchors, op)
        r = dv.respiration(dv.arrival_state(anchors, profile), anchors, profile)
        assert r.paco2 == pytest.approx(dv.arrival_paco2(anchors, profile), abs=1e-9)
    # With a depression the anchor is unchanged and the arrival PaCO2 departs from the authored one.
    depressed = replace(pe.profile(), central_drive_availability=0.5)
    a = er.anchors()
    assert dv.arrival_alveolar_ventilation(a, depressed) == dv.arrival_alveolar_ventilation(a, pe.profile())
    assert dv.respiration(dv.arrival_state(a, depressed), a, depressed).paco2 > dv.arrival_paco2(a, depressed)


def test_d8_refuses_a_profile_with_the_new_inputs_set():
    old = rd.p2p1_core()
    with pytest.raises(AssertionError, match="defaults"):
        rd._old_profile(old, replace(rd.base_profile(), central_drive_availability=0.5))


# Diagnostics and boundaries -------------------------------------------------------------------------------------------------

def test_pulmonary_edema_diagnostic_reads_direction_never_fits():
    out = rd.pulmonary_edema_diagnostic()
    assert out["direction_sensible"] and out["mechanics_gap"] and out["gain_from_case"] is False
    assert all(r["gap_to_authored_rr_at_arrival"] > 0.0 for r in out["runs"].values())
    assert set(out["runs"]) == {"unset"} | {f"synthetic_{g:g}" for g in rd.SYNTHETIC_GAINS}


def test_opioid_like_and_acidosis_probes():
    o, a = rd.opioid_probe(), rd.acidosis_probe()
    assert o["pass"] and all(o["checks"].values()) and o["checks"]["depression_raises_paco2"]
    assert a["pass"] and a["acid_drives"] and a["depression_attenuates"]


def test_the_composition_writes_nothing_and_nothing_downstream_reads_it():
    assert rd.downstream()["pass"]


def test_no_value_mechanics_or_disease_term_enters_the_core():
    b = rd.boundaries()
    assert b["pass"] and b["mechanics_separate"] and b["no_values"]
    assert not b["disease_terms_in_core_insertions"] and not b["new_state"]
    assert set(b["composition_literals"]) <= {0, 0.0, 1, 1.0}


def test_the_audit_reads_the_p2p1_core():
    a = rd.audit()
    assert a["pass"] and a["reads"]["drive_terms"] == ["acid_to_drive_gain"]
    assert a["classification"]["p2k2_candidate"].startswith("EXCITATORY_DRIVE_EXPLICIT")


# The readiness rule: every criterion decides ------------------------------------------------------------------------------------

def _all_true_found():
    p = {name: True for name in rd.PROBES}
    return {"probes": {"pass": p}, "absolute": {"pass": True}, "acidosis": {"pass": True, "depression_attenuates": True},
            "opioid": {"pass": True}, "boundaries": {"pass": True, "mechanics_separate": True, "no_values": True},
            "audit": {"pass": True},
            "non_regression": {"pass": True}, "downstream": {"pass": True},
            "proof": {"proofs": {"x": True}, "p2p1_freeze_digest": True, "p2p1_record": True,
                      "p2p1_common_untouched": {"x": True}}}


def test_readiness_is_ready_only_when_every_criterion_holds():
    assert rd.readiness(_all_true_found())["verdict"] == rd.READY
    flips = [("probes", "pass", "D3"), ("probes", "pass", "D1"), ("probes", "pass", "D9"), ("probes", "pass", "D6"),
             ("probes", "pass", "D8"), ("probes", "pass", "D10"), ("boundaries", "no_values", None),
             ("audit", "pass", None)]
    for index, (key, field, sub) in enumerate(flips):
        found = copy.deepcopy(_all_true_found())
        if sub is None:
            found[key][field] = False
        else:
            found[key][field][sub] = False
        out = rd.readiness(found)
        assert not out["ready"] and out["blocker"] == rd.READINESS_CRITERIA[index], (key, sub)
        assert out["verdict"].startswith(rd.NOT_READY) and out["recommendation"] is None


# The frozen record and the document ------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def record():
    if not rd.RECORD.exists():
        pytest.skip("the P2P-2 record is written by the evaluation run, after the freeze")
    return json.loads(rd.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert record == rd.go._plain(json.loads(json.dumps(rd.run(), sort_keys=True, default=str)))
    assert record["readiness"]["verdict"] == rd.READY
    assert record["readiness"]["recommendation"] == "PROCEED_TO_PE_GENERALIZATION_AUDIT"


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import respiratory_drive_report as report
    text = rd.DOC.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        opening, closing = report.MARKERS[name]
        start = text.index(opening) + len(opening)
        assert text[start:text.index(closing, start)] == render(record) + "\n", name
