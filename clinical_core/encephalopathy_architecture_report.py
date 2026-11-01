"""P2L-2 report: the generated blocks of docs/revision/P2L2_ARQUITECTURA_ENCEFALOPATIA.md.

    python -m clinical_core.encephalopathy_architecture_report --write <document> --data <the P2L-2 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("decisiones", "n", "senales", "composicion", "sondas_n", "robustez", "fisiologia", "ortogonalidad", "legado",
         "tono", "acidemia", "generalizacion", "identificabilidad", "aguas_arriba", "veredicto", "recomendacion",
         "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FROZEN = "(texto congelado, en inglés)"
SIGNAL_ES = {"cerebral_hypoperfusion": "hipoperfusión cerebral", "oxygen_deficit": "déficit de aporte de oxígeno",
             "hypoxaemia": "hipoxemia", "acidemia": "acidemia", "hypercapnia": "hipercapnia",
             "hypoglycaemia": "hipoglucemia"}
READING_ES = {"map": "PAM", "deficit_fraction": "déficit efectivo / demanda", "spo2": "SpO2", "ph": "pH",
              "paco2": "PaCO2", "glucose": "glucosa"}
SIDE_ES = {"low": "por debajo", "high": "por encima"}
SUPPORT_ES = {"POSITIVE_UNDER_SOME_ADMISSIBLE_MAPPING": "puede ser positiva",
              "ZERO_UNDER_EVERY_ADMISSIBLE_MAPPING": "0 con todo mapeo admisible", "UNAVAILABLE": "no disponible",
              "MAXIMAL_ARREST": "máxima (paro)"}
CRITERIA_ES = {"n_reserved_for_primary": "N reservado al estado neurológico primario",
               "systemic_acute_separate": "alteración sistémica aguda separada de N",
               "memory_gives_recovery_lag": "la memoria sistémica da el retraso de recuperación",
               "signals_causally_explicit": "señales causalmente explícitas (cableado, aislamiento, ortogonalidad)",
               "maximum_aggregation": "agregación por máximo, sin suma",
               "lactate_not_controller": "el lactato no controla la conciencia",
               "legacy_retired_from_candidate": "escaleras PAS/SpO2 y piso de llegada retirados del candidato",
               "primary_n_independent": "N primario afecta la conciencia por sí solo",
               "generalization_passes": "generalización plausible", "upstream_unchanged": "fisiología previa intacta",
               "nothing_approved": "nada aprobado"}
FAMILY_ES = {"A_hemorrhagic_shock": "A. Shock hemorrágico", "B_severe_hypoglycaemia": "B. Hipoglucemia grave",
             "C_hypercapnic_opioid_physiology": "C. Fisiología hipercápnica / opioides",
             "D_primary_stroke": "D. Ictus / lesión neurológica primaria", "E_severe_hypoxaemia": "E. Hipoxemia grave",
             "F_distributive_shock": "F. Shock distributivo"}
PROBE_ES = {"reference": "Referencia (llegada neutra)", "A_low_map_no_deficit": "A. PAM baja, sin déficit",
            "B_normal_map_high_deficit": "B. PAM normal, déficit alto", "C_low_map_and_deficit": "C. Ambos",
            "E_low_spo2_adequate_delivery": "E. SpO2 baja, aporte adecuado",
            "E2_fio2_falls_to_room_air": "E2. FiO2 1 → aire ambiente",
            "F_normal_spo2_critical_deficit": "F. SpO2 normal, déficit crítico",
            "G_low_ph_normal_paco2": "G. pH bajo, PaCO2 normal/baja",
            "H_high_paco2_near_normal_ph": "H. PaCO2 alta, pH casi normal",
            "acute_hypercapnia": "Hipercapnia aguda (no compensada)", "hypoglycaemia": "Hipoglucemia",
            "shock_and_acidemia": "Shock con acidemia", "primary_n_only": "Sólo N primario (0,5)",
            "arrival_label_obtunded": "Etiqueta de llegada «obnubilado», fisiología normal"}


def _signals(names) -> str:
    return ", ".join(SIGNAL_ES[n] for n in names) or "ninguna"


def render_decisiones(data: dict) -> str:
    return f"Decisiones de la docencia {FROZEN}:\n\n" + "\n".join(
        f"- **{k}**: {v}" for k, v in data["design"]["faculty"].items())


def render_n(data: dict) -> str:
    n = data["n"]
    return "\n".join([
        f"- **Escritores:** {', '.join(n['writers'])} (sólo el constructor de llegada, N = 0).",
        f"- **Lectores:** {', '.join(n['readers'])}: el único lector, `primary_from_state`, que lo lee como "
        "alteración neurológica primaria; ninguna señal sistémica lo lee ni lo escribe.",
        f"- **Archivos revisados:** {n['files_scanned']} (búsqueda recursiva congelada de P2L-1).",
        f"- **Semántica** {FROZEN}: {n['semantics']}",
        f"- **Escala:** {n['scale']}", f"- **Dinámica:** {n['dynamics']}", f"- **Valores GI:** {n['gi_values']}",
        f"- **Redacción cerrada:** {n['closed_wording']}"])


def render_senales(data: dict) -> str:
    rows = ["| Señal | Lectura certificada | Altera | Significado (congelado) |", "|---|---|---|---|"]
    for name, (reading, side, meaning) in data["design"]["signals"].items():
        rows.append(f"| {SIGNAL_ES[name]} | {READING_ES[reading]} | {SIDE_ES[side]} de su cota normal | {meaning} |")
    status = data["design"]["physiology_status"]
    return "\n".join(rows) + "\n\n" + "\n".join(
        f"- **{k}** {FROZEN}: {v}" for k, v in status.items() if k in ("signals", "ramp_shape", "availability"))


def render_composicion(data: dict) -> str:
    status = data["design"]["physiology_status"]
    proof = data["memory_proof"]
    return "\n".join([
        "```",
        "alteración neurológica primaria      = N                      (escala común [0, 1])",
        "estrés cerebral sistémico agudo  S   = máx(señales agudas)    (nunca suma)",
        "carga de encefalopatía sistémica F   → S: tau_subida si S > F; tau_aclaramiento (> tau_subida) si no",
        "alteración observable            I   = máx(N, S, F)           (nunca suma)",
        "```", "",
        f"- **Agregación** {FROZEN}: {status['aggregation']}", f"- **Memoria** {FROZEN}: {status['memory']}",
        f"- **Llegada** {FROZEN}: {status['arrival']}", f"- **Categoría observada** {FROZEN}: {status['category']}",
        "", f"Propiedades de la memoria, demostradas desde su ecuación {FROZEN}:", ""] + [
        f"- **{k}**: {v}" for k, v in proof.items()])


def render_sondas_n(data: dict) -> str:
    rows, d = data["neuro_probes"]["rows"], data["design"]["neuro_probes"]
    out = ["| Sonda | Qué aísla (congelado) | Resultado | Pasa |", "|---|---|---|---|"]
    detail = {
        "N1": lambda r: f"I máx {_n(r['max_impairment'], 2)}; F máx {_n(r['max_burden'], 2)}",
        "N2": lambda r: f"I {_n(r['impairment'], 2)}; S {_n(r['stress'], 2)}; F máx {_n(r['max_burden'], 2)}",
        "N9": lambda r: f"S {_n(r['stress'], 2)} = máximo; la suma daría {_n(r['sum_would_be'], 2)}",
        "N10": lambda r: f"al restaurar: S {_n(r['stress_at_restoration'], 2)}, F = I {_n(r['burden_at_restoration'], 3)}; "
                         f"cae monótona; área {_n(r['memory_area'], 2)}; bajo {_n(0.05, 2)} en "
                         f"{_n(r['time_to_residual'], 2)} u",
        "N11": lambda r: "F al restaurar: breve " + _n(r["brief"]["burden_at_restoration"], 3) + ", repetida "
                         + _n(r["repeated"]["burden_at_restoration"], 3) + ", prolongada "
                         + _n(r["prolonged"]["burden_at_restoration"], 3) + "; área " + _n(r["brief"]["memory_area"], 2)
                         + " / " + _n(r["repeated"]["memory_area"], 2) + " / " + _n(r["prolonged"]["memory_area"], 2)
                         + "; tiempo bajo 0,05: " + _n(r["brief"]["time_to_residual"], 2) + " / "
                         + _n(r["repeated"]["time_to_residual"], 2) + " / " + _n(r["prolonged"]["time_to_residual"], 2)
                         + " u",
        "N12": lambda r: f"I durante {_n(r['impairment_during'], 2)}; después nunca bajo N "
                         f"({_n(r['primary_throughout'], 2)}); F igual con o sin N: {_yes(r['burden_independent_of_n'])}"}
    for name in sorted(rows, key=lambda k: int(k[1:])):
        row = rows[name]
        text = detail[name](row) if name in detail else (
            f"{SIGNAL_ES[row['signal']]}: S = I {_n(row['stress'], 2)}; F al final {_n(row['burden_end'], 3)}; "
            f"N {_n(row['primary'], 2)}")
        out.append(f"| {name} | {d[name]} | {text} | {_yes(row['passes'])} |")
    return "\n".join(out) + "\n\nUnidades sintéticas (u), memoria sintética de sonda (tau_subida 1, tau_aclaramiento 4): " \
                            "SYNTHETIC_PROBE_ONLY, nunca minutos."


def render_robustez(data: dict) -> str:
    r = data["ratio_robustness"]
    rows = ["| tau_aclaramiento / tau_subida | Sondas que pasan |", "|---|---|"]
    for ratio, probes in r["by_ratio"].items():
        rows.append(f"| {ratio} | {sum(probes.values())} de {len(probes)} |")
    return "\n".join(rows) + f"\n\nTodas pasan en cada razón: {_yes(r['all_pass'])}."


def render_fisiologia(data: dict) -> str:
    out = [f"Regla {FROZEN}: {data['design']['physiology_rule']}", ""]
    for gain, rows in data["physiology"].items():
        out += [f"Ganancia de ventilación {gain.replace('.', ',')}:", "",
                "| Sonda | PAM | Déficit/demanda | SpO2 | pH | PaCO2 | Glucosa | Señales que pueden ser positivas | "
                "Cableado | Aislada |", "|---|---|---|---|---|---|---|---|---|---|"]
        for name in sorted(rows, key=list(PROBE_ES).index):
            row, r = rows[name], rows[name]["reading"]
            out.append(f"| {PROBE_ES[name]} | {_n(r['map'])} | {_n(r['deficit_fraction'], 3)} | {_n(r['spo2'])} | "
                       f"{_n(r['ph'], 3)} | {_n(r['paco2'])} | {_n(r['glucose'], 0)} | {_signals(row['positive'])} | "
                       f"{_yes(row['wired'])} | {_yes(row['isolated_as_declared'])} |")
        out.append("")
    return "\n".join(out) + "Con el perfil comprometido, cada señal de cada sonda queda UNMAPPED: ninguna lectura " \
                            "numérica de conciencia sale del núcleo real."


def render_ortogonalidad(data: dict) -> str:
    names = {"map_deficit": "PAM / déficit (A, B, C, D)", "spo2_delivery": "SpO2 / aporte (E, F)",
             "ph_paco2": "pH / PaCO2 (G, H)"}
    rows = ["| Grupo | Patrones de señales (ganancia 0,04) | Distinguibles | Aisladas |", "|---|---|---|---|"]
    for group, o in data["orthogonality"].items():
        patterns = "; ".join(_signals(p) for p in o["positive_by_gain"]["0.04"])
        rows.append(f"| {names[group]} | {patterns} | {_yes(o['distinguishable'])} | {_yes(o['isolated_as_declared'])} |")
    return "\n".join(rows)


def render_legado(data: dict) -> str:
    names = {"arrival_floor": "piso de llegada", "sbp_ladder": "escalera de PAS", "spo2_ladder": "escalera de SpO2",
             "lactate": "lactato", "d": "D", "hr": "FC", "arrival_label": "etiqueta de autoría de llegada",
             "derived_wording": "redacción de derived.PARAMETERS"}
    return f"Estado {FROZEN}:\n\n" + "\n".join(f"- **{names[k]}**: {v}" for k, v in data["legacy"].items())


def render_tono(data: dict) -> str:
    t = data["tone_loop"]
    rows = ["| Fila de P2L-1 | Déficit no decreciente | Presión no decreciente | El nivel heredado bajó |",
            "|---|---|---|---|"]
    for name, row in t["rows"].items():
        rows.append(f"| {name} | {_yes(row['deficit_non_decreasing'])} | {_yes(row['pressure_non_decreasing'])} | "
                    f"{_yes(row['legacy_level_fell'])} |")
    return "\n".join(rows) + (f"\n\nInversión heredada en {', '.join(t['legacy_inverted'])}. En el candidato el déficit "
                              f"entra con su propia señal, monótona: inversión eliminada: "
                              f"{_yes(t['candidate_inversion_removed'])}.")


def render_acidemia(data: dict) -> str:
    x = data["extreme_acidemia"]
    low = x["lowest"]
    lines = [f"- **Filas:** {x['flagged']:,}".replace(",", " ") + f" de {x['survivors']:,}".replace(",", " ")
             + f" ({x['unit']}; 57m: {x['by_case']['gi_bleed_57m']}, 72f: {x['by_case']['gi_bleed_72f']}).",
             f"- **pH:** de {_n(x['ph_range'][0], 3)} a menos de {_n(x['ph_range'][1], 2)}; la fila más baja en el "
             f"minuto {low['minute']}, déficit {_n(low['deficit'], 3)}, PaCO2 {_n(low['paco2'])}.",
             f"- **PAM sin tratar en el minuto 120:** {_n(x['map120_range'][0])}–{_n(x['map120_range'][1])} mmHg.",
             f"- **Gases de llegada de autoría:** {x['arrival_abg']}.", ""]
    lines += [f"- **{SIGNAL_ES[k]}** {FROZEN}: {v}" for k, v in x["signals"].items()]
    lines += ["", f"- **Agregación** {FROZEN}: {x['aggregation']}", f"- **Lectura** {FROZEN}: {x['reading']}",
              f"- **Clasificación:** {x['classification']}; filtradas: {_yes(x['filtered'])}."]
    return "\n".join(lines)


def render_generalizacion(data: dict) -> str:
    g = data["generalization"]
    rows = ["| Familia | Señales (sintéticas) | N | I durante | I al restaurar | Retraso | Portador físico | "
            "Representada |", "|---|---|---|---|---|---|---|---|"]
    for name, row in g["rows"].items():
        signals = ", ".join(f"{SIGNAL_ES[k]} {_n(v, 1)}" for k, v in row["signals"].items()) or "—"
        carrier = PROBE_ES.get(row["physiological_carrier"], "—")
        rows.append(f"| {FAMILY_ES[name]} | {signals} | {_n(row['primary'], 1)} | {_n(row['impairment_during'], 2)} | "
                    f"{_n(row['impairment_after_restoration'], 3)} | {_yes(row['lag'])} | {carrier} | "
                    f"{_yes(row['represented'])} |")
    return "\n".join(rows) + f"\n\n**Resultado:** {g['result']}. {FROZEN}: {g['reading']}\n\n" + "\n".join(
        f"- **{FAMILY_ES[k]}**, escritor que la familia aporta {FROZEN}: {v['writer']}" for k, v in g["rows"].items())


def render_identificabilidad(data: dict) -> str:
    return "\n".join([f"- **{k}** {FROZEN}: {v}" for k, v in data["identifiability"].items()] + [
        "", f"- **Trayectorias GI C1–C4** {FROZEN}: {data['trajectories']}",
        f"- **Depresión farmacológica del SNC** {FROZEN}: {data['pharmacologic']}"])


def render_aguas_arriba(data: dict) -> str:
    up = data["upstream"]
    return "\n".join([
        f"- **Árbol de P2L-1:** {up['files']} archivos, huella `{up['digest']}`; idéntico byte a byte: "
        f"{_yes(up['unchanged'])} (fuera de los módulos de P2L-2 y de las tuplas declaradas).",
        f"- **Quién importa la fisiología candidata:** {', '.join(up['imported_by'])} (ningún módulo del núcleo).",
        "- Por construcción no cambian BloodState, gasto, presión/tono, DO2/déficit, D, lactato, FC/barorreflejo, "
        "ácido-base ni FR/W/PaCO2: ningún paso del núcleo lee el candidato y el candidato no escribe estado."])


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    rows = ["| Criterio | Cumple |", "|---|---|"]
    rows += [f"| {CRITERIA_ES[k]} | {_yes(val)} |" for k, val in v["checks"].items()]
    return "\n".join(rows) + f"\n\n**Veredicto:** `{v['verdict']}`" + (
        f"; fallan: {', '.join(v['failing'])}." if v["failing"] else ".")


def render_recomendacion(data: dict) -> str:
    r = data["recommendation"]
    lines = [f"- **¿Hace falta más calibración numérica de conciencia antes de probar la generalización?** "
             f"{_yes(r.get('numeric_calibration_required_before_generalization'))}.",
             f"- **Estrategia:** `{r.get('strategy', '—')}`.", f"- **Recomendación:** `{r['recommendation']}`.",
             f"- **Por qué** {FROZEN}: {r.get('why', '—')}", f"- **Regla** {FROZEN}: {r['rule']}", "",
             f"Decisiones pedidas a la docencia {FROZEN}:", ""]
    return "\n".join(lines + [f"{i}. {d}" for i, d in enumerate(r["decisions"], 1)])


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return "\n".join([
        f"- Lecturas de estado fijo por el núcleo certificado: {e['fixed_state_readings']}.",
        f"- Pasos de la memoria sintética: {e['synthetic_memory_steps']} en {e['synthetic_courses']} cursos "
        "(aritmética exacta, sin integrador del núcleo).",
        f"- Pasos del integrador del núcleo: {e['integrator_steps']}; trayectorias simuladas: "
        f"{e['trajectory_simulations']}; trayectorias GI: {e['gi_trajectories']}.",
        f"- Registros reutilizados: {', '.join(e['records_read'])} (con huella fijada).",
        f"- Barrido cartesiano: {_yes(e['cartesian_sweep'])}; región reconstruida: {_yes(e['region_rebuilt'])}; "
        f"motor heredado leído: {_yes(e['legacy_read'])}."])


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the P2L-2 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
