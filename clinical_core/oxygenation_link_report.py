"""P2T-5 report: the generated blocks of docs/revision/P2T5_ENLACE_HIPOVENTILACION_OXIGENACION.md.

    python -m clinical_core.oxygenation_link_report --write <document> --data <the P2T-5 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("auditoria", "curva", "retenida", "sondas", "opioide", "asma", "tep", "edema", "fio2", "aguas_abajo",
         "parametros", "no_regresion", "prueba", "veredicto")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
CASES = ("asthma_49m", "asthma_24f")


def _pair(values, digits=2) -> str:
    return " → ".join(_n(v, digits) for v in values)


def render_auditoria(data: dict) -> str:
    a = data["audit"]
    return "\n".join([
        f"- Funciones nuevas en `derived.py`: {', '.join(f'`{f}`' for f in a['added'])}; cambiadas: "
        f"{', '.join(f'`{f}`' for f in a['changed'])}; campo nuevo del perfil: {', '.join(a['new_profile_fields'])}.",
        f"- El enlace lee: {', '.join(f'`{f}`' for f in a['link_reads'])}; no lee `oxygen_response_retained`, FiO2 ni G.",
        f"- Constantes numéricas: sólo las de la curva estándar y 0 / 1 "
        f"({'; '.join(f'`{k}` {v}' for k, v in a['constants'].items())}); sin Patm, PH2O ni altitud "
        f"({_yes(not a['absolute_alveolar_terms'])}).",
        f"- `_perfusion` llama al enlace: {_yes(a['perfusion_calls_link'])}. Pasa: {_yes(a['pass'])}."])


def render_curva(data: dict) -> str:
    c = data["odc"]
    pairs = c["authored_pairs"]
    worst = max(pairs, key=lambda k: abs(pairs[k]["odc"] - pairs[k]["spo2"]))
    return "\n".join([
        f"- Severinghaus (1979), sin parámetro ajustado: PaO2 → SpO2 "
        + ", ".join(f"{k} → {_n(v, 2)}" for k, v in c["forward"].items()) + ".",
        f"- Inversa exacta (Cardano): SpO2 → PaO2 " + ", ".join(f"{k} → {_n(v, 2)}" for k, v in c["inverse"].items())
        + f"; ida y vuelta, error máximo {c['round_trip_max_abs']:.2g}.",
        f"- Crecientes: directa {_yes(c['forward_increasing'])}, inversa {_yes(c['inverse_increasing'])}; límites: "
        f"PaO2 0 → {_n(c['limits']['pao2_0'], 0)}, PaO2 ∞ → {_n(c['limits']['pao2_inf'], 0)}, SpO2 0 → "
        f"{_n(c['limits']['spo2_0'], 0)}, SpO2 100 → {c['limits']['spo2_100']} (ODC_PLATEAU_IDENTIFIABILITY_DEBT).",
        f"- Pares autorados PaO2 / SpO2 de {len(pairs)} variantes: brecha máxima con la curva "
        f"{_n(c['authored_max_abs_gap'], 2)} puntos ({worst}); sólo coherencia, no se ajusta nada.",
        f"- Pasa: {_yes(c['pass'])}."])


def render_retenida(data: dict) -> str:
    r = data["retained"]
    return "\n".join([
        f"- retained(G) en G = −1, 0, 0,5, 1, 2: {', '.join(_n(v, 3) for v in r['values'])}; 1 hasta la llegada "
        f"{_yes(r['one_at_or_below_arrival'])}, no creciente {_yes(r['non_increasing'])}.",
        f"- Semántica: {r['semantics']}.",
        f"- Como transmisión alveolar: {r['as_alveolar_transmission']}; el enlace la lee: "
        f"{_yes(r['link_reads_retained'])}.", f"- Pasa: {_yes(r['pass'])}."])


def render_sondas(data: dict) -> str:
    p = data["probes"]
    o5 = p["O5"]["spo2_by_G"]
    lines = [f"- O1 (apagado = camino previo, el enlace nunca se llama): {_yes(p['O1']['pass'])} "
             f"({p['O1']['link_calls_with_r_none']} llamadas).",
             f"- O2 (llegada exacta con el enlace encendido; referencia = PaCO2 de llegada del modelo): "
             f"{_yes(p['O2']['pass'])}.",
             f"- O3 (G neutra, PaCO2 {_pair(p['O3']['paco2'])} → SpO2 {_pair(p['O3']['spo2'])}): {_yes(p['O3']['pass'])}.",
             f"- O4 (PaCO2 {_pair(p['O4']['paco2'])} → SpO2 {_pair(p['O4']['spo2'])}): {_yes(p['O4']['pass'])}.",
             f"- O5 (con el mismo cambio de PaCO2, peor G nunca sube la SpO2 final): {_yes(p['O5']['pass'])}; "
             f"{p['O5']['statement']}.", "",
             "| E relativa | G 0 | G 0,5 | G 1 | G 2 |", "|---|---|---|---|---|"]
    for f, row in o5.items():
        lines.append(f"| {f} | " + " | ".join(_n(v, 2) for v in row) + " |")
    lines += ["",
              f"- O6 (peor G nunca mejora, también analítico en ΔPaCO2 −10…30): {_yes(p['O6']['pass'])}.",
              f"- O7 (más FiO2 nunca empeora): {_yes(p['O7']['pass'])}.",
              f"- O8 (sin escritura hacia W, FR, mecánica, impulso ni carga ácida): {_yes(p['O8']['pass'])}; "
              f"{p['O8']['note']}.",
              f"- O9 (G no cambia la PaCO2): {_yes(p['O9']['pass'])}.",
              f"- O10 (sólo SpO2 y lo que la lee): {_yes(p['O10']['pass'])}; derivados movidos "
              f"{', '.join(p['O10']['derive_fields_moved'])}; estado movido "
              f"{', '.join(p['O10']['course_state_fields_moved']) or 'nada'}; {p['O10']['routes']}.",
              f"- O11 (PaO2 latente, sin estado): {_yes(p['O11']['pass'])}.",
              f"- Guardas: mecánica apagada rechazada {_yes(p['guards']['mechanics_off_refused'])}, perfil TEP "
              f"comprometido rechazado {_yes(p['guards']['committed_pe_refused'])}, impulso hipoxémico rechazado "
              f"{_yes(p['guards']['hypoxaemic_refused'])}, R no positivo rechazado "
              f"{_yes(p['guards']['non_positive_refused'])}, apnea sin resolver (APNOEA_BOUNDARY_UNRESOLVED) "
              f"{_yes(p['guards']['apnoea_unresolved'])}."]
    return "\n".join(lines)


def render_opioide(data: dict) -> str:
    o = data["opioid"]
    d, r = o["rows"]["depressed"], o["rows"]["restored"]
    i = o["integrated_improvement"]
    return "\n".join([
        f"- {o['label']}, sintético (disponibilidad central {d['availability']} frente a {r['availability']}, G "
        f"{_n(d['G'], 0)}): FR {_n(d['rr'], 1)} frente a {_n(r['rr'], 1)}, W {_n(d['W'], 3)} frente a {_n(r['W'], 3)}, "
        f"PaCO2 {_n(d['paco2'], 1)} frente a {_n(r['paco2'], 1)}, SpO2 {_n(d['spo2'], 2)} frente a {_n(r['spo2'], 2)}.",
        f"- Mejora integrada en el núcleo (alivio mecánico): PaCO2 {_pair(i['paco2'])}, SpO2 {_pair(i['spo2'])}.",
        f"- {o['gap']}.", f"- Pasa: {_yes(o['pass'])}."])


def render_asma(data: dict) -> str:
    a = data["asthma"]
    lines = []
    for case in CASES:
        c = a[case]
        o, s, r = c["obstruction"], c["serial_with_direct_G"], c["relief"]
        lines.append(f"- **{case}:** llegada exacta {_yes(c['arrival_exact'])}; obstrucción sin G: PaCO2 {_pair(o['paco2'])}, "
                     f"SpO2 con enlace {_pair(o['spo2_link_on'])} (sin enlace {_pair(o['spo2_link_off'])}); con G directa "
                     f"sintética además: {_n(s['both'], 2)} (sólo G {_n(s['g_only'], 2)}, sólo mecánica "
                     f"{_n(s['mechanics_only'], 2)}); composición serial {_yes(c['serial_composition'])}; alivio: PaCO2 "
                     f"{_pair(r['paco2'])}, SpO2 {_pair(r['spo2'])}.")
    lines.append(f"- Pasa: {_yes(a['pass'])}.")
    return "\n".join(lines)


def render_tep(data: dict) -> str:
    t = data["pe"]
    e = t["paco2_end"]
    return "\n".join([
        f"- {t['label']}; el perfil comprometido (mecánica apagada) rechaza el enlace: "
        f"{_yes(t['committed_mechanics_off_refused'])}.",
        f"- G {_pair(t['G'])}; G no mueve la PaCO2 en ningún estado: {_yes(t['same_state_g_moves_no_paco2'])}; "
        f"composición serial {_yes(t['serial_composition'])}.",
        f"- SpO2 con enlace {_pair(t['spo2_on'])}, sin enlace {_pair(t['spo2_off'])}; curso sin G con enlace "
        f"{_n(t['spo2_plain_course_on'], 2)}.",
        f"- PaCO2 al minuto final: G con enlace {_n(e['G_link_on'], 2)}, G sin enlace {_n(e['G_link_off'], 2)}, sin G con "
        f"enlace {_n(e['plain_link_on'], 2)}, sin G sin enlace {_n(e['plain_link_off'], 2)}; {t['drift']}; ruta "
        f"indirecta existente: {t['existing_indirect_route']} (compensadora {_yes(t['indirect_route_compensatory'])}).",
        f"- Pasa: {_yes(t['pass'])}."])


def render_edema(data: dict) -> str:
    e = data["edema"]
    lo, mo, bo = e["l_only"], e["mechanics_only"], e["both"]
    return "\n".join([
        f"- {e['label']}; llegada {_n(e['arrival'], 1)}; curso sin escritores: PaCO2 {_n(e['plain']['paco2'], 2)}, "
        f"SpO2 {_n(e['plain']['spo2'], 2)}.",
        f"- Sólo L: L {_n(lo['L'], 3)}, G {_n(lo['G'], 3)}, PaCO2 {_pair(lo['paco2'])} (igual al curso sin escritores "
        f"{_yes(e['l_moves_no_paco2'])}), SpO2 {_n(lo['spo2'], 2)}.",
        f"- Sólo mecánica: L y G 0 {_yes(e['mechanics_moves_no_g'])}, PaCO2 {_pair(mo['paco2'])}, SpO2 {_n(mo['spo2'], 2)}.",
        f"- Ambos: L {_n(bo['L'], 3)}, G {_n(bo['G'], 3)}, PaCO2 {_n(bo['paco2'], 2)}, SpO2 {_n(bo['spo2'], 2)}; "
        f"composición serial sin doble conteo {_yes(e['serial_composition'])}.", f"- Pasa: {_yes(e['pass'])}."])


def render_fio2(data: dict) -> str:
    f = data["fio2"]
    lines = ["| FiO2 | SpO2 base | SpO2 hipoventilando (E × 0,7) | Caída |", "|---|---|---|---|"]
    for k, row in f["rows"].items():
        lines.append(f"| {k} | {_n(row['spo2_base_state'], 2)} | {_n(row['spo2_hypoventilating'], 2)} | "
                     f"{_n(row['drop'], 2)} |")
    lines += ["", f"- {f['status']}; regla de FiO2 intacta: {_yes(f['fio2_rule_unchanged'])}.", f"- {f['plateau']}.",
              f"- Pasa: {_yes(f['pass'])}."]
    return "\n".join(lines)


def render_aguas_abajo(data: dict) -> str:
    d = data["downstream"]
    lines = []
    for name, label in (("probe", "Paciente de sonda"), ("pe", "TEP (mecánica encendida)")):
        r = d["rows"][name]
        lines.append(f"- {label}, empeoramiento mecánico sintético {r['factor_per_min']}/min por 60 min (PaCO2 "
                     f"{_n(r['paco2'], 1)}), con el enlace frente a sin él: SpO2 {_n(r['spo2'][0], 2)} frente a "
                     f"{_n(r['spo2'][1], 2)}; DO2 relativa {_n(r['delivery'][0], 3)} frente a {_n(r['delivery'][1], 3)}; D "
                     f"{_n(r['D'][0], 3)} frente a {_n(r['D'][1], 3)}; lactato {_n(r['lactate'][0], 3)} frente a "
                     f"{_n(r['lactate'][1], 3)}; FC {_n(r['hr'][0], 1)} frente a {_n(r['hr'][1], 1)}; conciencia "
                     f"{r['consciousness'][0]} frente a {r['consciousness'][1]}.")
    lines += [f"- FC: {d['hr_route']}.", f"- Conciencia: {'; '.join(d['consciousness_status'])}.",
              f"- Ácido-base: {d['acid_base']}.", f"- Bucle hipoxémico: {d['hypoxaemic_loop']}.",
              f"- Pasa: {_yes(d['pass'])}."]
    return "\n".join(lines)


def render_parametros(data: dict) -> str:
    p = data["parameters"]
    return "\n".join([
        f"- R en los perfiles comprometidos: None en todos {_yes(all(p['committed_r_none'].values()))} "
        f"({', '.join(p['committed_r_none'])}).",
        f"- Registro: {p['registry'][0]} — {p['registry'][1]}.",
        f"- R sintético {p['synthetic_r']['value']} sólo como {p['synthetic_r']['label']}; campos nuevos del perfil: "
        f"{', '.join(p['new_profile_fields'])}.",
        f"- Siguen sin valor: {', '.join(p['unset'])}.", f"- Pasa: {_yes(p['pass'])}."])


def render_no_regresion(data: dict) -> str:
    n = data["non_regression"]
    return "\n".join([f"- Registro de P2T-3 reproducido sobre su árbol: {_yes(n['p2t3_record_reproduced_on_its_tree'])} "
                      f"(anida P2T-1A, P2T-1, P2S-3, P2S-2 y, por ellos, GI, SCA, edema, TEP y P2P-2); intacto "
                      f"{_yes(n['p2t3_record_untouched'])}; su veredicto {n['p2t3_verdict']}.",
                      f"- Pasa: {_yes(n['pass'])}."])


def render_prueba(data: dict) -> str:
    p = data["proof"]
    return "\n".join([f"- Archivos revertidos a los de P2T-3: {', '.join(f'`{k}` {_yes(v)}' for k, v in p['proofs'].items())}.",
                      f"- Archivos comunes fijados por hash: {len(p['common_untouched'])}, intactos "
                      f"{_yes(all(p['common_untouched'].values()))}.",
                      f"- Vista de P2T-3: digest {_yes(p['p2t3_freeze_digest'])}, su prueba {_yes(p['p2t3_proof'])}, "
                      f"registro {_yes(p['p2t3_record'])}."])


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
    parser.add_argument("--data", type=Path, required=True, help="the P2T-5 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
