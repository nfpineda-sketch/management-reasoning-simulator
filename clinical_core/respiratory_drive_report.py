"""P2P-2 report: the generated blocks of docs/revision/P2P2_IMPULSO_RESPIRATORIO_COMUN.md.

    python -m clinical_core.respiratory_drive_report --write <document> --data <the P2P-2 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("auditoria", "sondas", "absoluta", "edema", "opioide", "acidosis", "aguas_abajo", "limites", "no_regresion",
         "prueba", "preparacion")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}


def _by_minute(rows: dict) -> list:
    return sorted(rows.items(), key=lambda item: int(item[0]))


def render_auditoria(data: dict) -> str:
    a = data["audit"]
    r = a["reads"]
    return (f"- `respiration` de P2P-1 lee SpO2: {_yes(r['respiration_reads_spo2'])}; lee W: "
            f"{_yes(r['respiration_reads_W'])}; términos del impulso: {', '.join(r['drive_terms'])}; "
            f"`rate_from_drive` lee una disponibilidad: {_yes(r['rate_reads_availability'])}.\n"
            f"- La vía P2K-1 lee W: {_yes(r['p2k1_reads_W'])} (factor de depresión `{r['p2k1_depression_factor']}`).\n"
            f"- **Clasificación:** candidata P2K-2 `{a['classification']['p2k2_candidate']}`; vía P2K-1 "
            f"`{a['classification']['p2k1_path']}`.")


def render_sondas(data: dict) -> str:
    p = data["probes"]
    d14 = (f"D1 FR {_n(p['D1']['expressed_rr'], 2)} (intrínseca {_n(p['D1']['baseline_rr'], 1)}); D2 "
           f"{_n(p['D2']['expressed_rr'], 2)}; D3 {_n(p['D3']['expressed_rr'], 2)}; D4 {_n(p['D4']['expressed_rr'], 2)} "
           f"(subaditiva: {_yes(p['D4']['sub_additive'])})")
    d5 = ", ".join(f"{_n(a, 2)} → {_n(rr, 2)}" for a, rr in zip(p["D5"]["availability"], p["D5"]["expressed_rr"]))
    d67 = "; ".join(f"{k}: disponibilidad 1 → {_n(p[k]['full_availability_rr'], 2)}, {_n(p[k]['availability'], 2)} → "
                    f"{_n(p[k]['depressed_rr'], 2)}, con un impulso enorme → {_n(p[k]['depressed_rr_any_drive'], 2)} "
                    f"(cota {_n(p[k]['bound_rr'], 2)}; disponibilidad que acota todo impulso a la intrínseca "
                    f"≤ {_n(p[k]['uniform_bound_availability'], 3)})" for k in ("D6", "D7"))
    d9 = ", ".join(f"{_n(a, 3)} → {_n(rr, 4)}" for a, rr in zip(p["D9"]["availability"], p["D9"]["expressed_rr"]))
    d10 = p["D10"]
    rows = ["| Sonda | Pregunta | Cumple |", "|---|---|---|"] + [
        f"| {k} | {data['design']['probes'][k]} | {_yes(p['pass'][k])} |"
        for k in sorted(data["design"]["probes"], key=lambda name: int(name[1:]))]
    return ("\n".join(rows) + f"\n\n- {d14}.\n- D5 (disponibilidad → FR, entradas fijas): {d5}.\n- {d67}.\n"
            f"- D8: {p['D8']['compared']} cursos comparados bit a bit contra el núcleo de P2P-1 (GI, ACS, edema, "
            f"acidosis); idénticos: {_yes(p['D8']['pass'])}.\n- D9 (disponibilidad → FR): {d9}; lineal: "
            f"{_yes(p['D9']['linear'])}; FR intrínseca intacta: {_yes(p['D9']['intrinsic_rr_unchanged'])}.\n"
            f"- D10: estados idénticos {_yes(d10['states_identical'])}; lecturas que cambian: "
            f"{', '.join(d10['derived_fields_differing'])}; G, D, L, carga ácida, SpO2, aporte, lactato, FC y conciencia "
            f"sin cambio: {_yes(all(d10['unchanged'].values()))}; FR {_n(d10['rr'][0], 2)} → {_n(d10['rr'][1], 2)}, "
            f"PaCO2 {_n(d10['paco2'][0], 2)} → {_n(d10['paco2'][1], 2)}, pH {_n(d10['ph'][0], 3)} → {_n(d10['ph'][1], 3)}; "
            f"la depresión hipoventila (FR menor, PaCO2 mayor, pH menor): "
            f"{_yes(d10['depression_raises_paco2_lowers_ph'])}.")


def render_absoluta(data: dict) -> str:
    a = data["absolute"]
    rows = "; ".join(f"llegada {k} %: SpO2 actual {_n(v['current_spo2'], 2)}, impulso {_n(v['hypoxaemic_drive'], 4)}"
                     for k, v in a["current_85_from_arrivals"].items())
    return (f"- Misma SpO2 actual con llegadas distintas: {rows}; misma PaCO2: {_yes(a['same_paco2'])}.\n"
            f"- Una llegada a 81 % ya tiene impulso hipoxémico: "
            f"{_n(a['arrival_81_drive'], 3)}; la composición de llegada es la del estado de llegada: "
            f"{_yes(a['arrival_composition_is_state_composition'])}.\n- Las funciones hipoxémicas del núcleo leen la "
            f"llegada: {_yes(any(a['reads_arrival'].values()))}.")


def render_edema(data: dict) -> str:
    e = data["pulmonary_edema"]
    rows = ["| Corrida | Minuto | SpO2 | FR | PaCO2 | Impulso ácido | Impulso hipoxémico |", "|---|---|---|---|---|---|---|"]
    for label, run in e["runs"].items():
        for minute, x in _by_minute(run["room_air"]):
            rows.append(f"| {label} | {minute} | {_n(x['spo2'], 2)} | {_n(x['rr'], 2)} | {_n(x['paco2'], 2)} | "
                        f"{_n(x['acid_drive'], 3)} | {_n(x['hypoxaemic_drive'], 3)} |")
    trends = "; ".join(f"{k}: FR de llegada {_n(v['arrival_rr'], 2)} (brecha a {e['authored']['rr']}: "
                       f"{_n(v['gap_to_authored_rr_at_arrival'], 2)}), cuota hipoxémica sube con la SpO2 "
                       f"{_yes(v['hypoxaemic_share_rises_as_spo2_falls'])}, cuota ácida {_n(v['acid_share_trend'], 3)}, "
                       f"FR neta {_n(v['net_rr_trend'], 3)}, el O2 baja la FR {_yes(v['oxygen_lowers_rr'])}"
                       for k, v in e["runs"].items())
    return ("\n".join(rows) + f"\n\n{trends}.\n\nFR de llegada sube con el impulso: "
            f"{_yes(e['arrival_rr_rises_with_hypoxaemic_drive'])}; a más impulso, menos PaCO2: "
            f"{_yes(e['higher_drive_lower_paco2'])}; dirección sensata: {_yes(e['direction_sensible'])}; ganancia "
            f"tomada del caso: {_yes(e['gain_from_case'])}.\n\n{e['net_direction']}.\n\n{e['classification']}.")


def render_opioide(data: dict) -> str:
    o = data["opioid"]
    rows = ["| Estado | SpO2 | Impulso hipoxémico | FR excitatoria | FR expresada | Intrínseca | PaCO2 | FC | Conciencia |",
            "|---|---|---|---|---|---|---|---|---|"]
    for label in ("hypoxaemia_intact", "hypoxaemia_depressed", "strong_hypoxaemic_drive_depressed"):
        x = o[label]
        rows.append(f"| {label} | {_n(x['spo2'], 1)} | {_n(x['hypoxaemic_drive'], 2)} | {_n(x['excitatory_rr'], 2)} | "
                    f"{_n(x['expressed_rr'], 2)} | {_n(x['intrinsic_rr'], 1)} | {_n(x['paco2'], 2)} | {_n(x['hr'], 1)} | "
                    f"{x['consciousness_level']} |")
    checks = "; ".join(f"{k} {_yes(v)}" for k, v in o["checks"].items())
    return "\n".join(rows) + f"\n\n{checks}."


def render_acidosis(data: dict) -> str:
    a = data["acidosis"]
    rows = ["| Disponibilidad | Impulso ácido | FR expresada | Intrínseca |", "|---|---|---|---|"] + [
        f"| {_n(r['availability'], 2)} | {_n(r['acid_drive'], 2)} | {_n(r['expressed_rr'], 2)} | "
        f"{_n(r['intrinsic_rr'], 1)} |" for r in a["rows"]]
    return ("\n".join(rows) + f"\n\nLa acidemia sube el impulso con disponibilidad 1: {_yes(a['acid_drives'])}; la "
            f"depresión central lo atenúa: {_yes(a['depression_attenuates'])}.")


def render_aguas_abajo(data: dict) -> str:
    d = data["downstream"]
    return (f"- Las funciones de la composición escriben atributos: {_yes(any(d['attribute_writes'].values()))}.\n"
            f"- El integrador lee la respiración: {_yes(d['reads']['integration_reads_respiration'])}; la FC lee el "
            f"impulso: {_yes(d['reads']['hr_reads_drive'])}.")


def render_limites(data: dict) -> str:
    b = data["boundaries"]
    return (f"- Literales numéricos de la composición: {', '.join(str(x) for x in b['composition_literals'])}.\n"
            f"- La composición lee la eficiencia ventilatoria: {_yes(any(b['composition_reads_efficiency'].values()))}.\n"
            f"- Valores por defecto: mapeo {b['defaults']['hypoxaemic_drive_mapping']}, ganancia "
            f"{b['defaults']['hypoxaemic_to_drive_gain']}, disponibilidad {b['defaults']['central_drive_availability']}.\n"
            f"- Términos de enfermedad en las inserciones del núcleo: "
            f"{', '.join(b['disease_terms_in_core_insertions']) or 'ninguno'}; estado nuevo: "
            f"{', '.join(b['new_state']) or 'ninguno'}.")


def render_no_regresion(data: dict) -> str:
    n = data["non_regression"]
    names = {"gi_o12": "GI (O12 de P2O-1)", "acs_evaluation": "evaluación ACS de P2O-1",
             "acs_authority_r7": "autoridad ACS (R7 de P2O-3)", "common_overload_r8": "sobrecarga común (R8)",
             "p2p1_untreated": "curso sin tratar de P2P-1", "p2p1_oxygen": "oxígeno de P2P-1",
             "p2p1_respiration": "respiración de P2P-1", "p2p1_heart_rate": "FC de P2P-1",
             "p2p1_consciousness": "conciencia de P2P-1"}
    lines = [f"- {label} reproducido: {_yes(n[key])}." for key, label in names.items()]
    untouched = n["common_files_untouched"]
    lines.append(f"- Archivos comunes intactos: {sum(untouched.values())} de {len(untouched)}.")
    return "\n".join(lines)


def render_prueba(data: dict) -> str:
    p = data["proof"]
    return ("- Archivos reconstruidos byte a byte como los dejó P2P-1: "
            + ", ".join(f"`{k}` {_yes(v)}" for k, v in p["proofs"].items())
            + f".\n- Digest congelado de P2P-1 reproducido por la vista: {_yes(p['p2p1_freeze_digest'])}; registro de "
              f"P2P-1 intacto: {_yes(p['p2p1_record'])}; archivos comunes de P2P-1 intactos vistos desde P2P-1: "
              f"{sum(p['p2p1_common_untouched'].values())} de {len(p['p2p1_common_untouched'])}.")


def render_preparacion(data: dict) -> str:
    r = data["readiness"]
    rows = ["| Criterio | Cumple |", "|---|---|"] + [f"| {k} | {_yes(x)} |" for k, x in r["criteria"].items()]
    tail = (f"\n\n**Recomendación:** `{r['recommendation']}` (no se inicia). Alcance de esa auditoría: "
            f"{r['pe_audit_scope']}." if r["ready"] else "")
    return "\n".join(rows) + f"\n\n**Veredicto:** `{r['verdict']}`." + tail


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the P2P-2 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
