# P2U-1 · Migración en sombra de los opioides: depresión respiratoria central

Migración de familia, en sombra. Rama `phase-2-clinical-core-shadow`; base `98a2bb0` (P2T-5 aceptado y cerrado:
`COMMON_HYPOVENTILATION_OXYGENATION_LINK_READY`).

Es la prueba de esfuerzo ortogonal de la cadena respiratoria común sin enfermedad pulmonar: disponibilidad central →
FR expresada → W → PaCO2 → (enlace relativo de P2T-5) SpO2 → DO2, sin G ni L de familia, sin distrés y sin ecuación de
oxígeno propia.

- **Cambio común mínimo** (`state.py`, `provenance.py`, `derived.py`, `integration.py`), probado contra `98a2bb0`:
  resuelve `CENTRAL_AVAILABILITY_STATE_DEFERRED`, documentado en P2T-5 (TD-123, punto 5).
  - `AuxiliaryState.central_availability` (0 a 1, 1 por defecto) y `Anchors.arrival_central_availability` (1 por
    defecto): la disponibilidad de P2P-2 pasa a ser escribible por una familia, como la mecánica de P2S-2 y el distrés
    de P2T-1. No es un canal canónico.
  - `provenance.AvailabilityChange`: aditivo, falla cerrado fuera de 0 a 1, con la regla de redondeo de P2T-1A en los
    dos extremos.
  - La composición expresa el valor estructural del perfil por la disponibilidad del estado (1 × 1 = 1 exacto por
    defecto), y necesita la fisiología ácido-base de P2K-2, igual que el valor del perfil.
- **Familia** (`clinical_core/modules/opioid.py`): `OpioidCentralDepression` y `NaloxoneReversal`. Sólo escriben la
  disponibilidad; las tasas son `SYNTHETIC_ONLY`.
- **Llegada** (`clinical_core/opioid_reference.py`): disponibilidad y eficiencia mecánica como estados latentes
  `FAMILY_CANDIDATE` en cada FR intrínseca llevada (12 / 16 / 20). No se elige ningún valor.
- **Análisis:** `clinical_core/opioid_migration.py`, congelado antes de la única evaluación. **Registro:**
  `docs/revision/P2U1_opioid_migration.json`. Este documento se genera desde el registro
  (`clinical_core/opioid_migration_report.py`); el texto fuera de los marcadores es la narrativa.

## 1. Decisiones docentes que rigen

- **Mecanismo único de familia:** la depresión central. No se escribe G para reproducir una SpO2 baja: si hiciera falta
  G sin patología pulmonar autorada, el paquete se detendría con `COMMON_OXYGENATION_LINK_INSUFFICIENT`.
- **Distrés:** queda inactivo (0). El trabajo respiratorio autorado es «Reduced»; es el contraste clave con el asma.
- **Naloxona:** señal de tratamiento de familia que devuelve disponibilidad hacia 1. No escribe FR, PaCO2, SpO2, FC ni
  conciencia. Sin curso posterior autorado: magnitud y cinética `UNSET` / `SYNTHETIC_ONLY`.
- **FC:** sin término opioide. El residual se lleva como `OPIOID_HR_FAMILY_GAP`.
- **Conciencia:** sólo diagnóstica (`CONSCIOUSNESS_INTEGRATION_DEBT`). N no se escribe ni se lee.
- **Oxígeno y ácido-base:** rutas comunes; `FIO2_RESPONSE_MAGNITUDE_DEBT` sigue abierta.
- **Colapso:** sólo estructural, sin umbral calibrado.
- **Legado:** se lee después de la verdad autoral y sólo se clasifica.

## 2. Verdad de los casos (P2U-1-1)

<!-- generado:verdad -->
- **opioid_35m:** PA 106/64 (PAM 78,0), FC 68, SpO2 80 %, FR 6, WOB «Reduced», Obtunded; gasometría arterial pH 7.21, PaCO2 69, PaO2 45, HCO3 26.7 (FiO2 21 %); lactato 2.6; glucosa 106; Hb 14.5; creatinina 1.0; Sinus rhythm; temperatura 36.4 °C; pulmón: No B-lines; A-line pattern bilaterally; radiografía: No focal infiltrate or pulmonary edema.; examen respiratorio: «Very slow, shallow breaths with reduced chest excursion; breath sounds are equal when air enters.»; neurológico: «Obtunded, with small reactive pupils and brief bilateral withdrawal to firm stimulation; no visible head injury.»; acciones definitivas: naloxone, bag_mask, reassessment; riesgo de recurrencia no.
- **opioid_67f:** PA 104/62 (PAM 76,0), FC 62, SpO2 84 %, FR 8, WOB «Reduced», Obtunded; gasometría arterial pH 7.25, PaCO2 61, PaO2 50, HCO3 25.8 (FiO2 21 %); lactato 2.2; glucosa 112; Hb 12.4; creatinina 2.2; Sinus rhythm; temperatura 36.3 °C; pulmón: No B-lines; A-line pattern bilaterally; radiografía: No focal consolidation or edema.; examen respiratorio: «Slow shallow breathing with reduced chest excursion; no focal wheeze or crackles.»; neurológico: «Obtunded with small reactive pupils, briefly withdrawing both arms to a firm stimulus.»; acciones definitivas: naloxone, bag_mask, reassessment; riesgo de recurrencia sí.
- Oxígeno: room air (ABG FiO2 21 %); no oxygen therapy authored.
- Observaciones posteriores: none authored (no post-naloxone truth).
- Clases: AUTHORED_CASE_TRUTH = the bank values above; LEGACY_ENGINE_BEHAVIOR = legacy() below; MODEL_DERIVED = every RR, W, PaCO2, pH, SpO2, delivery, HR and consciousness after arrival.
<!-- /generado:verdad -->

## 3. Mapa de canales (P2U-1-2)

<!-- generado:canales -->
- D: NORMAL_OR_NEUTRAL (perfusion preserved; lactate 2.6 / 2.2 mapped as clearable excess, no prior debt)
- G: NORMAL_OR_NEUTRAL (G = 0: the arrival SpO2 80 / 84, PaO2 45 / 50 on room air is the anchored arrival state; no pulmonary pathology is authored, so no G writer)
- Glu: NORMAL_OR_NEUTRAL
- Hb: NORMAL_OR_NEUTRAL
- K: NORMAL_OR_NEUTRAL (4.1)
- L: NORMAL_OR_NEUTRAL (L = 0: A-lines, no B-lines, clear radiograph)
- N: NORMAL_OR_NEUTRAL (obtunded with small pupils: the toxidrome, not a primary neurological process; N is P2L-2's and stays unread: CONSCIOUSNESS_INTEGRATION_DEBT)
- P: NORMAL_OR_NEUTRAL (P = 1; LV preserved, troponin 7 / 11)
- R: NORMAL_OR_NEUTRAL (sinus 68 / 62; no opioid HR term)
- T: NORMAL_OR_NEUTRAL (T = 1; warm, preserved perfusion, BP 106/64 and 104/62)
- V: NORMAL_OR_NEUTRAL (V = 0; IVC 1.8 / 1.9 cm, LV preserved)
- W: SECONDARY_RESPONSE (W derived from the expressed RR and the mechanics; PaCO2 69 / 61, pH 7.21 / 7.25)
- central_availability: PRIMARY_DRIVER (the family's mechanism: the arrival latent availability and the writers)

| Caso | V | T | P | L | G | D | N | Distrés | Disponibilidad | Eficiencia |
|---|---|---|---|---|---|---|---|---|---|---|
| opioid_35m | 0,0 | 1,0 | 1,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,3750 | 1,5459 |
| opioid_67f | 0,0 | 1,0 | 1,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,5000 | 1,3115 |

- Pasa: sí.
<!-- /generado:canales -->

## 4. Región de llegada (P2U-1-4)

<!-- generado:llegada -->
| Caso | FR intrínseca | Disponibilidad | Eficiencia | FR | PaCO2 | pH | SpO2 | FC | PaCO2 si se restaura |
|---|---|---|---|---|---|---|---|---|---|
| opioid_35m | 12 | 0,5000 | 1,1594 | 6,00 | 69,00 | 7,211 | 80,0 | 63,3 | 34,5 |
| opioid_35m | 16 | 0,3750 | 1,5459 | 6,00 | 69,00 | 7,211 | 80,0 | 71,3 | 25,9 |
| opioid_35m | 20 | 0,3000 | 1,9324 | 6,00 | 69,00 | 7,211 | 80,0 | 71,3 | 20,7 |
| opioid_67f | 12 | 0,6667 | 0,9836 | 8,00 | 61,00 | 7,249 | 84,0 | 63,9 | 40,7 |
| opioid_67f | 16 | 0,5000 | 1,3115 | 8,00 | 61,00 | 7,249 | 84,0 | 65,9 | 30,5 |
| opioid_67f | 20 | 0,4000 | 1,6393 | 8,00 | 61,00 | 7,249 | 84,0 | 65,9 | 24,4 |

- **opioid_35m:** autoral FR 6, PaCO2 69, pH 7.21, SpO2 80, FC 68; reproducción exacta en el núcleo vivo sí; producto FR × PaCO2 414 (FR intrínseca / eficiencia = 10,35); banda de FC del modelo 63,3–71,3, FC autoral dentro sí.
- **opioid_67f:** autoral FR 8, PaCO2 61, pH 7.25, SpO2 84, FC 62; reproducción exacta en el núcleo vivo sí; producto FR × PaCO2 488 (FR intrínseca / eficiencia = 12,20); banda de FC del modelo 63,9–65,9, FC autoral dentro no.

- **STEADY_STATE_W_ARRIVAL_TENSION:** the common PaCO2 is algebraic (PaCO2 = 40 x I / (E x RR) with no excitatory drive): the authored RR x PaCO2 sets I / E; at the carried I in 12-20, 35m needs E 1.16-1.93 (above the reference, against the authored 'shallow breaths') and its availability restored to 1 gives a hypocapnic PaCO2 (34.5 to 20.7); 67f is near E 1 only at I 12. Ways out, none chosen: an intrinsic RR below the carried band, CO2 kinetics (the arrival not at steady state), or E above 1 as read (P2S-2's accepted region, 'mechanics not reduced'). Decisión: FACULTY (no threshold, band or tau chosen here).
- Pasa: sí.
<!-- /generado:llegada -->

## 5. Interfaz común añadida (P2U-1-3)

<!-- generado:interfaz -->
- Campo auxiliar nuevo: central_availability; ancla de llegada nueva: arrival_central_availability; campos del perfil nuevos: ninguno.
- FR: expressed RR = (profile availability x state availability) x excitatory RR (P2P-2's form).
- Lectores de la disponibilidad: `_composition`, `arrival_drive_composition`, `arrival_state`, `respiratory_drive_composition`.
- `clinical_core/derived.py`: funciones nuevas `central_availability`; cambiadas `_composition`, `arrival_drive_composition`, `arrival_state`, `respiratory_drive_composition`.
- `clinical_core/integration.py`: funciones nuevas `_availability_after`, `availability_sum`; cambiadas `_check_conservation`, `_check_owned`, `step`.
- `clinical_core/provenance.py`: funciones nuevas ninguna; cambiadas `__post_init__`, `to_dict`.
- `clinical_core/state.py`: funciones nuevas ninguna; cambiadas `__post_init__`.
- Pasa: sí.
<!-- /generado:interfaz -->

## 6. Auditoría de los escritores

<!-- generado:escritores -->
- Construye: `AvailabilityChange`, `Contribution`, `CoreInvariantError`; única clave de contribución: availability; nombres prohibidos encontrados: ninguno.
- Lee del estado: central_availability, pulse_present; tipos registrados: opioid_central_depression, naloxone_reversal.
- Pasa: sí.
<!-- /generado:escritores -->

## 7. Sondas U1–U12 (P2U-1-14)

<!-- generado:sondas -->
- **opioid_35m:** U1 sí, U2 sí, U3 sí, U4 sí, U5 sí, U6 sí, U7 sí, U8 sí, U9 sí; sólo escribe disponibilidad sí.
  - Sin tratar (60 min): disponibilidad 0,3750 → 0,2776, FR 6,00 → 4,57, W 0,580 → 0,442, PaCO2 69,0 → 90,5, SpO2 80,00 → 25,25, pH 7,211 → 7,089, DO2 relativa 1,000 → 0,305.
  - Con antagonista: disponibilidad 0,4375 → 0,9971, FR 7,00 → 15,95, W 0,676 → 1,541, PaCO2 59,1 → 26,0, SpO2 89,04 → 97,62, pH 7,277 → 7,635, FC 70,7 → 68,0, conciencia 2 → 2.
- **opioid_67f:** U1 sí, U2 sí, U3 sí, U4 sí, U5 sí, U6 sí, U7 sí, U8 sí, U9 sí; sólo escribe disponibilidad sí.
  - Sin tratar (60 min): disponibilidad 0,5000 → 0,3701, FR 8,00 → 5,92, W 0,656 → 0,485, PaCO2 61,0 → 82,4, SpO2 84,00 → 37,22, pH 7,249 → 7,119, DO2 relativa 1,000 → 0,443.
  - Con antagonista: disponibilidad 0,5500 → 0,9977, FR 8,80 → 15,96, W 0,721 → 1,308, PaCO2 55,5 → 30,6, SpO2 88,53 → 96,60, pH 7,291 → 7,549, FC 65,5 → 62,0, conciencia 2 → 2.
- U10 (sin ecuación de oxígeno propia de la familia ni término opioide en el núcleo): sí; ruta de oxígeno: P2T-5's ventilated_oxygenation on the common FiO2 / G SpO2 (no opioid function).
- U11 (sin escritura directa de observables): sí.
- U12: non_regression(): P2T-5's record on its tree (P2T-3, P2T-1A, P2T-1, P2S-3, P2S-2, P2Q-2, P2P-2, P2P-1, ACS, GI); the committed profiles' availability is 1 (default).
- Pasa: sí.
<!-- /generado:sondas -->

## 8. Contraste primario / secundario (P2U-1-13)

<!-- generado:contraste -->
| FR intrínseca | Disponibilidad 35m | Disponibilidad 67f | Eficiencia 35m | Eficiencia 67f |
|---|---|---|---|---|
| lower | 0,5000 | 0,6667 | 1,1594 | 0,9836 |
| midpoint | 0,3750 | 0,5000 | 1,5459 | 1,3115 |
| upper | 0,3000 | 0,4000 | 1,9324 | 1,6393 |

- one family mechanism (the availability) at two severities: 35m deeper than 67f at every carried intrinsic RR, same writers, same common equations, no case residual writer.
- Pasa: sí.
<!-- /generado:contraste -->

## 9. Recurrencia del opioide de acción prolongada (P2U-1-10)

<!-- generado:recurrencia -->
- llegada (minuto 0): disponibilidad 0,5000, FR 8,00, PaCO2 61,0, SpO2 84,00, pH 7,249.
- al parar el antagonista (minuto 40): disponibilidad 0,9592, FR 15,35, PaCO2 31,8, SpO2 96,43, pH 7,532.
- al final (minuto 120): disponibilidad 0,1905, FR 4,30, PaCO2 113,4, SpO2 0,00, pH 6,910.
- RECURRENCE_KINETICS_UNSET (synthetic rates only).
- Pasa: sí.
<!-- /generado:recurrencia -->

## 10. Dirección del colapso (P2U-1-15)

<!-- generado:colapso -->
- Empeoramiento severo sintético (120 min): DO2 relativa 1,000 → 0,000, SpO2 80,00 → 0,00, D 0,000 → 108,700, PaCO2 69,0 → 1372,5.
- Sin regla de colapso propia de la familia: sí; STRUCTURAL_ONLY (no threshold calibrated; P2T-5's M2 floor applies at the deepest PaCO2).
- Pasa: sí.
<!-- /generado:colapso -->

## 11. Frecuencia cardíaca (P2U-1-8)

<!-- generado:fc -->
- **opioid_35m:** FC autoral 68, banda del modelo 63,3–71,3, dentro sí, residual 0,00 lpm.
- **opioid_67f:** FC autoral 62, banda del modelo 63,9–65,9, dentro no, residual −1,89 lpm.
- OPIOID_HR_FAMILY_GAP: opioid_67f -1.89 bpm outside the common band.
- Término de FC propio de la familia: no; diagnostic: the authored HR against the model HR over the common intrinsic-HR band; a residual is carried, never patched (no opioid HR term).
- Pasa: sí.
<!-- /generado:fc -->

## 12. Conciencia (P2U-1-9)

<!-- generado:conciencia -->
- **opioid_35m:** autoral «Obtunded» (nivel 2); niveles con antagonista [2]; the ADOPTED ladder reads SpO2 only; the toxidrome (obtundation, small pupils) and hypercapnic encephalopathy are not separated: CONSCIOUSNESS_INTEGRATION_DEBT.
- **opioid_67f:** autoral «Obtunded» (nivel 2); niveles con antagonista [2]; the ADOPTED ladder reads SpO2 only; the toxidrome (obtundation, small pupils) and hypercapnic encephalopathy are not separated: CONSCIOUSNESS_INTEGRATION_DEBT.
- N escrito: no.
- Pasa: sí.
<!-- /generado:conciencia -->

## 13. Oxígeno (P2U-1-11)

<!-- generado:oxigeno -->
- Llegada: aire ambiente 80,00, FiO2 0,4 85,70.
- Hipoventilando (60 min): aire ambiente 25,25, FiO2 0,4 42,98; la FiO2 no mueve la PaCO2 sí.
- the common FiO2 rule (spo2_per_fio2 30), no opioid gain; FIO2_RESPONSE_MAGNITUDE_DEBT.
- Pasa: sí.
<!-- /generado:oxigeno -->

## 14. Ácido-base (P2U-1-12)

<!-- generado:acido -->
- **opioid_35m:** con antagonista, pH 7,211 → 7,635, PaCO2 69,0 → 26,0, HCO3 26,70 → 26,70, carga ácida 0,000 → 0,000.
- **opioid_67f:** con antagonista, pH 7,249 → 7,549, PaCO2 61,0 → 30,6, HCO3 25,80 → 25,80, carga ácida 0,000 → 0,000.
- pH from the common PaCO2 and HCO3 (P2K-2); no opioid acid-base rule.
- Pasa: sí.
<!-- /generado:acido -->

## 15. Motor heredado (P2U-1-16)

<!-- generado:legado -->
- Encontrado en el motor heredado: fio2_gain_22_for_opioid sí, naloxone_decay_module sí, opioid_depot_field sí, oxygen_shunt_opioid sí, spontaneous_rr_formula sí (LEGACY_ENGINE_BEHAVIOR).
- depot: legacy's opioid depot is not mapped (no authored course)
- naloxone: legacy scripts a naloxone pool and decay; the core has only a structural availability recovery (kinetics UNSET)
- oxygen: legacy uses its own shunt (0.10) and an opioid FiO2 gain of 22; the core uses the common FiO2 rule (30) and P2T-5's link, no opioid oxygen term
- restored_rr: legacy restores toward 14 breaths/min; the core toward the case's intrinsic RR (a carried 12 / 16 / 20)
- Ajustado al legado: no. Pasa: sí.
<!-- /generado:legado -->

## 16. No regresión

<!-- generado:no_regresion -->
- Registro de P2T-5 reproducido sobre su árbol: sí (anida P2T-3, P2T-1A, P2T-1, P2S-3, P2S-2 y, por ellos, TEP, edema, SCA y GI); intacto sí; su veredicto COMMON_HYPOVENTILATION_OXYGENATION_LINK_READY.
- Disponibilidad de llegada 1 en los perfiles comprometidos: sí.
- Pasa: sí.
<!-- /generado:no_regresion -->

## 17. Prueba contra el árbol de P2T-5

<!-- generado:prueba -->
- Archivos revertidos a los de P2T-5: `clinical_core/decision_pack.py` sí, `clinical_core/derived.py` sí, `clinical_core/integration.py` sí, `clinical_core/lactate_slice.py` sí, `clinical_core/provenance.py` sí, `clinical_core/state.py` sí.
- Archivos comunes fijados por hash: 123, intactos sí.
- Vista de P2T-5: digest sí, su prueba sí, registro sí.
<!-- /generado:prueba -->

## 18. Veredicto

<!-- generado:veredicto -->
- sí — central depression maps cleanly to the common availability (non-empty arrival region at every carried intrinsic RR for both cases, arrival exact, G / L / distress neutral)
- sí — the RR / W / PaCO2 / SpO2 cascade works (U1-U4)
- sí — no G is required without lung pathology (U7, arrival G 0)
- sí — the distress stays inactive (U6)
- sí — naloxone reverses the common cascade structurally (U5, both cases; the recurrence direction for 67f)
- sí — the common equations are unchanged but the declared availability interface; no opioid term, no direct scripting, mechanics untouched (U8-U11, interface audit)
- sí — prior respiratory families unchanged (U12: P2T-5's record on its tree, every other file proven)

**Veredicto: OPIOID_SHADOW_MIGRATION_READY**
<!-- /generado:veredicto -->

## 19. Lectura

### 19.1 Qué deja este paquete

- La cadena respiratoria común representa la depresión respiratoria central **sin enfermedad pulmonar**: un solo
  mecanismo de familia (la disponibilidad central) reproduce la llegada de los dos casos y mueve FR, W, PaCO2, pH, SpO2,
  DO2, D, FC y conciencia sólo por lecturas comunes.
  - G y L quedan en 0 en todos los cursos; el distrés, en 0.
  - La mecánica no cambia: la hipoventilación no se disfraza de falla mecánica.
- `COMMON_OXYGENATION_LINK_INSUFFICIENT` **no** se activó: el enlace de P2T-5 basta para la caída de SpO2, sin escribir
  G ni ecuación de oxígeno propia.
- La naloxona revierte la cascada en estructura, y al pararla la depresión se reanuda (dirección de recurrencia del 67f).
- El contraste primario / secundario sale del mismo mecanismo: el 35m es más profundo que el 67f en las tres FR
  intrínsecas llevadas, con los mismos escritores y las mismas ecuaciones comunes, sin escritor residual por caso.
- La interfaz común añadida es mínima y neutra por defecto: 1 × 1 = 1 exacto, así que todo paquete cerrado queda igual.

### 19.2 Revisión adversarial

Una sola revisión, de sólo lectura, sobre `0b32a0e`. Ningún hallazgo alto; 4 medios y 3 bajos, todos confirmados con
sondas propias. No se cambió ninguna fuente congelada y no se volvió a congelar: los refuerzos son sólo de pruebas
(`test_review_hardening_r1_…` a `_r4_…`).

Lo que la revisión confirmó limpio: sin G, L, distrés ni cambio de mecánica en ningún curso (incluidos recurrencia y
colapso, que U6–U9 no cubren); N nunca leído ni escrito; el diff del núcleo es sólo la interfaz de disponibilidad;
1 × 1 = 1 exacto; naloxona nunca sobre 1; disponibilidad 0 falla cerrado; una sola ruta de oxigenación. Y una prueba
decisiva de que la vista de árbol no esconde comportamiento: con un cambio real en la composición (× 0,999) y la prueba
de hashes satisfecha a mano, las guardas cerradas siguieron fallando (11 fallos). Los parches filtran nombres y
archivos, no números.

- **R1 (media). La exactitud de llegada es algebraica, no evidencia.** Con el HCO3 autorado sobre la referencia, la carga
  ácida es 0 y la FR excitatoria es la intrínseca, así que el par (disponibilidad = FR/I, eficiencia = 40·I/(PaCO2·FR))
  reproduce *cualquier* par FR / PaCO2 autoral. Lo verifiqué con pares fabricados absurdos (FR 2 / PaCO2 200; FR 9,5 /
  PaCO2 55; FR 3 / PaCO2 120): se reproducen exactos. Lo que sí informa: que los dos casos estén hipoventilando
  (0 < disponibilidad < 1, es decir FR autoral bajo la intrínseca), más la identidad de SpO2 y el pH. El texto del
  criterio 1 sugiere más de lo que prueba.
- **R2 (media). La tensión de estado estacionario también es del 67f.** El enunciado congelado nombra al 35m y dice que
  el 67f sólo queda cerca de la referencia en FR intrínseca 12. Los números del propio registro muestran que en 16 y 20
  el 67f comparte la tensión: eficiencia 1,31 y 1,64 (sobre la referencia) y PaCO2 restaurada 30,5 y 24,4 (hipocápnica).
  La decisión docente debe cubrir los dos casos.
- **R3 (media). La dirección de recurrencia se leía en el suelo M2.** En el curso de 120 minutos, SpO2 y DO2 quedan en 0
  desde el minuto 108 (13 filas), y la comprobación congelada compara el minuto 120, o sea el suelo. La dirección se
  sostiene igual antes del suelo, y así queda fijada: entre el minuto en que para el antagonista y la primera SpO2 0, la
  disponibilidad baja, la PaCO2 sube y la SpO2 baja de forma estricta en cada minuto.
- **R4 (media). Booleanos literales o circulares, y la escalera de conciencia no puede moverse.** `opioid_hr_term`,
  `N_written`, `same_writer_types` y `same_common_equations` son literales o tautologías; los hechos son ciertos, pero
  esos booleanos no los prueban. Además, la escalera ADOPTED toma el máximo del nivel de llegada y el nivel por SpO2, y
  ese último tope es 2, el nivel de llegada de los dos casos: el nivel queda estructuralmente fijo en 2 y no registra ni
  la profundización ni la recuperación con naloxona. La frase «lee sólo SpO2» es honesta sobre la entrada, no sobre la
  alcanzabilidad.
- **Bajos.** La región de llegada es en realidad una curva de un parámetro, informada como dos bandas (los pares válidos
  sólo existen emparejados por punto); seis análisis (colapso, oxígeno, ácido-base, conciencia, FC, contraste, legado) se
  publican pero no entran en la regla del veredicto, aunque las pruebas sí los verifican; y
  `_records_only_availability` no mira transiciones, eventos ni demanda, cerrado en la práctica por la auditoría AST de
  los escritores.

### 19.3 Limitaciones y deudas (TD-124)

- **Disponibilidad de llegada:** UNSET. Se lleva como región `FAMILY_CANDIDATE` por FR intrínseca (35m 0,30–0,50; 67f
  0,40–0,67). No se eligió ningún valor.
- **`STEADY_STATE_W_ARRIVAL_TENSION`:** la PaCO2 común es algebraica, de modo que el producto FR × PaCO2 autoral fija
  FR intrínseca / eficiencia. Con la banda llevada 12–20, el 35m exige eficiencia 1,16–1,93, por encima de la referencia
  y contra las «respiraciones superficiales» autorales, y restaurar la disponibilidad a 1 da PaCO2 de 20,7 a 34,5. El 67f
  roza la referencia sólo en FR intrínseca 12. Salidas posibles, ninguna elegida: FR intrínseca bajo la banda llevada,
  cinética de CO2 (la llegada no estaría en estado estacionario), o eficiencia sobre 1 tal como se lee (la región que
  P2S-2 aceptó, «mecánica no reducida»). **Decisión docente.**
- **`OPIOID_HR_FAMILY_GAP`:** la FC autoral del 67f (62) queda 1,89 lpm bajo la banda del modelo (63,9–65,9). No se
  agregó ningún término opioide de FC. El 35m sí cae dentro de su banda.
- **`NALOXONE_KINETICS_UNSET` y `RECURRENCE_KINETICS_UNSET`:** sin curso posterior autorado, las tasas son sintéticas y
  la recurrencia es sólo la depresión que se reanuda al parar el antagonista.
- **`CONSCIOUSNESS_INTEGRATION_DEBT`:** la escalera ADOPTED lee sólo SpO2, así que el toxídromo (obnubilación, pupilas
  pequeñas) y la encefalopatía hipercápnica no se separan. N no se escribe ni se lee.
- **`FIO2_RESPONSE_MAGNITUDE_DEBT`** sigue abierta; se usó la regla común sin cambios.
- **Deudas heredadas de P2T-5 que esta familia ejercita:** M1, el bucle metabólico compensador desfasado un minuto
  (aquí sí se cruza la reserva de extracción, porque la entrega cae); y M2, el suelo silencioso de SpO2 0.
- **Sonda de colapso:** sólo dirección. Con el empeoramiento severo sintético a 120 minutos, las magnitudes del final
  (PaCO2 1372, SpO2 0, DO2 0) no son fisiológicas: son el producto de un empeoramiento sin cota más el suelo M2. Se lee
  la dirección (la entrega baja, D sube) y nada más; no hay regla ni umbral de colapso opioide.
- **Motor heredado:** clasificado, no ajustado. No se mapean el depósito opioide, la dosis ni la vía.

### 19.4 Siguiente paso

Auditoría de sólo lectura del estrés sistémico y la FC no respiratoria (P2V-0), que es el hueco que queda abierto en
TD-122 y TD-124 (el residual del SCA, el β-agonista, el dolor, la hipoglucemia y la fiebre). No se inicia aquí ninguna
implementación.
