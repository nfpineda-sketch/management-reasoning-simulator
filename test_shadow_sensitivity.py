"""Ciclo de observabilidad de la sombra en vivo (2026-11-10): P3-151, P3-152, P3-154 y P3-155.

- P3-151: auditoria ACOTADA de sensibilidad de los parametros sinteticos del opioide (bandas de llegada, tasa de
  profundizacion, tasa de recuperacion). Solo lectura y calculo: un parametro a la vez, sobre un adaptador de
  desarrollo, con los UNICOS valores que el repositorio ya tiene. Ninguno se inventa, y el conjunto por region
  no gana dimensiones;
- P3-152: el minuto de la descongestion del adaptador de desarrollo del edema, igualado a la regla de tiempo
  de la capa, sin tocar la magnitud ni la fisiologia comun;
- P3-154 y P3-155: las nueve compuertas y la hoja de ruta, leidas del registro.

Nada aqui es un valor clinico ni una recomendacion: son sondas de desarrollo sobre un caso.

Registro: shadow_observability_record. Etiquetas ``p3o``.
"""
import dataclasses
from pathlib import Path

import pytest

import management_causality as mc
import management_generalization_record as mgrec
import runtime_shadow as rs
import runtime_shadow_families as fam
import second_live_family_record as previous
import shadow_observability_record as rec
import test_management_generalization as mg
from clinical_core import derived as dv
from clinical_core import opioid_migration as om
from clinical_core import opioid_reference

ROOT = Path(__file__).resolve().parent
CASE = "opioid_35m"
R, FIELD = fam.TRANSMISSION_DECLARED_R, fam.TRANSMISSION_FIELD
WITNESSES = dict(fam.TRANSMISSION_WITNESSES)
END = mg.OPIOID_MINUTES
FLOOR = mg.TARGET["spo2_low"]

#: Un parametro a la vez. Cada valor esta YA en el repositorio; ``test_p3o_151a`` lo comprueba uno por uno.
CONFIGS = {
    "committed": {},
    "arrival_lower": {"point": "lower"}, "arrival_upper": {"point": "upper"},
    "recovery_0.5": {"recovery": 0.5}, "recovery_0.9": {"recovery": 0.9},
    "deepening_0.02": {"deepening": 0.02}, "deepening_0.03": {"deepening": 0.03},
}
CONFIGS_OF = {"arrival_bands": ("arrival_lower", "arrival_upper"),
              "opioid_recovery_rate": ("recovery_0.5", "recovery_0.9"),
              "opioid_deepening_rate": ("deepening_0.02", "deepening_0.03")}


def _variant(fraction, *, deepening=om.DEEPENING_PER_MIN, recovery=om.NALOXONE["recovery_per_min"],
             point="midpoint"):
    """Un adaptador de DESARROLLO con un parametro sintetico movido. Nunca se registra; el comprometido no cambia."""
    profile = dataclasses.replace(om.profile(), respiratory_quotient=R, **{FIELD: fraction})

    class Variant(fam.OpioidAdapter):
        def profile(self, _point):
            return profile

        def anchors(self, case_id, _point, state=None):
            return opioid_reference.anchors(case_id, point)

        def writers(self, case_id, _point, state=None):
            return (om.depression(deepening),)

        def interventions(self, mirrored, state=None):
            built, gaps = super().interventions(mirrored, state)
            return tuple(om.naloxone(rate=recovery, start=item.start_minute)
                         if type(item).__name__ == "NaloxoneReversal" else item for item in built), gaps

    return Variant()


def _arms(fraction, **changes):
    adapter = _variant(fraction, **changes)
    run = lambda events=(): mg._run(adapter, CASE, events, minutes=END)
    return {"untreated": run(), "oxygen": run(mg._oxygen()), "naloxone": run(mg._naloxone()),
            "oxygen_and_naloxone": run(mg._oxygen() + mg._naloxone()), "delayed_naloxone": run(mg._naloxone(60)),
            "wait": run(mg._reassess())}


def _bound(**changes) -> dict:
    """La cota superior de la region, por la MISMA formula certificada de la que salio 0,060621."""
    off = mg._run(_variant(0.0, **changes), CASE, minutes=60)
    base = off.series["spo2"][60]
    linked = dataclasses.replace(om.profile(), respiratory_quotient=R)
    delta = off.series["paco2"][60] - dv.arrival_paco2_reference(off.runner.anchors, linked)
    upper = (dv.pao2_from_oxygen_saturation(base) - dv.pao2_from_oxygen_saturation(FLOOR)) * R / delta
    return {"spo2_60_at_f0": base, "delta_paco2_60": delta, "f_upper": upper}


def _measure(**changes) -> dict:
    region = _bound(**changes)
    by_witness = {name: _arms(fraction, **changes) for name, fraction in WITNESSES.items()}
    verdicts, endpoints = {}, {}
    for name, arms in by_witness.items():
        base, reversal, oxygen, late = (arms[key] for key in ("untreated", "naloxone", "oxygen",
                                                             "delayed_naloxone"))
        s = lambda run, channel: run.series[channel]
        verdicts[name] = {
            "untreated_downhill": (s(base, "spo2")[END] < s(base, "spo2")[1]
                                   and s(base, "paco2")[END] > s(base, "paco2")[1]
                                   and s(base, "central_availability")[END] < s(base, "central_availability")[1]),
            "reversal_direction": (mc.direction(s(reversal, "spo2"), s(base, "spo2"), END, better="higher")
                                   and mc.direction(s(reversal, "paco2"), s(base, "paco2"), END, better="lower")),
            "reversal_first_effect_minute": mc.effect_starts_at(s(reversal, "central_availability"),
                                                                s(base, "central_availability"), 1),
            "no_effect_before_activation": mc.no_effect_before(s(reversal, "spo2"), s(base, "spo2"), 21),
            "oxygen_raises_saturation": mc.direction(s(oxygen, "spo2"), s(base, "spo2"), END, better="higher"),
            "oxygen_leaves_ventilation": (mc.untouched(s(oxygen, "paco2"), s(base, "paco2"))
                                          and mc.untouched(s(oxygen, "central_availability"),
                                                           s(base, "central_availability"))),
            "early_beats_late": (mg._area(s(reversal, "spo2"), END) > mg._area(s(late, "spo2"), END)
                                 > mg._area(s(base, "spo2"), END)),
            "waiting_is_not_a_treatment": arms["wait"].runner.digests() == base.runner.digests(),
            "replays": all(mg._replays(run) for run in arms.values()),
            "no_run_failed": all(run.runner.failures == [] for run in arms.values()),
            "saturation_reached_its_floor": min(s(base, "spo2").values()) == 0.0,
        }
        endpoints[name] = {"untreated_spo2": s(base, "spo2")[END], "reversal_spo2": s(reversal, "spo2")[END],
                           "untreated_paco2": s(base, "paco2")[END]}
    arms = by_witness["CENTER_REFERENCE"]
    contract = mg._contract(
        treated=arms["naloxone"], base=arms["untreated"], primary="central_availability", observable="spo2",
        better="higher", activation=20,
        by_dose={WITNESSES[w]: {m: by_witness[w]["naloxone"].series["spo2"][m]
                                - by_witness[w]["untreated"].series["spo2"][m] for m in range(1, END + 1)}
                 for w in WITNESSES},
        dose_better=(END, "higher"), early=arms["naloxone"].series["spo2"],
        late=arms["delayed_naloxone"].series["spo2"],
        reversible=arms["naloxone"].series["paco2"][END] < arms["untreated"].series["paco2"][1], minutes=END)
    return {"region": region,
            "witnesses_inside_the_bound": [name for name, fraction in WITNESSES.items()
                                           if fraction <= region["f_upper"]],
            "verdicts": verdicts, "endpoints": endpoints,
            "contract": {item: value for item, value in contract.items() if item != "moved_state_channels"}}


#: Que criterio de materialidad lee cada veredicto medido.
CRITERION_OF = {"untreated_downhill": "causal direction", "reversal_direction": "causal direction",
                "oxygen_raises_saturation": "causal direction", "oxygen_leaves_ventilation": "causal direction",
                "reversal_first_effect_minute": "temporal ordering",
                "no_effect_before_activation": "temporal ordering", "early_beats_late": "temporal ordering",
                "waiting_is_not_a_treatment": "temporal ordering", "replays": "live-versus-offline equivalence",
                "no_run_failed": "boundary", "saturation_reached_its_floor": "boundary"}


def _material(found: dict, committed: dict) -> list:
    """Los criterios de materialidad que CAMBIAN respecto del punto comprometido. Vacio: nada cambia."""
    changed = set()
    for witness, row in found["verdicts"].items():
        for item, value in row.items():
            if value != committed["verdicts"][witness][item]:
                changed.add(CRITERION_OF[item])
    if found["contract"] != committed["contract"]:
        changed.add("READY verdict")
    if found["witnesses_inside_the_bound"] != committed["witnesses_inside_the_bound"] or \
            abs(found["region"]["f_upper"] - committed["region"]["f_upper"]) > 1e-9:
        changed.add("region intersection")
    return [criterion for criterion in rec.MATERIALITY if criterion in changed]


def measure_sensitivity() -> dict:
    found = {name: _measure(**changes) for name, changes in CONFIGS.items()}
    committed = found["committed"]
    step = 0.01
    up, down = (_bound(deepening=om.DEEPENING_PER_MIN * (1 + sign * step))["f_upper"] for sign in (1, -1))
    return {
        "configs": {name: {"region": row["region"], "witnesses_inside_the_bound": row["witnesses_inside_the_bound"],
                           "contract": row["contract"], "endpoints": row["endpoints"],
                           "verdicts_that_differ_from_committed": {
                               witness: sorted(item for item, value in verdicts.items()
                                               if value != committed["verdicts"][witness][item])
                               for witness, verdicts in row["verdicts"].items()},
                           "material": _material(row, committed)} for name, row in found.items()},
        "committed_verdicts": committed["verdicts"],
        #: La derivada local de la cota respecto de la tasa, en el punto comprometido: una propiedad de la
        #: ecuacion, no un intervalo. d ln(cota) / d ln(tasa), por diferencia central de +-1 %.
        "bound_elasticity_to_the_deepening_rate": ((up - down) / committed["region"]["f_upper"]) / (2 * step),
    }


@pytest.fixture(scope="module")
def sensitivity():
    return measure_sensitivity()


# -- P3-151 -------------------------------------------------------------------------------------------------------

def test_p3o_151a_every_value_used_is_already_in_the_repository_and_none_is_invented():
    parameters = rec.SENSITIVITY["parameters"]
    assert set(parameters) == set(CONFIGS_OF) and rec.SENSITIVITY["ranges_used"].endswith("none is invented")
    # las bandas de llegada: los tres puntos declarados del mapeo de referencia certificado
    assert parameters["arrival_bands"]["values"] == om.POINTS == tuple(opioid_reference.INTRINSIC_POINTS)
    assert parameters["arrival_bands"]["interval_is_defensible"] is True
    bands = opioid_reference.bands(CASE)
    assert {"arrival_lactate_excess", "intrinsic_sinus_rate", "arrival_central_availability"} <= set(bands)
    # la tasa de recuperacion: el punto comprometido y dos sondas estructurales de las pruebas certificadas
    probes = (ROOT / "test_clinical_core_opioid_migration.py").read_text(encoding="utf-8")
    assert parameters["opioid_recovery_rate"]["values"] == (om.NALOXONE["recovery_per_min"], 0.5, 0.9)
    assert "un.naloxone(0.5, 0)" in probes and "un.naloxone(0.9, 0)" in probes
    # la tasa de profundizacion: el punto comprometido, la sonda de recurrencia y la de direccion de colapso
    assert parameters["opioid_deepening_rate"]["values"] == (
        om.DEEPENING_PER_MIN, om.RECURRENCE["deepening_per_min"], om.SEVERE_DEEPENING_PER_MIN) == (0.005, 0.02, 0.03)
    # y el propio repositorio dice que para las dos tasas NO hay intervalo declarado
    provenance = " ".join(fam.OpioidAdapter.witness("LOW").snapshot().provenance)
    assert "no span is declared" in provenance and "SYNTHETIC_ONLY" in provenance
    for name in ("opioid_recovery_rate", "opioid_deepening_rate"):
        assert parameters[name]["interval_is_defensible"] is False
    # cada configuracion mueve UN parametro
    assert all(len(changes) <= 1 for changes in CONFIGS.values())
    assert {name for names in CONFIGS_OF.values() for name in names} | {"committed"} == set(CONFIGS)


def test_p3o_151b_the_committed_point_is_the_certified_series(sensitivity):
    committed = sensitivity["configs"]["committed"]
    assert round(committed["region"]["f_upper"], 6) == 0.060621 == fam.TRANSMISSION_ACTIVE_REGION["up_to"]
    assert committed["witnesses_inside_the_bound"] == list(WITNESSES) and committed["material"] == []
    for witness, row in sensitivity["committed_verdicts"].items():
        assert row == {"untreated_downhill": True, "reversal_direction": True, "reversal_first_effect_minute": 21,
                       "no_effect_before_activation": True, "oxygen_raises_saturation": True,
                       "oxygen_leaves_ventilation": True, "early_beats_late": True,
                       "waiting_is_not_a_treatment": True, "replays": True, "no_run_failed": True,
                       "saturation_reached_its_floor": False}, witness
    assert all(value in (True, None) for value in committed["contract"].values())
    assert committed["contract"] == mgrec.MEASURED["contract"]["opioid"]            # la misma serie certificada


def test_p3o_151c_the_arrival_band_changes_no_verdict_and_not_the_region(sensitivity):
    committed = sensitivity["configs"]["committed"]
    for name in CONFIGS_OF["arrival_bands"]:
        found = sensitivity["configs"][name]
        assert found["material"] == [] and found["contract"] == committed["contract"], name
        # la cadena sin tratar es la misma en los tres puntos: el punto se cancela en la composicion, y lo
        # que queda es redondeo de coma flotante (no es identidad bit a bit, y no se dice que lo sea)
        for item, value in committed["region"].items():
            assert found["region"][item] == pytest.approx(value, rel=1e-12, abs=1e-12), (name, item)
        assert all(found["endpoints"][w]["untreated_spo2"] == pytest.approx(
            committed["endpoints"][w]["untreated_spo2"], abs=1e-9) for w in WITNESSES)
        # lo unico que se mueve es la magnitud de la rama tratada
        assert any(found["endpoints"][w]["reversal_spo2"] != committed["endpoints"][w]["reversal_spo2"]
                   for w in WITNESSES)
    assert rec.SENSITIVITY["parameters"]["arrival_bands"]["verdict"] == \
        "SENSITIVITY_NON_MATERIAL_FOR_CURRENT_VERDICT"


def test_p3o_151d_the_recovery_rate_changes_no_verdict_at_the_values_the_repository_holds(sensitivity):
    committed = sensitivity["configs"]["committed"]
    for name in CONFIGS_OF["opioid_recovery_rate"]:
        found = sensitivity["configs"][name]
        assert found["material"] == [] and found["contract"] == committed["contract"], name
        assert found["region"] == committed["region"]                    # la cota sale de la rama SIN tratar
    # sin intervalo declarado no se afirma nada entre esos valores ni mas alla: queda sintetico
    assert rec.SENSITIVITY["parameters"]["opioid_recovery_rate"]["verdict"] == \
        "SYNTHETIC_ONLY_NO_DEFENSIBLE_REGION"


def test_p3o_151e_the_region_bound_is_conditional_on_the_deepening_rate(sensitivity):
    committed = sensitivity["configs"]["committed"]
    bounds = {name: sensitivity["configs"][name]["region"] for name in ("committed",) +
              CONFIGS_OF["opioid_deepening_rate"]}
    # la cota es inversamente proporcional a la subida de PaCO2 sin tratar que la tasa produce
    products = [row["f_upper"] * row["delta_paco2_60"] for row in bounds.values()]
    assert all(row["spo2_60_at_f0"] == committed["region"]["spo2_60_at_f0"] for row in bounds.values())
    assert max(products) - min(products) < 1e-9
    assert bounds["committed"]["f_upper"] > bounds["deepening_0.02"]["f_upper"] > bounds["deepening_0.03"]["f_upper"]
    assert [round(row["f_upper"], 6) for row in bounds.values()] == [0.060621, 0.00901, 0.004076]
    # en las dos sondas TODOS los testigos quedan fuera de la cota
    for name in CONFIGS_OF["opioid_deepening_rate"]:
        found = sensitivity["configs"][name]
        assert found["witnesses_inside_the_bound"] == [] and "region intersection" in found["material"], name
        assert WITNESSES["LOW"] > found["region"]["f_upper"]
    assert "causal direction" in sensitivity["configs"]["deepening_0.02"]["material"]
    assert set(sensitivity["configs"]["deepening_0.03"]["material"]) >= {"causal direction", "boundary",
                                                                         "region intersection"}
    # lo que se sostiene en todos los valores: la direccion y el tiempo de la reversion, y el replay
    for name in CONFIGS_OF["opioid_deepening_rate"]:
        differing = sensitivity["configs"][name]["verdicts_that_differ_from_committed"]
        moved = {item for items in differing.values() for item in items}
        assert moved <= {"oxygen_leaves_ventilation", "oxygen_raises_saturation", "saturation_reached_its_floor"}
        assert "temporal ordering" not in sensitivity["configs"][name]["material"]
        assert "live-versus-offline equivalence" not in sensitivity["configs"][name]["material"]
    assert differing_low_is_clean(sensitivity)
    # y la derivada local en el punto comprometido: mas que proporcional
    assert sensitivity["bound_elasticity_to_the_deepening_rate"] < -1.0


def differing_low_is_clean(sensitivity) -> bool:
    """En el testigo BAJO ningun veredicto cambia, ni en la sonda mas severa."""
    return all(sensitivity["configs"][name]["verdicts_that_differ_from_committed"]["LOW"] == []
               for name in CONFIGS_OF["opioid_deepening_rate"])


def test_p3o_151f_each_verdict_follows_from_the_measurement_and_nothing_is_promoted(sensitivity):
    assert rec.SENSITIVITY_VERDICTS == ("ENSEMBLE_REQUIRED", "SENSITIVITY_NON_MATERIAL_FOR_CURRENT_VERDICT",
                                        "SYNTHETIC_ONLY_NO_DEFENSIBLE_REGION")
    material = {}
    for parameter, names in CONFIGS_OF.items():
        info = rec.SENSITIVITY["parameters"][parameter]
        changed = sorted({criterion for name in names for criterion in sensitivity["configs"][name]["material"]})
        material[parameter] = changed
        derived = ("SYNTHETIC_ONLY_NO_DEFENSIBLE_REGION" if not info["interval_is_defensible"] else
                   "ENSEMBLE_REQUIRED" if changed else "SENSITIVITY_NON_MATERIAL_FOR_CURRENT_VERDICT")
        assert info["verdict"] == derived and derived in rec.SENSITIVITY_VERDICTS, parameter
    assert material["arrival_bands"] == [] == material["opioid_recovery_rate"] and material["opioid_deepening_rate"]
    deepening = rec.SENSITIVITY["parameters"]["opioid_deepening_rate"]
    assert deepening["material_at_repository_probe_values"] is True and "NOT promoted" in deepening["open_question"]
    # ningun parametro se promueve: el conjunto sigue siendo UNA dimension con tres testigos
    assert "ENSEMBLE_REQUIRED" not in [info["verdict"] for info in rec.SENSITIVITY["parameters"].values()]
    assert rec.SENSITIVITY["ensemble_dimensionality_changed"] is False
    registered = fam.ADAPTERS["opioid"]
    assert list(registered.region_witnesses()) == ["LOW", "CENTER_REFERENCE", "HIGH"]
    assert dict(fam.TRANSMISSION_WITNESSES) == {"LOW": 0.015, "CENTER_REFERENCE": 0.03, "HIGH": 0.06}
    assert [writer.deepening_per_min for writer in registered.writers(CASE, fam.COMMITTED)] == [om.DEEPENING_PER_MIN]
    assert {field.name for field in dataclasses.fields(fam.RegionEnsemble)} >= {"parameter", "runners"}
    assert fam.RegionEnsemble.open("opioid", CASE).parameter == fam.TRANSMISSION_FIELD
    assert "AT the committed deepening rate" in rec.SENSITIVITY["region_statement"]


def test_p3o_151g_the_recorded_table_is_what_the_runtime_gives_now(sensitivity):
    assert mg._rounded(sensitivity, 6) == rec.MEASURED["sensitivity"]


# -- P3-152 -------------------------------------------------------------------------------------------------------

EDEMA_CASE = mg.EDEMA_CASE


def _treatment(adapter, minute):
    built, gaps = adapter.interventions(mg._diuretic(minute))
    assert gaps == [] and len(built) == 1
    return built[0]


def test_p3o_152a_the_treatment_begins_the_minute_after_its_order():
    adapter = fam.PulmonaryEdemaAdapter.development("CENTER_REFERENCE")
    for minute in (0, 1, 30, 90):
        treatment = _treatment(adapter, minute)
        assert type(treatment).__name__ == "DecongestiveTreatment" and treatment.begins_at_minute == minute + 1
    assert rec.EDEMA_TIMING["first_effect_minute"] == {"before": 30, "after": 31, "order_minute": 30}
    # el adaptador REGISTRADO no cambia: sigue declarando el hueco y sigue sin estar en vivo
    registered = fam.ADAPTERS["pulmonary_edema"]
    assert registered.decongestion_witness is None and registered.live is False
    built, gaps = registered.interventions(mg._diuretic(30))
    assert built == () and [gap["kind"] for gap in gaps] == ["diuretic"]
    assert "pulmonary_edema" not in rs.LIVE_FAMILIES


def test_p3o_152b_one_timing_rule_for_every_mapped_order():
    """Pedido en el minuto m, presente en el estado del m + 1: oxigeno, reversion y descongestion por igual."""
    edema = fam.PulmonaryEdemaAdapter.development("CENTER_REFERENCE")
    plain = mg._run(edema, EDEMA_CASE, minutes=60)
    channels = mg.STATE_CHANNELS + mg.AUX_CHANNELS
    assert min(mg._first_moved(mg._run(edema, EDEMA_CASE, mg._oxygen(10), minutes=60), plain, channels).values()) == 11
    assert min(mg._first_moved(mg._run(edema, EDEMA_CASE, mg._diuretic(30), minutes=60), plain, channels).values()) == 31
    opioid = mg._linked(fam.OpioidAdapter, om, WITNESSES["CENTER_REFERENCE"])
    base = mg._run(opioid, CASE, minutes=60)
    assert min(mg._first_moved(mg._run(opioid, CASE, mg._naloxone(20), minutes=60), base, channels).values()) == 21
    assert min(mg._first_moved(mg._run(opioid, CASE, mg._oxygen(10), minutes=60), base, channels).values()) == 11
    assert "m + 1" in rec.EDEMA_TIMING["after"]


class _DatedAtTheOrder(fam.PulmonaryEdemaAdapter):
    """El adaptador como era ANTES de P3-152, para medir exactamente que cambio. Solo en esta prueba."""

    def interventions(self, mirrored, state=None):
        from clinical_core.modules.pulmonary_edema import DecongestiveTreatment
        built, gaps = super().interventions(mirrored, state)
        return tuple(DecongestiveTreatment(item.id, max(1, item.begins_at_minute - 1))
                     if type(item).__name__ == "DecongestiveTreatment" else item for item in built), gaps


@pytest.mark.parametrize("witness", tuple(fam.EDEMA_DECONGESTION_WITNESSES))
def test_p3o_152c_the_change_is_one_minute_and_nothing_else(witness):
    now = fam.PulmonaryEdemaAdapter.development(witness)
    before = _DatedAtTheOrder.development(witness)
    assert now.decongestion_per_min == before.decongestion_per_min == fam.EDEMA_DECONGESTION_WITNESSES[witness]
    # la corrida de hoy con el pedido en el 30 ES la de antes con el pedido en el 31, estado por estado
    today = mg._run(now, EDEMA_CASE, mg._diuretic(30), minutes=mg.EDEMA_MINUTES)
    shifted = mg._run(before, EDEMA_CASE, mg._diuretic(31), minutes=mg.EDEMA_MINUTES)
    assert today.runner.digests() == shifted.runner.digests()
    # y los numeros de antes y de despues son los registrados
    old = mg._run(before, EDEMA_CASE, mg._diuretic(30), minutes=mg.EDEMA_MINUTES)
    back = lambda run: min(m for m in range(30, mg.EDEMA_MINUTES + 1) if run.series["L"][m] == 0.0)
    assert back(old) == rec.EDEMA_TIMING["back_to_arrival_minute"]["before"][witness]
    assert back(today) == rec.EDEMA_TIMING["back_to_arrival_minute"]["after"][witness] == \
        mgrec.MEASURED["edema"][witness]["back_to_arrival_at_minute"]
    plain = mg._run(now, EDEMA_CASE, minutes=mg.EDEMA_MINUTES)
    assert mc.effect_starts_at(old.series["L"], plain.series["L"], 1) == 30
    assert mc.effect_starts_at(today.series["L"], plain.series["L"], 1) == 31


def test_p3o_152d_no_causal_verdict_changed_and_the_region_is_the_same():
    from clinical_core import edema_migration as em
    assert fam.EDEMA_DECONGESTION_WITNESSES == {"LOW": 0.0025, "CENTER_REFERENCE": 0.005, "HIGH": 0.01}
    assert fam.EDEMA_DECONGESTION_REGION == (em.PROGRESSION[0], em.PROGRESSION[-1])
    assert rec.EDEMA_TIMING["magnitude_region_changed"] is False
    assert rec.EDEMA_TIMING["common_physiology_changed"] is False
    # el contrato de las seis vias, tal como lo recalcula y fija la serie de generalizacion: igual que antes
    assert mgrec.MEASURED["contract"]["pulmonary_edema"] == {
        "DIRECTION": True, "TEMPORALITY": True, "CAUSAL_SPECIFICITY": True, "MAGNITUDE_PLAUSIBILITY": True,
        "DOSE_ORDERING": True, "REVERSIBILITY": True, "TIME_WITHOUT_ACTION": True, "SAFETY": True}
    assert mgrec.MEASURED["moved_state_channels"]["pulmonary_edema"] == ["G", "L", "sympathetic_drive"]
    assert mgrec.EDEMA["verdict"] == "PULMONARY_EDEMA_MANAGEMENT_CAUSALITY_READY"
    assert rec.EDEMA_TIMING["contract_verdicts_changed"] is False
    assert rec.EDEMA_TIMING["verdict"] == "PULMONARY_EDEMA_TIMING_CORRECTED_NO_VERDICT_CHANGE"
    # el contribuyente certificado del nucleo sigue actuando en su propio minuto de inicio: no se toco
    from clinical_core.modules.pulmonary_edema import DecongestiveTreatment
    assert [field.name for field in dataclasses.fields(DecongestiveTreatment)][:2] == ["id", "begins_at_minute"]


# -- P3-154 y P3-155 ----------------------------------------------------------------------------------------------

GATE_STATES = ("GREEN", "PARTIAL", "BLOCKED", "NOT_YET_EVALUATED")


def test_p3o_154a_the_nine_gates_are_the_same_gates_read_again():
    assert [gate["gate"] for gate in rec.GATES] == [gate["gate"] for gate in previous.GATES] and len(rec.GATES) == 9
    before = {gate["gate"]: gate["status"] for gate in previous.GATES}
    for gate in rec.GATES:
        assert gate["status"] in GATE_STATES and gate["before"] == before[gate["gate"]], gate["gate"]
        assert gate["evidence"] and (gate["blocker"] is None) == (gate["status"] == "GREEN"), gate["gate"]
    counts = {state: sum(1 for gate in rec.GATES if gate["status"] == state) for state in GATE_STATES}
    pilot = rec.READINESS["RESIDENT_PILOT_DEPLOYMENT_READINESS"]
    assert pilot["gates"] == counts == {"GREEN": 4, "PARTIAL": 1, "BLOCKED": 3, "NOT_YET_EVALUATED": 1}
    moved = tuple(gate["gate"] for gate in rec.GATES if gate["status"] != gate["before"])
    assert moved == pilot["moved_this_cycle"] == ("trace capture", "failure visibility")
    assert pilot["still_blocked"] == tuple(gate["gate"] for gate in rec.GATES if gate["status"] == "BLOCKED")
    # una compuerta que se mueve a verde dice hasta donde llega ese verde
    assert all(gate.get("scope") for gate in rec.GATES if gate["gate"] in moved)


def test_p3o_154b_a_faculty_observer_does_not_make_resident_exposure_green():
    by_name = {gate["gate"]: gate for gate in rec.GATES}
    for name in ("UI exposure", "runtime exposure", "resident-facing safety"):
        assert by_name[name]["status"] == "BLOCKED" and by_name[name]["blocker"], name
    assert "does not make this green" in by_name["UI exposure"]["blocker"]
    assert by_name["faculty review workflow"]["status"] == "PARTIAL"
    assert by_name["case selection"]["status"] == "NOT_YET_EVALUATED"
    # tres respuestas, por separado
    assert set(rec.READINESS) == {"SIMULATION_ENGINE_READINESS", "FACULTY_REVIEW_READINESS",
                                  "RESIDENT_PILOT_DEPLOYMENT_READINESS"}
    assert rec.READINESS["RESIDENT_PILOT_DEPLOYMENT_READINESS"]["verdict"] == \
        "NOT_READY_FOR_RESIDENT_PILOT_REVIEW" == rec.CHECKPOINT["pilot_verdict"]
    assert rec.READINESS["FACULTY_REVIEW_READINESS"]["verdict"] == rec.CHECKPOINT["faculty_review_verdict"]
    assert rec.READINESS["FACULTY_REVIEW_READINESS"]["verdict"].endswith("_IN_DEVELOPMENT")
    assert all(row["holds"] and row["does_not_hold"] for name, row in rec.READINESS.items()
               if name != "RESIDENT_PILOT_DEPLOYMENT_READINESS")
    # y lo que la compuerta dice del codigo, es del codigo
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "runtime_shadow_observer" not in app and "runtime_shadow_store" not in app
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    assert {"clinical validation", "resident readiness", "any change to common physiology"} <= set(
        rec.CHECKPOINT["not_claimed"])


def test_p3o_155a_the_roadmap_ranks_blockers_and_does_not_assume_more_physiology():
    roadmap = rec.ROADMAP
    assert roadmap["criteria"] == ("pilot_criticality", "architecture_cost", "educational_value", "risk")
    rows = roadmap["blockers"]
    assert len(rows) == 8 and all(set(roadmap["criteria"]) <= set(row) and row["needs"] for row in rows)
    assert all(0 <= row[item] <= 3 for row in rows for item in roadmap["criteria"])
    # el orden es el de la regla declarada, no una preferencia
    key = lambda row: (-row["pilot_criticality"], row["architecture_cost"] + row["risk"], -row["educational_value"])
    assert list(rows) == sorted(rows, key=key) and "architecture_cost + risk" in roadmap["rank_rule"]
    assert rows[0]["architecture_cost"] == rows[0]["risk"] == 0 and "no code" in rows[0]["needs"]
    assert roadmap["next_step_is_another_physiology_family"] is False and roadmap["is_a_selection"] is False
    assert "physiology families" in rows[-1]["blocker"] and rows[-1]["pilot_criticality"] == 0
    assert len(roadmap["shortest_critical_path"]) == 3 and "faculty review" in roadmap["shortest_critical_path"][0]
    # las decisiones que abrieron el ciclo estan todas, cada una con su fila
    assert list(rec.FACULTY_DECISIONS) == [f"FD-NEW-{n}" for n in range(1, 6)]
    assert [row["row"] for row in rec.FACULTY_DECISIONS.values()] == [f"FD-P3-{n}" for n in range(139, 144)]
    text = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    for row in rec.FACULTY_DECISIONS.values():
        assert f"| {row['row']} |" in text, row["row"]
