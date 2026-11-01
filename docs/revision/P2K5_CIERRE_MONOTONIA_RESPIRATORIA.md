# P2K-5 · Cierre de la monotonía respiratoria: el pH no sube con la carga ácida

- **Fecha:** 2026-11-01. **Rama:** `phase-2-clinical-core-shadow`. **Base:** `b6908e5` (P2K-4, aceptado y cerrado).
- **Congelamiento:** `e17ecee` (digest `561a8878…`). Antes del recuento quedaron fijados la regla analítica, las clases
  de ganancia, la señal de tratamiento corregida, la regla de reutilización y la de alcance, las clases de
  identificabilidad y el veredicto.
  - Antes de congelar sólo se probó la maquinaria con datos sintéticos y con los certificados del registro de P2K-4.
  - **Nota de proceso.** Una comprobación rápida de `record_algebra` imprimió, antes del congelamiento, las cifras podadas
    que se deducen del registro de P2K-4: la mitad de cada conteo, por la invarianza de la ganancia. Ninguna regla,
    soporte ni criterio depende de esas cifras ni cambió después. Se declara aquí y en el commit de congelamiento.
- **Números:** `docs/revision/P2K5_respiratory_monotonicity.json`. Generador de los bloques:
  `python -m clinical_core.respiratory_monotonicity_report`.
- **Alcance:** sólo sombra.
  - No se aprueba ningún parámetro respiratorio ni se elige entre 0,03 y 0,04.
  - Sin conciencia, sin colapso, sin migraciones, sin integración en tiempo de ejecución y sin ajuste al motor heredado.

## Resumen

- **La contradicción.** Con el reclutamiento lineal de P2K-3, las ganancias 0,05 y 0,06 hacían subir el pH al aumentar la
  carga ácida metabólica cuando la carga era baja: la compensación invertía la dirección de la carga metabólica.
- **La regla analítica.**
  - El signo de la derivada del pH respecto de la carga es el de N(A) = (g·24 − 1) − 2g·A, que es lineal y no creciente
    en A. Por eso su valor en A = 0 decide todo el dominio.
  - El pH no sube en 0 ≤ A < 24 si y sólo si g ≤ 1/24 ≈ 0,0417 por mEq/L. Es una prueba con racionales exactos, no un
    muestreo.
  - 0,03 y 0,04 son admisibles. 0,05 y 0,06 se rechazan por monotonía: el pH sube en 0 ≤ A < 2 y en 0 ≤ A < 11/3,
    respectivamente.
- **La semántica del tratamiento.**
  - P2K-4 nunca leyó una carga mayor como mejora respiratoria. Su defecto era otro: cuando la sobrecompensación subía el
    pH, la regla «empeoran ambas» no podía rechazar un tratamiento que aumentaba la carga y empeoraba la perfusión (M1).
  - Ahora una carga mayor cuenta como empeoramiento respiratorio, haga lo que haga el pH; si el pH sube a la vez, queda
    marcado como paradoja.
  - Frente a P2K-4 sólo cambia una clase: «empeora la perfusión, la respiración no cambia» con carga mayor pasa a
    «empeoran ambas». No se añadió ningún umbral numérico.
  - La regla congelada va algo más allá del texto docente, aunque coincide con lo que proponía la M1 de TD-105 (§17).
- **La reutilización.**
  - La región de P2K-5 son los supervivientes de P2K-4 con ganancia 0,03 o 0,04.
  - El recuento de P2K-4 se reprodujo exactamente con su propio código congelado, reconstruyendo sólo las trayectorias
    R1 y R4. Tres reglas se tomaron como FULL por el certificado del registro (SIMULATION de los otros cinco tipos de
    trayectoria, E y F), así que en esas el acuerdo es por construcción.
  - Sin la poda, los observables de A–I y la acidemia extrema también se reproducen exactamente.
- **Resultado.**
  - Con demanda 1,0 quedan 82 740 de 165 480 supervivientes; con 1,1, 511 056 de 1 022 112. En ambas, 156
    combinaciones latentes.
  - Ningún superviviente falla por la semántica corregida, y todos siguen dentro de A–I.
  - En los observables registrados (llegada, a los 120 min y mínimo sin tratamiento), el pH ya no supera el de carga
    cero (7,401). Analíticamente es así para toda carga A ≥ 0: no hay alcalinización.
  - Las 17 604 filas de 57m con pH < 7,00 sin tratamiento y demanda 1,1 son las mismas que en P2K-4. Siguen todas en la
    región (lo observa el registro y lo fija una prueba) y pasan a CONSCIOUSNESS_COLLAPSE_REVIEW. El pH mínimo no cambia
    (6,961), porque se alcanza con 0,03.
- **Veredicto:** `GI_RESPIRATORY_PHYSIOLOGY_CLOSED_FOR_CURRENT_PHASE`. **Recomendación:** `MOVE_FORWARD_TO_CONSCIOUSNESS`.
  La incertidumbre latente que queda se propaga, sin abrir otro ciclo respiratorio.

## 1. Decisiones de la docencia (2026-11-01)

<!-- generado:decisiones -->
Texto congelado, en inglés, en el orden del encargo.

- **fecha**: 2026-11-01
- **P2K-4**: P2K-4 accepted and closed; RR_VENTILATION_OBSERVABLE_FILTER_SATISFIED accepted and MOVE_FORWARD agreed; one structural respiratory contradiction to close before consciousness, collapse, GI migration or a second family
- **objetivo**: remove the paradox in which a higher metabolic acid burden raises pH at low burden because ventilation recruitment is too strong; then, with a non-empty coherent region, close the respiratory domain for the current GI calibration
- **prioridad del proyecto**: a coherent common physiology with explicit plausible uncertainty and no causal contradiction, good enough to migrate other families; not identifying every latent, a tighter fit of two GI cases or one best candidate
- **regla estructural**: for increasing metabolic acid burden A, other physiology fixed, pH must be non-increasing: compensation may reduce the fall in pH, never reverse the metabolic load into alkalinization
- **regla analítica**: pH is log[(HCO3_reference - A)(1 + g_v A)] up to constants; at A = 0 a non-increasing pH requires g_v <= 1 / HCO3_reference = 1/24; 0.03 and 0.04 STRUCTURALLY_ADMISSIBLE_PRIMARY_SUPPORT, 0.05 and 0.06 REJECTED_BY_ACID_BASE_MONOTONICITY, by the analysis, never by counts or fit
- **sin saturación**: no saturating recruitment and no new parameter now: the support already holds admissible values; a saturating form may be reconsidered if a second respiratory family shows the linear form is insufficient
- **semántica del tratamiento**: a higher burden with a higher pH produced by excessive compensation is never respiratory improvement; no new numeric treatment threshold; once 0.05 / 0.06 are removed the condition is unreachable
- **soporte que se mantiene**: intrinsic RR 12 / 16 / 20 per patient, the P2K-4 drive gains, B 13.4 / 19.4 / 28, tau 60 / 120 / 240, ventilation gain 0.03 / 0.04, HCO3_reference 24 and PaCO2_reference 40 provisional, arrival RR and PaCO2 +/- 3, BASELINE_RELATIVE demand; nothing else narrowed
- **reutilización**: P2K-4's survivors filtered by the gain alone when the subset is exact; never the full bitset pipeline again
- **acidemia extrema**: untreated pH < 7.00 kept, never filtered: CONSCIOUSNESS_COLLAPSE_REVIEW, carried forward
- **R3 / R4**: PHYSIOLOGICAL_RESPIRATORY_CONVERGENCE retained while the underlying states stay distinct
- **identificabilidad**: the gain narrowed by a structural rule is not WELL_CONSTRAINED; no choice of 0.03 or 0.04
- **criterio de salida**: non-empty, pH monotone, A-I held, treatment responses coherent, R3 / R4 physiological, upstream unchanged: GI_RESPIRATORY_PHYSIOLOGY_CLOSED_FOR_CURRENT_PHASE and MOVE_FORWARD_TO_CONSCIOUSNESS; the remaining broad latents are propagated, never a reason for another respiratory cycle
- **parada temprana**: an empty region STOPs: no gain restored, no envelope widened, no HCO3 or PaCO2 reference, arrival tolerance, B or tau changed, no legacy fitting
- **alcance**: shadow only; no runtime integration, migration, parameter approval, consciousness or collapse; the upstream physiology reused, never reopened
<!-- /generado:decisiones -->

## 2. La regla analítica

<!-- generado:regla -->
**Ecuación (texto congelado).** pH(A) = pK + log10[(HCO3_reference - A) x (1 + g_v x A) / (s x PaCO2_reference)], pK 6.1, s 0.03, for 0 <= A < HCO3_reference (the P2K-3 mapping at efficiency 1 and the baseline demand)

**Derivada y desigualdad (texto congelado).** d pH / dA = (1 / ln 10) x [g_v / (1 + g_v A) - 1 / (HCO3_reference - A)] = (1 / ln 10) x N(A) / [(1 + g_v A)(HCO3_reference - A)], with N(A) = (g_v x HCO3_reference - 1) - 2 g_v x A. On 0 <= A < HCO3_reference the denominator is positive (g_v >= 0), so the sign of the slope is the sign of N. N is linear in A with slope -2 g_v <= 0, so its largest value on the domain is N(0) = g_v x HCO3_reference - 1. pH is non-increasing on the whole domain if and only if N(0) <= 0, i.e. g_v <= 1 / HCO3_reference (strictly decreasing when g_v < 1 / HCO3_reference). When g_v > 1 / HCO3_reference, pH rises on 0 <= A < A* = (g_v x HCO3_reference - 1) / (2 g_v). Efficiency and demand ratio multiply PaCO2 by constants independent of A and drop out of the derivative.

**Ganancia crítica.** 1 / HCO3_referencia = 1/24 ≈ 0,0416667 por mEq/L (HCO3_referencia 24, PaCO2_referencia 40; ambas provisionales).

**Alcance (texto congelado).** The bicarbonate at zero burden is the case's authored HCO3 plus its arrival burden: HCO3_reference when the authored HCO3 is at or below it (both GI cases). A family authored above the reference would carry 1 / its own zero-burden bicarbonate as the critical gain; that is a generalization question, not decided here.
<!-- /generado:regla -->

## 3. Las ganancias de P2K-4 bajo la regla

<!-- generado:ganancias -->
| ganancia | exacta | N(0) = g·24 − 1 | pendiente de N | pendiente del pH en A = 0 | intervalo donde el pH sube | pico | clase |
|---|---|---|---|---|---|---|---|
| 0,03 | 3/100 | −7/25 | −3/50 | −0,00507 | ninguno | — | admisible (soporte primario) |
| 0,04 | 1/25 | −1/25 | −2/25 | −0,00072 | ninguno | — | admisible (soporte primario) |
| 0,05 | 1/20 | 1/5 | −1/10 | 0,00362 | 0 ≤ A < 2 (2,00) | pH 7,4046 en A 2,00 (pH 7,4010 en 0) | rechazada por monotonía ácido-base |
| 0,06 | 3/50 | 11/25 | −3/25 | 0,00796 | 0 ≤ A < 11/3 (3,67) | pH 7,4154 en A 3,67 (pH 7,4010 en 0) | rechazada por monotonía ácido-base |
| 0,08 | 2/25 | 23/25 | −4/25 | 0,01665 | 0 ≤ A < 23/4 (5,75) | pH 7,4464 en A 5,75 (pH 7,4010 en 0) | rechazada por monotonía ácido-base · ya excluida en P2K-3 / P2K-4 |
<!-- /generado:ganancias -->

## 4. El mapeo ejecutable y las sondas sintéticas

<!-- generado:sondas -->
**El mapeo ejecutable es el analizado.** 57m: HCO3 de autoría 17,3, carga de llegada 6,7, HCO3 a carga cero 24,0; error máximo frente a la forma cerrada 8,9 × 10^−16; 72f: HCO3 de autoría 19,8, carga de llegada 4,2, HCO3 a carga cero 24,0; error máximo frente a la forma cerrada 8,9 × 10^−16.

**Sondas sintéticas** (22 cargas por caso, de 0 a 23 mEq/L, con la de llegada): con 0,03 y 0,04 el HCO3 baja, la PaCO2 baja y el pH no sube en ningún paso: sí. Con 0,05 y 0,06 el pH sube sólo en los pasos que empiezan dentro de [0, A*): sí. La PaCO2 baja con la carga en todas: sí.

| caso | ganancia | pH en 0 | pH en la llegada | pasos en que el pH sube |
|---|---|---|---|---|
| 57m | 0,03 | 7,4010 | 7,3384 | ninguno |
| 57m | 0,04 | 7,4010 | 7,3620 | ninguno |
| 57m | 0,05 | 7,4010 | 7,3843 | 0,00→0,25; 0,25→0,50; 0,50→1,00; 1,00→1,50; 1,50→2,00 |
| 57m | 0,06 | 7,4010 | 7,4056 | 0,00→0,25; 0,25→0,50; 0,50→1,00; 1,00→1,50; 1,50→2,00; 2,00→2,50; 2,50→3,00; 3,00→3,50 |
| 72f | 0,03 | 7,4010 | 7,3690 | ninguno |
| 72f | 0,04 | 7,4010 | 7,3849 | ninguno |
| 72f | 0,05 | 7,4010 | 7,4003 | 0,00→0,25; 0,25→0,50; 0,50→1,00; 1,00→1,50; 1,50→2,00 |
| 72f | 0,06 | 7,4010 | 7,4151 | 0,00→0,25; 0,25→0,50; 0,50→1,00; 1,00→1,50; 1,50→2,00; 2,00→2,50; 2,50→3,00; 3,00→3,50 |
<!-- /generado:sondas -->

## 5. La señal de tratamiento corregida (M1 / M2 de P2K-4)

<!-- generado:semantica -->
**Regla (texto congelado, en inglés).** Frozen before any recount. The respiratory signal of a matched reading follows the metabolic acid load: a higher burden is respiratory worsening whatever the pH does (a pH rise beside it is excessive compensation, flagged PH_RISES_WITH_HIGHER_ACID_BURDEN, never improvement); a lower burden is improvement only when pH is also higher (a pH fall beside it is flagged PH_FALLS_WITH_LOWER_ACID_BURDEN and is not improvement); no burden change is no respiratory change. Perfusion, the classes, the rejecting classes (RESPIRATORY_AND_PERFUSION_WORSEN and a treated arrest), the comparators, the minutes and P2J-3's no-change tolerance (1e-9 of the scale) are P2K-4's; no numeric threshold is added. Against P2K-4 the only class that moves is RESPIRATORY_UNCHANGED_WITH_PERFUSION_WORSENING with a higher burden, which becomes RESPIRATORY_AND_PERFUSION_WORSEN (M1: the conjunction could not fire when overcompensation raised pH). M2: the pH direction is now read, through the paradox flags.

| perfusión | carga | pH | clase P2K-4 | clase P2K-5 | marca |
|---|---|---|---|---|---|
| − | − | − | empeora la perfusión, la respiración no cambia | empeora la perfusión, la respiración no cambia | el pH baja con menos carga |
| − | + | 0 | empeora la perfusión, la respiración no cambia | empeoran ambas (rechaza) | — |
| − | + | + | empeora la perfusión, la respiración no cambia | empeoran ambas (rechaza) | el pH sube con más carga |
| 0 | − | − | sin cambio de perfusión | sin cambio de perfusión | el pH baja con menos carga |
| 0 | + | + | sin cambio de perfusión | sin cambio de perfusión | el pH sube con más carga |
| + | − | − | mejora la perfusión, la señal respiratoria no | mejora la perfusión, la señal respiratoria no | el pH baja con menos carga |
| + | + | + | mejora la perfusión, la señal respiratoria no | mejora la perfusión, la señal respiratoria no | el pH sube con más carga |

Sólo cambia la clase con perfusión peor y carga mayor: sí; ninguna clase deja de rechazar: sí. De las 27 combinaciones de signos, 25 conservan su clase; la tabla muestra sólo las que cambian o llevan marca. Ninguna marca de paradoja es alcanzable con 0,03 o 0,04: sí.
<!-- /generado:semantica -->

## 6. La reutilización exacta de P2K-4

<!-- generado:reutilizacion -->
**Regla (texto congelado, en inglés).** Frozen. P2K-5's region is P2K-4's survivors with the ventilation gain in the admissible support. The reuse is exact when (1) the closed files keep their P2K-4 bytes and P2K-4's freeze digest recomputes (the rule digest of the reused code), (2) the P2K-4 record is the pinned one, (3) its certificates hold at both demands: SIMULATION, E and F never failed (so their bitsets are FULL for every unit), the ventilation gain is NON_IDENTIFIABLE with the filter not reading it (every unit's survivors identical at every gain), no survivor reading has a worse perfusion (the only class the corrected signal can move), R3 / R4 has no state-collapse bug; and (4) the reached recomputation, P2K-4's own functions on the R1 / R4 trajectories with the certified rules FULL, reproduces P2K-4's tally exactly at every demand (candidate identity). The pruned region is then those survivors masked by the gain; nothing else is rerun.

- Archivos cerrados con sus bytes de P2K-4: sí (7); el digest de congelamiento de P2K-4 se recalcula igual: sí; registro de P2K-4 fijado: sí.

| demanda | SIMULATION, E y F nunca fallan | ganancia invariante por unidad | lecturas con perfusión peor | lecturas que rechazan | colapso R3 / R4 | recuento reproducido | observables y acidemia reproducidos | álgebra igual |
|---|---|---|---|---|---|---|---|---|
| 1,0 | sí | sí | 0 de 103 680 | 0 | no | sí | sí | sí |
| 1,1 | sí | sí | 0 de 329 400 | 0 | no | sí | sí | sí |

**Alcance de la recomputación (texto congelado).** Frozen. Only what the pruning reaches is rebuilt: the R1 and R4 trajectories of every P2J-3 upstream survivor (R1 decides A-D and the extreme acidemia, R4 G, G2, H and I), by P2K-4's trajectory and summarize; their rule bitsets by P2K-4's unit_rules, with the certified rules (SIMULATION of the other trajectories, E, F) FULL. The crystalloid, red-cell, counterfactual and no-red-cell trajectories, the no-red-cell blood runs, the R3 / R4 core states, the P2K-3 reconstruction and the comparator validation are not rerun.
<!-- /generado:reutilizacion -->

## 7. La poda

<!-- generado:poda -->
| demanda | entran (supervivientes de P2K-4) | rechazados por monotonía | rechazados por la semántica corregida | supervivientes P2K-5 | por tono | unidades con supervivientes | combinaciones latentes |
|---|---|---|---|---|---|---|---|
| 1,0 | 165 480 | 82 740 | 0 | **82 740** | g 0,25 33 600 de 67 200, g 0,5 28 236 de 56 472, g 1,0 20 904 de 41 808 | 531 de 531 | 156 |
| 1,1 | 1 022 112 | 511 056 | 0 | **511 056** | g 0,25 170 352 de 340 704, g 0,5 170 352 de 340 704, g 1,0 170 352 de 340 704 | 3 276 de 3 276 | 156 |

**Entre demandas** (1 620 combinaciones): robustas en ambas demandas 156; sólo con demanda 1,0 0; sólo con demanda 1,1 0; incompatibles con ambas (soporte admisible) 654; fuera del soporte (ganancia 0,05 / 0,06) 810.
<!-- /generado:poda -->

## 8. Soporte latente e identificabilidad

<!-- generado:latentes -->
| parámetro | demanda 1,0 | demanda 1,1 | soporte (combinaciones por valor) |
|---|---|---|---|
| B | poco identificado | no identificable | 13,4: 52, 19,4: 52, 28,0: 52 |
| ganancia ácido → FR | poco identificado | poco identificado | 1,00: 18, 1,41: 72, 2,00: 18, 2,83: 36, 4,00: 12 |
| FR intrínseca 57m | poco identificado | poco identificado | 12,0: 48, 16,0: 54, 20,0: 54 |
| FR intrínseca 72f | poco identificado | poco identificado | 12,0: 30, 16,0: 72, 20,0: 54 |
| τ de aclaramiento ácido | poco identificado | poco identificado | 60,0: 54, 120,0: 54, 240,0: 48 |
| ganancia ácido → ventilación | acotado por estructura, no identificable dentro | acotado por estructura, no identificable dentro | 0,03: 78, 0,04: 78 |
<!-- /generado:latentes -->

## 9. Recertificación A–I sobre los supervivientes podados

<!-- generado:observables -->
| observable | 57m · 1,0 | 57m · 1,1 | 72f · 1,0 | 72f · 1,1 |
|---|---|---|---|---|
| FR de llegada | 26,1 [23,9–28,4] | 26,1 [23,9–28,4] | 23,9 [21,3–25,5] | 23,9 [21,3–25,5] |
| PaCO2 de llegada | 32,4 [31,5–33,3] | 32,4 [31,5–33,3] | 34,9 [34,2–35,5] | 34,9 [34,2–35,5] |
| pH de llegada (diagnóstico) | 7,350 [7,338–7,362] | 7,350 [7,338–7,362] | 7,377 [7,369–7,385] | 7,377 [7,369–7,385] |
| FR a 120 · R1 | 28,9 [24,0–35,1] | 29,8 [24,5–36,2] | 25,4 [20,9–32,8] | 26,4 [21,6–34,7] |
| PaCO2 a 120 · R1 | 30,3 [24,4–33,2] | 29,5 [23,1–32,8] | 33,6 [28,7–35,8] | 32,8 [26,9–35,3] |
| pH a 120 · R1 | 7,311 [7,094–7,361] | 7,295 [6,961–7,355] | 7,364 [7,284–7,387] | 7,355 [7,230–7,383] |
| pH mínimo 0–120 · R1 | 7,311 [7,094–7,361] | 7,295 [6,961–7,355] | 7,364 [7,284–7,385] | 7,355 [7,230–7,383] |
| FR a 120 · R4 | 21,4 [15,0–25,7] | 21,8 [15,3–26,3] | 19,2 [13,6–23,4] | 19,4 [13,7–23,6] |
| PaCO2 a 120 · R4 | 36,3 [33,8–38,7] | 35,9 [33,2–38,5] | 37,9 [36,2–39,3] | 37,7 [36,0–39,3] |
| pH a 120 · R4 | 7,388 [7,365–7,399] | 7,385 [7,359–7,399] | 7,396 [7,384–7,400] | 7,395 [7,382–7,400] |
| FR − intrínseca a 120 · R4 | 4,1 [1,1–10,2] | 4,6 [1,2–11,5] | 2,4 [0,6–6,4] | 2,5 [0,6–6,7] |

Envolventes A–I y ventanas de llegada sobre estos observables: demanda 1,0: A–I sí, llegada sí; demanda 1,1: A–I sí, llegada sí.
<!-- /generado:observables -->

## 10. Acidemia extrema sin tratamiento (se arrastra, no se filtra)

<!-- generado:acidemia -->
| demanda | supervivientes | con pH < 7,00 sin tratamiento | 57m | 72f | pH mínimo | caso, minuto | carga | déficit efectivo | PaCO2 | FR | marca |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1,0 | 82 740 | 0 | 0 | 0 | 7,094 | 57m, 120 | 16,00 | 0,737 | 27,0 | 33,5 [30,9–35,1] | ninguna |
| 1,1 | 511 056 | 17 604 | 17 604 | 0 | 6,961 | 57m, 120 | 18,38 | 0,835 | 25,8 | 34,6 [32,2–36,2] | CONSCIOUSNESS_COLLAPSE_REVIEW |

Ninguna fila se filtra: las marcadas siguen en la región y pasan a CONSCIOUSNESS_COLLAPSE_REVIEW.
<!-- /generado:acidemia -->

## 11. R3 / R4

<!-- generado:r3r4 -->
**Regla (texto congelado, en inglés).** Not reopened. The underlying states (bleeding state, BloodState, chronology) read no respiratory latent, so P2K-4's result (no SCENARIO_STATE_COLLAPSE_BUG) holds for every pruned candidate; the respiratory gap is a maximum over the pair's surviving latent combinations, so the pruning can only keep a pair's class or move it from RESPIRATORY_OUTPUTS_DISTINCT to PHYSIOLOGICAL_RESPIRATORY_CONVERGENCE. P2K-4's counts are carried as the bound.

- Demanda 1,0: convergencia respiratoria fisiológica; clases de P2K-4 (cota): convergencia respiratoria fisiológica 108, salidas respiratorias distintas 0, colapso de escenario (STOP) 0; colapso: no.
- Demanda 1,1: convergencia respiratoria fisiológica; clases de P2K-4 (cota): convergencia respiratoria fisiológica 526, salidas respiratorias distintas 20, colapso de escenario (STOP) 0; colapso: no.
<!-- /generado:r3r4 -->

## 12. No regresión

<!-- generado:no_regresion -->
| dominio | sin cambio | evidencia |
|---|---|---|
| D | sí | archivos cerrados con los bytes de P2K-4; región de P2J-3 reproducida; validación de comparadores de P2K-4 sobre los mismos bytes |
| BloodState | sí | archivos cerrados con los bytes de P2K-4; región de P2J-3 reproducida; validación de comparadores de P2K-4 sobre los mismos bytes |
| DO2 / déficit efectivo | sí | archivos cerrados con los bytes de P2K-4; región de P2J-3 reproducida; validación de comparadores de P2K-4 sobre los mismos bytes |
| FC / barorreflejo | sí | archivos cerrados con los bytes de P2K-4; región de P2J-3 reproducida; validación de comparadores de P2K-4 sobre los mismos bytes |
| lactato | sí | archivos cerrados con los bytes de P2K-4; región de P2J-3 reproducida; validación de comparadores de P2K-4 sobre los mismos bytes |
| gasto | sí | archivos cerrados con los bytes de P2K-4; región de P2J-3 reproducida; validación de comparadores de P2K-4 sobre los mismos bytes |
| presión / tono | sí | archivos cerrados con los bytes de P2K-4; región de P2J-3 reproducida; validación de comparadores de P2K-4 sobre los mismos bytes |

Región de P2J-3 recalculada y comparada con su registro: clase de demanda sí, filtro primario sí, soporte sí, unidades sí.
<!-- /generado:no_regresion -->

## 13. Inventario para el próximo dominio: conciencia / respuesta neurológica N

<!-- generado:inventario_n -->
| señal | dónde está hoy | estado |
|---|---|---|
| déficit efectivo de oxígeno | derived.effective_oxygen_deficit, derived.acute_deficit_signal | núcleo: impulsa la carga ácida y el impulso simpático |
| D (deuda acumulada de aporte de oxígeno) | estado, Channel.D (C8) | núcleo: impulsa el lactato y el impulso simpático |
| pH / acidemia | derived.respiration (P2K-2), ventilation.ventilated_respiration (P2K-3) | candidato en sombra, sólo salida; las filas de acidemia extrema sin tratamiento pasan a CONSCIOUSNESS_COLLAPSE_REVIEW |
| PaCO2 | ventilation.ventilated_respiration (PaCO2_referencia / W) | candidato en sombra, sólo salida |
| glucosa | estado, Channel.GLUCOSE (C11, absoluta, del caso) | núcleo: término de hipoglucemia del impulso simpático (umbral provisional) |
| oxigenación | SpO2 en derived._perfusion (FiO2 e intercambio gaseoso G); PaO2 sólo de autoría | núcleo: término de hipoxemia del impulso simpático (umbral provisional) |
| canal neurológico N | estado, Channel.N (C9, depresión del SNC, desvío desde la llegada) | existe: sólo guardia de integración; ningún módulo escribe N todavía |
| PAM / perfusión cerebral (fuera de la lista docente) | derived._perfusion (pressure_rel) | núcleo: se ofrece a la decisión docente, no se da por supuesta |

Sólo inventario: sin calibración de conciencia, sin reglas y sin escritor de N; hoy nada llega a N. El próximo encargo decide cuáles de estas señales podrán llegar.
<!-- /generado:inventario_n -->

## 14. Veredicto y recomendación

<!-- generado:veredicto -->
**Veredicto:** `GI_RESPIRATORY_PHYSIOLOGY_CLOSED_FOR_CURRENT_PHASE`.

| criterio | cumple |
|---|---|
| fisiología previa intacta (archivos cerrados, región P2J-3, dominios) | sí |
| reutilización exacta (recuento de P2K-4 reproducido, álgebra del registro igual) | sí |
| la región podada no queda vacía | sí |
| pH no creciente con la carga para cada ganancia retenida | sí |
| los supervivientes cumplen A–I y las ventanas de llegada | sí |
| respuestas a los tratamientos coherentes con la señal corregida | sí |
| R3 / R4 sin colapso de estados | sí |
| el resto del soporte latente intacto, sin elegir valor | sí |
| las filas de acidemia extrema siguen en la región | sí |
| nada aprobado | sí |

**Recomendación:** `MOVE_FORWARD_TO_CONSCIOUSNESS` → conciencia / respuesta neurológica N (no iniciada).
- clases entre demandas → la pregunta de la demanda (diagnóstico)
- incertidumbre latente explícita, propagada; ningún ciclo respiratorio por identificabilidad
- acidemia extrema sin tratamiento → CONSCIOUSNESS_COLLAPSE_REVIEW
<!-- /generado:veredicto -->

## 15. Eficiencia

<!-- generado:eficiencia -->
- Región P2J-3 reconstruida (necesaria para las trayectorias): 1 326 corridas de sangre y 364 contrafactuales.
- Trayectorias alcanzadas (R1 y R4) reconstruidas: 984; no reconstruidas: 6 342 (cristaloide, GR, contrafactuales y sin GR, certificadas por P2K-4).
- Candidatos recontados como bitsets con el código congelado de P2K-4: 6 167 340 en 3 807 unidades; rechazados analíticamente por la ganancia: 593 796.
- No repetido: 182 corridas sin GR, 364 estados R3 / R4, 36 corridas de comparadores, 96 de validación P2K-3 y 19 440 candidatos de la verificación directa.
- Barrido cartesiano: no; lectura del motor heredado: no.
<!-- /generado:eficiencia -->

## 16. Nota estratégica de generalización

El modelo respiratorio GI actual es un modelo MÍNIMO de compensación ácida con respiración espontánea.

- **Lo que no establece todavía.** No establece una fisiología respiratoria general para la EPOC, el asma, la
  hipoventilación por opioides, la neumonía, el edema pulmonar ni la ventilación mecánica.
- **Lo que pondrán a prueba esas familias.** Si la descomposición actual FR / W / ácido-base generaliza.
- **Lo que no se hace ahora.** No se añade por adelantado su fisiología: ni saturación, ni volumen corriente explícito,
  ni espacio muerto, fatiga o mecánica, ni constante de tiempo del CO2, ni impulso hipoxémico.
- **El alcance de la regla.** La ganancia crítica es 1 / HCO3 a carga cero. Coincide con 1 / HCO3_referencia sólo cuando
  el HCO3 de autoría del caso no supera la referencia, como en los dos casos GI. Una familia con HCO3 de autoría por
  encima de 24 tendría un umbral menor; es una pregunta de generalización que no se decide aquí.

## 17. Limitaciones

- **HCO3_referencia y PaCO2_referencia.**
  - HCO3_referencia (24) sigue siendo provisional: la regla lee de él su umbral, pero eso no lo aprueba como fisiología.
  - PaCO2_referencia (40) es un factor constante y no entra en la regla.
- **La semántica corregida no se recalculó lectura por lectura.**
  - Su alcance sobre la región retenida es nulo por prueba: el registro de P2K-4 no tiene ninguna lectura de
    superviviente con perfusión peor, que es la única condición en la que la corrección cambia una clase.
  - Además, la paradoja es inalcanzable para 0,03 y 0,04 por la monotonía estricta.
  - Las trayectorias de cristaloide, GR, contrafactuales y sin GR no se reconstruyeron. Por eso no se recuentan aquí las
    lecturas «mejora la perfusión, la señal respiratoria no» de la región retenida.
- **R3 / R4 no se reabrió.** Los estados subyacentes no dependen de ningún latente respiratorio, y la brecha respiratoria
  es un máximo, así que la poda sólo puede mantener una clase o acercarla a la convergencia. Los conteos de P2K-4 quedan
  como cota.
- **Lo que sigue amplio.** La FR intrínseca, la ganancia ácido → FR, B y τ siguen poco identificados (B no identificable
  con demanda 1,1). La ganancia de ventilación queda acotada por estructura y no identificada dentro de {0,03, 0,04}.
  Todo se propaga como incertidumbre explícita.
- **Lo que este cierre no establece.** El cierre vale para la calibración GI actual: dos casos y envolventes docentes de
  caso y escenario.
- **La semántica corregida también alcanza a las ganancias retenidas, en el hueco de tolerancia** (revisión M-1).
  - El caso: una carga mayor por encima de su tolerancia, con un cambio de pH dentro de la suya (diferencias de carga
    menores que unos 10⁻⁵ mEq/L), y con perfusión peor.
  - P2K-4 no rechazaba esa lectura; P2K-5 la rechaza. No lleva marca de paradoja.
  - Hoy no alcanza a la región, porque ninguna lectura de superviviente tiene perfusión peor; una prueba fija el caso.
  - La regla congelada («una carga mayor es empeoramiento, haga lo que haga el pH») va más allá del texto docente («una
    carga mayor con un pH mayor nunca es mejora»). Queda para la decisión docente.
- **La M2 queda en la regla y en el análisis, no en lecturas reales** (revisión M-2).
  - Las marcas de paradoja están definidas, y su inalcanzabilidad con 0,03 y 0,04 sale de la monotonía estricta.
  - La holgura de redondeo es una constante declarada; la revisión la midió (8,0 × 10⁻¹⁵ de error máximo en un cambio de
    pH, frente a la tolerancia mínima de 10⁻⁹).
  - El run no aplicó la señal corregida a ninguna lectura real ni contó paradojas, porque no reconstruyó las trayectorias
    de tratamiento.
  - «Rechazados por la semántica corregida: 0» se deduce del certificado del registro; no es un recuento.
- **El criterio `extreme_acidemia_carried` no puede fallar** (revisión M-3). Sólo comprueba que la región conserva sus
  propias filas. Que las 17 604 filas marcadas de P2K-4 siguen todas en la región es una observación del registro, que
  fija una prueba aparte.
- **0,04 está al 96 % del umbral** (revisión L-2). Con HCO3_referencia por encima de 25 mEq/L sería rechazada, y por
  debajo de 20 se admitiría 0,05. Las clases de ganancia valen con la referencia provisional de 24.
- **Las 20 parejas R3 / R4 «distintas» de P2K-4 con demanda 1,1 no se recalcularon** (revisión L-3). La etiqueta
  heredada significa «sin colapso de estados».
- **La eficiencia no fue mínima** (revisión L-5).
  - Lo que se reconstruyó: la región de P2J-3 completa (necesaria para las trayectorias R1 y R4) y, como bitsets, los 6
    167 340 candidatos de P2K-4, incluidas las mitades con 0,05 y 0,06.
  - Por qué: era la prueba de identidad de los candidatos, y el recuento por candidato hacía falta para la acidemia extrema
    y los rangos podados.
  - Las cifras de la poda, en cambio, ya salían del registro (`record_algebra`), y A–I sobre un subconjunto queda
    implicado.
- **Dominio** (revisión L-7). La regla se prueba para 0 ≤ A < 24. Que la carga nunca sea negativa se cumple por
  construcción (déficit ≥ 0, carga de llegada max(0, ·), τ ≥ 60) y lo fija una prueba; con A < −0,5 el pH volvería a
  subir con 0,04.
- **El paquete P2G y su documento estaban desactualizados en el commit de congelamiento** (cambió la tupla de
  `decision_pack.py`), como en P2K-4. Se regeneraron una sola vez, en el commit de evaluación.

## 18. Revisión adversarial

Una revisión independiente, de sólo lectura, sobre el congelamiento `e17ecee`, el registro y los documentos, centrada en
la regla estructural. Confirmó cada hallazgo con una sonda fuera del repositorio.

- **Severidad alta:** ninguna. Ningún resultado ejecutable ni el veredicto cambian.
- **Limpio, con evidencia:**
  - el clasificador usa sólo racionales exactos y la referencia; ningún conteo, ajuste ni trayectoria alimenta las
    clases de ganancia;
  - la prueba analítica vale en todo el dominio, y el mapeo ejecutable es el analizado en los dos casos (error ≤ 10⁻¹⁵);
  - enumerando las transiciones con una implementación propia, sólo pasan a «empeoran ambas» las dos combinaciones
    declaradas, y ninguna clase deja de rechazar;
  - el certificado cubre todas las lecturas que fijan E y F en los supervivientes: 4 parejas × 2 casos, todas las
    combinaciones (ganancia, B, τ) y todos los minutos;
  - los stubs FULL, la invarianza por unidad y la mitad exacta son sólidos, y `see` replica a `observe`;
  - la ganancia nunca sale WELL_CONSTRAINED;
  - ningún otro soporte se estrechó; la acidemia extrema conserva su definición; el núcleo no cambió; no se lee el motor
    heredado.
- **Medios, declarados (§17), sin tocar el módulo congelado:**
  - **M-1.** La prueba que decía «ningún cambio de clase con 0,03 / 0,04» no exploraba el hueco de tolerancia. Se
    corrigió y se añadió una prueba de ese caso; el resumen ya no dice que P2K-4 leyera una carga mayor como mejora.
  - **M-2.** La M2 no se aplicó a lecturas reales. Se corrigen el resumen, §50 y TD-106.
  - **M-3.** El criterio `extreme_acidemia_carried` es tautológico. Una prueba fija ahora la igualdad con P2K-4.
- **Bajos, corregidos en el texto o declarados:**
  - L-1: el acuerdo por construcción de las reglas certificadas;
  - L-2: la sensibilidad de 0,04 a la referencia, con prueba;
  - L-3: R3 / R4;
  - L-4: el alcance de «el pH no supera el de carga cero»;
  - L-5: la eficiencia;
  - L-6: el paquete P2G en el congelamiento;
  - L-7: el dominio, con prueba;
  - L-8: la redacción de §5.
