# P2I-2AJ · Poda de la severidad de llegada por verdad del caso y paquete de observables de la FC

Este paquete funciona sólo en sombra. No hace nada de esto:
- selección latente final de la FC, ni filtrado por envolventes de FC;
- calibración de la presión, del tono vascular ni de la FR, ni activación del colapso;
- migración de GI ni de otra familia, ni integración en tiempo de ejecución;
- aprobación de ningún parámetro de FC, ni ajuste al motor heredado (no lo lee).

Código:
- `clinical_core/hr_observables.py`: la regla de verdad del caso, el soporte retenido, la reutilización, la demanda,
  la superficie, la identificabilidad, las trayectorias, el contraste de 72f, las propuestas de envolventes y el
  veredicto. Se congeló en `ac6608d`, antes de leer ninguna distribución de FC. Lo corrigió `559fa11` (una clave del
  resumen de 72f que impedía escribir el registro con las claves ordenadas), sin que se hubiera escrito ni leído ningún
  resultado.
- `clinical_core/hr_observables_report.py`: sólo este informe.

Números: `docs/revision/P2I2AJ_hr_observables.json`. Registro de partida: P2I-2AI (`805eff4e…`), ahora cerrado (su
módulo queda fijado byte a byte). El núcleo, BloodState, el gasto, el DO2, el déficit, D, el lactato y la FR no cambian.

## Resumen

- **Semántica exacta (AJ-1).**
  - 57m grave: D0 60, entrega 0,6 (0,24 reanclada), señal aguda 0,40.
  - 72f retenido: D0 20, entrega 0,85 (0,34 reanclada), señal aguda 0,15.
  - Los valores salen de dos bandas de `gi_reference` con valores literales, que citan lactato, sangrado activo, relleno
    capilar, Hb y perfusión periférica.
  - Ninguna lee un valor registrado del caso, la FC, el motor heredado ni un término de presión. Los dos pares ya estaban
    en el inventario certificado de P2I-2AI.
- **Poda por verdad del caso (AJ-2).** De los dos pares compatibles con el lactato, se rechaza el de 72f con entrega
  normalizada 1,0 (REJECTED_BY_CASE_TRUTH_COMPATIBILITY).
  - La regla lee sólo el nivel de entrega de 72f. Una prueba sube la FC registrada 50 lpm y el resultado no cambia.
  - Quedan fuera sus 25 613 sobrevivientes de lactato, sin simularlos.
- **Reutilización exacta.**
  - Las filas del par retenido se reconstruyeron con los chequeos de unidad de P2I-2AD, sólo para sus 405 puntos de
    lactato por caso.
  - Con demanda 1,0 reproducen byte a byte el digest de unidades de P2I-2AI (`06f6d5c8…`).
  - Con 0,9 y 1,1, P2I-2AI sólo guardó los conteos (0 y 1092), y coinciden. El módulo congelado no comprueba más
    (TD-96).
  - Las filas de 1,1 se recertifican con una prueba del repositorio, que repite sobre la fuente completa el filtro por
    caso, la estadística y la revisión de representantes de P2I-2AI con esa demanda:
    - las cuatro comprobaciones de la estadística dan 1092 de 1092;
    - los representantes no tienen banderas, D es coherente y la relectura es exacta;
    - el digest de unidades es `515a157e…`.
  - Todo `clinical_core` es idéntico al de `12346cb`, salvo este paquete y dos archivos que sólo cambian una tupla de
    exclusión (verificado sobre git). Fuera de `clinical_core` sólo cambiaron documentos y pruebas.
- **Demanda (AJ-3).**
  - Con 0,9 el par es CURRENTLY_INCOMPATIBLE. Superan L1 202 140 candidatos y L3 los elimina a todos; el primer fallo
    siempre es de 57m: FD-LAC-04 (95 580), L3 inadecuada (53 136), FD-LAC-05 (46 944) y adecuación perdida (6480).
  - Con 1,0 y 1,1 es CURRENTLY_COMPATIBLE: 216 y 1092 sobrevivientes.
  - En las tres demandas el primer fallo más pesado es el sobre de 57m en L1 (FD-LAC-02/03).
  - Robustos a las tres demandas: 0 (diagnóstico). Ninguna demanda se aprueba.
- **Superficie de llegada (AJ-4/5).** Las dimensiones no cambian: 450 descomposiciones y 675 candidatos conjuntos por
  demanda. Como la señal aguda es el déficit sobre la demanda, la llegada depende de la demanda y se lee en cada demanda
  compatible.
  - **Demanda 1,0:** 33 candidatos compatibles con 57m, 9 con 72f y **2 conjuntos**, los mismos de P2I-2AI: intrínseca
    100 / 100, aguda 1,46, deuda 0,0103, techo 150 o 175.
  - **Demanda 1,1:** 45, 78 y **13 conjuntos**: intrínseca 60 / 80 (7) o 100 / 100 (6), aguda 0,382–5,58, cuatro
    ganancias de deuda y los tres techos.
  - La intrínseca 80 sigue en la superficie por decisión docente, sin condiciones. Con 1,1 hay candidatos conjuntos
    con 72f en 80; en P2I-2AI no había ninguno, con ningún par.
- **Identificabilidad (AJ-6).** Hay dos observaciones de llegada y cinco latentes.
  - En la unión, las intrínsecas, la ganancia aguda y el techo quedan POORLY_IDENTIFIED. La ganancia de deuda es
    NON_IDENTIFIABLE (sólo llega como ganancia × D).
  - Con 1,0 sola, la aguda queda PARTIALLY_CONSTRAINED, encerrada entre 0,382 y 5,58. Una supervivencia estrecha en la
    grilla no se llama identificación.
- **Trayectorias (AJ-7).**
  - Se recorrieron todos los sobrevivientes por todos los candidatos: 432 lecturas por caso con 1,0 y 14 196 con 1,1.
  - Las 360 relecturas de validación son exactas, y en el minuto 0 coinciden con la llegada analítica.
  - Sin tratamiento, la FC sube de forma sostenida: mediana +22 lpm a los 120 con 1,0.
  - Con el cristaloide y demanda 1,0, la FC cae poco al terminar la infusión (medianas −2 a −3 lpm), toca su mínimo
    hacia el minuto 21–24 y rebota de +13 a +17 lpm. Con 1,1 el rango es mucho más amplio: el cambio va de +0,4 a
    −17,8 lpm, el mínimo cae entre los minutos 7 y 27 y el rebote va de 4 a 35 lpm.
  - Con los GR baja en cada unidad. Con 1,0, 57m baja −5 lpm con la unidad 1 y −11 con la unidad 2, que coincide con la
    hemostasia; 72f baja −7 y −2. Con 1,1 la unidad 1 baja de −0,6 a −31,5 lpm en 57m y de −1,9 a −30,1 en 72f.
  - La adecuación sostenida empieza en el minuto 60. A los 120, la taquicardia residual es de 0,2 a 1,5 lpm con 1,0 y de
    hasta 9,5 lpm con 1,1.
- **72f, cristaloide frente a GR (AJ-8).** Con el estado retenido, las trayectorias sí se distinguen.
  - Divergen desde el minuto 1 y superan 1 lpm hacia los minutos 9–13 con 1,0.
  - La primera entrada en cambiar es la señal aguda: con entrega 0,85 hay déficit en la llegada.
  - La mayor diferencia llega a los 120, con la FC de los GR 18–25 lpm más baja con 1,0 y 10–54 lpm más baja con 1,1.
    Ese tramo incluye la hemostasia del minuto 60 en L3, así que no es una firma específica del tratamiento.
- **Propuestas de envolventes A–G (AJ-9).** Se escribieron antes de leer las distribuciones. Ninguna se aplica ni se
  aprueba.
- **Veredicto: HR_OBSERVABLE_DECISION_PACK_READY.** Se cumplen las 8 comprobaciones.
  - La presión sigue DEFERRED, la tolerancia en ±5 lpm, y las ganancias y los techos son comunes.
  - Nada se aprobó: ni la demanda, ni el par, ni ninguna latente.

## 1. Decisiones docentes y punto de partida

<!-- generado:decisiones -->
Congelamiento: `2437e1b1c3075e180ef0fec912867974af43242a828c356190193820933fec4d` (una prueba lo fija). Registro de partida: P2I-2AI `805eff4efb562b19f1d280bdd48bbc1d458d0055f104b66f7bc7dca7ea61a861`.

| Decisión docente | Texto registrado |
|---|---|
| fecha | 2026-10-29 |
| verdad del caso (72f) | 72f's arrival state with D0 60 and normalized current delivery 1.0 is REJECTED_BY_CASE_TRUTH_COMPATIBILITY: 72f arrives with BP 98/62 (MAP about 74), CRT 4 s, a hyperdynamic LV, IVC 1.1 cm with > 50 % inspiratory collapse, active GI bleeding, lactate 3.4 and no known prehospital resuscitation restoring delivery; normalized current delivery is not compatible with that ongoing underfilled / impaired-perfusion phenotype, and accrued D0 60 does not rescue the contradiction; not rejected because of HR or of its survivor count |
| soporte retenido | 57m existing SEVERE pair with 72f D0 20 / delivery 0.85: FACULTY-CONSTRAINED CASE-COMPATIBLE ARRIVAL-SEVERITY SUPPORT for these authored cases and the current calibration; not a universal GI default, not a faculty-approved D scale, not a production migration parameter |
| demanda | simultaneous survival at demand 0.9, 1.0 and 1.1 is not required: the three values are explicit physiological uncertainty, not three states the same patient must satisfy; ROBUST_ACROSS_DEMAND stays diagnostic; demand 1.0 is not approved for being the central reference; demand values unchanged |
| intrínseca | intrinsic HR is patient-specific latent physiology: 60 / 80 / 100 per patient, explored independently, none approved, no value added; no survivor at 80 in P2I-2AI is not evidence that a resting HR of 80 is invalid, and 80 stays in the support |
| FC | common acute gain (five frozen points), common debt gain (five frozen points), common total sinus ceilings 150 / 175 / 200, pressure DEFERRED (zero in the primary calibration), arrival tolerance 57m 124 +- 5 and 72f 112 +- 5; no dimension changed |
| alcance | shadow only; no final latent HR selection, no HR-envelope filtering, no pressure / vascular-tone or RR calibration, no collapse, no GI or second-family migration, no runtime integration |
<!-- /generado:decisiones -->

## 2. Semántica exacta de los pares (P2I-2AJ-1)

<!-- generado:semantica -->
| Caso | Par (deuda / entrega) | Etiqueta | D0 | entrega | reanclada (÷2,5) | señal aguda x0 | en el inventario P2I-2AI |
|---|---|---|---|---|---|---|---|
| 57m | superior / inferior | severe: debt and low delivery | 60 | 0,60 | 0,24 | 0,40 | sí |
| 72f | medio / medio | middle | 20 | 0,85 | 0,34 | 0,15 | sí |

| Banda | Valores (inferior / medio / superior) | Variables del caso que cita | Valores literales | Lee un valor registrado |
|---|---|---|---|---|
| `arrival_oxygen_debt` | 0 / 20 / 60 (index-minutes) | active_bleeding, crt_s, lactate_mmol_l | sí | no |
| `arrival_delivery_ratio` | 0,6 / 0,85 / 1 (units of the delivery that meets the reference demand) | crt_s, hb_g_dl, peripheral_perfusion | sí | no |

| Comprobación | Resultado |
|---|---|
| en el inventario certificado de P2I-2AI | sí |
| ninguna FC en la definición | sí |
| ningún valor heredado | sí |
| ningún término de presión ni simpático | sí |
| admisible en P2I-2AI | sí |
| LACTATE_COMPATIBLE en P2I-2AI | sí |

Origen de los valores: gi_reference.case_bands: arrival_oxygen_debt and arrival_delivery_ratio only (asv.pair_values); delivery re-anchored by the extraction reserve 2.5.
<!-- /generado:semantica -->

## 3. Poda por verdad del caso (P2I-2AJ-2)

<!-- generado:verdad -->
| 57m | 72f | D0 de 72f | entrega de 72f | Estado | Motivo |
|---|---|---|---|---|---|
| superior / inferior | medio / medio | 20 | 0,85 | **RETAINED** | — |
| superior / inferior | superior / superior | 60 | 1,00 | **REJECTED_BY_CASE_TRUTH_COMPATIBILITY** | 72f normalized current delivery 1.0 at arrival contradicts its underfilled / impaired-perfusion phenotype |

Soporte retenido: 57m (superior / inferior) · 72f (medio / medio), **FACULTY_CONSTRAINED_CASE_COMPATIBLE_ARRIVAL_SEVERITY_SUPPORT**.

Regla congelada: Among P2I-2AI's LACTATE_COMPATIBLE case pairs, a pair is REJECTED_BY_CASE_TRUTH_COMPATIBILITY when 72f's arrival delivery is the top of its delivery band (1.0, normalized current delivery), whatever its arrival debt; otherwise RETAINED. The rule reads gi_reference's delivery band for 72f and the pair's level only: no HR, survivor count, tolerance, gain, ceiling, pressure or legacy value. The retained set must be exactly the faculty's pair (57m severe, 72f D0 20 / delivery 0.85), else the run stops.
<!-- /generado:verdad -->

## 4. Reutilización de las filas de D y lactato (P2I-2AJ-2)

<!-- generado:reutilizacion -->
- Par: `upper/lower|midpoint/midpoint`; registro P2I-2AI con su congelamiento `805eff4efb562b19f1d280bdd48bbc1d458d0055f104b66f7bc7dca7ea61a861`.
- Dependencias ejecutables (todo `clinical_core` salvo este paquete y los dos archivos que sólo cambian una tupla de exclusión): `a27eddf04f9b075a2093446ea7288dea423874d96823977d1e4b68005ce21e1c`, igual al de P2I-2AI (`a27eddf04f9b075a2093446ea7288dea423874d96823977d1e4b68005ce21e1c`): **sí**.
- Digest de las unidades reconstruidas con demanda 1,0: `06f6d5c82fa3047643c4073bf77614e88499575de51ef9b22aa5514bca18488b` (registrado `06f6d5c82fa3047643c4073bf77614e88499575de51ef9b22aa5514bca18488b`).
- Sobrevivientes por demanda: 0,9: 0; 1,0: 216; 1,1: 1092 (registrados 0,9: 0; 1,0: 216; 1,1: 1092).
- Reutilización válida: **sí**. Se reutilizan del registro, sin recalcular, la estadística (adequate_through_120 216, debt_coherent 216, evaluated_both 216, trigger_is_onset 216) y los representantes LOW / MID / HIGH.

Regla: P2I-2AI's record keeps the retained pair's units digest, survivors by demand and statistics, not the rows. The rows are rebuilt for the retained pair only (its 405 lactate-side bases per case, not P2I-2AI's 25 combinations) with P2I-2AD's own unit checks (lactate_closure._l1_unit, _l3_unit, _l2_unit and its Stage accounting, each case read at its own pair) and reused only when: the pair is the record's; the record is the committed one (its freeze digest); every clinical_core source the rows depend on equals P2I-2AI's certified HEAD (DEPENDENCIES_AT_P2I2AI); the units digest at demand 1.0 equals the record's and the survivors at 0.9 / 1.0 / 1.1 equal the record's. Otherwise the run stops.
<!-- /generado:reutilizacion -->

## 5. Demanda (P2I-2AJ-3)

<!-- generado:demanda -->
| Demanda | Candidatos | Sobrevivientes | Estado | Fallo dominante (primer fallo, peso) |
|---|---|---|---|---|
| 0,9 | 2225880 | 0 | **CURRENTLY_INCOMPATIBLE** | L1: FD-LAC-02/03 gi_bleed_57m (1711080) |
| 1,0 | 2225880 | 216 | **CURRENTLY_COMPATIBLE** | L1: FD-LAC-02/03 gi_bleed_57m (1734192) |
| 1,1 | 2225880 | 1092 | **CURRENTLY_COMPATIBLE** | L1: FD-LAC-02/03 gi_bleed_57m (1747728) |

Por etapa (primer fallo en el orden de P2I-2AD; dentro de cada restricción, 57m antes que 72f):

| Demanda | Etapa | Entran | Rechazados | Quedan | Primeros fallos |
|---|---|---|---|---|---|
| 0,9 | L1 | 2225880 | 2023740 | 202140 | FD-LAC-02/03 gi_bleed_57m 1711080; FD-LAC-02/03 gi_bleed_72f 312660 |
| 0,9 | L3 | 202140 | 202140 | 0 | FD-LAC-04 gi_bleed_57m 95580; FD-LAC-05 gi_bleed_57m 46944; L3_RESUSCITATION_INADEQUATE gi_bleed_57m 53136; L3_RESUSCITATION_LOST gi_bleed_57m 6480 |
| 0,9 | L2 | 0 | 0 | 0 | — |
| 1,0 | L1 | 2225880 | 1998000 | 227880 | FD-LAC-02/03 gi_bleed_57m 1734192; FD-LAC-02/03 gi_bleed_72f 263808 |
| 1,0 | L3 | 227880 | 227664 | 216 | FD-LAC-04 gi_bleed_57m 60336; FD-LAC-05 gi_bleed_57m 34560; L3_RESUSCITATION_INADEQUATE gi_bleed_57m 132768 |
| 1,0 | L2 | 216 | 0 | 216 | — |
| 1,1 | L1 | 2225880 | 1962072 | 263808 | FD-LAC-02/03 gi_bleed_57m 1747728; FD-LAC-02/03 gi_bleed_72f 214344 |
| 1,1 | L3 | 263808 | 262716 | 1092 | FD-LAC-04 gi_bleed_57m 44424; FD-LAC-05 gi_bleed_57m 15540; L3_RESUSCITATION_INADEQUATE gi_bleed_57m 197568; L3_RESUSCITATION_LOST gi_bleed_57m 5184 |
| 1,1 | L2 | 1092 | 0 | 1092 | — |

Robustos a las tres demandas: 0 (diagnóstico, nunca filtro).

Regla: Each demand factor is its own uncertainty condition. A value is CURRENTLY_COMPATIBLE when the retained pair has at least one lactate survivor there (P2I-2AD's constraints, both cases at their own pair), else CURRENTLY_INCOMPATIBLE; neither is approval. The dominant failure is the (stage, constraint, case) first failure with the largest candidate weight, read in P2I-2AD's order. ROBUST_ACROSS_DEMAND (survival at all three) is reported, never a filter. The HR surface and the trajectories are read at every CURRENTLY_COMPATIBLE value.
<!-- /generado:demanda -->

## 6. Superficie de llegada de la FC (P2I-2AJ-4, -5)

<!-- generado:superficie -->
**Demanda 1,0.** Descomposiciones: 450; candidatos conjuntos: 675; compatibles con 57m: 33 (descomposiciones 11); con 72f: 9 (descomposiciones 3); **conjuntamente compatibles: 2** (2 pares de FC predicha distintos).

| intrínseca 57m \ 72f | inferior (60) | medio (80) | superior (100) |
|---|---|---|---|
| inferior | 0 | 0 | 0 |
| medio | 0 | 0 | 0 |
| superior | 0 | 0 | 2 |

| Dimensión | Apoyo por valor |
|---|---|
| ganancia aguda | 0,1: 0; 0,382: 0; 1,46: 2; 5,58: 0; 21,3: 0 |
| ganancia de deuda | 0,000667: 0; 0,00262: 0; 0,0103: 2; 0,0407: 0; 0,16: 0 |
| techo | 150: 1; 175: 1; 200: 0 |

| Intrínsecas 57m / 72f | Ganancia aguda | Ganancia de deuda | Techo | FC predicha 57m / 72f |
|---|---|---|---|---|
| superior / superior | 1,46 | 0,0103 | 150 | 126,9 / 110,5 |
| superior / superior | 1,46 | 0,0103 | 175 | 128,6 / 110,6 |

**Demanda 1,1.** Descomposiciones: 450; candidatos conjuntos: 675; compatibles con 57m: 45 (descomposiciones 15); con 72f: 78 (descomposiciones 26); **conjuntamente compatibles: 13** (13 pares de FC predicha distintos).

| intrínseca 57m \ 72f | inferior (60) | medio (80) | superior (100) |
|---|---|---|---|
| inferior | 0 | 7 | 0 |
| medio | 0 | 0 | 0 |
| superior | 0 | 0 | 6 |

| Dimensión | Apoyo por valor |
|---|---|
| ganancia aguda | 0,1: 0; 0,382: 2; 1,46: 6; 5,58: 5; 21,3: 0 |
| ganancia de deuda | 0,000667: 1; 0,00262: 5; 0,0103: 5; 0,0407: 2; 0,16: 0 |
| techo | 150: 4; 175: 5; 200: 4 |

| Intrínsecas 57m / 72f | Ganancia aguda | Ganancia de deuda | Techo | FC predicha 57m / 72f |
|---|---|---|---|---|
| inferior / medio | 1,46 | 0,0407 | 150 | 122,8 / 107,1 |
| inferior / medio | 1,46 | 0,0407 | 175 | 127,6 / 107,8 |
| inferior / medio | 5,58 | 0,000667 | 200 | 120,3 / 111,3 |
| inferior / medio | 5,58 | 0,00262 | 175 | 120,6 / 111,8 |
| inferior / medio | 5,58 | 0,00262 | 200 | 122,6 / 112,2 |
| inferior / medio | 5,58 | 0,0103 | 150 | 123,5 / 113,8 |
| inferior / medio | 5,58 | 0,0103 | 175 | 128,5 / 115,1 |
| superior / superior | 0,382 | 0,0103 | 175 | 119,4 / 107,3 |
| superior / superior | 0,382 | 0,0103 | 200 | 119,6 / 107,3 |
| superior / superior | 1,46 | 0,00262 | 150 | 119,5 / 109,5 |
| superior / superior | 1,46 | 0,00262 | 175 | 120,0 / 109,6 |
| superior / superior | 1,46 | 0,00262 | 200 | 120,3 / 109,6 |
| superior / superior | 1,46 | 0,0103 | 150 | 128,3 / 113,2 |

Regla: The retained pair only, at each CURRENTLY_COMPATIBLE demand: arrival HR analytic (derived.heart_rate_decomposition, P2I-2AG's primary profile, pressure 0), 57m intrinsic 60 / 80 / 100 x 72f intrinsic 60 / 80 / 100 x the five common acute gains x the five common debt gains x the common ceilings 150 / 175 / 200. JOINT when |HR57 - 124| <= 5 and |HR72 - 112| <= 5. At demand 1.0 the joint set must equal P2I-2AI's retained-pair survivors (else stop). No dimension changed, no best candidate.
<!-- /generado:superficie -->

## 7. Identificabilidad latente (P2I-2AJ-6)

<!-- generado:identificabilidad -->
| Latente | demanda 1,0 | demanda 1,1 | unión |
|---|---|---|---|
| intrínseca 57m | **POORLY_IDENTIFIED** (superior) | **POORLY_IDENTIFIED** (inferior, superior) | **POORLY_IDENTIFIED** (inferior, superior) |
| intrínseca 72f | **POORLY_IDENTIFIED** (superior) | **POORLY_IDENTIFIED** (medio, superior) | **POORLY_IDENTIFIED** (medio, superior) |
| ganancia aguda | **PARTIALLY_CONSTRAINED** (1,46) | **POORLY_IDENTIFIED** (0,382, 1,46, 5,58) | **POORLY_IDENTIFIED** (0,382, 1,46, 5,58) |
| ganancia de deuda | **NON_IDENTIFIABLE** (0,0103) | **NON_IDENTIFIABLE** (0,000667, 0,00262, 0,0103, 0,0407) | **NON_IDENTIFIABLE** (0,000667, 0,00262, 0,0103, 0,0407) |
| techo sinusal total | **POORLY_IDENTIFIED** (150, 175) | **POORLY_IDENTIFIED** (150, 175, 200) | **POORLY_IDENTIFIED** (150, 175, 200) |

Observaciones: 57m authored arrival HR, 72f authored arrival HR. Estructural: only debt_to_sympathetic_gain x D reaches HR and the D scale is not approved (P2I-2AG: the D scale and the debt gain are one observable).

Regla: Per latent, over the joint survivors: NON_IDENTIFIABLE when the observable reaches it only through a product with an unapproved latent (STRUCTURAL); POORLY_IDENTIFIED when two or more grid values survive or the one surviving value is an edge of the explored support (unbounded on that side); PARTIALLY_CONSTRAINED when one interior value survives, bracketed by rejected neighbours, but the observations (two arrival HRs) are fewer than the latents (five), so the bracket is a grid artefact on a continuum of solutions; WELL_CONSTRAINED only when one interior value survives and the observations are at least as many as the latents. NOT_EVALUABLE without survivors. A narrow grid survivor set is never called identification; the arrival observables (acute, debt and total sympathetic increments, reserve utilization, predicted HR) are reported apart.
<!-- /generado:identificabilidad -->

## 8. Observables de llegada (P2I-2AJ-6)

<!-- generado:observables -->
Mínimo – máximo sobre los candidatos conjuntos de cada demanda.

| Observable de llegada | 57m, demanda 1,0 | 72f, demanda 1,0 | 57m, demanda 1,1 | 72f, demanda 1,1 |
|---|---|---|---|---|
| intrínseca (lpm) | 100,00 – 100,00 | 100,00 – 100,00 | 60,00 – 100,00 | 80,00 – 100,00 |
| señal aguda x0 | 0,40 – 0,40 | 0,15 – 0,15 | 0,45 – 0,45 | 0,23 – 0,23 |
| D0 | 60,00 – 60,00 | 20,00 – 20,00 | 60,00 – 60,00 | 20,00 – 20,00 |
| incremento agudo (lpm) | 13,07 – 13,87 | 5,40 – 5,44 | 4,25 – 59,33 | 2,16 – 31,00 |
| incremento por deuda (lpm) | 13,86 – 14,71 | 5,09 – 5,13 | 0,93 – 53,17 | 0,33 – 19,74 |
| incremento simpático total (lpm) | 26,93 – 28,59 | 10,49 – 10,57 | 19,39 – 68,52 | 7,31 – 35,15 |
| uso de la reserva | 0,38 – 0,54 | 0,14 – 0,21 | 0,20 – 0,71 | 0,07 – 0,48 |
| FC de llegada predicha | 126,93 – 128,59 | 110,49 – 110,57 | 119,39 – 128,52 | 107,14 – 115,15 |
<!-- /generado:observables -->

## 9. Validación de las trayectorias

<!-- generado:validacion -->
| Demanda | Corridas completas | Comprobaciones | Exacta |
|---|---|---|---|
| 1,0 | 90 | arrival sí, hr sí, hr_shock sí, lactate_closure sí | **sí** |
| 1,1 | 270 | arrival sí, hr sí, lactate_closure sí | **sí** |

Regla: At each CURRENTLY_COMPATIBLE demand with joint arrival survivors: every lactate survivor of the retained pair (P3 set, crystalloid point, its 57m and 72f lactate-side points) is run by the full core at that demand, each case with its own pair (L1 and L3 once per P3 set and point, L2 once per crystalloid point), and the primary HR (pressure 0) is post-processed for every joint survivor (hr_primary.primary_series, the core's arithmetic). Readings H1-H4 and H6 per (lactate survivor, joint survivor, case); distributions LOW / median / HIGH, also by the case's intrinsic level. Validated before any reading: on the first, middle and last lactate survivor, every joint survivor, case and scenario is re-run by the full core with its HR profile (exact HR, minute 0 equal to the analytic arrival), and the demand-aware run equals lactate_closure.full_run (lactate, D) and, at demand 1.0, hr_shock.full_run (every row); else the run stops. No trajectory filter, no envelope applied, no candidate selected.
<!-- /generado:validacion -->

## 10. Trayectorias H1–H4 y H6 (P2I-2AJ-7)

<!-- generado:trayectorias -->
Cada celda: LOW / mediana / HIGH sobre (sobreviviente de lactato × candidato conjunto), en lpm salvo indicación. Sin envolvente ni filtro.

**Demanda 1,0** — 216 sobrevivientes de lactato × 2 candidatos conjuntos = 432 lecturas por caso.

| Lectura | 57m | 72f |
|---|---|---|
| H1 sin tratamiento: FC a los 30 | 132,5 / 134,3 / 136,4 | 114,8 / 115,6 / 115,9 |
| H1: FC a los 60 | 137,3 / 140,4 / 144,1 | 119,6 / 121,4 / 122,3 |
| H1: FC a los 120 | 144,2 / 150,1 / 157,6 | 129,5 / 133,3 / 136,8 |
| H1: cambio desde la llegada a los 30 | 5,6 / 6,6 / 7,8 | 4,3 / 5,1 / 5,4 |
| H1: cambio a los 60 | 10,4 / 12,7 / 15,5 | 9,1 / 10,9 / 11,7 |
| H1: cambio a los 120 | 17,3 / 22,4 / 29,0 | 19,0 / 22,8 / 26,3 |
| H1: FC máxima | 144,2 / 150,1 / 157,6 | 129,5 / 133,3 / 136,8 |
| H2 cristaloide: cambio al terminar la infusión (min 20) | -2,6 / -1,9 / -1,0 | -3,8 / -2,9 / -2,2 |
| H2: FC mínima | 124,6 / 125,9 / 127,4 | 106,3 / 107,5 / 108,2 |
| H2: minuto de la FC mínima | 20 / 21 / 22 | 23 / 24 / 26 |
| H2: FC a los 60 | 130,0 / 132,4 / 136,0 | 109,2 / 110,9 / 113,2 |
| H2: FC a los 120 | 138,7 / 143,2 / 149,9 | 117,8 / 120,4 / 125,6 |
| H2: rebote (FC a los 120 menos la mínima) | 13,6 / 17,4 / 23,1 | 10,9 / 13,1 / 17,8 |
| H3 GR: FC antes de la unidad 1 | 126,9 / 127,8 / 128,6 | 110,5 / 110,5 / 110,6 |
| H3: FC tras la unidad 1 | 121,8 / 122,4 / 123,1 | 103,7 / 103,8 / 103,8 |
| H3: cambio con la unidad 1 | -6,0 / -5,3 / -4,7 | -6,9 / -6,8 / -6,7 |
| H3: FC tras la unidad 2 | 110,7 / 110,9 / 111,2 | 101,3 / 101,4 / 101,4 |
| H3: cambio adicional con la unidad 2 | -12,0 / -11,4 / -10,8 | -2,4 / -2,4 / -2,3 |
| H3: minuto en que termina la unidad 1 | 30 / 30 / 30 | 30 / 30 / 30 |
| H3: minuto en que termina la unidad 2 | 60 / 60 / 60 | 60 / 60 / 60 |
| H4 manejo definitivo: FC a los 60 | 110,7 / 110,9 / 111,2 | 101,3 / 101,4 / 101,4 |
| H4: FC a los 90 | 103,9 / 104,0 / 104,1 | 100,5 / 100,5 / 100,5 |
| H4: FC a los 120 | 101,4 / 101,5 / 101,5 | 100,2 / 100,2 / 100,2 |
| H4: minuto de adecuación sostenida | 60 / 60 / 60 | 60 / 60 / 60 |
| H4: cambio tras la adecuación | -9,8 / -9,5 / -9,3 | -1,2 / -1,2 / -1,1 |
| H4: taquicardia residual sobre la intrínseca a los 120 | 1,4 / 1,5 / 1,5 | 0,2 / 0,2 / 0,2 |
| H6: FC máxima (L1, L2, L3) | 144,2 / 150,1 / 157,6 | 129,5 / 133,3 / 136,8 |
| H6: techo | 150,0 / 162,5 / 175,0 | 150,0 / 162,5 / 175,0 |
| H6: distancia al techo | 4,5 / 11,6 / 20,2 | 16,6 / 29,3 / 43,3 |
| H6: uso de la reserva (máxima − intrínseca) / (techo − intrínseca) | 0,73 / 0,83 / 0,91 | 0,42 / 0,54 / 0,67 |

**Demanda 1,1** — 1092 sobrevivientes de lactato × 13 candidatos conjuntos = 14196 lecturas por caso.

| Lectura | 57m | 72f |
|---|---|---|
| H1 sin tratamiento: FC a los 30 | 121,4 / 127,6 / 135,7 | 108,8 / 113,8 / 123,7 |
| H1: FC a los 60 | 123,2 / 131,8 / 142,2 | 110,5 / 118,9 / 131,9 |
| H1: FC a los 120 | 126,9 / 139,1 / 153,1 | 114,4 / 129,8 / 146,2 |
| H1: cambio desde la llegada a los 30 | 1,9 / 4,7 / 7,9 | 1,5 / 5,3 / 8,6 |
| H1: cambio a los 60 | 3,8 / 9,0 / 15,6 | 3,2 / 10,6 / 17,2 |
| H1: cambio a los 120 | 7,5 / 16,0 / 29,4 | 7,1 / 19,9 / 33,2 |
| H1: FC máxima | 126,9 / 139,1 / 153,1 | 114,4 / 129,8 / 146,2 |
| H2 cristaloide: cambio al terminar la infusión (min 20) | -17,8 / -4,0 / 0,4 | -16,8 / -3,4 / -0,1 |
| H2: FC mínima | 100,3 / 116,1 / 127,6 | 92,7 / 105,4 / 111,5 |
| H2: minuto de la FC mínima | 7 / 25 / 27 | 19 / 25 / 27 |
| H2: FC a los 60 | 107,9 / 120,5 / 135,5 | 100,4 / 108,7 / 117,6 |
| H2: FC a los 120 | 121,8 / 128,8 / 146,7 | 110,5 / 119,3 / 134,7 |
| H2: rebote (FC a los 120 menos la mínima) | 5,8 / 12,6 / 33,3 | 4,0 / 14,0 / 34,7 |
| H3 GR: FC antes de la unidad 1 | 119,4 / 120,6 / 128,5 | 107,1 / 109,6 / 115,1 |
| H3: FC tras la unidad 1 | 88,7 / 112,3 / 126,1 | 81,3 / 100,0 / 105,9 |
| H3: cambio con la unidad 1 | -31,5 / -7,6 / -0,6 | -30,1 / -8,1 / -1,9 |
| H3: FC tras la unidad 2 | 61,2 / 104,2 / 120,2 | 80,1 / 87,6 / 102,1 |
| H3: cambio adicional con la unidad 2 | -31,9 / -8,4 / -2,0 | -12,9 / -3,1 / -1,0 |
| H3: minuto en que termina la unidad 1 | 30 / 30 / 30 | 30 / 30 / 30 |
| H3: minuto en que termina la unidad 2 | 60 / 60 / 60 | 60 / 60 / 60 |
| H4 manejo definitivo: FC a los 60 | 61,2 / 104,2 / 120,2 | 80,1 / 87,6 / 102,1 |
| H4: FC a los 90 | 60,3 / 84,8 / 106,7 | 80,0 / 82,8 / 100,8 |
| H4: FC a los 120 | 60,1 / 69,1 / 102,4 | 80,0 / 81,0 / 100,3 |
| H4: minuto de adecuación sostenida | 60 / 60 / 60 | 60 / 60 / 60 |
| H4: cambio tras la adecuación | -50,7 / -11,6 / -1,1 | -7,1 / -1,5 / -0,1 |
| H4: taquicardia residual sobre la intrínseca a los 120 | 0,1 / 1,8 / 9,5 | 0,0 / 0,2 / 1,1 |
| H6: FC máxima (L1, L2, L3) | 126,9 / 139,1 / 153,1 | 114,4 / 129,8 / 146,2 |
| H6: techo | 150,0 / 175,0 / 200,0 | 150,0 / 175,0 / 200,0 |
| H6: distancia al techo | 9,6 / 30,1 / 70,8 | 12,3 / 41,4 / 85,5 |
| H6: uso de la reserva (máxima − intrínseca) / (techo − intrínseca) | 0,29 / 0,65 / 0,89 | 0,14 / 0,53 / 0,82 |
<!-- /generado:trayectorias -->

## 11. 72f: cristaloide frente a GR (P2I-2AJ-8)

<!-- generado:fluido -->
| Lectura (72f, L2 cristaloide frente a L3 GR) | demanda 1,0 | demanda 1,1 |
|---|---|---|
| primer minuto con FC distinta | 1 / 1 / 1 | 1 / 1 / 1 |
| primer minuto con más de 1 lpm | 9 / 11 / 13 | 5 / 12 / 28 |
| mayor diferencia (lpm) | 17,6 / 20,2 / 25,4 | 10,2 / 38,2 / 54,4 |
| minuto de la mayor diferencia | 120 / 120 / 120 | 120 / 120 / 120 |
| GR − cristaloide en ese minuto (lpm) | -25,4 / -20,2 / -17,6 | -54,4 / -38,2 / -10,2 |
| primer minuto con señal aguda distinta | 1 / 1 / 1 | 1 / 1 / 1 |
| primer minuto con D distinta | 2 / 2 / 2 | 2 / 2 / 2 |
| pares sin ninguna divergencia | 0 | 0 |
| primera entrada que diverge (aguda / deuda / ninguna) | 432 / 0 / 0 | 14196 / 0 / 0 |

Regla: 72f only, diagnostic (no requirement that HR distinguish the treatments): for every 72f lactate survivor and joint survivor, L2 (2 L crystalloid over 20 min, bleeding continues) against L3 (2 PRBC units over 60 min with PPI from minute 0 and endoscopic haemostasis at 60) on the same P3 set and lactate-side point: the first minute the HRs differ at all and by more than 1 bpm, the largest difference and its minute, and which HR input diverges first (the acute signal, deficit over demand, or D). The scenarios differ in more than the fluid (PPI, haemostasis).
<!-- /generado:fluido -->

## 12. Propuestas de envolventes para la docencia (P2I-2AJ-9)

<!-- generado:envolventes -->
| | Magnitud | Propuesta (no aplicada) | Base | Interpretación |
|---|---|---|---|---|
| A | untreated 57m HR at 120 min (H1) | at or above the arrival HR (untreated ongoing haemorrhage does not relieve tachycardia) and below the age-predicted maximum (about 220 - 57 = 163 bpm) | PHYSIOLOGICAL | progressive compensation while bleeding continues untreated |
| B | untreated 72f HR at 120 min (H1) | at or above the arrival HR and below the age-predicted maximum (about 220 - 72 = 148 bpm) | PHYSIOLOGICAL | progressive compensation while bleeding continues untreated, in an older patient |
| C | HR change over the first PRBC unit (H3, both cases) | a fall or no rise (<= 0 bpm) while the unit restores delivery; magnitude open | PHYSIOLOGICAL (direction) / EXPLORATION (magnitude) | delivery restored by red cells lowers the acute signal before haemostasis |
| D | additional HR change over the second PRBC unit (H3, both cases) | a fall or no rise (<= 0 bpm); no requirement on its size relative to the first unit (endoscopic haemostasis lands at minute 60, when the second unit completes) | PHYSIOLOGICAL (direction) / EXPLORATION (magnitude) | continued restoration; the second interval also carries PPI and approaching haemostasis |
| E | HR at 120 min after successful definitive management (H4, both cases) | within intrinsic + 15 bpm | EXPLORATION | tachycardia largely resolved once delivery is adequate and bleeding controlled |
| F | residual tachycardia above intrinsic at 120 min (H4, both cases) | 0 to 15 bpm (some debt repayment may persist) | EXPLORATION | the debt drive repays after adequacy; a small residual is plausible, a large one is not |
| G | maximum sinus HR and the ceiling candidates 150 / 175 / 200 (H6) | a common total ceiling far above both age-predicted maxima (about 163 for 57m and 148 for 72f by 220 - age) is physiologically implausible: drop 200, keep 150 and 175 for the faculty | PHYSIOLOGICAL (general physiology, not repository truth) | ceilings bound the saturated sinus response; the arrival does not identify them |

Resultado actual (LOW / mediana / HIGH, lpm), por demanda y por la intrínseca del caso:

| | Caso | Demanda | Todos | Intrínseca 60 | Intrínseca 80 | Intrínseca 100 |
|---|---|---|---|---|---|---|
| A | 57m | 1,0 | 144,2 / 150,1 / 157,6 | — | — | 144,2 / 150,1 / 157,6 |
| A | 57m | 1,1 | 126,9 / 139,1 / 153,1 | 137,2 / 145,1 / 153,1 | — | 126,9 / 130,8 / 139,2 |
| B | 72f | 1,0 | 129,5 / 133,3 / 136,8 | — | — | 129,5 / 133,3 / 136,8 |
| B | 72f | 1,1 | 114,4 / 129,8 / 146,2 | — | 127,0 / 137,0 / 146,2 | 114,4 / 117,8 / 126,7 |
| C | 57m | 1,0 | -6,0 / -5,3 / -4,7 | — | — | -6,0 / -5,3 / -4,7 |
| C | 72f | 1,0 | -6,9 / -6,8 / -6,7 | — | — | -6,9 / -6,8 / -6,7 |
| C | 57m | 1,1 | -31,5 / -7,6 / -0,6 | -31,5 / -22,8 / -1,2 | — | -8,7 / -6,1 / -0,6 |
| C | 72f | 1,1 | -30,1 / -8,1 / -1,9 | — | -30,1 / -28,6 / -6,3 | -8,3 / -7,8 / -1,9 |
| D | 57m | 1,0 | -12,0 / -11,4 / -10,8 | — | — | -12,0 / -11,4 / -10,8 |
| D | 72f | 1,0 | -2,4 / -2,4 / -2,3 | — | — | -2,4 / -2,4 / -2,3 |
| D | 57m | 1,1 | -31,9 / -8,4 / -2,0 | -31,9 / -28,2 / -4,6 | — | -9,9 / -7,9 / -2,0 |
| D | 72f | 1,1 | -12,9 / -3,1 / -1,0 | — | -12,9 / -4,2 / -1,2 | -3,8 / -2,2 / -1,0 |
| E | 57m | 1,0 | 101,4 / 101,5 / 101,5 | — | — | 101,4 / 101,5 / 101,5 |
| E | 72f | 1,0 | 100,2 / 100,2 / 100,2 | — | — | 100,2 / 100,2 / 100,2 |
| E | 57m | 1,1 | 60,1 / 69,1 / 102,4 | 60,1 / 62,0 / 69,5 | — | 100,4 / 101,2 / 102,4 |
| E | 72f | 1,1 | 80,0 / 81,0 / 100,3 | — | 80,0 / 80,2 / 81,1 | 100,1 / 100,1 / 100,3 |
| F | 57m | 1,0 | 1,4 / 1,5 / 1,5 | — | — | 1,4 / 1,5 / 1,5 |
| F | 72f | 1,0 | 0,2 / 0,2 / 0,2 | — | — | 0,2 / 0,2 / 0,2 |
| F | 57m | 1,1 | 0,1 / 1,8 / 9,5 | 0,1 / 2,0 / 9,5 | — | 0,4 / 1,2 / 2,4 |
| F | 72f | 1,1 | 0,0 / 0,2 / 1,1 | — | 0,0 / 0,2 / 1,1 | 0,1 / 0,1 / 0,3 |
| G | 57m | 1,0 | 144,2 / 150,1 / 157,6 | — | — | 144,2 / 150,1 / 157,6 |
| G | 72f | 1,0 | 129,5 / 133,3 / 136,8 | — | — | 129,5 / 133,3 / 136,8 |
| G | 57m | 1,1 | 126,9 / 139,1 / 153,1 | 137,2 / 145,1 / 153,1 | — | 126,9 / 130,8 / 139,2 |
| G | 72f | 1,1 | 114,4 / 129,8 / 146,2 | — | 127,0 / 137,0 / 146,2 | 114,4 / 117,8 / 126,7 |

Regla: Each proposal is shown with the current survivors' LOW / median / HIGH, by the case's intrinsic level and by demand; nothing is filtered, no pass count is computed and no proposal is approved by the faculty here.
<!-- /generado:envolventes -->

## 13. Presión, intrínseca, ganancias y tolerancia (P2I-2AJ-10, -11)

- **Presión:** sigue `PRESSURE_TERM_DIAGNOSTIC_ONLY`. El perfil primario y todas las relecturas de validación ponen
  su ganancia en 0, y no interviene en la aceptación, en la llegada ni en las envolventes.
- **Intrínseca:** 60 / 80 / 100 por paciente, las tres exploradas por caso. Ninguna se aprueba ni se quita.
- **Ganancias:** una terna (aguda, deuda, techo) por candidato, común a los dos casos.
- **Tolerancia:** ±5 lpm, sin cambios (57m 119–129, 72f 107–117).
- **Parámetros ocultos:** ninguno se aprueba.
- **No regresión:**
  - El núcleo no cambia: no se tocó `clinical_core` fuera de este análisis y de dos tuplas de exclusión.
  - Las filas de D y lactato del par retenido reproducen las de P2I-2AI byte a byte con demanda 1,0. Con 1,1 las
    recertifica la prueba descrita arriba.
  - En los tres sobrevivientes de validación de cada demanda (primero, central y último), las corridas por demanda
    igualan a `lactate_closure.full_run` en lactato y D. Con demanda 1,0 igualan además a `hr_shock.full_run` fila por
    fila: BloodState, gasto, DO2, déficit, D, lactato y FR. La revisión adversarial repitió las lecturas con 1,1 en
    otras 8 combinaciones con corridas completas independientes, sin diferencias.
  - La certificación final repite el golden directo y Contracts v2.

## 14. Veredicto (P2I-2AJ-12)

<!-- generado:veredicto -->
**HR_OBSERVABLE_DECISION_PACK_READY**

| Comprobación | Resultado |
|---|---|
| el par retenido es compatible con la verdad del caso | sí |
| sus filas de D y lactato siguen certificadas (reutilización exacta) | sí |
| al menos un candidato conjunto compatible con la llegada | sí |
| ganancias y techo comunes | sí |
| intrínseca por paciente, sin aprobar (tres niveles por caso) | sí |
| presión aplazada | sí |
| sin regresión de D y lactato | sí |
| distribuciones de trayectoria disponibles y validadas | sí |

Aprobado: no.

Regla congelada: HR_OBSERVABLE_DECISION_PACK_READY when: (1) the retained case pair is independently case-truth compatible (the case-truth rule retains exactly the faculty's pair, and its values come from the case bands with no HR, legacy or pressure term, present in P2I-2AI's inventory); (2) its D / lactate rows remain certified (REUSE_RULE); (3) at least one joint arrival-compatible HR candidate remains at a CURRENTLY_COMPATIBLE demand (else HR_SURFACE_BLOCKED_AFTER_CASE_TRUTH_PRUNING); (4) the sympathetic gains and ceiling are common (one triple per candidate, applied to both cases); (5) the intrinsic rate is patient-specific candidate uncertainty (all three levels explored per case, none approved); (6) the pressure contribution is 0 in the primary profile and in every validation rerun; (7) no D / lactate regression (the rows reproduce P2I-2AI's and the demand-aware runs equal lactate_closure.full_run; RR by the final certification); (8) trajectory distributions are available and validated. Otherwise HR_OBSERVABLE_DECISION_PACK_NOT_READY with the first blocker. Nothing is approved.
<!-- /generado:veredicto -->

## 15. Decisiones que necesita la docencia

La docencia confirma o reemplaza cada una. Ninguna la toma el análisis.

1. **La demanda en el filtrado de la FC.** Las demandas 1,0 y 1,1 son compatibles hoy y llevan a superficies de FC
   distintas: 2 candidatos frente a 13, con intrínsecas distintas. Hay que decidir cómo entra esa incertidumbre en el
   paquete de filtrado: si las dos demandas siguen como condiciones separadas (lo que hace este paquete) o si una sale
   por razones clínicas, nunca por la FC.
2. **Envolvente A (57m sin tratamiento, FC a los 120):** ¿se acepta «≥ FC de llegada y < 163 (220 − edad)»? Hoy va de
   127 a 158.
3. **Envolvente B (72f sin tratamiento, FC a los 120):** ¿se acepta «≥ FC de llegada y < 148»? Hoy va de 114 a 146, y
   el máximo (intrínseca 80, demanda 1,1) queda a 2 lpm del límite propuesto.
4. **Envolventes C y D (GR antes de la hemostasia):** ¿sólo la dirección (≤ 0 lpm por unidad) o también una magnitud?
   Con intrínseca 60 y demanda 1,1, la unidad 1 baja la FC de 57m hasta 31 lpm.
5. **Envolventes E y F (FC a los 120 tras el manejo definitivo y taquicardia residual):** ¿es aceptable que la FC vuelva
   casi a la intrínseca 60 minutos después de la hemostasia? 57m queda entre 60 y 70 lpm (mediana 62) con intrínseca 60, con caídas de
   hasta 51 lpm después de la adecuación, y la taquicardia residual llega a 9,5 lpm.
6. **Envolvente G (techos):** los datos no distinguen 150, 175 y 200. La propuesta fisiológica es quitar 200, que supera
   en más de 35 lpm el máximo previsto para la edad de los dos pacientes.

Sigue detenido hasta una decisión expresa: la selección latente, el filtrado por envolventes, la presión, la FR, el
colapso, la migración y la integración.

## 16. Eficiencia

<!-- generado:eficiencia -->
Rechazos por verdad del caso: 1 par de casos (25613 sobrevivientes de lactato que no se simulan); trayectorias hemodinámicas: 3178; puntos de lactato por caso: 405 de 2025; descomposiciones de llegada analíticas: 900; corridas de validación: 360; corridas de trayectoria: demanda 1,0: 504 (sin compartir L1 y L3: 1296); demanda 1,1: 2548 (sin compartir L1 y L3: 6552); lecturas de FC posprocesadas: 29256; barrido cartesiano: no; motor heredado leído: no.
<!-- /generado:eficiencia -->
