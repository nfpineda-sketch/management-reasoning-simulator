"""P2K-5 report: the generated blocks of docs/revision/P2K5_CIERRE_MONOTONIA_RESPIRATORIA.md.

    python -m clinical_core.respiratory_monotonicity_report --write <document> --data <the P2K-5 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
closure's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _s, _yes
from .lactate_rebuild_report import CASE_ES
from .ventilation_filter_report import DIM_ES, DOMAINS_ES, KLASS_ES, OBS_ES, R3R4_ES, _demand, _int

NAMES = ("decisiones", "regla", "ganancias", "sondas", "semantica", "reutilizacion", "poda", "latentes", "observables",
         "acidemia", "r3r4", "no_regresion", "inventario_n", "veredicto", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
CASES = ("gi_bleed_57m", "gi_bleed_72f")
FACULTY_ES = {"decided": "fecha", "closed": "P2K-4", "goal": "objetivo", "priority": "prioridad del proyecto",
              "rule": "regla estructural", "analytic": "regla analítica", "no_saturation": "sin saturación",
              "treatment": "semántica del tratamiento", "retained": "soporte que se mantiene",
              "reuse": "reutilización", "extreme_acidemia": "acidemia extrema", "r3_r4": "R3 / R4",
              "identifiability": "identificabilidad", "exit": "criterio de salida", "early_stop": "parada temprana",
              "scope": "alcance"}
GAIN_CLASS_ES = {"STRUCTURALLY_ADMISSIBLE_PRIMARY_SUPPORT": "admisible (soporte primario)",
                 "REJECTED_BY_ACID_BASE_MONOTONICITY": "rechazada por monotonía ácido-base"}
SUPPORT_CLASS_ES = {"WELL_CONSTRAINED": "bien acotado", "PARTIALLY_CONSTRAINED": "parcialmente acotado",
                    "POORLY_IDENTIFIED": "poco identificado", "NON_IDENTIFIABLE": "no identificable",
                    "STRUCTURALLY_BOUNDED_NON_IDENTIFIABLE": "acotado por estructura, no identificable dentro",
                    "STRUCTURALLY_BOUNDED_POORLY_IDENTIFIED": "acotado por estructura, poco identificado dentro",
                    "STRUCTURALLY_BOUNDED_PARTIALLY_CONSTRAINED": "acotado por estructura, parcialmente acotado"}
CROSS_ES = {"ROBUST_ACROSS_DEMAND": "robustas en ambas demandas", "DEMAND_1_0_ONLY": "sólo con demanda 1,0",
            "DEMAND_1_1_ONLY": "sólo con demanda 1,1", "DEMAND_INCOMPATIBLE": "incompatibles con ambas (soporte admisible)",
            "REJECTED_BY_ACID_BASE_MONOTONICITY": "fuera del soporte (ganancia 0,05 / 0,06)"}
CRITERIA_ES = {"upstream_unchanged": "fisiología previa intacta (archivos cerrados, región P2J-3, dominios)",
               "reuse_exact": "reutilización exacta (recuento de P2K-4 reproducido, álgebra del registro igual)",
               "region_nonempty": "la región podada no queda vacía",
               "ph_monotone": "pH no creciente con la carga para cada ganancia retenida",
               "envelopes_hold": "los supervivientes cumplen A–I y las ventanas de llegada",
               "treatment_responses_coherent": "respuestas a los tratamientos coherentes con la señal corregida",
               "r3_r4_physiological": "R3 / R4 sin colapso de estados",
               "latent_uncertainty_kept": "el resto del soporte latente intacto, sin elegir valor",
               "extreme_acidemia_carried": "las filas de acidemia extrema siguen en la región",
               "nothing_approved": "nada aprobado"}
PARADOX_ES = {"PH_RISES_WITH_HIGHER_ACID_BURDEN": "el pH sube con más carga",
              "PH_FALLS_WITH_LOWER_ACID_BURDEN": "el pH baja con menos carga"}
SIGN_ES = {-1: "−", 0: "0", 1: "+"}
N_ES = {"effective oxygen deficit": ("déficit efectivo de oxígeno", "derived.effective_oxygen_deficit, "
                                     "derived.acute_deficit_signal", "núcleo: impulsa la carga ácida y el impulso simpático"),
        "D (accumulated oxygen-delivery debt)": ("D (deuda acumulada de aporte de oxígeno)", "estado, Channel.D (C8)",
                                                 "núcleo: impulsa el lactato y el impulso simpático"),
        "pH / acidemia": ("pH / acidemia", "derived.respiration (P2K-2), ventilation.ventilated_respiration (P2K-3)",
                          "candidato en sombra, sólo salida; las filas de acidemia extrema sin tratamiento pasan a "
                          "CONSCIOUSNESS_COLLAPSE_REVIEW"),
        "PaCO2": ("PaCO2", "ventilation.ventilated_respiration (PaCO2_referencia / W)", "candidato en sombra, sólo salida"),
        "glucose": ("glucosa", "estado, Channel.GLUCOSE (C11, absoluta, del caso)",
                    "núcleo: término de hipoglucemia del impulso simpático (umbral provisional)"),
        "oxygenation": ("oxigenación", "SpO2 en derived._perfusion (FiO2 e intercambio gaseoso G); PaO2 sólo de autoría",
                        "núcleo: término de hipoxemia del impulso simpático (umbral provisional)"),
        "neurologic channel N": ("canal neurológico N", "estado, Channel.N (C9, depresión del SNC, desvío desde la llegada)",
                                 "existe: sólo guardia de integración; ningún módulo escribe N todavía"),
        "MAP / cerebral perfusion (not in the faculty's list)": (
            "PAM / perfusión cerebral (fuera de la lista docente)", "derived._perfusion (pressure_rel)",
            "núcleo: se ofrece a la decisión docente, no se da por supuesta")}
FORWARDED_ES = {"untreated_extreme_acidemia": "acidemia extrema sin tratamiento → CONSCIOUSNESS_COLLAPSE_REVIEW",
                "cross_demand": "clases entre demandas → la pregunta de la demanda (diagnóstico)",
                "latent": "incertidumbre latente explícita, propagada; ningún ciclo respiratorio por identificabilidad"}
REGION_ES = {"units": "unidades", "primary": "filtro primario", "support": "soporte", "demand_class": "clase de demanda"}
FROZEN = "**Regla (texto congelado, en inglés).**"


def _e(value: float) -> str:
    mantissa, exponent = f"{value:.1e}".split("e")
    return f"{mantissa.replace('.', ',')} × 10^{int(exponent)}".replace("-", "−")


def _frac(text: str) -> str:
    return text.replace("-", "−")


def render_decisiones(data: dict) -> str:
    faculty = data["design"]["faculty"]
    return "Texto congelado, en inglés, en el orden del encargo.\n\n" + "\n".join(
        f"- **{FACULTY_ES[k]}**: {faculty[k]}" for k in FACULTY_ES if k in faculty)


def render_regla(data: dict) -> str:
    a = data["analytic"]
    return "\n".join([f"**Ecuación (texto congelado).** {a['equation']}", "",
                      f"**Derivada y desigualdad (texto congelado).** {a['inequality']}", "",
                      f"**Ganancia crítica.** 1 / HCO3_referencia = {_frac(a['critical_gain'])} ≈ "
                      f"{_n(a['critical_gain_float'], 7)} por mEq/L (HCO3_referencia {_n(a['hco3_reference'], 0)}, "
                      f"PaCO2_referencia {_n(a['paco2_reference'], 0)}; ambas provisionales).", "",
                      f"**Alcance (texto congelado).** {a['scope']}"])


def render_ganancias(data: dict) -> str:
    lines = ["| ganancia | exacta | N(0) = g·24 − 1 | pendiente de N | pendiente del pH en A = 0 | intervalo donde el pH sube "
             "| pico | clase |", "|---|---|---|---|---|---|---|---|"]
    for key, row in data["analytic"]["gains"].items():
        interval = "ninguno" if row["rising_interval"] is None else \
            f"0 ≤ A < {_frac(row['rising_interval_exact'][1])} ({_n(row['rising_interval'][1], 2)})"
        peak = "—" if row["peak"] is None else \
            f"pH {_n(row['peak']['ph'], 4)} en A {_n(row['peak']['burden'], 2)} (pH {_n(row['peak']['ph_at_0'], 4)} en 0)"
        klass = GAIN_CLASS_ES[row["class"]] + (" · ya excluida en P2K-3 / P2K-4" if key == "0.08" else "")
        lines.append(f"| {_n(row['gain'], 2)} | {_frac(row['exact'])} | {_frac(row['n0'])} | {_frac(row['n_slope'])} | "
                     f"{_n(row['slope_at_0'], 5)} | {interval} | {peak} | {klass} |")
    return "\n".join(lines)


def render_sondas(data: dict) -> str:
    m, p = data["mapping"], data["probes"]
    lines = ["**El mapeo ejecutable es el analizado.** " + "; ".join(
        f"{CASE_ES[c]}: HCO3 de autoría {_n(m[c]['authored_hco3'], 1)}, carga de llegada {_n(m[c]['arrival_burden'], 1)}, "
        f"HCO3 a carga cero {_n(m[c]['zero_burden_bicarbonate'], 1)}; error máximo frente a la forma cerrada "
        f"{_e(max([m[c]['hco3_error']] + [e for r in m[c]['gas_error'].values() for e in r.values()]))}"
        for c in CASES) + ".", "",
        f"**Sondas sintéticas** ({len(p['rows'][CASES[0]]['0.03']['burdens'])} cargas por caso, de 0 a 23 mEq/L, con la de "
        f"llegada): con 0,03 y 0,04 el HCO3 baja, la PaCO2 baja y el pH no sube en ningún paso: "
        f"{_yes(p['admissible_non_increasing'])}. Con 0,05 y 0,06 el pH sube sólo en los pasos que empiezan dentro de "
        f"[0, A*): {_yes(p['rejected_rise_at_low_burden'])}. La PaCO2 baja con la carga en todas: "
        f"{_yes(p['paco2_falls_with_burden'])}.", "",
        "| caso | ganancia | pH en 0 | pH en la llegada | pasos en que el pH sube |", "|---|---|---|---|---|"]
    for c in CASES:
        for g, row in p["rows"][c].items():
            steps = "; ".join(f"{_n(a, 2)}→{_n(b, 2)}" for a, b in row["ph_rising_steps"]) or "ninguno"
            lines.append(f"| {CASE_ES[c]} | {_n(float(g), 2)} | {_n(row['ph'][0], 4)} | "
                         f"{_n(row['ph'][0] + row['ph_change_0_to_arrival'], 4)} | {steps} |")
    return "\n".join(lines)


def render_semantica(data: dict) -> str:
    s = data["semantics"]
    lines = [f"{FROZEN} {s['rule']}", "", "| perfusión | carga | pH | clase P2K-4 | clase P2K-5 | marca |",
             "|---|---|---|---|---|---|"]
    for r in s["transitions"]:
        if r["changed"] or r["paradox"]:
            lines.append(f"| {SIGN_ES[r['perfusion']]} | {SIGN_ES[r['burden']]} | {SIGN_ES[r['ph']]} | "
                         f"{KLASS_ES[r['p2k4']]} | {KLASS_ES[r['p2k5']]} | {PARADOX_ES.get(r['paradox'], '—')} |")
    lines += ["", f"Sólo cambia la clase con perfusión peor y carga mayor: {_yes(s['only_perfusion_worse_higher_burden'])}; "
              f"ninguna clase deja de rechazar: {_yes(s['never_unrejects'])}. De las {len(s['transitions'])} "
              f"combinaciones de signos, {len(s['transitions']) - len(s['changed'])} conservan su clase; la tabla muestra "
              "sólo las que cambian o llevan marca. Ninguna marca de "
              "paradoja es alcanzable con 0,03 o 0,04: " + _yes(all(data["paradox_unreachable"].values())) + "."]
    return "\n".join(lines)


def render_reutilizacion(data: dict) -> str:
    e = data["equivalence"]
    lines = [f"{FROZEN} {data['design']['reuse_rule']}", "",
             f"- Archivos cerrados con sus bytes de P2K-4: {_yes(all(data['closed_unchanged'].values()))} "
             f"({len(data['closed_unchanged'])}); el digest de congelamiento de P2K-4 se recalcula igual: "
             f"{_yes(e['p2k4_freeze_digest'])}; registro de P2K-4 fijado: {_yes(e['record_pinned'])}.",
             "", "| demanda | SIMULATION, E y F nunca fallan | ganancia invariante por unidad | lecturas con perfusión peor "
             "| lecturas que rechazan | colapso R3 / R4 | recuento reproducido | observables y acidemia reproducidos | "
             "álgebra igual |", "|---|---|---|---|---|---|---|---|---|"]
    for key, c in e["certificates"].items():
        d = data["demands"][key]
        r = d["reproduced"]
        lines.append(f"| {_demand(key)} | {_yes(all(c['certified_full'].values()))} | {_yes(c['gain_invariant'])} | "
                     f"{_int(c['perfusion_worse_readings'])} de {_int(c['readings'])} | {_int(c['rejecting_readings'])} | "
                     f"{_yes(c['r3r4_bug'])} | {_yes(r['tally'])} | {_yes(r['observables'] and r['extreme_acidemia'])} | "
                     f"{_yes(d['algebra_equal'])} |")
    lines += ["", f"**Alcance de la recomputación (texto congelado).** {data['design']['reach_rule']}"]
    return "\n".join(lines)


def render_poda(data: dict) -> str:
    lines = ["| demanda | entran (supervivientes de P2K-4) | rechazados por monotonía | rechazados por la semántica "
             "corregida | supervivientes P2K-5 | por tono | unidades con supervivientes | combinaciones latentes |",
             "|---|---|---|---|---|---|---|---|"]
    for key, d in data["demands"].items():
        tones = ", ".join(f"g {_demand(g)} {_int(v['survivors'])} de {_int(v['entering'])}"
                          for g, v in d["by_tone_gain"].items())
        lines.append(f"| {_demand(key)} | {_int(d['entering'])} | {_int(d['rejected_by_monotonicity'])} | "
                     f"{_int(d['failed_by_semantic_correction'])} | **{_int(d['survivors'])}** | {tones} | "
                     f"{_int(d['upstream_units_with_survivors'])} de {_int(d['upstream_units'])} | "
                     f"{_int(d['latent_combinations'])} |")
    cross = data["cross_demand"]
    lines += ["", "**Entre demandas** (1 620 combinaciones): " + "; ".join(
        f"{CROSS_ES[k]} {_int(cross[k]['count'])}" for k in CROSS_ES) + "."]
    return "\n".join(lines)


def render_latentes(data: dict) -> str:
    keys = list(data["demands"])
    lines = ["| parámetro | " + " | ".join(f"demanda {_demand(k)}" for k in keys) + " | soporte (combinaciones por valor) |",
             "|---|" + "---|" * len(keys) + "---|"]
    first = data["demands"][keys[0]]["latent_support"]
    for dim in first:
        counts = dict(sorted(first[dim]["latent_combinations_by_value"].items(), key=lambda item: float(item[0])))
        support = ", ".join(f"{_n(float(v), 2 if dim == 'ventilation_gain' else 2 if dim == 'drive_gain' else 1)}: "
                            f"{_int(n)}" for v, n in counts.items())
        lines.append(f"| {DIM_ES[dim]} | " + " | ".join(
            SUPPORT_CLASS_ES[data["demands"][k]["latent_support"][dim]["class"]] for k in keys) + f" | {support} |")
    return "\n".join(lines)


def render_observables(data: dict) -> str:
    keys = list(data["demands"])
    lines = ["| observable | " + " | ".join(f"{CASE_ES[c]} · {_demand(k)}" for c in CASES for k in keys) + " |",
             "|---|" + "---|" * (len(CASES) * len(keys))]
    for name, label, digits in OBS_ES:
        cells = [_s(data["demands"][k]["observed"]["observables"].get(f"{name} {c}"), digits) for c in CASES for k in keys]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines += ["", "Envolventes A–I y ventanas de llegada sobre estos observables: " + "; ".join(
        f"demanda {_demand(k)}: A–I {_yes(d['envelopes']['envelopes_hold'])}, llegada "
        f"{_yes(d['envelopes']['arrival_compatible'])}" for k, d in data["demands"].items()) + "."]
    return "\n".join(lines)


def render_acidemia(data: dict) -> str:
    lines = ["| demanda | supervivientes | con pH < 7,00 sin tratamiento | 57m | 72f | pH mínimo | caso, minuto | carga | "
             "déficit efectivo | PaCO2 | FR | marca |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, d in data["demands"].items():
        x = d["observed"]["extreme_acidemia"]
        low = x["lowest"]
        lines.append(f"| {_demand(key)} | {_int(x['survivors'])} | {_int(x['flagged'])} | "
                     f"{_int(x['by_case']['gi_bleed_57m'])} | {_int(x['by_case']['gi_bleed_72f'])} | {_n(low['ph'], 3)} | "
                     f"{CASE_ES[low['case']]}, {low['minute']} | {_n(low['burden'], 2)} | {_n(low['deficit'], 3)} | "
                     f"{_n(low['paco2'], 1)} | {_s(low['rr'], 1)} | {low['flag'] or 'ninguna'} |")
    lines += ["", "Ninguna fila se filtra: las marcadas siguen en la región y pasan a CONSCIOUSNESS_COLLAPSE_REVIEW."]
    return "\n".join(lines)


def render_r3r4(data: dict) -> str:
    lines = [f"{FROZEN} {data['design']['r3r4_rule']}", ""]
    for key, r in data["r3r4"].items():
        lines.append(f"- Demanda {_demand(key)}: {R3R4_ES[r['status']]}; clases de P2K-4 (cota): " + ", ".join(
            f"{R3R4_ES[k]} {_int(v)}" for k, v in r["p2k4_classes"].items()) + f"; colapso: {_yes(r['bug'])}.")
    return "\n".join(lines)


def render_no_regresion(data: dict) -> str:
    u = data["region_unchanged"]
    lines = ["| dominio | sin cambio | evidencia |", "|---|---|---|"]
    for name, row in data["non_regression"].items():
        lines.append(f"| {DOMAINS_ES[name]} | {_yes(row['unchanged'])} | archivos cerrados con los bytes de P2K-4; "
                     "región de P2J-3 reproducida; validación de comparadores de P2K-4 sobre los mismos bytes |")
    lines += ["", "Región de P2J-3 recalculada y comparada con su registro: " + ", ".join(
        f"{REGION_ES[k]} {_yes(v)}" for k, v in u.items()) + "."]
    return "\n".join(lines)


def render_inventario_n(data: dict) -> str:
    lines = ["| señal | dónde está hoy | estado |", "|---|---|---|"]
    for row in data["n_inventory"]["signals"]:
        signal, source, status = N_ES[row["signal"]]
        lines.append(f"| {signal} | {source} | {status} |")
    lines += ["", "Sólo inventario: sin calibración de conciencia, sin reglas y sin escritor de N; hoy nada llega a N. El "
              "próximo encargo decide cuáles de estas señales podrán llegar."]
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    v, r = data["verdict"], data["recommendation"]
    lines = [f"**Veredicto:** `{v['verdict']}`.", "", "| criterio | cumple |", "|---|---|"]
    for name in data["design"]["criteria"]:
        lines.append(f"| {CRITERIA_ES.get(name, name)} | {_yes(v['checks'].get(name))} |")
    lines += ["", f"**Recomendación:** `{r['recommendation']}`" + (
        " → conciencia / respuesta neurológica N (no iniciada)." if "next" in r else ".")]
    for key in r.get("forwarded", {}):
        lines.append(f"- {FORWARDED_ES[key]}")
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    n = e["not_rerun"]
    return "\n".join([
        f"- Región P2J-3 reconstruida (necesaria para las trayectorias): {_int(e['p2j3_blood_runs'])} corridas de sangre y "
        f"{_int(e['p2j3_counterfactual_runs'])} contrafactuales.",
        f"- Trayectorias alcanzadas (R1 y R4) reconstruidas: {_int(e['reached_trajectories'])}; no reconstruidas: "
        f"{_int(e['trajectories_not_rebuilt'])} (cristaloide, GR, contrafactuales y sin GR, certificadas por P2K-4).",
        f"- Candidatos recontados como bitsets con el código congelado de P2K-4: {_int(e['candidates_retallied'])} en "
        f"{_int(e['upstream_units'])} unidades; rechazados analíticamente por la ganancia: {_int(e['analytic_rejections'])}.",
        f"- No repetido: {_int(n['no_prbc_runs'])} corridas sin GR, {_int(n['r3r4_state_runs'])} estados R3 / R4, "
        f"{_int(n['comparator_core_runs'])} corridas de comparadores, {_int(n['p2k3_validation_runs'])} de validación "
        f"P2K-3 y {_int(n['direct_check_candidates'])} candidatos de la verificación directa.",
        f"- Barrido cartesiano: {_yes(e['cartesian_sweep'])}; lectura del motor heredado: {_yes(e['legacy_read'])}."])


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the P2K-5 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
