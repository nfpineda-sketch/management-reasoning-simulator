# Baselines de validación

Autorización docente del 2026-09-28, ciclo 5 (§13, §44, §51).

Un baseline es el commit del motor contra el que se mide un resultado de
validación.

- **Nunca se reemplaza retroactivamente**; se agrega uno nuevo.
- **El registro que leen las herramientas** es `validation/baselines.json`.

## Registro

| Baseline | Idioma | Commit | Motor | Lista de defectos | Detalle |
|---|---|---|---|---|---|
| **SPANISH PILOT BASELINE** | es | `939978a5147ab859a6dc3566ef4e1a98611a5093` | `0.24.13-clinical-encounter` | versión 1 | `validation/pilot_v1/PILOT_BASELINE.md` |
| **ENGLISH VALIDATION BASELINE** | en | *se registra cuando la suite completa pase en el commit con KD-01* | `0.24.13-clinical-encounter` | versión 2 | esta página |

## Qué registra cada corrida

Una corrida de validación deja en su reporte (`report.json` y `report.md`,
sección *Provenance*):

| Campo | De dónde sale |
|---|---|
| **CORPUS VERSION** | `corpus_version` y la versión del subconjunto |
| **LANGUAGE** | `languages`: los idiomas de los documentos leídos |
| **ENGINE** | `engine`: el commit, si había cambios sin guardar y la versión del simulador |
| **ENGINE BASELINE** | `engine_baseline`: el baseline que es ese commit, según este registro, o vacío |
| **KNOWN DEFECTS VERSION** | `known_defects_version`: la lista contra la que se etiquetan sus errores |

**Tres reglas:**

- **Con cambios sin guardar, la lectura no es un baseline.**
- **El baseline se nombra al hacer el reporte**, por el commit de la corrida.
  Así, una corrida hecha en un commit que se registra después también queda
  nombrada. Un baseline sólo se agrega; nunca cambia de commit.
- **Una etiqueta `known_defect` tiene que existir en la lista.** Una etiqueta
  mal escrita contaría una falla nueva como conocida.

## Cómo se usan

- **La primera medición en español usa el SPANISH PILOT BASELINE.** Se leen los
  documentos con el código de `939978a`: `git checkout 939978a5147a`, o un
  worktree.
  - El reporte puede hacerse con la herramienta actual, que nombra el baseline
    por el commit.
  - En ese baseline, KD-01 está presente: un error de vía antes del fármaco se
    etiqueta KD-01.
- **La fase en inglés usa el ENGLISH VALIDATION BASELINE.** Ahí KD-01 está
  corregido: un error de esa clase sería una falla nueva.
- **Las respuestas se miden primero contra su baseline**, antes de usarlas para
  cambiar el motor. Nunca se cambia un baseline para que una respuesta pase.
- **Un defecto dice en qué baselines está presente** (`present_in` en
  `validation/pilot_v1/manifests/known_defects.json`). Así una sola lista sirve
  para los dos.
