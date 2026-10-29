"""P2I-2AF report: the generated blocks of docs/revision/P2I2AF_SHOCK_AGUDO_Y_SATURACION_FC.md.

    python -m clinical_core.hr_shock_report --write <document> --data <the HR-shock JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import hr_shock as hk
from .blood_filter_report import _n
from .lactate_rebuild_report import CASE_ES, CASES, LEVEL_ES

MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->")
           for name in ("decisiones", "resto", "estructura", "candidatos", "llegada", "trayectorias", "sondas",
                        "saturacion", "invariantes", "superficie", "presion", "identificabilidad", "fr", "legado",
                        "veredicto", "siguiente", "eficiencia")}
TAGS = hk.TAGS
FACULTY_ES = {"decided": "fecha", "shock_recoverable": "shock recuperable", "acute_signal": "señal aguda",
              "d_scale": "escala de D", "saturation": "saturación", "intrinsic": "intrínseca", "scope": "alcance"}
CHECKS_ES = {"factorization": "la reconstrucción de la FC coincide con el núcleo completo",
             "no_residual": "sin resto de llegada (la FC registrada no llega a la dinámica)",
             "acute_recoverable": "contribución aguda explícita y que se resuelve",
             "no_tau_d_leak": "τ_D no llega a la FC con D fija",
             "d_scale_invariance": "D × c con ganancia / c da la misma FC",
             "smooth_saturation": "saturación suave y ninguna FC sobre el techo",
             "invariants": "las doce direcciones se cumplen",
             "d_lactate_rr_unchanged": "D, lactato y FR sin cambios",
             "patient_like": "sin banderas estructurales"}
FIELDS = (("hr", "FC", 1), ("intrinsic", "intr.", 0), ("acute_bpm", "aguda", 1), ("debt_bpm", "deuda", 1),
          ("pressure_bpm", "presión", 1), ("unconstrained_bpm", "sin sat.", 1), ("saturated_bpm", "saturado", 1),
          ("effective_deficit", "déficit", 3), ("D", "D", 1), ("output", "gasto", 2),
          ("bleed_ml_per_min", "sangrado", 2), ("prbc_units", "GR (U)", 2), ("crystalloid_in_ml", "cristaloide", 0))


def _g(value) -> str:
    if value is None:
        return "—"
    if value == 0.0:
        return "0"
    return f"{value:.3g}".replace(".", ",")


def _yes(value) -> str:
    return "sí" if value else "no"


def _clean(value, digits: int):
    return 0.0 if round(value, digits) == 0 else value


def render_decisiones(data: dict) -> str:
    lines = [f"Congelamiento: `{data['freeze_digest']}` (una prueba lo fija). Registros de partida: P2I-2AD "
             f"`{data['records']['P2I-2AD']}` y P2I-2AE `{data['records']['P2I-2AE']}`.\n",
             "| Decisión docente | Texto registrado |", "|---|---|"]
    lines += [f"| {FACULTY_ES[name]} | {data['faculty'][name]} |" for name in FACULTY_ES]
    return "\n".join(lines)


def render_resto(data: dict) -> str:
    residual = data["residual"]
    lines = ["| Pregunta | Respuesta |", "|---|---|",
             f"| dónde se guarda | {residual['stored']} |", f"| cómo se calcula | {residual['calculation']} |",
             f"| ¿propio del caso? | {_yes(residual['case_specific'])} |",
             f"| ¿persiste indefinidamente? | {_yes(residual['persists_indefinitely'])} |",
             f"| quién lo lee | {'; '.join(residual['read_by'])} |",
             f"| clasificación | **{residual['class']}**: {residual['why']} |", "",
             "Cuánto de la parte simpática de la FC de llegada sostenía el resto en P2I-2AE (sobre su soporte "
             "coherente):", "", "| Caso | Fracción mín. | Fracción máx. | lpm mín. | lpm máx. | Intrínseca 80, D0 20 "
             "(lpm de resto / de la parte simpática, por ganancia) |", "|---|---|---|---|---|---|"]
    for case in CASES:
        row = residual["amounts"][case]
        ref = "; ".join(f"{_g(float(g))}: {_n(v['residual_bpm'], 1)} / {_n(v['of_bpm'], 0)}"
                        for g, v in row["at_intrinsic_80_debt_20"].items())
        lines.append(f"| {CASE_ES[case]} | {_n(100 * row['residual_share_min'], 0)} % | "
                     f"{_n(100 * row['residual_share_max'], 0)} % | {_n(row['residual_bpm_min'], 1)} | "
                     f"{_n(row['residual_bpm_max'], 1)} | {ref} |")
    return "\n".join(lines)


def render_estructura(data: dict) -> str:
    audit = data["audit"]
    lines = ["| Lectura del código vigente | Resultado |", "|---|---|"]
    lines += [f"| `{name}` | {_yes(value)} |" for name, value in audit["reads"].items()]
    lines += ["", f"Sin resto: {_yes(audit['no_residual'])}; término agudo: {_yes(audit['acute_term'])}; τ_D fuera de "
                  f"la FC: {_yes(audit['no_tau_d_in_hr'])}; saturación suave: {_yes(audit['smooth_saturation'])}; la FR "
                  f"no lee la FC: {_yes(audit['rr_independent_of_hr'])}."]
    return "\n".join(lines)


def render_candidatos(data: dict) -> str:
    design = data["design"]
    lines = []
    for name, label in (("acute", "acute_deficit_to_sympathetic_gain"), ("debt", "debt_to_sympathetic_gain")):
        item = design[name]
        lines.append(f"- `{label}`: de {_g(item['low'])} a {_g(item['high'])}, puntos "
                     f"{' · '.join(_g(p) for p in item['points'])} y 0 (referencia sintética); soporte "
                     f"{', '.join(_g(v) for v in item['support'])}.")
    ceiling = design["ceiling"]
    lines += [f"- Techo sinusal: {' / '.join(_n(c, 0) for c in ceiling['ceilings'])} lpm. {ceiling['rule']} Por encima de "
              f"toda FC registrada y de toda intrínseca: {_yes(ceiling['above_authored_and_intrinsic'])}; casi lineal "
              f"en la menor parte simpática registrada ({_n(ceiling['smallest_share_bpm'], 0)} lpm, compresión máxima "
              f"{_g(max(ceiling['compression_at_smallest_share_bpm'].values()))} lpm): {_yes(ceiling['near_linear'])}.",
              f"- Ancla de los cortes (punto de lectura, no una selección): ganancia aguda {_g(design['anchor']['acute'])},"
              f" de deuda {_g(design['anchor']['debt'])}, techo {_n(design['anchor']['ceiling'], 0)}, intrínseca media.",
              "", "Reglas:", "", f"- aguda: {hk.acute_gain_design.__doc__.strip()}",
              f"- deuda: {hk.debt_gain_design.__doc__.strip()}"]
    return "\n".join(lines)


def render_llegada(data: dict) -> str:
    arrival = data["arrival"]
    lines = [arrival["rule"], "", "| Caso | n | mín. | p10 | mediana | p90 | máx. | ≤ 1 | ≤ 5 | ≤ 10 | ≤ 20 | > 20 |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for case in CASES:
        row = arrival["summary"][case]
        bins = row["bins"]
        lines.append(f"| {CASE_ES[case]} | {row['n']} | {_n(row['min'], 1)} | {_n(row['q10'], 1)} | "
                     f"{_n(row['median'], 1)} | {_n(row['q90'], 1)} | {_n(row['max'], 1)} | "
                     + " | ".join(str(bins.get(k, 0)) for k in ("<= 1", "<= 5", "<= 10", "<= 20", "> 20")) + " |")
    lines += ["", f"Desajuste en lpm (predicha − registrada). Rechazos analíticos: {arrival['analytic_rejections']}. Con "
                  "ganancias comunes y los mismos niveles de llegada, la predicción es idéntica para ambos casos: "
                  f"{_yes(arrival['identical_prediction_for_both_cases'])}. El menor «peor desajuste de los dos casos» "
                  f"sobre la superficie es {_n(arrival['best_joint_worst_mismatch_shared_intrinsic'], 1)} lpm con la "
                  f"misma intrínseca y {_n(arrival['best_joint_worst_mismatch_case_intrinsic'], 1)} lpm si la "
                  "intrínseca puede diferir por caso: sólo el valor, no se registra qué punto lo da ni se elige "
                  "ninguno.", "", "Descomposición a la intrínseca media, en el ancla de las ganancias y del techo, por par "
                  "de llegada (deuda, entrega):", "",
              "| Caso | Par | D0 | señal | aguda | deuda | presión + otros | saturado | predicha | desajuste |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    anchor = data["design"]["anchor"]
    for case in CASES:
        for pair in data["design"]["support"]["pairs"]:
            key = f"midpoint|{pair['debt']}|{pair['delivery']}|{anchor['acute']!r}|{anchor['debt']!r}|{anchor['ceiling']:g}"
            row = arrival["table"][case][key]
            lines.append(f"| {CASE_ES[case]} | {LEVEL_ES[pair['debt']]} / {LEVEL_ES[pair['delivery']]} | "
                         f"{_n(row['D0'], 0)} | {_n(row['x0'], 2)} | {_n(row['acute_bpm'], 1)} | {_n(row['debt_bpm'], 1)} |"
                         f" {_n(_clean(row['pressure_and_other_unconstrained_bpm'], 1), 1)} | "
                         f"{_n(row['saturated_bpm'], 1)} | {_n(row['predicted'], 1)} | {_n(row['mismatch'], 1)} |")
    return "\n".join(lines)


def _row(point) -> str:
    return " | ".join(_n(_clean(point[name], digits), digits) if point.get(name) is not None else "—"
                      for name, _, digits in FIELDS)


def render_trayectorias(data: dict) -> str:
    lines = [data["scan_rule"], "", "En el ancla; aguda y deuda sin saturar, y su suma saturada (lpm). FC = intrínseca "
             "+ saturado. Hemostasia en el minuto 60 de L3.", ""]
    for name, block in data["trajectories"].items():
        lines += [f"### {name}: {block['title']}", ""]
        for case in CASES:
            lines += [f"**{CASE_ES[case]}**", "", "| Rep. | Min | " + " | ".join(label for _, label, _ in FIELDS) + " |",
                      "|---|---|" + "---|" * len(FIELDS)]
            for tag in TAGS:
                table = block["cases"][case][tag]
                for minute in block["minutes"]:
                    if str(minute) in table:
                        lines.append(f"| {tag} | {minute} | {_row(table[str(minute)])} |")
            lines.append("")
    return "\n".join(lines)


def render_sondas(data: dict) -> str:
    probes = data["probes"]
    lines = ["| Caso | Sonda | Se cumple |", "|---|---|---|"]
    for case in CASES:
        p = probes[case]
        for key, label in (("inv1_deficit", "más déficit (Hb menor), todo lo demás fijo"),
                           ("inv2_debt", "más D, todo lo demás fijo"), ("inv3_tau_d", "τ_D con D fija"),
                           ("inv4_resolves", "sin déficit, sin contribución aguda"),
                           ("inv12_rhythm", "ritmo: marcapasos y AESP")):
            lines.append(f"| {CASE_ES[case]} | {label} | {_yes(p[key]['holds'])} |")
        changes = p["inv8_9_through_physiology"]
        lines.append(f"| {CASE_ES[case]} | cristaloide 500 mL con bomba 1,0 / 0,7 (ΔFC a 30 min) | "
                     f"{' / '.join(_n(v, 1) for v in changes['crystalloid'])} lpm |")
        lines.append(f"| {CASE_ES[case]} | 1 U de GR con bomba 1,0 / 0,7 (ΔFC a 30 min) | "
                     f"{' / '.join(_n(v, 1) for v in changes['red_cells'])} lpm |")
    ns = probes["non_sinus_and_beta"]
    lines += ["", f"El cristaloide y los GR actúan por la fisiología: {_yes(probes['inv8_crystalloid']['holds'])} / "
                  f"{_yes(probes['inv9_red_cells']['holds'])}. Escala de D: FC igual con D × c y ganancia / c "
                  f"{_yes(probes['d_scale']['holds'])} (brecha máx. "
                  f"{', '.join(_g(r['max_gap_bpm']) for r in probes['d_scale']['rows'])} lpm). La FC registrada no llega "
                  f"a la dinámica: {_yes(probes['authored_hr_reaches_no_dynamics']['holds'])}. Llegada no sinusal o con "
                  f"betabloqueo completo y deuda (TD-93(5)): {ns['classification']}, {ns['status']}; afecta a GI: "
                  f"{_yes(ns['affects_gi'])}."]
    return "\n".join(lines)


def render_saturacion(data: dict) -> str:
    sat = data["saturation"]
    lines = ["| Techo · intrínseca | Reserva | Máx. (impulso 20) | Monótona | Sin saltos | Pendiente en 0 | Con impulso 2 "
             "(lineal 50) |", "|---|---|---|---|---|---|---|"]
    for key, row in sat["curves"].items():
        ceiling, level = key.split("|")
        lines.append(f"| {ceiling} · {LEVEL_ES[level]} | {_n(row['reserve'], 0)} | {_n(row['max_increment'], 2)} | "
                     f"{_yes(row['monotone'])} | {_yes(row['lipschitz'])} | {_n(row['slope_at_zero'], 4)} | "
                     f"{_n(row['at_drive_2'], 1)} |")
    run_ = sat["extreme_run"]
    lines += ["", f"H6, corrida extrema (57m, intrínseca 60, deuda 60, entrega inferior, ganancias en su máximo, techo "
                  f"{_n(run_['ceiling'], 0)}, bomba cayendo {run_['minutes']} min): FC "
                  f"{' → '.join(_n(v, 1) for v in run_['hr_0_50_end'])}, máxima {_n(run_['max_hr'], 2)}, mayor cambio "
                  f"por minuto {_n(run_['largest_minute_change'], 2)} lpm; bajo el techo: {_yes(run_['below_ceiling'])}."
                  f" Se cumple: {_yes(sat['holds'])}."]
    return "\n".join(lines)


def render_invariantes(data: dict) -> str:
    inv = data["invariants"]
    lines = ["| # | Dirección | Resultado |", "|---|---|---|"]
    lines += [f"| {k} | {text} | {'PASA' if inv['results'][str(k)] else 'FALLA'} |"
              for k, text in sorted(((int(k), v) for k, v in inv["statements"].items()))]
    lines += ["", f"Corridas L3 con T*: {inv['l3_runs']}; con deuda positiva y D(T*) > 0: {inv['delayed_runs']}; menor "
                  f"margen sobre la intrínseca un minuto después de la hemostasia: "
                  f"{_n(inv['min_margin_after_haemostasis_bpm'], 2)} lpm. {hk.FLAG_POLICY}", "",
              "| Bandera estructural | Corridas |", "|---|---|"]
    lines += [f"| {name} | {count} |" for name, count in inv["flags"].items()]
    return "\n".join(lines)


def render_superficie(data: dict) -> str:
    surface = data["decision_surface"]
    acute_scan, debt_scan = list(data["design"]["acute"]["points"]) + [0.0], list(data["design"]["debt"]["points"]) + [0.0]
    lines = [f"{surface['note']}. Intrínseca media y techo {_n(data['design']['anchor']['ceiling'], 0)}; cada celda: FC de "
             "LOW / MID / HIGH (lpm); filas: ganancia aguda; columnas: ganancia de deuda.", ""]
    for case in CASES:
        for name in ("arrival", "untreated_120", "crystalloid_120", "after_haemostasis_90", "restored_adequacy_120"):
            scenario, minute = surface["landmarks"][name]
            plane = surface["table"][case][name]["plane"]
            lines += [f"**{CASE_ES[case]} · {name} ({scenario}, {minute})**", "",
                      "| aguda \\ deuda | " + " | ".join(_g(g) for g in debt_scan) + " |",
                      "|---|" + "---|" * len(debt_scan)]
            for acute in acute_scan:
                cells = [" / ".join(_n(plane[f"{acute!r}|{g!r}"][tag], 0) for tag in TAGS) for g in debt_scan]
                lines.append(f"| {_g(acute)} | " + " | ".join(cells) + " |")
            lines.append("")
        lines += [f"**{CASE_ES[case]} · techo e intrínseca en el ancla** (FC de LOW / MID / HIGH)", "",
                  "| Hito | " + " | ".join(f"techo {c}" for c in ("150", "175", "200")) + " | "
                  + " | ".join(f"intr. {LEVEL_ES[l]}" for l in hk.LEVELS) + " |", "|---|" + "---|" * 6]
        for name in surface["landmarks"]:
            cell = surface["table"][case][name]
            lines.append(f"| {name} | " + " | ".join(" / ".join(_n(cell["ceiling"][c][t], 0) for t in TAGS)
                                                     for c in ("150", "175", "200")) + " | "
                         + " | ".join(" / ".join(_n(cell["intrinsic"][l][t], 0) for t in TAGS) for l in hk.LEVELS) + " |")
        lines.append("")
    return "\n".join(lines)


def render_presion(data: dict) -> str:
    p = data["pressure"]
    return (f"Minutos leídos en el ancla: {p['minutes']}. Aguda y presión positivas a la vez: {p['both_positive']}; "
            f"déficit con presión sobre la de llegada (la presión descarga el impulso): "
            f"{p['deficit_with_pressure_above_arrival']}; presión sin déficit: {p['pressure_without_deficit']}; déficit "
            f"sin impulso por presión: {p['deficit_without_pressure_drive']}; correlación de las dos contribuciones: "
            f"{_g(p['correlation'])}. Relativa a la llegada: {_yes(p['delta_from_arrival'])}; dependencia circular: "
            f"{_yes(p['circular_dependency'])}. Clasificación: **{p['classification']}**. {p['why']}")


def render_identificabilidad(data: dict) -> str:
    ident = data["identifiability"]
    lines = ["| Compuesto observable | Forma |", "|---|---|"]
    lines += [f"| {name} | {text} |" for name, text in ident["composites"].items()]
    lines += ["", "| Parámetro latente | Estado | Soporte | Nota |", "|---|---|---|---|"]
    for name, row in ident["dimensions"].items():
        lines.append(f"| {name} | {row['status']} | {row['support']} | {row.get('note', '')} |")
    return "\n".join(lines)


def render_fr(data: dict) -> str:
    rr = data["rr"]
    return (f"¿La FR lee la FC? {_yes(rr['rr_reads_hr'])}. FR, D y lactato idénticos entre todos los parámetros de FC de "
            f"las recorridas de validación: {_yes(rr['rr_d_lactate_equal_across_hr_parameters'])}. D y lactato idénticos "
            f"al registro P2I-2AD: {_yes(rr['d_lactate_unchanged_from_p2i2ad'])}. ¿Cambia la FR? "
            f"{_yes(rr['changes_rr'])}. FR calibrada: {_yes(rr['calibrated'])}.")


def render_legado(data: dict) -> str:
    legacy = data["legacy_reference"]
    lines = [legacy["rule"], "", "| Caso | Escenario | " + " | ".join(str(m) for m in hk.TIMES) + " |",
             "|---|---|" + "---|" * len(hk.TIMES)]
    for key, row in legacy["beside"].items():
        case, scenario = key.split("|")
        cells = [" / ".join(_n(row[str(m)]["core_at_anchor"][t], 0) for t in TAGS)
                 + f" ({_n(row[str(m)]['legacy'], 0) if row[str(m)]['legacy'] is not None else '—'})" for m in hk.TIMES]
        lines.append(f"| {CASE_ES[case]} | {scenario} | " + " | ".join(cells) + " |")
    lines += ["", "Cada celda: núcleo en el ancla para LOW / MID / HIGH y, entre paréntesis, el motor de familias. Sólo "
                  "referencia."]
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    verdict = data["verdict"]
    lines = [f"**{verdict['verdict']}**\n", "| Comprobación | Resultado |", "|---|---|"]
    lines += [f"| {CHECKS_ES[name]} | {_yes(verdict['checks'][name])} |" for name in CHECKS_ES
              if name in verdict["checks"]]
    lines += ["", f"Regla congelada: {verdict['rule']}"]
    return "\n".join(lines)


def render_siguiente(data: dict) -> str:
    design = data["verdict"].get("next_design")
    if not design:
        return "Ninguno: el veredicto no es READY."
    return "\n".join([f"Estado: **{design['status']}** (preparado, no ejecutado).", "", "Observables:", ""]
                     + [f"- {item}" for item in design["observables"]] + ["", "Lo que debe aportar la docencia:", ""]
                     + [f"- {item}" for item in design["faculty_inputs"]] + ["", f"Método: {design['method']}"])


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return (f"Corridas completas de representantes: {e['representative_runs']}; reejecuciones de validación: "
            f"{e['validation_full_reruns']}; series posprocesadas: {e['post_processed_series']}; descomposiciones de "
            f"llegada analíticas: {e['arrival_decompositions_analytic']} (rechazos analíticos: "
            f"{e['analytic_rejections']}); simulaciones evitadas: {e['simulations_avoided']}; barrido cartesiano: "
            f"{_yes(e['cartesian_sweep'])}.")


RENDERERS = {"decisiones": render_decisiones, "resto": render_resto, "estructura": render_estructura,
             "candidatos": render_candidatos, "llegada": render_llegada, "trayectorias": render_trayectorias,
             "sondas": render_sondas, "saturacion": render_saturacion, "invariantes": render_invariantes,
             "superficie": render_superficie, "presion": render_presion, "identificabilidad": render_identificabilidad,
             "fr": render_fr, "legado": render_legado, "veredicto": render_veredicto, "siguiente": render_siguiente,
             "eficiencia": render_eficiencia}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the HR-shock JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
