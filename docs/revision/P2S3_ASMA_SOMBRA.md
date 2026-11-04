# P2S-3 · Migración en sombra del asma

Paquete de migración de familia sobre el núcleo común cerrado por P2S-2. No cambia la fisiología común: sólo se añaden
los archivos de la familia y entradas en las dos tuplas de registro (§17). Rama `phase-2-clinical-core-shadow`; base
`daa23d6` (P2S-2 aceptado y cerrado).

- Casos: primario `asthma_49m` (asma con riesgo vital, fatiga e hipercapnia); secundario `asthma_24f` (asma aguda grave,
  ventilación compensada).
- Módulos:
  - `clinical_core/modules/asthma.py`: el escritor de familia;
  - `clinical_core/asthma_reference.py`: la verdad y el mapeo de llegada;
  - `clinical_core/asthma_migration.py`: el análisis, congelado antes de evaluar.
- Registro: `docs/revision/P2S3_asthma_migration.json`. Este documento se genera desde el registro
  (`clinical_core/asthma_migration_report.py`); el texto fuera de los marcadores es la narrativa.

## 1. Reglas que rigen

- Migración de familia, sin retocar el núcleo común: ni las bandas de FR intrínseca, ni las ganancias ácida e
  hipoxémica, ni la ecuación de la mecánica, la PaCO2 de referencia, G → SpO2, D / lactato, FC, conciencia o colapso. Si
  hiciera falta un cambio común, el paquete se detiene con COMMON_CORE_BLOCKER_FOUND.
- El escritor de la obstrucción escribe sólo la eficiencia mecánica común. La FR, la PaCO2, la SpO2, G, el aporte, D,
  el lactato, la FC y la conciencia siguen en el núcleo común.
- La mecánica de llegada es un estado latente FAMILY_CANDIDATE: una región pequeña declarada antes de evaluar, nunca un
  valor elegido para reconstruir.
- El impulso es el de P2P-2, sin cambios: sin residuo del asma, mapeo hipoxémico UNSET, disponibilidad 1.
- Sin broncodilatador si no hace falta y no existe la acción en el núcleo; sin esteroide
  (STEROID_ACUTE_PHYSIOLOGY_DEFERRED); O2 por la vía común; la brecha de FC no se toca; P2L-2 no se integra; colapso
  sólo estructural; el legado se lee al final.

## 2. Verdad del repositorio (P2S-3-1)

Leída del banco de casos por ruta (`asthma_reference.TRUTH_PATHS`), nunca retipeada. Clases:

- AUTHORED_CASE_TRUTH: todo lo del banco;
- LEGACY_ENGINE_BEHAVIOR: la deriva y las reglas del asma de `family_engine`;
- MODEL_DERIVED: la FR, W, la PaCO2 y la FC del núcleo.

<!-- generado:caso -->
- **`asthma_24f`:** «Acute severe asthma exacerbation». PA 138/84 (PAM 102,0), FC 126 (Sinus tachycardia), SpO2 90 % aire ambiente, FR 34, trabajo respiratorio «Markedly increased», «Alert», 36.8 °C, glucemia 116. Gases 7.45 / PaCO2 31 / PaO2 59, HCO3 20.8; lactato 2.1.
  - Flujo pico: Peak expiratory flow is 35% of her documented personal best. Exploración: «Marked effort, prolonged expiration and widespread expiratory wheeze with reduced air entry. Peak expiratory flow is 35% of her documented personal best.». POCUS: «No B-lines; A-line pattern bilaterally»; radiografía «Hyperinflation without focal consolidation or pneumothorax.».
  - Antes de llegar: «I have used my reliever repeatedly today; my preventer inhaler ran out last week.». Tratamientos definitivos autorales: bronchodilator, steroid, oxygen.
- **`asthma_49m`:** «Life-threatening asthma with fatigue and hypercapnia». PA 142/86 (PAM 104,7), FC 132 (Sinus tachycardia), SpO2 89 % aire ambiente, FR 30, trabajo respiratorio «Severe», «Drowsy», 37.0 °C, glucemia 121. Gases 7.3 / PaCO2 51 / PaO2 57, HCO3 24.2; lactato 2.6.
  - Flujo pico: He cannot complete a reliable peak-flow maneuver. Exploración: «Severe effort with very poor bilateral air entry and only faint wheeze. He cannot complete a reliable peak-flow maneuver.». POCUS: «No B-lines; A-line pattern bilaterally»; radiografía «Hyperinflation without pneumothorax or focal air-space opacity.».
  - Antes de llegar: «He uses an inhaled corticosteroid/long-acting bronchodilator and has repeatedly used his rescue inhaler today.». Tratamientos definitivos autorales: bronchodilator, steroid, oxygen.
- **Regla de selección:** the faculty's primary (asthma_49m: life-threatening asthma with fatigue and hypercapnia) and secondary (asthma_24f: acute severe asthma, compensated ventilation); the family's only two variants.
- **Observaciones posteriores:** NONE_AUTHORED: both cases state the arrival only; no peak flow, gas or vital sign after any treatment is authored.
- **Comportamiento heredado (sólo referencia):** asthma: obstruction +0.002 per minute, exhaustion tracking, bronchodilator / magnesium / epinephrine / ketamine bronchodilation, beta side effects, oxygen shunt 0.30 (family_engine, asthma_complications): LEGACY_ENGINE_BEHAVIOR.
- **Derivado del modelo:** the expressed RR, W, PaCO2 and pH (the P2S-2 candidate), the predicted HR, the delivery and the deficit, read from the common core at the mapped arrival.
- Verdad suficiente: sí.
<!-- /generado:caso -->

## 3. Mapeo de llegada (P2S-3-3, P2S-3-16)

La eficiencia de llegada se lee de la FR y la PaCO2 autorales con la forma común de P2S-2:
E = 40 × FR intrínseca / (PaCO2 × FR), con la FR intrínseca 12 / 16 / 20 declarada junto con su propia E. La FR
intrínseca se declara siempre: la revisión de P2S-2 mostró que, sin declararla, el candidato tomaría la FR autoral como
referencia de W. La disponibilidad central queda en 1: la somnolencia del 49m está escrita junto con la hipercapnia, no
como una depresión independiente.

<!-- generado:llegada -->
| Caso | Punto | FR intrínseca | E | FR del núcleo | FR autoral | W | PaCO2 del núcleo | PaCO2 autoral | PaCO2 con la FR autoral | pH | SpO2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `asthma_24f` | lower | 12 | 0,455 | 17,6 | 34 | 0,670 | 59,7 | 31 | 31,0 | 7,165 | 90,0 |
| `asthma_24f` | midpoint | 16 | 0,607 | 21,6 | 34 | 0,821 | 48,7 | 31 | 31,0 | 7,253 | 90,0 |
| `asthma_24f` | upper | 20 | 0,759 | 25,6 | 34 | 0,973 | 41,1 | 31 | 31,0 | 7,327 | 90,0 |
| `asthma_49m` | lower | 12 | 0,314 | 12,0 | 30 | 0,314 | 127,5 | 51 | 51,0 | 6,901 | 89,0 |
| `asthma_49m` | midpoint | 16 | 0,418 | 16,0 | 30 | 0,418 | 95,6 | 51 | 51,0 | 7,026 | 89,0 |
| `asthma_49m` | upper | 20 | 0,523 | 20,0 | 30 | 0,523 | 76,5 | 51 | 51,0 | 7,123 | 89,0 |

- Banda FAMILY_CANDIDATE de la eficiencia de llegada: `asthma_24f` 0,455 – 0,759 (punto medio 0,607); `asthma_49m` 0,314 – 0,523 (punto medio 0,418). Regla: P2S-2-11's analytic region: PaCO2_reference x demand x intrinsic RR / (authored PaCO2 x authored RR), each point with its own declared intrinsic RR (12 / 16 / 20), the arrival demand ratio 1; no value selected, nothing fitted to a later course.
- La PaCO2 de llegada del núcleo difiere de la autoral por el cociente FR autoral / FR del núcleo, y con la FR autoral el mapeo devuelve la PaCO2 autoral. Ambas cosas son identidades del mapeo (la E se invierte de la FR y la PaCO2 autorales), no evidencia de que el núcleo represente la llegada: el núcleo no la representa (COMMON_DRIVE_GAP). «Llegada coherente» de la regla congelada: sí.
<!-- /generado:llegada -->

## 4. El escritor de la familia (P2S-3-2)

<!-- generado:escritor -->
- Palabras de `Contribution` en el escritor: mechanics; nombres prohibidos: ninguno; deltas de canal: 0.
- Escribe [[0.9983333333333333, 'disease_module:asthma-obstruction']] por minuto con la tasa media; con tasa 0 no escribe nada (sí); registrado sí, módulo de enfermedad sí.
- Rechazos: boolean sí, candidate_off sí, nan sí, negative sí, one sí.
- Pasa: sí.
<!-- /generado:escritor -->

## 5. Contraste 49m / 24f (P2S-3-4)

<!-- generado:contraste -->
| Comprobación | 12 | 16 | 20 |
|---|---|---|---|
| E del 49m menor que la del 24f | sí | sí | sí |
| PaCO2 del núcleo: 49m mayor que 24f | sí | sí | sí |
| 49m hipercápnico en el núcleo | sí | sí | sí |
| 24f hipocápnico con su FR autoral | sí | sí | sí |
| 24f hipocápnico con la FR del núcleo | no | no | no |

- Solapamiento de las bandas: 0,455 – 0,523.
- Compensación del 24f: COMMON_DRIVE_GAP: the 24f hypocapnia holds at the authored RR but not at the core's RR (P2P-2 drive, hypoxaemic mapping UNSET, no non-chemical excitatory input); reported, never deciding.
- Pasa: sí.
<!-- /generado:contraste -->

## 6. Curso sin tratamiento (P2S-3-15 A)

Tramo predeclarado: la escala congelada del escritor isquémico de ACS (0,05 / 0,10 / 0,20 por hora), leída como
fracción de la eficiencia perdida por hora, y cero. No se ajusta: no hay curso autoral después de la llegada.

<!-- generado:curso -->
**`asthma_49m`** (sólo cambia la ventilación, y en la dirección exigida: sí):

| Empeoramiento por hora | Minuto | E | FR | W | PaCO2 | pH | SpO2 | FC | D | Lactato | Conciencia |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0,00 | 0 | 0,418 | 16,0 | 0,418 | 95,6 | 7,026 | 89,0 | 80,0 | 0,00 | 2,60 | 1 |
| 0,00 | 60 | 0,418 | 16,0 | 0,418 | 95,6 | 7,026 | 89,0 | 80,0 | 0,00 | 1,97 | 1 |
| 0,00 | 120 | 0,418 | 16,0 | 0,418 | 95,6 | 7,026 | 89,0 | 80,0 | 0,00 | 1,59 | 1 |
| 0,05 | 0 | 0,418 | 16,0 | 0,418 | 95,6 | 7,026 | 89,0 | 80,0 | 0,00 | 2,60 | 1 |
| 0,05 | 60 | 0,398 | 16,0 | 0,398 | 100,5 | 7,004 | 89,0 | 80,0 | 0,00 | 1,97 | 1 |
| 0,05 | 120 | 0,378 | 16,0 | 0,378 | 105,7 | 6,983 | 89,0 | 80,0 | 0,00 | 1,59 | 1 |
| 0,10 | 0 | 0,418 | 16,0 | 0,418 | 95,6 | 7,026 | 89,0 | 80,0 | 0,00 | 2,60 | 1 |
| 0,10 | 60 | 0,378 | 16,0 | 0,378 | 105,7 | 6,983 | 89,0 | 80,0 | 0,00 | 1,97 | 1 |
| 0,10 | 120 | 0,342 | 16,0 | 0,342 | 116,8 | 6,939 | 89,0 | 80,0 | 0,00 | 1,59 | 1 |
| 0,20 | 0 | 0,418 | 16,0 | 0,418 | 95,6 | 7,026 | 89,0 | 80,0 | 0,00 | 2,60 | 1 |
| 0,20 | 60 | 0,342 | 16,0 | 0,342 | 116,8 | 6,939 | 89,0 | 80,0 | 0,00 | 1,97 | 1 |
| 0,20 | 120 | 0,280 | 16,0 | 0,280 | 142,8 | 6,852 | 89,0 | 80,0 | 0,00 | 1,59 | 1 |

**`asthma_24f`** (sólo cambia la ventilación, y en la dirección exigida: sí):

| Empeoramiento por hora | Minuto | E | FR | W | PaCO2 | pH | SpO2 | FC | D | Lactato | Conciencia |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0,00 | 0 | 0,607 | 21,6 | 0,821 | 48,7 | 7,253 | 90,0 | 80,0 | 0,00 | 2,10 | 0 |
| 0,00 | 60 | 0,607 | 19,6 | 0,743 | 53,8 | 7,236 | 90,0 | 80,0 | 0,00 | 1,67 | 0 |
| 0,00 | 120 | 0,607 | 18,2 | 0,692 | 57,8 | 7,219 | 90,0 | 80,0 | 0,00 | 1,40 | 0 |
| 0,05 | 0 | 0,607 | 21,6 | 0,821 | 48,7 | 7,253 | 90,0 | 80,0 | 0,00 | 2,10 | 0 |
| 0,05 | 60 | 0,578 | 19,6 | 0,707 | 56,6 | 7,214 | 90,0 | 80,0 | 0,00 | 1,67 | 0 |
| 0,05 | 120 | 0,549 | 18,2 | 0,626 | 63,9 | 7,176 | 90,0 | 80,0 | 0,00 | 1,40 | 0 |
| 0,10 | 0 | 0,607 | 21,6 | 0,821 | 48,7 | 7,253 | 90,0 | 80,0 | 0,00 | 2,10 | 0 |
| 0,10 | 60 | 0,549 | 19,6 | 0,673 | 59,5 | 7,192 | 90,0 | 80,0 | 0,00 | 1,67 | 0 |
| 0,10 | 120 | 0,497 | 18,2 | 0,567 | 70,6 | 7,133 | 90,0 | 80,0 | 0,00 | 1,40 | 0 |
| 0,20 | 0 | 0,607 | 21,6 | 0,821 | 48,7 | 7,253 | 90,0 | 80,0 | 0,00 | 2,10 | 0 |
| 0,20 | 60 | 0,497 | 19,6 | 0,608 | 65,7 | 7,149 | 90,0 | 80,0 | 0,00 | 1,67 | 0 |
| 0,20 | 120 | 0,407 | 18,2 | 0,464 | 86,3 | 7,045 | 90,0 | 80,0 | 0,00 | 1,40 | 0 |

Pasa: sí.
<!-- /generado:curso -->

## 7. Alivio de la mecánica (P2S-3-15 B, P2S-3-9)

<!-- generado:alivio -->
| Minuto | E sin alivio | E con alivio | W sin | W con | PaCO2 sin | PaCO2 con |
|---|---|---|---|---|---|---|
| 0 | 0,418 | 0,418 | 0,418 | 0,418 | 95,6 | 95,6 |
| 30 | 0,398 | 0,398 | 0,398 | 0,398 | 100,5 | 100,5 |
| 60 | 0,378 | 0,510 | 0,378 | 0,510 | 105,7 | 78,4 |
| 90 | 0,360 | 0,485 | 0,360 | 0,485 | 111,1 | 82,4 |
| 120 | 0,342 | 0,462 | 0,342 | 0,462 | 116,8 | 86,7 |

- FR, SpO2 y FC sin cambio: sí.
- BRONCHODILATOR_WRITER_DEFERRED: the shadow core has no bronchodilator action and no post-treatment course is authored; relief is representable through the common mechanics target.
- Pasa: sí.
<!-- /generado:alivio -->

## 8. Oxígeno (P2S-3-11, P2S-3-15 C)

<!-- generado:oxigeno -->
| FiO2 | SpO2 min 0 | SpO2 min 30 | SpO2 min 60 | SpO2 min 90 | SpO2 min 120 |
|---|---|---|---|---|---|
| 0,21 | 89,0 | 89,0 | 89,0 | 89,0 | 89,0 |
| 0,40 | 89,0 | 94,7 | 94,7 | 94,7 | 94,7 |
| 0,60 | 89,0 | 100,0 | 100,0 | 100,0 | 100,0 |

- La SpO2 sube con la FiO2: sí; la PaCO2 y la FR no cambian con el O2: sí; función de O2 de la familia: no. Pasa: sí.
<!-- /generado:oxigeno -->

## 9. G directa e hipoventilación → oxigenación (P2S-3-5, P2S-3-6)

<!-- generado:g_directa -->
- DIRECT_G_NOT_REQUIRED: the arrival V/Q impairment is the anchored arrival (G = 0, the authored SpO2 exact); no later V/Q change is authored; the family writes no G and no L.
- Escrituras de G: 0; de L: 0; G y L en 0: sí.

| Caso | PaO2 | PaCO2 | PAO2 (diagnóstico) | Gradiente A-a | Pérdida alveolar hipoventilatoria |
|---|---|---|---|---|---|
| `asthma_24f` | 59 | 31 | 111,0 | 52,0 | −11,2 |
| `asthma_49m` | 57 | 51 | 86,0 | 29,0 | 13,8 |

- the alveolar arithmetic reads the authored gas with textbook constants; it is not a core path (HYPOVENTILATION_TO_OXYGENATION_LINK_DEFERRED).
- EXPECTED_ALVEOLAR_GAS_EXTENSION: in 49m part of the hypoxaemia is hypoventilatory; the core keeps the arrival SpO2 and does not lower it as PaCO2 rises.
- Pasa: sí.
<!-- /generado:g_directa -->

## 10. Impulso y disponibilidad (P2S-3-7, P2S-3-8)

<!-- generado:impulso -->
| Caso | FR autoral | Impulso ácido | FR (hipoxémico UNSET) | Impulso hipoxémico sintético | FR (sintético) | Disponibilidad |
|---|---|---|---|---|---|---|
| `asthma_24f` | 34 | 6,40 | 21,6 | 2,00 | 23,1 | 1,00 |
| `asthma_49m` | 30 | 0,00 | 16,0 | 2,20 | 18,1 | 1,00 |

- P2P-2 sin cambios (hipoxémico UNSET, disponibilidad 1, ganancia ácida común): sí; el impulso sintético crece estructuralmente: sí.
- COMMON_DRIVE_GAP (EXPECTED_EXTENSION): the arrival tachypnoea is not expressed without a non-chemical excitatory input; no asthma residual, no gain fitted.
<!-- /generado:impulso -->

## 11. Brecha de FC (P2S-3-12)

<!-- generado:fc -->
| Caso | Autoral | Predicha | Brecha | Predicha en la banda baja / media / alta | β-agonista previo |
|---|---|---|---|---|---|
| `asthma_24f` | 126 | 80,0 | −46,0 | 60,0 / 80,0 / 100,0 | sí |
| `asthma_49m` | 132 | 80,0 | −52,0 | 60,0 / 80,0 / 100,0 | sí |

- HR_GAP_DISTRESS_AROUSAL_DOMINANT carried forward (ACS, pulmonary oedema, PE, asthma); the authored repeated beta-agonist use is a confounder in asthma only; nothing patched.
- Ganancias intactas: sí.
<!-- /generado:fc -->

## 12. Conciencia (P2S-3-13)

<!-- generado:conciencia -->
- Autoral: 49m «Drowsy», 24f «Alert».
- 49m con la tasa media: nivel min 0: 1, min 30: 1, min 60: 1, min 90: 1, min 120: 1; PaCO2 95,6, 100,5, 105,7, 111,1, 116,8.
- the core's level is the authored arrival plus derive's ADOPTED SpO2 / SBP ladder: the rising PaCO2 does not reach it (P2L-2 not integrated); 49m is diagnostic evidence for a hypercapnic encephalopathy, never a calibration target.
<!-- /generado:conciencia -->

## 13. Colapso (P2S-3-14)

<!-- generado:colapso -->
- Máximo se mantiene: sí; UNSET es cota inferior: sí; la mecánica llega al gasto: no; sin regla de familia: sí.
- EXPECTED_EXTENSION: the mechanics do not reach output in the core (no hypercapnic / hypoxic arrest path); the collapse layer accepts the readings structurally.
<!-- /generado:colapso -->

## 14. Legado, leído al final (P2S-3-17)

<!-- generado:legado -->
| Minuto | Legado FR | Legado SpO2 | Legado FC | Legado conciencia | Núcleo FR | Núcleo SpO2 | Núcleo FC | Núcleo PaCO2 |
|---|---|---|---|---|---|---|---|---|
| 0 | 30 | 89 | 132 | Drowsy | 16,0 | 89,0 | 80,0 | 95,6 |
| 60 | 33 | 86 | 152 | Drowsy | 16,0 | 89,0 | 80,0 | 105,7 |
| 120 | 37 | 84 | 157 | Drowsy | 16,0 | 89,0 | 80,0 | 116,8 |

- **bronchodilator:** EXPECTED_EXTENSION: the legacy's bronchodilation family is not migrated (BRONCHODILATOR_WRITER_DEFERRED).
- **consciousness:** POSSIBLE_COMMON_CORE_GAP: the core's level does not read PaCO2 (P2L-2 not integrated).
- **fatigue_obstruction_drift:** LEGACY_DIFFERENCE_NOT_CLINICALLY_RELEVANT: both worsen untreated; the size is the family span's and the legacy drift's, neither authored; no fatigue memory.
- **hr:** POSSIBLE_COMMON_CORE_GAP: the legacy holds the authored HR (with beta side effects); the core's arrival HR is the common physiology's (HR_GAP_DISTRESS_AROUSAL_DOMINANT).
- **rr:** EXPECTED_EXTENSION: the legacy shows the authored RR; the core's RR is the P2P-2 drive's (COMMON_DRIVE_GAP).
- **spo2:** EXPECTED_EXTENSION: the legacy moves SpO2 with its obstruction (oxygen shunt 0.30); the core keeps the arrival SpO2 as PaCO2 rises (HYPOVENTILATION_TO_OXYGENATION_LINK_DEFERRED).
- Usado para parámetros: no.
<!-- /generado:legado -->

## 15. No regresión entre familias (P2S-3-18)

<!-- generado:no_regresion -->
- Registro de P2S-2 reproducido: p2s2_arrival_regions sí, p2s2_directions sí, p2s2_interface sí, p2s2_non_regression sí, p2s2_probes sí.
- Archivos comunes en sus bytes de P2S-2: sí. Pasa: sí.
<!-- /generado:no_regresion -->

## 16. Prueba contra el árbol de P2S-2

Los únicos archivos de `clinical_core` que cambian son las dos tuplas de registro (`lactate_slice.DOWNSTREAM_REPORTS`,
`decision_pack.PACK_DIGEST_EXCLUDED`). Se reconstruyen byte a byte como las dejó P2S-2. Todos los demás archivos `.py` de
`clinical_core` existentes en `daa23d6` están fijados por su hash.

<!-- generado:prueba -->
- Tuplas probadas contra P2S-2 (`daa23d6`): `clinical_core/decision_pack.py` sí, `clinical_core/lactate_slice.py` sí.
- Archivos comunes fijados por hash: 115, intactos sí.
- Vista de P2S-2: digest de congelación sí, su prueba contra P2Q-2 sí, registro sí.
<!-- /generado:prueba -->

## 17. Veredicto (P2S-3-19)

> **Clasificación del paquete tras la revisión adversarial:**
> `ASTHMA_SHADOW_MIGRATION_NOT_READY — COMMON_CORE_BLOCKER_FOUND (COMMON_DRIVE_GAP)`.
>
> Con el impulso de P2P-2 sin cambios, el núcleo no representa la llegada autoral:
> - el 49m sale con FR 16, PaCO2 95,6 y pH 7,03 (autoral: 30, 51 y 7,30);
> - el 24f, autoralmente hipocápnico y alcalémico, sale hipercápnico y acidémico (48,7 y 7,25).
>
> Representarlo exige un impulso excitador no químico común, un cambio del núcleo que P2S-3 prohíbe. El veredicto
> READY de abajo es el que da la regla congelada. La revisión mostró (§20, hallazgo 1) que esa regla decidía sobre
> identidades del mapeo y dejaba fuera la única comprobación no tautológica, que falla. No se vuelve a congelar ni se
> cambia la regla.

Regla predeclarada: READY si se cumplen todos los criterios; si no, NOT_READY con el primero que falla.

Se informan y nunca deciden, como en cada migración desde P2P-1:

- la brecha de FR de llegada (COMMON_DRIVE_GAP);
- su propagación a la PaCO2 de llegada, que es nueva con el candidato de mecánica;
- la parte hipoventilatoria de la hipoxemia;
- la brecha de FC;
- la conciencia;
- las diferencias con el legado.

<!-- generado:veredicto -->
- sí — the family mechanics writer cleanly targets the common mechanics (mechanics changes only; refused with the candidate off; no RR, PaCO2, SpO2, G, DO2, D, lactate, HR or consciousness writes)
- sí — the arrival mapping is coherent (truth by path; the authored arrival exact where the core models it; the intrinsic RR declared with its own efficiency; L and G 0; availability 1; the arrival PaCO2 differs from the authored by exactly the RR ratio, the mechanics mapping consistent at the authored RR)
- sí — the 49m / 24f distinction is representable by family mechanics severity only (mechanics and core PaCO2 ordered at every point; 49m hypercapnic; 24f hypocapnic at its authored RR; one profile, one set of equations)
- sí — W / PaCO2 behave coherently (worsening: E, W, pH down, PaCO2 up, nothing else moved; relief: the reverse; oxygen: SpO2 up, PaCO2 and RR unchanged)
- sí — no common retuning (the P2P-2 drive unchanged, hypoxaemic UNSET, availability 1, the PaCO2 reference 40, the gains untouched; the P2S-2 tree proven)
- sí — direct G optional and clean, no false L (no G or L write; G and L stay 0)
- sí — the HR gap stays diagnostic (no sympathetic input; residual reported)
- sí — prior families unchanged (P2S-2's probes, interface, regions, directions and non-regression reproduced; every common file at its P2S-2 bytes)
- sí — collapse accepts the readings structurally (max holds, UNSET a lower bound, no family rule)

**Veredicto: ASTHMA_SHADOW_MIGRATION_READY**

**Recomendación: P2T-0: COMMON SYMPATHETIC / ARRIVAL-HR GAP AUDIT (read-only); no further executable physiology**
<!-- /generado:veredicto -->

## 18. Lo que esta migración enseña (para la docencia)

1. **La interfaz común de mecánica funciona.** Una sola fuente de la familia (la obstrucción) mueve la eficiencia común,
   y la ventilación, la PaCO2 y el pH responden por la física común. No hizo falta ninguna ecuación del asma en el
   núcleo, ni tocar la disponibilidad central, el impulso, G o L.
2. **La diferencia entre el asma grave y la compensada es de severidad, no de fisiología.** La banda del 49m está por
   debajo de la del 24f a cada FR intrínseca común, y la misma forma da hipercapnia en uno y una PaCO2 menor en el otro.
3. **El impulso es ahora el eslabón que bloquea, y es común.**
   - Sin el ancla de llegada, la FR baja que da el núcleo, sin un impulso excitador no químico (distrés,
     mecanorreceptores), se convierte en una PaCO2 de llegada muy alta: 49m 95,6 frente a 51, y el 24f deja de estar
     compensado. Lo mismo ya se veía en la FR del edema y del TEP.
   - Que la mecánica mapeada devuelva la PaCO2 autoral con la FR autoral es una identidad del mapeo, no una prueba.
   - Para que el núcleo dé la PaCO2 autoral con su propia FR, harían falta E de 0,784 (49m) y 0,954 (24f). Esa segunda
     cifra contradice el flujo pico del 35 %: absorber la brecha en la mecánica sería un error semántico.
   - Fuentes en tensión, que dejo señaladas para decisión: P2S-2 recomendó mapear la disponibilidad y el impulso
     excitador antes que la mecánica, y el mandato de P2S-3 fija el impulso sin cambios.
4. **Parte del contraste viene del impulso ácido, no de la mecánica.**
   - El HCO3 20,8 del 24f da una carga ácida que sube su FR del núcleo a 21,6; con HCO3 24 su PaCO2 sería 65,9.
   - En el curso sin empeoramiento, esa carga se aclara (FR 21,6 → 18,2 y PaCO2 48,7 → 57,8 en 120 min). Por eso el
     curso del 24f no es estacionario.
5. **La hipoxemia no se explica entera.** En el 49m, unos 14 mmHg de la caída de la PO2 alveolar son hipoventilación, y
   el núcleo no baja la SpO2 cuando sube la PaCO2 (enlace diferido).

## 19. Proceso

- Duración: inicio 20:25 UTC (tras publicar P2S-2); congelación `2c055ca` a las 20:38; evaluación única a las 20:38
  (5 s); revisión 20:39–20:50.
- Los borradores se escribieron fuera del repositorio mientras corría la suite de P2S-2. Durante el desarrollo, el
  análisis se ejecutó para depurar. Las correcciones fueron de efecto dominó o de estructura: la vista de las fuentes
  capturadas por P2S-2 y la referencia sin importar módulos de análisis. Ningún valor predeclarado cambió.
- Pruebas de Fase 2 antes de congelar: 4 particiones, 1 786 pruebas; 17 fallaron por efecto dominó, se adaptaron y las
  reejecuciones pasaron (291 pruebas).
- Una sola evaluación, una sola revisión adversarial y una sola certificación final.

## 20. Revisión adversarial

Una revisión, independiente y de sólo lectura, sobre el candidato congelado y evaluado: 1 hallazgo alto, 2 medios y 8
bajos.

1. **Alto: el READY descansa en identidades.**
   - `mapping_coherent`, `paco2_at_authored_rr`, `bias_is_the_rr_ratio`, `secondary_hypocapnic_at_authored_rr` y
     `mechanics_ordered` se cumplen por construcción: la E se invierte de la FR y la PaCO2 autorales.
   - La única comprobación del núcleo sobre la compensación del 24f (`secondary_hypocapnic_in_core`) falla en los tres
     puntos y quedaba fuera del criterio.
   - Representar la llegada exige un cambio común (un impulso excitador no químico). Eso es COMMON_CORE_BLOCKER_FOUND,
     y `verdict()` no tenía camino para devolverlo.
   - No se señaló la tensión con la recomendación de P2S-2.
   - **Aceptado:** la clasificación del paquete pasa a NOT_READY — COMMON_CORE_BLOCKER_FOUND (§17). No se vuelve a
     congelar.
2. **Medio: casi la mitad de la separación de PaCO2 entre los casos viene del impulso ácido del 24f**, no de la
   mecánica. Aceptado; §18.4.
3. **Medio: el curso del 24f sin empeoramiento no es estacionario** (se aclara su carga ácida). Las direcciones se
   comparan contra ese curso, que deriva. Aceptado; §18.4.
4. **Bajo: `anchors()` empareja en silencio una E con otra FR intrínseca** si se cambia sólo una de las dos, y falla
   con campos explícitos duplicados. Ningún llamador actual lo hace. Queda como deuda.
5. **Bajo: constantes presentadas como resultados** (`same_profile_and_equations`, `used_for_parameters`, `used`). Queda
   como deuda.
6. **Bajo: el criterio de la FC sólo comprueba que las ganancias están intactas.** Queda como deuda.
7. **Bajo: tablas del informe en orden lexicográfico.** Corregido en el informe, que no está congelado.
8. **Bajo: la etiqueta LATENT_ARRIVAL_STATE se pierde en `ARRIVAL_CLASSES`.** Queda como deuda.
9. **Bajo: la banda no usa la severidad clínica ni el flujo pico.** Sólo expresa la incertidumbre de la FR intrínseca.
   Queda como deuda.
10. **Bajo: la recomendación no nombraba la brecha del impulso.** Corregido aquí y en §64.
11. **Bajo: una prueba fija el defecto (24f no hipocápnico en el núcleo) como invariante.** Queda como deuda: deberá
    cambiar cuando exista el impulso.

Verificado sin hallazgos:

- ningún cambio del núcleo común (115 hashes y 2 reversiones);
- el escritor sólo escribe la mecánica;
- la PaCO2 no está anclada;
- disponibilidad 1 e hipoxémico UNSET;
- sin G ni L;
- la aritmética alveolar no la lee nada;
- el alivio no programa observables;
- la FC no se parchea y el legado no se usa;
- la tasa y la banda coinciden con lo congelado;
- la vista y la cadena son sólidas.

## 21. Limitaciones

- Ningún valor clínico está aprobado:
  - la región de llegada de la mecánica es FAMILY_CANDIDATE;
  - la tasa de empeoramiento y el alivio son SYNTHETIC_ONLY;
  - el gas alveolar es sólo un diagnóstico.
- La FR de llegada del núcleo no reproduce la autoral sin un impulso excitador no químico (brecha común). Sin el ancla de
  PaCO2, esa brecha pasa a la PaCO2 de llegada: la hipocapnia compensada del 24f no aparece con la FR del núcleo.
- No hay escritor de broncodilatador ni de esteroide, ni estado de fatiga. La hipoventilación no baja la SpO2.
- La FC de llegada no se reproduce; el uso previo de β-agonista es un factor de confusión propio del asma.
- La conciencia no lee la PaCO2 (P2L-2 no está integrado).
