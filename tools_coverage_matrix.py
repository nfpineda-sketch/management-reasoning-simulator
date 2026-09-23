"""Write docs/COBERTURA_CASOS.md from the declarations themselves.

Generated, never hand-maintained: a matrix typed out by hand drifts from the
code it describes, and this one exists to be trusted.
"""
from case_assessment import COVERAGE_VERSION, declared, events, matrix
from history_topics import HISTORY_TOPIC_LABELS
from rubric import DOMAIN_IDS, DOMAINS, VERSION


def build():
    rows = matrix()
    out = [
        "# Matriz de cobertura de los casos",
        "",
        f"> Generado por `tools_coverage_matrix.py` desde `case_assessment_bank.py`.",
        f"> Rúbrica {VERSION} · declaraciones versión {COVERAGE_VERSION}.",
        "",
        "La cobertura completa es **requisito para comparar puntajes totales**. No demuestra "
        "dificultad equivalente entre casos ni validación psicométrica.",
        "",
        "Cada oportunidad declarada se verifica contra el caso: un estudio nombrado tiene que "
        "estar en sus investigaciones, una acción tiene que ser una que el motor ejecute, y una "
        "región de examen tiene que ser una que el caso escriba. `case_assessment.verify` "
        "reporta cualquier discrepancia y hay una prueba por caso.",
        "",
        "## Resumen",
        "",
        "| Casos | Cobertura completa | Evaluación parcial | Discrepancias | Eventos críticos |",
        "|---|---|---|---|---|",
    ]
    complete = sum(1 for r in rows if r["complete"])
    problems = sum(len(r["problems"]) for r in rows)
    distinct = sorted({e for r in rows for e in r["critical_events"]})
    out += [f"| {len(rows)} | {complete} | {len(rows) - complete} | {problems} | "
            f"{len(distinct)} definiciones distintas |", ""]

    out += ["## Por caso", "",
            "| Caso | Familia | " + " | ".join(DOMAIN_IDS) + " | Eventos críticos definidos |",
            "|---|---|" + "---|" * len(DOMAIN_IDS) + "---|"]
    for row in rows:
        marks = " | ".join("✅" if d in row["domains"] else "—" for d in DOMAIN_IDS)
        names = ", ".join(f"`{e}`" for e in row["critical_events"]) or "—"
        out.append(f"| `{row['case_id']}` | {row['family']} | {marks} | {names} |")
    out += ["", "## Los cinco dominios", "",
            "| | Dominio | Qué pregunta |", "|---|---|---|"]
    for domain in DOMAIN_IDS:
        out.append(f"| **{domain}** | {DOMAINS[domain]['title_es']} | {DOMAINS[domain]['asks']} |")

    out += ["", "## Qué declara cada caso", ""]
    for row in rows:
        entry = declared(row["case_id"])
        out += [f"### `{row['case_id']}`", ""]
        for domain in DOMAIN_IDS:
            item = entry["domains"].get(domain)
            if item is None:
                out.append(f"- **{domain} — no evaluable.** "
                           f"{entry.get('not_assessable', {}).get(domain, '')}")
                continue
            start, end = item["window_min"]
            out += [f"- **{domain}** · ventana {start}–{end} min. {item['opportunity']}",
                    f"  - Esperado: {'; '.join(item['expected'])}.",
                    f"  - Alternativas aceptables: {'; '.join(item['alternatives'])}." ]
        out += ["", f"**Información accesible:** {'; '.join(entry['information'])}.", "",
                f"**Criterio de cierre:** {entry['closure']}", "",
                "**Límites reales del motor:**"]
        out += [f"- {limit}" for limit in entry["engine_limits"]]
        out += ["", "**Eventos críticos:**", ""]
        for event in events(row["case_id"]):
            start, end = event["window_min"]
            kind = "Acción peligrosa" if event["kind"] == "dangerous_action" else "Omisión crítica"
            out += [f"- `{event['event_id']}` — **{kind}.** {event['action']}",
                    f"  - Se activa cuando: {event['trigger']}",
                    f"  - Información que debía estar en el registro: {'; '.join(event['information_required'])}.",
                    f"  - Ventana y oportunidad: {start}–{end} min.",]
            if event["information_on_asking"]:
                out.append("  - Disponible preguntando, se haya preguntado o no: "
                           + "; ".join(f"**{HISTORY_TOPIC_LABELS.get(topic, topic)}** ({tells})"
                                       for topic, tells in event["information_on_asking"]) + ".")
            out += [
                    f"  - Alternativas aceptables: {'; '.join(event['alternatives'])}.",
                    f"  - Evidencia necesaria: {event['evidence_required']}",
                    f"  - Exclusiones: {'; '.join(event['exclusions'])}.",
                    f"  - Dominios sobre los que pesa: {', '.join(event['domains'])}."]
        out.append("")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    from pathlib import Path
    target = Path(__file__).with_name("docs") / "COBERTURA_CASOS.md"
    target.write_text(build(), encoding="utf-8")
    print(f"escrito: {target} ({len(build().splitlines())} líneas)")
