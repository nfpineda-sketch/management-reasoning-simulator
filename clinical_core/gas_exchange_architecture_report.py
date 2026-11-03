"""P2O-1 report: the generated blocks of docs/revision/P2O1_INTERCAMBIO_GASEOSO_COMUN.md.

    python -m clinical_core.gas_exchange_architecture_report --write <document> --data <the P2O-1 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("decisiones", "auditoria", "semantica", "formas", "oxigenacion", "region", "sondas", "familias", "acs",
         "generacion", "gi", "capas", "fronteras", "prueba", "veredicto", "recomendacion", "diferidos")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FROZEN = "(texto congelado, en inglés)"
PROBES_ES = {"O1": "L = 0 y G = 0: la oxigenación de llegada se conserva", "O2": "L empeora: G no mejora",
             "O3": "G empeora con la ventilación fija: la oxigenación empeora",
             "O4": "G empeora con la PaCO2 fija: la oxigenación empeora sin pasar por la ventilación",
             "O5": "FiO2 sube con G leve: la oxigenación mejora",
             "O6": "FiO2 sube con G grave: la mejora es incompleta y nunca paradójica",
             "O7": "cambia la FR con W y G fijos: la oxigenación no cambia",
             "O8": "cambia W con G fijo: cambia la PaCO2, no G ni la SpO2",
             "O9": "sube la carga ácida con G fijo: G no cambia", "O10": "suben el lactato y D con G fijo: G no cambia",
             "O11": "L mejora hacia la llegada: G no empeora", "O12": "GI con L = 0: lectura idéntica"}
FAMILIES_ES = {"cardiogenic": "cardiogénica", "pneumonia": "neumonía", "asthma": "asma",
               "opioid": "hipoventilación por opioide", "pulmonary_embolism": "TEP", "anaphylaxis": "anafilaxia",
               "metabolic_acidosis": "acidosis metabólica aislada"}
PARAM_ES = {"lung_water_to_gas_exchange_gain": "k (G por unidad de L)",
            "spo2_per_gas_exchange_unit": "s (puntos de SpO2 por unidad de G)",
            "oxygen_response_loss_per_gas_exchange_unit": "r (pérdida de la respuesta al O2 por unidad de G)"}


def _items(mapping: dict) -> str:
    return "\n".join(f"- **{k}**: {v}" for k, v in mapping.items())


def render_decisiones(data: dict) -> str:
    d = data["design"]
    return (f"Decisiones de la docencia {FROZEN}:\n\n" + _items(d["decided"]) + "\n\nBrechas que se arrastran: "
            + ", ".join(f"`{v}`" for v in d["carried"].values()) + ".")


def render_auditoria(data: dict) -> str:
    rows = ["| Magnitud | Escritores | Lectores | Llegada | Tipo |", "|---|---|---|---|---|"]
    for name, item in data["design"]["audit"].items():
        rows.append(f"| {name} | {item['writers']} | {item['readers']} | {item['arrival']} | {item['kind']} |")
    return f"Semántica ejecutable antes de P2O-1 {FROZEN}:\n\n" + "\n".join(rows) + \
        f"\n\nCompatibilidad {FROZEN}: {data['design']['compatible']}."


def render_semantica(data: dict) -> str:
    d = data["design"]
    return (f"Antes {FROZEN}:\n\n" + _items(d["semantics_before"]) + f"\n\nAceptada {FROZEN}:\n\n"
            + _items(d["semantics"]))


def render_formas(data: dict) -> str:
    rows = ["| Forma | Expresión | Estado | Por qué |", "|---|---|---|---|"]
    for name, item in data["design"]["forms"].items():
        rows.append(f"| {name} | `{item['form']}` | {item['status']} | {item['why']} |")
    return "\n".join(rows) + f"\n\nDecisión {FROZEN}: {data['design']['form_decision']}."


def render_oxigenacion(data: dict) -> str:
    d = data["design"]
    return f"Estructura G → oxigenación {FROZEN}:\n\n" + _items(d["oxygenation"]) + \
        f"\n\nInteracción con la FiO2 {FROZEN}: {d['fio2']}."


def render_region(data: dict) -> str:
    d = data["design"]
    lines = [f"- **{PARAM_ES[k]}**: referencia {_n(d['reference'][k], 2)}; 1-D " +
             ", ".join(_n(v, 2) for v in d["one_d"][k]) + f"; por defecto `{d['parameter_status'][k]['default']}`, "
             f"en sondas `{d['parameter_status'][k]['probes']}`, aprobado: {_yes(d['parameter_status'][k]['approved'])}"
             for k in d["reference"]]
    return "\n".join(lines) + f"\n\nIdentificabilidad {FROZEN}: {d['identifiability']}."


def render_sondas(data: dict) -> str:
    p = data["probes"]
    rows = ["| Sonda | Qué prueba | Cumple |", "|---|---|---|"]
    rows += [f"| {k} | {PROBES_ES[k]} | {_yes(v)} |" for k, v in p["pass"].items()]
    o2 = p["O2"]["rows"]
    o11 = p["O11"]
    extra = [
        "",
        "- **O2:** con k = " + ", ".join(f"{_n(r['k'], 1)} → G final {_n(r['G_end'], 3)} (L {_n(r['L_end'], 3)}, "
                                         f"SpO2 {_n(r['spo2_end'], 2)})" for r in o2) + "; único escritor de G: el "
        "acoplamiento común.",
        f"- **O6:** con r > 0 la primera subida de FiO2 rinde menos con G grave en todos los puntos: "
        f"{_yes(p['O5_O6']['attenuated_when_r_positive'])}.",
        f"- **O8:** {p['O8']['deferred']}.",
        f"- **O9 / O10:** carga ácida {_n(p['O9_O10']['burden'][0], 2)} → {_n(p['O9_O10']['burden'][1], 2)}, D "
        f"{_n(p['O9_O10']['D'][0], 1)} → {_n(p['O9_O10']['D'][1], 1)}; G máximo {_n(p['O9_O10']['G_max'], 3)}.",
        f"- **O11:** L pico {_n(o11['L_peak'], 3)} → {_n(o11['L_end'], 3)}; G pico {_n(o11['G_peak'], 3)} → "
        f"{_n(o11['G_end'], 3)}; con L bajo la llegada (mínimo {_n(o11['below_arrival_L_min'], 2)}) G queda en "
        + ", ".join(_n(v, 1) for v in o11["below_arrival_G"]) + ".",
        "- **O12:** " + f"{sum(r['identical'] for r in p['O12']['rows'])} de {len(p['O12']['rows'])} cursos GI "
        "idénticos (dos casos × cuatro escenarios × perfil certificado y con ácido-base), L máximo "
        + _n(max(r["L_max"] for r in p["O12"]["rows"]), 1) + ".",
    ]
    return "\n".join(rows + extra)


def render_familias(data: dict) -> str:
    x = data["cross_family"]
    rows = ["| Familia | Entradas (sintéticas) | L máx | G máx | SpO2 0 → 60 | con O2 0,6 | PaCO2 0 → 60 (ref.) | FR "
            "(ref.) | Cumple |", "|---|---|---|---|---|---|---|---|---|"]
    for name, r in x["rows"].items():
        rows.append(f"| {FAMILIES_ES[name]} | {', '.join(r['writes'])} | {_n(r['L_max'], 2)} | {_n(r['G_max'], 2)} | "
                    f"{_n(r['first']['spo2'], 1)} → {_n(r['last']['spo2'], 1)} | {_n(r['with_oxygen']['spo2'], 1)} | "
                    f"{_n(r['first']['paco2'], 1)} → {_n(r['last']['paco2'], 1)} ({_n(r['reference_paco2'], 1)}) | "
                    f"{_n(r['first']['rr'], 1)} ({_n(r['reference_rr'], 1)}) | {_yes(x['checks'][name])} |")
    return "\n".join(rows) + (f"\n\nEntradas distintas por familia: {_yes(x['distinct_inputs'])}. "
                              f"Nota {FROZEN}: {x['single_g_note']}.")


ACS_KEYS = ("L", "G", "spo2", "delivery_index", "deficit", "D", "lactate", "hr", "paco2")


def _acs_row(r: dict) -> str:
    return " | ".join(_n(r.get(k), 3 if k in ("L", "G", "delivery_index", "deficit") else 1) for k in ACS_KEYS)


def render_acs(data: dict) -> str:
    a = data["acs"]
    head = "| Curso | Minuto | L | G | SpO2 | Aporte | Déficit | D | Lactato | FC | PaCO2 |\n|---|---|---|---|---|---|---|---|" \
           "---|---|---|"
    rows = [head]
    for r in a["control"]:
        rows.append(f"| P2N-2 sin P2O-1 | {r['minute']} | {_acs_row(r)} |")
    reference = [run for run in a["runs"].values()
                 if run["point"] == data["design"]["reference"]][0]
    for r in reference["rows"]:
        rows.append(f"| referencia | {r['minute']} | {_acs_row(r)} |")
    for r in a["oxygen"]["rows"][2:]:
        rows.append(f"| referencia + O2 {_n(a['oxygen']['order']['fio2'], 2)} desde el min "
                    f"{a['oxygen']['order']['minute']} | {r['minute']} | {_acs_row(r)} |")
    sens = ["", "Sensibilidad 1-D (SpO2 y aporte a los 120 min):", ""]
    for run in a["runs"].values():
        last = run["rows"][-1]
        sens.append("- " + ", ".join(f"{PARAM_ES[k].split(' ')[0]} {_n(v, 2)}" for k, v in run["point"].items())
                    + f": SpO2 {_n(last['spo2'], 1)}, aporte {_n(last['delivery_index'], 3)}, D {_n(last['D'], 1)}; "
                    f"G = k·L {_yes(run['g_is_k_l'])}, aporte ≤ control {_yes(run['delivery_not_above_control'])}, "
                    f"D ≥ control {_yes(run['d_not_below_control'])}, lactato ≥ control "
                    f"{_yes(run['lactate_not_below_control'])}")
    legacy = ", ".join(f"{m} min {v}" for m, v in a["legacy_reference_only"].items())
    return "\n".join(rows + sens) + (f"\n\nLlegada exacta (SpO2 94): {_yes(a['arrival_exact'])}. Legado (sólo "
                                     f"referencia, nunca objetivo): SpO2 {legacy}. Cumple: {_yes(a['pass'])}.")


def render_generacion(data: dict) -> str:
    g = data["congestion_generation"]
    lines = [f"- {_n(float(v), 0)} mL: L máximo {_n(item['L_max'], 3)}, G máximo {_n(item['G_max'], 3)}, posición de "
             f"precarga máxima {_n(item['position_max'], 3)} (rodilla {_n(item['knee'], 2)})"
             for v, item in g["fluid"].items()]
    return "\n".join(lines) + f"\n\nBrecha de generación común de congestión abierta: {_yes(g['gap_open'])}."


def render_gi(data: dict) -> str:
    rows = ["| Caso | Escenario | Perfil | Idéntico | L máx | Escrituras de G |", "|---|---|---|---|---|---|"]
    rows += [f"| {r['case']} | {r['scenario']} | {r['profile']} | {_yes(r['identical'])} | {_n(r['L_max'], 1)} | "
             f"{r['G_writes']} |" for r in data["probes"]["O12"]["rows"]]
    return "\n".join(rows)


def render_capas(data: dict) -> str:
    c = data["layers"]
    rows = ["| G | SpO2 | SpO2 que lee la encefalopatía | señal de hipoxemia (rampa sintética) | déficit que lee el "
            "colapso |", "|---|---|---|---|---|"]
    rows += [f"| {_n(r['G'], 1)} | {_n(r['spo2'], 1)} | {_n(r['enc_spo2'], 1)} | {_n(r['hypoxaemia_signal'], 3)} | "
             f"{_n(r['collapse_deficit'], 4)} |" for r in c["rows"]]
    return "\n".join(rows) + (f"\n\nConciencia coherente: {_yes(c['consciousness'])}; colapso sin cambios y sólo por "
                              f"el aporte: {_yes(c['collapse'])} (`{c['direct_spo2_collapse']}`); módulos sin cambios: "
                              + ", ".join(f"{k} {_yes(v)}" for k, v in c["unchanged"].items()) + ".")


def render_fronteras(data: dict) -> str:
    b = data["boundaries"]
    free = [k for k, v in b["respiration_and_downstream_read_no_L_or_G"].items() if v]
    return "\n".join([
        f"- Funciones de `derived.py` que leen G: {', '.join(b['readers_in_derived']['G'])}; que leen L: "
        f"{', '.join(b['readers_in_derived']['L'])}.",
        f"- No leen L ni G: {', '.join(free)}; `ventilation.py`: {_yes(b['ventilation_reads_no_L_or_G'])}.",
        f"- `oxygenation` lee L, W, D, lactato, FR, PaCO2, ventilación o carga ácida: "
        f"{', '.join(b['oxygenation_reads']) or 'nada de eso'}.",
        f"- Escritores de G en el núcleo: {b['core_G_writers']} (el acoplamiento); módulos de familia que escriben G: "
        f"{', '.join(b['family_modules_writing_G']) or 'ninguno'}.",
        f"- Términos de enfermedad en las inserciones del núcleo: {', '.join(b['disease_terms_in_core_insertions']) or 'ninguno'}.",
        f"- Pasa: {_yes(b['pass'])}."])


def render_prueba(data: dict) -> str:
    p = data["proof"]
    return (f"- Los archivos del núcleo son los de P2N-2 byte a byte sin las inserciones declaradas: "
            + ", ".join(f"`{k}` {_yes(v)}" for k, v in p["proofs"].items())
            + f".\n- Mapa de dependencias P2N-2 para los paquetes cerrados: {p['files']} archivos, digest "
              f"`{p['digest'][:12]}…`.\n- Registro P2N-2 intacto: {_yes(p['p2n2_record'])}.")


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    rows = ["| Criterio | Cumple |", "|---|---|"] + [f"| {k} | {_yes(x)} |" for k, x in v["criteria"].items()]
    rows += [f"| {k} | {_yes(x)} |" for k, x in v["extra"].items()]
    return "\n".join(rows) + f"\n\n**Veredicto:** `{v['verdict']}`."


def render_recomendacion(data: dict) -> str:
    return (f"**Recomendación:** `{data['recommendation']}`.\n\nRegla {FROZEN}: "
            f"{data['design']['recommendation_rule']}.")


def render_diferidos(data: dict) -> str:
    return f"Diferido o no representado {FROZEN}:\n\n" + _items(data["design"]["deferred"])


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the P2O-1 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
