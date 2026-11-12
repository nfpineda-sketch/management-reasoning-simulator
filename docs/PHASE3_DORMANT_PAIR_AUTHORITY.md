# Fase 3 · Plomería dormida de la autoridad presión + consciencia y aislamiento aguas abajo (P3-210 a P3-220) · registro (2026-11-12)

**Alcance.** Construir, **dormido y sin habilitar nada**, lo que la revisión de P3-208/P3-209 encontró que faltaba para que el par **presión + consciencia** de GI pudiera someterse algún día a una decisión
docente de autoridad: vista explícita de `mental_status` con todos sus lectores contados, la orden «Place an IV line.» sin detener el experimento, el compromiso del par en una sola transacción, el vínculo exacto con
`GI_DEVELOPMENT_SNAPSHOT_V1` en la capa, **todas** las rutas por las que el reloj avanza, y la granularidad de un turno de varios minutos. **No se habilita autoridad:** `COMMON_CORE_RUNTIME_AUTHORITY = False`; el
registro de instantáneas aprobadas para autoridad conserva **sólo** `gi_pressure_committed`; V1 sigue `RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS` y no está en ese registro; ningún valor del núcleo común se escribe en un
encuentro real; lo que ve el residente es lo heredado; la puntuación, el primer piloto y la fisiología no cambian; no se inventa ninguna regla terminal; **no hay afirmación de validación clínica**. No cambió ningún
byte de `clinical_core/` (diferencia vacía contra la base `50f387b`).

| Punto | Resultado |
|---|---|
| P3-210 lectores | 32 lectores ejecutables contados y clasificados (11 clases); 5 **enrutados** por la vista y congelados en el heredado, 13 leen trazas congeladas, 13 leen el campo vivo que ninguna transacción escribe (siete consecuentes: cuatro de imagen y **tres del motor**, que no se pueden enrutar en esta fase), 1 sin llamador |
| P3-211 guardas | vista explícita sin mutación global; la puntuación y los dos payloads de IA/docente quedan en el heredado; prueba diferencial en motor (variantes que no escriben el campo vivo), página, payloads y retención |
| P3-212 IV | `EXECUTED_NO_COMMON_PHYSIOLOGY`: lista explícita de **una** clase; no detiene; lo no soportado sigue deteniendo |
| P3-213 par | un solo payload `sbp`, `dbp`, `map` derivado, categoría; todo o nada; sólo en una copia y sólo en la superposición |
| P3-214 vínculo | en la capa (`runtime_authority_pair.py`); 15 manipulaciones rechazadas; V1 **no** se promueve |
| P3-215/216 reloj | **dos** rutas del reloj, **un** gancho; `VALIDATED_ATOMIC_INTERVAL`; el turno sin avance es un turno registrado, no un aborto |
| P3-217 página | la página real, autoridad apagada y evaluación en seco encendida: **idéntica** turno por turno, dos casos |
| P3-218 serie | 12 escenarios × 2 casos + 4 × 2 por tiempo clínico: 32 corridas; técnica y docente en columnas separadas |
| P3-219 revisión | independiente y de sólo lectura: **8 hallazgos, todos confirmados con sonda y corregidos** (§9) |
| P3-220 punto de control | cinco estados separados y **veredicto C** `PAIR_TRANSACTION_OR_RUNTIME_STILL_BLOCKED` (§10) |

Registros: `docs/revision/PHASE3_DORMANT_PAIR_AUTHORITY.json` (reconstruido desde el código por `test_phase3_dormant_record.py`), `docs/revision/PHASE3_PAIR_DRY_SERIES.json` (huella `3464f508…`).
Capa: `runtime_authority_pair.py` (nuevo, en `LAYER_SOURCES`), `observable_view.py` (nuevo, módulo neutro), `runtime_authority.py` (rutas, gancho, regla del turno sin avance, disposición, ventana de fallos).
Pruebas nuevas (171): `test_phase3_dormant_guards.py` (40), `test_phase3_dormant_pair.py` (46), `test_phase3_clock_routes.py` (38), `test_phase3_review_findings.py` (18), `test_phase3_pair_page.py` (17),
`test_phase3_pair_series.py` (10), `test_phase3_dormant_record.py` (2); arnés `test_gi_reader_guards.py`.

## 0 · Decisiones de la docencia que abren el ciclo (2026-11-12; FD-P3-188)
| Decisión | Contenido |
|---|---|
| NEW-01 | Los 15 episodios de divergencia de consciencia siguen `MECHANISTICALLY_COHERENT_DIFFERENCE`; no se modifica fisiología; la tabla docente sigue sin responder; **no hay autoridad de consciencia hasta que la docencia la revise**. |
| NEW-02 | La fisiología común **puede** representar `UNRESPONSIVE` con pulso; **no** se mapea de forma autoritativa en el `mental_status` vivo del heredado (`COMMON_PHYSIOLOGY_ALLOWED` / `LEGACY_MENTAL_STATUS_AUTHORITY_NOT_AUTHORIZED`). |
| NEW-03 | «Place an IV line.» no es una acción no soportada que detiene: se clasifica `EXECUTED_NO_COMMON_PHYSIOLOGY` si el motor confirma la ejecución; se reconoce, se traza, no hay contribuyente ni cambio fisiológico, la transacción puede seguir; **no se inventa un efecto**. |
| NEW-04 | Las ocho guardas aguas abajo son **requisito** antes de cualquier autoridad de consciencia; el arnés guionado **no** las sustituye; todo lector ejecutable que pueda afectar flujo, puntuación, payloads de IA, sugerencias docentes, disponibilidad de acciones, alta, terminación o texto del residente queda contabilizado. |
| NEW-05 | La autoridad de presión de GI está **lista en el arnés de desarrollo**, no en la página ni el runtime, hasta cubrir el tiempo clínico fuera de un turno de orden; no se amplía. |
| NEW-06 | Validar a la granularidad de la evolución fisiológica real; ningún turno externo de varios minutos esconde minutos del núcleo común sin validar en un solo compromiso; la granularidad no se elige por comodidad. |
| NEW-07 | Ninguna concesión de autoridad; ningún estado de un encuentro real lo cambia el par propuesto. |

## 1 · P3-210 · Diseño de las guardas de lectura
El inventario se **reproduce desde el código** (recorrido AST de P3-201), no se copia: **54** módulos con un uso sintáctico (7 sólo en texto), **119** sitios, **32** lectores ejecutables del observable vivo. Cada lector tiene
una **clase** (DISPLAY_ONLY 1, TEXT_GENERATION 9, CLINICAL_BRANCHING 9, SCORING 0, AI_PAYLOAD 2, FACULTY_PORTAL 3, ACTION_AVAILABILITY 3, DISCHARGE 1, TERMINATION 0, PERSISTENCE 3, OTHER 1), su **consecuencia**
(210A: visible al residente, puntuación, estado del escenario, acciones futuras, salida de IA, terminación) y su **guarda** (210B: `FREEZE_TO_LEGACY_DURING_DEVELOPMENT_AUTHORITY`, `ISOLATE_FROM_EXPERIMENTAL_AUTHORITY`,
`READ_COMMON_ONLY_IN_NONAUTHORITATIVE_DIAGNOSTIC_PATH`, `EXPLICITLY_AUTHORIZE_LATER`, `NONE_NEEDED`). Ningún lector puntúa ni termina por sí mismo: la puntuación indirecta pasa por los payloads de IA y por la retención de
una sugerencia en el portal docente.

**Las «ocho guardas» de TD-140 (2), una por una:** (1) disponibilidad de la anamnesis → **enrutada** (`_clinical_encounter_workspace`); (2) texto y pantalla visibles → el campo vivo, que **ninguna transacción escribe**
(aislada por construcción, no enrutada); (3) contrato y prompt de imagen → cuatro lectores consecuentes del campo vivo **sin enrutar**, que bloquean cualquier mapeo al campo vivo (`UNROUTED_CONSEQUENTIAL`);
(4) persistencia de traza y eventos → **enrutadas** (`learner_vitals_snapshot`, `management_state_snapshot`, y —hallazgo F4 de la revisión— `trace_phase0.observation_snapshot`); (5) payloads de IA y docente → congelados
por las capturas enrutadas; (6) retención de una sugerencia de IA (`record_findings`) → congelada por la misma captura; (7) preguntas de reflexión → congeladas por la misma captura; (8) captura de la palabra heredada
antes del compromiso → la superposición **conserva** la palabra heredada y la vista la lee de ahí.

**Los tres lectores del motor no se enrutan, y por qué.** `family_engine._validate`, `_order` y `_discharge_alarm` (elegibilidad de las órdenes orales y resultado del alta) son lectores consecuentes del campo vivo.
Un borrador de este ciclo los enrutó por la vista; **la suite completa lo rechazó**: `family_engine.py` es una de las fuentes del **congelamiento de calibración de la Fase 2** (`calibration.INPUT_PATH_SOURCES`), de modo
que editarlo mueve los digestos de congelamiento que el cierre registra (`test_phase2_closure`, `test_phase2_amendment_artifacts`). **No se edita `family_engine.py` en esta fase.** Hoy los sostiene lo único que puede
sostenerlos: ninguna transacción escribe el campo vivo y el escritor se niega a hacerlo; y son **bloqueadores nombrados** de cualquier mapeo al campo vivo (`UNROUTED_CONSEQUENTIAL` y `FROZEN_BY_THE_PHASE2_CLOSURE`).

## 2 · P3-211 · Guardas dormidas
`observable_view.py` (módulo neutro, sin estado propio, sin mutación global): la palabra común vive **sólo** en `state["development_authority_view"]` (propietario, minuto, vistas por lector, común, heredado, bandera de
mapeo), **nunca** en `observable["mental_status"]`. Cada lector enrutado (cinco: cuatro de la página y la instantánea de la traza) pide la palabra con `mental_status_for(estado, "módulo::función")` y recibe el heredado salvo que esté en `COMMON_VIEW_READERS`, que está
**vacío**. Una superposición mal formada, vieja o con vistas hostiles no es una vista: el lector obtiene el campo vivo y nunca levanta una excepción en el turno. **Prueba diferencial** (cuatro variantes: sólo
superposición, vistas hostiles, mapeada al campo vivo, mapeada y hostil): las instantáneas de la página, las tarjetas de actualización, la traza, los dos payloads de IA y la retención de una sugerencia **no cambian** en
las cuatro; la elegibilidad de las órdenes y el resultado del alta del **motor** no cambian en las dos variantes que **no** escriben el campo vivo (las únicas que una transacción puede dejar), y las dos mapeadas son exactamente
lo que el escritor rechaza. Cada lector es sensible a la palabra viva (mutante: sin la vista el efecto aparece).

## 3 · P3-212 · `EXECUTED_NO_COMMON_PHYSIOLOGY`
Vocabulario de disposición: `SUPPORTED_MODELED`, `STRUCTURAL_ONLY`, `EXECUTED_NO_COMMON_PHYSIOLOGY`, `HELD_NOT_EXECUTED`, `TERMINAL_NOT_EXECUTABLE`, `UNSUPPORTED_ACTION`. La lista explícita (212A) tiene **una**
clase (`vascular_access`) y es de sólo lectura; ninguna regla la generaliza. La ejecución es **real** (receta del libro mayor del motor), se reconoce **una vez** por id canónico, **sin contribuyente** y **sin mutación
fisiológica**, y es elegible. Una orden de acceso **retenida**, terminal, no modelada o no reconocida **no** es esa disposición. En los casos de GI el estado del libro mayor de la orden es `DUPLICATE_IGNORED` (el
paciente ya tiene acceso periférico); cuenta como ejecutada. **Esto sustituye el bloqueo C6 del punto de control anterior** (FD-P3-187): era la decisión pendiente y NEW-03 la resolvió.

## 4 · P3-213 · Compromiso del par, dormido
`PairPayload` = `sbp`, `dbp`, `map` (derivada por la regla de la pantalla), `consciousness_category`, `mental_status` (palabra de la categoría), `pulse_present`; completo o no es un payload (con NaN, booleanos y
flotantes rechazados). `PairAuthorityTransaction` compone la transacción de presión existente y añade las comprobaciones del par; **todo o nada**: si algo falla, la mitad de presión también se aborta (no hay
compromiso sólo de presión ni sólo de consciencia); **re-evalúa las nueve condiciones de la puerta** en `commit` (hoy siempre rechaza); escribe **sólo en una copia** y **sólo** `sbp`, `dbp`, `map` en el observable y la
superposición; el `mental_status` vivo **nunca** se escribe (NEW-02). Aborted y Committed son terminales (hallazgo F5). El colapso es **información de frontera**, no estado del residente (213B).

## 5 · P3-214 · Vínculo con V1 en la capa real
El vínculo (identificador, versión, SHA-256 del archivo, huellas de identidad, de registro y de registro completo, de los diez valores, del **perfil construido**, linaje declarado, vivo y de bytes, y la
ratificación) vive ahora en `runtime_authority_pair.py`; el perfil se construye **sólo** del registro inmutable. Se rechazan: otro identificador o versión, instantánea parcial, un parámetro modificado (1e-9), huella
errónea, linaje equivocado, sustitución por LOW, HIGH o CENTER_REFERENCE, un registro que no es de instantánea, no ratificado, o un punto de presión distinto. **214A:** V1 no se agrega al registro de autoridad. El archivo de
pruebas `test_gi_snapshot_binding.py` re-exporta el vínculo de la capa, así que cada prueba anterior ejerce ahora el código real. *El registro inmutable de V1 dice «ninguna importación por la capa ni la aplicación»:
ya no es cierto; el registro no se edita y esta nota lo declara.*

## 6 · P3-215 y P3-216 · Rutas del reloj y granularidad
**Inventario (reproducido del código):** `sim_time` lo escriben `family_engine.advance_clinical_time` y `family_engine.execute_family_bundle` (las **únicas** que alcanza un encuentro de GI), más la función de
línea heredada de la página, el motor acoplado y el generado (otras familias: el sitio y la evaluación rechazan el caso). La página las alcanza por **dos** rutas: el turno de orden (`execute_bundle`, una llamada) y
`spend_clinical_time` (tres sitios: pregunta, examen, espera). Un escritor nuevo del reloj hace fallar una prueba en lugar de pasar sin verse.

**Un solo gancho (215A).** `app._after_the_clock_moved` llama a `runtime_authority.after_clock_moved` (delegado de la capa) justo después de que el motor movió el reloj y la sombra lo observó, en **ambas** rutas con
la ruta como literal que una prueba lee; toma las decisiones **la capa**, no la página. En `spend_clinical_time` el sitio se abre **antes** de que pase el tiempo (un sitio sólo se abre en la llegada), como lo hace el
turno de orden. **Con autoridad y evaluación apagadas (lo predeterminado) la página es exactamente la heredada (215B)**: con la sombra apagada el gancho vuelve antes de importar nada; con la sombra encendida y la evaluación apagada no escribe ni guarda nada.

**Turno sin avance.** Un turno que no mueve el reloj y sólo trae órdenes estructurales o reconocidas sin fisiología (el IV, una consulta, una reevaluación) no es un minuto nuevo: se **registra**, se verifica que el
dominio de presión no se movió (un MAP que **aparece** en el primer refresco es su derivación, no un movimiento) y el experimento sigue. Si el turno trae otra clase, o la presión se movió, o la sombra registró un
fallo, **detiene**. Esto es un cambio deliberado y acotado del sitio certificado para cumplir NEW-03; el comportamiento certificado de «minuto duplicado sin estado previo» (g7) se conserva.

**Granularidad (216).** `PER_MINUTE_TRANSACTION` **se rechaza**: el motor heredado expone **un solo estado al final del turno**; no hay estado heredado intermedio que escribir ni comparar, así que una transacción
por minuto no tendría qué comprometer. Se elige `VALIDATED_ATOMIC_INTERVAL`, con **seguridad equivalente**: cada minuto del turno se valida con las **mismas** comprobaciones (candidato presente y finito, reproducible
desde el artefacto inmutable con **un** replay por turno, sin fallo en ese minuto, categoría en la escala, pulso, mismo curso que la corrida de presión, frontera de colapso, ventana de 240 min); el compromiso es **uno**,
del estado final; un fallo en el minuto *k* **no compromete nada**, detiene el experimento y **ningún minuto posterior** se vuelve autoritativo (216B); tras la detención, un encuentro que ya había comprometido es
`INVALID_FOR_CONTINUATION` y **nunca** continúa con el motor heredado. Un minuto intermedio escondido tras un final limpio lo detienen **dos** comprobaciones independientes (la del intervalo y la comparación del curso
por minuto; el mutante M1 quita ambas y entonces el final solo se compromete). **El sitio de presión sola** juzga el candidato y el replay del minuto final y **todo fallo aún no juzgado** (hallazgo F3);
la comprobación por minuto del candidato y del replay de cada minuto de un turno largo existe sólo en el evaluador del par (límite R2).

## 7 · P3-217 · La página real, en seco
`streamlit.testing.AppTest`, ambos casos de GI, el guion de un residente: pregunta, examen, IV, espera, bolo, **infusión de 60 minutos en un turno**, acción no soportada, espera. Tres modos del mismo guion: todo apagado
(lo predeterminado), sombra y evaluación en seco encendidas. **Resultado:** texto visible, observable del motor, eventos, libro mayor de órdenes y Management Trace **idénticos turno por turno** (sólo se enmascaran los
identificadores aleatorios de la corrida: id del caso, prefijo del id de orden y reloj de pared de un envío); nada del vocabulario de la evaluación aparece en la pantalla; con todo apagado la página **no guarda ningún
estado del par**. Con la evaluación encendida el gancho vio **ambas** rutas (la primera pregunta es el minuto 2), la infusión se validó en sus 60 minutos, el IV fue `NO_ADVANCE_TURN` y el experimento siguió, y la acción no
soportada lo terminó de forma visible (`supported_management`, autoridad ya había comenzado). Aparte: una espera de cinco horas sin tratar alcanza la ventana o la frontera de colapso y el experimento se detiene,
mientras la página no cambia. **Con la configuración de desarrollo ya existente de la autoridad de presión**, una primera pregunta abre el sitio **antes** de que pase el tiempo y compromete su minuto en la ruta de
tiempo clínico (cierra C9 en la página, no sólo en el arnés).

## 8 · P3-218 · Serie completa en seco (32 corridas; turnos de 5 min; preguntas de 2 min)
El evaluador es el de la capa, alimentado por el **mismo** gancho que la página. Turnos de 5 minutos (un turno que un residente realmente da); un turno de un minuto repetiría el replay del núcleo por minuto (una
corrida de 240 min costaba ~4,5 min de CPU): es costo, no seguridad, porque dentro de cada turno **todo minuto se valida**. Idéntico en los dos casos:

| Escenario | `WOULD_COMMIT` (turnos) | Último | Aborto | Causa |
|---|---|---|---|---|
| sin tratar | 41 | 205 | 210 | `collapse_boundary_not_reached` (la frontera se cruza en el 207, **dentro** del turno que termina en el 210) |
| tratamiento temprano · tardío · sólo fluidos · sólo sangre · deterioro grave | 13 · 29 · 18 · 13 · 45 | 120 · 200 · 120 · 120 · 240 | — | sin aborto |
| recuperación tras deterioro grave | 32 | 160 | 280 | `window_open` (4 U de sangre = 120 min en **un** turno que termina fuera de la ventana) |
| rescate tardío | 41 | 205 | 210 | la frontera llega antes de que se dé el rescate (la orden no se evalúa) |
| **IV line** (turno 0, luego SF+SG) | 13 | 120 | — | un `NO_ADVANCE_TURN`; **no detiene** |
| **acción no soportada** (norepinefrina) | 2 | 10 | 11 | `supported_management` + `pressure_validated` + `interval_minutes_validated`; autoridad ya comenzada → `INVALID_FOR_CONTINUATION` |
| recuperación dentro de la ventana · infusión de 60 min | 37 · 13 | 240 · 120 | — | la infusión se valida minuto a minuto |

Cada fila separa **`technical`** (lo que el evaluador reprodujo) de **`faculty`** (`consciousness_authority_decision: NOT_DECIDED`, siempre; la presión: `READY_IN_DEVELOPMENT_HARNESS_ONLY_NOT_PAGE_RUNTIME` hasta
este punto de control): una serie técnicamente limpia no es una aprobación (218A). Las cuatro series por tiempo clínico (esperas de 2 min por pregunta) dan el mismo curso donde coinciden los minutos, y el
mismo aborto por la frontera en el 208. Observar no cambia nada del heredado (comparación contra las mismas órdenes sin sombra ni evaluador).

## 9 · P3-219 · Revisión adversarial independiente
Revisor de sólo lectura (declaró no haber abierto `validation/` ni modificado archivo alguno); cada hallazgo se **confirmó con la sonda del revisor** antes de corregir y las sondas se convirtieron en pruebas (`test_phase3_review_findings.py`).

| # | Gravedad | Hallazgo | Corrección |
|---|---|---|---|
| F1 | **ALTO** | un turno sin avance no se contrastaba con el libro mayor: «Place an IV line. Also give ondansetron» seguía | `settle_provenance` juzga el turno sin avance con la **misma** regla que el evaluador |
| F2 | medio | una captura fallida (`before=None`) dejaba comprometer un turno largo sin su tratamiento; una brecha sin tipo se descartaba | todo fallo no juzgado rechaza; la brecha sin tipo es `untyped_gap` (no soportada) |
| F3 | medio | un fallo del primer minuto del turno, o durante un turno sin avance, no se juzgaba | marca de agua de fallos juzgados |
| F4 | medio | `trace_phase0.observation_snapshot` leía la palabra viva con clave dinámica, sin enrutar y mal clasificada | enrutada; ahora 5 lectores enrutados |
| F5 | bajo | un par rechazado se podía re-validar y comprometer | estados terminales |
| F6 | bajo | una superposición mal formada hacía lanzar a la vista; un 3.0 pasaba como categoría | entero exacto; la vista nunca lanza |
| F7 | bajo | la liquidación comparaba la clase sin normalizar | regla compartida normalizada |
| F8 | bajo | el caso del evaluador no se comparaba con el de la sesión; un resumen viejo sobrevivía; el replay era cuadrático | igualdad de caso; se descarta el resumen; un replay por turno |

**Los doce ataques del encargo**, con su defensa y su mutante/control negativo: (1) `mental_status` hacia puntuación, ramificación, payloads, alta o disponibilidad → vista + prueba diferencial (mutante: sin la vista el
lector cambia); (2) compromiso parcial → todo o nada (F5 cierra la resurrección); (3) V1 falsificado → 15 rechazos; (4) IV que detiene a mala hora / no soportado que sigue → M3 y M4 (sin la regla, el IV detiene; ampliar la
lista deja pasar la clase no soportada); (5) avance del reloj fuera de turno de orden no visto → inventario + M2 (un avance no cableado lo atrapa `turn_was_observed` en el turno siguiente); (6) minuto intermedio
de una infusión escondido → M1; (7) fallo de validación a mitad de intervalo → matriz `no_candidate`/`failure_at_minute`/`not_one_course` × minutos 1, 15, 29; (8) frontera cruzada dentro del turno → prueba de la
frontera y serie sin tratar; (9) respaldo al heredado tras comenzar la autoridad propuesta → `HALTED` sin `WOULD_COMMIT` posterior (serie 2) y `INVALID_FOR_CONTINUATION`; (10) página cambiada en seco → §7; (11) un evaluador
que escribe → M6 (su guarda lo registra); (12) un gancho roto que lanza al turno → M7. **No se halló ninguno sin defensa** salvo los ocho hallazgos corregidos.

## 10 · P3-220 · Punto de control
**Cinco estados, separados:**

| Estado | Valor |
|---|---|
| `PRESSURE_TECHNICAL_READINESS` | **`READY_FOR_A_DEVELOPMENT_EXPERIMENT`** — arnés **y** página, ambas rutas; el IV ya no detiene; todo fallo no juzgado rechaza. Límite: sólo desarrollo; el sitio de presión sola valida el minuto final y no el candidato/replay de cada minuto intermedio (R2). |
| `CONSCIOUSNESS_TECHNICAL_READINESS` | **`OVERLAY_ISOLATION_PROVEN_LIVE_FIELD_MAPPING_BLOCKED`** — los 32 lectores contados; ninguno consume la palabra común; el mapeo al campo vivo está bloqueado por siete lectores consecuentes sin enrutar: cuatro de imagen y tres del motor (R3). |
| `CONSCIOUSNESS_FACULTY_READINESS` | **`NOT_READY`** — la tabla de divergencia sin responder (NEW-01); «Unresponsive» con pulso permitido en la fisiología común pero **no** en el campo vivo (NEW-02). |
| `PAIR_TRANSACTION_READINESS` | **`TRANSACTION_AND_DRY_EVALUATION_READY_RUNTIME_SITE_NOT_BUILT`** — la transacción y su evaluación en seco están listas y probadas **en copias**; no existe un **sitio de autoridad del par** (R1). |
| `PAGE_RUNTIME_READINESS` | **`DRY_ONLY_PAGE_PROVEN_UNCHANGED`** — la página es idéntica en seco; no hay autoridad del par en la página. |

**Veredicto: C · `PAIR_TRANSACTION_OR_RUNTIME_STILL_BLOCKED`.** Ni siquiera un A concedería autoridad; esto no concede nada. Lo que bloquea: **R1** (construcción; no exige decisión docente para construirse, sí para
habilitarse) el sitio de autoridad del par que componga las comprobaciones del evaluador, `PairAuthorityTransaction.commit`, el artefacto, la procedencia, la detención y el almacén, con sus pruebas de página bajo una aprobación
de prueba; **R2** la comprobación por minuto del candidato y del replay en el sitio de presión sola si se va a usar sin el par en turnos largos; **R3** (sólo si la docencia pidiera alguna vez que el campo heredado lleve la
palabra común) el enrutamiento de los cuatro lectores de imagen y de los tres del motor (estos últimos exigen el procedimiento de enmienda del congelamiento de la Fase 2); **docencia:** F1 la tabla de divergencia y la lectura de «Unresponsive» con pulso (FD-P3-187 C1, C5); F2 la concesión de cualquier autoridad y la aprobación de
una instantánea **para** autoridad (no se pide). Lo que la docencia puede decidir **hoy** con evidencia: la serie técnica de §8 (qué ventanas de `WOULD_COMMIT` y por qué terminan).

## 11 · Adaptaciones declaradas y límites
- **Pruebas anteriores adaptadas** (cada una protege lo mismo que antes): `test_gi_preauthority_review.py` (rol `ROUTED`, clase `MECHANISM`, filas de `observable_view.py` y `runtime_authority_pair.py`),
  `test_phase3_gi_preauthority_review.py` (inventario: cuenta de sitios por los dos módulos de mecanismo; el sitio `trace_phase0` pasa de `<module>` a `observation_snapshot`; **la lectura de los dos límites de P3-208 se
  reemplaza por la de su cierre**: el registro de P3-208 es inmutable y sigue diciendo lo que el revisor leyó), `test_phase3_gi_authority_readiness.py` (conteo de consumidores: la página y la traza) y `test_phase3_gi_development_snapshot.py` (el registro de punto de control de este ciclo nombra la instantánea a propósito),
  `test_shadow_core_isolation.py` y `test_runtime_shadow_plumbing.py` (`runtime_authority_pair` en la capa declarada; la página sigue cruzando por **dos** puentes), `test_runtime_shadow_evidence.py`, `test_gi_snapshot_binding.py`
  (re-exporta la capa).
- **Cambios deliberados en archivos certificados:** `runtime_authority.py` (rutas, regla del turno sin avance, marca de agua de fallos, liquidación del turno sin avance, disposición), `trace_phase0.py` (una lectura por la
  vista; el orden de las claves de `visible` no cambia), `app.py` (cuatro lecturas por la vista, con la importación **dentro** de cada función porque las pruebas cargan esas funciones por AST sin las importaciones del módulo, y el
  gancho). **`family_engine.py` NO se modifica** (fuente del congelamiento de calibración de la Fase 2). Con las banderas apagadas el comportamiento es el heredado.
- **Límites:** las comprobaciones corren en **un** proceso de Python (no hay defensa contra código de proceso que alcance atributos privados, p. ej. la transacción de presión interior del par); el escaneo de lectores no ve
  acceso dinámico (declarado en la propia auditoría); la evaluación en seco con su bandera encendida cuesta un replay de la corrida por turno; las corridas de la serie son de turnos de 5 y 2 minutos, no de un minuto.
- **Sin validación clínica** de ninguna magnitud, de la instantánea ni de la divergencia; ninguna etiqueta de este registro es una afirmación clínica.
