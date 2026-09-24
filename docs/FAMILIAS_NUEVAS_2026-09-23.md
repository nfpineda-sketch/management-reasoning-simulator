# Tres familias nuevas: anafilaxia, cólico renal y bradicardia inestable

> 2026-09-23. El banco pasa de **21 casos en 8 familias** a **27 casos en 11**,
> todos con cobertura completa de los cinco dominios y cero discrepancias.
> Las decisiones clínicas que quedaron abiertas están en
> `FAMILIAS_NUEVAS_DECISIONES_2026-09-23.md`, con la recomendación que tomé en
> cada una.

| | Antes | Después |
|---|---|---|
| Casos | 21 | **27** |
| Familias | 8 | **11** |
| Cobertura completa | 21 de 21 | **27 de 27** |
| Discrepancias | 0 | **0** |
| Eventos críticos definidos | 16 | **27** |

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

- **Trauma (xABCDE)** y **toxicología** no están implementadas. Las dos están
  diseñadas en detalle en el documento de decisiones, con las órdenes nuevas que
  cada una necesita y las preguntas que requieren tu firma. Trauma es la más
  grande de las cinco: tres fisiologías distintas más el control de hemorragia
  como orden con consecuencia temporal.
- **La quinta familia que elegí fue anafilaxia**, y está entregada.
- De la bradicardia faltan dos variantes de las cuatro que pediste.

Preferí tres familias que cumplen todos los criterios antes que cinco a medio
construir. Cada una entró con sus cinco dominios declarados, sus eventos
críticos con ventana clínica, `case_assessment.verify` sin discrepancias, y
pruebas que fijan la enseñanza y no sólo que el código corre.
