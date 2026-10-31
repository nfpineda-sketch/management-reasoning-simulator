"""P2K-2 report: the generated blocks of docs/revision/P2K2_CARGA_ACIDA_Y_VENTILACION.md.

    python -m clinical_core.acid_base_report --write <document> --data <the P2K-2 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing; the one number it
derives, the resting PaCO2 of each arrival-compatible candidate, is the recorded arrival RR and authored PaCO2 divided
by the intrinsic RR, as the frozen semantics define it.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .lactate_rebuild_report import CASE_ES

NAMES = ("decisiones", "semantica", "gas", "candidatos", "llegada", "sondas", "reconstruccion", "preguntas",
         "dependencias", "identificabilidad", "veredicto", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FACULTY_ES = {"decided": "fecha", "closed": "P2K-1", "carried": "incertidumbre que se lleva",
              "acid_state": "estado de carga ácida", "acid_dynamics": "dinámica de la carga",
              "acid_parameters": "parámetros de producción y aclaramiento", "lactate": "lactato", "d": "D",
              "drive_rr_w": "impulso, FR y W", "drive": "impulso respiratorio", "rr": "FR", "intrinsic_rr": "FR intrínseca",
              "arrival": "llegada", "w": "W", "efficiency": "eficiencia ventilatoria", "paco2": "PaCO2", "ph": "pH",
              "w_leak": "fuga semántica de W", "hypoxaemia": "impulso hipoxémico", "lgn": "canales L, G y N",
              "support": "soporte respiratorio", "upstream": "fisiología aguas arriba", "early_stop": "parada temprana",
              "scope": "alcance"}
SCENARIO_ES = {"P1": "R1 · hemorragia sin tratamiento (L1)", "P2": "R2 · cristaloide (L2)",
               "P3": "R3 · GR sin hemostasia", "P4": "R4 · manejo definitivo (L3)"}
CRITERIA_ES = {"acid_burden_causal": "la carga ácida es un estado explícito que mueve la FR",
               "lactate_retired": "el lactato no llega a la FR candidata",
               "d_not_direct": "D no llega a la FR candidata",
               "distinct_drive_rr_w": "impulso, FR y W son distintos",
               "paco2_ph_coherent": "PaCO2 y pH coherentes",
               "rr_w_dissociation": "la FR y W pueden disociarse",
               "patient_like": "trayectorias propias de un paciente",
               "no_upstream_regression": "sin regresión aguas arriba",
               "bounded_surface": "superficie candidata acotada", "nothing_approved": "nada aprobado"}
IDENT_ES = {"intrinsic_rr_57m": "FR intrínseca 57m", "intrinsic_rr_72f": "FR intrínseca 72f",
            "acid_to_drive_gain": "ganancia ácido → impulso", "deficit_to_acid_gain": "ganancia déficit → ácido",
            "acid_clearance_tau": "τ de aclaramiento ácido", "acid_burden": "carga ácida",
            "w_efficiency": "W / eficiencia ventilatoria"}


def _n(value, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}".replace("-", "−").replace(".", ",")


def _s(item, digits: int = 1) -> str:
    if not item or not item.get("n"):
        return "—"
    if abs(item["low"] - item["high"]) < 0.5 * 10 ** -digits:
        return _n(item["median"], digits)
    return f"{_n(item['median'], digits)} [{_n(item['low'], digits)}–{_n(item['high'], digits)}]"


def _yes(value) -> str:
    return "sí" if value else "no"


def _share(item) -> str:
    return f"{item['true']} de {item['n']}"


def render_decisiones(data: dict) -> str:
    return "\n".join(f"- **{FACULTY_ES.get(k, k)}**: {v}" for k, v in data["faculty"].items())


def render_semantica(data: dict) -> str:
    d = data["design"]
    lines = ["| magnitud | definición |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in d["semantics"].items()]
    lines += ["", "**Vías retiradas en la candidata:**"]
    lines += [f"- `{k}`: {v}" for k, v in d["retired"].items()]
    lines += ["", "**Estados:** " + "; ".join(f"{k} = {v}" for k, v in d["status"].items()) + "."]
    lines += ["", "**Entradas candidatas de las anclas (fuera del registro de parámetros de caso y de la migración):** "
              + ", ".join(f"`{x}`" for x in d["candidate_inputs"]) + "."]
    lines += ["", "**L, G y N:**"] + [f"- {k}: {v}" for k, v in d["lgn"].items()]
    lines += ["", "**Soporte:**"] + [f"- {k}: {v}" for k, v in d["support"].items()]
    return "\n".join(lines)


def render_gas(data: dict) -> str:
    lines = ["| caso | pH | PaCO2 | HCO3 (banco) | carga ácida de llegada | pH derivado | error |", "|---|---|---|---|---|---|---|"]
    for case, gas in data["authored_gas"].items():
        rec = data["ph_reconstruction"][case]
        lines.append(f"| {CASE_ES[case]} | {_n(gas['ph'], 2)} | {_n(gas['paco2'], 0)} | {_n(gas['hco3'])} | "
                     f"{_n(data['arrival_burden'][case])} mEq/L | {_n(rec['derived_ph'], 4)} | {_n(rec['error'], 4)} |")
    lines += ["", "El HCO3 es el que calcula el banco de casos (0,03 × PaCO2 × 10^(pH − 6,1), redondeado a 0,1); el pH "
                  "derivado usa las mismas constantes. El error está dentro del redondeo del HCO3 (± 0,05 mEq/L, unos "
                  "± 0,0013 de pH). Ningún desplazamiento lo corrige. La PaCO2 de llegada es exacta por construcción."]
    return "\n".join(lines)


def render_candidatos(data: dict) -> str:
    d = data["design"]
    gains = ", ".join(_n(g, 3) for g in d["drive_gains"])
    exact = ", ".join(f"{CASE_ES[k.split()[0]]} {k.split()[1]}: {_n(v, 2)}" for k, v in data["exact_arrival_gains"].items())
    deficits = ", ".join(f"{CASE_ES[k.split()[0]]} {k.split()[1].replace('x', 'demanda ')}: {_n(v, 2)}"
                         for k, v in data["arrival_deficits"].items())
    return "\n".join([
        d["candidate_rule"], "",
        f"- **FR intrínseca:** {', '.join(_n(x, 0) for x in d['intrinsic_rr'])} rpm por paciente (EXPLORATORY).",
        f"- **Ganancia ácido → impulso:** {gains} rpm-equivalentes por mEq/L, común a los dos casos. Ganancias exactas de "
        f"llegada: {exact}.",
        f"- **Carga estacionaria por unidad de déficit B = k × τ:** {', '.join(_n(x) for x in d['steady_burdens'])} "
        f"mEq/L. Déficits efectivos de llegada: {deficits}.",
        f"- **τ ácido:** {', '.join(_n(x, 0) for x in d['acid_taus'])} min; k = B / τ.",
        f"- **Eficiencia ventilatoria:** {_n(d['efficiency'])} (referencia estructural). **Saturación S:** "
        f"{_n(d['saturation'], 0)} rpm. **Tolerancia de llegada:** ± {_n(d['arrival_tolerance'], 0)} rpm "
        "(ARRIVAL_RR_TOLERANCE_PROVISIONAL)."])


def render_llegada(data: dict) -> str:
    c = data["arrival_compatibility"]
    lines = [f"Combinaciones comunes compatibles (ganancia, FR intrínseca 57m, FR intrínseca 72f): **{c['count']} de "
             f"{c['of']}**.", "",
             "| ganancia | intrínseca 57m | FR llegada 57m | PaCO2 en reposo 57m | intrínseca 72f | FR llegada 72f | "
             "PaCO2 en reposo 72f |", "|---|---|---|---|---|---|---|"]
    gas = data["authored_gas"]
    for row in c["rows"]:
        if not row["compatible"]:
            continue
        cells = []
        for case in ("gi_bleed_57m", "gi_bleed_72f"):
            intrinsic, rr = row["intrinsic"][case], row["rr"][case]
            cells += [_n(intrinsic, 0), f"{_n(rr)} ({_n(row['mismatch'][case])})", _n(gas[case]["paco2"] * rr / intrinsic)]
        lines.append(f"| {_n(row['gain'], 3)} | " + " | ".join(cells) + " |")
    lines += ["", "Entre paréntesis, la diferencia con la FR de autor (26 y 24). PaCO2 en reposo: la que el anclaje implica "
                  "con W = 1 (PaCO2 de llegada × FR de llegada / FR intrínseca), a eficiencia 1."]
    return "\n".join(lines)


def render_sondas(data: dict) -> str:
    p = data["probes"]
    b = p["base"]
    e2 = p["E2"]["course"]
    lines = [p["rule"], "", f"Llegada de la sonda: carga {_n(b['burden'])}, FR {_n(b['rr'])}, W {_n(b['w'], 2)}, "
             f"PaCO2 {_n(b['paco2'])}, pH {_n(b['ph'], 3)}.", "",
             "| sonda | resultado |", "|---|---|",
             f"| A · sube la carga, oxigenación normal | impulso {_n(b['drive'])} → {_n(p['A']['result']['drive'])}, FR "
             f"{_n(b['rr'])} → {_n(p['A']['result']['rr'])} |",
             f"| B · sube sólo el lactato | lactato {_n(b['lactate'])} → {_n(p['B']['result']['lactate'])}; FR sin cambio: "
             f"{_yes(p['B']['rr_unchanged'])} |",
             f"| C · sube sólo D | D 0 → {_n(p['C']['result']['D'], 0)}; FR sin cambio: {_yes(p['C']['rr_unchanged'])} |",
             f"| D · se aclara la carga, el lactato sigue alto | carga {_n(p['D']['start']['burden'])} → "
             f"{_n(p['D']['end']['burden'])}, FR {_n(p['D']['start']['rr'])} → {_n(p['D']['end']['rr'])}, lactato "
             f"{_n(p['D']['start']['lactate'])} → {_n(p['D']['end']['lactate'])} |",
             f"| E1 · eficiencia 0,5 con carga alta | FR {_n(p['E1']['result']['rr'])}, W {_n(p['E1']['result']['w'], 2)} "
             f"(≤ 1: {_yes(p['E1']['w_at_most_1'])}) |",
             f"| E2 · la eficiencia cae de 1 a 0,5 mientras sube la carga | FR {_n(e2[0]['rr'])} → {_n(e2[-1]['rr'])}, W "
             f"{_n(e2[0]['w'], 2)} → {_n(e2[-1]['w'], 2)}, PaCO2 {_n(e2[0]['paco2'])} → {_n(e2[-1]['paco2'])} |",
             f"| F · baja la producción de CO2, carga fija | W {_n(b['w'], 2)} → {_n(p['F']['result']['w'], 2)}, PaCO2 "
             f"{_n(b['paco2'])} → {_n(p['F']['result']['paco2'])} |",
             f"| G · sube la producción de CO2, carga fija | W {_n(b['w'], 2)} → {_n(p['G']['result']['w'], 2)}, PaCO2 "
             f"{_n(b['paco2'])} → {_n(p['G']['result']['paco2'])} |",
             f"| H · pH de HCO3 y PaCO2 | carga 10: HCO3 {_n(p['H']['acid_up']['hco3'])}, PaCO2 "
             f"{_n(p['H']['acid_up']['paco2'])}, pH {_n(p['H']['acid_up']['ph'], 3)}; fórmula exacta: "
             f"{_yes(p['H']['ph_formula'])}; menos PaCO2, más pH: {_yes(p['H']['lower_paco2_higher_ph'])} |",
             f"| canal W ± 0,5 | FR sin cambio: {_yes(p['W_channel']['rr_unchanged'])} |"]
    return "\n".join(lines)


def _table(t: dict) -> list:
    rows = ["| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m, c in t["minutes"].items():
        u = t["upstream"][m]
        hem = t["haemostasis"][m]
        intervention = (f"cristaloide {_s(u['crystalloid_ml'], 0)} mL; GR {_s(u['prbc_units'], 1)} U; "
                        f"hemostasia {hem}/{t['trajectories']}")
        rows.append(f"| {m} | {_s(c['rr'])} | {_s(c['drive'])} | {_s(c['burden'])} | {_s(c['hco3'])} | {_s(c['w'], 2)} | "
                    f"{_s(c['paco2'])} | {_s(c['ph'], 2)} | {_s(u['lactate'])} | {_s(u['D'], 0)} | {_s(u['deficit'], 2)} | "
                    f"{intervention} |")
    return rows


def render_reconstruccion(data: dict) -> str:
    tables = data["reconstruction"]
    lines = [data["design"]["reconstruction_rule"], "",
             "Mediana [rango] sobre las trayectorias únicas y los candidatos compatibles en la llegada (FR intrínseca y "
             "ganancia de cada caso; B y τ, los nueve pares), a la ganancia de tono intermedia g = 0,5. Eficiencia "
             "ventilatoria 1 en todas. Las otras ganancias de tono están en el JSON (§10 da la dependencia)."]
    for factor in ("x1", "x1.1"):
        for name in ("P1", "P2", "P3", "P4"):
            for case in ("gi_bleed_57m", "gi_bleed_72f"):
                key = f"{factor} g0.5 {name} {case}"
                t = tables[key]
                lines += ["", f"**{SCENARIO_ES[name]} · {CASE_ES[case]} · demanda {factor[1:].replace('.', ',')}** "
                              f"({t['trajectories']} trayectorias; FR intrínseca {', '.join(_n(x, 0) for x in t['intrinsic'])})",
                          ""] + _table(t)
    return "\n".join(lines)


def render_preguntas(data: dict) -> str:
    q = data["key_questions"]
    q1, q2, q3 = q["1_untreated_acid_and_drive"], q["2_72f_early_dip"], q["3_post_resuscitation"]
    pairs = "; ".join(f"B/τ {k.replace('.', ',')}: {_share(v)}" for k, v in q1["by_pair"].items())
    dips = "; ".join(f"B {k.replace('.', ',')}: {_share(v)}" for k, v in q2["by_b"].items())
    return "\n".join([
        "1. **Hemorragia sin tratamiento:** la carga nunca baja en "
        f"{_share(q1['burden_non_decreasing'])} combinaciones (57m {_share(q1['by_case']['gi_bleed_57m'])}; 72f "
        f"{_share(q1['by_case']['gi_bleed_72f'])}); a los 120 min está en o sobre la de llegada en "
        f"{_share(q1['burden_120_at_or_above_arrival'])}. Por par: {pairs}.",
        f"2. **Bradipnea precoz de 72f:** caída de la FR en los primeros 30 min en {_share(q2['dip'])} ({dips}); "
        f"profundidad {_s(q2['depth'], 2)} rpm. Mecanismo: {q2['mechanism']}.",
        f"3. **Tras la reanimación (R4):** mayor paso de FR por minuto {_s(q3['max_rr_step'], 2)} rpm; 15 min después de "
        f"la hemostasia la FR sigue {_s(q3['rr_15_after_haemostasis_above_intrinsic'])} rpm sobre la intrínseca "
        f"(≥ 1 rpm en {_share(q3['no_instant_normalization'])}); a los 120 min, {_s(q3['rr_120_above_intrinsic'])} rpm "
        f"sobre la intrínseca. El paso del minuto de la hemostasia no supera a otro minuto en "
        f"{_share(q3['haemostasis_step_vs_others'])}. PaCO2 en reposo implícita {_s(q3['rest_paco2'])} mmHg; a los "
        f"120 min la PaCO2 está {_s(q3['paco2_120_below_rest'])} mmHg por debajo de ella y sube hacia ella.",
        f"4. **Lactato y FR en sentidos opuestos** al menos un minuto en {_share(q['4_lactate_rr_opposite'])} "
        "combinaciones.",
        f"5. **FR alta con ventilación efectiva insuficiente:** E1 W ≤ 1 con taquipnea: "
        f"{_yes(q['5_rr_w_dissociation']['E1_w_at_most_1'])}; E2 PaCO2 sube pese a la taquipnea: "
        f"{_yes(q['5_rr_w_dissociation']['E2_paco2_rises_despite_tachypnoea'])}."])


def render_dependencias(data: dict) -> str:
    d = data["dependencies"]
    return "\n".join([
        "| magnitud | vía | efecto |", "|---|---|---|",
        f"| demanda 1,0 / 1,1 | {d['demand']['path']} | carga a 120 min (mediana), diferencia "
        f"{_s(d['demand']['median_burden_120_difference'], 2)} mEq/L |",
        f"| ganancia de tono g | {d['tone_gain']['path']} | carga a 120 min (mediana), dispersión entre g "
        f"{_s(d['tone_gain']['median_burden_120_spread'], 2)} mEq/L |",
        f"| MAP_set | {d['map_set']['path']} | {d['map_set']['proof']} |",
        f"| ganancia del barorreflejo | {d['baroreflex_gain']['path']} | {d['baroreflex_gain']['proof']} |",
        f"| región latente de FC | {d['hr_latent']['path']} | {d['hr_latent']['proof']} |",
        "", "Se multiplican sólo: " + ", ".join(d["multiplied"]) + "."])


def render_identificabilidad(data: dict) -> str:
    i = data["identifiability"]
    lines = ["| magnitud | clase | detalle |", "|---|---|---|"]
    for key, label in IDENT_ES.items():
        item = i[key]
        detail = item.get("why") or ("valores compatibles: " + ", ".join(_n(v, 3 if "gain" in key else 0)
                                                                         for v in item.get("values", [])))
        if key == "w_efficiency":
            detail += "; PaCO2 en reposo implícita: " + "; ".join(
                f"{CASE_ES[c]} {_s(v)}" for c, v in item["resting_paco2"].items())
        lines.append(f"| {label} | {item['class']} | {detail} |")
    lines += ["", i["rule"]]
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    lines = [f"**{v['verdict']}**", "", "| criterio | se cumple |", "|---|---|"]
    lines += [f"| {CRITERIA_ES[k]} | {_yes(ok)} |" for k, ok in v["checks"].items()]
    val = data["validation"]
    lines += ["", f"- Validación contra el núcleo: {val['compared']} corridas completas con el candidato de validación "
                  f"(ganancia {_n(val['candidate'][0], 1)}, intrínseca {_n(val['candidate'][1], 0)} / "
                  f"{_n(val['candidate'][2], 0)}, B {_n(val['candidate'][3])}, τ {_n(val['candidate'][4], 0)}): iguales "
                  f"{_yes(val['equal'])} (diferencia máxima {val['max_abs_diff']}); aguas arriba iguales a la corrida sin "
                  f"la candidata: {_yes(val['upstream_equal'])}.",
              f"- Perfil por defecto: la FR, D, el lactato y el déficit de P2K-1 recalculados iguales al registro: "
              f"{_yes(data['p2k1_unchanged'])}; región de P2J-3 recalculada igual: "
              + ", ".join(f"{k} {_yes(x)}" for k, x in data["pressure_tone_unchanged"].items()) + ".",
              "- Prueba AST de las inserciones de P2K-2: " + ", ".join(f"`{k}` {_yes(x)}" for k, x in data["proofs"].items())
              + ".",
              f"- Rechazos: ANALYTIC_REJECTION {data['rejections']['ANALYTIC_REJECTION']}, SIMULATION_REJECTION "
              f"{data['rejections']['SIMULATION_REJECTION']}.", "",
              "**Paquete de decisión que se prepara (sin filtrar):**"]
    lines += [f"- {x}" for x in data["design"]["decision_pack"]]
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return (f"P2J-3 recalculado: {e['p2j3_blood_runs']} trayectorias de sangre y {e['p2j3_counterfactual_runs']} "
            f"contrafactuales. {e['deficit_trajectories']} trayectorias de déficit reconstruidas una vez; la carga se "
            f"integra para {e['acid_pairs']} pares (B, τ) y la FR, W, PaCO2 y pH son álgebra de la carga para los "
            f"{e['compatible_triples']} candidatos compatibles en la llegada (de {e['combinations']} combinaciones "
            f"posibles, factorizadas). Corridas completas del núcleo: {e['core_validation_runs']} (validación). Barrido "
            f"cartesiano: {_yes(e['cartesian_sweep'])}; FR heredada leída: {_yes(e['legacy_read'])}.")


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the P2K-2 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
