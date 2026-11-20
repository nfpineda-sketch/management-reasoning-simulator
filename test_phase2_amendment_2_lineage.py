"""PHASE2_AMENDMENT_2: el linaje certificado del nucleo y la compuerta de digesto del runtime.

La compuerta dejo de comparar el arbol vivo con UNA constante. Ahora exige cuatro cosas a la vez:

  1. el cierre historico sigue verificando (desde los archivos vivos, por la reversion declarada);
  2. el digesto vivo es miembro del linaje;
  3. ese miembro esta CERTIFICADO (el cierre por construccion; un sucesor solo por su registro ligado);
  4. los archivos recalculan al digesto de ese miembro, tambien por la definicion del propio sucesor.

Cada una tiene aqui su control negativo. (PHASE2_AMENDMENT_3: las pruebas de la compuerta sobre el nucleo VIVO viven ahora en
test_phase2_amendment_3_lineage.py; este archivo conserva lo que es del segundo sucesor, leido sobre SU arbol.) TODAS las pruebas leen el linaje real: ninguna usa la vista previa de
certificacion del arnes (marcador ``real_core_lineage``).
"""
import dataclasses
import json
import re
from pathlib import Path

import pytest
import reader_succession as succession

import runtime_shadow as rs
import runtime_shadow_evidence as ev
from clinical_core import amendment_1 as a1
from clinical_core import amendment_2 as a2
from clinical_core import amendment_3 as a3

pytestmark = pytest.mark.real_core_lineage
ROOT = Path(__file__).resolve().parent
RECORD = ROOT / "docs" / "revision" / "PHASE2_AMENDMENT_2.json"
CLOSURE, FIRST, AMENDMENT = rs.CORE_LINEAGE[0], rs.CORE_LINEAGE[1], rs.CORE_LINEAGE[2]


@pytest.fixture(autouse=True, scope="module")
def _second_amendment_tree():
    """PHASE2_AMENDMENT_3: this file tests what the SECOND amendment left, so it reads the tree as that amendment left it
    (the third stage's insertions reversed, its reader, memory, change and writer hidden). The live tree has its own tests."""
    with pytest.MonkeyPatch.context() as patch:
        a3.amendment_2_tree(patch)
        succession.install(patch)
        yield


@pytest.fixture(autouse=True)
def _fresh_cache():
    ev.core_lineage_cache_clear()
    yield
    ev.core_lineage_cache_clear()


def _record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _evidence(**changes) -> dict:
    """Un bloque de certificacion COMPLETO para la entrada de la enmienda: lo minimo que hace valer un CERTIFIED."""
    block = {"status": rs.CERTIFIED, "certified_core_digest": AMENDMENT.digest, "candidate_head": "a" * 40,
             "full_suite": {"tests": 11000, "failures": 0, "errors": 0, "skipped": 93},
             "regressions": {"passed": 12, "failed": 0}}
    block.update(changes)
    return block


def _record_at(tmp_path, name, **top) -> "rs.CoreVersion":
    """La entrada de la enmienda apuntando a una copia del registro con los campos de ``top`` reemplazados."""
    record = _record()
    record.update(top)
    path = tmp_path / name
    path.write_text(json.dumps(record), encoding="utf-8")
    return dataclasses.replace(AMENDMENT, record=str(path))


def _certified(monkeypatch):
    """El estado que tendra tras la promocion, para aislar las OTRAS tres condiciones."""
    monkeypatch.setattr(ev, "successor_status", lambda entry: rs.CERTIFIED)


# El registro de linaje ---------------------------------------------------------------------------------

def test_the_lineage_is_immutable_and_roots_at_the_historical_closure():
    assert isinstance(rs.CORE_LINEAGE, tuple) and len(rs.CORE_LINEAGE) == 4
    assert dataclasses.is_dataclass(CLOSURE) and CLOSURE.__dataclass_params__.frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        AMENDMENT.digest = "0" * 64
    assert (CLOSURE.version_id, CLOSURE.parent) == ("PHASE2_CLOSURE", None)
    assert CLOSURE.head == rs.PHASE2_CLOSURE_HEAD == "d2cca46626ed5d45a792ec9456d46fb75fe87731"
    assert CLOSURE.digest == rs.PHASE2_DIGEST == "22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a"
    assert (FIRST.version_id, FIRST.parent, FIRST.reversal) == ("PHASE2_AMENDMENT_1", "PHASE2_CLOSURE",
                                                                "clinical_core.amendment_1")
    assert FIRST.digest == "10b45ce2967ea55afccb35291afb5bb1f7f1b01eb4a253e6a0736c02a5878635"
    assert (AMENDMENT.version_id, AMENDMENT.parent) == ("PHASE2_AMENDMENT_2", "PHASE2_AMENDMENT_1")
    assert AMENDMENT.reversal == "clinical_core.amendment_2"
    assert not any("status" in field.name for field in dataclasses.fields(rs.CoreVersion))


def test_the_amended_digest_is_new_and_is_what_the_files_recompute_to():
    assert AMENDMENT.digest not in (CLOSURE.digest, FIRST.digest)
    assert AMENDMENT.digest == a2.amended_core_digest_now()   # the second amendment's digest, by ITS definition
    record = _record()
    assert record["amended"]["core_digest"] == AMENDMENT.digest
    assert record["amended"]["changed_sources"] == sorted(a2.REVERSAL) == [
        "clinical_core/decision_pack.py", "clinical_core/derived.py", "clinical_core/integration.py",
        "clinical_core/state.py"]
    assert record["amended"]["declared_insertions"] == {k: len(v) for k, v in a2.REVERSAL.items()}
    assert record["amended"]["added_sources"] == sorted(a2.OWN)
    assert record["amended"]["removed_sources"] == []
    assert record["amended"]["clinical_core_modules"] == len(a2.live_core_sources()) == 144
    assert (record["amendment"], record["parent"]) == (AMENDMENT.version_id, AMENDMENT.parent)


def test_the_two_earlier_cores_still_recompute_from_the_live_tree():
    assert a2.amendment_1_digest_now() == FIRST.digest == a2.AMENDMENT_1_DIGEST
    assert a2.amendment_1_verifies() == {"digest_recomputes": True, "reversal_proven": True}
    standing = a2.historical_closure_verifies()
    assert standing == {"reversal_proven": True, "common_untouched": True, "touched": [],
                        "closure_digest_recomputes": True, "closure_record_states_it": True}
    assert a2.historical_closure_digest_now() == rs.PHASE2_DIGEST
    assert a2.non_regression()["pass"] is True


# El cierre historico, intacto ---------------------------------------------------------------------------


# La compuerta real, tal como esta el registro -----------------------------------------------------------

def test_an_unlisted_core_is_named_as_such_and_naming_it_authorizes_nothing(monkeypatch):
    monkeypatch.setattr(ev, "phase2_digest_now", lambda: "ab" * 32)
    assert rs.active_core() == {"core_version": "NOT_IN_THE_LINEAGE", "core_digest": "ab" * 32}
    assert ev.core_lineage_ok() is False


def test_the_three_runtime_sites_ask_the_lineage_and_never_compare_one_constant():
    for name in ("runtime_shadow_evidence.py", "runtime_authority.py"):
        source = (ROOT / name).read_text(encoding="utf-8")
        assert not re.search(r"phase2_digest_now\(\)\s*[!=]=\s*rs\.PHASE2_DIGEST", source), name
    assert (ROOT / "runtime_shadow_evidence.py").read_text(encoding="utf-8").count("core_lineage_ok()") >= 3
    assert '"phase2_digest": ev.core_lineage_ok()' in (ROOT / "runtime_authority.py").read_text(encoding="utf-8")


def test_the_certification_preview_is_an_explicit_test_plugin_and_nothing_loads_it():
    flag, plugin = "MRS_CORE_CERTIFICATION_PREVIEW", "test_core_certification_preview"
    assert flag in (ROOT / f"{plugin}.py").read_text(encoding="utf-8")
    for path in sorted(ROOT.glob("*.py")) + sorted((ROOT / "clinical_core").rglob("*.py")):
        if path.name.startswith("test_"):
            continue                                    # codigo de pruebas: el plugin y quienes lo prueban
        text = path.read_text(encoding="utf-8")
        assert flag not in text, path.name              # ningun modulo del runtime lee la bandera
        assert plugin not in text or path.name == "conftest.py", path.name
    harness = (ROOT / "conftest.py").read_text(encoding="utf-8")
    # conftest.py lo nombra en un comentario y no lo carga, ni lee la capa de la Fase 3
    assert "pytest_plugins" not in harness and "import " + plugin not in harness
    assert "runtime_shadow" not in harness and "runtime_authority" not in harness
    assert getattr(ev.successor_status, "real", None) is None        # esta prueba lee el estado real


# Los cuatro controles negativos -------------------------------------------------------------------------

def test_nc2b_a_record_certifies_only_the_digest_it_states(tmp_path, monkeypatch):
    record = _record()
    record["certification"] = _evidence()
    honest = tmp_path / "honest.json"
    honest.write_text(json.dumps(record), encoding="utf-8")
    assert ev.successor_status(dataclasses.replace(AMENDMENT, record=str(honest))) == rs.CERTIFIED
    for mutate in (lambda r: r["amended"].update(core_digest="0" * 64),
                   lambda r: r.update(amendment="SOMETHING_ELSE"),
                   lambda r: r["historical_closure"].update(phase2_digest="0" * 64),
                   lambda r: r["historical_closure"].update(head="0" * 40)):
        forged = json.loads(json.dumps(record))
        mutate(forged)
        path = tmp_path / "forged.json"
        path.write_text(json.dumps(forged), encoding="utf-8")
        assert ev.successor_status(dataclasses.replace(AMENDMENT, record=str(path))) == \
            "RECORD_NOT_BOUND_TO_THE_LINEAGE"
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    assert ev.successor_status(dataclasses.replace(AMENDMENT, record=str(tmp_path / "broken.json"))) == "NO_RECORD"


def test_nc3b_a_tampered_closure_record_fails_closed(tmp_path, monkeypatch):
    _certified(monkeypatch)
    tampered = json.loads(a1.CLOSURE_RECORD.read_text(encoding="utf-8"))
    tampered["sources"]["clinical_core/derived.py"] = "0" * 64
    path = tmp_path / "closure.json"
    path.write_text(json.dumps(tampered), encoding="utf-8")
    monkeypatch.setattr(a1, "CLOSURE_RECORD", path)
    ev.core_lineage_cache_clear()
    with pytest.raises(AssertionError):
        a1.closure_sources()
    verdict = ev.core_lineage_verdict()
    assert verdict["ok"] is False and "historical_closure_verifies" in verdict["failed"]


def test_nc3c_an_undeclared_change_to_the_core_breaks_the_reversal():
    """La prueba de reversion solo acepta lo declarado: una linea de mas y el archivo ya no es el del cierre."""
    live = a2._live_text("clinical_core/derived.py")
    assert a2.proved("clinical_core/derived.py", live) is True
    assert a2.proved("clinical_core/derived.py", live + "\nUNDECLARED = 1\n") is False
    assert a2.proved("clinical_core/derived.py", live.replace("share * delta", "share * share * delta")) is False


def test_nc2c_one_word_is_not_a_promotion(tmp_path):
    """CERTIFIED vale solo con la evidencia de la certificacion: el digesto certificado, el commit candidato, una
    suite completa sin fallos ni errores y regresiones sin fallos. (Observacion de la revision adversarial.)"""
    assert ev.successor_status(_record_at(tmp_path, "full.json", certification=_evidence())) == rs.CERTIFIED
    lacking = [{"status": rs.CERTIFIED},
               _evidence(certified_core_digest="0" * 64), _evidence(certified_core_digest=None),
               _evidence(candidate_head="abc"), _evidence(candidate_head=None), _evidence(candidate_head="g" * 40),
               _evidence(full_suite={"tests": 11000, "failures": 1, "errors": 0}),
               _evidence(full_suite={"tests": 11000, "failures": 0, "errors": 3}),
               _evidence(full_suite={"tests": 0, "failures": 0, "errors": 0}),
               _evidence(full_suite={"tests": 11000, "errors": 0}),
               _evidence(full_suite={"tests": True, "failures": False, "errors": False}),
               _evidence(full_suite="11000 passed"), _evidence(full_suite=None),
               _evidence(regressions={"passed": 12, "failed": 1}), _evidence(regressions={"passed": 0, "failed": 0}),
               _evidence(regressions=None)]
    for number, block in enumerate(lacking):
        entry = _record_at(tmp_path, f"lacking{number}.json", certification=block)
        assert ev.successor_status(entry) == "CERTIFIED_WITHOUT_EVIDENCE", block
    # y solo CERTIFIED exige evidencia: los demas estados se leen tal cual, y ninguno abre la compuerta
    for status in (rs.CANDIDATE, "REVOKED", " CERTIFIED", "certified"):
        assert ev.successor_status(_record_at(tmp_path, "other.json", certification={"status": status})) == status


def test_nc2e_the_gate_answers_no_when_the_verdict_cannot_be_computed(monkeypatch):
    def broken():
        raise RuntimeError("no verdict")
    monkeypatch.setattr(ev, "core_lineage_verdict", broken)
    assert ev.core_lineage_ok() is False
    assert ev.core_lineage_reason() == "the common core lineage could not be evaluated"


def test_the_real_lineage_is_well_formed_and_only_the_closure_is_its_root():
    assert ev._lineage_well_formed() is True
    assert ev._is_the_historical_root(CLOSURE) is True and ev._is_the_historical_root(AMENDMENT) is False
    assert ev._is_the_historical_root(dataclasses.replace(CLOSURE)) is False      # una copia no es la entrada


def test_nc3d_a_duplicated_declared_insertion_does_not_reverse():
    """Cada insercion declarada debe aparecer exactamente una vez: dos veces no es el archivo declarado."""
    relative = "clinical_core/derived.py"
    live = a2._live_text(relative)
    for hunk, _before in a2.REVERSAL[relative]:
        assert live.count(hunk) == 1
        assert a2.proved(relative, live + "\n" + hunk) is False
        assert a2.proved(relative, live.replace(hunk, "")) is False


