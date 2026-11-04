# P2Q-2 · Migración en sombra del TEP / shock obstructivo

Paquete de migración de familia sobre el núcleo común cerrado. No rediseña el núcleo: ningún archivo de fisiología común
cambia (§21–§22). Rama `phase-2-clinical-core-shadow`; base `2a44327` (P2P-2 aceptado y cerrado).

- Casos: primario `pulmonary_embolism_61m` (TEP de alto riesgo con shock obstructivo); secundario diagnóstico
  `pulmonary_embolism_33f` (TEP con hipoxemia, sin hipotensión inicial).
- Módulos: `clinical_core/modules/pulmonary_embolism.py` (escritores de familia), `clinical_core/embolism_reference.py`
  (verdad y mapeo de llegada) y `clinical_core/embolism_migration.py` (análisis, congelado antes de evaluar).
- Registro: `docs/revision/P2Q2_pulmonary_embolism.json`. Este documento se genera desde el registro
  (`clinical_core/embolism_migration_report.py`); el texto fuera de los marcadores es la narrativa.

## 1. Decisiones docentes que rigen

- P2Q-1 aceptado: TRUE_CROSS_FAMILY_CONFLICT para el acoplamiento común de congestión sin lado; queda resuelto para esta
  migración por autoridad de familia.
- **PE_L_ZERO_OWNER_AUTHORIZED:** la familia del TEP es la dueña de L (`lung_water_authority`) con generación propia cero,
  salvo edema pulmonar autoral independiente. Suprime el escritor común provisional de sobrecarga. Un solo dueño de L por
  corrida (P2O-3).
- **IVC_IS_NOT_UNIVERSAL_V_MAPPING:** V (precarga anterógrada efectiva) se lee del VI pequeño e hipollenado; la VCI
  pletórica es evidencia del lado derecho, sólo observacional.
- **SIDED_PRELOAD_COMMON_STATE_DEFERRED:** ningún estado común con lado (precarga de VD o VI, presiones auriculares, PCWP,
  P o V con lado).
- Sin doble conteo de la obstrucción en V y P; G directa sin semántica de L_rev; respuesta común al O2; P2P-2 sólo
  estructural (mapeo hipoxémico UNSET o SYNTHETIC_ONLY); sin compensación presión → tono; sin reajuste de FC; D de llegada
  latente, nunca desde el lactato; colapso sólo estructural.

## 2. Verdad del repositorio (P2Q-2-1)

Leída del banco de casos por ruta (`embolism_reference.TRUTH_PATHS`), nunca retipeada. Clases: AUTHORED_CASE_TRUTH (todo
lo del banco), LEGACY_ENGINE_BEHAVIOR (la penalización del volumen rápido de `pe_obstruction` declarada en TDFC F1) y
MODEL_DERIVED (FC y FR predichas, aporte y deuda de llegada).

<!-- generado:caso -->
- **`pulmonary_embolism_33f`:** «Acute pulmonary embolism with hypoxemia, initially without hypotension». PA 110/70, FC 124 (Sinus tachycardia), SpO2 90 % aire ambiente, FR 30, trabajo respiratorio «Increased», llenado capilar 3 s, extremidades «Warm», perfusión «preserved», «Alert». Gases arteriales 7.47 / PaCO2 30 / PaO2 59, HCO3 21.1; lactato 2.0; Hb 12.6; troponina 31; ECG `baseline`.
  - POCUS: VD «Mildly enlarged, approximately equal to the LV; no septal flattening (no D-sign); no McConnell sign»; VI «Preserved contraction»; VCI «2.0 cm; <50% inspiratory collapse»; pulmones «No B-lines; A-line pattern bilaterally»; poplítea «Non-compressible on the operated (symptomatic) side, with echogenic intraluminal material; compressible on the other side». Radiografía «No focal consolidation, edema or pneumothorax.». Angio-TC «Acute lobar and segmental filling defects in the right and left pulmonary arteries. Mild RV enlargement.».
  - Exploración: «Regular tachycardia; no new murmur.»; «Increased effort; breath sounds are equal without focal crackles or wheeze.». Inicio: «The breathing and chest discomfort started abruptly about two hours ago.». Tratamientos definitivos autorales: anticoagulation, consult, oxygen.
- **`pulmonary_embolism_61m`:** «High-risk pulmonary embolism with obstructive shock». PA 86/54, FC 132 (Sinus tachycardia), SpO2 88 % aire ambiente, FR 32, trabajo respiratorio «Markedly increased», llenado capilar 5 s, extremidades «Cool», perfusión «impaired», «Alert». Gases arteriales 7.43 / PaCO2 28 / PaO2 55, HCO3 18.0; lactato 4.8; Hb 11.6; troponina 76; ECG `right_strain`.
  - POCUS: VD «Larger than the LV; septal flattening with a D-shaped LV; reduced free-wall contraction with apical sparing (McConnell sign)»; VI «Small, underfilled cavity with vigorous contraction»; VCI «2.3 cm; minimal inspiratory collapse»; pulmones «No B-lines; A-line pattern bilaterally»; poplítea «Left popliteal vein non-compressible; right popliteal vein compressible». Radiografía «No focal consolidation or pulmonary edema.». Angio-TC «Extensive acute bilateral main and lobar pulmonary arterial filling defects with RV enlargement and septal flattening.».
  - Exploración: «Rapid regular pulse; elevated jugular venous pressure.»; «Marked respiratory effort with equal breath sounds and no widespread crackles.». Inicio: «The severe breathlessness and near-collapse began about 45 minutes ago.». Tratamientos definitivos autorales: anticoagulation, consult, oxygen.
- **Regla de selección:** primary: the variant with the richest authored RV, preload, gas-exchange and haemodynamic physiology (pulmonary_embolism_61m, high-risk PE with obstructive shock); secondary diagnostic: pulmonary_embolism_33f (PE with hypoxaemia, initially without hypotension).
- **Observaciones posteriores:** NONE_AUTHORED: both cases state the arrival only; the TDFC declarations and the assessment bank describe the expected management (oxygen, anticoagulation, a reperfusion-capable team, cautious bounded volume), not a physiological course.
- **Comportamiento heredado (sólo referencia):** pe_obstruction (TOLERATED_ML_PER_MIN 10, RV_STRAIN_PER_ML 0.0006, RV_STRAIN_TAU_MIN 45, RV_STRAIN_LUNG_SHARE 0.35, lysis targets 0.62 / 0.80): LEGACY_ENGINE_BEHAVIOR.
- Verdad suficiente (todos los ítems leídos): sí.
<!-- /generado:caso -->

## 3. Mapa de canales y mapeo de llegada (P2Q-2-2, P2Q-2-15)

V es la posición de llegada en la curva de precarga, leída sólo del VI (`V_EVIDENCE = pocus_lv`). Cuando el VI se lee
hipollenado, la banda va desde el punto más profundo de subllenado de GI (0,2) hasta la posición neutra (0,5), con punto
medio 0,35. Es FAMILY_CANDIDATE: de GI sólo se toma la escala, porque sus bandas también leían una VCI colapsada en
casos hipovolémicos y no se transfieren como tales; la magnitud queda para decisión docente. El secundario, con VI
conservado, queda en la posición provisional del perfil, sin declarar. La VCI, las yugulares y el VD son observaciones del lado derecho
y no entran en V, L ni en la reserva. El aporte y la deuda de llegada (sólo el primario, con perfusión alterada) son
estados latentes por las reglas de GI, nunca calculados desde el lactato.

<!-- generado:llegada -->
| Canal | Papel |
|---|---|
| D | SECONDARY_RESPONSE (obstructive shock: a latent arrival debt, never from the lactate 4.8) |
| G | PRIMARY_DRIVER (dead space / V/Q mismatch: SpO2 88, PaO2 55 on room air): direct, never through L |
| Glu | NORMAL_OR_NEUTRAL (136: stress) |
| Hb | NORMAL_OR_NEUTRAL (11.6) |
| K | NORMAL_OR_NEUTRAL (4.1) |
| L | NORMAL_OR_NEUTRAL (no B-lines, no edema on the radiograph): family-owned at zero generation |
| N | NORMAL_OR_NEUTRAL (alert, faint) |
| P | PRIMARY_DRIVER (the obstruction: unsided forward-flow capacity of the series circuit; not LV contractility, the authored LV contracts vigorously) |
| R | SECONDARY_RESPONSE (sinus tachycardia 132) |
| T | SECONDARY_RESPONSE (vasoconstriction: the existing common tone response to the deficit) |
| V | NORMAL_OR_NEUTRAL as a deviation (V = 0 at arrival; no volume lost or gained); its arrival POSITION is the underfilled LV's (low on the preload curve). Never the plethoric IVC (IVC_IS_NOT_UNIVERSAL_V_MAPPING) |
| W | SECONDARY_RESPONSE (RR 32, markedly increased work, PaCO2 28: hyperventilation) |

| Banda | Inferior | Punto medio | Superior | Clase |
|---|---|---|---|---|
| arrival_delivery_ratio | 0,240 | 0,340 | 0,400 | FAMILY_CANDIDATE |
| arrival_lactate_excess | 2,800 | 3,800 | 4,000 | CASE_MAPPING |
| arrival_oxygen_debt | 0,000 | 20,000 | 60,000 | FAMILY_CANDIDATE |
| intrinsic_sinus_rate | 60,000 | 80,000 | 100,000 | CASE_MAPPING |
| preload_fraction | 0,200 | 0,350 | 0,500 | FAMILY_CANDIDATE |

| Ítem | Núcleo | Autoral | Exacto |
|---|---|---|---|
| sbp | 86,00 | 86,00 | sí |
| dbp | 54,00 | 54,00 | sí |
| map | 64,67 | 64,67 | sí |
| spo2 | 88,00 | 88,00 | sí |
| paco2 | 28,00 | 28,00 | sí |
| lactate | 4,80 | 4,80 | sí |
| consciousness_level | 0,00 | 0,00 | sí |
| pH | 7,431 | 7,43 | redondeo: sí |

- Reconstrucción de llegada: exact (SBP, DBP, SpO2, CRT, lactate, consciousness level).
- Posición de precarga de llegada 0,35 (por defecto 0,50), leída del VI (`pocus_lv`; VI hipollenado: sí). VCI «2.3 cm; minimal inspiratory collapse»: RIGHT_SIDED / OBSERVATIONAL (not mapped).
- Reserva de bomba 1,0 (neutra); L_rev 0,0; edema pulmonar autoral: no; generación propia de L 0,0.
- La posición de llegada no cambia nada de la llegada (puntos 0,20, 0,35, 0,50, 0,50, 0,80): sí.
<!-- /generado:llegada -->

## 4. Escritores de familia (P2Q-2-3, P2Q-2-4, P2Q-2-6)

Antes de escribir código se clasificó el blanco del escritor de obstrucción:

- **V queda descartado** como blanco del escritor: en el núcleo V sólo lo mueve el estado sanguíneo compartido (P2I-2T,
  `BLOOD_CHANNELS`). Bajarlo sin pérdida de sangre sería una hemorragia falsa (corrupción semántica). El subllenado del
  VI entra como posición de llegada, no como escritura.
- **P es el blanco:** P es la capacidad de flujo anterógrado del circuito en serie, sin lado (arrival = 1). Sus lectores
  en el núcleo son el gasto (multiplicativo), la forma de la curva de precarga (escala × P^c: menos ganancia por mL) y la
  falta de reserva de la congestión común. Esta última es la única semántica izquierda, y la autoridad de L la apaga.
  El VI autoral contrae vigorosamente: P no se interpreta como contractilidad del VI.
- **No hace falta un estado nuevo** (NEW_COMMON_STATE_REQUIRED no aplica).

<!-- generado:escritores -->
| Escritor | Escribe | Lee del estado | Autoridad sobre L |
|---|---|---|---|
| `EmbolicGasExchange` | G | R | no |
| `EmbolicLungWater` | L | R | sí |
| `ObstructiveForwardFlow` | P | P, R | no |

- Escribe V: no; nombres prohibidos usados: ninguno; código opioide: no.
- Registrados y reproducibles: sí; el dueño con tasa cero no escribe: sí; rechazos: floor_above_one sí, floor_zero sí, nan_g sí, negative_g sí, negative_l sí, negative_loss sí.
- Cumple: sí.
<!-- /generado:escritores -->

## 5. Obstrucción por el núcleo común y curso sin tratamiento (P2Q-2-3, P2Q-2-19)

Tramo predeclarado: la escala congelada del escritor isquémico de ACS sobre el mismo canal P (0,05 / 0,10 / 0,20 por hora,
piso 0,5). G directa: la sonda de TEP de P2O-1 (0,025 por minuto) como tope, dividida por dos dos veces. Ninguno se ajusta:
no hay curso autoral posterior a la llegada.

<!-- generado:obstruccion -->
Obstrucción sola (con el dueño de L), por punto del tramo:

| Pérdida de P / min | P 120 | Gasto 120 | PAM 120 | Aporte 120 | Déficit 120 | D 120 | V = 0 | L = 0 |
|---|---|---|---|---|---|---|---|---|
| 0.000833333 | 0,900 | 0,888 | 60,0 | 0,302 | 0,245 | 43,7 | sí | sí |
| 0.00166667 | 0,800 | 0,780 | 54,8 | 0,265 | 0,337 | 49,2 | sí | sí |
| 0.00333333 | 0,600 | 0,571 | 43,1 | 0,194 | 0,514 | 60,1 | sí | sí |

Cumple: sí.

Curso de referencia sin tratamiento (todos los escritores en el punto medio), hasta 240 min:

| Minuto | P | G | Gasto | PAM | Aporte | Déficit | D | Lactato | FC | T | SpO2 | FR | Conciencia |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1,000 | 0,000 | 1,000 | 64,7 | 0,340 | 0,150 | 20,0 | 4,80 | 95,6 | 1,000 | 88,0 | 25,5 | 0 |
| 30 | 0,950 | 0,375 | 0,942 | 62,7 | 0,313 | 0,217 | 25,5 | 4,10 | 100,0 | 1,030 | 86,1 | 24,8 | 1 |
| 60 | 0,900 | 0,750 | 0,884 | 60,6 | 0,288 | 0,280 | 32,9 | 3,60 | 104,7 | 1,060 | 84,2 | 24,7 | 1 |
| 90 | 0,850 | 1,125 | 0,828 | 58,3 | 0,264 | 0,341 | 42,2 | 3,27 | 109,7 | 1,088 | 82,4 | 24,9 | 1 |
| 120 | 0,800 | 1,500 | 0,773 | 55,8 | 0,241 | 0,399 | 53,3 | 3,08 | 114,8 | 1,115 | 80,5 | 25,4 | 1 |
| 180 | 0,700 | 2,250 | 0,667 | 50,2 | 0,198 | 0,505 | 80,4 | 3,04 | 125,4 | 1,165 | 76,8 | 26,8 | 2 |
| 240 | 0,600 | 3,000 | 0,565 | 44,2 | 0,159 | 0,602 | 113,6 | 3,37 | 135,6 | 1,209 | 73,0 | 28,4 | 2 |

Canales escritos por la familia: G, P; escrituras del acoplamiento común de sobrecarga: 0; L máximo 0,000; V máximo 0,000; pulso conservado: sí.
<!-- /generado:obstruccion -->

## 6. Sin doble conteo V / P

<!-- generado:doble_conteo -->
- Fuentes de V sin tratamiento: ninguna; con el bolo: intervention:pe-fluid-stress.
- Fuentes de P: disease_module:pe-obstruction (con el bolo: disease_module:pe-obstruction).
- Canales de la familia: G, P.
- La posición de llegada no cambia la llegada: sí.
- El mapeo de V lee: pocus_lv; lee el lado derecho (VCI, yugulares, VD): no.
- Cumple: sí.
<!-- /generado:doble_conteo -->

## 7. Dueño de L con generación cero (P2Q-2-4)

<!-- generado:dueno_l -->
- Con el dueño (mapeo del VI, obstrucción, G y bolo): escrituras comunes 0, escrituras de L 0, L máximo 0,000.
- Con el dueño en el mapeo rechazado de la VCI (0,8): escrituras comunes 0, L máximo 0,000.
- Contrafáctico sin dueño en el mapeo rechazado de la VCI: 73 escrituras comunes, L máximo 0,066, SpO2 final 80,17 (el conflicto de P2Q-1, reproducido).
- Contrafáctico sin dueño en el mapeo del VI: 0 escrituras, L máximo 0,000, posición máxima 0,521 (rodilla 0,85).
- Segundo dueño rechazado: sí; generación propia: `pulmonary_embolism_33f` 0,0, `pulmonary_embolism_61m` 0,0.
- Cumple: sí.
<!-- /generado:dueno_l -->

## 8. Estrés de fluidos (P2Q-2-5)

<!-- generado:fluidos -->
Bolo SYNTHETIC_ONLY de 2000 mL desde el minuto 30 en 30 min, con obstrucción, G y el dueño de L.

| Punto de la banda | Precarga | Minuto | Gasto sin | Gasto con | Ganancia | Ganancia sin obstrucción | Ganancia de PAM | Posición con | SpO2 sin / con | L máx | Escrituras comunes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| lower | 0,20 | 60 | 0,884 | 1,661 | 0,777 | 0,873 | 39,3 | 0,397 | 84,25 / 84,25 | 0,000 | 0 |
| lower | 0,20 | 120 | 0,773 | 1,196 | 0,423 | 0,549 | 19,5 | 0,361 | 80,50 / 80,50 | 0,000 | 0 |
| midpoint | 0,35 | 60 | 0,884 | 1,254 | 0,370 | 0,420 | 16,0 | 0,521 | 84,25 / 84,25 | 0,000 | 0 |
| midpoint | 0,35 | 120 | 0,773 | 0,958 | 0,185 | 0,263 | 9,7 | 0,507 | 80,50 / 80,50 | 0,000 | 0 |
| upper | 0,50 | 60 | 0,884 | 1,074 | 0,190 | 0,229 | 9,4 | 0,642 | 84,25 / 84,25 | 0,000 | 0 |
| upper | 0,50 | 120 | 0,773 | 0,867 | 0,094 | 0,138 | 5,3 | 0,645 | 80,50 / 80,50 | 0,000 | 0 |

Respuesta menor que sin obstrucción: lower sí, midpoint sí, upper sí. SpO2 y G no cambian con el bolo en ningún punto. Sin el dueño (contrafáctico, sólo informado): lower: 0 escrituras, L máx 0,000, posición máx 0,397, midpoint: 0 escrituras, L máx 0,000, posición máx 0,521, upper: 0 escrituras, L máx 0,000, posición máx 0,645. Cumple: sí.
<!-- /generado:fluidos -->

Lectura:

- No aparece L falso en ningún punto de la banda, y la SpO2 no cambia por el volumen.
- El gasto responde menos que sin obstrucción, porque P encoge la curva.
- En el punto bajo de la banda (0,2), sin embargo, el bolo sintético eleva mucho el gasto (1,66 veces el de llegada al
  terminar la infusión). El núcleo sin lado no representa la interdependencia ventricular ni el daño del volumen sobre el
  VD que el legado penaliza. No se ajusta nada; queda como evidencia para P2R-0 (lateralidad de la precarga).
- Este criterio no discrimina por sí solo: con el mapeo del VI la posición no llega a la rodilla de la congestión común
  ni siquiera sin el dueño (contrafáctico por punto). La necesidad del dueño se demuestra en el contrafáctico de la VCI
  rechazada (§7), que reproduce el edema falso de P2Q-1.

## 9. G directa sin crédito de L_rev (P2Q-2-6)

<!-- generado:g_directa -->
| G / min | G 120 | SpO2 120 | Aporte 120 | Lineal | Mapeo común | Sin crédito L_rev | L_rev −0,5 no cambia |
|---|---|---|---|---|---|---|---|
| 0.00625 | 0,750 | 84,25 | 0,324 | sí | sí | sí | sí |
| 0.0125 | 1,500 | 80,50 | 0,308 | sí | sí | sí | sí |
| 0.025 | 3,000 | 73,00 | 0,276 | sí | sí | sí | sí |

Cumple: sí.
<!-- /generado:g_directa -->

## 10. Oxígeno (P2Q-2-7)

<!-- generado:oxigeno -->
| Minuto | Aire ambiente | FiO2 0,4 | FiO2 0,6 |
|---|---|---|---|
| 0 | 88,00 | 88,00 | 88,00 |
| 30 | 86,12 | 90,92 | 95,98 |
| 60 | 84,25 | 88,40 | 92,76 |
| 90 | 82,38 | 86,02 | 89,86 |
| 120 | 80,50 | 83,76 | 87,19 |

- Monótona en FiO2 cada minuto: sí; ganancia de FiO2 0,6 a los 30 min 9,85 y a los 120 6,69 (atenuada al empeorar G: sí); función de oxígeno de la familia: no.
- Cumple: sí.
<!-- /generado:oxigeno -->

## 11. Impulso respiratorio (P2Q-2-8)

<!-- generado:impulso -->
| Minuto | Impulso ácido | Hipoxémico UNSET | Hipoxémico sintético | FR UNSET | FR sintética |
|---|---|---|---|---|---|
| 0 | 12,00 | 0,00 | 2,40 | 25,53 | 26,95 |
| 30 | 10,92 | 0,00 | 2,77 | 24,85 | 26,54 |
| 60 | 10,64 | 0,00 | 3,15 | 24,67 | 26,60 |
| 90 | 10,96 | 0,00 | 3,52 | 24,87 | 26,99 |
| 120 | 11,72 | 0,00 | 3,90 | 25,35 | 27,61 |

- FR autoral 32; FR de llegada UNSET 25,53 (brecha 6,47), sintética 26,95 (brecha 5,05).
- UNSET no da impulso hipoxémico: sí; el sintético impulsa en la llegada: sí y crece al empeorar G: sí; estados idénticos (la FR no realimenta nada): sí; la familia escribe W: no.
- Parámetros: UNSET by default; SYNTHETIC_ONLY here (P2P-2's); UNSET by default; SYNTHETIC_ONLY 10 here; elegido del TEP: no.
- Cumple: sí.
<!-- /generado:impulso -->

## 12. Guarda de depresión central (P2Q-2-9)

<!-- generado:depresion -->
| Minuto | FR intacta | FR deprimida | PaCO2 intacta | PaCO2 deprimida |
|---|---|---|---|---|
| 0 | 26,95 | 8,08 | 26,5 | 88,4 |
| 30 | 26,54 | 7,96 | 26,9 | 89,8 |
| 60 | 26,60 | 7,98 | 26,9 | 89,6 |
| 90 | 26,99 | 8,10 | 26,5 | 88,3 |
| 120 | 27,61 | 8,28 | 25,9 | 86,3 |

- Disponibilidad 0,30, cota 12,30: en o bajo la intrínseca sí, dentro de la cota sí, PaCO2 mayor sí, impulso hipoxémico igual sí, estados idénticos sí, archivo de la composición sin cambios sí.
- Cumple: sí.
<!-- /generado:depresion -->

## 13. Tono y barorreflejo (P2Q-2-10)

<!-- generado:tono -->
| Ganancia de tono | T 120 | Gasto 120 | PAM 120 | Déficit 120 | D 120 |
|---|---|---|---|---|---|
| 0.25 | 1,057 | 0,787 | 53,8 | 0,388 | 52,6 |
| 0.5 | 1,115 | 0,773 | 55,8 | 0,399 | 53,3 |
| 1 | 1,232 | 0,748 | 59,6 | 0,418 | 54,7 |

- A los 120 min (ganancia 0,50): T 11,5 %, gasto −22,7 %, PAM −13,8 %.
- La familia escribe T: no; ganancias sin tocar: sí.
- CROSS_FAMILY_COMMON_REFINEMENT_EVIDENCE_INCREASED (the missing pressure -> tone compensation, now independently in ACS and PE); P2J not reopened.
- Cumple: sí.
<!-- /generado:tono -->

## 14. Brecha de FC de llegada (P2Q-2-11)

<!-- generado:fc -->
| Caso | FC autoral | FC predicha | Desajuste | Predicha sobre las bandas | Autoral dentro |
|---|---|---|---|---|---|
| `pulmonary_embolism_33f` | 124 | 81,9 | −42,1 | 61,9 / 81,9 / 101,9 | no |
| `pulmonary_embolism_61m` | 132 | 95,6 | −36,4 | 76,9 / 95,6 / 121,4 | no |

- MULTI_FAMILY_COMMON_HR_GAP (ACS, pulmonary edema, PE): the arrival sympathetic share is not reproduced; no arrival hypoxaemia, distress, pain or RV-load term; not retuned.
- La FC sube con el deterioro: sí; ganancias sin tocar: sí.
<!-- /generado:fc -->

## 15. D y lactato (P2Q-2-12)

<!-- generado:d_lactato -->
| Minuto | D | Lactato |
|---|---|---|
| 0 | 20,0 | 4,80 |
| 30 | 25,5 | 4,10 |
| 60 | 32,9 | 3,60 |
| 90 | 42,2 | 3,27 |
| 120 | 53,3 | 3,08 |
| 180 | 80,4 | 3,04 |
| 240 | 113,6 | 3,37 |

- D de llegada 20,0 (banda 0–60, FAMILY_CANDIDATE); no depende del lactato: sí; secundario 0,0.
- Lactato del núcleo cada minuto: sí; sin escritura de la familia: sí; cinéticas sin tocar: sí.
- El exceso de llegada se aclara antes de que domine la deuda nueva: sí; mínimo en el minuto 155; vuelve a subir después: sí. No se fuerza la monotonía.
<!-- /generado:d_lactato -->

## 16. Colapso (P2Q-2-13)

<!-- generado:colapso -->
| Minuto | PAM | Señal de aporte | Perfusión UNSET | Perfusión estructural | Señal | max |
|---|---|---|---|---|---|---|
| 0 | 64,7 | 0,150 | — | 0,935 | 0,935 | sí |
| 60 | 60,6 | 0,280 | — | 0,939 | 0,939 | sí |
| 120 | 55,8 | 0,399 | — | 0,944 | 0,944 | sí |
| 240 | 44,2 | 0,602 | — | 0,956 | 0,956 | sí |

- La señal de falla de aporte sube: sí; la de perfusión estructural sube: sí; UNSET sigue siendo cota inferior: sí; sin regla de familia en la capa: sí.
- Activa: no; umbrales elegidos: no; transición terminal: no.
- Cumple: sí.
<!-- /generado:colapso -->

## 17. Caso secundario (P2Q-2-14)

<!-- generado:secundario -->
| Ítem | Núcleo | Autoral | Exacto |
|---|---|---|---|
| sbp | 110,00 | 110,00 | sí |
| dbp | 70,00 | 70,00 | sí |
| map | 83,33 | 83,33 | sí |
| spo2 | 90,00 | 90,00 | sí |
| paco2 | 30,00 | 30,00 | sí |
| lactate | 2,00 | 2,00 | sí |
| consciousness_level | 0,00 | 0,00 | sí |
| pH | 7,470 | 7,47 | redondeo: sí |

Llegada coherente: sí.

| Pérdida de P / min | Minuto | SpO2 | PAM | Gasto | FC | Lactato | D | Conciencia |
|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 90,00 | 83,3 | 1,000 | 81,9 | 2,00 | 0,0 | 0 |
| 0 | 30 | 88,12 | 83,3 | 1,000 | 82,8 | 1,78 | 0,0 | 0 |
| 0 | 60 | 86,25 | 83,3 | 1,000 | 83,7 | 1,61 | 0,0 | 1 |
| 0 | 90 | 84,38 | 83,3 | 1,000 | 84,7 | 1,47 | 0,0 | 1 |
| 0 | 120 | 82,50 | 83,3 | 1,000 | 85,6 | 1,37 | 0,0 | 1 |
| 0.000833333 | 0 | 90,00 | 83,3 | 1,000 | 81,9 | 2,00 | 0,0 | 0 |
| 0.000833333 | 30 | 88,12 | 81,2 | 0,975 | 83,4 | 1,78 | 0,0 | 0 |
| 0.000833333 | 60 | 86,25 | 79,2 | 0,950 | 84,9 | 1,61 | 0,0 | 1 |
| 0.000833333 | 90 | 84,38 | 77,1 | 0,925 | 86,4 | 1,47 | 0,0 | 1 |
| 0.000833333 | 120 | 82,50 | 75,0 | 0,900 | 87,9 | 1,37 | 0,0 | 1 |

Hipoxemia sin hipotensión (sólo G): sí. Cumple: sí.
<!-- /generado:secundario -->

## 18. Reconstrucción de observables de llegada (P2Q-2-15)

<!-- generado:observables -->
**`pulmonary_embolism_33f`** (contradicciones: ninguna):

| Ítem | Autoral | Núcleo | Estado |
|---|---|---|---|
| dbp | 70 | 70,00 | EXACT_ANCHORED |
| hr | 124 | 81,85 | GAP: MULTI_FAMILY_COMMON_HR_GAP (outside the mapped bands) |
| ivc | 2.0 cm; <50% inspiratory collapse | — | RIGHT_SIDED / OBSERVATIONAL (never V or L) |
| lactate | 2.0 | 2,00 | EXACT_ANCHORED |
| lungs | No B-lines; A-line pattern bilaterally | — | OBSERVATION_LAYER (L = 0, family-owned, zero generation) |
| lv | Preserved contraction | — | OBSERVATION_LAYER (the arrival preload position, V_EVIDENCE) |
| map | 83.33333333333333 | 83,33 | EXACT_ANCHORED |
| mental_status | Alert | 0 | EXACT_ANCHORED |
| paco2 | 30 | 30,00 | EXACT_ANCHORED |
| pao2 | 59 | — | NOT_MODELLED (the core carries SpO2, not PaO2) |
| ph | 7.47 | 7,47 | WITHIN_ROUNDING |
| rr | 30 | 21,18 | GAP: EXPECTED_RESPIRATORY_FAMILY_EXTENSION (no dead-space, mechanics or receptor drive; the hypoxaemic drive UNSET) |
| rv | Mildly enlarged, approximately equal to the LV; no septal flattening (no D-sign); no McConnell sign | — | OBSERVATION_LAYER (the obstruction, P = 1 at arrival) |
| sbp | 110 | 110,00 | EXACT_ANCHORED |
| spo2 | 90 | 90,00 | EXACT_ANCHORED |

**`pulmonary_embolism_61m`** (contradicciones: ninguna):

| Ítem | Autoral | Núcleo | Estado |
|---|---|---|---|
| dbp | 54 | 54,00 | EXACT_ANCHORED |
| hr | 132 | 95,64 | GAP: MULTI_FAMILY_COMMON_HR_GAP (outside the mapped bands) |
| ivc | 2.3 cm; minimal inspiratory collapse | — | RIGHT_SIDED / OBSERVATIONAL (never V or L) |
| lactate | 4.8 | 4,80 | EXACT_ANCHORED |
| lungs | No B-lines; A-line pattern bilaterally | — | OBSERVATION_LAYER (L = 0, family-owned, zero generation) |
| lv | Small, underfilled cavity with vigorous contraction | — | OBSERVATION_LAYER (the arrival preload position, V_EVIDENCE) |
| map | 64.66666666666667 | 64,67 | EXACT_ANCHORED |
| mental_status | Alert | 0 | EXACT_ANCHORED |
| paco2 | 28 | 28,00 | EXACT_ANCHORED |
| pao2 | 55 | — | NOT_MODELLED (the core carries SpO2, not PaO2) |
| ph | 7.43 | 7,43 | WITHIN_ROUNDING |
| rr | 32 | 25,53 | GAP: EXPECTED_RESPIRATORY_FAMILY_EXTENSION (no dead-space, mechanics or receptor drive; the hypoxaemic drive UNSET) |
| rv | Larger than the LV; septal flattening with a D-shaped LV; reduced free-wall contraction with apical sparing (McConnell sign) | — | OBSERVATION_LAYER (the obstruction, P = 1 at arrival) |
| sbp | 86 | 86,00 | EXACT_ANCHORED |
| spo2 | 88 | 88,00 | EXACT_ANCHORED |
<!-- /generado:observables -->

## 19. Legado, leído al final (P2Q-2-16)

<!-- generado:legado -->
| Minuto | Legado PA | Núcleo PA | Legado SpO2 | Núcleo SpO2 | Legado FC | Núcleo FC | Legado FR | Núcleo FR | Legado conciencia | Núcleo conciencia |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 86/54 | 86/54 | 88 | 88,0 | 132 | 95,6 | 32 | 25,5 | Alert | 0 |
| 60 | 83/53 | 81/51 | 88 | 84,2 | 133 | 104,7 | 33 | 24,7 | Alert | 1 |
| 120 | 81/51 | 74/47 | 87 | 80,5 | 135 | 114,8 | 33 | 25,4 | Alert | 1 |

- **bp_spo2_course:** LEGACY_DIFFERENCE_NOT_CLINICALLY_RELEVANT: both worsen untreated; the size is the family span's (the ACS P scale, P2O-1's G scale) and the legacy drift's, neither authored
- **consciousness:** POSSIBLE_COMMON_CORE_GAP: the legacy stays alert; derive's ADOPTED absolute SpO2 ladder (87 / 80) reads the worsening SpO2 as drowsy (ONE_HYPOXEMIA_CONSCIOUSNESS_SOURCE_ONLY, shared with pulmonary edema)
- **hr:** POSSIBLE_COMMON_CORE_GAP: the legacy shows the authored HR and lets it drift; the core's arrival HR is the common physiology's (MULTI_FAMILY_COMMON_HR_GAP); it rises with the deficit afterwards
- **rapid_volume:** EXPECTED_EXTENSION: the legacy punishes volume above 10 mL/min (RV strain, part of it as worse oxygenation); the core's unsided P gives a forward-flow response that may be limited, never harm: ventricular interdependence needs sided state (SIDED_PRELOAD_COMMON_STATE_DEFERRED)
- **rr:** EXPECTED_EXTENSION: the legacy holds the authored RR; the common RR is the P2P-2 composition with the hypoxaemic drive UNSET and no dead-space or mechanics drive
- **thrombolysis_reperfusion:** EXPECTED_EXTENSION: the legacy lysis and its bleeding are not migrated (reperfusion writer deferred)

Usado para parámetros: no.
<!-- /generado:legado -->

## 20. No regresión entre familias (P2Q-2-17)

<!-- generado:no_regresion -->
- acs_authority_r7: sí
- acs_evaluation: sí
- common_overload_r8: sí
- edema_authority: sí
- edema_heart_rate: sí
- edema_oxygen: sí
- edema_respiration: sí
- edema_untreated: sí
- gi_o12: sí
- p2p2_acidosis: sí
- p2p2_d1_d7_d9_d10: sí
- p2p2_edema_diagnostic: sí
- p2p2_opioid: sí
- Archivos comunes en sus bytes de P2P-2: 109 de 109.
- Cumple: sí.
<!-- /generado:no_regresion -->

## 21. Prueba contra el árbol de P2P-2

Los únicos archivos de `clinical_core` que cambian son las dos tuplas de registro (`lactate_slice.DOWNSTREAM_REPORTS`,
`decision_pack.PACK_DIGEST_EXCLUDED`), como en P2P-1. Se reconstruyen byte a byte como las dejó P2P-2. Todos los demás
archivos de `clinical_core` existentes en `2a44327` están fijados por su hash.

<!-- generado:prueba -->
- Tuplas reconstruidas byte a byte como las dejó P2P-2: `clinical_core/decision_pack.py` sí, `clinical_core/lactate_slice.py` sí.
- Archivos comunes sin cambios: 109 de 109.
- Digest de congelamiento de P2P-2 reproducido por la vista: sí; registro de P2P-2 intacto: sí.
<!-- /generado:prueba -->

## 22. Veredicto (P2Q-2-18)

Regla predeclarada: READY si se cumplen todos los criterios; si no, NOT_READY con el primer criterio que falla como
bloqueante. Las brechas de FC, FR, conciencia y tono, la forma del lactato y las diferencias con el legado se informan y
nunca deciden.

<!-- generado:veredicto -->
| Criterio | Cumple |
|---|---|
| D / lactate remain common (arrival D latent, never from lactate; lactate the core's; kinetics untouched) | sí |
| P2P-2 respiratory-drive architecture accepts hypoxaemia structurally (UNSET none, synthetic drives and grows; central depression still dominates) | sí |
| PE arrival mapping coherent (arrival exact where the core models it; V from the underfilled LV, the IVC not read; L 0; pump reserve neutral; the secondary neutral) | sí |
| PE owns L with zero generation (no common overload write, no L write; a second owner refused) | sí |
| collapse accepts the outputs structurally (signals rise, max holds, UNSET stays a lower bound, no family rule) | sí |
| direct G path works (G linear, the common SpO2 mapping, delivery down, no L_rev credit) | sí |
| fluid stress creates no false L (every LV-band point; SpO2 and G unchanged by the fluid) | sí |
| no V / P double counting (no PE source writes V or the blood state; the arrival position never changes the arrival; the V mapping reads only the LV) | sí |
| no prior family retuned (GI, ACS, pulmonary edema, P2P-2 reproduced; tone and HR gains untouched; every common file at its P2P-2 bytes; the P2P-2 tree proven) | sí |
| obstructive / forward-flow failure uses existing channels cleanly (the writer writes P only; Q, MAP, DO2, the deficit and D follow in the common core; V, Hb and L untouched) | sí |
| oxygen response common (monotone in FiO2, attenuated as G worsens, no family oxygen function) | sí |

**Veredicto:** `PE_SHADOW_MIGRATION_READY`.

**Recomendación:** `PROCEED_TO_P2R0_CROSS_FAMILY_GENERALIZATION_CHECKPOINT (read-only; do not tune PE)`.
<!-- /generado:veredicto -->

## 23. Brechas comunes repetidas (para P2R-0)

Datos para el punto de control, sin ordenar ni implementar nada:

<!-- generado:brechas -->
- **ARRIVAL_EXCESS_LACTATE_CLEARS_FIRST** (familias: pulmonary_edema, pulmonary_embolism): {"pe": true, "status": "reported, not a gap: the common kinetics are not retuned"}
- **MULTI_FAMILY_COMMON_HR_GAP** (familias: acs, pulmonary_edema, pulmonary_embolism): {"pe": {"pulmonary_embolism_33f": -42.148, "pulmonary_embolism_61m": -36.357}}
- **ONE_HYPOXEMIA_CONSCIOUSNESS_SOURCE** (familias: pulmonary_edema, pulmonary_embolism).
- **PRESSURE_TONE_COMPENSATION** (familias: acs, pulmonary_embolism): {"class": "CROSS_FAMILY_COMMON_REFINEMENT_EVIDENCE_INCREASED", "pe": {"T_change": 0.115, "map_change": -0.138, "output_change": -0.227}}
- **RESPIRATORY_DRIVE_AND_MECHANICS** (familias: pulmonary_edema, pulmonary_embolism): {"pe_arrival_rr_gap": {"synthetic": 5.054, "unset": 6.47}}
- **SIDED_PRELOAD_RIGHT_LEFT** (familias: pulmonary_embolism): {"status": "SIDED_PRELOAD_COMMON_STATE_DEFERRED: the false L is closed by family authority; ventricular interdependence (volume harm) is not representable"}
<!-- /generado:brechas -->

## 24. Proceso

- Auditoría de verdad y semántica (P2Q-2-1 a P2Q-2-3) antes de escribir código: blanco del escritor P, V descartado,
  ningún estado nuevo.
- Durante el desarrollo, el análisis completo se corrió en memoria para depurar el código (7 s). Fue una corrida de
  desarrollo previa al congelamiento: ningún criterio, tramo ni valor se cambió para que un resultado pasara. Los cambios
  previos al congelamiento vinieron sólo de la revisión adversarial (§25).
- Un solo congelamiento, `f26c877` (digest `6eabb721…`), y una sola evaluación sobre el árbol congelado, que escribió el
  registro. Este documento se genera desde ese registro.
- La certificación final (suite completa con Python 3.11, regresiones, golden, aislamiento y congelamiento del lector)
  corre una vez sobre el commit de evaluación.

## 25. Revisión adversarial

Una sola, independiente y de sólo lectura, sobre el candidato antes del congelamiento, con los focos del encargo. Dio dos
hallazgos medios y tres bajos, ninguno alto. Todos se corrigieron antes de congelar:

- **H1 (media):** la banda de V tomaba la envolvente de las bandas GI, construidas también con una VCI colapsada, y su
  tope (0,6) superaba la posición neutra.
  - Ahora sólo se toma el piso de la escala.
  - El tope es la posición neutra.
  - La clase es FAMILY_CANDIDATE y la magnitud, decisión docente.
- **H2 (media):** los controles de ganancias, cinéticas y D-desde-lactato no podían fallar.
  - Ahora comparan con el punto de ACS fijado por hash.
  - D se prueba reconstruyendo las anclas con el lactato duplicado.
  - Las sondas del revisor quedan como pruebas.
- **H3 (baja):** la lectura del edema autoral miraba prefijos. Ahora lee los tres textos de L por cláusulas y falla en
  cerrado.
- **H4 (baja):** el estrés de fluidos no discrimina por sí solo. Se informa el contrafáctico sin dueño por punto (§8).
- **H5 (baja):** la procedencia citaba artefactos de P2Q-1 que no están en el repositorio (aquella auditoría corrió en
  memoria). Los valores se declaran de nuevo, SYNTHETIC_ONLY, y se corrigió el nombre de la ganancia sintética.

Sin hallazgo, comprobado por el revisor:

- la VCI, el VD y las yugulares no llegan a las anclas;
- ninguna fuente del TEP escribe V ni flujos sanguíneos;
- el segundo dueño se rechaza por la razón correcta;
- todos los números están trazados;
- no hay D desde el lactato ni ganancias reajustadas;
- los 109 hashes comunes coinciden con `2a44327` y las 2 tuplas se reconstruyen exactas (111 archivos);
- las adaptaciones de los paquetes cerrados sólo filtran los archivos de P2Q-2.

El crédito de L_rev vale 0 por construcción (L ≡ 0 en el TEP), así que la sonda con L_rev negativo es informativa.

## 26. Limitaciones

- Ningún valor clínico está aprobado: las tasas de P y G son tramos predeclarados sobre escalas ya congeladas; el mapeo de
  intercambio gaseoso y el hipoxémico son SYNTHETIC_ONLY; los umbrales de colapso siguen UNSET.
- El núcleo no tiene PaO2, espacio muerto para el CO2, mecánica respiratoria ni interdependencia ventricular.
- Ni la reperfusión (trombólisis) ni la anticoagulación tienen efecto fisiológico modelado; la respuesta al volumen no
  representa el daño del VD.
- La FC de llegada no se reproduce (brecha común en tres familias); la compensación presión → tono falta (dos familias).
- El secundario sólo se usa como diagnóstico; no se calibra.
