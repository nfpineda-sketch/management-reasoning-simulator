"""P2T-3 report: the generated blocks of docs/revision/P2T3_ASMA_DISTRES_SOMBRA.md.

    python -m clinical_core.asthma_distress_migration_report --write <document> --data <the P2T-3 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("verdad", "region", "testigos", "cursos", "escala", "ortogonalidad", "familias", "parametros", "no_regresion",
         "prueba", "veredicto")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
CASES = ("asthma_49m", "asthma_24f")


def _iv(pair, digits=3) -> str:
    return f"[{_n(pair[0], digits)}; {_n(pair[1], digits)}]"


def render_verdad(data: dict) -> str:
    t = data["case_truth"]
    lines = []
    for case in CASES:
        a = t[case]["authored"]
        lines.append(f"- **{case}:** PA {a['sbp']}/{a['dbp']} (PAM {_n(t[case]['map'], 1)}), FC {a['hr']}, SpO2 {a['spo2']} %, "
                     f"FR {a['respiratory_rate']}, WOB «{a['work_of_breathing']}», {a['mental_status']}; gasometría "
                     f"arterial pH {a['abg_ph']}, PaCO2 {a['abg_paco2']}, PaO2 {a['abg_pao2']}, HCO3 {a['abg_hco3']} "
                     f"(FiO2 {a['abg_fio2_percent']} %); venosa pH {a['vbg_ph']}, PCO2 {a['vbg_pco2']}; lactato "
                     f"{a['lactate_mmol_l']}; glucosa {a['glucose_mg_dl']}; flujo espiratorio: {t[case]['peak_flow']}; "
                     f"examen: «{a['respiratory_exam']}»; POCUS: {a['pocus_lungs']}; radiografía: {a['chest_xray']}; "
                     f"β-agonista previo autorado {_yes(t[case]['prehospital_beta_agonist'])}.")
    lines += [f"- Después de la llegada: {t[CASES[0]]['later']}.",
              f"- Igual a la verdad que leyó P2S-3: {_yes(t['same_as_p2s3'])}."]
    return "\n".join(lines)


def render_region(data: dict) -> str:
    r = data["region"]
    lines = [f"- Estado: **{r['status']}**; no vacía en cada k llevado: {_yes(r['every_carried_k'])}; monótona en k: "
             f"{_yes(r['monotone_in_k'])}.", "",
             "| k | ρ permitido (k) | Cota inferior | Cota superior | x(49m) = g_FR·d(49m) en ρ medio | d(24f) en ρ medio "
             "| E(49m) | E(24f) |", "|---|---|---|---|---|---|---|---|"]
    for k, pt in r["points"].items():
        a = pt["at"]["mid"]["asthma"]
        lines.append(f"| {_n(float(k), 3)} | {_iv(pt['effective'], 4)} | {pt['bounds']['binding']['lo']} | "
                     f"{pt['bounds']['binding']['hi']} | {_iv(a['x49'], 2)} | {_iv(a['d24'])} | {_iv(a['E49'])} | "
                     f"{_iv(a['E24'])} |")
    lines += ["", f"- Intersección robusta en k ({r['diagnostic_label']}): {_iv(r['diagnostic_robust_intersection'], 4)}."]
    return "\n".join(lines)


def render_testigos(data: dict) -> str:
    w = data["witnesses"]
    lines = [f"- {w['label']}, regla predeclarada {w['rule']}, aplicada después de probar la región no vacía.", "",
             "| Testigo | k | ρ | g_FR·d(49m) | d(24f) | Caso | FR | PaCO2 | pH | W | E | FC (FC intrínseca 60) | FC autoral |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for label in ("LOW", "MID", "HIGH"):
        x = w[label]
        for case in CASES:
            c = x["cases"][case]
            lines.append(f"| {label} | {_n(x['k'], 3)} | {_n(x['rho'], 4)} | {_n(x['g_rr'], 2)} | {_n(x['d24'], 3)} | "
                         f"{case} | {_n(c['rr'], 2)} | {_n(c['paco2'], 2)} | {_n(c['ph'], 3)} | {_n(c['W'], 3)} | "
                         f"{_n(c['mechanics_efficiency'], 3)} | {_n(c['hr'], 1)} | {_n(c['authored']['hr'], 0)} |")
    lines += ["", f"- Todos soportados por el núcleo vivo, y la misma llegada con la mecánica apagada queda rechazada "
              f"(M1): {_yes(w['pass'])}."]
    return "\n".join(lines)


def render_cursos(data: dict) -> str:
    c = data["courses"]
    lines = []
    for case in CASES:
        u = c[case]
        lines.append(f"- **{case}:** obstrucción sin tratar: E baja {_yes(u['untreated']['E_down'])}, PaCO2 sube "
                     f"{_yes(u['untreated']['paco2_up'])}, FR y distrés intactos "
                     f"{_yes(u['untreated']['rr_unchanged_by_obstruction'] and u['untreated']['distress_unchanged_by_obstruction'])}, "
                     f"la familia sólo escribe mecánica {_yes(u['untreated']['family_writes_mechanics_only'])}; alivio "
                     f"mecánico: W sube y PaCO2 baja {_yes(u['mechanics_relief']['W_up_paco2_down'])} sin tocar distrés, FR "
                     f"ni FC {_yes(u['mechanics_relief']['distress_rr_hr_unchanged'])}; alivio del distrés (sintético): "
                     f"objetivo exacto {_yes(u['distress_relief']['exact_target'])}, FR y FC bajan "
                     f"{_yes(u['distress_relief']['rr_down'] and u['distress_relief']['hr_down'])}, mecánica intacta "
                     f"{_yes(u['distress_relief']['mechanics_unchanged'])}; G directa (sintética): SpO2 baja "
                     f"{_yes(u['direct_g']['spo2_down'])}, L 0 {_yes(u['direct_g']['L_zero'])}.")
    lines.append(f"- Pasa: {_yes(c['pass'])}.")
    return "\n".join(lines)


def render_escala(data: dict) -> str:
    s = data["scale_invariance"]
    return "\n".join([f"- {s['statement']}.",
                      f"- Diferencia máxima con λ potencia de 2: {s['powers_of_two_max_abs_difference']}; con λ = 10: "
                      f"{s['other_max_abs_difference']:.3g} (cota de redondeo {s['roundoff_bound']:.3g}).",
                      f"- Pasa: {_yes(s['pass'])}."])


def render_ortogonalidad(data: dict) -> str:
    o = data["orthogonality"]
    fe, fd = o["secondary_distress_at_fixed_mechanics"], o["secondary_mechanics_at_fixed_distress"]
    return "\n".join([
        f"- 24f con la mecánica fija (E {_n(fe['E'], 3)}): el distrés (x) cambia con k: "
        + ", ".join(f"k {_n(float(k), 3)} → {_n(v, 2)}" for k, v in fe["x_by_k"].items()) + ".",
        f"- 24f con el distrés fijo (x {_n(fd['x'], 1)}): la mecánica cambia: "
        + ", ".join(f"k {_n(float(k), 3)} → E {_n(v, 3)}" for k, v in fd["E_by_k"].items()) + ".",
        f"- Testigo medio: 49m E {_n(o['witness']['asthma_49m']['E'], 3)} y d 1; 24f E "
        f"{_n(o['witness']['asthma_24f']['E'], 3)} y d {_n(o['witness']['asthma_24f']['d'], 3)}: difieren en ambas "
        f"{_yes(o['both_differ'])}.",
        f"- La composición del impulso no lee la mecánica: {_yes(not o['composition_reads_mechanics'])}; ortogonalidad de "
        f"P2T-1 en vivo {_yes(o['p2t1_orthogonality_live'])}; {o['coupling']}.", f"- Pasa: {_yes(o['pass'])}."])


def render_familias(data: dict) -> str:
    cf = data["cross_family"]
    lines = ["| k | Edema 58m | TEP 61m | TEP 33f (cota sup.) | Opioides (d 0) | GI (d 0) | Anafilaxia forzada | "
             "Residual SCA explicado (mín.) |", "|---|---|---|---|---|---|---|---|"]
    for k, row in cf.items():
        if k == "pass":
            continue
        lines.append(f"| {_n(float(k), 3)} | {_yes(row['pulmonary_edema_58m']['compatible'])} | "
                     f"{_yes(row['pulmonary_embolism_61m']['compatible'])} | {_yes(row['pulmonary_embolism_33f']['compatible'])} | "
                     f"{_yes(row['opioid_35m']['distress_zero_admissible'] and row['opioid_67f']['distress_zero_admissible'])} | "
                     f"{_yes(row['gi_bleed_57m']['distress_zero_admissible'] and row['gi_bleed_72f']['distress_zero_admissible'])} | "
                     f"{_yes(row['anaphylaxis_29f']['forced_overprediction'] or row['anaphylaxis_63m_betablocked']['forced_overprediction'])} | "
                     f"{_n(100 * row['acs_70f_left_main']['share_of_residual_at_least_distress'], 1)} % |")
    h = data["hypoxaemic_sensitivity"]
    lines += ["", f"- Sensibilidad hipoxémica ({h['label']}, ganancia {h['gain']}): sigue no vacía "
                  f"{_yes(h['still_nonempty'])}; usada para el veredicto: {_yes(h['used_for_the_verdict'])}.",
              f"- Pasa: {_yes(cf['pass'])}."]
    return "\n".join(lines)


def render_parametros(data: dict) -> str:
    p = data["parameters"]
    return "\n".join([f"- Siguen UNSET: {', '.join(p['still_unset'])}.",
                      f"- Perfiles comprometidos sin lectores ni impulso hipoxémico: "
                      f"{_yes(all(p['committed_profiles_unset'].values()))}; campos nuevos del perfil: "
                      f"{p['new_profile_fields'] or 'ninguno'}; distrés de llegada comprometido: "
                      f"{p['committed_arrival_distress']}.", f"- Pasa: {_yes(p['pass'])}."])


def render_no_regresion(data: dict) -> str:
    n = data["non_regression"]
    return "\n".join([f"- Registro de P2T-1A reproducido sobre su árbol: {_yes(n['p2t1a_record_reproduced_on_its_tree'])}; "
                      f"intacto {_yes(n['p2t1a_record_untouched'])}.",
                      f"- Registro de P2S-3 intacto: {_yes(n['p2s3_record_untouched'])}; {n['p2s3_classification']}.",
                      f"- Perfil del asma con la mecánica encendida (M1): {_yes(n['asthma_profile_mechanics_on'])}.",
                      f"- Pasa: {_yes(n['pass'])}."])


def render_prueba(data: dict) -> str:
    p = data["proof"]
    return "\n".join([f"- Tuplas revertidas a las de P2T-1A: {', '.join(f'`{k}` {_yes(v)}' for k, v in p['proofs'].items())}.",
                      f"- Archivos comunes fijados por hash: {len(p['common_untouched'])}, intactos "
                      f"{_yes(all(p['common_untouched'].values()))}.",
                      f"- Vista de P2T-1A: digest {_yes(p['p2t1a_freeze_digest'])}, su prueba {_yes(p['p2t1a_proof'])}, "
                      f"registro {_yes(p['p2t1a_record'])}."])


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    lines = [f"- {_yes(c['holds'])} — {c['criterion']}" for c in v["criteria"]]
    lines += ["", f"**Veredicto: {v['verdict']}** ({v['region_status']})"]
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
    parser.add_argument("--data", type=Path, required=True, help="the P2T-3 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
