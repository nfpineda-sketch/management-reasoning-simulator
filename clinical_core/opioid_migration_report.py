"""P2U-1 report: the generated blocks of docs/revision/P2U1_OPIOIDE_SOMBRA.md.

    python -m clinical_core.opioid_migration_report --write <document> --data <the P2U-1 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("verdad", "canales", "llegada", "interfaz", "escritores", "sondas", "contraste", "recurrencia", "colapso",
         "fc", "conciencia", "oxigeno", "acido", "legado", "no_regresion", "prueba", "veredicto")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
CASES = ("opioid_35m", "opioid_67f")
POINTS = ("lower", "midpoint", "upper")


def _pair(values, digits=2) -> str:
    return " → ".join(_n(v, digits) for v in values)


def render_verdad(data: dict) -> str:
    t = data["case_truth"]
    lines = []
    for case in CASES:
        a = t[case]["authored"]
        lines.append(f"- **{case}:** PA {a['sbp']}/{a['dbp']} (PAM {_n(t[case]['map'], 1)}), FC {a['hr']}, SpO2 "
                     f"{a['spo2']} %, FR {a['respiratory_rate']}, WOB «{a['work_of_breathing']}», {a['mental_status']}; "
                     f"gasometría arterial pH {a['abg_ph']}, PaCO2 {a['abg_paco2']}, PaO2 {a['abg_pao2']}, HCO3 "
                     f"{a['abg_hco3']} (FiO2 {a['abg_fio2_percent']} %); lactato {a['lactate_mmol_l']}; glucosa "
                     f"{a['glucose_mg_dl']}; Hb {a['hb_g_dl']}; creatinina {a['creatinine_mg_dl']}; {a['rhythm']}; "
                     f"temperatura {a['temperature_c']} °C; pulmón: {t[case]['lungs'][0]}; radiografía: "
                     f"{t[case]['lungs'][1]}; examen respiratorio: «{t[case]['respiratory_exam']}»; neurológico: "
                     f"«{t[case]['neurological_exam']}»; acciones definitivas: {', '.join(t[case]['definitive_actions'])}; "
                     f"riesgo de recurrencia {_yes(bool(t[case]['recurrence_risk']))}.")
    lines += [f"- Oxígeno: {t[CASES[0]]['oxygen_authored']}.",
              f"- Observaciones posteriores: {t[CASES[0]]['later_observations']}.",
              f"- Clases: {'; '.join(f'{k} = {v}' for k, v in t['classes'].items())}."]
    return "\n".join(lines)


def render_canales(data: dict) -> str:
    c = data["channel_map"]
    lines = [f"- {name}: {role}" for name, role in c["roles"].items()]
    lines += ["", "| Caso | V | T | P | L | G | D | N | Distrés | Disponibilidad | Eficiencia |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for case in CASES:
        r = c["arrival_channels"][case]
        lines.append(f"| {case} | {_n(r['V'], 1)} | {_n(r['T'], 1)} | {_n(r['P'], 1)} | {_n(r['L'], 1)} | "
                     f"{_n(r['G'], 1)} | {_n(r['D'], 1)} | {_n(r['N'], 1)} | {_n(r['distress'], 1)} | "
                     f"{_n(r['availability'], 4)} | {_n(r['mechanics'], 4)} |")
    lines.append(f"\n- Pasa: {_yes(c['pass'])}.")
    return "\n".join(lines)


def render_llegada(data: dict) -> str:
    r = data["arrival_region"]
    lines = ["| Caso | FR intrínseca | Disponibilidad | Eficiencia | FR | PaCO2 | pH | SpO2 | FC | PaCO2 si se restaura |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for case in CASES:
        for point in POINTS:
            p = r[case]["points"][point]
            lines.append(f"| {case} | {_n(p['intrinsic_rr'], 0)} | {_n(p['availability'], 4)} | "
                         f"{_n(p['efficiency'], 4)} | {_n(p['rr'], 2)} | {_n(p['paco2'], 2)} | {_n(p['ph'], 3)} | "
                         f"{_n(p['spo2'], 1)} | {_n(p['hr'], 1)} | {_n(p['restored_paco2'], 1)} |")
    lines.append("")
    for case in CASES:
        a = r[case]["authored"]
        lines.append(f"- **{case}:** autoral FR {_n(a['rr'], 0)}, PaCO2 {_n(a['paco2'], 0)}, pH {a['ph']}, SpO2 "
                     f"{_n(a['spo2'], 0)}, FC {_n(a['hr'], 0)}; reproducción exacta en el núcleo vivo "
                     f"{_yes(r[case]['exact'])}; producto FR × PaCO2 {_n(r[case]['rr_paco2_product'], 0)} "
                     f"(FR intrínseca / eficiencia = {_n(r[case]['intrinsic_over_efficiency'], 2)}); banda de FC del "
                     f"modelo {_n(r[case]['hr_band'][0], 1)}–{_n(r[case]['hr_band'][1], 1)}, FC autoral dentro "
                     f"{_yes(r[case]['authored_hr_in_band'])}.")
    t = r["tension"]
    lines += ["", f"- **{t['label']}:** {t['statement']}. Decisión: {t['decision']}.", f"- Pasa: {_yes(r['pass'])}."]
    return "\n".join(lines)


def render_interfaz(data: dict) -> str:
    i = data["interface"]
    lines = [f"- Campo auxiliar nuevo: {', '.join(i['aux_fields_new'])}; ancla de llegada nueva: "
             f"{', '.join(i['anchor_fields_new'])}; campos del perfil nuevos: {i['profile_fields_new'] or 'ninguno'}.",
             f"- FR: {i['rr_formula']}.",
             f"- Lectores de la disponibilidad: {', '.join(f'`{r}`' for r in i['availability_readers'])}."]
    for relative, f in i["functions"].items():
        lines.append(f"- `{relative}`: funciones nuevas {', '.join(f'`{x}`' for x in f['added']) or 'ninguna'}; "
                     f"cambiadas {', '.join(f'`{x}`' for x in f['changed']) or 'ninguna'}.")
    lines.append(f"- Pasa: {_yes(i['pass'])}.")
    return "\n".join(lines)


def render_escritores(data: dict) -> str:
    w = data["probes"]["U11"]["writer_audit"]
    return "\n".join([
        f"- Construye: {', '.join(f'`{x}`' for x in w['constructed'])}; única clave de contribución: "
        f"{', '.join(w['contribution_keywords'])}; nombres prohibidos encontrados: "
        f"{w['forbidden_names'] or 'ninguno'}.",
        f"- Lee del estado: {', '.join(w['reads'])}; tipos registrados: {', '.join(w['registered'])}.",
        f"- Pasa: {_yes(w['pass'])}."])


def render_sondas(data: dict) -> str:
    p = data["probes"]
    lines = []
    for case in CASES:
        u, un_, na = p[case]["U"], p[case]["untreated"], p[case]["naloxone"]
        lines.append(f"- **{case}:** U1 {_yes(u['U1'])}, U2 {_yes(u['U2'])}, U3 {_yes(u['U3'])}, U4 {_yes(u['U4'])}, "
                     f"U5 {_yes(u['U5'])}, U6 {_yes(u['U6'])}, U7 {_yes(u['U7'])}, U8 {_yes(u['U8'])}, "
                     f"U9 {_yes(u['U9'])}; sólo escribe disponibilidad {_yes(p[case]['records_only_availability'])}.")
        lines.append(f"  - Sin tratar (60 min): disponibilidad {_pair(un_['availability'], 4)}, FR "
                     f"{_pair(un_['rr'])}, W {_pair(un_['W'], 3)}, PaCO2 {_pair(un_['paco2'], 1)}, SpO2 "
                     f"{_pair(un_['spo2'])}, pH {_pair(un_['ph'], 3)}, DO2 relativa {_pair(un_['delivery'], 3)}.")
        lines.append(f"  - Con antagonista: disponibilidad {_pair(na['availability'], 4)}, FR {_pair(na['rr'])}, W "
                     f"{_pair(na['W'], 3)}, PaCO2 {_pair(na['paco2'], 1)}, SpO2 {_pair(na['spo2'])}, pH "
                     f"{_pair(na['ph'], 3)}, FC {_pair(na['hr'], 1)}, conciencia "
                     f"{na['consciousness'][0]} → {na['consciousness'][1]}.")
    lines += [f"- U10 (sin ecuación de oxígeno propia de la familia ni término opioide en el núcleo): "
              f"{_yes(p['U10']['pass'])}; ruta de oxígeno: {p['U10']['oxygen_path']}.",
              f"- U11 (sin escritura directa de observables): {_yes(p['U11']['pass'])}.",
              f"- U12: {p['U12']['note']}.", f"- Pasa: {_yes(p['pass'])}."]
    return "\n".join(lines)


def render_contraste(data: dict) -> str:
    c = data["contrast"]
    lines = ["| FR intrínseca | Disponibilidad 35m | Disponibilidad 67f | Eficiencia 35m | Eficiencia 67f |",
             "|---|---|---|---|---|"]
    for point in POINTS:
        r = c["rows"][point]
        lines.append(f"| {point} | {_n(r['availability'][0], 4)} | {_n(r['availability'][1], 4)} | "
                     f"{_n(r['efficiency'][0], 4)} | {_n(r['efficiency'][1], 4)} |")
    lines += ["", f"- {c['statement']}.", f"- Pasa: {_yes(c['pass'])}."]
    return "\n".join(lines)


def render_recurrencia(data: dict) -> str:
    r = data["recurrence"]
    rows = [("llegada", r["arrival"]), ("al parar el antagonista", r["at_antagonist_stop"]), ("al final", r["end"])]
    lines = [f"- {label} (minuto {row['minute']}): disponibilidad {_n(row['availability'], 4)}, FR {_n(row['rr'], 2)}, "
             f"PaCO2 {_n(row['paco2'], 1)}, SpO2 {_n(row['spo2'], 2)}, pH {_n(row['ph'], 3)}." for label, row in rows]
    lines += [f"- {r['kinetics']}.", f"- Pasa: {_yes(r['pass'])}."]
    return "\n".join(lines)


def render_colapso(data: dict) -> str:
    c = data["collapse"]
    return "\n".join([
        f"- Empeoramiento severo sintético (120 min): DO2 relativa {_pair(c['delivery'], 3)}, SpO2 {_pair(c['spo2'])}, "
        f"D {_pair(c['D'], 3)}, PaCO2 {_pair(c['paco2'], 1)}.",
        f"- Sin regla de colapso propia de la familia: {_yes(c['no_opioid_collapse_rule'])}; {c['status']}.",
        f"- Pasa: {_yes(c['pass'])}."])


def render_fc(data: dict) -> str:
    h = data["heart_rate"]
    lines = [f"- **{case}:** FC autoral {_n(h[case]['authored'], 0)}, banda del modelo "
             f"{_n(h[case]['model_band'][0], 1)}–{_n(h[case]['model_band'][1], 1)}, dentro "
             f"{_yes(h[case]['within'])}, residual {_n(h[case]['residual_bpm'], 2)} lpm." for case in CASES]
    lines += [f"- {h['gap']}.", f"- Término de FC propio de la familia: {_yes(h['opioid_hr_term'])}; {h['rule']}.",
              f"- Pasa: {_yes(h['pass'])}."]
    return "\n".join(lines)


def render_conciencia(data: dict) -> str:
    c = data["consciousness"]
    lines = [f"- **{case}:** autoral «{c[case]['authored']}» (nivel {c[case]['arrival_level']}); niveles con "
             f"antagonista {c[case]['levels_under_naloxone']}; {c[case]['reading']}." for case in CASES]
    lines += [f"- N escrito: {_yes(c['N_written'])}.", f"- Pasa: {_yes(c['pass'])}."]
    return "\n".join(lines)


def render_oxigeno(data: dict) -> str:
    o = data["oxygen"]
    return "\n".join([
        f"- Llegada: aire ambiente {_n(o['room_air'], 2)}, FiO2 0,4 {_n(o['fio2_0.4'], 2)}.",
        f"- Hipoventilando (60 min): aire ambiente {_n(o['hypoventilating_room_air'], 2)}, FiO2 0,4 "
        f"{_n(o['hypoventilating_fio2_0.4'], 2)}; la FiO2 no mueve la PaCO2 {_yes(o['paco2_unchanged_by_fio2'])}.",
        f"- {o['rule']}; {o['debt']}.", f"- Pasa: {_yes(o['pass'])}."])


def render_acido(data: dict) -> str:
    a = data["acid_base"]
    lines = [f"- **{case}:** con antagonista, pH {_pair(a[case]['ph'], 3)}, PaCO2 {_pair(a[case]['paco2'], 1)}, HCO3 "
             f"{_pair(a[case]['hco3'], 2)}, carga ácida {_pair(a[case]['burden'], 3)}." for case in CASES]
    lines += [f"- {a['rule']}.", f"- Pasa: {_yes(a['pass'])}."]
    return "\n".join(lines)


def render_legado(data: dict) -> str:
    g = data["legacy"]
    lines = [f"- Encontrado en el motor heredado: {', '.join(f'{k} {_yes(v)}' for k, v in g['found'].items())} "
             f"({g['classification']})."]
    lines += [f"- {k}: {v}" for k, v in g["differences"].items()]
    lines += [f"- Ajustado al legado: {_yes(g['fitted'])}. Pasa: {_yes(g['pass'])}."]
    return "\n".join(lines)


def render_no_regresion(data: dict) -> str:
    n = data["non_regression"]
    return "\n".join([
        f"- Registro de P2T-5 reproducido sobre su árbol: {_yes(n['p2t5_record_reproduced_on_its_tree'])} (anida P2T-3, "
        f"P2T-1A, P2T-1, P2S-3, P2S-2 y, por ellos, TEP, edema, SCA y GI); intacto {_yes(n['p2t5_record_untouched'])}; "
        f"su veredicto {n['p2t5_verdict']}.",
        f"- Disponibilidad de llegada 1 en los perfiles comprometidos: {_yes(n['committed_arrival_availability_1'])}.",
        f"- Pasa: {_yes(n['pass'])}."])


def render_prueba(data: dict) -> str:
    p = data["proof"]
    return "\n".join([
        f"- Archivos revertidos a los de P2T-5: {', '.join(f'`{k}` {_yes(v)}' for k, v in p['proofs'].items())}.",
        f"- Archivos comunes fijados por hash: {len(p['common_untouched'])}, intactos "
        f"{_yes(all(p['common_untouched'].values()))}.",
        f"- Vista de P2T-5: digest {_yes(p['p2t5_freeze_digest'])}, su prueba {_yes(p['p2t5_proof'])}, registro "
        f"{_yes(p['p2t5_record'])}."])


def render_veredicto(data: dict) -> str:
    v = data["readiness"]
    lines = [f"- {_yes(c['holds'])} — {c['criterion']}" for c in v["criteria"]]
    lines += ["", f"**Veredicto: {v['verdict']}**"]
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
    parser.add_argument("--data", type=Path, required=True, help="the P2U-1 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
