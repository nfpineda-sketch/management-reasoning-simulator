# Fase 3 · Turno controlado por la autoridad y ancla de procedencia durable (P3-269 a P3-278) · registro (2026-11-13)

**Alcance.** Cerrar los dos bordes abiertos que dejó la parada efectiva (`docs/PHASE3_EFFECTIVE_AUTHORITY_STOP.md` §14; TD-144 §1 y §3):

* **R-FAILOPEN-1.** El turno que **provoca** un fallo de autoridad ya había corrido sobre el encuentro **real** (reloj, paciente, libro mayor de órdenes, eventos, Traza de Manejo) cuando la autoridad lo juzgaba y rechazaba: la parada empezaba en la **siguiente** operación.
* **R-FAILOPEN-2.** Un encuentro guardado que perdía a la vez su registro de sesión y su sitio, y cuyo motor heredado avanzaba más allá del último minuto autoritativo, no se reconocía como «antes autoritativo e inválido».

Sigue siendo **control del ciclo de vida del experimento de desarrollo**: no es muerte del paciente, no es terminalidad clínica, no escribe ningún campo fisiológico ni de puntuación.
**Qué NO se habilita (ni siquiera con el veredicto A):** autoridad de consciencia, mapeo de la consciencia común a `mental_status`, exposición al residente, despliegue a residentes, autoridad de producción, cambio del primer piloto congelado, semántica terminal inventada, reajuste de fisiología, puntuación nueva, generalización más allá de los dos casos de GI, ninguna afirmación de validación clínica. `COMMON_CORE_RUNTIME_AUTHORITY` **sigue `False`**; `clinical_core/` y `family_engine.py` **no se modificaron**; con las banderas de autoridad apagadas el comportamiento es idéntico (una búsqueda de clave y nada más).

## 0 · Decisión del arquitecto (2026-11-13)
No resolver R-FAILOPEN-1 **retrocediendo** el estado heredado tras mutarlo, ni **fingiendo** que el turno fallido no ocurrió, ni inventando semántica terminal del paciente. Preferir **evaluación previa a la mutación** o **copiar → simular → validar → aplicar**, de modo que un encuentro bajo autoridad nunca mute el encuentro real por un turno que luego se rechaza. Sin firma criptográfica salvo que sea imprescindible. FD-P3-213 a FD-P3-216.

## 1 · P3-269 · Auditoría del orden de ejecución (sólo lectura; qué había)
El orden real, medido en el código y con una sonda sobre la página real (no supuesto):

| Ruta | Orden **antes** | Qué mutaba el encuentro real antes de que la autoridad pudiera rechazar |
|---|---|---|
| Pregunta / tema de historia / examen (`spend_clinical_time`, tres sitios de llamada) | `add_event("you")` y `add_event` de la respuesta → `advance_clinical_time(state)` (el motor calcula sobre `deepcopy(state)` y **aplica** con `state.clear(); state.update(candidate)`) → observación de la sombra → `after_clock_moved` (el sitio juzga) → `record_information_activity` | el reloj, el paciente, dos eventos y la entrada de la traza |
| Orden de texto libre y orden guiada (`_process_encounter_submission`) | `add_event` → `open_turn` → `history.append`, `last_parse` → `execute_bundle` (el motor aplica) → observación → **`_authority.minute` (el sitio juzga y compromete)** → `order_pipeline.settle` (libro mayor) → `settle_provenance` → traza | reloj, paciente, libro mayor, eventos, historial, traza |
| Orden **retenida** liberada por el formulario guiado | `complete_pending_reasoning_fields` **consume** `pending_reasoning` y los eventos «ORDER HELD» **al dibujar**, antes de empezar el turno → el turno | la retención misma (un rechazo posterior la perdía) |
| Acción de cero minutos (p. ej. «Order urgent endoscopy.») | igual que la orden: el motor la ejecutaba y el sitio la rechazaba después (`MINUTE_ALREADY_COMMITTED`) | la orden quedaba en el estado y en el libro mayor |
| ECG (botón), cancelar pendientes, explicación retrospectiva | no mueven el reloj ni la presión; la autoridad **no los juzga** nunca | sólo su propio registro (clasificados `ENCOUNTER_MUTATING`; bloqueados al detenerse) |

**Hallazgo de diseño que condicionó todo.** `settle_provenance` documenta la decisión docente F: un minuto **comprometido no se reescribe**. Como la liquidación del libro mayor (linaje y clases no soportadas, el hueco P3-48) ocurría **después** del compromiso, un rechazo por liquidación dejaba un minuto comprometido que ya no podía retirarse. La solución no es retractar: es **liquidar antes de comprometer** (§3).

## 2 · P3-269A · Propiedad del estado (tabla clasificada y particionada contra `SESSION_FIELDS`)
Medida con una sonda que registró, en la página real con autoridad, qué claves de `st.session_state` cambia cada turno (pregunta, examen, vía IV, espera, bolo, orden no soportada). Copiar sólo el paciente **no** basta.

| Clase | Campos | Qué hace un turno con ellos |
|---|---|---|
| `TURN_OWNED` (se copian) | `state` (con el reloj), `events`, `history`, `management_trace`, `last_parse`, `order_ledger`, `rng_counter`, `pending_action`, `pending_bundle`, `pending_reasoning`, `reasoning_gate_counter`, `last_executed_action` | el turno trabaja sobre copias profundas; si se rechaza, los originales siguen siendo el encuentro |
| `OPERATIONAL` | `submission_log` | bitácora de lo que el residente escribió (escritura anticipada de la Fase 0): no se copia; el asiento se marca `blocked_by_authority_failure` |
| `EXTERNAL_ACCOUNTING` | `ai_call_ledger`, `ai_calls_spent` | gasto de llamadas pagadas que **sí** ocurrieron: restaurarlo ocultaría un costo real. Nunca se copia ni se restaura |
| `AUTHORITY_RECORD` | `phase3_authority_session` | lo escribe la autoridad; el rechazo debe quedar |
| `CLOSED_OR_REVIEW` | el resto de los campos guardados | un turno no los toca (no hay turno tras el cierre) |

Una prueba parte los campos guardados del encuentro en estas clases **sin solapes ni huecos**: un campo guardado nuevo obliga a decidir si un turno lo copia. Además de los campos, el turno cambia objetos de la capa (`phase3_authority_site`, `phase3_authority_artifact`, `phase3_shadow`) y claves de interfaz; ninguno se copia (§4).

## 3 · P3-270 · Diseño de la arquitectura mínima segura
**Patrón:** CAPTURAR → CLONAR → EJECUTAR EL TURNO SIN CAMBIOS SOBRE LA COPIA → la autoridad común JUZGA la copia → **válido:** la copia validada **es** el encuentro real; **inválido:** se descarta la copia y los objetos originales, que nada tocó, siguen siendo el encuentro.

* **Reutiliza el patrón del propio motor.** `execute_family_bundle` y `advance_clinical_time` ya ejecutan sobre `deepcopy(state)` y aplican al final. La transacción sube ese mismo patrón un nivel, alrededor del turno de la página; el motor heredado corre **igual que antes**, sobre la copia. **No hay segundo motor** y `family_engine.py` no se tocó.
* **No es un retroceso.** Los originales nunca se mutan: «descartar» no restaura ningún valor, deja de usar la copia (se prueba con identidad de objeto, no con igualdad).
* **Determinismo (P3-270B).** No se simula una vez y se vuelve a ejecutar aparte sobre el real. Lo que se compromete es **el estado validado**; no hay segunda ejecución que pueda divergir.
* **Cuándo es transaccional un turno.** Sólo si comienza con un sitio **real** (concesión), no detenido, que **ya comprometió** al menos un minuto (la sesión es `ACTIVE_AUTHORITY`). Antes del primer compromiso un fallo sigue siendo aborto limpio (`PRECOMMIT_ABORT`, FD-STOP-04): nada autoritativo se mostró, el turno heredado que corrió se mantiene. Con las banderas apagadas: una búsqueda de clave y la página corre como siempre.
* **Veredicto** (leído de los hechos del propio sitio; falla cerrada): se **aplica** si el sitio no se detuvo durante el turno, o si hizo un compromiso **durable** antes de cualquier fallo posterior; en cualquier otro caso (se detuvo, el sitio desapareció, un compromiso se retiró, no se puede leer) se **descarta**.
* **Liquidar antes de comprometer.** El libro mayor del turno ya liquidado se entrega a `AuthoritySite.minute(..., settled=...)`, que juzga linaje y clases ya liquidadas **antes** de comprometer (turno que avanza y turno de cero minutos). `settle_provenance` sigue después y sólo adjunta el linaje, como siempre. La página reordena una sola cosa: `order_pipeline.settle` pasa **antes** del bloque de autoridad (el reloj es el mismo y el compromiso sólo escribe presiones, así que lo que la liquidación lee no se mueve).
* **Un compromiso que el almacén no pudo escribir se retira** (`_withdraw_unpersisted_commit`): existió sólo en memoria durante `minute`; nunca fue durable ni se aplicó. Es el **único** registro que se retira, y por eso no reescribe historia (la decisión F habla de lo ya durable). Un compromiso **durable** nunca se toca: si falla una escritura **posterior** del mismo turno, el compromiso se mantiene, el turno se aplica y la sesión se detiene desde la siguiente operación.
* **`minutes_seen` cuenta sólo minutos alcanzados** (los comprometidos): un minuto rechazado es contrafactual y el reloj real se queda legítimamente detrás; contarlo haría que el sitio detenido de ese mismo encuentro dejara de ser «su sitio» en la siguiente corrida.

## 4 · P3-270A · Efectos laterales que no se pueden copiar
| Efecto | Dónde ocurre | Tratamiento |
|---|---|---|
| Guardado duradero del encuentro (`save_session`) | única vez, **al final** del turno | un turno rechazado desenrolla antes de llegar: nunca guarda el estado no validado; tras el descarte el envoltorio guarda los **originales** con el registro de sesión (para que una copia reabierta siga detenida) |
| Escritura anticipada de la bitácora (`submission_guard.begin`) | al empezar el turno | contiene el estado **previo**; el asiento se cierra `blocked_by_authority_failure` |
| Llamadas de IA (`normalize_clinical_turn`, `answer_history`) | antes de que la autoridad pueda opinar | gasto real: `ai_call_ledger`/`ai_calls_spent` no se copian ni se restauran |
| Artefacto de autoridad (almacén de sólo creación) | dentro de `site.minute` | es **el registro del propio sitio** de lo rechazado (nombra el minuto fallido, conserva el contrafactual heredado y marca el minuto `ABORTED`); **no** es el encuentro y debe quedar |
| Sesión de sombra (en memoria) | observó el turno intentado | no se persiste ni se muestra; se conserva como evidencia del rechazo (límite declarado, §14) |
| Aleatoriedad | `rng_counter` | campo del turno: se copia y se restaura |
| Caches / estado global | — | la capa no tiene estado mutable de módulo (certificado en P3-260) |

## 5 · P3-271 · Implementación
* `runtime_authority_turn.py` (módulo **nuevo** de la capa, importado sólo por `runtime_authority`): la tabla de propiedad, `AuthorityTurn` (contexto: clona al entrar; al salir aplica el veredicto), `AuthorityTurnDiscarded`, `begin`, `applies`, `check`. Importa sólo `copy`, `typing` y `runtime_authority`.
* `runtime_authority.py`: `AuthoritySite.minute(..., settled=)`, la verificación previa al compromiso (`settlement_contradictions`, la misma lógica que `settle_provenance`), la retracción del compromiso no durable, la escritura del ancla (§8), `minutes_seen`, y las funciones `authority_turn`, `turn_applies`, `turn_check`.
* `app.py` (sólo orquesta, no decide): `_authority_turn`, `_authority_turn_applies`, `_authority_turn_check`; los **tres** manejadores de reloj (pregunta, tema, examen) entran en `with _authority_turn(...)`; `_process_encounter_submission` pasa a ser un **envoltorio** (guarda de parada, transacción, y tras un descarte: asiento bloqueado, guardado y relectura) y el cuerpo del turno es `_process_encounter_submission_turn`; la liquidación pasa antes del compromiso; el consumo de la orden retenida por el formulario guiado se **difiere al interior del turno** (sólo cuando hay transacción aplicable; con banderas apagadas queda exactamente como estaba).
* El turno **desenrolla** en cuanto la autoridad lo rechaza (`AuthorityTurnDiscarded`, que el propio contexto traga): ninguna sentencia posterior (traza, guardado final) corre sobre una copia que se va a descartar. Cualquier otra salida (un `st.rerun`, un error) también aplica el veredicto y deja seguir la excepción original.

## 6 · P3-272 y P3-272A · Matriz «fallo antes de mutar» (página real, caso 57m; reloj en el caso 72f)
Tras **dos compromisos reales**, cada fallo se mide contra la instantánea del encuentro tomada **justo antes del turno que ejecuta** (ruta de órdenes; y ruta del reloj con pregunta y con examen). En **todos**: el encuentro (estado con su reloj, eventos, historial, traza, libro mayor, parse, retenciones, contadores) es **idéntico** al previo; el reloj real no se movió; no se comprometió ningún minuto (el artefacto nombra el rechazo como `ABORTED`); el ancla no cambió; no queda ninguna fila del libro mayor que afirme ejecución; la sesión queda `INVALID_FOR_CONTINUATION` y la **siguiente** operación está bloqueada (los mismos 5 intentos de parada efectiva: pregunta, orden, tratamiento, vía IV, examen).

| Fallo | Ruta de órdenes | Ruta del reloj (pregunta y examen) |
|---|---|---|
| acción no soportada | ✔ | — (la ruta del reloj no lleva acciones) |
| desajuste de linaje del núcleo | ✔ | — |
| fallo de validación | ✔ | ✔ |
| el replay no coincide | ✔ | ✔ |
| error interno del sitio | ✔ | ✔ |
| concesión equivocada | ✔ | ✔ |
| violación de invariante (escritura fuera del dominio) | ✔ | — |
| falla de persistencia del artefacto | ✔ (el compromiso se **retira**) | ✔ |
| fallo de **un minuto intermedio** de un intervalo largo (infusión de 60 min; minuto 1 y minuto 59) | ✔ (ninguno de los sesenta minutos llega al encuentro real) | — |
| turno de cero minutos repetido (`MINUTE_ALREADY_COMMITTED`; P3-272A) | ✔ | — |
| frontera de colapso (cuarta orden «Reassess in 60 minutes.», ambos casos) | ✔ (el reloj real queda en el minuto 180; el paciente es el del minuto 180) | — |
| contradicción de linaje que sólo la liquidación revela | ✔ **antes** del compromiso | — |
| clase liquidada que el mapeo no puede representar, en un turno de cero minutos | ✔ **antes** de registrarlo como turno del experimento | — |
| fallo de una escritura **posterior** de un compromiso ya durable | el compromiso **se mantiene**, el turno **se aplica**, la sesión se detiene desde la siguiente operación | — |
| liberación rechazada de una **orden retenida** | la retención y su aviso siguen ahí, como los dejó el residente | — |

La configuración que cambia a mitad del encuentro la detiene la guarda **antes** de que empiece el turno (cobertura de la parada efectiva, sin cambios). Antes del primer compromiso (acción no soportada como primera orden; compromiso que el almacén no puede escribir) el aborto es limpio y el turno heredado se mantiene; y con todas las banderas apagadas no hay turno, ni ancla, ni clave de autoridad.

## 7 · P3-273 · Ancla de procedencia durable (R-FAILOPEN-2)
**Pregunta:** ¿cómo prueba un encuentro guardado que ya hubo autoridad real aunque se pierdan a la vez el sitio vivo y el registro de sesión? **Respuesta:** el hecho viaja **dentro del propio paciente guardado**. Cada compromiso REAL escribe en el estado, **después** de la comprobación de dominio (no amplía ningún dominio), una clave de nivel superior fuera de `observable`, `phase3_authority_anchor`, con: caso, familia, identidad del encuentro y del experimento, concesión y su huella, instantánea, **primer** y **último** minuto autoritativo, número de compromisos y la última presión. Está sellada con un digesto.

* **Monótona (P3-273A):** sólo pasa de `NO_AUTHORITY` (ausencia) a `AUTHORITY_OCCURRED`; nunca retrocede en silencio. Avanzar exige que el minuto sea posterior al último, que el conteo coincida con el del sitio y que caso, encuentro y concesión sean los mismos; cualquier otra cosa es un `ValueError` que el sitio convierte en **rechazo del minuto** (`PROVENANCE_ANCHOR_INVALID`), nunca en un reinicio. Un sitio con compromisos cuyo estado perdió el ancla también se rechaza.
* **Falla cerrada (P3-273B):** la guarda trata el ancla como la evidencia más fuerte de que hubo autoridad. Un ancla **sin** ningún otro testigo (ni sitio, ni registro, ni artefacto) es una **parada** (`AUTHORITY_OCCURRED_BUT_ITS_PROVENANCE_IS_LOST`) y el registro de esa parada se guarda con el encuentro; un ancla que no verifica, ajena, o en desacuerdo con cualquier testigo, también detiene. No se infiere «sólo heredado».
* **Sin firma (decisión del arquitecto):** el digesto detecta corrupción y una edición a medias; **no** detiene a quien recalcula el digesto (se fija con una prueba para que nadie lo confunda con una firma). Firmar exige una llave: decisión de la docencia.
* **Efecto colateral que importa:** como el turno rechazado ya no avanza el encuentro real, el reloj real queda exactamente en el último minuto comprometido, con las presiones comprometidas: la coincidencia duradera del almacén (caso, minuto, presiones) vuelve a reconocerlo aunque se haya perdido todo lo demás.

## 8 · P3-274 y P3-274A · Estado perdido: todas las combinaciones, falla cerrada
Un encuentro reabierto **nunca** trae el sitio (no es campo guardado) ni el objeto artefacto. Sobre un encuentro cuya siguiente orden fue rechazada, y sobre uno activo sin fallo:

| Registro | Banderas | Artefacto del almacén | Reloj heredado | Resultado |
|---|---|---|---|---|
| conservado / perdido | encendidas / apagadas | presente / ausente / **corrupto** | como quedó / avanzó 25 min | **parada** en las 12 combinaciones de registro × banderas × reloj, y en las 3 del artefacto |
| perdido, sin fallo previo (activo) | apagadas y encendidas | — | avanzó 15 min | **parada** (antes: el motor heredado lo continuaba) |
| ancla manipulada o de otro encuentro; registro manipulado o en desacuerdo con el ancla | — | — | — | **parada** |
| **sin ancla**, sin registro, sin sitio, sin artefacto, banderas apagadas | — | — | — | **no reconocible** (límite declarado: no queda ninguna evidencia; pinneado por una prueba) |
| sin ancla y sin registro, banderas encendidas, almacén con el artefacto | encendidas | presente | exactamente donde quedó | **parada** (el respaldo anterior del almacén sigue funcionando) |
| sin ancla y sin registro, el motor heredado avanzó | encendidas | presente | avanzó | no reconocible por el respaldo (límite declarado; el ancla es lo que lo cubre) |

**P3-274A — sin reinicio falso a heredado:** refrescar, reabrir, cambiar la configuración o reconstruir el proceso no convierte un encuentro antes autoritativo en uno heredado normal.

## 9 · P3-275 · Página, refresco, reapertura
Pruebas con la página real (`AppTest`): turno autoritativo válido; siguiente turno rechazado; refresco; reapertura (con banderas encendidas y apagadas); sesión nueva (es un encuentro **nuevo**; el detenido queda en el registro); acción de cero minutos; pregunta; examen; espera; orden; navegación de sólo lectura. En todas, el turno fallido **no ocurrió** en el encuentro real.

## 10 · Adaptaciones declaradas de pruebas existentes (lo que protegen sigue protegido)
| Prueba | Por qué cambió |
|---|---|
| `test_runtime_authority_site::d3` | pin AST del bloque de la orden: ahora el compromiso recibe el libro liquidado, la liquidación va **antes**, y cada bloque termina con el veredicto |
| `test_runtime_shadow_evidence::u24`, `test_phase3_site_review::f5`, `test_phase3_stop_page::t1/t2` | el cuerpo del turno vive ahora en `_process_encounter_submission_turn`; el envoltorio conserva la guarda de parada |
| `test_phase3_pair_page._answer_the_gate` y el ayudante de `test_runtime_authority_streamlit_halt` | la orden retenida se consume en el turno que la ejecuta: si la autoridad lo rechaza, la retención **sigue** (sólo se admite si el sitio se detuvo) |
| `test_phase3_stop_page::s15[artifact_persistence]` | el compromiso que el almacén no pudo escribir **se retira**; antes quedaba como último estado autoritativo |
| `test_phase3_stop_concurrency::c6, c7b` | el ancla hace que el encuentro sin registro sea siempre una parada; el gemelo con llegada idéntica ahora es aborto limpio si colisiona su **primer** compromiso y parada si colisiona uno **posterior** |
| `test_phase3_stop_lifecycle::l19` | aísla el caso (sin ancla) y fija además que un ancla ajena sin sus propios testigos es procedencia perdida |
| `test_phase3_pressure_series::p2, p13, p14` | en el paso rechazado la página con autoridad queda en el último minuto autoritativo (la apagada corrió) y el ancla se enmascara como metadato declarado |
| `test_shadow_core_isolation`, `test_runtime_shadow_plumbing`, `test_runtime_shadow_evidence` | el módulo nuevo es de la capa |
| `docs/revision/PHASE3_PRESSURE_AUTHORITY_SERIES.json`, `PHASE3_PRESSURE_CHECKPOINT.json`, `PHASE3_EFFECTIVE_STOP_CHECKPOINT.json` | regenerados deliberadamente (§13) |

## 11 · Cobertura de las pruebas nuevas
`test_phase3_turn_transaction` (mecánica con un sitio simulado: ownership, veredicto, copia, descarte, contabilidad externa, desenrollado, salidas, turno no juzgado y turno huérfano), `test_phase3_provenance_anchor` (el ancla y la guarda), `test_phase3_turn_page` (la matriz de página y la recuperación), `test_phase3_turn_review` (las reparaciones de la revisión independiente, sobre la página real) y `test_phase3_turn_checkpoint` (el punto de control P3-278). Las cifras exactas y la certificación se informan fuera de este documento (un documento no puede contener la huella del árbol que lo incluye).

## 12 · P3-276 · Revisión adversarial independiente y mutantes
Revisor independiente, de sólo lectura y adversarial, sobre **su propia copia** del candidato (no sobre el árbol de trabajo: mientras corrían los mutantes un sondeo concurrente dio un resultado inválido y se adoptó la regla de no ejecutar sondas de página mientras se mutan archivos). **Cada hallazgo ALTO o MEDIO se reprodujo con una sonda propia antes de reparar** y se repitió después.

| Id | Gravedad | Qué ocurría (reproducido) | Reparación | Prueba que la fija |
|---|---|---|---|---|
| H1 | ALTO | Con `MRS_PHASE3_SHADOW` quitada del proceso, un turno de reloj que el sitio **nunca vio** se aplicaba: el reloj real pasó de 7 a 9, nada comprometido, nada registrado, la sesión seguía (`allowed = True`) | Dos capas. (1) La guarda exige también la sombra (`_configuration_holds`). (2) El veredicto del turno: si el reloj de la **copia** se movió y el sitio **no registró nada** (ni minuto, ni turno quieto, ni rechazo), el turno no se aplica y la sesión se detiene (`AUTHORITY_TURN_NOT_JUDGED`, clase `STOP_INTERNAL`); una salida por excepción sólo descarta, sin detener | `test_u7c` a `u7f`, `test_v1`, `test_v2` |
| M1 | MEDIO | Con el ancla **borrada** y el sitio, el registro y el artefacto vivos, la guarda permitía continuar | Sin ancla y con alguna afirmación que dice que la autoridad comenzó ⇒ parada de procedencia (`AUTHORITY_OCCURRED_BUT_ITS_PROVENANCE_IS_LOST`), registrada para una copia reabierta | `test_v3`, `test_v3b` (el otro lado: sin compromiso previo no hay parada) |
| M2 | MEDIO | Un turno de cero minutos que el almacén **no pudo escribir** quedaba listado en el artefacto (`no_advance_turns` 0→1) aunque el encuentro lo descartaba | Marca `_unpersisted_quiet`: se retira de la lista si la escritura falla y el rechazo se registra como el minuto fallido de ese turno; un turno quieto **ya durable** nunca se retira (decisión F) | `test_v4`, `test_v4b`, `test_v4c` |
| L1 | BAJO | El docstring de la capa afirmaba que ninguna escritura durable ocurre dentro del alcance | Corregido: sólo el turno **juzgado** no escribe antes del veredicto | lectura |
| L2 | BAJO | Un turno que quedó abierto por una corrida muerta hacía que todo turno posterior corriera sin transacción | `reset_stale` cierra el turno huérfano, con su propio veredicto, al inicio de la corrida siguiente; trampa estática de orden | `test_u11`, `test_u11b`, `test_v6`, `test_v6b` |
| L3 | BAJO | Dos aserciones de página eran vacías (una cláusula `or` siempre verdadera) | Sustituidas por comparaciones del libro mayor contra la instantánea previa al turno | `test_t2`, `test_t10` |

Rutas que la revisión encontró **sin prueba de página propia** y que ahora la tienen: el tema de la historia (`test_v5`), el turno de reloj que el sitio no vio (`test_v2`), el ancla borrada con sitio vivo (`test_v3`), el turno quieto rechazado bajo fallo de persistencia (`test_v4`), el turno quieto ya durable cuando falla una escritura posterior (`test_v4c`) y el turno huérfano (`test_v6`).

**Mutantes (por texto, uno a la vez, restauración byte a byte verificada por hash tras cada uno):** 65 distintos (45 del turno, el ancla y la página, **relanzados sobre el código ya reparado**; y 20 de las reparaciones). **61 muertos y 4 equivalentes declarados:** `P1`, `P1b` y `P2` (tres puntos de desenrollado redundantes: el cierre del propio contexto aplica el mismo veredicto y la misma parada) y `L2b` (un objeto que no es un turno llega a `_apply`, que no existe, y la rama de excepción lo descarta igual). El mutante `T15` dejó de aplicarse porque su línea cambió con H1 y se reescribió sobre la línea nueva (muerto).

## 13 · P3-277 · Certificación y registros regenerados
**Registros regenerados deliberadamente** (cada uno por su interruptor, una vez, con el diff revisado a mano): la serie de manejo (`MRS_WRITE_PRESSURE_SERIES=1`) cambia **sólo 4 de 26 filas y sólo en `pressure_steps_on_off`** (las que terminan en un rechazo: el paso rechazado deja de mostrar la presión heredada del turno que falló —p. ej. 56/36 en el minuto 240— y muestra la última presión autoritativa —43/27 en el 180—; el lado «autoridad apagada» no cambia; el resumen no cambia: 84 minutos comprometidos, 4 detenciones, todo verificado y reproducible); el punto de control P3-249 (`MRS_WRITE_PRESSURE_CHECKPOINT=1`) y el de la parada efectiva (`MRS_WRITE_STOP_CHECKPOINT=1`) cambian sólo por el digesto fijado de esa serie y, el segundo, por la nueva clase de parada `AUTHORITY_PROVENANCE`; el punto de control P3-278 es nuevo (`MRS_WRITE_TURN_CHECKPOINT=1`).

**Certificación:** una sola, sobre una huella única del candidato congelado (suite completa particionada + `run_regressions.py` + guardas de congelamiento del lector, de V3, de los baselines, del primer piloto y de la Fase 2), sin editar nada mientras corre y verificando que la huella final es la inicial. Un documento no puede contener la huella del árbol que lo incluye: **las cifras (huella, pruebas aprobadas, omitidas, fallidas, regresiones) se informan en el informe del ciclo**, no aquí.

## 14 · Límites declarados (no bloquean el desarrollo; sí el uso con residentes)
* **Registro y ancla sin firma:** quien recalcula el digesto no es refutable. Firmar exige una llave.
* **Sin ninguna evidencia (ni ancla, ni registro, ni sitio, ni artefacto alcanzable):** un encuentro reconstruido desde cero no es reconocible.
* **La sesión de sombra** conserva en memoria la observación del turno rechazado (no se persiste ni se muestra; sirve de evidencia del rechazo).
* **ECG, cancelar pendientes y explicación retrospectiva** no los juzga la autoridad (no mueven reloj ni presión) y no son transaccionales; se bloquean al detenerse.
* **Un solo proceso de Python**; resoluciones del operador: sólo salir; aviso en inglés de desarrollo; dos casos de GI, sólo desarrollo; la consciencia común sigue sin mapearse.

## 15 · Punto de control P3-278
Registro: `docs/revision/PHASE3_TURN_CHECKPOINT.json` (lo que dice el código se **lee del código**; los ocho estados, el veredicto, las confirmaciones y los bloqueos son la decisión del punto de control; la revisión y los mutantes son cifras **informadas**). Reemplaza **sólo** dos bloqueos del punto de control P3-264 (el turno que falla ya había corrido; el encuentro sin registro ni sitio con el motor heredado avanzado); no reescribe ese registro.

| Estado | Resultado |
|---|---|
| `FAILED_TURN_MUTATION_PREVENTION` | tras el primer compromiso real un turno rechazado no ocurre en el encuentro real (copiar, ejecutar, juzgar, aplicar o descartar); un turno que nadie juzgó y movió el reloj tampoco se aplica; antes del primer compromiso el turno heredado se mantiene (FD-STOP-04) |
| `AUTHORITY_PROVENANCE_DURABILITY` | cada compromiso real escribe un ancla monótona sellada con digesto dentro del paciente; sin firma (límite declarado) |
| `RESTART_FAIL_CLOSED` | refresco, reapertura, sesión nueva, banderas quitadas, y toda combinación de registro, sitio y artefacto perdidos con el reloj heredado avanzado: parada; ancla borrada con una afirmación viva: parada |
| `POST_COMMIT_STOP` | sin cambios, y ahora el propio turno que falla tampoco llega al encuentro real |
| `PRESSURE_AUTHORITY` | sin cambios (SBP, DBP, MAP derivada; dos casos de GI; concesión explícita, décima condición) |
| `PAGE_RUNTIME` | toda ruta que mueve el reloj corre dentro de un turno (trampa estática); un turno huérfano se cierra al inicio de la corrida; ECG, cancelar pendientes y explicación no se juzgan y se bloquean tras una parada |
| `RESIDENT_ISOLATION` | con las banderas apagadas: sin turno, sin ancla, sin clave de autoridad; sin texto clínico visible al residente; primer piloto y otras familias intactos; no listo para residentes |
| `SINGLE_PROCESS_DEVELOPMENT_SAFETY` | suficiente para desarrollo en un solo proceso; varios procesos comparten sólo el almacén durable |

**Veredicto único: A · `GI_PRESSURE_AUTHORITY_READY_FOR_CONTROLLED_FACULTY_ENVIRONMENT_REVIEW`.** Significa que el experimento es **elegible para que la docencia revise** un entorno controlado sólo para docentes. **No** inicia un piloto docente, **no** lo deja listo para residentes y **no** concede autoridad de consciencia, escritura en `mental_status`, uso en producción, cambio del primer piloto ni aprobación de V1 para autoridad; esa revisión no se toma aquí. El veredicto se sostiene sólo si la certificación única pasa sobre el candidato congelado; el informe del ciclo lo confirma o lo corrige.

**Bloqueos que subsisten (cinco; ninguno impide el desarrollo, los primeros impiden el uso con residentes):** registro y ancla sin firma; encuentro reconstruido sin ancla, registro, sitio ni artefacto alcanzable; ECG / cancelar pendientes / explicación sin juicio ni transacción; la sesión de sombra conserva en memoria la observación del turno rechazado; un solo proceso, una sola resolución del operador, aviso en inglés de desarrollo, dos casos de GI, consciencia común sin mapear y V1 sólo para desarrollo.
