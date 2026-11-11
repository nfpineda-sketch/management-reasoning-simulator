# Fase 3 · Instantánea de desarrollo de GI: criterios, sensibilidad, selección y registro (P3-189 a P3-192) · registro (2026-11-11)

**Alcance.** Elegir **una** instantánea explícita de desarrollo para experimentos reproducibles, **sin reemplazar la región por el punto**, y dejar
su registro versionado e inmutable. **Esto no concede autoridad** (`COMMON_CORE_RUNTIME_AUTHORITY = False`), no cambia lo que ve el residente, la
puntuación ni el primer piloto, no toca `clinical_core/` ni la capa, y **no es validación clínica**. Toda magnitud sigue siendo una
`FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION`.

**Resultado en una línea.** `GI_DEVELOPMENT_SNAPSHOT_V1` = el punto medio de cada región aprobada por la docencia (margen mínimo 0,5 a las cotas).
`CENTER_REFERENCE` **no** se eligió: no es el punto medio de la región, y dos de sus magnitudes están **sobre** la cota superior de su región.

Registros: `docs/revision/GI_DEVELOPMENT_SNAPSHOT_V1.json` (inmutable), `docs/revision/PHASE3_GI_SNAPSHOT_SENSITIVITY.json` (barrido y series físicas);
pruebas: `test_phase3_gi_development_snapshot.py` (24); arnés: `test_gi_snapshot_analysis.py`.

## 0 · Orden real del trabajo (para que se pueda juzgar)
1. Los criterios y la jerarquía de preferencia son los del encargo (P3-189, P3-191). Los **umbrales de clasificación de la sensibilidad** (10 y 3 minutos de
   oscilación) se fijaron en el código **antes** de correr el barrido.
2. La **lista de métricas clasificadas** creció una vez, **después** de ver una primera pasada: `collapse_clear_tau` no movía nada en los siete escenarios
   requeridos y se habría leído «irrelevante» cuando sólo estaba «no ejercida». Se añadió la rescate tardío (orden en el minuto 215, **después** del colapso
   establecido), el único escenario que ejerce la limpieza del colapso. Con él, `collapse_clear_tau` pasa a `LOW_SENSITIVITY` (2 min).
3. La métrica `rec_below_0_80` **se informa pero no se clasifica**: sobre una recuperación física fija depende de si la orden cae antes o después del minuto
   en que el perfil llega a SIN RESPUESTA, un artefacto de la orden fija y no de la ley.
4. La selección se calculó **después** del barrido, con una regla que **no lee ningún valor del heredado**. La distancia al heredado se calculó al final,
   sólo para informar (§3.4).

## 1 · P3-189 · Criterios de selección (y P3-189A, sin defecto al centro)
Un `GI_DEVELOPMENT_SNAPSHOT` válido cumple **todos** los criterios duros y se ordena por los preferentes. Están en el código como datos
(`HARD_CRITERIA`, `RANKED_CRITERIA`) y en el registro.

| | Criterio duro | Cómo se comprueba |
|---|---|---|
| H1 | estrictamente dentro de **toda** región aprobada (ninguna magnitud sobre una cota) | margen normalizado > 0 en cada magnitud |
| H2 | conserva las invariantes de la docencia (recuperación FD-P3-176; orden de los sucesos de inicio y de colapso) | invariante de recuperación sobre su propia recuperación; orden sobre 118 perfiles |
| H3 | conserva el orden causal, la recuperación y la semántica del colapso en cada escenario | 0 violaciones en 118 perfiles × 2 casos × 9 escenarios |
| H4 | generaliza a los dos casos GI | diferencia de tiempos de suceso ≤ 1 min |
| H5 | determinista | la reevaluación iguala el registro exactamente |
| H6 | procedencia explícita | registro completo, con huella fijada por prueba |
| H7 | no se elige para imitar un tiempo heredado | la regla **no lee ningún valor del heredado** (prueba por código fuente y por firma) |

| | Criterio preferente (en orden) |
|---|---|
| R1 | el mayor margen mínimo normalizado a las cotas de las regiones |
| R2 | las menos magnitudes fuera del puente entre los testigos LOW y HIGH |
| R3 | la procedencia más interpretable: una regla sin parámetros sobre las regiones aprobadas, no un sorteo |

«Sobre una cota» o «a menos de 5 % de ella» exige justificación; «margen amplio» es ≥ 20 %. **No se elige `CENTER_REFERENCE` por ser el testigo central**
(P3-189A): hay que ganar por estos criterios, y no gana.

## 2 · P3-190 · Sensibilidad y dominancia de las diez magnitudes
### 2.1 Método (sin rejilla cartesiana)
* **Series físicas registradas.** F y la carga del colapso no realimentan nada, así que la trayectoria física (entrega y perfusión relativas, pulso) **no depende
  de las diez magnitudes**: un perfil se lee fuera de línea **exactamente** sobre una serie registrada. 18 encuentros en vivo (2 casos × 9 escenarios) dan las series.
* **Un evaluador independiente** (las dos leyes escritas de nuevo desde sus ecuaciones, sin llamar al núcleo) **reproduce bit a bit** los canales de Amendment 2 de
  los tres testigos de **cada** encuentro en vivo, con la instantánea como testigo intermedio: **12 012 filas, diferencia máxima 0,0, 0 desajustes de categoría o de colapso.**
* **Cobertura:** una magnitud a la vez sobre cinco niveles de la región completa (50 perfiles), los 16 vértices de las cuatro magnitudes dominantes, 48 puntos de un
  **hipercubo latino** sembrado (20261111) y los cuatro testigos con nombre: **118 perfiles**.

### 2.2 Clasificación (umbrales declarados antes: ≥ 10 min `HIGH`, ≥ 3 `MODERATE`, > 0 `LOW`, 0 `IRRELEVANT`)
Oscilación, en minutos, del tiempo de cada suceso al recorrer la región de la magnitud (caso 57m; el 72f difiere como mucho en 1):

| Magnitud | Clase | SOMNOL. | OBNUB. | SIN RESP. | colapso inminente | colapso establ. | recup. F<0,50 | recup. normal | rescate: sale de establecido | rescate: sin colapso | rescate: normal |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `delivery_severe` | **HIGH** | 9 | 18 | **28** | 0 | 0 | 3 | 3 | 0 | 0 | 1 |
| `delivery_normal` | **HIGH** | **26** | 18 | 7 | 0 | 0 | 3 | 3 | 0 | 0 | 3 |
| `perfusion_normal` | **HIGH** | 0 | 0 | 0 | **23** | 14 | 0 | 0 | 4 | 4 | 0 |
| `perfusion_severe` | **HIGH** | 0 | 0 | 0 | 14 | **22** | 0 | 0 | 7 | 3 | 0 |
| `established_burden` | **HIGH** | 0 | 0 | 0 | 0 | **11** | 0 | 0 | 2 | 0 | 0 |
| `burden_clear_tau` | MODERATE | 0 | 0 | 0 | 0 | 0 | 2 | **5** | 0 | 0 | 5 |
| `impending_burden` | MODERATE | 0 | 0 | 0 | **3** | 0 | 0 | 0 | 0 | 1 | 0 |
| `collapse_clear_tau` | LOW | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| `burden_rise_tau` | LOW | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `collapse_rise_tau` | LOW | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |

**`STRUCTURALLY_IRRELEVANT_FOR_CURRENT_GI`: ninguna.** Todas mueven algo en algún escenario; la que menos, `collapse_rise_tau`, 1 minuto.

### 2.3 P3-190B · Dominancia: dos magnitudes dominan la consciencia y dos el colapso
Efectos estandarizados del hipercubo latino (regresión lineal; R² ≥ 0,99 en los tiempos de inicio):

| Suceso | rango en el hipercubo | magnitudes dominantes (efecto estandarizado) |
|---|---|---|
| SOMNOLIENTO | 96–123 | `delivery_normal` −0,96; `delivery_severe` −0,33 |
| OBNUBILADO | 117–143 | `delivery_normal` −0,73; `delivery_severe` −0,72 |
| SIN RESPUESTA | 143–172 | `delivery_severe` −0,99; `delivery_normal` −0,25 |
| colapso inminente | 176–202 | `perfusion_normal` −1,00; `perfusion_severe` −0,58 |
| colapso establecido | 192–219 | `perfusion_severe` −0,92; `perfusion_normal` −0,56; `established_burden` +0,44 |
| recuperación: F < 0,50 | 7–13 | `delivery_severe` +0,70; `delivery_normal` +0,59; `burden_clear_tau` +0,36 |
| recuperación: categoría normal | 12–20 | `burden_clear_tau` +0,65; `delivery_severe` +0,51; `delivery_normal` +0,49 |

**El comportamiento está dominado por cuatro cotas de rampa** (las dos de entrega gobiernan cuándo se altera la consciencia; las dos de perfusión, cuándo
colapsa) y por `established_burden` y `burden_clear_tau` en sus propios sucesos. **Las constantes de tiempo de subida** (`burden_rise_tau`, `collapse_rise_tau`)
**mueven ≤ 1 minuto**: la incertidumbre amplia de la región **no** se esconde en ellas. Ningún efecto de perfusión o de colapso mueve un inicio de consciencia (|efecto| < 0,05).

### 2.4 Interacciones, monotonía y seguridad
* **Casi aditivo:** el error entre la predicción aditiva (del barrido de una magnitud a la vez) y el valor real en el hipercubo es de **0,4–1,0 min de media y ≤ 3,7 min
  como máximo** (el colapso establecido, el peor).
* **Monótono:** todas las métricas definidas son monótonas en cada magnitud, a lo largo de los cinco niveles. **Ninguna región no monótona ni insegura.**
* **Invariantes sobre los 118 perfiles × 2 casos × 9 escenarios: 0 violaciones** de: orden de inicio (SOMNOL. ≤ OBNUB. ≤ SIN RESP.; inminente ≤ establecido), curso sin tratar
  monótono, colapso que **nunca** precede a SIN RESPUESTA por F (el colapso no «lidera» la categoría), F que **nunca** baja antes de la orden, y categoría que
  **nunca** devuelve dos bandas de golpe.

### 2.5 Hallazgo: los testigos LOW y HIGH no acotan todo el comportamiento
Los vértices de las cuatro magnitudes dominantes dan rangos más anchos que los de los dos testigos:

| Suceso (57m) | vértices | LOW y HIGH | minutos no acotados por los testigos |
|---|---|---|---|
| SOMNOLIENTO | 92–127 | 92–126 | 1 |
| OBNUBILADO | 114–149 | 114–148 | 1 |
| SIN RESPUESTA | 140–175 | 140–175 | 0 |
| colapso inminente | 171–207 | 172–205 | 3 |
| **colapso establecido** | **189–225** | **195–219** | **12** |

Por eso la región **no se reemplaza por el punto** y el barrido de la región completa sigue siendo la comprobación; LOW y HIGH, además, no son vértices en cuatro
magnitudes (p. ej. `burden_rise_tau`: HIGH vale 1,85 y la región llega a 2,485).

## 3 · P3-191 · Selección
### 3.1 Candidatos y distancia a las cotas (margen = distancia a la cota más cercana, como parte del ancho de la región)

| Candidato | margen mínimo | magnitudes sobre una cota | fuera del puente LOW–HIGH | ¿pasa H1? |
|---|---|---|---|---|
| LOW | 0,00 | 8 | — | no |
| HIGH | 0,00 | 7 | — | no |
| **CENTER_REFERENCE** | **0,00** | **`collapse_clear_tau` y `impending_burden`** | `impending_burden` | **no** |
| 48 puntos del hipercubo | 0,002 a 0,133 | ninguna (31 con alguna magnitud a menos de 5 %) | — | sí, pero ninguno se acerca a 0,5 |
| **Punto medio de cada región (V1)** | **0,50** | **ninguna** | `burden_rise_tau` | **sí** |

`CENTER_REFERENCE` no es el punto medio: `burden_rise_tau` = 1,65 (margen 0,20), `collapse_rise_tau` = 2,0 (0,29), `established_burden` = 0,65 (0,33), y
`collapse_clear_tau` = 8,0 y `impending_burden` = 0,39 están **en** la cota superior. El punto medio de una región en caja es el **único** maximizador del margen mínimo
(probado con 4 000 puntos al azar y moviendo cada magnitud, una a una); **no se eligió por su nombre**.

### 3.2 Valores (P3-191A: se llama `GI_DEVELOPMENT_SNAPSHOT`, **no** calibración clínica, **no** perfil de producción, **no** perfil aprobado para autoridad)

| Magnitud | Valor | Región | | Magnitud | Valor | Región |
|---|---|---|---|---|---|---|
| `delivery_normal` | 0,75 | 0,70–0,80 | | `perfusion_severe` | 0,35 | 0,30–0,40 |
| `delivery_severe` | 0,50 | 0,45–0,55 | | `collapse_rise_tau` | 1,85 | 1,5–2,2 |
| `burden_rise_tau` | 1,964 | 1,443–2,485 | | `collapse_clear_tau` | 7,0 | 6,0–8,0 |
| `burden_clear_tau` | 8,51 | 6,38–10,64 | | `impending_burden` | 0,37 | 0,35–0,39 |
| `perfusion_normal` | 0,55 | 0,50–0,60 | | `established_burden` | 0,625 | 0,55–0,70 |

### 3.3 Qué hace (H2, H3, H4)
* **Inicio sin tratar**, igual en los dos casos: SOMNOLIENTO 109, OBNUBILADO 131, SIN RESPUESTA 158, colapso inminente 189, establecido 207 (CENTER_REFERENCE: 109/131/157/190/209;
  LOW: 126/148/175/205/219; HIGH: 92/114/140/172/195). **Los tiempos de la instantánea quedan entre los de HIGH y los de LOW en cada suceso.**
* **Invariante FD-P3-176** sobre su **propia** recuperación (orden al llegar a SIN RESPUESTA, minuto 158), en los dos casos: 0,80 → < 0,50 en **7** min (6–8); quedan **1** min
  tras la entrada formal (0–2); **95–97 %** del descenso ya hecho al entrar (≥ 79 %); ley aislada **4,0** min (3–5).
* **Rescate tardío** (orden en el 215, tras el colapso establecido): sale de establecido en 5 min, sin colapso en 9, categoría normal en 22–23.
* Los dos casos difieren como mucho en **1 minuto** en una métrica (H4); 0 violaciones de invariantes en los 118 perfiles (H2, H3); la reevaluación es idéntica (H5).

### 3.4 «No se eligió ajustando curvas del heredado» (H7)
1. La regla (`select`) recibe **sólo** `candidates`, y su código fuente, el de la geometría y el del punto medio **no contienen la palabra «legacy»** (prueba).
2. **Si se hubiera ajustado al heredado**, el candidato más cercano a sus minutos de inicio (63 y 175) habría sido uno que **abraza una cota** (`LHS_13`, margen 0,005): lo contrario de lo que
   piden los criterios. La instantánea ocupa el puesto **26 de 52** por distancia al heredado (90 contra 82 minutos): ni es el mínimo ni se le acerca por construcción.
3. FD-GI-03 sigue vigente: ningún tiempo de inicio se ajusta a los minutos heredados. La distancia se calculó **al final y sólo para informar**.

### 3.5 P3-191B · La región sigue existiendo
Se conservan `LOW` · `SELECTED_SNAPSHOT` (= `GI_DEVELOPMENT_SNAPSHOT_V1`) · `HIGH` para las comprobaciones de sensibilidad. Los testigos LOW y HIGH son **los del núcleo, sin cambio**
(`systemic_consciousness.WITNESSES`); `CENTER_REFERENCE` sigue existiendo como testigo de referencia y **no** es la instantánea. La capa mantiene sus tres testigos por nombre; el arnés
corre la instantánea como testigo intermedio **sin tocar la capa ni el núcleo**: sustituye la entrada del diccionario sólo dentro de un bloque y la restaura (probado, también tras un error).

## 4 · P3-192 y P3-192A · Registro inmutable y versionado
`docs/revision/GI_DEVELOPMENT_SNAPSHOT_V1.json`: identificador, versión 1, linaje del núcleo (`PHASE2_AMENDMENT_2`, digesto `a0af7d08…ce2`, candidato certificado `ad7bf81`), las diez
magnitudes, las cotas y los márgenes, las referencias docentes (A2-FD-013/015/020, FD-GI-01 a 04, FD-P3-176/177), la justificación, la incertidumbre, **seis falsadores**, la fecha, las
pruebas que lo respaldan, el comportamiento medido y las huellas.

| Huella | Valor |
|---|---|
| archivo (SHA-256) | `d9de4800…4803` |
| identidad (id + versión + valores + linaje + cotas) | `1f292d01…ec40` |
| registro completo | `9e258ab5…cdc9` |

* **Inmutable:** las tres huellas están fijadas en `test_phase3_gi_development_snapshot.py`; cualquier edición del archivo, de un valor o de las huellas falla.
* **Versionado (P3-192A):** un cambio de **cualquier** valor, cota, linaje o razón es un **archivo nuevo** `GI_DEVELOPMENT_SNAPSHOT_V2.json` que nombra al anterior en `supersedes`; la versión 1 queda intacta.
* **No es un artefacto de autoridad:** vive en `docs/revision/`; ninguna tienda, registro (`APPROVED_SNAPSHOTS` conserva **sólo** `gi_pressure_committed`), módulo de la capa ni de la
  aplicación lo nombra o lo importa (prueba por recorrido de los módulos de ejecución).

**Falsadores** (lo que obligaría a una versión nueva): una violación de orden o de seguridad en cualquier curso GI; la invariante FD-P3-176 incumplida en una recuperación; el evaluador
independiente y los canales en vivo discrepando; un cambio docente de cota que deje la instantánea sobre, cerca (< 5 %) o fuera de una cota; un caso, un tratamiento o un miembro del linaje
que cambie qué magnitudes son `HIGH_SENSITIVITY`; el digesto del núcleo moviéndose.

## 5 · Límites
* **Incertidumbre.** Las diez magnitudes son regiones de desarrollo; cuatro están débilmente identificadas (`collapse_*`, `impending_burden`, `established_burden`). Sobre la región, el
  tiempo de SIN RESPUESTA oscila 140–175 min y el del colapso establecido 189–225 min.
* **Dos casos, siete escenarios más dos.** Otros ritmos de reposición, otros casos GI o tratamientos nuevos cambian la trayectoria física y obligarían a repetir el barrido.
* **La selección es de desarrollo.** La asignó el encargo; la **ratificación docente** de la instantánea sigue pendiente (bloqueo B2 de `docs/PHASE3_GI_AUTHORITY_READINESS.md`).
* **La capa no puede correr la instantánea por identificador y huella** (sólo por nombre de testigo): es un bloqueo técnico de una autoridad futura, no de este registro.
