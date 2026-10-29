"""P2I-2AI report: the generated blocks of docs/revision/P2I2AI_SEVERIDAD_LLEGADA_POR_CASO.md.

    python -m clinical_core.arrival_severity_report --write <document> --data <the arrival-severity JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import arrival_severity as asv
from .blood_filter_report import _n
from .lactate_rebuild_report import CASE_ES, CASES, LEVEL_ES

NAMES = ("decisiones", "inventario", "pares", "lectura", "equivalencia", "recertificacion", "superficie",
         "comparacion", "trayectorias", "veredicto", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FACULTY_ES = {"decided": "fecha", "severity": "severidad", "ordering": "orden clínico", "no_hr": "sin FC",
              "recertification": "recertificación", "intrinsic": "intrínseca", "common": "fisiología común",
              "scope": "alcance"}
CHECKS_ES = {"severity_without_hr": "severidad por caso sin leer la FC",
             "recertification": "recertificación de D y lactato (factorización, equivalencia, par compatible)",
             "explicit_intrinsic": "intrínseca declarada por caso", "common_gains": "ganancias comunes",
             "joint_arrival": "al menos un candidato conjunto compatible con la llegada",
             "pressure_deferred": "presión aplazada", "no_regression": "sin regresión de D y lactato",
             "structural": "reconstrucción de la FC igual al núcleo completo"}
READING_ES = {"H1_untreated": "H1 sin tratamiento", "H2_crystalloid": "H2 cristaloide", "H3_prbc": "H3 GR",
              "H4_definitive": "H4 manejo definitivo"}
DERIVED_ES = {"H1_change_0_120": "H1, cambio de 0 a 120", "H1_max": "H1, máximo",
              "H4_change_60_120": "H4, cambio de 60 a 120",
              "delayed_tachycardia_120": "taquicardia diferida en L3 a los 120 (sobre la intrínseca)",
              "max_saturated_hr": "FC máxima en L1 / L2 / L3", "distance_from_ceiling": "distancia al techo"}
REPRESENTATIVES = ("LOW", "MID", "HIGH")


def _f(value) -> str:
    return f"{value:g}".replace(".", ",")


def _by_demand(counts: dict) -> str:
    return "; ".join(f"{_f(float(k))}: {v}" for k, v in sorted(counts.items(), key=lambda kv: float(kv[0])))


def _reading_rows():
    for name, (_, minutes) in asv.READINGS.items():
        for minute in minutes:
            yield f"{name}@{minute}", f"{READING_ES[name]}, minuto {minute}"
    yield from DERIVED_ES.items()


def _p(pair) -> str:
    return " / ".join(LEVEL_ES[x] for x in pair)


def _key_es(key: str) -> str:
    first, second = key.split("|")
    return f"57m ({_p(first.split('/'))}) · 72f ({_p(second.split('/'))})"


def _yes(value) -> str:
    return "sí" if value else "no"


def _g(value) -> str:
    if value is None:
        return "—"
    return "0" if value == 0 else f"{value:.3g}".replace(".", ",")


def _s(item, digits: int = 0) -> str:
    if not item:
        return "—"
    return " / ".join(_n(item[k], digits) for k in ("min", "median", "max"))


def render_decisiones(data: dict) -> str:
    lines = [f"Congelamiento: `{data['freeze_digest']}` (una prueba lo fija). Registros de partida: P2I-2AD "
             f"`{data['records']['P2I-2AD']}` y P2I-2AG `{data['records']['P2I-2AG']}`.\n",
             "| Decisión docente | Texto registrado |", "|---|---|"]
    lines += [f"| {FACULTY_ES[name]} | {data['faculty'][name]} |" for name in FACULTY_ES]
    return "\n".join(lines)


def render_inventario(data: dict) -> str:
    lines = ["| Par (deuda / entrega) | Etiqueta | D0 | entrega | reanclada (÷2,5) | señal aguda | igual en ambos casos | "
             "sobrevivientes atados en P2I-2AD | válido |", "|---|---|---|---|---|---|---|---|---|"]
    for item in data["inventory"]:
        lines.append(f"| {_p(item['pair'])} | {item['label']} | {_n(item['D0'], 0)} | {_n(item['delivery'], 2)} | "
                     f"{_n(item['delivery_reanchored'], 2)} | {_n(item['x0'], 2)} | {_yes(item['same_values_both_cases'])} "
                     f"| {item['p2i2ad_tied_survivors']} | {_yes(item['valid_after_p2i2ad'])} |")
    lines += ["", f"Procedencia: {data['inventory'][0]['provenance']}."]
    return "\n".join(lines)


def render_pares(data: dict) -> str:
    lines = ["| 57m \\ 72f | " + " | ".join(_p(p) for p in asv.PAIRS) + " |", "|---|" + "---|" * len(asv.PAIRS)]
    table = {(tuple(p["57m"]), tuple(p["72f"])): p for p in data["case_pairs"]}
    for first in asv.PAIRS:
        cells = []
        for second in asv.PAIRS:
            item = table[(first, second)]
            cells.append("**admisible**" if item["status"] == asv.ADMISSIBLE else ", ".join(item["reasons"]))
        lines.append(f"| {_p(first)} | " + " | ".join(cells) + " |")
    rej = data["analytic_rejections"]
    lines += ["", f"Combinaciones: {len(data['case_pairs'])}; rechazos analíticos (motivos, una combinación puede tener "
                  f"dos): D57 < D72 {rej['D57_BELOW_D72']}, entrega57 > entrega72 {rej['DELIVERY57_ABOVE_DELIVERY72']}, "
                  f"idénticas {rej['IDENTICAL']}; **admisibles: {len(data['admissible'])}**.", "",
              f"Regla congelada: {asv.ORDERING_RULE}"]
    return "\n".join(lines)


def render_lectura(data: dict) -> str:
    reads = data["severity_reads"]
    return (f"El constructor de severidad (`pair_values`, `case_pairs`, `admissible`) lee: {', '.join(f'`{r}`' for r in reads)}. "
            f"Ninguno es una magnitud de FC (prohibidos: {', '.join(asv.HR_NAMES)}).")


def render_equivalencia(data: dict) -> str:
    eq, val = data["equivalence"], data["validation"]
    return (f"Validación de la factorización (muestra de P2I-2AD, cada caso con su punto): {val['runs']} corridas "
            f"completas; de acuerdo: {_yes(val['agree'])}; exactas a la reserva 2,5: {_yes(val['exact_at_reserve_2_5'])}; "
            f"desacuerdos: {val['disagreements']}.\n\nEquivalencia: los pares atados reproducen la región P2I-2AD — "
            f"digest `{eq['region_digest']}` (registrado `{eq['recorded_digest']}`); sobrevivientes por demanda "
            f"{_by_demand(eq['survivors'])} (registrados {_by_demand(eq['recorded_survivors'])}). Igual: "
            f"**{_yes(eq['equal'])}**.")


def render_recertificacion(data: dict) -> str:
    lines = ["| Par por caso | candidatos | sobrevivientes (1,0) | 0,9 / 1,0 / 1,1 | robustos a la demanda | FD-LAC-04/05 "
             "evaluados | T* = inicio | D coherente | adecuado hasta 120 | estado |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for key, item in data["recertification"].items():
        st = item["statistics"]
        dem = item["survivors_by_demand"]
        status = item["status"] + (f" ({item['first_failure']})" if item["first_failure"] else "")
        lines.append(f"| {_key_es(key)} | {item['candidates']} | {item['survivors']} | {dem['0.9']} / {dem['1']} / "
                     f"{dem['1.1']} | {item['robust_across_demand']} | {st['evaluated_both']} | {st['trigger_is_onset']} | "
                     f"{st['debt_coherent']} | {st['adequate_through_120']} | **{status}** |")
    lines += ["", "Representantes (LOW / MID / HIGH) por par compatible: banderas que excluyen (empeoramiento crítico "
                  "con gran caída de lactato, normalización instantánea, incompatible con la supervivencia), D fuera de "
                  "minutos adecuados, minutos críticos bajo la D de llegada y relectura exacta:", "",
              "| Par por caso | Rep. | banderas que excluyen | D coherente | relectura exacta |", "|---|---|---|---|---|"]
    for key, item in data["recertification"].items():
        for tag in REPRESENTATIVES:
            if tag not in item["representatives"]:
                continue
            runs = item["representatives"][tag]["runs"].values()
            bad = sorted({n for r in runs for n in ("WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL", "INSTANT_NORMALIZATION",
                                                     "INCOMPATIBLE_WITH_SURVIVAL") if r["flags"][n]})
            coherent = all(not r["debt"]["falls_outside_adequate_minutes"] and r["debt"]["critical_minutes_below_arrival"]
                           == 0 for r in runs)
            lines.append(f"| {_key_es(key)} | {tag} | {', '.join(bad) or 'ninguna'} | {_yes(coherent)} | "
                         f"{_yes(all(r['rerun_equals_factorized'] for r in runs))} |")
    lines += ["", f"Compatibles con el lactato: {', '.join(_key_es(asv._key(*map(tuple, c))) for c in data['lactate_compatible']) or 'ninguno'}.",
              "", f"Regla: {asv.COMPATIBILITY_RULE}"]
    return "\n".join(lines)


def render_superficie(data: dict) -> str:
    s = data["hr_surface"]
    if not s:
        return "No se construyó: ningún par por caso es compatible con el lactato."
    sup = s["support"]
    dec = s["compatible_decompositions"]
    lines = [f"Candidatos conjuntos: {s['joint_candidates']} (pares compatibles × 9 pares de intrínseca × 25 ganancias × "
             f"3 techos); de ellos, compatibles con 57m: {s['compatible_57m']}; con 72f: {s['compatible_72f']}; "
             f"**conjuntamente compatibles: {s['joint']}** ({s['distinct_predictions']} predicciones distintas) en "
             f"{s['distinct_case_pairs']} pares por caso. Descomposiciones de llegada distintas: {s['decompositions']} "
             f"(compatibles: 57m {dec[CASES[0]]}, 72f {dec[CASES[1]]}).", "",
             "| intrínseca 57m \\ 72f | inferior | medio | superior |", "|---|---|---|---|"]
    for a in ("lower", "midpoint", "upper"):
        lines.append(f"| {LEVEL_ES[a]} | " + " | ".join(str(sup["intrinsic_pairs"][f"{a}|{b}"])
                                                       for b in ("lower", "midpoint", "upper")) + " |")
    lines += ["", "| Dimensión | Apoyo por valor |", "|---|---|",
              "| ganancia aguda | " + "; ".join(f"{_g(float(k))}: {v}" for k, v in
                                                 sorted(sup["acute"].items(), key=lambda kv: float(kv[0]))) + " |",
              "| ganancia de deuda | " + "; ".join(f"{_g(float(k))}: {v}" for k, v in
                                                    sorted(sup["debt"].items(), key=lambda kv: float(kv[0]))) + " |",
              "| techo | " + "; ".join(f"{k}: {v}" for k, v in sorted(sup["ceiling"].items(),
                                                                       key=lambda kv: float(kv[0]))) + " |",
              "| par por caso | " + ", ".join(f"{_key_es(k)}: {v}" for k, v in sup["case_pairs"].items()) + " |",
              "", f"Regla: {s['rule']}"]
    return "\n".join(lines)


def render_comparacion(data: dict) -> str:
    c = data["comparison"]
    names = {"A": "severidad común, intrínseca común", "B": "severidad por caso, intrínseca común",
             "C": "severidad común, intrínseca por caso", "D": "severidad por caso, intrínseca por caso"}
    lines = ["| | Diseño | Conjuntos compatibles | Predicciones distintas |", "|---|---|---|---|"]
    lines += [f"| {k} | {names[k]} | {c[k]['joint']} de {c[k]['of']} | {c[k]['distinct_predictions']} |" for k in names]
    lines += ["", f"La severidad por caso restaura compatibilidad: {_yes(c['case_severity_restores'])}; la intrínseca por "
                  f"caso: {_yes(c['case_intrinsic_restores'])}; BOTH_CONTRIBUTE confirmado: "
                  f"**{_yes(c['both_contribute_confirmed'])}**.", "", f"Regla: {c['rule']}"]
    return "\n".join(lines)


def render_trayectorias(data: dict) -> str:
    t = data["trajectories"]
    if not t:
        return "No se construyeron: no hay candidatos conjuntos."
    lines = [f"Recorridas de validación de la FC: {t['validation_reruns']}, exactas: {_yes(t['exact'])}. Cada celda: "
             "mín. / mediana / máx. sobre representantes × sobrevivientes (lpm).", ""]
    for key, item in t["by_case_pair"].items():
        lines += [f"**{_key_es(key)}** — {item['survivors']} sobrevivientes", "",
                  "| Lectura | 57m | 72f |", "|---|---|---|"]
        for name, label in _reading_rows():
            lines.append(f"| {label} | {_s(item['readings'][CASES[0]].get(name))} | "
                         f"{_s(item['readings'][CASES[1]].get(name))} |")
        lines.append("")
    lines.append(f"Regla: {t['rule']}")
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    lines = [f"**{v['verdict']}**\n", "| Comprobación | Resultado |", "|---|---|"]
    lines += [f"| {CHECKS_ES[name]} | {_yes(v['checks'][name])} |" for name in CHECKS_ES if name in v["checks"]]
    lines += ["", f"Aprobado: {_yes(v['approved'])}.", "", f"Regla congelada: {v['rule']}"]
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    units = "; ".join(f"demanda {_f(float(f))}: L1 {u['L1']}, L3 {u['L3']}, L2 {u['L2']}"
                      for f, u in sorted(e["post_processed_units"].items(), key=lambda kv: float(kv[0])))
    return (f"Trayectorias hemodinámicas: {e['haemodynamic_trajectories']}; corridas completas de validación: "
            f"{e['validation_full_runs']}; de representantes: {e['representative_full_runs']}; de trayectorias de FC: "
            f"{e['trajectory_full_runs']}; unidades posprocesadas por caso ({units}); combinaciones de pares: "
            f"{e['case_pairs']}; rechazos analíticos: {e['analytic_rejections']}; pares admisibles no compatibles con el "
            f"lactato: {e['simulation_rejections']}; descomposiciones de llegada analíticas: "
            f"{e['arrival_hr_decompositions']}; barrido cartesiano: {_yes(e['cartesian_sweep'])}; motor heredado leído: "
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
    parser.add_argument("--data", type=Path, required=True, help="the arrival-severity JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
