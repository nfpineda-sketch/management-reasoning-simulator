# Cinco familias nuevas — decisiones clínicas a resolver

> Preparado mientras trabajaba de noche, 2026-09-23. Cada decisión trae **una
> recomendación**, no una lista de opciones: lo que sigue es lo que voy a
> implementar salvo que digas otra cosa. Las marcadas **⚠ REQUIERE TU FIRMA**
> son las que no puedo resolver desde lo ya decidido históricamente.

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

De éstas, la **FAST** merece una decisión propia: ya existe `pocus`. Propongo
que FAST **sea** el POCUS del caso de trauma, con los cuatro espacios, en vez de
un estudio nuevo. Menos código y clínicamente honesto.

### Decisión 2.4 — Qué pasa cuando el residente hace lo correcto ⚠ REQUIERE TU FIRMA

En hemotórax masivo, drenar da un retorno inmediato de sangre. ¿Cuánto? Propongo
**1200 mL iniciales** en el caso masivo, que es el umbral clásico de
toracotomía, y que el motor entonces **abra una segunda decisión**: seguir
reanimando o pedir cirugía. Ése es el momento educativo del caso. Necesito que
confirmes el umbral o me des el que uses.

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

Pregunta: ¿quieres que el potasio esté en los `basic_labs` de llegada, o que
haya que pedirlo? **Mi recomendación: que haya que pedirlo**, y que el ECG lo
sugiera. Si llega en la bandeja, el caso enseña a leer un número, no a
sospechar.

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
