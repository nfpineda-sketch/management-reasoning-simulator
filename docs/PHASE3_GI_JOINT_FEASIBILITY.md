# Fase 3 · Resolución conjunta tasa × presión de GI con las anclas docentes de sangre y de cristaloide lento (P3-326 a P3-336, 2026-11-15)

> **Intersección (P3-329A): `NONEMPTY`.**
> **Compuerta de Enmienda 3 (P3-335): `A · CURRENT_PHYSIOLOGY_HAS_FEASIBLE_JOINT_REGION`. No se abre la Enmienda 3; no se escribió ningún diseño.**
> **Condición del veredicto:** vale con la ventana de glóbulos leída al **minuto 30** (fin de la unidad). Si el piso de +8 mmHg se exigiera **ya al minuto 15**, la intersección con
> la región de cristaloide cerrada sería **`EMPTY`** (§5, punto 7). **Requiere tu confirmación de la lectura.**
> **No se eligió ningún punto, no se aprobó ninguna tasa ni ningún parámetro, y nada ejecutable cambió.**

Rama `phase-3-runtime-integration`. **Ciclo de factibilidad e identificabilidad, sólo lectura** (`MODEL_ANALYSIS`): `gi_joint_feasibility_analysis.py`, registro
`docs/revision/PHASE3_GI_JOINT_FEASIBILITY_ANALYSIS.json`, pruebas `test_phase3_joint_feasibility.py`. No cambia `clinical_core/` (el digesto vivo sigue siendo el certificado
`a0af7d08…`), ni `family_engine.py`, ni la instantánea `gi_pressure_committed`, ni la autoridad, ni la región de cristaloide cerrada. Los juicios humanos de la primera revisión quedan
**exactamente** como estaban (registro `9ba80fa7…`). Sin norepinefrina, sin control de fuente nuevo, sin validación clínica: todas las cifras son **lecturas del modelo**, no afirmaciones
clínicas.

Continúa `docs/PHASE3_GI_BLEED_RATE_SCALE.md` (P3-314 a P3-325), que dejó planteada la pregunta que este ciclo responde. `FD-BLD-0x` significa aquí **siempre** la restricción docente
congelada de `clinical_core/blood_constraints.py`; las decisiones nuevas son `FD-RATE-*`, nombre que **confirmaste** en este encargo («Use FD-RATE-* naming»).

---

## §0 · Decisiones docentes registradas

| Id | Decisión | Estado |
|---|---|---|
| **FD-RATE-09** | Ancla de respuesta a glóbulos: en los dos casos de GI redactados, con el sangrado **temporalmente controlado** y sin otra intervención de volumen simultánea, **una unidad** debe subir la PAS **≈ +8 a +18 mmHg en ≈ 15–30 min simulados**. Invariantes: +25 a +30 mmHg de una unidad es **demasiado** para el comportamiento de desarrollo por omisión; la respuesta **no** es instantánea; una unidad sola **no** normaliza todas las variables de perfusión. | `FACULTY_DEFINED_DEVELOPMENT_BEHAVIORAL_REGION`. No es regla clínica universal, ni de producción, ni visible al residente. No se elige un punto dentro de +8…+18. |
| **FD-RATE-10** | Cristaloide lento: 1 L de SF en 60 min **durante hemorragia activa** debe atenuar sólo **modestamente** al minuto 60: región operativa de desarrollo ≈ **15–35 % del deterioro de presión sin tratar evitado**. | La misma clase. No es un objetivo de calibración clínica exacto; no se ajusta una trayectoria en mmHg. |
| **FD-RATE-11** | No se aprueba ningún punto absoluto de tasa. `bleed_ml_per_min` sigue `UNRESOLVED_ABSOLUTE_SCALE` hasta que la región conjunta quede acotada. | Vigente. |
| **FD-RATE-12** | La región histórica **cerrada** de cristaloide **no** se modifica todavía; primero se prueba si las tres restricciones tienen intersección con la fisiología actual. | Vigente; no se tocó. |
| **FD-RATE-13** | La Enmienda 3 se justifica **sólo** si la fisiología común actual no puede cumplir a la vez A (deterioro sin tratar), B (una unidad +8…+18 mmHg) y C (1 L/60 min evita ~15–35 %). | Aplicada en §11: la intersección no es vacía → no se abre. |

## §1 · P3-326 · Publicación de P3-315 → P3-325

Dos commits, como se autorizó: `7ae5c9b` (análisis y pruebas) y `9e8278b` (documentos y registros). El árbol del `HEAD` es **idéntico** al candidato verificado
(`6e64e945b2c0ed1ff54d61196d926271c3a1338c`). `fetch` sin divergencia (0 / 0), push normal a `origin/phase-3-runtime-integration`; sin PR, sin push forzado. **La autorización cubría sólo
esa publicación: el trabajo de este ciclo (P3-327 a P3-336) queda en el árbol de trabajo, sin commit.**

## §2 · P3-327 · Qué hace exactamente una unidad de glóbulos

Lectura con el sangrado **contrafactualmente en 0 mL/min** (sólo para esta ancla; en ningún otro escenario se detiene el sangrado), llegada real de la página, una unidad, punto de ejecución actual.

| Eslabón | Qué ocurre | Cifra (72f, punto actual) |
|---|---|---|
| Contribuyente | `PackedRedCells`: 1 unidad = **300 mL-eq a 20 g/dL**, sin duración declarada → **1/30 de unidad por minuto** | 10 mL-eq/min durante 30 min |
| Volumen de sangre / volumen eficaz | El volumen entra **entero** al estado de sangre: es un solo canal (`ΔV`), el mismo que usa el cristaloide retenido | +50 / +150 / +300 mL-eq a los 5 / 15 / 30 min; plano después |
| Masa de Hb | Mezcla: `Hb = (Hb₀·V₀ + 20·v)/(V₀ + v)` | 6,40 → 7,35 g/dL (57m: 6,70 → 7,63) |
| Precarga | Posición sobre la curva: `1 − (1−f)·e^{−κ·ΔV/escala}` | 0,500 → 0,582 → 0,651 |
| Flujo anterógrado | Proporcional a la posición (`P ≡ 1`) | 1,000 → 1,165 → 1,302 |
| Presión | `PAS = PAS_llegada · g(ΔV)`, tono `T ≡ 1` | 98 → 114,1 → 127,6 mmHg |

Forma cerrada: **`ΔPAS = PAS_llegada · (1−f)(1 − e^{−κ·V_unidad/escala})/f`**; coincide con la corrida a 1e-9. En el punto actual da **+26,6 mmHg (57m) y +29,6 mmHg (72f)**: por
FD-RATE-09 eso es **demasiado**. La frecuencia cardiaca en sombra no se mueve (124 / 112): no es informativa en esta lectura y no se reporta como hallazgo.

## §3 · P3-327A · Tiempo de la respuesta

- Clase: **`FINITE_DURATION_INFUSION`**. No es instantánea: la unidad entra lineal en 30 minutos y la respuesta termina con ella (nada después del minuto 30).
- Al minuto 15 hay la mitad del volumen y **54,5 %** de la respuesta de presión (la curva es cóncava).
- **Mapa de la ventana docente (≈ 15–30 min):** se lee al **minuto 30**, el final de la unidad por omisión, donde está toda la respuesta; el minuto 15 se reporta al lado.
  **No se cambió la semántica de la infusión.**

## §4 · P3-328 · Reducción: tres restricciones, tres coordenadas

| Restricción | Lee sólo | Comprobación |
|---|---|---|
| **A · sin tratar** | `c = tasa/escala` (con la posición de llegada `f`) | Invariante a 1,6e-13 mmHg al escalar tasa y escala juntas (P3-319) |
| **B · una unidad** | `escala` (con `f`): `V_unidad·κ/escala` | A escala 2000: +13,6506 mmHg con y sin cambio de núcleo de cristaloide |
| **C · cristaloide lento** | `q = retenido a 60 min / sangre perdida en 60 min` → **tasa y núcleo, no el mapa** | A 8 mL/min sobre cuatro mapas: 0,345 / 0,331 / 0,328 / 0,331 (dispersión 0,016) |

Coordenadas libres: `tasa`, `escala`, el retenido del núcleo a 60 min (dentro de la región cerrada) y `f` (0,5 comprometida; 0,4 como sensibilidad). **A acota `c`, B acota `escala`,
C acota `c·escala/R60`.**

**Acoplamiento sangre–cristaloide.** Los dos actúan por el mismo volumen eficaz, así que la fracción que evita el litro lento es un **múltiplo fijo** de la ganancia de una unidad:
≈ **3,1–3,2 ×** con el núcleo menos protector de la región cerrada (retiene 134,6 mL = 0,449 de unidad a los 60 min) y ≈ 1,9–2,0 × con el núcleo de ejecución (81,9 mL = 0,273 de
unidad; **fuera** de la región cerrada). Cambiar la escala mueve a los dos juntos.

## §5 · P3-329 y P3-329A · Región de factibilidad

Analítico primero, luego testigos dispersos y bisección; sin rejilla densa. Posición de llegada compartida `f = 0,5`.

| Restricción | Región (ambos casos) | Qué la limita |
|---|---|---|
| **A** (envolventes docentes `U-OUT`) | `c` ∈ **[0,0030596; 0,0033646]** | 57m por abajo, 72f por arriba |
| **B** (+8…+18 mmHg) | escala 57m [1311; 3148], 72f [1478; 3523] → común **[1478,3; 3147,6] mL-eq** | menor escala: +18 en 72f; mayor escala: +8 en 57m |
| **A × B** | tasa ∈ [4,52; 10,59] mL-eq/min | — |
| **C** (15–35 %), núcleo menos protector de la **región cerrada** | escala **[2258,3; 3147,6]**, tasa **[7,60; 10,59]**, fracción evitada [0,253; 0,35] | menor escala: el techo de 35 %; mayor escala: el piso de +8 mmHg |

**Estado: `NONEMPTY`.** Con **todas** las restricciones existentes legibles y cumplidas (evaluador docente congelado: `U-OUT`, `U-HB`, `FD-BLD-01` a `FD-BLD-09`, `SECOND-UNIT`):

> **tasa ∈ [7,598; 9,326] mL-eq/min · escala ∈ [2258,3; 3048,0] mL-eq · núcleo dentro de la región cerrada · `c` ∈ [0,003060; 0,003365].**

Proyecciones: una unidad sube **+8,0 a +10,9 mmHg (57m)** y **+8,9 a +12,2 mmHg (72f)**; el litro lento evita **25,3 a 35 %**; el retenido a 60 min compatible es **[134,6; 187,6] mL**.

Lo que hay que leer junto con ese «no vacío»:

1. **Límite de legibilidad, no de fallo.** Por encima de **9,326 mL-eq/min** el evaluador congelado **no puede leer** `FD-BLD-06` en 57m (su lectura de 140 minutos llega a la frontera
   del núcleo antes de terminar). Es `UNREADABLE`, no incumplida; entre 9,33 y 10,59 las tres anclas se cumplen, pero no se cuenta como verificado.
2. **Fuera de la banda declarada.** La región entera queda **por encima** de la banda `CANDIDATE` de `preload_curve_scale_ml` [600; 1500]: su menor escala es **1,506 ×** el tope. Dentro
   de la banda, con un núcleo de la región cerrada, la intersección es **`EMPTY`** (la mejor fracción alcanzable es 0,519). La banda es un dominio declarado, no evidencia.
3. **Tres a casi cuatro veces la referencia histórica.** 7,60–9,33 mL-eq/min es **3,04–3,73 ×** los 2,5 de referencia. El punto de ejecución (2,5; 833,33) **no cumple ninguna** de las
   dos anclas nuevas (+26,6 / +29,6 mmHg; 63 % evitado).
4. **Sólo la parte menos retentiva de la región cerrada.** El mayor `e` compatible es 0,2812 (la fibra recorrida va de 0,2017 a 0,3151): se usa el **53,3 %** del tramo de retención de la
   región cerrada; su núcleo más retentivo (234,0 mL a 60 min) es **incompatible** con las tres anclas.
5. **Sensibilidad `f = 0,4`:** misma respuesta. `c` ∈ [0,002138; 0,002278], escala [3271; 4798], tasa [7,45; 10,93] → `NONEMPTY`. La tasa factible casi no depende de `f`; la escala sí.
6. **Con el núcleo de ejecución** (sólo información: está fuera de la región cerrada, incumple `FD-BLD-04` y `FD-BLD-05`): escala [1478; 3148], tasa [4,97; 10,59].
7. **El resultado depende de cómo se lee la ventana de 15–30 min.** La lectura declarada (§3) toma los dos bordes al minuto 30. Con la lectura **más estricta** — piso de +8 mmHg ya
   presente al **minuto 15** (media unidad dentro), techo de +18 al minuto 30 — la región de una unidad se reduce a escala **[1478; 1574] mL-eq** (una unidad completa valdría
   +15,3 a +16,2 mmHg en 57m y +17,0 a +18,0 en 72f) y con un núcleo de la región cerrada el litro lento evitaría **49,6–57,4 %**: intersección **`EMPTY`**. Con el núcleo de ejecución
   (fuera de la región cerrada) seguiría `NONEMPTY` (tasa [4,82; 5,30]). El veredicto A **no sobrevive** a esa lectura; por eso se pide confirmarla (§12).

## §6 · P3-330 · Serie de una unidad en los testigos

Tres testigos de la región verificada, núcleo menos protector de la región cerrada. **Ninguno es un punto elegido** (`is_a_chosen_point = False`); cada uno cumple las tres anclas, los
invariantes y todas las restricciones existentes en los dos casos.

| Testigo | Tasa (mL-eq/min) | Escala (mL-eq) | `c` | Por qué está ahí |
|---|---|---|---|---|
| **LOW** | 7,60 | 2270 | 0,003348 | Menor escala, curso sin tratar más rápido admitido: la mayor respuesta a una unidad de la región; fracción en el techo de 35 % |
| **CENTER** | 8,40 | 2617 | 0,003208 | Medio geométrico de las escalas y de los cursos admitidos |
| **HIGH** | 9,28 | 3018 | 0,003075 | Mayor escala legible, curso más lento admitido (el más cercano al aceptado): una unidad cerca del piso de +8 en 57m |

Llegada, sangrado controlado, una unidad. PAS/PAD (PAM) en mmHg:

| Testigo | Caso | 0 min | 5 min | 15 min | 30 min | ΔPAS a 15 / 30 | Hb 0 → 30 | Llenado capilar 0 → 30 (s) | Lactato 0 → 30 |
|---|---|---|---|---|---|---|---|---|---|
| LOW | 57m | 88,0/54,0 (65,3) | 89,9/55,2 (66,8) | 93,6/57,5 (69,5) | 98,9/60,7 (73,4) | +5,6 / **+10,9** | 6,70 → 7,63 | 5,0 → 4,5 | 4,4 → 4,4 |
| LOW | 72f | 98,0/62,0 (74,0) | 100,1/63,4 (75,6) | 104,3/66,0 (78,7) | 110,1/69,7 (83,2) | +6,3 / **+12,1** | 6,40 → 7,35 | 4,0 → 3,5 | 3,4 → 3,4 |
| CENTER | 57m | 88,0/54,0 (65,3) | 89,7/55,0 (66,6) | 92,9/57,0 (69,0) | 97,5/59,8 (72,4) | +4,9 / **+9,5** | 6,70 → 7,63 | 5,0 → 4,6 | 4,4 → 4,4 |
| CENTER | 72f | 98,0/62,0 (74,0) | 99,9/63,2 (75,4) | 103,5/65,5 (78,1) | 108,6/68,7 (82,0) | +5,5 / **+10,6** | 6,40 → 7,35 | 4,0 → 3,6 | 3,4 → 3,4 |
| HIGH | 57m | 88,0/54,0 (65,3) | 89,4/54,9 (66,4) | 92,3/56,6 (68,5) | 96,3/59,1 (71,5) | +4,3 / **+8,3** | 6,70 → 7,63 | 5,0 → 4,6 | 4,4 → 4,4 |
| HIGH | 72f | 98,0/62,0 (74,0) | 99,6/63,0 (75,2) | 102,8/65,0 (77,6) | 107,3/67,9 (81,0) | +4,8 / **+9,3** | 6,40 → 7,35 | 4,0 → 3,6 | 3,4 → 3,4 |

Volumen eficaz: +50 / +150 / +300 mL-eq en todos (no depende del testigo). FC en sombra: 124 → 124 y 112 → 112 (no informativa; sin autoridad). **No instantánea** (creciente hasta el
minuto 30), **por debajo de la marca de «demasiado»**, y **no normaliza la perfusión**: el lactato sigue sobre 2,0 y el llenado capilar no baja a la mitad del de llegada.

## §7 · P3-331 · Serie del cristaloide lento en los mismos testigos

1 L de SF en 60 min, orden real del FR-G en los dos casos, **sangrado activo en todos los minutos** a la tasa del testigo (un solo valor distinto por corrida).

| Testigo | Caso | Deterioro sin tratar a 60 (mmHg) | Deterioro tratado a 60 (mmHg) | % evitado a 30 / **60** / 70 / 120 | Cristaloide retenido a 60 (mL) | Sangre perdida a 60 (mL) | Balance neto de volumen eficaz a 60 (sin tratar) |
|---|---|---|---|---|---|---|---|
| LOW | 57m | 17,3 | 11,3 | 39 / **35** / 27 / 10 | 134,6 | 456 | −273 (−408) |
| LOW | 72f | 19,3 | 12,5 | 39 / **35** / 27 / 10 | 134,6 | 456 | −273 (−408) |
| CENTER | 57m | 16,5 | 11,3 | 35 / **32** / 24 / 9 | 134,6 | 504 | −316 (−451) |
| CENTER | 72f | 18,4 | 12,6 | 35 / **32** / 24 / 9 | 134,6 | 504 | −316 (−451) |
| HIGH | 57m | 15,8 | 11,3 | 32 / **29** / 22 / 8 | 134,6 | 557 | −364 (−498) |
| HIGH | 72f | 17,6 | 12,6 | 32 / **29** / 22 / 8 | 134,6 | 557 | −364 (−498) |

El efecto **se desvanece** tras la infusión (8–10 % a los 120 min) y el paciente tratado **sigue deteriorándose** (11–13 mmHg bajo la llegada a los 60 min). El ancla docente se lee al
minuto 60; el minuto 30 se muestra como información (medio litro dentro) y no tiene ancla.

## §8 · P3-332 · Curso sin tratar

PAS a 60 / 120 / 180 min (entre paréntesis, el curso aceptado en FR-A y FR-D con el punto actual). No se pide el mmHg histórico exacto, sólo la clase de severidad.

| Testigo | 57m (aceptado 73 / 58 / 43) | 72f (aceptado 81 / 64 / 48) |
|---|---|---|
| LOW | 71 / 54 / 37 | 79 / 60 / 41 |
| CENTER | 71 / 55 / 40 | 80 / 62 / 44 |
| HIGH | 72 / 57 / 42 | 80 / 64 / 47 |

En todos: deterioro **progresivo**, envolventes `U-OUT` cumplidas, orden de casos preservado (57m por debajo de 72f), sin frontera del núcleo antes de 180 min, y a menos de 8 mmHg del
curso aceptado en cada lectura. Caída de Hb a 120 min: 0,30–0,39 g/dL (`U-HB` cumplida).

## §9 · P3-333 · Intersección

**Una sola región de familia** sirve a los dos casos; **no** se introdujo ningún parámetro por caso (la evidencia redactada no lo exige). Los tres testigos cumplen A, B, C, los
invariantes de FD-RATE-09 y cada restricción existente. Anchura de identificación dentro de la región verificada: tasa **× 1,23**, escala **× 1,35** — estrecha, no débilmente
identificada.

## §10 · P3-334 · Auditoría estructural

**Por qué no es vacía.** Las dos ventanas docentes son lo bastante anchas para solaparse sobre la única línea que la fisiología permite: con un núcleo de la región cerrada, la fracción
que evita el litro lento es ≈ 3 × la ganancia de una unidad, así que una unidad de +8 a ≈ +12 mmHg (72f) va con una fracción de ≈ 25 a 35 %.

**Pero es una esquina.** Usa la parte **baja** de la ventana de glóbulos (+8,9…+12,2 de +8…+18), la parte **alta** de la de cristaloide (0,253…0,35 de 0,15…0,35) y sólo la mitad menos
retentiva de la región cerrada. Los **centros** de las dos ventanas (+13 mmHg → escala 2108; 25 %) **no** son compatibles con un núcleo de la región cerrada (daría 37–41 %); sí con uno
que retenga tan poco como el de ejecución (23–25 %), que está **por debajo del piso** de la región cerrada.

Subconjuntos casi contradictorios (los tres **vacíos**):

| Subconjunto | Lectura |
|---|---|
| B en su extremo de +18 mmHg + C + región cerrada | Una unidad que valga +18 mmHg en 72f deja un litro lento evitando **52,6 %** aun con el núcleo menos protector |
| Banda `CANDIDATE` declarada de la escala + B + C + región cerrada | Dentro de la banda no hay punto; la banda es dominio declarado, no evidencia |
| Núcleo más retentivo de la región cerrada + A + B + C | La mitad más retentiva de la región cerrada es incompatible con las tres anclas |

| Causa estructural | ¿Presente? | ¿Vacía la intersección? | Cuantificación |
|---|---|---|---|
| **A** · un solo canal de volumen eficaz, demasiado rígido | Sí | **No** | Un litro lento vale 0,27 (ejecución) a 0,45 (región cerrada, mínimo) de una unidad a los 60 min; B y C se mueven juntos: es lo que convierte la región en esquina |
| **B** · el núcleo de retención no depende de la velocidad de infusión | Sí | **No** | Núcleo invariante en el tiempo (P3-303): el litro lento retiene **más** a su propio final que un bolo al mismo minuto; estrecha, no vacía |
| **C** · el mapa de presión no puede representar a la vez sin tratar y transfusión | **No** | — | A fija `tasa/escala` y B fija `escala`, en coordenadas separadas |
| **D** · otro mecanismo | No | — | — |

## §11 · P3-335 · Compuerta de la Enmienda 3

**`A · CURRENT_PHYSIOLOGY_HAS_FEASIBLE_JOINT_REGION`.** Las ecuaciones actuales cumplen a la vez las envolventes sin tratar, la región de una unidad y la región del cristaloide lento, con
todas las restricciones existentes y un núcleo **dentro** de la región cerrada. Por FD-RATE-13, **no se abre la Enmienda 3**; no se diseñó (P3-335A no aplica) ni se implementó nada.

**Condición.** El veredicto es para la lectura declarada de la ventana (efecto de la unidad leído al minuto 30). Con la lectura más estricta de §5 (7) el estado con la región cerrada
sería `EMPTY` y la compuerta daría `C`, o bien habría que reabrir la región cerrada; el análisis **no** decide cuál lectura es la docente.

Por qué no las otras: **B** — cada coordenada queda identificada dentro de un factor ≈ 1,2–1,4; **C** — la intersección no es vacía; **D** — el mapa de presión sostiene los dos
comportamientos en coordenadas separadas; **E** — las tres anclas y las restricciones existentes bastan para decidir.

Lo que cuesta esa región (no es un «todo listo»):

1. Queda **entera sobre la banda `CANDIDATE`** declarada de la escala y a **3–3,7 ×** la tasa histórica de referencia.
2. Es una **esquina**: parte baja de la ventana de glóbulos, parte alta de la de cristaloide, parte menos retentiva de la región cerrada.
3. El punto actual no cumple ninguna de las dos anclas nuevas; en cualquier punto factible **todas** las trayectorias tratadas cambian de magnitud, así que FR-B, FR-C, FR-E y FR-G
   necesitarían una **nueva revisión humana ciega**. Su aceptación actual no se transfiere.
4. Aplicar cualquier punto exige una **instantánea de presión nueva** y un **sucesor certificado del núcleo**: la tasa se calcula dentro de `clinical_core/legacy_adapter.py` y la banda
   de la escala se declara en `clinical_core/calibration.py`. Además, el núcleo de cristaloide de ejecución está hoy **fuera** de la región cerrada. Nada de eso se hizo ni se diseñó.

## §12 · P3-336 · Punto de control

`docs/revision/PHASE3_JOINT_FEASIBILITY_CHECKPOINT.json`.

| Estado | Valor |
|---|---|
| `PRBC_RESPONSE_REGION` | +8…+18 mmHg (docente, desarrollo); lee sólo la escala → [1478,3; 3147,6] mL-eq; el punto actual da +26,6 / +29,6 (demasiado) |
| `SLOW_CRYSTALLOID_REGION` | 15–35 % (docente, desarrollo); lee tasa y núcleo, no el mapa; alcanzable 25,3–35 % con la región cerrada; el punto actual da 63 % |
| `UNTREATED_REGION` | `U-OUT`: `tasa/escala` ∈ [0,003060; 0,003365]; progresivo, orden de casos, misma clase de severidad que FR-A/FR-D |
| `JOINT_IDENTIFIABILITY` | Tres coordenadas (A → `c`, B → escala, C → tasa × núcleo); tasa × 1,23 y escala × 1,35: no débil |
| `INTERSECTION_STATUS` | **`NONEMPTY`** (lectura declarada, minuto 30): tasa [7,598; 9,326], escala [2258,3; 3048,0], núcleo en la región cerrada; también en `f = 0,4`; `EMPTY` dentro de la banda declarada y `EMPTY` con la lectura estricta (piso al minuto 15) |
| `STRUCTURAL_CONFLICT` | Ninguno que vacíe la intersección; el canal único de volumen la vuelve esquina; el núcleo invariante la estrecha; el mapa de presión no está implicado |
| `AMENDMENT3_STATUS` | **No justificada, no abierta, sin diseño** (condicionada a la lectura de la ventana) |

**Decisión docente y de arquitectura que sigue** (no la toma este análisis):

0. **Docente (primero, porque condiciona el veredicto):** en FD-RATE-09, ¿«+8 a +18 mmHg en ≈ 15–30 min» es el efecto de la unidad **completa**, que termina de entrar al minuto 30
   (lectura usada aquí), o el piso de +8 mmHg debe verse **ya al minuto 15**? Con la segunda, la intersección con la región cerrada es vacía.
1. **Docente:** ¿es aceptable para el desarrollo la **esquina** que la fisiología actual permite — una unidad ≈ +8 a +12 mmHg con el litro lento evitando ≈ 25–35 % — o se quiere el
   **centro** de las dos ventanas (≈ +13 mmHg y ≈ 25 %)? El centro sólo existe con un núcleo que retenga **menos** que el piso de la región cerrada: eso sería **reabrir la región
   cerrada** (FD-RATE-12), no una Enmienda 3.
2. **Docente:** ¿es aceptable como escala de **desarrollo** para estos dos casos una pérdida de 7,6–9,3 mL-eq/min (≈ 455–560 mL-eq por hora)? (Lectura del modelo, no dato clínico.)
3. **Arquitectura:** si se quiere un candidato conjunto, autorizar (a) extender la banda `CANDIDATE` de la escala más allá de 1500 mL-eq, (b) el camino de la tasa (sucesor certificado
   del núcleo o tasa desde la instantánea), (c) mover el núcleo de cristaloide dentro de la región cerrada, y (d) la nueva revisión humana ciega de todas las trayectorias tratadas.

Hasta entonces: `bleed_ml_per_min` sigue `UNRESOLVED_ABSOLUTE_SCALE`, no existe `FR-G_V2_CANDIDATE`, y el FR-G sigue en `RECALIBRATE`. **STOP.**

## §13 · Límites

- Todo es `MODEL_ANALYSIS`: propiedades de las ecuaciones actuales frente a regiones docentes de **desarrollo**. No hay validación clínica ni la IA actúa como estándar de referencia.
- Las anclas FD-RATE-09 y FD-RATE-10 son «aproximadas» por redacción; aquí se usaron como intervalos cerrados [8; 18] mmHg y [0,15; 0,35]. Mover un borde mueve la región (p. ej. un
  techo de 30 % en vez de 35 % sube la menor escala factible).
- La ventana de 15–30 min se leyó al minuto 30. La lectura alternativa (piso ya al minuto 15) **vacía** la intersección con la región cerrada: está medida en §5 (7) y es la
  principal condición del veredicto. No se probó una unidad más rápida que 30 min (sería cambiar la semántica de la infusión).
- `f` se mantuvo en 0,5 (comprometida) con 0,4 como sensibilidad; no se recorrió toda la banda por caso.
- La fibra de núcleos recorre `e` con `s` y `τ` del núcleo menos protector; no es toda la región cerrada, aunque sí cubre su tramo de retención a 60 min.
- El umbral de «débilmente identificada» (anchura > × 3) y el de «numéricamente ambigua» (< 1 %) son convenciones operativas de este análisis, no decisiones docentes.
- El límite de 9,326 mL-eq/min es de **legibilidad** del evaluador congelado, que no se modificó.
- Una persona revisora, un escenario (FR-G) y un caso dieron origen a la pregunta; las anclas nuevas son de la docencia, no de esa revisión.
