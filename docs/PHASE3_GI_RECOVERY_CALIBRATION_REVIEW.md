# Fase 3 · GI: revisión de la temporalidad de la recuperación antes de la instantánea (P3-181 a P3-188) · registro (2026-11-11)

**Veredicto al medir: B · `GI_REGION_NEEDS_ONE_MORE_FACULTY_DECISION`. Tras la decisión docente FD-P3-176 (opción a, §8):
A · `GI_DEVELOPMENT_REGION_READY_FOR_FACULTY_SNAPSHOT_SELECTION`.** En este ciclo **no cambió nada ejecutable**: ni `clinical_core/`, ni los
testigos, ni la capa de sombra. Se midió, se demostró y se detuvo en la compuerta docente de P3-183B. Sin autoridad
(`COMMON_CORE_RUNTIME_AUTHORITY = False`), sin exposición al residente, sin efecto en la puntuación, primer piloto sin cambios, ningún
encuentro terminado por el núcleo común y **sin afirmación de validación clínica**. Registro medido:
`docs/revision/PHASE3_GI_RECOVERY_REVIEW.json`; pruebas: `test_phase3_gi_recovery_review.py`.

## 0 · Decisiones de la docencia que abren el ciclo (2026-11-11)
| Decisión | Contenido |
|---|---|
| FD-GI-01 | **Se confirma la entrega relativa a la llegada** (`entrega efectiva actual / entrega efectiva de llegada`). Que los dos casos GI lean igual cuando su entrega relativa es equivalente **no es un defecto**. No se reintroducen umbrales absolutos de PAS ni de SpO2 para recuperar la separación del heredado. |
| FD-GI-02 | **Reloj de la recuperación.** Empieza cuando la fisiología aguas arriba **entra en la región de recuperación definida** (no en la orden, ni en el pico de F, ni al iniciar la infusión). Desde ahí, ≈ 3–5 min simulados de un deterioro ≈ 0,80 a < 0,50. Lo observado (0 / 1 / 3 min) **no lo cumple del todo**; la ley aislada (3,0 / 4,0 / 4,9) no basta si la trayectoria completa cruza la categoría antes. |
| FD-GI-03 | **Deterioro.** No se recalibra la subida ni los umbrales porque el heredado difiera. SOMNOLIENTO ≈ 92–126 min y SIN RESPUESTA ≈ 140–175 min sin tratar quedan como región de desarrollo. Sin ajuste a los minutos 63 / 138. |
| FD-GI-04 | **Colapso.** Arquitectura sin cambios; no termina el encuentro. `UnresolvedBoundary` (gasto cero con pulso) sigue siendo un bloqueo explícito de una autoridad futura, no un motivo para alterar la calibración. |

## 1 · P3-181 · Línea de tiempo exacta de la recuperación
Ambos casos GI × tres testigos. Para que cada testigo entre en su recuperación **sustancialmente alterado**, cada uno se trata en **su propio**
primer minuto SIN RESPUESTA (F ≈ 0,80): cristaloide 1 L y 4 U de glóbulos rojos, en un turno. La medida anterior trataba a los tres en el
minuto del testigo central, de modo que LOW se trataba con F = 0,60 y HIGH con 0,99.

| Evento (minuto) | LOW | CENTER_REFERENCE | HIGH |
|---|---|---|---|
| `T_ORDER` (la orden) | 175 | 157 | 140 |
| `T_EFFECT` (el volumen gira hacia arriba) | 176 | 158 | 141 |
| `T_SIGNAL_BEGINS_TO_FALL` (el objetivo de F empieza a caer) | 176 | 158 | 141 |
| el objetivo queda **por debajo de F** (la ley empieza a limpiar) | 176 | 158 | 141 |
| `T_F_PEAK` (F máxima: 0,817 / 0,812 / 0,818) | 176 | 158 | 141 |
| `T_F_BELOW_0_80` = `T_CATEGORY_IMPROVES` (3 → 2) | 178 | 160 | 143 |
| **`T_RECOVERY_REGION_ENTRY`** (entrega relativa ≥ su cota normal) | **184** (57m) / **183** (72f) | **166** | **149** |
| `T_F_BELOW_0_50` (2 → 1) | 184 | 167 | 151 |
| categoría de llegada (1 → 0) | 188 | 172 | 158 |
| **F al entrar en la región** | **0,43** / 0,50 | **0,50** | **0,56** |
| minutos de la entrada a F < 0,50 | 0 / 1 | 1 | 2 |
| minutos de F < 0,80 a F < 0,50 (trayectoria completa) | 6 | 7 | 8 |
| parte del descenso 0,80 → 0,50 hecha **antes** de entrar | 100 % | 99 % | 80 % |

Orden exacto, idéntico en los seis casos×testigo: **orden < efecto = el objetivo empieza a caer = el objetivo queda bajo F = pico de F <
F bajo 0,80 = la categoría mejora < ENTRADA en la región de recuperación ≤ F bajo 0,50 < categoría de llegada.** La entrada llega 8–9
minutos después de la orden: es tiempo de la fisiología aguas arriba (la entrega relativa sube ≈ 0,025 por minuto).

Minuto a minuto, testigo central (72 años; el de 57 difiere en la cuarta cifra):

| min | V | perfusión rel. | entrega rel. | objetivo de F | F | deterioro | categoría |
|---|---|---|---|---|---|---|---|
| 157 (orden) | −306,2 | 0,556 | 0,544 | 0,826 | 0,801 | 0,801 | 3 |
| 158 (efecto) | −291,6 | 0,581 | 0,570 | 0,719 | 0,812 | 0,812 | 3 |
| 159 | −277,2 | 0,605 | 0,596 | 0,614 | 0,802 | 0,802 | 3 |
| 160 | −262,9 | 0,629 | 0,622 | 0,511 | 0,781 | 0,781 | 2 |
| 162 | −234,6 | 0,675 | 0,673 | 0,308 | 0,713 | 0,713 | 2 |
| 164 | −206,7 | 0,718 | 0,722 | 0,112 | 0,617 | 0,617 | 2 |
| 165 | −192,9 | 0,740 | 0,746 | 0,016 | 0,561 | 0,561 | 2 |
| **166 (entrada)** | −179,2 | 0,760 | **0,770** | **0,000** | **0,501** | 0,501 | 2 |
| 167 | −165,6 | 0,780 | 0,793 | 0,000 | 0,445 | 0,445 | 1 |
| 172 | −98,7 | 0,874 | 0,906 | 0,000 | 0,247 | 0,247 | 0 |

(La tabla completa de los seis, minuto a minuto, está en el registro: `timelines`.)

### P3-181A · Por qué 3,0 / 4,0 / 4,9 aislado y 0 a 2 observado
La ley certificada es una relajación de primer orden hacia un objetivo **graduado**: `F(t+1) = s + (F − s)·e^(−1/τ)`, con `τ` de bajada cuando
el objetivo `s` está por debajo de F, y `s` es la rampa de fallo de entrega (1 en la cota grave, 0 en la cota normal). El cálculo aislado
supone que el objetivo cae a cero **de golpe** con F en 0,80: entonces `F = 0,80·e^(−t/τ)` y `t = τ·ln(0,8/0,5)` = 3,0 / 4,0 / 4,9 min.

En la trayectoria completa el objetivo **no cae de golpe**: la reposición sube la entrega ≈ 0,025 por minuto, así que el objetivo baja en rampa
≈ 0,10 por minuto durante 7–8 minutos. F empieza a limpiar **en cuanto el objetivo queda bajo ella** (un minuto después de la orden) y lo
sigue con retraso: `F(t) = s(t) + τk − (τk + s₀ − F₀)·e^(−t/τ)`, con `k` la pendiente del objetivo. Al llegar a la entrada (`s = 0`):
`F_entrada = τk·(1 − e^(−T/τ)) + (F₀ − s₀)·e^(−T/τ)` ≈ 0,43–0,56 (la forma cerrada coincide con lo medido dentro de 0,035). Lo que queda tras
entrar es lo que **la misma ley** predice desde ahí, `τ·ln(F_entrada/0,5)` = 0 a 1,2 min. **F ya había decaído del 80 % al 100 % de su camino
de 0,80 a 0,50 antes de `T_RECOVERY_REGION_ENTRY`.** Ninguna de las dos cifras es un error: miden cosas distintas.

## 2 · P3-182 · Semántica de la región de recuperación
«La fisiología aguas arriba se ha recuperado lo suficiente» significa hoy, en el diseño certificado, **C**: el objetivo sistémico de F es
cero, es decir, la entrega relativa está en o por encima de `delivery_normal` del testigo (0,70 / 0,75 / 0,80). Es el suceso del propio
diseño: la región de `burden_clear_tau` se derivó «*once the signal is gone*». No es A (la entrega sólo empieza a mejorar: eso es `T_EFFECT`),
ni B (una banda 0,80–0,90 que el diseño no tiene), ni un suceso elegido para que el tiempo pase (D). **No se redefinió.**

Con cualquier otro suceso el resultado cambia de signo, y eso es lo que hace de esto una decisión y no un ajuste: contado desde que el
objetivo queda bajo F (`T_EFFECT`), F < 0,50 tarda 8–10 min (demasiado lento); contado desde la entrada (C), 0–2 min (demasiado rápido).

## 3 · P3-183 · Re-derivación de la bajada de F: qué puede y qué no puede hacer una constante
Recalculando F **fuera de línea** sobre la entrega registrada de cada corrida (exacto: F no realimenta nada, y el control reproduce la F
registrada con diferencia 0), para cada constante de bajada bajo la ley certificada:

| `burden_clear_tau` (min) | F al entrar | entrada → F < 0,50 | 0,80 → 0,50 (completa) | orden → categoría de llegada | ley aislada 0,80 → 0,50 |
|---|---|---|---|---|---|
| 6,38 (borde bajo certificado) | 0,43–0,50 | 0–1 | 6–7 | 13 | 3,0 |
| 8,5 (el propio del testigo central; sólo ese testigo) | 0,50 | 1 | 7 | 15 | 4,0 |
| 10,64 (borde alto certificado) | 0,55–0,60 | 1–2 | 7–8 | 18 | 5,0 |
| 12 | 0,57–0,62 | 2–3 | 8 | 19–20 | 5,6 |
| 14 | 0,60–0,64 | 3–4 | 9 | 22 | 6,6 |
| 16 | 0,62–0,66 | 4–5 | 9–10 | 24 | 7,5 |
| 18 | 0,64–0,68 | 5–6 | 10–11 | 26–27 | 8,5 |
| 30 | 0,70–0,73 | 11–12 | 16 | 41 | 14,1 |
| 120 | 0,78–0,79 | 54–56 | 56–57 | — | 56,4 |

**Resultado (probado en una rejilla de 6,38 a 120 min, los dos casos y los tres testigos):**
1. Dentro de la región certificada (6,38–10,64) el tiempo tras la entrada **nunca llega a 3 minutos**.
2. Las constantes que dan 3–5 min tras la entrada (≈ 12–18 según el testigo; 14–16 en los seis) están **todas fuera de la región
   certificada**, hacen entrar al paciente en 0,57–0,68 (OBNUBILADO, **no** ≈ 0,80) y sacan la ley aislada del 3–5 acordado (5,6–8,5 min).
3. **Ninguna constante** hace entrar al paciente en ≈ 0,80 **y** cruzar 0,50 en 3–5 min: para entrar en ≥ 0,75 hace falta una constante de
   decenas de minutos, y entonces el cruce tarda decenas de minutos. Bajo una relajación hacia un objetivo graduado, con una fisiología
   aguas arriba que tarda 8–9 min en recuperarse, las dos cláusulas del requisito son **incompatibles**.

### P3-183B · Caso límite: el paciente ya bajó de 0,80 antes de entrar
Es exactamente lo que ocurre, en los seis. Por tanto **no se fuerza un reloj 0,80 → 0,50 sin sentido**. El invariante, dicho en términos del
**tiempo restante de transición de categoría**, es: *dentro de la región de recuperación, el paciente deja la categoría que tiene en un tiempo
`τ·ln(F_entrada / corte inferior)`, que vale como máximo `τ·ln(0,8/0,5)` = 3–5 min (si entra en lo alto de la banda OBNUBILADO) y menos si
entra a media banda.* La región certificada lo cumple exactamente; lo que la trayectoria GI completa nunca presenta es la premisa «entra en
≈ 0,80».

Eso **refina** la especificación original («la recuperación cruza una categoría en ≈ 3–5 min», leída como 0,80 → < 0,50 en 3–5 min sin
señal) y **cambia materialmente** lo que FD-GI-02 pide de la trayectoria completa. Según el encargo, aquí se **detiene para decisión docente**.

## 4 · P3-184 · Matriz GI completa (candidato actual, sin cambios)
Las 14 series (2 casos × 7 escenarios) se repitieron sobre la cabeza actual y **reproducen el registro** (`PHASE3_GI_AMENDMENT_2_SERIES.json`)
en los 42 pares escenario×testigo, más las 6 recuperaciones con disparo propio. En cada recuperación: aguas arriba primero (orden < efecto ≤
caída del objetivo); F aguas abajo (F **sigue subiendo** en el minuto en que el tratamiento surte efecto y sólo baja cuando su objetivo ya está
por debajo); sin normalización instantánea (la categoría devuelve una banda cada vez; de la orden a la categoría de llegada pasan 13–18 min);
sin arista directa tratamiento → consciencia (F es, minuto a minuto, **exactamente** la relajación certificada hacia el objetivo de entrega:
diferencia 0 al recalcularla sólo con la entrega).

## 5 · P3-185 · No regresión
* `clinical_core/` sin cambios: digesto `a0af7d08…`, linaje `CERTIFIED`; cierre histórico y Enmienda 1 se reconstruyen. La certificación de la
  Enmienda 2 sigue siendo válida (`ALREADY_VALID_ON_EQUIVALENT_CODE`); **no** se corrió la suite completa.
* Testigos de la sombra GI = `systemic_consciousness.WITNESSES`, dentro de `REGIONS`. Subida de F, umbrales de entrega y de perfusión, cortes de
  categoría y semántica del colapso: sin tocar.
* Deterioro: inicio, secuencia y colapso son los registrados (14/14). Además, **ninguna de las dos correcciones candidatas lo movería**: antes de
  cualquier tratamiento F es idéntica bajo la ley certificada, bajo una bajada más lenta y bajo una limpieza retenida (42/42).
* Aislamiento de la sombra GI, autoridad, residente y puntuación: sin cambios (sólo se añadieron funciones de análisis al arnés de pruebas).

## 6 · P3-186 · Tabla para la docencia
**Sin tratar** (idéntico en ambos casos):

| Testigo | SOMNOLIENTO | OBNUBILADO | SIN RESPUESTA | colapso inminente | colapso establecido |
|---|---|---|---|---|---|
| LOW | 126 | 148 | 175 | 205 | 219 |
| CENTER_REFERENCE | 109 | 131 | 157 | 190 | 209 |
| HIGH | 92 | 114 | 140 | 172 | 195 |

**Recuperación** (cada testigo tratado en su primer minuto SIN RESPUESTA):

| Testigo | orden | entrada en la región | F al entrar | F < 0,50 | secuencia de categorías tras la orden |
|---|---|---|---|---|---|
| LOW | 175 | 184 (57m) / 183 (72f) | 0,43 / 0,50 | 184 (+9) | 3 → 2 en 178 → 1 en 184 → 0 en 188 |
| CENTER_REFERENCE | 157 | 166 | 0,50 | 167 (+10) | 3 → 2 en 160 → 1 en 167 → 0 en 172 |
| HIGH | 140 | 149 | 0,56 | 151 (+11) | 3 → 2 en 143 → 1 en 151 → 0 en 158 |

**Diferencias entre los dos casos GI:** ninguna sin tratar. Tratados, la transfusión mueve la entrega relativa de cada paciente según su propia
llegada (hasta 0,054 de diferencia; F hasta 0,005): **un minuto** en una entrada (LOW: 184 frente a 183) y **ninguna** diferencia en las
categorías. No es material.

## 7 · P3-187 y P3-188 · Veredicto y la única pregunta
**B · `GI_REGION_NEEDS_ONE_MORE_FACULTY_DECISION`.** La región de deterioro y de colapso es coherente; falta una decisión sobre la recuperación.

> **Pregunta a la docencia.** En una trayectoria GI completa, F empieza a limpiar en cuanto la entrega mejora (un minuto tras la orden) y la
> entrega tarda 8–9 min en volver a su región normal, de modo que el paciente **entra en la región de recuperación ya en 0,43–0,56**, no en
> ≈ 0,80. ¿Qué debe cumplir la trayectoria completa?

| Respuesta | Qué se vería | Qué cuesta |
|---|---|---|
| **(a) Limpieza graduada** (la ley y la región certificadas, sin cambio) | La consciencia mejora **durante** la reanimación: 0,80 → < 0,50 en 6–8 min, de los que 0–2 tras entrar; categoría de llegada 13–18 min tras la orden. El 3–5 queda como el tiempo de cruzar la banda entera **una vez sin señal**; el invariante de trayectoria completa pasa a ser el tiempo restante de transición (§3). | Nada. Veredicto pasaría a A. |
| **(b) Bajada más lenta** (región ≈ 12–18 min, fuera de la certificada) | 3–5 min tras entrar, entrando en 0,57–0,68; la ley aislada pasa a 5,6–8,5 min; categoría de llegada 19–27 min tras la orden. Con cristaloide solo, la mejoría transitoria **desaparece en HIGH** y se retrasa en los otros. | Cambio de `clinical_core` (`REGIONS` y `WITNESSES`) → nueva etapa sucesora y certificación completa. |
| **(c) Limpieza retenida hasta entrar** (cambio de ley: F no baja mientras el objetivo sea positivo) | Entra en ≈ 0,81 y tarda 4–6 min en bajar de 0,50 (lo que FD-GI-02 dice literalmente); categoría de llegada 16–22 min tras la orden. La reanimación **parcial deja de mejorar la consciencia**: con cristaloide solo, la mejoría transitoria desaparece en CENTER y HIGH. | Cambio de ley en `clinical_core` → nueva etapa sucesora y certificación completa. |

No recomiendo (b) ni (c) por mí mismo: ambas cambian lo que un residente vería de una reanimación parcial y eso es juicio clínico-docente.
Señalo que (a) es la única coherente con las dos decisiones ya tomadas (ley aislada de 3–5 min y FD-GI-03/04 sin tocar) y la única sin coste.

**Diseño del paquete siguiente, según la respuesta (sin ejecutarlo):**
* (a) → **Selección de la instantánea de desarrollo de GI** (elegir explícitamente un punto o conservar los tres testigos como región, con su
  procedencia y su prueba de congelación) y, después, **diseño del experimento de preparación para autoridad en sombra** (qué se mediría, con
  qué criterio de divergencia y con la frontera `UnresolvedBoundary` como bloqueo previo). Sin habilitar autoridad.
* (b) o (c) → **Enmienda sucesora de la recuperación** (un cambio declarado y reversible del núcleo, mutantes propios, la matriz de este
  documento como prueba de aceptación, y **una** certificación completa), y sólo después la instantánea.

## 8 · Decisión docente FD-P3-176: opción (a), recuperación graduada sin cambio del núcleo común (2026-11-11)
La docencia aprobó la opción (a). **No cambia nada ejecutable**: ni `clinical_core/`, ni la cinética de la Enmienda 2, ni la región de subida,
ni la región de bajada, ni la semántica relativa a la llegada, ni los cortes de categoría, ni la semántica del colapso.

**Interpretación aprobada.** La recuperación de la consciencia sistémica puede empezar de forma gradual en cuanto mejora la entrega aguas arriba.
El 3–5 min **no** es un retraso obligatorio adicional tras la entrada formal en la región de recuperación. Por tanto, para la trayectoria GI
completa:
1. La trayectoria puede mejorar de forma continua durante la reanimación.
2. Cruzar de un deterioro grave (≈ 0,80) a < 0,50 en ≈ 6–8 min desde una recuperación aguas arriba significativa es aceptable.
3. Cuando el objetivo sistémico es esencialmente nulo, la ley aislada de F conserva una escala de ≈ 3–5 min para cruzar una categoría.
4. Que queden 0–2 min tras la entrada formal es aceptable si la mayor parte de la recuperación ya ocurrió antes de entrar.

**El invariante docente que sustituye al literal de FD-GI-02** (P3-183B, ya enunciado en §3 como tiempo restante de transición) se comprueba sobre los
seis registros medidos (`test_phase3_gi_recovery_review.py`):

| Condición aprobada | Medido |
|---|---|
| 0,80 → < 0,50 en la trayectoria completa: 6–8 min | 6 / 7 / 8 min (LOW, CENTER, HIGH) en los dos casos |
| Ley aislada de F: 3–5 min | 3,0 / 4,0 / 4,9 min con las constantes de los testigos |
| 0–2 min tras la entrada, con la mayor parte ya hecha | 0–2 min; el 80–100 % del descenso se hace antes de entrar |

**Reclasificación (P3-187): A · `GI_DEVELOPMENT_REGION_READY_FOR_FACULTY_SNAPSHOT_SELECTION`.** La región de desarrollo de GI queda **lista para
que la docencia elija una instantánea**; no se eligió ninguna. Esto **no es validación clínica** y **no autoriza autoridad en tiempo de ejecución**
(`COMMON_CORE_RUNTIME_AUTHORITY = False`). Los escenarios (b) y (c) de §7 quedan descartados por la docencia y siguen sin existir en el núcleo ni
en la capa; el barrido fuera de línea se conserva en el registro sólo como evidencia de la decisión.

**Paso siguiente (sin ejecutar; requiere un encargo nuevo):** diseño de la **selección de la instantánea de desarrollo de GI** y, después, diseño del
**experimento de preparación para autoridad en sombra** (§7, respuesta (a)); `UnresolvedBoundary` sigue siendo un bloqueo para una autoridad futura.
