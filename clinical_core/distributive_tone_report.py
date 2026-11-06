"""P2W-1 report: the generated blocks of docs/revision/P2W1_TONO_DISTRIBUTIVO_COMUN.md.

    python -m clinical_core.distributive_tone_report --write <document> --data <the P2W-1 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("decisiones", "arquitectura", "representacion", "lector", "sondas", "firma", "parametros", "deudas",
         "no_regresion", "prueba", "veredicto")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
PROBES = ("V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10", "V11", "V12", "V13", "V14")
CASES = ("anaphylaxis_29f", "anaphylaxis_63m_betablocked")


def render_decisiones(data: dict) -> str:
    d, s = data["design"]["decisions"], data["design"]["semantics"]
    lines = [f"- **{k}:** {v}" for k, v in d.items()]
    lines += ["", f"- Representa: {s['represents']}.",
              f"- No representa: {', '.join(s['does_not_represent'])}.",
              f"- Estado: {s['state']}.", f"- Llegada: {s['arrival']}.", f"- Escritor: {s['writer']}.",
              f"- Cinética del núcleo: {s['core_kinetics']}.", f"- Lector: {s['reader']}.",
              f"- Efecto: {s['effect']}.", f"- Observable: {s['observable']}."]
    return "\n".join(lines)


def render_arquitectura(data: dict) -> str:
    a = data["audit"]
    lines = [f"- Lectores del canal T: {', '.join(a['t_readers'])}; escritores: {', '.join(a['t_writers'])} (el "
             f"núcleo sigue siendo el único).",
             f"- La guardia de P2J-2 contra un segundo escritor de T sigue intacta: {_yes(a['guard_unchanged'])}.",
             f"- Lectores de la carga en `derived.py`: {', '.join(a['burden_readers'])}; del ancla: "
             f"{', '.join(a['arrival_readers'])}; de la ganancia: {', '.join(a['gain_readers'])}.",
             f"- Lectores en `integration.py`: {', '.join(a['integration_readers'])}.",
             f"- `beta_blockade` se lee en: {', '.join(a['beta_blockade_readers'])} — ni el tono ni la presión.",
             "", "Factores del objetivo de tono, en el orden en que el código los compone:", ""]
    lines += [f"{i + 1}. `{term}`" for i, term in enumerate(a["tone_target_terms"])]
    lines += ["", f"- Antes de P2W-1: `{a['tone_target_terms_before'][0]}`.",
              f"- Composición: {a['composition']}.", f"- Punto de inserción: {a['insertion_point']}.",
              f"- Pasa: {_yes(a['pass'])}."]
    return "\n".join(lines)


def render_representacion(data: dict) -> str:
    r = data["representation"]
    lines = ["- Campos nuevos: " + "; ".join(f"`{k}` → {v}" for k, v in r["added_fields"].items()) + ".",
             f"- Interfaz del escritor: {r['writer_interface']['record']}, campo "
             f"`{r['writer_interface']['contribution_field']}`, con la misma forma que "
             f"{r['writer_interface']['same_shape_as']} ({_yes(r['writer_interface']['fields_match'])}).",
             f"- Rastro aditivo de dos escritores: {' → '.join(_n(v, 2) for v in r['trail'])}; cambios por minuto "
             f"{r['records']}; fuente {', '.join(r['aux_source'])}.",
             f"- Rastro con una reversión declarada: {' → '.join(_n(v, 2) for v in r['down_trail'])}.",
             f"- Estado por defecto {_n(r['default_state'], 2)}; sin cota superior {_yes(r['no_upper_bound'])}; "
             f"escritores de familia: {r['family_writers'] or 'ninguno'}.", "", "Rechazos:", ""]
    lines += [f"- {k}: {_yes(v)}" for k, v in r["refused"].items()]
    lines.append(f"\n- Pasa: {_yes(r['pass'])}.")
    return "\n".join(lines)


def render_lector(data: dict) -> str:
    r = data["reader"]
    lines = [f"- Campo nuevo del perfil: {r['new_profile_fields']}; UNSET por defecto {_yes(r['default_unset'])}.",
             f"- UNSET en todos los perfiles comprometidos: "
             f"{', '.join(f'{k} {_yes(v)}' for k, v in r['committed_profiles_unset'].items())}.",
             f"- Declararlo no declara ningún otro lector: {_yes(r['declared_alone'])}.", "",
             "| Carga | Objetivo | Factor |", "|---|---|---|"]
    for burden, row in sorted(r["rows"].items(), key=lambda kv: float(kv[0])):
        lines.append(f"| {burden} | {_n(row['target'], 6)} | {_n(row['factor'], 6)} |")
    lines += ["", f"- El factor es exactamente 1 / (1 + k·b): {_yes(r['factor_is_the_gain'])}; nunca por encima de 1: "
                  f"{_yes(r['factor_at_or_below_one'])}; otra ganancia da su propio factor: "
                  f"{_yes(r['other_gain_is_its_own'])}.",
              f"- Escritores del canal T: {', '.join(r['t_channel_writers'])}.",
              f"- Registro de parámetros: {r['parameter_state']}. {r['parameter_note']}",
              f"- Pasa: {_yes(r['pass'])}."]
    return "\n".join(lines)


def render_sondas(data: dict) -> str:
    p = data["probes"]
    lines = ["| Sonda | Qué exige | Pasa |", "|---|---|---|"]
    for name in PROBES:
        lines.append(f"| {name} | {p[name]['requires']} | {_yes(p[name]['pass'])} |")
    v2, v3, v4, v5 = p["V2"], p["V3"], p["V4"], p["V5"]
    lines += ["", f"- V2: sobre la rejilla {v2['grid']} el objetivo va "
                  f"{' → '.join(_n(v, 4) for v in v2['target'])} y la PAM a ese tono "
                  f"{' → '.join(_n(v, 2) for v in v2['map_at_that_tone'])}.",
              f"- V3: con la carga fija, por ganancia de compensación: " + "; ".join(
                  f"g {g} → " + "/".join(_n(v, 4) for _, v in sorted(row.items(), key=lambda kv: float(kv[0])))
                  for g, row in sorted(v3["rows"].items(), key=lambda kv: float(kv[0]))) +
              f" (demandas {', '.join(sorted(next(iter(v3['rows'].values())), key=float))}); en el déficit de llegada "
              f"el objetivo es el factor de dilatación solo, igual para toda ganancia: "
              f"{_yes(v3['normalization_independent_of_the_gain'])}.",
              f"- V4: dilatación sola {_n(v4['dilation_only'], 4)}, cota de la compensación "
              f"{_n(v4['compensation_bound'], 4)}, objetivo máximo posible {_n(v4['largest_possible_target'], 4)}; "
              f"opone {_yes(v4['opposes'])}, nunca borra {_yes(v4['never_erases'])}, sigue bajo la llegada "
              f"{_yes(v4['still_below_arrival'])}.",
              f"- V5: con carga {_n(data['design']['synthetic']['severe_burden'], 0)} el objetivo es "
              f"{_n(v5['target_at_a_severe_burden'], 6)}; T queda en la guarda "
              f"{_n(v5['t_lower_guard'], 2)} con el recorte registrado, PAM {_n(v5['map_after'], 2)} y gasto "
              f"{_n(v5['output_after'], 4)} (flujo conservado)."]
    return "\n".join(lines)


def render_firma(data: dict) -> str:
    s = data["signature"]
    lines = ["| Carga | T | PAM | Gasto | Entrega | Relleno |", "|---|---|---|---|---|---|"]
    for burden, row in sorted(s["rows"].items(), key=lambda kv: float(kv[0])):
        lines.append(f"| {burden} | {_n(row['T'], 4)} | {_n(row['map'], 2)} | {_n(row['output_rel'], 4)} | "
                     f"{_n(row['delivery_rel'], 4)} | {_n(row['crt'], 2)} |")
    lines += ["", f"- Patrón: la presión baja {_yes(s['pattern']['pressure_falls'])}, el flujo se conserva o sube "
                  f"{_yes(s['pattern']['flow_preserved_or_raised'])}, el relleno no se alarga "
                  f"{_yes(s['pattern']['refill_not_prolonged'])}.", ""]
    for case in CASES:
        a = s["authored"][case]
        lines.append(f"- **{case}:** PA {a['sbp']}/{a['dbp']}, FC {a['hr']} ({a['rhythm']}), SpO2 {a['spo2']} %, FR "
                     f"{a['rr']}, lactato {a['lactate']}, relleno {a['crt_s']} s, extremidades {a['extremities']}, "
                     f"piel {a['skin']}; vía aérea: «{a['airway']}»; edema: {a['edema']}; cardíaco: "
                     f"«{a['cardiac']}»; acciones autorales: {', '.join(a['authored_actions'])}. Evidencia "
                     f"independiente: {'; '.join(s['independent_evidence'][case])}. Estado: {s['status'][case]}; "
                     f"carga de llegada {s['arrival_burden'][case]}.")
    lines += ["", f"- Legado (clasificado, nunca ajustado): {s['legacy']['classification']}; "
                  f"SBP por severidad {s['legacy']['sbp_per_severity']}, FC por severidad "
                  f"{s['legacy']['hr_per_severity']}, progresión {s['legacy']['progression_per_min']}/min.",
              f"- Lecturas cerradas que ya leían este patrón: "
              + "; ".join(f"{k}: {v}" for k, v in s["closed_readings"].items()) + ".",
              f"- {s['note']}. Pasa: {_yes(s['pass'])}."]
    return "\n".join(lines)


def render_parametros(data: dict) -> str:
    p = data["parameters"]
    lines = [f"- **{k}:** {v}" for k, v in p["unset"].items()]
    lines += ["", f"- En el registro de parámetros {_yes(p['declared_in_the_registry'])}, estado "
                  f"{p['registry_state']}; entrada candidata fuera del registro de parámetros de caso "
                  f"{_yes(p['candidate_input_outside_case_parameters'])}.",
              f"- Ganancias comprometidas: {', '.join(f'{k} {v}' for k, v in p['committed_gains'].items())}.",
              f"- Carga de llegada comprometida: "
              f"{', '.join(f'{k} {_n(v, 2)}' for k, v in p['committed_arrival'].items())}.",
              f"- Compensación comprometida (sin cambio): "
              f"{', '.join(f'{k} {_n(v, 2)}' for k, v in p['committed_compensation'].items())}.",
              f"- Valores sintéticos de las sondas (SYNTHETIC_ONLY): "
              f"{', '.join(f'{k} = {v}' for k, v in p['synthetic_only'].items())}.",
              f"- Pasa: {_yes(p['pass'])}."]
    return "\n".join(lines)


def render_deudas(data: dict) -> str:
    d = data["carried_debts"]
    lines = [f"- **{k}** (de {v['from']}): {v['status']}. {v['note']}." for k, v in d["debts"].items()]
    lines += ["", f"- La presión no entra en el camino del tono: {_yes(not d['pressure_in_the_tone_path'])}.",
              f"- Sin escritor de familia de la carga: {_yes(d['no_family_writer'])}.",
              f"- Estrés sistémico UNSET en todo perfil comprometido: {_yes(all(d['p2v1_stress_unset'].values()))}.",
              f"- Compensación sin cambio: "
              f"{', '.join(f'{k} {_n(v, 2)}' for k, v in d['compensation_unchanged'].items())}.",
              f"- Pasa: {_yes(d['pass'])}."]
    return "\n".join(lines)


def render_no_regresion(data: dict) -> str:
    n = data["non_regression"]
    return "\n".join([
        f"- Registro de P2V-1 reproducido sobre su árbol: {_yes(n['p2v1_record_reproduced_on_its_tree'])} (anida "
        f"P2U-1, P2T-5, P2T-3, P2T-1A, P2T-1, P2S-3, P2S-2 y, por ellos, opioides, asma, TEP, edema, SCA y GI); "
        f"intacto {_yes(n['p2v1_record_untouched'])}; su veredicto {n['p2v1_verdict']}.",
        f"- Carga de llegada 0 en los perfiles comprometidos: "
        f"{_yes(all(n['committed_arrival_burden_zero'].values()))}.",
        f"- Tuplas de registro: {', '.join(f'{k} {_yes(v)}' for k, v in n['tuples'].items())}.",
        f"- Pasa: {_yes(n['pass'])}."])


def render_prueba(data: dict) -> str:
    p = data["proof"]
    return "\n".join([
        f"- Archivos revertidos a los de P2V-1: {', '.join(f'`{k}` {_yes(v)}' for k, v in p['proofs'].items())}.",
        f"- Archivos comunes fijados por hash: {len(p['common_untouched'])}, intactos "
        f"{_yes(all(p['common_untouched'].values()))}.",
        f"- Vista de P2V-1: digest {_yes(p['p2v1_freeze_digest'])}, su prueba {_yes(p['p2v1_proof'])}, registro "
        f"{_yes(p['p2v1_record'])}."])


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
    parser.add_argument("--write", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
