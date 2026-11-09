# Fase 3 · P3-68A a P3-68G · Pack docente de calibración de la presión GI

Rama `phase-3-runtime-integration`, desde `395247f`. **Análisis**, más una herramienta de
previsualización **fuera** de `clinical_core` y del registro de autoridad. No se aprueba ninguna
calibración, ningún punto y ninguna región; no se cambia `gi_pressure_committed`; no se amplía la
autoridad; no se toca producción, el residente, el piloto ni la fisiología congelada; **nada se ajusta
contra el legado**. Digesto de la Fase 2 `22b90a6f…6ce6a`, sin mover.

**A quién va dirigido:** a la persona docente que decide. No se te pide elegir ν ni f. Se te piden tres
juicios sobre **comportamiento clínico**; la región de parámetros sale de ahí por álgebra.

## 1 · El modelo, en dos dimensiones y en lenguaje llano

La presión de un paciente GI en este simulador es su **presión de llegada multiplicada por un factor**
que depende de cuánto volumen circulante tiene de más o de menos que al llegar. Nada más. Dos números
fijan ese factor:

- **cuán empinada** es la respuesta de la presión al volumen **justo en la llegada**;
- **cuán alto** puede llegar la presión si se llena sin límite (el techo).

Formalmente, y verificado contra el núcleo congelado a **2,2·10⁻¹⁶** en los cursos GI (donde el motor fija
P ≡ 1, T ≡ 1, factor de ritmo 1, y ningún caso GI declara su propia posición de llegada):

```
g(ΔVol) = [1 − (1 − f) · exp(−ν · ΔVol)] / f
SBP = SBP_llegada · g(ΔVol)      DBP = DBP_llegada · g(ΔVol)      MAP = (SBP + 2·DBP)/3
ν = volume_preload_kappa / preload_curve_scale_ml
```

Tres hechos que hay que tener delante todo el tiempo, porque cada uno es una trampa:

1. **`g(0) = 1` para todo (ν, f).** La presión de llegada —el dato clínico mejor establecido que tenemos—
   **no contiene ninguna información** sobre estos dos parámetros. El modelo está normalizado ahí por
   construcción.
2. Cerca de la llegada sólo se ve la combinación **m = (1 − f)·ν/f**.
3. El techo asintótico es **1/f** veces la presión de llegada, así que el techo identifica f **sola**.

## 2 · Qué significa «la pendiente», clínicamente

**dSBP/dΔVol en la llegada = SBP_llegada · (1 − f) · ν / f = SBP_llegada · m**, y lo mismo para DBP con
su propia presión de llegada. MAP sigue determinísticamente, porque la pantalla la deriva como
(SBP + 2·DBP)/3.

Es el **mismo factor adimensional** para los dos casos; lo que los separa son sus presiones autoradas:

| | `gi_bleed_57m` (88/54) | `gi_bleed_72f` (98/62) |
|---|---|---|
| Pendiente de SBP en la llegada, hoy | **10,56 mmHg por 100 mL** | **11,76 mmHg por 100 mL** |
| Pendiente de DBP en la llegada, hoy | 6,48 mmHg por 100 mL | 7,44 mmHg por 100 mL |

## 3 · Qué significa «el techo», clínicamente

**SBP_máx / SBP_llegada = 1/f.** Con la posición de llegada en su valor actual (f = 0,5) el techo es el
**doble** de la presión de llegada:

| f | Multiplicador | SBP techo `57m` | SBP techo `72f` |
|---|---|---|---|
| 0,30 (borde inferior declarado) | 3,33 | 293 mmHg | 327 mmHg |
| 0,40 | 2,50 | 220 mmHg | 245 mmHg |
| **0,50 (hoy)** | **2,00** | **176 mmHg** | **196 mmHg** |
| 0,60 | 1,67 | 147 mmHg | 163 mmHg |
| 0,70 (borde superior declarado) | 1,43 | 126 mmHg | 140 mmHg |

**Ilustración, no recomendación.** No califico ninguno de estos techos.

## 4 · La curvatura: rendimientos decrecientes, y la primera unidad contra la segunda

La misma f que fija el techo fija **cuán rápido se agota** la respuesta al volumen, y ν fija **a qué
distancia de la llegada** empieza a aplanarse. Concretamente, el incremento de g por un mismo ΔVol
adicional cae en factor `exp(−ν·ΔVol)`.

Con los valores de hoy (ν = 1,2·10⁻³ por mL, 300 mL-eq por unidad de glóbulos):

| | Incremento de g | Razón respecto de la primera |
|---|---|---|
| Unidad 1 (0 → 300 mL-eq) | +0,302 | 1,00 |
| Unidad 2 (300 → 600) | +0,211 | **0,70** |
| Unidad 3 (600 → 900) | +0,147 | 0,49 |

La restricción docente **`second_unit`** ya dice en el repositorio: «a medida que se agota la respuesta
al preload, el beneficio hemodinámico de la unidad 2 es a lo más el de la unidad 1; la razón estructural
de ~0,70 no queda aprobada como número». En el lenguaje de este modelo, esa restricción es exactamente
una cota sobre `exp(−ν · 300)`, es decir **sobre la curvatura**, que es la dirección que la evidencia
actual determina peor. Es la restricción docente existente más valiosa para este problema.

## 5 · La base de volumen: la decisión que no se puede evitar

**Qué es ΔVol en la ecuación:** el cambio de volumen **circulante efectivo** respecto de la llegada, en
mL-equivalentes, por la vía `V = volume_preload_kappa · volumen_circulante + outside_v`.

El camino desde una orden real hasta ΔVol, rastreado en el código:

| Intervención | Conversión implementada | Parámetros propios |
|---|---|---|
| **Cristaloide** | `ganancia = infundido · effective_ml_per_ml`; de esa ganancia una fracción `transient_share` se va con constante `leak_tau_min` | **tres**: 0,125 · 0,6 · 30 min (valores de referencia) |
| **Glóbulos rojos** | `volumen = unidades · volume_ml_per_unit`, con su propia Hb que se mezcla en la circulación que encuentra | **dos**: 300 mL-eq y 20 g/dL por unidad |
| **Sangrado** | pérdida del proceso de la familia hacia el estado sanguíneo, más relleno plasmático endógeno | tasa de sangrado, más tres de relleno |

Con los valores de referencia, **1000 mL de cristaloide infundidos** son ≈ **125 mL-eq** en el instante,
≈ 78 a los 30 minutos y ≈ **50** asintóticamente. Es decir: **«mmHg por 100 mL infundidos» y «mmHg por
100 mL efectivos» difieren en un factor de 8 a 20, y además dependen del tiempo transcurrido.**

**Y hay un hallazgo que obliga a decidir:** el filtro congelado de las decisiones docentes, preguntado
sobre el punto de referencia, **rechaza** FD-BLD-04, FD-BLD-05 y FD-BLD-06 en los dos casos y en las
nueve variantes declaradas — las tres restricciones que gobiernan precisamente esa conversión. Esos
veredictos no dependen de (ν, f): son lecturas del estado sanguíneo, y salen `False` en **63 de 63**
puntos del barrido. Dicho de otro modo: **el mapa de volumen infundido a volumen efectivo, hoy, está
fuera de las envolventes que la propia docencia aprobó para él.**

> **Veredicto de P3-68C: `C · VOLUME_COORDINATE_REQUIRES_FURTHER_FACULTY_DECISION`.**
>
> El volumen efectivo es la coordenada **correcta** del modelo pero **no es clínicamente observable**; el
> volumen infundido **es** observable pero sólo transporta a través de un mapa que hoy no satisface sus
> propias envolventes. Por eso la pregunta 3 no es retórica.

## 6 · Qué evidencia existente restringe de verdad el comportamiento

`blood_constraints.py` dice que sus envolventes aprobadas excluyen **a propósito** SBP y MAP. Pero en GI
`pressure_rel = output_rel`, así que **una envolvente de output es una envolvente de la presión relativa**,
y la presión en mmHg sale multiplicando por la llegada autorada. Lo que eso da, medido con el filtro
congelado como oráculo:

- **`U-OUT`** (output relativo sin tratar, por caso y por minuto, aprobada el 2026-10-27) restringe
  (ν, f) **muy fuerte**: barriendo la región declarada completa, 7 valores de escala × 9 de posición, se
  satisface en los **dos** casos en **2 de 63** puntos, y esos puntos forman una **cresta diagonal**, que
  es la dirección iso-m predicha analíticamente;
- refinando sobre la cresta: a tasa de sangrado 2,5 mL/min, para cada escala la ventana admisible de f
  mide **0,01–0,02** de ancho (sobre un rango declarado de 0,40), y a f fija la ventana de escala mide
  **25–50 mL-eq** (sobre 900). La región es un **continuo real, finísimo**: de 2 a 5 % de cada rango;
- **pero la cresta se mueve con la tasa de sangrado**: a 1,5 / 2,0 / 2,5 / 3,0 / 3,5 mL/min siempre hay
  exactamente 2 de 63 puntos, y están en lugares distintos. La tasa es otro candidato, con su propia
  política de autoridad. Así que `U-OUT` fija un **manifold conjunto**, no una región en (ν, f);
- **`second_unit`**, FD-BLD-01, FD-BLD-07, FD-BLD-08, FD-BLD-09 y `U-HB` se satisfacen en 63 de 63:
  no discriminan aquí;
- **FD-BLD-02** (incremento de output por una unidad) se satisface en 35 de 63: sí discrimina, y es la
  única restricción aprobada que mira la **rama positiva** de volumen;
- **FD-BLD-03** en 23 de 63, y es cualitativa y declarada `NOT_YET_HARD_FILTER`.

### 6.1 Dónde cae el punto de desarrollo, contra la evidencia docente

| | |
|---|---|
| Contra la región **declarada** (la caja del registro) | dentro, y en su **centro exacto**, porque sus valores **son** las medianas: estar dentro no es evidencia |
| Contra `U-OUT`, a la tasa de referencia 2,5 mL/min | **satisface `gi_bleed_72f` y NO `gi_bleed_57m`** |
| Contra `U-OUT`, barriendo la tasa de 1,0 a 5,0 mL/min | satisface los **dos** casos a **exactamente una** tasa: **2,75 mL/min** |
| Procedencia de su escala | la razón declarada en el registro es que **mantiene la pendiente del legado** |

Esto es descriptivo y no se corrige aquí: no se mueve el punto, no se mueve la región y no se ajusta
nada para que encaje.

## 7 · Qué evidencia NO debe usarse

- **La trayectoria del legado.** Y con una advertencia específica: la pendiente del legado **ya está
  dentro** del canónico de la escala, así que «coincide con el legado» es una tautología, no una
  verificación.
- **La salida del propio modelo común.** Los 742 minutos de `pressure_rel` de las dos baterías miden la
  **geometría** del problema; no son 742 observaciones y no pueden calibrar.
- **Los 34 escenarios como 34 observaciones.** Son 17 categorías sobre **dos** pacientes autorados, que
  comparten ancla, generador de enfermedad, mapeo de intervenciones y parámetros latentes.
- **`volume_preload_kappa` como dato.** Es una conversión declarada `SYNTHETIC/CANDIDATE` y no tiene
  región en el registro.
- **La presión de llegada como restricción.** No restringe: `g(0) = 1` siempre.

## 8 · Las tres preguntas

> **Pregunta 1.** ¿Qué rango de aumento de la **sistólica** por cada 100 mL de la coordenada de volumen,
> **medido justo en la llegada**, es clínicamente plausible en un adulto con hemorragia digestiva como
> estos dos casos? *(valor de hoy, para referencia y no como respuesta: 10,6 y 11,8 mmHg/100 mL de
> volumen efectivo)*
>
> **Pregunta 2.** ¿Qué rango de **multiplicador máximo de presión respecto de la llegada** es
> clínicamente plausible si se llenara sin límite? *(valor de hoy: 2,0, es decir techos de 176 y
> 196 mmHg)*
>
> **Pregunta 3.** ¿La pregunta 1 se declara sobre **(A)** el cambio de volumen circulante **efectivo**
> dentro del modelo; **(B)** el volumen externo **infundido**; **(C)** el volumen infundido **después**
> del mapa certificado de retención y mezcla; o **(D)** otra coordenada clínica que convenga definir?

**No supongo la respuesta de ninguna.** Y la pregunta 3 tiene consecuencia inmediata: si se elige (B) o
(C), la región hereda la anchura de FD-BLD-04/05, que hoy el punto de referencia no satisface (§5).

### 8.1 Qué implicaría cada respuesta (ilustración del mapa, no recomendación)

Con el mapa inverso exacto del §9, y **sólo** para mostrar la sensibilidad de la transformación:

| Si la pregunta 2 se respondiera… | …entonces f quedaría en | ¿Dentro de la región declarada [0,3, 0,7]? |
|---|---|---|
| multiplicador 1,5 – 2,5 | 0,400 – 0,667 | sí |
| multiplicador 1,8 – 2,2 | 0,455 – 0,556 | sí |
| multiplicador 2,5 – 3,5 | 0,286 – 0,400 | parcialmente: por debajo de 0,3 queda fuera |
| multiplicador 1,2 – 1,4 | 0,714 – 0,833 | **no**: enteramente fuera |

| Si la pregunta 1 se respondiera… (`57m`, base efectiva) | …entonces m quedaría en | …y la escala/kappa, a f = 0,5 |
|---|---|---|
| 5 – 10 mmHg/100 mL | 5,7·10⁻⁴ – 1,14·10⁻³ | 880 – 1760 mL-eq |
| 8 – 14 mmHg/100 mL | 9,1·10⁻⁴ – 1,59·10⁻³ | 628 – 1100 mL-eq |
| 15 – 25 mmHg/100 mL | 1,70·10⁻³ – 2,84·10⁻³ | 352 – 587 mL-eq (**por debajo** de 600: fuera) |

Ninguna de estas filas es una propuesta. Están para que se vea que el rango declarado de la escala
(600–1500) ya excluye pendientes por encima de ~14 mmHg/100 mL a f = 0,5.

## 9 · De las respuestas a la región: la transformación exacta

```
f        = 1 / multiplicador_de_techo                          (biyección decreciente)
ν        = (pendiente/100) · f / [(1 − f) · SBP_llegada]
escala/kappa = 1 / ν
m        = (1 − f) · ν / f = (pendiente/100) / SBP_llegada
```

Verificada en los dos sentidos a precisión de máquina (`test_d1`, 40 combinaciones) y contra el núcleo
congelado (`test_d1b`, < 10⁻¹²).

**Geometría:** un rectángulo en (m, f) es un **cuadrilátero curvado** en (ν, f), porque
`ν = m·f/(1 − f)`. La herramienta devuelve `RECTANGULAR_IN_(m,f)_AND_CURVED_IN_(nu,f)`, sus cuatro
esquinas, el tramo de escala/kappa implicado, la intersección con la región declarada, el punto vacío de
cada esquina y la banda de SBP sobre el rango de volumen certificado — **y la banda tiene ancho cero en
la llegada**, que es el hecho 1 del §1 hecho visible.

**La herramienta:** `gi_pressure_calibration_preview.py`, fuera de `clinical_core` y del registro de
autoridad. No minimiza, no promedia, no ordena, no elige punto y no escribe nada; pregunta el veredicto
docente al filtro congelado en vez de reimplementarlo. 53 pruebas lo fijan, incluidas: que no importa
ningún módulo de autoridad (por AST y en proceso nuevo), que una intersección vacía se dice y no se
empuja, que una región no colapsa a un punto, que el punto de desarrollo nunca es una respuesta por
omisión, y que el digesto de la Fase 2 y los siete valores de la instantánea no se mueven.

## 10 · Qué sigue sin saberse

1. **Las dos coordenadas de presión no están separadas de la tasa de sangrado.** `U-OUT` fija una cresta
   conjunta; la tasa la mueve.
2. **El mapa de volumen infundido a efectivo no satisface sus propias envolventes** (§5).
3. **La rama positiva** está restringida por una sola envolvente aprobada (FD-BLD-02) y una cualitativa.
4. **Dos pacientes.** Nada aquí distingue error de modelo de variación entre pacientes.
5. **El techo nunca se observa.** El `pressure_rel` máximo de los cursos certificados es 1,48 contra un
   techo de 2,0: la evidencia **no llega** a la zona que identifica f.

## 11 · Qué datos añadirían más información, derivado de la sensibilidad

Las dos columnas del Jacobiano, en escala relativa, son `−((1−f)/f)·u·e^{−u}` y `(e^{−u} − 1)/f` con
u = ν·ΔVol. Su razón `r(u)` es lo que permite separar las coordenadas, y **sólo se mueve con |u|**:

| u | ΔVol efectivo | Unidades de glóbulos | Cristaloide infundido | r(u) |
|---|---|---|---|---|
| 0,05 | 42 mL | 0,1 | 333 mL | 0,488 |
| **0,66 (máximo observado hoy)** | **550 mL** | **1,8** | **4,4 L** | **0,353** |
| 1,0 | 833 mL | 2,8 | 6,7 L | 0,291 |
| **2,0** | **1667 mL** | **5,6** | **13,3 L** | **0,157** |

De ahí, y no de la intuición:

1. **Para `m` (la pendiente):** una perturbación de volumen **pequeña y cuantificada** cerca de la
   llegada, con presión en serie. Honestamente: la aproximación lineal `g − 1 ≈ m·ΔVol` yerra **5,8 %** a
   100 mL efectivos, **16 %** a 300 y **25 %** a 500, así que «pequeña» significa ≈100 mL efectivos
   (≈800 mL de cristaloide infundido), y más allá de eso la medición ya no da m limpio.
2. **Para `f` (la curvatura y el techo):** una excursión de volumen **grande**. El número es duro:
   alcanzar u = 2 exige ≈**5,6 unidades de glóbulos**, y con cristaloide exigiría ≈13 litros, que no es
   clínico. **Sólo una transfusión masiva documentada puede llegar al régimen que identifica f.**
3. **Para separar (ν, f) de la tasa de sangrado:** medir la respuesta de volumen **después del control
   del sangrado**, donde la tasa no contribuye.
4. **Más escenarios de los mismos dos pacientes no aportan nada** si se quedan en u ∈ [−0,52, +0,66]: las
   filas del Jacobiano son casi colineales ahí (correlación 0,991). Pacientes nuevos resuelven una
   pregunta distinta —si (ν, f) son del paciente o compartidos— que el modelo hoy **supone** compartida y
   con n = 2 no puede probar.

**Conjunto mínimo adicional, y nada más:**

| | Caso | Qué resuelve |
|---|---|---|
| 1 | un paciente con hemorragia digestiva de **volumen cuantificado** y presión en serie **antes** de tratar | m, y acota la tasa de sangrado |
| 2 | un paciente con transfusión **≥ 4 unidades** y presión en serie **tras la hemostasia** | f, por curvatura, libre de la tasa |
| 3 | un paciente cuyo curso llegue a llenado casi vacío, con pérdida documentada | la frontera del punto vacío |

Los casos 1 y 2 pueden ser el mismo paciente en momentos distintos. No invento ningún dato.

## 12 · Revisión adversarial

| Ataque | Clase | Resolución |
|---|---|---|
| La pregunta de la pendiente hereda supuestos del legado | **`ROBUST`** | El valor de referencia que se muestra **es** reconstrucción del legado, y por eso se marca como tal en §6.1 y en la propia herramienta, y no se usa como respuesta por omisión (probado) |
| La coordenada de volumen efectivo no es clínicamente observable | **`ROBUST`** | Es la razón del veredicto C de §5, no una objeción pendiente |
| El techo está fuera del rango observado y por tanto no es identificable | **`ROBUST`** | Medido: `pressure_rel` máximo 1,48 contra techo 2,0 (§10.5). La pregunta 2 pide por tanto un **juicio**, no una medición, y eso queda dicho |
| Las restricciones FD-BLD ya implican las respuestas, así que las preguntas son circulares | **`WEAK`, y parcialmente al revés** | `U-OUT` restringe muy fuerte pero **conjuntamente con la tasa**, y FD-BLD-02 es la única aprobada en la rama positiva. Las preguntas aportan información que las envolventes no tienen: son sobre el **mapa**, no sobre una trayectoria. Pero la objeción acierta en que las respuestas deben **comprobarse** contra `U-OUT`, no sustituirla — y la herramienta lo permite |
| Las anclas autoradas se cuelan en la calibración pese a la normalización | **`UNSUPPORTED`** | Entran sólo como **factor de escala** a mmHg. `g(0) = 1` lo hace estructuralmente imposible, y una prueba fija que la banda tiene ancho cero en la llegada |
| El mapa de retención crea parámetros extra ocultos | **`ROBUST`** | Son cinco: tres de cristaloide y dos de la unidad de glóbulos. Dejan de estar ocultos en §5 |
| El punto actual sesga los ejemplos | **`ROBUST`** | Por eso las ilustraciones del §8.1 son rangos simétricos y asimétricos alrededor y lejos del valor actual, y `region()` **no tiene valor por omisión** para ninguna de las dos preguntas (probado) |
| Elegir intervalos sería codificar opinión sin evidencia | **`ROBUST`, y es el punto** | Por eso el estado que se pide es el de FD-LAC y FD-BLD: **aprueban comportamiento, no un valor**, y la región resultante sigue siendo una región de candidatos, no un parámetro aprobado |
| Dos pacientes siguen siendo insuficientes | **`ROBUST`** | §10.4 y §11.4 |
| El mapa inverso exacto crea confianza falsa porque las ecuaciones son exactas | **`ROBUST`** | La exactitud es del álgebra. Lo dice §9 y lo repite el veredicto |

**Sobreviven:** la dimensión 2; la nulidad informativa de la llegada; la cresta `U-OUT` y su acoplamiento
con la tasa; el punto comprometido fuera de la envolvente en `57m` a la tasa de referencia; el fallo del
mapa de volumen contra sus propias envolventes; el techo inobservable; y los tres tipos de caso de §11.
**Se debilita:** la idea de que las envolventes existentes ya responden las preguntas.

## 13 · Veredicto

> **B · `FACULTY_CONSTRAINTS_CAN_NARROW_BUT_NOT_DEFENSIBLY_CALIBRATE_THE_REGION`**

Por qué no A: las restricciones docentes **existentes** ya estrechan (ν, f) a un 2–5 % de cada rango
declarado —mucho más de lo que nadie suponía— pero lo hacen sobre un **manifold conjunto con la tasa de
sangrado**, el mapa de volumen no satisface sus propias envolventes, el techo no se observa nunca y hay
dos pacientes. Llamar a eso una región calibrada sería defendible sólo si esas cuatro cosas no
existieran.

Por qué no C: **no hace falta evidencia externa para que los juicios docentes sean defendibles.** Las
tres preguntas del §8 son juicios sobre comportamiento, de la misma forma que FD-LAC y FD-BLD, y la
transformación a región es exacta. La evidencia externa de §11 hace falta para **medir**, no para
decidir.

Por qué no D: la semántica no necesita revisión. Es coherente y está rastreada; lo que necesita es una
**decisión** sobre qué coordenada se declara (§5), que es la pregunta 3.

## 14 · Las decisiones que te quedan

1. **Pregunta 1** (rango de pendiente) — con el estado de FD-LAC/FD-BLD: aprueba comportamiento, no un valor.
2. **Pregunta 2** (rango de multiplicador de techo) — igual.
3. **Pregunta 3** (base de volumen) — y, si eliges (B) o (C), decidir también si FD-BLD-04/05 se
   revisan, porque hoy el mapa no las satisface.
4. **Si quieres que la región se compruebe contra `U-OUT`**, decidir qué se hace con la tasa de sangrado:
   fijarla por decisión, o aceptar que la región es conjunta.

Nada de esto aprueba un parámetro. Con las cuatro respuestas habría una **región restringida por
docencia**, y seguiría sin haber ningún valor aprobado.
