"""P3-81 a P3-87: fija el registro de la región de comportamiento y lo que la valida.

Ninguna prueba aprueba un punto de parámetros. Documento: docs/PHASE3_VOLUME_BEHAVIOUR_CALIBRATION.md
"""
import ast
import subprocess
import sys

import pytest

import blood_volume_region as bvr
import volume_behaviour_record as rec
from clinical_core import blood_anchors as ba
from clinical_core import blood_constraints as bc


# W1 - el registro y su estado ------------------------------------------------------------------------

def test_w1_the_record_status_is_behavioural_and_never_an_approval():
    assert rec.STATUS == "FACULTY_DEFINED_BEHAVIORAL_REGION"
    assert rec.RECORD["status"] == rec.STATUS
    text = " ".join(str(v) for v in rec.RECORD.values())
    for forbidden in rec.FORBIDDEN_STATUSES:
        assert rec.RECORD["status"] != forbidden
        assert forbidden not in text, forbidden          # ningún campo del registro lo lleva
    # y el módulo no asigna ninguno de esos rótulos a nada
    tree = ast.parse(open(rec.__file__, encoding="utf-8").read())
    assigned = {node.value.value for node in ast.walk(tree)
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)}
    assert not assigned & set(rec.FORBIDDEN_STATUSES)


def test_w2_the_recorded_ranges_are_the_existing_faculty_envelopes():
    """Ningún número clínico nuevo: los rangos salen de las envolventes congeladas."""
    assert rec.RECORD["R30_range"] == bc.DECISIONS["FD-BLD-05"]["envelopes"][30]
    assert rec.RECORD["R120_range"] == bc.DECISIONS["FD-BLD-05"]["envelopes"][120]
    assert rec.RECORD["Rpeak_range"][0] == bc.DECISIONS["FD-BLD-04"]["envelope"][0]
    assert rec.RECORD["fourth_observation_used"] is False


def test_w3_the_historical_fd_bld_04_band_is_not_rewritten():
    """La banda histórica queda tal cual; el techo efectivo vive aparte."""
    assert rec.FD_BLD_04_HISTORICAL_PEAK == bc.DECISIONS["FD-BLD-04"]["envelope"] == (0.15, 0.30)
    assert rec.COMMON_PEAK_CAP < rec.FD_BLD_04_HISTORICAL_PEAK[1]
    assert rec.RECORD["Rpeak_range"][1] == rec.COMMON_PEAK_CAP


def test_w4_the_other_case_cap_does_not_disappear():
    assert rec.CASE_PEAK_CAPS == {"gi_bleed_57m": 0.27072, "gi_bleed_72f": 0.28518}
    assert set(rec.CASE_PEAK_CAPS) == set(bc.CASES)
    assert rec.COMMON_PEAK_CAP == rec.CASE_PEAK_CAPS["gi_bleed_57m"]
    band = rec.case_only_peak_band("gi_bleed_72f")
    assert band == (0.27072, 0.28518) and band[0] < band[1]
    with pytest.raises(ValueError):
        rec.case_only_peak_band("un_caso_que_no_existe")


# W2 - la cuarta lectura que la docencia no nombró ----------------------------------------------------

def test_w5_the_three_coordinate_box_does_not_imply_the_frozen_sixty_minute_reading():
    """Contraejemplo medido: las tres coordenadas dentro y R60 fuera."""
    box = {"peak": rec.RECORD["Rpeak_range"], 30: rec.RECORD["R30_range"],
           120: rec.RECORD["R120_range"]}
    low = bvr.e_interval(0.9, 13.0, box, e_max=1.0)
    assert low != bvr.EMPTY
    b = bvr.behaviour(low[0], 0.9, 13.0)
    assert box["peak"][0] <= b["peak"] <= box["peak"][1]
    assert box[30][0] <= b[30.0] <= box[30][1]
    assert box[120][0] <= b[120.0] <= box[120][1]
    assert b[60.0] < rec.R60_RANGE_FROM_FROZEN_FD_BLD_05[0]      # y aun así viola la congelada


def test_w6_the_effective_region_carries_that_fourth_reading():
    assert rec.EFFECTIVE_REGION[60] == rec.R60_RANGE_FROM_FROZEN_FD_BLD_05
    assert rec.EFFECTIVE_REGION[60] == bc.DECISIONS["FD-BLD-05"]["envelopes"][60]
    # y con ella el contraejemplo de W5 deja de ser admisible: ese (s, tau) se vacía por completo
    assert bvr.e_interval(0.9, 13.0, rec.EFFECTIVE_REGION, e_max=1.0) == bvr.EMPTY
    # donde la región efectiva sí admite algo, R60 queda dentro en los dos extremos
    lo, hi, _, _ = bvr.e_interval(0.4, 60.0, rec.EFFECTIVE_REGION, e_max=1.0)
    for e in (lo, hi):
        b = bvr.behaviour(e, 0.4, 60.0)
        assert rec.EFFECTIVE_REGION[60][0] - 1e-12 <= b[60.0] <= rec.EFFECTIVE_REGION[60][1] + 1e-12


# W3 - validación de entradas -------------------------------------------------------------------------

def test_w7_entries_the_model_cannot_produce_are_rejected_by_name():
    good = {"Rpeak_range": (0.16, 0.26), "R30_range": (0.16, 0.24), "R120_range": (0.06, 0.14)}
    assert rec.validate_entry(good) == []
    rising = {**good, "R30_range": (0.16, 0.27)}
    assert rec.UNREACHABLE_ORDER in rec.validate_entry(rising)
    inverted = {**good, "R120_range": (0.14, 0.06)}
    assert any(r.startswith(rec.RANGE_INVERTED) for r in rec.validate_entry(inverted))
    wider = {**good, "Rpeak_range": (0.15, 0.30)}
    assert any(r.startswith(rec.OUTSIDE_RECORDED_REGION) for r in rec.validate_entry(wider))


def test_w8_there_are_no_hidden_defaults():
    assert rec.validate_entry({}) == ["FALTA_R30_range", "FALTA_R120_range", "FALTA_Rpeak_range"]
    assert "FALTA_Rpeak_range" in rec.validate_entry({"R30_range": (0.15, 0.25),
                                                      "R120_range": (0.05, 0.15)})


def test_w9_the_record_imports_neither_the_core_nor_the_authority_registry():
    tree = ast.parse(open(rec.__file__, encoding="utf-8").read())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    assert not any(n.startswith(("clinical_core", "runtime_authority", "runtime_shadow"))
                   for n in names), names
    out = subprocess.run([sys.executable, "-c",
                          "import volume_behaviour_record, sys; "
                          "print(any(m.startswith('clinical_core') for m in sys.modules))"],
                         capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False", out.stdout


# W4 - testigos contra el evaluador congelado ---------------------------------------------------------

def _volume_fails(e, s, tau):
    out = []
    for case in bc.CASES:
        v = dict(bc.evaluate(case, {"crystalloid_effective_ml_per_ml": e,
                                    "crystalloid_transient_share": s,
                                    "crystalloid_leak_tau_min": tau})["verdicts"]["primary"])
        out += [f"{case}:{n}" for n in ("FD-BLD-04", "FD-BLD-05", "FD-BLD-06") if v[n] is False]
    return out


def test_w10_an_interior_witness_satisfies_the_three_volume_constraints():
    lo, hi, _, _ = bvr.e_interval(0.4, 60.0, rec.EFFECTIVE_REGION, e_max=1.0)
    assert _volume_fails(0.5 * (lo + hi), 0.4, 60.0) == []


def test_w11_an_exact_boundary_witness_is_not_reliably_admissible_and_the_margin_fixes_it():
    """El evaluador compara de forma inclusiva sobre un valor que difiere de la forma cerrada en ~1e-16."""
    lo, _, _, _ = bvr.e_interval(0.4, 60.0, rec.EFFECTIVE_REGION, e_max=1.0)
    assert _volume_fails(lo, 0.4, 60.0) != []                      # exactamente en el borde: falla
    assert _volume_fails(lo * (1 + rec.WITNESS_INTERIOR_MARGIN), 0.4, 60.0) == []
    assert rec.WITNESS_INTERIOR_MARGIN > 0.0


def test_w12_the_pressure_constraints_do_not_move_across_the_volume_region():
    """P3-87-1: la region de volumen no informa la presion, y se mide, no se supone."""
    names = ("U-OUT", "U-HB", "FD-BLD-01", "FD-BLD-02", "SECOND-UNIT", "FD-BLD-03")
    seen = set()
    for e, s, tau in ((0.16, 0.2, 30.0), (0.33, 0.6, 30.0)):
        row = []
        for case in bc.CASES:
            v = dict(bc.evaluate(case, {"crystalloid_effective_ml_per_ml": e,
                                        "crystalloid_transient_share": s,
                                        "crystalloid_leak_tau_min": tau})["verdicts"]["primary"])
            row += [v[n] for n in names]
        seen.add(tuple(row))
    assert len(seen) == 1, seen


def test_w13_the_two_cases_squeeze_the_bleeding_rate_from_opposite_sides():
    """P3-87-2: fijar el volumen no desacopla la tasa; sigue siendo coordenada candidata."""
    committed = {"preload_scale_over_kappa_ml": 833.3333333333334, "preload_fraction": 0.5,
                 "crystalloid_effective_ml_per_ml": 0.22, "crystalloid_transient_share": 0.4,
                 "crystalloid_leak_tau_min": 60.0}
    def uout(rate):
        return {case: dict(bc.evaluate(case, {**committed, "bleed_ml_per_min": rate}
                                       )["verdicts"]["primary"])["U-OUT"] for case in bc.CASES}
    low, mid, high = uout(2.5), uout(2.75), uout(3.0)
    assert low["gi_bleed_57m"] is False and low["gi_bleed_72f"] is True
    assert all(mid.values())
    assert high["gi_bleed_57m"] is True and high["gi_bleed_72f"] is False


def test_w14_the_recorded_region_bounds_the_infused_to_effective_ambiguity():
    lo, hi = rec.RECORD["Rpeak_range"]
    assert 1.80 < hi / lo < 1.81           # P3-68C reportaba un factor 8 a 20, dependiente del tiempo
    assert ba.REFERENCE["crystalloid_effective_ml_per_ml"] < lo


def test_w15_the_provisional_reference_is_formally_classified_without_rewriting_history():
    h = rec.HISTORICAL_REFERENCE
    assert h["classification"] == "HISTORICAL_PROVISIONAL_NON_SURVIVING_REFERENCE"
    assert h["rewrites_frozen_history"] is False
    # el valor sigue intacto en el módulo congelado: esto rotula, no reescribe
    assert ba.REFERENCE[h["parameter"]] == h["value"] == 0.125
    assert h["value"] < rec.RECORD["Rpeak_range"][0]


def test_w16_the_sixty_minute_interpretation_is_recorded_as_confirmed_not_as_a_new_constraint():
    """Decisión docente del 2026-11-09: conserva una restricción ya vigente, no añade ninguna."""
    r = rec.R60_INTERPRETATION
    assert r["status"] == "CONFIRMED_BY_FACULTY"
    assert r["is_a_new_clinical_constraint"] is False
    assert r["rewrites_frozen_history"] is False
    # y lo que confirma es exactamente lo que la región efectiva lleva
    assert rec.EFFECTIVE_REGION[60] == bc.DECISIONS["FD-BLD-05"]["envelopes"][60]
