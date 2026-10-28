"""P2I-2X report: the generated blocks of docs/revision/P2I2X_CIERRE_BORDES_TASA.md.

    python -m clinical_core.blood_rate_report --write <document> [--data <the rate-boundary JSON>]

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
scan's JSON and the current Level-1 registry and writes them in Spanish. It computes no verdict.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import blood_constraints as bc
from . import blood_extension as be
from . import blood_rate_boundary as rb
from .blood_extension_report import SHORT, STRUCTURAL_ES, _values, render_audit
from .blood_extension_report import _label as _base_label
from .blood_filter_report import CLASSES_ES, _n, _value

MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->")
           for name in ("verdad", "tasa", "representativos", "bordes", "auditoria")}
SIDES_ES = {"CONSTRAINED": "acotado por restricción", "OPEN": "abierto (borde de la cuadrícula)",
            "DOMAIN": "límite del dominio", "CASE_TRUTH": "verdad del caso", None: "—"}
TAGS_ES = {"low": "bajo", "middle": "medio", "high": "alto"}
#: P2I-2X-2: the crystalloid parameter is the initial intravascular fraction, not the retained one.
LABELS_ES = {"crystalloid_effective_ml_per_ml": "fracción intravascular inicial del cristaloide"}


def _label(label: str) -> str:
    return LABELS_ES.get(label, _base_label(label))
NAMES_ES = {be.COMMON: "tasa", be.POSITION["gi_bleed_57m"]: "57m", be.POSITION["gi_bleed_72f"]: "72f",
            "plasma_refill_target_share": "meta", "plasma_refill_tau_min": "τ"}
STATES_ES = {"ADEQUATE": "adecuada", "COMPENSATED": "compensada", "CRITICAL": "crítica"}


def _env(item, digits: int = 2) -> str:
    return "—" if not item else f"{_n(item['min'], digits)}–{_n(item['max'], digits)}"


def render_truth(data: dict) -> str:
    lines = []
    add = lines.append
    add("| Caso | Verdad del repositorio (POCUS) | Banda candidata comprometida | Referencia euvolémica |")
    add("|---|---|---|---|")
    for case in bc.CASES:
        item = data["case_truth"][case]
        truth = "; ".join(f"{t['item']}: «{t['value']}» (`{t['source']}`)" for t in item["repository_truth"])
        band = item["candidate_band"]
        add(f"| {SHORT[case]} | {truth} | {_value(band['lower'])}–{_value(band['upper'])} (medio "
            f"{_value(band['midpoint'])}); inferencia candidata | {_value(item['euvolaemic_reference']['lower'])}–"
            f"{_value(item['euvolaemic_reference']['upper'])} |")
    add("")
    add("Cajas de P2I-2W con una posición fuera de la banda del caso: sus candidatos quedan "
        f"`{rb.REJECTED_BY_CASE_TRUTH}` sin simular.\n")
    add("| Caja de P2I-2W | Caso fuera de banda | Sobrevivientes conjuntos | Sobrevivientes de cada caso solo "
        "(P2I-2W) |")
    add("|---|---|---|---|")
    total = 0
    for name, item in sorted(data["p2i2w_case_truth"].items()):
        total += item["survives"]
        fixed = ("esquina (todos los primeros pasos)" if name.startswith("corner") else
                 " · ".join(f"{NAMES_ES[label]} = {_value(value)}" for label, value in
                            (part.rsplit("=", 1) for part in name.split(" & "))))
        add(f"| {fixed} | {', '.join(SHORT[c] for c in item['outside'])} | {_n(item['survives'], 0)} | "
            + ", ".join(f"{SHORT[c]} {_n(n, 0)}" for c, n in item["alone"].items()) + " |")
    add("")
    add(f"En total, {_n(total, 0)} sobrevivientes conjuntos de P2I-2W quedan rechazados por compatibilidad con la "
        "verdad del caso.")
    return "\n".join(lines)


def render_rate(data: dict) -> str:
    lines = []
    add = lines.append
    scan, design = data["scan"], data["design"]
    add(f"Congelamiento de P2I-2X: `{data['freeze_digest']}`, comprometido antes de evaluar 6, 7, 8 y 9 (una prueba lo "
        f"fija). Registros: P2I-2V-R `{data['records']['P2I-2V-R']}`, P2I-2W `{data['records']['P2I-2W']}`.\n")
    add(f"Región: la superviviente de P2I-2V-R, con 57m en {_value(scan['positions']['gi_bleed_57m'])} y 72f en "
        f"{_value(scan['positions']['gi_bleed_72f'])}: {_n(scan['candidates'], 0)} candidatos conjuntos por tasa. "
        f"El prefiltro exacto (restricciones que no dependen de la tasa: {', '.join(design['rate_independent'])}) "
        f"rechaza {_n(scan['rate_independent_rejected'], 0)} sin simular ninguna tasa; se simulan "
        f"{_n(scan['candidates'] - scan['rate_independent_rejected'], 0)} por tasa.\n")
    add("«57m tras el prefiltro» y «72f tras el prefiltro»: cada caso por separado, pero sólo entre los candidatos "
        "que pasan el prefiltro exacto de los dos casos (sensibilidad acotada, no el recuento de cada caso con su propio "
        "prefiltro).\n")
    add("| Tasa (mL-eq/min) | Candidatos | Rechazo exacto | Simulados | Falla U-OUT 57m | Falla U-OUT 72f | "
        "Sobreviven | 57m tras el prefiltro | 72f tras el prefiltro | Ilegibles |")
    add("|---|---|---|---|---|---|---|---|---|---|")
    for rate in data["design"]["rates"]:
        item = scan["rates"][str(rate)]
        alone = [_n(item["alone"][c], 0) + (f" (+{_n(item['alone_unreadable'][c], 0)} ilegibles)"
                                            if item["alone_unreadable"][c] else "") for c in bc.CASES]
        new = "" if rate not in data["design"]["new_rates"] else " (nueva)"
        add(f"| {_value(rate)}{new} | {_n(item['candidates'], 0)} | {_n(scan['rate_independent_rejected'], 0)} | "
            f"{_n(item['simulated'], 0)} | {_n(item['u_out_fail']['gi_bleed_57m'], 0)} | "
            f"{_n(item['u_out_fail']['gi_bleed_72f'], 0)} | {_n(item['survives'], 0)} | {alone[0]} | {alone[1]} | "
            f"{_n(item['unreadable'], 0)} |")
    add("")
    add("Primera restricción que falla, por caso (entre los simulados), y dónde sale U-OUT de su envolvente (filas "
        "distintas, por minuto y lado):\n")
    add("| Tasa | 57m: primera falla | 72f: primera falla | U-OUT 57m | U-OUT 72f |")
    add("|---|---|---|---|---|")
    for rate in data["design"]["rates"]:
        item = scan["rates"][str(rate)]
        first = [" · ".join(f"{n} {_n(c, 0)}" for n, c in sorted(item["first_failure"][case].items(),
                                                                  key=lambda x: -x[1])) or "—" for case in bc.CASES]
        detail = [", ".join(f"{k.replace('below', 'bajo').replace('above', 'sobre')} ({v})"
                            for k, v in sorted(item["u_out_detail"][case].items())) or "—" for case in bc.CASES]
        add(f"| {_value(rate)} | {first[0]} | {first[1]} | {detail[0]} | {detail[1]} |")
    add("")
    add("Envolventes de los sobrevivientes (los dos casos juntos):\n")
    add("| Tasa | Gasto sin tratar 30′ / 60′ / 120′ | Caída de Hb 60′ / 120′ |")
    add("|---|---|---|")
    for rate in data["design"]["rates"]:
        item = scan["rates"][str(rate)]
        add(f"| {_value(rate)} | " + " / ".join(_env(item["survivor_output"][str(m)]) for m in bc.MINUTES_OUTPUT)
            + " | " + " / ".join(_env(item["survivor_hb_fall"][str(m)]) for m in bc.MINUTES_HB) + " |")
    add("")
    interval = data["interval"]
    add(f"**{interval['label']}.** Tasa más alta con al menos un sobreviviente conjunto: "
        f"{_value(interval['highest_with_survivor']) if interval['highest_with_survivor'] is not None else '—'}. "
        f"Tasa más baja sin sobreviviente conjunto: "
        f"{_value(interval['lowest_without_survivor']) if interval['lowest_without_survivor'] is not None else '—'}. "
        + ("El límite queda entre dos tasas probadas contiguas. " if interval["boundary_between_adjacent_tested_rates"]
           else "El límite no queda entre dos tasas probadas contiguas. ")
        + ("Los sobrevivientes no crecen con la tasa." if interval["monotone_survivor_counts"]
           else "Los sobrevivientes no son monótonos en la tasa.")
        + " No es un valor aprobado ni se interpola.\n")
    add("Las otras posiciones de cada banda, para cada caso solo (un sobreviviente conjunto necesita los dos casos):\n")
    add("| Caso y posición | Candidatos por tasa | Rechazo exacto | " + " | ".join(f"Tasa {_value(r)}: cumple / falla "
                                                                         f"U-OUT" for r in data["design"]["rates"]) + " |")
    add("|---|---|---|" + "---|" * len(data["design"]["rates"]))
    for key, entry in data["targeted"].items():
        case, label = key.split("|")
        cells = [f"{_n(entry['rates'][str(r)]['pass'], 0)} / {_n(entry['rates'][str(r)]['u_out_fail'], 0)}"
                 + (f" (+{_n(entry['rates'][str(r)]['unreadable'], 0)} ilegibles)"
                    if entry["rates"][str(r)]["unreadable"] else "") for r in data["design"]["rates"]]
        add(f"| {SHORT[case]} {_value(entry['position'])} ({'inf.' if label == 'lower' else 'medio'}) | "
            f"{_n(entry['candidates_per_rate'], 0)} | {_n(entry['rate_independent_rejected'], 0)} | "
            + " | ".join(cells) + " |")
    add("")
    add(f"Filas calculadas: {_n(data['rows_computed'], 0)}. Filas ilegibles: "
        f"{_n(sum(data['unreadable_rows'].values()), 0)}. Contradicciones en las comprobaciones cruzadas: "
        f"{len(data['contradictions'])}.")
    return "\n".join(lines)


def render_representatives(data: dict) -> str:
    lines = []
    add = lines.append
    add("Los tres representativos de P2I-2V-R (su regla congelada), con sólo la tasa cambiada. Se muestra el medio; "
        "la PAS y el lactato no se leen.\n")
    for rate in data["design"]["rates"]:
        item = data["representatives"][str(rate)]
        verdicts = []
        for tag in ("low", "middle", "high"):
            parts = []
            for case in bc.CASES:
                failing = [n for n in bc.CONSTRAINTS if item[tag]["verdicts"][case][n] is False]
                unread = [n for n in bc.CONSTRAINTS if item[tag]["verdicts"][case][n] is None]
                parts.append(f"{SHORT[case]} " + ("cumple todas" if not failing and not unread else
                                                  ("no cumple " + ", ".join(failing) if failing else "")
                                                  + (" (ilegible: " + ", ".join(unread) + ")" if unread else "")))
            verdicts.append(f"{TAGS_ES[tag]}: " + "; ".join(parts))
        add(f"**Tasa {_value(rate)}.** " + " · ".join(verdicts) + ".\n")
        add("| Medio, sin tratar | " + " | ".join(f"{SHORT[c]} {m}′" for c in bc.CASES for m in (0, 30, 60, 120)) + " |")
        add("|---|" + "---|" * 8)
        rows = {c: item["middle"]["rows"][c]["rows"] for c in bc.CASES}
        for key, name, digits in (("output_rel", "gasto relativo", 2), ("hb", "Hb (g/dL)", 2),
                                  ("circulating_ml", "volumen circulante C (mL-eq)", 0), ("do2", "DO2", 2),
                                  ("effective_deficit", "déficit crítico efectivo", 2), ("state", "estado de extracción", None)):
            cells = []
            for case in bc.CASES:
                for minute in (0, 30, 60, 120):
                    row = next((r for r in rows[case] if r["minute"] == minute), None)
                    cells.append("—" if row is None else STATES_ES.get(row[key], row[key]) if digits is None
                                 else _n(row[key], digits))
            add(f"| {name} | " + " | ".join(cells) + " |")
        add("")
    return "\n".join(lines)


def render_edges(data: dict) -> str:
    lines = []
    add = lines.append
    add("Clase: la regla congelada (cuántos valores explorados compatibles sobreviven). Borde: cada lado por "
        "separado y su estado. «Identificado» sólo si la clase es WELL_CONSTRAINED y los dos lados los acotan las "
        "restricciones docentes.\n")
    add("| Parámetro | Explorados | Sobreviven | Clase | Lado inferior | Lado superior | Borde | Identificado |")
    add("|---|---|---|---|---|---|---|---|")
    for label in (*be.COORDS, *(name for name in bc.STRUCTURAL if name not in be.COORDS)):
        item = data["edges"][label]
        if "explored" not in item:
            add(f"| {_label(label)} | — | — | {CLASSES_ES[item['class']]} | — | — | — | no ({STRUCTURAL_ES[label]}) |")
            continue
        add(f"| {_label(label)} | {_values(item['explored'])} | {_values(item['left'])} | {CLASSES_ES[item['class']]} | "
            f"{SIDES_ES[item['lower_side']]} | {SIDES_ES[item['upper_side']]} | {item['edge']} | "
            f"{'sí' if item['identified'] else 'no'} |")
    return "\n".join(lines)


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, help="the rate-boundary JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    document = apply(document, "auditoria", render_audit())
    if args.data:
        data = json.loads(args.data.read_text(encoding="utf-8"))
        for name, render in (("verdad", render_truth), ("tasa", render_rate), ("representativos",
                             render_representatives), ("bordes", render_edges)):
            document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
