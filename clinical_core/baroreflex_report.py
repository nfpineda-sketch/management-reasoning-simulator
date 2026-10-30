"""P2J-4 report: the generated blocks of docs/revision/P2J4_BARORREFLEJO_Y_RECERTIFICACION_FC.md.

    python -m clinical_core.baroreflex_report --write <document> --data <the baroreflex JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
recertification's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .lactate_rebuild_report import CASE_ES

NAMES = ("decisiones", "senal", "sondas", "orden", "region", "filtro", "soporte", "cruce", "observables",
         "incrementos", "escenarios", "doble_conteo", "identificabilidad", "no_regresion", "veredicto", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FACULTY_ES = {"decided": "fecha", "region": "región presión / tono", "signal": "señal", "contribution": "contribución",
              "map_set": "MAP_set", "gain": "ganancia del barorreflejo", "timing": "temporalidad",
              "orthogonality": "ortogonalidad", "double_counting": "doble conteo", "old_term": "término antiguo",
              "latent": "región latente de FC", "arrival": "llegada", "hr_rules": "reglas de FC A–F",
              "pressure": "presión / tono", "upstream": "fisiología previa", "scope": "alcance"}
RULE_ES = {"DOMAIN": "dominio", "SIMULATION": "simulación", "ARRIVAL": "llegada ±5 (barorreflejo)",
           "A": "A · 57m sin tratamiento", "B": "B · 72f sin tratamiento", "F": "F · residual a los 120",
           "E": "E · descenso tras la adecuación", "C": "C · 1.ª unidad de GR", "D": "D · 2.ª unidad de GR"}
RULES = ("DOMAIN", "SIMULATION", "ARRIVAL", "A", "B", "F", "E", "C", "D")
CHECKS_ES = {"pressure_tone_unchanged": "resultados de presión / tono A–I de P2J-3 recalculados iguales",
             "signal_nonnegative_and_distinct": "señal nunca negativa y estructuralmente distinta",
             "upstream_unchanged": "fisiología previa igual con y sin barorreflejo (filas y estados)",
             "reconstruction_exact": "FC reconstruida igual a la del núcleo",
             "drive_never_negative": "impulso simpático nunca negativo",
             "reference_reproduces_p2j3_hr": "la referencia sin barorreflejo reproduce el diagnóstico de FC de P2J-3",
             "latent_region_p2i2ak": "región latente igual a la de P2I-2AK",
             "old_term_retired": "término de presión relativa en 0", "nothing_approved": "nada aprobado"}
DC_ES = {"STRUCTURALLY_DISTINCT_BUT_CORRELATED": "estructuralmente distintas pero correlacionadas",
         "FUNCTIONALLY_REDUNDANT_IN_CURRENT_CASES": "funcionalmente redundantes en los casos actuales",
         "PATHOLOGICAL_DOUBLE_COUNTING": "doble conteo patológico"}
SCENARIO_ES = {"B1": "B1 · llegada", "B2": "B2 · hemorragia sin tratamiento (L1)", "B3": "B3 · cristaloide (L2)",
               "B4": "B4 · GR antes de la hemostasia (L3 sin hemostasia)", "B5": "B5 · manejo definitivo (L3)"}
OBS_ES = {"arrival": "FC de llegada", "l1_120": "FC sin tratamiento a los 120", "benefit_1": "beneficio 1.ª unidad",
          "benefit_2": "beneficio 2.ª unidad", "l3_60": "FC definitivo 60", "l3_90": "FC definitivo 90",
          "l3_120": "FC definitivo 120", "residual": "taquicardia residual (120 − intrínseca)", "max_hr": "FC máxima",
          "acute_l1_120": "incremento por déficit agudo (sin tratamiento 120, sin saturar)",
          "debt_l1_120": "incremento por deuda (sin tratamiento 120, sin saturar)",
          "baroreflex_l1_120": "incremento por barorreflejo (sin tratamiento 120, sin saturar)",
          "baroreflex_increment_arrival": "efecto del barorreflejo en la FC de llegada",
          "baroreflex_increment_l1_120": "efecto del barorreflejo sin tratamiento a los 120",
          "baroreflex_increment_l3_120": "efecto del barorreflejo tras el manejo definitivo a los 120"}


def _n(value, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}".replace("-", "−")


def _s(item, digits: int = 1) -> str:
    if not item or not item.get("n"):
        return "—"
    return f"{_n(item['median'], digits)} [{_n(item['low'], digits)}–{_n(item['high'], digits)}]"


def _pct(value) -> str:
    return "—" if value is None else f"{_n(100 * value)} %"


def _yes(value) -> str:
    return "sí" if value else "no"


def _point(key: str) -> str:
    if key == "reference":
        return "referencia (ganancia 0)"
    m, k = key.split()
    return f"MAP_set {m[3:]} · ganancia {k[1:]}"


def render_decisiones(data: dict) -> str:
    return "\n".join(f"- **{FACULTY_ES[k]}**: {v}" for k, v in data["faculty"].items())


def render_senal(data: dict) -> str:
    d = data["design"]
    return "\n".join([f"- **Señal y contribución:** {d['signal']}",
                      f"- **Temporalidad:** {d['timing']}. {d['timing_rule']}",
                      f"- **Término de presión relativa:** {d['old_term']}. {d['old_term_rule']}",
                      f"- **MAP_set:** {', '.join(f'{m:g}' for m in d['map_sets'])} mmHg ({d['map_set_status']}).",
                      "- **Ganancias:** " + ", ".join(f"{k} ({v})" for k, v in d["baro_gains"].items()) + "."])


def render_sondas(data: dict) -> str:
    p = data["probes"]
    lines = ["| sonda | qué | PAM | impulso agudo | impulso barorreflejo | objetivo | cumple |", "|---|---|---|---|---|---|---|"]
    for name in ("A", "B", "C", "D"):
        x = p[name]
        lines.append(f"| {name} | {x['what']} | {_n(x['map'])} | {_n(x['acute_drive'], 3)} | "
                     f"{_n(x['baroreflex_drive'], 3)} | {_n(x['target'], 3)} | {_yes(x['passed'])} |")
    h = p["high_pressure"]
    lines += ["", f"PAM {_n(h['map'])} mmHg sobre MAP_set {_n(h['map_set'], 0)}: impulso del barorreflejo "
                  f"{_n(h['baroreflex_drive'], 3)}, nunca negativo: {_yes(h['never_negative'])}. Sondas a MAP_set "
                  f"{_n(data['design']['probe_map_set'], 0)}; ganancias sintéticas, sin valor clínico."]
    return "\n".join(lines)


def render_orden(data: dict) -> str:
    d = data["design"]
    order = " → ".join(d["order"])
    classes = "; ".join(f"{k}: {v}" for k, v in d["rejection_class"].items())
    return f"{order}\n\nClases de rechazo: {classes}.\n\n{d['candidate_rule']}\n\n{d['empty_rule']}"


def render_region(data: dict) -> str:
    lat, pt = data["latent"], data["pressure_tone"]
    lines = [f"- Combinaciones latentes de P2I-2AK que entran: demanda 1,0: {len(lat['combos']['1'])}; demanda 1,1: "
             f"{len(lat['combos']['1.1'])} (iguales a su grupo de llegada: {_yes(lat['equal_to_arrival_pool'])}).",
             f"- HR_PRIOR_REGION_REJECTION (combinaciones de la malla de {lat['universe']} que nunca entran): "
             f"1,0: {lat['HR_PRIOR_REGION_REJECTION']['1']}; 1,1: {lat['HR_PRIOR_REGION_REJECTION']['1.1']}.",
             "- P2J-3 recalculado en el código vivo: " + "; ".join(f"{k}: {_yes(v)}" for k, v in pt["unchanged"].items())
             + "."]
    lines += ["", "| ganancia de tono | demanda | supervivientes P2J-3 (filas lactato) |", "|---|---|---|"]
    for g, by in pt["primary"].items():
        for f, item in by.items():
            lines.append(f"| {g} | {f} | {item['survivors']} |")
    return "\n".join(lines)


def _failures(item: dict) -> str:
    return ", ".join(f"{RULE_ES[r]}: {item['first_failure'][r]}" for r in RULES if item["first_failure"].get(r)) or "ninguna"


def render_filtro(data: dict) -> str:
    lines = ["| tono · demanda · punto | entran | sobreviven | primera falla | combinaciones que sobreviven |",
             "|---|---|---|---|---|"]
    for key, item in data["filter"].items():
        g, f, *rest = key.split()
        lines.append(f"| {g[1:]} · {f[1:]} · {_point(' '.join(rest))} | {item['entering']} | **{item['survivors']}** | "
                     f"{_failures(item)} | {item['survivor_combinations'] or '—'} |")
    return "\n".join(lines)


def render_soporte(data: dict) -> str:
    s = data["support"]
    names = {"map_set": "MAP_set", "gain": "ganancia", "tone": "ganancia de tono", "demand": "demanda"}
    lines = ["| dimensión | nivel | entran | sobreviven |", "|---|---|---|---|"]
    for dim, by in s["by"].items():
        for level, item in sorted(by.items(), key=lambda kv: float(kv[0])):
            lines.append(f"| {names[dim]} | {level} | {item['entering']} | {item['survivors']} |")
    bad = s["incompatible_tone_branches"]
    lines += ["", "Ramas de tono incompatibles con la FC tras reconectar el barorreflejo: "
                  + (", ".join(bad) if bad else "ninguna") + "."]
    return "\n".join(lines)


def render_cruce(data: dict) -> str:
    cross = data["support"]["cross"]
    rows = {}
    for key, value in cross.items():
        f, g, m, k = key.split()
        rows.setdefault((f[1:], g[1:]), {})[(m[3:], k[1:])] = value
    cols = sorted({c for r in rows.values() for c in r}, key=lambda c: (float(c[0]), float(c[1])))
    lines = ["| demanda · tono | " + " | ".join(f"{m}/{k}" for m, k in cols) + " |",
             "|---|" + "---|" * len(cols)]
    for (f, g), r in sorted(rows.items(), key=lambda kv: (float(kv[0][0]), float(kv[0][1]))):
        lines.append(f"| {f} · {g} | " + " | ".join(str(r.get(c, "—")) for c in cols) + " |")
    return "Filas supervivientes por MAP_set / ganancia del barorreflejo.\n\n" + "\n".join(lines)


def render_observables(data: dict) -> str:
    o = data["observables"]
    cases = list(o)
    lines = ["Sobre las trayectorias únicas de los supervivientes primarios (mediana [rango]), bpm.", "",
             "| lectura | " + " | ".join(CASE_ES[c] for c in cases) + " |", "|---|" + "---|" * len(cases)]
    for name, label in OBS_ES.items():
        lines.append(f"| {label} | " + " | ".join(_s(o[c].get(name)) for c in cases) + " |")
    return "\n".join(lines)


def render_incrementos(data: dict) -> str:
    lines = ["FC(punto) − FC(sin barorreflejo), mismo candidato (mediana [rango]), bpm, sobre los supervivientes del "
             "punto.", "", "| punto | caso | llegada | sin tratamiento 120 | definitivo 120 |", "|---|---|---|---|---|"]
    for key, by in data["increments"].items():
        for case, w in by.items():
            lines.append(f"| {_point(key)} | {CASE_ES[case]} | {_s(w['arrival'])} | {_s(w['l1_120'])} | "
                         f"{_s(w['l3_120'])} |")
    return "\n".join(lines)


def render_escenarios(data: dict) -> str:
    sc = data["scenarios"]
    lines = ["Señal del barorreflejo (mediana [rango]) y contribución sin saturar por unidad de ganancia (25 bpm × señal; "
             "la contribución es la ganancia por ese valor), por MAP_set, sobre las unidades que entran.", ""]
    for name in ("B1", "B2", "B3", "B4", "B5"):
        if name not in sc:
            continue
        lines += [f"**{SCENARIO_ES[name]}**", "", "| caso | MAP_set | " + " | ".join(
            f"min {m}" for m in data["design"]["minutes_reported"]) + " |",
                  "|---|---|" + "---|" * len(data["design"]["minutes_reported"])]
        for case, by_m in sc[name].items():
            for m, values in by_m.items():
                cells = [f"{_s(v['signal'], 2)}; {_s(v['bpm_per_unit_gain'])} bpm" if v["signal"].get("n") else "—"
                         for v in values]
                lines.append(f"| {CASE_ES[case]} | {m} | " + " | ".join(cells) + " |")
        lines.append("")
    for name, label in (("B6", "B6 · hipotensión aislada (sonda A)"), ("B7", "B7 · déficit de oxígeno aislado (sonda B)")):
        x = sc[name]
        lines.append(f"- **{label}:** PAM {_n(x['map'])}, impulso agudo {_n(x['acute_drive'], 3)}, impulso del "
                     f"barorreflejo {_n(x['baroreflex_drive'], 3)}; cumple: {_yes(x['passed'])}.")
    return "\n".join(lines)


def render_doble_conteo(data: dict) -> str:
    dc = data["double_counting"]
    lines = [f"**Clase: {dc['class']}** ({DC_ES[dc['class']]}). Sondas A–D: {_yes(dc['probes_passed'])}.", "",
             "| MAP_set | minutos | correlación | ambas > 0 | sólo barorreflejo | sólo déficit agudo | ninguna | "
             "violaciones de signo | clase |", "|---|---|---|---|---|---|---|---|---|"]
    for m, x in dc["by_map_set"].items():
        lines.append(f"| {m} | {x['minutes']} | {_n(x['correlation'], 3)} | {_pct(x['both_positive'])} | "
                     f"{_pct(x['baroreflex_only'])} | {_pct(x['acute_only'])} | {_pct(x['neither'])} | "
                     f"{x['sign_violations']} | {x['class']} |")
    lines += ["", "Participación en el objetivo simpático (L1 + L3, supervivientes del punto; mediana [rango]):", "",
              "| punto | déficit agudo | deuda | barorreflejo |", "|---|---|---|---|"]
    for key, x in dc["shares"].items():
        lines.append(f"| {_point(key)} | {_s(x['acute'], 2)} | {_s(x['debt'], 2)} | {_s(x['baroreflex'], 2)} |")
    lines += ["", "Cambios de orden atribuibles al barorreflejo (frente a la referencia sin barorreflejo):", "",
              "| demanda · tono · punto | supervivientes de la referencia perdidos | pares discordantes 57m | "
              "pares discordantes 72f |", "|---|---|---|---|"]
    for key, x in dc["ranking"].items():
        f, g, *rest = key.split()
        d = x["discordant_pairs"]
        lines.append(f"| {f[1:]} · {g[1:]} · {_point(' '.join(rest))} | {x['reference_survivors_lost']} | "
                     f"{_pct(d.get('gi_bleed_57m'))} | {_pct(d.get('gi_bleed_72f'))} |")
    return "\n".join(lines)


def render_identificabilidad(data: dict) -> str:
    i = data["identifiability"]
    lines = [f"- **MAP_set:** {i['map_set']['class']} (supervivientes por nivel: "
             + ", ".join(f"{k}: {v}" for k, v in i["map_set"]["survivors"].items()) + ").",
             f"- **Ganancia del barorreflejo:** {i['gain']['class']} (supervivientes por nivel: "
             + ", ".join(f"{k}: {v}" for k, v in i["gain"]["survivors"].items()) + ").",
             "- **Interacción con las combinaciones latentes (ganancias aguda y de deuda, intrínseca, techo):** "
             + "; ".join(f"demanda {k[1:]}: {v}" for k, v in i["latent_combinations"]["class"].items()) + ".",
             "- **Interacción con la ganancia de tono g:** "
             + "; ".join(f"demanda {k[1:]}: {v}" for k, v in i["tone_gain"]["class"].items()) + ".", "",
             data["design"]["identifiability_rule"]]
    return "\n".join(lines)


def render_no_regresion(data: dict) -> str:
    v = data["validation"]
    r = data["reference"]
    lines = [f"- Corridas de validación con el barorreflejo encendido: {v['tasks']} unidades × 4 escenarios; FC "
             f"reconstruida igual a la del núcleo: {_yes(v['hr_equal'])}; filas sin FC iguales (presión, gasto, aporte, "
             f"déficit, D, lactato, FR, sangrado, GR, cristaloide): {_yes(v['rows_equal'])}; estados de L3 iguales salvo "
             f"el impulso (BloodState y todos los canales): {_yes(v['states_equal'])}; el barorreflejo movió el impulso "
             f"en {v['baroreflex_moved_drive']} de {v['tasks']}.",
             "- Puntos validados contra el núcleo: " + ", ".join(_point(p) for p in v["checked_points"]) + ".",
             "- Referencia sin barorreflejo frente al diagnóstico de FC de P2J-3: "
             + "; ".join(f"{k}: {x['candidate_rows']} filas, fallas {x['failures'] or 'ninguna'}" for k, x in r.items())
             + "."]
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    lines = [f"**{v['verdict']}**", ""]
    lines += [f"- {CHECKS_ES[name]}: {_yes(ok)}" for name, ok in v["checks"].items()]
    lines.append(f"- Parámetros aprobados: {len(v['approved'])}.")
    if "recommendation" in data:
        rec = data["recommendation"]
        lines += ["", f"**Recomendación: {rec['recommendation']}**"
                      + (f" (decisiones: {', '.join(rec['decisions'])})" if rec["decisions"] else "") + "."]
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return (f"P2J-3 recalculado: {e['p2j3_blood_runs']} trayectorias de sangre y {e['p2j3_counterfactual_runs']} "
            f"contrafactuales en caché, {e['p2j3_groups']} grupos. FC: {e['hr_runs_without_baroreflex']} corridas "
            f"completas sin barorreflejo, {e['hr_validation_runs']} de validación con barorreflejo y {e['state_runs']} "
            f"de estados; {e['reconstructed_series']} series de FC reconstruidas sin correr el núcleo. Barrido "
            f"cartesiano: {_yes(e['cartesian_sweep'])}; FC o PA heredadas leídas: {_yes(e['legacy_read'])}.")


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the baroreflex JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
