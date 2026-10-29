# P2I-1 · Decisión docente: el lactato en la hemorragia digestiva (GI)

Apoyo a una decisión. El corte de P2I-1 no aprobó ningún número. La docencia respondió después FD-LAC-01 a FD-LAC-06
(§10 y §12): son restricciones clínicas de comportamiento del lactato, con estado FACULTY_APPROVED, y **no aprueban
ningún valor de parámetro oculto**. Todos los valores siguen CANDIDATE, los registros de autoridad siguen vacíos, el GI
no se migra y el golden canónico no cambia. Su aplicación a la región candidata está en
`docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md`. FC, PA, FR, volumen y colapso siguen sin abrirse.

- **Generado desde:** el congelamiento de calibración
  `c3fd2dd7de4b1621d6a772b24946812ddbf68a023cdea27c65018061b7d8c7ad` y el corte
  `4b2acb722121a9625a4583ebfeb652e61298d8fb2a5adeff682d052bd1b48442` (`python -m clinical_core.lactate_slice`).
  Los números están en `docs/revision/P2I_lactate_slice.json`. Una prueba falla si el código o las entradas cambian
  sin regenerarlos.
- **Base:** la región estructuralmente admisible de P2F que P2G ya usa: 1054 conjuntos (`decision_pack.admissible`).
  El diseño varía:
  - las tres cinéticas (τ_D `debt_clearance_tau_min`, G `lactate_per_output_deficit`, τ_L
    `lactate_clearance_tau_min`);
  - `arrival_lactate_excess`;
  - cinco combinaciones de `arrival_oxygen_debt` con `arrival_delivery_ratio`;
  - `intrinsic_sinus_rate`, que no mueve el lactato.
- **Toda la evidencia numérica es del modelo.** La verdad del repositorio va aparte (§1). La trayectoria del motor de
  familias aparece sólo al final (§9), como referencia, y no se usa para aceptar ni clasificar candidatos.
- **Umbrales de presentación:** 0,5 mmol/L para «aproximadamente estable» y para una «caída clara», y 2 mmol/L para
  una «subida sustancial». Sirven para agrupar las tablas; no son criterios y la docencia puede leerlas con otros.

<!-- generado:lactato -->
## 1. Verdad del repositorio (sin inferencia)

**gi_bleed_57m**

| Dato | Valor del caso | Fuente |
|---|---|---|
| `lactate_mmol_l` | 4,4 | `clinical_cases.py:900` |
| `sbp` | 88 | `clinical_cases.py:881` |
| `dbp` | 54 | `clinical_cases.py:881` |
| `map` | 65,3 (derivada, no escrita en el caso) | `clinical_cases.py:881` |
| `hr` | 124 | `clinical_cases.py:881` |
| `hb_g_dl` | 6,7 | `clinical_cases.py:900` |
| `spo2` | 97 | `clinical_cases.py:881` |
| `crt_s` | 5 | `clinical_cases.py:881` |
| `extremities` | Cool | `clinical_cases.py:881` |
| `peripheral_perfusion` | impaired | `clinical_cases.py:882` |
| `mental_status` | Alert | `clinical_cases.py:202` |
| `neurological_exam` | Awake and oriented, reporting persistent faintness | `clinical_cases.py:899` |
| `active_bleeding` | melena since yesterday; black tarry stool on rectal examination | `clinical_cases.py:890` |
| `prehospital_therapy` | no consta | `clinical_cases.py:884` |

**gi_bleed_72f**

| Dato | Valor del caso | Fuente |
|---|---|---|
| `lactate_mmol_l` | 3,4 | `clinical_cases.py:929` |
| `sbp` | 98 | `clinical_cases.py:910` |
| `dbp` | 62 | `clinical_cases.py:910` |
| `map` | 74,0 (derivada, no escrita en el caso) | `clinical_cases.py:910` |
| `hr` | 112 | `clinical_cases.py:910` |
| `hb_g_dl` | 6,4 | `clinical_cases.py:929` |
| `spo2` | 96 | `clinical_cases.py:910` |
| `crt_s` | 4 | `clinical_cases.py:910` |
| `extremities` | Cool | `clinical_cases.py:910` |
| `peripheral_perfusion` | impaired | `clinical_cases.py:911` |
| `mental_status` | Alert | `clinical_cases.py:202` |
| `neurological_exam` | Alert, oriented and moving all limbs symmetrically | `clinical_cases.py:928` |
| `active_bleeding` | melena for three days with another episode this morning | `clinical_cases.py:921` |
| `prehospital_therapy` | no consta | `clinical_cases.py:913` |

Los textos clínicos se citan tal como los escribe el caso, en inglés. La duración del shock antes de la llegada no consta en ninguno de los dos casos y no se infiere.

## 2. Las cuatro preguntas de trayectoria

Las cuatro corren 120 min con órdenes y tipos de entrada que ya existen; no se agrega fisiología. L1, L2 y L3 sólo usan lo que el motor produce para sus órdenes; L4 (contrafactual) le agrega a mano una hemostasia.

| Escenario | Qué representa | Cómo se construye |
|---|---|---|
| L1 | Hemorragia activa sin tratar | sin órdenes |
| L2 | Reanimación transitoria y parcial; el sangrado sigue | 2 L de solución salina en 20 min; sin IBP ni endoscopia |
| L3 | Control definitivo y reanimación adecuada | el manejo definitivo de P2G: 2 unidades de glóbulos rojos en 60 min, IBP y endoscopia urgente; el motor hace la endoscopia en el minuto 60 |
| L4 | Hemostasia sin recuperar la perfusión — **composición contrafactual manual** | IBP y endoscopia urgente, sin volumen. El motor de familias difiere esa endoscopia (PAS bajo 90) y nunca produce esta hemostasia. Se agregó a mano, en el mismo minuto que en L3 y con un identificador propio (`p2i_counterfactual_manual_hemostasis`), sobre las entradas que el motor sí produce para estas órdenes. Es una pregunta contrafactual |

**Dos tipos de trayectoria.** L1, L2 y L3 usan sólo entradas que produce el motor de familias por el camino congelado; su hemostasia, en L3, es la del propio motor. L4 es una composición contrafactual manual, y cada vez que aparece en este documento lleva esa etiqueta: ninguna pregunta de la hoja de trabajo la usa (FD-LAC-01, -02, -03 y -06 se leen en L1, y FD-LAC-04 y -05 en L3) y sólo sirve de contraste, para mostrar qué hace el modelo si el sangrado se detiene sin reanimación.

**Cómo se forma el lactato en el modelo.** D (la deuda de O2) acumula el déficit de entrega y lo paga con τ_D. El exceso de lactato X se produce desde D con ganancia G y se aclara con τ_L. El lactato visible es la basal candidata más X, y la basal candidata es el lactato de llegada menos `arrival_lactate_excess`. Dada la trayectoria del déficit, X se separa de forma exacta en tres partes: lo que queda del exceso de llegada, lo que todavía produce la D de llegada y lo que produjo el déficit posterior (§5). La separación es exacta para las ecuaciones del modelo, pero no es una atribución causal entre parámetros, porque éstos interactúan a través del déficit.

## 3. Tablas de trayectoria del lactato (mmol/L, región admisible)

**L1 · hemorragia activa sin tratar**

| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0 | 1054 | 4,40 | 4,40 | 4,40 | 4,40 | 4,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,45 | 4,16 | 4,67 | 4,76 | 23 % | 77 % | 5 % | 0 % |
| gi_bleed_57m | 30 | 1054 | 2,65 | 2,82 | 3,98 | 4,93 | 5,16 | 23 % | 77 % | 22 % | 0 % |
| gi_bleed_57m | 60 | 1054 | 1,81 | 2,20 | 3,75 | 5,47 | 6,06 | 28 % | 72 % | 50 % | 13 % |
| gi_bleed_57m | 90 | 1054 | 1,51 | 2,10 | 3,72 | 6,13 | 7,14 | 31 % | 69 % | 53 % | 22 % |
| gi_bleed_57m | 120 | 1054 | 1,54 | 2,22 | 3,98 | 6,97 | 8,42 | 43 % | 57 % | 53 % | 25 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,73 | 3,26 | 3,73 | 3,82 | 34 % | 66 % | 0 % | 0 % |
| gi_bleed_72f | 30 | 1054 | 2,13 | 2,31 | 3,16 | 4,07 | 4,27 | 34 % | 66 % | 10 % | 0 % |
| gi_bleed_72f | 60 | 1054 | 1,53 | 1,92 | 3,08 | 4,71 | 5,27 | 37 % | 63 % | 31 % | 0 % |
| gi_bleed_72f | 90 | 1054 | 1,30 | 1,90 | 3,18 | 5,37 | 6,39 | 44 % | 56 % | 42 % | 11 % |
| gi_bleed_72f | 120 | 1054 | 1,30 | 2,01 | 3,42 | 6,11 | 7,66 | 51 % | 49 % | 50 % | 20 % |

**L2 · reanimación transitoria y parcial (2 L de salina en 20 min; el sangrado sigue)**

| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0 | 1054 | 4,40 | 4,40 | 4,40 | 4,40 | 4,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,45 | 4,16 | 4,61 | 4,76 | 22 % | 78 % | 5 % | 0 % |
| gi_bleed_57m | 30 | 1054 | 2,63 | 2,80 | 3,94 | 4,81 | 5,13 | 20 % | 80 % | 24 % | 0 % |
| gi_bleed_57m | 60 | 1054 | 1,74 | 2,10 | 3,60 | 4,98 | 5,93 | 19 % | 81 % | 47 % | 16 % |
| gi_bleed_57m | 90 | 1054 | 1,31 | 1,78 | 3,31 | 5,23 | 6,84 | 18 % | 82 % | 62 % | 26 % |
| gi_bleed_57m | 120 | 1054 | 1,18 | 1,82 | 3,37 | 5,78 | 7,90 | 22 % | 78 % | 66 % | 31 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,73 | 3,26 | 3,70 | 3,82 | 31 % | 69 % | 0 % | 0 % |
| gi_bleed_72f | 30 | 1054 | 2,12 | 2,29 | 3,14 | 3,93 | 4,26 | 32 % | 68 % | 13 % | 0 % |
| gi_bleed_72f | 60 | 1054 | 1,48 | 1,86 | 2,97 | 4,27 | 5,18 | 34 % | 66 % | 31 % | 0 % |
| gi_bleed_72f | 90 | 1054 | 1,17 | 1,73 | 2,99 | 4,80 | 6,20 | 33 % | 67 % | 40 % | 12 % |
| gi_bleed_72f | 120 | 1054 | 1,07 | 1,77 | 3,04 | 5,45 | 7,34 | 41 % | 59 % | 41 % | 15 % |

**L3 · control definitivo y reanimación adecuada (2 unidades en 60 min, IBP y endoscopia)**

| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0 | 1054 | 4,40 | 4,40 | 4,40 | 4,40 | 4,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,45 | 4,15 | 4,61 | 4,76 | 22 % | 78 % | 5 % | 0 % |
| gi_bleed_57m | 30 | 1054 | 2,63 | 2,79 | 3,93 | 4,81 | 5,12 | 20 % | 80 % | 24 % | 0 % |
| gi_bleed_57m | 60 | 1054 | 1,73 | 1,97 | 3,56 | 4,96 | 5,67 | 17 % | 83 % | 47 % | 16 % |
| gi_bleed_57m | 90 | 1054 | 1,28 | 1,50 | 3,22 | 4,76 | 5,96 | 15 % | 85 % | 63 % | 26 % |
| gi_bleed_57m | 120 | 1054 | 1,04 | 1,26 | 2,88 | 4,43 | 6,05 | 10 % | 90 % | 73 % | 39 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,73 | 3,25 | 3,70 | 3,82 | 31 % | 69 % | 0 % | 0 % |
| gi_bleed_72f | 30 | 1054 | 2,12 | 2,28 | 3,12 | 3,93 | 4,25 | 27 % | 73 % | 13 % | 0 % |
| gi_bleed_72f | 60 | 1054 | 1,48 | 1,73 | 2,87 | 4,19 | 5,00 | 24 % | 76 % | 31 % | 0 % |
| gi_bleed_72f | 90 | 1054 | 1,14 | 1,41 | 2,66 | 4,21 | 5,46 | 21 % | 79 % | 47 % | 10 % |
| gi_bleed_72f | 120 | 1054 | 0,98 | 1,22 | 2,45 | 4,11 | 5,68 | 18 % | 82 % | 54 % | 16 % |

**L4 · hemostasia sin recuperar la perfusión (IBP y endoscopia sin volumen) — COMPOSICIÓN CONTRAFACTUAL MANUAL: la hemostasia se agregó a mano en el minuto de L3; el motor no la produce**

> L4 contrafactual: no es una trayectoria que el motor heredado produzca. Se muestra sólo como contraste y ninguna pregunta de la hoja de trabajo la usa.

| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0 | 1054 | 4,40 | 4,40 | 4,40 | 4,40 | 4,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,45 | 4,16 | 4,67 | 4,76 | 23 % | 77 % | 5 % | 0 % |
| gi_bleed_57m | 30 | 1054 | 2,64 | 2,82 | 3,98 | 4,93 | 5,16 | 23 % | 77 % | 22 % | 0 % |
| gi_bleed_57m | 60 | 1054 | 1,80 | 2,19 | 3,73 | 5,45 | 6,05 | 26 % | 74 % | 50 % | 13 % |
| gi_bleed_57m | 90 | 1054 | 1,45 | 2,05 | 3,66 | 6,09 | 7,09 | 31 % | 69 % | 57 % | 22 % |
| gi_bleed_57m | 120 | 1054 | 1,37 | 2,08 | 3,79 | 6,73 | 8,27 | 40 % | 60 % | 54 % | 27 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,73 | 3,26 | 3,73 | 3,82 | 34 % | 66 % | 0 % | 0 % |
| gi_bleed_72f | 30 | 1054 | 2,13 | 2,31 | 3,16 | 4,07 | 4,27 | 34 % | 66 % | 10 % | 0 % |
| gi_bleed_72f | 60 | 1054 | 1,52 | 1,91 | 3,07 | 4,69 | 5,26 | 37 % | 63 % | 29 % | 0 % |
| gi_bleed_72f | 90 | 1054 | 1,26 | 1,87 | 3,13 | 5,32 | 6,36 | 44 % | 56 % | 40 % | 11 % |
| gi_bleed_72f | 120 | 1054 | 1,19 | 1,92 | 3,29 | 5,95 | 7,56 | 49 % | 51 % | 50 % | 20 % |

## 4. Clases de comportamiento (conteos sobre la región; ninguna se declara correcta)

**gi_bleed_57m**

| Escenario y lectura | Clase | n | Dónde se concentra (mayor proporción por factor) |
|---|---|---|---|
| L1 a los 60 min | A baja | 604 | `arrival_delivery_ratio` superior (45 %); `arrival_lactate_excess` medio (37 %); `arrival_oxygen_debt` inferior (63 %); `debt_clearance_tau_min` 60 (36 %); `lactate_clearance_tau_min` 45 (55 %); `lactate_per_output_deficit` 6 (33 %) |
| L1 a los 60 min | B aproximadamente estable | 270 | `arrival_delivery_ratio` medio (40 %); `arrival_lactate_excess` inferior (47 %); `arrival_oxygen_debt` inferior (40 %); `debt_clearance_tau_min` 120 (37 %); `lactate_clearance_tau_min` 240 (70 %); `lactate_per_output_deficit` 12 (33 %) |
| L1 a los 60 min | C sube moderadamente | 180 | `arrival_delivery_ratio` inferior (60 %); `arrival_lactate_excess` inferior (40 %); `arrival_oxygen_debt` superior (100 %); `debt_clearance_tau_min` 120 (50 %); `lactate_clearance_tau_min` 240 (60 %); `lactate_per_output_deficit` 12 (33 %) |
| L1 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 604 | |
| L1 a los 120 min | A baja | 505 | `arrival_delivery_ratio` superior (50 %); `arrival_lactate_excess` medio (39 %); `arrival_oxygen_debt` inferior (70 %); `debt_clearance_tau_min` 60 (36 %); `lactate_clearance_tau_min` 45 (62 %); `lactate_per_output_deficit` 6 (33 %) |
| L1 a los 120 min | B aproximadamente estable | 225 | `arrival_delivery_ratio` inferior (44 %); `arrival_lactate_excess` inferior (52 %); `arrival_oxygen_debt` inferior (48 %); `debt_clearance_tau_min` 120 (36 %); `lactate_clearance_tau_min` 120 (48 %); `lactate_per_output_deficit` 12 (33 %) |
| L1 a los 120 min | C sube moderadamente | 198 | `arrival_delivery_ratio` medio (41 %); `arrival_lactate_excess` inferior (36 %); `arrival_oxygen_debt` superior (45 %); `debt_clearance_tau_min` 120 (41 %); `lactate_clearance_tau_min` 240 (55 %); `lactate_per_output_deficit` 12 (33 %) |
| L1 a los 120 min | D sube sustancialmente | 126 | `arrival_delivery_ratio` inferior (57 %); `arrival_lactate_excess` inferior (43 %); `arrival_oxygen_debt` superior (100 %); `debt_clearance_tau_min` 120 (50 %); `lactate_clearance_tau_min` 240 (86 %); `lactate_per_output_deficit` 12 (33 %) |
| L1 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 505 | |
| L2 a los 60 min | A baja | 667 | `arrival_delivery_ratio` superior (45 %); `arrival_lactate_excess` superior (38 %); `arrival_oxygen_debt` inferior (65 %); `debt_clearance_tau_min` 60 (35 %); `lactate_clearance_tau_min` 45 (50 %); `lactate_per_output_deficit` 6 (33 %) |
| L2 a los 60 min | B aproximadamente estable | 261 | `arrival_delivery_ratio` medio (38 %); `arrival_lactate_excess` inferior (41 %); `arrival_oxygen_debt` superior (41 %); `debt_clearance_tau_min` 60 (45 %); `lactate_clearance_tau_min` 240 (59 %); `lactate_per_output_deficit` 12 (33 %) |
| L2 a los 60 min | C sube moderadamente | 126 | `arrival_delivery_ratio` inferior (71 %); `arrival_lactate_excess` inferior (43 %); `arrival_oxygen_debt` superior (100 %); `debt_clearance_tau_min` 120 (57 %); `lactate_clearance_tau_min` 240 (71 %); `lactate_per_output_deficit` 12 (33 %) |
| L2 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 667 | |
| L2 a los 120 min | A baja | 631 | `arrival_delivery_ratio` superior (50 %); `arrival_lactate_excess` medio (37 %); `arrival_oxygen_debt` inferior (60 %); `debt_clearance_tau_min` 60 (37 %); `lactate_clearance_tau_min` 45 (53 %); `lactate_per_output_deficit` 6 (33 %) |
| L2 a los 120 min | B aproximadamente estable | 279 | `arrival_delivery_ratio` inferior (45 %); `arrival_lactate_excess` inferior (48 %); `arrival_oxygen_debt` inferior (39 %); `debt_clearance_tau_min` 120 (39 %); `lactate_clearance_tau_min` 240 (65 %); `lactate_per_output_deficit` 12 (33 %) |
| L2 a los 120 min | C sube moderadamente | 72 | `arrival_delivery_ratio` inferior (50 %); `arrival_lactate_excess` medio (38 %); `arrival_oxygen_debt` superior (100 %); `debt_clearance_tau_min` 120 (62 %); `lactate_clearance_tau_min` 120 (50 %); `lactate_per_output_deficit` 12 (33 %) |
| L2 a los 120 min | D sube sustancialmente | 72 | `arrival_delivery_ratio` inferior (100 %); `arrival_lactate_excess` inferior (50 %); `arrival_oxygen_debt` superior (100 %); `debt_clearance_tau_min` 120 (50 %); `lactate_clearance_tau_min` 240 (75 %); `lactate_per_output_deficit` 12 (33 %) |
| L2 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 631 | |
| L3 en 120 min | E baja claramente en 30 min | 504 | `arrival_delivery_ratio` superior (43 %); `arrival_lactate_excess` superior (39 %); `arrival_oxygen_debt` inferior (59 %); `debt_clearance_tau_min` 120 (36 %); `lactate_clearance_tau_min` 45 (66 %); `lactate_per_output_deficit` 12 (33 %) |
| L3 en 120 min | E' baja claramente después de 30 min | 379 | `arrival_delivery_ratio` inferior (38 %); `arrival_lactate_excess` inferior (38 %); `arrival_oxygen_debt` inferior (50 %); `debt_clearance_tau_min` 60 (41 %); `lactate_clearance_tau_min` 240 (59 %); `lactate_per_output_deficit` 6 (34 %) |
| L3 en 120 min | F sigue elevado con la entrega restaurada | 171 | `arrival_delivery_ratio` inferior (53 %); `arrival_lactate_excess` inferior (47 %); `arrival_oxygen_debt` superior (89 %); `debt_clearance_tau_min` 120 (58 %); `lactate_clearance_tau_min` 240 (74 %); `lactate_per_output_deficit` 12 (33 %) |
| L4 (contrafactual) en 120 min | E baja claramente en 30 min | 450 | `arrival_delivery_ratio` superior (44 %); `arrival_lactate_excess` medio (38 %); `arrival_oxygen_debt` inferior (66 %); `debt_clearance_tau_min` 120 (36 %); `lactate_clearance_tau_min` 45 (70 %); `lactate_per_output_deficit` 12 (33 %) |
| L4 (contrafactual) en 120 min | E' baja claramente después de 30 min | 181 | `arrival_delivery_ratio` superior (55 %); `arrival_lactate_excess` inferior (40 %); `arrival_oxygen_debt` inferior (60 %); `debt_clearance_tau_min` 60 (35 %); `lactate_clearance_tau_min` 120 (45 %); `lactate_per_output_deficit` 6 (34 %) |
| L4 (contrafactual) en 120 min | F' sigue elevado sin restaurar la entrega | 423 | `arrival_delivery_ratio` inferior (49 %); `arrival_lactate_excess` inferior (40 %); `arrival_oxygen_debt` superior (55 %); `debt_clearance_tau_min` 120 (43 %); `lactate_clearance_tau_min` 240 (64 %); `lactate_per_output_deficit` 12 (33 %) |

**gi_bleed_72f**

| Escenario y lectura | Clase | n | Dónde se concentra (mayor proporción por factor) |
|---|---|---|---|
| L1 a los 60 min | A baja | 432 | `arrival_delivery_ratio` superior (46 %); `arrival_lactate_excess` superior (46 %); `arrival_oxygen_debt` inferior (69 %); `debt_clearance_tau_min` 120 (35 %); `lactate_clearance_tau_min` 45 (69 %); `lactate_per_output_deficit` 12 (33 %) |
| L1 a los 60 min | B aproximadamente estable | 406 | `arrival_delivery_ratio` medio (40 %); `arrival_lactate_excess` inferior (49 %); `arrival_oxygen_debt` inferior (47 %); `debt_clearance_tau_min` 60 (36 %); `lactate_clearance_tau_min` 240 (53 %); `lactate_per_output_deficit` 6 (33 %) |
| L1 a los 60 min | C sube moderadamente | 216 | `arrival_delivery_ratio` inferior (50 %); `arrival_lactate_excess` inferior (33 %); `arrival_oxygen_debt` superior (100 %); `debt_clearance_tau_min` 120 (50 %); `lactate_clearance_tau_min` 120 (50 %); `lactate_per_output_deficit` 12 (33 %) |
| L1 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 432 | |
| L1 a los 120 min | A baja | 306 | `arrival_delivery_ratio` superior (65 %); `arrival_lactate_excess` superior (50 %); `arrival_oxygen_debt` inferior (71 %); `debt_clearance_tau_min` 120 (35 %); `lactate_clearance_tau_min` 45 (74 %); `lactate_per_output_deficit` 12 (33 %) |
| L1 a los 120 min | B aproximadamente estable | 298 | `arrival_delivery_ratio` inferior (39 %); `arrival_lactate_excess` inferior (42 %); `arrival_oxygen_debt` inferior (54 %); `debt_clearance_tau_min` 60 (37 %); `lactate_clearance_tau_min` 120 (46 %); `lactate_per_output_deficit` 6 (34 %) |
| L1 a los 120 min | C sube moderadamente | 270 | `arrival_delivery_ratio` inferior (47 %); `arrival_lactate_excess` inferior (47 %); `arrival_oxygen_debt` inferior (40 %); `debt_clearance_tau_min` 120 (37 %); `lactate_clearance_tau_min` 240 (60 %); `lactate_per_output_deficit` 12 (33 %) |
| L1 a los 120 min | D sube sustancialmente | 180 | `arrival_delivery_ratio` inferior (60 %); `arrival_lactate_excess` inferior (40 %); `arrival_oxygen_debt` superior (100 %); `debt_clearance_tau_min` 120 (50 %); `lactate_clearance_tau_min` 240 (60 %); `lactate_per_output_deficit` 12 (33 %) |
| L1 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 306 | |
| L2 a los 60 min | A baja | 486 | `arrival_delivery_ratio` superior (52 %); `arrival_lactate_excess` superior (41 %); `arrival_oxygen_debt` inferior (72 %); `debt_clearance_tau_min` 120 (35 %); `lactate_clearance_tau_min` 45 (61 %); `lactate_per_output_deficit` 12 (33 %) |
| L2 a los 60 min | B aproximadamente estable | 397 | `arrival_delivery_ratio` medio (41 %); `arrival_lactate_excess` inferior (45 %); `arrival_oxygen_debt` medio (41 %); `debt_clearance_tau_min` 60 (39 %); `lactate_clearance_tau_min` 240 (48 %); `lactate_per_output_deficit` 6 (34 %) |
| L2 a los 60 min | C sube moderadamente | 171 | `arrival_delivery_ratio` inferior (63 %); `arrival_lactate_excess` inferior (37 %); `arrival_oxygen_debt` superior (100 %); `debt_clearance_tau_min` 120 (53 %); `lactate_clearance_tau_min` 240 (63 %); `lactate_per_output_deficit` 12 (33 %) |
| L2 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 486 | |
| L2 a los 120 min | A baja | 423 | `arrival_delivery_ratio` superior (62 %); `arrival_lactate_excess` medio (36 %); `arrival_oxygen_debt` inferior (70 %); `debt_clearance_tau_min` 60 (36 %); `lactate_clearance_tau_min` 45 (68 %); `lactate_per_output_deficit` 12 (33 %) |
| L2 a los 120 min | B aproximadamente estable | 325 | `arrival_delivery_ratio` inferior (53 %); `arrival_lactate_excess` medio (36 %); `arrival_oxygen_debt` inferior (50 %); `debt_clearance_tau_min` 120 (39 %); `lactate_clearance_tau_min` 120 (61 %); `lactate_per_output_deficit` 6 (34 %) |
| L2 a los 120 min | C sube moderadamente | 198 | `arrival_delivery_ratio` medio (41 %); `arrival_lactate_excess` inferior (55 %); `arrival_oxygen_debt` superior (45 %); `debt_clearance_tau_min` 120 (41 %); `lactate_clearance_tau_min` 240 (82 %); `lactate_per_output_deficit` 12 (33 %) |
| L2 a los 120 min | D sube sustancialmente | 108 | `arrival_delivery_ratio` inferior (100 %); `arrival_lactate_excess` inferior (33 %); `arrival_oxygen_debt` superior (100 %); `debt_clearance_tau_min` 120 (50 %); `lactate_clearance_tau_min` 120 (50 %); `lactate_per_output_deficit` 12 (33 %) |
| L2 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 423 | |
| L3 en 120 min | E baja claramente en 30 min | 333 | `arrival_delivery_ratio` superior (51 %); `arrival_lactate_excess` superior (46 %); `arrival_oxygen_debt` inferior (73 %); `debt_clearance_tau_min` 120 (35 %); `lactate_clearance_tau_min` 45 (76 %); `lactate_per_output_deficit` 12 (33 %) |
| L3 en 120 min | E' baja claramente después de 30 min | 415 | `arrival_delivery_ratio` inferior (35 %); `arrival_lactate_excess` medio (35 %); `arrival_oxygen_debt` inferior (52 %); `debt_clearance_tau_min` 60 (39 %); `lactate_clearance_tau_min` 120 (41 %); `lactate_per_output_deficit` 6 (33 %) |
| L3 en 120 min | F sigue elevado con la entrega restaurada | 306 | `arrival_delivery_ratio` inferior (50 %); `arrival_lactate_excess` inferior (50 %); `arrival_oxygen_debt` superior (71 %); `debt_clearance_tau_min` 120 (53 %); `lactate_clearance_tau_min` 240 (62 %); `lactate_per_output_deficit` 12 (33 %) |
| L4 (contrafactual) en 120 min | E baja claramente en 30 min | 288 | `arrival_delivery_ratio` superior (53 %); `arrival_lactate_excess` superior (44 %); `arrival_oxygen_debt` inferior (75 %); `debt_clearance_tau_min` 120 (34 %); `lactate_clearance_tau_min` 45 (81 %); `lactate_per_output_deficit` 12 (33 %) |
| L4 (contrafactual) en 120 min | E' baja claramente después de 30 min | 198 | `arrival_delivery_ratio` superior (50 %); `arrival_lactate_excess` medio (36 %); `arrival_oxygen_debt` inferior (68 %); `debt_clearance_tau_min` 120 (36 %); `lactate_clearance_tau_min` 120 (41 %); `lactate_per_output_deficit` 12 (33 %) |
| L4 (contrafactual) en 120 min | F' sigue elevado sin restaurar la entrega | 568 | `arrival_delivery_ratio` inferior (44 %); `arrival_lactate_excess` inferior (43 %); `arrival_oxygen_debt` superior (48 %); `debt_clearance_tau_min` 60 (41 %); `lactate_clearance_tau_min` 240 (52 %); `lactate_per_output_deficit` 6 (33 %) |

## 5. Descomposición del mecanismo (exacta dada la trayectoria del déficit)

Exceso de lactato = lo que queda del exceso de llegada + lo que produce la D de llegada + lo producido por el déficit posterior. Suma exacta para las recurrencias del modelo; no es una atribución causal entre parámetros.

**gi_bleed_57m · bajo · L1** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 3,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 0,80 | 3,60 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,00 | 0,00 |
| 15 | 3,37 | 0,80 | 2,57 | 0,00 | 0,00 | 0,6 | 0,0 | 0,6 | 0,0 | 0,92 | 0,08 |
| 30 | 2,65 | 0,80 | 1,83 | 0,00 | 0,01 | 2,4 | 0,0 | 2,4 | 0,0 | 0,83 | 0,17 |
| 60 | 1,81 | 0,80 | 0,93 | 0,00 | 0,08 | 9,7 | 0,0 | 9,7 | 0,0 | 0,67 | 0,33 |
| 90 | 1,51 | 0,80 | 0,48 | 0,00 | 0,23 | 21,9 | 0,0 | 21,9 | 0,0 | 0,51 | 0,49 |
| 120 | 1,54 | 0,80 | 0,24 | 0,00 | 0,49 | 38,7 | 0,0 | 38,7 | 0,0 | 0,36 | 0,64 |

**gi_bleed_57m · bajo · L3** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 3,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 0,80 | 3,60 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,00 | 0,00 |
| 15 | 3,37 | 0,80 | 2,57 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,34 | 0,00 |
| 30 | 2,63 | 0,80 | 1,83 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,67 | 0,00 |
| 60 | 1,73 | 0,80 | 0,93 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 2,29 | 0,00 |
| 90 | 1,28 | 0,80 | 0,48 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 2,28 | 0,00 |
| 120 | 1,04 | 0,80 | 0,24 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 2,27 | 0,00 |

**gi_bleed_57m · medio · L1** — `arrival_oxygen_debt` 20, `arrival_lactate_excess` 3,40, `arrival_delivery_ratio` 0,85, τ_D 60, g 1,0, G 6, τ_L 120, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 1,00 | 3,40 | 0,00 | 0,00 | 20,0 | 20,0 | 0,0 | 0,0 | 0,85 | 0,15 |
| 15 | 4,17 | 1,00 | 3,00 | 0,16 | 0,01 | 22,7 | 20,0 | 2,7 | 0,0 | 0,78 | 0,22 |
| 30 | 3,98 | 1,00 | 2,65 | 0,30 | 0,04 | 26,5 | 20,0 | 6,5 | 0,0 | 0,71 | 0,29 |
| 60 | 3,79 | 1,00 | 2,06 | 0,53 | 0,21 | 37,3 | 20,0 | 17,3 | 0,0 | 0,57 | 0,43 |
| 90 | 3,83 | 1,00 | 1,60 | 0,71 | 0,52 | 52,1 | 20,0 | 32,1 | 0,0 | 0,44 | 0,56 |
| 120 | 4,11 | 1,00 | 1,25 | 0,84 | 1,02 | 70,9 | 20,0 | 50,9 | 0,0 | 0,31 | 0,69 |

**gi_bleed_57m · medio · L3** — `arrival_oxygen_debt` 20, `arrival_lactate_excess` 3,40, `arrival_delivery_ratio` 0,85, τ_D 60, g 1,0, G 6, τ_L 120, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 1,00 | 3,40 | 0,00 | 0,00 | 20,0 | 20,0 | 0,0 | 0,0 | 0,85 | 0,15 |
| 15 | 4,16 | 1,00 | 3,00 | 0,15 | 0,00 | 18,4 | 17,8 | 0,7 | 2,3 | 1,14 | 0,00 |
| 30 | 3,91 | 1,00 | 2,65 | 0,26 | 0,01 | 14,3 | 13,8 | 0,7 | 6,4 | 1,42 | 0,00 |
| 60 | 3,43 | 1,00 | 2,06 | 0,36 | 0,01 | 8,6 | 8,3 | 0,7 | 12,0 | 1,95 | 0,00 |
| 90 | 2,99 | 1,00 | 1,60 | 0,38 | 0,01 | 5,2 | 5,0 | 0,7 | 15,5 | 1,94 | 0,00 |
| 120 | 2,61 | 1,00 | 1,25 | 0,35 | 0,01 | 3,1 | 3,0 | 0,7 | 17,5 | 1,93 | 0,00 |

**gi_bleed_57m · alto · L1** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 6, τ_L 240, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 2,00 | 2,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 4,76 | 2,00 | 2,25 | 0,49 | 0,02 | 66,4 | 60,0 | 6,4 | 0,0 | 0,55 | 0,45 |
| 30 | 5,16 | 2,00 | 2,12 | 0,94 | 0,10 | 73,4 | 60,0 | 13,4 | 0,0 | 0,50 | 0,50 |
| 60 | 6,06 | 2,00 | 1,87 | 1,77 | 0,42 | 89,8 | 60,0 | 29,8 | 0,0 | 0,40 | 0,60 |
| 90 | 7,14 | 2,00 | 1,65 | 2,51 | 0,99 | 109,1 | 60,0 | 49,1 | 0,0 | 0,31 | 0,69 |
| 120 | 8,42 | 2,00 | 1,45 | 3,15 | 1,81 | 131,2 | 60,0 | 71,2 | 0,0 | 0,22 | 0,78 |

**gi_bleed_57m · alto · L3** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 6, τ_L 240, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 2,00 | 2,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 4,76 | 2,00 | 2,25 | 0,49 | 0,02 | 64,6 | 60,0 | 4,6 | 0,0 | 0,80 | 0,20 |
| 30 | 5,12 | 2,00 | 2,12 | 0,94 | 0,06 | 66,1 | 60,0 | 6,1 | 0,0 | 1,00 | 0,00 |
| 60 | 5,57 | 2,00 | 1,87 | 1,57 | 0,13 | 39,9 | 36,2 | 6,1 | 26,2 | 1,37 | 0,00 |
| 90 | 5,65 | 2,00 | 1,65 | 1,84 | 0,16 | 24,1 | 21,9 | 6,1 | 42,0 | 1,37 | 0,00 |
| 120 | 5,52 | 2,00 | 1,45 | 1,89 | 0,17 | 14,6 | 13,2 | 6,1 | 51,6 | 1,36 | 0,00 |

**gi_bleed_72f · bajo · L1** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 2,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 0,80 | 2,60 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,00 | 0,00 |
| 15 | 2,66 | 0,80 | 1,86 | 0,00 | 0,00 | 0,4 | 0,0 | 0,4 | 0,0 | 0,95 | 0,05 |
| 30 | 2,13 | 0,80 | 1,32 | 0,00 | 0,01 | 1,6 | 0,0 | 1,6 | 0,0 | 0,89 | 0,11 |
| 60 | 1,53 | 0,80 | 0,68 | 0,00 | 0,05 | 6,4 | 0,0 | 6,4 | 0,0 | 0,78 | 0,22 |
| 90 | 1,30 | 0,80 | 0,34 | 0,00 | 0,16 | 14,5 | 0,0 | 14,5 | 0,0 | 0,68 | 0,32 |
| 120 | 1,30 | 0,80 | 0,18 | 0,00 | 0,33 | 25,7 | 0,0 | 25,7 | 0,0 | 0,57 | 0,43 |

**gi_bleed_72f · bajo · L3** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 2,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 0,80 | 2,60 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,00 | 0,00 |
| 15 | 2,66 | 0,80 | 1,86 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,25 | 0,00 |
| 30 | 2,12 | 0,80 | 1,32 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,50 | 0,00 |
| 60 | 1,48 | 0,80 | 0,68 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,97 | 0,00 |
| 90 | 1,14 | 0,80 | 0,34 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,96 | 0,00 |
| 120 | 0,98 | 0,80 | 0,18 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,95 | 0,00 |

**gi_bleed_72f · medio · L1** — `arrival_oxygen_debt` 20, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,85, τ_D 60, g 1,0, G 6, τ_L 120, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 1,00 | 2,40 | 0,00 | 0,00 | 20,0 | 20,0 | 0,0 | 0,0 | 0,85 | 0,15 |
| 15 | 3,28 | 1,00 | 2,12 | 0,16 | 0,01 | 22,6 | 20,0 | 2,6 | 0,0 | 0,80 | 0,20 |
| 30 | 3,20 | 1,00 | 1,87 | 0,30 | 0,04 | 25,9 | 20,0 | 5,9 | 0,0 | 0,76 | 0,24 |
| 60 | 3,16 | 1,00 | 1,45 | 0,53 | 0,18 | 34,5 | 20,0 | 14,5 | 0,0 | 0,67 | 0,33 |
| 90 | 3,27 | 1,00 | 1,13 | 0,71 | 0,43 | 45,8 | 20,0 | 25,8 | 0,0 | 0,58 | 0,42 |
| 120 | 3,55 | 1,00 | 0,88 | 0,84 | 0,82 | 59,8 | 20,0 | 39,8 | 0,0 | 0,49 | 0,51 |

**gi_bleed_72f · medio · L3** — `arrival_oxygen_debt` 20, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,85, τ_D 60, g 1,0, G 6, τ_L 120, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 1,00 | 2,40 | 0,00 | 0,00 | 20,0 | 20,0 | 0,0 | 0,0 | 0,85 | 0,15 |
| 15 | 3,28 | 1,00 | 2,12 | 0,16 | 0,00 | 19,5 | 18,7 | 0,9 | 1,4 | 1,07 | 0,00 |
| 30 | 3,15 | 1,00 | 1,87 | 0,27 | 0,01 | 15,2 | 14,5 | 0,9 | 5,7 | 1,28 | 0,00 |
| 60 | 2,85 | 1,00 | 1,45 | 0,38 | 0,01 | 9,2 | 8,8 | 0,9 | 11,7 | 1,67 | 0,00 |
| 90 | 2,54 | 1,00 | 1,13 | 0,40 | 0,02 | 5,5 | 5,3 | 0,9 | 15,3 | 1,67 | 0,00 |
| 120 | 2,26 | 1,00 | 0,88 | 0,37 | 0,02 | 3,3 | 3,2 | 0,9 | 17,5 | 1,66 | 0,00 |

**gi_bleed_72f · alto · L1** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 1,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 6, τ_L 240, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 2,00 | 1,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 3,82 | 2,00 | 1,32 | 0,49 | 0,02 | 66,2 | 60,0 | 6,2 | 0,0 | 0,57 | 0,43 |
| 30 | 4,27 | 2,00 | 1,24 | 0,94 | 0,10 | 73,0 | 60,0 | 13,0 | 0,0 | 0,53 | 0,47 |
| 60 | 5,27 | 2,00 | 1,09 | 1,77 | 0,40 | 87,9 | 60,0 | 27,9 | 0,0 | 0,47 | 0,53 |
| 90 | 6,39 | 2,00 | 0,96 | 2,51 | 0,92 | 104,7 | 60,0 | 44,7 | 0,0 | 0,41 | 0,59 |
| 120 | 7,66 | 2,00 | 0,85 | 3,15 | 1,66 | 123,4 | 60,0 | 63,4 | 0,0 | 0,34 | 0,66 |

**gi_bleed_72f · alto · L3** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 1,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 6, τ_L 240, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 2,00 | 1,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 3,82 | 2,00 | 1,32 | 0,49 | 0,02 | 64,9 | 60,0 | 4,9 | 0,0 | 0,75 | 0,25 |
| 30 | 4,25 | 2,00 | 1,24 | 0,94 | 0,07 | 67,6 | 60,0 | 7,6 | 0,0 | 0,90 | 0,10 |
| 60 | 4,96 | 2,00 | 1,09 | 1,69 | 0,18 | 49,5 | 43,6 | 8,2 | 18,6 | 1,18 | 0,00 |
| 90 | 5,22 | 2,00 | 0,96 | 2,03 | 0,23 | 29,9 | 26,3 | 8,2 | 38,3 | 1,18 | 0,00 |
| 120 | 5,21 | 2,00 | 0,85 | 2,12 | 0,25 | 18,1 | 15,9 | 8,2 | 50,1 | 1,17 | 0,00 |

## 6. D frente a lactato (no se declaran inválidos)

| Caso | Patrón | corridas | de | ejemplos (D desde → hasta; lactato desde → hasta) |
|---|---|---|---|---|
| gi_bleed_57m | L1, 0–60 min: D sube mientras el lactato baja | 757 | 1054 | D 0,0→9,7, lactato 4,40→1,81; D 0,0→29,8, lactato 4,40→3,37; D 0,0→29,8, lactato 4,40→4,29 |
| gi_bleed_57m | L1, 0–120 min: D sube mientras el lactato baja | 604 | 1054 | D 0,0→38,7, lactato 4,40→1,54; D 0,0→71,2, lactato 4,40→3,24; D 0,0→38,7, lactato 4,40→4,21 |
| gi_bleed_57m | L3, 0–120 min: D baja mientras el lactato sigue a menos de 0,5 mmol/L de la llegada o por encima | 171 | 1054 | D 60,0→8,0, lactato 4,40→4,72; D 60,0→22,0, lactato 4,40→4,90; D 20,0→8,1, lactato 4,40→4,16 |
| gi_bleed_57m | L4 (contrafactual), 0–120 min: D sigue igual o por encima de la llegada mientras el lactato se mueve menos de 0,5 mmol/L | 180 | 1054 | D 0,0→22,6, lactato 4,40→3,97; D 0,0→61,6, lactato 4,40→4,33; D 60,0→121,6, lactato 4,40→4,54 |
| gi_bleed_72f | L1, 0–60 min: D sube mientras el lactato baja | 667 | 1054 | D 0,0→6,4, lactato 3,40→1,53; D 0,0→27,9, lactato 3,40→2,83; D 0,0→27,9, lactato 3,40→3,27 |
| gi_bleed_72f | L1, 0–120 min: D sube mientras el lactato baja | 514 | 1054 | D 0,0→25,7, lactato 3,40→1,30; D 60,0→85,7, lactato 3,40→2,70; D 20,0→50,1, lactato 3,40→3,38 |
| gi_bleed_72f | L3, 0–120 min: D baja mientras el lactato sigue a menos de 0,5 mmol/L de la llegada o por encima | 279 | 1054 | D 60,0→8,0, lactato 3,40→3,45; D 60,0→22,0, lactato 3,40→3,36; D 20,0→8,4, lactato 3,40→3,10 |
| gi_bleed_72f | L4 (contrafactual), 0–120 min: D sigue igual o por encima de la llegada mientras el lactato se mueve menos de 0,5 mmol/L | 271 | 1054 | D 0,0→15,0, lactato 3,40→3,19; D 60,0→117,0, lactato 3,40→3,47; D 0,0→57,0, lactato 3,40→3,11 |

## 7. Impacto de cada parámetro en las lecturas de las decisiones

ALTO ≥ 1 mmol/L (o ≥ 30 min), MEDIO ≥ 0,3 mmol/L (o ≥ 10 min), BAJO por debajo: bandas de presentación, no criterios. Cada valor por nivel es la mediana de la lectura sobre los conjuntos con ese nivel. La región no es un diseño balanceado: no contiene τ_D = 30 con la deuda de llegada alta, así que el efecto de `debt_clearance_tau_min` se mezcla en parte con el de la deuda. `debt_per_delivery_deficit` y `metabolic_demand_baseline` no varían en la región; se sondean de a uno alrededor del candidato medio.

**gi_bleed_57m · L1: cambio a los 60 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: -1,70, 120: -0,61, 240: 0,01 | 1,71 | efecto principal sobre la región admisible |
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: -1,03, medio: -0,61, superior: 0,63 | 1,66 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | MEDIO | la disminuye | inferior: -0,37, medio: -0,61, superior: -0,70 | 0,32 | efecto principal sobre la región admisible |
| `debt_per_delivery_deficit` | MEDIO | la aumenta | 0,5: -0,71, 1: -0,61, 2: -0,40 | 0,31 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_clearance_tau_min` | BAJO | la aumenta | 30: -0,85, 60: -0,59, 120: -0,59 | 0,27 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | BAJO | la disminuye | inferior: -0,43, medio: -0,65, superior: -0,70 | 0,27 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: -0,69, 1: -0,61, 1,1: -0,53 | 0,17 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `lactate_per_output_deficit` | BAJO | sin efecto | 2: -0,65, 6: -0,65, 12: -0,65 | 0,00 | efecto principal sobre la región admisible |

**gi_bleed_57m · L3: primera caída clara (min; 121 = no en 120)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 20, medio: 31, superior: 114 | 94 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: 11, 120: 31, 240: 76 | 65 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 47, medio: 30, superior: 27 | 20 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | MEDIO | la disminuye | inferior: 42, medio: 31, superior: 28 | 14 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | BAJO | la aumenta | 30: 27, 60: 36, 120: 36 | 9 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 30, 1: 31, 1,1: 33 | 3 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 31, 1: 31, 2: 32 | 1 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `lactate_per_output_deficit` | BAJO | sin efecto | 2: 33, 6: 33, 12: 33 | 0 | efecto principal sobre la región admisible |

**gi_bleed_57m · L3: lactato a los 120 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: 1,62, 120: 2,88, 240: 3,57 | 1,95 | efecto principal sobre la región admisible |
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 2,29, medio: 2,66, superior: 3,81 | 1,52 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 3,16, medio: 2,45, superior: 2,32 | 0,84 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | MEDIO | la aumenta | 30: 2,33, 60: 2,98, 120: 3,05 | 0,72 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | MEDIO | no monótona | inferior: 3,05, medio: 2,66, superior: 2,88 | 0,39 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 2,57, 1: 2,61, 1,1: 2,66 | 0,08 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 2,60, 1: 2,61, 2: 2,62 | 0,02 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `lactate_per_output_deficit` | BAJO | sin efecto | 2: 2,88, 6: 2,88, 12: 2,88 | 0,00 | efecto principal sobre la región admisible |

**gi_bleed_72f · L1: cambio a los 60 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: -0,65, medio: -0,24, superior: 1,01 | 1,66 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: -0,98, 120: -0,24, 240: 0,21 | 1,19 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 0,09, medio: -0,47, superior: -0,51 | 0,60 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | MEDIO | la disminuye | inferior: -0,17, medio: -0,24, superior: -0,49 | 0,32 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | BAJO | la aumenta | 30: -0,51, 60: -0,24, 120: -0,24 | 0,27 | efecto principal sobre la región admisible |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: -0,33, 1: -0,24, 2: -0,06 | 0,27 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: -0,33, 1: -0,24, 1,1: -0,16 | 0,17 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `lactate_per_output_deficit` | BAJO | sin efecto | 2: -0,32, 6: -0,32, 12: -0,32 | 0,00 | efecto principal sobre la región admisible |

**gi_bleed_72f · L3: primera caída clara (min; 121 = no en 120)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: 20, 120: 55, 240: 121 | 101 | efecto principal sobre la región admisible |
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 30, medio: 55, superior: 121 | 91 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | ALTO | la disminuye | inferior: 106, medio: 49, superior: 44 | 62 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | ALTO | la aumenta | 30: 44, 60: 70, 120: 80 | 36 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | MEDIO | la disminuye | inferior: 80, medio: 55, superior: 53 | 27 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | MEDIO | la aumenta | 0,9: 51, 1: 55, 1,1: 61 | 10 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 54, 1: 55, 2: 57 | 3 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `lactate_per_output_deficit` | BAJO | sin efecto | 2: 56, 6: 56, 12: 56 | 0 | efecto principal sobre la región admisible |

**gi_bleed_72f · L3: lactato a los 120 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 2,12, medio: 2,37, superior: 3,64 | 1,51 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: 1,56, 120: 2,51, 240: 3,03 | 1,48 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 2,85, medio: 2,26, superior: 2,09 | 0,76 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | MEDIO | la aumenta | 30: 2,15, 60: 2,51, 120: 2,68 | 0,53 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | BAJO | no monótona | inferior: 2,65, medio: 2,37, superior: 2,45 | 0,28 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 2,21, 1: 2,26, 1,1: 2,33 | 0,12 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 2,26, 1: 2,26, 2: 2,28 | 0,02 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `lactate_per_output_deficit` | BAJO | sin efecto | 2: 2,45, 6: 2,45, 12: 2,45 | 0,00 | efecto principal sobre la región admisible |

## 8. Lo que el modelo ofrece para cada pregunta (sólo modelo)

Sólo trayectorias producidas por el motor: L1 para FD-LAC-02/03/06 y L3 para FD-LAC-04/05. La composición contrafactual L4 no entra en ninguna.

**gi_bleed_57m** (lactato de llegada 4,4)

- Sin tratar, a los 60 min (FD-LAC-02/03): mínimo 1,81, p10 2,20, mediana 3,75, p90 5,47, máximo 6,06 (1054 corridas).
- Primera caída clara (≥ 0,5 mmol/L bajo la llegada) tras el manejo definitivo (FD-LAC-04): en 15 min: 30 %, 15–30 min: 18 %, 30–60 min: 21 %, después de 60 min: 15 %, no en 120 min: 16 %.
- A los 120 min tras el manejo definitivo (FD-LAC-05): de 1,04 a 6,05, mediana 2,88; mediana sobre la basal candidata 1,45; mediana según la deuda de llegada: inferior 2,29, medio 2,66, superior 3,81.
- Sin tratar, con la entrega bajo la demanda a los 0, 15, 30 y 60 min (FD-LAC-06): 649 corridas; en 460 el lactato baja.

**gi_bleed_72f** (lactato de llegada 3,4)

- Sin tratar, a los 60 min (FD-LAC-02/03): mínimo 1,53, p10 1,92, mediana 3,08, p90 4,71, máximo 5,27 (1054 corridas).
- Primera caída clara (≥ 0,5 mmol/L bajo la llegada) tras el manejo definitivo (FD-LAC-04): en 15 min: 15 %, 15–30 min: 16 %, 30–60 min: 21 %, después de 60 min: 19 %, no en 120 min: 29 %.
- A los 120 min tras el manejo definitivo (FD-LAC-05): de 0,98 a 5,68, mediana 2,45; mediana sobre la basal candidata 1,10; mediana según la deuda de llegada: inferior 2,12, medio 2,37, superior 3,64.
- Sin tratar, con la entrega bajo la demanda a los 0, 15, 30 y 60 min (FD-LAC-06): 649 corridas; en 388 el lactato baja.

## 9. REFERENCIA HEREDADA — NO ES OBJETIVO DE CALIBRACIÓN

El lactato que reporta el motor de familias en los mismos escenarios. Ninguna tabla ni clase de arriba la lee.

| Caso | Escenario | 0 min | 15 min | 30 min | 60 min | 90 min | 120 min |
|---|---|---|---|---|---|---|---|
| gi_bleed_57m | L1 | 4,4 | 4,5 | 4,6 | 4,8 | 4,9 | 5,1 |
| gi_bleed_57m | L2 | 4,4 | 4,1 | 4,2 | 4,5 | 4,7 | 4,9 |
| gi_bleed_57m | L3 | 4,4 | 4,1 | 3,8 | 3,2 | 3,3 | 3,3 |
| gi_bleed_57m | L4 (contrafactual: el motor difiere esta endoscopia y no tiene trayectoria L4) | — | — | — | — | — | — |
| gi_bleed_72f | L1 | 3,4 | 3,5 | 3,6 | 3,8 | 3,9 | 4,1 |
| gi_bleed_72f | L2 | 3,4 | 3,1 | 3,2 | 3,5 | 3,7 | 3,9 |
| gi_bleed_72f | L3 | 3,4 | 3,1 | 2,8 | 2,2 | 2,3 | 2,3 |
| gi_bleed_72f | L4 (contrafactual: el motor difiere esta endoscopia y no tiene trayectoria L4) | — | — | — | — | — | — |

<!-- /generado:lactato -->

## 10. Hoja de trabajo docente (FD-LAC)

La docencia respondió el 2026-10-25 y aclaró FD-LAC-01, FD-LAC-04 y FD-LAC-05 el 2026-10-26 (versión «FD-LAC v2»).
La selección resume la opción elegida, ya aclarada; el texto que rige está en §12, tal como lo escribió la docencia. Las
opciones del modelo para cada pregunta están en §8.

| ID | Pregunta | Opciones | Selección docente | Estado |
|---|---|---|---|---|
| FD-LAC-01 | En la hemorragia sin tratar con perfusión que empeora, el lactato debe… | A. poder bajar desde la llegada / B. mantenerse aproximadamente estable / C. subir en general / D. exigir una subida mínima en 60 min | C. subir o seguir elevado en general; sin descenso sostenido y sustancial antes de los 60 min; sin subida mínima obligatoria | FACULTY_APPROVED |
| FD-LAC-02 | 57m: ¿qué rango de lactato a los 60 min sin tratar es clínicamente aceptable? | el rango que ofrece el modelo para 57m (§8) u otro que la docencia fije | 4,4–7,0 mmol/L a los 60 min: envolvente clínica, no un objetivo | FACULTY_APPROVED |
| FD-LAC-03 | 72f: ¿qué rango de lactato a los 60 min sin tratar es clínicamente aceptable? | el rango que ofrece el modelo para 72f (§8) u otro que la docencia fije | 3,4–5,5 mmol/L a los 60 min: envolvente clínica, no un objetivo | FACULTY_APPROVED |
| FD-LAC-04 | Tras la hemostasia exitosa y la reanimación adecuada, ¿cuándo debe verse por primera vez una tendencia clara a la baja? | en 15 min / 15–30 min / 30–60 min / después de 60 min | 15–30 min: L(T*+30) < L(T*) con aclaramiento en curso; ningún porcentaje fijo aprobado | FACULTY_APPROVED |
| FD-LAC-05 | A los 120 min del manejo exitoso, el lactato debe… | seguir sustancialmente elevado / seguir levemente elevado / estar cerca de la basal de llegada / depender mucho de la deuda acumulada inicial | a los 120 min con entrega adecuada sostenida: 1,5–4,0 (57m) y 1,2–3,5 (72f) mmol/L, y L120 < L(T*) | FACULTY_APPROVED |
| FD-LAC-06 | ¿Puede la hemorragia activa con perfusión que sigue empeorando mostrar un lactato en descenso sólo porque se aclara el lactato aclarable de llegada? | SÍ / NO / SÓLO SI LA ENTREGA ES ADECUADA | SÓLO SI LA ENTREGA ES ADECUADA | FACULTY_APPROVED |

## 11. Lo que este corte no hace

- No aprueba valores. En el registro de calibración FACULTY_APPROVED sigue en 0: las decisiones FD-LAC aprueban
  comportamiento, no parámetros. Los registros de autoridad siguen vacíos y la puerta de migración sigue fallando para
  57m y 72f.
- No elige candidatos por su parecido con el motor de familias.
- No cambia la fisiología, las bandas, las reglas congeladas, los escenarios del golden ni el golden.
- No abre FC, PA, FR, volumen ni colapso.

<!-- generado:decisiones-lactato -->
## 12. Registro de decisiones docentes (P2I-2 y P2I-2R)

Respondidas por la docencia el 2026-10-25 y aclaradas el 2026-10-26 (versión «FD-LAC v2»), registradas en `clinical_core/faculty_constraints.py`. Son restricciones clínicas de comportamiento del lactato observable, con estado FACULTY_APPROVED. **No aprueban ningún valor de parámetro oculto:** `arrival_oxygen_debt`, `arrival_lactate_excess`, `debt_clearance_tau_min`, `debt_per_delivery_deficit`, `lactate_per_output_deficit`, `lactate_clearance_tau_min`, `arrival_delivery_ratio`, `metabolic_demand_baseline` siguen CANDIDATE, y nada de esto entra en los registros de autoridad de migración. Las envolventes de FD-LAC-05 son envolventes clínicas de calibración para estos casos GI, no límites fisiológicos universales. El texto que rige es el original, en inglés: la decisión y, cuando la hay, su aclaración. La docencia no dio un fundamento aparte: la columna «Frase clave» cita la frase de su propio texto que lo expresa. Su aplicación a la región candidata está en `docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md`.

| ID | Estado | Fecha · versión | Observable | Escenarios · casos | Decisión (texto original) | Aclaración docente (texto original) | Frase clave del texto docente | Valores de parámetros que aprueba |
|---|---|---|---|---|---|---|---|---|
| FD-LAC-01 | FACULTY_APPROVED | 2026-10-25, aclarada 2026-10-26 · FD-LAC v2 | trayectoria del lactato antes de los 60 min, con sangrado activo y entrega de O2 inadecuada | L1 · 57m, 72f | «With ongoing active haemorrhage and persistently inadequate/worsening oxygen delivery, lactate should GENERALLY RISE. A brief period of stability is acceptable. A sustained fall should NOT be the typical trajectory when oxygen delivery remains inadequate. Do NOT interpret this as: "lactate must rise every minute." The clinically important requirement is the trajectory over meaningful reassessment intervals.» | «Do NOT encode: L60 >= L0 as a universal physiological law. Faculty intent is: With active haemorrhage AND persistent/significant inadequate oxygen delivery, a substantial sustained fall in lactate should not be the dominant/acceptable trajectory. Lactate should generally remain elevated or rise. The case-specific 60-min clinical envelopes remain: 57m: 4.4-7.0 mmol/L 72f: 3.4-5.5 mmol/L These envelopes are the hard 60-min clinical constraints. For the trajectory before 60 min: retain the approved rule against a sustained substantial decline during persistent inadequate delivery. Do not require monotonic rise. Do not require a fixed percentage increase. Do not treat a small transient decrease as automatically physiologically invalid. Operationalize "substantial sustained decline" using the previously frozen clinically meaningful reassessment-window concept and expose sensitivity to the chosen percentage threshold.» | «The clinically important requirement is the trajectory over meaningful reassessment intervals.» | ninguno |
| FD-LAC-02 | FACULTY_APPROVED | 2026-10-25 · FD-LAC v2 | lactato (mmol/L) a los 60 min sin tratar | L1 · 57m | «APPROVED clinical band: arrival lactate: 4.4 mmol/L. 60-min untreated acceptable band: 4.4-7.0 mmol/L. Preferred direction: stable-to-rising, usually rising. Do NOT convert the midpoint of this band into a target. Values are a clinical acceptance envelope.» | sin cambios | «Values are a clinical acceptance envelope.» | ninguno |
| FD-LAC-03 | FACULTY_APPROVED | 2026-10-25 · FD-LAC v2 | lactato (mmol/L) a los 60 min sin tratar | L1 · 72f | «APPROVED clinical band: arrival lactate: 3.4 mmol/L. 60-min untreated acceptable band: 3.4-5.5 mmol/L. Preferred direction: stable-to-rising, usually rising. Again, this is a clinical envelope, not a point target.» | sin cambios | «Again, this is a clinical envelope, not a point target.» | ninguno |
| FD-LAC-04 | FACULTY_APPROVED | 2026-10-25, aclarada 2026-10-26 · FD-LAC v2 | lactato en T* + 30 min frente a T*, tras la hemostasia y con entrega adecuada sostenida | L3 · 57m, 72f | «After successful haemostasis AND adequate sustained restoration of oxygen delivery, a CLEAR downward lactate trend should begin within: 15-30 minutes. This means onset of a meaningful downward trend. It does NOT mean: normalization by 30 minutes; arbitrary fixed mmol/L decline; clearance independent of accumulated debt.» | «T* = the later of: A. haemostasis B. onset of adequate oxygen delivery that remains adequate for the required sustained period. Lactate may already be falling before T*; do not require a new peak after T*; do not reset physiology at haemostasis; use L(T*) as the reference; if the run does not provide 30 min of follow-up, mark NOT_EVALUABLE; if oxygen delivery ceases to be adequate during the 30-min interval, mark NOT_EVALUABLE rather than FAIL. Do NOT require: L(T* + 30) <= 0.90 * L(T*) as a faculty-approved physiological constant. Faculty intent is: After haemostasis AND sustained adequate restoration of oxygen delivery, a clearly downward lactate trajectory should be evident within 30 minutes. Therefore: by T* + 30 min: L(T* + 30) < L(T*) with a trajectory consistent with ongoing clearance. A fixed 10% reduction at 30 min is NOT yet faculty-approved. Report the actual percentage reduction at 30 min for each surviving candidate. Then separately evaluate candidate thresholds such as: any decrease, >=5%, >=10%, >=15% as SENSITIVITY ANALYSIS ONLY. If L(T*) <= 2.0 mmol/L: classify ALREADY_NORMALIZED and satisfy/not-applicable.» | «This means onset of a meaningful downward trend.» | ninguno |
| FD-LAC-05 | FACULTY_APPROVED | 2026-10-25, aclarada 2026-10-26 · FD-LAC v2 | lactato (mmol/L) a los 120 min del manejo definitivo, con entrega adecuada sostenida | L3 · 57m, 72f | «Residual lactate at 120 min should depend materially on accumulated oxygen debt. Typical severe-shock trajectories may remain MILDLY ELEVATED. Do NOT require full normalization within 120 minutes. Do NOT encode one fixed 120-min lactate target. The model should preserve memory of prior debt.» | «Faculty now approves case-specific 120-min clinical envelopes after successful definitive management with sustained adequate oxygen delivery. 57m: 1.5 <= L120 <= 4.0 mmol/L 72f: 1.2 <= L120 <= 3.5 mmol/L Additionally: L120 < L(T*) must hold when adequate oxygen delivery remained sustained after T*. These are clinical acceptance envelopes, NOT target values. Do not tune toward the midpoint. A value below 2 mmol/L is allowed. Normalization by 120 min is NOT required. Treat these as faculty clinical calibration envelopes for the current GI cases, not universal human physiological limits.» | «The model should preserve memory of prior debt.» | ninguno |
| FD-LAC-06 | FACULTY_APPROVED | 2026-10-25 · FD-LAC v2 | trayectoria del lactato con sangrado activo, según la adecuación de la entrega | L1, L2, L3 · 57m, 72f | «ONLY IF OXYGEN DELIVERY IS ADEQUATE. Active haemorrhage by itself does not require lactate to rise. If resuscitation maintains/restores adequate oxygen delivery despite ongoing bleeding, lactate may fall. However: active bleeding + persistent/worsening inadequate oxygen delivery must NOT produce a sustained declining lactate trajectory. This rule takes precedence over diagnosis labels.» | sin cambios | «This rule takes precedence over diagnosis labels.» | ninguno |

**Definiciones operativas confirmadas por la docencia (2026-10-26, texto original):** «inadequate delivery = oxygen delivery < oxygen demand»; «evaluation should use clinically meaningful reassessment intervals rather than minute-to-minute noise»; «sustained decline during inadequate delivery may be operationalized as a >=10% decline over a >=30-min interval»; «FD-LAC-06 applies according to physiology, not diagnosis label»; «active bleeding may coexist with falling lactate ONLY when delivery is adequate»; «D and lactate remain distinct state/observable concepts»; «arrival need not be steady state».

<!-- /generado:decisiones-lactato -->
