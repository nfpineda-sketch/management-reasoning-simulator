"""P2I-2AB report: the generated blocks of docs/revision/P2I2AB_RECONSTRUCCION_LACTATO.md.

    python -m clinical_core.lactate_rebuild_report --write <document> --data <the lactate-rebuild JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .blood_filter_report import _n, _value
from .blood_fluid_readiness_report import _point

MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->")
           for name in ("preparacion", "origen", "factorizacion", "filtro", "region", "identificabilidad",
                        "representativos", "legado", "veredicto")}
CASES = ("gi_bleed_57m", "gi_bleed_72f")
CASE_ES = {"gi_bleed_57m": "57m", "gi_bleed_72f": "72f"}
LEVEL_ES = {"lower": "inferior", "midpoint": "medio", "upper": "superior"}
STATUS_ES = {"PASS": "PASS", "FAIL": "FAIL", "NOT_EVALUABLE": "NOT_EVALUABLE", "NOT_APPLICABLE": "NOT_APPLICABLE",
             "ALREADY_NORMALIZED": "ALREADY_NORMALIZED"}
STAGE_ES = {"L1": "L1 (sin tratamiento)", "L3": "L3 (sangre + hemostasia)", "L2": "L2 (cristaloide con sangrado)"}
CLASS_ES = {"WELL_CONSTRAINED": "bien acotado", "PARTIALLY_CONSTRAINED": "parcialmente acotado",
            "POORLY_IDENTIFIED": "mal identificado", "NON_IDENTIFIABLE_SEPARATELY": "no identificable por separado",
            "NOT_VARIED": "no varía"}
EDGE_ES = {"INTERIOR": "interior", "OPEN_LOWER_GRID_EDGE": "abierto abajo", "OPEN_UPPER_GRID_EDGE": "abierto arriba",
           "OPEN_BOTH_GRID_EDGES": "abierto en ambos bordes", None: "—"}
DIMENSIONS_ES = {
    "bleed_ml_per_min": "tasa de sangrado (mL-eq/min)", "arrival_circulating_volume_ml": "B0 (mL)",
    "preload_scale_over_kappa_ml": "λ/κ (mL)", "plasma_refill_target_share": "meta del relleno",
    "plasma_refill_tau_min": "τ del relleno (min)", "plasma_refill_capacity_ml": "capacidad del relleno (mL)",
    "red_cell_unit_hb_g_dl": "Hb de la unidad (g/dL)", "red_cell_unit_volume_ml": "volumen de la unidad (mL)",
    "preload_fraction|gi_bleed_57m": "posición 57m", "preload_fraction|gi_bleed_72f": "posición 72f",
    "reserve": "reserva de extracción ρ", "crystalloid_point": "punto del cristaloide", "crystalloid_F0": "F0",
    "crystalloid_Finf": "Finf", "crystalloid_tau": "τ del cristaloide (min)",
    "debt_clearance_tau_min": "τ_D (min)", "debt_per_delivery_deficit": "ganancia déficit→D (g)",
    "lactate_per_output_deficit": "ganancia D→lactato (G)", "lactate_clearance_tau_min": "τ del lactato (min)",
    "arrival_lactate_excess": "exceso de lactato de llegada", "arrival_pair": "par (deuda, entrega) de llegada",
    "arrival_oxygen_debt": "deuda de llegada", "arrival_delivery_ratio": "entrega de llegada", "G x g": "G × g"}
FLAGS_ES = {"WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL": "déficit crítico que empeora con caída grande del lactato",
            "ADEQUATE_WITH_DELAYED_CLEARANCE": "adecuado con aclaramiento demorado",
            "PERSISTENT_HIGH_D": "D alta persistente (L3)", "INSTANT_NORMALIZATION": "normalización instantánea",
            "INCOMPATIBLE_WITH_SURVIVAL": "valores incompatibles con la supervivencia (marcadores propuestos)"}
INTERVAL_ES = {"ADEQUATE": "A", "RECOVERING_CRITICAL": "R", "PERSISTENT_OR_WORSENING_CRITICAL": "P"}
OXYGEN_ES = {"ADEQUATE": "ADEQUATE", "COMPENSATED": "COMPENSATED", "CRITICAL": "CRITICAL"}


def _int(value) -> str:
    return f"{value:,}".replace(",", " ")


def _share(part, whole) -> str:
    return "—" if not whole else _n(100 * part / whole, 1) + " %"


def _level(value) -> str:
    if isinstance(value, str) and "|" in value:
        debt, delivery = value.split("|")
        return f"deuda {LEVEL_ES[debt]} · entrega {LEVEL_ES[delivery]}"
    return LEVEL_ES.get(value, _value(value))


def _sci(value: float) -> str:
    return f"{value:.1e}".replace(".", ",")


def _part(name: str) -> str:
    """A certified part's name without the table-breaking bar: refill target and tau spelled out."""
    if name.startswith("P2I-2Y "):
        target, tau = name.split(" ", 1)[1].split("|")
        return f"P2I-2Y, meta {_value(target)} y τ {_value(tau)}"
    return (name.replace("plasma_refill_target_share=", "meta ").replace("plasma_refill_tau_min=", "τ ")
            .replace(" & ", " y "))


def _cell(cell: str) -> str:
    refill, positions = cell.split(" @ ")
    target, tau = refill.split("|")
    return (f"meta {_value(target)} y τ {_value(tau)}, posiciones "
            + " / ".join(_value(p) for p in positions.split(" / ")))


def render_preparacion(data: dict) -> str:
    ready = data["readiness"]
    lines = [f"Congelamiento: `{data['freeze_digest']}` (una prueba lo fija). Registro de partida: P2I-2AA "
             f"`{data['records']['P2I-2AA']}`.\n",
             "| Elemento | Valor |", "|---|---|",
             f"| Veredicto previo (P2I-2AA) | {ready['previous']} |",
             f"| Bloqueo previo | {', '.join(ready['previous_blockers'])} |",
             f"| Borde de τ / identificabilidad práctica | {ready['tau']['boundary']} / "
             f"{ready['tau']['practical']} |",
             f"| Estado de τ | {ready['tau']['status']} |",
             f"| **Preparación** | **{ready['verdict']}** |", ""]
    lines += ["| Decisión docente | Texto registrado |", "|---|---|"]
    lines += [f"| {name} | {text} |" for name, text in data["faculty"].items()]
    return "\n".join(lines)


def render_origen(data: dict) -> str:
    parts = data["components"]
    source = data["source"]
    lines = ["| Componente | Contenido |", "|---|---|",
             f"| A. Sangre | {parts['A_blood']['P1_sets']} conjuntos P1 y {parts['A_blood']['P3_sets']} conjuntos P3 "
             f"(reserva colapsada); por tasa: " + "; ".join(
                 f"{_value(rate)}: {item['P1']} P1 / {item['P3']} P3"
                 for rate, item in parts["A_blood"]["by_rate"].items())
             + " |",
             "| B. Posiciones que entran | " + "; ".join(
                 f"tasa {_value(rate)}: " + ", ".join(f"{CASE_ES[c]} {' y '.join(_value(p) for p in v)}"
                                                      for c, v in item.items())
                 for rate, item in parts["B_positions"].items()) + " |",
             f"| C. Tasas | {', '.join(_value(r) for r in parts['C_rates'])} mL-eq/min |",
             f"| D. Cristaloide | {len(parts['D_crystalloid'])} puntos: "
             + "; ".join(_point(k) for k in parts["D_crystalloid"]) + " |",
             "| E. Glóbulos rojos | " + "; ".join(f"{DIMENSIONS_ES[n]} {', '.join(_value(v) for v in values)}"
                                               for n, values in parts["E_red_cells"].items()) + " |",
             f"| F. DO2 / extracción | ρ {', '.join(_value(r) for r in parts['F_oxygen']['reserves'])} (simulado en "
             f"{_value(parts['F_oxygen']['simulated_at'])}; ρ se cancela) |",
             "| G. Hemostasia | " + "; ".join(f"{CASE_ES[c]} minuto {m}" for c, m in parts["G_haemostasis"].items())
             + " (endoscopía del propio motor) |",
             "| H. L3 | " + "; ".join(f"{n} {_value(v[0])} ({' + '.join(v[1])})" for n, v in parts["H_l3"].items())
             + " |",
             f"| Lado del lactato | {parts['lactate_side']} puntos |",
             f"| **Candidatos** | **{_int(parts['candidates'])}** (con la multiplicidad de ρ: "
             f"{_int(parts['candidates_with_reserve_multiplicity'])}) |", ""]
    lines += ["| Tasa | Parte certificada | Certificado | Reproducido |", "|---|---|---|---|"]
    for rate, item in source["reproduction"].items():
        for name, row in item["parts"].items():
            lines.append(f"| {_value(rate)} | {_part(name)} | {_int(row['certified'])} | {_int(row['reproduced'])} |")
        lines.append(f"| {_value(rate)} | **total** | **{_int(item['total']['certified'])}** | "
                     f"**{_int(item['total']['reproduced'])}** |")
    lines.append("")
    beyond = {rate: item["beyond_certified_exploration"] for rate, item in source["reproduction"].items()
              if item["beyond_certified_exploration"]}
    lines.append("Fuera de lo explorado por los registros certificados (entra por la regla docente de precarga): "
                 + ("; ".join(f"tasa {_value(rate)}, {_cell(cell)}: {_int(n)}" for rate, item in beyond.items()
                              for cell, n in item.items()) or "nada") + ".\n")
    keys = data["source_keys"]
    lines.append(f"Claves de sangre del espacio: {keys['keys']}; fuera de las certificadas para el cristaloide: "
                 f"{len(keys['outside_certified'])}; exclusiones de la tasa 2,5: {len(keys['rate_2_5_exclusions'])}. "
                 f"Filas de sangre calculadas: {_int(data['rows_computed'])}; ilegibles: "
                 f"{sum(source['unreadable'].values())}; contradicciones: {len(data['contradictions'])}.")
    return "\n".join(lines)


def render_factorizacion(data: dict) -> str:
    validation, efficiency = data["validation"], data["efficiency"]
    lines = ["| Comprobación | Resultado |", "|---|---|",
             f"| Corridas completas del núcleo comparadas | {validation['runs']} |",
             f"| Coinciden todas | {'sí' if validation['agree'] else 'no'} |",
             f"| Exactas con ρ 2,5 (lactato, D, déficit, hemostasia, detención) | "
             f"{'sí' if validation['exact_at_reserve_2_5'] else 'no'} |",
             f"| Mayor diferencia con ρ 1 y 3 | {_sci(validation['max_gap_other_reserves'])} |",
             f"| Desacuerdos | {len(validation['disagreements'])} |",
             f"| Solo G × g y G × D0 llegan al lactato (diferencia con productos iguales) | "
             f"{_sci(data['structural_products']['same_products_gap'])} |", ""]
    lines += ["Estados FD-LAC que ejerció la muestra: " + "; ".join(
        f"{name.replace('True', 'pasa').replace('False', 'falla')} {n}"
        for name, n in validation["verdicts_seen"].items())
        + ".\n"]
    lines += ["| Eficiencia | Valor |", "|---|---|",
              "| Trayectorias hemodinámicas simuladas | " + "; ".join(
                  f"{s} {_int(n)}" for s, n in efficiency["haemodynamic_trajectories"].items())
              + f" (total {_int(efficiency['factorized_core_runs'])}) |",
              f"| Corridas del producto ingenuo (candidatos × 3 escenarios × 2 casos) | "
              f"{_int(efficiency['naive_core_runs'])} |",
              f"| Corridas completas de validación | {efficiency['validation_full_runs']} |",
              f"| Filas de sangre | {_int(efficiency['blood_rows'])} |"]
    return "\n".join(lines)


def render_filtro(data: dict) -> str:
    lines = ["| Etapa | Entran | Rechazados (SIMULATION_REJECTION) | ANALYTIC_REJECTION | Sobreviven | Unidades "
             "evaluadas / rechazadas |", "|---|---|---|---|---|---|"]
    for stage in data["filter"]["stages"]:
        lines.append(f"| {STAGE_ES[stage['scenario']]} | {_int(stage['entering'])} | {_int(stage['rejected'])} | "
                     f"{stage['ANALYTIC_REJECTION']} | {_int(stage['survivors'])} | {_int(stage['units_evaluated'])} / "
                     f"{_int(stage['units_rejected'])} |")
    lines.append("")
    lines += ["| Etapa | Restricción y caso | Primer fallo | Cualquier fallo |", "|---|---|---|---|"]
    for stage in data["filter"]["stages"]:
        for name, n in stage["any_failure"].items():
            label = name.replace("gi_bleed_57m", "57m").replace("gi_bleed_72f", "72f")
            lines.append(f"| {stage['scenario']} | {label} | {_int(stage['first_failure'].get(name, 0))} | {_int(n)} |")
    filtered = data["filter"]
    lines += ["", f"Candidatos: {_int(filtered['candidates'])}; sobrevivientes: **{_int(filtered['survivors'])}** "
                  f"({_share(filtered['survivors'], filtered['candidates'])}); con la multiplicidad de ρ: "
                  f"{_int(filtered['survivors_with_reserve_multiplicity'])}."]
    return "\n".join(lines)


def _summary(item) -> str:
    if not item:
        return "—"
    return (f"{_n(item['min'], 2)} · {_n(item['p05'], 2)} · {_n(item['median'], 2)} · {_n(item['p95'], 2)} · "
            f"{_n(item['max'], 2)}")


def render_region(data: dict) -> str:
    region, stats = data["region"], data["statistics"]
    survivors = region["candidates"]
    lines = [f"**{region['status']}**: {_int(region['units'])} unidades (P1 × lado del lactato), "
             f"{_int(survivors)} candidatos; resumen de la región `{region['digest']}`.\n",
             "| Lectura (mín · p5 · mediana · p95 · máx) | 57m | 72f |", "|---|---|---|"]
    for key, label in (("L60", "L60 sin tratamiento (mmol/L)"), ("L120", "L120 con L3 (mmol/L)"),
                       ("fd04_at_trigger", "L(T*) cuando hay T* (mmol/L)"),
                       ("fd04_reduction", "caída a T* + 30 (fracción), si FD-LAC-04 se evalúa"),
                       ("fd05_debt_memory_at_reference_debt", "memoria de una deuda de 60 a los 120′ (mmol/L)")):
        lines.append(f"| {label} | {_summary(stats[key]['gi_bleed_57m'])} | {_summary(stats[key]['gi_bleed_72f'])} |")
    lines += ["", "| Estado entre los sobrevivientes | 57m | 72f |", "|---|---|---|"]
    for key, label in (("fd01_status", "FD-LAC-01"), ("fd04_status", "FD-LAC-04"), ("fd05_status", "FD-LAC-05")):
        for status in ("PASS", "ALREADY_NORMALIZED", "NOT_APPLICABLE", "NOT_EVALUABLE"):
            counts = [stats[key][c].get(status, 0) for c in CASES]
            if any(counts):
                lines.append(f"| {label} {STATUS_ES[status]} | {_int(counts[0])} ({_share(counts[0], survivors)}) | "
                             f"{_int(counts[1])} ({_share(counts[1], survivors)}) |")
    lines += ["", "| Sensibilidad de FD-LAC-04 (no filtra) | Sobrevivientes que también pasarían |", "|---|---|"]
    for threshold, n in stats["fd04_sensitivity"]["thresholds"].items():
        label = "cualquier caída" if float(threshold) == 0 else f"caída ≥ {_n(100 * float(threshold), 0)} %"
        lines.append(f"| {label} | {_int(n)} ({_share(n, survivors)}) |")
    recovering = stats["recovering_declines_allowed"]["survivors_with_one"]
    lines += ["", "| Lectura informativa (no filtra) | Sobrevivientes |", "|---|---|",
              "| con una caída sostenida aceptada como RECOVERING_CRITICAL | " + "; ".join(
                  f"{s} {_int(n)}" for s, n in recovering.items()) + " |",
              f"| con adecuación sólo por compensación en [T*, T* + 30] | "
              f"{_int(stats['adequacy_by_compensation_after_trigger'])} |",
              f"| con caída sostenida y déficit crítico persistente después de la hemostasia (L3) | "
              f"{_int(stats['persistent_critical_decline_after_haemostasis']['survivors'])} "
              f"({_share(stats['persistent_critical_decline_after_haemostasis']['survivors'], survivors)}) |",
              "| T* en L3 | " + "; ".join(f"{CASE_ES[c]}: " + ", ".join(
                  f"{'sin T*' if m == 'None' else 'minuto ' + m} {_int(n)}"
                  for m, n in stats['trigger_minute'][c].items())
                  for c in CASES) + " |"]
    return "\n".join(lines)


def render_identificabilidad(data: dict) -> str:
    dimensions = data["identifiability"]["dimensions"]
    lines = ["| Dimensión | Explorado | Sobrevive (candidatos) | Clase | Borde |", "|---|---|---|---|---|"]
    for name, item in dimensions.items():
        if name == "crystalloid_point":
            explored = f"{len(item['explored'])} puntos"
        else:
            explored = ", ".join(_level(v) for v in item["explored"])
        surviving = ", ".join(f"{_level(v)} {_int(item['surviving_weight'].get(v, 0))}" for v in item["explored"]
                              if name != "crystalloid_point")
        if name == "crystalloid_point":
            weights = sorted(item["surviving_weight"].values())
            surviving = f"los 12 sobreviven ({_int(weights[0])} a {_int(weights[-1])} cada uno)" if weights else "—"
        lines.append(f"| {DIMENSIONS_ES.get(name, name)} | {explored} | {surviving} | "
                     f"{CLASS_ES.get(item['status'], item['status'])} | {EDGE_ES.get(item['edge'], item['edge'])} |")
    return "\n".join(lines)


def render_representativos(data: dict) -> str:
    lines = []
    for tag in ("LOW", "MID", "HIGH"):
        item = data["representatives"].get(tag)
        if not item:
            continue
        lam, blood = item["lambda"], item["blood"]
        lines.append(f"**{tag}** (rango {_int(item['pick']['rank'])}): τ_D {_value(lam['debt_clearance_tau_min'])}, "
                     f"g {_value(lam['debt_per_delivery_deficit'])}, G {_value(lam['lactate_per_output_deficit'])}, "
                     f"τ_L {_value(lam['lactate_clearance_tau_min'])}, "
                     f"exceso {_level(lam['arrival_lactate_excess'])}, "
                     f"deuda {_level(lam['arrival_oxygen_debt'])}, entrega {_level(lam['arrival_delivery_ratio'])}; "
                     f"tasa {_value(blood['rate'])}, B0 {_value(blood['arrival_circulating_volume_ml'])}, "
                     f"λ/κ {_value(blood['preload_scale_over_kappa_ml'])}, relleno "
                     f"{_value(blood['plasma_refill_target_share'])} / {_value(blood['plasma_refill_tau_min'])} / "
                     f"{_value(blood['plasma_refill_capacity_ml'])}, "
                     f"unidad {_value(blood['red_cell_unit_hb_g_dl'])} g/dL "
                     f"× {_value(blood['red_cell_unit_volume_ml'])} mL, posiciones "
                     f"{_value(blood['positions']['gi_bleed_57m'])} / {_value(blood['positions']['gi_bleed_72f'])}; "
                     f"cristaloide {_point(item['crystalloid'])}.\n")
        lines += ["| Caso · escenario | min | Δ volumen circulante (mL-eq) | Perdido (mL) | Hb (g/dL) | "
                  "Gasto relativo | DO2 (índice) | Estado | Déficit | D | Lactato (mmol/L) |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        for key, run in item["runs"].items():
            case, scenario = key.split("|")
            for row in run["rows"]:
                lines.append(f"| {CASE_ES[case]} {scenario} | {row['minute']} | {_n(row['circulating_ml'], 0)} | "
                             f"{_n(row['shed_ml'], 0)} | {_n(row['hb'], 2)} | {_n(row['output_rel'], 3)} | "
                             f"{_n(row['do2'], 3)} | {OXYGEN_ES[row['state']]} | {_n(row['effective_deficit'], 3)} | "
                             f"{_n(row['D'], 1)} | {_n(row['lactate'], 2)} |")
        lines.append("")
        lines += ["| Caso · escenario | Intervalos de 15′ con sangrado (A / R / P) | Marcas |", "|---|---|---|"]
        for key, run in item["runs"].items():
            case, scenario = key.split("|")
            intervals = " ".join(INTERVAL_ES[label] for _, _, label in run["intervals"])
            flags = "; ".join(FLAGS_ES[name] for name, on in run["flags"].items() if on) or "ninguna"
            lines.append(f"| {CASE_ES[case]} {scenario} | {intervals or '—'} | {flags} |")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_legado(data: dict) -> str:
    legacy = data["legacy_reference"]
    times = list(next(iter(legacy["legacy"]["gi_bleed_57m"].values())))
    order = sorted(times, key=int)
    lines = [f"{legacy['rule']}\n", "| Caso · escenario | " + " | ".join(f"{t}′" for t in order) + " |",
             "|---|" + "---|" * len(order)]
    for case in CASES:
        for scenario, values in legacy["legacy"][case].items():
            lines.append(f"| {CASE_ES[case]} {scenario} | " + " | ".join(_n(values[t], 1) for t in order) + " |")
    lines += ["", "| Representativo · caso · escenario | núcleo / legado a los 0′, 60′ y 120′ |", "|---|---|"]
    for tag, runs in legacy["beside_representatives"].items():
        for key, values in runs.items():
            case, scenario = key.split("|")
            lines.append(f"| {tag} {CASE_ES[case]} {scenario} | " + "; ".join(
                f"{t}′ {_n(values[t]['core'], 2)} / {_n(values[t]['legacy'], 1)}" for t in ("0", "60", "120")) + " |")
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    verdict = data["verdict"]
    names = {"readiness": "preparación", "source": "fuente de sangre reproducida", "keys": "claves certificadas",
             "factorization": "factorización exacta", "survivors": "hay sobrevivientes",
             "definitive_management_evaluated": "FD-LAC-04/05 evaluadas en ambos casos en algún sobreviviente"}
    lines = [f"**{verdict['verdict']}**\n", "| Comprobación | Resultado |", "|---|---|"]
    lines += [f"| {names.get(name, name)} | {'sí' if passed else 'no'} |"
              for name, passed in verdict["checks"].items()]
    lines += ["", f"Regla congelada: {verdict['rule']}", "", f"Próximo dominio: {verdict['next_domain']}"]
    return "\n".join(lines)


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


RENDERERS = {"preparacion": render_preparacion, "origen": render_origen, "factorizacion": render_factorizacion,
             "filtro": render_filtro, "region": render_region, "identificabilidad": render_identificabilidad,
             "representativos": render_representativos, "legado": render_legado, "veredicto": render_veredicto}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the lactate-rebuild JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
