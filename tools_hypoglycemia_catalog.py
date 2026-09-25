"""Write docs/CATALOGO_HIPOGLICEMIA.md from the catalogue, the battery and the registry themselves.

Generated, never hand-maintained, like the coverage matrix: a table typed out
by hand drifts from the code it describes. Offline and free: it plays the
battery on the real engine with structured actions and calls no provider.
"""
from pathlib import Path

import case_catalog
import corrections_registry
import glucose_rescue
import hypoglycemia_battery as battery
import hypoglycemia_catalog as catalog
import hypoglycemia_preservation as preservation
from case_assessment import COVERAGE_VERSION

TARGET = Path(__file__).with_name("docs") / "CATALOGO_HIPOGLICEMIA.md"
_STATUS = {"passed": "✅", "failed": "❌", "not_observed": "—"}
_CLASS = {"technical_defect": "defecto técnico", "pending_clinical_decision": "decisión clínica pendiente",
          "differs_from_reference": "distinto de la referencia"}


def _axes(configuration):
    return " · ".join(catalog.AXES[axis]["values"][configuration["axes"][axis]]["es"]
                      for axis in ("mechanism", "iv_access", "severity"))


def _conditions(configuration):
    c = configuration["conditions"]
    names = [name for name in ("sulfonylurea_effect", "endogenous_insulin", "glycogen_depleted",
                               "thiamine_deficient", "iv_access_failed") if c[name]]
    return ", ".join(f"`{name}`" for name in names) or "—"


def _preservation():
    record = preservation.load_golden()["variants"]
    now = preservation.capture()
    rows = []
    for variant_id in preservation.VARIANTS:
        def differences(old, new, path=""):
            if isinstance(old, dict) and isinstance(new, dict):
                found = []
                for key in sorted(set(old) | set(new)):
                    found += differences(old.get(key, "<missing>"), new.get(key, "<missing>"), f"{path}/{key}")
                return found
            return [path] if old != new else []
        fields = differences(record[variant_id]["variant"], now[variant_id]["variant"])
        scripts = [name for name in preservation.SCRIPTS
                   if [s["fingerprint"] for s in record[variant_id]["scripts"][name]]
                   != [s["fingerprint"] for s in now[variant_id]["scripts"][name]]]
        same_declaration = record[variant_id]["declaration"] == now[variant_id]["declaration"]
        rows.append((variant_id, fields, scripts, same_declaration,
                     record[variant_id]["launch"] == now[variant_id]["launch"]))
    return rows


def build():
    report = battery.run()
    out = [
        "# Catálogo de hipoglicemia",
        "",
        "> Generado por `tools_hypoglycemia_catalog.py` desde `hypoglycemia_catalog.py`, "
        "`hypoglycemia_battery.py` y `corrections_registry.py`. No se edita a mano.",
        f"> Catálogo {catalog.VERSION} · batería {battery.BATTERY_VERSION} · mecanismo de glucosa "
        f"{glucose_rescue.VERSION} · declaraciones de evaluación {COVERAGE_VERSION}.",
        "",
        "Autorización docente del 2026-09-25, etapas 0–2. Las tres variantes del banco se expresan mediante el "
        "catálogo y el catálogo compone las otras nueve combinaciones de sus tres ejes. **Las nueve composiciones no "
        "se ofrecen a residentes**: sólo un docente o un administrador las abre, en el sandbox, para revisarlas.",
        "",
        "Tres estados que no se mezclan:",
        "",
        "- **Compatible**: cumple las relaciones del catálogo, pasa el contrato de los casos del banco, sus "
        "declaraciones de evaluación son alcanzables y se lanza en el motor real.",
        "- **Probado**: la batería lo jugó en el motor real con acciones estructuradas y ninguna comprobación "
        "técnica encontró un defecto técnico. Una comprobación que choca con una decisión clínica pendiente no se "
        "cuenta como defecto ni como aprobada: se muestra aparte, con su decisión. Describe una cobertura "
        "concreta —los guiones y comprobaciones de abajo— y no equivale a validado. No prueba el lenguaje libre.",
        "- **Revisado clínicamente**: sólo lo produce la acción registrada de un docente identificado, sobre una "
        "versión; se registra en la aplicación (panel del sandbox docente), no en este documento. Este documento no "
        "atribuye ninguna revisión.",
        "",
        "## Resumen",
        "",
        "| Combinaciones | Del banco | En revisión | Compatibles | Probadas | Defectos técnicos | Con decisión clínica pendiente |",
        "|---|---|---|---|---|---|---|",
    ]
    entries = report["configurations"]
    pending = [e for e in entries if e.get("summary", {}).get("pending_decisions")]
    out.append(f"| {len(entries)} | {sum(e['origin'] == 'bank' for e in entries)} | "
               f"{sum(e['origin'] != 'bank' for e in entries)} | "
               f"{sum(e['compatibility']['compatible'] for e in entries)} | {sum(e['tested'] for e in entries)} | "
               f"{sum(len(e['summary']['technical_defects']) for e in entries)} | {len(pending)} |")
    out += ["", "## Ejes", ""]
    for axis, spec in catalog.AXES.items():
        values = "; ".join(f"`{key}` {value['es']}" for key, value in spec["values"].items())
        out.append(f"- **{spec['es']}** (`{axis}`): {values}.")
    lower, upper = catalog.SEVERITY_BANDS["severe"]
    out.append(f"- Bandas de gravedad, derivadas de los umbrales del motor (`glucose_rescue`): severa "
               f"[{lower}, {upper}) mg/dL; moderada [{catalog.SEVERITY_BANDS['moderate'][0]}, {catalog.SEVERITY_BANDS['moderate'][1]}) mg/dL, con "
               f"{catalog.MODERATE_ARRIVAL_GLUCOSE} mg/dL en las composiciones. Son bandas del simulador, no una "
               "clasificación clínica.")
    out += ["", "## Condiciones que el motor ya ejecuta", "",
            "| Condición | Qué significa | Dónde vive | Decide el caso |", "|---|---|---|---|"]
    for name, spec in catalog.CONDITIONS.items():
        out.append(f"| `{name}` | {spec['es']} | {spec['implemented_by']} | "
                   f"{'sí' if spec['decision_relevant'] else 'no'} |")
    for kind, label in case_catalog.RELATION_KINDS.items():
        out += ["", f"## Compatibilidades · {label['es']}", "", "| | Regla | Por qué |", "|---|---|---|"]
        for relation in catalog.RELATIONS:
            if relation["kind"] == kind:
                out.append(f"| {relation['id']} | {relation['es']} | {relation['why']} |")
    pending = [item["id"] for item in catalog.SIMPLIFICATIONS if item["review"] == "pending"]
    out += ["", "## Parámetros del motor usados como referencia técnica", "",
            "La batería los usa como referencia, nunca como criterio para juzgar a un residente, estén revisados o "
            "no. La última columna dice lo que el repositorio registra de cada uno: una magnitud revisada es un "
            "parámetro docente del simulador, no un criterio de evaluación. Sin revisión registrada: "
            f"{', '.join(pending)}. Las preguntas están en `docs/HIPOGLICEMIA_DECISIONES_PENDIENTES.md`.", "",
            "| | Parámetro | Valor actual | Revisión |", "|---|---|---|---|"]
    for item in catalog.SIMPLIFICATIONS:
        out.append(f"| {item['id']} | `{item['parameter']}` | {item['es']} | "
                   f"{catalog.REVIEW_STATES[item['review']]}. {item['review_es']} |")
    out += ["", "## Las doce combinaciones", "",
            "| Configuración | Origen | Mecanismo · acceso · gravedad | Glucosa y conciencia al llegar | Condiciones | "
            "Compatible | Probado | Referencias | Pendiente |",
            "|---|---|---|---|---|---|---|---|---|"]
    for entry in entries:
        configuration = catalog.configuration(entry["configuration_id"])
        s = entry["summary"]
        held = sum(r["kind"] == "technical" and r["classification"] == "pending_clinical_decision"
                   for r in entry["checks"])
        out.append(
            f"| `{entry['configuration_id']}` | {'banco' if entry['origin'] == 'bank' else 'en revisión'} | "
            f"{_axes(configuration)} | {configuration['conditions']['arrival_glucose']} mg/dL, "
            f"{configuration['conditions']['arrival_mental_status']} | {_conditions(configuration)} | "
            f"{'sí' if entry['compatibility']['compatible'] else 'no'} | "
            f"{'sí' if entry['tested'] else 'no'} ({s['technical_passed']}/{s['technical_total']} técnicas"
            f"{f'; {held} en decisión pendiente' if held else ''}) | "
            f"{s['reference_within']}/{s['reference_total']} | {', '.join(s['pending_decisions']) or '—'} |")
    out += ["", "## Correspondencia de las tres variantes del banco", ""]
    for configuration in catalog.bank_configurations():
        assumptions = " ".join(item["es"] for item in configuration["assumptions"])
        out.append(f"- `{configuration['id']}` → {_axes(configuration)}. Condiciones: "
                   f"{_conditions(configuration)}. Supuestos de la configuración: {assumptions}")
    out += ["", "## Preservación técnica", "",
            "Comparación con el registro del 2026-09-25 (commit d184845), antes de que existiera el catálogo: el "
            "caso, su declaración de evaluación, su estado de lanzamiento y veinte guiones de acciones estructuradas "
            "en el motor real. Una coincidencia es regresión, no aceptación clínica.", "",
            "| Variante | Caso | Declaración | Lanzamiento | Guiones distintos |", "|---|---|---|---|---|"]
    for variant_id, fields, scripts, same_declaration, same_launch in _preservation():
        out.append(f"| `{variant_id}` | {'idéntico' if not fields else ', '.join(f'`{f}`' for f in fields)} | "
                   f"{'idéntica' if same_declaration else 'nueva versión (cobertura 1.1)'} | "
                   f"{'idéntico' if same_launch else 'distinto'} | "
                   f"{', '.join(f'`{s}`' for s in scripts) or f'ninguno de {len(preservation.SCRIPTS)}'} |")
    out += ["", "Cada diferencia está declarada en el registro de correcciones; la prueba "
            "`test_hypoglycemia_preservation` acepta esas y ninguna otra.", "",
            "## Correcciones intencionales", "",
            "| | Corrección | Alcance | Tipo | Relevancia clínica | Versiones |", "|---|---|---|---|---|---|"]
    for entry in corrections_registry.CORRECTIONS:
        scope = entry["scope"]
        where = {"general": "general", "family": f"familia {scope.get('family')}",
                 "variant": "variante " + ", ".join(scope.get("variants", ()))}[scope["level"]]
        versions = "; ".join(f"{key} {change['from'] or '—'} → {change['to']}"
                             for key, change in entry["affects"]["versions"].items()) or "—"
        out.append(f"| {entry['id']} | {entry['title']} | {where} | {entry['kind']} | "
                   f"{entry['clinical_relevance']} | {versions} |")
    out += ["", "## La batería, configuración por configuración", "",
            "Técnicas (T): el motor hace lo que el modelo dice; una falla es un defecto técnico, salvo que su "
            "arreglo exija una decisión clínica. Referencias (R): tiempos y magnitudes de los parámetros actuales, "
            "pendientes de revisión; se conservan para notar un cambio, no son criterios."]
    for entry in entries:
        out += ["", f"### `{entry['configuration_id']}`", "",
                f"{_axes(catalog.configuration(entry['configuration_id']))}. Guiones: "
                + "; ".join(f"{s['es']} ({battery.TRAJECTORY_KINDS[s['kind']].lower()})" for s in entry["scripts"])
                + ".", "", "| | Comprobación | Resultado | Observado | Parámetros |", "|---|---|---|---|---|"]
        for result in entry["checks"]:
            note = f" ({_CLASS[result['classification']]}" + (f" {result['decision']}" if result["decision"] else "") \
                + ")" if result["classification"] else ""
            out.append(f"| {result['id']} | {result['es']} | {_STATUS[result['status']]}{note} | "
                       f"{result['observed']} | {', '.join(result['parameters']) or '—'} |")
        out += ["", "Sin observar: " + " ".join(entry["unobserved"])]
    out += ["", "## Revisarlas en desarrollo", "",
            "1. Entrar con una cuenta docente o de administrador a la aplicación de desarrollo.",
            "2. En el sandbox docente elegir el desafío R1-06 o R1-07 (los que incluyen hipoglicemia).",
            "3. En «Case to open (faculty review)» elegir la configuración. Se abre sin generación y sin imagen "
            "pagadas, como encuentro de sandbox, fuera del progreso de los residentes.",
            "4. En «Clinical review of the hypoglycemia catalogue (faculty)» registrar la decisión y una nota. La "
            "revisión queda atada a la versión de la configuración; un cambio clínicamente relevante posterior la "
            "marca como desactualizada.", ""]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    TARGET.write_text(build(), encoding="utf-8")
    print(f"escrito: {TARGET} ({len(TARGET.read_text(encoding='utf-8').splitlines())} líneas)")
