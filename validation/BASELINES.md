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
| **ENGLISH EXTERNAL VALIDATION BASELINE** | en | `3d942eedf1d5922a8fed7df2e218bb3d7012c227` | `0.24.13-clinical-encounter` | versión 3 (`validation/known_defects_v3.json`) | sección «Decisión del baseline inglés (2026-09-29)» |

Los **DEVELOPMENT HARDENED BASELINES V1** del ciclo 6 (`72a4a53`) **y V2** del
ciclo 7 (`9d2cd9e`), y la **DEVELOPMENT PRE-VALIDATION BASELINE V3** del ciclo 9
(`3d942ee`), son referencias de desarrollo, no de validación. Están en
sus propias secciones, más abajo, y no en el registro que leen las
herramientas. V3 es el baseline recomendado para el corpus inglés: si el docente
lo elige, se agrega al registro como entrada nueva, antes de leer.

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

## DEVELOPMENT PRE-VALIDATION BASELINE V3 (ciclo 9)

Instrucción docente del 2026-09-29, ciclo 9 (§22, §74, §111–§116).

**Es el motor congelado antes de la medición externa, no una versión
validada.** No se llama «validated», «production» ni «final».

- **Qué no hace:**
  - No reemplaza al SPANISH PILOT BASELINE `939978a`, que sigue midiendo el
    corpus español (§66, §116).
  - No está en `validation/baselines.json`. Se agrega ahí, como entrada nueva,
    sólo si el docente lo elige como baseline inglés (abajo).
- **Para qué sirve:**
  - es el baseline recomendado para el corpus inglés;
  - permite comparar, sólo en DEVELOPMENT, `939978a`, V1, V2 y V3 (§23).
- **Congelado de verdad (§112):** después de V3, el lector no se toca en el
  ciclo 9. Lo nuevo MEDIUM o LOW es deuda técnica (`validation/KNOWN_DEFECTS_V3.md`).

| Campo | Valor |
|---|---|
| **COMMIT SHA** | `3d942eedf1d5922a8fed7df2e218bb3d7012c227` (el **FINAL V3 FREEZE COMMIT**) |
| **DATE** | 2026-09-29 |
| **TEST COUNT** | **6134 pasan, 77 omitidas, 1 xfail, 0 fallas** (suite completa en 4 shards sobre este commit) y **56 de 56 regresiones** |
| **KNOWN DEFECTS VERSION** | **3**, el estado propio de V3 (`validation/known_defects_v3.json`). La lista del piloto sigue en su versión 2, sin cambios |
| **TD-39 STATUS** | **Corregido por clase:** un alta para más tarde es un plan de destino, registrado, que no cierra el encuentro; el Trace la distingue del alta realizada (C-2026-09-29-01, -07) |
| **TD-34 STATUS** | **Corregido:** 1 h = 60 min en el lector, el motor, el reloj y el Trace (C-2026-09-29-02, -07) |
| **TD-36 STATUS** | **Corregido por clase:** lo recibido antes de la atención es historia, con qué, dosis, vía, quién y cuándo; nunca se da de nuevo (C-2026-09-29-03, -07) |
| **TD-33 STATUS** | **Corregido:** en trauma, sólo la sangre repone el déficit de la regla de sobrecarga (C-2026-09-29-04) |
| **DF-20 STATUS** | **CLOSED / NO CHANGE** (C-2026-09-29-05) |
| **TDFC STATUS** | **Completo en los 31 casos:** TD1 26 YES / 5 NO, F1 26/5, C1 19/12, C3 10/21. Ningún caso pendiente; tabla final y matriz regeneradas |
| **DF-23 4a** | **Aplicado** (C-2026-09-29-06). 4b, 6, 7 y 8 siguen en la cola |
| **EXTERNAL INGESTION** | Lista y ensayada sin respuestas reales (`docs/VALIDACION_EXTERNA_PREPARACION.md`) |
| **EXTERNAL DATA SEEN** | **Ninguno.** Nada se abrió, leyó ni procesó |

**Frente al V2** (`9d2cd9e`), este commit trae:

- el ciclo 8: TD-29 a TD-32, KD-05 y TDFC en 30 casos;
- el ciclo 9: TD-39, TD-34, TD-36, TD-33, DF-20 y las filas TDFC de
  `acs_54m_inferior`, la fila 4a de DF-23, las herramientas de ingesta externa
  y el estado de defectos conocidos de V3.

**Cómo llegó a ser este commit.** `72a7c01` fue un commit intermedio que pidió el entorno, anunciado como no congelado. La suite completa sobre el árbol de trabajo encontró dos fallas: el catálogo publicado de hipoglicemia no nombraba las correcciones nuevas del registro, y una prueba de la sala pasaba o fallaba según el caso sorteado (C-2026-09-29-09). `3d942ee` corrige ambas y cierra lo que halló la revisión pequeña de las correcciones (C-2026-09-29-08). La suite completa y las 56 regresiones de arriba corrieron sobre `3d942ee`, con el árbol limpio.

**Cómo usarlo:** `git checkout 3d942eedf1d5`. Una corrida sobre este commit la
nombra por el commit; la herramienta la nombra como baseline sólo si se agrega
a `validation/baselines.json`.

## Recomendación del baseline inglés (ciclo 9, §24, §65, §115)

**Recomendado: ENGLISH EXTERNAL VALIDATION BASELINE = V3 (`3d942ee`).** Es
una recomendación; la decisión es del docente y se toma antes de leer
cualquier respuesta inglesa.

| Punto | Respuesta |
|---|---|
| **Por qué V3** | 1) Se congeló sin exposición a ninguna respuesta externa. 2) El V2 contiene TD-39, TD-34 y TD-36 (verificado en el ciclo 9): medir el inglés en el V2 gastaría el corpus en redescubrir tres HIGH ya corregidos, y un alta falsa cierra el encuentro del documento, lo que puede alterar la lectura de las entradas siguientes del mismo documento. 3) V3 es el lector que se desarrollará después: un error externo hallado en V3 apunta a lo que hay que corregir (DATA-DRIVEN DEVELOPMENT). 4) Que el español y el inglés tengan baselines distintos es aceptable si ambos se congelaron antes de ver sus respuestas (§25) |
| **Por qué no el V2** | No aporta comparabilidad con el español: ni el V2 ni V3 son `939978a`. Su única ventaja, llevar más tiempo congelado, no compensa los tres HIGH que lleva |
| **Fecha de congelamiento** | 2026-09-29 |
| **¿Había empezado la recolección inglesa?** | Según el mensaje del docente del 2026-09-29, la recolección externa está en curso; el AI Advisor no sabe si la inglesa ya empezó. En el entorno no hubo ningún documento inglés devuelto |
| **¿Se vio algún contenido de respuesta?** | **No.** Ninguna respuesta, española ni inglesa, se abrió, leyó, buscó ni procesó; V3 se desarrolló sin exposición a ellas (§115) |
| **Consecuencias para la comparabilidad** | Las mediciones primarias usan motores distintos (español `939978a`, inglés V3): una diferencia entre idiomas mezcla idioma y motor, y el informe lo dice primero (§25, §105). Como análisis secundario y descriptivo, sólo en DEVELOPMENT, ambos corpus pueden leerse con los mismos commits (`939978a`, V1, V2, V3). Las formas de TD-39, TD-34 y TD-36 que V3 corrige pueden fallar en el español (se etiquetan, §67) y no en el inglés; en ambos quedan sus residuos conocidos (KD-16 a KD-24, `validation/KNOWN_DEFECTS_V3.md`) |
| **Cómo se adopta** | Una entrada nueva en `validation/baselines.json` (nombre, idioma `en`, commit de V3, `known_defects_version` 3), antes de leer. `ec1c77f` sigue registrado: un baseline nunca se reemplaza |

## Decisión del baseline inglés (2026-09-29)

Instrucción docente del 2026-09-29, posterior a V3 (ampliación no clínica, punto 1).
Se tomó **antes de recibir o leer cualquier respuesta inglesa**; en el entorno no
hay ninguna.

- **El corpus inglés se mide primero contra V3, `3d942eedf1d5922a8fed7df2e218bb3d7012c227`.**
  Se verificó que ese commit es «Cycle 9: V3 freeze commit (DEVELOPMENT
  PRE-VALIDATION BASELINE V3)» (`git log -1 3d942ee`).
- **Se agregó como entrada nueva** en `validation/baselines.json`: ENGLISH EXTERNAL
  VALIDATION BASELINE, idioma `en`, lista de defectos versión 3. `ec1c77f` sigue
  registrado y sigue nombrando una corrida hecha en su commit: un baseline nunca se
  reemplaza. Las secciones anteriores de esta página quedan como estaban.
- **El manifiesto del piloto inglés** (`validation/pilot_v1_en/manifests/pilot_manifest.json`)
  nombra ahora el baseline elegido, y conserva los candidatos y el estado previo
  (`status_until_2026_09_29`).

**Tres versiones distintas, que no se confunden:**

| Versión | Qué es | Dónde consta |
|---|---|---|
| **Baseline histórico** | V3 `3d942ee`: el motor contra el que se mide primero el corpus inglés. No cambia nunca | `validation/baselines.json`; esta página |
| **Versión posterior del motor** | Los commits de la rama después de V3 (roles, TEP, DC1, POCUS HDA, TD-31, hipoglicemia DC2–DC5 con `glucose_rescue` 2.0, acs_70f, foco de aprendizaje, TD-41, KD-31). Es desarrollo: **no es un baseline**, y una corrida en uno de esos commits se nombra por su commit | `git log 3d942ee..`; `corrections_registry.py`; `docs/POST_V3_CAMBIOS_CLINICOS.md` |
| **Versión de cada encuentro del piloto formativo** | La que cada encuentro congela al empezar: `assignment.code_version` y `evaluation_basis.code_version` (el commit desplegado, o `MRS_CODE_VERSION`), más las versiones de las que depende su evaluación (`evaluation_basis.versions`: cobertura, rúbrica, motor de familias, ejecución, oportunidades y, en hipoglicemia, `glucose_rescue`) | El registro de cada encuentro |

Un encuentro del piloto formativo **no** es una medición de validación externa: se
juega con el motor desplegado, que es una versión posterior del motor, y conserva
las reglas con que empezó.

## Confirmación formal al cerrar el ciclo posterior a V3 (2026-09-29)

Decisión docente registrada antes de recibir o leer cualquier respuesta externa:

| Medición | Baseline | Commit |
|---|---|---|
| **SPANISH EXTERNAL VALIDATION BASELINE** | registrado como SPANISH PILOT BASELINE | `939978a5147ab859a6dc3566ef4e1a98611a5093` |
| **ENGLISH EXTERNAL VALIDATION BASELINE** | V3, confirmado | `3d942eedf1d5922a8fed7df2e218bb3d7012c227` |

- **Ninguno cambia después de leer respuestas externas.**
- **V3 sigue congelado.** Todo commit posterior a `3d942ee` es **POST-V3 DEVELOPMENT**: no reescribe V3 ni el
  baseline histórico, y el HEAD de la rama nunca se presenta como el motor de la medición externa.

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
