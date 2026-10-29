# P2I-2AD · Cierre semántico de D y del lactato

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución ni migra GI u otra familia;
- no calibra la presión, la FC ni la FR, ni activa el colapso;
- no elige parámetros ocultos ni se ajusta al motor heredado;
- no reutiliza la región histórica de P2F: corre dentro de la guarda de P2I-2AB;
- no cambia FD-LAC-01..06 (`faculty_constraints.py` es idéntico byte a byte).

Código:
- `clinical_core/integration.py`: D no se devuelve en un minuto que cruza al déficit;
- `clinical_core/derived.py`: ganancia D → lactato propia, `debt_to_lactate_gain`;
- `clinical_core/lactate_closure.py`: el análisis, congelado en `c9647c8` antes de evaluar ningún candidato;
- `clinical_core/lactate_closure_report.py`: sólo este informe.

Números: `docs/revision/P2I2AD_lactate_closure.json`. Registros de partida, cerrados: P2I-2AB (`15d05c32…`) y P2I-2AC
(`fc49efae…`), cuyos módulos y registros quedan fijados por sus pruebas.

## 1. Decisiones docentes y punto de partida

<!-- generado:decisiones -->
Congelamiento: `5cb48163da4ff081e752b7684f4b036dbcf3e2acb4f94ee1603aaec742fe7fcf` (una prueba lo fija). Registros de partida: P2I-2AB `15d05c321b38d2e2512642bf2e3be64bc4382ad639ad05ea445c9050091d7cc4` y P2I-2AC `fc49efae455d8a5c259df703a5bcd43bf4c87d3b0ba35dfefdbf1a1567387df5`.

| Decisión docente | Texto registrado |
|---|---|
| devolución de D | D repays only during an interval that stays oxygen-adequate: effective deficit 0 at the start and at the end of the step; crossing 0 -> critical, no repayment and no debt added beyond what the deficit signal adds |
| fecha | 2026-10-29 |
| demanda metabólica | 0.9 / 1.0 / 1.1 explicit uncertainty: ROBUST_ACROSS_DEMAND, DEMAND_SENSITIVE, DEMAND_INCOMPATIBLE; no value approved; robustness never a hard filter |
| FD-LAC-01..06 | FD-LAC-01..06 unchanged (envelopes 57m 4.4-7.0 / 72f 3.4-5.5 at 60 untreated; FD-LAC-04 L(T*+30) < L(T*), no fixed 10 %; FD-LAC-05 57m 1.5-4.0 / 72f 1.2-3.5 with L120 < L(T*); FD-LAC-06 by actual flow and recovering-vs-persistent critical semantics) |
| FC / FR | CAUSAL_PROPAGATION_ACCEPTED; MAGNITUDE_PENDING_HR_RR_CALIBRATION: the corrected D raises HR and RR in untreated runs; D is not reverted; the historical P2F HR1 rejection is not a target; HR and RR are not calibrated here |
| adecuación L3 hasta 120 | L3 adequacy persists through 120: once sustained adequate or compensated oxygen availability begins after haemostasis, effective_deficit stays 0 through minute 120; otherwise L3_RESUSCITATION_LOST, rejected from the final L3 region, never an FD-LAC-05 failure; NOT_EVALUABLE is never a passing final L3 state |
| acople D → lactato | tau_D is debt-repayment kinetics only and must not define D -> lactate production; an independent D_to_lactate_gain, not derived from tau_D or tau_L, not tuned to the legacy, no value chosen |
| ρ | physiological 2.0-3.0, 2.5 representative; 1 only synthetic reference; not in the physiological multiplicity; invariance under re-anchoring reported once |

Espacio de sangre y cristaloide reutilizado de P2I-2AB: 87 conjuntos P1, 458 conjuntos P3 y 12 puntos del cristaloide; lado del lactato nuevo: 2025 puntos. FC / FR: CAUSAL_PROPAGATION_ACCEPTED · MAGNITUDE_PENDING_HR_RR_CALIBRATION; calibradas: no; el rechazo HR1 histórico es objetivo: no.
<!-- /generado:decisiones -->

## 2. D sólo se devuelve en un intervalo adecuado (P2I-2AD-1)

- **Antes (P2I-2AC):** cada minuto leía sólo el déficit al inicio. Un minuto que empezaba sin déficit devolvía D/τ_D
  aunque terminara en déficit crítico.
- **Ahora** (`integration._no_repayment_across`): D se devuelve sólo si el minuto no tiene déficit ni al inicio ni al
  final.
  - Al cruzar de 0 a crítico no se devuelve ni se agrega deuda, porque la señal de déficit del inicio era 0.
  - La entrega del estado final no lee D, así que se conoce antes de fijar D.
  - El integrador no se rediseñó; la corrección es acotada.
- **Ocho invariantes** (`test_clinical_core_debt_semantics.py`, con ρ 1 y 2,5; 24/24):
  1. adecuado → adecuado: devuelve;
  2. adecuado → crítico: no devuelve en el minuto que cruza;
  3. crítico → crítico: no devuelve;
  4. crítico que mejora sin dejar de serlo: no devuelve;
  5. crítico → adecuado: el minuto que termina adecuado todavía acumula, y la devolución empieza en el siguiente;
  6. D nunca es negativa;
  7. la repetición, la serialización y la procedencia siguen exactas;
  8. una llegada justo en la entrega crítica no pasa ningún minuto crítico bajo su D de llegada.

<!-- generado:deuda -->
| Comprobación | Resultado |
|---|---|
| Corridas completas del núcleo corregido comparadas | 936 |
| Coinciden todas (lactato, D, déficit, flujo, eventos y veredictos) | sí |
| Exactas con ρ 2,5 (demanda 0,9, 1, 1,1) | sí |
| ρ comparadas | 1, 2, 2,5, 3 (1 sólo como referencia sintética) |
| Mayor diferencia fuera de ρ 2,5 | 2,1e-14 |
| D baja sólo en minutos sin déficit al inicio ni al final | sí |
| Desacuerdos | 0 |
| El paso de lactato lee k y no τ_D ni G | sí |

| Región de P2I-2AC (candidatos) | Con la D de P2I-2AC | Con la D de P2I-2AD |
|---|---|---|
| con dos o más minutos críticos bajo su D de llegada | 95 698 | 0 |
| · con entrega de llegada superior (95 698 de 345 490) | 95 698 | 0 |
| máximo de minutos críticos bajo la D de llegada | 63 | 0 |

| Eficiencia | Valor |
|---|---|
| Trayectorias hemodinámicas simuladas (compartidas por las tres demandas) | 3 178 |
| Corridas del producto ingenuo (candidatos × 3 escenarios × 2 casos × 3 demandas) | 200 329 200 |
| Corridas completas de validación / de representativos | 936 / 12 |
| Unidades posprocesadas (unidad × lado del lactato) | ×0,9: L1 176 175, L2 95 640, L3 113 994; ×1: L1 176 175, L2 96 000, L3 111 666; ×1,1: L1 176 175, L2 93 672, L3 114 708 |
| Filas de sangre reutilizadas de P2I-2AB (no recalculadas) | 5 226 |
| Rechazos analíticos | 0 |
<!-- /generado:deuda -->

### 2.1 Lectura

- **El 27,7 % afectado en P2I-2AC queda resuelto.** Los 95 698 candidatos de esa región con entrega de llegada
  superior empezaban en el empate exacto y pasaban de 2 a 63 minutos críticos con D bajo su valor de llegada. Con la
  D de P2I-2AD, ninguno: es así por construcción de la regla, y lo respaldan las corridas completas de la validación y
  de los representativos.
- **La factorización sigue siendo exacta:** 936 corridas completas del núcleo coinciden. La hemodinámica de P2I-2AC
  (entrega, demanda, hemostasia, flujo, detención) no lee D ni las ganancias, así que no hubo que rehacer ninguna
  trayectoria por la semántica.

## 3. Ganancia D → lactato independiente (P2I-2AD-2 y 3)

- **Antes:** la producción era k = G / (τ_D τ_L), con G leído como ganancia de estado estacionario de la D anterior a
  P2I-2AC.
- **Ahora:**
  - el núcleo lee `debt_to_lactate_gain` (k): mmol/L de lactato por minuto y por unidad de D;
  - en la cadena del lactato, τ_D sólo fija la devolución de D y τ_L sólo el aclaramiento;
  - **fuera de ella, el impulso simpático (FC) todavía lee D / τ_D** (`derived.sympathetic_target`; revisión
    adversarial, §14). Con D sólo acumulando, τ_D 30 / 60 / 120 dan la misma D y el mismo lactato, pero la FC a los
    90 min es 99,6 / 95,4 / 93,3 lpm. No se toca aquí: es del dominio de la FC;
  - G (`lactate_per_output_deficit`) ya no llega al núcleo y queda sólo para leer los registros históricos;
  - el valor por defecto es el mismo número que daba el anterior (2 / 3600), es provisional y no se elige.

<!-- generado:ganancia -->
Rango anterior: **OLD_G_RANGE_SEMANTICALLY_INVALID**. G (lactate_per_output_deficit, 2 / 6 / 12) was read as the steady-state lactate excess per unit of g x sustained deficit of the pre-P2I-2AC D (D* = g s tau_D, X* = k D* tau_L = G g s), with k = G / (tau_D tau_L). Since P2I-2AC D has no steady state under a deficit, and one G maps to nine production constants across the tau_D x tau_L grid: the G range carries tau_D in its units and cannot be translated into a gain independent of tau_D. The production constants the old grid induced are reported for comparison only.

| Elemento | Valor |
|---|---|
| Unidades | mmol/L per minute per unit of D (index-minutes) |
| Horizonte de FD-LAC-02/03 | 60 min |
| Resolución de las envolventes docentes | 0,1 mmol/L |
| Mayor amplitud de la envolvente a 60 min sin tratamiento | 2,6 mmol/L |
| Niveles de D de llegada declarados (medio / superior) | 20 / 60 |
| Extremo bajo = resolución / (horizonte × D superior) | 2,78e-05 |
| Extremo alto = amplitud / (horizonte × D medio) | 0,00217 |
| Puntos (razón constante 2,97) | 2,78e-05, 8,26e-05, 0,000245, 0,000729, 0,00217 |
| Valor por defecto del núcleo (provisional, no elegido) | 0,000556 |
| Constantes que inducía la rejilla anterior (sólo comparación) | 6,94e-05, 0,000139, 0,000208, 0,000278, 0,00037, 0,000417, 0,000556, 0,000741, 0,000833, 0,00111, 0,00148, 0,00167, 0,00222, 0,00333, 0,00444, 0,00889 |

| Parámetro | Papel | Dónde actúa | Cómo llega al lactato |
|---|---|---|---|
| g (déficit → D) | deficit -> D accumulation per minute (g) | while the deficit at the start of a minute is > 0 | only as k x g |
| τ_D | D repayment kinetics (tau_D) | only across minutes with no deficit at start and end | through D's repayment only; never production |
| k (D → lactato) | D -> lactate production per minute (k) | every minute, on the D of the minute before | only as k x g and k x arrival D |
| τ_L | lactate clearance (tau_L) | every minute, on the excess | directly (clearance) |
| D de llegada (D0) | D at arrival (D0) | start value of D; repaid like any D | only as k x D0 |
| exceso de lactato de llegada (X0) | clearable lactate at arrival (X0) | start value of the excess | directly (X0 cleared with tau_L) |
<!-- /generado:ganancia -->

### 3.1 Lectura

- **El rango histórico de G no se traduce:**
  - sus unidades llevan τ_D: un mismo G da nueve constantes según τ_D y τ_L;
  - su lectura de estado estacionario dejó de existir con P2I-2AC.
- **El rango nuevo se construyó antes de cualquier conteo**, con consistencia dimensional, las envolventes
  docentes y sondas sintéticas: una deuda constante durante 60 min, sin acumulación ni aclaramiento.
  - Toma la escala de D de la banda de la deuda de llegada (niveles 20 y 60).
  - La revisión adversarial lo señala: esa banda es candidata (su forma es una decisión docente pendiente) y su
    nivel superior, 60, se describió como el estado estacionario de un déficit total con τ_D 60. Así τ_D entra de
    forma indirecta en los extremos del rango.
  - **Extremo bajo:** la deuda declarada más alta (60) mueve el lactato sólo 0,1 mmol/L, la resolución de las
    envolventes.
  - **Extremo alto:** la deuda declarada no nula más baja (20) cubre la mayor amplitud de la envolvente sin
    tratamiento a 60 min (2,6 mmol/L).
  - **Puntos:** cinco, en escala logarítmica, cruzados con todos los τ_D.
- **No identificable por separado:** el lactato lee g, k y D0 sólo como k × g y k × D0.

## 4. Filtro (P2I-2AD-4 y 5)

- **Orden congelado antes de ver conteos:** el de P2I-2AC, por costo: L1, después L3, después L2.
- **Dentro de L3, el primer fallo se lee en este orden:**
  1. L3_RESUSCITATION_INADEQUATE;
  2. L3_RESUSCITATION_LOST;
  3. FD-LAC-04;
  4. FD-LAC-05;
  5. FD-LAC-06 con sangrado activo;
  6. FD-LAC-06 con sangrado residual.
- **Cada restricción se evalúa en los dos casos.** Hay 11 129 400 candidatos: 458 conjuntos P3 × 12 puntos de
  cristaloide × 2025 puntos del lado del lactato.

<!-- generado:filtro -->
Demanda 1,0 (la región). Candidatos: 11 129 400; sobrevivientes: **353 302** (3,2 %).

| Etapa | Entran | Rechazados (SIMULATION_REJECTION) | ANALYTIC_REJECTION | Sobreviven | Unidades evaluadas / rechazadas |
|---|---|---|---|---|---|
| L1 (sin tratamiento) | 11 129 400 | 9 789 408 | 0 | 1 339 992 | 176 175 / 154 926 |
| L3 (sangre + hemostasia) | 1 339 992 | 897 876 | 0 | 442 116 | 111 666 / 74 823 |
| L2 (cristaloide con sangrado) | 442 116 | 88 814 | 0 | 353 302 | 96 000 / 17 232 |

| Etapa | Restricción y caso | Primer fallo | Cualquier fallo |
|---|---|---|---|
| L1 | FD-LAC-02/03 57m | 9 325 188 | 9 325 188 |
| L1 | FD-LAC-02/03 72f | 447 732 | 9 226 800 |
| L1 | FD-LAC-01 57m | 16 488 | 7 539 948 |
| L1 | FD-LAC-01 72f | 0 | 6 225 768 |
| L1 | FD-LAC-06 57m | 0 | 7 765 272 |
| L1 | FD-LAC-06 72f | 0 | 6 816 744 |
| L3 | L3_RESUSCITATION_INADEQUATE 57m | 347 112 | 347 112 |
| L3 | L3_RESUSCITATION_INADEQUATE 72f | 98 172 | 445 284 |
| L3 | L3_RESUSCITATION_LOST 72f | 9 396 | 9 396 |
| L3 | FD-LAC-04 57m | 78 816 | 111 540 |
| L3 | FD-LAC-04 72f | 158 808 | 245 376 |
| L3 | FD-LAC-05 57m | 184 272 | 469 596 |
| L3 | FD-LAC-05 72f | 21 300 | 402 708 |
| L3 | FD-LAC-06 (residual bleeding) 57m | 0 | 180 |
| L2 | FD-LAC-06 57m | 83 221 | 83 221 |
| L2 | FD-LAC-06 72f | 5 593 | 23 030 |

| Etapa | Única restricción que rechaza | Candidatos |
|---|---|---|
| L1 | FD-LAC-02/03 | 2 024 136 |
| L3 | L3_RESUSCITATION_INADEQUATE | 377 844 |
| L3 | L3_RESUSCITATION_LOST | 1 476 |
| L3 | FD-LAC-04 | 8 172 |
| L3 | FD-LAC-05 | 205 572 |
| L2 | FD-LAC-06 | 88 814 |
<!-- /generado:filtro -->

### 4.1 Lectura

- **La adecuación L3 sigue siendo el rechazo propio más grande:** 377 844 candidatos tienen
  L3_RESUSCITATION_INADEQUATE como única causa, y 379 320 si se suman los 1476 que sólo tienen
  L3_RESUSCITATION_LOST.
- **L3_RESUSCITATION_LOST rechaza a 9396 candidatos de 72f** cuya adecuación, recuperada en T*, se pierde antes de
  los 120 min. En 1476 es la única causa. Nunca cuenta como fallo de FD-LAC-05 ni pasa como NOT_EVALUABLE.
- **Rechazos analíticos:** 0. No se conoce ninguna imposibilidad exacta antes de simular. Ninguna trayectoria se
  detuvo.

## 5. Demanda metabólica 0,9 / 1,0 / 1,1

<!-- generado:demanda -->
Each candidate is filtered at demand x 0.9, x 1.0 and x 1.1 (the case's metabolic_demand_baseline scaled; demand reaches only the deficit, checked on full core runs). ROBUST_ACROSS_DEMAND: survives at all three; DEMAND_SENSITIVE: at one or two; DEMAND_INCOMPATIBLE: at none. Reported, never a filter: the final region is the one at 1.0, whatever its robustness.

| Demanda | Sobrevivientes |
|---|---|
| ×0,9 | 351 738 |
| ×1 | 353 302 |
| ×1,1 | 405 740 |

| Clase | Candidatos |
|---|---|
| ROBUST_ACROSS_DEMAND | 63 859 |
| DEMAND_SENSITIVE | 673 381 |
| DEMAND_INCOMPATIBLE | 10 392 160 |

| Sobrevive con demanda | Candidatos |
|---|---|
| 0,9 | 173 171 |
| 0,9 y 1 | 108 240 |
| 0,9 y 1 y 1,1 | 63 859 |
| 0,9 y 1,1 | 6 468 |
| 1 | 50 089 |
| 1 y 1,1 | 131 114 |
| 1,1 | 204 299 |

En la región (demanda 1,0): ROBUST_ACROSS_DEMAND 63 859, DEMAND_SENSITIVE 289 443.

Filtro con demanda ×0,9 (sólo informa):

| Etapa | Entran | Rechazados (SIMULATION_REJECTION) | ANALYTIC_REJECTION | Sobreviven | Unidades evaluadas / rechazadas |
|---|---|---|---|---|---|
| L1 (sin tratamiento) | 11 129 400 | 9 761 472 | 0 | 1 367 928 | 176 175 / 154 519 |
| L3 (sangre + hemostasia) | 1 367 928 | 930 360 | 0 | 437 568 | 113 994 / 77 530 |
| L2 (cristaloide con sangrado) | 437 568 | 85 830 | 0 | 351 738 | 95 640 / 16 056 |

| Etapa | Restricción y caso | Primer fallo | Cualquier fallo |
|---|---|---|---|
| L1 | FD-LAC-02/03 57m | 9 444 876 | 9 444 876 |
| L1 | FD-LAC-02/03 72f | 290 568 | 9 323 292 |
| L1 | FD-LAC-01 57m | 12 204 | 6 229 872 |
| L1 | FD-LAC-01 72f | 0 | 3 577 896 |
| L1 | FD-LAC-06 57m | 3 264 | 8 073 444 |
| L1 | FD-LAC-06 72f | 10 560 | 7 049 004 |
| L3 | L3_RESUSCITATION_INADEQUATE 57m | 154 980 | 154 980 |
| L3 | L3_RESUSCITATION_INADEQUATE 72f | 117 180 | 272 160 |
| L3 | L3_RESUSCITATION_LOST 57m | 0 | 18 900 |
| L3 | FD-LAC-04 57m | 114 108 | 163 536 |
| L3 | FD-LAC-04 72f | 184 392 | 298 500 |
| L3 | FD-LAC-05 57m | 291 000 | 639 852 |
| L3 | FD-LAC-05 72f | 68 700 | 608 292 |
| L3 | FD-LAC-06 (residual bleeding) 57m | 0 | 144 |
| L3 | FD-LAC-06 (residual bleeding) 72f | 0 | 108 |
| L2 | FD-LAC-06 57m | 83 904 | 83 904 |
| L2 | FD-LAC-06 72f | 1 926 | 39 957 |

| Etapa | Única restricción que rechaza | Candidatos |
|---|---|---|
| L1 | FD-LAC-02/03 | 1 668 720 |
| L1 | FD-LAC-06 | 13 824 |
| L3 | L3_RESUSCITATION_INADEQUATE | 178 308 |
| L3 | FD-LAC-04 | 10 584 |
| L3 | FD-LAC-05 | 359 700 |
| L2 | FD-LAC-06 | 85 830 |

Filtro con demanda ×1,1 (sólo informa):

| Etapa | Entran | Rechazados (SIMULATION_REJECTION) | ANALYTIC_REJECTION | Sobreviven | Unidades evaluadas / rechazadas |
|---|---|---|---|---|---|
| L1 (sin tratamiento) | 11 129 400 | 9 752 904 | 0 | 1 376 496 | 176 175 / 154 398 |
| L3 (sangre + hemostasia) | 1 376 496 | 917 472 | 0 | 459 024 | 114 708 / 76 456 |
| L2 (cristaloide con sangrado) | 459 024 | 53 284 | 0 | 405 740 | 93 672 / 10 967 |

| Etapa | Restricción y caso | Primer fallo | Cualquier fallo |
|---|---|---|---|
| L1 | FD-LAC-02/03 57m | 9 284 076 | 9 284 076 |
| L1 | FD-LAC-02/03 72f | 435 852 | 9 121 608 |
| L1 | FD-LAC-01 57m | 32 976 | 7 247 160 |
| L1 | FD-LAC-01 72f | 0 | 5 972 940 |
| L1 | FD-LAC-06 57m | 0 | 7 466 652 |
| L1 | FD-LAC-06 72f | 0 | 6 423 444 |
| L3 | L3_RESUSCITATION_INADEQUATE 57m | 409 896 | 409 896 |
| L3 | L3_RESUSCITATION_INADEQUATE 72f | 136 044 | 545 940 |
| L3 | L3_RESUSCITATION_LOST 57m | 0 | 10 764 |
| L3 | L3_RESUSCITATION_LOST 72f | 2 448 | 2 448 |
| L3 | FD-LAC-04 57m | 52 104 | 104 760 |
| L3 | FD-LAC-04 72f | 116 352 | 170 568 |
| L3 | FD-LAC-05 57m | 170 880 | 428 772 |
| L3 | FD-LAC-05 72f | 29 748 | 351 408 |
| L2 | FD-LAC-06 57m | 52 920 | 52 920 |
| L2 | FD-LAC-06 72f | 364 | 7 181 |

| Etapa | Única restricción que rechaza | Candidatos |
|---|---|---|
| L1 | FD-LAC-02/03 | 2 286 252 |
| L3 | L3_RESUSCITATION_INADEQUATE | 444 708 |
| L3 | L3_RESUSCITATION_LOST | 312 |
| L3 | FD-LAC-05 | 200 628 |
| L2 | FD-LAC-06 | 53 284 |
<!-- /generado:demanda -->

### 5.1 Lectura

- **La región es la del filtro con demanda 1,0.** La robustez no filtra y la demanda no se aprueba.
- **Clasificación de los 353 302 de la región:** 63 859 son ROBUST_ACROSS_DEMAND y 289 443 DEMAND_SENSITIVE.

## 6. Región, adecuación hasta 120 y FD-LAC-04/05

<!-- generado:region -->
**FACULTY-CONSTRAINED CURRENT-PHYSIOLOGY LACTATE REGION (no value selected or approved)**: 7 128 unidades (P1 × lado del lactato), 353 302 candidatos; resumen de la región `9ddbcf24e6d2a80c404036895fc0ce1512b6e124e7243db771d0bad6dcc8d2a7`.

| Lectura (mín · p5 · mediana · p95 · máx) | 57m | 72f |
|---|---|---|
| L60 sin tratamiento (mmol/L) | 4,40 · 4,42 · 4,67 · 6,03 · 6,17 | 3,46 · 3,62 · 3,98 · 5,23 · 5,33 |
| L120 con L3 (mmol/L) | 2,32 · 2,86 · 3,62 · 3,94 · 4,00 | 2,29 · 2,73 · 3,15 · 3,41 · 3,50 |
| D a los 120′ con L3 | 0,00 · 0,53 · 3,34 · 21,98 · 21,98 | 0,00 · 0,60 · 3,55 · 21,98 · 25,61 |
| L(T*) (mmol/L) | 3,14 · 3,75 · 4,23 · 4,62 · 4,80 | 2,92 · 3,20 · 3,52 · 3,98 · 4,28 |
| caída a T* + 30 (fracción) | 0,03 · 0,04 · 0,07 · 0,14 · 0,17 | 0,00 · 0,01 · 0,05 · 0,12 · 0,15 |

| Estado entre los sobrevivientes | 57m | 72f |
|---|---|---|
| L3 L3_RESUSCITATION_ADEQUATE_THROUGH_120 | 353 302 (100,0 %) | 353 302 (100,0 %) |
| FD-LAC-01 PASS | 353 302 (100,0 %) | 353 302 (100,0 %) |
| FD-LAC-04 PASS | 353 302 (100,0 %) | 353 302 (100,0 %) |
| FD-LAC-05 PASS | 353 302 (100,0 %) | 353 302 (100,0 %) |
| FD-LAC-04 y 05 evaluadas en ambos casos | 353 302 (100,0 %) | |
| T* de FD-LAC-04 = inicio de la adecuación L3 (ambos casos) | 353 302 | |
| D baja fuera de minutos sin déficit (L3) | 0 | |

| Sensibilidad de FD-LAC-04 (diagnóstico, no filtra) | Sobrevivientes que también pasarían |
|---|---|
| cualquier caída | 353 302 (100,0 %) |
| caída ≥ 5 % | 187 174 (53,0 %) |
| caída ≥ 10 % | 30 852 (8,7 %) |
| caída ≥ 15 % | 576 (0,2 %) |

| T* de FD-LAC-04 | 57m: minuto 60 353 302; 72f: minuto 60 353 302 |
<!-- /generado:region -->

### 6.1 Lectura

- **Todos los sobrevivientes mantienen la adecuación L3 desde T* = 60 hasta 120** en los dos casos.
- **FD-LAC-04 y 05 pasan evaluadas en todos.** No queda ningún NOT_EVALUABLE.
- **El T* de FD-LAC-04 coincide en todos con el inicio de la adecuación:** una sola definición de restauración. Es
  así por construcción, porque la adecuación usa la misma `restoration_trigger`.
- **La región está truncada arriba en k:** 78 207 sobrevivientes (22 %) están en el extremo alto del rango (§14).
- **Caída mediana a los 30 min de T*:** 7,0 % (57m) y 5,3 % (72f). Los umbrales de 5, 10 y 15 % son sólo
  diagnóstico.

## 7. Identificabilidad (P2I-2AD-3)

<!-- generado:identificabilidad -->
| Dimensión | Explorado | Sobrevive (candidatos) | Clase | Borde | P2I-2AC | Cambio |
|---|---|---|---|---|---|---|
| B0 (mL) | 3000, 4000, 5000 | 3000 91 848, 4000 147 411, 5000 114 043 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| entrega de llegada | inferior, medio, superior | inferior 32 556, medio 155 777, superior 164 969 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| exceso de lactato de llegada | inferior, medio, superior | inferior 102 945, medio 126 037, superior 124 320 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| deuda de llegada | inferior, medio, superior | inferior 27 336, medio 155 777, superior 170 189 | no identificable por separado | abierto en ambos bordes | mal identificado (3) | SAME |
| par (deuda, entrega) de llegada | deuda inferior · entrega inferior, deuda inferior · entrega superior, deuda medio · entrega medio, deuda superior · entrega inferior, deuda superior · entrega superior | deuda inferior · entrega inferior 20 640, deuda inferior · entrega superior 6 696, deuda medio · entrega medio 155 777, deuda superior · entrega inferior 11 916, deuda superior · entrega superior 158 273 | mal identificado | — | parcialmente acotado (4) | WIDER |
| tasa de sangrado (mL-eq/min) | 2,5, 5, 6 | 2,5 178 595, 5 100 171, 6 74 536 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| F0 | 0,2 | 0,2 353 302 | no varía | — | no varía (1) | SAME |
| Finf | 0,05, 0,1 | 0,05 205 914, 0,1 147 388 | mal identificado | abierto en ambos bordes | mal identificado (2) | SAME |
| punto del cristaloide | 12 puntos | 12 sobreviven (28 473 a 30 177 cada uno) | mal identificado | — | mal identificado (12) | SAME |
| τ del cristaloide (min) | 30, 60, 90, 120, 150, 180, 210, 240 | 30 28 473, 60 57 671, 90 58 327, 120 59 146, 150 59 637, 180 29 821, 210 30 050, 240 30 177 | mal identificado | abierto en ambos bordes | mal identificado (8) | SAME |
| τ_D (min) | 30, 60, 120 | 30 169 101, 60 124 317, 120 59 884 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| ganancia déficit→D (g) | 0,5, 1, 2 | 0,5 97 554, 1 124 121, 2 131 627 | no identificable por separado | abierto en ambos bordes | no identificable por separado (3) | SAME |
| ganancia D→lactato (k) | 5 valores, 2,78e-05 a 0,00217 | 3 sobreviven, 0,000245 a 0,00217 | no identificable por separado | abierto arriba | — | — |
| demanda (×) | 0,9, 1, 1,1 | 0,9 351 738, 1 353 302, 1,1 405 740 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| k × D0 | 11 valores, 0 a 0,13 | 5 sobreviven, 0 a 0,0437 | parcialmente acotado | abierto abajo | — | — |
| k × g | 15 valores, 1,39e-05 a 0,00433 | 9 sobreviven, 0,000123 a 0,00433 | parcialmente acotado | abierto arriba | — | — |
| τ del lactato (min) | 45, 120, 240 | 45 32 868, 120 97 522, 240 222 912 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| capacidad del relleno (mL) | 100, 500, 1000 | 100 81 844, 500 135 729, 1000 135 729 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| meta del relleno | 0,5, 0,75, 1 | 0,5 106 614, 0,75 120 750, 1 125 938 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| τ del relleno (min) | 120, 240, 480 | 120 152 158, 240 97 978, 480 103 166 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| posición 57m | 0,35, 0,5 | 0,35 28 944, 0,5 324 358 | mal identificado | abierto en ambos bordes | mal identificado (2) | SAME |
| posición 72f | 0,45, 0,6 | 0,45 28 944, 0,6 324 358 | mal identificado | abierto en ambos bordes | mal identificado (2) | SAME |
| λ/κ (mL) | 600, 833, 1500 | 600 81 997, 833 67 654, 1500 203 651 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| Hb de la unidad (g/dL) | 18, 20, 22 | 18 100 147, 20 122 311, 22 130 844 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| volumen de la unidad (mL) | 250, 300, 350 | 250 124 822, 300 141 207, 350 87 273 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |

ρ: NON_IDENTIFIABLE (invariant): rho cancels in deficit, D, lactate and adequacy because the arrival ratio is re-anchored as ratio / rho; evaluated at 2.5 (representative of the 2.0-3.0 band), checked at 2.0 and 3.0, 1 only as SYNTHETIC_REFERENCE; never counted in the candidate multiplicity.
<!-- /generado:identificabilidad -->

### 7.1 Lectura

- **No se afirma ninguna mejora de identificabilidad:**
  - ninguna dimensión queda bien acotada;
  - τ_D, τ_L, el exceso de llegada, la entrega y la sangre siguen mal identificados;
  - el par de llegada pasa a mal identificado: ahora sobreviven las cinco combinaciones.
- **Acotan algo:**
  - k: sobreviven sus tres puntos superiores, con el **borde superior abierto**;
  - k × g y k × D0, parcialmente.
- **g, k y la deuda de llegada no son identificables por separado.** Es una estructura algebraica, no falta de datos.
- **ρ es invariante y no se cuenta.**

## 8. Representativos (P2I-2AD-7)

Regla de P2I-2AB: entre los sobrevivientes ordenados por el lactato de 57m en L1 a los 60 min, el primero, el del
medio y el último. Cada uno se vuelve a correr con el núcleo completo (57m y 72f, L1 y L3).

<!-- generado:representativos -->
**LOW** (rango 0): τ_D 30, g 0,5, k 0,00217, τ_L 240, exceso superior, deuda inferior, entrega inferior; tasa 2,5, B0 5000, λ/κ 600, relleno 0,75 / 240 / 500, unidad 20 g/dL × 300 mL, posiciones 0,5 / 0,6; cristaloide F0 0,2 · Finf 0,05 · τ 60.

| Caso · escenario | min | Gasto relativo | DO2 (índice) | Demanda | Déficit | D | Lactato (mmol/L) | Sangrado activo (mL/min) | Estado de O2 |
|---|---|---|---|---|---|---|---|---|---|
| 57m L1 | 0 | 1,000 | 0,240 | 1,00 | 0,400 | 0,0 | 4,40 | 2,50 | CRITICAL |
| 57m L1 | 15 | 0,937 | 0,225 | 1,00 | 0,438 | 3,1 | 4,23 | 2,50 | CRITICAL |
| 57m L1 | 30 | 0,873 | 0,209 | 1,00 | 0,477 | 6,6 | 4,17 | 2,50 | CRITICAL |
| 57m L1 | 60 | 0,743 | 0,178 | 1,00 | 0,555 | 14,3 | 4,40 | 2,50 | CRITICAL |
| 57m L1 | 90 | 0,611 | 0,146 | 1,00 | 0,636 | 23,2 | 5,11 | 2,50 | CRITICAL |
| 57m L1 | 120 | 0,477 | 0,113 | 1,00 | 0,717 | 33,3 | 6,32 | 2,50 | CRITICAL |
| 57m L3 | 0 | 1,000 | 0,240 | 1,00 | 0,400 | 0,0 | 4,40 | 2,00 | CRITICAL |
| 57m L3 | 15 | 1,181 | 0,300 | 1,00 | 0,250 | 2,5 | 4,22 | 2,00 | CRITICAL |
| 57m L3 | 30 | 1,330 | 0,355 | 1,00 | 0,112 | 3,9 | 4,11 | 2,00 | CRITICAL |
| 57m L3 | 60 | 1,552 | 0,453 | 1,00 | 0,000 | 2,5 | 3,95 | 0,25 | COMPENSATED |
| 57m L3 | 90 | 1,546 | 0,451 | 1,00 | 0,000 | 0,9 | 3,67 | 0,25 | COMPENSATED |
| 57m L3 | 120 | 1,541 | 0,449 | 1,00 | 0,000 | 0,3 | 3,37 | 0,25 | COMPENSATED |
| 72f L1 | 0 | 1,000 | 0,240 | 1,00 | 0,400 | 0,0 | 3,40 | 2,50 | CRITICAL |
| 72f L1 | 15 | 0,958 | 0,230 | 1,00 | 0,425 | 3,1 | 3,29 | 2,50 | CRITICAL |
| 72f L1 | 30 | 0,915 | 0,220 | 1,00 | 0,451 | 6,4 | 3,28 | 2,50 | CRITICAL |
| 72f L1 | 60 | 0,829 | 0,198 | 1,00 | 0,504 | 13,5 | 3,59 | 2,50 | CRITICAL |
| 72f L1 | 90 | 0,740 | 0,177 | 1,00 | 0,558 | 21,5 | 4,33 | 2,50 | CRITICAL |
| 72f L1 | 120 | 0,651 | 0,155 | 1,00 | 0,613 | 30,2 | 5,49 | 2,50 | CRITICAL |
| 72f L3 | 0 | 1,000 | 0,240 | 1,00 | 0,400 | 0,0 | 3,40 | 2,00 | CRITICAL |
| 72f L3 | 15 | 1,121 | 0,286 | 1,00 | 0,286 | 2,6 | 3,28 | 2,00 | CRITICAL |
| 72f L3 | 30 | 1,220 | 0,328 | 1,00 | 0,180 | 4,4 | 3,24 | 2,00 | CRITICAL |
| 72f L3 | 60 | 1,368 | 0,404 | 1,00 | 0,000 | 5,5 | 3,28 | 0,25 | COMPENSATED |
| 72f L3 | 90 | 1,364 | 0,403 | 1,00 | 0,000 | 2,0 | 3,20 | 0,25 | COMPENSATED |
| 72f L3 | 120 | 1,360 | 0,402 | 1,00 | 0,000 | 0,7 | 2,99 | 0,25 | COMPENSATED |

| Caso · escenario | Intervalos de 15′ (A / R / P; * sin sangrado) | D baja fuera de minutos sin déficit | Minutos críticos bajo la D de llegada | Adecuación L3 | Igual a la factorización | Marcas |
|---|---|---|---|---|---|---|
| 57m L1 | P P P P P P P P | 0 | 0 | — | sí | ninguna |
| 57m L3 | R R A A A A A A | 0 | 0 | L3_RESUSCITATION_ADEQUATE_THROUGH_120 (T* 60) | sí | ninguna |
| 72f L1 | P P P P P P P P | 0 | 0 | — | sí | ninguna |
| 72f L3 | R R R A A A A A | 0 | 0 | L3_RESUSCITATION_ADEQUATE_THROUGH_120 (T* 60) | sí | ninguna |

**MID** (rango 176 651): τ_D 30, g 1, k 0,000729, τ_L 240, exceso medio, deuda medio, entrega medio; tasa 5, B0 3000, λ/κ 1500, relleno 0,5 / 120 / 500, unidad 18 g/dL × 250 mL, posiciones 0,5 / 0,6; cristaloide F0 0,2 · Finf 0,1 · τ 30.

| Caso · escenario | min | Gasto relativo | DO2 (índice) | Demanda | Déficit | D | Lactato (mmol/L) | Sangrado activo (mL/min) | Estado de O2 |
|---|---|---|---|---|---|---|---|---|---|
| 57m L1 | 0 | 1,000 | 0,340 | 1,00 | 0,150 | 20,0 | 4,40 | 5,00 | CRITICAL |
| 57m L1 | 15 | 0,950 | 0,323 | 1,00 | 0,193 | 22,5 | 4,42 | 5,00 | CRITICAL |
| 57m L1 | 30 | 0,901 | 0,305 | 1,00 | 0,236 | 25,7 | 4,47 | 5,00 | CRITICAL |
| 57m L1 | 60 | 0,804 | 0,270 | 1,00 | 0,324 | 34,1 | 4,67 | 5,00 | CRITICAL |
| 57m L1 | 90 | 0,708 | 0,235 | 1,00 | 0,412 | 45,1 | 5,05 | 5,00 | CRITICAL |
| 57m L1 | 120 | 0,613 | 0,200 | 1,00 | 0,500 | 58,8 | 5,63 | 5,00 | CRITICAL |
| 57m L3 | 0 | 1,000 | 0,340 | 1,00 | 0,150 | 20,0 | 4,40 | 4,00 | CRITICAL |
| 57m L3 | 15 | 1,042 | 0,379 | 1,00 | 0,054 | 21,6 | 4,42 | 4,00 | CRITICAL |
| 57m L3 | 30 | 1,083 | 0,417 | 1,00 | 0,000 | 17,8 | 4,43 | 4,00 | COMPENSATED |
| 57m L3 | 60 | 1,161 | 0,493 | 1,00 | 0,000 | 6,4 | 4,26 | 0,50 | COMPENSATED |
| 57m L3 | 90 | 1,153 | 0,490 | 1,00 | 0,000 | 2,3 | 3,96 | 0,50 | COMPENSATED |
| 57m L3 | 120 | 1,144 | 0,486 | 1,00 | 0,000 | 0,8 | 3,64 | 0,50 | COMPENSATED |
| 72f L1 | 0 | 1,000 | 0,340 | 1,00 | 0,150 | 20,0 | 3,40 | 5,00 | CRITICAL |
| 72f L1 | 15 | 0,967 | 0,328 | 1,00 | 0,179 | 22,5 | 3,48 | 5,00 | CRITICAL |
| 72f L1 | 30 | 0,934 | 0,317 | 1,00 | 0,208 | 25,3 | 3,58 | 5,00 | CRITICAL |
| 72f L1 | 60 | 0,869 | 0,292 | 1,00 | 0,269 | 32,5 | 3,87 | 5,00 | CRITICAL |
| 72f L1 | 90 | 0,806 | 0,267 | 1,00 | 0,332 | 41,4 | 4,29 | 5,00 | CRITICAL |
| 72f L1 | 120 | 0,742 | 0,242 | 1,00 | 0,395 | 52,3 | 4,86 | 5,00 | CRITICAL |
| 72f L3 | 0 | 1,000 | 0,340 | 1,00 | 0,150 | 20,0 | 3,40 | 4,00 | CRITICAL |
| 72f L3 | 15 | 1,028 | 0,375 | 1,00 | 0,062 | 21,6 | 3,48 | 4,00 | CRITICAL |
| 72f L3 | 30 | 1,055 | 0,410 | 1,00 | 0,000 | 19,2 | 3,56 | 4,00 | COMPENSATED |
| 72f L3 | 60 | 1,107 | 0,477 | 1,00 | 0,000 | 6,9 | 3,50 | 0,50 | COMPENSATED |
| 72f L3 | 90 | 1,102 | 0,475 | 1,00 | 0,000 | 2,5 | 3,30 | 0,50 | COMPENSATED |
| 72f L3 | 120 | 1,096 | 0,473 | 1,00 | 0,000 | 0,9 | 3,06 | 0,50 | COMPENSATED |

| Caso · escenario | Intervalos de 15′ (A / R / P; * sin sangrado) | D baja fuera de minutos sin déficit | Minutos críticos bajo la D de llegada | Adecuación L3 | Igual a la factorización | Marcas |
|---|---|---|---|---|---|---|
| 57m L1 | P P P P P P P P | 0 | 0 | — | sí | ninguna |
| 57m L3 | R A A A A A A A | 0 | 0 | L3_RESUSCITATION_ADEQUATE_THROUGH_120 (T* 60) | sí | ninguna |
| 72f L1 | P P P P P P P P | 0 | 0 | — | sí | ninguna |
| 72f L3 | R A A A A A A A | 0 | 0 | L3_RESUSCITATION_ADEQUATE_THROUGH_120 (T* 60) | sí | ninguna |

**HIGH** (rango 353 301): τ_D 30, g 2, k 0,000729, τ_L 240, exceso medio, deuda superior, entrega superior; tasa 2,5, B0 3000, λ/κ 600, relleno 0,75 / 240 / 1000, unidad 22 g/dL × 250 mL, posiciones 0,5 / 0,6; cristaloide F0 0,2 · Finf 0,1 · τ 150.

| Caso · escenario | min | Gasto relativo | DO2 (índice) | Demanda | Déficit | D | Lactato (mmol/L) | Sangrado activo (mL/min) | Estado de O2 |
|---|---|---|---|---|---|---|---|---|---|
| 57m L1 | 0 | 1,000 | 0,400 | 1,00 | 0,000 | 60,0 | 4,40 | 2,50 | COMPENSATED |
| 57m L1 | 15 | 0,937 | 0,375 | 1,00 | 0,063 | 60,9 | 4,83 | 2,50 | CRITICAL |
| 57m L1 | 30 | 0,873 | 0,349 | 1,00 | 0,128 | 63,7 | 5,26 | 2,50 | CRITICAL |
| 57m L1 | 60 | 0,743 | 0,296 | 1,00 | 0,260 | 75,2 | 6,17 | 2,50 | CRITICAL |
| 57m L1 | 90 | 0,611 | 0,242 | 1,00 | 0,395 | 94,7 | 7,30 | 2,50 | CRITICAL |
| 57m L1 | 120 | 0,477 | 0,188 | 1,00 | 0,531 | 122,3 | 8,77 | 2,50 | CRITICAL |
| 57m L3 | 0 | 1,000 | 0,400 | 1,00 | 0,000 | 60,0 | 4,40 | 2,00 | COMPENSATED |
| 57m L3 | 15 | 1,146 | 0,501 | 1,00 | 0,000 | 36,1 | 4,70 | 2,00 | COMPENSATED |
| 57m L3 | 30 | 1,271 | 0,599 | 1,00 | 0,000 | 21,7 | 4,78 | 2,00 | COMPENSATED |
| 57m L3 | 60 | 1,471 | 0,783 | 1,00 | 0,000 | 7,8 | 4,62 | 0,25 | COMPENSATED |
| 57m L3 | 90 | 1,464 | 0,780 | 1,00 | 0,000 | 2,8 | 4,29 | 0,25 | COMPENSATED |
| 57m L3 | 120 | 1,457 | 0,776 | 1,00 | 0,000 | 1,0 | 3,94 | 0,25 | COMPENSATED |
| 72f L1 | 0 | 1,000 | 0,400 | 1,00 | 0,000 | 60,0 | 3,40 | 2,50 | COMPENSATED |
| 72f L1 | 15 | 0,958 | 0,383 | 1,00 | 0,042 | 60,6 | 3,89 | 2,50 | CRITICAL |
| 72f L1 | 30 | 0,915 | 0,366 | 1,00 | 0,086 | 62,5 | 4,37 | 2,50 | CRITICAL |
| 72f L1 | 60 | 0,829 | 0,330 | 1,00 | 0,175 | 70,2 | 5,33 | 2,50 | CRITICAL |
| 72f L1 | 90 | 0,740 | 0,293 | 1,00 | 0,267 | 83,3 | 6,39 | 2,50 | CRITICAL |
| 72f L1 | 120 | 0,651 | 0,256 | 1,00 | 0,360 | 102,0 | 7,65 | 2,50 | CRITICAL |
| 72f L3 | 0 | 1,000 | 0,400 | 1,00 | 0,000 | 60,0 | 3,40 | 2,00 | COMPENSATED |
| 72f L3 | 15 | 1,098 | 0,482 | 1,00 | 0,000 | 36,1 | 3,76 | 2,00 | COMPENSATED |
| 72f L3 | 30 | 1,181 | 0,562 | 1,00 | 0,000 | 21,7 | 3,90 | 2,00 | COMPENSATED |
| 72f L3 | 60 | 1,314 | 0,712 | 1,00 | 0,000 | 7,8 | 3,84 | 0,25 | COMPENSATED |
| 72f L3 | 90 | 1,309 | 0,709 | 1,00 | 0,000 | 2,8 | 3,61 | 0,25 | COMPENSATED |
| 72f L3 | 120 | 1,305 | 0,707 | 1,00 | 0,000 | 1,0 | 3,34 | 0,25 | COMPENSATED |

| Caso · escenario | Intervalos de 15′ (A / R / P; * sin sangrado) | D baja fuera de minutos sin déficit | Minutos críticos bajo la D de llegada | Adecuación L3 | Igual a la factorización | Marcas |
|---|---|---|---|---|---|---|
| 57m L1 | P P P P P P P P | 0 | 0 | — | sí | ninguna |
| 57m L3 | A A A A A A A A | 0 | 0 | L3_RESUSCITATION_ADEQUATE_THROUGH_120 (T* 60) | sí | adecuado con aclaramiento demorado |
| 72f L1 | P P P P P P P P | 0 | 0 | — | sí | ninguna |
| 72f L3 | A A A A A A A A | 0 | 0 | L3_RESUSCITATION_ADEQUATE_THROUGH_120 (T* 60) | sí | adecuado con aclaramiento demorado |
<!-- /generado:representativos -->

### 8.1 Lectura

- **D:** en ningún representativo D baja durante un intervalo crítico, ni pasa un minuto crítico bajo su D de
  llegada. HIGH llega en el empate exacto: su D se mantiene en 60 en el minuto 1 y después acumula.
- **L3 en 57m y 72f:** todos mantienen la adecuación desde T* = 60 hasta 120.
- **Cada corrida completa coincide exactamente con la factorización.**
- **Sin marcas de inverosimilitud.**
- **«Adecuado con aclaramiento demorado»** aparece sólo en L3 de HIGH (57m y 72f). Es informativa: la deuda de llegada
  (60) sigue produciendo lactato mientras se devuelve.

## 9. FC y FR

- **Estado:** CAUSAL_PROPAGATION_ACCEPTED y MAGNITUDE_PENDING_HR_RR_CALIBRATION.
  - La D corregida sube la FC y la FR en las corridas sin tratamiento, y la docencia acepta esa propagación causal.
  - Las magnitudes no están aprobadas.
- **Nada de este paquete lee, apunta a o calibra la FC o la FR.**
- **El rechazo HR1 histórico de P2F no se restaura como objetivo.**

## 10. Legado sólo como referencia

<!-- generado:legado -->
LEGACY REFERENCE, NOT A CALIBRATION TARGET: the family engine's own lactate at 0, 15, 30, 60, 90 and 120 min, read after the filter and the representatives, never by a constraint or an ordering.

| Caso · escenario | 0′ | 15′ | 30′ | 60′ | 90′ | 120′ |
|---|---|---|---|---|---|---|
| 57m L1 | 4,4 | 4,5 | 4,6 | 4,8 | 4,9 | 5,1 |
| 57m L2 | 4,4 | 4,1 | 4,2 | 4,5 | 4,7 | 4,9 |
| 57m L3 | 4,4 | 4,1 | 3,8 | 3,2 | 3,3 | 3,3 |
| 72f L1 | 3,4 | 3,5 | 3,6 | 3,8 | 3,9 | 4,1 |
| 72f L2 | 3,4 | 3,1 | 3,2 | 3,5 | 3,7 | 3,9 |
| 72f L3 | 3,4 | 3,1 | 2,8 | 2,2 | 2,3 | 2,3 |

| Representativo · caso · escenario | núcleo / legado a los 0′, 60′ y 120′ |
|---|---|
| HIGH 57m L1 | 0′ 4,40 / 4,4; 60′ 6,17 / 4,8; 120′ 8,77 / 5,1 |
| HIGH 57m L3 | 0′ 4,40 / 4,4; 60′ 4,62 / 3,2; 120′ 3,94 / 3,3 |
| HIGH 72f L1 | 0′ 3,40 / 3,4; 60′ 5,33 / 3,8; 120′ 7,65 / 4,1 |
| HIGH 72f L3 | 0′ 3,40 / 3,4; 60′ 3,84 / 2,2; 120′ 3,34 / 2,3 |
| LOW 57m L1 | 0′ 4,40 / 4,4; 60′ 4,40 / 4,8; 120′ 6,32 / 5,1 |
| LOW 57m L3 | 0′ 4,40 / 4,4; 60′ 3,95 / 3,2; 120′ 3,37 / 3,3 |
| LOW 72f L1 | 0′ 3,40 / 3,4; 60′ 3,59 / 3,8; 120′ 5,49 / 4,1 |
| LOW 72f L3 | 0′ 3,40 / 3,4; 60′ 3,28 / 2,2; 120′ 2,99 / 2,3 |
| MID 57m L1 | 0′ 4,40 / 4,4; 60′ 4,67 / 4,8; 120′ 5,63 / 5,1 |
| MID 57m L3 | 0′ 4,40 / 4,4; 60′ 4,26 / 3,2; 120′ 3,64 / 3,3 |
| MID 72f L1 | 0′ 3,40 / 3,4; 60′ 3,87 / 3,8; 120′ 4,86 / 4,1 |
| MID 72f L3 | 0′ 3,40 / 3,4; 60′ 3,50 / 2,2; 120′ 3,06 / 2,3 |
<!-- /generado:legado -->

## 11. Preparación (P2I-2AD-8)

<!-- generado:veredicto -->
**LACTATE_PHYSIOLOGY_READY_FOR_HR_DOMAIN**

| Comprobación | Resultado |
|---|---|
| semántica temporal de D coherente | sí |
| factorización exacta | sí |
| la producción de lactato ya no lee τ_D | sí |
| hay sobrevivientes con demanda 1,0 | sí |
| todo sobreviviente mantiene la adecuación L3 hasta 120 | sí |
| FD-LAC-04/05 evaluadas en ambos casos para todo sobreviviente | sí |
| capa de demanda clasificó todos los candidatos | sí |
| representativos verosímiles | sí |
| T* de FD-LAC-04 = inicio de la adecuación L3 | sí |

Regla congelada: LACTATE_PHYSIOLOGY_READY_FOR_HR_DOMAIN when every check holds: (1) D temporal semantics coherent: the factorization validation finds D falling only across deficit-free minutes, no representative run has a D fall outside them or a critical minute below its arrival D, and in P2I-2AC's region no candidate keeps two or more critical minutes below its arrival D; (2) D -> lactate production no longer tied to tau_D (coupling_check); (3) the factorization agrees with the full core; (4) at least one candidate survives at demand 1.0 and every survivor is L3_RESUSCITATION_ADEQUATE_THROUGH_120 in both cases; (5) FD-LAC-04 is PASS or ALREADY_NORMALIZED and FD-LAC-05 PASS in both cases for every survivor (no NOT_EVALUABLE); (6) the demand layer classified every candidate; (7) the representatives are patient-like: no WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL, INSTANT_NORMALIZATION or INCOMPATIBLE_WITH_SURVIVAL flag and every rerun equals its factorized reading; (8) no unresolved lactate semantic contradiction: every survivor's FD-LAC-04 T* is its L3 adequacy onset in both cases. Otherwise LACTATE_PHYSIOLOGY_NOT_READY with the first blocker. Unique identification of hidden parameters is not required. No candidate, value or parameter is selected or approved.

Próximo dominio: Recommended next domain (not started; needs its own authorization): heart rate and the sympathetic response, whose magnitudes the corrected D already moves (MAGNITUDE_PENDING_HR_RR_CALIBRATION); then pressure and vascular tone, unless that analysis finds a more fundamental blocker. Before collapse, GI migration or any runtime integration.
<!-- /generado:veredicto -->

### 11.1 Lectura

- **Se cumplen las ocho condiciones de la regla congelada.** No se exige identificar parámetros únicos.
- **Próximo dominio recomendado, sin empezar:**
  - primero, FC y respuesta simpática;
  - después, presión y tono vascular.

## 12. Congelamiento y entrega

- **Congelamiento:** `c9647c8`, un solo commit, antes de evaluar cualquier candidato. Incluye:
  - las dos correcciones del núcleo y sus pruebas;
  - el rango de k, la adecuación hasta 120 y la capa de demanda;
  - la regla de preparación y las pruebas previas a la corrida.
- **Validación antes de congelar:** la factorización se validó sobre su muestra congelada (936 corridas completas,
  sin desacuerdos), y la suite del núcleo dio 913/913.
  - La muestra no contenía ninguna corrida L3_RESUSCITATION_LOST.
  - Por la revisión se agregó una prueba posterior: una unidad LOST de la región (conjunto P3 59, 72f, perdida en el
    minuto 101) coincide también con corridas completas del núcleo.
- **Corrida:** sobre `c9647c8`, 74 s con 4 procesos, cada uno con la guarda P2F y el bloqueo del legado. El registro
  es el del módulo; `--run` lo reproduce en un solo proceso.
- **Entrega:** un commit ejecutable (`dd585c2`: informe, pruebas sobre el registro, JSON y documentación), sobre el
  que corrió la certificación completa, y uno posterior sólo con documentación, el texto del informe generado y una
  prueba.
- **Revisión adversarial (una sola):**
  - sin BLOCKER; confirmó el núcleo, la adecuación L3, la demanda, ρ, las guardas y los números;
  - su MAJOR: τ_D todavía fija la ganancia D → impulso simpático. Es del dominio de la FC y queda en §3, §14 y TD-92;
  - sus MINOR: la lectura de §8.1, ya corregida; la escala del rango de k y la región truncada, en §3, §6 y §14; los
    documentos históricos que rotulan G, en TD-91(6);
  - sus NIT: procedencia con D = 0, comprobaciones verdaderas por construcción, LOST fuera de la muestra (prueba
    agregada), «sin hemostasia» rotulado STOPPED y redacción, corregidos aquí o en TD-92.

## 13. Qué no hace

- **Parámetros:** no elige ni aprueba ninguno; tampoco la ganancia k, la demanda ni ρ.
- **Restricciones:** no cambia FD-LAC-01..06, sus envolventes ni la fracción residual de L3 (FD-25).
- **Otros límites:**
  - no calibra la FC, la FR ni la presión;
  - no activa el colapso;
  - no migra ni integra nada;
  - no lee el lactato heredado salvo como referencia, después del filtro.

## 14. Decisiones pendientes (docencia)

- **Borde superior de k abierto y escala del rango:**
  - 78 207 sobrevivientes (22 %) tienen k = 2,17e-3, el extremo alto de la regla, y la rejilla anterior llegaba a
    8,9e-3: la región está truncada arriba en k;
  - la regla tomó la escala de D de la banda candidata de la deuda de llegada, cuyo nivel superior arrastra τ_D 60;
  - ¿qué escala de D aprueba la docencia para una regla nueva, congelada antes de contar?
- **τ_D en el impulso simpático:** la FC lee D / τ_D, así que τ_D sigue fijando la ganancia D → FC. Hay que decidirlo
  al abrir el dominio de la FC, con una ganancia propia y un rango fijado antes de cualquier conteo.
- **Valor por defecto del núcleo para k:** 2 / 3600, provisional, el mismo número que antes. Es sólo un marcador de
  continuidad, no un ajuste al legado. Los documentos regenerados que siguen variando G muestran G sin efecto
  (TD-91, punto 6).
- **Magnitudes de FC y FR:** pendientes de la calibración del dominio siguiente.
- **Siguen abiertas:**
  - FD-24 y FD-25;
  - TD-91, con lo que P2I-2AD no invalidó;
  - la autorización del próximo dominio.
