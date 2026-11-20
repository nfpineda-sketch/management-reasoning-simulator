# Fase 3 · Ratificación del control manual de tasa de norepinefrina y límite «objetivo ≠ tasa» (P3-449 a P3-461)

> **Nota del 2026-11-20 (FD-TARGET-01 a FD-TARGET-11).** Este documento describe la contención **antes del motor** del ciclo anterior. Después, el defecto se **reparó en la fuente** (`family_parser.py`, con su sucesión declarada): lo que aquí figura como limitación de la nitroglicerina, del verbo «restart» y de «increase norepinephrine» sin número quedó resuelto, y la regla del paso por el turno es hoy la **segunda barrera** (defensa en profundidad). Estado vigente: `docs/PHASE3_TARGET_RATE_SOURCE_REPAIR.md` y `TD-161`. Este texto **no se reescribe**.

Encargo del 2026-11-20. Rama `phase-3-runtime-integration`; linaje `PHASE2_AMENDMENT_3` (certificado, digesto `867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c`); instantánea común de tono `COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1`; concesión viva `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3` (sin cambio).

**El único cambio ejecutable está en `order_pipeline.py` (el paso previo al motor) y en el texto en español de su mensaje (`language.py`): una orden de infusión con un número y sin unidades se retiene como pregunta y nunca se ejecuta, sea cual sea el número (una PAM, una PA, una FC o un error).** El defecto nace en el lector de órdenes (`family_parser.py`) y se completa en `active_order_context.py`; **ambos, y el motor (`family_engine.py`), están congelados** (la prueba del lector congelado y el digesto de la congelación de calibración de la Fase 2), así que **no se tocaron** (§6). No cambia fisiología, constantes del tono, instantánea, acoplamiento con la bomba, el motor, el espejo, la sombra, `clinical_core/`, la autoridad, la puntuación ni el primer piloto, y no es una validación clínica. `COMMON_CORE_RUNTIME_AUTHORITY = False`.

## 0 · Decisiones docentes (2026-11-20; FD-NR-01 a FD-NR-07)

| Id | Decisión |
|---|---|
| FD-NR-01 | La semántica de control manual de tasa de norepinefrina se **acepta para DESARROLLO**. Operaciones explícitas soportadas: INICIAR, AUMENTAR, DISMINUIR, SUSPENDER y REINICIAR, con tasas absolutas en mcg/min. |
| FD-NR-02 | Se **cierra** más calibración de `tone_gain`, `half_effect_rate_mcg_min`, `onset_tau_min` y `offset_tau_min` para esta capacidad. **No** se reabren LOW, HIGH, la selección de CENTER_REFERENCE ni la calibración del tono común. |
| FD-NR-03 | Estado durable de desarrollo `NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_CLOSED`: aceptado para semántica de desarrollo. **No** significa validación clínica, aprobación de producción, aprobación para residentes ni ampliación de la autoridad viva. |
| FD-NR-04 | Siguen **no soportados**: mcg/kg/min; titulación automática por objetivo de PAM; órdenes relativas sin un contexto de tasa activa soportado; consciencia bajo tono; promoción educativa en familias limitadas por la bomba. Ninguno se implementa en este ciclo. |
| FD-NR-05 | La siguiente cuestión crítica de seguridad es el defecto heredado de interpretación: «titrate norepinephrine to MAP 65» puede leerse como 65 mcg/min. Se **reproduce, rastrea y corrige** antes de intentar que la sombra consuma órdenes resueltas por el motor. |
| FD-NR-06 | **No** se autoriza ampliar la autoridad de norepinefrina. El alcance de la autoridad viva sigue igual. |
| FD-NR-07 | El comportamiento ante una orden mal formada sigue, provisionalmente, **fallando cerrado**. No se cambia la recuperación en este paquete salvo para reparar un defecto de seguridad demostrado; que una orden válida posterior recupere tras una frontera mal formada es una decisión docente aparte. |

## 1 · P3-449 · Revisión humana preservada

**Resultados reportados** (`NOREPINEPHRINE_TITRATION_V1_FACULTY_REVIEW`, digesto del conjunto `576e11f2…`): TIT-1 aumento 5→10 mcg/min `ACCEPT`; TIT-2 disminución 10→4 `ACCEPT`; TIT-3 suspensión `ACCEPT`; TIT-4 secuencia 5→10→4→suspensión `ACCEPT`; TIT-5 reinicio 10→suspensión→10 `ACCEPT`. Totales: `ACCEPT` 5, `ACCEPT_WITH_LIMITATION` 0, `RECALIBRATE` 0, `REJECT` 0.

**Procedencia: `HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED`.** El almacén persistido de la persona revisora (`titration_review/` y `titration_reviews/` de su propio almacén) **no está en este contenedor**: el almacén de revisión que hay aquí está vacío, y los otros directorios `titration_review*` que existen son sesiones sintéticas de prueba y de capturas del asistente, que **no** son evidencia humana y no se leyeron como tal. Se usaron los resultados explícitos del encargo. **No se inventó** ninguna respuesta Q1–Q5 (no se reportaron), comentario, evento de bloqueo, marca de tiempo ni identidad de la persona revisora. Quedan sin verificar contra el almacén: las respuestas Q1–Q5, los juicios globales, el orden de los escenarios, la pantalla de cierre y los eventos con su orden.

Registro: `docs/revision/PHASE3_HUMAN_NOREPINEPHRINE_TITRATION_REVIEW.json` (sellado, versionado, indexado; cada escenario enlazado por digesto al conjunto fijado). Se **preservan** sin reescribir todos los registros anteriores de revisión: el conjunto de la revisión, su punto de control, las sondas de titulación, la instantánea común de tono y su ratificación (con su digesto y el hash del archivo).

## 2 · P3-450 · Ratificación

Registro `docs/revision/NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_V1.json`, estado **`NOREPINEPHRINE_MANUAL_RATE_CONTROL_DEVELOPMENT_SEMANTICS_CLOSED`** («aceptado para semántica de desarrollo»). Contiene las decisiones FD-NR-01 a FD-NR-07, las operaciones soportadas, el cierre de calibración, los dominios no soportados, la frontera provisional ante una orden mal formada y lo que **no** se concede. Se escribió **antes** de reparar el defecto, así que lo declara `OPEN_AT_RATIFICATION`; **no se edita** al repararse: la reparación la registra el punto de control del ciclo (un registro generado es inmutable; una representación nueva es un registro sucesor, `docs/PHASE3_HISTORICAL_RECORD_VERSIONING.md`). No se tocó la física, la instantánea común de tono ni la autoridad.

## 3 · P3-451 · Mapa de representaciones de una orden de norepinefrina (de extremo a extremo)

Sólo lectura, sobre el encuentro real (`pilot_acceptance.Encounter`, que es la rama de familias de `app.py`) con la infusión de 10 mcg/min en curso en el caso de hemorragia digestiva.

| Capa | Dónde | Campos que lleva la orden | Tasa / unidades | Objetivo | Origen de la tasa |
|---|---|---|---|---|---|
| 0 · Texto escrito | página; `parsed["raw_text"]` | texto libre | — | **en el texto** | — |
| 1 · Intérprete de texto | `family_parser.parse_family_actions` → bloque de goteos vasoactivos de `_parse_piece_core` | `type`, `operation` (inicio, ajuste, continuar, suspender; lo infiere del verbo, por omisión inicio), `rate`, `units`; para nitroglicerina `rate_mcg_min` | **explícita** sólo si hay una tasa con unidades (`10 mcg/min`); **inferida** si es el único número suelto (respaldo del número suelto) | **ningún campo**: el objetivo no existe como concepto en la orden | `rate=65.0, units=None` para «MAP 65» |
| 1b · Tiempo | `time_semantics.apply` | añade la demora o el momento | no toca tasa ni unidades | — | — |
| 2 · Turno y libro | `order_pipeline`, `order_ledger` | `_order_id`, etiquetas, entrada del libro (`kind: drug`) | no toca tasa ni unidades | — | — |
| 3 · Motor: completado y validación | `family_engine._validate` → `active_order_context.complete_active_order` (sobre una copia) | la orden **completada**: si es ajuste o continuar y falta la tasa o las unidades, se copian de la infusión en curso (`treatments.norepinephrine_rate`, `_units`); luego rangos (0,001–100 mcg/min; 0,001–1,5 mcg/kg/min) | **aquí `65, sin unidades` pasa a `65 mcg/min`**; un inicio sin unidades **no** se completa y el validador pregunta | — | **inferida** (heredada de la infusión en curso) |
| 3b · Estado del motor | `family_state.norepinephrine` (mcg/min efectivos; mcg/kg/min × peso), `treatments.norepinephrine*` | tasa efectiva; resumen de acción (`action_summaries`) | 65 mcg/min | — | — |
| 4 · Espejo | `runtime_shadow.ShadowSession._mirror` → `MirroredAction` | `action` = la orden **tal como la interpretó el intérprete** (copia); `receipt` = el resumen del motor del mismo tipo (por posición); minuto de antes del turno; sin texto crudo | acción: `65, sin unidades`; recibo: `65 mcg/min` | — | las dos |
| 5 · Lectura del mapeo | `runtime_tone_support.order_disposition(action, receipt)` | tasa en mcg/min o `None` + motivo | **lee la orden tal como está escrita**: sin unidades → se rechaza | — | **explícita** únicamente |
| 6 · Historia y escritor | `infusion_history`, `map_orders`, `NorepinephrineRateHistory` | `(minuto, tasa)` llevados; brechas declaradas | sólo tasas explícitas en mcg/min | — | explícita |
| 7 · Artefacto y repetición | `runtime_shadow_store`, `order_log` | la traza espejada, tal cual | la misma historia (función pura del espejo) | — | — |

**Pregunta principal: ¿en qué capa exacta «MAP 65» se confunde con 65 mcg/min?** En **dos**, y las dos hacen falta: la capa 1 fabrica la tasa (65) a partir del número del objetivo, y la capa 3 la vuelve ejecutable al heredar las unidades de la infusión en curso. Las capas 4 a 7 **no** se confunden: el espejo entrega las dos representaciones, el mapeo lee la orden tal como está escrita y la rechaza. **Congelados:** las capas 1 y 3 (`family_parser.py`, `active_order_context.py`) y el motor (`family_engine.py`) están en la prueba del lector congelado y/o en el digesto de la congelación de calibración de la Fase 2; el paso por el turno (`order_pipeline.py`, capa 2) **no** lo está.

La otra ruta de texto de la página (la del caso fijo PS001, `app.py::parse_agent_mcg_rate`) sólo lee una tasa **con** unidades: nunca leyó «MAP 65» como tasa (prueba `t17`).

## 4 · P3-452 · Reproducción (los diez textos del encargo, antes y después)

Infusión de 10 mcg/min en curso; «parser» = lo que sale del intérprete; «motor» = la tasa efectiva final; «sombra» = el desenlace del mapeo.

| | Texto | Antes del arreglo | Después del arreglo |
|---|---|---|---|
| A | titrate norepinephrine to MAP 65 | parser `ajuste 65 sin unidades` → **motor 65 mcg/min, ejecutada** → sombra `REFUSED_FAIL_CLOSED` | **retenida con pregunta** (un número sin unidades no es una tasa); motor 10; el espejo no recibe nada |
| B | titrate norepinephrine to MAP >65 | igual que A (65) | igual que A |
| C | maintain MAP 65 | sin acción (no es una orden) | sin cambio |
| D | increase norepinephrine to 10 mcg/min | ajuste 10 mcg/min; ejecutada | sin cambio |
| E | norepinephrine 10 mcg/min | inicio 10 mcg/min; ejecutada | sin cambio |
| F | decrease norepinephrine to 4 mcg/min | ajuste 4 mcg/min; `DECREASED` | sin cambio |
| G | stop norepinephrine | suspensión; `STOPPED` | sin cambio |
| H | restart norepinephrine at 10 mcg/min | **retenida: el intérprete (congelado) no lee el verbo «restart»** (nada se dosifica) | sin cambio (caracterización, §14) |
| I | norepinephrine 0.1 mcg/kg/min | el intérprete la lee tal cual; **el motor la convierte** por peso (11,1 mcg/min); la sombra la rechaza | sin cambio: el motor heredado la convierte por diseño; **la sombra nunca la convierte** |
| J | increase norepinephrine | ajuste sin tasa; el motor la completa con la tasa en curso (10; ningún cambio real); la sombra la rechaza | sin cambio (no hay número que retener; no se adivina ninguna tasa) |

**Cuantificación sobre 28 textos de objetivo** (23 de norepinefrina, 1 de dobutamina, 1 de epinefrina, 3 de nitroglicerina; verbos *titrate*, *wean*, *reduce*, *decrease*, *increase*, *continue* y las formas en español; palabras *MAP*, *PAM*, *SBP*, *PAS*, *pressure goal*, *meta*, *objetivo*): el intérprete dio una tasa numérica en **23/28** (norepinefrina 19/23; dobutamina 1/1; epinefrina 1/1; nitroglicerina 2/3; los 5 sin número fueron frases de meta sin cifra); el motor ejecutó una **dosis** en **16 de los 23** textos de norepinefrina (16 de los 19 numéricos; los otros 3 eran inicios sin unidades, que el validador ya preguntaba). **Tras la reparación: 0 de los 23 textos de norepinefrina se ejecutan como dosis.**

## 5 · P3-453 · Clasificación de la capa de falla: **F · `MULTIPLE_LAYERS`**

| Capa | Contribución | Medida |
|---|---|---|
| 1 · Intérprete de texto (origen) | **necesaria**: lee un objetivo como tasa por el respaldo del número suelto | 23/28 textos con tasa numérica |
| 3 · Completado del motor (habilitante) | **necesaria**: hereda las unidades y la vuelve ejecutable | 16/19 ejecutados como dosis con infusión en curso; 0 sin infusión en curso; 0 en un inicio |
| 4 · Espejo | no se confunde: entrega la orden como está escrita y el recibo | 0 |
| 5 · Mapeo / adaptador de tono | no se confunde: rechaza lo que no dice `mcg/min` | 0 (rechazó 2/2 en la traza) |
| 6 · Escritor e historia | nunca se alcanza | 0 |

La **primera** capa (el intérprete) es el origen y la que habría que reparar en la fuente, pero está congelada (§6). La reparación se hace en la capa permitida más temprana, el paso por el turno antes del motor: la orden de objetivo no llega al motor, ni al espejo, ni a la sombra.

## 6 · P3-454 · Diseño mínimo seguro (y el diseño que se descartó)

Regla pedida por la docencia: **una instrucción que da un objetivo fisiológico y ninguna tasa absoluta explícita no crea nunca una dosis.**

**Descubrimiento de gobernanza (no estaba en el encargo).** Las dos capas del defecto son lector congelado: `family_parser.py` y `active_order_context.py` figuran en `test_prephase1_reader_freeze.py` (`CLAUDE.md`: no se toca el lector mientras la validación externa esté en espera), y `family_parser.py`, `family_engine.py` y `active_order_context.py` están en las fuentes de la congelación de calibración de la Fase 2 (`calibration.frozen_digest()`, fijado por `test_phase2_amendment_artifacts.py`). Tocarlos exige decisiones y procedimientos que el encargo no concede (y se contradicen con una restricción vigente); no se eligió en silencio: **se reparó en una capa que no está congelada** y la decisión de reparar en la fuente se deja a la docencia (§14).

**Primer diseño, descartado.** Una guarda en el intérprete con un vocabulario de palabras de presión (inglés y español) y una retención con marca `unsupported_target_titration`. Funcionaba para la lista, y una **revisión adversarial independiente** lo derrotó: (1) es una lista de palabras, y cualquier palabra que no esté en ella deja pasar el número (`PA`, `TAM`, `TAS`, `TAD`, «meta de 65», «hasta 65 de PAM», «65 (mmHg)», «entre 65 y 70 con norepinefrina», FC, CPP; **121 630 frases de 1,65 millones generadas** seguían saliendo como tasa, y nitroglicerina arrancaba a 120 mcg/min sin infusión previa); (2) tenía falsos positivos (órdenes de «continuar» sin tasa que se retenían); y (3) **rompía dos congelamientos** (`test_prephase1_reader_freeze.py` y 5 pruebas de `test_phase2_amendment_artifacts.py`). Se revirtió por completo.

**Diseño final: una regla estructural, antes del motor.** En `order_pipeline.split_bundle`, el paso por el que pasa cada turno antes de ejecutarlo (`pilot_acceptance.Encounter`, el flujo de la página y `app.py`), una orden de infusión (norepinefrina, dobutamina, epinefrina u «orden por el rol» sin fármaco nombrado) que **trae una tasa sin unidades** no se ejecuta: se retiene con una pregunta («indica una tasa absoluta explícita con sus unidades») y **la copia retenida no conserva ningún número**, de modo que una respuesta posterior como «mcg/min» no la completa en una dosis (prueba `t9`). La regla **no depende de ninguna palabra**: una PAM, una PA, una FC, un objetivo o un error son lo mismo, un número sin unidades. Una **suspensión** no necesita tasa y nunca se retiene.

*Qué se decidió no hacer, y por qué:* no se tocó el lector, el completado ni el motor (congelados); no se arregló sólo la sombra (el defecto es visible para el residente y nace antes); no se quitó el respaldo del número suelto del lector (congelado); no se enseñó el verbo «restart»; ninguna titulación automática, controlador ni lazo cerrado; **la nitroglicerina no se cubrió** (§14).

## 7 · P3-455 · Implementación

- `order_pipeline.py`: `UNITS_REQUIRED` (el mensaje), `unitless_infusion_rate(action)` (la regla: `(pregunta, copia sin número)` o `None`) y su uso en `split_bundle`, antes de validar la orden. Retenida como pregunta, la orden entra en el mecanismo de órdenes pendientes de la página con `rate=None` y `units=None`.
- `language.py`: la regla en español del mensaje nuevo.
- `corrections_registry.py`: la entrada `C-2026-11-20-01` (la corrección con su alcance, razón y pruebas; es un registro: no cambia ningún comportamiento).
- **No** se tocó ningún archivo congelado (el lector de cinco archivos, el digesto de calibración), ni el motor, el espejo, la sombra, `clinical_core/` ni la autoridad: las pruebas de congelamiento y de aislamiento están en verde (§12).
- Invariantes que se mantienen (pruebas `t3`, `t15`): una tasa explícita con unidades de 10 y de 4 mcg/min; aumentar o disminuir **hasta** una tasa absoluta explícita; suspender; reiniciar (el inicio explícito tras suspender); una tasa explícita con un objetivo que sólo da la razón («increase norepinephrine to 10 mcg/min to keep MAP above 65») sigue siendo esa tasa; mcg/kg/min no se convierte en la sombra; ninguna física nueva; ningún camino «fármaco → mmHg»; ninguna ampliación de la autoridad.
- **Efecto declarado fuera del objetivo:** «Increase norepinephrine to 12» o «…to 10 gamma» (una tasa **sin unidades**, que el motor heredado completaba con las de la infusión en curso) ahora pregunta las unidades. Es la misma raíz (un número sin unidades no es una tasa) y la docencia aprobó sólo tasas explícitas en mcg/min (FD-NR-01); si se quiere recuperar la abreviatura, es una decisión suya (§14). Una consecuencia buena: una orden así ya no llega al espejo, y una suspensión posterior sí se sigue (prueba `t13`).

## 8 · P3-456 · No regresión del control manual de tasa

Las pruebas que regeneran lo certificado a través del intérprete real **no cambian de resultado**: los cinco escenarios aceptados por la docencia (TIT-1 5→10, TIT-2 10→4, TIT-3 10→suspensión, TIT-4 5→10→4→suspensión, TIT-5 10→suspensión→10) siguen siendo igual a sus fuentes certificadas (`test_phase3_titration_review_records.py`), y lo mismo el inicio único FR-F, la sonda de embolia pulmonar y la de bajo tono (`test_phase3_tone_pathway_records.py`, `test_phase3_tone_titration*.py`, `test_phase3_tone_support.py`). Ninguna constante ni parámetro cambió.

**Pruebas adaptadas, declaradas:** `test_phase3_tone_titration.py::test_r2…`. Sus expectativas para las sondas **R3** («Increase norepinephrine to 12», una tasa sin unidades, seguida de una suspensión) y **R5** («titrate to MAP 65»), que el arnés guarda como lo observado entonces (el motor corrió 12 y 65 mcg/min; la sombra los rechazó y se cerró), describían **defectos heredados de la tasa sin unidades**. Ahora ninguna llega al motor ni al espejo: R5 deja la sombra igual que el inicio solo (motor 10) y en R3 la suspensión posterior **sí se sigue** (motor 0, sombra 0). Lo que la prueba protege (un número sin unidades nunca se lee como tasa; la corrida y el motor coinciden) sigue protegido y más fuerte; las otras seis sondas se sostienen igual; el arnés `test_tone_titration_analysis.py` y sus registros sellados **no se editan** (siguen siendo el registro de lo observado).

## 9 · P3-457 · Frontera de la sombra: orden cruda frente a orden resuelta por el motor

*Medido sobre el encuentro real* (sólo lectura): el espejo guarda la orden **tal como la interpretó el intérprete** (`action`) y el **recibo** del motor del mismo tipo (`receipt`, emparejado por posición).

| Criterio | Orden cruda (hoy) | Orden resuelta por el motor |
|---|---|---|
| Fidelidad de la información | lo que la persona escribió, ya interpretado; incluye `rate=None`, órdenes sin fármaco y sin unidades | lo que el motor **hizo**; el motor sólo expone un resumen (`action_summaries`), no la orden completada |
| Identidad del fármaco | «stop the infusion» y «increase the infusion to 20 mcg/min» llegan como `infusion_adjustment` **sin fármaco**, con **recibo vacío** (el recibo es del tipo `norepinephrine`, no se empareja) | el motor las resuelve a la norepinefrina; **no** lo entrega |
| Unidades | `12` sin unidades llega sin unidades; el recibo sí dice mcg/min | completadas por el motor (conveniencia heredada) |
| Separación objetivo/tasa | **segura tras P3-455** (el objetivo ya no llega como tasa) y la regla «tal como está escrito» la rechazaría igualmente | sería la **menos segura**: exactamente el defecto de este ciclo vive en lo que el motor completa |
| Sustitución en el mismo minuto | funciona: el mapeo reemplaza igual que el motor (medido: `REPLACED_WITHIN_ITS_MINUTE` y `DECREASED`, motor 5) | habría que reproducir el orden de ejecución |
| `repeat_order` | **no divergen**: «repeat norepinephrine» no se ejecuta en el motor («Specify which recorded drug or fluid to repeat»), así que no se espeja | requeriría resolver la repetición |
| Orden diferida | el espejo ya tiene su propio mecanismo de retención y liberación; el mapeo recibe la orden y el recibo de la liberación | igual |
| Artefacto y repetición | la traza guardada es la orden cruda + recibo: la repetición es una función pura | cambiaría la forma de **todo** artefacto y registro histórico ya sellado |
| Compatibilidad histórica | total | rompería la regeneración de los registros ya certificados (sólo sucesores) |
| Riesgo de divergencia semántica | **declarada**: la sombra dice «ya no refleja la vasopresor del encuentro» | segundo motor de resolución dentro de la sombra, o un cambio en el motor y en el contrato del espejo compartido de todas las familias |

**Divergencias medidas (todas declaradas, ninguna inventa dosis):** orden sin fármaco («stop the infusion», «increase the infusion to 20 mcg/min»): el motor la sigue y la sombra se cierra y lo dice; tasa sin unidades («increase norepinephrine to 12»): el motor corre 12 mcg/min y la sombra la rechaza; mcg/kg/min: el motor la convierte (11,1 mcg/min) y la sombra la rechaza sin convertir.

**Veredicto P3-457: A · `RAW_ORDER_REMAINS_CORRECT_BOUNDARY`.** Una vez reparado el defecto del objetivo, la frontera cruda es la correcta **para esta etapa**: es la más segura (lee sólo lo explícito), es la única compatible con todo lo ya certificado y declara lo que no puede seguir. Ninguna divergencia medida es un defecto de seguridad. Lo que **no** se resuelve con la frontera cruda es un hueco de **fidelidad** (la sombra no sigue la suspensión escrita sin nombrar el fármaco), y repararlo exigiría un **contrato nuevo del espejo compartido** (por ejemplo, un híbrido con las dos representaciones y su procedencia). **Eso no se inventó**: si la docencia quiere que la sombra siga esas órdenes, es una decisión arquitectónica suya (§14).

## 10 · P3-458 · Política ante una orden mal formada (sólo análisis y recomendación)

*Medido* con «Start norepinephrine at 10 mcg/min», luego «Increase norepinephrine to 12.» (sin unidades, mal formada para el mapeo):

| Escenario | Motor al final | Sombra (política actual) |
|---|---|---|
| 1 · mal formada con la infusión activa | 12 | `STARTED`, `REFUSED_FAIL_CLOSED` |
| 2 · y luego una tasa absoluta explícita válida (20 mcg/min) | 20 | `STARTED`, rechazada, **rechazada** |
| 3 · y luego una suspensión | 0 | `STARTED`, rechazada, **rechazada** (la sombra sigue mostrando la tasa que tenía) |
| 4 · y luego un reinicio explícito (suspender, iniciar 10) | 10 | todo rechazado desde la primera |
| 5 · repetición de la sesión | — | idéntica (función pura; 6 de 6) |
| 6 · mal formada y válida en el mismo minuto | 20 | `STARTED`, rechazada, rechazada |

**`PERMANENT_FAIL_CLOSED` (hoy):** seguridad alta (después de una ambigüedad no se infiere ningún estado); auditoría simple (una regla; la brecha nombra la primera orden rechazada); repetición determinista; semántica educativa conservadora (la persona que revisa sabe que la trayectoria ya no es de fiar); riesgo: la sombra **diverge** del motor el resto del encuentro, pero **lo dice**.

**`RECOVER_ON_LATER_EXPLICIT_VALID_ABSOLUTE_ORDER`:** una tasa absoluta explícita o una suspensión fijan un valor sin depender de la historia; pero **la continuidad del estado a través del hueco no es exacta** (la tasa que corrió el motor entre la orden mal formada y la de recuperación es desconocida para la sombra, y el soporte es un retardo de primer orden que arrastra ese error unos minutos); exigiría un evento nuevo (por ejemplo, «reanudada tras un hueco») y marcar el intervalo; cambiaría la repetición de las historias con rechazos y, por tanto, los registros históricos que las contienen (sólo registros sucesores); el riesgo de divergir en silencio de lo que corre el motor crece si el hueco no se declara.

**Recomendación (no implementada): mantener `PERMANENT_FAIL_CLOSED` en esta etapa.** Ninguna conducta actual crea un defecto de seguridad demostrado (la sombra no tiene autoridad sobre norepinefrina, es invisible para el residente y declara cada divergencia). Si la docencia quiere recuperar, la forma más conservadora es una recuperación **sólo** con una orden de suspensión o de tasa absoluta explícita, con el intervalo declarado como no espejado y una tolerancia de continuidad fijada por la docencia; es una decisión suya, no una consecuencia de este paquete.

## 11 · P3-459 · Revisión adversarial independiente (una sola)

Una persona revisora independiente de sólo lectura, sobre una copia del primer diseño (la guarda con vocabulario en el lector) y con sondas de extremo a extremo (lector → motor → espejo → sombra). **Cada hallazgo se reprodujo antes de actuar** (las sondas de la revisión se volvieron a ejecutar aquí con el mismo corpus) y se confirmó el mismo resultado. Su veredicto sobre el primer diseño: *no es seguro entregarlo como «un objetivo de presión nunca es una dosis».* Se reconoció y se rehízo (§6); **lo que sigue es la disposición de cada hallazgo sobre el diseño final**, que se midió contra el mismo corpus.

| Hallazgo | Qué dijo | Reproducido | Disposición |
|---|---|---|---|
| BLOCKER-1 | La guarda es una lista de palabras de presión; cualquier palabra que no esté (`TAM`, `PA`, `TAS`, `TAD`, «meta de 65», «hasta 65 de PAM», «65 (mmHg)», «entre 65 y 70 con norepinefrina», FC, CPP, IC) deja pasar el número como tasa: **121 630 de 1,65 millones** de frases generadas, y la nitroglicerina arrancaba a 120 mcg/min sin infusión previa | **Sí** | **Rediseñado, estructural (§6):** ninguna palabra. Contra el mismo corpus, **0 fugas en las 91 508 frases de norepinefrina, epinefrina y dobutamina**. Las 30 122 de nitroglicerina **no** se cubren (residuo declarado, §14). |
| MAJOR-2 | El cambio dejó en rojo la prueba del lector congelado y no se registró ninguna decisión | **Sí**; además, cinco pruebas de la congelación de calibración de la Fase 2 (`family_parser.py` está en su digesto) | **Revertido por completo** (`family_parser.py` idéntico al de la base). La pregunta de gobernanza se registra como decisión docente pendiente número 0 (§14); no se eligió en silencio. Las pruebas de congelamiento y de aislamiento están en verde. |
| MINOR-3 | Falsos positivos: «Continue norepinephrine since MAP goal is met», «Continue dobutamine with BP stable at 110/70», la anafilaxia con TA 70/40 y «increase to 10 gamma for the pressure goal» se retenían con un mensaje engañoso | **Sí** | Las **continuaciones sin tasa** y la anafilaxia ya **no se retienen** (la regla sólo mira una tasa sin unidades; sin número no hay nada que retener): sin cambio frente a la base. «Start epinephrine for SBP 70» sigue retenida (un número sin unidades), con el mensaje nuevo. **«…to 10 gamma…» sigue retenida** porque el lector no lee «gamma» como unidad: es la misma regla («un número sin unidades»), un efecto declarado (§7, §14), no un falso positivo de objetivo. |
| MINOR-4 | Mutantes que sobreviven: `bp`, `dbp`, `pad`, `mean arterial`, la alternativa `mmHg`, `objetivo`, el agente y la operación de la marca | **Sí**, para ese diseño | **Mudos para el diseño final:** no hay vocabulario. Se escribieron **13 mutantes nuevos sobre la regla final** y los **13 fueron detectados** (quitar la guarda; quitar la exención de la suspensión; precedencia de las unidades explícitas; conservar el número en la copia retenida; dejar el inicio al motor; no cubrir dobutamina, epinefrina ni la orden por el rol; retener una orden relativa sin número; quitar la regla en español; no preguntar; no retener; descartar la orden retenida). |
| NOTE-5 | Una orden relativa sin número («Increase norepinephrine»), el peso (mcg/kg/min, que el motor convierte y la sombra no) y «Increase norepinephrine to 12» | **Sí** | La orden relativa sin número y el peso **no cambian** (caracterización, §14). «…to 12» (un número sin unidades) **ahora se retiene**: es la misma raíz que BLOCKER-1 y se declara. |
| NOTE-6 | El mismo minuto, `repeat_order`, la orden diferida, mal formada y luego válida: **no se falsó** | — | Sin acción. Las divergencias sólo aparecían en las frases que se filtraban (BLOCKER-1) y eran declaradas, no silenciosas. |
| NOTE-7 | Sin cambios fuera de los archivos declarados; digesto del núcleo `867bac09…`; `COMMON_CORE_RUNTIME_AUTHORITY = False` | — | Sin acción; se repite con el diseño final (§12). |
| NOTE-8 | Registros: sólo cinco juicios globales, sin identidad ni marcas de tiempo, sin modelo ni correo; dos observaciones menores de redacción (`NONE_REPORTED` puede leerse como «no existen», no «no reportados»; `executable_change: false` en un registro anterior a la reparación) | — | **Sin cambio**: la lista `not_verified` del registro dice «no se reportaron» y el registro está fechado en la ratificación (antes de la reparación; la reparación la registra el punto de control). Un registro generado es inmutable. |

**Qué nos enseñó:** el hallazgo más valioso fue el de gobernanza, no el de cobertura: el primer diseño acertaba en el defecto y fallaba en dónde se tocaba. Las pruebas focalizadas, escogidas por búsqueda de texto, no incluían las guardas de congelamiento; ahora se corren siempre que se toca un módulo raíz (§12).

## 12 · P3-460 · Certificación

**Dos corridas completas, una huella cada una; nunca se mezclaron cifras.**

| Corrida | Huella | Pruebas | Fallas | Errores | Omitidas | Resultado |
|---|---|---|---|---|---|---|
| 1 · no es la final | `77960017ffc3` | 13 798 | **1** | 0 | 100 | regresión de este cambio (abajo) |
| 2 · **final** | `b625a7e66060` | **13 798** | **0** | **0** | 100 (1 xfail) | **válida**: huella igual al inicio y al final, 24 particiones, sin reanudaciones, 06:41 a 09:01 UTC |

*Regresiones (`run_regressions.py`), corrida final:* **56/56 activas** aprobadas; 10 retiradas (se conservan, no se ejecutan: `RETIRED_REGRESSIONS`).

**La falla de la primera corrida, con evidencia.** `test_hypoglycemia_battery.py::test_the_published_catalogue_is_the_one_the_code_produces`: `docs/CATALOGO_HIPOGLICEMIA.md` se **genera** desde el registro de correcciones, y la entrada nueva `C-2026-11-20-01` no estaba en él. **Clasificación: regresión de este cambio** (reproducida aislada; la diferencia frente al generador es exactamente una línea, la fila nueva). *Corrección mínima:* se regeneró el catálogo con su propia herramienta (`python3 tools_hypoglycemia_catalog.py`), nada a mano; una huella nueva y **una** certificación completa nueva. *Por qué no la vio el conjunto focalizado:* se eligió por búsqueda de texto y la prueba del catálogo generado vive en un archivo de nueve minutos que no estaba en él. Lección: toda entrada nueva del registro de correcciones exige regenerar el catálogo y correr esa prueba.

**Antes de congelar:** conjunto relacionado con el lector y el motor, 70 archivos, **3 236** pruebas aprobadas; 19 archivos de guardas (congelamientos, contrato, aislamiento, documentos, registro, registros históricos), **717** aprobadas y 5 omitidas; regresiones 56/56; **86** pruebas nuevas; **13** mutantes sobre la regla, los 13 detectados, sobre una copia (el árbol no se mutó nunca). `family_parser.py`, `family_engine.py` y `active_order_context.py` idénticos a la base; digesto del núcleo `867bac09…`.

**Después de certificar** se añadieron sólo: el registro del punto de control, su entrada en el índice y el pin del índice en `test_phase3_historical_record_versioning.py`, las secciones 12 y 13 de este documento y la fila FD-P3-284 (nada ejecutable). Sobre el árbol final se repitieron las pruebas que los leen: las 19 archivos de guardas (congelamientos, contrato, aislamiento, documentos, registro de correcciones, deuda, registros históricos y su índice, el punto de control y el catálogo generado de hipoglucemia): **719 aprobadas, 3 omitidas, 0 fallas** (las dos pruebas del punto de control, antes omitidas, ya se ejecutan).

*No se ejecutó:* un navegador (no cambió ninguna página: el paso por el turno es la ruta propia de la página y lo cubren las pruebas con el encuentro real); `validation/` ni ninguna respuesta externa (congelados, no se abrieron).

## 13 · P3-461 · Punto de control

**A · `MANUAL_NOREPINEPHRINE_SEMANTICS_RATIFIED_AND_TARGET_ORDER_BUG_FIXED`**

La semántica de control manual de tasa de norepinefrina (iniciar, aumentar, disminuir, suspender y reiniciar con tasas absolutas en mcg/min) queda **ratificada sólo para desarrollo**; el defecto «objetivo ≠ tasa» está **reproducido, rastreado, clasificado y reparado** antes del motor, sin tocar nada congelado; la frontera de la sombra es la de la orden cruda (veredicto A) y no se inventó ningún contrato nuevo del espejo; la política ante una orden mal formada no se cambió. Registro: `docs/revision/PHASE3_NOREPINEPHRINE_TARGET_ORDER_CHECKPOINT.json` (sellado, versionado, indexado).

*Por qué no los otros cinco:* **B** no, porque la auditoría de frontera dio A (nada de la frontera segura queda sin resolver); **C** no, porque el cambio es una regla estructural en el paso por el turno, el lector genérico no se tocó (está congelado), ninguna otra familia de órdenes cambió y levantar el congelamiento del lector es una decisión docente que **no bloquea** esta reparación; **D** no, porque la elección entre orden cruda y resuelta no está abierta en esta etapa (todas las divergencias medidas son huecos de fidelidad declarados, no defectos de seguridad); **E** no, porque ninguna conducta ante una orden mal formada crea un defecto de seguridad demostrado; **F** no, porque el modelo de órdenes no necesitó rediseño.

**Confirmaciones.** Sin recalibración del tono; sin cambio del acoplamiento con la bomba; sin fisiología nueva; sin ampliación de la autoridad de norepinefrina; sin autoridad de consciencia ni terminal; sin despliegue a residentes; sin afirmación de validación clínica. Tampoco: sin parámetro elegido ni testigo sustituido, sin dosis por peso, sin titulación por objetivo de PAM, sin otro vasopresor, sin cambio de la recuperación tras una orden mal formada, sin contrato nuevo del espejo compartido. `COMMON_CORE_RUNTIME_AUTHORITY = False`.

**Lo que queda abierto y no es de este paquete** (§14): la decisión número 0 (levantar el congelamiento del lector para reparar en la fuente, lo que cubriría también la nitroglicerina, que **sigue sin cubrirse** y es el residuo de seguridad pendiente); si la sombra sigue las órdenes que el motor resuelve; si se recupera tras una orden mal formada; el verbo «restart», la orden relativa sin número y la abreviatura «increase to 12»; la aprobación del texto en español; la verificación del almacén de la revisión humana.

**Siguiente acción de desarrollo, una sola:** que la docencia decida el congelamiento del lector (decisión 0 de §14). Hasta entonces no se hace nada más (norepinefrina por peso, titulación por objetivo de presión, otro vasopresor y los dominios de FD-NR-04 sólo con autorización expresa).

## 14 · Limitaciones y decisiones pendientes

**Sin cambio, ya declarado:** no hay titulación por objetivo de PAM, dosis por peso, órdenes relativas sin contexto ni otro vasopresor (FD-NR-04); la consciencia bajo tono y la dependencia de la bomba siguen abiertas; el cierre persistente ante una orden mal formada sigue (FD-NR-07); el motor heredado sigue convirtiendo mcg/kg/min por peso y completando las unidades de una tasa declarada **con** unidades parciales.

**Hallazgo de seguridad que NO se repara (residuo declarado): la nitroglicerina.** La nitroglicerina lleva su única unidad en el nombre del campo (`rate_mcg_min`), de modo que el paso por el turno no distingue un número suelto de una tasa explícita: «titrate nitroglycerin to SBP 120» sigue leyéndose, en el lector congelado, como 120 mcg/min, y «start nitroglycerin for TAS 120» arranca a 120 mcg/min sin infusión previa (30 122 de las 121 630 frases del corpus del revisor son de nitroglicerina). Es **anterior** a este ciclo, está **fuera** del encargo (norepinefrina) y su reparación está en el lector congelado (prueba `t18`, que registra el residuo y debe cambiar cuando se repare).

**Descubierto en este ciclo y no cambiado (caracterización con prueba):**
1. **El verbo «restart» no lo lee el intérprete (congelado)** («restart norepinephrine at 10 mcg/min» se retiene como orden no reconocida, sin dosis). El reinicio soportado es el inicio explícito tras suspender, que es lo que hicieron los cinco escenarios revisados.
2. **«Increase norepinephrine» sin ningún número**: el motor la completa con la tasa en curso («ajustada a 10 mcg/min» sin cambio real); no se adivina ninguna tasa, pero tampoco se avisa. La sombra la rechaza y lo declara. (Con un número sin unidades, ahora se pregunta.)
3. **Una orden de infusión con un número sin unidades se retiene** aunque antes sólo se preguntara por las unidades («start norepinephrine, MAP 58»): ambos son una retención; cambia el mensaje y que la copia retenida no conserva el número.
4. **El texto del mensaje en español** es una redacción de desarrollo coherente con las reglas vecinas; **no** está aprobada por la docencia (`TD-46`).
5. **El lector sigue emitiendo el número como tasa** sin unidades (`rate 65, units None`): la reparación está después, no en la fuente. Repararlo en la fuente (que además cubriría la nitroglicerina) exige levantar el congelamiento del lector y seguir el procedimiento de enmienda de la congelación de calibración: decisión docente.

**Decisiones docentes pendientes:**
0. **Primera: el congelamiento del lector.** El encargo pide reparar el defecto del intérprete y `CLAUDE.md` congela el lector hasta que la validación externa avance: no se eligió en silencio. Se reparó fuera del lector (§6). Si la docencia quiere la reparación **en la fuente** (que cubriría también la nitroglicerina), debe decidir levantar el congelamiento para ese cambio, actualizar la prueba del lector y recertificar la congelación de calibración.
1. Si la sombra debe seguir órdenes que el motor resuelve (suspensión sin nombrar el fármaco, tasa sin unidades): decisión **arquitectónica** (híbrido con procedencia en el espejo compartido), no tomada.
2. Si se recupera tras una orden mal formada, y con qué tolerancia (§10).
3. Si se le enseña al intérprete el verbo «restart», si «increase norepinephrine» sin ningún número debe pedir la tasa y si la abreviatura «increase to 12» (sin unidades) debe volver a aceptarse.
4. La aprobación de la redacción en español del mensaje nuevo.
5. Qué sigue en el desarrollo (norepinefrina por peso, titulación por objetivo de presión, otro vasopresor y los dominios de FD-NR-04) sólo con autorización expresa.
