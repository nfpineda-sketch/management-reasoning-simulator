# Guía docente · piloto formativo

Para quien revisa encuentros durante el piloto. El detalle técnico está en
`docs/revision/PILOT_PROMOTION_DEPLOYMENT_RUNBOOK.md` (que reemplaza a `docs/RUNBOOK_PILOTO.md` para el piloto) y
en `docs/READINESS_PILOTO_FORMATIVO.md`.

> **Estado (2026-10-08): actualizada al candidato final local de B-5 (IG-6, con ES-P1 a ES-P13 decididos e
> implementados), para su firma (H-62); no está firmada.** El SHA exacto del candidato queda en el informe de su
> certificación.
> Describe el funcionamiento comprobado al cierre del paquete prepiloto (D-1 a D-11), lo que cambió la Fase 0
> (F0-1 a F0-12) y lo implementado en local el 2026-10-08 con las decisiones docentes de B-5 («El candidato de
> B-5»), todavía no desplegado, con las etiquetas de la pantalla en español y, entre paréntesis, en inglés. Lo
> implementado vale sólo para encuentros nuevos: uno anterior conserva su registro y la declaración con que se
> congeló.
>
> Firma y fecha: ________________________

## Lo esencial

- **Cada juicio es del docente.** La IA no asigna ni propone nada durante el piloto: durante el encuentro
  está apagada, y después del encuentro no está autorizada. No hay nota global, ranking ni tabla de
  posiciones.
- **El residente ve el foco de aprendizaje después de su revisión**, no al cerrar el encuentro. Usted lo
  ve durante la revisión.
- **Casos:** 30 de los 31 del banco, asignados por desafío y año de formación. `trauma_hemothorax_41m` queda
  fuera del piloto de residentes (F0-2): el pabellón no está modelado y, tras el drenaje, el paciente hace un
  paro hacia el minuto 60 haga lo que haga; sigue en el sandbox docente y no se ofrece al dirigir un caso. Las
  composiciones de hipoglicemia, los casos escritos por IA y PS001/PS002 no se usan, y R1-03, R1-04 y R2-01
  no se asignan (F0-4).
- **Idioma (X-1):** el piloto corre en inglés y en español. El residente elige el idioma antes de empezar y
  queda fijo durante el encuentro. En un encuentro en español la sala habla en español (X-1, 105 decisiones):
  el relato aprobado de los 30 casos, el examen, las preguntas sobre una orden, la compuerta de razonamiento,
  los recibos (F0-11), los rótulos, el monitor, el ECG, los tratamientos en curso y las pantallas del cierre.
  Los fármacos se nombran en español (V-9), también en los documentos que se descargan en español; dosis,
  unidades, vías y siglas se escriben igual. El registro, el Management Trace y el ledger se guardan en inglés;
  sus destinos y códigos (EXECUTED, UNRECOGNIZED, HELD_REASONING…) y los nombres canónicos de los fármacos no se
  traducen. La rúbrica en español (D1 a D5) es la que usted aprobó. Lo único que se ve en inglés en la sala de
  un encuentro en español es lo que escribió el residente, tal como lo escribió (véase «Limitaciones conocidas»).

## Revisar un encuentro

1. **Abra el encuentro completado** desde el panel docente: «Actividad del residente y evidencia
   registrada» («Resident activity and recorded evidence»).
2. **Lea el registro:** qué escribió el residente, cómo se leyó cada orden, qué se ejecutó y qué pasó
   con el paciente.
3. **Lea los límites del simulador en ese caso:** «Lo que el simulador no puede mostrar ni tratar en este
   caso». Están en la rúbrica y en los objetivos. Nunca los cuente contra el residente: lo que el simulador
   no puede mostrar no es evidencia, y una medida escrita para ello no es una omisión.
4. **Puntúe la rúbrica:** «Rúbrica de razonamiento de manejo - piloto 1.0» («Management reasoning rubric -
   pilot 1.0»), de 0 a 3 por dominio («Tu puntaje»), o «No evaluable» si el encuentro no dio la
   oportunidad, con su motivo. Confírmela con «Confirmar evaluación»; «Guardar borrador» no cuenta.
5. **Decida cada evento crítico** definido para el caso («Eventos críticos definidos para este caso»):
   «Confirmado - aplica la penalización» (−3, que queda visible) o «Aún sin decidir». En el piloto la IA no
   propone eventos, así que confirmar uno pide su motivo: «Por qué (la IA no propuso este)». La pantalla
   muestra lo que el registro establece de cada evento; la decisión es suya.
6. **Registre observaciones por objetivo**, cuando correspondan: «Evaluar objetivos observados», con su
   evidencia, profundidad y autonomía, y «Registrar evaluación del objetivo». Una orden reconocida o un buen
   desenlace no dan crédito solos. Si lo único que faltaría es algo que el simulador no muestra, no registre
   «Requiere mejorar»: esa parte no es evaluable.
7. **Para corregir un registro,** anule la evaluación con un motivo: «Anular evaluación» («Void
   assessment»). El original y el motivo quedan en el historial.

## Elegir el próximo caso de un residente

- **Requisito:** un administrador debe autorizarlo para ese residente: «Quién puede elegir los casos de un
  residente» («Who may choose a resident's cases»).
- **Cómo:** en «Dirigir el próximo encuentro de un residente» («Direct a resident's next encounter») elige
  el desafío y el caso, siempre con un motivo.
- **El residente no lo sabe:** ni que el caso fue elegido, ni cuál es, ni por qué.

## Lo decidido y comprobado

**Trombólisis en el TEP (P-04, P-05, P-06, D-4).**

- La lisis actúa sobre el trombo esté o no indicada, y su riesgo de sangrado es el que ya declaraba el
  caso. Toda dosis produce además una pérdida pequeña de hemoglobina, visible sólo en el laboratorio
  (decisión del 2026-09-20). La sala no promete mejoría: lo que cambia se ve al reevaluar.
- La indicación se juzga con el estado del minuto en que se dio: una mejoría posterior no la vuelve
  correcta.
- **Criterio (D-4), el mismo del motor:**
  - **Shock obstructivo:** sistólica bajo 90 mmHg, o un vasopresor necesario para llegar a 90, con signos de
    hipoperfusión. Indica la trombólisis desde que está presente: no hay que esperar 15 minutos.
  - **Hipotensión sostenida:** sin esos signos, sistólica bajo 90 mmHg, o un vasopresor necesario para
    mantenerla en 90 o más, durante 15 minutos consecutivos.
  - Un vasopresor que la presión no necesita no es ninguno de los dos.
- El resto de un esquema de alteplasa completa la primera dosis. Cualquier otra dosis posterior es un
  **segundo curso**: queda registrado con su exposición adicional, y el simulador no le da reperfusión ni
  sangrado propios. Es una simplificación, no evidencia de que repetir no tenga efecto.

**Anafilaxia.**

- **El examen dice el estridor que el motor tiene ahora (TD-50).** Cuando la reacción baja, la 29f dice
  «…; no stridor heard now.»; mientras la reacción sigue, el estridor sigue, aunque el oxígeno normalice la
  saturación. Con el tubo endotraqueal no se ausculta estridor (TD-47) y la anafilaxia sigue su curso.
- La 63m no tiene compromiso de la vía aérea alta: no tiene estridor ni se le cobra.
- **`anaphylaxis_29f`, C3 (R-3):** es una oportunidad **parcial**. Confirme C3 sólo si aparece la
  anticipación de la vía aérea (nombrar la amenaza, pedir ayuda capaz de manejarla o prepararla, reevaluar
  el estridor). Nunca por la adrenalina y el oxígeno solos. La ejecución no se observa: intubar siempre
  resulta.

**Trauma.**

- **El E-FAST muestra sus cinco ventanas (TD-48)** en la sala, el Management Trace y los documentos. Una
  ventana que el caso no documenta dice «Not documented»; nunca se completa con un hallazgo inventado. En la
  41m (sólo en el sandbox docente, F0-2) se ve el líquido en el receso pleural izquierdo.
- **La herida del muslo de la 27m** se describe como el caso la escribió mientras no se aplica nada; después,
  el examen dice si el sangrado externo está disminuido o detenido.

**«General appearance» (TD-59).** Bajo el resumen del motor (estado mental, expresión, color, sudoración),
el examen dice lo que el caso escribió y sigue siendo cierto: la fístula de diálisis, la marca del cinturón,
la picadura, las negativas que el caso escribe.

**Criterios C14 (R-2, D-7, D-8).** La tabla de criterios R-2 quedó aceptada el 2026-10-02; la firma de cada
ficha final sigue pendiente.

- `acs_61m_posterior`: no se exige reconocer la hipocinesia posterior sutil, que el informe entrega. Una
  aorta no dilatada en el POCUS no descarta una disección.
- `acs_52m_de_winter`: se usa la motilidad que entrega el informe, no se exige reconocerla, y el POCUS nunca
  demora la reperfusión: activarla sólo por el ECG es correcto y no es un déficit de C14.
- `acs_70f_left_main`: un bolo pequeño, justificado y reevaluado no se penaliza por sí solo. En este
  simulador el exceso de volumen se ve sólo en una presión que deja de responder y en un mensaje de la sala;
  el pulmón, el examen, la saturación y un POCUS de control no cambian. Evalúe con esas señales: no exija
  detectar sobrecarga por examen ni por POCUS, y si la única respuesta que buscó el residente es una que el
  simulador no muestra, esa parte no es evaluable.

**`pulmonary_embolism_33f`, alcance de la evaluación (D-3).** Tras un trombolítico, el sangrado del sitio
operado no se detiene en este simulador: la hemoglobina sigue bajando mientras la presión puede tranquilizar.
La sala no puede suspender una infusión de alteplasa; el ácido tranexámico y el crioprecipitado se registran
sin efecto modelado, y el concentrado de fibrinógeno no se reconoce. Esa respuesta no se evalúa y nunca juzga
el rescate hemorrágico: no revertirla nunca se cobra, y una medida bien indicada escrita para ella nunca es
una omisión. La decisión de trombolizar se juzga como antes, en su minuto.

**Otras.**

- **`pulmonary_edema_75f` (P-07):** llega con la vista neutral hasta que una imagen aprobada muestre su
  dificultad respiratoria.
- **Terminología (R-4):** «aumento de volumen», «dolor a la palpación» y «suero glucosado». Las 18 frases
  finales del motor esperan su firma (`docs/revision/CIERRE_PREPILOTO.md`, ordenadas en
  `docs/revision/FACULTY_SIGNOFF_PACKET_PREPILOT.md`).

## La pantalla del encuentro (2026-10-02)

- **Qué ve el residente:** el paciente a la izquierda; a la derecha, «Tiempo simulado», las vistas «Evolución»,
  «Historia y examen», «Resultados» e «Indicaciones», y abajo el lugar para escribir. La barra lateral no se
  dibuja durante el encuentro: la cuenta, la contraseña y el idioma están en «☰ Menú».
- **El cambio de pantalla no cambió nada de lo que se registra:** las mismas entradas producían la misma
  interpretación, ejecución, tiempo, estado y registro (comprobado antes/después, 2026-10-02). La Fase 0,
  después, sí cambió la ejecución y el tiempo: ver «La sala desde la Fase 0». Evolución no repite lo que el
  residente escribió ni los mensajes sobre una orden; todo sigue en el registro y en el Management Trace.
- **Lo que ya no se muestra al residente:** el panel vivo que leía la auscultación y el llene capilar del
  momento sin examinar (un hallazgo se ve cuando se obtuvo, con su minuto) y los controles de desarrollo de la
  imagen («Image issue details», «Retry patient image»), que quedan para docentes y administradores.

## Fotos y POCUS: qué muestran y qué no

- **Fotos.** Sólo se muestran fotos con sus dos revisiones humanas aprobadas. Una foto fija no muestra todos
  los signos: la sala lo recuerda junto a la foto, en el idioma del encuentro («Una fotografía fija no muestra
  todos los signos clínicos; examina al paciente para evaluar lo que no puede mostrar.»; J-64). Lo que la foto no
  muestra está en el examen. `bradycardia_bb_54f` y `pulmonary_edema_75f` llegan con la vista neutral.
- **POCUS y E-FAST.** Son informes escritos de hallazgos: no hay imágenes ni videos. Lo que se observa es la
  indicación (pedirlo y cuándo), la interpretación de los hallazgos entregados por escrito, su uso en el
  manejo y la reevaluación. **No** se observa la adquisición, la destreza psicomotora ni el reconocimiento
  de imágenes: no se los atribuya al residente.
- **POCUS y E-FAST de control (TD-54).** Un POCUS repetido no cambia la VCI con el volumen o el control de la
  hemorragia en el trauma; un E-FAST de control repite las ventanas de llegada (en la 41m, sólo en el sandbox
  docente, también el receso drenado). No exija ver un cambio que el simulador no muestra.
- **POCUS de control en la neumonía (D-42; `pneumonia_46f` y `pneumonia_83m`).** Un POCUS de control muestra que la
  VCI se llena con el volumen, pero en los pulmones no muestra líneas B nuevas por la sobrecarga de cristaloides; la
  saturación sí cae. No se exige ver líneas B nuevas.

## La sala desde la Fase 0 (2026-10-06)

Lo que cambió la Fase 0 y cómo leerlo al evaluar. Vale para encuentros nuevos.

- **Cada orden tiene un destino y un recibo.** El registro y el Management Trace guardan qué pasó con cada
  orden escrita (por ejemplo EXECUTED, HELD_CLARIFICATION, HELD_REASONING, RECORDED_NOT_MODELLED,
  UNRECOGNIZED o TERMINAL_NOT_EXECUTABLE), con el minuto en que se escribió, y la sala se lo dijo al residente.
  En un envío con varias órdenes, las independientes corren y el recibo dice qué corrió y qué no.
- **Tiempo (F0-5).** «Esperar u observar N minutos» (también en español) avanza el reloj N minutos.
  «Reevaluar» sin número es una mirada a la cabecera de 2 minutos; «dar X y reevaluar» es X más esa mirada, y
  la sala dice si X tuvo tiempo de actuar. Una orden para más tarde («en 30 minutos») no se ejecuta ni se
  programa: queda registrada y la sala lo dice. Un volumen «en 20 minutos» es un ritmo. Un paso del reloj
  llega a 120 minutos como máximo.
- **Interrupciones (F0-6).** Un evento del motor detiene la espera en su minuto: bloqueo AV, fibrilación o
  ectopia ventricular, paro, reacción bifásica, sangrado mayor tras la lisis, neumotórax a tensión, falla del
  VD por volumen, hipotensión sostenida de la obstrucción, convulsiones o la vuelta tras el alta. También la
  detienen dos cambios vigilados: una sistólica bajo 70 mmHg que cayó 20 o más, o una SpO₂ bajo 85 % que cayó
  5 puntos o más, durante 2 minutos seguidos. La causa de esos dos es desconocida y nunca se usa sola en
  contra del residente.
- **Paro (F0-8).** En la anafilaxia, la hemorragia y la bradicardia el paro es verdadero: sin pulso ni
  presión, con el mensaje acordado («Cardiac arrest occurred at minute X. Resuscitation management is not
  modelled in this pilot. Subsequent management is not assessable.»). Ninguna orden posterior se ejecuta y nada
  posterior es evaluable.
- **Compuerta de razonamiento.** Una orden de manejo sin modelo de trabajo, efecto esperado o qué revisar
  queda retenida con todo su envío (HELD_REASONING) hasta que el residente la complete, con sus palabras o con
  las preguntas guiadas. La prioridad y el momento de reevaluar se registran, pero no retienen la orden. Una
  intervención urgente (bolsa y mascarilla, descompresión del tórax, control de una hemorragia, cinturón
  pélvico) nunca se retiene, y el residente puede explicarla después, como retrospectiva.
- **Guardas del registro (A–E).** Antes de toda propuesta o lectura del registro: una orden escrita que el
  simulador no ejecutó (retenida, no entendida, registrada sin modelo, para más tarde, tras un paro) nunca es
  una omisión (A); una demora del simulador cuenta desde que el residente escribió, y la de la compuerta de
  razonamiento es de la compuerta, nunca del residente (B, F0-10); no se exige reconocer lo que no estaba
  disponible o lo contradecía (C); un evento con guion, una limitación del motor, un evento de causa
  desconocida o uno precedido por una orden no ejecutada nunca sostiene una retroalimentación negativa (D,
  F0-7); nada después de un paro no modelado es evaluable (E). Un «met» que el registro no puede resolver pasa
  a «reading», con su motivo: decide usted.
- **Respuesta a una aclaración (F0-12).** La respuesta completa sólo la orden retenida. Otra orden escrita en
  la misma respuesta se lee a continuación como orden propia, con su compuerta, sus preguntas, su destino y su
  recibo, y con el minuto en que se escribió. Si la respuesta deja algo retenido, esa otra orden no corre y su
  recibo lo dice (TD-70).
- **Envío.** Un doble clic o una recarga no repiten una orden. Una ejecución detenida se deshace y corre una
  vez más; si se detiene dos veces, queda marcada como interrumpida, la sala lo dice y no se repite.
- **Oxígeno (F0-9).** Una mascarilla con reservorio sin flujo escrito usa 15 L/min, y la sala lo dice.
- **Idioma (F0-11).** En un encuentro en español, las frases nuevas de la Fase 0 se dicen enteras en español;
  el registro las guarda en inglés.
- **Casos y límites por caso.** El piloto usa 30 casos (F0-2). El manifiesto de congelamiento
  (`docs/revision/PILOT_FREEZE_MANIFEST.md`) declara las limitaciones de cada caso; por ejemplo,
  C-LIMB-ARREST-13: sin tratamiento, la 27m llega al paro hacia el minuto 13.

## El candidato de B-5 (implementado en local el 2026-10-08)

Lo que las decisiones docentes de B-5 cambiaron en la sala. Vale para encuentros nuevos.

- **Relato (30 de 30) y rúbrica (5 de 5) en español,** cada uno atado al hash que usted aprobó; en la rúbrica, D4
  con «revisar/vigilar» (R-1) y D5 con la opción b. Estructura, niveles, puntaje y la rúbrica inglesa no cambian.
- **El examen dice el estado del motor.**
  - Edema pulmonar agotado (A-2): «Crépitos inspiratorios bilaterales; el esfuerzo respiratorio ahora es
    superficial e ineficaz, compatible con agotamiento.»
  - `asthma_49m` (A-6, A-6a, A-6b, A-7-49m, A-8a): conserva el examen grave de llegada mientras su obstrucción no
    mejora, respirando solo o con VMNI; intubado sin mejoría, «Tubo endotraqueal instalado: el murmullo pulmonar
    sigue muy disminuido…»; el neumotórax y la descompresión tienen sus frases propias. La elección es por el
    estado de cada examen, no por la orden ni por el fármaco de inducción. La 24f no cambia.
  - Opioides (A-9 a A-11): con ventilación asistida, «Frecuencia respiratoria {n}/min, dada por la ventilación
    asistida en curso.»
  - Opioides (TD-84): el examen inglés dice «Pupils are small and reactive.», como ya lo decía el español.
- **Paros y eventos.** Paro de la anafilaxia después de una dosis (K-18): «…la adrenalina administrada antes no
  logró mantener la reacción bajo control…»; etiqueta del paro (K-E5): «paro circulatorio por anafilaxia sin
  adrenalina eficaz»; bradicardia (K-E6 y TD-85): «paro circulatorio por bradicardia profunda» y, en la sala en
  español, «Paro circulatorio por bradicardia profunda.»; reacción bifásica (TD-85): «La reacción anafiláctica
  vuelve.»; saturación (K-E16): «saturación de 84 % y en descenso». Disparadores, minutos, prevenibilidad y
  fisiología no cambian.
- **Vía oral (XR-18):** con el paciente que no puede tragar, la pregunta termina «…hasta que sea seguro
  administrar por vía oral.» (en inglés, «…until oral administration is safe.»). La lógica de la vía no cambia.
- **Preguntas sobre una orden (X-1):** nombran el fármaco que el residente escribió o, si sólo se reconoció una
  clase, su nombre («betabloqueador»), nunca una clave interna.

## Limitaciones conocidas

Son para el docente; **no se le dicen al residente como instrucciones**.

- **Lector de órdenes:** tiene brechas registradas (TD-45; `validation/KNOWN_DEFECTS_V3.md`).
  - Desde la Fase 0, toda orden termina con un destino y un recibo. Un fármaco o un examen nombrado sin
    verbo ni dosis («- Aspirin» en una lista, «Cefepime now»), o que ningún vocabulario conoce («Zyvox IV»),
    queda como orden no entendida (UNRECOGNIZED) y la sala lo dice: «No se entendió: «…». No se administró ni
    se hizo nada por ello.»
  - Quedan formas sin recibo (TD-69). Guardadas en silencio, sin que la regla A lea una omisión: un nombre
    tras «with/con» que sigue a un nombre conocido («Give ceftriaxone with zyvox»); un nombre escrito solo,
    como verbo o participio («Suctioning.», «Lavado.»); una etiqueta con dos puntos («Sepsis: zyvox.»), una
    condición sin verbo («If hypotensive, zyvox.»), un número sin unidad («Zyvox 600») o un nombre unido a la
    nota con «y». Sin guarda propia: una orden de una sola palabra del vocabulario de notas («Vitals.»,
    «Airway.»), un nombre justo después de otro conocido sin «with/con» («Give ceftriaxone zyvox») o uno que
    una acción absorbe («Reassess BP and zyvox in 10 minutes»). El registro guarda el texto entero del turno:
    léalo.
  - Un fluido nombrado sin verbo («IV fluids 1 L») queda retenido.
  - Si una orden no se ejecutó, el registro lo muestra: evalúe el razonamiento, no el lector.
- **Transfusión (TD-32):** una unidad corre 30 minutos y el reloj avanza hasta que termina, salvo que el
  residente escriba una velocidad o un momento de reevaluación.
- **«Suero glucosado» sin concentración:** sigue sin decidir.
- **Edema pulmonar sin tratamiento (TD-51, resuelta por A-2):** cuando el esfuerzo del motor es «Exhausted», el
  examen lo dice: «Crépitos inspiratorios bilaterales; el esfuerzo respiratorio ahora es superficial e ineficaz,
  compatible con agotamiento.» (en inglés, «…consistent with exhaustion.»). Ya no hay minutos en que el examen diga
  un esfuerzo aumentado mientras el paciente está agotado.
- **Hallazgos sin evolución en el motor (TD-59):** la urticaria, el enrojecimiento y el edema de labios y
  párpados de la 29f, el enrojecimiento y los habones de la 63m, el enrojecimiento y los escalofríos de la
  58f y la inquietud de la 34m no se vuelven a describir después de la llegada (su presentación los dice).
  No exija reevaluarlos.
- **Relato y sala en español:** el relato en español de los 30 casos del piloto es el que usted aprobó, en su
  versión exacta (`case_text/es/approvals.json`); el caso del sandbox docente (`trauma_hemothorax_41m`) sigue en
  inglés. Las frases del motor de R-4, el aviso de la foto y las preguntas de la sala se dicen en español, y
  también, desde el 2026-10-08, los textos que usted decidió fuera del inventario de X-1 (ES-P1 a ES-P13;
  `docs/revision/B5_IG5_PENDIENTES_DOCENTES.md`): la ayuda del selector de idioma, «Preguntar por: {tema}», «Última
  respuesta», «Ficha clínica · examen · resultados · registro de tratamientos», las frases de gastroenterología
  (con la hemoglobina, con la presión sistólica o con ambas), «unidades» (nunca «UI»), «Control de la hemorragia»
  y «Glóbulos rojos», las 15 aclaraciones del lector sobre lo que no está activo, la base de la dosis del ácido
  tranexámico sin dosis escrita, las dos frases de la fibrilación ventricular y la última línea de una orden
  retenida. Lo que escribió el residente se muestra tal como lo escribió, también dentro de esas frases (por
  ejemplo, la lista de «También se reconoció lo siguiente, pero no puede ejecutarse en esta versión: …»). La
  etiqueta canónica «endoscopy performed» queda en inglés en el registro y en el tamizaje: no se muestra en la
  sala (ES-P11).
- **TEP:** un segundo curso de trombolítico no tiene efecto propio en el simulador (simplificación
  declarada).

## Si algo no calza

Anote el encuentro y la hora, y avise al responsable del piloto. Lo pendiente de su firma está en
`docs/revision/CIERRE_PREPILOTO.md` y `docs/revision/F0_11_FRASES_ES.md`, ordenado en
`docs/revision/FACULTY_SIGNOFF_PACKET_PREPILOT.md`.
