# P2S-2 · Mecánica respiratoria común y cierre del significado de W

Paquete estructural común, en sombra. No migra el asma ni calibra la mecánica. Rama `phase-2-clinical-core-shadow`; base
`100d541` (P2Q-2 aceptado y cerrado; P2R-0 y P2S-1 aceptados).

- Núcleo: `clinical_core/state.py`, `provenance.py`, `integration.py` y `derived.py`, con inserciones declaradas y
  probadas contra P2Q-2 (§18). Todo queda tras un interruptor apagado por defecto (`respiratory_mechanics`).
- Análisis: `clinical_core/respiratory_mechanics.py`, congelado antes de evaluar.
- Registro: `docs/revision/P2S2_respiratory_mechanics.json`. Este documento se genera desde el registro
  (`clinical_core/respiratory_mechanics_report.py`); el texto fuera de los marcadores es la narrativa.

## 1. Decisiones docentes que rigen

- **W_SEMANTICS_COMMON_GAP:** P2K-2 (W atada a la FR) no representa FR alta con PaCO2 alta (edema, asma grave); P2K-3
  (W libre de la FR) pierde la hipoventilación por FR baja (opioide). Ninguna lectura pura basta.
- **Significado único de W:** ventilación alveolar efectiva relativa a la necesidad ventilatoria metabólica actual,
  derivada. W no es impulso, frecuencia, disponibilidad central ni gravedad mecánica. Cadena causal: impulso +
  disponibilidad → FR expresada; FR + eficiencia mecánica + necesidad → W; W → PaCO2. Nunca W → FR en el candidato.
- **Una coordenada mecánica mínima:** `mechanics_efficiency`, común, escribible por familias, distinta del impulso, de la
  depresión central, de G y de L; no es un canal canónico. Dominio: mayor que 0; 1 es sólo la referencia estructural.
- **Forma:** factor de frecuencia = FR expresada / FR intrínseca; capacidad = factor × eficiencia; W = capacidad /
  razón de demanda; PaCO2 = PaCO2_ref / W, con PaCO2_ref = 40 mmHg (COMMON_REFERENCE_PROVISIONAL), nunca anclada a la
  PaCO2 autoral de llegada.
- **Mecánica de llegada:** estado latente de caso o familia, acotado por la FR y la PaCO2 autorales, la incertidumbre de
  la FR intrínseca y la demanda; se informan regiones, no se elige ningún valor.

## 2. Rutas respiratorias antes y después (P2S-2-1, P2S-2-2)

<!-- generado:rutas -->
| Ruta | Estado | Qué hace |
|---|---|---|
| `P2K2_path` | ACTIVE_CURRENT | every migration profile (acid-base on, mechanics off); unchanged |
| `P2K3_candidate` | SHADOW_CANDIDATE | clinical_core/ventilation.py (W from the acid recruitment, no RR term), off, unchanged for its closed records; superseded as W semantics: RETIRED from the common candidate |
| `P2P2_path` | ACTIVE_CURRENT | the drive composition; unchanged |
| `P2S2_candidate` | SHADOW_CANDIDATE | profile.respiratory_mechanics, off by default: W from RR, the state's mechanics efficiency and the demand; PaCO2 from W and the common reference |
| `PaCO2_P2K2` | ACTIVE_CURRENT | resting PaCO2 = authored arrival PaCO2 x arrival W at the reference (the arrival anchor); the P2K-2 path whenever the mechanics candidate is off; the candidate never reads it |
| `W_P2K2` | ACTIVE_CURRENT | Respiration.ventilation = efficiency x RR / intrinsic / demand ratio with the profile constant; the P2K-2 path whenever the mechanics candidate is off |
| `W_channel_P2K1_reader` | ACTIVE_CURRENT | derived.respiratory_rate reads state.W (above 0 multiplies the ventilatory RR, below 0 depresses it) only with the acid-base physiology off (DEFAULT_PROFILE, the golden); with it on that RR is replaced by P2K-2's. In the P2S-2 candidate RETIRED_FROM_COMMON_MECHANICS_CANDIDATE: no source may write the W channel (the integration refuses it) and nothing reads it; historical behaviour kept |
| `acid_drive` | ACTIVE_CURRENT | P2K-2: the burden from the authored HCO3 and the effective oxygen deficit; unchanged |
| `central_drive_availability` | ACTIVE_CURRENT | P2P-2 STRUCTURAL_INPUT, 1 by default; family values UNSET; it moves the RR only |
| `expressed_rr` | ACTIVE_CURRENT | availability x rate_from_drive(excitatory, intrinsic) whenever the acid-base physiology is on; P2S-2 begins after it |
| `intrinsic_rr` | ACTIVE_CURRENT | Anchors.intrinsic_respiratory_rate (None: the arrival RR), a P2K-2 candidate input (12 / 16 / 20 carried); the reference frequency of W, never a mechanics input |
| `legacy_engine` | LEGACY_ONLY | family_engine.py's respiratory model, the runtime source of truth; not read |
| `metabolic_demand` | ACTIVE_CURRENT | aux.oxygen_demand / anchors.metabolic_demand_baseline (BASELINE_RELATIVE), shared by P2K-2, P2K-3 and the candidate; CO2 production read proportional to it (a constant respiratory quotient, implicit) |
| `respiratory_drive` | ACTIVE_CURRENT | P2P-2 composition: excitatory drive = acid drive (acid_to_drive_gain x burden) + hypoxaemic drive (UNSET by default); unchanged; reads no mechanics, W or PaCO2 |
| `ventilation_efficiency` | ACTIVE_CURRENT | P2K-2 profile constant, STRUCTURAL_REFERENCE 1 in every migration; in the P2S-2 candidate RETIRED: it must be 1, mechanics live in the state |

- Lectores del canal W en `derived.py`: `respiratory_rate` (P2K-1). Con el candidato, la integración rechaza toda escritura de W (`respiratory_mechanics_active(profile) and any((delta.channel is Channel.W for delta in deltas))`).
- Lector de la eficiencia mecánica: `respiration`; la llegada la escribe `arrival_state` desde el ancla.
- Rama del candidato: lee `mechanics_efficiency`, `paco2_reference_mmhg`; la rama P2K-2 lee `arrival_alveolar_ventilation`, `arrival_paco2`, `mechanics_efficiency`, `ventilation_efficiency`.
- El impulso, la oxigenación y la FC no leen W, PaCO2 ni la mecánica; la integración compone la mecánica sólo con las contribuciones (`mechanics_efficiency=state.aux.mechanics_efficiency * math.prod((item.factor for item in mechanics))`). Auditoría: sí.
<!-- /generado:rutas -->

## 3. Semántica y dimensiones (P2S-2-5, P2S-2-6)

La forma docente es exactamente la que el núcleo ya usaba (`alveolar_ventilation`, la única fórmula de W): cambia de
dónde sale la eficiencia (del estado, escrita por familias, en lugar de una constante del perfil) y la referencia de la
PaCO2 (la común, en lugar del ancla de llegada). No existe una equivalente dimensionalmente más limpia.

<!-- generado:semantica -->
- **PaCO2:** PaCO2_reference / W: the alveolar ventilation equation relative to its reference (PaCO2 = k VCO2 / VA, so PaCO2 / PaCO2_ref = (VCO2 / VCO2_ref) / (VA / VA_ref)); 40 mmHg at W = 1.
- **W:** effective alveolar ventilation relative to the current metabolic ventilatory need (dimensionless; 1: the patient's need met at the eupnoeic reference); derived, never a state the drive reads.
- **capacity:** frequency factor x mechanics efficiency: the alveolar ventilation relative to its reference.
- **demand_ratio:** aux.oxygen_demand / metabolic_demand_baseline (BASELINE_RELATIVE): CO2 production relative to the patient's baseline, read proportional to the oxygen demand (constant respiratory quotient, implicit).
- **frequency_factor:** expressed RR / intrinsic RR (bpm / bpm): the breaths taken relative to the reference rate.
- **mechanics_efficiency:** effective alveolar ventilation per breath relative to the eupnoeic reference (VT - VD over its reference, implicitly): above 0, 1 the structural reference; the state's value, the case's latent arrival value times every family change since.
- **pH:** carbonic_ph(HCO3, PaCO2), unchanged.
- **Dimensiones:** PaCO2: mmHg (the reference carries the unit); W: 1; capacity: 1 (VA / VA_ref); demand_ratio: 1 (VCO2 / VCO2_baseline, through VO2); equivalence: the core computes W = efficiency x RR / intrinsic / demand (alveolar_ventilation, the one W formula, P2K-2's), algebraically the faculty's form; no dimensionally cleaner equivalent exists; frequency_factor: 1 (bpm / bpm); mechanics_efficiency: 1 (per-breath alveolar ventilation over its reference).
<!-- /generado:semantica -->

## 4. Interfaz para familias (P2S-2-4)

Sólo el destino común; no hay escritor de asma, edema ni opioide. Un cambio multiplica la eficiencia con la que empieza
el minuto y queda donde lo dejan sus escritores: el núcleo no le añade cinética propia ni la devuelve a la llegada.

<!-- generado:interfaz -->
- **composition:** the core multiplies the efficiency the minute starts with by every factor of the minute (RESPIRATORY_MECHANICS, a core composition, no kinetics): it stays where its writers leave it.
- **families:** no family writer exists: no asthma obstruction, oedema mechanics or opioid writer (P2S-2-4).
- **off:** with the candidate off a change, an arrival value other than 1 and a state value other than 1 are refused (nothing would read them).
- **provenance:** each change in MinuteRecord.mechanics with its source; the aux change under RESPIRATORY_MECHANICS; the conservation check holds the efficiency to exactly its recorded factors.
- **target:** aux.mechanics_efficiency (AUXILIARY_FIELDS), arrival value Anchors.arrival_mechanics_efficiency.
- **writer:** Contribution.mechanics: a tuple of provenance.MechanicsChange(factor > 0, source, minute, description); any non-reserved source kind (a family module, an order, a scripted probe).
- Persistencia: un escritor que se detiene en el minuto 5 deja la eficiencia en 0,59049 hasta el minuto 10 (sí); dos escritores componen (sí); cada minuto registra sus cambios ([2, 2, 2]); el cambio auxiliar queda bajo `core_coupling:respiratory_mechanics`.
- Rechazos: arrival_when_off sí, change_when_off sí, factor_boolean sí, factor_infinite sí, factor_nan sí, factor_negative sí, factor_zero sí, profile_needs_acid_base sí, profile_needs_reference_efficiency sí, state_when_off sí.
- Escritores de familia en `clinical_core/modules`: ninguno.
<!-- /generado:interfaz -->

## 5. Sondas M1–M12 (P2S-2-7)

<!-- generado:sondas -->
| Sonda | Qué exige | Resultado | Pasa |
|---|---|---|---|
| M1 | normal drive + availability 1 + mechanics reference: the W reference state (W 1, PaCO2 the reference) | FR 16,0, W 1,000, PaCO2 40,0, pH 7,401 | sí |
| M2 | RR up, mechanics fixed: W up, PaCO2 down | E 1: FR 16,0, 21,3, 25,5, 28,8; PaCO2 40,0, 30,0, 25,1, 22,2. E 0,5: PaCO2 80,0, 60,0, 50,1, 44,4 | sí |
| M3 | RR high + mechanics sufficiently reduced: W can stay low, PaCO2 high (the asthma / oedema property) | FR 36,0, disponibilidad 1,00; frontera E* 0,445; PaCO2 por E 1,00 → 17,8, 0,75 → 23,7, 0,50 → 35,6, 0,25 → 71,2 | sí |
| M4 | RR low from central depression + mechanics normal: W low, PaCO2 high (the opioid property) | FR 8,0 (intrínseca 16), E 1, W 0,500, PaCO2 80,0 | sí |
| M5 | same RR, lower mechanics: higher PaCO2 | misma FR 36,0; PaCO2 17,8, 23,7, 35,6, 71,2 | sí |
| M6 | same mechanics, lower RR: higher PaCO2 | E 1: FR 36,0, 27,0, 18,0, 9,0, 3,6, PaCO2 17,8, 23,7, 35,6, 71,2, 178,0 | sí |
| M7 | the acid drive raises RR; W responds through RR only, no direct lactate control | impulso ácido 0,00, 6,00, 12,00, 18,00; FR 16,0, 21,3, 25,5, 28,8; independiente del lactato sí; misma FR, misma W sí | sí |
| M8 | the hypoxaemic drive raises RR; W responds through RR only, no SpO2 -> PaCO2 shortcut | SpO2 97, 91, 85; FR 16,6, 17,7, 18,8; PaCO2 38,6, 36,1, 34,0; misma FR, misma W sí | sí |
| M9 | central depression suppresses RR: W falls, PaCO2 rises | disponibilidad 1,00, 0,75, 0,50, 0,25, 0,10, 0,00; FR 16,0, 12,0, 8,0, 4,0, 1,6, 0,0; PaCO2 40,0, 53,3, 80,0, 160,0, 400,0, — | sí |
| M10 | a mechanics change alone moves no drive, intrinsic RR, availability, G, SpO2, D or lactate | estados idénticos salvo la mecánica sí; derivados idénticos sí; E final 0,545; PaCO2 34,0, 62,3 | sí |
| M11 | a G impairment alone does not change the mechanics efficiency | G al final 0,30; E constante sí; con impulso hipoxémico sintético W 1,037, 1,055 (sólo por la FR) | sí |
| M12 | an L impairment alone does not change the mechanics efficiency unless a writer declares it | L 0,57, G 0,57, E constante sí; con un escritor declarado E 0,545 | sí |
<!-- /generado:sondas -->

## 6. Direcciones exigidas (P2S-2-5, P2S-2-6)

<!-- generado:direcciones -->
- Demanda 1,0, 1,2, 1,5 con la FR fija en 16,0: W 1,000, 0,833, 0,667, PaCO2 40,0, 48,0, 60,0.
- PaCO2 frente a W en 24 puntos de sonda: estrictamente decreciente sí; igual a la referencia / W sí; la forma docente reproduce W sí. Pasa: sí.
<!-- /generado:direcciones -->

## 7. FR alta con PaCO2 alta (P2S-2-8)

<!-- generado:alto_co2 -->
**`asthma_49m`** (FR autoral 30, PaCO2 autoral 51):

| FR intrínseca | Frontera E* | PaCO2 con E 0,25 | PaCO2 con E 0,50 | PaCO2 con E 0,75 | PaCO2 con E 1,00 |
|---|---|---|---|---|---|
| 12 | 0,400 | 64,0 | 32,0 | 21,3 | 16,0 |
| 16 | 0,533 | 85,3 | 42,7 | 28,4 | 21,3 |
| 20 | 0,667 | 106,7 | 53,3 | 35,6 | 26,7 |

**`pulmonary_edema_58m`** (FR autoral 38, PaCO2 autoral 49):

| FR intrínseca | Frontera E* | PaCO2 con E 0,25 | PaCO2 con E 0,50 | PaCO2 con E 0,75 | PaCO2 con E 1,00 |
|---|---|---|---|---|---|
| 12 | 0,316 | 50,5 | 25,3 | 16,8 | 12,6 |
| 16 | 0,421 | 67,4 | 33,7 | 22,5 | 16,8 |
| 20 | 0,526 | 84,2 | 42,1 | 28,1 | 21,1 |

- Núcleo, `neutral_probe`: FR 36,0, disponibilidad 1,00, E 0,25, W 0,562, PaCO2 71,2 (sí).

- Núcleo, `pulmonary_edema_58m_committed_arrival`: FR 36,4, disponibilidad 1,00, E 0,25, W 0,569, PaCO2 70,3 (sí).

- Clase: **HIGH_RR_HIGH_PACO2_STRUCTURALLY_REPRESENTABLE**.
<!-- /generado:alto_co2 -->

## 8. Contraste con el asma 24f (P2S-2-9)

<!-- generado:contraste_24f -->
E leve 0,75, E baja 0,25 (puntos de la rejilla sintética, no seleccionados). FR autoral: 24f 34, 49m 30.

| FR intrínseca | 24f con E leve | 49m con E baja | Frontera 24f | Frontera 49m |
|---|---|---|---|---|
| 12 | 18,8 | 64,0 | 0,353 | 0,400 |
| 16 | 25,1 | 85,3 | 0,471 | 0,533 |
| 20 | 31,4 | 106,7 | 0,588 | 0,667 |

Pasa: sí.
<!-- /generado:contraste_24f -->

## 9. Contraste con el opioide: dos fallas, una W (P2S-2-10)

<!-- generado:opioide -->
| Lectura | FR | Disponibilidad | E | W | PaCO2 |
|---|---|---|---|---|---|
| reference | 16,0 | 1,00 | 1,00 | 1,000 | 40,0 |
| CENTRAL_DRIVE_FAILURE | 4,8 | 0,30 | 1,00 | 0,300 | 133,3 |
| MECHANICAL_VENTILATORY_FAILURE | 36,0 | 1,00 | 0,25 | 0,562 | 71,2 |

`opioid_35m` autoral: FR 6, PaCO2 69; E implícita 12: 1,159, 16: 1,546, 20: 1,932 (mecánica no reducida). Pasa: sí.
<!-- /generado:opioide -->

## 10. Regiones de eficiencia de llegada (P2S-2-11)

La verdad autoral se usa sólo como diagnóstico: E = 40 × demanda × FR intrínseca / (PaCO2 × FR autoral), lineal en la FR
intrínseca (12 / 16 / 20) y en la razón de demanda (1 en la llegada por construcción). Ningún valor se selecciona.

<!-- generado:regiones -->
| Caso | FR | PaCO2 | E (12) | E (16) | E (20) | Demanda 1,2 | E con FR del modelo (16) |
|---|---|---|---|---|---|---|---|
| `acs_70f_left_main` | 26 | 33 | 0,559 | 0,746 | 0,932 | 0,671 – 1,119 | 0,760 |
| `asthma_24f` | 34 | 31 | 0,455 | 0,607 | 0,759 | 0,546 – 0,911 | 0,954 |
| `asthma_49m` | 30 | 51 | 0,314 | 0,418 | 0,523 | 0,376 – 0,627 | 0,784 |
| `gi_bleed_57m` | 26 | 31 | 0,596 | 0,794 | 0,993 | 0,715 – 1,191 | 0,783 |
| `gi_bleed_72f` | 24 | 33 | 0,606 | 0,808 | 1,010 | 0,727 – 1,212 | 0,838 |
| `opioid_35m` | 6 | 69 | 1,159 | 1,546 | 1,932 | 1,391 – 2,319 | 0,580 |
| `pulmonary_edema_58m` | 38 | 49 | 0,258 | 0,344 | 0,430 | 0,309 – 0,516 | 0,714 |
| `pulmonary_embolism_33f` | 30 | 30 | 0,533 | 0,711 | 0,889 | 0,640 – 1,067 | 1,007 |
| `pulmonary_embolism_61m` | 32 | 28 | 0,536 | 0,714 | 0,893 | 0,643 – 1,071 | 0,895 |

Regla: Predeclared, at each carried intrinsic RR (12 / 16 / 20, the same for every case): (a) the severe cases (oedema 58m, asthma 49m) below compensated asthma 24f; (b) asthma 24f below every reference without major mechanics impairment (GI 57m, GI 72f, ACS 70f); (c) opioid 35m not below the lowest of those references (mechanics relatively preserved). PE is informative only. Coherent when (a), (b) and (c) hold at every level; otherwise STOP with a semantic problem. Regions across different intrinsic RRs may overlap; that is reported as an identifiability limit, never decided here.
- (a) graves bajo 24f: 12 sí, 16 sí, 20 sí
- (b) 24f bajo las referencias: 12 sí, 16 sí, 20 sí
- (c) opioide no reducido: 12 sí, 16 sí, 20 sí
- Solapamientos entre FR intrínsecas distintas: asthma_24f|acs_70f_left_main: 0,559 – 0,759; asthma_24f|gi_bleed_57m: 0,596 – 0,759; asthma_49m|asthma_24f: 0,455 – 0,523; pulmonary_edema_58m|asthma_24f: ninguno
- Referencias con E < 1: acs_70f_left_main: 12, 16, 20; gi_bleed_57m: 12, 16, 20; gi_bleed_72f: 12, 16
- Lectura: the arrival efficiency is read with the authored RR: a region per case over the intrinsic RR, linear in it and in the demand ratio. With the model's arrival RR (acid drive only) the reading would absorb the drive gap (the opioid would read as a mechanical failure); the asthma migration must map availability and the excitatory drive before it maps mechanics.
- Clase: **CLINICALLY_COHERENT_ORDERING**.
<!-- /generado:regiones -->

Lectura: el orden es coherente (graves < asma compensada < referencias sin alteración mecánica mayor ≤ opioide). Tres
cautelas:

1. Con la misma FR intrínseca para todos los casos, E es proporcional a ella, así que el orden «a cada FR intrínseca» es
   un solo orden: el de los productos PaCO2 × FR autorales. Las tres comprobaciones no son evidencia de robustez frente a
   la incertidumbre de la FR intrínseca.
2. Esa robustez la miden los solapamientos. Con FR intrínsecas distintas entre casos, las regiones se solapan (asma 49m
   con 24f; 24f con SCA y GI 57m), así que la región sola no identifica la mecánica sin conocer la FR intrínseca. Los
   márgenes con una FR intrínseca común son amplios (24f 0,607 frente a 0,746 de la referencia más baja, con 16).
3. GI 57m y el SCA leen E < 1 con las tres FR intrínsecas, y GI 72f con 12 y 16. El factor de frecuencia lineal atribuye a
   la mecánica la respiración rápida y superficial de la taquipnea (la sobrerrestricción de frecuencia de P2K-3).

Ninguna de las tres decide el veredicto.

## 11. Sin absorción por el ancla de llegada (P2S-2-12)

<!-- generado:sin_ancla -->
| PaCO2 autoral de llegada | Candidato | P2K-2 (apagado) |
|---|---|---|
| 30 | 40,0 | 30,0 |
| 40 | 40,0 | 40,0 |
| 60 | 40,0 | 60,0 |

- Referencia del candidato en cada estado: 40,0 mmHg.
- Edema 58m con el candidato encendido y E de referencia: FR del modelo 18,3 (autoral 38), PaCO2 35,0 frente a 49 autoral: diferencia −14,0 mmHg, informada, nunca absorbida.
- La rama del candidato lee el ancla: no. Pasa: sí.
<!-- /generado:sin_ancla -->

## 12. Un solo significado de W (P2S-2-15)

<!-- generado:unicidad -->
- Escritura del canal W rechazada con el candidato: sí; un estado que lo lleve se lee igual que sin él: sí.
- La FR de `derive` es la de `respiration` (P2P-2): sí.
- Lector P2K-1 con la fisiología ácido-base apagada (W −0,5 / 0 / 0,5): FR 8,0, 16,0, 24,0; estado: RETIRED_FROM_COMMON_MECHANICS_CANDIDATE (still ACTIVE_CURRENT with the acid-base physiology off).
- El impulso no lee W ni la mecánica: sí. Pasa: sí.
<!-- /generado:unicidad -->

## 13. Sin estado adicional (P2S-2-14)

<!-- generado:estado_extra -->
- Campos añadidos: `Anchors`: arrival_mechanics_efficiency; `AuxiliaryState`: mechanics_efficiency; `Contribution`: mechanics; `CoreProfile`: respiratory_mechanics; `MinuteRecord`: mechanics.
- Canales: V, T, P, R, L, G, W, D, N, hb, glucose, k (sin cambios).
- Nombres prohibidos en las inserciones (fatiga, compliancia, resistencia, espacio muerto, volumen corriente, músculo, enfermedad): ninguno.
- Cinética propia del núcleo: none: the integration composes the minute's declared factors only. Pasa: sí.
<!-- /generado:estado_extra -->

## 14. Hipoventilación → oxigenación (P2S-2-13)

<!-- generado:oxigenacion -->
- Estado: **HYPOVENTILATION_TO_OXYGENATION_LINK_DEFERRED**. La SpO2 no cambia con la mecánica (M10): sí; la oxigenación no lee W, PaCO2 ni la mecánica: sí.
<!-- /generado:oxigenacion -->

## 15. Señal de carga respiratoria y FC (P2S-2-18)

<!-- generado:carga -->
- Estado: **EXPOSED_DIAGNOSTIC_ONLY**; definición: demand_ratio / mechanics_efficiency (dimensionless).
- Factor de frecuencia necesario para W = 1 con la demanda basal: E 0,25 → 4,00, E 0,50 → 2,00, E 0,75 → 1,33, E 1,00 → 1,00.
- Lectores en el núcleo: ninguno.
<!-- /generado:carga -->

<!-- generado:fc -->
- HR_GAP_DISTRESS_AROUSAL_DOMINANT (diagnostic hypothesis; no sympathetic gain, no reader).
- La FC lee la respiración: no. Pasa: sí.
<!-- /generado:fc -->

## 16. Estado de los parámetros (P2S-2-17)

<!-- generado:parametros -->
- **acid_parameters:** unchanged (the P2N-2 common point).
- **approved:** none.
- **arrival_mechanics_efficiency:** CASE / FAMILY LATENT ARRIVAL MAPPING, UNSET in every committed case.
- **central_drive_availability_family_values:** UNSET.
- **hypoxaemic_drive_mapping_and_gain:** UNSET.
- **k_s_r:** UNSET (P2O-1 gas-exchange values SYNTHETIC_ONLY).
- **mechanics_efficiency_clinical_values:** UNSET (1 the STRUCTURAL_REFERENCE; synthetic values in probes only).
- **paco2_reference_mmhg:** 40, COMMON_REFERENCE_PROVISIONAL, not approved.
- **respiratory_mechanics:** STRUCTURAL_SWITCH, off by default.
- Eficiencia de llegada en los casos comprometidos: `acs_70f_left_main` 1,00, `pulmonary_edema_58m` 1,00, `pulmonary_embolism_33f` 1,00, `pulmonary_embolism_61m` 1,00.
- Candidato encendido en algún perfil comprometido: no. Pasa: sí.
<!-- /generado:parametros -->

## 17. No regresión por defecto (P2S-2-16)

<!-- generado:no_regresion -->
- Lectura exacta del núcleo de P2Q-2 sobre los cursos de referencia: acs sí, gi_57m sí, p2p2_hypoxaemic sí, pulmonary_edema sí, pulmonary_embolism sí.
- Mecánica constante en 1 en esos cursos: sí.
- No regresión de P2Q-2 (GI, ACS, edema, P2P-2): acs_authority_r7 sí, acs_evaluation sí, common_overload_r8 sí, edema_authority sí, edema_heart_rate sí, edema_oxygen sí, edema_respiration sí, edema_untreated sí, gi_o12 sí, p2p2_acidosis sí, p2p2_d1_d7_d9_d10 sí, p2p2_edema_diagnostic sí, p2p2_opioid sí.
- Secciones del registro de P2Q-2 reproducidas: arrival sí, central_depression sí, oxygen sí, respiratory_drive sí, secondary sí, untreated sí.
- Pasa: sí.
<!-- /generado:no_regresion -->

## 18. Prueba contra el árbol de P2Q-2

Los archivos `.py` de `clinical_core` que cambian son los cuatro del núcleo y las dos tuplas de registro. Se reconstruyen
byte a byte como los dejó P2Q-2. Los demás archivos `.py` de `clinical_core` existentes en `100d541` (109) están fijados
por hash.

El golden (`clinical_core/golden/gi_bleed_shadow.json`) cambia sólo por la entrada nueva del registro de parámetros
(`respiratory_mechanics`, 4 líneas). Lo cubren las pruebas del golden directo y de Contracts v2, no esta prueba.

<!-- generado:prueba -->
- Archivos con inserciones declaradas, probados contra P2Q-2 (`100d541`): `clinical_core/decision_pack.py` sí, `clinical_core/derived.py` sí, `clinical_core/integration.py` sí, `clinical_core/lactate_slice.py` sí, `clinical_core/provenance.py` sí, `clinical_core/state.py` sí.
- Archivos comunes fijados por hash: 109, intactos sí.
- Vista de P2Q-2: archivos comunes sí, digest de congelación de P2Q-2 sí, su prueba contra P2P-2 sí, registro sí.
<!-- /generado:prueba -->

## 19. Veredicto (P2S-2-19)

Regla predeclarada: READY si se cumplen todos los criterios; si no, NOT_READY con el primero que falla. Un orden de llegada
incoherente es un STOP. Los solapamientos de regiones, la linealidad del factor de frecuencia y la brecha de FC se
informan y nunca deciden.

<!-- generado:veredicto -->
- sí — RR and mechanics are distinct (M5, M6, M10; the drive reads no mechanics; the mechanics read no drive)
- sí — both contribute to W (M1, M2, M3, M5; the directions, demand included; the faculty's form reproduced)
- sí — W has one meaning (W channel writes refused and the channel inert, RR never read from W, W after RR; P2K-1 retired from the candidate)
- sí — high RR / high PaCO2 representable (M3; oedema 58m and asthma 49m; availability 1)
- sí — low RR / high PaCO2 representable (M4, M9; the opioid contrast)
- sí — central depression remains distinct from mechanics (the opioid contrast; M10, M11, M12)
- sí — arrival PaCO2 not hidden in a case-specific reference anchor (no anchor absorption; arrival ordering coherent)
- sí — default prior behaviour unchanged (exact P2Q-2 reading; GI, ACS, oedema, PE and P2P-2 reproduced; the P2Q-2 tree proven)
- sí — no clinical mechanics value approved (no family writer; committed arrivals at the reference; parameter state)

**Veredicto: COMMON_RESPIRATORY_MECHANICS_ARCHITECTURE_READY**

**Recomendación: PROCEED_TO_ASTHMA_SHADOW_MIGRATION (no numerical mechanics calibration before it; the family provides the mechanics writer and its arrival mapping, after availability and the excitatory drive)**
<!-- /generado:veredicto -->

## 20. Proceso

- Duración: inicio 18:32 UTC; congelación `b107783` a las 19:18; evaluación única a las 19:19 (4 s).
- Durante el desarrollo se ejecutaron las sondas para depurar el código: cuatro expectativas de formato (orden de listas,
  nombres de canales, igualdad en coma flotante) y la ubicación del rechazo de W. Ese rechazo se movió de `respiration` al
  integrador para respetar las guardas cerradas de P2K-1 y P2K-2: sólo `respiratory_rate` lee `state.W`.
- Ningún valor sintético cambió por un resultado. El único punto cercano a una región de llegada implícita (0,35) se
  sustituyó por la rejilla genérica antes de congelar.
- Pruebas de Fase 2 antes de congelar: dos tandas de 4 particiones con 1 755 pruebas (963 + 792) y 2 omitidas (el registro
  y el documento, aún sin escribir). Fallaron dos, ambas de efecto dominó con precedente (el registro de P2P-1 y el pin
  de `scenario_inputs`); se adaptaron y volvieron a pasar.
- Una sola evaluación, una sola revisión adversarial (§21) y una sola certificación final.

## 21. Revisión adversarial

Una revisión, independiente y de sólo lectura, sobre el candidato congelado y evaluado. Encontró 1 hallazgo medio y 6
bajos, ninguno alto. No se volvió a congelar: la congelación es única, y los hallazgos son de alcance o de redacción.

1. **Medio: el valor por defecto de la FR intrínseca.** Sin una FR intrínseca declarada, `intrinsic_respiratory_rate`
   usa la FR autoral (el valor por defecto de P2K-2). En el candidato eso deja el factor de frecuencia de llegada en ≈ 1 y
   carga toda la brecha de PaCO2 sobre la mecánica: es un ancla nueva, la FR autoral. Hoy no tiene efecto, porque todo
   caso comprometido declara 16, pero es la vía que usaría la migración del asma. No se corrigió en el núcleo congelado:
   queda como deuda (TD-119) y como decisión docente. La migración debe declarar la FR intrínseca (banda 12 / 16 / 20) o
   el candidato debe exigirla.
2. **Bajo: los rechazos con el candidato apagado son más estrechos de lo que dice `INTERFACE["off"]`.**
   - Se rechazan siempre un cambio de mecánica (integración) y una eficiencia de llegada distinta de 1 (`arrival_state`).
   - Un estado con eficiencia distinta de 1 se rechaza sólo en `respiration`, es decir, con la fisiología ácido-base
     encendida. Con el perfil por defecto pasa en silencio, aunque nada lo lee.
   - `initial_state` descarta la eficiencia de llegada, como ya hacía con el bicarbonato de P2K-2; `run` lo detecta.
   - Queda como deuda.
3. **Bajo: la narrativa del §10 decía «E < 1 con 12–16» para todas las referencias.** Corregida: GI 57m y el SCA leen E < 1
   con las tres FR intrínsecas.
4. **Bajo: el §18 omitía el golden.** Corregido.
5. **Bajo: el orden «a cada FR intrínseca» es un solo orden.** Corregido en la lectura del §10: la robustez la miden los
   solapamientos.
6. **Bajo: la descripción de `paco2_reference_mmhg` en el registro de parámetros quedó desactualizada.** Sigue diciendo que
   es la PaCO2 de llegada por defecto; con el candidato es la PaCO2 a W = 1 de todo caso. La entrada
   `respiratory_mechanics` lo dice bien. Queda como deuda de redacción en el núcleo congelado.
7. **Bajo / informativo: con el candidato apagado las lecturas y los registros son idénticos, la serialización no.**
   - `MinuteRecord.to_dict` gana `mechanics: []`, el auxiliar gana `mechanics_efficiency` y el perfil gana
     `respiratory_mechanics`. Con eso cambian la traza en sombra y su `profile_digest`.
   - Un auxiliar serializado antes de P2S-2 ya no se carga. No hay ninguno guardado en el repositorio.
   - Hay precedente en P2K-2 y P2I-2T.

Verificado sin hallazgos:

- No hay ningún camino de W a la FR con el candidato.
- La FR intrínseca no codifica la mecánica.
- La rama del candidato no lee el ancla.
- El impulso, la disponibilidad y la mecánica están separados.
- No hay términos de enfermedad, estados prohibidos, gas alveolar ni cambio de FC.
- La rejilla sintética es genérica.
- La composición, la procedencia y la conservación de la mecánica son correctas.
- La prueba de reversión es sólida.
- Las adaptaciones de las pruebas cerradas no ocultan diferencias.

## 22. Limitaciones

- Ningún valor mecánico clínico está aprobado: las eficiencias de las sondas son una rejilla sintética genérica
  (1; 0,75; 0,5; 0,25) y las regiones de llegada son diagnósticas.
- El factor de frecuencia es lineal en la FR: la taquipnea normal (respiración rápida y superficial) aparece como E < 1.
- La FR del modelo en la llegada no reproduce la autoral sin un impulso excitador mapeado (P2S-1): con el candidato
  encendido la PaCO2 de llegada difiere de la autoral; se informa, no se absorbe.
- No hay acoplamiento hipoventilación → oxigenación, ni ecuación del gas alveolar, ni estado de fatiga, compliancia,
  resistencia o espacio muerto.
- La FC no cambia; HR_GAP_DISTRESS_AROUSAL_DOMINANT sigue como hipótesis diagnóstica.
- Sin una FR intrínseca declarada, el candidato toma la FR autoral como intrínseca (hallazgo 1 de la revisión).
- «Comportamiento idéntico por defecto» se refiere a las lecturas y a los registros. La serialización gana tres campos
  (hallazgo 7).
