"""P2I-2V: the Spanish report of the frozen shared-blood constraints and of their filter (report only).

    python -m clinical_core.blood_filter_report --write <document> [--sensitivity <JSON>] [--filter <JSON>]

It renders: every number comes from ``blood_constraints`` (its frozen decisions and readings) or from
the JSON that module wrote. It also holds one DIAGNOSTIC, labelled as such, which only calls the frozen
functions: the pre-registered leave-one-out set that decides an empty result, its representatives by the
frozen rule and how far they are from the constraint they miss. It is the one clinical_core module outside
the P2I-2V freeze, because it never defines or changes a constraint.

    python -m clinical_core.blood_filter_report --diagnostic-out <directory outside the repository>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import blood_constraints as bc, lactate_slice

MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->")
           for name in ("definiciones", "sensibilidad", "filtro")}
CONSTRAINTS_ES = {
    "U-OUT": "gasto sin tratar (envolventes por caso a 30, 60 y 120 min)",
    "U-HB": "caída de Hb sin tratar (envolventes por caso a 60 y 120 min)",
    "FD-BLD-01": "ΔHb de una unidad de GR",
    "FD-BLD-02": "aumento relativo del gasto con una unidad (techo)",
    "FD-BLD-03": "una unidad no normaliza el gasto",
    "SECOND-UNIT": "beneficio de la 2.ª unidad ≤ el de la 1.ª",
    "FD-BLD-04": "efecto circulante inicial de 1 L de cristaloide",
    "FD-BLD-05": "cristaloide retenido a 30, 60 y 120 min",
    "FD-BLD-06": "dilución de Hb con 1 y 2 L, con reversión parcial",
    "FD-BLD-07": "fracción del déficit agudo repuesta por el relleno",
    "FD-BLD-08": "el relleno sigue tras la hemostasia",
    "FD-BLD-09": "el relleno diluye la Hb y no añade GR",
}
OPERATIONAL_ES = {
    "U-OUT": "Sangrado GI del caso a la tasa del candidato desde el minuto 0, sin tratamiento y con la hemodinámica "
             "propia del candidato. Gasto relativo a la llegada en los minutos 30, 60 y 120. Una corrida cuyo gasto "
             "llega a 0 con pulso se detiene y lee gasto 0 desde entonces: no cumple la envolvente.",
    "U-HB": "v2 (P2I-2V-R): caída de Hb = Hb de llegada del caso − Hb a los 60 y 120 min, leída del estado sanguíneo "
            "compartido, dentro de [0, techo del caso]: no se exige caída mínima. Además, en la corrida sin tratar "
            "(hemorragia en curso, sin fuente de GR ni líquidos) la Hb no sube de un minuto al siguiente en 0–120 min "
            "(tolerancia numérica de 1e-9 g/dL). Ninguna deriva directa de Hb.",
    "FD-BLD-01": "Sangrado controlado; unidad 1 en 0–30 min. Hb a los 30 min − Hb a los 0, en cada caso. El modelo "
                 "mezcla al instante: leerla a los 45 o 60 min da lo mismo (sensibilidad).",
    "FD-BLD-02": "(gasto a los 30 − gasto a los 0) / gasto a los 0 no supera el techo del caso. El piso no se exige "
                 "(la docencia: no son respuestas obligatorias); V4 lo exige donde el estado responde a la precarga. "
                 "Todas las posiciones de la cuadrícula están bajo el punto medio euvolémico (0,7); la superior de 72f "
                 "(0,6) coincide con el límite inferior de esa banda, así que «con llenado bajo» es dudoso en ese punto.",
    "FD-BLD-03": "**Sólo diagnóstico desde P2I-2V-R: no rechaza ningún candidato.** Se informa cuántos sobrevivientes "
                 "llegarían a la referencia euvolémica tras una unidad, leída como posición de precarga en o sobre un "
                 "punto de la banda candidata `reference_preload_fraction` (0,6–0,7–0,8): 57m su límite inferior y 72f "
                 "su punto medio, y las lecturas V2 (ambos el medio) y V3 (ambos el inferior). Esa banda es CANDIDATA, "
                 "no una definición aprobada de normalización.",
    "SECOND-UNIT": "Δgasto de la unidad 2 (30 → 60 min) ≤ Δgasto de la unidad 1 (0 → 30 min), en cada caso.",
    "FD-BLD-04": "Sangrado del caso en curso; 1 L en 20 min desde el minuto 0. Contribución inicial = el mayor "
                 "cristaloide intravascular retenido (entrado − salido) en 0–30 min, sobre el volumen infundido: lo que "
                 "aporta la bolsa. V5 (implementada en P2I-2V-R tal como se declaró) lee en su lugar el mayor efecto "
                 "neto sobre C en 0–30 min: C con la bolsa − C sin ella, mismo sangrado, sobre el volumen infundido.",
    "FD-BLD-05": "Cristaloide intravascular retenido a los 30, 60 y 120 min desde el inicio de la infusión, sobre el "
                 "volumen infundido (1 L).",
    "FD-BLD-06": "Dilución = Hb sin la bolsa − Hb con ella, mismo sangrado. Su pico en 0–120 min dentro de la "
                 "envolvente de cada volumen (1 y 2 L); reversión parcial: 0 < dilución a los 120 < pico.",
    "FD-BLD-07": "Pérdida aguda sintética de 200 mL-eq en 10 min (la superficie de P2I-2U que vio la docencia). "
                 "Fracción repuesta = relleno acumulado / volumen perdido a los 60, 120 y 240 min.",
    "FD-BLD-08": "Sangrado GI del caso detenido por completo a los 60 min. Si a los 60 queda déficit (C < 0) y el "
                 "relleno está bajo min(capacidad, meta × perdido), el relleno debe ser positivo en cada minuto "
                 "61–70 y mayor a los 240 que a los 60; nunca supera la capacidad. La docencia dice «capacidad»; el "
                 "código mira también la meta. No cambia nada: la condición se aplica en todas las filas.",
    "FD-BLD-09": "Pérdida aguda con y sin relleno: donde el relleno es > 0 a los 60, 120 y 240 min, la Hb con relleno "
                 "es menor; ningún cambio de relleno lleva GR y el contenido de GR nunca sube.",
}
VARIANTS_ES = {
    "V1_envelope_tolerance": "cada envolvente numérica, ensanchada un 10 % de su ancho en cada extremo",
    "V2_fd03_both_midpoint": "diagnóstico de FD-BLD-03 con los dos casos bajo el punto medio euvolémico (no filtra)",
    "V3_fd03_both_lower": "diagnóstico de FD-BLD-03 con los dos casos bajo el límite inferior euvolémico (no filtra)",
    "V4_fd02_lower_bound_when_responsive": "FD-BLD-02: también el piso, donde un reto de +250 mL-eq a la llegada sube "
                                          "el gasto ≥ 10 % (el reto es una lectura contrafáctica de la curva en "
                                          "V + κ·250, no una trayectoria ni una escritura en el estado)",
    "V5_fd04_net_effect": "FD-BLD-04: efecto neto sobre C (con − sin bolsa) en vez del retenido (implementada en "
                          "P2I-2V-R tal como se declaró en P2I-2V)",
    "V6_fd06_from_arrival_hb": "FD-BLD-06: dilución = Hb de llegada − Hb con la bolsa",
    "V7_fd07_500_ml": "FD-BLD-07: pérdida aguda de 500 mL-eq en 10 min",
    "V8_case_specific_bleed_rate": "la tasa de sangrado puede diferir por caso (la lectura primaria de P2I-2V; en "
                                   "P2I-2V-R la primaria es la tasa común)",
    "V9_fd05_from_end_of_infusion": "FD-BLD-05 a los 30, 60 y 120 min desde el fin de la infusión (minutos 50, 80 y 140)",
    "V10_fd07_from_end_of_loss": "FD-BLD-07 a los 60, 120 y 240 min desde el fin de la pérdida (minutos 70, 130 y 250)",
}
PARAMETERS_ES = {
    "bleed_ml_per_min": "tasa de sangrado (mL-eq/min)", "arrival_circulating_volume_ml": "B0 (mL-eq)",
    "preload_scale_over_kappa_ml": "λ/κ (mL-eq)", "preload_fraction": "posición de precarga de llegada",
    "plasma_refill_target_share": "meta del relleno (fracción de lo perdido)",
    "plasma_refill_tau_min": "τ del relleno (min)", "plasma_refill_capacity_ml": "capacidad del relleno (mL-eq)",
    "red_cell_unit_hb_g_dl": "contenido de GR de la unidad (Hb, g/dL)", "red_cell_unit_volume_ml": "volumen de la unidad (mL-eq)",
    "crystalloid_effective_ml_per_ml": "fracción retenida del cristaloide",
    "crystalloid_leak_tau_min": "τ de redistribución del cristaloide (min)",
    "crystalloid_transient_share": "fracción transitoria del cristaloide", "reserve": "ρ (reserva de extracción)",
    "volume_preload_kappa": "κ (por separado)", "preload_curve_scale_ml": "λ (por separado)"}
CLASSES_ES = {bc.WELL: "WELL_CONSTRAINED", bc.PARTIAL: "PARTIALLY_CONSTRAINED", bc.POOR: "POORLY_IDENTIFIED",
              bc.SEPARATELY: "NON_IDENTIFIABLE_SEPARATELY", None: "sin sobrevivientes"}


def _n(value, digits: int = 2) -> str:
    if value is None:
        return "—"
    return lactate_slice._n(value, digits)


def _pair(pair, digits: int = 2) -> str:
    return f"{_n(pair[0], digits)}–{_n(pair[1], digits)}"


def _value(value) -> str:
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            return {"lower": "inf.", "midpoint": "medio", "upper": "sup."}.get(value, value)
    if float(value).is_integer() or abs(value) >= 100:
        return _n(value, 0)
    return _n(value, 3).rstrip("0").rstrip(",")


def _envelopes(case: str) -> dict:
    d = bc.DECISIONS
    return {
        "U-OUT": ", ".join(f"{m}′ {_pair(p)}" for m, p in d["untreated_output"][case].items()),
        "U-HB": ", ".join(f"{m}′ {_pair(p, 1)} g/dL" for m, p in d["untreated_hb_fall"][case].items())
                + "; la Hb no sube sin tratar",
        "FD-BLD-01": f"{_pair(d['FD-BLD-01']['envelope'], 1)} g/dL",
        "FD-BLD-02": f"≤ {_n(d['FD-BLD-02'][case][1], 2)} (piso {_n(d['FD-BLD-02'][case][0], 2)}, no exigido)",
        "FD-BLD-03": f"diagnóstico: posición ≥ {_n(bc._normalized_at(case, None), 1)} se informa (no filtra)",
        "SECOND-UNIT": "Δ2 ≤ Δ1",
        "FD-BLD-04": _pair(d["FD-BLD-04"]["envelope"]),
        "FD-BLD-05": ", ".join(f"{m}′ {_pair(p)}" for m, p in d["FD-BLD-05"]["envelopes"].items()),
        "FD-BLD-06": ", ".join(f"{v // 1000} L {_pair(p, 1)} g/dL" for v, p in d["FD-BLD-06"]["envelopes"].items())
                     + "; 0 < dilución(120′) < pico",
        "FD-BLD-07": ", ".join(f"{m}′ {_pair(p)}" for m, p in d["FD-BLD-07"]["envelopes"].items()),
        "FD-BLD-08": "sigue tras la hemostasia mientras quede déficit y brecha a la meta / capacidad",
        "FD-BLD-09": "Hb con relleno < sin relleno; ningún GR añadido",
    }


def render_definitions() -> str:
    lines = []
    add = lines.append
    add(f"Congelamiento de las decisiones y de su lectura: `{bc.freeze_digest()}` "
        "(`python -m clinical_core.blood_constraints --digest`). Lo fijan las decisiones transcritas, las lecturas, "
        "las variantes y todas las fuentes de `clinical_core` salvo este informe.\n")
    add("| Restricción | Envolvente 57m | Envolvente 72f | Lectura operativa |")
    add("|---|---|---|---|")
    e57, e72 = _envelopes(bc.CASES[0]), _envelopes(bc.CASES[1])
    for name in bc.READINGS:
        add(f"| {name}: {CONSTRAINTS_ES[name]} | {e57[name]} | {e72[name]} | {OPERATIONAL_ES[name]} |")
    add("")
    add("**Estructura de la región (P2I-2V-R).** La lectura primaria usa una sola tasa de sangrado candidata de "
        "familia GI para los dos casos: ningún caso declara una tasa verificada, y las diferencias entre casos no se "
        "explican antes de tiempo ajustando tasas separadas. La variante V8 deja que la tasa difiera por caso. Los demás "
        "parámetros del modelo son comunes; la posición de llegada es de cada caso (una banda del caso). Se informan "
        "también los sobrevivientes de cada caso por separado (todo libre por caso). Ninguna restricción lee ρ: queda en "
        "la región y sólo cambia la etiqueta del estado de extracción. La política de autoridad de producción no cambia "
        "(`CASE_OVERRIDES_FAMILY_DEFAULT`) y no se puebla ningún valor de familia.\n")
    add("**Lectura de la sangre.** Hb, volumen circulante, relleno y cristaloide no dependen de λ/κ, de la posición ni de "
        "ρ. Verificado en los puntos de prueba (Hb, volumen y relleno, cuatro superficies) y, en el filtro, en la Hb a "
        "los 60 y 120 min de cada candidato sin tratar que no se detiene. Se leen con λ/κ 1500 y la posición superior "
        "del caso, donde ninguna superficie de la cuadrícula se detiene: ningún candidato sale de una restricción de "
        "sangre porque su circulación se detuvo; eso lo juzgan las envolventes de gasto. Fuera de la cuadrícula (tasas "
        "más altas) esa lectura sí puede detenerse, y el código falla a la vista.\n")
    add("**Plantillas de los contribuyentes.** El sangrado, la bolsa y la unidad se construyen desde las entradas "
        "materializadas del camino del motor de familias (`blood_anchors._templates`). Cada campo numérico que actúa se "
        "sobrescribe con el valor del candidato; los demás no actúan. `family_engine.py` y `clinical_cases.py` no están "
        "en este congelamiento: los fija el de calibración (`scenario_inputs`, `input_path_sources`). Ninguna "
        "trayectoria heredada entra en una restricción.\n")
    add("**Variantes declaradas antes del filtro.** Cada una cambia una sola lectura y se informa junto a la primaria, "
        "nunca en su lugar.\n")
    add("| Variante | Qué cambia |")
    add("|---|---|")
    for name in bc.VARIANTS:
        add(f"| `{name}` | {VARIANTS_ES[name]} |")
    add("")
    add("V2 y V3 sólo cambian el diagnóstico de FD-BLD-03, que ya no filtra: su recuento de sobrevivientes es el de la "
        "lectura primaria. Con la región vacía, se buscan los conjuntos mínimos de restricciones sin sobreviviente "
        f"conjunto, hasta {bc.CONFLICT_SIZE} restricciones.\n")
    add("**Identificabilidad tras el filtro** (regla congelada, a la resolución de la cuadrícula): un solo valor "
        "explorado entre los sobrevivientes = WELL_CONSTRAINED; alguno excluido = PARTIALLY_CONSTRAINED; ninguno "
        "excluido = POORLY_IDENTIFIED; κ, λ y ρ = NON_IDENTIFIABLE_SEPARATELY (estructural). Un único valor en el borde "
        "de la cuadrícula se marca: lo acota la cuadrícula, no lo identifica. Sobre los sobrevivientes conjuntos; si no "
        "hay, sobre los de cada caso. Ningún valor se elige por su frecuencia.\n")
    add("**Candidatos representativos** (regla congelada): ρ en su referencia; ordenados por el gasto de 57m a los "
        "120 min, luego el de 72f, luego los valores; bajo / medio / alto = el primero, el ⌊n/2⌋-ésimo y el último. Sin "
        "sobrevivientes conjuntos, los de cada caso del mismo modo; sin ninguno, no hay representativo.\n")
    add("Texto congelado de cada lectura, tal como lo fija el código (`IMPLEMENTATION`):\n")
    for name, text in bc.IMPLEMENTATION.items():
        add(f"- `{name}`: {text}")
    return "\n".join(lines)


def render_sensitivity(data: dict) -> str:
    lines = []
    add = lines.append
    add(f"Calculada antes del congelamiento, con el código congelado `{data['freeze_digest']}`, sólo en dos puntos de "
        "prueba fuera de la cuadrícula en todos sus parámetros (P1, P2): ningún candidato de la región se evaluó antes "
        "del commit de congelamiento. Muestra cuánto mueve la métrica cada lectura que la docencia no fijó; no dice "
        "nada de cuántos candidatos sobreviven.\n")
    add("| Punto | " + " | ".join(f"`{k}`" for k in bc.PROBES["P1"]) + " |")
    add("|---|" + "---|" * len(bc.PROBES["P1"]))
    for label, point in bc.PROBES.items():
        add(f"| {label} | " + " | ".join(_value(v) for v in point.values()) + " |")
    add("")
    add(f"Premisa de la lectura de la sangre: cambiar λ/κ, la posición o ρ mueve la sangre como máximo "
        f"{_n(data['dependencies']['largest_blood_difference'], 12)} (Hb, volumen circulante, relleno; cuatro "
        "superficies, dos puntos, dos casos).\n")
    add("| Lectura | Qué se varió | " + " | ".join(data["sensitivity"]) + " |")
    add("|---|---|" + "---|" * len(data["sensitivity"]))
    items = list(data["sensitivity"].values())

    def row(label, what, fn):
        add(f"| {label} | {what} | " + " | ".join(fn(item) for item in items) + " |")
    row("gasto sin tratar", "minuto 25 / 30 / 35", lambda i: " / ".join(_n(i["untreated_output"][m]) for m in ("25", "30", "35")))
    row("gasto sin tratar", "minuto 115 / 120 / 125", lambda i: " / ".join(_n(i["untreated_output"][m]) for m in ("115", "120", "125")))
    row("caída de Hb", "minuto 55 / 60 / 65", lambda i: " / ".join(_n(i["untreated_hb_fall"][m], 3) for m in ("55", "60", "65")))
    row("caída de Hb", "minuto 115 / 120 / 125", lambda i: " / ".join(_n(i["untreated_hb_fall"][m], 3) for m in ("115", "120", "125")))
    if "untreated_hb_max_rise" in items[0]:
        row("U-HB v2: mayor subida de Hb sin tratar", "minuto a minuto, 0–120", lambda i: _n(i["untreated_hb_max_rise"], 12))
    row("ΔHb de una unidad (mezcla)", "minuto 30 / 45 / 60", lambda i: " / ".join(_n(i["one_unit"][m]["hb_gain"], 3) for m in ("30", "45", "60")))
    row("aumento del gasto con una unidad", "minuto 30 / 60", lambda i: " / ".join(_n(i["one_unit"][m]["output_gain"], 3) for m in ("30", "60")))
    row("posición tras una unidad", "frente a 0,6 / 0,7 / 0,8", lambda i: _n(i["one_unit"]["30"]["position"], 3))
    row("respuesta a la precarga", "reto de 100 / 250 / 500 mL-eq", lambda i: " / ".join(_n(i["challenge_gain"][m], 3) for m in ("100", "250", "500")))
    row("FD-BLD-04", "retenido / efecto neto", lambda i: f"{_n(i['crystalloid_1000']['retained_early'], 3)} / {_n(i['crystalloid_1000']['net_early'], 3)}")
    row("FD-BLD-05", "desde el inicio: 30 / 60 / 120", lambda i: " / ".join(_n(i["crystalloid_1000"]["retained"][m], 3) for m in ("30", "60", "120")))
    row("FD-BLD-05", "desde el fin: 50 / 80 / 140", lambda i: " / ".join(_n(i["crystalloid_1000"]["retained"][m], 3) for m in ("50", "80", "140")))
    row("FD-BLD-06 (1 L)", "pico y 120′: contrafáctico / desde la llegada",
        lambda i: f"{_n(i['crystalloid_1000']['peak'], 3)}, {_n(i['crystalloid_1000']['at_120'], 3)} / "
                  f"{_n(i['crystalloid_1000']['peak_from_arrival'], 3)}, {_n(i['crystalloid_1000']['from_arrival_120'], 3)}")
    row("FD-BLD-06 (2 L)", "pico con infusión de 20 / 40 min", lambda i: f"{_n(i['crystalloid_2000']['peak_20_min'], 3)} / {_n(i['crystalloid_2000']['peak_40_min'], 3)}")
    row("FD-BLD-07 (200 mL-eq)", "60 / 120 / 240 desde el inicio",
        lambda i: " / ".join(_n(i["acute_loss"]["200"][m], 3) for m in ("60", "120", "240")))
    row("FD-BLD-07 (200 mL-eq)", "70 / 130 / 250 (desde el fin)",
        lambda i: " / ".join(_n(i["acute_loss"]["200"][m], 3) for m in ("70", "130", "250")))
    row("FD-BLD-07 (500 mL-eq)", "60 / 120 / 240", lambda i: " / ".join(_n(i["acute_loss"]["500"][m], 3) for m in ("60", "120", "240")))
    row("FD-BLD-08", "relleno 60 → 240 (mL-eq); sigue en 61–70", lambda i: f"{_n(i['stopped']['after_ml'], 0)}; {'sí' if i['stopped']['continues'] else 'no'}")
    add("")
    add("Lectura de la tabla: el minuto exacto mueve el gasto unos 0,02 por cada 5 min y la caída de Hb menos de 0,01 "
        "g/dL; la mezcla no importa (el modelo mezcla al instante). Cambian la métrica de forma material: el reloj de "
        "FD-BLD-05 (desde el inicio o desde el fin de la infusión), la línea de base de la reversión en FD-BLD-06, la "
        "velocidad de la infusión de 2 L y el reloj de FD-BLD-07. Cada uno tiene su variante declarada antes del filtro "
        "(V9, V6, V10), salvo la velocidad de 2 L, que se deja como la de P2I-2U (20 min) y se señala como limitación. "
        "En los puntos de prueba, el efecto neto (V5) difiere del retenido en menos de 0,01. La Hb sin tratar no sube "
        "en ningún minuto (U-HB v2).")
    return "\n".join(lines)


def _count_cells(item: dict) -> list:
    return [_n(item["alone"][case], 0) for case in bc.CASES] + [_n(item["joint"], 0)]


def _marginal(counts: dict, region: list) -> str:
    return " · ".join(f"{_value(v)}: {_n(counts[str(v)], 0)}" for v in region)


def _range(counts: dict, region: list) -> str:
    left = [v for v in region if counts[str(v)] > 0]
    if not left:
        return "—"
    return _value(left[0]) if len(left) == 1 else f"{_value(left[0])} – {_value(left[-1])}"


ROWS_ES = (("red_cells_change", "contenido de GR (cambio relativo)", 3), ("hb", "Hb (g/dL)", 2),
           ("circulating_ml", "volumen circulante C (mL-eq)", 0),
           ("position", "precarga (posición)", 2), ("output_rel", "gasto relativo", 2), ("do2", "DO2", 2),
           ("state", "estado de extracción", None), ("effective_deficit", "déficit crítico efectivo", 2),
           ("refill_ml", "relleno acumulado (mL-eq)", 0), ("sbp", "PAS (sólo contexto)", 0),
           ("lactate", "lactato (sólo contexto)", 1))
STATES_ES = {"ADEQUATE": "adecuada", "COMPENSATED": "compensada", "CRITICAL": "crítica"}


def _trajectory_table(rows: list, label: str, minutes_label=None) -> list:
    out = [f"| {label} | " + " | ".join(minutes_label or [f"{row['minute']}′" for row in rows]) + " |",
           "|---|" + "---|" * len(rows)]
    for key, name, digits in ROWS_ES:
        if any(key not in row for row in rows):
            continue
        cells = [STATES_ES.get(row[key], row[key]) if digits is None else _n(row[key], digits) for row in rows]
        out.append(f"| {name} | " + " | ".join(cells) + " |")
    return out


def _representative(lines: list, label: str, item: dict, cases) -> None:
    add = lines.append
    for case in cases:
        values = item["values"][case]
        add(f"**{label} — {case}.** " + "; ".join(f"{PARAMETERS_ES[n]} {_value(values[n])}" for n in bc.PARAMETERS) + ".\n")
        t = item["trajectories"][case]
        stop = t["untreated"]["stop"]
        lines.extend(_trajectory_table(t["untreated"]["rows"], "Sin tratar"
                                       + ("" if stop is None else f" (se detiene en el minuto {stop})")))
        add("")
        lines.extend(_trajectory_table(t["red_cells"]["rows"], "GR, sangrado controlado", ["antes", "tras 1 U", "tras 2 U"]))
        add("")
        for volume in ("1000", "2000"):
            lines.extend(_trajectory_table(t[f"crystalloid_{volume}"]["rows"], f"{int(volume) // 1000} L en 20 min con sangrado"))
            add("")
        lines.extend(_trajectory_table(t["stopped_bleed"]["rows"], "Hemostasia a los 60 min"))
        add("")


def render_filter(data: dict, diagnostic_data: dict | None = None) -> str:
    """The P2I-2V-R filter (common bleed rate primary). The P2I-2V record is not regenerated."""
    lines = []
    add = lines.append
    region, sizes, primary = data["region"], data["sizes"], data["primary"]
    add(f"Filtro corrido con el congelamiento `{data['freeze_digest']}`, el mismo que fija la prueba. Región: la "
        "cuadrícula de P2I-2U, sin cambios (tres valores por parámetro). Lectura primaria: una tasa de sangrado común. "
        f"Candidatos antes del filtro: {_n(sizes['common_bleed'], 0)} conjuntos con tasa común (primaria), "
        f"{_n(sizes['case_specific'], 0)} con tasa por caso (V8) y {_n(sizes['alone'], 0)} por caso solo.\n")
    add("### 5.1 Sobrevivientes por restricción\n")
    add("«Sola»: sólo esa restricción. «Todas menos ésta»: el resto, sin ella. Conjunto = los dos casos con la tasa "
        "común. Las cifras cuentan candidatos de la cuadrícula, no pacientes.\n")
    add("| Restricción | sola: 57m | sola: 72f | sola: conjunto | todas menos ésta: 57m | todas menos ésta: 72f | "
        "todas menos ésta: conjunto |")
    add("|---|---|---|---|---|---|---|")
    for name in bc.CONSTRAINTS:
        add(f"| {name}: {CONSTRAINTS_ES[name]} | " + " | ".join(_count_cells(data["single"][name]))
            + " | " + " | ".join(_count_cells(data["without"][name])) + " |")
    add("| **Todas (las que filtran)** | " + " | ".join(_count_cells(primary)) + " | | | |")
    add("")
    add("FD-BLD-03 no filtra (FACULTY_APPROVED_QUALITATIVE / NOT_YET_HARD_FILTER); su diagnóstico está en §5.3.\n")
    add("### 5.2 Lectura primaria y variantes declaradas antes del filtro\n")
    add("| Lectura | 57m | 72f | conjunto |")
    add("|---|---|---|---|")
    add("| **primaria: tasa común** | " + " | ".join(_count_cells(primary)) + " |")
    for name in bc.VARIANTS:
        note = " — sólo cambia el diagnóstico de FD-BLD-03" if name in ("V2_fd03_both_midpoint", "V3_fd03_both_lower") else ""
        add(f"| `{name}`: {VARIANTS_ES[name]}{note} | " + " | ".join(_count_cells(data["variants"][name])) + " |")
    add("")
    add("### 5.3 FD-BLD-03, sólo diagnóstico\n")
    add("Cuántos sobrevivientes no llegarían a la referencia euvolémica tras una unidad, con cada lectura (la diferencia "
        "con el total son los que sí llegarían). Nadie se rechaza por esto.\n")
    add("| Lectura de «normalizado» | 57m | 72f | conjunto |")
    add("|---|---|---|---|")
    labels = {"primary": "57m ≥ 0,6, 72f ≥ 0,7", "V2_fd03_both_midpoint": "ambos ≥ 0,7", "V3_fd03_both_lower": "ambos ≥ 0,6"}
    for key, item in data["fd_bld_03"].items():
        add(f"| {labels[key]} | " + " | ".join(_count_cells(item)) + " |")
    add("| de un total de | " + " | ".join(_count_cells(primary)) + " |")
    add("")
    add("En el conjunto, un candidato «llega» si llega en al menos uno de los dos casos. La lectura «ambos ≥ 0,6» es "
        "degenerada en 72f: su posición de llegada superior (0,6) ya está en ese límite antes de la unidad.\n")
    joint = primary["joint"] > 0
    add("### 5.4 Región candidata restringida por la docencia (FACULTY-CONSTRAINED SHARED-BLOOD CANDIDATE REGION)\n")
    if joint:
        add("No son valores aprobados ni se elige ninguno por su frecuencia: cada celda dice cuántos sobrevivientes "
            "conjuntos (tasa común) tienen ese valor explorado.\n")
        add("| Parámetro | Sobrevivientes por valor | Rango que sobrevive |")
        add("|---|---|---|")
        rows = [(f"{bc.BLEED}|common", bc.BLEED, "tasa de sangrado común (mL-eq/min)")]
        rows += [(f"{bc.POS}|{case}", bc.POS, f"posición de precarga de llegada ({case})") for case in bc.CASES]
        rows += [(n, n, PARAMETERS_ES[n]) for n in bc.SHARED]
        for label, name, tag in rows:
            add(f"| {tag} | {_marginal(primary['marginal'][label], region[name])} | "
                f"{_range(primary['marginal'][label], region[name])} |")
        add("")
    else:
        add("**Ningún candidato cumple a la vez todas las restricciones que filtran**, con la tasa común. "
            + ("Por caso solo sí hay: ver la tabla siguiente." if any(primary["alone"].values()) else
               "Tampoco por caso solo.") + "\n")
        if any(primary["alone"].values()):
            add("| Parámetro | " + " | ".join(f"{case}: sobrevivientes por valor" for case in bc.CASES) + " |")
            add("|---|" + "---|" * len(bc.CASES))
            for name in bc.PARAMETERS:
                add(f"| {PARAMETERS_ES[name]} | " + " | ".join(
                    _marginal(primary["alone_marginal"][case][name], region[name]) for case in bc.CASES) + " |")
            add("")
        if data["conflicts"]:
            add(f"**Conjuntos mínimos sin sobreviviente conjunto** (búsqueda declarada hasta {bc.CONFLICT_SIZE}):\n")
            for item in data["conflicts"]:
                add(f"- {', '.join(item['constraints'])} (por caso: "
                    + ", ".join(f"{c} {_n(n, 0)}" for c, n in item["alone"].items()) + ")")
            add("")
    add("### 5.5 Identificabilidad tras el filtro\n")
    ident = data["identifiability"]
    if ident["basis"] == "joint":
        add("Base: los sobrevivientes conjuntos con la tasa común. A la resolución de la cuadrícula.\n")
        add("| Parámetro | Clase | Valores que quedan |")
        add("|---|---|---|")
        order = [f"{bc.BLEED}|common"] + [f"{bc.POS}|{case}" for case in bc.CASES] + list(bc.SHARED)
        order += [label for label in ident["classes"] if label not in order]
        for label in order:
            item = ident["classes"][label]
            name = label.split("|")[0]
            suffix = label.split("|")[1] if "|" in label else ""
            tag = ("tasa de sangrado común (mL-eq/min)" if suffix == "common"
                   else PARAMETERS_ES.get(name, name) + (f" ({suffix})" if suffix else ""))
            left = None if item.get("left") is None else ", ".join(_value(v) for v in item["left"]) or "ninguno"
            edge = " (borde de la cuadrícula: la acota, no la identifica)" if item.get("grid_edge") else ""
            explored = data["region"].get(name, [])
            if (item["class"] == bc.PARTIAL and item.get("left") and explored
                    and (item["left"][-1] == str(explored[-1]) or item["left"][0] == str(explored[0]))):
                edge = " (abierto en el borde de la cuadrícula: ese lado lo acota la cuadrícula, no las restricciones)"
            detail = "; ".join(part for part in (left, item.get("why")) if part) or "—"
            add(f"| {tag} | {CLASSES_ES[item['class']]}{edge} | {detail} |")
    else:
        add("No evaluable con la regla congelada sobre sobrevivientes conjuntos. κ, λ y ρ siguen "
            "NON_IDENTIFIABLE_SEPARATELY por estructura.\n")
    add("")
    add("### 5.6 Candidatos representativos\n")
    reps = data["representatives"]
    if joint and reps:
        add("Regla congelada: ρ en su referencia; ordenados por el gasto de 57m a los 120 min, luego el de 72f, luego "
            "los valores; bajo / medio / alto = el primero, el ⌊n/2⌋-ésimo y el último. La PAS y el lactato son sólo "
            "contexto. No son una selección: son tres puntos de la región.\n")
        for label in ("low", "middle", "high"):
            _representative(lines, {"low": "Bajo", "middle": "Medio", "high": "Alto"}[label], reps[label], bc.CASES)
    elif reps and any(reps.values()):
        for case in bc.CASES:
            if reps.get(case):
                for label in ("low", "middle", "high"):
                    _representative(lines, {"low": "Bajo", "middle": "Medio", "high": "Alto"}[label]
                                    + " (sólo este caso)", reps[case][label], (case,))
    else:
        add("No hay sobreviviente del que mostrar trayectorias.\n")
    add("### 5.7 Lo que leen las restricciones, en toda su tabla (contexto)\n")
    add("Mediana (mínimo–máximo) de cada lectura sobre la cuadrícula de su superficie, junto a la envolvente "
        "docente. No se ajusta nada a estas cifras.\n")
    add("| Lectura | Envolvente docente | " + " | ".join(bc.CASES) + " |")
    add("|---|---|" + "---|" * len(bc.CASES))
    m = data["metrics"]

    def env(item, digits=2):
        return "—" if item is None else f"{_n(item['median'], digits)} ({_n(item['min'], digits)}–{_n(item['max'], digits)})"
    d = bc.DECISIONS
    for minute in ("30", "60", "120"):
        add(f"| gasto sin tratar a {minute}′ | " + " / ".join(_pair(d["untreated_output"][c][int(minute)]) for c in bc.CASES)
            + " | " + " | ".join(env(m[c]["untreated_output"][minute]) for c in bc.CASES) + " |")
    add("| corridas sin tratar que se detienen antes de 120′ | — | " + " | ".join(
        f"{_n(m[c]['untreated_stopped'], 0)} de {_n(m[c]['untreated_output']['120']['n'], 0)}" for c in bc.CASES) + " |")
    for minute in ("60", "120"):
        add(f"| caída de Hb sin tratar a {minute}′ (v2) | " + " / ".join(_pair(d["untreated_hb_fall"][c][int(minute)], 1) for c in bc.CASES)
            + " | " + " | ".join(env(m[c]["untreated_hb_fall"][minute], 3) for c in bc.CASES) + " |")
    add("| mayor subida de Hb sin tratar, minuto a minuto | ≤ 1e-9 | " + " | ".join(
        env(m[c]["untreated_hb_max_rise"], 12) for c in bc.CASES) + " |")
    add("| ΔHb de una unidad | " + _pair(d["FD-BLD-01"]["envelope"], 1) + " | " + " | ".join(env(m[c]["one_unit_hb_gain"]) for c in bc.CASES) + " |")
    add("| aumento relativo del gasto con una unidad | techo " + " / ".join(_n(d["FD-BLD-02"][c][1]) for c in bc.CASES) + " | "
        + " | ".join(env(m[c]["one_unit_relative_output_gain"]) for c in bc.CASES) + " |")
    add("| posición tras una unidad (FD-BLD-03, diagnóstico) | — | "
        + " | ".join(env(m[c]["one_unit_position"]) for c in bc.CASES) + " |")
    add("| Δgasto 2.ª / 1.ª unidad | ≤ 1 | " + " | ".join(env(m[c]["second_over_first"]) for c in bc.CASES) + " |")
    add("| 1 L: contribución inicial (retenido) | " + _pair(d["FD-BLD-04"]["envelope"]) + " | " + " | ".join(env(m[c]["crystalloid_early"], 3) for c in bc.CASES) + " |")
    add("| 1 L: efecto neto inicial sobre C (V5) | " + _pair(d["FD-BLD-04"]["envelope"]) + " | " + " | ".join(env(m[c]["crystalloid_net_early"], 3) for c in bc.CASES) + " |")
    for minute, pair in d["FD-BLD-05"]["envelopes"].items():
        add(f"| 1 L: retenido a {minute}′ | {_pair(pair)} | " + " | ".join(env(m[c]["crystalloid_retained"][str(minute)], 3) for c in bc.CASES) + " |")
    for volume, pair in d["FD-BLD-06"]["envelopes"].items():
        add(f"| {volume // 1000} L: dilución pico (g/dL) | {_pair(pair, 1)} | " + " | ".join(env(m[c]["crystalloid_peak_dilution"][str(volume)], 3) for c in bc.CASES) + " |")
    for minute, pair in d["FD-BLD-07"]["envelopes"].items():
        add(f"| relleno: fracción repuesta a {minute}′ | {_pair(pair)} | " + " | ".join(env(m[c]["refill_share"][str(minute)], 3) for c in bc.CASES) + " |")
    add("| relleno tras la hemostasia, 60 → 240′ (mL-eq) | > 0 | " + " | ".join(env(m[c]["refill_after_haemostasis_ml"], 0) for c in bc.CASES) + " |")
    return "\n".join(lines)


#: The constraint whose leave-one-out set the diagnostic shows: the one that alone empties the region.
DIAGNOSTIC_DROP = "U-HB"


def diagnostic(region: dict = bc.REGION, progress=None) -> dict:
    """P2I-2V's diagnostic (its JSON is that package's historical record; rerunning it now applies the P2I-2V-R
    readings). NOT a filter result. Every constraint but DIAGNOSTIC_DROP (a set the frozen filter already counted),
    its low / middle / high members by the frozen representative rule, their trajectories and their reading
    of the dropped constraint; and, per case, the largest untreated Hb fall the region reaches among rows
    whose refill also meets FD-BLD-07."""
    table = bc.tables(region, bc.CASES, progress)
    names = tuple(name for name in bc.CONSTRAINTS if name != DIAGNOSTIC_DROP)
    counted = bc.count(table, region, None, names, survivors=True)
    found = counted.pop("found")

    def key(item):
        combination, bit_a, bit_b = item
        values = [bc._candidate(combination, bit, region) for bit in (bit_a, bit_b)]
        outputs = [table[case]["untreated"][tuple(v[n] for n in bc.TABLE_KEYS["untreated"])]["output"][120]
                   for case, v in zip(bc.CASES, values)]
        return (*outputs, json.dumps(values, sort_keys=True, default=str))
    representatives = {}
    if found:
        ordered = sorted(found, key=key)
        for label, (combination, bit_a, bit_b) in {"low": ordered[0], "middle": ordered[len(ordered) // 2],
                                                   "high": ordered[-1]}.items():
            values = {case: bc._candidate(combination, bit, region) for case, bit in zip(bc.CASES, (bit_a, bit_b))}
            representatives[label] = {
                "values": values,
                "trajectories": {case: bc.trajectories(case, values[case]) for case in bc.CASES},
                "untreated_hb": {case: bc.untreated_blood(case, values[case]) for case in bc.CASES},
                "verdicts": {case: bc.evaluate(case, values[case])["verdicts"]["primary"] for case in bc.CASES}}
    largest = {}
    for case in bc.CASES:
        refill_ok = {key: bc.passes("FD-BLD-07", case, row) for key, row in table[case]["acute_200"].items()}
        names_blood = bc.TABLE_KEYS["untreated_blood"]
        best = {m: None for m in bc.MINUTES_HB}
        for key_, row in table[case]["untreated_blood"].items():
            values = dict(zip(names_blood, key_))
            if refill_ok[tuple(values[n] for n in bc.TABLE_KEYS["acute"])]:
                for m in bc.MINUTES_HB:
                    if best[m] is None or row["fall"][m] > best[m]["fall"]:
                        best[m] = {"fall": row["fall"][m], "values": values}
        largest[case] = {"with_fd_bld_07": best,
                         "any": {m: max(row["fall"][m] for row in table[case]["untreated_blood"].values())
                                 for m in bc.MINUTES_HB}}
    return {"freeze_digest": bc.freeze_digest(), "dropped": DIAGNOSTIC_DROP, "count": counted,
            "classes": bc.classify(counted["marginal"], region,
                                   {**{f"{n}|{c}": n for n in bc.CASE_DIMS for c in bc.CASES},
                                    **{n: n for n in bc.SHARED}}) if counted["joint"] else None,
            "representatives": representatives, "largest_hb_fall": largest, "listed": len(found)}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, help="the document to update in place")
    parser.add_argument("--sensitivity", type=Path, help="the pre-freeze sensitivity JSON")
    parser.add_argument("--filter", type=Path, help="the filter JSON")
    parser.add_argument("--diagnostic", type=Path, help="the diagnostic JSON")
    parser.add_argument("--diagnostic-out", type=Path, help="compute the diagnostic into this directory")
    args = parser.parse_args(argv)
    if args.diagnostic_out:
        data = bc._plain(diagnostic(progress=lambda case, step: print(f"{case}: {step}", flush=True)))
        args.diagnostic_out.mkdir(parents=True, exist_ok=True)
        (args.diagnostic_out / "blood_diagnostic.json").write_text(
            json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0
    if not args.write:
        parser.error("--write or --diagnostic-out")
    document = args.write.read_text(encoding="utf-8")
    document = apply(document, "definiciones", render_definitions())
    if args.sensitivity:
        document = apply(document, "sensibilidad", render_sensitivity(json.loads(args.sensitivity.read_text("utf-8"))))
    if args.filter:
        diagnostic_data = json.loads(args.diagnostic.read_text("utf-8")) if args.diagnostic else None
        document = apply(document, "filtro", render_filter(json.loads(args.filter.read_text("utf-8")), diagnostic_data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
