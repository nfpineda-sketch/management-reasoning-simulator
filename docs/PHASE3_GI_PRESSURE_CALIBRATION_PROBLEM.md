# Fase 3 · P3-58 a P3-68 · El problema de calibración clínica de la presión GI

Rama `phase-3-runtime-integration`, desde `7d21dfc`. **Análisis de sólo lectura.** No se aprueba ningún
parámetro, no se cambia `gi_pressure_committed`, no se amplía la autoridad, no se toca producción, el
residente, el piloto ni la fisiología congelada de la Fase 2, y **nada se ajusta contra el legado**.

Digesto de la Fase 2 `22b90a6f…6ce6a`, sin mover. `COMMON_CORE_RUNTIME_AUTHORITY = False`.

## 1 · P3-58 · Qué es, exactamente, el problema

### 1.1 El grafo de dependencias, de la ecuación congelada

```
V (mL-eq)          = volume_preload_kappa x (desviacion de volumen circulante) + outside_v
preload_position(x)= 1 - exp(-max(0, F + x) / scale)      F = -scale x ln(1 - f)
scale              = preload_curve_scale_ml x P^(pump_preload_coupling)
f                  = anclas.preload_fraction, o arrival_preload_fraction si el caso no la declara
preload_rel        = preload_position(V) / preload_position(0)
afterload          = 1 / (1 + afterload_sensitivity x (T - 1))
output_rel         = P x (ritmo) x preload_rel x afterload
pressure_rel       = output_rel x T
SBP                = anclas.sbp x max(0, pressure_rel)
DBP                = anclas.dbp x max(0, pressure_rel)
MAP                = (SBP + 2 DBP) / 3
```

En GI, **P ≡ 1**, **T ≡ 1**, el factor del ritmo es 1 y los dos casos tienen
`anclas.preload_fraction = None`, así que la ecuación **se reduce exactamente** a una no linealidad
estática:

> **g(ΔVol) = (1 − (1 − f) · e^{−ν·ΔVol}) / f**, con **ν = volume_preload_kappa / preload_curve_scale_ml**
>
> **SBP = SBP_llegada · g**, **DBP = DBP_llegada · g**, **MAP = (SBP + 2·DBP)/3**

Comprobado contra `clinical_core.derived` en once valores de V: **peor diferencia 2,2·10⁻¹⁶**. Y la
dinámica de V **no lee** ν ni f («Output reads V only as V / preload_curve_scale_ml»), así que toda la
dependencia de parámetros vive en esta función estática y la trayectoria de volumen no se mueve.

### 1.2 Clasificación de las siete magnitudes

Verificada moviendo cada una ±y comprobando la presión GI bit a bit.

| Magnitud | Clasificación | Evidencia |
|---|---|---|
| `preload_curve_scale_ml` | `ACTIVE_GI_PRESSURE_PARAMETER` + `IDENTIFIABLE_ONLY_AS_COMBINATION` + **`LEGACY_RECONSTRUCTION_ONLY`** en el origen de su valor | la presión **cambia**; el registro dice que sólo la razón `scale/kappa` es identificable y «nunca se decide sola»; su canónico es la mediana y su razón declarada es **«mantiene la pendiente del legado»** |
| `arrival_preload_fraction` | `ACTIVE_GI_PRESSURE_PARAMETER` | la presión **cambia**; razón declarada en el registro: «default arrival position», sin fundamento evidencial |
| `pump_preload_coupling` | `INERT_IN_CURRENT_GI_MODEL` + `CONDITIONALLY_ACTIVE` | presión GI **idéntica** a ×0,5; entra como `P^c` y en GI P ≡ 1; ×1,7 lo rechaza el propio invariante del núcleo (0 ≤ c ≤ 1). Se activaría con P ≠ 1 |
| `afterload_sensitivity` | `INERT_IN_CURRENT_GI_MODEL` + `CONDITIONALLY_ACTIVE` + `CROSS_FAMILY_ONLY` | presión GI **idéntica** a ×0,5 y ×1,7; entra como `1/(1+a(T−1))` y en GI T ≡ 1. Actúa en las familias con tono |
| `low_output_pressure_knee` | `NOT_READ_BY_CURRENT_PRESSURE_EQUATION` + `LEGACY_RECONSTRUCTION_ONLY` | presión **idéntica**; desde P2J-1 la rama lineal se retiró y el docstring dice que la rodilla «queda en el perfil, sin leer, para que los registros históricos sigan legibles» |
| `sbp_per_pressure_deficit` | `NOT_READ_BY_CURRENT_PRESSURE_EQUATION` + `LEGACY_RECONSTRUCTION_ONLY` | igual; era `sbp − (circulation − 1)·45` del motor heredado |
| `dbp_per_pressure_deficit` | `NOT_READ_BY_CURRENT_PRESSURE_EQUATION` + `LEGACY_RECONSTRUCTION_ONLY` | igual, con 25 |

### 1.3 Dimensión efectiva

> **`GI_PRESSURE_EFFECTIVE_DIMENSION = 2`**

Derivación: de las siete, tres no se leen, dos están inertes porque GI fija P ≡ 1 y T ≡ 1, y las dos que
quedan entran **sólo** por `g(ΔVol; ν, f)`. Y de esas dos, `preload_curve_scale_ml` no aparece nunca sola:
sólo como ν = kappa/scale. Así que las coordenadas de calibración son **(ν, f)**, no siete campos y
tampoco dos campos del esquema.

Hoy: **ν = 1,2·10⁻³ por mL real** (kappa = 1,0; scale = 833,33) y **f = 0,5**.

### 1.4 Esquema de la instantánea contra dimensión de calibración

`RUNTIME_DETERMINISTIC_SNAPSHOT_FIELDS` = las siete. Las tres no leídas y las dos inertes **siguen
necesitando un valor determinista**, por dos razones que no son calibración: un registro histórico de la
rama lineal sólo es legible si las dos ganancias y la rodilla conservan sus números, y una instantánea
reproducible necesita que **todo** campo esté fijado para que el digesto del artefacto signifique algo.

`CLINICALLY_CALIBRATABLE_GI_PRESSURE_FIELDS` = **(ν, f)**, y ν no es un campo del esquema: es una razón
entre un campo de la instantánea y `volume_preload_kappa`, que **no está en el registro de calibración**
(sin región declarada) y que el propio registro marca `SYNTHETIC/CANDIDATE`.

Esto es lo que impide, con fundamento, mantener una calibración de siete dimensiones: cinco campos no
pueden ser calibrados por evidencia de GI porque la presión GI no los lee, y el sexto sólo existe para la
calibración dentro de una razón.

## 2 · P3-59 · Identificabilidad

### 2.1 Combinaciones analíticas

Con u = ν·ΔVol:

- **g(0) = 1 exactamente, para todo (ν, f).** La llegada no contiene **ninguna** información sobre los dos
  parámetros: el modelo está normalizado en la llegada por construcción. Un ancla de llegada —el dato
  clínico mejor establecido que hay— **no puede calibrar esta presión**.
- Primer orden: g ≈ 1 + ((1−f)·ν/f)·ΔVol. La pendiente inicial depende sólo del compuesto
  **m = (1−f)·ν/f**.
- Segundo orden: g = 1 + m·ΔVol − (m·ν/2)·ΔVol² + …, así que ν se separa de m **sólo por la curvatura**.
- Límite: g → **1/f** cuando ΔVol → ∞. El plateau identifica f **sola**, si la evidencia llega a verlo.
- Frontera: g = 0 cuando ν·ΔVol ≤ ln(1−f), el punto vacío.

### 2.2 Jacobiano local, sobre las trayectorias certificadas

Las dos columnas, en sensibilidad relativa (parámetros en escala logarítmica):

`S·∂g/∂S = −((1−f)/f)·u·e^{−u}` y `f·∂g/∂f = (e^{−u} − 1)/f`

Sobre **742 minutos distintos** de las dos baterías, con `pressure_rel` ∈ [0,324, 1,481] (plateau 2,0,
nunca alcanzado) y **u = ν·ΔVol ∈ [−0,516, +0,655]**, es decir **ΔVol ∈ [−430, +546] mL**:

| | |
|---|---|
| Valores singulares | 2,178·10¹ y 1,375 |
| **Rango numérico** | **2** |
| **Número de condición** | **15,8** |
| Correlación de las dos columnas (centradas) | **0,991** |
| Razón de sensibilidades en el rango observado | 0,39 a 0,49 (en u = 2 sería 0,16) |

El condicionamiento numérico **no** es certeza estadística y no se presenta como tal: dice que una
dirección está ~16 veces menos restringida que la otra por esta evidencia, no cuál es el error de un
parámetro.

### 2.3 Veredicto por parámetro, con la evidencia GI actual

| | |
|---|---|
| **m = (1−f)·ν/f** (pendiente en la llegada) | `SEPARATELY_IDENTIFIABLE` — es la dirección fuerte |
| **f** | `WEAKLY_IDENTIFIABLE` — separable sólo por la curvatura, y el rango de u observado deja poca |
| **ν** | `WEAKLY_IDENTIFIABLE`, por lo mismo |
| `preload_curve_scale_ml` **sola** | `NONIDENTIFIABLE` **por construcción**, no por falta de datos: entra sólo como kappa/scale |
| `volume_preload_kappa` **sola** | `NONIDENTIFIABLE`, igual |
| las otras cinco | fuera del problema: la presión GI no las lee o las anula |

### 2.4 Reparametrización propuesta (análisis, no cambio)

En vez de (scale, kappa, f), las coordenadas que la evidencia ve:

> **(m, f)** con **m = (1−f)·ν/f**, y ν = m·f/(1−f) de vuelta.

`clinical_core` **no se toca**. La propuesta es para el pack docente, y su valor es que m tiene unidades
clínicas directas: **mmHg de sistólica por mL de volumen, en la llegada** (multiplicada por la sistólica
de llegada).

## 3 · P3-60 · Atlas de respuesta

Región admisible declarada: `preload_curve_scale_ml` ∈ [600, 1500] (canónico 833,33),
`arrival_preload_fraction` ∈ [0,3, 0,7] (canónico 0,5). **Sin extrapolar.** Escenarios: los de las dos
baterías certificadas; **371 valores distintos de ΔVol**, de −430 a +546 mL. Ninguno inventado.

### 3.1 Monotonía

`∂g/∂ν = −((1−f)/f)·ΔVol·e^{−ν·ΔVol}` y `∂g/∂f = (e^{−ν·ΔVol} − 1)/f²`: **el signo de las dos es
−signo(ΔVol)**.

> Cada parámetro es **monótono** a ΔVol fijo, pero la **dirección se invierte al cruzar el llenado de
> llegada**: por encima de la llegada, subir ν o f **baja** la presión; por debajo, la **sube**.

En el vocabulario del encargo: **`INTERACTION_DEPENDENT`**, no `NONMONOTONIC` en el parámetro. Es una
consecuencia directa de la normalización en la llegada, y es la razón por la que un escenario sólo de
tratamiento y uno sólo de hemorragia dan evidencia de signo opuesto sobre el mismo parámetro.

### 3.2 Frontera

`BOUNDARY_LIMITED` en una esquina real de la región: el punto vacío está en ΔVol = ln(1−f)/ν, que para
f = 0,3 cae en **−535 mL** con scale 1500, **−297 mL** con 833 y **−214 mL** con 600. Los cursos
certificados llegan a **−430 mL**, así que en parte de la región declarada la presión toca **cero** dentro
del rango observado. Una futura calibración tiene que declarar eso como frontera, no como ajuste.

### 3.3 Degeneración

Exacta: ninguna. `{u·e^{−u}, 1 − e^{−u}}` son linealmente independientes, así que dos puntos distintos de
(ν, f) no dan trayectorias idénticas. **Práctica**, medida en mmHg sobre los ΔVol observados y sin
inventar ninguna tolerancia clínica:

| Dirección | Qué se mueve | Diferencia máxima de SBP en los ΔVol observados |
|---|---|---|
| **Débil** (m constante) | f 0,50 → 0,40, scale 833 → 1250 | **5,2 mmHg** (57m) · **5,8 mmHg** (72f) |
| **Débil**, resto de la curva iso-m | f ≤ 0,35 o ≥ 0,60 | **fuera de la región declarada** de la escala |
| **Fuerte** (f fijo, scale en toda su región) | scale 833 → 1500 | **30,2** (57m) · **33,7** (72f) |
| **Fuerte** | scale 833 → 600 | **32,8** (57m) · **36,5** (72f) |

Dicho en una línea: la evidencia observada distingue ~31–37 mmHg a lo largo de la dirección fuerte y
≤ 5,8 mmHg a lo largo de la débil, y la región declarada sólo admite dos compañeros iso-m.

### 3.4 Las dos magnitudes clínicamente juzgables

| | `gi_bleed_57m` (88/54) | `gi_bleed_72f` (98/62) |
|---|---|---|
| **Pendiente en la llegada, SBP** | **10,56 mmHg por 100 mL** | **11,76 mmHg por 100 mL** |
| Pendiente en la llegada, DBP | 6,48 mmHg por 100 mL | 7,44 mmHg por 100 mL |
| **Plateau de SBP** (llenado ilimitado) | **176 mmHg** | **196 mmHg** |

Estas dos cifras son todo lo que el punto comprometido afirma sobre la presión GI, y son juzgables por
una persona con formación clínica. **No las califico.**

## 4 · P3-61 · Inventario de evidencia

| | Categoría | Qué hay en el repositorio | Etiqueta | ¿Restringe (ν, f)? |
|---|---|---|---|---|
| A | Anclas de caso autoradas | SBP/DBP/HR/CRT de llegada de los dos casos (88/54 y 98/62) | `CLINICAL_AUTHORED` | **No, ninguna**: g(0) = 1 por construcción. Sí convierte g en mmHg |
| B | Evidencia de migración de la Fase 2 | **`untreated_output`** (output relativo al de llegada, hemorragia activa sin tratar, envolventes **por caso y por minuto**), **FD-BLD-02** (incremento de output por una unidad de glóbulos en estado preload-responsivo), **FD-BLD-03** (una unidad no debe normalizar el output; cualitativa, no filtra), **`second_unit`** (la unidad 2 aporta a lo más lo que la 1), **FD-BLD-04/05** (de mL infundidos a mL circulantes: 0,15–0,30 inicial, decayendo), FD-BLD-07/08/09 (relleno endógeno y dilución) | `CLINICAL_AUTHORED` (aprobadas 2026-10-27 como envolventes a nivel de paciente) | **Sí**: en GI `pressure_rel = output_rel`, así que una envolvente de output **es** una envolvente de g. `untreated_output` restringe la rama ΔVol < 0; FD-BLD-02 la rama ΔVol > 0; **`second_unit` restringe la curvatura, que es la dirección débil** |
| C | Narrativa clínica de los casos | descripciones, severidad, melena, relleno capilar | `CLINICAL_AUTHORED`, cualitativa | Indirectamente, por la severidad; no numéricamente |
| D | Vitales de llegada | lo mismo que A | `CLINICAL_AUTHORED` | **No** |
| E | Expectativas de respuesta al tratamiento | las categorías de la batería («el motor rinde menos con cristaloide que con sangre») | `STRUCTURAL_MODEL_CONSTRAINT` | Sí, de orden/signo, no de magnitud |
| F | Restricciones comunes entre familias | las constantes compartidas de la curva de preload; `afterload_sensitivity` restringido sólo por familias con tono | `STRUCTURAL_MODEL_CONSTRAINT` | f y ν son compartidos, así que otras familias podrían restringirlos; hoy ninguna lo hace por presión |
| G | Salidas del legado | la trayectoria de SBP/DBP del motor heredado | **`LEGACY_COMPARATOR`** | **Prohibido como verdad.** Y es el origen del canónico de `preload_curve_scale_ml` («mantiene la pendiente del legado»), de modo que **el valor comprometido hoy tiene procedencia de reconstrucción del legado, no clínica** |
| H | Referencias sintéticas | `volume_preload_kappa` (`SYNTHETIC/CANDIDATE`), el punto comprometido, los dos testigos de región | `SYNTHETIC_REFERENCE` / `DERIVED_FROM_COMMON_MODEL` | **No pueden calibrar**: son el modelo |

### 4.1 Evidencia circular, nombrada

- La trayectoria de `pressure_rel` de la sombra —la que usé para medir el Jacobiano y el rango de ΔVol—
  **es salida del propio modelo**. Es legítima para medir la **geometría** del problema (es una propiedad
  del modelo) y **no** puede ser un objetivo de calibración. Lo digo porque es la tentación obvia: hay
  742 minutos de datos aparentemente ricos y **ninguno** es evidencia.
- `volume_preload_kappa = 1,0` es una conversión sintética: cualquier «calibración» que la trate como dato
  está calibrando contra una convención.
- El canónico de `preload_curve_scale_ml` viene de la pendiente del legado. Usarlo como punto de partida y
  después «confirmarlo» contra el legado sería ajuste al legado disfrazado de calibración.

### 4.2 Lo que falta, derivado de la estructura del modelo

De §2.1 y §3.4, y de nada más: el modelo tiene **dos** grados de libertad y existen **exactamente dos**
magnitudes clínicamente juzgables que los determinan sin residuo (§6.1). Falta, en orden de poder
informativo:

1. **un juicio docente sobre la pendiente de la sistólica por volumen en la llegada** (hoy 10,6 y
   11,8 mmHg/100 mL) — fija la dirección fuerte;
2. **un juicio docente sobre el plateau de la sistólica con llenado ilimitado** (hoy 176 y 196 mmHg) —
   fija f, y con ella la dirección débil;
3. serial de presión tras una intervención de volumen **cuantificada** en un paciente real con hemorragia
   digestiva: es lo que convertiría (1) de juicio en medición;
4. tiempo de control del sangrado documentado, que separaría la rama negativa de la positiva;
5. casos independientes adicionales, para validación más que para calibración (§7).

Nada de esto es «más datos en general»: son las dos magnitudes de la estructura, y después su medición.

## 5 · P3-62 · Diseño del objetivo

### 5.1 Clases de objetivo

| Clase | ¿Hay evidencia clínica independiente? |
|---|---|
| `ARRIVAL_ANCHOR` | Sí, pero **no restringe**: g(0) = 1 siempre |
| `UNTREATED_TRAJECTORY` | **Sí**: `untreated_output` por caso y por minuto |
| `TREATMENT_RESPONSE` | **Sí**: FD-BLD-02, FD-BLD-03 (cualitativa) |
| `TEMPORAL_SLOPE` | Parcial: FD-BLD-05/07 dan la dinámica del volumen, no de la presión |
| `BOUNDARY_AVOIDANCE` | **No clínica**: que el punto vacío no se alcance es admisibilidad estructural, y tratarla como verdad clínica sería el error que P3-66 ataca |
| `CROSS_FAMILY_CONSTRAINT` | Hoy no para presión |

### 5.2 El legado

Sólo `DESCRIPTIVE_COMPARATOR`. Y con una advertencia que este ciclo encontró: la pendiente del legado ya
está dentro del canónico de la escala, así que «coincide con el legado» no es una verificación
independiente, es una tautología.

### 5.3 Forma del objetivo

**Satisfacción de intervalos y restricciones, no mínimos cuadrados** — que es exactamente lo que el
repositorio ya hace: «a constraint asks whether a reading falls inside one, and nothing is fitted to its
midpoint». Formas candidatas, ninguna aprobada:

- pertenencia a envolvente por caso y por minuto (`untreated_output`);
- desigualdades (`second_unit`: el beneficio de la unidad 2 ≤ el de la 1; FD-BLD-03: una unidad no
  normaliza);
- monotonía (la presión no baja con el volumen a tono fijo — ya es un invariante del núcleo, no un
  objetivo);
- coincidencia de rasgos de trayectoria (pendiente en la llegada, plateau);
- verosimilitud: **no**, porque no hay datos de incertidumbre reales que la justifiquen.

### 5.4 Reserva para validación

Propuesta: `untreated_output` de **un** caso y FD-BLD-02 se reservan y no entran en la calibración. Pero
véase §7: con dos pacientes autorados esa reserva es aritmética, no evidencial.

## 6 · P3-63 y P3-64 · Arnés y región factible

### 6.1 El arnés que no hace falta escribir

> **`NONAUTHORITATIVE_CALIBRATION_HARNESS_ALREADY_EXISTS_OUTSIDE_AUTHORITY`**

Dos razones, y las dos son medidas, no supuestos:

1. la parte de **presión** del problema es una **forma cerrada** verificada a 2,2·10⁻¹⁶, de dos
   parámetros. Evaluar un candidato no necesita simulación: es una expresión. Y el mapa inverso de las dos
   magnitudes juzgables a (ν, f) es exacto, con error 0,0:

   > **f = SBP_llegada / plateau** · **ν = pendiente · f / ((1 − f) · SBP_llegada)**

2. la parte de **trayectoria** —bleed rate, Hb, relleno, envolventes por minuto— ya tiene un filtro
   **congelado, de sólo lectura, sin autoridad y que escribe fuera del repositorio**:
   `python -m clinical_core.blood_constraints --filter --out <directorio fuera del repositorio>`, con su
   `freeze_digest` respondiendo hoy `f1242809bf83…`. Toma candidato, escenarios, definición de
   restricciones y digesto; emite satisfacción por restricción; no elige un punto; y ya filtró la región
   de P2I-2U en P2I-2V/V-R.

Escribir un segundo arnés duplicaría infraestructura congelada y añadiría una superficie nueva por
ninguna capacidad nueva. Si una decisión docente futura pide rasgos de **presión** que ese filtro no
emite, el paquete mínimo es una capa de lectura sobre la forma cerrada, fuera de `clinical_core` — no un
motor.

### 6.2 Región factible

> **`POORLY_IDENTIFIED_CONTINUUM`**, y con una parte **no evaluable desde el repositorio**.

- La **forma** de la región es analítica y conocida: una franja a lo largo de la curva iso-m, de ancho
  ≤ 5,8 mmHg en los ΔVol observados, recortada por la región declarada de la escala a f ∈ [0,40, 0,50]
  aproximadamente.
- La región factible **completa** —la que sale de las envolventes docentes— **no** es calculable aquí en
  2 dimensiones, porque `untreated_output` acopla (ν, f) con la **tasa de sangrado**, que es otro
  candidato (`bleed_rate_analysis` usa una tasa común de familia). Es un problema conjunto de ≥3
  parámetros, que es exactamente por lo que el filtro congelado recorre una rejilla conjunta.
- Y el conjunto superviviente de P2I-2V-R **no vive en el repositorio**: por política se escribe fuera. No
  lo reconstruyo ni lo supongo.

### 6.3 Dónde está `gi_pressure_committed`

| | |
|---|---|
| Contra la **región declarada** | **`INSIDE`** — y dicho con precisión: está en el **centro exacto** de las dos, porque sus valores **son** las medianas del registro. Estar dentro no es evidencia: el punto **define** el centro |
| Contra la región **restringida por docencia** | **`NOT_ASSESSABLE`** desde el repositorio: el conjunto superviviente vive fuera |
| Procedencia de sus dos valores activos | `preload_curve_scale_ml`: **reconstrucción del legado** («mantiene la pendiente del legado»). `arrival_preload_fraction`: convención («default arrival position») |

No se ajusta ninguna región para que lo contenga, y no se mueve el punto.

## 7 · P3-65 · Independencia y holdout

- **Dos** pacientes autorados, 17 categorías de escenario cada uno. Los escenarios de un mismo caso
  comparten el ancla autorada, el generador de la enfermedad, el mapeo de intervenciones y los parámetros
  latentes: **no son pacientes independientes**, y contarlos como tales sería pseudorreplicación.
- De las restricciones docentes, la mayoría son de **familia**; sólo `untreated_output` y FD-BLD-03 son
  **por caso**. Así que hay exactamente **dos** conjuntos de restricciones independientes por paciente.
- Un leave-one-case-out es aritméticamente posible y evidencialmente vacío: con n = 2 no separa error de
  modelo de variación entre pacientes.

> **Veredicto: `CURRENT_GI_DATA_SUPPORTS_INTERNAL_CALIBRATION_ONLY`.**

Lo que **sí** se puede validar con dos pacientes: que la región satisface las restricciones declaradas,
que el signo y el orden de las respuestas son los esperados, y que la frontera no se alcanza. Lo que **no**:
exactitud clínica, generalización a otros pacientes, y cualquier intervalo de confianza.

## 8 · P3-66 · Revisión adversarial

| Ataque | Clase | Resolución |
|---|---|---|
| Pseudorreplicación: 34 escenarios de 2 pacientes como si fueran datos | **`ROBUST`** (el ataque acierta) | Declarado en §7. Los 742 minutos **no** son 742 observaciones: son un modelo evaluado en 742 puntos |
| Uso circular de objetivos generados por el modelo | **`ROBUST`** (acierta) | Declarado en §4.1. La trayectoria de la sombra mide geometría, no calibra |
| Ajuste al legado disfrazado de calibración | **`ROBUST`** (acierta, y peor de lo esperado) | El canónico de la escala **ya** contiene la pendiente del legado, así que la tautología está dentro del punto de partida. Dicho en §4.1 y §6.3 |
| Los parámetros no son identificables | `WEAK` como objeción total | El rango es **2**: son identificables en principio. La objeción correcta y sostenida es de **condicionamiento**, no de identificabilidad, y está cuantificada (15,8; ≤5,8 mmHg) |
| Se «calibran» parámetros inertes | **`ROBUST`** (acierta) | Por eso la dimensión efectiva es 2 y no 7, con la prueba bit a bit de §1.2 |
| La evitación de la frontera se trata como verdad clínica | **`ROBUST`** (acierta) | Declarado en §5.1: `BOUNDARY_AVOIDANCE` no es evidencia clínica |
| Sobreinterpretar la respuesta al tratamiento | `WEAK` pero parcialmente válido | FD-BLD-02 es una envolvente docente real; lo que no se puede es leer magnitud fina de ella |
| Casos independientes insuficientes | **`ROBUST`** | §7 |
| Elegir un punto porque la autoridad ya lo usa | **`ROBUST`** (acierta) | Es exactamente lo que §6.3 prohíbe decir: el punto está en el centro porque **es** el centro |
| Confundir plausibilidad causal con exactitud clínica | **`ROBUST`** | P3-57 dio A de ingeniería; este documento no mueve esa frontera |
| «La dimensión es 2» sobreinterpretado como «el problema es fácil» | `UNSUPPORTED` si alguien lo dijera | Dos dimensiones mal condicionadas sobre dos pacientes y sin un objetivo clínico aprobado no es fácil: es **pequeño y honesto** |
| El mapa inverso exacto sugiere que la calibración es inmediata | `CIRCULAR` si se usara así | El mapa es exacto **dado** dos envolventes que nadie ha emitido. La exactitud es del álgebra, no de la clínica |

**Conclusiones que sobreviven:** la dimensión efectiva 2; la no identificabilidad por construcción de la
escala sola; el rango 2 con condición 15,8; la inversión de signo en la llegada; la nulidad informativa
del ancla de llegada; las dos magnitudes juzgables; la existencia de evidencia docente no circular por
la vía del output; y la procedencia de legado del valor comprometido.

**Conclusiones debilitadas por la revisión:** ninguna de las anteriores; y se debilita explícitamente
cualquier lectura de los 742 minutos como «datos».

## 9 · P3-67 · Checkpoint

> **B · `GI_PRESSURE_CAN_ONLY_BE_PARTIALLY_CONSTRAINED_WITH_EXISTING_EVIDENCE`**

Por qué B y no A: existe evidencia docente aprobada, no circular, que restringe la curva compartida por
la vía del **output** —y en GI el output **es** la presión relativa—, más anclas de llegada autoradas que
la convierten en mmHg. Hay con qué acotar una región.

Por qué B y no C: lo que falta **no es dato de paciente**. Son **dos juicios docentes** de la misma forma
que el repositorio ya emitió dos veces (FD-LAC-01..06 sobre el lactato, FD-BLD-01..09 sobre el volumen):
envolventes sobre un observable, que no aprueban ningún parámetro. El modelo tiene dos grados de libertad
y hay exactamente dos magnitudes juzgables que los fijan.

Por qué B y no D: no hay contradicción estructural. La ecuación es consistente, suave, monótona en sus
parámetros a volumen fijo, y su normalización en la llegada —que anula la información del ancla— es una
decisión de diseño declarada, no un defecto.

## 10 · P3-68 (diseño; **no ejecutado**) · Pack docente de calibración de la presión GI

**Evidencia usada:** `untreated_output` (por caso, por minuto), FD-BLD-02, FD-BLD-03 (cualitativa),
`second_unit`, FD-BLD-04/05 para la conversión de volumen. **Excluidas y por qué:** la trayectoria del
legado (comparador, y ya contenida en el punto de partida), la salida del modelo común (circular),
`volume_preload_kappa` como dato (sintético), el ancla de llegada como restricción (no restringe).

**Parámetros libres:** ν y f, equivalentemente (m, f). **Fijos y por qué:** `pump_preload_coupling` y
`afterload_sensitivity`, inertes en GI y restringidos por otras familias; `low_output_pressure_knee`,
`sbp_per_pressure_deficit` y `dbp_per_pressure_deficit`, no leídos, fijos para que los registros
históricos sigan legibles.

**Lo que se pide decidir, y es lo único:**

1. una **envolvente** para el aumento de la sistólica por volumen efectivo en la llegada, por caso
   (referencia actual: 10,6 y 11,8 mmHg por 100 mL);
2. una **envolvente** para la sistólica máxima alcanzable con llenado ilimitado, por caso (referencia
   actual: 176 y 196 mmHg);
3. si la envolvente se declara sobre volumen **efectivo** (mL-eq) o sobre volumen **infundido**, en cuyo
   caso FD-BLD-04/05 hacen la conversión y entran en la restricción.

**Restricciones:** satisfacción de intervalos, nunca ajuste a un punto medio; la frontera del punto vacío
declarada como frontera; el signo invertido en la llegada declarado, para que una envolvente de la rama
positiva y una de la negativa no se lean como la misma restricción.

**Holdout:** `untreated_output` de un caso reservado, con la advertencia de §7 escrita en el propio pack.

**Salidas:** la región de (ν, f) que las envolventes admiten, su ancho en mmHg sobre los ΔVol
certificados, dónde cae el punto comprometido respecto de ella, y qué restricción es la que ata cada
dirección.

**Decisión de aprobación requerida:** emitir (1), (2) y (3) como envolventes clínicas, con el estado que
FD-LAC y FD-BLD ya usan: aprueban **comportamiento**, no un valor de parámetro. Sin eso, ninguna
calibración es posible, y con eso **sigue sin haber** un parámetro aprobado: habría una región
restringida por docencia.

**Lo que este pack no pide y no debe pedir:** que la IA proponga las envolventes, que se elija un punto
dentro de la región, que se declare calibración clínica, ni que se amplíe la autoridad.
