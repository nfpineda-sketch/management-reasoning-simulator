# P2W-1 · Composición mínima del tono distributivo común

Cambio común, en sombra. Rama `phase-2-clinical-core-shadow`; base `cff2fb2` (P2V-1 aceptado y cerrado:
`COMMON_SYSTEMIC_STRESS_ARCHITECTURE_READY`; P2W-0 aceptado: clasificación B,
`MINIMUM_COMMON_VASODILATORY_AUXILIARY_REQUIRED`, compuerta PASS).

P2W-0 mostró que el canal T de P2J-2 tiene hoy un único escritor común —la respuesta de tono por déficit de
oxígeno— y que ese escritor es *buscador de objetivo*: un delta de familia sobre T es transitorio por construcción y
la guardia lo rechaza mientras la respuesta está activa. Falta, entonces, no un segundo escritor sino la **entrada
común** que una enfermedad distributiva aporta: la pérdida primaria de tono vascular. Este paquete añade esa entrada
y su único lector, y nada más.

- **Cambio común mínimo** (`state.py`, `provenance.py`, `derived.py`, `integration.py`), probado contra `cff2fb2`:
  - `AuxiliaryState.vasodilatory_burden` (finita, 0 o más, 0 por defecto, sin cota superior) y
    `Anchors.arrival_vasodilatory_burden` (el estado latente de llegada, 0 por defecto): una entrada auxiliar común,
    nunca un canal canónico V/T/P/R/L/G/W/D/N;
  - `provenance.VasodilationChange`: la interfaz del escritor, aditiva como un `DistressChange` o un
    `SystemicStressChange`; ninguna familia la implementa aquí;
  - `CoreProfile.vasodilatory_burden_to_tone_gain`: el único lector, UNSET (`None`) por defecto. Multiplica el
    objetivo de tono común por `(1 + k·b₀) / (1 + k·b)`, normalizado en la llegada, de modo que el objetivo es
    exactamente 1 en la llegada para cualquier carga autorada.
- **Composición, no un segundo escritor:** el núcleo sigue siendo el único que escribe T. La pregunta que P2J-2 dejó
  abierta («cómo componen dos escritores de T») se responde aquí sin abrirlo: las dos causas —la compensación por
  déficit y la vasodilatación de la enfermedad— entran en el *mismo* objetivo, de forma multiplicativa, cada una con
  su propia ganancia.
- **Fuera de alcance, por decisión:** no se migra la anafilaxia, no hay modelo de epinefrina, no se calibra ninguna
  magnitud clínica de tono, la presión no entra en el camino del tono, el estrés sistémico de P2V-1 no gana un lector
  vascular y no se toca la conciencia.
- **Análisis:** `clinical_core/distributive_tone.py`, congelado antes de la única evaluación. **Registro:**
  `docs/revision/P2W1_distributive_tone.json`. Este documento se genera desde el registro
  (`clinical_core/distributive_tone_report.py`); el texto fuera de los marcadores es la narrativa.

## 1. Decisiones docentes que rigen

<!-- generado:decisiones -->
- **arrival:** a latent FAMILY_CANDIDATE / CASE MAPPING arrival state constrained by independent authored evidence (warm or flushed peripheries with a low pressure, a filled refill, preserved or raised flow); never inverted from the MAP residual
- **classification:** B, MINIMUM_COMMON_VASODILATORY_AUXILIARY_REQUIRED (P2W-0, gate PASS)
- **composition:** multiplicative and normalized at arrival: target = (1 + g s) / (1 + g s0) x (1 + k b0) / (1 + k b). The two causes coexist without double counting: the compensation answers the oxygen deficit only, the burden is written by a family only
- **guard:** a burden large enough to take the target below T's guard parks T at 0.1 with the clamp recorded (CHANNEL_BOUNDS, 'guard only'), as any channel does: no clinical ceiling is chosen
- **magnitudes:** every magnitude UNSET: no distributive gain, no anaphylaxis or sepsis tone loss, no epinephrine effect, no pressure -> tone gain; deficit_to_tone_gain stays PROVISIONAL (0.5 is a carried structural point, not an approved value)
- **owner:** the core stays the T channel's only writer (integration._vascular_tone); P2J-2's refusal of a second writer is not relaxed, and no family delta on T is introduced
- **reader:** vasodilatory_burden_to_tone_gain, UNSET (None) by default; with it UNSET the target is P2J-2's exactly and a vasodilation change is refused
- **representation:** the primary loss of vascular tone a disease process causes: an auxiliary common input, never a new canonical V/T/P/R/L/G/W/D/N channel
- **residuals:** a common causal signal, never an observable residual fit: no MAP residual is inverted into a burden
- **scope:** one new common auxiliary input (vasodilatory_burden) and its one reader of the common tone target; no anaphylaxis migration, no epinephrine, no clinical tone calibration, no pressure -> tone, no systemic-stress vascular reader, no consciousness work
- **timing:** P2J-2's explicit one-minute lag, unchanged; the burden is a state written by a family, so no pressure -> tone path and no same-step loop is introduced

- Representa: the primary loss of vascular tone of a disease process: anaphylactic or septic vasodilation, a vasodilator drug, and in the other direction a vasopressor that opposes it.
- No representa: the compensatory tone response (that answers the oxygen deficit), T itself, the circulating volume, the pump, the oxygen deficit, D, the baroreflex, the systemic stress, the respiratory distress, a MAP residual.
- Estado: aux.vasodilatory_burden: finite, at or above 0, 0 none, no upper bound (the factor stays positive at any burden; T's own guard holds the channel).
- Llegada: Anchors.arrival_vasodilatory_burden: a case / family latent arrival value, 0 by default; refused other than 0 unless the reader is declared.
- Escritor: Contribution.vasodilation: provenance.VasodilationChange(amount, source, minute, description); amounts add to the value the minute starts with; a minute that would take it materially below 0 is refused; refused while the reader is UNSET.
- Cinética del núcleo: none: the integration sums the minute's declared changes only (source core_coupling:vasodilatory_burden); no decay, no coupling, no derivation from any other state.
- Lector: tone_target *= (1 + k b0) / (1 + k b): a factor at or below 1, 1 exactly at arrival, decreasing in the burden, multiplying the compensatory factor instead of joining it.
- Efecto: T falls -> afterload falls (output and delivery rise) and pressure_rel = output x T falls: the distributive signature (low pressure at preserved or raised flow), through the paths P2J-1 and P2J-2 already certified.
- Observable: no observable reads the burden; the warm or flushed periphery, the refill and the skin findings stay authored evidence.
<!-- /generado:decisiones -->

## 2. El camino del tono antes y después del cambio

Quién lee y quién escribe el canal T, dónde entra el factor nuevo y en qué orden se componen los factores del
objetivo. La auditoría se hace sobre el código, no sobre su descripción.

<!-- generado:arquitectura -->
- Lectores del canal T: _perfusion; escritores: _vascular_tone (el núcleo sigue siendo el único).
- La guardia de P2J-2 contra un segundo escritor de T sigue intacta: sí.
- Lectores de la carga en `derived.py`: tone_target; del ancla: arrival_state, tone_target; de la ganancia: __post_init__, arrival_state, tone_target.
- Lectores en `integration.py`: _check_conservation, _vasodilation_after.
- `beta_blockade` se lee en: arrival_layers, arrival_sympathetic_drive, derive, heart_rate_decomposition, sympathetic_increment, unconstrained_increment — ni el tono ni la presión.

Factores del objetivo de tono, en el orden en que el código los compone:

1. `(1.0 + gain * acute_deficit_signal(state, anchors, profile)) / (1.0 + gain * arrival_tone_signal(anchors, profile))`
2. `if tone_loss is not None: *= (1.0 + tone_loss * anchors.arrival_vasodilatory_burden) / (1.0 + tone_loss * state.aux.vasodilatory_burden)`
3. `return target`

- Antes de P2W-1: `return (1.0 + gain * acute_deficit_signal(state, anchors, profile)) / (1.0 + gain * arrival_tone_signal(anchors, profile))`.
- Composición: tone_target = (1 + g s) / (1 + g s0) x (1 + k b0) / (1 + k b); pressure_rel = output x T; afterload = 1 / (1 + a (T - 1)).
- Punto de inserción: derived.tone_target, as a factor on the compensatory ratio, and integration.step's tone call, which now also runs for a declared vasodilatory reader.
- Pasa: sí.
<!-- /generado:arquitectura -->

## 3. Qué representa la carga vasodilatoria, y qué rechaza

<!-- generado:representacion -->
- Campos nuevos: `Anchors` → ['arrival_vasodilatory_burden']; `AuxiliaryState` → ['vasodilatory_burden']; `Contribution` → ['vasodilation']; `CoreProfile` → ['vasodilatory_burden_to_tone_gain']; `MinuteRecord` → ['vasodilation'].
- Interfaz del escritor: provenance.VasodilationChange(amount, source, minute, description), campo `vasodilation`, con la misma forma que provenance.DistressChange (P2T-1) (sí).
- Rastro aditivo de dos escritores: 0,00 → 0,35 → 0,70 → 0,95 → 0,95 → 0,95; cambios por minuto [2, 2, 1, 0, 0]; fuente core_coupling:vasodilatory_burden.
- Rastro con una reversión declarada: 0,00 → 0,50 → 1,00 → 0,75 → 0,50 → 0,50.
- Estado por defecto 0,00; sin cota superior sí; escritores de familia: ninguno.

Rechazos:

- amount_boolean: sí
- amount_infinite: sí
- amount_nan: sí
- amount_without_description: sí
- amount_without_source: sí
- arrival_without_reader: sí
- boolean_arrival: sí
- change_below_zero: sí
- change_without_reader: sí
- family_delta_on_T: sí
- foreign_change_type: sí
- gain_boolean: sí
- gain_nan: sí
- gain_negative: sí
- gain_zero: sí
- infinite_arrival: sí
- infinite_state: sí
- nan_state: sí
- negative_arrival: sí
- negative_state: sí

- Pasa: sí.
<!-- /generado:representacion -->

## 4. El único lector, desactivado por defecto

Con la ganancia UNSET el objetivo de tono es exactamente el de P2J-2. Declarada, el factor de dilatación es
`(1 + k·b₀)/(1 + k·b)`: exactamente 1 en la llegada y decreciente en la carga.

**Alcance real de la tabla de abajo (revisión adversarial):** la rejilla corre con carga de llegada 0, así que
«nunca por encima de 1» es la rama `b ≥ b₀`. En la rama de resolución (`b < b₀`, que la semántica admite: «en la otra
dirección, un vasopresor que la opone») el factor sube por encima de 1 hasta exactamente `1 + k·b₀`, alcanzado en
`b = 0`. Esa rama no la visita ninguna sonda congelada, y con ella la guarda de ganancia de `_vascular_tone` (que
compara sólo `1 + g` con la cota de T) y la cota de contracción `g·a < 1` quedan cortas: la cota efectiva del lazo es
`(1 + k·b₀)·g·a`. Nada de esto corre hoy —toda ganancia está UNSET— y las dos decisiones son docentes. Queda fijado
en pruebas independientes y en TD-126 (punto 9).

<!-- generado:lector -->
- Campo nuevo del perfil: ['vasodilatory_burden_to_tone_gain']; UNSET por defecto sí.
- UNSET en todos los perfiles comprometidos: acs sí, asthma sí, edema sí, gi sí, opioid_35m sí, opioid_67f sí, pe sí.
- Declararlo no declara ningún otro lector: sí.

| Carga | Objetivo | Factor |
|---|---|---|
| 0.0 | 1,000000 | 1,000000 |
| 0.25 | 0,800000 | 0,800000 |
| 0.5 | 0,666667 | 0,666667 |
| 1.0 | 0,500000 | 0,500000 |

- El factor es exactamente 1 / (1 + k·b): sí; nunca por encima de 1: sí; otra ganancia da su propio factor: sí.
- Escritores del canal T: _vascular_tone.
- Registro de parámetros: provisional. UNSET (P2W-1): tone loss per unit of the common vasodilatory burden (a primary distributive loss of vascular tone), as the factor (1 + k b0) / (1 + k b) on the common tone target, normalized at arrival; None by default (no reader); it reads no pressure, deficit, D, baroreflex or systemic stress and is never solved from an observed MAP; SYNTHETIC_ONLY in probes; not approved
- Pasa: sí.
<!-- /generado:lector -->

## 5. Las catorce sondas (V1–V14)

<!-- generado:sondas -->
| Sonda | Qué exige | Pasa |
|---|---|---|
| V1 | no distributive signal: exactly the current behaviour (and a change is refused with the reader UNSET) | sí |
| V2 | more distributive tone loss lowers the effective tone, by its own gain | sí |
| V3 | more common compensation raises the effective tone at a deficit above arrival's | sí |
| V4 | both active: the compensation partially opposes the vasodilation without erasing it | sí |
| V5 | a severe vasodilation stays dominant; T's guard holds the channel with the clamp recorded | sí |
| V6 | a distributive signal alone alters no other channel or auxiliary state directly | sí |
| V7 | GI exact with the distributive signal absent | sí |
| V8 | ACS exact | sí |
| V9 | PE exact | sí |
| V10 | the pulmonary oedema exact | sí |
| V11 | the systemic stress affects the HR only, not the tone | sí |
| V12 | beta-blockade does not change the tone | sí |
| V13 | arrival exactness preserved at any arrival burden | sí |
| V14 | no recursion and no unstable same-step MAP / T loop | sí |

- V2: sobre la rejilla [0.0, 0.25, 0.5, 1.0] el objetivo va 1,0000 → 0,8000 → 0,6667 → 0,5000 y la PAM a ese tono 78,67 → 66,95 → 58,27 → 46,27.
- V3: con la carga fija, por ganancia de compensación: g 0.0 → 0,6667/0,6667/0,6667; g 0.5 → 0,6667/0,7420/0,7984; g 1.0 → 0,6667/0,8075/0,9130 (demandas 1.0, 1.4, 2.0); en el déficit de llegada el objetivo es el factor de dilatación solo, igual para toda ganancia: sí.
- V4: dilatación sola 0,6667, cota de la compensación 1,3953, objetivo máximo posible 0,9302; opone sí, nunca borra sí, sigue bajo la llegada sí.
- V5: con carga 50 el objetivo es 0,019608; T queda en la guarda 0,10 con el recorte registrado, PAM 10,78 y gasto 1,3699 (flujo conservado).
<!-- /generado:sondas -->

## 6. La firma distributiva y lo que la verdad autoral dice

Presión baja con flujo conservado y relleno no alargado: la firma que distingue el choque distributivo del
hipovolémico. Las cifras de los dos casos de anafilaxia son verdad autoral; la evidencia independiente de cada uno es
lo único que podría constreñir una región de carga de llegada, y ninguna se declara aquí.

**Qué NO compara esta sección (revisión adversarial):** el patrón se calcula contra la propia fila de carga 0 del
núcleo, no contra la verdad autoral. En dirección de presión y flujo coinciden, pero no en todo: el relleno del
núcleo se *acorta* al subir la carga (2,00 → 1,29 s) mientras los dos casos autorales llevan 3 y 4 s, y una carga pura
*baja* el lactato (mejora la entrega) mientras los casos llevan 3,4 y 4,6. El núcleo no representa maldistribución ni
defecto de extracción: queda como deuda nombrada en TD-126 (punto 9), no como un ajuste.

<!-- generado:firma -->
| Carga | T | PAM | Gasto | Entrega | Relleno |
|---|---|---|---|---|---|
| 0.0 | 1,0000 | 90,00 | 1,0000 | 1,0000 | 2,00 |
| 0.25 | 0,8000 | 76,60 | 1,0638 | 1,0638 | 1,74 |
| 0.5 | 0,6667 | 66,67 | 1,1111 | 1,1111 | 1,56 |
| 1.0 | 0,5000 | 52,94 | 1,1765 | 1,1765 | 1,29 |

- Patrón: la presión baja sí, el flujo se conserva o sube sí, el relleno no se alarga sí.

- **anaphylaxis_29f:** PA 84.0/46.0, FC 126.0 (Sinus tachycardia), SpO2 91.0 %, FR 28.0, lactato 3.4, relleno 3.0 s, extremidades Warm, piel flushed; vía aérea: «Increased effort with widespread expiratory wheeze and audible inspiratory stridor.»; edema: periorbital and lip swelling with widespread urticarial wheals; cardíaco: «Rapid regular pulse; the peripheries are warm and well filled.»; acciones autorales: epinephrine_im, fluid, oxygen. Evidencia independiente: warm and well filled peripheries with a low pressure; flushing and urticaria; angioedema minutes after an exposure; lactate 3.4 with preserved flow. Estado: FAMILY_CANDIDATE / REGION UNSET; carga de llegada UNSET.
- **anaphylaxis_63m_betablocked:** PA 76.0/42.0, FC 64.0 (AF), SpO2 89.0 %, FR 26.0, lactato 4.6, relleno 4.0 s, extremidades Warm, piel flushed; vía aérea: «Increased effort with widespread wheeze; no stridor heard.»; edema: flushing with scattered wheals and a sting site; cardíaco: «Irregular pulse at a rate that does not rise with the low pressure; peripheries warm.»; acciones autorales: epinephrine_im, glucagon, fluid. Evidencia independiente: warm peripheries with a low pressure; flushing and wheals after a sting; lactate 4.6 with preserved flow; a rate that does not rise with the pressure (beta blockade, an HR matter). Estado: FAMILY_CANDIDATE / REGION UNSET (the HR limitation is beta-blockade and AF, not tone); carga de llegada UNSET.

- Legado (clasificado, nunca ajustado): DISEASE_SPECIFIC_BP_AND_HR_EQUATION: the legacy family moves SBP and HR directly from its own severity, which is exactly what the common core must not reproduce; P2W-1 adds a cause (the burden) and lets the certified pressure path produce the pressure; SBP por severidad 40.0, FC por severidad 30.0, progresión 0.03/min.
- Lecturas cerradas que ya leían este patrón: collapse_architecture: P2M-2 reads the distributive pattern as T falling with flow kept or raised (its probe sets T by hand for want of a writer); consciousness_audit: a low tone gives a low MAP with preserved delivery: the MAP path is distinct from the deficit.
- SYNTHETIC burden and gain against the authored truth; no case is mapped, no arrival value is calibrated and nothing is approved. Pasa: sí.
<!-- /generado:firma -->

## 7. Magnitudes: todas UNSET

Ninguna cifra clínica se elige en este paquete. Los valores de las sondas son sintéticos y sólo sirven para probar
estructura.

<!-- generado:parametros -->
- **anaphylaxis_tone_loss:** UNSET and not approved (no family writer exists)
- **arrival_vasodilatory_burden:** UNSET (0.0 in every committed arrival mapping): no case carries an arrival burden
- **deficit_to_tone_gain:** PROVISIONAL and unchanged: 0.5 in the five committed profiles with the response on is a carried structural point (baroreflex.TONE_GAINS[1]), 0 in GI; the faculty sets it
- **epinephrine_effect:** UNSET and not approved (no treatment writer exists)
- **pressure_to_tone_gain:** UNSET and out of scope: PRESSURE_TO_TONE_NOT_REQUIRED_FOR_DISTRIBUTIVE_COMPOSITION (P2W-0), still open for ACS and PE
- **sepsis_tone_loss:** UNSET and not approved
- **upper_bound:** UNSET by decision: the burden has no ceiling (0 is none); T's own guard holds the channel
- **vasodilatory_burden_to_tone_gain:** UNSET (None): no vasodilatory reader is declared in any committed profile; the probe gains here are SYNTHETIC_ONLY
- **writer_rates:** UNSET: no family writer exists, so no rate of dilation or of its reversal is declared

- En el registro de parámetros sí, estado provisional; entrada candidata fuera del registro de parámetros de caso sí.
- Ganancias comprometidas: acs None, asthma None, edema None, gi None, opioid_35m None, opioid_67f None, pe None.
- Carga de llegada comprometida: acs 0,00, asthma 0,00, edema 0,00, gi 0,00, opioid_35m 0,00, opioid_67f 0,00, pe 0,00.
- Compensación comprometida (sin cambio): acs 0,50, asthma 0,50, edema 0,50, gi 0,00, opioid_35m 0,50, opioid_67f 0,50, pe 0,50.
- Valores sintéticos de las sondas (SYNTHETIC_ONLY): burden_grid = [0.0, 0.25, 0.5, 1.0], burden_step = 0.25, compensation_gains = [0.0, 0.5, 1.0], demands = [1.0, 1.4, 2.0], other_tone_gain = 0.4, probe_burden = 0.5, severe_burden = 50.0, tone_gain = 1.0.
- Pasa: sí.
<!-- /generado:parametros -->

## 8. Deudas que se llevan

<!-- generado:deudas -->
- **CONSCIOUSNESS_INTEGRATION_DEBT** (de P2L-2 / P2U-1): CARRIED. the consciousness ladder reads SpO2 only; the low-MAP path of distributive shock is diagnostic in the closed audits and is not wired here.
- **MULTI_FAMILY_COMMON_HR_GAP** (de P2N-2 / P2Q-2 / P2U-1): CARRIED, NOT PATCHED. the arrival HR gaps of the ACS, PE and opioid cases are untouched; P2V-1's systemic stress is the common input for the non-respiratory part and its magnitude stays UNSET.
- **PRESSURE_TO_TONE_COMPENSATION_MISSING** (de P2N-2 / P2Q-2 (TD-118 point 4)): CARRIED, NOT REQUIRED HERE. the compensatory response reads the oxygen deficit only; a pressure-driven tone compensation would need a new clinical gain, a reference pressure and an ordering decision, so P2W-0 classified it PRESSURE_TO_TONE_NOT_REQUIRED_FOR_DISTRIBUTIVE_COMPOSITION and it stays open for ACS and PE.
- **SIDED_PRELOAD_COMMON_STATE_DEFERRED** (de P2Q-2 (TD-118 point 2)): CARRIED. the core has no sided preload; the distributive composition needs none.
- **SYSTEMIC_STRESS_MAGNITUDES_UNSET** (de P2V-1 (TD-125)): CARRIED. the stress gain and every arrival region stay UNSET; P2W-1 adds no vascular reader of the stress.

- La presión no entra en el camino del tono: sí.
- Sin escritor de familia de la carga: sí.
- Estrés sistémico UNSET en todo perfil comprometido: sí.
- Compensación sin cambio: acs 0,50, asthma 0,50, edema 0,50, gi 0,00, opioid_35m 0,50, opioid_67f 0,50, pe 0,50.
- Pasa: sí.
<!-- /generado:deudas -->

## 9. No regresión de lo cerrado

<!-- generado:no_regresion -->
- Registro de P2V-1 reproducido sobre su árbol: sí (anida P2U-1, P2T-5, P2T-3, P2T-1A, P2T-1, P2S-3, P2S-2 y, por ellos, opioides, asma, TEP, edema, SCA y GI); intacto sí; su veredicto COMMON_SYSTEMIC_STRESS_ARCHITECTURE_READY.
- Carga de llegada 0 en los perfiles comprometidos: sí.
- Tuplas de registro: DOWNSTREAM_REPORTS sí, PACK_DIGEST_EXCLUDED sí.
- Pasa: sí.
<!-- /generado:no_regresion -->

## 10. Prueba de reversión

Cada archivo del núcleo que P2W-1 toca se reconstruye byte a byte como lo dejó P2V-1, y con esa vista corren las
guardas de los paquetes cerrados: si la composición cambiara de verdad, esas guardas fallarían.

<!-- generado:prueba -->
- Archivos revertidos a los de P2V-1: `clinical_core/decision_pack.py` sí, `clinical_core/derived.py` sí, `clinical_core/integration.py` sí, `clinical_core/lactate_slice.py` sí, `clinical_core/provenance.py` sí, `clinical_core/state.py` sí.
- Archivos comunes fijados por hash: 129, intactos sí.
- Vista de P2V-1: digest sí, su prueba sí, registro sí.
<!-- /generado:prueba -->

## 11. Criterios y veredicto

<!-- generado:veredicto -->
- sí — the architecture is minimal and declared: one auxiliary field, one arrival anchor, one writer record, one gain, with their refusals, and the core still the T channel's only writer (representation, reader audit, audit)
- sí — the composition is monotone in both causes: more burden never raises the tone, more compensation never lowers it at a deficit above arrival's (V2, V3)
- sí — the two causes coexist without double counting: the compensation opposes the vasodilation partially and never erases it, and a severe vasodilation stays dominant (V4, V5)
- sí — the distributive signal alters no other channel or auxiliary state directly, and neither the systemic stress nor the beta-blockade reaches the tone (V6, V11, V12)
- sí — arrival exactness and the explicit lag are preserved: the arrival tone is 1 at any arrival burden and there is no same-step MAP / tone loop (V13, V14)
- sí — every magnitude stays UNSET and no observable is inverted into a burden (the parameter state, the signature)
- sí — nothing prior changes by default: with the reader UNSET every prior reading is exact and the committed families are untouched (V1, V7-V10)
- sí — P2V-1's record reproduces on its tree and every other common file is P2V-1's (the non-regression, the proof)

**Veredicto: COMMON_DISTRIBUTIVE_TONE_COMPOSITION_READY**
<!-- /generado:veredicto -->

## 12. Qué queda abierto

- La **magnitud** de `vasodilatory_burden_to_tone_gain`: UNSET, decisión docente. Ninguna familia la declara.
- Los **valores de llegada por caso**: UNSET. Se llevan como región `FAMILY_CANDIDATE` constreñida por evidencia
  autoral independiente (urticaria, angioedema, exposición, estridor, broncoespasmo, la firma de presión y flujo),
  nunca invertida desde el residual de presión.
- La **cinética**: sin escritor de familia no hay tasa de aparición ni de resolución, y el núcleo no añade ninguna.
- La **migración de la anafilaxia**, la **epinefrina** y la **conciencia** siguen fuera de alcance, cada una en su
  propio paquete.
- Cuatro **decisiones que la revisión adversarial dejó abiertas**, ninguna de la IA: (a) qué debe hacer la composición
  cuando `b < b₀`, y si el canal admite dirección vasopresora; (b) si la guarda de `_vascular_tone` y la cota de
  contracción deben incluir el factor de dilatación; (c) si un escritor de familia puede leer la presión (hoy nada lo
  impide, y la cinética está UNSET); (d) la deuda de maldistribución / extracción y la descripción del relleno
  autoral.
- La **identificabilidad**: fijadas `k` y `b₀`, la carga se recupera exactamente del tono —y por tanto de la PAM y el
  flujo—. En la llegada no es identificable (el objetivo es 1 para cualquier `b₀`); el riesgo empieza en el minuto
  siguiente, justo donde P2W-2 fijaría una región. Exigencia que queda escrita: la región de llegada se constriñe con
  evidencia que no sea la presión.
