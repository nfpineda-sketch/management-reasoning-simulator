"""P2V-1 report: the generated blocks of docs/revision/P2V1_ESTRES_SISTEMICO_COMUN.md.

    python -m clinical_core.systemic_stress_report --write <document> --data <the P2V-1 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("decisiones", "camino", "representacion", "lector", "aislamiento", "hipoglucemia", "sondas", "contrastes",
         "metodologia", "parametros", "deudas", "no_regresion", "prueba", "veredicto")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
PROBES = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10")
CASES = ("hypoglycemia_28m", "acs_70f_left_main", "renal_colic_34m", "pneumonia_46f", "pneumonia_83m",
         "anaphylaxis_63m_betablocked")


def render_decisiones(data: dict) -> str:
    d = data["design"]["decisions"]
    s = data["design"]["semantics"]
    lines = [f"- **{k}:** {v}" for k, v in d.items()]
    lines += ["", f"- Representa: {s['represents']}.",
              f"- No representa: {', '.join(s['does_not_represent'])}.",
              f"- Estado: {s['state']}.", f"- Llegada: {s['arrival']}.", f"- Escritor: {s['writer']}.",
              f"- Cinética del núcleo: {s['core_kinetics']}.", f"- Lector simpático: {s['sympathetic_reader']}.",
              f"- Lector respiratorio: {s['respiratory_reader']}.", f"- Observable: {s['observable']}."]
    return "\n".join(lines)


def render_camino(data: dict) -> str:
    a = data["audit"]
    lines = ["Términos del objetivo simpático, en el orden en que el código los compone:", ""]
    lines += [f"{i + 1}. `{term}`" for i, term in enumerate(a["target_terms"])]
    lines += ["", "Qué expresa cada entrada:", ""]
    lines += [f"- **{k}:** {v}" for k, v in a["inputs"].items()]
    lines += ["", "Efector común, aguas abajo:", ""]
    lines += [f"- **{k}:** {v}" for k, v in a["effector"].items()]
    lines += ["", f"- Punto de inserción: {a['insertion_point']}.",
              f"- Términos añadidos: {a['terms_added']}; retirados: {a['terms_removed'] or 'ninguno'}.",
              f"- Lectores del estrés en `derived.py`: {', '.join(a['stress_readers'])}; del ancla de llegada: "
              f"{', '.join(a['arrival_readers'])}; de la ganancia: {', '.join(a['gain_readers'])}.",
              f"- Funciones respiratorias que leen el estrés: {a['respiratory_functions_reading_stress'] or 'ninguna'}.",
              f"- Lectores en `integration.py`: {', '.join(a['integration_readers'])}.",
              f"- Pasa: {_yes(a['pass'])}."]
    return "\n".join(lines)


def render_representacion(data: dict) -> str:
    r = data["representation"]
    added = r["added_fields"]
    lines = [f"- Campos nuevos: " + "; ".join(f"`{k}` → {v}" for k, v in added.items()) + ".",
             f"- Interfaz del escritor: {r['writer_interface']['record']}, campo "
             f"`{r['writer_interface']['contribution_field']}` de la contribución, con la misma forma que "
             f"{r['writer_interface']['same_shape_as']} ({_yes(r['writer_interface']['fields_match'])}).",
             f"- Rastro aditivo de dos escritores: {' → '.join(_n(v, 2) for v in r['trail'])}; cambios por minuto "
             f"{r['records']}; fuente {', '.join(r['aux_source'])}.",
             f"- Rastro con una caída declarada: {' → '.join(_n(v, 2) for v in r['down_trail'])}.",
             f"- Estado por defecto: {_n(r['default_state'], 2)}; sin cota superior: {_yes(r['no_upper_bound'])}.",
             f"- Escritores de familia: {r['family_writers'] or 'ninguno'}.", "", "Rechazos:", ""]
    lines += [f"- {k}: {_yes(v)}" for k, v in r["refused"].items()]
    lines.append(f"\n- Pasa: {_yes(r['pass'])}.")
    return "\n".join(lines)


def render_lector(data: dict) -> str:
    r = data["reader"]
    lines = [f"- Campo nuevo del perfil: {r['new_profile_fields']}; UNSET por defecto: {_yes(r['default_unset'])}; en "
             f"el perfil de sonda: {_yes(r['base_profile_unset'])}.",
             f"- UNSET en todos los perfiles comprometidos: "
             f"{', '.join(f'{k} {_yes(v)}' for k, v in r['committed_profiles_unset'].items())}.",
             f"- Declararlo no declara ningún otro lector: {_yes(r['declared_alone'])}.",
             f"- El alza del objetivo es exactamente la ganancia por el estrés: {_yes(r['target_rise_is_the_gain'])}.",
             f"- El alza de la FC pasa por el incremento común (saturación y bloqueo beta): "
             f"{_yes(r['hr_rise_through_the_increment'])}.",
             f"- Con un estrés enorme la FC queda en o bajo el techo sinusal ({_n(r['sinus_ceiling'], 2)} lpm): "
             f"{_n(r['hr_at_a_huge_stress'], 2)} lpm, {_yes(r['saturated_at_or_below_the_ceiling'])}; respuesta "
             f"sublineal: {_yes(r['saturation_is_sublinear'])}.",
             f"- Ganancias rechazadas: {', '.join(f'{k} {_yes(v)}' for k, v in r['refused_gains'].items())}.",
             f"- Registro de parámetros: {r['parameter_state']}.", f"- Nota: {r['parameter_note']}",
             f"- Pasa: {_yes(r['pass'])}."]
    return "\n".join(lines)


def render_aislamiento(data: dict) -> str:
    i = data["isolation"]
    lines = [f"- Funciones respiratorias que leen el estrés: {i['respiratory_functions_reading_stress'] or 'ninguna'}; "
             f"en la composición del impulso: {_yes(i['stress_in_the_drive_composition'])}.",
             f"- Argumentos de `_composition`: {', '.join(f'`{a}`' for a in i['composition_arguments'])}.",
             f"- Cadena respiratoria fija al mover el estrés: "
             f"{', '.join(f'{k} {_yes(v)}' for k, v in i['respiratory_chain_fixed'].items())}.",
             f"- La FC sí se mueve en la misma rejilla: {' → '.join(_n(v, 2) for v in i['hr_moves'])}.",
             f"- Guardia de integración: {i['integration_guard']}.", f"- Pasa: {_yes(i['pass'])}."]
    return "\n".join(lines)


def render_hipoglucemia(data: dict) -> str:
    h = data["hypoglycaemia"]
    return "\n".join([
        f"- Expresión en el código: `{h['expression']}`; idéntica a la de P2U-1: {_yes(h['unchanged_since_p2u1'])}.",
        f"- Umbral {_n(h['threshold_mg_dl'], 1)} mg/dL, ganancia {_n(h['gain_per_mg_dl'], 4)} por mg/dL.",
        f"- Clasificación: **{h['classification']}**.", f"- Estado: {h['status']}",
        f"- Con glucosa de llegada 34: objetivo {_n(h['at_arrival_with_glucose_34'], 4)} en la llegada; si sigue "
        f"cayendo {_n(h['falling_further'], 4)}; si se recupera a 90 {_n(h['recovering_to_90'], 4)}.",
        f"- FC de llegada con glucosa 34 y con glucosa 100: {_n(h['arrival_hr_with_glucose_34'], 2)} y "
        f"{_n(h['arrival_hr_with_glucose_100'], 2)} lpm (el término no aporta nada en la llegada).",
        f"- Ni retirado ni reinterpretado: {_yes(not h['removed_or_rewritten'])}; direccionable aparte del estrés: "
        f"{_yes(h['independently_addressable'])}.", f"- Pasa: {_yes(h['pass'])}."])


def render_sondas(data: dict) -> str:
    p = data["probes"]
    lines = ["| Sonda | Qué exige | Pasa |", "|---|---|---|"]
    for name in PROBES:
        lines.append(f"| {name} | {p[name]['requires']} | {_yes(p[name]['pass'])} |")
    s2, s8, s9 = p["S2"], p["S8"], p["S9"]
    lines += ["", f"- S2: objetivo {' → '.join(_n(v, 4) for v in s2['target'])} y FC "
                  f"{' → '.join(_n(v, 2) for v in s2['hr'])} sobre la rejilla {s2['grid']}; con otra ganancia "
                  f"{' → '.join(_n(v, 4) for v in s2['target_other_gain'])}.",
              f"- S6 / S7 (bloqueo beta): " + "; ".join(
                  f"β {b} alza de FC {_n(r['hr_rise'], 2)} lpm (por el incremento {_yes(r['through_increment'])})"
                  for b, r in sorted(p["S6"]["rows"].items())) + ".",
              f"- S8: " + "; ".join(f"{k} objetivo {_n(v['target'], 4)} → con estrés {_n(v['target_with_stress'], 4)}"
                                    for k, v in sorted(s8["rows"].items())) + ".",
              f"- S9: base {_n(s9['base'], 4)}, sólo distrés {_n(s9['distress_only'], 4)}, sólo estrés "
              f"{_n(s9['stress_only'], 4)}, juntos {_n(s9['together'], 4)} (aditivo {_yes(s9['additive'])}); la FR "
              f"sólo la mueve el distrés: {_yes(s9['stress_never_moves_the_rr'])}."]
    return "\n".join(lines)


def render_contrastes(data: dict) -> str:
    c = data["contrasts"]
    h, a, r = c["hypoglycemia_28m"], c["acs_70f_left_main"], c["renal_colic_34m"]
    pn, an = c["pneumonia"], c["anaphylaxis_63m_betablocked"]
    lines = ["| Caso | FC autoral | Banda común | Diferencia (lpm) | Estado | Estrés de llegada |",
             "|---|---|---|---|---|---|",
             f"| hypoglycemia_28m | {_n(h['authored']['hr'], 0)} | {h['neutral_band']} | {_n(h['forced_bpm'], 2)} | "
             f"{h['status']} | {h['arrival_stress']} |",
             f"| acs_70f_left_main | {_n(a['authored']['hr'], 0)} | modelo {_n(a['model_hr'], 2)} | "
             f"{_n(a['residual_bpm'], 2)} | {a['status']} | {a['arrival_stress']} |",
             f"| renal_colic_34m | {_n(r['authored']['hr'], 0)} | {r['neutral_band']} | {_n(r['forced_bpm'], 2)} | "
             f"{r['status']} | {r['arrival_stress']} |"]
    for case in ("pneumonia_46f", "pneumonia_83m"):
        row = pn["cases"][case]
        lines.append(f"| {case} | {_n(row['authored']['hr'], 0)} | {row['neutral_band']} | {_n(row['gap_bpm'], 2)} | "
                     f"{row['status']} | {row['arrival_stress']} |")
    lines.append(f"| anaphylaxis_63m_betablocked | {_n(an['authored']['hr'], 0)} | FA, sin vía sinusal | — | "
                 f"{an['status']} | {an['arrival_stress']} |")
    lines += ["", f"- **hypoglycemia_28m:** {h['why']} Evidencia independiente: {'; '.join(h['evidence'])}. Términos "
                  f"de shock en la llegada: entrega {_n(h['shock_terms']['delivery'], 3)}, D "
                  f"{_n(h['shock_terms']['D'], 3)}, objetivo {_n(h['shock_terms']['target'], 3)}.",
              f"- **acs_70f_left_main:** {a['why']} Cerrar el residual con el distrés exigiría "
              f"{_n(a['closing_with_distress']['distress'], 2)} unidades y llevaría la FR a "
              f"{_n(a['closing_with_distress']['rr'], 2)} (autoral {_n(a['authored_rr'], 0)}; "
              f"+{_n(a['distress_cost_on_the_rr'], 2)} sobre la misma sonda).",
              f"- **renal_colic_34m:** {r['why']}",
              f"- **neumonía:** {pn['why']} Contribuyentes posibles: "
              f"{'; '.join(pn['cases']['pneumonia_46f']['candidate_contributors'])}.",
              f"- **anaphylaxis_63m_betablocked:** {an['why']} En FA la frecuencia es la del ritmo "
              f"({_yes(an['af_rate_is_the_rhythms'])}); con bloqueo completo la FC no se mueve "
              f"({_yes(an['full_blockade_suppresses'])}) aunque el objetivo sí "
              f"({_yes(an['target_still_rises_under_blockade'])}). No implementado: "
              f"{', '.join(an['not_implemented'])}.",
              "", f"- {c['note']}. Pasa: {_yes(c['pass'])}."]
    return "\n".join(lines)


def render_metodologia(data: dict) -> str:
    m = data["arrival_methodology"]
    lines = [f"{i + 1}. {line.split('. ', 1)[1] if line[:2].rstrip('.').isdigit() else line}"
             for i, line in enumerate(m["methodology"])]
    lines += ["", "Estado de cada ancla:", ""]
    lines += [f"- **{k}:** {v}" for k, v in m["anchor_status"].items()]
    lines += ["", f"- Mapeos aprobados: "
                  f"{', '.join(f'{k} {_yes(v)}' for k, v in m['mappings_approved'].items())}.",
              f"- Literales numéricos que este paquete escribe en el estrés: {', '.join(m['stress_literals'])} (sondas "
              f"de rechazo y de saturación).",
              f"- Ningún caso lleva valor: {_yes(m['every_case_unset'])}; la verdad autoral transcrita no lleva estrés: "
              f"{_yes(m['authored_rows_carry_no_stress'])}.",
              f"- {m['no_lookup_table']}.", f"- Pasa: {_yes(m['pass'])}."]
    return "\n".join(lines)


def render_parametros(data: dict) -> str:
    p = data["parameters"]
    lines = [f"- **{k}:** {v}" for k, v in p["unset"].items()]
    lines += ["", f"- En el registro de parámetros: {_yes(p['declared_in_the_registry'])}, estado "
                  f"{p['registry_state']}.",
              f"- Entrada candidata fuera del registro de parámetros de caso: "
              f"{_yes(p['candidate_input_outside_case_parameters'])} ({', '.join(p['candidate_inputs'])}).",
              f"- Ganancias comprometidas: {', '.join(f'{k} {v}' for k, v in p['committed_gains'].items())}.",
              f"- Estrés de llegada comprometido: "
              f"{', '.join(f'{k} {_n(v, 2)}' for k, v in p['committed_arrival'].items())}.",
              f"- Valores sintéticos de las sondas (SYNTHETIC_ONLY, no aprobados): "
              f"{', '.join(f'{k} = {v}' for k, v in p['synthetic_only'].items())}.",
              f"- Pasa: {_yes(p['pass'])}."]
    return "\n".join(lines)


def render_deudas(data: dict) -> str:
    d = data["carried_debts"]
    lines = [f"- **{k}** (de {v['from']}): {v['status']}. {v['note']}." for k, v in d["debts"].items()]
    gap = d["opioid_hr_gap"]
    gaps = "; ".join(f"{k} autoral {_n(v['authored_hr'], 0)} vs modelo {_n(v['model_hr'], 2)} "
                     f"({_n(v['gap_bpm'], 2)} lpm)" for k, v in gap.items())
    lines += ["", f"- Enlace de P2T-5 UNSET en los perfiles comprometidos: "
                  f"{_yes(all(d['p2t5_link_unset'].values()))}; impulso hipoxémico UNSET: "
                  f"{_yes(all(d['hypoxaemic_drive_unset'].values()))}; archivos de P2T-5 intactos: "
                  f"{_yes(d['p2t5_files_untouched'])}.",
              f"- Brecha de FC opioide, sin parchear: {gaps}.",
              f"- Ningún escritor de estrés en las familias: {_yes(d['no_opioid_stress_writer'])}.",
              f"- Pasa: {_yes(d['pass'])}."]
    return "\n".join(lines)


def render_no_regresion(data: dict) -> str:
    n = data["non_regression"]
    return "\n".join([
        f"- Registro de P2U-1 reproducido sobre su árbol: {_yes(n['p2u1_record_reproduced_on_its_tree'])} (anida P2T-5, "
        f"P2T-3, P2T-1A, P2T-1, P2S-3, P2S-2 y, por ellos, opioides, asma, TEP, edema, SCA y GI); intacto "
        f"{_yes(n['p2u1_record_untouched'])}; su veredicto {n['p2u1_verdict']}.",
        f"- Estrés de llegada 0 en los perfiles comprometidos: "
        f"{_yes(all(n['committed_arrival_stress_zero'].values()))}.",
        f"- Tuplas de registro: {', '.join(f'{k} {_yes(v)}' for k, v in n['tuples'].items())}.",
        f"- Pasa: {_yes(n['pass'])}."])


def render_prueba(data: dict) -> str:
    p = data["proof"]
    return "\n".join([
        f"- Archivos revertidos a los de P2U-1: {', '.join(f'`{k}` {_yes(v)}' for k, v in p['proofs'].items())}.",
        f"- Archivos comunes fijados por hash: {len(p['common_untouched'])}, intactos "
        f"{_yes(all(p['common_untouched'].values()))}.",
        f"- Vista de P2U-1: digest {_yes(p['p2u1_freeze_digest'])}, su prueba {_yes(p['p2u1_proof'])}, registro "
        f"{_yes(p['p2u1_record'])}."])


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
    parser.add_argument("--data", type=Path, required=True, help="the P2V-1 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
