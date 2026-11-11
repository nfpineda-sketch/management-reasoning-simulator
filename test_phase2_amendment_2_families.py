"""PHASE2_AMENDMENT_2 (A2-018R): cross-family noninterference on the six committed families.

The amendment adds two memories (F and the reused collapse burden) and replaces how the observable consciousness level is
composed. It must change NOTHING else in any family: the physical state, every derived quantity other than the level, and
the trajectory of each family are bit-identical with and without the amendment declared. The opioid family is covered by
the same identity, and its consciousness reading is recorded as a LIMITATION, not solved here (the opioid-specific
mechanism is deferred by the faculty: a respiratory-depression cause is not a circulatory deficit, so this amendment's
composite does not represent it, and no direct oxygen-saturation ladder is restored to do it).
"""
import dataclasses

import pytest

from clinical_core import acs_migration as an
from clinical_core import acs_reference as ar
from clinical_core import asthma_migration as sm
from clinical_core import asthma_reference as sr
from clinical_core import derived as dv
from clinical_core import edema_migration as pe
from clinical_core import edema_reference as er
from clinical_core import embolism_migration as em
from clinical_core import embolism_reference as mr
from clinical_core import gas_exchange_architecture as go
from clinical_core import opioid_migration as un
from clinical_core import opioid_reference as orf
from clinical_core import respiratory_mechanics as mc
from clinical_core import systemic_consciousness as sc

DECLARED = sc.development_profile()
NEW_AUX = (sc.STATE_FIELD, "collapse_burden")


def _gi(case):
    anchors, base, values = go.ba.setup(case)
    profile = go._acid(base)
    scenario, volume = go.GI_SCENARIOS[0]
    items = go.ba.contributors(case, scenario, values, volume)
    return lambda p: mc.course(items, 120, anchors, p)[0], anchors, profile


def _acs():
    anchors, profile = ar.anchors(), ar.common_profile()
    return lambda p: an.course(an.writers(), 120, anchors, p)[0], anchors, profile


def _edema():
    anchors, profile = er.anchors(), pe.profile()
    return lambda p: pe.course((pe.writer(),), 120, anchors, p)[0], anchors, profile


def _embolism():
    anchors, profile = mr.anchors(), em.profile()
    return lambda p: em.course(em.writers(), 120, anchors, p)[0], anchors, profile


def _asthma():
    anchors, profile = sr.anchors(), sm.profile()
    return lambda p: sm.course((sm.obstruction(),), 120, anchors, p)[0], anchors, profile


def _opioid(case):
    anchors, profile = orf.anchors(case), orf.common_profile()
    return lambda p: un.course((un.depression(),), anchors, p)[0], anchors, profile


FAMILIES = {"gi_bleed_57m": lambda: _gi("gi_bleed_57m"), "gi_bleed_72f": lambda: _gi("gi_bleed_72f"),
            "acs": _acs, "pulmonary_edema": _edema, "pulmonary_embolism": _embolism, "asthma": _asthma,
            "opioid_35m": lambda: _opioid("opioid_35m"), "opioid_67f": lambda: _opioid("opioid_67f")}


def _physical(state) -> dict:
    data = state.to_dict()
    data["aux"] = {k: v for k, v in data["aux"].items() if k not in NEW_AUX}
    return data


def _derived_without_the_level(state, anchors, profile) -> dict:
    data = dataclasses.asdict(dv.derive(state, anchors, profile))
    data.pop("consciousness_level")
    return data


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_declaring_the_amendment_changes_no_physical_state_and_no_derived_quantity_but_the_level(family):
    run, anchors, profile = FAMILIES[family]()
    assert profile.amendment_2 is None                                           # off in every committed profile
    declared = dataclasses.replace(profile, amendment_2=DECLARED)
    without, with_it = run(profile), run(declared)
    assert len(without) == len(with_it) > 1
    for before, after in zip(without, with_it):
        assert _physical(before) == _physical(after), (family, before.minute)
        assert _derived_without_the_level(before, anchors, profile) == _derived_without_the_level(after, anchors, declared), (
            family, before.minute)


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_a_committed_family_never_writes_the_new_memories_when_the_amendment_is_off(family):
    run, anchors, profile = FAMILIES[family]()
    for state in run(profile):
        assert state.aux.systemic_encephalopathy_burden is None
        assert state.aux.collapse_burden == 0.0
        assert sc.STATE_FIELD not in state.aux.to_dict()


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_the_new_memories_stay_bounded_and_no_family_reaches_a_state_the_amendment_cannot_read(family):
    run, anchors, profile = FAMILIES[family]()
    declared = dataclasses.replace(profile, amendment_2=DECLARED)
    for state in run(declared):
        assert 0.0 <= sc.systemic_burden(state) <= 1.0 and 0.0 <= state.aux.collapse_burden <= 1.0
        derived = dv.derive(state, anchors, declared)
        assert derived.consciousness_level == sc.consciousness_level(state, anchors, declared)
        assert 0 <= derived.consciousness_level <= 3


def _levels(family):
    run, anchors, profile = FAMILIES[family]()
    declared = dataclasses.replace(profile, amendment_2=DECLARED)
    return ([dv.derive(s, anchors, profile).consciousness_level for s in run(profile)],
            [dv.derive(s, anchors, declared).consciousness_level for s in run(declared)])


@pytest.mark.parametrize("family", ["acs", "asthma", "opioid_35m", "opioid_67f"])
def test_where_the_old_ladders_did_not_write_the_level_the_amended_level_is_the_same(family):
    legacy, amended = _levels(family)
    assert legacy == amended


@pytest.mark.parametrize("family", ["pulmonary_edema", "pulmonary_embolism"])
def test_declaring_the_amendment_outside_gi_removes_the_hypoxaemic_level_so_it_is_not_a_supported_use(family):
    """LIMITATION, recorded and pinned: the oedema and embolism courses read a raised level today only through the direct
    oxygen-saturation ladder, which the faculty removed from the amendment's behaviour. Declared on them, the level reads
    lower. This stage therefore supports the amendment for GI only (A2-FD: GI first); no committed profile declares it
    elsewhere, and no oxygen-saturation mechanism is added here to compensate."""
    legacy, amended = _levels(family)
    assert all(a <= l for l, a in zip(legacy, amended)) and amended != legacy
    assert max(amended) == 0


def test_the_composite_names_no_opioid_and_no_oxygen_saturation_in_its_code():
    """Opioid-specific and saturation-specific consciousness mechanisms are deferred: not one identifier of them is here."""
    import ast
    import inspect
    names = set()
    for node in ast.walk(ast.parse(inspect.getsource(sc))):
        if isinstance(node, ast.Name):
            names.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            names.add(node.attr.lower())
        elif isinstance(node, ast.arg):
            names.add(node.arg.lower())
        elif isinstance(node, ast.FunctionDef):
            names.add(node.name.lower())
    assert not [name for name in names if any(word in name for word in ("opioid", "naloxone", "spo2", "saturation", "sbp", "gcs"))]


def test_no_family_declares_the_amendment_in_its_committed_profile():
    for name, build in FAMILIES.items():
        _, _, profile = build()
        assert profile.amendment_2 is None, name
