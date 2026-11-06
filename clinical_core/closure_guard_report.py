"""Render P2X-1A's record into docs/revision/P2X1A_REPARACION_GUARDAS_CIERRE.md.

    python -m clinical_core.closure_guard_report --write <document.md> --data <record.json>

Shadow and offline: it reads the record the frozen package produced and writes only between the generated markers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

NAMES = ("decisiones", "interpretacion", "guardas", "contrato", "sondas", "contradicciones", "deuda",
         "supersesion", "no_regresion", "veredicto")
MARKERS = {name: (f"<!-- generado:{name} -->\n", f"<!-- /generado:{name} -->") for name in NAMES}
PROBES = tuple(f"A{i}" for i in range(1, 23))


def _yes(value) -> str:
    return "sí" if value else "NO"


def _n(value, digits=4) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    return f"{value:.{digits}f}".replace(".", ",")


def render_decisiones(data: dict) -> str:
    return "\n".join(f"- **{key}:** {value}" for key, value in data["design"]["decisions"].items())


def render_interpretacion(data: dict) -> str:
    i = data["design"]["interpretation"]
    return "\n".join(f"- **{key}:** {value}" for key, value in i.items())


def render_guardas(data: dict) -> str:
    g = data["guards"]
    own, strict = g["ownership"], g["strict_domain"]
    lines = [
        f"- Propiedad del canal T: `{own['function']}`, llamada desde `step` sin condición: "
        f"{_yes(own['at_statement_level'])}; antes de reconstruir el canal: "
        f"{_yes(own['before_the_channel_rebuild'])}; fuera de la respuesta: "
        f"{_yes(own['out_of_the_response'])}.",
        f"- Qué rechaza: {own['refuses']}.",
        f"- Frontera por minuto: `{strict['per_minute'][0]}` — estricta: {_yes(strict['strict'])}; "
        f"reconstrucción comprobada: {_yes(strict['reconstruction_checked'])}; excepción: "
        f"`{strict['exception']}`.",
        f"- Admisibilidad por parámetros: {_yes(strict['parameter_level'])}, y sin condicionar al lector: "
        f"{_yes(strict['unconditional_parameter_level'])}.",
        f"- Sin épsilon, margen ni tolerancia: {_yes(strict['no_tolerance_constant'])} "
        f"(literales float distintos de 0 y 1: "
        f"{strict['float_literals_other_than_0_and_1'] or 'ninguno'}).",
        f"- Chequeos de P2J-2 intactos: invariante de perfil {_yes(g['p2j2_untouched']['profile_invariant'])}, "
        f"chequeo de ganancia {_yes(g['p2j2_untouched']['gain_check'])}, rechazo de composición "
        f"{_yes(g['p2j2_untouched']['composition_refusal'])}.",
        f"- Resultados de P2X-1 intactos: cota de contracción {_yes(g['p2x1_untouched']['contraction_guard'])}, "
        f"condicionada al lector {_yes(g['p2x1_untouched']['reader_conditional_contraction'])}, forma cerrada "
        f"{_yes(g['p2x1_untouched']['tone_domain_closed_form'])}.",
        f"- El recorte sigue siendo la última capa de seguridad: {_yes(g['clamp_still_the_last_layer'])}; el delta "
        f"devuelto es `{g['delta_expression']}`.",
        "",
        "Rechazos, por función:",
    ]
    for name, items in g["refusals"].items():
        lines.append(f"- `{name}`:")
        # The record keeps each refusal cut at a fixed width, and a cut can land on a space: the document does not.
        lines += [f"  {index + 1}. {text}".rstrip() for index, text in enumerate(items)]
    return "\n".join(lines)


def render_contrato(data: dict) -> str:
    c = data["writer_contract"]
    lines = [
        f"- Contrato declarado en `provenance.VasodilationChange`: {_yes(c['contract_declared'])}; refuerzo de "
        f"P2X-1A declarado: {_yes(c['p2x1a_strengthening_declared'])}.",
        f"- Observables prohibidos ({len(c['forbidden_reads'])}): {', '.join(c['forbidden_reads'])}.",
        f"- Archivos del repositorio escaneados que construyen el registro: {c['files_scanned']}.",
        f"- Escritores encontrados: {', '.join(f'`{w}`' for w in c['writers']) or 'ninguno'}.",
        f"- Infractores: {c['offenders'] or 'ninguno'}.",
        f"- Entradas permitidas: {c['allowed_inputs']}.",
        "",
        "| Evasión que la revisión de P2X-1 encontró | Rechazada |",
        "|---|---|",
    ]
    for name, rejected in c["bypasses_rejected"].items():
        lines.append(f"| {name} | {_yes(rejected)} |")
    lines.append("")
    lines.append(f"- Patrón permitido, aceptado: {_yes(c['allowed_pattern_accepted'])}.")
    return "\n".join(lines)


def render_sondas(data: dict) -> str:
    probes, design = data["probes"], data["design"]["probes"]
    lines = ["| Sonda | Qué exige | Pasa |", "|---|---|---|"]
    for name in PROBES:
        lines.append(f"| {name} | {design.get(name, '')} | {_yes(probes[name]['pass'])} |")
    a4, a8, a9 = probes["A4"], probes["A8"], probes["A9"]
    lines += [
        "",
        f"- A4: con k = 1 y carga de llegada 0, una carga de {_n(a4['burden'], 1)} deja el objetivo exactamente en "
        f"{_n(a4['target'], 6)}, el extremo inferior: rechazado {_yes(a4['refused'])} con el dominio admisible "
        f"{_yes(a4['domain_admissible'])}.",
        f"- A8: con carga {_n(a8['burden'], 1)} el objetivo es {_n(a8['target'], 6)} y el canal guarda "
        f"{_n(a8['rebuilt'], 6)}; la diferencia de reconstrucción es {a8['rebuild_difference']:.3e} y el minuto "
        f"aceptado no tiene recortes: {_yes(not a8['clamps'])}.",
        f"- A9: la carga recorre {a9['burden_trail']} y el tono {[round(t, 6) for t in a9['tone']]}; recortes en "
        f"todos los minutos: {a9['clamps']}.",
    ]
    a13, a14 = probes["A13"], probes["A14"]
    for key, row in a13["witnesses"].items():
        lines.append(f"- A13 {key}: cota {_n(row['bound'], 4)} = {_n(row['bound_without_the_factor'], 4)} x "
                     f"{_n(row['recovery_max'], 4)} (factor dentro de la cota: "
                     f"{_yes(row['factor_is_in_the_bound'])}), contracción {_yes(row['contraction'])}.")
    for key, row in a14["witnesses"].items():
        lines.append(f"- A14 {key}: factor distributivo {_n(row['distributive_factor'], 4)}; pendiente viva "
                     f"{ {k: round(v, 6) for k, v in row['live_slope'].items()} }, bajo la cota "
                     f"{_yes(row['under_the_bound'])}.")
    return "\n".join(lines)


def render_contradicciones(data: dict) -> str:
    c = data["contradictions"]
    lines = ["| Afirmación | Sondas que la deciden | Se sostiene |", "|---|---|---|"]
    for name, row in c["checks"].items():
        decided = ", ".join(f"{k}:{_yes(v)}" for k, v in row["probes"].items())
        lines.append(f"| {name} | {decided} | {_yes(row['holds'])} |")
    lines += ["", "Declarado como prosa, no como búsqueda ejecutada:"]
    lines += [f"- {key}: {value}" for key, value in c["declared_not_executable"].items()]
    lines.append("")
    lines.append(f"- Contradicciones dentro del alcance: {c['inside_certified_scope'] or 'ninguna'}. "
                 f"Pasa: {_yes(c['pass'])}.")
    return "\n".join(lines)


def render_deuda(data: dict) -> str:
    d = data["debt_classification"]
    lines = []
    for class_name, items in d["classes"].items():
        lines.append(f"**{class_name}** ({d['counts'][class_name]}):")
        lines.append("")
        lines += [f"- `{item}`: {source}" for item, source in items.items()]
        lines.append("")
    lines += [f"- Clases disjuntas: {_yes(d['classes_are_disjoint'])}; cada entrada trazada a una fila del registro: "
              f"{_yes(d['every_entry_traced'])}; cada entrada exigida clasificada: "
              f"{_yes(d['every_required_entry_classified'])}.",
              f"- Bloqueos demostrados resueltos: "
              f"{', '.join(f'{k}: {_yes(v)}' for k, v in d['closure_blockers_resolved'].items())}.",
              f"- {d['unset_is_not_a_blocker']}.",
              f"- Bloqueos: {d['blockers'] or 'ninguno'}. Pasa: {_yes(d['pass'])}."]
    return "\n".join(lines)


def render_supersesion(data: dict) -> str:
    s = data["supersession"]
    lines = []
    for name, row in s["rows"].items():
        lines.append(f"- **{name}** — estado `{row['status']}`.")
        lines.append(f"  - Qué pasó: {row['what_happened']}.")
        for side in ("historical", "superseding"):
            found = row[side]
            lines.append(f"  - {side}: `{found['document']}` ({_yes(found['document_exists'])}), "
                         f"`{found['record']}` ({_yes(found['record_exists'])}); digest de congelado "
                         f"{found['freeze_digest_matches']}, sha del registro {found['record_sha_matches']}.")
        lines.append(f"  - Historia preservada: {row['history_preserved']}.")
    live = s["live"]
    lines += ["", f"- Digest de congelado de P2X-1 recomputado sobre su árbol: {_yes(live['p2x1_digest_holds'])}; "
                  f"registro de P2W-1 intacto: {_yes(live['p2w1_record_untouched'])}.",
              f"- Problemas: {s['problems'] or 'ninguno'}. Pasa: {_yes(s['pass'])}."]
    return "\n".join(lines)


def render_no_regresion(data: dict) -> str:
    n, u = data["non_regression"], data["upstream_unchanged"]
    a21 = data["probes"]["A21"]
    lines = [
        f"- Registro de P2X-1 reproducido sobre su árbol: {_yes(n['p2x1_record_reproduced_on_its_tree'])}; intacto: "
        f"{_yes(n['p2x1_record_untouched'])}; su veredicto congelado: {n['p2x1_frozen_verdict']}.",
        f"- Archivos revertidos al texto de P2X-1: "
        f"{', '.join(f'`{k}` {_yes(v)}' for k, v in u['proofs'].items())}.",
        f"- Archivos comunes fijados por hash: {len(u['common_untouched'])}, intactos "
        f"{_yes(all(u['common_untouched'].values()))}.",
        f"- Digest de congelado de P2X-1: {_yes(u['p2x1_freeze_digest'])}.",
        f"- Trayectorias comprometidas idénticas por digest: "
        f"{_yes(all(a21['digests_match_the_predecessor'].values()))} "
        f"({len(a21['digests_match_the_predecessor'])} trayectorias, comparadas contra {a21['compared_against']}).",
        f"- Tuplas de registro: {', '.join(f'{k} {_yes(v)}' for k, v in n['tuples'].items())}.",
        f"- Pasa: {_yes(n['pass'])}.",
    ]
    return "\n".join(lines)


def render_veredicto(data: dict) -> str:
    v = data["readiness"]
    lines = [f"- {_yes(c['holds'])} — {c['criterion']}" + (f" (falla: {c['failed']})" if not c["holds"] else "")
             for c in v["criteria"]]
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
