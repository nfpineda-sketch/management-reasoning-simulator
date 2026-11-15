# Revisión de trayectorias docente (UX-001 a UX-013)

Fecha: 2026-11-14. Rama: `phase-3-runtime-integration`. Alcance: **sólo capa de UX de revisión** para el entorno docente de revisión controlada de la autoridad de presión de GI (`gi_bleed_57m`, `gi_bleed_72f`). **No** cambia fisiología, trayectorias, autoridad, concesión, instantánea, casos, puntuación, la UI del residente ni el primer piloto; **no** es validación clínica, piloto con residentes ni autoridad de consciencia. Decisiones: FD-UX-01 a FD-UX-08 (`docs/COLA_DECISIONES_AI_ADVISOR.md`).

Distingo en todo el documento: **implementado** · **probado** (con el comando y la cifra) · **pendiente**.

## 0 · Por qué
La primera persona revisora humana intentó FR-B y encontró el flujo en vivo «innecesariamente complejo»: jugar el encuentro, localizar un panel oculto, crear un paquete a mano, anotar códigos, alternar entre la app y varios archivos `.md`, mantener un formulario en papel, recordar qué hoja del comparador podía abrir, revelar a mano, anotar el identificador de retroalimentación y salir por una ruta de menú especial. Es auditable, pero es mala UX humana. Decisión (FD-UX-01): un flujo **separado**, optimizado para la persona docente, que revisa **trayectorias certificadas ya almacenadas**. El modo en vivo queda intacto.

## 1 · UX-001 · Auditoría de fricción del flujo anterior (FR-B, el escenario más simple)
Cada acción manual de la persona revisora, clasificada. `CJ` = `CLINICAL_JUDGMENT_REQUIRED`; `AM` = `AUDIT_METADATA`; `IA` = `IMPLEMENTATION_ARTIFACT`; `UF` = `UNNECESSARY_REVIEWER_FRICTION`. Conteo **por inspección del procedimiento del kit** (`04`, `06`, `07`), **no medido con una persona**.

| # | Acción manual (kit 01–10) | Acciones | Clase |
|---|---|---|---|
| 1 | Abrir `05_escenarios.md` / `FR-B_hoja_autoridad.md` para saber el guion y la tabla | 2 cambios de archivo | UF |
| 2 | Elegir el escenario en `Review encounter` y pulsar `Begin review encounter` | 2 | IA |
| 3 | Teclear **exactamente** 4 órdenes del guion y enviarlas (sin añadir plazos o se desvía el recorrido) | 8 | IA (repetir un encuentro para obtener una trayectoria que ya existe) |
| 4 | Completar 2 formularios de razonamiento de 4 preguntas (texto sugerido, a veces prellenado) y pulsar el botón | 8 | IA |
| 5 | Encontrar el panel oculto `FACULTY DEVELOPMENT REVIEW PANEL` y abrirlo (no se abre solo si no hay parada) | 1 | UF |
| 6 | Pulsar `Create review bundle` | 1 | AM |
| 7 | Anotar el código del paquete en `07_registro_artefactos.md` | 1 | AM |
| 8 | Leer la vista de autoridad como árbol JSON | — | UF (JSON crudo) |
| 9 | Responder Q1–Q5 en pantalla | 5 | **CJ** |
| 10 | Repetir Q1–Q5 y la impresión global en el formulario de papel `06` | 6 | UF (duplicación) |
| 11 | Pulsar `Reveal the nonauthoritative comparison` | 1 | CJ (es parte del método) |
| 12 | Abrir `FR-B_hoja_comparador.md` | 1 cambio de archivo | UF |
| 13 | Responder Q8, Q9 y `Overall.` | 3 | **CJ** |
| 14 | Elegir `Reviewer role` | 1 | AM |
| 15 | Comentarios | 1 | CJ (opcional) |
| 16 | `Submit feedback` y anotar el identificador `Feedback stored` en `07` | 2 | AM |
| 17 | Salir: `☰ Menu` → `End this attempt without completing review` (si no, se pierde lo no guardado) | 2 | IA |
| 18 | Al terminar la sesión: `08_resumen_fin_de_sesion.md` y avisar a la persona operadora para ejecutar `session_summary.py` | 1 archivo + aviso | IA |

**Total anterior (FR-B): ≈ 42 acciones de la persona revisora y ≥ 3 cambios de archivo por escenario**, de las cuales **sólo 9–10 son juicio clínico** (`CJ`). El flujo nuevo expone **sólo** `CJ` (y el método de ciego): lo demás sigue ocurriendo, pero **automáticamente** como metadato de auditoría.

## 2 · UX-002 · Objeto de revisión de trayectoria
`faculty_trajectory_review.py` (puro: sin Streamlit, sin motor, sin autoridad, sin concesión, sin núcleo; lo verifica `test_m15`). Se deriva del **paquete de revisión certificado** (`runtime_faculty_bundle`) guardado en el **conjunto de revisión** `docs/revision/PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json` (7 escenarios, fijado por digesto).
* **Visible a la persona revisora:** escenario, contexto clínico corto (la presentación del caso y los signos de llegada), línea de tiempo de intervenciones (texto de la orden y qué hizo el encuentro; **nunca** el texto del formulario de razonamiento), trayectoria de la autoridad (PAS/PAM/PAD), FC y llenado capilar **como se mostraron en el encuentro** (contexto, no parte de la trayectoria juzgada), preguntas ciegas, comparador, preguntas posteriores y juicio global.
* **Oculto, conservado como auditoría:** id del paquete, ids y digesto del artefacto, concesión, instantánea, linaje, digesto del conjunto, repetición, estado de la autoridad, cabeza del registro de eventos.
* **Cómo se obtuvo el conjunto sin tocar la fisiología:** `faculty_review_kit/tools/capture_trajectory_review_set.py` corre **una vez** los siete encuentros guionados en la página real (la misma ruta certificada de `test_phase3_faculty_review_page.py`), toma el paquete por la capa de paquetes **sin cambios** y lo congela junto con lo que el residente vio. **Rechaza escribir** si un escenario no coincide con la serie certificada (`PHASE3_PRESSURE_AUTHORITY_SERIES.json`); `--check` repite la captura en memoria y detecta deriva. En la **sesión de revisión no se ejecuta nada de eso**: sólo se lee el archivo y se re-verifica cada escenario al cargarlo (id del paquete, evidencia, serie certificada, minutos del comparador, digesto del conjunto). Un escenario que no verifica **no se ofrece**.

## 3 · UX-003 · Página ciega única (`faculty_trajectory_review_ui.py`)
Encabezado «Faculty Trajectory Review», `Scenario N of M` (5 obligatorios + 2 opcionales), título del escenario, tiempo restante estimado (**estimación de 4 min por escenario; no medida con una persona**). Luego: **A** contexto clínico; **B** tabla de intervenciones numerada; **C** gráfico de PAS/PAM/PAD (valores certificados; marcadores numerados en el minuto de cada intervención; una línea «Stop» donde el experimento se detiene). Eje 0–140 mmHg en todos los escenarios (comparable); color por variable (azul PAS, naranja PAM, verde PAD; validado con `validate_palette` en claro y oscuro, separación para daltonismo). FC y llenado capilar en un desplegable. Sin información de depuración.
* **Q1–Q5 (UX-003A)** exactamente como en el encargo: Dirección (Expected/Partly/Wrong), Momento (Too early/Plausible/Too late), Magnitud (Too small/Plausible/Too large), Respuesta al manejo (Coherent/Uncertain/Incoherent), Riesgo educativo (No/Maybe/Yes), más comentario libre opcional. **Sin formulario de papel.**
* **Q5H (decisión del arquitecto, FD-UX-05, pendiente de confirmación docente):** una pregunta condicional «¿el experimento se detuvo en un punto comprensible?» sólo en los escenarios con parada, para no perder la revisión de la experiencia de parada. La nota de parada es operativa («no un resultado del paciente»), sin palabras de muerte ni «terminal».

## 4 · UX-004 · Revelado del comparador
Un solo botón, `LOCK FIRST IMPRESSION & REVEAL COMPARATOR`, deshabilitado hasta que todas las preguntas obligatorias están respondidas. Al pulsarlo: las respuestas ciegas **se fijan** (evento de bloqueo con su sello de tiempo; las respuestas bloqueadas son las **leídas del registro, nunca las del llamante**, y sólo cuentan si todas las preguntas obligatorias tienen respuesta), aparece el comparador. Sin el estado bloqueado, **no hay forma de obtener los números del comparador** del módulo (`comparator_view` lanza `Locked`) y **ningún** elemento enviado al navegador antes del bloqueo contiene un valor, una serie o la palabra «legacy» (probado sobre etiquetas, tablas **y datos del gráfico**, `test_u1`). Rotulado «Legacy comparator — nonauthoritative comparison»; nota: «una diferencia respecto del motor heredado no es un error y la cercanía no es éxito… no es un estándar de referencia». Nunca «verdad», «correcto» ni «estándar de referencia» (`test_m16`).
**UX-004A:** gráfico superpuesto **Common authority (líneas continuas) vs Legacy comparator (discontinuas)** con los mismos ejes y escala de tiempo; marcadores de intervención **una vez**; tabla de diferencias (común − heredado, mmHg) en un desplegable. La persona no compara dos tablas `.md` a mano.

## 5 · UX-005 / UX-006A · Posterior al revelado y autoguardado
Tras el revelado: «¿Ver el comparador heredado cambió tu juicio?» (No / Sí — aumenta la confianza en la trayectoria del núcleo común / Sí — aumenta la preocupación), comentario opcional «después del revelado» y **juicio global** (ACCEPT, ACCEPT_WITH_LIMITATION, RECALIBRATE, REJECT).
**Persistencia:** un registro de eventos **de sólo añadido y encadenado por hash** por (revisor, escenario, paquete, ítem), con `flock` exclusivo y `fsync` del archivo y del directorio (`<almacén>/faculty_review/trajectory/<ref>/<escenario>__<paquete>__<ítem>.jsonl`). Cada respuesta se guarda **al darla**, por un *callback* del widget que la persona cambió (corre antes del cuerpo de la página: un widget viejo de otra pestaña nunca pisa una respuesta más nueva); un refresco restaura la respuesta, el comentario y el estado; tras el bloqueo **nunca** se desbloquea (el escritor rechaza el evento y el lector ignora un evento posterior forjado aunque esté bien encadenado); un registro alterado, truncado o reordenado es **ilegible** y no se escribe más; una cola truncada sin confirmar se ignora y se descarta antes de añadir. Un paquete o ítem distinto es un registro distinto y **no hereda respuestas**. Un refresco del navegador cierra la sesión de la cuenta (así funciona la aplicación con cuentas individuales): al volver a iniciar sesión, las respuestas guardadas están ahí (comprobado en un navegador real).

## 6 · UX-006 · Vinculación automática
La persona **nunca** copia ni ve identificadores. El registro final (`<almacén>/faculty_review/trajectory_reviews/`, creación única, atómica) vincula por sí mismo: revisor (referencia opaca de 12 hex; **sin** nombre de cuenta), rol, escenario, caso, paquete, artefacto y su digesto, concesión, instantánea, digesto del conjunto, comparador, respuestas ciegas **y su instantánea al bloquear**, momento del revelado, respuestas posteriores, juicio global y cabeza del registro de eventos. Su identidad se recalcula. El paquete que la persona vio se guarda además en su almacén (`bundles/`, idempotente) sin que haga nada. Un envío repetido, concurrente (8 hilos probados) o reintentado tras una caída entre el registro y el evento de cierre **no crea un segundo registro** (`test_m8`, `test_m9`).

## 7 · UX-007 · Navegación
Tras `Submit and continue` se pasa **solo/sola** al siguiente escenario (sin ruta de menú). Barra de escenarios (✓ enviados), progreso `N de 5`, tiempo restante estimado. Se puede **ver** (no modificar) un escenario ya enviado; no se puede entrar a uno que no es su turno (probado forzando la clave de sesión). Un envío que falla **no avanza**.

## 8 · UX-008 · Resumen final
Al terminar los 5 obligatorios: `REVIEW COMPLETE · 5/5 required scenarios reviewed`, recuento Accept / Accept with limitation / Recalibrate / Reject, tabla por escenario, **comentarios a seguir**, los opcionales (FR-D, FR-C) ofrecidos. **El resumen técnico se crea solo** (`<almacén>/faculty_review/trajectory/session_summary_<ref>.json`: vínculos verificados, comprobaciones técnicas, juicios tabulados). **No** se exige `08_resumen_fin_de_sesion.md`. Los recuentos son los juicios de la persona, tabulados: **el software no los interpreta, no los puntúa**.

## 9 · UX-009 · Aislamiento docente
El flujo vive **dentro** del lanzador docente, que sólo existe en un proceso que declaró `MRS_FACULTY_DEVELOPMENT_REVIEW` y supera la misma puerta (cuentas individuales, rol docente/administrador, entorno de desarrollo, casos fuera de línea, almacén local, proceso único, sin piloto…); la página vuelve a comprobar el rol. Un residente recibe sólo la negativa genérica y **no se crea nada** a su nombre; un despliegue sin la bandera no tiene ni el selector (`test_u5`, `test_u7`). Los módulos nuevos **no importan** motor, autoridad, sombra, concesión ni núcleo común (`test_m15`).

## 10 · UX-010 · Migración de FR-A…FR-G
Los siete paquetes existentes se migran al conjunto (capturados de las mismas corridas certificadas; **no** se regeneró ninguna fisiología ni se volvió a ejecutar la autoridad para dibujar la revisión). Orden: FR-B, FR-A, FR-E, FR-G, FR-F (obligatorios); FR-D, FR-C (opcionales). Cada escenario coincide con la serie certificada.

## 11 · UX-011 / UX-011A · Flujo humano de extremo a extremo y conteo
`test_phase3_trajectory_review_page.py` (AppTest sobre la `app.py` real): inicio de sesión → FR-B ciego → Q1–Q5 → **refresco (estado restaurado)** → bloqueo → comparador → respuestas posteriores → juicio global → envío → siguiente escenario automático → los 5 obligatorios → resumen; además FR-D opcional. **Ningún archivo `.md` es necesario** (el texto de la pantalla no menciona archivos ni papel).

| | Flujo anterior (FR-B) | Flujo nuevo (por escenario) |
|---|---|---|
| Acciones de la persona revisora tras iniciar sesión | ≈ 42 | **9** (5 respuestas ciegas + 2 posteriores + 1 clic de revelado + 1 clic de envío) · 10 en escenarios con parada (Q5H) |
| Cambios de archivo | ≥ 3 (guion, hoja de autoridad, hoja del comparador) + papel | **0** |
| Códigos copiados a mano | 2 (paquete, retroalimentación) | **0** |
| Salida por ruta de menú especial | sí | **no** |
| Tiempo por escenario | ≈ 8 min (estimación del kit: 32 min de escenarios + 5 + 3 para 5) | ≈ 4 min (**estimación del autor, no medida con una persona**) |

Medido en la prueba (`test_u3`): 7 respuestas + 2 clics por escenario sin parada, 8 + 2 con parada; 5 escenarios obligatorios = 37 respuestas y 10 clics. El «≈ 42» anterior y los tiempos son estimaciones por inspección; **ninguno se midió con una persona**.

## 12 · UX-012 · Revisión adversarial independiente y reparaciones
Un revisor independiente, de sólo lectura, con sondas propias (`/tmp/adv_review_ux/`, fuera del repositorio), atacó las 14 amenazas del encargo. **0 bloqueantes.** **No reprodujo** ni la fuga del comparador antes del bloqueo (sobre todos los elementos de los siete escenarios, incluidos datos de gráficos, barra lateral y excepciones; ni forzando claves de sesión; ni con una segunda sesión de la misma cuenta) ni la edición de la primera pasada tras el bloqueo (pestaña vieja, eventos forjados bien encadenados, 5 pruebas × 8 procesos). Encontró **3 mayores, 6 menores y notas**; **cada uno se reprodujo con una sonda propia (pruebas de regresión que fallaban) antes de corregirlo**:

| Id | Gravedad | Hallazgo | Reparación | Prueba |
|---|---|---|---|---|
| F1 | MAYOR | El registro y la bitácora podían discrepar (un `set_overall` de otra pestaña entre la escritura del registro y el cierre; 4 de 6 intentos) y nada lo señalaba. | El envío es **una sola sección crítica** bajo el mismo `flock`: lee el estado, escribe el registro y cierra la bitácora sin que nadie pueda intercalarse. `record_problems` compara campo a campo. | `test_m17` (25 pruebas con un escritor concurrente) |
| F2 | MAYOR | Tras una caída entre el registro y el cierre, cualquier cambio posterior movía la cabeza del registro de eventos y el reintento fallaba **para siempre** («another record has this identity»): la revisión entera quedaba bloqueada. | Un registro huérfano (la bitácora no está cerrada) se aparta como `…superseded-<id>.json` (se conserva para auditoría) y se reemplaza; nunca bloquea. | `test_m18` |
| F3 | MAYOR | El resumen contaba registros alterados o ajenos bajo un «REVIEW COMPLETE» verde y no señalaba uno faltante. | Sólo cuenta registros que **verifican** (identidad, revisor, escenario, paquete, ítem, conjunto, cabeza del registro de eventos y campo a campo contra la bitácora que lo cerró). Uno alterado, ajeno o faltante **no se cuenta** y se reporta; `complete` exige los cinco obligatorios verificados. | `test_m19` |
| F4 | menor | Un radio viejo (dos pestañas) sobrescribía una respuesta más nueva. | Guardado por *callback* sólo del widget cambiado. | `test_u10` |
| F5 | menor | Lo editado en la misma ejecución que un clic de navegación se perdía. | Los *callbacks* corren antes del cuerpo de la página. | `test_u11` |
| F6 | menor | «Review optional scenario FR-C» abría FR-D. | `enterable` incluye todos los opcionales pendientes tras los obligatorios. | `test_u12` |
| F7 | menor | El conjunto de revisión se atestiguaba a sí mismo; una edición re-firmada de llegada/título/guion o de los valores heredados se ofrecía; la bitácora no conocía la revisión del conjunto. | **Digesto fijado en código** (`PINNED_SET_DIGEST`); contraste con el escenario guionado certificado (título, razón, guion), con la presión de llegada certificada, con los valores del contrafáctico de la serie y con «común − heredado»; el digesto del ítem entra en la identidad de la bitácora y del registro. | `test_m21` |
| F8 | menor | Un error de disco mostraba al navegador un *traceback* con la ruta del almacén, la referencia del revisor y el nombre de archivo. | Todo error de E/S es un rechazo genérico («could not be saved»); los *callbacks* lo capturan; `os.write` se comprueba; se hace `fsync` del directorio. | `test_m22`, `test_u13` |
| F9 | menor | Un `lock` forjado y bien encadenado con una sola respuesta daba LOCKED y habilitaba el comparador; un evento sin `kind` o con `data` no-dict hacía lanzar a `_fold`. | El bloqueo sólo cuenta con **todas** las respuestas obligatorias y bloquea **lo que dice el registro**, no el evento; todo evento malformado hace la bitácora ilegible (sin excepción). | `test_m20` |
| notas | — | Propósito de FR-E mencionaba una comparación de consciencia que esta página no muestra; resumen mezclaba opcionales sin rotular; textos con «bundle/digest/identity» visibles; resumen técnico con permisos 0644; filtro de identificadores rechaza tripletes numéricos clínicos; FC/LLC vienen del motor heredado en la pantalla ciega. | Propósito de FR-E acotado; los opcionales se rotulan; los motivos técnicos van al registro del operador, no a la pantalla; resumen 0600/0700; el rechazo del filtro se **dice** («no guardado») y el texto queda en su caja (el filtro certificado se reutiliza y **no** se cambió); FC/LLC: nota de diseño declarada (no es presión ni está rotulado comparador). | `test_u14`, `test_m16` |

## 13 · Pruebas y adaptaciones declaradas
* Nuevas: `test_phase3_trajectory_review.py` (28 de modelo), `test_phase3_trajectory_review_page.py` (14 de página sobre la `app.py` real), `test_phase3_trajectory_review_checkpoint.py` (2).
* **Adaptada una prueba existente** (`test_phase3_faculty_review_page.py`, `_open`): por omisión el lanzador docente abre ahora la revisión de trayectorias, así que el ayudante selecciona el modo en vivo (`mode="live"`, valor por omisión del ayudante) para que las 77 pruebas existentes sigan ejerciendo el flujo en vivo **sin cambiar lo que protegen**. Un defecto real de mi primer enganche (al salir de un encuentro en vivo el selector volvía al modo nuevo: Streamlit descarta el estado de un widget que no se dibuja) lo detectó la prueba `e10` y se corrigió guardando la elección en una clave propia de la sesión.
* **El registro del punto de control P3-300 no se tocó** (su digesto `45b62670…` sigue igual): una primera versión del enganche añadía una importación a `faculty_review_ui.py` y rompía su afirmación «la página no importa nada de la capa de Fase 3»; se cambió a **inyectar** la página desde `app.py`, como ya se inyecta la capa de revisión.
* Deriva de la captura: `capture_trajectory_review_set.py --check` repitió la captura de los siete escenarios y **reprodujo** el conjunto almacenado (trayectorias, comparador, llegada, signos).
* Navegador real (Playwright sobre un servidor `streamlit run` de prueba con cuentas sintéticas): respuestas guardadas por *callback*, refresco con nuevo inicio de sesión que restaura las respuestas, bloqueo, comparador superpuesto, envío y paso automático a FR-A con su nota de parada.

## 14 · Límites declarados
* **No medido con una persona:** la usabilidad del flujo nuevo y su tiempo por escenario (≈ 4 min es la estimación del autor). El «≈ 42 acciones» del flujo anterior es por inspección del procedimiento del kit.
* **Q5H y la ausencia de Q8/Q9 de consciencia** son una decisión del arquitecto pendiente de confirmación docente (FD-UX-05).
* FC y llenado capilar se muestran **antes del bloqueo** tal como se mostraron en el encuentro (salida del motor heredado, sin presión heredada y sin rótulo de comparador): nota de diseño.
* Registro de sesión sin firma y proceso único (FD-FAC-05, FD-FAC-06): una bitácora o un registro cambiado por alguien con acceso de escritura **se detecta y no se cuenta**, no se impide.
* Una bitácora ilegible bloquea su escenario hasta que la persona operadora aparte el archivo (se conserva); el resumen lo reporta.
* El filtro de identificadores es el de la capa de paquetes certificada: puede rechazar tripletes numéricos clínicos («120 130 140»); la página lo dice y el texto no se pierde.
* Sin firma criptográfica, sin multiproceso, sin validación clínica, sin piloto con residentes, sin autoridad de consciencia.

## 15 · UX-013 · Punto de control
Registro: `docs/revision/PHASE3_FACULTY_TRAJECTORY_REVIEW_CHECKPOINT.json` (`test_phase3_trajectory_review_checkpoint.py`: el registro es lo que el código y los registros almacenados dicen ahora; cada estado cita sólo pruebas que existen).

| Estado | Resultado |
|---|---|
| BLINDED_REVIEW_FLOW | VERIFICADO (`m3`, `u1`, `u2`, `u3`) |
| COMPARATOR_REVEAL | VERIFICADO (`m4`, `m16`, `u2`) |
| FIRST_PASS_IMMUTABILITY | VERIFICADO (`m6`, `m7`, `m20`, `u2`, `u10`) |
| AUTOSAVE | VERIFICADO (`m5`, `m22`, `u2`, `u10`, `u11`, `u13`, `u14`) |
| ARTIFACT_LINKAGE | VERIFICADO (`m8`–`m11`, `m17`, `m18`, `u2`) |
| SCENARIO_NAVIGATION | VERIFICADO (`u2`, `u3`, `u4`, `u12`) |
| SESSION_SUMMARY | VERIFICADO (`m12`, `m13`, `m19`, `u3`) |
| FACULTY_ISOLATION | VERIFICADO (`m15`, `u6`, `u7`) |
| RESIDENT_ISOLATION | VERIFICADO (`u5`, `u7`) |

**Veredicto: A · `FACULTY_TRAJECTORY_REVIEW_READY_FOR_HUMAN_USE`**, con las salvedades de la §14. Habilita **un primer uso humano docente** en el entorno de desarrollo controlado y nada más; **no** es validación clínica, ni piloto con residentes, ni ampliación de la autoridad. Las cifras de la suite completa y la huella del árbol las da el informe final (no pueden estar en un registro que el propio árbol contiene).

## 16 · Qué no cambió
Fisiología, trayectorias (ni las de presión ni las de consciencia), autoridad, concesión (`GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1`), instantánea (`gi_pressure_committed`), casos, puntuación, UI del residente, primer piloto, `clinical_core/` y el motor heredado: **sin cambios**. Archivos tocados fuera de los nuevos: `faculty_review_ui.py` (sólo el selector de modo y un parámetro opcional), `app.py` (dos líneas: importar la página dentro del bloque de la bandera e inyectarla), `test_phase3_faculty_review_page.py` (el ayudante `_open`), `CLAUDE.md`, `docs/COLA_DECISIONES_AI_ADVISOR.md` y `faculty_review_kit/README.md`.
