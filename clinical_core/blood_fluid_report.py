"""P2I-2Y report: the generated blocks of docs/revision/P2I2Y_CRISTALOIDE_Y_TASA.md.

    python -m clinical_core.blood_fluid_report --write <document> --data <the fluid-calibration JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import blood_constraints as bc
from .blood_extension_report import SHORT
from .blood_filter_report import CLASSES_ES, _n, _value

MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->")
           for name in ("tasa", "cristaloide", "superficie", "trayectorias", "estado")}
STATES_ES = {"ADEQUATE": "adecuada", "COMPENSATED": "compensada", "CRITICAL": "crítica"}
SIDES_ES = {"CONSTRAINED": "acotado por restricción", "OPEN": "abierto (borde de la grilla)",
            "DOMAIN": "límite del dominio", None: "—"}
TAGS_ES = {"low": "bajo", "middle": "medio", "high": "alto"}
POSITIONS_ES = {"lower": "inferior", "midpoint": "media", "upper": "superior"}


def _point(key: str) -> str:
    f0, finf, tau = key.split("|")
    return f"F0 {_value(f0)} · Finf {_value(finf)} · τ {_value(tau)}"


def render_rate(data: dict) -> str:
    lines = []
    add = lines.append
    r, design = data["robustness"], data["robustness_design"]
    add(f"Congelamiento de P2I-2Y: `{data['freeze_digest']}`, comprometido antes de evaluar (una prueba lo fija). "
        f"Registros: P2I-2V-R `{data['records']['P2I-2V-R']}`, P2I-2X `{data['records']['P2I-2X']}`.\n")
    add(f"Registro docente de P2I-2X: TESTED_VIABLE_RATE_REGION = {{{', '.join(_value(v) for v in data['rate_record']['TESTED_VIABLE_RATE_REGION'])}}}; "
        f"FIRST_TESTED_NONVIABLE_RATE = {_value(data['rate_record']['FIRST_TESTED_NONVIABLE_RATE'])}. No es una tasa "
        "aprobada.\n")
    add(f"Diseño: tasas {', '.join(_value(v) for v in design['rates'])}; meta del relleno "
        f"{', '.join(_value(v) for v in design['targets'])}; τ del relleno {', '.join(_value(v) for v in design['taus'])} "
        f"({len(design['refill_pairs'])} pares, {len(design['new_refill_pairs'])} nuevos); las demás dimensiones con "
        f"sus valores supervivientes de P2I-2V-R ({_n(design['shared_combinations'], 0)} conjuntos compartidos); "
        "posiciones compatibles de cada caso: "
        + "; ".join(f"{SHORT[c]} {', '.join(_value(p) for p in design['positions'][c])}" for c in bc.CASES) + ".\n")
    add("| Tasa | Rechazo analítico 57m / 72f | Simulados 57m / 72f | Falla U-OUT 57m / 72f | 57m solo | 72f solo | "
        "Sobrevivientes conjuntos | Conjuntos ilegibles |")
    add("|---|---|---|---|---|---|---|---|")
    for rate in design["rates"]:
        item = r["rates"][str(rate)]
        alone = [_n(item["alone"][c], 0) + (f" (+{_n(item['alone_unreadable'][c], 0)} ilegibles)"
                                            if item["alone_unreadable"][c] else "") for c in bc.CASES]
        add(f"| {_value(rate)} | {_n(r['analytic_rejection']['gi_bleed_57m'], 0)} / "
            f"{_n(r['analytic_rejection']['gi_bleed_72f'], 0)} | {_n(item['simulated']['gi_bleed_57m'], 0)} / "
            f"{_n(item['simulated']['gi_bleed_72f'], 0)} | {_n(item['u_out_fail']['gi_bleed_57m'], 0)} / "
            f"{_n(item['u_out_fail']['gi_bleed_72f'], 0)} | {alone[0]} | {alone[1]} | {_n(item['joint'], 0)} | "
            f"{_n(item['joint_unreadable'], 0)} |")
    add("")
    add("«57m solo» y «72f solo»: cada caso con su propio prefiltro, en cualquiera de sus posiciones compatibles "
        "(sensibilidad).\n")
    add("Sobrevivientes conjuntos por par de relleno (meta, τ):\n")
    add("| Meta | τ (min) | Nuevo | " + " | ".join(f"Tasa {_value(rate)}" for rate in design["rates"]) + " |")
    add("|---|---|---|" + "---|" * len(design["rates"]))
    new = {f"{t:g}|{u:g}" for t, u in design["new_refill_pairs"]}
    for target, tau in design["refill_pairs"]:
        pair = f"{target:g}|{tau:g}"
        add(f"| {_value(target)} | {_value(tau)} | {'sí' if pair in new else 'no'} | "
            + " | ".join(_n(r["rates"][str(rate)]["by_refill"].get(pair, 0), 0) for rate in design["rates"]) + " |")
    add("")
    add("Sobrevivientes conjuntos por posición de llegada (cada caso):\n")
    add("| Tasa | " + " | ".join(f"{SHORT[c]} {_value(p)}" for c in bc.CASES for p in design["positions"][c]) + " |")
    add("|---|" + "---|" * sum(len(design["positions"][c]) for c in bc.CASES))
    for rate in design["rates"]:
        item = r["rates"][str(rate)]
        add(f"| {_value(rate)} | " + " | ".join(_n(item["by_position"][c][str(p)], 0) for c in bc.CASES
                                              for p in design["positions"][c]) + " |")
    add("")
    add(f"**Conclusión: {r['conclusion']}.**")
    return "\n".join(lines)


def render_crystalloid(data: dict) -> str:
    lines = []
    add = lines.append
    counts = data["counts"]
    add("Grilla de exploración docente (congelada antes de evaluar): F0 0,15 a 0,35; Finf 0 a 0,20; τ 15, 30 y 60 min. "
        f"{_n(len(data['grid']), 0)} combinaciones; {_n(counts['analytic_rejection'], 0)} con Finf > F0 quedan "
        f"`ANALYTIC_REJECTION` sin simular; se evalúan {_n(counts['evaluated'], 0)}.\n")
    add("Sondas de sangre de FD-BLD-06 (claves B0, tasa, meta, τ, capacidad de sobrevivientes certificados):\n")
    add("| Sonda | B0 | Tasa | Meta | τ | Capacidad |")
    add("|---|---|---|---|---|---|")
    for name, key in data["probes"].items():
        label = (name.replace("REFERENCE", "referencia").replace("REPRESENTATIVE", "representativo")
                 .replace("BOUNDARY", "borde").replace("low", "bajo").replace("middle", "medio")
                 .replace("high", "alto"))
        add(f"| {label} | " + " | ".join(_value(v) for v in key) + " |")
    add("")
    add("| Restricción | Sobrevivientes (de los evaluados) |")
    add("|---|---|")
    labels = {"FD-BLD-04": "FD-BLD-04 (aporte inicial)", "FD-BLD-05": "FD-BLD-05 (retenido a 30, 60 y 120 min)",
              "FD-BLD-06 (some probe)": "FD-BLD-06, en alguna sonda", "FD-BLD-06 (every probe)": "FD-BLD-06, en todas",
              "FD-BLD-06 (reference)": "FD-BLD-06, en la referencia"}
    for key, value in counts["per_constraint"].items():
        add(f"| {labels[key]} | {_n(value, 0)} |")
    add(f"| **combinado, primario** (FD-BLD-04, 05 y 06 en alguna sonda) | **{_n(counts['combined']['primary'], 0)}** |")
    add(f"| combinado, robusto (FD-BLD-06 en todas las sondas) | {_n(counts['combined']['robust'], 0)} |")
    add(f"| combinado, aislado (FD-BLD-06 en la referencia) | {_n(counts['combined']['isolated'], 0)} |")
    add("")
    add("Sobrevivientes primarios:\n")
    add("| Punto | Aporte inicial 57m | Retenido 30′ / 60′ / 120′ (57m) | Sondas donde falla FD-BLD-06 |")
    add("|---|---|---|---|")
    fails = {item["point"]: item["fails_at"] for item in counts["interaction"]}
    for key in sorted(counts["survivors"]["primary"], key=lambda k: [float(v) for v in k.split("|")]):
        entry = data["crystalloid"][key]
        reading = entry["readings"]["gi_bleed_57m"]
        add(f"| {_point(key)} | {_n(reading['early'])} | "
            + " / ".join(_n(reading["share"][str(m)]) for m in (30, 60, 120))
            + f" | {', '.join(fails.get(key, [])) or 'ninguna'} |")
    return "\n".join(lines)


def render_surface(data: dict) -> str:
    lines = []
    add = lines.append
    add("Clase: la regla congelada (cuántos valores de la grilla sobreviven). Borde: cada lado por separado. "
        "«Identificado» sólo si la clase es WELL_CONSTRAINED y los dos lados los acotan las restricciones.\n")
    for basis, title in (("primary", "primario"), ("robust", "robusto")):
        add(f"**Conjunto {title}.**\n")
        add("| Parámetro | Grilla | Sobreviven | Clase | Lado inferior | Lado superior | Borde | Identificado |")
        add("|---|---|---|---|---|---|---|---|")
        for name, item in data["edges"][basis].items():
            add(f"| {name} | {', '.join(_value(v) for v in item['explored'])} | "
                f"{', '.join(_value(v) for v in item['left']) or '—'} | {CLASSES_ES[item['class']]} | "
                f"{SIDES_ES[item['lower_side']]} | {SIDES_ES[item['upper_side']]} | {item['edge'] or '—'} | "
                f"{'sí' if item['identified'] else 'no'} |")
        add("")
    return "\n".join(lines)


def render_trajectories(data: dict) -> str:
    lines = []
    add = lines.append
    add("Representativos (sobrevivientes primarios ordenados por el aporte inicial de 57m; bajo, medio y alto), con "
        "la sangre del representativo medio de P2I-2V-R y sangrado en curso. El volumen circulante, el gasto, la DO2 y "
        "el déficit son consecuencias secundarias: no filtran.\n")
    for tag in ("low", "middle", "high"):
        item = data["trajectories"]["sets"].get(tag)
        if not item:
            continue
        add(f"**{TAGS_ES[tag].capitalize()}: {_point(item['point'])}.**\n")
        for case in bc.CASES:
            for volume in ("1000", "2000"):
                t = item["trajectories"][case][volume]
                add(f"{SHORT[case]}, {int(volume) // 1000} L en 20 min: aporte inicial {_n(t['early_retained'])}; "
                    f"dilución pico {_n(t['peak_dilution'])} g/dL; reversión a los 120 min "
                    f"{_n(100 * t['reversal_fraction'], 0) if t['reversal_fraction'] is not None else '—'} %"
                    + ("" if t["stop"] is None else f"; se detiene en el {t['stop']}′") + ".\n")
                add("| Minuto | " + " | ".join(f"{r['minute']}′" for r in t["rows"]) + " |")
                add("|---|" + "---|" * len(t["rows"]))
                for key, name, digits in (("retained_share", "retenido (fracción)", 2), ("dilution", "dilución de Hb", 2),
                                          ("circulating_ml", "volumen circulante C", 0), ("output_rel", "gasto relativo", 2),
                                          ("do2", "DO2", 2), ("effective_deficit", "déficit crítico", 2),
                                          ("state", "estado de extracción", None)):
                    add(f"| {name} | " + " | ".join(STATES_ES.get(r[key], r[key]) if digits is None else _n(r[key], digits)
                                                  for r in t["rows"]) + " |")
                add("")
    return "\n".join(lines)


def render_state(data: dict) -> str:
    lines = []
    add = lines.append
    add("La misma exposición en cada posición compatible de cada caso: aumento máximo del gasto en los primeros 30 min "
        "(sobre el gasto de llegada).\n")
    add("| Representativo | Caso | Volumen | " + " | ".join(f"Posición {POSITIONS_ES[p]}" for p in POSITIONS_ES) + " |")
    add("|---|---|---|---|---|---|")
    for tag in ("low", "middle", "high"):
        item = data["trajectories"]["state_dependence"].get(tag)
        if not item:
            continue
        for case in bc.CASES:
            for volume in ("1000", "2000"):
                cells = []
                for label in POSITIONS_ES:
                    entry = item[case][label][volume]
                    gain = entry["peak_output_gain"]
                    cells.append(f"{_value(entry['position'])}: " + ("—" if gain is None else f"{_n(100 * gain, 0)} %")
                                 + ("" if entry["stop"] is None else f" (se detiene en el {entry['stop']}′)"))
                add(f"| {TAGS_ES[tag]} | {SHORT[case]} | {int(volume) // 1000} L | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


RENDERERS = {"tasa": render_rate, "cristaloide": render_crystalloid, "superficie": render_surface,
             "trayectorias": render_trajectories, "estado": render_state}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the fluid-calibration JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
