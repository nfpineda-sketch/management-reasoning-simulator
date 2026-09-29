"""Faculty review sheets written from the code, never by hand (cycle 10, C10-02).

``python3 tools_review_sheets.py`` writes two sheets under ``docs/revision/``:

- ``DC9_COMPOSICIONES.md``: the 36 TD1/F1/C1/C3 rows proposed for the nine hypoglycaemia
  compositions (DC9), each with the case it was copied from and the facts in which the
  composition differs from that case;
- ``TD04_POCUS_C14.md``: the authored arrival POCUS of the 14 bank cases whose C14 is YES
  (TD-04), with its Spanish draft and the C14 declaration that rests on it.

A sheet approves nothing and changes nothing: every row is for a faculty member to confirm or
change, with a signature. The flags only point at facts a reviewer should look at; they never
judge a row. ``test_review_sheets_are_current.py`` fails when the code moves and the sheets were
not written again.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs" / "revision"
DC9_SHEET = OUT / "DC9_COMPOSICIONES.md"
TD04_SHEET = OUT / "TD04_POCUS_C14.md"

ROWS = ("TD1", "F1", "C1", "C3")
REVIEW_LINE = "**Revisión docente:** ☐ Confirmo tal como está · ☐ Cambio: ____________ · Firma y fecha: ________"
AXIS_ES = {"mechanism": "mecanismo", "iv_access": "vía de llegada", "severity": "gravedad"}
VALUE_ES = {"insulin": "insulina", "sulfonylurea": "sulfonilurea", "alcohol_fasting": "alcohol y ayuno",
            "working": "funciona", "failed": "fallida", "severe": "grave", "moderate": "moderada"}
POCUS_ORDER = ("lv", "rv", "pericardium", "ivc", "lung_sliding", "lungs", "lung_consolidation", "aorta_root",
               "aorta_descending", "aorta_abdominal", "dvt_femoral", "dvt_popliteal")


def _cell(text):
    return str(text).replace("|", "/").replace("\n", " ").strip()


def _configurations():
    import hypoglycemia_catalog
    return {c["id"]: c for c in hypoglycemia_catalog.configurations()}


def _row_text(row):
    parts = [row.get("rationale") or row.get("reason") or "", row.get("observable_component") or "",
             " ".join(row.get("expected_evidence") or ()), row.get("outside_the_encounter") or ""]
    return " ".join(str(p) for p in parts)


def composition_flags(composition, origin, row_id, row):
    """Facts a reviewer should look at: where the copied row speaks of the origin, not of this patient."""
    flags = []
    mine, theirs = composition["conditions"], origin["conditions"]
    text = _row_text(row)
    cited = {int(n) for n in re.findall(r"\b(\d{2,3}) ?mg/dL", text)}
    if theirs["arrival_glucose"] != mine["arrival_glucose"] and theirs["arrival_glucose"] in cited:
        flags.append(f"El texto cita {theirs['arrival_glucose']} mg/dL, la glucosa de llegada de "
                     f"`{origin['id']}`; esta composición llega con {mine['arrival_glucose']} mg/dL.")
    # F1 is the row about a treatment that has to reach the patient: the one a failed line changes.
    if (row_id == "F1" and mine["iv_access_failed"] and not theirs["iv_access_failed"]
            and not re.search(r"failed|not in the vein|infiltrat", text, re.I)):
        flags.append("La composición llega con la vía fallida; su origen no, y la fila no la menciona.")
    if theirs["iv_access_failed"] and not mine["iv_access_failed"] and re.search(r"failed|not in the vein", text, re.I):
        flags.append("La fila habla de una vía fallida y en esta composición la vía funciona.")
    if mine["sulfonylurea_effect"] != theirs["sulfonylurea_effect"] and re.search(
            r"sulfonylurea|octreotide|recurr", text, re.I):
        flags.append("La fila habla de sulfonilurea o de recurrencia, y el mecanismo de la composición es otro.")
    return flags


def dc9_sheet():
    import tdfc_declarations
    configurations = _configurations()
    proposals = tdfc_declarations.composition_proposals()
    lines = [
        "# DC9 · Filas TD/F/C propuestas para las nueve composiciones de hipoglicemia",
        "",
        "Generado por `tools_review_sheets.py` desde `tdfc_declarations.composition_proposals()` y el catálogo de",
        "hipoglicemia. **No se edita a mano** y **no aprueba nada**: cada fila es la de su caso de origen, copiada",
        "como propuesta (`PENDING FACULTY REVIEW (DC9)`), y ninguna composición se ofrece a un residente mientras",
        "tenga filas sin revisar. Las **alertas** sólo señalan hechos en que la composición difiere de su origen;",
        "no juzgan la fila.",
        "",
        f"**Composiciones:** {len(proposals)} · **Filas:** {sum(len(v) for v in proposals.values())}",
        "",
    ]
    for composition_id in sorted(proposals):
        rows = proposals[composition_id]
        composition = configurations[composition_id]
        origin_id = next(iter(rows.values()))["proposal"]["proposed_from"]
        origin = configurations[origin_id]
        differences = []
        for axis in ("mechanism", "iv_access", "severity"):
            a, b = composition["axes"][axis], origin["axes"][axis]
            if a != b:
                differences.append(f"{AXIS_ES[axis]}: {VALUE_ES.get(a, a)} (origen: {VALUE_ES.get(b, b)})")
        c, o = composition["conditions"], origin["conditions"]
        lines += [
            f"## `{composition_id}`",
            "",
            f"- **Copiada de:** `{origin_id}`.",
            f"- **Llegada:** glucosa {c['arrival_glucose']} mg/dL, {c['arrival_mental_status']} "
            f"(origen: {o['arrival_glucose']} mg/dL, {o['arrival_mental_status']}).",
            f"- **Difiere del origen en:** {'; '.join(differences) if differences else 'nada en sus ejes'}.",
            "",
        ]
        for row_id in ROWS:
            row = rows[row_id]
            lines += [f"### {row_id} · {row['opportunity'].upper()}", ""]
            if row["opportunity"] == "yes":
                lines += [
                    f"- **Por qué:** {_cell(row.get('rationale', ''))}",
                    f"- **Componente observable:** {_cell(row.get('observable_component', ''))}",
                    f"- **Evidencia esperada:** {'; '.join(_cell(e) for e in row.get('expected_evidence') or ())}",
                    f"- **Fuera del encuentro:** {_cell(row.get('outside_the_encounter', ''))}",
                ]
            else:
                lines.append(f"- **Razón:** {_cell(row.get('reason') or row.get('rationale', ''))}")
            for flag in composition_flags(composition, origin, row_id, row):
                lines.append(f"- ⚠ **Alerta:** {flag}")
            lines += ["", REVIEW_LINE, ""]
    return "\n".join(lines).rstrip() + "\n"


def _spanish_rows(family):
    path = ROOT / "case_text" / "es" / f"{family}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def td04_sheet():
    import case_assessment_bank
    from clinical_cases import variant_by_id
    cases = sorted(case_id for case_id, spec in case_assessment_bank.CASES.items()
                   if (spec.get("objectives") or {}).get("C14", {}).get("opportunity") == "yes")
    lines = [
        "# TD-04 · El POCUS de llegada de los casos C14 YES",
        "",
        "Generado por `tools_review_sheets.py` desde el banco de casos. **No se edita a mano** y **no aprueba",
        "nada**: el código sigue marcando todo el POCUS como borrador (`POCUS_DRAFT_PENDING_FACULTY_REVIEW`), y",
        "cada caso queda para que un docente lo confirme o lo cambie con su firma. Sin imágenes ni videos: es el",
        "texto que el residente lee al pedir el POCUS al llegar. El motor puede cambiar algunas líneas después",
        "(por ejemplo, la pared reperfundida o la VCI tras el volumen); eso no está en esta hoja.",
        "",
        f"**Casos:** {len(cases)}",
        "",
    ]
    for case_id in cases:
        case = variant_by_id(case_id)
        family = case["engine"]["family"]
        result = (case.get("investigations", {}).get("pocus") or {}).get("result") or {}
        spanish = _spanish_rows(family).get(case_id, {})
        c14 = case_assessment_bank.CASES[case_id]["objectives"]["C14"]
        lines += [f"## `{case_id}`", "", "| Campo | Texto del caso | Borrador en español |", "|---|---|---|"]
        for field in [f for f in POCUS_ORDER if f in result] + sorted(set(result) - set(POCUS_ORDER)):
            es = (spanish.get(f"/investigations/pocus/result/{field}") or {}).get("es", "—")
            lines.append(f"| {field} | {_cell(result[field])} | {_cell(es)} |")
        lines += [
            "",
            f"- **C14, por qué:** {_cell(c14.get('rationale', ''))}",
            f"- **Evidencia esperada:** {'; '.join(_cell(e) for e in c14.get('expected_evidence') or ())}",
            "",
            REVIEW_LINE,
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def sheets():
    return {DC9_SHEET: dc9_sheet(), TD04_SHEET: td04_sheet()}


def main(argv=None):
    OUT.mkdir(parents=True, exist_ok=True)
    for path, text in sheets().items():
        path.write_text(text, encoding="utf-8")
        print(f"{path.relative_to(ROOT)}: {text.count(REVIEW_LINE)} rows to review")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
