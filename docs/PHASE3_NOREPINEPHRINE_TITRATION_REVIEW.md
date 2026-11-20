# Fase 3 · Revisión docente interactiva de la titulación y suspensión de norepinefrina (P3-438 a P3-448)

Encargo del 2026-11-19. Rama `phase-3-runtime-integration`; linaje `PHASE2_AMENDMENT_3` (certificado, digesto `867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c`); instantánea común de tono `COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1`; punto de control anterior: A `NOREPINEPHRINE_TITRATION_AND_STOP_READY_FOR_HUMAN_DEVELOPMENT_REVIEW`.
**Esto es capa de revisión (UX y plomería de persistencia). No cambia fisiología, constantes del tono, acoplamiento con la bomba, parámetros, trayectorias, autoridad, puntuación ni el primer piloto, y no es una validación clínica.** La revisión humana **no se hizo**: este documento y el entorno la dejan lista.

## 0 · Decisiones docentes (2026-11-19; FD-TITREV-01 a FD-TITREV-13)

| Id | Decisión |
|---|---|
| FD-TITREV-01 | Pasar a la revisión docente humana de la semántica de cambio de tasa de norepinefrina. La meta **no** es calibrar mmHg: la persona revisora juzga dirección, tiempo, orden, suavidad, persistencia, decaimiento tras suspender y reinicio. |
| FD-TITREV-02 | La **misma** *Faculty Trajectory Review* simple: un escenario a la vez; contexto clínico, línea de intervenciones, gráfico PAS/PAD/PAM, tabla de presiones, Q1–Q5, comentario opcional, **LOCK FIRST IMPRESSION**, juicio global, **SUBMIT & NEXT**. Sin formularios en markdown ni tablero técnico. |
| FD-TITREV-03 | Hemorragia digestiva como familia principal (su comportamiento de presión por el tono común ya pasó revisión humana, su fisiología sigue activa y la persona revisora conoce el escenario). No se introduce otra familia clínica. |
| FD-TITREV-04 | Escenarios: **TIT-1** inicio 5 → aumento a 10 mcg/min; **TIT-2** inicio 10 → reducción a 4; **TIT-3** inicio 10 → suspensión; **TIT-4** inicio 5 → 10 → 4 → suspensión; **TIT-5** inicio 10 → suspensión → tasa absoluta explícita 10 (reinicio). Si las cinco trayectorias están certificadas, se incluyen las cinco; si TIT-5 exigiera código nuevo, se excluye antes que tocar la fisiología. |
| FD-TITREV-05 | **No** se incluye el caso simple de sólo inicio: ya tuvo revisión humana (FR-F). |
| FD-TITREV-06 | Sólo el comportamiento certificado de `CENTER_REFERENCE`. **No** se muestra LOW, HIGH, valores de parámetros, `tone_gain`, tau de inicio ni de cese, estado técnico, gasto cardiaco, entrega de oxígeno, consciencia, colapso, comparador heredado ni juicios docentes anteriores. |
| FD-TITREV-07 | Una pregunta propia por escenario (cinco, con la redacción exacta del encargo; ver §3). |
| FD-TITREV-08 | Q1–Q5 exactamente como antes (Dirección, Tiempo, Magnitud, Respuesta de manejo, Riesgo educativo), comentario opcional, bloqueo, juicio global (`ACCEPT`, `ACCEPT_WITH_LIMITATION`, `RECALIBRATE`, `REJECT`), comentario global opcional, **SUBMIT & NEXT**. |
| FD-TITREV-09 | No se pide calibrar valores exactos. `RECALIBRATE` sólo ante un problema material: dirección equivocada, tiempo claramente implausible, sobrepaso o discontinuidad, falta de respuesta al cambio de tasa, suspensión como borrado instantáneo, soporte que persiste indefinidamente, reinicio no causal o conducta educativamente engañosa. Las preferencias numéricas menores, a lo sumo `ACCEPT_WITH_LIMITATION`. |
| FD-TITREV-10 | Se conserva el fallo cerrado: una orden no soportada o mal formada que cierra la infusión de la sombra **no** se recupera después en ese encuentro. No se revisan órdenes mal formadas con la docencia en este paquete. |
| FD-TITREV-11 | Una orden explícita de tasa absoluta válida tras una suspensión **es** un reinicio. Una instrucción relativa («increase norepinephrine») sin infusión activa sigue sin soporte y falla cerrada. No se añade lectura de dosis relativas. |
| FD-TITREV-12 | **No** se cambia el espejo compartido para que consuma las órdenes asentadas por el motor: el motor heredado conserva el defecto por el que «titrate norepinephrine to MAP 65» puede leerse como 65 mcg/min; hasta resolverlo por separado, se mantiene la frontera declarada de la sombra. |
| FD-TITREV-13 | La dependencia de la bomba y la consciencia bajo tono **siguen abiertas** y no bloquean esta revisión de hemorragia digestiva: no se expone la consciencia ni se revisan familias limitadas por la bomba. |

## 1 · P3-438 y P3-439 · Auditoría de fuentes y conjunto (cada trayectoria es lo ya certificado)

Regla: **ninguna trayectoria se calcula con otro parámetro, ni se afina, ni se sustituye un testigo.** `CENTER_REFERENCE` es el único testigo, con los valores exactos certificados (`PHASE3_NOREPINEPHRINE_TITRATION_PROBES.json`, `gi_probes.probes`, intacto: sus bytes son los fijados por el índice de registros históricos). Los cinco escenarios son cinco sondas **ya certificadas** del encuentro real de `gi_bleed_57m`; ninguno necesita código nuevo ni fisiología nueva.

| Escenario | Sonda certificada | Historia de tasa (minuto, mcg/min) | Resultados que entregó el espejo | Estado |
|---|---|---|---|---|
| **TIT-1** Aumento | `B_START_INCREASE` | (2; 5) → (10; 10) | `STARTED`, `INCREASED` | incluido |
| **TIT-2** Reducción | `C_START_DECREASE` | (2; 10) → (10; 4) | `STARTED`, `DECREASED` | incluido |
| **TIT-3** Suspensión | `D_START_STOP` | (2; 10) → (10; 0) | `STARTED`, `STOPPED` | incluido |
| **TIT-4** Secuencia | `E_START_INCREASE_DECREASE_STOP` | (2; 5) → (10; 10) → (18; 4) → (25; 0) | `STARTED`, `INCREASED`, `DECREASED`, `STOPPED` | incluido |
| **TIT-5** Reinicio | `F_START_STOP_RESTART` | (2; 10) → (10; 0) → (18; 10) | `STARTED`, `STOPPED`, `RESTARTED` | incluido: **representable sin código nuevo** |

**No se excluyó ninguno.** TIT-5 era la sonda de reinicio (`0 → 10 → 0 → 10` del encargo anterior) y su trayectoria determinista completa ya estaba certificada, de modo que la condición de FD-TITREV-04 («excluir antes que modificar la fisiología») no llegó a activarse. El caso de sólo inicio (`A_START`, `A10_START`) **no** está en el conjunto (FD-TITREV-05).

**Pruebas de igualdad** (`test_phase3_titration_review_records.py`):
- **c6**: la serie del escenario es, minuto a minuto, el `per_minute` guardado de su sonda (33 puntos, minutos 0 a 32), **sin recalcular**; la presión mostrada en las lecturas certificadas (minutos 2, 10, 18, 25 y 32) es la guardada; la llegada es 88/54 mmHg (PAM 65).
- **c7**: los cambios de tasa mostrados son las órdenes que entregó el espejo en esa sonda y el plan que escribió la docencia (escrito a mano en la prueba, no leído del constructor).
- **c8**: cada serie es **igual** a la que produce **hoy** la llamada certificada del arnés (`test_tone_titration_analysis.gi_probe`: intérprete, motor, espejo, mapeo registrado y lector declarado reales).
- **c3**: el contenido completo del conjunto, regenerado, es igual al guardado, con independencia del código que generó su procedencia.
- **c9**: cinco sondas distintas, cinco trayectorias distintas; TIT-5 coincide con TIT-3 hasta el reinicio (una historia certificada, dos continuaciones).

Variables mostradas: **PAS, PAD y PAM** en mmHg enteros, con el criterio de las revisiones anteriores (PAS y PAD redondeadas; PAM = (PAS + 2 × PAD)/3). Minutos de la tabla (fijados al elegir los escenarios, antes de mirar las trayectorias; incluyen cada cambio y el último minuto): TIT-1, TIT-2, TIT-3: 0, 2, 4, 10, 12, 14, 18, 25, 32; TIT-4: 0, 2, 4, 10, 12, 18, 20, 25, 27, 32; TIT-5: 0, 2, 4, 10, 12, 18, 20, 25, 32.

## 2 · P3-440 · Identidad y datos del conjunto

Conjunto versionado: **`NOREPINEPHRINE_TITRATION_V1_FACULTY_REVIEW`** (`docs/revision/PHASE3_NOREPINEPHRINE_TITRATION_V1_REVIEW_SET.json`; registro histórico sellado e indexado; su digesto está fijado en el código, `faculty_titration_review.PINNED_SET_DIGEST`, y el cargador rechaza cualquier conjunto que no sea ése, aunque se le vuelva a firmar). **No** sobrescribe ninguna revisión anterior: sus registros viven en `titration_review/` y `titration_reviews/`, aparte de la primera revisión (`trajectory/`), la re-revisión (`trajectory_rereview/`) y la revisión de tono (`tone_review/`, `tone_reviews/`, `tone_sensitivity/`).

Cada escenario guarda sólo lo que la pantalla dibuja: rótulo, título, contexto clínico **autoral** (la presentación y el diagnóstico del caso, citados literalmente), hallazgos de base **autorales** (examen, ecografía, hemoglobina), llegada (PA, SpO₂, FR), la intervención, **los cambios de tasa** (número, minuto, operación y tasa tras el cambio), la tabla de lo hecho, los puntos por minuto y los minutos de la tabla. **No guarda** otro ajuste de la respuesta (ni LOW ni HIGH: el conjunto **no tiene** sección de sensibilidad), FC ni relleno capilar, estado de tono, soporte de la infusión, historia de tasas del escritor, flujo, entrega o deuda de oxígeno, consciencia, colapso, parámetros, comparador, trayectoria anterior ni juicio anterior. El cargador exige las claves exactas, rechaza cualquier palabra de mecanismo en un campo visible, y **sostiene cada escenario a su definición en el código**: la pregunta es la de la docencia (palabra por palabra), la historia de tasas es la del encargo (`RATE_PLAN`) y cada cambio es lo que su nombre dice (un aumento sube, una reducción baja a una tasa mayor que cero, una suspensión baja a cero, un reinicio parte de cero). Las **seis limitaciones** se guardan aparte de los escenarios y sólo se dibujan en el resumen final.

## 3 · P3-441 · Pantalla (reutiliza la existente)

`faculty_titration_review_ui.py` reutiliza el gráfico, la tabla de intervenciones, los widgets y los *callbacks* de autoguardado de la *Faculty Trajectory Review*; mismo diseño visual; sin tablero técnico ni archivos que la persona abra. Una pantalla por escenario, en este orden: rótulo (`SYNTHETIC DEVELOPMENT CASE`), título, **What you are judging** (la pregunta del escenario), contexto clínico y hallazgos de base, **What was done · every change of the norepinephrine rate** (tabla: #, minuto, qué se hizo, qué hizo el encuentro), gráfico PAS/PAD/PAM, tabla de valores en minutos clave, Q1 a Q5, comentario opcional, **LOCK FIRST IMPRESSION**, juicio global, comentario opcional, **SUBMIT & NEXT** (**SUBMIT & FINISH** en el quinto).

**Cada cambio de tasa está marcado en el gráfico**: una línea vertical discontinua en su minuto con su número y su operación (`1 · start 5`, `2 · up to 10`, `3 · down to 4`, `4 · stop`, `5 · restart 10`); el número es el de la fila de la tabla «What was done». No se muestra ningún valor de parámetro.

Las cinco preguntas (con la redacción del encargo, FD-TITREV-07):

| Escenario | Qué se juzga |
|---|---|
| TIT-1 | Does the pressure response increase smoothly and at an appropriate time after the norepinephrine rate is increased? |
| TIT-2 | Does the pressure response decrease smoothly and at an appropriate time after the norepinephrine rate is reduced? |
| TIT-3 | After norepinephrine is stopped, does the pressure effect decay with a clinically plausible delay rather than disappearing instantly? |
| TIT-4 | Across sequential rate changes, does the pressure trajectory follow the ordered norepinephrine dose changes in the correct direction and sequence? |
| TIT-5 | After norepinephrine is stopped and later restarted at an explicit valid rate, does the pressure response reappear causally without retaining an inappropriate residual effect? |

**Cambios compartidos, mínimos y declarados:**

* `faculty_review_ui.launcher`: nuevo modo `TITRATION_MODE` («Norepinephrine titration review»), su aviso propio, y una **retención propia**, con el mismo patrón que la de la re-revisión y la de tono: mientras esta persona revisora no tenga sus cinco escenarios enviados **y verificados**, el lanzador **no ofrece nada más** (ni la primera revisión, ni la re-revisión, ni la revisión de tono, ni el encuentro en vivo: dibujan trayectorias anteriores, el comparador heredado, FC, relleno capilar y juicios anteriores). Falla cerrado. **Precedencia:** primero la retención de la re-revisión, luego la de tono y por último ésta; una persona con alguna pendiente ve primero ésa, como antes. Interruptor del operador, nuevo: `MRS_FACULTY_TITRATION_GATE=off` la suelta (para el operador y para las pruebas de los otros modos); cualquier otro valor la deja en vigor. Tras el quinto envío vuelven los **cinco** modos.
* `app.py`: tres líneas (importación, entrega de la página y de su retención) y **el modo de aterrizaje es ahora el de titulación** (antes, el de tono).
* Las pantallas de esta revisión no importan nada de la capa de Fase 3, el motor, el núcleo ni la autoridad (prueba t16).
* **Pruebas anteriores adaptadas** (declaradas; lo que protegen sigue protegido): `test_phase3_faculty_review_page.py` (el entorno de pruebas abre también el interruptor de titulación, como ya hacía con los otros dos); `test_phase3_tone_review.py` t16 y `test_phase3_trajectory_rereview.py` (el aterrizaje del lanzador es el de titulación); `test_phase3_trajectory_rereview_page.py` p15c, p15e y p15f y `test_phase3_tone_review_page.py` (su ayudante `_open`, p16b y p20b: la lista de modos tiene **cinco** y la revisión de tono, ya no la de aterrizaje, es una elección explícita que el ayudante hace; el aterrizaje se verifica aparte con `land=True`); y `test_phase3_tone_review_records.py` c2 (el recuento de módulos de aplicación del conjunto de tono no cuenta los dos módulos de la titulación, posteriores a él).

## 4 · P3-442 · Persistencia

El registro de eventos de la revisión anterior (`ReviewLog`: añadir sólo, encadenado por hash, bajo `flock` y `fsync`) en archivos propios. **Autoguardado** por *callbacks* (cada respuesta y cada comentario, al darlos); un **refresco** restaura respuestas, comentario, bloqueo, juicio global y avance; **el bloqueo es irreversible** (una respuesta ciega posterior se ignora al leer y se rechaza al escribir); un segundo envío no crea un segundo registro; un registro forjado o alterado no cuenta y deja el registro ilegible; un bloqueo desde una pantalla desactualizada (otra ventana de la misma cuenta cambió una respuesta) **no bloquea nada**; un comentario rechazado no se pierde en silencio al enviar; tras **SUBMIT & NEXT** se pasa **solo** al escenario siguiente. Un registro por escenario, con el digesto del conjunto, el del escenario y los de la fuente certificada.

## 5 · P3-443 · Resumen final

Tras el quinto envío: **REVIEW COMPLETE · 5 / 5**; recuento de `ACCEPT` / `ACCEPT_WITH_LIMITATION` / `RECALIBRATE` / `REJECT`; tabla (escenario, juicio global, Q1 a Q5) apta para captura; comentarios; y, **sólo aquí**, **CURRENT LIMITATIONS**:

* sólo tasas absolutas explícitas en mcg/min (una instrucción relativa sin infusión en curso no se soporta);
* sin dosis por peso (mcg/kg/min): nunca se convierte;
* sin titulación a un objetivo de presión («titrate to MAP 65»): ninguna tasa se elige a partir de una presión;
* una orden que el sistema no puede leer como tasa absoluta explícita (no soportada o mal formada) **cierra** la infusión modelada por el resto del encuentro, se declara y nada la recupera después;
* la consciencia bajo soporte de tono no se mostró ni se juzgó: sigue sin resolver;
* la dependencia de la bomba no está validada; esta revisión usó un caso de hemorragia y no respalda el uso de un vasopresor en condiciones limitadas por la bomba.

El resumen cuenta **sólo** registros que verifican contra el registro de eventos que los cerró; uno que no verifica no se cuenta y se informa como problema técnico, nunca como excepción.

**Guía de interpretación posterior (sólo guía docente; no es aprobación automática):** `ACCEPT` / `ACCEPT_WITH_LIMITATION` en los cinco indican que la regla del cambio de tasa (constante de inicio mientras el aporte sube, de cese mientras baja) es aceptable **para desarrollo**; un `RECALIBRATE` apunta a un problema material de la regla, no a una calibración en mmHg; un `REJECT` o un `RECALIBRATE` en TIT-3 o TIT-5 apunta a la dinámica de cese o a la causalidad del reinicio. Nada de esto se implementa ni se decide aquí.

## 6 · P3-444 · Auditoría de ciego

Se atacó cada vía por la que algo prohibido podría llegar a la persona revisora: la etiqueta `CENTER_REFERENCE`, los parámetros (`tone_gain`, constantes de tiempo, vida media), el estado técnico y la historia de tasas del escritor, juicios y trayectorias anteriores, el comparador heredado, LOW/HIGH, las salidas mecanísticas (gasto cardiaco, entrega de oxígeno, consciencia, colapso) y FC y relleno capilar.

* **Pantalla real (AppTest sobre `app.py`)**: texto visible, texto propio de cada elemento (etiquetas, ayudas, opciones, expansores, barra lateral), especificaciones de gráfico, claves de sesión, enlaces y descargas, en **cada etapa de cada escenario**: sin ninguna de esas palabras, y **sin las limitaciones antes del resumen**. Los detectores se prueban a sí mismos (inyectan ocho fugas distintas y una en el gráfico y exigen verlas; lo mismo para FC y relleno capilar, y para la lectura de archivos por cuatro vías).
* **Rutas forzadas**: una clave de sesión que apunta a otro modo, al resumen o a un escenario aún no abierto no muestra nada de ellos (la prueba de la ruta al resumen existe porque un mutante la dejó pasar en la primera tanda).
* **Archivos**: la primera pasada **no lee** ningún archivo de otro conjunto, de las revisiones anteriores ni de las fuentes certificadas (gancho de auditoría de `open`).
* **Transporte (navegador real, Chromium)**: se capturaron **todos los mensajes del websocket que recibe el navegador** durante una revisión completa de los cinco escenarios (3 847 mensajes, 985 KB) y se buscaron 38 términos prohibidos. **Cero coincidencias** en el arranque y en la primera pasada y el bloqueo de los cinco escenarios; las únicas coincidencias están en la pantalla del resumen final (las limitaciones, que es donde deben estar). La nota que dice por qué no se muestran FC y relleno capilar los nombra a propósito (se excluye de la búsqueda).

## 7 · P3-445 · Capturas

Navegador real (Chromium), ventanas de portátil de **1366 × 768** y **1440 × 900**, cuenta docente desechable en un almacén temporal, recorrido completo de los cinco escenarios y del resumen: **sin desplazamiento horizontal** (`scrollWidth ≤ clientWidth` en cada pantalla). Por escenario, la persona revisora obtiene, desplazando la pantalla, **tres capturas** que lo contienen todo para juzgar: (1) título, pregunta, contexto, hallazgos de base y tabla de lo hecho; (2) tabla, gráfico con los cambios marcados y tabla de valores; (3) Q1 a Q5, comentario y bloqueo; el juicio global es una cuarta, corta. El resumen cabe en una captura. Lenguaje clínico únicamente; los nombres de los escenarios son cortos («Increase», «Decrease», «Stop», «Sequence», «Restart») para que los botones no se trunquen. No hay botón de exportación: la captura es el medio.

## 8 · P3-446 · Pruebas

* `test_phase3_titration_review.py` (módulo, 144 pruebas): conjunto fijado, cinco escenarios en orden, pregunta y plan de la docencia, marcadores, tabla de valores, Q1–Q5, vista ciega, limitaciones aparte, rechazo de un conjunto editado, ampliado, re-firmado o con fuga (62 mutaciones y 14 formas de texto), cambio que no es lo que su nombre dice, registro y bloqueo, reinicio tras refresco, un registro por escenario, resumen que sólo cuenta lo que verifica, comparación campo por campo contra el registro de eventos, aislamiento de importaciones, revisiones anteriores intactas.
* `test_phase3_titration_review_page.py` (página real, AppTest sobre `app.py`, 38 pruebas): el flujo humano completo, aterrizaje, pantalla de primera pasada, gráfico y tabla iguales a lo guardado con cada cambio marcado, bloqueo, resumen, ciego en cada etapa, detectores que fallan cuando deben, ningún archivo ajeno leído, persistencia tras refresco, envío fallido, comentario rechazado, bloqueo desde pantalla desactualizada, retención del lanzador y su precedencia, rutas forzadas, residente, ninguna palabra de autoridad.
* `test_phase3_titration_review_records.py` (registros y fuentes, 26 pruebas): sello, procedencia, índice, igualdad con la fuente certificada (también regenerada con la llamada certificada), constantes y autoridad sin cambio, sin datos privados.
* **21 mutantes** propios de las protecciones del paquete (palabras de fuga, pregunta, plan, marcadores, limitaciones antes de tiempo —en el módulo y en la página—, registro ligado al conjunto, juicio y revisor del registro, ancla del digesto, vista ciega, transición de cambio, retención del lanzador, predicado de retención, bloqueo desde pantalla desactualizada o con comentario rechazado, marcadores del gráfico, escenarios abiertos, resumen forzado, nota de FC): **los 21 detectados**. Siete sobrevivieron la primera vez (dos por mi propia tanda, cinco por la revisión independiente) y se repararon con pruebas, no con código de comportamiento.

## 9 · Revisión adversarial independiente

**Una** revisión adversarial independiente (agente de sólo lectura que no escribió el paquete; trabajó sobre una copia y en directorios temporales; confirmó cada hallazgo con una sonda). Resultado: **ningún hallazgo bloqueante ni mayor**; siete observaciones menores o notas, todas de cobertura de pruebas o defensa en profundidad.

| # | Sev. | Hallazgo (confirmado) | Disposición |
|---|---|---|---|
| 1 | Menor | Las limitaciones sobre un resumen incompleto no estaban protegidas **en la página** (un mutante que las dibujaba sobrevivió; el código era correcto) | **Reparado con una prueba** (p16 ahora lo exige, también con la ruta forzada al resumen); mutante detectado |
| 2 | Menor | Un comentario de primera pasada rechazado al **bloquear** no tenía prueba de página (sí el global) | **Reparado con una prueba** (p10e); mutante detectado |
| 3 | Menor | La nota sobre FC y relleno capilar se comprobaba contra la constante del propio módulo | **Reparado:** las pruebas leen las dos notas con sus palabras; mutante detectado |
| 4 | Menor | El cargador verifica menos de lo que su docstring decía: sobre 8 275 mutaciones re-firmadas **y** fijadas, ninguna lanzó excepción y 2 070 se aceptaron (la columna de resultados de la tabla, `advance`, el texto autoral, el texto de una limitación) | **Declarado y corregido el docstring:** el cargador verifica estructura, lo que fijó la docencia (pregunta, plan, cambios) y las palabras de fuga; el texto autoral lo guarda **sólo** el digesto fijado en el código (ver §13) |
| 5 | Nota | El filtro de palabras de fuga era más estrecho que la lista de la docencia («tau», «cardiac flow», «delivery of O2», «pulse», «gain», «titrate», «mg/kg», «soft collapse» pasaban en un conjunto re-firmado y fijado) | **Reparado:** el filtro cubre esas formas y hay 14 casos de texto en la prueba t21; el conjunto fijado ya estaba limpio |
| 6 | Nota | Comprobaciones redundantes sin prueba (revisor, escenario, conjunto y ligadura del registro, que ya cubre `record_id`; la transición de un cambio, que el plan vuelve inalcanzable; el borrado de una clave de sesión) | **Probadas por separado:** t15a y t15c comparan el registro campo por campo con el registro de eventos; t8e prueba la transición. La clave de sesión es inocua |
| 7 | Nota | Un `import` sin uso; un comentario del aterrizaje desactualizado en una prueba adaptada; el botón del último escenario dice **SUBMIT & FINISH** (heredado) y la nota de FC y relleno capilar aparece en cada pantalla (heredada, FD-REREVIEW-23) | **Limpiado** lo que era mío; lo heredado se mantiene |

Atacado sin éxito: la fidelidad de cada serie (igual al `per_minute` certificado, sin deriva de la regla de la PAM), el cargador (sin excepción ante 8 275 mutaciones, anidamiento profundo, NaN, una ruta que es un directorio), la persistencia (12 bloqueos concurrentes dieron 1 correcto; 12 envíos concurrentes, 1 registro; el registro de una persona copiado a la ruta de otra no se cuenta), el lanzador (precedencia re-revisión → tono → titulación; las claves forzadas no leen archivos de otro modo; falla cerrado ante predicado que lanza, sin almacén, sin rol docente o con un conjunto no verificable; sin los argumentos nuevos el lanzador es el de antes), la fuga (expresión amplia sobre texto, protocolos, gráficos y ayudas en las etapas en blanco, respondida, bloqueada y global: nada), el alcance (digesto del núcleo intacto, ningún archivo de `runtime_*`, `family_engine` ni de concesiones cambió) y los datos privados (ninguno en archivos nuevos). Sobre **55 mutantes** de esa revisión, unos 45 murieron; los que sobrevivieron son las observaciones de arriba. **Sospechado, no confirmado:** la adaptación del recuento de módulos de la revisión de tono es una lista de excepciones que crecerá con cada revisión posterior (declarado en §3 y en `TD-159`).

## 10 · P3-447 · Certificación

Cambió comportamiento ejecutable compartido (el lanzador, `app.py` y dos módulos de raíz nuevos), así que la certificación fue **completa**, sobre **una** huella congelada. **Análisis de dependencias:** la suite completa era obligatoria porque varias guardas recorren todos los módulos de la raíz (`ROOT.glob("*.py")`: límites de contrato, linaje de las enmiendas, guardas dormidas, índice de registros), el cambio añade dos módulos de raíz, toca el lanzador compartido y `app.py`, agrega un registro indexado y adapta pruebas de página anteriores.

- **Candidato:** rama `phase-3-runtime-integration`, base `c268ffd`, árbol de trabajo con huella `b4a6899857e6d11c58327e481cc04f15e3829039e0f1b84fb5f3ee07a8470aa7` (24 entradas cambiadas): el módulo, la pantalla, el lanzador, `app.py`, el conjunto sellado con su entrada de índice y su ancla, el arnés del conjunto, las tres pruebas nuevas, las pruebas anteriores adaptadas, este documento (§0 a §9, §12 y §13), las filas FD-TITREV-01 a 13 y FD-P3-277 a 279, `TD-159`, la cláusula de `CLAUDE.md` y las dos notas.
- **Suite completa:** 13 692 pruebas, **0 fallas, 0 errores**, 101 omitidas, 1 xfail, en 24 particiones; huella igual al inicio y al final (0 reanudaciones). Una sola corrida.
- **Regresiones:** `run_regressions.py`, **56/56** activas aprobadas; 10 retiradas, que el propio ejecutor conserva sin correr.
- **Antes de congelar:** las pruebas focalizadas del paquete: módulo (144), página real (38) y registros y fuentes (28 aprobadas y 3 omitidas hasta que existió este punto de control); las **tres páginas de revisión anteriores completas** tras adaptarlas (tono 46, re-revisión 30, primera revisión 14); las **20 guardas que recorren el árbol** (616 aprobadas, 3 omitidas); 21 mutantes, los 21 detectados; una revisión adversarial independiente (§9).
- **Pruebas adaptadas (declaradas):** las de §3 y `TD-159`, ítem 7.

**Lo que se añadió después de certificar, y no cambió nada ejecutable:** el registro del punto de control, su entrada en el índice con el ancla del índice, estas secciones 10 y 11 y la fila FD-P3-280. La suite completa corrió sobre el candidato de arriba, **no** sobre el árbol final. Sobre el árbol final se repitieron las pruebas que leen esos archivos: los registros de la titulación (con sus pruebas c16 a c18, que antes se omitían y ahora corren), el versionado de registros históricos, el módulo (144) y las guardas de documentos y de idioma (256 aprobadas, 0 omitidas); y, aparte, todas las guardas de registros y de puntos de control de la Fase 3, las de artefactos de enmiendas y la página real de la titulación (167 aprobadas, 3 omitidas por diseño: registros anteriores generados por otro código, que se conservan tal cual, P3-388).

**No se verificó:** una revisión humana de cualquier trayectoria de titulación (es la siguiente acción humana); trayectorias LOW/HIGH de estas historias (la revisión no las muestra ni las pide); una sesión de residente.

## 11 · P3-448 · Punto de control

Registro: `docs/revision/PHASE3_NOREPINEPHRINE_TITRATION_V1_REVIEW_CHECKPOINT.json`. Las opciones eran A `NOREPINEPHRINE_TITRATION_REVIEW_READY_FOR_HUMAN_USE`, B `CORE_TITRATION_SCENARIOS_READY_BUT_RESTART_EXCLUDED`, C `REVIEW_UI_READY_BUT_PERSISTENCE_NOT_CERTIFIED`, D `BLINDNESS_LEAK_FOUND` y E `CERTIFIED_TRAJECTORY_SOURCE_MISMATCH`.

**Punto de control: A · `NOREPINEPHRINE_TITRATION_REVIEW_READY_FOR_HUMAN_USE`.**

**Por qué A.** Los cinco escenarios (incluido el reinicio) están en el conjunto y cada trayectoria es igual a su fuente certificada; la persistencia está certificada; no se encontró fuga de ciego; la certificación completa está en verde.

**Por qué no B.** TIT-5 está en el conjunto: su trayectoria determinista completa ya estaba certificada (la sonda de reinicio), no hizo falta código ni fisiología nuevos y no se excluyó nada. **Por qué no C.** Autoguardado, bloqueo irreversible, refresco, un registro por escenario, bloqueo desde una pantalla desactualizada que no bloquea nada, registro forjado ilegible y registro que no verifica no contado. **Por qué no D.** Ninguna pantalla, elemento, especificación de gráfico, clave de sesión, lectura de archivo, ruta forzada ni mensaje del websocket llevó la configuración, otro ajuste, un parámetro, el escritor o su historia de tasas, una trayectoria o juicio anterior, el comparador, la FC, el relleno capilar ni una limitación antes del resumen. **Por qué no E.** Cada escenario es la serie guardada de su sonda certificada, igual a la que produce hoy la llamada certificada del arnés.

**Siguiente acción humana.** Que una persona docente haga la revisión de cinco escenarios (unos 20 minutos) y diga si la semántica explícita de cambio de tasa de norepinefrina —constante de inicio mientras sube, de cese mientras baja— es suficientemente plausible para **desarrollo**.

**Se confirma:** sin recalibrar el tono, sin cambio del acoplamiento con la bomba, sin fisiología nueva, sin ampliar la autoridad, sin autoridad de consciencia ni terminal, sin despliegue a residentes y sin afirmación de validación clínica; sin dosis por peso, sin titulación por objetivo de presión, sin otro vasopresor. **Alto** tras P3-448.

## 12 · Cómo se lanza y qué clics hace la persona revisora

**Operador** (el mismo entorno de un solo proceso de las revisiones anteriores; las mismas variables):

```bash
export MRS_FACULTY_DEVELOPMENT_REVIEW=faculty_development_review MRS_PHASE3_SHADOW=shadow_compare MRS_PHASE3_AUTHORITY=limited_common_authority \
       MRS_PHASE3_AUTHORITY_SNAPSHOT=GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1 MRS_PHASE3_AUTHORITY_ENVIRONMENT=development MRS_OFFLINE_CASES=1 \
       MRS_PHASE3_AUTHORITY_STORE="$HOME/faculty_review/R1/store" MRS_AUTH_MODE=accounts MRS_ALLOW_LOCAL_SQLITE=true \
       MRS_DATABASE_URL="sqlite:///$HOME/faculty_review/R1/accounts/accounts.sqlite3"
streamlit run app.py
```

Si el almacén de esa persona **no** contiene la re-revisión o la revisión de tono completadas, sus bloqueos siguen vigentes (sin cambios): la persona vería primero ésas. El operador, que sabe que ya se hicieron, añade `MRS_FACULTY_REREVIEW_GATE=off` y `MRS_FACULTY_TONE_GATE=off` (los interruptores del operador de FD-REREVIEW-22 y de la revisión de tono); la persona revisora no ve nada de eso. **No** se añade `MRS_FACULTY_TITRATION_GATE=off`: es el de esta revisión, y soltarlo abriría los otros modos antes de terminarla.

**Persona revisora:** (1) abre la dirección que imprime Streamlit; (2) inicia sesión con su cuenta docente; (3) **ya está en la revisión** (escenario 1 de 5): no hay nada que elegir ni nada más que abrir hasta el quinto envío; (4) por escenario: Q1 a Q5 → comentario opcional → **LOCK FIRST IMPRESSION** → **Overall judgment** → comentario opcional → **SUBMIT & NEXT** (en el quinto, **SUBMIT & FINISH**); (5) ve **REVIEW COMPLETE · 5 / 5**, el recuento, la tabla y las limitaciones actuales.

## 13 · Limitaciones y decisiones pendientes

1. **La revisión humana no se hizo** y nada aquí la sustituye. Lo que diga la persona revisora son juicios suyos, tabulados; no son una puntuación ni una validación.
2. **Un solo testigo** (`CENTER_REFERENCE`): no hay corrida LOW/HIGH de estas historias, y la revisión **no** muestra ni pide ninguna (FD-TITREV-06).
3. **Sólo tasas absolutas explícitas en mcg/min** (FD-TITREV-11): sin dosis por peso, sin objetivos de PAM, sin dosis relativas, sin otro vasopresor.
4. **Una orden que cierra la infusión no se recupera** (FD-TITREV-10) y **el espejo sigue entregando la orden tal como se escribió** (FD-TITREV-12): lo que `TD-158` declara sigue igual, y el defecto heredado de «MAP 65» sigue sin resolver.
5. **FC y relleno capilar no se muestran** (no se recalcularon para estas trayectorias); tampoco consciencia, flujo, entrega ni colapso. La dependencia de la bomba y la consciencia bajo tono siguen abiertas (FD-TITREV-13).
6. **Presiones en mmHg enteros**, con el criterio de pantalla de las revisiones anteriores; la PAM sin redondear del modelo difiere hasta ~1 mmHg.
7. **El eje de presión es el de las revisiones anteriores (0 a 140 mmHg)**: respuestas de 10 a 20 mmHg se leen como cambios pequeños en el gráfico; la tabla de valores da los números.
8. **El registro del conjunto no tiene firma**: el sello y el digesto fijado en el código detectan una edición descuidada, no una reescritura coherente de contenido, sello e índice a la vez (el mismo límite que `TD-153` ítem 7). Aceptado para esta revisión de un solo proceso. **El cargador no re-deriva el texto autoral** (contexto, hallazgos de base, columna de resultados de la tabla, `advance`, textos de las limitaciones): sobre un conjunto re-firmado **y** con su digesto cambiado en el código sólo ese digesto lo guarda (hallazgo 4 de la revisión adversarial).
9. **Retención del lanzador:** hasta el quinto envío verificado no se ofrece nada más; la persona que ya completó las otras revisiones pero cuyo almacén no las contiene las vería primero (el operador las suelta con sus interruptores, ver §12).
10. **Sin exportación**: la captura de pantalla es el único medio de compartir; el resumen técnico de la sesión se escribe solo y no se muestra.
11. **Sin cambios fuera de lo declarado:** no se tocó el núcleo (`clinical_core/`, digesto fijado), la fisiología de tono ni su titulación, el acoplamiento con la bomba o la poscarga, la calibración de GI, el volumen, la entrega, la consciencia, la dosis-respuesta ni el mapeo de desarrollo; sin parámetro elegido, sin autoridad de norepinefrina, sin control de fuente, sin autoridad de consciencia ni terminal, sin despliegue a residentes ni validación clínica; `COMMON_CORE_RUNTIME_AUTHORITY = False`.
12. **Pendiente (decisión docente):** el resultado de la revisión humana y, según la guía de §5, si la regla del cambio de tasa es aceptable para desarrollo.

---

**Nota 2026-11-20 (objetivo ≠ tasa).** El defecto heredado de «MAP 65» que este documento declara «no tocado» se reprodujo, rastreó y reparó antes del motor, sin tocar el lector congelado (`docs/PHASE3_NOREPINEPHRINE_TARGET_ORDER_BOUNDARY.md`, FD-P3-282, `TD-160`): una orden de infusión con un número sin unidades se retiene y nunca crea una dosis. Lo escrito arriba describe el estado de entonces y **no se edita**. El espejo compartido sigue entregando la orden tal como se escribió (veredicto A de la frontera) y el cierre persistente ante una orden mal formada sigue (FD-NR-07).
