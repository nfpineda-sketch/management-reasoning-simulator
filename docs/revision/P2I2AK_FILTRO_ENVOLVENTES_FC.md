# P2I-2AK · Filtro de la FC por envolventes observables docentes

Este paquete funciona sólo en sombra. No hace nada de esto:
- selección final de parámetros latentes de la FC, ni aprobación de ninguno;
- calibración de la presión, del tono vascular ni de la FR, ni activación del colapso;
- migración de GI ni de otra familia, ni integración en tiempo de ejecución;
- ajuste al motor heredado (no lo lee).

Código:
- `clinical_core/hr_envelope_filter.py`: demanda, envolventes A–F, comparadores contrafactuales de los GR, techos, orden
  del filtro, regla del candidato, reutilización, validación y veredicto. Se congeló en `9de09fa`, antes de ver ningún
  conteo.
- `clinical_core/hr_envelope_filter_report.py`: sólo este informe.

Números: `docs/revision/P2I2AK_hr_envelope_filter.json`. Registro de partida: P2I-2AJ (`2437e1b1…`), ahora cerrado (su
módulo queda fijado byte a byte). El núcleo, BloodState, el gasto, el DO2, el déficit, D, el lactato y la FR no cambian.

## Resumen

- **Filtro aplicado con las reglas congeladas.** Las demandas 1,0 y 1,1 se filtran por separado; 0,9 queda fuera. Las
  envolventes A–F se aplican tal como las fijó la docencia, con los GR contra su contrafactual y los techos primarios
  150 y 175.
- **Ninguna envolvente rechaza a ningún candidato.**
  - Con 1,0 entran 2 combinaciones latentes × 216 sobrevivientes de lactato = 432 candidatos, y sobreviven todos.
  - Con 1,1 entran 9 × 1092 = 9828, y sobreviven todos.
  - Toda la región compatible con la llegada, con el techo primario, cumple A–F con cada fila de lactato. **El filtro no
    estrecha la región latente**: la deja como estaba.
- **Márgenes (diagnóstico).**
  - A: la FC sin tratamiento de 57m llega a lo sumo a 157,6, a 2,4 lpm de 160.
  - B: la de 72f llega a lo sumo a 146,2, a 3,8 lpm de 150.
  - F: la taquicardia residual llega a lo sumo a 9,5 lpm, frente a 15.
  - E: la FC baja entre los minutos 60, 90 y 120 en todos los candidatos.
- **GR contra su contrafactual (C y D).**
  - Unidad 1: beneficio de 10–13 lpm con 1,0 y de 3–37 con 1,1.
  - Unidad 2 en 57m: 12–13 lpm con 1,0 y 3–32 con 1,1.
  - **Unidad 2 en 72f: exactamente 0 en todos los candidatos.** Lo explican una sonda fuera del registro, la revisión
    adversarial y una prueba:
    - en L3, el déficit efectivo de 72f llega a cero entre los minutos 12 y 13 (1,0) o 21 y 26 (1,1), según la unidad;
    - entre los minutos 30 y 60, L3 y el contrafactual tienen déficit cero y la misma D, aunque la entrega difiere;
    - las otras entradas de la FC (SpO2, glucosa y la memoria del impulso) también son iguales, así que la FC no
      cambia.
  - La regla D se cumple, porque el cero está permitido, pero en 72f no puede discriminar.
- **Techo 200 (sólo sensibilidad).** Las 4 combinaciones de 1,1 con techo 200 también cumplirían A–F. No entran en
  ningún resultado ni rescatan a nadie.
- **Entre demandas (diagnóstico):** 1 combinación ROBUST_ACROSS_DEMAND, 1 sólo con 1,0, 8 sólo con 1,1 y 440
  DEMAND_INCOMPATIBLE de 450. Hay 10 combinaciones primarias distintas.
- **Identificabilidad.** Todas las latentes quedan POORLY_IDENTIFIED, salvo la ganancia de deuda (NON_IDENTIFIABLE);
  con 1,0 sola, la ganancia aguda queda PARTIALLY_CONSTRAINED. Las envolventes son desigualdades y ninguna fue activa, así
  que no aportan identificación.
- **72f, cristaloide frente a GR:** la región superviviente conserva el hallazgo de P2I-2AJ.
  - Divergen desde el minuto 1, primero por la señal aguda.
  - Superan 1 lpm entre los minutos 9–13 (1,0) y 5–28 (1,1).
  - La mayor diferencia es de 18–25 lpm (1,0) o 10–54 lpm (1,1), con la FC más baja bajo GR. La revisión comprobó que
    cae en el minuto 120 en todos los pares; el registro no guarda ese minuto.
- **Veredicto: HR_OBSERVABLE_FILTER_SATISFIED.**
  - No se exigió robustez entre demandas.
  - La presión sigue DEFERRED, las ganancias son comunes y la fisiología previa no cambió.
  - Nada se aprobó.

## 1. Decisiones docentes y punto de partida

<!-- generado:decisiones -->
Congelamiento: `31f092650ee73ff4134fc9e5cc79b3a171fb7bb54de553fc2a7de2081f309dc3` (una prueba lo fija). Registro de partida: P2I-2AJ `2437e1b1c3075e180ef0fec912867974af43242a828c356190193820933fec4d`.

| Decisión docente | Texto registrado |
|---|---|
| fecha | 2026-10-30 |
| demanda | demand 0.9 (CURRENTLY_INCOMPATIBLE) is not in the primary HR filter; 1.0 and 1.1 are filtered separately with the same rules and never pooled before filtering; ROBUST_ACROSS_DEMAND, DEMAND_1_0_ONLY, DEMAND_1_1_ONLY and DEMAND_INCOMPATIBLE are diagnostic, never an acceptance criterion; no demand approved |
| sin tratamiento (A, B) | A: untreated 57m at minute 120, authored arrival HR (124) <= HR <= 160; B: untreated 72f at minute 120, 112 <= HR <= 150; case-specific calibration envelopes in the current non-collapse model, not a universal or 220 - age limit |
| GR (C, D) | C and D: each PRBC unit against its matched counterfactual at the same time (same case, latent HR, starting blood state, bleed, demand, other treatments, haemostasis and elapsed time; only the target unit omitted); HR with the unit <= HR without it; direction only, no minimum fall, no comparison between the units; the benefit HR_without - HR_with is reported, zero allowed |
| manejo definitivo (E, F) | E: after sustained adequacy no sustained rise through 120: HR_120 <= HR_90 <= HR_60 with adequacy sustained from minute 60; F: 0 <= HR_120 - intrinsic <= 15 after successful definitive management |
| techos | primary total sinus ceilings 150 and 175 (exploratory, not approved); 200 only as OUT_OF_PRIMARY_RANGE_SENSITIVITY_REFERENCE, never rescuing a primary rejection |
| alcance | shadow only; no final latent HR selection, no pressure / vascular-tone or RR calibration, no collapse, no migration, no runtime integration; pressure stays DEFERRED |
<!-- /generado:decisiones -->

## 2. Reglas congeladas (P2I-2AK-1, -2)

<!-- generado:reglas -->
| Regla | Escenario | Qué exige |
|---|---|---|
| A | L1, 57m, minuto 120 | 124 ≤ FC ≤ 160 lpm |
| B | L1, 72f, minuto 120 | 112 ≤ FC ≤ 150 lpm |
| F | L3, cada caso, minuto 120 | 0 ≤ FC − intrínseca ≤ 15 lpm |
| E | L3, cada caso | adecuación sostenida desde el minuto 60 (a más tardar) hasta 120, y FC_120 ≤ FC_90 ≤ FC_60, sin tolerancia |
| C | L3 frente a L3 sin la unidad 1, cada caso | en el minuto en que L3 completa la unidad 1: FC con la unidad ≤ FC sin ella |
| D | L3 frente a L3 sin la unidad 2, cada caso | en el minuto en que L3 completa la unidad 2: FC con la unidad ≤ FC sin ella |

- Techos primarios: 150, 175; 200 sólo como `OUT_OF_PRIMARY_RANGE_SENSITIVITY_REFERENCE`.
- Demanda: 1,0 y 1,1 por separado, con las mismas reglas; 0,9 queda fuera (CURRENTLY_INCOMPATIBLE).
- Orden congelado: ARRIVAL → PRIMARY_CEILING → A → B → F → E → C → D. Frozen before any count, cheapest first: the arrival +-5 compatibility (analytic, P2I-2AJ's surface), the primary ceiling support (analytic), then A, B (L1), F, E (L3), C, D (L3 against its counterfactuals). Every rule is evaluated for every candidate; the first failure is read in this order and the overlaps are reported.
- Comparador: A counterfactual is L3's own inputs with only the target PRBC unit removed. L3 infuses its units continuously (2 units over 60 min from minute 0: one unit per 30 min). Without unit 1: the infusion starts one unit-interval later with one unit less (unit 2 keeps its slot); without unit 2: the infusion stops after one unit-interval. The haemorrhage, PPI, endoscopic haemostasis, unit volume and Hb, blood state, demand, latent HR and elapsed time are L3's. The assessment minute is the first minute L3 has delivered that many units. Proved by tests: the counterfactual inputs equal L3's but for that one item; without unit 2 the run equals L3 minute for minute until unit 2 starts; the delivered units follow the omission; haemostasis lands at the same minute.
- Candidato: A candidate is (latent HR combination, lactate survivor of the retained pair) at one demand; the latent HR combination is (57m intrinsic, 72f intrinsic, acute gain, debt gain, ceiling). The rules read L1, L3 and its counterfactuals, which do not depend on the crystalloid point: a lactate survivor's verdict is its (P3 set, 57m point, 72f point) verdict. A latent HR combination SURVIVES at a demand when at least one of its lactate survivors satisfies every rule (the lactate side is uncertainty, as demand); how many do is reported, and ROW_ROBUST marks the combinations whose every lactate survivor survives (diagnostic).
<!-- /generado:reglas -->

## 3. Reutilización

<!-- generado:reutilizacion -->
- Dependencias ejecutables (todo `clinical_core` salvo las dos tuplas de exclusión y este módulo): `dfb02ee2cb3065258d1b648be7278a385334f678a892feebd83e05c0d4e3c6da`, igual al de P2I-2AJ: **sí**.
- Unidades de lactato del par retenido, reconstruidas con `hr_observables.retained_region`: demanda 1,0: `06f6d5c82fa3047643c4073bf77614e88499575de51ef9b22aa5514bca18488b`; demanda 1,1: `515a157e21181013c631d4ff879dcb18986b9be89d40ad44654105781f1e2db0`; iguales a las de P2I-2AJ: **sí**.
- Superficie de llegada analítica igual a la del registro de P2I-2AJ: **sí**.

Regla: Reused, never re-derived: the retained pair and its lactate survivors per demand (P2I-2AJ's retained_region, reproduced exactly: units digest 06f6d5c8... at 1.0 and 515a157e... at 1.1, else stop), the arrival surface (P2I-2AJ's analytic arrival table; its joint survivors equal its record's, else stop) and the executable dependencies (every clinical_core source equal to P2I-2AJ's certified HEAD but the exclusion tuples and this module, else stop). The physiology is the full core per (case, P3 set, lactate-side point, demand): L1, L3 and the two counterfactuals once each, HR post-processed for every latent HR combination; L2 only for the survivors (the 72f crystalloid diagnostic and the maximum HR). No blood, fluid or lactate re-calibration.
<!-- /generado:reutilizacion -->

## 4. Conteos por categoría

<!-- generado:conteos -->
| Categoría | demanda 1,0 | demanda 1,1 |
|---|---|---|
| rechazo por verdad del caso (P2I-2AJ) | 1 par de casos (25613 sobrevivientes de lactato) | 1 par de casos (8631 sobrevivientes de lactato) |
| rechazo por la FC de llegada (±5 lpm), sobre 450 combinaciones primarias | 448 | 441 |
| fuera del soporte primario de techo (200, sólo sensibilidad) | 0 | 4 |
| rechazo por envolventes A–F (candidatos) | 0 | 0 |
| rechazo de simulación (pulso perdido o corrida detenida) | 0 | 0 |
<!-- /generado:conteos -->

## 5. Filtro por demanda (P2I-2AK-3, -4)

<!-- generado:filtro -->
**Demanda 1,0.** Entran 2 combinaciones latentes × 216 sobrevivientes de lactato = **432 candidatos** (18 unidades de fisiología distintas). Rechazados por primer fallo: A 0; B 0; C 0; D 0; E 0; F 0; SIMULATION_REJECTION 0. Fallos en cualquier posición: ninguno; patrones de solapamiento: ninguno. **Sobreviven 432 candidatos y 2 combinaciones latentes.**

| Intrínsecas 57m / 72f, ganancias, techo | FC de llegada predicha 57m / 72f | Sobrevivientes de lactato que cumplen A–F | Estado | Todas las filas |
|---|---|---|---|---|
| superior / superior, aguda 1,46, deuda 0,0103, techo 150 | 126,9 / 110,5 | 216 de 216 | **SURVIVES** | sí |
| superior / superior, aguda 1,46, deuda 0,0103, techo 175 | 128,6 / 110,6 | 216 de 216 | **SURVIVES** | sí |

**Demanda 1,1.** Entran 9 combinaciones latentes × 1092 sobrevivientes de lactato = **9828 candidatos** (91 unidades de fisiología distintas). Rechazados por primer fallo: A 0; B 0; C 0; D 0; E 0; F 0; SIMULATION_REJECTION 0. Fallos en cualquier posición: ninguno; patrones de solapamiento: ninguno. **Sobreviven 9828 candidatos y 9 combinaciones latentes.**

| Intrínsecas 57m / 72f, ganancias, techo | FC de llegada predicha 57m / 72f | Sobrevivientes de lactato que cumplen A–F | Estado | Todas las filas |
|---|---|---|---|---|
| inferior / medio, aguda 1,46, deuda 0,0407, techo 150 | 122,8 / 107,1 | 1092 de 1092 | **SURVIVES** | sí |
| inferior / medio, aguda 1,46, deuda 0,0407, techo 175 | 127,6 / 107,8 | 1092 de 1092 | **SURVIVES** | sí |
| inferior / medio, aguda 5,58, deuda 0,00262, techo 175 | 120,6 / 111,8 | 1092 de 1092 | **SURVIVES** | sí |
| inferior / medio, aguda 5,58, deuda 0,0103, techo 150 | 123,5 / 113,8 | 1092 de 1092 | **SURVIVES** | sí |
| inferior / medio, aguda 5,58, deuda 0,0103, techo 175 | 128,5 / 115,1 | 1092 de 1092 | **SURVIVES** | sí |
| superior / superior, aguda 0,382, deuda 0,0103, techo 175 | 119,4 / 107,3 | 1092 de 1092 | **SURVIVES** | sí |
| superior / superior, aguda 1,46, deuda 0,00262, techo 150 | 119,5 / 109,5 | 1092 de 1092 | **SURVIVES** | sí |
| superior / superior, aguda 1,46, deuda 0,00262, techo 175 | 120,0 / 109,6 | 1092 de 1092 | **SURVIVES** | sí |
| superior / superior, aguda 1,46, deuda 0,0103, techo 150 | 128,3 / 113,2 | 1092 de 1092 | **SURVIVES** | sí |
<!-- /generado:filtro -->

## 6. Márgenes de cada regla

<!-- generado:margenes -->
Diagnóstico, sin cambiar ninguna regla: LOW / mediana / HIGH sobre todos los candidatos que entran (lpm).

| Magnitud | demanda 1,0 | demanda 1,1 |
|---|---|---|
| A: FC sin tratamiento a los 120, 57m | 144,20 / 150,11 / 157,62 | 126,92 / 139,07 / 153,13 |
| B: FC sin tratamiento a los 120, 72f | 129,47 / 133,31 / 136,85 | 114,39 / 129,77 / 146,23 |
| C: beneficio de la unidad 1 (sin − con), 57m | 10,03 / 11,52 / 13,20 | 2,83 / 9,18 / 34,83 |
| C: beneficio de la unidad 1 (sin − con), 72f | 10,56 / 11,34 / 11,62 | 3,24 / 12,43 / 36,52 |
| D: beneficio de la unidad 2 (sin − con), 57m | 12,37 / 12,94 / 13,48 | 2,95 / 9,71 / 32,08 |
| D: beneficio de la unidad 2 (sin − con), 72f | 0,00 / 0,00 / 0,00 | 0,00 / 0,00 / 0,00 |
| E: mayor subida entre 60, 90 y 120 (negativa = desciende), 57m | -2,62 / -2,56 / -2,50 | -16,44 / -3,57 / -0,76 |
| E: mayor subida entre 60, 90 y 120 (negativa = desciende), 72f | -0,32 / -0,32 / -0,30 | -1,90 / -0,42 / -0,10 |
| F: FC − intrínseca a los 120, 57m | 1,42 / 1,45 / 1,48 | 0,43 / 2,03 / 9,55 |
| F: FC − intrínseca a los 120, 72f | 0,17 / 0,18 / 0,18 | 0,06 / 0,24 / 1,08 |
<!-- /generado:margenes -->

## 7. Techo 200: sólo sensibilidad

<!-- generado:sensibilidad -->
- Demanda 1,0: ninguna combinación con techo 200 es compatible con la llegada.
- Demanda 1,1: 4 combinaciones con techo 200 (4368 candidatos); cumplirían A–F 4368 candidatos y 4 combinaciones. Estado `OUT_OF_PRIMARY_RANGE_SENSITIVITY_REFERENCE`: no entran en ningún resultado primario ni rescatan a nadie (rescata: no).
<!-- /generado:sensibilidad -->

## 8. Clasificación entre demandas (P2I-2AK-5)

<!-- generado:demanda_cruzada -->
| Clase | Combinaciones latentes primarias |
|---|---|
| ROBUST_ACROSS_DEMAND | 1 |
| DEMAND_1_0_ONLY | 1 |
| DEMAND_1_1_ONLY | 8 |
| DEMAND_INCOMPATIBLE | 440 |

Universo: 450 combinaciones primarias (9 pares de intrínseca × 25 ganancias × 2 techos). Diagnóstico, nunca filtro.

- ROBUST_ACROSS_DEMAND: superior / superior, aguda 1,46, deuda 0,0103, techo 150
- DEMAND_1_0_ONLY: superior / superior, aguda 1,46, deuda 0,0103, techo 175
- DEMAND_1_1_ONLY: inferior / medio, aguda 1,46, deuda 0,0407, techo 150
- DEMAND_1_1_ONLY: inferior / medio, aguda 1,46, deuda 0,0407, techo 175
- DEMAND_1_1_ONLY: inferior / medio, aguda 5,58, deuda 0,00262, techo 175
- DEMAND_1_1_ONLY: inferior / medio, aguda 5,58, deuda 0,0103, techo 150
- DEMAND_1_1_ONLY: inferior / medio, aguda 5,58, deuda 0,0103, techo 175
- DEMAND_1_1_ONLY: superior / superior, aguda 0,382, deuda 0,0103, techo 175
- DEMAND_1_1_ONLY: superior / superior, aguda 1,46, deuda 0,00262, techo 150
- DEMAND_1_1_ONLY: superior / superior, aguda 1,46, deuda 0,00262, techo 175
<!-- /generado:demanda_cruzada -->

## 9. Apoyo latente e identificabilidad (P2I-2AK-6)

<!-- generado:identificabilidad -->
| Latente | demanda 1,0 | demanda 1,1 | unión (suma por demanda) |
|---|---|---|---|
| intrínseca 57m | **POORLY_IDENTIFIED** (superior: 2) | **POORLY_IDENTIFIED** (inferior: 5, superior: 4) | **POORLY_IDENTIFIED** (inferior: 5, superior: 6) |
| intrínseca 72f | **POORLY_IDENTIFIED** (superior: 2) | **POORLY_IDENTIFIED** (medio: 5, superior: 4) | **POORLY_IDENTIFIED** (medio: 5, superior: 6) |
| ganancia aguda | **PARTIALLY_CONSTRAINED** (1,46: 2) | **POORLY_IDENTIFIED** (0,382: 1, 1,46: 5, 5,58: 3) | **POORLY_IDENTIFIED** (0,382: 1, 1,46: 7, 5,58: 3) |
| ganancia de deuda | **NON_IDENTIFIABLE** (0,0103: 2) | **NON_IDENTIFIABLE** (0,00262: 3, 0,0103: 4, 0,0407: 2) | **NON_IDENTIFIABLE** (0,00262: 3, 0,0103: 6, 0,0407: 2) |
| techo sinusal total | **POORLY_IDENTIFIED** (150: 1, 175: 1) | **POORLY_IDENTIFIED** (150: 4, 175: 5) | **POORLY_IDENTIFIED** (150: 5, 175: 6) |

En la unión, el apoyo suma las combinaciones que sobreviven en cada demanda: la combinación ROBUST_ACROSS_DEMAND cuenta dos veces.

Regla: P2I-2AJ's rule on the surviving latent HR combinations, with the primary ceiling grid 150 / 175: NON_IDENTIFIABLE for the debt gain (only gain x D reaches HR, the D scale unapproved); POORLY_IDENTIFIED when two or more grid values survive or the one survivor is an edge of the explored support; PARTIALLY_CONSTRAINED for one interior value bracketed by rejected neighbours while the point observations (the two arrival HRs; envelopes A-F are inequalities, not observations) are fewer than the latents; WELL_CONSTRAINED only with as many point observations as latents. A narrow grid survivor set is never called identification.
<!-- /generado:identificabilidad -->

## 10. Observables de los sobrevivientes (P2I-2AK-7)

<!-- generado:observables -->
LOW / mediana / HIGH sobre los candidatos sobrevivientes (sobreviviente de lactato × combinación latente).

| Observable | 57m, demanda 1,0 | 72f, demanda 1,0 | 57m, demanda 1,1 | 72f, demanda 1,1 |
|---|---|---|---|---|
| FC de llegada | 126,9 / 127,8 / 128,6 | 110,5 / 110,5 / 110,6 | 119,4 / 122,8 / 128,5 | 107,1 / 109,6 / 115,1 |
| sin tratamiento: FC a los 120 | 144,2 / 150,1 / 157,6 | 129,5 / 133,3 / 136,8 | 126,9 / 139,1 / 153,1 | 114,4 / 129,8 / 146,2 |
| beneficio contrafactual de la unidad 1 (lpm) | 10,0 / 11,5 / 13,2 | 10,6 / 11,3 / 11,6 | 2,8 / 9,2 / 34,8 | 3,2 / 12,4 / 36,5 |
| beneficio contrafactual de la unidad 2 (lpm) | 12,4 / 12,9 / 13,5 | 0,0 / 0,0 / 0,0 | 3,0 / 9,7 / 32,1 | 0,0 / 0,0 / 0,0 |
| manejo definitivo: FC a los 60 | 110,7 / 110,9 / 111,2 | 101,3 / 101,4 / 101,4 | 63,6 / 104,7 / 120,2 | 80,4 / 87,6 / 102,1 |
| manejo definitivo: FC a los 90 | 103,9 / 104,0 / 104,1 | 100,5 / 100,5 / 100,5 | 61,2 / 84,8 / 106,7 | 80,2 / 82,8 / 100,8 |
| manejo definitivo: FC a los 120 | 101,4 / 101,5 / 101,5 | 100,2 / 100,2 / 100,2 | 60,4 / 69,1 / 102,4 | 80,1 / 81,0 / 100,3 |
| taquicardia residual sobre la intrínseca a los 120 | 1,4 / 1,5 / 1,5 | 0,2 / 0,2 / 0,2 | 0,4 / 2,0 / 9,5 | 0,1 / 0,2 / 1,1 |
| FC máxima (L1, L2, L3) | 144,2 / 150,1 / 157,6 | 129,5 / 133,3 / 136,8 | 126,9 / 139,1 / 153,1 | 114,4 / 129,8 / 146,2 |
| uso de la reserva | 0,73 / 0,83 / 0,91 | 0,42 / 0,54 / 0,67 | 0,38 / 0,77 / 0,89 | 0,19 / 0,56 / 0,82 |
<!-- /generado:observables -->

## 11. 72f: cristaloide frente a GR (P2I-2AK-8)

<!-- generado:fluido -->
| 72f, L2 cristaloide frente a L3 GR, sobrevivientes | demanda 1,0 | demanda 1,1 |
|---|---|---|
| primer minuto con FC distinta | 1 / 1 / 1 | 1 / 1 / 1 |
| primer minuto con más de 1 lpm | 9 / 11 / 13 | 5 / 12 / 28 |
| mayor diferencia (lpm) | 17,6 / 20,2 / 25,4 | 10,2 / 38,4 / 54,4 |
| GR − cristaloide (lpm) | -25,4 / -20,2 / -17,6 | -54,4 / -38,4 / -10,2 |
| pares sin divergencia | 0 | 0 |
| primera entrada que diverge (aguda / deuda / ninguna) | 432 / 0 / 0 | 9828 / 0 / 0 |

Diagnóstico, sin filtro; no se exige que la FC distinga el líquido.
<!-- /generado:fluido -->

## 12. Validación contra el núcleo completo

<!-- generado:validacion -->
| Demanda | Unidades de muestra | Corridas completas | Comprobaciones | Exacta |
|---|---|---|---|---|
| 1,0 | 3 | 114 | arrival sí, comparator_haemostasis sí, comparator_prefix sí, comparator_units sí, hr sí, hr_observables sí, lactate_closure sí, lactate_unchanged_by_hr sí | **sí** |
| 1,1 | 3 | 378 | arrival sí, comparator_haemostasis sí, comparator_prefix sí, comparator_units sí, hr sí, hr_observables sí, lactate_closure sí, lactate_unchanged_by_hr sí | **sí** |
<!-- /generado:validacion -->

## 13. Presión, demanda, parámetros y no regresión (P2I-2AK-9, -10)

- **Presión:** sigue `PRESSURE_TERM_DIAGNOSTIC_ONLY`. Su ganancia es 0 en el perfil primario y en todas las
  relecturas de validación, y no rescata ni rechaza a nadie.
- **Demanda:** 1,0 y 1,1 siguen siendo CURRENTLY_COMPATIBLE, sin aprobar. 0,9 queda fuera del filtro primario.
- **Parámetros ocultos:** ninguno se aprueba. Quedan 10 combinaciones latentes primarias como incertidumbre.
- **Puerta de migración:** sin cambios. Qué FC vería el residente en el minuto 0 sigue en la puerta (TD-94, punto 2).
  No hay migración ni integración.
- **No regresión:**
  - El núcleo no cambia: no se tocó `clinical_core` fuera de este análisis y de dos tuplas de exclusión.
  - Las unidades de lactato de las dos demandas reproducen las de P2I-2AJ.
  - En las unidades de muestra, las corridas igualan a `lactate_closure.full_run` en lactato y D, y a
    `hr_observables.full_run` fila por fila: BloodState, gasto, DO2, déficit, D, lactato y FR.
  - La regla congelada del veredicto menciona también la igualdad con `hr_shock.full_run` con demanda 1,0. La validación
    del paquete no la comprueba. Se cumple por transitividad: P2I-2AJ comprobó `hr_observables.full_run` frente a
    `hr_shock.full_run`, y una prueba nueva lo comprueba directamente en una unidad (TD-97).
  - Las relecturas con el perfil de FC de cada candidato no cambian ni el lactato, ni D, ni la FR.

## 14. Veredicto (P2I-2AK-11)

<!-- generado:veredicto -->
**HR_OBSERVABLE_FILTER_SATISFIED**

| Comprobación | Resultado |
|---|---|
| al menos un candidato sobrevive con demanda 1,0 o 1,1 | sí |
| todos los sobrevivientes cumplen A–F (recomprobado) | sí |
| ganancias y techo comunes (por construcción) | sí |
| presión aplazada | sí |
| fisiología previa sin cambios | sí |
| sin contradicción estructural de la FC | sí |

Robustez entre demandas exigida: no. Aprobado: no.

Regla congelada: HR_OBSERVABLE_FILTER_SATISFIED when: (1) at least one candidate survives at demand 1.0 or 1.1 (else HR_OBSERVABLE_FILTER_EMPTY, for faculty review, nothing loosened or restored); (2) every final survivor satisfies A-F (re-checked); (3) the sympathetic gains and ceiling are common (one triple per combination, both cases); (4) the pressure contribution is 0 in the primary profile and every validation rerun; (5) the upstream physiology is unchanged (dependencies, lactate units and arrival surface reproduced; the runs equal lactate_closure.full_run and, at demand 1.0, hr_shock.full_run); (6) no structural HR contradiction (exact reconstruction; every sinus HR within [intrinsic, ceiling]). Cross-demand robustness is not required. Otherwise HR_OBSERVABLE_FILTER_NOT_READY with the first blocker. Nothing is approved.
<!-- /generado:veredicto -->

## 15. Recomendación: ¿presión o una decisión más de FC?

**Opción A: la FC está acotada lo suficiente para pasar a la presión y el tono vascular**, con tres salvedades.

1. Las envolventes no fueron activas: toda la región compatible con la llegada se comporta como la docencia pide. Las
   latentes siguen sin identificarse y se arrastran como incertidumbre (10 combinaciones, dos condiciones de demanda),
   sin elegir ninguna.
2. Para calibrar la presión no hace falta elegir la FC. En este núcleo la FC no llega al gasto, la entrega, D, el
   lactato ni la FR. Es la factorización de P2I-2AF: la validación de este paquete la comprueba para lactato, D y FR,
   y una prueba para el gasto, la entrega y el déficit en una unidad.
3. El término de presión sobre el impulso simpático está aplazado. Cuando se calibre la presión habrá que reabrir la
   superficie de la FC con ese término y repetir las mismas envolventes A–F como pruebas de no regresión.

Ninguna decisión adicional de FC bloquea el paso a la presión. Las del §16 son mejoras de discriminación, no requisitos.

## 16. Decisiones que necesita la docencia

Ninguna la toma el análisis, y ninguna bloquea el paso siguiente.

1. **Paso siguiente:** pasar a la presión y el tono vascular con la región de la FC como incertidumbre arrastrada
   (recomendación A), o pedir antes una decisión de FC.
2. **FC absoluta tras la reanimación:** F es relativa a la intrínseca, así que nada acota la FC absoluta. Con demanda
   1,1, 57m queda a los 120 entre 60 y 102 lpm según la intrínseca (60 o 100). ¿Hace falta un criterio sobre la FC
   absoluta, o sobre la plausibilidad de cada intrínseca, para estos pacientes?
3. **Segunda unidad de GR en 72f:** la FC no puede distinguirla, porque el déficit ya es cero. ¿Basta con que D se
   cumpla con beneficio 0, o la segunda unidad debe juzgarse con otro observable (Hb, lactato)?
4. **Demanda:** ¿se siguen arrastrando 1,0 y 1,1 como condiciones separadas?

Sigue detenido hasta una decisión expresa: la selección de latentes de la FC, la presión y el tono vascular, la FR, el
colapso, la migración y la integración.

## 17. Eficiencia

<!-- generado:eficiencia -->
Trayectorias hemodinámicas: 3178; descomposiciones de llegada analíticas: 900; corridas de fisiología del filtro (L1, L3 y los dos contrafactuales una vez por caso, conjunto P3 y punto): demanda 1,0: 144; demanda 1,1: 728; corridas de L2 y L3 para los sobrevivientes: demanda 1,0: 864; demanda 1,1: 4368; corridas de validación: 492; reconstrucciones de FC posprocesadas: demanda 1,0: 72; demanda 1,1: 1638; barrido cartesiano: no; motor heredado leído: no. La mitad de las corridas de sobrevivientes repite L3, que no depende del punto de cristaloide, y las reconstrucciones contadas son sólo las de techo primario (revisión adversarial, TD-97).
<!-- /generado:eficiencia -->
