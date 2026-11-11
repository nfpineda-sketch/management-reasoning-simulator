"""P3-172 / P3-173 / P3-173A: la Enmienda 2 certificada se integra en la Fase 3, sin autoridad y sin efecto en el residente.

Tres cosas se fijan aqui, cada una con la medida que la sostiene:

1. LINAJE: tras la integracion el arbol ``clinical_core/`` es el del candidato certificado (digesto ``a0af7d08...``), la
   Enmienda 1 y el cierre historico se reconstruyen exactos desde los archivos vivos, y la compuerta real reporta
   CERTIFIED (sin la vista previa del arnes: marcador ``real_core_lineage``).
2. PI-1 (auditoria previa): los dos digestos de congelacion de la Enmienda 1 que ya no se recalculaban sobre el arbol de
   la Enmienda 1 con el cierre anidado (``closure_guard_P2X1A``, ``tone_domain``) son un ARTEFACTO DE REPRESENTACION DEL
   ARNES, no una inconsistencia de linaje: la vista de cierre de la Enmienda 1 no sabe que la Enmienda 2 modifico
   ``state.py`` e ``integration.py`` (la Enmienda 1 nunca los toco), de modo que los lee crudos. Bajo la vista de cierre
   de la Enmienda 2 recalculan exactamente a su valor registrado. Aqui se fija QUE archivos difieren y POR QUE.
3. PI-2 (apagado por omision): con ``amendment_2 = None`` la evolucion fisica, todas las cantidades derivadas (con el
   nivel de consciencia) y el estado auxiliar son los de la Enmienda 1, estado por estado: los 10 digestos de abajo se
   midieron sobre el nucleo de la Enmienda 1 (cabeza de la Fase 3 ``3e911ea``) ANTES de integrar. No se exige identidad
   de bytes entre esquemas distintos: el diccionario del perfil gana UNA clave (``amendment_2: null``), y eso se declara.
"""
import dataclasses
import hashlib
import json

import pytest

import runtime_shadow as rs
import runtime_shadow_evidence as ev
from clinical_core import acs_migration as an, acs_reference as ar, amendment_1 as a1, amendment_2 as a2
from clinical_core import asthma_migration as sm, asthma_reference as sr, blood_anchors as ba
from clinical_core import blood_fluid_calibration as bf, closure_guard as cg, derived as dv, edema_migration as pe
from clinical_core import edema_reference as er, embolism_migration as em, embolism_reference as mr
from clinical_core import gas_exchange_architecture as go, integration as ig, opioid_migration as un
from clinical_core import opioid_reference as orf, respiratory_mechanics as mc, state as st, tone_domain as td

CERTIFIED_DIGEST = "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
AMENDMENT_1_DIGEST = "10b45ce2967ea55afccb35291afb5bb1f7f1b01eb4a253e6a0736c02a5878635"
CLOSURE_DIGEST = "22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a"

#: Medidos sobre el nucleo de la Enmienda 1 (cabeza de la Fase 3 3e911ea), con el perfil comprometido (apagado): por corrida,
#: (numero de estados, sha256 de la lista [estado.to_dict(), derivadas] serializada con claves ordenadas).
DEFAULT_OFF_BASELINE = {
    "acs": (121, "21411c453b07fa786471b3f66d67dcfd413359d1fe6f1ccaa7f672b30319af69"),
    "asthma": (121, "c9c35ef2adabd402494aa621e701e77a0ce68da4efee3922c6070be9a5e53f8f"),
    "edema": (121, "9057d9e766b83caede2288717855b6ade0a993c189681f75dd6ac02a256f14b1"),
    "embolism": (121, "eeef8cd1566333f79aa4c2486a4a95bfb6cab06d91126892d62943e2d2d80789"),
    "gi_bleed_57m/untreated/None": (121, "03517542f7edff74bb27ac2a0d7bfe99c07f787ef72f03b18de43fdb26cf0b49"),
    "gi_bleed_57m/untreated_ig_run": (151, "841a52ea50549307c8da5460aa675e9903758513f32c4c0f6aa37d16e1b056d6"),
    "gi_bleed_72f/untreated/None": (121, "144c10b5fb5d39b0ee91c5d39edcfbb9820ee351e0a293363b91a4e2774afb76"),
    "gi_bleed_72f/untreated_ig_run": (151, "9277c52790336647c02d65613156173c6473716f62c48335ca4f2e11ba25e40d"),
    "opioid_35m": (61, "60737efb40ef1f306b70b0b2c8b46c2c813ff1437dd5eade710a9d8943a8267f"),
    "opioid_67f": (61, "f55f7672e7ad9fcd5c852073535554c05d9e860610946a17b8e12c0cc13f6e5a"),
}


# -- 1. linaje -----------------------------------------------------------------------------------------------------------

@pytest.mark.real_core_lineage
def test_the_integrated_core_is_the_certified_amendment_2_and_both_predecessors_reconstruct_exactly():
    assert a2.amended_core_digest_now() == CERTIFIED_DIGEST == rs.CORE_LINEAGE[-1].digest
    assert a2.amendment_1_verifies() == {"digest_recomputes": True, "reversal_proven": True}
    assert rs.CORE_LINEAGE[1].digest == AMENDMENT_1_DIGEST
    assert a2.historical_closure_verifies() == {"reversal_proven": True, "common_untouched": True, "touched": [],
                                                "closure_digest_recomputes": True, "closure_record_states_it": True}
    assert rs.PHASE2_DIGEST == CLOSURE_DIGEST
    verdict = ev.core_lineage_verdict()
    assert verdict["ok"] is True and verdict["status"] == "CERTIFIED" and verdict["active_core"] == "PHASE2_AMENDMENT_2"
    assert verdict["failed"] == [] and verdict["active_core_recomputes"] and verdict["historical_closure_verifies"]


@pytest.mark.real_core_lineage
def test_the_certified_record_binds_the_candidate_and_no_historical_record_or_digest_was_redefined():
    record = json.loads((_root() / "docs/revision/PHASE2_AMENDMENT_2.json").read_text(encoding="utf-8"))
    certification = record["certification"]
    assert certification["status"] == "CERTIFIED" and certification["certified_core_digest"] == CERTIFIED_DIGEST
    assert certification["candidate_head"] == "ad7bf815e57e63c892ad2be7a63c5a8302a3e688"
    assert record["amended"]["core_digest"] == CERTIFIED_DIGEST
    assert record["predecessor_amendment"]["core_digest"] == AMENDMENT_1_DIGEST
    assert record["historical_closure"]["phase2_digest"] == CLOSURE_DIGEST
    # los digestos registrados por los paquetes cerrados siguen siendo los que ellos registraron
    closure_record = json.loads(a1.CLOSURE_RECORD.read_text(encoding="utf-8"))
    assert closure_record["freeze_digests"]["closure_guard_P2X1A"] == a1.P2X1A_FREEZE_DIGEST
    first = json.loads((_root() / "docs/revision/PHASE2_AMENDMENT_1.json").read_text(encoding="utf-8"))
    assert first["amended"]["core_digest"] == AMENDMENT_1_DIGEST


def _root():
    from pathlib import Path
    return Path(__file__).resolve().parent


# -- 2. PI-1: los dos digestos de congelacion --------------------------------------------------------------------------------

def _freeze_files(view):
    """El mapa archivo -> sha256 que ambos digestos de congelacion hashean (``bf.freeze_sources``), bajo una vista."""
    with view():
        return bf.freeze_sources()


def test_pi1_both_freeze_digests_recompute_exactly_under_the_closure_view_of_the_stage_that_knows_the_whole_chain():
    recorded = json.loads(a1.CLOSURE_RECORD.read_text(encoding="utf-8"))["freeze_digests"]
    with a2.closure_view():
        assert cg.freeze_digest() == recorded["closure_guard_P2X1A"] == a1.P2X1A_FREEZE_DIGEST
        assert td.freeze_digest() == recorded["tone_domain_on_the_live_tree"]


def test_pi1_the_nested_first_amendment_view_misreads_exactly_the_two_files_it_never_knew_were_changed(monkeypatch):
    """CLASIFICACION B, ARTEFACTO DE REPRESENTACION DEL ARNES. Dentro de ``amendment_1_tree`` (el arbol como lo dejo la
    Enmienda 1), la vista de cierre PROPIA de la Enmienda 1 solo tiene reversiones para los archivos que la Enmienda 1
    modifico (derived.py, decision_pack.py): ``state.py`` e ``integration.py`` los lee crudos del disco, y ahi esta el texto
    de la Enmienda 2. Son exactamente esos dos los que difieren del cierre; nada mas."""
    closure = _freeze_files(a2.closure_view)
    with monkeypatch.context() as patch:
        a2.amendment_1_tree(patch)
        nested = _freeze_files(a1.closure_view)
    assert closure.keys() == nested.keys()
    assert sorted(path for path in closure if closure[path] != nested[path]) == ["clinical_core/integration.py",
                                                                                 "clinical_core/state.py"]
    assert "clinical_core/state.py" not in a1.REVERSAL and "clinical_core/integration.py" not in a1.REVERSAL
    for relative in ("clinical_core/state.py", "clinical_core/integration.py"):
        live = hashlib.sha256((_root() / relative).read_bytes()).hexdigest()
        assert nested[relative] == live and closure[relative] != live        # el anidado lee el texto VIVO (el de la Enmienda 2)
        assert relative in a2.REVERSAL                                       # y la Enmienda 2 SI declara su reversion


def test_pi1_the_first_amendments_own_certified_digest_still_recomputes_on_its_own_tree(monkeypatch):
    with monkeypatch.context() as patch:
        a2.amendment_1_tree(patch)
        assert a1.amended_core_digest_now() == AMENDMENT_1_DIGEST
        assert a1.historical_closure_verifies()["closure_digest_recomputes"] is True


# -- 3. PI-2: apagado por omision ------------------------------------------------------------------------------------------------

def _gi_runs():
    runs = {}
    for case in ("gi_bleed_57m", "gi_bleed_72f"):
        anchors, base, values = go.ba.setup(case)
        profile = go._acid(base)
        scenario, volume = go.GI_SCENARIOS[0]
        items = go.ba.contributors(case, scenario, values, volume)
        runs[f"{case}/{scenario}/{volume}"] = (lambda i=items, a=anchors, p=profile: mc.course(i, 120, a, p)[0],
                                               anchors, profile)
    for case in ("gi_bleed_57m", "gi_bleed_72f"):
        anchors, profile, values = ba.setup(case)
        runs[f"{case}/untreated_ig_run"] = (
            lambda c=case, a=anchors, p=profile, v=values: ig.run(a, ba.contributors(c, "untreated", v), 150, p),
            anchors, profile)
    return runs


def _all_runs():
    runs = _gi_runs()
    a, p = ar.anchors(), ar.common_profile()
    runs["acs"] = (lambda a=a, p=p: an.course(an.writers(), 120, a, p)[0], a, p)
    a, p = er.anchors(), pe.profile()
    runs["edema"] = (lambda a=a, p=p: pe.course((pe.writer(),), 120, a, p)[0], a, p)
    a, p = mr.anchors(), em.profile()
    runs["embolism"] = (lambda a=a, p=p: em.course(em.writers(), 120, a, p)[0], a, p)
    a, p = sr.anchors(), sm.profile()
    runs["asthma"] = (lambda a=a, p=p: sm.course((sm.obstruction(),), 120, a, p)[0], a, p)
    for case in ("opioid_35m", "opioid_67f"):
        a, p = orf.anchors(case), orf.common_profile()
        runs[case] = (lambda a=a, p=p: un.course((un.depression(),), a, p)[0], a, p)
    return runs


def _measure(run, anchors, profile):
    result = run()
    pairs = list(zip(result.states, result.derived())) if hasattr(result, "states") else [
        (s, dv.derive(s, anchors, profile)) for s in result]
    rows = [{"state": s.to_dict(), "derived": dataclasses.asdict(d)} for s, d in pairs]
    return len(rows), hashlib.sha256(json.dumps(rows, sort_keys=True, default=repr).encode()).hexdigest()


def test_pi2_default_off_reproduces_the_first_amendments_states_and_every_derived_quantity_exactly():
    runs = _all_runs()
    assert set(runs) == set(DEFAULT_OFF_BASELINE)
    for name, (run, anchors, profile) in sorted(runs.items()):
        assert profile.amendment_2 is None, name
        assert _measure(run, anchors, profile) == DEFAULT_OFF_BASELINE[name], name


def test_pi2_the_default_off_schema_difference_is_exactly_one_profile_key_and_no_auxiliary_key():
    """Lo que cambia entre esquemas, dicho con precision: el diccionario del perfil gana ``amendment_2`` (None), y el
    estado auxiliar NO gana la memoria nueva mientras es None. Ni el estado ni las derivadas cambian (prueba anterior)."""
    profile = dv.DEFAULT_PROFILE.to_dict()
    assert len(profile) == 72 and profile["amendment_2"] is None
    assert len(st.AUXILIARY_FIELDS) == 10 and "systemic_encephalopathy_burden" not in st.AUXILIARY_FIELDS
    state = _all_runs()["gi_bleed_72f/untreated_ig_run"][0]().states[-1]
    assert sorted(state.aux.to_dict()) == sorted(st.AUXILIARY_FIELDS)


# -- 173A: seguridad ---------------------------------------------------------------------------------------------------------

def test_173a_the_core_still_has_no_runtime_authority_and_no_committed_profile_declares_the_amendment():
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    for name, (_run, _anchors, profile) in _all_runs().items():
        assert profile.amendment_2 is None, name
    assert dv.DEFAULT_PROFILE.amendment_2 is None
