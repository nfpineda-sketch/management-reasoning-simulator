"""P2J-2 report: the generated blocks of docs/revision/P2J2_TONO_VASCULAR_DINAMICO.md.

    python -m clinical_core.vascular_tone_report --write <document> --data <the vascular-tone JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import vascular_tone as vt
from .lactate_rebuild_report import CASE_ES

NAMES = ("decisiones", "tono", "tiempo", "superficie", "sondas", "llegada", "trayectorias", "detalle", "sin_tratamiento",
         "definitivo", "intercambio", "lactato", "fc", "conciencia", "envolventes", "identificabilidad", "barorreflejo",
         "validacion", "veredicto", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FACULTY_ES = {"decided": "fecha", "structure": "estructura de P2J-1", "tone": "respuesta de tono", "semantics": "semántica",
              "no_pressure_driver": "sin la presión como impulsor", "no_memory": "sin memoria de D",
              "timing": "temporalidad", "loop": "lazo", "range": "rango", "afterload": "poscarga", "arrival": "llegada",
              "demand": "demanda", "hr": "FC", "lactate": "lactato", "scope": "alcance"}
SCENARIO_ES = {"P1": "P1 · sin tratamiento (L1)", "P2": "P2 · 2 L de cristaloide, sangrado activo (L2)",
               "P3": "P3 · IBP y 2 U de GR sin hemostasia (L3 sin la endoscopia)",
               "P4": "P4 · manejo definitivo: IBP, 2 U de GR y hemostasia a los 60 (L3)"}
CHECKS_ES = {"tone_semantics_coherent": "semántica del tono coherente (sondas 1, 2 y 6; T = 1 en los minutos 0 y 1; "
                                        "la ganancia 0 reproduce P2J-1)",
             "feedback_deterministic_stable": "retroalimentación determinista y estable (sonda 5, sin rechazo de "
                                              "simulación, repeticiones idénticas)",
             "no_pathological_loop": "sin lazo patológico presión / gasto (ningún UNSTABLE_FEEDBACK)",
             "pressure_continuous_nonnegative": "presión continua y no negativa",
             "zero_output_consistent": "gasto cero y paro coherentes",
             "lactate_satisfiable": "restricciones de lactato satisfacibles por alguna ganancia > 0 en cada demanda",
             "distributions_available": "distribuciones de P1–P4 para ambos casos, ambas demandas y cada ganancia",
             "reconstruction_exact": "reconstrucción igual al núcleo en la muestra",
             "upstream_reproduced": "unidades de P2I-2AK reproducidas y referencia de lactato intacta a ganancia 0",
             "pressure_to_hr_deferred": "presión → FC aplazada (0 en el perfil primario)",
             "nothing_approved": "nada aprobado"}
TRADE_ES = {"REFERENCE_T_EQUALS_1": "referencia T = 1", "ANALYTIC_REJECTION": "rechazo analítico",
            "PRESSURE_SUPPORTED_WITH_STABLE_DELIVERY": "presión sostenida sin perder candidatos FD-LAC (el aporte "
                                                       "baja igual: §9)",
            "PRESSURE_SUPPORTED_AT_DELIVERY_COST": "presión sostenida con costo de aporte",
            "UNSTABLE_FEEDBACK": "retroalimentación inestable"}
SCOPE_ES = {"ALL_RETAINED_UNITS": "todas las unidades retenidas", "SAMPLE_ONLY": "sólo la muestra"}
PROBES_ES = {"1": "déficit 0 → T_abs = 1", "2": "el objetivo nunca baja al subir el déficit",
             "3": "más T con precarga, bomba y ritmo fijos baja el gasto", "4": "p = Q × T sube con T en todo el guardia",
             "5": "estado estable: T monótono, paso que se achica bajo la cota, punto fijo analítico",
             "6": "al resolverse el déficit T vuelve a T_abs = 1",
             "7": "sin pulso no hay presión; gasto 0 con pulso detiene la corrida; gasto mínimo, presión mínima",
             "8": "ninguna presión negativa; un minuto desde la llegada intacta conserva T y PAM"}
IDENT_ES = {"tone gain": "ganancia de tono", "afterload a": "poscarga a", "T trajectory": "trayectoria de T",
            "pressure / output composite": "compuesto presión / gasto"}
IDENT_WHY_ES = {
    "tone gain": "no hay presión, gasto ni resistencia registrados después de la llegada, y la presión de llegada es "
                 "exacta por construcción con cualquier ganancia (T = 1 allí): nada observado alcanza g. Sólo está "
                 "acotada por estructura (g a < 1, 1 + g ≤ 3); las envolventes A, B y F la harían "
                 "PARTIALLY_CONSTRAINED",
    "afterload a": "llega a la presión y al gasto sólo con T ≠ 1, y no se observa gasto ni resistencia; con tono "
                   "dinámico a y g actúan juntos, así que una envolvente de presión acotaría el par, no a",
    "T trajectory": "T nunca se observa; dada g, su forma la fija la señal certificada (aporte y demanda)",
    "pressure / output composite": "PAM = PAM de llegada × Q × T: en la llegada, bien acotada por anclaje (exacta por "
                                   "construcción); después, nada observado; el gasto lo fija la fisiología sanguínea "
                                   "certificada con T = 1 y sólo se mueve con el tono a través de a",
}
ENV_FIELD_ES = {"sbp": "PAS", "dbp": "PAD", "map": "PAM", "map_change": "ΔPAM", "sbp_change": "ΔPAS", "T": "T",
                "T_abs": "T_abs", "T_max": "T máx", "output_cost": "costo de gasto", "delivery_cost": "costo de aporte",
                "deficit_change": "Δ déficit", "D_change": "ΔD"}
HR_ES = {"l1_120": "L1 a los 120", "l3_60": "L3 a los 60", "l3_90": "L3 a los 90", "l3_120": "L3 a los 120",
         "benefit_1": "beneficio de la 1.ª unidad", "benefit_2": "beneficio de la 2.ª unidad"}
TONE_FIELDS = ("T", "T_abs", "T_max")


def _n(value, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}".replace("-", "−")


def _g(value) -> str:
    return f"{value:g}".replace(".", ",") if isinstance(value, float) else str(value)


def _yes(value) -> str:
    return "sí" if value else "no"


def _s(item, digits: int = 1) -> str:
    if item is None:
        return "—"
    return f"{_n(item['median'], digits)} [{_n(item['low'], digits)}–{_n(item['high'], digits)}]"


def _m(item, digits: int = 1) -> str:
    return "—" if item is None else _n(item["median"], digits)


def _pct(item) -> str:
    if item is None:
        return "—"
    return f"{_n(100 * item['median'])} % [{_n(100 * item['low'])}–{_n(100 * item['high'])}]"


def _gains(data: dict) -> list[str]:
    return [f"{g:g}" for g in data["gains"] if f"g{g:g} a0.3" in data["screen"]
            and data["screen"][f"g{g:g} a0.3"]["status"] == "ADMISSIBLE"]


def render_decisiones(data: dict) -> str:
    return "\n".join(f"- **{FACULTY_ES[k]}**: {v}" for k, v in data["faculty"].items())


def render_tono(data: dict) -> str:
    t = data["tone"]
    return "\n".join([f"- **Señal**: {t['signal']}", f"- **Tono absoluto**: {t['absolute']}",
                      f"- **Canal T**: {t['channel']}", f"- **Núcleo**: {t['core']}"])


def render_tiempo(data: dict) -> str:
    f = data["feedback"]
    return "\n".join([f"- **Temporalidad**: {data['timing']}", f"- **Clasificación del lazo**: `{f['classification']}`",
                      f"- **Lazo**: {f['loop']}", f"- **Mapa**: {f['map']}", f"- **Cota**: {f['bound']}",
                      f"- **Determinismo**: {f['determinism']}", f"- **Mismo paso**: {f['same_step']}",
                      f"- **Llegada**: {data['arrival_rule']}", f"- **Alternativa literal**: "
                                                                f"{data['literal_alternative_rule']}"])


def render_superficie(data: dict) -> str:
    lines = [f"Ganancias: {', '.join(_g(float(g)) for g in data['gains'])}; poscarga a: "
             f"{', '.join(_g(float(a)) for a in data['afterload'])} (primaria 0,3).", "", data["range_rule"], "",
             "| par (g, a) | cota g·a | estado | motivo |", "|---|---|---|---|"]
    for key, item in data["screen"].items():
        lines.append(f"| {key} | {_n(item['slope_bound'], 2)} | {item['status']} | "
                     f"{', '.join(item['reasons']) or '—'} |")
    return "\n".join(lines)


def render_sondas(data: dict) -> str:
    p = data["probes"]
    lines = ["| sonda | qué comprueba | resultado |", "|---|---|---|"]
    lines += [f"| {k} | {PROBES_ES[k]} | {_yes(v)} |" for k, v in p["checks"].items()]
    for name, base in p["bases"].items():
        worst = max(base["steady"].items(), key=lambda kv: kv[1]["largest_ratio"])
        lines.append("")
        lines.append(f"**{name}** (s0 = {_n(base['s0'], 3)}): en estado estable T sube de forma monótona hasta el punto "
                     f"fijo analítico en todos los pares; la mayor razón entre pasos sucesivos es "
                     f"{_n(worst[1]['largest_ratio'], 3)} ({worst[0]}, cota {_n(worst[1]['bound'], 3)}). Al resolverse "
                     f"el déficit, T_abs termina en 1 en todos los pares.")
    return "\n".join(lines)


def render_llegada(data: dict) -> str:
    lines = ["| caso · nivel de aporte de llegada · demanda | s0 | T_abs de llegada con g = 1 | salto que haría el canal "
             "literal en el minuto 1 (g = 1, a = 0,3) |", "|---|---|---|---|"]
    for key, s0 in data["arrival_signals"].items():
        case, level, factor = key.split()
        jump = data["literal_alternative"].get(f"{key} g1 a0.3")
        lines.append(f"| {CASE_ES[case]} · {level} · {factor} | {_n(s0, 3)} | {_n(1 + s0, 3)} | "
                     f"{'ninguno' if not jump or jump['map_factor'] == 1.0 else '×' + _n(jump['map_factor'], 3) + ' PAM'} |")
    return "\n".join(lines)


def render_trayectorias(data: dict) -> str:
    gains = _gains(data)
    lines = []
    for key, table in data["trajectories"].items():
        name, case, factor = key.split()
        lines += [f"**{SCENARIO_ES[name]} · {CASE_ES[case]} · demanda {factor[1:]}** ({table['keys']} claves). PAM "
                  "mediana por minuto; entre corchetes, el rango a los 120.", "",
                  "| g | " + " | ".join(str(m) for m in vt.TIMES) + " | rango a los 120 |",
                  "|---|" + "---|" * (len(vt.TIMES) + 1)]
        for g in gains:
            at = table["gains"][g]["at"]
            item = at["120"]["map"]
            lines.append(f"| {g} | " + " | ".join(_m(at[str(m)]["map"]) for m in vt.TIMES) +
                         f" | {_n(item['low'])}–{_n(item['high'])} |")
        state = table["interventions"]
        lines += ["", "Intervenciones (mediana): " + "; ".join(
            f"{m}: sangrado {_m(state[str(m)]['bleed'], 2)} mL/min, cristaloide {_m(state[str(m)]['crystalloid'], 0)} "
            f"mL, GR {_m(state[str(m)]['prbc'], 2)} U" for m in vt.TIMES) + ".", ""]
    return "\n".join(lines).rstrip()


def render_detalle(data: dict) -> str:
    gains = _gains(data)
    lines = ["Minuto 120, a = 0,3, mediana [rango] sobre las claves; Δ y costos contra la referencia T = 1 de la misma "
             "clave.", "", "| escenario · caso · demanda | g | T | T_abs | señal s | Q | PAS / PAD | PAM | déficit | D | "
             "lactato |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, table in data["trajectories"].items():
        name, case, factor = key.split()
        for g in gains:
            a = table["gains"][g]["at"]["120"]
            lines.append(f"| {name} · {CASE_ES[case]} · {factor[1:]} | {g} | {_s(a['T'], 2)} | {_s(a['T_abs'], 2)} | "
                         f"{_m(a['s'], 2)} | {_s(a['output'], 2)} | {_m(a['sbp'])} / {_m(a['dbp'])} | {_s(a['map'])} | "
                         f"{_m(a['deficit'], 3)} | {_m(a['D'])} | {_m(a['lactate'], 2)} |")
    return "\n".join(lines)


def _pair(data, scenario, case, factor, g, minute="120"):
    return data["trajectories"][f"{scenario} {case} x{factor}"]["gains"][g]["at"][minute]


def render_sin_tratamiento(data: dict) -> str:
    gains = _gains(data)
    lines = ["| caso · demanda | g | PAS a los 120 | PAM a los 120 | ΔPAM vs T = 1 | ΔPAS vs T = 1 | costo de Q | costo de "
             "aporte | Δ déficit | ΔD |", "|---|---|---|---|---|---|---|---|---|---|"]
    for case in vt.CASES:
        for factor in ("1", "1.1"):
            for g in gains:
                a = _pair(data, "P1", case, factor, g)
                lines.append(f"| {CASE_ES[case]} · {factor} | {g} | {_s(a['sbp'])} | {_s(a['map'])} | "
                             f"{_s(a['map_change'])} | {_s(a['sbp_change'])} | {_pct(a['output_cost'])} | "
                             f"{_pct(a['delivery_cost'])} | {_m(a['deficit_change'], 3)} | {_m(a['D_change'], 2)} |")
    return "\n".join(lines)


def render_definitivo(data: dict) -> str:
    gains = _gains(data)
    lines = ["| caso · demanda | g | T | T_abs | Q | PAS / PAD | PAM | ΔPAM vs T = 1 | PAM / PAM de llegada | parte del "
             "gasto (Q) | parte del tono (T) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for case in vt.CASES:
        for factor in ("1", "1.1"):
            arrival = _pair(data, "P4", case, factor, "0", "0")["map"]["median"]
            for g in gains:
                a = _pair(data, "P4", case, factor, g)
                q, t = a["output"]["median"], a["T"]["median"]
                lines.append(f"| {CASE_ES[case]} · {factor} | {g} | {_m(a['T'], 2)} | {_m(a['T_abs'], 2)} | "
                             f"{_m(a['output'], 2)} | {_m(a['sbp'])} / {_m(a['dbp'])} | {_m(a['map'])} | "
                             f"{_m(a['map_change'])} | ×{_n(a['map']['median'] / arrival, 2)} | ×{_n(q, 2)} | "
                             f"×{_n(t, 2)} |")
    return "\n".join(lines)


def render_intercambio(data: dict) -> str:
    lines = [data["tradeoff_rule"], "", "| par (g, a) | clasificación | candidatos perdidos (FD-LAC / adecuación) | "
             "alcance | rechazos de simulación |", "|---|---|---|---|---|"]
    for key, item in data["tradeoff"].items():
        lines.append(f"| {key} | {TRADE_ES[item['class']]} | {item.get('fd_lac_candidates_lost', '—')} | "
                     f"{SCOPE_ES.get(item.get('scope'), '—')} | {', '.join(item.get('simulation_rejections', [])) or '—'} |")
    return "\n".join(lines)


def render_lactato(data: dict) -> str:
    lines = ["| demanda | a | g | candidatos que conservan FD-LAC y adecuación L3 | de | unidades con algún candidato |",
             "|---|---|---|---|---|---|"]
    sources = [("0.3", data["fd_lac"])] + [(a[1:], v) for a, v in data["fd_lac_sample"].items()]
    for a, block in sources:
        for factor, item in block.items():
            for g, x in item["gains"].items():
                lines.append(f"| {factor} | {_g(float(a))} | {g} | {x['candidates']} | {item['reference_candidates']} | "
                             f"{x['units_kept']} de {item['units']} |")
    return "\n".join(lines)


def render_fc(data: dict) -> str:
    fields = tuple(HR_ES)
    lines = ["Diagnóstico, nunca filtro: corridas completas de la muestra (L1, L3 y los dos contrafactuales), a = 0,3, "
             "bajo las combinaciones latentes primarias del grupo de P2I-2AK en cada demanda; cambio de la FC contra "
             "g = 0 en bpm (mediana [rango]) y reglas A–F que fallarían.", "",
             "| demanda | g | caso | filas | " + " | ".join(HR_ES[k] for k in fields) + " | A–F que fallan |",
             "|---|---|---|---|" + "---|" * (len(fields) + 1)]
    largest = {}
    for factor, by_gain in data["hr"].items():
        for g, slot in by_gain.items():
            failures = ", ".join(f"{k} ({v})" for k, v in slot["failures"].items()) or "ninguna"
            for case in vt.CASES:
                cells = [_s(slot["change"].get(f"{case} {k}"), 1) for k in fields]
                lines.append(f"| {factor} | {g} | {CASE_ES[case]} | {slot['rows']} | " + " | ".join(cells) +
                             f" | {failures} |")
            changes = [c for c in slot["change"].values() if c]
            largest[(factor, g)] = max((max(abs(c["low"]), abs(c["high"])) for c in changes), default=0.0)
    lines += ["", "Mayor |cambio| de la FC en cualquier lectura y fila: " + "; ".join(
        f"demanda {f}, g {g}: {_n(v)} bpm" for (f, g), v in largest.items() if g != "0") + "."]
    return "\n".join(lines)


def render_conciencia(data: dict) -> str:
    gains = _gains(data)
    lines = ["Umbrales vigentes de PAS (80 → nivel 1, 65 → nivel 2), sin recalibrar: claves que los cruzan alguna vez "
             "y minuto mediano del primer cruce.", "",
             "| escenario · caso · demanda | " + " | ".join(f"g {g}" for g in gains) + " |",
             "|---|" + "---|" * len(gains)]
    for key, table in data["trajectories"].items():
        name, case, factor = key.split()
        cells = []
        for g in gains:
            c = table["gains"][g]["consciousness"]
            cells.append("; ".join(f"<{int(float(lv))}: {c[lv]['keys_crossing']}/{table['keys']}"
                                   + (f" (min {_m(c[lv]['first_minute'], 0)})" if c[lv]["first_minute"] else "")
                                   for lv in ("80.0", "65.0")))
        lines.append(f"| {name} · {CASE_ES[case]} · {factor[1:]} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_envolventes(data: dict) -> str:
    gains = _gains(data)
    lines = [data["envelope_rule"], ""]
    for name, item in data["envelopes"].items():
        lines += [f"**{name}. {item['question']}** — {item['status']}. Fundamento: {item['rationale']}. Base de un "
                  f"límite: {item['basis']}.", ""]
        for case, block in item["by_case"].items():
            fields = list(next(iter(next(iter(block["distribution"].values())).values())))
            lines += [f"*{CASE_ES[case]}* — " + ", ".join(ENV_FIELD_ES[f] for f in fields) + ":", "",
                      "| demanda | " + " | ".join(f"g {g}" for g in gains) + " |", "|---|" + "---|" * len(gains)]
            for factor, rows in block["distribution"].items():
                cells = []
                for g in gains:
                    values = rows.get(g, {})
                    cells.append("; ".join((_pct(values.get(f)) if f in ("output_cost", "delivery_cost")
                                            else _s(values.get(f), 2 if f in TONE_FIELDS else 1)) for f in fields))
                lines.append(f"| {factor} | " + " | ".join(cells) + " |")
            sens = block["sensitivity_a_sample"]
            if sens:
                lines.append("")
                lines.append("Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): " + "; ".join(
                    f"{key}: " + " / ".join(
                        ", ".join(_n(v, 2 if f in TONE_FIELDS else 1) if f not in ("output_cost", "delivery_cost")
                                  else _n(100 * v) + " %" if v is not None else "—"
                                  for f, v in point.items()) for point in by_a.values())
                    for key, by_a in sens.items() if key.endswith(("g0", "g1", "g2")) or key.endswith("g1.5")) + ".")
            lines.append("")
    return "\n".join(lines).rstrip()


def render_identificabilidad(data: dict) -> str:
    table = data["identifiability"]["table"]
    lines = ["| magnitud | clase | por qué |", "|---|---|---|"]
    lines += [f"| {IDENT_ES[k]} | {v[0]} | {IDENT_WHY_ES[k]} |" for k, v in table.items()]
    spread = data["identifiability"]["envelope_spread_across_gains"]
    lines += ["", "Amplitud de las medianas entre ganancias (lo que una envolvente podría acotar, mmHg): " + "; ".join(
        f"{k}: {_n(v)}" for k, v in spread.items()) + "."]
    return "\n".join(lines)


def render_barorreflejo(data: dict) -> str:
    plan = data["baroreflex_plan"]
    names = {"status": "estado", "signal": "señal", "tone_interaction": "interacción con el tono",
             "double_counting": "doble conteo", "requires": "requiere"}
    return "\n".join(f"- **{names[k]}**: {v}" for k, v in plan.items())


def render_validacion(data: dict) -> str:
    v, e = data["validation"], data["reuse"]
    return (f"Reconstrucción contra el núcleo: {v['compared']} corridas completas en {v['rows']} filas de la muestra, "
            f"todas iguales: {_yes(v['equal'])} (máxima diferencia {v['max_difference']}). Repetición idéntica: "
            f"{_yes(data['deterministic'])}. Referencia g = 0 igual a la presión de P2J-1: "
            f"{_yes(data['reference_equals_p2j1'])}. Unidades de lactato de P2I-2AK reproducidas: "
            f"{_yes(e['units_equal'])} (1.0: `{e['units_digests']['1'][:12]}…`, 1.1: `{e['units_digests']['1.1'][:12]}…`; "
            f"{data['units']['1']} y {data['units']['1.1']} unidades). Prueba AST de lo que P2J-2 cambió fuera de su "
            f"módulo: " + "; ".join(f"`{k}` {_yes(all(x.values()))}" for k, x in e["outside_unchanged"].items()) + ".")


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    lines = [f"**{v['verdict']}**", ""]
    lines += [f"- {CHECKS_ES[name]}: {_yes(ok)}" for name, ok in v["checks"].items()]
    lines.append(f"- Parámetros aprobados: {len(v['approved'])}.")
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return (f"Trayectorias hemodinámicas para reproducir las unidades: {data['reuse']['haemodynamic_trajectories']}; "
            f"trayectorias de sangre en caché (una por conjunto y escenario): {e['blood_runs']}; reconstrucciones por "
            f"ganancia con a = 0,3: {e['key_rebuilds_primary']} y de la muestra con a = 0,1 / 0,3 / 0,5: "
            f"{e['key_rebuilds_sample']} (corridas del núcleo que habrían hecho falta sin reconstrucción: "
            f"{e['core_runs_without_reconstruction']}); unidades releídas por FD-LAC: {e['fd_units']} por ganancia; "
            f"corridas completas de validación: {e['validation_full_runs']}; corridas completas para la FC: "
            f"{e['hr_full_runs']}; rechazos analíticos: {e['analytic_rejections']}; barrido cartesiano: "
            f"{_yes(e['cartesian_sweep'])}; presión heredada leída: {_yes(e['legacy_read'])}.")


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the vascular-tone JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
