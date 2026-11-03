# P2M-2 · Capa común mínima de seguridad ante colapso

**Rama:** `phase-2-clinical-core-shadow` · **Base:** `61628ec` (P2M-1 cerrado) · **Congelamiento:** `2213173` (digest `5f96f860…`) · **Fecha:** 2026-11-03

Sólo sombra. Un candidato de fisiología (`clinical_core/collapse.py`) que ningún paso del núcleo lee, y su análisis congelado (`clinical_core/collapse_architecture.py`). Ningún archivo del núcleo cambia, ningún umbral clínico recibe valor y nada se activa. Las secciones generadas salen del registro `docs/revision/P2M2_collapse_architecture.json` (`collapse_architecture_report`).

## Resumen

**Veredicto congelado: `COMMON_COLLAPSE_SAFETY_ARCHITECTURE_READY_FOR_GENERALIZATION`.** La revisión adversarial
deja tres hallazgos medios sin recongelar (§18). La lectura corregida mantiene el veredicto, pero antes de usar la capa
sobre la trayectoria de una familia o de integrarla hay que corregir dos defectos de implementación: un minuto
contrafactual que puede fallar (M1) y la escritura de la carga sin registro (M2). Recomendación:
`MOVE_TO_SECOND_FAMILY_GENERALIZATION_WITH_COLLAPSE_THRESHOLDS_UNSET`. No hace falta calibrar el colapso con números
antes de la segunda familia: la capa está en sombra, inactiva, y se ejercita con valores sintéticos sin imponer un paro
clínico. Ningún umbral recibe valor.

- **Señal:** `collapse_signal = max(falla de PAM, falla de aporte de O2)`, nunca una suma.
  - La falla de PAM lee la PAM de `derive` por una rampa cuyas cotas quedan `UNSET_CLINICAL_MAPPING`.
  - La falla de aporte es el déficit efectivo normalizado ya certificado (`acute_deficit_signal`), sin recalibrar.
- **Exclusiones:**
  - Q, P y R llegan sólo por la PAM y el aporte (C5: mismo par PAM/aporte con gasto 0,500 frente a 0,357, la misma
    señal);
  - la SpO2 directa queda DEFERRED (C6);
  - lactato, D, pH, I y F no se leen. El C7 congelado sólo compara la señal en un estado dominado por la PAM, y el
    escaneo sólo ve atributos (M3). Una prueba nueva compara las dos entradas en un estado dominado por el aporte y
    detecta una fuga plantada.
- **Pulso:** `pulse_present` es el estado de ritmo que perfunde, no un pulso palpable garantizado.
  - Con pulso y PAM 1,8 mmHg el estado es colapso profundo representable (C14).
  - Con pulso y gasto en el cero numérico el núcleo falla en voz alta (C13).
  - Sin pulso hay paro, no colapso (C12).
- **Persistencia:** la misma `aux.collapse_burden`, sin otra variable.
  - Se relaja exactamente hacia `señal × τ`: nunca negativa, se repaga, cae siempre a 0 con señal 0 y queda acotada por
    τ.
  - El criterio terminal exige persistencia (carga ≥ límite) **y** no viabilidad actual (señal ≥ piso).
  - El perfil rechaza un límite alcanzable en un minuto desde carga 0 y un criterio sin piso.
  - Toda pérdida del pulso pone la carga en 0.
- **Orden:** `state(t) → derive(t) → señal(t) → carga(t+1) → decisión → transición en el minuto del núcleo →
  state(t+1)`.
  - Acíclico: una transición, sin redisparo.
  - Un ritmo que mueve un contribuyente gana, y la decisión se toma de nuevo sobre la fisiología del ritmo nuevo.
- **Sondas:** C1–C14 cumplen; las siete familias pasan con la misma función, sin términos de enfermedad.
- **Llegada:** la carga es 0 por defecto y la señal es la de la fisiología de llegada (0,222 con PAM 70), no forzada a 0.
- **ROSC:** no está modelado, pero sigue siendo posible: la carga queda en 0 y el candidato no lee `terminal_since`.
- **Subconjunto extremo GI** (17 604 filas): evaluable cuando existan los mapeos; no se clasifica ni se filtra.
- **No regresión:** el árbol de P2M-1 (67 archivos) coincide byte a byte. En sombra activa, todo el estado del núcleo
  salvo la carga es idéntico durante 30 minutos. Los registros del núcleo coinciden en parte porque la escritura de la
  carga no queda registrada (M2).
- **P2M-1:** cinco puntos quedan `SUPERSEDED_BY_P2M2` sin reescribir su registro.

## 1. Decisiones de la docencia

<!-- generado:decisiones -->
Decisiones de la docencia (texto congelado, en inglés):

- **brief**: P2M-2 minimal common collapse safety layer (2026-11-03): structural; no clinical threshold chosen
- **delivery**: the certified effective oxygen-delivery deficit, not recalibrated, not replaced by D or lactate
- **gi_subset**: 57m, demand 1.1, 17,604 rows, untreated pH < 7.00, MAP about 32.5-46.3, pulse present: diagnostic only, never used to choose a threshold, never classified as arrest / non-arrest while UNSET
- **order**: EXPLICIT_LAG_REQUIRED: state(t) -> derive(t) -> collapse_signal(t) -> burden -> terminal decision -> terminal rhythm / pulse transition -> state(t+1); no recursive same-step loop
- **perfusion**: MAP is the source; its clinical mapping stays UNSET_CLINICAL_MAPPING; synthetic tests may inject the normalized value
- **persistence**: the existing aux.collapse_burden; no second persistence variable, no consecutive-minute counter; non-negative, 0 at arrival by default, arrival signal from the actual arrival physiology, rises while the signal persists, repays as it improves, tends monotonically to 0 at zero signal, never arrests alone, terminal needs persistence AND current non-viability, reset or frozen at the transition; never from tau_D, lactate or the encephalopathy memory; numbers UNSET
- **pulse**: pulse_present is the effective perfusing rhythm state, not a guaranteed palpable pulse; pulse with an extremely low MAP is allowed as transient profound collapse; never derived from pressure
- **q_p_r**: Q reaches MAP and DO2; P and R reach Q; rhythm stays authoritative for pulse_present; a no-pulse rhythm is arrest, not collapse
- **rosc**: ROSC_NOT_CURRENTLY_MODELED; no ACLS; the architecture must not make a future ROSC impossible
- **scope**: shadow only: no clinical threshold, GI collapse filtering, ROSC / ACLS, runtime activation, GI or second-family migration
- **signal**: collapse_signal = MAX(perfusion_failure_signal, oxygen_delivery_failure_signal); never a sum; no Q, direct SpO2, P, R, lactate, D, pH, I or F as a graded input
- **spo2**: direct SpO2 DEFERRED: oxygenation already reaches oxygen content and DO2; revisit in generalization
- **terminal_rhythm**: TERMINAL_RHYTHM_PHENOTYPE_UNSET; the existing machinery only for structural tests
- **zero_flow**: pulse=true + Q=0 stays an inconsistent state that fails loudly; not a clinical arrest rule; near-zero Q with a pulse stays representable
<!-- /generado:decisiones -->

## 2. El candidato: señal, entradas, exclusiones y estado

<!-- generado:candidato -->
**Ecuación:** `collapse_signal = max(perfusion_failure_signal, oxygen_delivery_failure_signal)`; nunca una suma.

**Entradas graduadas** (texto congelado, en inglés):

- **oxygen_delivery_failure** (lee `deficit_fraction`): derived.acute_deficit_signal: the certified effective oxygen-delivery deficit over the current demand (0 when availability is adequate or compensated by extraction, 1 at no delivery); read as it is, not recalibrated, no onset threshold
- **perfusion_failure** (lee `map`): derive's MAP, the perfusion-pressure source; mapped through a monotone saturating ramp whose bounds are UNSET_CLINICAL_MAPPING (synthetic tests may inject the normalized value directly)

**Lo que no entra** (texto congelado, en inglés):

- **D**: NOT_AN_INPUT: the oxygen debt is not collapse memory
- **F**: NOT_AN_INPUT: the encephalopathy memory is not collapse memory
- **I**: NOT_AN_INPUT: consciousness is downstream
- **P**: NOT_A_GRADED_INPUT: the pump reaches Q, hence MAP and delivery
- **Q**: NOT_A_GRADED_INPUT: flow reaches MAP (pressure = flow x tone) and delivery (delivery = flow x content)
- **R**: NOT_A_GRADED_INPUT: a perfusing rhythm's output factor reaches Q; a non-perfusing rhythm is arrest; R stays authoritative for pulse_present
- **SpO2**: DEFERRED: oxygenation already reaches oxygen content and so delivery; revisit in generalization if a respiratory family shows that is insufficient
- **acidemia_pH**: NOT_AN_INPUT: no path to P or R today; the acid burden integrates the deficit
- **lactate**: NOT_AN_INPUT: a marker and a consequence

**Estado de cada parte** (texto congelado, en inglés):

- **aggregation**: MAXIMUM (faculty): no sum and no interaction term
- **approved**: none FACULTY_APPROVED
- **burden_kinetics**: UNSET (tau); the form is structural: exact first-order relaxation toward signal x tau, never from tau_D, lactate or the encephalopathy memory
- **current_nonviability**: UNSET
- **delivery_failure**: STRUCTURAL_IDENTITY_ON_THE_CERTIFIED_NORMALIZED_DEFICIT: no clinical onset threshold; whether one is needed is UNSET
- **map_mapping**: UNSET_CLINICAL_MAPPING
- **p2e3**: the P2E-3 output rule and this candidate are never active together (shadow_step refuses it)
- **pulse**: RhythmState.pulse_present is the EFFECTIVE PERFUSING RHYTHM STATE, not a guaranteed palpable peripheral pulse; never derived from pressure. pulse=true with an extremely low MAP is a transient profound collapse
- **ramp_shape**: STRUCTURAL_SHAPE_PROVISIONAL: linear between the two MAP bounds, saturating at 0 and 1
- **rosc**: ROSC_NOT_CURRENTLY_MODELED
- **terminal_burden**: UNSET
- **terminal_machinery**: STRUCTURAL_TEST_ONLY: the shadow transition is carried by the existing scripted-rhythm primitive and derived.terminal_rhythm; its provenance reads scripted, so a runtime integration needs the core's own collapse source (not done here)
- **terminal_rhythm**: TERMINAL_RHYTHM_PHENOTYPE_UNSET
- **zero_flow**: pulse=true with Q at the numerical zero stays an inconsistent state that fails loudly (derive's UnresolvedBoundary, the RhythmState invariant): a coding invariant, never a clinical arrest rule

**Valores de las sondas** (texto congelado, en inglés): SYNTHETIC_ONLY: perfusion mapping (viable 90, failed 0 mmHg) anchored to the neutral probe arrival's own MAP; burden tau 30 min (P2E-3's committed synthetic repayment); terminal burden 10 (P2E-3's synthetic limit, minutes at full signal); current non-viability floor 0.5; PEA only to exercise the existing terminal machinery. None is a candidate, a range or an approval.
<!-- /generado:candidato -->

## 3. Sondas estructurales C1–C14

<!-- generado:sondas -->
| Sonda | Qué prueba (congelado) | Cumple |
|---|---|---|
| C1 | normal perfusion + normal delivery -> collapse_signal = 0 | sí |
| C2 | perfusion failure only -> signal > 0 | sí |
| C3 | delivery failure only -> signal > 0 | sí |
| C4 | both abnormal -> signal = max, not sum | sí |
| C5 | Q changes with MAP / DO2 fixed -> no independent Q term | sí |
| C6 | SpO2 changes with effective delivery fixed -> no direct SpO2 term | sí |
| C7 | lactate / D / I / F (and pH) changed alone -> signal unchanged | sí |
| C8 | one transient severe insult -> burden rises, no terminal transition (persistence required) | sí |
| C9 | prolonged severe insult -> burden rises further and meets the synthetic terminal criterion | sí |
| C10 | near-threshold burden + physiology restored -> burden decays, no delayed arrest | sí |
| C11 | intermittent insults with recovery -> no indefinite accumulation | sí |
| C12 | pulse=false -> Q / pressure / DO2 terminal consistency | sí |
| C13 | pulse=true + Q=0 -> the invariant fires | sí |
| C14 | pulse=true + near-zero Q / MAP -> representable profound collapse before arrest | sí |

Lecturas (valores sintéticos):

- **C1–C4 inyectadas:** (0; 0) → 0,00; (0,6; 0) → 0,60; (0; 0,5) → 0,50; (0,6; 0,5) → 0,60, no 1,1.
- **C2 en estado** (tono 0,45): PAM 48,5, falla de PAM 0,461, de aporte 0,000.
- **C3 en estado** (Hb al 25 %): falla de PAM 0,000, de aporte 0,375.
- **C4 en estado** (bomba 0,3): 0,700 y 0,250 → señal 0,700 (la suma sería 0,950).
- **C5:** gasto 0,500 frente a 0,357 con la misma PAM (45,00) y el mismo aporte; diferencia de señal -1.1e-16. El estado de la revisión ALTO-2 de P2M-1 (bomba 0,7, tono 2,0: gasto 0,538, PAM 96,9) da señal 0,00.
- **C6:** SpO2 97,0 frente a 73,3 con el mismo aporte: señal 0,700 en ambos.
- **C7:** con bomba 0,3 la señal es 0,700; con D, lactato o carga ácida cambiados solos: D 0,700, acid_pH 0,700, lactate 0,700. I y F: not readable: the candidate imports neither the encephalopathy candidate nor any consciousness code.
- **C12:** sin pulso, gasto 0,0, PAM —, aporte 0,0; estado ARREST; la carga pasa de 4 a 0,0.
- **C13:** con pulso y gasto en el cero numérico: evaluate → UnresolvedBoundary, rhythm → CoreInvariantError, shadow_step → UnresolvedBoundary.
- **C14:** con pulso, PAM 1,8 (bomba 0,02) y 4,5 (bomba 0,1 con bloqueo AV): colapso representable; el primer minuto no produce transición.
<!-- /generado:sondas -->

## 4. Persistencia: la carga existente, con repago

<!-- generado:persistencia -->
**Forma** (texto congelado, en inglés): `b(t+1) = b(t) e^(-1/tau) + s(t) tau (1 - e^(-1/tau)): exact first-order relaxation toward s tau`.

- **C8, un insulto breve** (3 min a señal 1): pico 2,85; transición: no. Un minuto al máximo suma a lo sumo 0,984; el perfil rechaza un límite a esa altura: sí.
- **C9, un insulto prolongado** (señal 0,9): carga 2,57 a los 3 min, 10,07 a los 14, 23,35 a los 60; criterio sintético en el minuto 14.
- **C10, fisiología restaurada:** desde 9,9: 1,34 a los 60 min y 0,18 a los 120, cae siempre: sí, paro tardío: no; desde 12,0: 1,62 a los 60 min y 0,22 a los 120, cae siempre: sí, paro tardío: no. Restauración parcial (señal 0,3, bajo el piso 0,5): 9,05 a los 120 min, hacia 9,0; paro: no. El perfil rechaza un criterio sin piso de no viabilidad actual: sí.
- **C11, insultos intermitentes** (5 min at 1.0, 25 min at 0, for 24 h): picos 4,61 → 7,29, crecimiento en el último ciclo 0,000000; máximo 7,29 (cota τ = 30); paro: no.
<!-- /generado:persistencia -->

## 5. Orden de eventos y bucles

<!-- generado:orden -->
Orden: `state(t) → derive(t) → collapse_signal(t) → carga(t+1) → decisión (persistencia + no viabilidad actual) → transición del ritmo en el minuto del núcleo → state(t+1)`.

- **Trayectoria** (bomba 0,1): transición en el minuto 14, una sola (1); carga al cumplirse 9,49 antes del minuto; cada minuto lee el estado previo: sí. Después: ARREST, carga 0,0, pulso no.
- **Código:** `evaluate` una vez por minuto (1), antes del paso del núcleo: sí, sobre el estado de inicio: sí.
- **Diferimiento:** en el minuto 14 un evento guionizado pasa a bloqueo AV; la transición se difiere (sí) y en el 15 se decide sobre la fisiología del ritmo nuevo (señal 0,95): pea.
- **Paro guionizado con carga:** carga 3,37 → 0,0 al perder el pulso.
- **Carga vieja con fisiología normal** (revisión ALTO-1 de P2M-1): carga 10,5, señal 0,0 → 10,16, pulso sí, sin transición.
<!-- /generado:orden -->

## 6. Llegada

<!-- generado:llegada -->
- **Llegada de referencia:** carga 0,0, señal 0,00; a los 30 min, carga 0,00.
- **Llegada con PAM 70 (presión autorizada 95/57,5):** carga 0,0, señal 0,222 (la de su fisiología, no forzada a 0); a los 30 min, carga 4,21, sin transición.
<!-- /generado:llegada -->

## 7. ROSC

<!-- generado:rosc -->
- **Estado:** ROSC_NOT_CURRENTLY_MODELED.
- Tras la transición la carga es 0,0; un estado con ritmo que perfunde (el que daría un ROSC futuro, con terminal_since borrado por esa regla futura) se evalúa: EVALUATED. El candidato no lee terminal_since: sí.
- Guardas del núcleo que siguen: el regreso del pulso lanza un error (sí); terminal_since no se borra (sí).
<!-- /generado:rosc -->

## 8. Generalización a siete familias

<!-- generado:generalizacion -->
| Familia | Qué mueve su escritor | Lógica esperada | Falla de PAM | Falla de aporte | Señal | Domina | Cumple |
|---|---|---|---|---|---|---|---|
| Shock hemorrágico | V and Hb fall | MAP + delivery failure | 0,433 | 0,150 | 0,433 | PAM | sí |
| Shock cardiogénico | P falls | derived MAP / DO2 failure | 0,700 | 0,250 | 0,700 | PAM | sí |
| Shock obstructivo | effective preload falls, Hb kept (no obstruction channel: the writer lowers preload) | derived MAP / DO2 failure | 0,616 | 0,040 | 0,616 | PAM | sí |
| Shock distributivo | T falls: flow kept or raised | MAP failure dominates despite preserved flow | 0,461 | 0,000 | 0,461 | PAM | sí |
| Anafilaxia | T falls and V leaks | the same distributive / common path | 0,567 | 0,000 | 0,567 | PAM | sí |
| Arritmia maligna (pulseless) | a non-perfusing rhythm; a perfusing VT with a low output factor | no-pulse rhythm = arrest; pulse-present rhythm collapses through MAP / DO2 | — | — | paro | — | sí |
| Arritmia maligna (with_pulse) | a non-perfusing rhythm; a perfusing VT with a low output factor | no-pulse rhythm = arrest; pulse-present rhythm collapses through MAP / DO2 | 0,700 | 0,250 | 0,700 | PAM | sí |
| Insuficiencia respiratoria (neutral_reserve) | SpO2 falls (FiO2 1.0 withdrawn), flow and Hb kept | delivery failure may drive collapse without a direct SpO2 input | 0,000 | 0,244 | 0,244 | aporte | sí |
| Insuficiencia respiratoria (probe_reserve) | SpO2 falls (FiO2 1.0 withdrawn), flow and Hb kept | delivery failure may drive collapse without a direct SpO2 input | 0,000 | 0,000 | 0,000 | — | sí |

Términos de enfermedad en el candidato: ninguno. (texto congelado, en inglés): every family is read by the same collapse.readings / signal_at; no family branch.
<!-- /generado:generalizacion -->

## 9. Subconjunto extremo GI (diagnóstico)

<!-- generado:subconjunto -->
- **Filas:** 17 604 (57m: 17 604); filtradas: no; pulso: sí; PAM a los 120 min 32,5–46,3 mmHg.
- **Entradas disponibles:** MAP, effective deficit. **Estado:** `EVALUABLE_ONCE_MAPPINGS_DEFINED`; clasificación: ninguna.
- (texto congelado, en inglés): the rows keep a pulse with MAP and an effective deficit, the two inputs the layer reads; with the MAP mapping, the kinetics and the terminal criterion UNSET no row is classified as arrest or non-arrest and no number was chosen from them
<!-- /generado:subconjunto -->

## 10. Reemplazos de P2M-1

<!-- generado:supersesion -->
| Punto de P2M-1 | Estado | Lo que decía P2M-1 (congelado) | Lo que lo reemplaza | Evidencia |
|---|---|---|---|---|
| ambiguous_arrival_zero_semantics | `SUPERSEDED_BY_P2M2` | P2M-1 minimum 3: require a null signal at arrival (review MEDIUM-6) | the arrival burden is 0 by default; the arrival signal is the arrival physiology's, never forced to 0 | arrival |
| flow_only_overstatement | `SUPERSEDED_BY_P2M2` | P2M-1 redundancy: 'the low flow never fails alone', which held only for the chosen probes (review HIGH-2) | Q is not a graded input by decision; a flow fall that keeps MAP and delivery reads no collapse signal | C5 (flow_alone_h2) |
| incomplete_persistence_invariants | `SUPERSEDED_BY_P2M2` | P2M-1 minimum: a persistence floor and a mandatory repayment, still to decide (review MEDIUM-7) | the nine burden semantics formalized: repayment by construction (relaxation toward signal x tau), the floor enforced by the profile, the terminal criterion needs current non-viability | C8-C11 |
| probe_dependent_frozen_verdict | `SUPERSEDED_BY_P2M2` | P2M-1's frozen redundancy_resolved / persistence_classified leaned on the probe choice (review HIGH-2, MEDIUM-7) | each P2M-2 criterion is a property of the candidate checked by construction (its profile invariants and code scan) and on probes; the probes illustrate, they do not define the property | criteria |
| stale_burden_on_rhythm_deferral | `SUPERSEDED_BY_P2M2` | P2M-1 review HIGH-1: a burden left at the limit arrests a patient with normal output the next minute | any loss of the pulse resets the burden; the terminal criterion reads the current signal, so a stale burden never arrests normal physiology | event_order.deferral / stale_burden_normal_physiology / C10 |

El registro y el informe de P2M-1 no se reescriben (huella fijada).
<!-- /generado:supersesion -->

## 11. Estado de los parámetros

<!-- generado:parametros -->
- **burden_tau_repayment_kinetics:** `UNSET`
- **delivery_failure_threshold:** `UNSET (the structural signal is the certified normalized deficit itself)`
- **map_failure_mapping:** `UNSET_CLINICAL_MAPPING`
- **minimum_current_nonviability:** `UNSET`
- **rosc:** `NOT_MODELED`
- **terminal_burden_threshold:** `UNSET`
- **terminal_rhythm_phenotype:** `TERMINAL_RHYTHM_PHENOTYPE_UNSET`
- **test_numbers:** `SYNTHETIC_ONLY`
<!-- /generado:parametros -->

## 12. No regresión de la fisiología previa

<!-- generado:no_regresion -->
| Elemento | Idéntico |
|---|---|
| BloodState | sí |
| gasto | sí |
| presión / tono | sí |
| DO2 / déficit | sí |
| D | sí |
| lactato | sí |
| FC / barorreflejo | sí |
| ácido-base | sí |
| FR / W | sí |
| conciencia | sí |

- **Inactiva:** el árbol de P2M-1 coincide byte a byte: sí (67 archivos, `ecbcfefce945…`); importan el candidato sólo: clinical_core/collapse_architecture.py.
- **Activa en sombra** (30 min, bomba que cae 0,03 por minuto, cinética sintética sin criterio terminal): todo el estado salvo la carga coincide: sí; registros del núcleo idénticos: sí; carga del núcleo 0,0, de la capa 8,43.
<!-- /generado:no_regresion -->

## 13. Veredicto

<!-- generado:veredicto -->
| Criterio | Cumple |
|---|---|
| máximo de la falla de PAM y la de aporte | sí |
| sin entradas duplicadas (Q, SpO2, lactato, D, pH, I, F) | sí |
| la persistencia se repaga | sí |
| la carga histórica sola no produce paro | sí |
| llegada: carga 0, señal de la fisiología real | sí |
| orden de eventos acíclico | sí |
| sin pulso, coherente | sí |
| un ROSC futuro sigue siendo posible | sí |
| las siete familias pasan | sí |
| fisiología previa intacta | sí |
| ningún umbral clínico aprobado | sí |

**Veredicto:** `COMMON_COLLAPSE_SAFETY_ARCHITECTURE_READY_FOR_GENERALIZATION`.
<!-- /generado:veredicto -->

## 14. Recomendación estratégica

<!-- generado:recomendacion -->
**Recomendación:** `MOVE_TO_SECOND_FAMILY_GENERALIZATION_WITH_COLLAPSE_THRESHOLDS_UNSET`.

- ¿Hace falta calibrar el colapso numéricamente antes de la segunda familia? no.
- Por qué (texto congelado, en inglés): the layer is shadow and inactive; a second family is exercised structurally with synthetic numbers, and no family needs a clinical arrest enforced to be migrated in shadow; the clinical numbers stay faculty decisions from general physiology

Regla (texto congelado, en inglés): Predeclared. READY: numeric collapse calibration is not required before second-family generalization while the layer stays shadow / inactive and can be exercised structurally without enforcing a clinical arrest: MOVE_TO_SECOND_FAMILY_GENERALIZATION_WITH_COLLAPSE_THRESHOLDS_UNSET; no GI collapse-calibration package is opened because thresholds stay UNSET. NOT_READY: the blocker and the smallest correction.
<!-- /generado:recomendacion -->

## 15. Decisiones pedidas

<!-- generado:pedidas -->
Decisiones pedidas a la docencia (texto congelado, en inglés):

1. the MAP failure mapping (viable and failed bounds; absolute or relative to the patient's autoregulation), from general physiology, never from the GI cases
2. whether the delivery-failure signal needs an onset threshold above the certified normalized deficit
3. the burden time constant (one tau for accrual and repayment, as structured) and the terminal burden
4. the minimum current non-viability floor
5. the terminal rhythm phenotype (PEA / asystole) or its selection rule
6. direct SpO2: stays DEFERRED unless a respiratory family shows delivery is insufficient
7. runtime integration: the core's own collapse source replacing the scripted-rhythm primitive, and the P2E-3 output rule's retirement
8. ROSC in a later package (the reset burden and the candidate's indifference to terminal_since keep it possible)
<!-- /generado:pedidas -->

Decisiones agregadas por la revisión adversarial (§18):

9. Corregir `shadow_step`, recongelando, antes de usar la capa sobre la trayectoria de una familia: un solo minuto del
   núcleo con la transición, y el diferimiento decidido sin materializar state(t+1).
10. Decidir cómo registra el Trace la escritura de la carga: un `AuxiliaryChange` de la capa o la fuente de colapso del
    propio núcleo en la integración.
11. Confirmar la lectura adoptada de «se repaga cuando la señal mejora»: con una sola τ, la acumulación baja de inmediato
    y la carga cae una vez que supera `señal × τ`.
12. Aceptar el registro con estas correcciones o recongelar.

## 16. Eficiencia

<!-- generado:eficiencia -->
- Secciones de estado fijo leídas por el núcleo certificado: signals, no_q, no_spo2, no_markers, no_pulse, generalization.
- Minutos de sombra o del núcleo: 179; actualizaciones de la carga: 1923.
- Trayectorias GI: 0; barrido cartesiano: no; región reconstruida: no; motor heredado ajustado: no.
- Registros reutilizados (con huella fijada): P2M1_collapse_audit.json.
<!-- /generado:eficiencia -->

## 17. Limitaciones

- **Sólo sombra.** Ningún paso del núcleo lee el candidato; no hay gancho en tiempo de ejecución.
  - La transición de prueba usa el evento de ritmo guionizado (`STRUCTURAL_TEST_ONLY`); su procedencia dice
    «scripted».
  - Una integración real necesita la fuente de colapso del propio núcleo y retirar la regla P2E-3, que sigue en el
    núcleo, apagada.
- **Forma de la carga.** Usa una sola τ para acumular y repagar. Al mejorar la señal, la acumulación baja en ese mismo
  minuto, pero la carga sigue subiendo mientras esté por debajo de `señal × τ`; cae cuando la supera, y siempre con
  señal 0.
  - Ésa es la lectura de «se repaga cuando la señal mejora» adoptada aquí.
  - Un repago más rápido que la acumulación necesitaría un parámetro más, que no se agregó.
- **Invariantes del perfil.** Imponen que el límite terminal esté por encima de lo que suma un minuto y por debajo de τ.
  Son relaciones estructurales, no valores.
- **El aporte depende de la reserva de extracción.** Con 2,5 (perfil de sondas), la hipoxemia moderada no da señal
  (está compensada); con 1, sí.
  - El aporte relativo a la llegada no ve una hipoxemia ya presente a la llegada (límite M5 de P2M-1, que sigue).
  - Si una familia respiratoria muestra que esto no basta, la SpO2 directa se revisa en la generalización.
- **El mapeo sintético** (viable 90, falla 0 mmHg) está anclado a la PAM de las sondas.
  - Con él predomina la PAM en casi todos los estados de flujo bajo. Ese predominio depende del mapeo, que está UNSET; no
    es un hallazgo.
- **No regresión en sombra activa.** Se probó en una trayectoria de sondas de 30 minutos (perfil de sondas: ganancia de
  tono 0, barorreflejo apagado).
  - La garantía de la capa inactiva es el árbol idéntico byte a byte, más el golden.
- **Sin trayectorias GI.** Las cifras del subconjunto vienen del registro fijado de P2M-1.
  - Con la rampa sintética y el piso 0,5, el límite cae en PAM 45, dentro del rango GI (32,5–46,3). Si se aplicara al
    subconjunto lo partiría; no se aplicó.
- **Criterios que no pueden fallar** (revisión B1). Tres comprobaciones de `no_clinical_threshold_approved` comparan
  constantes: la clasificación del subconjunto, el estado de aprobación y el perfil por defecto. Lo mismo pasa con la
  desigualdad 0,6 ≠ 1,1 de C4.
- **Semántica previa de la carga** (B2). `state.py` y `derived.py` todavía la describen como la de P2E-3 (gasto
  críticamente bajo, 0 con la regla apagada). El núcleo no se toca; se actualiza con la integración.
- **Tipos del perfil** (B4). No se validan: una tupla en lugar del mapeo falla recién al usarla. Un criterio terminal con
  el mapeo UNSET se acepta y nunca evalúa.
- **Proceso** (B6). Las sondas estructurales se ejercitaron (pasa / no pasa) mientras se escribían los módulos, antes del
  congelamiento. No había ningún número clínico que ajustar.

## 18. Revisión adversarial

Una revisión independiente, de sólo lectura, sobre `2213173` y `fb50c3e`. Confirmé cada hallazgo medio con una sonda
propia antes de actuar. Las sondas quedaron fuera del repositorio.

**Revisado y limpio:**
- `derived.py`, `integration.py` y `state.py` son byte a byte los de `61628ec`. Las pruebas cerradas sólo excluyen los
  módulos nuevos.
- Los JSON de P2G, P2I, P2I-2T y P2I-2U sólo cambian el digest.
- La no regresión se mantiene también con ganancia de tono 0,5 y barorreflejo 0,5.
- Los mutantes de suma, término de Q, término de SpO2, carga sin decaimiento, carga histórica que basta para el paro y
  llegada forzada a 0 dan NOT_READY.
- La carga queda acotada.
- No hay paro tardío por debajo del piso.
- El fenotipo UNSET falla en voz alta.
- No hay ningún umbral GI.
- Las cifras del informe coinciden con el registro.
- El congelamiento está íntegro.

**Hallazgos:**

- **MEDIO-1. El minuto contrafactual puede fallar donde el orden declarado no falla.** En un minuto con la transición
  debida, `shadow_step` corre primero el minuto del núcleo sin la transición. Si ese estado t+1 tiene pulso y gasto 0
  (V vaciado en ese minuto), lanza un error, aunque con la transición aplicada en el mismo minuto el estado sin pulso
  es válido.
  - No hay bucle: la decisión se toma una sola vez, sobre state(t).
  - *Confirmado y fijado en una prueba.* La corrección (un solo minuto del núcleo con la transición, y el diferimiento
    decidido sin materializar state(t+1)) exige recongelar. Decisión 9.
- **MEDIO-2. La carga se escribe sin registro de procedencia.** El registro del minuto del núcleo no la lleva (sí el
  `ShadowMinute`), y la comprobación de conservación del núcleo fallaría sobre ese minuto.
  - *Confirmado y fijado en una prueba.* Se resuelve en la integración. Decisión 10.
- **MEDIO-3. `no_duplicate_inputs` no podía fallar por una fuga de lactato o D hacia el aporte.** El C7 congelado
  compara sólo la señal en un estado donde domina la PAM, y el escaneo sólo ve atributos.
  - El candidato está limpio.
  - *Reforzado en pruebas:* una prueba nueva compara las dos entradas en un estado dominado por el aporte (Hb al 25 %),
    detecta una fuga plantada de lactato y revisa las lecturas indirectas. La redacción del resumen quedó corregida.
- **Bajos.**
  - B1: comprobaciones constantes dentro de los criterios.
  - B2: semántica previa de `aux.collapse_burden` en el núcleo.
  - B3: el piso de persistencia vale desde carga 0 (redacción corregida y fijada en una prueba).
  - B4: tipos del perfil sin validar (fijado en una prueba).
  - B5: el piso sintético cae dentro del rango GI.
  - B6: nota de proceso.

  Todos quedan declarados en §17.

**Sin segundo congelamiento,** como pide el encargo y como se trató en P2L-1, P2L-2 y P2M-1. Sólo se corrigió lo no
congelado: pruebas, informe y documentos. El registro sigue siendo el de la corrida del congelamiento `5f96f860`.
