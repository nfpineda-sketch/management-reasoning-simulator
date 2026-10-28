# P2I-2AB · Reconstrucción del lactato GI con la fisiología actual

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución ni migra GI u otra familia;
- no calibra la presión ni la FC, ni activa el colapso;
- no elige parámetros ocultos ni se ajusta al motor heredado;
- no reutiliza la región histórica de P2F: corre dentro de una guarda que hace fallar cualquier acceso a ella;
- no cambia ninguna restricción docente: las FD-BLD y las FD-LAC son las congeladas, y FD-LAC-01 y 06 se leen con la
  semántica de recuperación que la docencia fijó el 2026-10-28.

Código: `clinical_core/lactate_rebuild.py` (espacio de origen, posproceso, FD-LAC vigentes, filtro, identificabilidad,
representativos y veredicto; congelado en `e234a54` y recongelado en `68b92de` antes de evaluar cualquier lactato,
§12) y `clinical_core/lactate_rebuild_report.py` (sólo este informe). Números:
`docs/revision/P2I2AB_lactate_rebuild.json`. Registro de partida, cerrado: P2I-2AA (`5087cf02…`).

## 1. Preparación y decisiones docentes

<!-- generado:preparacion -->
Congelamiento: `15d05c321b38d2e2512642bf2e3be64bc4382ad639ad05ea445c9050091d7cc4` (una prueba lo fija). Registro de partida: P2I-2AA `5087cf022f928fed5d3893a00a4907578e7f91b3543ee10c6ba3786abde01001`.

| Elemento | Valor |
|---|---|
| Veredicto previo (P2I-2AA) | NOT_READY |
| Bloqueo previo | crystalloid candidate support characterized |
| Borde de τ / identificabilidad práctica | TAU_REMAINS_OPEN_AT_240 / CONSTRAINT_BOUNDED_BEYOND_TESTED_DOMAIN |
| Estado de τ | STRUCTURALLY_IDENTIFIABLE BUT PRACTICALLY_WEAKLY_IDENTIFIED_WITHIN_120_MIN_HORIZON |
| **Preparación** | **READY_FOR_CURRENT_PHYSIOLOGY_LACTATE_REBUILD_WITH_PROPAGATED_FLUID_UNCERTAINTY** |

| Decisión docente | Texto registrado |
|---|---|
| adequacy | Adequate oxygen availability for lactate production is effective_oxygen_deficit == 0 (ADEQUATE and COMPENSATED); CRITICAL is effective_oxygen_deficit > 0. Normal resting DO2 is not required. |
| l3 | fraction_with_ppi 0.8 and fraction_after_hemostasis 0.1: FIXED_PROVISIONAL_FOR_PRIMARY_LACTATE_ANALYSIS and FACULTY_DECISION_PENDING. No range exists, so there is no sensitivity on them. |
| preload | Primary support 57m 0.5 and 72f 0.6; a lower position enters only where it survives the current blood constraints; the positions that enter are reported exactly. |
| rates | Bleed rates 2.5, 5 and 6 mL-eq/min; none is approved; 7 and above are excluded. |
| readiness | The open crystalloid tau edge does not block the lactate rebuild: readiness becomes READY_FOR_CURRENT_PHYSIOLOGY_LACTATE_REBUILD_WITH_PROPAGATED_FLUID_UNCERTAINTY. This approves no tau value. |
| recovery | FD-LAC-06 with active bleeding: PERSISTENT_OR_WORSENING_CRITICAL when the deficit > 0 is stable or worsening over the reassessment interval; RECOVERING_CRITICAL when the deficit > 0 decreases over it, and lactate may fall. The net trajectory at the reassessment points decides, not minute-to-minute monotonicity. No active treatment order is required; no percentage tolerance is added to the deficit. |
| tau | tau is STRUCTURALLY_IDENTIFIABLE BUT PRACTICALLY_WEAKLY_IDENTIFIED_WITHIN_120_MIN_HORIZON. Every certified crystalloid point propagates as fluid uncertainty; no preferred tau is chosen and nothing above 240 min is added. |
<!-- /generado:preparacion -->

### 1.1 Lectura

- **Qué levanta la decisión:**
  - P2I-2AA quedó NOT_READY por un solo bloqueo: el borde de τ del cristaloide, abierto en 240;
  - la decisión docente levanta exactamente ese bloqueo y ningún otro, y no aprueba ningún valor de τ;
  - si P2I-2AA hubiera tenido otro bloqueo, la preparación seguiría NOT_READY (una prueba lo comprueba).
- **Cómo se propaga la incertidumbre del fluido:** los 12 puntos certificados del cristaloide entran tal cual, sin un
  τ preferido y sin nada por encima de 240. Cada candidato lleva uno de esos puntos.
- **La adecuación** es déficit efectivo = 0 (ADEQUATE y COMPENSATED), sin exigir la DO2 normal. En la práctica de
  este paquete eso es decisivo (§7.1).

## 2. Espacio de origen (P2I-2AB-1)

<!-- generado:origen -->
| Componente | Contenido |
|---|---|
| A. Sangre | 87 conjuntos P1 y 458 conjuntos P3 (reserva colapsada); por tasa: 2,5: 42 P1 / 203 P3; 5: 27 P1 / 153 P3; 6: 18 P1 / 102 P3 |
| B. Posiciones que entran | tasa 2,5: 57m 0,35 y 0,5, 72f 0,45 y 0,6; tasa 5: 57m 0,5, 72f 0,6; tasa 6: 57m 0,5, 72f 0,6 |
| C. Tasas | 2,5, 5, 6 mL-eq/min |
| D. Cristaloide | 12 puntos: F0 0,2 · Finf 0,05 · τ 60; F0 0,2 · Finf 0,05 · τ 90; F0 0,2 · Finf 0,05 · τ 120; F0 0,2 · Finf 0,05 · τ 150; F0 0,2 · Finf 0,05 · τ 180; F0 0,2 · Finf 0,05 · τ 210; F0 0,2 · Finf 0,05 · τ 240; F0 0,2 · Finf 0,1 · τ 30; F0 0,2 · Finf 0,1 · τ 60; F0 0,2 · Finf 0,1 · τ 90; F0 0,2 · Finf 0,1 · τ 120; F0 0,2 · Finf 0,1 · τ 150 |
| E. Glóbulos rojos | Hb de la unidad (g/dL) 18, 20, 22; volumen de la unidad (mL) 250, 300, 350 |
| F. DO2 / extracción | ρ 1, 2,5, 3 (simulado en 2,5; ρ se cancela) |
| G. Hemostasia | 57m minuto 60; 72f minuto 60 (endoscopía del propio motor) |
| H. L3 | gi_fraction_after_hemostasis 0,1 (FIXED_PROVISIONAL_FOR_PRIMARY_LACTATE_ANALYSIS + FACULTY_DECISION_PENDING); gi_fraction_with_ppi 0,8 (FIXED_PROVISIONAL_FOR_PRIMARY_LACTATE_ANALYSIS + FACULTY_DECISION_PENDING) |
| Lado del lactato | 1215 puntos |
| **Candidatos** | **6 677 640** (con la multiplicidad de ρ: 20 032 920) |

| Tasa | Parte certificada | Certificado | Reproducido |
|---|---|---|---|
| 2,5 | P2I-2V-R | 2 628 | 2 628 |
| 2,5 | P2I-2W meta 1 | 264 | 264 |
| 2,5 | P2I-2W meta 1 y τ 480 | 756 | 756 |
| 2,5 | P2I-2W meta 1 y τ 960 | 0 | 0 |
| 2,5 | P2I-2W τ 480 | 0 | 0 |
| 2,5 | P2I-2W τ 960 | 0 | 0 |
| 2,5 | **total** | **3 648** | **3 648** |
| 5 | P2I-2Y, meta 0,5 y τ 120 | 1 134 | 1 134 |
| 5 | P2I-2Y, meta 0,75 y τ 120 | 378 | 378 |
| 5 | P2I-2Y, meta 0,75 y τ 240 | 756 | 756 |
| 5 | P2I-2Y, meta 1 y τ 120 | 399 | 399 |
| 5 | P2I-2Y, meta 1 y τ 480 | 756 | 756 |
| 5 | **total** | **3 423** | **3 423** |
| 6 | P2I-2Y, meta 0,5 y τ 120 | 756 | 756 |
| 6 | P2I-2Y, meta 0,75 y τ 240 | 756 | 756 |
| 6 | P2I-2Y, meta 1 y τ 480 | 756 | 756 |
| 6 | **total** | **2 268** | **2 268** |

Fuera de lo explorado por los registros certificados (entra por la regla docente de precarga): tasa 2,5, meta 1 y τ 480, posiciones 0,35 / 0,45: 756.

Claves de sangre del espacio: 72; fuera de las certificadas para el cristaloide: 0; exclusiones de la tasa 2,5: 0. Filas de sangre calculadas: 5 226; ilegibles: 0; contradicciones: 0.
<!-- /generado:origen -->

### 2.1 Lectura

- **De dónde sale la sangre:**
  - la región de robustez de P2I-2Y: los valores sobrevivientes de P2I-2V-R, con la extensión del relleno de P2I-2W
    (meta 1,0; τ 480);
  - las tasas 2,5, 5 y 6, con las tres posiciones de la banda de cada caso;
  - quedan los conjuntos que cumplen, en los dos casos, las restricciones de sangre vigentes que no leen el
    cristaloide (U-OUT, U-HB, FD-BLD-01, 02, SECOND-UNIT, 07, 08 y 09);
  - el cristaloide viejo sólo sirve para comprobar que se reproducen los conteos certificados (multiplicidad m por
    clave, con FD-BLD-04, 05 y 06).
- **Reproducción:** todos los conteos certificados se reproducen exactamente, cada uno en las posiciones que exploró su
  corrida (2,5: 2628 + 264 + 756; 5: 3423; 6: 2268).
- **Posiciones que entran:**
  - con las tasas 5 y 6, sólo la superior (57m 0,5 y 72f 0,6), igual que en P2I-2Y;
  - con la tasa 2,5 y el relleno meta 1 y τ 480, también **las posiciones medias (57m 0,35 y 72f 0,45)**: 34 conjuntos
    P3 y 756 candidatos de sangre que cumplen todas las restricciones de sangre vigentes;
  - nadie había explorado esas posiciones con esa tasa y ese relleno: P2I-2W fijó la posición superior en sus cajas y
    P2I-2Y exploró ese relleno sólo con las tasas 5, 6 y 7;
  - entran por la regla docente («las posiciones más bajas, sólo si sobreviven a las restricciones de sangre
    vigentes») y se informan aparte;
  - las posiciones inferiores no entran con ninguna tasa.
- **Claves:** las 72 claves de sangre del espacio son claves en las que el soporte del cristaloide está certificado
  (las de los sobrevivientes de P2I-2Y en 5 y 6; las de la tasa 2,5 que comprobó P2I-2AA, sin exclusiones).
- **ρ:**
  - el espacio se simula con ρ 2,5 y lleva la multiplicidad de los valores de ρ de la grilla de sangre (1; 2,5; 3);
  - todos los conjuntos sobreviven con los tres valores, y ρ se cancela en el déficit, D, el lactato y la adecuación
    (§4): los veredictos son idénticos con ρ 1 y 3;
  - ρ 1 queda fuera de la banda [2; 3] que registró P2I-2AA, y con ρ 1 no existe el estado COMPENSATED. Por eso las
    lecturas de «adecuación por compensación» y de la DO2 relativa a la normal (§7.1 y §9.1) valen para ρ 2,5.
- **Hemostasia y L3:** la endoscopía es la del propio motor, en el minuto 60 de los dos casos. Los modificadores de L3
  quedan fijos (0,8 y 0,1).

## 3. Lado del lactato (P2I-2AB-2)

- **Rangos, sin cambios:** los puntos candidatos del registro, sin agregar ni quitar ninguno:
  - τ_D: 30, 60, 120;
  - ganancia déficit→D (g): 0,5, 1, 2;
  - ganancia D→lactato (G): 2, 6, 12;
  - τ del lactato: 45, 120, 240;
  - exceso de lactato de llegada: los tres niveles de la banda de cada caso;
  - deuda y entrega de llegada: los cinco pares (deuda, entrega) de P2F, sin cambios.
  - Son 1215 puntos.
- **Demanda basal:** no es variable.
  - El registro no tiene puntos candidatos («nunca un parámetro libre para el lactato») y `calibration.case_values` la
    fija en 1,0.
  - El borrador de P2I-2AA preveía una sensibilidad de 0,9 / 1,1 sobre los sobrevivientes. Las dos fuentes no dicen lo
    mismo: el paquete siguió el registro, no la aplicó en la región congelada y lo deja como decisión (§14).
  - **Sensibilidad posterior, sólo informativa** (fuera del congelamiento; no filtra nada):
    - mismo filtro congelado, con la demanda escalada en el posproceso;
    - equivale exactamente al núcleo completo con la demanda basal escalada (diferencia 0,0 en corridas completas
      fuera de la región), y con ×1,0 reproduce la región exacta;
    - con ×0,9 sobreviven 274 960 (se conservan 216 407 de los 439 291);
    - con ×1,1 sobreviven 674 108 (se conservan 382 934 y entran 291 174);
    - la pertenencia a la región depende mucho de este supuesto, porque la demanda entra directo en el déficit.
- **Frecuencia intrínseca:** queda en el punto medio de la banda, porque no llega a la hemodinámica, a D ni al lactato
  (lo comprueba la validación, con los niveles inferior y superior).

## 4. Factorización (P2I-2AB-3)

<!-- generado:factorizacion -->
| Comprobación | Resultado |
|---|---|
| Corridas completas del núcleo comparadas | 720 |
| Coinciden todas | sí |
| Exactas con ρ 2,5 (lactato, D, déficit, hemostasia, detención) | sí |
| Mayor diferencia con ρ 1 y 3 | 7,1e-15 |
| Desacuerdos | 0 |
| Solo G × g y G × D0 llegan al lactato (diferencia con productos iguales) | 0,0e+00 |

Estados FD-LAC que ejerció la muestra: L1 FD-LAC-01 FAIL 81; L1 FD-LAC-01 PASS 99; L1 FD-LAC-02/03 falla 144; L1 FD-LAC-02/03 pasa 36; L1 FD-LAC-06 falla 126; L1 FD-LAC-06 pasa 54; L2 FD-LAC-06 falla 249; L2 FD-LAC-06 pasa 111; L3 FD-LAC-04 FAIL 9; L3 FD-LAC-04 NOT_EVALUABLE 28; L3 FD-LAC-04 PASS 143; L3 FD-LAC-05 FAIL 19; L3 FD-LAC-05 NOT_EVALUABLE 28; L3 FD-LAC-05 PASS 133; L3 FD-LAC-06 pasa 180.

| Eficiencia | Valor |
|---|---|
| Trayectorias hemodinámicas simuladas | L1 174; L2 2 088; L3 916 (total 3 178) |
| Corridas del producto ingenuo (candidatos × 3 escenarios × 2 casos) | 40 065 840 |
| Corridas completas de validación | 720 |
| Filas de sangre | 5 226 |
<!-- /generado:factorizacion -->

### 4.1 Lectura

- **Qué se simula:** el núcleo simula la hemodinámica una sola vez por escenario y entrada de sangre:
  - L1, por conjunto P1;
  - L2, por conjunto P1 y punto del cristaloide;
  - L3, por conjunto P3.
- **Qué se posprocesa:** el déficit, D y el lactato, con la aritmética del propio núcleo:
  - D lee la entrega del minuto anterior y la demanda del minuto;
  - el lactato, la D del minuto anterior;
  - las FD-LAC leen el estado al final de cada minuto.
- **Validación, antes del filtro:**
  - 720 corridas completas del núcleo: 3 conjuntos P3 por tasa, 6 puntos del lado del lactato, los tres escenarios
    (L2 con el primer y el último punto del cristaloide), y ρ 1 y 3 y la frecuencia intrínseca inferior y superior en
    el punto canónico;
  - coinciden exactamente con ρ 2,5 en el lactato, D, el déficit, la hemostasia y la detención, minuto a minuto;
  - con ρ 1 y 3 la diferencia máxima es de 7e-15, con los mismos veredictos;
  - la muestra ejerció PASS y FAIL de FD-LAC-01, 02/03, 04 y 05 y de FD-LAC-06 en L1 y L2, y NOT_EVALUABLE de 04 y
    05. No ejerció FD-LAC-06 FAIL en L3 (ningún candidato lo tuvo en todo el filtro), ni NOT_APPLICABLE ni
    ALREADY_NORMALIZED;
  - si hubiera fallado, la corrida se detenía sin recurrir a un cartesiano.
- **Qué llega al lactato:** sólo G × g y G × D0, dados τ_D y τ_L (álgebra de las recurrencias, comprobada
  numéricamente). Por eso g y G no son identificables por separado.
- **Eficiencia:** 3178 trayectorias del núcleo en lugar de 40 millones de corridas del producto ingenuo.

## 5. Escenarios y FD-LAC con la semántica vigente (P2I-2AB-4 a 9)

- **Escenarios:** los que produce el motor, con los valores del candidato. L4 queda fuera.
  - **L1:** sangrado sin tratamiento.
  - **L2:** 2000 mL de cristaloide en 20 min con el sangrado activo.
  - **L3:** IBP desde el minuto 0, 2 unidades de glóbulos rojos en 60 min y hemostasia endoscópica en el minuto 60,
    con los modificadores 0,8 y 0,1.
- **Adecuación:** un minuto es adecuado cuando el déficit efectivo es 0, es decir ρ × DO2 ≥ demanda. Las funciones
  congeladas de `faculty_constraints` leen exactamente eso, con «entrega» = ρ × DO2 y tolerancia 0 (una prueba lo
  comprueba minuto a minuto en la validación).
- **FD-LAC-01 y 06:**
  - **Ventanas:** se juzga cada tramo maximal con sangrado activo (antes de la hemostasia que registra el módulo GI) y
    déficit > 0, de al menos 30 min.
  - **Caída sostenida sustancial:** dos puntos de reevaluación (los extremos del tramo y cada múltiplo de 15) a 30 min
    o más, con L(tardío) ≤ 0,90 L(temprano). Es el umbral congelado, sin cambios.
  - **Clasificación de cada caída:** RECOVERING_CRITICAL si el déficit en el punto tardío es menor que en el temprano,
    con comparación exacta y sin tolerancia; si es igual o mayor, PERSISTENT_OR_WORSENING_CRITICAL. Sólo esta última
    viola la restricción.
  - **FD-LAC-01** lee L1 antes del minuto 60. **FD-LAC-06** lee las tres corridas completas.
  - La lectura de recuperación se aplica también a FD-LAC-01, como pide el encargo para esa restricción. El texto
    docente registrado en el módulo sólo nombra FD-LAC-06 (TD-90). En L1 no cambia nada: sin tratamiento el déficit
    nunca baja, y la revisión no encontró diferencias con la función congelada en 211 410 evaluaciones.
- **FD-LAC-02 a 05:** son las funciones congeladas.
  - **FD-LAC-02/03:** L60 de L1 dentro del sobre del caso, inclusive.
  - **FD-LAC-04:**
    - T* es lo último entre la hemostasia y el inicio de una adecuación que se sostiene 30 min;
    - exige L(T*+30) < L(T*) con aclaramiento en curso;
    - ALREADY_NORMALIZED si L(T*) ≤ 2,0; NOT_EVALUABLE si no hay adecuación sostenida (cuenta como que no contradice,
      como en FD-LAC v2).
  - **FD-LAC-05:** L120 dentro del sobre y por debajo de L(T*), con adecuación desde T* hasta 120; si no, NOT_EVALUABLE.
- **Trayectoria detenida:** si el gasto llega a cero con pulso, el candidato se rechaza aparte (STOPPED_TRAJECTORY).
  No ocurrió ninguna.

## 6. Filtro secuencial (P2I-2AB-10)

<!-- generado:filtro -->
| Etapa | Entran | Rechazados (SIMULATION_REJECTION) | ANALYTIC_REJECTION | Sobreviven | Unidades evaluadas / rechazadas |
|---|---|---|---|---|---|
| L1 (sin tratamiento) | 6 677 640 | 5 551 008 | 0 | 1 126 632 | 105 705 / 87 835 |
| L3 (sangre + hemostasia) | 1 126 632 | 558 936 | 0 | 567 696 | 93 886 / 46 578 |
| L2 (cristaloide con sangrado) | 567 696 | 128 405 | 0 | 439 291 | 114 756 / 26 187 |

| Etapa | Restricción y caso | Primer fallo | Cualquier fallo |
|---|---|---|---|
| L1 | FD-LAC-01 57m | 94 080 | 3 845 916 |
| L1 | FD-LAC-01 72f | 0 | 2 998 764 |
| L1 | FD-LAC-02/03 57m | 5 019 492 | 5 019 492 |
| L1 | FD-LAC-02/03 72f | 241 056 | 4 642 272 |
| L1 | FD-LAC-06 57m | 192 276 | 4 645 332 |
| L1 | FD-LAC-06 72f | 4 104 | 3 920 964 |
| L3 | FD-LAC-04 57m | 41 832 | 41 832 |
| L3 | FD-LAC-04 72f | 99 516 | 129 624 |
| L3 | FD-LAC-05 57m | 356 700 | 496 296 |
| L3 | FD-LAC-05 72f | 60 888 | 463 248 |
| L2 | FD-LAC-06 57m | 126 356 | 126 356 |
| L2 | FD-LAC-06 72f | 2 049 | 48 684 |

Candidatos: 6 677 640; sobrevivientes: **439 291** (6,6 %); con la multiplicidad de ρ: 1 317 873.
<!-- /generado:filtro -->

### 6.1 Lectura

- **Orden:** se fijó por costo antes de ver resultados: L1, después L3 y al final L2. Dentro de cada etapa se evalúan
  todas las restricciones en los dos casos, así que los conteos de «cualquier fallo» están completos.
- **Tipo de rechazo:** todos son SIMULATION_REJECTION; ANALYTIC_REJECTION es 0. Cada candidato toma el veredicto de su
  propia trayectoria posprocesada, y las trayectorias que no hizo falta simular por un rechazo anterior se cuentan
  como simulaciones evitadas, no como rechazos.
- **L1:**
  - FD-LAC-02 en 57m explica el 90 % de los rechazos como primer fallo: L60 debe quedar en 4,4–7,0, es decir, no
    puede bajar de la llegada;
  - por ejemplo, el par (deuda inferior, entrega superior), sin deuda y con la entrega de llegada justo en el umbral
    crítico (DO2 de 0,40 de la normal con ρ 2,5; déficit 0 al llegar), no deja ningún sobreviviente.
- **L3:** domina FD-LAC-05 en 57m (L120 fuera de 1,5–4,0 o no por debajo de L(T*)).
- **L2:** FD-LAC-06 en 57m rechaza 126 356 candidatos. Son caídas sostenidas del lactato con un déficit crítico
  persistente mientras el cristaloide entra con el sangrado activo.

## 7. Región (P2I-2AB-14) y lecturas de los sobrevivientes

<!-- generado:region -->
**FACULTY-CONSTRAINED CURRENT-PHYSIOLOGY LACTATE REGION (no value selected or approved)**: 7 811 unidades (P1 × lado del lactato), 439 291 candidatos; resumen de la región `ead624104a57948bf66ffd72e163e4847cff83f18698bc9b603f93f288006efe`.

| Lectura (mín · p5 · mediana · p95 · máx) | 57m | 72f |
|---|---|---|
| L60 sin tratamiento (mmol/L) | 4,40 · 4,44 · 4,92 · 5,98 · 6,22 | 3,61 · 3,68 · 4,22 · 5,34 · 5,50 |
| L120 con L3 (mmol/L) | 2,24 · 3,12 · 4,15 · 5,59 · 6,39 | 2,19 · 2,88 · 3,77 · 5,14 · 5,86 |
| L(T*) cuando hay T* (mmol/L) | 3,47 · 3,74 · 4,24 · 4,57 · 4,96 | 3,17 · 3,42 · 3,59 · 3,95 · 4,35 |
| caída a T* + 30 (fracción), si FD-LAC-04 se evalúa | 0,03 · 0,04 · 0,07 · 0,19 · 0,21 | 0,00 · 0,02 · 0,06 · 0,17 · 0,19 |
| memoria de una deuda de 60 a los 120′ (mmol/L) | 0,34 · 0,72 · 1,44 · 2,80 · 3,15 | 0,34 · 0,72 · 1,44 · 2,80 · 3,15 |

| Estado entre los sobrevivientes | 57m | 72f |
|---|---|---|
| FD-LAC-01 PASS | 439 291 (100,0 %) | 439 291 (100,0 %) |
| FD-LAC-04 PASS | 158 172 (36,0 %) | 137 194 (31,2 %) |
| FD-LAC-04 NOT_EVALUABLE | 281 119 (64,0 %) | 302 097 (68,8 %) |
| FD-LAC-05 PASS | 158 172 (36,0 %) | 135 115 (30,8 %) |
| FD-LAC-05 NOT_EVALUABLE | 281 119 (64,0 %) | 304 176 (69,2 %) |

| Sensibilidad de FD-LAC-04 (no filtra) | Sobrevivientes que también pasarían |
|---|---|
| cualquier caída | 439 291 (100,0 %) |
| caída ≥ 5 % | 370 444 (84,3 %) |
| caída ≥ 10 % | 311 208 (70,8 %) |
| caída ≥ 15 % | 290 927 (66,2 %) |

| Lectura informativa (no filtra) | Sobrevivientes |
|---|---|
| con una caída sostenida aceptada como RECOVERING_CRITICAL | L1 0; L2 3 338; L3 9 576 |
| con adecuación sólo por compensación en [T*, T* + 30] | 158 172 |
| con caída sostenida y déficit crítico persistente después de la hemostasia (L3) | 71 661 (16,3 %) |
| T* en L3 | 57m: minuto 60 158 172, sin T* 281 119; 72f: minuto 60 137 194, sin T* 302 097 |
<!-- /generado:region -->

### 7.1 Lectura

- **Sesgo de supervivencia: FD-LAC-04 y 05 se cumplen sin evaluarse en la mayoría.**
  - En 57m el 64 % de los sobrevivientes no tiene T* en L3, y en 72f el 69 %: con 2 unidades y hemostasia en el
    minuto 60, el déficit no vuelve a 0 dentro de los 120 min.
  - Un cálculo posterior, sólo informativo y fuera del congelamiento (una prueba lo recalcula), cruza los dos casos:
    - 135 115 sobrevivientes (30,8 %) tienen FD-LAC-04 y 05 evaluadas de verdad en ambos casos;
    - los otros 304 176 (69,2 %) las cumplen como NOT_EVALUABLE en al menos un caso, y **todos tienen la entrega de
      llegada inferior** (DO2 de llegada = 0,6 de la entrega crítica);
    - con la entrega media o superior, todos los sobrevivientes se evalúan.
  - El veredicto congelado sólo exige que FD-LAC-04/05 se evalúen en algún sobreviviente; esto queda como decisión
    docente (§14).
- **T*:** cuando existe, es siempre el minuto 60. En L3 la adecuación o ya estaba antes de la hemostasia y se sostiene,
  o no llega dentro del horizonte.
- **NOT_EVALUABLE con T*:** en 72f, 2079 sobrevivientes tienen T* y FD-LAC-04 PASS, pero FD-LAC-05 NOT_EVALUABLE,
  porque pierden la adecuación después de T* + 30. De ellos, 336 terminan con L120 por encima del sobre de 72f (máximo
  3,83 contra 3,5). Todos tienen la entrega de llegada inferior y están dentro de los 304 176 de arriba (cálculo
  posterior, confirmado con una sonda propia).
- **Compensación:** 158 172 sobrevivientes tienen algún minuto COMPENSATED (déficit 0 con la DO2 por debajo de la
  normal) entre T* y T* + 30, el mismo número que tiene T* en 57m. La adecuación que habilita FD-LAC-04/05 es
  compensada (en los representativos, DO2 de 0,42 a 0,62 de la normal); con la lectura previa a la decisión docente
  (entrega ≥ demanda) esos minutos no serían adecuados. La decisión sobre la adecuación es, por eso, decisiva.
- **Recuperación:** la semántica de recuperación cambió el resultado de unos pocos: 3338 sobrevivientes en L2 y 9576 en
  L3 tienen una caída sostenida durante el sangrado que se aceptó porque el déficit estaba bajando.
- **FD-LAC-04, magnitud:** entre los evaluados, la caída a T* + 30 tiene una mediana del 7 % (57m) y del 5,5 % (72f).
  Con un umbral ≥ 10 % (sensibilidad, no aprobado) dejarían de pasar 128 083 sobrevivientes, la mayoría de los que
  tienen FD-LAC-04 evaluada.
- **Trayectorias que la regla no juzga:** 71 661 sobrevivientes (16,3 %) tienen en L3, después de la hemostasia, una
  caída sostenida del lactato con un déficit crítico persistente o que empeora.
  - FD-LAC-06 no lo juzga porque, con la semántica congelada, el sangrado ya no está activo después del minuto 60,
    aunque el modificador deja un 10 % de pérdida residual.
  - Se informa y no se filtra (§14).
- **L60 y L120:**
  - L60 queda dentro de los sobres por construcción: 57m de 4,40 a 6,22 y 72f de 3,61 a 5,50.
  - Los L120 altos (hasta 6,4) son de candidatos sin T*, en los que FD-LAC-05 no se evalúa.

## 8. Identificabilidad y bordes (P2I-2AB-11)

<!-- generado:identificabilidad -->
| Dimensión | Explorado | Sobrevive (candidatos) | Clase | Borde |
|---|---|---|---|---|
| G × g | 1, 2, 3, 4, 6, 12, 24 | 1 0, 2 0, 3 29 316, 4 9 318, 6 100 064, 12 161 421, 24 139 172 | parcialmente acotado | abierto arriba |
| B0 (mL) | 3000, 4000, 5000 | 3000 106 637, 4000 182 075, 5000 150 579 | mal identificado | abierto en ambos bordes |
| entrega de llegada | inferior, medio, superior | inferior 332 361, medio 95 249, superior 11 681 | mal identificado | abierto en ambos bordes |
| exceso de lactato de llegada | inferior, medio, superior | inferior 181 450, medio 135 103, superior 122 738 | mal identificado | abierto en ambos bordes |
| deuda de llegada | inferior, medio, superior | inferior 95 472, medio 95 249, superior 248 570 | mal identificado | abierto en ambos bordes |
| par (deuda, entrega) de llegada | deuda inferior · entrega inferior, deuda inferior · entrega superior, deuda medio · entrega medio, deuda superior · entrega inferior, deuda superior · entrega superior | deuda inferior · entrega inferior 95 472, deuda inferior · entrega superior 0, deuda medio · entrega medio 95 249, deuda superior · entrega inferior 236 889, deuda superior · entrega superior 11 681 | parcialmente acotado | — |
| tasa de sangrado (mL-eq/min) | 2,5, 5, 6 | 2,5 91 614, 5 205 883, 6 141 794 | mal identificado | abierto en ambos bordes |
| F0 | 0,2 | 0,2 439 291 | no varía | — |
| Finf | 0,05, 0,1 | 0,05 256 528, 0,1 182 763 | mal identificado | abierto en ambos bordes |
| punto del cristaloide | 12 puntos | los 12 sobreviven (36 017 a 38 070 cada uno) | mal identificado | — |
| τ del cristaloide (min) | 30, 60, 90, 120, 150, 180, 210, 240 | 30 37 534, 60 74 640, 90 73 339, 120 72 766, 150 72 388, 180 36 359, 210 36 210, 240 36 055 | mal identificado | abierto en ambos bordes |
| τ_D (min) | 30, 60, 120 | 30 157 106, 60 156 766, 120 125 419 | mal identificado | abierto en ambos bordes |
| ganancia déficit→D (g) | 0,5, 1, 2 | 0,5 74 233, 1 121 182, 2 243 876 | no identificable por separado | abierto en ambos bordes |
| τ del lactato (min) | 45, 120, 240 | 45 53 175, 120 157 176, 240 228 940 | mal identificado | abierto en ambos bordes |
| ganancia D→lactato (G) | 2, 6, 12 | 2 9 318, 6 179 849, 12 250 124 | no identificable por separado | abierto en ambos bordes |
| capacidad del relleno (mL) | 100, 500, 1000 | 100 92 745, 500 173 273, 1000 173 273 | mal identificado | abierto en ambos bordes |
| meta del relleno | 0,5, 0,75, 1 | 0,5 139 985, 0,75 148 255, 1 151 051 | mal identificado | abierto en ambos bordes |
| τ del relleno (min) | 120, 240, 480 | 120 196 275, 240 120 110, 480 122 906 | mal identificado | abierto en ambos bordes |
| posición 57m | 0,35, 0,5 | 0,35 13 330, 0,5 425 961 | mal identificado | abierto en ambos bordes |
| posición 72f | 0,45, 0,6 | 0,45 13 330, 0,6 425 961 | mal identificado | abierto en ambos bordes |
| λ/κ (mL) | 600, 833, 1500 | 600 37 377, 833 40 907, 1500 361 007 | mal identificado | abierto en ambos bordes |
| Hb de la unidad (g/dL) | 18, 20, 22 | 18 126 160, 20 155 322, 22 157 809 | mal identificado | abierto en ambos bordes |
| volumen de la unidad (mL) | 250, 300, 350 | 250 166 078, 300 157 711, 350 115 502 | mal identificado | abierto en ambos bordes |
| reserva de extracción ρ | 1, 2,5, 3 | 1 439 291, 2,5 439 291, 3 439 291 | no identificable por separado | abierto en ambos bordes |
<!-- /generado:identificabilidad -->

### 8.1 Lectura

- **Bien acotado:** ninguna dimensión.
- **Parcialmente acotados:**
  - G × g: quedan afuera los productos 1 y 2; el borde superior sigue abierto;
  - el par de llegada: queda afuera (deuda inferior, entrega superior).
- **Mal identificadas, con los dos bordes abiertos:** τ_D, τ_L, el exceso de llegada, la deuda y la entrega de llegada,
  y todas las de sangre. Las restricciones FD-LAC no acotan ninguna cinética del lactato dentro de la grilla.
- **No identificables por separado:**
  - g y G: sólo llegan G × g y G × D0;
  - la deuda de llegada D0, por la misma razón: (G, g, D0) y (cG, g/c, D0/c) dan el mismo lactato. La tabla la muestra
    como mal identificada, pero estructuralmente tampoco se identifica por separado (TD-90);
  - ρ, que se cancela.
- **Qué significa «abierto»:** los bordes se leen sobre la grilla del espacio de origen, después del filtro de sangre.
  Fuera de esa grilla sí hay límites:
  - las posiciones 0,2 y 0,3 las rechazó la sangre, y 0,5 y 0,6 son el límite de la banda del caso;
  - las tasas de 7 o más las excluyó la docencia;
  - τ del cristaloide tiene tope en 240.
- **Cristaloide:** sobreviven los 12 puntos, con pesos casi iguales (36 017 a 38 070). El lactato no distingue τ del
  cristaloide, y la incertidumbre del fluido se propaga entera.
- **Ningún valor se elige por su frecuencia.**

## 9. Revisión fisiológica de los representativos (P2I-2AB-12)

LOW, MID y HIGH son el primero, el del medio (rango ⌊n/2⌋) y el último de los sobrevivientes ordenados por el L60 de
L1 en 57m, después en 72f y después por el orden de origen. Cada uno se vuelve a correr con el núcleo completo.
Intervalos: A adecuado, R crítico en recuperación, P crítico persistente o que empeora (sólo con sangrado activo).

<!-- generado:representativos -->
**LOW** (rango 0): τ_D 30, g 1, G 6, τ_L 240, exceso inferior, deuda medio, entrega medio; tasa 2,5, B0 5000, λ/κ 833, relleno 1 / 480 / 500, unidad 18 g/dL × 350 mL, posiciones 0,5 / 0,6; cristaloide F0 0,2 · Finf 0,05 · τ 60.

| Caso · escenario | min | Δ volumen circulante (mL-eq) | Perdido (mL) | Hb (g/dL) | Gasto relativo | DO2 (índice) | Estado | Déficit | D | Lactato (mmol/L) |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m L1 | 0 | 0 | 0 | 6,70 | 1,000 | 0,340 | CRITICAL | 0,150 | 20,0 | 4,40 |
| 57m L1 | 15 | -37 | 38 | 6,70 | 0,955 | 0,325 | CRITICAL | 0,189 | 14,1 | 4,46 |
| 57m L1 | 30 | -73 | 75 | 6,70 | 0,909 | 0,309 | CRITICAL | 0,228 | 10,9 | 4,46 |
| 57m L1 | 60 | -141 | 150 | 6,69 | 0,815 | 0,277 | CRITICAL | 0,308 | 9,2 | 4,40 |
| 57m L1 | 90 | -205 | 225 | 6,67 | 0,721 | 0,244 | CRITICAL | 0,390 | 10,1 | 4,34 |
| 57m L1 | 120 | -266 | 300 | 6,65 | 0,624 | 0,211 | CRITICAL | 0,473 | 12,0 | 4,33 |
| 57m L3 | 0 | 0 | 0 | 6,70 | 1,000 | 0,340 | CRITICAL | 0,150 | 20,0 | 4,40 |
| 57m L3 | 15 | 145 | 30 | 7,08 | 1,160 | 0,417 | COMPENSATED | 0,000 | 12,7 | 4,45 |
| 57m L3 | 30 | 290 | 60 | 7,44 | 1,294 | 0,489 | COMPENSATED | 0,000 | 7,6 | 4,43 |
| 57m L3 | 60 | 582 | 118 | 8,10 | 1,502 | 0,618 | COMPENSATED | 0,000 | 2,8 | 4,26 |
| 57m L3 | 90 | 574 | 126 | 8,10 | 1,498 | 0,616 | COMPENSATED | 0,000 | 1,0 | 4,03 |
| 57m L3 | 120 | 567 | 133 | 8,10 | 1,493 | 0,614 | COMPENSATED | 0,000 | 0,4 | 3,81 |
| 72f L1 | 0 | 0 | 0 | 6,40 | 1,000 | 0,340 | CRITICAL | 0,150 | 20,0 | 3,40 |
| 72f L1 | 15 | -37 | 38 | 6,40 | 0,970 | 0,330 | CRITICAL | 0,176 | 14,0 | 3,52 |
| 72f L1 | 30 | -73 | 75 | 6,40 | 0,939 | 0,319 | CRITICAL | 0,202 | 10,7 | 3,58 |
| 72f L1 | 60 | -141 | 150 | 6,39 | 0,877 | 0,298 | CRITICAL | 0,256 | 8,3 | 3,61 |
| 72f L1 | 90 | -205 | 225 | 6,37 | 0,814 | 0,276 | CRITICAL | 0,311 | 8,5 | 3,61 |
| 72f L1 | 120 | -266 | 300 | 6,35 | 0,750 | 0,253 | CRITICAL | 0,367 | 9,6 | 3,64 |
| 72f L3 | 0 | 0 | 0 | 6,40 | 1,000 | 0,340 | CRITICAL | 0,150 | 20,0 | 3,40 |
| 72f L3 | 15 | 145 | 30 | 6,79 | 1,106 | 0,399 | CRITICAL | 0,002 | 12,9 | 3,52 |
| 72f L3 | 30 | 290 | 60 | 7,16 | 1,196 | 0,455 | COMPENSATED | 0,000 | 7,8 | 3,55 |
| 72f L3 | 60 | 582 | 118 | 7,84 | 1,335 | 0,556 | COMPENSATED | 0,000 | 2,8 | 3,48 |
| 72f L3 | 90 | 574 | 126 | 7,84 | 1,332 | 0,555 | COMPENSATED | 0,000 | 1,0 | 3,35 |
| 72f L3 | 120 | 567 | 133 | 7,84 | 1,329 | 0,553 | COMPENSATED | 0,000 | 0,4 | 3,21 |

| Caso · escenario | Intervalos de 15′ con sangrado (A / R / P) | Marcas |
|---|---|---|
| 57m L1 | P P P P P P P P | ninguna |
| 57m L3 | A A A A | ninguna |
| 72f L1 | P P P P P P P P | ninguna |
| 72f L3 | R A A A | ninguna |

**MID** (rango 219 645): τ_D 60, g 2, G 6, τ_L 240, exceso medio, deuda superior, entrega inferior; tasa 5, B0 3000, λ/κ 1500, relleno 0,75 / 120 / 100, unidad 20 g/dL × 250 mL, posiciones 0,5 / 0,6; cristaloide F0 0,2 · Finf 0,05 · τ 180.

| Caso · escenario | min | Δ volumen circulante (mL-eq) | Perdido (mL) | Hb (g/dL) | Gasto relativo | DO2 (índice) | Estado | Déficit | D | Lactato (mmol/L) |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m L1 | 0 | 0 | 0 | 6,70 | 1,000 | 0,240 | CRITICAL | 0,400 | 60,0 | 4,40 |
| 57m L1 | 15 | -72 | 75 | 6,69 | 0,951 | 0,228 | CRITICAL | 0,430 | 57,7 | 4,55 |
| 57m L1 | 30 | -138 | 150 | 6,67 | 0,904 | 0,216 | CRITICAL | 0,460 | 56,7 | 4,68 |
| 57m L1 | 60 | -268 | 300 | 6,63 | 0,804 | 0,191 | CRITICAL | 0,523 | 57,7 | 4,92 |
| 57m L1 | 90 | -403 | 450 | 6,59 | 0,692 | 0,163 | CRITICAL | 0,592 | 61,4 | 5,16 |
| 57m L1 | 120 | -541 | 600 | 6,56 | 0,565 | 0,133 | CRITICAL | 0,668 | 67,1 | 5,42 |
| 57m L3 | 0 | 0 | 0 | 6,70 | 1,000 | 0,240 | CRITICAL | 0,400 | 60,0 | 4,40 |
| 57m L3 | 15 | 65 | 60 | 7,24 | 1,042 | 0,270 | CRITICAL | 0,324 | 56,3 | 4,55 |
| 57m L3 | 30 | 130 | 120 | 7,74 | 1,083 | 0,300 | CRITICAL | 0,249 | 51,5 | 4,66 |
| 57m L3 | 60 | 264 | 236 | 8,67 | 1,161 | 0,360 | CRITICAL | 0,099 | 39,2 | 4,77 |
| 57m L3 | 90 | 249 | 252 | 8,67 | 1,153 | 0,358 | CRITICAL | 0,105 | 28,5 | 4,72 |
| 57m L3 | 120 | 234 | 266 | 8,67 | 1,144 | 0,355 | CRITICAL | 0,112 | 22,4 | 4,58 |
| 72f L1 | 0 | 0 | 0 | 6,40 | 1,000 | 0,240 | CRITICAL | 0,400 | 60,0 | 3,40 |
| 72f L1 | 15 | -72 | 75 | 6,39 | 0,967 | 0,232 | CRITICAL | 0,420 | 57,6 | 3,61 |
| 72f L1 | 30 | -138 | 150 | 6,37 | 0,936 | 0,224 | CRITICAL | 0,441 | 56,3 | 3,80 |
| 72f L1 | 60 | -268 | 300 | 6,33 | 0,869 | 0,206 | CRITICAL | 0,484 | 56,0 | 4,13 |
| 72f L1 | 90 | -403 | 450 | 6,29 | 0,794 | 0,187 | CRITICAL | 0,531 | 58,0 | 4,43 |
| 72f L1 | 120 | -541 | 600 | 6,26 | 0,710 | 0,167 | CRITICAL | 0,583 | 61,5 | 4,73 |
| 72f L3 | 0 | 0 | 0 | 6,40 | 1,000 | 0,240 | CRITICAL | 0,400 | 60,0 | 3,40 |
| 72f L3 | 15 | 65 | 60 | 6,95 | 1,028 | 0,268 | CRITICAL | 0,330 | 56,4 | 3,61 |
| 72f L3 | 30 | 130 | 120 | 7,47 | 1,055 | 0,295 | CRITICAL | 0,261 | 51,8 | 3,78 |
| 72f L3 | 60 | 264 | 236 | 8,41 | 1,107 | 0,349 | CRITICAL | 0,127 | 40,3 | 4,00 |
| 72f L3 | 90 | 249 | 252 | 8,41 | 1,102 | 0,347 | CRITICAL | 0,131 | 30,5 | 4,06 |
| 72f L3 | 120 | 234 | 266 | 8,41 | 1,096 | 0,346 | CRITICAL | 0,136 | 24,8 | 4,02 |

| Caso · escenario | Intervalos de 15′ con sangrado (A / R / P) | Marcas |
|---|---|---|
| 57m L1 | P P P P P P P P | ninguna |
| 57m L3 | R R R R | ninguna |
| 72f L1 | P P P P P P P P | ninguna |
| 72f L3 | R R R R | ninguna |

**HIGH** (rango 439 290): τ_D 30, g 0,5, G 12, τ_L 240, exceso medio, deuda superior, entrega inferior; tasa 6, B0 3000, λ/κ 1500, relleno 1 / 480 / 1000, unidad 22 g/dL × 250 mL, posiciones 0,5 / 0,6; cristaloide F0 0,2 · Finf 0,1 · τ 150.

| Caso · escenario | min | Δ volumen circulante (mL-eq) | Perdido (mL) | Hb (g/dL) | Gasto relativo | DO2 (índice) | Estado | Déficit | D | Lactato (mmol/L) |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m L1 | 0 | 0 | 0 | 6,70 | 1,000 | 0,240 | CRITICAL | 0,400 | 60,0 | 4,40 |
| 57m L1 | 15 | -89 | 90 | 6,70 | 0,939 | 0,225 | CRITICAL | 0,437 | 38,6 | 5,38 |
| 57m L1 | 30 | -175 | 180 | 6,69 | 0,877 | 0,210 | CRITICAL | 0,475 | 25,9 | 5,90 |
| 57m L1 | 60 | -339 | 360 | 6,65 | 0,747 | 0,178 | CRITICAL | 0,555 | 14,4 | 6,22 |
| 57m L1 | 90 | -493 | 540 | 6,58 | 0,611 | 0,144 | CRITICAL | 0,640 | 11,0 | 6,19 |
| 57m L1 | 120 | -638 | 720 | 6,49 | 0,470 | 0,109 | CRITICAL | 0,727 | 10,6 | 6,08 |
| 57m L3 | 0 | 0 | 0 | 6,70 | 1,000 | 0,240 | CRITICAL | 0,400 | 60,0 | 4,40 |
| 57m L3 | 15 | 53 | 72 | 7,32 | 1,035 | 0,271 | CRITICAL | 0,322 | 38,2 | 5,38 |
| 57m L3 | 30 | 106 | 144 | 7,90 | 1,068 | 0,302 | CRITICAL | 0,244 | 24,7 | 5,87 |
| 57m L3 | 60 | 216 | 284 | 8,98 | 1,134 | 0,365 | CRITICAL | 0,088 | 10,4 | 6,08 |
| 57m L3 | 90 | 198 | 302 | 8,98 | 1,124 | 0,361 | CRITICAL | 0,097 | 4,7 | 5,82 |
| 57m L3 | 120 | 180 | 320 | 8,98 | 1,113 | 0,358 | CRITICAL | 0,105 | 2,7 | 5,42 |
| 72f L1 | 0 | 0 | 0 | 6,40 | 1,000 | 0,240 | CRITICAL | 0,400 | 60,0 | 3,40 |
| 72f L1 | 15 | -89 | 90 | 6,40 | 0,959 | 0,230 | CRITICAL | 0,425 | 38,5 | 4,44 |
| 72f L1 | 30 | -175 | 180 | 6,39 | 0,918 | 0,220 | CRITICAL | 0,450 | 25,8 | 5,01 |
| 72f L1 | 60 | -339 | 360 | 6,35 | 0,831 | 0,198 | CRITICAL | 0,505 | 13,9 | 5,43 |
| 72f L1 | 90 | -493 | 540 | 6,29 | 0,741 | 0,175 | CRITICAL | 0,563 | 10,2 | 5,46 |
| 72f L1 | 120 | -638 | 720 | 6,20 | 0,647 | 0,150 | CRITICAL | 0,624 | 9,4 | 5,39 |
| 72f L3 | 0 | 0 | 0 | 6,40 | 1,000 | 0,240 | CRITICAL | 0,400 | 60,0 | 3,40 |
| 72f L3 | 15 | 53 | 72 | 7,03 | 1,023 | 0,270 | CRITICAL | 0,326 | 38,2 | 4,44 |
| 72f L3 | 30 | 106 | 144 | 7,63 | 1,045 | 0,299 | CRITICAL | 0,252 | 24,7 | 4,99 |
| 72f L3 | 60 | 216 | 284 | 8,72 | 1,089 | 0,356 | CRITICAL | 0,109 | 10,6 | 5,31 |
| 72f L3 | 90 | 198 | 302 | 8,72 | 1,083 | 0,354 | CRITICAL | 0,115 | 4,9 | 5,15 |
| 72f L3 | 120 | 180 | 320 | 8,72 | 1,075 | 0,352 | CRITICAL | 0,121 | 2,9 | 4,84 |

| Caso · escenario | Intervalos de 15′ con sangrado (A / R / P) | Marcas |
|---|---|---|
| 57m L1 | P P P P P P P P | ninguna |
| 57m L3 | R R R R | déficit crítico que empeora con caída grande del lactato |
| 72f L1 | P P P P P P P P | ninguna |
| 72f L3 | R R R R | ninguna |
<!-- /generado:representativos -->

### 9.1 Lectura

- **LOW (tasa 2,5, entrega media, deuda media):**
  - L1 queda estable (57m de 4,4 a 4,3; 72f de 3,4 a 3,6) con un déficit que empeora;
  - en L3 la adecuación llega a los 15 min por compensación (DO2 0,42–0,62 de la normal) y el lactato baja despacio:
    57m de 4,26 a 3,81 entre los minutos 60 y 120;
  - no tiene marcas.
- **MID (tasa 5, entrega inferior, deuda superior):**
  - L1 sube de forma sostenida (57m de 4,4 a 5,4);
  - en L3 el déficit baja de 0,40 a 0,10 hasta la hemostasia y después **vuelve a subir un poco (0,10 → 0,11) y sigue
    crítico hasta 120**;
  - el lactato queda casi plano (4,8 → 4,6), y FD-LAC-04/05 son NOT_EVALUABLE;
  - no tiene marcas.
- **HIGH (tasa 6, entrega inferior, deuda superior, τ_D 30, g 0,5, G 12):**
  - en L1, **D baja de 60 a 10,6 mientras el déficit empeora de 0,40 a 0,73**: con τ_D 30 y g 0,5, la devolución de
    primer orden del núcleo domina aunque siga habiendo déficit. El lactato sube igual, porque G es 12;
  - en L3 (57m) queda la marca de déficit crítico que empeora con una caída grande del lactato: entre los minutos 60 y
    120 el lactato baja de 6,08 a 5,42 (−11 %) con el déficit en 0,088 → 0,105, después de la hemostasia.
- **Lo que no apareció en ninguno:** normalización instantánea, D alta persistente en L3 ni valores fuera de los
  marcadores propuestos de supervivencia.
- **Efecto de las 2 unidades:**
  - la Hb sube de 6,7 a 8,1–9,0 y el gasto relativo a 1,1–1,5 veces el de llegada;
  - con la entrega de llegada inferior, la DO2 llega a 0,36 de la normal, por debajo del umbral crítico de 0,40 con
    ρ 2,5: por eso esos candidatos no recuperan la adecuación dentro de los 120 min.

## 10. Legado sólo como referencia (P2I-2AB-13)

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
| HIGH 57m L1 | 0′ 4,40 / 4,4; 60′ 6,22 / 4,8; 120′ 6,08 / 5,1 |
| HIGH 57m L3 | 0′ 4,40 / 4,4; 60′ 6,08 / 3,2; 120′ 5,42 / 3,3 |
| HIGH 72f L1 | 0′ 3,40 / 3,4; 60′ 5,43 / 3,8; 120′ 5,39 / 4,1 |
| HIGH 72f L3 | 0′ 3,40 / 3,4; 60′ 5,31 / 2,2; 120′ 4,84 / 2,3 |
| LOW 57m L1 | 0′ 4,40 / 4,4; 60′ 4,40 / 4,8; 120′ 4,33 / 5,1 |
| LOW 57m L3 | 0′ 4,40 / 4,4; 60′ 4,26 / 3,2; 120′ 3,81 / 3,3 |
| LOW 72f L1 | 0′ 3,40 / 3,4; 60′ 3,61 / 3,8; 120′ 3,64 / 4,1 |
| LOW 72f L3 | 0′ 3,40 / 3,4; 60′ 3,48 / 2,2; 120′ 3,21 / 2,3 |
| MID 57m L1 | 0′ 4,40 / 4,4; 60′ 4,92 / 4,8; 120′ 5,42 / 5,1 |
| MID 57m L3 | 0′ 4,40 / 4,4; 60′ 4,77 / 3,2; 120′ 4,58 / 3,3 |
| MID 72f L1 | 0′ 3,40 / 3,4; 60′ 4,13 / 3,8; 120′ 4,73 / 4,1 |
| MID 72f L3 | 0′ 3,40 / 3,4; 60′ 4,00 / 2,2; 120′ 4,02 / 2,3 |
<!-- /generado:legado -->

### 10.1 Lectura

- **Cuándo se leyó:** el lactato del motor heredado se leyó después del filtro y de los representativos. Ninguna
  restricción ni ningún orden lo usan; una prueba exige que sólo `legacy_reference` lo lea y que falle mientras dura
  el filtro.
- **Comparación con el núcleo:** en L3 el legado baja rápido (57m de 4,4 a 3,2 en 60 min); el núcleo baja más despacio
  (LOW de 4,40 a 4,26) o no baja (MID y HIGH, sin adecuación). Es una diferencia de conducta, no un blanco.

## 11. Veredicto y próximo dominio (P2I-2AB-15)

<!-- generado:veredicto -->
**LACTATE_CALIBRATION_CONSTRAINTS_SATISFIED**

| Comprobación | Resultado |
|---|---|
| FD-LAC-04/05 evaluadas en ambos casos en algún sobreviviente | sí |
| factorización exacta | sí |
| claves certificadas | sí |
| preparación | sí |
| fuente de sangre reproducida | sí |
| hay sobrevivientes | sí |

Regla congelada: LACTATE_CALIBRATION_CONSTRAINTS_SATISFIED when readiness is the faculty's READY, the blood source reproduces the certified counts, its keys are certified for the crystalloid support, the factorization agrees with the full core, at least one candidate survives, and among the survivors FD-LAC-04 and FD-LAC-05 are actually evaluated (PASS or ALREADY_NORMALIZED) in both cases for at least one candidate, so the definitive-management constraints are not met only as NOT_EVALUABLE. Otherwise LACTATE_NOT_READY with the first blocker. No candidate, value or parameter is selected or approved.

Próximo dominio: Recommended next domain (not started; needs its own authorization): blood-pressure and heart-rate calibration of the shadow core on the faculty-constrained blood, crystalloid and lactate region, before collapse, GI migration or any runtime integration.
<!-- /generado:veredicto -->

### 11.1 Lectura

- **Qué dice el veredicto:** LACTATE_CALIBRATION_CONSTRAINTS_SATISFIED según la regla congelada. Existe una región no
  vacía de candidatos de la fisiología actual que cumple FD-LAC-01 a 06 en los dos casos, con la factorización exacta,
  la sangre reproducida, las claves certificadas y FD-LAC-04/05 evaluadas de verdad en una parte.
- **Qué no dice:** que la región esté bien identificada (§8), ni que el 69 % que cumple FD-LAC-04/05 sin evaluarlas
  sea aceptable (§7.1), ni que las caídas posteriores a la hemostasia (16 %) sean fisiológicas. Esas preguntas quedan
  en §14.
- **Código y texto del veredicto:** el texto exige FD-LAC-04/05 evaluadas en los dos casos en un mismo candidato; el
  código lo comprueba en cada caso por separado (TD-90). Con este registro da lo mismo: 135 115 candidatos las tienen
  evaluadas en ambos casos, y una prueba lo fija.
- **Demanda basal:** con la demanda ±10 % la región cambia mucho (§3). El veredicto se mantendría, porque sigue
  habiendo sobrevivientes evaluados, pero la pertenencia a la región no es robusta a ese supuesto.
- **Próximo dominio recomendado, sin empezar:** la calibración de la presión arterial y la frecuencia cardíaca del
  núcleo en sombra sobre esta región, antes del colapso, de la migración de GI o de cualquier integración. Necesita
  su propia autorización.

## 12. Congelamiento, recongelamiento y entrega

- **Primer congelamiento:** `e234a54`, antes de evaluar cualquier candidato.
- **La corrida se detuvo en su primera comprobación**, dentro de la fuente de sangre y antes de la validación y de
  cualquier FD-LAC:
  - con la tasa 2,5 y el relleno meta 1 y τ 480 reproducía 1512 contra 756 certificados;
  - causa: la regla congelada comparaba las tres posiciones con un conteo de P2I-2W que sólo exploró la superior.
- **Recongelamiento:** `68b92de`.
  - Cada conteo certificado se compara sólo en las posiciones y los rellenos que exploró su corrida, y debe coincidir
    exactamente.
  - Ninguna celda explorada puede quedar sin cubrir.
  - Lo que está fuera de lo explorado se informa aparte.
  - No cambió ninguna regla FD-LAC, ningún rango, el lado del lactato, el orden del filtro ni el veredicto.
- **Corrida:** la evaluación corrió sobre `68b92de` (unos 2 min con 4 procesos, cada uno con la guarda P2F y el bloqueo
  del legado). El registro es el del módulo; sólo el mapeo fue paralelo, y `--run` lo reproduce en un solo proceso.
- **Entrega:** un commit ejecutable (código del informe, pruebas, JSON e informes), sobre el que corre la certificación
  completa, y uno posterior sólo de documentación, si hace falta.
- **Revisión adversarial (una sola):**
  - sin BLOCKER: reprodujo la región, las etapas y la factorización, y juzgó 83 candidatos al azar con corridas
    completas del núcleo, sin diferencias;
  - no encontró fugas de la región de P2F ni del legado;
  - su hallazgo MAJOR, la sensibilidad a la demanda basal, se informa en §3 y queda como decisión docente;
  - tres detalles de código sin efecto en el registro quedan como TD-90:
    - la regla de reproducción toma de P2I-2Y sólo los pares con sobrevivientes, y su cláusula de celdas no cubiertas
      es vacía por construcción (sin efecto, porque nada queda fuera de lo explorado con las tasas 5 y 6);
    - el veredicto comprueba cada caso por separado;
    - la etiqueta de la deuda de llegada;
  - el resto son precisiones de este informe.

## 13. Qué no hace

- **Restricciones:** no cambia ninguna FD-BLD ni FD-LAC (`faculty_constraints.py` y `blood_constraints.py` son
  idénticos byte a byte). Tampoco cambia ningún rango del registro.
- **Aprobaciones:** no aprueba, no elige y no interpola ningún parámetro; tampoco usa la frecuencia entre los
  sobrevivientes.
- **P2F:** no lee la región histórica de P2F (1054 candidatos) ni sus registros.
- **Legado:** no usa el lactato heredado como objetivo.
- **L3:** no inventa rangos para los modificadores de L3 (FD-24 y FD-25 siguen abiertas).
- **Otros límites:** no calibra la presión ni la FC, no activa el colapso, no migra ni integra nada. TD-88 y TD-89
  siguen abiertas.

## 14. Decisiones pendientes (docencia)

- **FD-LAC-04/05 sin evaluar:**
  - el 69 % de los sobrevivientes, todos con la entrega de llegada inferior, no recupera el déficit 0 dentro de
    120 min con 2 unidades y hemostasia, y cumple esas restricciones como NOT_EVALUABLE;
  - opciones:
    - aceptarlo;
    - tratar NOT_EVALUABLE como fallo (la sensibilidad que ya prevé FD-LAC v2);
    - revisar si la entrega de llegada inferior (0,6 de la crítica) es compatible con los casos.
- **Caída del lactato con déficit crítico después de la hemostasia** (16 %): si la regla de FD-LAC-06 sobre el déficit
  persistente debe aplicarse también después de la hemostasia, cuando el déficit sigue crítico y queda un 10 % de
  sangrado residual.
- **Devolución de D con déficit en curso** (representativo HIGH): el núcleo devuelve D con τ_D aunque siga habiendo
  déficit. ¿Es aceptable, o hace falta una restricción sobre D?
- **Magnitud de FD-LAC-04:** entre los evaluados, la caída a los 30 min es del 5 al 7 % en mediana. ¿Alcanza como
  «tendencia descendente clara»?
- **Posiciones medias con la tasa 2,5 y el relleno (1; 480):** entraron por la regla de precarga; confirmar.
- **Identificabilidad:** con las seis FD-LAC no se acota ninguna cinética del lactato. Para identificarlas harían falta
  otras anclas (por ejemplo, sobres a los 30 o 90 min).
- **Demanda basal:** el registro la fija en 1,0 y el borrador de P2I-2AA preveía 0,9 / 1,1. Con ±10 % la región pasa
  de 439 291 a 274 960 o 674 108 sobrevivientes (§3). ¿Se fija en 1,0, se explora como incertidumbre o se acota con
  otra evidencia?
- **Siguen abiertas:**
  - FD-24 y FD-25;
  - la autorización del próximo dominio.
