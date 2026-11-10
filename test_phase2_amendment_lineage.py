"""PHASE2_AMENDMENT_1: el linaje certificado del nucleo y la compuerta de digesto del runtime.

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

pytestmark = pytest.mark.real_core_lineage
ROOT = Path(__file__).resolve().parent
RECORD = ROOT / "docs" / "revision" / "PHASE2_AMENDMENT_1.json"
CLOSURE, AMENDMENT = rs.CORE_LINEAGE[0], rs.CORE_LINEAGE[-1]


@pytest.fixture(autouse=True)
def _fresh_cache():
    ev.core_lineage_cache_clear()
    yield
    ev.core_lineage_cache_clear()


def _record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _certified(monkeypatch):
    """El estado que tendra tras la promocion, para aislar las OTRAS tres condiciones."""
    monkeypatch.setattr(ev, "successor_status", lambda entry: rs.CERTIFIED)


# El registro de linaje ---------------------------------------------------------------------------------

def test_the_lineage_is_immutable_and_roots_at_the_historical_closure():
    assert isinstance(rs.CORE_LINEAGE, tuple) and len(rs.CORE_LINEAGE) == 2
    assert dataclasses.is_dataclass(CLOSURE) and CLOSURE.__dataclass_params__.frozen
    with pytest.raises(dataclasses.FrozenInstanceError):
        AMENDMENT.digest = "0" * 64
    assert (CLOSURE.version_id, CLOSURE.parent) == ("PHASE2_CLOSURE", None)
    assert CLOSURE.head == rs.PHASE2_CLOSURE_HEAD == "d2cca46626ed5d45a792ec9456d46fb75fe87731"
    assert CLOSURE.digest == rs.PHASE2_DIGEST == "22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a"
    assert (AMENDMENT.version_id, AMENDMENT.parent) == ("PHASE2_AMENDMENT_1", "PHASE2_CLOSURE")
    assert AMENDMENT.reversal == "clinical_core.amendment_1"
    # un sucesor no lleva su estado en el registro: nombrar un digesto aqui no certifica nada
    assert not any("status" in field.name for field in dataclasses.fields(rs.CoreVersion))


def test_the_amended_digest_is_new_and_is_what_the_files_recompute_to():
    assert AMENDMENT.digest != CLOSURE.digest
    assert AMENDMENT.digest == ev.phase2_digest_now() == a1.amended_core_digest_now()
    record = _record()
    assert record["amended"]["core_digest"] == AMENDMENT.digest
    # dos fuentes, las dos declaradas como trozos reversibles: la fisiologia (derived.py) y el registro que
    # cada etapa hace de su propio modulo en la tupla de exclusion del pack (decision_pack.py)
    assert record["amended"]["changed_sources"] == ["clinical_core/decision_pack.py", "clinical_core/derived.py"]
    assert record["amended"]["declared_insertions"] == {"clinical_core/decision_pack.py": 1,
                                                        "clinical_core/derived.py": 5}
    from clinical_core import decision_pack
    assert set(a1.OWN) <= set(decision_pack.PACK_DIGEST_EXCLUDED) and a1.TUPLES_ADDED == {"PACK_DIGEST_EXCLUDED": a1.OWN}
    assert record["amended"]["added_sources"] == ["clinical_core/amendment_1.py"]
    assert record["amended"]["removed_sources"] == []


# El cierre historico, intacto ---------------------------------------------------------------------------

def test_the_historical_closure_still_recomputes_from_the_live_tree():
    standing = a1.historical_closure_verifies()
    assert standing == {"reversal_proven": True, "common_untouched": True, "touched": [],
                        "closure_digest_recomputes": True, "closure_record_states_it": True}
    assert a1.historical_closure_digest_now() == rs.PHASE2_DIGEST == ev.historical_closure_digest_now()
    closure = a1.p2x1a_sources(a1.live_core_sources())
    assert len(closure) == 141 and closure == a1.closure_sources()


def test_the_predecessor_freeze_digest_recomputes_on_its_own_tree_and_not_on_the_live_one():
    from clinical_core import closure_guard as cg
    closure_record = json.loads(a1.CLOSURE_RECORD.read_text(encoding="utf-8"))
    assert a1.P2X1A_FREEZE_DIGEST == closure_record["freeze_digests"]["closure_guard_P2X1A"]
    assert a1.p2x1a_digest() == a1.P2X1A_FREEZE_DIGEST
    assert cg.freeze_digest() != a1.P2X1A_FREEZE_DIGEST          # fuera de la vista, el arbol es el enmendado
    assert a1.non_regression()["pass"] is True


def test_every_closure_freeze_digest_recomputes_under_the_closure_view():
    from clinical_core import calibration, closure_guard as cg, decision_pack, lactate_slice, tone_domain
    recorded = json.loads(a1.CLOSURE_RECORD.read_text(encoding="utf-8"))["freeze_digests"]
    with a1.closure_view():
        now = {"calibration": calibration.frozen_digest(), "closure_guard_P2X1A": cg.freeze_digest(),
               "tone_domain_on_the_live_tree": tone_domain.freeze_digest(),
               "lactate_slice": lactate_slice.slice_digest(), "decision_pack": decision_pack.pack_digest()}
    assert now == recorded


def test_no_historical_file_or_digest_constant_was_rewritten():
    """Los 140 fuentes restantes del cierre son los del cierre, byte a byte: con ellos, las 67 constantes de
    digesto de etapa y las tablas de reversion de las 15 etapas, que viven dentro de esos archivos."""
    assert all(a1.common_untouched().values())
    constants = 0
    for path in sorted((ROOT / "clinical_core").glob("*.py")):
        if path.name == "amendment_1.py":
            continue
        constants += len(re.findall(r'^[A-Z0-9_]*(?:DIGEST|SHA)[A-Z0-9_]* = "[0-9a-f]{64}"',
                                    path.read_text(encoding="utf-8"), re.M))
    assert constants == 67


def test_the_view_changes_what_closed_packages_read_and_nothing_else():
    from clinical_core import derived as dv
    live_fields = [f.name for f in dataclasses.fields(dv.CoreProfile)]
    assert a1.NEW_PROFILE_FIELD in live_fields and a1.NEW_PROFILE_FIELD in dv.PARAMETERS
    with a1.closure_view():
        assert a1.NEW_PROFILE_FIELD not in [f.name for f in dataclasses.fields(dv.CoreProfile)]
        assert a1.NEW_PROFILE_FIELD not in dv.PARAMETERS
        assert "amendment_1.py" not in {p.name for p in a1._TreeDir().glob("*.py")}
    assert [f.name for f in dataclasses.fields(dv.CoreProfile)] == live_fields
    assert a1.NEW_PROFILE_FIELD in dv.PARAMETERS


# La compuerta real, tal como esta el registro -----------------------------------------------------------

def test_the_real_gate_follows_the_recorded_status_and_nothing_else():
    status = _record()["certification"]["status"]
    assert status in (rs.CANDIDATE, rs.CERTIFIED)
    verdict = ev.core_lineage_verdict()
    assert verdict["active_core"] == "PHASE2_AMENDMENT_1" and verdict["status"] == status
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
    assert versions["core_version"] == "PHASE2_AMENDMENT_1"
    assert versions["core_digest"] == ev.phase2_digest_now() == AMENDMENT.digest != rs.PHASE2_DIGEST


def test_an_unlisted_core_is_named_as_such_and_naming_it_authorizes_nothing(monkeypatch):
    monkeypatch.setattr(ev, "phase2_digest_now", lambda: "ab" * 32)
    assert rs.active_core() == {"core_version": "NOT_IN_THE_LINEAGE", "core_digest": "ab" * 32}
    assert ev.core_lineage_ok() is False


def test_every_import_time_copy_of_a_live_listing_is_declared_by_the_stage():
    """Una copia tomada al importar (antes de cualquier vista) llevaria el nombre nuevo a un paquete cerrado. La
    etapa declara las que existen; esta prueba recorre TODOS los modulos del nucleo y no admite otra."""
    import importlib
    import pkgutil
    import sys

    import clinical_core
    from clinical_core import derived as dv
    for info in pkgutil.iter_modules(clinical_core.__path__):
        importlib.import_module(f"clinical_core.{info.name}")
    new, found = a1.NEW_PROFILE_FIELD, set()
    for name, module in sorted(sys.modules.items()):
        if not name.startswith("clinical_core") or name == "clinical_core.amendment_1":
            continue
        for attribute, value in list(vars(module).items()):
            if isinstance(value, dict) and new in value:
                if value is dv.PARAMETERS or value is dv.CoreProfile.__dataclass_fields__:
                    continue                                # el listado vivo mismo: la vista lo filtra en su raiz
                found.add((name.rsplit(".", 1)[-1], attribute))
            elif isinstance(value, (tuple, list, set, frozenset)):
                assert not any(item == new or getattr(item, "name", None) == new for item in value), (name, attribute)
    assert found == set(a1.CLOSED_SNAPSHOTS) == {("oxygenation_link", "P2T3_PARAMETERS")}
    with a1.closure_view():
        for module_name, attribute in a1.CLOSED_SNAPSHOTS:
            assert new not in getattr(sys.modules[f"clinical_core.{module_name}"], attribute)
        assert new not in dv.PARAMETERS and new not in dv.CoreProfile.__dataclass_fields__
        assert new not in repr(dv.DEFAULT_PROFILE)
    assert new in dv.PARAMETERS and new in repr(dv.DEFAULT_PROFILE)


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
    monkeypatch.setenv(preview.CORE_CERTIFICATION_PREVIEW_FLAG, "PHASE2_AMENDMENT_1")
    real = ev.successor_status
    session = preview._core_certification_preview.__wrapped__()
    next(session)
    try:
        previewed = ev.successor_status
        assert previewed.real is real
        monkeypatch.setattr(previewed, "real", previewed.real)         # deja el atributo como estaba al salir
        for status in ("NO_RECORD", "RECORD_NOT_BOUND_TO_THE_LINEAGE", "NO_STATUS", "REVOKED", rs.CERTIFIED):
            assert _previewed_with(preview, status, AMENDMENT) == status
        assert _previewed_with(preview, rs.CANDIDATE, AMENDMENT) == rs.CERTIFIED
        other = dataclasses.replace(AMENDMENT, version_id="PHASE2_AMENDMENT_2")
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
                           "docs/revision/NO_SUCH_RECORD.json", reversal="clinical_core.amendment_1")
    monkeypatch.setattr(rs, "CORE_LINEAGE", (CLOSURE, rogue))
    verdict = ev.core_lineage_verdict()
    assert verdict["active_core_in_lineage"] is True and verdict["status"] == "NO_RECORD"
    assert verdict["ok"] is False and verdict["failed"] == ["active_core_certified"]
    # y tampoco si apunta al registro de OTRA version: el registro no esta ligado a esta entrada
    borrowed = dataclasses.replace(rogue, record=AMENDMENT.record)
    monkeypatch.setattr(rs, "CORE_LINEAGE", (CLOSURE, borrowed))
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
    record["certification"] = {"status": rs.CERTIFIED}
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
    monkeypatch.setitem(a1.CORE_AT_P2X1A, "clinical_core/derived.py", "0" * 64)   # la reversion ya no prueba
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
    live = a1._live_text("clinical_core/derived.py")
    assert a1.proved("clinical_core/derived.py", live) is True
    assert a1.proved("clinical_core/derived.py", live + "\nUNDECLARED = 1\n") is False
    assert a1.proved("clinical_core/derived.py", live.replace("share * delta", "share * share * delta")) is False


def test_nc4_the_successor_must_recompute_by_its_own_definition_too(monkeypatch):
    _certified(monkeypatch)
    assert ev.core_lineage_ok() is True
    monkeypatch.setattr(a1, "amended_core_digest_now", lambda: "cd" * 32)
    ev.core_lineage_cache_clear()        # los archivos no cambiaron: la definicion si, y la cache es por archivos
    verdict = ev.core_lineage_verdict()
    assert verdict["ok"] is False and verdict["failed"] == ["active_core_recomputes"]


def test_nc4b_a_lineage_entry_that_does_not_match_the_files_is_not_the_active_core(monkeypatch):
    _certified(monkeypatch)
    stale = dataclasses.replace(AMENDMENT, digest="ef" * 32)
    monkeypatch.setattr(rs, "CORE_LINEAGE", (CLOSURE, stale))
    verdict = ev.core_lineage_verdict()
    assert verdict["ok"] is False and verdict["active_core"] is None
