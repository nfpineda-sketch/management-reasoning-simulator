"""P2I-2AC report: the generated blocks of docs/revision/P2I2AC_DEUDA_Y_ADECUACION_L3.md.

    python -m clinical_core.lactate_adequacy_report --write <document> --data <the lactate-adequacy JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import lactate_adequacy as la
from .blood_filter_report import _n, _value
from .blood_fluid_readiness_report import _point
from .lactate_rebuild_report import (CASE_ES, CASES, CLASS_ES, DIMENSIONS_ES, EDGE_ES, FLAGS_ES, STAGE_ES, STATUS_ES,
                                     _int, _level, _sci, _share, _summary)

MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->")
           for name in ("decisiones", "deuda", "auditoria", "filtro", "demanda", "region", "identificabilidad",
                        "representativos", "legado", "veredicto")}
INTERVAL_ES = {"ADEQUATE": "A", "RECOVERING_CRITICAL": "R", "PERSISTENT_OR_WORSENING_CRITICAL": "P"}
FACULTY_ES = {"decided": "fecha", "debt": "D (deuda de entrega de O2)", "l3_adequacy": "adecuación L3",
              "bleeding": "sangrado en curso", "demand": "demanda metabólica", "rho": "ρ",
              "fd_lac_04": "FD-LAC-04", "fd_lac_05": "FD-LAC-05"}
AUDIT_ES = {"PERSISTENT_OR_WORSENING_WITH_RESIDUAL_BLEEDING": "déficit persistente o que empeora, con sangrado residual "
                                                              "(viola FD-LAC-06)",
            "RECOVERING_WITH_RESIDUAL_BLEEDING": "déficit crítico que se recupera, con sangrado residual (permitido)",
            "NO_RESIDUAL_BLEEDING": "sin sangrado residual en la caída (permitido)",
            "ADEQUATE_OR_COMPENSATED": "adecuado o compensado (permitido)"}
CHECKS_ES = {"p2i2ab_record": "registro P2I-2AB comprometido", "factorization": "factorización exacta (D no cae con "
                                                                               "déficit)",
             "debt_coherent": "D coherente en los representativos", "survivors": "hay sobrevivientes con demanda 1,0",
             "l3_adequacy": "todo sobreviviente restaura la adecuación L3",
             "definitive_management_evaluable": "FD-LAC-04/05 evaluadas en ambos casos para todo sobreviviente",
             "actual_flow": "sangrado residual leído por flujo real",
             "demand_characterized": "capa de demanda clasificó todos los candidatos",
             "patient_like": "sin marcas de inverosimilitud en los representativos"}


def _case(text: str) -> str:
    return text.replace("gi_bleed_57m", "57m").replace("gi_bleed_72f", "72f")


def render_decisiones(data: dict) -> str:
    lines = [f"Congelamiento: `{data['freeze_digest']}` (una prueba lo fija). Registro de partida: P2I-2AB "
             f"`{data['records']['P2I-2AB']}`.\n", "| Decisión docente | Texto registrado |", "|---|---|"]
    lines += [f"| {FACULTY_ES.get(name, name)} | {text} |" for name, text in data["faculty"].items()]
    source = data["source"]
    lines += ["", f"Espacio fuente reutilizado de P2I-2AB: {source['p1_sets']} conjuntos P1, {source['p3_sets']} "
                  f"conjuntos P3, {source['crystalloid_points']} puntos del cristaloide y {source['lactate_side']} "
                  f"puntos del lado del lactato. ρ en la rejilla de sangre: "
                  f"{', '.join(_value(r) for r in source['reserves_on_the_blood_grid'])} (no se cuenta)."]
    return "\n".join(lines)


def render_deuda(data: dict) -> str:
    validation, efficiency = data["validation"], data["efficiency"]
    lines = ["| Comprobación | Resultado |", "|---|---|",
             f"| Corridas completas del núcleo corregido comparadas | {validation['runs']} |",
             f"| Coinciden todas (lactato, D, déficit, flujo, eventos y veredictos) | "
             f"{'sí' if validation['agree'] else 'no'} |",
             f"| Exactas con ρ 2,5 (demanda {', '.join(_value(d) for d in validation['demands'])}) | "
             f"{'sí' if validation['exact_at_reserve_2_5'] else 'no'} |",
             f"| ρ comparadas | {', '.join(_value(r) for r in validation['reserves'])} (1 sólo como referencia "
             f"sintética) |",
             f"| Mayor diferencia fuera de ρ 2,5 | {_sci(validation['max_gap_other_reserves'])} |",
             f"| D nunca cae en un minuto que leyó déficit | {'sí' if validation['no_debt_fall_in_deficit'] else 'no'} |",
             f"| Desacuerdos | {len(validation['disagreements'])} |", ""]
    lines += ["Estados que ejerció la muestra: " + "; ".join(
        f"{_case(name).replace('True', 'pasa').replace('False', 'falla')} {n}"
        for name, n in validation["verdicts_seen"].items()) + ".\n"]
    units = efficiency["post_processed_units"]
    lines += ["| Eficiencia | Valor |", "|---|---|",
              f"| Trayectorias hemodinámicas simuladas (compartidas por las tres demandas) | "
              f"{_int(efficiency['haemodynamic_trajectories'])} |",
              f"| Corridas del producto ingenuo (candidatos × 3 escenarios × 2 casos × 3 demandas) | "
              f"{_int(efficiency['naive_core_runs'])} |",
              f"| Corridas completas de validación / de representativos | {efficiency['validation_full_runs']} / "
              f"{efficiency['representative_full_runs']} |",
              "| Unidades post-procesadas (unidad × lado del lactato) | " + "; ".join(
                  f"×{_value(f)}: " + ", ".join(f"{s} {_int(n)}" for s, n in item.items()) for f, item in units.items()) + " |",
              f"| Filas de sangre reutilizadas de P2I-2AB (no recalculadas) | "
              f"{_int(efficiency['blood_rows_reused_from_p2i2ab'])} |",
              f"| Rechazos analíticos | {efficiency['analytic_rejections']} |"]
    return "\n".join(lines)


def render_auditoria(data: dict) -> str:
    audit = data["audit"]
    lines = [f"{audit['rule']}\n", "| Lectura | Candidatos |", "|---|---|",
             f"| Sobrevivientes de P2I-2AB | {_int(audit['survivors'])} |",
             f"| Señalados por P2I-2AB (caída con déficit persistente tras la hemostasia) | {_int(audit['flagged'])} "
             f"(registro: {_int(audit['p2i2ab_flagged'])}; reproducido: {'sí' if audit['reproduced'] else 'no'}) |"]
    for name in la.AUDIT_CLASSES:
        lines.append(f"| · {AUDIT_ES[name]} | {_int(audit['classes'][name])} |")
    lines += [f"| **Violarían FD-LAC-06 con sangrado por flujo real** | **{_int(audit['would_violate_fd06'])}** |",
              f"| Sobrevivientes que violan FD-LAC-06 por sangrado residual (D de P2I-2AB) | "
              f"{_int(audit['violating_residual_old_d'])} |",
              f"| · de ellos, no señalados por P2I-2AB (pares que cruzan la hemostasia) | "
              f"{_int(audit['violating_residual_old_d_not_flagged'])} |",
              f"| Sobrevivientes que violan FD-LAC-06 por flujo real, en cualquier ventana (D de P2I-2AB) | "
              f"{_int(audit['violating_actual_flow_fd06_old_d'])} |",
              f"| Con la D corregida: violan por sangrado residual (todos / señalados) | "
              f"{_int(audit['violating_residual_corrected_d'])} / "
              f"{_int(audit['flagged_violating_residual_corrected_d'])} |"]
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
        for bit in range(len(la.BITS[stage["scenario"]])):
            name = la._label(stage["scenario"], bit)
            if name in stage["any_failure"]:
                lines.append(f"| {stage['scenario']} | {_case(name)} | {_int(stage['first_failure'].get(name, 0))} | "
                             f"{_int(stage['any_failure'][name])} |")
    lines += ["", "| Etapa | Única restricción que rechaza | Candidatos |", "|---|---|---|"]
    for stage in filtered["stages"]:
        for name in dict.fromkeys(name for name, _ in la.BITS[stage["scenario"]]):
            if name in stage["only_failure"]:
                lines.append(f"| {stage['scenario']} | {name} | {_int(stage['only_failure'][name])} |")
    return lines


def render_filtro(data: dict) -> str:
    primary = data["filter"]["1"]
    lines = [f"Demanda 1,0 (la región). Candidatos: {_int(primary['candidates'])}; sobrevivientes: "
             f"**{_int(primary['survivors'])}** ({_share(primary['survivors'], primary['candidates'])}).\n"]
    lines += _stage_tables(primary)
    l3 = next(stage for stage in primary["stages"] if stage["scenario"] == "L3")
    inadequate = {name: n for name, n in l3["any_failure"].items() if name.startswith("L3_RESUSCITATION_INADEQUATE")}
    lines += ["", "L3_RESUSCITATION_INADEQUATE, informado aparte (nunca como fallo de FD-LAC-04): "
              + ("; ".join(f"{_case(name).split()[-1]} {_int(n)}" for name, n in inadequate.items()) or "ninguno")
              + f"; como primer fallo de L3: {_int(sum(n for k, n in l3['first_failure'].items() if k in inadequate))}"
              + f"; como única causa: {_int(l3['only_failure'].get('L3_RESUSCITATION_INADEQUATE', 0))}."]
    return "\n".join(lines)


def render_demanda(data: dict) -> str:
    demand = data["demand"]
    lines = [f"{demand['rule']}\n", "| Demanda | Sobrevivientes |", "|---|---|"]
    lines += [f"| ×{_value(f)} | {_int(n)} |" for f, n in demand["survivors"].items()]
    lines += ["", "| Clase | Candidatos |", "|---|---|"]
    lines += [f"| {name} | {_int(demand['classes'][name])} |" for name in (la.ROBUST, la.SENSITIVE, la.INCOMPATIBLE)]
    lines += ["", "| Sobrevive con demanda | Candidatos |", "|---|---|"]
    lines += [f"| {' y '.join(_value(f) for f in key.split('+'))} | {_int(n)} |" for key, n in demand["patterns"].items()]
    final = demand["final_region"]
    lines += ["", f"En la región (demanda 1,0): ROBUST {_int(final['ROBUST'])}, DEMAND-SENSITIVE "
                  f"{_int(final['DEMAND-SENSITIVE'])}."]
    for factor in ("0.9", "1.1"):
        filtered = data["filter"][factor]
        lines += ["", f"Filtro con demanda ×{_value(factor)} (sólo informa):", ""] + _stage_tables(filtered)
    return "\n".join(lines)


def render_region(data: dict) -> str:
    region, stats, against = data["region"], data["statistics"], data["against_p2i2ab"]
    survivors = region["candidates"]
    lines = [f"**{region['status']}**: {_int(region['units'])} unidades (P1 × lado del lactato), {_int(survivors)} "
             f"candidatos; resumen de la región `{region['digest']}`. Frente a P2I-2AB ({_int(against['p2i2ab'])}): "
             f"se mantienen {_int(against['kept'])}, salen {_int(against['lost'])}, entran {_int(against['new'])}.\n"]
    if not stats:
        return "\n".join(lines)
    lines += ["| Lectura (mín · p5 · mediana · p95 · máx) | 57m | 72f |", "|---|---|---|"]
    for key, label in (("L60", "L60 sin tratamiento (mmol/L)"), ("L120", "L120 con L3 (mmol/L)"),
                       ("D120", "D a los 120′ con L3"), ("fd04_at_trigger", "L(T*) (mmol/L)"),
                       ("fd04_reduction", "caída a T* + 30 (fracción)")):
        lines.append(f"| {label} | {_summary(stats[key]['gi_bleed_57m'])} | {_summary(stats[key]['gi_bleed_72f'])} |")
    lines += ["", "| Estado entre los sobrevivientes | 57m | 72f |", "|---|---|---|"]
    for key, label in (("fd01_status", "FD-LAC-01"), ("fd04_status", "FD-LAC-04"), ("fd05_status", "FD-LAC-05")):
        for status in ("PASS", "ALREADY_NORMALIZED", "NOT_APPLICABLE", "NOT_EVALUABLE"):
            counts = [stats[key][c].get(status, 0) for c in CASES]
            if any(counts):
                lines.append(f"| {label} {STATUS_ES[status]} | {_int(counts[0])} ({_share(counts[0], survivors)}) | "
                             f"{_int(counts[1])} ({_share(counts[1], survivors)}) |")
    for key, label in (("fd04_not_evaluable", "FD-LAC-04"), ("fd05_not_evaluable", "FD-LAC-05")):
        for case in CASES:
            for reason, n in stats[key][case].items():
                lines.append(f"| {label} NOT_EVALUABLE {CASE_ES[case]}: {reason} | {_int(n)} | |")
    lines += [f"| FD-LAC-04 y 05 evaluadas en ambos casos | {_int(stats['fd04_and_05_evaluated_in_both_cases'])} "
              f"({_share(stats['fd04_and_05_evaluated_in_both_cases'], survivors)}) | |",
              f"| 72f con FD-LAC-05 NOT_EVALUABLE y L120 sobre la envolvente | "
              f"{_int(stats['fd05_not_evaluable_72f_above_envelope'])} | |"]
    lines += ["", "| Sensibilidad de FD-LAC-04 (diagnóstico, no filtra) | Sobrevivientes que también pasarían |",
              "|---|---|"]
    for threshold, n in stats["fd04_sensitivity"]["thresholds"].items():
        label = "cualquier caída" if float(threshold) == 0 else f"caída ≥ {_n(100 * float(threshold), 0)} %"
        lines.append(f"| {label} | {_int(n)} ({_share(n, survivors)}) |")
    recovering = stats["recovering_declines_allowed"]["survivors_with_one"]
    lines += ["", "| Lectura informativa (no filtra) | Sobrevivientes |", "|---|---|",
              "| con una caída sostenida aceptada como RECOVERING_CRITICAL | " + "; ".join(
                  f"{s.replace('residual bleeding', 'con sangrado residual')} {_int(n)}"
                  for s, n in recovering.items()) + " |",
              f"| con algún minuto COMPENSATED (déficit 0, entrega < demanda) en [T*, T* + 30] | "
              f"{_int(stats['adequacy_by_compensation_after_trigger'])} |"]
    for key, label in (("adequacy_onset", "inicio de la adecuación sostenida"), ("trigger_minute", "T* de FD-LAC-04")):
        lines.append(f"| {label} | " + "; ".join(f"{CASE_ES[c]}: " + ", ".join(
            f"{'ninguno' if m == 'None' else 'minuto ' + m} {_int(n)}"
            for m, n in sorted(stats[key][c].items(), key=lambda kv: (kv[0] == "None", int(kv[0]) if kv[0] != "None"
                                                                      else 0)))
            for c in CASES) + " |")
    return "\n".join(lines)


def render_identificabilidad(data: dict) -> str:
    identifiability = data["identifiability"]
    lines = ["| Dimensión | Explorado | Sobrevive (candidatos) | Clase | Borde | P2I-2AB | Cambio |",
             "|---|---|---|---|---|---|---|"]
    for name, item in identifiability["dimensions"].items():
        if name == "crystalloid_point":
            explored = f"{len(item['explored'])} puntos"
            weights = sorted(item["surviving_weight"].values())
            surviving = f"{len(item['surviving'])} sobreviven" + (
                f" ({_int(weights[0])} a {_int(weights[-1])} cada uno)" if weights else "")
        else:
            explored = ", ".join(_level(v) for v in item["explored"])
            surviving = ", ".join(f"{_level(v)} {_int(item['surviving_weight'].get(v, 0))}" for v in item["explored"])
        before = item["p2i2ab"]
        previous = "—" if before is None else f"{CLASS_ES.get(before['status'], before['status'])} " \
                                              f"({len(before['surviving'])})"
        label = "demanda (×)" if name == "demand_factor" else DIMENSIONS_ES.get(name, name)
        lines.append(f"| {label} | {explored} | {surviving} | {CLASS_ES.get(item['status'], item['status'])} | "
                     f"{EDGE_ES.get(item['edge'], item['edge'])} | {previous} | {item['change'] or '—'} |")
    rho = identifiability["rho"]
    lines += ["", f"ρ: {rho['status']}."]
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
        lines += ["", "| Caso · escenario | Intervalos de 15′ (A / R / P; * sin sangrado) | D cae con déficit leído "
                  "por el núcleo | D cae con déficit final que empeora | Igual a la factorización | Marcas |",
                  "|---|---|---|---|---|---|"]
        for key, run in item["runs"].items():
            case, scenario = key.split("|")
            intervals = " ".join(INTERVAL_ES[label] + ("" if bleeding else "*")
                                 for _, _, label, bleeding in run["intervals"])
            debt = run["debt"]
            end_state = debt["end_state_worsening_with_falling_d"]
            flags = "; ".join(FLAGS_ES[name] for name, on in run["flags"].items() if on) or "ninguna"
            lines.append(f"| {CASE_ES[case]} {scenario} | {intervals or '—'} | "
                         f"{len(debt['core_read_deficit_with_falling_d'])} | "
                         f"{len(end_state)}{' (minuto ' + ', '.join(map(str, end_state)) + ', inicio)' if end_state else ''}"
                         f" | {'sí' if run['rerun_equals_factorized'] else 'no'} | {flags} |")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_legado(data: dict) -> str:
    legacy = data["legacy_reference"]
    order = sorted(next(iter(legacy["legacy"]["gi_bleed_57m"].values())), key=int)
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
    lines = [f"**{verdict['verdict']}**\n", "| Comprobación | Resultado |", "|---|---|"]
    lines += [f"| {CHECKS_ES[name]} | {'sí' if verdict['checks'][name] else 'no'} |" for name in CHECKS_ES
              if name in verdict["checks"]]
    lines += ["", f"Regla congelada: {verdict['rule']}", "",
              f"Próximo dominio: {verdict['next_domain'] or 'ninguno (el veredicto no es READY)'}"]
    return "\n".join(lines)


RENDERERS = {"decisiones": render_decisiones, "deuda": render_deuda, "auditoria": render_auditoria,
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
    parser.add_argument("--data", type=Path, required=True, help="the lactate-adequacy JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
