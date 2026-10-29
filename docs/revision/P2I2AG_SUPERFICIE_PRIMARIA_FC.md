# P2I-2AG · Presión aplazada y superficie primaria de calibración de la FC

Este paquete funciona sólo en sombra. No hace nada de esto:
- integración en tiempo de ejecución, ni migración de GI ni de otra familia;
- calibración de la presión, del tono vascular ni de la FR, ni activación del colapso;
- aprobación de ningún parámetro de FC, ni envolventes de trayectoria como filtro duro;
- ajuste al motor heredado: no lo lee.

Código:
- `clinical_core/calibration.py`:
  - `check_hr` exige la intrínseca declarada (`CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR`) y comprueba HR2 (a);
  - se actualizaron los textos de HR1, HR2 y AC1 y la descripción de `arrival_sympathetic_drive`;
- `clinical_core/hr_primary.py`: el modo primario, la guarda, la tolerancia, la superficie, el prefiltro analítico y
  los diagnósticos, congelados en `8eba7fc` antes de cualquier conteo;
- `clinical_core/hr_primary_report.py`: sólo este informe.

Números: `docs/revision/P2I2AG_hr_primary.json`. Registros de partida, cerrados: P2I-2AD (`5cb48163…`), P2I-2AE
(`1b65d303…`) y P2I-2AF (`adb3767b…`). El módulo de P2I-2AF queda fijado byte a byte.

## Resumen

- **Presión aplazada, no eliminada.** En la calibración primaria la contribución de presión es DEFERRED.
  - El modo `PRIMARY_HR_CALIBRATION` pone en 0 sólo la ganancia de presión, y sólo en el perfil de análisis.
  - La fisiología común la conserva (1,0 por defecto) y su valor se informa en una columna diagnóstica.
  - Probado con 54 recorridas exactas y con 2178 estados idénticos salvo el impulso.
- **Intrínseca explícita.** La guarda actúa en `check_hr` y en la superficie: hubo 0 respaldos en la FC registrada.
  Fuera de la calibración el respaldo sigue igual.
- **HR1 y HR2 son pruebas estructurales del modelo vigente**, nunca evidencia clínica.
  - HR2 (a): sin contribución simpática, la FC de llegada predicha es la intrínseca declarada.
  - El congelamiento de la calibración pasó a `22bd65e4…`. Los artefactos sólo cambian sus digests, el golden directo
    no cambia y Contracts v2 da IDENTICAL.
- **Filtro de llegada (±5 lpm), con 1350 descomposiciones analíticas.**
  - Compatibles con su caso: 30 en 57m (de 675) y 58 en 72f.
  - Conjuntamente compatibles con intrínseca común: **0**. Los 675 candidatos conjuntos caen por un rechazo analítico
    exacto.
  - La razón: en la fisiología de llegada certificada, cada representante tiene la misma llegada en ambos casos. Con la
    misma intrínseca y las mismas ganancias la FC predicha es idéntica, y las ventanas 119–129 y 107–117 no se
    superponen. El peor desajuste no puede bajar de 6 lpm.
- **Veredicto: HR_NUMERIC_DECISION_SURFACE_NOT_READY — HR_NUMERIC_CALIBRATION_BLOCKED_BY_ARRIVAL_RECONSTRUCTION.**
  Como pide el encargo, el paquete se detiene: no hay paquete de trayectorias (P2I-2AG-6), ni propuesta de envolventes
  (P2I-2AG-7), ni certificación completa. La tolerancia no se tocó.
- **Sensibilidad, no aprobada.** Si la intrínseca puede diferir por caso, sobreviven 5 de 2025 combinaciones, y todas
  comparten casi todo:
  - representante LOW;
  - 57m con intrínseca 80 y 72f con 60;
  - ganancia aguda 5,58 y techo 150;
  - cualquier ganancia de deuda.
  Es un apoyo estrecho, apoyado en el techo más bajo.
- **Presión, sólo diagnóstico.**
  - Correlación con la señal aguda: 0,753.
  - En el 44 % de los minutos las dos suben; en el 21 % la presión baja el impulso aunque haya déficit. En esos minutos
    cancela una mediana de 2,3 lpm (hasta 10,9) y, en el ancla, el 24 % del impulso agudo más el de deuda (en la
    mediana).
  - La llegada no cambia. El orden de los 25 puntos por FC se invierte en 383 de 18 000 pares (2,1 %).
- D, lactato, FR, BloodState y DO2 no cambian. Nada se aprobó.

## 1. Decisiones docentes y punto de partida

<!-- generado:decisiones -->
Congelamiento: `94c94584009449c43b15bd3bb8673bccbead3db86fcf71fa10f508b674ccf763` (una prueba lo fija). Registros de partida: P2I-2AD `5cb48163da4ff081e752b7684f4b036dbcf3e2acb4f94ee1603aaec742fe7fcf`, P2I-2AE `1b65d303831011014ca8cf8ce98e5fb880c5ea9cd3244f47773ce9d47b3712c8` y P2I-2AF `adb3767b4e8042b9976057587ab337fd5de5cd25119a1bb28e7a119d85768ed3`.

| Decisión docente | Texto registrado |
|---|---|
| fecha | 2026-10-29 |
| presión | PRESSURE_SYMPATHETIC_CONTRIBUTION = DEFERRED for the primary HR calibration: the relative-pressure term (referenced to the shocked arrival; pressure domain uncalibrated; correlated with the acute deficit; unloading the drive while a deficit persists) selects no HR gain, compensates no acute or debt drive and enters no arrival matching or ranking; reported as PRESSURE_TERM_DIAGNOSTIC_ONLY; not rejected: kept in the common physiology for the pressure domain; no absolute pressure reference |
| intrínseca | every HR calibration candidate declares its intrinsic HR (60 / 80 / 100); no implicit recorded-HR floor (CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR); the fallback stays outside calibration |
| HR1 / HR2 | accepted only as structural tests of the current predicted-arrival model, never historical clinical evidence; HR2: with no sympathetic contribution the predicted arrival HR reduces to the declared intrinsic, rhythm-consistent rate |
| llegada | authored 57m 124 and 72f 112 bpm (no later authored HR); arrival match tolerance +-5 bpm for each case, an educational calibration tolerance, not a measurement-error model; never tuned after counts |
| ganancias comunes | acute and debt gains common to both cases; common intrinsic first; a case-specific intrinsic only as sensitivity / identifiability, never approved |
| saturación | the P2I-2AF smooth form unchanged; candidates 150 / 175 / 200 bpm, exploratory, not approved, not extended |
| escala de D | D's scale is not approved: HR depends on the observable debt contribution; D 20 / 60 are never faculty constants |
| ritmo | non-sinus and complete beta-blockade edges stay GENERALIZATION_BLOCKER_ONLY; they do not block GI |
| alcance | shadow only; no final HR approval, no hard trajectory envelope, no pressure / vascular-tone or RR calibration, no collapse, migration or runtime integration |
<!-- /generado:decisiones -->

## 2. La presión aplazada en la calibración primaria (P2I-2AG-1)

<!-- generado:modo -->
PRESSURE_SYMPATHETIC_CONTRIBUTION = **DEFERRED**. Cambio del perfil de análisis en el modo primario: `{"sympathetic_per_pressure_deficit": 0.0}`; el valor por defecto común no cambia. Columna diagnóstica: `PRESSURE_TERM_DIAGNOSTIC_ONLY` = 25 × (1 − β) × 1,0 × (1 − P_rel), nunca leída por una aceptación, una coincidencia ni un orden. Guarda: `CALIBRATION_REQUIRES_EXPLICIT_INTRINSIC_HR`.
<!-- /generado:modo -->

- La fisiología común no cambia: `derived.sympathetic_target` sigue sumando el término de presión con su ganancia por
  defecto.
- El modo primario es un perfil de análisis: el de P2I-2AF, con la ganancia de presión en 0. Como la FC no llega a la
  fisiología, las trayectorias primarias se reconstruyen exactamente desde la fisiología ya calculada (§12).
- La aceptación (`compatible`) lee sólo la FC predicha.
- La FC de llegada no depende de la presión: P_rel vale 1 en la llegada, así que el filtro de llegada es el mismo con
  el término activo o neutralizado.
- No se inventó ninguna referencia absoluta de presión.

## 3. Intrínseca explícita y semántica de HR1 y HR2 (P2I-2AG-3)

<!-- generado:semantica -->
| Regla | Enunciado | Sonda y criterio vigentes |
|---|---|---|
| HR1 | deterioration can increase HR | each GI case's full declared arrival (the candidate's, explicit intrinsic), volume loss 8 mL/min for 30 min: HR rises above the run's own predicted arrival HR (P2I-2AG: a structural test of the current predicted-arrival model, never clinical calibration evidence; no authored, legacy or historical target) |
| HR2 | recovery can reduce HR toward intrinsic | (a) an arrival physiology with no sympathetic contribution predicts exactly the declared, rhythm-consistent intrinsic rate (P2I-2AG, faculty); (b) the same arrival and loss, then 400 mL beyond arrival, 240 min: HR ends below an arrival HR that carried a sympathetic share, else at it (P2I-2AF). A structural test of the current model, never clinical calibration evidence |

Sólo estructurales: sí; `check_hr` exige la intrínseca declarada: sí; HR2 (a) codificada: sí; sin objetivo registrado ni heredado: sí; el respaldo en la FC registrada sigue fuera de la calibración: sí.
<!-- /generado:semantica -->

- HR1 protege que, desde la llegada predicha por el propio modelo, el deterioro sube la FC.
- HR2 protege dos cosas:
  - (a) una llegada sin contribución simpática predice exactamente la intrínseca declarada (decisión docente);
  - (b) la recuperación termina por debajo de una llegada que traía parte simpática, y en ella si no la traía
    (adaptación de P2I-2AF).
- Ninguna de las dos usa la FC registrada, el motor heredado ni el rechazo HR1 histórico.

## 4. Superficie congelada (P2I-2AG-4)

<!-- generado:superficie -->
- Tolerancia de llegada: ±5 lpm por caso; 57m 119–129, 72f 107–117.
- Intrínseca: 60 / 80 / 100. Ganancia aguda: 0,1 · 0,382 · 1,46 · 5,58 · 21,3. Ganancia de deuda: 0,000667 · 0,00262 · 0,0103 · 0,0407 · 0,16. Techo: 150 / 175 / 200 (HR_RESERVE = techo − intrínseca). 225 candidatos.

Regla: Primary surface: intrinsic 60 / 80 / 100 (declared) x acute_deficit_to_sympathetic_gain at the five frozen P2I-2AF points x debt_to_sympathetic_gain at the five frozen P2I-2AF points x the three frozen P2I-2AF ceilings 150 / 175 / 200 (HR_RESERVE = ceiling - intrinsic): 225 candidates, gains and intrinsic common to both cases, pressure contribution 0. Arrival physiology: the three P2I-2AD representatives (LOW / MID / HIGH, its committed record) as the core builds them. Arrival HR is analytic (derived.heart_rate_decomposition), no simulation per candidate. Sensitivity only: the intrinsic may differ by case (3 x 3 pairs), the gains and ceiling stay common.

Compatibilidad: ARRIVAL-COMPATIBLE for a case: |predicted arrival HR - authored| <= 5 bpm (57m 119-129, 72f 107-117). JOINT: both cases at once with the same candidate. Fixed before any count; never loosened.
<!-- /generado:superficie -->

Los candidatos 150 / 175 / 200 son el conjunto congelado de P2I-2AF: techos sinusales, con HR_RESERVE = techo −
intrínseca, es decir, reservas de 50 a 140 lpm. El encargo los llama «HR_RESERVE». Si la docencia quería reservas
literales de 150 / 175 / 200 lpm, se trata de otra superficie, que no se evaluó porque el encargo prohíbe extender la
grilla (§15).

## 5. Filtro de llegada (P2I-2AG-5)

<!-- generado:llegada -->
| | 57m | 72f |
|---|---|---|
| compatibles (de 675) | 30 | 58 |
| … representante HIGH | 0 | 25 |
| … representante LOW | 5 | 30 |
| … representante MID | 25 | 3 |

Descomposiciones de llegada: 1350 (analíticas). Conjuntamente compatibles con la intrínseca común: **0** (por representante: HIGH 0, LOW 0, MID 0).

| Rechazo analítico | Candidatos |
|---|---|
| IDENTICAL_PREDICTION_DISJOINT_WINDOWS | 675 |
| IMPLICIT_RECORDED_HR_FALLBACK | 0 |
| INVALID_RESERVE_BASE | 0 |
| NEGATIVE_SYMPATHETIC_COMPONENT | 0 |

Rechazos por simulación: 0. Fisiología de llegada idéntica en ambos casos por representante: HIGH sí, LOW sí, MID sí; ventanas disjuntas: sí. Con una predicción común, la cota inferior del peor desajuste es 6 lpm (la mitad de 124 − 112), mayor que la tolerancia. Ganancias propias de cada caso requeridas: no. La llegada es la misma con la presión activa o neutralizada: sí.
<!-- /generado:llegada -->

## 6. Apoyo entre los compatibles de cada caso

<!-- generado:soporte -->
**intrínseca**

| Caso | inferior | medio | superior |
|---|---|---|---|
| 57m | 6 | 6 | 18 |
| 72f | 25 | 0 | 33 |

**ganancia aguda**

| Caso | 0,1 | 0,382 | 1,46 | 5,58 | 21,3 |
|---|---|---|---|---|---|
| 57m | 4 | 4 | 4 | 15 | 3 |
| 72f | 5 | 5 | 23 | 20 | 5 |

**ganancia de deuda**

| Caso | 0,000667 | 0,00262 | 0,0103 | 0,0407 | 0,16 |
|---|---|---|---|---|---|
| 57m | 5 | 5 | 5 | 11 | 4 |
| 72f | 6 | 6 | 24 | 16 | 6 |

**techo**

| Caso | 150 | 175 | 200 |
|---|---|---|---|
| 57m | 17 | 6 | 7 |
| 72f | 21 | 21 | 16 |
<!-- /generado:soporte -->

Por separado, cada caso tiene compatibles, pero en regiones distintas de la superficie:
- 72f no admite la intrínseca media;
- con el representante HIGH, 57m no tiene ninguno;
- con el MID, 72f tiene sólo 3.

## 7. Sensibilidad: intrínseca propia de cada caso (no aprobada)

<!-- generado:sensibilidad -->
Sólo sensibilidad, no aprobada (aprobada: no). Candidatos conjuntamente compatibles si la intrínseca puede diferir por caso (ganancias y techo comunes): **5** de 2025 (por representante: HIGH 0, LOW 5, MID 0).

| intrínseca 57m \ 72f | inferior | medio | superior |
|---|---|---|---|
| inferior | 0 | 0 | 0 |
| medio | 5 | 0 | 0 |
| superior | 0 | 0 | 0 |

| Dimensión | Apoyo por valor |
|---|---|
| ganancia aguda | 0,1: 0, 0,382: 0, 1,46: 0, 5,58: 5, 21,3: 0 |
| ganancia de deuda | 0,000667: 1, 0,00262: 1, 0,0103: 1, 0,0407: 1, 0,16: 1 |
| techo | 150: 5, 175: 0, 200: 0 |
<!-- /generado:sensibilidad -->

Que la intrínseca pueda diferir por caso cambia el resultado, pero poco:
- aparecen 5 combinaciones de 2025, todas en el representante LOW;
- todas llevan el techo 150 y la ganancia aguda 5,58.

No se aprueba una intrínseca por caso; es una decisión docente (§15).

## 8. Ejemplos de descomposición en la llegada

<!-- generado:ejemplos -->
Primer candidato compatible de cada representante y caso, en el orden de la superficie (ilustración, nunca un orden de preferencia):

| Rep. | Caso | intr. | aguda | deuda | techo | señal | D0 | aguda (lpm) | deuda (lpm) | saturado | uso de reserva | predicha | desajuste |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HIGH | 72f | 60 | 0,1 | 0,0407 | 150 | 0,00 | 60 | 0,0 | 61,0 | 53,1 | 0,59 | 113,1 | 1,1 |
| LOW | 57m | 80 | 5,58 | 0,000667 | 150 | 0,40 | 0 | 55,8 | 0,0 | 46,4 | 0,66 | 126,4 | 2,4 |
| LOW | 72f | 60 | 5,58 | 0,000667 | 150 | 0,40 | 0 | 55,8 | 0,0 | 49,6 | 0,55 | 109,6 | -2,4 |
| MID | 57m | 60 | 0,1 | 0,16 | 150 | 0,15 | 20 | 0,4 | 80,0 | 64,2 | 0,71 | 124,2 | 0,2 |
| MID | 72f | 100 | 1,46 | 0,0103 | 150 | 0,15 | 20 | 5,5 | 5,2 | 10,5 | 0,21 | 110,5 | -1,5 |
<!-- /generado:ejemplos -->

## 9. Identificabilidad (P2I-2AG-8)

<!-- generado:identificabilidad -->
Regla congelada: Per latent dimension, over a set of arrival-compatible candidates: WELL_CONSTRAINED when one value survives; PARTIALLY_CONSTRAINED when more than one but not all survive; POORLY_IDENTIFIED when all survive and the least-supported value holds less than half the survivors of the most-supported; NON_IDENTIFIABLE when all survive and it holds at least half; EMPTY when the set has no survivor (no constraint is assessable).

| Conjunto | Dimensión | Estado |
|---|---|---|
| 57m sola | ganancia aguda | POORLY_IDENTIFIED |
| 57m sola | techo | POORLY_IDENTIFIED |
| 57m sola | ganancia de deuda | POORLY_IDENTIFIED |
| 57m sola | intrínseca | POORLY_IDENTIFIED |
| 72f sola | ganancia aguda | POORLY_IDENTIFIED |
| 72f sola | techo | NON_IDENTIFIABLE |
| 72f sola | ganancia de deuda | POORLY_IDENTIFIED |
| 72f sola | intrínseca | PARTIALLY_CONSTRAINED |
| conjunta, intrínseca por caso (sólo sensibilidad) | ganancia aguda | WELL_CONSTRAINED |
| conjunta, intrínseca por caso (sólo sensibilidad) | techo | WELL_CONSTRAINED |
| conjunta, intrínseca por caso (sólo sensibilidad) | ganancia de deuda | NON_IDENTIFIABLE |
| conjunta, intrínseca por caso (sólo sensibilidad) | intrínseca de 57m | WELL_CONSTRAINED |
| conjunta, intrínseca por caso (sólo sensibilidad) | intrínseca de 72f | WELL_CONSTRAINED |
| conjunta, intrínseca común (primaria) | ganancia aguda | EMPTY |
| conjunta, intrínseca común (primaria) | techo | EMPTY |
| conjunta, intrínseca común (primaria) | ganancia de deuda | EMPTY |
| conjunta, intrínseca común (primaria) | intrínseca | EMPTY |

Compuestos observables entre los compatibles de cada caso (mín. / mediana / máx.):

| Caso | aguda en la llegada (lpm) | deuda en la llegada (lpm) | incremento simpático total (lpm) | uso de la reserva saturada |
|---|---|---|---|---|
| 57m | 0,4 / 20,9 / 80,0 | 0,0 / 5,2 / 80,0 | 19,6 / 25,1 / 66,6 | 0,20 / 0,41 / 0,74 |
| 72f | 0,0 / 14,6 / 55,8 | 0,0 / 0,0 / 61,0 | 10,5 / 15,4 / 55,9 | 0,11 / 0,30 / 0,59 |

Escala de D: the debt increment is gain x D0: only gain x D scale is observable.
<!-- /generado:identificabilidad -->

- El conjunto primario está vacío: la tolerancia no restringe ningún parámetro porque ningún candidato reproduce las dos
  llegadas.
- Los «WELL_CONSTRAINED» de la sensibilidad salen de sólo 5 sobrevivientes de un único representante. Describen una
  región estrecha, no una identificación.
- Ningún valor latente queda identificado ni se elige. La escala de D sigue latente.

## 10. Auditoría del doble conteo por presión (P2I-2AG-2, sólo diagnóstico)

<!-- generado:presion -->
Muestra P2I-2AF: 2160 minutos con pulso de las 18 corridas representativas. Correlación entre las señales (déficit / demanda y 1 − P_rel): 0,753. Las dos empujan la FC hacia arriba en 948 minutos (44 %); la presión la empuja hacia abajo con déficit presente en 457 (21 %). En esos minutos (mín. / mediana / máx.): señal de déficit 0,002 / 0,190 / 0,422; cancelación por presión -10,9 / -2,3 / -0,0 lpm sin saturar; fracción de aguda + deuda cancelada en el ancla 0,00 / 0,24 / 9,43.

FC con la presión activa menos neutralizada, y FC sobre la intrínseca, en el plano 5 × 5 de ganancias (techo 175, intrínseca media; LOW / MID / HIGH × 57m / 72f):

| Hito | activa − neutralizada (lpm) | sobre la intrínseca, activa (lpm) | sobre la intrínseca, neutralizada (lpm) |
|---|---|---|---|
| after_crystalloid_30 | -9,4 / -2,2 / -0,1 | 0,0 / 14,7 / 91,8 | 0,4 / 20,0 / 91,9 |
| after_haemostasis_90 | -11,5 / -0,8 / -0,0 | 0,0 / 0,0 / 9,3 | 0,0 / 0,7 / 13,4 |
| after_prbc_unit_1 | -8,1 / -1,7 / -0,3 | 0,0 / 4,2 / 81,8 | 0,3 / 6,6 / 83,0 |
| after_prbc_unit_2_and_haemostasis | -10,9 / -2,2 / -0,1 | 0,0 / 0,0 / 29,5 | 0,1 / 2,4 / 35,4 |
| arrival | 0,0 / 0,0 / 0,0 | 0,7 / 15,4 / 93,8 | 0,7 / 15,4 / 93,8 |
| crystalloid_120 | 0,0 / 0,3 / 5,7 | 0,4 / 28,9 / 95,0 | 0,3 / 26,6 / 95,0 |
| restored_adequacy_120 | -4,9 / -0,3 / -0,0 | 0,0 / 0,0 / 1,9 | 0,0 / 0,3 / 4,9 |
| untreated_120 | 0,0 / 4,4 / 12,9 | 8,3 / 69,8 / 95,0 | 1,9 / 64,2 / 95,0 |
| untreated_30 | 0,0 / 1,8 / 3,2 | 2,6 / 32,6 / 94,8 | 0,9 / 29,7 / 94,8 |
| untreated_60 | 0,0 / 3,2 / 6,4 | 4,5 / 46,9 / 95,0 | 1,2 / 43,1 / 95,0 |

Órdenes descriptivos de los 25 puntos por FC en cada hito, activa frente a neutralizada (no hay ninguna selección): 383 pares invertidos y 0 empates que cambian, de 18000. pressure_rel is 1 at arrival, so the arrival filter is the same on and off. Clasificación: **NEEDS_PRESSURE_DOMAIN_REVIEW**; calibrado: no.
<!-- /generado:presion -->

- El término de presión suma FC sin tratamiento: mediana de +4,4 lpm a los 120 min, hasta +12,9.
- La resta tras los GR y la hemostasia: mediana de −2,2 lpm, hasta −10,9.
- Con el término neutralizado, la taquicardia diferida por deuda se ve más:
  - a los 90 min, mediana de 0,7 lpm sobre la intrínseca (antes 0) y máximo de 13,4 (antes 9,3);
  - a los 120 min, máximo de 4,9 lpm (antes 1,9).
- Nada de esto calibra el término: sigue NEEDS_PRESSURE_DOMAIN_REVIEW.

## 11. Escala de D y ritmo (P2I-2AG-9, -10)

<!-- generado:escala_d -->
Escala de D en el modo primario (D × c, ganancia / c): c = 0,37: brecha 1,42e-14 lpm (sin dividir la ganancia, 7,5 lpm); c = 3: brecha 1,42e-14 lpm (sin dividir la ganancia, 20,9 lpm). Se cumple: sí.

Ritmo y betabloqueo con deuda en el modo primario: beta_1: [124.0] lpm, constante sí; paced: [124.0] lpm, constante sí. Clasificación: GENERALIZATION_BLOCKER_ONLY; afecta a GI: no.
<!-- /generado:escala_d -->

## 12. No-regresión (P2I-2AG-11)

<!-- generado:no_regresion -->
Reconstrucción primaria frente al núcleo completo con la ganancia de presión 0: 54 recorridas, todas exactas: sí (impulso, FC y FC de llegada analítica); ninguna contribución de presión: sí. Estados completos con la presión activa y neutralizada: 2178 comparados, iguales salvo el impulso: sí (BloodState, V, Hb, D, lactato, demanda). Entrega, déficit efectivo, FR, lactato y gasto derivados iguales: sí. D y lactato frente al registro P2I-2AD: 72 filas, iguales sí.
<!-- /generado:no_regresion -->

## 13. Veredicto (P2I-2AG-12)

<!-- generado:veredicto -->
**HR_NUMERIC_DECISION_SURFACE_NOT_READY — HR_NUMERIC_CALIBRATION_BLOCKED_BY_ARRIVAL_RECONSTRUCTION**

| Comprobación | Resultado |
|---|---|
| la presión no entra en la aceptación de candidatos | sí |
| toda intrínseca declarada (sin respaldo en la FC registrada) | sí |
| HR1 / HR2 con la semántica estructural vigente | sí |
| al menos un candidato conjunto compatible con la llegada (intrínseca común) | no |
| sin ganancias propias de cada caso | sí |
| D, lactato, FR, BloodState y DO2 sin cambios; reconstrucción exacta | sí |

Detenido (sin paquete de trayectorias ni propuesta de envolventes): sí. Aprobado: no.

Regla congelada: HR_NUMERIC_DECISION_SURFACE_READY_FOR_FACULTY when: (1) the pressure contribution enters no candidate acceptance (the primary profile zeroes it; the reconstruction reads no pressure; its value is reported apart, diagnostic only); (2) every candidate declares its intrinsic rate (no fallback); (3) HR1 / HR2 carry the current structural semantics (frozen rule texts, check_hr's guard and HR2 arrival reduction); (4) at least one candidate is jointly arrival-compatible with COMMON intrinsic and common gains; (5) no case-specific gain (by construction); (6) D, lactate, RR, BloodState and DO2 / effective deficit unchanged, and the reconstruction agrees with the full core. The suite criterion (no new failure) is the final certification's, outside this module. Otherwise HR_NUMERIC_DECISION_SURFACE_NOT_READY with the first blocker; zero joint survivors is HR_NUMERIC_CALIBRATION_BLOCKED_BY_ARRIVAL_RECONSTRUCTION and stops the package: no trajectory decision pack (P2I-2AG-6) and no envelope proposal (P2I-2AG-7) is built, and the tolerance is never loosened.
<!-- /generado:veredicto -->

## 14. Lo que no se hizo, por la parada temprana

- P2I-2AG-6 (paquete de trayectorias) y P2I-2AG-7 (propuesta de envolventes). Sólo se construyen sobre candidatos
  conjuntamente compatibles con la intrínseca común, y no hay ninguno.
- La certificación final completa no se corrió:
  - suite completa;
  - comparación de las fallas de base sobre `79a3895`;
  - regresiones;
  - revisión adversarial;
  - push.
  El protocolo de parada temprana la detiene ante un bloqueo docente.
- Lo que sí se verificó:
  - 354 pruebas focalizadas, incluida la reproducción en vivo de P2I-2AF;
  - el golden directo, igual byte a byte;
  - Contracts v2, IDENTICAL.

## 15. Decisiones que necesita la docencia

- **Cómo desbloquear la llegada** (el paquete no elige):
  - a) permitir una intrínseca propia de cada caso: la sensibilidad deja 5 combinaciones, estrechas;
  - b) permitir niveles de llegada (deuda y entrega) propios de cada caso: no se evaluó, porque hoy los representantes
    certificados comparten niveles;
  - c) revisar la tolerancia. Es sólo un hecho aritmético, no una propuesta: con una predicción común ningún valor
    queda a menos de 6 lpm de las dos FC registradas.
- **Aclarar si 150 / 175 / 200 son techos**, como en P2I-2AF, o reservas literales.
- **Si se certifica y se sube ya el cierre estructural** de este paquete (presión aplazada, intrínseca explícita,
  HR1/HR2), o si espera a la decisión anterior.

## 16. Eficiencia

<!-- generado:eficiencia -->
Corridas de representantes: 18; recorridas de validación: 54; corridas de estados para la no-regresión: 36; descomposiciones de llegada analíticas: 1350; rechazos analíticos: 675; rechazos por simulación: 0; series posprocesadas (auditoría de presión): 900; paquete de trayectorias construido: no; barrido cartesiano: no; motor heredado leído: no.
<!-- /generado:eficiencia -->

- La evaluación completa tomó 6,5 s; la llegada es analítica.
- 0 llamadas de IA de la app.
- Hubo un solo congelamiento y una sola evaluación.
