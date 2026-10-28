"""P2I-2Z report: the generated blocks of docs/revision/P2I2Z_TAU_Y_PREPARACION_LACTATO.md.

    python -m clinical_core.blood_fluid_readiness_report --write <document> --data <the readiness JSON>

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
from .blood_fluid_report import SIDES_ES, STATES_ES

MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->")
           for name in ("tau", "region", "trayectorias", "estructura", "preparacion", "lactato")}
YES = {True: "pasa", False: "falla", None: "ilegible"}
FIELDS_ES = {"haemodynamics": "hemodinámica", "D": "D", "lactate": "lactato", "delivery_index": "índice de entrega"}
STATUS_ES = {"PREPARED": "PREPARADO", "DRAFT (readiness not met)": "BORRADOR (no se cumple la preparación)"}
CRITERIA_ES = {
    "shared BloodState active": "BloodState compartido activo",
    "DO2 / extraction model current": "modelo de DO2 y extracción vigente",
    "case-compatible preload region defined": "región de precarga compatible con el caso definida",
    "bleed-rate boundary characterized": "borde de la tasa de sangrado caracterizado",
    "crystalloid candidate region characterized": "región candidata del cristaloide caracterizada",
    "no stale active haemorrhage probe bypasses BloodState": "ninguna sonda de hemorragia activa y obsoleta evita el BloodState",
    "hidden parameters unapproved, candidate support explicit": "parámetros ocultos sin aprobar y soporte candidato explícito",
}
STRUCTURAL_ES = {
    "lactate_kinetics_post_process_only": "la cinética del lactato (ganancia y τ del lactato) no mueve la hemodinámica ni D",
    "debt_side_never_reaches_haemodynamics": "la cinética de la deuda y la deuda de llegada no mueven la hemodinámica",
    "intrinsic_rate_reaches_nothing_read": "la frecuencia intrínseca no mueve la hemodinámica, D ni el lactato",
    "rho_cancels_in_D_and_lactate": "ρ (banda re-anclada) no mueve D ni el lactato",
    "rho_moves_the_delivery_index": "ρ sí mueve el índice de entrega (lo que lee la adecuación)",
}


def _point(key: str) -> str:
    f0, finf, tau = key.split("|")
    return f"F0 {_value(f0)} · Finf {_value(finf)} · τ {_value(tau)}"


def _blood(label: str) -> str:
    b0, rate, target, tau, cap = label.split("|")
    return f"B0 {_value(b0)} · tasa {_value(rate)} · meta {_value(target)} · τ {_value(tau)} · cap. {_value(cap)}"


def render_tau(data: dict) -> str:
    lines = []
    add = lines.append
    add(f"Congelamiento de P2I-2Z: `{data['freeze_digest']}`, comprometido antes de evaluar (una prueba lo fija). "
        f"Registro de partida: P2I-2Y `{data['record']['P2I-2Y']}`.\n")
    add(f"Diseño: F0 0,2; Finf 0,05 y 0,1; τ 60, 90 y 120 min ({len(data['design'])} puntos; τ 60 reproduce P2I-2Y). "
        f"FD-BLD-06 se lee en las {_n(len(data['keys']['probes']), 0)} sondas de P2I-2Y y en las "
        f"{_n(len(data['keys']['certified']), 0)} claves certificadas (tasas 5 y 6): {_n(data['keys']['distinct'], 0)} "
        "claves de sangre distintas, en los dos casos.\n")
    add("| Punto | Regla | FD-BLD-04 | FD-BLD-05 | FD-BLD-06 referencia | FD-BLD-06 todas las sondas | "
        "FD-BLD-06 todas las claves certificadas | Robusto en la región de sangre |")
    add("|---|---|---|---|---|---|---|---|")
    for point in data["design"]:
        key = f"{point['F0']:g}|{point['Finf']:g}|{point['tau']:g}"
        item = data["classified"][key]
        if item["status"] != "ACTIVE_CALIBRATION_CANDIDATE":
            add(f"| {_point(key)} | {item['status']} | — | — | — | — | — | — |")
            continue
        add(f"| {_point(key)} | Finf < F0 | {YES[item['FD-BLD-04']]} | {YES[item['FD-BLD-05']]} | "
            f"{YES[item['FD-BLD-06 reference']]} | {YES[item['FD-BLD-06 every probe']]} | "
            f"{YES[item['FD-BLD-06 every certified key']]} | **{'sí' if item['robust'] else 'no'}** |")
    add("")
    add("Lecturas, por punto (los dos casos):\n")
    add("| Punto | Aporte inicial | Dilución pico 1 L (mín.–máx. en las claves) | Dilución pico 2 L (mín.–máx.) | "
        "Claves donde falla FD-BLD-06 |")
    add("|---|---|---|---|---|")
    for point in data["design"]:
        key = f"{point['F0']:g}|{point['Finf']:g}|{point['tau']:g}"
        entry = data["evaluated"][key]
        if entry["status"] != "ACTIVE_CALIBRATION_CANDIDATE":
            continue
        peaks = {v: [entry["fd06"][label][case]["reading"][v]["peak"] for label in entry["fd06"] for case in bc.CASES]
                 for v in ("1000", "2000")}
        failing = data["classified"][key]["FD-BLD-06 failing keys"]
        add(f"| {_point(key)} | {_n(entry['readings']['gi_bleed_57m']['early'])} | "
            f"{_n(min(peaks['1000']))}–{_n(max(peaks['1000']))} | {_n(min(peaks['2000']))}–{_n(max(peaks['2000']))} | "
            f"{'; '.join(_blood(label) for label in failing) or 'ninguna'} |")
    add("")
    tau = data["tau"]
    add(f"τ 90 sobrevive: **{'sí' if tau['tau_90_survives'] else 'no'}**. τ 120 sobrevive: "
        f"**{'sí' if tau['tau_120_survives'] else 'no'}**. Lado superior de τ: **{tau['upper_status']}**."
        + (" La extensión se detiene aquí: no se agrega ningún τ sin autorización docente." if tau["stop"] else ""))
    return "\n".join(lines)


def render_region(data: dict) -> str:
    lines = []
    add = lines.append
    add(f"Región robusta (puntos activos, Finf < F0): {', '.join(_point(k) for k in data['region'])}.\n")
    add("| Parámetro | Explorado | Soporte candidato | Clase | Lado inferior | Lado superior | Borde | "
        "Identificado (regla congelada) |")
    add("|---|---|---|---|---|---|---|---|")
    for name, item in data["edges"].items():
        add(f"| {name} | {', '.join(_value(v) for v in item['explored'])} | "
            f"{', '.join(_value(v) for v in item['left']) or '—'} | {CLASSES_ES[item['class']]} | "
            f"{SIDES_ES[item['lower_side']]} | {SIDES_ES[item['upper_side']]} | {item['edge'] or '—'} | "
            f"{'sí' if item['identified'] else 'no'} |")
    return "\n".join(lines)


def render_trajectories(data: dict) -> str:
    lines = []
    add = lines.append
    add("Sangre del representativo medio de P2I-2V-R (tasa 5, posición superior de la banda), sangrado en curso, "
        "bolsa en 20 min desde el minuto 0. Contexto: no filtra.\n")
    add("| Punto | Caso | Volumen | Aporte inicial | Retenido 30′ / 60′ / 120′ | Dilución 20′ / 30′ / 60′ / 120′ (g/dL) | "
        "Pico | Reversión a 120′ | Gasto 20′ / 120′ | DO2 20′ / 120′ | Déficit 20′ / 120′ | Estado 120′ |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for point in data["design"]:
        key = f"{point['F0']:g}|{point['Finf']:g}|{point['tau']:g}"
        cases = data["trajectories"]["sets"][key]
        for case in bc.CASES:
            for volume in ("1000", "2000"):
                t = cases[case][volume]
                rows = {r["minute"]: r for r in t["rows"]}
                cell = lambda field, minutes, digits=2: " / ".join(_n(rows[m][field], digits) if m in rows else "—"
                                                               for m in minutes)
                end = rows.get(120)
                add(f"| {_point(key)} | {SHORT[case]} | {int(volume) // 1000} L | {_n(t['early_retained'])} | "
                    f"{cell('retained_share', (30, 60, 120))} | {cell('dilution', (20, 30, 60, 120))} | "
                    f"{_n(t['peak_dilution'])} | "
                    f"{_n(100 * t['reversal_fraction'], 0) if t['reversal_fraction'] is not None else '—'} % | "
                    f"{cell('output_rel', (20, 120))} | {cell('do2', (20, 120))} | "
                    f"{cell('effective_deficit', (20, 120))} | {STATES_ES.get(end['state'], end['state']) if end else '—'}"
                    + ("" if t["stop"] is None else f" (se detiene en el {t['stop']}′)") + " |")
    return "\n".join(lines)


def render_structure(data: dict) -> str:
    lines = []
    add = lines.append
    summary, checks = data["structural"]["summary"], data["structural"]["checks"]
    add(f"Tres representativos de P2I-2V-R × dos casos, posición superior, 120 min sin tratamiento (y 2 L de "
        f"0,2|0,1|60 para ρ). Tolerancia {summary['tolerance']:.0e} (redondeo de punto flotante).\n")
    add("| Comprobación | Resultado | Mayor diferencia |")
    add("|---|---|---|")
    worst = {}
    for item in checks.values():
        for name, gaps in item["checks"].items():
            for field, gap in gaps.items():
                prefix = ("rho" if name.startswith("rho=") else "intrinsic" if "intrinsic" in name else
                          "lactate" if name.startswith(("lactate_per", "lactate_clearance")) else "debt")
                worst[(prefix, field)] = max(worst.get((prefix, field), 0.0), gap)
    rows = (("lactate_kinetics_post_process_only", ("lactate", "haemodynamics"), ("lactate", "D")),
            ("debt_side_never_reaches_haemodynamics", ("debt", "haemodynamics")),
            ("intrinsic_rate_reaches_nothing_read", ("intrinsic", "haemodynamics"), ("intrinsic", "D"),
             ("intrinsic", "lactate")),
            ("rho_cancels_in_D_and_lactate", ("rho", "D"), ("rho", "lactate")),
            ("rho_moves_the_delivery_index", ("rho", "delivery_index")))
    for name, *fields in rows:
        gaps = "; ".join(f"{FIELDS_ES[field]} {worst[(prefix, field)]:.1e}".replace(".", ",") for prefix, field in fields)
        add(f"| {STRUCTURAL_ES[name]} | {'sí' if summary[name] else 'no'} | {gaps} |")
    return "\n".join(lines)


def render_readiness(data: dict) -> str:
    lines = []
    add = lines.append
    ready = data["readiness"]
    add("| Criterio | Resultado |")
    add("|---|---|")
    for name in CRITERIA_ES:
        item = ready["criteria"][name]
        add(f"| {CRITERIA_ES[name]} | {'cumple' if item['passed'] else '**no cumple**'} |")
    add("")
    add(f"**Veredicto: {ready['verdict']}**"
        + (f" — {'; '.join(CRITERIA_ES[b] for b in ready['blockers'])}." if ready["blockers"] else "."))
    return "\n".join(lines)


def render_lactate(data: dict) -> str:
    lines = []
    add = lines.append
    space = data["lactate_input_space"]
    a, counts = space["A_blood"], space["counts"]
    add(f"Estado: **{STATUS_ES[space['status']]}**. No se ejecuta.\n")
    add("| | Fuente | Valores |")
    add("|---|---|---|")
    add(f"| A. Sangre | sobrevivientes conjuntos de P2I-2Y con las tasas 5 y 6 | "
        f"{_n(a['joint_candidates']['5.0'], 0)} y {_n(a['joint_candidates']['6.0'], 0)} conjuntos; "
        f"{_n(a['certified_5_keys'], 0)} claves de 5 dimensiones; P1 (L1, L2) {_n(a['P1_bounds'][0], 0)}–"
        f"{_n(a['P1_bounds'][1], 0)}; P3 (L3) {_n(a['P3_bounds'][0], 0)}–{_n(a['P3_bounds'][1], 0)} |")
    add(f"| B. Posición | la única con sobrevivientes conjuntos | "
        + "; ".join(f"{SHORT[c]} {_value(p)}" for c, p in space["B_positions"].items()) + " |")
    add(f"| C. Tasa | registro docente | {', '.join(_value(v) for v in space['C_rates'])} |")
    add(f"| D. Cristaloide | región robusta de P2I-2Z | {', '.join(_point(k) for k in space['D_crystalloid'])} |")
    e = space["E_oxygen"]
    add(f"| E. Extracción de O2 | ρ candidata 2,0–3,0, banda re-anclada | trayectorias con ρ {_value(e['trajectories_at_reserve'])}; "
        f"adecuación leída con ρ {', '.join(_value(v) for v in e['adequacy_read_at'])} |")
    f = space["F_lactate_side"]
    add(f"| F. Lactato | registro de calibración y bandas del caso | τ de la deuda {', '.join(_value(v) for v in f['debt_clearance_tau_min'])}; "
        f"ganancia {', '.join(_value(v) for v in f['lactate_per_output_deficit'])}; τ del lactato "
        f"{', '.join(_value(v) for v in f['lactate_clearance_tau_min'])}; exceso de llegada inf./medio/sup.; "
        f"{len(f['arrival_pairs (debt, delivery)'])} pares (deuda, entrega) de llegada |")
    add("")
    add("| Recuento (antes de simular) | Mínimo | Máximo |")
    add("|---|---|---|")
    add(f"| Candidatos (conjuntos) | {_n(counts['candidates'][0], 0)} | {_n(counts['candidates'][1], 0)} |")
    add(f"| Simulaciones del núcleo, diseño factorizado | {_n(counts['core_simulations_factorized'][0], 0)} | "
        f"{_n(counts['core_simulations_factorized'][1], 0)} |")
    add(f"| Simulaciones del núcleo, producto ingenuo | {_n(counts['naive_core_simulations'][0], 0)} | "
        f"{_n(counts['naive_core_simulations'][1], 0)} |")
    add(f"| Posprocesos de cinética y exceso por trayectoria y nivel de deuda de llegada (sin simular; más 3 lecturas "
        f"de adecuación, una por ρ) | {_n(counts['post_processing_per_trajectory'], 0)} | "
        f"{_n(counts['post_processing_per_trajectory'], 0)} |")
    add("")
    add(f"Factorización válida según las comprobaciones estructurales: **{'sí' if space['factorization_valid'] else 'no'}**.")
    return "\n".join(lines)


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


RENDERERS = {"tau": render_tau, "region": render_region, "trayectorias": render_trajectories,
             "estructura": render_structure, "preparacion": render_readiness, "lactato": render_lactate}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the readiness JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
