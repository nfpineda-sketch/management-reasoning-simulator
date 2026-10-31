"""P2K-1 report: the generated blocks of docs/revision/P2K1_AUDITORIA_FR_Y_VENTILACION.md.

    python -m clinical_core.rr_audit_report --write <document> --data <the audit JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
audit's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .lactate_rebuild_report import CASE_ES

NAMES = ("decisiones", "ecuacion", "contribuyentes", "ruta_d", "w", "acido_base", "sondas", "soporte", "observado",
         "reconstruccion", "direcciones", "dependencias", "identificabilidad", "veredicto", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FACULTY_ES = {"decided": "fecha", "closed": "dominios cerrados", "carried": "incertidumbre que se lleva",
              "w_rr": "W y FR", "lactate": "lactato", "kd_s1": "KD-S1", "d": "D", "early_stop": "parada temprana",
              "scope": "alcance"}
SCENARIO_ES = {"P1": "R1 · hemorragia sin tratamiento (L1)", "P2": "R2 · cristaloide (L2)",
               "P3": "R3 · GR antes de la hemostasia", "P4": "R4 · manejo definitivo (L3)"}
STATUS_ES = {"PASSES": "se cumple", "PASSES_FOR_THE_PROXY_ONLY": "se cumple sólo para el sustituto (lactato)",
             "VIOLATED_BY_THE_PROXY": "lo viola el sustituto (lactato)", "NOT_REPRESENTABLE": "no representable"}
BLOCKER_ES = {"ACID_BASE_STATE_REQUIRED": "falta un estado ácido-base: la acidosis metabólica sólo llega a la FR "
                                          "a través del lactato",
              "LACTATE_BIOMARKER_PROXY": "la concentración de lactato manda directamente sobre la FR",
              "W_MIXED_DRIVE_AND_VENTILATION": "W mezcla impulso y ventilación",
              "VENTILATION_FREQUENCY_CONFLATED": "no hay ventilación efectiva aparte de la FR",
              "CO2_NOT_REPRESENTABLE": "no hay CO2",
              "MECHANICAL_VENTILATION_NOT_MODELED": "no hay ventilación mecánica"}


def _n(value, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}".replace("-", "−")


def _s(item, digits: int = 1) -> str:
    if not item or not item.get("n"):
        return "—"
    return f"{_n(item['median'], digits)} [{_n(item['low'], digits)}–{_n(item['high'], digits)}]"


def _yes(value) -> str:
    return "sí" if value else "no"


def render_decisiones(data: dict) -> str:
    return "\n".join(f"- **{FACULTY_ES[k]}**: {v}" for k, v in data["faculty"].items())


def render_ecuacion(data: dict) -> str:
    d, reads = data["design"], data["reads"]
    return "\n".join([d["equation"], "",
                      "- `respiratory_rate` lee: " + ", ".join(f"`{x}`" for x in reads["respiratory_rate"]["attributes"])
                      + "; llama a " + ", ".join(f"`{x}`" for x in reads["respiratory_rate"]["calls"]) + ".",
                      "- `_metabolic_drive` lee: " + ", ".join(f"`{x}`" for x in reads["_metabolic_drive"]["attributes"])
                      + ".",
                      "- `lactate_after_minute` lee: " + ", ".join(
                          f"`{x}`" for x in reads["lactate_after_minute"]["attributes"]) + ".",
                      "- Parámetros de la FR: " + ", ".join(f"`{x}`" for x in d["rr_parameters"]) + "."])


def render_contribuyentes(data: dict) -> str:
    lines = ["| contribuyente | clase | vía |", "|---|---|---|"]
    for c in data["design"]["contributors"]:
        lines.append(f"| {c['name']} | {c['class']} | {c['path']} |")
    return "\n".join(lines)


def render_ruta_d(data: dict) -> str:
    c = data["probes"]["C"]
    lines = [f"{i}. `{where}`: {what}" for i, (where, what) in enumerate(data["design"]["d_path"], 1)]
    lines += ["", f"Sonda C (bomba 0,3 durante {c['minutes']} min): con producción de lactato la FR pasa de "
                  f"{_n(c['with_lactate_production']['rr'][0])} a {_n(c['with_lactate_production']['rr'][-1])} "
                  f"(D al final {_n(c['with_lactate_production']['D_end'])}); con el lactato fijo (producción 0) la "
                  f"FR queda en {_n(c['lactate_held']['rr'][0])} aunque D llegue a {_n(c['lactate_held']['D_end'])}. "
                  f"Cambio en el primer minuto: {_n(c['first_minute_rr_change'], 2)}. La FR se mueve sólo con el "
                  f"lactato: {_yes(c['rr_moves_only_with_lactate'])}."]
    return "\n".join(lines)


def render_w(data: dict) -> str:
    w = data["design"]["w_audit"]
    names = {"meaning": "significado", "arrival": "llegada", "change": "cómo cambia", "writers": "escritores",
             "readers": "lectores", "rr": "FR", "pco2": "pCO2", "ph": "pH", "support": "soporte",
             "spontaneous_mechanical": "espontánea frente a mecánica", "class": "clase", "why": "por qué"}
    lines = [f"- **{names[k]}**: {v}" for k, v in w.items()]
    lines.append("- **archivos del núcleo que nombran W**: " + ", ".join(f"`{x}`" for x in data["w_references"]) + ".")
    return "\n".join(lines)


def render_acido_base(data: dict) -> str:
    lines = ["| magnitud | clase | dónde |", "|---|---|---|"]
    for k, v in data["design"]["acid_base"].items():
        lines.append(f"| {k} | {v['class']} | {v['where']} |")
    a = data["design"]["acidosis_to_drive"]
    lines += ["", f"¿Puede representarse acidosis metabólica → impulso ventilatorio sin el lactato? "
                  f"{_yes(a['representable_without_lactate'])}: {a['why']}."]
    return "\n".join(lines)


def render_sondas(data: dict) -> str:
    p = data["probes"]
    lines = [f"FR de llegada de la sonda: {_n(p['arrival_rr'])}.", "",
             "| sonda | qué | resultado | vía |", "|---|---|---|---|"]
    for name in ("A", "B", "C", "D", "E"):
        x = p[name]
        result = x.get("result") or ("FR solo con lactato" if x.get("rr_moves_only_with_lactate") else "—")
        if name == "B":
            result = f"{x['result']} (FR {_n(x['rr'])}, +{_n(x['rise'])})"
        if name == "D":
            result = f"{x['result']} (W −0,5: FR {_n(x['w_minus_half_rr'])})"
        if name == "E":
            result = f"{x['result']} (W +0,5: FR {_n(x['w_plus_half_rr'])})"
        lines.append(f"| {name} | {x['what']} | {result} | {x['pathway']} |")
    h, o, c = p["hypoxaemia"], p["oxygen"], p["clearance"]
    lines += ["", f"- Hipoxemia: FR con SpO2 85 = {_n(h['spo2_85_rr'])}, con 97 = {_n(h['spo2_97_rr'])}; impulso "
                  f"hipoxémico propio de la FR: {_yes(h['independent_drive'])}.",
              f"- Oxígeno (FiO2 {_n(o['fio2'], 2)}): SpO2 {_n(o['spo2_room_air'])} → {_n(o['spo2'])}; FR "
              f"{_n(o['rr_room_air'])} → {_n(o['rr'])}; W {_n(o['W'])}; sólo oxigenación: {_yes(o['oxygenation_only'])}.",
              f"- Aclaramiento con la misma D ({_n(c['same_D'])}): τ 30 min → lactato {_n(c['30']['lactate'], 2)}, FR "
              f"{_n(c['30']['rr'])}; τ 120 min → lactato {_n(c['120']['lactate'], 2)}, FR {_n(c['120']['rr'])}.",
              "", data["design"]["probe_rule"]]
    return "\n".join(lines)


def render_soporte(data: dict) -> str:
    return "\n".join(f"- **{k}**: {v}" for k, v in data["design"]["support"].items())


def render_observado(data: dict) -> str:
    lines = ["| caso | dato | valor | origen | fuente |", "|---|---|---|---|---|"]
    for case, items in data["authored"].items():
        for item, x in items.items():
            value = x["value"]
            if "parts" in x:
                value = f"{value} ({', '.join(f'{k}: {v}' for k, v in x['parts'].items())})"
            lines.append(f"| {CASE_ES[case]} | {item} | {value} | {x['origin']} | {x.get('source', '—')} |")
    return "\n".join(lines)


def render_reconstruccion(data: dict) -> str:
    rec = data["reconstruction"]
    minutes = data["design"]["minutes_reported"]
    lines = ["FR por escenario, caso, demanda y ganancia de tono g: mediana [rango] sobre las trayectorias únicas de los "
             "supervivientes de P2J-3; entre paréntesis, las medianas de lactato (mmol/L), D y déficit efectivo "
             "relativo. W = 0, pH y pCO2 no modelados, impulso hipoxémico no modelado, aire ambiente (FiO2 0,21).", ""]
    for name in ("P1", "P2", "P3", "P4"):
        for case in ("gi_bleed_57m", "gi_bleed_72f"):
            lines += [f"**{SCENARIO_ES[name]} · {CASE_ES[case]}**", "",
                      "| demanda · g | n | " + " | ".join(f"min {m}" for m in minutes) + " |",
                      "|---|---|" + "---|" * len(minutes)]
            keys = sorted((k for k in rec if k.endswith(f" {name} {case}")),
                          key=lambda k: (float(k.split()[0][1:]), float(k.split()[1][1:])))
            for key in keys:
                x = rec[key]
                cells = []
                for m in minutes:
                    v = x["minutes"].get(str(m))
                    if not v or not v["rr"].get("n"):
                        cells.append("—")
                        continue
                    cells.append(f"{_s(v['rr'])} ({_n(v['lactate']['median'], 2)}; {_n(v['D']['median'])}; "
                                 f"{_n(v['deficit']['median'], 2)})")
                f, g = key.split()[:2]
                lines.append(f"| {f[1:]} · {g[1:]} | {x['trajectories']} | " + " | ".join(cells) + " |")
            lines.append("")
    v = data["validation"]
    lines.append(f"Validación contra el núcleo: {v['compared']} corridas completas, FR, D y lactato iguales: "
                 f"{_yes(v['equal'])}.")
    return "\n".join(lines)


def render_direcciones(data: dict) -> str:
    lines = ["| # | expectativa | estado | detalle |", "|---|---|---|---|"]
    for k, text in data["design"]["directions"].items():
        x = data["directions"][k]
        extra = x.get("note", "")
        if k == "8":
            extra = (f"mayor cambio de FR en el minuto de la hemostasia {_n(x['haemostasis_step'], 2)}, mayor cambio "
                     f"de un minuto de las trayectorias {_n(x['largest_step'], 2)}; {extra}")
        lines.append(f"| {k} | {text} | {STATUS_ES[x['status']]} | {extra} |")
    lines += ["", data["design"]["direction_rule"]]
    return "\n".join(lines)


def render_dependencias(data: dict) -> str:
    names = {"demand": "demanda 1,0 / 1,1", "tone_gain": "ganancia de tono g", "map_set": "MAP_set",
             "baroreflex_gain": "ganancia del barorreflejo", "hr_latent": "región latente de FC"}
    lines = ["| magnitud | vía hasta la FR | diferencia máxima de FR (bpm) |", "|---|---|---|"]
    for k, x in data["dependencies"].items():
        diff = _s(x["max_rr_difference"], 2) if "max_rr_difference" in x else (x.get("evidence") or "—")
        lines.append(f"| {names[k]} | {x['path']} | {diff} |")
    return "\n".join(lines)


def render_identificabilidad(data: dict) -> str:
    names = {"baseline_rr": "FR basal / intrínseca", "metabolic_gain": "ganancia metabólica / acidémica",
             "hypoxaemic_gain": "ganancia hipoxémica", "w_drive_coupling": "acoplamiento W / impulso",
             "rr_max": "techo de FR (rr_max)", "rr_metabolic_max": "saturación metabólica",
             "rr_ventilatory_floor": "piso ventilatorio", "d_lactate_pathway": "vía D / lactato"}
    i = data["identifiability"]
    lines = ["| magnitud | clase | detalle |", "|---|---|---|"]
    for k, label in names.items():
        x = i[k]
        detail = x.get("why") or ""
        if "peak_rr" in x:
            detail = f"FR máxima reconstruida {_n(x['peak_rr'])}"
        if "binds" in x:
            detail += "; el piso limita el reparto de llegada: " + ", ".join(
                f"{CASE_ES[c]} {_yes(b)}" for c, b in x["binds"].items())
        lines.append(f"| {label} | {x['class']} | {detail} |")
    lines += ["", i["rule"]]
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    lines = [f"**{v['verdict']}**", "", "Bloqueos, en orden:"]
    lines += [f"- `{b}`: {BLOCKER_ES[b]}" for b in v["blockers"]]
    lines += ["", f"- Corrección estructural: {_yes(data['design']['correction']['made'])}. "
                  f"{data['design']['correction']['why']}",
              f"- Superficie candidata: {_yes(data['design']['candidate_surface']['built'])}. "
              f"{data['design']['candidate_surface']['why']}.",
              f"- Núcleo sin cambios: " + ", ".join(f"`{k}` {_yes(x)}" for k, x in data["core_unchanged"].items()) + ".",
              f"- Región de P2J-3 recalculada igual: " + ", ".join(f"{k} {_yes(x)}"
                                                                 for k, x in data["pressure_tone_unchanged"].items()) + ".",
              f"- Parámetros aprobados: {len(v['approved'])}.", "", "**Estructura mínima que falta:** "
              + data["design"]["missing_structure"], "", "**Decisiones que se piden a la docencia:**"]
    lines += [f"{n}. {d}" for n, d in enumerate(data["design"]["decisions"], 1)]
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return (f"P2J-3 recalculado: {e['p2j3_blood_runs']} trayectorias de sangre y {e['p2j3_counterfactual_runs']} "
            f"contrafactuales en caché. FR: {e['rr_trajectories_rebuilt']} trayectorias reconstruidas sin correr el "
            f"núcleo y {e['core_validation_runs']} corridas completas de validación; corridas de candidatos: "
            f"{e['candidate_runs']}. Barrido cartesiano: {_yes(e['cartesian_sweep'])}; FR heredada leída: "
            f"{_yes(e['legacy_read'])}.")


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the audit JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
