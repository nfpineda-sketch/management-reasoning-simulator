"""P2G: the decision pack's tables as Markdown (Spanish), rendered from the pack's JSON.

    python -m clinical_core.decision_pack_markdown <decision_pack.json> <document.md> [--write]

Presentation only: it reads the numbers ``decision_pack`` computed and never recomputes or
chooses. Each table sits in the document between ``<!-- generado:NAME -->`` and
``<!-- /generado:NAME -->``; ``--write`` replaces those blocks, and without it the command fails
when a block differs from what the JSON gives (the document is stale).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CASES = ("gi_bleed_57m", "gi_bleed_72f")
LEVEL = {"lower": "inf.", "midpoint": "medio", "upper": "sup."}
SCENARIO = {"untreated_120": "sin tratamiento", "fluids_alone": "sólo cristaloides (2 L en 20 min)",
            "prbc_alone": "sólo GR (2 U en 60 min)",
            "definitive_management": "manejo definitivo (GR + IBP + endoscopia)",
            "aggressive_volume": "volumen agresivo (4 U GR + 2 L SF)"}
STATUS = {"ADMISSIBLE": "admisible", "REJECTED_BY_FROZEN_RULES": "rechazado por las reglas congeladas",
          "NOT_ASSESSED": "no evaluado (ninguna regla congelada lo lee)", "SENSITIVITY_PROBE": "sonda de sensibilidad"}
KINETIC = {"debt_clearance_tau_min": "τ_D", "lactate_per_output_deficit": "G", "lactate_clearance_tau_min": "τ_L"}


def num(value, digits: int = 1) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "sí" if value else "no"
    return f"{value:.{digits}f}".replace(".", ",")


def level(text: str) -> str:
    """An effect row's level: a band level, or a number (whole above 100)."""
    if text in LEVEL:
        return LEVEL[text]
    try:
        value = float(text.lstrip("x"))
    except ValueError:
        return text
    shown = f"{value:.0f}" if value >= 100 else f"{value:g}"
    return ("×" if text.startswith("x") else "") + shown.replace(".", ",")


FRACTION = {"untreated 60 min above arrival": "sin tratamiento, 60′ por encima de la llegada",
            "untreated 60 min more than 1 mmol/L above arrival": "sin tratamiento, 60′ más de 1 mmol/L por encima",
            "definitive 30 min below arrival": "manejo definitivo, 30′ por debajo de la llegada",
            "definitive 120 min below arrival": "manejo definitivo, 120′ por debajo de la llegada"}
FACTOR = {"bleeding source (x rate)": "`blood_loss_ml_per_min` (× tasa; volumen y glóbulos rojos de una sola fuente)"}
PATTERN = {"transient moderate low flow (0.25 for 10 min)": "flujo moderado transitorio (0,25 durante 10 min)",
           "sustained moderate low flow (0.25)": "flujo moderado sostenido (0,25)",
           "profound low flow (0.1)": "flujo profundo sostenido (0,1)",
           "recovery before substantial burden (0.15 for 10 min)": "recuperación antes de una carga sustancial "
                                                                    "(0,15 durante 10 min)",
           "recovery after substantial burden (0.15 for 26 min)": "recuperación tras una carga sustancial "
                                                                   "(0,15 durante 26 min)"}


def candidate(key: str) -> str:
    """A design point's key, short: kinetics, then the case-band levels."""
    kinetics, *levels = key.split(";")
    parts = [f"{KINETIC.get(name, name)} {float(value):g}".replace(".", ",")
             for name, value in (item.split("=") for item in kinetics.split(","))]
    names = {"excess": "exceso", "intrinsic": "intrínseca", "preload": "precarga", "debt": "D", "delivery": "entrega"}
    parts += [f"{names[name]} {LEVEL[value]}" for name, value in (item.split("=") for item in levels)
              if value != "midpoint"]
    return " · ".join(parts) + ("" if len(parts) > 3 else " · resto medio")


def table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def spread(item: dict, digits: int = 1) -> str:
    if not item or not item.get("n"):
        return "—"
    text = f"{num(item['min'], digits)} – {num(item['median'], digits)} – {num(item['max'], digits)}"
    return text + (f" ({item['stopped_before']} detenidas)" if item.get("stopped_before") else "")


def status(row: dict) -> str:
    """The frozen rules' verdict, and whether P2F's sweep ran this set."""
    return STATUS[row["status"]] + ("" if row.get("in_p2f_design") else " · fuera del diseño de P2F")


def _effects(rows: list[dict], times, digits: int, scenarios: dict) -> str:
    """Effect rows of several scenarios side by side (same factors and levels in each)."""
    names = list(scenarios)
    header = ["Factor", "Nivel", "Estado"] + [f"{scenarios[name]} {minute}′" for name in names for minute in times]
    body = []
    for index, row in enumerate(rows[names[0]]):
        cells = [FACTOR.get(row["factor"], f"`{row['factor']}`"), level(row["level"]), status(row)]
        for name in names:
            other = rows[name][index]
            cells += [num(other["values"].get(str(minute)), digits) for minute in times]
        body.append(cells)
    return table(header, body)


# Blocks ------------------------------------------------------------------------------------------

def lactate(pack: dict) -> str:
    out = []
    if pack.get("inconsistent_arrivals"):
        levels = "; ".join(f"intrínseca {LEVEL[a]} y deuda {LEVEL[b]}" for a, b in pack["inconsistent_arrival_levels"])
        out.append(f"P2I-2AE: en {pack['inconsistent_arrivals']} de los {pack['admissible_candidates']} candidatos "
                   f"admisibles de P2F ({levels}) el núcleo vigente rechaza la llegada a la ganancia por defecto: su "
                   "deuda pediría una contribución simpática negativa. Como el impulso simpático no llega al gasto, la "
                   "entrega, D, el lactato, la presión ni la FR, esos candidatos se leen sin impulso por deuda "
                   "(ganancia 0) en el lactato, la presión y la FR, y quedan fuera de las envolventes de FC.\n")
    for case in CASES:
        data = pack["lactate"][case]
        out.append(f"**{case}** — lactato (mmol/L), mínimo – mediana – máximo en la región admisible:\n")
        out.append(table(["Corrida", "0′", "30′", "60′", "120′"],
                         [[SCENARIO[scenario]] + [spread(data["envelopes"][scenario][str(minute)], 2)
                                                  for minute in (0, 30, 60, 120)]
                          for scenario in ("untreated_120", "definitive_management")]))
        out.append("")
        out.append("Representantes (posición del lactato a los 60 min sin tratamiento; no son preferencias):\n")
        rows = []
        for label, name in (("bajo", "low"), ("medio", "middle"), ("alto", "high")):
            item = data["representatives"][name]
            for scenario in ("untreated_120", "definitive_management"):
                rows.append([label, candidate(item["candidate"]), SCENARIO[scenario]]
                            + [num(item["trajectories"][scenario][str(minute)], 2) for minute in (0, 30, 60, 120)])
        out.append(table(["Región", "Conjunto", "Corrida", "0′", "30′", "60′", "120′"], rows))
        out.append("")
        out.append("Proporción de la región admisible a cada lado de las preguntas docentes (sólo modelo):\n")
        out.append(table(["Lectura", "Conjuntos", "Proporción"],
                         [[label, str(data["fractions"][name]["n"]),
                           f"{round(100 * data['fractions'][name]['fraction'])} %"] for name, label in FRACTION.items()]))
        out.append("")
        out.append("Efecto de cada factor alrededor del punto medio:\n")
        out.append(_effects(data["effects"], (30, 60, 120), 2,
                            {"untreated_120": "sin trat.", "definitive_management": "definitivo"}))
        out.append("")
    return "\n".join(out).rstrip()


def heart_rate(pack: dict) -> str:
    out = []
    if pack.get("inconsistent_arrivals"):
        out.append(f"P2I-2AE: la envolvente de FC lee sólo los {pack['admissible_candidates'] - pack['inconsistent_arrivals']}"
                   " candidatos cuya llegada acepta el núcleo vigente.\n")
    out.append("Desde P2I-2AE el impulso por deuda es debt_to_sympathetic_gain × D y el núcleo ya no lee "
               "sympathetic_per_debt: sus filas (0,25 / 0,5 / 1) son idénticas por construcción, no un resultado. Desde "
               "P2I-2AF la FC de llegada es la que predice la fisiología de llegada (déficit agudo, deuda; sin resto de "
               "llegada), con la ganancia aguda en 0 por defecto y el incremento simpático saturado hacia el techo "
               "sinusal provisional: esta tabla histórica no reproduce la FC de llegada registrada y no es una "
               "calibración.\n")
    for case in CASES:
        data = pack["hr"][case]
        intrinsic, sympathetic = data["intrinsic_band"], data["sympathetic_band_bpm"]
        arrival = data["arrival_hr_by_intrinsic"]
        out.append(f"**{case}** — FC de llegada predicha {num(data['arrival_hr'], 0)} lpm = intrínseca media "
                   f"{num(intrinsic[1], 0)} + parte simpática {num(sympathetic[1], 1)}; con la intrínseca "
                   f"{num(intrinsic[0], 0)} / {num(intrinsic[2], 0)}: {num(arrival[0], 0)} / {num(arrival[2], 0)} lpm "
                   f"(parte simpática {num(sympathetic[0], 1)} / {num(sympathetic[2], 1)}); betabloqueo 0 "
                   "(factor 1 − β = 1); ninguna otra fuente cronotrópica en estas corridas.\n")
        rows = []
        for scenario, item in data["scenarios"].items():
            times = [minute for minute in ("30", "60", "120") if minute in item["envelope"]]
            envelope = {minute: spread(item["envelope"][minute]) for minute in times}
            for label, points in item["decomposition"].items():
                rows.append([SCENARIO[scenario], label.replace("intrinsic", "intrínseca").replace("upper", "sup.")
                             .replace("lower", "inf.").replace("middle", "medio")]
                            + [f"{num(points[minute]['hr'])} = {num(points[minute]['intrinsic_bpm'], 0)} + "
                               f"{num(points[minute]['sympathetic_bpm'])}" if minute in points else "—"
                               for minute in ("30", "60", "120")]
                            + ["; ".join(f"{minute}′ {envelope[minute]}" for minute in times)
                               if label == "middle" else ""])
        out.append(table(["Corrida", "Intrínseca", "30′ (FC = intr. + simp.)", "60′", "120′",
                          "Región admisible (mín – mediana – máx)"], rows))
        out.append("")
        out.append("Velocidad de resolución con manejo definitivo, por decaimiento simpático (τ) e intrínseca: minuto en "
                   "que la parte simpática cae a la mitad de la de llegada («mitad simpática», depende de la "
                   "intrínseca) y minuto en que la FC recorre la mitad de su propia caída hasta los 120′ («mitad de "
                   "la caída»):\n")
        rows = [[decay, LEVEL[name], str(item["sympathetic_half_min"] or "nunca"), str(item["half_of_fall_min"] or "—"),
                 num(item["hr_end"]), num(item["fall_bpm"]), num(item["sympathetic_end_bpm"])]
                for decay, levels in sorted(data["resolution"].items(), key=lambda pair: float(pair[0]))
                for name, item in levels.items()]
        out.append(table(["τ simpático (min)", "Intrínseca", "Mitad simpática (min)", "Mitad de la caída (min)",
                          "FC 120′", "Caída (lpm)", "Parte simpática 120′ (lpm)"], rows))
        out.append("")
        out.append(_effects(data["effects"], (30, 60, 120), 1,
                            {"untreated_120": "sin trat.", "definitive_management": "definitivo"}))
        out.append("")
    return "\n".join(out).rstrip()


def pressure(pack: dict) -> str:
    out = []
    for case in CASES:
        data = pack["bp"][case]
        out.append(f"**{case}** — sin tratamiento, mínimo – mediana – máximo en la región admisible:\n")
        out.append(table(["", "0′", "15′", "30′", "60′", "120′"],
                         [[name.upper()] + [spread(data["envelopes"][name][str(minute)]) for minute in
                                            (0, 15, 30, 60, 120)] for name in ("sbp", "map")]))
        out.append("")
        rows = []
        for index, row in enumerate(data["effects"]["sbp"]):
            mean = data["effects"]["map"][index]
            rows.append([FACTOR.get(row["factor"], f"`{row['factor']}`"), level(row["level"]), status(row)]
                        + [f"{num(row['values'].get(str(minute)), 0)} / {num(mean['values'].get(str(minute)), 0)}"
                           for minute in (15, 30, 60, 120)]
                        + [str(row["stopped_at"]) if row["stopped_at"] else ""])
        out.append(table(["Factor", "Nivel", "Estado", "15′ PAS/PAM", "30′", "60′", "120′", "Se detiene en"], rows))
        out.append("")
    return "\n".join(out).rstrip()


def collapse(pack: dict) -> str:
    data = pack["collapse"]
    out = ["Minutos de acumulación hasta el límite con gasto constante, en aritmética exacta: ⌈límite × umbral / "
           "(ganancia × (umbral − gasto))⌉. Un paro simulado llega un minuto después (el minuto en que cae el gasto), "
           "y uno más cuando el cociente es entero, porque la suma en coma flotante del modelo queda justo bajo el "
           "límite:\n"]
    outputs = ("0.05", "0.1", "0.15", "0.2", "0.25", "0.35")
    rows = [[num(row["threshold"]), num(row["gain"]), num(row["limit"], 0)]
            + [str(row["minutes_to_transition"][output]) if row["minutes_to_transition"][output] else "nunca"
               for output in outputs] for row in data["analytic_minutes"]]
    out.append(table(["Umbral", "Ganancia", "Límite"] + [f"gasto {output.replace('.', ',')}" for output in outputs],
                     rows))
    out.append("")
    out.append("Patrones sobre la llegada sintética neutra, con la regla en sus puntos medios (umbral 0,3, ganancia 1, "
               "límite 15, repago 60 min):\n")
    rows = [[PATTERN[name], str(item["arrest_minute"]) if item["arrest_minute"] else "no", num(item["peak_burden"])]
            + [num(item["burden_at"].get(str(minute))) for minute in (10, 26, 60, 120, 240)]
            for name, item in sorted(data["patterns"].items(), key=lambda pair: list(PATTERN).index(pair[0]))]
    out.append(table(["Patrón", "Paro (min)", "Carga máx.", "carga 10′", "26′", "60′", "120′", "240′"], rows))
    out.append("")
    out.append("Repago entre episodios (0,15 durante 26 min; recuperado 30 min; 0,15 durante 15 min):\n")
    order = sorted(data["repayment"], key=lambda tau: -1.0 if tau == "none" else float(tau))
    rows = [["sin repago" if tau == "none" else tau,
             str(data["repayment"][tau]["26 min at 0.15, 30 min recovered, 15 min at 0.15"]["arrest_minute"] or "no"),
             num(data["repayment"][tau]["after 26 min at 0.15"]["burden_at"].get("60"))] for tau in order]
    out.append(table(["τ de repago (min)", "Paro en el 2.º episodio (min)", "Carga 34 min después del 1.º"], rows))
    out.append("")
    out.append("Ritmo terminal según la política declarada: "
               + "; ".join(f"`{key}` → `{value}`" for key, value in data["terminal_rhythm_by_policy"].items())
               + ". La regla no mira la causa ni el estado: el ritmo es el que declara el perfil.")
    return "\n".join(out)


def volume(pack: dict) -> str:
    out = []
    data = pack["volume"]["summary"]
    for case in CASES:
        out.append(f"**{case}** — volumen agresivo (90 min). Lo que mueve la presión es la posición y la escala de la "
                   "curva; la rodilla y la ganancia de congestión y la reserva sólo cambian L (rango en «L final»). "
                   "«Estado» aplica las reglas congeladas al conjunto completo (el mismo nivel en los dos casos) con "
                   "esa escala; «En el diseño de P2F» dice si P2F barrió esa celda (sólo con la escala por defecto).\n")
        rows = [[LEVEL[cell["preload_fraction"]], num(cell["preload_curve_scale_ml"], 0), num(cell["net_V_ml_eq"], 0),
                 f"{num(cell['arrival_sbp'], 0)} → {num(cell['peak_sbp'], 0)}", num(cell["peak_map"], 0),
                 num(cell["peak_output"], 2), f"{num(cell['arrival_position'], 2)} → {num(cell['final_position'], 2)}",
                 num(cell["marginal_responsiveness"], 2), num(cell["final_hr"], 0),
                 f"{num(cell['final_L'][0], 3)} – {num(cell['final_L'][1], 3)}", STATUS[cell["status"]],
                 num(cell["in_p2f_design"])]
                for cell in data["cells"][case]]
        out.append(table(["Precarga", "Escala (mL)", "V neto (mL-eq)", "PAS llegada → pico", "PAM pico",
                          "Gasto pico (× llegada)", "Posición llegada → final", "Respuesta marginal final",
                          "FC final", "L final", "Estado", "En el diseño de P2F"], rows))
        out.append("")
    status = pack["volume"]["summary"]["congestion_parameter_status"]
    out.append("Estado de los parámetros de congestión: "
               + "; ".join(f"`{name}` " + ", ".join(f"{point.replace('.', ',')} {STATUS[value]}"
                                                    for point, value in points.items())
                           for name, points in status.items()) + ".")
    return "\n".join(out)


def respiratory_rate(pack: dict) -> str:
    out = []
    for case in CASES:
        data = pack["rr"][case]
        bounds = data["bounds"]
        out.append(f"**{case}** — FR de llegada {num(bounds['arrival_rr'], 0)} resp/min con lactato "
                   f"{num(bounds['arrival_lactate'])} mmol/L. Cotas del modelo sobre la cuadrícula de bandas de FR "
                   "(`rr_per_lactate` × `lactate_drive_threshold_mmol_l` × `rr_ventilatory_floor`, por "
                   "`rr_metabolic_max`): techo con lactato sin límite, antes y después de `rr_max`, y piso con lactato "
                   "bajo el umbral (mínimo – máximo):\n")
        rows = [[cap] + [f"{num(values[0])} – {num(values[1])}" for key, values in item.items()]
                for cap, item in sorted(bounds["by_cap"].items(), key=lambda pair: float(pair[0]))]
        keys = list(next(iter(bounds["by_cap"].values())))
        out.append(table(["`rr_metabolic_max`"] + [key.replace("ceiling at rr_max", "techo con `rr_max`")
                                                    .replace("floor", "piso") for key in keys], rows))
        out.append("")
        out.append(f"En las corridas del paquete, FR observada entre {num(data['floor'])} y {num(data['ceiling'])}. "
                   "Mínimo – mediana – máximo en la región admisible:\n")
        out.append(table(["Corrida", "0′", "30′", "60′", "120′"],
                         [[SCENARIO[scenario]] + [spread(data["envelopes"][scenario][str(minute)])
                                                  for minute in (0, 30, 60, 120)]
                          for scenario in ("untreated_120", "definitive_management")]))
        out.append("")
        rows = []
        for label, item in data["severities"].items():
            for scenario in ("untreated_120", "definitive_management"):
                points = item[scenario]
                rows.append([label.replace("mild", "leve").replace("moderate", "moderado").replace("severe", "grave")
                             .replace("debt", "D").replace("delivery", "entrega").replace(".", ","),
                             SCENARIO[scenario] if scenario == "untreated_120" else "mejoría (manejo definitivo)"]
                            + [f"{num(points[minute]['rr'])} = {num(points[minute]['rr_ventilatory'])} + "
                               f"{num(points[minute]['rr_metabolic'])}" for minute in ("0", "30", "60", "120")])
        out.append(table(["Shock", "Corrida", "0′ (FR = ventilatoria + metabólica)", "30′", "60′", "120′"], rows))
        out.append("")
        out.append(_effects(data["effects"], (30, 60, 120), 1,
                            {"untreated_120": "sin trat.", "definitive_management": "definitivo"}))
        out.append("")
    return "\n".join(out).rstrip()


def pl2(pack: dict) -> str:
    rows = [[num(row["arrival_preload_fraction"], 2), num(row["preload_curve_scale_ml"], 0),
             num(row["pump_preload_coupling"], 1), num(row["gain_normal_pump"], 3), num(row["gain_pump_0_6"], 3),
             num(row["output_pump_0_6_after_500"], 3), num(row["clause_1_holds"]), num(row["clause_2_holds"]),
             num(row["in_registry_band"])]
            for row in pack["pl2"]["rows"] if row["pump_preload_coupling"] in (0.0, 1.0)
            and row["arrival_preload_fraction"] in (0.3, 0.35, 0.4)]
    return table(["Posición", "Escala (mL)", "Acoplamiento", "Ganancia bomba normal", "Ganancia bomba 0,6",
                  "Gasto bomba 0,6 tras 500 mL", "Cláusula 1", "Cláusula 2", "Punto del registro"], rows)


def reachability(pack: dict) -> str:
    data = pack["reachability"]
    rows = [[num(row["debt_clearance_tau_min"], 0), num(row["debt_per_delivery_deficit"]),
             num(row["bound_at_demand_1"], 0), ", ".join(LEVEL[level] for level in row["excluded_arrival_D_levels"])
             or "ninguno"] for row in data["by_kinetics"]]
    return (table(["τ_D (min)", "g", "Cota g × 1 × τ_D", "Niveles de D de llegada (0 / 20 / 60) excluidos"], rows)
            + f"\n\nEn el diseño GI de P2F (g = 1) la cota excluiría {data['excluded_design_points']} conjuntos; "
            + ("todos son los que P2F ya rechazó por HR1." if data["all_rejected_by_p2f"]
               else "algunos no los rechazó P2F.")
            + " Desde P2I-2AC la deuda no se devuelve mientras dura el déficit, así que ninguna deuda de llegada "
              "baja durante un déficit y esta cota ya no describe el modelo: queda como registro del análisis de "
              "P2G.")


def preload_edge(pack: dict) -> str:
    rows = [[num(row["preload_fraction"], 2), num(row["preload_curve_scale_ml"], 0),
             num(row["arrival_filling_ml_eq"], 0),
             str(row["probe 8 mL/min"] or "no"), str(row["probe 4 mL/min"] or "no"),
             str(row["case source 2.5 mL/min"] or "no (120 min)")]
            for row in pack["preload_edge"]["rows"]]
    return table(["Posición", "Escala (mL)", "Llenado sobre el vacío (mL-eq)", "Sonda HR1 8 mL/min: vacío en",
                  "Sonda 4 mL/min", "Sangrado del caso 2,5 mL/min"], rows)


BLOCKS = {"lactato": lactate, "fc": heart_rate, "presion": pressure, "colapso": collapse, "volumen": volume,
          "fr": respiratory_rate, "pl2": pl2, "alcanzabilidad": reachability, "precarga_02": preload_edge}


def render(pack: dict) -> dict[str, str]:
    return {name: function(pack) for name, function in BLOCKS.items()}


def apply(document: str, blocks: dict[str, str]) -> str:
    for name, body in blocks.items():
        opening, closing = f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->"
        start, end = document.find(opening), document.find(closing)
        if start < 0 or end < start:
            raise ValueError(f"the document has no block {name}")
        document = document[:start + len(opening)] + body + "\n" + document[end:]
    return document


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pack", type=Path)
    parser.add_argument("document", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    pack = json.loads(args.pack.read_text(encoding="utf-8"))
    current = args.document.read_text(encoding="utf-8")
    updated = apply(current, render(pack))
    if args.write:
        args.document.write_text(updated, encoding="utf-8")
        return 0
    if updated != current:
        raise SystemExit("the document's generated tables differ from the pack: run with --write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
