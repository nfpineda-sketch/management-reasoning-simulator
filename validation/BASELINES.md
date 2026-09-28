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
| **ENGLISH VALIDATION BASELINE** | en | `ec1c77f0339a6e3087337d2a621b2e630d3549a5` | `0.24.13-clinical-encounter` | versión 2 | esta página, sección siguiente |

## ENGLISH VALIDATION BASELINE: `ec1c77f`

**Qué trae, frente al baseline español:**

- **KD-01 corregido por clase:** la vía escrita antes del fármaco.
- **C14 declarado en 30 casos.**
- **La herramienta del piloto** con baselines, versión de defectos y
  etiquetas validadas.

**Suite completa en este commit** (4 shards):

| Medida | Resultado |
|---|---|
| Pruebas | **4956 pasan, 77 omitidas, 2 xfail, 0 fallas** |
| Regresiones | 56 de 56 |
| Corpus de ensayo (20 ES + 20 EN, semilla 3000) | idéntico al ciclo 4 decisión por decisión: 96/96 órdenes por idioma |

**Cómo llegó a ser este commit.** La primera corrida completa, sobre
`3745b0f`, encontró una sola falla: el catálogo publicado de hipoglicemia no
listaba las correcciones nuevas. `ec1c77f` lo regenera, y su generador nombra
la corrección detrás de cada declaración nueva.

- Una segunda corrida se descartó: el disco temporal se llenó a mitad de
  camino.
- La tercera, limpia, es la de arriba.

**El código del motor es el mismo en `3745b0f` y en `ec1c77f`.** Sólo cambian
el generador de un documento y el documento.

**Cómo comprobar que se usa este baseline:** `git checkout ec1c77f0339a`.

**Commits posteriores del ciclo 5:**

- documentación y registro de baselines;
- la corrección nocturna 59Z (`3f0524c`), en `app.py`: un encuentro nuevo ya
  no hereda el cierre del anterior;
- el catálogo de hipoglicemia regenerado.

Ninguno toca el lector ni el motor: `git diff ec1c77f0339a -- family_parser.py
shared_order_language.py family_engine.py` sale vacío. Aun así, una medición
se corre en el commit del baseline, no en uno posterior.

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
