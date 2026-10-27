# P2I-1 · Decisión docente: el lactato en la hemorragia digestiva (GI)

Apoyo a una decisión. El corte de P2I-1 no aprobó ningún número. La docencia respondió después FD-LAC-01 a FD-LAC-06
(§10 y §12): son restricciones clínicas de comportamiento del lactato, con estado FACULTY_APPROVED, y **no aprueban
ningún valor de parámetro oculto**. Todos los valores siguen CANDIDATE, los registros de autoridad siguen vacíos, el GI
no se migra y el golden canónico no cambia. Su aplicación a la región candidata está en
`docs/revision/P2I2_RESTRICCIONES_LACTATO_GI.md`. FC, PA, FR, volumen y colapso siguen sin abrirse.

- **Generado desde:** el congelamiento de calibración
  `eee140134e96590d4dfa0a31573aeef53933f41064fff58054ed5905ddf52494` y el corte
  `2ee5127c171f4926b6460a30f4447529c97fd4439b1a76b8b251d52f590abcd9` (`python -m clinical_core.lactate_slice`).
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
| gi_bleed_57m | 30 | 1054 | 2,64 | 3,11 | 4,03 | 5,04 | 8,34 | 23 % | 77 % | 23 % | 2 % |
| gi_bleed_57m | 60 | 1054 | 1,78 | 2,61 | 3,79 | 5,32 | 9,50 | 25 % | 75 % | 37 % | 11 % |
| gi_bleed_57m | 90 | 1054 | 1,41 | 2,47 | 3,70 | 5,55 | 9,81 | 26 % | 74 % | 45 % | 14 % |
| gi_bleed_57m | 120 | 1054 | 1,30 | 2,46 | 3,77 | 5,90 | 10,01 | 30 % | 70 % | 51 % | 16 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,86 | 3,28 | 3,91 | 6,20 | 32 % | 68 % | 5 % | 2 % |
| gi_bleed_72f | 30 | 1054 | 2,13 | 2,59 | 3,21 | 4,25 | 7,82 | 32 % | 68 % | 16 % | 3 % |
| gi_bleed_72f | 60 | 1054 | 1,51 | 2,27 | 3,10 | 4,70 | 9,14 | 33 % | 67 % | 23 % | 5 % |
| gi_bleed_72f | 90 | 1054 | 1,23 | 2,15 | 3,08 | 4,93 | 9,41 | 35 % | 65 % | 33 % | 7 % |
| gi_bleed_72f | 120 | 1054 | 1,14 | 2,06 | 3,14 | 5,22 | 9,44 | 40 % | 60 % | 38 % | 10 % |

**L2 · reanimación transitoria y parcial (2 L de salina en 20 min; el sangrado sigue)**

| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0 | 1054 | 4,40 | 4,40 | 4,40 | 4,40 | 4,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,56 | 4,20 | 4,78 | 6,89 | 23 % | 77 % | 6 % | 2 % |
| gi_bleed_57m | 30 | 1054 | 2,63 | 3,05 | 4,01 | 5,00 | 8,18 | 21 % | 79 % | 23 % | 2 % |
| gi_bleed_57m | 60 | 1054 | 1,74 | 2,41 | 3,68 | 4,90 | 8,90 | 19 % | 81 % | 40 % | 13 % |
| gi_bleed_57m | 90 | 1054 | 1,29 | 2,05 | 3,47 | 4,81 | 8,82 | 18 % | 82 % | 53 % | 15 % |
| gi_bleed_57m | 120 | 1054 | 1,12 | 2,14 | 3,35 | 5,08 | 8,75 | 20 % | 80 % | 58 % | 19 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,85 | 3,28 | 3,90 | 6,19 | 32 % | 68 % | 5 % | 2 % |
| gi_bleed_72f | 30 | 1054 | 2,12 | 2,55 | 3,19 | 4,23 | 7,72 | 32 % | 68 % | 17 % | 2 % |
| gi_bleed_72f | 60 | 1054 | 1,48 | 2,16 | 3,04 | 4,42 | 8,77 | 30 % | 70 % | 27 % | 4 % |
| gi_bleed_72f | 90 | 1054 | 1,16 | 1,93 | 2,95 | 4,49 | 8,80 | 30 % | 70 % | 34 % | 9 % |
| gi_bleed_72f | 120 | 1054 | 1,03 | 1,83 | 2,92 | 4,63 | 8,67 | 32 % | 68 % | 37 % | 9 % |

**L3 · control definitivo y reanimación adecuada (2 unidades en 60 min, IBP y endoscopia)**

| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0 | 1054 | 4,40 | 4,40 | 4,40 | 4,40 | 4,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,55 | 4,20 | 4,78 | 6,89 | 23 % | 77 % | 5 % | 2 % |
| gi_bleed_57m | 30 | 1054 | 2,63 | 2,99 | 4,00 | 4,99 | 8,11 | 21 % | 79 % | 24 % | 2 % |
| gi_bleed_57m | 60 | 1054 | 1,73 | 2,21 | 3,64 | 4,81 | 8,19 | 18 % | 82 % | 43 % | 14 % |
| gi_bleed_57m | 90 | 1054 | 1,28 | 1,69 | 3,29 | 4,63 | 7,01 | 12 % | 88 % | 63 % | 20 % |
| gi_bleed_57m | 120 | 1054 | 1,04 | 1,39 | 2,98 | 4,28 | 5,97 | 9 % | 91 % | 72 % | 33 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,84 | 3,28 | 3,90 | 6,18 | 32 % | 68 % | 5 % | 2 % |
| gi_bleed_72f | 30 | 1054 | 2,12 | 2,52 | 3,18 | 4,23 | 7,64 | 31 % | 69 % | 17 % | 2 % |
| gi_bleed_72f | 60 | 1054 | 1,48 | 1,98 | 2,95 | 4,28 | 8,09 | 24 % | 76 % | 28 % | 3 % |
| gi_bleed_72f | 90 | 1054 | 1,14 | 1,63 | 2,73 | 4,16 | 7,04 | 19 % | 81 % | 39 % | 11 % |
| gi_bleed_72f | 120 | 1054 | 0,98 | 1,39 | 2,51 | 3,92 | 5,74 | 16 % | 84 % | 47 % | 11 % |

**L4 · hemostasia sin recuperar la perfusión (IBP y endoscopia sin volumen) — COMPOSICIÓN CONTRAFACTUAL MANUAL: la hemostasia se agregó a mano en el minuto de L3; el motor no la produce**

> L4 contrafactual: no es una trayectoria que el motor heredado produzca. Se muestra sólo como contraste y ninguna pregunta de la hoja de trabajo la usa.

| Caso | min | n | mínimo | p10 | mediana | p90 | máximo | sube | baja | cambia > 1 | cambia > 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0 | 1054 | 4,40 | 4,40 | 4,40 | 4,40 | 4,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_57m | 15 | 1054 | 3,37 | 3,58 | 4,20 | 4,80 | 6,92 | 23 % | 77 % | 6 % | 2 % |
| gi_bleed_57m | 30 | 1054 | 2,64 | 3,10 | 4,03 | 5,03 | 8,33 | 23 % | 77 % | 23 % | 2 % |
| gi_bleed_57m | 60 | 1054 | 1,77 | 2,55 | 3,78 | 5,27 | 9,44 | 23 % | 77 % | 36 % | 12 % |
| gi_bleed_57m | 90 | 1054 | 1,37 | 2,41 | 3,64 | 5,40 | 9,60 | 24 % | 76 % | 47 % | 14 % |
| gi_bleed_57m | 120 | 1054 | 1,21 | 2,31 | 3,57 | 5,43 | 9,45 | 27 % | 73 % | 54 % | 17 % |
| gi_bleed_72f | 0 | 1054 | 3,40 | 3,40 | 3,40 | 3,40 | 3,40 | 0 % | 0 % | 0 % | 0 % |
| gi_bleed_72f | 15 | 1054 | 2,66 | 2,86 | 3,28 | 3,91 | 6,20 | 32 % | 68 % | 5 % | 2 % |
| gi_bleed_72f | 30 | 1054 | 2,13 | 2,59 | 3,21 | 4,25 | 7,81 | 32 % | 68 % | 16 % | 3 % |
| gi_bleed_72f | 60 | 1054 | 1,50 | 2,26 | 3,10 | 4,70 | 9,10 | 32 % | 68 % | 23 % | 5 % |
| gi_bleed_72f | 90 | 1054 | 1,21 | 2,09 | 3,05 | 4,81 | 9,27 | 34 % | 66 % | 34 % | 7 % |
| gi_bleed_72f | 120 | 1054 | 1,08 | 1,96 | 3,04 | 4,99 | 9,07 | 35 % | 65 % | 38 % | 9 % |

## 4. Clases de comportamiento (conteos sobre la región; ninguna se declara correcta)

**gi_bleed_57m**

| Escenario y lectura | Clase | n | Dónde se concentra (mayor proporción por factor) |
|---|---|---|---|
| L1 a los 60 min | A baja | 592 | `arrival_delivery_ratio` superior (46 %); `arrival_lactate_excess` superior (40 %); `arrival_oxygen_debt` inferior (64 %); `debt_clearance_tau_min` 120 (43 %); `lactate_clearance_tau_min` 45 (41 %); `lactate_per_output_deficit` 2 (51 %) |
| L1 a los 60 min | B aproximadamente estable | 309 | `arrival_delivery_ratio` inferior (43 %); `arrival_lactate_excess` inferior (49 %); `arrival_oxygen_debt` superior (36 %); `debt_clearance_tau_min` 60 (40 %); `lactate_clearance_tau_min` 240 (59 %); `lactate_per_output_deficit` 6 (48 %) |
| L1 a los 60 min | C sube moderadamente | 120 | `arrival_delivery_ratio` inferior (45 %); `arrival_lactate_excess` inferior (42 %); `arrival_oxygen_debt` superior (78 %); `debt_clearance_tau_min` 60 (42 %); `lactate_clearance_tau_min` 120 (35 %); `lactate_per_output_deficit` 12 (80 %) |
| L1 a los 60 min | D sube sustancialmente | 33 | `arrival_delivery_ratio` inferior (64 %); `arrival_lactate_excess` inferior (45 %); `arrival_oxygen_debt` superior (100 %); `debt_clearance_tau_min` 60 (91 %); `lactate_clearance_tau_min` 45 (64 %); `lactate_per_output_deficit` 12 (100 %) |
| L1 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 592 | |
| L1 a los 120 min | A baja | 580 | `arrival_delivery_ratio` superior (47 %); `arrival_lactate_excess` superior (37 %); `arrival_oxygen_debt` inferior (56 %); `debt_clearance_tau_min` 120 (43 %); `lactate_clearance_tau_min` 45 (35 %); `lactate_per_output_deficit` 2 (60 %) |
| L1 a los 120 min | B aproximadamente estable | 240 | `arrival_delivery_ratio` inferior (42 %); `arrival_lactate_excess` inferior (39 %); `arrival_oxygen_debt` inferior (44 %); `debt_clearance_tau_min` 120 (40 %); `lactate_clearance_tau_min` 240 (49 %); `lactate_per_output_deficit` 6 (56 %) |
| L1 a los 120 min | C sube moderadamente | 156 | `arrival_delivery_ratio` inferior (46 %); `arrival_lactate_excess` inferior (40 %); `arrival_oxygen_debt` superior (50 %); `debt_clearance_tau_min` 60 (44 %); `lactate_clearance_tau_min` 120 (37 %); `lactate_per_output_deficit` 12 (81 %) |
| L1 a los 120 min | D sube sustancialmente | 78 | `arrival_delivery_ratio` inferior (69 %); `arrival_lactate_excess` inferior (50 %); `arrival_oxygen_debt` superior (69 %); `debt_clearance_tau_min` 60 (58 %); `lactate_clearance_tau_min` 45 (65 %); `lactate_per_output_deficit` 12 (100 %) |
| L1 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 580 | |
| L2 a los 60 min | A baja | 676 | `arrival_delivery_ratio` superior (43 %); `arrival_lactate_excess` superior (38 %); `arrival_oxygen_debt` inferior (64 %); `debt_clearance_tau_min` 120 (41 %); `lactate_clearance_tau_min` 45 (40 %); `lactate_per_output_deficit` 2 (46 %) |
| L2 a los 60 min | B aproximadamente estable | 273 | `arrival_delivery_ratio` inferior (42 %); `arrival_lactate_excess` inferior (46 %); `arrival_oxygen_debt` superior (47 %); `debt_clearance_tau_min` 60 (43 %); `lactate_clearance_tau_min` 240 (59 %); `lactate_per_output_deficit` 6 (45 %) |
| L2 a los 60 min | C sube moderadamente | 75 | `arrival_delivery_ratio` inferior (48 %); `arrival_lactate_excess` inferior (48 %); `arrival_oxygen_debt` superior (96 %); `debt_clearance_tau_min` 60 (52 %); `lactate_clearance_tau_min` 45 (36 %); `lactate_per_output_deficit` 12 (84 %) |
| L2 a los 60 min | D sube sustancialmente | 30 | `arrival_delivery_ratio` inferior (70 %); `arrival_lactate_excess` inferior (40 %); `arrival_oxygen_debt` superior (100 %); `debt_clearance_tau_min` 60 (90 %); `lactate_clearance_tau_min` 45 (70 %); `lactate_per_output_deficit` 12 (100 %) |
| L2 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 676 | |
| L2 a los 120 min | A baja | 739 | `arrival_delivery_ratio` superior (45 %); `arrival_lactate_excess` superior (37 %); `arrival_oxygen_debt` inferior (56 %); `debt_clearance_tau_min` 120 (42 %); `lactate_clearance_tau_min` 45 (35 %); `lactate_per_output_deficit` 2 (47 %) |
| L2 a los 120 min | B aproximadamente estable | 192 | `arrival_delivery_ratio` inferior (50 %); `arrival_lactate_excess` inferior (44 %); `arrival_oxygen_debt` superior (41 %); `debt_clearance_tau_min` 60 (44 %); `lactate_clearance_tau_min` 240 (45 %); `lactate_per_output_deficit` 12 (58 %) |
| L2 a los 120 min | C sube moderadamente | 96 | `arrival_delivery_ratio` inferior (56 %); `arrival_lactate_excess` inferior (50 %); `arrival_oxygen_debt` superior (78 %); `debt_clearance_tau_min` 60 (47 %); `lactate_clearance_tau_min` 240 (34 %); `lactate_per_output_deficit` 12 (91 %) |
| L2 a los 120 min | D sube sustancialmente | 27 | `arrival_delivery_ratio` inferior (100 %); `arrival_lactate_excess` inferior (56 %); `arrival_oxygen_debt` superior (89 %); `debt_clearance_tau_min` 60 (78 %); `lactate_clearance_tau_min` 45 (56 %); `lactate_per_output_deficit` 12 (100 %) |
| L2 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 739 | |
| L3 en 120 min | E baja claramente en 30 min | 417 | `arrival_delivery_ratio` superior (44 %); `arrival_lactate_excess` superior (38 %); `arrival_oxygen_debt` inferior (72 %); `debt_clearance_tau_min` 120 (40 %); `lactate_clearance_tau_min` 45 (58 %); `lactate_per_output_deficit` 2 (46 %) |
| L3 en 120 min | E' baja claramente después de 30 min | 481 | `arrival_delivery_ratio` inferior (36 %); `arrival_lactate_excess` inferior (36 %); `arrival_oxygen_debt` inferior (39 %); `debt_clearance_tau_min` 60 (39 %); `lactate_clearance_tau_min` 240 (59 %); `lactate_per_output_deficit` 6 (40 %) |
| L3 en 120 min | F sigue elevado con la entrega restaurada | 156 | `arrival_delivery_ratio` inferior (48 %); `arrival_lactate_excess` inferior (46 %); `arrival_oxygen_debt` superior (94 %); `debt_clearance_tau_min` 60 (54 %); `lactate_clearance_tau_min` 240 (44 %); `lactate_per_output_deficit` 12 (75 %) |
| L4 (contrafactual) en 120 min | E baja claramente en 30 min | 402 | `arrival_delivery_ratio` superior (45 %); `arrival_lactate_excess` medio (38 %); `arrival_oxygen_debt` inferior (72 %); `debt_clearance_tau_min` 120 (42 %); `lactate_clearance_tau_min` 45 (59 %); `lactate_per_output_deficit` 2 (47 %) |
| L4 (contrafactual) en 120 min | E' baja claramente después de 30 min | 304 | `arrival_delivery_ratio` superior (43 %); `arrival_lactate_excess` superior (36 %); `arrival_oxygen_debt` inferior (44 %); `debt_clearance_tau_min` 120 (39 %); `lactate_clearance_tau_min` 240 (65 %); `lactate_per_output_deficit` 2 (52 %) |
| L4 (contrafactual) en 120 min | F' sigue elevado sin restaurar la entrega | 348 | `arrival_delivery_ratio` inferior (47 %); `arrival_lactate_excess` inferior (46 %); `arrival_oxygen_debt` superior (56 %); `debt_clearance_tau_min` 60 (45 %); `lactate_clearance_tau_min` 240 (44 %); `lactate_per_output_deficit` 12 (64 %) |

**gi_bleed_72f**

| Escenario y lectura | Clase | n | Dónde se concentra (mayor proporción por factor) |
|---|---|---|---|
| L1 a los 60 min | A baja | 369 | `arrival_delivery_ratio` superior (54 %); `arrival_lactate_excess` superior (46 %); `arrival_oxygen_debt` inferior (73 %); `debt_clearance_tau_min` 120 (43 %); `lactate_clearance_tau_min` 45 (52 %); `lactate_per_output_deficit` 2 (55 %) |
| L1 a los 60 min | B aproximadamente estable | 466 | `arrival_delivery_ratio` inferior (42 %); `arrival_lactate_excess` inferior (43 %); `arrival_oxygen_debt` inferior (43 %); `debt_clearance_tau_min` 120 (39 %); `lactate_clearance_tau_min` 240 (55 %); `lactate_per_output_deficit` 6 (41 %) |
| L1 a los 60 min | C sube moderadamente | 165 | `arrival_delivery_ratio` inferior (42 %); `arrival_lactate_excess` inferior (42 %); `arrival_oxygen_debt` superior (65 %); `debt_clearance_tau_min` 60 (44 %); `lactate_clearance_tau_min` 45 (36 %); `lactate_per_output_deficit` 12 (69 %) |
| L1 a los 60 min | D sube sustancialmente | 54 | `arrival_delivery_ratio` inferior (56 %); `arrival_lactate_excess` inferior (44 %); `arrival_oxygen_debt` superior (94 %); `debt_clearance_tau_min` 60 (72 %); `lactate_clearance_tau_min` 45 (67 %); `lactate_per_output_deficit` 12 (94 %) |
| L1 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 369 | |
| L1 a los 120 min | A baja | 402 | `arrival_delivery_ratio` superior (52 %); `arrival_lactate_excess` superior (45 %); `arrival_oxygen_debt` inferior (61 %); `debt_clearance_tau_min` 120 (46 %); `lactate_clearance_tau_min` 45 (39 %); `lactate_per_output_deficit` 2 (69 %) |
| L1 a los 120 min | B aproximadamente estable | 358 | `arrival_delivery_ratio` inferior (39 %); `arrival_lactate_excess` inferior (45 %); `arrival_oxygen_debt` inferior (48 %); `debt_clearance_tau_min` 120 (38 %); `lactate_clearance_tau_min` 240 (46 %); `lactate_per_output_deficit` 6 (53 %) |
| L1 a los 120 min | C sube moderadamente | 198 | `arrival_delivery_ratio` inferior (48 %); `arrival_lactate_excess` inferior (45 %); `arrival_oxygen_debt` superior (45 %); `debt_clearance_tau_min` 60 (44 %); `lactate_clearance_tau_min` 240 (35 %); `lactate_per_output_deficit` 12 (67 %) |
| L1 a los 120 min | D sube sustancialmente | 96 | `arrival_delivery_ratio` inferior (66 %); `arrival_lactate_excess` inferior (47 %); `arrival_oxygen_debt` superior (72 %); `debt_clearance_tau_min` 60 (56 %); `lactate_clearance_tau_min` 45 (56 %); `lactate_per_output_deficit` 12 (97 %) |
| L1 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 402 | |
| L2 a los 60 min | A baja | 429 | `arrival_delivery_ratio` superior (55 %); `arrival_lactate_excess` superior (44 %); `arrival_oxygen_debt` inferior (74 %); `debt_clearance_tau_min` 120 (41 %); `lactate_clearance_tau_min` 45 (48 %); `lactate_per_output_deficit` 2 (49 %) |
| L2 a los 60 min | B aproximadamente estable | 448 | `arrival_delivery_ratio` inferior (45 %); `arrival_lactate_excess` inferior (44 %); `arrival_oxygen_debt` inferior (37 %); `debt_clearance_tau_min` 120 (38 %); `lactate_clearance_tau_min` 240 (55 %); `lactate_per_output_deficit` 6 (40 %) |
| L2 a los 60 min | C sube moderadamente | 132 | `arrival_delivery_ratio` inferior (41 %); `arrival_lactate_excess` inferior (45 %); `arrival_oxygen_debt` superior (80 %); `debt_clearance_tau_min` 60 (48 %); `lactate_clearance_tau_min` 120 (36 %); `lactate_per_output_deficit` 12 (68 %) |
| L2 a los 60 min | D sube sustancialmente | 45 | `arrival_delivery_ratio` inferior (67 %); `arrival_lactate_excess` inferior (47 %); `arrival_oxygen_debt` superior (100 %); `debt_clearance_tau_min` 60 (73 %); `lactate_clearance_tau_min` 45 (73 %); `lactate_per_output_deficit` 12 (93 %) |
| L2 a los 60 min | de las que bajan: con la entrega de O2 cayendo | 429 | |
| L2 a los 120 min | A baja | 520 | `arrival_delivery_ratio` superior (52 %); `arrival_lactate_excess` superior (42 %); `arrival_oxygen_debt` inferior (62 %); `debt_clearance_tau_min` 120 (40 %); `lactate_clearance_tau_min` 45 (39 %); `lactate_per_output_deficit` 2 (57 %) |
| L2 a los 120 min | B aproximadamente estable | 315 | `arrival_delivery_ratio` inferior (44 %); `arrival_lactate_excess` inferior (47 %); `arrival_oxygen_debt` inferior (37 %); `debt_clearance_tau_min` 120 (41 %); `lactate_clearance_tau_min` 240 (50 %); `lactate_per_output_deficit` 6 (50 %) |
| L2 a los 120 min | C sube moderadamente | 165 | `arrival_delivery_ratio` inferior (53 %); `arrival_lactate_excess` inferior (47 %); `arrival_oxygen_debt` superior (60 %); `debt_clearance_tau_min` 60 (44 %); `lactate_clearance_tau_min` 120 (35 %); `lactate_per_output_deficit` 12 (75 %) |
| L2 a los 120 min | D sube sustancialmente | 54 | `arrival_delivery_ratio` inferior (89 %); `arrival_lactate_excess` inferior (50 %); `arrival_oxygen_debt` superior (83 %); `debt_clearance_tau_min` 60 (67 %); `lactate_clearance_tau_min` 45 (56 %); `lactate_per_output_deficit` 12 (100 %) |
| L2 a los 120 min | de las que bajan: con la entrega de O2 cayendo | 520 | |
| L3 en 120 min | E baja claramente en 30 min | 261 | `arrival_delivery_ratio` superior (55 %); `arrival_lactate_excess` superior (45 %); `arrival_oxygen_debt` inferior (83 %); `debt_clearance_tau_min` 120 (41 %); `lactate_clearance_tau_min` 45 (71 %); `lactate_per_output_deficit` 2 (48 %) |
| L3 en 120 min | E' baja claramente después de 30 min | 490 | `arrival_delivery_ratio` inferior (37 %); `arrival_lactate_excess` medio (36 %); `arrival_oxygen_debt` inferior (50 %); `debt_clearance_tau_min` 60 (37 %); `lactate_clearance_tau_min` 240 (42 %); `lactate_per_output_deficit` 2 (40 %) |
| L3 en 120 min | F sigue elevado con la entrega restaurada | 303 | `arrival_delivery_ratio` inferior (45 %); `arrival_lactate_excess` inferior (55 %); `arrival_oxygen_debt` superior (70 %); `debt_clearance_tau_min` 60 (48 %); `lactate_clearance_tau_min` 240 (48 %); `lactate_per_output_deficit` 12 (54 %) |
| L4 (contrafactual) en 120 min | E baja claramente en 30 min | 255 | `arrival_delivery_ratio` superior (56 %); `arrival_lactate_excess` superior (45 %); `arrival_oxygen_debt` inferior (82 %); `debt_clearance_tau_min` 120 (42 %); `lactate_clearance_tau_min` 45 (72 %); `lactate_per_output_deficit` 2 (48 %) |
| L4 (contrafactual) en 120 min | E' baja claramente después de 30 min | 256 | `arrival_delivery_ratio` superior (45 %); `arrival_lactate_excess` medio (41 %); `arrival_oxygen_debt` inferior (49 %); `debt_clearance_tau_min` 120 (40 %); `lactate_clearance_tau_min` 240 (47 %); `lactate_per_output_deficit` 2 (63 %) |
| L4 (contrafactual) en 120 min | F' sigue elevado sin restaurar la entrega | 543 | `arrival_delivery_ratio` inferior (46 %); `arrival_lactate_excess` inferior (48 %); `arrival_oxygen_debt` superior (46 %); `debt_clearance_tau_min` 60 (42 %); `lactate_clearance_tau_min` 240 (43 %); `lactate_per_output_deficit` 12 (50 %) |

## 5. Descomposición del mecanismo (exacta dada la trayectoria del déficit)

Exceso de lactato = lo que queda del exceso de llegada + lo que produce la D de llegada + lo producido por el déficit posterior. Suma exacta para las recurrencias del modelo; no es una atribución causal entre parámetros.

**gi_bleed_57m · bajo · L1** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 3,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 2, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 0,80 | 3,60 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,00 | 0,00 |
| 15 | 3,37 | 0,80 | 2,57 | 0,00 | 0,00 | 0,6 | 0,0 | 0,6 | 0,0 | 0,92 | 0,08 |
| 30 | 2,64 | 0,80 | 1,83 | 0,00 | 0,01 | 2,2 | 0,0 | 2,4 | 0,2 | 0,83 | 0,17 |
| 60 | 1,78 | 0,80 | 0,93 | 0,00 | 0,05 | 8,3 | 0,0 | 9,7 | 1,4 | 0,67 | 0,33 |
| 90 | 1,41 | 0,80 | 0,48 | 0,00 | 0,13 | 17,3 | 0,0 | 21,9 | 4,5 | 0,51 | 0,49 |
| 120 | 1,30 | 0,80 | 0,24 | 0,00 | 0,26 | 28,5 | 0,0 | 38,7 | 10,2 | 0,36 | 0,64 |

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
| 15 | 4,22 | 1,00 | 3,00 | 0,21 | 0,01 | 18,0 | 15,5 | 2,7 | 4,7 | 0,78 | 0,22 |
| 30 | 4,05 | 1,00 | 2,65 | 0,35 | 0,06 | 17,4 | 12,1 | 6,5 | 9,1 | 0,71 | 0,29 |
| 60 | 3,77 | 1,00 | 2,06 | 0,48 | 0,23 | 19,1 | 7,3 | 17,3 | 18,1 | 0,57 | 0,43 |
| 90 | 3,63 | 1,00 | 1,60 | 0,50 | 0,52 | 23,4 | 4,4 | 32,1 | 28,7 | 0,44 | 0,56 |
| 120 | 3,63 | 1,00 | 1,25 | 0,47 | 0,91 | 29,2 | 2,7 | 50,9 | 41,7 | 0,31 | 0,69 |

**gi_bleed_57m · medio · L3** — `arrival_oxygen_debt` 20, `arrival_lactate_excess` 3,40, `arrival_delivery_ratio` 0,85, τ_D 60, g 1,0, G 6, τ_L 120, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 1,00 | 3,40 | 0,00 | 0,00 | 20,0 | 20,0 | 0,0 | 0,0 | 0,85 | 0,15 |
| 15 | 4,21 | 1,00 | 3,00 | 0,21 | 0,01 | 16,1 | 15,5 | 0,7 | 4,6 | 1,14 | 0,00 |
| 30 | 4,00 | 1,00 | 2,65 | 0,35 | 0,01 | 12,5 | 12,1 | 0,7 | 8,2 | 1,42 | 0,00 |
| 60 | 3,55 | 1,00 | 2,06 | 0,48 | 0,02 | 7,5 | 7,3 | 0,7 | 13,1 | 1,95 | 0,00 |
| 90 | 3,12 | 1,00 | 1,60 | 0,50 | 0,02 | 4,6 | 4,4 | 0,7 | 16,1 | 1,94 | 0,00 |
| 120 | 2,73 | 1,00 | 1,25 | 0,47 | 0,02 | 2,8 | 2,7 | 0,7 | 17,9 | 1,93 | 0,00 |

**gi_bleed_57m · alto · L1** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 2,00 | 2,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 6,92 | 2,00 | 1,71 | 3,04 | 0,16 | 52,3 | 46,6 | 6,4 | 14,0 | 0,55 | 0,45 |
| 30 | 8,34 | 2,00 | 1,22 | 4,53 | 0,59 | 47,0 | 36,2 | 13,4 | 26,5 | 0,50 | 0,50 |
| 60 | 9,50 | 2,00 | 0,62 | 5,05 | 1,83 | 41,5 | 21,9 | 29,8 | 48,4 | 0,40 | 0,60 |
| 90 | 9,81 | 2,00 | 0,32 | 4,22 | 3,26 | 40,4 | 13,2 | 49,1 | 68,7 | 0,31 | 0,69 |
| 120 | 10,01 | 2,00 | 0,16 | 3,15 | 4,70 | 42,0 | 8,0 | 71,2 | 89,2 | 0,22 | 0,78 |

**gi_bleed_57m · alto · L3** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,40 | 2,00 | 2,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 6,89 | 2,00 | 1,71 | 3,04 | 0,13 | 50,6 | 46,6 | 4,6 | 13,9 | 0,80 | 0,20 |
| 30 | 8,11 | 2,00 | 1,22 | 4,53 | 0,35 | 40,7 | 36,2 | 6,1 | 25,4 | 1,00 | 0,00 |
| 60 | 8,19 | 2,00 | 0,62 | 5,05 | 0,52 | 24,6 | 21,9 | 6,1 | 41,5 | 1,37 | 0,00 |
| 90 | 7,01 | 2,00 | 0,32 | 4,22 | 0,47 | 14,8 | 13,2 | 6,1 | 51,3 | 1,37 | 0,00 |
| 120 | 5,67 | 2,00 | 0,16 | 3,15 | 0,36 | 9,0 | 8,0 | 6,1 | 57,2 | 1,36 | 0,00 |

**gi_bleed_72f · bajo · L1** — `arrival_oxygen_debt` 0, `arrival_lactate_excess` 2,60, `arrival_delivery_ratio` 1,00, τ_D 120, g 1,0, G 2, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 0,80 | 2,60 | 0,00 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 1,00 | 0,00 |
| 15 | 2,66 | 0,80 | 1,86 | 0,00 | 0,00 | 0,4 | 0,0 | 0,4 | 0,0 | 0,95 | 0,05 |
| 30 | 2,13 | 0,80 | 1,32 | 0,00 | 0,00 | 1,5 | 0,0 | 1,6 | 0,1 | 0,89 | 0,11 |
| 60 | 1,51 | 0,80 | 0,68 | 0,00 | 0,03 | 5,5 | 0,0 | 6,4 | 0,9 | 0,78 | 0,22 |
| 90 | 1,23 | 0,80 | 0,34 | 0,00 | 0,09 | 11,5 | 0,0 | 14,5 | 3,0 | 0,68 | 0,32 |
| 120 | 1,14 | 0,80 | 0,18 | 0,00 | 0,17 | 18,9 | 0,0 | 25,7 | 6,7 | 0,57 | 0,43 |

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
| 15 | 3,34 | 1,00 | 2,12 | 0,21 | 0,01 | 17,9 | 15,5 | 2,6 | 4,7 | 0,80 | 0,20 |
| 30 | 3,27 | 1,00 | 1,87 | 0,35 | 0,05 | 16,8 | 12,1 | 5,9 | 9,0 | 0,76 | 0,24 |
| 60 | 3,14 | 1,00 | 1,45 | 0,48 | 0,20 | 17,1 | 7,3 | 14,5 | 17,4 | 0,67 | 0,33 |
| 90 | 3,06 | 1,00 | 1,13 | 0,50 | 0,43 | 19,4 | 4,4 | 25,8 | 26,4 | 0,58 | 0,42 |
| 120 | 3,07 | 1,00 | 0,88 | 0,47 | 0,73 | 22,9 | 2,7 | 39,8 | 36,9 | 0,49 | 0,51 |

**gi_bleed_72f · medio · L3** — `arrival_oxygen_debt` 20, `arrival_lactate_excess` 2,40, `arrival_delivery_ratio` 0,85, τ_D 60, g 1,0, G 6, τ_L 120, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 1,00 | 2,40 | 0,00 | 0,00 | 20,0 | 20,0 | 0,0 | 0,0 | 0,85 | 0,15 |
| 15 | 3,33 | 1,00 | 2,12 | 0,21 | 0,01 | 16,3 | 15,5 | 0,9 | 4,6 | 1,07 | 0,00 |
| 30 | 3,23 | 1,00 | 1,87 | 0,35 | 0,01 | 12,6 | 12,1 | 0,9 | 8,2 | 1,28 | 0,00 |
| 60 | 2,95 | 1,00 | 1,45 | 0,48 | 0,02 | 7,6 | 7,3 | 0,9 | 13,2 | 1,67 | 0,00 |
| 90 | 2,65 | 1,00 | 1,13 | 0,50 | 0,02 | 4,6 | 4,4 | 0,9 | 16,2 | 1,67 | 0,00 |
| 120 | 2,37 | 1,00 | 0,88 | 0,47 | 0,02 | 2,8 | 2,7 | 0,9 | 18,1 | 1,66 | 0,00 |

**gi_bleed_72f · alto · L1** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 1,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 2,00 | 1,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 6,20 | 2,00 | 1,00 | 3,04 | 0,16 | 52,2 | 46,6 | 6,2 | 14,0 | 0,57 | 0,43 |
| 30 | 7,82 | 2,00 | 0,71 | 4,53 | 0,57 | 46,6 | 36,2 | 13,0 | 26,4 | 0,53 | 0,47 |
| 60 | 9,14 | 2,00 | 0,36 | 5,05 | 1,73 | 40,0 | 21,9 | 27,9 | 47,9 | 0,47 | 0,53 |
| 90 | 9,41 | 2,00 | 0,19 | 4,22 | 3,00 | 37,5 | 13,2 | 44,7 | 67,1 | 0,41 | 0,59 |
| 120 | 9,44 | 2,00 | 0,09 | 3,15 | 4,20 | 37,6 | 8,0 | 63,4 | 85,8 | 0,34 | 0,66 |

**gi_bleed_72f · alto · L3** — `arrival_oxygen_debt` 60, `arrival_lactate_excess` 1,40, `arrival_delivery_ratio` 0,60, τ_D 60, g 1,0, G 12, τ_L 45, demanda 1,00

| min | lactato | basal | exceso de llegada restante | de la D de llegada | del déficit posterior | D | D de llegada restante | D acumulada desde la llegada | D pagada | entrega | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,40 | 2,00 | 1,40 | 0,00 | 0,00 | 60,0 | 60,0 | 0,0 | 0,0 | 0,60 | 0,40 |
| 15 | 6,18 | 2,00 | 1,00 | 3,04 | 0,14 | 51,0 | 46,6 | 4,9 | 13,9 | 0,75 | 0,25 |
| 30 | 7,64 | 2,00 | 0,71 | 4,53 | 0,40 | 42,0 | 36,2 | 7,6 | 25,6 | 0,90 | 0,10 |
| 60 | 8,09 | 2,00 | 0,36 | 5,05 | 0,68 | 25,7 | 21,9 | 8,2 | 42,5 | 1,18 | 0,00 |
| 90 | 7,04 | 2,00 | 0,19 | 4,22 | 0,63 | 15,5 | 13,2 | 8,2 | 52,6 | 1,18 | 0,00 |
| 120 | 5,74 | 2,00 | 0,09 | 3,15 | 0,50 | 9,4 | 8,0 | 8,2 | 58,8 | 1,17 | 0,00 |

## 6. D frente a lactato (no se declaran inválidos)

| Caso | Patrón | corridas | de | ejemplos (D desde → hasta; lactato desde → hasta) |
|---|---|---|---|---|
| gi_bleed_57m | L1, 0–60 min: D sube mientras el lactato baja | 591 | 1054 | D 0,0→8,3, lactato 4,40→1,78; D 0,0→7,2, lactato 4,40→3,56; D 0,0→13,8, lactato 4,40→4,38 |
| gi_bleed_57m | L1, 0–120 min: D sube mientras el lactato baja | 565 | 1054 | D 0,0→28,5, lactato 4,40→1,30; D 20,0→29,2, lactato 4,40→3,34; D 20,0→29,2, lactato 4,40→4,34 |
| gi_bleed_57m | L3, 0–120 min: D baja mientras el lactato sigue a menos de 0,5 mmol/L de la llegada o por encima | 156 | 1054 | D 60,0→8,0, lactato 4,40→4,28; D 60,0→9,0, lactato 4,40→5,07; D 20,0→7,6, lactato 4,40→3,95 |
| gi_bleed_57m | L4 (contrafactual), 0–120 min: D sigue igual o por encima de la llegada mientras el lactato se mueve menos de 0,5 mmol/L | 141 | 1054 | D 20,0→20,2, lactato 4,40→3,94; D 20,0→32,1, lactato 4,40→3,91; D 0,0→39,9, lactato 4,40→3,90 |
| gi_bleed_72f | L1, 0–60 min: D sube mientras el lactato baja | 513 | 1054 | D 0,0→5,5, lactato 3,40→1,51; D 0,0→18,1, lactato 3,40→2,87; D 0,0→22,3, lactato 3,40→3,37 |
| gi_bleed_72f | L1, 0–120 min: D sube mientras el lactato baja | 492 | 1054 | D 0,0→18,9, lactato 3,40→1,14; D 0,0→14,6, lactato 3,40→2,66; D 20,0→34,8, lactato 3,40→3,39 |
| gi_bleed_72f | L3, 0–120 min: D baja mientras el lactato sigue a menos de 0,5 mmol/L de la llegada o por encima | 279 | 1054 | D 60,0→8,0, lactato 3,40→2,98; D 60,0→22,0, lactato 3,40→3,84; D 20,0→7,7, lactato 3,40→2,95 |
| gi_bleed_72f | L4 (contrafactual), 0–120 min: D sigue igual o por encima de la llegada mientras el lactato se mueve menos de 0,5 mmol/L | 159 | 1054 | D 0,0→4,7, lactato 3,40→2,92; D 0,0→14,6, lactato 3,40→3,57; D 0,0→36,7, lactato 3,40→3,24 |

## 7. Impacto de cada parámetro en las lecturas de las decisiones

ALTO ≥ 1 mmol/L (o ≥ 30 min), MEDIO ≥ 0,3 mmol/L (o ≥ 10 min), BAJO por debajo: bandas de presentación, no criterios. Cada valor por nivel es la mediana de la lectura sobre los conjuntos con ese nivel. La región no es un diseño balanceado: no contiene τ_D = 30 con la deuda de llegada alta, así que el efecto de `debt_clearance_tau_min` se mezcla en parte con el de la deuda. `debt_per_delivery_deficit` y `metabolic_demand_baseline` no varían en la región; se sondean de a uno alrededor del candidato medio.

**gi_bleed_57m · L1: cambio a los 60 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | MEDIO | la aumenta | inferior: -0,84, medio: -0,51, superior: 0,13 | 0,97 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | MEDIO | la aumenta | 2: -0,95, 6: -0,51, 12: 0,01 | 0,97 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | MEDIO | la aumenta | 45: -1,31, 120: -0,72, 240: -0,40 | 0,91 | efecto principal sobre la región admisible |
| `debt_per_delivery_deficit` | MEDIO | la aumenta | 0,5: -0,74, 1: -0,63, 2: -0,39 | 0,35 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: -0,40, medio: -0,68, superior: -0,74 | 0,34 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | BAJO | la disminuye | inferior: -0,48, medio: -0,51, superior: -0,74 | 0,26 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | BAJO | no monótona | 30: -0,61, 60: -0,47, 120: -0,70 | 0,22 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: -0,72, 1: -0,63, 1,1: -0,53 | 0,19 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

**gi_bleed_57m · L3: primera caída clara (min; 121 = no en 120)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 21, medio: 46, superior: 106 | 85 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: 11, 120: 31, 240: 58 | 47 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | ALTO | la aumenta | 2: 28, 6: 41, 12: 60 | 32 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 56, medio: 39, superior: 36 | 20 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | MEDIO | no monótona | 30: 32, 60: 44, 120: 39 | 12 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | MEDIO | no monótona | inferior: 39, medio: 46, superior: 36 | 10 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 37, 1: 38, 1,1: 39 | 2 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 37, 1: 38, 2: 38 | 1 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

**gi_bleed_57m · L3: lactato a los 120 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: 2,06, 120: 2,88, 240: 3,45 | 1,39 | efecto principal sobre la región admisible |
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 2,39, medio: 3,04, superior: 3,77 | 1,38 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 3,39, medio: 2,73, superior: 2,60 | 0,79 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | MEDIO | la aumenta | 2: 2,64, 6: 2,98, 12: 3,21 | 0,57 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | MEDIO | no monótona | 30: 2,60, 60: 3,06, 120: 3,01 | 0,46 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | BAJO | no monótona | inferior: 3,03, medio: 3,04, superior: 2,88 | 0,16 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 2,71, 1: 2,73, 1,1: 2,75 | 0,04 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 2,72, 1: 2,73, 2: 2,74 | 0,02 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

**gi_bleed_72f · L1: cambio a los 60 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: -0,53, medio: -0,18, superior: 0,49 | 1,02 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | MEDIO | la aumenta | 2: -0,55, 6: -0,19, 12: 0,34 | 0,89 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | MEDIO | la aumenta | 45: -0,61, 120: -0,34, 240: -0,19 | 0,42 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: -0,09, medio: -0,42, superior: -0,46 | 0,37 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | MEDIO | la disminuye | inferior: -0,18, medio: -0,18, superior: -0,50 | 0,32 | efecto principal sobre la región admisible |
| `debt_per_delivery_deficit` | MEDIO | la aumenta | 0,5: -0,37, 1: -0,26, 2: -0,06 | 0,30 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: -0,36, 1: -0,26, 1,1: -0,17 | 0,19 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_clearance_tau_min` | BAJO | no monótona | 30: -0,34, 60: -0,19, 120: -0,34 | 0,15 | efecto principal sobre la región admisible |

**gi_bleed_72f · L3: primera caída clara (min; 121 = no en 120)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 36, medio: 79, superior: 121 | 85 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | ALTO | la aumenta | 45: 24, 120: 58, 240: 106 | 82 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | ALTO | la disminuye | inferior: 118, medio: 56, superior: 52 | 66 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | ALTO | la aumenta | 2: 52, 6: 76, 12: 109 | 57 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | MEDIO | no monótona | 30: 56, 60: 85, 120: 67 | 29 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | MEDIO | no monótona | inferior: 74, medio: 79, superior: 53 | 26 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 64, 1: 66, 1,1: 69 | 5 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 65, 1: 66, 2: 68 | 3 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

**gi_bleed_72f · L3: lactato a los 120 min (mmol/L)**

| Parámetro | Impacto | Dirección (de bajo a alto) | Valor por nivel | Rango | Origen |
|---|---|---|---|---|---|
| `arrival_oxygen_debt` | ALTO | la aumenta | inferior: 2,18, medio: 2,57, superior: 3,32 | 1,14 | efecto principal sobre la región admisible |
| `lactate_clearance_tau_min` | MEDIO | la aumenta | 45: 2,00, 120: 2,51, 240: 2,85 | 0,84 | efecto principal sobre la región admisible |
| `arrival_lactate_excess` | MEDIO | la disminuye | inferior: 2,89, medio: 2,41, superior: 2,29 | 0,61 | efecto principal sobre la región admisible |
| `lactate_per_output_deficit` | MEDIO | la aumenta | 2: 2,30, 6: 2,58, 12: 2,85 | 0,55 | efecto principal sobre la región admisible |
| `debt_clearance_tau_min` | BAJO | no monótona | 30: 2,38, 60: 2,63, 120: 2,56 | 0,26 | efecto principal sobre la región admisible |
| `arrival_delivery_ratio` | BAJO | la disminuye | inferior: 2,59, medio: 2,57, superior: 2,45 | 0,14 | efecto principal sobre la región admisible |
| `metabolic_demand_baseline` | BAJO | la aumenta | 0,9: 2,35, 1: 2,37, 1,1: 2,40 | 0,05 | sonda de a uno alrededor del candidato medio (la región no lo varía) |
| `debt_per_delivery_deficit` | BAJO | la aumenta | 0,5: 2,36, 1: 2,37, 2: 2,39 | 0,03 | sonda de a uno alrededor del candidato medio (la región no lo varía) |

## 8. Lo que el modelo ofrece para cada pregunta (sólo modelo)

Sólo trayectorias producidas por el motor: L1 para FD-LAC-02/03/06 y L3 para FD-LAC-04/05. La composición contrafactual L4 no entra en ninguna.

**gi_bleed_57m** (lactato de llegada 4,4)

- Sin tratar, a los 60 min (FD-LAC-02/03): mínimo 1,78, p10 2,61, mediana 3,79, p90 5,32, máximo 9,50 (1054 corridas).
- Primera caída clara (≥ 0,5 mmol/L bajo la llegada) tras el manejo definitivo (FD-LAC-04): en 15 min: 20 %, 15–30 min: 20 %, 30–60 min: 28 %, después de 60 min: 17 %, no en 120 min: 15 %.
- A los 120 min tras el manejo definitivo (FD-LAC-05): de 1,04 a 5,97, mediana 2,98; mediana sobre la basal candidata 1,55; mediana según la deuda de llegada: inferior 2,39, medio 3,04, superior 3,77.
- Sin tratar, con la entrega bajo la demanda a los 0, 15, 30 y 60 min (FD-LAC-06): 649 corridas; en 475 el lactato baja.

**gi_bleed_72f** (lactato de llegada 3,4)

- Sin tratar, a los 60 min (FD-LAC-02/03): mínimo 1,51, p10 2,27, mediana 3,10, p90 4,70, máximo 9,14 (1054 corridas).
- Primera caída clara (≥ 0,5 mmol/L bajo la llegada) tras el manejo definitivo (FD-LAC-04): en 15 min: 11 %, 15–30 min: 14 %, 30–60 min: 21 %, después de 60 min: 26 %, no en 120 min: 29 %.
- A los 120 min tras el manejo definitivo (FD-LAC-05): de 0,98 a 5,74, mediana 2,51; mediana sobre la basal candidata 1,16; mediana según la deuda de llegada: inferior 2,18, medio 2,57, superior 3,32.
- Sin tratar, con la entrega bajo la demanda a los 0, 15, 30 y 60 min (FD-LAC-06): 649 corridas; en 400 el lactato baja.

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
