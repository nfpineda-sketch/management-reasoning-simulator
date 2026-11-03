"""P2O-3 report: the generated blocks of docs/revision/P2O3_REVERSIBILIDAD_L_Y_AUTORIDAD.md.

    python -m clinical_core.lung_water_reference_report --write <document> --data <the P2O-3 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("composicion", "autoridad", "signo_g", "sondas", "acs", "recuperacion", "fc", "parametros", "prueba",
         "bordes", "veredicto")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
PROBES_ES = {"R1": "L = 0 y L_rev = 0: P2O-1 idéntico", "R2": "L > 0: G y SpO2 empeoran",
             "R3": "L < 0 con L_rev = 0: sin crédito", "R4": "L < 0 con L_rev < 0: mejora",
             "R5": "L < L_rev: el crédito se detiene en L_rev", "R6": "subir la FiO2 nunca empeora la SpO2",
             "R7": "escritor de familia y sobrecarga: sólo la familia cambia L",
             "R8": "sin escritor de familia: la sobrecarga común sigue disponible"}
G_ES = {"g_zero_exact": "G = 0 reproduce la llegada exactamente",
        "monotone_in_g": "la SpO2 nunca sube con G (bajar G bajo 0 nunca empeora)",
        "monotone_in_fio2": "la SpO2 nunca baja con la FiO2",
        "bounded": "la mejora es a lo sumo s × |c| y queda en [0, 100]",
        "below_credit_uncredited": "una G por debajo de c no recibe más crédito",
        "positive_credit_refused": "un crédito positivo se rechaza"}


def render_composicion(data: dict) -> str:
    c = data["probes"]["composition"]
    return (f"Regla: **{c['rule']}** (los deltas de L se suman con `fsum` y luego se acotan). En el escenario de "
            f"sobrecarga de ACS, el clon sin autoridad escribe a la vez que el acoplamiento común en "
            f"{c['minutes_with_both']} minutos: L final {_n(c['L_end_non_owning'], 3)}, frente a "
            f"{_n(c['L_end_owning'], 3)} con la autoridad y {_n(c['L_end_common_alone'], 3)} con el acoplamiento "
            f"común solo.")


def render_autoridad(data: dict) -> str:
    a = data["probes"]["authority"]
    return (f"- Declaran la autoridad: {', '.join(f'`{x}`' for x in a['declaring'])} (tipo "
            f"{', '.join(a['declaring_kinds'])}).\n"
            f"- Un evento guionizado que la declara se rechaza: {_yes(a['refused_outside_disease_module'])}.\n"
            f"- Un segundo dueño en la misma corrida se rechaza: {_yes(a['second_owner_refused'])}.\n"
            f"- Una autoridad distinta de la del tipo registrado se rechaza: {_yes(a['registry_mismatch_refused'])}; "
            f"una copia sintética con tipo propio, no registrado, se acepta: {_yes(a['unregistered_probe_accepted'])}.")


def render_signo_g(data: dict) -> str:
    g = data["probes"]["g_sign"]
    d = data["probes"]["direct_g"]
    rows = ["| Propiedad | Cumple |", "|---|---|"] + [f"| {G_ES[k]} | {_yes(g[k])} |" for k in G_ES]
    return ("\n".join(rows) + f"\n\nEscritor directo de G con L = 0 y L_rev = −1: G {_n(d['G'], 2)}, SpO2 "
            f"{_n(d['spo2'], 1)} (sin crédito: {_yes(d['pass'])}).\n\n**Resultado:** `{g['verdict']}`.")


def render_sondas(data: dict) -> str:
    p = data["probes"]["probes"]
    rows = ["| Sonda | Qué prueba | Cumple |", "|---|---|---|"]
    rows += [f"| {k} | {PROBES_ES[k]} | {_yes(data['probes']['pass'][k])} |" for k in PROBES_ES]
    r2, r3, r4, r5, r7, r8 = p["R2"]["end"]["0.0"], p["R3"], p["R4"], p["R5"], p["R7"], p["R8"]
    extra = [
        "",
        f"- **R1:** acoplamiento y oxigenación iguales a P2O-1 en las rejillas; secciones congeladas de P2O-1 "
        f"reproducidas: {', '.join(f'{k} {_yes(v)}' for k, v in p['R1']['p2o1_sections_reproduced'].items())}.",
        f"- **R2:** L {_n(r2['L'], 3)}, G {_n(r2['G'], 3)}, SpO2 {_n(r2['spo2'], 2)}; igual con todo L_rev: "
        f"{_yes(p['R2']['l_rev_irrelevant_above_arrival'])}.",
        f"- **R3:** L {_n(r3['L'], 2)}, G {_n(r3['G'], 2)}, SpO2 {_n(r3['spo2'], 1)}.",
        f"- **R4:** L_rev {_n(r4['l_rev'], 1)}: L {_n(r4['L'], 3)}, G {_n(r4['G'], 3)}, SpO2 {_n(r4['spo2'], 2)}.",
        f"- **R5:** L_rev {_n(r5['l_rev'], 1)}: L {_n(r5['L'], 2)}, G {_n(r5['G'], 2)}, SpO2 {_n(r5['spo2'], 2)} "
        f"(tope {_n(r5['cap_spo2'], 2)}).",
        f"- **R7:** escrituras comunes {r7['common_writes']}; L igual al de la familia sola: "
        f"{_yes(r7['L_equals_family_alone'])}; L final {_n(r7['L_end'], 3)}.",
        f"- **R8:** escrituras comunes {r8['common_writes']}; L final {_n(r8['L_end'], 3)}, G {_n(r8['G_end'], 3)}.",
    ]
    return "\n".join(rows + extra)


def render_acs(data: dict) -> str:
    m, r = data["acs_mapping"], data["acs_representation"]
    fraction = "sin declarar" if m["preload_fraction"] is None else _n(m["preload_fraction"], 2)
    return (f"- `preload_fraction`: {fraction} (declarada: {_yes(m['preload_declared'])}); la VCI "
            f"informa V: {_yes(m['ivc_informs_v'])}; las líneas B no llegan a V: {_yes(m['b_lines_not_in_v'])}; las "
            f"líneas B informan L: {_yes(m['b_lines_inform_l'])}; L_rev en ACS: {_n(m['l_rev_at_acs'], 1)}.\n"
            f"- `pump_reserve` lo leen sólo {', '.join(f'`{x}`' for x in m['pump_reserve_readers'])}; su banda cita "
            f"las líneas B: {_yes(m['pump_reserve_note_cites_b_lines'])}; inerte en ACS bajo la autoridad: "
            f"{_yes(m['pump_reserve_inert_under_authority'])}.\n"
            f"- Llegada: L {_n(r['arrival']['L'], 1)}, G {_n(r['arrival']['G'], 1)}, SpO2 {_n(r['arrival']['spo2'], 1)}.\n"
            f"- Congestión (sin tratar, 120 min): L {_n(r['congestion']['L'], 3)}, G {_n(r['congestion']['G'], 3)}, "
            f"SpO2 {_n(r['congestion']['spo2'], 2)}.\n"
            f"- Descongestión (sonda guionizada, L_rev {_n(r['decongestion']['l_rev'], 1)}): L "
            f"{_n(r['decongestion']['L'], 2)}, G {_n(r['decongestion']['G'], 2)}, SpO2 "
            f"{_n(r['decongestion']['spo2'], 2)} (tope {_n(r['decongestion']['cap'], 2)}); V sin cambio: "
            f"{_yes(r['v_unchanged'])}; P sin cambio: {_yes(r['p_unchanged'])}.")


def render_recuperacion(data: dict) -> str:
    rows = ["| Recuperación | P al reperfundir | P final | L al reperfundir | L máximo | L final | Caída máx./min "
            "| Acotada por el aclaramiento |", "|---|---|---|---|---|---|---|---|"]
    for key, v in data["partial_recovery"].items():
        if isinstance(v, dict):
            rows.append(f"| {key} | {_n(v['P_at_reperfusion'], 3)} | {_n(v['P_end'], 3)} | {_n(v['L_at_reperfusion'], 3)} "
                        f"| {_n(v['L_peak'], 3)} | {_n(v['L_end'], 3)} | {_n(v['max_fall_per_min'], 5)} "
                        f"| {_yes(v['fall_bounded_by_clearance'])} |")
    return "\n".join(rows)


def render_fc(data: dict) -> str:
    h = data["heart_rate"]
    rows = ["| Llegada | Objetivo con pulmón de llegada | Objetivo mejorado | SpO2 mejorada | Término de hipoxemia |",
            "|---|---|---|---|---|"]
    rows += [f"| {k} | {_n(v['target_at_arrival_lungs'], 3)} | {_n(v['target_improved'], 3)} | "
             f"{_n(v['spo2_improved'], 1)} | {_n(v['hypoxaemia_term'], 1)} |" for k, v in h["rows"].items()]
    return "\n".join(rows) + f"\n\nP de la sonda {_n(h['pump'], 1)}; umbral {_n(h['threshold'], 0)}."


def render_parametros(data: dict) -> str:
    p = data["parameters"]
    return ("\n".join(f"- **{k}**: {v}" for k, v in p["status"].items())
            + f"\n\nk, s y r en `None` por defecto: {_yes(all(p['k_s_r_unset'].values()))}; L_rev por defecto "
              f"{_n(p['l_rev_default'], 1)} y en ACS {_n(p['l_rev_at_acs'], 1)}.")


def render_prueba(data: dict) -> str:
    p = data["proof"]
    return ("- Archivos P2O-1 reconstruidos byte a byte: "
            + ", ".join(f"`{k}` {_yes(v)}" for k, v in p["proofs"].items())
            + f".\n- Digest congelado de P2O-1 reproducido por la vista: {_yes(p['p2o1_freeze_digest'])}.\n"
              f"- Registro de P2O-1 intacto: {_yes(p['p2o1_record'])}.\n"
              f"- GI: O12 de P2O-1 reproducido {_yes(data['gi']['o12_reproduced'])}; otros dueños de L: "
              f"{len(data['gi']['other_owners'])}.")


def render_bordes(data: dict) -> str:
    e = data["probes"]["edges"]
    x, z = e["non_arrival_start_credit"], e["zero_gain_owner"]
    return (f"- La guarda de G detiene la corrida con L_rev < 0: {_yes(e['g_guard_stops_with_l_rev'])}; con L_rev = 0 "
            f"la sostiene como en P2O-1: {_yes(e['g_guard_clamps_at_default'])}.\n"
            f"- Un minuto que cruza la llegada con L_rev < 0 se registra como cruce: {_yes(e['across_label'])}.\n"
            f"- Límite conocido (inicio fuera de la llegada, L = L_rev con G = 0, escritor directo de G): G "
            f"{_n(x['G'], 2)}, SpO2 {_n(x['spo2'], 1)} frente a {_n(x['arrival_spo2'], 1)} de llegada.\n"
            f"- Dueño con ganancia 0 en el escenario de sobrecarga: L final {_n(z['L_end'], 3)}, frente a "
            f"{_n(z['L_end_common_alone'], 3)} con el acoplamiento común solo.")


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    rows = ["| Criterio | Cumple |", "|---|---|"] + [f"| {k} | {_yes(x)} |" for k, x in v["criteria"].items()]
    return (("\n".join(rows) + f"\n\n**Veredicto:** `{v['verdict']}`.\n\n**Recomendación:** "
             f"`{data['recommendation']}` (no se inicia)."))


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the P2O-3 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
