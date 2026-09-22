# Los tres informes, rehechos — qué cambió y qué queda

> Respuesta a tus siete prioridades sobre los PDF y a las correcciones de interpretación de la
> evidencia, más la decisión B4.
>
> **Todo se verificó reusando el encuentro y las respuestas ya guardadas.** El guion que
> rehace los tres documentos bloquea cualquier conexión saliente: si algo intentara llamar al
> proveedor, falla en vez de gastar. **Cero llamadas nuevas.**
>
> Los tres PDF están regenerados y los revisé página por página, en imagen, no sólo en texto.

---

## 1. Textos truncados, títulos incompletos y saltos de página

**El truncado no era del renderizador.** El esquema del análisis limita cada campo a 600
caracteres y cada título a 90. El modelo escribe hasta el tope y el proveedor corta a media
palabra. Por eso la síntesis terminaba en *"After pressure and oxygenation improved but
perfusion markers"* y el título de la decisión 1 en *"(monitoring, IV access, ECG,"*.

Hice dos cosas distintas:

- **Subí los límites** a 900 y 140 caracteres, y agregué a las instrucciones que el campo debe
  terminar dentro del límite, escribiendo menos frases antes que una más larga.
- **Mientras tanto, el informe lo declara.** Un campo cuya longitud es exactamente la del tope
  y que no termina en punto fue cortado, y ahora se marca:
  `[…interrumpido: el análisis alcanzó su límite de extensión]`. Al pie, la procedencia dice
  cuántos campos quedaron así. Prefiero que se vea el corte a que se lea como una frase
  terminada.

**Saltos de página**: cada decisión abre con su encabezado, su título y lo observado en un
bloque que no se parte, y el resto fluye. Antes una decisión ocupaba media página y la otra
mitad quedaba en blanco; ahora la decisión 1 entera cabe en una página.

## 2. El mismo identificador en los tres documentos

Los tres muestran **`CE-ca78233055d782a3 · R1-05`**: el identificador del encuentro y su
desafío. Antes el informe del residente se encabezaba con el id del caso escrito por la IA y
el docente con el desafío, así que el mismo encuentro parecía dos. Hay una prueba que lo
verifica en los tres.

## 3. Acciones legibles en vez de campos del motor

Antes:

> `diagnostic (diagnostic type: pocus; duration min: 15); continuous monitoring and pulse oximetry started (operation: start; duration min: 2)`

Ahora:

> • Continuous monitoring and pulse oximetry (started)
> • Peripheral IV access (started)
> • 12-lead ECG requested · takes 1 min
> • Bedside ultrasound (POCUS) requested · result at 15 min

Se conservan dosis, vía, parámetros y tiempos, que es lo clínico: `Morphine 2 mg IV`,
`Non-invasive ventilation 14 cm H2O IPAP, 8 cm H2O EPAP, 50 % FiO2 (started)`,
`500 mL normal saline IV · over 20 min`, `Transcutaneous pacing 70 /min, 50 mA`. Una orden
compuesta conserva sus fármacos (`... with etomidate 20 mg IV + rocuronium 90 mg IV`).

Dos cosas que salieron de ahí: los resultados también llevan su unidad
(`lactate_mmol_l: 3.2` → **`lactate 3.2 mmol/L`**), y **la narración del motor dejó de
aparecer como orden del residente** — *"The monitor watches the patient and treats nothing"*
no lo escribió él.

## 4. El Management Trace, reorganizado

**Página 1**: síntesis del encuentro · trayectoria con los cuatro gráficos · interpretación de
la trayectoria · **qué llevarse** (patrones a conservar y preguntas para el próximo
encuentro). Antes los aprendizajes estaban al final, después de todo.

**Después, cada decisión en seis bloques**, en el orden en que un clínico la lee:

1. Qué habías observado · 2. Cómo razonaste · 3. Qué indicaste ·
4. Qué esperabas · 5. Qué quedó registrado después · 6. Punto para revisar

**La reflexión posterior va aparte**, en su propio recuadro, encabezada *"escrita después del
encuentro"* y con la advertencia de que no establece lo que entendiste mientras decidías.

**Los metadatos quedaron al final**, con el identificador, el modelo, la versión del prompt,
la huella de origen y el recuento de campos truncados.

## 5. Los gráficos

Cada panel lleva ahora **marcas de tiempo punteadas con D1…D5**, en el minuto en que se tomó
cada decisión, y el pie dice explícitamente que muestran cuándo actuaste y que **un cambio
después de una marca no establece que la acción lo haya causado**.

Además, una serie que **no se movió en todo el encuentro se rotula "no recorded change"**. En
este caso la frecuencia respiratoria: estuvo en 28 las cuatro horas. Eso responde a tu punto
de verificar que las variables usadas para evaluar realmente evolucionaban — si el motor no la
mueve, el informe no deja que parezca un hallazgo clínico.

## 6. El Faculty Brief

**Se dio vuelta el orden.** Página 1: síntesis del desempeño → prioridades de revisión →
preguntas para el debriefing → qué puede y qué no puede mostrar este encuentro. **Las
valoraciones sugeridas vienen después**, en la página 2, con su nota de que son provisionales
hasta que registres tu juicio.

El compacto pasó de 2 a **3 páginas**. Es deliberado: con texto de 11 puntos y las siete
valoraciones, en dos páginas el ajuste automático reemplazaba **todas** las justificaciones por
*"Review the full rationale in the app"*. Una ayuda de lectura sin la justificación no es una
ayuda de lectura. Si prefieres dos páginas, se recupera bajando el cuerpo a 9,5 puntos.

El completo sigue siendo el respaldo y lleva el mismo texto del modelo sin recortar. Hay una
prueba que verifica que **ambos documentos llevan la misma valoración por objetivo**, aunque
la redacción de la etiqueta sea distinta en cada uno.

## 7. Legibilidad

- Cuerpo de **11 puntos** en los tres documentos (antes 9,3–9,4).
- **Se eliminó el prefijo "AI interpretation:"** que el modelo repetía en cada campo. Los tres
  documentos ya dicen en su encabezado, su pie y sus títulos que todo eso es interpretación.
- **Referencias breves**: `Sources: Presentation · 0 min [encounter:0]; ...` pasó a
  `Based on: presentation at 0 min, examination at 0 min, D1 at 0 min`, sin identificadores de
  máquina y sin repetir la misma referencia dos veces.
- Metadatos completos al final, no a media página.

---

## Interpretación de la evidencia

### Lo que quedó implementado en el renderizador (verificable ahora)

**Las cuatro situaciones de una orden.** El bloque *"qué quedó registrado después"* distingue
ahora un estudio cuyo resultado llegó, uno **pedido cuyo resultado no está en el registro**,
uno **cuyo resultado no vencía todavía** y uno **pendiente al cierre del encuentro**. Un
electrocardiograma es un caso propio: su resultado es el trazado, que se guarda con el
encuentro, así que se informa como *acquired* y no como un resultado faltante — contarlo como
faltante habría sido cobrarle al residente una característica del simulador.

**Objetivos sin oportunidad.** Un objetivo con recomendación *insufficient evidence* y **sin
ninguna ancla de evidencia** se rotula **"Not assessed in this encounter — no recorded
opportunity to demonstrate it"**, en los dos documentos docentes. Es el caso de C4, sedación
procedural: el encuentro nunca dio ocasión de mostrarla. Un objetivo con evidencia citada
**no** se reetiqueta: eso sigue siendo una demostración débil, que es otra cosa.

**Provisionalidad.** El informe del residente dice en la primera página que toda interpretación
es provisional hasta la revisión docente; el compacto lo dice junto a la síntesis y encabeza
las valoraciones con "Provisional".

### Lo que quedó escrito en las instrucciones (requiere una llamada pagada para verificarse)

Agregué a los dos prompts, con el mismo texto:

- Una medición en un momento es una medición: no establece tendencia, persistencia ni falta de
  mejoría. Decir *"fue registrado como"* y no *"se mantuvo"* salvo que haya dos observaciones
  separadas.
- Distinguir la orden nunca escrita, la escrita y no ejecutada, la pendiente al cierre y
  aquella cuyo resultado no se registró. Un resultado ausente falta del registro; no lo negó el
  residente.
- **Una limitación de la simulación no es una decisión del residente.** El tiempo avanza en los
  intervalos que el encuentro permite, un estudio no disponible no se puede obtener, y una
  variable que el registro nunca mueve puede no estar modelada. Nada de eso es evidencia sobre
  el residente, y nada de eso va en un punto de revisión.
- No pedir una respuesta fuera de la ventana observada.
- (Docente) Cuando un objetivo no tuvo oportunidad de mostrarse, decirlo en la justificación.

**Esto es exactamente lo que produjo el juicio que te llamó la atención**: *"No supplemental
oxygen/support for 15 minutes despite hypoxemia and distress"*. El residente pidió su primera
reevaluación a los 15 minutos porque ése fue el intervalo que eligió; el motor no le ofrece una
granularidad menor para el soporte. Con la regla nueva eso no debería aparecer como una
demora atribuida a él. **No puedo confirmarlo sin regenerar el análisis**, y eso cuesta.

---

## Lo que cuesta verificar el cambio de análisis

Medido en las corridas de anoche, con `gpt-5`:

| Llamada | Tokens entrada | Tokens salida | Costo estimado |
|---|---|---|---|
| Análisis del Management Trace | 14.821 | 5.461 | ≈ **US$ 0,07** |
| Informe docente | 11.566 | 6.373 | ≈ **US$ 0,08** |
| **Una verificación completa (los dos)** | | | ≈ **US$ 0,15** |

**Los tokens son medidos; el dinero es estimado** y supone tarifas de US$ 1,25 por millón de
entrada y US$ 10 por millón de salida. Confírmalo contra tu factura antes de tomarlo como
cifra buena.

Con reintentos —y `gpt-5` falló la validación 1 de 2 veces— una verificación realista son
**dos o tres llamadas, unos US$ 0,25 a 0,45**. Ése es el alcance que te pido autorizar cuando
quieras confirmar las reglas nuevas y ver la síntesis sin cortes.

---

## La decisión B4, implementada

**La normalización de lenguaje pagada ya no se enciende sola.** Antes bastaba con que hubiera
clave configurada: corre antes de cada orden, de cada aclaración y de cada completación de
razonamiento, o sea **una llamada por envío** — seis llamadas en un encuentro de cinco órdenes,
que es como lo descubrí.

Ahora requiere las dos cosas: la clave **y** el interruptor `MRS_AI_LANGUAGE`. Por omisión está
apagada y trabaja el parser determinista, que es con el que jugamos todo este mes en español.
El modo offline sigue mandando por encima de ambos. Quince pruebas lo cubren, incluida una que
vigila que la aplicación consulte el interruptor **antes** de leer la clave, para que un
despliegue configurado no vuelva a pagar por orden sin que nadie lo decida.

---

## Pendientes

**De los PDF, nada bloqueante.** Lo que queda es tuyo de decidir:

1. **El compacto quedó en tres páginas.** Si lo quieres en dos, se baja el cuerpo a 9,5 puntos
   y te pierdes algo de legibilidad. Dime cuál prefieres.
2. **La síntesis y la trayectoria siguen cortadas** en los PDF que te entrego, porque vienen
   del análisis ya guardado. Se arregla en la próxima generación, con el límite nuevo.

**De las decisiones B1–B10, lo que no alcancé esta vuelta**, en el orden en que lo haría:

- **B10** — analizar y clasificar los seis intentos de generación guardados (tiempo, formato,
  contenido clínico, capacidad del motor, contradicción del revisor) y corregir la
  contradicción del revisor con un chequeo determinista trazable. Reprocesar primero las
  respuestas guardadas, sin pagar. Después te presento hipótesis, costo máximo y criterios de
  éxito antes de pedir generaciones nuevas.
- **B5** — ampliar el contrato a horizontes de 180 minutos o más **con trayectorias coherentes
  para ese período**, y permitir cierre o traspaso explícito al llegar al límite sin inventar
  evolución.
- **B2** — subir el timeout del cliente a 180 s si eliges `gpt-5`, y guardar el estado y el
  resultado del análisis para que recargar la página no genere otra llamada.
- **B3** — degradación controlada: validar por secciones, mostrar sólo las que se validan solas
  marcando *"análisis parcial"*, retener las inválidas con su motivo y no presentar el informe
  como utilizable si la conclusión global está comprometida.
- **B7** — consecuencias de la taquicardia por dobutamina en isquemia activa, sin penalización
  automática por cruzar un umbral.
- **B1** — el pin de versión de Python y las instrucciones exactas de despliegue, cuando me
  digas si la app de desarrollo existente ya apunta a `clinical-encounter-v0.13`. Eso no lo
  puedo comprobar yo: necesita tu cuenta.
- **B4, segunda parte** — el registro de llamadas, tokens, latencia y costo por componente y por
  encuentro, y la protección contra llamadas duplicadas por recargas o doble clic.
- **B9** — guardar la imagen generada y sus metadatos junto al caso y cargarla desde ahí durante
  el replay, sin habilitar la API.

**Nada de esto está desplegado.** Los cambios están en la rama del PR #1, que sigue sin
fusionar, y espero tu aprobación de esta versión antes de subir nada a la app pública.
