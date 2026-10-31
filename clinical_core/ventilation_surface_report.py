"""P2K-3 report: the generated blocks of docs/revision/P2K3_VENTILACION_EFECTIVA_Y_SUPERFICIE_RESPIRATORIA.md.

    python -m clinical_core.ventilation_surface_report --write <document> --data <the P2K-3 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _s, _share, _yes
from .lactate_rebuild_report import CASE_ES

NAMES = ("decisiones", "semantica", "soportes", "desacople", "sondas", "llegada", "reconstruccion", "preguntas",
         "identificabilidad", "dependencias", "paquete", "no_regresion", "veredicto", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
CASES = ("gi_bleed_57m", "gi_bleed_72f")
FACULTY_ES = {"decided": "fecha", "closed": "P2K-2", "issue": "problema", "shared_driver": "impulsor común",
              "mapping": "mapeo de la ventilación efectiva", "efficiency": "eficiencia ventilatoria",
              "paco2": "PaCO2", "ventilation_gain": "ganancia ácido → ventilación", "rr": "FR", "acid": "carga ácida",
              "references": "referencias y tolerancias", "arrival_paco2": "PaCO2 de llegada", "arrival_rr": "FR de llegada",
              "arrival_ph": "pH de llegada", "upstream": "incertidumbre previa", "support": "soporte respiratorio",
              "non_regression": "no regresión", "decision_pack": "paquete de decisión", "scope": "alcance"}
SCENARIO_ES = {"P1": "R1 · hemorragia sin tratamiento (L1)", "P2": "R2 · cristaloide (L2)",
               "P3": "R3 · GR sin hemostasia", "P4": "R4 · manejo definitivo (L3)"}
CRITERIA_ES = {"rr_not_determining_w": "la FR no determina W",
               "intrinsic_not_determining_rest": "la FR intrínseca no determina la PaCO2 en reposo",
               "lactate_d_retired": "el lactato y D siguen retirados como controladores",
               "arrival_rr_reproduced": "la FR de llegada se reproduce",
               "arrival_paco2_reproduced": "la PaCO2 de llegada se reproduce con una ganancia común",
               "ph_coherent": "el pH es coherente", "patient_like": "trayectorias propias de un paciente",
               "factorization_valid": "la factorización es válida", "upstream_unchanged": "fisiología previa intacta",
               "nothing_approved": "nada aprobado"}
DOMAINS_ES = {"blood_state": "BloodState", "output": "gasto", "pressure_tone": "presión / tono",
              "delivery_deficit": "DO2 / déficit efectivo", "D": "D", "lactate": "lactato",
              "hr_baroreflex": "FC / barorreflejo"}
IDENT_ES = {"intrinsic_rr_57m": "FR intrínseca 57m", "intrinsic_rr_72f": "FR intrínseca 72f",
            "acid_to_drive_gain": "ganancia ácido → FR", "acid_to_ventilation_gain": "ganancia ácido → ventilación",
            "B": "B (escala déficit → ácido)", "acid_clearance_tau": "τ de aclaramiento ácido"}
FACTORS_ES = {"intrinsic_rr": "FR intrínseca", "drive_gain": "ganancia de frecuencia", "ventilation_gain":
              "ganancia de ventilación", "acid_pair": "B / τ", "demand": "demanda", "tone_gain": "tono g"}
PACK_ES = {"A": "FR a 120 min sin tratamiento · 57m", "B": "FR a 120 min sin tratamiento · 72f",
           "C": "PaCO2 / pH a 120 min sin tratamiento · 57m", "D": "PaCO2 / pH a 120 min sin tratamiento · 72f",
           "E": "respuesta de la FR al cristaloide (FR120 − FR0, R2)",
           "F": "respuesta de la FR a los GR sin hemostasia (FR120 − FR0, R3)",
           "G": "FR a 120 min tras el manejo definitivo (R4)", "H": "PaCO2 / pH a 120 min tras el manejo definitivo (R4)",
           "I": "FR residual sobre la intrínseca a 120 min tras la reanimación adecuada (R4)"}
RATIONALE_ES = {
    "A": "la carga ácida de una hemorragia no controlada mueve la frecuencia; cuánto sube a los 120 min depende de su "
         "producción y aclaramiento (B, τ), de la ganancia de frecuencia y de la FR intrínseca",
    "B": "como A, con la carga y el déficit de llegada menores de 72f; una caída precoz es posible si el aclaramiento "
         "supera a la producción",
    "C": "la hiperventilación compensadora por reclutamiento (ganancia común de ventilación) baja la PaCO2 al subir la "
         "carga; el pH sigue al HCO3 y a la PaCO2",
    "D": "como C, para 72f",
    "E": "el cristaloide restaura por un tiempo la precarga y la entrega; baja el déficit, con él la producción, y la FR "
         "sigue a la carga",
    "F": "los GR restauran el contenido de oxígeno; sin hemostasia el déficit puede volver",
    "G": "con hemostasia y reanimación el déficit termina y la carga se aclara en τ; la FR baja hacia la intrínseca",
    "H": "al aclararse la carga se apaga el reclutamiento y la PaCO2 vuelve hacia 40 mientras se recupera el HCO3",
    "I": "la parte de la FR que todavía mueve la carga no aclarada"}


#: The frozen ENVELOPE_REQUEST and FACULTY_QUESTIONS (English in the record), in Spanish, in the same order.
ENVELOPE_ES = ("FR a 120 min sin tratamiento, por caso (A, B): una envolvente educativa BAJO–ALTO, o ninguna",
               "PaCO2 / pH a 120 min sin tratamiento, por caso (C, D): una envolvente, o ninguna",
               "FR, PaCO2 y pH a 120 min tras el manejo definitivo (G, H): envolventes, o ninguna",
               "FR residual sobre la intrínseca tras la reanimación adecuada (I): una envolvente, o ninguna",
               "si las respuestas de la FR al cristaloide y a los GR (E, F) se acotan o sólo se informan")
QUESTIONS_ES = ("confirmar la semántica de la demanda relativa a la basal en W (el índice absoluto haría hipercápnica "
                "en reposo a la clase 1,1)",
                "mantener la ganancia de ventilación EXPLORATORY sobre su soporte conjunto, o adoptar una (no se "
                "propone ningún valor)",
                "las envolventes de arriba, si el veredicto es READY; ninguna se aplica en P2K-3")


def _case(case: str) -> str:
    return CASE_ES.get(case, case)


def render_decisiones(data: dict) -> str:
    return "\n".join(f"- **{FACULTY_ES.get(k, k)}**: {v}" for k, v in data["faculty"].items())


def render_semantica(data: dict) -> str:
    d = data["design"]
    lines = ["| magnitud | definición |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in d["semantics"].items()]
    lines += ["", "**Estados:** " + "; ".join(f"{k} = {v}" for k, v in d["status"].items()) + "."]
    lines += ["", "**FUTURE_RESPIRATORY_GENERALIZATION** (nada de esto se agrega en P2K-3):"]
    lines += [f"- {k}: {v}" for k, v in d["future"].items()]
    return "\n".join(lines)


def render_soportes(data: dict) -> str:
    d = data["design"]
    exact = "; ".join(f"{_case(c)} {_n(v, 4)}" for c, v in data["exact_ventilation_gains"].items())
    stated = "; ".join(f"{_case(c)} {_n(v, 3)}" for c, v in d["faculty_implied_gains"].items())
    windows = "; ".join(f"{_case(c)} {_n(w[0], 0)}–{_n(w[1], 0)} mmHg" for c, w in d["paco2_windows"].items())
    return "\n".join([
        d["candidate_rule"], "",
        f"- **Ganancia ácido → ventilación (común):** {', '.join(_n(g, 2) for g in d['ventilation_gains'])} por mEq/L "
        f"(EXPLORATORY). Ganancias que reproducirían exactamente la PaCO2 de autor: {exact} (las de la docencia: "
        f"{stated}).",
        f"- **FR (de P2K-2, sin cambio):** FR intrínseca {', '.join(_n(x, 0) for x in d['intrinsic_rr'])} rpm por "
        f"paciente; ganancia de frecuencia {', '.join(_n(g, 3) for g in d['drive_gains'])}; S = {_n(d['saturation'], 0)}.",
        f"- **Carga ácida (de P2K-2, sin cambio):** B {', '.join(_n(x) for x in d['steady_burdens'])} mEq/L × τ "
        f"{', '.join(_n(x, 0) for x in d['acid_taus'])} min; nunca se exige que suba.",
        f"- **Referencias:** HCO3 {_n(d['hco3_reference'], 0)} mEq/L y PaCO2 {_n(d['paco2_reference'], 0)} mmHg "
        "(COMMON_REFERENCE_PROVISIONAL); eficiencia ventilatoria 1 (STRUCTURAL_REFERENCE).",
        f"- **Tolerancias de llegada:** FR ± {_n(d['rr_tolerance'], 0)} rpm (26 y 24); PaCO2 ± "
        f"{_n(d['paco2_tolerance'], 0)} mmHg ({windows}); pH ± {_n(d['ph_tolerance'], 2)} sólo diagnóstico.",
        f"- **Lecturas diagnósticas congeladas (no filtran):** pH plausible {_n(d['ph_plausible'][0], 1)}–"
        f"{_n(d['ph_plausible'][1], 1)}; pregunta 3: FR a ≤ {_n(d['approach_rr'], 0)} rpm de la intrínseca y PaCO2 a ≤ "
        f"{_n(d['reasonable_paco2'], 0)} mmHg de 40."])


def render_desacople(data: dict) -> str:
    w = data["w_inputs"]
    v = data["validation"]
    lines = ["**Prueba estática** (lo que leen las funciones de W y las asignaciones de W en `ventilated_respiration`):", "",
             "| función o asignación | nombres que lee |", "|---|---|"]
    lines += [f"| `{k}` | {', '.join(f'`{x}`' for x in names)} |" for k, names in w["reads"].items()]
    lines += ["", f"Nombres prohibidos encontrados: {', '.join(w['leaks']) or 'ninguno'} (prohibidos: la FR, la FR "
                  "intrínseca, el impulso y sus parámetros, el lactato, D y el canal W).", "",
              f"**En el núcleo completo** ({v['compared']} corridas con la candidata): recalculada sobre los mismos estados "
              f"con otra ganancia de frecuencia, W, PaCO2 y pH idénticos: {_yes(v['rr_alone_moves_no_w'])} (la FR sí "
              f"cambió: {_yes(v['rr_moved'])}); con otra FR intrínseca, idénticos: "
              f"{_yes(v['intrinsic_alone_moves_no_w'])}; en orden inverso, idénticos: {_yes(v['order_independent'])}."]
    return "\n".join(lines)


def render_sondas(data: dict) -> str:
    p, ok = data["probes"], data["probes_pass"]
    b = p["base"]
    c = p["C"]["by_intrinsic"]
    g1, g5 = p["G"]["efficiency_1"], p["G"]["efficiency_0.5"]
    course = p["G"]["course"]
    rest = p["H"]["rows"]
    lines = [p["rule"], "", f"Llegada de la sonda: carga {_n(b['burden'])}, FR {_n(b['rr'])}, W {_n(b['w'], 2)}, PaCO2 "
             f"{_n(b['paco2'])}, pH {_n(b['ph'], 3)}.", "", "| sonda | resultado | pasa |", "|---|---|---|",
             f"| A · sube la carga 4 → 8 | FR {_n(b['rr'])} → {_n(p['A']['result']['rr'])}; W {_n(b['w'], 2)} → "
             f"{_n(p['A']['result']['w'], 2)}; PaCO2 {_n(b['paco2'])} → {_n(p['A']['result']['paco2'])} | {_yes(ok['A'])} |",
             f"| B · cambia sólo la FR (ganancia 2 → 4; S 25 → 15) | FR {_n(p['A']['result']['rr'])} → "
             f"{_n(p['B']['drive_gain_4']['rr'])} y {_n(p['B']['saturation_15']['rr'])}; W "
             f"{_n(p['B']['drive_gain_4']['w'], 2)} y {_n(p['B']['saturation_15']['w'], 2)} | {_yes(ok['B'])} |",
             "| C · cambia sólo la FR intrínseca (12 / 16 / 20) | FR " + " / ".join(_n(c[k]['rr']) for k in c) + "; W "
             + " / ".join(_n(c[k]['w'], 2) for k in c) + "; PaCO2 " + " / ".join(_n(c[k]['paco2']) for k in c)
             + f" | {_yes(ok['C'])} |",
             f"| D · carga fija, ganancia de ventilación 0,03 → 0,08 | W {_n(p['D']['gain_0.03']['w'], 2)} → "
             f"{_n(p['D']['gain_0.08']['w'], 2)}; PaCO2 {_n(p['D']['gain_0.03']['paco2'])} → "
             f"{_n(p['D']['gain_0.08']['paco2'])}; FR {_n(p['D']['gain_0.03']['rr'])} = {_n(p['D']['gain_0.08']['rr'])} "
             f"| {_yes(ok['D'])} |",
             f"| E · cambia sólo el lactato | lactato {_n(b['lactate'])} → {_n(p['E']['result']['lactate'])}; FR, W y "
             f"PaCO2 sin cambio | {_yes(ok['E'])} |",
             f"| F · cambia sólo D | D 0 → {_n(p['F']['result']['D'], 0)}; FR, W y PaCO2 sin cambio | {_yes(ok['F'])} |",
             f"| G · eficiencia 0,5 con FR alta | FR {_n(g5['rr'])} (igual con eficiencia 1); W {_n(g1['w'], 2)} → "
             f"{_n(g5['w'], 2)}; PaCO2 {_n(g1['paco2'])} → {_n(g5['paco2'])}. Curso de 20 min (eficiencia 1 → 0,5, carga "
             f"4 → 10): FR {_n(course[0]['rr'])} → {_n(course[-1]['rr'])}, PaCO2 {_n(course[0]['paco2'])} → "
             f"{_n(course[-1]['paco2'])} | {_yes(ok['G'])} |",
             f"| H · sin carga, demanda basal | {len(rest)} combinaciones (FR intrínseca × ganancia de frecuencia × "
             f"ganancia de ventilación): W = 1 en todas: {_yes(p['H']['w_is_1'])}; PaCO2 = 40 en todas: "
             f"{_yes(p['H']['paco2_is_reference'])}; FR = intrínseca: {_yes(p['H']['rr_is_intrinsic'])} | {_yes(ok['H'])} |",
             f"| I · demanda × 1,25 con la misma carga | W {_n(p['A']['result']['w'], 2)} → {_n(p['I']['demand_1.25']['w'], 2)}; "
             f"PaCO2 {_n(p['A']['result']['paco2'])} → {_n(p['I']['demand_1.25']['paco2'])}; FR sin cambio; la carga que "
             f"compensa por reclutamiento: {_n(p['I']['compensating_burden'])} mEq/L | {_yes(ok['I'])} |",
             f"| canal W ± 0,5 | FR, W y PaCO2 sin cambio | {_yes(ok['W_channel'])} |",
             f"| sin pulso | FR 0, W 0, sin PaCO2 | {_yes(ok['no_pulse'])} |"]
    return "\n".join(lines)


def render_llegada(data: dict) -> str:
    rr, pc, js = data["arrival_rr"], data["arrival_paco2"], data["joint_surface"]
    lines = [f"**FR (prueba analítica de P2K-2, ± 3):** {rr['count']} de {rr['of']} combinaciones (ganancia de frecuencia, "
             "FR intrínseca 57m, FR intrínseca 72f) compatibles: " + "; ".join(
                 f"({_n(g, 3)}, {_n(a, 0)}, {_n(b, 0)})" for g, a, b in rr["compatible"]) + ".", "",
             "**PaCO2 (± 3) y pH diagnóstico (± 0,03) por ganancia común de ventilación:**", "",
             "| ganancia | reclutamiento 57m | PaCO2 57m | pH 57m (error) | reclutamiento 72f | PaCO2 72f | pH 72f (error) | "
             "compatible |", "|---|---|---|---|---|---|---|---|"]
    for row in pc["rows"]:
        cells = []
        for case in CASES:
            cells += [_n(row["recruitment"][case], 3), f"{_n(row['paco2'][case])} ({_n(row['mismatch'][case])})",
                      f"{_n(row['ph'][case], 3)} ({_n(row['ph_error'][case], 3)}, {row['ph_class'][case]})"]
        lines.append(f"| {_n(row['gain'], 2)} | " + " | ".join(cells) + f" | {_yes(row['compatible'])} |")
    a, w = js["arrival_read"], js["with_acid_support"]
    sup = js["support"]
    lines += ["", "Entre paréntesis, la diferencia con la PaCO2 de autor (31 y 33) y con el pH de autor (7,37 y 7,40). El pH "
                  "no filtra: contaría dos veces el mismo HCO3 y la misma PaCO2.", "",
              "**Superficie conjunta de llegada (FR, luego PaCO2):**", "",
              "| | lo que lee la llegada | con el soporte ácido (× 9 pares B/τ) |", "|---|---|---|",
              f"| total | {a['total']} | {w['total']} |", f"| compatibles por FR | {a['rr_compatible']} | {w['rr_compatible']} |",
              f"| compatibles por PaCO2 | {a['paco2_compatible']} | {w['paco2_compatible']} |",
              f"| compatibles en conjunto | **{a['joint']}** | **{w['joint']}** |", "",
              "Soporte entre los compatibles en conjunto (sin elegir una combinación):", ""]
    labels = {"intrinsic_57m": "FR intrínseca 57m", "intrinsic_72f": "FR intrínseca 72f", "drive_gain":
              "ganancia de frecuencia", "ventilation_gain": "ganancia de ventilación", "B": "B", "tau": "τ"}
    for key, label in labels.items():
        lines.append(f"- **{label}:** " + ", ".join(f"{_n(float(k), 3).rstrip('0').rstrip(',')} ({v})"
                                                  for k, v in sorted(sup[key].items(), key=lambda kv: float(kv[0])))
                     + ".")
    lines += ["- B y τ: la llegada no los lee (la carga de llegada es la del HCO3 de autor); cada par se lleva con cada "
              "candidato compatible en conjunto.", "",
              f"Rechazos analíticos en la llegada: {data['arrival_rejections']['ANALYTIC_REJECTION']}. Sensibilidad a la "
              "semántica de la demanda (índice absoluto, no usado): con la demanda 1,1 serían compatibles las ganancias "
              + ", ".join(_n(g, 2) for g in data["demand_semantics"]["1.1"]["compatible"]) + "; con 1,0, "
              + ", ".join(_n(g, 2) for g in data["demand_semantics"]["1"]["compatible"]) + "."]
    return "\n".join(lines)


def _table(t: dict) -> list:
    rows = ["| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | "
            "demanda | intervención |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in sorted(t["minutes"], key=int):
        c = t["minutes"][m]
        u = t["upstream"][m]
        intervention = (f"cristaloide {_s(u['crystalloid_ml'], 0)} mL; GR {_s(u['prbc_units'], 1)} U; hemostasia "
                        f"{t['haemostasis'][m]}/{t['trajectories']}")
        rows.append(f"| {m} | {_s(c['rr'])} | {_s(c['frequency_drive'])} | {_s(c['burden'])} | {_s(c['hco3'])} | "
                    f"{_s(c['recruitment'], 3)} | {_s(c['w'], 2)} | {_s(c['paco2'])} | {_s(c['ph'], 2)} | "
                    f"{_s(u['lactate'])} | {_s(u['D'], 0)} | {_s(u['deficit'], 2)} | {_s(c['metabolic_demand'], 2)} | "
                    f"{intervention} |")
    return rows


def render_reconstruccion(data: dict) -> str:
    tables = data["reconstruction"]
    lines = [data["design"]["reconstruction_rule"], "",
             "Mediana [rango] a la ganancia de tono intermedia g = 0,5. La FR y su parte de impulso se leen sobre "
             "(trayectoria, B/τ, ganancia de frecuencia, FR intrínseca); el reclutamiento, W, la PaCO2 y el pH sobre "
             "(trayectoria, B/τ, ganancia de ventilación); la carga y el HCO3 sobre (trayectoria, B/τ). Eficiencia "
             "ventilatoria 1 y razón de demanda 1 en todas. Las otras ganancias de tono están en el JSON."]
    for factor in ("x1", "x1.1"):
        for name in ("P1", "P2", "P3", "P4"):
            for case in CASES:
                t = tables[f"{factor} g0.5 {name} {case}"]
                intrinsic = sorted({c[1] for c in t["rr_candidates"]})
                gains = sorted({c[0] for c in t["rr_candidates"]})
                lines += ["", f"**{SCENARIO_ES[name]} · {_case(case)} · demanda {factor[1:].replace('.', ',')}** "
                              f"({t['trajectories']} trayectorias; FR intrínseca {', '.join(_n(x, 0) for x in intrinsic)}; "
                              f"ganancia de frecuencia {', '.join(_n(x, 2) for x in gains)}; ganancia de ventilación "
                              f"{', '.join(_n(x, 2) for x in t['ventilation_gains'])}; eficiencia {_n(t['efficiency'], 0)})",
                          ""] + _table(t)
    return "\n".join(lines)


def render_preguntas(data: dict) -> str:
    q = data["key_questions"]
    q1, q2, q3, q4 = (q["1_resting_hypercapnia"], q["2_paco2_toward_40"], q["3_rr_near_intrinsic_with_reasonable_paco2"],
                      q["4_72f_early_dip"])
    old = "; ".join(f"{_case(c)} {_s(v)}" for c, v in q1["p2k2_over_the_same_rr_candidates"].items())
    post = q["post_resuscitation"]
    six = q["6_rr_paco2_directions"]
    return "\n".join([
        f"1. **¿La FR intrínseca baja implica hipercapnia en reposo?** No. Sin carga y con la demanda basal, la PaCO2 es 40 "
        f"mmHg para toda FR intrínseca y toda ganancia de ventilación: {_yes(q1['all_reference'])}. Con el mapeo de P2K-2, "
        f"sobre los mismos candidatos de FR, era {old} mmHg.",
        f"2. **¿La PaCO2 vuelve hacia 40 al aclararse la carga?** En R4, a los 120 min la PaCO2 está tan o más cerca de 40 "
        f"que a la llegada en {_share(q2['r4_toward'])} combinaciones; PaCO2 a 120: "
        + "; ".join(f"{_case(c)} {_s(v)}" for c, v in q2["r4_paco2_120"].items()) + " mmHg (distancia a 40: "
        + "; ".join(f"{_case(c)} {_s(v)}" for c, v in q2["r4_distance_120"].items()) + "). Sin tratamiento (R1), a 120: "
        + "; ".join(f"{_case(c)} {_s(v)}" for c, v in q2["r1_paco2_120"].items()) + " mmHg. Sonda H: sin carga y con "
        "la demanda basal, W = 1 y PaCO2 = 40 a toda FR intrínseca.",
        "3. **¿La FR puede acercarse a una intrínseca baja con una PaCO2 razonable?** Estructuralmente sí: al aclararse la "
        "carga, la FR tiende a la intrínseca y la PaCO2 a 40, sin que una dependa de la otra (sonda H). En R4 a los 120 min, "
        "con la intrínseca más baja de cada caso ("
        + ", ".join(f"{_case(c)} {_n(v, 0)}" for c, v in q3["lowest_intrinsic"].items()) + "), la FR sigue "
        + "; ".join(f"{_case(c)} {_s(v)}" for c, v in q3["rr_120_above_intrinsic"].items()) + " rpm sobre ella; "
        "a ≤ 3 rpm: " + "; ".join(f"{_case(c)} {_share(v)}" for c, v in q3["rr_near"].items())
        + "; además con la PaCO2 a ≤ 5 mmHg de 40: " + "; ".join(f"{_case(c)} {_share(v)}" for c, v in
                                                                  q3["joint_share"].items()) + ".",
        f"4. **¿Sigue siendo posible la caída precoz leve de la FR de 72f sin lactato?** Sí: en {_share(q4['dip'])} "
        "combinaciones (" + "; ".join(f"B {k.replace('.', ',')}: {_share(v)}" for k, v in q4["by_b"].items())
        + f"); profundidad {_s(q4['depth'], 2)} rpm. Mecanismo: el aclaramiento A0 / τ supera a la producción "
        "(B / τ) × d0 cuando B × d0 < A0; el lactato no llega a ningún término de la FR (sonda E).",
        f"5. **¿El lactato y la FR pueden moverse en sentidos opuestos?** Sí, al menos un minuto en "
        f"{_share(q['5_lactate_rr_opposite'])} combinaciones.",
        "6. **¿La FR y la PaCO2 pueden reflejar respuestas distintas de frecuencia y de reclutamiento?** En las "
        f"trayectorias GI (eficiencia 1, demanda basal) las dos siguen a la misma carga: se mueven en sentidos opuestos en "
        f"{_share(six['opposite_direction'])} combinaciones y en el mismo sentido en {_share(six['same_direction'])}. Sus "
        "magnitudes dependen de ganancias distintas (§11: la FR no reacciona a la de ventilación ni la PaCO2 a la de "
        f"frecuencia). Pueden disociarse cuando cambian la eficiencia o la demanda: curso de la sonda G "
        f"{_yes(six['probe_G_course'])}, sonda I {_yes(six['probe_I'])}, sondas B y D {_yes(six['probe_B_and_D'])}.",
        f"- **Tras la reanimación (R4):** 15 min después de la hemostasia la FR sigue "
        f"{_s(post['rr_15_after_haemostasis_above_intrinsic'])} rpm sobre la intrínseca (≥ 1 rpm en "
        f"{_share(post['no_instant_normalization'])}); el minuto de la hemostasia no mueve la FR más que otro minuto en "
        f"{_share(post['rr_haemostasis_step'])}, ni la PaCO2 en {_share(post['paco2_haemostasis_step'])}."])


def render_identificabilidad(data: dict) -> str:
    i = data["identifiability"]
    lines = ["| magnitud | clase | detalle |", "|---|---|---|"]
    for key, label in IDENT_ES.items():
        item = i[key]
        detail = item.get("why") or ("valores que sobreviven: " + ", ".join(_n(v, 3 if "gain" in key else 0)
                                                                            for v in item.get("values", [])))
        lines.append(f"| {label} | {item['class']} | {detail} |")
    lines += ["", "**Compuestos observables en la llegada** (sobre los candidatos compatibles en conjunto):", "",
              "| caso | incremento de FR | reclutamiento | PaCO2 predicha | pH predicho |", "|---|---|---|---|---|"]
    for case, comp in i["composites"].items():
        cells = [f"{_s(comp['arrival_rr_increment']['spread'])} ({comp['arrival_rr_increment']['class']})",
                 f"{_s(comp['arrival_recruitment']['spread'], 3)} ({comp['arrival_recruitment']['class']})",
                 f"{_s(comp['predicted_arrival_paco2']['spread'])} ({comp['predicted_arrival_paco2']['class']})",
                 f"{_s(comp['predicted_arrival_ph']['spread'], 3)} ({comp['predicted_arrival_ph']['class']})"]
        lines.append(f"| {_case(case)} | " + " | ".join(cells) + " |")
    lines += ["", i["rule"]]
    return "\n".join(lines)


def render_dependencias(data: dict) -> str:
    d = data["dependencies"]
    q = d["by_quantity"]
    units = {"burden": ("carga", "mEq/L", 2), "rr": ("FR", "rpm", 2), "paco2": ("PaCO2", "mmHg", 2), "ph": ("pH", "", 4)}
    lines = ["| magnitud a 120 min (mediana por tabla) | demanda 1,0 vs 1,1: diferencia | tono g: dispersión |",
             "|---|---|---|"]
    for key, (label, unit, digits) in units.items():
        lines.append(f"| {label} {unit} | {_s(q[key]['demand_median_difference'], digits)} | "
                     f"{_s(q[key]['tone_median_spread'], digits)} |")
    lines += ["", "| dimensión | vía | estado |", "|---|---|---|",
              f"| demanda 1,0 / 1,1 | {d['demand']['path']} | causal; se lleva |",
              f"| ganancia de tono g | {d['tone_gain']['path']} | causal pequeña; se lleva |",
              f"| MAP_set | {d['map_set']['path']} | {d['map_set']['proof']} |",
              f"| ganancia del barorreflejo | {d['baroreflex_gain']['path']} | {d['baroreflex_gain']['proof']} |",
              f"| región latente de FC | {d['hr_latent']['path']} | {d['hr_latent']['proof']} |",
              "", "Se multiplican sólo: " + ", ".join(d["multiplied"]) + "."]
    return "\n".join(lines)


def render_paquete(data: dict) -> str:
    lines = ["Preparado, **no aprobado** (PREPARED_NOT_APPROVED). Bajo / mediana / alto sobre trayectorias × B/τ × los "
             "candidatos compatibles en conjunto que lee cada observable. Sensibilidad: diferencia entre la mayor y la "
             "menor mediana al agrupar por cada factor («sin vía»: el observable no lee ese factor).", ""]
    for letter, item in data["decision_pack"].items():
        rationale = RATIONALE_ES[letter]
        lines += [f"**{letter} · {PACK_ES[letter]}.** {rationale[0].upper() + rationale[1:]}.", "",
                  "| observable | bajo | mediana | alto | n | " + " | ".join(FACTORS_ES.values()) + " |",
                  "|---|---|---|---|---|" + "---|" * len(FACTORS_ES)]
        for name, summary in item["distributions"].items():
            parts = name.split()
            digits = 3 if parts[-1] == "pH" else 1
            extra = " ".join(parts[2:]).replace("RR120", "FR a 120 min")
            label = _case(parts[1]) + (" · " + extra if extra else "")
            dist = summary["distribution"]
            sens = []
            for factor in FACTORS_ES:
                entry = summary[factor]
                sens.append("sin vía" if entry.get("path") == "NONE" else _n(entry["range"], digits + 1))
            lines.append(f"| {label} | {_n(dist.get('low'), digits)} | {_n(dist.get('median'), digits)} | "
                         f"{_n(dist.get('high'), digits)} | {dist.get('n', 0)} | " + " | ".join(sens) + " |")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_no_regresion(data: dict) -> str:
    v = data["validation"]
    lines = [f"Validación contra el núcleo: {v['compared']} corridas completas con el candidato de validación "
             f"(ganancia de frecuencia {_n(v['candidate'][0], 1)}, FR intrínseca {_n(v['candidate'][1], 0)} / "
             f"{_n(v['candidate'][2], 0)}, B {_n(v['candidate'][3])}, τ {_n(v['candidate'][4], 0)}, ganancia de "
             f"ventilación {_n(v['candidate'][5], 2)}) y las mismas {v['compared']} sin él.", "",
             f"- Módulo de ventilación = álgebra factorizada en cada estado: {_yes(v['equal'])} (diferencia máxima "
             f"{v['max_abs_diff']:g}); razón de demanda 1 en todos los estados: {_yes(v['demand_ratio_one'])}; FR del núcleo "
             f"= FR del módulo: {_yes(v['core_rr_equal'])}.",
             "- Fisiología previa, filas y estados con la candidata iguales a sin ella:", "",
             "| dominio | igual |", "|---|---|"]
    lines += [f"| {label} | {_yes(v['domains'][k])} |" for k, label in DOMAINS_ES.items()]
    rep = data["p2k2_reproduced"]
    lines += ["", f"- Todo el estado salvo la carga ácida igual: {_yes(v['upstream_equal'])}; FR por defecto = la de P2K-1: "
                  f"{_yes(v['default_rr_equal'])}.",
              f"- P2K-1 recalculado igual a su registro: {_yes(data['p2k1_unchanged'])}; región de P2J-3 recalculada "
              "igual: " + ", ".join(f"{k} {_yes(x)}" for k, x in data["pressure_tone_unchanged"].items()) + ".",
              f"- P2K-2 reproducido en vivo: compatibilidad de llegada {_yes(rep['arrival_compatibility'])}, sondas "
              f"{_yes(rep['probes'])}, tablas aguas arriba {_yes(rep['upstream_tables'])}.",
              "- Archivos del núcleo y módulo de P2K-2 con sus huellas de `cbec249`: "
              + ", ".join(f"`{k.split('/')[-1]}` {_yes(x)}" for k, x in data["core_unchanged"].items()) + ".",
              f"- Rechazos: ANALYTIC_REJECTION {data['rejections']['ANALYTIC_REJECTION']}, SIMULATION_REJECTION "
              f"{data['rejections']['SIMULATION_REJECTION']}. Valores: pH {_n(data['plausible']['ph_low'], 3)}–"
              f"{_n(data['plausible']['ph_high'], 3)} (fuera de 6,8–7,8: {data['plausible']['outside']}); PaCO2 mínima "
              f"{_n(data['plausible']['paco2_low'])} mmHg; W mínima {_n(data['plausible']['w_low'], 3)}; W o PaCO2 no "
              f"positivas: {data['plausible']['non_positive']}."]
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    lines = [f"**{v['verdict']}**", "", "| criterio | se cumple |", "|---|---|"]
    lines += [f"| {CRITERIA_ES[k]} | {_yes(v['checks'][k])} |" for k in CRITERIA_ES]
    if data.get("envelope_request"):
        if len(data["envelope_request"]) != len(ENVELOPE_ES):
            raise ValueError("the envelope request changed: update its Spanish rendering")
        lines += ["", "**Envolventes observables que se piden a la docencia (no se aplican en P2K-3):**"]
        lines += [f"- {x}" for x in ENVELOPE_ES]
    if len(data["faculty_questions"]) != len(QUESTIONS_ES):
        raise ValueError("the faculty questions changed: update their Spanish rendering")
    lines += ["", "**Otras decisiones que se piden:**"] + [f"- {x}" for x in QUESTIONS_ES]
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return (f"P2J-3 recalculado: {e['p2j3_blood_runs']} trayectorias de sangre y {e['p2j3_counterfactual_runs']} "
            f"contrafactuales. {e['deficit_trajectories']} trayectorias de déficit reconstruidas una vez; la carga se "
            f"integra para {e['acid_pairs']} pares (B, τ); la FR es álgebra de la carga para "
            f"{e['rr_candidates']['gi_bleed_57m']} (57m) y {e['rr_candidates']['gi_bleed_72f']} (72f) pares (ganancia, FR "
            f"intrínseca) y W / PaCO2 / pH para {e['ventilation_gains']} ganancias de ventilación. Las tablas y el "
            f"paquete A–I no las cruzan; sólo las preguntas 3 y 6, que por definición piden la relación entre FR y "
            f"PaCO2, recorren los dos lados (con los conjuntos de la PaCO2 calculados una vez por ganancia). La llegada se resolvió analíticamente ({e['arrival_combinations']} combinaciones con el soporte "
            f"ácido). Corridas completas del núcleo: {e['core_validation_runs']} (validación). Barrido cartesiano: "
            f"{_yes(e['cartesian_sweep'])}; FR heredada leída: {_yes(e['legacy_read'])}.")


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the P2K-3 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
