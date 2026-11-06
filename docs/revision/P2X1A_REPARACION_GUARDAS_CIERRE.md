# P2X-1A · Reparación de las guardas del cierre de la Fase 2

Cambio común, en sombra. Rama `phase-2-clinical-core-shadow`; base `e0e520d` (P2X-1 aceptado, con su veredicto
operativo corregido por su propia revisión adversarial: **`PHASE2_DECLARED_PROPERTIES_NOT_CLOSED`**).

P2X-1 no es un paquete fallido: su derivación analítica, sus guardas y su contrato siguen en pie, y este paquete no
los reabre. Lo que su revisión demostró —y yo reproduje con mis propias sondas— fueron **dos bloqueos reales del
cierre** y un conjunto de criterios que no podían fallar. P2X-1A repara exactamente eso: guardas, falsabilidad y
trazabilidad. No añade fisiología clínica, no elige ninguna magnitud, no integra nada en tiempo de ejecución.

1. **La propiedad del canal T era condicional.** `step` llamaba a `_vascular_tone` sólo si la ganancia de
   compensación era mayor que 0 o el lector distributivo estaba declarado, y el rechazo de un segundo escritor de T
   vivía **dentro** de esa función. El perfil comprometido GI tiene las dos cosas apagadas: un escritor clínico de T
   llegaba al canal y su guarda —una cota de seguridad— fijaba el valor, con recortes registrados.
   `integration._tone_ownership` corre ahora en todo minuto de todo perfil, antes de reconstruir el canal.
2. **El dominio era inclusivo y el minuto aceptado podía llevar recorte.** La admisibilidad por minuto aceptaba un
   objetivo exactamente sobre la guarda de T, y la reconstrucción del canal dejaba un recorte de 2,8e-17 dentro de un
   minuto aceptado. El dominio soportado es ahora el intervalo **abierto**, y se comprueba el valor que el canal va a
   guardar de verdad, sin épsilon, margen ni tolerancia. La admisibilidad del objetivo mayor también es estricta, y
   ya no depende de que el lector esté declarado.
3. **Tres criterios no podían fallar y un resultado se calculaba sin leerse.** `contradictions`,
   `debt_classification` y `supersession` derivaban su veredicto de listas que construían vacías o de prosa no vacía,
   y la regla de disposición nunca leía la prueba de reversión. Los cuatro son ejecutables y falsables aquí.
4. **El escaneo del contrato del escritor era evadible.** Se le escapaban el constructor cualificado, la función
   auxiliar, el acceso posicional y los observables del mismo lazo fuera de su lista, y leía sólo los módulos del
   paquete. Ahora sigue alias, nombres cualificados y auxiliares del propio módulo, cubre todos los observables del
   lazo que el núcleo deriva, y lee el código del repositorio.

- **Cambio común mínimo** (`integration.py`, `provenance.py`; más las dos tuplas de registro), probado contra
  `e0e520d`:
  - `integration._tone_ownership`: la propiedad del canal T, incondicional, llamada desde `step`;
  - en `_vascular_tone`: frontera estricta por minuto sobre el objetivo **y** sobre la reconstrucción del canal, y
    admisibilidad estricta del objetivo mayor para todo perfil;
  - en `provenance.VasodilationChange`: el contrato publica lo que el escaneo reforzado exige.
- **Análisis:** `clinical_core/closure_guard.py`, congelado antes de la única evaluación. **Registro:**
  `docs/revision/P2X1A_closure_guard.json`. Este documento se genera desde el registro
  (`clinical_core/closure_guard_report.py`); el texto fuera de los marcadores es la narrativa.

## 1. Las decisiones docentes que rigen

<!-- generado:decisiones -->
- **1_unconditional_ownership:** T_CHANNEL_SINGLE_OWNER_INVARIANT_UNCONDITIONAL: the common core is the only owner and writer of Channel.T for the certified Phase-2 architecture; the ownership invariant executes independently of whether the core has a tone response to compute, with no profile-dependent behaviour
- **2_strict_domain:** TONE_DOMAIN_ENDPOINTS = UNRESOLVED_BOUNDARY: the supported tone domain is the open interval T_lo < target < T_hi; the exact endpoints are unresolved boundaries, not accepted interior physiology, and fail closed before the channel clamp - with no epsilon, clinical margin, floating tolerance or alternative floor
- **3_zero_clamp:** ACCEPTED_TONE_MINUTE_HAS_ZERO_CLAMP: no accepted Phase-2 tone update carries a clamp:bounds:T or equivalent clipping; a floating adjustment of 2.8e-17 means the candidate reached the boundary and should have been refused before the channel was rebuilt
- **4_keep_p2x1_analysis:** the accepted P2X-1 analytic results stand: B(b) = (1 + k b0) / (1 + k b), b >= 0, b < b0 is allowed recovery, Bmax = 1 + k b0, and the analytically derived contraction bound; they are reopened only on an actual mathematical error, and this package found none
- **5_no_pressure_driven_writer:** PRESSURE_DRIVEN_FAMILY_VASODILATION_NOT_AUTHORIZED: a future VasodilationChange writer may not depend on the current MAP, pressure_rel, SBP, DBP, T or an equivalent same-loop observable; pressure -> tone stays a separate future common mechanism and is not implemented
- **6_maldistribution:** the distributive CRT, extraction heterogeneity, maldistribution, distributive lactate, plasma leak, upper airway and epinephrine targets stay FUTURE_RESEARCH_DEBT, outside the Phase-2 closure scope
- **7_p2x1_supersession:** P2X1_FROZEN_VERDICT_SUPERSEDED_BY_P2X1A: P2X-1 is not recut; its frozen rule said CLOSED, its review demonstrated two real blockers, its operative verdict became NOT_CLOSED, and P2X-1A repairs those exact blockers with every P2X-1 digest and artifact preserved
- **8_decision_file:** the eight faculty decisions behind P2X-1 and P2X-1A are recorded in the project's authoritative Decision File, using the repository's existing convention
- **scope:** a closure repair package: guards, falsifiability and traceability only. No new clinical physiology, no magnitude, no new canonical state, no runtime integration, no Phase 3
<!-- /generado:decisiones -->

## 2. La interpretación declarada (y abierta a confirmación)

La decisión 1 dice «una familia o cualquier otra contribución». El repositorio ya clasifica a los escritores, y este
paquete usa esa clasificación en vez de inventar otra: rechaza toda fuente **clínica** en todo perfil, y deja a las
sondas sintéticas declaradas escribiendo T como ya escriben V y Hb. Lo que la revisión demostró —un módulo de
enfermedad aceptado en GI— queda cerrado. La lectura amplia retiraría tres sondas de banda y las lecturas cerradas que
las citan: eso es fisiología, y necesita otra autorización.

<!-- generado:interpretacion -->
- **decision:** FACULTY DECISION 1, 'a family or any other contribution must NOT directly write Channel.T'
- **if_the_faculty_wants_the_wider_reading:** bands.PROBES['vasodilation'], bands.PROBES['vasodilation_with_demand'] and bands.HISTORICAL_PROBES['vasodilation_with_preload_loss'] are the only remaining T writers; refusing them retires those probes and the closed readings that cite them, and needs a separate authorization
- **implemented_as:** every clinical source (disease module, treatment, intervention, case) is refused on every profile, unconditionally; a declared synthetic probe (SourceKind.SCRIPTED_EVENT) still writes T, as it still writes V and Hb
- **repository_basis:** integration._check_owned (P2I-2T) and pressure_tone.TONE_RULE / PROBE_MODULES (P2J-1)
- **what_the_review_demonstrated:** a DISEASE_MODULE writer of T accepted on the GI profile: refused now
<!-- /generado:interpretacion -->

## 3. Las guardas reparadas (P2X-1A-1, P2X-1A-2 y P2X-1A-3)

Lo que se añadió son **rechazos**, y uno de ellos cambió de sitio: la propiedad del canal salió de la respuesta y
pasó a `step`. Ninguna lectura aceptada cambia, el delta que el acoplamiento devuelve sigue siendo el mismo, y los
chequeos publicados de P2J-2 y de P2X-1 quedan intactos.

<!-- generado:guardas -->
- Propiedad del canal T: `integration._tone_ownership`, llamada desde `step` sin condición: sí; antes de reconstruir el canal: sí; fuera de la respuesta: sí.
- Qué rechaza: every clinical writer of T (a source whose kind is not SCRIPTED_EVENT).
- Frontera por minuto: `not lower < target < upper or not lower < reconstructed < upper` — estricta: sí; reconstrucción comprobada: sí; excepción: `UnresolvedBoundary`.
- Admisibilidad por parámetros: sí, y sin condicionar al lector: sí.
- Sin épsilon, margen ni tolerancia: sí (literales float distintos de 0 y 1: ninguno).
- Chequeos de P2J-2 intactos: invariante de perfil sí, chequeo de ganancia sí, rechazo de composición sí.
- Resultados de P2X-1 intactos: cota de contracción sí, condicionada al lector sí, forma cerrada sí.
- El recorte sigue siendo la última capa de seguridad: sí; el delta devuelto es `amount`.

Rechazos, por función:
- `_tone_ownership`:
  1. f"minute {minute}: {clinical} write T, whose only clinical o
- `_vascular_tone`:
  1. f"the tone response's largest target 1 + {profile.deficit_to
  2. f"the tone target's largest reachable value {domain['largest
  3. f'minute {minute}: {writers} write T while the vascular-tone
  4. f"minute {minute}: the tone target {target!r} is not inside
  5. f"the tone loop's derived bound with the distributive factor
<!-- /generado:guardas -->

## 4. El contrato del escritor, exigible (P2X-1A-8)

<!-- generado:contrato -->
- Contrato declarado en `provenance.VasodilationChange`: sí; refuerzo de P2X-1A declarado: sí.
- Observables prohibidos (10): crt_s, dbp, delivery_rel, map, mean_arterial_pressure, output_rel, pressure_rel, sbp, sympathetic_drive, T.
- Archivos del repositorio escaneados que construyen el registro: 9.
- Escritores encontrados: `clinical_core/distributive_tone.py:SyntheticVasodilation.contribute`, `clinical_core/distributive_tone.py:representation`, `test_clinical_core_distributive_tone.py:test_the_writer_record_has_the_distress_records_shape_and_its_guards`.
- Infractores: ninguno.
- Entradas permitidas: the writer's own disease-process state, time, a treatment, and authored family mechanisms that do not close the haemodynamic loop.

| Evasión que la revisión de P2X-1 encontró | Rechazada |
|---|---|
| alias | sí |
| attrgetter | sí |
| decorator_injects_the_pressure | sí |
| dict_get | sí |
| getattr_through_a_variable | sí |
| helper_function | sí |
| inheritance | sí |
| method_of_another_class | sí |
| module_level_alias | sí |
| module_level_lambda | sí |
| positional_access | sí |
| qualified_constructor | sí |
| same_loop_observable | sí |
| subscript_access | sí |
| tone_feedback | sí |

- Patrón permitido, aceptado: sí.
<!-- /generado:contrato -->

## 5. Las veintidós sondas (A1–A22)

<!-- generado:sondas -->
| Sonda | Qué exige | Pasa |
|---|---|---|
| A1 | GI, the committed profile with the compensation off and no distributive reader, plus a clinical writer of T: | sí |
| A2 | ACS, where the response does run: the same writer, the same refusal, from the same guard. | sí |
| A3 | Every committed profile: one ownership invariant, one message, no profile-dependent behaviour. | sí |
| A4 | A target exactly on the lower guard is an unresolved boundary, not accepted physiology. | sí |
| A5 | Below the lower guard, refused, with no clinical maximum burden declared anywhere. | sí |
| A6 | A parameter domain whose largest reachable target is exactly the upper guard: refused before execution, now on | sí |
| A7 | Above the upper guard, refused before execution (P2X-1's X6, kept). | sí |
| A8 | An interior target - including one next to the lower guard - runs, and the channel holds exactly it. | sí |
| A9 | The accepted minutes themselves, not the arithmetic of the target: no clamp record of any kind on T, over a | sí |
| A10 | A negative burden stays invalid everywhere: the state, the arrival anchor and a writer's minute (P2X-1's X5). | sí |
| A11 | A burden below the arrival one is still allowed recovery, and the target still rises as it resolves. | sí |
| A12 | The maximum recovery factor is still exactly 1 + k b0. | sí |
| A13 | The contraction guard exercised with an arrival burden above 0, so the distributive factor is really in it: the | sí |
| A14 | The LIVE slope where the distributive factor is not 1: measured on the real equations, at a state whose burden | sí |
| A15 | A combination whose derived bound is not a contraction is refused, with its largest target inside the range. | sí |
| A16 | Each bypass the P2X-1 review found, rejected by the scan; the allowed pattern still accepted. | sí |
| A17 | P2S-3 -> P2T-3: both artifacts on disk, both digests where they were, nothing recut. | sí |
| A18 | P2X-1 -> P2X-1A: the historical artifacts exist, its freeze digest still recomputes to the frozen value on the | sí |
| A19 | The reversion criterion is read, not merely computed: with a protected predecessor source mutated, the | sí |
| A20 | A known debt removed or misclassified makes the readiness rule fail. | sí |
| A21 | Every committed family keeps its default trajectory exactly, by digest, against the predecessor's record. | sí |
| A22 | No clinical magnitude: no new state, no new profile field, no new calibration entry, every value this package | sí |

- A4: con k = 1 y carga de llegada 0, una carga de 9,0 deja el objetivo exactamente en 0,100000, el extremo inferior: rechazado sí con el dominio admisible sí.
- A8: con carga 8,9 el objetivo es 0,101010 y el canal guarda 0,101010; la diferencia de reconstrucción es -1.388e-17 y el minuto aceptado no tiene recortes: sí.
- A9: la carga recorre [0.0, 2.0, 2.0, 2.0, 0.0, 0.0, 0.0] y el tono [1.0, 1.0, 0.333333, 0.310078, 0.310078, 0.930233, 0.991548]; recortes en todos los minutos: [[], [], [], [], [], []].
- A13 k0.25_b2: cota 0,2867 = 0,1911 x 1,5000 (factor dentro de la cota: sí), contracción sí.
- A13 k1_b0.5: cota 0,2867 = 0,1911 x 1,5000 (factor dentro de la cota: sí), contracción sí.
- A13 k1_b1: cota 0,3823 = 0,1911 x 2,0000 (factor dentro de la cota: sí), contracción sí.
- A14 k0.25_b2: factor distributivo 1,5000; pendiente viva {'1.0': 0.177907, '1.5': 0.134523, '2.0': 0.10527}, bajo la cota sí.
- A14 k1_b0.5: factor distributivo 1,5000; pendiente viva {'1.0': 0.177907, '1.5': 0.134523, '2.0': 0.10527}, bajo la cota sí.
- A14 k1_b1: factor distributivo 2,0000; pendiente viva {'1.0': 0.237209, '1.5': 0.179364, '2.0': 0.140361}, bajo la cota sí.
<!-- /generado:sondas -->

## 6. Contradicciones, ahora decididas por sondas (P2X-1A-4)

<!-- generado:contradicciones -->
| Afirmación | Sondas que la deciden | Se sostiene |
|---|---|---|
| below_arrival_recovery_lost | A11:sí, A12:sí | sí |
| clamp_defines_physiology | A8:sí, A9:sí | sí |
| endpoint_accepted_as_interior | A4:sí, A5:sí, A6:sí, A7:sí | sí |
| hidden_point_calibration | A22:sí | sí |
| incompatible_writer_ownership | A1:sí, A2:sí, A3:sí | sí |
| negative_burden_as_vasoconstriction | A10:sí | sí |
| pressure_driven_vasodilation | A16:sí | sí |
| prior_families_change | A21:sí | sí |
| unstable_feedback | A13:sí, A14:sí, A15:sí | sí |

Declarado como prosa, no como búsqueda ejecutada:
- disease_specific_rule_in_the_common_core: the tone equation names no family; read from the source by P2W-1 and P2X-1, not re-derived here
- impossible_ordering: the tone answers the previous minute's signal and the burden is written before it is read (P2J-2's timing probe)
- same_mechanism_double_counted: the compensation reads the oxygen deficit and the burden is written by a family: independent factors, multiplied once (P2W-1's reader audit)
- worse_state_improves_output: the distributive regime where a rising burden raises output is reachable only with a declared reader, which no migrated family declares: FUTURE_RESEARCH_DEBT (FACULTY DECISION 6)

- Contradicciones dentro del alcance: ninguna. Pasa: sí.
<!-- /generado:contradicciones -->

## 7. La deuda consolidada, trazada al registro (P2X-1A-5)

Ninguna entrada es bloqueo por estar UNSET: una magnitud UNSET deja su término inerte, que es el diseño. Lo que sí es
bloqueo es un bloqueo demostrado clasificado como deuda aceptable, y eso lo decide una sonda.

<!-- generado:deuda -->
**ACCEPTABLE_PHASE2_DEBT** (13):

- `COLLAPSE_THRESHOLDS`: TD-109
- `CUMULATIVE_FLOATING_POINT_CANCELLATION`: TD-121
- `DISTRIBUTIVE_TONE_MAGNITUDE`: TD-126
- `FIO2_MAGNITUDE`: TD-123
- `HYPOXAEMIC_FEEDBACK_STABILITY`: TD-117
- `OPIOID_HR_RESIDUAL`: TD-124
- `PHYSICAL_PAO2_BOUNDARY`: TD-123
- `PRESSURE_TO_TONE`: TD-118
- `RESPIRATORY_DISTRESS_CALIBRATION`: TD-121
- `SIDED_PRELOAD_AND_INTERDEPENDENCE`: TD-118
- `STEADY_STATE_W_ARRIVAL_TENSION`: TD-124
- `SYSTEMIC_STRESS_CALIBRATION`: TD-125
- `TONE_DOMAIN_LIMITS`: TD-127

**FUTURE_RESEARCH_DEBT** (5):

- `ADDITIONAL_FAMILY_MIGRATIONS`: TD-126
- `DRUG_KINETICS`: TD-126
- `MALDISTRIBUTION_AND_EXTRACTION`: TD-126
- `PLASMA_LEAK`: TD-126
- `UPPER_AIRWAY`: TD-126

**NEXT_PHASE_INTEGRATION_DEBT** (3):

- `CONSCIOUSNESS_WIRING`: TD-107
- `RESIDENT_VISIBLE_BEHAVIOUR`: TD-127
- `RUNTIME_INTEGRATION`: TD-127

- Clases disjuntas: sí; cada entrada trazada a una fila del registro: sí; cada entrada exigida clasificada: sí.
- Bloqueos demostrados resueltos: P2X1_R_F1_CONDITIONAL_T_OWNERSHIP: sí, P2X1_R_F4_CLAMP_IN_AN_ACCEPTED_MINUTE: sí.
- an UNSET magnitude leaves its term inert, which is the design.
- Bloqueos: ninguno. Pasa: sí.
<!-- /generado:deuda -->

## 8. Supersesiones, verificadas contra los artefactos (P2X-1A-6)

<!-- generado:supersesion -->
- **P2J2_UPPER_ENDPOINT_PROBE_SUPERSEDED_BY_P2X1A** — estado `P2J2_ENDPOINT_PROBE_READING_SUPERSEDED`.
  - Qué pasó: its probe entry point must be run with that gain removed from the grid, which its suite does and this row declares: the grid is part of P2J-2's own frozen digest, so a view that patched it would move that digest, and the digest is what history preservation means here. P2J-2's probe grid includes the gain 2.0, whose largest reachable target is exactly T's upper guard on anchors with no arrival deficit. P2J-2 accepted that reading (its check is 1 + g > upper); FACULTY DECISION 2 makes the endpoint an unresolved boundary, so the combination is refused and that probe row is superseded. Every gain below it is unchanged.
  - historical: `docs/revision/P2J2_TONO_VASCULAR_DINAMICO.md` (sí), `docs/revision/P2J2_vascular_tone.json` (sí); digest de congelado True, sha del registro True.
  - superseding: `docs/revision/P2X1A_REPARACION_GUARDAS_CIERRE.md` (sí), `docs/revision/P2X1A_closure_guard.json` (sí); digest de congelado None, sha del registro None.
  - Historia preservada: the P2J-2 record and digest are not recut; the superseded reading is declared here and its suite reads the grid without the endpoint gain.
- **P2X1_FROZEN_VERDICT_SUPERSEDED_BY_P2X1A** — estado `P2X1_FROZEN_VERDICT_SUPERSEDED_BY_P2X1A`.
  - Qué pasó: P2X-1's frozen rule returned PHASE2_DECLARED_PROPERTIES_CLOSED; its adversarial review demonstrated two real closure blockers - the ownership guard did not run with the tone response off, and the inclusive boundary left a 2.8e-17 clamp inside an accepted minute - so the operative verdict became NOT_CLOSED; P2X-1A repairs those exact blockers.
  - historical: `docs/revision/P2X1_CIERRE_PROPIEDADES_DECLARADAS.md` (sí), `docs/revision/P2X1_tone_domain.json` (sí); digest de congelado True, sha del registro True.
  - superseding: `docs/revision/P2X1A_REPARACION_GUARDAS_CIERRE.md` (sí), `docs/revision/P2X1A_closure_guard.json` (sí); digest de congelado None, sha del registro None.
  - Historia preservada: no P2X-1 source, record or digest is recut or rewritten; the two rows it published - its P2W-1 V5 clamp reading and TD-120 - stand as it published them, and its V5 refusal still holds live.
- **TD120_HISTORICAL_SUPERSESSION_ACCEPTED** — estado `P2S3_FROZEN_VERDICT_SUPERSEDED_BY_P2T3`.
  - Qué pasó: P2S-3's frozen rule returned ASTHMA_SHADOW_MIGRATION_READY; its adversarial review demonstrated a COMMON_DRIVE_GAP and the corrected operative classification was NOT_READY; P2T-1, P2T-2 and P2T-3 closed that blocker and P2T-3 is the authoritative asthma result.
  - historical: `docs/revision/P2S3_ASMA_SOMBRA.md` (sí), `docs/revision/P2S3_asthma_migration.json` (sí); digest de congelado True, sha del registro True.
  - superseding: `docs/revision/P2T3_ASMA_DISTRES_SOMBRA.md` (sí), `docs/revision/P2T3_asthma_distress_migration.json` (sí); digest de congelado True, sha del registro True.
  - Historia preservada: no P2S-3 source, record or digest is recut or rewritten.

- Digest de congelado de P2X-1 recomputado sobre su árbol: sí; registro de P2W-1 intacto: sí.
- Problemas: ninguno. Pasa: sí.
<!-- /generado:supersesion -->

## 9. No regresión y prueba de reversión (P2X-1A-7)

<!-- generado:no_regresion -->
- Registro de P2X-1 reproducido sobre su árbol: sí; intacto: sí; su veredicto congelado: PHASE2_DECLARED_PROPERTIES_CLOSED.
- Archivos revertidos al texto de P2X-1: `clinical_core/decision_pack.py` sí, `clinical_core/integration.py` sí, `clinical_core/lactate_slice.py` sí, `clinical_core/provenance.py` sí.
- Archivos comunes fijados por hash: 135, intactos sí.
- Digest de congelado de P2X-1: sí.
- Trayectorias comprometidas idénticas por digest: sí (9 trayectorias, comparadas contra docs/revision/P2X1_tone_domain.json: X12).
- Tuplas de registro: DOWNSTREAM_REPORTS sí, PACK_DIGEST_EXCLUDED sí.
- Pasa: sí.
<!-- /generado:no_regresion -->

## 10. Criterios y veredicto

<!-- generado:veredicto -->
- sí — 1. the T single-owner invariant is unconditional: every clinical writer of T is refused on every profile, before the channel is rebuilt, whether or not the core has a response to compute
- sí — 2. the supported tone domain is the open interval: both endpoints fail closed, at the parameter level and at the minute, with no epsilon, margin or tolerance
- sí — 3. no accepted tone minute carries a clamp on T, the floating reconstruction included
- sí — 4. where the distributive reader is declared, the contraction guard carries the distributive factor, holds against the live slope with B != 1, and refuses a combination that is not a contraction (with the reader UNSET the derived bound is not checked, as P2X-1 left it and TD-127 declares)
- sí — 5. the pressure-driven vasodilation contract is enforced by a scan that rejects each bypass the P2X-1 review found
- sí — 6. the predecessor and reversion integrity holds, and the readiness rule reads it
- sí — 7. the contradictions check is executable: each row is decided by its probes and can become false
- sí — 8. the debt classification is executable: disjoint classes, every entry traced to the register, no demonstrated blocker classified as acceptable, and a mutation makes it fail
- sí — 9. the supersession check verifies the repository's own artifacts and immutable references
- sí — 10. every prior migrated family keeps its default trajectory exactly
- sí — 11. no new clinical magnitude is selected
- sí — 12. the eight faculty decisions are recorded in the project's Decision File, by classification and by row

**Veredicto: PHASE2_DECLARED_PROPERTIES_CLOSED**
<!-- /generado:veredicto -->

## 11. Qué NO hace este paquete

- No reabre la derivación de P2X-1: `B(b)`, `b ≥ 0`, la recuperación por debajo de la carga de llegada, `Bmax` y la
  cota de contracción derivada siguen como P2X-1 las dejó (decisión 4). No se encontró ningún error matemático.
- No implementa maldistribución, extracción, relleno capilar ni lactato distributivos, ni fuga de plasma, ni vía
  aérea alta, ni blancos de epinefrina (decisión 6).
- No abre presión → tono (decisión 5).
- No elige ninguna magnitud clínica, ni cota máxima de carga, ni parámetro de tono inferior, ni suelo de enfermedad,
  ni épsilon, ni factor de seguridad.
- No re-corta P2X-1, P2W-1, P2S-3 ni P2J-2: declara las supersesiones y verifica que sus digests no se movieron.
- No integra nada en tiempo de ejecución, no cambia lo que ve el residente y no inicia la Fase 3.
