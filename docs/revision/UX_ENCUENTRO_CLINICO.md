# UX del encuentro clínico — informe único (2026-10-02)

Instrucción: «UX DEL ENCUENTRO CLÍNICO — PROMPT ÚNICO FINAL» (2026-10-02). Sólo presentación: no se
modificó el lector, los routers clínicos, los casos, la fisiología, la temporización, la rúbrica, D1–D5,
el puntaje, −3, los eventos críticos, TDFC, C14, los mappings, la confirmación docente, los PDF ni la
lógica del Management Trace. `validation/`, `939978a` y `3d942ee` quedan intactos; no se abrió ninguna
respuesta externa.

- **Rama:** `clinical-encounter-v0.13`. **HEAD inicial:** `1766f4d`. **HEAD final:** el commit de UX que
  sigue a `1766f4d` (separado de todo cambio clínico).

## 1. CURRENT → PROPOSED

| | CURRENT (`1766f4d`) | PROPOSED (implementado) |
|---|---|---|
| Distribución | Foto a todo el ancho; monitor grande arriba a la derecha; consola de 35 % abajo a la derecha; barra lateral abierta que reserva ~300 px | Paciente en la mitad izquierda, casi toda la altura; monitor compacto sobre su esquina superior izquierda; a la derecha, información arriba y escritura abajo |
| Información | «Latest response» y un desplegable cerrado con tres pestañas (intercambio actual, informes, registro completo = transcript con lo escrito por el residente) y un panel «At the bedside» con signos, llene capilar y examen respiratorio **vivos** | Cuatro vistas: Evolución, Historia y examen, Resultados, Indicaciones (lo más reciente primero, cada entrada con su minuto) |
| Escritura | Radio de cuatro círculos; encabezado que cambiaba según el modo; botón «Submit» | Título permanente «Management/Manejo»; cuatro modos como botones, uno solo marcado (fondo, borde, negrita y ✓); «Send/Enviar» |
| Reloj | En la cabecera del monitor, «00:14» | Uno solo, «Simulated time · 14 min / Tiempo simulado · 14 min», en la franja superior; los minutos de las entradas usan la misma convención |
| ECG | Expander «ECG recordings» con selector | Además, cada aviso de ECG ofrece «View ECG/Ver ECG», que abre ese trazado |
| Controles de desarrollo | «Image issue details» y «Retry patient image» visibles para residentes | Sólo docentes y administradores |
| Barra lateral | Abierta por defecto durante el encuentro | No se dibuja durante el encuentro; «☰ Menu/Menú» arriba a la izquierda |

## 2. Cambios visuales

1. **Distribución 50/50** (`clinical_scene.BEDSPACE_CSS`): la foto (`cover`, centrada; sin deformar) ocupa la
   mitad izquierda; el monitor compacto (≤ 44 % del ancho de la foto, ~110 px de alto) queda arriba a la
   izquierda; la nota sobre los límites de la fotografía sigue abajo, igual.
2. **Monitor:** valores reales; la presión no se parte (`white-space: nowrap`); la unidad junto a la etiqueta.
3. **Franja superior:** «Simulated time · N min» y el botón «ECG».
4. **Cuatro vistas** (`encounter_screen.py`, que sólo decide dónde se muestra cada entrada según su tipo):
   - **Evolución:** todo evento salvo los del intercambio (`you`, `reasoning_completion`, `clarification`,
     `prototype`, `reasoning_note`, `order_cancelled`); un tipo desconocido se muestra, nunca se descarta.
   - **Historia y examen:** peso y talla, la fuente de la historia, cada respuesta con su pregunta y cada
     examen con la región pedida (nunca con el texto de una orden); un examen no se actualiza.
   - **Resultados:** lo pendiente, los informes recibidos con «View ECG», el visor «ECG recordings» y el panel
     «Diagnostics» (plegado, por la regresión v0.7.12). Lo pendiente lleva su minuto sólo donde el registro
     clínico ya lo daba («pending · expected at N min»); en los motores de familia la sala dice cuándo vuelve un
     resultado sólo si el residente pide revisarlo, y eso cuesta minutos, así que la franja da sólo el nombre
     («Troponin: Pending / Troponina: Pendiente») y no adelanta nada.
   - **Indicaciones:** lo pendiente ahora, el soporte y los tratamientos en curso, y cada orden del
     Management Trace con su texto (verbatim), su resultado y los mensajes de la sala sobre ella; las
     cancelaciones como filas propias. El resultado se dice con el estado que registró el Management Trace y
     con las palabras que ya usa el registro de decisiones: «Action: …» si se ejecutó; si no, «Status:
     clarification required / Estado: requiere aclaración», «not executed / no ejecutada» (también la orden que
     el motor no corrió porque el paciente estaba en paro: el «terminal locked» del registro se lee en español
     como «cerrada al terminar el encuentro», que no es lo que pasó) o «Pending / Pendiente». Una orden sin
     entrada propia en el Trace (retenida y luego cancelada; una respuesta que no respondió la pregunta) se
     muestra con sus palabras y lo que siguió; un mensaje que no pertenece a ninguna orden («There are no
     pending orders to cancel.») es una fila propia. Cada mensaje aparece una sola vez. Los mensajes de cada
     orden se toman desde la entrada del residente que la registró, también cuando la sala retiró después su
     aviso de orden retenida (completar en texto libre o la anulación docente).
5. **Zona de escritura:** título, modos, respuesta de la sala a la última orden (recuadro compacto), la
   orientación breve existente, el cuadro y «Send/Enviar»; los cuatro campos cuando corresponden; «Complete
   Encounter & Begin Review». Con los cuatro campos abiertos o con la pregunta de cierre («How is this
   encounter ending?»), la zona de escritura se amplía y la información se reduce a sus pestañas.
6. **Menú:** cuenta, contraseña, idioma (deshabilitado durante el encuentro, como antes), «Save & return to
   dashboard» y «End this attempt without completing review».
7. Se retiró del encuentro el pie con la versión (sigue arriba de la página) y la frase «Act · anticipate the
   response · reassess» (la orientación traducida que ya existía queda como única orientación).

## 3. Partes diferidas o no implementadas

- **Hover del menú: DIFERIDO** (TD-60). `st.popover` de Streamlit 1.64 no lo ofrece; hacerlo exigiría
  JavaScript sobre la página. Tampoco hay «×»: el menú se cierra con Escape, un clic fuera o el mismo botón.
- **Texto «Repeat ECG available.»:** no se agregó una frase nueva; cada aviso existente de ECG («12-lead ECG
  acquired…» o «ECG: Performed at minute N…») lleva su botón «View ECG». El emparejamiento aviso–trazado se
  usa sólo cuando es seguro (tantos avisos como trazados, ninguno anunciado antes de existir); si no, no hay
  botón y el trazado sigue en Resultados.
- **Reevaluaciones programadas:** no existen como dato estructurado (el motor ejecuta la reevaluación en el
  mismo envío); la franja muestra sólo estudios pendientes.
- **Modo de contraseña compartida:** sin cuentas no hay roles, así que «Image issue details» y «Retry patient
  image» no se muestran a nadie (antes, a todos). El piloto usa cuentas.
- **Etiquetas sin español aprobado** (TD-61): los modos, «Complete Encounter & Begin Review», «Save & return
  to dashboard», los avisos de la orden retenida, etc. siguen en inglés en la vista en español, como antes.
  Sólo se agregaron las palabras que la instrucción dio en ambos idiomas.

## 4. Los cuatro campos (nombres exactos) y su semántica

Formulario `reasoning_completion_form_{gate_id}`, preguntas de `reasoning_questions.QUESTIONS`:

| Clave | Pregunta (EN) | ES |
|---|---|---|
| `working_model` | What do you think is going on? | ¿Qué crees que está pasando? |
| `action` | What are you going to do? (deshabilitado: la orden retenida) | ¿Qué vas a hacer? |
| `expected_effect` | What do you expect to happen, or what are you trying to clarify? | ¿Qué esperas que ocurra o qué buscas aclarar? |
| `reassessment_target` | What will you check, and when? | ¿Qué vas a revisar y cuándo? |

Más «I will check in… minutes» y la prioridad opcional; botón «Complete reasoning & execute held order».
El código del formulario, su disparador (`pending_reasoning`), la validación, el reloj y el registro no se
tocaron. Verificado (`test_encounter_screen.py` y la equivalencia): aparecen con el mismo disparador; con un
campo faltante el formulario sigue a la vista y conserva lo escrito; completados, desaparecen, la ejecución
queda en el Management Trace y el `reasoning_completion` queda en el registro sin aparecer en Evolución.

## 5. Qué sigue visible, qué deja de persistir visualmente y dónde se conserva

| Qué | Antes | Ahora | Dónde queda |
|---|---|---|---|
| Lo escrito por el residente | Transcript en «Complete encounter record» | En Indicaciones, como texto de cada orden; no en Evolución | `events` (`you`), Management Trace (`learner_input`) |
| Aclaraciones resueltas | En el transcript | En Indicaciones, con su orden | `events`, Trace (`clarification`) |
| Aclaración pendiente | En «Latest response» | Aviso fijo junto a la escritura mientras la orden espera, aunque se hagan otras cosas; en Indicaciones, «Status: clarification required» con la pregunta | `pending_action` / `pending_bundle`, Trace (`clarification_required`) |
| Cuatro campos completados | En el transcript | No se muestran | `events` (`reasoning_completion`), Trace (`reasoning`) |
| Mensajes del sistema (no ejecutado, límites, nota de contexto) | En el transcript | Junto a la escritura (última orden) y en Indicaciones (todas) | `events`, Trace |
| Panel vivo de auscultación y llene capilar | Visible sin examinar | No se dibuja: un hallazgo se ve cuando se obtuvo | El estado del motor; el examen y las reevaluaciones lo entregan |
| Después del cierre | «Latest response» abierto, grabaciones de ECG, soporte y plan del intento anterior sobre el registro clínico plegado | Igual; el registro clínico plegado contiene ahora las cuatro vistas; «Image issue details» sólo para docentes | Sin cambios |

## 6. Modo único y apertura directa del resultado

- **Un solo modo:** el mismo `st.radio` (mismas opciones, `index=3` = Treat, misma lógica), dibujado como
  cuatro botones; el elegido lleva fondo, borde, negrita y ✓; el radio expone `aria-checked`. Navegador: un
  único `input:checked` antes y después de consultar vistas, abrir un ECG y el menú.
- **«View ECG»:** abre exactamente la grabación de su aviso (prueba: dos ECG en minutos distintos; cada botón
  muestra el SVG idéntico a `render_ecg_svg` de su grabación) y no cambia estado, eventos, Trace, reloj ni
  modo.

## 7. Barra lateral: comportamiento real

Durante el encuentro (`started` y no cerrado) la barra lateral no se dibuja: no reserva espacio (`stMain`
ocupa el ancho completo en las tres resoluciones). «☰ Menu/Menú» es un `st.popover` fijo arriba a la
izquierda, sobre la sala: abre con clic y con teclado (Enter), cierra con Escape y con un clic fuera; abrirlo
no mueve la foto ni la consola (cajas idénticas medidas en el navegador), no envía, no cambia el modo, no
borra el borrador ni los cuatro campos, no avanza el reloj, no crea eventos ni entradas del Trace y no llama a
ningún modelo. Hover: DIFERIDO. Antes y después del encuentro, la barra lateral es la de siempre.

## 8. Equivalencia y permisos

- **Equivalencia** (`AppTest`, mismo caso `acs_61m_posterior`, misma semilla, 16 pasos: retención, cuatro
  campos con un faltante y completos, ECG, pregunta, examen, aclaración y respuesta, estudios, reevaluación,
  ECG de control, varias acciones, retención y cancelación, cierre): eventos, Management Trace (menos la
  versión del código), estado clínico, órdenes pendientes y el registro guardado en la base son **idénticos**
  entre `1766f4d` y la versión nueva.
- **Permisos:** residente sin «Image issue details», «Retry patient image» ni expanders «Developer»; docente con
  ellos. El idioma sigue fijo durante el encuentro. Ninguna llamada nueva a IA (sin clave en las pruebas; el
  código nuevo no importa ningún cliente).

## 9. Límites de la revisión visual y riesgos

- Capturas con Chromium sin cabeza, sin fuentes del sistema del usuario; Streamlit Community Cloud muestra
  otra barra de herramientas arriba a la derecha (la franja del reloj deja 15 rem libres para ella).
- La foto se recorta a lo ancho (`cover`) en ventanas estrechas: a 1000 px se ve ~45 % del ancho de la imagen,
  centrado; en las fotos revisadas se ven rostro, tórax y manos, pero una foto con algo clínico en un borde
  podría perderlo.
- Con los cuatro campos abiertos, la zona de escritura ocupa hasta 84 % de la columna y se desplaza dentro de
  sí; la información queda reducida a sus pestañas.
- La versión en español conserva etiquetas en inglés sin traducción aprobada (TD-61).
- En un teléfono (390×844) la sala se apila: el reloj y «ECG» en una fila propia bajo el menú, la foto con el
  monitor y, debajo, la consola; se revisó sólo la llegada (las tres resoluciones pedidas son de escritorio).
- ANTES, a 1366×768, la pregunta de cierre dejaba «Finish now» fuera de la vista (había que desplazarse dentro
  de la consola); DESPUÉS la zona de escritura se amplía y el botón queda a la vista (medido en el navegador).

## 10. Verificación

- **Equivalencia** (sección 8), repetida sobre el árbol final: idéntica a `1766f4d` en los 16 pasos y en el registro
  guardado, salvo la versión del código y las horas de reloj (`frozen_at`, identificadores de la base).
- **Navegador** (Chromium, 1366×768 y 1000×768): un solo modo marcado con ✓; Enter agrega una línea y no envía; el
  borrador y el modo se conservan al consultar las vistas, abrir un ECG y abrir el menú; «View ECG» abre el visor sin
  mover el reloj; el menú abre con clic y con teclado, cierra con Escape y con un clic fuera, no abre por hover y no
  mueve nada; el envío muestra el indicador de Streamlit y limpia el cuadro.
- **Pruebas:** `test_encounter_screen.py` (18); las **56/56 regresiones activas**; la **suite completa** en cuatro
  partes sobre el candidato final: 6.575 aprobadas, 83 omitidas, 1 xfail, **0 fallidas**.
- **Pruebas existentes adaptadas** (no cambia lo que protegen): «Submit» → «Send» en 22 pruebas y en las
  herramientas de ensayo; el ayudante compartido pulsa el botón en el idioma del encuentro («Enviar» en español); la
  prueba del ritmo que leía el panel de signos vivos ahora lee el monitor, que es donde la sala muestra los signos
  (sigue exigiendo que no nombre el ritmo, también en paro); el ensayo en navegador abre el menú para guardar y volver.
- **Revisión independiente del diff** (sólo lectura). Corregido: una orden completada en texto libre o por anulación
  docente perdía su resultado en las vistas (el registro adelanta su cuenta de eventos cuando la sala retira el aviso
  de orden retenida; las vistas ahora se anclan a la entrada del residente); los avisos de ECG y un error de guardado
  caían en la franja fija de una línea (ahora en la consola); el ensayo en navegador no encontraba «Save & return to
  dashboard» dentro del menú cerrado; una cancelación aparecía dos veces; mensajes sin orden dejaban de verse tras el
  siguiente intercambio; el indicador de Streamlit no respondía a clics; «terminal locked» se leía mal en español; y
  la franja adelantaba el minuto de un resultado de los motores de familia. Nada de esto cambiaba lo registrado.

## 11. Iteración 2 (2026-10-02): presentación, jerarquía y color

Sólo presentación: el motor, la evaluación, el Management Trace, la persistencia y los cuatro campos no cambian.
Se toma como referencia el mockup aprobado del encargo original.

- **Paciente centrado.** Las 133 fotos del banco (1536×1024) se recortan a lo ancho y el paciente no siempre está
  en el medio del cuadro: la cara cae entre el 33 % y el 54 % del ancho. Cada foto se encuadra ahora en su
  paciente: el centro horizontal de las zonas blancas (almohada, bata y sábana) bajo el techo, medido una vez por
  foto (`image_scene.framing_style`), y aplicado con CSS sin salirse de la imagen. Una foto que no se puede leer
  queda centrada como antes. No cambia qué foto se muestra, su revisión ni su registro.
- **Monitor.** Más ancho y legible (cifras de 19 a 36 px según la pantalla, trazado más alto), sobre la esquina
  superior izquierda de la foto. El «ECG» de cabecera está en el propio monitor. Cuando el monitor es angosto
  (1000 px, teléfono), las cifras pasan a dos filas en vez de superponerse.
- **Color por categoría** (`encounter_screen.CATEGORY`), que decide sólo cómo se ve una entrada y nunca si se
  muestra:
  - Talk y las respuestas del paciente, en azul;
  - Examine y el examen, en verde;
  - Tests y los resultados y estudios, en violeta;
  - Treat y lo que hizo el equipo, en coral;
  - la respuesta del paciente, en turquesa;
  - lo retenido o lo que espera una respuesta, en ámbar;
  - lo escrito por el residente, en gris pizarra.

  Los cuatro modos llevan su color y el elegido conserva ✓, borde y relleno.
- **Evolution** como línea de tiempo: cada entrada es una tarjeta con su minuto, su categoría y «View ECG» cuando
  corresponde. El texto de cada entrada es el mismo.
- **Escritura:** el cuadro tiene marco propio y «Send» es la acción principal, a su derecha. «Complete Encounter &
  Begin Review» sigue disponible, como botón secundario y separado.
- **Aviso de la fotografía:** franja fina al pie de la foto, con el mismo texto.

**Verificación:**
- equivalencia del registro con `ux-antes-despues` (perfil de 20 pasos con las cuatro vistas): idéntica a
  `890e733`;
- 6 comprobaciones de navegador;
- 56/56 regresiones activas;
- suite completa: 6.659 aprobadas, 83 omitidas, 1 xfail, 0 fallidas.

**Límites:**
- La foto que elige el banco depende del identificador del intento, distinto en cada base sintética, así que las
  capturas ANTES y DESPUÉS muestran pacientes distintos. El encuadre se comparó con las mismas fotos aparte.
- En teléfono el monitor sigue sobre la foto y, en algunos encuadres, tapa parte de la cabeza, como antes.

## 12. Monitor arriba, paciente debajo: cierre (2026-10-03)

Sólo presentación. No cambian el motor, el lector, el reloj clínico, la evaluación, el Management Trace, la
persistencia, los cuatro campos ni la columna derecha. `39f9558` puso el monitor arriba, a todo el ancho de la
columna, y al paciente en un bloque propio debajo. Esta sección cierra lo que esa entrega dejó pendiente.

**Limitaciones de partida (`39f9558`).**
- El trazado de cabecera era una ventana fija de 4 s (`viewBox` 600×132, 4,5:1). Con escala uniforme, en un monitor
  ancho ocupaba sólo una parte de la banda: a 1366×768, 421 de 629 px.
- En teléfono, la franja superior de 36vh dejaba el trazado en 186×41 px y la foto en 377×173 px. La consola se
  desplazaba por dentro.
- El aviso de la fotografía iba sobre el pie de la imagen y tapaba entre 29 y 46 px de la foto.
- En un marco con la proporción de la foto, el encuadre de §11 no podía mover al paciente. Recortar sólo cambia qué
  parte de la foto se ve, y ahí no sobra ancho. A 1366×768 el paciente quedaba entre 0,33 y 0,54 del ancho. Así se
  veía en la app de desarrollo.
- Lo anotado en §11 sobre el monitor que tapaba la cabeza en teléfono ya lo resolvió `39f9558`. Aquí se confirma en
  los cuatro tamaños.

**Solución.**
- **Trazado** (`ecg12.monitor_wave_svg`, `MONITOR_VIEW`):
  - la ventana mide 792×132 (6:1) y muestra unos 5,3 s de la misma señal (`_signals`);
  - conserva la velocidad de papel (145 u/s) y la ganancia (42 u/mV);
  - los primeros 4 s coinciden punto por punto con el trazado anterior;
  - lo que sigue lo da el mismo reloj de latidos del modelo: no se duplican segmentos ni se inventan latidos;
  - el barrido cruza la ventana en su propia duración;
  - sin escalado no uniforme. El ECG de 12 derivaciones no cambia.
- **Escritorio** (`clinical_scene.BEDSPACE_CSS`): el SVG toma su alto de su ancho y llena la banda. El alto del
  monitor se reserva a partir del ancho de la columna (`--mon-h`), y la foto empieza debajo.
- **Teléfono:**
  - una sola columna con desplazamiento vertical normal: monitor → paciente (4:3) → aviso → consola;
  - sin desplazamiento horizontal;
  - los botones propios de Streamlit (⋮, y «Deploy» en local) llevan fondo propio. El encabezado es transparente
    (`encounter_screen.MENU_CSS`), y ahora la página se desplaza bajo él: sin ese fondo, los botones quedaban sobre
    el texto o la foto.
- **Aviso:** el mismo texto aprobado, como pie bajo la foto. Queda fuera de la imagen, completo y sin truncar.
- **Paciente centrado** (`image_scene.framing_style`):
  - además del centro medido, la sala puede agrandar la foto lo justo para centrar al paciente (`--fz`), nunca más
    de ×1,25;
  - el ancla vertical sigue en el 30 % de la imagen: se recorta algo de pared y sábana, no la cabeza;
  - una foto que no se puede leer queda como antes;
  - no cambian qué foto se muestra, su revisión ni su registro.

**Medidas en navegador** (sala real, datos sintéticos, Chromium sin red; antes `39f9558` → después):

| Tamaño | Trazado dibujado (px; % del ancho de la banda) | Segundos | Foto visible, sin el aviso encima (px) | Aviso | Página |
|---|---|---|---|---|---|
| 1440×900 | 450×99 (68 %) → 666×111 (100 %) | 4 → 5,3 | 696×575 → 696×554 | sobre la foto (29 px) → debajo | sin desplazamiento |
| 1366×768 | 421×93 (67 %) → 629×105 (100 %) | 4 → 5,3 | 659×435 → 659×430 | sobre la foto (46 px) → debajo | sin desplazamiento |
| 1000×768 | 446×98 (100 %) → 446×74 (100 %) | 4 → 5,3 | 476×435 → 476×471 | sobre la foto (46 px) → debajo | sin desplazamiento |
| 390×844 | 186×41 (52 %) → 357×60 (100 %) | 4 → 5,3 | 377×136 → 377×283 | sobre la foto (37 px) → debajo | consola con desplazamiento propio → página de 1.344 px; sin desplazamiento horizontal |

Comprobado en los cuatro tamaños:
- la escala es uniforme (la misma en x y en y) en el trazado y en su rótulo «II»;
- el botón ECG queda dentro del monitor;
- el cuadro y «Send» se alcanzan, también en teléfono con 480 px de alto (teclado virtual simulado);
- ni la app ni la página hicieron solicitudes externas:
  - los servidores tienen la red bloqueada en el proceso: 0 intentos;
  - la página: 0 solicitudes;
  - Chromium intentó por su cuenta conectar con servicios de Google (cuentas, hora, DNS), y el proxy del entorno
    rechazó esas conexiones.

**Centrado del paciente.** Cálculo con la fórmula del CSS sobre los centros medidos de las 133 fotos del banco.
La posición va de 0 (borde izquierdo) a 1; 0,5 es el centro. Las capturas lo muestran en el navegador con las fotos
que eligieron las bases sintéticas.

| Marco | Sin el aumento | Con el aumento | Exactamente al centro | Recorte máximo arriba / abajo |
|---|---|---|---|---|
| 1440×900 | 0,39–0,50 | 0,41–0,50 | 103/133 | 1 % / 3 % |
| 1366×768 | 0,33–0,54 | 0,41–0,50 | 103/133 | 7 % / 15 % |
| 1000×768 | 0,49–0,50 | 0,49–0,50 | 131/133 | 0 % / 0 % |
| 390×844 | 0,37–0,50 | 0,41–0,50 | 103/133 | 3 % / 7 % |

**Capturas** (fuera del repositorio, entregadas con el informe):
- EN y ES a 1440×900, 1366×768, 1000×768 y 390×844;
- estados: llegada, cuatro campos pendientes y completos, ECG abierto y encuentro largo;
- vista neutral sin imagen aprobada en los cuatro tamaños.

**Versión verificada.** El árbol de trabajo sobre `39f9558`, con el código de la app de este commit. Después sólo
cambió este documento.
- **Pruebas focalizadas** (29 archivos que usan la escena, el monitor o el ECG): 596 aprobadas, 1 omitida,
  209 subpruebas.
- **Equivalencia del registro con `39f9558`** (perfil de 20 pasos con la orden retenida, los cuatro campos, el ECG y
  las cuatro vistas): idéntica.
  - Sólo se normalizan el commit registrado (`code_version`) y la hora en que se congela la base de la evaluación.
  - Los 19 «hechos visibles nuevos» son todos la duración del barrido en el estilo del SVG («5.324s»). Se revisaron
    a mano: no son hechos clínicos.
- **Capturas y medidas** de arriba.
- **Comportamiento:** 6 de 6 comprobaciones a 1366×768 y a 390×844.
  - En teléfono, «abrir el menú no mueve nada» fallaba en falso. Con la página desplazada hasta abajo, Playwright
    la subía 500 px para alcanzar el botón, y la comprobación medía posiciones en pantalla.
  - `comportamiento.py` ahora trae el botón a la vista antes de medir.
- **Ventana y vistas:** cambiar el tamaño de la ventana y recorrer las vistas no agrega eventos ni avanza el
  reloj.

La suite completa y las 56/56 regresiones activas corrieron sobre el candidato anterior (árbol de trabajo con huella
`2b4970b38cee`), con el renderizador del trazado ya cambiado. La suite dio 6.661 aprobadas, 83 omitidas, 1 xfail y
0 fallidas. Después cambiaron sólo dos cosas en la app, ambas cubiertas por las pruebas focalizadas:
- `image_scene.framing_style` y dos reglas de CSS, para centrar al paciente;
- una regla de CSS para teléfono: el fondo de los botones de Streamlit.

**Límites.**
- **1000×768:** el trazado ocupa todo el ancho, como antes, pero muestra 5,3 s en vez de 4 s. Su alto baja de 98 a
  74 px (escala 0,74 → 0,56). Sigue legible en las capturas. Una ventana más corta para monitores angostos daría
  más alto; no está implementada.
- **Fibrilación auricular:** el modelo usa un ciclo de 16 latidos. Desde unos 181/min, ese ciclo cabe en la ventana
  de 5,3 s y puede verse repetido; con 4 s pasaba desde 240/min. Es propiedad del modelo, no de la ventana.
- **Barra lateral abierta:** la reserva del monitor se calcula con el ancho de la ventana del navegador. Con la
  barra abierta, la columna real es más angosta y sólo crece el espacio entre monitor y foto, sin superposición.
  Durante el encuentro, la barra está cerrada por defecto.
- **Aumento:** en un marco ancho (1366×768) puede recortar hasta 15 % de la sábana abajo y 7 % arriba.
- **Teléfono:**
  - «☰ Menu» queda arriba de la página y se va con el desplazamiento: para abrirlo hay que volver arriba;
  - el teclado virtual se simuló con 480 px de alto en Chromium sin interfaz; no se probó en un teléfono real.
- **Capturas:** cada base sintética elige su foto, así que EN y ES muestran pacientes distintos.
- **App de desarrollo:** no se comprueba desde este entorno, cuyo proxy no deja pasar el WebSocket de Streamlit.
  Ver el informe de entrega.

## 13. La línea de versión, fuera de la sala (2026-10-05)

**Observado en la app de desarrollo** (video del 2026-10-05, con el código de §12): cada ~2 s la sala se pone gris
durante unos 0,9 s. Mientras tanto, a través del monitor se lee «Management Reasoning Simulator · Clinical encounter
v0.24.13».

**Causa.**
- La sala es un fragmento que se refresca solo cada 2 s (`resuscitation_room.render_room`,
  `@st.fragment(run_every=2)`, desde el 2026-09-21), para mostrar una foto apenas esté lista.
- Mientras corre, Streamlit atenúa la sala. En Streamlit Cloud cada refresco tarda lo bastante para que se vea.
- En local es tan breve que la sala no se atenúa: la opacidad del monitor fue 1 en 160 muestras durante 8 s.
- La línea de versión se dibuja arriba de la página, debajo del monitor, y se transparentaba con la sala atenuada.
  Lo mismo pasa al enviar una acción, mientras la página corre.

**Cambio.** `app.py` ya no dibuja la línea de versión durante el encuentro; antes y después del encuentro sigue
igual. Prueba nueva: `test_the_version_line_stays_out_of_the_room`.

**Verificación.**
- 606 pruebas aprobadas y 1 omitida, en los 29 archivos de la sala, `test_generation_progress.py` y
  `test_problem_launch.py`.
- La prueba nueva falla sin el cambio.
- En navegador local, la línea está en la página de inicio y no en la sala. 0 solicitudes externas.

**Sigue pendiente.**
- El gris periódico de la sala en Streamlit Cloud: lo causa el refresco de 2 s, no la línea.
- Para cuentas docentes, la línea sobre la interpretación del lenguaje («… language interpretation is active.»)
  sigue debajo del monitor y se transparentaría igual.
