"""P2T-1 report: the generated blocks of docs/revision/P2T1_DISTRES_RESPIRATORIO_COMUN.md.

    python -m clinical_core.respiratory_distress_report --write <document> --data <the P2T-1 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("auditoria", "representacion", "sondas", "contrastes", "beta", "ordenamiento", "ortogonalidad", "parametros",
         "no_regresion", "prueba", "veredicto")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}


def _row(values) -> str:
    return "| " + " | ".join(str(v) for v in values) + " |"


def _list(values) -> str:
    return ", ".join(f"`{v}`" for v in values) or "ninguno"


def render_auditoria(data: dict) -> str:
    a = data["audit"]
    lines = [f"- **{k}:** {v}" for k, v in sorted(a["insertion_points"].items())]
    lines += [f"- Lectores del distrés en `derived.py`: {_list(a['distress_readers'])}; del distrés de llegada: "
              f"{_list(a['arrival_distress_readers'])}.",
              f"- Lectores de las ganancias: respiratoria {_list(a['gain_readers']['distress_to_respiratory_drive_gain'])}; "
              f"simpática {_list(a['gain_readers']['distress_to_sympathetic_gain'])}.",
              f"- Argumentos de distrés de la composición: {_list(a['composition_distress_arguments'])} (nunca la SpO2 "
              f"ni la mecánica).",
              f"- El objetivo simpático lee de nuevo sólo {_list(a['sympathetic_target_new_reads'])}; el incremento lee el "
              f"β-bloqueo: {_yes(a['increment_reads_beta_blockade'])}.",
              f"- La integración lee para el distrés sólo {_list(a['integration_distress_reads'])} y suma: "
              f"`{a['integration_sums'][0]}`.",
              f"- Pasa: {_yes(a['pass'])}."]
    return "\n".join(lines)


def render_representacion(data: dict) -> str:
    r = data["representation"]
    added = "; ".join(f"`{k}`: {_list(v)}" for k, v in r["added_fields"].items())
    refused = ", ".join(f"{k} {_yes(v)}" for k, v in r["refused"].items())
    return "\n".join([
        f"- Campos añadidos: {added}.",
        f"- Rechazos: {refused}.",
        f"- Aditivo y persistente (dos escritores sintéticos, +1 en los minutos 1–3 y +0,5 en los minutos 1–2): "
        f"{', '.join(_n(v, 1) for v in r['trail'])}; cambios registrados por minuto {r['records']}; fuente del cambio "
        f"auxiliar {_list(r['aux_source'])}.",
        f"- El perfil por defecto declara algún lector: {_yes(r['default_profile_reads'])}. Escritores de familia en "
        f"`clinical_core/modules`: {_list(r['family_writers'])}.",
        f"- Pasa: {_yes(r['pass'])}."])


def render_sondas(data: dict) -> str:
    p = data["probes"]
    d = {k: p[k] for k in p}
    detail = {
        "D1": f"cursos de referencia releídos con los lectores declarados: "
              f"{', '.join(f'{k} {_yes(v)}' for k, v in d['D1']['re_read'].items())}; curso del SCA re-ejecutado: "
              f"{_yes(d['D1']['re_run_states_equal'])}",
        "D2": f"distrés {', '.join(_n(r['distress'], 1) for r in d['D2']['rows'])}: impulso excitador "
              f"{', '.join(_n(v, 2) for v in d['D2']['excitatory'])}; FR {', '.join(_n(v, 1) for v in d['D2']['rr'])}; FC "
              f"{', '.join(_n(v, 1) for v in d['D2']['hr'])}",
        "D3": f"objetivo simpático {', '.join(_n(v, 3) for v in d['D3']['target'])}; FC "
              f"{', '.join(_n(v, 1) for v in d['D3']['hr'])}; FR {', '.join(_n(v, 1) for v in d['D3']['rr'])}",
        "D4": "; ".join(f"{k} (g_R {v[0]}, g_S {v[1]}): ΔFR {_n(d['D4']['delta'][k]['rr'], 2)}, ΔFC "
                        f"{_n(d['D4']['delta'][k]['hr'], 2)}" for k, v in d['D4']['pairs'].items()),
        "D5": f"disponibilidad {', '.join(_n(v, 1) for v in d['D5']['availability'])}: FR "
              f"{', '.join(_n(v, 1) for v in d['D5']['rr'])}; distrés {', '.join(_n(v, 1) for v in d['D5']['distress'])}; "
              f"término de distrés {', '.join(_n(v, 1) for v in d['D5']['distress_drive'])}",
        "D6": f"disponibilidad {', '.join(_n(v, 1) for v in d['D6']['availability'])}: FC "
              f"{', '.join(_n(v, 1) for v in d['D6']['hr'])} (sin distrés {_n(d['D6']['hr_without_distress'], 1)})",
        "D7": f"SpO2 {_n(d['D7']['spo2'][0], 0)} → {_n(d['D7']['spo2'][-1], 1)}; distrés siempre 0: "
              f"{_yes(set(d['D7']['distress']) == {0.0})}; cambios registrados {d['D7']['records']}; misma FR y FC: "
              f"{_yes(d['D7']['same_rr_hr'])}",
        "D8": f"E {_n(d['D8']['mechanics'][0], 3)} → {_n(d['D8']['mechanics'][-1], 3)}; PaCO2 "
              f"{_n(d['D8']['paco2'][0], 1)} → {_n(d['D8']['paco2'][-1], 1)}; distrés siempre 0: "
              f"{_yes(set(d['D8']['distress']) == {0.0})}; misma FR y FC: {_yes(d['D8']['same_rr_hr'])}",
        "D9": "; ".join(f"{k}: se mueven {_list(v['moved'])}; W sigue sólo a la FR {_yes(v['w_follows_rr_only'])}"
                        for k, v in d['D9'].items() if isinstance(v, dict)),
        "D10": f"impulso ácido {_n(d['D10']['acid_drive'], 1)} + distrés {_n(d['D10']['distress_drive'], 1)} = "
               f"{_n(d['D10']['excitatory'], 1)}; FR {_n(d['D10']['rr'], 2)} (si se sumara después de la saturación, "
               f"{_n(d['D10']['rr_if_summed_after_saturation'], 2)}; techo {_n(d['D10']['ceiling'], 0)})",
        "D11": "; ".join(f"{k}: hipoxémico {_n(v['hypoxaemic_drive'], 2)}, distrés {_n(v['distress_drive'], 2)}"
                         for k, v in d['D11']['table'].items())
               + f"; mapeo hipoxémico UNSET en los perfiles comprometidos: {_yes(d['D11']['committed_hypoxaemic_unset'])}",
        "D12": f"lectura exacta del núcleo de P2S-3: "
               f"{', '.join(f'{k} {_yes(v)}' for k, v in d['D12']['exact_reading_p2s3_core'].items())}; distrés 0 en "
               f"todos: {_yes(all(d['D12']['distress_zero'].values()))}",
    }
    rows = ["| Sonda | Qué exige | Resultado | Pasa |", "|---|---|---|---|"]
    for k in sorted(p, key=lambda x: int(x[1:])):
        rows.append(_row([k, p[k]["requires"], detail[k], _yes(p[k]["pass"])]))
    return "\n".join(rows)


def _c(row: dict) -> str:
    z, s = row["distress_0"], row["distress_synthetic"]
    return (f"FR {_n(z['rr'], 1)} → {_n(s['rr'], 1)}, FC {_n(z['hr'], 1)} → {_n(s['hr'], 1)}, PaCO2 "
            f"{_n(z['paco2'], 1)} → {_n(s['paco2'], 1)}")


def render_contrastes(data: dict) -> str:
    c = data["contrasts"]
    o = c["opioid_contrast"]
    lines = [
        f"- **Edema 58m** (mapeo de llegada comprometido, distrés 0 → sintético): {_c(c['pulmonary_edema_58m'])}.",
        f"- **TEP 61m:** {_c(c['pulmonary_embolism_61m'])}; términos del shock (déficit agudo, deuda) sin cambio: "
        f"{_yes(c['pulmonary_embolism_61m']['shock_terms_unchanged'])}; el objetivo sube exactamente g_S × distrés: "
        f"{_yes(c['pulmonary_embolism_61m']['target_rise_is_the_reader'])}.",
        f"- **TEP 33f:** {_c(c['pulmonary_embolism_33f'])}.",
        f"- **Asma 49m** (mecánica de llegada FAMILY_CANDIDATE de P2S-3): {_c(c['asthma_49m'])}; la mecánica no cambia: "
        f"{_yes(c['asthma_49m']['mechanics_unchanged'])}.",
        f"- **Contraste del opioide** (sondas sintéticas: SpO2 {_n(o['declared']['spo2'], 0)}, disponibilidad 0,3, "
        f"distrés 0): FR {_n(o['declared']['rr'], 1)} y FC {_n(o['declared']['hr'], 1)} con los lectores declarados, "
        f"{_n(o['unset']['rr'], 1)} y {_n(o['unset']['hr'], 1)} sin ellos: ni taquicardia ni taquipnea forzadas "
        f"{_yes(o['no_forced_tachycardia_or_tachypnoea'])}.",
        f"- **SCA 70f:** FC autoral {_n(c['acs_70f_left_main']['authored_hr'], 0)}, núcleo "
        f"{_n(c['acs_70f_left_main']['core_hr'], 1)}, residual {_n(c['acs_70f_left_main']['residual'], 1)} sin cambio con "
        f"distrés 0 ({c['acs_70f_left_main']['status']}).",
    ]
    for name, v in c["systemic_stress_residuals"].items():
        lines.append(f"- **{name}** (estado sintético, distrés 0): FC autoral {_n(v['authored_hr'], 0)}, núcleo "
                     f"{_n(v['core_hr'], 1)}, residual {_n(v['residual'], 1)}, sin cambio {_yes(v['unchanged'])}.")
    lines.append(f"- {c['note']}. Pasa: {_yes(c['pass'])}.")
    return "\n".join(lines)


def render_beta(data: dict) -> str:
    b = data["beta_blockade"]
    rows = "; ".join(f"β {k}: ΔFC {_n(v['hr_rise'], 2)} (por `sympathetic_increment` {_yes(v['through_increment'])})"
                     for k, v in b["rows"].items())
    return f"- {rows}.\n- Pasa: {_yes(b['pass'])}."


def render_ordenamiento(data: dict) -> str:
    o = data["ordering"]
    rows = ["| Caso | WOB autoral | Etiqueta ordinal | Rango |", "|---|---|---|---|"]
    for case in sorted(o["authored"], key=lambda k: (o["ranks"].get(k, -1), k)):
        rows.append(_row([f"`{case}`", o["authored"][case], o["labels"][case] or "fuera del orden",
                          o["ranks"].get(case, "—")]))
    regions = "; ".join(f"{k} {v}" for k, v in o["candidate_regions"].items())
    return "\n".join(rows + [
        "",
        f"- Regiones candidatas (FAMILY_CANDIDATE / SYNTHETIC_ONLY, sólo cuenta su orden): {regions}; estrictamente "
        f"ordenadas: {_yes(o['regions_strictly_ordered'])}.",
        f"- Orden no vacío: {_yes(o['non_empty_ordering'])}; pares que el WOB ordena: {o['identified_pairs']}; empates "
        f"(el WOB no los ordena): {'; '.join(', '.join(t) for t in o['ties']) or 'ninguno'}.",
        f"- Los lectores preservan el orden: {_yes(o['readers_preserve_order'])}. Ajustado a la FR o la FC: "
        f"{_yes(o['fitted_to_rr_or_hr'])}. Estado: {o['status']}."])


def render_ortogonalidad(data: dict) -> str:
    o = data["orthogonality"]
    same_e = "; ".join(f"distrés {k}: FR {_n(v['rr'], 1)}, FC {_n(v['hr'], 1)}, W {_n(v['W'], 3)}, PaCO2 "
                       f"{_n(v['paco2'], 1)}" for k, v in o["same_mechanics"].items())
    same_d = "; ".join(f"E {_n(float(k), 3)}: término de distrés {_n(v['distress_drive'], 1)}, FR {_n(v['rr'], 1)}, FC "
                       f"{_n(v['hr'], 1)}, W {_n(v['W'], 3)}, PaCO2 {_n(v['paco2'], 1)}" for k, v in o["same_distress"].items())
    return f"- Misma mecánica, distinto distrés: {same_e}.\n- Mismo distrés, distinta mecánica: {same_d}.\n" \
           f"- Pasa: {_yes(o['pass'])}."


def render_parametros(data: dict) -> str:
    p = data["parameters"]
    lines = [f"- **{k}:** {v}" for k, v in p["status"].items()]
    lines += [f"- Lectores UNSET en los perfiles comprometidos: "
              f"{', '.join(f'{k} {_yes(v)}' for k, v in p['profiles_unset'].items())}.",
              f"- Distrés de llegada 0 en los mapeos comprometidos: {_yes(all(p['arrival_distress_zero'].values()))}.",
              f"- Observable: {data['observable']['status']}; el núcleo lee el WOB: "
              f"{_yes(bool(data['observable']['wob_read_by_core']))}.",
              f"- Estrés sistémico: {data['systemic_stress']['status']}; identificadores nuevos "
              f"{_list(data['systemic_stress']['new_identifiers'])}; filtrados {_list(data['systemic_stress']['leaked'])}.",
              f"- Pasa: {_yes(p['pass'] and data['observable']['pass'] and data['systemic_stress']['pass'])}."]
    return "\n".join(lines)


def render_no_regresion(data: dict) -> str:
    n = data["non_regression"]
    return "\n".join([
        f"- Registro de P2S-2 reproducido en vivo (a través de las vistas cerradas, que anidan P2Q-2, P2P-2, P2P-1, SCA y "
        f"GI): {_yes(n['p2s2_record_reproduced'])}.",
        f"- Registro de P2S-3 reproducido en vivo: {_yes(n['p2s3_record_reproduced'])}; archivo intacto: "
        f"{_yes(n['p2s3_record_untouched'])}; su veredicto congelado sigue siendo `{n['p2s3_historical_verdict']}`.",
        f"- Clasificación vigente de P2S-3: {n['p2s3_classification']}.",
        f"- Pasa: {_yes(n['pass'])}."])


def render_prueba(data: dict) -> str:
    p = data["proof"]
    return "\n".join([
        f"- Archivos con inserciones declaradas, probados contra P2S-3 (`{data['design']['p2s3']['head']}`): "
        f"{', '.join(f'`{k}` {_yes(v)}' for k, v in p['proofs'].items())}.",
        f"- Archivos comunes fijados por hash: {len(p['common_untouched'])}, intactos "
        f"{_yes(all(p['common_untouched'].values()))}.",
        f"- Vista de P2S-3: digest de congelación {_yes(p['p2s3_freeze_digest'])}, su prueba contra P2S-2 "
        f"{_yes(p['p2s3_proof'])}, registro {_yes(p['p2s3_record'])}."])


def render_veredicto(data: dict) -> str:
    r = data["readiness"]
    lines = [f"- {_yes(c['holds'])} — {c['criterion']}" for c in r["criteria"]]
    lines += ["", f"**Veredicto: {r['verdict']}**", "", f"Composición: {', '.join(r['composition'])}.", "",
              f"**Recomendación: {r['recommendation']}**"]
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
    parser.add_argument("--data", type=Path, required=True, help="the P2T-1 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
