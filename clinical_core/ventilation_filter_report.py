"""P2K-4 report: the generated blocks of docs/revision/P2K4_FILTRO_ENVOLVENTES_RESPIRATORIAS.md.

    python -m clinical_core.ventilation_filter_report --write <document> --data <the P2K-4 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
filter's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _s, _yes
from .lactate_rebuild_report import CASE_ES

NAMES = ("decisiones", "reglas", "filtro", "demanda", "latentes", "observables", "contrafactuales", "acidemia",
         "r3r4", "no_regresion", "veredicto", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
CASES = ("gi_bleed_57m", "gi_bleed_72f")
FACULTY_ES = {"decided": "fecha", "closed": "P2K-3", "goal": "objetivo", "priority": "prioridad del proyecto",
              "demand": "demanda en W", "support": "soporte latente", "references": "referencias y llegada",
              "untreated_ph": "pH sin tratamiento", "crystalloid": "E · cristaloide", "prbc": "F · GR",
              "r3_r4": "R3 / R4", "early_stop": "parada temprana", "exit": "criterio de salida", "scope": "alcance"}
RULE_ES = {"SIMULATION": "estructural (SIMULATION)", "ARRIVAL_RR": "FR de llegada", "ARRIVAL_PACO2": "PaCO2 de llegada",
           "A": "A · FR R1 57m", "B": "B · FR R1 72f", "G": "G · FR R4 57m", "G2": "G2 · FR R4 72f",
           "H_PACO2": "H · PaCO2 R4", "H_PH": "H · pH R4", "I": "I · FR residual R4", "C": "C · PaCO2 R1 57m",
           "D": "D · PaCO2 R1 72f", "E": "E · cristaloide", "F": "F · GR"}
CLASS_ES = {"SIMULATION_REJECTION": "simulación", "ARRIVAL_RR_REJECTION": "FR de llegada",
            "ARRIVAL_PACO2_REJECTION": "PaCO2 de llegada", "RR_ENVELOPE_REJECTION": "envolvente de FR",
            "PACO2_ENVELOPE_REJECTION": "envolvente de PaCO2", "PH_ENVELOPE_REJECTION": "envolvente de pH",
            "TREATMENT_DIRECTION_REJECTION": "dirección del tratamiento"}
DIM_ES = {"drive_gain": "ganancia ácido → FR", "intrinsic_57m": "FR intrínseca 57m", "intrinsic_72f": "FR intrínseca 72f",
          "ventilation_gain": "ganancia ácido → ventilación", "B": "B", "tau": "τ de aclaramiento ácido"}
CRITERIA_ES = {"upstream_unchanged": "fisiología previa intacta (P2J-3, P2K-1, P2K-3, comparadores = núcleo)",
               "comparators_matched": "cada comparador omite sólo su exposición",
               "survivors_exist": "sobrevive al menos un candidato",
               "filter_consistent": "la recomputación directa iguala al filtro",
               "envelopes_hold": "los observables de los supervivientes cumplen A–I",
               "arrival_compatible": "FR y PaCO2 de llegada en sus ventanas",
               "ph_coherent": "pH coherente (6,8–7,8; banco ± 0,005)",
               "treatment_responses_coherent": "respuestas a los tratamientos coherentes",
               "r3_r4_physiological": "R3 / R4: convergencia fisiológica, sin colapso",
               "nothing_approved": "nada aprobado"}
DOMAINS_ES = {"blood_state": "BloodState", "output": "gasto", "pressure_tone": "presión / tono",
              "delivery_deficit": "DO2 / déficit efectivo", "D": "D", "lactate": "lactato",
              "hr_baroreflex": "FC / barorreflejo"}
PAIR_ES = {"crystalloid": "E · cristaloide (R2 frente a R1)", "prbc_R3": "F · GR sin hemostasia (R3 frente a R3 sin GR)",
           "prbc_R4_unit1": "F · unidad 1 en R4 (frente a L3 sin ella)",
           "prbc_R4_unit2": "F · unidad 2 en R4 (frente a L3 sin ella)"}
MINUTE_ES = {"crystalloid": ("cristaloide completo", "120"), "prbc_R3": ("unidad 1 completa", "unidad 2 completa", "120"),
             "prbc_R4_unit1": ("unidad 1 completa", "120"), "prbc_R4_unit2": ("unidad 2 completa", "120")}
KLASS_ES = {"RESPIRATORY_AND_PERFUSION_IMPROVE": "mejoran respiración y perfusión",
            "RESPIRATORY_SIGNAL_NONIMPROVING_WITH_PERFUSION_IMPROVEMENT": "mejora la perfusión, la señal respiratoria no",
            "RESPIRATORY_IMPROVING_WITH_PERFUSION_WORSENING": "mejora la respiración, empeora la perfusión",
            "RESPIRATORY_UNCHANGED_WITH_PERFUSION_WORSENING": "empeora la perfusión, la respiración no cambia",
            "RESPIRATORY_AND_PERFUSION_WORSEN": "empeoran ambas (rechaza)", "NO_PERFUSION_CHANGE": "sin cambio de perfusión",
            "COMPARATOR_ARREST_WITH_TREATED_BREATHING": "el comparador sin pulso, el tratado respira",
            "TREATED_ARREST_WITH_COMPARATOR_BREATHING": "el tratado sin pulso (rechaza)",
            "NO_COMPARISON_BOTH_ARRESTED": "ambos sin pulso", "NO_COMPARISON_IMPOSSIBLE_VALUE": "valor imposible"}
R3R4_ES = {"PHYSIOLOGICAL_RESPIRATORY_CONVERGENCE": "convergencia respiratoria fisiológica",
           "RESPIRATORY_OUTPUTS_DISTINCT": "salidas respiratorias distintas",
           "SCENARIO_STATE_COLLAPSE_BUG": "colapso de escenario (STOP)"}
OBS_ES = (("arrival_rr", "FR de llegada", 1), ("arrival_paco2", "PaCO2 de llegada", 1),
          ("arrival_ph_diagnostic", "pH de llegada (diagnóstico)", 3), ("untreated_rr_120", "FR a 120 · R1", 1),
          ("untreated_paco2_120", "PaCO2 a 120 · R1", 1), ("untreated_ph_120", "pH a 120 · R1", 3),
          ("untreated_ph_lowest_0_120", "pH mínimo 0–120 · R1", 3), ("definitive_rr_120", "FR a 120 · R4", 1),
          ("definitive_paco2_120", "PaCO2 a 120 · R4", 1), ("definitive_ph_120", "pH a 120 · R4", 3),
          ("residual_rr_above_intrinsic_120", "FR − intrínseca a 120 · R4", 1))


SIGN_ES = {"rr_follows_burden": "la FR sigue a la carga", "paco2_follows_burden": "la PaCO2 sigue a la carga"}


def _minute(value) -> str:
    return "ninguna" if value is None else f"minuto {value}"


def _int(value) -> str:
    return f"{value:,}".replace(",", " ")


def _demand(key: str) -> str:
    return key.replace(".", ",") if "." in key else f"{key},0"


def render_decisiones(data: dict) -> str:
    return "\n".join(f"- **{FACULTY_ES.get(k, k)}**: {v}" for k, v in data["design"]["faculty"].items())


def render_reglas(data: dict) -> str:
    d = data["design"]
    lines = ["| regla | qué exige |", "|---|---|"]
    lines.append(f"| llegada | FR 57m {_n(d['arrival_rr']['gi_bleed_57m'][0], 0)}–{_n(d['arrival_rr']['gi_bleed_57m'][1], 0)}, "
                 f"72f {_n(d['arrival_rr']['gi_bleed_72f'][0], 0)}–{_n(d['arrival_rr']['gi_bleed_72f'][1], 0)}; "
                 f"PaCO2 57m {_n(d['arrival_paco2']['gi_bleed_57m'][0], 0)}–{_n(d['arrival_paco2']['gi_bleed_57m'][1], 0)}, "
                 f"72f {_n(d['arrival_paco2']['gi_bleed_72f'][0], 0)}–{_n(d['arrival_paco2']['gi_bleed_72f'][1], 0)}; "
                 "pH sólo diagnóstico |")
    for letter, envelope in d["envelopes"].items():
        lines.append(f"| {letter} | {envelope['text']} |")
    lines.append(f"| pH sin tratamiento | {d['extreme_rule']} |")
    lines += ["", f"**Orden congelado:** {' → '.join(RULE_ES[r] for r in d['order'])}.", "",
              f"**Comparadores:** {d['comparator_rule']}", "", f"**Señal respiratoria:** {d['signal_rule']}", "",
              f"**Soporte latente:** " + "; ".join(f"{DIM_ES[k]} {', '.join(_n(x, 2 if k == 'ventilation_gain' else 1) for x in v)}"
                                                for k, v in d["values"].items())
              + f" ({_int(data['efficiency']['latent_combinations']) if 'efficiency' in data else '1 620'} combinaciones); "
              "ganancia 0,08 excluida por la docencia."]
    return "\n".join(lines)


def render_filtro(data: dict) -> str:
    lines = []
    for key, d in data.get("demands", {}).items():
        f = d["filter"]
        lines += [f"**Demanda {_demand(key)}.** Entran {_int(f['entering'])} candidatos ({_int(f['upstream_units'])} "
                  f"supervivientes de P2J-3 × 1 620 combinaciones latentes, por tono: "
                  + ", ".join(f"g {_demand(g)} {_int(v['entering'])}" for g, v in f["by_tone_gain"].items())
                  + f"); sobreviven **{_int(f['survivors'])}** ("
                  + ", ".join(f"g {_demand(g)} {_int(v['survivors'])}" for g, v in f["by_tone_gain"].items())
                  + f"); {_int(f['latent_survivors'])} combinaciones latentes distintas; "
                  f"{_int(f['upstream_units_with_survivors'])} de {_int(f['upstream_units'])} unidades aguas arriba con "
                  "algún superviviente.", "",
                  "| regla | primer fallo | cualquier fallo | fallo único |", "|---|---|---|---|"]
        for rule in data["design"]["order"]:
            lines.append(f"| {RULE_ES[rule]} | {_int(f['first_failure'][rule])} | {_int(f['any_failure'][rule])} | "
                         f"{_int(f['only_failure'][rule])} |")
        lines += ["", "| clase de rechazo | primer fallo | cualquier fallo |", "|---|---|---|"]
        for klass in CLASS_ES:
            lines.append(f"| {CLASS_ES[klass]} | {_int(f['rejection_classes_first'][klass])} | "
                         f"{_int(f['rejection_classes_any'][klass])} |")
        top = sorted(((v, k) for k, v in f["overlap"].items() if v), reverse=True)[:8]
        lines += ["", "Pares de fallos más frecuentes: " + ("; ".join(
            f"{' + '.join(RULE_ES[r] for r in k.split('+'))} {_int(v)}" for v, k in top) or "ninguno") + ".", ""]
    return "\n".join(lines).rstrip()


def render_demanda(data: dict) -> str:
    cross = data.get("cross_demand", {})
    names = {"ROBUST_ACROSS_DEMAND": "en ambas demandas", "DEMAND_1_0_ONLY": "sólo con demanda 1,0",
             "DEMAND_1_1_ONLY": "sólo con demanda 1,1", "DEMAND_INCOMPATIBLE": "en ninguna"}
    lines = ["Diagnóstico, no criterio: sobre las 1 620 combinaciones latentes.", "",
             "| clase | combinaciones | valores que aparecen |", "|---|---|---|"]
    for name in ("ROBUST_ACROSS_DEMAND", "DEMAND_1_0_ONLY", "DEMAND_1_1_ONLY", "DEMAND_INCOMPATIBLE"):
        item = cross.get(name)
        if item is None:
            continue
        support = "; ".join(f"{DIM_ES[k]} {', '.join(_n(x, 2 if k == 'ventilation_gain' else 1) for x in v)}"
                            for k, v in item["support"].items() if v) or "—"
        lines.append(f"| {name} ({names[name]}) | {_int(item['count'])} | {support} |")
    return "\n".join(lines)


def render_latentes(data: dict) -> str:
    lines = ["| parámetro | demanda | clase | valores que sobreviven | combinaciones por valor |", "|---|---|---|---|---|"]
    for key, d in data.get("demands", {}).items():
        for dim, item in d["latent_support"].items():
            digits = 2 if dim == "ventilation_gain" else 1
            lines.append(f"| {DIM_ES[dim]} | {_demand(key)} | {item['class']} | "
                         f"{', '.join(_n(v, digits) for v in item['values']) or '—'} | "
                         + ", ".join(f"{k.replace('.', ',')}: {_int(n)}" for k, n in
                                     item["latent_combinations_by_value"].items()) + " |")
    lines += ["", data["design"]["identifiability_rule"]]
    return "\n".join(lines)


def render_observables(data: dict) -> str:
    lines = ["Bajo / mediana / alto sobre los supervivientes (entradas únicas: trayectoria × subcombinación latente que "
             "el observable lee).", "", "| observable | demanda | 57m | 72f |", "|---|---|---|---|"]
    for key, d in data.get("demands", {}).items():
        o = d["observed"]["observables"]
        for name, label, digits in OBS_ES:
            cells = [_s(o.get(f"{name} {case}"), digits) for case in CASES]
            lines.append(f"| {label} | {_demand(key)} | {cells[0]} | {cells[1]} |")
    return "\n".join(lines)


def render_contrafactuales(data: dict) -> str:
    lines = []
    for key, d in data.get("demands", {}).items():
        o, classes = d["observed"]["observables"], d["observed"]["classes"]
        lines += [f"**Demanda {_demand(key)}.**", "",
                  "| comparación | minuto | caso | clases | Δ carga | Δ FR | Δ PaCO2 | Δ pH | Δ déficit |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for tag, label in PAIR_ES.items():
            for j, minute in enumerate(MINUTE_ES[tag]):
                for case in CASES:
                    counts = classes.get(f"{tag} m{j} {case}", {})
                    text = "; ".join(f"{KLASS_ES.get(k, k)} {_int(v)}" for k, v in sorted(counts.items())) or "—"
                    get = lambda q, digits=2: _s(o.get(f"{tag} delta_{q} m{j} {case}"), digits)
                    lines.append(f"| {label} | {minute} | {CASE_ES[case]} | {text} | {get('burden')} | "
                                 f"{_s(o.get(f'{tag} delta_rr m{j} {case}'), 2)} | {get('paco2')} | {get('ph', 4)} | "
                                 f"{get('deficit', 3)} |")
        signs = d["observed"]["signs"]
        lines += ["", "La FR y la PaCO2 siguen a la carga en cada lectura: "
                  + "; ".join(f"{SIGN_ES[k]} {_int(v['held'])} de {_int(v['checked'])}" for k, v in signs.items())
                  + ".", ""]
    return "\n".join(lines).rstrip()


def render_acidemia(data: dict) -> str:
    lines = []
    for key, d in data.get("demands", {}).items():
        x = d["observed"]["extreme_acidemia"]
        share = x["flagged"] / x["survivors"] if x["survivors"] else 0.0
        lines.append(f"- **Demanda {_demand(key)}:** {_int(x['flagged'])} de {_int(x['survivors'])} supervivientes "
                     f"({_n(100 * share, 1)} %) con pH sin tratamiento < 7,00 en algún minuto 0–120 (57m "
                     f"{_int(x['by_case']['gi_bleed_57m'])}, 72f {_int(x['by_case']['gi_bleed_72f'])}).")
        low = x.get("lowest")
        if low:
            lines.append(f"  - pH mínimo {_n(low['ph'], 3)} ({CASE_ES[low['case']]}, minuto {low['minute']}): carga "
                         f"{_n(low['burden'], 2)} mEq/L, déficit efectivo {_n(low['deficit'], 3)}, PaCO2 "
                         f"{_n(low['paco2'], 1)} mmHg, FR {_s(low['rr'], 1)} rpm"
                         + (f"; marcado {low['flag']}" if low.get("flag") else "") + ".")
    lines.append("- Diagnóstico, nunca un rechazo (decisión docente): pasa a CONSCIOUSNESS_COLLAPSE_REVIEW.")
    return "\n".join(lines)


def render_r3r4(data: dict) -> str:
    lines = []
    for key, d in data.get("demands", {}).items():
        r = d["observed"]["r3r4"]
        lines.append(f"- **Demanda {_demand(key)}:** " + "; ".join(f"{R3R4_ES[k]} {_int(v)}" for k, v in
                                                                    r["classes"].items()) + " pares.")
        for pair in r["pairs"][:2]:
            u, g = pair["underlying"], pair["gap"]
            if not u.get("complete"):
                continue
            lines.append(
                f"  - {CASE_ES[pair['case']]} (conjunto de GR {pair['q']}): hemostasia R3 {_minute(u['haemostasis'][0])}, R4 "
                f"{_minute(u['haemostasis'][1])}; sangrado a 120 {_n(u['bleed_rate_120'][0], 2)} frente a "
                f"{_n(u['bleed_rate_120'][1], 2)} mL/min; pérdida acumulada {_n(u['shed_ml_120'][0], 0)} frente a "
                f"{_n(u['shed_ml_120'][1], 0)} mL; volumen circulante {_n(u['volume_ml_120'][0], 0)} frente a "
                f"{_n(u['volume_ml_120'][1], 0)} mL; contenido eritrocitario {_n(u['red_cells_120'][0], 3)} frente a "
                f"{_n(u['red_cells_120'][1], 3)}; Hb {_n(u['hb_120'][0], 4)} frente a {_n(u['hb_120'][1], 4)}; gasto "
                f"{_n(u['output_120'][0], 3)} frente a {_n(u['output_120'][1], 3)}; DO2 relativa "
                f"{_n(u['delivery_120'][0], 3)} frente a {_n(u['delivery_120'][1], 3)}; déficit "
                f"{_n(u['deficit_120'][0], 3)} frente a {_n(u['deficit_120'][1], 3)} (máxima diferencia 0–120 "
                f"{_n(u['deficit_max_abs_difference'], 3)}); misma cronología de GR y cristaloide: "
                f"{_yes(u['chronology_same'])}. Diferencias respiratorias máximas a 120: carga {_n(g['burden'], 3)}, "
                f"FR {_n(g['rr'], 2)}, W {_n(g['w'], 3)}, PaCO2 {_n(g['paco2'], 2)}, pH {_n(g['ph'], 4)}. "
                f"Clase: {R3R4_ES[pair['class']]}.")
    lines.append(f"- {data['design']['r3r4_rule']}")
    return "\n".join(lines)


def render_no_regresion(data: dict) -> str:
    rep, comp = data.get("p2k3_reproduced", {}), data.get("comparator_validation", {})
    lines = ["| comprobación | resultado |", "|---|---|"]
    for k, v in data["closed_unchanged"].items():
        lines.append(f"| `{k}` con su huella de `ef2cfe8` | {_yes(v)} |")
    names = {"reconstruction": "reconstrucción R1–R4 de P2K-3", "decision_pack": "paquete A–I de P2K-3",
             "rejections": "rechazos de P2K-3", "plausible": "plausibilidad de P2K-3",
             "validation": "validación de P2K-3 contra el núcleo (96 corridas)", "p2k1_unchanged": "P2K-1",
             "p2j3_region": "región de P2J-3"}
    for k, v in rep.items():
        lines.append(f"| {names.get(k, k)}: se reproduce igual a su registro | {_yes(v)} |")
    if comp:
        lines.append(f"| comparadores nuevos (CF1, CF2, R3 sin GR) = núcleo, {comp['compared']} corridas con y sin la "
                     f"candidata | {_yes(comp['equal'])} (diferencia máxima {_n(comp['max_abs_diff'], 3)}) |")
        for k, v in comp["domains"].items():
            lines.append(f"| {DOMAINS_ES[k]}: filas y estados iguales con y sin la candidata | {_yes(v)} |")
    matched = data.get("comparators_matched")
    if matched:
        lines.append(f"| cada comparador omite sólo su exposición ({_int(matched['checked'])} pares) | "
                     f"{_yes(matched['matched'])} |")
    direct = data.get("direct_check")
    if direct:
        lines.append(f"| recomputación directa = filtro ({_int(direct['candidates'])} candidatos, {direct['units']} "
                     f"unidades) | {_yes(direct['equal'])} ({direct['mismatches']} discrepancias) |")
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    lines = [f"**{v['verdict']}**", "", "| criterio | se cumple |", "|---|---|"]
    for name in data["design"]["criteria"]:
        state = v["checks"].get(name)
        lines.append(f"| {CRITERIA_ES[name]} | {'no evaluado' if state is None else _yes(state)} |")
    r = data.get("recommendation", {})
    lines += ["", f"**Recomendación (propuesta, no decisión): {r.get('recommendation', '—')}.** "
                  f"{r.get('next', r.get('blocker', ''))}"]
    for k, text in r.get("forwarded", {}).items():
        lines.append(f"- {k.replace('_', ' ')}: {text}")
    lines += ["", f"Aprobaciones: {data['approval']}. {data['migration_gate']}."]
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data.get("efficiency")
    if not e:
        return "—"
    return (f"Región de P2J-3 recalculada: {_int(e['p2j3_blood_runs'])} trayectorias de sangre y "
            f"{_int(e['p2j3_counterfactual_runs'])} contrafactuales; {_int(e['no_prbc_runs'])} corridas nuevas de R3 sin "
            f"GR; {_int(e['r3r4_state_runs'])} estados de R3 / R4; {_int(e['comparator_core_runs'])} corridas del núcleo "
            f"para validar los comparadores y {_int(e['p2k3_validation_runs'])} para reproducir la validación de P2K-3. "
            f"{_int(e['candidates_evaluated'])} candidatos evaluados como bitsets ({e['bitset_rules']} reglas por "
            f"{_int(e['upstream_units'])} unidades aguas arriba × {_int(e['latent_combinations'])} combinaciones), sin "
            f"simular ninguno; {_int(e['direct_check_candidates'])} recalculados por la vía directa. Barrido cartesiano: "
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
    parser.add_argument("--data", type=Path, required=True, help="the P2K-4 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
