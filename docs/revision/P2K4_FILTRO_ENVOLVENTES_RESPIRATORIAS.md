# P2K-4 · Filtro docente de envolventes observables de FR / ventilación

- **Fecha:** 2026-10-31. **Rama:** `phase-2-clinical-core-shadow`. **Base:** `ef2cfe8` (P2K-3, cerrado).
- **Congelamiento:** `46d009a` (digest `638b64f6…`), antes de calcular cualquier conteo de candidatos que entran, de
  rechazos o de supervivientes.
  - Antes de congelar sólo se probó la maquinaria:
    - con sangres sintéticas, fuera de la grilla clínica: el filtro por bitsets igual a la recomputación directa, 0
      discrepancias;
    - con la fisiología real, sólo hasta antes del filtro y imprimiendo sólo booleanos: P2K-3 reproducido, los
      comparadores nuevos iguales al núcleo y el emparejamiento de comparadores.
- **Números:** `docs/revision/P2K4_ventilation_filter.json`. Generador de los bloques:
  `python -m clinical_core.ventilation_filter_report`.
- **Alcance:** sólo sombra. Sin aprobar parámetros respiratorios ni la ganancia de ventilación, sin conciencia, sin
  colapso, sin migraciones, sin integración en tiempo de ejecución y sin ajuste a la FR heredada.

## Resumen

- **Qué se hizo.**
  - Se aplicaron las envolventes docentes A–I a todo el espacio de candidatos, sin muestrear: cada superviviente de
    P2J-3 (sangre, puntos del lado del lactato, conjunto de GR y punto de cristaloide, en su ganancia de tono y su
    demanda), cruzado con cada combinación latente respiratoria. Son 1620 combinaciones: ganancia ácido → FR, FR
    intrínseca de cada paciente, ganancia de ventilación 0,03–0,06, B y τ.
  - Las trayectorias son las factorizadas de P2K-3. Cada regla es una tabla sobre los factores que lee y se arma como
    bitset, sin simulación cartesiana.
  - Una recomputación independiente iguala al filtro bit a bit: 19 440 candidatos, 0 discrepancias.
- **Supervivientes.**
  - Demanda 1,0: sobreviven 165 480 de 860 220 candidatos.
  - Demanda 1,1: sobreviven 1 022 112 de 5 307 120.
  - En ambas demandas sobreviven las mismas 312 combinaciones latentes (ROBUST_ACROSS_DEMAND), y cada unidad aguas
    arriba conserva alguna.
- **Por qué se rechaza.**
  - Casi todo, por la FR de llegada, la misma prueba analítica de P2K-3 (9 de 45 combinaciones de FR).
  - Después, sólo I (FR residual a 120 tras la reanimación): 6372 y 39 312 candidatos.
  - A, únicamente con demanda 1,0: 192 candidatos.
  - Ningún candidato cae por la PaCO2 de llegada, C, D, H (PaCO2 ni pH), E, F ni la regla estructural.
- **Identificabilidad.**
  - La ganancia de ventilación queda NON_IDENTIFIABLE: sobreviven las cuatro por igual, porque C, D y H no las separan.
  - La FR intrínseca de cada paciente y la ganancia ácido → FR quedan POORLY_IDENTIFIED.
  - B queda POORLY_IDENTIFIED con demanda 1,0 y NON_IDENTIFIABLE con 1,1; τ, POORLY_IDENTIFIED.
  - Es incertidumbre explícita, aceptable según la docencia.
- **Contrafactuales.**
  - Ninguna lectura emparejada empeora a la vez la respiración y la perfusión.
  - El cristaloide y los GR mejoran ambas, o mejoran la perfusión con una señal respiratoria que no mejora: 3571 de
    103 680 lecturas con demanda 1,0 y 3176 de 329 400 con 1,1. En esas lecturas la carga es menor y el pH algo menor
    (hasta −0,010), efecto de la sobrecompensación (§13, punto 4).
  - En R4 de 72f la unidad 1 mejora la perfusión al completarse. A los 120 min y en los dos minutos de la unidad 2 el
    déficit ya es 0 y no hay cambio.
  - La FR y la PaCO2 siguen a la carga en cada lectura.
- **Acidemia extrema sin tratamiento.**
  - Sólo con demanda 1,1 y sólo en 57m: 17 604 de 1 022 112 supervivientes (1,7 %).
  - El pH mínimo es 6,96, a los 120 min, con carga 18,4 mEq/L, déficit 0,84, PaCO2 25,8 mmHg y FR 32–36.
  - Pasa a CONSCIOUSNESS_COLLAPSE_REVIEW; no filtra.
- **R3 / R4.**
  - En 634 pares, R3 y R4 convergen en lo respiratorio, en 20 pares (demanda 1,1) las salidas difieren, y no hay ningún
    colapso de escenario.
  - Debajo, los estados difieren donde deben: hemostasia en el minuto 60 frente a ninguna; sangrado a 120 de 2,0 frente
    a 0,25 mL/min; pérdida 240 frente a 133 mL; volumen, contenido eritrocitario, gasto y DO2 distintos; Hb casi igual
    (pérdida de sangre entera).
  - La convergencia es fisiológica. A los 120 min R4 no tiene déficit y R3 lo tiene nulo o pequeño: ≤ 0,034 en todos los
    pares que leen los supervivientes, y del orden de 0,002 en los que convergen, según la revisión. No queda producción
    ácida apreciable por déficit (§9, §15).
- **Previo intacto.**
  - P2J-3, P2K-1 y P2K-3 (reconstrucción, paquete A–I y validación) se reproducen exactamente.
  - Los comparadores nuevos igualan al núcleo en 18 corridas, con los siete dominios aguas arriba iguales.
  - Los archivos cerrados conservan sus bytes de `ef2cfe8`.
- **Veredicto: RR_VENTILATION_OBSERVABLE_FILTER_SATISFIED.** Recomendación (propuesta): MOVE_FORWARD hacia conciencia /
  respuesta neurológica, sin empezarla. Nada se aprueba.

## 1. Decisiones docentes registradas (generado)

<!-- generado:decisiones -->
- **P2K-3**: P2K-3 accepted and closed; RR_VENTILATION_DECISION_SURFACE_READY accepted
- **E · cristaloide**: E: P2J-3's matched comparator, R2 against R1 at P2J-3's minutes; only RESPIRATORY_AND_PERFUSION_WORSEN rejects; never judged from RR alone
- **fecha**: 2026-10-31
- **demanda en W**: BASELINE_RELATIVE: W is effective ventilation relative to the patient's baseline / current ventilatory requirement; demand 1.1 is not an absolute hypermetabolism with a new resting PaCO2; a modeling semantic decision, not an approval of demand 1.0 or 1.1
- **parada temprana**: an empty region or a causal contradiction STOPs; no widened envelope or tolerance, no new support value, no gain 0.08, no B / tau change, no legacy fitting, no hypoxaemic drive, no tidal-volume or fatigue state
- **criterio de salida**: a coherent non-empty region, no contradiction, intact upstream, structurally coherent RR / W / PaCO2 / pH and plausible counterfactuals bound the current GI respiratory domain: default MOVE_FORWARD; broad B, tau, intrinsic RR or gains never call for another respiratory package
- **objetivo**: bound the current respiratory candidate region with interpretable RR / PaCO2 / pH observables, keep the acid burden, drive, RR, W and PaCO2 separate, keep the latent uncertainty (no single set), and say whether the GI respiratory domain is bounded enough to move on
- **F · GR**: F: the red cells against matched trajectories omitting only the target exposure: R3 against R3 without the red cells; in R4 unit 1 and unit 2 each against L3 without it; never R3 against R4
- **prioridad del proyecto**: a coherent common physiology with explicit plausible uncertainty and no causal contradiction, good enough to migrate other families; not a tighter fit of two GI cases; a non-empty region is acceptable
- **R3 / R4**: similar R3 / R4 respiratory outputs at 120 are not a contradiction when neither has an effective deficit; the bleeding state, BloodState and chronology must differ where they should, else STOP
- **referencias y llegada**: HCO3 24, PaCO2 40 (COMMON_REFERENCE_PROVISIONAL); arrival RR 57m 26 +/- 3, 72f 24 +/- 3; arrival PaCO2 57m 31 +/- 3, 72f 33 +/- 3; arrival pH diagnostic only (same HCO3 and PaCO2)
- **alcance**: shadow only; no runtime integration, migration, parameter approval, consciousness, collapse or legacy fitting; the upstream physiology reused, never reopened
- **soporte latente**: P2K-3's primary support unchanged: intrinsic RR 12 / 16 / 20 per patient, the frozen drive gains, ventilation gain 0.03-0.06 (0.08 excluded: it failed the arrival PaCO2 windows), B 13.4 / 19.4 / 28, tau 60 / 120 / 240; no value FACULTY_APPROVED
- **pH sin tratamiento**: no untreated pH filter; its distribution reported; pH < 7.00 flagged UNTREATED_EXTREME_ACIDEMIA (diagnostic, CONSCIOUSNESS_COLLAPSE_REVIEW)
<!-- /generado:decisiones -->

## 2. Reglas congeladas (generado)

<!-- generado:reglas -->
| regla | qué exige |
|---|---|
| llegada | FR 57m 23–29, 72f 21–27; PaCO2 57m 28–34, 72f 30–36; pH sólo diagnóstico |
| A | R1 57m untreated, RR at 120 in 24-38 |
| B | R1 72f untreated, RR at 120 in 20-36; not required to be at or above the arrival RR |
| C | R1 57m untreated, PaCO2 at 120 in 18-35 |
| D | R1 72f untreated, PaCO2 at 120 in 22-38 |
| E | R2 against matched R1: no RESPIRATORY_AND_PERFUSION_WORSEN at the frozen minutes |
| F | red cells against matched no-PRBC trajectories: no PRBC_CAUSES_RESPIRATORY_AND_PERFUSION_WORSENING at the frozen minutes |
| G | R4 57m definitive, RR at 120 in 12-27 |
| G2 | R4 72f definitive, RR at 120 in 12-24 |
| H | R4 both cases, PaCO2 at 120 in 30-42 and pH at 120 in 7.35-7.45 |
| I | R4 at 120, RR - intrinsic RR in 0-12 (57m) and 0-10 (72f) |
| pH sin tratamiento | UNTREATED_EXTREME_ACIDEMIA: R1 pH below 7.00 at any minute 0-120 in either case; diagnostic, never a rejection; handed to CONSCIOUSNESS_COLLAPSE_REVIEW |

**Orden congelado:** estructural (SIMULATION) → FR de llegada → PaCO2 de llegada → A · FR R1 57m → B · FR R1 72f → G · FR R4 57m → G2 · FR R4 72f → H · PaCO2 R4 → H · pH R4 → I · FR residual R4 → C · PaCO2 R1 57m → D · PaCO2 R1 72f → E · cristaloide → F · GR.

**Comparadores:** Each comparator omits only the target exposure and keeps the blood set, the lactate-side point, the tone gain, the demand, the latent respiratory combination, the elapsed time, the bleeding chronology, the PPI and haemostasis timing. E is P2J-3's comparator (L2 against L1, the same blood set). F: R3 against R3's inputs without the red cells; in R4 each unit against L3 without it (P2J-3's CF1 / CF2). R3 is never compared with R4 as a red-cell counterfactual: that pair changes the haemostasis.

**Señal respiratoria:** At each comparison minute, delta = treated - matched comparator, the same latent combination. Perfusion improves when the effective deficit is lower, worsens when higher. The respiratory signal reads the acid burden and the compensation state together: it improves when the burden is lower and pH higher, worsens when the burden is higher and pH lower (a physiologically worse compensation), and is otherwise not improving. RR and PaCO2 are reported and checked to follow the burden at fixed latent parameters (RR never lower, PaCO2 never higher when the burden is higher); RR alone never classifies. A delta within 1e-9 of its scale is no change (P2J-3's rule). Only RESPIRATORY_AND_PERFUSION_WORSEN rejects (for the red cells named PRBC_CAUSES_RESPIRATORY_AND_PERFUSION_WORSENING: worse deficit + worse burden + lower pH), and a treated arrest while the comparator still breathes; a comparator arrest with the treated breathing is the treated doing better.

**Soporte latente:** B 13,4, 19,4, 28,0; ganancia ácido → FR 1,0, 1,4, 2,0, 2,8, 4,0; FR intrínseca 57m 12,0, 16,0, 20,0; FR intrínseca 72f 12,0, 16,0, 20,0; τ de aclaramiento ácido 60,0, 120,0, 240,0; ganancia ácido → ventilación 0,03, 0,04, 0,05, 0,06 (1 620 combinaciones); ganancia 0,08 excluida por la docencia.
<!-- /generado:reglas -->

## 3. Filtro por demanda (generado)

<!-- generado:filtro -->
**Demanda 1,0.** Entran 860 220 candidatos (531 supervivientes de P2J-3 × 1 620 combinaciones latentes, por tono: g 0,25 349 920, g 0,5 293 220, g 1,0 217 080); sobreviven **165 480** (g 0,25 67 200, g 0,5 56 472, g 1,0 41 808); 312 combinaciones latentes distintas; 531 de 531 unidades aguas arriba con algún superviviente.

| regla | primer fallo | cualquier fallo | fallo único |
|---|---|---|---|
| estructural (SIMULATION) | 0 | 0 | 0 |
| FR de llegada | 688 176 | 688 176 | 256 776 |
| PaCO2 de llegada | 0 | 0 | 0 |
| A · FR R1 57m | 192 | 213 420 | 192 |
| B · FR R1 72f | 0 | 154 296 | 0 |
| G · FR R4 57m | 0 | 105 120 | 0 |
| G2 · FR R4 72f | 0 | 114 696 | 0 |
| H · PaCO2 R4 | 0 | 0 | 0 |
| H · pH R4 | 0 | 0 | 0 |
| I · FR residual R4 | 6 372 | 57 348 | 6 372 |
| C · PaCO2 R1 57m | 0 | 0 | 0 |
| D · PaCO2 R1 72f | 0 | 0 | 0 |
| E · cristaloide | 0 | 0 | 0 |
| F · GR | 0 | 0 | 0 |

| clase de rechazo | primer fallo | cualquier fallo |
|---|---|---|
| simulación | 0 | 0 |
| FR de llegada | 688 176 | 688 176 |
| PaCO2 de llegada | 0 | 0 |
| envolvente de FR | 6 564 | 437 964 |
| envolvente de PaCO2 | 0 | 0 |
| envolvente de pH | 0 | 0 |
| dirección del tratamiento | 0 | 0 |

Pares de fallos más frecuentes: FR de llegada + A · FR R1 57m 213 228; FR de llegada + B · FR R1 72f 154 296; FR de llegada + G2 · FR R4 72f 114 696; FR de llegada + G · FR R4 57m 105 120; A · FR R1 57m + B · FR R1 72f 66 744; FR de llegada + I · FR residual R4 50 976; G · FR R4 57m + G2 · FR R4 72f 47 784; G2 · FR R4 72f + I · FR residual R4 38 232.

**Demanda 1,1.** Entran 5 307 120 candidatos (3 276 supervivientes de P2J-3 × 1 620 combinaciones latentes, por tono: g 0,25 1 769 040, g 0,5 1 769 040, g 1,0 1 769 040); sobreviven **1 022 112** (g 0,25 340 704, g 0,5 340 704, g 1,0 340 704); 312 combinaciones latentes distintas; 3 276 de 3 276 unidades aguas arriba con algún superviviente.

| regla | primer fallo | cualquier fallo | fallo único |
|---|---|---|---|
| estructural (SIMULATION) | 0 | 0 | 0 |
| FR de llegada | 4 245 696 | 4 245 696 | 1 712 640 |
| PaCO2 de llegada | 0 | 0 | 0 |
| A · FR R1 57m | 0 | 1 320 336 | 0 |
| B · FR R1 72f | 0 | 835 920 | 0 |
| G · FR R4 57m | 0 | 721 440 | 0 |
| G2 · FR R4 72f | 0 | 707 616 | 0 |
| H · PaCO2 R4 | 0 | 0 | 0 |
| H · pH R4 | 0 | 0 | 0 |
| I · FR residual R4 | 39 312 | 353 808 | 39 312 |
| C · PaCO2 R1 57m | 0 | 0 | 0 |
| D · PaCO2 R1 72f | 0 | 0 | 0 |
| E · cristaloide | 0 | 0 | 0 |
| F · GR | 0 | 0 | 0 |

| clase de rechazo | primer fallo | cualquier fallo |
|---|---|---|
| simulación | 0 | 0 |
| FR de llegada | 4 245 696 | 4 245 696 |
| PaCO2 de llegada | 0 | 0 |
| envolvente de FR | 39 312 | 2 572 368 |
| envolvente de PaCO2 | 0 | 0 |
| envolvente de pH | 0 | 0 |
| dirección del tratamiento | 0 | 0 |

Pares de fallos más frecuentes: FR de llegada + A · FR R1 57m 1 320 336; FR de llegada + B · FR R1 72f 835 920; FR de llegada + G · FR R4 57m 721 440; FR de llegada + G2 · FR R4 72f 707 616; A · FR R1 57m + B · FR R1 72f 369 840; G · FR R4 57m + G2 · FR R4 72f 318 912; FR de llegada + I · FR residual R4 314 496; A · FR R1 57m + G · FR R4 57m 259 776.
<!-- /generado:filtro -->

## 4. Clases entre demandas (generado)

<!-- generado:demanda -->
Diagnóstico, no criterio: sobre las 1 620 combinaciones latentes.

| clase | combinaciones | valores que aparecen |
|---|---|---|
| ROBUST_ACROSS_DEMAND (en ambas demandas) | 312 | B 13,4, 19,4, 28,0; ganancia ácido → FR 1,0, 1,4, 2,0, 2,8, 4,0; FR intrínseca 57m 12,0, 16,0, 20,0; FR intrínseca 72f 12,0, 16,0, 20,0; τ de aclaramiento ácido 60,0, 120,0, 240,0; ganancia ácido → ventilación 0,03, 0,04, 0,05, 0,06 |
| DEMAND_1_0_ONLY (sólo con demanda 1,0) | 0 | — |
| DEMAND_1_1_ONLY (sólo con demanda 1,1) | 0 | — |
| DEMAND_INCOMPATIBLE (en ninguna) | 1 308 | B 13,4, 19,4, 28,0; ganancia ácido → FR 1,0, 1,4, 2,0, 2,8, 4,0; FR intrínseca 57m 12,0, 16,0, 20,0; FR intrínseca 72f 12,0, 16,0, 20,0; τ de aclaramiento ácido 60,0, 120,0, 240,0; ganancia ácido → ventilación 0,03, 0,04, 0,05, 0,06 |
<!-- /generado:demanda -->

## 5. Soporte latente e identificabilidad (generado)

<!-- generado:latentes -->
| parámetro | demanda | clase | valores que sobreviven | combinaciones por valor |
|---|---|---|---|---|
| B | 1,0 | POORLY_IDENTIFIED | 13,4, 19,4, 28,0 | 13,4: 104, 19,4: 104, 28: 104 |
| ganancia ácido → FR | 1,0 | POORLY_IDENTIFIED | 1,0, 1,4, 2,0, 2,8, 4,0 | 1: 36, 1,41421: 144, 2: 36, 2,82843: 72, 4: 24 |
| FR intrínseca 57m | 1,0 | POORLY_IDENTIFIED | 12,0, 16,0, 20,0 | 12: 96, 16: 108, 20: 108 |
| FR intrínseca 72f | 1,0 | POORLY_IDENTIFIED | 12,0, 16,0, 20,0 | 12: 60, 16: 144, 20: 108 |
| τ de aclaramiento ácido | 1,0 | POORLY_IDENTIFIED | 60,0, 120,0, 240,0 | 120: 108, 240: 96, 60: 108 |
| ganancia ácido → ventilación | 1,0 | NON_IDENTIFIABLE | 0,03, 0,04, 0,05, 0,06 | 0,03: 78, 0,04: 78, 0,05: 78, 0,06: 78 |
| B | 1,1 | NON_IDENTIFIABLE | 13,4, 19,4, 28,0 | 13,4: 104, 19,4: 104, 28: 104 |
| ganancia ácido → FR | 1,1 | POORLY_IDENTIFIED | 1,0, 1,4, 2,0, 2,8, 4,0 | 1: 36, 1,41421: 144, 2: 36, 2,82843: 72, 4: 24 |
| FR intrínseca 57m | 1,1 | POORLY_IDENTIFIED | 12,0, 16,0, 20,0 | 12: 96, 16: 108, 20: 108 |
| FR intrínseca 72f | 1,1 | POORLY_IDENTIFIED | 12,0, 16,0, 20,0 | 12: 60, 16: 144, 20: 108 |
| τ de aclaramiento ácido | 1,1 | POORLY_IDENTIFIED | 60,0, 120,0, 240,0 | 120: 108, 240: 96, 60: 108 |
| ganancia ácido → ventilación | 1,1 | NON_IDENTIFIABLE | 0,03, 0,04, 0,05, 0,06 | 0,03: 78, 0,04: 78, 0,05: 78, 0,06: 78 |

Per demand, on the survivors: NON_IDENTIFIABLE when no candidate survives, or when the filter does not read the parameter (for every upstream unit, every combination of the other parameters survives at all its values or at none); WELL_CONSTRAINED when one value survives; PARTIALLY_CONSTRAINED when some but not all do; POORLY_IDENTIFIED when all survive although the filter reads it (trade-offs). No best combination is selected.
<!-- /generado:latentes -->

## 6. Observables de los supervivientes (generado)

<!-- generado:observables -->
Bajo / mediana / alto sobre los supervivientes (entradas únicas: trayectoria × subcombinación latente que el observable lee).

| observable | demanda | 57m | 72f |
|---|---|---|---|
| FR de llegada | 1,0 | 26,1 [23,9–28,4] | 23,9 [21,3–25,5] |
| PaCO2 de llegada | 1,0 | 30,8 [28,5–33,3] | 33,7 [31,9–35,5] |
| pH de llegada (diagnóstico) | 1,0 | 7,373 [7,338–7,406] | 7,393 [7,369–7,415] |
| FR a 120 · R1 | 1,0 | 28,9 [24,0–35,1] | 25,4 [20,9–32,8] |
| PaCO2 a 120 · R1 | 1,0 | 28,2 [20,4–33,2] | 32,1 [25,2–35,8] |
| pH a 120 · R1 | 1,0 | 7,333 [7,094–7,405] | 7,382 [7,284–7,415] |
| pH mínimo 0–120 · R1 | 1,0 | 7,333 [7,094–7,405] | 7,382 [7,284–7,415] |
| FR a 120 · R4 | 1,0 | 21,4 [15,0–25,7] | 19,2 [13,6–23,4] |
| PaCO2 a 120 · R4 | 1,0 | 35,5 [31,3–38,7] | 37,3 [34,6–39,3] |
| pH a 120 · R4 | 1,0 | 7,399 [7,365–7,415] | 7,402 [7,384–7,414] |
| FR − intrínseca a 120 · R4 | 1,0 | 4,1 [1,1–10,2] | 2,4 [0,6–6,4] |
| FR de llegada | 1,1 | 26,1 [23,9–28,4] | 23,9 [21,3–25,5] |
| PaCO2 de llegada | 1,1 | 30,8 [28,5–33,3] | 33,7 [31,9–35,5] |
| pH de llegada (diagnóstico) | 1,1 | 7,373 [7,338–7,406] | 7,393 [7,369–7,415] |
| FR a 120 · R1 | 1,1 | 29,8 [24,5–36,2] | 26,4 [21,6–34,7] |
| PaCO2 a 120 · R1 | 1,1 | 27,4 [19,0–32,8] | 31,1 [23,2–35,3] |
| pH a 120 · R1 | 1,1 | 7,316 [6,961–7,401] | 7,371 [7,230–7,415] |
| pH mínimo 0–120 · R1 | 1,1 | 7,316 [6,961–7,401] | 7,371 [7,230–7,415] |
| FR a 120 · R4 | 1,1 | 21,8 [15,3–26,3] | 19,4 [13,7–23,6] |
| PaCO2 a 120 · R4 | 1,1 | 35,2 [30,6–38,5] | 37,2 [34,3–39,3] |
| pH a 120 · R4 | 1,1 | 7,398 [7,359–7,415] | 7,402 [7,382–7,415] |
| FR − intrínseca a 120 · R4 | 1,1 | 4,6 [1,2–11,5] | 2,5 [0,6–6,7] |
<!-- /generado:observables -->

## 7. Contrafactuales E y F (generado)

<!-- generado:contrafactuales -->
**Demanda 1,0.**

| comparación | minuto | caso | clases | Δ carga | Δ FR | Δ PaCO2 | Δ pH | Δ déficit |
|---|---|---|---|---|---|---|---|---|
| E · cristaloide (R2 frente a R1) | cristaloide completo | 57m | mejoran respiración y perfusión 19 116 | −0,38 [−1,18–−0,10] | −0,41 [−1,41–−0,08] | 0,38 [0,09–1,33] | 0,0036 [0,0006–0,0188] | −0,228 [−0,261–−0,180] |
| E · cristaloide (R2 frente a R1) | cristaloide completo | 72f | mejoran respiración y perfusión 18 312; mejora la perfusión, la señal respiratoria no 804 | −0,32 [−1,07–−0,08] | −0,46 [−2,29–−0,07] | 0,40 [0,08–1,68] | 0,0013 [−0,0003–0,0106] | −0,189 [−0,210–−0,146] |
| E · cristaloide (R2 frente a R1) | 120 | 57m | mejoran respiración y perfusión 19 116 | −2,42 [−6,45–−0,67] | −2,34 [−4,79–−0,51] | 2,27 [0,56–5,11] | 0,0310 [0,0040–0,1961] | −0,218 [−0,277–−0,099] |
| E · cristaloide (R2 frente a R1) | 120 | 72f | mejoran respiración y perfusión 18 073; mejora la perfusión, la señal respiratoria no 1 043 | −2,14 [−5,91–−0,56] | −2,92 [−8,60–−0,48] | 2,59 [0,54–7,32] | 0,0122 [−0,0028–0,0874] | −0,198 [−0,253–−0,085] |
| F · GR sin hemostasia (R3 frente a R3 sin GR) | unidad 1 completa | 57m | mejoran respiración y perfusión 1 944 | −0,93 [−2,74–−0,29] | −1,04 [−3,33–−0,23] | 0,98 [0,25–3,14] | 0,0087 [0,0017–0,0432] | −0,428 [−0,468–−0,382] |
| F · GR sin hemostasia (R3 frente a R3 sin GR) | unidad 1 completa | 72f | mejoran respiración y perfusión 1 770; mejora la perfusión, la señal respiratoria no 174 | −0,67 [−1,84–−0,22] | −0,98 [−4,09–−0,19] | 0,83 [0,21–2,96] | 0,0025 [−0,0011–0,0178] | −0,211 [−0,222–−0,194] |
| F · GR sin hemostasia (R3 frente a R3 sin GR) | unidad 2 completa | 57m | mejoran respiración y perfusión 1 944 | −2,82 [−7,24–−0,99] | −3,22 [−9,48–−0,78] | 3,00 [0,85–8,58] | 0,0232 [0,0050–0,1140] | −0,524 [−0,535–−0,491] |
| F · GR sin hemostasia (R3 frente a R3 sin GR) | unidad 2 completa | 72f | mejoran respiración y perfusión 1 622; mejora la perfusión, la señal respiratoria no 322 | −1,55 [−3,98–−0,53] | −2,26 [−9,01–−0,46] | 1,96 [0,52–6,48] | 0,0055 [−0,0045–0,0385] | −0,272 [−0,292–−0,237] |
| F · GR sin hemostasia (R3 frente a R3 sin GR) | 120 | 57m | mejoran respiración y perfusión 1 944 | −6,09 [−13,48–−2,36] | −6,98 [−17,80–−1,89] | 6,41 [2,09–15,83] | 0,0496 [0,0045–0,2504] | −0,645 [−0,664–−0,577] |
| F · GR sin hemostasia (R3 frente a R3 sin GR) | 120 | 72f | mejoran respiración y perfusión 1 634; mejora la perfusión, la señal respiratoria no 310 | −3,39 [−8,03–−1,25] | −5,07 [−16,40–−1,10] | 4,46 [1,25–12,24] | 0,0128 [−0,0101–0,0905] | −0,393 [−0,426–−0,320] |
| F · unidad 1 en R4 (frente a L3 sin ella) | unidad 1 completa | 57m | mejoran respiración y perfusión 1 944 | −0,93 [−2,74–−0,29] | −1,04 [−3,33–−0,23] | 0,98 [0,25–3,14] | 0,0087 [0,0017–0,0432] | −0,428 [−0,468–−0,382] |
| F · unidad 1 en R4 (frente a L3 sin ella) | unidad 1 completa | 72f | mejoran respiración y perfusión 1 770; mejora la perfusión, la señal respiratoria no 174 | −0,67 [−1,84–−0,22] | −0,98 [−4,09–−0,19] | 0,83 [0,21–2,96] | 0,0025 [−0,0011–0,0178] | −0,211 [−0,222–−0,194] |
| F · unidad 1 en R4 (frente a L3 sin ella) | 120 | 57m | mejoran respiración y perfusión 1 668; mejora la perfusión, la señal respiratoria no 276 | −1,67 [−3,59–−0,70] | −2,24 [−8,67–−0,58] | 2,15 [0,65–6,09] | 0,0071 [−0,0062–0,0326] | −0,096 [−0,118–−0,057] |
| F · unidad 1 en R4 (frente a L3 sin ella) | 120 | 72f | sin cambio de perfusión 1 944 | −0,40 [−0,66–−0,21] | −0,68 [−2,04–−0,19] | 0,60 [0,22–1,28] | 0,0006 [−0,0035–0,0049] | 0,000 |
| F · unidad 2 en R4 (frente a L3 sin ella) | unidad 2 completa | 57m | mejoran respiración y perfusión 1 863; mejora la perfusión, la señal respiratoria no 81 | −0,20 [−0,91–−0,03] | −0,26 [−1,78–−0,02] | 0,24 [0,02–1,36] | 0,0012 [−0,0003–0,0098] | −0,088 [−0,109–−0,046] |
| F · unidad 2 en R4 (frente a L3 sin ella) | unidad 2 completa | 72f | sin cambio de perfusión 1 944 | 0,00 | 0,00 | 0,00 | 0,0000 | 0,000 |
| F · unidad 2 en R4 (frente a L3 sin ella) | 120 | 57m | mejoran respiración y perfusión 1 557; mejora la perfusión, la señal respiratoria no 387 | −0,77 [−2,39–−0,18] | −1,13 [−6,31–−0,15] | 1,03 [0,17–4,29] | 0,0027 [−0,0055–0,0198] | −0,103 [−0,122–−0,061] |
| F · unidad 2 en R4 (frente a L3 sin ella) | 120 | 72f | sin cambio de perfusión 1 944 | 0,00 | 0,00 | 0,00 | 0,0000 | 0,000 |

La FR y la PaCO2 siguen a la carga en cada lectura: la PaCO2 sigue a la carga 103 680 de 103 680; la FR sigue a la carga 159 778 de 159 778.

**Demanda 1,1.**

| comparación | minuto | caso | clases | Δ carga | Δ FR | Δ PaCO2 | Δ pH | Δ déficit |
|---|---|---|---|---|---|---|---|---|
| E · cristaloide (R2 frente a R1) | cristaloide completo | 57m | mejoran respiración y perfusión 47 952 | −0,36 [−1,27–−0,09] | −0,39 [−1,40–−0,07] | 0,35 [0,08–1,35] | 0,0037 [0,0006–0,0221] | −0,221 [−0,287–−0,159] |
| E · cristaloide (R2 frente a R1) | cristaloide completo | 72f | mejoran respiración y perfusión 47 952 | −0,30 [−1,20–−0,07] | −0,44 [−2,30–−0,06] | 0,38 [0,07–1,77] | 0,0015 [0,0001–0,0132] | −0,185 [−0,271–−0,119] |
| E · cristaloide (R2 frente a R1) | 120 | 57m | mejoran respiración y perfusión 47 952 | −2,28 [−7,07–−0,61] | −2,01 [−4,38–−0,46] | 2,03 [0,50–4,81] | 0,0358 [0,0044–0,2885] | −0,196 [−0,293–−0,094] |
| E · cristaloide (R2 frente a R1) | 120 | 72f | mejoran respiración y perfusión 47 952 | −2,04 [−6,75–−0,48] | −2,58 [−7,31–−0,40] | 2,32 [0,45–7,12] | 0,0162 [0,0006–0,1248] | −0,180 [−0,279–−0,077] |
| F · GR sin hemostasia (R3 frente a R3 sin GR) | unidad 1 completa | 57m | mejoran respiración y perfusión 9 828 | −0,85 [−2,67–−0,25] | −0,91 [−2,85–−0,19] | 0,85 [0,21–2,79] | 0,0087 [0,0016–0,0481] | −0,389 [−0,465–−0,323] |
| F · GR sin hemostasia (R3 frente a R3 sin GR) | unidad 1 completa | 72f | mejoran respiración y perfusión 9 555; mejora la perfusión, la señal respiratoria no 273 | −0,86 [−2,51–−0,27] | −1,23 [−4,96–−0,23] | 1,05 [0,26–3,76] | 0,0039 [−0,0006–0,0270] | −0,310 [−0,319–−0,293] |
| F · GR sin hemostasia (R3 frente a R3 sin GR) | unidad 2 completa | 57m | mejoran respiración y perfusión 9 828 | −3,00 [−8,16–−0,98] | −3,27 [−9,01–−0,76] | 3,04 [0,83–8,73] | 0,0291 [0,0056–0,1514] | −0,618 [−0,634–−0,587] |
| F · GR sin hemostasia (R3 frente a R3 sin GR) | unidad 2 completa | 72f | mejoran respiración y perfusión 9 143; mejora la perfusión, la señal respiratoria no 685 | −2,12 [−5,45–−0,73] | −2,97 [−10,68–−0,63] | 2,57 [0,71–8,13] | 0,0088 [−0,0037–0,0609] | −0,368 [−0,388–−0,334] |
| F · GR sin hemostasia (R3 frente a R3 sin GR) | 120 | 57m | mejoran respiración y perfusión 9 828 | −6,74 [−15,55–−2,63] | −7,55 [−17,58–−2,08] | 6,89 [2,29–16,70] | 0,0649 [0,0124–0,3581] | −0,734 [−0,761–−0,644] |
| F · GR sin hemostasia (R3 frente a R3 sin GR) | 120 | 72f | mejoran respiración y perfusión 9 002; mejora la perfusión, la señal respiratoria no 826 | −4,22 [−10,24–−1,70] | −6,29 [−18,00–−1,48] | 5,51 [1,67–14,24] | 0,0207 [−0,0085–0,1374] | −0,486 [−0,519–−0,415] |
| F · unidad 1 en R4 (frente a L3 sin ella) | unidad 1 completa | 57m | mejoran respiración y perfusión 9 828 | −0,85 [−2,67–−0,25] | −0,91 [−2,85–−0,19] | 0,85 [0,21–2,79] | 0,0087 [0,0016–0,0481] | −0,389 [−0,465–−0,323] |
| F · unidad 1 en R4 (frente a L3 sin ella) | unidad 1 completa | 72f | mejoran respiración y perfusión 9 555; mejora la perfusión, la señal respiratoria no 273 | −0,86 [−2,51–−0,27] | −1,23 [−4,96–−0,23] | 1,05 [0,26–3,76] | 0,0039 [−0,0006–0,0270] | −0,310 [−0,319–−0,293] |
| F · unidad 1 en R4 (frente a L3 sin ella) | 120 | 57m | mejoran respiración y perfusión 9 356; mejora la perfusión, la señal respiratoria no 472 | −2,78 [−6,61–−1,14] | −3,56 [−11,71–−0,93] | 3,37 [1,03–9,27] | 0,0166 [−0,0061–0,0815] | −0,224 [−0,280–−0,168] |
| F · unidad 1 en R4 (frente a L3 sin ella) | 120 | 72f | sin cambio de perfusión 9 828 | −0,66 [−1,07–−0,34] | −1,06 [−3,26–−0,31] | 0,93 [0,35–2,07] | 0,0011 [−0,0051–0,0084] | 0,000 |
| F · unidad 2 en R4 (frente a L3 sin ella) | unidad 2 completa | 57m | mejoran respiración y perfusión 9 828 | −0,64 [−1,92–−0,18] | −0,76 [−2,85–−0,15] | 0,70 [0,16–2,43] | 0,0046 [0,0001–0,0268] | −0,217 [−0,272–−0,158] |
| F · unidad 2 en R4 (frente a L3 sin ella) | unidad 2 completa | 72f | sin cambio de perfusión 9 828 | 0,00 | 0,00 | 0,00 | 0,0000 | 0,000 |
| F · unidad 2 en R4 (frente a L3 sin ella) | 120 | 57m | mejoran respiración y perfusión 9 181; mejora la perfusión, la señal respiratoria no 647 | −2,01 [−5,65–−0,63] | −2,69 [−10,67–−0,52] | 2,45 [0,58–8,24] | 0,0103 [−0,0058–0,0652] | −0,230 [−0,285–−0,172] |
| F · unidad 2 en R4 (frente a L3 sin ella) | 120 | 72f | sin cambio de perfusión 9 828 | 0,00 | 0,00 | 0,00 | 0,0000 | 0,000 |

La FR y la PaCO2 siguen a la carga en cada lectura: la PaCO2 sigue a la carga 329 400 de 329 400; la FR sigue a la carga 507 825 de 507 825.
<!-- /generado:contrafactuales -->

## 8. Acidemia extrema sin tratamiento (generado)

<!-- generado:acidemia -->
- **Demanda 1,0:** 0 de 165 480 supervivientes (0,0 %) con pH sin tratamiento < 7,00 en algún minuto 0–120 (57m 0, 72f 0).
  - pH mínimo 7,094 (57m, minuto 120): carga 16,00 mEq/L, déficit efectivo 0,737, PaCO2 27,0 mmHg, FR 33,5 [30,9–35,1] rpm.
- **Demanda 1,1:** 17 604 de 1 022 112 supervivientes (1,7 %) con pH sin tratamiento < 7,00 en algún minuto 0–120 (57m 17 604, 72f 0).
  - pH mínimo 6,961 (57m, minuto 120): carga 18,38 mEq/L, déficit efectivo 0,835, PaCO2 25,8 mmHg, FR 34,6 [32,2–36,2] rpm; marcado CONSCIOUSNESS_COLLAPSE_REVIEW.
- Diagnóstico, nunca un rechazo (decisión docente): pasa a CONSCIOUSNESS_COLLAPSE_REVIEW.
<!-- /generado:acidemia -->

## 9. R3 / R4 (generado)

<!-- generado:r3r4 -->
- **Demanda 1,0:** convergencia respiratoria fisiológica 108; salidas respiratorias distintas 0; colapso de escenario (STOP) 0 pares.
  - 57m (conjunto de GR 1): hemostasia R3 ninguna, R4 minuto 60; sangrado a 120 2,00 frente a 0,25 mL/min; pérdida acumulada 240 frente a 133 mL; volumen circulante 360 frente a 467 mL; contenido eritrocitario 1,440 frente a 1,486; Hb 8,6140 frente a 8,6140; gasto 1,492 frente a 1,584; DO2 relativa 1,918 frente a 2,036; déficit 0,000 frente a 0,000 (máxima diferencia 0–120 0,000); misma cronología de GR y cristaloide: sí. Diferencias respiratorias máximas a 120: carga 0,000, FR 0,00, W 0,000, PaCO2 0,00, pH 0,0000. Clase: convergencia respiratoria fisiológica.
  - 57m (conjunto de GR 13): hemostasia R3 ninguna, R4 minuto 60; sangrado a 120 2,00 frente a 0,25 mL/min; pérdida acumulada 240 frente a 133 mL; volumen circulante 360 frente a 467 mL; contenido eritrocitario 1,440 frente a 1,486; Hb 8,6140 frente a 8,6140; gasto 1,492 frente a 1,584; DO2 relativa 1,918 frente a 2,036; déficit 0,000 frente a 0,000 (máxima diferencia 0–120 0,000); misma cronología de GR y cristaloide: sí. Diferencias respiratorias máximas a 120: carga 0,000, FR 0,00, W 0,000, PaCO2 0,00, pH 0,0000. Clase: convergencia respiratoria fisiológica.
- **Demanda 1,1:** convergencia respiratoria fisiológica 526; salidas respiratorias distintas 20; colapso de escenario (STOP) 0 pares.
  - 57m (conjunto de GR 1): hemostasia R3 ninguna, R4 minuto 60; sangrado a 120 2,00 frente a 0,25 mL/min; pérdida acumulada 240 frente a 133 mL; volumen circulante 360 frente a 467 mL; contenido eritrocitario 1,440 frente a 1,486; Hb 8,6140 frente a 8,6140; gasto 1,497 frente a 1,589; DO2 relativa 1,925 frente a 2,043; déficit 0,000 frente a 0,000 (máxima diferencia 0–120 0,000); misma cronología de GR y cristaloide: sí. Diferencias respiratorias máximas a 120: carga 0,000, FR 0,00, W 0,000, PaCO2 0,00, pH 0,0000. Clase: convergencia respiratoria fisiológica.
  - 57m (conjunto de GR 10): hemostasia R3 ninguna, R4 minuto 60; sangrado a 120 2,00 frente a 0,25 mL/min; pérdida acumulada 240 frente a 133 mL; volumen circulante 260 frente a 367 mL; contenido eritrocitario 1,400 frente a 1,446; Hb 8,6322 frente a 8,6321; gasto 1,392 frente a 1,503; DO2 relativa 1,794 frente a 1,937; déficit 0,024 frente a 0,000 (máxima diferencia 0–120 0,024); misma cronología de GR y cristaloide: sí. Diferencias respiratorias máximas a 120: carga 0,062, FR 0,18, W 0,004, PaCO2 0,12, pH 0,0005. Clase: salidas respiratorias distintas.
- For every surviving (tone gain, demand, case, red-cell set, lactate-side level), R3 (L3 without haemostasis) and R4 (L3) are compared at 120. Underlying: the haemostasis minute, the active bleed rate and the cumulative blood loss, the circulating volume and red-cell content of the core's BloodState, Hb, output and delivery, the effective deficit; the red-cell and crystalloid chronology must be the same. Respiratory: burden, RR, W, PaCO2 and pH over the pair's surviving latent combinations. SCENARIO_STATE_COLLAPSE_BUG (a STOP) when the bleeding state or the BloodState does not differ or the chronology differs beyond the haemostasis; otherwise PHYSIOLOGICAL_RESPIRATORY_CONVERGENCE when the respiratory outputs are within R3R4_NEAR, else RESPIRATORY_OUTPUTS_DISTINCT. Respiratory identity is never required to differ by treatment identity.
<!-- /generado:r3r4 -->

## 10. No regresión (generado)

<!-- generado:no_regresion -->
| comprobación | resultado |
|---|---|
| `clinical_core/acid_base.py` con su huella de `ef2cfe8` | sí |
| `clinical_core/derived.py` con su huella de `ef2cfe8` | sí |
| `clinical_core/integration.py` con su huella de `ef2cfe8` | sí |
| `clinical_core/state.py` con su huella de `ef2cfe8` | sí |
| `clinical_core/ventilation.py` con su huella de `ef2cfe8` | sí |
| `clinical_core/ventilation_surface.py` con su huella de `ef2cfe8` | sí |
| paquete A–I de P2K-3: se reproduce igual a su registro | sí |
| región de P2J-3: se reproduce igual a su registro | sí |
| P2K-1: se reproduce igual a su registro | sí |
| plausibilidad de P2K-3: se reproduce igual a su registro | sí |
| reconstrucción R1–R4 de P2K-3: se reproduce igual a su registro | sí |
| rechazos de P2K-3: se reproduce igual a su registro | sí |
| validación de P2K-3 contra el núcleo (96 corridas): se reproduce igual a su registro | sí |
| comparadores nuevos (CF1, CF2, R3 sin GR) = núcleo, 18 corridas con y sin la candidata | sí (diferencia máxima 0,000) |
| D: filas y estados iguales con y sin la candidata | sí |
| BloodState: filas y estados iguales con y sin la candidata | sí |
| DO2 / déficit efectivo: filas y estados iguales con y sin la candidata | sí |
| FC / barorreflejo: filas y estados iguales con y sin la candidata | sí |
| lactato: filas y estados iguales con y sin la candidata | sí |
| gasto: filas y estados iguales con y sin la candidata | sí |
| presión / tono: filas y estados iguales con y sin la candidata | sí |
| cada comparador omite sólo su exposición (1 434 pares) | sí |
| recomputación directa = filtro (19 440 candidatos, 12 unidades) | sí (0 discrepancias) |
<!-- /generado:no_regresion -->

## 11. Veredicto y recomendación (generado)

<!-- generado:veredicto -->
**RR_VENTILATION_OBSERVABLE_FILTER_SATISFIED**

| criterio | se cumple |
|---|---|
| fisiología previa intacta (P2J-3, P2K-1, P2K-3, comparadores = núcleo) | sí |
| cada comparador omite sólo su exposición | sí |
| sobrevive al menos un candidato | sí |
| la recomputación directa iguala al filtro | sí |
| los observables de los supervivientes cumplen A–I | sí |
| FR y PaCO2 de llegada en sus ventanas | sí |
| pH coherente (6,8–7,8; banco ± 0,005) | sí |
| respuestas a los tratamientos coherentes | sí |
| R3 / R4: convergencia fisiológica, sin colapso | sí |
| nada aprobado | sí |

**Recomendación (propuesta, no decisión): MOVE_FORWARD.** CONSCIOUSNESS / NEUROLOGIC RESPONSE (not begun)
- cross demand: the demand question (diagnostic)
- latent: explicit uncertainty; no respiratory package for identifiability alone
- untreated extreme acidemia: CONSCIOUSNESS_COLLAPSE_REVIEW

Aprobaciones: none FACULTY_APPROVED. MIGRATION_GATE_CLOSED: no runtime integration, GI or second-family migration or parameter approval is authorized; consciousness and collapse are not calibrated.
<!-- /generado:veredicto -->

## 12. Eficiencia (generado)

<!-- generado:eficiencia -->
Región de P2J-3 recalculada: 1 326 trayectorias de sangre y 364 contrafactuales; 182 corridas nuevas de R3 sin GR; 364 estados de R3 / R4; 36 corridas del núcleo para validar los comparadores y 96 para reproducir la validación de P2K-3. 6 167 340 candidatos evaluados como bitsets (14 reglas por 3 807 unidades aguas arriba × 1 620 combinaciones), sin simular ninguno; 19 440 recalculados por la vía directa. Barrido cartesiano: no; FR heredada leída: no.
<!-- /generado:eficiencia -->

## 13. Lo que se pide a la docencia

Ninguna de estas decisiones la toma la IA. Todo valor sigue EXPLORATORY o PROVISIONAL.

1. **Seguir adelante.**
   - La recomendación predeclarada es MOVE_FORWARD: con estas envolventes, el dominio respiratorio GI queda acotado
     para los casos actuales.
   - Falta confirmar si la próxima etapa es conciencia / respuesta neurológica.
2. **Acidemia extrema sin tratamiento** (57m con demanda 1,1, pH mínimo 6,96): se entrega a CONSCIOUSNESS_COLLAPSE_REVIEW.
   Falta decidir cómo se trata en conciencia o colapso. Aquí no se filtra.
3. **Ganancia de ventilación.** Las cuatro (0,03–0,06) sobreviven por igual, porque C, D y H no la separan. Sigue
   EXPLORATORY: no se propone ningún valor ni hace falta otro paquete respiratorio para elegirlo.
4. **Monotonía de la compensación (hallazgo de P2K-4, TD-105).**
   - Con la referencia HCO3 24, el mapeo lineal de P2K-3 sólo da un pH que baja con la carga si la ganancia de
     ventilación es ≤ 1/24 ≈ 0,042.
   - Con 0,05 el pH sube con la carga por debajo de 2,0 mEq/L (máximo 7,405); con 0,06, por debajo de 3,7 mEq/L
     (máximo 7,415), y sigue sobre 7,40 aun con la carga de llegada de 57m.
   - Eso es una compensación respiratoria mayor que la completa a cargas bajas. Aquí aparece como lecturas emparejadas
     en las que la menor carga va con un pH algo más bajo: hasta 0,010, clase «mejora la perfusión, la señal
     respiratoria no».
   - Ninguna regla congelada lo rechaza, y el veredicto no cambia.
   - Pido decidir si la fisiología común debe exigir la monotonía: limitar la ganancia a 0,03–0,04 o adoptar una forma
     de reclutamiento acotada cuando se migre otra familia. La otra opción es declararla limitación.
   - Es una cuestión de coherencia de la fisiología común, no de identificabilidad, y no bloquea seguir con conciencia en
     los casos GI actuales.
   - Debe condicionar la migración de esta fisiología respiratoria común a otra familia y cualquier regla de conciencia
     que lea la dirección o la tendencia del pH (revisión adversarial).
   - Consecuencia para las reglas (revisión M1): en esa zona, la regla «empeoran ambas» de E y F, que exige más carga y
     menos pH, no puede dispararse. En los datos reales ninguna lectura empeoró la perfusión, así que ningún conteo
     cambia. Para un próximo congelamiento se propone definir el empeoramiento respiratorio por la carga, con el pH
     informado.
   - Contexto, como información y no como selección:
     - el gas de llegada de 72f (pH 7,40, HCO3 19,8, PaCO2 33) ya está en compensación completa;
     - las ganancias implícitas del mapeo docente (0,043 y 0,050) superan 1/24;
     - 0,04 es la única ganancia monótona y PH_CONSISTENT en la llegada de ambos casos.

## 14. Limitaciones

- **Supervivientes aguas arriba.** Las envolventes se aplican sobre los supervivientes de P2J-3 en las ganancias de tono
  primarias; nada aguas arriba se recalibra. Que una unidad aguas arriba conserve supervivientes respiratorios es un
  diagnóstico, no una restricción sobre ella.
- **Ponderación de los conteos.** Los conteos de candidatos completos pesan por igual cada combinación de factores que
  ninguna regla lee. Los observables se resumen sobre entradas únicas (trayectoria × subcombinación latente).
- **Comparador F de R3.** El contrafactual sin GR de R3 es nuevo: los mismos insumos de R3 sin los GR, validado contra el
  núcleo. Los de R4 (CF1, CF2) y el de E son los certificados de P2J-3.
- **Lecturas emparejadas.** Se leen en los minutos congelados (fin de cada intervención y 120), no en cada minuto.
- **Volumen corriente.** El volumen corriente sigue implícito: no hay estado de espacio muerto, de mecánica ni de fatiga
  (P2K-3).
- **Sobrecompensación a cargas bajas.** Con las ganancias 0,05 y 0,06 la compensación supera a la completa a cargas
  bajas (§13, punto 4). Es pequeña en estos casos (≤ 0,015 de pH), pero una familia con cargas ácidas pequeñas la notaría.
- **Criterios del veredicto (revisión M2, L4, L6).**
  - «Respuestas coherentes» cuenta que la FR y la PaCO2 siguen a la carga, algo que se cumple por construcción. La
    dirección del pH no se prueba, y está invertida en las lecturas «no mejora».
  - «pH coherente» comprueba sólo el rango 6,8–7,8 y el banco. Su límite inferior lee también R1: actúa como un piso del
    pH sin tratamiento a nivel de veredicto, sin efecto aquí (mínimo 6,96).
  - «Envolventes» y «llegada» releen los mismos resúmenes que construyeron los bits. La evidencia independiente es la
    recomputación directa, más las sondas de mutación sintéticas, en las que E y F rechazan.
  - El emparejamiento de R3 sin GR se cumple por definición. Su evidencia real es la validación contra el núcleo,
    realizada sólo con demanda 1,0 en el registro.
- **Eficiencia.** «Barrido cartesiano: no» y «FR heredada leída: no» son declaraciones del diseño, no mediciones. El
  grafo de importación carga `family_engine` y el adaptador heredado sólo para la cronología de los insumos del
  escenario; no se lee ninguna FR heredada.
- **Veredicto.** Se aplicaron sólo las reglas congeladas. Ninguna regla se añadió ni cambió después de ver los conteos.

## 15. Revisión adversarial

Una revisión independiente, de sólo lectura, sobre el congelamiento `46d009a` y la evaluación, con el foco que pidió la
docencia. Confirmó cada hallazgo con una sonda o una mutación fuera del repositorio.

- **Severidad alta:** ninguna. Ningún hallazgo cambia los resultados ejecutables de la corrida congelada.
- **Limpios, con evidencia:**
  - el módulo no cambió desde el congelamiento (`git diff 46d009a` vacío, el mismo digest) y el registro es el de esa
    corrida;
  - sólo H lee el pH, el de R4 a los 120 min; el pH de llegada y el pH sin tratamiento nunca filtran; en la llegada la
    PaCO2 filtra y el pH no;
  - la robustez entre demandas es sólo diagnóstica;
  - E y F no leen la FR;
  - R3 y R4 no tienen que diferir por la identidad del tratamiento, y su comparación subyacente es genuina;
  - la FR intrínseca 12 sobrevive;
  - ninguna regla de pH elige la ganancia;
  - no se ajusta a la FR heredada;
  - los archivos cerrados conservan sus bytes de `ef2cfe8`;
  - no hay simulación cartesiana;
  - los comparadores omiten sólo su exposición, en los minutos congelados;
  - la maquinaria de bitsets coincide con una fuerza bruta ingenua.
- **M1 (medio, diseño de la regla), declarado.** Con las ganancias 0,05 y 0,06 a cargas bajas, la regla «empeoran
  ambas» de E y F no puede dispararse (§13, punto 4). En los datos reales ninguna lectura empeoró la perfusión, así que
  ningún conteo cambia. Se propone para un próximo congelamiento; aquí no se cambia una regla después de ver los conteos.
- **M2 (medio, criterios), declarado.** Los criterios de coherencia prueban direcciones que valen por construcción. La
  dirección del pH no la prueba ninguno y está invertida en las lecturas «no mejora». Se matizan en §14 y en TD-105.
- **L1, corregido en el texto.** El resumen y §49 decían «sin cambio respiratorio», «ninguno tiene déficit» y «las unidades
  de 72f no cambian la perfusión». Ahora dicen lo que muestra el registro.
- **L2 y L5, verificados con una sonda fuera del registro.**
  - En los 182 conjuntos de GR, R3 y R4 difieren en volumen circulante, en contenido eritrocitario y en hemostasia.
  - Los comparadores nuevos igualan al núcleo también con demanda 1,1: 18 corridas, diferencia máxima 0, aguas arriba
    igual.
  - El código no se cambia, para no tocar el módulo congelado; la deuda queda en TD-105 (3).
- **L3, corregido en las pruebas.** Una prueba sintética hace que E y F rechacen un tratamiento perjudicial, con el
  filtro igual a la recomputación directa. La revisión halló además 0 discrepancias en 6480 candidatos reales de
  unidades al azar.
- **L4, L6, L7 y L8, declarados en §14:**
  - criterios que valen por construcción;
  - el piso de pH 6,8 que también lee R1;
  - las marcas de eficiencia, que son declaraciones y no mediciones;
  - el nombre NON_IDENTIFIABLE de la ganancia de ventilación.
- **L9:** `rr_follows_burden` sólo lo usan las pruebas; se deja.
