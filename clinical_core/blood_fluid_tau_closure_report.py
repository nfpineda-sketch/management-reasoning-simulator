"""P2I-2AA report: the generated blocks of docs/revision/P2I2AA_CIERRE_TAU_Y_SEMANTICA_LACTATO.md.

    python -m clinical_core.blood_fluid_tau_closure_report --write <document> --data <the tau-closure JSON>

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
from .blood_fluid_readiness_report import CRITERIA_ES as BASE_CRITERIA_ES, YES, _blood, _point
from .blood_fluid_report import SIDES_ES
from .blood_fluid_tau_closure import rate25_keys

MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->")
           for name in ("tau", "region", "practico", "semantica", "claves", "preparacion", "espacio")}
CRITERIA_ES = {**{k: v for k, v in BASE_CRITERIA_ES.items() if k not in (
    "bleed-rate boundary characterized", "crystalloid candidate region characterized")},
    "bleed-rate support characterized (2.5, 5, 6)": "soporte de la tasa de sangrado caracterizado (2,5, 5 y 6)",
    "crystalloid candidate support characterized": "soporte candidato del cristaloide caracterizado",
    "oxygen adequacy semantics locked": "semántica de la adecuación del oxígeno fijada"}
ORDER = ("shared BloodState active", "DO2 / extraction model current", "case-compatible preload region defined",
         "bleed-rate support characterized (2.5, 5, 6)", "crystalloid candidate support characterized",
         "no stale active haemorrhage probe bypasses BloodState",
         "hidden parameters unapproved, candidate support explicit", "oxygen adequacy semantics locked")
MARGINS_ES = {"FD-BLD-04": "FD-BLD-04 (aporte inicial)", "FD-BLD-05 30": "FD-BLD-05 a los 30′",
              "FD-BLD-05 60": "FD-BLD-05 a los 60′", "FD-BLD-05 120": "FD-BLD-05 a los 120′",
              "FD-BLD-06 1000": "FD-BLD-06 pico con 1 L", "FD-BLD-06 2000": "FD-BLD-06 pico con 2 L",
              "FD-BLD-06 1000 partial reversal": "FD-BLD-06 reversión parcial con 1 L",
              "FD-BLD-06 2000 partial reversal": "FD-BLD-06 reversión parcial con 2 L"}
FIELDS_ES = {"retained_share": "retenido", "dilution": "dilución de Hb (g/dL)", "output_rel": "gasto relativo",
             "do2": "DO2", "effective_deficit": "déficit crítico"}
SOURCES_ES = {"P2I-2V-R joint survivors (refill target <= 0.75, tau <= 240)":
                  "sobrevivientes conjuntos de P2I-2V-R (meta del relleno ≤ 0,75; τ ≤ 240)",
              "P2I-2V-R joint survivors and P2I-2W's in-band extension boxes (refill target 1.0; target 1.0 with tau "
              "480)": "sobrevivientes conjuntos de P2I-2V-R y de las cajas de extensión de P2I-2W dentro de la banda "
                      "(meta del relleno 1,0; 1,0 con τ 480)",
              "P2I-2Y joint survivors (with the refill extension)":
                  "sobrevivientes conjuntos de P2I-2Y (con la extensión del relleno)"}
STATUS_ES = {"CERTIFIED_SOURCE_SPACE (not executed)": "ESPACIO DE ORIGEN CERTIFICADO (sin ejecutar)",
             "DRAFT — NOT EXECUTABLE UNTIL BLOOD/FLUID READINESS = READY":
                 "DRAFT — NOT EXECUTABLE UNTIL BLOOD/FLUID READINESS = READY (borrador: no se ejecuta)"}


def _key(point: dict) -> str:
    return f"{point['F0']:g}|{point['Finf']:g}|{point['tau']:g}"


def render_tau(data: dict) -> str:
    lines = []
    add = lines.append
    add(f"Congelamiento de P2I-2AA: `{data['freeze_digest']}`, comprometido antes de evaluar (una prueba lo fija). "
        f"Registros de partida: P2I-2Z `{data['record']['P2I-2Z']}`, P2I-2Y `{data['record']['P2I-2Y']}`.\n")
    add("Diseño: F0 0,2; Finf 0,05 y 0,1; τ 120, 150, 180, 210 y 240 min (10 puntos; τ 120 reproduce P2I-2Z; nada por "
        "encima de 240). Criterio robusto de P2I-2Z: FD-BLD-06 en las 48 claves de sangre, en los dos casos.\n")
    add("| Punto | FD-BLD-04 | FD-BLD-05 | FD-BLD-06 referencia | FD-BLD-06 todas las sondas | FD-BLD-06 todas las claves "
        "certificadas | Robusto | Aporte inicial | Retenido 30′ / 60′ / 120′ |")
    add("|---|---|---|---|---|---|---|---|---|")
    for point in data["design"]:
        key = _key(point)
        item, entry = data["classified"][key], data["evaluated"][key]
        share = entry["readings"]["gi_bleed_57m"]["share"]
        add(f"| {_point(key)} | {YES[item['FD-BLD-04']]} | {YES[item['FD-BLD-05']]} | {YES[item['FD-BLD-06 reference']]} | "
            f"{YES[item['FD-BLD-06 every probe']]} | {YES[item['FD-BLD-06 every certified key']]} | "
            f"**{'sí' if item['robust'] else 'no'}** | {_n(entry['readings']['gi_bleed_57m']['early'], 3)} | "
            f"{_n(share['30'], 3)} / {_n(share['60'], 3)} / {_n(share['120'], 3)} |")
    add("")
    b = data["boundary"]
    add("| Finf | τ con sobreviviente robusto | Mayor τ que sobrevive | Primer τ sin sobreviviente |")
    add("|---|---|---|---|")
    for finf, item in b["per_finf"].items():
        add(f"| {_value(finf)} | {', '.join(_value(t) for t in item['surviving']) or 'ninguno'} | "
            f"{_value(item['highest']) if item['highest'] is not None else '—'} | "
            f"{_value(item['first_failing']) if item['first_failing'] is not None else 'ninguno'} |")
    add("")
    add(f"Mayor τ con sobreviviente: **{_value(b['highest_surviving'])}**. Primer τ probado sin sobreviviente: "
        f"**{_value(b['first_without_survivor']) if b['first_without_survivor'] is not None else 'ninguno'}**. "
        f"Clasificación: **{b['status']}**."
        + (" La extensión se detiene: nada por encima de 240 sin decisión docente." if b["stop"] else ""))
    return "\n".join(lines)


def render_region(data: dict) -> str:
    lines = []
    add = lines.append
    add(f"Soporte candidato (puntos activos, Finf < F0): {', '.join(_point(k) for k in data['region'])}.\n")
    add("| Parámetro | Explorado | Soporte candidato | Clase | Lado inferior | Lado superior | Borde | "
        "Identificado (regla congelada) |")
    add("|---|---|---|---|---|---|---|---|")
    for name, item in data["edges"].items():
        add(f"| {name} | {', '.join(_value(v) for v in item['explored'])} | "
            f"{', '.join(_value(v) for v in item['left']) or '—'} | {CLASSES_ES[item['class']]} | "
            f"{SIDES_ES[item['lower_side']]} | {SIDES_ES[item['upper_side']]} | {item['edge'] or '—'} | "
            f"{'sí' if item['identified'] else 'no'} |")
    return "\n".join(lines)


def render_practical(data: dict) -> str:
    lines = []
    add = lines.append
    p = data["practical"]
    add(f"Identificabilidad estructural: {p['structural'].replace(' when ', ' cuando ')}. Clasificación práctica (horizonte de 120 min, frente a las "
        f"restricciones docentes): **{p['classification']}**.\n")
    add("| Margen con τ 240 (distancia al borde más cercano) | " + " | ".join(f"Finf {_value(f)}" for f in p["per_finf"])
        + " | Límite τ → ∞ (Finf = F0, sólo referencia) |")
    add("|---|" + "---|" * (len(p["per_finf"]) + 1))
    for name, label in MARGINS_ES.items():
        add(f"| {label} | " + " | ".join(_n(item["margins_at_240"][name], 3) for item in p["per_finf"].values())
            + f" | {_n(p['limit']['margins'][name], 3)} |")
    add("")
    add("| Finf | Monótono en τ | Mayor cambio 210 → 240 (retenido) | Mayor cambio 210 → 240 (cualquier lectura) | "
        "Distancia de 240 al límite (retenido) | Distancia de 240 al límite (cualquier lectura) |")
    add("|---|---|---|---|---|---|")
    for finf, item in p["per_finf"].items():
        add(f"| {_value(finf)} | {'sí' if item['monotone_in_tau'] else 'no'} | {_n(item['step_210_240_retained'], 3)} | "
            f"{_n(item['step_210_240'], 3)} | {_n(item['distance_240_to_limit_retained'], 3)} | "
            f"{_n(item['distance_240_to_limit'], 3)} |")
    add("")
    v = p["limit"]["verdicts"]
    add(f"Límite τ → ∞ ({_point(p['limit']['point'])}, REFERENCE_ONLY): FD-BLD-04 {YES[v['FD-BLD-04']]}, "
        f"FD-BLD-05 {YES[v['FD-BLD-05']]}, FD-BLD-06 {YES[v['FD-BLD-06']]} (48 claves, dos casos).\n")
    add("Diferencias en el horizonte (representativo medio de sangre, 1 L y 2 L, minutos 0–120, los dos casos):\n")
    add("| Finf | Comparación | " + " | ".join(FIELDS_ES.values()) + " |")
    add("|---|---|" + "---|" * len(FIELDS_ES))
    for finf, item in data["horizon"].items():
        for name, label in (("210_vs_240", "τ 210 frente a 240"), ("240_vs_limit", "τ 240 frente al límite")):
            add(f"| {_value(finf)} | {label} | " + " | ".join(_n(item[name][f], 3) for f in FIELDS_ES) + " |")
    return "\n".join(lines)


def render_semantics(data: dict) -> str:
    lines = []
    add = lines.append
    grid = data["adequacy"]["grid"]
    add("| Decisión docente (2026-10-28) | Registro | Comprobación |")
    add("|---|---|---|")
    add(f"| Adecuación del oxígeno para el lactato | déficit efectivo = 0 (ADEQUATE y COMPENSATED); CRITICAL si > 0 | "
        f"{_n(grid['cases'], 0)} combinaciones de entrega, demanda y reserva: {'coinciden' if grid['agree'] else 'NO coinciden'} "
        "con los estados del núcleo |")
    add(f"| Tasas del futuro espacio del lactato | {', '.join(_value(r) for r in data['rates']['lactate'])} | "
        "sin preeliminar ninguna |")
    for name, item in data["l3"].items():
        add(f"| {name} ({item['open_decision']}) | {_value(item['value'])}: {' + '.join(item['status'])} | "
            f"rango comprometido: {'sí' if item['committed_range'] else 'no'} (registro {_value(item['lower'])}–"
            f"{_value(item['upper'])}); sensibilidad: {'preparada' if item['sensitivity_design'] else 'ninguna (no se inventa un rango)'} |")
    return "\n".join(lines)


def render_keys(data: dict) -> str:
    lines = []
    add = lines.append
    compat = data["rate25_compatibility"]
    failing = {k: v for k, v in compat.items() if v}
    keys25 = len(rate25_keys())
    add(f"Tasa 2,5: FD-BLD-06 de los {len(compat)} puntos del soporte en las {keys25} claves de la tasa 2,5 (superconjunto "
        f"de las de sus sobrevivientes, de P2I-2V-R y de P2I-2W), en los dos casos: "
        + ("todos pasan." if not failing else "fallan " + "; ".join(f"{_point(k)} en {len(v)} claves" for k, v in failing.items()) + "."))
    add("")
    c = data["completeness"]
    add(f"Completitud de la sustitución: {_n(c['keys'], 0)} claves exploradas de las tasas 2,5, 5 y 6; cristaloides viejos "
        f"que cumplen FD-BLD-04 y 05: {c['grids_passing_fd04_05']['P2I-2V-R']} de la grilla de P2I-2V-R y "
        f"{c['grids_passing_fd04_05']['P2I-2Y']} de los valores de P2I-2Y. Claves sin testigo (excluidas sólo por el "
        f"cristaloide viejo): **{len(c['without_witness'])}**"
        + (": " + "; ".join(_blood(k) for k in c["without_witness"]) if c["without_witness"] else "") + ".\n")
    s = data["structural"]["summary"]
    add("| Comprobación estructural | Resultado |")
    add("|---|---|")
    add(f"| ρ no mueve el déficit efectivo ni la etiqueta de adecuación | {'sí' if s['rho_cancels_in_deficit_and_adequacy'] else 'no'} |")
    add(f"| el nivel de entrega de llegada no mueve la hemodinámica | {'sí' if s['delivery_level_never_reaches_haemodynamics'] else 'no'} |")
    add(f"| el nivel de entrega de llegada sí mueve el déficit | {'sí' if s['delivery_level_moves_the_deficit'] else 'no'} |")
    z = data["structural"]["p2i2z_summary"]
    add(f"| (P2I-2Z, repetidas) cinética del lactato y de la deuda sin efecto en la hemodinámica; ρ se cancela en D y el "
        f"lactato | {'sí' if z['lactate_kinetics_post_process_only'] and z['debt_side_never_reaches_haemodynamics'] and z['rho_cancels_in_D_and_lactate'] else 'no'} |")
    return "\n".join(lines)


def render_readiness(data: dict) -> str:
    lines = []
    add = lines.append
    ready = data["readiness"]
    add("| Criterio | Resultado |")
    add("|---|---|")
    for name in ORDER:
        add(f"| {CRITERIA_ES[name]} | {'cumple' if ready['criteria'][name]['passed'] else '**no cumple**'} |")
    add("")
    add(f"**Veredicto: {ready['verdict']}**"
        + (f" — {'; '.join(CRITERIA_ES[b] for b in ready['blockers'])}." if ready["blockers"] else "."))
    return "\n".join(lines)


def render_space(data: dict) -> str:
    lines = []
    add = lines.append
    space = data["source_space"]
    a, counts = space["A_blood"], space["counts"]
    add(f"Estado: **{STATUS_ES[space['status']]}**.\n")
    add("| Tasa | Fuente | Sobrevivientes conjuntos | P1 (L1, L2) | P3 (L3) |")
    add("|---|---|---|---|---|")
    for rate in ("2.5", "5.0", "6.0"):
        add(f"| {_value(rate)} | {SOURCES_ES[a['rates'][rate]]} | {_n(a['joint'][rate], 0)} | {_n(a['P1_bounds'][rate][0], 0)}–"
            f"{_n(a['P1_bounds'][rate][1], 0)} | {_n(a['P3_bounds'][rate][0], 0)}–{_n(a['P3_bounds'][rate][1], 0)} |")
    add("")
    add(f"Posición: " + "; ".join(f"{SHORT[c]} {_value(p)}" for c, p in space["B_positions"].items())
        + f". Cristaloide: {len(space['D_crystalloid'])} puntos. ρ: banda 2,0–3,0, simulada con "
        f"{_value(space['E_oxygen']['simulated_at'])} (lactato y adecuación invariantes: "
        f"{'sí' if space['E_oxygen']['lactate_and_adequacy_invariant'] else 'no'}).\n")
    add("| Recuento (antes de simular) | Mínimo | Máximo |")
    add("|---|---|---|")
    add(f"| Candidatos (conjuntos) | {_n(counts['candidates'][0], 0)} | {_n(counts['candidates'][1], 0)} |")
    add(f"| Trayectorias hemodinámicas únicas (simulaciones del núcleo, diseño factorizado) | "
        f"{_n(counts['haemodynamic_trajectories'][0], 0)} | {_n(counts['haemodynamic_trajectories'][1], 0)} |")
    add(f"| Posprocesos por trayectoria hemodinámica (sin simular) | {_n(counts['post_process_per_haemodynamic_trajectory'], 0)} | "
        f"{_n(counts['post_process_per_haemodynamic_trajectory'], 0)} |")
    add(f"| Simulaciones del producto ingenuo | {_n(counts['naive_core_simulations'][0], 0)} | "
        f"{_n(counts['naive_core_simulations'][1], 0)} |")
    add(f"| Simulaciones evitadas | {_n(counts['simulations_avoided'][0], 0)} | {_n(counts['simulations_avoided'][1], 0)} |")
    add("")
    add(f"Factorización válida según las comprobaciones estructurales: **{'sí' if space['factorization_valid'] else 'no'}**.")
    return "\n".join(lines)


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


RENDERERS = {"tau": render_tau, "region": render_region, "practico": render_practical, "semantica": render_semantics,
             "claves": render_keys, "preparacion": render_readiness, "espacio": render_space}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the tau-closure JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
