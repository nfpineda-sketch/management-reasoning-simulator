# P2O-1 · Arquitectura común de agua pulmonar e intercambio gaseoso (en sombra)

**Rama:** `phase-2-clinical-core-shadow` · **Base:** `85d18e6` (P2N-3) · **Congelamiento:** `5d1db63` (digest
`22bb29b9…`) · **Fecha:** 2026-11-03

Sólo sombra. El núcleo común gana el camino que fijó la docencia (O3): **L → G → oxigenación → contenido de O2 →
aporte**. Son dos inserciones inertes en `clinical_core/derived.py` y `clinical_core/integration.py`, apagadas por
defecto: los tres valores nuevos del perfil quedan en `None` (UNSET). La evaluación está en
`clinical_core/gas_exchange_architecture.py`. Ningún valor clínico se aprueba, el legado no es objetivo, el colapso
(P2M-2) no cambia y nada llega al tiempo de ejecución. Las secciones generadas salen del registro
`docs/revision/P2O1_gas_exchange.json` (`gas_exchange_architecture_report`).

## Resumen

**Veredicto: `COMMON_GAS_EXCHANGE_ARCHITECTURE_READY_FOR_GENERALIZATION`.** Recomendación, por la regla
predeclarada: `CARDIOGENIC_CONGESTION_GENERATION`.

- **El núcleo gana el camino L → G → SpO2 → aporte, apagado por defecto.**
  - Son dos inserciones inertes (§14). Se demuestra que los dos archivos del núcleo son, byte a byte, los de P2N-2 sin
    ellas.
  - Con los tres valores en `None`, el golden sólo gana tres entradas de parámetros. Ninguna trayectoria cambia.
- **L → G es el término de primer orden, G_L = k·max(0, L)** (§4).
  - Las demás formas plausibles se eliminaron analíticamente, porque añaden:
    - un parámetro de forma no identificable;
    - un umbral (O4 lo prohíbe);
    - un estado nuevo;
    - o un crédito sin cota por debajo de la llegada (O1 deja esa cota sin representar).
  - No fue una elección sustantiva, así que no hubo parada.
- **G → oxigenación** (§5):
  - es exacta en G = 0;
  - nunca mejora con G y nunca empeora con la FiO2;
  - con G grave la respuesta a la FiO2 es incompleta, por una fracción interna tipo shunt que queda CANDIDATE / UNSET.
- **Las sondas estructurales pasan todas** (O1–O12, §7). Además:
  - el único escritor de G es el acoplamiento común;
  - ni la FR, ni la ventilación, ni la carga ácida, ni D, ni el lactato mueven G;
  - GI queda idéntico en 16 de 16 cursos (dos casos, cuatro escenarios, con y sin ácido-base).
- **Las siete familias se representan con entradas comunes distintas** (§8):
  - la neumonía y el TEP usan G sin L;
  - el opioide y la acidosis metabólica no necesitan G.

  El asma, el TEP y la anafilaxia comparten el patrón de signos y se distinguen por qué entrada domina.
- **acs_70f_left_main después del congelamiento** (§9):
  - la llegada es exacta (SpO2 94);
  - con el L que escribe la familia, la SpO2 baja a 91,5 a los 120 min en la referencia (88,9–92,7 en la región 1-D);
  - el aporte queda 3 % bajo el control y D sube 0,9;
  - el lactato nunca queda bajo el control;
  - el O2 al 40 % la sube a 96–97,5.

  El 90 % del legado a los 60 min es sólo referencia; no se ajustó nada.
- **La conciencia lee la misma SpO2 y el colapso sigue viendo sólo el aporte** (§12): P2M-2 no cambia, y queda
  `DIRECT_SPO2_COLLAPSE_INPUT_DEFERRED`.
- **La brecha que manda es aguas arriba** (§10). En el caso ACS el volumen común no genera L, ni con 4000 mL: la
  posición de precarga llega a 0,69, bajo la rodilla de 0,85. Todo efecto respiratorio cardiogénico depende hoy de un L
  que escribe la familia. Por eso la regla elige la generación común de congestión.

## 1. Decisiones de la docencia

<!-- generado:decisiones -->
Decisiones de la docencia (texto congelado, en inglés):

- **O1**: L remains a dynamic deviation from arrival: L = 0 is the authored arrival lung state (arrival congestion may already exist), L > 0 worsening, L < 0 improvement only if the channel domain allows it safely; arrival anchors are not changed to give L an absolute meaning
- **O2**: G is one common gas-exchange impairment coordinate; shunt, V/Q mismatch and diffusion are not split (latent contributors to one effective G); a single-G causal contradiction across families stops the package
- **O3**: the common path is L -> G -> oxygenation -> oxygen content / DO2; L writes no SpO2, DO2, D, lactate, RR, W, consciousness or collapse
- **O4**: L -> G is monotonic, non-pathological, zero at L = 0 (arrival), never improves gas exchange when L worsens; clinical gain and thresholds UNSET; synthetic structural values for probes
- **O5**: no NIV in P2O-1 (a future treatment-composition task)
- **O6**: no direct SpO2 collapse input; collapse sees respiratory failure through oxygen delivery; P2M-2 unchanged

Brechas que se arrastran: `COMMON_CONGESTION_GENERATION_GAP`, `ACS_ARRIVAL_HR_COMMON_GAP_CANDIDATE`, `RV_LV_INTERDEPENDENCE_COMMON_GAP`, `DIRECT_SPO2_COLLAPSE_INPUT_DEFERRED`.
<!-- /generado:decisiones -->

## 2. Auditoría de la semántica actual (P2O-1A)

<!-- generado:auditoria -->
Semántica ejecutable antes de P2O-1 (texto congelado, en inglés):

| Magnitud | Escritores | Lectores | Llegada | Tipo |
|---|---|---|---|---|
| DO2 | derived.relative_delivery (output x Hb ratio x SpO2 ratio) x arrival_delivery_ratio | deficit, D, lactate, acid burden, sympathetic acute term, encephalopathy, collapse | arrival_delivery_ratio | relative to normal through the arrival layer |
| FiO2 | interventions.oxygen (SettingChange) | SpO2 | authored | absolute setting |
| G | none ('guard only; no module writes G yet') | none | 0 | deviation from arrival ('shunt / V-Q impairment') |
| L | core: derived.congestion_rate (excess preload above the knee x (1 - reserve x P)) and lung_water_clearance (first order toward arrival, only above it); family: ACS IschaemicCongestion | only its own clearance | 0 | deviation from arrival |
| PaCO2 | derived.respiration (P2K-2: resting / ventilation, anchored to the arrival PaCO2); P2K-3 closure: reference / W | pH, encephalopathy hypercapnia | authored (anchored) | absolute, derived |
| PaO2 | none (authored at arrival only) | none | authored | not represented |
| RR | derived (P2K-1 RR, or P2K-2 intrinsic + S(1 - exp(-drive / S)) with the acid drive) | P2K-2 ventilation (RR x efficiency / intrinsic) | model (reported against the authored) | absolute, derived |
| SpO2 | derived (_perfusion): arrival SpO2 + spo2_per_fio2 x the oxygen benefit over arrival, cap 100 | delivery (relative_delivery), sympathetic hypoxaemia term, consciousness level (oxygen_levels), encephalopathy hypoxaemia signal; collapse only through delivery | authored | absolute observable anchored to arrival |
| W | none (channel); P2K-3 ventilation.ventilated_respiration computes an effective-ventilation W (capacity / demand) that is not the channel | the channel: only the pre-P2K-2 RR (derived.respiratory_rate); with the acid-base physiology on, derived.respiration reads no W channel | 0 (channel); computed W 1 at baseline | channel: deviation; computed W: ratio to need |
| acid_burden | integration._acid_burden (deficit_to_acid_gain x effective deficit, first-order clearance) | HCO3, respiratory drive | max(0, reference - authored HCO3) | absolute state |
| oxygen_content | none as a state: Hb x SpO2 inside relative_delivery (dissolved O2 not modelled) | delivery | relative 1 | relative to arrival |

Compatibilidad (texto congelado, en inglés): O1-O6 are compatible with the channel domains: L and G are already deviations from arrival on [-10, 10] with no reader of G, SpO2 is derived in one place (derived._perfusion) and every reader of oxygenation reads it there, collapse reads delivery only, and the respiratory closures read neither L nor G.
<!-- /generado:auditoria -->

## 3. Conceptos separados y semántica aceptada (P2O-1B, C)

<!-- generado:semantica -->
Antes (texto congelado, en inglés):

- **G**: deviation from arrival ('shunt / V-Q impairment'); no writer, no reader
- **L**: deviation from arrival; read by nothing but its clearance
- **W**: channel: deviation; computed W: ratio to need

Aceptada (texto congelado, en inglés):

- **G**: the effective gas-exchange impairment relative to arrival (O2, P2O-1C): G = 0 is the arrival gas exchange; a worse G never improves oxygenation; G changes no ventilation; L may raise it (the core coupling) and a family may write it through other mechanisms; no disease is named in it
- **L**: lung water / congestion change: a dynamic deviation from the authored arrival lung state (O1); its own writers and clearance; it reaches oxygenation only through G
- **RR**: the respiratory drive's observable rate (P2K-2): reads no L, G or SpO2 (no hypoxaemic drive in P2O-1)
- **SpO2**: the result of gas exchange G and inspired oxygen, anchored to the authored arrival
- **W**: ventilatory capacity / effective ventilation relative to need: unchanged by P2O-1 (P2K-2 / P2K-3); reads no L or G and is read by no oxygenation term
- **acid_burden**: metabolic acid physiology (P2K-2): produced by the effective oxygen deficit, read by HCO3 and the drive; never written into or read from G
<!-- /generado:semantica -->

## 4. L → G (P2O-1D): formas comparadas antes de ver casos

<!-- generado:formas -->
| Forma | Expresión | Estado | Por qué |
|---|---|---|---|
| lagged | `dG_L/dt = (k x max(0, L) - G_L) / tau` | ELIMINATED | needs a new state for the L share of G and a second time constant: L's own writers and clearance already carry the dynamics; tau is unidentifiable without authored courses |
| linear_first_order | `G_L = k x max(0, L)` | SELECTED | the first-order term every smooth monotone L -> G with G(0) = 0 shares; continuous, monotone, zero at arrival, no threshold, one explicit gain, inactive at L = 0 |
| power | `k x max(0, L)^n` | ELIMINATED | n unidentifiable without authored courses; n = 1 is the selected form |
| saturating | `k x L / (1 + L / L_half)` | ELIMINATED | reduces to the selected form to first order; L_half is a curvature with no authored data (unidentifiable); the SpO2 mapping is already bounded |
| symmetric | `k x L (credits L < 0)` | ELIMINATED | an improvement below arrival needs a bound, the arrival congestion's share of the arrival impairment, which O1 leaves unrepresented; any bound would be a new clinical value |
| threshold | `k x max(0, L - L0)` | ELIMINATED | needs a clinical threshold (O4: none) and is inert over a range of worsening lung water |

Decisión (texto congelado, en inglés): NOT_A_SUBSTANTIVE_CHOICE: the selected form is the shared first-order term of the plausible forms; every eliminated form adds an unidentifiable shape parameter, a threshold O4 forbids, a new state, or an unbounded credit O1 leaves unrepresented. Curvature, lag and improvement below arrival stay UNSET for the faculty.
<!-- /generado:formas -->

## 5. G → oxigenación y FiO2 (P2O-1E)

<!-- generado:oxigenacion -->
Estructura G → oxigenación (texto congelado, en inglés):

- **at_arrival**: exact: at G = 0 the expression is the core's SpO2 term by term
- **below_arrival**: G < 0 changes nothing (no credit below the arrival reference, as for L)
- **content_and_delivery**: unchanged: delivery = output x Hb ratio x SpO2 ratio (dissolved O2 not modelled); PaO2 stays NOT_REPRESENTED (no dissociation curve)
- **effective_shunt**: 1 - retained(G): internal to the mapping (CANDIDATE / UNSET), never a shunt or V/Q state
- **incomplete_response**: retained(G) = 1 / (1 + r G) falls toward 0 with a severe G, never reaching it; r = 0 keeps the full FiO2 response (a purely V/Q-like G)
- **monotone_in_FiO2**: dSpO2/dFiO2 = spo2_per_fio2 x retained(G) > 0 above room air: never paradoxically worse
- **monotone_in_G**: dSpO2/dG = -s + spo2_per_fio2 x benefit(FiO2) x d retained / dG <= -s < 0 for G > 0 (both terms non-positive), whatever the arrival FiO2
- **structure**: SpO2 = arrival SpO2 - s x max(0, G) + spo2_per_fio2 x (benefit(FiO2) x 1 / (1 + r x max(0, G)) - benefit(arrival FiO2)), benefit(F) = max(0, F - 0.21), clamped to [0, 100]
- **ventilation**: reads no ventilation, PaCO2, RR or acid burden: oxygenation impairment stays separable from ventilation; hypoventilation reaches PaCO2, not G

Interacción con la FiO2 (texto congelado, en inglés): FiO2 adds spo2_per_fio2 (ADOPTED, 30 points per unit) x its benefit over room air, scaled by the share G keeps; the arrival FiO2's benefit is part of the authored arrival SpO2, so a patient who arrived on oxygen loses part of it as G worsens, and a FiO2 rise always helps.
<!-- /generado:oxigenacion -->

## 6. Parámetros: región sintética (P2O-1O)

<!-- generado:region -->
- **k (G por unidad de L)**: referencia 1,00; 1-D 0,50, 1,00, 2,00; por defecto `UNSET`, en sondas `SYNTHETIC_ONLY`, aprobado: no
- **r (pérdida de la respuesta al O2 por unidad de G)**: referencia 0,50; 1-D 0,00, 0,50, 2,00; por defecto `UNSET`, en sondas `SYNTHETIC_ONLY`, aprobado: no
- **s (puntos de SpO2 por unidad de G)**: referencia 5,00; 1-D 2,50, 5,00, 10,00; por defecto `UNSET`, en sondas `SYNTHETIC_ONLY`, aprobado: no

Identificabilidad (texto congelado, en inglés): only k x s is identifiable from a lung-water course at room air; s alone from a family that writes G; r only from an oxygen response; none is identifiable from the current authored truth (arrival only).
<!-- /generado:region -->

## 7. Sondas estructurales O1–O12 (P2O-1G)

<!-- generado:sondas -->
| Sonda | Qué prueba | Cumple |
|---|---|---|
| O1 | L = 0 y G = 0: la oxigenación de llegada se conserva | sí |
| O2 | L empeora: G no mejora | sí |
| O3 | G empeora con la ventilación fija: la oxigenación empeora | sí |
| O4 | G empeora con la PaCO2 fija: la oxigenación empeora sin pasar por la ventilación | sí |
| O5 | FiO2 sube con G leve: la oxigenación mejora | sí |
| O6 | FiO2 sube con G grave: la mejora es incompleta y nunca paradójica | sí |
| O7 | cambia la FR con W y G fijos: la oxigenación no cambia | sí |
| O8 | cambia W con G fijo: cambia la PaCO2, no G ni la SpO2 | sí |
| O9 | sube la carga ácida con G fijo: G no cambia | sí |
| O10 | suben el lactato y D con G fijo: G no cambia | sí |
| O11 | L mejora hacia la llegada: G no empeora | sí |
| O12 | GI con L = 0: lectura idéntica | sí |

- **O2:** con k = 0,5 → G final 0,532 (L 1,064, SpO2 94,34), 1,0 → G final 1,064 (L 1,064, SpO2 91,68), 2,0 → G final 2,128 (L 1,064, SpO2 86,36); único escritor de G: el acoplamiento común.
- **O6:** con r > 0 la primera subida de FiO2 rinde menos con G grave en todos los puntos: sí.
- **O8:** ALVEOLAR_GAS_OXYGENATION_DEFERRED: hypoventilation raises PaCO2 but lowers no SpO2 (no alveolar gas equation; a faculty decision, TASK 3 (3)).
- **O9 / O10:** carga ácida 0,00 → 1,25, D 0,0 → 8,2; G máximo 0,000.
- **O11:** L pico 0,848 → 0,583; G pico 0,848 → 0,583; con L bajo la llegada (mínimo −0,90) G queda en 0,0.
- **O12:** 16 de 16 cursos GI idénticos (dos casos × cuatro escenarios × perfil certificado y con ácido-base), L máximo 0,0.
<!-- /generado:sondas -->

## 8. Sondas entre familias (P2O-1H)

<!-- generado:familias -->
| Familia | Entradas (sintéticas) | L máx | G máx | SpO2 0 → 60 | con O2 0,6 | PaCO2 0 → 60 (ref.) | FR (ref.) | Cumple |
|---|---|---|---|---|---|---|---|---|
| anafilaxia | W (airway), G, T | 0,00 | 0,60 | 97,0 → 94,0 | 100,0 | 57,1 → 57,1 (40,0) | 16,0 (16,0) | sí |
| asma | W (structural efficiency), G | 0,00 | 0,30 | 97,0 → 95,5 | 100,0 | 66,7 → 66,7 (40,0) | 16,0 (16,0) | sí |
| cardiogénica | L | 1,06 | 1,06 | 97,0 → 91,7 | 99,3 | 40,0 → 40,0 (40,0) | 16,0 (16,0) | sí |
| acidosis metabólica aislada | acid burden (arrival HCO3) | 0,00 | 0,00 | 97,0 → 97,0 | 100,0 | 26,7 → 30,7 (40,0) | 29,8 (16,0) | sí |
| hipoventilación por opioide | W (structural efficiency) | 0,00 | 0,00 | 97,0 → 97,0 | 100,0 | 80,0 → 80,0 (40,0) | 16,0 (16,0) | sí |
| neumonía | G | 0,00 | 1,20 | 97,0 → 91,0 | 98,3 | 40,0 → 40,0 (40,0) | 16,0 (16,0) | sí |
| TEP | G, W (dead space) | 0,00 | 1,50 | 97,0 → 89,5 | 96,2 | 47,1 → 47,1 (40,0) | 16,0 (16,0) | sí |

Entradas distintas por familia: sí. Nota (texto congelado, en inglés): SINGLE_G_OXYGEN_RESPONSE: one r for every family (O2); a family cannot declare a more or less oxygen-responsive G at the same impairment.
<!-- /generado:familias -->

## 9. Validación cardiogénica: acs_70f_left_main después del congelamiento (P2O-1I)

<!-- generado:acs -->
| Curso | Minuto | L | G | SpO2 | Aporte | Déficit | D | Lactato | FC | PaCO2 |
|---|---|---|---|---|---|---|---|---|---|---|
| P2N-2 sin P2O-1 | 0 | 0,000 | 0,000 | 94,0 | 0,340 | 0,150 | 20,0 | 3,1 | 91,8 | 30,8 |
| P2N-2 sin P2O-1 | 30 | 0,035 | 0,000 | 94,0 | 0,321 | 0,198 | 25,2 | 2,8 | 95,0 | 31,5 |
| P2N-2 sin P2O-1 | 60 | 0,136 | 0,000 | 94,0 | 0,302 | 0,245 | 31,8 | 2,6 | 98,6 | 31,8 |
| P2N-2 sin P2O-1 | 90 | 0,296 | 0,000 | 94,0 | 0,283 | 0,291 | 39,8 | 2,5 | 102,4 | 31,8 |
| P2N-2 sin P2O-1 | 120 | 0,508 | 0,000 | 94,0 | 0,265 | 0,337 | 49,2 | 2,4 | 106,5 | 31,5 |
| referencia | 0 | 0,000 | 0,000 | 94,0 | 0,340 | 0,150 | 20,0 | 3,1 | 91,8 | 30,8 |
| referencia | 30 | 0,035 | 0,035 | 93,8 | 0,320 | 0,199 | 25,2 | 2,8 | 95,2 | 31,5 |
| referencia | 60 | 0,136 | 0,136 | 93,3 | 0,300 | 0,251 | 31,9 | 2,6 | 99,0 | 31,8 |
| referencia | 90 | 0,296 | 0,296 | 92,5 | 0,279 | 0,304 | 40,2 | 2,5 | 103,4 | 31,7 |
| referencia | 120 | 0,508 | 0,508 | 91,5 | 0,257 | 0,357 | 50,1 | 2,4 | 108,2 | 31,4 |
| referencia + O2 0,40 desde el min 60 | 60 | 0,136 | 0,136 | 93,3 | 0,300 | 0,251 | 31,9 | 2,6 | 99,0 | 31,8 |
| referencia + O2 0,40 desde el min 60 | 90 | 0,296 | 0,296 | 97,5 | 0,295 | 0,262 | 38,9 | 2,5 | 101,7 | 31,9 |
| referencia + O2 0,40 desde el min 60 | 120 | 0,508 | 0,508 | 96,0 | 0,271 | 0,322 | 47,7 | 2,4 | 105,9 | 31,8 |

Sensibilidad 1-D (SpO2 y aporte a los 120 min):

- k 0,50, r 0,50, s 5,00: SpO2 92,7, aporte 0,261, D 49,7; G = k·L sí, aporte ≤ control sí, D ≥ control sí, lactato ≥ control sí
- k 1,00, r 0,00, s 5,00: SpO2 91,5, aporte 0,257, D 50,1; G = k·L sí, aporte ≤ control sí, D ≥ control sí, lactato ≥ control sí
- k 1,00, r 0,50, s 10,00: SpO2 88,9, aporte 0,249, D 51,0; G = k·L sí, aporte ≤ control sí, D ≥ control sí, lactato ≥ control sí
- k 1,00, r 0,50, s 2,50: SpO2 92,7, aporte 0,261, D 49,7; G = k·L sí, aporte ≤ control sí, D ≥ control sí, lactato ≥ control sí
- k 1,00, r 0,50, s 5,00: SpO2 91,5, aporte 0,257, D 50,1; G = k·L sí, aporte ≤ control sí, D ≥ control sí, lactato ≥ control sí
- k 1,00, r 2,00, s 5,00: SpO2 91,5, aporte 0,257, D 50,1; G = k·L sí, aporte ≤ control sí, D ≥ control sí, lactato ≥ control sí
- k 2,00, r 0,50, s 5,00: SpO2 88,9, aporte 0,249, D 51,0; G = k·L sí, aporte ≤ control sí, D ≥ control sí, lactato ≥ control sí

Llegada exacta (SpO2 94): sí. Legado (sólo referencia, nunca objetivo): SpO2 60 min 90, 90 min 88. Cumple: sí.
<!-- /generado:acs -->

## 10. Generación común de congestión (M4, sólo lectura)

<!-- generado:generacion -->
- 1000 mL: L máximo 0,000, G máximo 0,000, posición de precarga máxima 0,555 (rodilla 0,85)
- 4000 mL: L máximo 0,000, G máximo 0,000, posición de precarga máxima 0,686 (rodilla 0,85)

Brecha de generación común de congestión abierta: sí.
<!-- /generado:generacion -->

## 11. No regresión de GI (P2O-1J)

<!-- generado:gi -->
| Caso | Escenario | Perfil | Idéntico | L máx | Escrituras de G |
|---|---|---|---|---|---|
| gi_bleed_57m | untreated | certified | sí | 0,0 | 0 |
| gi_bleed_57m | untreated | acid_base_on | sí | 0,0 | 0 |
| gi_bleed_57m | red_cells | certified | sí | 0,0 | 0 |
| gi_bleed_57m | red_cells | acid_base_on | sí | 0,0 | 0 |
| gi_bleed_57m | crystalloid | certified | sí | 0,0 | 0 |
| gi_bleed_57m | crystalloid | acid_base_on | sí | 0,0 | 0 |
| gi_bleed_57m | stopped_bleed | certified | sí | 0,0 | 0 |
| gi_bleed_57m | stopped_bleed | acid_base_on | sí | 0,0 | 0 |
| gi_bleed_72f | untreated | certified | sí | 0,0 | 0 |
| gi_bleed_72f | untreated | acid_base_on | sí | 0,0 | 0 |
| gi_bleed_72f | red_cells | certified | sí | 0,0 | 0 |
| gi_bleed_72f | red_cells | acid_base_on | sí | 0,0 | 0 |
| gi_bleed_72f | crystalloid | certified | sí | 0,0 | 0 |
| gi_bleed_72f | crystalloid | acid_base_on | sí | 0,0 | 0 |
| gi_bleed_72f | stopped_bleed | certified | sí | 0,0 | 0 |
| gi_bleed_72f | stopped_bleed | acid_base_on | sí | 0,0 | 0 |
<!-- /generado:gi -->

## 12. Conciencia y colapso (P2O-1K, L)

<!-- generado:capas -->
| G | SpO2 | SpO2 que lee la encefalopatía | señal de hipoxemia (rampa sintética) | déficit que lee el colapso |
|---|---|---|---|---|
| 0,0 | 97,0 | 97,0 | 0,000 | 0,5009 |
| 0,5 | 94,5 | 94,5 | 0,000 | 0,5138 |
| 1,0 | 92,0 | 92,0 | 0,143 | 0,5266 |
| 2,0 | 87,0 | 87,0 | 0,500 | 0,5524 |
| 4,0 | 77,0 | 77,0 | 1,000 | 0,6038 |
| 8,0 | 57,0 | 57,0 | 1,000 | 0,7067 |

Conciencia coherente: sí; colapso sin cambios y sólo por el aporte: sí (`DIRECT_SPO2_COLLAPSE_INPUT_DEFERRED`); módulos sin cambios: clinical_core/collapse.py sí, clinical_core/encephalopathy.py sí, clinical_core/ventilation.py sí.
<!-- /generado:capas -->

## 13. Fronteras

<!-- generado:fronteras -->
- Funciones de `derived.py` que leen G: _perfusion; que leen L: lung_water_clearance.
- No leen L ni G: acid_burden_after_minute, alveolar_ventilation, congestion_rate, effective_oxygen_deficit, lactate_after_minute, rate_from_drive, relative_delivery, respiration, respiratory_drive, respiratory_rate, sympathetic_target; `ventilation.py`: sí.
- `oxygenation` lee L, W, D, lactato, FR, PaCO2, ventilación o carga ácida: nada de eso.
- Escritores de G en el núcleo: 1 (el acoplamiento); módulos de familia que escriben G: ninguno.
- Términos de enfermedad en las inserciones del núcleo: ninguno.
- Pasa: sí.
<!-- /generado:fronteras -->

## 14. Prueba del núcleo y paquetes cerrados

<!-- generado:prueba -->
- Los archivos del núcleo son los de P2N-2 byte a byte sin las inserciones declaradas: `clinical_core/derived.py` sí, `clinical_core/integration.py` sí.
- Mapa de dependencias P2N-2 para los paquetes cerrados: 72 archivos, digest `3a64770e85a2…`.
- Registro P2N-2 intacto: sí.
<!-- /generado:prueba -->

## 15. Veredicto

<!-- generado:veredicto -->
| Criterio | Cumple |
|---|---|
| FiO2 response coherent (O5, O6) | sí |
| G can worsen oxygenation (O3, O4) | sí |
| GI unchanged (O1, O12) | sí |
| L can worsen G (O2, cardiogenic) | sí |
| L, G and W causally distinct (boundaries, O3, O4, O7, O8) | sí |
| collapse unchanged (P2M-2 untouched; delivery only) | sí |
| consciousness coherent (one SpO2, its hypoxaemia signal monotone) | sí |
| hypoventilation occurs independently of G (O8, opioid) | sí |
| metabolic acidosis needs no G (O9, metabolic acidosis) | sí |
| no clinical value approved (every new value UNSET by default, SYNTHETIC_ONLY in probes) | sí |
| pneumonia and PE use G without cardiogenic L | sí |
| O10 | sí |
| O11 | sí |
| acs_arrival_exact | sí |
| acs_direction | sí |
| cross_family | sí |

**Veredicto:** `COMMON_GAS_EXCHANGE_ARCHITECTURE_READY_FOR_GENERALIZATION`.
<!-- /generado:veredicto -->

## 16. Recomendación estratégica

<!-- generado:recomendacion -->
**Recomendación:** `CARDIOGENIC_CONGESTION_GENERATION`.

Regla (texto congelado, en inglés): Predeclared. With READY: A (CARDIOGENIC_CONGESTION_GENERATION) when the cardiogenic L -> G -> SpO2 chain acts only on a family-written L, i.e. the common P / V coupling still produces no lung water in the frozen P2N-2 fluid probe (COMMON_CONGESTION_GENERATION_GAP open); B (RESPIRATORY_TREATMENT_COMPOSITION) when the common coupling already produces L there; C and D are outside what P2O-1 can show and are never chosen by it.
<!-- /generado:recomendacion -->

## 17. Diferido y brechas que se arrastran

<!-- generado:diferidos -->
Diferido o no representado (texto congelado, en inglés):

- **alveolar_gas_hypoxaemia**: ALVEOLAR_GAS_OXYGENATION_DEFERRED: hypoventilation raises PaCO2 but lowers no SpO2 (no alveolar gas equation; a faculty decision, TASK 3 (3))
- **collapse_spo2**: DIRECT_SPO2_COLLAPSE_INPUT_DEFERRED (O6)
- **dynamic_mechanics**: W_MECHANICS_DYNAMIC_WRITER_NOT_AVAILABLE: with the acid-base closure on, no channel carries a dynamic ventilatory mechanics; the probes use the P2K-2 structural efficiency (static)
- **family_oxygen_response**: SINGLE_G_OXYGEN_RESPONSE: one r for every family (O2); a family cannot declare a more or less oxygen-responsive G at the same impairment
- **hypoxaemic_drive**: HYPOXAEMIC_DRIVE_DEFERRED: SpO2 reaches RR only through delivery and the acid burden
- **niv**: NIV_NOT_MODELLED (O5)
- **pao2**: PAO2_NOT_REPRESENTED: no dissociation curve; SpO2 is the oxygenation observable
<!-- /generado:diferidos -->

## 18. Decisiones pedidas a la docencia

1. **Valores de k, s y r**, todos UNSET:
   - con un curso de agua pulmonar al aire ambiente sólo se identifica k·s;
   - s sólo se identifica con una familia que escriba G;
   - r sólo con una respuesta al O2 (§6).
2. **Una sola G para todas las familias** (`SINGLE_G_OXYGEN_RESPONSE`). Con una G única, la respuesta al O2 por
   unidad de G es la misma en neumonía y en TEP. Hay que decidir si, antes de migrar esas familias, se necesita una
   fracción refractaria declarada por la familia o dividir G (O2 lo dejó fuera de P2O-1).
3. **Mejoría por debajo de la llegada** (L < 0, G < 0). Hoy no se acredita, porque haría falta la parte de la
   alteración de llegada que se debe a la congestión. Es una decisión para la composición de tratamientos.
4. **Término de gas alveolar.** Sin él, la hipoventilación (opioide) sube la PaCO2 pero no baja la SpO2 al aire
   ambiente (`ALVEOLAR_GAS_OXYGENATION_DEFERRED`; TAREA 3, decisión 3).
5. **Impulso hipoxémico sobre la FR** (TAREA 3, decisión 4).
6. **Mecánica ventilatoria dinámica y significado único de W** (TAREA 3, decisión 5). Hoy el asma y la anafilaxia sólo
   tienen la eficiencia estructural estática.
7. **Término de hipoxemia de la FC.** Ya existía y ahora G lo alcanza: es `sympathetic_per_hypoxaemia_point`
   PROVISIONAL, con un umbral de 94 relativo a la llegada. Hay que confirmar que debe actuar (en el caso ACS suma
   +1,7 lpm a los 120 min).
8. **Paquete siguiente:** generación común de congestión P / V / llenado → L (la M4). Siguen pendientes la M5
   (`ACS_ARRIVAL_HR_COMMON_GAP_CANDIDATE`) y `RV_LV_INTERDEPENDENCE_COMMON_GAP`.

## 19. Limitaciones

- **Valores sintéticos.** Todos los valores son SYNTHETIC_ONLY. Las magnitudes ilustran la dirección y el rango, no
  una calibración.
- **Las familias son sondas, no migraciones.** Se escriben con `bands.Drift` y ajustes estructurales.
  - La de anafilaxia apaga la respuesta de tono: el núcleo rechaza un escritor de T mientras ese tono está activo, y
    cómo se componen sigue sin decidir (P2J-2).
  - La mecánica ventilatoria es la eficiencia estática de P2K-2.
- **r no se discrimina en ACS.** Sólo escala el beneficio del O2, así que al aire ambiente no actúa: el curso ACS no
  la discrimina.
- **Límites de la oxigenación representada:**
  - la SpO2 es lineal en puntos, como el término de FiO2 adoptado del legado;
  - no hay curva de disociación;
  - la PaO2 no está representada;
  - no se modela el O2 disuelto.
- **G = k·max(0, L) depende del integrador.** Se cumple porque el integrador escribe G a partir de L. Un estado que se
  construya fuera del integrador con L ≠ 0 conserva la G que se le dé; las sondas estáticas fijan G directamente. Si
  la guarda de G (±10) actuara, se registraría como un clamp y la igualdad dejaría de cumplirse.
- **Adaptación de los paquetes cerrados.** Se adaptaron 16 archivos de prueba de paquetes cerrados para que sus
  guardas lean el núcleo P2N-2 por la vista demostrada (fixtures y vistas). Ningún registro ni módulo cerrado cambió.
- **Origen del aumento de FC en ACS.** Incluye el término de hipoxemia existente, PROVISIONAL (decisión 7).
