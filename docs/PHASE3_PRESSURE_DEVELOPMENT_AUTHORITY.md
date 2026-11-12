# Fase 3 · Primer experimento real de autoridad de desarrollo: presión de GI + superposición de consciencia candidata (P3-238 a P3-249) · registro (2026-11-12)

**Alcance.** Cruzar la última frontera técnica, de `WOULD_COMMIT` a un **compromiso real de presión de desarrollo**, en un experimento acotado de GI, y correr al mismo tiempo la consciencia común como **superposición candidata
no autoritativa**. Se construyó la concesión explícita, se activó, se probó en la **página real** con los dos casos y trece escenarios de manejo, se midieron los fallos tras el primer compromiso, la frontera de colapso, el
artefacto y su replay, y el aislamiento contra la corrida sin autoridad; un revisor independiente atacó el resultado.
**Qué NO se habilita (ni siquiera con el veredicto A):** autoridad de consciencia, escritura de la consciencia común en `mental_status`, exposición al residente, aprobación de V1 para autoridad, despliegue a residentes,
modificación del primer piloto congelado, autoridad de producción, semántica terminal inventada, reajuste de fisiología, consciencia por opioides, ninguna afirmación de validación clínica.
`COMMON_CORE_RUNTIME_AUTHORITY` **sigue `False`** (la concesión no lo cambia ni lo lee); `app.py`, `family_engine.py` y `clinical_core/` **no se modificaron**.

## 0 · Decisiones de la docencia (2026-11-12; FD-AUTH-23 a FD-AUTH-31; FD-P3-203)
| Decisión | Contenido |
|---|---|
| FD-AUTH-23 · C1-A | `ACCEPT_WITH_LIMITATION`: las trayectorias de consciencia común de GI **previas al colapso** son educativamente defendibles **para desarrollo**; **no** se recalibran F ni los umbrales a partir de las diferencias con el heredado; la divergencia **posterior** al colapso queda **excluida** de la aprobación. |
| FD-AUTH-24 · C1-B | `YES_WITH_LIMITATION`: la semántica relativa a la llegada sigue aceptada para GI en desarrollo (el umbral absoluto heredado de PAS y la fisiología de entrega relativa responden preguntas distintas); los dos casos bastan para desarrollo, **no** para generalizar a una población ni a otras familias. |
| FD-AUTH-25 · C1-C | `YES_WITH_LIMITATION`: las categorías de desarrollo (sin deterioro observable material, SOMNOLENT, OBTUNDED, UNRESPONSIVE) se aceptan **sólo para pruebas de desarrollo**; no son validación clínica, equivalentes de GCS ni umbrales de producción. |
| FD-AUTH-26 · C5 | `YES_BUT_NOT_RESIDENT_VISIBLE`: `UNRESPONSIVE_WITH_PULSE` es un estado fisiológico común válido; **no** se escribe en el `mental_status` vivo, que sigue siendo del heredado. |
| FD-AUTH-27 | Estado conceptual `CONSCIOUSNESS_FACULTY_READINESS = READY_FOR_DEVELOPMENT_AUTHORITY_EXPERIMENT_WITH_LIVE_MENTAL_STATUS_STILL_BLOCKED`: la fisiología ya no es el bloqueador; el mapeo al campo vivo sigue bloqueado por los lectores nombrados. |
| FD-AUTH-28 | Se autoriza el **primer experimento real de autoridad de desarrollo de GI sólo para PRESIÓN** (`sbp`, `dbp`, `map` derivada), en `gi_bleed_57m` y `gi_bleed_72f`, con `gi_pressure_committed` y el linaje común certificado activo. |
| FD-AUTH-29 | `GI_DEVELOPMENT_SNAPSHOT_V1` sigue `RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS`: no se promueve ni se usa como calibración de presión. |
| FD-AUTH-30 | La consciencia común corre **junto** a la presión como superposición candidata (V1 exacta), `FACULTY_ACCEPTED_FOR_DEVELOPMENT_COMPARISON`: ni autoridad ni visible al residente. |
| FD-AUTH-31 | Prohibido en el ciclo: lo enumerado en el alcance de arriba. |

Registro: `docs/revision/PHASE3_PRESSURE_AUTHORITY_DECISIONS.json` (reconstruido por `test_phase3_pressure_decisions.py`). El paquete de evidencia que la docencia leyó se conserva **sin cambios** en
`docs/revision/PHASE3_FACULTY_CONSCIOUSNESS_DIVERGENCE_PACKET.md` (copia byte a byte, SHA-256 fijado) y el registro P3-200 conserva sus preguntas **sin responder** (`faculty_answers` nulas, SHA-256 fijado): las respuestas se
agregan como decisiones, no se escriben en la evidencia anterior.

## 1 · P3-239 · La concesión `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1`
`runtime_pressure_grant.py` (módulo de la capa; sólo importa `hashlib`, `json`, `types` y `typing`, y no lee nada del entorno, de un archivo ni del llamador). Es **datos**, no un interruptor.

| Campo | Valor |
|---|---|
| identidad | `kind = FACULTY_GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT`, `grant_id = GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1`, versión 1, estado `ACTIVE_FOR_DEVELOPMENT_EXPERIMENT`, propósito `DEVELOPMENT_AUTHORITY_EXPERIMENT_ONLY` |
| modo | `PRESSURE_ONLY` |
| dominio | exactamente `sbp`, `dbp`, `map` |
| **dominios excluidos (239A, explícitos, no por omisión)** | `consciousness`, `mental_status`, `collapse`, `terminal`, `pulse`, `oxygenation`, `lactate`, `hb` (disjuntos del dominio) |
| casos | exactamente `gi_bleed_57m` y `gi_bleed_72f` (familia `gi_bleed`); entorno `development` únicamente (más estrecho que la compuerta) |
| instantánea de presión | `gi_pressure_committed` + el digesto fijado de sus valores (`c4fb416f…`) |
| linaje | `PHASE2_AMENDMENT_2` + su digesto (`a0af7d08…`) |
| ventana | 240 minutos (el límite predefinido, FD-AUTH-07) |
| frontera de colapso | `ESTABLISHED`, no `IMPENDING`; **precompromiso en cada minuto del intervalo**; falla cerrada; no es estado terminal ni muerte; sin texto para el residente |
| política de fallo | antes del primer compromiso: `EXPERIMENT_HALTED` y el encuentro heredado intacto; **después**: `INVALID_FOR_CONTINUATION`; **sin** retorno silencioso al motor heredado; no es muerte del paciente |
| superposición | V1 (`RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS`), `FACULTY_ACCEPTED_FOR_DEVELOPMENT_COMPARISON`, `CANDIDATE_OVERLAY_NONAUTHORITATIVE`; sin autoridad, no visible, no escribe `mental_status`, no es calibración de presión |
| decisión | `FD-P3-203 (FD-AUTH-23 a FD-AUTH-31)`, rol emisor `faculty`, 2026-11-12 |
| **huella (239B)** | `3c29c2b9eb070ea1728bea2b17fd4484ff42c5105070c9402b17e73b29c3c136`, **fijada en el archivo**: si cambia un solo byte del cuerpo, el módulo **no se importa** (`_guard_the_grant`); el cuerpo es de sólo lectura anidado (`MappingProxyType` y tuplas); ampliar el dominio exige una **versión nueva** de la concesión |

`grant_problems` nombra **cada** rechazo (35 falsificaciones parametrizadas, también con la huella recalculada por el falsificador: sólo la huella fijada lo detiene); un fixture de prueba (`TEST_ONLY_PRESSURE_GRANT_FIXTURE`) no es cargable.

## 2 · P3-240 · Activación: la décima condición de la compuerta
`runtime_authority.gate` evalúa ahora **diez** condiciones; la décima, `explicit_development_grant`, le pregunta a `runtime_pressure_grant.permits` si una concesión **registrada** autoriza exactamente este caso, entorno, instantánea,
familia, dominio y linaje. Como `AuthorityTransaction.commit` **vuelve a evaluar la compuerta**, la concesión se verifica **en cada compromiso**. Lo que **no** activa nada, probado: una bandera sola; `COMMON_CORE_RUNTIME_AUTHORITY = True`
(la compuerta ni la nombra); la concesión sola (sin las banderas, `open_site` devuelve `None`); las banderas sin concesión (registro vacío: la décima es la **única** condición que falla); el entorno `faculty`; el nombre de V1 como
instantánea; un caso fuera de la lista (`family_and_case` y la concesión fallan antes del primer compromiso); un linaje distinto.
**`COMMON_CORE_RUNTIME_AUTHORITY` significa lo mismo que antes:** el motor heredado es la autoridad por omisión; el experimento es un sitio por encuentro, que se abre sólo en la llegada, con las banderas de desarrollo y la concesión.
`open_site` adjunta la concesión al sitio sólo si autoriza **esta** corrida, y **no abre** un sitio para el punto real registrado sin ella.
**240A:** con la concesión activa la consciencia común sigue siendo superposición; el `mental_status` heredado manda.

## 3 · P3-241 · La página real, y el primer bloqueador de ejecución
`AppTest` con la configuración de desarrollo autorizada, el punto aprobado **real** y la concesión **real** (sin inyectar nada). El primer compromiso real: una pregunta de 2 minutos en el 57m comprometió **87/54** frente a **88/54**
del heredado (la página muestra lo comprometido). **241A — probado que lo escribió la autoridad común:** en cada paso comprometido la página tiene el candidato común registrado (con la forma del heredado), la corrida APAGADA muestra
el valor heredado que el sitio registró como contrafactual, y existen 96 pasos donde los dos difieren; sin la concesión (registro vacío) con todas las banderas, la página muestra la presión heredada.
**Hallazgo (la primera corrida real lo encontró; reparado y probado).** Tras un compromiso real en el minuto *m*, un turno que **no mueve el reloj** (una vía IV, una orden duplicada) hace que el motor refresque su observable y
**devuelva en silencio la presión heredada del minuto *m* sobre la comprometida**, y el sitio lo leía como un movimiento del paciente y se detenía con `MINUTE_ALREADY_COMMITTED`. El sitio **reafirma** ahora la presión que ese minuto
ya comprometió (`_reassertion`): sólo con concesión, sólo para un minuto comprometido y sólo cuando el refresco del motor **es** el contrafactual heredado que ese minuto registró; escribe el candidato ya escrito (misma forma, MAP derivado
como lo deriva la pantalla), no es un segundo compromiso ni un valor nuevo, y se verifica que no toque nada fuera del dominio. Antes de cualquier compromiso la excepción certificada del turno sin avance no cambia.

## 4 · P3-242 · Serie de manejo real (2 casos × 13 escenarios, autoridad encendida y apagada)
Escenarios: sin tratar, tratamiento temprano, tardío, sólo fluidos, sólo sangre, deterioro grave, recuperación, rescate tardío, vía IV, acción no soportada, infusión larga (60 min + reevaluación de 60 min en **un** turno), tiempo de
pregunta y tiempo de examen. Registro: `docs/revision/PHASE3_PRESSURE_AUTHORITY_SERIES.json` (reconstruido por `test_phase3_pressure_series.py`).
| Escenario | Pasos | Minutos comprometidos (por caso) | Último compromiso | Estado | Pasos con presión común ≠ heredada (57m / 72f) | Turnos reafirmados | Palabras comunes de la superposición |
|---|---|---|---|---|---|---|---|
| `untreated` | 5 | 3 | 180 | HALTED · COLLAPSE_BOUNDARY_REACHED | 3 / 3 | 0 | Alert, Drowsy, Obtunded, Unresponsive |
| `early_treatment` | 4 | 3 | 30 | ACTIVE | 4 / 4 | 0 | Alert |
| `delayed_treatment` | 6 | 5 | 150 | ACTIVE | 6 / 6 | 1 | Alert, Drowsy |
| `fluid_only` | 4 | 3 | 30 | ACTIVE | 3 / 3 | 0 | Alert |
| `blood_only` | 3 | 2 | 25 | ACTIVE | 2 / 2 | 0 | Alert |
| `severe_deterioration` | 5 | 5 | 205 | ACTIVE | 5 / 5 | 0 | Alert, Drowsy, Obtunded, Unresponsive |
| `recovery` | 6 | 5 | 160 | ACTIVE | 6 / 6 | 1 | Alert, Drowsy |
| `late_rescue` | 7 | 6 | 205 | ACTIVE | 7 / 7 | 1 | Alert, Drowsy, Obtunded, Unresponsive |
| `iv_line` | 3 | 1 | 2 | ACTIVE | 3 / 3 | 1 | Alert |
| `unsupported_action` | 3 | 1 | 2 | HALTED · UNSUPPORTED_AUTHORITY_ACTION | 1 / 1 | 0 | Alert |
| `long_infusion` | 3 | 2 | 70 | ACTIVE | 2 / 2 | 0 | Alert |
| `question_time` | 3 | 3 | 6 | ACTIVE | 3 / 3 | 0 | Alert |
| `exam_time` | 3 | 3 | 6 | ACTIVE | 3 / 3 | 0 | Alert |

Totales: **26 corridas, 84 minutos comprometidos, estados {'ACTIVE': 22, 'HALTED': 4}, paradas {'COLLAPSE_BOUNDARY_REACHED': 2, 'UNSUPPORTED_AUTHORITY_ACTION': 2}**, 26/26 artefactos verificados (`complete`) y 26/26 con replay exacto (candidato, validación, presión comprometida, digesto, superposición y razón de parada); **26/26 corridas tienen al menos un paso donde la presión común difiere de la heredada (96 de 140 pasos)**; el `mental_status` heredado es idéntico con la autoridad apagada y encendida en los 140 pasos.
**242A:** en cada minuto comprometido, SBP/DBP/MAP = el candidato común registrado, el **único** campo movido es la presión (`moved_fields ⊆ {sbp, dbp, map}`), y todo lo demás sigue del heredado.
**242B — `VALIDATED_ATOMIC_INTERVAL`:** la infusión larga es **un** intervalo de 60 minutos con una fila de superposición por minuto y **un** compromiso final; con una falla inyectada en el minuto 1, 20 o 59 del intervalo (ver §6) se aborta
**todo** el intervalo, nada se compromete y el registro nombra el minuto; ningún minuto fallido queda oculto.

## 5 · P3-243 · La consciencia común, al lado
`ConsciousnessOverlay` (en `runtime_authority_pair.py`) es la corrida ligada a V1 **junto** a la presión: por cada minuto que el experimento cruza registra el estado heredado (`mental_status`), la categoría y la palabra comunes, F, la
entrega y la perfusión relativas, la carga y el estado de colapso y el pulso; el digesto del estado que se le entrega se verifica antes y después. **Etiqueta `FACULTY_ACCEPTED_FOR_DEVELOPMENT_COMPARISON`** (no autoridad, no visible al residente).
**Pruebas de que no escribe `mental_status` (y fugas):** en los 26 encuentros el `mental_status` es idéntico con la autoridad apagada y encendida en **cada** paso; el estado preparado por el compromiso no contiene la clave de superposición ni
ninguna ficha de la superposición; ningún módulo fuera de la capa nombra la superposición ni lee el artefacto (por lo que la puntuación, los payloads de IA y docentes no pueden verla); la sesión **entera** tras cerrar es igual salvo los valores de presión.
La superposición es también **la única lectura de la frontera**: el sitio de presión no tenía ninguna.

## 6 · P3-244 · Fallos tras el primer compromiso real, y qué hace la página
Cada prueba juega la página real, deja que ocurra el primer compromiso, inyecta **un** fallo y comprueba (`test_phase3_pressure_failures.py`): acción no soportada (dos casos), linaje distinto (la compuerta, en el compromiso), artefacto que no reproduce el
minuto, fallo de validación en el minuto final, **fallo de un minuto interno de una infusión larga (minutos 1, 20 y 59)**, error interno del sitio. En todos: el experimento queda **`INVALID_FOR_CONTINUATION`**
(`authority_began`, `mixed_trajectory`, `experiment_outcome`), el turno fallido **no comprometió nada** y tiene su registro de reversión, ningún minuto posterior vuelve a ser autoritativo (los turnos siguientes dejan `AUTHORITY_HALTED_AFTER_A_HARD_FAILURE`),
el artefacto verifica y su razón de parada se **re-deriva** del artefacto cuando es derivable. Una falla **antes** del primer compromiso deja el encuentro heredado **exactamente** como si el experimento no se hubiera pedido (`EXPERIMENT_HALTED`).
**244A — qué hace la página:** el motor heredado sigue corriendo el encuentro (es lo único que puede), **el residente no ve nada del experimento** (ni una palabra, ni una acción distinta) y desde el minuto fallido la presión de la página es la
heredada; **eso no es silencioso**: el artefacto declara `mixed_trajectory`, `experiment_outcome = INVALID_FOR_CONTINUATION` y `post_commit_policy.what_the_page_does`, y la lectura de estado de la facultad (`authority_status`) lo dice. Es **terminación del
experimento, no muerte del paciente**: no hay estado terminal, el pulso no cambia y ninguna palabra terminal llega al residente.

## 7 · P3-245 · La frontera de colapso y la ventana
El guardia `_boundary_guard` corre **antes** de cualquier compromiso, sobre **cada** minuto del intervalo: un minuto pasado la ventana (240), uno que la superposición no puede mostrar, una corrida de la superposición que no es la de la presión, o uno en
colapso `ESTABLISHED`, **no se compromete** (falla cerrada; sin superposición no hay frontera verificable y no hay compromiso). `IMPENDING` **no** es parada. **245A:** sin tratar, el 57m compromete hasta el minuto **180**, el primer minuto rechazado es el
**240** (el intervalo 181–240 contiene el minuto **207**, el primero en `ESTABLISHED`), la razón es `COLLAPSE_BOUNDARY_REACHED`, y el estado común en el rechazo (F, entrega relativa, colapso, palabra común `Unresponsive` frente a la heredada) queda en el artefacto; el
residente conserva la palabra heredada y el pulso. El replay re-deriva la frontera del artefacto.
**Cambio declarado de la serie certificada:** la serie P3-48 (34 escenarios) se reproduce **exactamente** (26 completos, 8 detenidos, 66 minutos comprometidos, 78 registros, huella `41ad6975…`) con el guardia neutralizado; **con** el guardia sólo cambian los dos
`terminal_deterioration` (8 compromisos pasan a 6, último minuto 180; se detienen por `COLLAPSE_BOUNDARY_REACHED`): 24 completos, 10 detenidos, 62 comprometidos y la huella nueva `16251731…`; los otros 32 escenarios conservan sus filas **bit a bit**.

## 8 · P3-246 · Artefacto y replay
Un artefacto de un experimento bajo la concesión es del tipo `phase3_authority_experiment` con la etiqueta **`REAL_DEVELOPMENT_PRESSURE_AUTHORITY`** y lleva: la concesión (identidad, huella, dominio, dominios excluidos, casos, ventana), el modo `PRESSURE_ONLY`, el caso, la
instantánea y el linaje, por minuto el **estado heredado capturado** (contrafactual de presión, forma, digesto del observable previo y los campos heredados **no** autoritativos), el candidato común, la validación (fallos, intervalo), la presión **efectivamente comprometida**, el resultado de la
transacción y su reversión, la **superposición de consciencia** (con la entrada inmutable de la corrida ligada a V1) y la política de frontera y de fallo.
**246A — replay desde el artefacto solo:** reconstruye el candidato de presión, la validación, la presión comprometida y el digesto (como antes), **más** las filas de la superposición y cada lectura de frontera (re-derivadas de la corrida de V1) y la **razón de parada**
cuando es derivable. Un candidato, una presión, una fila de superposición, una frontera, una huella de concesión, un modo, un dominio, una lista de exclusiones o una etiqueta alterados (con el digesto recalculado) **no** se aceptan.
**246B — real frente a dormido y a histórico:** `artifact_class` distingue `REAL_DEVELOPMENT_PRESSURE_AUTHORITY` (etiqueta + concesión + superposición), `HISTORICAL_PRESSURE_EXPERIMENT` (el mismo tipo, sin ellos: el de las series anteriores), `DORMANT_AUTHORITY_EVALUATION` (otro tipo, que el almacén de presión rechaza) e `INCONSISTENT_ARTIFACT` (el contenido real con otra etiqueta, o la etiqueta real sin contenido: se decide por el contenido y no sólo por la etiqueta, §10 M5);
el listado del almacén lleva la clase.

## 9 · P3-247 · Aislamiento: autoridad apagada frente a encendida
En cada paso de los 26 encuentros: mismo minuto, mismos botones, mismos eventos, mismo libro de órdenes, mismo observable salvo `sbp`, `dbp` y `map`, y el texto visible igual una vez enmascarados los valores de presión; tras cerrar los encuentros cerrados,
**la sesión entera** (puntuación, traza, terminación, disposición, revisión) es igual salvo los valores de presión. El primer piloto y la producción **no** pueden usar la concesión (banderas de piloto, marcadores del congelamiento del piloto, entorno `production`: la compuerta rechaza), y `app.py` no importa la concesión.
**247A — la consciencia no se filtra a** `mental_status`, puntuación, payloads de IA, retención de sugerencias docentes, bifurcación del escenario, alta, terminación ni elegibilidad de acciones: el estado nunca la contiene y ningún lector fuera de la capa puede leer el artefacto.

## 10 · P3-248 · Revisión adversarial independiente
Revisión de **sólo lectura** (un agente independiente; ninguna edición del repositorio; sondas propias en el directorio de trabajo), 24 ataques, contra el árbol de trabajo antes de las reparaciones. **0 altos, 5 medios, 8 bajos.** El núcleo de seguridad aguantó: la concesión (falsificada, con huella coherente, intercambiada en el registro, vacía), la compuerta de diez condiciones, el compromiso atómico (nada parcial; un fallo dentro de la escritura o después de ella no instala el estado), la frontera de colapso (el intervalo 181 a 240 se detiene en el 207 con 0 comprometidos; `ESTABLISHED` en el minuto 1 se detiene; `IMPENDING` no), la ventana, la infusión larga (la primera fila interna ausente o inválida aborta todo el intervalo) y `_reassertion` (80 secuencias aleatorias de órdenes y tiempo, sin halts ni retornos silenciosos; 16 secuencias con y sin sitio, estado idéntico salvo `sbp`/`dbp`/`map`; 14 secuencias de esperas, eventos e interrupciones, iguales).

| # | Ataque | Veredicto |
|---|---|---|
| 1 a 7 | familia, caso fuera de lista, consciencia en la concesión, V1 confundida, concesión falsificada, bandera sola, compromiso antes de la concesión | **aguantan** (31 variantes de caso: sólo los dos GI abren sitio) |
| 8, 9, 20 | compromiso parcial, minuto interno fallido, infusión que valida sólo el último minuto | **aguantan** |
| 10 | retorno silencioso al heredado tras el primer compromiso | **hallazgo M1** (reanudar) y L2 (datos viejos tras el halt); el resto aguanta |
| 11 | frontera `ESTABLISHED` | la guarda **aguanta**; hallazgo M4 (el verificador no veía una regresión de la guarda) |
| 12 | acción no soportada (incluida la sólo visible en el libro mayor) | se detiene; hallazgo M2 (su replay daba falso negativo) |
| 13, 19 | la vía IV detiene por error; la página esquiva la autoridad fuera del turno de órdenes | **aguantan** (las órdenes retenidas detienen el experimento en el turno que las retiene) |
| 14 a 16, 18, 23, 24 | fuga de la consciencia a `mental_status`, puntuación, payloads; etiqueta o modo equivocados; primer piloto; cambios visibles | **aguantan** en lo probado (estático y estado/libro/eventos); L5 (debilidades de pruebas) y L7 (acoplamiento latente) |
| 17, 22 | replay que no reproduce, artefacto adulterado, otra concesión | los compromisos reales reproducen (80 de 80); **hallazgos M2, M3, M4, M5** (huecos del replay y de la verificación) y L6 |
| 21 | linaje equivocado (al abrir, al comprometer, a mitad del encuentro) | **aguanta** |

**Medios (cada uno reproducido con una sonda propia del autor ANTES de repararlo, y reparado):**
* **M1 · reanudar tras un compromiso.** El estado guardado lleva las presiones comprometidas pero no el sitio; el registro duradero quedaba `ACTIVE` para siempre y el estado mostraba `REFUSED` sin trayectoria mixta, contra el reclamo de que no hay retorno silencioso. **Reparación:** al encontrar una página con la bandera encendida, `sim_time > 0` y sin sitio, la capa busca en el almacén el experimento `ACTIVE` cuyo último minuto comprometido es este estado (mismo caso, mismo minuto, mismas presiones comprometidas) y escribe un registro duradero `ENCOUNTER_RESUMED_WITHOUT_ITS_AUTHORITY_SITE` (`HALTED`, `INVALID_FOR_CONTINUATION`, trayectoria mixta, `resumed_at_minute`); la sesión lleva ese artefacto y `authority_status` lo dice. **No** previene la reanudación (eso es de la página, que no se toca): la **marca**. Se declara en TD-143.
* **M2 · replay de un halt real tras un compromiso.** La contradicción de procedencia se registra en el minuto comprometido (o en el turno sin avance), no en el registro fresco del fallo, y el replay buscaba sólo en este: `verify.complete` y minutos correctos, pero `reproduces: False`. **Reparación:** la evidencia se busca donde vive.
* **M3 · un halt relabelado se aceptaba con el digesto recalculado.** Una rama `... or kind in reason` era una tautología (`kind` es el prefijo de `reason`) y las razones no derivables devolvían `reproduces: True` sin decir que no se re-derivaban. **Reparación:** el minuto abortado debe nombrar **la misma** razón que el artefacto; la rama no soportada exige una clase no soportada registrada; la ventana se compara con la constante **fijada**, no con la copia del artefacto; una razón no derivable (error interno, cambio de configuración, reanudación) se reporta `rederived: False` en `halt_reason_replay`, en `halt_reason_rederived` y en `verdict_notes` (el texto de `verdict` es el certificado y no cambia). **Límite declarado:** un falsificador que reescribe a la vez la razón y el fallo de un minuto con razón no derivable no se puede refutar desde el artefacto (el digesto no tiene firma).
* **M4 · nadie contrastaba «comprometido» con «frontera despejada y dentro de la ventana».** Con una regresión de la guarda simulada, el minuto 240 (con el 207 establecido) y el 300 se comprometían y el artefacto verificaba y reproducía. **Reparación:** `real_artifact_problems` exige, sobre cada minuto comprometido, `collapse_boundary.clear`, ninguna frontera establecida, ningún minuto no mostrado, superposición disponible y despejada y el minuto dentro de la ventana **fijada**; `replay_overlay_artifact` re-deriva el veredicto `clear` de cada turno (frontera, un solo curso, sin fallos), su digesto y el digesto del conjunto.
* **M5 · la etiqueta apagaba las comprobaciones nuevas.** Bajar o quitar `authority_label` hacía que `verify` no corriera las de concesión ni las de honestidad y que el replay omitiera la superposición, aun con la huella de la concesión adulterada. **Reparación:** un artefacto es real por lo que **contiene** (`claims_real_content`), no sólo por su etiqueta; contenido real con otra etiqueta, o etiqueta real sin contenido, es `INCONSISTENT_ARTIFACT` (clase, verificación incompleta, replay que no reproduce).

**Bajos.** *Reparados:* L1 (el turno sin avance entraba en colisión de identidad en el almacén: ahora cuenta en la identidad **cuando existe**; los artefactos sin esos turnos conservan la que tenían), L2 (un turno tras el halt ya no copia el último turno obsoleto de la superposición), L3 (el constructor de campos reales ya no puede lanzar desde el manejador de fallos), L4 (`permits` exige las cinco dimensiones: una omitida es un rechazo), L5 (tres aserciones que no podían fallar, `... or True`, ahora son reales; el predicado del escaneo del artefacto veía sólo subíndices y ahora ve atributos, literales y `ARTIFACT_KEY`), L6 (campos derivados que se aceptaban con el digesto recalculado: `halted`, `experiment_outcome`, `authority_began`, `mixed_trajectory`, `invalid_for_continuation`, la política posterior al compromiso, el resumen de la concesión, la política de frontera y la ventana, ahora se re-derivan). *Declarados, no reparados:* L7 (el aislamiento de eventos y texto depende de las trayectorias, no es por construcción: `event_provenance.Watch` lee `sbp` al inicio del turno, que tras un compromiso es el común; la diferencia máxima común-heredado en las trayectorias naturales es de ±26 mmHg y ni la serie ni la revisión produjeron una divergencia de eventos) y L8 (un turno inocuo de cero minutos, como una vía central en el minuto 0, detiene el experimento: es el comportamiento declarado de las clases no soportadas, previo al ciclo).

**Mutantes de las reparaciones: 19 de 19 muertos** (M1 ×2, M2, M3 ×3, M4 ×4, M5 ×2, L1, L2, L3, L4 y tres de L6; el ejecutor restaura cada archivo y verifica su huella). Dos sobrevivieron en la primera pasada y se cerraron **endureciendo la prueba**, no el código: el digesto propio de un turno sólo lo ve un campo que ninguna otra comprobación re-deriva, y la bajada de la etiqueta se detectaba por la inconsistencia aunque las comprobaciones reales no corrieran (ahora la prueba exige que **corran**). *Lo que la revisión no pudo probar:* las 13 situaciones × 2 casos por la página real con `AppTest` (se apoyó en la serie del autor y en su arnés headless), la reanudación de verdad por la base de datos y `restore_attempt` (la simuló con una sesión vacía más el estado guardado), reejecuciones y reentrada concurrente de Streamlit, un cambio de archivos de `clinical_core/` a mitad de encuentro, el camino de secretos de Streamlit, NaN o infinitos del núcleo, y fuzz más largo que 80 secuencias; tampoco la autenticidad de la decisión docente FD-P3-203 (sólo leyó el texto del repositorio): **el usuario la confirmó después como auténtica** (2026-11-12), sin ampliar ningún dominio de autoridad. Las pruebas de la revisión: `test_phase3_pressure_review.py` (34).

## 11 · P3-249 · Punto de control
Registro: `docs/revision/PHASE3_PRESSURE_CHECKPOINT.json` (reconstruido por `test_phase3_pressure_checkpoint.py`; lo que el código puede decir se lee del código y los ocho estados y el veredicto son literales del punto de control).

| Estado | Valor |
|---|---|
| `PRESSURE_REAL_DEVELOPMENT_AUTHORITY` | **activa** para los dos casos de GI, sólo presión, sólo desarrollo, detrás de una concesión explícita (la décima condición de la compuerta) |
| `PRESSURE_PAGE_RUNTIME` | página real, 26 corridas, las dos rutas del reloj; presión común comprometida y nada más cambiado para el residente |
| `PRESSURE_REPLAY` | los artefactos reales verifican y reproducen **desde el artefacto solo** (candidato, validación, presión comprometida, digesto, superposición, frontera y razón de parada) |
| `POST_COMMIT_HARD_FAIL` | `INVALID_FOR_CONTINUATION` **declarado, no silencioso**, pero **consultivo** para el encuentro; la reanudación se **marca**, no se previene |
| `COLLAPSE_BOUNDARY` | precompromiso en cada minuto, falla cerrada, `ESTABLISHED` y no `IMPENDING`, ventana de 240; no es un estado terminal |
| `CONSCIOUSNESS_OVERLAY` | V1, candidata, registrada junto a la autoridad; nunca escrita ni visible para el residente |
| `CONSCIOUSNESS_LIVE_AUTHORITY` | **no concedida** (lectores nombrados y decisión C5) |
| `RESIDENT_PILOT_READINESS` | **no lista** (sólo desarrollo; la parada es consultiva; las comprobaciones corren en un proceso) |

**Veredicto A · `GI_PRESSURE_DEVELOPMENT_AUTHORITY_EXPERIMENT_VALIDATED`.** El experimento está validado **como experimento de desarrollo**: la concesión es inmutable y de huella fijada, la compuerta la exige en cada compromiso, la presión común se compromete de verdad en la página real con la superposición al lado, los fallos tras el compromiso se declaran, la frontera se respeta antes de comprometer, los artefactos reproducen y se verifican, y la corrida encendida difiere de la apagada sólo en la presión; la revisión independiente (0 altos) y sus 5 medios están reproducidos, reparados y con mutantes. **No habilita nada más allá de la autoridad de desarrollo de presión de GI ya concedida.**

**Bloqueadores exactos (de cualquier paso siguiente, no de este veredicto):** (1) la parada tras un fallo es consultiva: una parada **efectiva** exige un diseño de interfaz que no se construyó y que no debe inventarse como regla terminal; (2) el mapeo de la palabra común al `mental_status` vivo sigue bloqueado por siete lectores consecuentes (tres del motor, congelados por el cierre de la Fase 2) y por C5; (3) V1 sigue ratificada sólo para desarrollo; (4) un solo proceso; (5) la reanudación se marca pero no se previene; (6) dos casos y semántica relativa a la llegada, sin generalizar; (7) crecimiento del almacén y aislamiento de eventos demostrado en la serie, no por construcción.

**Paquete siguiente recomendado (a decisión de la docencia, no autorizado aquí):** el diseño de la **parada efectiva** (qué hace la interfaz cuando un experimento queda `INVALID_FOR_CONTINUATION`, sin inventar una regla terminal ni la muerte del paciente), con la prevención de la reanudación, antes de cualquier uso fuera del desarrollo; en paralelo, y sólo si la docencia lo pide, la ampliación de dominio (otro canal físico) **como concesión nueva y versionada**. Ninguno modifica la consciencia viva ni el primer piloto.

**Confirmaciones** (pinneadas en el registro): `COMMON_CORE_RUNTIME_AUTHORITY` sigue `False`; ninguna autoridad de consciencia; el `mental_status` heredado no cambió; ninguna consciencia común visible al residente; ningún despliegue a residentes; ninguna autoridad de producción; el primer piloto no cambió; V1 no se promovió; ninguna regla terminal inventada; ninguna fisiología reajustada; ninguna consciencia por opioides; ninguna afirmación de validación clínica.

## 11b · Certificación integrada
Una corrida anterior, sobre el árbol de trabajo **sin commit**, se hizo sobre **dos huellas** distintas (una prueba se adaptó entre medias y una partición hubo de repetirse): **no se acepta como certificación final y queda superada.** La certificación final se corre sobre **una sola huella: el HEAD de tres commits** (código, pruebas, documentación) ya congelado, con la suite particionada sin `test_clinical_core*` (`clinical_core/` es idéntico a la base; la clasificación `ALREADY_VALID_ON_EQUIVALENT_CODE` y su análisis de dependencias van en el informe del ciclo), un límite por partición de al menos 150 minutos desde el principio, las regresiones activas y una verificación adversarial dirigida a M1 a M5 y a las propiedades de presión sola, aislamiento de la consciencia, parada tras un compromiso, frontera de colapso, aislamiento de la página y rechazo de una concesión adulterada.
Sus cifras y su huella **no se escriben aquí**: un documento no puede contener la huella del árbol que lo incluye, y cambiar un solo archivo después invalidaría la certificación. Se informan en el informe del ciclo.

## 12 · Adaptaciones declaradas, cambios deliberados y límites
* **Adaptaciones declaradas tras la revisión (P3-248):** los módulos `runtime_authority.py` (registra la palabra heredada junto a la superposición, como dato) y `runtime_pressure_grant.py` (nombra la palabra como dominio EXCLUIDO) se clasifican como **mecanismo** en la tabla de lectores (`test_gi_preauthority_review.py::MECHANISM_MODULES`) y quedan fuera de la cuenta de lectores de `test_phase3_dormant_guards.py`, `test_phase3_site_isolation.py`, `test_phase3_gi_preauthority_review.py` y `test_phase3_gi_authority_readiness.py` (los números certificados —54 módulos, 7 sólo de texto, 119 filas, 32 lectores vivos— no cambian); esos dos últimos permiten además que la concesión nombre el id de la instantánea de la superposición, como dato; `test_phase3_gi_preauthority_review.py` espera que `terminal_deterioration` se detenga en la frontera (6 comprometidos, los mismos minutos bit a bit; el A/B está en `test_phase3_minute_validation.py` r2); `test_runtime_authority_streamlit_halt.py` espera los campos reales del artefacto; y el registro `docs/revision/PHASE3_DORMANT_PAIR_AUTHORITY.json` se **regeneró deliberadamente** (sólo cambia el inventario de lectores: un módulo más con uso sintáctico, uno más sólo de texto, cuatro sitios más).
* **Adaptaciones declaradas de pruebas certificadas** (lo que protegen sigue protegido): `test_runtime_authority.py::test_a3` (diez condiciones); `test_shadow_core_isolation.py`, `test_runtime_shadow_plumbing.py` y `test_runtime_shadow_evidence.py` (el módulo `runtime_pressure_grant` es de la capa);
  `test_runtime_authority_series.py` (s2, s3, s6: la parada por la frontera y la forma del artefacto real); `test_runtime_authority_lineage.py` (l11, la forma del artefacto real); `test_phase3_minute_validation.py` (la serie certificada, con la comparación A/B).
* **Una semilla de prueba, sólo del lado de las pruebas:** `conftest.py` (`_pressure_grant_test_seam`) responde «sí» a la pregunta de la concesión **sólo** para una instantánea de prueba que **no** es el punto real registrado (las pruebas certificadas inyectan puntos de prueba por el registro privado y no
  aprueban nada real); el punto real siempre recibe la respuesta real, y `@pytest.mark.strict_grant` apaga la semilla. Un sitio abierto con un punto de prueba **no lleva concesión ni superposición** y se comporta como antes de la concesión (alcanzable sólo inyectando en el registro privado, la misma frontera de confianza que el registro tenía).
* **Límites que se conservan:** un solo proceso de Python (las constantes son alcanzables por código en proceso; la defensa es la revisión y las pruebas por AST); la parada tras un fallo es **consultiva para el encuentro** (el motor heredado lo continúa; TD-142 §4 sigue vigente y **bloquea** cualquier uso con residentes);
  el replay re-deriva sólo lo que depende de la corrida; el artefacto crece con el largo del encuentro (la superposición y su entrada de replay se guardan completas); la validación clínica de cualquier magnitud no se afirma.
