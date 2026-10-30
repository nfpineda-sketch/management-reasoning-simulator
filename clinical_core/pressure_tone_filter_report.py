"""P2J-3 report: the generated blocks of docs/revision/P2J3_FILTRO_PRESION_TONO.md.

    python -m clinical_core.pressure_tone_filter_report --write <document> --data <the filter JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
filter's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .lactate_rebuild_report import CASE_ES

NAMES = ("decisiones", "soporte", "envolventes", "orden", "primario", "demanda", "observables", "intercambio", "fc",
         "conciencia", "sensibilidad", "identificabilidad", "comparadores", "validacion", "veredicto", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FACULTY_ES = {"decided": "fecha", "normalization": "normalización", "timing": "temporalidad", "gain": "ganancia",
              "afterload": "poscarga", "output": "gasto tras la reanimación", "envelopes": "envolventes",
              "demand": "demanda", "hr": "FC", "scope": "alcance"}
RULE_ES = {"SIMULATION": "estructural (corrida detenida o guardia de T)", "G": "G · T_abs en [1, 2]",
           "H": "H · T_abs = 1 tras un minuto sin déficit", "A": "A · 57m sin tratamiento", "B": "B · 72f sin tratamiento",
           "F": "F · manejo definitivo", "C": "C · cristaloide", "D": "D · 1.ª unidad de GR",
           "E": "E · 2.ª unidad de GR", "I": "I · FD-LAC y adecuación L3"}
CHECKS_ES = {"primary_survivors": "sobrevive algún candidato primario",
             "g_h_hold": "G y H se cumplen en todos los candidatos primarios",
             "fd_lac_region_nonempty": "queda región FD-LAC no vacía",
             "feedback_stable": "retroalimentación estable (sin rechazo estructural)",
             "comparators_change_only_their_intervention": "los comparadores cambian sólo su intervención",
             "reconstruction_exact": "reconstrucción igual al núcleo (P4 y contrafactuales)",
             "upstream_reproduced": "unidades de P2I-2AK y tablas de P2J-2 reproducidas",
             "pressure_to_hr_deferred": "presión → FC aplazada (0 en el perfil primario de FC)",
             "nothing_approved": "nada aprobado"}
CLASS_ES = {"PRESSURE_AND_PERFUSION_IMPROVE": "presión y perfusión mejoran",
            "PRESSURE_NONIMPROVING_WITH_PERFUSION_IMPROVEMENT": "presión sin mejora, perfusión mejora",
            "PRESSURE_IMPROVING_WITH_PERFUSION_WORSENING": "presión mejora, perfusión empeora",
            "PRESSURE_UNCHANGED_WITH_PERFUSION_WORSENING": "presión igual, perfusión empeora",
            "NO_PERFUSION_CHANGE": "perfusión sin cambio", "PRESSURE_AND_PERFUSION_WORSEN": "presión y perfusión empeoran"}
DEMAND_ES = {"ROBUST_ACROSS_DEMAND": "robusto en ambas demandas", "DEMAND_1_0_ONLY": "sólo demanda 1,0",
             "DEMAND_1_1_ONLY": "sólo demanda 1,1", "DEMAND_INCOMPATIBLE": "incompatible con ambas"}
IDENT_ES = {"tone gain": "ganancia de tono", "afterload a": "poscarga a", "T_abs trajectory": "trayectoria de T_abs",
            "pressure / output composite": "compuesto presión / gasto"}
RULES = ("SIMULATION", "G", "H", "A", "B", "F", "C", "D", "E", "I")


def _n(value, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}".replace("-", "−")


def _s(item, digits: int = 1) -> str:
    if not item:
        return "—"
    return f"{_n(item['median'], digits)} [{_n(item['low'], digits)}–{_n(item['high'], digits)}]"


def _pct(item) -> str:
    if not item:
        return "—"
    return f"{_n(100 * item['median'])} % [{_n(100 * item['low'])}–{_n(100 * item['high'])}]"


def _yes(value) -> str:
    return "sí" if value else "no"


def render_decisiones(data: dict) -> str:
    return "\n".join(f"- **{FACULTY_ES[k]}**: {v}" for k, v in data["faculty"].items())


def render_soporte(data: dict) -> str:
    d = data["design"]
    lines = ["| ganancia g | estado |", "|---|---|"]
    lines += [f"| {g} | {s} |" for g, s in d["gain_status"].items()]
    lines += ["", "| poscarga a | estado |", "|---|---|"]
    lines += [f"| {a} | {s} |" for a, s in d["afterload_status"].items()]
    lines += ["", f"Pares primarios: {', '.join(f'(g {g:g}, a {a:g})' for g, a in d['primary_pairs'])}. Pares de "
                  f"sensibilidad: {', '.join(f'(g {g:g}, a {a:g})' for g, a in d['sensitivity_pairs'])}. Los demás pares "
                  f"explorados en P2J-2 cuentan como PRIMARY_RANGE_REJECTION: "
                  + "; ".join(f"demanda {f}: {n} candidatos" for f, n in
                              data["support_accounting"]["PRIMARY_RANGE_REJECTION"].items()) + "."]
    return "\n".join(lines)


def render_envolventes(data: dict) -> str:
    d = data["design"]
    lines = [f"- **{name}**: {item['text']}." for name, item in d["envelopes"].items()]
    lines += ["", "Minutos de comparación (congelados): " + "; ".join(
        f"{name}: {', '.join(str(x) for x in times)}" for name, times in d["comparison_times"].items()) + ".", "",
        d["comparison_rule"]]
    return "\n".join(lines)


def render_orden(data: dict) -> str:
    d = data["design"]
    return " → ".join(d["order"]) + "\n\n" + d["order_rule"]


def _rule_table(points: dict, label: str) -> list:
    lines = [f"| {label} | demanda | entran | sobreviven | primera falla | toda falla | superposiciones | FD-LAC sola | "
             "envolventes solas |", "|---|---|---|---|---|---|---|---|---|"]
    for point, by in points.items():
        for factor, item in by.items():
            first = ", ".join(f"{RULE_ES[k]}: {v}" for k, v in item["first_failure"].items() if v) or "ninguna"
            anyf = ", ".join(f"{k}: {v}" for k, v in item["any_failure"].items() if v) or "ninguna"
            overlap = ", ".join(f"{k}: {v}" for k, v in item["overlap"].items()) or "ninguna"
            lines.append(f"| {point} | {factor} | {item['entering']} | **{item['survivors']}** | {first} | {anyf} | "
                         f"{overlap} | {item['fd_lac_survivors_alone']} | {item['envelope_survivors_alone']} |")
    return lines


def render_primario(data: dict) -> str:
    return "\n".join(_rule_table({f"g {g}": by for g, by in data["primary"].items()}, "ganancia (a = 0,3)"))


def render_demanda(data: dict) -> str:
    lines = ["| ganancia (a = 0,3) | clase |", "|---|---|"]
    lines += [f"| {g} | {DEMAND_ES[c]} |" for g, c in data["demand_class"].items()]
    return "\n".join(lines)


def render_observables(data: dict) -> str:
    lines = ["Sobre las trayectorias únicas de los supervivientes primarios (mediana [rango]); entre paréntesis, la "
             "referencia T = 1 en las mismas claves.", "",
             "| punto | caso | PAS / PAM sin tratamiento a los 120 | PAS / PAM definitivo a los 120 | T_abs máx. (P1) | "
             "T_abs a los 120 tras la adecuación |", "|---|---|---|---|---|---|"]
    for point, by_case in data["support"].items():
        for case, it in by_case.items():
            lines.append(
                f"| {point} | {CASE_ES[case]} | {_s(it['untreated']['sbp120'])} / {_s(it['untreated']['map120'])} "
                f"({_n(it['untreated_reference']['sbp120']['median'])} / "
                f"{_n(it['untreated_reference']['map120']['median'])}) | {_s(it['definitive']['sbp120'])} / "
                f"{_s(it['definitive']['map120'])} ({_n(it['definitive_reference']['sbp120']['median'])} / "
                f"{_n(it['definitive_reference']['map120']['median'])}) | "
                f"{_s(it['t_abs_max_by_scenario']['P1'], 2)} | {_s(it['t_abs120_after_adequacy'], 3)} |")
    lines += ["", "Contrafactuales emparejados (intervención − comparador): clases y ΔPAM / Δaporte en cada minuto de "
                  "comparación.", "",
              "| punto | caso | contraste | clases | minuto: ΔPAM; Δaporte; ΔQ; Δdéficit |", "|---|---|---|---|---|"]
    for point, by_case in data["support"].items():
        for case, it in by_case.items():
            for name, label in (("C", "cristaloide"), ("D", "1.ª unidad"), ("E", "2.ª unidad")):
                block = it[name]
                classes = ", ".join(f"{CLASS_ES[c]}: {n}" for c, n in block["classes"].items())
                minutes = "; ".join(
                    f"{m.split()[1]}: {_s(v['map'])}; {_s(v['delivery'], 3)}; {_s(v['output'], 3)}; "
                    f"{_s(v['deficit'], 3)}" for m, v in block.items() if m.startswith("at "))
                lines.append(f"| {point} | {CASE_ES[case]} | {label} | {classes} | {minutes} |")
    return "\n".join(lines)


def render_intercambio(data: dict) -> str:
    lines = ["Sin tratamiento (P1) a los 120, contra T = 1 en la misma clave; sin umbral (la docencia lo remite a "
             "FD-LAC).", "", "| punto | caso | cambio del gasto | cambio del aporte |", "|---|---|---|---|"]
    for point, by_case in data["support"].items():
        for case, it in by_case.items():
            lines.append(f"| {point} | {CASE_ES[case]} | {_pct(it['tradeoff']['output_change'])} | "
                         f"{_pct(it['tradeoff']['delivery_change'])} |")
    return "\n".join(lines)


def render_fc(data: dict) -> str:
    hr = data["hr"]
    lines = ["Diagnóstico, nunca filtro: corridas completas del núcleo (L1, L3 y los dos contrafactuales) con el tono "
             "de cada punto, bajo las combinaciones latentes primarias de P2I-2AK; reglas A–F que fallarían, contadas "
             "sobre los candidatos supervivientes × combinaciones latentes.", "",
             "| punto | unidades fisiológicas | filas (candidato × combinación) | A–F que fallan |", "|---|---|---|---|"]
    for point, item in hr["by_point"].items():
        failures = ", ".join(f"{k}: {v}" for k, v in item["failures"].items()) or "ninguna"
        lines.append(f"| {point} | {item['physiology_units']} | {item['candidate_rows']} | {failures} |")
    return "\n".join(lines)


def render_conciencia(data: dict) -> str:
    lines = ["Umbrales vigentes de PAS, sin recalibrar: minutos con PAS < 80 y < 65 por trayectoria (mediana [rango]) "
             "de los supervivientes primarios.", "",
             "| punto | caso | P1 <80 | P1 <65 | P2 <80 | P2 <65 | P3 <80 | P4 <80 |", "|---|---|---|---|---|---|---|---|"]
    for point, by_case in data["support"].items():
        for case, it in by_case.items():
            b = it["below"]
            lines.append(f"| {point} | {CASE_ES[case]} | {_s(b['P1']['80.0'], 0)} | {_s(b['P1']['65.0'], 0)} | "
                         f"{_s(b['P2']['80.0'], 0)} | {_s(b['P2']['65.0'], 0)} | {_s(b['P3']['80.0'], 0)} | "
                         f"{_s(b['P4']['80.0'], 0)} |")
    return "\n".join(lines)


def render_sensibilidad(data: dict) -> str:
    lines = _rule_table(data["sensitivity"], "par de sensibilidad")
    lines += ["", "Clase por demanda: " + "; ".join(f"{k}: {DEMAND_ES[v]}" for k, v in
                                                   data["sensitivity_demand_class"].items()) + ". Ningún punto de "
              "sensibilidad rescata un candidato primario: se evalúan después y aparte."]
    return "\n".join(lines)


def render_identificabilidad(data: dict) -> str:
    ident = data["identifiability"]
    lines = ["| magnitud | clase | detalle |", "|---|---|---|"]
    for key in ("tone gain", "afterload a", "T_abs trajectory", "pressure / output composite"):
        item = ident[key]
        detail = item.get("why") or json.dumps(item.get("by_demand") or item.get("by_point"), ensure_ascii=False)
        lines.append(f"| {IDENT_ES[key]} | {item['class']} | {detail} |")
    lines += ["", ident["rule"]]
    return "\n".join(lines)


def render_comparadores(data: dict) -> str:
    c = data["comparators"]
    lines = [f"Válidos: {_yes(c['valid'])}.", "", "| caso | comprobación | resultado |", "|---|---|---|"]
    for case, item in c["cases"].items():
        for name, value in item.items():
            lines.append(f"| {CASE_ES[case]} | {name} | {value} |")
    return "\n".join(lines)


def render_validacion(data: dict) -> str:
    r, v = data["reuse"], data["hr"]["validation"]
    return (f"Unidades de P2I-2AK reproducidas: {_yes(r['units_equal'])} (1.0: `{r['units_digests']['1'][:12]}…`, 1.1: "
            f"`{r['units_digests']['1.1'][:12]}…`; {data['units']['1']} y {data['units']['1.1']} unidades; "
            f"{data['entering_per_point']['1']} y {data['entering_per_point']['1.1']} candidatos por punto). Tablas de "
            f"trayectorias de P2J-2 reproducidas para g = 0, 0,25, 0,5 y 1: {_yes(r['p2j2_tables_reproduced'])}. "
            f"Reconstrucción de P4 y de los contrafactuales contra el núcleo: {v['compared']} trayectorias, iguales: "
            f"{_yes(v['equal'])} ({v['full_runs']} corridas completas). Minutos con déficit 0 y T_abs ≠ 1 en el mismo "
            f"minuto (el retraso aceptado de un paso; H se lee en el minuto siguiente): "
            + "; ".join(f"g {g}: {n}" for g, n in data["domain"]["same_minute_lag"].items()) + ".")


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    lines = [f"**{v['verdict']}**", ""]
    lines += [f"- {CHECKS_ES[name]}: {_yes(ok)}" for name, ok in v["checks"].items()]
    lines.append(f"- Parámetros aprobados: {len(v['approved'])}.")
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return (f"Trayectorias de sangre en caché: {e['blood_runs']}, contrafactuales: {e['counterfactual_runs']}; grupos de "
            f"reglas: {e['groups']}; puntos (g, a) evaluados: {e['points_evaluated']}; corridas completas del núcleo "
            f"(FC y validación): {e['hr_full_runs']}; corridas del núcleo que habrían hecho falta sin reconstrucción: "
            f"{e['core_runs_without_reconstruction']}; barrido cartesiano: {_yes(e['cartesian_sweep'])}; presión "
            f"heredada leída: {_yes(e['legacy_read'])}.")


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the filter JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
