"""P2I-2AE report: the generated blocks of docs/revision/P2I2AE_ESTRUCTURA_FC_SIMPATICA.md.

    python -m clinical_core.hr_structure_report --write <document> --data <the HR-structure JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import hr_structure as hs
from .blood_filter_report import _n
from .lactate_rebuild_report import CASE_ES, CASES, LEVEL_ES

MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->")
           for name in ("decisiones", "auditoria", "anclas", "intrinseca", "ganancia", "llegada", "trayectorias",
                        "sondas", "invariantes", "superficie", "identificabilidad", "fr", "legado", "veredicto")}
FACULTY_ES = {"decided": "fecha", "td_92": "TD-92 (τ_D y FC)", "arrival": "descomposición de la FC de llegada",
              "lactate": "lactato", "scope": "alcance"}
CHECKS_ES = {"factorization": "la reconstrucción de la FC coincide con el núcleo completo",
             "no_tau_d_leak": "τ_D ya no llega a la FC con D fija",
             "contributors_explicit": "cada FC informada es la suma de sus contribuciones",
             "arrival_coherent": "descomposición de llegada coherente",
             "invariants": "las diez direcciones se cumplen",
             "patient_like": "sin banderas estructurales",
             "support_explicit": "soporte explícito",
             "nothing_approved": "nada aprobado"}
CLASS_ES = {hs.VALID_CAUSAL_PATH: "VALID_CAUSAL_PATH", hs.SEMANTIC_LEAK: "SEMANTIC_LEAK",
            hs.LEGACY_ARTIFACT: "LEGACY_ARTIFACT", hs.CASE_SPECIFIC_ARTIFACT: "CASE_SPECIFIC_ARTIFACT"}
CONTRIBUTORS_ES = {"intrinsic_rate": "frecuencia intrínseca", "sympathetic": "componente simpático",
                   "debt": "contribución de D", "direct_deficit": "déficit directo",
                   "acute_haemodynamic": "estímulo agudo (presión)", "other_stimuli": "otros estímulos",
                   "arrival_rest": "resto de llegada", "drugs_interventions": "fármacos e intervenciones",
                   "rhythm": "ritmo", "caps_floors": "topes y pisos", "case_specific": "términos del caso"}
TAGS = ("LOW", "MID", "HIGH")
LANDMARKS = ("arrival", "untreated_30", "untreated_60", "untreated_120", "after_crystalloid_30", "crystalloid_120",
             "after_prbc_unit_1", "after_prbc_unit_2_and_haemostasis", "after_haemostasis_90", "restored_adequacy_120",
             "persistent_critical_120")
FIELDS = (("hr", "FC", 1), ("intrinsic", "intr.", 0), ("debt_bpm", "deuda", 1), ("acute_pressure_bpm", "presión", 1),
          ("arrival_rest_bpm", "resto", 1), ("lag_bpm", "retardo", 1), ("D", "D", 1), ("effective_deficit", "déficit", 3),
          ("output", "gasto", 2), ("bleed_ml_per_min", "sangrado", 2), ("prbc_units", "GR (U)", 2),
          ("crystalloid_in_ml", "cristaloide (mL)", 0))


def _g(value) -> str:
    if value is None:
        return "—"
    if value == 0.0:
        return "0"
    return f"{value:.3g}".replace(".", ",")


def _yes(value) -> str:
    return "sí" if value else "no"


def render_decisiones(data: dict) -> str:
    lines = [f"Congelamiento: `{data['freeze_digest']}` (una prueba lo fija). Registro de partida: P2I-2AD "
             f"`{data['records']['P2I-2AD']}`.\n", "| Decisión docente | Texto registrado |", "|---|---|"]
    lines += [f"| {FACULTY_ES[name]} | {data['faculty'][name]} |" for name in FACULTY_ES]
    return "\n".join(lines)


def render_auditoria(data: dict) -> str:
    audit = data["audit"]
    lines = [f"Ecuación anterior (e0dffa8): {audit['old_equation']}", "",
             f"Ecuación nueva: {audit['new_equation']}", "", "| Contribuyente | Estado |", "|---|---|"]
    lines += [f"| {CONTRIBUTORS_ES[name]} | {audit['contributors'][name]} |" for name in CONTRIBUTORS_ES]
    lines += ["", "| Vía τ_D → FC | Clase | Estado | Por qué |", "|---|---|---|---|"]
    lines += [f"| {p['path']} | {CLASS_ES[p['class']]} | {p['status']} | {p['why']} |" for p in audit["tau_d_paths"]]
    deficit, live = audit["deficit"], audit["live"]
    lines += ["", f"Déficit directo frente a D (P2I-2AE-3): A (déficit efectivo instantáneo) "
                  f"{_yes(deficit['A_instantaneous_effective_oxygen_deficit'])}; B (D acumulada) "
                  f"{_yes(deficit['B_accumulated_D'])}; C (ambos) {_yes(deficit['C_both'])}. Término agudo existente: "
                  f"{deficit['acute_term_present']}. ¿Hace falta un término nuevo? "
                  f"{_yes(deficit['new_acute_term_needed'])}: {deficit['why']}", "",
              "Lectura del código vigente: " + "; ".join(f"`{name}` {_yes(value)}"
                                                          for name, value in live["reads"].items()) + "."]
    return "\n".join(lines)


def render_anclas(data: dict) -> str:
    lines = ["| Caso | Dato | Valor | Etiqueta | Nota |", "|---|---|---|---|---|"]
    for case in CASES:
        for name, row in data["anchors"][case].items():
            lines.append(f"| {CASE_ES[case]} | {name} | {row.get('value', '—')} | {row['label']} | "
                         f"{row.get('note') or row.get('source', '')} |")
    return "\n".join(lines)


def render_intrinseca(data: dict) -> str:
    audit = data["intrinsic"]
    bands = "; ".join(f"{CASE_ES[c]} {' / '.join(_n(v, 0) for v in audit['band'][c])}" for c in CASES)
    return (f"Banda: {bands} lpm. ¿Derivada de HR1? {_yes(audit['derived_from_hr1'])}. Clasificación: "
            f"**{audit['status']}**. {audit['why']}")


def render_ganancia(data: dict) -> str:
    gain = data["gain"]
    points = " · ".join(_g(p) for p in gain["points"])
    old = "; ".join(f"τ_D {tau}: {' / '.join(_g(v) for v in values)}"
                    for tau, values in gain["old_induced_gains_for_comparison_only"].items())
    return "\n".join([
        f"Unidades: {gain['units']}. Regla (congelada antes de cualquier resultado): {hs.GAIN_RULE.strip()}", "",
        f"Extremos: {_g(gain['low'])} (1 lpm a D0 = {_n(max(gain['debt_levels']), 0)}) y {_g(gain['high'])}; razón "
        f"{_g(gain['ratio'])}. Puntos: {points}; referencia sintética 0 (sin impulso por deuda, nunca contada). Ancla del "
        f"corte intrínseco: {_g(hs.GAIN_ANCHOR)} (punto medio logarítmico, no una selección). Por debajo de "
        f"{_g(gain['every_declared_arrival_consistent_below'])} toda llegada declarada es coherente. El valor por "
        f"defecto del perfil, {_g(gain['default'])} (= 0,5 / 60), es un marcador de continuidad PROVISIONAL.", "",
        f"Rango anterior: {gain['old_status']}. {gain['old_reason']} Ganancias que inducía (sólo comparación): {old}."])


def render_llegada(data: dict) -> str:
    analytic = data["analytic"]
    lines = [f"{analytic['rule']}", "", f"Combinaciones: {analytic['combinations']}; ANALYTIC_REJECTION: "
             f"{analytic['analytic_rejections']}; FC de llegada reproducida exactamente en todas las coherentes: "
             f"{_yes(analytic['arrival_reproduced_exactly'])}; el núcleo rechaza exactamente las mismas: "
             f"{_yes(data['refused_by_core']['agree'])}.", ""]
    for case in CASES:
        lines += [f"**{CASE_ES[case]}** (FC de llegada {_n(data['anchors'][case]['arrival_hr']['value'], 0)}): "
                  "simpático = deuda + resto, en lpm, por intrínseca y D0 (filas) y ganancia (columnas).", "",
                  "| Intrínseca | D0 | " + " | ".join(_g(g) for g in hs.GAIN_SCAN) + " |",
                  "|---|---|" + "---|" * len(hs.GAIN_SCAN)]
        table = analytic["table"][case]
        for level in hs.LEVELS:
            for debt in hs.LEVELS:
                cells, d0, rate = [], None, None
                for gain in hs.GAIN_SCAN:
                    row = table[f"{level}|{debt}|{gain!r}"]
                    d0, rate = row["D0"], row["intrinsic"]
                    cells.append("rechazo analítico" if row["status"] == hs.ANALYTIC_REJECTION else
                                 f"{_n(row['debt_bpm'], 1)} + {_n(row['non_debt_bpm'], 1)}")
                lines.append(f"| {_n(rate, 0)} | {_n(d0, 0)} | " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines)


def _clean(value, digits: int):
    """A reading as shown: a value that rounds to zero is shown as 0 (never -0)."""
    return 0.0 if round(value, digits) == 0 else value


def _row(point) -> str:
    if not isinstance(point, dict):
        return " | ".join(["—"] * len(FIELDS))
    return " | ".join(_n(_clean(point[name], digits), digits) if point.get(name) is not None else "—"
                      for name, _, digits in FIELDS)


def render_trayectorias(data: dict) -> str:
    lines = [f"{data['scan_rule']}", "", "Aquí, cada representativo a la intrínseca media y la ganancia ancla "
             f"({_g(hs.GAIN_ANCHOR)}); los cortes completos de ganancia (cinco puntos y 0) e intrínseca (inferior, media, "
             "superior) están en el JSON (`trajectories`) y, por hito, en la superficie de decisión (§10). Columnas en "
             "lpm salvo D (índice·min), déficit efectivo, gasto relativo, sangrado (mL/min), glóbulos rojos dados (U) y "
             "cristaloide infundido (mL): FC = intrínseca + deuda + presión + resto + otros estímulos + piso + retardo. "
             "Hemostasia en el minuto 60 de L3.", ""]
    for name, block in data["trajectories"].items():
        lines += [f"### {name}: {block['title']}", ""]
        for case in CASES:
            lines += [f"**{CASE_ES[case]}**", "", "| Rep. | Intr. | Ganancia | Min | " + " | ".join(
                label for _, label, _ in FIELDS) + " |", "|---|---|---|---|" + "---|" * len(FIELDS)]
            for tag in TAGS:
                label = f"{tag}|midpoint|{hs.GAIN_ANCHOR!r}"
                table = block["cases"][case][label]
                _, level, gain = label.split("|")
                if table == hs.ANALYTIC_REJECTION:
                    lines.append(f"| {tag} | {LEVEL_ES[level]} | {_g(float(gain))} | — | rechazo analítico |"
                                 + " |" * (len(FIELDS) - 1))
                    continue
                for minute in block["minutes"]:
                    if str(minute) in table:
                        lines.append(f"| {tag} | {LEVEL_ES[level]} | {_g(float(gain))} | {minute} | "
                                     f"{_row(table[str(minute)])} |")
            lines.append("")
    return "\n".join(lines)


def render_sondas(data: dict) -> str:
    probes = data["probes"]
    lines = ["| Caso | Sonda | Se cumple | Lectura |", "|---|---|---|---|"]
    for case in CASES:
        p = probes[case]
        tau = p["tau_d_at_fixed_D"]
        lines.append(f"| {CASE_ES[case]} | τ_D {' / '.join(_n(t, 0) for t in tau['tau_levels'])} con D fija | "
                     f"{_yes(tau['holds'])} | objetivos iguales en D = "
                     f"{', '.join(_n(r['D'], 0) for r in tau['rows'])} |")
        more = p["inv1_more_debt"]
        lines.append(f"| {CASE_ES[case]} | más D, todo lo demás fijo | {_yes(more['holds'])} | FC "
                     f"{' → '.join(_n(v, 1) for v in more['hr'])} para D {' → '.join(_n(v, 0) for v in more['D'])} |")
        acute = p["inv2_acute_deficit"]
        lines.append(f"| {CASE_ES[case]} | déficit agudo mayor (bomba) | {_yes(acute['holds'])} | objetivo "
                     f"{' → '.join(_g(v) for v in acute['targets_by_pump'])}; Hb sola: "
                     f"{' → '.join(_g(v) for v in acute['targets_by_hb'])} ({acute['note']}) |")
        floor = p["inv9_floor"]
        lines.append(f"| {CASE_ES[case]} | piso intrínseco | {_yes(floor['holds'])} | FC {_n(floor['hr'], 1)}, "
                     f"intrínseca {_n(floor['intrinsic'], 0)} |")
        cells = p["inv6_7_red_cells"]
        lines.append(f"| {CASE_ES[case]} | glóbulos rojos sin sangrado (2 U en 60 min) | ver abajo | FC "
                     f"{' / '.join(_n(v, 1) for v in cells['hr_0_30_60'])} a 0 / 30 / 60 |")
        for r in p["inv8_crystalloid"]["responses"]:
            lines.append(f"| {CASE_ES[case]} | cristaloide 500 mL, bomba {_n(r['pump'], 1)} | ver abajo | ΔFC a 30 min "
                         f"{_n(r['hr_change_at_30'], 1)}, presión relativa {_n(r['pressure_rel_at_30'], 2)} |")
        rhythm = p["inv10_rhythm"]
        pulse = "sin frecuencia de pulso" if rhythm["pea_pulse_rates"] == ["None"] else ", ".join(rhythm["pea_pulse_rates"])
        lines.append(f"| {CASE_ES[case]} | AESP / marcapasos | {_yes(rhythm['holds'])} | AESP: {pulse}, impulso "
                     f"{', '.join(_g(v) for v in rhythm['pea_drives'])}; marcapasos "
                     f"{', '.join(_n(v, 0) for v in rhythm['paced_rates'])} lpm |")
    lines += ["", f"Una unidad no fija un descenso: {_yes(probes['inv6_one_unit_not_fixed']['holds'])} (ΔFC de la "
                  f"primera unidad {' / '.join(_n(v, 1) for v in probes['inv6_one_unit_not_fixed']['first_unit_changes'])}"
                  f"); la segunda puede diferir: {_yes(probes['inv7_second_unit_may_differ']['holds'])} (ΔFC "
                  f"{' / '.join(_n(v, 1) for v in probes['inv7_second_unit_may_differ']['second_unit_changes'])}); "
                  f"el cristaloide responde a la fisiología, no a su identidad: "
                  f"{_yes(probes['inv8_physiology_not_identity']['holds'])}. Escala de D (g, ganancia, D0) → "
                  f"(c g, ganancia / c, c D0): FC igual "
                  f"{_yes(probes['d_scale']['holds'])} (brecha máxima "
                  f"{', '.join(_g(r['max_gap_bpm']) for r in probes['d_scale']['rows'])} lpm)."]
    return "\n".join(lines)


def render_invariantes(data: dict) -> str:
    inv = data["invariants"]
    lines = ["| # | Dirección | Resultado |", "|---|---|---|"]
    lines += [f"| {k} | {text} | {'PASA' if inv['results'][str(k)] else 'FALLA'} |"
              for k, text in ((int(k), v) for k, v in inv["statements"].items())]
    flags = data["flags"]
    lines += ["", f"Corridas L3 con ganancia positiva: {inv['l3_runs']}; con T* y D(T*) > 0: {inv['recovery_runs']}. "
                  f"{hs.FLAG_POLICY}", "", "| Bandera estructural | Corridas |", "|---|---|"]
    lines += [f"| {name} | {count} |" for name, count in flags.items()]
    return "\n".join(lines)


def render_superficie(data: dict) -> str:
    surface = data["decision_surface"]
    lines = [f"{surface['note']}. Intrínseca en su punto medio; cada celda: FC de LOW / MID / HIGH (lpm).", ""]
    for case in CASES:
        table = surface["table"][case]
        lines += [f"**{CASE_ES[case]}**", "", "| Hito (escenario, min) | " + " | ".join(_g(g) for g in hs.GAIN_SCAN)
                  + " |", "|---|" + "---|" * len(hs.GAIN_SCAN)]
        for name in LANDMARKS:
            scenario, minute = surface["landmarks"][name]
            cells = []
            for gain in hs.GAIN_SCAN:
                values = table[name][repr(gain)]
                cells.append(" / ".join("rech." if v == hs.ANALYTIC_REJECTION else "det." if v == "STOPPED"
                                        else _n(v["hr"], 0) for v in (values[tag] for tag in TAGS)))
            lines.append(f"| {name} ({scenario}, {minute}) | " + " | ".join(cells) + " |")
        onsets = table["restored_adequacy_onset_at_gain_anchor"]
        lines += ["", "Inicio de la adecuación restaurada (T*) a la ganancia ancla: " + "; ".join(
            f"{tag} min {onsets[tag]['onset']}, FC {_n(onsets[tag]['hr_at_onset'], 0)}" if onsets[tag] else f"{tag} —"
            for tag in TAGS), ""]
    return "\n".join(lines)


def render_identificabilidad(data: dict) -> str:
    ident = data["identifiability"]
    pair = ident["intrinsic_vs_gain"]
    lines = [ident["rule"], "", f"Intrínseca frente a ganancia: **{pair['status']}**. Pares comparados "
             f"{pair['pairs_compared']}, brecha máxima de FC {_g(pair['max_hr_gap_bpm'])} lpm; pares con el piso activo "
             f"{pair['pairs_where_the_floor_binds']}. {pair['why']}.", "", "| Dimensión | Estado | Soporte |",
             "|---|---|---|"]
    for name, row in ident["dimensions"].items():
        lines.append(f"| {name} | {row['status']} | {row['support']} |")
    return "\n".join(lines)


def render_fr(data: dict) -> str:
    rr = data["rr"]
    return (f"{rr['source']}. ¿La FR lee la FC? {_yes(rr['rr_reads_hr'])}. FR idéntica entre ganancias e intrínsecas en "
            f"las recorridas de validación: {_yes(rr['rr_equal_across_gain_and_intrinsic'])}. D y lactato idénticos al "
            f"registro P2I-2AD: {_yes(rr['d_and_lactate_unchanged_from_p2i2ad'])}. ¿El cambio de FC altera la FR? "
            f"{_yes(rr['changes_rr'])}. FR calibrada: {_yes(rr['calibrated'])}.")


def render_legado(data: dict) -> str:
    legacy = data["legacy_reference"]
    lines = [legacy["rule"], "", "| Caso | Escenario | " + " | ".join(str(m) for m in hs.TIMES) + " |",
             "|---|---|" + "---|" * len(hs.TIMES)]
    for key, row in legacy["beside"].items():
        case, scenario = key.split("|")
        cells = []
        for m in hs.TIMES:
            core, old = row["core_range_over_gains_and_tags"].get(str(m)), row["legacy"].get(str(m))
            cells.append(f"{_n(core[0], 0)}–{_n(core[1], 0)} ({_n(old, 0) if old is not None else '—'})"
                         if core else "—")
        lines.append(f"| {CASE_ES[case]} | {scenario} | " + " | ".join(cells) + " |")
    lines += ["", "Cada celda: rango del núcleo sobre ganancias y representativos (intrínseca media) y, entre "
                  "paréntesis, la FC del motor de familias. Sólo referencia."]
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    verdict = data["verdict"]
    lines = [f"**{verdict['verdict']}**\n", "| Comprobación | Resultado |", "|---|---|"]
    lines += [f"| {CHECKS_ES[name]} | {_yes(verdict['checks'][name])} |" for name in CHECKS_ES
              if name in verdict["checks"]]
    lines += ["", f"Regla congelada: {verdict['rule']}", "",
              f"Siguiente paso: {verdict['next_step'] or 'ninguno (el veredicto no es READY)'}"]
    return "\n".join(lines)


RENDERERS = {"decisiones": render_decisiones, "auditoria": render_auditoria, "anclas": render_anclas,
             "intrinseca": render_intrinseca, "ganancia": render_ganancia, "llegada": render_llegada,
             "trayectorias": render_trayectorias, "sondas": render_sondas, "invariantes": render_invariantes,
             "superficie": render_superficie, "identificabilidad": render_identificabilidad, "fr": render_fr,
             "legado": render_legado, "veredicto": render_veredicto}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the HR-structure JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
