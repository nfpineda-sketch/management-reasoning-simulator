"""Render P2X-1's record into docs/revision/P2X1_CIERRE_PROPIEDADES_DECLARADAS.md.

    python -m clinical_core.tone_domain_report --write <document.md> --data <record.json>

Shadow and offline: it reads the record the frozen package produced and writes only between the generated markers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

NAMES = ("decisiones", "derivacion", "guardas", "contrato", "sondas", "supersesion", "deuda", "no_regresion",
         "prueba", "veredicto")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
PROBES = tuple(f"X{i}" for i in range(1, 16))


def _yes(value) -> str:
    return "sí" if value else "NO"


def _n(value, digits=4) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    return f"{value:.{digits}f}".replace(".", ",")


def render_decisiones(data: dict) -> str:
    return "\n".join(f"- **{key}:** {value}" for key, value in data["design"]["decisions"].items())


def render_derivacion(data: dict) -> str:
    d = data["derivation"]
    lines = [f"- {key}: `{value}`" for key, value in d["statement"].items()]
    lines += ["", "| Extremo | Observado | Predicho |", "|---|---|---|"]
    for key in d["observed"]:
        lines.append(f"| {key} | {_n(d['observed'][key], 6)} | {_n(d['predicted'][key], 6)} |")
    lines += ["", "| T | Pendiente numérica | Forma cerrada | Rama activa | Coincide | Bajo la cota |",
              "|---|---|---|---|---|---|"]
    for tone, row in sorted(d["slope"].items(), key=lambda kv: float(kv[0])):
        lines.append(f"| {tone} | {_n(row['numeric'], 6)} | {_n(row['closed_form'], 6)} | "
                     f"{_yes(row['active_branch'])} | {_yes(row['agree'])} | {_yes(row['within_bound'])} |")
    kink = d["kink"]
    lines += ["", f"- Codo de la señal (el déficit efectivo llega a 0) en T = {_n(kink['tone'], 6)}: por debajo la "
                  f"pendiente es {_n(kink['left'], 6)} (plana: {_yes(kink['flat_below_the_kink'])}) y por encima "
                  f"{_n(kink['right'], 6)} (bajo la cota: {_yes(kink['within_bound_above'])}).",
              f"- Monótona en la carga: {_yes(d['monotone_in_the_burden'])}; en el déficit: "
              f"{_yes(d['monotone_in_the_deficit'])}.",
              f"- Formas cerradas: {_yes(d['closed_forms_hold'])}; pendiente: {_yes(d['slope_closed_form_holds'])}. "
              f"Pasa: {_yes(d['pass'])}."]
    domain = data["domain"]
    lines += ["", f"- Dominio con el lector declarado: compensación [{_n(domain['compensation_min'], 6)}, "
                  f"{_n(domain['compensation_max'], 6)}], recuperación máxima {_n(domain['recovery_max'], 6)}, "
                  f"objetivo mayor {_n(domain['largest_target'], 6)}, ínfimo {domain['smallest_target']}, rango "
                  f"soportado {domain['supported']}.",
              f"- Cota del lazo derivada: {_n(domain['loop_slope_bound'], 6)}; la de P2J-2, g·a: "
              f"{_n(domain['p2j2_slope_bound'], 6)}."]
    return "\n".join(lines)


def render_guardas(data: dict) -> str:
    g = data["guards"]
    lines = [f"- Invariante de perfil de P2J-2: {g['p2j2_profile_invariant']} — intacto: "
             f"{_yes(g['p2j2_invariant_unchanged'])}.",
             f"- Chequeo de ganancia de P2J-2 intacto: {_yes(g['p2j2_gain_check_unchanged'])}.",
             f"- `tone_domain` lee: {', '.join(g['tone_domain_reads'])}.",
             f"- Admisibilidad superior: {g['upper_admissibility']}.",
             f"- Contracción: {g['contraction']}.",
             f"- Frontera por minuto: {g['per_minute_boundary']}.",
             f"- Sólo se añadieron rechazos: {_yes(g['only_refusals_added'])}; el delta devuelto sigue siendo "
             f"`{g['delta_expression']}`.", "", "Rechazos del acoplamiento, en orden:", ""]
    lines += [f"{i + 1}. {text}".rstrip() for i, text in enumerate(g["refusals"])]
    return "\n".join(lines)


def render_contrato(data: dict) -> str:
    c = data["writer_contract"]
    return "\n".join([
        f"- Contrato declarado en `provenance.VasodilationChange`: {_yes(c['contract_declared'])}.",
        f"- Entradas prohibidas a un escritor de familia: {', '.join(c['forbidden_inputs'])}.",
        f"- Entradas permitidas: {'; '.join(c['allowed_inputs'])}.",
        f"- Módulos que construyen el registro: {', '.join(f'`{m}`' for m in c['modules_that_build_the_record'])}.",
        f"- Escritores de familia: {c['family_writers'] or 'ninguno'}; infractores del contrato: "
        f"{c['offenders'] or 'ninguno'}.",
        f"- Pasa: {_yes(c['pass'])}."])


def render_sondas(data: dict) -> str:
    p = data["probes"]
    lines = ["| Sonda | Qué exige | Pasa |", "|---|---|---|"]
    for name in PROBES:
        lines.append(f"| {name} | {data['design']['probes'][name]} | {_yes(p[name]['pass'])} |")
    x3, x4, x6, x7, x9, x10 = p["X3"], p["X4"], p["X6"], p["X7"], p["X9"], p["X10"]
    lines += ["", f"- X3: con carga de llegada {x3['arrival_burden']}, sobre la rejilla {x3['grid']} el objetivo va "
                  f"{' → '.join(_n(v, 4) for v in x3['target'])}: sube al resolverse "
                  f"({_yes(x3['rises_as_it_resolves'])}) y pasa de 1 por debajo de la carga de llegada "
                  f"({_yes(x3['above_one_below_the_arrival_burden'])}).",
              "- X4: la recuperación máxima, observada y predicha: "
              + "; ".join(f"{k} → {_n(v['observed'], 6)} / {_n(v['predicted'], 6)}" for k, v in x4["rows"].items())
              + ".",
              f"- X6: con k = {x6['gain']} y b₀ = {x6['arrival_burden']} el objetivo mayor es "
              f"{_n(x6['largest_target'], 4)}, fuera de {x6['supported']}: rechazado {_yes(x6['refused'])}, aunque el "
              f"chequeo de P2J-2 pasaría ({_yes(x6['p2j2_check_would_pass'])}).",
              f"- X7: con carga {x7['burden']} el objetivo es {_n(x7['target'], 6)}, bajo el rango soportado: "
              f"rechazado {_yes(x7['refused'])}, y sin declarar ninguna carga máxima clínica "
              f"({_yes(x7['no_clinical_maximum_burden'])}).",
              "- X9: testigos aceptados, cota derivada contra la mayor pendiente viva: "
              + "; ".join(f"{k} → {_n(v['bound'], 4)} / {_n(v['largest_live_slope'], 4)}"
                          for k, v in x9["witnesses"].items()) + ".",
              f"- X10: con k = {x10['gain']} y b₀ = {x10['arrival_burden']} la cota es "
              f"{_n(x10['loop_slope_bound'], 4)} (no contracción) con el objetivo mayor "
              f"{_n(x10['largest_target'], 4)} dentro del rango: rechazado {_yes(x10['refused'])}, aunque la cota de "
              f"P2J-2 pasaría ({_yes(x10['p2j2_bound_would_pass'])})."]
    return "\n".join(lines)


def render_supersesion(data: dict) -> str:
    lines = []
    for name, row in data["supersession"]["records"].items():
        lines += [f"- **{name}** — estado `{row['status']}`.",
                  f"  - Histórico: {row['historical']}.",
                  f"  - Resuelto por: {row['resolved_by']}.",
                  f"  - Autoritativo: {row['authoritative']}.",
                  f"  - Naturaleza: {row['nature']}.",
                  f"  - Historia preservada: {row['history_preserved']}."]
    lines.append(f"\n- Digest congelado de P2W-1 intacto: {_yes(data['supersession']['p2w1_digest_unchanged'])}. "
                 f"Pasa: {_yes(data['supersession']['pass'])}.")
    return "\n".join(lines)


def render_deuda(data: dict) -> str:
    d = data["debt_classification"]
    lines = []
    for name, rows in d["classes"].items():
        lines += [f"**{name}** ({len(rows)}):", ""]
        lines += [f"- `{key}`: {value}" for key, value in rows.items()]
        lines.append("")
    lines += [f"- {d['unset_is_not_a_blocker']}.",
              f"- Bloqueos: {d['blockers'] or 'ninguno'}. Pasa: {_yes(d['pass'])}."]
    return "\n".join(lines)


def render_no_regresion(data: dict) -> str:
    n = data["non_regression"]
    c = data["contradictions"]
    lines = [f"- Registro de P2W-1 reproducido sobre su árbol: {_yes(n['p2w1_record_reproduced_on_its_tree'])}; "
             f"intacto: {_yes(n['p2w1_record_untouched'])}; su veredicto {n['p2w1_verdict']}.",
             f"- Valores por defecto de cada familia comprometida, exactos: {_yes(n['committed_defaults_exact'])}.",
             f"- Tuplas de registro: {', '.join(f'{k} {_yes(v)}' for k, v in n['tuples'].items())}.",
             f"- Pasa: {_yes(n['pass'])}.", "", "Búsqueda de contradicciones causales dentro del alcance certificado:",
             ""]
    lines += [f"- {key}: {value}" for key, value in c["searched"].items()]
    lines.append(f"\n- Contradicciones dentro del alcance: {c['inside_certified_scope'] or 'ninguna'}. "
                 f"Pasa: {_yes(c['pass'])}.")
    return "\n".join(lines)


def render_prueba(data: dict) -> str:
    p = data["proof"]
    return "\n".join([
        f"- Archivos revertidos a los de P2W-1: {', '.join(f'`{k}` {_yes(v)}' for k, v in p['proofs'].items())}.",
        f"- Archivos comunes fijados por hash: {len(p['common_untouched'])}, intactos "
        f"{_yes(all(p['common_untouched'].values()))}.",
        f"- Digest de congelado de P2W-1 sobre su árbol: {_yes(p['p2w1_freeze_digest'])}; sha de su registro "
        f"`{p['p2w1_record'][:16]}…`."])


def render_veredicto(data: dict) -> str:
    v = data["readiness"]
    lines = [f"- {_yes(c['holds'])} — {c['criterion']}" for c in v["criteria"]]
    lines += ["", f"**Veredicto: {v['verdict']}**"]
    return "\n".join(lines)


RENDERERS = {name: globals()[f"render_{name}"] for name in NAMES}


def apply(document: str, name: str, block: str) -> str:
    opening, closing = MARKERS[name]
    start = document.index(opening) + len(opening)
    end = document.index(closing, start)
    return document[:start] + block + "\n" + document[end:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    args = parser.parse_args(argv)
    document = args.write.read_text(encoding="utf-8")
    data = json.loads(args.data.read_text(encoding="utf-8"))
    for name, render in RENDERERS.items():
        document = apply(document, name, render(data))
    args.write.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
