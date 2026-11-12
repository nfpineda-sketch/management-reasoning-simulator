# Fase 3 · Parada efectiva del experimento de autoridad de presión de GI y prevención de la continuación posterior a la autoridad (P3-250 a P3-264) · registro (2026-11-12)

**Alcance.** Convertir la parada **consultiva** del primer experimento real de autoridad de desarrollo (TD-143 §1 y §10) en una parada **efectiva**: una vez que hubo **al menos un compromiso REAL** de presión
y una transacción posterior deja el experimento `INVALID_FOR_CONTINUATION`, **ningún** avance de tiempo clínico ni acción de manejo puede continuar esa sesión hasta que un operador la resuelva (este ciclo: sólo
abandonar o bloquear). Es **control del ciclo de vida del experimento**; no es muerte del paciente, no es terminalidad clínica, no es un estado terminal de la fisiología común ni un desenlace que lea el residente.
**Qué NO se habilita (ni siquiera con el veredicto A):** autoridad de consciencia, escritura de la consciencia común en `mental_status`, exposición al residente, despliegue a residentes, autoridad de producción,
cambio del primer piloto congelado, semántica terminal inventada, reajuste de fisiología, puntuación nueva, ninguna afirmación de validación clínica. `COMMON_CORE_RUNTIME_AUTHORITY` **sigue `False`**;
`clinical_core/` y `family_engine.py` **no se modificaron**; con las banderas de autoridad apagadas el comportamiento es idéntico al de antes (una sola búsqueda de claves, sin lecturas del almacén).

## 0 · Decisiones de la docencia y del arquitecto (2026-11-12; FD-STOP-01 a FD-STOP-09; FD-P3-209 a FD-P3-212)
| Decisión | Contenido |
|---|---|
| FD-STOP-01 | La parada es una **parada operativa efectiva** (control del experimento), no una regla clínica terminal. |
| FD-STOP-02 | Tras ≥ 1 compromiso REAL y una transacción posterior que deja el experimento `INVALID_FOR_CONTINUATION`, no puede avanzar el tiempo clínico ni ejecutarse una acción de manejo en esa sesión hasta una resolución explícita del operador. |
| FD-STOP-03 | **Sin retroceso silencioso al motor heredado.** El motor heredado puede seguir intacto para análisis forense; no continúa el encuentro. |
| FD-STOP-04 | Un fallo **antes** del primer compromiso es un aborto limpio: el encuentro heredado intacto puede continuar. La distinción es explícita. |
| FD-STOP-05 | Sin semántica terminal: ni muerto, ni paro, ni estado mental terminal, ni diagnóstico, ni cambio de fisiología; sólo un estado operativo del experimento. |
| FD-STOP-06 | Sin reanudación automática. En este ciclo sólo se exige **abandonar/bloquear**; no se revierte el estado autoritativo ya comprometido. |
| FD-STOP-07 | La página impide toda progresión clínica de la sesión; puede mostrar un aviso operativo **de desarrollo/docente**, sin texto médico para el residente que sugiera muerte, y sin tocar el primer piloto congelado. |
| FD-STOP-08 | Ninguna autoridad de consciencia nueva, ningún mapeo vivo de `mental_status`, ningún cambio de C1 ni de C5. |
| FD-STOP-09 | Ninguna ampliación de autoridad. |

## 1 · P3-250 · Reconstrucción del ciclo de vida (qué había y qué hay)
**Antes.** Existía **una** máquina de estados, la de la **transacción** (`AuthorityTransaction`: `OPEN`, `COMMITTED`, `ABORTED`, un minuto a la vez). El experimento se marcaba `HALTED` en el artefacto y la página
seguía: el motor heredado corría el encuentro desde el minuto fallido con la presión heredada y **la página no decía nada**. El estado de sesión (`SITE_KEY`, `ARTIFACT_KEY`, `HALTED_KEY`) era **volátil**: no estaba
en `SESSION_FIELDS`, así que un encuentro guardado y reabierto no traía el sitio; sólo se **marcaba** en el almacén (M1 de la revisión anterior).

**Ahora: dos máquinas, nunca confundidas.**
| Máquina | Estados | Dueña |
|---|---|---|
| Transacción (por minuto) | `OPEN` → `COMMITTED` \| `ABORTED` | `runtime_authority.AuthorityTransaction` |
| **Sesión de autoridad (todo el experimento)** | `NOT_STARTED`, `PREAUTHORITY`, `ACTIVE_AUTHORITY`, `PRECOMMIT_ABORT`, `INVALID_FOR_CONTINUATION`, `COMPLETED_AUTHORITY` | `runtime_authority_session` (módulo nuevo de la capa) |

Grafo (datos, `TRANSITIONS`, cerrado y sin transición oculta): `NOT_STARTED → PREAUTHORITY → {ACTIVE_AUTHORITY, PRECOMMIT_ABORT, COMPLETED_AUTHORITY}`; `ACTIVE_AUTHORITY → {INVALID_FOR_CONTINUATION, COMPLETED_AUTHORITY}`;
`INVALID_FOR_CONTINUATION`, `PRECOMMIT_ABORT` y `COMPLETED_AUTHORITY` son **terminales para la sesión**. **No existe** `ACTIVE_AUTHORITY → fallo → continuación heredada ordinaria`, ni `INVALID → ACTIVE`, ni `PRECOMMIT_ABORT → ACTIVE`.
Estado final de un encuentro con autoridad de desarrollo: A) preautoridad/compatible con el heredado, B) `ACTIVE_AUTHORITY`, C) `COMPLETED_AUTHORITY`, D) `INVALID_FOR_CONTINUATION` bloqueado efectivamente.

**Fuente de verdad: el artefacto del experimento.** El estado de la sesión se **deriva** de él (`lifecycle_of_artifact`: `halted` con compromiso → `INVALID`; `halted` sin compromiso → `PRECOMMIT_ABORT`; con compromiso y sin
halt → `ACTIVE`; sin compromiso → `PREAUTHORITY`; cerrado sin halt → `COMPLETED`). Lo que sobrevive: **rerun** (todo el `session_state`); **refresco/nueva sesión de navegador** (nada: es un encuentro **nuevo**, el viejo queda en el
almacén duradero y no se vuelve sesión); **encuentro guardado y reabierto** (sólo `SESSION_FIELDS`: viaja el registro, no el sitio); **reinicio del proceso** (sólo lo duradero: el almacén; la guarda no depende de él salvo el caso de estado perdido).

## 2 · P3-251 · El registro persistente de sesión (`phase3_authority_session`)
Un diccionario con huella (`record_digest`) derivado del artefacto (`session_record_of`), publicado por el sitio en el `session_state` tras cada turno y **incluido en `SESSION_FIELDS`**: viaja con el intento guardado. Contiene:
`lifecycle`, `continuation_allowed`, `stop_policy` (`EFFECTIVE_STOP` para sitios reales con concesión; `ADVISORY_TEST_ONLY` para puntos de prueba), `legacy_fallback_allowed`, `authority_began`,
`last_authoritative_minute` y `last_authoritative_pressure` (la presión común del último minuto comprometido), identidad de la concesión (id y huella), modo, caso, familia, instantánea, linaje, ids de encuentro y de
experimento, `halted`, `halt_reason`, `stop_class` (vocabulario cerrado), `failed_minute`, `failed_operation`, `last_artifact` (digesto y minutos registrados). **No contiene consciencia ni dato del paciente.**
`record_problems` lo verifica (digesto, coherencia interna: un `INVALID` con `continuation_allowed` verdadero no verifica); `replay_session_record` lo reproduce **desde el artefacto solo**. Un registro editado a mano
(campo por campo, parametrizado en las pruebas) no es aceptado.

## 3 · P3-252 · La guarda compartida `AUTHORITY_SESSION_CAN_CONTINUE`
`continuation_guard(store, state, environ, encounter_ended)` (en la capa; la página la alcanza **sólo** por `runtime_authority.continuation_guard`). Se consulta **antes** de toda operación que pueda avanzar el tiempo,
ejecutar una acción, liberar una orden retenida, alterar al paciente o abrir otra transacción de autoridad.
* **Fuentes**: el sitio vivo (si es de este encuentro), el registro de sesión (verificado y de este encuentro) y el artefacto de sesión. **La afirmación más estricta gana; el desacuerdo niega** (forma `(authority_began, último minuto, halted)` distinta entre fuentes → `STALE_OR_CONFLICTING_STATE`); una fuente ilegible niega; el registro que no verifica niega; cualquier excepción interna niega (falla cerrada).
* **Camino barato**: sin claves de autoridad en la sesión y con las banderas apagadas, el resultado es «permitido» tras un puñado de búsquedas en un diccionario (probado con un almacén espía: ≤ 4 lecturas).
* **Regla del sitio perdido**: un registro `ACTIVE_AUTHORITY` sin sitio vivo (encuentro reabierto, objetos perdidos) con política de parada efectiva → `INVALID` (`ENCOUNTER_RESUMED_WITHOUT_ITS_AUTHORITY_SITE`), el registro se invalida y se guarda; un registro `PREAUTHORITY` sin sitio → se permite como `PRECOMMIT_ABORT` (nunca fue autoritativo).
* **Sin ninguna afirmación** pero con banderas pedidas y minuto > 0: se busca la marca duradera (`note_resume_without_site`) o la coincidencia estricta caso + minuto + presiones comprometidas (`durable_match`).
* **Clases de operación** (`OPERATIONS`): `READ_ONLY`, `ENCOUNTER_MUTATING`, `CLINICAL_TIME_ADVANCING`, `LEAVES_THE_SESSION`. Con la sesión detenida **sólo** sobreviven leer y salir; una operación que nadie clasificó se **niega** (una ruta sin clasificar es un desvío).
* **Persistencia del compromiso**: si el artefacto de un sitio real **ya comprometido** no puede escribirse (error del almacén o colisión de identidad), el sitio se detiene con `ARTIFACT_PERSISTENCE_FAILED`: una sesión de autoridad que nadie podría reconocer después sería el camino silencioso de vuelta al motor heredado.

## 4 · P3-253 y P3-254 · La página y el bloqueo de la continuación
`app.py` (los únicos cambios; con las banderas apagadas son una búsqueda de claves por pasada):
* `_authority_continuation()` pregunta **una vez por pasada** del espacio de trabajo; `_authority_blocks(operación)` es el punto de consulta de cada chokepoint.
* **`spend_clinical_time`** (la única vía del reloj fuera de un turno de orden) levanta `AuthoritySessionStopped` **antes** de llamar al motor; **`_process_encounter_submission`** (la única llamada de `execute_bundle`) consume una entrada duradera pendiente y la marca `blocked_by_authority_stop`: **no corre, no mueve nada y no hace que la página gire sobre ella**.
* Con la sesión detenida **no se dibujan** la caja de preguntas, «Ask»/«Ask about this topic», «Examine patient», la caja de órdenes y su panel (Send, Cancel pending orders, el formulario de razonamiento/orden retenida, la explicación retrospectiva) ni el ECG; **«Complete Encounter & Begin Review» y «Finish now» quedan deshabilitados**. Se conservan lo que **sale** de la sesión («Reset scenario», «Save & return to dashboard», «End this attempt without completing review») y la lectura.
* **Aviso** (sólo de desarrollo, operativo): «DEVELOPMENT AUTHORITY EXPERIMENT HALTED · This experimental encounter session cannot continue: no further clinical time or management actions are available in it. To start a new one, end this attempt without completing review (or reset the scenario).» Sin palabras clínicas terminales (`notice_is_operational` lo verifica contra la lista de prohibidas). «Save & return to dashboard» **guarda** el intento detenido y al reabrirlo sigue detenido (el registro viaja): sólo terminar el intento o reiniciar lo resuelve.
* **`execute_bundle` no se edita** (las regresiones lo cargan por AST); su único llamador está protegido.
* **Inventario con alarma** (`test_phase3_stop_page.py` t1 a t4): exactamente qué funciones de `app.py` pueden mover el reloj, ejecutar un paquete o alterar el encuentro; los 13 botones del espacio de trabajo, cada uno clasificado (región no dibujada, deshabilitado, inocuo o sale de la sesión); un botón o ruta nuevos **fallan** hasta que alguien los clasifique.

## 5 · P3-255 · Refresco, reapertura, sesión nueva y pestaña duplicada
| Situación | Resultado (probado en la página real) |
|---|---|
| `rerun` de la página detenida | Sigue detenida; ningún motor corre; estado, libro, eventos y Management Trace sin cambio |
| Encuentro guardado y reabierto (sólo `SESSION_FIELDS`) con banderas **encendidas** | Detenido (viaja el registro `INVALID`) |
| Ídem con banderas **apagadas** | Detenido: **apagar la bandera no reanuda** |
| Encuentro `ACTIVE_AUTHORITY` reabierto sin sitio | `INVALID` (`RESUMED_WITHOUT_SITE`), sin retroceso al heredado |
| Refresco / sesión nueva de navegador | Un encuentro **nuevo**; lo detenido queda en el almacén duradero y **no** vuelve a ser sesión |
| Pestaña duplicada (el mismo guardado dos veces) | Detenida en ambas; si estaba `ACTIVE`, inválida en ambas; ninguna se mueve |
| Registro y artefacto en desacuerdo, registro obsoleto o de otro caso, almacén ilegible | Se niega (falla cerrada); un registro de otro encuentro no dice nada de éste |

## 6 · P3-256 · Fallos antes del primer compromiso
Acción no soportada como **primera** acción, configuración de concesión/linaje/entorno errónea, instantánea que no coincide, colapso ya establecido en el primer minuto, fallo de validación en el primer minuto, sin almacén
configurado: **0 compromisos**, `PRECOMMIT_ABORT` (o ningún sitio), `continuation_allowed = True`, `legacy_fallback_allowed = True`, el encuentro heredado intacto **idéntico** (presiones observadas frente a un encuentro de control
que nunca pidió el experimento) y **sin aviso de parada**. La distinción con el estado posterior al primer compromiso es explícita en el registro (`authority_began`) y en la página.

## 7 · P3-257 · Matriz de fallos posteriores al primer compromiso (página real, el caso 57m)
Cada fila: tras ≥ 1 compromiso real, el fallo deja `INVALID_FOR_CONTINUATION`, `continuation_allowed = False`, `legacy_fallback_allowed = False`, `stop_class` esperado, `last_authoritative_minute`/`pressure` **iguales a lo que se comprometió antes del fallo** (leído del artefacto, no del registro), `failed_minute`, `failed_operation` y digesto del último artefacto; no se compromete ningún minuto después; y **cinco intentos** (pregunta, orden, tratamiento, vía IV, examen) más un `rerun` **no** llegan al motor (contadores de las dos entradas del motor = 0) ni mueven el estado.
| Fallo | `stop_class` |
|---|---|
| acción no soportada | `UNSUPPORTED_ACTION` |
| linaje distinto | `GATE_OR_LINEAGE` |
| artefacto que no reproduce el minuto | `VALIDATION` |
| fallo de validación | `VALIDATION` |
| minuto interno (error interno) | `INTERNAL_ERROR` |
| persistencia del artefacto (el minuto sí se comprometió y **es** el último autoritativo) | `ARTIFACT_PERSISTENCE` |
| concesión equivocada | `GATE_OR_LINEAGE` |
| invariante (escritura fuera de dominio) | `REPLAY_OR_ARTIFACT` |
| turno duplicado/repetido de cero minutos sobre un minuto ya comprometido | `REPLAY_OR_ARTIFACT` |
Además, a nivel de sesión (`test_phase3_stop_lifecycle.py`): sesión obsoleta, registro editado, fuentes en conflicto.

## 8 · P3-258 · La frontera de colapso como parada efectiva (no un desenlace del paciente)
Sin tratar, el GI compromete hasta el minuto 180 (frontera `ESTABLISHED` desde el 207, ventana de 240 minutos): el primer minuto rechazado es el **240**, y **el estado que cruzaría la frontera nunca se compromete**. La sesión queda
`INVALID_FOR_CONTINUATION` con `stop_class = COLLAPSE_BOUNDARY`, último minuto autoritativo 180, minuto fallido 240, y **no continúa**. En la página real (ambos casos) el paciente **no** pasa a un estado terminal (`pulse_present` no es falso,
`mental_status` no pasa a «Unresponsive»), no aparece ninguna palabra terminal en la pantalla ni en el aviso, y ningún intento posterior alcanza al motor. La parada es del **experimento**, no un hecho clínico.

## 9 · P3-259 · Consistencia artefacto/almacén/sesión y replay
Un artefacto confirmado nunca convive con «no hay autoridad»; un artefacto detenido nunca convive con `ACTIVE`; el registro **se reproduce desde el artefacto solo** (`replay_session_record`: último estado válido, fallo, razón de
parada, `continuation_allowed = False`) y el registro, el sitio y el artefacto de un mismo encuentro **coinciden** campo por campo (las pruebas de consistencia del ciclo). Un registro cuyo digesto no verifica, o que dice
«continuable» sobre un artefacto detenido, no se acepta.

## 10 · P3-260 · Concurrencia y sesiones duplicadas — veredicto `SINGLE_PROCESS_SESSION_SAFETY_SUFFICIENT_FOR_DEVELOPMENT`
Streamlit da a cada sesión de navegador su propio `session_state` dentro de **un** proceso de Python; la capa **no guarda estado mutable propio** (sólo tablas constantes: `_APPROVED_SNAPSHOT_POINTS`, `TRANSITIONS`, `OPERATIONS`,
`_BODY`; sin `global`, sin caché; una prueba por AST lo exige y otra prueba que ningún módulo escribe en ellas). Probado: dos encuentros vivos del mismo caso (uno detenido y otro en curso) no se tocan; los turnos
intercalados entre dos sesiones consultan cada una **sólo su estado**; un registro ajeno en la sesión equivocada no abre ni cierra nada; la misma sesión guardada abierta en dos pestañas queda detenida (o inválida) en ambas;
dos sesiones reales de la página nunca llegan **idénticas** (identidades de encuentro y de experimento distintas) ni se pisan en el almacén (create-only, un nombre por encuentro, escritura idempotente del mismo contenido).
**Residuales declarados** (no bloquean el desarrollo de un solo proceso): (i) varios procesos de Python detrás de una misma dirección comparten **sólo** el almacén duradero, cuyos archivos se escriben de una vez (un lector puede
encontrar un archivo parcial: se omite) y **no** son lo que la guarda usa para continuar; (ii) dos encuentros de llegada **idéntica** (la semilla fija del arnés sin cabeza, nunca la página real) que luego divergen con una acción de igual
duración chocan en el almacén create-only y el **segundo se detiene** (`ARTIFACT_PERSISTENCE_FAILED`, falla cerrada), nunca continúa sin registro duradero.

## 11 · P3-261 · Página real de extremo a extremo (los dos casos)
| Escenario | Prueba | Resultado |
|---|---|---|
| A · progreso normal con autoridad | s1 | La guarda no estorba: compromisos sucesivos, controles dibujados, sin aviso |
| B · acción no soportada tras el primer compromiso | s2, s3, s15 | `INVALID`, aviso, controles ausentes, cero llamadas al motor, estado sin cambio; una entrada pendiente se reclama y se marca bloqueada |
| C · fallo de validación inyectado | s5, s15 | Ídem |
| D · frontera de colapso | s6 | Parada en el 240 con último autoritativo 180; sin lenguaje terminal ni campo terminal |
| E · refresco/reapertura tras el paro | s7 a s10, s9 | Sigue detenido con banderas encendidas y apagadas; `ACTIVE` sin sitio → `INVALID` |
| F · acción mutante de cero tiempo tras el paro | s2 | Examen, orden de cero minutos, IV y «reassess» no llegan al motor |
| G · lectura tras el paro | s4, s16 | Pantalla y monitor disponibles, nada se mueve, sin fuga de consciencia común ni de la concesión |
Además: «Reset scenario» (sale de la sesión) borra las claves del experimento y deja el experimento detenido en el almacén (`s4b`).

## 12 · P3-262 · Revisión adversarial independiente (sólo lectura, 11 ataques en 19 sondas)
Un revisor independiente, de sólo lectura, atacó el candidato con 19 sondas propias (el reloj y las órdenes, refresco/reapertura/pestaña duplicada con las banderas encendidas y apagadas, registro y artefacto alterados, orden retenida, intervalo largo, frontera de colapso,
concesión o linaje equivocados, escritores no protegidos, identidad byte a byte frente al HEAD con las banderas apagadas, desempeño, aislamiento de la capa). **Resultado: 1 alto (condicionado a un fallo interno), 2 medios (uno de ellos «bajo/medio» del revisor), 5 bajos.**
**Cada alto y medio fue reproducido por mí con la sonda del revisor antes de repararlo**, y repetido después:

| Hallazgo | Defecto | Reparación | Prueba de regresión |
|---|---|---|---|
| **ALTO-1** | Si `artifact()` falla **tras el primer compromiso**, devuelve un esqueleto degradado («halted, sin minutos») y el registro se derivaba sólo de él: `PRECOMMIT_ABORT`, `authority_began` falso, continuable. Registro, artefacto guardado y sitio coincidían en la historia degradada: **retroceso silencioso al heredado después de que la autoridad empezó** (probado en la página: dos acciones ejecutadas tras la parada). Se necesita un fallo interno; ningún camino alcanzable por el residente | `session_record()` cruza el registro con los **hechos propios del sitio** (sus minutos comprometidos): un sitio real que comprometió y cuyo artefacto no puede describirlo se **detiene de forma pegajosa** (`ARTIFACT_ERROR`, `STOP_INTERNAL`) y su registro falla cerrado desde sus propios registros; un artefacto sano posterior no levanta la parada | `test_phase3_stop_lifecycle.py` r1 (transitorio y persistente; reapertura con sólo el registro; antes del primer compromiso sigue siendo aborto limpio) |
| **MEDIO-1** | La decisión se tomaba **una vez**, antes de procesar el Send de texto libre (que no termina en `rerun`); un clic de ECG, «Complete» o «Finish now» fusionado en esa misma pasada se ejecutaba en una sesión que acababa de detenerse (ECG 0→1 y eventos 3→6; con destino, `encounter_ended: True`). Los registros `ecg_acquisition`, `complete_encounter`, `finish_encounter`, `cancel_pending_orders` y `retrospective_explanation` no se aplicaban en el código | La pregunta se hace **de nuevo** justo después de procesar el envío previo al dibujo (antes de dibujar o atender cualquier otra cosa) y **cada mutador no reloj la vuelve a hacer en su propio manejador** | `test_phase3_stop_page.py` s17 (ECG fusionado, ambos casos), s18 (Complete fusionado con destino), tripwires t2/t3 actualizados (los siete nombres gateados) |
| **MEDIO-2** (bajo/medio) | Quitar una bandera a mitad de encuentro dejaba que la ruta del reloj siguiera en el heredado con la guarda diciendo `ACTIVE` hasta que el siguiente turno de **orden** lo notaba (4 preguntas, del minuto 2 al 10) | La guarda niega con `CONFIGURATION_CHANGED` cuando hay un sitio **real activo** y la configuración (modo de autoridad e instantánea) ya no se pide; el registro invalidado queda pegado | r2 (cabeza y página: s19 con la bandera de modo y la de instantánea) |
| BAJO-3 | Con banderas encendidas y sin afirmaciones, cada llamada de la guarda leía y parseaba **todo** el almacén (190 ms con 130 archivos) antes de filtrar por caso | `_resumed_artifact` filtra por el prefijo del nombre (`<caso>__`) antes de parsear | r4 |
| BAJO-4 | La pasada que procesa el turno que falla dibujaba una página normal sin aviso | Misma reparación que MEDIO-1 (el aviso ya sale en esa pasada) | s17 |
| BAJO-7 (parte) | `WINDOW_CLOSED` se clasificaba como `COLLAPSE_BOUNDARY`; el aviso decía «Leave this encounter» sin decir cómo | Clase propia `WINDOW_CLOSED`, `ARTIFACT_ERROR → INTERNAL_ERROR`; el aviso nombra «End this attempt without completing review» o reiniciar | r3 |
**Declarados, no reparados** (véase §14): BAJO-5 (tras la parada la presión que muestra la página es la heredada del turno que falló, no la última autoritativa: ejemplos del revisor 57m 43/26 @182 frente a 55/36 @242, 72f 64/40 @122 frente a 69/46 @212; no es peor que el límite 1); BAJO-6 (una orden sana interrumpida y recuperada por la Fase 0 revierte el estado y el registro pero no el sitio: la guarda responde `RESUMED_WITHOUT_SITE` y escribe una marca duradera espuria; falla cerrada, sólo disponibilidad);
BAJO-7 (resto): `OUT_OF_DOMAIN_WRITE → REPLAY_OR_ARTIFACT` y `PROVENANCE_CONTRADICTION → UNSUPPORTED_ACTION` son decisiones de clasificación; una versión anterior de la aplicación que vuelva a guardar el intento pierde la clave nueva (no hay forma de impedirlo desde aquí).
**Controles que se mantuvieron sin romperse (HELD):** reloj y órdenes tras cualquier fallo (pregunta, orden, examen, espera, IV, liberación de orden retenida, orden de cero minutos, envío duplicado o pendiente), refresco/reapertura/restauración con banderas encendidas y apagadas (toda combinación de sitio/registro/artefacto presente niega), registro editado sin recalcular el digesto, concesión/linaje/entorno equivocados (ningún sitio, encuentro heredado ordinario), frontera de colapso (sin compromiso ≥ 207, sin palabra terminal en página, registro ni eventos, `mental_status` heredado), **identidad byte a byte frente al HEAD con las banderas apagadas** (8 pasos de un GI: `state`, libro, eventos, Management Trace, historia, `submission_log`, texto de pantalla, etiquetas y estado de los botones sin diferencia salvo el ruido por ejecución), aislamiento de la capa (`runtime_authority_session` sólo importa `os`, `typing`, `runtime_authority` y, perezosamente, `clinical_core.legacy_adapter`; la página no lo importa).
**No probable:** una pestaña vieja todavía `ACTIVE` en memoria (necesita la base de la cuenta); familias no GI y puntuación D1–D5 (no se tocó código de ellas).

## 13 · P3-263 · Certificación integrada
Una sola certificación sobre un candidato congelado (sin editar código ni pruebas mientras corre): la suite completa del repositorio por particiones (`suite_particionada.py`, tiempo de espera por partición de 12 000 s) y `run_regressions.py`, con **una** huella del árbol de trabajo (HEAD + diferencia + archivos nuevos). **Las cifras y la huella no se escriben aquí** (un documento no puede contener la huella del árbol que lo incluye): están en el informe del ciclo. `clinical_core/` no cambió (diferencia vacía), de modo que su certificación sigue vigente sobre código equivalente; sus pruebas corren de todos modos dentro de la suite completa.

## 14 · Límites declarados (no son bloqueos del desarrollo; sí del uso con residentes)
1. **El turno que falla ya corrió en el motor heredado** antes de que el sitio lo juzgue: la parada se aplica **desde la siguiente acción**. La presión de ese turno ya es la heredada y **la página la sigue mostrando** (no está marcada como no autoritativa; el aviso no la corrige); el artefacto y el registro dicen cuál fue el último minuto y la última presión autoritativos (BAJO-5 de la revisión).
2. **El registro no tiene firma**: quien reescribe a la vez un registro menos restrictivo y recalcula su digesto no es refutable desde el registro; el artefacto y el sitio vivo siguen ganando si existen. Firmarlo exige una llave (decisión de la docencia).
3. **Registro y sitio ambos perdidos y el motor heredado avanza más allá del último compromiso**: la coincidencia duradera (caso + minuto + presiones) falla; es un borde que abre; sólo se cierra con la firma o con un guardado que lleve el artefacto.
4. **Un solo proceso de Python** (véase §10).
5. **Aviso sólo en inglés** y de desarrollo: no es un texto del residente ni del primer piloto.
6. **No hay reanudación ni retroceso**: la única resolución es salir (FD-STOP-06); `RESET_FROM_PREAUTHORITY_SNAPSHOT` y `START_NEW_ENCOUNTER` quedan como resoluciones futuras nombradas, no construidas.
7. **No se revierte** la presión comprometida (el estado autoritativo se conserva en el artefacto).
7b. **Recuperación de la Fase 0 tras una orden sana interrumpida** (BAJO-6): revierte estado y registro pero no el sitio, y la guarda detiene con `RESUMED_WITHOUT_SITE` (falla cerrada, sólo disponibilidad; escribe una marca duradera espuria).
8. **Lo que sigue bloqueado, sin cambio**: mapeo de la consciencia común al `mental_status` vivo (C5), V1 sólo de desarrollo, dos casos, semántica relativa a la llegada, concesión en el mismo proceso, almacén creciente (TD-143).

## 15 · Punto de control P3-264
Registro: `docs/revision/PHASE3_EFFECTIVE_STOP_CHECKPOINT.json` (reconstruido por `test_phase3_stop_checkpoint.py`: lo que el código puede decir se **lee del código**; los estados, el veredicto y los bloqueadores son del punto de control). **Ocho estados:** `PRESSURE_AUTHORITY_VALIDATION`, `POST_COMMIT_STOP`, `RESTART_PERSISTENCE`, `PAGE_CONTINUATION_GUARD`, `COLLAPSE_BOUNDARY_STOP`, `ARTIFACT_SESSION_CONSISTENCY`, `SINGLE_PROCESS_CONCURRENCY`, `RESIDENT_ISOLATION`.
**Veredicto único: A · `GI_PRESSURE_DEVELOPMENT_AUTHORITY_WITH_EFFECTIVE_STOP_VALIDATED`.** (Las otras opciones, no elegidas: B `AUTHORITY_VALID_BUT_CONTINUATION_STOP_INCOMPLETE`, C `SESSION_PERSISTENCE_OR_CONCURRENCY_BLOCKER`, D `AUTHORITY_RUNTIME_NEEDS_REDESIGN`.) **El veredicto A no habilita nada más** de lo que la docencia ya concedió: ninguna autoridad de consciencia, ninguna escritura en `mental_status`, ningún despliegue a residentes, ninguna autoridad de producción, el primer piloto sin cambio, V1 no promovida, ninguna regla terminal inventada, ninguna fisiología reajustada, ninguna validación clínica afirmada.
**Bloqueadores que quedan (ocho, en el registro):** el turno que falla ya corrió; el registro sin firma; el borde de registro y sitio perdidos; un solo proceso; sólo «salir» como resolución; el mapeo de consciencia al campo vivo sigue bloqueado; el aviso sólo de desarrollo en inglés; dos casos y semántica relativa a la llegada.
**Decisión siguiente (no se toma aquí):** si el experimento está listo para un **entorno piloto controlado sólo docente**. El checkpoint P3-264 **sustituye** al P3-249 únicamente en que la parada ya no es consultiva y la reanudación ya no es sólo marcada; no lo reescribe (una prueba fija que el P3-249 sigue diciendo lo que decidió entonces).
