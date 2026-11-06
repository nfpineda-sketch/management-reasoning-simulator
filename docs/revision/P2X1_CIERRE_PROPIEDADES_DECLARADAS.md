# P2X-1 · Cierre de las propiedades declaradas de la Fase 2

Cambio común, en sombra. Rama `phase-2-clinical-core-shadow`; base `d4e6fe9` (P2W-0, P2W-1, P2W-2 y P2X-0 aceptados;
P2X-0 dio **B — `PHASE2_READY_AFTER_ONE_MINIMUM_PACKAGE`**).

P2X-0 dejó exactamente dos deudas genuinas antes de la salida, y este paquete las cierra **sin añadir fisiología
clínica y sin elegir ninguna magnitud**.

1. **El dominio declarado del tono distributivo.** P2W-1 publicó tres afirmaciones que sólo valían en parte del
   dominio que declaró: que el factor distributivo está «en 1 o por debajo» (cierto sólo con la carga en o sobre la de
   llegada), que el chequeo de ganancia de `_vascular_tone` impide que la guarda de T modele la respuesta (lee sólo la
   compensación), y que la cota de contracción `g·a < 1` cubre el lazo (no escala con el factor distributivo). La
   docencia decidió que una carga por debajo de la de llegada **es resolución permitida**, que una carga negativa es
   inválida y no es vasoconstricción, que las guardas deben contemplar `Bmax = 1 + k·b₀`, y que una combinación que
   saliera del dominio soportado debe **fallar cerrado** en vez de dejar que el recorte del canal defina la
   fisiología.
2. **El veredicto histórico de P2S-3.** Su regla congelada devolvió READY; la revisión adversarial mostró una brecha
   del impulso común; la clasificación operativa corregida fue NOT_READY; P2T-1/P2T-2/P2T-3 resolvieron ese bloqueo y
   P2T-3 es el resultado autoritativo del asma. No se re-corta ni se reescribe nada: se declara la supersesión.

- **Cambio común mínimo** (`integration.py`, `provenance.py`; más las dos tuplas de registro), probado contra
  `d4e6fe9`:
  - `integration.tone_domain`: las formas cerradas del objetivo alcanzable y de la cota del lazo retardado;
  - en `_vascular_tone`, donde el lector distributivo está declarado: admisibilidad superior, cota de contracción
    derivada y, cada minuto, la frontera semántica que falla cerrado;
  - en `provenance.VasodilationChange`: el contrato del escritor (sin carga negativa; sin leer la PAM, `pressure_rel`
    ni T), estructural y verificado por un escaneo del repositorio.
- **Análisis:** `clinical_core/tone_domain.py`, congelado antes de la única evaluación. **Registro:**
  `docs/revision/P2X1_tone_domain.json`. Este documento se genera desde el registro
  (`clinical_core/tone_domain_report.py`); el texto fuera de los marcadores es la narrativa.

## 1. Las decisiones docentes que rigen

<!-- generado:decisiones -->
- **1_below_arrival_burden:** BELOW_ARRIVAL_BURDEN = ALLOWED_RECOVERY: b < b0 is the resolution of the arrival distributive vasodilation, physiologically allowed and not a generic vasopressor signal; the maximum recovery is at b = 0, so Bmax = 1 + k b0. T rising above the arrival-relative 1 is not a reason to reject it
- **2_no_negative_burden:** the burden stays at or above 0; a writer never resolves it below physiologic zero and a negative burden is NOT vasoconstriction (a vasopressor acts through its own mechanism)
- **3_guards_include_the_factor:** the upper-target admissibility and the contraction analysis of the delayed T loop must both account for Bmax = 1 + k b0: the full reachable target under the declared domain must stay inside the range for which the architecture claims the guard does not shape physiology
- **4_fail_closed:** TONE_CLAMP_AS_PHYSIOLOGY = REJECTED: a declared parameter / state combination whose tone target would leave the supported domain fails closed (CoreInvariantError, this repository's semantic boundary) before execution instead of being clamped into shape; the channel guard remains the last safety layer but is never the expected clinical response
- **5_no_pressure_driven_writer:** PRESSURE_DRIVEN_FAMILY_VASODILATION = DEFERRED / NOT_AUTHORIZED: a family writer of the burden may not read the current MAP, pressure_rel, T or another same-loop haemodynamic observable; allowed inputs are its disease-process state, time, a treatment and authored family mechanisms
- **6_maldistribution:** the distributive CRT / lactate direction is FUTURE_RESEARCH_DEBT, not a Phase-2 blocker: no MIGRATED_AND_CERTIFIED family writes the burden and anaphylaxis is not required for exit; no maldistribution, extraction heterogeneity, distributive CRT or distributive lactate model is implemented here
- **7_anaphylaxis_gaps:** plasma leak without red-cell loss, maldistribution / extraction, upper-airway and stridor representation, a pharmacologic chronotropic target, epinephrine kinetics and the anaphylaxis parameter regions are POST-PHASE2 / FAMILY-MIGRATION work
- **8_p2s3:** TD120_HISTORICAL_SUPERSESSION_ACCEPTED: the historical P2S-3 frozen package, its sources and its digest are not recut or rewritten; the operative result is declared superseded by P2T-3
- **scope:** a closure package: no new clinical physiology, no magnitude, no new canonical state, no runtime integration, no Phase 3
<!-- /generado:decisiones -->

## 2. El dominio alcanzable, derivado (P2X-1-1)

Derivación analítica sobre las ecuaciones reales, verificada numéricamente en los extremos y en la pendiente. La
señal tiene **un codo** —donde el déficit efectivo llega a 0—: por debajo el lazo es plano, así que la forma cerrada
se comprueba en la rama activa y el codo se informa aparte.

<!-- generado:derivacion -->
- B_range: `(0, 1 + k b0], strictly decreasing in b, exactly 1 at b = b0, maximum 1 + k b0 at b = 0`
- C_range: `[1 / (1 + g s0), (1 + g) / (1 + g s0)], non-decreasing in s`
- b_domain: `b in [0, inf): the state domain of aux.vasodilatory_burden (no clinical maximum is declared)`
- independence: `s reads delivery and demand (derived.acute_deficit_signal), b is written by a family and read nowhere else: neither factor reads the other, so the reachable set is the product of the ranges`
- infimum: `0, approached as b grows without bound; not attained`
- insufficiency: `with a distributive reader declared, 1 + g (the published admissibility check) sees neither Bmax nor a severe burden, and g a < 1 does not scale with Bmax: both were insufficient exactly where the distributive factor is active`
- loop: `T -> afterload A(T) = 1 / (1 + a (T - 1)) -> output -> delivery -> s -> target -> T_next, one minute behind`
- maximum: `C_max x B_max = (1 + g) (1 + k b0) / (1 + g s0), at s = 1 (no effective delivery) and b = 0`
- monotonicity: `non-decreasing in s, strictly decreasing in b; the two are independent, so the extremes are the products of the extremes`
- p2j2_bound: `g a < 1 is this bound with B = 1 and the A(T_lo) / (1 + g s0) factor dropped; it was published as a profile invariant and is NOT reopened here`
- s_domain: `s in [0, 1]: effective_oxygen_deficit is max(0, demand - reserve x delivery) over demand`
- slope: `d(target)/dT = B(b) x [g / (1 + g s0)] x a x A(T) x (1 - s) on the active deficit branch, 0 off it: from s(T) = max(0, 1 - mu A(T)) with mu = reserve x arrival_delivery_ratio x K / demand (K the part of delivery that does not read T), so ds/dT = mu a A(T)^2 = (1 - s) a A(T)`
- slope_bound: `(1 + k b0) g a A(T_lo) / (1 + g s0), with T_lo the lower end of the supported range: (1 - s) <= 1, B(b) <= 1 + k b0 and A is decreasing`
- target: `tone_target = C(s) x B(b), C(s) = (1 + g s) / (1 + g s0), B(b) = (1 + k b0) / (1 + k b)`
- where_the_guards_are_hit: `above, when C_max x Bmax > T's upper guard (reached by resolution, b -> 0); below, when C(s) B(b) < T's lower guard (reached by a severe burden)`

| Extremo | Observado | Predicho |
|---|---|---|
| arrival_is_one | 1,000000 | 1,000000 |
| compensation_max | 1,395349 | 1,395349 |
| far_below | 0,000001 | 0,000001 |
| joint_max | 2,093023 | 2,093023 |
| recovery_max | 1,500000 | 1,500000 |

| T | Pendiente numérica | Forma cerrada | Rama activa | Coincide | Bajo la cota |
|---|---|---|---|---|---|
| 1.0 | 0,118605 | 0,118605 | sí | sí | sí |
| 1.5 | 0,089682 | 0,089682 | sí | sí | sí |
| 2.0 | 0,070180 | 0,070180 | sí | sí | sí |
| 2.5 | 0,056411 | 0,056411 | sí | sí | sí |

- Codo de la señal (el déficit efectivo llega a 0) en T = 0,500000: por debajo la pendiente es 0,000000 (plana: sí) y por encima 0,164159 (bajo la cota: sí).
- Monótona en la carga: sí; en el déficit: sí.
- Formas cerradas: sí; pendiente: sí. Pasa: sí.

- Dominio con el lector declarado: compensación [0,930233, 1,395349], recuperación máxima 1,500000, objetivo mayor 2,093023, ínfimo 0 (approached as the burden grows; no clinical maximum burden is declared), rango soportado [0.1, 3.0].
- Cota del lazo derivada: 0,286716; la de P2J-2, g·a: 0,150000.
<!-- /generado:derivacion -->

## 3. Las guardas implementadas (P2X-1-2 y P2X-1-3)

Lo que se añadió son **rechazos**: ninguna lectura aceptada cambia, y el delta que el acoplamiento devuelve sigue
siendo el mismo. Los chequeos publicados de P2J-2 quedan intactos; la cota derivada se aplica exactamente donde
existe el factor distributivo, de modo que la región admisible de todo perfil sin lector declarado es idéntica.

<!-- generado:guardas -->
- Invariante de perfil de P2J-2: deficit_to_tone_gain x afterload_sensitivity < 1, in CoreProfile.__post_init__ — intacto: sí.
- Chequeo de ganancia de P2J-2 intacto: sí.
- `tone_domain` lee: T, afterload_sensitivity, arrival_vasodilatory_burden, deficit_to_tone_gain, vasodilatory_burden_to_tone_gain.
- Admisibilidad superior: largest_target > upper, where the distributive reader is declared.
- Contracción: loop_slope_bound >= 1.0, where the distributive reader is declared.
- Frontera por minuto: not lower <= target <= upper, every minute.
- Sólo se añadieron rechazos: sí; el delta devuelto sigue siendo `target - state.T`.

Rechazos del acoplamiento, en orden:

1. f"the tone response's largest target 1 + {profile.deficit_to_tone_gain
2. f'minute {minute}: {writers} write T while the vascular-tone response
3. f"minute {minute}: the tone target {target!r} leaves T's supported ran
4. f"the tone target's largest reachable value {domain['largest_target']!
5. f"the tone loop's derived bound with the distributive factor, {domain[
<!-- /generado:guardas -->

## 4. El contrato del escritor (P2X-1-4)

<!-- generado:contrato -->
- Contrato declarado en `provenance.VasodilationChange`: sí.
- Entradas prohibidas a un escritor de familia: map, pressure_rel, mean_arterial_pressure, sbp, dbp, T.
- Entradas permitidas: the writer's own disease-process state; time; a treatment; authored family mechanisms that do not close the haemodynamic loop.
- Módulos que construyen el registro: `clinical_core/distributive_tone.py`.
- Escritores de familia: ninguno; infractores del contrato: ninguno.
- Pasa: sí.
<!-- /generado:contrato -->

## 5. Las quince sondas (X1–X15)

<!-- generado:sondas -->
| Sonda | Qué exige | Pasa |
|---|---|---|
| X1 | b = b0 gives the distributive factor exactly 1 | sí |
| X2 | b > b0 lowers the effective tone | sí |
| X3 | 0 <= b < b0 raises it as the vasodilation resolves (ALLOWED_RECOVERY) | sí |
| X4 | b = 0 is the maximum recovery, exactly 1 + k b0 | sí |
| X5 | b < 0 is rejected everywhere | sí |
| X6 | a reachable upper target outside the supported range fails closed | sí |
| X7 | a reachable lower target outside the supported range fails closed | sí |
| X8 | valid interior combinations run with no clamp | sí |
| X9 | the derived contraction condition holds for every accepted boundary witness | sí |
| X10 | a combination violating the derived condition is rejected | sí |
| X11 | burden 0 everywhere: the predecessor's behaviour, with one declared supersession | sí |
| X12 | every prior migrated family keeps its default behaviour exactly | sí |
| X13 | the systemic stress still does not affect T | sí |
| X14 | beta-blockade still does not affect T | sí |
| X15 | no pressure-driven vasodilation writer exists | sí |

- X3: con carga de llegada 2.0, sobre la rejilla [2.0, 1.0, 0.5, 0.25, 0.0] el objetivo va 1,0000 → 1,5000 → 2,0000 → 2,4000 → 3,0000: sube al resolverse (sí) y pasa de 1 por debajo de la carga de llegada (sí).
- X4: la recuperación máxima, observada y predicha: b0=0.5 k=1.0 → 1,500000 / 1,500000; b0=1.0 k=0.25 → 1,250000 / 1,250000; b0=2.0 k=1.0 → 3,000000 / 3,000000.
- X6: con k = 2.0 y b₀ = 10.0 el objetivo mayor es 29,3023, fuera de [0.1, 3.0]: rechazado sí, aunque el chequeo de P2J-2 pasaría (sí).
- X7: con carga 50.0 el objetivo es 0,019608, bajo el rango soportado: rechazado sí, y sin declarar ninguna carga máxima clínica (sí).
- X9: testigos aceptados, cota derivada contra la mayor pendiente viva: k=0.25 b0=2.0 → 0,2867 / 0,1186; k=1.0 b0=0.5 → 0,2867 / 0,1186; k=1.0 b0=1.0 → 0,3823 / 0,1186; k=None b0=0.0 → 0,1911 / 0,1186.
- X10: con k = 1.0 y b₀ = 0.0 la cota es 3,0473 (no contracción) con el objetivo mayor 1,3953 dentro del rango: rechazado sí, aunque la cota de P2J-2 pasaría (sí).
<!-- /generado:sondas -->

## 6. Supersesiones, con la historia intacta (P2X-1-6)

<!-- generado:supersesion -->
- **P2W1_V5_CLAMP_BEHAVIOUR_SUPERSEDED_BY_P2X1** — estado `P2W1_V5_CLAMP_READING_SUPERSEDED`.
  - Histórico: P2W-1's V5 read a severe burden as parking T on its lower guard with the clamp recorded, and published that as 'no clinical ceiling is chosen'.
  - Resuelto por: FACULTY DECISION 4 (TONE_CLAMP_AS_PHYSIOLOGY = REJECTED): that combination now fails closed before execution, and no clinical maximum burden is declared either.
  - Autoritativo: P2X-1's X7: the refusal, not the clamp.
  - Naturaleza: a declared-property correction inside the same architecture; the frozen P2W-1 record and its digest are unchanged, and every other P2W-1 probe still reproduces exactly (X11).
  - Historia preservada: the P2W-1 record is read, never rewritten.
- **TD120_HISTORICAL_SUPERSESSION_ACCEPTED** — estado `P2S3_FROZEN_VERDICT_SUPERSEDED_BY_P2T3`.
  - Histórico: P2S-3's frozen rule returned ASTHMA_SHADOW_MIGRATION_READY; its adversarial review then demonstrated a COMMON_DRIVE_GAP and the corrected operative classification was NOT_READY.
  - Resuelto por: P2T-1 (the common respiratory distress), P2T-2 (its cross-family identifiability) and P2T-3 (the asthma distress mapping), which closed that blocker.
  - Autoritativo: P2T-3: ASTHMA_SHADOW_MIGRATION_READY is the current asthma migration result.
  - Naturaleza: a traceability lesson: a frozen rule can return READY while a review shows otherwise, so the operative classification is the reviewed one. Not a current physiology blocker.
  - Historia preservada: no P2S-3 source, record or digest is recut or rewritten.

- Digest congelado de P2W-1 intacto: sí. Pasa: sí.
<!-- /generado:supersesion -->

## 7. La deuda consolidada de la Fase 2 (P2X-1-7)

Ninguna entrada es bloqueo por estar UNSET: una magnitud UNSET deja su término inerte, que es el diseño.

<!-- generado:deuda -->
**ACCEPTABLE_PHASE2_DEBT** (11):

- `COLLAPSE_THRESHOLDS`: TD-109 / TD-110: collapse is structural only, with no threshold
- `CUMULATIVE_FLOATING_POINT_CANCELLATION`: TD-121A: the binary64 roundoff snap is in place for the auxiliary sums; the general cancellation question stays open
- `FIO2_MAGNITUDE`: TD-123: the FiO2 response magnitude is UNSET
- `HYPOXAEMIC_FEEDBACK_STABILITY`: TD-117 / TD-123: the hypoxaemic drive mapping is UNSET, so the loop is off
- `OPIOID_HR_RESIDUAL`: TD-124: the 67f's authored 62 stays 1.89 bpm under the model's band; no opioid HR term was added
- `PHYSICAL_PAO2_BOUNDARY`: TD-123: the PaO2 floor is a declared boundary, non-blocking
- `PRESSURE_TO_TONE`: TD-118 point 4 / P2W-0: the compensation reads the oxygen deficit only; a pressure-driven tone compensation needs a new clinical gain, a reference pressure and an ordering decision, and stays open for ACS and PE
- `RESPIRATORY_DISTRESS_CALIBRATION`: TD-121 / TD-122: every distress gain and arrival region is UNSET
- `SIDED_PRELOAD_AND_INTERDEPENDENCE`: TD-118 point 2: the core has no sided preload
- `STEADY_STATE_W_ARRIVAL_TENSION`: TD-124: the arrival efficiency reads above its reference for both opioid cases against the authored shallow breaths; three exits exist, none chosen
- `SYSTEMIC_STRESS_CALIBRATION`: TD-125: the stress gain and every arrival region are UNSET

**FUTURE_RESEARCH_DEBT** (5):

- `ADDITIONAL_FAMILY_MIGRATIONS`: anaphylaxis and any further family
- `DRUG_KINETICS`: P2U-1 / P2W-2: naloxone, epinephrine and vasopressor kinetics are UNSET
- `MALDISTRIBUTION_AND_EXTRACTION`: FACULTY DECISION 6: the distributive CRT and lactate directions, accepted as research debt; no migrated family writes the burden
- `PLASMA_LEAK`: P2W-2: no blood process moves plasma without red cells for a disease module
- `UPPER_AIRWAY`: P2W-2: no common representation of upper-airway obstruction or stridor

**NEXT_PHASE_INTEGRATION_DEBT** (3):

- `CONSCIOUSNESS_WIRING`: TD-107 / TD-108 / TD-124: N is an unused placeholder and the encephalopathy layer is shadow only; the common ladder already reproduces the authored levels of the cases audited so far (P2W-2)
- `RESIDENT_VISIBLE_BEHAVIOUR`: nothing the resident sees changes in Phase 2
- `RUNTIME_INTEGRATION`: clinical_core runs in shadow; family_engine.py stays the source of truth

- no item is a blocker merely because it is UNSET: an UNSET magnitude leaves its term inert, which is the design.
- Bloqueos: ninguno. Pasa: sí.
<!-- /generado:deuda -->

## 8. No regresión y contradicciones causales

<!-- generado:no_regresion -->
- Registro de P2W-1 reproducido sobre su árbol: sí; intacto: sí; su veredicto COMMON_DISTRIBUTIVE_TONE_COMPOSITION_READY.
- Valores por defecto de cada familia comprometida, exactos: sí.
- Tuplas de registro: DOWNSTREAM_REPORTS sí, PACK_DIGEST_EXCLUDED sí.
- Pasa: sí.

Búsqueda de contradicciones causales dentro del alcance certificado:

- disease_specific_rule_in_the_common_core: no: the tone equation reads the common burden, its arrival anchor and the profile gain only; no family name appears in it
- hidden_point_calibration: no: every distributive and stress magnitude is UNSET, and the probe values are declared SYNTHETIC_ONLY
- impossible_ordering: no: the tone answers the previous minute's signal, the burden is written before it is read, and the arrival is the response's fixed point
- incompatible_writer_ownership: no: T keeps exactly one writer (the core's response), the burden one interface, and a family delta on T is refused
- same_mechanism_double_counted: no: the compensation reads the oxygen deficit only and the burden is written by a family; the two factors are independent and multiply once
- unstable_feedback: no: the delayed loop's derived bound is a contraction for every accepted combination, and a combination that is not is refused (X9, X10)
- worse_state_improves_output: inside the certified scope, no: the distributive regime where a rising burden raises output and shortens the refill is reachable only with a declared vasodilatory reader, which no migrated family declares; it is recorded as FUTURE_RESEARCH_DEBT (FACULTY DECISION 6)

- Contradicciones dentro del alcance: ninguna. Pasa: sí.
<!-- /generado:no_regresion -->

## 9. Prueba de reversión

<!-- generado:prueba -->
- Archivos revertidos a los de P2W-1: `clinical_core/decision_pack.py` sí, `clinical_core/integration.py` sí, `clinical_core/lactate_slice.py` sí, `clinical_core/provenance.py` sí.
- Archivos comunes fijados por hash: 133, intactos sí.
- Digest de congelado de P2W-1 sobre su árbol: sí; sha de su registro `1ad221db80ed989b…`.
<!-- /generado:prueba -->

## 10. Criterios y veredicto

**Aviso de alcance (revisión adversarial).** La regla congelada de abajo devuelve
`PHASE2_DECLARED_PROPERTIES_CLOSED` con 9 de 9. La revisión mostró dos cosas que la corrigen, y las confirmé con mis
propias sondas:

1. **El criterio 3 no vale sobre todo el dominio declarado.** `step` llama a `_vascular_tone` sólo si la ganancia de
   compensación es mayor que 0 o el lector distributivo está declarado, y **tanto** la guardia de segundo escritor de
   T de P2J-2 **como** la frontera por minuto de P2X-1 viven dentro de esa función. El perfil comprometido **GI tiene
   g = 0 y lector UNSET**: con un escritor del canal T —hoy inexistente— el tono cae 1,0 → 0,1 y el **recorte** fija
   el valor. Y la frontera es inclusiva, así que un objetivo exactamente en 0,1 se acepta y el viaje de ida y vuelta
   del canal deja un recorte de 2,8e-17 **en un minuto aceptado**, contra lo que afirma X8.
2. **Tres de los nueve criterios no pueden fallar:** `contradictions()`, `debt_classification()` y `supersession()`
   derivan su `pass` de listas que construyen vacías o de prosa no vacía, así que los criterios 7 (en su mitad), 8 y 9
   no son evidencia ejecutable. Y la regla del veredicto no lee la prueba de reversión de §9.

**Veredicto operativo:
`PHASE2_DECLARED_PROPERTIES_NOT_CLOSED — el criterio 3 no vale con la respuesta de tono apagada, y la frontera
inclusiva deja un recorte de redondeo en un minuto aceptado`**
(`P2X1_FROZEN_VERDICT_SUPERSEDED_BY_ITS_REVIEW`, el mismo patrón que P2S-3). No se ejecuta la auditoría final de
salida y **no** se hace el congelado final de la Fase 2. Los 14 hallazgos, con lo que la revisión no pudo romper,
quedan en TD-127 y en §72 de `docs/PHASE2_SHADOW_CORE.md`, y los diez están fijados en pruebas independientes.

<!-- generado:veredicto -->
- sí — 1. b < b0 is explicit and coherent: the factor rises to exactly 1 + k b0 as the arrival vasodilation resolves, and it is declared as recovery, not as a vasopressor signal (X1-X4, the derivation)
- sí — 2. no negative burden: the state, the arrival anchor and a writer's minute all refuse it, and the contract says it is not vasoconstriction (X5)
- sí — 3. the upper and lower reachable domains fail closed instead of letting the channel's clamp shape physiology (X6, X7, X8)
- sí — 4. the contraction guard covers the distributive factor, derived from the common equations, and holds for every accepted witness (X9, X10, the derivation)
- sí — 5. no pressure-driven family vasodilation loop exists, and the writer contract forbids one (X15)
- sí — 6. every prior family remains exact by default, and the predecessor's behaviour is reproduced with the one declared supersession (X11, X12, X13, X14)
- sí — 7. TD-120 is formally superseded without rewriting history (the supersession record)
- sí — 8. the Phase-2 debt classes are explicit, and no item is a blocker merely because it is UNSET
- sí — 9. no known causal contradiction remains inside the certified Phase-2 scope

**Veredicto: PHASE2_DECLARED_PROPERTIES_CLOSED**
<!-- /generado:veredicto -->

## 11. Qué NO hace este paquete

- No implementa maldistribución, heterogeneidad de extracción, ni un modelo distributivo de relleno capilar o de
  lactato: la docencia lo clasificó `FUTURE_RESEARCH_DEBT` (decisión 6).
- No implementa nada específico de la anafilaxia (fuga de plasma sin glóbulos rojos, vía aérea alta, blanco
  cronotrópico farmacológico, cinética de epinefrina, regiones de parámetros): decisión 7, trabajo posterior.
- No abre presión → tono: `PRESSURE_DRIVEN_FAMILY_VASODILATION = DEFERRED / NOT_AUTHORIZED` (decisión 5).
- No elige ninguna magnitud clínica, ni cota máxima de carga, ni parámetro de tono inferior, ni suelo específico de
  enfermedad, ni factor de seguridad.
- No integra nada en tiempo de ejecución, no cambia lo que ve el residente y no inicia la Fase 3.
