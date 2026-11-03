"""P2O-1: the common lung-water / gas-exchange architecture (L -> G -> oxygenation -> delivery), shadow only.

The core gains two inert insertions (derived.py, integration.py), off by default; these tests pin that the live core is
the P2N-2 core plus exactly those insertions, that the default profile changes nothing, the structure's analytic
properties, the boundaries, and that the frozen record is reproduced live.
"""
import hashlib
import json
import math
from dataclasses import replace

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import gas_exchange_architecture as go
from clinical_core.state import CoreInvariantError

#: The P2O-1 freeze: the semantics, the L -> G and G -> oxygenation structures, the SYNTHETIC_ONLY region, the probes,
#: the cross-family criteria, the GI / ACS designs, the verdict and recommendation rules, the proof and every
#: clinical_core source but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "22bb29b95714b28044c418cd8e4b5f0058d1f5065eafffc509e656ff8c6db733"


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert go.OWN[0] in sources and go.REPORT not in sources
    assert go.REPORT in lactate_slice.DOWNSTREAM_REPORTS
    assert {go.OWN[0], go.REPORT} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    assert hashlib.sha256(go.P2N2_RECORD.read_bytes()).hexdigest() == go.P2N2_RECORD_SHA
    if FROZEN_DIGEST is not None:
        assert go.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_the_core_is_the_p2n2_core_plus_exactly_the_declared_insertions():
    assert go.proofs() == {go.DERIVED: True, go.INTEGRATION: True}
    for relative in go.CORE_FILES:
        assert go.INSERTIONS_AT_P2O1[relative] is not None
        assert go.insertions_digest(relative) == go.INSERTIONS_AT_P2O1[relative]
        assert hashlib.sha256(go.p2n2_text(relative).encode("utf-8")).hexdigest() == go.CORE_AT_P2N2[relative]
    mapped = go.p2n2_sources(bf.freeze_sources())
    assert go.OWN[0] not in mapped
    for relative, sha in {**go.CORE_AT_P2N2, **go.TUPLE_AT_P2N2}.items():
        assert mapped[relative] == sha


@pytest.mark.parametrize("relative, old, new", [
    # a change outside the insertions
    (go.DERIVED, "OUTPUT_EPSILON = 1e-9", "OUTPUT_EPSILON = 1e-8"),
    # an insertion no longer guarded
    (go.DERIVED, "    if gas_exchange_active(profile):\n        spo2 = oxygenation(",
     "    if True:\n        spo2 = oxygenation("),
    (go.INTEGRATION, "if channel is Channel.G and lung_water_gas_exchange_active(profile):", "if channel is Channel.G:"),
    # an inserted field on by default
    (go.DERIVED, "lung_water_to_gas_exchange_gain: float | None = None",
     "lung_water_to_gas_exchange_gain: float | None = 1.0"),
    # an inserted function changed after the freeze
    (go.DERIVED, "1.0 / (1.0 + profile.oxygen_response_loss_per_gas_exchange_unit",
     "2.0 / (1.0 + profile.oxygen_response_loss_per_gas_exchange_unit"),
])
def test_the_proof_notices_any_other_change(relative, old, new):
    live = go._live(relative)
    mutated = live.replace(old, new)
    assert mutated != live
    assert not go.proved(relative, mutated)


def test_the_default_profile_keeps_every_p2o1_path_off():
    p = dv.DEFAULT_PROFILE
    assert all(getattr(p, name) is None for name in go.REFERENCE)
    assert not dv.gas_exchange_active(p) and not dv.lung_water_gas_exchange_active(p)
    for name in go.REFERENCE:
        status, text = dv.PARAMETERS[name]
        assert status == dv.PROVISIONAL and text.startswith("UNSET (P2O-1)") and "not approved" in text


@pytest.mark.parametrize("changes", [
    {"spo2_per_gas_exchange_unit": 5.0},
    {"oxygen_response_loss_per_gas_exchange_unit": 0.5},
    {"spo2_per_gas_exchange_unit": 0.0, "oxygen_response_loss_per_gas_exchange_unit": 0.5},
    {"lung_water_to_gas_exchange_gain": 1.0},
    {"lung_water_to_gas_exchange_gain": -1.0, "spo2_per_gas_exchange_unit": 5.0,
     "oxygen_response_loss_per_gas_exchange_unit": 0.5},
    {"spo2_per_gas_exchange_unit": 5.0, "oxygen_response_loss_per_gas_exchange_unit": -0.1},
])
def test_the_profile_refuses_a_partial_or_invalid_gas_exchange(changes):
    with pytest.raises(CoreInvariantError):
        replace(dv.DEFAULT_PROFILE, **changes)


# The structure, analytically ------------------------------------------------------------------------------------------------

def _old_spo2(fio2, anchors, profile):
    oxygen = max(0.0, fio2 - profile.room_air_fio2) - max(0.0, anchors.fio2 - profile.room_air_fio2)
    return min(100.0, max(0.0, anchors.spo2 + profile.spo2_per_fio2 * oxygen))


@pytest.mark.parametrize("anchors", [go.NEUTRAL, go.ON_OXYGEN])
def test_oxygenation_is_exact_at_arrival_never_better_with_g_never_worse_with_fio2(anchors):
    for point in go.one_d_points():
        p = go.gas_profile(dv.DEFAULT_PROFILE, **point)
        for fio2 in (0.21, 0.3, 0.4, 0.6, 1.0):
            if fio2 < anchors.fio2:
                continue
            assert dv.oxygenation(0.0, fio2, anchors, p) == _old_spo2(fio2, anchors, p)
            assert dv.oxygenation(-1.0, fio2, anchors, p) == _old_spo2(fio2, anchors, p)
            values = [dv.oxygenation(g, fio2, anchors, p) for g in (0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0)]
            assert all(b <= a for a, b in zip(values, values[1:]))
            assert all(b < a for a, b in zip(values, values[1:]) if 0.0 < a < 100.0)
        for g in (0.0, 0.5, 2.0, 8.0):
            curve = [dv.oxygenation(g, f, anchors, p) for f in (0.21, 0.3, 0.4, 0.6, 1.0) if f >= anchors.fio2]
            assert all(b >= a for a, b in zip(curve, curve[1:]))
            retained = dv.oxygen_response_retained(g, p)
            assert 0.0 < retained <= 1.0 and (retained < 1.0) == (g > 0.0 and p.oxygen_response_loss_per_gas_exchange_unit > 0.0)


def test_the_coupling_sums_to_k_times_lung_water_above_arrival_and_ignores_water_below_it():
    p = go.gas_profile(dv.DEFAULT_PROFILE)
    k = p.lung_water_to_gas_exchange_gain
    path = [0.0, 0.3, 0.9, 1.4, 1.1, 0.4, 0.0, -0.5, -0.2, 0.6]
    total = 0.0
    for before, after in zip(path, path[1:]):
        step_ = dv.lung_water_gas_exchange(before, after, p)
        total += step_
        assert math.isclose(total, k * max(0.0, after), abs_tol=1e-12)
        if after < before:
            assert step_ <= 0.0       # lung water improving never worsens G


def test_the_boundaries_hold():
    b = go.boundaries()
    assert b["pass"], b
    assert b["readers_in_derived"]["G"] == ["_perfusion"] and b["core_G_writers"] == 1
    assert not b["disease_terms_in_core_insertions"] and not b["family_modules_writing_G"]


def test_one_d_region_has_no_cartesian_product():
    points = go.one_d_points()
    assert len(points) == 1 + sum(len(v) - 1 for v in go.ONE_D.values())
    for point in points[1:]:
        assert sum(point[k] != go.REFERENCE[k] for k in go.REFERENCE) == 1


def test_the_l_to_g_forms_were_compared_and_only_the_first_order_term_kept():
    selected = [k for k, v in go.L_TO_G_FORMS.items() if v["status"] == "SELECTED"]
    assert selected == ["linear_first_order"]
    assert all(v["status"] == "ELIMINATED" and v["why"] for k, v in go.L_TO_G_FORMS.items() if k not in selected)


# The frozen evaluation ----------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def record():
    if not go.RECORD.exists():
        pytest.skip("the P2O-1 record is written by the evaluation run, after the freeze")
    return json.loads(go.RECORD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def result():
    return json.loads(json.dumps(go.run(), sort_keys=True))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, result):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert result == record


def test_the_verdict_follows_the_predeclared_rule(record):
    judged = record["verdict"]
    ready = all(judged["criteria"].values()) and all(judged["extra"].values())
    assert judged["verdict"].startswith("COMMON_GAS_EXCHANGE_ARCHITECTURE_READY") == ready
    assert record["recommendation"] == (go.recommendation(ready, record["congestion_generation"]))
    assert all(not s["approved"] for s in record["design"]["parameter_status"].values())
