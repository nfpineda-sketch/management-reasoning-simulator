# Revisión completa del banco — 21 variantes jugadas en español

> Resultado de jugar las 21 variantes del banco de punta a punta el 2026-09-21, escribiendo
> como escribe un residente chileno.
>
> - **La sección A son decisiones tuyas y no está implementada.** Dieciocho preguntas, cada
>   una con lo que vi y las opciones que se me ocurren. No toqué nada de eso.
> - **La sección B son defectos del idioma y del manejo de órdenes, sin criterio clínico de por
>   medio.** Están arreglados en el árbol de trabajo **y no commiteados**, con pruebas nuevas.
>   Nada de fisiología cambió. Si te parecen bien, los commiteo; si no, se revierten enteros.

## Estado de las decisiones (2026-09-21)

| # | Decisión | Estado |
|---|---|---|
| 1 | Alta con consecuencia | **implementada** |
| 2 | Unidad coronaria | **implementada** |
| 5 | Atropina y marcapasos transcutáneo | **implementada** · `docs/DECISIONES_5_6_10_MAGNITUDES.md` |
| 6 | Dobutamina en el banco | **implementada** · mismo documento |
| 10 | Morfina | **implementada** · mismo documento |
| 15 | Vocabulario de laboratorio | **implementada** (primer tramo: sinónimos; los paneles por analito siguen pendientes) |
| B1–B8 | Defectos de lenguaje y de órdenes | **arreglados** |
| 7 | Derivadas derechas y posteriores | **implementada** · `docs/DECISIONES_7_9_MAGNITUDES.md` |
| 9 | Trabajo respiratorio en todas las familias | **implementada** · mismo documento |
| 3, 3b, 4, 8 | Magnitudes: techo, opioide corto, volumen en VD, vía perdida | **implementadas** · `docs/DECISIONES_3_4_8_MAGNITUDES.md` |
| 11 | Inducción, bloqueo neuromuscular y sedación en infusión | **implementada** · `docs/DECISIONES_11_A_14_MAGNITUDES.md` |
| 12 | Diuresis medible | **implementada** · mismo documento |
| 13 | Órdenes de enfermería y soporte | **implementada** · mismo documento |
| 14 | Analgésicos y antipiréticos | **implementada** · mismo documento |
| 16 | Idioma de presentación | **primera etapa implementada** · `docs/DECISION_16_IDIOMA.md` |
| 17 | Caso generado por IA | bloqueada: falta la clave del proveedor |

## Qué se jugó

Las ocho familias, las 21 variantes, forzando cada caso con una semilla fija:

| Familia | Variantes | Desafío usado |
|---|---|---|
| Neumonía | 46f, 83m | R2-03 |
| Edema pulmonar | 58m, 75f | R3-01 |
| Asma | 24f, 49m | R3-01 |
| SCA | inferior 54m, NSTEMI 66f, posterior 61m, de Winter 52m, Wellens 48m, tronco 70f | R2-02 |
| TEP | 33f, 61m | R2-03 |
| Hemorragia digestiva | 57m, 72f | R2-05 |
| Hipoglicemia | 28m, 76f, 54m tiamina | R1-06 |
| Opioides | 35m, 67f | R1-06 |

Lo que **no** se ha jugado nunca: el caso generado por IA. Requiere una corrida pagada y no
está autorizada (ver decisión 17).

## Lo que funciona bien (para no tocarlo)

- **La recurrencia de la glimepirida** en la 76f: 129 → 111 → 93 → 75 → 57 → 39 → 21 mg/dL,
  con el estado mental bajando detrás. Es el mejor caso del banco.
- **El Wernicke del 54m**: glucosa sola deja "Confused" con el mensaje explícito, y no mejora
  sola por más que se espere. La tiamina lo resuelve.
- **El TEP**: trombolisis sin hipotensión sostenida → hemorragia del sitio quirúrgico y
  deterioro; con hipotensión sostenida → la obstrucción cae y la perfusión mejora. Impecable.
- **El paro del opioide**: veinte minutos de apnea sin ventilar y el paciente se detiene, con
  el mensaje que dice que faltaba la ventilación, no el antídoto.
- **de Winter, Wellens y NSTEMI** dan tres respuestas distintas y correctas al activar hemodinamia.
- **El bloqueo AV completo del infarto inferior** aparece a los 45 minutos, solo.
- **La hemorragia digestiva** completa: transfusión, IBP, endoscopía a la hora, y el paciente
  queda mejor que al llegar.

---

# A · Decisiones clínicas y docentes

## 1. Dar de alta no existe

"Dale de alta con indicaciones", "alta a domicilio", "dar de alta con control en 24 horas":
ninguna se reconoce. Lo único que existe es hospitalizar/trasladar a **UCI, intermedio o sala**.

En R1-06 —el desafío que pregunta *si el problema quedó resuelto*— decidir el destino **es** la
conducta final, y el residente no la puede escribir. En el opioide de acción corta, "observar
y dar de alta" es la respuesta correcta y es inexpresable.

- **Opción A**: agregar `alta` como destino, sin consecuencia (queda registrado y se evalúa en la revisión).
- **Opción B**: agregar `alta` **con** consecuencia: si el paciente todavía tiene opioide activo
  o hipoglicemiante de vida media larga, el alta precipita el evento que el caso enseña.
- **Opción C**: dejarlo fuera y decir explícitamente que este simulador termina en la decisión de ingreso.

## 2. "Unidad coronaria" no es un destino

"Hospitaliza en la unidad coronaria" y "traslada a la unidad de cuidados coronarios" piden
aclaración. "UCI coronaria" sí funciona (cae en UCI). ¿Agregamos UCO como sinónimo de UCI, o
como un destino propio?

## 3. El techo de la recuperación: ¿puede quedar mejor que al llegar?

Hoy hay dos reglas distintas según la familia:

- **SCA**: al reperfundir, la presión y el llene vuelven **exactamente al estado de llegada** y
  ahí se detienen. La 70f de tronco termina en 104/66 con llene 3 s y FC 112, igual que cuando
  entró, para siempre.
- **Hemorragia digestiva**: el paciente termina en 132/81 con llene 2 s, **mejor** que sus 98/62 de llegada.

¿Debe un paciente cuya causa se resolvió poder quedar mejor que al llegar? Yo lo preguntaría
así: el infartado reperfundido a las cuatro horas, ¿está como cuando llegó, o está mejor?

## 3b. El opioide corto nunca termina de despertar

Con la revisión de magnitudes del 2026-09-21 (vida media de cuatro horas), el 35m ventilado y
revertido queda así, medido en el motor:

| Tiempo | Opioide | Estado |
|---|---|---|
| 70 min | 0.82 | obnubilado |
| 190 min | 0.58 | obnubilado |
| 250 min | 0.49 | **somnoliento** |
| 490 min | 0.24 | somnoliento |

A las ocho horas sigue somnoliento. Nunca vuelve a estar alerta dentro de un turno, así que
"observar y dar de alta" —la conducta correcta del comprimido de acción corta— no es
alcanzable ni aunque exista la orden de alta (decisión 1). Es el mismo pendiente que te dejé
anotado: la absorción no está modelada, solo la eliminación. ¿Acortamos más la vida media,
modelamos la curva de subida y bajada, o aceptamos que el caso termina con el paciente
somnoliento y vigilado?

## 4. Volumen en el infarto de ventrículo derecho

En el 54m inferior con compromiso de VD e hipotensión, 500 mL de suero fisiológico **no hacen
nada**. El cristaloide en la familia SCA solo rescata la caída provocada por nitroglicerina;
sin nitro, el volumen no tiene efecto.

Es el gesto de manual en el infarto de VD. ¿Debe el VD precargo-dependiente responder al
volumen aunque no haya nitratos de por medio?

## 5. Bloqueo AV completo sin tratamiento

El bloqueo aparece a los 45 minutos y la presión cae con él (92/60 → 87/57, llene 4.2 s).
El residente no tiene nada que ofrecer: **atropina no existe** y **marcapasos transcutáneo
tampoco**. ¿Los agregamos? ¿Con qué efecto — atropina inútil en el bloqueo nodal por infarto
(que es la enseñanza), marcapasos que sí sube la frecuencia?

## 6. Dobutamina en el shock cardiogénico del banco

En la 70f de tronco, "inicia dobutamina a 5 mcg/kg/min" responde:
*"This intervention requires a generated encounter with an explicit response rule."*
Es la decisión de inótropo clásica del shock cardiogénico, y además el mensaje es
incomprensible para un residente. ¿La implementamos en la familia SCA, o damos una negativa
clínica ("este encuentro no modela inótropos")?

## 7. Derivadas derechas y posteriores

"Pide un electrocardiograma con derivadas derechas" entrega **un ECG de 12 estándar**, sin
avisar. "Pide derivaciones posteriores V7 V8 V9" no se reconoce.

Son el examen específico de dos de las seis variantes de SCA (inferior con VD, posterior).
El residente que hace lo correcto recibe lo mismo que el que no lo hace.

## 8. La tiamina revierte el Wernicke de golpe

Confundido → Alerta dentro del mismo paso, y si se da junto con la glucosa el paciente nunca
se confunde. Clínicamente la encefalopatía mejora en horas o días. ¿La dejamos instantánea
(el punto docente es "faltaba la tiamina") o la hacemos gradual/parcial?

## 9. El trabajo respiratorio solo es proporcional en la neumonía

La decisión 5 del 2026-09-21 (seis niveles por unidad de pulmón) se aplicó únicamente a la
neumonía. En el TEP 61m, después de trombolizar, la frecuencia baja de 32 a 29, la saturación
sube a 95 y el trabajo respiratorio sigue diciendo **"Markedly increased"**, la palabra con que
el caso fue escrito. Lo mismo en el asma cuando empeora. ¿Extendemos la regla proporcional al
TEP y a las demás familias que no escriben la suya?

## 10. Morfina no existe

"Indica morfina 3 mg IV" no se reconoce en ninguna familia. En el SCA es una conducta estándar
—y discutible, que es lo interesante—. ¿La agregamos? ¿Con qué efecto: analgesia sin efecto
hemodinámico, o con la caída de precarga que importa en el infarto de VD?

## 11. Drogas de intubación

La sedación **sí** funciona y funciona bien: en el asma 49m intubado, "sédalo con midazolam
5 mg IV" lo pasa de *Awake and fighting the ventilator* a *Sedated*, la disincronía desaparece
y el auto-PEEP baja de 1.4 a 0.6. Lo que no existe es lo que viene después:

- **Relajante neuromuscular**: "administra rocuronio 1 mg/kg IV" no se reconoce. En el asma casi
  fatal con presiones altas es la conducta siguiente.
- **Sedación en infusión**: "inicia propofol a 2 mg/kg/h" responde que la orden usa unidades de
  peso o de infusión y pide una dosis fija.
- **Drogas de inducción** en la intubación: "intubación de secuencia rápida con ketamina
  2 mg/kg y rocuronio 1.2 mg/kg" intuba, y deja "rocuronio 1.2 mg/kg" colgado.

¿Modelamos relajación e infusión de sedación, o declaramos que la vía aérea es una sola acción
y que el residente no debe escribir las drogas?

## 12. La furosemida no muestra nada

Está modelada (efecto sobre el pulmón a los 30 minutos, casi nulo mientras el edema no cede),
pero en el registro **no pasa absolutamente nada**: ni diuresis, ni volumen urinario, ni una
línea. El residente no puede saber si su orden hizo algo. ¿Agregamos diuresis horaria como
signo observable?

## 13. Órdenes de enfermería y soporte

Vía venosa periférica, monitorización, oximetría, régimen cero, sonda Foley, sonda
nasogástrica, "deriva a pabellón". Desaparecían en silencio; con el arreglo B2 ahora se citan
de vuelta y retienen el turno, que es lo correcto pero no necesariamente lo que quieres.

Decisión docente: ¿se aceptan como *registradas sin efecto fisiológico* (aparecen en el
registro y en la revisión y el turno sigue), o se siguen rechazando como fuera del simulador?
Son órdenes razonables que un residente escribe sin pensar, y hoy le cuestan el turno completo.

## 14. Analgesia y antipiréticos

Paracetamol y metamizol no existen. En la neumonía la fiebre no responde a nada por diseño.
¿Los agregamos como órdenes registradas sin efecto, o los dejamos fuera?

## 15. El vocabulario de laboratorio

"Función renal", "perfil bioquímico", "perfil hepático", "ELP", "exámenes generales",
"pruebas hepáticas", "BUN", "urea": **ninguno** se reconoce. Solo "hemograma", "electrolitos",
"creatinina", "laboratorio". Y "marcadores cardíacos" / "enzimas cardíacas" no son troponina.

Todos los casos tienen `basic_labs` disponible. ¿Los metemos todos en el mismo panel básico, o
prefieres que algunos exámenes existan por separado?

## 16. El idioma

El residente escribe en español; **el paciente responde en inglés**, la historia está en inglés,
los exámenes están en inglés y la revisión posterior también:
*"Your recorded expected effect was: suba la frecuencia."*

Es la decisión más grande de todas y no la he tocado nunca. ¿Se traduce la interfaz del
encuentro al español? ¿Solo las respuestas del paciente? ¿O se queda bilingüe a propósito?

## 17. El caso generado por IA

Es la única parte del simulador que nunca se ha jugado de punta a punta. Necesita una corrida
pagada. Si la autorizas, la acotaría a **una sola generación de un desafío**, sin imágenes, con
el registro guardado en disco para poder re-jugarlo después sin pagar (`MRS_REPLAY_CASE` ya
existe para eso). No la voy a ejecutar sin que lo digas explícitamente.

---

# B · Defectos sin decisión clínica

Esto no requiere criterio docente: son cosas que están mal. **Están arregladas en el árbol de
trabajo, con pruebas, y sin commitear**: `test_chilean_order_language.py` (25 pruebas) cubre
cada una. No toqué nada de fisiología. Si te parece bien, lo commiteo tal cual; si no, lo
reviertes con `git checkout .` y no se perdió nada.

## B1 · GRAVE · **arreglado** · una orden retenida se completaba con palabras de una orden nueva

Cuando un turno queda retenido pidiendo la vía o la dosis, el **texto completo del turno
siguiente** se lee como si fuera la respuesta a esa pregunta. Dos ejemplos reales de esta corrida:

- Hipoglicemia 76f: la orden retenida pedía la vía de la glucosa. El turno siguiente decía
  *"el hipoglicemiante **oral** dura horas debido a la insuficiencia renal"* — y el motor tomó
  la palabra "oral" y completó la orden como **vía PO**.
- Opioide 67f: la orden retenida era naloxona 0.04 mg sin vía. El turno siguiente pedía
  **naloxona 0.1 mg IV**. El motor completó la retenida como **0.04 mg IV** y descartó la dosis nueva.

**Arreglo**: una respuesta genuina a una pregunta retenida es un fragmento —"IV", "0.4 mg IV",
"naricera a 4 L/min"—. Un turno que declara una prioridad o pide una reevaluación no es una
respuesta: es una orden nueva, y ahora **reemplaza** a la retenida diciéndolo en el registro
("The held order was discarded to run this one: …"). Verificado jugando los dos casos.

## B2 · GRAVE · **arreglado** · órdenes que desaparecían sin una palabra

Estas frases producen **una lista de acciones vacía**: no se ejecutan, no se retienen, no se
mencionan. El registro solo dice "After 10 minutes…", como si el residente no hubiera escrito nada:

- `Instala un marcapasos transcutáneo a 70 por minuto.`
- `Instala VMNI con IPAP 14, EPAP 6 y FiO2 50%.`
- `Instala una vía venosa periférica gruesa.`
- `Monitoriza al paciente.` · `Instala monitor y oximetría de pulso.`
- `Deja régimen cero.` · `Deriva a pabellón.` · `Avisa a UCI para cama.`

La causa era la misma en todas: el verbo (**instalar, avisar, derivar, monitorizar**) no estaba
en la tabla de imperativos, y una frase sin verbo conocido y sin sustancia conocida se descarta.

**Arreglo**: los cinco verbos entraron a la tabla, y "deja **de** …" se lee como suspender
("deja de pasar el suero" detiene el cristaloide) mientras que "deja …" a secas es una indicación. Ahora `Instala naricera a 4 litros por
minuto` y `Instala VMNI con IPAP 14, EPAP 6 y FiO2 50%` **se ejecutan**, `Avisa a UCI para cama`
es una interconsulta, y el marcapasos, la vía venosa y "monitoriza al paciente" se **citan de
vuelta** en vez de desaparecer. Lo que esas tres deberían hacer de verdad es la decisión 13.

## B3 · **arreglado** · "endovenoso" no era una vía

Se aceptaban `iv`, `ev`, `intravenoso`. No `endovenoso/endovenosa`, que es la palabra estándar
en Chile, ni `e.v.` con puntos —que además partían la frase en tres, porque el punto separa
órdenes—. La orden quedaba retenida pidiendo la vía que ya estaba escrita.

## B4 · **arreglado** · "4 litros" no era un flujo

`4 L/min`, `4 lt/min`, `4 lpm` funcionaban. **`4 litros`** y **`4 litros por minuto`** no.

## B5 · **arreglado** · "volumen corriente 6 mL/kg" se convertía en un bolo de suero

En `Intuba con secuencia rápida y conecta en VC/AC con FiO2 100%, PEEP 5, volumen corriente
6 mL/kg y frecuencia 12`, el motor entendía: una intubación **sin parámetros** y un **bolo de
6 mL de cristaloide**. La segunda mitad se separaba de la intubación y se perdían los
parámetros, y el volumen corriente por kilo pasaba a ser volumen de fluido.

**Arreglo**: "y conecta / y conéctalo a ventilación mecánica en …" se lee como parte de la
misma orden de vía aérea. La frase de arriba ahora entrega una sola intubación con VC/AC,
FiO₂ 100%, PEEP 5, 6 mL/kg y frecuencia 12, y ningún bolo.

## B6 · **arreglado** · "bolsa-máscara" no, "bolsa-mascarilla" sí

`bolsa-mascarilla`, `ambú` y `bvm` funcionaban; `bolsa-máscara` y `bolsa de reanimación` no.
Es la primera maniobra en la apnea por opioides. Ahora se reconocen las cuatro.

## B7 · **arreglado** · "mascarilla de recirculación" entregaba la mascarilla equivocada

Se ejecutaba como **mascarilla simple a 15 L/min** en vez de mascarilla con reservorio, sin
avisar: no una aclaración, una ejecución equivocada. Ahora "de recirculación", "con reservorio"
y "máscara de reservorio" son el mismo dispositivo, y "máscara" a secas sigue siendo la simple.

## B8 · **arreglado** · el mismo panel pedido dos veces se duplicaba

"Pide electrolitos, función renal y hemograma" → **"Laboratory results + Laboratory results"**
más un fragmento no reconocido. Dos muestras tomadas en el mismo minuto son una muestra: ahora
colapsan. (Que "función renal" se reconozca o no sigue siendo la decisión 15.)

## B9 · Anotaciones menores, sin arreglar

- Cuando una orden no se reconoce, se cita de vuelta **en infinitivo canónico**: el residente
  escribió "Instala un marcapasos" y el mensaje dice *"colocar un marcapasos"*. Es de siempre,
  pero ahora se ve más porque hay más verbos mapeados. ¿Devolvemos el texto tal cual se escribió?
- "Monitoriza la presión **cada** 15 minutos" no se entiende; solo "reevalúa **en** 15 minutos".
  Una reevaluación repetida no existe como concepto. ¿Vale la pena?
- "Mascarilla de alto flujo" se rechaza como cánula de alto flujo. El mensaje es correcto, pero
  en Chile "mascarilla de alto flujo" suele significar Venturi o reservorio. ¿Sinónimo o se deja?
- "Mascarilla Venturi al 35%" pide un flujo en L/min; el Venturi se indica por porcentaje.

---

# C · Cómo seguir

Un orden posible, de más a menos rendimiento por hora de trabajo:

1. **Decisiones 1 y 2** (alta y destino): cierran el arco de R1-06 y son baratas.
2. **Decisión 15** (vocabulario de laboratorio): es una línea de sinónimos y desbloquea
   "buscar la causa", que es la conducta central de la hipoglicemia.
3. **Decisiones 5, 6 y 10** (atropina/marcapasos, dobutamina, morfina): el SCA es la familia
   con más variantes y la que se queda más corta de conductas.
4. **Decisión 7** (derivadas derechas y posteriores): es la única forma de premiar al residente
   que reconoce un infarto de VD o posterior.
5. **Decisión 9** (trabajo respiratorio proporcional en TEP y asma).
6. **Decisiones 3, 3b, 4, 8** (magnitudes: techo, opioide, volumen en VD, tiamina).
7. **Decisión 16** (idioma), que es la más grande y la que conviene pensar sin apuro.

# D · Cómo se reproduce cualquiera de estos hallazgos

Los guiones de esta corrida están en el scratchpad de la sesión. El banco se fuerza con una
semilla: `bank.Play("R1-06", "hypoglycemia_76f")` abre siempre esa paciente, sin pagar nada y
sin depender de qué caso salga al reiniciar el servidor. Eso también sirve para el futuro:
hasta ahora cada reinicio del servidor sorteaba la variante y había que jugar hasta que saliera
la que se quería revisar.
