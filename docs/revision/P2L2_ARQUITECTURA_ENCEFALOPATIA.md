# P2L-2 · Arquitectura común de la encefalopatía sistémica

**Rama:** `phase-2-clinical-core-shadow` · **Base:** `d88f125` (P2L-1 cerrado) · **Congelamiento:** `8072279`
(digest `970db00d…`) · **Fecha:** 2026-11-01

Sólo sombra. Un módulo de fisiología candidata (`clinical_core/encephalopathy.py`) que ningún paso del núcleo lee y
que no escribe estado, y su evaluación estructural (`clinical_core/encephalopathy_architecture.py`). No cambia ningún
archivo del núcleo, no elige ninguna cota ni constante de tiempo, no asigna categorías de estado mental, no genera
trayectorias GI y no calibra nada; el colapso sigue apagado. Las secciones marcadas como generadas salen del registro
`docs/revision/P2L2_encephalopathy_architecture.json` (`encephalopathy_architecture_report`).

## Resumen

**Veredicto: `COMMON_CONSCIOUSNESS_ARCHITECTURE_READY`**, con los once criterios calculados desde la evidencia.
Es una arquitectura lista, no una calibración: ninguna cota, constante de tiempo ni categoría tiene valor, y nada se
aprueba.

- **N** queda reservado al estado neurológico primario. Su único lector es `primary_from_state`; nada lo escribe
  salvo el constructor de llegada (N = 0), y ninguna señal sistémica lo lee.
- **Seis señales agudas**, cada una desde una lectura certificada: PAM (no PAS), déficit efectivo / demanda, SpO2,
  pH, PaCO2 (aparte del pH) y glucosa. Sin lactato, D, FC ni nivel de autoría. Sin pulso, la hipoperfusión es máxima.
- **Agregación y composición por máximo:** S = máx(señales); I = máx(N, S, F); nunca suma.
- **La memoria F** (carga de encefalopatía sistémica) es un estado auxiliar del candidato:
  - relaja hacia S, más rápido al subir que al aclararse;
  - es no negativa, nunca supera a S, no lee N ni D y no se deriva de tau_D.
- **N1–N12 pasan** con las razones sintéticas 2, 4 y 8. En particular:
  - N9: S 0,6 frente a una suma de 1,8;
  - N10: al restaurar la fisiología, S = 0 y la memoria queda en 0,898, decreciente;
  - N11: la agresión breve deja menos memoria que la repetida y ésta que la prolongada (0,569 / 0,779 / 0,898);
  - N12: con N y una agresión sistémica, I es el peor de los dos y F no depende de N.
- **Ortogonalidad A–H a las dos ganancias retenidas:**
  - cada patrón es distinto y aislado tal como se declaró;
  - la hipercapnia aguda lee acidemia e hipercapnia a la vez, y el máximo evita contarlas dos veces;
  - una etiqueta de llegada «obnubilado» con fisiología normal lee igual que la referencia: no hay piso.
- **La inversión del bucle del tono** (P2L-1) desaparece: el déficit tiene su propia señal, monótona.
- **Las 17 604 filas de acidemia extrema** se arrastran sin filtrar. Con cualquier mapeo admisible pueden leer
  alteradas por acidemia, por perfusión y por aporte; el máximo no las cuenta tres veces.
- **Generalización:** `COMMON_NEUROLOGIC_ARCHITECTURE_PLAUSIBLE` para las seis familias, sin términos de enfermedad.
  Lo que cada familia aún aporta es el escritor de su señal.
- **Identificabilidad:** todo queda STRUCTURALLY_DEFINED_BUT_CLINICALLY_UNIDENTIFIED; nada es WELL_CONSTRAINED.
- **Trayectorias GI C1–C4:** no se generan, porque no existe ningún mapeo independiente de los casos GI.
- **El núcleo no cambia:** el árbol de P2L-1 (64 archivos) es idéntico byte a byte y el golden es idéntico.
- **Siguiente paso:** no hace falta más calibración numérica antes de probar la generalización
  (`DO_NOT_OVERFIT_GI`). Por necesidad causal se recomienda `COLLAPSE_SAFETY_ARCHITECTURE`: con el colapso apagado,
  las filas sin tratar con pH < 7,00 y PAM 32–46 a los 120 min conservan el pulso, y toda familia de shock necesita
  esa seguridad antes de migrar. Una segunda familia sin shock puede venir después.

## 1. Decisiones de la docencia

<!-- generado:decisiones -->
Decisiones de la docencia (texto congelado, en inglés):

- **aggregation**: systemic_acute_brain_stress = MAX of the six signals; observable = MAX(primary N, acute, memory); no sum, no synergy
- **brief**: P2L-2 common systemic-encephalopathy architecture (2026-11-01): structural; no numeric fit to the GI cases
- **collapse**: not calibrated, not activated
- **d**: D stays the oxygen-delivery debt; never the consciousness memory (it misses isolated hypotension, hypercapnia, hypoglycaemia and primary injury); at most diagnostic
- **identifiability**: STRUCTURALLY_DEFINED BUT_CLINICALLY_UNIDENTIFIED where appropriate; never WELL_CONSTRAINED from synthetic probes
- **map**: MAP, not SBP; the SBP 80 / 65 and SpO2 87 / 80 ladders and the arrival floor retired from candidate physiology, kept LEGACY_REFERENCE_ONLY; no MAP threshold selected
- **memory**: a new auxiliary dynamic state, systemic_encephalopathy_burden, not a canonical channel: reversible accumulated cerebral dysfunction from systemic insults; non-negative; rises with severe systemic brain stress, may persist after it, clears gradually; cannot create N; never alters upstream physiology
- **n**: N is reserved for the primary neurologic state / injury or reserve (structural CNS injury, seizure / postictal, primary encephalopathy, other primary neurologic pathology); shock, hypoperfusion, hypoxaemia, acidemia, hypercapnia and hypoglycaemia are never written into N
- **pharmacologic**: no pharmacologic CNS depression in N and no drug-depression state here: FUTURE_COMMON_SYSTEMIC_OR_PHARMACOLOGIC_MODIFIER
- **signals**: cerebral hypoperfusion (MAP), effective oxygen-delivery deficit, hypoxaemia (SpO2), metabolic acidemia (pH), hypercapnia (PaCO2, apart from pH), hypoglycaemia (glucose); primary N apart; no lactate, no HR
- **thresholds**: no threshold from the GI cases (no authored post-arrival neurologic observation): synthetic normalized inputs or committed common ranges only; STOP before choosing a new number
- **trajectories**: GI consciousness trajectories only if signal mappings exist independently of GI outcomes
<!-- /generado:decisiones -->

## 2. N: estado neurológico primario

<!-- generado:n -->
- **Escritores:** state.py:697 (sólo el constructor de llegada, N = 0).
- **Lectores:** encephalopathy.py:189: el único lector, `primary_from_state`, que lo lee como alteración neurológica primaria; ninguna señal sistémica lo lee ni lo escribe.
- **Archivos revisados:** 65 (búsqueda recursiva congelada de P2L-1).
- **Semántica** (texto congelado, en inglés): PRIMARY_NEUROLOGIC_STATE (faculty, 2026-11-01): static during the encounter, no recovery kinetics; no systemic cause and no pharmacologic depression is written into it; state.py's closed wording ('CNS depression / neurological state') is kept for the closed records and superseded for this candidate
- **Escala:** the common impairment scale [0, 1]: 0 intact, 1 maximal primary impairment; outside it the candidate stops (CoreInvariantError)
- **Dinámica:** static in the encounter (no recovery or healing kinetics)
- **Valores GI:** none: no GI case declares N (the legacy adapter builds N = 0)
- **Redacción cerrada:** state.CHANNEL_DEFINITIONS keeps 'CNS depression / neurological state' and the guard (-10, 10) for the closed records: DOCUMENTED_SEMANTIC_DEBT until runtime integration
<!-- /generado:n -->

## 3. Señales agudas de estrés cerebral sistémico

<!-- generado:senales -->
| Señal | Lectura certificada | Altera | Significado (congelado) |
|---|---|---|---|
| acidemia | pH | por debajo de su cota normal | the current arterial pH of the respiratory closure; any acidemia lowers it, so an acute hypercapnia also carries some; the maximum keeps the two from adding |
| hipoperfusión cerebral | PAM | por debajo de su cota normal | mean arterial pressure as the cerebral-perfusion-pressure proxy (no ICP is modelled; autoregulation enters through the bounds); without a pulse it is maximal by definition (circulatory arrest) |
| hipercapnia | PaCO2 | por encima de su cota normal | the current PaCO2 of the respiratory closure, read apart from pH |
| hipoglucemia | glucosa | por debajo de su cota normal | CoreState.glucose (absolute, mg/dL) |
| hipoxemia | SpO2 | por debajo de su cota normal | arterial oxygenation (derive's SpO2), its own input beside the deficit: the systemic deficit with its extraction reserve misses cerebral hypoxaemia (P2L-1) |
| déficit de aporte de oxígeno | déficit efectivo / demanda | por encima de su cota normal | derived.acute_deficit_signal: the current effective oxygen-delivery deficit over the current demand (0 to 1); no D, no lactate |

- **availability** (texto congelado, en inglés): S is the maximum of the available signals: with a signal UNAVAILABLE (no respiratory closure) or UNMAPPED it is a lower bound, and the reasons say which
- **ramp_shape** (texto congelado, en inglés): STRUCTURAL_SHAPE_PROVISIONAL: linear between the two bounds, saturating at 0 and 1; any monotone saturating shape is admissible, none is approved
- **signals** (texto congelado, en inglés): STRUCTURALLY_DEFINED_BUT_CLINICALLY_UNIDENTIFIED: no bound has a committed value (UNMAPPED)
<!-- /generado:senales -->

## 4. Agregación, memoria y composición

<!-- generado:composicion -->
```
alteración neurológica primaria      = N                      (escala común [0, 1])
estrés cerebral sistémico agudo  S   = máx(señales agudas)    (nunca suma)
carga de encefalopatía sistémica F   → S: tau_subida si S > F; tau_aclaramiento (> tau_subida) si no
alteración observable            I   = máx(N, S, F)           (nunca suma)
```

- **Agregación** (texto congelado, en inglés): MAXIMUM (faculty): no sum and no interaction term
- **Memoria** (texto congelado, en inglés): STRUCTURALLY_DEFINED_BUT_CLINICALLY_UNIDENTIFIED: tau_rise and tau_clear UNSET; never derived from tau_D, never fitted to the GI cases; 'sufficiently severe' stress is the signals' own normal bound (below it a signal reads 0 and loads nothing), no second threshold
- **Llegada** (texto congelado, en inglés): no arrival floor: an arrival impairment comes from N, S, a declared pre-arrival burden F0 or another declared cause; an authored mental-status label is never read
- **Categoría observada** (texto congelado, en inglés): no mapping from the impairment to an observed mental-status category (pending faculty)

Propiedades de la memoria, demostradas desde su ecuación (texto congelado, en inglés):

- **bounded_by_stress**: F never exceeds the largest S it has seen: the memory delays recovery, it never adds an impairment the acute signals did not reach
- **distinct_from_d**: D integrates the delivery deficit alone, without bound, and repays on tau_D (lactate and the sympathetic drive); F relaxes toward the maximum of six signals on its own constants and never exceeds it; F reads no D and D reads no F
- **monotone_recovery**: with S < F, F_next lies strictly between S and F: the memory falls monotonically
- **no_n**: burden_after reads no N, D, lactate or authored level, and nothing writes N
- **non_negative**: F_next = S + (F - S) e^(-dt/tau) is a convex combination of F and S, both in [0, 1]
- **persists**: with S = 0, F_next = F e^(-dt/tau_clear) > 0 for F > 0: zero stress never zeroes the memory at once
- **prolonged_greater**: after a constant S from F = 0, F = S (1 - e^(-t/tau_rise)) rises with the duration t, so a longer insult leaves a larger residual, a larger area F_end x tau_clear and a longer recovery
- **worsens**: with S > F, F_next lies strictly between F and S: acute stress raises the memory
<!-- /generado:composicion -->

## 5. Sondas N1–N12 (señales normalizadas sintéticas)

<!-- generado:sondas_n -->
| Sonda | Qué aísla (congelado) | Resultado | Pasa |
|---|---|---|---|
| N1 | normal N and every systemic signal normal: normal consciousness | I máx 0,00; F máx 0,00 | sí |
| N2 | primary N 0.6 only: consciousness worsens; the systemic memory stays 0 | I 0,60; S 0,00; F máx 0,00 | sí |
| N3 | oxygen deficit 0.6 only | déficit de aporte de oxígeno: S = I 0,60; F al final 0,599; N 0,00 | sí |
| N4 | cerebral hypoperfusion 0.6 only | hipoperfusión cerebral: S = I 0,60; F al final 0,599; N 0,00 | sí |
| N5 | metabolic acidemia 0.6 only | acidemia: S = I 0,60; F al final 0,599; N 0,00 | sí |
| N6 | hypercapnia 0.6 only | hipercapnia: S = I 0,60; F al final 0,599; N 0,00 | sí |
| N7 | hypoglycaemia 0.6 only | hipoglucemia: S = I 0,60; F al final 0,599; N 0,00 | sí |
| N8 | severe hypoxaemia 0.6 only | hipoxemia: S = I 0,60; F al final 0,599; N 0,00 | sí |
| N9 | hypoperfusion 0.5, deficit 0.6, acidemia 0.4, hypoxaemia 0.3 together: the maximum, not the sum | S 0,60 = máximo; la suma daría 1,80 | sí |
| N10 | a prolonged severe insult (hypoperfusion 0.9, deficit 0.8, acidemia 0.7, 6 units), then physiology restored (40 units) | al restaurar: S 0,00, F = I 0,898; cae monótona; área 3,70; bajo 0,05 en 11,75 u | sí |
| N11 | brief (1) vs prolonged (6) vs repeated brief (3 x 1, gaps 1) insults of equal intensity 0.9 | F al restaurar: breve 0,569, repetida 0,779, prolongada 0,898; área 2,35 / 3,21 / 3,70; tiempo bajo 0,05: 9,75 / 11,00 / 11,75 u | sí |
| N12 | primary N 0.4 with a systemic insult 0.7 (6 units), then restored | I durante 0,70; después nunca bajo N (0,40); F igual con o sin N: sí | sí |

Unidades sintéticas (u), memoria sintética de sonda (tau_subida 1, tau_aclaramiento 4): SYNTHETIC_PROBE_ONLY, nunca minutos.
<!-- /generado:sondas_n -->

## 6. Robustez a la razón sintética de la memoria

<!-- generado:robustez -->
| tau_aclaramiento / tau_subida | Sondas que pasan |
|---|---|
| 2 | 12 de 12 |
| 4 | 12 de 12 |
| 8 | 12 de 12 |

Todas pasan en cada razón: sí.
<!-- /generado:robustez -->

## 7. Sondas fisiológicas: cableado y aislamiento

<!-- generado:fisiologia -->
Regla (texto congelado, en inglés): Fixed states on P2K-2's neutral probe arrival (bands.ARRIVAL with the probe gas: HCO3 20, PaCO2 36, intrinsic RR 16; extraction reserve 2.5), read through the candidate's readings with the ventilation candidate at each retained gain. The reference is the arrival itself (N1 requires it to read normal); each signal is classified threshold-free: zero under every admissible mapping, or positive under some. The sizes are illustrative extremes, P2L-1's probes.

Ganancia de ventilación 0,03:

| Sonda | PAM | Déficit/demanda | SpO2 | pH | PaCO2 | Glucosa | Señales que pueden ser positivas | Cableado | Aislada |
|---|---|---|---|---|---|---|---|---|---|
| Referencia (llegada neutra) | 90,0 | 0,000 | 97,0 | 7,371 | 35,7 | 100 | ninguna | sí | sí |
| A. PAM baja, sin déficit | 48,5 | 0,000 | 97,0 | 7,371 | 35,7 | 100 | hipoperfusión cerebral | sí | sí |
| B. PAM normal, déficit alto | 90,0 | 0,250 | 97,0 | 7,371 | 35,7 | 100 | déficit de aporte de oxígeno | sí | sí |
| C. Ambos | 27,0 | 0,250 | 97,0 | 7,371 | 35,7 | 100 | hipoperfusión cerebral, déficit de aporte de oxígeno | sí | sí |
| E. SpO2 baja, aporte adecuado | 90,0 | 0,000 | 82,0 | 7,371 | 35,7 | 100 | hipoxemia | sí | sí |
| E2. FiO2 1 → aire ambiente | 90,0 | 0,000 | 73,3 | 7,371 | 35,7 | 100 | hipoxemia | sí | sí |
| F. SpO2 normal, déficit crítico | 90,0 | 0,375 | 97,0 | 7,371 | 35,7 | 100 | déficit de aporte de oxígeno | sí | sí |
| G. pH bajo, PaCO2 normal/baja | 90,0 | 0,000 | 97,0 | 7,136 | 27,6 | 100 | acidemia | sí | sí |
| H. PaCO2 alta, pH casi normal | 90,0 | 0,000 | 97,0 | 7,429 | 50,0 | 100 | hipercapnia | sí | sí |
| Hipercapnia aguda (no compensada) | 90,0 | 0,000 | 97,0 | 7,149 | 59,5 | 100 | acidemia, hipercapnia | sí | sí |
| Hipoglucemia | 90,0 | 0,000 | 97,0 | 7,371 | 35,7 | 30 | hipoglucemia | sí | sí |
| Shock con acidemia | 27,0 | 0,250 | 97,0 | 7,136 | 27,6 | 100 | acidemia, hipoperfusión cerebral, déficit de aporte de oxígeno | sí | sí |
| Sólo N primario (0,5) | 90,0 | 0,000 | 97,0 | 7,371 | 35,7 | 100 | ninguna | sí | sí |
| Etiqueta de llegada «obnubilado», fisiología normal | 90,0 | 0,000 | 97,0 | 7,371 | 35,7 | 100 | ninguna | sí | sí |

Ganancia de ventilación 0,04:

| Sonda | PAM | Déficit/demanda | SpO2 | pH | PaCO2 | Glucosa | Señales que pueden ser positivas | Cableado | Aislada |
|---|---|---|---|---|---|---|---|---|---|
| Referencia (llegada neutra) | 90,0 | 0,000 | 97,0 | 7,386 | 34,5 | 100 | ninguna | sí | sí |
| A. PAM baja, sin déficit | 48,5 | 0,000 | 97,0 | 7,386 | 34,5 | 100 | hipoperfusión cerebral | sí | sí |
| B. PAM normal, déficit alto | 90,0 | 0,250 | 97,0 | 7,386 | 34,5 | 100 | déficit de aporte de oxígeno | sí | sí |
| C. Ambos | 27,0 | 0,250 | 97,0 | 7,386 | 34,5 | 100 | hipoperfusión cerebral, déficit de aporte de oxígeno | sí | sí |
| E. SpO2 baja, aporte adecuado | 90,0 | 0,000 | 82,0 | 7,386 | 34,5 | 100 | hipoxemia | sí | sí |
| E2. FiO2 1 → aire ambiente | 90,0 | 0,000 | 73,3 | 7,386 | 34,5 | 100 | hipoxemia | sí | sí |
| F. SpO2 normal, déficit crítico | 90,0 | 0,375 | 97,0 | 7,386 | 34,5 | 100 | déficit de aporte de oxígeno | sí | sí |
| G. pH bajo, PaCO2 normal/baja | 90,0 | 0,000 | 97,0 | 7,179 | 25,0 | 100 | acidemia | sí | sí |
| H. PaCO2 alta, pH casi normal | 90,0 | 0,000 | 97,0 | 7,429 | 50,0 | 100 | hipercapnia | sí | sí |
| Hipercapnia aguda (no compensada) | 90,0 | 0,000 | 97,0 | 7,164 | 57,5 | 100 | acidemia, hipercapnia | sí | sí |
| Hipoglucemia | 90,0 | 0,000 | 97,0 | 7,386 | 34,5 | 30 | hipoglucemia | sí | sí |
| Shock con acidemia | 27,0 | 0,250 | 97,0 | 7,179 | 25,0 | 100 | acidemia, hipoperfusión cerebral, déficit de aporte de oxígeno | sí | sí |
| Sólo N primario (0,5) | 90,0 | 0,000 | 97,0 | 7,386 | 34,5 | 100 | ninguna | sí | sí |
| Etiqueta de llegada «obnubilado», fisiología normal | 90,0 | 0,000 | 97,0 | 7,386 | 34,5 | 100 | ninguna | sí | sí |
Con el perfil comprometido, cada señal de cada sonda queda UNMAPPED: ninguna lectura numérica de conciencia sale del núcleo real.
<!-- /generado:fisiologia -->

## 8. Ortogonalidad A–H

<!-- generado:ortogonalidad -->
| Grupo | Patrones de señales (ganancia 0,04) | Distinguibles | Aisladas |
|---|---|---|---|
| PAM / déficit (A, B, C, D) | ninguna; hipoperfusión cerebral; déficit de aporte de oxígeno; hipoperfusión cerebral, déficit de aporte de oxígeno | sí | sí |
| pH / PaCO2 (G, H) | acidemia; hipercapnia | sí | sí |
| SpO2 / aporte (E, F) | hipoxemia; déficit de aporte de oxígeno | sí | sí |
<!-- /generado:ortogonalidad -->

## 9. Caminos heredados retirados

<!-- generado:legado -->
Estado (texto congelado, en inglés):

- **piso de llegada**: RETIRED_FROM_CANDIDATE: the candidate has no arrival floor; derive keeps max(anchors.consciousness_level, ...) as LEGACY_REFERENCE_ONLY for the closed records
- **etiqueta de autoría de llegada**: an authored mental-status label (the GI cases' default 'Alert') is never read and never calibration evidence; an arrival impairment needs N, S, a declared pre-arrival burden F0 or another declared cause
- **D**: ABSENT_AS_CONTROLLER: D is never read by the candidate; it stays the oxygen-delivery debt, diagnostic
- **redacción de derived.PARAMETERS**: derived.PARAMETERS keeps the ladders' closed status text ('adopted'): DOCUMENTED_SEMANTIC_DEBT until runtime integration
- **FC**: ABSENT: the heart rate is never read
- **lactato**: ABSENT: no lactate path (faculty); never read
- **escalera de PAS**: RETIRED_FROM_CANDIDATE: SBP 80 / 65 never read (MAP is the pressure signal); LEGACY_REFERENCE_ONLY in derive
- **escalera de SpO2**: RETIRED_FROM_CANDIDATE: SpO2 87 / 80 never read; SpO2 enters only as the hypoxaemia signal through its own (unmapped) ramp; LEGACY_REFERENCE_ONLY in derive
<!-- /generado:legado -->

## 10. El bucle del tono de P2L-1

<!-- generado:tono -->
| Fila de P2L-1 | Déficit no decreciente | Presión no decreciente | El nivel heredado bajó |
|---|---|---|---|
| anaemia g0 | sí | sí | no |
| anaemia g0.25 | sí | sí | no |
| anaemia g0.5 | sí | sí | sí |
| anaemia g1 | sí | sí | sí |
| demand_x2 g0 | sí | sí | no |
| demand_x2 g0.25 | sí | sí | no |
| demand_x2 g0.5 | sí | sí | sí |
| demand_x2 g1 | sí | sí | sí |

Inversión heredada en anaemia g0.5, anaemia g1, demand_x2 g0.5, demand_x2 g1. En el candidato el déficit entra con su propia señal, monótona: inversión eliminada: sí.
<!-- /generado:tono -->

## 11. Subconjunto de acidemia extrema

<!-- generado:acidemia -->
- **Filas:** 17 604 de 511 056 (candidate rows (upstream unit x latent combination), not trajectories; 57m: 17604, 72f: 0).
- **pH:** de 6,961 a menos de 7,00; la fila más baja en el minuto 120, déficit 0,835, PaCO2 25,8.
- **PAM sin tratar en el minuto 120:** 32,5–46,3 mmHg.
- **Gases de llegada de autoría:** pH 7.37, PaCO2 31, HCO3 17.3, PaO2 91 on FiO2 21%.

- **acidemia** (texto congelado, en inglés): POSITIVE_UNDER_SOME_ADMISSIBLE_MAPPING: every row lies below pH 7.00, the most acidemic rows of the candidate set, so their acidemia signal is the set's highest under every admissible mapping; it is 0 for every row only if the normal bound is at or below the lowest pH (6.961) and positive for every row once the normal bound is at or above 7.00
- **hipoperfusión cerebral** (texto congelado, en inglés): POSITIVE_UNDER_SOME_ADMISSIBLE_MAPPING: untreated MAP at minute 120 between 32.5 and 46.3 mmHg
- **hipercapnia** (texto congelado, en inglés): ZERO_UNDER_EVERY_ADMISSIBLE_MAPPING at the lowest row (PaCO2 25.8, below the case's authored arrival PaCO2 (pH 7.37, PaCO2 31, HCO3 17.3, PaO2 91 on FiO2 21%)): a metabolic acidemia with respiratory compensation; pH and PaCO2 kept apart
- **déficit de aporte de oxígeno** (texto congelado, en inglés): POSITIVE_UNDER_SOME_ADMISSIBLE_MAPPING: the lowest row carries a deficit of 0.835

- **Agregación** (texto congelado, en inglés): three independent signals can read positive in these rows; the observable is their maximum, so one shock is not counted three times
- **Lectura** (texto congelado, en inglés): kept as CONSCIOUSNESS_COLLAPSE_REVIEW, never filtered: once bounds exist these rows read impaired through acidemia, perfusion and delivery alike; no bound is fitted to make them impaired, and their collapse question belongs to the collapse architecture
- **Clasificación:** CONSCIOUSNESS_COLLAPSE_REVIEW; filtradas: no.
<!-- /generado:acidemia -->

## 12. Generalización

<!-- generado:generalizacion -->
| Familia | Señales (sintéticas) | N | I durante | I al restaurar | Retraso | Portador físico | Representada |
|---|---|---|---|---|---|---|---|
| A. Shock hemorrágico | acidemia 0,5, hipoperfusión cerebral 0,6, déficit de aporte de oxígeno 0,7 | 0,0 | 0,70 | 0,698 | sí | Shock con acidemia | sí |
| B. Hipoglucemia grave | hipoglucemia 0,8 | 0,0 | 0,80 | 0,798 | sí | Hipoglucemia | sí |
| C. Fisiología hipercápnica / opioides | acidemia 0,3, hipercapnia 0,7 | 0,0 | 0,70 | 0,698 | sí | Hipercapnia aguda (no compensada) | sí |
| D. Ictus / lesión neurológica primaria | — | 0,7 | 0,70 | 0,700 | no | — | sí |
| E. Hipoxemia grave | hipoxemia 0,8 | 0,0 | 0,80 | 0,798 | sí | E2. FiO2 1 → aire ambiente | sí |
| F. Shock distributivo | hipoperfusión cerebral 0,6 | 0,0 | 0,60 | 0,599 | sí | A. PAM baja, sin déficit | sí |

**Resultado:** COMMON_NEUROLOGIC_ARCHITECTURE_PLAUSIBLE. (texto congelado, en inglés): one composition for every family: the systemic families through the six generic signals and the one memory, the primary family through N without loading the memory; no family term in the physiology; what each family still needs is its own writer of the signal, not a consciousness rule

- **A. Shock hemorrágico**, escritor que la familia aporta (texto congelado, en inglés): the bleed's own writers (volume, Hb); shared perfusion and delivery
- **B. Hipoglucemia grave**, escritor que la familia aporta (texto congelado, en inglés): a glucose writer and dextrose: none in the core yet (the family's own contributor)
- **C. Fisiología hipercápnica / opioides**, escritor que la familia aporta (texto congelado, en inglés): the ventilation efficiency or drive the family lowers; its primary CNS depression is a future pharmacologic modifier, not N
- **D. Ictus / lesión neurológica primaria**, escritor que la familia aporta (texto congelado, en inglés): N, the primary neurologic family's own writer (no kinetics here)
- **E. Hipoxemia grave**, escritor que la familia aporta (texto congelado, en inglés): a gas-exchange writer (SpO2 moves only with FiO2 in the core today)
- **F. Shock distributivo**, escritor que la familia aporta (texto congelado, en inglés): tone (vasodilation): the MAP path apart from the deficit
<!-- /generado:generalizacion -->

## 13. Identificabilidad, trayectorias y depresión farmacológica

<!-- generado:identificabilidad -->
- **arrival_burden** (texto congelado, en inglés): STRUCTURALLY_DEFINED: 0 unless a case declares a pre-arrival insult; never from an authored label
- **category_mapping** (texto congelado, en inglés): UNDEFINED: no impairment-to-category mapping (pending faculty)
- **memory_time_constants** (texto congelado, en inglés): STRUCTURALLY_DEFINED_BUT_CLINICALLY_UNIDENTIFIED: tau_rise < tau_clear, UNSET; never derived from tau_D
- **n_scale** (texto congelado, en inglés): STRUCTURALLY_DEFINED (the common scale); no case value
- **ramp_shape** (texto congelado, en inglés): STRUCTURALLY_DEFINED_BUT_CLINICALLY_UNIDENTIFIED (linear provisional)
- **signal_bounds** (texto congelado, en inglés): STRUCTURALLY_DEFINED_BUT_CLINICALLY_UNIDENTIFIED: twelve bounds (normal, severe per signal), UNMAPPED; the GI cases carry no post-arrival neurologic observation
- **well_constrained** (texto congelado, en inglés): none: synthetic probes constrain structure only

- **Trayectorias GI C1–C4** (texto congelado, en inglés): NOT_GENERATED: no signal mapping or memory constant exists independently of GI outcomes (P2L-2-10); inventing them to draw C1-C4 would be the fitting the faculty forbade: STRUCTURAL_ONLY
- **Depresión farmacológica del SNC** (texto congelado, en inglés): FUTURE_COMMON_SYSTEMIC_OR_PHARMACOLOGIC_MODIFIER: a sedative or opioid family may need its own signal, entering the observable maximum like the systemic signals and never written into N; whether it also loads the systemic memory, or carries its own drug kinetics, is that family's decision
<!-- /generado:identificabilidad -->

## 14. No regresión

<!-- generado:aguas_arriba -->
- **Árbol de P2L-1:** 64 archivos, huella `f63cbb93ace102622b46de7f62bc6e6d1473bf8e78f63fe6a515d4859cc924fa`; idéntico byte a byte: sí (fuera de los módulos de P2L-2 y de las tuplas declaradas).
- **Quién importa la fisiología candidata:** clinical_core/encephalopathy_architecture.py (ningún módulo del núcleo).
- Por construcción no cambian BloodState, gasto, presión/tono, DO2/déficit, D, lactato, FC/barorreflejo, ácido-base ni FR/W/PaCO2: ningún paso del núcleo lee el candidato y el candidato no escribe estado.
<!-- /generado:aguas_arriba -->

## 15. Veredicto

<!-- generado:veredicto -->
| Criterio | Cumple |
|---|---|
| generalización plausible | sí |
| el lactato no controla la conciencia | sí |
| escaleras PAS/SpO2 y piso de llegada retirados del candidato | sí |
| agregación por máximo, sin suma | sí |
| la memoria sistémica da el retraso de recuperación | sí |
| N reservado al estado neurológico primario | sí |
| nada aprobado | sí |
| N primario afecta la conciencia por sí solo | sí |
| señales causalmente explícitas (cableado, aislamiento, ortogonalidad) | sí |
| alteración sistémica aguda separada de N | sí |
| fisiología previa intacta | sí |

**Veredicto:** `COMMON_CONSCIOUSNESS_ARCHITECTURE_READY`.
<!-- /generado:veredicto -->

## 16. Siguiente paso y decisiones pedidas

<!-- generado:recomendacion -->
- **¿Hace falta más calibración numérica de conciencia antes de probar la generalización?** no.
- **Estrategia:** `DO_NOT_OVERFIT_GI`.
- **Recomendación:** `COLLAPSE_SAFETY_ARCHITECTURE`.
- **Por qué** (texto congelado, en inglés): the consciousness architecture needs no more GI numbers to be tested; the carried subset (untreated pH below 7.00, MAP 32-46 at minute 120) keeps a pulse because collapse is off, and every shock family needs a collapse safety architecture before migration; a non-shock second family (hypoglycaemia, hypercapnia) is causally independent of collapse and can follow
- **Regla** (texto congelado, en inglés): Predeclared. READY: additional numeric consciousness calibration is not required before testing generalization (the GI cases cannot identify it): DO_NOT_OVERFIT_GI. Next by causal necessity: COLLAPSE_SAFETY_ARCHITECTURE if the carried subset still needs collapse review with collapse off (every shock family, GI included, needs it before migration), else SECOND_FAMILY_GENERALIZATION. NOT_READY: the blocker and the smallest correction.

Decisiones pedidas a la docencia (texto congelado, en inglés):

1. the twelve signal bounds (normal, severe) as clinical decisions from general physiology, never from the GI cases; MAP absolute or relative to the patient's autoregulation (chronic hypertension)
2. the memory's tau_rise and tau_clear, and whether one memory serves every insult or the clearance differs by cause
3. the mapping from the impairment I to an observed mental-status category (or a GCS-like scale): needed before any observable
4. the acidemia signal on total pH (as decided: an acute hypercapnia co-signals it, the maximum keeps one) or on the metabolic component
5. the future pharmacologic CNS-depression signal: whether it loads the systemic memory or carries its own kinetics
6. how a case declares an arrival impairment (N, a pre-arrival burden F0, another cause) instead of a mental-status label
7. the closed wording of N (state.py) and of derive's ladders (derived.PARAMETERS), updated at runtime integration
8. the carried extreme-acidemia subset: stays CONSCIOUSNESS_COLLAPSE_REVIEW for the collapse architecture
<!-- /generado:recomendacion -->

## 17. Eficiencia

<!-- generado:eficiencia -->
- Lecturas de estado fijo por el núcleo certificado: 28.
- Pasos de la memoria sintética: 6288 en 66 cursos (aritmética exacta, sin integrador del núcleo).
- Pasos del integrador del núcleo: 0; trayectorias simuladas: 0; trayectorias GI: 0.
- Registros reutilizados: P2L1_consciousness_audit.json (con huella fijada).
- Barrido cartesiano: no; región reconstruida: no; motor heredado leído: no.
<!-- /generado:eficiencia -->

## 18. Limitaciones

- **Sin números clínicos.** La arquitectura está probada con señales normalizadas sintéticas y una memoria
  sintética (unidades sintéticas, nunca minutos). Ninguna sonda dice a qué PAM, SpO2, pH, PaCO2 o glucosa se altera la
  conciencia, ni cuánto tarda en recuperarse.
- **Sin categoría observable.** I no se traduce todavía a alerta / somnoliento / obnubilado / sin respuesta ni a una
  escala tipo GCS: lo que ve el residente sigue saliendo del motor heredado.
- **La clasificación sin umbral** usa como referencia la llegada neutra de la familia de sondas (HCO3 20). Dice qué
  señales pueden ser positivas con algún mapeo admisible, no cuáles lo son.
- **La rampa lineal** es una forma provisional; cualquier forma monótona y saturante es admisible.
- **Una sola memoria** para todas las agresiones. Si la recuperación difiere por causa (por ejemplo, más rápida tras la
  hipercapnia que tras una hipoperfusión prolongada), hará falta decidirlo; no se agregó sin evidencia.
- **La acidemia lee el pH total**, como se decidió: en la hipercapnia aguda acompaña a la señal de hipercapnia.
- **Deuda semántica documentada.** La redacción cerrada de N en `state.py` («CNS depression / neurological state») y
  el estado «adopted» de las escaleras en `derived.PARAMETERS` no se tocaron, porque los archivos del núcleo y los
  registros cerrados dependen de ellos; se corrigen en la integración en tiempo de ejecución.
- **El déficit de la fila más baja** del subconjunto (0,835) es el valor que registra P2K-5, en unidades de índice, no
  la fracción déficit / demanda; para la clasificación basta que sea positivo.
- **La memoria es una capa del candidato**, integrada fuera del núcleo y sin retroalimentarlo. Entra en `CoreState.aux`
  sólo con la integración en tiempo de ejecución, que no está autorizada.
- **Las pruebas de P2L-1 se adaptaron** para ver su propio árbol, dejando fuera la capa de P2L-2, y el análisis de P2L-2
  reutiliza su búsqueda congelada; el registro de P2L-1 no cambia.
- **Proceso:** las sondas estructurales se ejercitaron (sólo aprobado o fallido) mientras se escribían los módulos,
  como prevé el orden del encargo; el registro sale de la corrida del módulo congelado.

## 19. Revisión adversarial

Pendiente.
