"""PHASE2_AMENDMENT_2: el linaje certificado del nucleo y la compuerta de digesto del runtime.

La compuerta dejo de comparar el arbol vivo con UNA constante. Ahora exige cuatro cosas a la vez:

  1. el cierre historico sigue verificando (desde los archivos vivos, por la reversion declarada);
  2. el digesto vivo es miembro del linaje;
  3. ese miembro esta CERTIFICADO (el cierre por construccion; un sucesor solo por su registro ligado);
  4. los archivos recalculan al digesto de ese miembro, tambien por la definicion del propio sucesor.

Cada una tiene aqui su control negativo. TODAS las pruebas leen el linaje real: ninguna usa la vista previa de
certificacion del arnes (marcador ``real_core_lineage``).
"""
import dataclasses
import json
import re
from pathlib import Path

import pytest

import runtime_shadow as rs
import runtime_shadow_evidence as ev
from clinical_core import amendment_1 as a1
from clinical_core import amendment_2 as a2

pytestmark = pytest.mark.real_core_lineage
ROOT = Path(__file__).resolve().parent
RECORD = ROOT / "docs" / "revision" / "PHASE2_AMENDMENT_2.json"
CLOSURE, FIRST, AMENDMENT = rs.CORE_LINEAGE[0], rs.CORE_LINEAGE[1], rs.CORE_LINEAGE[-1]



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
    assert isinstance(rs.CORE_LINEAGE, tuple) and len(rs.CORE_LINEAGE) == 3
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
    assert AMENDMENT.digest == ev.phase2_digest_now() == a2.amended_core_digest_now()
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
    assert a2.historical_closure_digest_now() == rs.PHASE2_DIGEST == ev.historical_closure_digest_now()
    assert a2.non_regression()["pass"] is True





# El cierre historico, intacto ---------------------------------------------------------------------------











# La compuerta real, tal como esta el registro -----------------------------------------------------------

def test_the_real_gate_follows_the_recorded_status_and_nothing_else():
    status = _record()["certification"]["status"]
    assert status in (rs.CANDIDATE, rs.CERTIFIED)
    verdict = ev.core_lineage_verdict()
    assert verdict["active_core"] == "PHASE2_AMENDMENT_2" and verdict["status"] == status
    assert verdict["historical_closure_verifies"] and verdict["active_core_in_lineage"]
    assert verdict["active_core_recomputes"]
    if status == rs.CANDIDATE:
        assert verdict["ok"] is False and verdict["failed"] == ["active_core_certified"]
        assert ev.core_lineage_ok() is False
    else:
        assert verdict["ok"] is True and verdict["failed"] == []


def test_an_artifact_names_the_core_that_produced_it_beside_the_closure_it_roots_at():
    versions = rs.versions()
    assert versions["phase2_closure_head"] == rs.PHASE2_CLOSURE_HEAD and versions["phase2_digest"] == rs.PHASE2_DIGEST
    assert versions["core_version"] == "PHASE2_AMENDMENT_2"
    assert versions["core_digest"] == ev.phase2_digest_now() == AMENDMENT.digest != rs.PHASE2_DIGEST


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


def test_the_preview_upgrades_one_named_candidate_and_nothing_else(monkeypatch):
    """La vista previa, ejercitada a mano: solo CANDIDATE -> CERTIFIED y solo para la version nombrada."""
    import test_core_certification_preview as preview
    monkeypatch.setenv(preview.CORE_CERTIFICATION_PREVIEW_FLAG, "PHASE2_AMENDMENT_2")
    real = ev.successor_status
    session = preview._core_certification_preview.__wrapped__()
    next(session)
    try:
        previewed = ev.successor_status
        assert previewed.real is real
        monkeypatch.setattr(previewed, "real", previewed.real)         # deja el atributo como estaba al salir
        for status in ("NO_RECORD", "RECORD_NOT_BOUND_TO_THE_LINEAGE", "NO_STATUS", "REVOKED",
                       "CERTIFIED_WITHOUT_EVIDENCE", rs.CERTIFIED):
            assert _previewed_with(preview, status, AMENDMENT) == status
        assert _previewed_with(preview, rs.CANDIDATE, AMENDMENT) == rs.CERTIFIED
        other = dataclasses.replace(AMENDMENT, version_id="PHASE2_AMENDMENT_1")
        assert _previewed_with(preview, rs.CANDIDATE, other) == rs.CANDIDATE
    finally:
        next(session, None)
    assert ev.successor_status is real


def _previewed_with(preview, status, entry):
    """Lo que la vista previa devuelve cuando el estado REAL del registro es ``status``."""
    kept = ev.successor_status
    ev.successor_status = lambda _entry: status
    session = preview._core_certification_preview.__wrapped__()
    next(session)
    try:
        return ev.successor_status(entry)
    finally:
        next(session, None)
        ev.successor_status = kept


# Los cuatro controles negativos -------------------------------------------------------------------------

def test_nc1_a_digest_nobody_certified_is_refused(monkeypatch):
    _certified(monkeypatch)
    assert ev.core_lineage_ok() is True                               # el control: con todo en regla, abre
    monkeypatch.setattr(ev, "phase2_digest_now", lambda: "ab" * 32)
    verdict = ev.core_lineage_verdict()
    assert verdict["ok"] is False and verdict["active_core"] is None
    assert "active_core_in_lineage" in verdict["failed"]


def test_nc1b_writing_a_digest_into_the_lineage_does_not_authorize_it(monkeypatch):
    """Una entrada nueva con el digesto vivo, sin registro que la certifique: miembro, y rechazada."""
    rogue = rs.CoreVersion("ROGUE_VERSION", "PHASE2_CLOSURE", AMENDMENT.digest,
                           "docs/revision/NO_SUCH_RECORD.json", reversal="clinical_core.amendment_2")
    monkeypatch.setattr(rs, "CORE_LINEAGE", (CLOSURE, FIRST, rogue))
    verdict = ev.core_lineage_verdict()
    assert verdict["active_core_in_lineage"] is True and verdict["status"] == "NO_RECORD"
    assert verdict["ok"] is False and verdict["failed"] == ["active_core_certified"]
    # y tampoco si apunta al registro de OTRA version: el registro no esta ligado a esta entrada
    borrowed = dataclasses.replace(rogue, record=AMENDMENT.record)
    monkeypatch.setattr(rs, "CORE_LINEAGE", (CLOSURE, FIRST, borrowed))
    assert ev.core_lineage_verdict()["status"] == "RECORD_NOT_BOUND_TO_THE_LINEAGE"
    assert ev.core_lineage_ok() is False


def test_nc2_an_uncertified_successor_is_refused_and_only_its_status_decides(monkeypatch):
    monkeypatch.setattr(ev, "successor_status", lambda entry: rs.CANDIDATE)
    verdict = ev.core_lineage_verdict()
    assert verdict["ok"] is False and verdict["failed"] == ["active_core_certified"]
    monkeypatch.setattr(ev, "successor_status", lambda entry: rs.CERTIFIED)
    assert ev.core_lineage_ok() is True
    for other in ("NO_STATUS", "NO_RECORD", "certified", "", "RECORD_NOT_BOUND_TO_THE_LINEAGE"):
        monkeypatch.setattr(ev, "successor_status", lambda entry, value=other: value)
        assert ev.core_lineage_ok() is False, other


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


def test_nc3_a_valid_certified_successor_does_not_hide_a_broken_historical_closure(monkeypatch):
    _certified(monkeypatch)
    assert ev.core_lineage_ok() is True
    monkeypatch.setitem(a2.CORE_AT_AMENDMENT_1, "clinical_core/derived.py", "0" * 64)   # la reversion ya no prueba
    ev.core_lineage_cache_clear()
    verdict = ev.core_lineage_verdict()
    assert verdict["active_core_in_lineage"] and verdict["active_core_certified"]
    assert verdict["ok"] is False and "historical_closure_verifies" in verdict["failed"]


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


def test_nc4_the_successor_must_recompute_by_its_own_definition_too(monkeypatch):
    _certified(monkeypatch)
    assert ev.core_lineage_ok() is True
    monkeypatch.setattr(a2, "amended_core_digest_now", lambda: "cd" * 32)
    ev.core_lineage_cache_clear()        # los archivos no cambiaron: la definicion si, y la cache es por archivos
    verdict = ev.core_lineage_verdict()
    assert verdict["ok"] is False and verdict["failed"] == ["active_core_recomputes"]


def test_nc4b_a_lineage_entry_that_does_not_match_the_files_is_not_the_active_core(monkeypatch):
    _certified(monkeypatch)
    stale = dataclasses.replace(AMENDMENT, digest="ef" * 32)
    monkeypatch.setattr(rs, "CORE_LINEAGE", (CLOSURE, FIRST, stale))
    verdict = ev.core_lineage_verdict()
    assert verdict["ok"] is False and verdict["active_core"] is None


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


@pytest.mark.parametrize("shape", [[], "CERTIFIED", 7, None, {"amended": "x"}, {"certification": "CERTIFIED"},
                                   {"certification": ["CERTIFIED"]}, {"historical_closure": []},
                                   {"certification": {"status": ["CERTIFIED"]}},
                                   {"certification": {"status": True}}])
def test_nc2d_a_record_of_the_wrong_shape_is_a_refusal_and_never_a_raise(tmp_path, monkeypatch, shape):
    """JSON valido de otra forma: antes lanzaba dentro de la compuerta (revision adversarial). Ahora rechaza."""
    if isinstance(shape, dict):
        record = _record()
        record.update(shape)
    else:
        record = shape
    path = tmp_path / "shape.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    entry = dataclasses.replace(AMENDMENT, record=str(path))
    assert ev.successor_status(entry) in ("NO_RECORD", "RECORD_NOT_BOUND_TO_THE_LINEAGE", "NO_STATUS")
    monkeypatch.setattr(rs, "CORE_LINEAGE", (CLOSURE, FIRST, entry))
    verdict = ev.core_lineage_verdict()
    assert verdict["ok"] is False and verdict["failed"] == ["active_core_certified"]
    assert ev.core_lineage_ok() is False


def test_nc2e_the_gate_answers_no_when_the_verdict_cannot_be_computed(monkeypatch):
    def broken():
        raise RuntimeError("no verdict")
    monkeypatch.setattr(ev, "core_lineage_verdict", broken)
    assert ev.core_lineage_ok() is False
    assert ev.core_lineage_reason() == "the common core lineage could not be evaluated"


def test_the_refusal_says_what_failed_and_not_that_the_closure_moved(monkeypatch):
    """Con el sucesor sin certificar el cierre SI recalcula: el motivo no puede decir lo contrario."""
    monkeypatch.setattr(ev, "successor_status", lambda entry: rs.CANDIDATE)
    reason = ev.core_lineage_reason()
    assert "PHASE2_AMENDMENT_2" in reason and "CANDIDATE" in reason and "active_core_certified" in reason
    assert "does not recompute" not in reason
    monkeypatch.setattr(ev, "successor_status", lambda entry: rs.CERTIFIED)
    assert ev.core_lineage_reason() == ""
    monkeypatch.setitem(a2.CORE_AT_AMENDMENT_1, "clinical_core/derived.py", "0" * 64)
    ev.core_lineage_cache_clear()
    assert ev.core_lineage_reason() == "the Phase-2 closure digest does not recompute"
    monkeypatch.setattr(ev, "phase2_digest_now", lambda: "ab" * 32)
    assert "not a member of the certified core lineage" in ev.core_lineage_reason()
    source = (ROOT / "runtime_authority.py").read_text(encoding="utf-8")
    assert "ev.core_lineage_reason()" in source and '"the Phase-2 closure digest does not recompute"' not in source


def test_nc5_an_entry_is_not_the_root_because_it_names_no_parent(monkeypatch):
    """Hallazgo MEDIO de la revision adversarial: "certificado por construccion" se decidia por ``parent is None``.
    Una entrada sin padre con el digesto vivo quedaba certificada sin registro. La unica raiz es el cierre."""
    rogue = rs.CoreVersion("ROGUE_ROOT", None, AMENDMENT.digest, "docs/revision/NO_SUCH_RECORD.json",
                           reversal="clinical_core.amendment_2")
    for certified_by_record in (False, True):
        if certified_by_record:
            _certified(monkeypatch)                      # ni siquiera con un registro que dijera CERTIFIED
        for lineage in ((CLOSURE, FIRST, rogue), (rogue, CLOSURE, AMENDMENT), (CLOSURE, FIRST, rogue, AMENDMENT),
                        (CLOSURE, FIRST, AMENDMENT, dataclasses.replace(rogue, digest="ab" * 32))):
            monkeypatch.setattr(rs, "CORE_LINEAGE", lineage)
            ev.core_lineage_cache_clear()
            verdict = ev.core_lineage_verdict()
            assert verdict["ok"] is False and verdict["status"] == "LINEAGE_MALFORMED", lineage
            assert verdict["active_core"] is None and "active_core_in_lineage" in verdict["failed"]
            assert ev.core_lineage_ok() is False


MALFORMED = {
    "duplicate_digest": lambda: (CLOSURE, FIRST, AMENDMENT, dataclasses.replace(AMENDMENT, version_id="PHASE2_AMENDMENT_2",
                                                                         parent="PHASE2_AMENDMENT_2")),
    "duplicate_version": lambda: (CLOSURE, FIRST, AMENDMENT, dataclasses.replace(AMENDMENT, digest="ab" * 32)),
    "orphan_parent": lambda: (CLOSURE, FIRST, dataclasses.replace(AMENDMENT, parent="PHASE2_AMENDMENT_0")),
    "parent_listed_later": lambda: (CLOSURE, FIRST, dataclasses.replace(AMENDMENT, parent="LATER"),
                                    rs.CoreVersion("LATER", "PHASE2_CLOSURE", "cd" * 32, AMENDMENT.record,
                                                   reversal=AMENDMENT.reversal)),
    "successor_without_reversal": lambda: (CLOSURE, FIRST, dataclasses.replace(AMENDMENT, reversal=None)),
    "root_restated_with_the_live_digest": lambda: (dataclasses.replace(CLOSURE, digest=AMENDMENT.digest),),
    "root_restated_with_another_head": lambda: (dataclasses.replace(CLOSURE, head="0" * 40), AMENDMENT),
    "root_with_a_reversal": lambda: (dataclasses.replace(CLOSURE, reversal="clinical_core.amendment_2"), AMENDMENT),
    "root_renamed": lambda: (dataclasses.replace(CLOSURE, version_id="PHASE2_AMENDMENT_2"),),
    "no_root": lambda: (AMENDMENT,),
    "empty": lambda: (),
    "a_mutable_list": lambda: [CLOSURE, AMENDMENT],
}


@pytest.mark.parametrize("label", sorted(MALFORMED))
def test_nc5b_a_malformed_lineage_is_refused_whole(monkeypatch, label):
    _certified(monkeypatch)
    assert ev.core_lineage_ok() is True                  # el linaje real, con el mismo estado forzado, si vale
    monkeypatch.setattr(rs, "CORE_LINEAGE", MALFORMED[label]())
    ev.core_lineage_cache_clear()
    verdict = ev.core_lineage_verdict()
    assert verdict["ok"] is False and verdict["status"] == "LINEAGE_MALFORMED" and verdict["active_core"] is None
    assert ev.core_lineage_ok() is False


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


def test_nc3e_a_moved_declared_insertion_is_not_the_certified_successor(monkeypatch):
    """Every hunk this stage declares is anchored on the closure's own context (none is a pure insertion), so relocating
    one is not even a reconstruction of the predecessor: the reversal does not prove it. And a tree whose digest moved
    is not the lineage's core, whatever it reconstructs."""
    _certified(monkeypatch)
    assert all(before != "" for pairs in a2.REVERSAL.values() for _, before in pairs)
    for relative, pairs in sorted(a2.REVERSAL.items()):
        live = a2._live_text(relative)
        for hunk, _ in pairs:
            moved = live.replace(hunk, "") + hunk
            assert moved != live and a2.proved(relative, moved) is False, (relative, hunk[:60])
    relative = "clinical_core/derived.py"
    moved = a2._live_text(relative) + "\n# a moved line\n"
    sources = a2.live_core_sources()
    sources[relative] = __import__("hashlib").sha256(moved.encode("utf-8")).hexdigest()
    tampered_digest = a1.core_digest(sources)
    assert tampered_digest != AMENDMENT.digest
    monkeypatch.setattr(ev, "phase2_digest_now", lambda: tampered_digest)
    verdict = ev.core_lineage_verdict()
    assert verdict["ok"] is False and verdict["status"] == "NOT_IN_THE_LINEAGE"


def test_no_runtime_module_enters_the_closure_view():
    """La vista es de lectura y para paquetes cerrados: dentro de ella un perfil con fraccion declarada perderia
    la fraccion al copiarse (limite declarado). Por eso nada fuera de las pruebas la abre: la compuerta usa
    ``historical_closure_verifies``, que no instala ninguna vista."""
    for path in sorted(ROOT.glob("*.py")) + sorted((ROOT / "clinical_core").rglob("*.py")):
        if path.name.startswith("test_") or path.name in ("amendment_1.py", "amendment_2.py", "conftest.py"):
            continue
        text = path.read_text(encoding="utf-8")
        assert "closure_view" not in text and "amendment_1 as" not in text and "import amendment_1" not in text, path.name
    from clinical_core import closure_guard as cg, derived as dv
    before = (cg._live, dv.PARAMETERS, dv.CoreProfile.__dataclass_fields__, dv.CoreProfile.__repr__)
    ev.core_lineage_cache_clear()
    a2.historical_closure_verifies(), ev.core_lineage_verdict(), rs.active_core()
    assert (cg._live, dv.PARAMETERS, dv.CoreProfile.__dataclass_fields__, dv.CoreProfile.__repr__) == before






def test_every_import_time_copy_of_a_live_listing_is_declared_by_the_stage():
    """A closed package that took a copy of the parameter registry at import still lists ``amendment_2``: the stage's views
    drop the name from the live listing at its root and from the copies it declares, and from nothing else."""
    import importlib
    import pkgutil
    import sys

    import clinical_core
    from clinical_core import derived as dv
    for info in pkgutil.iter_modules(clinical_core.__path__):
        importlib.import_module(f"clinical_core.{info.name}")
    new, found = "amendment_2", set()
    for name, module in sorted(sys.modules.items()):
        if not name.startswith("clinical_core") or name == "clinical_core.amendment_2":
            continue
        for attribute, value in list(vars(module).items()):
            if isinstance(value, dict) and new in value:
                if value is dv.PARAMETERS or value is dv.CoreProfile.__dataclass_fields__:
                    continue
                found.add((name.rsplit(".", 1)[-1], attribute))
            elif isinstance(value, (tuple, list, set, frozenset)):
                assert not any(item == new or getattr(item, "name", None) == new for item in value), (name, attribute)
    # every such copy is reached by the stage's registry scan (``PARAMETERS``) or by the first amendment's declared list
    assert {attribute for _, attribute in found} <= {"PARAMETERS", "P2T3_PARAMETERS"}, found
    with a2.closure_view():
        for module_name, attribute in sorted(found):
            held = getattr(importlib.import_module(f"clinical_core.{module_name}"), attribute)
            assert new not in held, (module_name, attribute)
