"""P2M-2 report: the generated blocks of docs/revision/P2M2_ARQUITECTURA_COLAPSO.md.

    python -m clinical_core.collapse_architecture_report --write <document> --data <the P2M-2 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("decisiones", "candidato", "sondas", "persistencia", "orden", "llegada", "rosc", "generalizacion",
         "subconjunto", "supersesion", "parametros", "no_regresion", "veredicto", "recomendacion", "pedidas",
         "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FROZEN = "(texto congelado, en inglés)"
CRITERIA_ES = {"max_of_map_and_delivery": "máximo de la falla de PAM y la de aporte",
               "no_duplicate_inputs": "sin entradas duplicadas (Q, SpO2, lactato, D, pH, I, F)",
               "persistence_repays": "la persistencia se repaga",
               "historical_burden_cannot_arrest": "la carga histórica sola no produce paro",
               "arrival_semantics": "llegada: carga 0, señal de la fisiología real",
               "event_order_acyclic": "orden de eventos acíclico", "no_pulse_consistent": "sin pulso, coherente",
               "future_rosc_possible": "un ROSC futuro sigue siendo posible",
               "seven_family_probes_pass": "las siete familias pasan", "upstream_unchanged": "fisiología previa intacta",
               "no_clinical_threshold_approved": "ningún umbral clínico aprobado"}
FAMILY_ES = {"hemorrhagic": "Shock hemorrágico", "cardiogenic": "Shock cardiogénico", "obstructive": "Shock obstructivo",
             "distributive": "Shock distributivo", "anaphylaxis": "Anafilaxia", "malignant_arrhythmia": "Arritmia maligna",
             "respiratory_failure": "Insuficiencia respiratoria"}
ITEM_ES = {"BloodState": "BloodState", "output": "gasto", "pressure_tone": "presión / tono", "DO2_deficit": "DO2 / déficit",
           "D": "D", "lactate": "lactato", "HR_baroreflex": "FC / barorreflejo", "acid_base": "ácido-base",
           "RR_W": "FR / W", "consciousness": "conciencia"}
DOM_ES = {"perfusion_failure": "PAM", "oxygen_delivery_failure": "aporte"}


def _dom(row: dict) -> str:
    return " y ".join(DOM_ES[d] for d in row.get("dominant") or []) or "—"


def render_decisiones(data: dict) -> str:
    return f"Decisiones de la docencia {FROZEN}:\n\n" + "\n".join(
        f"- **{k}**: {v}" for k, v in data["design"]["faculty"].items())


def render_candidato(data: dict) -> str:
    d = data["design"]
    lines = ["**Ecuación:** `collapse_signal = max(perfusion_failure_signal, oxygen_delivery_failure_signal)`; nunca "
             "una suma.", "", "**Entradas graduadas** " + FROZEN + ":", ""]
    lines += [f"- **{k}** (lee `{v[0]}`): {v[1]}" for k, v in d["inputs"].items()]
    lines += ["", f"**Lo que no entra** {FROZEN}:", ""] + [f"- **{k}**: {v}" for k, v in d["excluded"].items()]
    lines += ["", f"**Estado de cada parte** {FROZEN}:", ""] + [
        f"- **{k}**: {v}" for k, v in d["candidate_status"].items()]
    s = d["synthetic"]
    lines += ["", f"**Valores de las sondas** {FROZEN}: {s['rule']}"]
    return "\n".join(lines)


def render_sondas(data: dict) -> str:
    st, d = data["structural"], data["design"]["structural"]
    s, q, o, m, p = data["signals"], data["no_q"], data["no_spo2"], data["no_markers"], data["no_pulse"]
    rows = ["| Sonda | Qué prueba (congelado) | Cumple |", "|---|---|---|"]
    rows += [f"| {k} | {d[k]} | {_yes(st[k])} |" for k in sorted(st, key=lambda c: int(c[1:]))]
    r4 = s["C4"]["reading"]
    rows += ["", "Lecturas (valores sintéticos):", "",
             f"- **C1–C4 inyectadas:** (0; 0) → {_n(s['C1']['injected_signal'], 2)}; (0,6; 0) → "
             f"{_n(s['C2']['injected_signal'], 2)}; (0; 0,5) → {_n(s['C3']['injected_signal'], 2)}; (0,6; 0,5) → "
             f"{_n(s['C4']['injected_signal'], 2)}, no 1,1.",
             f"- **C2 en estado** (tono 0,45): PAM {_n(s['C2']['reading']['map'])}, falla de PAM "
             f"{_n(s['C2']['reading']['perfusion'], 3)}, de aporte {_n(s['C2']['reading']['delivery'], 3)}.",
             f"- **C3 en estado** (Hb al 25 %): falla de PAM {_n(s['C3']['reading']['perfusion'], 3)}, de aporte "
             f"{_n(s['C3']['reading']['delivery'], 3)}.",
             f"- **C4 en estado** (bomba 0,3): {_n(r4['perfusion'], 3)} y {_n(r4['delivery'], 3)} → señal "
             f"{_n(r4['signal'], 3)} (la suma sería {_n(r4['perfusion'] + r4['delivery'], 3)}).",
             f"- **C5:** gasto {_n(q['a']['output_rel'], 3)} frente a {_n(q['b']['output_rel'], 3)} con la misma PAM "
             f"({_n(q['a']['map'], 2)}) y el mismo aporte; diferencia de señal {q['signal_difference']:.1e}. El estado "
             f"de la revisión ALTO-2 de P2M-1 (bomba 0,7, tono 2,0: gasto {_n(q['flow_alone_h2']['output_rel'], 3)}, PAM "
             f"{_n(q['flow_alone_h2']['map'])}) da señal {_n(q['flow_alone_h2']['signal'], 2)}.",
             f"- **C6:** SpO2 {_n(o['a']['spo2'])} frente a {_n(o['b']['spo2'])} con el mismo aporte: señal "
             f"{_n(o['a']['signal'], 3)} en ambos.",
             f"- **C7:** con bomba 0,3 la señal es {_n(m['base_signal'], 3)}; con D, lactato o carga ácida cambiados "
             f"solos: " + ", ".join(f"{k} {_n(r['signal'], 3)}" for k, r in m["rows"].items()) + f". I y F: {m['I_F']}.",
             f"- **C12:** sin pulso, gasto {_n(p['C12']['output_rel'], 1)}, PAM {_n(p['C12']['map'])}, aporte "
             f"{_n(p['C12']['delivery_rel'], 1)}; estado {p['C12']['status']}; la carga pasa de 4 a "
             f"{_n(p['C12']['burden_after'], 1)}.",
             f"- **C13:** con pulso y gasto en el cero numérico: " + ", ".join(
                 f"{k} → {v}" for k, v in p["C13"]["fired"].items()) + ".",
             f"- **C14:** con pulso, PAM {_n(p['C14']['rows']['P_0_02']['map'], 1)} (bomba 0,02) y "
             f"{_n(p['C14']['rows']['P_0_1_avb']['map'], 1)} (bomba 0,1 con bloqueo AV): colapso representable; el "
             f"primer minuto no produce transición."]
    return "\n".join(rows)


def render_persistencia(data: dict) -> str:
    p = data["persistence"]
    c8, c9, c10, c11 = p["C8"], p["C9"], p["C10"], p["C11"]
    return "\n".join([
        f"**Forma** {FROZEN}: `{p['form']}`.", "",
        f"- **C8, un insulto breve** (3 min a señal 1): pico {_n(c8['peak'], 2)}; transición: "
        f"{_yes(c8['terminal'] is not None)}. Un minuto al máximo suma a lo sumo {_n(c8['one_minute_ceiling'], 3)}; el "
        f"perfil rechaza un límite a esa altura: {_yes(c8['single_minute_limit_refused'])}.",
        f"- **C9, un insulto prolongado** (señal 0,9): carga {_n(c9['burden_at_3'], 2)} a los 3 min, "
        f"{_n(c9['burden_at_14'], 2)} a los 14, {_n(c9['burden_at_60'], 2)} a los 60; criterio sintético en el minuto "
        f"{c9['terminal_minute']}.",
        "- **C10, fisiología restaurada:** " + "; ".join(
            f"desde {_n(float(k), 1)}: {_n(v['after_60'], 2)} a los 60 min y {_n(v['after_120'], 2)} a los 120, cae siempre: "
            f"{_yes(v['falls_monotonically'])}, paro tardío: {_yes(v['terminal'] is not None)}"
            for k, v in sorted(c10["from"].items(), key=lambda kv: float(kv[0]))) +
        f". Restauración parcial (señal {_n(c10['partial_signal'], 1)}, bajo el piso 0,5): "
        f"{_n(c10['partial_after_120'], 2)} a los 120 min, hacia {_n(c10['partial_ceiling'], 1)}; paro: "
        f"{_yes(c10['partial_terminal'] is not None)}. El perfil rechaza un criterio sin piso de no viabilidad actual: "
        f"{_yes(c10['terminal_without_floor_refused'])}.",
        f"- **C11, insultos intermitentes** ({c11['pattern']}): picos {_n(c11['cycle_peaks_first_last'][0], 2)} → "
        f"{_n(c11['cycle_peaks_first_last'][1], 2)}, crecimiento en el último ciclo {_n(c11['peak_growth_last_cycle'], 6)}; "
        f"máximo {_n(c11['max'], 2)} (cota τ = {_n(c11['bound'], 0)}); paro: {_yes(c11['terminal'] is not None)}."])


def render_orden(data: dict) -> str:
    o = data["event_order"]
    df, sa, sb = o["deferral"], o["scripted_arrest"], o["stale_burden_normal_physiology"]
    return "\n".join([
        "Orden: `state(t) → derive(t) → collapse_signal(t) → carga(t+1) → decisión (persistencia + no viabilidad "
        "actual) → transición del ritmo en el minuto del núcleo → state(t+1)`.", "",
        f"- **Trayectoria** (bomba 0,1): transición en el minuto {o['terminal_minute']}, una sola "
        f"({o['transitions']}); carga al cumplirse {_n(o['burden_when_met'], 2)} antes del minuto; cada minuto lee el "
        f"estado previo: {_yes(o['reads_start_state'])}. Después: {', '.join(o['after_transition']['statuses'])}, carga "
        f"{', '.join(_n(b, 1) for b in o['after_transition']['burdens'])}, pulso {_yes(o['after_transition']['pulse'])}.",
        f"- **Código:** `evaluate` una vez por minuto ({o['code']['evaluate_calls_in_shadow_step']}), antes del paso "
        f"del núcleo: {_yes(o['code']['evaluate_before_step'])}, sobre el estado de inicio: "
        f"{_yes(o['code']['evaluate_reads_start_state'])}.",
        f"- **Diferimiento:** en el minuto 14 un evento guionizado pasa a bloqueo AV; la transición se difiere "
        f"({_yes(df['minute_14']['deferred'])}) y en el 15 se decide sobre la fisiología del ritmo nuevo (señal "
        f"{_n(df['minute_15']['signal'], 2)}): {df['minute_15']['applied']}.",
        f"- **Paro guionizado con carga:** carga {_n(sa['burden_before'], 2)} → {_n(sa['burden_after'], 1)} al perder "
        f"el pulso.",
        f"- **Carga vieja con fisiología normal** (revisión ALTO-1 de P2M-1): carga 10,5, señal "
        f"{_n(sb['signal'], 1)} → {_n(sb['burden_after'], 2)}, pulso {_yes(sb['pulse'])}, sin transición."])


def render_llegada(data: dict) -> str:
    a = data["arrival"]["rows"]
    return "\n".join([
        f"- **Llegada de referencia:** carga {_n(a['reference']['arrival_burden'], 1)}, señal "
        f"{_n(a['reference']['arrival_signal'], 2)}; a los 30 min, carga {_n(a['reference']['burden_after_30'], 2)}.",
        f"- **Llegada con PAM 70 (presión autorizada 95/57,5):** carga {_n(a['authored_map_70']['arrival_burden'], 1)}, "
        f"señal {_n(a['authored_map_70']['arrival_signal'], 3)} (la de su fisiología, no forzada a 0); a los 30 min, "
        f"carga {_n(a['authored_map_70']['burden_after_30'], 2)}, sin transición."])


def render_rosc(data: dict) -> str:
    r = data["rosc"]
    return "\n".join([f"- **Estado:** {r['status']}.",
                      f"- Tras la transición la carga es {_n(r['burden'], 1)}; un estado con ritmo que perfunde (el que "
                      f"daría un ROSC futuro, con terminal_since borrado por esa regla futura) se evalúa: "
                      f"{r['post_arrest_pulse_state']}. El candidato no lee terminal_since: "
                      f"{_yes(not r['candidate_reads_terminal_since'])}.",
                      f"- Guardas del núcleo que siguen: el regreso del pulso lanza un error "
                      f"({_yes(r['core_guards']['return_of_pulse_raises'])}); terminal_since no se borra "
                      f"({_yes(r['core_guards']['terminal_since_never_cleared'])})."])


def render_generalizacion(data: dict) -> str:
    g = data["generalization"]
    rows = ["| Familia | Qué mueve su escritor | Lógica esperada | Falla de PAM | Falla de aporte | Señal | Domina | "
            "Cumple |", "|---|---|---|---|---|---|---|---|"]
    for name in FAMILY_ES:
        r = g["rows"][name]
        cells = r["variants"].items() if "variants" in r else (("", r["reading"]),)
        for label, x in cells:
            title = FAMILY_ES[name] + (f" ({label})" if label else "")
            rows.append(f"| {title} | {r['what']} | {r['logic']} | {_n(x['perfusion'], 3)} | {_n(x['delivery'], 3)} | "
                        f"{_n(x['signal'], 3) if x['pulse'] else 'paro'} | {_dom(x) if x['pulse'] else '—'} | "
                        f"{_yes(g['checks'][name])} |")
    return "\n".join(rows) + (f"\n\nTérminos de enfermedad en el candidato: {', '.join(g['disease_terms']) or 'ninguno'}. "
                              f"{FROZEN}: {g['one_function']}.")


def render_subconjunto(data: dict) -> str:
    x = data["extreme_subset"]
    return "\n".join([
        f"- **Filas:** {x['flagged']:,}".replace(",", " ") + f" (57m: {x['by_case']['gi_bleed_57m']:,}".replace(",", " ")
        + f"); filtradas: {_yes(x['filtered'])}; pulso: {_yes(x['pulse'])}; PAM a los 120 min "
        f"{_n(x['map120'][0])}–{_n(x['map120'][1])} mmHg.",
        f"- **Entradas disponibles:** {', '.join(x['inputs_available'])}. **Estado:** `{x['status']}`; clasificación: "
        f"{x['classification'] or 'ninguna'}.", f"- {FROZEN}: {x['reading']}"])


def render_supersesion(data: dict) -> str:
    rows = ["| Punto de P2M-1 | Estado | Lo que decía P2M-1 (congelado) | Lo que lo reemplaza | Evidencia |",
            "|---|---|---|---|---|"]
    rows += [f"| {k} | `{v['status']}` | {v['p2m1']} | {v['p2m2']} | {v['evidence']} |"
             for k, v in data["supersession"].items()]
    return "\n".join(rows) + "\n\nEl registro y el informe de P2M-1 no se reescriben (huella fijada)."


def render_parametros(data: dict) -> str:
    return "\n".join(f"- **{k}:** `{v}`" for k, v in data["parameters"].items())


def render_no_regresion(data: dict) -> str:
    n, up = data["nonregression"], data["upstream"]
    rows = ["| Elemento | Idéntico |", "|---|---|"] + [f"| {ITEM_ES[k]} | {_yes(n['identical'][k])} |" for k in ITEM_ES]
    return "\n".join(rows) + "\n\n" + "\n".join([
        f"- **Inactiva:** el árbol de P2M-1 coincide byte a byte: {_yes(up['unchanged'])} ({up['files']} archivos, "
        f"`{up['digest'][:12]}…`); importan el candidato sólo: {', '.join(up['imported_by'])}.",
        f"- **Activa en sombra** ({n['minutes']} min, bomba que cae 0,03 por minuto, cinética sintética sin criterio "
        f"terminal): todo el estado salvo la carga coincide: {_yes(n['whole_state_but_burden'])}; registros del núcleo "
        f"idénticos: {_yes(n['records_identical'])}; carga del núcleo {_n(n['plain_burden'], 1)}, de la capa "
        f"{_n(n['shadow_burden_last'], 2)}."])


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    rows = ["| Criterio | Cumple |", "|---|---|"] + [f"| {CRITERIA_ES[k]} | {_yes(v['checks'][k])} |" for k in CRITERIA_ES]
    return "\n".join(rows) + f"\n\n**Veredicto:** `{v['verdict']}`" + (
        f"; fallan: {', '.join(v['failing'])}." if v["failing"] else ".")


def render_recomendacion(data: dict) -> str:
    r = data["recommendation"]
    lines = [f"**Recomendación:** `{r['recommendation']}`."]
    if "numeric_collapse_calibration_required_before_second_family" in r:
        lines += ["", f"- ¿Hace falta calibrar el colapso numéricamente antes de la segunda familia? "
                      f"{_yes(r['numeric_collapse_calibration_required_before_second_family'])}.",
                  f"- Por qué {FROZEN}: {r['why']}"]
    return "\n".join(lines + ["", f"Regla {FROZEN}: {r['rule']}"])


def render_pedidas(data: dict) -> str:
    return f"Decisiones pedidas a la docencia {FROZEN}:\n\n" + "\n".join(
        f"{i}. {d}" for i, d in enumerate(data["decisions"], 1))


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return "\n".join([
        f"- Secciones de estado fijo leídas por el núcleo certificado: {', '.join(e['fixed_state_sections'])}.",
        f"- Minutos de sombra o del núcleo: {e['shadow_minutes']}; actualizaciones de la carga: {e['burden_updates']}.",
        f"- Trayectorias GI: {e['gi_trajectories']}; barrido cartesiano: {_yes(e['cartesian_sweep'])}; región "
        f"reconstruida: {_yes(e['region_rebuilt'])}; motor heredado ajustado: {_yes(e['legacy_engine_fitted'])}.",
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
    parser.add_argument("--data", type=Path, required=True, help="the P2M-2 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
