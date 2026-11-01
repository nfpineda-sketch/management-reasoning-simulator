"""P2L-1 report: the generated blocks of docs/revision/P2L1_AUDITORIA_CONCIENCIA.md.

    python -m clinical_core.consciousness_audit_report --write <document> --data <the P2L-1 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
audit's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes
from .lactate_rebuild_report import CASE_ES

NAMES = ("decisiones", "n", "ecuacion", "caminos", "map_deficit", "oxigenacion", "acido_base", "glucosa",
         "recuperacion", "sondas_n", "autoria", "acidemia", "aguas_arriba", "generalizacion", "veredicto", "estructura",
         "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
CASES = ("gi_bleed_57m", "gi_bleed_72f")
LEVEL_ES = {0: "alerta", 1: "somnoliento", 2: "obnubilado", 3: "sin respuesta"}
CLASS_ES = {"VALID_CAUSAL_PATH": "camino causal válido", "BIOMARKER_PROXY": "proxy de biomarcador",
            "SEMANTIC_LEAK": "fuga semántica", "LEGACY_ARTIFACT": "artefacto heredado",
            "NOT_CURRENTLY_MODELED": "no modelado hoy",
            "BIOMARKER_PROXY_REQUIRES_REFACTOR": "proxy de biomarcador que requiere refactorización"}
PATH_ES = {"pulse": "pulso", "sbp": "PAS", "spo2": "SpO2", "arrival_level": "nivel de autoría de llegada", "N": "N",
           "effective_oxygen_deficit": "déficit efectivo de oxígeno", "D": "D", "map": "PAM", "glucose": "glucosa",
           "ph": "pH", "paco2": "PaCO2", "lactate": "lactato", "hr": "FC", "demand": "demanda"}
CRITERIA_ES = {"n_semantics_explicit": "semántica de N explícita",
               "observable_separated_from_n": "conciencia observable separada de N (N más modificadores explícitos)",
               "causal_modifiers_explicit": "modificadores sistémicos causales explícitos (sin artefactos ni fugas)",
               "lactate_not_proxy": "el lactato no es un proxy", "double_counting_resolved": "doble conteo resuelto",
               "recovery_lag_coherent": "semántica de recuperación coherente",
               "generalization_plausible": "arquitectura generalizable", "upstream_unchanged": "fisiología previa intacta",
               "nothing_approved": "nada aprobado"}
FAMILY_ES = {"hemorrhagic_shock": "shock hemorrágico", "hypoglycaemia": "hipoglucemia",
             "hypercapnia_opioid": "hipercapnia / opioides", "primary_neurologic_injury": "lesión neurológica primaria",
             "severe_hypoxaemia": "hipoxemia grave", "distributive_shock": "shock distributivo"}
UPSTREAM_ES = {"demand": "demanda", "tone_gain": "ganancia de tono g", "map_set": "MAP_set",
               "baroreflex_gain": "ganancia del barorreflejo", "hr_latent_region": "región latente de FC",
               "respiratory_latents": "latentes respiratorios"}
DOUBLE_ES = {"map_and_deficit": "PAM y déficit", "spo2_and_delivery": "SpO2 y aporte", "ph_and_paco2": "pH y PaCO2"}
FROZEN = "(texto congelado, en inglés)"


def _int(value) -> str:
    return f"{value:,}".replace(",", " ")


def _v(value, digits=1):
    return "—" if value is None else _n(value, digits)


def render_decisiones(data: dict) -> str:
    return f"Decisiones de la docencia {FROZEN}:\n\n" + "\n".join(
        f"- **{k}**: {v}" for k, v in data["design"]["faculty"].items())


def render_n(data: dict) -> str:
    n = data["n"]
    r = n["references"]
    return "\n".join([
        f"- **Clasificación:** `{n['classification']}`; semántica declarada {FROZEN}: {n['declared_semantics']}.",
        f"- **Valor de llegada:** {_v(n['arrival_value'])}. **Escrituras:** {', '.join(r['writes'])} (sólo los "
        f"constructores de llegada). **Lecturas** (atributo, subíndice o canal): {len(r['reads'])}. Archivos "
        f"examinados, recursivamente en `clinical_core/`: {r['files_scanned']}. {FROZEN} {n['readers_rule']}.",
        f"- **Bucles genéricos sobre los canales escalares** (finitud, guarda, deltas, carga en sombra): "
        f"{', '.join(r['generic_scalar_loops'])}.",
        f"- **Serialización** {FROZEN}: {n['serialization']}.",
        f"- **Efecto observable:** con N = " + ", ".join(f"{k}: nivel {v}" for k, v in n["observable_effect"].items())
        + "; ningún caso cambia N."])


def render_ecuacion(data: dict) -> str:
    e = data["equation"]
    return "\n".join([f"**Ecuación** {FROZEN}: {e['equation']}", "",
                      f"- La línea del código está presente: {_yes(e['source_line_present'])}; sin pulso, nivel 3: "
                      f"{_yes(e['pulseless_level'])}.",
                      f"- Umbrales de PAS {e['pressure_levels']} y de SpO2 {e['oxygen_levels']}, ambos "
                      f"`{e['provenance']['pressure_levels'][0]}` de `family_engine`."])


def render_caminos(data: dict) -> str:
    p, q = data["paths"], data["perturbations"]
    lines = ["| entrada | clase | la perturbación mueve el nivel | perturbación | por qué (texto congelado) |",
             "|---|---|---|---|---|"]
    for name in [k for k in PATH_ES if k in p]:
        row = p[name]
        moves = "—" if row.get("moves_level") is None else _yes(row["moves_level"])
        if row.get("moves_level_dynamic"):
            moves += "; sí, con la respuesta del tono"
        lines.append(f"| {PATH_ES.get(name, name)} | {CLASS_ES[row['class']]} | {moves} | "
                     f"{q['what'].get(name, '—')} | {row['why']} |")
    t = data["tone_loop"]
    lines += ["", f"**El bucle del tono** (bomba de partida {_v(data['design']['tone_start_pump'], 2)}, nivel de "
                  f"partida {t['start_level']}, tres minutos del integrador por condición):", "",
              "| condición | nivel por minuto | PAS por minuto | déficit por minuto | el nivel mejora con más déficit |",
              "|---|---|---|---|---|"]
    for name, rows in t["rows"].items():
        lines.append(f"| {name} | {' → '.join(str(r['level']) for r in rows)} | "
                     f"{' → '.join(_v(r['sbp']) for r in rows)} | {' → '.join(_v(r['deficit'], 3) for r in rows)} | "
                     f"{_yes(t['level_improves_with_deficit'][name])} |")
    lines += ["", f"Inversión con alguna ganancia primaria: {_yes(t['inverted_at_some_primary_gain'])}. {FROZEN} "
                  f"{t['reading']}."]
    return "\n".join(lines)


def _probe_rows(rows: dict, fields) -> list:
    heads = {"level": "nivel", "sbp": "PAS", "map": "PAM", "spo2": "SpO2", "do2": "DO2", "deficit_fraction": "déficit",
             "ph": "pH", "paco2": "PaCO2", "glucose": "glucosa", "N": "N", "D": "D"}
    lines = ["| sonda | " + " | ".join(heads[f] for f in fields) + " |", "|---|" + "---|" * len(fields)]
    for name, row in rows.items():
        cells = []
        for f in fields:
            value = row.get(f)
            if f == "level":
                cells.append(f"{value} ({LEVEL_ES[value]})")
            else:
                cells.append(_v(value, 3 if f in ("ph", "deficit_fraction", "do2") else 1))
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return lines


def render_map_deficit(data: dict) -> str:
    p = data["deficit_map"]
    return "\n".join(_probe_rows(p["rows"], ("level", "sbp", "map", "do2", "deficit_fraction")) + [
        "", f"Las señales distinguen A de B: {_yes(p['signals_distinguish_a_from_b'])}. Hoy A sale deteriorado: "
            f"{_yes(p['current_a_impaired'])}; B sale alerta: {_yes(p['current_b_alert'])}.",
        "", f"**Superposición** {FROZEN}: {p['overlap']}"])


def render_oxigenacion(data: dict) -> str:
    p = data["oxygenation"]
    return "\n".join(_probe_rows(p["rows"], ("level", "spo2", "do2", "deficit_fraction")) + [
        "", f"SpO2 a la que empieza el déficit sistémico (gasto y Hb normales): {_v(p['deficit_onset_spo2'])} %; techo "
            f"de la escalera de SpO2: {_v(p['ladder_top'])} %. Doble conteo en el rango de la escalera: "
            f"{_yes(p['double_count_in_ladder_range'])}. El déficit sistémico no ve la hipoxemia: "
            f"{_yes(p['deficit_misses_hypoxaemia'])}.",
        "", f"{FROZEN} {p['spo2_in_delivery']}. {p['reading']}"])


def render_acido_base(data: dict) -> str:
    p = data["acid_base"]
    c = p["compensated_at_arrival"]
    return "\n".join(_probe_rows(p["rows"], ("level", "ph", "paco2")) + [
        "", f"Distingue acidemia metabólica de hipercapnia: {_yes(p['distinguishes'])}. Hipercapnia compensada de "
            f"autoría a la llegada (HCO3 {_v(c['hco3'])}, PaCO2 {_v(c['paco2'])}): pH {_v(c['ph'], 3)}, nivel "
            f"{c['level']}; representable: {_yes(p['compensated_at_arrival_representable'])}. Compensación renal "
            f"durante el encuentro: {_yes(p['renal_compensation_during_encounter'])}.", "", f"{FROZEN} {p['reading']}"])


def render_glucosa(data: dict) -> str:
    p = data["glucose"]
    return "\n".join(_probe_rows(p["rows"], ("level", "glucose", "deficit_fraction")) + [
        "", f"El nivel no cambia: {_yes(p['level_unchanged'])}. {FROZEN} Estado: {p['state']}; escritores: "
            f"{', '.join(p['writers'])} ({p['writers_rule']}); lector: {p['reader']}."])


def render_recuperacion(data: dict) -> str:
    r = data["recovery_lag"]
    lines = [f"- Nivel durante la agresión (gasto 0,3): {r['insult_level']}; con la fisiología restablecida (D 600): "
             f"{r['restored_level']}; el retraso queda representado: {_yes(r['lag_represented'])}. {FROZEN} "
             f"{r['instantaneous']}.",
             f"- Expectativa {FROZEN}: {r['expectation']}.", "",
             "| agresión (un minuto del integrador) | D tras un minuto | D cubre la agresión |", "|---|---|---|"]
    for k, v in r["d_after_one_minute"].items():
        lines.append(f"| {k} | {_v(v, 2)} | {_yes(r['d_covers_insult'][k]) if k in r['d_covers_insult'] else '—'} |")
    lines += ["", f"- D basta: {_yes(r['d_sufficient'])}. Hace falta una memoria nueva: {_yes(r['new_state_required'])} "
                  f"(`{r['verdict']}`). Opciones {FROZEN}: " + "; ".join(r["options"]) + ".",
              f"- {FROZEN} {r['why_not_d']}", "", "| memoria existente | qué es (texto congelado) |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in r["memories"].items()]
    return "\n".join(lines)


def render_sondas_n(data: dict) -> str:
    p = data["neuro_probes"]
    lines = ["| sonda | qué se aísla | lo esperado | nivel hoy | lo representa la derivación actual | existe la señal | "
             "hueco |", "|---|---|---|---|---|---|---|"]
    for name, row in p["rows"].items():
        lines.append(f"| {name} | {row['isolated']} | {row['expected']} | {row['level']} ({LEVEL_ES[row['level']]}) | "
                     f"{_yes(row['current_derivation_represents'])} | {_yes(row['signal_exists_in_core'])} | "
                     f"{row['gap']} |")
    return "\n".join(lines)


def render_autoria(data: dict) -> str:
    lines = ["| caso | elemento | valor | fuente | clase |", "|---|---|---|---|---|"]
    for case in CASES:
        a = data["authored"][case]
        for key, row in a.items():
            if isinstance(row, dict) and "value" in row:
                lines.append(f"| {CASE_ES[case]} | {key} | {row['value']} | {row.get('source', '—')} | {row['class']} |")
        lines.append(f"| {CASE_ES[case]} | ausentes | " + "; ".join(f"{k}: {v}" for k, v in a["absent"].items())
                     + " | — | — |")
    return "\n".join(lines)


def render_acidemia(data: dict) -> str:
    x = data["extreme_acidemia"]
    low = x["lowest"]
    lines = [f"- Filas con pH < 7,00 sin tratamiento (57m, demanda 1,1): {_int(x['flagged'])} de "
             f"{_int(x['survivors'])}; pH mínimo {_v(low['ph'], 3)} en el minuto {low['minute']} (carga "
             f"{_v(low['burden'], 2)}, déficit {_v(low['deficit'], 3)}, PaCO2 {_v(low['paco2'], 1)}); marca "
             f"`{x['classification']}`.",
             "", "| tono, demanda | PAS a 120 (mín – mediana – máx) | PAM a 120 | minutos bajo 80 | minutos bajo 65 |",
             "|---|---|---|---|---|"]
    for key, p in x["untreated_pressure_57m_d1.1"].items():
        s, m = p["sbp120"], p["map120"]
        lines.append(f"| {key} | {_v(s['low'])} – {_v(s['median'])} – {_v(s['high'])} | {_v(m['low'])} – "
                     f"{_v(m['high'])} | {p['minutes_below_80']['low']}–{p['minutes_below_80']['high']} | "
                     f"{p['minutes_below_65']['low']}–{p['minutes_below_65']['high']} |")
    lines += ["", "Unidades: " + "; ".join(f"tono {k}: P2K-5 {_int(v['p2k5'])}, P2J-3 {_int(v['p2j3'])}"
                                         for k, v in x["units"].items())
              + f" (coinciden: {_yes(x['units_match'])}; {FROZEN} {x['unit']})."]
    lines += ["", f"Nivel actual a los 120 min: {x['current_level_at_120']} ({LEVEL_ES[x['current_level_at_120']]}), "
                  f"PAS máxima {_v(x['highest_untreated_sbp120'])}. Alerta plena plausible: "
                  f"{_yes(x['fully_alert_plausible'])}; filtradas: {_yes(x['filtered'])}.", "", f"{FROZEN} {x['reading']}"]
    return "\n".join(lines)


def render_aguas_arriba(data: dict) -> str:
    u = data["upstream"]
    lines = ["| incertidumbre | llega hoy a la conciencia | llegaría con los modificadores candidatos | por qué "
             "(texto congelado) |", "|---|---|---|---|"]
    for k, row in u["table"].items():
        lines.append(f"| {UPSTREAM_ES[k]} | {row['current']} | {row['candidate']} | {row['why']} |")
    lines += ["", "Evidencia por perturbación: " + ", ".join(f"{k} {_yes(v)}" for k, v in u["evidence"].items()) + "."]
    return "\n".join(lines)


def render_generalizacion(data: dict) -> str:
    g = data["generalization"]
    lines = ["| familia | lo que existe | lo que falta | recuperación |", "|---|---|---|---|"]
    for k, row in g["families"].items():
        lines.append(f"| {FAMILY_ES[k]} | {row['present']} | {row['missing']} | {row['lag']} |")
    lines += ["", f"**Resultado:** `{g['result']}`. {FROZEN} {g['reading']}"]
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    v, r = data["verdict"], data["recommendation"]
    lines = [f"**Veredicto:** `{v['verdict']}`.", "", "| criterio | cumple |", "|---|---|"]
    for name in data["design"]["criteria"]:
        lines.append(f"| {CRITERIA_ES[name]} | {_yes(v['checks'].get(name))} |")
    lines += ["", f"Criterios que fallan: {', '.join(v['failing']) or 'ninguno'}.", "",
              "| doble conteo | estado | hallazgo (texto congelado) |", "|---|---|---|"]
    for k, row in data["double_counting"].items():
        lines.append(f"| {DOUBLE_ES[k]} | `{row['status']}` | {row['finding']} |")
    lines += ["", f"**Recomendación:** `{r['recommendation']}`."]
    return "\n".join(lines)


def render_estructura(data: dict) -> str:
    r = data["recommendation"]
    lines = [f"**La estructura mínima que falta** {FROZEN}, descrita y no implementada:", ""]
    lines += [f"- **{k}**: {v}" for k, v in r.get("smallest_structure", {}).items()]
    lines += ["", "**Decisiones que se piden a la docencia** (texto congelado):", ""]
    lines += [f"{i}. {d}" for i, d in enumerate(r.get("decisions", []), 1)]
    surface = data["design"]["decision_surface"]
    lines += ["", "**Superficie de decisión (sólo estructural):** " + "; ".join(
        f"{k}: {' / '.join(v)}" for k, v in surface["options"].items()) + f". Numérica: {surface['numeric']}."]
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return "\n".join([f"- Lecturas de estados fijos sintéticos por el núcleo certificado: {e['fixed_state_readings']}; "
                      f"pasos del integrador (bucle del tono y un minuto de D): {e['integrator_steps']}; simulaciones "
                      f"de trayectorias: {e['trajectory_simulations']}; región reconstruida: "
                      f"{_yes(e['region_rebuilt'])}; barrido "
                      f"cartesiano: {_yes(e['cartesian_sweep'])}; motor heredado leído como código: "
                      f"{_yes(e['legacy_read'])} (sólo citado como texto).",
                      f"- Registros comprometidos leídos con su hash fijado: {', '.join(e['records_read'])}."])


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the P2L-1 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
