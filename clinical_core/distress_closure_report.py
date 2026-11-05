"""P2T-1A report: the generated blocks of docs/revision/P2T1A_CIERRE_DISTRES.md.

    python -m clinical_core.distress_closure_report --write <document> --data <the P2T-1A JSON>

Presentation only, downstream of every numerical artifact (lactate_slice.DOWNSTREAM_REPORTS): it reads the frozen
evaluation's JSON and writes it in Spanish. It computes no verdict, changes no rule and selects nothing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acid_base_report import _n, _yes

NAMES = ("auditoria", "m1", "l1", "no_regresion", "prueba", "veredicto")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}


def _list(values) -> str:
    return ", ".join(f"`{v}`" for v in values) or "ninguna"


def _g(value) -> str:
    return value if isinstance(value, str) else f"{value:.3g}"


def render_auditoria(data: dict) -> str:
    a = data["audit"]
    return "\n".join([
        f"- `derived.py`: funciones cambiadas {_list(a['derived']['changed'])}; añadidas "
        f"{_list(a['derived']['added'])}; retiradas {_list(a['derived']['removed'])}.",
        f"- `integration.py`: funciones cambiadas {_list(a['integration']['changed'])}; añadidas "
        f"{_list(a['integration']['added'])}; retiradas {_list(a['integration']['removed'])}.",
        f"- La guarda la llaman {_list(a['guard_callers']['derived'])} (`derived.py`) y "
        f"{_list(a['guard_callers']['integration'])} (`integration.py`); lee sólo {_list(a['guard_reads'])}.",
        f"- La suma la llaman {_list(a['sum_callers'])}; sus constantes numéricas son {_list(a['sum_constants'])} y sus "
        f"llamadas {_list(a['sum_calls'])}.",
        f"- Lectores del ancla de PaCO2 de llegada: {_list(a['anchor_readers'])}; idénticos a los de P2T-1: "
        f"{_yes(a['anchor_readers_are_p2t1s'])}. La guarda no lee ningún ancla: {_yes(a['guard_reads_no_anchor'])}.",
        f"- Pasa: {_yes(a['pass'])}."])


def render_m1(data: dict) -> str:
    m = data["m1"]
    lines = [f"- Clasificación: **{m['classification']}**; opción 2: **{m['option_2']}**.",
             "- Rechazos con la mecánica apagada y distrés 5 (sintético): "
             + ", ".join(f"{k} {_yes(v)}" for k, v in m["refused"].items()) + ".",
             "", "| Mapeo comprometido | Mecánica | Lector respiratorio rechazado | Sólo simpático aceptado |",
             "|---|---|---|---|"]
    lines += [f"| {k} | {_yes(v['mechanics_candidate'])} | {_yes(v['refused'])} | {_yes(v['sympathetic_only_accepted'])} |"
              for k, v in m["committed"].items()]
    s, z, o = m["sympathetic_only"], m["distress_zero"], m["mechanics_on"]
    rows = list(o["rows"].values())
    lines += ["",
              f"- Sólo el lector simpático, mecánica apagada: FC {_n(s['distress_0']['hr'], 2)} → "
              f"{_n(s['arrival']['hr'], 2)}; FR, PaCO2, pH y W sin cambio {_yes(s['rr_paco2_unchanged'])}; escritor "
              f"en evolución {', '.join(_n(v, 1) for v in s['evolving_trail'])}.",
              f"- Distrés 0 con ambos lectores y la mecánica apagada: lectura idéntica a la de los lectores UNSET "
              f"{_yes(z['same_as_unset'])}; un cambio de 0 aceptado {_yes(z['evolving_zero_change_accepted'])}.",
              f"- Mecánica encendida, distrés 5: FR {_n(rows[0]['rr'], 2)}; la PaCO2 ({_n(rows[0]['paco2'], 2)}) es la "
              f"misma con PaCO2 de llegada {' y '.join(o['rows'])}: {_yes(o['paco2_ignores_the_arrival_paco2'])}; "
              f"escritor en evolución {', '.join(_n(v, 1) for v in o['evolving_trail'])}.",
              f"- Por defecto: lectores UNSET {_yes(m['default']['readers_unset'])}; llegada aceptada "
              f"{_yes(m['default']['default_arrival_accepted'])}.",
              f"- Pasa: {_yes(m['pass'])}."]
    return "\n".join(lines)


def render_l1(data: dict) -> str:
    l1 = data["l1"]
    a, b, c, d, e, f = (l1[k] for k in "ABCDEF")
    lines = [f"- Tolerancia: {l1['tolerance']}.",
             f"- **A.** +0,3 −0,1 −0,2: la suma binaria da {_g(a['raw_one_minute'])}; en un minuto "
             f"{_g(a['one_minute'][-1])}, en tres {_g(a['three_minutes'][-1])}. Pasa: {_yes(a['pass'])}.",
             f"- **B.** Los 6 órdenes en un minuto dan 0; {len(b['sequences'])} secuencias por minutos terminan en 0 y "
             f"{len(b['refused_sequences'])} se rechazan, exactamente las que cierran algún minuto materialmente por "
             f"debajo de 0: {_yes(b['refused_exactly_when_a_minute_ends_materially_below_0'])}. Pasa: {_yes(b['pass'])}.",
             "", "| Caso | Suma binaria | Cota de redondeo | Decisión |", "|---|---|---|---|"]
    for label, part in (("C", c), ("D", d)):
        lines += [f"| {label} {k} | {_g(v['raw'])} | {_g(v['bound'])} | {_g(v['decided'])} |"
                  for k, v in part["rows"].items()]
    lines += [f"| E {k} | {_g(v['raw'])} | — | {_g(v['decided'])} |" for k, v in e["rows"].items()]
    lines += ["",
              f"- **C** pasa {_yes(c['pass'])}; **D** pasa {_yes(d['pass'])} (la integración también los rechaza); "
              f"**E** pasa {_yes(e['pass'])}.",
              f"- **F.** Campos del perfil iguales a los de P2T-1 {_yes(f['profile_fields_are_p2t1s'])}; nombres del "
              f"registro de parámetros iguales {_yes(f['parameter_names_are_p2t1s'])}; constantes de la suma "
              f"{_list(f['sum_constants'])}; las decisiones no cambian al escalar todo por "
              f"{', '.join(f['scaled'])}. Pasa: {_yes(f['pass'])}.",
              f"- Pasa: {_yes(l1['pass'])}."]
    return "\n".join(lines)


def render_no_regresion(data: dict) -> str:
    n = data["non_regression"]
    probes = ", ".join(f"{k} {_yes(v)}" for k, v in sorted(n["p2t1_probes_live"].items(), key=lambda kv: int(kv[0][1:])))
    return "\n".join([
        f"- D1–D12 de P2T-1 en vivo (con la guarda): {probes}.",
        "- Otras secciones de P2T-1 en vivo: " + ", ".join(f"{k} {_yes(v)}" for k, v in n["p2t1_sections_live"].items())
        + ".",
        f"- Los contrastes de P2T-1 en vivo quedan rechazados por M1 (edema y TEP con la mecánica apagada): "
        f"{_yes(n['p2t1_contrasts_live_refused_by_m1'])}.",
        f"- El registro de P2T-1 se reproduce sobre su propio árbol: {_yes(n['p2t1_record_reproduced_on_its_tree'])}; su "
        f"digest de congelación {_yes(n['p2t1_freeze_digest_on_its_tree'])}; el archivo intacto "
        f"{_yes(n['p2t1_record_untouched'])}.",
        f"- Registros de P2S-2 y P2S-3 reproducidos: {_yes(n['p2s2_p2s3_records_reproduced'])}; veredicto histórico de "
        f"P2S-3 `{n['p2s3_historical_verdict']}`, clasificación vigente `{n['p2s3_classification']}`.",
        f"- Perfiles comprometidos con los lectores UNSET: {_yes(n['committed_profiles_unset'])}. "
        f"{n['systemic_stress']}.",
        f"- Pasa: {_yes(n['pass'])}."])


def render_prueba(data: dict) -> str:
    p = data["proof"]
    return "\n".join([
        "- Inserciones declaradas revertidas a los archivos de P2T-1: "
        f"{', '.join(f'`{k}` {_yes(v)}' for k, v in p['proofs'].items())}.",
        f"- Archivos comunes fijados por hash: {len(p['common_untouched'])}, intactos "
        f"{_yes(all(p['common_untouched'].values()))}.",
        f"- Vista de P2T-1: digest de congelación {_yes(p['p2t1_freeze_digest'])}, su prueba contra P2S-3 "
        f"{_yes(p['p2t1_proof'])}, registro {_yes(p['p2t1_record'])}."])


def render_veredicto(data: dict) -> str:
    r = data["readiness"]
    lines = [f"- {_yes(c['holds'])} — {c['criterion']}" for c in r["criteria"]]
    lines += ["", f"**Veredicto: {r['verdict']}**", "", f"M1: {r['m1']}; {r['option_2']}."]
    return "\n".join(lines)


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True, help="the document to update in place")
    parser.add_argument("--data", type=Path, required=True, help="the P2T-1A JSON")
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
