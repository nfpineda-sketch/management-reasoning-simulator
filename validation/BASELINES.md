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

Los **DEVELOPMENT HARDENED BASELINES V1** del ciclo 6 (`72a4a53`) **y V2** del
ciclo 7 (`9d2cd9e`) son referencias de desarrollo, no de validación. Están en
sus propias secciones, más abajo, y no en el registro que leen las
herramientas.

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

## DEVELOPMENT HARDENED BASELINE V1 (ciclo 6)

Instrucción docente del 2026-09-28, ciclo 6 (§29 y §42).

**Es una referencia de desarrollo, no una versión validada.**

- **Qué no hace:**
  - No reemplaza al SPANISH PILOT BASELINE.
  - No es un baseline de validación: no está en `validation/baselines.json`,
    cuyas entradas tienen idioma.
  - No se mide ningún documento del piloto contra él antes que contra su
    baseline.
- **Para qué sirve:** comparar después PILOT BASELINE con HARDENED ENGINE sin
  contaminar la medición original.

| Campo | Valor |
|---|---|
| **COMMIT SHA** | `72a4a5307fa5ae401044ca7f47780f9a221645b3` |
| **DATE** | 2026-09-28 |
| **TEST COUNT** | **5197 pasan, 77 omitidas, 2 xfail, 0 fallas** (suite completa en 4 shards sobre este commit) y **56 de 56 regresiones** |
| **KNOWN DEFECTS VERSION** | 2 (`validation/pilot_v1/manifests/known_defects.json`, sin cambios en el ciclo 6) |
| **DF-22 STATUS** | **Completo para las nueve clases** (C01–C09, C-2026-09-28-04), en EN y ES, con 192 pruebas. Tres conjuntos ciegos y una revisión adversarial del diff; las regresiones que ésta halló en las propias correcciones están corregidas (C-2026-09-28-09), y cada lectura que difiere del ciclo 5 se revisó. Con el código final, ninguna de las 118 negativas ciegas ejecuta nada de más en el motor. Quedan pérdidas sin aviso, sobre todo de hemoderivados (TD-26), y vocabulario que se retiene con una pregunta (TD-14) |
| **59O-03 STATUS** | **Completo** (C-2026-09-28-05): casos A–F de punta a punta, EN/ES |
| **L-F01 STATUS** | **Completo** (C-2026-09-28-06): A → B → reabrir da A; lo legacy sin caso queda UNAVAILABLE |
| **L-F04 STATUS** | **Completo** (C-2026-09-28-07): orden por la fecha del encuentro, confirmación como metadato. Probado en SQLite; **PostgreSQL NOT TESTED** (TD-24) |

**Cómo usarlo:** `git checkout 72a4a5307fa5`. Una corrida sobre este commit la
nombra por el commit; la herramienta no la nombra como baseline.

**Cómo llegó a ser este commit.**

- **La primera suite completa del ciclo, sobre `39bac97`, quedó verde** (5154
  pasan).
- **Después, una revisión adversarial del diff halló regresiones de las propias
  correcciones.** Se corrigieron en `3df039e` (C-2026-09-28-09).
- **La suite sobre `3df039e` encontró una falla.** Una prueba que ejecuta
  funciones de la página sin sus constantes chocó con una lectura adelantada.
  `72a4a53` la corrige sin cambiar la conducta.
- **La suite sobre `72a4a53` es la de arriba.**

**Frente al SPANISH PILOT BASELINE**, este commit trae:

- DF-22 y sus correcciones;
- 59O-03 y la seguridad de la aclaración;
- L-F01 y L-F04;
- las dos correcciones de DF-23.

Los defectos conocidos se etiquetan contra la misma lista (versión 2).

## DEVELOPMENT HARDENED BASELINE V2 (ciclo 7)

Instrucción docente del 2026-09-28, ciclo 7 (§71 y §120).

**Es una referencia de desarrollo, no una versión validada.**

- **Qué no hace:**
  - No reemplaza al SPANISH PILOT BASELINE ni al V1.
  - No es un baseline de validación: no está en `validation/baselines.json`.
  - No es el baseline del piloto inglés, que el docente elige antes de leer
    respuestas.
- **Para qué sirve:** comparar SPANISH PILOT BASELINE, V1 y V2 sobre el mismo
  subconjunto de desarrollo cuando lleguen datos externos (§116). La
  herramienta del piloto registra el commit de cada corrida. Basta correrla en
  cada commit: no hace falta tooling nuevo.

| Campo | Valor |
|---|---|
| **COMMIT SHA** | `9d2cd9e0d208b2878c5810e1a264a8b8d85be2e0` |
| **DATE** | 2026-09-28 |
| **TEST COUNT** | **5510 pasan, 77 omitidas, 1 xfail, 0 fallas** (suite completa en 4 shards sobre este commit) y **56 de 56 regresiones** |
| **KNOWN DEFECTS VERSION** | 2 (`validation/pilot_v1/manifests/known_defects.json`, sin cambios en el ciclo 7) |
| **POSTGRESQL STATUS** | **Verificado** en PostgreSQL 16 local y descartable, sin datos reales, sobre el código de persistencia de este commit: 168 pruebas pasan (115 bases creadas en PostgreSQL). Las 3 que leen el archivo SQLite no aplican; su equivalente (la migración conserva las filas) se comprobó a mano. El clúster se borró. Staging no se tocó (§9) |
| **C14 STATUS** | 31/31 casos revisados: **14 YES, 17 NO, 0 NOT REVIEWED**. `acs_54m_inferior` NO (C-2026-09-28-11). Las 9 composiciones de hipoglicemia heredan el NO de su origen (C-2026-09-28-16) |
| **C4 STATUS** | **NO** en todo el entorno de observación: 31 casos, generados y PS001. Es prospectivo (C-2026-09-28-10) |
| **TD-21 STATUS** | **Resuelto con el principio D** (C-2026-09-28-12). Tiene un residuo documentado que pide una decisión clínica (TD-33) |
| **TD-26 STATUS** | **Completo por clase**, con el estándar A–J (C-2026-09-28-13 y 14). En los conjuntos medidos, 0 pérdidas reales y 0 ejecuciones falsas. Residuos LOW en TD-32 y clases generales en TD-29 y TD-30 |

**Frente al V1** (`72a4a53`), este commit trae:

- TD-21 y TD-26;
- C7-06 y TD-22;
- C4 y C14 completos;
- DF-24;
- la separación ES/EN;
- DF-23, fila 3.

**El lector está congelado en este commit (§120).** Lo que se halle después se
registra en `docs/REGISTRO_DEUDA_TECNICA.md` y no se corrige hasta un ciclo
aprobado.

**Cómo usarlo:** `git checkout 9d2cd9e0d208`. Una corrida sobre este commit la
nombra por el commit; la herramienta no la nombra como baseline.

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
