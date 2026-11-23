# Fase 3 · Convergencia final previa al piloto de la traza de manejo de GI

**Ciclo P3-534 a P3-555 · decisiones docentes FD-FINALPILOT-01 a FD-FINALPILOT-10 · 2026-11-23.**

Este es el último ciclo de laboratorio previo al piloto. Su objetivo: que el piloto de desarrollo de `gi_bleed_57m` quede **realmente** usable con residentes, en un piloto pequeño, supervisado y sin consecuencias de puntuación.

Lo que este ciclo **no** es:
- No es validación clínica ni aprobación de producción.
- No es despliegue general a residentes.
- No inicia el piloto.

Lo que **no** cambia:
- sin fisiología nueva ni fisiología de control de fuente;
- sin recalibrar la presión de GI ni el tono común;
- sin autoridad en familias limitadas por la bomba, de consciencia ni terminal;
- sin puntaje;
- `clinical_core/`, el lector (`family_parser.py`, `active_order_context.py`), `order_pipeline.py`, `family_engine.py`, `development_management_trace.py`, las concesiones y las instantáneas quedan intactos.

Lo que cambia (código ejecutable): `runtime_authority.py`, `runtime_authority_turn.py`, `gi_pilot.py`, `gi_pilot_ui.py` y tres líneas de `app.py`.

## 1. El bloqueo (P3-535)

Reproducido en la página real, con la autoridad viva y la concesión `GI_NOREPINEPHRINE_DEVELOPMENT_AUTHORITY_GRANT_V1`:

- **Turno sin avance tras un minuto comprometido.** Tras «Give 1 litre…» se compromete el minuto 15. «Give normal saline.» llega a la autoridad con:
  - ningún orden ejecutado (`ran = []`);
  - una fila `fluid/HELD_CLARIFICATION` en el libro;
  - el reloj en 15 y la presión sin cambio.

  La autoridad se detenía para siempre: `MINUTE_ALREADY_COMMITTED: 15`. Lo mismo pasaba con «Increase norepinephrine to 12.», «Titrate norepinephrine to MAP 65.», «Restart norepinephrine.» y «What is the hemoglobin?».
- **Un segundo bloqueo, hallado en este ciclo.** En un turno que mezcla una orden completa con una incompleta, por ejemplo «Give 500 mL… Increase norepinephrine to 12. Reassess…» o «Place a second large-bore IV. Increase norepinephrine to 12.», la parte retenida queda con la clase `clarification`. La regla compartida de liquidación (`unsupported_in_settlement`) la contaba como clase no representable, y la autoridad se detenía con `PROVENANCE_CONTRADICTION`, avanzara o no el reloj.

## 2. La clasificación de los turnos sin avance (P3-536)

Todo turno que no mueve el reloj después de un minuto comprometido es exactamente una de estas clases (`runtime_authority.NONADVANCING_CLASSES`). La función pura es `classify_nonadvancing`.

| Clase | Qué es | Qué hace la autoridad |
|---|---|---|
| `STRUCTURAL_ONLY` | sólo reevaluación o consulta | el camino certificado de siempre: turno registrado, nada comprometido |
| `CERTIFIED_SAME_MINUTE_MUTATION` | una clase de la lista explícita sin fisiología común (la vía IV, FD-P3-NEW-03) | el mismo camino certificado de siempre |
| `CLARIFICATION_NOOP` | **probado**: nada actuó y nada de lo protegido cambió | **nuevo**: se registra sobre el mismo minuto comprometido y el encuentro sigue |
| `UNSAFE_MUTATION` | hay evidencia de mutación: corrió una intervención, cambió el estado del paciente o un campo protegido, o una orden del libro actuó | falla cerrado (`MINUTE_ALREADY_COMMITTED`) |
| `UNKNOWN` | la prueba no se pudo hacer: sin origen, sin libro, una falla nueva de la sombra, una sombra que avanzó, una presión que no es la comprometida | falla cerrado (`MINUTE_ALREADY_COMMITTED`); si además hay una orden no representable, `UNSUPPORTED_AUTHORITY_ACTION` |

Las clases se leen **antes** que la prueba: una intervención que corrió nunca es un no-op, diga lo que diga la prueba. Una prueba incompleta es `UNKNOWN`, nunca `UNSAFE_MUTATION`: el artefacto no llama mutación a lo que no mutó.

## 3. La prueba de equivalencia del estado (P3-537)

No se clasifica por el texto. El turno transaccional (`runtime_authority_turn.AuthorityTurn`, P3-271) ya ejecuta la página sobre copias y conserva intactos los originales. `turn_origin` entrega al sitio esos originales y sus copias de trabajo, sólo para los campos protegidos (`NOOP_PROTECTED_FIELDS`):
- el estado del paciente (fisiología, estado del caso, infusiones, reloj y presiones);
- la última acción ejecutada;
- el contador aleatorio del motor.

La prueba (`NOOP_PROOF_FIELDS`) compara **digestos canónicos**. Cada hecho queda verdadero, falso (evidencia de mutación) o desconocido. Sólo es no-op si todos son verdaderos:
- turno de orden;
- reloj sin cambio, en el último minuto comprometido;
- ninguna intervención corrió (sólo pueden haber corrido las estructurales: reevaluación, consulta, prueba diagnóstica);
- libro liquidado recibido, y **ninguna** de sus órdenes actuó (`order_did_not_act`): retenidas (`HELD_CLARIFICATION`, `HELD_REASONING`), no reconocidas (`UNRECOGNIZED`), canceladas, duplicadas ignoradas, o sólo registradas cuando son estructurales o un plan;
- toda clase del libro es representable (la decisión C y el contrato de la norepinefrina no se esquivan con un no-op);
- ninguna falla nueva de la sombra, y la sombra sin muestras nuevas;
- origen recibido;
- estado del paciente idéntico al original y a la copia;
- campos protegidos idénticos;
- presión igual a la del minuto comprometido;
- ninguna muestra de autoridad comprometida en el turno.

Lo único que puede cambiar es la metadata de la aclaración: el evento escrito, la historia, la lectura, la orden retenida (`pending_action`), la traza y el libro.

## 4. La integración en la autoridad (P3-538)

Un no-op probado se registra en `no_advance_turns` con el resultado `NONADVANCING_CLARIFICATION_NOOP`. Lleva:
- la clase y la prueba completa;
- las órdenes del turno, ninguna de las cuales actuó;
- el digesto de la presión y el de la presión del minuto comprometido;
- los digestos de estado (`state_digests`): origen, copia, estado juzgado y campos protegidos;
- el minuto al que queda unido.

Lo que **no** hace: no compromete nada, no agrega ninguna muestra, no inventa tiempo y no reescribe un minuto comprometido. Es durable sólo cuando se persiste, como todo turno sin avance: si el almacén no puede escribirlo, se retira y la autoridad se detiene con `ARTIFACT_PERSISTENCE_FAILED` (`test_c16`).

Las comprobaciones de configuración corren **antes** que el no-op: una presión calculada con otra instantánea es `PRESSURE_CONFIGURATION_MISMATCH` (`test_c23`), y el contrato de la norepinefrina (FD-AUTHNE) también se evalúa antes.

Después, `settle_provenance` vuelve a juzgar el libro liquidado con la **misma** regla (`order_did_not_act`): si una orden del turno actuó, es una contradicción y la autoridad se detiene. La orden completada corre normalmente en un turno posterior y se compromete el minuto siguiente, una sola vez. Un turno juzgado dos veces nunca compromete dos veces el mismo minuto (`test_b13`).

**La regla compartida de liquidación.** Una orden retenida o no reconocida, o un plan sólo registrado, de una clase que no está en la lista explícita no actuó: no cuenta como clase no representable. La orden completada se juzga por su propia clase en el turno que la ejecuta. Lo que sigue siendo contradicción:
- una clase de la lista (la vía IV) retenida;
- una clase no soportada que actuó o que el motor registró (decisión C).

La sombra seca usa la misma regla, así que ambas siguen de acuerdo.

## 5. Artefacto y repetición (P3-539)

`clarification_noop_problems` vuelve a derivar cada no-op **sólo desde el artefacto**:
- la clase y el resultado coinciden;
- todos los hechos de la prueba son verdaderos;
- no corrió ninguna intervención;
- ninguna orden nombrada actuó;
- está unido a un minuto comprometido;
- la presión es exactamente la de ese minuto;
- los digestos de estado existen, tienen forma de digesto y son iguales entre sí.

`verify_artifact` incluye estas comprobaciones, así que un no-op adulterado deja el artefacto incompleto aunque se lo vuelva a sellar con su propio digesto, y la revisión docente de la repetición (`gi_pilot.replay_review`) da `MISMATCH` (`test_c17`). Con un registro auténtico da MATCH en todas sus comprobaciones tras varios no-ops (`test_c14`).

## 6. Flujos de órdenes incompletas (P3-540)

Certificados de extremo a extremo en la página real:

| Turno | Qué pasa | Cómo sigue |
|---|---|---|
| «Give normal saline.» | se retiene («Confirm the bolus volume in mL…»); no-op en el mismo minuto | «1000 mL over 30 minutes.» se ejecuta y se compromete el minuto siguiente |
| «Increase norepinephrine to 12.» | se retiene con el texto aprobado: «The order specifies a target or an incomplete rate. Specify an explicit rate with its units to continue.» | «12 mcg/min.» sola **no** completa la orden: el lector congelado responde «Name one supported order to replace that item, or say cancel.» y nada corre (FD-ORDER-01). «Increase norepinephrine to 12 mcg/min…» descarta la retenida y corre a 12 |
| «Restart norepinephrine.» | se retiene; nunca reutiliza la tasa anterior | «Restart norepinephrine at 8 mcg/min…» corre a 8 |
| «Titrate norepinephrine to MAP 65.» | nunca se vuelve una dosis; el estado del paciente queda idéntico byte a byte | una orden explícita en mcg/min corre |
| «Double the norepinephrine.», «Increase norepinephrine by 2 mcg/min.» | se retienen; nada corre | una tasa absoluta explícita corre |
| Órdenes rutinarias que no actúan («Keep NPO.», «Monitor vitals every 5 minutes.», «Type and screen.», «Hold antihypertensives.») | no-op probado; el encuentro sigue | — |
| Varias aclaraciones seguidas | cada una es un no-op en el mismo minuto, o una respuesta a la orden retenida que tampoco ejecuta nada | la orden completada corre |
| Turno mixto | la orden completa corre y la retenida no actúa | el encuentro sigue |

Lo no soportado sigue fallando cerrado sin cambios (decisión C, FD-P3-30; contrato FD-AUTHNE): ondansetrón, ácido tranexámico, sonda nasogástrica, sonda vesical, monitoreo cardíaco continuo, norepinefrina en mg/min o mcg/kg/min. Detienen el experimento (`AUTHORITY_STOP`) sin dar nada (`test_c7`, `test_c19`, `test_dry5_an_order…`). El lanzador ahora lo dice antes de empezar, junto con cómo completar una orden retenida.

## 7. La frontera del control de fuente (P3-541, FD-FINALPILOT-05)

En `family_engine.py`, la única vía del motor anterior a una hemostasia en este caso es una **consulta ejecutada a gastroenterología**: cuando el servicio ha tenido tiempo de llegar, el motor hace la endoscopia. El piloto la cierra en capas, todas **antes** del motor:

1. **Estructural** (`gi_pilot.definitive_actions`). Revisa las acciones que el motor está por ejecutar: una consulta o derivación a un servicio definitivo (gastroenterología, cirugía, radiología intervencionista o endoscopia), o una endoscopia. Ninguna llega al motor, cualesquiera hayan sido las palabras o la lectura del libro. Con un mutante que anula toda lectura por palabras, «Call gastroenterology.» sigue sin llegar al motor (`test_c9`). **Ésta es la garantía de seguridad.**
2. **Por la orden** (`definitive_intent`). Las clases de consulta, endoscopia y procedimiento usan la regla revisada por docentes (`mt.is_definitive_request`, sin cambios). Las demás (plan, retenida, no reconocida) cuentan sólo si sus propias palabras piden el control **ahora** (`_words_request`).
3. **Por las palabras del turno**, sólo cuando el lector no hizo ninguna orden, con el mismo `_words_request`.

`_words_request` exige una palabra definitiva y descarta:
- un diagnóstico («upper GI bleed», «GI bleed protocol»);
- un matiz («may need surgery later», «if he rebleeds, call GI»);
- una negación («Hold off on GI for now.», «Do not consult gastroenterology yet.»);
- una pregunta («What is the GI plan?», «Is GI aware?»);
- un informe («GI has been informed»);
- un aplazamiento («endoscopy once stable», «possible endoscopy»).

«band» o «clip» sueltos ya no cuentan (sólo «band the varices», «clipping»…), así que «Check CBC with bands.» no termina el encuentro. `OR` y `TIPS` se leen sólo en mayúsculas.

La primera solicitud termina el encuentro en la **frontera del modelo de desarrollo**: el turno queda registrado y no se ejecuta, y la traza lo dice así («not carried out: the encounter ended at the development boundary», `test_c21`). Lo que el piloto no leyó como solicitud tampoco aparece como frontera en la traza (`_aligned_with_the_boundary`, `test_c20`). Se cubrieron en la página diez formulaciones de solicitud (de «Notify GI.» a «Take him to the OR.» o «He needs surgery.», `test_c8`): ninguna consulta llegó al motor y el reloj no se movió. «Consult ICU.» sí corre, porque no es control de fuente (`test_c9b`). La segunda barrera, que lee el estado del motor (`engine_source_control`), se mantiene.

## 8. Estado mental (P3-542, FD-FINALPILOT-06)

Lo que ya hacía el piloto:
- antes de la norepinefrina, el estado mental del modelo anterior aparece rotulado como tal;
- desde que se da norepinefrina, se oculta en el monitor, en las actualizaciones, en la apariencia y en el examen.

Lo **nuevo**: desde la norepinefrina, el modo Talk tampoco se ofrece. Si el paciente puede contestar lo decide el estado mental del modelo anterior, así que la respuesta lo delataría. La historia ya obtenida queda en la ficha (`test_c10`).

El motor no cambia. No se infiere mejoría por la presión.

## 9. Persistencia, reconexión, configuración y aborto (P3-545, FD-FINALPILOT-09)

**Contrato de un solo proceso.** El piloto corre en un solo proceso de Streamlit. Las bitácoras se escriben de forma serializada y con candado, el almacén de la autoridad es de sólo creación y el turno es transaccional.

| Situación | Comportamiento certificado |
|---|---|
| Nueva ejecución o reconexión en la misma sesión | conserva la orden retenida y la autoridad (`test_c11`, `test_dry7`) |
| Recarga, reinicio del proceso o segunda pestaña (sesión nueva) | nunca reanuda. En cuanto la sesión nueva muestra el inicio del piloto, el encuentro abierto de ese participante queda `INTERRUPTED` en el registro (antes quedaba `ACTIVE`: TD-165, ítem 13). La pestaña vieja termina en su siguiente ejecución (`ENCOUNTER_CLOSED_IN_RECORD`) sin poder completar la orden retenida (`test_c12`) |
| La configuración desaparece a mitad del encuentro (autoridad, instantánea de tono) | la página se niega antes de correr nada; el encuentro abierto queda `ENDED` con `AUTHORITY_UNAVAILABLE` en el registro y, si la configuración vuelve, termina antes de que la orden retenida corra (`test_c22`) |
| El almacén no puede escribir un no-op | se retira y la autoridad se detiene (`test_c16`) |
| Detención docente durante una aclaración | termina el encuentro en la siguiente ejecución, antes de que la orden retenida corra (`test_c13`, `test_dry8`) |
| La frontera | termina el encuentro sin ejecutar el turno |
| Repetición | da MATCH (§5) |

## 10. Revisión adversarial independiente (P3-551) y reparaciones (P3-552)

Una revisión independiente, de sólo lectura, con la consigna «encontrar razones para no usar esto mañana con un residente real», con sondas sin interfaz y en la página. Cada hallazgo material se reprodujo antes de repararlo y quedó fijado por prueba.

| Hallazgo | Severidad | Qué pasaba | Reparación | Prueba |
|---|---|---|---|---|
| 1 | MATERIAL | Órdenes rutinarias que no actúan («Keep NPO.», «Type and screen.», «Monitor vitals…», «Increase norepinephrine by 2 mcg/min.», «12 mg/min») terminaban el encuentro como `UNSAFE_MUTATION` sin haber mutación; el lanzador y `FAIL_SAFE_FINAL` decían lo contrario | La prueba lee «ninguna orden actuó» (`order_did_not_act`), no «todas retenidas»; una prueba incompleta es `UNKNOWN`; lo no representable sigue fallando cerrado con su motivo propio; el lanzador lista lo que termina el encuentro | `test_c18`, `test_c19`, `test_b14`, `test_b15` |
| 2 | MATERIAL | Falsos positivos de la frontera: negaciones, preguntas, informes, aplazamientos, un diagnóstico dentro de una orden, «bands» en un hemograma | `_words_request` (§7) para toda lectura por palabras; las clases de consulta, endoscopia y procedimiento conservan la regla docente; la barrera estructural no cambia | `test_c20`, `test_c21` |
| 3 | MENOR | El no-op guardaba sólo booleanos: un artefacto adulterado y vuelto a sellar pasaba | Digestos de estado en el registro y su comprobación | `test_b16`, `test_c17` |
| 4 | SOSPECHADO | Traza incoherente en una frontera que sólo lee el piloto | La traza marca la solicitud cuando el piloto terminó por ella y no marca lo que no leyó como solicitud | `test_c20`, `test_c21` |

Lo que resistió el ataque, según la revisión: ninguna mutación real pasa por no-op; el no-op no agrega muestra, no inventa tiempo ni duplica presión; la seguridad de la norepinefrina no cambia; toda consulta a gastroenterología se detiene; ninguna palabra de estado mental llega a la pantalla tras la norepinefrina; la persistencia, el aborto y la repetición no se rompieron.

Hallado además al verificar: el turno posterior a la orden retenida se re-juzgaba con la regla vieja (`_HELD_FATES`) en `settle_provenance`, que habría detenido después un no-op válido de orden no reconocida; ahora usa la misma regla que la prueba (`test_b14`).

## 11. Inyección de fallas (P3-550)

| Falla inyectada | Resultado | Prueba |
|---|---|---|
| almacén no disponible durante un no-op | el no-op se retira; `ARTIFACT_PERSISTENCE_FAILED`; nada aplicado | `test_c16` |
| artefacto adulterado y vuelto a sellar | `verify_artifact` incompleto; repetición `MISMATCH`, no usable | `test_c17`, `test_b11`, `test_b16` |
| concesión o configuración retirada a mitad del encuentro | la página se niega; el encuentro queda `ENDED` (`AUTHORITY_UNAVAILABLE`); nunca se reanuda | `test_c22` |
| instantánea distinta (presión de otra configuración) | `PRESSURE_CONFIGURATION_MISMATCH` antes del no-op | `test_c23` |
| configuración incompleta o no permitida al iniciar | el piloto no arranca | `test_gi_pilot::test_u1`, `test_gi_pilot_page::test_p10` |
| solicitud duplicada (el mismo turno juzgado dos veces) | nunca compromete dos veces el mismo minuto | `test_b13` |
| recarga o reinicio durante una aclaración | `INTERRUPTED`; la orden retenida nunca corre | `test_c12`, `test_dry7` |
| bitácora rota | `PILOT_RECORD_UNAVAILABLE`; la orden siguiente no corre | `test_gi_pilot_page::test_p11` |
| orden no soportada | falla cerrado con su motivo | `test_c7`, `test_c19`, `test_dry5_an_order…` |
| mutación insegura en el mismo minuto (estado, campo protegido, orden que actuó) | `UNSAFE_MUTATION`, falla cerrado | `test_b4`, `test_b5`, `test_b6` |
| solicitud de control de fuente | frontera; nada llega al motor | `test_c8`, `test_c9`, `test_c9b`, `test_dry6` |

## 12. Ensayos en seco (P3-548, P3-549)

En la página real, con cuentas sintéticas (`test_gi_final_pilot_dryruns.py`). Cada uno termina con una traza que verifica y una revisión de la repetición que da MATCH en todo, o con una detención correcta y declarada:

- DRY-1: volumen y sangre → reevaluación → norepinefrina → reevaluación → solicitud de control → frontera.
- DRY-2: suero incompleto → aclaración → completado → sigue.
- DRY-3: tasa de norepinefrina incompleta → aclaración → completada → sigue.
- DRY-4: inicio → cambio de tasa → suspensión de norepinefrina.
- DRY-5: objetivo de PAM, cambio relativo y tasa sin unidad se retienen y nunca corren; mcg/kg/min y un medicamento no representado fallan cerrado.
- DRY-6: «Get the GI team to scope him.» → frontera, sin consulta en el motor.
- DRY-7: reconexión y recarga a mitad del encuentro.
- DRY-8: aborto docente.
- Ensayo docente: observar, revisar la repetición, inspeccionar la traza, señalar y marcar inutilizable, sin ninguna consecuencia de puntuación ni intento de cuenta.

## 13. Adaptaciones declaradas de pruebas existentes

- `test_gi_pilot_page::test_p16`: la detención anterior pasa a ser el no-op probado.
- `test_phase3_gi_pilot_records`: los tres registros del ciclo anterior se generaron con `gi_pilot.py` en `cc1d3af` (sha fijado). No se regeneran y su contenido se reproduce con ese código generador. `FAIL_SAFE` queda como se ratificó; la tabla vigente es `FAIL_SAFE_FINAL`.
- `test_phase3_management_trace::test_d2`: el conjunto revisado de los diez caminos se generó con `runtime_authority.py` en `352d5fe` (sha fijado). No se regenera (la revisión humana se hizo sobre él). La autoridad del árbol repite los diez caminos con el **mismo contenido**, campo por campo; sólo cambian los dos digestos que fijan la capa (`artifact_digest`, `trace_digest`). Cada traza guardada se vuelve a extraer a su digesto desde el registro (`test_d2b`).
- `test_runtime_authority_site::test_d3`: la llamada de compromiso recibe además `origin=_authority_turn_origin()`, de sólo lectura; el bloque no decide nada nuevo.
- `test_phase3_stop_page` (`test_s15[duplicate_zero_minute_turn]`, `test_s17`, `test_s18`; las hereda `test_phase3_pressure_promotion_stop`, y `test_phase3_turn_page::test_t2` usa la misma matriz) y `test_phase3_turn_page::test_t5`: «Order urgent endoscopy.» y «Reassess in 300 minutes.» no ejecutan nada (el lector no reconoce la primera; ninguna mueve el estado), así que hoy son no-ops probados y el encuentro sigue. Lo que protegían —que un turno de cero minutos **no probado** se detiene con `MINUTE_ALREADY_COMMITTED`, que el turno rechazado no deja rastro en el encuentro real y que un clic que llega junto con él no se atiende— se conserva inyectando que el origen del turno no esté disponible (la prueba no puede hacerse: `UNKNOWN`).

## 14. Matriz de aceptación (P3-553)

Cada criterio de «PILOT-READY» del encargo, con su estado y la evidencia que lo decide. **Cero FAIL.** El registro del punto de control guarda la misma matriz (`acceptance_matrix`, `acceptance_fail_count: 0`).

| Grupo | Criterio | Estado | Evidencia |
|---|---|---|---|
| A. Flujo del residente | entra a `gi_bleed_57m` (un caso, sin intento de cuenta) | PASS | `test_gi_pilot_page::test_p1`, `test_dry1` |
| | ve sólo la información clínica prevista | PASS | `test_gi_pilot_page` (internos), `test_c10`, Chromium |
| | escribe órdenes completas | PASS | `test_dry1`, `test_dry4` |
| | escribe órdenes incompletas y recibe la aclaración | PASS | `test_c1` a `test_c5`, `test_c18` |
| | completa la orden aclarada | PASS | `test_c1` a `test_c3`, `test_dry2`, `test_dry3` |
| | reevalúa y sigue | PASS | `test_dry1`, `test_dry2`, `test_dry4` |
| | llega a la frontera de forma segura | PASS | `test_c8`, `test_c9`, `test_c21`, `test_dry1`, `test_dry6` |
| B. Autoridad | sigue unida tras no-ops de aclaración | PASS | `test_b1`, `test_b2`, `test_b14`; `test_c1` a `test_c5` |
| | las mutaciones inseguras del mismo minuto fallan cerrado | PASS | `test_b4` a `test_b9`, `test_b15`; `test_c19`, `test_c23`; `test_phase3_stop_page::test_s15` |
| | sin minuto ni muestra duplicados | PASS | `test_b1`, `test_b13` |
| | sin retroceso silencioso | PASS | `test_c16`, `test_c22`, `test_c23`, `test_p10`, `test_p11` |
| | sin deriva (configuración, instantánea, concesión) | PASS | `test_c22`, `test_c23`, `test_u1`, `test_phase3_management_trace::test_d2` |
| C. Traza de manejo | estado, acción, aclaración, orden ejecutada, respuesta, reevaluación, estado nuevo | PASS | `test_c14`, `test_c20`, `test_dry1` a `test_dry4` |
| | sin razonamiento inventado | PASS | `test_gi_pilot` (razonamiento sólo como se expresó) |
| | frontera explícita | PASS | `test_c21`, `test_dry1`, `test_dry6` |
| | repetición idéntica | PASS | `test_c14`, `test_c17`, `test_dry1` a `test_dry4`, `test_dry7` |
| D. Control de fuente | ninguna solicitud llega a la hemostasia heredada | PASS | `test_c8`, `test_c9`, `test_c9b`, `test_b17` (36 formulaciones) |
| | el piloto se detiene en la frontera | PASS | `test_c8`, `test_c21`, `test_dry6` |
| E. Estado mental | sin estado mental engañoso bajo tono | PASS | `test_c10`, `test_gi_pilot` (filtros), Chromium (pantalla y Talk) |
| F. Controles docentes | observar, abortar, revisar traza y repetición, marcar y señalar | PASS | `test_dry8`, ensayo docente, Chromium |
| G. Aislamiento | sin consecuencias de puntuación | PASS | ensayo docente, `test_p1` |
| | sin acceso a internos | PASS | `test_gi_pilot_page`, `test_c20`, Chromium (0 tokens en el cable) |
| | sin identificadores de instantánea o concesión visibles | PASS | `test_gi_pilot_page`, `FORBIDDEN_ON_PARTICIPANT_TRACE` |
| | sin ampliar autoridad de producción | PASS | `test_u1`, `test_u2`; pruebas de autoridad y concesión |
| H. Robustez | recarga, reinicio y reconexión certificados | PASS | `test_c11`, `test_c12`, `test_c22`, `test_dry7` |
| | contrato de un solo proceso claro | PASS | §9; el protocolo |
| | falla del almacén segura | PASS | `test_c16`, `test_p11` |
| I. Certificación | pruebas focalizadas en verde | PASS | §15 |
| | revisión adversarial sin bloqueo material abierto | PASS | §10 |
| | suite completa en verde o tiempos de espera ambientales demostrados sobre la misma huella | PASS | §15 |
| | `run_regressions.py` en verde | PASS | §15 |
| | árbol publicado igual al certificado | PASS | §15 |

## 15. Certificación (P3-554) y punto de control (P3-555)

**Candidato.** Rama `phase-3-runtime-integration`, base `e2f05c2`, huella del árbol de trabajo `4eecc208fbe0e9df55a8d990e557f7a10277b9216cd305bfa85d65fc1dd314a7`, la misma al inicio y al final de la suite, de las regresiones, de la repetición aislada y de la medición de tiempos. Cubre el código, las pruebas, este documento hasta la §13, el protocolo, la fila TD-166 y las filas FD-P3-306 a FD-P3-308 tal como estaban al empezar. **Se agregaron después de la huella**, y se declaran:
- el registro del punto de control;
- su entrada en el índice;
- el pin movido (`ALL_ENTRIES_DIGEST`);
- las filas FD-P3-309 y FD-P3-310;
- las §14 y §15 de este documento;
- la cláusula de `CLAUDE.md`.

**Corridas.** Antes de la primera se comprobó que no quedaba ningún proceso de pytest, Streamlit ni del navegador (carga 0,9). Cada partición corre bajo `timeout` y el ejecutor la mata al vencer; al terminar todo no queda ningún proceso de prueba ni del navegador.
- **Primera corrida (incompleta, no cuenta).** Se lanzó sin `--timeout`, y el límite por omisión del ejecutor, 3600 s por partición, detuvo 18 de las 24 particiones. Las 6 que terminaron (2972 pruebas) dieron 4 fallas: los mismos cuatro tiempos de espera de `test_faculty_cohort` que muestra la certificación. No se cambió nada antes de la segunda.
- **Segunda corrida (la certificación),** sobre la misma huella. `suite_particionada.py` con 24 particiones, `--timeout 14400`, 4 núcleos y una carga de 15 a 20.
  - **14885 pruebas: 14775 aprobadas, 10 fallas, 0 errores, 99 omitidas, 1 xfail.**
  - Las 10 fallas son todas `RuntimeError: AppTest script run timed out after 20(s)`, ninguna es una aserción, y ninguna está en un archivo que este ciclo cambió:
    - `test_faculty_cohort`: 4;
    - `test_catalog_review_in_the_sandbox`: 3;
    - `test_curriculum_app`: 2;
    - `test_inactive_account_portfolio_export`: 1.
  - Los 11 archivos de prueba del ciclo y de las adaptaciones (430 pruebas) pasan todos dentro de la suite.
- **Repetición aislada de las 10,** en serie, sobre la misma huella y con carga 0,6: **10 aprobadas, 0 fallas**, en 131 s. Clasificación: **ambiental**, no regresión.
- **Sin enlentecimiento.** Las mismas 10 pruebas se midieron en serie, en dos rondas alternadas, en la base `e2f05c2` (un worktree desechable, retirado después) y en el candidato:
  - totales: base 129,7 y 129,6 s; candidato 128,6 y 131,5 s;
  - por prueba, la mayor diferencia de medias es ≈1,1 s, sobre 46–49 s, dentro de la variación entre rondas de la propia base.
- **`run_regressions.py`:** **56/56 activas aprobadas**, salida 0. Hay 10 retiradas, conservadas y no ejecutadas por `RETIRED_REGRESSIONS`, según el propio ejecutor.

Se cumplen las cinco condiciones de P3-554 para aceptar tiempos de espera:
1. son sólo de tiempo;
2. la huella es la misma;
3. la repetición aislada pasa;
4. no hay enlentecimiento;
5. quedan documentados aquí y en el registro.

**Pruebas adaptadas:** las de la §13, declaradas también en el registro. Ninguna se saltó, se desactivó ni se marcó como inestable.

**Punto de control.** `GI_FINAL_PILOT_CONVERGENCE_CHECKPOINT_V1` (`docs/revision/PHASE3_GI_FINAL_PILOT_CHECKPOINT.json`) es un registro sellado, versionado e indexado, con un solo resultado:

> **A · `GI_MANAGEMENT_TRACE_READY_FOR_SMALL_CONTROLLED_RESIDENT_PILOT`**

**Por qué no el bloqueo duro.** Todo hallazgo material fue un defecto ordinario de implementación dentro del alcance del piloto, y se reparó. Nada exigió:
- fisiología nueva o de control de fuente;
- reabrir una calibración;
- autoridad limitada por la bomba o de consciencia;
- un juicio clínico docente nuevo;
- un rediseño general del lenguaje de órdenes;
- un problema de seguridad que no se pudiera mitigar.

El registro guarda:
- la matriz A–I (§14) con **cero FAIL**;
- la certificación;
- la revisión adversarial (2 materiales, 1 menor y 1 sospechada, todas reparadas, más V1 y V2 halladas al verificar; ningún bloqueo material abierto);
- la secuencia P3-534 a P3-555;
- las limitaciones;
- el protocolo (`docs/PHASE3_GI_PILOT_PROTOCOL.md`).

**El piloto real no se inició:** iniciarlo es una decisión docente.

**NO SE REQUIERE OTRO CICLO DE LABORATORIO PREVIO AL PILOTO** (NO FURTHER PRE-PILOT LAB CYCLE REQUIRED).
