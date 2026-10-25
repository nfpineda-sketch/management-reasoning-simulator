# P2I-1 · Decisión docente: el lactato en la hemorragia digestiva (GI)

Apoyo a una decisión. El corte de P2I-1 no aprobó ningún número. La docencia respondió después FD-LAC-01 a FD-LAC-06
(§10 y §12): son restricciones clínicas de comportamiento del lactato, con estado FACULTY_APPROVED, y **no aprueban
ningún valor de parámetro oculto**. Todos los valores siguen CANDIDATE, los registros de autoridad siguen vacíos, el GI
no se migra y el golden canónico no cambia. Su aplicación a la región candidata está en
`docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md`. FC, PA, FR, volumen y colapso siguen sin abrirse.

- **Generado desde:** el congelamiento de calibración
  `152abc6cf3e2812fcade237f60db0430df78749e09f4199b0a0fff13a0dd4338` y el corte
  `7368a4b6b70a9f0f2ecdd8c665a7e8e666afc3c67ebf8639e13f3d3eed52e57a` (`python -m clinical_core.lactate_slice`).
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
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,58 | 4,20 | 4,80 | 6,92 | 23 % | 77 % | 6 % | 2 % |
| gi_bleed_57m | 30 | 1054 | 2,64 | 3,11 | 4,04 | 5,04 | 8,35 | 23 % | 77 % | 23 % | 2 % |
| gi_bleed_57m | 60 | 1054 | 1,79 | 2,68 | 3,80 | 5,36 | 9,58 | 25 % | 75 % | 38 % | 11 % |
| gi_bleed_57m | 90 | 1054 | 1,44 | 2,56 | 3,78 | 5,69 | 10,02 | 29 % | 71 % | 43 % | 13 % |
| gi_bleed_57m | 120 | 1054 | 1,37 | 2,56 | 3,91 | 6,22 | 10,42 | 35 % | 65 % | 51 % | 17 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,87 | 3,29 | 3,92 | 6,20 | 32 % | 68 % | 5 % | 2 % |
| gi_bleed_72f | 30 | 1054 | 2,13 | 2,60 | 3,21 | 4,26 | 7,83 | 32 % | 68 % | 16 % | 3 % |
| gi_bleed_72f | 60 | 1054 | 1,52 | 2,35 | 3,12 | 4,72 | 9,22 | 34 % | 66 % | 23 % | 5 % |
| gi_bleed_72f | 90 | 1054 | 1,26 | 2,20 | 3,15 | 5,12 | 9,62 | 38 % | 62 % | 34 % | 8 % |
| gi_bleed_72f | 120 | 1054 | 1,21 | 2,17 | 3,28 | 5,48 | 9,85 | 47 % | 53 % | 38 % | 12 % |

**L2 · reanimación transitoria y parcial (2 L de salina en 20 min; el sangrado sigue)**

| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0 | 1054 | 4,40 | 4,40 | 4,40 | 4,40 | 4,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,57 | 4,20 | 4,78 | 6,90 | 23 % | 77 % | 6 % | 2 % |
| gi_bleed_57m | 30 | 1054 | 2,63 | 3,07 | 4,02 | 5,00 | 8,26 | 22 % | 78 % | 23 % | 2 % |
| gi_bleed_57m | 60 | 1054 | 1,75 | 2,48 | 3,75 | 5,07 | 9,27 | 20 % | 80 % | 38 % | 12 % |
| gi_bleed_57m | 90 | 1054 | 1,36 | 2,37 | 3,62 | 5,37 | 9,53 | 23 % | 77 % | 48 % | 14 % |
| gi_bleed_57m | 120 | 1054 | 1,26 | 2,39 | 3,69 | 5,74 | 9,78 | 28 % | 72 % | 53 % | 16 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,86 | 3,28 | 3,91 | 6,20 | 32 % | 68 % | 5 % | 2 % |
| gi_bleed_72f | 30 | 1054 | 2,13 | 2,58 | 3,21 | 4,25 | 7,80 | 32 % | 68 % | 16 % | 3 % |
| gi_bleed_72f | 60 | 1054 | 1,51 | 2,27 | 3,10 | 4,70 | 9,14 | 33 % | 67 % | 23 % | 5 % |
| gi_bleed_72f | 90 | 1054 | 1,25 | 2,18 | 3,11 | 5,01 | 9,52 | 36 % | 64 % | 33 % | 8 % |
| gi_bleed_72f | 120 | 1054 | 1,19 | 2,14 | 3,25 | 5,40 | 9,73 | 44 % | 56 % | 37 % | 11 % |

**L3 · control definitivo y reanimación adecuada (2 unidades en 60 min, IBP y endoscopia)**

| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0 | 1054 | 4,40 | 4,40 | 4,40 | 4,40 | 4,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,55 | 4,20 | 4,78 | 6,89 | 23 % | 77 % | 5 % | 2 % |
| gi_bleed_57m | 30 | 1054 | 2,63 | 3,00 | 4,00 | 4,99 | 8,12 | 21 % | 79 % | 23 % | 2 % |
| gi_bleed_57m | 60 | 1054 | 1,73 | 2,23 | 3,65 | 4,81 | 8,24 | 18 % | 82 % | 43 % | 14 % |
| gi_bleed_57m | 90 | 1054 | 1,28 | 1,71 | 3,30 | 4,63 | 7,06 | 12 % | 88 % | 63 % | 20 % |
| gi_bleed_57m | 120 | 1054 | 1,04 | 1,40 | 3,00 | 4,28 | 6,00 | 9 % | 91 % | 72 % | 32 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,84 | 3,28 | 3,90 | 6,18 | 32 % | 68 % | 5 % | 2 % |
| gi_bleed_72f | 30 | 1054 | 2,12 | 2,54 | 3,18 | 4,23 | 7,66 | 32 % | 68 % | 17 % | 2 % |
| gi_bleed_72f | 60 | 1054 | 1,48 | 2,01 | 2,96 | 4,28 | 8,17 | 26 % | 74 % | 28 % | 4 % |
| gi_bleed_72f | 90 | 1054 | 1,14 | 1,69 | 2,73 | 4,16 | 7,15 | 19 % | 81 % | 39 % | 10 % |
| gi_bleed_72f | 120 | 1054 | 0,98 | 1,42 | 2,52 | 3,94 | 5,83 | 16 % | 84 % | 47 % | 11 % |

**L4 · hemostasia sin recuperar la perfusión (IBP y endoscopia sin volumen) — COMPOSICIÓN CONTRAFACTUAL MANUAL: la hemostasia se agregó a mano en el minuto de L3; el motor no la produce**

> L4 contrafactual: no es una trayectoria que el motor heredado produzca. Se muestra sólo como contraste y ninguna pregunta de la hoja de trabajo la usa.

| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0 | 1054 | 4,40 | 4,40 | 4,40 | 4,40 | 4,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,58 | 4,20 | 4,80 | 6,92 | 23 % | 77 % | 6 % | 2 % |
| gi_bleed_57m | 30 | 1054 | 2,64 | 3,11 | 4,03 | 5,04 | 8,34 | 23 % | 77 % | 23 % | 2 % |
| gi_bleed_57m | 60 | 1054 | 1,78 | 2,61 | 3,79 | 5,32 | 9,50 | 25 % | 75 % | 37 % | 11 % |
| gi_bleed_57m | 90 | 1054 | 1,40 | 2,46 | 3,68 | 5,53 | 9,77 | 26 % | 74 % | 46 % | 14 % |
| gi_bleed_57m | 120 | 1054 | 1,26 | 2,40 | 3,70 | 5,72 | 9,77 | 29 % | 71 % | 53 % | 16 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,86 | 3,28 | 3,91 | 6,20 | 32 % | 68 % | 5 % | 2 % |
| gi_bleed_72f | 30 | 1054 | 2,13 | 2,59 | 3,21 | 4,26 | 7,82 | 32 % | 68 % | 16 % | 3 % |
| gi_bleed_72f | 60 | 1054 | 1,51 | 2,28 | 3,11 | 4,71 | 9,16 | 33 % | 67 % | 23 % | 5 % |
| gi_bleed_72f | 90 | 1054 | 1,24 | 2,16 | 3,10 | 4,94 | 9,44 | 36 % | 64 % | 34 % | 7 % |
| gi_bleed_72f | 120 | 1054 | 1,14 | 2,03 | 3,12 | 5,20 | 9,37 | 38 % | 62 % | 38 % | 9 % |

## 4. Clases de comportamiento (conteos sobre la región; ninguna se declara correcta)

**gi_bleed_57m**

| Escenario y lectura | Clase | n | Dónde se concentra (mayor proporción por factor) |
|---|---|---|---|
| L1 a los 60 min | A baja | 580 | `arrival_delivery_ratio` superior (46 %); `arrival_lactate_excess` superior (40 %); `arrival_oxygen_debt` inferior (65 %); `debt_clearance_tau_min` 120 (43 %); `lactate_clearance_tau_min` 45 (42 %); `lactate_per_output_deficit` 2 (52 %) |
| L1 a los 60 min | B aproximadamente estable | 318 | `arrival_delivery_ratio` inferior (42 %); `arrival_lactate_excess` inferior (49 %); `arrival_oxygen_debt` superior (36 %); `debt_clearance_tau_min` 60 (40 %); `lactate_clearance_tau_min` 240 (58 %); `lactate_per_output_deficit` 6 (48 %) |
| L1 a los 60 min | C sube moderadamente | 120 | `arrival_delivery_ratio` inferior (45 %); `arrival_lactate_excess` inferior (42 %); `arrival_oxygen_debt` superior (78 %); `debt_clearance_tau_min` 60 (45 %); `lactate_clearance_tau_min` 120 (38 %); `lactate_per_output_deficit` 12 (80 %) |
| L1 a los 60 min | D sube sustancialmente | 36 | `arrival_delivery_ratio` inferior (58 %); `arrival_lactate_excess` inferior (50 %); `arrival_oxygen_debt` superior (92 %); `debt_clearance_tau_min` 60 (83 %); `lactate_clearance_tau_min` 45 (67 %); `lactate_per_output_deficit` 12 (100 %) |
| L1 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 580 | |
| L1 a los 120 min | A baja | 520 | `arrival_delivery_ratio` superior (45 %); `arrival_lactate_excess` superior (38 %); `arrival_oxygen_debt` inferior (56 %); `debt_clearance_tau_min` 120 (46 %); `lactate_clearance_tau_min` 120 (35 %); `lactate_per_output_deficit` 2 (66 %) |
| L1 a los 120 min | B aproximadamente estable | 264 | `arrival_delivery_ratio` inferior (38 %); `arrival_lactate_excess` inferior (38 %); `arrival_oxygen_debt` inferior (48 %); `debt_clearance_tau_min` 120 (38 %); `lactate_clearance_tau_min` 240 (50 %); `lactate_per_output_deficit` 6 (60 %) |
| L1 a los 120 min | C sube moderadamente | 177 | `arrival_delivery_ratio` inferior (46 %); `arrival_lactate_excess` inferior (41 %); `arrival_oxygen_debt` superior (46 %); `debt_clearance_tau_min` 60 (44 %); `lactate_clearance_tau_min` 120 (37 %); `lactate_per_output_deficit` 12 (78 %) |
| L1 a los 120 min | D sube sustancialmente | 93 | `arrival_delivery_ratio` inferior (58 %); `arrival_lactate_excess` inferior (48 %); `arrival_oxygen_debt` superior (65 %); `debt_clearance_tau_min` 60 (55 %); `lactate_clearance_tau_min` 45 (61 %); `lactate_per_output_deficit` 12 (100 %) |
| L1 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 520 | |
| L2 a los 60 min | A baja | 628 | `arrival_delivery_ratio` superior (45 %); `arrival_lactate_excess` superior (38 %); `arrival_oxygen_debt` inferior (64 %); `debt_clearance_tau_min` 120 (43 %); `lactate_clearance_tau_min` 45 (40 %); `lactate_per_output_deficit` 2 (49 %) |
| L2 a los 60 min | B aproximadamente estable | 294 | `arrival_delivery_ratio` inferior (42 %); `arrival_lactate_excess` inferior (45 %); `arrival_oxygen_debt` superior (40 %); `debt_clearance_tau_min` 60 (40 %); `lactate_clearance_tau_min` 240 (59 %); `lactate_per_output_deficit` 6 (45 %) |
| L2 a los 60 min | C sube moderadamente | 99 | `arrival_delivery_ratio` inferior (48 %); `arrival_lactate_excess` inferior (48 %); `arrival_oxygen_debt` superior (85 %); `debt_clearance_tau_min` 60 (48 %); `lactate_clearance_tau_min` 45 (39 %); `lactate_per_output_deficit` 12 (79 %) |
| L2 a los 60 min | D sube sustancialmente | 33 | `arrival_delivery_ratio` inferior (64 %); `arrival_lactate_excess` inferior (45 %); `arrival_oxygen_debt` superior (100 %); `debt_clearance_tau_min` 60 (91 %); `lactate_clearance_tau_min` 45 (64 %); `lactate_per_output_deficit` 12 (100 %) |
| L2 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 628 | |
| L2 a los 120 min | A baja | 616 | `arrival_delivery_ratio` superior (47 %); `arrival_lactate_excess` superior (38 %); `arrival_oxygen_debt` inferior (56 %); `debt_clearance_tau_min` 120 (43 %); `lactate_clearance_tau_min` 120 (36 %); `lactate_per_output_deficit` 2 (56 %) |
| L2 a los 120 min | B aproximadamente estable | 222 | `arrival_delivery_ratio` inferior (46 %); `arrival_lactate_excess` inferior (42 %); `arrival_oxygen_debt` inferior (39 %); `debt_clearance_tau_min` 60 (39 %); `lactate_clearance_tau_min` 240 (49 %); `lactate_per_output_deficit` 6 (58 %) |
| L2 a los 120 min | C sube moderadamente | 156 | `arrival_delivery_ratio` inferior (46 %); `arrival_lactate_excess` inferior (42 %); `arrival_oxygen_debt` superior (48 %); `debt_clearance_tau_min` 60 (40 %); `lactate_clearance_tau_min` 45 (35 %); `lactate_per_output_deficit` 12 (87 %) |
| L2 a los 120 min | D sube sustancialmente | 60 | `arrival_delivery_ratio` inferior (80 %); `arrival_lactate_excess` inferior (50 %); `arrival_oxygen_debt` superior (75 %); `debt_clearance_tau_min` 60 (60 %); `lactate_clearance_tau_min` 45 (65 %); `lactate_per_output_deficit` 12 (100 %) |
| L2 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 616 | |
| L3 en 120 min | E baja claramente en 30 min | 417 | `arrival_delivery_ratio` superior (44 %); `arrival_lactate_excess` superior (38 %); `arrival_oxygen_debt` inferior (72 %); `debt_clearance_tau_min` 120 (40 %); `lactate_clearance_tau_min` 45 (58 %); `lactate_per_output_deficit` 2 (46 %) |
| L3 en 120 min | E' baja claramente después de 30 min | 481 | `arrival_delivery_ratio` inferior (36 %); `arrival_lactate_excess` inferior (36 %); `arrival_oxygen_debt` inferior (39 %); `debt_clearance_tau_min` 60 (39 %); `lactate_clearance_tau_min` 240 (59 %); `lactate_per_output_deficit` 6 (40 %) |
| L3 en 120 min | F sigue elevado con la entrega restaurada | 156 | `arrival_delivery_ratio` inferior (48 %); `arrival_lactate_excess` inferior (46 %); `arrival_oxygen_debt` superior (94 %); `debt_clearance_tau_min` 60 (54 %); `lactate_clearance_tau_min` 240 (44 %); `lactate_per_output_deficit` 12 (75 %) |
| L4 (contrafactual) en 120 min | E baja claramente en 30 min | 402 | `arrival_delivery_ratio` superior (45 %); `arrival_lactate_excess` medio (38 %); `arrival_oxygen_debt` inferior (72 %); `debt_clearance_tau_min` 120 (42 %); `lactate_clearance_tau_min` 45 (59 %); `lactate_per_output_deficit` 2 (47 %) |
| L4 (contrafactual) en 120 min | E' baja claramente después de 30 min | 289 | `arrival_delivery_ratio` superior (46 %); `arrival_lactate_excess` superior (35 %); `arrival_oxygen_debt` inferior (46 %); `debt_clearance_tau_min` 60 (40 %); `lactate_clearance_tau_min` 240 (66 %); `lactate_per_output_deficit` 2 (55 %) |
| L4 (contrafactual) en 120 min | F' sigue elevado sin restaurar la entrega | 363 | `arrival_delivery_ratio` inferior (47 %); `arrival_lactate_excess` inferior (45 %); `arrival_oxygen_debt` superior (55 %); `debt_clearance_tau_min` 60 (44 %); `lactate_clearance_tau_min` 240 (44 %); `lactate_per_output_deficit` 12 (63 %) |

**gi_bleed_72f**

| Escenario y lectura | Clase | n | Dónde se concentra (mayor proporción por factor) |
|---|---|---|---|
| L1 a los 60 min | A baja | 351 | `arrival_delivery_ratio` superior (54 %); `arrival_lactate_excess` superior (46 %); `arrival_oxygen_debt` inferior (73 %); `debt_clearance_tau_min` 120 (44 %); `lactate_clearance_tau_min` 45 (53 %); `lactate_per_output_deficit` 2 (56 %) |
| L1 a los 60 min | B aproximadamente estable | 481 | `arrival_delivery_ratio` inferior (42 %); `arrival_lactate_excess` inferior (44 %); `arrival_oxygen_debt` inferior (45 %); `debt_clearance_tau_min` 120 (38 %); `lactate_clearance_tau_min` 240 (55 %); `lactate_per_output_deficit` 6 (41 %) |
| L1 a los 60 min | C sube moderadamente | 168 | `arrival_delivery_ratio` inferior (41 %); `arrival_lactate_excess` inferior (41 %); `arrival_oxygen_debt` superior (66 %); `debt_clearance_tau_min` 60 (45 %); `lactate_clearance_tau_min` 45 (36 %); `lactate_per_output_deficit` 12 (68 %) |
| L1 a los 60 min | D sube sustancialmente | 54 | `arrival_delivery_ratio` inferior (56 %); `arrival_lactate_excess` inferior (44 %); `arrival_oxygen_debt` superior (94 %); `debt_clearance_tau_min` 60 (72 %); `lactate_clearance_tau_min` 45 (67 %); `lactate_per_output_deficit` 12 (94 %) |
| L1 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 351 | |
| L1 a los 120 min | A baja | 369 | `arrival_delivery_ratio` superior (50 %); `arrival_lactate_excess` superior (45 %); `arrival_oxygen_debt` inferior (61 %); `debt_clearance_tau_min` 120 (49 %); `lactate_clearance_tau_min` 45 (38 %); `lactate_per_output_deficit` 2 (72 %) |
| L1 a los 120 min | B aproximadamente estable | 346 | `arrival_delivery_ratio` superior (39 %); `arrival_lactate_excess` inferior (46 %); `arrival_oxygen_debt` inferior (48 %); `debt_clearance_tau_min` 60 (40 %); `lactate_clearance_tau_min` 240 (48 %); `lactate_per_output_deficit` 6 (54 %) |
| L1 a los 120 min | C sube moderadamente | 222 | `arrival_delivery_ratio` inferior (47 %); `arrival_lactate_excess` inferior (43 %); `arrival_oxygen_debt` superior (39 %); `debt_clearance_tau_min` 60 (41 %); `lactate_clearance_tau_min` 240 (35 %); `lactate_per_output_deficit` 12 (65 %) |
| L1 a los 120 min | D sube sustancialmente | 117 | `arrival_delivery_ratio` inferior (62 %); `arrival_lactate_excess` inferior (44 %); `arrival_oxygen_debt` superior (67 %); `debt_clearance_tau_min` 60 (54 %); `lactate_clearance_tau_min` 45 (56 %); `lactate_per_output_deficit` 12 (97 %) |
| L1 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 369 | |
| L2 a los 60 min | A baja | 369 | `arrival_delivery_ratio` superior (54 %); `arrival_lactate_excess` superior (46 %); `arrival_oxygen_debt` inferior (73 %); `debt_clearance_tau_min` 120 (43 %); `lactate_clearance_tau_min` 45 (51 %); `lactate_per_output_deficit` 2 (55 %) |
| L2 a los 60 min | B aproximadamente estable | 466 | `arrival_delivery_ratio` inferior (42 %); `arrival_lactate_excess` inferior (44 %); `arrival_oxygen_debt` inferior (43 %); `debt_clearance_tau_min` 120 (39 %); `lactate_clearance_tau_min` 240 (55 %); `lactate_per_output_deficit` 6 (41 %) |
| L2 a los 60 min | C sube moderadamente | 165 | `arrival_delivery_ratio` inferior (42 %); `arrival_lactate_excess` inferior (42 %); `arrival_oxygen_debt` superior (65 %); `debt_clearance_tau_min` 60 (44 %); `lactate_clearance_tau_min` 45 (36 %); `lactate_per_output_deficit` 12 (69 %) |
| L2 a los 60 min | D sube sustancialmente | 54 | `arrival_delivery_ratio` inferior (56 %); `arrival_lactate_excess` inferior (44 %); `arrival_oxygen_debt` superior (94 %); `debt_clearance_tau_min` 60 (72 %); `lactate_clearance_tau_min` 45 (67 %); `lactate_per_output_deficit` 12 (94 %) |
| L2 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 369 | |
| L2 a los 120 min | A baja | 372 | `arrival_delivery_ratio` superior (51 %); `arrival_lactate_excess` superior (45 %); `arrival_oxygen_debt` inferior (61 %); `debt_clearance_tau_min` 120 (48 %); `lactate_clearance_tau_min` 45 (38 %); `lactate_per_output_deficit` 2 (72 %) |
| L2 a los 120 min | B aproximadamente estable | 355 | `arrival_delivery_ratio` superior (37 %); `arrival_lactate_excess` inferior (45 %); `arrival_oxygen_debt` inferior (47 %); `debt_clearance_tau_min` 60 (39 %); `lactate_clearance_tau_min` 240 (47 %); `lactate_per_output_deficit` 6 (54 %) |
| L2 a los 120 min | C sube moderadamente | 222 | `arrival_delivery_ratio` inferior (45 %); `arrival_lactate_excess` inferior (46 %); `arrival_oxygen_debt` superior (42 %); `debt_clearance_tau_min` 60 (41 %); `lactate_clearance_tau_min` 240 (35 %); `lactate_per_output_deficit` 12 (68 %) |
| L2 a los 120 min | D sube sustancialmente | 105 | `arrival_delivery_ratio` inferior (66 %); `arrival_lactate_excess` inferior (43 %); `arrival_oxygen_debt` superior (66 %); `debt_clearance_tau_min` 60 (57 %); `lactate_clearance_tau_min` 45 (60 %); `lactate_per_output_deficit` 12 (97 %) |
| L2 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 372 | |
| L3 en 120 min | E baja claramente en 30 min | 261 | `arrival_delivery_ratio` superior (55 %); `arrival_lactate_excess` superior (45 %); `arrival_oxygen_debt` inferior (83 %); `debt_clearance_tau_min` 120 (41 %); `lactate_clearance_tau_min` 45 (71 %); `lactate_per_output_deficit` 2 (48 %) |
| L3 en 120 min | E' baja claramente después de 30 min | 484 | `arrival_delivery_ratio` inferior (37 %); `arrival_lactate_excess` medio (37 %); `arrival_oxygen_debt` inferior (50 %); `debt_clearance_tau_min` 60 (37 %); `lactate_clearance_tau_min` 240 (42 %); `lactate_per_output_deficit` 2 (40 %) |
| L3 en 120 min | F sigue elevado con la entrega restaurada | 309 | `arrival_delivery_ratio` inferior (45 %); `arrival_lactate_excess` inferior (56 %); `arrival_oxygen_debt` superior (69 %); `debt_clearance_tau_min` 60 (47 %); `lactate_clearance_tau_min` 240 (48 %); `lactate_per_output_deficit` 12 (53 %) |
| L4 (contrafactual) en 120 min | E baja claramente en 30 min | 252 | `arrival_delivery_ratio` superior (56 %); `arrival_lactate_excess` superior (45 %); `arrival_oxygen_debt` inferior (82 %); `debt_clearance_tau_min` 120 (43 %); `lactate_clearance_tau_min` 45 (73 %); `lactate_per_output_deficit` 2 (49 %) |
| L4 (contrafactual) en 120 min | E' baja claramente después de 30 min | 228 | `arrival_delivery_ratio` superior (46 %); `arrival_lactate_excess` medio (43 %); `arrival_oxygen_debt` inferior (49 %); `debt_clearance_tau_min` 120 (42 %); `lactate_clearance_tau_min` 240 (49 %); `lactate_per_output_deficit` 2 (68 %) |
| L4 (contrafactual) en 120 min | F' sigue elevado sin restaurar la entrega | 574 | `arrival_delivery_ratio` inferior (45 %); `arrival_lactate_excess` inferior (48 %); `arrival_oxygen_debt` superior (43 %); `debt_clearance_tau_min` 60 (41 %); `lactate_clearance_tau_min` 240 (42 %); `lactate_per_output_deficit` 12 (49 %) |

## 5. Descomposición del mecanismo (exacta dada la trayectoria del déficit)

Exceso de lactato = lo que queda del exceso de llegada + lo que produce la D de llegada + lo producido por el déficit posterior. Suma exacta para las recurrencias del modelo; no es una atribución causal entre parámetros.

**gi_bleed_57m · bajo · L1** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 3,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 2, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 0,80 | 3,60 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,00 | 0,00 |
| 15 | 3,37 | 0,80 | 2,57 | 0,00 | 0,00 | 0,7 | 0,0 | 0,7 | 0,0 | 0,90 | 0,10 |
| 30 | 2,64 | 0,80 | 1,83 | 0,00 | 0,01 | 2,8 | 0,0 | 3,0 | 0,2 | 0,79 | 0,21 |
| 60 | 1,79 | 0,80 | 0,93 | 0,00 | 0,06 | 10,5 | 0,0 | 12,3 | 1,8 | 0,58 | 0,42 |
| 90 | 1,44 | 0,80 | 0,48 | 0,00 | 0,16 | 22,1 | 0,0 | 27,8 | 5,7 | 0,37 | 0,63 |
| 120 | 1,37 | 0,80 | 0,24 | 0,00 | 0,33 | 36,7 | 0,0 | 49,7 | 13,0 | 0,16 | 0,84 |

**gi_bleed_57m · bajo · L3** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 3,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 2, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 0,80 | 3,60 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,00 | 0,00 |
| 15 | 3,37 | 0,80 | 2,57 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,31 | 0,00 |
| 30 | 2,63 | 0,80 | 1,83 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,60 | 0,00 |
| 60 | 1,73 | 0,80 | 0,93 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 2,16 | 0,00 |
| 90 | 1,28 | 0,80 | 0,48 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 2,14 | 0,00 |
| 120 | 1,04 | 0,80 | 0,24 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 2,12 | 0,00 |

**gi_bleed_57m · medio · L1** — `arrival_oxygen_debt` 20, `arrival_lactate_excess` 3,40, `arrival_delivery_ratio` 0,85, τ_D 60, g 1,0, G 6, τ_L 120, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 1,00 | 3,40 | 0,00 | 0,00 | 20,0 | 20,0 | 0,0 | 0,0 | 0,85 | 0,15 |
| 15 | 4,22 | 1,00 | 3,00 | 0,21 | 0,01 | 18,1 | 15,5 | 2,9 | 4,7 | 0,76 | 0,24 |
| 30 | 4,05 | 1,00 | 2,65 | 0,35 | 0,06 | 17,8 | 12,1 | 7,1 | 9,2 | 0,67 | 0,33 |
| 60 | 3,80 | 1,00 | 2,06 | 0,48 | 0,26 | 20,8 | 7,3 | 19,4 | 18,7 | 0,50 | 0,50 |
| 90 | 3,70 | 1,00 | 1,60 | 0,50 | 0,60 | 26,8 | 4,4 | 37,2 | 30,4 | 0,32 | 0,68 |
| 120 | 3,78 | 1,00 | 1,25 | 0,47 | 1,07 | 34,6 | 2,7 | 60,2 | 45,6 | 0,14 | 0,86 |

**gi_bleed_57m · medio · L3** — `arrival_oxygen_debt` 20, `arrival_lactate_excess` 3,40, `arrival_delivery_ratio` 0,85, τ_D 60, g 1,0, G 6, τ_L 120, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 1,00 | 3,40 | 0,00 | 0,00 | 20,0 | 20,0 | 0,0 | 0,0 | 0,85 | 0,15 |
| 15 | 4,21 | 1,00 | 3,00 | 0,21 | 0,01 | 16,1 | 15,5 | 0,7 | 4,6 | 1,11 | 0,00 |
| 30 | 4,00 | 1,00 | 2,65 | 0,35 | 0,01 | 12,5 | 12,1 | 0,7 | 8,2 | 1,36 | 0,00 |
| 60 | 3,56 | 1,00 | 2,06 | 0,48 | 0,02 | 7,6 | 7,3 | 0,7 | 13,1 | 1,84 | 0,00 |
| 90 | 3,12 | 1,00 | 1,60 | 0,50 | 0,02 | 4,6 | 4,4 | 0,7 | 16,1 | 1,82 | 0,00 |
| 120 | 2,73 | 1,00 | 1,25 | 0,47 | 0,02 | 2,8 | 2,7 | 0,7 | 18,0 | 1,81 | 0,00 |

**gi_bleed_57m · alto · L1** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 2,00 | 2,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 6,92 | 2,00 | 1,71 | 3,04 | 0,17 | 52,4 | 46,6 | 6,4 | 14,1 | 0,54 | 0,46 |
| 30 | 8,35 | 2,00 | 1,22 | 4,53 | 0,60 | 47,3 | 36,2 | 13,8 | 26,5 | 0,48 | 0,52 |
| 60 | 9,58 | 2,00 | 0,62 | 5,05 | 1,91 | 42,6 | 21,9 | 31,4 | 48,8 | 0,35 | 0,65 |
| 90 | 10,02 | 2,00 | 0,32 | 4,22 | 3,48 | 42,8 | 13,2 | 52,7 | 70,0 | 0,22 | 0,78 |
| 120 | 10,42 | 2,00 | 0,16 | 3,15 | 5,11 | 45,8 | 8,0 | 77,8 | 92,0 | 0,10 | 0,90 |

**gi_bleed_57m · alto · L3** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 2,00 | 2,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 6,89 | 2,00 | 1,71 | 3,04 | 0,14 | 50,8 | 46,6 | 4,7 | 13,9 | 0,78 | 0,22 |
| 30 | 8,12 | 2,00 | 1,22 | 4,53 | 0,37 | 41,2 | 36,2 | 6,7 | 25,5 | 0,96 | 0,04 |
| 60 | 8,24 | 2,00 | 0,62 | 5,05 | 0,57 | 24,9 | 21,9 | 6,8 | 41,8 | 1,30 | 0,00 |
| 90 | 7,06 | 2,00 | 0,32 | 4,22 | 0,52 | 15,0 | 13,2 | 6,8 | 51,7 | 1,29 | 0,00 |
| 120 | 5,71 | 2,00 | 0,16 | 3,15 | 0,40 | 9,1 | 8,0 | 6,8 | 57,7 | 1,27 | 0,00 |

**gi_bleed_72f · bajo · L1** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 2,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 2, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 0,80 | 2,60 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,00 | 0,00 |
| 15 | 2,66 | 0,80 | 1,86 | 0,00 | 0,00 | 0,5 | 0,0 | 0,5 | 0,0 | 0,92 | 0,08 |
| 30 | 2,13 | 0,80 | 1,32 | 0,00 | 0,01 | 2,0 | 0,0 | 2,2 | 0,2 | 0,85 | 0,15 |
| 60 | 1,52 | 0,80 | 0,68 | 0,00 | 0,04 | 7,7 | 0,0 | 9,0 | 1,3 | 0,69 | 0,31 |
| 90 | 1,26 | 0,80 | 0,34 | 0,00 | 0,12 | 16,2 | 0,0 | 20,4 | 4,2 | 0,54 | 0,46 |
| 120 | 1,21 | 0,80 | 0,18 | 0,00 | 0,24 | 26,8 | 0,0 | 36,3 | 9,5 | 0,39 | 0,61 |

**gi_bleed_72f · bajo · L3** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 2,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 2, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 0,80 | 2,60 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,00 | 0,00 |
| 15 | 2,66 | 0,80 | 1,86 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,22 | 0,00 |
| 30 | 2,12 | 0,80 | 1,32 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,44 | 0,00 |
| 60 | 1,48 | 0,80 | 0,68 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,84 | 0,00 |
| 90 | 1,14 | 0,80 | 0,34 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,83 | 0,00 |
| 120 | 0,98 | 0,80 | 0,18 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,81 | 0,00 |

**gi_bleed_72f · medio · L1** — `arrival_oxygen_debt` 20, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,85, τ_D 60, g 1,0, G 6, τ_L 120, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 1,00 | 2,40 | 0,00 | 0,00 | 20,0 | 20,0 | 0,0 | 0,0 | 0,85 | 0,15 |
| 15 | 3,34 | 1,00 | 2,12 | 0,21 | 0,01 | 18,0 | 15,5 | 2,7 | 4,7 | 0,79 | 0,21 |
| 30 | 3,27 | 1,00 | 1,87 | 0,35 | 0,06 | 17,3 | 12,1 | 6,4 | 9,1 | 0,72 | 0,28 |
| 60 | 3,16 | 1,00 | 1,45 | 0,48 | 0,23 | 18,7 | 7,3 | 16,6 | 18,0 | 0,59 | 0,41 |
| 90 | 3,14 | 1,00 | 1,13 | 0,50 | 0,50 | 22,6 | 4,4 | 30,8 | 28,2 | 0,46 | 0,54 |
| 120 | 3,22 | 1,00 | 0,88 | 0,47 | 0,88 | 28,1 | 2,7 | 48,8 | 40,8 | 0,33 | 0,67 |

**gi_bleed_72f · medio · L3** — `arrival_oxygen_debt` 20, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,85, τ_D 60, g 1,0, G 6, τ_L 120, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 1,00 | 2,40 | 0,00 | 0,00 | 20,0 | 20,0 | 0,0 | 0,0 | 0,85 | 0,15 |
| 15 | 3,33 | 1,00 | 2,12 | 0,21 | 0,01 | 16,4 | 15,5 | 1,0 | 4,6 | 1,04 | 0,00 |
| 30 | 3,23 | 1,00 | 1,87 | 0,35 | 0,01 | 12,7 | 12,1 | 1,0 | 8,3 | 1,22 | 0,00 |
| 60 | 2,96 | 1,00 | 1,45 | 0,48 | 0,02 | 7,7 | 7,3 | 1,0 | 13,3 | 1,57 | 0,00 |
| 90 | 2,66 | 1,00 | 1,13 | 0,50 | 0,02 | 4,6 | 4,4 | 1,0 | 16,3 | 1,55 | 0,00 |
| 120 | 2,37 | 1,00 | 0,88 | 0,47 | 0,02 | 2,8 | 2,7 | 1,0 | 18,2 | 1,54 | 0,00 |

**gi_bleed_72f · alto · L1** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 1,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 2,00 | 1,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 6,20 | 2,00 | 1,00 | 3,04 | 0,16 | 52,3 | 46,6 | 6,3 | 14,0 | 0,55 | 0,45 |
| 30 | 7,83 | 2,00 | 0,71 | 4,53 | 0,58 | 46,9 | 36,2 | 13,3 | 26,4 | 0,51 | 0,49 |
| 60 | 9,22 | 2,00 | 0,36 | 5,05 | 1,81 | 41,1 | 21,9 | 29,4 | 48,3 | 0,42 | 0,58 |
| 90 | 9,62 | 2,00 | 0,19 | 4,22 | 3,21 | 39,8 | 13,2 | 48,2 | 68,4 | 0,33 | 0,67 |
| 120 | 9,85 | 2,00 | 0,09 | 3,15 | 4,60 | 41,2 | 8,0 | 69,8 | 88,5 | 0,23 | 0,77 |

**gi_bleed_72f · alto · L3** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 1,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 2,00 | 1,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 6,18 | 2,00 | 1,00 | 3,04 | 0,14 | 51,1 | 46,6 | 5,1 | 14,0 | 0,73 | 0,27 |
| 30 | 7,66 | 2,00 | 0,71 | 4,53 | 0,42 | 42,4 | 36,2 | 8,2 | 25,7 | 0,86 | 0,14 |
| 60 | 8,17 | 2,00 | 0,36 | 5,05 | 0,76 | 26,5 | 21,9 | 9,4 | 42,9 | 1,11 | 0,00 |
| 90 | 7,15 | 2,00 | 0,19 | 4,22 | 0,74 | 16,0 | 13,2 | 9,4 | 53,4 | 1,10 | 0,00 |
| 120 | 5,83 | 2,00 | 0,09 | 3,15 | 0,58 | 9,7 | 8,0 | 9,4 | 59,7 | 1,09 | 0,00 |

## 6. D frente a lactato (no se declaran inválidos)

| Caso | Patrón | corridas | de | ejemplos (D desde → hasta; lactato desde → hasta) |
|---|---|---|---|---|
| gi_bleed_57m | L1, 0–60 min: D sube mientras el lactato baja | 642 | 1054 | D 0,0→10,5, lactato 4,40→1,79; D 0,0→10,5, lactato 4,40→3,62; D 0,0→14,7, lactato 4,40→4,39 |
| gi_bleed_57m | L1, 0–120 min: D sube mientras el lactato baja | 577 | 1054 | D 0,0→36,7, lactato 4,40→1,37; D 20,0→20,8, lactato 4,40→3,38; D 0,0→28,4, lactato 4,40→4,39 |
| gi_bleed_57m | L3, 0–120 min: D baja mientras el lactato sigue a menos de 0,5 mmol/L de la llegada o por encima | 156 | 1054 | D 60,0→8,0, lactato 4,40→4,28; D 60,0→9,1, lactato 4,40→5,09; D 20,0→7,6, lactato 4,40→3,95 |
| gi_bleed_57m | L4 (contrafactual), 0–120 min: D sigue igual o por encima de la llegada mientras el lactato se mueve menos de 0,5 mmol/L | 159 | 1054 | D 20,0→24,2, lactato 4,40→4,17; D 20,0→37,2, lactato 4,40→4,69; D 0,0→43,4, lactato 4,40→3,96 |
| gi_bleed_72f | L1, 0–60 min: D sube mientras el lactato baja | 507 | 1054 | D 0,0→7,7, lactato 3,40→1,52; D 0,0→7,7, lactato 3,40→2,88; D 0,0→23,6, lactato 3,40→3,36 |
| gi_bleed_72f | L1, 0–120 min: D sube mientras el lactato baja | 442 | 1054 | D 0,0→26,8, lactato 3,40→1,21; D 0,0→26,8, lactato 3,40→2,66; D 0,0→13,8, lactato 3,40→3,38 |
| gi_bleed_72f | L3, 0–120 min: D baja mientras el lactato sigue a menos de 0,5 mmol/L de la llegada o por encima | 282 | 1054 | D 60,0→8,0, lactato 3,40→2,98; D 60,0→22,0, lactato 3,40→4,73; D 20,0→7,7, lactato 3,40→2,96 |
| gi_bleed_72f | L4 (contrafactual), 0–120 min: D sigue igual o por encima de la llegada mientras el lactato se mueve menos de 0,5 mmol/L | 258 | 1054 | D 20,0→20,5, lactato 3,40→2,90; D 20,0→32,2, lactato 3,40→3,57; D 0,0→40,0, lactato 3,40→3,29 |

## 7. Impacto de cada parámetro en las lecturas de las decisiones

ALTO ≥ 1 mmol/L (o ≥ 30 min), MEDIO ≥ 0,3 mmol/L (o ≥ 10 min), BAJO por debajo: bandas de presentación, no criterios. Cada valor por nivel es la mediana de la lectura sobre los conjuntos con ese nivel. La región no es un diseño balanceado: no contiene τ_D = 30 con la deuda de llegada alta, así que el efecto de `debt_clearance_tau_min` se mezcla en parte con el de la deuda. `debt_per_delivery_deficit` y `metabolic_demand_baseline` no varían en la región; se sondean de a uno alrededor del candidato medio.

**gi_bleed_57m · L1: cambio a los 60 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `lactate_per_output_deficit` | ALTO | la aumenta | 2: -0,95, 6: -0,49, 12: 0,07 | 1,02 | efecto principal sobre la región admisible |
| `arrival_oxygen_debt` | MEDIO | la aumenta | inferior: -0,81, medio: -0,49, superior: 0,16 | 0,97 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | MEDIO | la aumenta | 45: -1,27, 120: -0,70, 240: -0,39 | 0,87 | efecto principal sobre la región admisible |
| `debt_per_delivery_deficit` | MEDIO | la aumenta | 0,5: -0,73, 1: -0,60, 2: -0,34 | 0,39 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: -0,38, medio: -0,67, superior: -0,72 | 0,33 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | BAJO | la disminuye | inferior: -0,47, medio: -0,49, superior: -0,73 | 0,26 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | BAJO | no monótona | 30: -0,60, 60: -0,46, 120: -0,67 | 0,21 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: -0,70, 1: -0,60, 1,1: -0,51 | 0,19 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

**gi_bleed_57m · L3: primera caída clara (min; 121 = no en 120)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 21, medio: 46, superior: 107 | 86 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: 11, 120: 31, 240: 59 | 48 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | ALTO | la aumenta | 2: 28, 6: 41, 12: 60 | 32 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 56, medio: 39, superior: 36 | 20 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | MEDIO | no monótona | 30: 32, 60: 44, 120: 39 | 12 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | MEDIO | no monótona | inferior: 40, medio: 46, superior: 36 | 10 | efecto principal sobre la región admisible |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 37, 1: 38, 2: 39 | 2 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 37, 1: 38, 1,1: 39 | 2 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

**gi_bleed_57m · L3: lactato a los 120 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: 2,06, 120: 2,88, 240: 3,45 | 1,39 | efecto principal sobre la región admisible |
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 2,41, medio: 3,04, superior: 3,78 | 1,37 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 3,40, medio: 2,73, superior: 2,60 | 0,80 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | MEDIO | la aumenta | 2: 2,64, 6: 3,00, 12: 3,22 | 0,58 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | MEDIO | no monótona | 30: 2,60, 60: 3,06, 120: 3,01 | 0,46 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | BAJO | la disminuye | inferior: 3,05, medio: 3,04, superior: 2,88 | 0,17 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 2,71, 1: 2,73, 1,1: 2,76 | 0,04 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 2,72, 1: 2,73, 2: 2,75 | 0,03 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

**gi_bleed_72f · L1: cambio a los 60 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: -0,52, medio: -0,14, superior: 0,52 | 1,03 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | MEDIO | la aumenta | 2: -0,55, 6: -0,18, 12: 0,39 | 0,94 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | MEDIO | la aumenta | 45: -0,58, 120: -0,32, 240: -0,18 | 0,40 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: -0,09, medio: -0,40, superior: -0,45 | 0,36 | efecto principal sobre la región admisible |
| `debt_per_delivery_deficit` | MEDIO | la aumenta | 0,5: -0,35, 1: -0,24, 2: -0,01 | 0,34 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `arrival_delivery_ratio` | MEDIO | no monótona | inferior: -0,16, medio: -0,14, superior: -0,47 | 0,33 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: -0,33, 1: -0,24, 1,1: -0,15 | 0,19 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_clearance_tau_min` | BAJO | no monótona | 30: -0,29, 60: -0,18, 120: -0,33 | 0,16 | efecto principal sobre la región admisible |

**gi_bleed_72f · L3: primera caída clara (min; 121 = no en 120)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: 24, 120: 62, 240: 106 | 82 | efecto principal sobre la región admisible |
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 40, medio: 79, superior: 121 | 81 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | ALTO | la disminuye | inferior: 120, medio: 56, superior: 52 | 68 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | ALTO | la aumenta | 2: 52, 6: 77, 12: 109 | 57 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | ALTO | no monótona | 30: 56, 60: 89, 120: 69 | 33 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | MEDIO | no monótona | inferior: 76, medio: 79, superior: 53 | 26 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 64, 1: 66, 1,1: 70 | 6 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 65, 1: 66, 2: 68 | 3 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

**gi_bleed_72f · L3: lactato a los 120 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 2,22, medio: 2,57, superior: 3,32 | 1,10 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | MEDIO | la aumenta | 45: 2,01, 120: 2,51, 240: 2,85 | 0,84 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 2,90, medio: 2,42, superior: 2,30 | 0,60 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | MEDIO | la aumenta | 2: 2,31, 6: 2,60, 12: 2,85 | 0,55 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | BAJO | no monótona | 30: 2,38, 60: 2,67, 120: 2,58 | 0,30 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | BAJO | la disminuye | inferior: 2,62, medio: 2,57, superior: 2,45 | 0,17 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 2,35, 1: 2,37, 1,1: 2,41 | 0,06 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 2,36, 1: 2,37, 2: 2,39 | 0,03 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

## 8. Lo que el modelo ofrece para cada pregunta (sólo modelo)

Sólo trayectorias producidas por el motor: L1 para FD-LAC-02/03/06 y L3 para FD-LAC-04/05. La composición contrafactual L4 no entra en ninguna.

**gi_bleed_57m** (lactato de llegada 4,4)

- Sin tratar, a los 60 min (FD-LAC-02/03): mínimo 1,79, p10 2,68, mediana 3,80, p90 5,36, máximo 9,58 (1054 corridas).
- Primera caída clara (≥ 0,5 mmol/L bajo la llegada) tras el manejo definitivo (FD-LAC-04): en 15 min: 20 %, 15–30 min: 20 %, 30–60 min: 28 %, después de 60 min: 17 %, no en 120 min: 15 %.
- A los 120 min tras el manejo definitivo (FD-LAC-05): de 1,04 a 6,00, mediana 3,00; mediana sobre la basal candidata 1,57; mediana según la deuda de llegada: inferior 2,41, medio 3,04, superior 3,78.
- Sin tratar, con la entrega bajo la demanda a los 0, 15, 30 y 60 min (FD-LAC-06): 649 corridas; en 472 el lactato baja.

**gi_bleed_72f** (lactato de llegada 3,4)

- Sin tratar, a los 60 min (FD-LAC-02/03): mínimo 1,52, p10 2,35, mediana 3,12, p90 4,72, máximo 9,22 (1054 corridas).
- Primera caída clara (≥ 0,5 mmol/L bajo la llegada) tras el manejo definitivo (FD-LAC-04): en 15 min: 11 %, 15–30 min: 14 %, 30–60 min: 20 %, después de 60 min: 25 %, no en 120 min: 29 %.
- A los 120 min tras el manejo definitivo (FD-LAC-05): de 0,98 a 5,83, mediana 2,52; mediana sobre la basal candidata 1,18; mediana según la deuda de llegada: inferior 2,22, medio 2,57, superior 3,32.
- Sin tratar, con la entrega bajo la demanda a los 0, 15, 30 y 60 min (FD-LAC-06): 649 corridas; en 391 el lactato baja.

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

La docencia respondió el 2026-10-25 (versión «FD-LAC v1»). La selección resume la opción elegida; el texto que rige
está en §12, tal como lo escribió la docencia. Las opciones del modelo para cada pregunta están en §8.

| ID | Pregunta | Opciones | Selección docente | Estado |
|---|---|---|---|---|
| FD-LAC-01 | En la hemorragia sin tratar con perfusión que empeora, el lactato debe… | A. poder bajar desde la llegada / B. mantenerse aproximadamente estable / C. subir en general / D. exigir una subida mínima en 60 min | C. subir en general; una estabilidad breve es aceptable | FACULTY_APPROVED |
| FD-LAC-02 | 57m: ¿qué rango de lactato a los 60 min sin tratar es clínicamente aceptable? | el rango que ofrece el modelo para 57m (§8) u otro que la docencia fije | 4,4–7,0 mmol/L a los 60 min: envolvente clínica, no un objetivo | FACULTY_APPROVED |
| FD-LAC-03 | 72f: ¿qué rango de lactato a los 60 min sin tratar es clínicamente aceptable? | el rango que ofrece el modelo para 72f (§8) u otro que la docencia fije | 3,4–5,5 mmol/L a los 60 min: envolvente clínica, no un objetivo | FACULTY_APPROVED |
| FD-LAC-04 | Tras la hemostasia exitosa y la reanimación adecuada, ¿cuándo debe verse por primera vez una tendencia clara a la baja? | en 15 min / 15–30 min / 30–60 min / después de 60 min | 15–30 min: inicio de una tendencia clara a la baja | FACULTY_APPROVED |
| FD-LAC-05 | A los 120 min del manejo exitoso, el lactato debe… | seguir sustancialmente elevado / seguir levemente elevado / estar cerca de la basal de llegada / depender mucho de la deuda acumulada inicial | depender de la deuda acumulada; puede seguir levemente elevado; sin normalización obligatoria | FACULTY_APPROVED |
| FD-LAC-06 | ¿Puede la hemorragia activa con perfusión que sigue empeorando mostrar un lactato en descenso sólo porque se aclara el lactato aclarable de llegada? | SÍ / NO / SÓLO SI LA ENTREGA ES ADECUADA | SÓLO SI LA ENTREGA ES ADECUADA | FACULTY_APPROVED |

## 11. Lo que este corte no hace

- No aprueba valores. En el registro de calibración FACULTY_APPROVED sigue en 0: las decisiones FD-LAC aprueban
  comportamiento, no parámetros. Los registros de autoridad siguen vacíos y la puerta de migración sigue fallando para
  57m y 72f.
- No elige candidatos por su parecido con el motor de familias.
- No cambia la fisiología, las bandas, las reglas congeladas, los escenarios del golden ni el golden.
- No abre FC, PA, FR, volumen ni colapso.

<!-- generado:decisiones-lactato -->
## 12. Registro de decisiones docentes (P2I-2)

Respondidas por la docencia y registradas el 2026-10-25, versión «FD-LAC v1», en `clinical_core/faculty_constraints.py`. Son restricciones clínicas de comportamiento del lactato observable, con estado FACULTY_APPROVED. **No aprueban ningún valor de parámetro oculto:** `arrival_oxygen_debt`, `arrival_lactate_excess`, `debt_clearance_tau_min`, `debt_per_delivery_deficit`, `lactate_per_output_deficit`, `lactate_clearance_tau_min`, `arrival_delivery_ratio`, `metabolic_demand_baseline` siguen CANDIDATE, y nada de esto entra en los registros de autoridad de migración. El texto que rige es el original, en inglés. La docencia no dio un fundamento aparte: la columna «Frase clave» cita la frase de su propio texto que lo expresa. Su aplicación a la región candidata está en `docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md`.

| ID | Estado | Fecha · versión | Observable | Escenarios · casos | Decisión (texto original) | Frase clave del texto docente | Valores de parámetros que aprueba |
|---|---|---|---|---|---|---|---|
| FD-LAC-01 | FACULTY_APPROVED | 2026-10-25 · FD-LAC v1 | trayectoria del lactato con sangrado activo y entrega de O2 inadecuada | L1 · 57m, 72f | «With ongoing active haemorrhage and persistently inadequate/worsening oxygen delivery, lactate should GENERALLY RISE. A brief period of stability is acceptable. A sustained fall should NOT be the typical trajectory when oxygen delivery remains inadequate. Do NOT interpret this as: "lactate must rise every minute." The clinically important requirement is the trajectory over meaningful reassessment intervals.» | «The clinically important requirement is the trajectory over meaningful reassessment intervals.» | ninguno |
| FD-LAC-02 | FACULTY_APPROVED | 2026-10-25 · FD-LAC v1 | lactato (mmol/L) a los 60 min sin tratar | L1 · 57m | «APPROVED clinical band: arrival lactate: 4.4 mmol/L. 60-min untreated acceptable band: 4.4-7.0 mmol/L. Preferred direction: stable-to-rising, usually rising. Do NOT convert the midpoint of this band into a target. Values are a clinical acceptance envelope.» | «Values are a clinical acceptance envelope.» | ninguno |
| FD-LAC-03 | FACULTY_APPROVED | 2026-10-25 · FD-LAC v1 | lactato (mmol/L) a los 60 min sin tratar | L1 · 72f | «APPROVED clinical band: arrival lactate: 3.4 mmol/L. 60-min untreated acceptable band: 3.4-5.5 mmol/L. Preferred direction: stable-to-rising, usually rising. Again, this is a clinical envelope, not a point target.» | «Again, this is a clinical envelope, not a point target.» | ninguno |
| FD-LAC-04 | FACULTY_APPROVED | 2026-10-25 · FD-LAC v1 | inicio de una tendencia clara a la baja tras la hemostasia y la restauración sostenida de la entrega | L3 · 57m, 72f | «After successful haemostasis AND adequate sustained restoration of oxygen delivery, a CLEAR downward lactate trend should begin within: 15-30 minutes. This means onset of a meaningful downward trend. It does NOT mean: normalization by 30 minutes; arbitrary fixed mmol/L decline; clearance independent of accumulated debt.» | «This means onset of a meaningful downward trend.» | ninguno |
| FD-LAC-05 | FACULTY_APPROVED | 2026-10-25 · FD-LAC v1 | lactato residual a los 120 min del manejo definitivo y su dependencia de la deuda de O2 acumulada | L3 · 57m, 72f | «Residual lactate at 120 min should depend materially on accumulated oxygen debt. Typical severe-shock trajectories may remain MILDLY ELEVATED. Do NOT require full normalization within 120 minutes. Do NOT encode one fixed 120-min lactate target. The model should preserve memory of prior debt.» | «The model should preserve memory of prior debt.» | ninguno |
| FD-LAC-06 | FACULTY_APPROVED | 2026-10-25 · FD-LAC v1 | trayectoria del lactato con sangrado activo, según la adecuación de la entrega | L1, L2, L3 · 57m, 72f | «ONLY IF OXYGEN DELIVERY IS ADEQUATE. Active haemorrhage by itself does not require lactate to rise. If resuscitation maintains/restores adequate oxygen delivery despite ongoing bleeding, lactate may fall. However: active bleeding + persistent/worsening inadequate oxygen delivery must NOT produce a sustained declining lactate trajectory. This rule takes precedence over diagnosis labels.» | «This rule takes precedence over diagnosis labels.» | ninguno |

<!-- /generado:decisiones-lactato -->
