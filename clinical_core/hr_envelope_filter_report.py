"""P2I-2AK report: the generated blocks of docs/revision/P2I2AK_FILTRO_ENVOLVENTES_FC.md.

    python -m clinical_core.hr_envelope_filter_report --write <document> --data <the envelope-filter JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import hr_envelope_filter as hf
from .blood_filter_report import _n
from .lactate_rebuild_report import CASE_ES, CASES, LEVEL_ES

NAMES = ("decisiones", "reglas", "reutilizacion", "conteos", "filtro", "margenes", "sensibilidad", "demanda_cruzada",
         "identificabilidad", "observables", "fluido", "validacion", "veredicto", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FACULTY_ES = {"decided": "fecha", "demand": "demanda", "untreated": "sin tratamiento (A, B)", "prbc": "GR (C, D)",
              "definitive": "manejo definitivo (E, F)", "ceiling": "techos", "scope": "alcance"}
CHECKS_ES = {"survivors": "al menos un candidato sobrevive con demanda 1,0 o 1,1",
             "envelopes_hold": "todos los sobrevivientes cumplen A–F (recomprobado)",
             "common_gains_by_construction": "ganancias y techo comunes (por construcción)",
             "pressure_deferred": "presión aplazada", "upstream_unchanged": "fisiología previa sin cambios",
             "structural": "sin contradicción estructural de la FC"}
LATENT_ES = {"intrinsic_57m": "intrínseca 57m", "intrinsic_72f": "intrínseca 72f", "acute": "ganancia aguda",
             "debt": "ganancia de deuda", "ceiling": "techo sinusal total"}
OBS_ES = {"arrival": "FC de llegada", "l1_120": "sin tratamiento: FC a los 120",
          "benefit_1": "beneficio contrafactual de la unidad 1 (lpm)",
          "benefit_2": "beneficio contrafactual de la unidad 2 (lpm)", "l3_60": "manejo definitivo: FC a los 60",
          "l3_90": "manejo definitivo: FC a los 90", "l3_120": "manejo definitivo: FC a los 120",
          "residual": "taquicardia residual sobre la intrínseca a los 120", "max_hr": "FC máxima (L1, L2, L3)",
          "reserve_utilization": "uso de la reserva"}
MARGIN_ES = {"A_l1_120": "A: FC sin tratamiento a los 120, 57m", "B_l1_120": "B: FC sin tratamiento a los 120, 72f"}
FLUID_ES = {"diverges_at": "primer minuto con FC distinta", "diverges_by_1_bpm_at": "primer minuto con más de 1 lpm",
            "largest_difference": "mayor diferencia (lpm)", "prbc_minus_fluid_at_largest": "GR − cristaloide (lpm)"}
COUNT_ES = {hf.CASE_TRUTH_REJECTION: "rechazo por verdad del caso (P2I-2AJ)",
            hf.ARRIVAL_HR_REJECTION: "rechazo por la FC de llegada (±5 lpm), sobre 450 combinaciones primarias",
            hf.OUT_OF_PRIMARY: "fuera del soporte primario de techo (200, sólo sensibilidad)",
            hf.HR_ENVELOPE_REJECTION: "rechazo por envolventes A–F (candidatos)",
            hf.SIMULATION_REJECTION: "rechazo de simulación (pulso perdido o corrida detenida)"}


def _d(value) -> str:
    return f"{float(value):.1f}".replace(".", ",")


def _g(value) -> str:
    if value is None:
        return "—"
    return "0" if value == 0 else f"{value:.3g}".replace(".", ",")


def _yes(value) -> str:
    return "sí" if value else "no"


def _s(item, digits: int = 1) -> str:
    if not item:
        return "—"
    return " / ".join(_n(item[k], digits) for k in ("low", "median", "high"))


def _latent(item) -> str:
    a, b, acute, debt, ceiling = item
    return f"{LEVEL_ES[a]} / {LEVEL_ES[b]}, aguda {_g(acute)}, deuda {_g(debt)}, techo {_g(ceiling)}"


def _demands(data: dict) -> list[str]:
    return sorted(data["demands"], key=float)


def _label(label: str) -> str:
    parts = label.split(" ")
    return parts[0] if len(parts) == 1 else f"{parts[0]} {CASE_ES.get(parts[1], parts[1])}"


def render_decisiones(data: dict) -> str:
    lines = [f"Congelamiento: `{data['freeze_digest']}` (una prueba lo fija). Registro de partida: P2I-2AJ "
             f"`{data['record']}`.\n", "| Decisión docente | Texto registrado |", "|---|---|"]
    lines += [f"| {FACULTY_ES[name]} | {data['faculty'][name]} |" for name in FACULTY_ES]
    return "\n".join(lines)


def render_reglas(data: dict) -> str:
    env = hf.ENVELOPES
    lines = ["| Regla | Escenario | Qué exige |", "|---|---|---|",
             f"| A | L1, 57m, minuto 120 | {_g(env['A']['low'])} ≤ FC ≤ {_g(env['A']['high'])} lpm |",
             f"| B | L1, 72f, minuto 120 | {_g(env['B']['low'])} ≤ FC ≤ {_g(env['B']['high'])} lpm |",
             f"| F | L3, cada caso, minuto 120 | {_g(env['F']['low'])} ≤ FC − intrínseca ≤ {_g(env['F']['high'])} lpm |",
             "| E | L3, cada caso | adecuación sostenida desde el minuto 60 (a más tardar) hasta 120, y FC_120 ≤ FC_90 ≤ "
             "FC_60, sin tolerancia |",
             "| C | L3 frente a L3 sin la unidad 1, cada caso | en el minuto en que L3 completa la unidad 1: FC con la unidad "
             "≤ FC sin ella |",
             "| D | L3 frente a L3 sin la unidad 2, cada caso | en el minuto en que L3 completa la unidad 2: FC con la unidad "
             "≤ FC sin ella |", "",
             f"- Techos primarios: {', '.join(_g(c) for c in hf.PRIMARY_CEILINGS)}; 200 sólo como `{hf.SENSITIVITY}`.",
             f"- Demanda: 1,0 y 1,1 por separado, con las mismas reglas; 0,9 queda fuera (CURRENTLY_INCOMPATIBLE).",
             f"- Orden congelado: {' → '.join(hf.ORDER)}. {hf.ORDER_RULE}",
             f"- Comparador: {hf.COMPARATOR_RULE}", f"- Candidato: {hf.CANDIDATE_RULE}"]
    return "\n".join(lines)


def render_reutilizacion(data: dict) -> str:
    r = data["reuse"]
    units = "; ".join(f"demanda {_d(k)}: `{v}`" for k, v in sorted(r["units_digests"].items(), key=lambda kv: float(kv[0])))
    return "\n".join([
        f"- Dependencias ejecutables (todo `clinical_core` salvo las dos tuplas de exclusión y este módulo): "
        f"`{r['dependency']['digest']}`, igual al de P2I-2AJ: **{_yes(r['dependency']['equal'])}**.",
        f"- Unidades de lactato del par retenido, reconstruidas con `hr_observables.retained_region`: {units}; iguales "
        f"a las de P2I-2AJ: **{_yes(r['equal'])}**.",
        f"- Superficie de llegada analítica igual a la del registro de P2I-2AJ: **{_yes(r['arrival_surface_equal'])}**.",
        "", f"Regla: {r['rule']}"])


def render_conteos(data: dict) -> str:
    c = data["counts"]
    lines = ["| Categoría | " + " | ".join(f"demanda {_d(k)}" for k in _demands(data)) + " |",
             "|---|" + "---|" * len(_demands(data))]
    truth = c[hf.CASE_TRUTH_REJECTION]
    # The record's count is demand 1.0's (P2I-2AJ's efficiency field, TD-97): each demand's is read from the committed
    # P2I-2AI record of the rejected case pair.
    rejected = [t for t in hf.p2i2aj_record()["case_truth"] if t["status"] == hf.ho.CASE_TRUTH_REJECTION]
    by_demand = {k: sum(hf.ho.p2i2ai_record()["recertification"][hf.ho.asv._key(tuple(t["pair_57m"]),
                                                                                tuple(t["pair_72f"]))]
                        ["survivors_by_demand"][k] for t in rejected) for k in _demands(data)}
    lines.append(f"| {COUNT_ES[hf.CASE_TRUTH_REJECTION]} | " + " | ".join(
        f"{truth['case_pairs']} par de casos ({by_demand[k]} sobrevivientes de lactato)" for k in _demands(data)) + " |")
    for key in (hf.ARRIVAL_HR_REJECTION, hf.OUT_OF_PRIMARY, hf.HR_ENVELOPE_REJECTION, hf.SIMULATION_REJECTION):
        lines.append(f"| {COUNT_ES[key]} | " + " | ".join(str(c[key][k]) for k in _demands(data)) + " |")
    return "\n".join(lines)


def render_filtro(data: dict) -> str:
    lines = []
    for k in _demands(data):
        dm = data["demands"][k]
        s = dm["summary"]
        by_rule = "; ".join(f"{name} {v}" for name, v in s["first_failure_by_rule"].items())
        lines += [f"**Demanda {_d(k)}.** Entran {dm['entering_latent_combinations']} combinaciones latentes × "
                  f"{dm['lactate_survivors']} sobrevivientes de lactato = **{s['entering']} candidatos** "
                  f"({dm['physiology_units']} unidades de fisiología distintas). Rechazados por primer fallo: {by_rule}. "
                  f"Fallos en cualquier posición: {s['any_failure'] or 'ninguno'}; patrones de solapamiento: "
                  f"{s['failure_patterns'] or 'ninguno'}. **Sobreviven {s['surviving']} candidatos y "
                  f"{s['surviving_candidates']} combinaciones latentes.**", "",
                  "| Intrínsecas 57m / 72f, ganancias, techo | FC de llegada predicha 57m / 72f | Sobrevivientes de "
                  "lactato que cumplen A–F | Estado | Todas las filas |", "|---|---|---|---|---|"]
        for c in s["candidates"]:
            lines.append(f"| {_latent(c['latent'])} | {_n(c['predicted'][0], 1)} / {_n(c['predicted'][1], 1)} | "
                         f"{c['surviving']} de {c['lactate_survivors']} | **{c['status']}** | {_yes(c['row_robust'])} |")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_margenes(data: dict) -> str:
    names = list(next(iter(data["demands"].values()))["margins"])
    lines = ["Diagnóstico, sin cambiar ninguna regla: LOW / mediana / HIGH sobre todos los candidatos que entran (lpm).",
             "", "| Magnitud | " + " | ".join(f"demanda {_d(k)}" for k in _demands(data)) + " |",
             "|---|" + "---|" * len(_demands(data))]
    for name in names:
        if name in MARGIN_ES:
            label = MARGIN_ES[name]
        else:
            key, case = name.split(" ")
            label = {"F_residual": "F: FC − intrínseca a los 120",
                     "E_largest_rise": "E: mayor subida entre 60, 90 y 120 (negativa = desciende)",
                     "C_benefit": "C: beneficio de la unidad 1 (sin − con)",
                     "D_benefit": "D: beneficio de la unidad 2 (sin − con)"}[key] + f", {CASE_ES[case]}"
        lines.append(f"| {label} | " + " | ".join(_s(data["demands"][k]["margins"][name], 2) for k in _demands(data))
                     + " |")
    return "\n".join(lines)


def render_sensibilidad(data: dict) -> str:
    lines = []
    for k in _demands(data):
        sens = data["demands"][k]["sensitivity_200"]
        if not sens:
            lines.append(f"- Demanda {_d(k)}: ninguna combinación con techo 200 es compatible con la llegada.")
            continue
        s = sens["summary"]
        lines.append(f"- Demanda {_d(k)}: {len(s['candidates'])} combinaciones con techo 200 ({s['entering']} "
                     f"candidatos); cumplirían A–F {s['surviving']} candidatos y {s['surviving_candidates']} "
                     f"combinaciones. Estado `{sens['status']}`: no entran en ningún resultado primario ni rescatan a "
                     f"nadie (rescata: {_yes(sens['rescues'])}).")
    return "\n".join(lines)


def render_demanda_cruzada(data: dict) -> str:
    c = data["cross_demand"]
    lines = ["| Clase | Combinaciones latentes primarias |", "|---|---|"]
    lines += [f"| {name} | {c['counts'][name]} |" for name in (hf.ROBUST, hf.ONLY_1_0, hf.ONLY_1_1, hf.INCOMPATIBLE)]
    lines += ["", f"Universo: {c['universe']} combinaciones primarias (9 pares de intrínseca × 25 ganancias × 2 techos). "
                  "Diagnóstico, nunca filtro.", ""]
    for name in (hf.ROBUST, hf.ONLY_1_0, hf.ONLY_1_1):
        for item in c["surviving"][name]:
            lines.append(f"- {name}: {_latent(item)}")
    return "\n".join(lines)


def render_identificabilidad(data: dict) -> str:
    ident = data["identifiability"]
    keys = sorted((k for k in ident if k != "union"), key=float) + ["union"]
    header = " | ".join("unión (suma por demanda)" if k == "union" else f"demanda {_d(k)}" for k in keys)
    lines = [f"| Latente | {header} |", "|---|" + "---|" * len(keys)]
    for name in hf.ho.LATENTS:
        cells = []
        for k in keys:
            item = ident[k][name]
            support = ", ".join(f"{LEVEL_ES.get(v, _g(float(v)) if v.replace('.', '', 1).isdigit() else v)}: {n}"
                                for v, n in item["support"].items() if n)
            cells.append(f"**{item['status']}** ({support or '—'})")
        lines.append(f"| {LATENT_ES[name]} | " + " | ".join(cells) + " |")
    lines += ["", "En la unión, el apoyo suma las combinaciones que sobreviven en cada demanda: la combinación "
                  "ROBUST_ACROSS_DEMAND cuenta dos veces.", "", f"Regla: {hf.IDENTIFIABILITY_RULE}"]
    return "\n".join(lines)


def render_observables(data: dict) -> str:
    lines = ["LOW / mediana / HIGH sobre los candidatos sobrevivientes (sobreviviente de lactato × combinación latente).",
             "", "| Observable | " + " | ".join(f"{CASE_ES[c]}, demanda {_d(k)}" for k in _demands(data) for c in CASES)
             + " |", "|---|" + "---|" * (len(CASES) * len(_demands(data)))]
    for name, label in OBS_ES.items():
        digits = 2 if name == "reserve_utilization" else 1
        lines.append(f"| {label} | " + " | ".join(_s(data["demands"][k]["observables"][c].get(name), digits)
                                                   for k in _demands(data) for c in CASES) + " |")
    return "\n".join(lines)


def render_fluido(data: dict) -> str:
    lines = ["| 72f, L2 cristaloide frente a L3 GR, sobrevivientes | " + " | ".join(
        f"demanda {_d(k)}" for k in _demands(data)) + " |", "|---|" + "---|" * len(_demands(data))]
    for name, label in FLUID_ES.items():
        digits = 1 if "difference" in name or "minus" in name else 0
        lines.append(f"| {label} | " + " | ".join(_s(data["demands"][k]["fluid_vs_prbc_72f"][name], digits)
                                                   for k in _demands(data)) + " |")
    lines.append("| pares sin divergencia | " + " | ".join(str(data["demands"][k]["fluid_vs_prbc_72f"]["never_diverge"])
                                                            for k in _demands(data)) + " |")
    lines.append("| primera entrada que diverge (aguda / deuda / ninguna) | " + " | ".join(
        " / ".join(str(data["demands"][k]["fluid_vs_prbc_72f"]["first_input"][kind]) for kind in ("acute", "debt",
                                                                                                  "none"))
        for k in _demands(data)) + " |")
    lines += ["", "Diagnóstico, sin filtro; no se exige que la FC distinga el líquido."]
    return "\n".join(lines)


def render_validacion(data: dict) -> str:
    lines = ["| Demanda | Unidades de muestra | Corridas completas | Comprobaciones | Exacta |", "|---|---|---|---|---|"]
    for k, v in sorted(data["validation"].items(), key=lambda kv: float(kv[0])):
        checks = ", ".join(f"{name} {_yes(ok)}" for name, ok in v["checks"].items())
        lines.append(f"| {_d(k)} | {len(v['sample'])} | {v['full_runs']} | {checks} | **{_yes(v['exact'])}** |")
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    lines = [f"**{v['verdict']}**\n", "| Comprobación | Resultado |", "|---|---|"]
    lines += [f"| {CHECKS_ES[name]} | {_yes(v['checks'][name])} |" for name in CHECKS_ES if name in v["checks"]]
    lines += ["", f"Robustez entre demandas exigida: {_yes(v['cross_demand_required'])}. Aprobado: {_yes(v['approved'])}.",
              "", f"Regla congelada: {v['rule']}"]
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    by = lambda item: "; ".join(f"demanda {_d(k)}: {v}" for k, v in sorted(item.items(), key=lambda kv: float(kv[0])))
    return (f"Trayectorias hemodinámicas: {e['haemodynamic_trajectories']}; descomposiciones de llegada analíticas: "
            f"{e['analytic_arrival_decompositions']}; corridas de fisiología del filtro (L1, L3 y los dos "
            f"contrafactuales una vez por caso, conjunto P3 y punto): {by(e['physiology_full_runs'])}; corridas de L2 y "
            f"L3 para los sobrevivientes: {by(e['survivor_full_runs'])}; corridas de validación: "
            f"{e['validation_full_runs']}; reconstrucciones de FC posprocesadas: {by(e['hr_post_processed'])}; barrido "
            f"cartesiano: {_yes(e['cartesian_sweep'])}; motor heredado leído: {_yes(e['legacy_read'])}. La mitad de las "
            "corridas de sobrevivientes repite L3, que no depende del punto de cristaloide, y las reconstrucciones "
            "contadas son sólo las de techo primario (revisión adversarial, TD-97).")


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the envelope-filter JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
