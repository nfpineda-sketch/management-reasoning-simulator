# P2N-2 · Migración en sombra del caso cardiogénico acs_70f_left_main

**Rama:** `phase-2-clinical-core-shadow` · **Base:** `6601fc7` (P2M-2 cerrado, certificación trasladada por equivalencia) · **Congelamiento:** `ab248db` (digest `e7ff21e5…`) · **Fecha:** 2026-11-03

Sólo sombra. El mapeo de llegada del caso (`clinical_core/acs_reference.py`) y sus escritores de familia (`clinical_core/modules/acs_ischaemia.py`) corren sobre el núcleo común certificado sin cambios; la evaluación es `clinical_core/acs_migration.py`. Ningún valor común se aprueba, el legado no es objetivo, el colapso sólo se lee y nada llega al tiempo de ejecución. Las secciones generadas salen del registro `docs/revision/P2N2_acs_migration.json` (`acs_migration_report`).

## Resumen

**Veredicto: `CARDIOGENIC_SHADOW_MIGRATION_READY`.** Recomendación, por la regla predeclarada:
`IMPLEMENT_EXPECTED_RESPIRATORY_EXTENSION`.

`acs_70f_left_main` corre sobre el núcleo común certificado sin cambiar ningún archivo común y sin reajustar GI.

- **La llegada autorizada es representable:**
  - PA 104/66, PAM 78,7, SpO2 94, lactato 3,1, alerta;
  - FR 25,5 frente a 26;
  - gases 7,39 / 30,8 frente a 7,36 / 33 autorizados (con la ventilación candidata de P2K-3, sin ajustar).
- **La falla de bomba entra por P:**
  - P es relativo a la llegada;
  - la disfunción ventricular de llegada queda en la capa de llegada (reserva de bomba y razón de aporte), sin contarse
    dos veces.
- **La isquemia sólo escribe P y la congestión sólo L.** En los tres puntos de la región predeclarada, Q, PAM, aporte,
  déficit, D, FC y tono responden por la fisiología común; el lactato es siempre el del núcleo.
- **La D de llegada no depende del lactato**, y una prueba permanente lo fija.
- **La reperfusión detiene la pérdida de P y deja recuperar una fracción declarada.** Lo demás sigue por la fisiología
  común.
- **Contrafactual de fluidos:** el volumen da mucho menos en la bomba débil (+0,05 de gasto) que en el déficit de
  precarga (+0,26), y no normaliza la falla de bomba.
- **El colapso sólo se lee:** máximo de las dos señales, cota inferior con el mapeo de PAM UNSET y ninguna regla
  cardiogénica. Nunca actúa.
- **El legado se compara al final y no elige nada.** Su caída de SpO2 y su FV a los 120 min son extensiones esperadas:
  la respiratoria, y el evento de familia diferido.
- **La extensión respiratoria es la brecha que queda:** L sube bajo isquemia, pero SpO2 y G no se mueven, porque la
  fisiología común no tiene camino de L al intercambio gaseoso.

## 1. Decisiones de la docencia

<!-- generado:decisiones -->
Decisiones de la docencia (texto congelado, en inglés):

- **arrival_d**: a latent arrival-state variable; no lactate -> D rule
- **authorized**: arrival mapping; ischaemic pump writer; reperfusion writer; congestion / L writer; observation layer; case intrinsic sinus rate; family arrival latent mapping
- **hr**: the common HR physiology only (intrinsic rate as a case mapping); no ACS sympathetic gain or HR residual
- **not_authorized**: common-core retuning; GI changes; runtime; collapse activation or thresholds; ROSC / ACLS; NIV; common L -> G / SpO2; pressure -> tone baroreflex; P-dependent afterload; full ACS rollout; a third family
- **objective**: acs_70f_left_main through the existing common physiology without retuning the GI core; shadow only
- **p2n1**: GENERALIZES_WITH_NEW_FAMILY_WRITERS_ONLY; PROCEED_TO_CARDIOGENIC_SHADOW_MIGRATION
- **pump**: the common P channel; no second pump equation; LV impairment kept through the arrival layer
- **baroreflex_to_tone** (diferido): BAROREFLEX_TO_TONE_COMMON_REFINEMENT_DEFERRED
- **collapse_m1** (diferido): REQUIRED_BEFORE_ACTIVE_FAMILY_COLLAPSE
- **collapse_m2** (diferido): REQUIRED_BEFORE_RUNTIME_TRACE_INTEGRATION
- **legacy_vf_120** (diferido): LEGACY_FAMILY_EVENT_DEFERRED
- **p_afterload** (diferido): P_DEPENDENT_AFTERLOAD_REFINEMENT_DEFERRED
- **respiratory** (diferido): EXPECTED_RESPIRATORY_FAMILY_EXTENSION (L -> gas exchange, oxygenation, congestion drive, NIV)
<!-- /generado:decisiones -->

## 2. Verdad del repositorio

<!-- generado:verdad -->
- **Caso:** `acs_70f_left_main`, leído del banco de casos (`clinical_cases.py`), por ruta.
- **Signos:** PA 104/66 (PAM 78,7), FC 112 (Sinus tachycardia), SpO2 94 % aire ambiente, FR 26, trabajo respiratorio «Mildly increased», llenado capilar 3 s, extremidades «Cool», «Alert».
- **Laboratorio:** lactato 3,1, Hb 12,2, glucosa 168, K 4,1, creatinina 1,6; gases arteriales 7.36 / 33 / 72, HCO3 18,0 (el repositorio; no 18,4); troponina 260.
- **ECG y POCUS:** `diffuse_st_depression_avr`; VI «Globally mildly reduced contraction without a single focal defect»; VCI «1.9 cm; about 50% inspiratory collapse»; pulmones «Scattered B-lines at both bases; no diffuse B-line pattern»; radiografía «Mild pulmonary congestion without focal consolidation.».
- **Coronaria:** {"active_occlusion": true, "omi": true, "pci_capable": true, "rv_involvement": false, "symptom_onset_min": 60, "territory": "left_main"}; acciones esperadas aspirin, consult, reperfusion_referral.
<!-- /generado:verdad -->

## 3. Mapeo de llegada

<!-- generado:mapeo -->
| Campo | Clase |
|---|---|
| arrival_bicarbonate | CASE_AUTHORED |
| arrival_delivery_ratio | FAMILY_CANDIDATE |
| arrival_lactate_excess | CASE_MAPPING |
| arrival_oxygen_debt | FAMILY_CANDIDATE |
| arrival_paco2 | CASE_AUTHORED |
| beta_blockade | CASE_MAPPING (0: no beta-blocker authored) |
| consciousness_level | CASE_AUTHORED |
| crt_s | CASE_AUTHORED |
| dbp | CASE_AUTHORED |
| fio2 | CASE_AUTHORED |
| glucose | CASE_AUTHORED |
| hb | CASE_AUTHORED |
| hr | CASE_AUTHORED |
| intrinsic_respiratory_rate | FAMILY_CANDIDATE (P2K-2's candidate input, the middle of its 12 / 16 / 20) |
| intrinsic_sinus_rate | CASE_MAPPING |
| k | CASE_AUTHORED |
| lactate | CASE_AUTHORED |
| metabolic_demand_baseline | CASE_MAPPING (1: afebrile 36.9, alert, no hypermetabolic evidence; gi_reference.demand_band's rule) |
| preload_fraction | CASE_MAPPING (neutral: IVC 1.9 cm with ~50% collapse is neither collapsing nor plethoric; the profile's provisional arrival position, nothing declared) |
| pump_reserve | FAMILY_CANDIDATE |
| respiratory_rate | CASE_AUTHORED |
| rhythm | CASE_AUTHORED |
| sbp | CASE_AUTHORED |
| spo2 | CASE_AUTHORED |

| Banda | Inferior | Punto medio | Superior | Clase | Regla (congelada) |
|---|---|---|---|---|---|
| arrival_delivery_ratio | 0,240 | 0,340 | 0,400 | FAMILY_CANDIDATE | gi_reference.delivery_ratio_band (0.6-1.0, at or below adequacy: cool extremities, CRT 3 s, mildly impaired perfusion, lactate 3.1) read under the extraction reserve as ratio / reserve (P2I-2P), as every GI package does |
| arrival_lactate_excess | 1,100 | 2,100 | 2,300 | CASE_MAPPING | gi_reference.lactate_excess_band's rule: the arrival lactate less a non-shock clearance baseline of 0.8-2.0 mmol/L; the baseline is not stated |
| arrival_oxygen_debt | 0,000 | 20,000 | 60,000 | FAMILY_CANDIDATE | gi_reference.arrival_debt_band's scale (0-60 index-minutes, the same for every case): a latent arrival-state variable, never computed from the arrival lactate; the authored onset (60 min) does not set it (no history is reconstructed) |
| intrinsic_sinus_rate | 60,000 | 80,000 | 100,000 | CASE_MAPPING | gi_reference.intrinsic_hr_band's rule: the resting adult sinus rate, at most the observed HR; no beta-blocker or rate control is authored (metformin, losartan, statin) |
| pump_reserve | 0,300 | 0,500 | 0,700 | FAMILY_CANDIDATE | the case shows reduced reserve (globally mildly reduced LV contraction, bibasal B-lines, mild congestion on the radiograph, basal crackles, troponin 260): below the GI band's 0.7-1.0, which had no such evidence; the value is not stated: faculty decision |

Papel de cada canal a la llegada (verificado, no forzado):

- **D**: SECONDARY_RESPONSE (prior oxygen-delivery debt)
- **G**: SECONDARY_RESPONSE (mild gas-exchange impairment)
- **L**: SECONDARY_RESPONSE (congestion present)
- **N**: NORMAL_OR_NEUTRAL
- **P**: PRIMARY_DRIVER
- **R**: SECONDARY_RESPONSE (sinus tachycardia)
- **T**: SECONDARY_RESPONSE
- **V**: NORMAL_OR_NEUTRAL
- **W**: SECONDARY_RESPONSE
<!-- /generado:mapeo -->

## 4. Semántica de P y D de llegada

<!-- generado:bomba -->
- **P_relative_to_arrival** (texto congelado, en inglés): Channel.P: multiplier, arrival = 1
- **absolute_impairment** (texto congelado, en inglés): the arrival layer: arrival_delivery_ratio (DO2 index against normal, derived.effective_delivery) and pump_reserve; never multiplied into output again
- **double_counting** (texto congelado, en inglés): False
- **output** (texto congelado, en inglés): output_rel = P x rhythm share x preload response (on the current pump's curve, relative to arrival filling) x afterload (derived._perfusion)
- **pending_common_decision** (texto congelado, en inglés): a depressed pump without added volume does not congest through the common coupling (derived.congestion_rate's own note): the family congestion writer carries the cardiogenic part
- **preload** (texto congelado, en inglés): the curve's scale is preload_curve_scale_ml x P^c (derived.preload_position): a falling P lowers the plateau and the gain per mL
- **reserve** (texto congelado, en inglés): pump_reserve enters only the congestion shortfall 1 - reserve x P (derived.congestion_rate)
- **second_pump_equation** (texto congelado, en inglés): True

- **D de llegada y lactato:** D con el lactato autorizado 20,0; con el lactato al doble 20,0; la función de mapeo no recibe el lactato: sí; pasa: sí.
<!-- /generado:bomba -->

## 5. Escritores de familia y capa de observación

<!-- generado:escritores -->
- **Pérdida isquémica de P** (FAMILY_CANDIDATE): 0,05, 0,10, 0,20 de la bomba de llegada por hora; piso 0,50; referencia 0,10 por hora.
- **Congestión en L** (FAMILY_CANDIDATE): ganancia = 0,5, 1,0, 2,0 × la escala común de congestión por precarga, por unidad de déficit de bomba (1 − P).
- **Reperfusión** (proceso logístico): señal en el minuto 60 (SYNTHETIC_ONLY: no hay tiempo puerta-balón autorizado); recuperación de 0,0, 0,5, 1,0 de lo que la oclusión quitó, con tau 30 min, nunca por encima de P = 1.
- **Contrafactual de fluidos:** {"duration_min": 30.0, "preload_deficiency_fraction": 0.25, "pump_failure_P": 0.7, "read_minute": 60, "volume_ml": 1000.0}.

Capa de observación (congelada, en inglés):

- **b_lines_congestion**: an observation of L: the authored bibasal B-lines and mild congestion are the arrival reading (L = 0 is arrival); L above 0 reads more congestion
- **ecg_ischaemia**: a family observation (diffuse ST depression with aVR elevation while the artery is occluded); no common channel
- **lv_function**: an observation of P: the authored 'globally mildly reduced contraction' is the arrival reading (P = 1 with the reduced reserve and delivery the arrival layer declares); a fall of P from arrival reads worse, a recovery toward 1 reads back to the authored finding
- **rhythm**: R (sinus, its rate from the common HR physiology)
- **troponin**: a family observation (the legacy curve is LEGACY_REFERENCE_ONLY); no common channel
<!-- /generado:escritores -->

## 6. Reconstrucción de la llegada

<!-- generado:llegada -->
| Observable | Núcleo | Autorizado |
|---|---|---|
| hr | 91,84 | 112 |
| sbp | 104,00 | 104 |
| dbp | 66,00 | 66 |
| map | 78,67 | 78,67 |
| spo2 | 94,00 | 94 |
| rr | 25,53 | 26 |
| lactate | 3,10 | 3,10 |
| ph | 7,39 | 7,36 |
| paco2 | 30,77 | 33 |
| mental_status | 0 | Alert |

Canales: V 0,000, T 1,000, P 1,000, R sinus, L 0,000, G 0,000, W 0,000, D 20,000, N 0,000.
FC de llegada en la banda intrínseca: inferior 73,1, media 91,8, superior 117,8 (autorizada 112); déficit de llegada 0,150, impulso simpático 0,476.
<!-- /generado:llegada -->

## 7. Isquemia sin tratar (región de familia predeclarada)

<!-- generado:sin_tratar -->
| Pérdida / h | Minuto | P | Q | PAM | Aporte | Déficit | D | Lactato | FC | L |
|---|---|---|---|---|---|---|---|---|---|---|
| 0,05 | 0 | 1,000 | 1,000 | 78,7 | 0,340 | 0,150 | 20,0 | 3,1 | 91,8 | 0,000 |
| 0,05 | 60 | 0,950 | 0,944 | 75,9 | 0,321 | 0,198 | 30,4 | 2,6 | 96,3 | 0,068 |
| 0,05 | 120 | 0,900 | 0,888 | 72,9 | 0,302 | 0,245 | 43,7 | 2,4 | 101,4 | 0,254 |
| 0,10 | 0 | 1,000 | 1,000 | 78,7 | 0,340 | 0,150 | 20,0 | 3,1 | 91,8 | 0,000 |
| 0,10 | 60 | 0,900 | 0,888 | 72,9 | 0,302 | 0,245 | 31,8 | 2,6 | 98,6 | 0,136 |
| 0,10 | 120 | 0,800 | 0,780 | 66,6 | 0,265 | 0,337 | 49,2 | 2,4 | 106,5 | 0,508 |
| 0,20 | 0 | 1,000 | 1,000 | 78,7 | 0,340 | 0,150 | 20,0 | 3,1 | 91,8 | 0,000 |
| 0,20 | 60 | 0,800 | 0,780 | 66,6 | 0,265 | 0,337 | 34,6 | 2,6 | 103,1 | 0,273 |
| 0,20 | 120 | 0,600 | 0,571 | 52,5 | 0,194 | 0,514 | 60,1 | 2,5 | 116,3 | 1,017 |

Direcciones en toda la región: D_up sí; L_up sí; P_nonincreasing sí; Q_down sí; deficit_up sí; delivery_down sí; map_down sí; pulse_kept sí; la familia escribe sólo P y L: sí; lactato sólo del núcleo: sí; FC por el impulso común: sí.

L a los 120 min según la ganancia de congestión: 0.5 × → 0,2542, 1.0 × → 0,5085, 2.0 × → 1,0169.
Sensibilidad 1-D a la ganancia de tono (P, Q, PAM, T, D a los 120 min): 0.25: 0,800, 0,790, 64,8, 1,043, 48,7; 0.5: 0,800, 0,780, 66,6, 1,086, 49,2; 1.0: 0,800, 0,760, 70,3, 1,176, 50,4.
Sensibilidad 1-D a k_LD (lactato a 0, 60, 120 min): 0.000245327: 3,10, 2,57, 2,42; 0.000729069: 3,10, 3,16, 3,71; 0.00216667: 3,10, 4,92, 7,54; 2.77778e-05: 3,10, 2,31, 1,84; 8.25508e-05: 3,10, 2,37, 1,99.
<!-- /generado:sin_tratar -->

## 8. Contrafactual de reperfusión

<!-- generado:reperfusion -->
| Curso | P | Q | PAM | Aporte | Déficit | D | Lactato | FC | L |
|---|---|---|---|---|---|---|---|---|---|
| isquemia en curso | 0,800 | 0,780 | 66,6 | 0,265 | 0,337 | 49,2 | 2,4 | 106,5 | 0,508 |
| reperfusión, recuperación 0.0 | 0,902 | 0,890 | 73,1 | 0,303 | 0,243 | 46,4 | 2,4 | 102,0 | 0,368 |
| reperfusión, recuperación 0.5 | 0,944 | 0,937 | 75,6 | 0,319 | 0,203 | 44,8 | 2,4 | 100,0 | 0,290 |
| reperfusión, recuperación 1.0 | 0,987 | 0,985 | 78,0 | 0,335 | 0,162 | 43,2 | 2,4 | 98,0 | 0,213 |

A los 120 min, con reperfusión en el minuto 60: P mejor que con la isquemia en curso sí; Q y déficit siguen por la fisiología común sí; sólo P y L escritos sí.
<!-- /generado:reperfusion -->

## 9. Contrafactual de fluidos

<!-- generado:fluidos -->
| Estado | Q inicial | Q sin fluido | Q con fluido | Ganancia de Q | Ganancia de PAM | L con fluido |
|---|---|---|---|---|---|---|
| falla de bomba | 0,700 | 0,674 | 0,720 | 0,046 | 3,3 | 0,0000 |
| déficit de precarga | 1,000 | 1,000 | 1,259 | 0,259 | 13,4 | 0,0000 |

El volumen mejora la precarga sí; da menos en la bomba débil sí; no normaliza la falla de bomba sí; la congestión queda visible en L sí.
<!-- /generado:fluidos -->

## 10. Colapso: lectura estructural, nunca activo

<!-- generado:colapso -->
| Minuto | Aporte | Perfusión (UNSET) | Perfusión (rampa estructural) | Señal (máximo) | Máximo |
|---|---|---|---|---|---|
| 0 | 0,150 | — | 0,921 | 0,921 | sí |
| 60 | 0,245 | — | 0,927 | 0,927 | sí |
| 120 | 0,337 | — | 0,933 | 0,933 | sí |

Con el mapeo de PAM UNSET la señal es una cota inferior sí; sin regla cardiogénica sí; activo no; umbrales elegidos no; transición terminal no. M1: `REQUIRED_BEFORE_ACTIVE_FAMILY_COLLAPSE`; M2: `REQUIRED_BEFORE_RUNTIME_TRACE_INTEGRATION`.
<!-- /generado:colapso -->

## 11. Comparación con el legado (después de la verdad autorizada)

<!-- generado:legado -->
| Minuto | PAS legado / núcleo | FC legado / núcleo | SpO2 legado / núcleo | Ritmo legado |
|---|---|---|---|---|
| 0 | 104 / 104,0 | 112 / 91,8 | 94 / 94,0 | Sinus tachycardia |
| 60 | 98 / 96,4 | 115 / 98,6 | 90 / 94,0 | Sinus tachycardia |
| 90 | 95 / 92,3 | 117 / 102,4 | 88 / 94,0 | Sinus tachycardia |
| 120 | 0 / 88,1 | 0 / 106,5 | 0 / 94,0 | VF |

Clasificación (texto congelado, en inglés):

- **hr_arrival**: LEGACY_DIFFERENCE_NOT_CLINICALLY_RELEVANT: the legacy shows the authored HR; the core's is the common HR physiology's at the midpoint intrinsic rate (reported, not absorbed)
- **sbp_course**: LEGACY_DIFFERENCE_NOT_CLINICALLY_RELEVANT: both fall under untreated ischaemia; the size is the family candidate's and the legacy drift's, neither authored
- **spo2_course**: EXPECTED_EXTENSION_NOT_YET_MODELED: the legacy SpO2 falls with congestion; the core's L has no gas-exchange path (EXPECTED_RESPIRATORY_FAMILY_EXTENSION)
- **vf_120**: EXPECTED_EXTENSION_NOT_YET_MODELED: LEGACY_FAMILY_EVENT_DEFERRED (no scripted VF, no ROSC / ACLS)

Posible brecha del núcleo común: ninguna; el legado usado para elegir parámetros: no.
<!-- /generado:legado -->

## 12. Frontera familia / común

<!-- generado:frontera -->
- Canales que escriben los escritores de familia: L, P.
- Observables nombrados por los escritores: ninguno; otras escrituras: ninguna.
- Archivos comunes que nombran la familia: ninguno.
- Clases: CoronaryReperfusion FAMILY_WRITER (logistic signal, no write); IschaemicCongestion FAMILY_WRITER (L); IschaemicPump FAMILY_WRITER (P); OBSERVATION_LAYER OBSERVATION_LAYER; anchors ARRIVAL_MAPPING; legacy LEGACY_ONLY.
- Pasa: sí.
<!-- /generado:frontera -->

## 13. No regresión del núcleo y de GI

<!-- generado:gi -->
- **Árbol de P2M-2** (`6601fc7`), 69 archivos: sí (los de fisiología y análisis cerrados byte a byte; dos archivos de tuplas sólo ganan entradas); ningún archivo común lee la familia: sí.
- **GI 57m sin tratar, 120 min, con los escritores ACS inertes:** canales y estado auxiliar idénticos sí; escrituras de los inertes 0.
<!-- /generado:gi -->

## 14. Veredicto

<!-- generado:veredicto -->
| Criterio | Cumple |
|---|---|
| L representa la congestión | sí |
| la llegada autorizada es representable | sí |
| fronteras familia / común | sí |
| el colapso sigue inactivo | sí |
| el colapso evalúa el estado (estructural) | sí |
| Q, aporte y FC responden por la fisiología común | sí |
| D y lactato coherentes | sí |
| GI sin cambios | sí |
| la isquemia mueve P | sí |
| el legado no es objetivo | sí |
| sin reajuste del núcleo | sí |
| la falla de bomba entra por P | sí |
| la reperfusión actúa sobre P | sí |
| extensión respiratoria diferida y explícita | sí |

**Veredicto:** `CARDIOGENIC_SHADOW_MIGRATION_READY`.
<!-- /generado:veredicto -->

## 15. Recomendación estratégica

<!-- generado:recomendacion -->
**Recomendación:** `IMPLEMENT_EXPECTED_RESPIRATORY_EXTENSION`.

Regla (texto congelado, en inglés): Predeclared. With READY: IMPLEMENT_EXPECTED_RESPIRATORY_EXTENSION when the case's authored congestion has no downstream path in the core (L rises with no SpO2 / G change) and the legacy comparison carries a respiratory EXPECTED_EXTENSION; otherwise PROCEED_TO_CARDIOGENIC_CASE_EXPANSION; TEST_THIRD_MECHANISTIC_FAMILY only if both the respiratory extension and case expansion are found unnecessary.
<!-- /generado:recomendacion -->

## 16. Decisiones pedidas

<!-- generado:pedidas -->
Decisiones pedidas a la docencia (texto congelado, en inglés):

1. the arrival mapping's candidates (pump reserve, arrival delivery ratio, arrival D, lactate excess, intrinsic sinus rate): FAMILY_CANDIDATE / CASE_MAPPING values to accept, narrow or replace
2. the ischaemic family writer's kinetics (loss per minute, floor, recovery share and time) and the congestion gain
3. whether a common P -> L coupling replaces the family congestion writer (derived.congestion_rate's pending note)
4. the arrival HR: the common physiology at the midpoint intrinsic rate reads below the authored 112; accept the gap, narrow the intrinsic band, or revisit the common HR gains (never an ACS residual)
5. the next package (the recommendation)
<!-- /generado:pedidas -->

## 17. Eficiencia

<!-- generado:eficiencia -->
- Pasos del integrador: 2760; lecturas de estado fijo: 6.
- Trayectorias GI: 2 (non-regression only); minutos del motor heredado: 120.
- Barrido cartesiano: no.
- Registros reutilizados (con huella fijada): P2M2_collapse_architecture.json.
<!-- /generado:eficiencia -->

## 18. Limitaciones

- **Ningún valor de la familia está aprobado.** Las pérdidas de P (5, 10 y 20 % por hora), el piso, la recuperación, la
  ganancia de congestión y el minuto de reperfusión son FAMILY_CANDIDATE o SYNTHETIC_ONLY. Las bandas de llegada usan
  las reglas de GI, y la reserva de bomba (0,3-0,7) es candidata.
- **El perfil común es un solo punto** (el centro de cada conjunto certificado). Sólo se barrieron, en 1-D, la ganancia
  de tono y k_LD.
- **Lactato bajo isquemia.** Con el k_LD medio baja (3,1 → 2,4 en 120 min) aunque D sube, porque el exceso de llegada
  (2,3) supera el estado estacionario de la D de llegada. Sólo sube con los dos k_LD superiores (3,7 y 7,5). Es
  incertidumbre común, que una segunda familia ayuda a discriminar; no se eligió ningún valor.
- **FC de llegada.** La fisiología común da 91,8 con la intrínseca media, frente a 112 autorizado. La banda (73-118)
  contiene lo autorizado. Se informa y no se absorbe.
- **Congestión con fluidos.** Con 1000 mL, la posición de precarga de la bomba débil (0,67) no llega a la rodilla común
  (0,85): L no sube por fluidos. El criterio «congestión visible» se cumplió sólo porque L no bajó (es débil, y queda
  declarado). La congestión que muestra el caso la da el escritor de familia.
- **El legado se leyó del motor de familia sólo como referencia.** No se usó para elegir parámetros.
- **Fuera del alcance:** L → G / SpO2, VNI, barorreflejo → tono, poscarga dependiente de P, ROSC / ACLS y la FV
  heredada.

## 19. Revisión adversarial

Pendiente: la revisión adversarial independiente corre sobre el congelamiento y esta evaluación.
