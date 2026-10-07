# B-5 · Revisión docente del relato y de la rúbrica en español (diseño)

> **DISEÑO APROBADO por la docencia el 2026-10-07 (§8). Nada implementado.** Este documento define cómo revisar el
> relato en español de los 30 casos del piloto y los descriptores D1–D5 de la rúbrica. No activa el español, no crea
> `approvals.json`, no cambia el relato ni la rúbrica y no toca el corpus de la validación externa.
>
> 2026-10-07 · rama `clinical-encounter-v0.13` · decisión docente del mismo día: con X-1 decidida, preparar esta etapa
> sin empezar la implementación (Decision File, vigésima actualización). Base: decisiones docentes del 2026-10-07 sobre
> el relato y la rúbrica (paquete, 4.1 y 4.2; TD-81).

**En una mirada**

- **Relato:** 30 casos, 1.069 pasajes y unos 58.000 caracteres en inglés. Todos tienen español, ninguno está
  desactualizado y ninguno sobra.
- **Lectura real:** 587 textos distintos. 47 frases comunes cubren 527 pasajes y se leen una sola vez. Las demás, 542,
  se leen caso por caso, en 6 lotes de 77 a 111 pasajes.
- **Decisiones genuinas del relato:** 3 de terminología (T-1 a T-3), decididas el 2026-10-07. Además, 18 pasajes que
  fija el corpus congelado de la validación externa, aprobados tal cual (§8).
- **Lo demás no pide decisión:**
  - las comprobaciones automáticas no encontraron cifras distintas, textos sin traducir, nombres de fármacos fuera de
    V-9 ni una misma frase traducida de dos formas;
  - sus 29 alertas de negación o lateralidad se leyeron una por una, y ninguna es un error.
- **Rúbrica:** 5 dominios y 25 descriptores, alineados con el inglés vigente (5 de 5). Una decisión de terminología
  con el lenguaje de razonamiento aprobado en X-1 (R-1), decidida: «revisar» para «check».
- **Unidades de aprobación:** 30 casos y 5 dominios, cada uno con el hash exacto de lo que se leyó. Los dos
  `approvals.json` salen de esas decisiones de forma determinista, después de la revisión.

## 1. Qué se aprueba

El código ya define la unidad y el formato. No hace falta inventar otro.

- **Relato:**
  - se aprueba un caso entero, en la versión exacta que se leyó;
  - la versión es el hash de todos sus pasajes, en inglés y en español (`case_text.version`);
  - si después cambia una palabra en cualquiera de los dos idiomas, el caso vuelve a «pendiente» (`case_text.status`);
  - la aprobación vale sólo para su caso: una frase que otro caso dice igual sigue en inglés en él.
- **Rúbrica:**
  - se aprueba un dominio entero (su pregunta y sus cuatro niveles), con el hash de sus descriptores en los dos
    idiomas (`rubric_text.version`);
  - un dominio se ve en español sólo si está aprobado y cada descriptor sigue traduciendo lo que dice
    `rubric.DOMAINS` (`rubric_text.current`).
- **Lo que lleva cada archivo, cuando se cree después de la revisión:**
  - relato, `case_text/es/approvals.json`: una fila por caso aprobado, `{variant_id, version, decision}`;
  - rúbrica, `rubric_text/es/approvals.json`: una fila por dominio aprobado, `{domain_id, version, decision}`. Ojo: la
    clave es `domain_id`, no `domain` (`rubric_text.status`);
  - ninguno lleva nombres ni identificadores personales (TD-81). `status` sólo necesita el caso o el dominio, la
    versión y la decisión.

## 2. Inventario del relato (comprobado el 2026-10-07, sin cambiar código)

Lectura determinista de `case_text/es/*.json` contra el inglés vigente de cada caso (`case_text.current_english`),
para los 30 casos aceptados del manifiesto (`pilot_freeze.accepted_variants`). Sin IA y sin red.

| Qué | Cuántos |
|---|---|
| Casos | 30 |
| Pasajes | 1.069: presentación 30, fuente de la historia 30, historia 357, examen 131, informes de exámenes 511, apariencia 7, líneas derivadas 3 |
| Sin español · desactualizados (su inglés cambió) · sobrantes | 0 · 0 · 0 |
| Textos ingleses distintos | 587 |
| Frases comunes (iguales en 2 casos o más) | 47, que cubren 527 pasajes: 430 de informes, 40 de historia, 32 de examen, 23 de fuente y 2 de apariencia |
| Frases comunes traducidas de más de una forma | 0 |
| Cifras distintas entre inglés y español | 0 |
| Pasajes sin traducir o con restos en inglés | 0 |
| Nombres de fármacos fuera de V-9 | 0 (5 pasajes nombran un fármaco, y los 5 usan V-9) |
| Fuentes de la historia fuera de lo fijado (Paciente, Esposa, Hijo, Hija, Pareja) | 0 |
| Alertas de negación o lateralidad | 29. Leídas una por una: ninguna es un error. Son paráfrasis fieles («pain-free» → «sin dolor», «clear breath sounds» → «sin ruidos agregados») o falsos positivos («right now» → «en este momento») |

## 3. Decisiones genuinas del relato

### 3.1 Terminología (decidida el 2026-10-07: T-1 a T-3, como se recomendó; §8)

Un mismo término clínico, en la voz del clínico (examen e informes), está escrito de dos formas. Las palabras del
paciente («me silba el pecho») no se cuentan: ahí el registro coloquial es esperable.

**T-1 · «crackles»: «crépitos» o «crepitaciones»** (11 pasajes, todos `/examination/Respiratory`)
- «crepitaciones», 7: `acs_52m_de_winter`, `acs_66f_nonst`, `acs_70f_left_main`, `pneumonia_46f`, `pneumonia_83m`,
  `pulmonary_edema_58m` y `pulmonary_edema_75f`.
- «crépitos», 4: `bradycardia_hyperk_63m`, `opioid_67f`, `pulmonary_embolism_33f` y `pulmonary_embolism_61m`.
- La frase del motor A-3, aprobada en el paquete, dice «Persisten crépitos bilaterales» en la 58m y la 75f. Hoy, en
  esos dos encuentros, la llegada diría «crepitaciones» y el motor, «crépitos».
- Recomendación: **«crépitos»** en los 11, para coincidir con A-3 y con el resto de las frases del motor.

**T-2 · «guarding»: «defensa» o «resistencia muscular»** (8 pasajes, `/examination/Abdomen`)
- «defensa», 6: `anaphylaxis_29f`, `gi_bleed_57m`, `gi_bleed_72f`, `obstructive_pyelonephritis_58f`,
  `pulmonary_embolism_61m` y `renal_colic_34m`.
- «resistencia muscular», 2: `acs_54m_inferior` y `pneumonia_46f`.
- Recomendación: **«defensa»** en los 8.

**T-3 · «confused» en la voz del clínico: «confundido» o «confuso»** (1 caso, `hypoglycemia_28m`)
- La presentación dice «confundido»; el examen neurológico, «confuso».
- Recomendación: **«confundido»**, como la presentación y la historia del mismo caso.

Cada caso que cambia se revisa en su lote ya con el término aprobado, y su aprobación lleva la versión de ese
contenido. `case_text/es` cambia al implementar, y su versión tiene que coincidir entonces con la aprobada.

### 3.2 Pasajes que fija el corpus de la validación externa (18)

El corpus congelado genera sus hojas en español desde este mismo relato (`validation_corpus.case_sheet`), y una prueba
exige que las plantillas comprometidas sean byte a byte lo que genera hoy
(`test_validation_corpus.py::test_the_committed_blank_templates_are_what_the_generator_writes`).

- **Qué pasajes:** en sus 6 casos (`asthma_24f`, `pneumonia_46f`, `gi_bleed_57m`, `anaphylaxis_29f`,
  `renal_colic_34m` y `trauma_limb_hemorrhage_27m`), la presentación, `/history/chief_complaint/0` y
  `/history/onset/0`: 18 pasajes.
- **Qué pasa si se corrige uno:** cambia lo que genera el corpus, que no se toca mientras la validación esté en espera.
- **Decidido el 2026-10-07 (§8):** se aprueban tal cual para este candidato y no se cambian en esta revisión.
  Una mejora de estilo espera a que la validación externa se cierre formalmente. Un error clínicamente relevante,
  si apareciera, se escala; no se conserva en silencio.
- **Otro texto fijo, en una prueba:** la prueba del corpus también fija «Esposa» como fuente de la historia de
  `anaphylaxis_63m_betablocked` (`test_validation_corpus.py:62`). No es una de las 6 hojas, pero cambiarla obligaría a
  tocar esa prueba.

T-1 a T-3 no tocan ninguno de estos pasajes.

## 4. Lotes de revisión (orden docente: 0, RUB y R1 a R6)

| Lote | Qué | Casos | Pasajes | A leer | Marcados por el corpus |
|---|---|---|---|---|---|
| 0 | Frases comunes y terminología (T-1 a T-3) | — | 527 | 47 frases y 3 decisiones | 0 |
| RUB | Rúbrica D1–D5, por dominio | — | 25 descriptores | 25 y 1 decisión (R-1) | — |
| R1 | Síndrome coronario agudo | 6 | 210 | 93 | 0 |
| R2 | Respiratorio: asma, neumonía y edema pulmonar | 6 | 202 | 102 | 6 |
| R3 | TEP y bradicardias | 6 | 220 | 111 | 0 |
| R4 | Hipoglicemia y opioides | 5 | 165 | 79 | 0 |
| R5 | Anafilaxia y hemorragia digestiva | 4 | 146 | 80 | 6 |
| R6 | Urología y trauma | 3 | 126 | 77 | 6 |

Los casos van agrupados por familia, para leerlos con su contexto clínico. «A leer» son los pasajes propios de cada
caso, sin las frases comunes que el lote 0 ya cubrió.

**Cada documento de lote:**
- **Encabezado:**
  - qué significa aprobar: el caso entero, en la versión impresa, y sólo ese caso;
  - qué significa pedir un cambio: decir qué cambia; la corrección hace una versión nueva, que se vuelve a revisar
    sola.
- **Por caso:**
  - su identificador y el hash de versión que se revisa;
  - sus pasajes propios, por sección (presentación, fuente, historia, examen, apariencia, informes y líneas derivadas),
    cada uno con su ruta (por ejemplo, `/examination/Respiratory`) y su inglés y español;
  - los pasajes con cifras, unidades, lateralidad o resultados, marcados para leerlos con atención (142 de los 542);
  - los pasajes que fija el corpus, marcados;
  - la casilla: ☐ APPROVE (versión …) · ☐ REVISE (nota).
- **El lote 0:** cada frase común, con su español y los casos que la usan. Leerla una vez evita leerla 527 veces. No
  aprueba ningún caso, porque la aprobación sigue siendo por caso.

Los documentos se generan de forma determinista desde `case_text/es/*.json` y el inglés vigente, con el hash de cada
caso. El generador queda fuera del repositorio mientras no se autorice la implementación, para no cambiar el
candidato. El hash impreso ata cada aprobación a lo que se leyó.

## 5. Rúbrica (lote RUB)

- **Estructura:**
  - D1–D5, cada uno con «qué evalúa» y los niveles 0 a 3;
  - el inglés del borrador coincide con `rubric.DOMAINS` en los 5 dominios (`rubric_text.current`);
  - nada se agrega ni se quita.
- **Títulos:** los 5 títulos en español ya están activos en el código, sin la compuerta de aprobación
  (`rubric.DOMAINS[…]["title_es"]`). Se leen con su dominio, para ver que son coherentes; no son unidades de
  aprobación.
- **Unidades:** 5 dominios, con su hash.

**Terminología frente al lenguaje de razonamiento aprobado en X-1** (G-03, XR-02; L-03 y X1-C16):

| Rúbrica (ES) | X-1 aprobado | Lectura |
|---|---|---|
| D1: «si se decidió qué debía hacerse primero» | «qué problema estás abordando primero» | Concuerda |
| D2: «una explicación que guíe las decisiones» | «qué crees que está pasando» | Concuerda: la misma idea, en el registro de la evaluación |
| D3: «especificadas lo suficiente para poder ejecutarse»; «Indica un manejo apropiado» | «Indica …» (aclaraciones); «Indicaciones» | Concuerda |
| D4: «reevaluación», «reevalúa» | «reevaluación» (X1-C16); «Reevalúo … en … minutos» (L-03) | Concuerda |
| **D4: «qué vigilar»; «se comprobaron la ejecución y la respuesta»; «Comprueba…»; «No comprueba…»** | **«qué vas a revisar»; «cuándo lo vas a revisar»** | **Difiere (R-1)** |

**R-1 · «check»: «comprobar» (rúbrica, D4) o «revisar» (compuerta, aprobado)**
- **De dónde viene:** la compuerta pide «qué vas a revisar» («what you will check»). La rúbrica D4 juzga lo mismo,
  pero dice «comprobar» para «checked» y «checks», y «vigilar» para «watch», como su inglés.
- **Opciones:**
  - (a) dejar la rúbrica como está, siguiendo su propio inglés;
  - (b) usar «revisar» donde la rúbrica traduce «check» (la pregunta de D4 y sus niveles 0 y 2), y conservar
    «vigilar» para «watch».
- **Recomendada: (b).** El residente lee «revisar» en la compuerta y en la rúbrica para el mismo acto, y el inglés no
  cambia. **Decidida (b) el 2026-10-07** (§8).

## 6. Después de la revisión (no autorizado todavía)

1. **Correcciones:** las que se pidan (T-1 a T-3, R-1 y las notas de cada caso) se aplican en
   `case_text/es/*.json` o `rubric_text/es/descriptors.json`, cada una con su nueva versión, que se revisa de nuevo.
   No hay ninguna en los 18 pasajes que fija el corpus mientras la validación esté en espera.
2. **`approvals.json`:**
   - se generan con un script determinista, desde las decisiones registradas y el hash de cada versión aprobada,
     nunca a mano;
   - un caso o un dominio sin aprobar no entra;
   - el archivo se crea en la implementación, no antes.
3. **Pruebas:**
   - con la base vacía, `case_text.status` y `rubric_text.status` dan «approved» sólo a lo que dice cada archivo, y
     sólo en la versión aprobada;
   - un cambio posterior de una palabra devuelve el caso a «pendiente»;
   - el centinela del español (X-1, §10) corre con esas aprobaciones.
4. **Candidato:** el cambio es de repositorio. Hace un SHA nuevo, y el contrato 16.4 (suite, 56 regresiones, B-1)
   vuelve a correr.

## 7. Decisiones que necesitaba esta etapa (tomadas el 2026-10-07: §8)

- **Para empezar:** aprobar este diseño: la unidad de aprobación, el lote 0 y los lotes R1 a R6 y RUB, y el trato de
  los 18 pasajes que fija el corpus.
- **Rúbrica, TD-81 (b):**
  - el código ya lee `rubric_text/es/approvals.json` con `{domain_id, version, decision}`, igual que el relato;
  - falta confirmar que la rúbrica sigue ese mismo camino (a), y probarlo con la base vacía.
- **En cada lote:**
  - T-1 a T-3 y R-1;
  - APPROVE o REVISE por caso y por dominio.

## 8. Decisiones docentes (2026-10-07)

**El diseño, aprobado.** Sin implementar y sin `approvals.json`.

- **Relato:**
  - 30 casos; las frases comunes se revisan una vez donde es seguro, con trazabilidad exacta a cada pasaje;
  - la unidad de aprobación final es el **caso entero**, y cada aprobación ata `variant_id`, `version` y
    `decision = approved`;
  - la versión es el hash ya definido del contenido bilingüe exacto que se revisó (`case_text.version`);
  - sin nombres ni identificadores personales;
  - `case_text/es/approvals.json` se genera sólo cuando los 30 casos hayan terminado su revisión docente; no antes.
- **Terminología:** T-1 «crépitos», como la terminología ya aprobada de R-4; T-2 «defensa»; T-3 «confundido». Se
  aplican de forma coherente en la revisión del relato.
- **Los 18 pasajes que fija el corpus de la validación externa:**
  - se **aprueban tal cual** para este candidato del piloto, porque no tienen errores de traducción ni de contenido y
    cambiarlos ahora alteraría el corpus congelado;
  - no se cambia su redacción en esta revisión;
  - una mejora de estilo espera a que la validación externa se cierre formalmente;
  - un error clínicamente relevante, si apareciera, se escala igual; no se conserva en silencio.
- **Rúbrica D1–D5:**
  - mismo principio que el relato, respaldado en el repositorio y determinista;
  - una aprobación por dominio (D1 a D5), que ata `domain_id`, `version` y `decision = approved`, sin nombres ni
    identificadores personales;
  - no se crean todavía las aprobaciones finales;
  - antes de congelar el candidato, se identifica y se prueba el camino exacto de activación que ya usa la app.
- **R-1:**
  - «revisar» para «check», y «vigilar» reservado para «watch»;
  - la rúbrica en español usa el mismo vocabulario de razonamiento ya aprobado en X-1 donde los constructos son los
    mismos;
  - no cambian el sentido, los niveles, el puntaje ni la estructura D1–D5.
- **Orden de revisión:** lote 0 (las 47 frases comunes; T-1 a T-3 ya decididas), RUB (D1–D5, por dominio), R1, R2,
  R3, R4, R5 y R6, sin entregar todos los pasajes de una vez.
- **Lote 0, entregado para revisión:** `docs/revision/B5_RELATO_LOTE_0.md`.
- **Lote 0, decidido (2026-10-07):**
  - APPROVE en los 11 grupos: 47 de 47 frases comunes aprobadas, y sus 527 apariciones siguen trazables;
  - se mantienen «susceptibilidad» (L0-21) y «Campos pulmonares limpios; sin consolidación ni edema.» (L0-26);
  - T-1 a T-3 siguen como se aprobaron, y los 18 pasajes del corpus no se tocan.
- **Lote RUB, entregado para revisión:** `docs/revision/B5_RUBRICA_RUB.md`: 5 decisiones, una por dominio, con R-1 aplicada en D4.
- **Lote RUB, decidido (2026-10-07): 5 de 5.**
  - D1, D2 y D3, tal cual;
  - D4, con R-1 (versión `041597d9…`);
  - D5, opción (b), versión `52958f1c…`: «control posterior» para «follow-up» en el nivel 3, porque «Seguimiento»
    nombra D4;
  - sin cambios en los niveles, el puntaje, la estructura ni el inglés; sin aprobaciones ni cambios en
    `rubric_text/es`.
- **R1 dividido en R1A y R1B (docente, 2026-10-07), en el orden canónico del banco.** R1A, entregado para revisión: `docs/revision/B5_RELATO_R1A.md`.
- **R1A, decidido (2026-10-07):** APPROVE WHOLE CASE en `acs_54m_inferior` (`e1afcda5…`, con T-2), `acs_66f_nonst`
  (`d64dc726…`, con T-1) y `acs_61m_posterior` (`a6311c11…`). Van 3 de 30 casos. **Regla de versión:** la aprobación ata la versión objetivo presentada en la revisión, no la que está hoy en el repositorio. Al implementar, el español del repositorio tiene que dar exactamente ese hash antes de generar la entrada de aprobación; si da otro, se detiene y vuelve a revisión docente.
- **R1B, entregado para revisión:** `docs/revision/B5_RELATO_R1B.md`.
- **R1B, decidido (2026-10-07):** APPROVE WHOLE CASE en `acs_52m_de_winter` (`daf76611…`, con T-1),
  `acs_48m_wellens` (`13a56987…`, la del repositorio) y `acs_70f_left_main` (`c94b56ee…`, con T-1 y «crépitos
  basales dispersos»). El bloque de SCA queda aprobado entero (6 de 6); van 6 de 30 casos. Rige la misma regla
  de versión.
- **R2 dividido en R2A y R2B (docente, 2026-10-07), en el orden canónico del banco** (`clinical_cases.FAMILIES`:
  neumonía, edema pulmonar y asma). R2A (`pneumonia_46f`, `pneumonia_83m` y `pulmonary_edema_58m`), entregado
  para revisión: `docs/revision/B5_RELATO_R2A.md`. R2B: `pulmonary_edema_75f`, `asthma_24f` y `asthma_49m`.
- **R2A, decidido (2026-10-07):** APPROVE WHOLE CASE en `pneumonia_46f` (`d16cb333…`, con T-1 y T-2; sus 3 pasajes
  fijos del corpus, sin cambios), `pneumonia_83m` (`45a84e87…`, con T-1) y `pulmonary_edema_58m` (`dffcae29…`, con
  T-1 y «crépitos bilaterales difusos»). Van 9 de 30 casos. Rige la misma regla de versión.
- **R2B, entregado para revisión:** `docs/revision/B5_RELATO_R2B.md`. Trae una observación de sentido en `asthma_24f` (P-1, «opresivo» →
  «aplastante»), con las dos versiones objetivo, y la intersección de `asthma_49m` con A-6a a A-8a, que no pide
  decisión nueva.
