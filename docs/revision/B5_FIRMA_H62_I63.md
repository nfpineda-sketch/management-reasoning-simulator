# B-5 · H-62 e I-63: paquete para la firma docente (2026-10-08)

> **Para revisión final y firma; no está firmado.** No es otra pasada de rediseño: las guías no se reescribieron
> para este paquete. Muestra el contenido final de cada guía en el candidato local congelado, todo lo que cambió
> desde la última versión que la docencia revisó y lo que depende del candidato. La firma la pone la docencia en
> la línea «Firma y fecha» de cada guía; nadie firma en su nombre.

| Dato | Valor |
|---|---|
| Candidato local congelado | `37c9afb1094327dd498857aa97a91820ddb4fe4c` (rama `clinical-encounter-v0.13`, sin push) |
| Última versión revisada por la docencia | `f59b953` (2026-10-07): sobre ella la docencia decidió «DEFER de la firma» hasta el candidato final (`docs/revision/FACULTY_SIGNOFF_PACKET_PREPILOT.md`, H-62 e I-63) |
| Commits que cambiaron las guías desde entonces | `ba94fc9` (IG-6: guías al candidato) y `2dc09e4` (ES-P1 a ES-P13); `37c9afb` no las cambió |

## 1. H-62 · `docs/GUIA_DOCENTE_PILOTO.md`

**Título y versión.** «Guía docente · piloto formativo». Estado en el archivo: «actualizada al candidato final
local de B-5 (IG-6, con ES-P1 a ES-P13 decididos e implementados), para su firma (H-62); no está firmada».

**Archivo final.** 297 líneas · sha256 `6327a2134913f32d660139a59cac13760b68a299c5c7cd803f363e350a454c33` · blob git `9895037c9bc1faa1b8a955660236715f25e4a1e0`.

**Secciones (todas sustantivas):** Lo esencial · Revisar un encuentro · Elegir el próximo caso de un residente · Lo
decidido y comprobado · La pantalla del encuentro (2026-10-02) · Fotos y POCUS: qué muestran y qué no · La sala
desde la Fase 0 (2026-10-06) · **El candidato de B-5 (implementado en local el 2026-10-08)** (nueva) · Limitaciones
conocidas · Si algo no calza.

**Dónde está cada tema (líneas del archivo final):**

| Tema | Líneas | Qué dice, en breve |
|---|---|---|
| Limitaciones del simulador | 46–48, 57–59, 113–131, 154–169, 184–218, 247–291 | Lo que el simulador no muestra no es evidencia ni omisión; límites por caso (manifiesto); POCUS/E-FAST sólo informes escritos; brechas del lector (TD-45, TD-69); transfusión (TD-32); «suero glucosado» sin decidir; hallazgos sin evolución (TD-59); segundo curso de trombolítico |
| Idioma | 30–38, 156–158, 214–215, 277–289 | Piloto en inglés y español; sala en español (X-1, V-9, F0-11, ES-P1 a ES-P13); registro, Trace y ledger en inglés canónico; lo escrito por el residente, tal como lo escribió |
| Puntaje y retroalimentación | 20–24, 49–59, 199–206, 224–225 | La IA no asigna ni propone; sin nota global ni ranking; rúbrica 0–3 o «No evaluable»; evento crítico −3 sólo confirmado por el docente; guardas A–E; foco de aprendizaje tras la revisión; rúbrica en español aprobada (D4 R-1, D5 b) |
| Datos y privacidad | 35–37, 60–61, 69 | Registro canónico en inglés; anular con motivo, el original queda; el residente no sabe que su caso fue elegido |
| Flujo del residente (visto por el docente) | 141–152, 175–218 | Pantalla, recibos, tiempo, interrupciones, paro, compuerta, aclaraciones, envío |
| Flujo docente | 40–69, 293–297 | Revisar, puntuar, eventos críticos, objetivos, anular, dirigir un caso, qué hacer si algo no calza |
| Qué puede y qué no puede modelar | 25–29, 73–131, 160–169, 184–193, 247–291 | 30 casos (la 41m fuera); lisis del TEP; anafilaxia; trauma; C14; 33f; paro no modelado tras el paro; POCUS sin destreza ni imágenes |

**Lo que depende del candidato recién implementado** (deja de ser cierto si se despliega otro SHA):
- líneas 7–14 (estado y alcance: «candidato final local de B-5 … ES-P1 a ES-P13»);
- líneas 30–38 (la sala en español: X-1, V-9, rúbrica en español, «lo único que se ve en inglés … es lo que escribió el residente»);
- líneas 156–158 (nota de la foto en el idioma del encuentro, J-64);
- líneas 167–169 (POCUS de control en la neumonía, D-42);
- líneas 220–245 (sección «El candidato de B-5»: relato 30/30 y rúbrica 5/5 con su hash, A-2, A-6 a A-8a, A-9 a A-11, TD-84, K-18, K-E5, K-E6, K-E16, TD-85, XR-18, X-1);
- líneas 269–272 (TD-51 resuelta por A-2);
- líneas 277–289 (relato y sala en español, ES-P1 a ES-P13, ES-P11 canónico).

**Observaciones para la revisión (no se cambiaron; decide la docencia).** Tres frases no cambiaron desde `f59b953` y
ya no coinciden con lo decidido el 2026-10-07:
- líneas 113–114: «la firma de cada ficha final sigue pendiente» — las 13 fichas R-2 del piloto (F-47 a F-58 y
  F-60) quedaron aprobadas el 2026-10-07 (paquete de firma, bloque F); sólo la de la 41m (F-59, opcional, sandbox
  docente) quedó sin decidir;
- líneas 137–139: «Las 18 frases finales del motor esperan su firma» — las 18 frases de R-4 quedaron decididas el
  2026-10-07 (bloque A: 15 APPROVE y 3 REVISE, implementadas en IG-4 e IG-5);
- líneas 295–297: «Lo pendiente de su firma está en `CIERRE_PREPILOTO.md` y `F0_11_FRASES_ES.md`» — las decisiones
  requeridas de esas hojas quedaron tomadas en el paquete (100 de 100); sin decidir quedan sólo los ítems opcionales
  de la 41m, fuera del piloto de residentes, y la firma de estas dos guías.
Si la docencia quiere corregirlas antes de firmar, es un cambio sólo de documentación en la guía (cambia su hash,
no el código del candidato). Si firma así, quedan como texto histórico.

**Cambios desde la última versión revisada (`f59b953` → `37c9afb`), exactos:**

```diff
diff --git a/docs/GUIA_DOCENTE_PILOTO.md b/docs/GUIA_DOCENTE_PILOTO.md
index 106e53b..9895037 100644
--- a/docs/GUIA_DOCENTE_PILOTO.md
+++ b/docs/GUIA_DOCENTE_PILOTO.md
@@ -2,9 +2,14 @@
 
-Para quien revisa encuentros durante el piloto. El detalle técnico está en `docs/RUNBOOK_PILOTO.md` y en
-`docs/READINESS_PILOTO_FORMATIVO.md`.
-
-> **Estado (Fase 0 cerrada el 2026-10-06): lista para su firma, no aprobada.** Describe el funcionamiento
-> comprobado al cierre del paquete prepiloto (D-1 a D-11) y lo que cambió la Fase 0 (F0-1 a F0-12), con las
-> etiquetas de la pantalla en español y, entre paréntesis, en inglés. Lo implementado vale sólo para
-> encuentros nuevos: uno anterior conserva su registro y la declaración con que se congeló.
+Para quien revisa encuentros durante el piloto. El detalle técnico está en
+`docs/revision/PILOT_PROMOTION_DEPLOYMENT_RUNBOOK.md` (que reemplaza a `docs/RUNBOOK_PILOTO.md` para el piloto) y
+en `docs/READINESS_PILOTO_FORMATIVO.md`.
+
+> **Estado (2026-10-08): actualizada al candidato final local de B-5 (IG-6, con ES-P1 a ES-P13 decididos e
+> implementados), para su firma (H-62); no está firmada.** El SHA exacto del candidato queda en el informe de su
+> certificación.
+> Describe el funcionamiento comprobado al cierre del paquete prepiloto (D-1 a D-11), lo que cambió la Fase 0
+> (F0-1 a F0-12) y lo implementado en local el 2026-10-08 con las decisiones docentes de B-5 («El candidato de
+> B-5»), todavía no desplegado, con las etiquetas de la pantalla en español y, entre paréntesis, en inglés. Lo
+> implementado vale sólo para encuentros nuevos: uno anterior conserva su registro y la declaración con que se
+> congeló.
 >
@@ -25,7 +30,10 @@ Para quien revisa encuentros durante el piloto. El detalle técnico está en `do
 - **Idioma (X-1):** el piloto corre en inglés y en español. El residente elige el idioma antes de empezar y
-  queda fijo durante el encuentro. Los mensajes nuevos de la Fase 0 sobre las órdenes (recibos, esperas,
-  interrupciones, paro, la respuesta a una aclaración) se dicen en ese idioma (F0-11). El registro, el
-  Management Trace y el ledger se guardan en inglés; sus destinos y códigos (EXECUTED, UNRECOGNIZED,
-  HELD_REASONING…) son canónicos y no se traducen. Lo que todavía se ve en inglés en un encuentro en español
-  está en «Limitaciones conocidas».
+  queda fijo durante el encuentro. En un encuentro en español la sala habla en español (X-1, 105 decisiones):
+  el relato aprobado de los 30 casos, el examen, las preguntas sobre una orden, la compuerta de razonamiento,
+  los recibos (F0-11), los rótulos, el monitor, el ECG, los tratamientos en curso y las pantallas del cierre.
+  Los fármacos se nombran en español (V-9), también en los documentos que se descargan en español; dosis,
+  unidades, vías y siglas se escriben igual. El registro, el Management Trace y el ledger se guardan en inglés;
+  sus destinos y códigos (EXECUTED, UNRECOGNIZED, HELD_REASONING…) y los nombres canónicos de los fármacos no se
+  traducen. La rúbrica en español (D1 a D5) es la que usted aprobó. Lo único que se ve en inglés en la sala de
+  un encuentro en español es lo que escribió el residente, tal como lo escribió (véase «Limitaciones conocidas»).
 
@@ -148,4 +156,4 @@ una omisión. La decisión de trombolizar se juzga como antes, en su minuto.
 - **Fotos.** Sólo se muestran fotos con sus dos revisiones humanas aprobadas. Una foto fija no muestra todos
-  los signos: la sala lo recuerda junto a la foto («A still photograph does not show every clinical sign;
-  examine the patient to assess what it cannot carry.»; esa nota todavía se ve en inglés). Lo que la foto no
+  los signos: la sala lo recuerda junto a la foto, en el idioma del encuentro («Una fotografía fija no muestra
+  todos los signos clínicos; examina al paciente para evaluar lo que no puede mostrar.»; J-64). Lo que la foto no
   muestra está en el examen. `bradycardia_bb_54f` y `pulmonary_edema_75f` llegan con la vista neutral.
@@ -156,5 +164,7 @@ una omisión. La decisión de trombolizar se juzga como antes, en su minuto.
 - **POCUS y E-FAST de control (TD-54).** Un POCUS repetido no cambia la VCI con el volumen o el control de la
-  hemorragia en el trauma, ni muestra líneas B nuevas con la sobrecarga de cristaloides en la neumonía (la
-  saturación sí cae); un E-FAST de control repite las ventanas de llegada (en la 41m, sólo en el sandbox
+  hemorragia en el trauma; un E-FAST de control repite las ventanas de llegada (en la 41m, sólo en el sandbox
   docente, también el receso drenado). No exija ver un cambio que el simulador no muestra.
+- **POCUS de control en la neumonía (D-42; `pneumonia_46f` y `pneumonia_83m`).** Un POCUS de control muestra que la
+  VCI se llena con el volumen, pero en los pulmones no muestra líneas B nuevas por la sobrecarga de cristaloides; la
+  saturación sí cae. No se exige ver líneas B nuevas.
 
@@ -209,2 +219,29 @@ Lo que cambió la Fase 0 y cómo leerlo al evaluar. Vale para encuentros nuevos.
 
+## El candidato de B-5 (implementado en local el 2026-10-08)
+
+Lo que las decisiones docentes de B-5 cambiaron en la sala. Vale para encuentros nuevos.
+
+- **Relato (30 de 30) y rúbrica (5 de 5) en español,** cada uno atado al hash que usted aprobó; en la rúbrica, D4
+  con «revisar/vigilar» (R-1) y D5 con la opción b. Estructura, niveles, puntaje y la rúbrica inglesa no cambian.
+- **El examen dice el estado del motor.**
+  - Edema pulmonar agotado (A-2): «Crépitos inspiratorios bilaterales; el esfuerzo respiratorio ahora es
+    superficial e ineficaz, compatible con agotamiento.»
+  - `asthma_49m` (A-6, A-6a, A-6b, A-7-49m, A-8a): conserva el examen grave de llegada mientras su obstrucción no
+    mejora, respirando solo o con VMNI; intubado sin mejoría, «Tubo endotraqueal instalado: el murmullo pulmonar
+    sigue muy disminuido…»; el neumotórax y la descompresión tienen sus frases propias. La elección es por el
+    estado de cada examen, no por la orden ni por el fármaco de inducción. La 24f no cambia.
+  - Opioides (A-9 a A-11): con ventilación asistida, «Frecuencia respiratoria {n}/min, dada por la ventilación
+    asistida en curso.»
+  - Opioides (TD-84): el examen inglés dice «Pupils are small and reactive.», como ya lo decía el español.
+- **Paros y eventos.** Paro de la anafilaxia después de una dosis (K-18): «…la adrenalina administrada antes no
+  logró mantener la reacción bajo control…»; etiqueta del paro (K-E5): «paro circulatorio por anafilaxia sin
+  adrenalina eficaz»; bradicardia (K-E6 y TD-85): «paro circulatorio por bradicardia profunda» y, en la sala en
+  español, «Paro circulatorio por bradicardia profunda.»; reacción bifásica (TD-85): «La reacción anafiláctica
+  vuelve.»; saturación (K-E16): «saturación de 84 % y en descenso». Disparadores, minutos, prevenibilidad y
+  fisiología no cambian.
+- **Vía oral (XR-18):** con el paciente que no puede tragar, la pregunta termina «…hasta que sea seguro
+  administrar por vía oral.» (en inglés, «…until oral administration is safe.»). La lógica de la vía no cambia.
+- **Preguntas sobre una orden (X-1):** nombran el fármaco que el residente escribió o, si sólo se reconoció una
+  clase, su nombre («betabloqueador»), nunca una clave interna.
+
 ## Limitaciones conocidas
@@ -231,4 +268,6 @@ Son para el docente; **no se le dicen al residente como instrucciones**.
 - **«Suero glucosado» sin concentración:** sigue sin decidir.
-- **Edema pulmonar sin tratamiento (TD-51, diferida):** durante unos 12 minutos el examen dice «Bilateral
-  inspiratory crackles with increased respiratory effort.» mientras el esfuerzo ya es «Exhausted».
+- **Edema pulmonar sin tratamiento (TD-51, resuelta por A-2):** cuando el esfuerzo del motor es «Exhausted», el
+  examen lo dice: «Crépitos inspiratorios bilaterales; el esfuerzo respiratorio ahora es superficial e ineficaz,
+  compatible con agotamiento.» (en inglés, «…consistent with exhaustion.»). Ya no hay minutos en que el examen diga
+  un esfuerzo aumentado mientras el paciente está agotado.
 - **Hallazgos sin evolución en el motor (TD-59):** la urticaria, el enrojecimiento y el edema de labios y
@@ -237,9 +276,15 @@ Son para el docente; **no se le dicen al residente como instrucciones**.
   No exija reevaluarlos.
-- **Relato en español:** sólo se muestra el de los casos cuya traducción usted aprobó en el tablero
-  docente. El resto se ve en inglés, línea por línea entera, también en el POCUS y el E-FAST. Las frases
-  nuevas de la Fase 0 se dicen siempre en español en un encuentro en español (F0-11). Mientras no se activen
-  (X-1), las frases del motor de R-4 (la auscultación y las vías venosas, entre otras) y el aviso de la foto
-  se ven en inglés. Anteriores a la Fase 0, también se ven en inglés, en todo o en parte, la mayoría de las
-  preguntas de aclaración de la sala (dosis, vía, flujo, ritmo de infusión), el aviso de una orden retenida
-  por la compuerta de razonamiento y varios rótulos de la sala.
+- **Relato y sala en español:** el relato en español de los 30 casos del piloto es el que usted aprobó, en su
+  versión exacta (`case_text/es/approvals.json`); el caso del sandbox docente (`trauma_hemothorax_41m`) sigue en
+  inglés. Las frases del motor de R-4, el aviso de la foto y las preguntas de la sala se dicen en español, y
+  también, desde el 2026-10-08, los textos que usted decidió fuera del inventario de X-1 (ES-P1 a ES-P13;
+  `docs/revision/B5_IG5_PENDIENTES_DOCENTES.md`): la ayuda del selector de idioma, «Preguntar por: {tema}», «Última
+  respuesta», «Ficha clínica · examen · resultados · registro de tratamientos», las frases de gastroenterología
+  (con la hemoglobina, con la presión sistólica o con ambas), «unidades» (nunca «UI»), «Control de la hemorragia»
+  y «Glóbulos rojos», las 15 aclaraciones del lector sobre lo que no está activo, la base de la dosis del ácido
+  tranexámico sin dosis escrita, las dos frases de la fibrilación ventricular y la última línea de una orden
+  retenida. Lo que escribió el residente se muestra tal como lo escribió, también dentro de esas frases (por
+  ejemplo, la lista de «También se reconoció lo siguiente, pero no puede ejecutarse en esta versión: …»). La
+  etiqueta canónica «endoscopy performed» queda en inglés en el registro y en el tamizaje: no se muestra en la
+  sala (ES-P11).
 - **TEP:** un segundo curso de trombolítico no tiene efecto propio en el simulador (simplificación
```

## 2. I-63 · `docs/GUIA_RESIDENTE_PILOTO.md`

**Título y versión.** «Guía del residente · piloto formativo». Estado en el archivo: «actualizada al candidato final
local de B-5 (IG-6, con ES-P1 a ES-P13), para la firma docente (I-63); no está firmada … Se entrega a los residentes
sólo después de la firma».

**Archivo final.** 112 líneas · sha256 `0b37b7acca04d677174d32b71140d1b112dc43f7c125631f8d69a2c239e113a6` · blob git `8af7d361d1a8658fd99fe6734693df80034a5fb5`.

**Secciones (todas sustantivas):** (introducción) · Antes de empezar · El encuentro · La pantalla del encuentro · La
foto y el POCUS · Después.

**Dónde está cada tema (líneas del archivo final):**

| Tema | Líneas | Qué dice, en breve |
|---|---|---|
| Limitaciones del simulador | 34–37, 49–54, 77–82, 92–97 | Aclaraciones sin minutos; reloj máx. 120 min; espera cortada por un evento; reanimación no modelada (nada después del paro se ejecuta ni se evalúa); «registrado, no administrado»; orden para más tarde no programada; foto fija; POCUS/E-FAST como informe escrito |
| Idioma | 17–23, 74–75, 86 | Elegir idioma, fijo durante el encuentro; la sala en español; fármacos en español, dosis/unidades/vías/siglas igual; lo escrito por el residente, tal como lo escribió |
| Puntaje y retroalimentación | 8–9, 101–102 | Formativo; sin nota global, ranking ni tabla; ninguna IA lo evalúa; un docente revisa; foco y retroalimentación después de la revisión |
| Datos y privacidad | 13–16, 24, 44, 107–109 | Cuenta por invitación; foto e iniciales opcionales; sin datos reales; el Trace guarda lo escrito y lo ocurrido; descarga del registro completo; otro residente no ve nada tuyo |
| Flujo del residente | 26–88, 99–110 | Comenzar, leer la llegada, actuar en texto libre, razonamiento con las órdenes de manejo, tiempo, paro, destino, revisión de decisiones, pantalla, envío, menú, páginas propias |
| Flujo docente (visto por el residente) | 9, 101–102 | Un docente revisa cada encuentro |
| Qué puede y qué no puede modelar | 41–43, 53–54, 78–81, 92–97 | Intervenciones urgentes nunca retenidas; reanimación no modelada; respuestas no modeladas; foto y POCUS |

**Lo que depende del candidato recién implementado:**
- líneas 3–6 (estado: «candidato final local de B-5 … ES-P1 a ES-P13»);
- líneas 19–23 (la sala en español, fármacos en español, «lo que tú escribiste se muestra tal como lo escribiste, también cuando la sala lo cita dentro de una frase en español»);
- líneas 74–75 (los modos en español: «Conversar», «Examinar», «Exámenes», «Tratar»);
- líneas 92–93 (la nota de la foto, ya sin «por ahora, en inglés»).

**Observaciones para la revisión:** ninguna contradicción hallada con el candidato.

**Cambios desde la última versión revisada (`f59b953` → `37c9afb`), exactos:**

```diff
diff --git a/docs/GUIA_RESIDENTE_PILOTO.md b/docs/GUIA_RESIDENTE_PILOTO.md
index 54e73d7..8af7d36 100644
--- a/docs/GUIA_RESIDENTE_PILOTO.md
+++ b/docs/GUIA_RESIDENTE_PILOTO.md
@@ -2,5 +2,6 @@
 
-> **Estado (Fase 0 cerrada el 2026-10-06): lista para la firma docente, no aprobada.** Se entrega a los
-> residentes sólo después de esa aprobación. Las etiquetas van como las muestra la pantalla en español y,
-> entre paréntesis, en inglés.
+> **Estado (2026-10-08): actualizada al candidato final local de B-5 (IG-6, con ES-P1 a ES-P13), para la firma
+> docente (I-63); no está firmada.** Describe la sala implementada en local el 2026-10-08, todavía no desplegada. Se entrega a los
+> residentes sólo después de la firma. Las etiquetas van como las muestra la pantalla en español y, entre
+> paréntesis, en inglés.
 
@@ -17,9 +18,7 @@ posiciones, y ninguna inteligencia artificial lo evalúa. Un docente revisa cada
   español o en inglés, y puedes escribir tus órdenes en cualquiera de los dos. Durante un encuentro el idioma
-  queda fijo. Lo que la sala te dice sobre tus órdenes (qué pasó con cada una, las esperas, las
-  interrupciones, el paro) se ve en el idioma que elegiste. Parte del relato de un caso, como su informe
-  POCUS, puede verse en inglés mientras su traducción no esté aprobada, y también algunas líneas del examen
-  que escribe el simulador (por ejemplo, la auscultación o las vías venosas); cada línea se ve entera en un
-  solo idioma. Por ahora, muchas preguntas de la sala sobre una orden (por ejemplo, qué dosis o qué vía), el
-  aviso de una orden retenida para que expliques tu razonamiento y algunos rótulos de la pantalla todavía se
-  ven en inglés, en todo o en parte.
+  queda fijo. En un encuentro en español, la sala te habla en español: el relato del caso (también el POCUS y
+  el E-FAST), el examen, las preguntas sobre tus órdenes, el aviso de una orden retenida, los recibos, los
+  rótulos y los documentos que descargas. Los fármacos se nombran en español («noradrenalina», «salbutamol»);
+  las dosis, las unidades, las vías y las siglas se escriben igual (mg, mL/h, IV, FiO₂, CPAP). Lo que tú
+  escribiste se muestra tal como lo escribiste, también cuando la sala lo cita dentro de una frase en español.
 - **Sin datos reales:** no escribas nombres ni datos de pacientes reales. Todo es simulado.
@@ -74,3 +73,4 @@ posiciones, y ninguna inteligencia artificial lo evalúa. Un docente revisa cada
   Consultarlas no envía nada ni borra lo que estás escribiendo.
-- **A la derecha, abajo, «Manejo»:** elige un modo (Talk, Examine, Tests, Treat; el elegido lleva ✓), escribe
+- **A la derecha, abajo, «Manejo»:** elige un modo («Conversar», «Examinar», «Exámenes» o «Tratar»; en inglés,
+  Talk, Examine, Tests y Treat; el elegido lleva ✓), escribe
   y pulsa «Enviar» («Send»). Enter agrega una línea; no envía. Bajo los modos, la sala te dice qué pasó con tu
@@ -92,4 +92,4 @@ posiciones, y ninguna inteligencia artificial lo evalúa. Un docente revisa cada
 - **La foto** es una imagen fija del paciente, revisada por un docente. No muestra todos los signos clínicos:
-  examina al paciente para evaluar lo que una foto no puede mostrar. La sala lo recuerda junto a la foto
-  (por ahora, en inglés). Algunos casos llegan con una vista neutral, sin foto: el monitor, el examen y los
+  examina al paciente para evaluar lo que una foto no puede mostrar. La sala lo recuerda junto a la foto.
+  Algunos casos llegan con una vista neutral, sin foto: el monitor, el examen y los
   resultados dicen lo mismo de todos modos.
```
