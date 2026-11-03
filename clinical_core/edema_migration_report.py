"""P2P-1 report: the generated blocks of docs/revision/P2P1_EDEMA_PULMONAR_SOMBRA.md.

    python -m clinical_core.edema_migration_report --write <document> --data <the P2P-1 JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("caso", "llegada", "escritor", "curso", "oxigeno", "autoridad", "descongestion", "volumen", "fc", "conciencia",
         "respiracion", "tratamientos", "legado", "no_regresion", "prueba", "veredicto")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}


def _by_minute(rows: dict) -> list:
    return sorted(rows.items(), key=lambda item: int(item[0]))


def render_caso(data: dict) -> str:
    c = data["case"]
    t = c["truth"]
    return (f"- **Caso:** `{c['case']}` (familia `{c['family']}`), leído de `{c['source']}` por ruta. Regla de selección: "
            f"{c['selection_rule']}. Otra variante: `{c['other_variant']}` («{c['other_variant_diagnosis']}»).\n"
            f"- **Diagnóstico autoral:** «{t['diagnosis']}».\n"
            f"- **Signos:** PA {t['sbp']}/{t['dbp']}, FC {t['hr']} ({t['rhythm']}), SpO2 {t['spo2']} % aire ambiente, "
            f"FR {t['respiratory_rate']}, trabajo respiratorio «{t['work_of_breathing']}», llenado capilar "
            f"{t['crt_s']} s, extremidades «{t['extremities']}», «{t['mental_status']}», {t['temperature_c']} °C.\n"
            f"- **Gases y laboratorio:** arterial {t['abg_ph']} / PaCO2 {t['abg_paco2']} / PaO2 {t['abg_pao2']} "
            f"(FiO2 {t['abg_fio2_percent']} %), HCO3 {t['abg_hco3']}; venoso {t['vbg_ph']} / {t['vbg_pco2']}; lactato "
            f"{t['lactate_mmol_l']}, Hb {t['hb_g_dl']}, glucosa {t['glucose_mg_dl']}, K {t['potassium_mmol_l']}, "
            f"creatinina {t['creatinine_mg_dl']}, troponina {t['troponin_ng_l']}.\n"
            f"- **POCUS y radiografía:** VI «{t['pocus_lv']}»; VCI «{t['pocus_ivc']}»; pulmones «{t['pocus_lungs']}» "
            f"(«{t['pocus_consolidation']}»); radiografía «{t['chest_xray']}».\n"
            f"- **Exploración:** «{t['respiratory_exam']}»; «{t['cardiac_exam']}».\n"
            f"- **Tratamientos definitivos autorales:** {', '.join(t['definitive_actions'])}.\n"
            f"- **Observaciones posteriores:** {c['later_observations']}.\n"
            f"- **Comportamiento heredado (sólo referencia):** {c['legacy_constants']}.")


def render_llegada(data: dict) -> str:
    a = data["arrival"]
    rows = ["| Canal | Papel |", "|---|---|"] + [f"| {k} | {v} |" for k, v in a["channel_roles"].items()]
    def fmt(name, value):
        return str(value) if name == "consciousness_level" else _n(value, 1)
    mism = "\n".join(f"- **{k}:** núcleo {fmt(k, v['core'])}, autoral {fmt(k, v['authored'])}. {v['class']}."
                     for k, v in a["mismatches"].items())
    exact = ", ".join(f"{k} {_yes(v)}" for k, v in a["exact"].items())
    return ("\n".join(rows) + f"\n\nExactos en la llegada: {exact}. L = 0 y G = 0 son la congestión de llegada: "
            f"{_yes(a['arrival_L_is_arrival_congestion'])}; L_rev {_n(a['l_rev'], 1)}.\n\nDiferencias:\n\n" + mism)


def render_escritor(data: dict) -> str:
    w = data["writer"]
    return (f"- Canales que escribe: {', '.join(w['channels_written'])}; flujos sanguíneos: {_yes(w['blood_flows'])}; "
            f"ajustes: {_yes(w['settings'])}; demanda: {_yes(w['demand'])}.\n"
            f"- Dueño de L: {_yes(w['authority'])}; tipo {w['kind']}; registrado: {_yes(w['registered'])}.\n"
            f"- El tratamiento descongestivo sólo publica la señal `{w['signal']}` y no escribe deltas: "
            f"{_yes(w['treatment_writes'])}.")


def render_curso(data: dict) -> str:
    u = data["untreated"]
    rows = ["| Progresión (L/min) | Minuto | L | G | SpO2 | FC | FR | PAM | Lactato | Conciencia |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for rate, v in u["region"].items():
        for m, r in _by_minute(v["at"]):
            rows.append(f"| {rate} | {m} | {_n(r['L'], 3)} | {_n(r['G'], 3)} | {_n(r['spo2'], 2)} | {_n(r['hr'], 1)} "
                        f"| {_n(r['rr'], 1)} | {_n(r['map'], 1)} | {_n(r['lactate'], 2)} | {r['consciousness_level']} |")
    dirs = "; ".join(f"{rate}: " + ", ".join(f"{k} {_yes(x)}" for k, x in v["directions"].items())
                     for rate, v in u["region"].items())
    return "\n".join(rows) + f"\n\nDirecciones: {dirs}."


def render_oxigeno(data: dict) -> str:
    o = data["oxygen"]
    rows = ["| FiO2 | Minuto | L | G | SpO2 |", "|---|---|---|---|---|"]
    for m, r in _by_minute(o["room_air"]):
        rows.append(f"| 0,21 | {m} | {_n(r['L'], 3)} | {_n(r['G'], 3)} | {_n(r['spo2'], 2)} |")
    for f, at in o["fio2"].items():
        for m, r in _by_minute(at):
            rows.append(f"| {f.replace('.', ',')} | {m} | {_n(r['L'], 3)} | {_n(r['G'], 3)} | {_n(r['spo2'], 2)} |")
    return ("\n".join(rows) + f"\n\nMonótona en FiO2: {_yes(o['monotone_in_fio2'])}. Ganancia de FiO2 0,6 a los 30 min "
            f"{_n(o['gain_at_30'], 2)} y a los 120 min {_n(o['gain_at_120'], 2)}: atenuada al empeorar G "
            f"{_yes(o['attenuated_as_G_worsens'])}. Sin función de oxígeno propia de la familia.")


def render_autoridad(data: dict) -> str:
    a = data["authority"]
    return (f"- Escritor de familia más sobrecarga común: {a['owned']['common_writes']} escrituras comunes; L igual a la "
            f"del escritor solo: {_yes(a['owned']['L_equals_writer_alone'])}; L final {_n(a['owned']['L_end'], 3)}; V se "
            f"mueve: {_yes(a['owned']['V_moved'])}.\n"
            f"- Sin escritor de familia: {a['common_only']['common_writes']} escrituras comunes; L final "
            f"{_n(a['common_only']['L_end'], 3)}.\n"
            f"- Dueño con ganancia 0: {a['zero_gain_owner']['common_writes']} escrituras comunes; L final "
            f"{_n(a['zero_gain_owner']['L_end'], 3)} (aceptado).\n"
            f"- Un segundo dueño (el escritor ACS) se rechaza: {_yes(a['second_owner_refused'])}.")


def render_descongestion(data: dict) -> str:
    d = data["decongestion"]
    rows = ["| Minuto | L | G | SpO2 | V | P |", "|---|---|---|---|---|---|"]
    rows += [f"| {m} | {_n(r['L'], 3)} | {_n(r['G'], 3)} | {_n(r['spo2'], 2)} | {_n(r['V'], 1)} | {_n(r['P'], 3)} |"
             for m, r in _by_minute(d["at"])]
    s = d["scripted_below_arrival"]
    return ("\n".join(rows) + f"\n\nL_rev {_n(d['l_rev'], 1)}; L mínima {_n(d['L_min'], 3)}; SpO2 máxima "
            f"{_n(d['spo2_max'], 1)}. Mejora tras el tratamiento: {_yes(d['improves_after_treatment'])}; vuelve a la "
            f"llegada: {_yes(d['back_to_arrival'])}; nunca por debajo: {_yes(d['never_below_arrival'])}; V y P sin "
            f"cambio: {_yes(d['V_P_unchanged'])}. Sonda guionizada bajo la llegada: L {_n(s['L'], 2)}, G {_n(s['G'], 2)}, "
            f"SpO2 {_n(s['spo2'], 1)} (sin crédito: {_yes(d['no_below_arrival_credit'])}).")


def render_volumen(data: dict) -> str:
    v = data["volume_loading"]
    w, b = v["without"], v["with"]
    return (f"Evento crítico autoral `{v['event']}` (sonda SYNTHETIC_ONLY de {_n(v['volume_ml'], 0)} mL a los 120 min): "
            f"L {_n(w['L'], 3)} → {_n(b['L'], 3)}, SpO2 {_n(w['spo2'], 2)} → {_n(b['spo2'], 2)}, PAM {_n(w['map'], 1)} → "
            f"{_n(b['map'], 1)}, aporte {_n(w['delivery_index'], 3)} → {_n(b['delivery_index'], 3)}; posición de "
            f"precarga {_n(v['position_with'], 3)} bajo la rodilla {_n(v['knee'], 2)}. L sin cambio: "
            f"{_yes(v['L_unchanged'])}. {v['class']}.")


def render_fc(data: dict) -> str:
    h = data["heart_rate"]
    return (f"FC a los 120 min (progresión más rápida): sin escritor {_n(h['hr_120']['no_writer'], 1)}, sin tratar "
            f"{_n(h['hr_120']['untreated'], 1)}, con FiO2 0,6 {_n(h['hr_120']['oxygen'], 1)}. Diferencias "
            f"{_n(h['untreated_minus_no_writer'], 2)} y {_n(h['oxygen_minus_untreated'], 2)} lpm; objetivo del impulso "
            f"{_n(h['target_120']['no_writer'], 3)} / {_n(h['target_120']['untreated'], 3)} / "
            f"{_n(h['target_120']['oxygen'], 3)}. Umbral {_n(h['threshold'], 0)}; ninguna ganancia se retocó.")


def render_conciencia(data: dict) -> str:
    c = data["consciousness"]
    return (f"Nivel en la llegada: núcleo {c['arrival_level_core']}, autoral {c['arrival_level_authored']}. Niveles "
            f"durante el curso: sin tratar {c['levels']['untreated']}, con oxígeno {c['levels']['oxygen']}. `derive` lee "
            f"el candidato de P2L-2: {_yes(c['derive_reads_p2l2_candidate'])}.\n\n{c['guard']}.")


def render_respiracion(data: dict) -> str:
    r = data["respiration"]
    return (f"FR autoral {r['authored_rr']}, FR común en la llegada {_n(r['core_rr_arrival'], 1)} (brecha "
            f"{_n(r['gap'], 1)}); la FR común sigue a L o G: {_yes(r['rr_follows_L_or_G'])}. Trabajo respiratorio "
            f"«{r['work_of_breathing']}», pH {r['ph']}, PaCO2 {r['paco2']}. Acciones diferidas: "
            f"{', '.join(r['deferred_actions'])}. Falta: {'; '.join(r['needs'])}. Clase: `{r['classification']}`; "
            f"esperada: {_yes(r['extension_expected'])}. Tendencias sin tratar (minuto 0 → 120, progresión más "
            f"rápida): " + "; ".join(f"{k} {_n(v[0], 2)} → {_n(v[1], 2)}" for k, v in r["untreated_trends"].items())
            + ": la FR común baja con el ácido de llegada y el lactato baja con su exceso, mientras la SpO2 empeora.")


def render_tratamientos(data: dict) -> str:
    t = data["treatments"]
    rows = ["| Tratamiento | Clase | Objetivo |", "|---|---|---|"]
    rows += [f"| {k} | {v['class']} | {v['target']} |" for k, v in t["map"].items()]
    return "\n".join(rows) + f"\n\nMagnitudes: {t['magnitudes']}."


def render_legado(data: dict) -> str:
    lc = data["legacy_comparison"]
    rows = ["| Minuto | Legado SpO2 | Núcleo SpO2 | Legado FR | Núcleo FR | Legado FC | Núcleo FC | Legado conciencia | "
            "Núcleo conciencia |", "|---|---|---|---|---|---|---|---|---|"]
    for m, r in sorted(lc["rows"].items(), key=lambda item: int(item[0])):
        lg, cr = r["legacy"], r["core"]
        rows.append(f"| {m} | {lg.get('spo2')} | {_n(cr['spo2'], 1)} | {lg.get('respiratory_rate')} | {_n(cr['rr'], 1)} "
                    f"| {lg.get('hr')} | {_n(cr['hr'], 1)} | {lg.get('mental_status')} | {cr['consciousness_level']} |")
    classes = "\n".join(f"- **{k}:** {v}." for k, v in lc["classes"].items())
    return "\n".join(rows) + f"\n\n{classes}\n\nUsado para parámetros: {_yes(lc['used_for_parameters'])}."


def render_no_regresion(data: dict) -> str:
    n = data["non_regression"]
    return (f"- GI (O12 de P2O-1) reproducido: {_yes(n['gi_o12'])}.\n- Evaluación ACS de P2O-1 reproducida: "
            f"{_yes(n['acs_evaluation'])}.\n- Autoridad ACS (R7 de P2O-3) reproducida: {_yes(n['acs_authority_r7'])}; "
            f"sobrecarga común (R8): {_yes(n['common_overload_r8'])}.\n- Archivos comunes intactos: "
            f"{sum(n['common_files_untouched'].values())} de {len(n['common_files_untouched'])}.")


def render_prueba(data: dict) -> str:
    p = data["proof"]
    return ("- Tuplas reconstruidas byte a byte como las dejó P2O-3: "
            + ", ".join(f"`{k}` {_yes(v)}" for k, v in p["proofs"].items())
            + f".\n- Digest congelado de P2O-3 reproducido por la vista: {_yes(p['p2o3_freeze_digest'])}; registro de "
              f"P2O-3 intacto: {_yes(p['p2o3_record'])}.")


def render_veredicto(data: dict) -> str:
    v = data["verdict"]
    rows = ["| Criterio | Cumple |", "|---|---|"] + [f"| {k} | {_yes(x)} |" for k, x in v["criteria"].items()]
    return ("\n".join(rows) + f"\n\n**Veredicto:** {v['letter']}, `{v['verdict']}`. Arquitectura familia-escritor / "
            f"lector común satisfactoria: {_yes(v['architecture_successful'])}.\n\n**Recomendación:** "
            f"`{v['recommendation']}` (no se inicia).")


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the P2P-1 JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
