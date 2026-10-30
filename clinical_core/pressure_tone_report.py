"""P2J-1 report: the generated blocks of docs/revision/P2J1_PRESION_Y_TONO_VASCULAR.md.

    python -m clinical_core.pressure_tone_report --write <document> --data <the pressure / tone JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
analysis's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import pressure_tone as pt
from .lactate_rebuild_report import CASE_ES

NAMES = ("decisiones", "ecuaciones", "topes", "rodilla", "tono", "acoplamiento", "cero", "registradas", "llegada",
         "cambio", "superficie", "trayectorias", "contexto", "direcciones", "identificabilidad", "dependencia",
         "barorreflejo", "veredicto", "eficiencia")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
FACULTY_ES = {"decided": "fecha", "hr": "FC", "demand": "demanda", "pressure_to_hr": "presión → FC",
              "structure": "estructura esperada", "correction": "corrección", "scope": "alcance"}
STATUS_ES = {pt.AUTHORED: "registrada en el caso", pt.ADOPTED_LEGACY: "magnitud heredada adoptada (no aprobada)",
             pt.PROVISIONAL: "candidata provisional", pt.STRUCTURAL: "estructural",
             pt.NOT_READ: "no se lee desde P2J-1"}
SCENARIO_ES = {"P1": "P1 · sin tratamiento (L1)", "P2": "P2 · 2 L de cristaloide en 20 min, sangrado activo (L2)",
               "P3": "P3 · IBP y 2 U de GR sin hemostasia (L3 sin la endoscopia)",
               "P4": "P4 · manejo definitivo: IBP, 2 U de GR y hemostasia a los 60 (L3)"}
CHECKS_ES = {"mapping_coherent": "relación continua, suave, monótona, 0 en 0 y sin resistencia oculta",
             "tone_semantics_explicit": "rutas de T enumeradas, sin escritor clínico",
             "zero_output_consistent": "gasto cero y paro coherentes (P7)",
             "no_floor_or_knee": "sin piso ni rodilla",
             "arrival_reconstruction_available": "reconstrucción de la llegada para ambos casos y demandas",
             "candidate_surface_explicit": "superficie candidata congelada y admisible en P5",
             "upstream_unchanged": "fisiología previa sin cambios",
             "hr_feedback_deferred": "retroalimentación presión → FC aplazada",
             "directions_hold": "direcciones 1–5, 7 y 8"}
DIRECTIONS_ES = {
    "1": "si el gasto baja con T fijo, la PAM no sube (P6 y cada par de minutos consecutivos de cada trayectoria, T = 1)",
    "2": "si el gasto sube con T fijo, la PAM no baja (los mismos pares)",
    "3": "más tono con gasto fijo no baja la PAM (P5 con gasto fijo, en cada punto de poscarga)",
    "4": "sin gasto no se conserva una presión normal (P7)",
    "5": "la hemorragia sin tratamiento no normaliza sola la presión: en P1 la PAM nunca supera la de llegada en los "
         "minutos 1–120, en cada conjunto de sangre",
    "6": "la reanimación eficaz puede mejorar la presión: en P4, PAM a los 120 sobre la de llegada en al menos un "
         "conjunto (alcanzabilidad, contada)",
    "7": "la hemostasia sola no normaliza al instante: P4 es igual a P3 antes del minuto de hemostasia h, y el paso de la "
         "PAM hacia h no supera el mayor paso de un minuto anterior, en cada conjunto",
    "8": "la respuesta de la presión a líquidos o sangre pasa por la fisiología, no por la identidad del tratamiento: en "
         "cada minuto PAM = PAM de llegada × gasto × T exactamente, y `arterial_pressures` sólo lee p y la llegada",
}
IDENT_WHY_ES = {
    "tone reference level": "T vale 1 en la llegada por la regla de anclaje y ningún mecanismo GI lo mueve: cualquier "
                            "referencia queda absorbida por la presión registrada de llegada",
    "pressure mapping scale": "sólo por anclaje: la PAS y la PAD registradas de llegada de cada caso, exactas; la "
                              "reconstrucción de la llegada es exacta por construcción y no hay ninguna presión "
                              "registrada posterior, así que la forma fuera de la llegada no está probada",
    "nonlinear shape / knee": "antes de P2J-1, la rodilla y las dos ganancias no tenían ninguna presión registrada fuera "
                              "de la llegada que las acotara; desde P2J-1 no hay parámetro de forma",
    "low-output parameter": "no queda ninguno: OUTPUT_EPSILON es numérico y la regla de colapso está apagada",
    "afterload sensitivity": "sólo llega al gasto y a la presión con T ≠ 1, y T vale 1 en todos los escenarios GI",
    "pump / tone interaction": "P y T valen 1 en todos los escenarios GI; sólo las sondas sintéticas P5 y P6 los mueven",
}
IDENT_ES = {"tone reference level": "nivel de referencia del tono", "pressure mapping scale": "escala de la relación",
            "nonlinear shape / knee": "forma no lineal / rodilla", "low-output parameter": "parámetro de gasto bajo",
            "afterload sensitivity": "sensibilidad a la poscarga", "pump / tone interaction": "interacción bomba / tono"}


def _n(value, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{float(value):.{digits}f}".replace(".", ",")


def _g(value) -> str:
    if value is None:
        return "—"
    return "0" if value == 0 else f"{value:.3g}".replace(".", ",")


def _yes(value) -> str:
    return "sí" if value else "no"


def _s(item, digits: int = 1) -> str:
    if item is None:
        return "—"
    if abs(item["high"] - item["low"]) < 0.5 * 10 ** -digits:
        return _n(item["median"], digits)
    return f"{_n(item['low'], digits)} / {_n(item['median'], digits)} / {_n(item['high'], digits)}"


def render_decisiones(data: dict) -> str:
    return "\n".join(f"- **{FACULTY_ES[key]}:** {value}" for key, value in data["faculty"].items())


def render_ecuaciones(data: dict) -> str:
    lines = ["| Término | Ecuación | Parámetros | Procedencia | Valor | Estado | Alcance |", "|---|---|---|---|---|---|---|"]
    for term, equation, params, source, default, status, scope in data["equations"]:
        lines.append(f"| {term} | {equation} | {params} | {source} | {default or '—'} | {STATUS_ES[status]} | {scope} |")
    return "\n".join(lines)


def render_topes(data: dict) -> str:
    item = data["floors_caps_knees"]
    return ("**Antes de P2J-1:**\n" + "\n".join(f"- {line}" for line in item["before_p2j1"])
            + "\n\n**Desde P2J-1:**\n" + "\n".join(f"- {line}" for line in item["since_p2j1"]))


def render_rodilla(data: dict) -> str:
    lines = ["| Llegada | Antes de P2J-1 | Pendiente de PAS bajo / sobre la rodilla (×) | Pendiente de PAD (×) | "
             "Resistencia implícita con p 0,5 · 1,5 · 2 | Desde P2J-1 |", "|---|---|---|---|---|---|"]
    for name, item in data["knee"].items():
        sbp, dbp = item["prior_slopes_at_knee"]["SBP"], item["prior_slopes_at_knee"]["DBP"]
        r = item["prior"]["implicit_resistance"]
        lines.append(f"| {name} | {item['prior']['classification']} | {_n(sbp['below'])} / {_n(sbp['above'])} "
                     f"({_n(sbp['ratio'], 2)}) | {_n(dbp['below'])} / {_n(dbp['above'])} ({_n(dbp['ratio'], 2)}) | "
                     f"{_n(r['0.5'], 2)} · {_n(r['1.5'], 2)} · {_n(r['2'], 2)} | {item['current']['classification']}, "
                     f"resistencia {_n(item['current']['implicit_resistance']['0.5'], 2)} |")
    check = data["prior_matches_p2i2q"]
    lines.append("")
    lines.append(f"La réplica de la relación previa reproduce el registro de P2I-2Q, calculado por el núcleo de entonces "
                 f"(diferencia máxima {_g(check['max_difference'])}).")
    return "\n".join(lines)


def render_tono(data: dict) -> str:
    tone = data["tone"]
    reads = "; ".join(f"`{r[0]}` · {r[1]} ({r[2]})" for r in tone["reads"])
    writes = "; ".join(f"`{w[0]}` · {w[1]} ({w[2]})" for w in tone["writes"])
    return (f"- **Lecturas:** {reads}.\n- **Escrituras:** {writes}.\n"
            f"- **Escritores clínicos:** {len(tone['clinical_writers'])}. Sólo escriben T las sondas sintéticas y el "
            "valor 1 de la llegada (anclaje).")


def render_acoplamiento(data: dict) -> str:
    c = data["coupling"]
    flags = c["coupling"]
    lines = [f"- **Más tono (T 1 → 2):** el gasto baja: {_yes(flags['tone_up']['output_falls'])}; la presión sube: "
             f"{_yes(flags['tone_up']['pressure_rises'])}.",
             f"- **Menos tono (T 1 → 0,5):** el gasto sube: {_yes(flags['tone_down']['output_rises'])}; la presión baja: "
             f"{_yes(flags['tone_down']['pressure_falls'])}.",
             f"- **Más bomba (P 1 → 1,5) con T fijo:** el gasto sube: {_yes(flags['pump_up']['output_rises'])}; la "
             f"presión sube: {_yes(flags['pump_up']['pressure_rises'])}.",
             f"- **Techo del tono:** con P y precarga fijos, p no supera {_n(flags['pressure_supremum_over_tone'], 2)} "
             "veces el gasto base (1 / a), a cualquier tono.", "",
             "| a | PAM con bomba fija, T 0,5 · 1 · 2 · 3 | Gasto con bomba fija, T 0,5 · 1 · 2 · 3 | "
             "PAM con gasto fijo, T 0,5 · 1 · 2 · 3 |", "|---|---|---|---|"]
    for a, item in c["P5"].items():
        fp, fo = item["fixed_pump"], item["fixed_output"]
        lines.append(f"| {_n(float(a), 1)} | {' · '.join(_n(fp[t]['map']) for t in ('0.5', '1', '2', '3'))} | "
                     f"{' · '.join(_n(fp[t]['output'], 3) for t in ('0.5', '1', '2', '3'))} | "
                     f"{' · '.join(_n(fo[t]['map']) for t in ('0.5', '1', '2', '3'))} |")
    lines += ["", "| T | PAM con P 0,1 · 0,25 · 0,5 · 0,75 · 1 · 1,5 |", "|---|---|"]
    for t in ("1", "2"):
        lines.append(f"| {t} | {' · '.join(_n(v['map']) for v in c['P6'][t].values())} |")
    volume = c["P6"]["V at T 1"]
    lines.append(f"| 1 (V −75 %, −50 %, 0, +50 %, +100 % del llenado de llegada) | "
                 f"{' · '.join(_n(v['map']) for v in volume.values())} |")
    return "\n".join(lines)


def render_cero(data: dict) -> str:
    z = data["zero_output"]
    small = z["small_output"]
    return (f"- **Cero numérico con pulso:** {z['numerical_zero_with_pulse']} (la corrida se detiene; nunca hay pulso ni "
            "presión sin gasto).\n"
            f"- **Gasto pequeño:** PAM {_g(small['1e-06 at T 1']['map'])} y {_g(small['1e-06 at T 3']['map'])} mmHg con "
            f"P 1e-6 y T 1 o 3; {_g(small['0.001 at T 3']['map'])} mmHg con P 0,001 y T 3.\n"
            f"- **Sin pulso (AESP, asistolia, FV):** gasto 0 y PAS, PAD y PAM no medibles en los tres: "
            f"{_yes(all(v['map'] is None for v in z['pulseless'].values()))}.\n"
            f"- **Cumple:** {_yes(z['holds'])}.")


def render_registradas(data: dict) -> str:
    lines = []
    for case, item in data["authored"].items():
        lines.append(f"- **{CASE_ES[case]}:** PAS {item['sbp']['value']} y PAD {item['dbp']['value']} mmHg "
                     f"(`{item['sbp']['source']}`, AUTHORED_OBSERVATION); PAM {item['map']['value']} "
                     f"(MODEL_DERIVED, {item['map']['equation']}). Observaciones posteriores de presión registradas: "
                     f"{len(item['later'])}. El motor heredado tiene trayectorias de presión: LEGACY_REFERENCE, nunca "
                     "leídas.")
    return "\n".join(lines)


def render_llegada(data: dict) -> str:
    lines = ["| Caso · demanda | Par (D0, entrega) | Gasto | T | PAS / PAD / PAM modeladas | Registradas | Desajuste |",
             "|---|---|---|---|---|---|---|"]
    for key, row in data["arrival"].items():
        case, factor = key.split(" x")
        a = row["authored"]
        lines.append(f"| {CASE_ES[case]} · {_n(float(factor), 1)} | D0 {_n(row['D0'], 0)}, {_n(row['delivery_ratio'], 2)} | "
                     f"{_n(row['output'], 2)} | {_n(row['T'], 0)} | {_n(row['sbp'])} / {_n(row['dbp'])} / "
                     f"{_n(row['map'])} | {_n(a[0], 0)} / {_n(a[1], 0)} / {_n(a[2])} | "
                     f"{' / '.join(_n(m, 1) for m in row['mismatch'])} |")
    return "\n".join(lines)


def render_cambio(data: dict) -> str:
    c = data["changed"]
    big = c["largest_change_mmhg"]
    return (f"- **Cambia:** {', '.join(c['changed'])}.\n- **No cambia:** {', '.join(c['unchanged'])}.\n"
            f"- **Mayor cambio en las trayectorias de decisión** ({c['minutes_compared']} minutos con pulso): PAS "
            f"{_n(big['sbp'])}, PAD {_n(big['dbp'])}, PAM {_n(big['map'])} mmHg. En la llegada no cambia: "
            f"{_yes(c['arrival_unchanged'])}.")


def render_superficie(data: dict) -> str:
    s = data["candidate_surface"]
    return (f"- **Relación:** `{s['mapping']['form']}`; parámetros libres: {len(s['mapping']['free_parameters'])}. Es "
            "estructural (la corrección de P2J-1): no es candidata.\n"
            f"- **Sensibilidad a la poscarga a:** {', '.join(_n(v, 1) for v in s['afterload_sensitivity']['points'])}, la "
            "banda registrada en `calibration.REGISTRY` (P2G, provisional); una dimensión, sólo en las sondas sintéticas "
            "P5, porque sólo actúa con T ≠ 1.\n"
            f"- **Referencia del tono:** {_n(s['tone_reference']['value'], 0)}, por la regla de anclaje (§7.4 de la "
            "propuesta); no es candidata.\n"
            "- **Respuesta del tono:** `NOT_AUTHORIZED`. Ningún mecanismo escribe T; una respuesta del tono pide "
            "parámetros nuevos (ganancia, punto de ajuste, constante de tiempo) cuyos rangos debe autorizar la docencia.\n"
            f"- **Bomba:** {_n(s['pump']['value'], 0)}; ningún mecanismo GI escribe P.\n"
            "- **Fisiología previa:** la sangre y los líquidos conservados (las unidades de lactato de P2I-2AJ y P2I-2AK con "
            "demanda 1,0 y 1,1) se arrastran como incertidumbre; no se reabren ni se refiltran.\n\n"
            "**Cómo se construyó, antes de cualquier trayectoria:** la banda registrada del único parámetro de presión que "
            "queda, su límite dimensional (a < 1, para que el gasto siga positivo y la presión suba con el tono), las "
            "presiones registradas de llegada como escala y las sondas sintéticas. No se leyó ninguna trayectoria GI ni "
            "presión heredada. No hay envolventes de presión más allá de la llegada, así que no se aplica ningún filtro.")


def render_trayectorias(data: dict) -> str:
    lines = []
    for name, label in SCENARIO_ES.items():
        lines.append(f"**{label}**")
        lines.append("")
        lines.append("| Caso | Min | Gasto | PAS | PAD | PAM | PP | PAM antes de P2J-1 | Sangrado (mL/min) | Cristaloide | GR (U) |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for case in pt.CASES:
            item = data["trajectories"][f"{name} {case}"]
            for minute in map(str, pt.TIMES):
                t = item["times"][minute]
                lines.append(f"| {CASE_ES[case]} | {minute} | {_s(t['output'], 2)} | {_s(t['sbp'])} | {_s(t['dbp'])} | "
                             f"{_s(t['map'])} | {_s(t['pp'])} | {_s(t['map_prior'])} | {_s(t['bleed_ml_per_min'], 2)} | "
                             f"{_s(t['crystalloid_in_ml'], 0)} | {_s(t['prbc_units'], 2)} |")
        sets = {case: data["trajectories"][f"{name} {case}"]["blood_sets"] for case in pt.CASES}
        lines.append("")
        lines.append(f"Conjuntos de sangre: {sets[pt.C57]} (57m) y {sets[pt.C72]} (72f). T vale 1 en todos los minutos.")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_contexto(data: dict) -> str:
    context = data["dependency"]["context"]
    lines = ["| Escenario · caso · demanda | Déficit efectivo a 0 · 30 · 60 · 120 | D a 0 · 30 · 60 · 120 |", "|---|---|---|"]
    for key in sorted(context, key=lambda k: (k.split(" ")[0], k.split(" ")[1], float(k.split(" ")[2][1:]))):
        item = context[key]
        name, case, factor = key.split(" ")
        lines.append(f"| {name} · {CASE_ES[case]} · {_n(float(factor[1:]), 1)} | "
                     f"{' · '.join(_s(item[m]['deficit'], 3) for m in ('0', '30', '60', '120'))} | "
                     f"{' · '.join(_s(item[m]['D'], 1) for m in ('0', '30', '60', '120'))} |")
    return "\n".join(lines)


def render_direcciones(data: dict) -> str:
    d = data["directions"]
    lines = []
    for key in d["rule"]:
        rule, item = DIRECTIONS_ES[key], d[key]
        verdict = (f"alcanzable: {_yes(item['reachable'])} ({item['improved']} de {item['blood_sets']})" if key == "6"
                   else f"cumple: {_yes(item['holds'])}")
        extra = ""
        if key == "7":
            extra = (f" Minuto de hemostasia: {', '.join(map(str, item['haemostasis_minute']))}; efecto propio sobre la "
                     f"PAM en ese minuto: {_s(item['haemostasis_minute_effect_map'], 2)} mmHg.")
        if key == "5":
            extra = f" Conjuntos: {item['blood_sets']}; fallan: {item['failing']}."
        lines.append(f"{key}. {rule} — **{verdict}**.{extra}")
    return "\n".join(lines)


def render_identificabilidad(data: dict) -> str:
    lines = ["| Latente | Clase | Por qué |", "|---|---|---|"]
    for name, (label, _) in data["identifiability"].items():
        lines.append(f"| {IDENT_ES[name]} | {label} | {IDENT_WHY_ES[name]} |")
    return "\n".join(lines) + ("\n\nLas únicas observaciones de presión son dos, una por caso y en la llegada, donde el "
                               "modelo las reproduce por construcción. No se elige ningún conjunto.")


def render_dependencia(data: dict) -> str:
    path, dep = data["path"], data["dependency"]
    return (f"- **Código:** la ruta de la presión ({', '.join(pt.PRESSURE_PATH)}) lee {len(path['reads'])} nombres y "
            f"ninguno prohibido ({len(path['forbidden_read'])}); contribuyentes que leen derivados: "
            f"{len(path['contributors_reading_derived'])}.\n"
            f"- **Números:** {dep['full_runs']} corridas completas de la muestra (demandas 1,0 y 1,1, otro punto de "
            f"lactato y dos perfiles de FC) dan exactamente el gasto, p, PAS, PAD y PAM de la corrida sólo de sangre: "
            f"{_yes(dep['pressure_equal'])}; D cambia con la demanda: {_yes(dep['d_moves_with_demand'])}.\n"
            "- **Consecuencia:** la presión no depende de la región de FC ni de la demanda; se simula una vez por "
            "conjunto de sangre.")


def render_barorreflejo(data: dict) -> str:
    plan = data["baroreflex_plan"]
    return "\n".join([
        f"- **Estado:** `{plan['status'].split(':')[0]}`: en P2J-1 la presión → FC sigue PRESSURE_TERM_DIAGNOSTIC_ONLY.",
        "- **Señal:** la PAM absoluta que ahora deriva el dominio de la presión (mmHg, anclada en la llegada registrada) "
        "frente a un punto de ajuste que fija la docencia, max(0, PAM_ajuste − PAM) / PAM_ajuste; no el 1 − p relativo a "
        "la llegada.",
        "- **Signo:** el impulso sube cuando la PAM cae bajo el punto de ajuste y vale 0 en él o por encima; nunca es "
        "negativo (P2D-3), así que no hay bradicardia barorrefleja sin una fuente explícita que cambie R.",
        "- **El término actual 1 − p no debe quedar como está:** relativo a la llegada, vale 0 en una llegada hipotensa "
        "(88/54 es su cero), se vuelve negativo sobre la llegada y descuenta los otros estímulos de la suma, y hasta "
        "P2J-1 discrepaba de la PAM mostrada por un factor de casi dos (desde P2J-1 es exactamente el déficit relativo "
        "de la PAM mostrada respecto de la llegada).",
        "- **Doble conteo:** la señal aguda del déficit de oxígeno y un déficit de presión caen ambos con el gasto "
        "(correlación 0,75, P2I-2AF). El término de presión lee la presión (PAM) y el agudo la disponibilidad de "
        "oxígeno; la ganancia aguda se vuelve a explorar junto con la barorrefleja sobre la misma superficie de llegada "
        "y se informa la varianza compartida; el término nunca se suma encima de la región aguda actual.",
        "- **Pruebas que se repiten:** la ventana de FC de llegada ±5 lpm (P2I-2AI, P2I-2AJ) y las envolventes A–F de "
        f"P2I-2AK ({len(plan['repeat']) - 1}).",
        "- **Requiere:** primero las envolventes docentes de presión; después un punto de ajuste y un rango de ganancia "
        "autorizados antes de cualquier valor."])


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    lines = [f"**{v['verdict']}**", ""]
    lines += [f"- {CHECKS_ES[name]}: {_yes(ok)}" for name, ok in v["checks"].items()]
    lines.append(f"- Parámetros aprobados: {len(v['approved'])}.")
    return "\n".join(lines)


def render_eficiencia(data: dict) -> str:
    e = data["efficiency"]
    return (f"Trayectorias hemodinámicas para reproducir las unidades de lactato: {e['haemodynamic_trajectories']}; "
            f"corridas de presión, una por conjunto de sangre y escenario: {e['pressure_runs']} (un diseño por "
            f"candidato y demanda habría pedido {e['pressure_runs_without_sharing']}); corridas completas de "
            f"validación: {e['validation_full_runs']}; barrido cartesiano: {_yes(e['cartesian_sweep'])}; presión "
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
    parser.add_argument("--data", type=Path, required=True, help="the pressure / tone JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
