# Fase 3 · Endurecimiento final de la seguridad de las órdenes vasoactivas (P3-474 a P3-487)

Encargo del 2026-11-21. Rama `phase-3-runtime-integration`; punto de partida `08b9873` (punto de control A del ciclo anterior); linaje `PHASE2_AMENDMENT_3` (certificado, digesto `867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c`, **sin cambio**); concesión viva `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3` (sin cambio).

**Qué se hizo, en una frase.** Se cerraron las conductas **demostradas** del ciclo anterior (L-1 a L-8 de `TD-161`) por las que una orden vasoactiva podía ejecutar una tasa equivocada, atribuir la tasa de otro fármaco, suspender la infusión equivocada, volverse ejecutable estando incompleta o saltarse la defensa en profundidad: **una tasa y una suspensión pertenecen a un solo fármaco**, la unidad se exige y se compara con la del fármaco, el «/min» de una tasa no es una duración, `restart`/`continue` sin tasa explícita son la pregunta aprobada, la barrera posterior lee el campo `rate_mcg_min` y la respuesta suelta a «¿qué tasa?» nunca es una tasa. **No** es un rediseño del lector: es la **última** endurecida planeada de este tipo antes de volver a la autoridad y al desarrollo del simulador.

El lector (`family_parser.py`) cambió por **segunda** vez bajo el levantamiento acotado de su congelamiento; ahora hay **tres** lectores (el del cierre de la Fase 2, el del primer sucesor y el vivo), cada uno reconstruible por sí solo, y ningún registro sellado se reescribió (§10).

## 0 · Decisiones docentes (2026-11-21; FD-ORDER-01 a FD-ORDER-11)

| Id | Decisión |
|---|---|
| FD-ORDER-01 | **L-1 · compatibilidad de unidades.** Una orden vasoactiva es ejecutable sólo si la atribución del fármaco es válida **y** la tasa es explícita **y** la unidad es explícita **y** la unidad está soportada para ese fármaco; en cualquier otro caso, falla cerrado. Un ajuste «de la infusión» nunca asume mcg/min. |
| FD-ORDER-02 | **L-2 · propiedad de la tasa.** Una tasa nunca se atribuye entre fármacos. Pertenece a lo más a un fármaco y su atribución se justifica **estructuralmente**; sin heurística del número más cercano; la ambigüedad se pregunta. |
| FD-ORDER-03 | **L-3 · propiedad de la suspensión.** Una suspensión heredada de una lista, un paquete, una cláusula previa o un fármaco vecino no suspende un vasoactivo a menos que se le atribuya sin ambigüedad; lo ambiguo falla cerrado. |
| FD-ORDER-04 | **L-4 · «/min» diferido.** El «/min» de una orden diferida o ajena no se lee como duración ni como otro campo que vuelva ejecutable una orden vasoactiva; la lectura explícita y válida de unidades de tasa se conserva; sin rediseño amplio de la gramática. |
| FD-ORDER-05 | **L-5 · `restart` sin tasa.** `restart norepinephrine` sin tasa absoluta explícita y soportada es el texto aprobado de tasa incompleta («La orden especifica un objetivo o una tasa incompleta. Indique una tasa explícita con sus unidades para continuar.»); no reutiliza la tasa anterior; no ejecuta. |
| FD-ORDER-06 | **L-6 · `continue` con un número.** `continue norepinephrine at 12` es tasa incompleta (pide unidades); `… at 12 mcg/min` es válida. |
| FD-ORDER-07 | **L-7 · defensa en profundidad.** La barrera posterior entiende `rate_mcg_min`; la nitroglicerina deja de depender sólo del lector. Sin cambio de fisiología y sin esquema genérico nuevo. |
| FD-ORDER-08 | **L-8 · respuesta numérica.** La respuesta de sólo un número a una pregunta de dosis o tasa nunca es una tasa vasoactiva ejecutable; se exige tasa explícita **y** unidad soportada; la unidad nunca se infiere de la infusión en curso, de una orden previa, de la redacción de la pregunta ni de la unidad habitual del fármaco. |
| FD-ORDER-09 | `PERMANENT_FAIL_CLOSED` sigue para la sombra tras una orden mal formada o no soportada; sin recuperación. |
| FD-ORDER-10 | `RAW_ORDER_REMAINS_CORRECT_BOUNDARY` sigue para el espejo compartido; sin híbrido crudo/resuelto. |
| FD-ORDER-11 | **Fuera de alcance:** titulación automática por PAM/PAS, conversión mcg/kg/min, aritmética relativa, otro vasopresor u otro fármaco, fisiología específica de la bomba, recalibrar el tono, ampliar la autoridad. |

El mandato incluye una **detención dura** tras P3-487: no se siguen cazando casos límite de bajo riesgo tras el cierre.

## 1 · P3-474 · Los ocho reproductores, antes de tocar código

Todos pasan por el camino **real** (lector → semántica del tiempo → paso por el turno → motor), con un encuentro de sangrado digestivo y las infusiones indicadas **ya en curso**. «Antes» es el árbol de `08b9873`.

| Id | ENTRADA | LECTURA (antes) | ACCIÓN DEL MOTOR (antes) | RESULTADO DESEADO |
|---|---|---|---|---|
| L-1 | nitroglicerina 20 mcg/min en curso; `increase the infusion to 40 mL/h` | `infusion_adjustment`, `rate_value 40`, `rate_units ml/h` | **ejecuta**: nitroglicerina 20 → **40 mcg/min** (la unidad se descarta al completarla) | no ejecuta; pregunta de tasa incompleta; sigue en 20 |
| L-2 | NE 10 mcg/min en curso; `titrate norepinephrine to MAP 65 with propofol 5 mcg/min` | NE, `rate 5`, mcg/min | **ejecuta**: NE 10 → **5 mcg/min** (la tasa del propofol) | no ejecuta; la NE sigue en 10; pregunta |
| L-3 | NE 10 en curso; `stop NS, norepinephrine to MAP 65` | `fluid stop` + **`norepinephrine stop`** | **suspende** la NE (10 → 0) | sólo se suspende el suero; la NE se pregunta |
| L-4 | NE 10 en curso; `increase norepinephrine to 12 mcg/min in 5 minutes` | NE ajustada a 12 (la duración leyó «/min») | **ejecuta ahora** (10 → 12) | no ejecuta ahora; plan diferido registrado |
| L-5 | `restart norepinephrine` | inicio sin tasa | pregunta **del motor** («Specify or confirm … dose and units»), no el texto aprobado | texto aprobado de tasa incompleta; sin ejecutar ni reutilizar la tasa |
| L-6 | NE 10 en curso; `continue norepinephrine at 12` | `continue` **sin número** (el 12 se perdía) | «ejecuta» sin mensaje: continúa en 10 en silencio | tasa incompleta (pide unidades); `… at 12 mcg/min` válida |
| L-7 | `nitroglicerina para PAS 120` / `nitroglycerin 20` con el lector **histórico** delante | `nitroglycerin`, `rate_mcg_min 120` / `20` | **ejecuta** 120 y 20 mcg/min: la barrera posterior sólo miraba `rate`/`rate_value`/`units` | la barrera posterior sostiene sola: no ejecuta |
| L-8 | respuesta «12» a «¿qué tasa de norepinefrina?» en la ruta heredada de la página | el 12 se aceptaba como tasa con la unidad habitual del fármaco | tasa ejecutable sin unidad escrita | pregunta de nuevo; nunca una tasa |

(Las líneas exactas de cada reproductor, con la orden leída y la acción del motor, viven en `test_phase3_order_safety_hardening.py`; los cuatro estados de L-2, L-3, L-6 y L-7 están además en el registro sellado, §10.)

## 2 · P3-475 · El contrato de propiedad fármaco–tasa–unidad–acción

Una **pieza** de la orden es el trozo que el lector lee por separado (se parte en comas, «and», «y», «+», «then»; la acción puede heredarse de una lista). Contrato, estructural y sin vocabulario por fármaco:

- **Tasa.** Una pieza que **no nombra otro medicamento** conserva su tasa como siempre. Si nombra otro, un número escrito con unidad de tasa pertenece **al fármaco nombrado justo antes**, sólo a través de los **conectores de una dosis** (`at`, `to`, `a`, `de`, `rate`, `dose`, `infusion`, `drip`, `iv`, `up`, `hasta`, `titrated`, `for`, puntuación), o **después** de su nombre con «of <fármaco>». Un número que **otro** fármaco reclama, o que **nadie** reclama, retiene la pieza **entera** (la pregunta aprobada de «una sola tasa absoluta»): no se ejecuta nada ni se pierde en silencio la orden del otro medicamento. Sin «el número más cercano por distancia».
- **Unidad.** Una tasa es ejecutable sólo con unidad explícita y soportada **para ese fármaco** (§3).
- **Suspensión.** Una suspensión gobierna un vasoactivo sólo si el verbo está escrito **en su pieza y sin excepción entre el verbo y su nombre** («stop all except norepinephrine», «stop NS but keep norepinephrine», «stop NS, not norepinephrine» no la suspenden), o si la pieza es **sólo el nombre** (más artículos y la palabra «infusion») dentro de una lista que el verbo distribuye («stop NS, norepinephrine»). Una pieza que dice **más** («norepinephrine to MAP 65», «norepinephrine at 12») no hereda el verbo: se lee como lo que es, y pide su tasa.

La lista de nombres de otros medicamentos que usa el lector es **sólo de reconocimiento** (no da soporte ni tasa a ninguno): le permite ver que una pieza nombra a otro.

## 3 · P3-476 · Guarda de compatibilidad de unidades (L-1)

- **Lector.** Un ajuste nombrado sólo por su papel («la infusión», «el goteo») ya no entrega el número cuando éste está escrito en una unidad que ninguna infusión vasoactiva corre (p. ej. mL/h) ni cuando la pieza lo comparte con otro medicamento: la acción queda como ajuste **sin tasa**, y el paso por el turno la retiene con el texto aprobado.
- **Paso por el turno.** La regla de unidades (`order_pipeline`) retiene un ajuste por papel cuya unidad no es una que el fármaco en curso corre: sólo `mcg/min` y `mcg/kg/min`, y `mcg/kg/min` **no** para la nitroglicerina. Una suspensión y un ajuste sin tasa no se tocan por esta regla. La copia retenida no conserva el número.
- **Página heredada (`app.py`).** La respuesta de sólo un número a «¿qué dosis?» ya no toma la unidad de la infusión en curso ni la habitual del fármaco (§8).

## 4 · P3-477 · Atribución de la suspensión (L-3)

Implementada como se describe en §2. Se conserva: `stop norepinephrine`, `stop the norepinephrine infusion`, `suspende la noradrenalina`, `stop norepinephrine and nitroglycerin`, `stop NS, norepinephrine`, `stop nitroglycerin, norepinephrine`, `discontinue …`, y una suspensión con una **razón** («stop norepinephrine because MAP is not low», «… to keep MAP above 65») sigue suspendiendo la infusión. Se **declara** la consecuencia: las excepciones («stop NS but keep norepinephrine») son ahora una orden **no reconocida** (se pregunta), no una suspensión.

*Corrección tras la comparación con el corpus generado:* la primera versión de la clase de excepciones leía «keep» en una **finalidad** posterior al nombre («stop norepinephrine to keep MAP above 65») y la dejaba «no reconocida»; la excepción sólo cuenta **antes** del nombre (entre el verbo y su objeto). Quedó cubierta por pruebas y por un mutante.

## 5 · P3-478 · El «/min» de una orden diferida (L-4)

`time_semantics._runs_for_a_duration` aparta la unidad de tasa («mcg/min», «mg/h», «mcg per minute») **sólo** en una cláusula que nombra uno de los cuatro vasoactivos y **sólo** para la prueba de duración: `increase norepinephrine to 12 mcg/min in 5 minutes` queda como plan diferido y la infusión no cambia. La unidad de otras órdenes **no** se aparta (`give diltiazem 10 mg/h in 5 minutes` conserva su `/h`). Una orden con duración propia («over 5 minutes») se lee como antes.

## 6 · P3-479 · `restart` y `continue`

| Orden | Resultado |
|---|---|
| `restart norepinephrine` / `resume …` / `reinicia la noradrenalina` (sin tasa) | texto aprobado de tasa incompleta; sin ejecutar; sin reutilizar la tasa anterior |
| `restart norepinephrine at 10 mcg/min` | inicio válido a 10 |
| `restart norepinephrine at 10` | tasa incompleta (unidad) |
| `continue norepinephrine` | continúa como antes |
| `continue norepinephrine at 12` | tasa incompleta (pide unidades); la tasa en curso no se toca |
| `continue norepinephrine at 12 mcg/min` | válida: 12 |
| `continue norepinephrine for 5 minutes` / `… in 5 minutes` | como antes |
| `increase norepinephrine` / `increase norepinephrine to 12` / `to MAP 65` | tasa incompleta (como en el ciclo anterior) |
| `increase norepinephrine to 12 mcg/min` | válida |

La matriz completa se ejecuta por el encuentro real en `test_p3_479_the_whole_increase_restart_continue_matrix_in_the_real_encounter`.

## 7 · P3-480 · La barrera posterior entiende `rate_mcg_min` (L-7)

`order_pipeline.incomplete_explicit_rate(action, text, state)` lee ahora también `rate_mcg_min`: el número debe estar **escrito con una unidad de masa por tiempo** (mg ×1000, por hora ÷60, nunca por kilo) en una **cláusula que nombra a ese fármaco** (`order_ledger._clauses`), no en la de otro medicamento. La copia retenida no conserva el número. Con ello la nitroglicerina deja de ser «sólo la fuente»: **cada barrera protege sola** (barrera posterior sola, con el lector del cierre delante; lector solo, con la barrera posterior quitada). Sin esquema genérico nuevo y sin cambio de fisiología.

## 8 · P3-481 · La respuesta de sólo un número (L-8)

La ruta heredada de la página (función suelta, `app.py`) ya no completa una pregunta de dosis con un número: la norepinefrina exige tasa **y** unidad; la dobutamina, que no tenía un valor por omisión de número suelto, también. Se prueban `12`, `12 mcg/min`, `0.1 mcg/kg/min`, `MAP 65`, `stop` y `restart at 10 mcg/min`; una respuesta suelta en el encuentro real no es una orden de ninguna infusión.

## 9 · P3-482 · Las órdenes válidas se leen y ejecutan exactamente como antes

Guiones de órdenes válidas (inicio, aumento, reducción, suspensión, reinicio por tasa explícita, nitroglicerina, epinefrina, dobutamina, las cinco secuencias de titulación ratificadas) se ejecutan **paso a paso con el mismo estado del motor** bajo el lector vivo y bajo el lector del primer sucesor (y, para lo que éste leía, bajo el del cierre): **sin deriva numérica**.

## 10 · P3-483 · Sucesión histórica: tres lectores, cada uno reconstruible por sí solo

`family_parser.py` es una de las 35 fuentes de la congelación de calibración de la Fase 2 (`clinical_core.calibration.INPUT_PATH_SOURCES`) y el digesto se calcula sobre sus **bytes**. La docencia levantó su congelamiento **dos veces**, cada una sólo para una corrección de seguridad acotada (FD-TARGET-01, 2026-11-20; FD-ORDER-01 a 11, 2026-11-21). El lector tiene, por tanto, tres estados, todos conservados:

| Estado | Identidad (blob de git) | Lo fija |
|---|---|---|
| 1 · Cierre de la Fase 2 | `1d17bf8b3dce66da5f1c8291237e2e7a7afde1c0` | el congelamiento previo a la Fase 1 y los digestos del cierre y de los baselines V3 |
| 2 · Primer sucesor (objetivo ≠ tasa) | `7a85714eb2b6fccb47507384a71fe91451e71ecb` | `PHASE3_READER_SUCCESSION_TARGET_SAFETY.json` (sellado; **no se regenera**) |
| 3 · Segundo sucesor (este ciclo) | el archivo vivo | `test_prephase1_reader_freeze.py` (`EXPECTED_BLOBS`) y `PHASE3_READER_SUCCESSION_ORDER_SAFETY.json` |

Mecanismo (el precedente de las enmiendas: hunks reversibles declarados), **compuesto**: `REVERSAL_ORDER_SAFETY` lleva el archivo vivo al estado 2 y `REVERSAL` lleva el estado 2 al estado 1; cada etapa se prueba contra su identidad fijada y **ninguna depende de que un registro se vuelva a generar**. `reader_succession.py` ofrece los bytes y el módulo ejecutable de cada lector anterior (`target_safety_reader_*`, `historical_reader_*`: corren como módulos aparte y **nunca** reemplazan a `family_parser` en `sys.modules`) y las vistas con que todo digesto de la Fase 2 —y todo digesto construido sobre ellos— se recalcula con el lector de su época, **dentro** de `clinical_core.amendment_3.closure_view()`. `clinical_core/` **no se editó** y ningún registro sellado se reescribió. El primer registro se sigue regenerando idéntico porque su constructor lee el primer sucesor desde su propia vista reconstruida.

El digesto de calibración se movió en **un** solo componente (`input_path_sources`, el hash del lector); las entradas materializadas de los escenarios **no** se movieron y la lista de fuentes de la ruta de entrada no cambió. El segundo registro sellado (`docs/revision/PHASE3_READER_SUCCESSION_ORDER_SAFETY.json`, indexado) muestra lado a lado la lectura de los tres lectores para los textos relevantes.

## 11 · P3-484 · Corpus y revisión adversarial independiente

**Una** revisión adversarial independiente (agente de sólo lectura que no escribió el cambio, sobre una **copia** del árbol, sin abrir `validation/` ni `faculty_review*`), con los reproductores y los corpus propios del revisor. Cada hallazgo material se **reprodujo sobre el árbol vigente antes de corregirlo** (el revisor trabajó sobre una copia anterior al arreglo de «keep»: F04 ya estaba resuelto en el árbol).

**Cifras del revisor.** 26 779 textos únicos (1 339 literales extraídos de las pruebas del propio repositorio); ≈ 81 000 casos generados (≈ 200 000 evaluaciones de lectura y motor); 5 921 diferencias entre el lector vivo y el del primer sucesor, clasificadas: tasa de otro fármaco 2 331, atribución de la suspensión 2 270, reinicio/continuar/número sin unidad 330, diferido que ahora es plan 976, **14 sin explicar** (todas en F06). **Conclusión del revisor: ninguna ejecución nueva insegura**: el lector vivo nunca suspende un fármaco que el primer sucesor no suspendiera, nunca emite una tasa que no emitiera y nunca cambia una orden que no sea vasoactiva; la barrera posterior y el cambio de la semántica del tiempo sólo pueden **quitar** ejecución; la tasa explícita válida (250 guiones de 4 fármacos en inglés y español) se ejecuta idéntica. Por mi parte, el corpus generado propio (83 894 textos) y el minado (1 486 textos) quedaron sin una sola diferencia sin explicar, y la lectura con la barrera desactivada no filtró ninguna tasa (3 000 textos).

| Hallazgo | Clase | Reproducido sobre el árbol | Disposición |
|---|---|---|---|
| **F01** · la respuesta «20 mcg/min» a «¿qué tasa de nitroglicerina?» se rechazaba para siempre | regresión de este cambio (ALTA) | sí | **reparado**: la continuación que la página añade a la orden retenida («Clarification: …») cuenta como evidencia si **no nombra a otra infusión** |
| **F02** · «µg/min», «μg/min», «micrograms/min», «microgramos/min» de nitroglicerina retenidos | regresión de este cambio (MEDIA) | sí | **reparado**: el signo micro es una letra para la barrera y «micrograms/microgramos» son unidad de masa |
| **F03** · «… to reach MAP 65 in 10 minutes» pasó a plan diferido | cambio de lectura (conservador) | sí | **declarado**: no se ejecuta nada y el plan queda registrado; no se puede distinguir «meta en el tiempo» de «orden para después» sin semántica nueva |
| **F04** · una suspensión se perdía con «but/keep/leave/pero…» tras el nombre | regresión (BAJA-MEDIA) | **ya resuelto** | resuelto por el arreglo de «keep» (la excepción sólo cuenta **antes** del nombre); se añaden las frases del revisor a las pruebas |
| **F05** · una orden válida con una palabra que no es de dosis más otro medicamento se pregunta como ambigua | regresión (BAJA) | sí | **declarado**: falla cerrado y pregunta (la regla es estructural); sin cambio |
| **F06** · «espera 5 minutos y luego reanuda dobutamina» (y «resume adrenalina without salbutamol 5 mcg/min») **desaparecía sin acción ni pregunta ni registro** | regresión (BAJA-MEDIA) | sí | **reparado**: la pregunta de tasa incompleta (o la de una sola tasa) de una parte diferida se conserva, y el reinicio con pregunta de propiedad se lee como infusión; sale la pregunta, nada se ejecuta |
| **F07** · «stop all except dobutamine and norepinephrine» suspendía la última de la lista | previo, **parcial** del L-3 (ALTA) | sí | **reparado**: una excepción termina la suspensión heredada para las piezas que siguen |
| **F08** · una suspensión que nombra dos infusiones («stop norepinephrine while dobutamine continues») suspendía la que va primero en la prioridad fija del lector | previo (ALTA) | sí | **reparado**: la pieza que nombra dos infusiones no se lee y se pregunta |
| **F09** · la propiedad de la tasa depende de una lista cerrada de nombres: «NTG», «GTN», «NE», «levo», treprostinilo, epoprostenol, efedrina… | previo, **parcial** del L-2 (ALTA) | sí | **reparado en lo demostrado y declarado en lo estructural**: se amplía el reconocimiento (los otros nombres de las cuatro infusiones y varias decenas de medicamentos más); sigue siendo una **lista cerrada** (L-11) |
| **F10** · «start norepinephrine 12 mcg/min of propofol» | previo (MEDIA) | sí | **reparado**: «… of <fármaco>» decide antes que el nombre anterior |
| **F11** · las respuestas: «dobutamine 12 mcg/min» a la pregunta de norepinefrina completaba 12; la ruta heredada tomaba el primer literal; «12 mcg/min in 5 minutes» corría ahora | previo (MEDIA-ALTA) | sí | **reparado** en las dos rutas: la respuesta es **una** tasa con su unidad, para el fármaco que preguntó y sin tiempo de espera; si no, se vuelve a preguntar |
| **F12** · el «/min» diferido: «infusion», el alias «epi», el signo micro, «per kg per minute», la infusión por papel; y los giros de tiempo genéricos | previo (MEDIA-ALTA) | sí | **reparado** lo que pertenece al «/min» y a los nombres de las infusiones; **declarado** el resto (L-12): «después de», «luego de», «in 5 minutes,» con coma, «wait 5 minutes then», «in five minutes», «later» son giros del sistema de tiempo común a todas las órdenes |
| **F13** · «nor-epi» y «nor epi» se leían como epinefrina | previo (MEDIA) | sí | **reparado**: nunca epinefrina; la orden se pregunta (no se lee como norepinefrina: no se añade vocabulario) |
| F14 · la barrera posterior sola no hace cumplir la propiedad de una tasa explícita | nota | sí | **declarado**: la propiedad es del lector (L-2, una sola capa); la barrera posterior ya detiene objetivos, números sin unidad y unidades |
| F15 · «to MAP 65 max 20 mcg/min» ejecuta 20 (techo/paso/base como tasa) | previo (nota) | sí | **declarado** (L-13): es una decisión docente de semántica |
| F16 · mg/min, mg/h y mcg/h se convierten | — | — | **no es un defecto**: conversión de masa/tiempo explícita |
| F17 · «2 mcg/min more» se lee como absoluta | previo (nota) | sí | **declarado**: aritmética relativa, fuera de alcance (FD-ORDER-11) |

También se reproduce y se **declara** lo que el revisor anotó de pasada: «restart X in 5 minutes» ahora se pregunta en vez de quedar como plan, «stop X then Y» también suspende Y, «levophed 12» y «epi 12» no se leen y, para lo que **no es vasoactivo**, «stop all except propofol» suspende la sedación (previo; no es vasoactivo y no se toca).

**Pruebas añadidas por la revisión:** una por hallazgo reparado (`test_f01` … `test_f13` en `test_phase3_order_safety_hardening.py`), cada una probada en el encuentro real.

## 12 · P3-485 · Auditoría de cierre de L-1 a L-10 (y de lo que la revisión añadió)

Un solo estado por limitación: `CLOSED`, `MITIGATED_BY_DEFENSE_IN_DEPTH` o `INTENTIONALLY_DEFERRED`. **L-9 ya no significa «sólo la fuente»**: la barrera posterior lee `rate_mcg_min` y la nitroglicerina queda protegida por dos capas independientes. El registro sellado del punto de control (§14) repite esta tabla.

| Id | Estado | Qué quedó |
|---|---|---|
| **L-1** | `CLOSED` | un ajuste por papel corre sólo en una unidad que una infusión vasoactiva corre (el lector retira el número; la regla del paso por el turno sobre las formas estructuradas); mL/h sobre nitroglicerina ya no corre como mcg/min |
| **L-2** | `CLOSED` (formas demostradas) | una tasa pertenece a un solo fármaco; el reconocimiento de otros medicamentos es una **lista cerrada** → residuo **L-11** |
| **L-3** | `CLOSED` | la suspensión gobierna un vasoactivo sólo si el verbo gobierna su nombre; ni heredada por una pieza que dice más, ni por una excepción (que además termina la suspensión para las piezas siguientes), ni elegida por prioridad entre dos infusiones |
| **L-4** | `CLOSED` (el «/min») | el «/min» de una tasa vasoactiva y la palabra «infusion» que la nombra no son una duración; los giros de tiempo genéricos son el residuo **L-12** |
| **L-5** | `CLOSED` | `restart` sin tasa: texto aprobado; la tasa anterior nunca se reutiliza |
| **L-6** | `CLOSED` | `continue … at 12`: texto aprobado; `… at 12 mcg/min`: válida |
| **L-7** | `MITIGATED_BY_DEFENSE_IN_DEPTH` | la barrera posterior lee `rate_mcg_min`; cada barrera protege **sola** (probado con la otra quitada y por mutantes) |
| **L-8** | `CLOSED` | la respuesta es **una** tasa con su unidad, del fármaco que preguntó, sin otro medicamento ni tiempo de espera, en la ruta de familias y en la ruta heredada de la página |
| **L-9** | `MITIGATED_BY_DEFENSE_IN_DEPTH` | la nitroglicerina deja de depender de la fuente sola |
| **L-10** | `INTENTIONALLY_DEFERRED` | la retención es por turno; no hay recuperación de órdenes mal formadas (FD-ORDER-09) |
| L-11 | `INTENTIONALLY_DEFERRED` | reconocimiento de medicamentos: lista cerrada (F09) |
| L-12 | `INTENTIONALLY_DEFERRED` | giros de tiempo genéricos del sistema de tiempo común (F12) |
| L-13 | `INTENTIONALLY_DEFERRED` | techo, paso o base junto a un objetivo se ejecuta como la tasa (F15) |
| L-14 | `INTENTIONALLY_DEFERRED` | «… to reach MAP 65 in 10 minutes» queda como plan; orden válida con una palabra que no es de dosis y otro medicamento se pregunta (F03, F05) |
| L-15 | `INTENTIONALLY_DEFERRED` | pieza no suspensión con dos infusiones; «stop X then Y»; «restart X in 5 minutes»; alias sin lectura; aritmética relativa (F08 resto, F17) |

**Nuevos defectos materiales de ejecución:** la revisión halló dos conductas que **ejecutaban** una suspensión equivocada (F07, F08) y una atribución de tasa a otro fármaco en las respuestas (F11) y por nombres no reconocidos (F09, F10); **se reprodujeron y se repararon dentro de este paquete**. Ninguna queda abierta como ejecución insegura **demostrada**; lo que queda declarado necesita una decisión docente de semántica clínica (L-13) o un rediseño genérico del reconocimiento de medicamentos (L-11), ambos fuera del mandato.

## 13 · P3-486 · Certificación

Candidato: rama `phase-3-runtime-integration`, base `08b9873`, **una huella** `6978a030e2919f592ece9311825e6b406bde20ff83dab768299adf92b30b88ed` (24 archivos modificados o nuevos: el lector sucedido, la barrera y la semántica del tiempo, el reconocimiento de respuestas, el registro y el catálogo, el registro sucesor con su índice y pin, las pruebas nuevas y las adaptadas, el constructor del punto de control, el documento hasta la sección 12, las filas FD-ORDER-01 a 11 y FD-P3-289 a 291, `TD-162` y la cláusula de `CLAUDE.md`).

- **Suite completa:** 14 452 pruebas, **0 fallas, 0 errores**, 98 omitidas, 1 xfail, 24 particiones, 0 reanudaciones; inicio 2026-11-21T02:17:10Z, fin 2026-11-21T04:41:45Z; huella al inicio y al final **iguales** (corrida válida; la huella del árbol al terminar sigue siendo la misma). Ejecutor: las funciones del ejecutor particionado de la skill bajo un envoltorio reanudable que vive fuera del repositorio.
- **Regresiones activas:** **56/56** aprobadas; 10 retiradas, con el motivo que declara el propio ejecutor (`run_regressions.py`).
- **Por qué la suite completa:** el cambio está en el lector (congelado hasta el ciclo anterior y levantado de nuevo por la docencia), en módulos raíz del camino de toda orden (`order_pipeline`, `time_semantics`, `pending_family_orders`, `app`), añade una familia de pruebas y un registro indexado, y adapta pruebas de los congelamientos.
- **Antes del congelamiento (una sola huella, sin mezclar):** 151 archivos de prueba que tocan los módulos modificados, **5 028 aprobadas, 0 fallas**; la familia nueva (355 pruebas) y las guardas de registros e índice (741 pruebas) verdes; **53 mutantes por protección, 53 detectados** (en la primera pasada sobrevivieron 4: dos huecos de prueba reales —el alias de la epinefrina y la continuación que nombra a otra infusión—, una guarda redundante con otra —se probó directamente— y alternativas muertas de la lista de nombres del sistema de tiempo, que se retiraron; los diez mutantes afectados se corrieron otra vez y se detectaron todos); corpus generado propio de 83 894 textos y minado de 1 486 textos **sin una diferencia sin explicar**.
- **No se corrió:** navegador (ninguna pantalla cambió de diseño: la ruta heredada de la respuesta es una función que las pruebas llaman); `validation/` y cualquier respuesta externa (congelados, **no se abrieron**).
- **Después de la certificación se añadieron sólo cuatro elementos no ejecutables:** el registro de punto de control con su entrada de índice y el pin del índice, la prueba de guarda `test_v16` de ese registro, las secciones 13 a 15 y la fila FD-P3-292. La suite completa corrió sobre el candidato de arriba, **no** sobre el árbol final: difieren por esos elementos; se volvieron a correr las guardas que los leen sobre el árbol final: **1 254 aprobadas, 1 omitida, 0 fallas** en 38 archivos (los 31 que leen documentos o el índice, el registro de correcciones, los congelamientos del lector y de la calibración, la sucesión y los límites de órdenes, y el catálogo generado).

## 14 · P3-487 · Punto de control

**Veredicto B · `HIGH_RISK_ORDER_GAPS_FIXED_WITH_LOW_RISK_SEMANTICS_DEFERRED`** (registro `docs/revision/PHASE3_ORDER_SAFETY_CHECKPOINT.json`, sellado e indexado). Las conductas **demostradas** de alto riesgo están cerradas y certificadas: una tasa y una suspensión pertenecen a un solo fármaco; la unidad se exige y es compatible; el «/min» no es una duración; `restart`/`continue` sin tasa son el texto aprobado; la barrera posterior lee `rate_mcg_min` y cada barrera de la nitroglicerina protege sola; la respuesta es una tasa del fármaco que preguntó. Los tres lectores se reconstruyen byte a byte y ningún registro sellado se reescribió.

**Por qué no A.** Quedan declaradas, con su forma exacta, semánticas de bajo riesgo que necesitan una decisión docente o un rediseño genérico: el reconocimiento de medicamentos es una lista cerrada (L-11), los giros de tiempo genéricos (L-12), un techo/paso/base se ejecuta como la tasa (L-13), la meta con tiempo queda como plan (L-14) y la pieza no suspensión con dos infusiones (L-15). **Por qué no C.** Lo demostrado se cerró con reglas estructurales dentro del lenguaje de órdenes existente; sólo L-11 exigiría un reconocimiento genérico de medicamentos y no hace falta para lo demostrado. **Por qué no D.** La reconstrucción histórica es exacta en las dos sucesiones y todo digesto del cierre se recalcula con el lector de su época. **Por qué no E.** Todo defecto material hallado (F07, F08, F11, F09, F10, F13) se **reprodujo y reparó dentro de este paquete**; no queda un defecto material de ejecución sin reparar: lo que queda necesita una decisión de semántica clínica.

**Se detiene aquí (detención dura).** Sin titulación automática por PAM, sin conversión por peso, sin recuperación de órdenes mal formadas, sin cambio de la frontera orden cruda/resuelta, sin otro fármaco, sin recalibrar el tono ni cambiar el acoplamiento con la bomba, sin ampliar la autoridad, sin despliegue a residentes y sin validación clínica. No se siguen cazando casos límite de bajo riesgo.

## 15 · Limitaciones y decisiones pendientes

**Lo implementado y probado.** Ver §1 a §12. Todo lo anterior se probó en el encuentro **real** (lector → semántica del tiempo → paso por el turno → motor) con las infusiones ya en curso, no sólo en el lector.

**Limitaciones (L-n) — exacto lo que sigue sin cubrirse** (ninguna es una ejecución nueva; `TD-162`):
- **L-10** orden aislada retenida por turno; sin recuperación de órdenes mal formadas.
- **L-11** el reconocimiento de otros medicamentos es una lista cerrada: un medicamento ausente de ella, junto a una infusión y con el único literal de tasa de la pieza, le cede la tasa a la infusión (56 de 3 000 textos del corpus de propiedad del revisor, con nombres inventados fuera de la lista).
- **L-12** «después de», «luego de», «in 5 minutes,» con coma, «wait 5 minutes then», «in five minutes», «later» ejecutan una orden vasoactiva **ahora** (limitación previa y de todas las órdenes del sistema de tiempo común).
- **L-13** un techo, un paso o una base junto a un objetivo se ejecuta como la tasa («to MAP 65 max 20 mcg/min»).
- **L-14** «… to 12 mcg/min to reach MAP 65 in 10 minutes» queda como plan (no corre nada); una orden válida con una palabra que no es de dosis y otro medicamento en la pieza se pregunta.
- **L-15** una pieza no suspensión que nombra dos infusiones lee la primera según la prioridad del lector (46 de 3 000 textos); «stop X then Y» también suspende Y; «restart X in 5 minutes» se pregunta; «levophed 12» y «epi 12» no se leen; «nor-epi» se pregunta; «2 mcg/min more» se lee como absoluta.
- **Sólo una capa** protege la propiedad de una tasa explícita (la barrera posterior no la hace cumplir) y las frases de tiempo.
- Fuera de lo vasoactivo (previo): «stop all except propofol» suspende la sedación.
- **No cubierto, por decisión:** `mcg/kg/min` sigue entrando por `weight_based_doses` (la sombra falla cerrado); sin titulación automática por PAM; sin dosis relativas con contexto.

**Decisiones docentes pendientes** (ninguna se tomó): (1) si un techo/paso/base escrito junto a un objetivo es una tasa (L-13); (2) si el reconocimiento de medicamentos pasa a ser genérico en vez de una lista cerrada (L-11); (3) cómo lee el sistema de tiempo común los giros restantes (L-12); (4) retirar la respuesta heredada de la página, si no se conduce (queda cerrada por este paquete).

**Siguiente paso de desarrollo recomendado.** Volver a la línea de **autoridad y desarrollo del simulador**; en la línea de órdenes no hay nada más por hacer hasta que la docencia decida los puntos de arriba.

**Tiempo.** Estimado antes de empezar (reportado): optimista ≈ 10,5 h, más probable ≈ 16,5 h, conservador ≈ 27 h, con **dos** certificaciones completas previstas. Real: inicio 2026-11-20T23:59Z, certificación 02:17Z–04:41Z, cierre y publicación a continuación (≈ 5 h en total). Etapa más lenta: la **certificación completa** (2 h 24 min, **una** sola corrida); la revisión adversarial independiente (≈ 35 min en segundo plano) y las pruebas enfocadas (≈ 28 min) le siguen. Mayor error de estimación: el número de certificaciones (se previeron dos y hizo falta una, porque la revisión y sus reparaciones ocurrieron **antes** de congelar la huella) y el costo del riesgo principal (la sucesión de tres lectores, que con el generador de hunks costó minutos). Lección de calibración: reparar lo que halle la revisión sobre el candidato **previo** a la huella y paralelizar mutantes y pruebas enfocadas en copias del árbol evita la segunda certificación completa, que fue el grueso del costo previsto.
