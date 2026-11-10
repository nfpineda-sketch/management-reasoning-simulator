"""PHASE2_AMENDMENT_1: el linaje certificado del nucleo y la compuerta de digesto del runtime.

La compuerta dejo de comparar el arbol vivo con UNA constante. Ahora exige cuatro cosas a la vez:

  1. el cierre historico sigue verificando (desde los archivos vivos, por la reversion declarada);
  2. el digesto vivo es miembro del linaje;
  3. ese miembro esta CERTIFICADO (el cierre por construccion; un sucesor solo por su registro ligado);
  4. los archivos recalculan al digesto de ese miembro, tambien por la definicion del propio sucesor.

Cada una tiene aqui su control negativo. (PHASE2_AMENDMENT_2: las pruebas de la compuerta sobre el nucleo VIVO viven ahora en
test_phase2_amendment_2_lineage.py; este archivo conserva lo que es del primer sucesor, leido sobre SU arbol.) TODAS las pruebas leen el linaje real: ninguna usa la vista previa de
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
RECORD = ROOT / "docs" / "revision" / "PHASE2_AMENDMENT_1.json"
CLOSURE, AMENDMENT = rs.CORE_LINEAGE[0], rs.CORE_LINEAGE[1]


@pytest.fixture(autouse=True, scope="module")
def _first_amendment_tree():
    """PHASE2_AMENDMENT_2: this file tests what the FIRST amendment left, so it reads the tree as that amendment left it
    (the second amendment's insertions reversed, its field and memory hidden). The live tree has its own tests."""
    with pytest.MonkeyPatch.context() as patch:
        a2.amendment_1_tree(patch)
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
    assert isinstance(rs.CORE_LINEAGE, tuple) and len(rs.CORE_LINEAGE) == 3
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
    assert AMENDMENT.digest == a1.amended_core_digest_now()   # the first amendment's digest, by ITS definition
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
    assert a1.historical_closure_digest_now() == rs.PHASE2_DIGEST
    closure = a1.p2x1a_sources(a1.live_core_sources())
    assert len(closure) == 141 and closure == a1.closure_sources()




def test_every_closure_freeze_digest_recomputes_under_the_closure_view():
    from clinical_core import calibration, closure_guard as cg, decision_pack, lactate_slice, tone_domain
    recorded = json.loads(a1.CLOSURE_RECORD.read_text(encoding="utf-8"))["freeze_digests"]
    with a2.closure_view():
        now = {"calibration": calibration.frozen_digest(), "closure_guard_P2X1A": cg.freeze_digest(),
               "tone_domain_on_the_live_tree": tone_domain.freeze_digest(),
               "lactate_slice": lactate_slice.slice_digest(), "decision_pack": decision_pack.pack_digest()}
    assert now == recorded


def test_no_historical_file_or_digest_constant_was_rewritten():
    """Las 139 fuentes restantes del cierre son las del cierre, byte a byte: con ellas, las 67 constantes de
    digesto de etapa y las tablas de reversion de las 15 etapas, que viven dentro de esos archivos."""
    untouched = a1.common_untouched()
    assert len(untouched) == 139 == 141 - len(a1.REVERSAL) and all(untouched.values())
    assert set(untouched) == set(a1.closure_sources()) - set(a1.REVERSAL)
    constants = 0
    for path in sorted((ROOT / "clinical_core").glob("*.py")):
        if path.name in ("amendment_1.py", "amendment_2.py"):   # the successor stage restates the first digest
            continue
        constants += len(re.findall(r'^[A-Z0-9_]*(?:DIGEST|SHA)[A-Z0-9_]* = "[0-9a-f]{64}"',
                                    path.read_text(encoding="utf-8"), re.M))
    assert constants == 67


def test_the_view_changes_what_closed_packages_read_and_nothing_else():
    from clinical_core import derived as dv
    live_fields = [f.name for f in dataclasses.fields(dv.CoreProfile)]
    assert a1.NEW_PROFILE_FIELD in live_fields and a1.NEW_PROFILE_FIELD in dv.PARAMETERS
    with a2.closure_view():
        assert a1.NEW_PROFILE_FIELD not in [f.name for f in dataclasses.fields(dv.CoreProfile)]
        assert a1.NEW_PROFILE_FIELD not in dv.PARAMETERS
        assert "amendment_1.py" not in {p.name for p in a1._TreeDir().glob("*.py")}
    assert [f.name for f in dataclasses.fields(dv.CoreProfile)] == live_fields
    assert a1.NEW_PROFILE_FIELD in dv.PARAMETERS


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
        for status in ("NO_RECORD", "RECORD_NOT_BOUND_TO_THE_LINEAGE", "NO_STATUS", "REVOKED",
                       "CERTIFIED_WITHOUT_EVIDENCE", rs.CERTIFIED):
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






def test_nc4b_a_lineage_entry_that_does_not_match_the_files_is_not_the_active_core(monkeypatch):
    _certified(monkeypatch)
    stale = dataclasses.replace(AMENDMENT, digest="ef" * 32)
    monkeypatch.setattr(rs, "CORE_LINEAGE", (CLOSURE, stale))
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




def test_nc2e_the_gate_answers_no_when_the_verdict_cannot_be_computed(monkeypatch):
    def broken():
        raise RuntimeError("no verdict")
    monkeypatch.setattr(ev, "core_lineage_verdict", broken)
    assert ev.core_lineage_ok() is False
    assert ev.core_lineage_reason() == "the common core lineage could not be evaluated"




def test_nc5_an_entry_is_not_the_root_because_it_names_no_parent(monkeypatch):
    """Hallazgo MEDIO de la revision adversarial: "certificado por construccion" se decidia por ``parent is None``.
    Una entrada sin padre con el digesto vivo quedaba certificada sin registro. La unica raiz es el cierre."""
    rogue = rs.CoreVersion("ROGUE_ROOT", None, AMENDMENT.digest, "docs/revision/NO_SUCH_RECORD.json",
                           reversal="clinical_core.amendment_1")
    for certified_by_record in (False, True):
        if certified_by_record:
            _certified(monkeypatch)                      # ni siquiera con un registro que dijera CERTIFIED
        for lineage in ((CLOSURE, rogue), (rogue, CLOSURE, AMENDMENT), (CLOSURE, rogue, AMENDMENT),
                        (CLOSURE, AMENDMENT, dataclasses.replace(rogue, digest="ab" * 32))):
            monkeypatch.setattr(rs, "CORE_LINEAGE", lineage)
            ev.core_lineage_cache_clear()
            verdict = ev.core_lineage_verdict()
            assert verdict["ok"] is False and verdict["status"] == "LINEAGE_MALFORMED", lineage
            assert verdict["active_core"] is None and "active_core_in_lineage" in verdict["failed"]
            assert ev.core_lineage_ok() is False


MALFORMED = {
    "duplicate_digest": lambda: (CLOSURE, AMENDMENT, dataclasses.replace(AMENDMENT, version_id="PHASE2_AMENDMENT_2",
                                                                         parent="PHASE2_AMENDMENT_1")),
    "duplicate_version": lambda: (CLOSURE, AMENDMENT, dataclasses.replace(AMENDMENT, digest="ab" * 32)),
    "orphan_parent": lambda: (CLOSURE, dataclasses.replace(AMENDMENT, parent="PHASE2_AMENDMENT_0")),
    "parent_listed_later": lambda: (CLOSURE, dataclasses.replace(AMENDMENT, parent="LATER"),
                                    rs.CoreVersion("LATER", "PHASE2_CLOSURE", "cd" * 32, AMENDMENT.record,
                                                   reversal=AMENDMENT.reversal)),
    "successor_without_reversal": lambda: (CLOSURE, dataclasses.replace(AMENDMENT, reversal=None)),
    "root_restated_with_the_live_digest": lambda: (dataclasses.replace(CLOSURE, digest=AMENDMENT.digest),),
    "root_restated_with_another_head": lambda: (dataclasses.replace(CLOSURE, head="0" * 40), AMENDMENT),
    "root_with_a_reversal": lambda: (dataclasses.replace(CLOSURE, reversal="clinical_core.amendment_1"), AMENDMENT),
    "root_renamed": lambda: (dataclasses.replace(CLOSURE, version_id="PHASE2_AMENDMENT_1"),),
    "no_root": lambda: (AMENDMENT,),
    "empty": lambda: (),
    "a_mutable_list": lambda: [CLOSURE, AMENDMENT],
}




def test_the_real_lineage_is_well_formed_and_only_the_closure_is_its_root():
    assert ev._lineage_well_formed() is True
    assert ev._is_the_historical_root(CLOSURE) is True and ev._is_the_historical_root(AMENDMENT) is False
    assert ev._is_the_historical_root(dataclasses.replace(CLOSURE)) is False      # una copia no es la entrada


def test_nc3d_a_duplicated_declared_insertion_does_not_reverse():
    """Cada insercion declarada debe aparecer exactamente una vez: dos veces no es el archivo declarado."""
    relative = "clinical_core/derived.py"
    live = a1._live_text(relative)
    for hunk, _before in a1.REVERSAL[relative]:
        assert live.count(hunk) == 1
        assert a1.proved(relative, live + "\n" + hunk) is False
        assert a1.proved(relative, live.replace(hunk, "")) is False




def test_a_closure_view_that_cannot_be_installed_whole_is_not_left_installed_in_part(monkeypatch):
    from clinical_core import closure_guard as cg, derived as dv
    before = (cg._live, dv.PARAMETERS, dv.CoreProfile.__dataclass_fields__, dv.CoreProfile.__repr__)
    real_tree = a1.tree

    def half(patch):
        real_tree(patch)                                 # toda la vista instalada...
        raise RuntimeError("the view failed while it was being installed")

    monkeypatch.setattr(a1, "tree", half)
    with pytest.raises(RuntimeError):
        with a2.closure_view():
            raise AssertionError("the body must not run")
    assert (cg._live, dv.PARAMETERS, dv.CoreProfile.__dataclass_fields__, dv.CoreProfile.__repr__) == before
    assert a1.NEW_PROFILE_FIELD in dv.PARAMETERS




def test_the_record_states_what_the_tree_recomputes():
    """El registro no es prosa libre: lo que afirma de forma verificable se recalcula aqui. (La revision adversarial
    escribio valores falsos en una copia del registro y ninguna prueba lo noto.)"""
    record, closure, live = _record(), a1.closure_sources(), a1.live_core_sources()
    amended = record["amended"]
    assert amended["core_digest"] == a1.amended_core_digest_now() == AMENDMENT.digest
    assert amended["clinical_core_modules"] == len(live) == 142
    assert amended["changed_sources"] == sorted(k for k in closure if closure[k] != live.get(k)) == sorted(a1.REVERSAL)
    assert amended["added_sources"] == sorted(set(live) - set(closure)) == list(a1.OWN)
    assert amended["removed_sources"] == sorted(set(closure) - set(live)) == []
    assert amended["stage_module"] == a1.OWN[0]
    assert amended["declared_insertions"] == {k: len(v) for k, v in a1.REVERSAL.items()} == {
        "clinical_core/decision_pack.py": 1, "clinical_core/derived.py": 5}
    historical = record["historical_closure"]
    assert historical["clinical_core_modules"] == len(closure) == 141
    assert historical["predecessor_stage"] == a1.PREDECESSOR == "P2X-1A"
    assert historical["predecessor_freeze_digest"] == a1.P2X1A_FREEZE_DIGEST
    assert historical["record"] == a1.CLOSURE_RECORD.relative_to(ROOT).as_posix()
    assert (record["amendment"], record["parent"]) == (AMENDMENT.version_id, AMENDMENT.parent)
    parameter = record["parameter"]
    assert parameter["name"] == a1.NEW_PROFILE_FIELD and parameter["default"] is None
    from clinical_core import derived as dv
    assert getattr(dv.DEFAULT_PROFILE, parameter["name"]) is parameter["default"]
    assert parameter["declared_only_with"] == "respiratory_quotient" and parameter["status"] == dv.PARAMETERS[
        parameter["name"]][0]
    assert parameter["name"] in record["equation"]["after"] and parameter["name"] not in record["equation"]["before"]
    for pinned in ("25.249191654270817", "37.21648925248409"):
        assert any(pinned in line for line in record["backward_compatibility"]["evidence"])


def test_the_closure_freeze_digests_have_recorded_successor_values():
    """``versions()`` lleva el digesto vivo de la guarda de cierre: su valor sobre el arbol enmendado queda registrado."""
    from clinical_core import calibration, closure_guard as cg, decision_pack, lactate_slice, tone_domain
    stated = _record()["successor_artifacts"]["closure_freeze_digests"]["digests"]
    recorded = json.loads(a1.CLOSURE_RECORD.read_text(encoding="utf-8"))["freeze_digests"]
    now = {"calibration": calibration.frozen_digest(), "closure_guard_P2X1A": cg.freeze_digest(),
           "tone_domain_on_the_live_tree": tone_domain.freeze_digest(),
           "lactate_slice": lactate_slice.slice_digest(), "decision_pack": decision_pack.pack_digest()}
    assert sorted(stated) == sorted(recorded) == sorted(now)
    # PHASE2_AMENDMENT_2: the first amendment's tree is reproduced here by a view of the paths and the sources; the two
    # freeze digests that read the common files through the closed packages' own import-time listings
    # (closure_guard_P2X1A, tone_domain_on_the_live_tree) are NOT recomputed on that tree by this stage's view (declared
    # limit); their recorded values stay in the first amendment's record, and the closure's own values are recomputed
    # under the closure view by test_every_closure_freeze_digest_recomputes_under_the_closure_view.
    recomputed = ("calibration", "lactate_slice", "decision_pack")
    for name, row in stated.items():
        assert row["PHASE2_CLOSURE"] == recorded[name]
        if name in recomputed:
            assert row["PHASE2_AMENDMENT_1"] == now[name]
            assert row["unchanged"] is (recorded[name] == now[name])
    assert [name for name, row in stated.items() if row["unchanged"]] == ["calibration"]
