"""P2I-2V: the Spanish report of the frozen shared-blood constraints and of their filter (report only).

    python -m clinical_core.blood_filter_report --write <document> [--sensitivity <JSON>] [--filter <JSON>]

It only renders: every number comes from ``blood_constraints`` (its frozen decisions and readings) or
from the JSON that module wrote. It is the one clinical_core module outside the P2I-2V freeze, because
it never computes a constraint.
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
    "U-HB": "Caída de Hb = Hb de llegada del caso − Hb a los 60 y 120 min, leída del estado sanguíneo compartido. "
            "Ninguna deriva directa de Hb.",
    "FD-BLD-01": "Sangrado controlado; unidad 1 en 0–30 min. Hb a los 30 min − Hb a los 0, en cada caso. El modelo "
                 "mezcla al instante: leerla a los 45 o 60 min da lo mismo (sensibilidad).",
    "FD-BLD-02": "(gasto a los 30 − gasto a los 0) / gasto a los 0 no supera el techo del caso. El piso no se exige "
                 "(la docencia: no son respuestas obligatorias); V4 lo exige donde el estado responde a la precarga. "
                 "Todas las posiciones de la cuadrícula están bajo la referencia euvolémica.",
    "FD-BLD-03": "«Normalizado» = posición de precarga tras una unidad en o sobre la referencia euvolémica del caso "
                 "(banda 0,6–0,7–0,8). 57m debe quedar bajo su límite inferior (no entra en el rango euvolémico); "
                 "72f bajo su punto medio (puede acercarse, no llegar). Una corrida determinista por candidato: "
                 "«de forma fiable» se lee por candidato.",
    "SECOND-UNIT": "Δgasto de la unidad 2 (30 → 60 min) ≤ Δgasto de la unidad 1 (0 → 30 min), en cada caso.",
    "FD-BLD-04": "Sangrado del caso en curso; 1 L en 20 min desde el minuto 0. Contribución inicial = el mayor "
                 "cristaloide intravascular retenido (entrado − salido) en 0–30 min, sobre el volumen infundido.",
    "FD-BLD-05": "Cristaloide intravascular retenido a los 30, 60 y 120 min desde el inicio de la infusión, sobre el "
                 "volumen infundido (1 L).",
    "FD-BLD-06": "Dilución = Hb sin la bolsa − Hb con ella, mismo sangrado. Su pico en 0–120 min dentro de la "
                 "envolvente de cada volumen (1 y 2 L); reversión parcial: 0 < dilución a los 120 < pico.",
    "FD-BLD-07": "Pérdida aguda sintética de 200 mL-eq en 10 min (la superficie de P2I-2U que vio la docencia). "
                 "Fracción repuesta = relleno acumulado / volumen perdido a los 60, 120 y 240 min.",
    "FD-BLD-08": "Sangrado GI del caso detenido por completo a los 60 min. Si a los 60 queda déficit (C < 0) y el "
                 "relleno está bajo min(capacidad, meta × perdido), el relleno debe ser positivo en cada minuto "
                 "61–70 y mayor a los 240 que a los 60; nunca supera la capacidad.",
    "FD-BLD-09": "Pérdida aguda con y sin relleno: donde el relleno es > 0 a los 60, 120 y 240 min, la Hb con relleno "
                 "es menor; ningún cambio de relleno lleva GR y el contenido de GR nunca sube.",
}
VARIANTS_ES = {
    "V1_envelope_tolerance": "cada envolvente numérica, ensanchada un 10 % de su ancho en cada extremo",
    "V2_fd03_both_midpoint": "FD-BLD-03: los dos casos bajo el punto medio euvolémico",
    "V3_fd03_both_lower": "FD-BLD-03: los dos casos bajo el límite inferior euvolémico",
    "V4_fd02_lower_bound_when_responsive": "FD-BLD-02: también el piso, donde un reto de +250 mL-eq a la llegada sube "
                                          "el gasto ≥ 10 %",
    "V5_fd04_net_effect": "FD-BLD-04: efecto neto sobre C (con − sin bolsa) en vez del retenido",
    "V6_fd06_from_arrival_hb": "FD-BLD-06: dilución = Hb de llegada − Hb con la bolsa",
    "V7_fd07_500_ml": "FD-BLD-07: pérdida aguda de 500 mL-eq en 10 min",
    "V8_common_bleed_rate": "una sola tasa de sangrado para los dos casos (camino del valor de familia)",
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
        "U-HB": ", ".join(f"{m}′ {_pair(p, 1)} g/dL" for m, p in d["untreated_hb_fall"][case].items()),
        "FD-BLD-01": f"{_pair(d['FD-BLD-01']['envelope'], 1)} g/dL",
        "FD-BLD-02": f"≤ {_n(d['FD-BLD-02'][case][1], 2)} (piso {_n(d['FD-BLD-02'][case][0], 2)}, no exigido)",
        "FD-BLD-03": f"posición < {_n(bc._normalized_at(case, None), 1)}",
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
    for name in bc.CONSTRAINTS:
        add(f"| {name}: {CONSTRAINTS_ES[name]} | {e57[name]} | {e72[name]} | {OPERATIONAL_ES[name]} |")
    add("")
    add("**Estructura de la región.** Los parámetros del modelo son comunes a los dos casos; la tasa de sangrado y la "
        "posición de llegada son de cada caso. La posición es una banda del caso; una tasa propia del caso es admisible "
        "con `CASE_OVERRIDES_FAMILY_DEFAULT`, pero hoy ningún caso la declara: V8 exige una tasa común. Se informan "
        "también los sobrevivientes de cada caso por separado (todo libre por caso). Ninguna restricción lee ρ: queda "
        "en la región y sólo cambia la etiqueta del estado de extracción.\n")
    add("**Lectura de la sangre.** Hb, volumen circulante, relleno y cristaloide no dependen de λ/κ, de la posición ni de "
        "ρ (verificado en los puntos de prueba y, en el filtro, en cada candidato sin tratar que no se detiene). Se "
        "leen con λ/κ 1500 y la posición superior del caso, donde ninguna superficie se detiene: ningún candidato sale "
        "de una restricción de sangre porque su circulación se detuvo; eso lo juzgan las envolventes de gasto.\n")
    add("**Variantes declaradas antes del filtro.** Cada una cambia una sola lectura y se informa junto a la primaria, "
        "nunca en su lugar.\n")
    add("| Variante | Qué cambia |")
    add("|---|---|")
    for name in bc.VARIANTS:
        add(f"| `{name}` | {VARIANTS_ES[name]} |")
    add("")
    add("**Identificabilidad tras el filtro** (regla congelada, a la resolución de la cuadrícula): un solo valor "
        "explorado entre los sobrevivientes = WELL_CONSTRAINED; alguno excluido = PARTIALLY_CONSTRAINED; ninguno "
        "excluido = POORLY_IDENTIFIED; κ, λ y ρ = NON_IDENTIFIABLE_SEPARATELY (estructural). Sobre los sobrevivientes "
        "conjuntos; si no hay, sobre los de cada caso. Ningún valor se elige por su frecuencia.\n")
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
        "velocidad de la infusión de 2 L, el reloj de FD-BLD-07 y el umbral de FD-BLD-03. Cada uno tiene su variante "
        "declarada antes del filtro (V9, V6, V10, V2/V3), salvo la velocidad de 2 L, que se deja como la de P2I-2U "
        "(20 min) y se señala como limitación.")
    return "\n".join(lines)


def render_filter(data: dict) -> str:
    return "Pendiente."


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--sensitivity", type=Path, help="the pre-freeze sensitivity JSON")
    parser.add_argument("--filter", type=Path, help="the filter JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    document = apply(document, "definiciones", render_definitions())
    if args.sensitivity:
        document = apply(document, "sensibilidad", render_sensitivity(json.loads(args.sensitivity.read_text("utf-8"))))
    if args.filter:
        document = apply(document, "filtro", render_filter(json.loads(args.filter.read_text("utf-8"))))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
