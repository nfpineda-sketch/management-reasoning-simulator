# Cinco familias nuevas — decisiones clínicas a resolver

> Preparado mientras trabajaba de noche, 2026-09-23. Cada decisión trae **una
> recomendación**, no una lista de opciones.
>
> **TODAS FIRMADAS por el docente el 2026-09-23.** Lo que sigue está aprobado.
> Tres decisiones cambiaron con la firma y ahora son mejores que mi propuesta —
> están marcadas **✍ CORREGIDA POR EL DOCENTE** y hay que leerlas, no
> hojearlas: 2.3 (E-FAST), 2.4 (hemotórax masivo) y 3.3 (hiperkalemia).

El banco actual tiene **21 casos en 8 familias**, todos con cobertura completa
de los cinco dominios y sin discrepancias. Todo lo nuevo tiene que entrar con el
mismo estándar: oportunidades declaradas que el caso realmente ofrece, eventos
críticos con ventana clínica, y `case_assessment.verify` sin discrepancias.

---

## Principios que arrastro de lo ya decidido

Los aplico sin volver a preguntarlos. Están aquí para que veas el criterio.

1. **La información disponible a la pregunta está disponible.** Un residente que
   no preguntó no fue privado del dato: omitió obtenerlo. Un evento crítico no se
   excusa por no haber preguntado (decisión 2026-09-23).
2. **El motor no hace lo que no puede hacer.** Una derivación se registra, su
   resultado no. Si el caso necesita que urología resuelva, lo que se evalúa es
   que el residente lo pida y diga qué vigila mientras tanto — no el resultado
   quirúrgico.
3. **Nada fabrica razonamiento que el residente no escribió.**
4. **Un evento crítico necesita ventana.** Sin ventana no se puede distinguir
   una omisión de una falta de oportunidad.
5. **Dos variantes por familia como mínimo**, una donde el manejo correcto es
   conservador y otra donde no. Si las dos se ven igual al llegar, mejor.
6. **La rúbrica no premia extensión ni vocabulario.** Un caso cuyo puntaje suba
   por escribir más está mal diseñado.

---

## Familia 1 · Cólico renal y pielonefritis obstructiva

La que pediste con dos variantes que se parecen al llegar. Es la mejor de las
cinco para empezar: fisiológicamente es sepsis con foco, que el motor ya sabe
hacer (`pneumonia`), y la decisión que la define es limpia y medible.

**Lo que la hace valiosa:** las dos variantes llegan con dolor lumbar cólico y
la ecografía muestra **dilatación pielocalicial unilateral en ambas**. La
ecografía no decide. Lo que decide es la fiebre, el aspecto de la orina, la
taquicardia, el lactato y la perfusión — y preguntar por ellos.

### Decisión 1.1 — Qué separa las dos variantes ⚠ REQUIERE TU FIRMA

Propongo que la diferencia **no** sea un solo valor sino un conjunto coherente:

| | `renal_colic_34m` (no complicado) | `obstructive_pyelonephritis_58f` |
|---|---|---|
| Temperatura | 36,8 | 38,9 |
| FC / PA | 96 · 138/82 | 122 · 92/54 |
| Llene capilar | 2 s | 4 s |
| Orina | clara | turbia, nitritos y leucocitos positivos |
| Lactato | 1,4 | 4,2 |
| Ecografía | dilatación pielocalicial derecha leve | dilatación pielocalicial izquierda moderada |
| Manejo correcto | analgesia, antiemético, alta con control y criterios de reconsulta | cultivos, antibiótico, volumen, **urología para descompresión** |

**Por qué así:** si la única diferencia fuera la fiebre, el caso enseñaría a
buscar un número. Con un conjunto, enseña a construir una explicación.

### Decisión 1.2 — El evento crítico de la variante séptica

Propongo **tres** eventos definidos:

- `pyelo_no_antibiotic` — no se administra antibiótico en una obstrucción
  infectada reconocida. Ventana (0, 60). Dominio D3.
- `pyelo_no_source_control` — **el importante**: no se involucra a urología ni se
  pide descompresión en una pielonefritis obstructiva con signos de sepsis.
  Ventana (0, 90). Dominios D3 y D5. Alternativas aceptables: nombrar la
  derivación como "urología" o como "nefrostomía/catéter doble J"; declarar el
  traslado a un centro con urología como la vía de resolución.
- `pyelo_unsafe_discharge` — se decide alta o manejo ambulatorio con fiebre,
  taquicardia o hipotensión presentes. Ventana (0, 180). Dominios D1 y D5.

Y en la variante no complicada, un evento de **acción peligrosa**, que es el
espejo:

- `colic_unnecessary_admission` — **no** lo propongo como evento. Hospitalizar
  de más es un error de eficiencia, no de seguridad, y esta rúbrica penaliza
  daño. Se mide en D5 como calidad de la continuidad, no como evento.

### Decisión 1.3 — Analgesia ⚠ REQUIERE TU FIRMA

El motor tiene `analgesia.py` y opioides. Para cólico renal el AINE es el
tratamiento de elección. Propongo agregar **ketorolaco IV** y **diclofenaco IM**
como órdenes ejecutables, con efecto sobre el dolor y ninguno sobre la
obstrucción. Pregunta abierta: ¿quieres que el AINE en la variante séptica con
creatinina elevada tenga alguna consecuencia, o se registra sin castigo
fisiológico? **Mi recomendación: sin consecuencia fisiológica.** El motor no
modela nefrotoxicidad aguda y fingirla sería inventar.

---

## Familia 2 · Trauma con xABCDE (ATLS 11)

La más grande de las cinco y la que más motor nuevo necesita. La dejo para el
final por eso, no por importancia.

### Decisión 2.1 — Alcance ⚠ REQUIERE TU FIRMA

Pediste un inestable por hemotórax, otro por fractura inestable de pelvis, otro
por hemorragia externa exanguinante, o combinaciones. Eso son tres fisiologías
distintas más la posibilidad de combinarlas.

**Mi recomendación: tres variantes, una por mecanismo, sin combinarlas al
principio.** Un caso combinado es mejor enseñanza pero hace imposible atribuir
una omisión: si el paciente muere, ¿fue por no poner el torniquete o por no
drenar el tórax? La rúbrica necesita poder decir cuál. Las combinaciones son la
segunda tanda, cuando cada mecanismo esté medido por separado.

### Decisión 2.2 — La **x** de xABCDE

La versión 11 antepone el control de hemorragia exanguinante. Eso tiene una
consecuencia de diseño fuerte: **en la variante de hemorragia externa, el orden
importa y el motor tiene que castigarlo**. Un residente que intuba antes de
poner el torniquete pierde volumen durante la intubación.

Propongo que el motor lo modele como pérdida continua hasta que se ejecute el
control (torniquete, compresión directa, empaquetamiento), y que el evento sea:

- `trauma_no_hemorrhage_control` — ventana (0, 10), dominios D1 y D3. Diez
  minutos porque es lo que la x significa.

### Decisión 2.3 — Órdenes nuevas que el motor necesita

Torniquete · compresión directa · empaquetamiento · faja pélvica · toracostomía
con dedo y con tubo · transfusión masiva · **ácido tranexámico** · inmovilización
cervical · ecografía FAST · pelvis y tórax AP.

De éstas, la **FAST** merece una decisión propia: ya existe `pocus`. Propuse que
FAST **fuera** el POCUS del caso de trauma, con los cuatro espacios.

### ✍ CORREGIDA POR EL DOCENTE — el E-FAST son cinco ventanas, no cuatro

El protocolo, tal como lo escribió el docente:

| Ventana | Qué busca |
|---|---|
| **1 · Cuadrante superior derecho** | líquido libre en el espacio de Morrison (hepatorrenal), el subdiafragmático y el receso pleural |
| **2 · Cuadrante superior izquierdo** | líquido libre en el espacio esplenorrenal, el subdiafragmático y el receso pleural |
| **3 · Suprapúbica**, longitudinal y transversal | líquido libre entre vejiga y colon; en mujeres, el fondo de saco de Douglas |
| **4 · Subxifoidea** | líquido libre en el pericardio |
| **5 · Pulmonar** | presencia de *lung sliding*; en modo M el signo de la playa, en modo B las colas de cometa. **Su presencia excluye el neumotórax** |

Y una regla de orden que es evaluable por sí sola:

> **En trauma abierto o penetrante se hacen primero las ventanas cardíacas.**

Esto cambia el diseño: el E-FAST es un estudio propio con cinco secciones (no el
POCUS de siempre), cada caso las reporta todas —incluidas las normales, como
hace el resto del banco—, y el **orden** en el trauma penetrante es una
oportunidad declarada en D1, no una preferencia.

### Decisión 2.4 — ✍ CORREGIDA POR EL DOCENTE

Propuse un umbral de 1200 mL drenados. **El docente lo reemplazó por algo
mejor**, y hay que implementar esto en vez de un número:

> El hemotórax masivo se define hoy no sólo por el volumen sino **también por la
> inestabilidad hemodinámica, independiente del volumen inicial que se drene**.
> Si se drena y sigue inestable, se debe volver a buscar un sitio de sangrado —
> intraabdominal, pelvis por ejemplo. Si se ha descartado otro sitio y sigue
> hipotenso y mal perfundido **con el tubo pleural instalado, debe ir a
> pabellón**.

Esto es mejor que un umbral porque convierte el caso en una **secuencia
evaluable** en vez de en un número que se lee:

1. drenar → ¿se estabilizó?
2. si no → **volver a buscar**: abdomen y pelvis, que es donde el E-FAST y la
   radiografía de pelvis vuelven a servir;
3. si no hay otro sitio y sigue inestable con el tubo puesto → **pabellón**.

El evento crítico ya no es «no drenó». Es **«drenó, siguió inestable, y no
volvió a buscar»**, que es el error real y el que la rúbrica puede sostener.

---

## Familia 3 · Bradicardia inestable

Fisiológicamente la más limpia después del cólico. Cuatro variantes por causa,
como pediste, y la causa **no se ve en el monitor**: se pregunta.

### Decisión 3.1 — Las cuatro variantes y su antídoto

| Variante | Lo que la revela | Tratamiento que la separa |
|---|---|---|
| `bradycardia_bb_50m` (betabloqueo) | historia de fármacos, PA baja con FC fija que no responde a atropina | **glucagón**, e insulina en dosis alta con dextrosa |
| `bradycardia_ccb_71f` (antagonistas del calcio) | historia de fármacos, hiperglicemia | **calcio** IV, insulina en dosis alta |
| `bradycardia_hyperk_63m` (hiperkalemia grave) | ERC o diálisis perdida, ECG con T picudas y QRS ancho | **calcio**, insulina-dextrosa, salbutamol, diálisis |
| `bradycardia_avb3_78f` (BAV completo) | ECG con disociación AV | **marcapasos** transcutáneo y transvenoso |

Y la quinta ya existe: el **SCA inferior** con bradicardia, que reusa `acs`.

### Decisión 3.2 — Atropina como discriminador

Propongo que la atropina **funcione parcialmente y de forma transitoria** en BAV
de nodo AV y **no funcione** en BAV completo infranodal ni en intoxicación por
betabloqueo o calcioantagonista. Eso convierte la respuesta a la atropina en
información diagnóstica, que es exactamente lo que es en la sala.

**Evento crítico compartido:**
- `bradycardia_no_support` — bradicardia con hipotensión o compromiso de
  conciencia y no se ejecuta ninguna medida de soporte de frecuencia (atropina,
  marcapasos, catecolamina) en (0, 20). Dominios D1 y D3.

### Decisión 3.3 — La hiperkalemia ⚠ REQUIERE TU FIRMA

La variante de hiperkalemia es la única donde **no dar calcio es letal en
minutos**. Propongo un segundo evento crítico:

- `hyperk_no_membrane_stabilisation` — potasio informado ≥ 6,5 con QRS ancho y
  no se ejecuta calcio en (0, 15). Dominios D1 y D3.

### ✍ PRECISADA POR EL DOCENTE

Confirmado que hay que pedirlo, y con dos precisiones que cambian el caso:

> Que el ECG lo sugiera: **mientras más enfermo el paciente, más lenta la
> frecuencia y más ancho el QRS**. Debe sospechar y actuar **incluso antes de
> tener el resultado**. El gluconato de calcio debe administrarse **apenas
> exista la sospecha clínica**.

Dos consecuencias de diseño:

- El ECG tiene que **graduarse con la gravedad**, no ser un dibujo fijo: la
  anchura del QRS y la frecuencia se mueven juntas con el potasio. Eso es
  fisiología nueva en `ecg12`, y es la que hace que el caso se pueda leer.
- El evento crítico **no es no dar calcio tras el resultado**. Es **no darlo
  ante la sospecha**, con la ventana corriendo desde el ECG y no desde el
  laboratorio. Un residente que espera el potasio para tratar ya llegó tarde, y
  la declaración tiene que decir eso.

---

## Familia 4 · Toxicología

### Decisión 4.1 — Cuáles ⚠ REQUIERE TU FIRMA

`opioid` ya existe. Propongo cuatro que no se solapan y que cubren mecanismos
distintos:

| Variante | Por qué ésta |
|---|---|
| `tox_tca_26f` (antidepresivos tricíclicos) | QRS ancho → **bicarbonato**; el ECG es el que decide, no el nivel |
| `tox_paracetamol_31m` | la ventana temporal y el nomograma; **N-acetilcisteína** temprana en un paciente que se ve bien |
| `tox_organophosphate_44m` | síndrome colinérgico; **atropina hasta secar secreciones**, no hasta la frecuencia |
| `tox_salicylate_67f` | alcalosis respiratoria con acidosis metabólica; **no intubar sin plan**, que es la trampa clásica |

La cuarta es la más difícil de modelar bien. Si hay que sacrificar una, es ésa.

### ✍ AMPLIADA POR EL DOCENTE

Agregar **alcohol, cocaína y benzodiacepinas**. Con eso la familia queda en
siete, y las tres nuevas cubren lo que más entra por la puerta:

| Variante | Por qué ésta |
|---|---|
| `tox_alcohol_*` | el diagnóstico que oculta otro: el traumatismo, la hipoglicemia y la abstinencia viven debajo |
| `tox_cocaine_*` | la simpaticomimética; el betabloqueo es la trampa clásica y el diazepam es el tratamiento |
| `tox_benzodiazepine_*` | depresión respiratoria sin miosis; **el flumazenil es la trampa**, no el antídoto |

Siete variantes es más de lo que una familia del banco ha tenido nunca (el
máximo son las seis coronarias). Propongo entregarlas en dos tandas: primero
TCA, paracetamol y benzodiacepinas —las tres donde el error de manejo es más
nítido— y después organofosforado, salicilato, alcohol y cocaína.

### Decisión 4.2 — El paciente que se ve bien

`tox_paracetamol_31m` es el caso donde **todas las observables son normales** y
la decisión correcta depende de la historia y del tiempo transcurrido. Eso rompe
un supuesto del motor: hasta ahora todo caso llega con algo anormal en el
monitor.

**Mi recomendación: hacerlo igual.** Es el caso más valioso de los cuatro
precisamente por eso, y la rúbrica ya sabe distinguir una omisión de una falta
de oportunidad. Pero necesita que D1 declare la oportunidad de otra forma: la
gravedad no está en el monitor, está en la anamnesis.

---

## Familia 5 · La que elijo yo: anafilaxia

De las que faltan, ésta es la que más peso tiene en urgencias y la que mejor
encaja con lo ya construido.

**Tres razones concretas:**

1. **Cierra un hueco que ya medimos.** El 2026-09-23, midiendo la jugabilidad,
   `adrenalina 0,5 mg IM` se devolvió como orden no reconocida: la vía
   intramuscular no es una intervención que este motor administre. La familia
   que la necesita es ésta.
2. **La fisiología se reusa.** Broncoespasmo (`asthma`) más shock distributivo
   (`pneumonia`, `gi_bleed`). Poco motor nuevo para mucho caso.
3. **El evento crítico es el más nítido del banco.** No dar adrenalina, o darla
   tarde, o tratar con antihistamínico y corticoide solamente. Es la omisión más
   estudiada de la urgencia y la más fácil de defender ante un docente.

Y la **reacción bifásica** da, sin forzar nada, el challenge de cierre prematuro
(`R1-06`) que ya existe: el paciente mejora, el residente lo da de alta, y
vuelve.

### Decisión 5.1 — Variantes

| Variante | Lo que enseña |
|---|---|
| `anaphylaxis_29f` | adrenalina IM temprana; la vía y el sitio importan |
| `anaphylaxis_63m_betablocked` | **refractaria a la adrenalina** por betabloqueo — glucagón; y la trampa de subir la adrenalina sin preguntar por los fármacos |

### Decisión 5.2 — Eventos críticos

- `anaphylaxis_no_epinephrine` — anafilaxia reconocida y no se ejecuta
  adrenalina en (0, 15). Dominios D1 y D3.
- `anaphylaxis_antihistamine_only` — se tratan la urticaria y el broncoespasmo
  con antihistamínico, corticoide o broncodilatador **sin** adrenalina en la
  ventana. Acción peligrosa, dominio D3.
- `anaphylaxis_unsafe_discharge` — alta antes de la ventana de observación con
  la reacción bifásica documentada como riesgo. Dominios D1 y D5.

### Decisión 5.3 — La vía intramuscular ⚠ REQUIERE TU FIRMA

Para esto el motor necesita administrar **IM** de verdad, no sólo aceptarla como
palabra. Eso implica un retraso de absorción distinto al IV.

**Mi recomendación: modelarlo.** Un inicio a los 3–5 minutos frente a los 30–60
segundos del IV es clínicamente la diferencia entre las dos vías y es lo que
hace que "la vía importa" sea algo que el residente puede observar en vez de que
se lo digan. Necesito tu visto bueno porque es fisiología nueva.

---

## Lo que voy a hacer mientras no contestes

Por orden, y cada una entra completa o no entra:

1. **Anafilaxia** — cierra un hueco medido, reusa fisiología, evento nítido.
2. **Cólico renal / pielonefritis obstructiva** — dos variantes, sepsis con foco.
3. **Bradicardia** — cuatro variantes, la causa se pregunta.
4. **Toxicología** — empezando por TCA y paracetamol.
5. **Trauma** — la más grande; probablemente no alcance esta noche.

Donde una decisión marcada ⚠ bloquee, tomo la recomendación que escribí aquí,
la implemento así, y lo dejo anotado en el caso para que se pueda cambiar sin
rehacer nada.

---

## Estado tras la firma (2026-09-23)

| Familia | Estado |
|---|---|
| **Anafilaxia** | entregada, 2 variantes |
| **Cólico renal** | entregada, 2 variantes |
| **Bradicardia** | 2 de 4 variantes entregadas; faltan betabloqueo e hiperkalemia |
| **Toxicología** | diseñada, 7 variantes, no implementada |
| **Trauma** | diseñada con el E-FAST y la secuencia del hemotórax, no implementada |
