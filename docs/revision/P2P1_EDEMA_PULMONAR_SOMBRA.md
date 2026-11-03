# P2P-1 · Migración en sombra del edema pulmonar con escritor de L de familia

Rama `phase-2-clinical-core-shadow`. Todo es sombra: nada llega al tiempo de ejecución ni cambia lo que ve el
residente. Ningún archivo común cambia: 23 quedan fijados en sus bytes de P2O-3. Los bloques entre marcadores
`generado` salen del registro congelado `docs/revision/P2P1_pulmonary_edema.json` con
`python -m clinical_core.edema_migration_report`. El congelamiento `ea1eaa2` y el recongelamiento por la revisión
`ddd5d4b` preceden a la evaluación del registro.

## 1. Encargo y alcance

El paquete prueba la frontera entre escritor de familia y lector común:

escritor de congestión de la familia → L → G común → SpO2 / aporte de O2

Se hace en una familia respiratoria y congestiva, sin cambiar el núcleo común. No busca ajustar un caso. No se
calibran k, s ni r: las sondas corren con la referencia SYNTHETIC_ONLY de P2O-1 (k 1, s 5, r 0,5) y el punto común
que P2N-2 predeclaró para ACS.

## 2. Caso canónico (P2P-1-1)

La familia tiene dos variantes aprobadas y ninguna canónica. Antes de cualquier corrida se fijó una regla textual:
la variante cuyo diagnóstico autoral es edema pulmonar cardiogénico agudo.

<!-- generado:caso -->
- **Caso:** `pulmonary_edema_58m` (familia `pulmonary_edema`), leído de `clinical_cases.py` por ruta. Regla de selección: the variant whose authored faculty diagnosis names acute cardiogenic pulmonary edema; the other variant (pulmonary_edema_75f: decompensated HFrEF with volume overload and CKD) is left for later. Otra variante: `pulmonary_edema_75f` («Acute decompensated systolic heart failure with pulmonary edema»).
- **Diagnóstico autoral:** «Hypertensive acute cardiogenic pulmonary edema».
- **Signos:** PA 218/116, FC 126 (Sinus tachycardia), SpO2 81 % aire ambiente, FR 38, trabajo respiratorio «Severe», llenado capilar 2 s, extremidades «Warm», «Alert», 36.6 °C.
- **Gases y laboratorio:** arterial 7.29 / PaCO2 49 / PaO2 46 (FiO2 21 %), HCO3 22.8; venoso 7.25 / 56; lactato 2.8, Hb 14.3, glucosa 148, K 4.1, creatinina 1.2, troponina 28.
- **POCUS y radiografía:** VI «Moderately reduced global contraction»; VCI «2.4 cm; <50% inspiratory collapse»; pulmones «Diffuse bilateral B-lines in the anterior and lateral zones» («No consolidation or pleural effusion»); radiografía «Bilateral perihilar air-space and interstitial opacities with vascular congestion.».
- **Exploración:** «Severe respiratory effort with widespread bilateral crackles and some expiratory wheeze.»; «Rapid regular pulse; elevated jugular venous pressure.».
- **Tratamientos definitivos autorales:** niv, nitroglycerin, diuretic.
- **Observaciones posteriores:** NONE_AUTHORED: the case states the arrival only; the TDFC declarations and the assessment bank ask the resident to reassess SpO2, respiratory rate and pressure and to decide whether support continues, escalates or can be reduced (an improvement is expected), but no value after arrival is authored: the course is INSUFFICIENT_AUTHORED_TRUTH (as P2N-3), the arrival is not.
- **Comportamiento heredado (sólo referencia):** family_engine.EDEMA (drift 0.003/min, NIV, nitrate, diuretic, recruitment): LEGACY_ENGINE_BEHAVIOR.
<!-- /generado:caso -->

## 3. Mapa de canales y llegada (P2P-1-2, P2P-1-5)

- **V** viene de la evidencia de precarga (VCI, yugulares, el bloque de congestión del caso); **L**, de la congestión
  pulmonar (líneas B, crépitos, radiografía).
- Las líneas B nunca informan V, la bomba ni su reserva.
- L = 0 es la congestión de llegada, nunca pulmones secos.
- `pump_reserve` queda neutral: sólo la lee el acoplamiento común, que la autoridad de la familia apaga.

<!-- generado:llegada -->
| Canal | Papel |
|---|---|
| D | NORMAL_OR_NEUTRAL (perfusion preserved; lactate 2.8 mapped as clearable excess, no prior debt) |
| G | SECONDARY_RESPONSE (severe hypoxaemia: SpO2 81, PaO2 46 on room air) |
| Glu | NORMAL_OR_NEUTRAL (148: mild stress hyperglycaemia) |
| Hb | NORMAL_OR_NEUTRAL (14.3) |
| K | NORMAL_OR_NEUTRAL (4.1) |
| L | PRIMARY_DRIVER (diffuse bilateral B-lines, widespread crackles, perihilar edema on the radiograph) |
| N | NORMAL_OR_NEUTRAL (awake, oriented, distressed) |
| P | NORMAL_OR_NEUTRAL (P = 1 is the authored moderately reduced LV; no ischaemic process: a single troponin 28) |
| R | SECONDARY_RESPONSE (sinus tachycardia 126) |
| T | PRIMARY_DRIVER (the precipitant: uncontrolled hypertension, SBP 218 after missing antihypertensives; T = 1 is that arrival tone; its coupling to congestion is not modelled: the family writer does not read T) |
| V | NORMAL_OR_NEUTRAL (V = 0 at arrival; the full IVC and JVP read a full filling state that no common rule maps to a preload position: CASE_MAPPING_GAP) |
| W | SECONDARY_RESPONSE (RR 38, severe work of breathing, PaCO2 49 with pH 7.29: ventilation failing) |

Exactos en la llegada: map sí, paco2 sí, spo2 sí. L = 0 y G = 0 son la congestión de llegada: sí; L_rev 0,0.

Diferencias:

- **consciousness_level:** núcleo 1, autoral 0. LEGACY_SPO2_LADDER_ARRIVAL_MISREAD: derive's ADOPTED absolute SpO2 ladder (87 / 80) reads 81 % as drowsy against the authored alert patient; ONE_HYPOXEMIA_CONSCIOUSNESS_SOURCE_ONLY must resolve it at integration.
- **hr:** núcleo 80,0, autoral 126,0. ARRIVAL_HR_COMMON_GAP (shared with ACS's M5): the intrinsic rate is the GI rule's band midpoint; the common drive has no arrival term for respiratory distress or hypoxaemia, so the sympathetic share of the arrival tachycardia is not reproduced (reported, not absorbed).
- **rr:** núcleo 18,3, autoral 38,0. EXPECTED_RESPIRATORY_FAMILY_EXTENSION: the common RR is the acid-base drive's (HCO3 22.8), with no congestion, hypoxaemia or mechanics drive.
<!-- /generado:llegada -->

## 4. Escritor de L de la familia (P2P-1-3, P2P-1-4)

`EdemaCongestion` es el único coordinador de L de la familia, y su dueño:
- **sin tratar**, añade por minuto una progresión declarada (el empeoramiento rápido autoral);
- **al oír la señal** de un tratamiento descongestivo, deja de progresar y retira congestión, nunca por debajo de
  L_rev, descontando lo que el aclaramiento común retira en el mismo minuto;
- **escribe sólo L.** SpO2, G, aporte de O2, FR y lactato salen del núcleo común.

La progresión se predeclaró antes de cualquier corrida: 0,0025 / 0,005 / 0,01 por minuto. Es la escala del curso
congelado del escritor ACS (L 0,508 a los 120 min), con un paso ×2 a cada lado. No viene del legado ni de un
resultado.

<!-- generado:escritor -->
- Canales que escribe: L; flujos sanguíneos: no; ajustes: no; demanda: no.
- Dueño de L: sí; tipo disease_module; registrado: sí.
- El tratamiento descongestivo sólo publica la señal `edema_decongestion` y no escribe deltas: sí.
<!-- /generado:escritor -->

## 5. L → G → SpO2 sin tratar (P2P-1-7)

<!-- generado:curso -->
| Progresión (L/min) | Minuto | L | G | SpO2 | FC | FR | PAM | Lactato | Conciencia |
|---|---|---|---|---|---|---|---|---|---|
| 0.0025 | 0 | 0,000 | 0,000 | 81,00 | 80,0 | 18,3 | 150,0 | 2,80 | 1 |
| 0.0025 | 30 | 0,071 | 0,071 | 80,65 | 80,2 | 17,8 | 150,0 | 2,40 | 1 |
| 0.0025 | 60 | 0,133 | 0,133 | 80,34 | 80,3 | 17,4 | 150,0 | 2,09 | 1 |
| 0.0025 | 90 | 0,188 | 0,188 | 80,06 | 80,5 | 17,1 | 150,0 | 1,85 | 1 |
| 0.0025 | 120 | 0,237 | 0,237 | 79,82 | 80,6 | 16,9 | 150,0 | 1,66 | 2 |
| 0.005 | 0 | 0,000 | 0,000 | 81,00 | 80,0 | 18,3 | 150,0 | 2,80 | 1 |
| 0.005 | 30 | 0,141 | 0,141 | 80,29 | 80,4 | 17,8 | 150,0 | 2,40 | 1 |
| 0.005 | 60 | 0,266 | 0,266 | 79,67 | 80,7 | 17,4 | 150,0 | 2,09 | 2 |
| 0.005 | 90 | 0,376 | 0,376 | 79,12 | 80,9 | 17,1 | 150,0 | 1,85 | 2 |
| 0.005 | 120 | 0,473 | 0,473 | 78,63 | 81,2 | 16,9 | 150,0 | 1,66 | 2 |
| 0.01 | 0 | 0,000 | 0,000 | 81,00 | 80,0 | 18,3 | 150,0 | 2,80 | 1 |
| 0.01 | 30 | 0,283 | 0,283 | 79,59 | 80,7 | 17,8 | 150,0 | 2,40 | 2 |
| 0.01 | 60 | 0,532 | 0,532 | 78,34 | 81,3 | 17,4 | 150,0 | 2,09 | 2 |
| 0.01 | 90 | 0,752 | 0,752 | 77,24 | 81,9 | 17,1 | 150,0 | 1,85 | 2 |
| 0.01 | 120 | 0,946 | 0,946 | 76,27 | 82,4 | 16,9 | 150,0 | 1,66 | 2 |

Direcciones: 0.0025: G_is_lung_share sí, G_up sí, L_up sí, V_P_untouched sí, spo2_down sí; 0.005: G_is_lung_share sí, G_up sí, L_up sí, V_P_untouched sí, spo2_down sí; 0.01: G_is_lung_share sí, G_up sí, L_up sí, V_P_untouched sí, spo2_down sí.
<!-- /generado:curso -->

## 6. Oxígeno (P2P-1-8)

El oxígeno usa la vía común de FiO2, con la única respuesta G → SpO2 de P2O-1. No hay función de oxígeno propia de
la familia ni se divide G.

<!-- generado:oxigeno -->
| FiO2 | Minuto | L | G | SpO2 |
|---|---|---|---|---|
| 0,21 | 0 | 0,000 | 0,000 | 81,00 |
| 0,21 | 30 | 0,141 | 0,141 | 80,29 |
| 0,21 | 60 | 0,266 | 0,266 | 79,67 |
| 0,21 | 90 | 0,376 | 0,376 | 79,12 |
| 0,21 | 120 | 0,473 | 0,473 | 78,63 |
| 0,4 | 0 | 0,000 | 0,000 | 81,00 |
| 0,4 | 30 | 0,141 | 0,141 | 85,62 |
| 0,4 | 60 | 0,266 | 0,266 | 84,70 |
| 0,4 | 90 | 0,376 | 0,376 | 83,92 |
| 0,4 | 120 | 0,473 | 0,473 | 83,24 |
| 0,6 | 0 | 0,000 | 0,000 | 81,00 |
| 0,6 | 30 | 0,141 | 0,141 | 91,22 |
| 0,6 | 60 | 0,266 | 0,266 | 90,00 |
| 0,6 | 90 | 0,376 | 0,376 | 88,97 |
| 0,6 | 120 | 0,473 | 0,473 | 88,10 |

Monótona en FiO2: sí. Ganancia de FiO2 0,6 a los 30 min 10,93 y a los 120 min 9,46: atenuada al empeorar G sí. Sin función de oxígeno propia de la familia.
<!-- /generado:oxigeno -->

## 7. Autoridad (P2P-1-12)

<!-- generado:autoridad -->
- Escritor de familia más sobrecarga común: 0 escrituras comunes; L igual a la del escritor solo: sí; L final 0,473; V se mueve: sí.
- Sin escritor de familia: 113 escrituras comunes; L final 0,305.
- Dueño con ganancia 0: 0 escrituras comunes; L final 0,000 (aceptado).
- Un segundo dueño (el escritor ACS) se rechaza: sí.
<!-- /generado:autoridad -->

## 8. Descongestión con L_rev = 0 (P2P-1-6, P2P-1-13)

L_rev sigue en 0. Ninguna observación autoral posterior a la llegada pide mejorar por debajo de la congestión de
llegada (decisión 6). Por eso la descongestión devuelve L, G y SpO2 hasta la llegada y no más allá.

**Consecuencia que debe decidir la docencia:** con L_rev = 0, ningún tratamiento descongestivo puede mejorar la
oxigenación por encima de la llegada. Sólo la FiO2 la sube. Si la docencia quiere que el tratamiento mejore respecto
de la llegada, hay que declarar un L_rev por caso o familia, con fuente clínica, antes de componer los tratamientos.

<!-- generado:descongestion -->
| Minuto | L | G | SpO2 | V | P |
|---|---|---|---|---|---|
| 0 | 0,000 | 0,000 | 81,00 | 0,0 | 1,000 |
| 60 | 0,256 | 0,256 | 79,72 | 0,0 | 1,000 |
| 90 | 0,085 | 0,085 | 80,58 | 0,0 | 1,000 |
| 120 | 0,000 | 0,000 | 81,00 | 0,0 | 1,000 |
| 150 | 0,000 | 0,000 | 81,00 | 0,0 | 1,000 |
| 180 | 0,000 | 0,000 | 81,00 | 0,0 | 1,000 |

L_rev 0,0; L mínima 0,000; SpO2 máxima 81,0. Mejora tras el tratamiento: sí; vuelve a la llegada: sí; nunca por debajo: sí; V y P sin cambio: sí. Sonda guionizada bajo la llegada: L −0,60, G 0,00, SpO2 81,0 (sin crédito: sí).
<!-- /generado:descongestion -->

## 9. El bolo de volumen autoral

El banco de evaluación declara `edema_volume_loading` (un bolo en un EAP) como acción peligrosa. Esto es lo que hace
la familia migrada con el volumen; se informa y no se repara aquí.

<!-- generado:volumen -->
Evento crítico autoral `edema_volume_loading` (sonda SYNTHETIC_ONLY de 2000 mL a los 120 min): L 0,473 → 0,473, SpO2 78,63 → 78,63, PAM 150,0 → 167,7, aporte 0,971 → 1,058; posición de precarga 0,559 bajo la rodilla 0,85. L sin cambio: sí. AUTHORED_DANGEROUS_ACTION_NOT_REPRESENTED: FAMILY_WRITER_REQUIRED (a volume term inside the family's L coordinator) and CASE_MAPPING_GAP (an IVC -> preload rule); a faculty decision before treatments are composed.
<!-- /generado:volumen -->

## 9b. FC (P2P-1-14)

<!-- generado:fc -->
FC a los 120 min (progresión más rápida): sin escritor 80,0, sin tratar 82,4, con FiO2 0,6 80,0. Diferencias 2,37 y −2,37 lpm; objetivo del impulso 0,000 / 0,095 / 0,000. Umbral 94; ninguna ganancia se retocó.
<!-- /generado:fc -->

## 10. Conciencia (P2P-1-15)

<!-- generado:conciencia -->
Nivel en la llegada: núcleo 1, autoral 0. Niveles durante el curso: sin tratar [1, 2], con oxígeno [0, 1]. `derive` lee el candidato de P2L-2: no.

ONE_HYPOXEMIA_CONSCIOUSNESS_SOURCE_ONLY: derive's ADOPTED SpO2 ladder (87 / 80) and P2L-2's hypoxaemia signal must never both act in one candidate pathway; P2P-1 is shadow only and runs derive's ladder alone (the P2L-2 candidate is not wired into derive); at runtime integration one source remains (LEGACY_SPO2_CONSCIOUSNESS_LADDER_MUST_BE_DISABLED_ON_P2L2_INTEGRATION).
<!-- /generado:conciencia -->

## 11. FR, trabajo respiratorio y VNI (P2P-1-9, P2P-1-10)

<!-- generado:respiracion -->
FR autoral 38, FR común en la llegada 18,3 (brecha 19,7); la FR común sigue a L o G: no. Trabajo respiratorio «Severe», pH 7.29, PaCO2 49. Acciones diferidas: VNI_COMMON_EXTENSION_DEFERRED. Falta: congestion / hypoxaemia respiratory drive; respiratory mechanics and work of breathing; respiratory-muscle oxygen demand; NIV (EPAP, recruitment, afterload, preload). Clase: `EXPECTED_RESPIRATORY_FAMILY_EXTENSION`; esperada: sí. Tendencias sin tratar (minuto 0 → 120, progresión más rápida): lactate 2,80 → 1,66; paco2 49,00 → 53,14; rr 18,29 → 16,86; spo2 81,00 → 76,27: la FR común baja con el ácido de llegada y el lactato baja con su exceso, mientras la SpO2 empeora.
<!-- /generado:respiracion -->

## 12. Tratamientos (P2P-1-11)

<!-- generado:tratamientos -->
| Tratamiento | Clase | Objetivo |
|---|---|---|
| diuretic | FAMILY_WRITER_REQUIRED + NEW_COMMON_MECHANISM_REQUIRED | L through the family writer's decongestion (the signal); V outflow needs a renal plasma-loss blood process the core does not have |
| nitroglycerin | NEW_COMMON_MECHANISM_REQUIRED | T / V: a writer of T is refused while the common tone response is on (the integrator's rule; the profile's tone response is on); venodilation has no blood process; its decongestive effect on L is the family's (FAMILY_WRITER_REQUIRED, via the decongestion signal) |
| niv | VNI_COMMON_EXTENSION_DEFERRED | W, G, afterload and preload (outside P2P-1) |
| oxygen | COMMON_TARGET_EXISTS | FiO2 (interventions.oxygen.Oxygen) |

Magnitudes: UNSET: no treatment magnitude is calibrated, to legacy or otherwise.
<!-- /generado:tratamientos -->

## 13. Legado (P2P-1-16), leído al final

<!-- generado:legado -->
| Minuto | Legado SpO2 | Núcleo SpO2 | Legado FR | Núcleo FR | Legado FC | Núcleo FC | Legado conciencia | Núcleo conciencia |
|---|---|---|---|---|---|---|---|---|
| 0 | 81 | 81,0 | 38 | 18,3 | 126 | 80,0 | Alert | 1 |
| 60 | 78 | 79,7 | 41 | 17,4 | 126 | 80,7 | Obtunded | 2 |
| 120 | 75 | 78,6 | 44 | 16,9 | 126 | 81,2 | Obtunded | 2 |

- **consciousness:** POSSIBLE_COMMON_CORE_GAP: the legacy shows the authored alert patient at arrival and its own ladder afterwards (obtunded from minute 30, SpO2 79); derive's absolute SpO2 ladder already reads 81 % as drowsy at arrival (no arrival anchoring; ONE_HYPOXEMIA_CONSCIOUSNESS_SOURCE_ONLY).
- **hr_arrival:** EXPECTED_EXTENSION_NOT_YET_MODELED: the legacy shows the authored HR; the core's is the common HR physiology's at the GI-rule intrinsic rate (ARRIVAL_HR_COMMON_GAP, shared with ACS).
- **niv_nitrate_diuretic:** EXPECTED_EXTENSION_NOT_YET_MODELED: legacy treatment effects (NIV recruitment, nitrate pressure, delayed diuretic) are not migrated.
- **rr_course:** EXPECTED_EXTENSION_NOT_YET_MODELED: the legacy RR follows its lung index; the common RR has no congestion or hypoxaemia drive (EXPECTED_RESPIRATORY_FAMILY_EXTENSION).
- **spo2_course:** LEGACY_DIFFERENCE_NOT_CLINICALLY_RELEVANT: both fall untreated; the size is the family span's and the legacy drift's, neither authored.

Usado para parámetros: no.
<!-- /generado:legado -->

## 14. No regresión GI y ACS (P2P-1-17)

<!-- generado:no_regresion -->
- GI (O12 de P2O-1) reproducido: sí.
- Evaluación ACS de P2O-1 reproducida: sí.
- Autoridad ACS (R7 de P2O-3) reproducida: sí; sobrecarga común (R8): sí.
- Archivos comunes intactos: 23 de 23.
<!-- /generado:no_regresion -->

## 15. Demostración

<!-- generado:prueba -->
- Tuplas reconstruidas byte a byte como las dejó P2O-3: `clinical_core/decision_pack.py` sí, `clinical_core/lactate_slice.py` sí.
- Digest congelado de P2O-3 reproducido por la vista: sí; registro de P2O-3 intacto: sí.
<!-- /generado:prueba -->

## 16. Veredicto (P2P-1-18)

<!-- generado:veredicto -->
| Criterio | Cumple |
|---|---|
| GI and ACS unchanged; no common file changed | sí |
| HR sign physiological | sí |
| L worsening -> G worsening -> SpO2 worsening (every progression rate) | sí |
| arrival exact where the core models it (SpO2, MAP, PaCO2; L = 0 is the arrival congestion; L_rev 0) | sí |
| authority: no double writing; common overload without the family; second owner refused | sí |
| case truth sufficient (every item read) | sí |
| decongestion back to arrival improves G and SpO2, none below arrival (L_rev 0), V and P unchanged | sí |
| family writer writes L only and owns it (no SpO2, G, DO2, RR or lactate scripting) | sí |
| oxygen through the common FiO2 path (monotone, attenuated by the common r, no family function) | sí |

**Veredicto:** B, `PULMONARY_EDEMA_NEEDS_EXPECTED_RESPIRATORY_EXTENSION`. Arquitectura familia-escritor / lector común satisfactoria: sí.

**Recomendación:** `IMPLEMENT_ONLY_THE_MINIMUM_RESPIRATORY_EXTENSION_REQUIRED` (no se inicia).
<!-- /generado:veredicto -->

## 17. Ondulación sobre los paquetes cerrados

- Las 17 pruebas encadenadas (P2O-1 y las cerradas) más la de P2O-3 leen el árbol de P2O-3 a través de `pe.chain` y
  `pe.p2o3_sources`:
  - sin los archivos de P2P-1;
  - con las tuplas reconstruidas;
  - con el registro de tipos sin los de la familia.

  Sus registros no cambian.
- **Excepciones explícitas:**
  - la prueba de P2O-2 excluye el escritor de P2P-1 de su escaneo de escritores de L;
  - la de ACS lo excluye de los lectores de la familia;
  - la de RR excluye los archivos de P2P-1, que nombran W sólo para informar;
  - la de aislamiento admite que `edema_reference.py` lea la verdad del caso, como `acs_reference.py`.
- **Registros históricos:** P2G, P2I, P2I-2T y P2I-2U se regeneraron (sólo los digests).

## 18. Revisión adversarial

Hubo una revisión independiente y de sólo lectura. Encontró 2 hallazgos medios, 4 bajos y ningún alto, todos
confirmados con sondas, y ninguno cambia la letra. El recongelamiento `ddd5d4b` los incorpora; los resultados de
§5–§8 y §9b–§14 no cambian.

- **M1, el bolo autoral es inerte en L:** §9. El `congestion_block` heredado ya no se cita como evidencia de V.
- **M2, la justificación de L_rev = 0 omitía «continue, escalate or can be reduced»:** queda como contradicción para
  la docencia (§8, §19).
- **B1, el veredicto ignoraba la llegada, la FC y la demostración de P2O-3:** ahora cada criterio decide una letra.
- **B2:** la guarda del escritor sólo acepta `Channel.L` literal.
- **B3:** los booleanos de la FC y del oxígeno se calculan.
- **B4:** las tablas van ordenadas por minuto.
- **B5:** se registran las tendencias de FR, PaCO2 y lactato (§11).
- **Sospechas declaradas (§19):** la regla de selección y el curso sin verdad autoral.
- **Lo que se comprobó sólido:**
  - el escritor sólo escribe L;
  - sin doble conteo;
  - piso en L_rev exacto en 150 corridas aleatorias;
  - las líneas B no llegan a V;
  - sin subtipo de O2;
  - la VNI, diferida;
  - la FC sin retocar;
  - una sola fuente de conciencia;
  - GI y ACS sin regresión, con los 23 archivos comunes byte a byte;
  - el legado no es objetivo;
  - la maquinaria de demostración no se deja engañar.

## 19. Brechas y decisiones pendientes

- **EXPECTED_RESPIRATORY_FAMILY_EXTENSION:** el núcleo no tiene impulso respiratorio por congestión o hipoxemia,
  mecánica, trabajo respiratorio ni demanda de O2 de los músculos respiratorios. La FR autoral (38) no se reproduce.
- **VNI_COMMON_EXTENSION_DEFERRED.**
- **ARRIVAL_HR_COMMON_GAP**, compartida con ACS: la FC de llegada (126) no se reproduce con la frecuencia intrínseca de
  la regla GI.
- **Escalera de SpO2:** la escalera ADOPTED de `derive` lee 81 % como somnolencia frente al paciente alerta autoral
  (ONE_HYPOXEMIA_CONSCIOUSNESS_SOURCE_ONLY).
- **Mecanismos comunes que faltan para el nitrato y el diurético:** la entrada del vasodilatador al tono y a V, y un
  proceso sanguíneo de diuresis.
- **L_rev:** con 0, la descongestión no mejora por encima de la llegada; adoptar un valor es decisión docente.
- **V:** no hay una regla común VCI → fracción de precarga; la VCI llena queda sin valor declarado.
- **MAPPING_DOCUMENTATION_DEBT:** la banda de `pump_reserve` de ACS sigue citando las líneas B.
- **Otras variantes:** `pulmonary_edema_75f` (IC con FE reducida y sobrecarga de volumen) queda para después.
- **Bolo de volumen (M1):** la acción peligrosa autoral `edema_volume_loading` no se representa. Bajo la autoridad,
  el escritor de familia no tiene término de volumen y la posición de precarga provisional queda bajo la rodilla. Antes
  de componer tratamientos hacen falta un término de volumen en el coordinador de L de la familia y una regla
  VCI → precarga.
- **L_rev frente al texto autoral (M2):** el banco de evaluación y las declaraciones TDFC esperan que el soporte pueda
  «reducirse», lo que implica mejorar respecto de la llegada. Con L_rev = 0 eso no es posible en aire ambiente. Es una
  contradicción que debe resolver la docencia.
- **Direcciones sin tratar (B5):** mientras la SpO2 empeora:
  - la FR común baja de 18,3 a 16,9, porque se aclara el ácido de llegada;
  - la PaCO2 sube de 49 a 53,1;
  - el lactato baja de 2,8 a 1,66, porque se aclara su exceso y no hay deuda.

  La extensión respiratoria tendrá que corregir la FR.
- **Alcance del veredicto:** cubre el EAP sin sobrecarga de volumen (`pulmonary_edema_58m`). La variante con
  sobrecarga, que exige V, diuresis y quizá D, no se probó.
- **Verdad autoral del curso:** no hay ningún valor autoral después de la llegada (INSUFFICIENT_AUTHORED_TRUTH para el
  curso, como en P2N-3). La de la llegada es suficiente.
- **Guarda de G:** la decisión 5 dice que no cambie. Hoy, con L_rev = 0 sostiene G como en P2O-1 y con L_rev < 0
  detiene la corrida. P2P-1 no la toca.
