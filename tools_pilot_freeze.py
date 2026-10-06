"""Write docs/revision/PILOT_FREEZE_MANIFEST.md from the code that enforces it (Phase 0, 0K).

The manifest is generated, like the hypoglycaemia catalogue: ``pilot_freeze`` holds the
decisions and the limitations, ``pilot_acceptance`` runs the battery, and this file writes
what both say. ``test_phase0_pilot_freeze.py`` fails when the document drifts from the code.

    python3 tools_pilot_freeze.py            # print the manifest
    python3 tools_pilot_freeze.py --write    # write docs/revision/PILOT_FREEZE_MANIFEST.md
"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parent / "docs" / "revision" / "PILOT_FREEZE_MANIFEST.md"

_DECISION_ES = {"ACCEPT": "ACCEPT", "ACCEPT WITH DECLARED LIMITATION": "ACCEPT WITH DECLARED LIMITATION",
                "EXCLUDE": "EXCLUDE"}


def _cell(text):
    return str(text).replace("|", "/").replace("\n", " ")


def build():
    import curriculum
    import pilot_acceptance as acceptance
    import pilot_freeze as freeze
    rows = [acceptance.summary(variant) for variant in acceptance.variants()]
    out = [
        "# Manifiesto de congelamiento del piloto (Fase 0, 0K)",
        "",
        "Generado por `tools_pilot_freeze.py` a partir de `pilot_freeze.py` (decisiones y limitaciones) y de",
        "`pilot_acceptance.py` (batería). No se edita a mano: `test_phase0_pilot_freeze.py` falla si se aparta",
        "del código. El informe de la fase es `docs/revision/PHASE_0_PILOT_SAFETY_REPORT.md`.",
        "",
        f"- **Identificador:** `{freeze.FREEZE_ID}`.",
        "- **Regla de despliegue:** el piloto corre sobre el commit que fija `MRS_CODE_VERSION`; cada encuentro",
        "  registra el código con que empezó (`assignment.code_version`) y cada turno el código con que corrió",
        "  (`versions.code_version` del Trace). Un despliegue durante el piloto queda visible en el registro; la",
        "  regla es no desplegar mientras haya encuentros abiertos.",
        "",
        "## Versiones",
        "",
        "| Componente | Versión |",
        "|---|---|",
    ]
    for key, value in freeze.versions().items():
        out.append(f"| {key} | {_cell(value)} |")
    out += ["", "## Indicadores del entorno", "", "| Indicador | Valor exigido |", "|---|---|"]
    for key, value in freeze.RUNTIME_FLAGS.items():
        out.append(f"| `{key}` | {_cell(value)} |")
    out += ["", "## Rutas heredadas excluidas", "",
            "Los desafíos " + ", ".join(f"`{c}`" for c in freeze.EXCLUDED_LEGACY_CHALLENGES)
            + " corren sobre el motor heredado PS001 y no se asignan automáticamente a residentes (0C). Siguen en",
            "el catálogo, el sandbox docente y las pruebas; una directiva docente no puede alcanzarlos.", ""]
    accepted = [r for r in rows if r["decision"] != "EXCLUDE"]
    excluded = [r for r in rows if r["decision"] == "EXCLUDE"]
    out += ["## Desafíos permitidos", "",
            "Lo que la asignación automática puede dar a cada año (`curriculum.assignable_challenges`) y cuántos",
            "casos aceptados puede sortear cada desafío.", "",
            "| Año | Desafíos |", "|---|---|"]
    for year in (1, 2, 3):
        out.append(f"| R{year} | {', '.join(curriculum.assignable_challenges(year))} |")
    out += ["", "| Desafío | Casos aceptados que puede sortear |", "|---|---|"]
    for key in curriculum.assignable_challenges(3):
        out.append(f"| {key} | {sum(key in r['challenges'] for r in accepted)} |")
    out += ["", "## Casos: batería y decisión", "",
            "La columna de limitaciones nombra las que halló la batería en cada caso y cuenta las que el caso ya",
            "declaraba (`engine_limits` de `case_assessment_bank`, cierre prepiloto C-2026-10-02-08: congeladas con",
            "cada encuentro y mostradas al docente con «Never count these against the resident»; no se repiten",
            "aquí). Las de todo el banco (abajo) valen para los 31; tres tocan decisiones evaluadas",
            "(G-RESUSCITATION, G-LATER-ORDERS, G-READER-V3) y cada una tiene su guarda.", "",
            "| Caso | Familia | Desafíos | Motor | Batería | Limitaciones declaradas | ¿Afecta una decisión "
            "evaluada? | Decisión |",
            "|---|---|---|---|---|---|---|---|"]
    for row in rows:
        out.append("| `{case}` | {family} | {challenges} | {engine} | {battery} | {limitations} | {affects} | "
                   "**{decision}** |".format(
                       case=row["case"], family=row["family"], challenges=", ".join(row["challenges"]),
                       engine=row["engine"], battery=_cell(row["battery"]),
                       limitations=(", ".join(row["limitations"]) or "—")
                       + f" + {row['case_limits']} del caso",
                       affects="sí (con guarda)" if row["affects_assessed"] else "no",
                       decision=_DECISION_ES[row["decision"]]))
    out += ["", f"**Aceptados:** {len(accepted)} de {len(rows)} "
                f"({sum(r['decision'] == 'ACCEPT' for r in rows)} ACCEPT, "
                f"{sum(r['decision'] == 'ACCEPT WITH DECLARED LIMITATION' for r in rows)} ACCEPT WITH DECLARED "
                f"LIMITATION). **Excluidos:** {len(excluded)}.", ""]
    for row in excluded:
        out += [f"### Excluido: `{row['case']}`", "", freeze.CASES[row["case"]]["why_excluded"], ""]
    out += ["## Versiones de los casos aceptados", "",
            "Huella del texto del caso (`clinical_cases`) y de su declaración de evaluación: la segunda es la que",
            "`evaluation_basis` congela con cada encuentro al iniciar (sus 12 primeros caracteres), para comparar un",
            "encuentro con este congelamiento. Un cambio posterior en cualquiera de las dos cambia este manifiesto.", "",
            "| Caso | Huella del caso | Huella de la declaración |", "|---|---|---|"]
    for row in accepted:
        version = freeze.case_versions(row["case"])
        out.append(f"| `{row['case']}` | `{version['case']}` | `{version['declaration']}` |")
    out.append("")
    out += ["## Limitaciones de todo el banco", ""]
    for key, item in freeze.GLOBAL_LIMITATIONS.items():
        out.append(f"- **{key}** — {item['text']} *Guarda:* {item['guard']}.")
    out += ["", "## Limitaciones por caso", ""]
    for key, item in freeze.CASE_LIMITATIONS.items():
        cases = [v for v, case in freeze.CASES.items() if key in case["limitations"]]
        out.append(f"- **{key}** ({', '.join(f'`{c}`' for c in cases)}) — {item['text']} *Guarda:* {item['guard']}.")
    out += ["", "## Cómo se hace cumplir", "",
            "- **Selección de casos:** un caso excluido nunca se sortea para un residente "
            "(`cognitive_generator`) ni se ofrece para una directiva docente (`encounter_directives.case_options`);",
            "  sólo un caso nombrado explícitamente (sandbox docente, pruebas) lo alcanza.",
            "- **Análisis:** un evento del curso que el simulador decide en un caso nunca cuenta en contra del",
            "  residente (`rubric_screening.may_support_negative_feedback`, regla D).",
            "- **Batería:** `test_phase0_acceptance_battery.py` (motor, 19 categorías por caso) y",
            "  `test_phase0_acceptance_page.py` (la página real, con recarga y reanudación) cubren los 31 casos.",
            ""]
    return "\n".join(out)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    text = build()
    if "--write" in argv:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_text(text, encoding="utf-8")
        print(f"written {TARGET}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
