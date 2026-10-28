# P2I-2AC · Deuda de oxígeno acumulada y adecuación de la reanimación L3

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución ni migra GI u otra familia;
- no calibra la presión ni la FC, ni activa el colapso;
- no elige parámetros ocultos ni se ajusta al motor heredado;
- no reutiliza la región histórica de P2F: corre dentro de la guarda de P2I-2AB, que hace fallar cualquier acceso a
  ella;
- no cambia FD-LAC-04 ni FD-LAC-05 (`faculty_constraints.py` es idéntico byte a byte).

Código:
- `clinical_core/integration.py`: la corrección mínima de D en el núcleo;
- `clinical_core/lactate_adequacy.py`: el análisis, congelado en `2a9129e` antes de evaluar ningún candidato;
- `clinical_core/lactate_adequacy_report.py`: sólo este informe.

Números: `docs/revision/P2I2AC_lactate_adequacy.json`. Registro de partida, cerrado: P2I-2AB (`15d05c32…`), cuyo
módulo y cuyo registro quedan fijados por sus pruebas.

## 1. Decisiones docentes y punto de partida

<!-- generado:decisiones -->
Congelamiento: `fc49efae455d8a5c259df703a5bcd43bf4c87d3b0ba35dfefdbf1a1567387df5` (una prueba lo fija). Registro de partida: P2I-2AB `15d05c321b38d2e2512642bf2e3be64bc4382ad639ad05ea445c9050091d7cc4`.

| Decisión docente | Texto registrado |
|---|---|
| sangrado en curso | ongoing bleeding is actual flow (current blood loss rate > 0), not the haemostasis event label; after 60 a residual bleed with a PERSISTENT or WORSENING critical deficit keeps FD-LAC-06's protection; RECOVERING_CRITICAL or deficit == 0 still allows a decline; fraction_after_hemostasis unchanged (FD-25 pending) |
| D (deuda de entrega de O2) | D is accumulated oxygen-delivery debt: while effective_oxygen_deficit > 0 it does not decrease (production continues, repayment suspended, dD >= 0); with deficit == 0 it may repay gradually with tau_D. No channel added; the deficit, DO2, extraction, tau_D, the D gain and the lactate gain unchanged |
| fecha | 2026-10-28 |
| demanda metabólica | metabolic demand 0.9 / 1.0 / 1.1 as explicit uncertainty: ROBUST (all three), DEMAND-SENSITIVE (some), DEMAND-INCOMPATIBLE (none); no value approved, case truth unchanged, robustness never a filter |
| FD-LAC-04 | unchanged: L(T*+30) < L(T*), no fixed 10 %; 5 / 10 / 15 % diagnostic only |
| FD-LAC-05 | unchanged: 57m 1.5-4.0, 72f 1.2-3.5, L120 < L(T*); remaining NOT_EVALUABLE reported with its reason |
| adecuación L3 | L3_RESUSCITATION_ADEQUACY: after 2 red-cell units and haemostasis at 60, sustained effective_deficit == 0 (ADEQUATE or COMPENSATED) begins no later than minute 90 (>= 30 min observed by 120); otherwise L3_RESUSCITATION_INADEQUATE, rejected from the final region and reported apart, never an FD-LAC-04 failure |
| ρ | physiological band 2.0-3.0, 2.5 representative; 1 only as SYNTHETIC_REFERENCE; rho not counted in the candidate multiplicity; reported as non-identifiable (invariant) |

Espacio fuente reutilizado de P2I-2AB: 87 conjuntos P1, 458 conjuntos P3, 12 puntos del cristaloide y 1215 puntos del lado del lactato. ρ en la rejilla de sangre: 1, 2,5, 3 (no se cuenta).
<!-- /generado:decisiones -->

### 1.1 Lectura

- **Qué cambia:** D pasa a ser la deuda de entrega de O2 acumulada. Mientras el déficit efectivo es positivo, D no
  baja; sólo se devuelve, con τ_D, cuando el déficit es 0.
- **Qué no cambia:**
  - la definición del déficit, la DO2 y la extracción;
  - τ_D y las ganancias;
  - la recurrencia del lactato;
  - FD-LAC-04 y 05.
- **El espacio fuente es el de P2I-2AB, leído de su registro comprometido** (resúmenes de congelamiento y de región
  comprobados). Las restricciones de sangre no leen D, la FC ni el lactato, así que la corrección no cambia qué
  conjuntos de sangre pertenecen a ese espacio; no se recalcularon sus 5226 filas.

## 2. Semántica de D (P2I-2AC-1) y factorización

- **Núcleo** (`integration._oxygen_debt`):
  - con déficit > 0: D aumenta g × déficit y no se devuelve nada;
  - con déficit = 0: D baja D / τ_D;
  - siempre dentro del límite del canal (nunca negativa).
- **Convención temporal, sin cambios:** cada minuto lee el déficit que lee el integrador, es decir, la entrega al
  inicio del minuto contra la demanda del minuto. Como la demanda es constante en estos casos, en el primer minuto de
  un tramo crítico D todavía puede devolver un paso: ese minuto empezó sin déficit. Se informa en §8 y no aparece en
  ningún otro minuto.
- **Siete pruebas de invariantes** (`test_clinical_core_debt_semantics.py`, con ρ 1 y 2,5):
  - con déficit crítico que empeora, estable o que mejora sin dejar de ser crítico, D no baja;
  - con déficit 0 puede devolverse, y con adecuación sostenida baja en forma gradual con τ_D;
  - D nunca es negativa;
  - la repetición, la serialización y la procedencia siguen siendo exactas.
- **Efectos en el resto del código:**
  - descomposición del corte P2I-1, sondas de entrega, recurrencia de la sonda previa a la llegada y nota de
    alcanzabilidad de P2G;
  - golden, paquete, corte, sondas y anclas regenerados; el golden por Contracts v2 sigue IDENTICAL;
  - las pruebas vivas de P2I-2AB leen ahora sólo lo que la corrección no tocó.
- **Reevaluación de la factorización:**
  - la hemodinámica no lee D, τ_D ni las ganancias;
  - las trayectorias se simulan una vez por escenario y entrada de sangre, ahora con el flujo real de sangrado de
    cada minuto (el volumen perdido del estado de sangre compartido);
  - D y el lactato se posprocesan con la recurrencia corregida;
  - la validación previa al congelamiento y la de la corrida coinciden; si no, la corrida se habría detenido.

<!-- generado:deuda -->
| Comprobación | Resultado |
|---|---|
| Corridas completas del núcleo corregido comparadas | 936 |
| Coinciden todas (lactato, D, déficit, flujo, eventos y veredictos) | sí |
| Exactas con ρ 2,5 (demanda 0,9, 1, 1,1) | sí |
| ρ comparadas | 1, 2, 2,5, 3 (1 sólo como referencia sintética) |
| Mayor diferencia fuera de ρ 2,5 | 2,1e-14 |
| D nunca cae en un minuto que leyó déficit | sí |
| Desacuerdos | 0 |

Estados que ejerció la muestra: L1 FD-LAC-01 FAIL 27; L1 FD-LAC-01 PASS 207; L1 FD-LAC-02/03 falla 126; L1 FD-LAC-02/03 pasa 108; L1 FD-LAC-06 (residual bleeding) pasa 234; L1 FD-LAC-06 falla 27; L1 FD-LAC-06 pasa 207; L2 FD-LAC-06 (residual bleeding) pasa 468; L2 FD-LAC-06 falla 105; L2 FD-LAC-06 pasa 363; L3 FD-LAC-04 FAIL 10; L3 FD-LAC-04 NOT_EVALUABLE 28; L3 FD-LAC-04 PASS 196; L3 FD-LAC-05 FAIL 22; L3 FD-LAC-05 NOT_EVALUABLE 28; L3 FD-LAC-05 PASS 184; L3 FD-LAC-06 (residual bleeding) pasa 234; L3 FD-LAC-06 pasa 234; L3 L3_RESUSCITATION_INADEQUATE L3_RESUSCITATION_ADEQUATE 206; L3 L3_RESUSCITATION_INADEQUATE L3_RESUSCITATION_INADEQUATE 28.

| Eficiencia | Valor |
|---|---|
| Trayectorias hemodinámicas simuladas (compartidas por las tres demandas) | 3 178 |
| Corridas del producto ingenuo (candidatos × 3 escenarios × 2 casos × 3 demandas) | 120 197 520 |
| Corridas completas de validación / de representativos | 936 / 12 |
| Unidades post-procesadas (unidad × lado del lactato) | ×0,9: L1 105 705, L2 110 508, L3 116 503; ×1: L1 105 705, L2 101 592, L3 113 250; ×1,1: L1 105 705, L2 91 260, L3 121 422 |
| Filas de sangre reutilizadas de P2I-2AB (no recalculadas) | 5 226 |
| Rechazos analíticos | 0 |
<!-- /generado:deuda -->

## 3. Auditoría de las 71 661 caídas tras la hemostasia (P2I-2AC-2)

<!-- generado:auditoria -->
P2I-2AB's survivors re-read with their own (pre-P2I-2AC) D and lactate, never refiltered: on each L3 run, P2I-2AB's flag (a sustained substantial fall during a persistent or worsening deficit after haemostasis) and the actual-flow FD-LAC-06. Class per run: PERSISTENT_OR_WORSENING_WITH_RESIDUAL_BLEEDING when a failing pair lies at or after haemostasis in a window with actual flow (an FD-LAC-06 violation); else RECOVERING_WITH_RESIDUAL_BLEEDING when a recovering decline does (allowed); else NO_RESIDUAL_BLEEDING when P2I-2AB's flagged fall lies where the flow had stopped; else ADEQUATE_OR_COMPENSATED. A candidate takes its worse case, in that order. Also counted: the same survivors' violations with the corrected D.

| Lectura | Candidatos |
|---|---|
| Sobrevivientes de P2I-2AB | 439 291 |
| Señalados por P2I-2AB (caída con déficit persistente tras la hemostasia) | 71 661 (registro: 71 661; reproducido: sí) |
| · déficit persistente o que empeora, con sangrado residual (viola FD-LAC-06) | 71 661 |
| · déficit crítico que se recupera, con sangrado residual (permitido) | 0 |
| · sin sangrado residual en la caída (permitido) | 0 |
| · adecuado o compensado (permitido) | 0 |
| **Violarían FD-LAC-06 con sangrado por flujo real** | **71 661** |
| Sobrevivientes que violan FD-LAC-06 por sangrado residual (D de P2I-2AB) | 71 661 |
| · de ellos, no señalados por P2I-2AB (pares que cruzan la hemostasia) | 0 |
| Sobrevivientes que violan FD-LAC-06 por flujo real, en cualquier ventana (D de P2I-2AB) | 71 661 |
| Con la D corregida: violan por sangrado residual (todos / señalados) | 120 / 120 |
<!-- /generado:auditoria -->

### 3.1 Lectura

- **Las 71 661 caídas violan FD-LAC-06 con el sangrado leído por flujo real.** En L3 la fracción residual
  provisional de 0,1 (FD-25 pendiente) mantiene un sangrado de 0,25 a 0,6 mL-eq/min después de la hemostasia. Así,
  toda caída sostenida del lactato con déficit persistente o que empeora cae en una ventana juzgada.
- **Ningún sobreviviente de P2I-2AB las viola de otra forma:** ni por sangrado residual fuera de lo señalado ni por
  pares que cruzan la hemostasia.
- **Con la D corregida casi desaparecen:** sólo 120 de esos sobrevivientes violarían la protección por sangrado
  residual. Ahora la deuda no se devuelve mientras hay déficit, y el lactato deja de caer.

## 4. Filtro (P2I-2AC-3)

- **Orden congelado antes de ver ningún conteo:** el de P2I-2AB, por costo: L1, después L3, después L2.
- **Dentro de L3**, el primer fallo se lee en el orden de las capas docentes:
  1. adecuación L3;
  2. FD-LAC-04;
  3. FD-LAC-05;
  4. FD-LAC-06 con sangrado activo antes de la hemostasia;
  5. FD-LAC-06 con sangrado residual.
- **Cada restricción se evalúa en los dos casos.** El soporte del cristaloide y la D corregida se aplican a todos los
  candidatos.

<!-- generado:filtro -->
Demanda 1,0 (la región). Candidatos: 6 677 640; sobrevivientes: **345 490** (5,2 %).

| Etapa | Entran | Rechazados (SIMULATION_REJECTION) | ANALYTIC_REJECTION | Sobreviven | Unidades evaluadas / rechazadas |
|---|---|---|---|---|---|
| L1 (sin tratamiento) | 6 677 640 | 5 318 640 | 0 | 1 359 000 | 105 705 / 84 184 |
| L3 (sangre + hemostasia) | 1 359 000 | 881 688 | 0 | 477 312 | 113 250 / 73 474 |
| L2 (cristaloide con sangrado) | 477 312 | 131 822 | 0 | 345 490 | 101 592 / 25 475 |

| Etapa | Restricción y caso | Primer fallo | Cualquier fallo |
|---|---|---|---|
| L1 | FD-LAC-02/03 57m | 4 892 508 | 4 892 508 |
| L1 | FD-LAC-02/03 72f | 392 028 | 4 616 364 |
| L1 | FD-LAC-01 57m | 34 104 | 3 085 320 |
| L1 | FD-LAC-01 72f | 0 | 2 357 808 |
| L1 | FD-LAC-06 57m | 0 | 3 197 856 |
| L1 | FD-LAC-06 72f | 0 | 2 524 764 |
| L3 | L3_RESUSCITATION_INADEQUATE 57m | 341 748 | 341 748 |
| L3 | L3_RESUSCITATION_INADEQUATE 72f | 96 552 | 438 300 |
| L3 | FD-LAC-04 57m | 48 420 | 79 524 |
| L3 | FD-LAC-04 72f | 122 724 | 171 144 |
| L3 | FD-LAC-05 57m | 215 700 | 426 108 |
| L3 | FD-LAC-05 72f | 56 544 | 370 560 |
| L3 | FD-LAC-06 (residual bleeding) 57m | 0 | 300 |
| L2 | FD-LAC-06 57m | 121 957 | 121 957 |
| L2 | FD-LAC-06 72f | 9 865 | 49 705 |

| Etapa | Única restricción que rechaza | Candidatos |
|---|---|---|
| L1 | FD-LAC-02/03 | 2 120 784 |
| L3 | L3_RESUSCITATION_INADEQUATE | 375 720 |
| L3 | FD-LAC-04 | 10 176 |
| L3 | FD-LAC-05 | 272 244 |
| L2 | FD-LAC-06 | 131 822 |

L3_RESUSCITATION_INADEQUATE, informado aparte (nunca como fallo de FD-LAC-04): 57m 341 748; 72f 438 300; como primer fallo de L3: 438 300; como única causa: 375 720.
<!-- /generado:filtro -->

### 4.1 Lectura

- **La adecuación L3 es el rechazo propio más grande.** Rechaza sola 375 720 candidatos con demanda 1,0, informados
  aparte y nunca como fallos de FD-LAC-04.
- **Un candidato inadecuado no puede sobrevivir.** Ya no pasa FD-LAC-04/05 como NOT_EVALUABLE, como ocurría con los
  304 176 de P2I-2AB.
- **La protección por sangrado residual casi no actúa con la D corregida:** 300 candidatos de 57m que, además, fallan
  otras restricciones.
- **Rechazos analíticos:** 0. Ninguna trayectoria se detuvo.

## 5. Demanda metabólica 0,9 / 1,0 / 1,1 como incertidumbre

<!-- generado:demanda -->
Each candidate is filtered at demand x 0.9, x 1.0 and x 1.1 (the case's metabolic_demand_baseline scaled; demand reaches only the deficit, checked on full core runs). ROBUST: survives at all three; DEMAND-SENSITIVE: at one or two; DEMAND-INCOMPATIBLE: at none. Reported, never a filter: the final region is the one at 1.0, whatever its robustness.

| Demanda | Sobrevivientes |
|---|---|
| ×0,9 | 404 371 |
| ×1 | 345 490 |
| ×1,1 | 367 703 |

| Clase | Candidatos |
|---|---|
| ROBUST | 71 079 |
| DEMAND-SENSITIVE | 678 007 |
| DEMAND-INCOMPATIBLE | 5 928 554 |

| Sobrevive con demanda | Candidatos |
|---|---|
| 0,9 | 179 326 |
| 0,9 y 1 | 148 236 |
| 0,9 y 1 y 1,1 | 71 079 |
| 0,9 y 1,1 | 5 730 |
| 1 | 53 821 |
| 1 y 1,1 | 72 354 |
| 1,1 | 218 540 |

En la región (demanda 1,0): ROBUST 71 079, DEMAND-SENSITIVE 274 411.

Filtro con demanda ×0,9 (sólo informa):

| Etapa | Entran | Rechazados (SIMULATION_REJECTION) | ANALYTIC_REJECTION | Sobreviven | Unidades evaluadas / rechazadas |
|---|---|---|---|---|---|
| L1 (sin tratamiento) | 6 677 640 | 5 279 604 | 0 | 1 398 036 | 105 705 / 83 571 |
| L3 (sangre + hemostasia) | 1 398 036 | 874 332 | 0 | 523 704 | 116 503 / 72 861 |
| L2 (cristaloide con sangrado) | 523 704 | 119 333 | 0 | 404 371 | 110 508 / 22 691 |

| Etapa | Restricción y caso | Primer fallo | Cualquier fallo |
|---|---|---|---|
| L1 | FD-LAC-02/03 57m | 4 864 056 | 4 864 056 |
| L1 | FD-LAC-02/03 72f | 318 840 | 4 778 844 |
| L1 | FD-LAC-01 57m | 60 456 | 2 554 704 |
| L1 | FD-LAC-01 72f | 0 | 1 227 492 |
| L1 | FD-LAC-06 57m | 6 636 | 3 494 388 |
| L1 | FD-LAC-06 72f | 29 616 | 2 750 448 |
| L3 | L3_RESUSCITATION_INADEQUATE 57m | 138 744 | 138 744 |
| L3 | L3_RESUSCITATION_INADEQUATE 72f | 104 904 | 243 648 |
| L3 | FD-LAC-04 57m | 66 936 | 106 608 |
| L3 | FD-LAC-04 72f | 135 612 | 202 548 |
| L3 | FD-LAC-05 57m | 329 460 | 583 044 |
| L3 | FD-LAC-05 72f | 98 676 | 593 424 |
| L3 | FD-LAC-06 (residual bleeding) 57m | 0 | 576 |
| L3 | FD-LAC-06 (residual bleeding) 72f | 0 | 864 |
| L2 | FD-LAC-06 57m | 116 863 | 116 863 |
| L2 | FD-LAC-06 72f | 2 470 | 74 815 |

| Etapa | Única restricción que rechaza | Candidatos |
|---|---|---|
| L1 | FD-LAC-02/03 | 1 716 096 |
| L1 | FD-LAC-06 | 36 252 |
| L3 | L3_RESUSCITATION_INADEQUATE | 174 744 |
| L3 | FD-LAC-04 | 2 184 |
| L3 | FD-LAC-05 | 428 136 |
| L2 | FD-LAC-06 | 119 333 |

Filtro con demanda ×1,1 (sólo informa):

| Etapa | Entran | Rechazados (SIMULATION_REJECTION) | ANALYTIC_REJECTION | Sobreviven | Unidades evaluadas / rechazadas |
|---|---|---|---|---|---|
| L1 (sin tratamiento) | 6 677 640 | 5 220 576 | 0 | 1 457 064 | 105 705 / 82 647 |
| L3 (sangre + hemostasia) | 1 457 064 | 1 021 512 | 0 | 435 552 | 121 422 / 85 126 |
| L2 (cristaloide con sangrado) | 435 552 | 67 849 | 0 | 367 703 | 91 260 / 14 105 |

| Etapa | Restricción y caso | Primer fallo | Cualquier fallo |
|---|---|---|---|
| L1 | FD-LAC-02/03 57m | 4 750 356 | 4 750 356 |
| L1 | FD-LAC-02/03 72f | 383 304 | 4 498 068 |
| L1 | FD-LAC-01 57m | 86 916 | 2 781 060 |
| L1 | FD-LAC-01 72f | 0 | 2 112 108 |
| L1 | FD-LAC-06 57m | 0 | 2 887 788 |
| L1 | FD-LAC-06 72f | 0 | 2 219 796 |
| L3 | L3_RESUSCITATION_INADEQUATE 57m | 459 288 | 459 288 |
| L3 | L3_RESUSCITATION_INADEQUATE 72f | 152 316 | 611 604 |
| L3 | FD-LAC-04 57m | 30 744 | 86 880 |
| L3 | FD-LAC-04 72f | 137 928 | 168 672 |
| L3 | FD-LAC-05 57m | 170 928 | 434 304 |
| L3 | FD-LAC-05 72f | 70 308 | 390 444 |
| L2 | FD-LAC-06 57m | 66 842 | 66 842 |
| L2 | FD-LAC-06 72f | 1 007 | 21 967 |

| Etapa | Única restricción que rechaza | Candidatos |
|---|---|---|
| L1 | FD-LAC-02/03 | 2 332 788 |
| L3 | L3_RESUSCITATION_INADEQUATE | 507 324 |
| L3 | FD-LAC-04 | 1 128 |
| L3 | FD-LAC-05 | 241 236 |
| L2 | FD-LAC-06 | 67 849 |
<!-- /generado:demanda -->

### 5.1 Lectura

- **La región es la del filtro con demanda 1,0.** La robustez no filtra.
- **Clasificación de los 345 490 de la región:** 71 079 sobreviven con las tres demandas (ROBUST) y 274 411 sólo con
  algunas (DEMAND-SENSITIVE).
- **Con demanda ±10 % la región cambia mucho:** 53 821 candidatos sobreviven sólo con 1,0. La demanda no se aprueba
  ni se usa para calibrar.

## 6. Región y FD-LAC-04/05

<!-- generado:region -->
**FACULTY-CONSTRAINED CURRENT-PHYSIOLOGY LACTATE REGION (no value selected or approved)**: 7 091 unidades (P1 × lado del lactato), 345 490 candidatos; resumen de la región `99456c31a934b4553960ce56412ffc4980ddc75797655c6aa07b1fe4201f5994`. Frente a P2I-2AB (439 291): se mantienen 42 225, salen 397 066, entran 303 265.

| Lectura (mín · p5 · mediana · p95 · máx) | 57m | 72f |
|---|---|---|
| L60 sin tratamiento (mmol/L) | 4,40 · 4,47 · 5,00 · 5,83 · 6,29 | 3,66 · 3,74 · 4,27 · 5,42 · 5,50 |
| L120 con L3 (mmol/L) | 1,62 · 2,49 · 3,55 · 3,97 · 4,00 | 1,56 · 2,47 · 3,19 · 3,43 · 3,90 |
| D a los 120′ con L3 | 0,23 · 0,54 · 3,40 · 8,83 · 37,58 | 0,42 · 0,60 · 3,63 · 9,25 · 50,92 |
| L(T*) (mmol/L) | 2,91 · 3,75 · 4,24 · 4,65 · 5,08 | 2,65 · 3,24 · 3,64 · 4,02 · 5,03 |
| caída a T* + 30 (fracción) | 0,03 · 0,04 · 0,08 · 0,20 · 0,30 | 0,00 · 0,02 · 0,06 · 0,17 · 0,28 |

| Estado entre los sobrevivientes | 57m | 72f |
|---|---|---|
| FD-LAC-01 PASS | 345 490 (100,0 %) | 345 490 (100,0 %) |
| FD-LAC-04 PASS | 345 490 (100,0 %) | 345 490 (100,0 %) |
| FD-LAC-05 PASS | 345 490 (100,0 %) | 343 978 (99,6 %) |
| FD-LAC-05 NOT_EVALUABLE | 0 (0,0 %) | 1 512 (0,4 %) |
| FD-LAC-05 NOT_EVALUABLE 72f: delivery not adequate throughout from T* to 120 min | 1 512 | |
| FD-LAC-04 y 05 evaluadas en ambos casos | 343 978 (99,6 %) | |
| 72f con FD-LAC-05 NOT_EVALUABLE y L120 sobre la envolvente | 1 008 | |

| Sensibilidad de FD-LAC-04 (diagnóstico, no filtra) | Sobrevivientes que también pasarían |
|---|---|
| cualquier caída | 345 490 (100,0 %) |
| caída ≥ 5 % | 218 338 (63,2 %) |
| caída ≥ 10 % | 60 745 (17,6 %) |
| caída ≥ 15 % | 25 993 (7,5 %) |

| Lectura informativa (no filtra) | Sobrevivientes |
|---|---|
| con una caída sostenida aceptada como RECOVERING_CRITICAL | L1 0; L2 324; L3 0; L3 con sangrado residual 0 |
| con algún minuto COMPENSATED (déficit 0, entrega < demanda) en [T*, T* + 30] | 345 490 |
| inicio de la adecuación sostenida | 57m: minuto 60 345 490; 72f: minuto 60 345 490 |
| T* de FD-LAC-04 | 57m: minuto 60 345 490; 72f: minuto 60 345 490 |
<!-- /generado:region -->

### 6.1 Lectura

- **Adecuación:** todos los sobrevivientes recuperan la adecuación sostenida desde el minuto 60 en los dos casos.
- **FD-LAC-04** se evalúa y pasa en todos (T* = 60).
- **FD-LAC-05 queda NOT_EVALUABLE en 1512 sobrevivientes de 72f (0,44 %):**
  - motivo: la entrega deja de ser adecuada antes de los 120 min, con sangrado residual;
  - 1008 de ellos tienen L120 por encima de la envolvente de 72f (3,5 mmol/L);
  - es el único bloqueo del veredicto (§10).
- **Toda la adecuación tras T* incluye minutos COMPENSATED:** la extracción con ρ 2,5 sostiene la demanda con una
  entrega de 0,5 a 0,8.
- **Caída a los 30 min de T*:** mediana del 8,1 % (57m) y del 6,4 % (72f). Los umbrales de 5, 10 y 15 % son sólo
  diagnóstico.
- **Frente a P2I-2AB** se mantienen 42 225 candidatos, salen 397 066 y entran 303 265. La corrección de D reordena la
  región: no sólo la recorta.

## 7. Identificabilidad (P2I-2AC-4)

<!-- generado:identificabilidad -->
| Dimensión | Explorado | Sobrevive (candidatos) | Clase | Borde | P2I-2AB | Cambio |
|---|---|---|---|---|---|---|
| G × g | 1, 2, 3, 4, 6, 12, 24 | 1 18 686, 2 19 067, 3 50 699, 4 17 913, 6 102 636, 12 106 725, 24 29 764 | mal identificado | abierto en ambos bordes | parcialmente acotado (5) | WIDER |
| B0 (mL) | 3000, 4000, 5000 | 3000 90 240, 4000 144 607, 5000 110 643 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| entrega de llegada | inferior, medio, superior | inferior 31 188, medio 218 604, superior 95 698 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| exceso de lactato de llegada | inferior, medio, superior | inferior 110 909, medio 101 368, superior 133 213 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| deuda de llegada | inferior, medio, superior | inferior 16 812, medio 218 604, superior 110 074 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| par (deuda, entrega) de llegada | deuda inferior · entrega inferior, deuda inferior · entrega superior, deuda medio · entrega medio, deuda superior · entrega inferior, deuda superior · entrega superior | deuda inferior · entrega inferior 16 812, deuda inferior · entrega superior 0, deuda medio · entrega medio 218 604, deuda superior · entrega inferior 14 376, deuda superior · entrega superior 95 698 | parcialmente acotado | — | parcialmente acotado (4) | SAME |
| tasa de sangrado (mL-eq/min) | 2,5, 5, 6 | 2,5 173 142, 5 101 360, 6 70 988 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| F0 | 0,2 | 0,2 345 490 | no varía | — | no varía (1) | SAME |
| Finf | 0,05, 0,1 | 0,05 200 996, 0,1 144 494 | mal identificado | abierto en ambos bordes | mal identificado (2) | SAME |
| punto del cristaloide | 12 puntos | 12 sobreviven (27 721 a 29 606 cada uno) | mal identificado | — | mal identificado (12) | SAME |
| τ del cristaloide (min) | 30, 60, 90, 120, 150, 180, 210, 240 | 30 28 135, 60 56 760, 90 56 748, 120 57 626, 150 58 414, 180 29 006, 210 29 275, 240 29 526 | mal identificado | abierto en ambos bordes | mal identificado (8) | SAME |
| τ_D (min) | 30, 60, 120 | 30 166 735, 60 153 359, 120 25 396 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| ganancia déficit→D (g) | 0,5, 1, 2 | 0,5 105 479, 1 127 812, 2 112 199 | no identificable por separado | abierto en ambos bordes | no identificable por separado (3) | SAME |
| demanda (×) | 0,9, 1, 1,1 | 0,9 404 371, 1 345 490, 1,1 367 703 | mal identificado | abierto en ambos bordes | — | — |
| τ del lactato (min) | 45, 120, 240 | 45 57 864, 120 141 796, 240 145 830 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| ganancia D→lactato (G) | 2, 6, 12 | 2 55 666, 6 181 763, 12 108 061 | no identificable por separado | abierto en ambos bordes | no identificable por separado (3) | SAME |
| capacidad del relleno (mL) | 100, 500, 1000 | 100 79 850, 500 132 820, 1000 132 820 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| meta del relleno | 0,5, 0,75, 1 | 0,5 103 570, 0,75 117 366, 1 124 554 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| τ del relleno (min) | 120, 240, 480 | 120 147 592, 240 95 274, 480 102 624 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| posición 57m | 0,35, 0,5 | 0,35 28 870, 0,5 316 620 | mal identificado | abierto en ambos bordes | mal identificado (2) | SAME |
| posición 72f | 0,45, 0,6 | 0,45 28 870, 0,6 316 620 | mal identificado | abierto en ambos bordes | mal identificado (2) | SAME |
| λ/κ (mL) | 600, 833, 1500 | 600 75 564, 833 68 708, 1500 201 218 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| Hb de la unidad (g/dL) | 18, 20, 22 | 18 98 261, 20 118 896, 22 128 333 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |
| volumen de la unidad (mL) | 250, 300, 350 | 250 122 322, 300 137 002, 350 86 166 | mal identificado | abierto en ambos bordes | mal identificado (3) | SAME |

ρ: NON_IDENTIFIABLE (invariant): rho cancels in deficit, D, lactate and adequacy because the arrival ratio is re-anchored as ratio / rho; evaluated at 2.5 (representative of the 2.0-3.0 band), checked at 2.0 and 3.0, 1 only as SYNTHETIC_REFERENCE; never counted in the candidate multiplicity.
<!-- /generado:identificabilidad -->

### 7.1 Lectura

- **La D corregida no mejora la identificabilidad:**
  - ninguna dimensión queda bien acotada;
  - G × g pasa de parcialmente acotado (5 valores) a mal identificado (7);
  - todo lo demás conserva su clase.
- **Siguen mal identificados:** τ_D, τ_L, el exceso y la deuda de llegada.
- **Par de llegada:** sigue parcialmente acotado; no sobrevive deuda inferior con entrega superior.
- **No identificables por separado:**
  - g y G (sólo llegan como G × g y G × D0);
  - la demanda: sobreviven los tres factores;
  - ρ, que es invariante (se cancela con la razón de llegada reanclada) y no se cuenta como candidato. Se comprobó con
    corridas completas con ρ 2,0 y 3,0, y con 1 como referencia sintética.

## 8. Representativos (P2I-2AC-5)

Regla de P2I-2AB: entre los sobrevivientes ordenados por el lactato de 57m en L1 a los 60 min, el primero, el del
medio y el último. Cada uno se vuelve a correr con el núcleo completo (57m y 72f, L1 y L3).

<!-- generado:representativos -->
**LOW** (rango 0): τ_D 120, g 0,5, G 12, τ_L 45, exceso inferior, deuda medio, entrega medio; tasa 2,5, B0 4000, λ/κ 600, relleno 1 / 120 / 100, unidad 18 g/dL × 300 mL, posiciones 0,5 / 0,6; cristaloide F0 0,2 · Finf 0,05 · τ 60.

| Caso · escenario | min | Gasto relativo | DO2 (índice) | Demanda | Déficit | D | Lactato (mmol/L) | Sangrado activo (mL/min) | Estado de O2 |
|---|---|---|---|---|---|---|---|---|---|
| 57m L1 | 0 | 1,000 | 0,340 | 1,00 | 0,150 | 20,0 | 4,40 | 2,50 | CRITICAL |
| 57m L1 | 15 | 0,939 | 0,319 | 1,00 | 0,202 | 21,3 | 4,30 | 2,50 | CRITICAL |
| 57m L1 | 30 | 0,883 | 0,299 | 1,00 | 0,251 | 23,0 | 4,28 | 2,50 | CRITICAL |
| 57m L1 | 60 | 0,774 | 0,261 | 1,00 | 0,347 | 27,5 | 4,40 | 2,50 | CRITICAL |
| 57m L1 | 90 | 0,647 | 0,218 | 1,00 | 0,456 | 33,4 | 4,72 | 2,50 | CRITICAL |
| 57m L1 | 120 | 0,499 | 0,167 | 1,00 | 0,582 | 41,2 | 5,22 | 2,50 | CRITICAL |
| 57m L3 | 0 | 1,000 | 0,340 | 1,00 | 0,150 | 20,0 | 4,40 | 2,00 | CRITICAL |
| 57m L3 | 15 | 1,181 | 0,426 | 1,00 | 0,000 | 19,7 | 4,29 | 2,00 | COMPENSATED |
| 57m L3 | 30 | 1,330 | 0,506 | 1,00 | 0,000 | 17,4 | 4,17 | 2,00 | COMPENSATED |
| 57m L3 | 60 | 1,552 | 0,645 | 1,00 | 0,000 | 13,6 | 3,85 | 0,25 | COMPENSATED |
| 57m L3 | 90 | 1,546 | 0,643 | 1,00 | 0,000 | 10,5 | 3,53 | 0,25 | COMPENSATED |
| 57m L3 | 120 | 1,541 | 0,641 | 1,00 | 0,000 | 8,2 | 3,23 | 0,25 | COMPENSATED |
| 72f L1 | 0 | 1,000 | 0,340 | 1,00 | 0,150 | 20,0 | 3,40 | 2,50 | CRITICAL |
| 72f L1 | 15 | 0,959 | 0,326 | 1,00 | 0,185 | 21,2 | 3,59 | 2,50 | CRITICAL |
| 72f L1 | 30 | 0,922 | 0,313 | 1,00 | 0,218 | 22,8 | 3,76 | 2,50 | CRITICAL |
| 72f L1 | 60 | 0,849 | 0,287 | 1,00 | 0,283 | 26,5 | 4,11 | 2,50 | CRITICAL |
| 72f L1 | 90 | 0,765 | 0,257 | 1,00 | 0,357 | 31,3 | 4,50 | 2,50 | CRITICAL |
| 72f L1 | 120 | 0,666 | 0,223 | 1,00 | 0,442 | 37,2 | 4,96 | 2,50 | CRITICAL |
| 72f L3 | 0 | 1,000 | 0,340 | 1,00 | 0,150 | 20,0 | 3,40 | 2,00 | CRITICAL |
| 72f L3 | 15 | 1,121 | 0,406 | 1,00 | 0,000 | 20,4 | 3,58 | 2,00 | COMPENSATED |
| 72f L3 | 30 | 1,220 | 0,468 | 1,00 | 0,000 | 18,0 | 3,68 | 2,00 | COMPENSATED |
| 72f L3 | 60 | 1,368 | 0,576 | 1,00 | 0,000 | 14,0 | 3,63 | 0,25 | COMPENSATED |
| 72f L3 | 90 | 1,364 | 0,575 | 1,00 | 0,000 | 10,9 | 3,43 | 0,25 | COMPENSATED |
| 72f L3 | 120 | 1,360 | 0,573 | 1,00 | 0,000 | 8,5 | 3,20 | 0,25 | COMPENSATED |

| Caso · escenario | Intervalos de 15′ (A / R / P; * sin sangrado) | D cae con déficit leído por el núcleo | D cae con déficit final que empeora | Igual a la factorización | Marcas |
|---|---|---|---|---|---|
| 57m L1 | P P P P P P P P | 0 | 0 | sí | ninguna |
| 57m L3 | A A A A A A A A | 0 | 0 | sí | ninguna |
| 72f L1 | P P P P P P P P | 0 | 0 | sí | ninguna |
| 72f L3 | A A A A A A A A | 0 | 0 | sí | adecuado con aclaramiento demorado |

**MID** (rango 172 745): τ_D 60, g 2, G 6, τ_L 240, exceso superior, deuda superior, entrega superior; tasa 5, B0 5000, λ/κ 1500, relleno 0,75 / 240 / 500, unidad 22 g/dL × 350 mL, posiciones 0,5 / 0,6; cristaloide F0 0,2 · Finf 0,1 · τ 120.

| Caso · escenario | min | Gasto relativo | DO2 (índice) | Demanda | Déficit | D | Lactato (mmol/L) | Sangrado activo (mL/min) | Estado de O2 |
|---|---|---|---|---|---|---|---|---|---|
| 57m L1 | 0 | 1,000 | 0,400 | 1,00 | 0,000 | 60,0 | 4,40 | 5,00 | COMPENSATED |
| 57m L1 | 15 | 0,950 | 0,380 | 1,00 | 0,050 | 59,7 | 4,54 | 5,00 | CRITICAL |
| 57m L1 | 30 | 0,900 | 0,359 | 1,00 | 0,102 | 61,9 | 4,68 | 5,00 | CRITICAL |
| 57m L1 | 60 | 0,799 | 0,318 | 1,00 | 0,205 | 71,0 | 5,00 | 5,00 | CRITICAL |
| 57m L1 | 90 | 0,699 | 0,276 | 1,00 | 0,309 | 86,3 | 5,43 | 5,00 | CRITICAL |
| 57m L1 | 120 | 0,600 | 0,235 | 1,00 | 0,412 | 107,9 | 6,02 | 5,00 | CRITICAL |
| 57m L3 | 0 | 1,000 | 0,400 | 1,00 | 0,000 | 60,0 | 4,40 | 4,00 | COMPENSATED |
| 57m L3 | 15 | 1,074 | 0,463 | 1,00 | 0,000 | 46,6 | 4,51 | 4,00 | COMPENSATED |
| 57m L3 | 30 | 1,142 | 0,526 | 1,00 | 0,000 | 36,2 | 4,53 | 4,00 | COMPENSATED |
| 57m L3 | 60 | 1,266 | 0,651 | 1,00 | 0,000 | 21,9 | 4,43 | 0,50 | COMPENSATED |
| 57m L3 | 90 | 1,258 | 0,648 | 1,00 | 0,000 | 13,2 | 4,21 | 0,50 | COMPENSATED |
| 57m L3 | 120 | 1,251 | 0,644 | 1,00 | 0,000 | 8,0 | 3,93 | 0,50 | COMPENSATED |
| 72f L1 | 0 | 1,000 | 0,400 | 1,00 | 0,000 | 60,0 | 3,40 | 5,00 | COMPENSATED |
| 72f L1 | 15 | 0,967 | 0,387 | 1,00 | 0,034 | 59,5 | 3,60 | 5,00 | CRITICAL |
| 72f L1 | 30 | 0,933 | 0,373 | 1,00 | 0,068 | 61,0 | 3,80 | 5,00 | CRITICAL |
| 72f L1 | 60 | 0,866 | 0,345 | 1,00 | 0,138 | 67,1 | 4,19 | 5,00 | CRITICAL |
| 72f L1 | 90 | 0,799 | 0,316 | 1,00 | 0,210 | 77,5 | 4,64 | 5,00 | CRITICAL |
| 72f L1 | 120 | 0,733 | 0,287 | 1,00 | 0,282 | 92,1 | 5,18 | 5,00 | CRITICAL |
| 72f L3 | 0 | 1,000 | 0,400 | 1,00 | 0,000 | 60,0 | 3,40 | 4,00 | COMPENSATED |
| 72f L3 | 15 | 1,049 | 0,454 | 1,00 | 0,000 | 46,6 | 3,57 | 4,00 | COMPENSATED |
| 72f L3 | 30 | 1,095 | 0,509 | 1,00 | 0,000 | 36,2 | 3,65 | 4,00 | COMPENSATED |
| 72f L3 | 60 | 1,177 | 0,615 | 1,00 | 0,000 | 21,9 | 3,65 | 0,50 | COMPENSATED |
| 72f L3 | 90 | 1,172 | 0,612 | 1,00 | 0,000 | 13,2 | 3,52 | 0,50 | COMPENSATED |
| 72f L3 | 120 | 1,167 | 0,610 | 1,00 | 0,000 | 8,0 | 3,32 | 0,50 | COMPENSATED |

| Caso · escenario | Intervalos de 15′ (A / R / P; * sin sangrado) | D cae con déficit leído por el núcleo | D cae con déficit final que empeora | Igual a la factorización | Marcas |
|---|---|---|---|---|---|
| 57m L1 | P P P P P P P P | 0 | 1 (minuto 1, inicio) | sí | ninguna |
| 57m L3 | A A A A A A A A | 0 | 0 | sí | adecuado con aclaramiento demorado |
| 72f L1 | P P P P P P P P | 0 | 1 (minuto 1, inicio) | sí | ninguna |
| 72f L3 | A A A A A A A A | 0 | 0 | sí | adecuado con aclaramiento demorado |

**HIGH** (rango 345 489): τ_D 30, g 1, G 6, τ_L 240, exceso superior, deuda superior, entrega superior; tasa 2,5, B0 3000, λ/κ 600, relleno 0,75 / 240 / 1000, unidad 22 g/dL × 250 mL, posiciones 0,5 / 0,6; cristaloide F0 0,2 · Finf 0,1 · τ 150.

| Caso · escenario | min | Gasto relativo | DO2 (índice) | Demanda | Déficit | D | Lactato (mmol/L) | Sangrado activo (mL/min) | Estado de O2 |
|---|---|---|---|---|---|---|---|---|---|
| 57m L1 | 0 | 1,000 | 0,400 | 1,00 | 0,000 | 60,0 | 4,40 | 2,50 | COMPENSATED |
| 57m L1 | 15 | 0,937 | 0,375 | 1,00 | 0,063 | 58,4 | 4,89 | 2,50 | CRITICAL |
| 57m L1 | 30 | 0,873 | 0,349 | 1,00 | 0,128 | 59,8 | 5,36 | 2,50 | CRITICAL |
| 57m L1 | 60 | 0,743 | 0,296 | 1,00 | 0,260 | 65,6 | 6,29 | 2,50 | CRITICAL |
| 57m L1 | 90 | 0,611 | 0,242 | 1,00 | 0,395 | 75,4 | 7,29 | 2,50 | CRITICAL |
| 57m L1 | 120 | 0,477 | 0,188 | 1,00 | 0,531 | 89,2 | 8,46 | 2,50 | CRITICAL |
| 57m L3 | 0 | 1,000 | 0,400 | 1,00 | 0,000 | 60,0 | 4,40 | 2,00 | COMPENSATED |
| 57m L3 | 15 | 1,146 | 0,501 | 1,00 | 0,000 | 36,1 | 4,76 | 2,00 | COMPENSATED |
| 57m L3 | 30 | 1,271 | 0,599 | 1,00 | 0,000 | 21,7 | 4,87 | 2,00 | COMPENSATED |
| 57m L3 | 60 | 1,471 | 0,783 | 1,00 | 0,000 | 7,8 | 4,71 | 0,25 | COMPENSATED |
| 57m L3 | 90 | 1,464 | 0,780 | 1,00 | 0,000 | 2,8 | 4,37 | 0,25 | COMPENSATED |
| 57m L3 | 120 | 1,457 | 0,776 | 1,00 | 0,000 | 1,0 | 3,99 | 0,25 | COMPENSATED |
| 72f L1 | 0 | 1,000 | 0,400 | 1,00 | 0,000 | 60,0 | 3,40 | 2,50 | COMPENSATED |
| 72f L1 | 15 | 0,958 | 0,383 | 1,00 | 0,042 | 58,3 | 3,95 | 2,50 | CRITICAL |
| 72f L1 | 30 | 0,915 | 0,366 | 1,00 | 0,086 | 59,2 | 4,47 | 2,50 | CRITICAL |
| 72f L1 | 60 | 0,829 | 0,330 | 1,00 | 0,175 | 63,1 | 5,47 | 2,50 | CRITICAL |
| 72f L1 | 90 | 0,740 | 0,293 | 1,00 | 0,267 | 69,7 | 6,48 | 2,50 | CRITICAL |
| 72f L1 | 120 | 0,651 | 0,256 | 1,00 | 0,360 | 79,0 | 7,55 | 2,50 | CRITICAL |
| 72f L3 | 0 | 1,000 | 0,400 | 1,00 | 0,000 | 60,0 | 3,40 | 2,00 | COMPENSATED |
| 72f L3 | 15 | 1,098 | 0,482 | 1,00 | 0,000 | 36,1 | 3,82 | 2,00 | COMPENSATED |
| 72f L3 | 30 | 1,181 | 0,562 | 1,00 | 0,000 | 21,7 | 3,99 | 2,00 | COMPENSATED |
| 72f L3 | 60 | 1,314 | 0,712 | 1,00 | 0,000 | 7,8 | 3,93 | 0,25 | COMPENSATED |
| 72f L3 | 90 | 1,309 | 0,709 | 1,00 | 0,000 | 2,8 | 3,68 | 0,25 | COMPENSATED |
| 72f L3 | 120 | 1,305 | 0,707 | 1,00 | 0,000 | 1,0 | 3,38 | 0,25 | COMPENSATED |

| Caso · escenario | Intervalos de 15′ (A / R / P; * sin sangrado) | D cae con déficit leído por el núcleo | D cae con déficit final que empeora | Igual a la factorización | Marcas |
|---|---|---|---|---|---|
| 57m L1 | P P P P P P P P | 0 | 1 (minuto 1, inicio) | sí | ninguna |
| 57m L3 | A A A A A A A A | 0 | 0 | sí | adecuado con aclaramiento demorado |
| 72f L1 | P P P P P P P P | 0 | 1 (minuto 1, inicio) | sí | ninguna |
| 72f L3 | A A A A A A A A | 0 | 0 | sí | adecuado con aclaramiento demorado |
<!-- /generado:representativos -->

### 8.1 Lectura

- **D:** en ningún representativo D baja en un minuto en el que el núcleo leyó déficit. Las únicas excepciones con
  la lectura del estado final son el minuto 1 de L1 en HIGH y MID: llegan COMPENSATED en la entrega crítica y el
  minuto 1 empezó sin déficit.
- **Cada corrida completa coincide exactamente con la factorización.**
- **No aparece ninguna marca de inverosimilitud:** ni déficit crítico que empeora con caída grande del lactato, ni
  normalización instantánea, ni valores incompatibles con la supervivencia.
- **Sangrado activo en L3:** 2,0 a 4,0 mL-eq/min antes de la hemostasia y 0,25 a 0,5 después.
- **«Adecuado con aclaramiento demorado»** aparece en L3 de HIGH, MID y LOW 72f. El lactato sube o se mantiene los
  primeros 30 min con déficit 0, porque la deuda de llegada sigue produciendo lactato mientras se devuelve. Es una
  marca informativa, no de inverosimilitud.

## 9. Legado sólo como referencia

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
| HIGH 57m L1 | 0′ 4,40 / 4,4; 60′ 6,29 / 4,8; 120′ 8,46 / 5,1 |
| HIGH 57m L3 | 0′ 4,40 / 4,4; 60′ 4,71 / 3,2; 120′ 3,99 / 3,3 |
| HIGH 72f L1 | 0′ 3,40 / 3,4; 60′ 5,47 / 3,8; 120′ 7,55 / 4,1 |
| HIGH 72f L3 | 0′ 3,40 / 3,4; 60′ 3,93 / 2,2; 120′ 3,38 / 2,3 |
| LOW 57m L1 | 0′ 4,40 / 4,4; 60′ 4,40 / 4,8; 120′ 5,22 / 5,1 |
| LOW 57m L3 | 0′ 4,40 / 4,4; 60′ 3,85 / 3,2; 120′ 3,23 / 3,3 |
| LOW 72f L1 | 0′ 3,40 / 3,4; 60′ 4,11 / 3,8; 120′ 4,96 / 4,1 |
| LOW 72f L3 | 0′ 3,40 / 3,4; 60′ 3,63 / 2,2; 120′ 3,20 / 2,3 |
| MID 57m L1 | 0′ 4,40 / 4,4; 60′ 5,00 / 4,8; 120′ 6,02 / 5,1 |
| MID 57m L3 | 0′ 4,40 / 4,4; 60′ 4,43 / 3,2; 120′ 3,93 / 3,3 |
| MID 72f L1 | 0′ 3,40 / 3,4; 60′ 4,19 / 3,8; 120′ 5,18 / 4,1 |
| MID 72f L3 | 0′ 3,40 / 3,4; 60′ 3,65 / 2,2; 120′ 3,32 / 2,3 |
<!-- /generado:legado -->

## 10. Veredicto (P2I-2AC-6)

<!-- generado:veredicto -->
**LACTATE_PHYSIOLOGY_NOT_READY — FD-LAC-04 / 05 are met only as NOT_EVALUABLE by some survivors**

| Comprobación | Resultado |
|---|---|
| registro P2I-2AB comprometido | sí |
| factorización exacta (D no cae con déficit) | sí |
| D coherente en los representativos | sí |
| hay sobrevivientes con demanda 1,0 | sí |
| todo sobreviviente restaura la adecuación L3 | sí |
| FD-LAC-04/05 evaluadas en ambos casos para todo sobreviviente | no |
| sangrado residual leído por flujo real | sí |
| capa de demanda clasificó todos los candidatos | sí |
| sin marcas de inverosimilitud en los representativos | sí |

Regla congelada: LACTATE_PHYSIOLOGY_READY_FOR_NEXT_DOMAIN when every check holds: the P2I-2AB record is the committed one; the factorization agrees with the full core (D never falls under a deficit the core read); D is coherent in every representative run (never falls under a core-read deficit; any end-state exception is an onset minute); at least one candidate survives at demand 1.0; every survivor restores L3 adequacy in both cases; FD-LAC-04 is PASS or ALREADY_NORMALIZED and FD-LAC-05 PASS in both cases for every survivor (no definitive-management constraint met only as NOT_EVALUABLE); residual bleeding is read by actual flow (the L3 runs carry the flow after haemostasis and the validation reproduces it exactly); the demand layer classified every candidate; and no representative carries a patient-like flag (WORSENING_CRITICAL_WITH_LARGE_LACTATE_FALL, INSTANT_NORMALIZATION, INCOMPATIBLE_WITH_SURVIVAL). Otherwise LACTATE_PHYSIOLOGY_NOT_READY with the first blocker. No candidate, value or parameter is selected or approved.

Próximo dominio: ninguno (el veredicto no es READY)
<!-- /generado:veredicto -->

### 10.1 Lectura

- **Se cumplen todas las demás condiciones:**
  - D coherente;
  - factorización exacta;
  - hay sobrevivientes, y todos recuperan la adecuación L3;
  - FD-LAC-04 evaluada en todos;
  - sangrado residual por flujo real;
  - demanda caracterizada;
  - representativos sin marcas.
- **Única excepción:** 1512 sobrevivientes de 72f cumplen FD-LAC-05 sólo como NOT_EVALUABLE. La regla congelada exige
  FD-LAC-04/05 evaluadas para todo sobreviviente, así que el veredicto es NOT_READY.
- **Se resolvería con una decisión docente** sobre esos candidatos (§13). El paquete no la toma ni excluye esos
  candidatos por su cuenta.
- **No se recomienda ni se empieza otro dominio.** El orden que la docencia prefiere queda registrado para cuando
  corresponda: FC y respuesta simpática, después presión y tono vascular.

## 11. Congelamiento y entrega

- **Congelamiento:** `2a9129e`, en un solo commit y antes de evaluar cualquier candidato. Incluye:
  - la corrección del núcleo, las 7 invariantes y el análisis;
  - el flujo real, la adecuación L3 y la capa de demanda;
  - la regla del veredicto y las pruebas previas a la corrida.
- **Validación antes de congelar:** la factorización se validó sobre su muestra congelada (936 corridas completas,
  sin desacuerdos).
- **Corrida:** sobre `2a9129e`, 83 s con 4 procesos, cada uno con la guarda P2F y el bloqueo del legado. El registro
  es el del módulo; sólo el mapeo fue paralelo, y `--run` lo reproduce en un solo proceso.
- **Entrega:** un commit ejecutable (informe, pruebas sobre el registro, JSON y documentación), sobre el que corre la
  certificación completa.

## 12. Qué no hace

- **Parámetros y región:** no elige ni aprueba ningún parámetro, ninguna demanda ni ningún ρ. Tampoco excluye por su
  cuenta los 1512 NOT_EVALUABLE.
- **Restricciones:** no cambia FD-LAC-04/05, sus envolventes ni la fracción residual de L3 (FD-25).
- **Legado:** no lee el lactato heredado salvo como referencia, después del filtro.
- **Otros límites:** no calibra la presión ni la FC, no activa el colapso, no migra ni integra nada.

## 13. Decisiones pendientes (docencia)

- **FD-LAC-05 NOT_EVALUABLE en 1512 sobrevivientes de 72f.** La adecuación, recuperada a los 60 min, se pierde
  antes de los 120 por el sangrado residual. Opciones:
  - exigir que la adecuación L3 se sostenga hasta los 120 min;
  - evaluar FD-LAC-05 igual (1008 caerían fuera de la envolvente);
  - aceptar NOT_EVALUABLE en ese caso.
- **Convención temporal de D:** en el primer minuto de un tramo crítico D puede devolver un paso, porque el minuto
  empezó sin déficit. ¿Basta así, o la docencia quiere otra convención? Cambiarla tocaría la definición del déficit
  que lee D.
- **Memoria de deuda de FD-LAC-05** (`debt_memory_coefficient`, sólo informativa): supone devolución desde la
  llegada. Con la D corregida es una cota inferior cuando hay déficit (TD-91).
- **Demanda:** la región depende fuertemente de ±10 %; sólo 71 079 candidatos son robustos.
- **Identificabilidad:** las seis FD-LAC no acotan ninguna cinética del lactato. Harían falta otras anclas.
- **Siguen abiertas:**
  - FD-24 y FD-25;
  - la autorización del próximo dominio.
