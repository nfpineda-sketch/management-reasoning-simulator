"""P2I-2AD report: the generated blocks of docs/revision/P2I2AD_CIERRE_DEUDA_LACTATO.md.

    python -m clinical_core.lactate_closure_report --write <document> --data <the lactate-closure JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import lactate_closure as lc
from .blood_filter_report import _n, _value
from .blood_fluid_readiness_report import _point
from .lactate_adequacy_report import INTERVAL_ES, _case
from .lactate_rebuild_report import (CASE_ES, CASES, CLASS_ES, DIMENSIONS_ES, EDGE_ES, FLAGS_ES, STAGE_ES, STATUS_ES,
                                     _int, _level, _sci, _share, _summary)

MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->")
           for name in ("decisiones", "deuda", "ganancia", "filtro", "demanda", "region", "identificabilidad",
                        "representativos", "legado", "veredicto")}
FACULTY_ES = {"decided": "fecha", "l3_adequacy": "adecuación L3 hasta 120", "debt_repayment": "devolución de D",
              "lactate_coupling": "acople D → lactato", "hr_rr": "FC / FR", "demand": "demanda metabólica",
              "rho": "ρ", "fd_lac": "FD-LAC-01..06"}
CHECKS_ES = {"debt_semantics": "semántica temporal de D coherente",
             "factorization": "factorización exacta",
             "lactate_coupling": "la producción de lactato ya no lee τ_D",
             "survivors": "hay sobrevivientes con demanda 1,0",
             "l3_adequate_through_120": "todo sobreviviente mantiene la adecuación L3 hasta 120",
             "definitive_management_evaluable": "FD-LAC-04/05 evaluadas en ambos casos para todo sobreviviente",
             "demand_characterized": "capa de demanda clasificó todos los candidatos",
             "patient_like": "representativos verosímiles",
             "semantic_consistency": "T* de FD-LAC-04 = inicio de la adecuación L3"}
SEMANTICS_ES = {"debt_per_delivery_deficit": "g (déficit → D)", "debt_clearance_tau_min": "τ_D",
                "debt_to_lactate_gain": "k (D → lactato)", "lactate_clearance_tau_min": "τ_L",
                "arrival_oxygen_debt": "D de llegada (D0)", "arrival_lactate_excess": "exceso de lactato de llegada (X0)"}
DIMS = {**DIMENSIONS_ES, "debt_to_lactate_gain": "ganancia D→lactato (k)", "k x g": "k × g", "k x D0": "k × D0",
        "demand_factor": "demanda (×)"}


def _k(value: float) -> str:
    return f"{value:.3g}".replace(".", ",")


def render_decisiones(data: dict) -> str:
    lines = [f"Congelamiento: `{data['freeze_digest']}` (una prueba lo fija). Registros de partida: P2I-2AB "
             f"`{data['records']['P2I-2AB']}` y P2I-2AC `{data['records']['P2I-2AC']}`.\n",
             "| Decisión docente | Texto registrado |", "|---|---|"]
    lines += [f"| {FACULTY_ES.get(name, name)} | {text} |" for name, text in data["faculty"].items()]
    source, hr = data["source"], data["hr_rr"]
    lines += ["", f"Espacio fuente reutilizado de P2I-2AB: {source['p1_sets']} conjuntos P1, {source['p3_sets']} "
                  f"conjuntos P3, {source['crystalloid_points']} puntos del cristaloide y {source['lactate_side']} "
                  f"puntos del lado del lactato. FC / FR: {' · '.join(hr['status'])}; calibradas: "
                  f"{'sí' if hr['calibrated'] else 'no'}; el rechazo HR1 histórico es objetivo: "
                  f"{'sí' if hr['historical_hr1_target'] else 'no'}."]
    return "\n".join(lines)


def render_deuda(data: dict) -> str:
    validation, crossing, coupling = data["validation"], data["crossing"], data["coupling"]
    lines = ["| Comprobación | Resultado |", "|---|---|",
             f"| Corridas completas del núcleo corregido comparadas | {validation['runs']} |",
             f"| Coinciden todas (lactato, D, déficit, flujo, eventos y veredictos) | "
             f"{'sí' if validation['agree'] else 'no'} |",
             f"| Exactas con ρ 2,5 (demanda {', '.join(_value(d) for d in validation['demands'])}) | "
             f"{'sí' if validation['exact_at_reserve_2_5'] else 'no'} |",
             f"| ρ comparadas | {', '.join(_value(r) for r in validation['reserves'])} (1 sólo como referencia "
             f"sintética) |",
             f"| Mayor diferencia fuera de ρ 2,5 | {_sci(validation['max_gap_other_reserves'])} |",
             f"| D baja sólo en minutos sin déficit al inicio ni al final | "
             f"{'sí' if validation['debt_coherent'] else 'no'} |",
             f"| Desacuerdos | {len(validation['disagreements'])} |",
             f"| El paso de lactato lee k y no τ_D ni G | {'sí' if coupling['independent'] else 'no'} |", "",
             "| Región de P2I-2AC (candidatos) | Con la D de P2I-2AC | Con la D de P2I-2AD |", "|---|---|---|",
             f"| con dos o más minutos críticos bajo su D de llegada | {_int(crossing['affected_old'])} | "
             f"{_int(crossing['affected_new'])} |",
             f"| · con entrega de llegada superior ({_int(crossing['upper_delivery'])} de {_int(crossing['region'])}) | "
             f"{_int(crossing['upper_affected_old'])} | {_int(crossing['upper_affected_new'])} |",
             f"| máximo de minutos críticos bajo la D de llegada | {crossing['max_minutes_old']} | "
             f"{crossing['max_minutes_new']} |"]
    efficiency = data["efficiency"]
    lines += ["", "| Eficiencia | Valor |", "|---|---|",
              f"| Trayectorias hemodinámicas simuladas (compartidas por las tres demandas) | "
              f"{_int(efficiency['haemodynamic_trajectories'])} |",
              f"| Corridas del producto ingenuo (candidatos × 3 escenarios × 2 casos × 3 demandas) | "
              f"{_int(efficiency['naive_core_runs'])} |",
              f"| Corridas completas de validación / de representativos | {efficiency['validation_full_runs']} / "
              f"{efficiency['representative_full_runs']} |",
              "| Unidades posprocesadas (unidad × lado del lactato) | " + "; ".join(
                  f"×{_value(f)}: " + ", ".join(f"{s} {_int(n)}" for s, n in item.items())
                  for f, item in efficiency["post_processed_units"].items()) + " |",
              f"| Filas de sangre reutilizadas de P2I-2AB (no recalculadas) | "
              f"{_int(efficiency['blood_rows_reused_from_p2i2ab'])} |",
              f"| Rechazos analíticos | {efficiency['analytic_rejections']} |"]
    return "\n".join(lines)


def render_ganancia(data: dict) -> str:
    k = data["k_ld"]
    lines = [f"Rango anterior: **{k['old_status']}**. {k['old_reason']}\n",
             "| Elemento | Valor |", "|---|---|",
             f"| Unidades | {k['units']} |",
             f"| Horizonte de FD-LAC-02/03 | {k['horizon_min']} min |",
             f"| Resolución de las envolventes docentes | {_value(k['envelope_resolution'])} mmol/L |",
             f"| Mayor amplitud de la envolvente a 60 min sin tratamiento | {_value(k['widest_untreated_span'])} "
             f"mmol/L |",
             f"| Niveles de D de llegada declarados (medio / superior) | {_value(k['debt_levels']['midpoint'])} / "
             f"{_value(k['debt_levels']['upper'])} |",
             f"| Extremo bajo = resolución / (horizonte × D superior) | {_k(k['low'])} |",
             f"| Extremo alto = amplitud / (horizonte × D medio) | {_k(k['high'])} |",
             f"| Puntos (razón constante {_k(k['ratio'])}) | {', '.join(_k(p) for p in k['points'])} |",
             f"| Valor por defecto del núcleo (provisional, no elegido) | {_k(k['default'])} |",
             f"| Constantes que inducía la rejilla anterior (sólo comparación) | "
             f"{', '.join(_k(p) for p in k['old_induced_constants_for_comparison_only'])} |", "",
             "| Parámetro | Papel | Dónde actúa | Cómo llega al lactato |", "|---|---|---|---|"]
    semantics = data["parameter_semantics"]
    lines += [f"| {SEMANTICS_ES[name]} | {semantics[name]['role']} | {semantics[name]['acts']} | "
              f"{semantics[name]['reaches_lactate']} |" for name in lc.PARAMETER_SEMANTICS]
    return "\n".join(lines)


def _stage_tables(filtered: dict) -> list:
    lines = ["| Etapa | Entran | Rechazados (SIMULATION_REJECTION) | ANALYTIC_REJECTION | Sobreviven | Unidades "
             "evaluadas / rechazadas |", "|---|---|---|---|---|---|"]
    for stage in filtered["stages"]:
        lines.append(f"| {STAGE_ES[stage['scenario']]} | {_int(stage['entering'])} | {_int(stage['rejected'])} | "
                     f"{stage['ANALYTIC_REJECTION']} | {_int(stage['survivors'])} | {_int(stage['units_evaluated'])} / "
                     f"{_int(stage['units_rejected'])} |")
    lines += ["", "| Etapa | Restricción y caso | Primer fallo | Cualquier fallo |", "|---|---|---|---|"]
    for stage in filtered["stages"]:
        for bit in range(len(lc.BITS[stage["scenario"]])):
            name = lc._label(stage["scenario"], bit)
            if name in stage["any_failure"]:
                lines.append(f"| {stage['scenario']} | {_case(name)} | {_int(stage['first_failure'].get(name, 0))} | "
                             f"{_int(stage['any_failure'][name])} |")
    lines += ["", "| Etapa | Única restricción que rechaza | Candidatos |", "|---|---|---|"]
    for stage in filtered["stages"]:
        for name in dict.fromkeys(name for name, _ in lc.BITS[stage["scenario"]]):
            if name in stage["only_failure"]:
                lines.append(f"| {stage['scenario']} | {name} | {_int(stage['only_failure'][name])} |")
    return lines


def render_filtro(data: dict) -> str:
    primary = data["filter"]["1"]
    lines = [f"Demanda 1,0 (la región). Candidatos: {_int(primary['candidates'])}; sobrevivientes: "
             f"**{_int(primary['survivors'])}** ({_share(primary['survivors'], primary['candidates'])}).\n"]
    lines += _stage_tables(primary)
    return "\n".join(lines)


def render_demanda(data: dict) -> str:
    demand = data["demand"]
    lines = [f"{demand['rule']}\n", "| Demanda | Sobrevivientes |", "|---|---|"]
    lines += [f"| ×{_value(f)} | {_int(n)} |" for f, n in demand["survivors"].items()]
    lines += ["", "| Clase | Candidatos |", "|---|---|"]
    lines += [f"| {name} | {_int(demand['classes'][name])} |" for name in (lc.ROBUST, lc.SENSITIVE, lc.INCOMPATIBLE)]
    lines += ["", "| Sobrevive con demanda | Candidatos |", "|---|---|"]
    lines += [f"| {' y '.join(_value(f) for f in key.split('+'))} | {_int(n)} |" for key, n in demand["patterns"].items()]
    final = demand["final_region"]
    lines += ["", f"En la región (demanda 1,0): {lc.ROBUST} {_int(final[lc.ROBUST])}, {lc.SENSITIVE} "
                  f"{_int(final[lc.SENSITIVE])}."]
    for factor in ("0.9", "1.1"):
        lines += ["", f"Filtro con demanda ×{_value(factor)} (sólo informa):", ""] + _stage_tables(data["filter"][factor])
    return "\n".join(lines)


def render_region(data: dict) -> str:
    region, stats = data["region"], data["statistics"]
    survivors = region["candidates"]
    lines = [f"**{region['status']}**: {_int(region['units'])} unidades (P1 × lado del lactato), {_int(survivors)} "
             f"candidatos; resumen de la región `{region['digest']}`.\n"]
    if not stats:
        return "\n".join(lines)
    lines += ["| Lectura (mín · p5 · mediana · p95 · máx) | 57m | 72f |", "|---|---|---|"]
    for key, label in (("L60", "L60 sin tratamiento (mmol/L)"), ("L120", "L120 con L3 (mmol/L)"),
                       ("D120", "D a los 120′ con L3"), ("fd04_at_trigger", "L(T*) (mmol/L)"),
                       ("fd04_reduction", "caída a T* + 30 (fracción)")):
        lines.append(f"| {label} | {_summary(stats[key]['gi_bleed_57m'])} | {_summary(stats[key]['gi_bleed_72f'])} |")
    lines += ["", "| Estado entre los sobrevivientes | 57m | 72f |", "|---|---|---|"]
    for key, label in (("adequacy", "L3"), ("fd01_status", "FD-LAC-01"), ("fd04_status", "FD-LAC-04"),
                       ("fd05_status", "FD-LAC-05")):
        statuses = sorted(set(stats[key][CASES[0]]) | set(stats[key][CASES[1]]))
        for status in statuses:
            counts = [stats[key][c].get(status, 0) for c in CASES]
            lines.append(f"| {label} {STATUS_ES.get(status, status)} | {_int(counts[0])} "
                         f"({_share(counts[0], survivors)}) | {_int(counts[1])} ({_share(counts[1], survivors)}) |")
    lines += [f"| FD-LAC-04 y 05 evaluadas en ambos casos | {_int(stats['fd04_and_05_evaluated_in_both_cases'])} "
              f"({_share(stats['fd04_and_05_evaluated_in_both_cases'], survivors)}) | |",
              f"| T* de FD-LAC-04 = inicio de la adecuación L3 (ambos casos) | "
              f"{_int(stats['trigger_is_adequacy_onset'])} | |",
              f"| D baja fuera de minutos sin déficit (L3) | {_int(stats['debt_incoherent_l3'])} | |"]
    lines += ["", "| Sensibilidad de FD-LAC-04 (diagnóstico, no filtra) | Sobrevivientes que también pasarían |",
              "|---|---|"]
    for threshold, n in stats["fd04_sensitivity"]["thresholds"].items():
        label = "cualquier caída" if float(threshold) == 0 else f"caída ≥ {_n(100 * float(threshold), 0)} %"
        lines.append(f"| {label} | {_int(n)} ({_share(n, survivors)}) |")
    lines += ["", "| T* de FD-LAC-04 | " + "; ".join(f"{CASE_ES[c]}: " + ", ".join(
        f"{'ninguno' if m == 'None' else 'minuto ' + m} {_int(n)}"
        for m, n in sorted(stats["trigger_minute"][c].items(), key=lambda kv: (kv[0] == "None",
                                                                                int(kv[0]) if kv[0] != "None" else 0)))
        for c in CASES) + " |"]
    return "\n".join(lines)


def render_identificabilidad(data: dict) -> str:
    identifiability = data["identifiability"]
    lines = ["| Dimensión | Explorado | Sobrevive (candidatos) | Clase | Borde | P2I-2AC | Cambio |",
             "|---|---|---|---|---|---|---|"]
    for name, item in identifiability["dimensions"].items():
        if name == "crystalloid_point":
            explored = f"{len(item['explored'])} puntos"
            weights = sorted(item["surviving_weight"].values())
            surviving = f"{len(item['surviving'])} sobreviven" + (
                f" ({_int(weights[0])} a {_int(weights[-1])} cada uno)" if weights else "")
        elif name in ("debt_to_lactate_gain", "k x g", "k x D0"):
            explored = f"{len(item['explored'])} valores, {_k(float(item['explored'][0]))} a " \
                       f"{_k(float(item['explored'][-1]))}"
            surviving = f"{len(item['surviving'])} sobreviven" + (
                f", {_k(float(item['surviving'][0]))} a {_k(float(item['surviving'][-1]))}" if item["surviving"] else "")
        else:
            explored = ", ".join(_level(v) for v in item["explored"])
            surviving = ", ".join(f"{_level(v)} {_int(item['surviving_weight'].get(v, 0))}" for v in item["explored"])
        before = item["p2i2ac"]
        previous = "—" if before is None else f"{CLASS_ES.get(before['status'], before['status'])} " \
                                              f"({len(before['surviving'])})"
        lines.append(f"| {DIMS.get(name, name)} | {explored} | {surviving} | {CLASS_ES.get(item['status'], item['status'])}"
                     f" | {EDGE_ES.get(item['edge'], item['edge'])} | {previous} | {item['change'] or '—'} |")
    lines += ["", f"ρ: {identifiability['rho']['status']}."]
    return "\n".join(lines)


def render_representativos(data: dict) -> str:
    lines = []
    for tag in ("LOW", "MID", "HIGH"):
        item = data["representatives"].get(tag)
        if not item:
            continue
        lam, blood = item["lambda"], item["blood"]
        lines.append(f"**{tag}** (rango {_int(item['pick']['rank'])}): τ_D {_value(lam['debt_clearance_tau_min'])}, "
                     f"g {_value(lam['debt_per_delivery_deficit'])}, k {_k(lam['debt_to_lactate_gain'])}, "
                     f"τ_L {_value(lam['lactate_clearance_tau_min'])}, exceso {_level(lam['arrival_lactate_excess'])}, "
                     f"deuda {_level(lam['arrival_oxygen_debt'])}, entrega {_level(lam['arrival_delivery_ratio'])}; "
                     f"tasa {_value(blood['rate'])}, B0 {_value(blood['arrival_circulating_volume_ml'])}, "
                     f"λ/κ {_value(blood['preload_scale_over_kappa_ml'])}, relleno "
                     f"{_value(blood['plasma_refill_target_share'])} / {_value(blood['plasma_refill_tau_min'])} / "
                     f"{_value(blood['plasma_refill_capacity_ml'])}, unidad {_value(blood['red_cell_unit_hb_g_dl'])} "
                     f"g/dL × {_value(blood['red_cell_unit_volume_ml'])} mL, posiciones "
                     f"{_value(blood['positions']['gi_bleed_57m'])} / {_value(blood['positions']['gi_bleed_72f'])}; "
                     f"cristaloide {_point(item['crystalloid'])}.\n")
        lines += ["| Caso · escenario | min | Gasto relativo | DO2 (índice) | Demanda | Déficit | D | Lactato (mmol/L) | "
                  "Sangrado activo (mL/min) | Estado de O2 |", "|---|---|---|---|---|---|---|---|---|---|"]
        for key, run in item["runs"].items():
            case, scenario = key.split("|")
            for row in run["rows"]:
                lines.append(f"| {CASE_ES[case]} {scenario} | {row['minute']} | {_n(row['output_rel'], 3)} | "
                             f"{_n(row['do2'], 3)} | {_n(row['demand'], 2)} | {_n(row['effective_deficit'], 3)} | "
                             f"{_n(row['D'], 1)} | {_n(row['lactate'], 2)} | {_n(row['bleed_ml_per_min'], 2)} | "
                             f"{row['state']} |")
        lines += ["", "| Caso · escenario | Intervalos de 15′ (A / R / P; * sin sangrado) | D baja fuera de minutos sin "
                  "déficit | Minutos críticos bajo la D de llegada | Adecuación L3 | Igual a la factorización | Marcas |",
                  "|---|---|---|---|---|---|---|"]
        for key, run in item["runs"].items():
            case, scenario = key.split("|")
            intervals = " ".join(INTERVAL_ES[label] + ("" if bleeding else "*")
                                 for _, _, label, bleeding in run["intervals"])
            debt = run["debt"]
            adequacy = debt.get("l3_adequacy")
            adequacy_text = "—" if adequacy is None else f"{adequacy['status']} (T* {adequacy['onset']})"
            flags = "; ".join(FLAGS_ES[name] for name, on in run["flags"].items() if on) or "ninguna"
            lines.append(f"| {CASE_ES[case]} {scenario} | {intervals or '—'} | "
                         f"{len(debt['falls_outside_adequate_minutes'])} | {debt['critical_minutes_below_arrival']} | "
                         f"{adequacy_text} | {'sí' if run['rerun_equals_factorized'] else 'no'} | {flags} |")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_legado(data: dict) -> str:
    from .lactate_adequacy_report import render_legado as legado
    return legado(data)


def render_veredicto(data: dict) -> str:
    verdict = data["verdict"]
    lines = [f"**{verdict['verdict']}**\n", "| Comprobación | Resultado |", "|---|---|"]
    lines += [f"| {CHECKS_ES[name]} | {'sí' if verdict['checks'][name] else 'no'} |" for name in CHECKS_ES
              if name in verdict["checks"]]
    lines += ["", f"Regla congelada: {verdict['rule']}", "",
              f"Próximo dominio: {verdict['next_domain'] or 'ninguno (el veredicto no es READY)'}"]
    return "\n".join(lines)


RENDERERS = {"decisiones": render_decisiones, "deuda": render_deuda, "ganancia": render_ganancia,
             "filtro": render_filtro, "demanda": render_demanda, "region": render_region,
             "identificabilidad": render_identificabilidad, "representativos": render_representativos,
             "legado": render_legado, "veredicto": render_veredicto}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the lactate-closure JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
