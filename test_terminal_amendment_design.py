"""Diseno formal de la Enmienda 2 (transicion terminal y consciencia) y frontera terminal de la traza
(2026-11-10): A2-001 a A2-010, P3-169 a P3-171.

El nucleo comun NO cambia en este ciclo: lo que estas pruebas fijan es (1) que cada afirmacion del registro de
diseno es lo que el codigo tiene hoy, (2) que no se eligio ningun umbral, y (3) la unica pieza ejecutable: la
frontera terminal de la traza, fuera del nucleo y sin umbrales.

Registro: terminal_amendment_record. Etiquetas ``a2``.
"""
import copy
from pathlib import Path

import pytest

import pilot_acceptance as acceptance
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
import runtime_shadow_observer as obs
import runtime_shadow_store as store
import shadow_resolution_record as previous
import terminal_amendment_record as rec
from clinical_core import amendment_2 as a2
from clinical_core import calibration, collapse, derived as dv, encephalopathy, opioid_migration as om
from test_shadow_observability import GI, NALOXONE, OPIOID, _latest, _play, traces  # noqa: F401

ROOT = Path(__file__).resolve().parent
CORE = ROOT / "clinical_core"


def _source(name):
    """P3-173: este paquete es de DISENO (el nucleo era la Enmienda 1 y no cambio en aquel ciclo). El nucleo vivo es hoy
    su sucesor certificado, que declara sus inserciones: lo que el diseno describe se lee en el arbol de la Enmienda 1,
    reconstruido por esa reversion declarada y probada."""
    return a2.a1_text(f"clinical_core/{name}")


# -- A2-001: linaje -----------------------------------------------------------------------------------------------------

def test_a2_001_the_lineage_is_the_certified_one_and_the_core_did_not_change():
    lineage = rec.LINEAGE
    # El registro de diseno describe el nucleo de ENTONCES (la Enmienda 1). Hoy ese miembro sigue en el linaje, con su
    # digesto, y el nucleo vivo es su sucesor certificado (P3-173): el diseno no se reescribe, se lee contra su miembro.
    parent = rs.CORE_LINEAGE[1]
    assert parent.version_id == lineage["parent"]["name"] == lineage["active_core_on_the_phase3_branch"]
    assert parent.digest == lineage["parent"]["digest"]
    assert a2.amendment_1_verifies()["digest_recomputes"] is True
    active = rs.active_core()
    assert active["core_version"] == "PHASE2_AMENDMENT_2" and active["core_digest"] == rs.CORE_LINEAGE[-1].digest
    assert [entry.version_id for entry in rs.CORE_LINEAGE] == ["PHASE2_CLOSURE", "PHASE2_AMENDMENT_1",
                                                                 "PHASE2_AMENDMENT_2"]
    assert rs.CORE_LINEAGE[0].digest == lineage["historical_closure"]["digest"]
    assert lineage["historical_closure"]["changed"] is False and lineage["parent"]["changed"] is False
    verdict = ev.core_lineage_verdict()
    assert verdict["ok"] is True and verdict["historical_closure_verifies"] and verdict["status"] == "CERTIFIED", verdict
    workspace = lineage["workspace"]
    assert workspace["created_from"] == lineage["parent"]["branch_head"] and workspace["commits_on_it"] == 0
    assert workspace["common_core_changed"] is False and workspace["status"] == "WORKSPACE_ONLY_NO_CANDIDATE"
    assert rec.DESIGN["certified"] is False and rec.DESIGN["full_certification_run"] is False


# -- A2-002: el grafo ejecutable ------------------------------------------------------------------------------------------

def test_a2_002_every_edge_of_the_graph_has_one_status_and_the_key_ones_are_in_the_code():
    assert all(row["status"] in rec.EDGE_STATUSES and row["edge"] for row in rec.GRAPH)
    assert {row["status"] for row in rec.GRAPH} == set(rec.EDGE_STATUSES)
    by_edge = {row["edge"]: row["status"] for row in rec.GRAPH}
    derived = _source("derived.py")
    # las dos escaleras directas son lo que hoy mueve la consciencia en el nucleo
    assert ("level = max(anchors.consciousness_level, _level(sbp, profile.pressure_levels), "
            "_level(spo2, profile.oxygen_levels))") in derived
    assert by_edge["SBP ladder -> consciousness level"] == by_edge["SpO2 ladder -> consciousness level"] == \
        "IMPLEMENTED_COMMON_CORE"
    # nadie escribe N; la regla de colapso esta apagada; no hay estado de fallo respiratorio
    integration = _source("integration.py")
    assert "no module writes N yet" in integration and by_edge["N -> neurologic impairment"] == "DEFERRED"
    assert dv.DEFAULT_PROFILE.collapse_output_threshold is None and dv.DEFAULT_PROFILE.collapse_burden_limit is None
    for name in ("state.py", "derived.py", "integration.py"):
        text = _source(name).lower()
        assert "respiratory_failure" not in text and "respiratory_arrest" not in text, name
    assert by_edge["respiratory failure as a state or predicate"] == "MISSING"
    assert "APNOEA_BOUNDARY_UNRESOLVED" in derived
    # las reglas terminales viven en el motor heredado y sus modulos
    legacy = (ROOT / "opioid_reversal.py").read_text(encoding="utf-8")
    assert 'f["arrest_at"] = f["elapsed"]' in legacy and "ARREST_AFTER_MIN" in legacy
    assert by_edge["family rule -> arrest / fibrillation minute"] == "IMPLEMENTED_LEGACY"
    assert by_edge["legacy terminal record + core pulse -> terminal boundary of the trace"] == "IMPLEMENTED_RUNTIME"


def test_a2_002_the_opioid_run_measures_the_executed_and_the_missing_edges():
    encounter = _play(OPIOID, (), until=15)
    rows = fam.run_channels(encounter.shadow.runner)
    first, last = rows[0]["channels"], rows[-1]["channels"]
    assert last["central_availability"] < first["central_availability"]
    assert last["respiratory_rate"] < first["respiratory_rate"] and last["paco2"] > first["paco2"]
    assert last["ph"] < first["ph"]
    # ...y nada de eso llega a la consciencia ni a la saturacion en el perfil comprometido
    assert {row["channels"]["consciousness_level"] for row in rows} == {first["consciousness_level"]}
    assert {row["channels"]["spo2"] for row in rows} == {first["spo2"]}
    assert all(row["channels"]["pulse_present"] is True for row in rows)


# -- A2-003: descomposicion de la consciencia ---------------------------------------------------------------------------------

def test_a2_003_the_contributors_and_the_ladder_they_must_replace():
    design = rec.CONSCIOUSNESS
    verdicts = {name: row["verdict"] for name, row in design["contributors"].items()}
    assert set(verdicts.values()) <= set(rec.CONTRIBUTOR_VERDICTS) and len(verdicts) == 5
    assert verdicts["B central depressant state"] == "NEW_MECHANISM_REQUIRED"
    assert [verdicts[name] for name in verdicts if not name.startswith("B")] == ["STRUCTURALLY_JUSTIFIED"] * 4
    assert design["existing ladder"]["verdict"] == "DUPLICATIVE"
    assert design["existing ladder"]["values"] == {"pressure_levels": dv.DEFAULT_PROFILE.pressure_levels,
                                                   "oxygen_levels": dv.DEFAULT_PROFILE.oxygen_levels}
    assert dv.PARAMETERS["pressure_levels"][0] == dv.ADOPTED and "family_engine" in dv.PARAMETERS["pressure_levels"][1]
    assert dv.PARAMETERS["oxygen_levels"][0] == dv.ADOPTED
    assert design["structure_identifiable"] is True and design["magnitudes_identifiable"] is False
    # la capa candidata: estructura completa, magnitudes sin fijar, y nunca lee el depresor central
    profile = encephalopathy.DEFAULT_ENCEPHALOPATHY
    assert profile.mappings == () and profile.burden_rise_tau is None and profile.burden_clear_tau is None
    source = _source("encephalopathy.py")
    assert "central_availability" not in source
    assert encephalopathy.observable_impairment(0.2, 0.5, 0.1)["impairment"] == 0.5    # el maximo: no suma
    assert all("NOT_IDENTIFIABLE" in row["magnitude"] or "none needed" in row["magnitude"]
               for row in design["contributors"].values())


# -- A2-004 y A2-005: fallo respiratorio y colapso ------------------------------------------------------------------------------

def test_a2_004_respiratory_failure_needs_a_state_and_no_threshold_was_chosen():
    failure = rec.RESPIRATORY_FAILURE
    assert failure["verdict"] == "NEW_COMMON_STATE_REQUIRED" and failure["threshold_chosen"] is False
    assert "never SpO2 alone" in failure["semantic_principle"]
    # la perdida del opioide es proporcional: la disponibilidad nunca llega a cero
    encounter = _play(OPIOID, (), until=20)
    values = [row["channels"]["central_availability"] for row in fam.run_channels(encounter.shadow.runner)]
    assert values == sorted(values, reverse=True) and values[-1] > 0
    ratios = {round(later / earlier, 9) for earlier, later in zip(values, values[1:])}
    assert ratios == {round(1 - om.DEEPENING_PER_MIN, 9)}
    assert all(row["channels"]["respiratory_rate"] > 0 for row in fam.run_channels(encounter.shadow.runner))


def test_a2_005_the_collapse_structure_exists_and_every_magnitude_is_unset():
    design = rec.CIRCULATORY_COLLAPSE
    assert design["verdict"] == "EXISTING_VARIABLES_SUFFICIENT_STRUCTURE" and design["threshold_chosen"] is False
    profile = collapse.CollapseProfile()
    assert (profile.perfusion_mapping, profile.burden_tau_min, profile.terminal_burden,
            profile.current_nonviability, profile.terminal_rhythm) == (None,) * 5
    assert dv.PARAMETERS["collapse_output_threshold"][0] == dv.PROVISIONAL
    registry = calibration.REGISTRY
    for name in ("collapse_output_threshold", "collapse_burden_limit"):
        assert name in registry and "FACULTY_APPROVED" not in str(getattr(registry[name], "status", ""))
    assert "No entry is FACULTY_APPROVED" in _source("calibration.py")
    assert "terminal_since is set exactly when there is no pulse" in _source("state.py")
    assert "two overlapping structures" in design["open_structural_choice"]


# -- A2-006: la frontera, y su unica pieza ejecutable ------------------------------------------------------------------------------

def test_a2_006_a_terminal_legacy_patient_beside_an_active_core_run_is_an_explicit_state(traces):
    encounter = _play(OPIOID, (), until=30)
    trace = _latest(encounter)
    boundary = trace["terminal_boundary"]
    assert encounter.arrested and encounter.shadow.legacy_terminal == {"arrest_at": 20, "vf_at": None}
    assert boundary["state"] == fam.LEGACY_TERMINAL_CORE_ACTIVE and "declared boundary" in boundary["why"].lower()
    assert boundary["legacy"] == {"terminal": True, "minute": 20, "arrest_at": 20, "vf_at": None}
    assert boundary["core"]["pulse_present"] is True and boundary["core"]["collapse_rule_declared"] is False
    assert set(boundary["core"]["predicates"].values()) == {fam.PREDICATE_NOT_DETERMINED}
    assert boundary["decides_the_encounter"] == "legacy"
    assert store.verify(trace)["verified"] and store.replay(trace)["reproduces"]
    for case, turns in ((GI, ("Give 1 L of lactated Ringer's.",)), (OPIOID, (NALOXONE,))):
        living = _latest(_play(case, turns, until=10))["terminal_boundary"]
        assert living["state"] == fam.BOTH_ACTIVE and living["legacy"]["terminal"] is False
    assert rec.BOUNDARY["states"] == fam.TERMINAL_BOUNDARY_STATES
    index = obs.review_markdown([obs.review_entry(trace)])
    assert "### Terminal boundary" in index and "LEGACY_TERMINAL_CORE_ACTIVE" in index


def test_a2_006_the_boundary_reads_and_never_decides():
    told = fam.terminal_boundary
    pulse = {"pulse_present": True, "respiratory_rate": 9.0, "consciousness_level": 1}
    none = {"pulse_present": False, "respiratory_rate": 0.0, "consciousness_level": 3}
    assert told({"arrest_at": None, "vf_at": None}, pulse, False)["state"] == fam.BOTH_ACTIVE
    assert told({"arrest_at": 20, "vf_at": None}, pulse, False)["state"] == fam.LEGACY_TERMINAL_CORE_ACTIVE
    assert told({"arrest_at": None, "vf_at": 7}, none, True)["state"] == fam.TERMINAL_AGREEMENT
    assert told({"arrest_at": None, "vf_at": None}, none, True)["state"] == fam.CORE_TERMINAL_LEGACY_ACTIVE
    for legacy, channels in ((None, pulse), ({"arrest_at": 3, "vf_at": None}, None), (None, None), ("x", {})):
        assert told(legacy, channels, None)["state"] == fam.TERMINAL_NOT_COMPARABLE
    # predicados sin umbral: solo lo que la lectura del nucleo ya resuelve
    assert told({}, none, True)["core"]["predicates"] == {
        "circulatory_arrest": "TRUE", "respiratory_failure": "NOT_DETERMINED",
        "severe_consciousness_impairment": "TRUE"}
    apnoeic = dict(pulse, respiratory_rate=0)
    assert told({}, apnoeic, False)["core"]["predicates"]["respiratory_failure"] == "TRUE"
    # R-F4 de la revision: tipos raros no fabrican un predicado ni un estado
    assert told({}, dict(pulse, respiratory_rate=False), False)["core"]["predicates"]["respiratory_failure"] == \
        "NOT_DETERMINED"
    odd = told({}, {"pulse_present": None, "respiratory_rate": 0, "consciousness_level": 3}, None)
    assert odd["state"] == fam.TERMINAL_NOT_COMPARABLE and set(odd["core"]["predicates"].values()) == {"NOT_DETERMINED"}
    assert told({}, dict(pulse, pulse_present=0), False)["state"] == fam.TERMINAL_NOT_COMPARABLE
    assert told({"arrest_at": "20", "vf_at": 3}, pulse, False)["state"] == fam.TERMINAL_NOT_COMPARABLE   # no levanta
    assert "collapse limits are unset" not in told({"arrest_at": 2, "vf_at": None}, pulse, True)["why"]
    low = dict(pulse, respiratory_rate=0.4, spo2=40.0, sbp=30.0)
    assert set(told({}, low, False)["core"]["predicates"].values()) == {"NOT_DETERMINED"}     # ningun umbral
    source = (ROOT / "runtime_shadow_families.py").read_text(encoding="utf-8")
    body = source[source.index("def terminal_boundary("):source.index("def held_rows(")]
    assert not any(token in body for token in ("spo2", "sbp", "map", " < ", " > ", "<=", ">="))
    # no toca el encuentro: el estado heredado es el mismo con la sombra encendida y apagada
    on, off = _play(OPIOID, (), until=30), _play(OPIOID, (), until=30, mode=None)
    assert on.state == off.state and ev.authoritative(on) == ev.authoritative(off)
    assert rs.legacy_terminal_of(None) is None and rs.legacy_terminal_of({"family_state": "x"}) is None


def test_a2_006_a_resealed_trace_cannot_hide_the_boundary(traces):
    trace = _latest(_play(OPIOID, (), until=30))

    def resealed(edit):
        body = copy.deepcopy(trace)
        edit(body)
        body["trace_digest"] = store.trace_digest(body)
        return store.verify(body)

    for name, edit in {
            "state relabelled": lambda b: b["terminal_boundary"].update(state=fam.BOTH_ACTIVE),
            "reason rewritten": lambda b: b["terminal_boundary"].update(why="fine"),
            "core side flipped": lambda b: b["terminal_boundary"]["core"].update(pulse_present=False),
            "predicate invented": lambda b: b["terminal_boundary"]["core"]["predicates"].update(
                circulatory_arrest="TRUE"),
            "legacy flag cleared, minute kept": lambda b: b["terminal_boundary"]["legacy"].update(terminal=False),
            "boundary replaced by text": lambda b: b.update(terminal_boundary="none")}.items():
        assert not resealed(edit)["verified"], name

    # R-F1 de la revision: reescribir ENTERO y coherente el lado heredado. Borrar el paro se ve, porque la
    # propia corrida registro la divergencia de pulso; lo demas queda fuera de la coherencia interna, declarado.
    def rewritten(legacy, declared=False):
        def edit(body):
            last = body["runs"][store.SESSION_RUN_NAME]["minutes"][-1]["channels"]
            body["terminal_boundary"] = fam.terminal_boundary(legacy, last, declared)
        return resealed(edit)

    assert not rewritten({"arrest_at": None, "vf_at": None})["verified"]            # el paro borrado
    assert not rewritten(None)["verified"]                                          # o vuelto "desconocido"
    beyond = rec.BOUNDARY["verification_does_not_see"]
    assert rewritten({"arrest_at": 3, "vf_at": None})["verified"] and "minute" in beyond[0]      # declarado
    assert resealed(lambda b: b.pop("terminal_boundary"))["verified"] and "removed" in beyond[1]  # declarado
    assert "replay" in beyond[2]
    assert rec.BOUNDARY["implemented"].startswith("IMPLEMENTED_RUNTIME")


# -- A2-007 a A2-010: identificabilidad, diseno y veredicto ---------------------------------------------------------------------------

def test_a2_007_no_threshold_is_identifiable_and_none_was_invented():
    found = rec.IDENTIFIABILITY
    assert all(row["evidence"] in rec.EVIDENCE_CLASSES and row["usable_as_a_threshold"] is False
               for row in found["evidence"])
    assert not [row for row in found["evidence"] if row["evidence"] == "FACULTY_DEFINED"]
    assert found["development_regions"] == () and len(found["faculty_questions"]) == 6
    assert all(question.count("?") >= 1 for question in found["faculty_questions"])
    # el nucleo de ENTONCES es byte a byte el certificado (la Enmienda 1, reconstruida desde el arbol vivo)
    assert a2.amended_core_digest_now() == rs.CORE_LINEAGE[-1].digest
    assert a2.amendment_1_verifies()["digest_recomputes"] and rs.CORE_LINEAGE[1].digest == rec.LINEAGE["parent"]["digest"]
    # y la capa de sombra no trae ningun umbral clinico nuevo para la frontera
    for name in ("TERMINAL", "PREDICATE", "CONSCIOUSNESS", "ARREST", "APNOEA"):
        for attribute in dir(fam):
            if name in attribute:
                assert not isinstance(getattr(fam, attribute), (int, float)), attribute


def test_a2_008_the_design_separates_required_optional_and_not_justified():
    design = rec.DESIGN
    assert len(design["required_now"]) == 4 and design["optional_later"] and design["not_justified"]
    blocked = [row for row in design["required_now"] if row["blocked_on"]]
    assert len(blocked) == 3 and design["required_now"][-1].get("done")
    assert "a single terminal scalar" in design["not_justified"]
    assert any("SpO2 -> unconscious" in item for item in design["not_justified"])
    assert any("legacy" in item for item in design["not_justified"])
    assert len(design["output_contract"]) == 5


def test_a2_009_and_010_the_core_was_not_touched_and_the_verdict_is_one_of_the_four():
    design = rec.DESIGN
    assert design["implementation"]["common_core"] == "INTENTIONALLY_STOPPED"
    assert design["verdict"] == "AMENDMENT_2_BLOCKED_ON_FACULTY_THRESHOLDS"
    assert design["verdict"] in design["verdict_options"] and len(design["verdict_options"]) == 4
    assert design["full_certification_required"] is False and design["certified"] is False
    # P3-173: el diseno decidio detenerse; hoy la Enmienda 2 existe como etapa certificada y el registro de diseno
    # sigue diciendo lo que dijo (no se reescribe).
    assert (CORE / "amendment_2.py").exists() and rs.CORE_LINEAGE[-1].version_id == "PHASE2_AMENDMENT_2"
    assert "Amendment 2" in rec.NOT_CLAIMED[3] and "any change to common physiology" in rec.NOT_CLAIMED


# -- P3-169 a P3-171 ----------------------------------------------------------------------------------------------------------------

def test_p3_169_gi_is_the_preferred_future_case_and_nothing_is_deployed():
    review = rec.CASE_REVIEW
    assert review["preferred_future_case"] == "gi_bleed" == review["ranking"][0] == review["better_in_every_criterion"]
    assert review["ranking"] == previous.CASE_SELECTION["ranking"]
    assert review["first_pilot_modified"] is False and review["is_a_deployment"] is False
    assert list(review["comparison"]) == ["causal completeness", "live runtime readiness",
                                          "unsupported-action surface", "parameter uncertainty",
                                          "terminal/consciousness dependency", "trace interpretability",
                                          "faculty calibration burden"]
    assert all(row["gi_bleed"] and row["opioid"] for row in review["comparison"].values())
    # lo que la comparacion afirma del runtime: GI no tiene regla de paro en el motor heredado
    untreated = _play(GI, (), until=120)
    assert not untreated.arrested and untreated.shadow.legacy_terminal == {"arrest_at": None, "vf_at": None}
    assert list(rec.FACULTY_DECISIONS) == [f"FD-NEW-{letter}" for letter in "ABCDEF"]


def test_p3_170_and_171_readiness_and_the_shortest_path():
    impact = rec.PILOT_IMPACT
    assert impact["readiness"] == impact["gi_bleed"]["verdict"] == impact["opioid"]["verdict"] == \
        "NOT_READY_FOR_RESIDENT_PILOT_REVIEW"
    before = {gate["gate"]: gate["status"] for gate in previous.GATES}
    for name, gate in impact["gates"].items():
        assert gate["before"] == before[name], name
    assert impact["gates"]["resident-facing safety"]["status"] == "BLOCKED"
    assert impact["gates"]["case selection"]["status"] == "GREEN" and "no case is deployed" in impact["gates"][
        "case selection"]["scope"]
    assert impact["gi_bleed"]["terminal_contradiction_today"] is False
    assert impact["opioid"]["terminal_contradiction_today"] is True
    roadmap = rec.ROADMAP
    assert roadmap["case"] == "gi_bleed" and roadmap["next_step_is_another_physiology_family"] is False
    assert len(roadmap["critical_path"]) == 5 and "faculty" in roadmap["critical_path"][0]
    assert "not deployment" in roadmap["target"] and rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    source = (ROOT / "terminal_amendment_record.py").read_text(encoding="utf-8")
    assert "import " not in source and "runtime_" + "shadow" not in source and "phase3_" + "shadow" not in source
