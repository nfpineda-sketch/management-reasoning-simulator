"""P2S-2 report: the generated blocks of docs/revision/P2S2_MECANICA_RESPIRATORIA_COMUN.md.

    python -m clinical_core.respiratory_mechanics_report --write <document> --data <the P2S-2 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("rutas", "semantica", "interfaz", "sondas", "direcciones", "alto_co2", "contraste_24f", "opioide", "regiones",
         "sin_ancla", "unicidad", "estado_extra", "oxigenacion", "carga", "fc", "parametros", "no_regresion", "prueba",
         "veredicto")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}


def _row(values) -> str:
    return "| " + " | ".join(str(v) for v in values) + " |"


def _list(values, digits=2) -> str:
    return ", ".join("—" if v is None else _n(v, digits) for v in values)


def render_rutas(data: dict) -> str:
    paths = data["design"]["paths"]
    rows = ["| Ruta | Estado | Qué hace |", "|---|---|---|"]
    rows += [_row((f"`{k}`", status, text)) for k, (status, text) in paths.items()]
    a = data["audit"]
    rows.append("")
    rows.append(f"- Lectores del canal W en `derived.py`: {', '.join(f'`{x}`' for x in a['w_channel_readers'])} (P2K-1). "
                f"Con el candidato, la integración rechaza toda escritura de W "
                f"(`{a['integration_refuses_w_writes'][0]}`).")
    rows.append(f"- Lector de la eficiencia mecánica: {', '.join(f'`{x}`' for x in a['mechanics_readers'])}; la "
                f"llegada la escribe `{a['arrival_mechanics_readers'][0]}` desde el ancla.")
    rows.append(f"- Rama del candidato: lee {', '.join(f'`{x}`' for x in a['candidate_branch_reads'])}; la rama P2K-2 "
                f"lee {', '.join(f'`{x}`' for x in a['p2k2_branch_reads'])}.")
    rows.append(f"- El impulso, la oxigenación y la FC no leen W, PaCO2 ni la mecánica; la integración compone la "
                f"mecánica sólo con las contribuciones (`{a['integration_composition'][0]}`). Auditoría: "
                f"{_yes(a['pass'])}.")
    return "\n".join(rows)


def render_semantica(data: dict) -> str:
    d = data["design"]
    lines = [f"- **{k}:** {v}." for k, v in d["semantics"].items()]
    lines.append("- **Dimensiones:** " + "; ".join(f"{k}: {v}" for k, v in d["dimensions"].items()) + ".")
    return "\n".join(lines)


def render_interfaz(data: dict) -> str:
    i = data["interface"]
    lines = [f"- **{k}:** {v}." for k, v in data["design"]["interface"].items()]
    lines.append(f"- Persistencia: un escritor que se detiene en el minuto 5 deja la eficiencia en "
                 f"{_n(i['burst'][5], 5)} hasta el minuto 10 ({_yes(i['persists'])}); dos escritores componen "
                 f"({_yes(i['compose'])}); cada minuto registra sus cambios ({i['records']}); el cambio auxiliar queda "
                 f"bajo `{i['aux_source'][0]}`.")
    lines.append("- Rechazos: " + ", ".join(f"{k} {_yes(v)}" for k, v in i["refused"].items()) + ".")
    lines.append(f"- Escritores de familia en `clinical_core/modules`: {'ninguno' if not i['family_writers'] else i['family_writers']}.")
    return "\n".join(lines)


def render_sondas(data: dict) -> str:
    p = data["probes"]["probes"]
    text = data["design"]["probes"]
    rows = ["| Sonda | Qué exige | Resultado | Pasa |", "|---|---|---|---|"]
    m3 = p["M3"]
    summary = {
        "M1": f"FR {_n(p['M1']['rr'], 1)}, W {_n(p['M1']['W'], 3)}, PaCO2 {_n(p['M1']['paco2'], 1)}, pH {_n(p['M1']['ph'], 3)}",
        "M2": "E 1: FR " + _list(p["M2"]["1"]["rr"], 1) + "; PaCO2 " + _list(p["M2"]["1"]["paco2"], 1)
              + ". E 0,5: PaCO2 " + _list(p["M2"]["0.5"]["paco2"], 1),
        "M3": f"FR {_n(m3['points'][0]['rr'], 1)}, disponibilidad {_n(m3['availability'], 2)}; frontera E* "
              f"{_n(m3['boundary_efficiency'], 3)}; PaCO2 por E " + ", ".join(
                  f"{_n(x['efficiency'], 2)} → {_n(x['paco2'], 1)}" for x in m3["points"]),
        "M4": f"FR {_n(p['M4']['rr'], 1)} (intrínseca {_n(p['M4']['intrinsic_rr'], 0)}), E 1, W {_n(p['M4']['W'], 3)}, "
              f"PaCO2 {_n(p['M4']['paco2'], 1)}",
        "M5": "misma FR " + _n(p["M5"]["rr"][0], 1) + "; PaCO2 " + _list(p["M5"]["paco2"], 1),
        "M6": "E 1: FR " + _list(p["M6"]["1"]["rr"], 1) + ", PaCO2 " + _list(p["M6"]["1"]["paco2"], 1),
        "M7": "impulso ácido " + _list(p["M7"]["acid_drive"], 2) + "; FR " + _list(p["M7"]["rr"], 1)
              + f"; independiente del lactato {_yes(p['M7']['lactate_independent'])}; misma FR, misma W "
              f"{_yes(p['M7']['matched_rr']['same'])}",
        "M8": "SpO2 " + _list(p["M8"]["spo2"], 0) + "; FR " + _list(p["M8"]["rr"], 1) + "; PaCO2 "
              + _list(p["M8"]["paco2"], 1) + f"; misma FR, misma W {_yes(p['M8']['matched_rr']['same'])}",
        "M9": "disponibilidad " + _list(p["M9"]["availability"], 2) + "; FR " + _list(p["M9"]["rr"], 1)
              + "; PaCO2 " + _list(p["M9"]["paco2"], 1),
        "M10": f"estados idénticos salvo la mecánica {_yes(p['M10']['states_identical_but_mechanics'])}; derivados "
               f"idénticos {_yes(p['M10']['derived_identical'])}; E final {_n(p['M10']['efficiency_end'], 3)}; "
               "PaCO2 " + _list(p["M10"]["paco2"], 1),
        "M11": "G al final " + _n(p["M11"]["hypoxaemic_drive_unset"]["G_end"], 2) + "; E constante "
               + _yes(p["M11"]["hypoxaemic_drive_unset"]["efficiency_constant"] and
                      p["M11"]["synthetic_hypoxaemic_drive"]["efficiency_constant"])
               + "; con impulso hipoxémico sintético W " + _list(p["M11"]["synthetic_hypoxaemic_drive"]["W"], 3)
               + " (sólo por la FR)",
        "M12": f"L {_n(p['M12']['L_end'], 2)}, G {_n(p['M12']['G_end'], 2)}, E constante "
               f"{_yes(p['M12']['efficiency_constant'])}; con un escritor declarado E {_n(p['M12']['with_declared_writer'], 3)}",
    }
    for name in sorted(p, key=lambda k: int(k[1:])):
        rows.append(_row((name, text[name], summary[name], _yes(p[name]["pass"]))))
    return "\n".join(rows)


def render_direcciones(data: dict) -> str:
    d = data["directions"]
    return (f"- Demanda {_list(d['demand']['ratio'], 1)} con la FR fija en {_n(d['demand']['rr'][0], 1)}: W "
            f"{_list(d['demand']['W'], 3)}, PaCO2 {_list(d['demand']['paco2'], 1)}.\n"
            f"- PaCO2 frente a W en {d['paco2_against_w']['points']} puntos de sonda: estrictamente decreciente "
            f"{_yes(d['paco2_against_w']['strictly_decreasing'])}; igual a la referencia / W "
            f"{_yes(d['paco2_against_w']['reference_over_w'])}; la forma docente reproduce W "
            f"{_yes(d['paco2_against_w']['form_matches'])}. Pasa: {_yes(d['pass'])}.")


def render_alto_co2(data: dict) -> str:
    h = data["high_rr_high_paco2"]
    lines = []
    for case, v in h["cases"].items():
        rows = ["| FR intrínseca | Frontera E* | " + " | ".join(f"PaCO2 con E {_n(float(k), 2)}" for k in next(iter(
            v["paco2_by_intrinsic"].values()))) + " |", "|---|---|" + "---|" * len(next(iter(
                v["paco2_by_intrinsic"].values())))]
        for i, by in v["paco2_by_intrinsic"].items():
            rows.append(_row((i, _n(v["boundary_efficiency"][i], 3), *(_n(x, 1) for x in by.values()))))
        lines.append(f"**`{case}`** (FR autoral {v['authored_rr']}, PaCO2 autoral {v['authored_paco2']}):\n\n"
                     + "\n".join(rows))
    for label, c in h["core"].items():
        lines.append(f"- Núcleo, `{label}`: FR {_n(c['rr'], 1)}, disponibilidad {_n(c['availability'], 2)}, E "
                     f"{_n(c['mechanics_efficiency'], 2)}, W {_n(c['W'], 3)}, PaCO2 {_n(c['paco2'], 1)} "
                     f"({_yes(c['pass'])}).")
    lines.append(f"- Clase: **{h['class']}**.")
    return "\n\n".join(lines)


def render_contraste_24f(data: dict) -> str:
    c = data["compensated"]
    rows = ["| FR intrínseca | 24f con E leve | 49m con E baja | Frontera 24f | Frontera 49m |", "|---|---|---|---|---|"]
    for i, r in c["by_intrinsic"].items():
        rows.append(_row((i, _n(r["asthma_24f_mild"], 1), _n(r["asthma_49m_low"], 1), _n(r["boundary_24f"], 3),
                          _n(r["boundary_49m"], 3))))
    return (f"E leve {_n(c['efficiencies']['mild'], 2)}, E baja {_n(c['efficiencies']['low'], 2)} (puntos de la rejilla "
            f"sintética, no seleccionados). FR autoral: 24f {c['authored']['asthma_24f']['rr']}, 49m "
            f"{c['authored']['asthma_49m']['rr']}.\n\n" + "\n".join(rows) + f"\n\nPasa: {_yes(c['pass'])}.")


def render_opioide(data: dict) -> str:
    o = data["opioid"]
    rows = ["| Lectura | FR | Disponibilidad | E | W | PaCO2 |", "|---|---|---|---|---|---|"]
    for k in ("reference", "CENTRAL_DRIVE_FAILURE", "MECHANICAL_VENTILATORY_FAILURE"):
        v = o[k]
        rows.append(_row((k, _n(v["rr"], 1), _n(v["availability"], 2), _n(v["mechanics_efficiency"], 2),
                          _n(v["W"], 3), _n(v["paco2"], 1))))
    a = o["opioid_35m_authored"]
    return ("\n".join(rows) + f"\n\n`opioid_35m` autoral: FR {a['rr']}, PaCO2 {a['paco2']}; E implícita "
            + ", ".join(f"{i}: {_n(v, 3)}" for i, v in a["implied_efficiency"].items())
            + f" (mecánica no reducida). Pasa: {_yes(o['pass'])}.")


def render_regiones(data: dict) -> str:
    r = data["arrival_regions"]
    rows = ["| Caso | FR | PaCO2 | E (12) | E (16) | E (20) | Demanda 1,2 | E con FR del modelo (16) |",
            "|---|---|---|---|---|---|---|---|"]
    for case, v in r["regions"].items():
        b = v["by_intrinsic"]
        rows.append(_row((f"`{case}`", v["authored_rr"], v["authored_paco2"], _n(b["12"], 3), _n(b["16"], 3),
                          _n(b["20"], 3), " – ".join(_n(x, 3) for x in v["demand_sensitivity"]["1.2"]),
                          _n(v["counterfactual_efficiency_at_model_rr"]["16"], 3))))
    o = r["ordering"]
    lines = ["\n".join(rows) + "\n", f"Regla: {r['rule']}.",
             "- (a) graves bajo 24f: " + ", ".join(f"{k} {_yes(v)}" for k, v in o["severe_below_compensated"].items()),
             "- (b) 24f bajo las referencias: " + ", ".join(f"{k} {_yes(v)}" for k, v in
                                                            o["compensated_below_references"].items()),
             "- (c) opioide no reducido: " + ", ".join(f"{k} {_yes(v)}" for k, v in o["opioid_preserved"].items()),
             "- Solapamientos entre FR intrínsecas distintas: " + "; ".join(
                 f"{k}: {'ninguno' if v is None else ' – '.join(_n(x, 3) for x in v)}"
                 for k, v in r["overlaps_across_intrinsic"].items()),
             "- Referencias con E < 1: " + "; ".join(f"{k}: {', '.join(v) if v else 'ninguna'}"
                                                     for k, v in r["references_below_1"].items()),
             f"- Lectura: {r['reading']}.", f"- Clase: **{r['class']}**."]
    return "\n".join(lines)


def render_sin_ancla(data: dict) -> str:
    a = data["no_anchor_absorption"]
    rows = ["| PaCO2 autoral de llegada | Candidato | P2K-2 (apagado) |", "|---|---|---|"]
    rows += [_row((k, _n(v["candidate"], 1), _n(v["p2k2"], 1))) for k, v in a["by_authored_paco2"].items()]
    e = a["edema_candidate_arrival"]
    return ("\n".join(rows) + "\n\n- Referencia del candidato en cada estado: "
            + ", ".join(_n(x, 1) for x in a["references"]) + " mmHg.\n- Edema 58m con el "
            f"candidato encendido y E de referencia: FR del modelo {_n(e['model_rr'], 1)} (autoral "
            f"{_n(e['authored_rr'], 0)}), PaCO2 {_n(e['candidate_paco2'], 1)} frente a {_n(e['authored_paco2'], 0)} "
            "autoral: diferencia "
            f"{_n(e['mismatch_reported'], 1)} mmHg, informada, nunca absorbida.\n- La rama del candidato lee el ancla: "
            f"{_yes(a['candidate_reads_anchor'])}. Pasa: {_yes(a['pass'])}.")


def render_unicidad(data: dict) -> str:
    w = data["w_uniqueness"]
    return (f"- Escritura del canal W rechazada con el candidato: {_yes(w['w_channel_write_refused'])}; un estado que lo "
            f"lleve se lee igual que sin él: {_yes(w['w_channel_inert'])}.\n"
            f"- La FR de `derive` es la de `respiration` (P2P-2): {_yes(w['derive_rr_is_respiration_rr'])}.\n"
            f"- Lector P2K-1 con la fisiología ácido-base apagada (W −0,5 / 0 / 0,5): FR "
            f"{_list(w['p2k1_reader_default_profile'], 1)}; estado: {w['p2k1_status']}.\n"
            f"- El impulso no lee W ni la mecánica: {_yes(not any(w['drive_reads_w_or_mechanics'].values()))}. "
            f"Pasa: {_yes(w['pass'])}.")


def render_estado_extra(data: dict) -> str:
    s = data["no_extra_state"]
    return ("- Campos añadidos: " + "; ".join(f"`{k}`: {', '.join(v)}" for k, v in s["added_fields"].items())
            + f".\n- Canales: {', '.join(s['channels'])} (sin cambios).\n- Nombres prohibidos en las inserciones "
            f"(fatiga, compliancia, resistencia, espacio muerto, volumen corriente, músculo, enfermedad): "
            f"{', '.join(s['forbidden_in_insertions']) or 'ninguno'}.\n- Cinética propia del núcleo: "
            f"{s['core_kinetics']}. Pasa: {_yes(s['pass'])}.")


def render_oxigenacion(data: dict) -> str:
    o = data["oxygenation"]
    return (f"- Estado: **{o['status']}**. La SpO2 no cambia con la mecánica (M10): "
            f"{_yes(o['spo2_unchanged_by_mechanics'])}; la oxigenación no lee W, PaCO2 ni la mecánica: "
            f"{_yes(not any(o['oxygenation_reads_ventilation'].values()))}.")


def render_carga(data: dict) -> str:
    c = data["respiratory_load"]
    return (f"- Estado: **{c['status']}**; definición: {c['definition']}.\n- Factor de frecuencia necesario para W = 1 "
            "con la demanda basal: " + ", ".join(f"E {_n(float(k), 2)} → {_n(v, 2)}" for k, v in
                                                 c["required_frequency_factor_at_baseline_demand"].items())
            + f".\n- Lectores en el núcleo: {', '.join(c['readers']) or 'ninguno'}.")


def render_fc(data: dict) -> str:
    h = data["heart_rate"]
    return (f"- {h['carried_forward']}.\n- La FC lee la respiración: "
            f"{_yes(any(h['hr_reads_respiration'].values()))}. Pasa: {_yes(h['pass'])}.")


def render_parametros(data: dict) -> str:
    p = data["parameter_state"]
    lines = [f"- **{k}:** {v}." for k, v in p["status"].items()]
    lines.append("- Eficiencia de llegada en los casos comprometidos: " + ", ".join(
        f"`{k}` {_n(v, 2)}" for k, v in p["committed_arrival_efficiency"].items()) + ".")
    lines.append("- Candidato encendido en algún perfil comprometido: "
                 f"{_yes(any(p['committed_profiles_on'].values()))}. Pasa: {_yes(p['pass'])}.")
    return "\n".join(lines)


def render_no_regresion(data: dict) -> str:
    n = data["non_regression"]
    lines = ["- Lectura exacta del núcleo de P2Q-2 sobre los cursos de referencia: " + ", ".join(
        f"{k} {_yes(v)}" for k, v in n["exact_reading_p2q2_core"].items()) + ".",
             "- Mecánica constante en 1 en esos cursos: " + _yes(all(n["mechanics_constant"].values())) + ".",
             "- No regresión de P2Q-2 (GI, ACS, edema, P2P-2): " + ", ".join(
                 f"{k} {_yes(v)}" for k, v in n["p2q2_non_regression"].items() if k != "pass") + ".",
             "- Secciones del registro de P2Q-2 reproducidas: " + ", ".join(
                 f"{k} {_yes(v)}" for k, v in n["p2q2_sections"].items()) + ".",
             f"- Pasa: {_yes(n['pass'])}."]
    return "\n".join(lines)


def render_prueba(data: dict) -> str:
    p = data["proof"]
    d = data["design"]
    return (f"- Archivos con inserciones declaradas, probados contra P2Q-2 (`{d['p2q2']['head']}`): "
            + ", ".join(f"`{k}` {_yes(v)}" for k, v in p["proofs"].items())
            + f".\n- Archivos comunes fijados por hash: {len(d['common_at_p2q2'])}, intactos "
              f"{_yes(all(p['common_untouched'].values()))}.\n- Vista de P2Q-2: archivos comunes "
              f"{_yes(all(p['p2q2_common_untouched'].values()))}, digest de congelación de P2Q-2 "
              f"{_yes(p['p2q2_freeze_digest'])}, su prueba contra P2P-2 {_yes(p['p2q2_proof'])}, registro "
              f"{_yes(p['p2q2_record'])}.")


def render_veredicto(data: dict) -> str:
    v = data["readiness"]
    lines = [f"- {_yes(v['criteria'][name])} — {name}" for name in data["design"]["readiness_criteria"]]
    lines.append(f"\n**Veredicto: {v['verdict']}**")
    if v["recommendation"]:
        lines.append(f"\n**Recomendación: {v['recommendation']}**")
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
    parser.add_argument("--data", type=Path, required=True, help="the P2S-2 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
