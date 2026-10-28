"""P2I-2W report: the generated blocks of docs/revision/P2I2W_EXTENSION_BORDES_AUDITORIA.md.

    python -m clinical_core.blood_extension_report --write <document> [--data <the extension JSON>]

Presentation only, outside the P2I-2W freeze (like blood_filter_report for P2I-2V-R): it reads the frozen
extension's JSON, the Level-1 registry and the historical-probe registry, and writes them in Spanish. It computes
no verdict.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import bands, calibration
from . import blood_constraints as bc
from . import blood_extension as be
from .blood_filter_report import CLASSES_ES, CONSTRAINTS_ES, PARAMETERS_ES, _n, _trajectory_table, _value

MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->")
           for name in ("regla", "auditoria", "extension")}
SHORT = {"gi_bleed_57m": "57m", "gi_bleed_72f": "72f"}
SPACING_ES = {be.ARITHMETIC: "diferencia constante", be.GEOMETRIC: "razón constante", be.AMBIGUOUS: "AMBIGUO"}
KIND_ES = {"base": "caja superviviente (P2I-2V-R)", "one": "un punto a la vez", "pair": "pares",
           "corner": "esquina de los primeros pasos"}
STRUCTURAL_ES = {"volume_preload_kappa": "sólo λ/κ llega a alguna ancla; la Hb nunca lee κ",
                 "preload_curve_scale_ml": "sólo λ/κ llega a alguna ancla",
                 "reserve": "sólo ρ × la razón de entrega de llegada llega a D y al déficit; ninguna restricción lo lee"}
EDGES_ES = {be.INTERIOR: "INTERIOR", be.OPEN_LOWER: "OPEN_LOWER_GRID_EDGE", be.OPEN_UPPER: "OPEN_UPPER_GRID_EDGE",
            be.OPEN_BOTH: "OPEN_BOTH_GRID_EDGES", None: "—"}
#: The Level-1 audit in Spanish, one entry per LEVEL1_DIRECT_WRITES row (a test keeps them in step).
AUDIT_ES = {
    "RR1": ("V −8 por minuto durante 40 min y +900 en el minuto 40, desde la llegada sintética de las sondas",
            "un shock genérico y su corrección sobre la coordenada de precarga, para comprobar que aclarar el lactato "
            "no lleva la FR bajo su piso ventilatorio; sin caso GI, sin GR, sin relleno y sin cambio de Hb"),
    "HR1-HR4": ("V −8 por minuto durante 30 min y +640 en el minuto 30, desde la llegada declarada de cada caso GI",
                "las reglas son la respuesta cronotrópica al deterioro y a la recuperación hemodinámicos (KD-S2, "
                "P2E-1, P2D-3) y leen sólo la FC y el impulso simpático. La pérdida mueve sólo V (sin GR, sin "
                "relleno, Hb sin cambio) y la reposición no es ningún producto: es una perturbación hipovolémica de "
                "la coordenada de precarga, no una hemorragia. Pasarla por BloodState exigiría valores de relleno y "
                "de volumen de llegada que no están aprobados"),
    "PL1-PL3": ("V fijada en 0, 250, 500 y 750 en el minuto 0 de la llegada neutra (lecturas estáticas)",
                "lee la forma de la curva de precarga y el límite que pone una bomba deprimida; sin pérdida ni producto"),
    "PL4": ("V +2900 en el primer minuto, desde una llegada sintética con reserva de bomba 0,3",
            "alcanzabilidad del agua pulmonar con exceso de precarga y reserva limitada: una carga de volumen, no un "
            "producto (la cinética del cristaloide no está aprobada) ni una hemorragia"),
    "DM1": ("Hb −30 % en el minuto 0 de la llegada neutra",
            "una anemia aislada que fija la entrega mientras cambia la demanda; no hay pérdida de sangre"),
}


def _label(label: str) -> str:
    parameter, case = be._parameter(label)
    if label == be.COMMON:
        return "tasa de sangrado común (mL-eq/min)"
    name = PARAMETERS_ES.get(parameter, parameter)
    return f"{name} ({SHORT[case]})" if case else name


def _values(values) -> str:
    return ", ".join(_value(v) for v in values) if values else "—"


def _fixed(fixed: dict) -> str:
    return " · ".join(f"{_label(label)} = {_value(value)}" for label, value in fixed.items()) or "—"


def _reason_es(a: str, b: str) -> str:
    (pa, ca), (pb, cb) = be._parameter(a), be._parameter(b)
    if ca and cb and ca != cb:
        return "ninguna restricción las lee a la vez (cada caso se lee solo); el sobreviviente conjunto necesita ambos"
    return "las leen a la vez: " + ", ".join(sorted(be._reads(pa) & be._reads(pb)))


def render_rule(data: dict) -> str:
    lines = []
    add = lines.append
    add(f"Congelamiento de P2I-2W: `{data['freeze_digest']}`, con un commit hecho antes de evaluar ningún candidato "
        f"extendido (una prueba lo fija). Registro de partida: el filtro de P2I-2V-R, `{data['record_digest']}`.\n")
    add("| Dimensión abierta en P2I-2V-R | Explorados | Sobreviven | Lado abierto | Espaciado | Paso | Puntos de "
        "extensión | Descartados (fuera del dominio) |")
    add("|---|---|---|---|---|---|---|---|")
    for label, item in data["extension"].items():
        step = "—" if item["step"] is None else (f"× {_value(item['step'])}" if item["spacing"] == be.GEOMETRIC
                                                 else f"+ {_value(item['step'])}")
        add(f"| {_label(label)} | {_values(item['explored'])} | {_values(item['surviving'])} | "
            f"{'superior' if item['side'] == 'upper' else item['side']} | {SPACING_ES[item['spacing']]} | {step} | "
            f"{_values(item['points'])} | {_values(item['dropped'])} |")
    add("")
    for label, item in data["extension"].items():
        if item["spacing"] == be.AMBIGUOUS:
            options = "; ".join(f"{'por la última diferencia' if 'difference' in way else 'por la última razón'}: "
                                f"{_values(points)}" for way, points in item["not_evaluated"].items())
            add(f"**{_label(label)}: continuación AMBIGUA, sin extender.** Los valores explorados "
                f"({_values(item['explored'])}) no tienen una diferencia ni una razón constantes. Las dos "
                f"continuaciones simples dan valores distintos ({options}). No se eligió ninguna ni se evaluó: "
                f"queda para una decisión docente.\n")
    boxes = data["design"]
    add("| Parte del diseño | Cajas | Candidatos |")
    add("|---|---|---|")
    for kind in ("base", "one", "pair", "corner"):
        chosen = [box for box in boxes if box["kind"] == kind]
        add(f"| {KIND_ES[kind]} | {len(chosen)} | {_n(sum(box['size'] for box in chosen), 0)} |")
    add(f"| **extendidos (sin la caja superviviente)** | {len(boxes) - 1} | "
        f"{_n(data['candidates']['extended'], 0)} |")
    add("")
    add("Pares combinados y por qué:\n")
    seen = set()
    for box in boxes:
        if box["kind"] == "pair":
            pair = tuple(box["fixed"])
            if pair not in seen:
                seen.add(pair)
                add(f"- {_label(pair[0])} × {_label(pair[1])}: {_reason_es(*pair)}.")
    return "\n".join(lines)


def render_audit() -> str:
    lines = []
    add = lines.append
    add("| Comprobación | Escribe | Cómo | Clase | Por qué |")
    add("|---|---|---|---|---|")
    for name, entry in calibration.LEVEL1_DIRECT_WRITES.items():
        how, why = AUDIT_ES[name]
        add(f"| {name} (`{entry['function']}`) | {entry['writes']} | {how} | {entry['semantics']} | {why} |")
    add("")
    add("Ninguna es PHYSIOLOGICAL_HAEMORRHAGE_PROBE, así que ninguna se convierte a BloodState. Todas siguen "
        "escribiendo la coordenada de forma directa, rotuladas, y no son evidencia sobre la fisiología de la "
        f"hemorragia, la Hb ni la DO2 (`NOT_EVIDENCE_FOR` = {', '.join(calibration.NOT_EVIDENCE_FOR)}).\n")
    add("| Sonda histórica de nivel 2 | Familia | Estado |")
    add("|---|---|---|")
    for name, (family, *_rest) in bands.HISTORICAL_PROBES.items():
        add(f"| `{name}` | {family} | {bands.HISTORICAL_PROBE}: fuera de `bands.PROBES`, de las bandas y de la tabla "
            f"del arnés; no la lee ningún filtro |")
    return "\n".join(lines)


def _failing(stats: dict) -> str:
    items = sorted(((n, c) for n, c in stats["failing"].items() if c), key=lambda item: -item[1])
    return " · ".join(f"{name} {_n(count, 0)}" + (f" (sola {_n(stats['sole'][name], 0)})" if stats["sole"][name]
                                                   else "") for name, count in items) or "—"


def _details(stats: dict) -> str:
    out = []
    for case in bc.CASES:
        for name, where in stats["details"][case].items():
            parts = ", ".join(f"{item.replace('below', 'bajo').replace('above', 'sobre')} ({count})"
                              for item, count in sorted(where.items()))
            out.append(f"{SHORT[case]} {name}: {parts}")
    return "; ".join(out) or "—"


def _envelope(item) -> str:
    if not item:
        return "—"
    return f"{_n(item['min'])}–{_n(item['max'])}"


def render_extension(data: dict) -> str:
    lines = []
    add = lines.append
    base = data["boxes"]["base"]
    add(f"La caja superviviente reproduce el filtro congelado: {_n(base['survives'], 0)} sobrevivientes con la tasa "
        f"común, los mismos de P2I-2V-R (la corrida se detiene si no). Filas ilegibles: "
        f"{_n(sum(data['unreadable_rows'].values()), 0)}. Contradicciones en las comprobaciones cruzadas: "
        f"{len(data['contradictions'])}.\n")
    add("### Resultado por caja\n")
    add("Sobreviviente conjunto: tasa común (lectura primaria). «Sólo 57m» y «sólo 72f»: cada caso por separado, "
        "como sensibilidad (qué tolera cada caso con su propia tasa; no es el recuento conjunto V8 de P2I-2V-R); entre "
        "paréntesis, los candidatos de ese caso que quedan ILEGIBLES (ninguna restricción legible falla, pero alguna "
        "no se puede leer), que no son un rechazo. «Ilegibles»: candidatos conjuntos ilegibles. Rechazos: cuántos "
        "candidatos falla cada restricción en algún caso (entre paréntesis, en cuántos es la única que falla).\n")
    add("| Caja | Candidatos | Sobreviven | Sólo 57m | Sólo 72f | Ilegibles | Rechazos |")
    add("|---|---|---|---|---|---|---|")
    order = [box["name"] for box in data["design"]]
    for name in order:
        stats = data["boxes"][name]
        title = "caja superviviente" if stats["kind"] == "base" else _fixed(stats["fixed"])
        alone = [_n(stats["alone"][case], 0) + (f" (+{_n(stats['alone_unreadable'][case], 0)} ilegibles)"
                                                if stats["alone_unreadable"][case] else "") for case in bc.CASES]
        add(f"| {title} | {_n(stats['size'], 0)} | {_n(stats['survives'], 0)} | {alone[0]} | {alone[1]} | "
            f"{_n(stats['unreadable'], 0)} | {_failing(stats)} |")
    add("")
    add("### Dónde salen de su envolvente U-OUT, U-HB y FD-BLD-07 (un punto a la vez)\n")
    add("Filas distintas que fallan, por minuto y lado («bajo»: por debajo del mínimo; «sobre»: por encima del "
        "máximo).\n")
    add("| Caja | Detalle |")
    add("|---|---|")
    for name in order:
        stats = data["boxes"][name]
        if stats["kind"] == "one":
            add(f"| {_fixed(stats['fixed'])} | {_details(stats)} |")
    add("")
    add("### Lo que leen las restricciones en cada punto (filas de su caja; contexto, nada se ajusta)\n")
    add("| Punto | Caso | Gasto sin tratar 30′ / 60′ / 120′ | Caída de Hb 60′ / 120′ | Relleno 60′ / 120′ / 240′ | "
        "1 U: Δ gasto | 2.ª U: Δ gasto | Dilución pico 1 L |")
    add("|---|---|---|---|---|---|---|---|")
    for point in [f"{label}={value:g}" for label, item in data["extension"].items() for value in item["points"]]:
        cases = data["metrics"][point]
        label, _, value = point.rpartition("=")
        for case, m in cases.items():
            add(f"| {_label(label)} = {_value(value)} | {SHORT[case]} | "
                + " / ".join(_envelope(m["untreated_output"][str(k)]) for k in bc.MINUTES_OUTPUT) + " | "
                + " / ".join(_envelope(m["untreated_hb_fall"][str(k)]) for k in bc.MINUTES_HB) + " | "
                + " / ".join(_envelope(m["refill_share"][str(k)]) for k in bc.REFILL_MINUTES) + " | "
                + f"{_envelope(m['one_unit_relative_output_gain'])} | {_envelope(m['second_unit_gain'])} | "
                + f"{_envelope(m['crystalloid_peak_dilution']['1000'])} |")
    add("")
    add("### Identificabilidad y estado de borde, antes y después\n")
    add("Clase: la regla congelada de P2I-2V-R (cuántos valores explorados sobreviven). Borde: si sobrevive el valor "
        "explorado más bajo o el más alto. Son dos lecturas distintas: un solo valor superviviente en el borde es "
        "WELL_CONSTRAINED por recuento, pero no está identificado.\n")
    add("| Parámetro | Explorados | Sobreviven | Clase antes → después | Borde antes → después | Nota |")
    add("|---|---|---|---|---|---|")
    for label in (*be.COORDS, *(name for name in bc.STRUCTURAL if name not in be.COORDS)):
        item = data["edges"][label]
        if "before" not in item:
            add(f"| {_label(label)} | — | — | {CLASSES_ES[item['class']]} | — | {STRUCTURAL_ES[label]} |")
            continue
        before = item["before"]
        note = []
        if label in data["extension"] and not item["extended"]:
            note.append("continuación ambigua: sin extender")
        elif item["extended"]:
            note.append(f"extendido: {_values(item['extended'])}")
        elif before["edge"] in (be.OPEN_BOTH, be.OPEN_LOWER, be.OPEN_UPPER):
            note.append("no señalado abierto en P2I-2V-R: sin extender")
        if item["at_domain_limit"]:
            note.append("el valor más alto que sobrevive es el límite del dominio")
        if label in bc.STRUCTURAL:
            note.append(STRUCTURAL_ES[label])
        add(f"| {_label(label)} | {_values(item['explored'])} | {_values(item['left'])} | "
            f"{CLASSES_ES[before['class']]} → {CLASSES_ES[item['class']]} | {EDGES_ES[before['edge']]} → "
            f"{EDGES_ES[item['edge']]} | {'; '.join(note) or '—'} |")
    add("")
    add("### Representativos de P2I-2V-R movidos a cada punto\n")
    add("Los tres representativos de P2I-2V-R (bajo, medio y alto, por su regla congelada), con sólo la coordenada "
        "extendida cambiada. Se muestra el medio; la PAS y el lactato son sólo contexto.\n")
    surfaces = {be.COMMON: ("untreated", "crystalloid_1000", "stopped_bleed"),
                "plasma_refill_target_share": ("untreated", "crystalloid_1000", "stopped_bleed"),
                "plasma_refill_tau_min": ("untreated", "crystalloid_1000", "stopped_bleed")}
    titles = {"untreated": "Sin tratar", "red_cells": "GR, sangrado controlado", "crystalloid_1000":
              "1 L en 20 min con sangrado", "stopped_bleed": "Hemostasia a los 60 min"}
    points = [f"{label}={value:g}" for label, item in data["extension"].items() for value in item["points"]]
    for point in points:
        item = data["representatives"][point]
        label, _, value = point.rpartition("=")
        add(f"**{_label(label)} = {_value(value)}.**\n")
        for tag in ("low", "middle", "high"):
            entry = item[tag]
            verdicts = []
            for case in bc.CASES:
                failing = [n for n in bc.CONSTRAINTS if entry["verdicts"][case][n] is False]
                unread = [n for n in bc.CONSTRAINTS if entry["verdicts"][case][n] is None]
                verdicts.append(f"{SHORT[case]}: " + ("cumple todas" if not failing and not unread else
                                                      ("no cumple " + ", ".join(failing) if failing else "")
                                                      + (" (ilegible: " + ", ".join(unread) + ")" if unread else "")))
            add(f"- {({'low': 'bajo', 'middle': 'medio', 'high': 'alto'})[tag]}: " + "; ".join(verdicts) + ".")
        add("")
        middle = item["middle"]
        for case in bc.CASES:
            t = middle["trajectories"][case]
            if be.UNREADABLE in t:
                add(f"{SHORT[case]}: trayectoria ilegible ({t[be.UNREADABLE]}).\n")
                continue
            parameter, case_of = be._parameter(label)
            if case_of and case_of != case:
                continue
            chosen = surfaces.get(label, ("untreated", "red_cells", "crystalloid_1000"))
            for surface in chosen:
                rows = t[surface]["rows"]
                stop = t[surface].get("stop")
                heading = f"{SHORT[case]} · {titles[surface]}" + ("" if stop is None else f" (se detiene en el {stop}′)")
                lines.extend(_trajectory_table(rows, heading, ["antes", "tras 1 U", "tras 2 U"]
                                               if surface == "red_cells" else None))
                add("")
    if data["unreadable_messages"]:
        add("### Filas ilegibles\n")
        add("| Caso y tabla | Filas |")
        add("|---|---|")
        for key, count in data["unreadable_rows"].items():
            if count:
                add(f"| {key} | {_n(count, 0)} |")
        add("")
        add("Mensajes (hasta 20): " + "; ".join(f"`{message}`" for message in data["unreadable_messages"]) + "\n")
    return "\n".join(lines)


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, help="the extension JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    document = apply(document, "auditoria", render_audit())
    if args.data:
        data = json.loads(args.data.read_text(encoding="utf-8"))
        document = apply(document, "regla", render_rule(data))
        document = apply(document, "extension", render_extension(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
