"""PHASE2_AMENDMENT_1: los artefactos sucesores -- documentos generados (A6), golden (A7) y serializacion (A8).

Nada historico se regenera ni se reescribe. Cada documento historico y el golden historico siguen reproduciendose
desde los archivos vivos bajo la vista del cierre (sus propias pruebas). Aqui se fija lo OTRO: el valor que los
MISMOS generadores dan sobre el arbol enmendado, registrado como sucesor con version explicita, y la unica
diferencia admitida respecto del historico.

Todas las pruebas leen el arbol real, sin la vista previa de certificacion del arnes.
"""
import dataclasses
import hashlib
import json
import sys
import types
from pathlib import Path

import pytest

from clinical_core import amendment_1 as a1
from clinical_core import blood_anchors as ba
from clinical_core import blood_probes as bp
from clinical_core import calibration, decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import integration as ig
from clinical_core.shadow import GOLDEN, golden_report
from clinical_core.state import Anchors, RhythmState

pytestmark = pytest.mark.real_core_lineage
ROOT = Path(__file__).resolve().parent
RECORD = json.loads((ROOT / "docs" / "revision" / "PHASE2_AMENDMENT_1.json").read_text(encoding="utf-8"))
ARTIFACTS = RECORD["successor_artifacts"]
NEW = a1.NEW_PROFILE_FIELD
GENERATORS = {"decision_pack": decision_pack.pack_digest, "lactate_slice": lactate_slice.slice_digest,
              "blood_anchors": ba.anchors_digest, "blood_probes": bp.probes_digest}


def _sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


# A6: los cuatro documentos "generados del codigo actual" -----------------------------------------------------

def test_the_record_names_exactly_the_four_generated_documents():
    assert sorted(ARTIFACTS["generated_documents"]) == sorted(GENERATORS)


@pytest.mark.parametrize("name", sorted(GENERATORS))
def test_a_generated_document_keeps_its_historical_value_and_gains_a_versioned_successor(name):
    stated = ARTIFACTS["generated_documents"][name]
    historical, successor = stated["PHASE2_CLOSURE"], stated["PHASE2_AMENDMENT_1"]
    assert historical != successor and len(historical) == len(successor) == 64
    # el sucesor es lo que el generador da sobre el arbol enmendado, y solo eso
    assert GENERATORS[name]() == successor
    # el historico sigue saliendo de los archivos vivos, por la reversion declarada
    with a1.closure_view():
        assert GENERATORS[name]() == historical
    assert GENERATORS[name]() == successor, "la vista del cierre no se restauro"
    # el documento historico no se regenero: dice su digesto de cierre, no el sucesor, y sus bytes son los fijados
    data = json.loads((ROOT / stated["historical_data"]).read_text(encoding="utf-8"))
    document = (ROOT / stated["historical_document"]).read_text(encoding="utf-8")
    assert data[stated["digest_key"]] == historical and historical in document
    assert successor not in document and successor not in json.dumps(data)
    assert _sha(stated["historical_document"]) == stated["historical_document_sha256"]
    assert _sha(stated["historical_data"]) == stated["historical_data_sha256"]
    assert stated["historical_document_rewritten"] is False


INPUTS = {"decision_pack": decision_pack.pack_sources, "lactate_slice": lactate_slice.slice_sources,
          "blood_anchors": lactate_slice.slice_sources, "blood_probes": lactate_slice.slice_sources}


@pytest.mark.parametrize("name", sorted(GENERATORS))
def test_a_generated_digest_moves_only_because_declared_sources_moved(name):
    """La causa del digesto nuevo, RECALCULADA: las entradas del generador sobre el arbol enmendado frente a las
    mismas bajo la vista del cierre. Se mueven las fuentes que esta etapa declara, y ninguna otra."""
    live = INPUTS[name]()
    with a1.closure_view():
        closure = INPUTS[name]()
    moved = sorted(source for source in set(live) | set(closure) if live.get(source) != closure.get(source))
    stated = ARTIFACTS["generated_documents"][name]["inputs"]
    assert moved == stated["sources_that_moved"] and stated["digested_sources"] == len(live)
    assert moved and set(moved) <= set(a1.REVERSAL) | set(a1.OWN)
    assert set(a1.REVERSAL) <= set(moved)                    # las dos fuentes cambiadas entran en los cuatro
    assert sorted(set(live) - set(closure)) == [s for s in a1.OWN if s in live]     # y solo se anade la etapa


def test_the_calibration_freeze_digest_did_not_move():
    stated = ARTIFACTS["calibration_freeze_digest"]
    assert stated["unchanged"] is True and stated["PHASE2_CLOSURE"] == stated["PHASE2_AMENDMENT_1"]
    assert calibration.frozen_digest() == stated["PHASE2_AMENDMENT_1"]
    with a1.closure_view():
        assert calibration.frozen_digest() == stated["PHASE2_CLOSURE"]


# A7: el golden -----------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def goldens():
    live = json.loads(json.dumps(golden_report(), allow_nan=False))
    return live, json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_the_historical_golden_was_not_rewritten():
    stated = ARTIFACTS["golden"]
    assert stated["historical_golden_rewritten"] is False
    assert _sha(stated["historical_golden"]) == stated["historical_golden_sha256"]
    assert NEW not in GOLDEN.read_text(encoding="utf-8")


def test_every_behavioural_block_of_the_golden_is_identical_on_the_amended_core(goldens):
    live, historical = goldens
    stated = ARTIFACTS["golden"]
    assert sorted(live) == sorted(historical) == stated["blocks"] and len(stated["blocks"]) == 9
    identical = sorted(block for block in historical if live[block] == historical[block])
    assert identical == stated["blocks_identical_on_the_amended_core"] and len(identical) == 8
    assert sorted(set(historical) - set(identical)) == stated["blocks_that_differ"] == ["parameters"]
    assert live["scenarios"] == historical["scenarios"] and live["differences"] == historical["differences"]
    assert stated["behavioural_blocks_identical"] is True


def _golden_difference(live: dict, historical: dict) -> dict:
    """Lo que separa un golden del historico, bloque a bloque y entrada a entrada."""
    lp, hp = live.get("parameters", {}), historical.get("parameters", {})
    return {"blocks_that_differ": sorted(b for b in set(live) | set(historical) if live.get(b) != historical.get(b)),
            "added": {name: lp[name] for name in sorted(lp) if name not in hp},
            "removed": sorted(name for name in hp if name not in lp),
            "changed": sorted(name for name in hp if name in lp and lp[name] != hp[name])}


def _is_the_declared_difference(difference: dict) -> bool:
    stated = ARTIFACTS["golden"]["parameters"]
    return (difference["blocks_that_differ"] == ARTIFACTS["golden"]["blocks_that_differ"] == ["parameters"]
            and difference["added"] == stated["added"] and list(difference["added"]) == [NEW]
            and difference["removed"] == stated["removed"] == []
            and difference["changed"] == stated["changed"] == [])


def test_the_only_golden_difference_is_one_registry_entry_for_the_new_control(goldens):
    live, historical = goldens
    stated = ARTIFACTS["golden"]["parameters"]
    difference = _golden_difference(live, historical)
    assert _is_the_declared_difference(difference), difference
    assert difference["added"] == {NEW: list(dv.PARAMETERS[NEW])}
    assert (len(historical["parameters"]), len(live["parameters"])) == (
        stated["PHASE2_CLOSURE_entries"], stated["PHASE2_AMENDMENT_1_entries"]) == (70, 71)
    assert live["parameters"][NEW][0] == "provisional"


def test_the_current_golden_expectation_is_versioned_and_recomputes(goldens):
    live, historical = goldens
    stated = ARTIFACTS["golden"]

    def canonical(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode("utf-8")).hexdigest()

    assert canonical(live) == stated["PHASE2_AMENDMENT_1_golden_sha256"]
    assert canonical(historical) == stated["PHASE2_CLOSURE_golden_canonical_sha256"]
    assert stated["PHASE2_AMENDMENT_1_golden_sha256"] != stated["PHASE2_CLOSURE_golden_canonical_sha256"]
    # y quitando la unica entrada declarada, el golden vivo ES el historico
    without = {**live, "parameters": {k: v for k, v in live["parameters"].items() if k != NEW}}
    assert without == historical


CORRUPTIONS = {
    "an_undeclared_registry_entry": lambda g: g["parameters"].update(undeclared_control=["provisional", "x"]),
    "a_changed_registry_entry": lambda g: g["parameters"].update(
        respiratory_quotient=["provisional", "restated by nobody"]),
    "a_removed_registry_entry": lambda g: g["parameters"].pop("respiratory_quotient"),
    "the_new_entry_restated": lambda g: g["parameters"].update({NEW: ["faculty-approved", "not what the core says"]}),
    "a_behavioural_block_moved": lambda g: g["scenarios"].update(undeclared_scenario={}),
    "a_block_added": lambda g: g.update(undeclared_block={}),
    "no_difference_at_all": lambda g: g["parameters"].pop(NEW),
}


@pytest.mark.parametrize("corruption", sorted(CORRUPTIONS))
def test_negative_control_the_golden_expectation_refuses_anything_but_the_declared_difference(goldens, corruption):
    """El control: la expectativa no es "lo que el golden contenga". Cada corrupcion de una COPIA del golden vivo
    deja de ser la diferencia declarada, por la misma funcion que acepta el golden real."""
    live, historical = goldens
    assert "respiratory_quotient" in live["parameters"]
    corrupted = json.loads(json.dumps(live))
    CORRUPTIONS[corruption](corrupted)
    assert _is_the_declared_difference(_golden_difference(live, historical)) is True
    assert _is_the_declared_difference(_golden_difference(corrupted, historical)) is False


def test_no_committed_profile_declares_the_new_control():
    """Por eso el comportamiento por omision es exacto: ningun perfil comprometido lo enciende."""
    from clinical_core import distributive_tone as dt
    assert getattr(dv.DEFAULT_PROFILE, NEW) is None
    profiles = dt.committed_profiles()
    assert profiles and all(getattr(profile, NEW) is None for profile in profiles.values())
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        if path.name in ("derived.py", "amendment_1.py"):
            continue
        assert NEW not in path.read_text(encoding="utf-8"), path.name


# A8: serializacion -------------------------------------------------------------------------------------------

ANCHORS = Anchors(case_id="gi_bleed_72f", sbp=98.0, dbp=62.0, hr=112.0, spo2=96.0, respiratory_rate=24.0, crt_s=4.0,
                  lactate=3.4, hb=6.4, glucose=130.0, k=4.1, fio2=0.21, rhythm=RhythmState.sinus(112.0),
                  consciousness_level=0)


@pytest.fixture()
def closure_core():
    """El derived.py DEL CIERRE (probado por la reversion), ejecutado como modulo propio junto al vivo."""
    name = "clinical_core._derived_at_phase2_closure_for_serialization"
    module = types.ModuleType(name)
    module.__package__ = "clinical_core"
    sys.modules[name] = module
    try:
        exec(compile(a1.p2x1a_text("clinical_core/derived.py"), "derived_at_phase2_closure.py", "exec"),
             module.__dict__)
        yield module
    finally:
        sys.modules.pop(name, None)


def _profile_kwargs(data: dict) -> dict:
    out = dict(data)
    for name in ("pressure_levels", "oxygen_levels"):
        out[name] = tuple(tuple(pair) for pair in out[name])
    return out


def test_the_closure_core_is_reconstructed_whole(closure_core):
    """A5: la clase que las pruebas historicas no encontraban existe en cuanto la reconstruccion no aborta."""
    names = {field.name for field in dataclasses.fields(closure_core.CoreProfile)}
    assert NEW not in names and len(names) == len(dataclasses.fields(dv.CoreProfile)) - 1 == 70
    assert names | {NEW} == {field.name for field in dataclasses.fields(dv.CoreProfile)}


def test_backward_an_artifact_written_before_the_amendment_reads_unchanged(closure_core):
    written_at_closure = closure_core.CoreProfile().to_dict()
    assert NEW not in written_at_closure
    artifact = {"anchors": ANCHORS.to_dict(), "profile": written_at_closure, "minutes": 5, "contributors": []}
    _anchors, _contributors, minutes, profile = ig.scenario_from_dict(json.loads(json.dumps(artifact)))
    assert minutes == 5 and profile == dv.DEFAULT_PROFILE and getattr(profile, NEW) is None
    assert RECORD["serialization"]["BACKWARD_READ_COMPATIBLE"] is True


def test_forward_the_closure_core_refuses_an_artifact_written_by_the_amended_core(closure_core):
    written_now = ig.scenario_to_dict(ANCHORS, (), 5)["profile"]
    assert NEW in written_now and written_now[NEW] is None
    with pytest.raises(TypeError) as refused:
        closure_core.CoreProfile(**_profile_kwargs(written_now))
    assert NEW in str(refused.value)
    # la UNICA razon es la clave nueva: sin ella el mismo artefacto se lee en el nucleo del cierre
    readable = {k: v for k, v in written_now.items() if k != NEW}
    assert closure_core.CoreProfile(**_profile_kwargs(readable)) == closure_core.CoreProfile()
    assert RECORD["serialization"]["FORWARD_READ_COMPATIBILITY"] == "NOT_PROVIDED"


def test_the_amended_core_round_trips_a_declared_share():
    from clinical_core import opioid_migration as om
    profile = dataclasses.replace(om.profile(), respiratory_quotient=0.8, **{NEW: 0.03})
    written = json.loads(json.dumps(ig.scenario_to_dict(ANCHORS, (), 5, profile)))
    assert written["profile"][NEW] == 0.03
    assert ig.scenario_from_dict(written)[3] == profile


def test_the_record_invents_no_compatibility_guarantee():
    stated = RECORD["serialization"]
    assert set(stated) == {"BACKWARD_READ_COMPATIBLE", "backward_note", "FORWARD_READ_COMPATIBILITY", "forward_note"}
    assert "No forward-compatibility guarantee existed" in stated["forward_note"]
