"""P2S-3 report: the generated blocks of docs/revision/P2S3_ASMA_SOMBRA.md.

    python -m clinical_core.asthma_migration_report --write <document> --data <the P2S-3 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("caso", "llegada", "escritor", "contraste", "curso", "alivio", "oxigeno", "g_directa", "impulso", "fc",
         "conciencia", "colapso", "legado", "no_regresion", "prueba", "veredicto")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
PRIMARY, SECONDARY = "asthma_49m", "asthma_24f"
POINTS = ("lower", "midpoint", "upper")
POINT_NAMES = {"lower": "FR intrínseca 12", "midpoint": "16", "upper": "20"}


def _row(values) -> str:
    return "| " + " | ".join(str(v) for v in values) + " |"


def render_caso(data: dict) -> str:
    lines = []
    for name, c in data["case"]["cases"].items():
        t = c["truth"]
        lines.append(f"- **`{name}`:** «{t['diagnosis']}». PA {t['sbp']}/{t['dbp']} (PAM {_n(c['map'], 1)}), FC {t['hr']} "
                     f"({t['rhythm']}), SpO2 {t['spo2']} % aire ambiente, FR {t['respiratory_rate']}, trabajo respiratorio "
                     f"«{t['work_of_breathing']}», «{t['mental_status']}», {t['temperature_c']} °C, glucemia "
                     f"{t['glucose_mg_dl']}. Gases {t['abg_ph']} / PaCO2 {t['abg_paco2']} / PaO2 {t['abg_pao2']}, HCO3 "
                     f"{t['abg_hco3']}; lactato {t['lactate_mmol_l']}.\n"
                     f"  - Flujo pico: {c['peak_flow']}. Exploración: «{t['respiratory_exam']}». POCUS: «{t['pocus_lungs']}»; "
                     f"radiografía «{t['chest_xray']}».\n"
                     f"  - Antes de llegar: «{' '.join(t['medications'])}». Tratamientos definitivos autorales: "
                     f"{', '.join(t['definitive_actions'])}.")
    c = data["case"]
    lines.append(f"- **Regla de selección:** {c['selection_rule']}.\n- **Observaciones posteriores:** "
                 f"{c['later_observations']}.\n- **Comportamiento heredado (sólo referencia):** {c['legacy_constants']}.\n"
                 f"- **Derivado del modelo:** {c['model_derived']}.\n- Verdad suficiente: {_yes(c['available'])}.")
    return "\n".join(lines)


def render_llegada(data: dict) -> str:
    a = data["arrival"]
    rows = ["| Caso | Punto | FR intrínseca | E | FR del núcleo | FR autoral | W | PaCO2 del núcleo | PaCO2 autoral | "
            "PaCO2 con la FR autoral | pH | SpO2 |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, c in a["cases"].items():
        for point in POINTS:
            r = c["points"][point]
            rows.append(_row((f"`{name}`", point, _n(r["intrinsic_rr"], 0), _n(r["mechanics_efficiency"], 3),
                              _n(r["rr"], 1), c["authored"]["rr"], _n(r["W"], 3), _n(r["paco2"], 1),
                              c["authored"]["paco2"], _n(r["paco2_at_authored_rr"], 1), _n(r["ph"], 3),
                              _n(r["spo2"], 1))))
    return ("\n".join(rows) + "\n\n- Banda FAMILY_CANDIDATE de la eficiencia de llegada: " + "; ".join(
        f"`{n}` {_n(c['band']['lower'], 3)} – {_n(c['band']['upper'], 3)} (punto medio {_n(c['band']['midpoint'], 3)})"
        for n, c in a["cases"].items()) + f". Regla: {next(iter(a['cases'].values()))['band']['rule']}.\n"
            f"- La PaCO2 de llegada del núcleo difiere de la autoral por el cociente FR autoral / FR del núcleo, y con la "
            f"FR autoral el mapeo devuelve la PaCO2 autoral. Ambas cosas son identidades del mapeo (la E se invierte de la "
            f"FR y la PaCO2 autorales), no evidencia de que el núcleo represente la llegada: el núcleo no la representa "
            f"(COMMON_DRIVE_GAP). «Llegada coherente» de la regla congelada: {_yes(a['mapping_coherent'])}.")


def render_escritor(data: dict) -> str:
    w = data["writer"]
    return (f"- Palabras de `Contribution` en el escritor: {', '.join(w['contribution_keywords'])}; nombres prohibidos: "
            f"{', '.join(w['forbidden_names']) or 'ninguno'}; deltas de canal: {w['deltas']}.\n"
            f"- Escribe {w['writes']} por minuto con la tasa media; con tasa 0 no escribe nada "
            f"({_yes(w['zero_rate_writes_nothing'])}); registrado {_yes(w['registered'])}, módulo de enfermedad "
            f"{_yes(w['disease_module'])}.\n- Rechazos: " + ", ".join(f"{k} {_yes(v)}" for k, v in w["refused"].items())
            + f".\n- Pasa: {_yes(w['pass'])}.")


def render_contraste(data: dict) -> str:
    c = data["contrast"]
    keys = ("mechanics_ordered", "paco2_ordered_in_core", "primary_hypercapnic_in_core",
            "secondary_hypocapnic_at_authored_rr", "secondary_hypocapnic_in_core")
    labels = {"mechanics_ordered": "E del 49m menor que la del 24f",
              "paco2_ordered_in_core": "PaCO2 del núcleo: 49m mayor que 24f",
              "primary_hypercapnic_in_core": "49m hipercápnico en el núcleo",
              "secondary_hypocapnic_at_authored_rr": "24f hipocápnico con su FR autoral",
              "secondary_hypocapnic_in_core": "24f hipocápnico con la FR del núcleo"}
    rows = ["| Comprobación | 12 | 16 | 20 |", "|---|---|---|---|"]
    for k in keys:
        rows.append(_row((labels[k], *(_yes(c[k][p]) for p in POINTS))))
    return ("\n".join(rows) + f"\n\n- Solapamiento de las bandas: {_n(c['band_overlap'][0], 3)} – "
            f"{_n(c['band_overlap'][1], 3)}.\n- Compensación del 24f: {c['secondary_compensation']}.\n- Pasa: "
            f"{_yes(c['pass'])}.")


def render_curso(data: dict) -> str:
    u = data["untreated"]
    lines = []
    for name in (PRIMARY, SECONDARY):
        rows = ["| Empeoramiento por hora | Minuto | E | FR | W | PaCO2 | pH | SpO2 | FC | D | Lactato | Conciencia |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for rate, v in u[name].items():
            for m in ("0", "60", "120"):
                r = v["at"][m]
                rows.append(_row((_n(float(rate) * 60, 2), m, _n(r["mechanics_efficiency"], 3), _n(r["rr"], 1),
                                  _n(r["W"], 3), _n(r["paco2"], 1), _n(r["ph"], 3), _n(r["spo2"], 1), _n(r["hr"], 1),
                                  _n(r["D"], 2), _n(r["lactate"], 2), r["consciousness_level"])))
        ok = all(all(v["only_mechanics_moves"].values()) and v["states_identical_but_mechanics"] and
                 all(v["directions"].values()) for v in u[name].values())
        lines.append(f"**`{name}`** (sólo cambia la ventilación, y en la dirección exigida: {_yes(ok)}):\n\n"
                     + "\n".join(rows))
    return "\n\n".join(lines) + f"\n\nPasa: {_yes(u['pass'])}."


def render_alivio(data: dict) -> str:
    r = data["relief"]
    rows = ["| Minuto | E sin alivio | E con alivio | W sin | W con | PaCO2 sin | PaCO2 con |", "|---|---|---|---|---|---|---|"]
    for m, v in sorted(r["at"].items(), key=lambda kv: int(kv[0])):
        rows.append(_row((m, _n(v["plain"]["mechanics_efficiency"], 3), _n(v["relieved"]["mechanics_efficiency"], 3),
                          _n(v["plain"]["W"], 3), _n(v["relieved"]["W"], 3), _n(v["plain"]["paco2"], 1),
                          _n(v["relieved"]["paco2"], 1))))
    return ("\n".join(rows) + f"\n\n- FR, SpO2 y FC sin cambio: {_yes(r['rr_spo2_hr_unchanged'])}.\n- {r['status']}.\n"
            f"- Pasa: {_yes(r['pass'])}.")


def render_oxigeno(data: dict) -> str:
    o = data["oxygen"]
    minutes = sorted(o["room_air"], key=int)
    rows = ["| FiO2 | " + " | ".join(f"SpO2 min {m}" for m in minutes) + " |", "|---|" + "---|" * len(minutes)]
    rows.append(_row(("0,21", *(_n(o["room_air"][m], 1) for m in minutes))))
    for f, v in o["fio2"].items():
        rows.append(_row((_n(float(f), 2), *(_n(v[m], 1) for m in minutes))))
    return ("\n".join(rows) + f"\n\n- La SpO2 sube con la FiO2: {_yes(o['spo2_rises_with_fio2'])}; la PaCO2 y la FR no "
            f"cambian con el O2: {_yes(o['paco2_rr_unchanged_by_oxygen'])}; función de O2 de la familia: "
            f"{_yes(o['family_oxygen_function'])}. Pasa: {_yes(o['pass'])}.")


def render_g_directa(data: dict) -> str:
    g = data["direct_g"]
    rows = ["| Caso | PaO2 | PaCO2 | PAO2 (diagnóstico) | Gradiente A-a | Pérdida alveolar hipoventilatoria |",
            "|---|---|---|---|---|---|"]
    for name, v in g["cases"].items():
        rows.append(_row((f"`{name}`", v["pao2"], v["paco2"], _n(v["alveolar_po2"], 1), _n(v["a_a_gradient"], 1),
                          _n(v["hypoventilatory_alveolar_loss"], 1))))
    return (f"- {g['status']}.\n- Escrituras de G: {g['g_writes']}; de L: {g['l_writes']}; G y L en 0: "
            f"{_yes(g['G_L_stay_zero'])}.\n\n" + "\n".join(rows) + f"\n\n- {g['diagnostic_only']}.\n- {g['unexplained']}.\n"
            f"- Pasa: {_yes(g['pass'])}.")


def render_impulso(data: dict) -> str:
    d = data["drive"]
    rows = ["| Caso | FR autoral | Impulso ácido | FR (hipoxémico UNSET) | Impulso hipoxémico sintético | FR (sintético) | "
            "Disponibilidad |", "|---|---|---|---|---|---|---|"]
    for name, v in d["cases"].items():
        rows.append(_row((f"`{name}`", _n(v["authored_rr"], 0), _n(v["unset"]["acid"], 2), _n(v["unset"]["rr"], 1),
                          _n(v["synthetic_hypoxaemic"]["hypoxaemic"], 2), _n(v["synthetic_hypoxaemic"]["rr"], 1),
                          _n(v["availability"], 2))))
    return ("\n".join(rows) + f"\n\n- P2P-2 sin cambios (hipoxémico UNSET, disponibilidad 1, ganancia ácida común): "
            f"{_yes(d['unchanged'])}; el impulso sintético crece estructuralmente: {_yes(d['synthetic_grows'])}.\n"
            f"- {d['classification']}.")


def render_fc(data: dict) -> str:
    h = data["heart_rate"]
    rows = ["| Caso | Autoral | Predicha | Brecha | Predicha en la banda baja / media / alta | β-agonista previo |",
            "|---|---|---|---|---|---|"]
    for name, v in h["cases"].items():
        rows.append(_row((f"`{name}`", _n(v["authored"], 0), _n(v["predicted"], 1), _n(v["mismatch_bpm"], 1),
                          " / ".join(_n(v["predicted_over_bands"][p], 1) for p in POINTS),
                          _yes(v["prehospital_beta_agonist"]))))
    return ("\n".join(rows) + f"\n\n- {h['classification']}.\n- Ganancias intactas: {_yes(h['gains_untouched'])}.")


def render_conciencia(data: dict) -> str:
    c = data["consciousness"]
    minutes = sorted(c["core_level"], key=int)
    return (f"- Autoral: 49m «{c['authored_49m']}», 24f «{c['authored_24f']}».\n- 49m con la tasa media: nivel "
            + ", ".join(f"min {m}: {c['core_level'][m]}" for m in minutes) + "; PaCO2 "
            + ", ".join(f"{_n(c['paco2'][m], 1)}" for m in minutes) + f".\n- {c['reading']}.")


def render_colapso(data: dict) -> str:
    c = data["collapse"]
    return (f"- Máximo se mantiene: {_yes(c['max_holds'])}; UNSET es cota inferior: {_yes(c['unset_is_lower_bound'])}; "
            f"la mecánica llega al gasto: {_yes(c['mechanics_reach_output'])}; sin regla de familia: "
            f"{_yes(c['no_family_rule'])}.\n- {c['status']}.")


def render_legado(data: dict) -> str:
    lc = data["legacy_comparison"]
    rows = ["| Minuto | Legado FR | Legado SpO2 | Legado FC | Legado conciencia | Núcleo FR | Núcleo SpO2 | Núcleo FC | "
            "Núcleo PaCO2 |", "|---|---|---|---|---|---|---|---|---|"]
    for m, v in sorted(lc["rows"].items(), key=lambda kv: int(kv[0])):
        leg, core = v["legacy"], v["core"]
        rows.append(_row((m, leg.get("respiratory_rate"), leg.get("spo2"), leg.get("hr"), leg.get("mental_status"),
                          _n(core["rr"], 1), _n(core["spo2"], 1), _n(core["hr"], 1), _n(core["paco2"], 1))))
    return ("\n".join(rows) + "\n\n" + "\n".join(f"- **{k}:** {v}." for k, v in lc["classes"].items())
            + f"\n- Usado para parámetros: {_yes(lc['used_for_parameters'])}.")


def render_no_regresion(data: dict) -> str:
    n = data["non_regression"]
    return ("- Registro de P2S-2 reproducido: " + ", ".join(f"{k} {_yes(v)}" for k, v in n.items()
                                                         if k not in ("common_files_untouched", "pass"))
            + f".\n- Archivos comunes en sus bytes de P2S-2: {_yes(all(n['common_files_untouched'].values()))}. Pasa: "
              f"{_yes(n['pass'])}.")


def render_prueba(data: dict) -> str:
    p = data["proof"]
    d = data["design"]
    return (f"- Tuplas probadas contra P2S-2 (`{d['p2s2']['head']}`): "
            + ", ".join(f"`{k}` {_yes(v)}" for k, v in p["proofs"].items())
            + f".\n- Archivos comunes fijados por hash: {len(d['common_at_p2s2'])}, intactos "
              f"{_yes(all(p['common_untouched'].values()))}.\n- Vista de P2S-2: digest de congelación "
              f"{_yes(p['p2s2_freeze_digest'])}, su prueba contra P2Q-2 {_yes(p['p2s2_proof'])}, registro "
              f"{_yes(p['p2s2_record'])}.")


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    lines = [f"- {_yes(v['criteria'][name])} — {name}" for name in data["design"]["verdict_criteria"]]
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
    parser.add_argument("--data", type=Path, required=True, help="the P2S-3 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
