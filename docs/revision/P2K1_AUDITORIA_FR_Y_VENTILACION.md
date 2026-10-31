# P2K-1 · Auditoría estructural de la FR y del impulso ventilatorio

- **Fecha:** 2026-10-31. **Rama:** `phase-2-clinical-core-shadow`. **Base:** `6aad5cc` (P2J-4, cerrado).
- **Congelamiento:** `c1952da` (digest `a3f098de…`), antes de leer cualquier trayectoria clínica de FR.
  - Antes de congelar, las sondas estructurales imprimieron sólo sus propios valores sintéticos, y una prueba de rutas
    de código sobre dos supervivientes sintéticos imprimió sólo claves y booleanos.
  - Se subió el lactato de llegada de las sondas a 2,5, por encima del umbral de impulso, para que las sondas leyeran
    un cambio.
- **Números:** `docs/revision/P2K1_rr_audit.json`. Generador de los bloques: `python -m clinical_core.rr_audit_report`.
- **Alcance:** sólo sombra; el núcleo no cambia. Sin aprobación ni envolvente de FR, sin recalibrar conciencia, sin
  colapso, sin migraciones ni integración en tiempo de ejecución, sin reabrir sangre, líquidos, lactato, FC ni presión.

## Resumen

- **La FR actual sale de W y de la concentración de lactato:** FR = (FR de llegada − la parte que se atribuye al
  lactato de llegada) × (1 + W⁺) + impulso metabólico(lactato), con techo y piso.
  - No lee D, déficit, SpO2, glucosa, pH, pCO2 ni FC.
  - D llega a la FR sólo por el lactato que produce. Así se explica que el cambio de D de P2I-2AC moviera la FR.
- **El lactato es un sustituto, no un controlador:** BIOMARKER_PROXY_REQUIRES_REFACTOR.
  - El impulso «acidémico» lee directamente la concentración de lactato; no hay carga ácida, pH ni bicarbonato.
  - El valor de la ganancia es el heredado del motor GI (LEGACY_ARTIFACT).
  - Sonda B: subir el lactato sin déficit, sin D y con W = 0 sube la FR 14 rpm.
  - Con la misma D, un aclaramiento más rápido baja la FR (dirección 3, violada por el sustituto).
  - En la hemorragia sin tratamiento de 72f, la FR baja de 24 a 23,4–23,6 entre los 15 y los 30 min, aunque la
    hemorragia sigue: al principio el lactato de llegada se aclara más rápido de lo que D lo produce.
- **W es una construcción mixta (MIXED_DRIVE_AND_VENTILATION_CONSTRUCT):**
  - se define como ventilación respecto a la necesidad, pero se lee como impulso o carga: W > 0 sube la FR y W < 0 la
    baja;
  - ningún módulo GI escribe W; sólo dos sondas sintéticas;
  - no hay una salida de ventilación efectiva aparte de la FR.
- **Equilibrio ácido-base:**
  - pH, pCO2 y bicarbonato son sólo observaciones de la gasometría de llegada (el HCO3 lo calcula el banco de casos);
  - la carga ácida metabólica y la compensación respiratoria no están modeladas;
  - **la acidosis metabólica no puede llevar a la FR sin pasar por el lactato.**
- **Sondas:**
  - A, D y E no son representables.
  - B sube la FR sólo por el lactato.
  - C: el déficit llega a la FR sólo por D → lactato, con retraso; con el lactato fijo la FR no cambia aunque D crezca.
  - La FR no tiene impulso hipoxémico propio.
  - El oxígeno mejora la SpO2 sin tocar la FR ni W.
- **Soporte respiratorio:** sólo FiO2, que mueve la SpO2. No existen VNI, ventilación invasiva, PEEP ni modo; no hay
  ventilación mecánica que pueda imponerse a la FR espontánea, y ningún escenario GI ventila.
- **Reconstrucción R1–R4:** sin cambiar ningún parámetro.
  - 5364 trayectorias reconstruidas desde la fisiología certificada de P2J-3, iguales al núcleo en las 48 corridas de
    validación.
  - Sin tratamiento, 57m sube de 26 a ≈ 35 rpm a los 120 min y 72f de 24 a ≈ 28–30.
  - Con manejo definitivo, 57m baja a ≈ 21–24 y 72f a ≈ 15–16, por debajo de la llegada, a medida que se aclara el
    lactato.
  - R3 (GR sin hemostasia) y R4 coinciden hasta los 120 min: tras las GR el déficit efectivo es 0 en los dos (la
    reserva de extracción lo absorbe), D se repaga igual y la FR también.
- **Dependencias:**
  - La FR depende de la demanda y de g a través de déficit → D → lactato. Con g, la diferencia máxima es de 0,18 rpm
    (mediana) y 2,45 como máximo.
  - MAP_set, la ganancia del barorreflejo y la región latente de FC no llegan a la FR y no se multiplican.
- **Corrección estructural: ninguna.** Ninguna es clara sin un estado nuevo. **Superficie candidata: ninguna.**
- **Veredicto: RR_STRUCTURE_NOT_READY — ACID_BASE_STATE_REQUIRED.** Falta, como mínimo, un estado de carga ácida
  metabólica y una representación del CO2 (§16).

## 1. Decisiones docentes registradas (generado)

<!-- generado:decisiones -->
- **incertidumbre que se lleva**: MAP_set 80 / 90 / 100 not selected; baroreflex gain conditional on demand (1.0: 0.25 / 0.5; 1.1: 0.25 / 0.5 / 1.0 / 1.5), not collapsed into one range; nothing FACULTY_APPROVED
- **dominios cerrados**: P2J-4 accepted (BAROREFLEX_HR_RECERTIFICATION_SATISFIED); BloodState, preload, P, T, the pressure mapping, D, lactate and HR / baroreflex stay closed and are not reopened or silently recalibrated
- **D**: D is not accepted as a direct ventilatory controller
- **fecha**: 2026-10-31
- **parada temprana**: a needed new major state (mechanics, fatigue, PaCO2, acid-base controller) stops the package before any numeric range; missing physiology is not hidden behind RR gains
- **KD-S1**: RR from ventilatory need / W plus metabolic / acidaemic drive; no lactate-clearance-induced bradypnoea while ventilatory need remains
- **lactato**: lactate concentration is a biomarker, not itself a respiratory controller; a lactate-related path is acceptable only as an explicit metabolic acid load, acidaemia or CO2-production signal in the state model; a direct lactate -> RR mapping is BIOMARKER_PROXY_REQUIRES_REFACTOR and its gain is not tuned
- **alcance**: shadow only; no runtime integration, GI or second-family migration, final RR approval, RR hard envelope, consciousness recalibration, collapse activation, legacy fitting or upstream recalibration
- **W y FR**: W is effective alveolar ventilation relative to physiologic need (drive, mechanics, fatigue where represented); RR is an observable; higher RR is not automatically higher effective ventilation
<!-- /generado:decisiones -->

## 2. La ecuación actual de la FR (generado)

<!-- generado:ecuacion -->
derive(state) -> lactate L = max(min(floor, L_arrival), baseline + aux.lactate_excess); RR = respiratory_rate(state, anchors, profile, L). With M(x) = rr_metabolic_max x (1 - exp(-rr_per_lactate x max(0, x - lactate_drive_threshold) / rr_metabolic_max)): the arrival RR splits into an arrival metabolic share S = min(M(L0), max(0, RR0 - rr_ventilatory_floor)) and a ventilatory part (RR0 - S) x (1 + max(0, W)); the metabolic part is S + M(L) - M(L0) when M(L) >= M(L0), else S x M(L) / M(L0); RR = min(rr_max, max(0, 1 + min(0, W)) x (ventilatory + metabolic)); 0 without a pulse. L0 and RR0 are the authored arrival lactate and RR. The aux lactate excess follows dX = debt_to_lactate_gain x D - X / tau_lactate on the minute before's D.

- `respiratory_rate` lee: `anchors.lactate`, `anchors.respiratory_rate`, `profile.rr_max`, `profile.rr_ventilatory_floor`, `state.W`; llama a `_metabolic_drive`, `max`, `min`.
- `_metabolic_drive` lee: `math.exp`, `profile.lactate_drive_threshold_mmol_l`, `profile.rr_metabolic_max`, `profile.rr_per_lactate`.
- `lactate_after_minute` lee: `profile.debt_to_lactate_gain`, `profile.lactate_clearance_tau_min`, `state.D`.
- Parámetros de la FR: `rr_per_lactate`, `lactate_drive_threshold_mmol_l`, `rr_metabolic_max`, `rr_ventilatory_floor`, `rr_max`.
<!-- /generado:ecuacion -->

## 3. Contribuyentes y clasificación (generado)

<!-- generado:contribuyentes -->
| contribuyente | clase | vía |
|---|---|---|
| baseline / intrinsic RR | VALID_CAUSAL_PATH | anchors.respiratory_rate, the authored arrival RR (26 / 24): the arrival fixed point and the ventilatory part's scale; no intrinsic or resting RR exists apart from it |
| arrival metabolic share | BIOMARKER_PROXY | S = min(M(arrival lactate), RR0 - floor): part of the authored arrival RR is attributed to the arrival lactate concentration, not to an acid load |
| W | SEMANTIC_LEAK | W > 0 multiplies the ventilatory part (read as load or drive), W < 0 scales the whole RR down (depressed drive); W is defined as ventilation relative to need, so the two signs read two different physiologies; no GI module writes W |
| effective oxygen deficit | NOT_CURRENTLY_MODELED | no direct path; it reaches RR only through D -> lactate production -> lactate concentration |
| D | BIOMARKER_PROXY | no direct read; D produces lactate (debt_to_lactate_gain x D, lactate_after_minute), and the lactate concentration drives RR: the P2I-2AC D change moved RR through this chain |
| lactate | BIOMARKER_PROXY | the derived lactate concentration drives the metabolic part directly (_metabolic_drive, documented as 'acidaemia'); no acid load, pH or bicarbonate stands behind it: BIOMARKER_PROXY_REQUIRES_REFACTOR |
| lactate gain value | LEGACY_ARTIFACT | rr_per_lactate 7.5 is the legacy GI RR gain (15 per circulation unit / lactate 2 per unit), PARAMETERS |
| pH | NOT_CURRENTLY_MODELED | no state or derived output; authored ABG only |
| pCO2 | NOT_CURRENTLY_MODELED | no state or derived output; authored ABG only |
| metabolic demand | NOT_CURRENTLY_MODELED | no CO2-production path; demand reaches RR only through the deficit -> D -> lactate chain |
| hypoxaemia | NOT_CURRENTLY_MODELED | RR reads no SpO2; hypoxaemia drives the sympathetic HR drive only (sympathetic_target) |
| glucose | NOT_CURRENTLY_MODELED | RR reads no glucose (the sympathetic drive does) |
| drugs | NOT_CURRENTLY_MODELED | demand modifiers reach RR only through the lactate chain; respiratory depressants exist only as the synthetic W -0.7 probe (bands 'opioid') |
| respiratory support | NOT_CURRENTLY_MODELED | Oxygen sets FiO2, which moves SpO2 only; no NIV, invasive ventilation, PEEP or mode |
| mechanics | NOT_CURRENTLY_MODELED | no mechanics state; the synthetic W +0.5 'work' probe (bands 'bronchospasm') raises RR |
| fatigue | NOT_CURRENTLY_MODELED | no fatigue state |
| caps / floors | VALID_CAUSAL_PATH | rr_max (safety bound), rr_metabolic_max (saturation), rr_ventilatory_floor (split bound), max(0, ...) on the W < 0 scaling: bounds, not physiology |
| case-specific terms | VALID_CAUSAL_PATH | only the authored arrival RR and lactate of each case (anchors); no case gain |
| legacy terms | LEGACY_ARTIFACT | the lactate gain's value (above); no legacy RR is read at run time |
<!-- /generado:contribuyentes -->

## 4. La vía D → FR (generado)

<!-- generado:ruta_d -->
1. `integration.step`: _oxygen_debt writes D for the minute from the delivery shortfall (demand, delivery, reserve)
2. `integration.step`: aux.lactate_excess_mmol_l = lactate_after_minute(state, profile): production debt_to_lactate_gain x D of the minute before, clearance X / tau_lactate
3. `derived.derive`: lactate = max(min(lactate_floor, anchors.lactate), lactate_baseline + lactate_excess)
4. `derived.derive`: rr = respiratory_rate(state, anchors, profile, lactate)
5. `derived.respiratory_rate`: metabolic part from _metabolic_drive(lactate); state.W the only other state read

Sonda C (bomba 0,3 durante 20 min): con producción de lactato la FR pasa de 16.0 a 16.2 (D al final 5.0); con el lactato fijo (producción 0) la FR queda en 16.0 aunque D llegue a 5.0. Cambio en el primer minuto: 0.00. La FR se mueve sólo con el lactato: sí.
<!-- /generado:ruta_d -->

## 5. W (generado)

<!-- generado:w -->
- **llegada**: 0.0
- **cómo cambia**: only through contributor deltas; no core equation moves W
- **clase**: MIXED_DRIVE_AND_VENTILATION_CONSTRUCT
- **significado**: C7, 'deviation of alveolar ventilation relative to need (drive, mechanics, fatigue)' (state.py), 0 at arrival; integration bounds it to [-10, 10] as a guard ('no module writes W yet')
- **pCO2**: NOT_MODELED (no pCO2)
- **pH**: NOT_MODELED (no pH)
- **lectores**: derived.respiratory_rate only in the physiology (not SpO2, D, lactate or HR); the offline P2G decision pack keeps a copy of the RR split (decision_pack.rr_parts) and checks W = 0 at a GI arrival
- **FR**: W > 0 multiplies the ventilatory part of RR; W < 0 scales the whole RR down
- **espontánea frente a mecánica**: not representable: there is no mechanical ventilation
- **soporte**: oxygen (FiO2) does not touch W; NIV and invasive ventilation do not exist
- **por qué**: defined as ventilation relative to need, read as a drive / load: a bronchospasm load (less effective ventilation) is written as W > 0 and raises RR, a depressed drive (less ventilation) as W < 0 and lowers it; no output reports effective ventilation, and RR is the only ventilatory observable
- **escritores**: no GI or core module; only the synthetic calibration probes (bands 'bronchospasm' W +0.5 as work, 'opioid' W -0.7 as drive)
- **archivos del núcleo que nombran W**: `clinical_core/bands.py`, `clinical_core/decision_pack.py`, `clinical_core/derived.py`, `clinical_core/integration.py`, `clinical_core/state.py`.
<!-- /generado:w -->

## 6. Representación ácido-base (generado)

<!-- generado:acido_base -->
| magnitud | clase | dónde |
|---|---|---|
| bicarbonate | AUTHORED_OBSERVATION_ONLY | computed by the case bank from pH and PaCO2 (clinical_cases.py:251), not authored |
| metabolic acid load | NOT_MODELED | no state; lactate concentration stands in for it in RR |
| pCO2 | AUTHORED_OBSERVATION_ONLY | arrival ABG (PaCO2 31 / 33 mmHg) |
| pH | AUTHORED_OBSERVATION_ONLY | arrival ABG of each case (gi_reference 'abg') |
| respiratory compensation | NOT_MODELED | only the lactate-concentration term of RR; no pCO2 to compensate |

¿Puede representarse acidosis metabólica → impulso ventilatorio sin el lactato? no: no state or derived quantity carries an acid load, pH, bicarbonate or pCO2; the only metabolic input to RR is the lactate concentration.
<!-- /generado:acido_base -->

## 7. Sondas estructurales (generado)

<!-- generado:sondas -->
FR de llegada de la sonda: 16.0.

| sonda | qué | resultado | vía |
|---|---|---|---|
| A | normal oxygen delivery + metabolic acidosis | NOT_REPRESENTABLE | none: no acid-load, pH or bicarbonate input exists; only a lactate rise would move RR (B) |
| B | high lactate + normal acid-base / ventilatory need | RR_RISES_FROM_LACTATE_ALONE (FR 30.0, +14.0) | lactate concentration -> _metabolic_drive -> RR (BIOMARKER_PROXY) |
| C | effective oxygen deficit + normal acid-base state | FR solo con lactato | deficit -> D -> lactate production -> lactate concentration -> RR; no direct deficit or D read |
| D | high pCO2 / inadequate W | NOT_REPRESENTABLE (W −0,5: FR 8.0) | no pCO2; the only writable 'inadequate ventilation' is W < 0, read as depressed drive: RR falls (no compensation) |
| E | RR high + mechanical / fatigue limitation | NOT_REPRESENTABLE (W +0,5: FR 22.3) | no effective-ventilation output apart from RR; a load written as W > 0 raises RR and nothing reports that ventilation stays inadequate |

- Hipoxemia: FR con SpO2 85 = 16.0, con 97 = 16.0; impulso hipoxémico propio de la FR: no.
- Oxígeno (FiO2 0.60): SpO2 97.0 → 100.0; FR 16.0 → 16.0; W 0.0; sólo oxigenación: sí.
- Aclaramiento con la misma D (20.0): τ 30 min → lactato 2.79, FR 17.8; τ 120 min → lactato 3.03, FR 19.1.

Synthetic, structural only (no gain read from them), on the neutral arrival (RR0 16, demand met, FiO2 0.21) with its lactate at 2.5 (above the 2.0 drive threshold, so a change is read), at the default RR parameters with reserve 2.5. A: an acid load with normal delivery is not representable. B: the RR the core derives at lactate 6 with no deficit, no D and W 0, against arrival. C: the pump cut to 0.3 for 20 minutes (an effective deficit, D accruing) with the default lactate production and with production 0 (lactate held), so any RR response is attributed to its path. D: pCO2 is not representable; W -0.5 (the only 'inadequate ventilation' the core can write) is read. E: an effective-ventilation output separate from RR does not exist; W +0.5 is read. Hypoxaemia: arrival SpO2 85 against 97. Oxygen: FiO2 0.6 from minute 1. Clearance: the same steady D with tau_lactate 30 and 120 min.
<!-- /generado:sondas -->

## 8. Soporte respiratorio (generado)

<!-- generado:soporte -->
- **FiO2**: a setting; read by SpO2 only
- **NIV / BiPAP**: NOT_MODELED
- **PEEP**: NOT_MODELED
- **gi_scenarios**: L1, L2, L3 without haemostasis and L3 carry no oxygen or ventilatory support (room air, FiO2 0.21)
- **invasive ventilation**: NOT_MODELED
- **mechanical override**: NOT_REPRESENTABLE: with no mechanical ventilation, no controlled rate can override the spontaneous RR; no current scenario ventilates, so there is no live contradiction
- **pCO2 / pH**: NOT_MODELED: no support can move them
- **supplemental oxygen**: Oxygen writes the FiO2 setting; SpO2 = arrival SpO2 + 30 x (FiO2 - arrival FiO2 above room air); W, RR, D and lactate unchanged by it
- **ventilation mode**: NOT_MODELED
<!-- /generado:soporte -->

## 9. Observaciones respiratorias del caso (generado)

<!-- generado:observado -->
| caso | dato | valor | origen | fuente |
|---|---|---|---|---|
| 57m | abg | pH 7.37, PaCO2 31, HCO3 17.3, PaO2 91 on FiO2 21% (HCO3: MODEL_DERIVED (computed by the case bank), PaCO2: AUTHORED_OBSERVATION, PaO2: AUTHORED_OBSERVATION, pH: AUTHORED_OBSERVATION) | AUTHORED_OBSERVATION | clinical_cases.py:901 |
| 57m | lactate_mmol_l | 4.4 | AUTHORED_OBSERVATION | clinical_cases.py:900 |
| 57m | later_respiratory_observations | none authored | NOT_STATED | — |
| 57m | lungs | no B-lines; chest X-ray without oedema | AUTHORED_OBSERVATION | clinical_cases.py:903 |
| 57m | oxygen_support | room air (FiO2 0.21) | LEGACY_REFERENCE | family_engine.py:973 |
| 57m | respiratory_rate | 26 | AUTHORED_OBSERVATION | clinical_cases.py:881 |
| 57m | spo2 | 97 | AUTHORED_OBSERVATION | clinical_cases.py:881 |
| 57m | work_of_breathing | not stated | NOT_STATED | — |
| 72f | abg | pH 7.40, PaCO2 33, HCO3 19.8, PaO2 84 on FiO2 21% (HCO3: MODEL_DERIVED (computed by the case bank), PaCO2: AUTHORED_OBSERVATION, PaO2: AUTHORED_OBSERVATION, pH: AUTHORED_OBSERVATION) | AUTHORED_OBSERVATION | clinical_cases.py:930 |
| 72f | lactate_mmol_l | 3.4 | AUTHORED_OBSERVATION | clinical_cases.py:929 |
| 72f | later_respiratory_observations | none authored | NOT_STATED | — |
| 72f | lungs | no B-lines; no acute cardiopulmonary abnormality on X-ray | AUTHORED_OBSERVATION | clinical_cases.py:932 |
| 72f | oxygen_support | room air (FiO2 0.21) | LEGACY_REFERENCE | family_engine.py:973 |
| 72f | respiratory_rate | 24 | AUTHORED_OBSERVATION | clinical_cases.py:910 |
| 72f | spo2 | 96 | AUTHORED_OBSERVATION | clinical_cases.py:910 |
| 72f | work_of_breathing | not stated | NOT_STATED | — |
<!-- /generado:observado -->

## 10. Reconstrucción de la FR actual, R1–R4 (generado)

<!-- generado:reconstruccion -->
FR por escenario, caso, demanda y ganancia de tono g: mediana [rango] sobre las trayectorias únicas de los supervivientes de P2J-3; entre paréntesis, las medianas de lactato (mmol/L), D y déficit efectivo relativo. W = 0, pH y pCO2 no modelados, impulso hipoxémico no modelado, aire ambiente (FiO2 0,21).

**R1 · hemorragia sin tratamiento (L1) · 57m**

| demanda · g | n | min 0 | min 15 | min 30 | min 60 | min 90 | min 120 |
|---|---|---|---|---|---|---|---|
| 1 · 0.25 | 18 | 26.0 [26.0–26.0] (4.40; 60.0; 0.40) | 26.9 [26.9–26.9] (4.66; 72.5; 0.44) | 28.1 [28.0–28.1] (5.02; 86.3; 0.48) | 30.8 [30.7–30.8] (6.05; 117.3; 0.56) | 33.4 [33.2–33.4] (7.50; 152.9; 0.64) | 35.4 [35.2–35.5] (9.37; 193.3; 0.71) |
| 1 · 0.5 | 18 | 26.0 [26.0–26.0] (4.40; 60.0; 0.40) | 26.9 [26.9–26.9] (4.66; 72.6; 0.44) | 28.1 [28.0–28.1] (5.02; 86.3; 0.48) | 30.8 [30.7–30.8] (6.05; 117.5; 0.56) | 33.4 [33.2–33.4] (7.52; 153.5; 0.64) | 35.5 [35.3–35.5] (9.40; 194.2; 0.72) |
| 1 · 1 | 18 | 26.0 [26.0–26.0] (4.40; 60.0; 0.40) | 26.9 [26.9–26.9] (4.66; 72.6; 0.44) | 28.1 [28.0–28.1] (5.02; 86.5; 0.48) | 30.8 [30.7–30.8] (6.06; 118.0; 0.57) | 33.4 [33.3–33.4] (7.53; 154.4; 0.65) | 35.5 [35.3–35.5] (9.43; 195.5; 0.73) |
| 1.1 · 0.25 | 37 | 26.0 [26.0–26.0] (4.40; 60.0; 0.45) | 28.5 [28.5–28.5] (5.15; 63.9; 0.49) | 30.2 [30.2–30.2] (5.80; 68.0; 0.52) | 32.5 [32.4–32.5] (6.93; 77.2; 0.59) | 34.0 [33.9–34.0] (7.97; 87.4; 0.66) | 35.1 [35.0–35.2] (9.02; 98.9; 0.74) |
| 1.1 · 0.5 | 37 | 26.0 [26.0–26.0] (4.40; 60.0; 0.45) | 28.5 [28.5–28.5] (5.15; 63.9; 0.49) | 30.2 [30.2–30.2] (5.80; 68.1; 0.52) | 32.5 [32.4–32.5] (6.93; 77.2; 0.59) | 34.0 [33.9–34.0] (7.98; 87.5; 0.66) | 35.1 [35.0–35.2] (9.03; 99.0; 0.74) |
| 1.1 · 1 | 37 | 26.0 [26.0–26.0] (4.40; 60.0; 0.45) | 28.5 [28.5–28.5] (5.15; 63.9; 0.49) | 30.2 [30.2–30.2] (5.81; 68.1; 0.53) | 32.5 [32.5–32.5] (6.94; 77.3; 0.59) | 34.0 [34.0–34.0] (7.98; 87.7; 0.67) | 35.1 [35.0–35.2] (9.05; 99.3; 0.75) |

**R1 · hemorragia sin tratamiento (L1) · 72f**

| demanda · g | n | min 0 | min 15 | min 30 | min 60 | min 90 | min 120 |
|---|---|---|---|---|---|---|---|
| 1 · 0.25 | 18 | 24.0 [24.0–24.0] (3.40; 20.0; 0.15) | 23.6 [23.6–23.6] (3.32; 25.0; 0.19) | 23.6 [23.5–23.6] (3.31; 31.2; 0.23) | 24.5 [24.4–24.5] (3.51; 47.0; 0.30) | 26.8 [26.3–26.8] (4.01; 67.3; 0.38) | 29.8 [29.0–29.8] (4.84; 92.3; 0.46) |
| 1 · 0.5 | 18 | 24.0 [24.0–24.0] (3.40; 20.0; 0.15) | 23.6 [23.6–23.6] (3.32; 25.1; 0.19) | 23.6 [23.6–23.6] (3.31; 31.3; 0.23) | 24.6 [24.4–24.6] (3.51; 47.4; 0.31) | 26.8 [26.4–26.9] (4.03; 68.4; 0.39) | 29.9 [29.1–30.0] (4.88; 94.0; 0.47) |
| 1 · 1 | 18 | 24.0 [24.0–24.0] (3.40; 20.0; 0.15) | 23.6 [23.6–23.6] (3.32; 25.1; 0.19) | 23.6 [23.6–23.6] (3.32; 31.6; 0.24) | 24.6 [24.4–24.6] (3.53; 48.4; 0.33) | 27.0 [26.5–27.0] (4.07; 70.4; 0.41) | 30.2 [29.3–30.2] (4.97; 97.2; 0.49) |
| 1.1 · 0.25 | 37 | 24.0 [24.0–24.0] (3.40; 20.0; 0.23) | 23.5 [23.5–23.5] (3.30; 22.0; 0.26) | 23.4 [23.4–23.4] (3.29; 24.3; 0.29) | 24.3 [24.2–24.3] (3.46; 29.6; 0.36) | 26.0 [25.8–26.1] (3.83; 36.0; 0.43) | 28.1 [27.7–28.2] (4.36; 43.7; 0.50) |
| 1.1 · 0.5 | 37 | 24.0 [24.0–24.0] (3.40; 20.0; 0.23) | 23.5 [23.5–23.5] (3.30; 22.0; 0.26) | 23.4 [23.4–23.4] (3.29; 24.3; 0.30) | 24.3 [24.2–24.3] (3.46; 29.7; 0.36) | 26.0 [25.8–26.1] (3.84; 36.2; 0.43) | 28.2 [27.7–28.3] (4.37; 44.0; 0.51) |
| 1.1 · 1 | 37 | 24.0 [24.0–24.0] (3.40; 20.0; 0.23) | 23.5 [23.5–23.5] (3.30; 22.0; 0.27) | 23.4 [23.4–23.4] (3.29; 24.4; 0.30) | 24.3 [24.2–24.4] (3.47; 29.9; 0.37) | 26.1 [25.9–26.2] (3.86; 36.6; 0.45) | 28.3 [27.8–28.4] (4.41; 44.6; 0.53) |

**R2 · cristaloide (L2) · 57m**

| demanda · g | n | min 0 | min 15 | min 30 | min 60 | min 90 | min 120 |
|---|---|---|---|---|---|---|---|
| 1 · 0.25 | 216 | 26.0 [26.0–26.0] (4.40; 60.0; 0.40) | 26.9 [26.9–26.9] (4.65; 69.7; 0.26) | 27.8 [27.8–27.9] (4.95; 77.0; 0.25) | 29.9 [29.8–30.0] (5.68; 94.0; 0.32) | 31.9 [31.7–32.2] (6.62; 115.6; 0.40) | 33.8 [33.6–34.2] (7.83; 141.7; 0.48) |
| 1 · 0.5 | 181 | 26.0 [26.0–26.0] (4.40; 60.0; 0.40) | 26.9 [26.9–26.9] (4.65; 69.6; 0.25) | 27.8 [27.8–27.9] (4.95; 76.8; 0.25) | 29.9 [29.8–30.0] (5.68; 93.7; 0.32) | 31.9 [31.8–32.2] (6.62; 115.3; 0.41) | 33.8 [33.6–34.2] (7.82; 141.8; 0.49) |
| 1 · 1 | 134 | 26.0 [26.0–26.0] (4.40; 60.0; 0.40) | 26.9 [26.9–26.9] (4.65; 69.5; 0.24) | 27.8 [27.8–27.9] (4.94; 76.3; 0.24) | 29.8 [29.8–30.0] (5.66; 93.3; 0.32) | 31.9 [31.8–32.2] (6.61; 115.2; 0.41) | 33.8 [33.6–34.1] (7.81; 142.5; 0.49) |
| 1.1 · 0.25 | 444 | 26.0 [26.0–26.0] (4.40; 60.0; 0.45) | 28.4 [28.4–28.4] (5.15; 63.2; 0.33) | 30.1 [30.1–30.1] (5.76; 65.8; 0.32) | 32.1 [32.0–32.2] (6.72; 71.7; 0.39) | 33.4 [33.3–33.5] (7.52; 78.7; 0.46) | 34.4 [34.2–34.6] (8.29; 86.8; 0.52) |
| 1.1 · 0.5 | 444 | 26.0 [26.0–26.0] (4.40; 60.0; 0.45) | 28.4 [28.4–28.4] (5.15; 63.2; 0.32) | 30.1 [30.1–30.1] (5.76; 65.7; 0.32) | 32.1 [32.0–32.2] (6.71; 71.6; 0.38) | 33.4 [33.2–33.5] (7.51; 78.5; 0.46) | 34.4 [34.2–34.6] (8.28; 86.6; 0.52) |
| 1.1 · 1 | 444 | 26.0 [26.0–26.0] (4.40; 60.0; 0.45) | 28.4 [28.4–28.4] (5.15; 63.1; 0.31) | 30.1 [30.0–30.1] (5.76; 65.6; 0.31) | 32.1 [32.0–32.2] (6.70; 71.3; 0.38) | 33.4 [33.2–33.5] (7.49; 78.3; 0.45) | 34.3 [34.1–34.6] (8.25; 86.4; 0.52) |

**R2 · cristaloide (L2) · 72f**

| demanda · g | n | min 0 | min 15 | min 30 | min 60 | min 90 | min 120 |
|---|---|---|---|---|---|---|---|
| 1 · 0.25 | 216 | 24.0 [24.0–24.0] (3.40; 20.0; 0.15) | 23.6 [23.6–23.6] (3.32; 22.7; 0.04) | 23.3 [23.1–23.3] (3.26; 23.6; 0.04) | 23.0 [22.3–23.3] (3.20; 27.6; 0.10) | 23.4 [22.1–24.0] (3.28; 35.5; 0.17) | 24.6 [22.8–25.7] (3.53; 47.7; 0.24) |
| 1 · 0.5 | 181 | 24.0 [24.0–24.0] (3.40; 20.0; 0.15) | 23.6 [23.6–23.6] (3.32; 22.6; 0.03) | 23.3 [23.0–23.3] (3.26; 23.3; 0.03) | 22.9 [21.8–23.2] (3.19; 27.0; 0.10) | 23.3 [21.4–23.9] (3.25; 35.0; 0.18) | 24.5 [22.0–25.7] (3.50; 47.8; 0.26) |
| 1 · 1 | 134 | 24.0 [24.0–24.0] (3.40; 20.0; 0.15) | 23.6 [23.6–23.6] (3.31; 22.4; 0.02) | 23.2 [23.0–23.3] (3.23; 19.7; 0.02) | 22.4 [21.6–23.1] (3.10; 22.8; 0.10) | 22.5 [21.3–23.7] (3.10; 31.0; 0.19) | 23.6 [22.0–25.5] (3.32; 45.0; 0.27) |
| 1.1 · 0.25 | 444 | 24.0 [24.0–24.0] (3.40; 20.0; 0.23) | 23.5 [23.5–23.5] (3.29; 21.4; 0.13) | 23.2 [23.2–23.3] (3.25; 22.4; 0.13) | 23.4 [23.2–23.7] (3.28; 25.0; 0.18) | 24.2 [23.7–24.7] (3.45; 28.5; 0.24) | 25.5 [24.8–26.3] (3.72; 33.1; 0.31) |
| 1.1 · 0.5 | 444 | 24.0 [24.0–24.0] (3.40; 20.0; 0.23) | 23.5 [23.5–23.5] (3.29; 21.4; 0.12) | 23.2 [23.2–23.3] (3.25; 22.3; 0.12) | 23.4 [23.1–23.6] (3.27; 24.9; 0.18) | 24.2 [23.6–24.7] (3.44; 28.3; 0.24) | 25.4 [24.6–26.3] (3.71; 33.0; 0.31) |
| 1.1 · 1 | 444 | 24.0 [24.0–24.0] (3.40; 20.0; 0.23) | 23.5 [23.5–23.5] (3.29; 21.4; 0.11) | 23.2 [23.2–23.3] (3.24; 22.2; 0.11) | 23.3 [23.0–23.6] (3.26; 24.5; 0.18) | 24.1 [23.4–24.7] (3.41; 27.9; 0.25) | 25.3 [24.4–26.3] (3.68; 32.7; 0.32) |

**R3 · GR antes de la hemostasia · 57m**

| demanda · g | n | min 0 | min 15 | min 30 | min 60 | min 90 | min 120 |
|---|---|---|---|---|---|---|---|
| 1 · 0.25 | 18 | 26.0 [26.0–26.0] (4.40; 60.0; 0.40) | 26.9 [26.9–26.9] (4.65; 69.5; 0.23) | 27.8 [27.8–27.8] (4.94; 73.9; 0.06) | 28.2 [28.2–28.3] (5.08; 32.4; 0.00) | 26.4 [26.4–26.5] (4.52; 11.7; 0.00) | 23.8 [23.7–23.9] (3.84; 4.2; 0.00) |
| 1 · 0.5 | 18 | 26.0 [26.0–26.0] (4.40; 60.0; 0.40) | 26.9 [26.9–26.9] (4.65; 69.5; 0.22) | 27.8 [27.8–27.8] (4.93; 73.4; 0.03) | 28.0 [28.0–28.1] (5.01; 30.0; 0.00) | 26.1 [26.1–26.2] (4.44; 10.8; 0.00) | 23.4 [23.4–23.5] (3.76; 3.9; 0.00) |
| 1 · 1 | 18 | 26.0 [26.0–26.0] (4.40; 60.0; 0.40) | 26.9 [26.9–26.9] (4.65; 69.3; 0.20) | 27.8 [27.8–27.8] (4.93; 72.5; 0.00) | 27.7 [27.7–27.8] (4.89; 26.2; 0.00) | 25.6 [25.6–25.8] (4.30; 9.5; 0.00) | 22.9 [22.9–23.1] (3.64; 3.4; 0.00) |
| 1.1 · 0.25 | 91 | 26.0 [26.0–26.0] (4.40; 60.0; 0.45) | 28.4 [28.4–28.4] (5.15; 63.2; 0.31) | 30.1 [30.1–30.1] (5.75; 65.2; 0.17) | 31.4 [30.9–31.7] (6.35; 45.5; 0.00) | 28.1 [27.1–29.0] (5.04; 16.5; 0.00) | 22.4 [21.2–23.9] (3.53; 6.0; 0.00) |
| 1.1 · 0.5 | 91 | 26.0 [26.0–26.0] (4.40; 60.0; 0.45) | 28.4 [28.4–28.4] (5.15; 63.2; 0.30) | 30.1 [30.0–30.1] (5.75; 65.1; 0.15) | 31.1 [30.5–31.5] (6.22; 40.9; 0.00) | 27.5 [26.4–28.4] (4.84; 14.8; 0.00) | 21.7 [20.5–22.7] (3.38; 5.4; 0.00) |
| 1.1 · 1 | 91 | 26.0 [26.0–26.0] (4.40; 60.0; 0.45) | 28.4 [28.4–28.4] (5.15; 63.1; 0.29) | 30.1 [30.0–30.1] (5.75; 64.9; 0.13) | 30.5 [30.1–31.1] (5.95; 34.3; 0.00) | 26.4 [25.7–27.5] (4.51; 12.4; 0.00) | 20.5 [19.7–21.7] (3.15; 4.5; 0.00) |

**R3 · GR antes de la hemostasia · 72f**

| demanda · g | n | min 0 | min 15 | min 30 | min 60 | min 90 | min 120 |
|---|---|---|---|---|---|---|---|
| 1 · 0.25 | 18 | 24.0 [24.0–24.0] (3.40; 20.0; 0.15) | 23.6 [23.6–23.6] (3.31; 19.7; 0.00) | 22.9 [22.9–22.9] (3.18; 11.9; 0.00) | 20.7 [20.7–20.8] (2.79; 4.3; 0.00) | 18.3 [18.3–18.3] (2.40; 1.6; 0.00) | 15.9 [15.9–16.0] (2.07; 0.6; 0.00) |
| 1 · 0.5 | 18 | 24.0 [24.0–24.0] (3.40; 20.0; 0.15) | 23.5 [23.5–23.6] (3.31; 19.0; 0.00) | 22.8 [22.8–22.9] (3.17; 11.4; 0.00) | 20.7 [20.7–20.7] (2.78; 4.1; 0.00) | 18.2 [18.2–18.3] (2.39; 1.5; 0.00) | 15.8 [15.8–15.9] (2.06; 0.5; 0.00) |
| 1 · 1 | 18 | 24.0 [24.0–24.0] (3.40; 20.0; 0.15) | 23.5 [23.5–23.5] (3.31; 18.2; 0.00) | 22.8 [22.8–22.8] (3.16; 11.0; 0.00) | 20.6 [20.6–20.6] (2.77; 4.0; 0.00) | 18.1 [18.1–18.1] (2.38; 1.4; 0.00) | 15.8 [15.8–15.8] (2.05; 0.5; 0.00) |
| 1.1 · 0.25 | 91 | 24.0 [24.0–24.0] (3.40; 20.0; 0.23) | 23.5 [23.5–23.5] (3.29; 21.2; 0.06) | 22.9 [22.8–23.1] (3.18; 15.8; 0.00) | 19.3 [19.0–19.8] (2.57; 5.7; 0.00) | 15.4 [15.4–15.6] (1.96; 2.1; 0.00) | 15.4 [15.4–15.4] (1.55; 0.7; 0.00) |
| 1.1 · 0.5 | 91 | 24.0 [24.0–24.0] (3.40; 20.0; 0.23) | 23.5 [23.5–23.5] (3.29; 21.2; 0.05) | 22.8 [22.7–23.0] (3.17; 15.2; 0.00) | 19.2 [18.9–19.6] (2.54; 5.5; 0.00) | 15.4 [15.4–15.4] (1.94; 2.0; 0.00) | 15.4 [15.4–15.4] (1.54; 0.7; 0.00) |
| 1.1 · 1 | 91 | 24.0 [24.0–24.0] (3.40; 20.0; 0.23) | 23.5 [23.4–23.5] (3.29; 21.1; 0.03) | 22.7 [22.5–22.8] (3.14; 14.1; 0.00) | 18.9 [18.6–19.2] (2.50; 5.1; 0.00) | 15.4 [15.4–15.4] (1.91; 1.8; 0.00) | 15.4 [15.4–15.4] (1.52; 0.7; 0.00) |

**R4 · manejo definitivo (L3) · 57m**

| demanda · g | n | min 0 | min 15 | min 30 | min 60 | min 90 | min 120 |
|---|---|---|---|---|---|---|---|
| 1 · 0.25 | 18 | 26.0 [26.0–26.0] (4.40; 60.0; 0.40) | 26.9 [26.9–26.9] (4.65; 69.5; 0.23) | 27.8 [27.8–27.8] (4.94; 73.9; 0.06) | 28.2 [28.2–28.3] (5.08; 32.4; 0.00) | 26.4 [26.4–26.5] (4.52; 11.7; 0.00) | 23.8 [23.7–23.9] (3.84; 4.2; 0.00) |
| 1 · 0.5 | 18 | 26.0 [26.0–26.0] (4.40; 60.0; 0.40) | 26.9 [26.9–26.9] (4.65; 69.5; 0.22) | 27.8 [27.8–27.8] (4.93; 73.4; 0.03) | 28.0 [28.0–28.1] (5.01; 30.0; 0.00) | 26.1 [26.1–26.2] (4.44; 10.8; 0.00) | 23.4 [23.4–23.5] (3.76; 3.9; 0.00) |
| 1 · 1 | 18 | 26.0 [26.0–26.0] (4.40; 60.0; 0.40) | 26.9 [26.9–26.9] (4.65; 69.3; 0.20) | 27.8 [27.8–27.8] (4.93; 72.5; 0.00) | 27.7 [27.7–27.8] (4.89; 26.2; 0.00) | 25.6 [25.6–25.8] (4.30; 9.5; 0.00) | 22.9 [22.9–23.1] (3.64; 3.4; 0.00) |
| 1.1 · 0.25 | 91 | 26.0 [26.0–26.0] (4.40; 60.0; 0.45) | 28.4 [28.4–28.4] (5.15; 63.2; 0.31) | 30.1 [30.1–30.1] (5.75; 65.2; 0.17) | 31.4 [30.9–31.7] (6.35; 45.5; 0.00) | 28.1 [27.1–29.0] (5.04; 16.5; 0.00) | 22.4 [21.2–23.4] (3.53; 6.0; 0.00) |
| 1.1 · 0.5 | 91 | 26.0 [26.0–26.0] (4.40; 60.0; 0.45) | 28.4 [28.4–28.4] (5.15; 63.2; 0.30) | 30.1 [30.0–30.1] (5.75; 65.1; 0.15) | 31.1 [30.5–31.5] (6.22; 40.9; 0.00) | 27.5 [26.4–28.4] (4.84; 14.8; 0.00) | 21.7 [20.5–22.7] (3.38; 5.4; 0.00) |
| 1.1 · 1 | 91 | 26.0 [26.0–26.0] (4.40; 60.0; 0.45) | 28.4 [28.4–28.4] (5.15; 63.1; 0.29) | 30.1 [30.0–30.1] (5.75; 64.9; 0.13) | 30.5 [30.1–31.1] (5.95; 34.3; 0.00) | 26.4 [25.7–27.5] (4.51; 12.4; 0.00) | 20.5 [19.7–21.7] (3.15; 4.5; 0.00) |

**R4 · manejo definitivo (L3) · 72f**

| demanda · g | n | min 0 | min 15 | min 30 | min 60 | min 90 | min 120 |
|---|---|---|---|---|---|---|---|
| 1 · 0.25 | 18 | 24.0 [24.0–24.0] (3.40; 20.0; 0.15) | 23.6 [23.6–23.6] (3.31; 19.7; 0.00) | 22.9 [22.9–22.9] (3.18; 11.9; 0.00) | 20.7 [20.7–20.8] (2.79; 4.3; 0.00) | 18.3 [18.3–18.3] (2.40; 1.6; 0.00) | 15.9 [15.9–16.0] (2.07; 0.6; 0.00) |
| 1 · 0.5 | 18 | 24.0 [24.0–24.0] (3.40; 20.0; 0.15) | 23.5 [23.5–23.6] (3.31; 19.0; 0.00) | 22.8 [22.8–22.9] (3.17; 11.4; 0.00) | 20.7 [20.7–20.7] (2.78; 4.1; 0.00) | 18.2 [18.2–18.3] (2.39; 1.5; 0.00) | 15.8 [15.8–15.9] (2.06; 0.5; 0.00) |
| 1 · 1 | 18 | 24.0 [24.0–24.0] (3.40; 20.0; 0.15) | 23.5 [23.5–23.5] (3.31; 18.2; 0.00) | 22.8 [22.8–22.8] (3.16; 11.0; 0.00) | 20.6 [20.6–20.6] (2.77; 4.0; 0.00) | 18.1 [18.1–18.1] (2.38; 1.4; 0.00) | 15.8 [15.8–15.8] (2.05; 0.5; 0.00) |
| 1.1 · 0.25 | 91 | 24.0 [24.0–24.0] (3.40; 20.0; 0.23) | 23.5 [23.5–23.5] (3.29; 21.2; 0.06) | 22.9 [22.8–23.1] (3.18; 15.8; 0.00) | 19.3 [19.0–19.8] (2.57; 5.7; 0.00) | 15.4 [15.4–15.6] (1.96; 2.1; 0.00) | 15.4 [15.4–15.4] (1.55; 0.7; 0.00) |
| 1.1 · 0.5 | 91 | 24.0 [24.0–24.0] (3.40; 20.0; 0.23) | 23.5 [23.5–23.5] (3.29; 21.2; 0.05) | 22.8 [22.7–23.0] (3.17; 15.2; 0.00) | 19.2 [18.9–19.6] (2.54; 5.5; 0.00) | 15.4 [15.4–15.4] (1.94; 2.0; 0.00) | 15.4 [15.4–15.4] (1.54; 0.7; 0.00) |
| 1.1 · 1 | 91 | 24.0 [24.0–24.0] (3.40; 20.0; 0.23) | 23.5 [23.4–23.5] (3.29; 21.1; 0.03) | 22.7 [22.5–22.8] (3.14; 14.1; 0.00) | 18.9 [18.6–19.2] (2.50; 5.1; 0.00) | 15.4 [15.4–15.4] (1.91; 1.8; 0.00) | 15.4 [15.4–15.4] (1.52; 0.7; 0.00) |

Validación contra el núcleo: 48 corridas completas, FR, D y lactato iguales: sí.
<!-- /generado:reconstruccion -->

## 11. Expectativas direccionales (generado)

<!-- generado:direcciones -->
| # | expectativa | estado | detalle |
|---|---|---|---|
| 1 | greater ventilatory need must not reduce RR if mechanics permit | se cumple sólo para el sustituto (lactato) | true ventilatory need (CO2, acid load) is not represented |
| 2 | resolving metabolic / acidaemic drive permits RR recovery | se cumple |  |
| 3 | lactate decline alone must not force RR down while ventilatory need remains | lo viola el sustituto (lactato) | with the same D, faster lactate clearance lowers RR: RR tracks the concentration, and the core cannot tell a resolving acid load from a persisting one; KD-S1's guard only bounds the fall to the arrival metabolic share |
| 4 | high RR must not imply adequate W when mechanics or fatigue limit ventilation | no representable | no effective-ventilation output apart from RR |
| 5 | mechanical-ventilation semantics override the spontaneous frequency where appropriate | no representable | no mechanical ventilation in the core; no current scenario ventilates |
| 6 | oxygen therapy may improve oxygenation without correcting ventilation | se cumple | FiO2 moves SpO2 only |
| 7 | CO2 clearance follows effective ventilation rather than RR alone | no representable | no CO2 |
| 8 | no instantaneous RR normalization merely from haemostasis | se cumple | mayor cambio de FR en el minuto de la hemostasia 0.14, mayor cambio de un minuto de las trayectorias 0.21; RR follows lactate, which lags D by first-order clearance; no RR term reads haemostasis |

Structural, no RR range: 1 reads RR's monotonicity in lactate and W > 0 (the only 'need' the core has); 2 the RR at the clearance baseline against the ventilatory part; 3 the clearance probe (same D, different tau_lactate); 4, 5, 7 need an effective-ventilation output, mechanical ventilation and CO2, absent; 6 the oxygen probe; 8 the R4 trajectories: no RR term reads haemostasis, and the RR change across the haemostasis minute is compared with the largest one-minute RR change of the same trajectory.
<!-- /generado:direcciones -->

## 12. Dependencias de la incertidumbre previa (generado)

<!-- generado:dependencias -->
| magnitud | vía hasta la FR | diferencia máxima de FR (bpm) |
|---|---|---|
| ganancia del barorreflejo | NONE (as MAP_set) | P2J-4 rows_equal |
| demanda 1,0 / 1,1 | demand -> effective deficit -> D -> lactate -> RR | — |
| región latente de FC | NONE: HR reaches no output, D, lactate or RR (P2I-2AG, P2J-1) | respiratory_rate reads anchors.lactate, anchors.respiratory_rate, profile.rr_max, profile.rr_ventilatory_floor, state.W |
| MAP_set | NONE: the baroreflex moves only the sympathetic drive, which RR, lactate and D never read | P2J-4: every non-HR row, rr included, equal with the baroreflex on and off (654 units) |
| ganancia de tono g | g -> T -> afterload / output -> delivery -> deficit -> D -> lactate -> RR | 0.18 [0.02–2.45] |
<!-- /generado:dependencias -->

## 13. Identificabilidad (generado)

<!-- generado:identificabilidad -->
| magnitud | clase | detalle |
|---|---|---|
| FR basal / intrínseca | PARTIALLY_CONSTRAINED | authored arrival RR 26 / 24 fixes the sum only |
| ganancia metabólica / acidémica | NOT_APPLICABLE | BIOMARKER_PROXY_REQUIRES_REFACTOR |
| ganancia hipoxémica | NOT_APPLICABLE | not modeled |
| acoplamiento W / impulso | NOT_APPLICABLE | MIXED_DRIVE_AND_VENTILATION_CONSTRUCT, no writer |
| techo de FR (rr_max) | NON_IDENTIFIABLE | FR máxima reconstruida 35.5 |
| saturación metabólica | NOT_APPLICABLE | on the lactate proxy |
| piso ventilatorio | NOT_APPLICABLE | splits the arrival RR by the lactate proxy; el piso limita el reparto de llegada: 57m no, 72f no |
| vía D / lactato | NOT_APPLICABLE | BIOMARKER_PROXY_REQUIRES_REFACTOR |

Frozen. A quantity on a path classified BIOMARKER_PROXY, SEMANTIC_LEAK or NOT_CURRENTLY_MODELED is NOT_APPLICABLE (no candidate surface stands on it). The baseline is PARTIALLY_CONSTRAINED: the authored arrival RR fixes the sum of the ventilatory part and the arrival metabolic share, not the split. A bound is NON_IDENTIFIABLE when no reconstructed trajectory reaches it, POORLY_IDENTIFIED when some do.
<!-- /generado:identificabilidad -->

## 14. Veredicto (generado)

<!-- generado:veredicto -->
**RR_STRUCTURE_NOT_READY — ACID_BASE_STATE_REQUIRED**

Bloqueos, en orden:
- `ACID_BASE_STATE_REQUIRED`: falta un estado ácido-base: la acidosis metabólica sólo llega a la FR a través del lactato
- `LACTATE_BIOMARKER_PROXY`: la concentración de lactato manda directamente sobre la FR
- `W_MIXED_DRIVE_AND_VENTILATION`: W mezcla impulso y ventilación
- `VENTILATION_FREQUENCY_CONFLATED`: no hay ventilación efectiva aparte de la FR
- `CO2_NOT_REPRESENTABLE`: no hay CO2
- `MECHANICAL_VENTILATION_NOT_MODELED`: no hay ventilación mecánica

- Corrección estructural: no. no defect is clear to fix without a new state: removing the lactate term would leave the core without any metabolic compensation (KD-S1, patient-like compensation) and replacing it needs an acid-base state the faculty has not authorized; W has no GI writer, so its mixed reading moves nothing now; there is no mechanical ventilation to override. Nothing in the core changes.
- Superficie candidata: no. the structure is not coherent (readiness blockers): no numeric RR surface.
- Núcleo sin cambios: `clinical_core/derived.py` sí, `clinical_core/integration.py` sí, `clinical_core/shadow.py` sí, `clinical_core/state.py` sí.
- Región de P2J-3 recalculada igual: demand_class sí, primary sí, support sí, units sí.
- Parámetros aprobados: 0.

**Estructura mínima que falta:** Smallest missing physiology, in order: (1) a metabolic acid-load state (a base-deficit-like quantity with an explicit source tied to the delivery shortfall and an explicit clearance), from which acidaemia is read, so that metabolic acidosis drives ventilation causally and lactate stays a biomarker beside it; (2) a CO2 representation: PaCO2 from CO2 production (demand) against effective alveolar ventilation W, algebraic unless kinetics are needed; (3) W split into ventilatory drive (acidaemia, PaCO2, hypoxaemia, depressants) and effective ventilation (drive limited by mechanics / fatigue), with RR the observable of the drive; (4) respiratory-support semantics separating oxygenation (FiO2) from ventilatory support (NIV, controlled ventilation) that sets W or the rate. (1) and (2) are the first step; each needs faculty authorization before any number.

**Decisiones que se piden a la docencia:**
1. authorize the metabolic acid-load state (1): its meaning, source and clearance, and lactate's relation to it
2. decide PaCO2 (2): algebraic from production and W, or a state with its own time constant
3. decide W's semantics (3): effective ventilation as an output, drive as its own signal
4. decide whether the lactate term stays as a flagged interim proxy until (1) exists, or is removed (RR would lose all metabolic compensation)
5. decide the respiratory-support scope (4) and whether mechanical ventilation enters the GI family
<!-- /generado:veredicto -->

## 15. Eficiencia (generado)

<!-- generado:eficiencia -->
P2J-3 recalculado: 1326 trayectorias de sangre y 364 contrafactuales en caché. FR: 5364 trayectorias reconstruidas sin correr el núcleo y 48 corridas completas de validación; corridas de candidatos: 0. Barrido cartesiano: no; FR heredada leída: no.
<!-- /generado:eficiencia -->

## 16. Lo que falta y lo que se pide

La FR actual no es un modelo de ventilación: es una función de la concentración de lactato anclada a la FR de
llegada. Por eso la auditoría se detiene antes de cualquier rango numérico (parada temprana del encargo), sin esconder
la fisiología que falta detrás de ganancias de FR.

**Estructura mínima que falta, en orden:**

1. **Carga ácida metabólica.**
   - Un estado tipo déficit de base, con fuente explícita ligada al déficit de aporte y aclaramiento explícito.
   - De él se lee la acidemia; el lactato queda como biomarcador al lado.
2. **CO2.**
   - PaCO2 a partir de la producción de CO2 (la demanda) frente a la ventilación alveolar efectiva W.
   - Algebraica, salvo que haga falta cinética.
3. **W separado en dos.**
   - Impulso ventilatorio: acidemia, PaCO2, hipoxemia y depresores.
   - Ventilación efectiva: el impulso limitado por la mecánica o la fatiga.
   - La FR, como observable del impulso.
4. **Soporte respiratorio.** Separar la oxigenación (FiO2) del soporte ventilatorio (VNI, ventilación controlada), que
   fija W o la frecuencia.

(1) y (2) son el primer paso. Cada uno necesita autorización docente antes de cualquier número; la IA no elige.

**Mientras tanto:**

- el término del lactato queda **marcado** como sustituto: no se ajusta y no se usa para filtrar;
- quitarlo dejaría al núcleo sin ninguna compensación metabólica.

Si se mantiene como sustituto provisional o se retira es una decisión docente (§14).

## 17. Limitaciones

- **Dependencia de la demanda:** la comparación congelada busca la misma unidad (conjunto de sangre y punto del lado
  lactato) en las dos demandas y no encontró ninguna (n = 0). Los puntos que sobreviven a 1,0 y a 1,1 son distintos.
  - La vía estructural existe (demanda → déficit → D → lactato → FR).
  - Una prueba añadida tras la corrida lo confirma: la misma unidad a demanda 1,0 y 1,1 da una FR distinta.
- **R3 y R4 coinciden hasta los 120 min:** es un hecho del modelo, no un fallo de claves. La sangre difiere (en R4 el
  sangrado cae desde el minuto 60), pero el déficit efectivo es 0 en los dos tras las GR, así que D, el lactato y la
  FR coinciden. La validación contra el núcleo lo confirma en los dos escenarios.
- **Reconstrucción:** se valida contra el núcleo con una corrida completa por escenario, caso, demanda y g (48). El
  resto se reconstruye con la misma función `respiratory_rate` que usa el núcleo.
- **Sondas:** son estados sintéticos sobre el arranque neutro con lactato 2,5; no dan ningún valor clínico.
- **Medianas y rangos:** de la reconstrucción se calculan sobre trayectorias únicas, sin ponderar.
- **Copia del reparto de la FR:** el paquete P2G mantiene una copia offline (`decision_pack.rr_parts`) que debe
  cambiar junto con la FR si la FR cambia.
