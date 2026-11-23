# Fase 3 · Ratificación de la traza de manejo de GI y preparación de un piloto controlado

**Ciclo P3-518 a P3-533 · decisiones docentes FD-PILOT-01 a FD-PILOT-08 · 2026-11-22.**

Este documento registra la ratificación de `GI_MANAGEMENT_TRACE_V1` **para preparar** un piloto de desarrollo pequeño, supervisado y reversible. También registra el paquete que lo prepara. **No es** validación clínica, aprobación de producción ni despliegue a residentes. **No se inició ningún piloto con residentes reales.**

## 1. Revisión humana y ratificación (P3-518, P3-519)

La revisión humana de `GI_MANAGEMENT_TRACE_V1_FACULTY_REVIEW` se registró **tal como se reportó**, con la procedencia `HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED`. En este contenedor no hay almacén persistido de esa revisión: una búsqueda sólo encontró transcripciones del asistente, que no son evidencia humana.

- **Juicios:** 10 caminos con `ACCEPT_WITH_LIMITATION` 10, `ACCEPT` 0, `RECALIBRATE` 0 y `REJECT` 0.
- **Hallazgos,** copiados con sus palabras:
  - coherencia causal en los diez caminos;
  - ningún camino requiere recalibración;
  - los caminos negativos o incompletos son útiles si se enmarcan con claridad;
  - la hemorragia en curso sigue visible;
  - la norepinefrina se muestra como soporte temporal de la presión;
  - la sangre y el cristaloide no implican control del sangrado;
  - no se infiere razonamiento del residente.
- **No se inventó** nada de lo siguiente: Q1–Q6, comentarios por camino, eventos de bloqueo, marcas de tiempo ni identidad.

El registro de ratificación `GI_MANAGEMENT_TRACE_V1_RATIFICATION` contiene:
- el estado `RATIFIED_FOR_CONTROLLED_DEVELOPMENT_PILOT_PREPARATION`;
- las decisiones FD-PILOT-01 a 08;
- lo que **no** se reabre: la calibración de presión de GI, la del tono común y la de la tasa manual de norepinefrina, la seguridad de las órdenes y la calibración de los caminos;
- los significados de manejo (razonable, temporizador, incompleto, claramente no beneficioso) como **interpretaciones docentes**: nunca puntajes, nunca rótulos de corrección y nunca visibles al participante;
- H1 y H2 **abiertos**, con su tratamiento en el piloto.

Los registros son `docs/revision/PHASE3_HUMAN_GI_MANAGEMENT_TRACE_REVIEW.json`, `GI_MANAGEMENT_TRACE_V1_RATIFICATION.json` y `GI_MANAGEMENT_TRACE_PILOT_SCOPE_V1.json`: sellados, versionados e indexados. Los genera `test_gi_pilot_records.py`.

## 2. Alcance y casos (P3-520, P3-527)

`gi_pilot.SCOPE` es la fuente, y el registro de alcance la copia. Fija qué queda INCLUIDO, EXCLUIDO o DIFERIDO en cinco dimensiones: casos, intervenciones, salidas visibles, campos de la traza y controles docentes.

- **Caso:** sólo `gi_bleed_57m`. Es el caso de los diez caminos revisados, y su propio curso da las dos situaciones del piloto:
  - volumen y sangre con reevaluación;
  - una presión que vuelve a caer, de modo que la norepinefrina a tasa explícita se vuelve una decisión.

  `gi_bleed_72f` queda DIFERIDO porque no fue parte de la revisión humana. No se maximizó el número de casos.
- **Excluido** (FD-PILOT-06):
  - casos de vasopresor limitados por la bomba;
  - norepinefrina en edema pulmonar y en ACS;
  - otros vasopresores;
  - titulación por objetivo y dosis por peso.
- **Excluido también en las salidas:**
  - variables internas;
  - identificadores de concesión, instantánea y linaje;
  - categorías docentes;
  - todo puntaje;
  - fotografías del paciente (banco de imágenes apagado);
  - la capa de revisión heredada tras el encuentro (autorrevisión guiada, comparación con el modelo experto, análisis con IA);
  - toda llamada a IA.

**Configuración que falla cerrada** (`gi_pilot.evaluate`). El piloto está apagado salvo `MRS_PHASE3_GI_PILOT=on`. Exige:
- cuentas individuales;
- no ser un despliegue público alojado;
- no ser el despliegue del primer piloto;
- no combinarse con el entorno de revisión docente;
- la configuración de desarrollo publicada: autoridad, instantánea de presión ratificada, instantánea de tono, entorno `development` y sombra;
- un directorio de registro fuera del repositorio;
- ninguna clave de IA;
- el banco de imágenes apagado.

Si se pide el piloto y algo falta, la página se detiene. El participante ve un mensaje genérico; el docente ve la lista de problemas.

## 3. Frontera antes de la hemostasia no revisada (P3-521, FD-PILOT-04, H1)

**Primera barrera, antes del motor.** Las órdenes del turno ya están en el registro de órdenes (`order_pipeline.open_turn`) y todavía no se ejecutaron (`execute_bundle`). Ahí se aplica el mismo detector de la traza ratificada (`mt.is_definitive_request`). Si el turno pide control definitivo del sangrado (gastroenterología, endoscopia, radiología intervencionista o cirugía):
- el turno **no se ejecuta**;
- cada orden queda `RECORDED_NOT_MODELLED` con la razón «development pilot boundary»;
- el turno se registra tal como se escribió;
- el reloj no avanza y la autoridad no compromete ningún minuto;
- la siguiente ejecución termina el encuentro con el mensaje de frontera.

La interconsulta nunca llega al motor, así que la endoscopia del motor (`_endoscopy_minute`) no puede ocurrir.

**Segunda barrera, estructural.** En cada ejecución, si el estado del motor muestra igualmente una interconsulta definitiva, una endoscopia o un evento de hemostasia, el encuentro termina de inmediato y lo que siguió no se muestra.

No se implementó fisiología de control de fuente, y el motor, el lector y `clinical_core/` no se tocaron.

## 4. Lo que ve el participante (P3-522, FD-PILOT-05, H2)

`gi_pilot.FIELD_CLASSES` clasifica cada campo visible:

- **AUTHORITATIVE:** PAS/PAD y la PAM derivada, que son minutos comprometidos de la autoridad viva.
- **LEGACY_NONAUTHORITATIVE:** FC y ritmo; SpO₂, soporte, FR y trabajo respiratorio; relleno capilar, extremidades y apariencia; **estado mental**; resultados, historia y examen; y la narrativa de eventos.
- **DEVELOPMENT_ONLY:** la frontera, el aviso del piloto, la parada docente y la traza tras el encuentro.
- **HIDDEN:** V, T, ganancia de tono, escala de presión, coordenada de tasa, núcleo de cristaloide, deuda de oxígeno; identificadores de concesión, instantánea, linaje y digesto; la consciencia del núcleo común; las categorías docentes; y las referencias del participante y del encuentro.

**Estado mental.** En cada superficie del piloto se rotula como del modelo anterior: la celda del monitor, la tarjeta de respuesta del paciente, la línea de apariencia de la sala y el examen físico (general y neurológico, incluida la frase de interacción que deriva de él). **Una vez administrada la norepinefrina, se oculta** en todas ellas y una nota explica por qué. El registro guardado no cambia: sólo cambia la presentación. Desde la reparación de P3-532 los filtros son **transformaciones de texto puras**: no leen el campo `mental_status`. Rotulan u ocultan la frase que ya escribieron los lectores inventariados del motor, ubicándola por la estructura de la oración (`… RR n/min. <palabra>; respiratory effort …`, `Mental status: <Palabra>`) o, en la celda del monitor, por su rótulo. Tras la norepinefrina, una oración que el filtro no conoce se filtra por un vocabulario fijo (`gi_pilot.MENTAL_WORDS`), que cubre la escala propia del motor. Por eso el inventario de lectores de `mental_status` no cambió.

**Aviso del piloto.** Dice que la presión viene del modelo de desarrollo revisado y que todo lo demás viene del modelo anterior, no validado con él. También dice que no es una evaluación y que no se escriba información personal.

## 5. La traza tras el encuentro (P3-523)

El participante ve la traza ratificada (`mt.render`), extraída del **registro del piloto**: los turnos registrados y el artefacto. Así, lo que ve es lo mismo que comprueba el replay docente.

- **Separaciones:** el razonamiento del participante aparece tal como lo escribió, o como «no expresado». La traza de un encuentro real no tiene prioridad de escenario.
- **Cada orden con su destino en palabras simples:** «carried out», «not understood by the simulator; nothing was done», «recorded and not carried out (development boundary)», etc.
- **Soporte temporal frente a tratamiento definitivo:** la norepinefrina es soporte temporal; el sangrado no está controlado.
- **Frontera:** aparece siempre. Si el encuentro terminó por otra salida (parada docente, fin decidido por el participante, problema del registro), esa salida se agrega como frontera.

No hay categoría, puntaje ni internos. Si la traza no verifica, **se retiene** y el participante ve sólo una nota.

**Defecto declarado del constructo** (`TD-165`, punto 2). El verificador ratificado (`mt.trace_problems`) rechaza un turno sin avance del reloj a mitad del encuentro, porque su «nuevo estado» conserva la última lectura comprometida sin un compromiso en ese minuto. El código del constructo **no se editó**: sus registros sellados fijan su digesto. El piloto tolera exactamente ese caso y sólo cuando el reloj no se movió y el nuevo estado *es* el estado del paso, en valor, procedencia y fuente (`gp.carried_reading_tolerated`). Una prueba muestra que una lectura arrastrada falsificada, o un turno que sí movió el reloj, siguen rechazados.

## 6. Controles docentes (P3-524)

Página de supervisión, sólo para docentes y administradores:
- lista de encuentros (referencia seudónima, caso, estado, salida, turnos, minuto);
- **observar** los turnos registrados, con un botón de refresco;
- **detener** un encuentro;
- **inspeccionar** la traza, incluida la vista estructurada y la configuración, sólo para docentes;
- **marcar** una salida como UNSAFE o AMBIGUOUS, con su ubicación y una nota;
- **marcar el encuentro como inutilizable**, con su motivo;
- **revisar el replay**.

Ninguna acción docente cambia lo que ve el participante, salvo la parada, que lo dice. La parada se lee **antes** de que un envío pendiente pueda correr: la orden enviada después de una parada nunca se ejecuta.

## 7. Registro, replay y desidentificación (P3-525)

`gi_pilot.PilotStore` usa `encounters/PE-<16 hex>/` y guarda:
- `meta.json`: caso, llegada y configuración (sólo para docentes);
- `participant.jsonl`: los turnos tal como la página los registró, con presión y minuto, y la salida;
- `faculty.jsonl`: las acciones docentes;
- `artifact.json`: el artefacto de la autoridad;
- `trace.json`: la traza de cierre, escrita una sola vez.

Ambos registros son de **sólo agregado** y van **encadenados por digesto**: una cadena rota falla cerrado. Participante y docente nunca escriben el mismo archivo.

**Identificadores:**
- participante `P-<12 hex>` y docente `F-<12 hex>`: digestos de la cuenta con el id del piloto; ni nombre, ni usuario, ni id de cuenta;
- encuentro `PE-` aleatorio.

**Seudónimo, no anónimo:** volver a vincular un participante exige la base de cuentas. El texto libre del participante se conserva porque es el encuentro; por eso el aviso pide no escribir información personal.

**Revisión de replay.** Comprueba la cadena de los dos registros, que el artefacto verifica y se reproduce desde sí mismo, y que la traza se reextrae de los turnos registrados hasta la traza de cierre. Cualquier resultado distinto de MATCH deja el encuentro como no utilizable para análisis.

**Aislamiento de la puntuación (FD-PILOT-08).** El encuentro piloto **no crea un intento en la cuenta** (`curriculum_runtime.start_pilot_encounter`). Por eso no llega a progreso, portafolio, rúbrica ni superficies de evaluación, y `save_session` no escribe nada.

## 8. Fallo seguro (P3-526)

`gi_pilot.FAIL_SAFE`, probado:

| Situación | Comportamiento |
|---|---|
| desajuste o detención de la autoridad | el encuentro se detiene (AUTHORITY_STOP); sin retroceso al modelo anterior |
| encuentro piloto sin sitio de autoridad | no corre (AUTHORITY_UNAVAILABLE) |
| orden no reconocida o incompleta **antes** del primer minuto comprometido | se registra; no se hace nada; el encuentro sigue |
| turno sin avance del reloj **después** del primer minuto comprometido que no es puramente estructural | **el experimento se detiene de forma permanente** (`MINUTE_ALREADY_COMMITTED`); ver §9 |
| orden que el motor ejecuta y la autoridad no representa (p. ej., ácido tranexámico) | el experimento se detiene (AUTHORITY_STOP, comportamiento certificado) |
| solicitud de control definitivo | el turno no se ejecuta; el encuentro termina en la frontera |
| el estado del motor muestra control de fuente igualmente | el encuentro termina de inmediato |
| horizonte de dos horas | el encuentro termina en la frontera |
| registro no disponible o su registro docente roto | el encuentro se detiene; no se ejecuta nada más |
| replay que no coincide | la traza del participante se retiene; el docente ve MISMATCH |
| parada docente | termina en la siguiente acción o refresco del participante, antes de ejecutar nada |
| refresco, pestaña nueva o reinicio del proceso | nunca se reanuda; el registro lo muestra INTERRUPTED |
| segundo encuentro iniciado mientras otro está abierto (otra pestaña del mismo participante) | el abierto se registra INTERRUPTED y, en su propia ejecución siguiente, termina (`ENCOUNTER_CLOSED_IN_RECORD`) sin ejecutar la orden pendiente (revisión P3-531, F2) |
| dos sesiones que escriben el registro a la vez | el agregado es un solo paso serializado y bloqueado; la comprobación de escritura es única por llamada (F3) |
| la página no entrega la capa de la Fase 3 al piloto | el piloto pedido se rechaza antes de empezar («the development authority configuration cannot be read»); P3-532, `test_u1` |

## 9. Hallazgo material para la preparación: turnos sin avance tras el primer compromiso

En la página viva, con la configuración de desarrollo publicada, la autoridad certificada exige algo concreto tras el primer minuto comprometido. Un turno que no mueve el reloj sólo es «tranquilo» si todas sus acciones son estructurales: reevaluación, interconsulta o acceso venoso. Cualquier otro se rechaza con `MINUTE_ALREADY_COMMITTED`, y el experimento **se detiene de forma permanente**. Es una regla deliberada (revisión P3-28: «a plan, a held order, a clarification may not commit the same minute a second time»).

**Reproducido** en la base publicada `352d5fe` sin el piloto, y también con él. Lo detienen órdenes comunes de un residente que el lector responde con una pregunta o no entiende:
- «Give normal saline.», sin volumen;
- «Start a pantoprazole infusion.», sin dosis;
- «Start norepinephrine.», sin tasa;
- «Titrate norepinephrine to MAP 65.»;
- una pregunta escrita como orden.

En cambio, «Check a hemoglobin.» y «Place a second large-bore IV.» no lo detienen.

**El ejecutor de desarrollo del ciclo anterior no reproduce esta detención.** No llama a la autoridad en esos turnos. Los diez caminos revisados no la encontraron porque todos sus turnos mueven el reloj.

**Lo que hace el piloto:**
- **no** elude la autoridad: hacerlo sería saltarse la única autoridad viva;
- **no** cambia su regla: eso sería un cambio de la autoridad certificada, no autorizado;
- lo declara en el lanzador («Write each order complete … can end the development encounter early»);
- termina el encuentro con el mensaje operativo;
- lo fija con una prueba (`test_gi_pilot_page.py::test_p16`).

Para la pregunta principal del piloto (FD-PILOT-07: decisiones secuenciales y consecuencias coherentes), esto es un **bloqueo práctico**: la primera orden incompleta de un residente, después de la primera reevaluación, termina el encuentro.

## 10. Ensayos en seco (P3-528, P3-529) y seguridad educativa (P3-530)

**Ensayo del residente,** con cuentas sintéticas, en AppTest y en Chromium real:
1. Arranque sin intento en la cuenta.
2. Volumen y sangre con la expectativa escrita por el residente.
3. Reevaluación a 60 minutos.
4. Norepinefrina a 10 mcg/min.
5. Examen.
6. Solicitud a gastroenterología → frontera.
7. Traza.

Resultado: sin scroll horizontal; ningún token prohibido en todo lo que el navegador recibió en la sesión del residente; capturas revisadas.

**Ensayo docente:**
- supervisión, revisión de replay (cuatro MATCH) e inspección de la traza;
- marca y «inutilizable» sin tocar el registro del participante;
- parada que impide la siguiente orden.

**Ataques de seguridad educativa,** todos fijados por prueba:
- vasopresor como sustituto del volumen;
- la sangre detiene el sangrado;
- presión normal igual a curación;
- esperar es aceptable;
- estado mental falsamente validado;
- hemostasia no revisada que aparece;
- camino negativo que parece recomendado;
- categoría docente como puntaje;
- razonamiento inventado.

Ninguno tiene implicación material dentro del piloto. Las pruebas son `test_gi_pilot.py::test_u18` (sobre la traza del participante: soporte que no reemplaza el volumen, líquido y sangre que no detienen el sangrado, el tiempo que pasa con el sangrado activo, cada estado nuevo con «bleeding not controlled», ninguna palabra de recompensa o recomendación, ningún estado mental, ningún razonamiento inventado), `test_gi_pilot_page.py::test_p6b` (lo mismo sobre la pantalla real del residente tras el encuentro), `test_p3` y `test_u6`/`test_u17` (estado mental), `test_p4` y `test_u3` (hemostasia no revisada), `test_p5` (categoría docente o puntaje) y `test_p6` (razonamiento sólo como se expresó).

## 11. Revisión adversarial independiente (P3-531)

Una revisión independiente, de sólo lectura, de un agente que no escribió el piloto, atacó las diez áreas del encargo con sondas propias. Cada hallazgo material se **reprodujo antes** de corregirse, se corrigió y quedó fijado por prueba. Cada corrección se comprobó con un mutante que la prueba detecta.

**Materiales (cuatro, corregidos):**
- **F1 · estado mental en español tras la norepinefrina.** Quien elegía «Español» antes de empezar leía «Alerta» y «Estado mental: Alerta» en la respuesta del paciente y en el examen: la página traducía el evento **antes** de la transformación del piloto, que sólo conocía las palabras inglesas.
  - El encuentro piloto se presenta sólo en inglés (`start_pilot_encounter` fija `encounter_language = "en"`).
  - La transformación se aplica sobre las palabras **inglesas** del evento, antes de cualquier traducción, así que el idioma elegido tras el cierre tampoco la salta.
  - Cada barrera protege sola (dos mutantes). Pruebas: `test_gi_pilot_page.py::test_p17`.
- **F2 · una segunda pestaña.** La segunda pestaña del mismo participante marcaba el primer encuentro `INTERRUPTED`, pero éste seguía ejecutando órdenes con autoridad y docencia ya no podía detenerlo.
  - Ahora `check` lee el estado del registro en cada ejecución: si ya no está `ACTIVE`, el encuentro termina con su propia salida (`ENCOUNTER_CLOSED_IN_RECORD`) antes de que corra la orden pendiente.
  - Prueba: `test_p18`.
- **F3 · carreras dentro del único proceso.**
  - La comprobación de escritura del almacén usaba un nombre por proceso, compartido por todos los hilos de sesión: un encuentro sano podía terminar como `PILOT_RECORD_UNAVAILABLE`. Ahora el nombre es único por llamada.
  - El agregado a una bitácora leía y escribía sin bloqueo: seis docentes a la vez rompían la cadena, y desde entonces ningún «Stop» se podía registrar. Ahora el agregado es un solo paso, serializado entre hilos y bloqueado entre procesos (`fcntl.flock`).
  - Prueba: `test_gi_pilot.py::test_u19`.
- **F4 · imágenes activas en los secretos.** El banco de imágenes lee primero los secretos y el piloto leía primero el entorno: con `off` en el entorno y `on` en los secretos, el piloto no se negaba. Ahora se exige `off` en **toda** fuente que lo fije. Pruebas: `test_u2` (filas nuevas) y `test_p19`.

**Menores corregidos:**
- **F5.** Las banderas del primer piloto y del entorno docente de revisión puestas sólo en los secretos también niegan el piloto.
- **F6.** Sin `MRS_PHASE3_AUTHORITY_STORE` el piloto se niega antes de empezar, en lugar de abrir y cerrar cada encuentro como `AUTHORITY_UNAVAILABLE`.
- **F8.** Las fichas internas del registro de órdenes («unread», «plan:future_timed», «held_with_question») ya no se muestran: el participante lee sus propias palabras entre comillas (`test_u20`).

**Menores declarados (sin corregir, `TD-165`):**
- **F7.** La cadena de hashes no tiene clave: quien pueda escribir el directorio puede rehacer una cadena coherente. La repetición tampoco verifica `meta` ni contrasta las órdenes con el artefacto.
- **F9.** El seudónimo se recupera hasta el id de cuenta enumerando ids pequeños. De ahí a la persona hace falta la base de cuentas.
- **F10.** La revisión de `procedure_events` en `engine_source_control` es código muerto. Las de `consultations` y `endoscopy_at` siguen activas y bastan.
- **F11.** Un encuentro abandonado (pestaña cerrada, sesión cerrada) queda `ACTIVE` en el registro hasta que el mismo participante empiece otro. Un «Stop» docente sobre él queda registrado, pero no hay sesión que lo aplique.
- **Sin reproducir.** En el modo de conversación, si el paciente puede hablar deriva del estado mental heredado y podría delatarlo tras la norepinefrina.

**Observación propia del ensayo.** Tras el encuentro siguen visibles los botones heredados «Save & return to dashboard» y «End this attempt without completing review». Sin intento de cuenta no escriben nada (`curriculum_runtime.save_session` y `return_to_dashboard` salen sin `_attempt_id`), pero sus rótulos no corresponden al piloto.

**Áreas que se sostienen,** con evidencia de la revisión:
- control de la fuente: 47 formulaciones, incluidas las diferidas, encadenadas, con hora, en español y por completado de un paquete retenido;
- autoridad: un sitio detenido o ausente termina el encuentro, sin retroceso al modelo heredado;
- puntaje y cuenta: nada se escribe sin intento;
- órdenes vasoactivas: falla cerrado;
- lectura arrastrada: sólo se tolera en su forma exacta;
- roles: la supervisión se decide en el servidor, y docencia sólo escribe su bitácora;
- sin la bandera: la página no cambia.

## 12. Certificación (P3-532) y punto de control (P3-533)

El cambio toca la plomería ejecutable (`app.py`, `curriculum_runtime.py`, `resuscitation_room.py` y dos módulos nuevos), así que el candidato se certifica completo sobre **una sola huella**: la suite particionada y `run_regressions.py`.

**Primera corrida: falló, y el candidato se reparó.** La primera certificación, válida sobre su huella, dio 16 fallas en 14 772 pruebas, y `run_regressions.py` también falló. Las fallas se clasificaron así:

- **13 eran regresiones de este cambio (11 de C1 y 2 de C2).** Son guardas estructurales del árbol que el piloto cruzaba:
  - sólo `app.py` importa la autoridad, su almacén y la sombra;
  - el tiempo de ejecución llega al núcleo común sólo por los cruces declarados (el piloto llegaba por `runtime_pressure_snapshot`);
  - los lectores de `mental_status` son un inventario cerrado (el piloto leía el campo para rotularlo);
  - un registro de tono enumera los módulos del árbol (C2).

  A eso se suma la regresión v0.8.2, que ejecuta `_vitals_grid_html` sola y no conocía el gancho del piloto.
- **Dos eran ambientales (C4):** tiempos de espera de AppTest, con 24 particiones en 4 núcleos.
- **Una (`test_phase3_minute_validation`, C3) es una no-determinación previa del arnés de prueba.** No se reproduce aislada ni en el orden exacto de su partición.
  - El arnés de la serie nombraba cada experimento con `id(self)`, y las dos series del módulo comparten un almacén que sólo crea registros.
  - Si se reutiliza una dirección de memoria, el nombre choca con otro contenido. El almacén lo rechaza y la autoridad se detiene (`ARTIFACT_PERSISTENCE_FAILED`).
  - Una sonda que reutiliza el `id` reproduce exactamente esa detención.
  - El arnés usa ahora un contador por proceso. Ninguna prueba ni registro fija esos nombres.

**La reparación sigue el patrón que ya usan las páginas de revisión docente.**
- Los módulos del piloto no importan nada de la capa de la Fase 3. El bloque del piloto en `app.py`, el único cruce de la página, les entrega una `gi_pilot.Layer` estrecha: nombres de configuración, comprobaciones puras, la verificación y el replay de un artefacto **guardado**, y el sitio del encuentro por el propio ayudante de la página (`_runtime_authority_site`, la llamada que la página hace en cada turno).
- Ningún miembro abre, avanza, compromete ni escribe una autoridad propia (`test_u22`, `test_u23`).
- Los filtros de estado mental son transformaciones de texto (§4, `test_u24`).
- `_vitals_grid_html` vuelve a ser autocontenida.
- Dos adaptaciones declaradas:
  - `test_c2` declara los dos módulos nuevos entre los posteriores a su registro;
  - el recuento de llamadas al ayudante del sitio en `app.py` pasa de dos a tres. La tercera es la capa del piloto, fijada dentro de su bloque, y las dos rutas de la página no cambian.
- Tras la norepinefrina, el filtro del texto de respuesta retiene también cualquier otra mención del vocabulario.

Los tres registros de este ciclo, que nunca se commitearon, se regeneraron con el código reparado. Su contenido no cambió: sólo cambiaron la procedencia del código generador y los digestos encadenados.

**Segunda corrida: falló, y el candidato se reparó otra vez.** Sobre la huella `ee8d8f6f…`, válida en sus dos extremos, dio 16 fallas en 14 775 pruebas (0 errores, 99 omitidas, 1 xfail). `run_regressions.py` pasó: 56/56 activas y 10 retiradas.
- **Dos eran regresiones de la reparación anterior (C5).** Al sacar de `gi_pilot.py` los imports de la capa, la configuración publicada quedó como constantes literales. Dos guardas permiten nombrar las instantáneas ratificadas sólo a un conjunto **exacto** de módulos ejecutables: `test_phase3_joint_region_ratification::test_t9` y `test_phase3_tone_ratification::test_t19`.
  - El piloto no puede alcanzar los módulos de enlace: sólo `app.py` cruza, y sólo hacia la autoridad y la sombra.
  - Por eso las dos guardas declaran ahora `gi_pilot.py` (adaptación declarada). Lo fijan a **una** mención de cada identificador, sin import de un enlace y sin ruta de registro.
  - `test_u23` mantiene las constantes iguales a las de los enlaces.
  - Lo demás que protegen no cambió: ni la limitación monitoreada, ni el marcador de cierre, ni los registros humanos, la ratificación o el punto de control los nombra el piloto.
  - Cinco mutantes se detectan: una segunda mención, un import, nombrar el punto de control de tono, nombrar la limitación y una ruta de registro.
- **Catorce eran ambientales (C6):** tiempos de espera de AppTest de 20 s.
  - Un `pytest` huérfano de la suite completa, que dejó una sonda anterior de este ciclo, ocupó uno de los cuatro núcleos durante 2,5 h.
  - Se detuvo, y las catorce pasan aisladas sobre la misma huella: 14 aprobadas en 134 s, con carga 0,4.

**Tercera corrida.** Las cifras finales, la huella y la clasificación de cada fallo están en la fila FD-P3-305 del Decision File y en el registro sellado `docs/revision/PHASE3_GI_PILOT_READINESS_CHECKPOINT.json` (`GI_PILOT_READINESS_CHECKPOINT_V1`). Ese registro lleva **un solo veredicto** de los seis (A–F) y, para cada uno de los otros, por qué no. Como en los ciclos anteriores, la fila, el registro, su entrada del índice y el pin movido se agregan **después** de la huella certificada.

Lo que decide el veredicto es el hallazgo de la §9: la regla certificada de turnos sin avance hace que la primera orden incompleta de un residente termine el encuentro. Para la pregunta principal del piloto (FD-PILOT-07) eso es un problema de arquitectura de la autoridad, no del piloto. Cambiar la regla es una decisión docente con su propia certificación.

## 13. Qué no se hizo

- sin fisiología nueva y sin control de fuente;
- sin recalibrar GI, el tono, la norepinefrina ni los caminos;
- sin tocar el lector, el motor, `clinical_core/`, las concesiones ni las instantáneas;
- sin cambiar la regla de la autoridad;
- sin ampliar la autoridad en familias limitadas por la bomba, de consciencia ni terminal;
- sin puntaje ni consecuencias;
- sin iniciar ningún piloto con residentes reales;
- sin afirmación de validación clínica.
