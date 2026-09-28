# TD-26 y C7-06 · Hemoderivados, transfusión masiva, control de hemorragia, acceso IO y prueba de embarazo

Ciclo 7 · 2026-09-28 · decisiones docentes §5–§7 y §63–§82 de la instrucción del
ciclo.
Registro: C-2026-09-28-13 (TD-26) y C-2026-09-28-14 (C7-06).
Pruebas: `test_blood_products_and_bleeding_orders.py`.

**Principio.** Si la persona residente indica claramente algo, el motor nunca lo
pierde en silencio. Hay tres salidas posibles:

- **lo ejecuta**, si lo modela;
- **lo registra como indicado, con el efecto no modelado**, si no lo modela;
- **pregunta**, si es realmente ambiguo.

Y dos distinciones que se mantienen siempre:

- **NO MODELADO ≠ NO HECHO:** lo que el motor no modela no se registra como
  omisión.
- **FISIOLOGÍA ≠ TRACE:** el Trace dice lo que hizo la persona residente,
  aunque el motor no simule su efecto.

## Qué hace ahora el lector

| Qué escribe la persona residente | Qué pasa | Qué dice el Trace |
|---|---|---|
| **Glóbulos rojos**: «2 U de GR O negativo», «2 UGR», «O-neg», «packed cells», «uncrossmatched», «concentrado eritrocitario», «dos unidades» | Corren las unidades escritas (1–4 por orden, la regla del motor). Sin unidades, el motor pregunta cuántas | «Packed red cells 2 units started» |
| **Plasma, plaquetas, crioprecipitado, sangre total** | Se registran como indicados, con su efecto fisiológico no modelado. Nunca se convierten en glóbulos rojos, y el resto del envío corre | «2 units ffp (blood product ordered; physiologic effect not modelled)» |
| **Activación del protocolo de transfusión masiva** («MTP», «PTM», «activo transfusión masiva») | Se registra la activación. No administra nada por sí sola: corren sólo las unidades que se escriben. No se inventan unidades, razones ni protocolos | «activate mtp (massive transfusion protocol activated; the activation gives no blood product by itself)» |
| **Transfusión sin producto** («transfuse», «hemoderivados») | Pregunta. Con un número de unidades y sin otro producto nombrado («transfundir 2 unidades») son glóbulos rojos, como se escribe en urgencia | — o las unidades |
| **Una proporción o un conteo para varios productos** («GR/PFC 2 U c/u», «GR y plasma 1:1, 4 U de cada uno», «PRBC and FFP 1:1») | Pregunta: «Write each blood product with its own number of units» | — |
| **Dos órdenes de glóbulos rojos en una frase** («2 U GR ahora y 2 U GR en 1 hora») | Una sola orden, cuyo número se pregunta | — |
| **Reserva o disponibilidad** («reservar», «dejar listas», «cruzar 4 U», «hold 2 units») | Nunca transfunde. Con «reservar», grupo y pruebas cruzadas; si no, pregunta si transfundir ahora o reservar | «Blood group and crossmatch» o la pregunta |
| **Detener, suspender o mantener una transfusión** («suspender transfusión de las 2 U GR», «stop the PRBC», «mantener transfusión de 2 U GR») | Nunca transfunde. El motor no modela detenerla: la orden se devuelve citada para reescribirla | — |
| **Lo que no es una orden ahora** (un resultado, lo recibido antes o en ruta, un rechazo, una pregunta, un plan, un umbral, un consentimiento, una pérdida estimada, insulina junto a «blood glucose») | No transfunde nada | — |
| **Control de hemorragia** («pack the wound», «hold pressure», «presión directa sobre la herida», «empaquetar», «torniquete») | Cada medida es su propia orden, en el orden escrito, y ninguna se convierte en otra. Un apósito conserva su nombre («pressure dressing», «apósito hemostático») | «Packing applied to the wound…», «Direct pressure applied…» |
| **«Hemorrhage control» sin medida** | Pregunta cuál medida | — |
| **Detener el sangrado con una medida** («stop the bleeding with direct pressure», «detener sangrado: presión directa») | Es esa medida | la medida |
| **Retirar, soltar o convertir una medida** («remove the tourniquet», «reemplazar torniquete por vendaje compresivo») | Nunca aplica la medida. El motor no modela retirarla: se devuelve citada | — |
| **Acceso intraóseo** («humeral IO», «EZ-IO», «vía intraósea humeral», «coloco una vía intraósea», «place humeral IO for fluids») | Se registra como intraóseo, con su sitio. Nunca como vía venosa. Retirarlo o describirlo («the humeral IO is infiltrated») no lo instala | «intraosseous access (humeral) placed» |
| **Una dosis escrita «IO»** | Es la vía de esa dosis, nunca una vía instalada | la dosis, con vía IO |
| **Prueba de embarazo** («β-hCG», «UPT», «prueba de embarazo», «test pack») | Se registra el pedido. Su resultado no está modelado y no se inventa. Nada más se retiene | «Study requested; not modelled…: Pregnancy test» |

**Un envío con sólo lo registrado** (por ejemplo, «Activate the massive
transfusion protocol» o «Transfuse 2 units FFP» solo):

- **Antes:** el motor respondía «Please specify a question…», retenía la orden
  y la dejaba fuera del registro que lee la docencia.
- **Ahora:** se registra como decisión de la persona residente, sin que pase
  ningún minuto (`family_engine.recorded_only`). Vale en los tres motores:
  familias, generados y el núcleo acoplado.

## Qué no cambió

- Los eventos críticos, el −3, los puntajes, D1–D5 y el radar.
- La regla de 1–4 unidades por orden.
- La fisiología de la hemorragia y de la transfusión (TD-21 es aparte).
- **Nada nuevo tiene efecto fisiológico propio.** El plasma, las plaquetas, el
  crioprecipitado, la sangre total y la activación no mueven el paciente. La
  única consecuencia nueva: una IO instalada cuenta como vía nueva, como
  cualquier otra, y reemplaza una vía fallida (§82: la abstracción existente).

## Lo que la docencia ve

- **Sala:** «Blood product ordered and recorded as your decision: … Its
  physiologic effect is not modelled…». Nunca «nothing was given», que diría
  que la persona residente no lo dio. En español: «Hemoderivado indicado y
  registrado como tu decisión…».
- **Rúbrica.** Un hemoderivado se nombra «a blood product», no «a medicine»,
  y como indicado: «Ordered by the resident, with its physiologic effect not
  modelled».
- **Eventos críticos.** En «cristaloide en vez de sangre» y «HDA sin
  reanimación», la definición nombra sangre ejecutada. Si en la ventana se
  indicó un hemoderivado no modelado, el resultado pasa de «met» a
  **«reading»**, con el hecho a la vista. El límite del motor nunca aparece
  como omisión de la persona residente. La definición no cambió.
- **Análisis con IA.** Los prompts dicen que un hemoderivado se indicó y
  queda como indicado, nunca «no administrado». Versiones: `faculty_analysis`
  1.7 y `rubric_analysis` 1.3; las anteriores siguen validando.

## Límites documentados

- **Acceso IO.**
  - El motor da el mismo efecto a una dosis IV y a una IO. No tiene fisiología
    IO propia (así lo dice la nota de la sala).
  - Instalar una IO reemplaza una vía fallida.
  - **Una dosis «IO» escrita sin instalar la IO** pasa todavía como por la vía
    fallida de la configuración de hipoglicemia. Es el resto de DC3, pendiente
    con el alcance de la decisión 8 (P10, DC4).
- **«gr» como gramos** («paracetamol 1 gr ev») sigue sin leerse, como antes:
  retenido con una pregunta, nunca como glóbulos rojos. Queda en TD-14.
- **Vía y suero en la misma frase** («two large-bore IVs with 1 L NS», «2 VVP
  gruesas con SF 1000 mL») sigue retenido con una pregunta, como antes. No se
  pierde, pero cuesta una respuesta. Queda en TD-14.
- **Hemocultivos sin verbo** («blood cultures x2, then ceftriaxone…») se
  siguen perdiendo en silencio (TD-14, fuera de este alcance, §8).
- **Órdenes sin verbo que siguen sin leerse, como antes del ciclo** (TD-14 y
  KD-02, fuera de este alcance):
  - «surgery consult»;
  - «Endoscopía urgente» (con o sin «para control de hemorragia»);
  - «2 large-bore IVs» y «2 large-bore IVs or IO».

  Antes, «Endoscopía urgente para control de hemorragia» y «Hemorrhage control:
  surgery consult» **aplicaban presión directa**. Ya no la aplican, pero la
  endoscopia y la interconsulta siguen sin leerse.
- **«Direct pressure with packing»** son dos medidas, y el motor suma sus
  efectos: controla el sangrado como un torniquete. Es la regla del motor para
  medidas combinadas, sin cambio.
- **Lo que queda sin aviso, LOW:**
  - «Deactivate MTP»;
  - «Platelets if count < 50» (un plan de plaquetas sin verbo);
  - «2 U. GR» (el punto parte la frase);
  - el sufijo «c/u» de una duración («2 U GR en 2 horas c/u» corre en 2 horas en
    total).
- **Un estado de las pruebas cruzadas se registra como pedido** («pruebas
  cruzadas en curso», «type and cross pending»). Así era antes del ciclo; LOW.
- **«When» y «cuando» no hacen condicional una orden que no es sangre.** «When
  BP drops, give NS 500 mL» y «Cuando baje la PA, bolo SF 500 mL» corren ahora;
  «if» y «si» sí la guardan como plan. En la sangre, «cuando» y «once» ya
  preguntan. Es anterior al ciclo y está en TD-14 (HIGH); lo mide el piloto.

## Cómo se decide si unas unidades corren

La revisión adversarial mostró que bastaba una palabra de glóbulos rojos y un
número en cualquier parte de la frase para que corriera una transfusión que
nadie ordenó: «Hb 6,2 tras 2 U GR», «SAMU: 1 U GR O negativo en ruta», «rechaza
transfusión de 2 U GR», «Insulin 4 units SC for blood glucose 300». Se rediseñó
la regla. Ahora las unidades corren sólo en dos casos:

- **Una línea de ficha.** La línea abre con los glóbulos rojos («2 U GR O
  negativo», «GR 2 U», «O-neg 2 units», «2 UGR», «Transfusión de 2 U GR») y no
  dice más que cuándo, por dónde y a qué velocidad.
- **Un verbo que los da.** Un verbo que da glóbulos rojos los tiene por objeto:
  «transfundir 2 U», «hang 4 PRBC», «pasen 2 GR no cruzados».

Todo lo demás:

- **Si la línea dice algo más,** se pregunta.
- **Si dice que ya ocurrió, o es un plan, una alternativa, una pregunta o una
  detención,** no se ordena nada.
- **Lo que el motor no hace** (detener o mantener una transfusión, retirar una
  medida) se devuelve citado.

## Validación A–J

Todos los conjuntos son **INTERNAL DEVELOPMENT DATA**: frases escritas para
este ciclo y guardadas fuera del repositorio, en el espacio temporal de la
sesión. **No son datos externos
ni validación.** Ninguno se mezcló con el corpus del piloto, y nada SEALED se
usó.

**Cómo leer las tablas.** «Correcta» es ejecutar, registrar o preguntar lo que
corresponde. «Retenida» es una pregunta, que no es silenciosa pero cuesta una
respuesta. «Perdida» es sin aviso. «Falsa» es ejecutar o registrar lo que no
se ordenó.

| Medición | Frases | Lector anterior (HEAD del ciclo 6) | Lector final |
|---|---|---|---|
| **A · Conjunto independiente** EN/ES, escrito sin ver el código; se usó para desarrollar | 74 | 32 correctas · 39 retenidas · **3 perdidas** | 51 correctas · 19 retenidas · **0 perdidas · 0 falsas** (las 4 «perdidas» del puntaje automático son errores de etiqueta, adjudicados uno por uno) |
| **B · Conjunto ciego** (held-out) EN/ES, escrito sin ver el código, **medido una vez** antes de cualquier arreglo | 70 | 23 correctas · 45 retenidas · **1 perdida · 1 falsa** | **Medición ciega:** 35 correctas · 30 retenidas · **1 perdida real · 2 falsas** (2 «perdidas» más eran errores de etiqueta). **Post hoc**, tras los arreglos: 44 · 20 · **0 perdidas reales · 0 falsas** |
| **C · Revisión adversarial** (agente aparte, 656 entradas EN/ES en frases, motor, rúbrica y Trace) | 656 | — | Halló 16 CRITICAL, 16 HIGH, 14 MEDIUM y 7 LOW. Los 12 grupos de fallas re-ejecutados (203 entradas) pasan con el lector final |
| **D · Controles negativos** (lo que no debe transfundir, registrar ni aplicar nada) | 94 en la revisión, 39 en las pruebas | — | Ninguno ejecuta |
| **E · Comparación con el lector anterior** en todo texto de orden que guarda el repositorio | 12 142 | — | 70 textos se leen distinto fuera de las pruebas del ciclo 7; cada diferencia se revisó: son correcciones o mejoras. Las regresiones que mostró la comparación se corrigieron |

**Cuatro detalles de lectura:**

- **«Perdida» por etiqueta.** Las etiquetas pedían registrar como «hemoderivado
  no modelado» órdenes de glóbulos rojos. Esas unidades **corren** en el número
  escrito, que es lo decidido (TD-26 A).
- **Lo que halló la medición ciega:**
  - la unidad escrita «O-» no se leía;
  - «tubo pleural ya instalado» y «chest tube already in place» instalaban un
    tubo.
- **Arreglos post hoc.** Estos tres, y los de las filas siguientes, son
  **post hoc**. La medición ciega no se repite como si fuera ciega.
- **Retenidas que quedan:** comentario clínico junto a la orden, un alcance
  condicional («if avail»), un IBP, «start abx», lo informado como dado,
  «call it», «mando» y la adrenalina IM sin dosis. Ninguna se pierde sin aviso.

### Hallado después de la revisión adversarial y corregido (post hoc)

Un barrido final sobre el lector ya corregido encontró nuevos casos. Todos se
corrigieron y tienen prueba:

- **Tres regresiones del propio ciclo:**
  - «transfusión de …» tomaba el verbo de la bolsa por encima de «suspender»,
    «retirar» o «mantener». Así, «Suspender transfusión de las 2 U GR», «Stop
    transfusion of 2 units» y «Mantener transfusión de 2 U GR» **ejecutaban** 2
    unidades. Ahora se devuelven citadas.
  - Un verbo que detiene se leía como la medida retirada. Así, «Stop the
    bleeding with direct pressure», «Detener sangrado: presión directa» y
    «Detén el sangrado con un torniquete» se perdían.
  - «Stop the PRBC» y «Disconnect the blood» quedaban sin aviso.
- **Pérdidas sin aviso anteriores al ciclo, dentro de TD-26 y C7-06:**

  | Orden | Ahora |
  |---|---|
  | «GR y plasma 1:1, 4 U de cada uno», «Plasma y GR 1:1» | pregunta |
  | «Un GR» | 1 unidad |
  | «Meets MTP criteria, activate» | activación registrada |
  | «Place humeral IO for fluids» | IO instalada |
  | «Remove the tourniquet», «Loosen the tourniquet…» | devueltas citadas |
  | «Balance: 2 U GR, 2 L SF», «So far 2 units PRBC and 2 L crystalloid» | nada; antes volvían a pasar el suero |

  Antes de este ciclo, «Remove the tourniquet» y «Loosen the tourniquet…»
  **aplicaban** el torniquete.

Tras estos arreglos se repitieron: el conjunto independiente, el ciego (post
hoc), los 12 grupos adversariales, la comparación con el lector anterior y la
suite completa. Después, **el lector se congeló para el ciclo**: lo que se
halle en adelante se registra y no se corrige (§120).
