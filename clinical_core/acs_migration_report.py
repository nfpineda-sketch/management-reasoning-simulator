"""P2N-2 report: the generated blocks of docs/revision/P2N2_MIGRACION_CARDIOGENICA_ACS.md.

    python -m clinical_core.acs_migration_report --write <document> --data <the P2N-2 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("decisiones", "verdad", "mapeo", "bomba", "escritores", "llegada", "sin_tratar", "reperfusion", "fluidos",
         "colapso", "legado", "frontera", "gi", "veredicto", "recomendacion", "pedidas", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FROZEN = "(texto congelado, en inglés)"
CRITERIA_ES = {"arrival_representable": "la llegada autorizada es representable",
               "pump_through_P": "la falla de bomba entra por P", "ischaemia_writer_evolves_P": "la isquemia mueve P",
               "common_downstream": "Q, aporte y FC responden por la fisiología común",
               "d_lactate_coherent": "D y lactato coherentes", "reperfusion_targets_P": "la reperfusión actúa sobre P",
               "L_represents_congestion": "L representa la congestión", "no_core_retuning": "sin reajuste del núcleo",
               "gi_unchanged": "GI sin cambios", "respiratory_deferred": "extensión respiratoria diferida y explícita",
               "collapse_structural": "el colapso evalúa el estado (estructural)",
               "collapse_inactive": "el colapso sigue inactivo", "legacy_not_target": "el legado no es objetivo",
               "boundaries_hold": "fronteras familia / común"}
KEYS = ("P", "output_rel", "map", "delivery_index", "deficit", "D", "lactate", "hr", "L")


def _row(r: dict) -> str:
    return " | ".join(_n(r.get(k), 3 if k in ("P", "output_rel", "delivery_index", "deficit", "L") else 1) for k in KEYS)


def render_decisiones(data: dict) -> str:
    f = data["design"]["faculty"]
    lines = [f"- **{k}**: {v}" for k, v in f.items() if k != "deferred"]
    lines += [f"- **{k}** (diferido): {v}" for k, v in f["deferred"].items()]
    return f"Decisiones de la docencia {FROZEN}:\n\n" + "\n".join(lines)


def render_verdad(data: dict) -> str:
    t = data["arrival"]["truth"]
    return "\n".join([
        f"- **Caso:** `{data['design']['case']}`, leído del banco de casos (`clinical_cases.py`), por ruta.",
        f"- **Signos:** PA {t['sbp']}/{t['dbp']} (PAM {_n(data['arrival']['authored_map'])}), FC {t['hr']} "
        f"({t['rhythm']}), SpO2 {t['spo2']} % aire ambiente, FR {t['respiratory_rate']}, trabajo respiratorio "
        f"«{t['work_of_breathing']}», llenado capilar {t['crt_s']} s, extremidades «{t['extremities']}», "
        f"«{t['mental_status']}».",
        f"- **Laboratorio:** lactato {_n(t['lactate_mmol_l'])}, Hb {_n(t['hb_g_dl'])}, glucosa {t['glucose_mg_dl']}, "
        f"K {_n(t['potassium_mmol_l'])}, creatinina {_n(t['creatinine_mg_dl'])}; gases arteriales {t['abg_ph']} / "
        f"{t['abg_paco2']} / {t['abg_pao2']}, HCO3 {_n(t['abg_hco3'])} (el repositorio; no 18,4); troponina "
        f"{t['troponin_ng_l']}.",
        f"- **ECG y POCUS:** `{t['ecg_profile']}`; VI «{t['pocus_lv']}»; VCI «{t['pocus_ivc']}»; pulmones "
        f"«{t['pocus_lungs']}»; radiografía «{t['chest_xray']}».",
        f"- **Coronaria:** {json.dumps(t['coronary'], ensure_ascii=False)}; acciones esperadas "
        f"{', '.join(t['definitive_actions'])}."])


def render_mapeo(data: dict) -> str:
    rows = ["| Campo | Clase |", "|---|---|"] + [f"| {k} | {v} |" for k, v in data["arrival"]["classes"].items()]
    bands = ["", "| Banda | Inferior | Punto medio | Superior | Clase | Regla (congelada) |", "|---|---|---|---|---|---|"]
    for name, b in data["arrival"]["bands"].items():
        bands.append(f"| {name} | {_n(b['lower'], 3)} | {_n(b['midpoint'], 3)} | {_n(b['upper'], 3)} | "
                     f"{b['classification']} | {b['rule']} |")
    roles = ["", "Papel de cada canal a la llegada (verificado, no forzado):", ""] + [
        f"- **{k}**: {v}" for k, v in data["arrival"]["channel_roles"].items()]
    return "\n".join(rows + bands + roles)


def render_bomba(data: dict) -> str:
    p = data["pump"]
    d = data["lactate_d"]
    return "\n".join([f"- **{k}** {FROZEN}: {v}" for k, v in p.items()] + [
        "", f"- **D de llegada y lactato:** D con el lactato autorizado {_n(d['d_base'], 1)}; con el lactato al doble "
            f"{_n(d['d_other_lactate'], 1)}; la función de mapeo no recibe el lactato: "
            f"{_yes(d['mapping_takes_no_lactate'])}; pasa: {_yes(d['pass'])}."])


def render_escritores(data: dict) -> str:
    de = data["design"]
    return "\n".join([
        f"- **Pérdida isquémica de P** (FAMILY_CANDIDATE): {', '.join(_n(x * 60, 2) for x in de['loss_per_min'])} de "
        f"la bomba de llegada por hora; piso {_n(de['floor'], 2)}; referencia "
        f"{_n(de['reference_writer']['loss_per_min'] * 60, 2)} por hora.",
        f"- **Congestión en L** (FAMILY_CANDIDATE): ganancia = {', '.join(_n(x, 1) for x in de['congestion_shares'])} × "
        f"la escala común de congestión por precarga, por unidad de déficit de bomba (1 − P).",
        f"- **Reperfusión** (proceso logístico): señal en el minuto {de['reperfusion_minute']} (SYNTHETIC_ONLY: no hay "
        f"tiempo puerta-balón autorizado); recuperación de {', '.join(_n(x, 1) for x in de['recovery_shares'])} de lo "
        f"que la oclusión quitó, con tau {_n(de['recovery_tau_min'], 0)} min, nunca por encima de P = 1.",
        f"- **Contrafactual de fluidos:** {json.dumps(de['fluid'], ensure_ascii=False)}.",
        "", "Capa de observación (congelada, en inglés):", ""] +
        [f"- **{k}**: {v}" for k, v in de["observation_layer"].items()])


def render_llegada(data: dict) -> str:
    r = data["arrival"]["reconstruction"]
    row = data["arrival"]["row"]
    hr = data["arrival"]["hr_over_intrinsic_band"]
    lines = ["| Observable | Núcleo | Autorizado |", "|---|---|---|"]
    for k in ("hr", "sbp", "dbp", "map", "spo2", "rr", "lactate", "ph", "paco2", "mental_status"):
        core, authored = r[k]
        shown = _n(authored, 2) if isinstance(authored, float) else authored
        lines.append(f"| {k} | {core if isinstance(core, (int, str)) else _n(core, 2)} | {shown} |")
    lines += ["", "Canales: " + ", ".join(f"{k} {row[k] if isinstance(row[k], str) else _n(row[k], 3)}"
                                          for k in ("V", "T", "P", "R", "L", "G", "W", "D", "N")) + ".",
              f"FC de llegada con todas las bandas del mapeo en el mismo punto (no sólo la intrínseca): inferior "
              f"{_n(hr['lower'], 1)}, media {_n(hr['midpoint'], 1)}, "
              f"superior {_n(hr['upper'], 1)} (autorizada {r['hr'][1]}); déficit de llegada "
              f"{_n(data['arrival']['arrival_deficit'], 3)}, impulso simpático {_n(data['arrival']['arrival_drive'], 3)}."]
    return "\n".join(lines)


def render_sin_tratar(data: dict) -> str:
    u = data["untreated"]
    head = ["| Pérdida / h | Minuto | P | Q | PAM | Aporte | Déficit | D | Lactato | FC | L |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for loss, r in u["region"].items():
        for minute in ("0", "60", "120"):
            head.append(f"| {_n(float(loss) * 60, 2)} | {minute} | {_row(r['at'][minute])} |")
    lines = head + ["", "Direcciones en toda la región: " + "; ".join(f"{k} {_yes(v)}" for k, v in u["directions"].items())
                    + f"; la familia escribe sólo P y L: {_yes(u['family_writes_only_P_and_L'])}; lactato sólo del "
                      f"núcleo: {_yes(u['lactate_core_only'])}; FC por el impulso común: {_yes(u['hr_up_through_drive'])}.",
                    "", "L a los 120 min según la ganancia de congestión: " + ", ".join(
                        f"{k} × → {_n(v, 4)}" for k, v in u["congestion"].items()) + ".",
                    "Sensibilidad 1-D a la ganancia de tono (P, Q, PAM, T, D a los 120 min): " + "; ".join(
                        f"{k}: {_n(v['P'], 3)}, {_n(v['output_rel'], 3)}, {_n(v['map'], 1)}, {_n(v['T'], 3)}, "
                        f"{_n(v['D'], 1)}" for k, v in u["tone"].items()) + ".",
                    "Sensibilidad 1-D a k_LD (lactato a 0, 60, 120 min): " + "; ".join(
                        f"{k}: {', '.join(_n(x, 2) for x in v)}" for k, v in u["k_ld"].items()) + "."]
    return "\n".join(lines)


def render_reperfusion(data: dict) -> str:
    rp = data["reperfusion"]
    lines = ["| Curso | P | Q | PAM | Aporte | Déficit | D | Lactato | FC | L |", "|---|---|---|---|---|---|---|---|---|---|",
             f"| isquemia en curso | {_row(rp['ongoing'])} |"]
    for share, r in rp["shares"].items():
        lines.append(f"| reperfusión, recuperación {share} | {_row(r)} |")
    return "\n".join(lines + ["", f"A los 120 min, con reperfusión en el minuto {rp['reperfusion_minute']}: P mejor que con la "
                              f"isquemia en curso {_yes(rp['P_better_than_ongoing'])}; Q y déficit siguen por la "
                              f"fisiología común {_yes(rp['downstream_follow'])}; sólo P y L escritos "
                              f"{_yes(rp['only_P_and_L_written'])}."])


def render_fluidos(data: dict) -> str:
    f = data["fluid"]
    lines = ["| Estado | Q inicial | Q sin fluido | Q con fluido | Ganancia de Q | Ganancia de PAM | L con fluido |",
             "|---|---|---|---|---|---|---|"]
    for name, label in (("pump_failure", "falla de bomba"), ("preload_deficiency", "déficit de precarga")):
        r = f[name]
        lines.append(f"| {label} | {_n(r['output_start'], 3)} | {_n(r['output_without'], 3)} | {_n(r['output_with'], 3)} "
                     f"| {_n(r['output_gain'], 3)} | {_n(r['map_gain'], 1)} | {_n(r['L_with'], 4)} |")
    return "\n".join(lines + ["", f"El volumen mejora la precarga {_yes(f['volume_improves_preload'])}; da menos en la bomba "
                              f"débil {_yes(f['less_benefit_in_weak_pump'])}; no normaliza la falla de bomba "
                              f"{_yes(f['no_normalization_of_pump_failure'])}; la congestión queda visible en L "
                              f"{_yes(f['congestion_visible'])}."])


def render_colapso(data: dict) -> str:
    c = data["collapse"]
    rows = ["| Minuto | Aporte | Perfusión (UNSET) | Perfusión (rampa estructural) | Señal (máximo) | Máximo |",
            "|---|---|---|---|---|---|"]
    for r in c["rows"]:
        rows.append(f"| {r['minute']} | {_n(r['delivery'], 3)} | — | {_n(r['structural_perfusion'], 3)} | "
                    f"{_n(r['structural_value'], 3)} | {_yes(r['max_holds'])} |")
    return "\n".join(rows + ["", f"Con el mapeo de PAM UNSET la señal es una cota inferior "
                             f"{_yes(c['unset_is_lower_bound'])}; sin regla cardiogénica {_yes(c['no_family_rule'])}; "
                             f"activo {_yes(c['active'])}; umbrales elegidos {_yes(c['thresholds_selected'])}; "
                             f"transición terminal {_yes(c['terminal_transition'])}. M1: `{c['m1']}`; M2: `{c['m2']}`."])


def render_legado(data: dict) -> str:
    lc = data["legacy_comparison"]
    rows = ["| Minuto | PAS legado / núcleo | FC legado / núcleo | SpO2 legado / núcleo | Ritmo legado |", "|---|---|---|---|---|"]
    for m, r in sorted(lc["rows"].items(), key=lambda item: int(item[0])):
        lg, cr = r["legacy"], r["core"]
        rows.append(f"| {m} | {lg.get('sbp')} / {_n(cr.get('sbp'), 1)} | {lg.get('hr')} / {_n(cr.get('hr'), 1)} | "
                    f"{lg.get('spo2')} / {_n(cr.get('spo2'), 1)} | {lg.get('rhythm')} |")
    return "\n".join(rows + ["", f"Clasificación {FROZEN}:", ""] + [f"- **{k}**: {v}" for k, v in lc["classes"].items()]
                     + ["", f"Posible brecha del núcleo común: {', '.join(lc['possible_common_core_gap']) or 'ninguna'}; "
                            f"el legado usado para elegir parámetros: {_yes(lc['used_for_parameters'])}."])


def render_frontera(data: dict) -> str:
    b = data["boundary"]
    return "\n".join([f"- Canales que escriben los escritores de familia: {', '.join(b['writer_channels'])}.",
                      f"- Observables nombrados por los escritores: {', '.join(b['writer_never_names']) or 'ninguno'}; "
                      f"otras escrituras: {', '.join(b['writer_other_writes']) or 'ninguna'}.",
                      f"- Archivos comunes que nombran la familia: {', '.join(b['common_files_name_acs']) or 'ninguno'}.",
                      "- Clases: " + "; ".join(f"{k} {v}" for k, v in b["classes"].items()) + ".",
                      f"- Pasa: {_yes(b['pass'])}."])


def render_gi(data: dict) -> str:
    g, up = data["gi"], data["upstream"]
    return "\n".join([f"- **Árbol de P2M-2** (`6601fc7`), {up['files']} archivos: {_yes(up['unchanged'])} (los de fisiología "
                      f"y análisis cerrados byte a byte; dos archivos de tuplas sólo ganan entradas); ningún archivo común "
                      f"lee la familia: {_yes(not up['core_readers_of_family'])}.",
                      f"- **GI 57m sin tratar, {g['minutes']} min, con los escritores ACS inertes:** canales y estado "
                      f"auxiliar idénticos {_yes(g['identical'])}; escrituras de los inertes {g['inert_writes']}."])


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    rows = ["| Criterio | Cumple |", "|---|---|"] + [f"| {CRITERIA_ES[k]} | {_yes(ok)} |" for k, ok in v["checks"].items()]
    return "\n".join(rows + ["", f"**Veredicto:** `{v['verdict']}`."])


def render_recomendacion(data: dict) -> str:
    return f"**Recomendación:** `{data['recommendation']}`.\n\nRegla {FROZEN}: {data['design']['recommendation_rule']}"


def render_pedidas(data: dict) -> str:
    return f"Decisiones pedidas a la docencia {FROZEN}:\n\n" + "\n".join(
        f"{i}. {d}" for i, d in enumerate(data["decisions"], 1))


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return "\n".join([f"- Pasos del integrador: {e['integrator_steps']}; lecturas de estado fijo: {e['fixed_state_readings']}.",
                      f"- Trayectorias GI: {e['gi_trajectories']} ({e['gi_trajectory_purpose']}); minutos del motor "
                      f"heredado: {e['legacy_minutes']}.",
                      f"- Barrido cartesiano: {_yes(e['cartesian_sweep'])}.",
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
    parser.add_argument("--data", type=Path, required=True, help="the P2N-2 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
