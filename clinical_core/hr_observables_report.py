"""P2I-2AJ report: the generated blocks of docs/revision/P2I2AJ_PODA_SEVERIDAD_Y_OBSERVABLES_FC.md.

    python -m clinical_core.hr_observables_report --write <document> --data <the HR observables JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict, applies no envelope and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import hr_observables as ho
from .blood_filter_report import _n
from .lactate_rebuild_report import CASE_ES, CASES, LEVEL_ES

NAMES = ("decisiones", "semantica", "verdad", "reutilizacion", "demanda", "superficie", "identificabilidad",
         "observables", "validacion", "trayectorias", "fluido", "envolventes", "veredicto", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FACULTY_ES = {"decided": "fecha", "case_truth": "verdad del caso (72f)", "retained": "soporte retenido",
              "demand": "demanda", "intrinsic": "intrínseca", "hr": "FC", "scope": "alcance"}
CHECKS_ES = {"case_truth_compatible": "el par retenido es compatible con la verdad del caso",
             "lactate_rows_certified": "sus filas de D y lactato siguen certificadas (reutilización exacta)",
             "joint_arrival": "al menos un candidato conjunto compatible con la llegada",
             "common_gains": "ganancias y techo comunes",
             "intrinsic_patient_specific": "intrínseca por paciente, sin aprobar (tres niveles por caso)",
             "pressure_deferred": "presión aplazada", "no_regression": "sin regresión de D y lactato",
             "trajectories_available": "distribuciones de trayectoria disponibles y validadas"}
SEMANTIC_ES = {"no_hr": "ninguna FC en la definición", "no_legacy": "ningún valor heredado",
               "no_pressure_hr_term": "ningún término de presión ni simpático",
               "in_p2i2ai_inventory": "en el inventario certificado de P2I-2AI",
               "p2i2ai_admissible": "admisible en P2I-2AI", "p2i2ai_lactate_compatible": "LACTATE_COMPATIBLE en P2I-2AI"}
LATENT_ES = {"intrinsic_57m": "intrínseca 57m", "intrinsic_72f": "intrínseca 72f", "acute": "ganancia aguda",
             "debt": "ganancia de deuda", "ceiling": "techo sinusal total"}
OBSERVABLE_ES = {"intrinsic": "intrínseca (lpm)", "x0": "señal aguda x0", "D0": "D0",
                 "acute_bpm": "incremento agudo (lpm)", "debt_bpm": "incremento por deuda (lpm)",
                 "sympathetic_bpm": "incremento simpático total (lpm)", "reserve_utilization": "uso de la reserva",
                 "predicted": "FC de llegada predicha"}
READING_ES = {
    "H1.hr_30": "H1 sin tratamiento: FC a los 30", "H1.hr_60": "H1: FC a los 60", "H1.hr_120": "H1: FC a los 120",
    "H1.delta_30": "H1: cambio desde la llegada a los 30", "H1.delta_60": "H1: cambio a los 60",
    "H1.delta_120": "H1: cambio a los 120", "H1.max": "H1: FC máxima",
    "H2.early_change": "H2 cristaloide: cambio al terminar la infusión (min 20)", "H2.nadir": "H2: FC mínima",
    "H2.nadir_minute": "H2: minuto de la FC mínima", "H2.hr_60": "H2: FC a los 60", "H2.hr_120": "H2: FC a los 120",
    "H2.rebound": "H2: rebote (FC a los 120 menos la mínima)",
    "H3.before_unit_1": "H3 GR: FC antes de la unidad 1", "H3.after_unit_1": "H3: FC tras la unidad 1",
    "H3.delta_unit_1": "H3: cambio con la unidad 1", "H3.after_unit_2": "H3: FC tras la unidad 2",
    "H3.delta_unit_2": "H3: cambio adicional con la unidad 2", "H3.unit_1_minute": "H3: minuto en que termina la unidad 1",
    "H3.unit_2_minute": "H3: minuto en que termina la unidad 2",
    "H4.hr_60": "H4 manejo definitivo: FC a los 60", "H4.hr_90": "H4: FC a los 90", "H4.hr_120": "H4: FC a los 120",
    "H4.adequacy_onset": "H4: minuto de adecuación sostenida", "H4.change_after_adequacy": "H4: cambio tras la adecuación",
    "H4.residual_above_intrinsic_120": "H4: taquicardia residual sobre la intrínseca a los 120",
    "H6.max_hr": "H6: FC máxima (L1, L2, L3)", "H6.ceiling": "H6: techo", "H6.distance_to_ceiling": "H6: distancia al techo",
    "H6.reserve_utilization": "H6: uso de la reserva (máxima − intrínseca) / (techo − intrínseca)",
}
FLUID_ES = {"diverges_at": "primer minuto con FC distinta", "diverges_by_1_bpm_at": "primer minuto con más de 1 lpm",
            "largest_difference": "mayor diferencia (lpm)", "largest_at": "minuto de la mayor diferencia",
            "prbc_minus_fluid_at_largest": "GR − cristaloide en ese minuto (lpm)",
            "acute_signal_diverges_at": "primer minuto con señal aguda distinta",
            "debt_diverges_at": "primer minuto con D distinta"}
STATUS_ES = {"CURRENTLY_COMPATIBLE": "CURRENTLY_COMPATIBLE", "CURRENTLY_INCOMPATIBLE": "CURRENTLY_INCOMPATIBLE"}


def _p(pair) -> str:
    return " / ".join(LEVEL_ES[x] for x in pair)


def _yes(value) -> str:
    return "sí" if value else "no"


def _g(value) -> str:
    if value is None:
        return "—"
    return "0" if value == 0 else f"{value:.3g}".replace(".", ",")


def _f(value) -> str:
    return f"{float(value):g}".replace(".", ",")


def _d(value) -> str:
    return f"{float(value):.1f}".replace(".", ",")


def _by_demand(counts: dict) -> str:
    return "; ".join(f"{_d(k)}: {v}" for k, v in sorted(counts.items(), key=lambda kv: float(kv[0])))


def _s(item, digits: int = 1) -> str:
    if not item:
        return "—"
    return " / ".join(_n(item[k], digits) for k in ("low", "median", "high"))


def _demands(data: dict) -> list[str]:
    return sorted(data["trajectories"]["by_demand"], key=float)


def render_decisiones(data: dict) -> str:
    lines = [f"Congelamiento: `{data['freeze_digest']}` (una prueba lo fija). Registro de partida: P2I-2AI "
             f"`{data['record']}`.\n", "| Decisión docente | Texto registrado |", "|---|---|"]
    lines += [f"| {FACULTY_ES[name]} | {data['faculty'][name]} |" for name in FACULTY_ES]
    return "\n".join(lines)


def render_semantica(data: dict) -> str:
    sem = data["pair_semantics"]
    lines = ["| Caso | Par (deuda / entrega) | Etiqueta | D0 | entrega | reanclada (÷2,5) | señal aguda x0 | "
             "en el inventario P2I-2AI |", "|---|---|---|---|---|---|---|---|"]
    for case in CASES:
        item = sem[case]
        lines.append(f"| {CASE_ES[case]} | {_p(item['pair'])} | {item['label']} | {_n(item['D0'], 0)} | "
                     f"{_n(item['delivery'], 2)} | {_n(item['delivery_reanchored'], 2)} | {_n(item['x0'], 2)} | "
                     f"{_yes(item['in_p2i2ai_inventory'])} |")
    reads = sem["band_reads"]
    lines += ["", "| Banda | Valores (inferior / medio / superior) | Variables del caso que cita | Valores literales | "
                  "Lee un valor registrado |", "|---|---|---|---|---|"]
    for name, band_key in (("arrival_oxygen_debt", "debt_band"), ("arrival_delivery_ratio", "delivery_band")):
        band = sem[CASES[0]][band_key]
        lines.append(f"| `{name}` | {_g(band['lower'])} / {_g(band['midpoint'])} / {_g(band['upper'])} "
                     f"({band['units']}) | {', '.join(reads[name]['cited_items'])} | {_yes(reads[name]['literal_values'])} "
                     f"| {_yes(reads[name]['reads_authored_value'])} |")
    lines += ["", "| Comprobación | Resultado |", "|---|---|"]
    lines += [f"| {SEMANTIC_ES[k]} | {_yes(v)} |" for k, v in sem["checks"].items()]
    lines += ["", f"Origen de los valores: {sem[CASES[0]]['values_from']}."]
    return "\n".join(lines)


def render_verdad(data: dict) -> str:
    lines = ["| 57m | 72f | D0 de 72f | entrega de 72f | Estado | Motivo |", "|---|---|---|---|---|---|"]
    for item in data["case_truth"]:
        lines.append(f"| {_p(item['pair_57m'])} | {_p(item['pair_72f'])} | {_n(item['72f_D0'], 0)} | "
                     f"{_n(item['72f_delivery'], 2)} | **{item['status']}** | {item['reason'] or '—'} |")
    lines += ["", f"Soporte retenido: 57m ({_p(data['retained'][0])}) · 72f ({_p(data['retained'][1])}), "
                  f"**{data['retained_status']}**.", "", f"Regla congelada: {ho.CASE_TRUTH_RULE}"]
    return "\n".join(lines)


def render_reutilizacion(data: dict) -> str:
    r = data["reuse"]
    dep = r["dependency"]
    return "\n".join([
        f"- Par: `{r['pair']}`; registro P2I-2AI con su congelamiento `{r['record_freeze_digest']}`.",
        f"- Dependencias ejecutables (todo `clinical_core` salvo este paquete y los dos archivos que sólo cambian una "
        f"tupla de exclusión): `{dep['digest']}`, igual al de P2I-2AI (`{dep['at_p2i2ai']}`): **{_yes(dep['equal'])}**.",
        f"- Digest de las unidades reconstruidas con demanda 1,0: `{r['units_digest']}` (registrado "
        f"`{r['recorded_units_digest']}`).",
        f"- Sobrevivientes por demanda: {_by_demand(r['survivors'])} (registrados "
        f"{_by_demand(r['recorded_survivors'])}).",
        f"- Reutilización válida: **{_yes(r['equal'])}**. Se reutilizan del registro, sin recalcular, la estadística "
        f"({', '.join(f'{k} {v}' for k, v in r['reused_from_record']['statistics'].items())}) y los representantes "
        f"LOW / MID / HIGH.", "", f"Regla: {ho.REUSE_RULE}"])


def render_demanda(data: dict) -> str:
    d = data["demand"]
    lines = ["| Demanda | Candidatos | Sobrevivientes | Estado | Fallo dominante (primer fallo, peso) |",
             "|---|---|---|---|---|"]
    for key in ("0.9", "1", "1.1"):
        item = d[key]
        lines.append(f"| {_d(key)} | {item['candidates']} | {item['survivors']} | **{item['status']}** | "
                     f"{item['dominant_failure']} ({item['dominant_failure_weight']}) |")
    lines += ["", "Por etapa (primer fallo en el orden de P2I-2AD; dentro de cada restricción, 57m antes que 72f):", "",
              "| Demanda | Etapa | Entran | Rechazados | Quedan | Primeros fallos |", "|---|---|---|---|---|---|"]
    for key in ("0.9", "1", "1.1"):
        for stage in d[key]["stages"]:
            first = "; ".join(f"{name} {weight}" for name, weight in stage["first_failure"].items()) or "—"
            lines.append(f"| {_d(key)} | {stage['scenario']} | {stage['entering']} | {stage['rejected']} | "
                         f"{stage['survivors']} | {first} |")
    lines += ["", f"Robustos a las tres demandas: {d['robust_across_demand']} (diagnóstico, nunca filtro).", "",
              f"Regla: {d['rule']}"]
    return "\n".join(lines)


def render_superficie(data: dict) -> str:
    lines = []
    for key, s in sorted(data["hr_surfaces"].items(), key=lambda kv: float(kv[0])):
        sup = s["support"]
        dec = s["compatible_decompositions"]
        lines += [f"**Demanda {_d(key)}.** Descomposiciones: {s['decompositions']}; candidatos conjuntos: "
                  f"{s['joint_candidates']}; compatibles con 57m: {s['compatible_57m']} (descomposiciones "
                  f"{dec[CASES[0]]}); con 72f: {s['compatible_72f']} (descomposiciones {dec[CASES[1]]}); "
                  f"**conjuntamente compatibles: {s['joint']}** ({s['distinct_predictions']} pares de FC predicha "
                  "distintos).", "",
                  "| intrínseca 57m \\ 72f | inferior (60) | medio (80) | superior (100) |", "|---|---|---|---|"]
        for a in ("lower", "midpoint", "upper"):
            lines.append(f"| {LEVEL_ES[a]} | " + " | ".join(str(sup["intrinsic_pairs"][f"{a}|{b}"])
                                                           for b in ("lower", "midpoint", "upper")) + " |")
        lines += ["", "| Dimensión | Apoyo por valor |", "|---|---|",
                  "| ganancia aguda | " + "; ".join(f"{_g(float(k))}: {v}" for k, v in
                                                     sorted(sup["acute"].items(), key=lambda kv: float(kv[0]))) + " |",
                  "| ganancia de deuda | " + "; ".join(f"{_g(float(k))}: {v}" for k, v in
                                                        sorted(sup["debt"].items(), key=lambda kv: float(kv[0]))) + " |",
                  "| techo | " + "; ".join(f"{k}: {v}" for k, v in
                                           sorted(sup["ceiling"].items(), key=lambda kv: float(kv[0]))) + " |", "",
                  "| Intrínsecas 57m / 72f | Ganancia aguda | Ganancia de deuda | Techo | FC predicha 57m / 72f |",
                  "|---|---|---|---|---|"]
        for x in s["survivors"]:
            lines.append(f"| {_p(x['intrinsic'])} | {_g(x['acute'])} | {_g(x['debt'])} | {_f(x['ceiling'])} | "
                         f"{_n(x['predicted'][0], 1)} / {_n(x['predicted'][1], 1)} |")
        lines.append("")
    lines.append(f"Regla: {ho.HR_RULE}")
    return "\n".join(lines)


def render_identificabilidad(data: dict) -> str:
    ident = data["identifiability"]
    keys = sorted((k for k in ident if k != "union"), key=float) + ["union"]
    header = " | ".join("unión" if k == "union" else f"demanda {_d(k)}" for k in keys)
    lines = [f"| Latente | {header} |", "|---|" + "---|" * len(keys)]
    for name in ho.LATENTS:
        cells = []
        for k in keys:
            item = ident[k][name]
            values = ", ".join(LEVEL_ES.get(v, v) if isinstance(v, str) else _g(v) for v in item["surviving"])
            cells.append(f"**{item['status']}** ({values or '—'})")
        lines.append(f"| {LATENT_ES[name]} | " + " | ".join(cells) + " |")
    lines += ["", f"Observaciones: {', '.join(ident['union']['observations'])}. Estructural: "
                  f"{ho.STRUCTURAL['debt']}.", "", f"Regla: {ho.IDENTIFIABILITY_RULE}"]
    return "\n".join(lines)


def render_observables(data: dict) -> str:
    lines = ["Mínimo – máximo sobre los candidatos conjuntos de cada demanda.", "",
             "| Observable de llegada | " + " | ".join(f"{CASE_ES[c]}, demanda {_d(k)}" for k in
                                                      sorted(data["observables"], key=float) for c in CASES) + " |",
             "|---|" + "---|" * (len(CASES) * len(data["observables"]))]
    for name in ho.OBSERVABLES:
        cells = []
        for k in sorted(data["observables"], key=float):
            for c in CASES:
                item = data["observables"][k][c][name]
                cells.append("—" if item is None else f"{_n(item['min'], 2)} – {_n(item['max'], 2)}")
        lines.append(f"| {OBSERVABLE_ES[name]} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_validacion(data: dict) -> str:
    lines = ["| Demanda | Corridas completas | Comprobaciones | Exacta |", "|---|---|---|---|"]
    for k, v in sorted(data["validation"].items(), key=lambda kv: float(kv[0])):
        checks = ", ".join(f"{name} {_yes(ok)}" for name, ok in v["checks"].items())
        lines.append(f"| {_d(k)} | {v['full_runs']} | {checks} | **{_yes(v['exact'])}** |")
    lines += ["", f"Regla: {ho.TRAJECTORY_RULE}"]
    return "\n".join(lines)


def render_trayectorias(data: dict) -> str:
    lines = ["Cada celda: LOW / mediana / HIGH sobre (sobreviviente de lactato × candidato conjunto), en lpm salvo "
             "indicación. Sin envolvente ni filtro.", ""]
    for k in _demands(data):
        t = data["trajectories"]["by_demand"][k]
        lines += [f"**Demanda {_d(k)}** — {t['lactate_survivors']} sobrevivientes de lactato × {t['joint_survivors']} "
                  f"candidatos conjuntos = {t['readings_per_case']} lecturas por caso.", "",
                  "| Lectura | 57m | 72f |", "|---|---|---|"]
        for name, label in READING_ES.items():
            digits = 2 if name.endswith("utilization") else (0 if name.endswith("minute") or name.endswith("onset")
                                                              else 1)
            lines.append(f"| {label} | {_s(t['distributions'][CASES[0]].get(name), digits)} | "
                         f"{_s(t['distributions'][CASES[1]].get(name), digits)} |")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_fluido(data: dict) -> str:
    lines = ["| Lectura (72f, L2 cristaloide frente a L3 GR) | " + " | ".join(f"demanda {_d(k)}" for k in _demands(data))
             + " |", "|---|" + "---|" * len(_demands(data))]
    for name, label in FLUID_ES.items():
        digits = 1 if "difference" in name or "minus" in name else 0
        lines.append(f"| {label} | " + " | ".join(_s(data["trajectories"]["by_demand"][k]["fluid_vs_prbc_72f"][name],
                                                     digits) for k in _demands(data)) + " |")
    lines.append("| pares sin ninguna divergencia | " + " | ".join(
        str(data["trajectories"]["by_demand"][k]["fluid_vs_prbc_72f"]["never_diverge"]) for k in _demands(data)) + " |")
    lines.append("| primera entrada que diverge (aguda / deuda / ninguna) | " + " | ".join(
        " / ".join(str(data["trajectories"]["by_demand"][k]["fluid_vs_prbc_72f"]["first_input"][kind])
                   for kind in ("acute", "debt", "none")) for k in _demands(data)) + " |")
    lines += ["", f"Regla: {ho.FLUID_PRBC_RULE}"]
    return "\n".join(lines)


def render_envolventes(data: dict) -> str:
    env = data["envelopes"]
    if not env:
        return "No se prepararon: no hay trayectorias."
    lines = ["| | Magnitud | Propuesta (no aplicada) | Base | Interpretación |", "|---|---|---|---|---|"]
    for key in "ABCDEFG":
        e = env[key]
        lines.append(f"| {key} | {e['quantity']} | {e['proposal']} | {e['basis']} | {e['interpretation']} |")
    lines += ["", "Resultado actual (LOW / mediana / HIGH, lpm), por demanda y por la intrínseca del caso:", "",
              "| | Caso | Demanda | Todos | Intrínseca 60 | Intrínseca 80 | Intrínseca 100 |",
              "|---|---|---|---|---|---|---|"]
    for key in "ABCDEFG":
        e = env[key]
        for demand in sorted(e["current"], key=float):
            for case in e["cases"]:
                item = e["current"][demand][case]
                levels = [_s(item["by_intrinsic"].get(level)) for level in ("lower", "midpoint", "upper")]
                lines.append(f"| {key} | {CASE_ES[case]} | {_d(demand)} | {_s(item['all'])} | " + " | ".join(levels)
                             + " |")
    lines += ["", f"Regla: {env['rule']}"]
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    lines = [f"**{v['verdict']}**\n", "| Comprobación | Resultado |", "|---|---|"]
    lines += [f"| {CHECKS_ES[name]} | {_yes(v['checks'][name])} |" for name in CHECKS_ES if name in v["checks"]]
    lines += ["", f"Aprobado: {_yes(v['approved'])}.", "", f"Regla congelada: {v['rule']}"]
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    runs = "; ".join(f"demanda {_d(k)}: {v} (sin compartir L1 y L3: {e['trajectory_full_runs_without_sharing'][k]})"
                     for k, v in sorted(e["trajectory_full_runs"].items(), key=lambda kv: float(kv[0])))
    return (f"Rechazos por verdad del caso: {e['case_truth_rejections']} par de casos ({e['case_truth_rejected_lactate_survivors']} "
            f"sobrevivientes de lactato que no se simulan); trayectorias hemodinámicas: {e['haemodynamic_trajectories']}; "
            f"puntos de lactato por caso: {e['lactate_side_points_per_case']} de {e['of_lactate_side_points_per_case_in_p2i2ai']}; "
            f"descomposiciones de llegada analíticas: {e['arrival_decompositions']}; corridas de validación: "
            f"{e['validation_full_runs']}; corridas de trayectoria: {runs}; lecturas de FC posprocesadas: "
            f"{sum(e['hr_post_processed_readings'].values())}; barrido cartesiano: {_yes(e['cartesian_sweep'])}; motor "
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
    parser.add_argument("--data", type=Path, required=True, help="the HR observables JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
