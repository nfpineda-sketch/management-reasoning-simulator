# Vía común de tono vascular y primer vasopresor (P3-387 a P3-401)

> **Nota 2026-11-18 (ratificación):** la revisión humana multiescenario se reportó completada (`ACCEPT` 1, `ACCEPT_WITH_LIMITATION` 3, `RECALIBRATE` 0, `REJECT` 1; **reportada, no verificada contra el almacén persistido**) y `CENTER_REFERENCE` quedó ratificado como `COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1`, sólo para desarrollo; ver `docs/PHASE3_COMMON_TONE_RATIFICATION.md`. Las frases «la revisión humana no se hizo», «ningún testigo ratificado/elegido» y «FR-F es un candidato sin veredicto» de este documento eran ciertas al escribirlo y **no se editan**.

Fecha: 2026-11-17. Rama: `phase-3-runtime-integration`. Alcance: **Enmienda 3 del núcleo común (apagada por omisión) y su
mapeo de desarrollo en la sombra**; sin autoridad nueva, sin cambio para el residente, sin calibración clínica.
Decisiones: FD-TONE-01 a FD-TONE-12, FD-RECORD-01 a FD-RECORD-04 y FD-P3-257 a FD-P3-264 (`docs/COLA_DECISIONES_AI_ADVISOR.md`).
Deuda: `TD-154` y `TD-155`. Registro de la enmienda: `docs/revision/PHASE2_AMENDMENT_3.md`.

Distingo en todo el documento: **implementado** · **probado** (con la cifra) · **pendiente**.

**En una frase.** El núcleo común tenía tono vascular (el canal `T`) pero ninguna entrada por la que un fármaco que
constriñe pudiera llegar a él. Este ciclo agrega **un** estado general —el *soporte vasoconstrictor*— que multiplica el tono
que el estado pide, y **un** escritor de ese estado —una infusión de norepinefrina a tasa fija—. La presión que resulta es la
que el tono, el flujo, la precarga y la bomba del núcleo hacen de él: no hay ninguna ecuación «norepinefrina → +X mmHg».

## 0 · Decisiones del encargo (2026-11-17)
| Decisión | Contenido |
|---|---|
| **FD-TONE-01** | El objetivo es el **tono vascular común `T`**: un estado fisiológico general, no un sinónimo de norepinefrina. |
| **FD-TONE-02** | La norepinefrina es el **primer** escritor. La arquitectura admite otros (vasopresores, vasodilatadores, estados endógenos) sin ecuaciones de presión por fármaco; no se implementan otros fármacos. |
| **FD-TONE-03** | Auditar la interacción de `T` con volumen/precarga, bomba/flujo, presión, perfusión y entrega/deuda de oxígeno: representado frente a faltante. |
| **FD-TONE-04** | `T` no rescata un flujo ausente; la semántica dura de «sin pulso» no cambia. |
| **FD-TONE-05** | `T` no aumenta en silencio el volumen intravascular. |
| **FD-TONE-06** | No se calibra clínicamente la dosis-respuesta: dirección, clase temporal, magnitud acotada, dependencia del estado previo y orden de las intervenciones. Sin objetivo en mmHg. |
| **FD-TONE-07** | La instantánea de presión de GI y la concesión V2 quedan **congeladas**; no se recalibra GI para que la norepinefrina «se vea mejor». |
| **FD-TONE-08** | La re-revisión humana de FR-A y FR-D es deseable y **no bloqueante**; sus trayectorias no se alteran. |
| **FD-TONE-09** | La concesión V1 y el punto anterior siguen reproducibles, pero **no seleccionables para sesiones nuevas**. |
| **FD-TONE-10** | *(decisión del 2026-11-17, por consulta)* Implementar la **Enmienda 3** en esta rama, apagada por omisión, y emitir la concesión **V3** como **re-ligado puro de linaje**: misma instantánea, mismos casos, sólo presión, la norepinefrina sigue **no concedida** a la autoridad viva. |
| **FD-TONE-11** | *(ídem)* La V2 queda intacta, registrada y reproducible, pero **histórica**: la reemplaza la V3. FR-F es un **candidato versionado en la sombra**. |
| **FD-TONE-12** | *(ídem)* Si el punto de control final no es A, se publica igualmente lo certificado (commits separados, *push* normal, sólo con suite y regresiones en verde sobre una huella congelada). |

## 1 · P3-387 · Activación de V1 y V2 (auditoría y formalización)
**Hallazgo (auditoría de sólo lectura).** Tras la promoción del 2026-11-16 el punto anterior (`gi_pressure_committed`,
concesión V1) seguía siendo una **segunda configuración aceptada** de la compuerta viva: un entorno que lo nombraba abría una
sesión autoritativa **nueva**. La promoción lo había dejado anotado como decisión pendiente.

**Implementado.**
- `runtime_pressure_grant.py`: registro `SUPERSEDED` (V1 → V2, V2 → V3), `LIVE_GRANT_ID = …_V3`, y `permits(...)` niega una
  concesión reemplazada por configuración ordinaria (`SUPERSEDED_FOR_NEW_SESSIONS`). Las concesiones V1 y V2 **no se
  editaron**: sus huellas fijadas son las mismas (`3c29c2b9…c136`, `8a91145d…3642f`).
- **Reconstrucción histórica explícita.** Una concesión reemplazada sólo abre algo si el proceso **declara** que la
  reconstruye (`MRS_PHASE3_HISTORICAL_RECONSTRUCTION=<id exacto de la concesión>`), la declaración **no** viene de un Secret, y
  el núcleo certificado vivo **reconstruye exactamente** el miembro del linaje que esa concesión nombra
  (`runtime_shadow_evidence.rebuilt_predecessors`, que lee la reversión declarada de la etapa viva y nunca la palabra de quien
  llama). La sesión resultante lo dice en su registro de elegibilidad: `is_a_new_development_session: false`.
- **Verificación y repetición de artefactos** de V1 y V2: sin cambio. Un artefacto se resuelve por la concesión que nombra.
- *Endurecido tras la revisión (§13, H8):* una reconstrucción declarada de la concesión que liga una instantánea la decide
  **esa** concesión y ninguna otra, y sólo sobre el núcleo de la concesión viva; el linaje reconstruido ya no se acepta de
  quien llama a `permits` sin esa comprobación, de modo que la compuerta y el sitio no pueden discrepar.
- El entorno docente de revisión sólo corre la concesión viva (V3).

**Probado.** `test_phase3_grant_supersession.py` (12 pruebas): registro y huellas; V3 = alcance de V2 con sólo las
diferencias declaradas; una concesión reemplazada no autoriza por configuración ordinaria ni en la compuerta ni al abrir el
sitio; una reconstrucción exige declaración **y** linaje reconstruido; una declaración por Secret o con otro valor no declara
nada. Las suites anteriores que ejercitan el punto anterior lo hacen ahora como reconstrucción declarada (§12).

## 2 · P3-388 · Versionado de registros históricos
Contrato, clases del índice y pruebas: `docs/PHASE3_HISTORICAL_RECORD_VERSIONING.md`.

## 3 · P3-389 · Auditoría del tono existente → veredicto **B**
| Pregunta | Lo que hay en el núcleo |
|---|---|
| ¿Existe un estado de tono común? | **Sí**: el canal `T` (C2), multiplicador con llegada = 1, guarda abierta (0,1; 3,0). |
| ¿Quién lo escribe? | **Sólo** la respuesta de tono del núcleo (`_vascular_tone`): lleva `T` al objetivo que pide el estado del minuto anterior (retroalimentación retardada explícita). Ninguna fuente clínica puede escribir `T`. |
| ¿De qué depende el objetivo? | `objetivo = C(s) × B(b)`: la compensación ante el déficit agudo de oxígeno (`deficit_to_tone_gain`, 0 en el perfil por omisión, 0,5 en varias familias) y el factor distributivo de la carga vasodilatadora (`vasodilatory_burden_to_tone_gain`, **sin declarar** en todo perfil comprometido). |
| ¿Qué lee `T`? | La presión (`presión_rel = gasto_rel × T`) y la poscarga (`gasto_rel ∝ 1 / (1 + a·(T − 1))`, `a = 0,3`). La entrega, la deuda y el relleno capilar leen el **gasto**, no la presión. |
| ¿Hay entrada para un vasoconstrictor exógeno? | **No.** P2X-1 la dejó sin decidir a propósito: «un vasopresor actúa por un mecanismo propio, no como carga negativa». |
| ¿Y en el motor heredado? | Tiene la forma que este encargo prohíbe (`norepi_pressure_bonus = 21·n / (0,25 + n)` mmHg). Sigue siendo la autoridad en tiempo de ejecución y **no se tocó**. |

**Veredicto B — `PARTIAL_TONE_PHYSIOLOGY_EXISTS_BUT_NEEDS_SUCCESSOR`.** El estado, su único escritor y su acoplamiento con
presión y flujo existen y son generales; falta la entrada. No es A (nada que extender sin tocar el núcleo) ni C (no hay que
inventar el estado).

## 4 · P3-390 · Estado mínimo
`aux.vasoconstrictor_support` (`u`): un estado **general**, ≥ 0, adimensional, en unidades de su propio efecto semimáximo
(`u = 1` es la mitad del efecto mayor). `None` significa «no se registra» (el lector está sin declarar) y entonces no aparece
en ningún estado serializado. No es norepinefrina: cualquier escritor que constriña suma al mismo estado con el mismo registro
(`provenance.VasoconstrictionChange`); un vasodilatador conserva su propia entrada, la carga.

`CoreProfile.vasoconstrictor_support_to_tone_gain` (`k`): el mayor aumento fraccional del objetivo de tono. **Sin declarar por
omisión**; entonces nada de esto corre y toda trayectoria comprometida es idéntica bit a bit.

    objetivo de tono = C(s) × B(b) × K(u),        K(u) = 1 + k·u / (1 + u)

`K(0) = 1` exactamente (la llegada sigue siendo la escala), crece con `u` y nunca alcanza `1 + k`: **acotado por su forma**, sin
recorte. El dominio del tono rechaza, **antes de ejecutar**, una ganancia cuyo mayor objetivo alcanzable llegue a la guarda.

## 5 · P3-391 · Acoplamiento de `T` con presión y perfusión
No se agregó ninguna ecuación de presión: lo que sigue sale de la fisiología que el núcleo ya tenía.

| Invariante del encargo | Estado | Evidencia (CENTER_REFERENCE salvo indicación) |
|---|---|---|
| Con flujo, `T` sostiene la presión | **Se cumple** | FR-F: PAM 64 → 76 mmHg al primer control. |
| Sin flujo, `T` no crea circulación | **Se cumple** | Sin pulso (asistolia, AESP): PAS, PAM, gasto y entrega nulos a cualquier tono; precarga vacía: presión 0. |
| `T` no agrega volumen | **Se cumple** | `V`, hemoglobina, bomba y agua pulmonar idénticos minuto a minuto con y sin soporte, en las seis familias. |
| Tono excesivo no es mejor entrega | **Se cumple** (y de sobra) | El gasto y la entrega **nunca** suben con el tono; la deuda crece más rápido (FR-F, minuto 32: 1,68 sin soporte, 3,81 con él). |
| La depleción de volumen modifica la respuesta | **Se cumple en mmHg** | Misma orden, sangrado sin tratar: +13,2 mmHg al minuto 5, +10,5 al 60, +8,1 al 110. |
| La falla de bomba modifica la respuesta | **Se cumple en mmHg; falta en proporción** | Bomba a la mitad: +7,1 mmHg frente a +14,3. El **costo en gasto** es la misma fracción (0,917) con cualquier bomba y volumen: ver §14. |
| No hay una ganancia universal en mmHg | **Se cumple** | La misma orden da entre +11,5 y +28,9 mmHg según la familia. |

## 6 · P3-392 · Escritor de norepinefrina
**Auditoría de la orden (lo que entrega el motor).** `family_parser` produce
`{"type": "norepinephrine", "rate": 10.0, "units": "mcg/min", "operation": "start"}`; también conoce `mcg/kg/min`, y las
operaciones `adjust` (titulación) y `stop` (sin tasa). La orden no tiene duración: corre hasta que se detiene.

**Implementado (núcleo).** `clinical_core/vascular_support.Norepinephrine`: infusión continua a tasa fija desde un minuto de
inicio, con comienzo y cese de primer orden propios. Su aporte al soporte es una forma cerrada de la orden y del tiempo
**únicamente** (contrato del escritor: no lee presión, tono, gasto, entrega, volumen ni bomba; no puede cerrar un lazo ni
titular). No escribe `T`, `V`, hemoglobina ni bomba. Una orden dada en el minuto `s` actúa por primera vez en `(s, s + 1]`.

*Rejilla de los escritores (tras la revisión, §13, H1).* El aporte de cada escritor se guarda en múltiplos de
`SUPPORT_QUANTUM = 2⁻⁴⁰` (≈ 9,1 × 10⁻¹³ unidades de semiefecto) y un soporte estacionario de `SUPPORT_LIMIT = 2¹⁰` semiefectos
o más se rechaza al construir la orden. Así las diferencias minuto a minuto y su suma son **exactas**: el estado es, en cada
minuto, exactamente la suma de lo que sostienen sus escritores, y exactamente 0 cuando ya decayeron. Es una regla de
representación, no una magnitud clínica: no mueve ninguna presión mostrada.

**Implementado (Fase 3, sólo sombra).** `runtime_tone_support.py` mapea **una** forma de la orden: `start` a tasa fija en
`mcg/min`, y **sólo si es la primera orden de norepinefrina del encuentro** (tras la revisión, §13, H6). Todo lo demás es una
**brecha declarada** con su motivo: `adjust`, `stop`, dosis por peso, una tasa ausente o no positiva, una tasa que el escritor
del núcleo no representa, y **toda orden posterior a la primera** (titular, detener o reiniciar: la corrida dice que desde
ahí ya no refleja el vasopresor del encuentro). Si la primera orden no es mapeable, **ninguna posterior la reemplaza**: la
corrida llevaría una infusión que el encuentro inició en otro minuto y a otra dosis. El orden es el del motor (minuto y,
dentro del minuto, posición en el reflejo), y un identificador de orden cuenta una vez. No hay motor de titulación.

## 7 · P3-393 · Matriz de casos límite
La dirección se **predijo antes de correr** (`test_tone_pathway_analysis.PREDICTIONS`) y el registro guarda la predicción junto
a lo observado. Las diez filas coinciden; lo que la fisiología del núcleo **no** representa está en la última columna.

| Caso | Presión | Flujo | Acotado | Clase | No representado |
|---|---|---|---|---|---|
| Hemorrágico, volumen bajo (GI) | sube | baja | sí | sostén de presión a costa de flujo | retorno venoso por venoconstricción; sangrado dependiente de la presión |
| Cardiogénico, limitado por bomba (SCA) | sube | baja | sí | ídem | sensibilidad a la poscarga dependiente de la bomba; perfusión coronaria; inotropismo |
| Congestión pulmonar (edema) | sube | baja | sí | daño o ausencia de beneficio | agua pulmonar por poscarga; más mmHg a mayor presión de llegada |
| Obstructivo (embolia) | sube | baja | sí | sostén de presión a costa de flujo | perfusión coronaria del ventrículo derecho |
| Hemodinamia normal (asma, opioide) | sube | baja | sí | daño o ausencia de beneficio | — |
| Tono bajo de tipo distributivo | sube | **hacia la llegada** | sí | restaura hacia la llegada | **no hay caso autorado**: sonda sintética (P2W-1) |
| Sin pulso | ninguna | ninguno | sí | sin efecto | — |
| Precarga vacía, sin flujo | ninguna | ninguno | sí | sin efecto | — |
| Tono ya alto | sube | baja | sí | rendimientos decrecientes | isquemia por vasoconstricción; quien **llega** vasoconstreñido no está más cerca del techo |

Tono bajo distributivo (sonda del núcleo): la carga lleva `T` a 0,50 y la PAM de 90 a 52,9 mmHg con gasto 1,18; con soporte
`T` = 0,65, PAM 65,4 y gasto 1,12: presión y flujo vuelven **hacia** la llegada y el flujo queda por encima de ella. Es el
único caso en que el vasopresor es el fármaco correcto, y el núcleo lo muestra así.

Tono ya alto: a 5, 10, 20, 40 y 80 mcg/min, `T` = 1,20 · 1,30 · 1,40 · 1,48 · 1,53; a 10 230 mcg/min —la mayor tasa que el
escritor representa con este testigo— 1,5994, **por debajo** del techo `1 + k` = 1,60, que no se alcanza; una tasa mayor se
rechaza en la orden (no se corre a un soporte absurdo).
*Corrección del arnés:* la primera formulación de la comprobación («cada duplicación agrega menos tono») era falsa por debajo
de la tasa semimáxima —una curva Emax es simétrica en el logaritmo de la dosis— y se reemplazó por la correcta: **cada
mcg/min adicional agrega menos tono**. La predicción de la matriz (sube / baja / acotado) no cambió.

## 8 · P3-394 · Región de comportamiento de desarrollo
Sin calibración clínica. Cotas amplias; **todas** las confianzas están por debajo de 0,80, así que **no** se adopta una región
estrecha ni se elige un punto.

| Magnitud | Cotas | Confianza | Evidencia | Falsador |
|---|---|---|---|---|
| `tone_gain` (`k`) | 0,3 – 0,9 | 0,5 | Un vasopresor sube la presión de forma dosis-dependiente y saturable; no hay magnitud en el repositorio ni objetivo docente en mmHg. | Que la docencia encuentre la respuesta a soporte saturante implausible con flujo conservado. |
| `half_effect_rate_mcg_min` | 5 – 20 mcg/min | 0,5 | La orden autorada es una tasa fija (FR-F: 10 mcg/min). | Que 10 mcg/min casi no produzca efecto o produzca uno casi máximo. |
| `onset_tau_min` | 0,5 – 3,0 min | 0,7 | Actúa en uno o dos minutos; efecto estable en varios. | Que la presión del primer control llegue demasiado pronto o tarde. |
| `offset_tau_min` | 1,0 – 5,0 min | 0,6 | Vida media plasmática de pocos minutos. | Sostén de presión por decenas de minutos tras detener, o pérdida en uno. |

Testigos de prueba, **ninguno elegido**: `LOW` {0,3; 20; 3,0; 1,0}, `CENTER_REFERENCE` {0,6; 10; 1,5; 2,5}, `HIGH` {0,9; 5; 0,5; 5,0}.

**Hallazgo de las sondas multifamilia.** La primera región propuesta llegaba a `k = 1,0`. En tres familias (edema pulmonar,
asma, opioide) la compensación comprometida puede llegar a 1,5 veces el tono de llegada, de modo que con `k = 1,0` el mayor
objetivo alcanzable es exactamente la guarda de `T` (3,0) y **el dominio del tono rechazó el testigo antes de ejecutar**. La
cota superior se bajó a 0,9, que todo perfil comprometido admite. Es la guarda del núcleo haciendo su trabajo, no una
calibración; el mensaje del rechazo ahora nombra el tercer factor cuando está declarado.

## 9 · P3-395 · Decisión de sucesor → **C**
**`PHASE2 AMENDMENT 3 — COMMON VASCULAR TONE`.** Hace falta una memoria nueva, un campo nuevo del perfil, un registro de
cambio nuevo y un tipo de contribuyente nuevo en archivos comunes: es fisiología, no configuración (descarta A y B), y cabe
como inserción declarada y reversible sobre el núcleo vigente sin rediseñarlo (descarta D).

## 10 · P3-396 · Implementación
**Núcleo (`clinical_core/`, Enmienda 3, apagada por omisión).**
- `provenance.py`: `VasoconstrictionChange` y `MinuteRecord.vasoconstriction` (se serializa sólo si no está vacío).
- `state.py`: `AuxiliaryState.vasoconstrictor_support` (`None` = no se registra; ausente del estado serializado).
- `derived.py`: campo del perfil, su entrada en el registro de parámetros (`PROVISIONAL`, sin aprobar) y el factor `K` en
  `tone_target`.
- `integration.py`: el campo en `Contribution`, la suma del minuto (`_vasoconstriction_after`, que rechaza un cambio con el
  lector sin declarar, un estado que **ya trae** soporte con el lector sin declarar —se perdería en silencio—, un soporte
  bajo cero y cambios que no suman un valor finito), el invariante de conservación del minuto (el soporte se mueve
  **exactamente** por sus cambios registrados) y el factor `1 + k` en el dominio del tono, cuyos rechazos nombran el factor
  declarado.
- `vascular_support.py` (nuevo): el factor, la región, los testigos, la rejilla de los escritores y el escritor
  `Norepinephrine`.
- `amendment_3.py` (nuevo): la etapa formal. Reconstruye la Enmienda 2 (`a0af7d08…`, 144 fuentes), la Enmienda 1
  (`10b45ce2…`) y el cierre histórico (`22b90a6f…`, 141 fuentes) revirtiendo inserciones declaradas y probadas.
- Digesto del núcleo: ver §13 y `docs/revision/PHASE2_AMENDMENT_3.json` (146 fuentes).

**Capa de la Fase 3 (fuera de `clinical_core/`).**
- `runtime_tone_support.py` (nuevo, en `LAYER_SOURCES`): `with_tone_support(adaptador, testigo)` devuelve una **copia de
  desarrollo** del adaptador de cualquier familia que declara el lector y mapea la orden. El adaptador registrado no se
  modifica, la copia nunca se registra y **falla cerrada** si el núcleo vivo no es un miembro certificado que tenga el lector.
- `runtime_shadow_families.py`: el atributo `tone_support_witness` (siempre `None` en todo adaptador registrado) y la
  procedencia de una corrida de desarrollo, que nombra su propia instantánea de parámetros. La copia **se rechaza** sobre un
  adaptador testigo de la consciencia de la Enmienda 2 (§13, H2), y cada copia tiene su propia clase: el módulo no guarda
  estado mutable.
- `runtime_shadow.py`: la entrada de la Enmienda 3 en el linaje y `core_is_or_descends_from` (un parámetro que existe en un
  miembro existe en sus sucesores registrados).
- `runtime_pressure_grant.py`, `runtime_authority.py`, `runtime_authority_pair.py`, `runtime_shadow_evidence.py`,
  `runtime_pair_site.py`, `runtime_faculty_review.py`, `runtime_faculty_bundle.py`: la concesión V3, la supersesión y la
  reconstrucción histórica (§1), y el re-ligado del vínculo de la instantánea de consciencia al sucesor (el digesto de la
  Enmienda 2 se **recalcula** desde el árbol vivo; un campo de perfil del sucesor sin declarar no entra en la huella fijada, y
  declarado la cambia).

**Lo que no cambió.** `family_engine.py` sigue siendo la única autoridad (`COMMON_CORE_RUNTIME_AUTHORITY = False`).
`runtime_authority.SUPPORTED_ACTIONS` **no** incluye la norepinefrina: la autoridad viva sigue deteniéndose ante la orden.
Ningún adaptador registrado declara el lector. Nada de esto lo lee la página, la puntuación ni el primer piloto.

## 11 · P3-397 · FR-F en la sombra (candidato versionado)
Registro: `docs/revision/PHASE3_FRF_TONE_V1_CANDIDATE.json` (`FR-F_TONE_V1_CANDIDATE`, clase `VERSIONED`). **No lleva
veredicto ni predeclara uno.** Caso `gi_bleed_57m`, sobre la instantánea ratificada de presión de GI (la lee, no la cambia).
Guion: dos minutos de historia, la orden en el minuto 2 con el control implícito de cinco minutos de la página, y dos
controles que la corrida certificada nunca alcanzó (porque se detuvo en la orden).

| Minuto | Orden sin mapear | `LOW` | `CENTER_REFERENCE` | `HIGH` |
|---|---|---|---|---|
| 2 (orden) | 87/54 (65) | 87/54 (65) | 87/54 (65) | 87/54 (65) |
| 7 | 86/53 (64) | 91/56 (68) | 102/63 (76) | 117/72 (87) |
| 17 | 83/51 (62) | 89/54 (66) | 99/61 (74) | 113/69 (84) |
| 32 | 79/48 (58) | 84/52 (63) | 94/58 (70) | 107/66 (80) |

*PAS/PAD (PAM), mmHg enteros como los muestra la página.*

Lo que la migración debía mostrar, leído de cada corrida (hechos de la corrida, no un juicio clínico):
- **Orden aceptada:** disposición `BUILT`, sin brecha ni falla, efectiva desde el minuto 3.
- **El tono cambia:** `T` máximo 1,10 · 1,30 · 1,60 (techos 1,3 · 1,6 · 1,9).
- **La respuesta empieza de forma causal:** soporte desde el minuto 3, tono y presión desde el 4; hasta el minuto 3 la
  corrida es idéntica a la que no mapea la orden. Nunca hay un escalón en el minuto de la orden.
- **El control es posible:** lecturas con pulso en 7, 17 y 32.
- Además: sin volumen ni bomba creados; acotado por su forma; repetición exacta.
- **La presión comprada sigue cayendo** con el sangrado en los tres testigos (no se dio volumen), y la deuda de oxígeno crece
  más rápido que sin vasopresor.

**Preservado.** La corrida certificada de FR-F (la autoridad viva se detiene: `HALTED_BY_UNSUPPORTED_ACTION`) y la primera
revisión humana quedan byte a byte como estaban (índice de P3-388), y siguen siendo lo que la autoridad viva hace.

**Pendiente (decisión docente).** Cómo se presenta el candidato a una persona —qué testigo o testigos, a ciegas o no, con qué
preguntas—. **No** se construyó conjunto de revisión ni pantalla.

## 12 · P3-398 · Sondas multifamilia y adaptaciones declaradas
Registro: `docs/revision/PHASE3_COMMON_TONE_PROBES.json` (`COMMON_TONE_PROBES_V1`). La **misma** orden (10 mcg/min en el
minuto 5, leída al 30) por el mapeo comprometido de cada familia más el lector declarado. Sin ampliar autoridad.

| Familia (caso) | PAM sin → con (`CENTER_REFERENCE`) | Ganancia `LOW` / `CENTER` / `HIGH` (mmHg) | Presión × | Gasto × |
|---|---|---|---|---|
| GI (`gi_bleed_57m`) | 59,5 → 71,0 | 4,0 / 11,5 / 21,2 | 1,193 | 0,917 |
| SCA (`acs_70f_left_main`) | 75,8 → 92,3 | 5,8 / 16,5 / 30,6 | 1,217 | 0,905 |
| Edema pulmonar (`pulmonary_edema_58m`) | 150,0 → 178,9 | 10,2 / 28,9 / 53,4 | 1,193 | 0,917 |
| Embolia pulmonar (`pulmonary_embolism_61m`) | 62,7 → 76,3 | 4,8 / 13,5 / 25,1 | 1,216 | 0,905 |
| Asma (`asthma_49m`) | 104,7 → 124,8 | 7,1 / 20,2 / 37,3 | 1,193 | 0,917 |
| Opioide (`opioid_35m`) | 78,0 → 93,0 | 5,3 / 15,0 / 27,8 | 1,193 | 0,917 |

En las seis: la orden se construye por el mismo mapeo (que no nombra familia, caso ni presión), ninguna corrida falla, todas
se repiten exactamente, y volumen, bomba, hemoglobina y agua pulmonar no se mueven. En SCA y embolia el factor es algo mayor
(1,22) y el gasto cae algo más (0,905): su compensación está encendida y responde a la caída del flujo. **No** apareció
comportamiento no general.

**Adaptaciones de pruebas existentes (declaradas, ninguna regenera un registro histórico).**
- *Vistas del cierre:* 47 archivos de pruebas de paquetes cerrados leen el árbol de cierre a través de la etapa que conoce la
  cadena completa (`a3.chain`, `a3.tree`, `a3.closure_view`), como ya hicieron con la Enmienda 2.
- *«El núcleo no se movió»:* donde una prueba afirmaba que el núcleo vivo era la Enmienda 2, ahora afirma lo equivalente —que
  el digesto de la Enmienda 2 **se recalcula** desde el árbol vivo por la reversión declarada— (`test_phase3_bleed_rate_scale`,
  `test_phase3_first_review_analysis`, `test_phase3_gi_development_snapshot`, `test_phase3_gi_recovery_review`,
  `test_phase3_joint_feasibility`, `test_phase3_joint_region`, `test_phase3_gi_authority_readiness`,
  `test_phase3_amendment_2_integration`, `test_phase3_dormant_pair`, `test_shadow_observability`, `test_shadow_resolution`,
  `test_runtime_shadow_evidence`).
- *«La norepinefrina no está implementada»:* dos pruebas lo afirmaban de todo `clinical_core/`; ahora afirman que existe
  **sólo** en los dos archivos que posee la Enmienda 3.
- *Punto anterior:* las suites que construyen un entorno explícito con `gi_pressure_committed` lo declaran como reconstrucción
  histórica (`test_runtime_authority`, `test_phase3_pressure_grant`, `test_phase3_pressure_attacks`,
  `test_phase3_pressure_review`, `test_phase3_stop_lifecycle`); para las que usan el entorno del proceso lo hace una
  *fixture* de sesión en `conftest.py`, y las pruebas marcadas `ordinary_configuration` la retiran.
- *Capa:* `runtime_tone_support` se agregó a las dos listas literales de la capa (`test_shadow_core_isolation`,
  `test_runtime_shadow_plumbing`).
- *Concesión vigente:* V2 → V3 donde se nombraba la concesión de una sesión nueva (`test_phase3_pressure_promotion`,
  `test_phase3_pair_site`, `test_phase3_pressure_review::test_r10`, que además muestra la instantánea de V1 rechazada por
  supersesión), y las tablas de constantes de sólo lectura de la capa incluyen `_BODY_V3` (`test_phase3_stop_concurrency`).
- *Punto de control de la promoción:* `test_phase3_pressure_promotion_checkpoint` reconstruía el registro con «el último
  miembro del linaje» como predecesor; ahora nombra el miembro sobre el que se decidió la promoción (`PHASE2_AMENDMENT_2`,
  que el linaje sigue registrando y reconstruyendo). El registro histórico **no** se regeneró: sigue sellado byte a byte.
- *Identidad de la capa:* `test_runtime_shadow_evidence::test_u15` fija por nombre el conjunto de fuentes de la capa, que
  ahora incluye `runtime_tone_support.py`.
- *«El núcleo vivo es la Enmienda 2» / «la sesión nueva corre la V2» (hallados por la corrida de descubrimiento, §13.2):*
  `test_management_generalization`, `test_opioid_live_shadow` (2), `test_terminal_amendment_design` (5),
  `test_phase3_gi_preauthority_review` (3), `test_phase3_faculty_review_page` (2) y
  `test_phase3_pressure_promotion_stop` (1) afirman ahora lo equivalente: el núcleo vivo es el **último miembro
  certificado** del linaje y desciende de la Enmienda 2; los registros que nombran la Enmienda 2 se leen contra ese
  miembro (`CORE_LINEAGE[2]`), que sigue registrado; las pruebas que simulan «los bytes del núcleo cambiaron» parchean
  la etapa viva; y una sesión nueva corre la concesión vigente. Ningún registro histórico se regeneró.
- *Líneas de fuente fijadas por paquetes cerrados:* dos pruebas (`test_clinical_core_closure_guard`,
  `test_clinical_core_tone_domain`) leen la línea que su paquete congeló en el archivo **tal como lo dejó el predecesor**
  (reversión declarada) y afirman además la línea viva; la auditoría cerrada `collapse_audit` corta `integration.py` por
  un marcador de texto, y la inserción de la Enmienda 3 se escribió de modo que **conserva** ese marcador (el núcleo se
  ajustó a la auditoría, no al revés).

## 13 · P3-399 y P3-400 · Revisión adversarial y certificación
### 13.1 · Revisión adversarial (P3-399)
**Una** revisión independiente, de sólo lectura (un subagente sin acceso de escritura, con el código y no con mis
conclusiones). Es análisis de modelo, no juicio docente. **Ningún hallazgo bloqueante.** Cada hallazgo se confirmó con una
sonda antes de corregirlo.

| # | Gravedad | Hallazgo | Disposición |
|---|---|---|---|
| H1 | Mayor | **Deriva de acumulación del soporte.** Con aportes en binary64 libre, las diferencias por minuto no sumaban de vuelta: una infusión detenida dejaba un residuo y, con el cese de `LOW`, el residuo se hacía negativo (−1,4 × 10⁻²⁰) y el núcleo **rechazaba la corrida** en el minuto 48. | **Corregido:** rejilla de los escritores (§6). Verificado en 120 corridas aleatorias con 1 a 3 escritores detenidos y en la sonda `stopped_infusion` del registro: estado = suma exacta de los escritores en cada minuto, y exactamente 0 al final. |
| H2 | Menor | El soporte de tono se podía declarar sobre un adaptador testigo de la Enmienda 2, y el soporte **retrasa el colapso blando** y **mejora** la lectura de consciencia mientras la entrega cae. | **Corregido** (se rechaza la combinación) y **declarado**: sonda `consciousness_reading` y limitación 7. Queda como decisión docente. |
| H3 | Menor | Las fijaciones del índice de registros no estaban a su vez fijadas; clases de linaje utilizables fuera de los registros de enmienda. | **Corregido:** el digesto de **todas** las entradas se fija en la prueba; las clases de linaje sólo valen para `PHASE2_AMENDMENT_<n>.json`; un registro abierto que diga `CERTIFIED` es un problema; una entrada `VERSIONED` debe nombrar el id y el sello del propio registro. |
| H4 | Menor | La huella del código generador de los registros nuevos cubría una lista corta de archivos. | **Corregido:** cubre el núcleo, **todos** los módulos de la aplicación (por contenido) y el arnés. |
| H5 | Menor | Sin invariante de conservación para el soporte; con el lector sin declarar, un estado que traía soporte lo perdía en silencio. | **Corregido:** invariante del minuto y rechazo explícito. |
| H6 | Menor | Mapeo de órdenes: mensaje equívoco en `start`–`stop`–`start`; un `start` por peso seguido de uno fijo construía **el segundo**; desempate lexicográfico por id; ids duplicados. | **Corregido:** sólo la primera orden del tipo puede construirse (§6); desempate por posición en el reflejo; un id cuenta una vez. |
| H7 | Nota | Mensaje del límite del lazo, desbordamiento de la suma y tasas absurdas. | **Corregido:** el rechazo nombra el factor declarado; el desbordamiento es un rechazo de procedencia; `SUPPORT_LIMIT`. |
| H8 | Nota | En una reconstrucción histórica, `permits` aceptaba el linaje reconstruido que le pasaba quien llamaba; compuerta y sitio podían discrepar. | **Corregido** (§1). |
| H9 | Notas | Aserción de linaje real tolerante a `CANDIDATE`; un comentario que decía «versión 2»; nombres de hechos del punto de control. | La aserción se **estrecha a `CERTIFIED`** al certificar; comentario corregido; el sha de la instantánea de GI se fija como literal tomado del commit base. |
| H10 | Nota | Las trazas de sombra almacenadas bajo la Enmienda 2 no se repiten sobre el núcleo vivo. | Comportamiento **preexistente** en todo cambio de miembro; declarado como limitación 10. Sin cambio de código. |

**Mutantes (herramienta de trabajo, fuera del repositorio).** 19 mutantes sembrados a mano y aplicados en proceso sobre las cuatro suites nuevas (control: 115 aprobadas): 12 de la vía de tono, la supersesión de concesiones y el linaje, y 7 que deshacen las correcciones de H1, H2, H5 y H6. **Los 19 fueron detectados.** No son una suite permanente.

### 13.2 · Certificación (P3-400)
**Etapa 1 · el candidato.** Candidato certificado: huella `e1fd602e7aa88057e4a8a0531573e989a4d57ef39287567b1bcc8fe32f4cba0c`, commit `93e4cf7fb806c2dd9193f677f88dbccf79496f30` (árbol `84c3edfb389c50a16c3f1b32a9d0d3d2543e8195`). Suite completa: **13 230 pruebas, 0 fallas, 0 errores**, 99 omitidas, 1 xfail; regresiones **56/56** activas (10 retiradas, declaradas por el propio ejecutor). La corrida usó la vista previa de certificación (`MRS_CORE_CERTIFICATION_PREVIEW=PHASE2_AMENDMENT_3`): el registro decía `CANDIDATE` y las pruebas marcadas `real_core_lineage` leyeron el estado real.

*Lanzamientos descartados (nada de ellos se reutiliza):* (1) sobre otro candidato, detenido al 21 % con 1 falla: una inserción de la Enmienda 3 había puesto entre paréntesis la condición que la auditoría cerrada `collapse_audit` usa como marcador de texto en `integration.py`; la inserción se reescribió para conservarlo y el digesto del núcleo pasó a `867bac09…`. (2) Sobre otro candidato, corrida de descubrimiento: 14 pruebas en 6 archivos fijaban la Enmienda 2 como núcleo vivo o la V2 como concesión de una sesión nueva; se adaptaron de forma declarada (§12). (3) y (4) Sobre este candidato: la plataforma reinició el contenedor a la hora y a las dos horas de corrida, sin fallas vistas y sin escasez de memoria. La corrida que certifica usó un ejecutor **reanudable** (24 bloques de archivos, cuatro a la vez, una huella tomada al inicio y comprobada en cada bloque y al final) y terminó sin necesitar reanudación.

**Etapa 2 · el árbol final sobre el linaje real.** Escribir la certificación en `PHASE2_AMENDMENT_3.json`, el índice y este punto de control cambia la huella; por eso el árbol final se corre de nuevo completo, **sin** vista previa, antes de publicarse. Sus cifras van en el informe de entrega: escribirlas en el árbol cambiaría la huella que certifican.

## 14 · Limitaciones
Todo lo siguiente es **desarrollo en la sombra**: nada es autoritativo, visible al residente, puntuado ni validado
clínicamente.

1. **El gasto y la entrega nunca suben con el tono.** La poscarga es el único camino del tono al flujo, y su sensibilidad es
   **un solo número** para toda bomba y todo volumen: un ventrículo que falla no pierde más gasto por unidad de poscarga que
   uno sano. Es la limitación de mayor peso clínico para el choque cardiogénico.
2. **El soporte no recluta retorno venoso** ni tiene inotropismo ni efecto coronario.
3. **El factor es sobre la presión de llegada del propio paciente:** la misma orden compra **más** mmHg con una llegada
   hipertensa (edema pulmonar: +28,9) que con una hipotensa (GI: +11,5). Quien **llega** vasoconstreñido no está más cerca
   del techo, y quien llega **ya con un vasopresor** no puede representarse: la llegada es la escala (tono 1, soporte 0).
4. **El agua pulmonar no lee el tono** y el sangrado no depende de la presión.
5. **No hay caso distributivo autorado**: el lector vasodilatador es `SYNTHETIC_ONLY`.
6. **Sólo se mapea la primera orden de norepinefrina del encuentro, y sólo si es `start` a tasa fija en `mcg/min`.** Detener,
   titular, reiniciar y la dosis por peso son brechas declaradas; el escritor del núcleo sabe cesar (`stop_minute`), pero el
   mapeo no lo usa. Desde la primera brecha de este tipo la corrida **ya no refleja** el vasopresor del encuentro, y lo dice.
7. **Las lecturas de consciencia se toman de la presión, así que con soporte leen MEJOR mientras el gasto y la entrega son
   menores.** Vale para la escalera directa de presión de los perfiles comprometidos (GI sin tratar, `CENTER_REFERENCE`: 70
   minutos con un nivel mejor que sin soporte, siempre con menor entrega; el primero, el minuto 52: PAM 71,9 frente a 60,2 y
   entrega 0,745 frente a 0,812) y para la conjunción de colapso blando de la Enmienda 2, que el soporte **retrasa** (colapso
   establecido en el minuto 171 sin soporte, 191 con 10 mcg/min y 199 con 40 mcg/min, con menor entrega al final). El núcleo
   lo **muestra** (sonda `consciousness_reading`) y no lo juzga: es una decisión docente. El mapeo de desarrollo **rechaza**
   combinarse con un testigo de la Enmienda 2, y una corrida con soporte de tono no abre el conjunto de testigos de
   consciencia.
8. Los tres testigos son sondas de una región cuyas magnitudes tienen confianza menor de 0,80: **ninguno es una calibración**.
9. `GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE` sigue como limitación monitoreada; nada de esto la toca.
10. **Las trazas de sombra almacenadas bajo la Enmienda 2 no se repiten sobre el núcleo vivo** (su procedencia nombra el
    digesto del núcleo que las produjo). Es el comportamiento que ya existía en cada cambio de miembro del linaje; quedan
    como registro de lo que aquel núcleo produjo y se verifican por su propia huella.

## 15 · P3-401 · Punto de control
Registro: `docs/revision/PHASE3_COMMON_TONE_CHECKPOINT.json` (`COMMON_TONE_CHECKPOINT_V1`, clase `VERSIONED`).

**Veredicto: A · `COMMON_VASCULAR_TONE_PATHWAY_READY_FOR_HUMAN_DEVELOPMENT_REVIEW`.** Es el único que admiten los hechos recomputados del árbol y la evidencia tipada: la matriz salió 10/10 como se predijo y la misma orden corre por un solo mapeo en las seis familias (no E); FR-F cumple las siete comprobaciones en los tres testigos (no C); la vía es una inserción declarada y reversible sobre el núcleo certificado (no D); y ninguna etapa de implementación espera una decisión docente, la revisión no dejó hallazgos bloqueantes y la certificación quedó en verde (no B).

«Lista para revisión humana de desarrollo» **no** es una aceptación: FR-F es un candidato sin veredicto y ningún testigo está elegido.

**Siguiente acción humana:** una persona docente decide cómo se presenta el candidato de FR-F a un revisor (qué testigo o testigos, a ciegas o no, con qué preguntas) y si hace falta una sensibilidad a la poscarga dependiente de la bomba antes de cualquier uso educativo de un vasopresor.

**Decisiones docentes abiertas:** la revisión humana de FR-F; el costo de gasto del tono según la bomba; retorno venoso e inotropismo; el paciente que llega vasoconstreñido o ya con vasopresor; un caso distributivo autorado; detener y titular la infusión; la lectura de consciencia bajo soporte (limitación 7); y la re-revisión humana de FR-A y FR-D (deseable, no bloqueante).
