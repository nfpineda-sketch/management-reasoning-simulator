"""P2M-1 report: the generated blocks of docs/revision/P2M1_AUDITORIA_COLAPSO.md.

    python -m clinical_core.collapse_audit_report --write <document> --data <the P2M-1 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
audit's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("decisiones", "pulso", "mecanismos", "flujo_cero", "sondas", "redundancia", "persistencia", "orden", "rosc",
         "subconjunto", "generalizacion", "disparadores", "minimo", "veredicto", "pedidas", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FROZEN = "(texto congelado, en inglés)"
INPUT_ES = {"output": "gasto (regla P2E-3 actual)", "perfusion_pressure": "presión de perfusión (PAM)",
            "oxygen_delivery": "aporte de O2 (déficit)", "arterial_oxygenation": "oxigenación arterial (SpO2)"}
MECH_ES = {"CIRCULATORY_COLLAPSE_RISK": "riesgo de colapso circulatorio",
           "METABOLIC_NONVIABILITY_RISK": "riesgo de no viabilidad metabólica", "ARREST": "paro (sin pulso)",
           "NONE": "ninguno"}
CRITERIA_ES = {"pulse_semantics_explicit": "semántica del pulso explícita",
               "collapse_vs_arrest_separated": "colapso y paro separados",
               "causal_inputs_explicit": "entradas causales explícitas", "redundancy_resolved": "redundancia resuelta",
               "persistence_classified": "persistencia clasificada", "event_order_safe": "orden de eventos seguro",
               "generalization_plausible": "generalización plausible", "no_gi_threshold": "sin umbral GI",
               "upstream_unchanged": "fisiología previa intacta"}
FAMILY_ES = {"hemorrhagic": "Shock hemorrágico", "cardiogenic": "Shock cardiogénico",
             "obstructive_pe": "Shock obstructivo / TEP", "distributive_sepsis": "Shock distributivo / sepsis",
             "anaphylaxis": "Anafilaxia", "malignant_arrhythmia": "Arritmia maligna",
             "hypoxaemia_respiratory_failure": "Hipoxemia grave / insuficiencia respiratoria"}
EVIDENCE_ES = {"flow_never_alone": "el flujo bajo nunca falla solo (siempre lo acompaña presión o aporte)",
               "pressure_needed": "hay un estado donde sólo falla la presión (vasoplejía)",
               "delivery_needed": "hay un estado donde falla el aporte con la presión conservada",
               "arterial_distinct": "hay un estado donde falla la oxigenación arterial sin déficit",
               "pump_and_rhythm_through_flow": "bomba y ritmo llegan a las entradas sólo por el flujo",
               "pulseless_rhythm_is_arrest": "un ritmo sin pulso es paro, no colapso",
               "acid_reaches_no_input": "la acidemia no llega a ninguna entrada"}


def _int(value) -> str:
    return f"{value:,}".replace(",", " ")


def render_decisiones(data: dict) -> str:
    return f"Decisiones de la docencia {FROZEN}:\n\n" + "\n".join(
        f"- **{k}**: {v}" for k, v in data["design"]["faculty"].items())


def render_pulso(data: dict) -> str:
    s, sem = data["pulse"], data["design"]["pulse_semantics"]
    return "\n".join(
        [f"- **{k}** {FROZEN}: {v}" for k, v in sem.items()] + [
            "", f"Búsqueda por AST en {s['files_scanned']} archivos del núcleo (sin los de análisis ni los informes):", "",
            f"- **Transiciones de ritmo** ({len(s['transitions'])}): {', '.join(s['transitions'])}.",
            f"- **Escrituras de R por palabra clave** ({len(s['r_keyword_writes'])}): {', '.join(s['r_keyword_writes'])}.",
            f"- **Escrituras de terminal_since** ({len(s['terminal_since_writes'])}): "
            f"{', '.join(s['terminal_since_writes'])}.",
            f"- **Lecturas de pulse_present:** {len(s['pulse_reads'])}; de terminal_since: "
            f"{len(s['terminal_since_reads'])}.",
            f"- **Constructores de ritmo:** {len(s['rhythm_constructors'])}; guardas que detienen la corrida "
            f"(UnresolvedBoundary): {', '.join(s['unresolved_boundaries'])}."])


def render_mecanismos(data: dict) -> str:
    rows = ["| Mecanismo | Dónde | Condición (congelada) | Clase | Activo por defecto |", "|---|---|---|---|---|"]
    for name, (where, condition, cls, active) in data["design"]["mechanisms"].items():
        rows.append(f"| {name} | `{where}` | {condition} | {cls} | {_yes(active)} |")
    quoted = data["legacy_quoted"]
    return "\n".join(rows) + "\n\nLos mecanismos heredados se citan como texto (nunca se importan ni se ajustan): " + \
        ", ".join(f"`{k}` {_yes(v)}" for k, v in quoted.items()) + "."


def _r(row: dict, key: str, digits: int = 2) -> str:
    return _n(row.get(key), digits)


def render_flujo_cero(data: dict) -> str:
    z = data["zero_flow"]
    p, near, one = z["pulseless"], z["pulse_with_near_zero_flow"], z["one_minute"]
    lines = [
        f"- **Sin pulso (FV):** gasto {_r(p, 'output_rel')}, presión {_r(p, 'pressure_rel')}, aporte "
        f"{_r(p, 'delivery_rel')}; PAM, PAS y SpO2 no medibles; nivel heredado {p['legacy_level']}.",
        f"- **Un minuto sin pulso:** D {_n(one['D'][0], 2)} → {_n(one['D'][1], 2)}; carga ácida "
        f"{_n(one['acid_burden'][0], 3)} → {_n(one['acid_burden'][1], 3)}; lactato en exceso {_n(one['lactate_excess'][0], 2)}"
        f" → {_n(one['lactate_excess'][1], 2)} (sigue a D con un minuto de retraso); carga de colapso "
        f"{_n(one['collapse_burden'][0], 2)} → {_n(one['collapse_burden'][1], 2)}; T y P latentes sin cambio; "
        f"terminal_since {one['terminal_since'][1]}.",
        "- **Ritmos imposibles:** " + ", ".join(f"{k}: {v}" for k, v in z["impossible_rhythms"].items()) + ".",
        f"- **Pulso con gasto en el cero numérico:** {z['pulse_with_zero_output']}; carga ácida 30 (HCO3 ≤ 0): "
        f"{z['acid_burden_30']}.",
        f"- **Pulso con gasto 0,02:** representable: PAM {_r(near, 'map', 1)} mmHg, PAS {_r(near, 'sbp', 1)} mmHg, "
        f"déficit {_r(near, 'deficit_fraction', 3)}, nivel heredado {near['legacy_level']}.",
        "", f"Lectura {FROZEN}: {z['reading']}"]
    return "\n".join(lines)


def render_sondas(data: dict) -> str:
    pr = data["probes"]
    out = [f"Regla {FROZEN}: {pr['rule']}", "",
           "| Sonda | Qué fija | Pulso | Gasto | PAM | Aporte rel. | Déficit / demanda | SpO2 | pH | Entradas que pueden "
           "fallar | Mecanismo |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, row in pr["rows"].items():
        r = row["reading"]
        inputs = ", ".join(INPUT_ES[k] for k in row["positive"]) or "ninguna"
        out.append(f"| {name} | {row['what']} | {_yes(r['pulse'])} | {_r(r, 'output_rel', 3)} | {_r(r, 'map', 1)} | "
                   f"{_r(r, 'delivery_rel', 3)} | {_r(r, 'deficit_fraction', 3)} | {_r(r, 'spo2', 1)} | {_r(r, 'ph', 3)} | "
                   f"{inputs} | {MECH_ES[row['mechanism']]} |")
    g = pr["groups"]
    out += ["", f"- **Flujo / PAM (A, B, C, D) distinguibles:** {_yes(g['flow_map']['distinguishable'])}; la regla "
                f"actual (sólo gasto) no ve: {', '.join(g['flow_map']['current_rule_blind']) or 'nada'}.",
            f"- **Aporte de O2 (A, B, C, D) distinguibles:** {_yes(g['oxygen']['distinguishable'])}; la regla actual no "
            f"ve: {', '.join(g['oxygen']['current_rule_blind'])}.",
            f"- **Bomba / ritmo:** un ritmo con pulso y gasto 0,5 lee igual que una bomba en 0,5: "
            f"{_yes(g['pump_rhythm']['rhythm_equals_pump_at_equal_output'])}; la falla de bomba y la combinada comparten "
            f"entradas: {_yes(g['pump_rhythm']['pump_and_rhythm_failures_share_inputs'])}; un ritmo sin pulso es paro: "
            f"{_yes(g['pump_rhythm']['pulseless_rhythm_is_arrest'])}."]
    return "\n".join(out)


def render_redundancia(data: dict) -> str:
    rows = [f"- **{k}** {FROZEN}: {v}" for k, v in data["redundancy"].items()]
    ev = [f"- {EVIDENCE_ES[k]}: {_yes(v)}" for k, v in data["redundancy_evidence"].items()]
    return "\n".join(rows + ["", "Comprobado sobre las sondas elegidas (no sobre todo el espacio de estados: ver la nota "
                              "que sigue):", ""] + ev)


def render_persistencia(data: dict) -> str:
    p = data["persistence"]
    v = p["values"]
    lines = [
        f"Con los valores sintéticos comprometidos de P2E-3 (umbral {_n(v['threshold'], 1)}, límite {_n(v['limit'], 0)}, "
        f"τ de repago {_n(v['repayment_tau_min'], 0)} min), por la función del núcleo:", "",
        f"- **Un minuto crítico aislado** (gasto casi 0): carga {_n(p['one_transient_minute']['burden'], 2)}; paro: "
        f"{_yes(p['one_transient_minute']['arrest'])}.",
        f"- **Gasto 0,1 sostenido:** {_n(p['sustained_output_0_1']['per_minute'], 2)} por minuto; se cumple el criterio "
        f"en el minuto {p['sustained_output_0_1']['criterion_minute']}.",
        f"- **8 min críticos y luego restaurado:** carga {_n(p['restored_after_8_min']['burden_at_8'], 2)}; a los 60 min "
        f"sin repago {_n(p['restored_after_8_min']['held_after_60'], 2)}, con repago "
        f"{_n(p['restored_after_8_min']['repaid_after_60'], 2)}.",
        f"- **Un minuto crítico cada 10 durante 4 h:** sin repago se cumple el criterio en el minuto "
        f"{p['intermittent_1_in_10_for_4h']['held_criterion_minute']}; con repago la carga no pasa de "
        f"{_n(p['intermittent_1_in_10_for_4h']['repaid_max'], 2)} y nunca se cumple.",
        f"- **Límite 0,5 (el perfil lo acepta: {_yes(p['single_minute_limit_0_5']['profile_accepts_it'])}):** paro en "
        f"el minuto {p['single_minute_limit_0_5']['criterion_minute']}.", ""]
    lines += [f"- **{k}** {FROZEN}: {v2}" for k, v2 in p["findings"].items()]
    lines += [f"- **Reglas comprometidas {k}:** {r['rule']} ({r['probe']})" for k, r in p["committed_rules"].items()]
    lines += ["", f"**Clasificación** {FROZEN}: {p['classification']}"]
    return "\n".join(lines)


def render_orden(data: dict) -> str:
    o = data["event_order"]
    return "\n".join([
        f"- La carga y el criterio se leen sobre el estado al inicio del minuto: {_yes(o['reads_start_state'])}; las "
        f"invariantes de observación se comprueban sobre el estado nuevo: {_yes(o['derive_on_new_state'])}.",
        f"- En la trayectoria sintética (gasto 0,1, {o['trajectory_steps']} pasos): la carga del estado previo "
        f"{_n(o['previous_state_burden'], 2)} < límite ≤ {_n(o['burden_when_met'], 2)}; el pulso se pierde en el minuto "
        f"{o['pulse_lost_minute']}.",
        f"- Tras el paro la carga queda congelada y no hay otra transición: {_yes(o['frozen_after_arrest'])}; un solo "
        f"disparo: {_yes(o['no_retrigger'])}.",
        f"- **Clasificación** {FROZEN}: {o['classification']}"])


def render_rosc(data: dict) -> str:
    r = data["rosc"]
    return "\n".join([f"- **Estado:** {r['status']}.",
                      f"- El regreso del pulso tras el paro lanza un error: {_yes(r['guards']['return_of_pulse_raises'])}; "
                      f"terminal_since nunca se borra: {_yes(r['guards']['terminal_since_never_cleared'])}.",
                      f"- Lectura {FROZEN}: {r['reading']}"])


def render_subconjunto(data: dict) -> str:
    x = data["extreme_subset"]
    low = x["lowest"]
    return "\n".join([
        f"- **Filas:** {_int(x['flagged'])} (57m: {_int(x['by_case']['gi_bleed_57m'])}; 72f: "
        f"{_int(x['by_case']['gi_bleed_72f'])}); filtradas: {_yes(x['filtered'])}.",
        f"- **PAM a los 120 min:** {_n(x['map120'][0])}–{_n(x['map120'][1])} mmHg; **PAS:** {_n(x['sbp120'][0])}–"
        f"{_n(x['sbp120'][1])} mmHg; presión relativa {_n(x['pressure_rel120'][0], 3)}–{_n(x['pressure_rel120'][1], 3)}.",
        f"- **Fila de pH más bajo:** pH {_n(low['ph'], 3)}, PaCO2 {_n(low['paco2'])}, déficit {_n(low['deficit'], 3)} "
        f"(fracción {_n(x['deficit_fraction_lowest'], 3)}), minuto {low['minute']}.",
        f"- **DO2 efectivo** (índice, exacto desde el déficit): {_n(x['effective_delivery_lowest'], 3)}; aporte relativo "
        f"{_n(x['delivery_rel_lowest'][0], 3)}–{_n(x['delivery_rel_lowest'][1], 3)}.",
        f"- **Gasto Q (cota, no reconstruido):** {_n(x['output_rel_bounds'][0], 3)}–{_n(x['output_rel_bounds'][1], 3)} "
        f"del de llegada. {FROZEN}: {x['bounds_reading']}",
        f"- **P** {FROZEN}: {x['P']}", f"- **R** {FROZEN}: {x['R']}", f"- **SpO2** {FROZEN}: {x['spo2']}",
        f"- **Pulso:** {_yes(x['pulse'])}. **Problema de estabilidad:** {_yes(x['stability_problem'])}.",
        f"- **Mecanismo de seguridad que falta** {FROZEN}: {x['missing_safety_mechanism']}"])


def render_generalizacion(data: dict) -> str:
    g = data["generalization"]
    rows = ["| Familia | Camino (congelado) | Sonda | La regla actual lo ve | La señal propuesta lo ve | Mecanismo |",
            "|---|---|---|---|---|---|"]
    for name, r in g["rows"].items():
        rows.append(f"| {FAMILY_ES[name]} | {r['pathway']} | {r['probe']} | {_yes(r['current_sees'])} | "
                    f"{_yes(r['proposed_sees'])} | {MECH_ES[r['mechanism']]} |")
    return "\n".join(rows) + (f"\n\n**Con la regla actual:** {g['current']} (no ve: {', '.join(g['current_gap'])}). "
                              f"**Con la señal propuesta:** {g['proposed']}. Condición {FROZEN}: {g['condition']}")


def render_disparadores(data: dict) -> str:
    t = data["trigger_audit"]
    return "\n".join([f"- Lo que la regla de colapso lee de los disparadores prohibidos: "
                      f"{', '.join(t['collapse_rule_reads']) or 'nada'}; en el bloque del integrador: "
                      f"{', '.join(t['integration_block_reads']) or 'nada'}.",
                      f"- El ritmo terminal lee {FROZEN}: {t['terminal_rhythm_reads']}.",
                      f"- Lectura {FROZEN}: {t['reading']}"])


def render_minimo(data: dict) -> str:
    m, rg = data["minimum"], data["ranges"]
    return "\n".join([f"**Clasificación: `{m['classification']}`.**", ""] + [
        f"- **{k}** {FROZEN}: {v}" for k, v in m.items() if k != "classification"] + [
        "", f"- **Rangos candidatos ya comprometidos** {FROZEN}: {rg['existing_committed_candidates']}",
        f"- **Sin valor (UNSET)** {FROZEN}: {rg['unset']}"])


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    rows = ["| Criterio | Cumple |", "|---|---|"] + [f"| {CRITERIA_ES[k]} | {_yes(c)} |" for k, c in v["checks"].items()]
    return "\n".join(rows) + f"\n\n**Veredicto:** `{v['verdict']}`" + (
        f"; fallan: {', '.join(v['failing'])}." if v["failing"] else ".")


def render_pedidas(data: dict) -> str:
    return f"Decisiones pedidas a la docencia {FROZEN}:\n\n" + "\n".join(
        f"{i}. {d}" for i, d in enumerate(data["decisions"], 1))


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return "\n".join([
        f"- Lecturas de estado fijo por el núcleo certificado: {e['fixed_state_readings']}.",
        f"- Pasos del integrador: {e['integrator_steps']} (una trayectoria sintética de orden y un minuto sin pulso); "
        f"actualizaciones de la carga por la función del núcleo: {e['burden_updates']}.",
        f"- Trayectorias GI: {e['gi_trajectories']}; barrido cartesiano: {_yes(e['cartesian_sweep'])}; región "
        f"reconstruida: {_yes(e['region_rebuilt'])}; motor heredado ajustado: {_yes(e['legacy_engine_fitted'])} "
        f"(citado como texto en {e['legacy_text_quoted']} archivos).",
        f"- Registros reutilizados (con huella fijada): {', '.join(e['records_read'])}."])


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the P2M-1 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
