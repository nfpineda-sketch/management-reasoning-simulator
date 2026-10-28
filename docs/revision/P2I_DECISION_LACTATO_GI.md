# P2I-1 · Decisión docente: el lactato en la hemorragia digestiva (GI)

Apoyo a una decisión. El corte de P2I-1 no aprobó ningún número. La docencia respondió después FD-LAC-01 a FD-LAC-06
(§10 y §12): son restricciones clínicas de comportamiento del lactato, con estado FACULTY_APPROVED, y **no aprueban
ningún valor de parámetro oculto**. Todos los valores siguen CANDIDATE, los registros de autoridad siguen vacíos, el GI
no se migra y el golden canónico no cambia. Su aplicación a la región candidata está en
`docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md`. FC, PA, FR, volumen y colapso siguen sin abrirse.

- **Generado desde:** el congelamiento de calibración
  `a8f00e04320823d24d5d1d802ae2eae14564fb970da4d7c0d44c65368fc9a8b0` y el corte
  `15202cd878380edbde1d92ed6db28b67d0802c946a6640e2917db8bd1f5af549` (`python -m clinical_core.lactate_slice`).
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
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,60 | 4,21 | 4,93 | 7,32 | 25 % | 75 % | 8 % | 2 % |
| gi_bleed_57m | 30 | 1054 | 2,64 | 3,18 | 4,09 | 5,50 | 9,79 | 26 % | 74 % | 26 % | 4 % |
| gi_bleed_57m | 60 | 1054 | 1,79 | 2,83 | 3,96 | 6,60 | 14,02 | 33 % | 67 % | 43 % | 18 % |
| gi_bleed_57m | 90 | 1054 | 1,43 | 2,79 | 4,14 | 8,04 | 17,93 | 42 % | 58 % | 52 % | 25 % |
| gi_bleed_57m | 120 | 1054 | 1,37 | 2,92 | 4,61 | 10,66 | 21,97 | 55 % | 45 % | 59 % | 32 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,89 | 3,30 | 4,01 | 6,61 | 32 % | 68 % | 7 % | 2 % |
| gi_bleed_72f | 30 | 1054 | 2,13 | 2,67 | 3,25 | 4,64 | 9,27 | 34 % | 66 % | 20 % | 7 % |
| gi_bleed_72f | 60 | 1054 | 1,51 | 2,42 | 3,29 | 6,09 | 13,63 | 46 % | 54 % | 33 % | 14 % |
| gi_bleed_72f | 90 | 1054 | 1,25 | 2,34 | 3,50 | 7,37 | 17,42 | 52 % | 48 % | 44 % | 23 % |
| gi_bleed_72f | 120 | 1054 | 1,19 | 2,47 | 3,93 | 9,67 | 21,10 | 62 % | 38 % | 51 % | 31 % |

**L2 · reanimación transitoria y parcial (2 L de salina en 20 min; el sangrado sigue)**

| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0 | 1054 | 4,40 | 4,40 | 4,40 | 4,40 | 4,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,58 | 4,20 | 4,89 | 7,30 | 25 % | 75 % | 7 % | 2 % |
| gi_bleed_57m | 30 | 1054 | 2,63 | 3,12 | 4,03 | 5,09 | 9,62 | 24 % | 76 % | 25 % | 3 % |
| gi_bleed_57m | 60 | 1054 | 1,74 | 2,59 | 3,82 | 5,42 | 13,21 | 24 % | 76 % | 40 % | 14 % |
| gi_bleed_57m | 90 | 1054 | 1,30 | 2,36 | 3,68 | 6,13 | 16,35 | 30 % | 70 % | 55 % | 20 % |
| gi_bleed_57m | 120 | 1054 | 1,13 | 2,34 | 3,81 | 7,50 | 19,55 | 36 % | 64 % | 61 % | 27 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,87 | 3,30 | 3,97 | 6,59 | 32 % | 68 % | 6 % | 2 % |
| gi_bleed_72f | 30 | 1054 | 2,12 | 2,65 | 3,24 | 4,49 | 9,16 | 33 % | 67 % | 18 % | 5 % |
| gi_bleed_72f | 60 | 1054 | 1,48 | 2,36 | 3,17 | 5,27 | 13,14 | 35 % | 65 % | 32 % | 9 % |
| gi_bleed_72f | 90 | 1054 | 1,16 | 2,11 | 3,21 | 6,19 | 16,44 | 43 % | 57 % | 44 % | 18 % |
| gi_bleed_72f | 120 | 1054 | 1,04 | 2,04 | 3,42 | 7,48 | 19,60 | 50 % | 50 % | 48 % | 24 % |

**L3 · control definitivo y reanimación adecuada (2 unidades en 60 min, IBP y endoscopia)**

| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0 | 1054 | 4,40 | 4,40 | 4,40 | 4,40 | 4,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,57 | 4,20 | 4,85 | 7,29 | 25 % | 75 % | 7 % | 2 % |
| gi_bleed_57m | 30 | 1054 | 2,63 | 3,06 | 4,02 | 5,07 | 9,53 | 23 % | 77 % | 25 % | 3 % |
| gi_bleed_57m | 60 | 1054 | 1,73 | 2,29 | 3,66 | 5,15 | 10,83 | 19 % | 81 % | 43 % | 15 % |
| gi_bleed_57m | 90 | 1054 | 1,28 | 1,76 | 3,33 | 4,94 | 9,52 | 15 % | 85 % | 62 % | 21 % |
| gi_bleed_57m | 120 | 1054 | 1,04 | 1,47 | 3,04 | 4,46 | 7,65 | 11 % | 89 % | 71 % | 33 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,86 | 3,29 | 3,97 | 6,58 | 32 % | 68 % | 6 % | 2 % |
| gi_bleed_72f | 30 | 1054 | 2,12 | 2,60 | 3,20 | 4,36 | 9,07 | 32 % | 68 % | 18 % | 5 % |
| gi_bleed_72f | 60 | 1054 | 1,48 | 2,10 | 3,04 | 4,64 | 11,59 | 28 % | 72 % | 30 % | 6 % |
| gi_bleed_72f | 90 | 1054 | 1,14 | 1,76 | 2,82 | 4,51 | 10,63 | 25 % | 75 % | 39 % | 12 % |
| gi_bleed_72f | 120 | 1054 | 0,98 | 1,49 | 2,57 | 4,27 | 8,66 | 19 % | 81 % | 47 % | 13 % |

**L4 · hemostasia sin recuperar la perfusión (IBP y endoscopia sin volumen) — COMPOSICIÓN CONTRAFACTUAL MANUAL: la hemostasia se agregó a mano en el minuto de L3; el motor no la produce**

> L4 contrafactual: no es una trayectoria que el motor heredado produzca. Se muestra sólo como contraste y ninguna pregunta de la hoja de trabajo la usa.

| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0 | 1054 | 4,40 | 4,40 | 4,40 | 4,40 | 4,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,60 | 4,21 | 4,93 | 7,32 | 25 % | 75 % | 8 % | 2 % |
| gi_bleed_57m | 30 | 1054 | 2,64 | 3,18 | 4,08 | 5,48 | 9,78 | 26 % | 74 % | 26 % | 4 % |
| gi_bleed_57m | 60 | 1054 | 1,78 | 2,78 | 3,95 | 6,54 | 13,94 | 33 % | 67 % | 43 % | 17 % |
| gi_bleed_57m | 90 | 1054 | 1,39 | 2,72 | 4,02 | 7,72 | 17,65 | 38 % | 62 % | 53 % | 24 % |
| gi_bleed_57m | 120 | 1054 | 1,26 | 2,66 | 4,35 | 9,96 | 21,16 | 49 % | 51 % | 58 % | 33 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,89 | 3,30 | 4,01 | 6,61 | 32 % | 68 % | 7 % | 2 % |
| gi_bleed_72f | 30 | 1054 | 2,13 | 2,67 | 3,24 | 4,63 | 9,26 | 34 % | 66 % | 20 % | 6 % |
| gi_bleed_72f | 60 | 1054 | 1,50 | 2,41 | 3,27 | 6,07 | 13,58 | 45 % | 55 % | 33 % | 14 % |
| gi_bleed_72f | 90 | 1054 | 1,22 | 2,26 | 3,44 | 7,11 | 17,23 | 51 % | 49 % | 45 % | 22 % |
| gi_bleed_72f | 120 | 1054 | 1,12 | 2,33 | 3,77 | 9,37 | 20,56 | 59 % | 41 % | 51 % | 30 % |

## 4. Clases de comportamiento (conteos sobre la región; ninguna se declara correcta)

**gi_bleed_57m**

| Escenario y lectura | Clase | n | Dónde se concentra (mayor proporción por factor) |
|---|---|---|---|
| L1 a los 60 min | A baja | 483 | `arrival_delivery_ratio` superior (52 %); `arrival_lactate_excess` superior (40 %); `arrival_oxygen_debt` inferior (71 %); `debt_clearance_tau_min` 120 (46 %); `lactate_clearance_tau_min` 45 (42 %); `lactate_per_output_deficit` 2 (56 %) |
| L1 a los 60 min | B aproximadamente estable | 301 | `arrival_delivery_ratio` inferior (46 %); `arrival_lactate_excess` inferior (45 %); `arrival_oxygen_debt` inferior (38 %); `debt_clearance_tau_min` 120 (40 %); `lactate_clearance_tau_min` 240 (58 %); `lactate_per_output_deficit` 6 (45 %) |
| L1 a los 60 min | C sube moderadamente | 144 | `arrival_delivery_ratio` inferior (40 %); `arrival_lactate_excess` inferior (38 %); `arrival_oxygen_debt` superior (54 %); `debt_clearance_tau_min` 60 (40 %); `lactate_clearance_tau_min` 120 (42 %); `lactate_per_output_deficit` 12 (56 %) |
| L1 a los 60 min | D sube sustancialmente | 126 | `arrival_delivery_ratio` inferior (48 %); `arrival_lactate_excess` inferior (40 %); `arrival_oxygen_debt` superior (74 %); `debt_clearance_tau_min` 60 (60 %); `lactate_clearance_tau_min` 45 (62 %); `lactate_per_output_deficit` 12 (81 %) |
| L1 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 483 | |
| L1 a los 120 min | A baja | 354 | `arrival_delivery_ratio` superior (53 %); `arrival_lactate_excess` superior (39 %); `arrival_oxygen_debt` inferior (64 %); `debt_clearance_tau_min` 120 (59 %); `lactate_clearance_tau_min` 120 (36 %); `lactate_per_output_deficit` 2 (70 %) |
| L1 a los 120 min | B aproximadamente estable | 211 | `arrival_delivery_ratio` inferior (41 %); `arrival_lactate_excess` inferior (38 %); `arrival_oxygen_debt` inferior (47 %); `debt_clearance_tau_min` 60 (40 %); `lactate_clearance_tau_min` 240 (54 %); `lactate_per_output_deficit` 2 (43 %) |
| L1 a los 120 min | C sube moderadamente | 186 | `arrival_delivery_ratio` superior (37 %); `arrival_lactate_excess` inferior (39 %); `arrival_oxygen_debt` inferior (42 %); `debt_clearance_tau_min` 120 (37 %); `lactate_clearance_tau_min` 240 (39 %); `lactate_per_output_deficit` 6 (52 %) |
| L1 a los 120 min | D sube sustancialmente | 303 | `arrival_delivery_ratio` inferior (50 %); `arrival_lactate_excess` inferior (39 %); `arrival_oxygen_debt` superior (49 %); `debt_clearance_tau_min` 60 (48 %); `lactate_clearance_tau_min` 45 (44 %); `lactate_per_output_deficit` 12 (69 %) |
| L1 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 354 | |
| L2 a los 60 min | A baja | 606 | `arrival_delivery_ratio` superior (48 %); `arrival_lactate_excess` superior (38 %); `arrival_oxygen_debt` inferior (68 %); `debt_clearance_tau_min` 120 (43 %); `lactate_clearance_tau_min` 45 (39 %); `lactate_per_output_deficit` 2 (48 %) |
| L2 a los 60 min | B aproximadamente estable | 271 | `arrival_delivery_ratio` inferior (43 %); `arrival_lactate_excess` inferior (46 %); `arrival_oxygen_debt` superior (43 %); `debt_clearance_tau_min` 60 (42 %); `lactate_clearance_tau_min` 240 (55 %); `lactate_per_output_deficit` 6 (48 %) |
| L2 a los 60 min | C sube moderadamente | 120 | `arrival_delivery_ratio` inferior (42 %); `arrival_lactate_excess` inferior (42 %); `arrival_oxygen_debt` superior (68 %); `debt_clearance_tau_min` 60 (38 %); `lactate_clearance_tau_min` 120 (40 %); `lactate_per_output_deficit` 12 (78 %) |
| L2 a los 60 min | D sube sustancialmente | 57 | `arrival_delivery_ratio` inferior (79 %); `arrival_lactate_excess` inferior (37 %); `arrival_oxygen_debt` superior (95 %); `debt_clearance_tau_min` 60 (79 %); `lactate_clearance_tau_min` 45 (68 %); `lactate_per_output_deficit` 12 (84 %) |
| L2 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 606 | |
| L2 a los 120 min | A baja | 549 | `arrival_delivery_ratio` superior (55 %); `arrival_lactate_excess` superior (38 %); `arrival_oxygen_debt` inferior (62 %); `debt_clearance_tau_min` 120 (47 %); `lactate_clearance_tau_min` 120 (36 %); `lactate_per_output_deficit` 2 (56 %) |
| L2 a los 120 min | B aproximadamente estable | 190 | `arrival_delivery_ratio` inferior (47 %); `arrival_lactate_excess` inferior (39 %); `arrival_oxygen_debt` superior (41 %); `debt_clearance_tau_min` 60 (46 %); `lactate_clearance_tau_min` 240 (54 %); `lactate_per_output_deficit` 6 (49 %) |
| L2 a los 120 min | C sube moderadamente | 147 | `arrival_delivery_ratio` inferior (49 %); `arrival_lactate_excess` inferior (39 %); `arrival_oxygen_debt` superior (43 %); `debt_clearance_tau_min` 60 (43 %); `lactate_clearance_tau_min` 240 (41 %); `lactate_per_output_deficit` 12 (55 %) |
| L2 a los 120 min | D sube sustancialmente | 168 | `arrival_delivery_ratio` inferior (70 %); `arrival_lactate_excess` inferior (41 %); `arrival_oxygen_debt` superior (55 %); `debt_clearance_tau_min` 60 (48 %); `lactate_clearance_tau_min` 45 (52 %); `lactate_per_output_deficit` 12 (79 %) |
| L2 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 549 | |
| L3 en 120 min | E baja claramente en 30 min | 408 | `arrival_delivery_ratio` superior (45 %); `arrival_lactate_excess` medio (38 %); `arrival_oxygen_debt` inferior (72 %); `debt_clearance_tau_min` 120 (41 %); `lactate_clearance_tau_min` 45 (58 %); `lactate_per_output_deficit` 2 (47 %) |
| L3 en 120 min | E' baja claramente después de 30 min | 460 | `arrival_delivery_ratio` inferior (34 %); `arrival_lactate_excess` inferior (36 %); `arrival_oxygen_debt` inferior (42 %); `debt_clearance_tau_min` 60 (37 %); `lactate_clearance_tau_min` 240 (59 %); `lactate_per_output_deficit` 6 (38 %) |
| L3 en 120 min | F sigue elevado con la entrega restaurada | 186 | `arrival_delivery_ratio` inferior (52 %); `arrival_lactate_excess` inferior (45 %); `arrival_oxygen_debt` superior (90 %); `debt_clearance_tau_min` 60 (53 %); `lactate_clearance_tau_min` 240 (44 %); `lactate_per_output_deficit` 12 (68 %) |
| L4 (contrafactual) en 120 min | E baja claramente en 30 min | 387 | `arrival_delivery_ratio` superior (47 %); `arrival_lactate_excess` superior (39 %); `arrival_oxygen_debt` inferior (73 %); `debt_clearance_tau_min` 120 (43 %); `lactate_clearance_tau_min` 45 (60 %); `lactate_per_output_deficit` 2 (47 %) |
| L4 (contrafactual) en 120 min | E' baja claramente después de 30 min | 174 | `arrival_delivery_ratio` superior (53 %); `arrival_lactate_excess` superior (36 %); `arrival_oxygen_debt` inferior (66 %); `debt_clearance_tau_min` 120 (47 %); `lactate_clearance_tau_min` 240 (79 %); `lactate_per_output_deficit` 2 (64 %) |
| L4 (contrafactual) en 120 min | F' sigue elevado sin restaurar la entrega | 493 | `arrival_delivery_ratio` inferior (43 %); `arrival_lactate_excess` inferior (42 %); `arrival_oxygen_debt` superior (52 %); `debt_clearance_tau_min` 60 (45 %); `lactate_clearance_tau_min` 240 (43 %); `lactate_per_output_deficit` 12 (48 %) |

**gi_bleed_72f**

| Escenario y lectura | Clase | n | Dónde se concentra (mayor proporción por factor) |
|---|---|---|---|
| L1 a los 60 min | A baja | 294 | `arrival_delivery_ratio` superior (61 %); `arrival_lactate_excess` superior (46 %); `arrival_oxygen_debt` inferior (81 %); `debt_clearance_tau_min` 120 (49 %); `lactate_clearance_tau_min` 45 (53 %); `lactate_per_output_deficit` 2 (55 %) |
| L1 a los 60 min | B aproximadamente estable | 430 | `arrival_delivery_ratio` inferior (42 %); `arrival_lactate_excess` inferior (41 %); `arrival_oxygen_debt` inferior (47 %); `debt_clearance_tau_min` 120 (40 %); `lactate_clearance_tau_min` 240 (53 %); `lactate_per_output_deficit` 2 (43 %) |
| L1 a los 60 min | C sube moderadamente | 186 | `arrival_delivery_ratio` inferior (47 %); `arrival_lactate_excess` inferior (42 %); `arrival_oxygen_debt` superior (52 %); `debt_clearance_tau_min` 60 (37 %); `lactate_clearance_tau_min` 120 (42 %); `lactate_per_output_deficit` 6 (50 %) |
| L1 a los 60 min | D sube sustancialmente | 144 | `arrival_delivery_ratio` inferior (42 %); `arrival_lactate_excess` inferior (38 %); `arrival_oxygen_debt` superior (67 %); `debt_clearance_tau_min` 60 (58 %); `lactate_clearance_tau_min` 45 (62 %); `lactate_per_output_deficit` 12 (79 %) |
| L1 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 294 | |
| L1 a los 120 min | A baja | 234 | `arrival_delivery_ratio` superior (60 %); `arrival_lactate_excess` superior (46 %); `arrival_oxygen_debt` inferior (73 %); `debt_clearance_tau_min` 120 (60 %); `lactate_clearance_tau_min` 120 (37 %); `lactate_per_output_deficit` 2 (73 %) |
| L1 a los 120 min | B aproximadamente estable | 285 | `arrival_delivery_ratio` superior (44 %); `arrival_lactate_excess` inferior (40 %); `arrival_oxygen_debt` inferior (54 %); `debt_clearance_tau_min` 120 (39 %); `lactate_clearance_tau_min` 240 (51 %); `lactate_per_output_deficit` 2 (51 %) |
| L1 a los 120 min | C sube moderadamente | 211 | `arrival_delivery_ratio` inferior (44 %); `arrival_lactate_excess` inferior (40 %); `arrival_oxygen_debt` inferior (40 %); `debt_clearance_tau_min` 120 (40 %); `lactate_clearance_tau_min` 240 (36 %); `lactate_per_output_deficit` 6 (47 %) |
| L1 a los 120 min | D sube sustancialmente | 324 | `arrival_delivery_ratio` inferior (50 %); `arrival_lactate_excess` inferior (39 %); `arrival_oxygen_debt` superior (51 %); `debt_clearance_tau_min` 60 (46 %); `lactate_clearance_tau_min` 45 (44 %); `lactate_per_output_deficit` 12 (66 %) |
| L1 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 234 | |
| L2 a los 60 min | A baja | 372 | `arrival_delivery_ratio` superior (64 %); `arrival_lactate_excess` superior (43 %); `arrival_oxygen_debt` inferior (81 %); `debt_clearance_tau_min` 120 (44 %); `lactate_clearance_tau_min` 45 (46 %); `lactate_per_output_deficit` 2 (48 %) |
| L2 a los 60 min | B aproximadamente estable | 412 | `arrival_delivery_ratio` inferior (46 %); `arrival_lactate_excess` inferior (42 %); `arrival_oxygen_debt` inferior (39 %); `debt_clearance_tau_min` 120 (42 %); `lactate_clearance_tau_min` 240 (56 %); `lactate_per_output_deficit` 2 (41 %) |
| L2 a los 60 min | C sube moderadamente | 174 | `arrival_delivery_ratio` inferior (38 %); `arrival_lactate_excess` inferior (40 %); `arrival_oxygen_debt` superior (59 %); `debt_clearance_tau_min` 60 (43 %); `lactate_clearance_tau_min` 120 (36 %); `lactate_per_output_deficit` 12 (57 %) |
| L2 a los 60 min | D sube sustancialmente | 96 | `arrival_delivery_ratio` inferior (59 %); `arrival_lactate_excess` inferior (47 %); `arrival_oxygen_debt` superior (69 %); `debt_clearance_tau_min` 60 (56 %); `lactate_clearance_tau_min` 45 (62 %); `lactate_per_output_deficit` 12 (84 %) |
| L2 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 372 | |
| L2 a los 120 min | A baja | 378 | `arrival_delivery_ratio` superior (67 %); `arrival_lactate_excess` superior (41 %); `arrival_oxygen_debt` inferior (73 %); `debt_clearance_tau_min` 120 (49 %); `lactate_clearance_tau_min` 45 (37 %); `lactate_per_output_deficit` 2 (56 %) |
| L2 a los 120 min | B aproximadamente estable | 256 | `arrival_delivery_ratio` inferior (42 %); `arrival_lactate_excess` inferior (43 %); `arrival_oxygen_debt` inferior (40 %); `debt_clearance_tau_min` 120 (41 %); `lactate_clearance_tau_min` 240 (52 %); `lactate_per_output_deficit` 2 (48 %) |
| L2 a los 120 min | C sube moderadamente | 192 | `arrival_delivery_ratio` inferior (47 %); `arrival_lactate_excess` inferior (44 %); `arrival_oxygen_debt` superior (44 %); `debt_clearance_tau_min` 60 (45 %); `lactate_clearance_tau_min` 240 (38 %); `lactate_per_output_deficit` 6 (50 %) |
| L2 a los 120 min | D sube sustancialmente | 228 | `arrival_delivery_ratio` inferior (61 %); `arrival_lactate_excess` inferior (37 %); `arrival_oxygen_debt` superior (50 %); `debt_clearance_tau_min` 60 (46 %); `lactate_clearance_tau_min` 45 (45 %); `lactate_per_output_deficit` 12 (72 %) |
| L2 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 378 | |
| L3 en 120 min | E baja claramente en 30 min | 255 | `arrival_delivery_ratio` superior (56 %); `arrival_lactate_excess` superior (45 %); `arrival_oxygen_debt` inferior (82 %); `debt_clearance_tau_min` 120 (42 %); `lactate_clearance_tau_min` 45 (72 %); `lactate_per_output_deficit` 2 (48 %) |
| L3 en 120 min | E' baja claramente después de 30 min | 439 | `arrival_delivery_ratio` superior (36 %); `arrival_lactate_excess` medio (37 %); `arrival_oxygen_debt` inferior (53 %); `debt_clearance_tau_min` 60 (37 %); `lactate_clearance_tau_min` 240 (42 %); `lactate_per_output_deficit` 2 (42 %) |
| L3 en 120 min | F sigue elevado con la entrega restaurada | 360 | `arrival_delivery_ratio` inferior (48 %); `arrival_lactate_excess` inferior (52 %); `arrival_oxygen_debt` superior (64 %); `debt_clearance_tau_min` 60 (46 %); `lactate_clearance_tau_min` 240 (47 %); `lactate_per_output_deficit` 12 (52 %) |
| L4 (contrafactual) en 120 min | E baja claramente en 30 min | 237 | `arrival_delivery_ratio` superior (58 %); `arrival_lactate_excess` superior (44 %); `arrival_oxygen_debt` inferior (85 %); `debt_clearance_tau_min` 120 (44 %); `lactate_clearance_tau_min` 45 (73 %); `lactate_per_output_deficit` 2 (46 %) |
| L4 (contrafactual) en 120 min | E' baja claramente después de 30 min | 150 | `arrival_delivery_ratio` superior (56 %); `arrival_lactate_excess` superior (42 %); `arrival_oxygen_debt` inferior (70 %); `debt_clearance_tau_min` 120 (54 %); `lactate_clearance_tau_min` 240 (52 %); `lactate_per_output_deficit` 2 (64 %) |
| L4 (contrafactual) en 120 min | F' sigue elevado sin restaurar la entrega | 667 | `arrival_delivery_ratio` inferior (44 %); `arrival_lactate_excess` inferior (43 %); `arrival_oxygen_debt` superior (44 %); `debt_clearance_tau_min` 60 (43 %); `lactate_clearance_tau_min` 240 (41 %); `lactate_per_output_deficit` 12 (41 %) |

## 5. Descomposición del mecanismo (exacta dada la trayectoria del déficit)

Exceso de lactato = lo que queda del exceso de llegada + lo que produce la D de llegada + lo producido por el déficit posterior. Suma exacta para las recurrencias del modelo; no es una atribución causal entre parámetros.

**gi_bleed_57m · bajo · L1** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 3,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 2, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 0,80 | 3,60 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,00 | 0,00 |
| 15 | 3,37 | 0,80 | 2,57 | 0,00 | 0,00 | 0,6 | 0,0 | 0,6 | 0,0 | 0,92 | 0,08 |
| 30 | 2,64 | 0,80 | 1,83 | 0,00 | 0,01 | 2,4 | 0,0 | 2,4 | 0,0 | 0,83 | 0,17 |
| 60 | 1,79 | 0,80 | 0,93 | 0,00 | 0,05 | 9,7 | 0,0 | 9,7 | 0,0 | 0,67 | 0,33 |
| 90 | 1,43 | 0,80 | 0,48 | 0,00 | 0,16 | 21,9 | 0,0 | 21,9 | 0,0 | 0,51 | 0,49 |
| 120 | 1,37 | 0,80 | 0,24 | 0,00 | 0,33 | 38,7 | 0,0 | 38,7 | 0,0 | 0,36 | 0,64 |

**gi_bleed_57m · bajo · L3** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 3,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 2, τ_L 45, demanda 1,00

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
| 15 | 4,25 | 1,00 | 3,00 | 0,24 | 0,01 | 22,7 | 20,0 | 2,7 | 0,0 | 0,78 | 0,22 |
| 30 | 4,15 | 1,00 | 2,65 | 0,44 | 0,07 | 26,5 | 20,0 | 6,5 | 0,0 | 0,71 | 0,29 |
| 60 | 4,16 | 1,00 | 2,06 | 0,79 | 0,31 | 37,3 | 20,0 | 17,3 | 0,0 | 0,57 | 0,43 |
| 90 | 4,44 | 1,00 | 1,60 | 1,06 | 0,78 | 52,1 | 20,0 | 32,1 | 0,0 | 0,44 | 0,56 |
| 120 | 5,04 | 1,00 | 1,25 | 1,27 | 1,52 | 70,9 | 20,0 | 50,9 | 0,0 | 0,31 | 0,69 |

**gi_bleed_57m · medio · L3** — `arrival_oxygen_debt` 20, `arrival_lactate_excess` 3,40, `arrival_delivery_ratio` 0,85, τ_D 60, g 1,0, G 6, τ_L 120, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 1,00 | 3,40 | 0,00 | 0,00 | 20,0 | 20,0 | 0,0 | 0,0 | 0,85 | 0,15 |
| 15 | 4,24 | 1,00 | 3,00 | 0,23 | 0,01 | 18,4 | 17,8 | 0,7 | 2,3 | 1,14 | 0,00 |
| 30 | 4,05 | 1,00 | 2,65 | 0,39 | 0,01 | 14,3 | 13,8 | 0,7 | 6,4 | 1,42 | 0,00 |
| 60 | 3,62 | 1,00 | 2,06 | 0,54 | 0,02 | 8,6 | 8,3 | 0,7 | 12,0 | 1,95 | 0,00 |
| 90 | 3,19 | 1,00 | 1,60 | 0,57 | 0,02 | 5,2 | 5,0 | 0,7 | 15,5 | 1,94 | 0,00 |
| 120 | 2,79 | 1,00 | 1,25 | 0,53 | 0,02 | 3,1 | 3,0 | 0,7 | 17,5 | 1,93 | 0,00 |

**gi_bleed_57m · alto · L1** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 2,00 | 2,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 7,32 | 2,00 | 1,71 | 3,43 | 0,18 | 66,4 | 60,0 | 6,4 | 0,0 | 0,55 | 0,45 |
| 30 | 9,79 | 2,00 | 1,22 | 5,89 | 0,69 | 73,4 | 60,0 | 13,4 | 0,0 | 0,50 | 0,50 |
| 60 | 14,02 | 2,00 | 0,62 | 8,88 | 2,51 | 89,8 | 60,0 | 29,8 | 0,0 | 0,40 | 0,60 |
| 90 | 17,93 | 2,00 | 0,32 | 10,41 | 5,20 | 109,1 | 60,0 | 49,1 | 0,0 | 0,31 | 0,69 |
| 120 | 21,97 | 2,00 | 0,16 | 11,19 | 8,61 | 131,2 | 60,0 | 71,2 | 0,0 | 0,22 | 0,78 |

**gi_bleed_57m · alto · L3** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 2,00 | 2,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 7,29 | 2,00 | 1,71 | 3,43 | 0,14 | 64,6 | 60,0 | 4,6 | 0,0 | 0,80 | 0,20 |
| 30 | 9,53 | 2,00 | 1,22 | 5,89 | 0,42 | 66,1 | 60,0 | 6,1 | 0,0 | 1,00 | 0,00 |
| 60 | 10,83 | 2,00 | 0,62 | 7,53 | 0,68 | 39,9 | 36,2 | 6,1 | 26,2 | 1,37 | 0,00 |
| 90 | 9,52 | 2,00 | 0,32 | 6,57 | 0,62 | 24,1 | 21,9 | 6,1 | 42,0 | 1,37 | 0,00 |
| 120 | 7,65 | 2,00 | 0,16 | 5,00 | 0,49 | 14,6 | 13,2 | 6,1 | 51,6 | 1,36 | 0,00 |

**gi_bleed_72f · bajo · L1** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 2,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 2, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 0,80 | 2,60 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,00 | 0,00 |
| 15 | 2,66 | 0,80 | 1,86 | 0,00 | 0,00 | 0,4 | 0,0 | 0,4 | 0,0 | 0,95 | 0,05 |
| 30 | 2,13 | 0,80 | 1,32 | 0,00 | 0,00 | 1,6 | 0,0 | 1,6 | 0,0 | 0,89 | 0,11 |
| 60 | 1,51 | 0,80 | 0,68 | 0,00 | 0,03 | 6,4 | 0,0 | 6,4 | 0,0 | 0,78 | 0,22 |
| 90 | 1,25 | 0,80 | 0,34 | 0,00 | 0,10 | 14,5 | 0,0 | 14,5 | 0,0 | 0,68 | 0,32 |
| 120 | 1,19 | 0,80 | 0,18 | 0,00 | 0,22 | 25,7 | 0,0 | 25,7 | 0,0 | 0,57 | 0,43 |

**gi_bleed_72f · bajo · L3** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 2,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 2, τ_L 45, demanda 1,00

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
| 15 | 3,37 | 1,00 | 2,12 | 0,24 | 0,01 | 22,6 | 20,0 | 2,6 | 0,0 | 0,80 | 0,20 |
| 30 | 3,37 | 1,00 | 1,87 | 0,44 | 0,06 | 25,9 | 20,0 | 5,9 | 0,0 | 0,76 | 0,24 |
| 60 | 3,51 | 1,00 | 1,45 | 0,79 | 0,27 | 34,5 | 20,0 | 14,5 | 0,0 | 0,67 | 0,33 |
| 90 | 3,84 | 1,00 | 1,13 | 1,06 | 0,65 | 45,8 | 20,0 | 25,8 | 0,0 | 0,58 | 0,42 |
| 120 | 4,38 | 1,00 | 0,88 | 1,27 | 1,23 | 59,8 | 20,0 | 39,8 | 0,0 | 0,49 | 0,51 |

**gi_bleed_72f · medio · L3** — `arrival_oxygen_debt` 20, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,85, τ_D 60, g 1,0, G 6, τ_L 120, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 1,00 | 2,40 | 0,00 | 0,00 | 20,0 | 20,0 | 0,0 | 0,0 | 0,85 | 0,15 |
| 15 | 3,36 | 1,00 | 2,12 | 0,23 | 0,01 | 19,5 | 18,7 | 0,9 | 1,4 | 1,07 | 0,00 |
| 30 | 3,28 | 1,00 | 1,87 | 0,40 | 0,01 | 15,2 | 14,5 | 0,9 | 5,7 | 1,28 | 0,00 |
| 60 | 3,04 | 1,00 | 1,45 | 0,57 | 0,02 | 9,2 | 8,8 | 0,9 | 11,7 | 1,67 | 0,00 |
| 90 | 2,75 | 1,00 | 1,13 | 0,59 | 0,02 | 5,5 | 5,3 | 0,9 | 15,3 | 1,67 | 0,00 |
| 120 | 2,46 | 1,00 | 0,88 | 0,55 | 0,02 | 3,3 | 3,2 | 0,9 | 17,5 | 1,66 | 0,00 |

**gi_bleed_72f · alto · L1** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 1,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 2,00 | 1,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 6,61 | 2,00 | 1,00 | 3,43 | 0,17 | 66,2 | 60,0 | 6,2 | 0,0 | 0,57 | 0,43 |
| 30 | 9,27 | 2,00 | 0,71 | 5,89 | 0,67 | 73,0 | 60,0 | 13,0 | 0,0 | 0,53 | 0,47 |
| 60 | 13,63 | 2,00 | 0,36 | 8,88 | 2,38 | 87,9 | 60,0 | 27,9 | 0,0 | 0,47 | 0,53 |
| 90 | 17,42 | 2,00 | 0,19 | 10,41 | 4,82 | 104,7 | 60,0 | 44,7 | 0,0 | 0,41 | 0,59 |
| 120 | 21,10 | 2,00 | 0,09 | 11,19 | 7,81 | 123,4 | 60,0 | 63,4 | 0,0 | 0,34 | 0,66 |

**gi_bleed_72f · alto · L3** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 1,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 2,00 | 1,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 6,58 | 2,00 | 1,00 | 3,43 | 0,15 | 64,9 | 60,0 | 4,9 | 0,0 | 0,75 | 0,25 |
| 30 | 9,07 | 2,00 | 0,71 | 5,89 | 0,48 | 67,6 | 60,0 | 7,6 | 0,0 | 0,90 | 0,10 |
| 60 | 11,59 | 2,00 | 0,36 | 8,27 | 0,95 | 49,5 | 43,6 | 8,2 | 18,6 | 1,18 | 0,00 |
| 90 | 10,63 | 2,00 | 0,19 | 7,51 | 0,93 | 29,9 | 26,3 | 8,2 | 38,3 | 1,18 | 0,00 |
| 120 | 8,66 | 2,00 | 0,09 | 5,82 | 0,75 | 18,1 | 15,9 | 8,2 | 50,1 | 1,17 | 0,00 |

## 6. D frente a lactato (no se declaran inválidos)

| Caso | Patrón | corridas | de | ejemplos (D desde → hasta; lactato desde → hasta) |
|---|---|---|---|---|
| gi_bleed_57m | L1, 0–60 min: D sube mientras el lactato baja | 703 | 1054 | D 0,0→9,7, lactato 4,40→1,79; D 0,0→9,7, lactato 4,40→3,68; D 0,0→29,8, lactato 4,40→4,39 |
| gi_bleed_57m | L1, 0–120 min: D sube mientras el lactato baja | 477 | 1054 | D 0,0→38,7, lactato 4,40→1,37; D 0,0→71,2, lactato 4,40→3,51; D 20,0→70,9, lactato 4,40→4,37 |
| gi_bleed_57m | L3, 0–120 min: D baja mientras el lactato sigue a menos de 0,5 mmol/L de la llegada o por encima | 186 | 1054 | D 60,0→8,0, lactato 4,40→4,28; D 60,0→22,0, lactato 4,40→3,99; D 20,0→8,1, lactato 4,40→3,98 |
| gi_bleed_57m | L4 (contrafactual), 0–120 min: D sigue igual o por encima de la llegada mientras el lactato se mueve menos de 0,5 mmol/L | 199 | 1054 | D 60,0→81,6, lactato 4,40→4,43; D 20,0→57,2, lactato 4,40→4,23; D 60,0→121,6, lactato 4,40→4,79 |
| gi_bleed_72f | L1, 0–60 min: D sube mientras el lactato baja | 573 | 1054 | D 0,0→6,4, lactato 3,40→1,51; D 0,0→6,4, lactato 3,40→2,88; D 20,0→34,5, lactato 3,40→3,39 |
| gi_bleed_72f | L1, 0–120 min: D sube mientras el lactato baja | 396 | 1054 | D 0,0→25,7, lactato 3,40→1,19; D 0,0→25,7, lactato 3,40→2,75; D 0,0→63,4, lactato 3,40→3,40 |
| gi_bleed_72f | L3, 0–120 min: D baja mientras el lactato sigue a menos de 0,5 mmol/L de la llegada o por encima | 318 | 1054 | D 60,0→8,0, lactato 3,40→2,98; D 60,0→22,0, lactato 3,40→3,97; D 20,0→8,4, lactato 3,40→2,92 |
| gi_bleed_72f | L4 (contrafactual), 0–120 min: D sigue igual o por encima de la llegada mientras el lactato se mueve menos de 0,5 mmol/L | 270 | 1054 | D 60,0→74,0, lactato 3,40→3,28; D 20,0→50,8, lactato 3,40→2,92; D 0,0→57,0, lactato 3,40→3,55 |

## 7. Impacto de cada parámetro en las lecturas de las decisiones

ALTO ≥ 1 mmol/L (o ≥ 30 min), MEDIO ≥ 0,3 mmol/L (o ≥ 10 min), BAJO por debajo: bandas de presentación, no criterios. Cada valor por nivel es la mediana de la lectura sobre los conjuntos con ese nivel. La región no es un diseño balanceado: no contiene τ_D = 30 con la deuda de llegada alta, así que el efecto de `debt_clearance_tau_min` se mezcla en parte con el de la deuda. `debt_per_delivery_deficit` y `metabolic_demand_baseline` no varían en la región; se sondean de a uno alrededor del candidato medio.

**gi_bleed_57m · L1: cambio a los 60 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `lactate_per_output_deficit` | ALTO | la aumenta | 2: -0,79, 6: -0,23, 12: 0,64 | 1,42 | efecto principal sobre la región admisible |
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: -0,75, medio: -0,24, superior: 0,60 | 1,35 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | MEDIO | la aumenta | 45: -0,94, 120: -0,52, 240: -0,29 | 0,65 | efecto principal sobre la región admisible |
| `debt_per_delivery_deficit` | MEDIO | la aumenta | 0,5: -0,40, 1: -0,24, 2: 0,06 | 0,46 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `arrival_delivery_ratio` | MEDIO | la disminuye | inferior: -0,24, medio: -0,24, superior: -0,68 | 0,44 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: -0,23, medio: -0,52, superior: -0,59 | 0,36 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | MEDIO | no monótona | 30: -0,34, 60: -0,24, 120: -0,57 | 0,32 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: -0,37, 1: -0,24, 1,1: -0,12 | 0,25 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

**gi_bleed_57m · L3: primera caída clara (min; 121 = no en 120)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 21, medio: 49, superior: 121 | 100 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: 12, 120: 33, 240: 63 | 51 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | ALTO | la aumenta | 2: 28, 6: 45, 12: 72 | 44 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 56, medio: 39, superior: 36 | 20 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | MEDIO | no monótona | inferior: 45, medio: 49, superior: 36 | 13 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | MEDIO | sin efecto | 30: 39, 60: 50, 120: 39 | 11 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 38, 1: 41, 1,1: 45 | 7 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 41, 1: 41, 2: 42 | 1 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

**gi_bleed_57m · L3: lactato a los 120 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 2,44, medio: 3,07, superior: 3,95 | 1,51 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: 2,16, 120: 2,88, 240: 3,45 | 1,29 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 3,45, medio: 2,80, superior: 2,67 | 0,79 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | MEDIO | la aumenta | 2: 2,69, 6: 3,06, 12: 3,34 | 0,66 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | MEDIO | no monótona | 30: 2,76, 60: 3,10, 120: 3,06 | 0,34 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | BAJO | la disminuye | inferior: 3,11, medio: 3,07, superior: 2,88 | 0,23 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 2,74, 1: 2,79, 1,1: 2,86 | 0,12 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 2,78, 1: 2,79, 2: 2,81 | 0,03 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

**gi_bleed_72f · L1: cambio a los 60 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: -0,49, medio: 0,11, superior: 0,91 | 1,40 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | ALTO | la aumenta | 2: -0,48, 6: 0,10, 12: 0,86 | 1,34 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | MEDIO | no monótona | inferior: 0,03, medio: 0,11, superior: -0,46 | 0,57 | efecto principal sobre la región admisible |
| `debt_per_delivery_deficit` | MEDIO | la aumenta | 0,5: -0,02, 1: 0,11, 2: 0,38 | 0,40 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 0,08, medio: -0,25, superior: -0,32 | 0,40 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | MEDIO | no monótona | 30: -0,11, 60: 0,06, 120: -0,29 | 0,34 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: -0,02, 1: 0,11, 1,1: 0,24 | 0,25 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `lactate_clearance_tau_min` | BAJO | la aumenta | 45: -0,24, 120: -0,15, 240: -0,08 | 0,16 | efecto principal sobre la región admisible |

**gi_bleed_72f · L3: primera caída clara (min; 121 = no en 120)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: 27, 120: 66, 240: 111 | 84 | efecto principal sobre la región admisible |
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 52, medio: 90, superior: 121 | 69 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | ALTO | la aumenta | 2: 53, 6: 89, 12: 121 | 68 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | ALTO | la disminuye | inferior: 121, medio: 62, superior: 54 | 67 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | ALTO | la disminuye | inferior: 96, medio: 90, superior: 53 | 43 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | ALTO | no monótona | 30: 68, 60: 100, 120: 71 | 32 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | MEDIO | la aumenta | 0,9: 67, 1: 75, 1,1: 85 | 18 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 74, 1: 75, 2: 78 | 4 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

**gi_bleed_72f · L3: lactato a los 120 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 2,33, medio: 2,64, superior: 3,54 | 1,21 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | MEDIO | la aumenta | 45: 2,09, 120: 2,51, 240: 2,85 | 0,75 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | MEDIO | la aumenta | 2: 2,38, 6: 2,64, 12: 3,00 | 0,62 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 2,94, medio: 2,45, superior: 2,38 | 0,56 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | BAJO | no monótona | 30: 2,45, 60: 2,74, 120: 2,60 | 0,28 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | BAJO | la disminuye | inferior: 2,73, medio: 2,64, superior: 2,45 | 0,28 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 2,38, 1: 2,46, 1,1: 2,56 | 0,18 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 2,44, 1: 2,46, 2: 2,48 | 0,03 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

## 8. Lo que el modelo ofrece para cada pregunta (sólo modelo)

Sólo trayectorias producidas por el motor: L1 para FD-LAC-02/03/06 y L3 para FD-LAC-04/05. La composición contrafactual L4 no entra en ninguna.

**gi_bleed_57m** (lactato de llegada 4,4)

- Sin tratar, a los 60 min (FD-LAC-02/03): mínimo 1,79, p10 2,83, mediana 3,96, p90 6,60, máximo 14,02 (1054 corridas).
- Primera caída clara (≥ 0,5 mmol/L bajo la llegada) tras el manejo definitivo (FD-LAC-04): en 15 min: 19 %, 15–30 min: 20 %, 30–60 min: 26 %, después de 60 min: 17 %, no en 120 min: 18 %.
- A los 120 min tras el manejo definitivo (FD-LAC-05): de 1,04 a 7,65, mediana 3,04; mediana sobre la basal candidata 1,60; mediana según la deuda de llegada: inferior 2,44, medio 3,07, superior 3,95.
- Sin tratar, con la entrega bajo la demanda a los 0, 15, 30 y 60 min (FD-LAC-06): 649 corridas; en 388 el lactato baja.

**gi_bleed_72f** (lactato de llegada 3,4)

- Sin tratar, a los 60 min (FD-LAC-02/03): mínimo 1,51, p10 2,42, mediana 3,29, p90 6,09, máximo 13,63 (1054 corridas).
- Primera caída clara (≥ 0,5 mmol/L bajo la llegada) tras el manejo definitivo (FD-LAC-04): en 15 min: 11 %, 15–30 min: 14 %, 30–60 min: 18 %, después de 60 min: 24 %, no en 120 min: 34 %.
- A los 120 min tras el manejo definitivo (FD-LAC-05): de 0,98 a 8,66, mediana 2,57; mediana sobre la basal candidata 1,29; mediana según la deuda de llegada: inferior 2,33, medio 2,64, superior 3,54.
- Sin tratar, con la entrega bajo la demanda a los 0, 15, 30 y 60 min (FD-LAC-06): 649 corridas; en 285 el lactato baja.

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
