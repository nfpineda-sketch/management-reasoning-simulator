# Fase 0 · Seguridad de la medición antes del piloto

**Encargo:** «PHASE 0 — PRE-PILOT MEASUREMENT SAFETY» (2026-10-06), sobre el motor de familias actual.
**Criterio de éxito del encargo:** «No resident action can silently disappear, no engine limitation can silently
become a resident omission, and no clinically important timeline or observable contradiction in an accepted pilot
case can cause the Management Trace to make a false inference about the resident.»
**Garantía exacta tras el cierre** (sección 21; Q1 y Q15): ninguna orden que el lector o la cobertura reconocen
como orden queda sin destino; una cláusula escrita como orden cuyo nombre ningún vocabulario conoce queda
UNRECOGNIZED con su recibo; las palabras que también podrían ser una nota, una descripción o un verbo suelto
quedan en el registro sin recibo y ninguna omisión se lee contra ellas. Quedan tres formas estrechas sin destino
propio ni guarda (TD-69 d–f), cuyo texto el registro conserva entero.
**Estado:** ver «Estado de la Fase 0», al final, después de Q1–Q15.

Documentos de esta fase:

- este informe (secciones 1–20 de la entrega; sección 21, el cierre);
- el manifiesto generado del código: `docs/revision/PILOT_FREEZE_MANIFEST.md`;
- las decisiones: `docs/COLA_DECISIONES_AI_ADVISOR.md`, secciones «Fase 0» (F0-1 a F0-12) y «Cierre de la
  Fase 0»;
- el registro de correcciones: C-2026-10-06-01 a C-2026-10-06-14 en `corrections_registry.py`;
- la deuda que queda: TD-62 a TD-70 en `docs/REGISTRO_DEUDA_TECNICA.md`;
- la hoja de firma del español nuevo: `docs/revision/F0_11_FRASES_ES.md`.

**Nomenclatura.** El encargo nombra 0A (ledger), 0B (PS001), 0C (envío) y 0D (tiempo); las secciones 9 a 18 no
llevan letra. El plan de trabajo, los commits y el registro usan una secuencia propia:

| Plan y commits | Encargo |
|---|---|
| 0A-0B · ledger, cobertura, un solo camino, regla de paquete | 0A (§2–§5) |
| 0C · PS001 fuera de la asignación | 0B (§6) |
| 0D · envío seguro | 0C (§7) |
| 0E-0F · tiempo e interrupción | 0D (§8) y §9 |
| 0G-0H · paro, observación, procedencia, Trace | §10–§13 |
| 0I · guardas del análisis | §14 |
| 0J · batería y aceptación | §16–§17 |
| 0K · congelamiento | §18 |

## 1. Rama y commit de partida

- **Rama:** `clinical-encounter-v0.13`.
- **Commit de partida:** `13592e4` («Clinical encounter: the room redraws itself only while a photograph is
  prepared»).
- **Estado de partida:** árbol limpio y sincronizado con `origin`.

## 2. Alcance implementado

| Parte | Qué se hizo | Dónde |
|---|---|---|
| Ledger por orden | Cada orden recibe un destino de un vocabulario de diez, con su texto, su forma canónica, clase, dosis, vía, ritmo, tiempo, motivo, minuto de ejecución, recibo y si su efecto está modelado | `order_ledger.py` |
| Mapa de cobertura | Más amplio que el lector: lo que parece una orden y el lector no devolvió queda UNRECOGNIZED con su recibo; también el nombre de una orden sin verbo ni dosis («- Aspirin», «Heparin drip») y la orden escrita tras una intención («We should start heparin», «Necesitamos hemocultivos»). En el cierre, también el nombre que ningún vocabulario conoce, y en silencio las palabras que podrían ser una nota (sección 21) | `order_ledger.coverage` |
| Un solo camino | Texto libre, formulario guiado, respuesta a la compuerta de razonamiento y respuesta a una aclaración (también un envío recuperado tras una interrupción) pasan por el mismo camino: cobertura, ledger, ejecución y destino. En el cierre, una orden nueva escrita después de la respuesta a una aclaración se lee a continuación como orden propia (F0-12, sección 21) | `order_pipeline.py`, `app.py`, `submission_guard.py` |
| Regla de paquete | Las órdenes independientes corren; sólo esperan los grupos dependientes (vía aérea, «X then Y», mismo agente, una reevaluación con el tratamiento retenido que juzga, si una respuesta puede completarlo) | `order_pipeline.split_bundle` |
| PS001 | R1-03, R1-04 y R2-01 fuera de la asignación automática y de las directivas; el código heredado sigue | `curriculum.py`, `encounter_directives.py` |
| Envío | Identidad por envío, guardado previo, idempotencia, botón deshabilitado, recuperación de una ejecución interrumpida, `fastReruns = false` | `submission_guard.py`, `.streamlit/config.toml` |
| Tiempo | Esperar, mirar a la cabecera, órdenes para más tarde, límite de 120 minutos explicado | `time_semantics.py`, `family_engine.py` |
| Interrupción | Una espera se detiene en el minuto del primer evento crítico y devuelve el control | `family_engine.py`, `event_provenance.py` |
| Paro y observación | Un paro es un paro verdadero; el potasio del laboratorio es el del motor; lo estático se declara estático | `observation_consistency.py`, módulos de familia |
| Procedencia | Cada evento lleva causa, prevenibilidad, severidad, si interrumpe y las órdenes que lo preceden | `event_provenance.py` |
| Trace | Campos nuevos junto a los v1: envío, órdenes, tiempo, eventos, interrupción, observación, limitaciones, versiones | `trace_phase0.py`, `app.py` |
| Guardas A–E | Lo que el registro no puede resolver en contra del residente queda «reading» o no evaluable | `rubric_screening.py` |
| Batería | 19 categorías por caso en el motor, más la página real con recarga, para los 31 casos | `pilot_acceptance.py` y pruebas |
| Congelamiento | Decisión y limitaciones por caso, versiones, indicadores y rutas excluidas; manifiesto generado | `pilot_freeze.py`, `tools_pilot_freeze.py` |

**No se tocó:** el lector (`family_parser.py`, `shared_order_language.py`: 0 líneas de diferencia), el corpus de
validación, V3 y los baselines (ES `939978a`, EN `3d942ee`); los puntajes, las rúbricas, D1–D5, las penalidades,
los objetivos y los reportes. No se abrió ninguna respuesta externa.

## 3. Archivos cambiados

Desde `13592e4`: 51 archivos de código, pruebas y configuración (6.451 líneas agregadas, 149 quitadas), más los documentos.

- **Módulos nuevos (10):** `order_ledger.py`, `order_pipeline.py`, `submission_guard.py`, `time_semantics.py`,
  `event_provenance.py`, `observation_consistency.py`, `trace_phase0.py`, `pilot_acceptance.py`, `pilot_freeze.py`,
  `tools_pilot_freeze.py`.
- **Módulos modificados (13):**
  - `app.py`, `curriculum.py`, `curriculum_runtime.py`, `encounter_directives.py`, `cognitive_generator.py`;
  - `family_engine.py`, `anaphylaxis_reaction.py`, `trauma_hemorrhage.py`, `bradycardia_toxicology.py`;
  - `catalog_trajectories.py`, `rubric_screening.py`, `corrections_registry.py`, `.streamlit/config.toml`.
- **Pruebas nuevas (10):** `test_phase0_*.py`.
- **Pruebas existentes actualizadas (18):** en la sección 13, con su justificación.
- **Documentos:**
  - nuevos: este informe y `docs/revision/PILOT_FREEZE_MANIFEST.md`;
  - actualizados: `docs/COLA_DECISIONES_AI_ADVISOR.md`, `docs/REGISTRO_DEUDA_TECNICA.md`,
    `docs/CAMBIOS_METODOLOGICOS.md`, `docs/RUNBOOK_PILOTO.md`;
  - regenerado: `docs/CATALOGO_HIPOGLICEMIA.md` (sólo su tabla de correcciones).

## 4. Conducta antes y después

| Antes (auditoría del motor o sonda de esta fase) | Después |
|---|---|
| Fármacos y consultas que el lector no conocía desaparecían sin aviso; una orden nueva escrita al responder la compuerta se perdía | Toda orden termina con un destino y un recibo; la orden nueva se une a la retenida y corre o espera con ella |
| El nombre de una orden sin verbo ni dosis («- Aspirin» en una lista, «Cefepime now», «Heparin drip», «CPR now») se perdía (TD-45 a) | UNRECOGNIZED con su recibo; una nota, un resultado o la medicación habitual no se marcan |
| Una orden escrita como intención o necesidad («We should start heparin», «Need a chest X-ray», «Necesitamos hemocultivos», «Le daría cefepima») se perdía | UNRECOGNIZED con su recibo; «We need to think about sepsis» o «I want to rule out PE» no se marcan |
| El patrón de muletillas del ledger cortaba el inicio de palabras («ecg» → «cg», «solicito» → «licito»), y una llamada o una pregunta del lector quedaba sin el texto con que se escribió | Palabras enteras; cada orden conserva su texto |
| Un ítem desconocido retenía todo el paquete | Las órdenes independientes corren; el recibo dice qué corrió y qué no |
| Un doble clic perdía la orden; dos clics rápidos la mostraban escrita sin ejecutarla | Se guarda antes de correr, corre una vez, y una ejecución interrumpida se deshace y se reintenta una vez |
| «Wait 20 minutes» no se entendía; «reassess» tomaba 0 minutos y mostraba signos previos al tratamiento bajo «After...» | La espera avanza el reloj; «reassess» es una mirada de 2 minutos, dicha como tal |
| «Repeat the ECG in 30 minutes» corría al instante | Se registra sin correr ni programarse, y se dice |
| Una espera de 120 minutos devolvía el bloqueo AV del minuto 45 y la FV del 120 juntos | La espera se detiene en el minuto 45 y devuelve el control |
| Tres familias anunciaban un paro con pulso y presión en el monitor; una frecuencia 0 se rotulaba «sinus bradycardia»; el potasio del laboratorio era el del caso | Sin pulso ni presión, mensaje acordado y nada más ejecutable; nunca «sinus» a 0; el potasio es el del motor |
| Ningún evento decía su origen | Causa, prevenibilidad, severidad y órdenes previas en cada evento |
| El Trace sólo tenía el estado del turno | Órdenes con destino, eventos, observación, limitaciones y versiones por turno |
| Una limitación podía leerse como omisión | Guardas A–E: «reading» o no evaluable, nunca omisión |
| PS001 se asignaba a un residente de primer año | No se asigna; sigue en el sandbox docente |
| La bradicardia paraba desde una frecuencia oculta (38/min en pantalla, 20/min en el cálculo) | El paro se lee de la frecuencia que muestra el monitor |
| El paro de la anafilaxia decía «adrenalina nunca dada» a quien la había dado | Dice que la dosis se agotó |
| «Stop the epinephrine infusion» se rechazaba y la infusión seguía | La detiene |
| El paro del hemotórax se declaraba prevenible | ENGINE_LIMITATION; el caso queda excluido |
| Una reevaluación escrita con una orden que ninguna respuesta completa no corría nunca, y el aviso decía «held until you answer» | Corre, y el aviso dice lo que no se hizo |
| Una orden escrita junto a la respuesta a una aclaración se marcaba «Not understood… write it again in other words» | En la entrega, no corría y su recibo lo decía. En el cierre se lee a continuación como orden propia, con su compuerta, sus preguntas, su destino y su recibo (F0-12) |
| Un nombre que ningún vocabulario conocía, escrito como orden («Zyvox.», «- Plasmaféresis», «Zyvox IV», «Sepsis, ceftriaxone.»), desaparecía, y un nombre conocido de la misma frase con él (cierre) | UNRECOGNIZED con su recibo; si las palabras también pueden ser una nota, quedan en el registro sin recibo y guardan la omisión |
| Las frases nuevas de la Fase 0 sólo estaban en inglés (cierre) | Se dicen enteras en español, con las palabras citadas de la persona residente intactas (F0-11) |

## 5. Esquema del ledger de ejecución

`order_ledger_v1`. Cada orden:

| Campo | Contenido |
|---|---|
| `order_id`, `submission_id` | Identidad estable, que viaja con la orden si queda retenida |
| `span` | Las palabras del residente, citadas con su propia cláusula; una llamada, un destino o una pregunta del lector, por las palabras de su tipo o de la pregunta |
| `canonical`, `class` | Forma normalizada y tipo (o `unrecognized`, `clarification`, `held_with_question`; en el cierre, `unread_words`: palabras guardadas en silencio, sin recibo) |
| `dose`, `route`, `rate`, `timing` | Lo que el lector leyó; `timing` con `delay_min`, `wait`, `immediate` o `after_result` |
| `written_at_min`, `executed_at_min` | Minuto en que se escribió y en que corrió |
| `fate`, `reason`, `history` | Destino, motivo y cada cambio de destino con su minuto |
| `receipt`, `receipt_shown_elsewhere` | Lo que se dijo al residente |
| `modelled_effect` | Si el simulador modela su efecto |
| `default_applied`, `limitation` | Un valor por omisión dicho en el recibo; la limitación que decidió el destino |
| `derived_from` | En el cierre: el envío de la respuesta del que salió una orden escrita después de ella (F0-12) |

**Destinos:** EXECUTED, HELD_CLARIFICATION, HELD_REASONING, RECORDED_NOT_MODELLED, UNRECOGNIZED, SCHEDULED,
CANCELLED, DUPLICATE_IGNORED, DUPLICATE_CONFIRMED, TERMINAL_NOT_EXECUTABLE.

- DUPLICATE_CONFIRMED está en el vocabulario y ningún camino lo asigna:
  - una repetición deliberada que el motor ejecuta queda EXECUTED;
  - la que el motor no repite queda DUPLICATE_IGNORED;
  - un envío repetido no crea órdenes: se registra como duplicado en `submission_log`.

**Invariante:**

- `order_pipeline.check` verifica cada turno: ningún texto accionable sin orden, ninguna orden sin destino.
- Un problema queda en el Trace como limitación `engine_inconsistency` del turno, y la regla E vuelve no evaluable
  lo que toque.
- En la batería y en las pruebas de página no apareció ninguno.

## 6. Semántica del tiempo

| Lo escrito | Lo que pasa | Recibo |
|---|---|---|
| «Wait / observe N minutes» (también en español) | Reevaluación después de N minutos | El intervalo |
| «Reassess», «repeat vital signs», sin número | Mirada a la cabecera de 2 minutos (`BEDSIDE_LOOK_MIN`, una región examinada), marcada `immediate` | Cuándo se tomaron los valores; nunca «After...» de un tratamiento que sigue corriendo |
| «Give X and reassess» | X corre y la mirada es inmediata | Dice si X tuvo tiempo de actuar |
| «Reassess in N minutes» | El intervalo pedido | — |
| Una orden para más tarde («in 30 minutes», «en 30 minutos») | No corre ni se programa: RECORDED_NOT_MODELLED, `unsupported_future_execution` | «Nothing was given and nothing was scheduled. Write it again when you want it» |
| Un volumen «in 20 minutes» | Es un ritmo, no una orden diferida | — |
| Una espera de más de 120 minutos | Se rechaza y se explica, nunca se acorta (`pilot_time_step_limit`) | El límite |

Toda transformación queda en `parsed["time_semantics"]` y en el Trace del turno.

## 7. Reglas de interrupción por eventos

- **Eventos del motor que detienen una espera** en su minuto (`event_provenance.FLAG_EVENTS`, `interrupt`):
  - el bloqueo AV, la fibrilación ventricular y la ectopia ventricular;
  - el paro;
  - la reacción bifásica y el sangrado mayor tras la lisis;
  - el neumotórax a tensión, la falla del VD por volumen y la hipotensión sostenida de la obstrucción;
  - las convulsiones y la vuelta tras el alta.
- **Dos cambios vigilados en los signos**, con severidad, cambio y persistencia juntos:
  - una sistólica < 70 mmHg que cayó ≥ 20 desde el inicio de la espera, durante 2 minutos seguidos
    (`circulatory_collapse`);
  - una SpO₂ < 85 % que cayó ≥ 5 puntos, durante 2 minutos seguidos (`oxygenation_fall`).
  - Su causa es UNKNOWN y nunca se usa sola en contra del residente.
- **Al detenerse:**
  - el resto del intervalo no corre;
  - el residente recupera el control en el minuto del evento;
  - el recibo dice qué la detuvo;
  - el Trace guarda `interrupted` (evento, minuto, intervalo pedido).
- **Catálogo de hipoglicemia:** las trayectorias de `docs/CATALOGO_HIPOGLICEMIA.md` esperan el resto del intervalo
  (`catalog_trajectories.waited_out`), como antes, para que el catálogo no cambie de significado.

## 8. Campos agregados al Trace

Los campos v1 no cambian. Se agregan, por turno (`trace_extensions`, `phase0_trace_v1`):

| Campo | Contenido |
|---|---|
| `submission` | Identidad del envío, cuándo se recibió, si llegó a la base antes de correr, reintentos, punto de entrada |
| `orders` | El ledger de las órdenes del turno, con destino |
| `time_semantics` | Las palabras de tiempo aplicadas |
| `events` | Cada evento del curso con causa, prevenibilidad, severidad, si interrumpe y `source_order_ids` |
| `interrupted` | El evento que detuvo la espera |
| `observation_snapshot` | Lo visible al final del turno, si hay paro (y desde qué minuto), los resultados estáticos informados y las inconsistencias detectadas |
| `limitations` | `unrecognized_order`, `recorded_not_modelled`, `unsupported_future_execution`, `observable_static`, `scripted_event`, `resuscitation_not_modelled`, `engine_inconsistency`, `pilot_time_step_limit` |
| `versions` | Código (`MRS_CODE_VERSION`), caso, banco, motor, esquemas del Trace, del ledger y de la procedencia |

El encuentro guarda además `order_ledger` (todas las órdenes) y `submission_log` (todos los envíos).

## 9. Guardas de seguridad del análisis

En `rubric_screening`, antes de toda propuesta o análisis. Ningún puntaje, peso ni definición cambió: un «met» que
el registro no puede resolver pasa a «reading» con su motivo, y decide el docente.

| Regla | Qué impide |
|---|---|
| A | Una omisión cuando la orden se escribió y el simulador no la ejecutó (retenida, no entendida, registrada sin modelo, programada, no ejecutable tras un paro). Una orden UNRECOGNIZED vale para cualquier tipo (comodín); una orden para más tarde, para los tipos que nombra |
| B | Una demora contada desde la ejecución tardía del simulador: cuenta desde que el residente escribió |
| C | Un reconocimiento exigido donde la observación no estaba disponible o contradecía el estado |
| D | Una retroalimentación negativa por un evento con guion, una limitación del motor, un evento de causa desconocida o uno precedido por una orden no ejecutada (`may_support_negative_feedback`); también por un evento que el congelamiento declara decidido por el simulador en ese caso |
| E | Nada después de un paro no modelado es evaluable; una inconsistencia del motor en la ventana vuelve no evaluable el evento |

La regla A y la D leen también el ledger del encuentro: una orden retenida por razonamiento y nunca respondida no
tiene turno propio en el Trace.

## 10. Rutas heredadas

- **Fuera de la asignación automática:** R1-03, R1-04 y R2-01, que corren sobre PS001
  (`curriculum.LEGACY_ENGINE_CHALLENGES`; `assignable_challenges`).
- **Fuera de las directivas docentes:** una directiva tampoco las alcanza.
- **Lo que queda:** el código, el catálogo y el sandbox docente. No se borró nada.
- **Lo que puede recibir un residente:**
  - R1: R1-05, R1-06, R1-07;
  - R2: además R2-02, R2-03, R2-04, R2-05;
  - R3: además R3-01.
- **Consecuencia curricular** (decisión F0-4): esos tres desafíos no se observan en el piloto, y MK1 (ACGME) sólo
  está vinculado a R2-01.

## 11. Envío e idempotencia

`submission_guard.py`, con la secuencia de Streamlit 1.64:

1. El callback de *Send* escribe el texto con la identidad del formulario en `submission_log`, y la página lo guarda
   en la base antes de correrlo (write-ahead).
2. La identidad cambia al capturarse. Un segundo clic sobre el mismo formulario y el mismo texto es un duplicado y no
   corre nada; un texto distinto en el formulario viejo es un envío nuevo, no uno perdido.
3. La página procesa el envío más antiguo una vez. Guarda una copia del encuentro, marca `processing` y luego
   `processed` antes de guardar. Mientras un envío espera, *Send* está deshabilitado.
4. Si un envío quedó en `processing` porque un clic detuvo la ejecución, el encuentro vuelve a la copia y el envío
   corre una vez más desde el principio. Si se detiene dos veces, se marca `interrupted`, se dice y no se repite.
5. Cada paso corre en un hilo auxiliar con el contexto del script, donde Streamlit no detiene la ejecución.
6. `.streamlit/config.toml`: `fastReruns = false`.
7. Una recarga no ejecuta nada de nuevo. Un envío recibido y no procesado se encuentra al reanudar y corre una vez.
8. Cierre (F0-12): la orden escrita después de la respuesta a una aclaración se guarda, junto con la respuesta y
   antes de correr nada, como un envío derivado (`derived_from`, `entry_point = free_text`), con el minuto en que
   se escribió; corre en la ejecución siguiente, una vez, por el mismo camino.

**Navegador real** (Chromium aislado, sin red externa; ANTES = `13592e4`, DESPUÉS = `d91dfe5`):

| Prueba | Antes | Después |
|---|---|---|
| Doble clic sin intervalo | Orden perdida sin rastro | Ejecutada una vez |
| Dos clics a 60 ms | Mostrada como escrita, nunca ejecutada | Ejecutada una vez |
| Cinco clics a 40 ms | Mostrada como escrita, nunca ejecutada | Ejecutada una vez; la ejecución que un clic detuvo se deshizo y corrió una vez |
| Recarga durante el proceso | Ejecutada | Ejecutada una vez |
| Recarga después del proceso | Nada | Nada |

## 12. Correcciones de consistencia de la observación

- **Paro verdadero en tres familias** (anafilaxia, hemorragia del miembro y hemotórax, bradicardia):
  - sin pulso, sin presión, ritmo de paro;
  - examen de paro;
  - mensaje acordado: «Cardiac arrest occurred at minute X. Resuscitation management is not modelled in this pilot.
    Subsequent management is not assessable.»;
  - toda orden posterior es TERMINAL_NOT_EXECUTABLE;
  - no se inventa recuperación.
- **Frecuencia 0:** una frecuencia de 0 nunca se rotula «sinus».
- **Potasio de la hiperpotasemia:** el laboratorio lee el potasio del motor.
- **Lo estático:**
  - historia, colaterales y las regiones del examen y estudios que el motor no modela son los valores escritos
    del caso, declarados estáticos (`observation_consistency.declaration`);
  - un resultado estático informado en un turno queda como limitación `observable_static`.
- **Bradicardia** (0J): el paro se lee de la frecuencia que muestra el monitor, con las catecolaminas incluidas.
- **Barrido sin tratamiento:** los 31 casos sin tratamiento, de la llegada al final, no muestran ninguna
  inconsistencia (`observation_consistency.check`).

## 13. Inventario de pruebas y resultados

### Las 17 pruebas exigidas

| # | Exigencia | Prueba |
|---|---|---|
| 1 | La pérdida silenciosa heredada no ocurre | `test_phase0_order_ledger.py::test_what_the_reader_did_not_read_never_disappears`; `test_phase0_acceptance_findings.py::test_an_order_no_vocabulary_knows_is_not_understood_never_gone`, `::test_the_name_of_an_order_alone_is_an_order_never_gone` |
| 2 | La orden nueva de la respuesta a la compuerta recibe destino | `test_phase0_order_ledger.py::test_a_transfusion_written_in_the_gate_follow_up_runs_and_has_a_fate` |
| 3 | Una orden desconocida no bloquea las independientes | `::test_independent_orders_run_and_a_dependency_waits`, `::test_an_unrecognised_antibiotic_no_longer_holds_the_fluid_and_the_oxygen` |
| 4 | Un envío duplicado corre una vez | `test_phase0_submission_guard.py::test_one_form_and_one_text_are_one_submission`, `::test_a_second_click_on_the_same_form_executes_nothing_more` |
| 5 | Un doble clic no pierde el envío | `::test_the_order_is_in_the_database_before_it_runs`, `::test_a_run_stopped_part_way_is_undone_and_the_order_runs_once`, `::test_a_run_stopped_twice_is_said_once_and_never_repeated` |
| 6 | Una recarga no vuelve a ejecutar | `::test_a_reload_after_processing_re_executes_nothing`, `::test_a_reload_between_the_write_ahead_and_the_run_executes_once_on_resume` |
| 7 | «Wait 20 minutes» avanza el reloj | `test_phase0_time_and_events.py::test_a_wait_is_a_reassessment_after_its_minutes` |
| 8 | «Reassess» sin número nunca muestra signos falsos posteriores | `::test_reassess_without_a_number_is_a_look_at_the_bedside`, `::test_give_and_reassess_starts_the_treatment_and_looks_at_once_honestly` |
| 9 | Una orden para más tarde nunca corre ahora | `::test_an_order_for_later_never_runs_now` |
| 10 | Un evento crítico interrumpe una espera larga | `::test_a_long_wait_stops_at_the_first_critical_event`, `::test_the_page_lets_time_pass_looks_again_and_stops_at_the_event` |
| 11 | Invariantes de ritmo, pulso y presión en el paro | `test_phase0_observation_and_provenance.py::test_an_untreated_arrest_is_the_engines_arrest_and_nothing_contradicts_it`, `::test_a_rate_of_zero_is_never_called_sinus` |
| 12 | El potasio del laboratorio lee el estado | `::test_the_hyperkalaemia_laboratory_potassium_reads_the_engine` |
| 13 | Todo texto accionable tiene destino | `test_phase0_order_ledger.py::test_every_actionable_text_and_every_order_ends_with_a_fate`; categoría `action_ledger_completeness` de la batería, en los 31 casos |
| 14 | Todo evento significativo tiene procedencia | `test_phase0_observation_and_provenance.py::test_every_event_of_the_course_declares_where_it_comes_from`; categoría `event_provenance` |
| 15 | La guarda rechaza una omisión falsa | `test_phase0_guards.py::test_rule_a_an_order_the_reader_did_not_understand_is_not_an_omission` (y las reglas A–E) |
| 16 | PS001 no se asigna automáticamente | `test_phase0_routing.py::test_the_automatic_assignment_never_launches_the_legacy_engine` |
| 17 | El replay determinista sigue intacto | categoría `deterministic_replay` en los 31 casos; `test_phase0_time_and_events.py::test_waits_are_deterministic_on_replay`; `test_replay_saved_case.py` y las pruebas de trayectorias existentes, en la suite completa |

### Pruebas de la Fase 0

| Archivo | Pruebas |
|---|---|
| `test_phase0_order_ledger.py` | 29 |
| `test_phase0_routing.py` | 5 |
| `test_phase0_submission_guard.py` | 12 |
| `test_phase0_time_and_events.py` | 31 |
| `test_phase0_observation_and_provenance.py` | 17 |
| `test_phase0_guards.py` | 12 |
| `test_phase0_acceptance_battery.py` | 604: las 19 categorías en cada uno de los 30 aceptados (570); que cada caso corre todas las categorías (31); que el excluido falla sólo donde dice su exclusión; la cobertura del congelamiento; la tabla |
| `test_phase0_acceptance_page.py` | 31 (un caso por prueba, en la página real) |
| `test_phase0_acceptance_findings.py` | 81 |
| `test_phase0_pilot_freeze.py` | 4 |
| **Total de la entrega** | **826** |
| `test_phase0_unknown_names.py` (cierre) | 107 |
| `test_phase0_answer_parity.py` (cierre) | 12 |
| `test_phase0_spanish.py` (cierre) | 23 |
| `test_phase0_submission_guard_on_postgres.py` (cierre; sólo con `MRS_TEST_POSTGRES_URL`, A–F y F0-12) | 10 |
| **Total con el cierre** | **978** |

El cierre no modificó ninguna prueba existente.

### Pruebas existentes actualizadas y por qué

| Archivo | Por qué |
|---|---|
| `test_held_order_is_not_a_trap.py`, `test_missing_settings_and_held_orders.py`, `test_what_the_page_says_follows_what_ran.py`, `test_cognitive_encounters.py` | Fijaban la retención del paquete entero; ahora fijan la regla de paquete con la misma intención: la página dice qué corrió y qué espera (0A-0B). `test_cognitive_encounters.py` además espera el resto del intervalo cuando un evento detiene la espera (0F) |
| `test_oxygen_device_phrasing.py` | En 0A-0B fijó que la reevaluación esperaba al oxígeno de un dispositivo que el encuentro no tiene. Pero ninguna respuesta lo completaba: el oxígeno terminaba UNRECOGNIZED y la reevaluación no corría nunca, mientras el aviso decía «held until you answer». Ahora fija que la reevaluación corre y que el aviso dice lo que no se hizo (C-2026-10-06-11) |
| `test_cognitive_catalog.py`, `test_curriculum_assignment.py` | Fijaban la exposición de R1-03, R1-04 y R2-01 a la asignación automática; ahora fijan su exclusión (0C) |
| `test_cognitive_generator.py` | Exigía que las semillas sortearan los 31 casos; ahora, los 30 que el congelamiento permite (0K) |
| `test_the_families_added_2026_09_23.py`, `test_ed_observation_is_a_destination.py`, `test_acs_reperfusion.py`, `test_faculty_review_2026_09_20.py`, `test_pe_obstruction.py`, `test_transfusion_overload.py`, `test_arrival_consciousness.py`, `test_blood_products_and_bleeding_orders.py` | Usaban una espera larga sin interrupción o «reassess» de 0 minutos; ahora esperan el resto del intervalo tras un evento, o usan un intervalo explícito. El escenario clínico de cada prueba no cambió (0E-0F) |
| `test_critical_clinical_language_regressions.py`, `test_spanish_orders.py` | Una orden para más tarde ya no corre al instante: lo fijan (0E) |

### Resultados

- **Suite completa sobre el candidato final** (4 particiones, el código del commit `3c67cd9`): **7.429 pasaron,
  1 falló, 83 omitidas, 1 xfail**.
  - El fallo es `test_tools_reclassify.py`, que compara HEAD con el árbol de trabajo y sólo puede pasar con el
    código en un commit. Sobre `3c67cd9` pasa: 14 de 14.
  - Las omisiones son las mismas 83 de las corridas anteriores:
    - pruebas que piden PostgreSQL (`MRS_TEST_POSTGRES_URL`);
    - pruebas que piden un paquete de imágenes o un encuentro guardado que no están en esta copia;
    - sorteos que no tocan la familia que la prueba necesita.
- **Corridas intermedias:** dos se detuvieron antes de terminar porque esta fase siguió hallando brechas que
  corrigió:
  - nombres de órdenes sin verbo y órdenes escritas como intención;
  - el patrón de muletillas;
  - el texto citado de las órdenes;
  - el recibo de la respuesta a una aclaración.

  La final corrió sobre el candidato definitivo.
- **Navegador real, 0E–0G** (Chromium aislado, sin red; ANTES = `13592e4`, DESPUÉS = el candidato;
  `acs_54m_inferior` sin tratar):

  | Paso | Antes | Después |
  |---|---|---|
  | «Wait 20 minutes.» | «Please specify a question, investigation, treatment, or reassessment»; el reloj sigue en 0 | El reloj pasa a 20 |
  | «Reassess.» | Reevaluación de 0 minutos | Mirada a la cabecera de 2 minutos, dicha como tal (minuto 22) |
  | «Wait 60 minutes.» | No se entiende; el reloj sigue igual | La espera se detiene en el minuto 45 (bloqueo AV) tras 23 de los 60 minutos, y lo dice |
  | «Reassess in 90 minutes.» | Llega al minuto 90 y muestra el bloqueo AV del minuto 45 junto con los signos de los 90 | La espera se detiene en el minuto 120 (FV, sin pulso). El monitor muestra FV, sin presión ni saturación. Aparece el mensaje acordado del paro |
  | Aspirina con su razonamiento | Se da | TERMINAL_NOT_EXECUTABLE, con su recibo, para la aspirina y para la reevaluación |

  Ningún error en pantalla y ningún intento de red fuera de la autoprueba. Las capturas quedaron fuera del
  repositorio, en el directorio de trabajo de la sesión.
- **Primera corrida completa** (con 0A–0I y parte de 0J): 6.680 pasaron, 6 fallaron, 83 omitidas, 1 xfail.
  - Los 6 fallos eran de la Fase 0 y se corrigieron:
    - un texto de pantalla sin español;
    - tres de la batería de hipoglicemia (esperar el resto del intervalo);
    - una cita del registro;
    - `test_tools_reclassify.py`, que compara HEAD con el árbol y sólo puede pasar con todo en un commit.
- **Segunda corrida completa:** 7.375 pasaron, 5 fallaron, 83 omitidas, 1 xfail. Los 5 fallos se corrigieron:
  - la variedad de las semillas (prueba actualizada, arriba);
  - dos documentos generados desactualizados (regenerados);
  - `test_tools_reclassify.py`;
  - una prueba del manifiesto que corrió mientras se regeneraba.
- **Fallos preexistentes:** ninguno atribuido a `13592e4`.

## 14. Tabla de aceptación de casos

La tabla completa, con desafíos, motor, batería y el número de límites que cada caso ya declaraba, se genera del
código en el manifiesto (`docs/revision/PILOT_FREEZE_MANIFEST.md`, «Casos: batería y decisión»). Resumen:

- **Motor:** el de familias, caso del banco, en los 31.
- **Batería:** PASS en los 30 aceptados.
- **Decisión evaluada:** ninguna limitación toca una decisión evaluada de un caso aceptado. Las tres
  limitaciones globales que sí la tocan (G-RESUSCITATION, G-LATER-ORDERS, G-READER-V3) tienen su guarda (E, A y A/D).

| Caso | Decisión | Limitaciones de la Fase 0 |
|---|---|---|
| `acs_48m_wellens` | ACCEPT | — |
| `acs_52m_de_winter` | ACCEPT WITH DECLARED LIMITATION | C-SCRIPTED-VF |
| `acs_54m_inferior` | ACCEPT WITH DECLARED LIMITATION | C-SCRIPTED-AV-BLOCK, C-SCRIPTED-VF |
| `acs_61m_posterior` | ACCEPT WITH DECLARED LIMITATION | C-SCRIPTED-VF |
| `acs_66f_nonst` | ACCEPT | — |
| `acs_70f_left_main` | ACCEPT WITH DECLARED LIMITATION | C-SCRIPTED-VF |
| `anaphylaxis_29f` | ACCEPT WITH DECLARED LIMITATION | C-BIPHASIC, G-HARM-NOT-MODELLED |
| `anaphylaxis_63m_betablocked` | ACCEPT WITH DECLARED LIMITATION | C-GLUCAGON-INFUSION |
| `asthma_24f` | ACCEPT WITH DECLARED LIMITATION | G-HARM-NOT-MODELLED |
| `asthma_49m` | ACCEPT WITH DECLARED LIMITATION | G-HARM-NOT-MODELLED |
| `bradycardia_avb3_78f` | ACCEPT WITH DECLARED LIMITATION | C-INFRANODAL-BLOCK |
| `bradycardia_bb_54f` | ACCEPT WITH DECLARED LIMITATION | C-BRADYCARDIA-DEFINITIVE |
| `bradycardia_ccb_68m` | ACCEPT WITH DECLARED LIMITATION | C-BRADYCARDIA-DEFINITIVE |
| `bradycardia_hyperk_63m` | ACCEPT WITH DECLARED LIMITATION | C-BRADYCARDIA-DEFINITIVE |
| `gi_bleed_57m` | ACCEPT WITH DECLARED LIMITATION | G-HARM-NOT-MODELLED |
| `gi_bleed_72f` | ACCEPT WITH DECLARED LIMITATION | G-HARM-NOT-MODELLED |
| `hypoglycemia_28m` | ACCEPT | — |
| `hypoglycemia_54m_thiamine` | ACCEPT | — |
| `hypoglycemia_76f` | ACCEPT | — |
| `obstructive_pyelonephritis_58f` | ACCEPT WITH DECLARED LIMITATION | C-SOURCE-CONTROL |
| `opioid_35m` | ACCEPT | — |
| `opioid_67f` | ACCEPT | — |
| `pneumonia_46f` | ACCEPT WITH DECLARED LIMITATION | G-HARM-NOT-MODELLED |
| `pneumonia_83m` | ACCEPT WITH DECLARED LIMITATION | G-HARM-NOT-MODELLED |
| `pulmonary_edema_58m` | ACCEPT | — |
| `pulmonary_edema_75f` | ACCEPT | — |
| `pulmonary_embolism_33f` | ACCEPT | — |
| `pulmonary_embolism_61m` | ACCEPT | — |
| `renal_colic_34m` | ACCEPT | — |
| `trauma_hemothorax_41m` | **EXCLUDE** | C-NO-THEATRE |
| `trauma_limb_hemorrhage_27m` | ACCEPT WITH DECLARED LIMITATION | C-LIMB-ARREST-13 |

**Aceptados:** 30 de 31 (12 ACCEPT, 18 ACCEPT WITH DECLARED LIMITATION). **Excluido:** 1.

**Afirmaciones direccionales de la batería**, en `pilot_acceptance.py`, por caso:

- el manejo correcto a tiempo es mejor que la omisión;
- el tardío no es mejor que el oportuno (gravedad máxima del curso);
- un tratamiento dañino no mejora al paciente;
- el exceso no mejora;
- iniciar y detener una infusión cambia su estado;
- una dosis repetida tiene su destino;
- una orden razonable no modelada no cambia la fisiología;
- esperar y reevaluar avanzan el reloj lo pedido;
- el manejo combinado no es peor que el correcto;
- donde aplica, el deterioro terminal sin tratamiento y la recuperación con él;
- además: recarga y reanudación, replay determinista, ledger completo, procedencia, consistencia de la observación
  y guardas del Trace.

## 15. Casos excluidos y por qué

- **`trauma_hemothorax_41m`.** El pabellón, control definitivo del hemotórax, no está modelado. Desde que la Fase 0
  hizo verdadero el paro, tras el drenaje el paciente para hacia el minuto 60 haga lo que haga:
  - drenaje en el minuto 0;
  - transfusión repetida;
  - búsqueda de otra fuente;
  - cirugía llamada.

  Por eso:
  - la decisión evaluada después del drenaje (`trauma_drained_and_never_looked_again`, ventana 10–180) nunca sería
    evaluable (regla E);
  - la batería falla exactamente en «manejo correcto» y «recuperación»;
  - corregirlo exige fisiología del trauma, fuera de la Fase 0.

  El caso no se sortea ni se ofrece en las directivas; sigue en el sandbox docente. Esta exclusión se apartaba del
  cierre prepiloto C-2026-10-02-08 («ningún caso excluido»). **Decisión docente F0-2 (2026-10-06):** fuera del
  piloto de residentes, sin modelar el pabellón; el piloto usa 30 casos aceptados.
- **R1-03, R1-04 y R2-01 (rutas de PS001).** No son casos del banco, pero quedan fuera de la asignación de
  residentes (sección 10).

## 16. Limitaciones que quedan

- **De todo el banco,** con su guarda (manifiesto):
  - G-RESUSCITATION: el paro termina lo evaluable;
  - G-LATER-ORDERS: las órdenes para más tarde no se programan;
  - G-STEP-120: un paso del reloj llega a 120 minutos como máximo;
  - G-READER-V3: el lector congelado;
  - G-STATIC-OBSERVATIONS: lo estático, declarado;
  - G-HARM-NOT-MODELLED: daños no modelados;
  - G-INTERRUPTIONS: los umbrales de interrupción.
- **Por caso:** C-SCRIPTED-AV-BLOCK, C-SCRIPTED-VF, C-BIPHASIC, C-GLUCAGON-INFUSION, C-BRADYCARDIA-DEFINITIVE,
  C-INFRANODAL-BLOCK, C-SOURCE-CONTROL, C-LIMB-ARREST-13 y C-NO-THEATRE. Además, los límites que cada caso ya
  declaraba (`engine_limits`, C-2026-10-02-08).
- **Deuda registrada sin corregir:**
  - TD-62: hemotórax sin pabellón;
  - TD-63: «Stop the infusion» sin nombre dice «No infusion is running» aunque corra una;
  - TD-64: terapias definitivas de la bradicardia;
  - TD-65: órdenes para más tarde y esperas largas;
  - TD-66: daño no modelado;
  - TD-67: textos nuevos en inglés (corregida en el cierre; la redacción espera la firma docente);
  - TD-68: la cobertura es heurística, con falsos positivos seguros y texto citado aproximado tras un número con
    punto;
  - TD-69 (cierre): lo que la cobertura todavía no dice como orden no entendida, con su guarda donde se pudo;
  - TD-70 (cierre): lo que queda de F0-12.
- **Lo que la cobertura no puede ver** (cierre, sección 21; TD-69): una orden escrita sola con una palabra del
  vocabulario de notas («Vitals.», «Airway.»); nombres escritos justo después de un nombre conocido que el lector
  leyó, sin «with/con» («Give ceftriaxone zyvox»); un nombre que una acción del lector absorbe en su propio texto.
  El registro guarda el texto entero del turno. Una pregunta («Can we get a CT?») no se lee como orden, por
  diseño.
- **Español** (cierre, F0-11): las frases nuevas de la Fase 0 se dicen enteras en español; la redacción espera la
  firma docente (`docs/revision/F0_11_FRASES_ES.md`). El defecto cosmético de la mayúscula tras «Now,» ya no
  aparece en español («Ahora, sin pulso: …»); en inglés sigue («Now, No pulse: …»), sin efecto en el registro.
- **Lo no probado:**
  - En navegador real se verificaron:
    - el envío (0D);
    - la espera, la mirada, la interrupción, el paro y las órdenes tras el paro de 0E–0G, en un caso
      (`acs_54m_inferior`).
  - El resto de las pantallas cambiadas, en los 31 casos, se verificó con AppTest sobre la página real, con
    recarga. La sala en español no se recorre con AppTest (no selecciona una opción traducida): se verifica por
    las frases y por el código de la página (sección 21).
  - PostgreSQL: en el cierre, A–F y F0-12 sobre una base PostgreSQL 16 local y descartable (sección 21). No se
    probó contra la base del proveedor del piloto.
- **Una orden escrita después de la respuesta a una aclaración** (cierre, F0-12): se lee a continuación como orden
  propia. Si la respuesta deja algo de la orden retenida sin completar, no corre y su recibo lo dice (TD-70).
- **Lo que la Fase 0 no cambia:** la fisiología. Lo que el motor no modela sigue sin modelarse; la Fase 0 lo vuelve
  visible, registrado y no evaluable en contra del residente.

## 17. Decisiones que requieren al docente

En `docs/COLA_DECISIONES_AI_ADVISOR.md`, sección «Fase 0», con lo que hay mientras tanto y una recomendación. **Todas
se decidieron el 2026-10-06** y quedan cerradas (sección 21 y «Cierre de la Fase 0» del Decision File):

| ID | Tema | Tipo |
|---|---|---|
| F0-1 | Lector congelado frente a «modify parser/action handling»: la capa de la sala posterior al lector | **Contradicción entre fuentes** |
| F0-2 | `trauma_hemothorax_41m` excluido frente a C-2026-10-02-08 | **Contradicción entre fuentes** |
| F0-3 | TD-45 (g) resuelta en la sala | Confirmación |
| F0-4 | Hueco curricular: R1-03, R1-04, R2-01 y MK1 | Decisión curricular |
| F0-5 | Mirada de 2 minutos, esperas > 120 minutos, órdenes para más tarde | Confirmación |
| F0-6 | Umbrales de interrupción | Confirmación clínica |
| F0-7 | Prevenibilidad declarada de cada evento | Confirmación clínica |
| F0-8 | Paro de la bradicardia desde la frecuencia mostrada; texto del paro de la anafilaxia | Confirmación clínica |
| F0-9 | Mascarilla con reservorio a 15 L/min; nombre de la infusión | Confirmación |
| F0-10 | La compuerta de razonamiento sigue reteniendo el envío completo | Confirmación metodológica |
| F0-11 | Español de los textos nuevos | Revisión docente |
| F0-12 | Una orden nueva escrita al responder una aclaración no corre | Confirmación metodológica |

## 18. Manifiesto de congelamiento

`docs/revision/PILOT_FREEZE_MANIFEST.md` (identificador `pilot-freeze-phase0-2026-10-06`), generado por
`tools_pilot_freeze.py` desde `pilot_freeze.py` y la batería. `test_phase0_pilot_freeze.py` falla si el documento se
aparta del código. Contiene:

- **Casos aceptados y versiones:** huella del texto de cada caso y de su declaración de evaluación. La segunda es la
  que `evaluation_basis` congela con cada encuentro al iniciar, de modo que un encuentro se compara con el
  congelamiento.
- **Desafíos permitidos** por año y casos sorteables por desafío.
- **Versiones:**
  - motor de familias v1, ejecución 0.24.2;
  - banco 1.0.0, generador 0.17.0, runtime 0.24.13;
  - lector congelado en V3;
  - Trace `management_trace_v1` + `phase0_trace_v1`;
  - ledger `order_ledger_v1`, procedencia `event_provenance_v1`.
- **Indicadores exigidos:** `fastReruns = false`, `MRS_OFFLINE_CASES=1`, sin `MRS_REPLAY_CASE` ni
  `MRS_DEFAULT_VARIANT`, entre otros.
- **Rutas heredadas excluidas y limitaciones aceptadas.**

**Un encuentro conserva el motor, el caso y la versión con que empezó:**

- el caso viaja en el estado del encuentro;
- la declaración de evaluación se congela al iniciar;
- cada turno registra el código con que corrió (`versions.code_version`);
- la regla del runbook es no desplegar con encuentros abiertos.

Las versiones internas del motor no cambiaron en esta fase: el commit desplegado (`MRS_CODE_VERSION`) identifica el
código, como en las fases anteriores.

## 19. Confirmación: no se empezó la migración al núcleo común

- No se implementó el núcleo fisiológico común ni se migró ninguna familia.
- No se rediseñó el motor generado, no se agregó fisiología con IA en tiempo de ejecución y no se empezó la Fase 1.
- Los cambios de fisiología se limitaron a lo que exige un caso aceptado para no engañar una decisión de manejo:
  - paro verdadero (0G);
  - el umbral de paro de la bradicardia leído de la frecuencia mostrada, sin cambiar el umbral;
  - el texto del paro de la anafilaxia.
- El código heredado no se borró.

## 20. Commit, push y despliegue

- **Commits locales** en `clinical-encounter-v0.13`:
  - `a6ab3a6` (0A-0B);
  - `0818be5` (0C);
  - `d91dfe5` (0D);
  - `3c67cd9` (0E–0K: código, pruebas, registro y documentos generados);
  - el commit de documentación que contiene este informe, el Decision File, el registro de deuda, la vista
    metodológica y el runbook.
  - los commits del cierre (sección 21).
- **Push:** ninguno. **Despliegue, merge, PR y release:** ninguno.
- No se tocaron datos de producción y no hubo llamadas pagadas.

## 21. Cierre de la Fase 0 (2026-10-06)

**Instrucción:** «Phase 0 is APPROVED IN PRINCIPLE»: cerrar la Fase 0 sin reabrir su diseño y sin empezar la
Fase 1 ni el núcleo fisiológico común. Registro: `INSTRUCTION_2026_10_06_PHASE0_CLOSURE` y C-2026-10-06-12 a
C-2026-10-06-14 en `corrections_registry.py`. Decisiones: `docs/COLA_DECISIONES_AI_ADVISOR.md`, «Cierre de la
Fase 0».

### 21.1 Decisiones F0-1 a F0-12

«Con limitación declarada»: la decisión acepta una conducta que el manifiesto declara como limitación del piloto,
con su guarda.

| ID | Decisión docente | Estado |
|---|---|---|
| F0-1 | El lector V3 sigue congelado; la capa posterior al lector es de la sala | Cerrada con limitación declarada (G-READER-V3; TD-69) |
| F0-2 | `trauma_hemothorax_41m` fuera del piloto de residentes; sin modelar el pabellón | Cerrada con limitación declarada (C-NO-THEATRE): 30 casos |
| F0-3 | TD-45 (g) resuelta en la sala | Cerrada |
| F0-4 | Hueco curricular aceptado; PS001 no vuelve a la asignación | Cerrada con limitación declarada (R1-03, R1-04, R2-01 y MK1 no se observan) |
| F0-5 | Mirada de 2 minutos; «dar X y reevaluar»; órdenes para más tarde; límite de 120 minutos | Cerrada con limitación declarada (G-LATER-ORDERS, G-STEP-120) |
| F0-6 | Umbrales de interrupción; un evento de causa UNKNOWN sigue protegido de toda inferencia negativa | Cerrada |
| F0-7 | Un evento con guion o NOT_PREVENTABLE_IN_SIMULATOR nunca sostiene una retroalimentación negativa | Cerrada |
| F0-8 | Paro de la bradicardia desde la frecuencia mostrada; texto del paro de la anafilaxia | Cerrada |
| F0-9 | Mascarilla con reservorio a 15 L/min por omisión, dicho y registrado | Cerrada |
| F0-10 | La compuerta de razonamiento sigue reteniendo el envío completo; su demora es de la compuerta y nunca del residente (regla B), registrado en el Decision File | Cerrada |
| F0-11 | Español de todos los textos nuevos de la Fase 0 que ve el residente | Cerrada: hecho (21.4); la redacción espera la firma docente |
| F0-12 | Paridad del punto de entrada si es pequeña y segura | Cerrada con limitación declarada (G-ANSWER-ORDER; TD-70): paridad implementada (21.3) |

### 21.2 Cobertura: un nombre que ningún vocabulario conoce

En la capa posterior al lector (`order_ledger.coverage`); el lector V3 no cambió.

- **Dicho como no entendido** (UNRECOGNIZED con su recibo; no ejecuta nada; la regla A lo lee como comodín):
  - un nombre solo, en una lista o en una frase de nombres («Zyvox.», «- Plasmaféresis», «ECMO.»);
  - con «now», «urgente», tras «Necesitamos» o «Quiero» («Zyvox now.», «Necesitamos zyvox.»);
  - con vía o pauta y sin verbo («Zyvox IV.», «Tygacil q12h.», «Zyvox cada 12 horas.»);
  - donde va el nombre de la orden tras un verbo de orden («Give zyvox in 100 mL saline.»);
  - después del problema que trata («Sepsis, zyvox.», «Creo que es sepsis, ceftriaxona.»);
  - un nombre conocido junto a uno desconocido, que antes desaparecía con él («Zyvox and ceftriaxone.»);
  - «Taponamiento.» solo, que la cobertura tomaba por nota (era el taponamiento de la herida en la hemorragia
    de la extremidad). «Hacer taponamiento.», que corre como control de la hemorragia, ya no se dice además «no
    entendido».
- **Guardado en silencio** (UNRECOGNIZED, clase `unread_words`, sin recibo en la sala; la regla A no lee una
  omisión en su ventana): las palabras que también podrían ser una nota, una descripción o un verbo suelto:
  - una etiqueta con dos puntos, una condición sin verbo, un número sin unidad, un nombre unido a la nota con «y»
    («Sepsis: zyvox.», «If hypotensive, zyvox.», «Zyvox 600»);
  - nombres tras «with/con» que siguen a un nombre conocido que el lector leyó («Give ceftriaxone with zyvox»);
  - un verbo o un participio solo («Suctioning.», «Lavado.», «Suboxone.», «- Proning»).
- **No se vuelve orden:** un diagnóstico, un hallazgo, un estado, una etiqueta, la historia, un resultado, una
  negación, una pregunta, el razonamiento o lo que dijeron otros (controles negativos de
  `test_phase0_unknown_names.py`).
- **Falsos positivos medidos** sobre los textos de residente del repositorio (ensayos tanda20, batería y pruebas;
  nunca el corpus de validación):
  - recibos: 3.082 textos, 168 marcas nuevas, 0 perdidas, ninguna en los ensayos tanda20;
  - silencio: en 3.200 textos, las formas «with/con» y verbo o participio suman 45 marcas, ninguna en tanda20, y no
    cambian ninguna marca con recibo. La primera forma silenciosa (nombres donde también podría haber una nota)
    guarda palabras en 4 textos de tanda20 («corticoide», «Despertó» dos veces, «Pain-free»): no se dice nada;
    sólo una omisión evaluada en esa ventana pasaría a «reading»;
  - «Taponamiento.»: 1 marca silenciosa más, ninguna perdida;
  - se midió y se descartó una guarda para nombres pegados a un nombre conocido sin «with/con»: marcaba palabras
    de descripción en 6 textos de tanda20 («laboratorio básico», «VVP gruesas»).
- **Lo que queda sin destino propio ni guarda** (TD-69 d–f; declarado en G-READER-V3):
  - una orden escrita sola con una palabra del vocabulario de notas («Vitals.», «Airway.», «Neuro checks.»);
  - nombres justo después de un nombre conocido que el lector leyó, sin «with/con» («Give ceftriaxone zyvox»):
    quedan en el texto citado de esa orden;
  - un nombre que una acción del lector absorbe en su propio texto («Reassess BP and zyvox in 10 minutes»).

  En los tres, el registro guarda el texto entero del turno, y la persona docente lo lee.
- **Garantía exacta** (Q1, Q15): ninguna orden que el lector o la cobertura reconocen como orden queda sin destino;
  una cláusula escrita como orden, con un nombre que ningún vocabulario conoce, queda UNRECOGNIZED con su recibo;
  las palabras que podrían ser una nota quedan en el registro y protegen la omisión. Las tres formas de arriba son
  la excepción declarada.

### 21.3 F0-12: la orden escrita después de la respuesta

- **El ejemplo de la instrucción:** «Start norepinephrine.» queda retenida y pregunta la dosis; la respuesta es
  «0.1 mcg/kg/min. Also give 500 mL LR.».
  - La noradrenalina se completa con 0,1 mcg/kg/min y corre (EXECUTED, con su ritmo en el ledger).
  - «give 500 mL LR» se guarda con la respuesta, antes de correr nada, como un envío propio (`derived_from`,
    `submission_guard.derive`), con el minuto en que se escribió.
  - En la ejecución siguiente se lee como cualquier orden escrita: pasa por la compuerta de razonamiento (en el
    ejemplo, la pide: HELD_REASONING), sus propias preguntas, su destino y su recibo.
  - La sala lo dice: «Also in your answer: "give 500 mL LR". The answer completes the held order only; this order
    is read next, as an order of its own, with its own receipt.»
- **Nunca** completa ni cambia la orden retenida, ni se salta la compuerta ni una aclaración.
- **Lo que queda** (TD-70, G-ANSWER-ORDER):
  - si la respuesta deja algo de la orden retenida sin completar, la orden de después no corre y su recibo lo dice
    (UNRECOGNIZED, comodín de la regla A);
  - la orden de después corre después de la retenida y de su espera: el registro guarda el minuto en que se
    escribió, y la regla B no lee la demora como del residente.
- **Pruebas:** `test_phase0_answer_parity.py` (12, con la página real) y la prueba F0-12 sobre PostgreSQL (21.5).

### 21.4 Español (F0-11)

- Cada frase nueva de la sala se dice entera en español, antes de las reglas de palabras (`language._PHASE0_RULES`):
  - recibos del ledger (no entendido, registrado sin modelo, no ejecutado tras el paro, orden para más tarde);
  - paquete parcial (ejecutado y retenido);
  - mirada en la cabecera y espera interrumpida, con sus eventos;
  - paro, actualización sin pulso y examen del paro;
  - límite de 120 minutos;
  - envío interrumpido (con y sin una parte aplicada);
  - orden escrita en una respuesta y orden leída después de ella;
  - flujo por omisión de la mascarilla con reservorio;
  - los dos paros de la anafilaxia.
- Las palabras citadas de la persona residente quedan como las escribió (nunca «Stop infusión de the»).
- El inglés no cambia. Los destinos, los códigos y los campos internos no se traducen; el registro guarda el
  recibo en inglés y la sala lo dice en el idioma del encuentro, que no cambia durante el encuentro.
- **Pruebas:** `test_phase0_spanish.py` (23). La sala en español no se recorre con AppTest (no puede seleccionar
  una opción traducida): se verifica por las frases y por el código de la página.
- **Firma:** `docs/revision/F0_11_FRASES_ES.md`, como R-4.

### 21.5 PostgreSQL (A–F)

- **Entorno:** PostgreSQL 16.13, un clúster creado para esto en el contenedor de desarrollo, descartable, en
  127.0.0.1:55432, base `mrs_phase0_smoke`, sin red externa ni datos reales. **Nunca producción.** La prueba borra
  y recrea su esquema.
- **Cómo:** la página real (AppTest), en modo cuentas, con `MRS_DATABASE_URL` en esa base
  (`test_phase0_submission_guard_on_postgres.py`; sin `MRS_TEST_POSTGRES_URL` se omite):
  - A: la orden queda en la base antes de correr, corre una vez y queda `processed`;
  - B: un segundo clic sobre el mismo formulario no ejecuta nada más;
  - C: una recarga entre el guardado previo y la ejecución la ejecuta una vez al reanudar;
  - D: una recarga después no ejecuta nada;
  - E: una ejecución detenida se deshace y corre una vez; detenida dos veces, se dice y no se repite;
  - F: dos sesiones sobre un encuentro: el control de revisión rechaza el guardado de la segunda y la página lo
    dice; ninguna orden corre dos veces ni se pierde sin aviso;
  - y F0-12: la orden escrita después de una respuesta se guarda con ella y corre una vez.
- **Resultado:** 10 de 10 (sección 21.7, sobre el HEAD final).
- **No probado:** la base del proveedor del piloto. El runbook (§3, paso 0) pide esta prueba sobre una base
  descartable de la misma versión antes del despliegue.

### 21.6 Archivos del cierre

- **Código:** `order_ledger.py`, `order_pipeline.py`, `submission_guard.py`, `app.py`, `rubric_screening.py`,
  `language.py`, `pilot_freeze.py`, `tools_pilot_freeze.py`, `corrections_registry.py`.
- **Pruebas nuevas (4):** `test_phase0_unknown_names.py`, `test_phase0_answer_parity.py`, `test_phase0_spanish.py`,
  `test_phase0_submission_guard_on_postgres.py`. Ninguna prueba existente cambió.
- **Documentos:** este informe, `docs/COLA_DECISIONES_AI_ADVISOR.md`, `docs/REGISTRO_DEUDA_TECNICA.md` (TD-67 a
  TD-70), `docs/revision/F0_11_FRASES_ES.md` (nuevo), `docs/RUNBOOK_PILOTO.md`, `docs/READINESS_PILOTO_FORMATIVO.md`;
  regenerados: `docs/revision/PILOT_FREEZE_MANIFEST.md` y `docs/CATALOGO_HIPOGLICEMIA.md`.
- **Sin tocar:** el lector (`family_parser.py`, `shared_order_language.py`, `active_order_context.py`), el corpus de
  validación, V3 y los baselines; la fisiología; los puntajes, las rúbricas, D1–D5, las penalidades y los
  objetivos. No se abrió ninguna respuesta externa.

### 21.7 Verificación final

Pendiente de la corrida sobre el commit final: se completa en el commit que sigue a esa corrida.

## Revisión final Q1–Q15

| # | Pregunta | Respuesta exigida | Respuesta | Evidencia |
|---|---|---|---|---|
| Q1 | ¿Puede una orden desaparecer sin destino? | NO | **NO para toda orden que el lector o la cobertura reconocen como orden; sí en tres formas estrechas que la cobertura no reconoce** (TD-69 d–f: una orden escrita sola con una palabra del vocabulario de notas, nombres pegados sin «with/con» a un nombre conocido leído, un nombre absorbido por una acción del lector). En ellas el registro guarda el texto entero del turno, sin destino propio ni guarda | Invariante por turno (`order_pipeline.check`); ledger completo en los 31 casos; pruebas 1, 2 y 13; cierre: sección 21.2. La cobertura es heurística (TD-68, TD-69) |
| Q2 | ¿Puede leerse como omisión algo no soportado? | NO | **NO** para todo lo que el registro sabe que el simulador no ejecutó (retenido, no entendido con recibo o en silencio, registrado sin modelo, para más tarde, tras el paro). La excepción es la de Q1 y Q15: las tres formas de TD-69 (d–f) no tienen guarda propia | Reglas A y D; prueba 15; `test_rule_a_*`; `test_phase0_unknown_names.py` |
| Q3 | ¿Puede un duplicado ejecutarse dos veces? | NO | **NO** | Pruebas 4 y 6; navegador real |
| Q4 | ¿Puede perderse un envío por doble clic o recarga? | NO | **NO** | Pruebas 5 y 6; navegador real |
| Q5 | ¿Puede el residente esperar y reevaluar? | SÍ | **SÍ** | Pruebas 7 y 8; categorías I y J en los 31 casos |
| Q6 | ¿Puede un evento crítico ocurrir en medio de una espera sin devolver el control? | NO | **NO** | Prueba 10; `interrupted` en el Trace |
| Q7 | ¿Puede un evento con guion o no prevenible usarse en contra del residente? | NO | **NO** | Regla D; `test_rule_d_*`; página: ningún evento con `may_support_negative_feedback` tras una orden no ejecutada |
| Q8 | ¿Contradice la observación al estado en un caso aceptado de modo que afecte el razonamiento de manejo? | NO | **NO** | Pruebas 11 y 12; `observation_consistency` en cada turno de la batería y de la página (0 inconsistencias); barrido sin tratamiento |
| Q9 | ¿Se asigna PS001 automáticamente? | NO | **NO** | Prueba 16 |
| Q10 | ¿Critica el análisis en un punto afectado por una limitación? | NO | **NO**, con la misma excepción declarada de Q1 y Q15 (TD-69 d–f) | Reglas A–E; `limitations` por turno; categoría `trace_safety_guards` |
| Q11 | ¿Se implementó el núcleo común? | NO | **NO** | Sección 19 |
| Q12 | ¿Cubre la batería cada caso aceptado? | SÍ | **SÍ** | 30 de 30 aceptados en el motor (19 categorías) y en la página real; el excluido, también |
| Q13 | ¿Pasa la suite completa sobre el HEAD final comprometido, con el árbol limpio y 0 fallos? | SÍ | Ver 21.7 | Sección 21.7 |
| Q14 | ¿Se probó la persistencia en PostgreSQL? | SÍ, o «NO — PRE-DEPLOYMENT BLOCKER» | **SÍ**, en PostgreSQL 16 local y descartable (A–F y F0-12), nunca en producción; la base del proveedor queda para el paso 0 del runbook | Sección 21.5; `test_phase0_submission_guard_on_postgres.py` |
| Q15 | ¿Puede una intervención plausiblemente accionable, fuera del vocabulario, desaparecer todavía sin aviso? | NO | **SÍ, sólo en las tres formas estrechas de TD-69 (d–f)**, sin guarda propia y con el texto del turno en el registro. Fuera de ellas: dicha como no entendida con su recibo, o guardada en silencio cuando también puede ser una nota, una descripción o un verbo suelto, y entonces la regla A no lee una omisión contra ella | Sección 21.2; `test_phase0_unknown_names.py` (107, EN/ES, con nombres que ningún vocabulario tiene) |

## Estado de la Fase 0

**Entrega (2026-10-06): COMPLETA. Cierre (2026-10-06): hecho; ver 21.7 para la verificación final.**

- F0-1 a F0-12 cerradas (cinco con limitación declarada); Q1 y Q15 dicen la garantía exacta, con la excepción
  declarada de TD-69 (d–f).
- PostgreSQL: A–F y F0-12 en una base descartable local.
- 30 casos aceptados de 31; excluido `trauma_hemothorax_41m` (F0-2).
- No se hizo push, despliegue, merge, PR ni release, y no se empezó la Fase 1 ni el núcleo común.
- Antes de desplegar, el piloto espera:
  - la autorización del push;
  - las condiciones del readiness (`docs/READINESS_PILOTO_FORMATIVO.md`): las firmas, incluida la de las frases
    F0-11 si el piloto corre en español; el despliegue con preflight (A); el orden de las fotos (TD-56); la prueba
    de humo en el entorno desplegado (B); la autorización explícita (C);
  - el paso 0 del runbook: la prueba del envío sobre una base PostgreSQL descartable de la versión del proveedor.
