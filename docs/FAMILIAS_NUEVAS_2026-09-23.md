# Cuatro familias nuevas: anafilaxia, cólico renal, bradicardia y trauma

> 2026-09-23. El banco pasa de **21 casos en 8 familias** a **31 casos en 12**,
> todos con cobertura completa de los cinco dominios y cero discrepancias.
> Las decisiones clínicas están en `FAMILIAS_NUEVAS_DECISIONES_2026-09-23.md`,
> **todas firmadas por el docente**, y tres de ellas corregidas por él de una
> forma que mejoró el diseño.

| | Antes | Después |
|---|---|---|
| Casos | 21 | **31** |
| Familias | 8 | **12** |
| Cobertura completa | 21 de 21 | **31 de 31** |
| Discrepancias | 0 | **0** |
| Eventos críticos definidos | 16 | **33** |

---

## Familia 1 · Anafilaxia

`anaphylaxis_29f` · `anaphylaxis_63m_betablocked`
Challenges: **R1-06** (cierre prematuro) y **R3-01** (elegir según la respuesta).

### Por qué ésta

La elegí yo, y por tres razones concretas:

1. **Cierra un hueco que ya habíamos medido.** El 2026-09-23, midiendo la
   jugabilidad, `adrenalina 0,5 mg IM` se devolvió como orden no reconocida: la
   vía intramuscular no era una intervención que este motor administrara. Ahora
   lo es.
2. **Reusa fisiología.** Broncoespasmo del asma más shock distributivo.
3. **El evento crítico es el más nítido del banco.** No dar adrenalina.

### Lo que enseña, y se puede ver

**La vía es visible.** El depósito intramuscular se absorbe a lo largo de
minutos. A los dos minutos de la dosis, la presión no se ha movido; a los cinco
empieza; a los quince es otra paciente. Medido:

```
adrenalina 0,5 mg IM en el muslo
  t= 2 min   84/46   ← sin cambio: el depósito no se ha absorbido
  t= 4 min   86/47
  t= 7 min   91/50
  t=17 min  101/56   Alert
```

Un residente que reevalúa a los dos minutos no ve nada, y **qué hace con eso**
es la decisión del caso.

**El corticoide no trata la reacción.** Se registra, se responde por él, y la
paciente sigue deteriorándose. No es un castigo: es la razón por la que ésta es
la omisión más estudiada de la especialidad.

**Sin tratamiento hay un desenlace.** A los 25 minutos el motor declara el paro
y dice por qué: *«Adrenaline was the treatment that was missing; nothing else
that was given acts on the reaction.»* La presión a esa altura es 55/30 — el
número hace legible el evento.

**Refractario es una pregunta, no una dosis.** En el betabloqueado la adrenalina
hace un tercio de lo que debería, y repetirla no cierra la brecha. El glucagón
sí. Y el dato que lo explica está en la lista de medicamentos, que la esposa
trajo.

**La frecuencia que no sube es el hallazgo.** El paciente betabloqueado llega en
shock con 64 de frecuencia y se mantiene ahí. Un receptor bloqueado tampoco
monta la taquicardia.

### Decisiones tomadas

- **Piel enrojecida.** El vocabulario visual sólo tenía natural / palidez leve /
  palidez. Un shock distributivo es caliente y rojo, y una ilustración con
  palidez contradiría el examen que el mismo caso escribe. Agregué `flushed` y
  un perfil `distributive_visual_profile`, con la prueba que nombra la excepción.
- **La vía IM se modela de verdad** (decisión 5.3 del documento): inicio a los
  3–5 minutos frente a los segundos del IV. Sin eso, «la vía importa» sería algo
  que se le dice al residente en vez de algo que observa.

---

## Familia 2 · Cólico renal y pielonefritis obstructiva

`renal_colic_34m` · `obstructive_pyelonephritis_58f`
Challenge: **R2-05** (explicar lo que queda después del primer hallazgo).

### Lo que enseña

**Las dos llegan con dolor lumbar cólico y las dos tienen dilatación
pielocalicial en la ecografía.** El estudio no decide. Deciden la temperatura,
la orina, la perfusión, el lactato — y preguntar.

| | `renal_colic_34m` | `obstructive_pyelonephritis_58f` |
|---|---|---|
| Temperatura | 36,8 | 38,9 |
| FC / PA | 94 · 142/84 | 118 · 94/54 |
| Llene capilar | 2 s | 4 s |
| Orina | sangre +++, sin nitritos | esterasa +++, nitritos positivos |
| Lactato | 1,4 | 4,2 |
| Ecografía | dilatación derecha leve, cálculo de 5 mm | dilatación izquierda moderada, cálculo de 9 mm |

**Un antibiótico no drena un riñón obstruido.** El motor no descomprime nada —
una derivación se registra, nunca su resultado — así que el tratamiento **frena
el curso y no lo da vuelta**. Medido:

```
sólo ceftriaxona     t=15  92/53 FC 119  →  t=135  82/47 FC 125
con volumen          t=30  98/56 FC 116  →  t=135  90/52 FC 120
```

El volumen compra presión y la devuelve. Ésa es la lección: el foco sigue detrás
del cálculo, y lo que falta es **quién lo descomprime**.

### Decisiones tomadas

- **La ecografía renal es un estudio propio**, no una ventana del protocolo
  POCUS. Intenté agregar la ventana renal al protocolo y el radio de cambio era
  demasiado grande (23 casos, el esquema de generación, dos análisis docentes).
  El patrón establecido para un estudio de una familia es el de la
  angiotomografía en embolia, y lo seguí.
- **El AINE no tiene consecuencia fisiológica** (decisión 1.3): el motor no
  modela nefrotoxicidad aguda y fingirla sería inventar. El ketorolaco baja el
  dolor y no toca nada más.
- **Hospitalizar de más no es evento crítico.** Esta rúbrica penaliza daño, no
  ineficiencia. Se mide en D5 como calidad de la continuidad.

---

## Familia 3 · Bradicardia inestable

`bradycardia_ccb_68m` · `bradycardia_avb3_78f`
Challenge: **R2-04** (reconocer enfermedad fuera del patrón habitual).

### Lo que enseña

**El monitor dice la frecuencia y no dice qué se la llevó.** Las dos llegan
lentas y mal perfundidas. Ninguna responde a la atropina, y lo que las trata es
distinto.

```
intoxicación por bloqueador de calcio        bloqueo AV completo
  llegada   74/44 FC 38  glucosa 214          llegada   78/46 FC 32  BAV completo
  atropina  74/44 FC 38  ← nada               atropina  78/46 FC 32  ← nada
  atropina  74/44 FC 38  ← nada               calcio    78/46 FC 32  ← nada
  calcio   121/70 FC 64  Alert                MP 50 mA  78/46 FC 32  espigas sin captura
  glucagón 122/70 FC 65                       MP 90 mA 112/65 FC 70  captura confirmada
  +15 min  106/62 FC 56  ← el antídoto cede
```

Tres cosas quedan separadas y observables:

- **La atropina no es el tratamiento de una bradicardia cuyo bloqueo está bajo
  el nodo**, ni de un canal de calcio bloqueado. En ambos casos no hace nada, y
  eso es información diagnóstica.
- **Elegir una frecuencia no es marcapasear.** A 50 mA hay espigas sin complejo
  y la frecuencia sigue en 32; el ritmo lo dice. A 90 mA captura. El residente
  tiene que confirmar pulso y presión, no una traza.
- **El antídoto cede.** El calcio compra 26 latidos y 47 mmHg, y a los 30 minutos
  ya devolvió parte. El caso es sobre pedir la ayuda que este motor no da.

**La glicemia es la pista** y está en uno solo de los dos: 214 en el
envenenamiento, 104 en el bloqueo. Ninguno tiene un potasio que explique la
frecuencia.

### Las cuatro variantes

Tras la firma se completaron las cuatro que pediste:

| Variante | Lo que la revela | Lo que la trata |
|---|---|---|
| `bradycardia_ccb_68m` | glicemia 214 sin diabetes; el verapamilo que duplicó | **calcio** |
| `bradycardia_bb_54f` | el blíster vacío de propranolol que trajo la pareja | **glucagón** |
| `bradycardia_avb3_78f` | disociación AV en el ECG, ondas cañón | **marcapasos** |
| `bradycardia_hyperk_63m` | QRS ancho que se ensancha con la bradicardia | **calcio ante la sospecha** |

El calcio y el glucagón están en los dos envenenamientos con los tamaños
invertidos: el que responde en uno apenas responde en el otro, y eso es el
diagnóstico diferencial completo.

### La hiperkalemia, como la precisaste

> «Mientras más enfermo el paciente, más lenta la FC y más ancho el QRS… debe
> sospechar y hacer incluso antes de tener el resultado. El gluconato de calcio
> debe administrarse apenas exista la sospecha clínica.»

Implementado literalmente. El ancho del QRS y la frecuencia **se mueven juntos
con el potasio**, y `ecg12` dibuja el complejo ancho de verdad:

```
llegada                      84/50  FC 38  QRS 180 ms   K desconocido
gluconato de calcio 2 g     100/59  FC 66  QRS 108 ms   K 7,60  ← ante la sospecha
+15 min                      96/57  FC 58  QRS 128 ms   K 7,60  ← vuelve a ensancharse
+55 min                      89/53  FC 46  QRS 158 ms   K 7,48
```

El calcio **no baja el potasio**: protege la membrana y cede. El salbutamol
nebulizado sí lo mueve, despacio, y vuelve a subir porque nada de lo que hay
aquí lo saca del cuerpo. El caso termina en una derivación a diálisis.

Y el que espera el laboratorio no ve nada cambiar: 38 de frecuencia y 180 ms a
los 30 minutos, con la atropina sin efecto.

**El evento crítico no es no dar calcio tras el resultado.** Es
`hyperk_calcium_awaited_the_laboratory`, con la ventana corriendo **desde el
trazado**, no desde el laboratorio.

### Decisiones tomadas

- **El calcio es una orden nueva**, con los dos gluconatos separados: el cloruro
  lleva unas tres veces el calcio elemental del gluconato para la misma masa, y
  el motor lo conserva en vez de tratar una ampolla como una ampolla.
- **El glucagón llegaba hasta 2 mg.** La dosis que responde a un envenenamiento
  por betabloqueo o calcioantagonista es cinco a diez veces la de la
  hipoglicemia, y el rango la rechazaba. Ahora llega a 10 mg.
- **El piso de frecuencia era 42.** Es una guarda contra que la aritmética de
  una familia se dispare, y habría borrado esta familia entera: una llegada de
  32 se mostraba como 42. En esta familia el piso es 20.
- **La hiperkalemia grave y el betabloqueo puro** quedan para la siguiente
  tanda: la primera necesita fisiología del potasio y cambios del QRS que el
  motor no tiene.

---

---

## Familia 4 · Trauma

`trauma_limb_hemorrhage_27m` · `trauma_hemothorax_41m`
Challenges: **R2-04** (enfermedad fuera del patrón) y **R2-05** (lo que queda
después del primer hallazgo).

Dos mecanismos, **uno a la vez**, como firmaste en 2.1: un caso combinado hace
imposible decir por cuál omisión respondió el paciente, y la rúbrica tiene que
poder decirlo.

### La x de xABCDE, y lo que cuesta no respetarla

Firmaste que el motor lo castigue. Lo hace, sin negarse a nada: la herida sangra
145 mL por minuto hasta que alguien la detiene.

```
el torniquete primero                      intubar primero
  llegada   96/54  FC 132  Alert             llegada   96/54  FC 132  Alert
  torniquete                                 (intubación, 10 min)
  +25 min  103/58  FC 127  Alert             +10 min   50/25  FC 178  Obtunded
           700 mL perdidos                             2150 mL perdidos
```

El torniquete después sigue funcionando. Lo que no vuelve es la sangre.

Sin control, a los ~17 minutos el motor declara el paro y dice por qué:
*«no volume replaces a source that is still open»*.

### El hemotórax, como lo redefiniste

Propuse un umbral de 1200 mL drenados. Lo reemplazaste por una **secuencia**, y
es mejor:

> «No sólo por el volumen sino también por la inestabilidad hemodinámica,
> independiente del volumen inicial que se drene. Si se drena y sigue
> inestable, se debe volver a buscar un sitio de sangrado… Si se ha descartado
> otro sitio y sigue hipotenso, mal perfundido con el tubo pleural instalado,
> debe ir a pabellón.»

```
tubo pleural izquierdo   → 1200 mL drenados de inmediato, y sigue llenándose
  +5 min    79/45  FC 133  Drowsy
  2 unidades de glóbulos rojos
  +10 min   73/42  FC 138  Drowsy      ← drenar no es detener
  E-FAST y radiografía de pelvis        ← volver a buscar
  cirugía                               ← y cuando no hay otro sitio, pabellón
```

El evento crítico ya no es «no drenó». Es
**`trauma_drained_and_never_looked_again`**: drenó, siguió inestable, y no
volvió a buscar. Y una aguja no drena un hemotórax — el motor lo dice con esas
palabras en vez de ejecutarlo.

### El E-FAST, con tus cinco ventanas

`efast_report.py` lleva el protocolo tal como lo escribiste: cuadrante superior
derecho (Morrison, subdiafragmático, receso pleural), cuadrante superior
izquierdo (esplenorrenal, subdiafragmático, receso pleural), suprapúbica
longitudinal y transversal, subxifoidea y pulmonar con *lung sliding*, signo de
la playa en modo M y colas de cometa en modo B.

Doce campos, y **cada caso reporta los doce**, incluidos los normales — por la
misma razón que reporta todo el protocolo POCUS: una ventana ausente de un
informe es una ventana que nadie miró, y no puede leerse como un hallazgo
negativo. Ninguna frase normal dice «negativo» ni «sin taponamiento».

La regla de que **en trauma penetrante las ventanas cardíacas van primero** está
implementada como `cardiac_first()`: el motor no se lo impide a nadie. Registra
qué miró primero, y la rúbrica lo lee — porque el orden es una decisión, no una
configuración.

---

## Lo que el camino dejó arreglado de paso

Todas estas fallas aparecieron jugando las familias nuevas, y todas son de
jugabilidad — el problema del que veníamos:

| Lo que fallaba | Qué pasaba |
|---|---|
| `adrenalina 0,5 mg IM` | orden no reconocida; ahora es `epinephrine_im` |
| `IM adrenaline 0.5 mg` | una vía escrita primero no abría una orden |
| `adrenalina 0,5 mg IM` sin verbo | un fármaco no abría una cláusula sin un verbo delante |
| `pido nefrostomía` | se leía como solicitud de estudio y se rechazaba |
| `ecografía renal` | devolvía además el protocolo POCUS completo |
| `eco renal y vesical` | la segunda cláusula retenía el turno |
| `alta con criterios de reconsulta` | la indicación de seguridad retenía el alta |
| **`Alta con analgesia oral y control en 7 días`** | **no producía nada: ni ejecución ni pregunta** |

La última es la peor de todas y es previa a este trabajo: la decisión de cierre
del encuentro, perdida en silencio.

---

## Lo que no está

- **Toxicología** no está implementada. Está diseñada con siete variantes tras
  tu ampliación (alcohol, cocaína y benzodiacepinas sobre las cuatro que
  propuse), y sugerí entregarla en dos tandas: primero TCA, paracetamol y
  benzodiacepinas, que son donde el error de manejo es más nítido.
- **De trauma falta la tercera variante**, la fractura inestable de pelvis. La
  faja pélvica ya es una orden ejecutable y el modelo ya la contempla como
  fuente; lo que falta es el caso.
- **La quinta familia que elegí fue anafilaxia**, y está entregada.

Cada familia entró con sus cinco dominios declarados, sus eventos críticos con
ventana clínica, `case_assessment.verify` sin discrepancias, y pruebas que fijan
la enseñanza clínica y no sólo que el código corre.
