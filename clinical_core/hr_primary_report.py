"""P2I-2AG report: the generated blocks of docs/revision/P2I2AG_SUPERFICIE_PRIMARIA_FC.md.

    python -m clinical_core.hr_primary_report --write <document> --data <the primary-surface JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import hr_primary as hp
from .blood_filter_report import _n
from .lactate_rebuild_report import CASE_ES, CASES, LEVEL_ES

NAMES = ("decisiones", "modo", "semantica", "superficie", "llegada", "soporte", "sensibilidad", "ejemplos",
         "identificabilidad", "presion", "escala_d", "no_regresion", "veredicto", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FACULTY_ES = {"decided": "fecha", "pressure": "presión", "intrinsic": "intrínseca", "hr1_hr2": "HR1 / HR2",
              "arrival": "llegada", "common_gains": "ganancias comunes", "saturation": "saturación",
              "d_scale": "escala de D", "rhythm": "ritmo", "scope": "alcance"}
CHECKS_ES = {"pressure_excluded": "la presión no entra en la aceptación de candidatos",
             "explicit_intrinsic": "toda intrínseca declarada (sin respaldo en la FC registrada)",
             "hr_semantics": "HR1 / HR2 con la semántica estructural vigente",
             "joint_arrival": "al menos un candidato conjunto compatible con la llegada (intrínseca común)",
             "common_gains": "sin ganancias propias de cada caso",
             "unchanged_physiology": "D, lactato, FR, BloodState y DO2 sin cambios; reconstrucción exacta"}
DIMS_ES = {"intrinsic": "intrínseca", "acute": "ganancia aguda", "debt": "ganancia de deuda", "ceiling": "techo",
           "intrinsic gi_bleed_57m": "intrínseca de 57m", "intrinsic gi_bleed_72f": "intrínseca de 72f"}
SETS_ES = {"gi_bleed_57m alone": "57m sola", "gi_bleed_72f alone": "72f sola",
           "joint, common intrinsic (primary)": "conjunta, intrínseca común (primaria)",
           "joint, case-specific intrinsic (sensitivity)": "conjunta, intrínseca por caso (sólo sensibilidad)"}
ORDER = {"intrinsic": list(hp.INTRINSIC), "acute": [repr(v) for v in hp.ACUTE], "debt": [repr(v) for v in hp.DEBT],
         "ceiling": [repr(v) for v in hp.CEILINGS]}


def _g(value) -> str:
    if value is None:
        return "—"
    if value == 0.0:
        return "0"
    return f"{value:.3g}".replace(".", ",")


def _yes(value) -> str:
    return "sí" if value else "no"


def _q(item, digits: int = 1) -> str:
    if not item:
        return "—"
    return " / ".join(_n(item[key], digits) for key in ("min", "median", "max"))


def render_decisiones(data: dict) -> str:
    records = data["records"]
    lines = [f"Congelamiento: `{data['freeze_digest']}` (una prueba lo fija). Registros de partida: P2I-2AD "
             f"`{records['P2I-2AD']}`, P2I-2AE `{records['P2I-2AE']}` y P2I-2AF `{records['P2I-2AF']}`.\n",
             "| Decisión docente | Texto registrado |", "|---|---|"]
    lines += [f"| {FACULTY_ES[name]} | {data['faculty'][name]} |" for name in FACULTY_ES]
    return "\n".join(lines)


def render_modo(data: dict) -> str:
    mode = data["design"]["primary_mode"]
    return (f"PRESSURE_SYMPATHETIC_CONTRIBUTION = **{mode['pressure']}**. Cambio del perfil de análisis en el modo "
            f"primario: `{json.dumps(mode['profile_changes'])}`; el valor por defecto común no cambia. Columna "
            f"diagnóstica: `{mode['diagnostic_column']}` = 25 × (1 − β) × 1,0 × (1 − P_rel), nunca leída por una "
            f"aceptación, una coincidencia ni un orden. Guarda: `{data['design']['guard']}`.")


def render_semantica(data: dict) -> str:
    sem = data["hr_semantics"]
    lines = ["| Regla | Enunciado | Sonda y criterio vigentes |", "|---|---|---|"]
    lines += [f"| {name} | {sem[name]['rule']} | {sem[name]['probe']} |" for name in ("HR1", "HR2")]
    lines += ["", f"Sólo estructurales: {_yes(sem['structural_only'])}; `check_hr` exige la intrínseca declarada: "
                  f"{_yes(sem['check_hr_requires_explicit_intrinsic'])}; HR2 (a) codificada: "
                  f"{_yes(sem['hr2_arrival_reduction_encoded'])}; sin objetivo registrado ni heredado: "
                  f"{_yes(sem['no_authored_or_legacy_target'])}; el respaldo en la FC registrada sigue fuera de la "
                  f"calibración: {_yes(sem['fallback_outside_calibration'])}."]
    return "\n".join(lines)


def render_superficie(data: dict) -> str:
    design = data["design"]
    surface = design["surface"]
    windows = design["windows"]
    return "\n".join([
        f"- Tolerancia de llegada: ±{_g(design['tolerance_bpm'])} lpm por caso; 57m {_n(windows[CASES[0]][0], 0)}–"
        f"{_n(windows[CASES[0]][1], 0)}, 72f {_n(windows[CASES[1]][0], 0)}–{_n(windows[CASES[1]][1], 0)}.",
        f"- Intrínseca: 60 / 80 / 100. Ganancia aguda: {' · '.join(_g(v) for v in surface['acute'])}. Ganancia de "
        f"deuda: {' · '.join(_g(v) for v in surface['debt'])}. Techo: "
        f"{' / '.join(_n(v, 0) for v in surface['ceilings'])} (HR_RESERVE = techo − intrínseca). "
        f"{surface['count']} candidatos.", "", f"Regla: {surface['rule']}", "", f"Compatibilidad: {design['arrival_rule']}"])


def render_llegada(data: dict) -> str:
    arrival = data["arrival"]
    lines = ["| | 57m | 72f |", "|---|---|---|",
             f"| compatibles (de {arrival['total_decompositions'] // 2}) | {arrival['compatible'][CASES[0]]} | "
             f"{arrival['compatible'][CASES[1]]} |"]
    for tag, counts in arrival["compatible_by_representative"].items():
        lines.append(f"| … representante {tag} | {counts[CASES[0]]} | {counts[CASES[1]]} |")
    rej = arrival["analytic_rejections"]
    lines += ["", f"Descomposiciones de llegada: {arrival['total_decompositions']} (analíticas). Conjuntamente "
                  f"compatibles con la intrínseca común: **{arrival['joint_common_intrinsic']}** (por representante: "
                  f"{', '.join(f'{t} {v}' for t, v in arrival['joint_by_representative'].items())}).", "",
              "| Rechazo analítico | Candidatos |", "|---|---|"]
    lines += [f"| {name} | {count} |" for name, count in rej.items()]
    lines += ["", f"Rechazos por simulación: {arrival['simulation_rejections']}. Fisiología de llegada idéntica en ambos "
                  f"casos por representante: {', '.join(f'{t} {_yes(v)}' for t, v in arrival['identical_arrival_physiology'].items())}; "
                  f"ventanas disjuntas: {_yes(arrival['windows_disjoint'])}. Con una predicción común, la cota inferior del "
                  f"peor desajuste es {_n(arrival['minimum_common_mismatch_bound_bpm'], 0)} lpm (la mitad de 124 − 112), "
                  f"mayor que la tolerancia. Ganancias propias de cada caso requeridas: "
                  f"{_yes(arrival['case_specific_gain_required'])}. La llegada es la misma con la presión activa o "
                  f"neutralizada: {_yes(arrival['pressure_on_equal_at_arrival'])}."]
    return "\n".join(lines)


def render_soporte(data: dict) -> str:
    support = data["arrival"]["support"]
    lines = []
    for dim in ("intrinsic", "acute", "debt", "ceiling"):
        values = ORDER[dim]
        label = {"intrinsic": lambda v: LEVEL_ES[v], "ceiling": lambda v: _n(float(v), 0)}.get(dim, lambda v: _g(float(v)))
        lines += [f"**{DIMS_ES[dim]}**", "", "| Caso | " + " | ".join(label(v) for v in values) + " |",
                  "|---|" + "---|" * len(values)]
        lines += [f"| {CASE_ES[case]} | " + " | ".join(str(support[case][dim][v]) for v in values) + " |" for case in CASES]
        lines.append("")
    return "\n".join(lines).rstrip()


def _values(counts: dict, keys: list) -> str:
    return ", ".join(f"{_g(float(key))}: {counts[key]}" for key in keys)


def render_sensibilidad(data: dict) -> str:
    sens = data["arrival"]["case_intrinsic_sensitivity"]
    lines = [f"Sólo sensibilidad, no aprobada (aprobada: {_yes(sens['approved'])}). Candidatos conjuntamente compatibles "
             f"si la intrínseca puede diferir por caso (ganancias y techo comunes): **{sens['joint']}** de {sens['of']} "
             f"(por representante: {', '.join(f'{t} {v}' for t, v in sens['by_representative'].items())}).", "",
             "| intrínseca 57m \\ 72f | inferior | medio | superior |", "|---|---|---|---|"]
    for first in hp.INTRINSIC:
        lines.append(f"| {LEVEL_ES[first]} | " + " | ".join(str(sens["intrinsic_pairs"][f"{first}|{second}"])
                                                              for second in hp.INTRINSIC) + " |")
    lines += ["", "| Dimensión | Apoyo por valor |", "|---|---|",
              f"| ganancia aguda | {_values(sens['acute'], ORDER['acute'])} |",
              f"| ganancia de deuda | {_values(sens['debt'], ORDER['debt'])} |",
              f"| techo | {_values(sens['ceiling'], [f'{v:g}' for v in hp.CEILINGS])} |"]
    return "\n".join(lines)


def render_ejemplos(data: dict) -> str:
    lines = ["Primer candidato compatible de cada representante y caso, en el orden de la superficie (ilustración, nunca "
             "un orden de preferencia):", "",
             "| Rep. | Caso | intr. | aguda | deuda | techo | señal | D0 | aguda (lpm) | deuda (lpm) | saturado | "
             "uso de reserva | predicha | desajuste |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, row in data["examples"].items():
        tag, rest = key.split("|")
        if rest == "sensitivity" or row is None:
            continue
        lines.append(f"| {tag} | {CASE_ES[rest]} | {_n(row['intrinsic'], 0)} | {_g(row['acute'])} | {_g(row['debt'])} | "
                     f"{_n(row['ceiling'], 0)} | {_n(row['x0'], 2)} | {_n(row['D0'], 0)} | "
                     f"{_n(row['acute_unconstrained_bpm'], 1)} | {_n(row['debt_unconstrained_bpm'], 1)} | "
                     f"{_n(row['saturated_bpm'], 1)} | {_n(row['reserve_utilization'], 2)} | {_n(row['predicted'], 1)} | "
                     f"{_n(row['mismatch'], 1)} |")
    return "\n".join(lines)


def render_identificabilidad(data: dict) -> str:
    ident = data["identifiability"]
    lines = [f"Regla congelada: {ident['rule']}", "", "| Conjunto | Dimensión | Estado |", "|---|---|---|"]
    for name, dims in ident["sets"].items():
        for dim, status in dims.items():
            lines.append(f"| {SETS_ES[name]} | {DIMS_ES[dim]} | {status} |")
    lines += ["", "Compuestos observables entre los compatibles de cada caso (mín. / mediana / máx.):", "",
              "| Caso | aguda en la llegada (lpm) | deuda en la llegada (lpm) | incremento simpático total (lpm) | "
              "uso de la reserva saturada |", "|---|---|---|---|---|"]
    for case in CASES:
        comp = ident["composites"][case]
        lines.append(f"| {CASE_ES[case]} | {_q(comp['acute_increment_at_arrival_bpm'])} | "
                     f"{_q(comp['debt_increment_at_arrival_bpm'])} | {_q(comp['total_sympathetic_increment_bpm'])} | "
                     f"{_q(comp['saturated_reserve_utilization'], 2)} |")
    lines += ["", f"Escala de D: {ident['d_scale']}."]
    return "\n".join(lines)


def render_presion(data: dict) -> str:
    audit = data["pressure_audit"]
    lines = [f"Muestra P2I-2AF: {audit['minutes']} minutos con pulso de las 18 corridas representativas. Correlación "
             f"entre las señales (déficit / demanda y 1 − P_rel): {_g(audit['correlation_signals'])}. Las dos empujan "
             f"la FC hacia arriba en {audit['both_push_up']} minutos ({_n(100 * audit['both_push_up_share'], 0)} %); la "
             f"presión la empuja hacia abajo con déficit presente en {audit['pressure_down_while_deficit']} "
             f"({_n(100 * audit['pressure_down_while_deficit_share'], 0)} %). En esos minutos (mín. / mediana / máx.): "
             f"señal de déficit {_q(audit['deficit_signal_in_those_minutes'], 3)}; cancelación por presión "
             f"{_q(audit['pressure_cancellation_bpm'])} lpm sin saturar; fracción de aguda + deuda cancelada en el "
             f"ancla {_q(audit['cancelled_share_of_acute_and_debt_at_anchor'], 2)}.", "",
             "FC con la presión activa menos neutralizada, y FC sobre la intrínseca, en el plano 5 × 5 de ganancias "
             "(techo 175, intrínseca media; LOW / MID / HIGH × 57m / 72f):", "",
             "| Hito | activa − neutralizada (lpm) | sobre la intrínseca, activa (lpm) | sobre la intrínseca, "
             "neutralizada (lpm) |", "|---|---|---|---|"]
    for name, row in audit["landmarks"].items():
        lines.append(f"| {name} | {_q(row['hr_on_minus_off_bpm'])} | {_q(row['on_above_intrinsic_bpm'])} | "
                     f"{_q(row['off_above_intrinsic_bpm'])} |")
    changes = audit["ranking_changes"]
    lines += ["", f"Órdenes descriptivos de los 25 puntos por FC en cada hito, activa frente a neutralizada (no hay "
                  f"ninguna selección): {changes['discordant']} pares invertidos y {changes['ties_changed']} empates "
                  f"que cambian, de {changes['pairs']}. {audit['arrival_unaffected']}. Clasificación: "
                  f"**{audit['classification']}**; calibrado: {_yes(audit['calibrated'])}."]
    return "\n".join(lines)


def render_escala_d(data: dict) -> str:
    probe, rhythm = data["d_scale"], data["rhythm"]
    rows = "; ".join(f"c = {_g(r['c'])}: brecha {_g(r['max_gap_bpm'])} lpm (sin dividir la ganancia, "
                     f"{_n(r['without_gain_division_gap_bpm'], 1)} lpm)" for r in probe["rows"])
    cases = "; ".join(f"{name}: {item['rates']} lpm, constante {_yes(item['rate_constant'])}"
                      for name, item in rhythm["cases"].items())
    return (f"Escala de D en el modo primario (D × c, ganancia / c): {rows}. Se cumple: {_yes(probe['holds'])}.\n\n"
            f"Ritmo y betabloqueo con deuda en el modo primario: {cases}. Clasificación: {rhythm['classification']}; "
            f"afecta a GI: {_yes(rhythm['affects_gi'])}.")


def render_no_regresion(data: dict) -> str:
    val, nr = data["validation"], data["non_regression"]
    return (f"Reconstrucción primaria frente al núcleo completo con la ganancia de presión 0: {val['full_reruns']} "
            f"recorridas, todas exactas: {_yes(val['agree'])} (impulso, FC y FC de llegada analítica); ninguna "
            f"contribución de presión: {_yes(val['no_pressure'])}. Estados completos con la presión activa y "
            f"neutralizada: {nr['states_compared']} comparados, iguales salvo el impulso: "
            f"{_yes(nr['states_equal_but_drive'])} (BloodState, V, Hb, D, lactato, demanda). Entrega, déficit efectivo, "
            f"FR, lactato y gasto derivados iguales: {_yes(nr['delivery_deficit_rr_lactate_equal'])}. D y lactato "
            f"frente al registro P2I-2AD: {nr['d_lactate_vs_p2i2ad']['rows_checked']} filas, iguales "
            f"{_yes(nr['d_lactate_vs_p2i2ad']['equal'])}.")


def render_veredicto(data: dict) -> str:
    verdict = data["verdict"]
    lines = [f"**{verdict['verdict']}**\n", "| Comprobación | Resultado |", "|---|---|"]
    lines += [f"| {CHECKS_ES[name]} | {_yes(verdict['checks'][name])} |" for name in CHECKS_ES]
    lines += ["", f"Detenido (sin paquete de trayectorias ni propuesta de envolventes): {_yes(verdict['stopped'])}. "
                  f"Aprobado: {_yes(verdict['approved'])}.", "", f"Regla congelada: {verdict['rule']}"]
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return (f"Corridas de representantes: {e['representative_runs']}; recorridas de validación: "
            f"{e['validation_full_reruns']}; corridas de estados para la no-regresión: {e['non_regression_state_runs']}; "
            f"descomposiciones de llegada analíticas: {e['arrival_decompositions_analytic']}; rechazos analíticos: "
            f"{sum(e['analytic_rejections'].values())}; rechazos por simulación: {e['simulation_rejections']}; series "
            f"posprocesadas (auditoría de presión): {e['post_processed_series']}; paquete de trayectorias construido: "
            f"{_yes(e['trajectory_decision_pack_built'])}; barrido cartesiano: {_yes(e['cartesian_sweep'])}; motor "
            f"heredado leído: {_yes(e['legacy_read'])}.")


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the primary-surface JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
