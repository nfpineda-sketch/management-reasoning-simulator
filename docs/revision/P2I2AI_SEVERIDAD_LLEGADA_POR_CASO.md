# P2I-2AI · Severidad de llegada por caso y recertificación de D y lactato

Este paquete funciona sólo en sombra. No hace nada de esto:
- integración en tiempo de ejecución, ni migración de GI ni de otra familia;
- calibración de la presión, del tono vascular ni de la FR, ni activación del colapso;
- selección latente de la FC, aprobación de ningún parámetro, ni envolventes de trayectoria como filtro;
- valores nuevos de D0 o de entrega, interpolación, ganancias por caso o ajuste al motor heredado (no lo lee).

Código:
- `clinical_core/arrival_severity.py`: la regla de orden, el constructor de severidad sin FC, el filtro por caso, la
  clasificación, la superficie de llegada, la comparación A/B/C/D, las trayectorias y el veredicto, congelados en
  `2b82a71` antes de cualquier conteo;
- `clinical_core/arrival_severity_report.py`: sólo este informe.

Números: `docs/revision/P2I2AI_arrival_severity.json`. Registros de partida, cerrados: P2I-2AD (`5cb48163…`),
P2I-2AF (`adb3767b…`) y P2I-2AG (`94c94584…`). El módulo de P2I-2AG queda fijado byte a byte.

## Resumen

- **Severidad por caso sin leer la FC.**
  - Sólo se usan los cinco pares (deuda, entrega) existentes, con los valores de las bandas de cada caso: no hay
    valores nuevos ni interpolación.
  - La regla de orden se congeló antes de cualquier conteo: D0 de 57m ≥ D0 de 72f, entrega de 57m ≤ entrega de 72f, al
    menos una estricta.
  - De 25 combinaciones, **7 son admisibles**; las otras 18 son rechazos analíticos (5 de ellas por idénticas).
  - El constructor lee sólo las bandas de deuda y de entrega de llegada de cada caso. Una prueba lo registra y
    comprueba que el orden no cambia con la FC registrada + 50 lpm.
  - Una guarda sobre el árbol sintáctico comprueba además que el constructor no nombra ninguna FC, tolerancia,
    ganancia, techo ni el motor heredado. La guarda sólo ve los nombres que lee directamente.
- **Recertificación de D y lactato.** Se usó la maquinaria de P2I-2AD sin cambios: cada caso se filtra con su propio par
  y un candidato sobrevive si pasan los dos casos.
  - La factorización coincide con el núcleo completo: 936 corridas, 0 desacuerdos.
  - Los pares atados reproducen **exactamente** la región de P2I-2AD: digest `9ddbcf24…`; 353 302 / 351 738 / 405 740
    sobrevivientes con demanda 1,0 / 0,9 / 1,1.
- **Dos pares por caso son LACTATE_COMPATIBLE**, los dos con 57m en el par grave (D0 60, entrega 0,6):
  - con 72f en el par medio (20, 0,85): **216** sobrevivientes;
  - con 72f en el par mixto (60, 1,0): **25 613** sobrevivientes.
  - En ambos, todos los sobrevivientes pasan FD-LAC-04/05 evaluadas en los dos casos, con T* igual al inicio de la
    adecuación, D coherente y L3 adecuada hasta 120.
  - Los representantes LOW / MID / HIGH no tienen contradicciones de paciente, y sus relecturas completas son exactas.
  - Los otros 5 pares admisibles no tienen ningún sobreviviente con demanda 1,0. Uno de ellos, 57m medio con 72f
    «ninguno», tiene 168 sólo con 1,1.
- **Ningún candidato conjunto es robusto a la demanda** en los dos pares compatibles: 0 robustos. Se informa y no filtra,
  como en P2I-2AD.
  - El par con 72f medio no tiene sobrevivientes con 0,9.
  - El par con 72f mixto tiene sobrevivientes con 0,9 (8184) y con 1,1 (8631), pero ninguno común a las dos demandas.
  - Comprobación aparte, fuera del registro. Se hizo con un script de diagnóstico no commiteado que usa el mismo
    módulo congelado, y la revisión adversarial la reprodujo con sus propias sondas:
    - el mismo cálculo sobre los pares atados da 63 859 robustos, igual que P2I-2AD;
    - cada caso por separado sí tiene candidatos robustos: 57m, 9420; 72f, 164 461 en el par medio y 123 686 en el
      mixto;
    - un candidato conjunto exige el mismo conjunto P3, el mismo punto de cristaloide y el mismo λ base para los dos
      casos, y ninguno pasa con las tres demandas.
- **Superficie de llegada de la FC.** Se recorrieron 2 pares compatibles × 9 pares de intrínseca × 25 ganancias × 3
  techos = 1350 candidatos.
  - Compatibles con 57m: 66; con 72f: 84.
  - **Conjuntamente compatibles: 10**, con 10 predicciones distintas, en los dos pares.
  - El apoyo es estrecho:
    - intrínseca 100 / 100 (5), 60 / 100 (3) y 60 / 60 (2); nunca 80;
    - ganancia aguda 1,46 (6), 5,58 (3) y 0,382 (1);
    - ganancia de deuda 0,0103 (8) y 0,0407 (2);
    - techos 150 (4), 175 (4) y 200 (2): el techo no queda identificado.
- **Comparación A / B / C / D: BOTH_CONTRIBUTE confirmado.**
  - Con la severidad y la intrínseca comunes: 0 de 1125.
  - Sólo la severidad por caso: 7 de 450.
  - Sólo la intrínseca por caso: 9 de 3375.
  - Las dos: 10 de 1350.
  - Cada una restaura por sí sola la compatibilidad.
- **Trayectorias, sin envolventes.** Hubo 12 relecturas de validación exactas y 48 corridas completas.
  - Sin tratamiento, la FC sube en 120 minutos: mediana de +26 a +29 lpm en 57m y de +23 a +24 en 72f.
  - La FC máxima de 57m es 171 lpm, y algún candidato queda a 1 lpm de su techo.
  - La taquicardia diferida a los 120 en L3 es pequeña: mediana de 1 a 5 lpm sobre la intrínseca en 57m y de 0 a 1 en
    72f; máximo 21.
  - En L3 varias trayectorias vuelven cerca de su intrínseca. En 57m, con 72f en el par mixto, la FC a los 120 va de 61
    a 105 lpm (mediana 67) sobre lecturas que mezclan intrínsecas de 60 y de 100. El mínimo, 61, está 1,4 lpm sobre
    la intrínseca 60.
  - En 72f con entrega completa, el cristaloide y los GR dan la misma FC hasta los minutos 67–96. Lo comprobó el mismo
    script de diagnóstico (fuera del registro): la FC sólo lee el déficit y D, y ninguno de los dos cambia antes.
- **Veredicto: HR_NUMERIC_DECISION_SURFACE_READY_FOR_FACULTY.** Se cumplen las 8 comprobaciones congeladas.
  - La presión sigue DEFERRED, la tolerancia en ±5 lpm, y las ganancias y los techos son comunes.
  - La FC no eligió la severidad.
  - **Nada se aprobó**: ni un par, ni una intrínseca, ni una ganancia ni un techo.
  - El criterio de la suite es el de la certificación final.

## 1. Decisiones docentes y punto de partida

<!-- generado:decisiones -->
Congelamiento: `805eff4efb562b19f1d280bdd48bbc1d458d0055f104b66f7bc7dca7ea61a861` (una prueba lo fija). Registros de partida: P2I-2AD `5cb48163da4ff081e752b7684f4b036dbcf3e2acb4f94ee1603aaec742fe7fcf` y P2I-2AG `94c94584009449c43b15bd3bb8673bccbead3db86fcf71fa10f508b674ccf763`.

| Decisión docente | Texto registrado |
|---|---|
| fecha | 2026-10-29 |
| severidad | arrival D0 and arrival delivery are patient-state initial conditions: each case may take its own EXISTING certified arrival pair; no new D0 or delivery value, no interpolation, no case-specific sympathetic gain |
| orden clínico | the non-HR perfusion phenotype (57m: BP 88/54, lactate 4.4, CRT 5 s, IVC 0.9 cm near-complete collapse, near-obliterated LV, HCO3 17.3; 72f: 98/62, 3.4, 4 s, 1.1 cm > 50 %, hyperdynamic LV, 19.8) makes 57m more severe; the slightly lower Hb of 72f does not reverse it; no exact severity is derived from a single observation |
| sin FC | the arrival HR (124 / 112) never chooses D0, delivery, a level or a pair; the pairing is frozen before any lactate or HR count |
| recertificación | D / lactate recertified on the current physiology with P2I-2AD's machinery; D and D -> lactate semantics, FD-LAC constraints, blood / fluid ranges, demand values, rho handling and L3 adequacy unchanged; only the arrival case-pair assignment changes |
| intrínseca | intrinsic HR is patient-specific: 60 / 80 / 100 per case, candidate uncertainty, never identified or approved, no extra value |
| fisiología común | acute and debt gains, the smooth saturation law and the total sinus ceilings 150 / 175 / 200 stay common; pressure stays DEFERRED (diagnostic only); arrival tolerance +-5 bpm |
| alcance | shadow only; no HR latent selection, no trajectory envelope, no pressure / RR calibration, collapse, migration or runtime integration |
<!-- /generado:decisiones -->

## 2. Inventario de los pares existentes (P2I-2AI-1)

<!-- generado:inventario -->
| Par (deuda / entrega) | Etiqueta | D0 | entrega | reanclada (÷2,5) | señal aguda | igual en ambos casos | sobrevivientes atados en P2I-2AD | válido |
|---|---|---|---|---|---|---|---|---|
| inferior / superior | none: no debt, full delivery | 0 | 1,00 | 0,40 | 0,00 | sí | 6696 | sí |
| medio / medio | middle | 20 | 0,85 | 0,34 | 0,15 | sí | 155777 | sí |
| superior / inferior | severe: debt and low delivery | 60 | 0,60 | 0,24 | 0,40 | sí | 11916 | sí |
| inferior / inferior | mixed: no debt, low delivery | 0 | 0,60 | 0,24 | 0,40 | sí | 20640 | sí |
| superior / superior | mixed: debt, full delivery | 60 | 1,00 | 0,40 | 0,00 | sí | 158273 | sí |

Procedencia: blood_fluid_readiness.ARRIVAL_PAIRS ('the P2F arrival (debt, delivery) pairs, unchanged (calibration.gi_candidates)'), carried by lactate_rebuild / lactate_closure (P2I-2AB..AD); values from gi_reference.arrival_debt_band and delivery_ratio_band; delivery re-anchored by the extraction reserve 2.5 as the core builds the arrival.
<!-- /generado:inventario -->

## 3. Combinaciones por caso y regla de orden (P2I-2AI-2)

<!-- generado:pares -->
| 57m \ 72f | inferior / superior | medio / medio | superior / inferior | inferior / inferior | superior / superior |
|---|---|---|---|---|---|
| inferior / superior | IDENTICAL | D57_BELOW_D72, DELIVERY57_ABOVE_DELIVERY72 | D57_BELOW_D72, DELIVERY57_ABOVE_DELIVERY72 | DELIVERY57_ABOVE_DELIVERY72 | D57_BELOW_D72 |
| medio / medio | **admisible** | IDENTICAL | D57_BELOW_D72, DELIVERY57_ABOVE_DELIVERY72 | DELIVERY57_ABOVE_DELIVERY72 | D57_BELOW_D72 |
| superior / inferior | **admisible** | **admisible** | IDENTICAL | **admisible** | **admisible** |
| inferior / inferior | **admisible** | D57_BELOW_D72 | D57_BELOW_D72 | IDENTICAL | D57_BELOW_D72 |
| superior / superior | **admisible** | DELIVERY57_ABOVE_DELIVERY72 | DELIVERY57_ABOVE_DELIVERY72 | DELIVERY57_ABOVE_DELIVERY72 | IDENTICAL |

Combinaciones: 25; rechazos analíticos (motivos, una combinación puede tener dos): D57 < D72 8, entrega57 > entrega72 8, idénticas 5; **admisibles: 7**.

Regla congelada: A (57m pair, 72f pair) of the existing support is CLINICALLY_ADMISSIBLE when D0(57m) >= D0(72f) AND delivery(57m) <= delivery(72f) AND at least one inequality is strict (identical pairs are not a case-specific assignment). Ordinal only: it identifies no D0 and no delivery. Otherwise ANALYTIC_REJECTION with every reason: D57_BELOW_D72, DELIVERY57_ABOVE_DELIVERY72, IDENTICAL.
<!-- /generado:pares -->

## 4. La severidad no lee la FC (P2I-2AI-3)

<!-- generado:lectura -->
El constructor de severidad (`pair_values`, `case_pairs`, `admissible`) lee: `57m`, `72f`, `ADMISSIBLE`, `ANALYTIC_REJECTION`, `C57`, `C72`, `D0`, `D57_BELOW_D72`, `DELIVERY57_ABOVE_DELIVERY72`, `Every (57m pair, 72f pair) of the existing support with the frozen ordinal verdict (no physiology run).`, `IDENTICAL`, `PAIRS`, `RESERVE`, `The arrival values of one existing pair for one case, from the case bands only.`, `_level`, `a`, `append`, `arrival_delivery_ratio`, `arrival_oxygen_debt`, `b`, `band`, `bands`, `case`, `case_bands`, `case_pairs`, `debt`, `delivery`, `delivery_reanchored`, `derived`, `dict`, `effective_oxygen_deficit`, `first`, `float`, `gi_reference`, `item`, `level`, `list`, `lower`, `midpoint`, `out`, `pair`, `pair_values`, `ratio`, `reanchored`, `reasons`, `second`, `status`, `str`, `tuple`, `upper`, `x0`. Ninguno es una magnitud de FC (prohibidos: hr, pulse, sympathetic, ceiling, tolerance, authored, legacy, intrinsic, acute, gain, hp, hk, hs, heart). Esta guarda mira sólo los nombres que el constructor lee directamente: `case_bands` construye todas las bandas del caso, también las de FC. Una prueba registra que el constructor lee sólo `arrival_oxygen_debt` y `arrival_delivery_ratio`, y que el orden y los 7 admisibles no cambian con la FC registrada + 50 lpm.
<!-- /generado:lectura -->

## 5. Factorización y equivalencia con P2I-2AD (P2I-2AI-4)

<!-- generado:equivalencia -->
Validación de la factorización (muestra de P2I-2AD, cada caso con su punto): 936 corridas completas; de acuerdo: sí; exactas a la reserva 2,5: sí; desacuerdos: 0.

Equivalencia: los pares atados reproducen la región P2I-2AD — digest `9ddbcf24e6d2a80c404036895fc0ce1512b6e124e7243db771d0bad6dcc8d2a7` (registrado `9ddbcf24e6d2a80c404036895fc0ce1512b6e124e7243db771d0bad6dcc8d2a7`); sobrevivientes por demanda 0,9: 351738; 1: 353302; 1,1: 405740 (registrados 0,9: 351738; 1: 353302; 1,1: 405740). Igual: **sí**.
<!-- /generado:equivalencia -->

## 6. Recertificación de D y lactato por par (P2I-2AI-5, -6, -7)

<!-- generado:recertificacion -->
| Par por caso | candidatos | sobrevivientes (1,0) | 0,9 / 1,0 / 1,1 | robustos a la demanda | FD-LAC-04/05 evaluados | T* = inicio | D coherente | adecuado hasta 120 | estado |
|---|---|---|---|---|---|---|---|---|---|
| 57m (inferior / inferior) · 72f (inferior / superior) | 2225880 | 0 | 0 / 0 / 0 | 0 | 0 | 0 | 0 | 0 | **LACTATE_INCOMPATIBLE (survivors)** |
| 57m (medio / medio) · 72f (inferior / superior) | 2225880 | 0 | 0 / 0 / 168 | 0 | 0 | 0 | 0 | 0 | **LACTATE_INCOMPATIBLE (survivors)** |
| 57m (superior / inferior) · 72f (inferior / inferior) | 2225880 | 0 | 0 / 0 / 0 | 0 | 0 | 0 | 0 | 0 | **LACTATE_INCOMPATIBLE (survivors)** |
| 57m (superior / inferior) · 72f (inferior / superior) | 2225880 | 0 | 0 / 0 / 0 | 0 | 0 | 0 | 0 | 0 | **LACTATE_INCOMPATIBLE (survivors)** |
| 57m (superior / inferior) · 72f (medio / medio) | 2225880 | 216 | 0 / 216 / 1092 | 0 | 216 | 216 | 216 | 216 | **LACTATE_COMPATIBLE** |
| 57m (superior / inferior) · 72f (superior / superior) | 2225880 | 25613 | 8184 / 25613 / 8631 | 0 | 25613 | 25613 | 25613 | 25613 | **LACTATE_COMPATIBLE** |
| 57m (superior / superior) · 72f (inferior / superior) | 2225880 | 0 | 0 / 0 / 0 | 0 | 0 | 0 | 0 | 0 | **LACTATE_INCOMPATIBLE (survivors)** |

Representantes (LOW / MID / HIGH) por par compatible: banderas que excluyen (empeoramiento crítico con gran caída de lactato, normalización instantánea, incompatible con la supervivencia), D fuera de minutos adecuados, minutos críticos bajo la D de llegada y relectura exacta:

| Par por caso | Rep. | banderas que excluyen | D coherente | relectura exacta |
|---|---|---|---|---|
| 57m (superior / inferior) · 72f (medio / medio) | LOW | ninguna | sí | sí |
| 57m (superior / inferior) · 72f (medio / medio) | MID | ninguna | sí | sí |
| 57m (superior / inferior) · 72f (medio / medio) | HIGH | ninguna | sí | sí |
| 57m (superior / inferior) · 72f (superior / superior) | LOW | ninguna | sí | sí |
| 57m (superior / inferior) · 72f (superior / superior) | MID | ninguna | sí | sí |
| 57m (superior / inferior) · 72f (superior / superior) | HIGH | ninguna | sí | sí |

Compatibles con el lactato: 57m (superior / inferior) · 72f (medio / medio), 57m (superior / inferior) · 72f (superior / superior).

Regla: A clinically admissible case pair is LACTATE_COMPATIBLE when P2I-2AD's readiness checks hold on its own region at demand 1.0: at least one survivor; every survivor L3_RESUSCITATION_ADEQUATE_THROUGH_120, FD-LAC-04 PASS or ALREADY_NORMALIZED and FD-LAC-05 PASS (evaluated) in both cases, its FD-LAC-04 T* its adequacy onset and its D falling only across deficit-free minutes; its LOW / MID / HIGH representatives patient-like (no WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL, INSTANT_NORMALIZATION or INCOMPATIBLE_WITH_SURVIVAL flag, no D fall outside adequate minutes, no critical minute below the arrival D) and each full rerun equal to its factorized reading. Otherwise LACTATE_INCOMPATIBLE with the first failing check. Robustness across demand is reported, never a filter (as P2I-2AD). No pair is approved.
<!-- /generado:recertificacion -->

## 7. Superficie de llegada de la FC (P2I-2AI-8, -9)

<!-- generado:superficie -->
Candidatos conjuntos: 1350 (pares compatibles × 9 pares de intrínseca × 25 ganancias × 3 techos); de ellos, compatibles con 57m: 66; con 72f: 84; **conjuntamente compatibles: 10** (10 predicciones distintas) en 2 pares por caso. Descomposiciones de llegada distintas: 675 (compatibles: 57m 11, 72f 28).

| intrínseca 57m \ 72f | inferior | medio | superior |
|---|---|---|---|
| inferior | 2 | 0 | 3 |
| medio | 0 | 0 | 0 |
| superior | 0 | 0 | 5 |

| Dimensión | Apoyo por valor |
|---|---|
| ganancia aguda | 0,1: 0; 0,382: 1; 1,46: 6; 5,58: 3; 21,3: 0 |
| ganancia de deuda | 0,000667: 0; 0,00262: 0; 0,0103: 8; 0,0407: 2; 0,16: 0 |
| techo | 150: 4; 175: 4; 200: 2 |
| par por caso | 57m (superior / inferior) · 72f (medio / medio): 2, 57m (superior / inferior) · 72f (superior / superior): 8 |

Regla: Arrival HR is analytic (derived.heart_rate_decomposition at the case's own arrival pair, P2I-2AG's primary profile: pressure 0): 57m intrinsic 60 / 80 / 100 x 72f intrinsic 60 / 80 / 100 x the five common acute gains x the five common debt gains x the common ceilings 150 / 175 / 200, on the LACTATE_COMPATIBLE case pairs only. JOINT when |HR57 - 124| <= 5 and |HR72 - 112| <= 5. No best candidate.
<!-- /generado:superficie -->

## 8. Comparación A / B / C / D (P2I-2AI-10)

<!-- generado:comparacion -->
| | Diseño | Conjuntos compatibles | Predicciones distintas |
|---|---|---|---|
| A | severidad común, intrínseca común | 0 de 1125 | 0 |
| B | severidad por caso, intrínseca común | 7 de 450 | 7 |
| C | severidad común, intrínseca por caso | 9 de 3375 | 5 |
| D | severidad por caso, intrínseca por caso | 10 de 1350 | 10 |

La severidad por caso restaura compatibilidad: sí; la intrínseca por caso: sí; BOTH_CONTRIBUTE confirmado: **sí**.

Regla: A: the same pair for both cases (the five tied pairs, all valid in P2I-2AD) and the same intrinsic level; B: the LACTATE_COMPATIBLE case pairs, the same intrinsic level; C: the tied pairs, intrinsic per case; D: the LACTATE_COMPATIBLE case pairs, intrinsic per case. Gains and ceilings common in all four; analytic on the same arrival decompositions. A change restores compatibility when its joint count exceeds A's; BOTH_CONTRIBUTE is confirmed when case severity (B) and patient-specific intrinsic (C) each restore it.
<!-- /generado:comparacion -->

## 9. Trayectorias (P2I-2AI-11, sin envolventes)

<!-- generado:trayectorias -->
Recorridas de validación de la FC: 12, exactas: sí. Cada celda: mín. / mediana / máx. sobre representantes × sobrevivientes (lpm).

**57m (superior / inferior) · 72f (medio / medio)** — 2 sobrevivientes

| Lectura | 57m | 72f |
|---|---|---|
| H1 sin tratamiento, minuto 0 | 127 / 129 / 129 | 110 / 111 / 111 |
| H1 sin tratamiento, minuto 30 | 132 / 136 / 136 | 115 / 116 / 116 |
| H1 sin tratamiento, minuto 60 | 137 / 143 / 144 | 120 / 121 / 122 |
| H1 sin tratamiento, minuto 120 | 144 / 155 / 158 | 129 / 133 / 137 |
| H2 cristaloide, minuto 0 | 127 / 129 / 129 | 110 / 111 / 111 |
| H2 cristaloide, minuto 15 | 125 / 127 / 127 | 108 / 108 / 109 |
| H2 cristaloide, minuto 30 | 126 / 128 / 129 | 107 / 108 / 108 |
| H2 cristaloide, minuto 120 | 139 / 146 / 149 | 119 / 123 / 124 |
| H3 GR, minuto 0 | 127 / 129 / 129 | 110 / 111 / 111 |
| H3 GR, minuto 30 | 122 / 123 / 123 | 104 / 104 / 104 |
| H3 GR, minuto 60 | 111 / 111 / 111 | 101 / 101 / 101 |
| H4 manejo definitivo, minuto 60 | 111 / 111 / 111 | 101 / 101 / 101 |
| H4 manejo definitivo, minuto 90 | 104 / 104 / 104 | 100 / 100 / 100 |
| H4 manejo definitivo, minuto 120 | 101 / 101 / 101 | 100 / 100 / 100 |
| H1, cambio de 0 a 120 | 17 / 26 / 29 | 19 / 23 / 26 |
| H1, máximo | 144 / 155 / 158 | 129 / 133 / 137 |
| H4, cambio de 60 a 120 | -10 / -10 / -9 | -1 / -1 / -1 |
| taquicardia diferida en L3 a los 120 (sobre la intrínseca) | 1 / 1 / 1 | 0 / 0 / 0 |
| FC máxima en L1 / L2 / L3 | 144 / 155 / 158 | 129 / 133 / 137 |
| distancia al techo | 5 / 17 / 20 | 17 / 38 / 43 |

**57m (superior / inferior) · 72f (superior / superior)** — 8 sobrevivientes

| Lectura | 57m | 72f |
|---|---|---|
| H1 sin tratamiento, minuto 0 | 119 / 126 / 129 | 113 / 115 / 116 |
| H1 sin tratamiento, minuto 30 | 123 / 134 / 143 | 115 / 119 / 127 |
| H1 sin tratamiento, minuto 60 | 127 / 142 / 156 | 117 / 124 / 140 |
| H1 sin tratamiento, minuto 120 | 135 / 151 / 171 | 121 / 137 / 164 |
| H2 cristaloide, minuto 0 | 119 / 126 / 129 | 113 / 115 / 116 |
| H2 cristaloide, minuto 15 | 110 / 122 / 129 | 100 / 111 / 113 |
| H2 cristaloide, minuto 30 | 107 / 124 / 134 | 85 / 107 / 110 |
| H2 cristaloide, minuto 120 | 129 / 141 / 164 | 67 / 109 / 133 |
| H3 GR, minuto 0 | 119 / 126 / 129 | 113 / 115 / 116 |
| H3 GR, minuto 30 | 94 / 121 / 128 | 85 / 107 / 110 |
| H3 GR, minuto 60 | 71 / 110 / 114 | 69 / 102 / 106 |
| H4 manejo definitivo, minuto 60 | 71 / 110 / 114 | 69 / 102 / 106 |
| H4 manejo definitivo, minuto 90 | 64 / 80 / 109 | 63 / 101 / 104 |
| H4 manejo definitivo, minuto 120 | 61 / 67 / 105 | 61 / 100 / 102 |
| H1, cambio de 0 a 120 | 13 / 29 / 45 | 6 / 24 / 49 |
| H1, máximo | 135 / 151 / 171 | 121 / 137 / 164 |
| H4, cambio de 60 a 120 | -44 / -9 / -9 | -15 / -2 / -2 |
| taquicardia diferida en L3 a los 120 (sobre la intrínseca) | 1 / 5 / 21 | 0 / 1 / 9 |
| FC máxima en L1 / L2 / L3 | 135 / 151 / 171 | 121 / 137 / 164 |
| distancia al techo | 1 / 16 / 65 | 5 / 27 / 79 |

Regla: For each LACTATE_COMPATIBLE case pair with joint arrival survivors: its LOW / MID / HIGH lactate representatives, each case run once by the full core with its own pair (L1, L2 at the representative's crystalloid point, L3), and the primary HR (pressure 0) post-processed for every joint survivor of that pair; distributions (min / median / max) per case over representatives x survivors. One survivor per representative and case is re-run by the full core at L3 (exact HR, else the run stops). No envelope filters anything.
<!-- /generado:trayectorias -->

## 10. Presión (P2I-2AI-12)

La contribución de presión sigue DEFERRED (`PRESSURE_TERM_DIAGNOSTIC_ONLY`): el perfil primario de P2I-2AG la pone en
0 sólo en el análisis; la fisiología común la conserva. Este paquete no la usa para separar los casos.

## 11. Veredicto (P2I-2AI-13)

<!-- generado:veredicto -->
**HR_NUMERIC_DECISION_SURFACE_READY_FOR_FACULTY**

| Comprobación | Resultado |
|---|---|
| severidad por caso sin leer la FC | sí |
| recertificación de D y lactato (factorización, equivalencia, par compatible) | sí |
| intrínseca declarada por caso | sí |
| ganancias comunes | sí |
| al menos un candidato conjunto compatible con la llegada | sí |
| presión aplazada | sí |
| sin regresión de D y lactato | sí |
| reconstrucción de la FC igual al núcleo completo | sí |

Aprobado: no.

Regla congelada: HR_NUMERIC_DECISION_SURFACE_READY_FOR_FACULTY when: (1) the arrival severity is case-specific without HR (severity_reads() names no HR quantity) and at least one case pair is admissible; (2) the D / lactate recertification passes: the factorization agrees with the full core, the tied pairs reproduce P2I-2AD exactly, and at least one admissible pair is LACTATE_COMPATIBLE; (3) the intrinsic rate is declared per case (explicit; no fallback); (4) the gains are common (by construction); (5) at least one jointly arrival-compatible candidate exists (else ARRIVAL_HR_MODEL_REMAINS_STRUCTURALLY_UNRESOLVED); (6) the pressure contribution is 0 in the primary profile; (7) no D / lactate / RR regression (tied equivalence, the core unchanged); (8) no structural contradiction (the HR reconstruction equals the full core on the representatives). The suite criterion is the final certification's. Otherwise HR_NUMERIC_DECISION_SURFACE_NOT_READY with the first blocker. Nothing is approved.
<!-- /generado:veredicto -->

Alcance de las comprobaciones (revisión adversarial):
- `explicit_intrinsic` y `common_gains` valen sí por construcción. La protección real está en otros dos lugares:
  `hp.require_explicit_intrinsic`, que detiene la tabla si falta la intrínseca, y el código, que usa las mismas
  ganancias y techos para los dos casos (una prueba lo fija).
- `pressure_deferred` comprueba la constante del modo primario.
- `no_regression` repite la equivalencia de los pares atados y no evalúa la FR. La no regresión de D, lactato y FR la da
  la certificación final.
- En la clasificación:
  - `adequate_through_120` no puede fallar después del filtro L3, que ya descarta INADEQUATE y LOST;
  - `fd04_05_evaluated` casi tampoco.
  - Las dos son heredadas de P2I-2AD, y lo que discrimina es `survivors`.
- La regla de trayectorias dice que la corrida se detiene si una relectura difiere. El código no se detiene: la marca
  como contradicción estructural y bloquea el veredicto. En esta corrida, las 12 fueron exactas.

## 12. Decisiones que necesita la docencia

Ninguna de estas decisiones la toma el análisis; la docencia las confirma o las reemplaza.

1. **La asignación de severidad por caso.**
   - Sobreviven dos asignaciones, y en las dos 57m está en el par grave (60, 0,6). 72f puede estar en el par medio
     (20, 0,85) o en el mixto (60, 1,0).
   - En el par mixto, 72f llega con la misma deuda que 57m y con la entrega completa. Hay que decidir si eso es
     clínicamente aceptable para su fenotipo (PA 98/62, lactato 3,4).
   - El par medio tiene pocos sobrevivientes (216) y ninguno con demanda 0,9.
2. **La robustez a la demanda.** Ningún candidato conjunto sobrevive a ±10 % de demanda. Hasta hoy la robustez nunca fue
   un filtro (P2I-2AD). Si se exige, la superficie actual queda vacía.
3. **La intrínseca por caso.** El apoyo conjunto usa 100 / 100, 60 / 100 y 60 / 60, nunca 80. Es incertidumbre de
   candidato, no identificación: falta juzgar si esos valores son plausibles para estos pacientes.
4. **Las ganancias y el techo.**
   - Los techos 150, 175 y 200 aparecen los tres. La ganancia aguda se concentra en 1,46, y la de deuda en 0,0103.
   - Ninguno queda identificado ni aprobado, y la selección latente de la FC queda fuera de este paquete.
5. **Lectura de las trayectorias.**
   - La FC se normaliza hasta casi la intrínseca tras el manejo definitivo, y la taquicardia diferida es pequeña.
   - La FC de 72f con entrega completa no distingue el cristaloide de los GR en la primera hora.
   - Falta decidir si estas lecturas son aceptables antes de cualquier envolvente.
6. **El paso siguiente.** La selección latente de la FC, las envolventes, la presión, la FR, el colapso, la migración y la
   integración siguen detenidos hasta una decisión expresa.

## 13. Eficiencia

<!-- generado:eficiencia -->
Trayectorias hemodinámicas: 3178; corridas completas de validación: 936; de representantes: 24; de trayectorias de FC: 48; unidades posprocesadas, suma de los dos casos (demanda 0,9: L1 352350, L3 288179, L2 301800; demanda 1: L1 352350, L3 303405, L2 306900; demanda 1,1: L1 352350, L3 315393, L2 275316); combinaciones de pares: 25; rechazos analíticos: 18; pares admisibles no compatibles con el lactato: 5; descomposiciones de llegada analíticas: 2250; barrido cartesiano: no; motor heredado leído: no.
<!-- /generado:eficiencia -->
