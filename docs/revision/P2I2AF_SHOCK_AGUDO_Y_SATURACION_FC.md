# P2I-2AF · Impulso agudo del shock y saturación suave de la FC

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución ni migra GI u otra familia;
- no calibra la presión, el tono vascular ni la FR, ni fija números de FC; no activa el colapso;
- no elige ni aprueba parámetros ocultos (ganancias, escala de D, techo, intrínseca) ni se ajusta al motor heredado;
- no reabre el lactato (P2I-2AD cerrado) ni la estructura de P2I-2AE fuera de lo que la docencia pidió;
- no reutiliza la región histórica de P2F para el análisis: corre dentro de la guarda de P2I-2AB.

Es el último paquete estructural de la FC.

Código:
- `clinical_core/derived.py`:
  - el objetivo simpático suma un término agudo explícito, `acute_deficit_to_sympathetic_gain × déficit efectivo /
    demanda`, y ya no contiene el resto de llegada;
  - la FC de llegada se predice desde la fisiología de llegada y su desajuste con la registrada se informa, nunca se
    absorbe;
  - el incremento sinusal satura suavemente: `HR_RESERVE · tanh(25 (1 − β) impulso / HR_RESERVE)`, con
    `HR_RESERVE = sinus_rate_ceiling_bpm − intrínseca`;
- `clinical_core/integration.py`: la demanda del minuto se actualiza antes de que el impulso la lea;
- `clinical_core/calibration.py`: HR1 y HR2 comparan con la FC de llegada de la propia corrida (§17);
- `clinical_core/decision_pack.py`: el paquete P2G registra el incremento simpático saturado (§17);
- `clinical_core/hr_shock.py`: el análisis, congelado en `565e323` antes de leer ningún resultado de FC;
- `clinical_core/hr_shock_report.py`: sólo este informe.

Números: `docs/revision/P2I2AF_hr_shock.json`. Registros de partida, cerrados: P2I-2AD (`5cb48163…`) y P2I-2AE
(`1b65d303…`), cuyos módulos y registros quedan fijados por sus pruebas.

## Resumen

- **Sin resto fijo.** El resto de llegada de P2I-2AE era un CASE_CALIBRATION_OFFSET:
  - qué era: una constante por caso, despejada de la FC registrada para reproducirla exactamente;
  - cuánto pesaba: hasta el 100 % de la parte simpática de llegada (64 lpm en 57m, 52 en 72f);
  - qué causaba: nunca se resolvía al resolverse el shock.
  Se eliminó; la parte del shock la genera ahora el estado actual.
- **Señal aguda explícita.** Es el déficit efectivo de oxígeno sobre la demanda:
  - vale 0 sin déficit;
  - no lee τ_D, lactato ni presión absoluta;
  - se resuelve con el déficit: 0 corridas con contribución aguda tras la adecuación;
  - por defecto la ganancia es 0 (apagada) y no se aprueba ninguna.
- **Escala de D respetada.** D × c con ganancia / c da la misma FC (brecha 2,8·10⁻¹⁴ lpm con c = 0,37 y 3). Ninguna D
  se usa como ancla aprobada.
- **Saturación suave.**
  - forma y propiedades: tanh sobre el incremento, sin recorte; monótona, continua, de pendiente 1 en 0;
  - frente a la intrínseca y el ritmo: nunca baja de la intrínseca y no toca el ritmo;
  - en la corrida extrema (techo 150): la FC máxima es 149,9999998 lpm.
  - el techo no se elige: 150 / 175 / 200 lpm es fisiología general y lo confirma la docencia.
- **Llegada predicha, desajuste informado.** 3240 descomposiciones analíticas y 0 rechazos:
  - mediana del desajuste: −24 lpm en 57m y −12 en 72f;
  - con ganancias comunes y los mismos niveles de llegada, la predicción es idéntica en ambos casos: la diferencia de
    12 lpm entre las FC registradas sólo puede venir de una intrínseca o de niveles de llegada propios de cada caso.
- **Invariantes y banderas.** Las doce direcciones se cumplen y no se levanta ninguna bandera estructural:
  - la reconstrucción coincide exactamente con 162 reejecuciones completas;
  - D, lactato y FR quedan idénticos al registro P2I-2AD.
- **Hallazgo para la docencia (§9, §11).** Tras los GR y la hemostasia (L3), la FC vuelve a la intrínseca desde el
  minuto 60 en casi todo el plano:
  - la causa: la presión queda sobre la de llegada y el término de presión relativa, negativo, cancela la parte de la
    deuda;
  - dónde se ve la taquicardia diferida: sólo con la mayor ganancia de deuda (36 de 432 lecturas en los minutos 90
    y 120);
  - qué mide la invariante 5: la parte de deuda del impulso, no la FC visible.
  Es una cuestión del dominio de la presión: el término queda como NEEDS_PRESSURE_DOMAIN_REVIEW.
- **Veredicto: HR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION**, con el diseño numérico docente preparado, no
  ejecutado (§16).
- Nada se seleccionó ni aprobó. La FR, la presión y el lactato no cambian.

## 1. Decisiones docentes y punto de partida

<!-- generado:decisiones -->
Congelamiento: `70106108285ced1556e746548fa79480d903a0495f6f65b6792cb17d9155eb2d` (una prueba lo fija). Registros de partida: P2I-2AD `5cb48163da4ff081e752b7684f4b036dbcf3e2acb4f94ee1603aaec742fe7fcf` y P2I-2AE `1b65d303831011014ca8cf8ce98e5fb880c5ea9cd3244f47773ce9d47b3712c8`.

| Decisión docente | Texto registrado |
|---|---|
| fecha | 2026-10-29 |
| shock recuperable | the shock part of arrival tachycardia is generated from the current state and resolves when shock resolves; no fixed case-specific offset; S0 is not forced to zero without replacing its causal role |
| señal aguda | the effective oxygen deficit (over demand) is the acute shock signal; no absolute-pressure reference; the relative-pressure term may stay if it does not double count (audited) |
| escala de D | D's absolute scale is not approved: debt_to_sympathetic_gain is read with it (D x c, gain / c leaves HR unchanged); the arrival-debt support is propagated uncertainty, never an anchor |
| saturación | a smooth monotone saturation of the sympathetic increment (no hard clip); no final reserve |
| intrínseca | 60 / 80 / 100 stays STILL_VALID_CANDIDATE_RANGE; no value approved; cancellation is not equivalence |
| alcance | shadow only; no pressure, RR or numeric HR calibration, no collapse, GI migration, second family or runtime integration; no hidden parameter approved |
<!-- /generado:decisiones -->

## 2. El resto de llegada (P2I-2AF-1)

Lectura del código de P2I-2AE y de su registro cerrado:

<!-- generado:resto -->
| Pregunta | Respuesta |
|---|---|
| dónde se guarda | no state variable: derived.arrival_non_debt_drive (P2I-2AE) recomputed every minute from the anchors and added as a constant to sympathetic_target; before P2I-2AE, S0 itself inside the target |
| cómo se calcula | S0 = (authored arrival HR - intrinsic) / (25 (1 - beta)), less debt_to_sympathetic_gain x D0: solved so that the arrival HR reproduces the authored one exactly (P2E-1, P2F-1, AC1) |
| ¿propio del caso? | sí |
| ¿persiste indefinidamente? | sí |
| quién lo lee | derived.sympathetic_target -> aux drive -> derive (sinus HR); derived.heart_rate_decomposition; derived.arrival_layers (sympathetic_drive, sympathetic_bpm); decision_pack._record (sympathetic_bpm); hr_structure (P2I-2AE) |
| clasificación | **CASE_CALIBRATION_OFFSET**: a per-case constant solved from the authored HR to force exact arrival matching; it has no dynamics, so the shock tachycardia it carried never resolved when the shock did |

Cuánto de la parte simpática de la FC de llegada sostenía el resto en P2I-2AE (sobre su soporte coherente):

| Caso | Fracción mín. | Fracción máx. | lpm mín. | lpm máx. | Intrínseca 80, D0 20 (lpm de resto / de la parte simpática, por ganancia) |
|---|---|---|---|---|---|
| 57m | 0 % | 100 % | 0,0 | 64,0 | 0: 44,0 / 44; 0,000667: 43,7 / 44; 0,00248: 42,8 / 44; 0,00924: 39,4 / 44; 0,0344: 26,8 / 44 |
| 72f | 1 % | 100 % | 0,4 | 52,0 | 0: 32,0 / 32; 0,000667: 31,7 / 32; 0,00248: 30,8 / 32; 0,00924: 27,4 / 32; 0,0344: 14,8 / 32 |
<!-- /generado:resto -->

## 3. La estructura nueva (P2I-2AF-2, P2I-2AF-3)

```
x        = déficit efectivo de oxígeno (demanda, entrega efectiva, reserva de extracción) / demanda
objetivo = max(0, k_A · x + a_P (1 − P_rel) + k_S · D + hipoxemia + hipoglucemia)
FC sinusal = intrínseca + HR_RESERVE · tanh(25 (1 − β) · impulso / HR_RESERVE),  HR_RESERVE = techo − intrínseca
FC de llegada = intrínseca + aguda + deuda + presión (0 en la llegada) + otros: predicha, nunca forzada
```

- El impulso sigue subiendo al instante y bajando con su constante (τ simpático), como antes.
- Sin resto, la FC registrada sólo se compara con la predicha (§5): el desajuste se informa.
- Valores por defecto, provisionales y no aprobados:
  - `acute_deficit_to_sympathetic_gain` = 0 (apagada);
  - `debt_to_sympathetic_gain` = 1/120;
  - `sinus_rate_ceiling_bpm` = 175.
- Con ellos, el golden directo sólo cambia en la metadata y el de Contracts v2 es IDÉNTICO: el golden no declara deuda
  ni entrega de llegada, así que su llegada no tiene parte simpática y su FC es la intrínseca, igual a la registrada.

<!-- generado:estructura -->
| Lectura del código vigente | Resultado |
|---|---|
| `arrival_solves_from_authored_hr` | no |
| `rr_reads_drive_or_rate` | no |
| `saturation_hard_clip` | no |
| `saturation_is_tanh` | sí |
| `sinus_rate_saturates` | sí |
| `target_reads_acute_gain` | sí |
| `target_reads_authored_hr` | no |
| `target_reads_debt_gain` | sí |
| `target_reads_effective_deficit` | sí |
| `target_reads_lactate` | no |
| `target_reads_residual` | no |
| `target_reads_tau_d` | no |
| `update_reads_tau_d` | no |

Sin resto: sí; término agudo: sí; τ_D fuera de la FC: sí; saturación suave: sí; la FR no lee la FC: sí.
<!-- /generado:estructura -->

## 4. Puntos candidatos predeclarados (P2I-2AF-5)

Fijados antes de cualquier corrida, sin leer el motor heredado ni ninguna trayectoria:

<!-- generado:candidatos -->
- `acute_deficit_to_sympathetic_gain`: de 0,1 a 21,3, puntos 0,1 · 0,382 · 1,46 · 5,58 · 21,3 y 0 (referencia sintética); soporte 0,15, 0,4.
- `debt_to_sympathetic_gain`: de 0,000667 a 0,16, puntos 0,000667 · 0,00262 · 0,0103 · 0,0407 · 0,16 y 0 (referencia sintética); soporte 20, 60.
- Techo sinusal: 150 / 175 / 200 lpm. Three sinus-rate ceilings, 150 / 175 / 200 bpm: the broad adult maximal-sinus-rate range (about 150 for an older adult to about 200 for a young adult, the span of the age-predicted maximum over adult ages; general physiology, not repository truth) and its midpoint. HR_RESERVE = ceiling - sinus base rate. Checked before any run: every ceiling lies above every authored GI arrival HR and every intrinsic level (the authored arrival stays reachable), and at every (ceiling, intrinsic) the smallest authored arrival sympathetic share is read almost linearly (saturation takes off less than the authored HR resolution, 1 bpm). Never read: legacy HR, any trajectory. Por encima de toda FC registrada y de toda intrínseca: sí; casi lineal en la menor parte simpática registrada (12 lpm, compresión máxima 0,225 lpm): sí.
- Ancla de los cortes (punto de lectura, no una selección): ganancia aguda 1,46, de deuda 0,0103, techo 175, intrínseca media.

Reglas:

- aguda: The candidate points of acute_deficit_to_sympathetic_gain (drive per unit of deficit / demand), predeclared from
    dimensional consistency (drive = gain x signal, 25 bpm per unit, ADOPTED), the authored arrival HR, the intrinsic
    band, the ceilings and the current arrival support of the signal (0.15 and 0.4; 0 adds nothing):
    - highest: the gain at which the acute signal alone carries an authored arrival share through the saturation, the
      maximum over cases, intrinsic levels, ceilings and non-zero signals of HR_RESERVE atanh(share / HR_RESERVE) /
      (25 x signal);
    - lowest: the largest arrival signal moves HR by the authored resolution, 1 / (25 x max signal).
    Five log-spaced points, both ends included; 0 a synthetic reference. Never read: tau_D, lactate, legacy, any run.
- deuda: The candidate points of debt_to_sympathetic_gain, by the same rule on the current arrival-debt support (20 and
    60). D's absolute scale is not approved: the support is propagated uncertainty, and the points mean nothing apart
    from it (D x c with gain / c is the same HR); they are reported with the HR increments they give.
<!-- /generado:candidatos -->

## 5. Llegada: descomposición y desajuste (P2I-2AF-4, P2I-2AF-6)

<!-- generado:llegada -->
Arrival mismatch = predicted arrival HR (intrinsic + the saturated acute and debt increments the arrival physiology produces, derived.heart_rate_decomposition) - authored arrival HR, in bpm, signed. No tolerance exists, so none is applied: the distribution is reported, binned by |mismatch| at 1 / 5 / 10 / 20 bpm for presentation only (1 bpm is the authored resolution). ANALYTIC_REJECTION only for a domain violation (a sinus base rate at or above the ceiling); a mismatch is never a rejection here.

| Caso | n | mín. | p10 | mediana | p90 | máx. | ≤ 1 | ≤ 5 | ≤ 10 | ≤ 20 | > 20 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 57m | 1620 | -64,0 | -63,0 | -24,0 | 37,3 | 76,0 | 10 | 41 | 128 | 123 | 1318 |
| 72f | 1620 | -52,0 | -51,0 | -12,0 | 49,3 | 88,0 | 9 | 92 | 115 | 343 | 1061 |

Desajuste en lpm (predicha − registrada). Rechazos analíticos: 0. Con ganancias comunes y los mismos niveles de llegada, la predicción es idéntica para ambos casos: sí. El menor «peor desajuste de los dos casos» sobre la superficie es 6,2 lpm con la misma intrínseca y 2,4 lpm si la intrínseca puede diferir por caso: sólo el valor, no se registra qué punto lo da ni se elige ninguno.

Descomposición a la intrínseca media, en el ancla de las ganancias y del techo, por par de llegada (deuda, entrega):

| Caso | Par | D0 | señal | aguda | deuda | presión + otros | saturado | predicha | desajuste |
|---|---|---|---|---|---|---|---|---|---|
| 57m | inferior / superior | 0 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 80,0 | -44,0 |
| 57m | medio / medio | 20 | 0,15 | 5,5 | 5,1 | 0,0 | 10,6 | 90,6 | -33,4 |
| 57m | superior / inferior | 60 | 0,40 | 14,1 | 15,0 | 0,0 | 29,1 | 109,1 | -14,9 |
| 57m | inferior / inferior | 0 | 0,40 | 14,5 | 0,0 | 0,0 | 14,5 | 94,5 | -29,5 |
| 57m | superior / superior | 60 | 0,00 | 0,0 | 15,4 | 0,0 | 15,4 | 95,4 | -28,6 |
| 72f | inferior / superior | 0 | 0,00 | 0,0 | 0,0 | 0,0 | 0,0 | 80,0 | -32,0 |
| 72f | medio / medio | 20 | 0,15 | 5,5 | 5,1 | 0,0 | 10,6 | 90,6 | -21,4 |
| 72f | superior / inferior | 60 | 0,40 | 14,1 | 15,0 | 0,0 | 29,1 | 109,1 | -2,9 |
| 72f | inferior / inferior | 0 | 0,40 | 14,5 | 0,0 | 0,0 | 14,5 | 94,5 | -17,5 |
| 72f | superior / superior | 60 | 0,00 | 0,0 | 15,4 | 0,0 | 15,4 | 95,4 | -16,6 |
<!-- /generado:llegada -->

## 6. Trayectorias H1–H4 (P2I-2AF-7)

Representantes LOW / MID / HIGH de P2I-2AD (su registro), en el ancla de lectura:

<!-- generado:trayectorias -->
On each of the 18 representative runs (3 tags x 2 cases x L1 / L2 / L3), post-processed, no further simulation: the one-dimensional slices through the anchor (acute gain over its five points and 0; debt gain likewise; ceiling 150 / 175 / 200; intrinsic lower / midpoint / upper) and the acute x debt plane (6 x 6) at the anchor's ceiling and intrinsic. The anchor is a reading point, not a selection. No Cartesian product with blood, fluid or lactate.

En el ancla; aguda y deuda sin saturar, y su suma saturada (lpm). FC = intrínseca + saturado. Hemostasia en el minuto 60 de L3.

### H1: untreated active bleed (L1)

**57m**

| Rep. | Min | FC | intr. | aguda | deuda | presión | sin sat. | saturado | déficit | D | gasto | sangrado | GR (U) | cristaloide |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | 0 | 94,5 | 80 | 14,6 | 0,0 | 0,0 | 14,6 | 14,5 | 0,400 | 0,0 | 1,00 | 2,50 | 0,00 | 0 |
| LOW | 15 | 98,2 | 80 | 16,0 | 0,8 | 1,6 | 18,4 | 18,2 | 0,438 | 3,1 | 0,94 | 2,50 | 0,00 | 0 |
| LOW | 30 | 101,9 | 80 | 17,4 | 1,7 | 3,2 | 22,3 | 21,9 | 0,477 | 6,6 | 0,87 | 2,50 | 0,00 | 0 |
| LOW | 60 | 109,4 | 80 | 20,3 | 3,7 | 6,4 | 30,4 | 29,4 | 0,555 | 14,3 | 0,74 | 2,50 | 0,00 | 0 |
| LOW | 90 | 116,9 | 80 | 23,2 | 6,0 | 9,7 | 38,9 | 36,9 | 0,636 | 23,2 | 0,61 | 2,50 | 0,00 | 0 |
| LOW | 120 | 124,2 | 80 | 26,2 | 8,6 | 13,1 | 47,9 | 44,2 | 0,717 | 33,3 | 0,48 | 2,50 | 0,00 | 0 |
| MID | 0 | 90,6 | 80 | 5,5 | 5,2 | 0,0 | 10,6 | 10,6 | 0,150 | 20,0 | 1,00 | 5,00 | 0,00 | 0 |
| MID | 15 | 94,0 | 80 | 7,0 | 5,8 | 1,2 | 14,1 | 14,0 | 0,193 | 22,5 | 0,95 | 5,00 | 0,00 | 0 |
| MID | 30 | 97,6 | 80 | 8,6 | 6,6 | 2,5 | 17,8 | 17,6 | 0,236 | 25,7 | 0,90 | 5,00 | 0,00 | 0 |
| MID | 60 | 105,0 | 80 | 11,8 | 8,8 | 4,9 | 25,6 | 25,0 | 0,324 | 34,1 | 0,80 | 5,00 | 0,00 | 0 |
| MID | 90 | 112,6 | 80 | 15,1 | 11,7 | 7,3 | 34,0 | 32,6 | 0,412 | 45,1 | 0,71 | 5,00 | 0,00 | 0 |
| MID | 120 | 120,4 | 80 | 18,3 | 15,2 | 9,7 | 43,1 | 40,4 | 0,500 | 58,8 | 0,61 | 5,00 | 0,00 | 0 |
| HIGH | 0 | 95,4 | 80 | 0,0 | 15,5 | 0,0 | 15,5 | 15,4 | 0,000 | 60,0 | 1,00 | 2,50 | 0,00 | 0 |
| HIGH | 15 | 99,3 | 80 | 2,3 | 15,7 | 1,6 | 19,6 | 19,3 | 0,063 | 60,9 | 0,94 | 2,50 | 0,00 | 0 |
| HIGH | 30 | 103,8 | 80 | 4,7 | 16,4 | 3,2 | 24,3 | 23,8 | 0,128 | 63,7 | 0,87 | 2,50 | 0,00 | 0 |
| HIGH | 60 | 113,8 | 80 | 9,5 | 19,4 | 6,4 | 35,4 | 33,8 | 0,260 | 75,2 | 0,74 | 2,50 | 0,00 | 0 |
| HIGH | 90 | 124,8 | 80 | 14,4 | 24,5 | 9,7 | 48,6 | 44,8 | 0,395 | 94,7 | 0,61 | 2,50 | 0,00 | 0 |
| HIGH | 120 | 135,9 | 80 | 19,4 | 31,6 | 13,1 | 64,1 | 55,9 | 0,531 | 122,3 | 0,48 | 2,50 | 0,00 | 0 |

**72f**

| Rep. | Min | FC | intr. | aguda | deuda | presión | sin sat. | saturado | déficit | D | gasto | sangrado | GR (U) | cristaloide |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | 0 | 94,5 | 80 | 14,6 | 0,0 | 0,0 | 14,6 | 14,5 | 0,400 | 0,0 | 1,00 | 2,50 | 0,00 | 0 |
| LOW | 15 | 97,2 | 80 | 15,5 | 0,8 | 1,1 | 17,4 | 17,2 | 0,425 | 3,1 | 0,96 | 2,50 | 0,00 | 0 |
| LOW | 30 | 99,9 | 80 | 16,5 | 1,6 | 2,1 | 20,2 | 19,9 | 0,451 | 6,4 | 0,92 | 2,50 | 0,00 | 0 |
| LOW | 60 | 105,5 | 80 | 18,4 | 3,5 | 4,3 | 26,2 | 25,5 | 0,504 | 13,5 | 0,83 | 2,50 | 0,00 | 0 |
| LOW | 90 | 111,2 | 80 | 20,4 | 5,5 | 6,5 | 32,4 | 31,2 | 0,558 | 21,5 | 0,74 | 2,50 | 0,00 | 0 |
| LOW | 120 | 116,9 | 80 | 22,4 | 7,8 | 8,7 | 38,9 | 36,9 | 0,613 | 30,2 | 0,65 | 2,50 | 0,00 | 0 |
| MID | 0 | 90,6 | 80 | 5,5 | 5,2 | 0,0 | 10,6 | 10,6 | 0,150 | 20,0 | 1,00 | 5,00 | 0,00 | 0 |
| MID | 15 | 93,1 | 80 | 6,5 | 5,8 | 0,8 | 13,2 | 13,1 | 0,179 | 22,5 | 0,97 | 5,00 | 0,00 | 0 |
| MID | 30 | 95,7 | 80 | 7,6 | 6,5 | 1,7 | 15,8 | 15,7 | 0,208 | 25,3 | 0,93 | 5,00 | 0,00 | 0 |
| MID | 60 | 101,1 | 80 | 9,8 | 8,4 | 3,3 | 21,5 | 21,1 | 0,269 | 32,5 | 0,87 | 5,00 | 0,00 | 0 |
| MID | 90 | 106,9 | 80 | 12,1 | 10,7 | 4,9 | 27,7 | 26,9 | 0,332 | 41,4 | 0,81 | 5,00 | 0,00 | 0 |
| MID | 120 | 112,9 | 80 | 14,4 | 13,5 | 6,4 | 34,4 | 32,9 | 0,395 | 52,3 | 0,74 | 5,00 | 0,00 | 0 |
| HIGH | 0 | 95,4 | 80 | 0,0 | 15,5 | 0,0 | 15,5 | 15,4 | 0,000 | 60,0 | 1,00 | 2,50 | 0,00 | 0 |
| HIGH | 15 | 98,0 | 80 | 1,5 | 15,6 | 1,1 | 18,2 | 18,0 | 0,042 | 60,6 | 0,96 | 2,50 | 0,00 | 0 |
| HIGH | 30 | 101,0 | 80 | 3,1 | 16,1 | 2,1 | 21,4 | 21,0 | 0,086 | 62,5 | 0,92 | 2,50 | 0,00 | 0 |
| HIGH | 60 | 107,9 | 80 | 6,4 | 18,1 | 4,3 | 28,8 | 27,9 | 0,175 | 70,2 | 0,83 | 2,50 | 0,00 | 0 |
| HIGH | 90 | 115,9 | 80 | 9,7 | 21,5 | 6,5 | 37,7 | 35,9 | 0,267 | 83,3 | 0,74 | 2,50 | 0,00 | 0 |
| HIGH | 120 | 124,4 | 80 | 13,1 | 26,3 | 8,7 | 48,2 | 44,4 | 0,360 | 102,0 | 0,65 | 2,50 | 0,00 | 0 |

### H2: crystalloid 2 L over 20 min with continued bleeding (L2)

**57m**

| Rep. | Min | FC | intr. | aguda | deuda | presión | sin sat. | saturado | déficit | D | gasto | sangrado | GR (U) | cristaloide |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | 0 | 94,5 | 80 | 14,6 | 0,0 | 0,0 | 14,6 | 14,5 | 0,400 | 0,0 | 1,00 | 2,50 | 0,00 | 0 |
| LOW | 15 | 84,7 | 80 | 9,0 | 0,6 | -8,1 | 4,7 | 4,7 | 0,247 | 2,4 | 1,32 | 2,50 | 0,00 | 300 |
| LOW | 30 | 82,0 | 80 | 9,1 | 1,1 | -8,2 | 2,0 | 2,0 | 0,250 | 4,1 | 1,33 | 2,50 | 0,00 | 400 |
| LOW | 60 | 92,0 | 80 | 13,0 | 2,2 | -3,1 | 12,1 | 12,0 | 0,355 | 8,6 | 1,12 | 2,50 | 0,00 | 400 |
| LOW | 90 | 101,9 | 80 | 16,8 | 3,8 | 1,7 | 22,3 | 21,9 | 0,460 | 14,7 | 0,93 | 2,50 | 0,00 | 400 |
| LOW | 120 | 110,5 | 80 | 20,2 | 5,8 | 5,7 | 31,6 | 30,5 | 0,552 | 22,3 | 0,77 | 2,50 | 0,00 | 400 |
| MID | 0 | 90,6 | 80 | 5,5 | 5,2 | 0,0 | 10,6 | 10,6 | 0,150 | 20,0 | 1,00 | 5,00 | 0,00 | 0 |
| MID | 15 | 88,1 | 80 | 4,6 | 5,7 | -3,0 | 8,1 | 8,1 | 0,127 | 22,0 | 1,12 | 5,00 | 0,00 | 300 |
| MID | 30 | 89,4 | 80 | 5,6 | 6,2 | -2,4 | 9,4 | 9,4 | 0,154 | 24,1 | 1,10 | 5,00 | 0,00 | 400 |
| MID | 60 | 97,3 | 80 | 8,9 | 7,7 | 0,9 | 17,5 | 17,3 | 0,243 | 30,0 | 0,96 | 5,00 | 0,00 | 400 |
| MID | 90 | 104,5 | 80 | 11,8 | 9,9 | 3,3 | 25,0 | 24,5 | 0,323 | 38,4 | 0,87 | 5,00 | 0,00 | 400 |
| MID | 120 | 111,6 | 80 | 14,6 | 12,7 | 5,5 | 32,8 | 31,6 | 0,399 | 49,2 | 0,78 | 5,00 | 0,00 | 400 |
| HIGH | 0 | 95,4 | 80 | 0,0 | 15,5 | 0,0 | 15,5 | 15,4 | 0,000 | 60,0 | 1,00 | 2,50 | 0,00 | 0 |
| HIGH | 15 | 84,5 | 80 | 0,0 | 9,3 | -8,6 | 4,5 | 4,5 | 0,000 | 36,1 | 1,35 | 2,50 | 0,00 | 300 |
| HIGH | 30 | 80,2 | 80 | 0,0 | 5,6 | -9,8 | 0,2 | 0,2 | 0,000 | 21,7 | 1,39 | 2,50 | 0,00 | 400 |
| HIGH | 60 | 80,0 | 80 | 0,0 | 2,0 | -6,9 | 0,0 | 0,0 | 0,000 | 7,8 | 1,27 | 2,50 | 0,00 | 400 |
| HIGH | 90 | 80,0 | 80 | 0,0 | 0,7 | -3,6 | 0,0 | 0,0 | 0,000 | 2,8 | 1,14 | 2,50 | 0,00 | 400 |
| HIGH | 120 | 84,7 | 80 | 3,5 | 1,1 | 0,1 | 4,7 | 4,7 | 0,095 | 4,1 | 0,99 | 2,50 | 0,00 | 400 |

**72f**

| Rep. | Min | FC | intr. | aguda | deuda | presión | sin sat. | saturado | déficit | D | gasto | sangrado | GR (U) | cristaloide |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | 0 | 94,5 | 80 | 14,6 | 0,0 | 0,0 | 14,6 | 14,5 | 0,400 | 0,0 | 1,00 | 2,50 | 0,00 | 0 |
| LOW | 15 | 88,5 | 80 | 11,3 | 0,7 | -5,4 | 8,5 | 8,5 | 0,308 | 2,6 | 1,22 | 2,50 | 0,00 | 300 |
| LOW | 30 | 87,2 | 80 | 11,4 | 1,3 | -5,5 | 7,2 | 7,2 | 0,312 | 4,9 | 1,22 | 2,50 | 0,00 | 400 |
| LOW | 60 | 94,2 | 80 | 13,8 | 2,6 | -2,1 | 14,3 | 14,2 | 0,379 | 10,0 | 1,08 | 2,50 | 0,00 | 400 |
| LOW | 90 | 101,3 | 80 | 16,3 | 4,2 | 1,1 | 21,7 | 21,3 | 0,447 | 16,2 | 0,96 | 2,50 | 0,00 | 400 |
| LOW | 120 | 107,6 | 80 | 18,6 | 6,0 | 3,8 | 28,4 | 27,6 | 0,508 | 23,4 | 0,85 | 2,50 | 0,00 | 400 |
| MID | 0 | 90,6 | 80 | 5,5 | 5,2 | 0,0 | 10,6 | 10,6 | 0,150 | 20,0 | 1,00 | 5,00 | 0,00 | 0 |
| MID | 15 | 89,7 | 80 | 5,8 | 5,8 | -2,0 | 9,8 | 9,7 | 0,158 | 22,3 | 1,08 | 5,00 | 0,00 | 300 |
| MID | 30 | 91,3 | 80 | 6,5 | 6,4 | -1,6 | 11,3 | 11,3 | 0,179 | 24,8 | 1,06 | 5,00 | 0,00 | 400 |
| MID | 60 | 96,9 | 80 | 8,5 | 8,0 | 0,6 | 17,1 | 16,9 | 0,233 | 30,9 | 0,98 | 5,00 | 0,00 | 400 |
| MID | 90 | 102,3 | 80 | 10,5 | 10,0 | 2,2 | 22,7 | 22,3 | 0,288 | 38,7 | 0,91 | 5,00 | 0,00 | 400 |
| MID | 120 | 107,8 | 80 | 12,5 | 12,4 | 3,7 | 28,6 | 27,8 | 0,343 | 48,2 | 0,85 | 5,00 | 0,00 | 400 |
| HIGH | 0 | 95,4 | 80 | 0,0 | 15,5 | 0,0 | 15,5 | 15,4 | 0,000 | 60,0 | 1,00 | 2,50 | 0,00 | 0 |
| HIGH | 15 | 86,6 | 80 | 0,0 | 9,3 | -5,8 | 6,6 | 6,6 | 0,000 | 36,1 | 1,23 | 2,50 | 0,00 | 300 |
| HIGH | 30 | 80,5 | 80 | 0,0 | 5,6 | -6,6 | 0,5 | 0,5 | 0,000 | 21,7 | 1,26 | 2,50 | 0,00 | 400 |
| HIGH | 60 | 80,0 | 80 | 0,0 | 2,0 | -4,6 | 0,0 | 0,0 | 0,000 | 7,8 | 1,18 | 2,50 | 0,00 | 400 |
| HIGH | 90 | 80,0 | 80 | 0,4 | 0,8 | -2,4 | 0,0 | 0,0 | 0,010 | 3,3 | 1,09 | 2,50 | 0,00 | 400 |
| HIGH | 120 | 85,1 | 80 | 3,4 | 1,6 | 0,1 | 5,1 | 5,1 | 0,093 | 6,2 | 1,00 | 2,50 | 0,00 | 400 |

### H3: PRBC before haemostasis (L3, 2 units over 0-60 min, PPI)

**57m**

| Rep. | Min | FC | intr. | aguda | deuda | presión | sin sat. | saturado | déficit | D | gasto | sangrado | GR (U) | cristaloide |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | 0 | 94,5 | 80 | 14,6 | 0,0 | 0,0 | 14,6 | 14,5 | 0,400 | 0,0 | 1,00 | 2,00 | 0,00 | 0 |
| LOW | 15 | 87,8 | 80 | 9,1 | 0,6 | -4,5 | 7,9 | 7,8 | 0,250 | 2,5 | 1,18 | 2,00 | 0,50 | 0 |
| LOW | 30 | 80,8 | 80 | 4,1 | 1,0 | -8,2 | 0,8 | 0,8 | 0,112 | 3,9 | 1,33 | 2,00 | 1,00 | 0 |
| LOW | 60 | 80,0 | 80 | 0,0 | 0,6 | -13,8 | 0,0 | 0,0 | 0,000 | 2,5 | 1,55 | 0,25 | 2,00 | 0 |
| MID | 0 | 90,6 | 80 | 5,5 | 5,2 | 0,0 | 10,6 | 10,6 | 0,150 | 20,0 | 1,00 | 4,00 | 0,00 | 0 |
| MID | 15 | 87,7 | 80 | 2,0 | 5,6 | -1,1 | 7,7 | 7,7 | 0,054 | 21,6 | 1,04 | 4,00 | 0,50 | 0 |
| MID | 30 | 83,6 | 80 | 0,0 | 4,6 | -2,1 | 3,6 | 3,6 | 0,000 | 17,8 | 1,08 | 4,00 | 1,00 | 0 |
| MID | 60 | 80,0 | 80 | 0,0 | 1,7 | -4,0 | 0,0 | 0,0 | 0,000 | 6,4 | 1,16 | 0,50 | 2,00 | 0 |
| HIGH | 0 | 95,4 | 80 | 0,0 | 15,5 | 0,0 | 15,5 | 15,4 | 0,000 | 60,0 | 1,00 | 2,00 | 0,00 | 0 |
| HIGH | 15 | 88,2 | 80 | 0,0 | 9,3 | -3,7 | 8,2 | 8,2 | 0,000 | 36,1 | 1,15 | 2,00 | 0,50 | 0 |
| HIGH | 30 | 81,1 | 80 | 0,0 | 5,6 | -6,8 | 1,1 | 1,1 | 0,000 | 21,7 | 1,27 | 2,00 | 1,00 | 0 |
| HIGH | 60 | 80,0 | 80 | 0,0 | 2,0 | -11,8 | 0,0 | 0,0 | 0,000 | 7,8 | 1,47 | 0,25 | 2,00 | 0 |

**72f**

| Rep. | Min | FC | intr. | aguda | deuda | presión | sin sat. | saturado | déficit | D | gasto | sangrado | GR (U) | cristaloide |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | 0 | 94,5 | 80 | 14,6 | 0,0 | 0,0 | 14,6 | 14,5 | 0,400 | 0,0 | 1,00 | 2,00 | 0,00 | 0 |
| LOW | 15 | 89,9 | 80 | 10,4 | 0,7 | -3,0 | 9,9 | 9,9 | 0,286 | 2,6 | 1,12 | 2,00 | 0,50 | 0 |
| LOW | 30 | 83,9 | 80 | 6,6 | 1,1 | -5,5 | 3,9 | 3,9 | 0,180 | 4,4 | 1,22 | 2,00 | 1,00 | 0 |
| LOW | 60 | 80,0 | 80 | 0,0 | 1,4 | -9,2 | 0,0 | 0,0 | 0,000 | 5,5 | 1,37 | 0,25 | 2,00 | 0 |
| MID | 0 | 90,6 | 80 | 5,5 | 5,2 | 0,0 | 10,6 | 10,6 | 0,150 | 20,0 | 1,00 | 4,00 | 0,00 | 0 |
| MID | 15 | 88,1 | 80 | 2,3 | 5,6 | -0,7 | 8,2 | 8,1 | 0,062 | 21,6 | 1,03 | 4,00 | 0,50 | 0 |
| MID | 30 | 84,6 | 80 | 0,0 | 5,0 | -1,4 | 4,6 | 4,6 | 0,000 | 19,2 | 1,06 | 4,00 | 1,00 | 0 |
| MID | 60 | 80,1 | 80 | 0,0 | 1,8 | -2,7 | 0,1 | 0,1 | 0,000 | 6,9 | 1,11 | 0,50 | 2,00 | 0 |
| HIGH | 0 | 95,4 | 80 | 0,0 | 15,5 | 0,0 | 15,5 | 15,4 | 0,000 | 60,0 | 1,00 | 2,00 | 0,00 | 0 |
| HIGH | 15 | 89,1 | 80 | 0,0 | 9,3 | -2,4 | 9,1 | 9,1 | 0,000 | 36,1 | 1,10 | 2,00 | 0,50 | 0 |
| HIGH | 30 | 82,7 | 80 | 0,0 | 5,6 | -4,5 | 2,7 | 2,7 | 0,000 | 21,7 | 1,18 | 2,00 | 1,00 | 0 |
| HIGH | 60 | 80,0 | 80 | 0,0 | 2,0 | -7,8 | 0,0 | 0,0 | 0,000 | 7,8 | 1,31 | 0,25 | 2,00 | 0 |

### H4: definitive management: haemostasis at 60 and restored adequacy (L3, 60-120 min)

**57m**

| Rep. | Min | FC | intr. | aguda | deuda | presión | sin sat. | saturado | déficit | D | gasto | sangrado | GR (U) | cristaloide |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | 60 | 80,0 | 80 | 0,0 | 0,6 | -13,8 | 0,0 | 0,0 | 0,000 | 2,5 | 1,55 | 0,25 | 2,00 | 0 |
| LOW | 90 | 80,0 | 80 | 0,0 | 0,2 | -13,7 | 0,0 | 0,0 | 0,000 | 0,9 | 1,55 | 0,25 | 2,00 | 0 |
| LOW | 120 | 80,0 | 80 | 0,0 | 0,1 | -13,5 | 0,0 | 0,0 | 0,000 | 0,3 | 1,54 | 0,25 | 2,00 | 0 |
| MID | 60 | 80,0 | 80 | 0,0 | 1,7 | -4,0 | 0,0 | 0,0 | 0,000 | 6,4 | 1,16 | 0,50 | 2,00 | 0 |
| MID | 90 | 80,0 | 80 | 0,0 | 0,6 | -3,8 | 0,0 | 0,0 | 0,000 | 2,3 | 1,15 | 0,50 | 2,00 | 0 |
| MID | 120 | 80,0 | 80 | 0,0 | 0,2 | -3,6 | 0,0 | 0,0 | 0,000 | 0,8 | 1,14 | 0,50 | 2,00 | 0 |
| HIGH | 60 | 80,0 | 80 | 0,0 | 2,0 | -11,8 | 0,0 | 0,0 | 0,000 | 7,8 | 1,47 | 0,25 | 2,00 | 0 |
| HIGH | 90 | 80,0 | 80 | 0,0 | 0,7 | -11,6 | 0,0 | 0,0 | 0,000 | 2,8 | 1,46 | 0,25 | 2,00 | 0 |
| HIGH | 120 | 80,0 | 80 | 0,0 | 0,3 | -11,4 | 0,0 | 0,0 | 0,000 | 1,0 | 1,46 | 0,25 | 2,00 | 0 |

**72f**

| Rep. | Min | FC | intr. | aguda | deuda | presión | sin sat. | saturado | déficit | D | gasto | sangrado | GR (U) | cristaloide |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | 60 | 80,0 | 80 | 0,0 | 1,4 | -9,2 | 0,0 | 0,0 | 0,000 | 5,5 | 1,37 | 0,25 | 2,00 | 0 |
| LOW | 90 | 80,0 | 80 | 0,0 | 0,5 | -9,1 | 0,0 | 0,0 | 0,000 | 2,0 | 1,36 | 0,25 | 2,00 | 0 |
| LOW | 120 | 80,0 | 80 | 0,0 | 0,2 | -9,0 | 0,0 | 0,0 | 0,000 | 0,7 | 1,36 | 0,25 | 2,00 | 0 |
| MID | 60 | 80,1 | 80 | 0,0 | 1,8 | -2,7 | 0,1 | 0,1 | 0,000 | 6,9 | 1,11 | 0,50 | 2,00 | 0 |
| MID | 90 | 80,0 | 80 | 0,0 | 0,6 | -2,5 | 0,0 | 0,0 | 0,000 | 2,5 | 1,10 | 0,50 | 2,00 | 0 |
| MID | 120 | 80,0 | 80 | 0,0 | 0,2 | -2,4 | 0,0 | 0,0 | 0,000 | 0,9 | 1,10 | 0,50 | 2,00 | 0 |
| HIGH | 60 | 80,0 | 80 | 0,0 | 2,0 | -7,8 | 0,0 | 0,0 | 0,000 | 7,8 | 1,31 | 0,25 | 2,00 | 0 |
| HIGH | 90 | 80,0 | 80 | 0,0 | 0,7 | -7,7 | 0,0 | 0,0 | 0,000 | 2,8 | 1,31 | 0,25 | 2,00 | 0 |
| HIGH | 120 | 80,0 | 80 | 0,0 | 0,3 | -7,6 | 0,0 | 0,0 | 0,000 | 1,0 | 1,30 | 0,25 | 2,00 | 0 |

<!-- /generado:trayectorias -->

## 7. Sondas H5 (P2I-2AF-7, -8, -11)

<!-- generado:sondas -->
| Caso | Sonda | Se cumple |
|---|---|---|
| 57m | más déficit (Hb menor), todo lo demás fijo | sí |
| 57m | más D, todo lo demás fijo | sí |
| 57m | τ_D con D fija | sí |
| 57m | sin déficit, sin contribución aguda | sí |
| 57m | ritmo: marcapasos y AESP | sí |
| 57m | cristaloide 500 mL con bomba 1,0 / 0,7 (ΔFC a 30 min) | -11,7 / -23,4 lpm |
| 57m | 1 U de GR con bomba 1,0 / 0,7 (ΔFC a 30 min) | -11,7 / -20,6 lpm |
| 72f | más déficit (Hb menor), todo lo demás fijo | sí |
| 72f | más D, todo lo demás fijo | sí |
| 72f | τ_D con D fija | sí |
| 72f | sin déficit, sin contribución aguda | sí |
| 72f | ritmo: marcapasos y AESP | sí |
| 72f | cristaloide 500 mL con bomba 1,0 / 0,7 (ΔFC a 30 min) | -11,7 / -13,5 lpm |
| 72f | 1 U de GR con bomba 1,0 / 0,7 (ΔFC a 30 min) | -11,6 / -14,2 lpm |

El cristaloide y los GR actúan por la fisiología: sí / sí. Escala de D: FC igual con D × c y ganancia / c sí (brecha máx. 2,84e-14, 2,84e-14 lpm). La FC registrada no llega a la dinámica: sí. Llegada no sinusal o con betabloqueo completo y deuda (TD-93(5)): GENERALIZATION_BLOCKER_ONLY, RESOLVED_BY_P2I2AF; afecta a GI: no.
<!-- /generado:sondas -->

## 8. Saturación H6

<!-- generado:saturacion -->
| Techo · intrínseca | Reserva | Máx. (impulso 20) | Monótona | Sin saltos | Pendiente en 0 | Con impulso 2 (lineal 50) |
|---|---|---|---|---|---|---|
| 150 · inferior | 90 | 90,00 | sí | sí | 1,0000 | 45,4 |
| 150 · medio | 70 | 70,00 | sí | sí | 1,0000 | 42,9 |
| 150 · superior | 50 | 50,00 | sí | sí | 1,0000 | 38,1 |
| 175 · inferior | 115 | 114,96 | sí | sí | 1,0000 | 47,1 |
| 175 · medio | 95 | 94,99 | sí | sí | 1,0000 | 45,8 |
| 175 · superior | 75 | 75,00 | sí | sí | 1,0000 | 43,7 |
| 200 · inferior | 140 | 139,78 | sí | sí | 1,0000 | 48,0 |
| 200 · medio | 120 | 119,94 | sí | sí | 1,0000 | 47,3 |
| 200 · superior | 100 | 99,99 | sí | sí | 1,0000 | 46,2 |

H6, corrida extrema (57m, intrínseca 60, deuda 60, entrega inferior, ganancias en su máximo, techo 150, bomba cayendo 100 min): FC 150,0 → 150,0 → 150,0, máxima 150,00, mayor cambio por minuto 0,00 lpm; bajo el techo: sí. Se cumple: sí.
<!-- /generado:saturacion -->

## 9. Invariantes y banderas (P2I-2AF-8)

<!-- generado:invariantes -->
| # | Dirección | Resultado |
|---|---|---|
| 1 | a larger effective deficit, all else fixed, never lowers HR | PASA |
| 2 | a larger D, all else fixed, never lowers HR | PASA |
| 3 | tau_D at fixed D leaves HR unchanged | PASA |
| 4 | the acute contribution resolves when the effective deficit resolves | PASA |
| 5 | D may keep a delayed tachycardia after the acute deficit resolves | PASA |
| 6 | as D repays, the debt-driven contribution may fall | PASA |
| 7 | haemostasis alone does not instantly normalize HR | PASA |
| 8 | the crystalloid effect arises through physiology, not fluid identity | PASA |
| 9 | the PRBC effect arises through physiology, not a fixed HR decrement | PASA |
| 10 | high sympathetic drive approaches saturation smoothly | PASA |
| 11 | no discontinuous HR jump at saturation | PASA |
| 12 | the intrinsic rhythm and the rhythm state remain authoritative | PASA |

Corridas L3 con T*: 240; con deuda positiva y D(T*) > 0: 204; menor margen sobre la intrínseca un minuto después de la hemostasia: 0,00 lpm. Structural flags only, declared before any run; no bpm threshold (none is committed). Magnitudes and the arrival mismatch are reported on the decision surface for the faculty.

| Bandera estructural | Corridas |
|---|---|
| ACUTE_PERSISTS_AFTER_ADEQUACY | 0 |
| ACUTE_WITHOUT_DEFICIT | 0 |
| DRIVE_FALLS_FASTER_THAN_ITS_DECAY | 0 |
| HR_ABOVE_CEILING | 0 |
| HR_BELOW_INTRINSIC | 0 |
| INSTANT_NORMALIZATION_AT_HAEMOSTASIS | 0 |
| NEGATIVE_INCREMENT | 0 |
| NO_DEBT_RECOVERY_AFTER_ADEQUACY | 0 |
<!-- /generado:invariantes -->

Lectura descriptiva del registro, posterior al veredicto y sin cambiarlo:
- La invariante 5 («D puede mantener una taquicardia diferida») se comprueba sobre la parte de deuda del impulso en
  T\*: es positiva en las 204 corridas con deuda.
- La FC visible es otra cosa. En L3, la parte de presión relativa se vuelve negativa (presión sobre la de llegada, tras
  los GR) y anula la de deuda; el objetivo queda en 0 y la FC en la intrínseca desde el minuto 60. Ejemplo en el ancla
  (§6, H4), en lpm sin saturar al minuto 60:
  - 57m HIGH: deuda 2,0 y presión −11,8;
  - 72f MID: deuda 1,8 y presión −2,7.
- En la superficie (§10), una FC más de 0,5 lpm sobre la intrínseca en los minutos 90 y 120 de L3 sólo aparece con la
  mayor ganancia de deuda (0,160): 36 de 432 lecturas (caso × hito × punto del plano × representante).
- Por lo mismo, la invariante 7 («la hemostasia sola no normaliza la FC al instante») se cumple porque la FC ya está en
  la intrínseca antes de la hemostasia: el menor margen un minuto después es 0 lpm.
- Que la estructura permita la taquicardia diferida no significa que se vea. Que se vea depende de la ganancia de
  deuda y del término de presión (§11). Es una decisión del dominio de la presión y del paquete numérico, no de este.

## 10. Superficie de decisión

<!-- generado:superficie -->
no committed numeric HR band exists; nothing here is an envelope or a target. Intrínseca media y techo 175; cada celda: FC de LOW / MID / HIGH (lpm); filas: ganancia aguda; columnas: ganancia de deuda.

**57m · arrival (L1, 0)**

| aguda \ deuda | 0,000667 | 0,00262 | 0,0103 | 0,0407 | 0,16 | 0 |
|---|---|---|---|---|---|---|
| 0,1 | 81 / 81 / 81 | 81 / 82 / 84 | 81 / 86 / 95 | 81 / 100 / 134 | 81 / 145 / 174 | 81 / 80 / 80 |
| 0,382 | 84 / 82 / 81 | 84 / 83 / 84 | 84 / 87 / 95 | 84 / 101 / 134 | 84 / 146 / 174 | 84 / 81 / 80 |
| 1,46 | 94 / 86 / 81 | 94 / 87 / 84 | 94 / 91 / 95 | 94 / 105 / 134 | 94 / 148 / 174 | 94 / 85 / 80 |
| 5,58 | 130 / 101 / 81 | 130 / 102 / 84 | 130 / 105 / 95 | 130 / 119 / 134 | 130 / 155 / 174 | 130 / 101 / 80 |
| 21,3 | 173 / 145 / 81 | 173 / 146 / 84 | 173 / 148 / 95 | 173 / 155 / 134 | 173 / 169 / 174 | 173 / 145 / 80 |
| 0 | 80 / 80 / 81 | 80 / 81 / 84 | 80 / 85 / 95 | 80 / 100 / 134 | 80 / 145 / 174 | 80 / 80 / 80 |

**57m · untreated_120 (L1, 120)**

| aguda \ deuda | 0,000667 | 0,00262 | 0,0103 | 0,0407 | 0,16 | 0 |
|---|---|---|---|---|---|---|
| 0,1 | 95 / 92 / 96 | 97 / 95 / 102 | 103 / 105 / 123 | 125 / 140 / 165 | 167 / 174 / 175 | 95 / 91 / 94 |
| 0,382 | 100 / 95 / 100 | 102 / 98 / 106 | 108 / 109 / 126 | 129 / 142 / 166 | 168 / 174 / 175 | 100 / 94 / 98 |
| 1,46 | 118 / 108 / 113 | 119 / 111 / 118 | 124 / 120 / 136 | 141 / 149 / 168 | 170 / 174 / 175 | 117 / 107 / 111 |
| 5,58 | 159 / 145 / 150 | 160 / 147 / 152 | 161 / 152 / 161 | 167 / 165 / 173 | 174 / 175 / 175 | 159 / 145 / 149 |
| 21,3 | 175 / 174 / 175 | 175 / 174 / 175 | 175 / 175 / 175 | 175 / 175 / 175 | 175 / 175 / 175 | 175 / 174 / 175 |
| 0 | 94 / 91 / 95 | 95 / 93 / 101 | 101 / 104 / 122 | 123 / 139 / 165 | 167 / 174 / 175 | 93 / 90 / 93 |

**57m · crystalloid_120 (L2, 120)**

| aguda \ deuda | 0,000667 | 0,00262 | 0,0103 | 0,0407 | 0,16 | 0 |
|---|---|---|---|---|---|---|
| 0,1 | 87 / 87 / 80 | 89 / 90 / 81 | 93 / 99 / 81 | 109 / 131 / 85 | 153 / 172 / 97 | 87 / 86 / 80 |
| 0,382 | 91 / 90 / 81 | 92 / 92 / 81 | 97 / 102 / 82 | 112 / 133 / 85 | 154 / 173 / 97 | 91 / 89 / 81 |
| 1,46 | 106 / 101 / 84 | 107 / 103 / 84 | 110 / 112 / 85 | 125 / 140 / 88 | 160 / 173 / 100 | 105 / 100 / 84 |
| 5,58 | 147 / 135 / 93 | 147 / 136 / 94 | 149 / 142 / 94 | 156 / 158 / 97 | 170 / 174 / 109 | 147 / 134 / 93 |
| 21,3 | 175 / 173 / 126 | 175 / 173 / 127 | 175 / 174 / 127 | 175 / 174 / 129 | 175 / 175 / 138 | 175 / 173 / 126 |
| 0 | 86 / 86 / 80 | 87 / 89 / 80 | 91 / 98 / 81 | 108 / 130 / 84 | 152 / 172 / 96 | 86 / 85 / 80 |

**57m · after_haemostasis_90 (L3, 90)**

| aguda \ deuda | 0,000667 | 0,00262 | 0,0103 | 0,0407 | 0,16 | 0 |
|---|---|---|---|---|---|---|
| 0,1 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 87 / 82 | 80 / 80 / 80 |
| 0,382 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 87 / 82 | 80 / 80 / 80 |
| 1,46 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 87 / 82 | 80 / 80 / 80 |
| 5,58 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 87 / 82 | 80 / 80 / 80 |
| 21,3 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 87 / 82 | 80 / 80 / 80 |
| 0 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 87 / 82 | 80 / 80 / 80 |

**57m · restored_adequacy_120 (L3, 120)**

| aguda \ deuda | 0,000667 | 0,00262 | 0,0103 | 0,0407 | 0,16 | 0 |
|---|---|---|---|---|---|---|
| 0,1 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 |
| 0,382 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 |
| 1,46 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 |
| 5,58 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 |
| 21,3 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 |
| 0 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 |

**57m · techo e intrínseca en el ancla** (FC de LOW / MID / HIGH)

| Hito | techo 150 | techo 175 | techo 200 | intr. inferior | intr. medio | intr. superior |
|---|---|---|---|---|---|---|
| after_crystalloid_30 | 82 / 89 / 80 | 82 / 89 / 80 | 82 / 89 / 80 | 62 / 69 / 60 | 82 / 89 / 80 | 102 / 109 / 100 |
| after_haemostasis_90 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 60 / 60 / 60 | 80 / 80 / 80 | 100 / 100 / 100 |
| after_prbc_unit_1 | 81 / 84 / 81 | 81 / 84 / 81 | 81 / 84 / 81 | 61 / 64 / 61 | 81 / 84 / 81 | 101 / 104 / 101 |
| after_prbc_unit_2_and_haemostasis | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 60 / 60 / 60 | 80 / 80 / 80 | 100 / 100 / 100 |
| arrival | 94 / 91 / 95 | 94 / 91 / 95 | 95 / 91 / 95 | 75 / 71 / 75 | 94 / 91 / 95 | 114 / 111 / 115 |
| crystalloid_120 | 110 / 111 / 85 | 110 / 112 / 85 | 111 / 112 / 85 | 91 / 92 / 65 | 110 / 112 / 85 | 130 / 131 / 105 |
| restored_adequacy_120 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 60 / 60 / 60 | 80 / 80 / 80 | 100 / 100 / 100 |
| untreated_120 | 122 / 118 / 131 | 124 / 120 / 136 | 125 / 121 / 139 | 105 / 101 / 118 | 124 / 120 / 136 | 142 / 139 / 152 |
| untreated_30 | 102 / 97 / 103 | 102 / 98 / 104 | 102 / 98 / 104 | 82 / 78 / 84 | 102 / 98 / 104 | 122 / 117 / 123 |
| untreated_60 | 109 / 104 / 113 | 109 / 105 / 114 | 110 / 105 / 114 | 90 / 85 / 94 | 109 / 105 / 114 | 129 / 125 / 133 |

**72f · arrival (L1, 0)**

| aguda \ deuda | 0,000667 | 0,00262 | 0,0103 | 0,0407 | 0,16 | 0 |
|---|---|---|---|---|---|---|
| 0,1 | 81 / 81 / 81 | 81 / 82 / 84 | 81 / 86 / 95 | 81 / 100 / 134 | 81 / 145 / 174 | 81 / 80 / 80 |
| 0,382 | 84 / 82 / 81 | 84 / 83 / 84 | 84 / 87 / 95 | 84 / 101 / 134 | 84 / 146 / 174 | 84 / 81 / 80 |
| 1,46 | 94 / 86 / 81 | 94 / 87 / 84 | 94 / 91 / 95 | 94 / 105 / 134 | 94 / 148 / 174 | 94 / 85 / 80 |
| 5,58 | 130 / 101 / 81 | 130 / 102 / 84 | 130 / 105 / 95 | 130 / 119 / 134 | 130 / 155 / 174 | 130 / 101 / 80 |
| 21,3 | 173 / 145 / 81 | 173 / 146 / 84 | 173 / 148 / 95 | 173 / 155 / 134 | 173 / 169 / 174 | 173 / 145 / 80 |
| 0 | 80 / 80 / 81 | 80 / 81 / 84 | 80 / 85 / 95 | 80 / 100 / 134 | 80 / 145 / 174 | 80 / 80 / 80 |

**72f · untreated_120 (L1, 120)**

| aguda \ deuda | 0,000667 | 0,00262 | 0,0103 | 0,0407 | 0,16 | 0 |
|---|---|---|---|---|---|---|
| 0,1 | 91 / 88 / 91 | 92 / 91 / 96 | 98 / 101 / 114 | 119 / 134 / 159 | 164 / 173 / 175 | 90 / 87 / 90 |
| 0,382 | 95 / 91 / 94 | 96 / 94 / 99 | 102 / 103 / 117 | 122 / 135 / 160 | 165 / 173 / 175 | 94 / 90 / 92 |
| 1,46 | 110 / 101 / 103 | 112 / 104 / 108 | 117 / 113 / 124 | 134 / 142 / 162 | 168 / 174 / 175 | 110 / 101 / 101 |
| 5,58 | 152 / 135 / 134 | 153 / 136 / 137 | 155 / 143 / 148 | 162 / 159 / 169 | 173 / 174 / 175 | 152 / 134 / 132 |
| 21,3 | 175 / 173 / 172 | 175 / 173 / 173 | 175 / 174 / 173 | 175 / 174 / 175 | 175 / 175 / 175 | 175 / 173 / 172 |
| 0 | 89 / 87 / 90 | 91 / 90 / 95 | 96 / 100 / 114 | 117 / 133 / 159 | 163 / 173 / 175 | 89 / 86 / 89 |

**72f · crystalloid_120 (L2, 120)**

| aguda \ deuda | 0,000667 | 0,00262 | 0,0103 | 0,0407 | 0,16 | 0 |
|---|---|---|---|---|---|---|
| 0,1 | 85 / 85 / 80 | 87 / 88 / 81 | 91 / 97 / 82 | 108 / 128 / 87 | 154 / 172 / 105 | 85 / 85 / 80 |
| 0,382 | 89 / 88 / 81 | 90 / 90 / 81 | 95 / 99 / 83 | 111 / 130 / 87 | 155 / 172 / 105 | 89 / 87 / 81 |
| 1,46 | 102 / 97 / 84 | 103 / 99 / 84 | 108 / 108 / 85 | 123 / 137 / 90 | 160 / 173 / 108 | 102 / 96 / 83 |
| 5,58 | 143 / 128 / 93 | 143 / 129 / 93 | 146 / 136 / 95 | 154 / 155 / 99 | 170 / 174 / 116 | 142 / 127 / 93 |
| 21,3 | 174 / 171 / 126 | 174 / 172 / 126 | 174 / 172 / 127 | 175 / 174 / 130 | 175 / 175 / 142 | 174 / 171 / 126 |
| 0 | 84 / 84 / 80 | 85 / 87 / 81 | 90 / 96 / 82 | 107 / 128 / 86 | 153 / 172 / 104 | 84 / 84 / 80 |

**72f · after_haemostasis_90 (L3, 90)**

| aguda \ deuda | 0,000667 | 0,00262 | 0,0103 | 0,0407 | 0,16 | 0 |
|---|---|---|---|---|---|---|
| 0,1 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 81 / 89 / 86 | 80 / 80 / 80 |
| 0,382 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 81 / 89 / 86 | 80 / 80 / 80 |
| 1,46 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 81 / 89 / 86 | 80 / 80 / 80 |
| 5,58 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 81 / 89 / 86 | 80 / 80 / 80 |
| 21,3 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 81 / 89 / 86 | 80 / 80 / 80 |
| 0 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 81 / 89 / 86 | 80 / 80 / 80 |

**72f · restored_adequacy_120 (L3, 120)**

| aguda \ deuda | 0,000667 | 0,00262 | 0,0103 | 0,0407 | 0,16 | 0 |
|---|---|---|---|---|---|---|
| 0,1 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 82 / 80 | 80 / 80 / 80 |
| 0,382 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 82 / 80 | 80 / 80 / 80 |
| 1,46 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 82 / 80 | 80 / 80 / 80 |
| 5,58 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 82 / 80 | 80 / 80 / 80 |
| 21,3 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 82 / 80 | 80 / 80 / 80 |
| 0 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 82 / 80 | 80 / 80 / 80 |

**72f · techo e intrínseca en el ancla** (FC de LOW / MID / HIGH)

| Hito | techo 150 | techo 175 | techo 200 | intr. inferior | intr. medio | intr. superior |
|---|---|---|---|---|---|---|
| after_crystalloid_30 | 87 / 91 / 80 | 87 / 91 / 80 | 87 / 91 / 80 | 67 / 71 / 60 | 87 / 91 / 80 | 107 / 111 / 100 |
| after_haemostasis_90 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 60 / 60 / 60 | 80 / 80 / 80 | 100 / 100 / 100 |
| after_prbc_unit_1 | 84 / 85 / 83 | 84 / 85 / 83 | 84 / 85 / 83 | 64 / 65 / 63 | 84 / 85 / 83 | 104 / 105 / 103 |
| after_prbc_unit_2_and_haemostasis | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 60 / 60 / 60 | 80 / 80 / 80 | 100 / 100 / 100 |
| arrival | 94 / 91 / 95 | 94 / 91 / 95 | 95 / 91 / 95 | 75 / 71 / 75 | 94 / 91 / 95 | 114 / 111 / 115 |
| crystalloid_120 | 107 / 107 / 85 | 108 / 108 / 85 | 108 / 108 / 85 | 88 / 88 / 65 | 108 / 108 / 85 | 127 / 127 / 105 |
| restored_adequacy_120 | 80 / 80 / 80 | 80 / 80 / 80 | 80 / 80 / 80 | 60 / 60 / 60 | 80 / 80 / 80 | 100 / 100 / 100 |
| untreated_120 | 115 / 112 / 122 | 117 / 113 / 124 | 118 / 113 / 126 | 97 / 93 / 106 | 117 / 113 / 124 | 136 / 132 / 143 |
| untreated_30 | 100 / 96 / 101 | 100 / 96 / 101 | 100 / 96 / 101 | 80 / 76 / 81 | 100 / 96 / 101 | 120 / 116 / 121 |
| untreated_60 | 105 / 101 / 107 | 106 / 101 / 108 | 106 / 101 / 108 | 86 / 81 / 88 | 106 / 101 / 108 | 125 / 121 / 127 |

<!-- /generado:superficie -->

## 11. Término de presión relativa (P2I-2AF-9)

<!-- generado:presion -->
Minutos leídos en el ancla: 2160. Aguda y presión positivas a la vez: 948; déficit con presión sobre la de llegada (la presión descarga el impulso): 457; presión sin déficit: 0; déficit sin impulso por presión: 457; correlación de las dos contribuciones: 0,753. Relativa a la llegada: sí; dependencia circular: no. Clasificación: **NEEDS_PRESSURE_DOMAIN_REVIEW**. the term is a deviation from arrival (0 at arrival, negative above arrival pressure) of output x tone, and both it and the deficit fall with output, so in bleeding they rise together (partial double counting of one shock); it also carries what the deficit does not (tone, and pressure falling while extraction still compensates) and, above arrival pressure, unloads the drive while a deficit persists. Neither reads the drive (no circularity). Whether it stays, becomes absolute or is removed is a pressure-domain decision; it is neither removed nor recalibrated here.
<!-- /generado:presion -->

## 12. Identificabilidad (P2I-2AF-10)

Sólo compuestos; no se informa ningún «mejor conjunto»:

<!-- generado:identificabilidad -->
| Compuesto observable | Forma |
|---|---|
| acute_increment_at_arrival | 25 x acute gain x arrival signal (bpm, unconstrained) |
| arrival_hr | intrinsic + HR_RESERVE tanh(25 (acute gain x arrival signal + debt gain x D0) / HR_RESERVE), HR_RESERVE = ceiling - intrinsic: one equation per case |
| debt_increment_at_arrival | 25 x debt gain x D0 (bpm, unconstrained; D scale latent) |
| debt_over_time | debt gain x D(t) = debt gain x D0 x D(t) / D0: only gain x scale is observable |

| Parámetro latente | Estado | Soporte | Nota |
|---|---|---|---|
| acute_deficit_to_sympathetic_gain | NON_IDENTIFIABLE | [0.1, 21.3] and 0 | shares the arrival equation with the debt gain; it resolves with the deficit and the debt persists, so post-arrival HR would separate them; none is authored |
| d_scale | NON_IDENTIFIABLE | propagated (0 / 20 / 60), not approved |  |
| debt_to_sympathetic_gain | NON_IDENTIFIABLE | [0.000667, 0.16] and 0, on the current D support | only gain x D scale; D x c, gain / c gives the same HR |
| intrinsic_sinus_rate | NON_IDENTIFIABLE | 60 / 80 / 100 (STILL_VALID_CANDIDATE_RANGE) | no longer an exact shift: through HR_RESERVE it changes the saturated increment (largest change of HR - intrinsic between levels at the anchor 3.85 bpm); not identifiable from the arrival HR alone |
| sinus_rate_ceiling_bpm | NON_IDENTIFIABLE | 150 / 175 / 200 | visible only where the increment approaches the reserve (high drive); the authored arrival shares sit in the near-linear range |
| sympathetic_per_pressure_deficit | NOT_EVALUATED_PRESSURE_DOMAIN | 1.0 (PROVISIONAL) |  |
<!-- /generado:identificabilidad -->

## 13. FR, D y lactato (P2I-2AF-12)

<!-- generado:fr -->
¿La FR lee la FC? no. FR, D y lactato idénticos entre todos los parámetros de FC de las recorridas de validación: sí. D y lactato idénticos al registro P2I-2AD: sí. ¿Cambia la FR? no. FR calibrada: no.
<!-- /generado:fr -->

## 14. Referencia del motor heredado

<!-- generado:legado -->
LEGACY REFERENCE, NOT A CALIBRATION TARGET: the family engine's HR at 0, 15, 30, 60, 90 and 120 min, read after the verdict, never by the gain range, a flag, an invariant, identifiability or the verdict.

| Caso | Escenario | 0 | 15 | 30 | 60 | 90 | 120 |
|---|---|---|---|---|---|---|---|
| 57m | L1 | 94 / 91 / 95 (124) | 98 / 94 / 99 (125) | 102 / 98 / 104 (126) | 109 / 105 / 114 (128) | 117 / 113 / 125 (131) | 124 / 120 / 136 (133) |
| 57m | L2 | 94 / 91 / 95 (124) | 85 / 88 / 84 (120) | 82 / 89 / 80 (121) | 92 / 97 / 80 (125) | 102 / 104 / 80 (127) | 110 / 112 / 85 (130) |
| 57m | L3 | 94 / 91 / 95 (124) | 88 / 88 / 88 (120) | 81 / 84 / 81 (117) | 80 / 80 / 80 (109) | 80 / 80 / 80 (100) | 80 / 80 / 80 (95) |
| 72f | L1 | 94 / 91 / 95 (112) | 97 / 93 / 98 (113) | 100 / 96 / 101 (114) | 106 / 101 / 108 (116) | 111 / 107 / 116 (119) | 117 / 113 / 124 (121) |
| 72f | L2 | 94 / 91 / 95 (112) | 88 / 90 / 87 (108) | 87 / 91 / 80 (109) | 94 / 97 / 80 (113) | 101 / 102 / 80 (115) | 108 / 108 / 85 (118) |
| 72f | L3 | 94 / 91 / 95 (112) | 90 / 88 / 89 (108) | 84 / 85 / 83 (105) | 80 / 80 / 80 (97) | 80 / 80 / 80 (88) | 80 / 80 / 80 (83) |

Cada celda: núcleo en el ancla para LOW / MID / HIGH y, entre paréntesis, el motor de familias. Sólo referencia.
<!-- /generado:legado -->

## 15. Veredicto (P2I-2AF-13)

<!-- generado:veredicto -->
**HR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION**

| Comprobación | Resultado |
|---|---|
| la reconstrucción de la FC coincide con el núcleo completo | sí |
| sin resto de llegada (la FC registrada no llega a la dinámica) | sí |
| contribución aguda explícita y que se resuelve | sí |
| τ_D no llega a la FC con D fija | sí |
| D × c con ganancia / c da la misma FC | sí |
| saturación suave y ninguna FC sobre el techo | sí |
| las doce direcciones se cumplen | sí |
| D, lactato y FR sin cambios | sí |
| sin banderas estructurales | sí |

Regla congelada: HR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION when every check holds: (1) no arrival residual (the core's source and the probe in which the authored HR reaches no dynamics); (2) the acute contribution is explicit and recoverable (the source; 0 at no deficit; no acute contribution after sustained adequacy in any read L3 run); (3) tau_D does not reach HR at fixed D; (4) D x c with gain / c gives the same HR; (5) smooth saturation (tanh, no clip) and no sinus HR at or above the ceiling anywhere; (6) the twelve directions pass; (7) D, lactate and RR unchanged (P2I-2AD record and every validation rerun); (8) no structural flag; and the post-processing agrees with the full core. Otherwise HR_STRUCTURE_NOT_READY with the first blocker. The arrival mismatch is reported for the faculty, never a gate; no numeric parameter needs to be identified.
<!-- /generado:veredicto -->

## 16. Diseño numérico docente siguiente

<!-- generado:siguiente -->
Estado: **PREPARED_NOT_EXECUTED** (preparado, no ejecutado).

Observables:

- arrival HR mismatch (57m 124, 72f 112)
- untreated HR trajectory (30 / 60 / 120)
- HR response to crystalloid (end of bolus, 120)
- HR response to each PRBC unit (30, 60)
- HR after sustained adequacy (T*, 90, 120)
- residual delayed tachycardia (debt share at 120)

Lo que debe aportar la docencia:

- an arrival HR tolerance
- envelopes on the observable trajectories above, per case
- whether the intrinsic rate may differ by case (the two authored arrivals differ by 12 bpm while the gains are common)
- the sinus-ceiling range (150-200 proposed here, general physiology)
- whether the relative-pressure term stays (pressure domain)

Método: filter the acute x debt x ceiling x intrinsic points (and their D support) against the faculty envelopes on observables, post-processed from the cached physiology; report survivors and composites, never one best set; latent gains are never approved directly
<!-- /generado:siguiente -->

## 17. Efectos sobre artefactos anteriores

- **HR1 y HR2** (reglas congeladas de calibración; registro de congelamiento `990f3ad8…`).
  - Antes comparaban con la FC registrada, que el resto forzaba como FC de llegada de la corrida. Sin resto, comparan
    con la FC de llegada de la propia corrida.
  - HR2 («la recuperación puede bajar la FC hacia la intrínseca; una parte simpática de llegada puede resolverse»)
    pide, a una llegada sin parte simpática (ya en la intrínseca), terminar en ella: no hay nada que resolver, y HR4
    impide bajar más.
  - Sin ese ajuste, 2 candidatos fuera del diseño P2F (deuda inferior, con entrega media o superior) pasaban a
    rechazados. Con él, todos los estados de P2G quedan como antes. Ninguna sonda, umbral ni banda cambió.
- **Paquete P2G.**
  - La descomposición registra el incremento simpático saturado, el que suma el núcleo. La parte «otros» queda en
    7·10⁻¹⁵ lpm; antes absorbía la compresión de la saturación.
  - El núcleo acepta ahora las 108 llegadas que P2I-2AE rechazaba. Las cifras de FC del paquete cambian (no hay resto);
    las de lactato, presión y FR, no.
- **Corte P2I-1, sondas P2I-2T y anclas P2I-2U.** Sólo cambian sus digests y el conteo de llegadas leídas sin impulso
  por deuda, que baja de 108 a 0.

## 18. Eficiencia

<!-- generado:eficiencia -->
Corridas completas de representantes: 18; reejecuciones de validación: 162; series posprocesadas: 720; descomposiciones de llegada analíticas: 3240 (rechazos analíticos: 0); simulaciones evitadas: 540; barrido cartesiano: no.
<!-- /generado:eficiencia -->

- Evaluación completa: 9,3 s.
- 0 llamadas de IA de la app.
- Una sola congelación y una sola evaluación.

## 19. Lo que queda para la docencia

Registrado en `docs/REGISTRO_DEUDA_TECNICA.md` (TD-93, actualizada, y TD-94):

- La tolerancia de la FC de llegada. Hoy sólo hay distribución y superficie: no existe tolerancia y no se inventó
  ninguna.
- Si la intrínseca o los niveles de llegada pueden diferir por caso. Con ganancias comunes, 57m y 72f reciben la misma
  predicción.
- El rango del techo sinusal: 150 / 175 / 200 lpm es fisiología general, no verdad del repositorio.
- El término de presión relativa: se queda, se vuelve absoluto o se quita. De eso depende que la taquicardia diferida
  por deuda sea visible (§9, §11).
- Las envolventes sobre los observables (§16). Ninguna ganancia latente se aprueba directamente.
