"""Resumen técnico de UNA sesión de revisión docente (SÓLO LECTURA; no escribe en el almacén ni en el repositorio).

Qué hace el software, y sólo eso (FD-FR-08):
  * vincula cada respuesta con su paquete, su caso, su escenario y su artefacto almacenado;
  * comprueba la consistencia técnica: el paquete se verifica, el artefacto se verifica y se REPITE, la trayectoria coincide (o no) con el guion de referencia certificado;
  * comprueba la completitud del protocolo: qué escenarios del conjunto tienen paquete y respuesta, si se reveló el comparador y si quedó registrada la primera pasada ciega;
  * TABULA las respuestas de la persona docente tal cual, sin interpretarlas.

Qué NO hace: no puntúa, no promedia, no clasifica como aceptable o no, no decide si una trayectoria es plausible. Eso lo juzga la persona docente.

Uso:
    python3 faculty_review_kit/tools/session_summary.py --store /ruta/absoluta/al/almacen --reviewer R1 [--out resumen.md]

Código de salida: 0 si todo lo técnico es consistente; 2 si hay una inconsistencia técnica (se lista); 1 si no se pudo leer el almacén.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import runtime_authority_store as ras            # noqa: E402
import runtime_faculty_bundle as bundles         # noqa: E402
import runtime_faculty_review as fr              # noqa: E402

#: El conjunto de la primera revisión (docs del kit, 05_escenarios.md). Núcleo = se espera; opcional = sólo si hizo falta.
CORE = ("FR-B", "FR-A", "FR-E", "FR-G", "FR-F")
OPTIONAL = ("FR-D",)
SERIES = ROOT / "docs" / "revision" / "PHASE3_PRESSURE_AUTHORITY_SERIES.json"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _reference(scenario_id: str):
    """(minutos comprometidos, {minuto: (pas, pad)}) de la serie certificada para este escenario guionado, o None."""
    scenario = fr.scenario(scenario_id)
    if scenario is None:
        return None
    row = next((item for item in _json(SERIES)["runs"] if item["case"] == scenario["case_id"] and item["scenario"] == scenario["series"]), None)
    if row is None:
        return None
    seen = {}
    for minute, on, _off in row["pressure_steps_on_off"]:
        seen.setdefault(int(minute), tuple(on))
    return [int(item) for item in row["committed_minutes"]], seen


def _vs_script(bundle: dict):
    """('COINCIDE' | 'DIFIERE' | 'SIN_REFERENCIA', detalle). Difiere no es un error: la persona revisora pudo explorar otro curso."""
    scenario_id = dict(bundle.get("encounter") or {}).get("scenario_id")
    reference = _reference(scenario_id) if scenario_id else None
    if reference is None:
        return "SIN_REFERENCIA", "el paquete no nombra un escenario guionado"
    minutes, pressures = reference
    timeline = list(dict(bundle["authority_view"]).get("authoritative_pressure_timeline") or [])
    got = [int(item["minute"]) for item in timeline]
    if got != minutes:
        return "DIFIERE", f"minutos comprometidos {got} frente al guion {minutes}"
    for item in timeline:
        expected = pressures.get(int(item["minute"]))
        if expected is None or (round(float(item["sbp"])), round(float(item["dbp"]))) != tuple(int(v) for v in expected):
            return "DIFIERE", f"presión del minuto {item['minute']}: {round(float(item['sbp']))}/{round(float(item['dbp']))} frente al guion {expected}"
    return "COINCIDE", f"minutos {minutes} y presiones iguales al guion certificado"


def _read_dir(directory: Path) -> list:
    out = []
    for path in sorted(directory.glob("*.json")):
        try:
            out.append((path, _json(path)))
        except Exception as error:                      # un archivo ilegible es un hallazgo técnico, no se ignora
            out.append((path, {"__unreadable__": f"{type(error).__name__}"}))
    return out


def build(store: Path, reviewer: str) -> tuple:
    env = {ras.STORE_FLAG: str(store)}
    root = fr.review_root(env)
    if root is None or not root.exists():
        raise SystemExit(f"No hay carpeta de revisión en {store} (¿es la ruta del almacén correcta?).")
    technical, lines = [], []
    stored_bundles = _read_dir(root / "bundles")
    stored_feedback = _read_dir(root / "feedback")
    by_id = {}
    for path, body in stored_bundles:
        if "__unreadable__" in body:
            technical.append(f"paquete ilegible: {path.name} ({body['__unreadable__']})")
            continue
        by_id[body.get("bundle_id")] = (path, body)

    per_scenario: dict = {}
    for bundle_id, (path, body) in by_id.items():
        problems = bundles.bundle_problems(body)
        evidence = bundles.evidence_problems(body)
        artifact_id = dict(body.get("evidence") or {}).get("artifact_id")
        verified = ras.verify(artifact_id, environ=env) if artifact_id else {"found": False, "verified": False}
        replay = ras.replay(artifact_id, environ=env) if artifact_id else {"found": False, "reproduces": False}
        script, detail = _vs_script(body)
        scenario_id = dict(body.get("encounter") or {}).get("scenario_id") or "(sin escenario)"
        row = {"bundle_id": bundle_id, "case": dict(body.get("encounter") or {}).get("case_id"), "artifact_id": artifact_id, "bundle_ok": not problems, "evidence_ok": not evidence,
               "artifact_found": bool(verified.get("found")), "artifact_verified": bool(verified.get("verified")), "replay_reproduces": bool(replay.get("reproduces")), "script": script, "script_detail": detail,
               "halted": bool(dict(body.get("authority_view") or {}).get("halted")), "file": path.name}
        for flag, text in ((not problems, "el paquete no verifica: " + "; ".join(problems[:2])), (not evidence, "la evidencia del paquete falla: " + "; ".join(evidence[:2])),
                           (row["artifact_found"], "el artefacto del paquete no está almacenado"), (row["artifact_verified"], "el artefacto almacenado no verifica"),
                           (row["replay_reproduces"], "el artefacto almacenado no se reproduce")):
            if not flag:
                technical.append(f"{scenario_id} · paquete {bundle_id}: {text}")
        per_scenario.setdefault(scenario_id, {"bundles": [], "feedback": []})["bundles"].append(row)

    for path, body in stored_feedback:
        if "__unreadable__" in body:
            technical.append(f"retroalimentación ilegible: {path.name} ({body['__unreadable__']})")
            continue
        linked = by_id.get(body.get("bundle_id"))
        if linked is None:
            technical.append(f"retroalimentación {body.get('feedback_id')}: su paquete {body.get('bundle_id')} no está en el almacén")
            continue
        encounter = dict(linked[1].get("encounter") or {})
        if body.get("case_id") != encounter.get("case_id") or (body.get("scenario_id") or None) != (encounter.get("scenario_id") or None):
            technical.append(f"retroalimentación {body.get('feedback_id')}: caso o escenario distinto del de su paquete")
        blind = {key: value for key, value in dict(body.get("answers") or {}).items() if key in ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7")}
        snapshot = body.get("blinded_answers_at_reveal")
        if body.get("comparator_revealed") and snapshot != blind:
            technical.append(f"retroalimentación {body.get('feedback_id')}: la primera pasada registrada no coincide con las respuestas ciegas finales")
        per_scenario.setdefault(encounter.get("scenario_id") or "(sin escenario)", {"bundles": [], "feedback": []})["feedback"].append(
            {"feedback_id": body.get("feedback_id"), "bundle_id": body.get("bundle_id"), "revealed": bool(body.get("comparator_revealed")), "first_pass_kept": bool(snapshot) if body.get("comparator_revealed") else None,
             "role": body.get("reviewer_role"), "answers": dict(body.get("answers") or {}), "comments": body.get("comments") or "", "file": path.name,
             "saved_at": datetime.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="minutes")})

    now = datetime.datetime.now().isoformat(timespec="minutes")
    lines += [f"# Resumen técnico de la sesión de revisión · revisor {reviewer}", "",
              f"Generado {now} · almacén `{store}` · **sólo lectura**. Este resumen **no puntúa ni interpreta** las respuestas de la persona docente: las tabula tal cual (FD-FR-08).", ""]
    lines += ["## 1 · Completitud del protocolo (sólo presencia, no calidad)", "", "| Escenario | Tipo | Paquete(s) | Respuesta(s) | Comparador revelado | Primera pasada registrada |", "|---|---|---|---|---|---|"]
    for scenario_id in CORE + OPTIONAL:
        entry = per_scenario.get(scenario_id, {"bundles": [], "feedback": []})
        kind = "núcleo" if scenario_id in CORE else "opcional"
        revealed = ", ".join("sí" if item["revealed"] else "no" for item in entry["feedback"]) or "—"
        kept = ", ".join(("sí" if item["first_pass_kept"] else "NO") if item["first_pass_kept"] is not None else "n/a (no reveló)" for item in entry["feedback"]) or "—"
        lines.append(f"| {scenario_id} | {kind} | {len(entry['bundles'])} | {len(entry['feedback'])} | {revealed} | {kept} |")
        if scenario_id in CORE and not entry["bundles"]:
            technical.append(f"{scenario_id} (núcleo): no hay paquete")
        elif scenario_id in CORE and not entry["feedback"]:
            technical.append(f"{scenario_id} (núcleo): hay paquete pero no hay respuesta guardada")
    extra = sorted(set(per_scenario) - set(CORE) - set(OPTIONAL))
    if extra:
        lines += ["", "Escenarios fuera del conjunto (presentes en el almacén): " + ", ".join(extra)]
    lines += ["", "## 2 · Vínculos y consistencia técnica por paquete", "",
              "| Escenario | Caso | Paquete | Artefacto almacenado | Paquete y evidencia | Artefacto verifica | Se reproduce | Frente al guion certificado | Parada |", "|---|---|---|---|---|---|---|---|---|"]
    for scenario_id in sorted(per_scenario):
        for row in per_scenario[scenario_id]["bundles"]:
            lines.append(f"| {scenario_id} | {row['case']} | `{row['bundle_id']}` | `{row['artifact_id']}` | {'ok' if row['bundle_ok'] and row['evidence_ok'] else 'FALLA'} | "
                         f"{'sí' if row['artifact_verified'] else 'NO'} | {'sí' if row['replay_reproduces'] else 'NO'} | {row['script']} — {row['script_detail']} | {'sí' if row['halted'] else 'no'} |")
    lines += ["", "«DIFIERE» frente al guion no es un error: la persona revisora pudo explorar otro curso o teclear algo distinto. Sirve para saber si lo que se juzgó es lo que se esperaba juzgar.", ""]
    lines += ["## 3 · Respuestas de la persona docente (tal cual, sin interpretar)", ""]
    for scenario_id in sorted(per_scenario):
        for item in per_scenario[scenario_id]["feedback"]:
            lines += [f"### {scenario_id} · respuesta `{item['feedback_id']}` (paquete `{item['bundle_id']}`; guardada {item['saved_at']}; rol {item['role']})", "",
                      f"Comparador revelado: **{'sí' if item['revealed'] else 'no'}**. Primera pasada ciega registrada al revelar: **{('sí' if item['first_pass_kept'] else 'NO') if item['first_pass_kept'] is not None else 'n/a'}**.", "",
                      "| " + " | ".join(f"Q{i}" for i in range(1, 11)) + " |", "|" + "---|" * 10,
                      "| " + " | ".join(str(item["answers"].get(f"Q{i}", "—")) for i in range(1, 11)) + " |", ""]
            if item["comments"].strip():
                lines += ["Comentarios (literal):", ""] + ["> " + part for part in item["comments"].splitlines()] + [""]
    lines += ["## 4 · Hallazgos técnicos", ""]
    lines += [f"- {item}" for item in technical] if technical else ["- Ninguno: todos los vínculos y comprobaciones técnicas son consistentes."]
    lines += ["", "*Nada de lo anterior es un juicio clínico ni una validación. Los juicios son de la persona docente.*", ""]
    return "\n".join(lines), technical


def main() -> int:
    parser = argparse.ArgumentParser(description="Resumen técnico (sólo lectura) de una sesión de revisión docente.")
    parser.add_argument("--store", required=True, help="Ruta absoluta del almacén de esta sesión (MRS_PHASE3_AUTHORITY_STORE).")
    parser.add_argument("--reviewer", default="R?", help="Código del revisor, p. ej. R1 (no un nombre).")
    parser.add_argument("--out", default="", help="Archivo Markdown de salida (por omisión, la pantalla).")
    args = parser.parse_args()
    try:
        text, technical = build(Path(args.store).resolve(), args.reviewer)
    except SystemExit as error:
        print(error, file=sys.stderr)
        return 1
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Resumen escrito en {args.out}")
    else:
        print(text)
    return 2 if technical else 0


if __name__ == "__main__":
    sys.exit(main())
