# Fase 3 · Región conjunta de GI formalizada y paquete para la re-revisión humana ciega (P3-337 a P3-348, 2026-11-15)

> **Punto de control (P3-348): `A · JOINT_REGION_READY_FOR_BLINDED_HUMAN_REREVIEW`.**
> **Banda antigua de la escala (P3-338): `A · PURE_CANDIDATE_ANALYSIS_BAND`** → marcada `SUPERSEDED_BY_JOINT_FEASIBILITY_ANALYSIS` para el análisis conjunto, sin reescribir nada.
> **No se eligió ningún punto como calibración, no se aprobó ningún parámetro, la Enmienda 3 sigue cerrada y nada ejecutable cambió.**
> **Hallazgo aparte (§11):** tres guardas de aislamiento estaban **rojas en la rama publicada** desde `388f279` por los módulos de análisis de los tres ciclos anteriores. Reparado sin tocar ninguna guarda; su publicación, en un commit propio, se autorizó después condicionada a una certificación completa (FD-P3-239).

Rama `phase-3-runtime-integration`. **Sólo lectura y análisis** (`MODEL_ANALYSIS`): `test_gi_joint_region.py` (arnés del lado de pruebas), registro `docs/revision/PHASE3_GI_JOINT_REGION_V1.json`, pruebas
`test_phase3_joint_region.py`. No cambia `clinical_core/` (digesto vivo = `a0af7d08…`), ni `family_engine.py`, ni la instantánea `gi_pressure_committed`, ni la concesión, ni la región
de cristaloide cerrada, ni la pantalla de revisión. La revisión humana anterior queda **exactamente** como estaba (`9ba80fa7…`). Todas las cifras son lecturas del modelo en
mL-equivalentes: **no** son una pérdida de sangre medida clínicamente ni una validación clínica.

Continúa `docs/PHASE3_GI_JOINT_FEASIBILITY.md` (P3-326 a P3-336).

---

## §0 · Decisiones docentes registradas (FD-RATE-14 a FD-RATE-20)

| Id | Decisión | Qué se hizo con ella |
|---|---|---|
| **FD-RATE-14** | La región +8…+18 mmHg se refiere a la respuesta tras **una unidad completa**; con la infusión actual de 30 min, hacia el minuto 30. Al minuto 15 se espera una respuesta **parcial monótona**, sin exigir el piso de +8. **La lectura anterior queda confirmada.** | La ventana de una unidad de la región es la misma del análisis de factibilidad, sin cambio. Cierra la condición del veredicto de P3-335. |
| **FD-RATE-15** | Que la región factible quede cerca de bordes de las ventanas **no** la invalida; las ventanas son regiones y sus centros **no** son objetivos. | Nada se optimiza hacia +13 mmHg ni 25 %. `CENTER_REFERENCE` es el punto más lejos de **toda frontera**, no el centro de una ventana. |
| **FD-RATE-16** | Se acepta `CURRENT_PHYSIOLOGY_HAS_FEASIBLE_JOINT_REGION` como resultado **estructural**; no es un punto calibrado ni validado clínicamente. | Estado de la región: `JOINT_DEVELOPMENT_REGION__NOT_A_CALIBRATED_POINT__NOT_CLINICALLY_VALIDATED`. |
| **FD-RATE-17** | El intervalo ≈ 7,60–9,33 mL-eq/min es parte de una **región conjunta de desarrollo** sólo junto con su escala compatible; no es tasa medida clínicamente; no se elige una tasa sola. | La tasa **no es una coordenada**: un punto es `(c, escala, núcleo)` y la tasa es siempre `c × escala` (§3). |
| **FD-RATE-18** | Auditar la banda `CANDIDATE` [600; 1500]; si es sólo análisis candidato, marcarla `SUPERSEDED_BY_JOINT_FEASIBILITY_ANALYSIS` sin reescribir evidencia histórica; si tiene estado más fuerte, parar. | §2: veredicto A; marcada. |
| **FD-RATE-19** | La Enmienda 3 sigue **cerrada**. | Ni diseño ni implementación. |
| **FD-RATE-20** | Antes de adoptar cualquier configuración conjunta: nuevas trayectorias candidatas **ciegas** para FR-B, FR-C, FR-E y FR-G. Los juicios humanos originales se conservan y **no** se transfieren. | §6 a §8. |

## §1 · P3-337 · Publicación de P3-327 → P3-336

Dos commits, como se autorizó: `32bb4a5` (análisis y pruebas) y `ddfca36` (documentos y registros). `fetch` antes del commit y antes del push, sin divergencia; árbol del `HEAD`
idéntico al candidato verificado (`eb258e83…`); push normal, sin PR ni push forzado. La autorización de entonces cubría sólo esa publicación; la de este ciclo llegó después (FD-P3-239).

## §2 · P3-338 · La banda antigua [600; 1500] mL-eq

**Veredicto: `A · PURE_CANDIDATE_ANALYSIS_BAND`.**

| Qué | Evidencia |
|---|---|
| Dónde vive | `clinical_core/calibration.py`, `REGISTRY["preload_curve_scale_ml"]`: inferior 600, canónico 833,33, superior 1500, estado **`CANDIDATE`** |
| Cuándo entró | Commit `b4040ba` (2026-10-23), «P2F-2..11: GI truth, **candidate bands**, registry…»; su mensaje cuenta el registro: `FACULTY_APPROVED 0` |
| Estado más fuerte disponible | El registro tiene el estado `FACULTY_APPROVED` y **ninguna** de sus 58 entradas lo lleva (hoy `CANDIDATE` 52, `DEFAULT_UNMAPPED` 4, `SYNTHETIC_ONLY` 2) |
| Qué aprobó la docencia | Un **punto** (833,33, con los otros seis valores de `gi_pressure_committed`) y sólo para el experimento de presión de desarrollo (FD-P3-42): «aprobar el punto no es aprobar la verdad clínica de cada magnitud». Nunca la banda |
| Procedencia del canónico | La razón declarada es que «mantiene la pendiente del legado» (FD-P3-61): reconstrucción heredada, no evidencia clínica |
| ¿Decisión docente, restricción congelada o validador que la exija? | No, no y no. Las filas que nombraban la escala (FD-P3-39, 42, 58, 59, 61) no definen la banda |
| Quién la lee | Barridos de exploración; los testigos de sombra de las esquinas de la región declarada (FD-P3-13), que no cambian; las sondas del propio núcleo, que ya exploraron hasta **3000** («explored, never approved»); y el evaluador congelado de sangre, que **lee** la hemoglobina en un estado fijo de escala 1500 (convención de lectura, no restricción) |

**Supersesión.** La banda queda marcada **`SUPERSEDED_BY_JOINT_FEASIBILITY_ANALYSIS`** sólo para el análisis conjunto actual: deja de leerse como dominio de la región. Se registra aquí,
en el Decision File y en la deuda. **El registro del núcleo no se edita** (sigue diciendo `CANDIDATE [600, 1500]`): vive en `clinical_core/`, cuyo digesto certificado cubre todas sus
fuentes; llevar la marca ahí exigiría un sucesor certificado. No se reescribe evidencia histórica.

## §3 · P3-339 · La región como objeto

`GI_JOINT_RATE_PRESSURE_DEVELOPMENT_REGION_V1` — clase `test_gi_joint_region.JointRegion`. **No** es un punto calibrado, ni un conjunto aprobado, ni rangos escalares independientes.

Coordenadas mínimas, en la posición de llegada comprometida 0,5: **`c = tasa/escala`**, **`escala`** y el **núcleo de cristaloide `(e, s, τ)`**. La tasa nunca es coordenada: `tasa = c × escala`.

| Restricción | Regla de pertenencia | Fuente |
|---|---|---|
| **A · sin tratar** | `0,003060 ≤ c ≤ 0,003365` | Envolventes docentes `U-OUT` congeladas, los dos casos |
| **B · una unidad completa** | `1478,3 ≤ escala ≤ 3147,6` mL-eq (+8…+18 mmHg a 30 min, los dos casos) | FD-RATE-09 con FD-RATE-14 |
| **C · cristaloide lento** | `0,15 ≤ fracción(c × escala, escala, núcleo) ≤ 0,35` | FD-RATE-10. **Acopla las tres coordenadas** |
| **K · región cerrada** | Rpico, R30, R60 y R120 del núcleo dentro de sus envolventes | `volume_behaviour_record.EFFECTIVE_REGION`, sin tocar (FD-RATE-12) |
| **R · restricciones existentes** | Todas legibles y cumplidas; en la práctica `c × escala ≤ 9,326` | `clinical_core.blood_constraints`, sin tocar |

**Por qué no son rangos.** Un punto con la tasa de `LOW` y la escala y el núcleo de `HIGH` queda **fuera** (deteriora demasiado lento), y al revés también (demasiado rápido), aunque
cada número por separado esté dentro de su proyección. Está probado (`test_c1`).

Retención compatible del cristaloide (mL retenidos a los 60 min de 1 L/60 min; la región cerrada va de 134,6 a 234,0):

| `c` | Escala 2300 | 2600 | 2900 | 3148 |
|---|---|---|---|---|
| 0,003060 (borde lento) | ningún núcleo | ≤ 141,7 | ≤ 158,0 | ≤ 171,5 *(ilegible)* |
| 0,003212 (medio) | ningún núcleo | ≤ 148,3 | ≤ 165,5 | ≤ 179,6 *(ilegible)* |
| 0,003365 (borde rápido) | ≤ 137,1 | ≤ 155,0 | ≤ 172,8 *(ilegible)* | ≤ 182,7 *(ilegible)* |

*Ilegible*: por encima de 9,326 mL-eq/min el evaluador congelado no puede leer `FD-BLD-06` en 57m. Familia de núcleos usada: en cada profundidad dentro de la región cerrada, el núcleo
**menos retentivo** (el más favorable a C); otros núcleos de la misma profundidad retienen más y son compatibles en una parte menor.

## §4 · P3-340 · Geometría y márgenes

Cada margen se normaliza por el ancho de su propia ventana (A: ventana de `c`; B: 10 mmHg; C: 20 puntos; K: cada envolvente; R: tramo de tasa de la región verificada).

| Escala (mL-eq) | Margen de una unidad (B) | Mayor margen igual de A, C y K | Restricción dominante | Tasa ahí |
|---|---|---|---|---|
| 2300 | 0,276 | 0,013 | **C** (techo de 35 %), con A y K | 7,73 |
| 2450 | 0,214 | 0,058 | C | 8,20 |
| 2600 | 0,159 | 0,100 | C | 8,67 |
| 2750 | 0,109 | 0,140 | **B** (piso de +8, 57m) | 9,14 |
| 2900 | 0,065 | 0,178 | B | 9,60 *(ilegible)* |
| 3050 | 0,024 | 0,215 | B | 10,06 *(ilegible)* |

- **Dominantes:** a escalas pequeñas, el techo de 35 % del cristaloide junto con el piso de la región cerrada y el borde rápido del curso sin tratar; a escalas grandes, el piso de
  +8 mmHg de la unidad en 57m; a tasas altas, la legibilidad del evaluador congelado.
- **Nunca ligan dentro de la región:** el techo de +18 mmHg, el piso de 15 % y los bordes superiores de la región cerrada.
- **Esquinas frágiles:** (i) menor escala, curso más rápido y núcleo menos retentivo (7,60; 2258): se tocan C, K y A a la vez; (ii) mayor escala y curso más lento (9,63; 3148): la
  unidad queda exactamente en +8 mmHg y además es ilegible.
- **Interior:** el mayor margen que todas las restricciones pueden mantener a la vez es **0,126** de cada ventana: **1,26 mmHg** sobre el piso de la unidad, **2,5 puntos** bajo el techo
  del cristaloide, y `c` a **1,16 %** de su borde rápido. **La región es estrecha.**
- **Piso de robustez usado:** 0,05 de cada ventana (0,5 mmHg de la ventana de la unidad, medio mmHg mostrado; 1 punto de la del cristaloide). Es una **convención operativa** de este
  análisis, no una decisión docente.

## §5 · P3-341 y P3-341A · Tres testigos de prueba

Son **testigos de prueba de desarrollo**. Ninguno es una calibración ni es preferido clínicamente. Cada uno enlaza **juntos** tasa, escala y núcleo: no se puede tomar un valor de otro.

| | `LOW` | `CENTER_REFERENCE` | `HIGH` |
|---|---|---|---|
| Tasa (mL-eq/min) = `c × escala` | 8,26 | 8,97 | 9,09 |
| Escala (mL-eq) | 2468,8 | 2697,1 | 2905,9 |
| `c` (por minuto) | 0,003345 | 0,003326 | 0,003127 |
| Núcleo `(e; s; τ)` | 0,2073; 0,865; 60,6 | 0,2131; 0,835; 60,6 | 0,2150; 0,835; 60,6 |
| Retenido a 60 min de 1 L/60 min (mL) | 140,9 | 147,2 | 148,5 |
| Una unidad completa, ΔPAS a 30 min (57m / 72f) | +10,1 / +11,2 | +9,3 / +10,3 | +8,6 / +9,6 |
| Cristaloide lento, % evitado a 60 min | 33,7 | 32,5 | 32,2 |
| Margen A · B · C · K · R (normalizado) | 0,063 · 0,207 · 0,063 · 0,063 · 0,62 | 0,126 · 0,126 · 0,126 · 0,126 · 0,21 | 0,220 · 0,063 · 0,139 · 0,139 · 0,14 |
| Menor margen | 0,063 | **0,126** | 0,063 |
| Restricciones existentes (evaluador congelado, 2 casos) | legibles y cumplidas | legibles y cumplidas | legibles y cumplidas |
| ¿Sigue dentro si se mueve ±0,5 % la tasa, la escala o el `e` del núcleo, de uno en uno? | sí | sí | sí |
| ¿Y ±1 %? | **no** (tasa +1 % o escala −1 % cruzan el borde rápido de A) | sí | sí |

**Por qué cada uno.**
- **`CENTER_REFERENCE`:** el punto **más lejos de toda frontera**: los márgenes sin tratar, de una unidad, de cristaloide y de región cerrada son iguales y los mayores posibles a la vez.
  No es el centro de ninguna ventana (la unidad da +9,3, no +13; el cristaloide 32,5 %, no 25 %).
- **`LOW`:** la **menor** escala en la que todo margen sigue siendo la mitad del del centro: la respuesta a la sangre más fuerte y la mayor fracción del cristaloide sin tocar un borde.
- **`HIGH`:** la **mayor** escala en la que el margen de la unidad sigue siendo la mitad del del centro, con `c` y el núcleo puestos para dejar los demás márgenes lo más amplios
  posible: la respuesta a la sangre más débil de los tres.

`LOW` y `HIGH` no son los extremos factibles (esos no tienen margen): son los dos extremos, a lo largo de la escala, de la parte de la región que conserva la mitad de la robustez.

**Etiquetas reutilizadas.** Estos `LOW`, `CENTER_REFERENCE` y `HIGH` **no** son los testigos de factibilidad del ciclo anterior (7,60 / 8,40 / 9,28 mL-eq/min; FD-P3-232) ni los testigos de
consciencia del mismo nombre de la sombra de GI (Enmienda 2): comparten etiqueta, no valores.

## §6 · P3-342 a P3-345 · Trayectorias candidatas (`JOINT_REGION_V1_CANDIDATE`)

Mismo guion, mismos minutos y mismas variables que la primera revisión. **Comprobado:** corrido en la configuración actual, el arnés da exactamente las presiones revisadas y la
frecuencia cardíaca y el relleno capilar que se mostraron; los candidatos difieren **sólo** por el testigo. PAS/PAD en mmHg:

| Escenario | Minuto | Revisada (config. actual) | `LOW` | `CENTER_REFERENCE` | `HIGH` |
|---|---|---|---|---|---|
| **FR-B** · 57m, tratamiento precoz (llegada 88/54) | 5 | 91/56 | 89/55 | 89/54 | 89/54 |
| | 10 | 98/60 | 91/56 | 91/56 | 91/56 |
| | 30 | **112/68** | 93/57 | **92/57** | 92/56 |
| **FR-C** · 57m, tratamiento tardío | 60 | 73/45 | 71/43 | 71/43 | 72/44 |
| | 120 | 58/36 | 54/33 | 54/33 | 56/35 |
| | 125 | 62/38 | 56/34 | 56/34 | 58/36 |
| | 130 | 72/44 | 60/37 | 59/36 | 61/38 |
| | 150 | **92/56** | 65/40 | **64/39** | 65/40 |
| **FR-E** · 72f, tratamiento tardío y recuperación (llegada 98/62) | 60 | 81/51 | 79/50 | 79/50 | 80/51 |
| | 120 | 64/41 | 60/38 | 60/38 | 63/40 |
| | 125 | 69/44 | 62/39 | 62/39 | 65/41 |
| | 130 | 80/51 | 67/42 | 66/42 | 68/43 |
| | 160 | **109/69** | 74/47 | **72/46** | 74/47 |
| **FR-G** · 72f, cristaloide lento | 60 | 92/58 | 85/54 | 85/54 | 86/54 |
| | 70 | **88/56** | 81/52 | **81/51** | 82/52 |

Lo que hay que leer en esa tabla:

1. **Las trayectorias tratadas cambian mucho.** En `CENTER_REFERENCE` la PAS final baja **20 mmHg** en FR-B, **28** en FR-C, **37** en FR-E y **7** en FR-G respecto de lo revisado.
   Con el sangrado activo a ≈ 9 mL-eq/min, 1 L de suero y la parte de las 2 unidades que entra en el guion apenas superan lo que se pierde. Es la consecuencia directa de las dos anclas
   docentes juntas, y es exactamente lo que la re-revisión tiene que juzgar; **este análisis no lo juzga**.
2. **Los tres testigos son casi la misma trayectoria en pantalla:** la mayor diferencia de PAS entre ellos es 1 mmHg en FR-B y FR-G, 2 en FR-C y 3 en FR-E. Los conjuntos de
   sensibilidad añaden poca información visual.
3. **FR-G:** atenuación **modesta** y paciente que sigue deteriorándose (98 → 85 → 81; sin tratar 79 → 76 en `CENTER_REFERENCE`); 32–34 % evitado a 60 min. No se ajustó a ningún objetivo
   oculto y no se eligió el testigo que lo favorece: los tres son revisables.
4. **Ningún candidato se detiene:** sin frontera no resuelta del núcleo y sin colapso `ESTABLISHED` de la superposición de consciencia dentro de ningún guion. (La misma lectura, en la
   configuración actual, reproduce la parada del FR-A al minuto 207.)
5. **Frecuencia cardíaca y relleno capilar** son los del encuentro (motor vigente), como en la primera revisión: **no dependen del testigo** y son iguales en los tres conjuntos. En FR-B
   mejoran (124 → 116/min; 5 → 3,8 s) mientras la presión candidata sube 4 mmHg: es un límite de la autoridad sólo de presión que la persona revisora debe tener presente.

## §7 · P3-346 · Auditoría causal entre escenarios

Se cumple en los tres testigos (`CENTER_REFERENCE` entre paréntesis):

| Comprobación | Resultado |
|---|---|
| El sangrado sigue activo | Un solo valor de tasa en cada minuto de cada candidato (8,97); sólo se controla en la **lectura** de una unidad de FD-RATE-09 |
| La sangre mejora volumen y presión causalmente | El mismo escenario **sin** los glóbulos: la sangre aporta +7,8 mmHg y +242 mL-eq en FR-B, +10,9 y +250 en FR-C, +17,1 y +350 en FR-E; Hb 7,24 frente a 6,43 (FR-B) |
| El cristaloide lento es más débil que la sangre | 1 L lento a 60 min: +6,2 mmHg (147 mL retenidos) < una unidad completa: +10,3 mmHg (300 mL) < dos unidades en FR-E: +17,1 mmHg |
| El deterioro sin tratar es progresivo | 57m: 88 → 79 → 71 → 54 → 37 (0/30/60/120/180 min); 72f: 98 → 88 → 79 → 60 → 42 |
| El orden de tratamientos se conserva | Tratado sobre no tratado al mismo minuto (FR-B 92 frente a 79; FR-C 64 frente a 46; FR-G 85 y 81 frente a 79 y 76); precoz termina sobre tardío (92 frente a 64); 57m bajo 72f |
| Sin rama por caso | Una sola tupla de testigo para los dos casos; lo único por caso son los estados de llegada redactados |
| Sin ajuste al motor heredado | Los testigos salen sólo de las ventanas docentes, las envolventes de la región cerrada y las envolventes sin tratar; el módulo no lee ninguna presión heredada |

## §8 · P3-347 · Paquete de re-revisión ciega

**La pantalla actual no admite estos candidatos sin cambio de código:** `faculty_trajectory_review.load_set` sólo ofrece su conjunto certificado y fijado por digesto, verificado contra la
serie certificada de la autoridad real (probado: rechaza el conjunto candidato). Integrarlos sería un cambio ejecutable, no autorizado en este ciclo. Por eso el paquete es un **kit
estático** con ciego **de procedimiento**:

| Archivo | Para quién | Qué es |
|---|---|---|
| `faculty_review_kit/region_conjunta_v1/README.md` | revisor | Qué es, orden, ciego, límites |
| `…/conjunto_1.md` | revisor | **El que se revisa**: los cuatro escenarios, en el orden FR-B, FR-C, FR-E, FR-G (es `CENTER_REFERENCE`; el archivo no lo dice) |
| `…/conjunto_2.md`, `…/conjunto_3.md` | revisor | De sensibilidad (`LOW` y `HIGH`; numerados por un digesto, no por nombre): **no se abren** salvo que la docencia los pida después (FD-P3-239) |
| `…/formulario_respuestas.md` | revisor | Q1 Direction · Q2 Timing · Q3 Magnitude · Q4 Management response · Q5 Educational risk + juicio global, con el texto y las opciones exactas de la pantalla |
| `…/ABRIR_DESPUES_DE_LA_PRIMERA_PASADA.md` | revisor, tras la primera pasada | La clave (qué testigo es cada conjunto y sus parámetros) y la trayectoria revisada antes |
| `docs/revision/PHASE3_JOINT_REGION_V1_CANDIDATE_REVIEW_SET.json` | registro | Lo que ve la persona revisora: sin parámetros, sin nombre de testigo, sin presión heredada y sin comparador heredado (la frecuencia cardíaca y el relleno capilar de contexto **sí** son del motor vigente, como en la primera revisión) |
| `docs/revision/PHASE3_JOINT_REGION_V1_BLIND_KEY.json` | registro | La clave |

- **Misma vista que antes:** probado que la vista del candidato es la vista ciega de la pantalla para el escenario guardado con **sólo** los puntos de presión reemplazados (título,
  contexto, propósito, llegada, línea de tiempo, FC y relleno capilar idénticos).
- **Sin comparador heredado en la primera pasada.** La clave no lo copia: remite al conjunto de la primera revisión, que no cambia.
- **Revisión anterior preservada aparte:** `PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json` intacto; sus juicios (FR-B y FR-C `ACCEPT_WITH_LIMITATION`, FR-E `ACCEPT`, FR-G `RECALIBRATE`) **no** se
  transfieren.
- **Diferencias de protocolo con la primera revisión** (los juicios no son comparables uno a uno): el juicio global se da en la primera pasada (en la pantalla se pedía tras ver el comparador
  heredado) y no hay revelado de comparador; el comentario es opcional, como en la pantalla.
- **No verificado:** que una persona docente complete la revisión, ni su duración. El kit no se probó con nadie.

## §9 · P3-348 · Punto de control

`docs/revision/PHASE3_JOINT_REGION_CHECKPOINT.json`.

| Estado | Valor |
|---|---|
| `OLD_SCALE_BAND_STATUS` | `A · PURE_CANDIDATE_ANALYSIS_BAND`; marcada `SUPERSEDED_BY_JOINT_FEASIBILITY_ANALYSIS` fuera del núcleo; registro del núcleo sin editar |
| `JOINT_REGION_FORMALIZED` | Sí: `GI_JOINT_RATE_PRESSURE_DEVELOPMENT_REGION_V1`, coordenadas `(c, escala, núcleo)`; la tasa nunca es libre |
| `JOINT_REGION_MARGIN` | Mayor margen simultáneo 0,126 de cada ventana (1,26 mmHg; 2,5 puntos; 1,16 % de `c`): región **estrecha** |
| `LOW_WITNESS` | 8,26 mL-eq/min; 2468,8 mL-eq; menor margen 0,063 |
| `CENTER_REFERENCE_WITNESS` | 8,97 mL-eq/min; 2697,1 mL-eq; menor margen 0,126 |
| `HIGH_WITNESS` | 9,09 mL-eq/min; 2905,9 mL-eq; menor margen 0,063 |
| `FR_B_READY_FOR_REREVIEW` | Sí (tres candidatos; PAS final 92–93 frente a 112 revisada) |
| `FR_C_READY_FOR_REREVIEW` | Sí (64–65 frente a 92) |
| `FR_E_READY_FOR_REREVIEW` | Sí (72–74 frente a 109) |
| `FR_G_READY_FOR_REREVIEW` | Sí (81–82 a 70 min frente a 88; atenuación modesta) |
| `AMENDMENT3_STATUS` | Cerrada (FD-RATE-19): sin diseño ni implementación |

**Bloqueo:** ninguno para empezar la re-revisión. **Siguiente acción humana:** que una persona docente haga la re-revisión ciega con el kit —**sólo `conjunto_1.md`**, en el orden FR-B, FR-C, FR-E, FR-G— y entregue el
formulario; su resultado se registra como evidencia humana, aparte del análisis. **STOP.**

Antes de adoptar nada seguirían faltando, y no se hicieron: una instantánea de presión nueva, un sucesor certificado del núcleo (la tasa y la banda viven en `clinical_core/`), mover el
núcleo de cristaloide de ejecución dentro de la región cerrada, y la decisión docente sobre el resultado de la re-revisión.

## §10 · Límites

- `MODEL_ANALYSIS`: propiedades de las ecuaciones actuales frente a regiones docentes de **desarrollo**. Sin validación clínica; la IA no es estándar de referencia.
- La región es estrecha: `LOW` no resiste un cambio de 1 % en la tasa sola. El piso de robustez (0,05) y la regla «mitad del margen del centro» son convenciones de este análisis.
- La familia de núcleos es una curva de la región cerrada (la menos retentiva en cada profundidad, sobre la misma rejilla de P3-304); no se recorrió toda la región.
- Posición de llegada fija en 0,5; no se formalizó la región en otra posición.
- La regla de parada evaluada sobre los candidatos cubre las dos causas que existen en los guiones revisados (colapso `ESTABLISHED` de la superposición V1 y frontera del núcleo); no es
  una corrida por la autoridad real, que sigue ligada a `gi_pressure_committed`.
- FC y relleno capilar vienen del motor vigente y no cambian con el testigo; pueden contar una historia distinta de la presión candidata.
- El ciego del kit es de procedimiento: nada impide abrir la clave. Y sólo protege de la identidad de los parámetros a quien **no** haya leído el material técnico: este documento, el
  Decision File, la deuda y los informes del ciclo dan las presiones candidatas junto a las revisadas y dicen que `conjunto_1` es `CENTER_REFERENCE`. Quien los haya leído no llega ciego a
  la dirección ni al tamaño del cambio.
- En la auditoría causal, «sin rama por caso» y «sin ajuste al heredado» son **declaraciones estructurales** que las pruebas sostienen leyendo el código del arnés, no mediciones; y en la
  auditoría de la banda, que ninguna decisión docente, restricción congelada ni validador la exija es la conclusión de una **auditoría manual** registrada, no un cálculo.
- Los límites del ciclo anterior siguen vigentes (`docs/PHASE3_GI_JOINT_FEASIBILITY.md` §13), salvo la lectura de la ventana, ya confirmada.

## §11 · Regresión de aislamiento encontrada y reparada (hallada al cerrar P3-348; no era parte de la secuencia encargada)

**Qué pasó.** Al verificar este ciclo aparecieron guardas rojas que no estaban en las tandas focalizadas de los ciclos anteriores. En una copia limpia del `HEAD` publicado (`ddfca36`)
fallan **tres**:

| Guarda | Qué protege | Qué la rompía |
|---|---|---|
| `test_shadow_core_isolation::test_no_runtime_module_but_the_declared_shadow_bridge_imports_the_core` | Ningún módulo raíz que no sea de prueba, salvo la capa declarada, importa `clinical_core` | Los tres módulos de análisis (`frg_crystalloid_analysis.py`, `gi_bleed_rate_analysis.py`, `gi_joint_feasibility_analysis.py`) |
| `test_shadow_core_isolation::test_cutting_the_shadow_bridge_restores_the_phase2_isolation_exactly` | Sólo `app.py` y `pilot_acceptance.py` usan el puente de sombra | `frg_crystalloid_analysis.py` |
| `test_runtime_shadow_plumbing::test_r13_nothing_authoritative_reads_the_shadow_result` | Nada fuera de la capa nombra `runtime_shadow` | `frg_crystalloid_analysis.py` |

**Desde cuándo.** En `586d60a` (el commit anterior a `388f279`) pasan; fallan desde `388f279` (publicación de P3-314) y siguen así en `7ae5c9b`, `9e8278b`, `32bb4a5` y `ddfca36`.
**Por qué no se vio:** esas tres publicaciones se verificaron con tandas focalizadas («no se corrió la suite completa: no hay cambio ejecutable») que no incluían estos dos archivos. Los
mensajes de commit dicen qué se corrió y son ciertos, pero el árbol publicado **no** estaba verde en esas guardas. Es un error de verificación mío, no de la fisiología: ningún módulo de
ejecución importa esos análisis y nada cambió en lo que ve el residente.

**Reparación (preparada en el árbol de trabajo; publicada en un commit propio, FD-P3-239).** La convención del repositorio para un arnés de análisis que usa el núcleo o el puente es un módulo **del lado de pruebas** `test_gi_*.py`
(como `test_gi_counterfactual.py`). Los cuatro arneses se renombraron; **no** se tocó ninguna guarda:

| Antes | Ahora |
|---|---|
| `frg_crystalloid_analysis.py` | `test_gi_frg_crystalloid_analysis.py` |
| `gi_bleed_rate_analysis.py` | `test_gi_bleed_rate_analysis.py` |
| `gi_joint_feasibility_analysis.py` | `test_gi_joint_feasibility_analysis.py` |
| `gi_joint_region.py` (nuevo de este ciclo) | `test_gi_joint_region.py` |

Sólo cambiaron los `import` y las líneas de uso. **Ningún registro sellado cambió:** los literales que alimentan registros se dejaron tal cual, así que algunos registros anteriores
nombran los módulos por su nombre antiguo (la tabla de arriba es la equivalencia). El módulo nuevo, además, nombraba el registro de la instantánea V1 de consciencia (lo lee para evaluar
la regla de parada), cosa que otras tres guardas reservan a la capa y al lado de pruebas; con el renombre queda conforme.

**Verificación ampliada.** Para cubrir esta clase de fallo se corrieron las pruebas que recorren el árbol o leen el Decision File, la deuda, `CLAUDE.md` o el kit (65 archivos de los 520
`test_*.py`; en los de recomputación pesada del núcleo, sólo las funciones que hacen ese recorrido), además de las tandas habituales. En ese ciclo **no** se corrió la suite completa. Por eso la publicación se condicionó después a una certificación final con la suite completa y las regresiones
sobre una huella congelada (FD-P3-239): una tanda focalizada ya falló una vez.
