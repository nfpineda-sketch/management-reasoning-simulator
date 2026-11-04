"""P2Q-2 report: the generated blocks of docs/revision/P2Q2_TEP_SOMBRA.md.

    python -m clinical_core.embolism_migration_report --write <document> --data <the P2Q-2 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("caso", "llegada", "escritores", "obstruccion", "doble_conteo", "dueno_l", "fluidos", "g_directa", "oxigeno",
         "impulso", "depresion", "tono", "fc", "d_lactato", "colapso", "secundario", "observables", "legado",
         "no_regresion", "prueba", "veredicto", "brechas")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
PRIMARY, SECONDARY = "pulmonary_embolism_61m", "pulmonary_embolism_33f"


def _by_minute(rows: dict) -> list:
    return sorted(rows.items(), key=lambda item: int(item[0]))


def _truth_lines(name: str, t: dict) -> str:
    return (f"- **`{name}`:** «{t['diagnosis']}». PA {t['sbp']}/{t['dbp']}, FC {t['hr']} ({t['rhythm']}), SpO2 "
            f"{t['spo2']} % aire ambiente, FR {t['respiratory_rate']}, trabajo respiratorio «{t['work_of_breathing']}», "
            f"llenado capilar {t['crt_s']} s, extremidades «{t['extremities']}», perfusión «{t['peripheral_perfusion']}», "
            f"«{t['mental_status']}». Gases arteriales {t['abg_ph']} / PaCO2 {t['abg_paco2']} / PaO2 {t['abg_pao2']}, "
            f"HCO3 {t['abg_hco3']}; lactato {t['lactate_mmol_l']}; Hb {t['hb_g_dl']}; troponina {t['troponin_ng_l']}; "
            f"ECG `{t['ecg_profile']}`.\n"
            f"  - POCUS: VD «{t['pocus_rv']}»; VI «{t['pocus_lv']}»; VCI «{t['pocus_ivc']}»; pulmones «{t['pocus_lungs']}»; "
            f"poplítea «{t['pocus_dvt_popliteal']}». Radiografía «{t['chest_xray']}». Angio-TC «{t['ctpa']}».\n"
            f"  - Exploración: «{t['cardiac_exam']}»; «{t['respiratory_exam']}». Inicio: «{' '.join(t['onset'])}». "
            f"Tratamientos definitivos autorales: {', '.join(t['definitive_actions'])}.")


def render_caso(data: dict) -> str:
    c = data["case"]
    lines = [_truth_lines(name, v["truth"]) for name, v in c["cases"].items()]
    return ("\n".join(lines) + f"\n- **Regla de selección:** {c['selection_rule']}.\n- **Observaciones posteriores:** "
            f"{c['later_observations']}.\n- **Comportamiento heredado (sólo referencia):** {c['legacy_constants']}.\n"
            f"- Verdad suficiente (todos los ítems leídos): {_yes(c['available'])}.")


def _arrival_table(a: dict) -> str:
    rows = ["| Ítem | Núcleo | Autoral | Exacto |", "|---|---|---|---|"]
    for k in ("sbp", "dbp", "map", "spo2", "paco2", "lactate", "consciousness_level"):
        rows.append(f"| {k} | {_n(a['core'][k], 2)} | {_n(a['authored'][k], 2)} | {_yes(a['exact'][k])} |")
    rows.append(f"| pH | {_n(a['core']['ph'], 3)} | {_n(a['authored']['ph'], 2)} | redondeo: "
                f"{_yes(a['ph_within_rounding'])} |")
    return "\n".join(rows)


def render_llegada(data: dict) -> str:
    a = data["arrival"]
    m = a["mapping"]
    roles = ["| Canal | Papel |", "|---|---|"] + [f"| {k} | {v} |" for k, v in a["channel_roles"].items()]
    bands = ["| Banda | Inferior | Punto medio | Superior | Clase |", "|---|---|---|---|---|"]
    bands += [f"| {k} | {_n(b['lower'], 3)} | {_n(b['midpoint'], 3)} | {_n(b['upper'], 3)} | {b['classification']} |"
              for k, b in a["bands"].items()]
    p = data["position"]
    return ("\n".join(roles) + "\n\n" + "\n".join(bands) + "\n\n" + _arrival_table(a)
            + f"\n\n- Reconstrucción de llegada: {a['reconstruction']}.\n- Posición de precarga de llegada "
            f"{_n(m['preload_position'], 2)} (por defecto {_n(m['default_position'], 2)}), leída del VI "
            f"(`{', '.join(m['v_evidence'])}`; VI hipollenado: {_yes(m['lv_underfilled'])}). VCI «{m['ivc']}»: "
            f"{m['ivc_status']}.\n- Reserva de bomba {_n(m['pump_reserve'], 1)} (neutra); L_rev {_n(m['reversible_lung_water'], 1)}; "
            f"edema pulmonar autoral: {_yes(m['authored_pulmonary_edema'])}; generación propia de L "
            f"{_n(m['lung_water_generation'], 1)}.\n- La posición de llegada no cambia nada de la llegada (puntos "
            f"{', '.join(_n(x, 2) for x in p['points'])}): {_yes(p['pass'])}.")


def render_escritores(data: dict) -> str:
    w = data["writer"]
    rows = ["| Escritor | Escribe | Lee del estado | Autoridad sobre L |", "|---|---|---|---|"]
    rows += [f"| `{k}` | {', '.join(v['writes'])} | {', '.join(v['reads_state'])} | {_yes(w['authority'][k])} |"
             for k, v in w["classes"].items()]
    return ("\n".join(rows) + f"\n\n- Escribe V: {_yes(w['writes_v'])}; nombres prohibidos usados: "
            f"{', '.join(w['forbidden_names_used']) or 'ninguno'}; código opioide: {_yes(w['opioid_code'])}.\n"
            f"- Registrados y reproducibles: {_yes(w['registered'])}; el dueño con tasa cero no escribe: "
            f"{_yes(w['zero_owner_writes'])}; rechazos: "
            + ", ".join(f"{k} {_yes(v)}" for k, v in w["refusals"].items()) + f".\n- Cumple: {_yes(w['pass'])}.")


def render_obstruccion(data: dict) -> str:
    o, u = data["obstruction"], data["untreated"]
    rows = ["| Pérdida de P / min | P 120 | Gasto 120 | PAM 120 | Aporte 120 | Déficit 120 | D 120 | V = 0 | L = 0 |",
            "|---|---|---|---|---|---|---|---|---|"]
    for k, v in o["region"].items():
        x = v["at"]["120"]
        rows.append(f"| {k} | {_n(x['P'], 3)} | {_n(x['output_rel'], 3)} | {_n(x['map'], 1)} | "
                    f"{_n(x['delivery_index'], 3)} | {_n(x['deficit'], 3)} | {_n(x['D'], 1)} | {_yes(v['V_zero'])} | "
                    f"{_yes(v['L_zero'])} |")
    traj = ["| Minuto | P | G | Gasto | PAM | Aporte | Déficit | D | Lactato | FC | T | SpO2 | FR | Conciencia |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m, x in _by_minute(u["at"]):
        traj.append(f"| {m} | {_n(x['P'], 3)} | {_n(x['G'], 3)} | {_n(x['output_rel'], 3)} | {_n(x['map'], 1)} | "
                    f"{_n(x['delivery_index'], 3)} | {_n(x['deficit'], 3)} | {_n(x['D'], 1)} | {_n(x['lactate'], 2)} | "
                    f"{_n(x['hr'], 1)} | {_n(x['T'], 3)} | {_n(x['spo2'], 1)} | {_n(x['rr'], 1)} | "
                    f"{x['consciousness_level']} |")
    return ("Obstrucción sola (con el dueño de L), por punto del tramo:\n\n" + "\n".join(rows)
            + f"\n\nCumple: {_yes(o['pass'])}.\n\nCurso de referencia sin tratamiento (todos los escritores en el punto "
              "medio), hasta 240 min:\n\n" + "\n".join(traj)
            + f"\n\nCanales escritos por la familia: {', '.join(u['family']['channels'])}; escrituras del acoplamiento "
              f"común de sobrecarga: {u['common_overload_writes']}; L máximo {_n(u['L_max'], 3)}; V máximo "
              f"{_n(u['V_max'], 3)}; pulso conservado: {_yes(u['pulse_kept'])}.")


def render_doble_conteo(data: dict) -> str:
    d = data["no_double_count"]
    return (f"- Fuentes de V sin tratamiento: {', '.join(d['v_sources_untreated']) or 'ninguna'}; con el bolo: "
            f"{', '.join(d['v_sources_with_fluid'])}.\n- Fuentes de P: {', '.join(d['p_sources_untreated'])} (con el "
            f"bolo: {', '.join(d['p_sources_with_fluid'])}).\n- Canales de la familia: "
            f"{', '.join(d['untreated_family_channels'])}.\n- La posición de llegada no cambia la llegada: "
            f"{_yes(d['arrival_position_invariant'])}.\n- El mapeo de V lee: {', '.join(d['v_mapping_reads'])}; lee "
            f"el lado derecho (VCI, yugulares, VD): {_yes(d['v_mapping_reads_right_side'])}.\n- Cumple: {_yes(d['pass'])}.")


def render_dueno_l(data: dict) -> str:
    o = data["lung_water_owner"]
    c, m = o["counterfactual_rejected_ivc_no_owner"], o["counterfactual_lv_mapping_no_owner"]
    return (f"- Con el dueño (mapeo del VI, obstrucción, G y bolo): escrituras comunes {o['owned']['common_writes']}, "
            f"escrituras de L {o['owned']['L_writes']}, L máximo {_n(o['owned']['L_max'], 3)}.\n- Con el dueño en el "
            f"mapeo rechazado de la VCI ({_n(o['rejected_ivc_preload'], 1)}): escrituras comunes "
            f"{o['rejected_ivc_owned']['common_writes']}, L máximo "
            f"{_n(o['rejected_ivc_owned']['L_max'], 3)}.\n- Contrafáctico sin dueño en el mapeo rechazado de la VCI: "
            f"{c['common_writes']} escrituras comunes, L máximo {_n(c['L_max'], 3)}, SpO2 final {_n(c['spo2_end'], 2)} "
            f"(el conflicto de P2Q-1, reproducido).\n- Contrafáctico sin dueño en el mapeo del VI: {m['common_writes']} "
            f"escrituras, L máximo {_n(m['L_max'], 3)}, posición máxima {_n(m['position_max'], 3)} (rodilla "
            f"{_n(o['knee'], 2)}).\n- Segundo dueño rechazado: {_yes(o['second_owner_refused'])}; generación propia: "
            + ", ".join(f"`{k}` {_n(v, 1)}" for k, v in o["generation"].items()) + f".\n- Cumple: {_yes(o['pass'])}.")


def render_fluidos(data: dict) -> str:
    f = data["fluid_stress"]
    rows = ["| Punto de la banda | Precarga | Minuto | Gasto sin | Gasto con | Ganancia | Ganancia sin obstrucción | "
            "Ganancia de PAM | Posición con | SpO2 sin / con | L máx | Escrituras comunes |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for point, v in f["points"].items():
        for minute, x in _by_minute(v["at"]):
            rows.append(f"| {point} | {_n(v['preload_fraction'], 2)} | {minute} | {_n(x['output_without'], 3)} | "
                        f"{_n(x['output_with'], 3)} | {_n(x['output_gain'], 3)} | {_n(x['unobstructed_output_gain'], 3)} | "
                        f"{_n(x['map_gain'], 1)} | {_n(x['position_with'], 3)} | {_n(x['spo2_without'], 2)} / "
                        f"{_n(x['spo2_with'], 2)} | {_n(v['L_max'], 3)} | {v['common_overload_writes']} |")
    limited = ", ".join(f"{p} {_yes(v['response_limited_vs_unobstructed'])}" for p, v in f["points"].items())
    bare = ", ".join(f"{p}: {v['no_owner']['common_writes']} escrituras, L máx {_n(v['no_owner']['L_max'], 3)}, posición "
                     f"máx {_n(v['no_owner']['position_max'], 3)}" for p, v in f["points"].items())
    d = f["design"]
    return (f"Bolo SYNTHETIC_ONLY de {_n(d['volume_ml'], 0)} mL desde el minuto {d['begins_at_minute']} en "
            f"{_n(d['duration_min'], 0)} min, con obstrucción, G y el dueño de L.\n\n" + "\n".join(rows)
            + f"\n\nRespuesta menor que sin obstrucción: {limited}. SpO2 y G no cambian con el bolo en ningún punto. "
              f"Sin el dueño (contrafáctico, sólo informado): {bare}. Cumple: {_yes(f['pass'])}.")


def render_g_directa(data: dict) -> str:
    g = data["direct_g"]
    rows = ["| G / min | G 120 | SpO2 120 | Aporte 120 | Lineal | Mapeo común | Sin crédito L_rev | L_rev −0,5 no cambia |",
            "|---|---|---|---|---|---|---|---|"]
    for k, v in g["rates"].items():
        x = v["at"]["120"]
        rows.append(f"| {k} | {_n(x['G'], 3)} | {_n(x['spo2'], 2)} | {_n(x['delivery_index'], 3)} | "
                    f"{_yes(v['G_linear'])} | {_yes(v['spo2_is_common_mapping'])} | {_yes(v['credit_zero'])} | "
                    f"{_yes(v['negative_l_rev_changes_nothing'])} |")
    return "\n".join(rows) + f"\n\nCumple: {_yes(g['pass'])}."


def render_oxigeno(data: dict) -> str:
    o = data["oxygen"]
    rows = ["| Minuto | Aire ambiente | FiO2 0,4 | FiO2 0,6 |", "|---|---|---|---|"]
    for m, x in _by_minute(o["room_air"]):
        rows.append(f"| {m} | {_n(x, 2)} | {_n(o['fio2']['0.4'][m], 2)} | {_n(o['fio2']['0.6'][m], 2)} |")
    return ("\n".join(rows) + f"\n\n- Monótona en FiO2 cada minuto: {_yes(o['monotone_in_fio2'])}; ganancia de FiO2 0,6 "
            f"a los 30 min {_n(o['gain_at_30'], 2)} y a los 120 {_n(o['gain_at_120'], 2)} (atenuada al empeorar G: "
            f"{_yes(o['attenuated_as_G_worsens'])}); función de oxígeno de la familia: "
            f"{_yes(o['family_oxygen_function'])}.\n- Cumple: {_yes(o['pass'])}.")


def render_impulso(data: dict) -> str:
    r = data["respiratory_drive"]
    rows = ["| Minuto | Impulso ácido | Hipoxémico UNSET | Hipoxémico sintético | FR UNSET | FR sintética |",
            "|---|---|---|---|---|---|"]
    for m, x in _by_minute(r["synthetic"]):
        u = r["unset"][m]
        rows.append(f"| {m} | {_n(x['acid'], 2)} | {_n(u['hypoxaemic'], 2)} | {_n(x['hypoxaemic'], 2)} | "
                    f"{_n(u['expressed_rr'], 2)} | {_n(x['expressed_rr'], 2)} |")
    ps = r["parameter_status"]
    return ("\n".join(rows) + f"\n\n- FR autoral {r['authored_rr']}; FR de llegada UNSET {_n(r['arrival_rr']['unset'], 2)} "
            f"(brecha {_n(r['arrival_rr_gap']['unset'], 2)}), sintética {_n(r['arrival_rr']['synthetic'], 2)} (brecha "
            f"{_n(r['arrival_rr_gap']['synthetic'], 2)}).\n- UNSET no da impulso hipoxémico: "
            f"{_yes(r['unset_no_hypoxaemic_drive'])}; el sintético impulsa en la llegada: "
            f"{_yes(r['synthetic_drives_at_arrival'])} y crece al empeorar G: {_yes(r['synthetic_rises_with_G'])}; "
            f"estados idénticos (la FR no realimenta nada): {_yes(r['states_identical'])}; la familia escribe W: "
            f"{_yes(r['family_writes_w'])}.\n- Parámetros: {ps['hypoxaemic_drive_mapping']}; {ps['hypoxaemic_to_drive_gain']}; "
            f"elegido del TEP: {_yes(ps['chosen_from_pe'])}.\n- Cumple: {_yes(r['pass'])}.")


def render_depresion(data: dict) -> str:
    d = data["central_depression"]
    rows = ["| Minuto | FR intacta | FR deprimida | PaCO2 intacta | PaCO2 deprimida |", "|---|---|---|---|---|"]
    for m, x in _by_minute(d["depressed"]):
        i = d["intact"][m]
        rows.append(f"| {m} | {_n(i['expressed_rr'], 2)} | {_n(x['expressed_rr'], 2)} | {_n(i['paco2'], 1)} | "
                    f"{_n(x['paco2'], 1)} |")
    return ("\n".join(rows) + f"\n\n- Disponibilidad {_n(d['availability'], 2)}, cota {_n(d['bound'], 2)}: en o bajo la "
            f"intrínseca {_yes(d['at_or_below_intrinsic'])}, dentro de la cota {_yes(d['within_bound'])}, PaCO2 mayor "
            f"{_yes(d['paco2_higher'])}, impulso hipoxémico igual {_yes(d['hypoxaemic_drive_unchanged'])}, estados "
            f"idénticos {_yes(d['states_identical'])}, archivo de la composición sin cambios "
            f"{_yes(d['composition_file_unchanged'])}.\n- Cumple: {_yes(d['pass'])}.")


def render_tono(data: dict) -> str:
    t = data["tone"]
    rows = ["| Ganancia de tono | T 120 | Gasto 120 | PAM 120 | Déficit 120 | D 120 |", "|---|---|---|---|---|---|"]
    rows += [f"| {k} | {_n(v['T'], 3)} | {_n(v['output_rel'], 3)} | {_n(v['map'], 1)} | {_n(v['deficit'], 3)} | "
             f"{_n(v['D'], 1)} |" for k, v in t["sensitivity"].items()]
    return ("\n".join(rows) + f"\n\n- A los 120 min (ganancia {_n(t['tone_gain'], 2)}): T {_n(100 * t['T_change'], 1)} %, "
            f"gasto {_n(100 * t['output_change'], 1)} %, PAM {_n(100 * t['map_change'], 1)} %.\n- La familia escribe T: "
            f"{_yes(t['family_writes_T'])}; ganancias sin tocar: {_yes(t['gains_untouched'])}.\n- {t['classification']}."
            f"\n- Cumple: {_yes(t['pass'])}.")


def render_fc(data: dict) -> str:
    h = data["heart_rate"]
    rows = ["| Caso | FC autoral | FC predicha | Desajuste | Predicha sobre las bandas | Autoral dentro |",
            "|---|---|---|---|---|---|"]
    for k, v in h["cases"].items():
        band = " / ".join(_n(x, 1) for x in v["predicted_over_bands"].values())
        rows.append(f"| `{k}` | {_n(v['authored'], 0)} | {_n(v['predicted'], 1)} | {_n(v['mismatch_bpm'], 1)} | {band} | "
                    f"{_yes(v['authored_inside_band'])} |")
    return ("\n".join(rows) + f"\n\n- {h['classification']}.\n- La FC sube con el deterioro: "
            f"{_yes(h['hr_rises_with_deterioration'])}; ganancias sin tocar: {_yes(h['gains_untouched'])}.")


def render_d_lactato(data: dict) -> str:
    d = data["d_lactate"]
    rows = ["| Minuto | D | Lactato |", "|---|---|---|"]
    rows += [f"| {m} | {_n(d['D'][m], 1)} | {_n(x, 2)} |" for m, x in _by_minute(d["lactate"])]
    b = d["arrival_D_band"]
    return ("\n".join(rows) + f"\n\n- D de llegada {_n(d['arrival_D'], 1)} (banda {_n(b['lower'], 0)}–{_n(b['upper'], 0)}, "
            f"{b['classification']}); no depende del lactato: {_yes(d['d_independent_of_lactate'])}; secundario "
            f"{_n(d['secondary_arrival_D'], 1)}.\n- Lactato del núcleo cada minuto: "
            f"{_yes(d['lactate_core_only']['core_lactate_every_minute'])}; sin escritura de la familia: "
            f"{_yes(d['lactate_core_only']['no_family_lactate_write'])}; cinéticas sin tocar: "
            f"{_yes(d['kinetics_untouched'])}.\n- El exceso de llegada se aclara antes de que domine la deuda nueva: "
            f"{_yes(d['arrival_excess_clears_first'])}; mínimo en el minuto {d['minimum_lactate_minute']}; vuelve a subir "
            f"después: {_yes(d['rises_after_minimum'])}. No se fuerza la monotonía.")


def render_colapso(data: dict) -> str:
    c = data["collapse"]
    rows = ["| Minuto | PAM | Señal de aporte | Perfusión UNSET | Perfusión estructural | Señal | max |",
            "|---|---|---|---|---|---|---|"]
    rows += [f"| {r['minute']} | {_n(r['map'], 1)} | {_n(r['delivery'], 3)} | {r['unset_perfusion'] or '—'} | "
             f"{_n(r['structural_perfusion'], 3)} | {_n(r['structural_value'], 3)} | {_yes(r['max_holds'])} |"
             for r in c["rows"]]
    return ("\n".join(rows) + f"\n\n- La señal de falla de aporte sube: {_yes(c['delivery_signal_rises'])}; la de "
            f"perfusión estructural sube: {_yes(c['perfusion_signal_rises'])}; UNSET sigue siendo cota inferior: "
            f"{_yes(c['unset_is_lower_bound'])}; sin regla de familia en la capa: {_yes(c['no_family_rule'])}.\n- Activa: "
            f"{_yes(c['active'])}; umbrales elegidos: {_yes(c['thresholds_selected'])}; transición terminal: "
            f"{_yes(c['terminal_transition'])}.\n- Cumple: {_yes(c['pass'])}.")


def render_secundario(data: dict) -> str:
    s = data["secondary"]
    rows = ["| Pérdida de P / min | Minuto | SpO2 | PAM | Gasto | FC | Lactato | D | Conciencia |",
            "|---|---|---|---|---|---|---|---|---|"]
    for loss, v in s["runs"].items():
        for m, x in _by_minute(v["at"]):
            rows.append(f"| {loss} | {m} | {_n(x['spo2'], 2)} | {_n(x['map'], 1)} | {_n(x['output_rel'], 3)} | "
                        f"{_n(x['hr'], 1)} | {_n(x['lactate'], 2)} | {_n(x['D'], 1)} | {x['consciousness_level']} |")
    return (_arrival_table(s["arrival"]) + f"\n\nLlegada coherente: {_yes(s['arrival']['pass'])}.\n\n" + "\n".join(rows)
            + f"\n\nHipoxemia sin hipotensión (sólo G): {_yes(s['hypoxaemia_without_hypotension'])}. "
              f"Cumple: {_yes(s['pass'])}.")


def render_observables(data: dict) -> str:
    out = []
    for name, o in data["observables"].items():
        rows = ["| Ítem | Autoral | Núcleo | Estado |", "|---|---|---|---|"]
        for k, v in o["rows"].items():
            core = v.get("core")
            core = "—" if core is None else (core if isinstance(core, (int, str)) else _n(core, 2))
            rows.append(f"| {k} | {v['authored']} | {core} | {v['status']} |")
        out.append(f"**`{name}`** (contradicciones: {', '.join(o['contradictions']) or 'ninguna'}):\n\n" + "\n".join(rows))
    return "\n\n".join(out)


def render_legado(data: dict) -> str:
    lc = data["legacy_comparison"]
    rows = ["| Minuto | Legado PA | Núcleo PA | Legado SpO2 | Núcleo SpO2 | Legado FC | Núcleo FC | Legado FR | Núcleo FR | "
            "Legado conciencia | Núcleo conciencia |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m, v in _by_minute(lc["rows"]):
        lg, co = v["legacy"], v["core"]
        rows.append(f"| {m} | {lg.get('sbp')}/{lg.get('dbp')} | {_n(co['sbp'], 0)}/{_n(co['dbp'], 0)} | {lg.get('spo2')} | "
                    f"{_n(co['spo2'], 1)} | {lg.get('hr')} | {_n(co['hr'], 1)} | {lg.get('respiratory_rate')} | "
                    f"{_n(co['rr'], 1)} | {lg.get('mental_status')} | {co['consciousness_level']} |")
    classes = "\n".join(f"- **{k}:** {v}" for k, v in lc["classes"].items())
    return ("\n".join(rows) + "\n\n" + classes + f"\n\nUsado para parámetros: {_yes(lc['used_for_parameters'])}.")


def render_no_regresion(data: dict) -> str:
    n = data["non_regression"]
    items = "\n".join(f"- {k}: {_yes(v)}" for k, v in n.items() if k not in ("common_files_untouched", "pass"))
    common = n["common_files_untouched"]
    return (items + f"\n- Archivos comunes en sus bytes de P2P-2: {sum(common.values())} de {len(common)}.\n"
            f"- Cumple: {_yes(n['pass'])}.")


def render_prueba(data: dict) -> str:
    p = data["proof"]
    return ("- Tuplas reconstruidas byte a byte como las dejó P2P-2: "
            + ", ".join(f"`{k}` {_yes(v)}" for k, v in p["proofs"].items())
            + f".\n- Archivos comunes sin cambios: {sum(p['common_untouched'].values())} de {len(p['common_untouched'])}."
              f"\n- Digest de congelamiento de P2P-2 reproducido por la vista: {_yes(p['p2p2_freeze_digest'])}; registro "
              f"de P2P-2 intacto: {_yes(p['p2p2_record'])}.")


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    rows = ["| Criterio | Cumple |", "|---|---|"] + [f"| {k} | {_yes(x)} |" for k, x in v["criteria"].items()]
    return ("\n".join(rows) + f"\n\n**Veredicto:** `{v['verdict']}`.\n\n**Recomendación:** "
            f"`{v['recommendation'] or '—'}`.")


def _rounded(value):
    if isinstance(value, float):
        return round(value, 3)
    if isinstance(value, dict):
        return {k: _rounded(v) for k, v in value.items()}
    return value


def render_brechas(data: dict) -> str:
    g = data["repeated_gaps"]
    lines = []
    for k, v in g.items():
        extra = {x: _rounded(y) for x, y in v.items() if x != "families"}
        lines.append(f"- **{k}** (familias: {', '.join(v['families'])})"
                     + (": " + json.dumps(extra, ensure_ascii=False) if extra else "."))
    return "\n".join(lines)


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the P2Q-2 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
