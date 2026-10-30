# P2J-2 · Tono vascular dinámico y superficie de decisión de la presión

- **Fecha:** 2026-10-30. Sólo en sombra. No se integra nada; ninguna ganancia, poscarga ni envolvente se aprueba ni se
  selecciona, y la presión no alimenta la FC.
- **Base:** `f6b4cd0` (P2J-1, cerrado: su módulo y su registro quedan fijados byte a byte, y su congelamiento se
  recalcula con la prueba AST de P2J-2). Congelamiento de P2J-2: `b3b63b1` (digest `baa2ee12…`), antes de evaluar
  las trayectorias clínicas sobre la fisiología retenida; las dos excepciones (una corrida técnica previa y la
  enmienda del congelamiento) están en §21.
- **Números:** `docs/revision/P2J2_vascular_tone.json`. Las secciones marcadas «generado» las escribe
  `python -m clinical_core.vascular_tone_report` desde ese registro.

## Resumen

- **Respuesta de tono común**, con una sola ganancia g para todos los casos. La impulsa la señal aguda s, el déficit
  efectivo de oxígeno sobre la demanda: la misma señal que ya lee el impulso simpático.
  - Respecto del tono sin déficit: T_abs = 1 + g·s.
  - El canal T es relativo a la llegada, así que guarda T = (1 + g·s) / (1 + g·s0), con s0 la señal de llegada.
  - En la llegada T = 1 exactamente: la PAS y la PAD registradas siguen siendo la escala de la relación aceptada, y la
    llegada es el punto fijo de la respuesta.
  - Con déficit 0, T_abs = 1 (el canal vale 1 / (1 + g·s0)).
  - La normalización no elige ningún número por caso, pero en la práctica actúa como un desplazamiento propio de cada
    caso. Lee s0, que sale del nivel de aporte de llegada del lado del lactato, y ese nivel no está aprobado. En las
    unidades retenidas, 57m usa siempre el nivel inferior (s0 = 0,40 con demanda 1,0 y 0,45 con 1,1) y 72f el medio
    (0,15 y 0,23).
  - No lee la presión, D, el lactato ni la FC. Por defecto g = 0, y nada de lo anterior cambia.
- **Temporalidad y lazo:** respuesta instantánea con el retraso del paso. T(m+1) es el objetivo que pide el estado del
  minuto m. El lazo T → poscarga → gasto → aporte → s → T es retroalimentación explícita con un minuto de retraso.
  - Pendiente < g·a: con g·a < 1 es una contracción, con un solo punto fijo y sin oscilación, porque el mapa nunca
    cambia de signo.
  - No hace falta constante de tiempo ni solucionador. El par (g 2, a 0,5) se rechaza analíticamente y el perfil lo
    refuta.
  - En las 1866 claves × 6 ganancias no hay contacto con el guardia, oscilación ni corrida detenida.
- **Hemorragia sin tratamiento (P1, 120 min, a = 0,3, demanda 1,0, medianas):**
  - **57m:** la PAM pasa de 32,4 (T = 1) a 33,9 / 35,2 / 37,2 / 38,8 / 39,9 con g = 0,25 / 0,5 / 1 / 1,5 / 2, es
    decir +1,6 a +7,5 mmHg. La PAS va de 43,6 a 45,7–53,8. El costo es −2 % a −10 % de gasto y de aporte de O₂.
  - **72f:** la PAM pasa de 49,1 a 51,6–65,9 (+2,5 a +16,9), con costo −2 % a −15 %.
  - El apoyo de 57m es menor porque buena parte de su vasoconstricción ya está contenida en la presión de llegada (la
    normalización a la llegada).
- **Reanimación definitiva (P4, 120 min):** el déficit se resuelve y T_abs vuelve a 1. El canal T baja a 1 / (1 + g·s0),
  y el gasto sube porque cae la poscarga: 3–17 % en 57m y 1–10 % en 72f.
  - **57m:** la PAM pasa de 100,7 a 94,1 / 88,3 / 78,6 / 70,9 / 64,5.
  - **72f:** la PAM pasa de 100,7 a 98,1 / 95,6 / 91,1 / 87,0 / 83,2.
  - La sobrepresión baja pero persiste. La PAM a los 120 sobre la de llegada es:
    - 57m: ×1,54 con T = 1, ×1,20 con g = 1, ×1,09 con g = 1,5 y ×0,99 con g = 2 (×0,94 con demanda 1,1);
    - 72f: ×1,12–1,36 con demanda 1,0 y ×1,03–1,36 con 1,1, sin bajar nunca de la llegada.
  - A los 120 el gasto es 1,5–1,8 veces el de llegada en 57m y 1,4–1,5 en 72f: **lo que queda sobre la llegada lo
    pone el gasto (precarga y volumen de la fisiología sanguínea certificada), no el tono.**
- **Caída de la presión en el paciente tratado, causada por la normalización a la llegada:** T baja de 1 en cuanto el
  déficit es menor que el de llegada (s < s0), aunque todavía haya déficit, porque el canal está relativo al tono de
  llegada.
  - En 57m, con g ≥ 1,5, la PAM baja durante la primera unidad de GR: −4,2 mmHg con g = 1,5 y −9,7 con g = 2 (demanda
    1,0).
  - Con g = 2, el 57m tratado (P3/P4) cruza PAS 80 hacia el minuto 22–31, antes que el no tratado con la misma ganancia
    (minuto 39). Con g = 1,5 y demanda 1,1, 9 de 91 claves de P3/P4 cruzan bajo 80.
  - Una constante de tiempo o un término de memoria sólo retrasarían la caída. El nivel final, 1 / (1 + g·s0), es el de
    la normalización. Es decisión docente (§19).
- **Lactato:**
  - La adecuación L3 se mantiene en todas las claves y ganancias.
  - **Demanda 1,0, a = 0,3:** g = 0,25 conserva los 216 candidatos de P2I-2AK; g = 0,5 deja 181, g = 1 deja 134,
    g = 1,5 deja 39 y g = 2 deja 4.
  - **Demanda 1,1:** sólo g = 2 pierde candidatos (quedan 980 de 1092).
  - Un diagnóstico fuera del congelamiento (§13), no committeado, muestra que la única regla que se pierde es
    FD-LAC-06 de 72f en L2.
  - Con a = 0,3, ninguna ganancia vuelve insatisfacibles las restricciones vigentes.
  - Con a = 0,5, en la muestra, g = 1,5 conserva 0 de 36 candidatos a demanda 1,0, y g = 1 conserva 2.
- **FC (diagnóstico):** el tono cambia la FC sólo a través del déficit agudo y de D.
  - Las medianas de la FC en un minuto cambian hasta 6,5 bpm (L3 a los 60 min).
  - El beneficio de la 2.ª unidad de 57m (una diferencia entre corridas) cae 12,5 bpm de mediana con g = 2 a demanda
    1,0.
  - En el rango, la FC de L3 a los 60 min de 57m llega a −24 bpm con g = 2 a demanda 1,1.
  - Las reglas A–F de P2I-2AK seguirían cumpliéndose en la muestra, salvo B en una fila con g = 2 a demanda 1,1.
  - La FC tendría que recertificarse cuando se fije el tono (§14).
- **Veredicto: DYNAMIC_TONE_DECISION_SURFACE_READY.**

## 1. Decisiones docentes registradas (generado)

<!-- generado:decisiones -->
- **poscarga**: a = 0.3 provisional with 0.1 / 0.3 / 0.5 exploratory; none approved; a sparse tone_gain x a design
- **llegada**: the authored arrival BP stays exactly 88/54 (57m) and 98/62 (72f) at minute 0; the response begins from the anchored arrival state; arrival BP never infers the gain
- **fecha**: 2026-10-30
- **demanda**: 1.0 and 1.1 carried separately unless the signal is invariant to demand; never one chosen
- **FC**: pressure -> HR stays DEFERRED; no HR latent selected; P2I-2AK A-F read as a diagnostic, never a filter
- **lactato**: faculty lactate rules unchanged, never recalibrated; if every tone candidate violates the certified lactate physiology, stop
- **lazo**: the T -> afterload -> Q -> DO2 -> deficit -> T loop is audited; deterministic, no hidden iterative convergence, no oscillation, no evaluation-order dependence; a same-step algebraic closure without a guaranteed unique solution stops the package, and no iterative solver is added
- **sin memoria de D**: no accumulated D as a tone driver: tone answers the current acute deficit
- **sin la presión como impulsor**: T is never driven by 1 - relative pressure or another pressure error in P2J-2 (circular before the baroreflex set point and gain exist)
- **rango**: a small gain range (about 4-6 values, 0 included as the synthetic reference) from T_base, the T domain [0.1, 3.0], the normalized deficit range of the certified physiology, broad vasoconstrictor plausibility and fixed-state probes; never from legacy BP, a desired BP or survivor counts; frozen before outcomes
- **alcance**: shadow only; no runtime integration, GI or second-family migration, final tone or afterload approval, hard BP envelope, pressure -> HR reconnection, RR calibration, consciousness recalibration, collapse activation or legacy fitting
- **semántica**: T_base = 1 and a non-negative acute vasoconstrictor increment, T_target = 1 + gain x signal within the T domain; no case-specific offset; no dependence on lactate, HR or legacy pressure; a smooth monotone saturation if one is needed, never a hard clamp as the primary mapping
- **estructura de P2J-1**: P2J-1's mapping is STRUCTURE_APPROVED: p = Q x T, SBP = arrival SBP x max(0, p), DBP = arrival DBP x max(0, p), MAP proportional to p; the p = 0.5 knee and the 45 / 25 mmHg gains stay retired. Not approved: the numerical BP trajectories, T = 1 as clinical physiology, a tone gain, an afterload parameter, any BP envelope
- **temporalidad**: test an instantaneous common response first (deterministic, no algebraic instability, smooth minute to minute); a response time constant is not authorized: if one is structurally required, stop
- **respuesta de tono**: a COMMON dynamic vascular-tone response; primary acute driver the normalized effective oxygen deficit (effective_oxygen_deficit / demand, or an exactly equivalent normalized deficit already in the core); deficit 0 -> acute contribution 0; a larger deficit never lowers the vasoconstrictor contribution; no GI-specific or case-specific coefficient, no legacy BP fitting
<!-- /generado:decisiones -->

## 2. La respuesta de tono (generado)

<!-- generado:tono -->
- **Señal**: s = effective_oxygen_deficit(demand, delivery, reserve) / demand, read on the state (derived.acute_deficit_signal, P2I-2AF; the same signal the sympathetic drive reads): 0 when oxygen availability is adequate or compensated, non-decreasing as the effective deficit grows, at most 1 (no delivery); it reads delivery and demand only
- **Tono absoluto**: tone relative to the tone with no deficit: T_abs = 1 + g x s (g = deficit_to_tone_gain >= 0); T_abs = 1 exactly at no deficit, non-decreasing in s, linear: no saturation is needed because 1 + g <= 3 (ANALYTIC_RULES) keeps it inside T's guard
- **Canal T**: the T channel is relative to arrival (proposal §7.2, P2J-1's anchoring): T = T_abs / T_abs(arrival) = (1 + g s) / (1 + g s0), s0 = derived.arrival_tone_signal (the arrival delivery against the case's baseline demand). T = 1 at arrival exactly, so the authored arrival pressure stays the scale of the accepted mapping and the arrival state is the response's own fixed point; T > 1 while the deficit exceeds arrival's; T = 1 / (1 + g s0) once no deficit is left (T_abs = 1). s0 is read from the arrival state, never fitted: no case offset is chosen
- **Núcleo**: derived.tone_target (the target), integration._vascular_tone (the delta, source core_coupling:vascular_tone); deficit_to_tone_gain 0 writes no delta, so every run before P2J-2 is unchanged
<!-- /generado:tono -->

## 3. Temporalidad, lazo y llegada (generado)

La lectura literal del encargo (T = 1 + g·s en el canal, con T = 1 anclado en la llegada) se rechaza analíticamente.
En toda llegada con déficit (s0 > 0, todas las unidades retenidas), su primera actualización saltaría de 1 a
1 + g·s0 sin que el paciente cambie. Evitar el salto exigiría una constante de tiempo, que no está autorizada. La forma
normalizada cumple la misma ecuación en la escala del tono sin déficit (T_abs = 1 + g·s) y respeta la definición del
canal (llegada = 1). Que esta lectura sea la buscada es la primera decisión que se pide (§19).

<!-- generado:tiempo -->
- **Temporalidad**: Option A, instantaneous: each minute T takes the target the state at the start of the minute calls for, T(m+1) = tone_target(state(m)) (the delta is the target minus T(m)). No time constant: the only lag is the integration step, which the debt D already uses (its deficit is read at the start of the minute). The minute after arrival keeps T = 1 exactly, because the arrival state is the target's fixed point: tone starts to move at minute 2, answering the minute-1 state.
- **Clasificación del lazo**: `EXPLICIT_LAGGED_FEEDBACK`
- **Lazo**: T -> afterload 1 / (1 + a (T - 1)) -> output Q -> delivery -> s -> T, closed one minute behind
- **Mapa**: with the blood state, rhythm and FiO2 given (none reads T or anything derived from it), T(m+1) = F(T(m)) = (1 + g s(T(m))) / (1 + g s0); s rises when T rises (T lowers Q), so F is non-decreasing: the loop is positive feedback and can never alternate in sign
- **Cota**: in a deficit s = 1 - R, R = reserve x delivery / demand < 1, and dR/dT = -a R / (1 + a (T - 1)), so dF/dT = g a R / ((1 + g s0)(1 + a (T - 1))) < g a / (1 + g s0 (1 - a)) <= g a (T >= 1 / (1 + g s0)); outside a deficit dF/dT = 0. g a < 1 makes F a contraction: one fixed point for a steady state, approached monotonically, no oscillation; the amplification at the fixed point is 1 / (1 - dF/dT)
- **Determinismo**: no solver, no iteration inside a minute, no clock or random input; contributors are read from the same start-of-minute state in a fixed order (integration.step), and the tone delta reads only that state, so the result never depends on evaluation order
- **Mismo paso**: not used: a same-minute reading would make T an algebraic fixed point T = F(T) of the minute's own output (no solver is authorized); the explicit scheme converges to that fixed point while the upstream is steady
- **Llegada**: Minute 0 is the anchored arrival (T = 1, the authored SBP / DBP exactly); minute 1 keeps T = 1 (the target read on the arrival state is 1); from minute 2 on T answers the previous minute's state. The arrival BP is never used to infer the gain: it is exact by construction.
- **Alternativa literal**: The literal channel T = 1 + g s with T = 1 anchored at arrival (no arrival normalization) is rejected analytically (ANALYTIC_REJECTION, ARRIVAL_DISCONTINUITY): at any arrival with a deficit (s0 > 0) its first update jumps T from 1 to 1 + g s0 with no change in the patient, raising pressure by (1 + g s0) / (1 + a g s0) in one minute (``literal_alternative``); removing the step would need a response time constant, which is not authorized.
<!-- /generado:tiempo -->

## 4. Superficie congelada y prefiltro analítico (generado)

<!-- generado:superficie -->
Ganancias: 0, 0,25, 0,5, 1, 1,5, 2; poscarga a: 0,1, 0,3, 0,5 (primaria 0,3).

Built before any trajectory, from: T_base = 1 and T's guard [0.1, 3.0]; the normalized acute signal of the certified physiology (P2J-1's sample at T = 1: s0 0 to 0.45 at arrival, s up to 0.74 untreated at 120, 0 once resuscitated), so 1 + g s spans 1 to 1 + 0.74 g; broad vasoconstrictor plausibility (in severe haemorrhagic shock systemic vascular resistance rises to about 1.5-2.5 times its unstressed value, so g up to 2 at s near 0.7 spans the range); and the fixed-state probes. 0 is the synthetic no-response reference (P2J-1's T = 1), kept diagnostic, not a primary candidate; 2 is the largest gain whose largest target 1 + g stays inside the guard. Neither a legacy BP, a desired BP nor a survivor count is read. Every gain is crossed with the three afterload points (the pairwise surface), then screened analytically.

| par (g, a) | cota g·a | estado | motivo |
|---|---|---|---|
| g0 a0.1 | 0.00 | ADMISSIBLE | — |
| g0 a0.3 | 0.00 | ADMISSIBLE | — |
| g0 a0.5 | 0.00 | ADMISSIBLE | — |
| g0.25 a0.1 | 0.03 | ADMISSIBLE | — |
| g0.25 a0.3 | 0.07 | ADMISSIBLE | — |
| g0.25 a0.5 | 0.12 | ADMISSIBLE | — |
| g0.5 a0.1 | 0.05 | ADMISSIBLE | — |
| g0.5 a0.3 | 0.15 | ADMISSIBLE | — |
| g0.5 a0.5 | 0.25 | ADMISSIBLE | — |
| g1 a0.1 | 0.10 | ADMISSIBLE | — |
| g1 a0.3 | 0.30 | ADMISSIBLE | — |
| g1 a0.5 | 0.50 | ADMISSIBLE | — |
| g1.5 a0.1 | 0.15 | ADMISSIBLE | — |
| g1.5 a0.3 | 0.45 | ADMISSIBLE | — |
| g1.5 a0.5 | 0.75 | ADMISSIBLE | — |
| g2 a0.1 | 0.20 | ADMISSIBLE | — |
| g2 a0.3 | 0.60 | ADMISSIBLE | — |
| g2 a0.5 | 1.00 | ANALYTIC_REJECTION | NO_CONTRACTION |
<!-- /generado:superficie -->

## 5. Sondas estructurales 1–8 (generado)

<!-- generado:sondas -->
| sonda | qué comprueba | resultado |
|---|---|---|
| 1 | déficit 0 → T_abs = 1 | sí |
| 2 | el objetivo nunca baja al subir el déficit | sí |
| 3 | más T con precarga, bomba y ritmo fijos baja el gasto | sí |
| 4 | p = Q × T sube con T en todo el guardia | sí |
| 5 | estado estable: T monótono, paso que se achica bajo la cota, punto fijo analítico | sí |
| 6 | al resolverse el déficit T vuelve a T_abs = 1 | sí |
| 7 | sin pulso no hay presión; gasto 0 con pulso detiene la corrida; gasto mínimo, presión mínima | sí |
| 8 | ninguna presión negativa; un minuto desde la llegada intacta conserva T y PAM | sí |

**57m lower x1 (s0 = 0.4)** (s0 = 0.400): en estado estable T sube de forma monótona hasta el punto fijo analítico en todos los pares; la mayor razón entre pasos sucesivos es 0.134 (g1.5 a0.5, cota 0.577). Al resolverse el déficit, T_abs termina en 1 en todos los pares.

**neutral (s0 = 0)** (s0 = 0.000): en estado estable T sube de forma monótona hasta el punto fijo analítico en todos los pares; la mayor razón entre pasos sucesivos es 0.371 (g1.5 a0.5, cota 0.750). Al resolverse el déficit, T_abs termina en 1 en todos los pares.
<!-- /generado:sondas -->

## 6. Llegada: señal s0 por caso, nivel de aporte y demanda (generado)

La señal de llegada depende del nivel de aporte de llegada (lado del lactato) y de la demanda. Por eso el tono, el
gasto, la presión, D y el lactato dependen ahora de la demanda, y 1,0 y 1,1 se llevan por separado. La respuesta empieza
en el minuto 2: los minutos 0 y 1 son la llegada exacta, en cada clave y cada ganancia.

<!-- generado:llegada -->
| caso · nivel de aporte de llegada · demanda | s0 | T_abs de llegada con g = 1 | salto que haría el canal literal en el minuto 1 (g = 1, a = 0,3) |
|---|---|---|---|
| 57m · lower · x1 | 0.400 | 1.400 | ×1.250 PAM |
| 57m · lower · x1.1 | 0.455 | 1.455 | ×1.280 PAM |
| 57m · midpoint · x1 | 0.150 | 1.150 | ×1.100 PAM |
| 57m · midpoint · x1.1 | 0.227 | 1.227 | ×1.149 PAM |
| 57m · upper · x1 | 0.000 | 1.000 | ninguno |
| 57m · upper · x1.1 | 0.091 | 1.091 | ×1.062 PAM |
| 72f · lower · x1 | 0.400 | 1.400 | ×1.250 PAM |
| 72f · lower · x1.1 | 0.455 | 1.455 | ×1.280 PAM |
| 72f · midpoint · x1 | 0.150 | 1.150 | ×1.100 PAM |
| 72f · midpoint · x1.1 | 0.227 | 1.227 | ×1.149 PAM |
| 72f · upper · x1 | 0.000 | 1.000 | ninguno |
| 72f · upper · x1.1 | 0.091 | 1.091 | ×1.062 PAM |
<!-- /generado:llegada -->

## 7. Trayectorias P1–P4 (generado)

<!-- generado:trayectorias -->
**P1 · sin tratamiento (L1) · 57m · demanda 1** (18 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 65.3 | 61.2 | 57.1 | 48.9 | 40.7 | 32.4 | 31.1–41.8 |
| 0.25 | 65.3 | 61.6 | 57.8 | 50.1 | 42.2 | 33.9 | 32.7–43.3 |
| 0.5 | 65.3 | 61.9 | 58.4 | 51.2 | 43.4 | 35.2 | 34.0–44.5 |
| 1 | 65.3 | 62.4 | 59.5 | 52.9 | 45.5 | 37.2 | 36.0–46.5 |
| 1.5 | 65.3 | 62.9 | 60.3 | 54.2 | 47.0 | 38.8 | 37.5–48.0 |
| 2 | 65.3 | 63.2 | 60.9 | 55.2 | 48.2 | 39.9 | 38.6–49.2 |

Intervenciones (mediana): 0: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 30: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 60: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 90: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 120: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U.

**P1 · sin tratamiento (L1) · 57m · demanda 1.1** (37 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 65.3 | 61.4 | 57.7 | 50.6 | 42.3 | 32.6 | 31.1–42.2 |
| 0.25 | 65.3 | 61.7 | 58.2 | 51.6 | 43.6 | 34.0 | 32.5–43.5 |
| 0.5 | 65.3 | 61.9 | 58.7 | 52.4 | 44.7 | 35.1 | 33.7–44.6 |
| 1 | 65.3 | 62.4 | 59.6 | 53.8 | 46.3 | 36.8 | 35.4–46.3 |
| 1.5 | 65.3 | 62.7 | 60.2 | 54.8 | 47.6 | 38.1 | 36.6–47.6 |
| 2 | 65.3 | 63.0 | 60.7 | 55.6 | 48.5 | 39.1 | 37.6–48.5 |

Intervenciones (mediana): 0: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 30: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 60: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 90: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 120: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U.

**P1 · sin tratamiento (L1) · 72f · demanda 1** (18 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 74.0 | 70.9 | 67.8 | 61.6 | 55.4 | 49.1 | 48.2–56.5 |
| 0.25 | 74.0 | 71.3 | 68.7 | 63.2 | 57.5 | 51.6 | 50.7–58.5 |
| 0.5 | 74.0 | 71.8 | 69.5 | 64.7 | 59.6 | 53.9 | 53.0–60.5 |
| 1 | 74.0 | 72.7 | 71.3 | 67.9 | 63.5 | 58.3 | 57.5–64.3 |
| 1.5 | 74.0 | 73.7 | 73.2 | 70.9 | 67.3 | 62.3 | 61.5–68.0 |
| 2 | 74.0 | 74.7 | 75.1 | 74.0 | 70.8 | 65.9 | 65.0–71.5 |

Intervenciones (mediana): 0: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 30: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 60: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 90: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 120: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U.

**P1 · sin tratamiento (L1) · 72f · demanda 1.1** (37 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 74.0 | 71.0 | 68.2 | 62.8 | 56.6 | 49.3 | 48.2–56.5 |
| 0.25 | 74.0 | 71.4 | 68.9 | 64.1 | 58.4 | 51.4 | 50.4–58.4 |
| 0.5 | 74.0 | 71.7 | 69.6 | 65.4 | 60.1 | 53.4 | 52.4–60.1 |
| 1 | 74.0 | 72.4 | 70.9 | 67.7 | 63.1 | 57.0 | 56.0–63.2 |
| 1.5 | 74.0 | 73.1 | 72.2 | 69.8 | 65.9 | 60.1 | 59.1–66.0 |
| 2 | 74.0 | 73.8 | 73.4 | 71.8 | 68.3 | 62.7 | 61.7–68.4 |

Intervenciones (mediana): 0: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 30: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 60: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 90: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 120: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U.

**P2 · 2 L de cristaloide, sangrado activo (L2) · 57m · demanda 1** (216 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 65.3 | 87.5 | 89.6 | 79.5 | 70.6 | 61.8 | 50.4–65.0 |
| 0.25 | 65.3 | 85.4 | 87.2 | 78.6 | 70.5 | 62.4 | 51.7–65.6 |
| 0.5 | 65.3 | 83.5 | 84.9 | 77.8 | 70.5 | 63.0 | 52.8–66.1 |
| 1 | 65.3 | 80.0 | 81.0 | 76.2 | 70.3 | 64.0 | 54.5–67.0 |
| 1.5 | 65.3 | 76.7 | 77.1 | 74.6 | 70.2 | 64.8 | 55.9–67.7 |
| 2 | 65.3 | 73.8 | 73.4 | 73.0 | 69.9 | 65.5 | 57.0–68.2 |

Intervenciones (mediana): 0: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.50 mL/min, cristaloide 300 mL, GR 0.00 U; 30: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U; 60: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U; 90: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U; 120: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U.

**P2 · 2 L de cristaloide, sangrado activo (L2) · 57m · demanda 1.1** (444 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 65.3 | 86.5 | 87.3 | 78.6 | 70.4 | 61.8 | 50.4–65.1 |
| 0.25 | 65.3 | 84.7 | 85.4 | 77.9 | 70.3 | 62.4 | 51.5–65.6 |
| 0.5 | 65.3 | 83.1 | 84.0 | 77.1 | 70.3 | 62.8 | 52.4–66.0 |
| 1 | 65.3 | 80.3 | 81.1 | 75.7 | 70.0 | 63.7 | 53.9–66.7 |
| 1.5 | 65.3 | 77.9 | 78.4 | 74.5 | 69.8 | 64.3 | 55.0–67.3 |
| 2 | 65.3 | 75.7 | 76.0 | 73.7 | 69.6 | 64.7 | 55.9–67.8 |

Intervenciones (mediana): 0: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.50 mL/min, cristaloide 300 mL, GR 0.00 U; 30: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U; 60: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U; 90: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U; 120: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U.

**P2 · 2 L de cristaloide, sangrado activo (L2) · 72f · demanda 1** (216 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 74.0 | 90.7 | 92.3 | 84.7 | 78.0 | 71.3 | 62.7–73.8 |
| 0.25 | 74.0 | 88.9 | 90.2 | 84.1 | 78.1 | 72.3 | 64.5–74.7 |
| 0.5 | 74.0 | 86.8 | 88.1 | 83.3 | 78.3 | 73.4 | 66.2–75.8 |
| 1 | 74.0 | 82.3 | 83.9 | 81.2 | 78.5 | 75.5 | 69.6–77.9 |
| 1.5 | 74.0 | 78.4 | 79.7 | 77.9 | 79.0 | 77.8 | 72.9–80.1 |
| 2 | 74.0 | 75.0 | 76.3 | 76.3 | 79.1 | 80.0 | 76.2–82.4 |

Intervenciones (mediana): 0: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.50 mL/min, cristaloide 300 mL, GR 0.00 U; 30: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U; 60: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U; 90: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U; 120: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U.

**P2 · 2 L de cristaloide, sangrado activo (L2) · 72f · demanda 1.1** (444 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 74.0 | 90.0 | 90.4 | 84.0 | 77.8 | 71.3 | 62.7–73.8 |
| 0.25 | 74.0 | 88.3 | 88.9 | 83.4 | 78.0 | 72.2 | 64.2–74.7 |
| 0.5 | 74.0 | 86.7 | 87.5 | 82.7 | 77.9 | 73.0 | 65.6–75.5 |
| 1 | 74.0 | 82.8 | 83.5 | 81.2 | 78.1 | 74.6 | 68.3–77.2 |
| 1.5 | 74.0 | 79.5 | 79.5 | 79.4 | 78.3 | 76.1 | 70.7–78.8 |
| 2 | 74.0 | 76.0 | 75.3 | 77.6 | 78.4 | 77.6 | 72.9–80.3 |

Intervenciones (mediana): 0: sangrado 2.50 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.50 mL/min, cristaloide 300 mL, GR 0.00 U; 30: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U; 60: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U; 90: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U; 120: sangrado 2.50 mL/min, cristaloide 400 mL, GR 0.00 U.

**P3 · IBP y 2 U de GR sin hemostasia (L3 sin la endoscopia) · 57m · demanda 1** (18 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 65.3 | 77.2 | 86.9 | 101.3 | 98.2 | 94.8 | 94.8–97.4 |
| 0.25 | 65.3 | 75.1 | 82.1 | 94.7 | 91.8 | 88.6 | 88.6–91.0 |
| 0.5 | 65.3 | 73.2 | 77.6 | 88.9 | 86.2 | 83.2 | 83.2–85.4 |
| 1 | 65.3 | 69.7 | 68.3 | 79.1 | 76.7 | 74.1 | 74.1–76.1 |
| 1.5 | 65.3 | 66.7 | 61.2 | 71.3 | 69.2 | 66.8 | 66.8–68.6 |
| 2 | 65.3 | 63.9 | 55.7 | 64.9 | 63.0 | 60.8 | 60.8–62.4 |

Intervenciones (mediana): 0: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.50 U; 30: sangrado 2.00 mL/min, cristaloide 0 mL, GR 1.00 U; 60: sangrado 2.00 mL/min, cristaloide 0 mL, GR 2.00 U; 90: sangrado 2.00 mL/min, cristaloide 0 mL, GR 2.00 U; 120: sangrado 2.00 mL/min, cristaloide 0 mL, GR 2.00 U.

**P3 · IBP y 2 U de GR sin hemostasia (L3 sin la endoscopia) · 57m · demanda 1.1** (91 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 65.3 | 76.5 | 86.7 | 101.3 | 98.2 | 94.8 | 84.6–97.4 |
| 0.25 | 65.3 | 74.9 | 82.6 | 93.8 | 91.0 | 87.8 | 78.8–90.2 |
| 0.5 | 65.3 | 73.5 | 78.6 | 87.4 | 84.7 | 81.8 | 73.1–84.0 |
| 1 | 65.3 | 70.8 | 71.4 | 76.9 | 74.5 | 71.9 | 64.2–73.9 |
| 1.5 | 65.3 | 68.4 | 65.2 | 68.6 | 66.5 | 64.2 | 57.3–65.9 |
| 2 | 65.3 | 66.5 | 59.8 | 61.9 | 60.0 | 57.9 | 51.7–59.5 |

Intervenciones (mediana): 0: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.50 U; 30: sangrado 2.00 mL/min, cristaloide 0 mL, GR 1.00 U; 60: sangrado 2.00 mL/min, cristaloide 0 mL, GR 2.00 U; 90: sangrado 2.00 mL/min, cristaloide 0 mL, GR 2.00 U; 120: sangrado 2.00 mL/min, cristaloide 0 mL, GR 2.00 U.

**P3 · IBP y 2 U de GR sin hemostasia (L3 sin la endoscopia) · 72f · demanda 1** (18 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 74.0 | 82.9 | 90.3 | 101.2 | 98.8 | 96.3 | 96.3–97.9 |
| 0.25 | 74.0 | 80.8 | 88.0 | 98.6 | 96.3 | 93.8 | 93.8–95.4 |
| 0.5 | 74.0 | 78.8 | 85.8 | 96.1 | 93.9 | 91.5 | 91.5–93.0 |
| 1 | 74.0 | 75.1 | 81.7 | 91.6 | 89.4 | 87.1 | 87.1–88.6 |
| 1.5 | 74.0 | 71.7 | 78.0 | 87.4 | 85.4 | 83.2 | 83.2–84.6 |
| 2 | 74.0 | 68.5 | 74.6 | 83.6 | 81.7 | 79.6 | 79.6–80.9 |

Intervenciones (mediana): 0: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.50 U; 30: sangrado 2.00 mL/min, cristaloide 0 mL, GR 1.00 U; 60: sangrado 2.00 mL/min, cristaloide 0 mL, GR 2.00 U; 90: sangrado 2.00 mL/min, cristaloide 0 mL, GR 2.00 U; 120: sangrado 2.00 mL/min, cristaloide 0 mL, GR 2.00 U.

**P3 · IBP y 2 U de GR sin hemostasia (L3 sin la endoscopia) · 72f · demanda 1.1** (91 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 74.0 | 82.3 | 89.9 | 101.2 | 98.8 | 96.3 | 88.4–97.9 |
| 0.25 | 74.0 | 80.3 | 86.5 | 97.3 | 95.1 | 92.6 | 85.0–94.1 |
| 0.5 | 74.0 | 78.1 | 83.3 | 93.7 | 91.6 | 89.2 | 81.9–90.7 |
| 1 | 74.0 | 73.0 | 77.6 | 87.3 | 85.3 | 83.0 | 76.3–84.5 |
| 1.5 | 74.0 | 67.8 | 72.6 | 81.7 | 79.8 | 77.7 | 71.4–79.0 |
| 2 | 74.0 | 62.9 | 68.2 | 76.7 | 75.0 | 73.0 | 67.1–74.3 |

Intervenciones (mediana): 0: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.50 U; 30: sangrado 2.00 mL/min, cristaloide 0 mL, GR 1.00 U; 60: sangrado 2.00 mL/min, cristaloide 0 mL, GR 2.00 U; 90: sangrado 2.00 mL/min, cristaloide 0 mL, GR 2.00 U; 120: sangrado 2.00 mL/min, cristaloide 0 mL, GR 2.00 U.

**P4 · manejo definitivo: IBP, 2 U de GR y hemostasia a los 60 (L3) · 57m · demanda 1** (18 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 65.3 | 77.2 | 86.9 | 101.4 | 101.0 | 100.7 | 100.7–103.5 |
| 0.25 | 65.3 | 75.1 | 82.1 | 94.8 | 94.4 | 94.1 | 94.1–96.7 |
| 0.5 | 65.3 | 73.2 | 77.6 | 88.9 | 88.6 | 88.3 | 88.3–90.8 |
| 1 | 65.3 | 69.7 | 68.3 | 79.2 | 78.9 | 78.6 | 78.6–80.9 |
| 1.5 | 65.3 | 66.7 | 61.2 | 71.4 | 71.1 | 70.9 | 70.9–72.9 |
| 2 | 65.3 | 63.9 | 55.7 | 65.0 | 64.8 | 64.5 | 64.5–66.4 |

Intervenciones (mediana): 0: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.50 U; 30: sangrado 2.00 mL/min, cristaloide 0 mL, GR 1.00 U; 60: sangrado 0.25 mL/min, cristaloide 0 mL, GR 2.00 U; 90: sangrado 0.25 mL/min, cristaloide 0 mL, GR 2.00 U; 120: sangrado 0.25 mL/min, cristaloide 0 mL, GR 2.00 U.

**P4 · manejo definitivo: IBP, 2 U de GR y hemostasia a los 60 (L3) · 57m · demanda 1.1** (91 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 65.3 | 76.5 | 86.7 | 101.4 | 101.0 | 100.7 | 91.7–103.5 |
| 0.25 | 65.3 | 74.9 | 82.6 | 93.9 | 93.6 | 93.2 | 84.9–95.9 |
| 0.5 | 65.3 | 73.5 | 78.6 | 87.5 | 87.2 | 86.8 | 79.1–89.3 |
| 1 | 65.3 | 70.8 | 71.4 | 76.9 | 76.6 | 76.4 | 69.5–78.5 |
| 1.5 | 65.3 | 68.4 | 65.2 | 68.6 | 68.4 | 68.1 | 62.0–70.1 |
| 2 | 65.3 | 66.5 | 59.8 | 62.0 | 61.7 | 61.5 | 56.0–63.3 |

Intervenciones (mediana): 0: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.50 U; 30: sangrado 2.00 mL/min, cristaloide 0 mL, GR 1.00 U; 60: sangrado 0.25 mL/min, cristaloide 0 mL, GR 2.00 U; 90: sangrado 0.25 mL/min, cristaloide 0 mL, GR 2.00 U; 120: sangrado 0.25 mL/min, cristaloide 0 mL, GR 2.00 U.

**P4 · manejo definitivo: IBP, 2 U de GR y hemostasia a los 60 (L3) · 72f · demanda 1** (18 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 74.0 | 82.9 | 90.3 | 101.2 | 101.0 | 100.7 | 100.7–102.5 |
| 0.25 | 74.0 | 80.8 | 88.0 | 98.6 | 98.4 | 98.1 | 98.1–99.8 |
| 0.5 | 74.0 | 78.8 | 85.8 | 96.2 | 95.9 | 95.6 | 95.6–97.3 |
| 1 | 74.0 | 75.1 | 81.7 | 91.6 | 91.4 | 91.1 | 91.1–92.7 |
| 1.5 | 74.0 | 71.7 | 78.0 | 87.5 | 87.2 | 87.0 | 87.0–88.5 |
| 2 | 74.0 | 68.5 | 74.6 | 83.7 | 83.4 | 83.2 | 83.2–84.7 |

Intervenciones (mediana): 0: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.50 U; 30: sangrado 2.00 mL/min, cristaloide 0 mL, GR 1.00 U; 60: sangrado 0.25 mL/min, cristaloide 0 mL, GR 2.00 U; 90: sangrado 0.25 mL/min, cristaloide 0 mL, GR 2.00 U; 120: sangrado 0.25 mL/min, cristaloide 0 mL, GR 2.00 U.

**P4 · manejo definitivo: IBP, 2 U de GR y hemostasia a los 60 (L3) · 72f · demanda 1.1** (91 claves). PAM mediana por minuto; entre corchetes, el rango a los 120.

| g | 0 | 15 | 30 | 60 | 90 | 120 | rango a los 120 |
|---|---|---|---|---|---|---|---|
| 0 | 74.0 | 82.3 | 89.9 | 101.2 | 101.0 | 100.7 | 93.6–102.5 |
| 0.25 | 74.0 | 80.3 | 86.5 | 97.4 | 97.1 | 96.8 | 90.0–98.5 |
| 0.5 | 74.0 | 78.1 | 83.3 | 93.8 | 93.5 | 93.3 | 86.7–94.9 |
| 1 | 74.0 | 73.0 | 77.6 | 87.3 | 87.1 | 86.9 | 80.8–88.4 |
| 1.5 | 74.0 | 67.8 | 72.6 | 81.7 | 81.5 | 81.3 | 75.6–82.7 |
| 2 | 74.0 | 62.9 | 68.2 | 76.8 | 76.6 | 76.4 | 71.0–77.7 |

Intervenciones (mediana): 0: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.00 U; 15: sangrado 2.00 mL/min, cristaloide 0 mL, GR 0.50 U; 30: sangrado 2.00 mL/min, cristaloide 0 mL, GR 1.00 U; 60: sangrado 0.25 mL/min, cristaloide 0 mL, GR 2.00 U; 90: sangrado 0.25 mL/min, cristaloide 0 mL, GR 2.00 U; 120: sangrado 0.25 mL/min, cristaloide 0 mL, GR 2.00 U.
<!-- /generado:trayectorias -->

## 8. Minuto 120 en detalle (generado)

<!-- generado:detalle -->
Minuto 120, a = 0,3, mediana [rango] sobre las claves; Δ y costos contra la referencia T = 1 de la misma clave.

| escenario · caso · demanda | g | T | T_abs | señal s | Q | PAS / PAD | PAM | déficit | D | lactato |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 · 57m · 1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.71 | 0.50 [0.48–0.64] | 43.6 / 26.7 | 32.4 [31.1–41.8] | 0.709 | 192.3 | 9.35 |
| P1 · 57m · 1 | 0.25 | 1.07 [1.05–1.07] | 1.18 [1.16–1.18] | 0.71 | 0.48 [0.47–0.63] | 45.7 / 28.0 | 33.9 [32.7–43.3] | 0.715 | 193.3 | 9.37 |
| P1 · 57m · 1 | 0.5 | 1.13 [1.09–1.14] | 1.36 [1.31–1.36] | 0.72 | 0.48 [0.46–0.62] | 47.4 / 29.1 | 35.2 [34.0–44.5] | 0.720 | 194.2 | 9.40 |
| P1 · 57m · 1 | 1 | 1.23 [1.17–1.24] | 1.72 [1.64–1.73] | 0.73 | 0.46 [0.44–0.61] | 50.2 / 30.8 | 37.2 [36.0–46.5] | 0.728 | 195.5 | 9.43 |
| P1 · 57m · 1 | 1.5 | 1.31 [1.23–1.32] | 2.10 [1.96–2.11] | 0.73 | 0.45 [0.44–0.60] | 52.2 / 32.0 | 38.8 [37.5–48.0] | 0.733 | 196.6 | 9.46 |
| P1 · 57m · 1 | 2 | 1.37 [1.27–1.38] | 2.47 [2.29–2.49] | 0.74 | 0.45 [0.43–0.59] | 53.8 / 33.0 | 39.9 [38.6–49.2] | 0.738 | 197.4 | 9.48 |
| P1 · 57m · 1.1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.73 | 0.50 [0.48–0.65] | 43.9 / 26.9 | 32.6 [31.1–42.2] | 0.806 | 98.6 | 9.01 |
| P1 · 57m · 1.1 | 0.25 | 1.06 [1.04–1.07] | 1.18 [1.16–1.19] | 0.74 | 0.49 [0.47–0.64] | 45.8 / 28.1 | 34.0 [32.5–43.5] | 0.812 | 98.9 | 9.02 |
| P1 · 57m · 1.1 | 0.5 | 1.12 [1.08–1.12] | 1.37 [1.33–1.38] | 0.74 | 0.48 [0.46–0.63] | 47.3 / 29.0 | 35.1 [33.7–44.6] | 0.816 | 99.0 | 9.03 |
| P1 · 57m · 1.1 | 1 | 1.20 [1.14–1.21] | 1.75 [1.66–1.76] | 0.75 | 0.47 [0.45–0.62] | 49.6 / 30.5 | 36.8 [35.4–46.3] | 0.823 | 99.3 | 9.05 |
| P1 · 57m · 1.1 | 1.5 | 1.26 [1.19–1.27] | 2.13 [2.00–2.14] | 0.75 | 0.46 [0.44–0.61] | 51.3 / 31.5 | 38.1 [36.6–47.6] | 0.828 | 99.5 | 9.06 |
| P1 · 57m · 1.1 | 2 | 1.31 [1.23–1.32] | 2.51 [2.34–2.53] | 0.76 | 0.46 [0.43–0.60] | 52.6 / 32.3 | 39.1 [37.6–48.5] | 0.831 | 99.7 | 9.07 |
| P1 · 72f · 1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.45 | 0.66 [0.65–0.76] | 65.0 / 41.1 | 49.1 [48.2–56.5] | 0.447 | 90.7 | 4.80 |
| P1 · 72f · 1 | 0.25 | 1.07 [1.05–1.08] | 1.11 [1.09–1.12] | 0.46 | 0.65 [0.64–0.75] | 68.3 / 43.2 | 51.6 [50.7–58.5] | 0.459 | 92.3 | 4.84 |
| P1 · 72f · 1 | 0.5 | 1.15 [1.10–1.15] | 1.23 [1.19–1.24] | 0.47 | 0.64 [0.62–0.74] | 71.4 / 45.2 | 53.9 [53.0–60.5] | 0.470 | 94.0 | 4.88 |
| P1 · 72f · 1 | 1 | 1.29 [1.21–1.30] | 1.49 [1.39–1.50] | 0.49 | 0.61 [0.60–0.72] | 77.3 / 48.9 | 58.3 [57.5–64.3] | 0.492 | 97.2 | 4.97 |
| P1 · 72f · 1 | 1.5 | 1.44 [1.32–1.45] | 1.76 [1.62–1.78] | 0.51 | 0.59 [0.57–0.70] | 82.5 / 52.2 | 62.3 [61.5–68.0] | 0.511 | 100.4 | 5.05 |
| P1 · 72f · 1 | 2 | 1.58 [1.43–1.59] | 2.05 [1.85–2.07] | 0.53 | 0.57 [0.55–0.68] | 87.3 / 55.2 | 65.9 [65.0–71.5] | 0.529 | 103.4 | 5.13 |
| P1 · 72f · 1.1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.49 | 0.67 [0.65–0.76] | 65.2 / 41.3 | 49.3 [48.2–56.5] | 0.542 | 43.3 | 4.34 |
| P1 · 72f · 1.1 | 0.25 | 1.06 [1.05–1.07] | 1.13 [1.11–1.13] | 0.50 | 0.65 [0.64–0.75] | 68.1 / 43.1 | 51.4 [50.4–58.4] | 0.553 | 43.7 | 4.36 |
| P1 · 72f · 1.1 | 0.5 | 1.13 [1.09–1.13] | 1.25 [1.21–1.26] | 0.51 | 0.64 [0.63–0.74] | 70.8 / 44.8 | 53.4 [52.4–60.1] | 0.563 | 44.0 | 4.37 |
| P1 · 72f · 1.1 | 1 | 1.24 [1.17–1.25] | 1.53 [1.44–1.54] | 0.53 | 0.62 [0.61–0.73] | 75.5 / 47.8 | 57.0 [56.0–63.2] | 0.580 | 44.6 | 4.41 |
| P1 · 72f · 1.1 | 1.5 | 1.35 [1.25–1.36] | 1.81 [1.68–1.83] | 0.54 | 0.60 [0.59–0.71] | 79.5 / 50.3 | 60.1 [59.1–66.0] | 0.595 | 45.2 | 4.44 |
| P1 · 72f · 1.1 | 2 | 1.44 [1.33–1.46] | 2.10 [1.93–2.13] | 0.55 | 0.59 [0.57–0.70] | 83.1 / 52.5 | 62.7 [61.7–68.4] | 0.608 | 45.7 | 4.47 |
| P2 · 57m · 1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.48 | 0.95 [0.77–1.00] | 83.2 / 51.1 | 61.8 [50.4–65.0] | 0.476 | 142.4 | 7.88 |
| P2 · 57m · 1 | 0.25 | 1.02 [1.01–1.04] | 1.12 [1.11–1.14] | 0.48 | 0.94 [0.76–0.99] | 84.1 / 51.6 | 62.4 [51.7–65.6] | 0.479 | 141.7 | 7.84 |
| P2 · 57m · 1 | 0.5 | 1.03 [1.02–1.07] | 1.24 [1.22–1.28] | 0.48 | 0.94 [0.76–0.99] | 84.9 / 52.1 | 63.0 [52.8–66.1] | 0.481 | 141.0 | 7.81 |
| P2 · 57m · 1 | 1 | 1.06 [1.03–1.12] | 1.48 [1.44–1.57] | 0.49 | 0.93 [0.74–0.99] | 86.2 / 52.9 | 64.0 [54.5–67.0] | 0.485 | 139.8 | 7.76 |
| P2 · 57m · 1 | 1.5 | 1.08 [1.04–1.17] | 1.73 [1.66–1.87] | 0.49 | 0.92 [0.73–0.98] | 87.3 / 53.6 | 64.8 [55.9–67.7] | 0.488 | 138.7 | 7.71 |
| P2 · 57m · 1 | 2 | 1.10 [1.05–1.20] | 1.98 [1.88–2.17] | 0.49 | 0.92 [0.73–0.98] | 88.2 / 54.1 | 65.5 [57.0–68.2] | 0.491 | 137.7 | 7.66 |
| P2 · 57m · 1.1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.52 | 0.95 [0.77–1.00] | 83.2 / 51.1 | 61.8 [50.4–65.1] | 0.568 | 86.9 | 8.30 |
| P2 · 57m · 1.1 | 0.25 | 1.01 [1.01–1.03] | 1.13 [1.12–1.15] | 0.52 | 0.94 [0.76–0.99] | 84.0 / 51.5 | 62.4 [51.5–65.6] | 0.571 | 86.8 | 8.29 |
| P2 · 57m · 1.1 | 0.5 | 1.03 [1.01–1.06] | 1.26 [1.24–1.30] | 0.52 | 0.94 [0.76–0.99] | 84.6 / 51.9 | 62.8 [52.4–66.0] | 0.573 | 86.6 | 8.28 |
| P2 · 57m · 1.1 | 1 | 1.05 [1.02–1.11] | 1.52 [1.49–1.61] | 0.52 | 0.93 [0.75–0.99] | 85.8 / 52.6 | 63.7 [53.9–66.7] | 0.576 | 86.4 | 8.25 |
| P2 · 57m · 1.1 | 1.5 | 1.06 [1.03–1.14] | 1.79 [1.74–1.92] | 0.53 | 0.93 [0.74–0.99] | 86.6 / 53.1 | 64.3 [55.0–67.3] | 0.578 | 86.1 | 8.24 |
| P2 · 57m · 1.1 | 2 | 1.07 [1.04–1.17] | 2.05 [1.98–2.24] | 0.53 | 0.93 [0.73–0.98] | 87.2 / 53.5 | 64.7 [55.9–67.8] | 0.580 | 86.0 | 8.22 |
| P2 · 72f · 1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.24 | 0.96 [0.85–1.00] | 94.4 / 59.8 | 71.3 [62.7–73.8] | 0.241 | 48.3 | 3.57 |
| P2 · 72f · 1 | 0.25 | 1.02 [1.01–1.04] | 1.06 [1.05–1.08] | 0.25 | 0.96 [0.84–0.99] | 95.8 / 60.6 | 72.3 [64.5–74.7] | 0.246 | 47.7 | 3.53 |
| P2 · 72f · 1 | 0.5 | 1.05 [1.03–1.08] | 1.12 [1.10–1.17] | 0.25 | 0.95 [0.83–0.99] | 97.1 / 61.5 | 73.4 [66.2–75.8] | 0.251 | 46.9 | 3.49 |
| P2 · 72f · 1 | 1 | 1.09 [1.05–1.17] | 1.26 [1.21–1.35] | 0.26 | 0.94 [0.81–0.98] | 100.0 / 63.2 | 75.5 [69.6–77.9] | 0.262 | 41.3 | 3.19 |
| P2 · 72f · 1 | 1.5 | 1.15 [1.08–1.26] | 1.40 [1.32–1.55] | 0.27 | 0.92 [0.79–0.97] | 103.0 / 65.2 | 77.8 [72.9–80.1] | 0.273 | 34.1 | 2.82 |
| P2 · 72f · 1 | 2 | 1.20 [1.11–1.35] | 1.56 [1.45–1.76] | 0.28 | 0.91 [0.77–0.96] | 106.0 / 67.1 | 80.0 [76.2–82.4] | 0.284 | 29.4 | 2.63 |
| P2 · 72f · 1.1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.30 | 0.96 [0.85–1.00] | 94.4 / 59.8 | 71.3 [62.7–73.8] | 0.334 | 33.3 | 3.73 |
| P2 · 72f · 1.1 | 0.25 | 1.02 [1.01–1.04] | 1.08 [1.07–1.10] | 0.31 | 0.96 [0.84–0.99] | 95.6 / 60.5 | 72.2 [64.2–74.7] | 0.338 | 33.1 | 3.72 |
| P2 · 72f · 1.1 | 0.5 | 1.04 [1.02–1.07] | 1.15 [1.14–1.20] | 0.31 | 0.95 [0.83–0.99] | 96.7 / 61.2 | 73.0 [65.6–75.5] | 0.342 | 33.0 | 3.71 |
| P2 · 72f · 1.1 | 1 | 1.07 [1.04–1.14] | 1.32 [1.28–1.40] | 0.32 | 0.94 [0.81–0.98] | 98.8 / 62.5 | 74.6 [68.3–77.2] | 0.350 | 32.7 | 3.68 |
| P2 · 72f · 1.1 | 1.5 | 1.11 [1.06–1.21] | 1.48 [1.43–1.62] | 0.32 | 0.93 [0.80–0.98] | 100.8 / 63.8 | 76.1 [70.7–78.8] | 0.357 | 32.4 | 3.65 |
| P2 · 72f · 1.1 | 2 | 1.14 [1.08–1.27] | 1.66 [1.58–1.85] | 0.33 | 0.92 [0.78–0.97] | 102.7 / 65.0 | 77.6 [72.9–80.3] | 0.364 | 31.9 | 3.61 |
| P3 · 57m · 1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.00 | 1.45 [1.45–1.49] | 127.7 / 78.4 | 94.8 [94.8–97.4] | 0.000 | 4.8 | 3.96 |
| P3 · 57m · 1 | 0.25 | 0.91 [0.91–0.91] | 1.00 [1.00–1.00] | 0.00 | 1.49 [1.49–1.53] | 119.4 / 73.2 | 88.6 [88.6–91.0] | 0.000 | 4.3 | 3.85 |
| P3 · 57m · 1 | 0.5 | 0.83 [0.83–0.83] | 1.00 [1.00–1.00] | 0.00 | 1.53 [1.53–1.57] | 112.0 / 68.7 | 83.2 [83.2–85.4] | 0.000 | 4.0 | 3.78 |
| P3 · 57m · 1 | 1 | 0.71 [0.71–0.71] | 1.00 [1.00–1.00] | 0.00 | 1.59 [1.59–1.63] | 99.8 / 61.2 | 74.1 [74.1–76.1] | 0.000 | 3.4 | 3.64 |
| P3 · 57m · 1 | 1.5 | 0.62 [0.62–0.62] | 1.00 [1.00–1.00] | 0.00 | 1.64 [1.64–1.68] | 89.9 / 55.2 | 66.8 [66.8–68.6] | 0.000 | 3.2 | 3.57 |
| P3 · 57m · 1 | 2 | 0.56 [0.56–0.56] | 1.00 [1.00–1.00] | 0.00 | 1.67 [1.67–1.72] | 81.9 / 50.2 | 60.8 [60.8–62.4] | 0.000 | 2.9 | 3.50 |
| P3 · 57m · 1.1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.01 | 1.45 [1.30–1.49] | 127.7 / 78.4 | 94.8 [84.6–97.4] | 0.014 | 10.0 | 3.78 |
| P3 · 57m · 1.1 | 0.25 | 0.90 [0.90–0.90] | 1.00 [1.00–1.01] | 0.00 | 1.50 [1.33–1.54] | 118.3 / 72.6 | 87.8 [78.8–90.2] | 0.000 | 6.0 | 3.53 |
| P3 · 57m · 1.1 | 0.5 | 0.81 [0.81–0.82] | 1.00 [1.00–1.00] | 0.00 | 1.54 [1.37–1.58] | 110.2 / 67.6 | 81.8 [73.1–84.0] | 0.000 | 5.4 | 3.38 |
| P3 · 57m · 1.1 | 1 | 0.69 [0.69–0.69] | 1.00 [1.00–1.00] | 0.00 | 1.60 [1.43–1.64] | 96.9 / 59.4 | 71.9 [64.2–73.9] | 0.000 | 4.5 | 3.15 |
| P3 · 57m · 1.1 | 1.5 | 0.59 [0.59–0.59] | 1.00 [1.00–1.00] | 0.00 | 1.65 [1.47–1.70] | 86.4 / 53.0 | 64.2 [57.3–65.9] | 0.000 | 4.0 | 3.02 |
| P3 · 57m · 1.1 | 2 | 0.52 [0.52–0.52] | 1.00 [1.00–1.00] | 0.00 | 1.69 [1.51–1.74] | 78.0 / 47.9 | 57.9 [51.7–59.5] | 0.000 | 3.8 | 2.93 |
| P3 · 72f · 1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.00 | 1.30 [1.30–1.32] | 127.5 / 80.6 | 96.3 [96.3–97.9] | 0.000 | 0.6 | 2.08 |
| P3 · 72f · 1 | 0.25 | 0.96 [0.96–0.96] | 1.00 [1.00–1.00] | 0.00 | 1.32 [1.32–1.34] | 124.2 / 78.6 | 93.8 [93.8–95.4] | 0.000 | 0.6 | 2.07 |
| P3 · 72f · 1 | 0.5 | 0.93 [0.93–0.93] | 1.00 [1.00–1.00] | 0.00 | 1.33 [1.33–1.35] | 121.1 / 76.6 | 91.5 [91.5–93.0] | 0.000 | 0.5 | 2.06 |
| P3 · 72f · 1 | 1 | 0.87 [0.87–0.87] | 1.00 [1.00–1.00] | 0.00 | 1.35 [1.35–1.38] | 115.4 / 73.0 | 87.1 [87.1–88.6] | 0.000 | 0.5 | 2.05 |
| P3 · 72f · 1 | 1.5 | 0.82 [0.82–0.82] | 1.00 [1.00–1.00] | 0.00 | 1.38 [1.38–1.40] | 110.1 / 69.7 | 83.2 [83.2–84.6] | 0.000 | 0.5 | 2.04 |
| P3 · 72f · 1 | 2 | 0.77 [0.77–0.77] | 1.00 [1.00–1.00] | 0.00 | 1.40 [1.40–1.42] | 105.4 / 66.7 | 79.6 [79.6–80.9] | 0.000 | 0.5 | 2.03 |
| P3 · 72f · 1.1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.00 | 1.30 [1.19–1.32] | 127.5 / 80.6 | 96.3 [88.4–97.9] | 0.000 | 0.8 | 1.57 |
| P3 · 72f · 1.1 | 0.25 | 0.95 [0.95–0.95] | 1.00 [1.00–1.00] | 0.00 | 1.32 [1.21–1.34] | 122.6 / 77.6 | 92.6 [85.0–94.1] | 0.000 | 0.7 | 1.55 |
| P3 · 72f · 1.1 | 0.5 | 0.90 [0.90–0.90] | 1.00 [1.00–1.00] | 0.00 | 1.34 [1.23–1.36] | 118.1 / 74.7 | 89.2 [81.9–90.7] | 0.000 | 0.7 | 1.54 |
| P3 · 72f · 1.1 | 1 | 0.81 [0.81–0.81] | 1.00 [1.00–1.00] | 0.00 | 1.38 [1.26–1.40] | 110.0 / 69.6 | 83.0 [76.3–84.5] | 0.000 | 0.7 | 1.52 |
| P3 · 72f · 1.1 | 1.5 | 0.75 [0.75–0.75] | 1.00 [1.00–1.00] | 0.00 | 1.41 [1.29–1.43] | 102.9 / 65.1 | 77.7 [71.4–79.0] | 0.000 | 0.6 | 1.50 |
| P3 · 72f · 1.1 | 2 | 0.69 [0.69–0.69] | 1.00 [1.00–1.00] | 0.00 | 1.44 [1.32–1.46] | 96.7 / 61.2 | 73.0 [67.1–74.3] | 0.000 | 0.6 | 1.48 |
| P4 · 57m · 1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.00 | 1.54 [1.54–1.58] | 135.6 / 83.2 | 100.7 [100.7–103.5] | 0.000 | 4.8 | 3.96 |
| P4 · 57m · 1 | 0.25 | 0.91 [0.91–0.91] | 1.00 [1.00–1.00] | 0.00 | 1.58 [1.58–1.63] | 126.7 / 77.8 | 94.1 [94.1–96.7] | 0.000 | 4.3 | 3.85 |
| P4 · 57m · 1 | 0.5 | 0.83 [0.83–0.83] | 1.00 [1.00–1.00] | 0.00 | 1.62 [1.62–1.67] | 118.9 / 73.0 | 88.3 [88.3–90.8] | 0.000 | 4.0 | 3.78 |
| P4 · 57m · 1 | 1 | 0.71 [0.71–0.71] | 1.00 [1.00–1.00] | 0.00 | 1.69 [1.69–1.73] | 105.9 / 65.0 | 78.6 [78.6–80.9] | 0.000 | 3.4 | 3.64 |
| P4 · 57m · 1 | 1.5 | 0.62 [0.62–0.62] | 1.00 [1.00–1.00] | 0.00 | 1.74 [1.74–1.79] | 95.5 / 58.6 | 70.9 [70.9–72.9] | 0.000 | 3.2 | 3.57 |
| P4 · 57m · 1 | 2 | 0.56 [0.56–0.56] | 1.00 [1.00–1.00] | 0.00 | 1.78 [1.78–1.83] | 86.9 / 53.3 | 64.5 [64.5–66.4] | 0.000 | 2.9 | 3.50 |
| P4 · 57m · 1.1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.00 | 1.54 [1.40–1.58] | 135.6 / 83.2 | 100.7 [91.7–103.5] | 0.000 | 6.9 | 3.74 |
| P4 · 57m · 1.1 | 0.25 | 0.90 [0.90–0.90] | 1.00 [1.00–1.00] | 0.00 | 1.59 [1.45–1.63] | 125.6 / 77.1 | 93.2 [84.9–95.9] | 0.000 | 6.0 | 3.53 |
| P4 · 57m · 1.1 | 0.5 | 0.81 [0.81–0.81] | 1.00 [1.00–1.00] | 0.00 | 1.63 [1.49–1.68] | 117.0 / 71.8 | 86.8 [79.1–89.3] | 0.000 | 5.4 | 3.38 |
| P4 · 57m · 1.1 | 1 | 0.69 [0.69–0.69] | 1.00 [1.00–1.00] | 0.00 | 1.70 [1.55–1.75] | 102.9 / 63.1 | 76.4 [69.5–78.5] | 0.000 | 4.5 | 3.15 |
| P4 · 57m · 1.1 | 1.5 | 0.59 [0.59–0.59] | 1.00 [1.00–1.00] | 0.00 | 1.75 [1.60–1.80] | 91.8 / 56.3 | 68.1 [62.0–70.1] | 0.000 | 4.0 | 3.02 |
| P4 · 57m · 1.1 | 2 | 0.52 [0.52–0.52] | 1.00 [1.00–1.00] | 0.00 | 1.80 [1.64–1.85] | 82.9 / 50.8 | 61.5 [56.0–63.3] | 0.000 | 3.8 | 2.93 |
| P4 · 72f · 1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.00 | 1.36 [1.36–1.38] | 133.3 / 84.3 | 100.7 [100.7–102.5] | 0.000 | 0.6 | 2.08 |
| P4 · 72f · 1 | 0.25 | 0.96 [0.96–0.96] | 1.00 [1.00–1.00] | 0.00 | 1.38 [1.38–1.40] | 129.9 / 82.2 | 98.1 [98.1–99.8] | 0.000 | 0.6 | 2.07 |
| P4 · 72f · 1 | 0.5 | 0.93 [0.93–0.93] | 1.00 [1.00–1.00] | 0.00 | 1.39 [1.39–1.41] | 126.7 / 80.1 | 95.6 [95.6–97.3] | 0.000 | 0.5 | 2.06 |
| P4 · 72f · 1 | 1 | 0.87 [0.87–0.87] | 1.00 [1.00–1.00] | 0.00 | 1.42 [1.42–1.44] | 120.7 / 76.3 | 91.1 [91.1–92.7] | 0.000 | 0.5 | 2.05 |
| P4 · 72f · 1 | 1.5 | 0.82 [0.82–0.82] | 1.00 [1.00–1.00] | 0.00 | 1.44 [1.44–1.47] | 115.2 / 72.9 | 87.0 [87.0–88.5] | 0.000 | 0.5 | 2.04 |
| P4 · 72f · 1 | 2 | 0.77 [0.77–0.77] | 1.00 [1.00–1.00] | 0.00 | 1.46 [1.46–1.49] | 110.2 / 69.7 | 83.2 [83.2–84.7] | 0.000 | 0.5 | 2.03 |
| P4 · 72f · 1.1 | 0 | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 0.00 | 1.36 [1.27–1.38] | 133.3 / 84.3 | 100.7 [93.6–102.5] | 0.000 | 0.8 | 1.57 |
| P4 · 72f · 1.1 | 0.25 | 0.95 [0.95–0.95] | 1.00 [1.00–1.00] | 0.00 | 1.38 [1.29–1.41] | 128.2 / 81.1 | 96.8 [90.0–98.5] | 0.000 | 0.7 | 1.55 |
| P4 · 72f · 1.1 | 0.5 | 0.90 [0.90–0.90] | 1.00 [1.00–1.00] | 0.00 | 1.40 [1.31–1.43] | 123.5 / 78.1 | 93.3 [86.7–94.9] | 0.000 | 0.7 | 1.54 |
| P4 · 72f · 1.1 | 1 | 0.81 [0.81–0.81] | 1.00 [1.00–1.00] | 0.00 | 1.44 [1.34–1.47] | 115.0 / 72.8 | 86.9 [80.8–88.4] | 0.000 | 0.7 | 1.52 |
| P4 · 72f · 1.1 | 1.5 | 0.75 [0.75–0.75] | 1.00 [1.00–1.00] | 0.00 | 1.47 [1.37–1.50] | 107.6 / 68.1 | 81.3 [75.6–82.7] | 0.000 | 0.6 | 1.50 |
| P4 · 72f · 1.1 | 2 | 0.69 [0.69–0.69] | 1.00 [1.00–1.00] | 0.00 | 1.50 [1.40–1.53] | 101.1 / 64.0 | 76.4 [71.0–77.7] | 0.000 | 0.6 | 1.48 |
<!-- /generado:detalle -->

## 9. Hemorragia sin tratamiento: presión ganada y su costo (generado)

<!-- generado:sin_tratamiento -->
| caso · demanda | g | PAS a los 120 | PAM a los 120 | ΔPAM vs T = 1 | ΔPAS vs T = 1 | costo de Q | costo de aporte | Δ déficit | ΔD |
|---|---|---|---|---|---|---|---|---|---|
| 57m · 1 | 0 | 43.6 [42.0–56.3] | 32.4 [31.1–41.8] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 % [0.0–0.0] | 0.0 % [0.0–0.0] | 0.000 | 0.00 |
| 57m · 1 | 0.25 | 45.7 [44.0–58.3] | 33.9 [32.7–43.3] | 1.6 [1.5–1.6] | 2.1 [2.0–2.1] | −2.1 % [−2.1–−1.5] | −2.1 % [−2.1–−1.5] | 0.006 | 0.98 |
| 57m · 1 | 0.5 | 47.4 [45.8–60.0] | 35.2 [34.0–44.5] | 2.9 [2.7–2.9] | 3.8 [3.6–3.9] | −3.8 % [−3.9–−2.8] | −3.8 % [−3.9–−2.8] | 0.011 | 1.81 |
| 57m · 1 | 1 | 50.2 [48.5–62.7] | 37.2 [36.0–46.5] | 4.9 [4.7–4.9] | 6.6 [6.3–6.6] | −6.5 % [−6.7–−4.8] | −6.5 % [−6.7–−4.8] | 0.019 | 3.17 |
| 57m · 1 | 1.5 | 52.2 [50.5–64.7] | 38.8 [37.5–48.0] | 6.4 [6.2–6.4] | 8.6 [8.3–8.7] | −8.5 % [−8.7–−6.3] | −8.5 % [−8.7–−6.3] | 0.025 | 4.21 |
| 57m · 1 | 2 | 53.8 [52.0–66.3] | 39.9 [38.6–49.2] | 7.5 [7.4–7.6] | 10.1 [9.9–10.2] | −10.0 % [−10.3–−7.6] | −10.0 % [−10.3–−7.6] | 0.029 | 5.05 |
| 57m · 1.1 | 0 | 43.9 [42.0–56.9] | 32.6 [31.1–42.2] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 % [0.0–0.0] | 0.0 % [0.0–0.0] | 0.000 | 0.00 |
| 57m · 1.1 | 0.25 | 45.8 [43.8–58.6] | 34.0 [32.5–43.5] | 1.4 [1.3–1.4] | 1.9 [1.8–1.9] | −1.9 % [−1.9–−1.3] | −1.9 % [−1.9–−1.3] | 0.005 | 0.21 |
| 57m · 1.1 | 0.5 | 47.3 [45.3–60.1] | 35.1 [33.7–44.6] | 2.5 [2.4–2.6] | 3.4 [3.2–3.4] | −3.4 % [−3.5–−2.4] | −3.4 % [−3.5–−2.4] | 0.010 | 0.39 |
| 57m · 1.1 | 1 | 49.6 [47.7–62.4] | 36.8 [35.4–46.3] | 4.2 [4.1–4.3] | 5.7 [5.5–5.8] | −5.7 % [−5.9–−4.1] | −5.7 % [−5.9–−4.1] | 0.017 | 0.67 |
| 57m · 1.1 | 1.5 | 51.3 [49.3–64.1] | 38.1 [36.6–47.6] | 5.5 [5.3–5.6] | 7.4 [7.2–7.5] | −7.3 % [−7.6–−5.4] | −7.3 % [−7.6–−5.4] | 0.021 | 0.88 |
| 57m · 1.1 | 2 | 52.6 [50.6–65.4] | 39.1 [37.6–48.5] | 6.4 [6.3–6.5] | 8.6 [8.5–8.8] | −8.6 % [−8.9–−6.4] | −8.6 % [−8.9–−6.4] | 0.025 | 1.04 |
| 72f · 1 | 0 | 65.0 [63.8–74.8] | 49.1 [48.2–56.5] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 % [0.0–0.0] | 0.0 % [0.0–0.0] | 0.000 | 0.00 |
| 72f · 1 | 0.25 | 68.3 [67.1–77.5] | 51.6 [50.7–58.5] | 2.5 [2.0–2.5] | 3.3 [2.7–3.3] | −2.2 % [−2.2–−1.5] | −2.2 % [−2.2–−1.5] | 0.012 | 1.67 |
| 72f · 1 | 0.5 | 71.4 [70.3–80.1] | 53.9 [53.0–60.5] | 4.9 [4.0–4.9] | 6.4 [5.3–6.5] | −4.2 % [−4.4–−3.0] | −4.2 % [−4.4–−3.0] | 0.023 | 3.32 |
| 72f · 1 | 1 | 77.3 [76.1–85.2] | 58.3 [57.5–64.3] | 9.3 [7.8–9.4] | 12.3 [10.4–12.4] | −8.1 % [−8.3–−5.9] | −8.1 % [−8.3–−5.9] | 0.045 | 6.57 |
| 72f · 1 | 1.5 | 82.5 [81.4–90.1] | 62.3 [61.5–68.0] | 13.3 [11.5–13.4] | 17.6 [15.2–17.7] | −11.6 % [−11.9–−8.7] | −11.6 % [−11.9–−8.7] | 0.064 | 9.72 |
| 72f · 1 | 2 | 87.3 [86.1–94.7] | 65.9 [65.0–71.5] | 16.9 [14.9–17.0] | 22.4 [19.8–22.5] | −14.7 % [−15.1–−11.3] | −14.7 % [−15.1–−11.3] | 0.082 | 12.74 |
| 72f · 1.1 | 0 | 65.2 [63.8–74.9] | 49.3 [48.2–56.5] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 % [0.0–0.0] | 0.0 % [0.0–0.0] | 0.000 | 0.00 |
| 72f · 1.1 | 0.25 | 68.1 [66.7–77.3] | 51.4 [50.4–58.4] | 2.2 [1.8–2.2] | 2.9 [2.4–3.0] | −1.9 % [−2.0–−1.4] | −1.9 % [−2.0–−1.4] | 0.011 | 0.36 |
| 72f · 1.1 | 0.5 | 70.8 [69.4–79.5] | 53.4 [52.4–60.1] | 4.2 [3.5–4.3] | 5.6 [4.6–5.7] | −3.7 % [−3.8–−2.6] | −3.7 % [−3.8–−2.6] | 0.020 | 0.70 |
| 72f · 1.1 | 1 | 75.5 [74.2–83.7] | 57.0 [56.0–63.2] | 7.8 [6.6–7.9] | 10.3 [8.7–10.5] | −6.8 % [−7.0–−5.0] | −6.8 % [−7.0–−5.0] | 0.038 | 1.33 |
| 72f · 1.1 | 1.5 | 79.5 [78.3–87.4] | 60.1 [59.1–66.0] | 10.8 [9.3–11.0] | 14.4 [12.3–14.6] | −9.5 % [−9.8–−7.1] | −9.5 % [−9.8–−7.1] | 0.053 | 1.91 |
| 72f · 1.1 | 2 | 83.1 [81.7–90.6] | 62.7 [61.7–68.4] | 13.5 [11.8–13.7] | 17.8 [15.6–18.1] | −11.8 % [−12.2–−8.9] | −11.8 % [−12.2–−8.9] | 0.066 | 2.42 |
<!-- /generado:sin_tratamiento -->

## 10. Reanimación definitiva: qué sostiene la presión a los 120 (generado)

PAM / PAM de llegada = Q × T exactamente. Con T < 1, lo que queda sobre la llegada lo pone el gasto.

<!-- generado:definitivo -->
| caso · demanda | g | T | T_abs | Q | PAS / PAD | PAM | ΔPAM vs T = 1 | PAM / PAM de llegada | parte del gasto (Q) | parte del tono (T) |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m · 1 | 0 | 1.00 | 1.00 | 1.54 | 135.6 / 83.2 | 100.7 | 0.0 | ×1.54 | ×1.54 | ×1.00 |
| 57m · 1 | 0.25 | 0.91 | 1.00 | 1.58 | 126.7 / 77.8 | 94.1 | −6.6 | ×1.44 | ×1.58 | ×0.91 |
| 57m · 1 | 0.5 | 0.83 | 1.00 | 1.62 | 118.9 / 73.0 | 88.3 | −12.4 | ×1.35 | ×1.62 | ×0.83 |
| 57m · 1 | 1 | 0.71 | 1.00 | 1.69 | 105.9 / 65.0 | 78.6 | −22.0 | ×1.20 | ×1.69 | ×0.71 |
| 57m · 1 | 1.5 | 0.62 | 1.00 | 1.74 | 95.5 / 58.6 | 70.9 | −29.8 | ×1.08 | ×1.74 | ×0.62 |
| 57m · 1 | 2 | 0.56 | 1.00 | 1.78 | 86.9 / 53.3 | 64.5 | −36.1 | ×0.99 | ×1.78 | ×0.56 |
| 57m · 1.1 | 0 | 1.00 | 1.00 | 1.54 | 135.6 / 83.2 | 100.7 | 0.0 | ×1.54 | ×1.54 | ×1.00 |
| 57m · 1.1 | 0.25 | 0.90 | 1.00 | 1.59 | 125.6 / 77.1 | 93.2 | −7.4 | ×1.43 | ×1.59 | ×0.90 |
| 57m · 1.1 | 0.5 | 0.81 | 1.00 | 1.63 | 117.0 / 71.8 | 86.8 | −13.8 | ×1.33 | ×1.63 | ×0.81 |
| 57m · 1.1 | 1 | 0.69 | 1.00 | 1.70 | 102.9 / 63.1 | 76.4 | −24.3 | ×1.17 | ×1.70 | ×0.69 |
| 57m · 1.1 | 1.5 | 0.59 | 1.00 | 1.75 | 91.8 / 56.3 | 68.1 | −32.5 | ×1.04 | ×1.75 | ×0.59 |
| 57m · 1.1 | 2 | 0.52 | 1.00 | 1.80 | 82.9 / 50.8 | 61.5 | −39.1 | ×0.94 | ×1.80 | ×0.52 |
| 72f · 1 | 0 | 1.00 | 1.00 | 1.36 | 133.3 / 84.3 | 100.7 | 0.0 | ×1.36 | ×1.36 | ×1.00 |
| 72f · 1 | 0.25 | 0.96 | 1.00 | 1.38 | 129.9 / 82.2 | 98.1 | −2.6 | ×1.33 | ×1.38 | ×0.96 |
| 72f · 1 | 0.5 | 0.93 | 1.00 | 1.39 | 126.7 / 80.1 | 95.6 | −5.0 | ×1.29 | ×1.39 | ×0.93 |
| 72f · 1 | 1 | 0.87 | 1.00 | 1.42 | 120.7 / 76.3 | 91.1 | −9.6 | ×1.23 | ×1.42 | ×0.87 |
| 72f · 1 | 1.5 | 0.82 | 1.00 | 1.44 | 115.2 / 72.9 | 87.0 | −13.7 | ×1.18 | ×1.44 | ×0.82 |
| 72f · 1 | 2 | 0.77 | 1.00 | 1.46 | 110.2 / 69.7 | 83.2 | −17.5 | ×1.12 | ×1.46 | ×0.77 |
| 72f · 1.1 | 0 | 1.00 | 1.00 | 1.36 | 133.3 / 84.3 | 100.7 | 0.0 | ×1.36 | ×1.36 | ×1.00 |
| 72f · 1.1 | 0.25 | 0.95 | 1.00 | 1.38 | 128.2 / 81.1 | 96.8 | −3.9 | ×1.31 | ×1.38 | ×0.95 |
| 72f · 1.1 | 0.5 | 0.90 | 1.00 | 1.40 | 123.5 / 78.1 | 93.3 | −7.4 | ×1.26 | ×1.40 | ×0.90 |
| 72f · 1.1 | 1 | 0.81 | 1.00 | 1.44 | 115.0 / 72.8 | 86.9 | −13.8 | ×1.17 | ×1.44 | ×0.81 |
| 72f · 1.1 | 1.5 | 0.75 | 1.00 | 1.47 | 107.6 / 68.1 | 81.3 | −19.4 | ×1.10 | ×1.47 | ×0.75 |
| 72f · 1.1 | 2 | 0.69 | 1.00 | 1.50 | 101.1 / 64.0 | 76.4 | −24.3 | ×1.03 | ×1.50 | ×0.69 |
<!-- /generado:definitivo -->

## 11. Presión frente a perfusión (generado)

<!-- generado:intercambio -->
Per admissible (gain, a), predeclared: UNSTABLE_FEEDBACK when a SIMULATION_RULES rejection occurs on any key; else PRESSURE_SUPPORTED_AT_DELIVERY_COST when a retained unit that passes FD-LAC and L3 adequacy at T = 1 fails them with the tone response (a faculty-approved outcome lost to the delivery the tone takes); else PRESSURE_SUPPORTED_WITH_STABLE_DELIVERY. The continuous costs (output, delivery, deficit and D against the T = 1 reference) are reported for every pair, with no threshold: the faculty sets the acceptable cost (envelope I). At a = 0.1 and 0.5 the FD-LAC part reads the sample units only (SAMPLE_ONLY).

| par (g, a) | clasificación | candidatos perdidos (FD-LAC / adecuación) | alcance | rechazos de simulación |
|---|---|---|---|---|
| g0 a0.1 | referencia T = 1 | — | — | — |
| g0 a0.3 | referencia T = 1 | — | — | — |
| g0 a0.5 | referencia T = 1 | — | — | — |
| g0.25 a0.1 | presión sostenida sin perder candidatos FD-LAC (el aporte baja igual: §9) | 0 | sólo la muestra | — |
| g0.25 a0.3 | presión sostenida sin perder candidatos FD-LAC (el aporte baja igual: §9) | 0 | todas las unidades retenidas | — |
| g0.25 a0.5 | presión sostenida con costo de aporte | 4 | sólo la muestra | — |
| g0.5 a0.1 | presión sostenida sin perder candidatos FD-LAC (el aporte baja igual: §9) | 0 | sólo la muestra | — |
| g0.5 a0.3 | presión sostenida con costo de aporte | 35 | todas las unidades retenidas | — |
| g0.5 a0.5 | presión sostenida con costo de aporte | 13 | sólo la muestra | — |
| g1 a0.1 | presión sostenida sin perder candidatos FD-LAC (el aporte baja igual: §9) | 0 | sólo la muestra | — |
| g1 a0.3 | presión sostenida con costo de aporte | 82 | todas las unidades retenidas | — |
| g1 a0.5 | presión sostenida con costo de aporte | 34 | sólo la muestra | — |
| g1.5 a0.1 | presión sostenida con costo de aporte | 4 | sólo la muestra | — |
| g1.5 a0.3 | presión sostenida con costo de aporte | 177 | todas las unidades retenidas | — |
| g1.5 a0.5 | presión sostenida con costo de aporte | 68 | sólo la muestra | — |
| g2 a0.1 | presión sostenida con costo de aporte | 7 | sólo la muestra | — |
| g2 a0.3 | presión sostenida con costo de aporte | 324 | todas las unidades retenidas | — |
| g2 a0.5 | rechazo analítico | — | — | — |
<!-- /generado:intercambio -->

## 12. D y lactato: compatibilidad con FD-LAC (generado)

En la tabla de §8, D sube con el tono sin tratamiento y baja tras la reanimación, cuando el canal cae bajo 1 y el gasto
sube. El lactato a los 120 cambia poco (+0,13 mmol/L en 57m y +0,32 en 72f con g = 2 en P1; −0,46 en 57m en P4).

<!-- generado:lactato -->
| demanda | a | g | candidatos que conservan FD-LAC y adecuación L3 | de | unidades con algún candidato |
|---|---|---|---|---|---|
| 1 | 0,3 | 0 | 216 | 216 | 18 de 18 |
| 1 | 0,3 | 0.25 | 216 | 216 | 18 de 18 |
| 1 | 0,3 | 0.5 | 181 | 216 | 18 de 18 |
| 1 | 0,3 | 1 | 134 | 216 | 18 de 18 |
| 1 | 0,3 | 1.5 | 39 | 216 | 11 de 18 |
| 1 | 0,3 | 2 | 4 | 216 | 2 de 18 |
| 1.1 | 0,3 | 0 | 1092 | 1092 | 37 de 37 |
| 1.1 | 0,3 | 0.25 | 1092 | 1092 | 37 de 37 |
| 1.1 | 0,3 | 0.5 | 1092 | 1092 | 37 de 37 |
| 1.1 | 0,3 | 1 | 1092 | 1092 | 37 de 37 |
| 1.1 | 0,3 | 1.5 | 1092 | 1092 | 37 de 37 |
| 1.1 | 0,3 | 2 | 980 | 1092 | 37 de 37 |
| 1 | 0,1 | 0 | 36 | 36 | 3 de 3 |
| 1 | 0,1 | 0.25 | 36 | 36 | 3 de 3 |
| 1 | 0,1 | 0.5 | 36 | 36 | 3 de 3 |
| 1 | 0,1 | 1 | 36 | 36 | 3 de 3 |
| 1 | 0,1 | 1.5 | 32 | 36 | 3 de 3 |
| 1 | 0,1 | 2 | 29 | 36 | 3 de 3 |
| 1.1 | 0,1 | 0 | 108 | 108 | 3 de 3 |
| 1.1 | 0,1 | 0.25 | 108 | 108 | 3 de 3 |
| 1.1 | 0,1 | 0.5 | 108 | 108 | 3 de 3 |
| 1.1 | 0,1 | 1 | 108 | 108 | 3 de 3 |
| 1.1 | 0,1 | 1.5 | 108 | 108 | 3 de 3 |
| 1.1 | 0,1 | 2 | 108 | 108 | 3 de 3 |
| 1 | 0,5 | 0 | 36 | 36 | 3 de 3 |
| 1 | 0,5 | 0.25 | 32 | 36 | 3 de 3 |
| 1 | 0,5 | 0.5 | 23 | 36 | 3 de 3 |
| 1 | 0,5 | 1 | 2 | 36 | 1 de 3 |
| 1 | 0,5 | 1.5 | 0 | 36 | 0 de 3 |
| 1.1 | 0,5 | 0 | 108 | 108 | 3 de 3 |
| 1.1 | 0,5 | 0.25 | 108 | 108 | 3 de 3 |
| 1.1 | 0,5 | 0.5 | 108 | 108 | 3 de 3 |
| 1.1 | 0,5 | 1 | 108 | 108 | 3 de 3 |
| 1.1 | 0,5 | 1.5 | 76 | 108 | 3 de 3 |
<!-- /generado:lactato -->

## 13. Qué regla de lactato se pierde (diagnóstico fuera del congelamiento)

Un script de scratch reutiliza las mismas funciones que `vascular_tone._fd_task` (las de `lactate_closure` sin
cambios) y sólo decodifica los bits de la máscara que la tarea congelada descarta. No forma parte del registro.

Resultado (candidatos perdidos con a = 0,3), todos por FD-LAC-06 de 72f en L2 (cristaloide con sangrado activo):

| demanda | g | candidatos perdidos |
|---|---|---|
| 1,0 | 0,5 | 35 |
| 1,0 | 1 | 82 |
| 1,0 | 1,5 | 177 |
| 1,0 | 2 | 212 |
| 1,1 | 2 | 112 |

FD-LAC-06 prohíbe que el lactato baje en una ventana de déficit crítico persistente o creciente mientras hay sangrado.
El costo de aporte del tono alarga o profundiza esa ventana en 72f. No se descompuso más el mecanismo.

## 14. FC: impacto indirecto (generado)

La FC cambia sólo a través del déficit agudo y de D. Presión → FC sigue en 0 en el perfil primario.

<!-- generado:fc -->
Diagnóstico, nunca filtro: corridas completas de la muestra (L1, L3 y los dos contrafactuales), a = 0,3, bajo las combinaciones latentes primarias del grupo de P2I-2AK en cada demanda; cambio de la FC contra g = 0 en bpm (mediana [rango]) y reglas A–F que fallarían.

| demanda | g | caso | filas | L1 a los 120 | L3 a los 60 | L3 a los 90 | L3 a los 120 | beneficio de la 1.ª unidad | beneficio de la 2.ª unidad | A–F que fallan |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 57m | 6 | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | ninguna |
| 1 | 0 | 72f | 6 | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | ninguna |
| 1 | 0.25 | 57m | 6 | 0.2 [0.1–0.2] | −1.1 [−1.2–−1.1] | −0.4 [−0.4–−0.4] | −0.2 [−0.2–−0.2] | 0.7 [0.6–0.8] | 0.2 [0.1–0.3] | ninguna |
| 1 | 0.25 | 72f | 6 | 0.6 [0.4–0.7] | −0.0 [−0.1–−0.0] | −0.0 [−0.0–−0.0] | −0.0 [−0.0–−0.0] | 0.2 [0.1–0.3] | 0.0 [0.0–0.0] | ninguna |
| 1 | 0.5 | 57m | 6 | 0.4 [0.1–0.4] | −1.9 [−1.9–−1.8] | −0.7 [−0.7–−0.7] | −0.3 [−0.3–−0.2] | 1.4 [1.2–1.5] | 0.0 [−0.2–0.2] | ninguna |
| 1 | 0.5 | 72f | 6 | 1.1 [0.9–1.3] | −0.1 [−0.1–−0.1] | −0.0 [−0.0–−0.0] | −0.0 [−0.0–−0.0] | 0.4 [0.4–0.6] | 0.0 [0.0–0.0] | ninguna |
| 1 | 1 | 57m | 6 | 0.6 [0.3–0.6] | −2.9 [−3.2–−2.8] | −1.1 [−1.2–−1.0] | −0.4 [−0.4–−0.4] | 2.7 [2.4–2.8] | −2.4 [−4.9–−0.6] | ninguna |
| 1 | 1 | 72f | 6 | 2.2 [1.7–2.5] | −0.2 [−0.2–−0.1] | −0.1 [−0.1–−0.0] | −0.0 [−0.0–−0.0] | 0.9 [0.8–1.0] | 0.0 [0.0–0.0] | ninguna |
| 1 | 1.5 | 57m | 6 | 0.8 [0.3–0.8] | −3.7 [−3.8–−3.6] | −1.4 [−1.4–−1.3] | −0.5 [−0.5–−0.5] | 3.9 [3.5–4.2] | −10.9 [−12.4–−10.0] | ninguna |
| 1 | 1.5 | 72f | 6 | 3.3 [2.5–3.6] | −0.2 [−0.2–−0.2] | −0.1 [−0.1–−0.1] | −0.0 [−0.0–−0.0] | 1.3 [1.2–1.5] | 0.0 [0.0–0.0] | ninguna |
| 1 | 2 | 57m | 6 | 0.9 [0.4–1.0] | −4.2 [−4.3–−4.1] | −1.6 [−1.6–−1.5] | −0.6 [−0.6–−0.6] | 5.0 [4.5–5.3] | −12.5 [−13.5–−12.4] | ninguna |
| 1 | 2 | 72f | 6 | 4.3 [3.2–4.6] | −0.2 [−0.2–−0.2] | −0.1 [−0.1–−0.1] | −0.0 [−0.0–−0.0] | 1.8 [1.6–1.9] | 0.0 [0.0–0.0] | ninguna |
| 1.1 | 0 | 57m | 27 | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | ninguna |
| 1.1 | 0 | 72f | 27 | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | 0.0 [0.0–0.0] | ninguna |
| 1.1 | 0.25 | 57m | 27 | 0.1 [0.1–0.3] | −1.6 [−5.7–−0.4] | −0.8 [−4.0–−0.1] | −0.3 [−1.5–−0.0] | 0.5 [0.1–2.0] | 0.9 [−1.3–5.2] | ninguna |
| 1.1 | 0.25 | 72f | 27 | 0.4 [0.1–0.8] | −0.1 [−0.5–−0.0] | −0.0 [−0.2–−0.0] | −0.0 [−0.1–−0.0] | 0.6 [0.2–1.2] | 0.0 [0.0–0.0] | ninguna |
| 1.1 | 0.5 | 57m | 27 | 0.2 [0.1–0.6] | −2.9 [−9.8–−0.7] | −1.3 [−6.2–−0.2] | −0.5 [−2.3–−0.1] | 0.9 [0.3–3.9] | 1.4 [−2.7–8.8] | ninguna |
| 1.1 | 0.5 | 72f | 27 | 0.7 [0.3–1.5] | −0.2 [−0.8–−0.0] | −0.1 [−0.3–−0.0] | −0.0 [−0.1–−0.0] | 1.2 [0.4–1.9] | 0.0 [0.0–0.0] | ninguna |
| 1.1 | 1 | 57m | 27 | 0.4 [0.2–1.1] | −4.5 [−16.6–−1.1] | −1.9 [−9.3–−0.4] | −0.7 [−3.5–−0.1] | 1.7 [0.5–7.3] | 1.2 [−5.5–14.7] | ninguna |
| 1.1 | 1 | 72f | 27 | 1.3 [0.5–2.8] | −0.4 [−1.5–−0.1] | −0.1 [−0.6–−0.0] | −0.0 [−0.2–−0.0] | 2.0 [0.7–3.7] | 0.0 [0.0–0.0] | ninguna |
| 1.1 | 1.5 | 57m | 27 | 0.6 [0.3–1.4] | −5.6 [−20.5–−1.4] | −2.3 [−11.0–−0.5] | −0.9 [−4.1–−0.2] | 2.4 [0.7–10.4] | −0.0 [−8.3–17.8] | ninguna |
| 1.1 | 1.5 | 72f | 27 | 1.7 [0.8–3.9] | −0.5 [−2.0–−0.1] | −0.2 [−0.7–−0.0] | −0.1 [−0.3–−0.0] | 2.7 [0.9–4.9] | 0.0 [0.0–0.0] | ninguna |
| 1.1 | 2 | 57m | 27 | 0.7 [0.4–1.6] | −6.5 [−24.1–−1.6] | −2.7 [−12.5–−0.6] | −1.0 [−4.6–−0.2] | 3.0 [0.9–13.3] | −0.6 [−11.1–20.6] | B (1) |
| 1.1 | 2 | 72f | 27 | 2.2 [1.0–4.9] | −0.5 [−2.2–−0.1] | −0.2 [−0.8–−0.0] | −0.1 [−0.3–−0.0] | 3.3 [1.1–5.6] | 0.0 [0.0–0.0] | B (1) |

Mayor |cambio| de la FC en cualquier lectura y fila: demanda 1, g 0.25: 1.2 bpm; demanda 1, g 0.5: 1.9 bpm; demanda 1, g 1: 4.9 bpm; demanda 1, g 1.5: 12.4 bpm; demanda 1, g 2: 13.5 bpm; demanda 1.1, g 0.25: 5.7 bpm; demanda 1.1, g 0.5: 9.8 bpm; demanda 1.1, g 1: 16.6 bpm; demanda 1.1, g 1.5: 20.5 bpm; demanda 1.1, g 2: 24.1 bpm.
<!-- /generado:fc -->

## 15. Umbrales de conciencia (generado)

<!-- generado:conciencia -->
Umbrales vigentes de PAS (80 → nivel 1, 65 → nivel 2), sin recalibrar: claves que los cruzan alguna vez y minuto mediano del primer cruce.

| escenario · caso · demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| P1 · 57m · 1 | <80: 18/18 (min 22); <65: 18/18 (min 63) | <80: 18/18 (min 24); <65: 18/18 (min 68) | <80: 18/18 (min 26); <65: 18/18 (min 72) | <80: 18/18 (min 31); <65: 18/18 (min 80) | <80: 18/18 (min 35); <65: 18/18 (min 86) | <80: 18/18 (min 39); <65: 14/18 (min 90) |
| P1 · 57m · 1.1 | <80: 37/37 (min 23); <65: 37/37 (min 69) | <80: 37/37 (min 25); <65: 37/37 (min 74) | <80: 37/37 (min 27); <65: 37/37 (min 77) | <80: 37/37 (min 31); <65: 37/37 (min 83) | <80: 37/37 (min 35); <65: 37/37 (min 88) | <80: 37/37 (min 39); <65: 31/37 (min 90) |
| P1 · 72f · 1 | <80: 18/18 (min 66); <65: 8/18 (min 117) | <80: 18/18 (min 75); <65: 0/18 | <80: 14/18 (min 86); <65: 0/18 | <80: 14/18 (min 109); <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 |
| P1 · 72f · 1.1 | <80: 37/37 (min 73); <65: 12/37 (min 117) | <80: 37/37 (min 81); <65: 0/37 | <80: 37/37 (min 89); <65: 0/37 | <80: 21/37 (min 101); <65: 0/37 | <80: 21/37 (min 118); <65: 0/37 | <80: 0/37; <65: 0/37 |
| P2 · 57m · 1 | <80: 68/216 (min 111); <65: 0/216 | <80: 60/216 (min 111); <65: 0/216 | <80: 46/216 (min 113); <65: 0/216 | <80: 32/216 (min 112); <65: 0/216 | <80: 18/216 (min 109); <65: 0/216 | <80: 14/216 (min 113); <65: 0/216 |
| P2 · 57m · 1.1 | <80: 126/444 (min 111); <65: 0/444 | <80: 110/444 (min 111); <65: 0/444 | <80: 87/444 (min 111); <65: 0/444 | <80: 58/444 (min 111); <65: 0/444 | <80: 54/444 (min 114); <65: 0/444 | <80: 34/444 (min 110); <65: 0/444 |
| P2 · 72f · 1 | <80: 0/216; <65: 0/216 | <80: 0/216; <65: 0/216 | <80: 0/216; <65: 0/216 | <80: 0/216; <65: 0/216 | <80: 0/216; <65: 0/216 | <80: 0/216; <65: 0/216 |
| P2 · 72f · 1.1 | <80: 0/444; <65: 0/444 | <80: 0/444; <65: 0/444 | <80: 0/444; <65: 0/444 | <80: 0/444; <65: 0/444 | <80: 0/444; <65: 0/444 | <80: 0/444; <65: 0/444 |
| P3 · 57m · 1 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 18/18 (min 22); <65: 0/18 |
| P3 · 57m · 1.1 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 9/91 (min 39); <65: 0/91 | <80: 91/91 (min 31); <65: 0/91 |
| P3 · 72f · 1 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 |
| P3 · 72f · 1.1 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 |
| P4 · 57m · 1 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 18/18 (min 22); <65: 0/18 |
| P4 · 57m · 1.1 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 9/91 (min 39); <65: 0/91 | <80: 91/91 (min 31); <65: 0/91 |
| P4 · 72f · 1 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 | <80: 0/18; <65: 0/18 |
| P4 · 72f · 1.1 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 | <80: 0/91; <65: 0/91 |
<!-- /generado:conciencia -->

## 16. Propuestas de envolventes A–I para la docencia (generado)

Ninguna se aplica ni se aprueba. No se propone ningún número: más allá de la llegada no hay presión registrada, así que
un número saldría del propio modelo.

<!-- generado:envolventes -->
Each proposal shows the model distribution (LOW / median / HIGH over the retained keys, per gain at a = 0.3 and per demand), the T = 1 reference, the physiological rationale, its sensitivity to the gain (the medians across gains), to a (the sample at a = 0.1 / 0.3 / 0.5) and to demand (1.0 against 1.1), and the basis of any bound: PHYSIOLOGICAL for a direction the physiology fixes, EXPLORATORY for a number (none is proposed: no authored pressure exists beyond arrival, so a number would come from the model itself), EVIDENCE for an authored observation (none). No envelope is applied or approved.

**A. untreated 57m SBP / MAP at 120** — PROPOSED_NOT_APPROVED. Fundamento: ongoing haemorrhage with compensatory vasoconstriction: pressure supported against the T = 1 reference, never normalized (direction 5). Base de un límite: PHYSIOLOGICAL (direction); EXPLORATORY (no numeric bound proposed); no EVIDENCE beyond arrival.

*57m* — PAM, PAS:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 32.4 [31.1–41.8]; 43.6 [42.0–56.3] | 33.9 [32.7–43.3]; 45.7 [44.0–58.3] | 35.2 [34.0–44.5]; 47.4 [45.8–60.0] | 37.2 [36.0–46.5]; 50.2 [48.5–62.7] | 38.8 [37.5–48.0]; 52.2 [50.5–64.7] | 39.9 [38.6–49.2]; 53.8 [52.0–66.3] |
| 1.1 | 32.6 [31.1–42.2]; 43.9 [42.0–56.9] | 34.0 [32.5–43.5]; 45.8 [43.8–58.6] | 35.1 [33.7–44.6]; 47.3 [45.3–60.1] | 36.8 [35.4–46.3]; 49.6 [47.7–62.4] | 38.1 [36.6–47.6]; 51.3 [49.3–64.1] | 39.1 [37.6–48.5]; 52.6 [50.6–65.4] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 32.4, 43.6 / 32.4, 43.6 / 32.4, 43.6; x1 g1: 38.7, 52.1 / 37.2, 50.2 / 35.8, 48.2; x1 g1.5: 40.6, 54.7 / 38.8, 52.2 / 36.9, 49.6; x1 g2: 42.2, 56.8 / 39.9, 53.8; x1.1 g0: 41.8, 56.3 / 41.8, 56.3 / 41.8, 56.3; x1.1 g1: 47.0, 63.3 / 45.9, 61.8 / 44.8, 60.3; x1.1 g1.5: 48.5, 65.4 / 47.2, 63.5 / 45.7, 61.6; x1.1 g2: 49.7, 67.0 / 48.1, 64.8.

**B. untreated 72f SBP / MAP at 120** — PROPOSED_NOT_APPROVED. Fundamento: as A, for the 72f course. Base de un límite: PHYSIOLOGICAL (direction); EXPLORATORY (no numeric bound proposed); no EVIDENCE beyond arrival.

*72f* — PAM, PAS:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 49.1 [48.2–56.5]; 65.0 [63.8–74.8] | 51.6 [50.7–58.5]; 68.3 [67.1–77.5] | 53.9 [53.0–60.5]; 71.4 [70.3–80.1] | 58.3 [57.5–64.3]; 77.3 [76.1–85.2] | 62.3 [61.5–68.0]; 82.5 [81.4–90.1] | 65.9 [65.0–71.5]; 87.3 [86.1–94.7] |
| 1.1 | 49.3 [48.2–56.5]; 65.2 [63.8–74.9] | 51.4 [50.4–58.4]; 68.1 [66.7–77.3] | 53.4 [52.4–60.1]; 70.8 [69.4–79.5] | 57.0 [56.0–63.2]; 75.5 [74.2–83.7] | 60.1 [59.1–66.0]; 79.5 [78.3–87.4] | 62.7 [61.7–68.4]; 83.1 [81.7–90.6] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 49.1, 65.0 / 49.1, 65.0 / 49.1, 65.0; x1 g1: 60.5, 80.2 / 58.3, 77.3 / 55.9, 74.0; x1 g1.5: 65.4, 86.5 / 62.3, 82.5 / 58.8, 77.8; x1 g2: 69.7, 92.3 / 65.9, 87.3; x1.1 g0: 56.5, 74.8 / 56.5, 74.8 / 56.5, 74.8; x1.1 g1: 64.4, 85.3 / 63.0, 83.5 / 61.4, 81.4; x1.1 g1.5: 67.5, 89.4 / 65.8, 87.1 / 63.6, 84.3; x1.1 g2: 70.2, 92.9 / 68.2, 90.4.

**C. pressure response to crystalloid** — PROPOSED_NOT_APPROVED. Fundamento: MAP at the minute the crystalloid volume reaches its total less MAP the minute before it starts (net of the bleeding meanwhile); tone falls as delivery recovers, so the response is smaller than at T = 1. Base de un límite: PHYSIOLOGICAL (direction); EXPLORATORY (no numeric bound proposed); no EVIDENCE beyond arrival.

*57m* — ΔPAM, ΔPAS:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 27.3 [21.6–28.1]; 36.8 [29.0–37.8] | 24.6 [19.5–25.6]; 33.2 [26.3–34.5] | 22.3 [17.5–23.3]; 30.0 [23.6–31.4] | 17.6 [14.0–19.1]; 23.7 [18.9–25.7] | 13.1 [10.8–15.2]; 17.6 [14.6–20.5] | 9.2 [7.9–11.7]; 12.4 [10.7–15.7] |
| 1.1 | 25.9 [19.4–28.1]; 34.9 [26.1–37.8] | 23.6 [17.8–25.9]; 31.8 [24.0–34.9] | 21.6 [16.4–23.9]; 29.1 [22.1–32.2] | 18.1 [13.9–20.4]; 24.4 [18.8–27.5] | 14.7 [11.9–17.5]; 19.8 [16.0–23.6] | 12.1 [10.1–14.9]; 16.3 [13.7–20.1] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 25.9, 34.9 / 25.9, 34.9 / 25.9, 34.9; x1 g1: 15.6, 20.9 / 16.5, 22.2 / 17.7, 23.8; x1 g1.5: 12.0, 16.2 / 12.4, 16.7 / 12.6, 17.0; x1 g2: 9.1, 12.3 / 8.7, 11.7; x1.1 g0: 22.2, 29.9 / 22.2, 29.9 / 22.2, 29.9; x1.1 g1: 14.6, 19.7 / 15.5, 20.9 / 16.7, 22.4; x1.1 g1.5: 12.2, 16.5 / 13.0, 17.5 / 14.0, 18.8; x1.1 g2: 10.8, 14.5 / 11.3, 15.2.

*72f* — ΔPAM, ΔPAS:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 20.6 [16.1–21.2]; 27.3 [21.3–28.1] | 18.4 [14.2–19.2]; 24.3 [18.8–25.4] | 16.1 [12.2–17.0]; 21.4 [16.1–22.5] | 11.6 [7.5–12.2]; 15.4 [10.0–16.1] | 7.8 [3.8–8.3]; 10.3 [5.1–10.9] | 4.2 [0.4–4.7]; 5.6 [0.6–6.2] |
| 1.1 | 19.6 [14.6–21.2]; 25.9 [19.4–28.1] | 17.5 [13.2–19.4]; 23.2 [17.5–25.7] | 15.5 [11.8–17.6]; 20.5 [15.6–23.3] | 10.7 [8.7–13.7]; 14.1 [11.5–18.2] | 6.2 [4.0–10.2]; 8.2 [5.3–13.5] | 1.7 [−2.8–7.1]; 2.2 [−3.7–9.4] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 19.6, 25.9 / 19.6, 25.9 / 19.6, 25.9; x1 g1: 8.7, 11.6 / 10.7, 14.1 / 13.0, 17.3; x1 g1.5: 3.8, 5.0 / 6.8, 9.0 / 10.1, 13.4; x1 g2: −0.3, −0.4 / 3.3, 4.4; x1.1 g0: 16.5, 21.9 / 16.5, 21.9 / 16.5, 21.9; x1.1 g1: 9.5, 12.5 / 9.9, 13.0 / 10.4, 13.7; x1.1 g1.5: 7.1, 9.5 / 7.0, 9.3 / 6.4, 8.5; x1.1 g2: 5.1, 6.7 / 3.9, 5.2.

**D. pressure response to the first PRBC unit** — PROPOSED_NOT_APPROVED. Fundamento: MAP at the minute the first unit completes less MAP the minute before it starts (net). Base de un límite: PHYSIOLOGICAL (direction); EXPLORATORY (no numeric bound proposed); no EVIDENCE beyond arrival.

*57m* — ΔPAM, ΔPAS:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 21.5 [21.3–21.5]; 29.0 [28.7–29.0] | 16.8 [16.6–16.8]; 22.6 [22.4–22.7] | 12.2 [12.0–12.2]; 16.5 [16.1–16.5] | 3.0 [2.7–3.3]; 4.0 [3.6–4.4] | −4.2 [−4.3–−4.2]; −5.6 [−5.8–−5.6] | −9.6 [−9.8–−9.6]; −13.0 [−13.2–−13.0] |
| 1.1 | 21.3 [14.4–21.5]; 28.7 [19.4–29.0] | 17.3 [11.3–17.8]; 23.3 [15.3–24.0] | 13.3 [8.5–14.3]; 17.9 [11.4–19.3] | 6.1 [3.2–8.0]; 8.2 [4.3–10.7] | −0.1 [−1.6–2.3]; −0.2 [−2.2–3.1] | −5.5 [−7.8–−3.0]; −7.4 [−10.4–−4.0] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 21.5, 29.0 / 21.5, 29.0 / 21.5, 29.0; x1 g1: 2.5, 3.4 / 3.0, 4.0 / 7.1, 9.5; x1 g1.5: −4.2, −5.7 / −4.2, −5.6 / 1.5, 2.0; x1 g2: −9.8, −13.2 / −9.6, −13.0; x1.1 g0: 21.3, 28.7 / 21.3, 28.7 / 21.3, 28.7; x1.1 g1: 5.2, 7.0 / 6.2, 8.4 / 7.5, 10.1; x1.1 g1.5: 0.6, 0.8 / 0.7, 1.0 / −0.4, −0.6; x1.1 g2: −3.0, −4.1 / −4.4, −5.9.

*72f* — ΔPAM, ΔPAS:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 16.3 [15.9–16.3]; 21.5 [21.1–21.5] | 14.0 [13.6–14.0]; 18.5 [18.0–18.5] | 11.8 [11.4–11.8]; 15.6 [15.1–15.6] | 7.7 [7.4–7.7]; 10.2 [9.7–10.2] | 4.0 [3.7–4.0]; 5.3 [4.9–5.3] | 0.6 [0.3–0.6]; 0.8 [0.4–0.8] |
| 1.1 | 15.9 [10.8–16.3]; 21.1 [14.3–21.5] | 12.5 [7.5–12.8]; 16.5 [10.0–17.0] | 9.3 [4.5–9.6]; 12.3 [6.0–12.7] | 3.6 [−0.9–3.9]; 4.7 [−1.2–5.1] | −1.4 [−5.6–−1.1]; −1.9 [−7.4–−1.5] | −5.8 [−9.7–−5.5]; −7.7 [−12.8–−7.3] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 16.3, 21.5 / 16.3, 21.5 / 16.3, 21.5; x1 g1: 5.5, 7.3 / 7.7, 10.2 / 10.0, 13.2; x1 g1.5: 1.1, 1.4 / 4.0, 5.3 / 7.1, 9.5; x1 g2: −2.9, −3.9 / 0.6, 0.8; x1.1 g0: 15.9, 21.1 / 15.9, 21.1 / 15.9, 21.1; x1.1 g1: 0.6, 0.8 / 3.6, 4.7 / 6.7, 8.9; x1.1 g1.5: −5.2, −6.9 / −1.4, −1.9 / 2.8, 3.7; x1.1 g2: −10.2, −13.5 / −5.8, −7.7.

**E. pressure response to the second PRBC unit** — PROPOSED_NOT_APPROVED. Fundamento: MAP at the minute the second unit completes less MAP at the first unit's completion (net). Base de un límite: PHYSIOLOGICAL (direction); EXPLORATORY (no numeric bound proposed); no EVIDENCE beyond arrival.

*57m* — ΔPAM, ΔPAS:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 14.5 [14.5–17.7]; 19.6 [19.6–23.8] | 12.6 [12.6–15.6]; 17.0 [16.9–21.0] | 11.5 [11.4–14.2]; 15.5 [15.3–19.1] | 11.2 [10.9–13.5]; 15.1 [14.7–18.2] | 10.2 [10.2–12.4]; 13.8 [13.8–16.8] | 9.3 [9.3–11.3]; 12.5 [12.5–15.3] |
| 1.1 | 14.5 [12.8–17.7]; 19.6 [17.3–23.8] | 11.0 [9.1–14.2]; 14.8 [12.3–19.1] | 8.1 [6.1–11.5]; 11.0 [8.2–15.5] | 3.9 [1.7–8.0]; 5.3 [2.3–10.8] | 1.7 [−1.2–6.3]; 2.3 [−1.6–8.6] | 0.5 [−3.0–6.0]; 0.6 [−4.1–8.0] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 14.5, 19.6 / 14.5, 19.6 / 14.5, 19.6; x1 g1: 7.0, 9.4 / 11.2, 15.1 / 12.1, 16.3; x1 g1.5: 5.1, 6.9 / 10.2, 13.8 / 11.2, 15.0; x1 g2: 3.9, 5.2 / 9.3, 12.5; x1.1 g0: 14.5, 19.6 / 14.5, 19.6 / 14.5, 19.6; x1.1 g1: 1.5, 2.1 / 5.5, 7.4 / 10.2, 13.7; x1.1 g1.5: −2.9, −3.8 / 3.0, 4.0 / 10.8, 14.6; x1.1 g2: −6.4, −8.6 / 1.4, 1.9.

*72f* — ΔPAM, ΔPAS:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 11.0 [11.0–13.2]; 14.5 [14.5–17.4] | 10.7 [10.7–12.8]; 14.2 [14.2–17.0] | 10.4 [10.4–12.5]; 13.8 [13.8–16.6] | 9.9 [9.9–11.9]; 13.1 [13.1–15.8] | 9.5 [9.5–11.4]; 12.5 [12.5–15.1] | 9.1 [9.1–10.9]; 12.0 [12.0–14.4] |
| 1.1 | 11.0 [9.6–13.2]; 14.5 [12.7–17.4] | 10.5 [9.2–12.7]; 14.0 [12.2–16.8] | 10.2 [8.9–12.2]; 13.5 [11.7–16.2] | 9.5 [8.2–11.4]; 12.5 [10.9–15.1] | 8.9 [7.7–10.6]; 11.7 [10.2–14.1] | 8.3 [7.3–10.0]; 11.0 [9.6–13.2] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 11.0, 14.5 / 11.0, 14.5 / 11.0, 14.5; x1 g1: 9.7, 12.8 / 9.9, 13.1 / 10.2, 13.5; x1 g1.5: 9.1, 12.1 / 9.5, 12.5 / 9.9, 13.1; x1 g2: 8.6, 11.4 / 9.1, 12.0; x1.1 g0: 11.0, 14.5 / 11.0, 14.5 / 11.0, 14.5; x1.1 g1: 9.1, 12.1 / 9.5, 12.5 / 9.8, 13.0; x1.1 g1.5: 8.4, 11.1 / 8.9, 11.7 / 9.4, 12.4; x1.1 g2: 7.8, 10.3 / 8.3, 11.0.

**F. pressure at 120 after successful definitive resuscitation** — PROPOSED_NOT_APPROVED. Fundamento: deficit resolved, so the acute tone is withdrawn: what remains above arrival is output. Base de un límite: PHYSIOLOGICAL (direction); EXPLORATORY (no numeric bound proposed); no EVIDENCE beyond arrival.

*57m* — PAD, PAM, PAS:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 83.2 [83.2–85.6]; 100.7 [100.7–103.5]; 135.6 [135.6–139.4] | 77.8 [77.8–80.0]; 94.1 [94.1–96.7]; 126.7 [126.7–130.3] | 73.0 [73.0–75.0]; 88.3 [88.3–90.8]; 118.9 [118.9–122.3] | 65.0 [65.0–66.8]; 78.6 [78.6–80.9]; 105.9 [105.9–108.9] | 58.6 [58.6–60.3]; 70.9 [70.9–72.9]; 95.5 [95.5–98.2] | 53.3 [53.3–54.8]; 64.5 [64.5–66.4]; 86.9 [86.9–89.4] |
| 1.1 | 83.2 [75.8–85.6]; 100.7 [91.7–103.5]; 135.6 [123.4–139.4] | 77.1 [70.2–79.3]; 93.2 [84.9–95.9]; 125.6 [114.4–129.2] | 71.8 [65.4–73.8]; 86.8 [79.1–89.3]; 117.0 [106.5–120.3] | 63.1 [57.5–64.9]; 76.4 [69.5–78.5]; 102.9 [93.7–105.8] | 56.3 [51.3–57.9]; 68.1 [62.0–70.1]; 91.8 [83.6–94.4] | 50.8 [46.3–52.3]; 61.5 [56.0–63.3]; 82.9 [75.4–85.2] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 83.2, 100.7, 135.6 / 83.2, 100.7, 135.6 / 83.2, 100.7, 135.6; x1 g1: 61.2, 74.0, 99.7 / 65.0, 78.6, 105.9 / 69.3, 83.9, 113.0; x1 g1.5: 54.0, 65.4, 88.0 / 58.6, 70.9, 95.5 / 64.0, 77.4, 104.3; x1 g2: 48.4, 58.5, 78.8 / 53.3, 64.5, 86.9; x1.1 g0: 83.2, 100.7, 135.6 / 83.2, 100.7, 135.6 / 83.2, 100.7, 135.6; x1.1 g1: 59.0, 71.4, 96.2 / 63.1, 76.4, 102.9 / 67.8, 82.0, 110.5; x1.1 g1.5: 51.6, 62.4, 84.0 / 56.3, 68.1, 91.8 / 62.0, 75.1, 101.1; x1.1 g2: 45.8, 55.4, 74.6 / 50.8, 61.5, 82.9.

*72f* — PAD, PAM, PAS:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 84.3 [84.3–85.8]; 100.7 [100.7–102.5]; 133.3 [133.3–135.7] | 82.2 [82.2–83.6]; 98.1 [98.1–99.8]; 129.9 [129.9–132.2] | 80.1 [80.1–81.6]; 95.6 [95.6–97.3]; 126.7 [126.7–128.9] | 76.3 [76.3–77.7]; 91.1 [91.1–92.7]; 120.7 [120.7–122.8] | 72.9 [72.9–74.2]; 87.0 [87.0–88.5]; 115.2 [115.2–117.2] | 69.7 [69.7–70.9]; 83.2 [83.2–84.7]; 110.2 [110.2–112.1] |
| 1.1 | 84.3 [78.4–85.8]; 100.7 [93.6–102.5]; 133.3 [124.0–135.7] | 81.1 [75.4–82.6]; 96.8 [90.0–98.5]; 128.2 [119.2–130.5] | 78.1 [72.7–79.5]; 93.3 [86.7–94.9]; 123.5 [114.8–125.7] | 72.8 [67.7–74.1]; 86.9 [80.8–88.4]; 115.0 [107.0–117.1] | 68.1 [63.3–69.3]; 81.3 [75.6–82.7]; 107.6 [100.1–109.5] | 64.0 [59.5–65.1]; 76.4 [71.0–77.7]; 101.1 [94.1–102.9] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 84.3, 100.7, 133.3 / 84.3, 100.7, 133.3 / 84.3, 100.7, 133.3; x1 g1: 74.3, 88.7, 117.5 / 76.3, 91.1, 120.7 / 78.5, 93.6, 124.0; x1 g1.5: 70.1, 83.7, 110.9 / 72.9, 87.0, 115.2 / 75.8, 90.5, 119.8; x1 g2: 66.4, 79.3, 105.0 / 69.7, 83.2, 110.2; x1.1 g0: 84.3, 100.7, 133.3 / 84.3, 100.7, 133.3 / 84.3, 100.7, 133.3; x1.1 g1: 70.0, 83.6, 110.7 / 72.8, 86.9, 115.0 / 75.7, 90.4, 119.7; x1.1 g1.5: 64.5, 77.0, 102.0 / 68.1, 81.3, 107.6 / 72.1, 86.0, 113.9; x1.1 g2: 59.9, 71.4, 94.6 / 64.0, 76.4, 101.1.

**G. acceptable T during shock** — PROPOSED_NOT_APPROVED. Fundamento: the vasoconstriction an untreated haemorrhage reaches, on the arrival scale and on the no-deficit scale. Base de un límite: PHYSIOLOGICAL (direction); EXPLORATORY (no numeric bound proposed); no EVIDENCE beyond arrival.

*57m* — T, T_abs, T máx:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 1.00 [1.00–1.00]; 1.00 [1.00–1.00]; 1.00 [1.00–1.00] | 1.07 [1.05–1.07]; 1.18 [1.16–1.18]; 1.07 [1.05–1.07] | 1.13 [1.09–1.14]; 1.36 [1.31–1.36]; 1.13 [1.09–1.14] | 1.23 [1.17–1.24]; 1.72 [1.64–1.73]; 1.23 [1.17–1.24] | 1.31 [1.23–1.32]; 2.10 [1.96–2.11]; 1.31 [1.23–1.32] | 1.37 [1.27–1.38]; 2.47 [2.29–2.49]; 1.37 [1.27–1.38] |
| 1.1 | 1.00 [1.00–1.00]; 1.00 [1.00–1.00]; 1.00 [1.00–1.00] | 1.06 [1.04–1.07]; 1.18 [1.16–1.19]; 1.06 [1.04–1.07] | 1.12 [1.08–1.12]; 1.37 [1.33–1.38]; 1.12 [1.08–1.12] | 1.20 [1.14–1.21]; 1.75 [1.66–1.76]; 1.20 [1.14–1.21] | 1.26 [1.19–1.27]; 2.13 [2.00–2.14]; 1.26 [1.19–1.27] | 1.31 [1.23–1.32]; 2.51 [2.34–2.53]; 1.31 [1.23–1.32] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 1.00, 1.00, 1.00 / 1.00, 1.00, 1.00 / 1.00, 1.00, 1.00; x1 g1: 1.22, 1.71, 1.22 / 1.23, 1.72, 1.23 / 1.24, 1.74, 1.24; x1 g1.5: 1.29, 2.07, 1.29 / 1.31, 2.09, 1.31 / 1.32, 2.12, 1.32; x1 g2: 1.35, 2.43, 1.35 / 1.37, 2.47, 1.37; x1.1 g0: 1.00, 1.00, 1.00 / 1.00, 1.00, 1.00 / 1.00, 1.00, 1.00; x1.1 g1: 1.14, 1.66, 1.14 / 1.15, 1.67, 1.15 / 1.15, 1.68, 1.15; x1.1 g1.5: 1.18, 1.99, 1.18 / 1.19, 2.01, 1.19 / 1.20, 2.03, 1.20; x1.1 g2: 1.21, 2.32, 1.21 / 1.23, 2.35, 1.23.

*72f* — T, T_abs, T máx:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 1.00 [1.00–1.00]; 1.00 [1.00–1.00]; 1.00 [1.00–1.00] | 1.07 [1.05–1.08]; 1.11 [1.09–1.12]; 1.07 [1.05–1.08] | 1.15 [1.10–1.15]; 1.23 [1.19–1.24]; 1.15 [1.10–1.15] | 1.29 [1.21–1.30]; 1.49 [1.39–1.50]; 1.29 [1.21–1.30] | 1.44 [1.32–1.45]; 1.76 [1.62–1.78]; 1.44 [1.32–1.45] | 1.58 [1.43–1.59]; 2.05 [1.85–2.07]; 1.58 [1.43–1.59] |
| 1.1 | 1.00 [1.00–1.00]; 1.00 [1.00–1.00]; 1.00 [1.00–1.00] | 1.06 [1.05–1.07]; 1.13 [1.11–1.13]; 1.06 [1.05–1.07] | 1.13 [1.09–1.13]; 1.25 [1.21–1.26]; 1.13 [1.09–1.13] | 1.24 [1.17–1.25]; 1.53 [1.44–1.54]; 1.24 [1.17–1.25] | 1.35 [1.25–1.36]; 1.81 [1.68–1.83]; 1.35 [1.25–1.36] | 1.44 [1.33–1.46]; 2.10 [1.93–2.13]; 1.44 [1.33–1.46] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 1.00, 1.00, 1.00 / 1.00, 1.00, 1.00 / 1.00, 1.00, 1.00; x1 g1: 1.27, 1.46, 1.27 / 1.29, 1.49, 1.29 / 1.32, 1.52, 1.32; x1 g1.5: 1.38, 1.69, 1.38 / 1.44, 1.76, 1.44 / 1.49, 1.83, 1.49; x1 g2: 1.49, 1.93, 1.49 / 1.57, 2.05, 1.57; x1.1 g0: 1.00, 1.00, 1.00 / 1.00, 1.00, 1.00 / 1.00, 1.00, 1.00; x1.1 g1: 1.16, 1.42, 1.16 / 1.18, 1.44, 1.18 / 1.20, 1.47, 1.20; x1.1 g1.5: 1.22, 1.64, 1.22 / 1.26, 1.69, 1.26 / 1.29, 1.73, 1.29; x1.1 g2: 1.28, 1.86, 1.28 / 1.33, 1.94, 1.33.

**H. acceptable T at 120 after adequacy** — PROPOSED_NOT_APPROVED. Fundamento: the tone left once delivery is adequate: T_abs = 1 when no deficit remains. Base de un límite: PHYSIOLOGICAL (direction); EXPLORATORY (no numeric bound proposed); no EVIDENCE beyond arrival.

*57m* — T, T_abs:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 1.00 [1.00–1.00]; 1.00 [1.00–1.00] | 0.91 [0.91–0.91]; 1.00 [1.00–1.00] | 0.83 [0.83–0.83]; 1.00 [1.00–1.00] | 0.71 [0.71–0.71]; 1.00 [1.00–1.00] | 0.62 [0.62–0.62]; 1.00 [1.00–1.00] | 0.56 [0.56–0.56]; 1.00 [1.00–1.00] |
| 1.1 | 1.00 [1.00–1.00]; 1.00 [1.00–1.00] | 0.90 [0.90–0.90]; 1.00 [1.00–1.00] | 0.81 [0.81–0.81]; 1.00 [1.00–1.00] | 0.69 [0.69–0.69]; 1.00 [1.00–1.00] | 0.59 [0.59–0.59]; 1.00 [1.00–1.00] | 0.52 [0.52–0.52]; 1.00 [1.00–1.00] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 1.00, 1.00 / 1.00, 1.00 / 1.00, 1.00; x1 g1: 0.71, 1.00 / 0.71, 1.00 / 0.71, 1.00; x1 g1.5: 0.62, 1.00 / 0.62, 1.00 / 0.62, 1.00; x1 g2: 0.56, 1.00 / 0.56, 1.00; x1.1 g0: 1.00, 1.00 / 1.00, 1.00 / 1.00, 1.00; x1.1 g1: 0.69, 1.00 / 0.69, 1.00 / 0.69, 1.00; x1.1 g1.5: 0.59, 1.00 / 0.59, 1.00 / 0.59, 1.00; x1.1 g2: 0.52, 1.00 / 0.52, 1.00.

*72f* — T, T_abs:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 1.00 [1.00–1.00]; 1.00 [1.00–1.00] | 0.96 [0.96–0.96]; 1.00 [1.00–1.00] | 0.93 [0.93–0.93]; 1.00 [1.00–1.00] | 0.87 [0.87–0.87]; 1.00 [1.00–1.00] | 0.82 [0.82–0.82]; 1.00 [1.00–1.00] | 0.77 [0.77–0.77]; 1.00 [1.00–1.00] |
| 1.1 | 1.00 [1.00–1.00]; 1.00 [1.00–1.00] | 0.95 [0.95–0.95]; 1.00 [1.00–1.00] | 0.90 [0.90–0.90]; 1.00 [1.00–1.00] | 0.81 [0.81–0.81]; 1.00 [1.00–1.00] | 0.75 [0.75–0.75]; 1.00 [1.00–1.00] | 0.69 [0.69–0.69]; 1.00 [1.00–1.00] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 1.00, 1.00 / 1.00, 1.00 / 1.00, 1.00; x1 g1: 0.87, 1.00 / 0.87, 1.00 / 0.87, 1.00; x1 g1.5: 0.82, 1.00 / 0.82, 1.00 / 0.82, 1.00; x1 g2: 0.77, 1.00 / 0.77, 1.00; x1.1 g0: 1.00, 1.00 / 1.00, 1.00 / 1.00, 1.00; x1.1 g1: 0.81, 1.00 / 0.81, 1.00 / 0.81, 1.00; x1.1 g1.5: 0.75, 1.00 / 0.75, 1.00 / 0.75, 1.00; x1.1 g2: 0.69, 1.00 / 0.69, 1.00.

**I. acceptable output / DO2 penalty from vasoconstriction** — PROPOSED_NOT_APPROVED. Fundamento: output and delivery against the T = 1 reference on the same key (fractional change), the effective deficit and D change: the price of the pressure gained. Base de un límite: PHYSIOLOGICAL (direction); EXPLORATORY (no numeric bound proposed); no EVIDENCE beyond arrival.

*57m* — ΔD, Δ déficit, costo de aporte, costo de gasto:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 0.0 [0.0–0.0]; 0.0 [0.0–0.0]; 0.0 % [0.0–0.0]; 0.0 % [0.0–0.0] | 1.0 [0.8–1.0]; 0.0 [0.0–0.0]; −2.1 % [−2.1–−1.5]; −2.1 % [−2.1–−1.5] | 1.8 [1.5–1.8]; 0.0 [0.0–0.0]; −3.8 % [−3.9–−2.8]; −3.8 % [−3.9–−2.8] | 3.2 [2.7–3.2]; 0.0 [0.0–0.0]; −6.5 % [−6.7–−4.8]; −6.5 % [−6.7–−4.8] | 4.2 [3.6–4.2]; 0.0 [0.0–0.0]; −8.5 % [−8.7–−6.3]; −8.5 % [−8.7–−6.3] | 5.0 [4.3–5.1]; 0.0 [0.0–0.0]; −10.0 % [−10.3–−7.6]; −10.0 % [−10.3–−7.6] |
| 1.1 | 0.0 [0.0–0.0]; 0.0 [0.0–0.0]; 0.0 % [0.0–0.0]; 0.0 % [0.0–0.0] | 0.2 [0.2–0.2]; 0.0 [0.0–0.0]; −1.9 % [−1.9–−1.3]; −1.9 % [−1.9–−1.3] | 0.4 [0.3–0.4]; 0.0 [0.0–0.0]; −3.4 % [−3.5–−2.4]; −3.4 % [−3.5–−2.4] | 0.7 [0.6–0.7]; 0.0 [0.0–0.0]; −5.7 % [−5.9–−4.1]; −5.7 % [−5.9–−4.1] | 0.9 [0.8–0.9]; 0.0 [0.0–0.0]; −7.3 % [−7.6–−5.4]; −7.3 % [−7.6–−5.4] | 1.0 [0.9–1.1]; 0.0 [0.0–0.0]; −8.6 % [−8.9–−6.4]; −8.6 % [−8.9–−6.4] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 0.0, 0.0, 0.0 %, 0.0 % / 0.0, 0.0, 0.0 %, 0.0 % / 0.0, 0.0, 0.0 %, 0.0 %; x1 g1: 1.0, 0.0, −2.2 %, −2.2 % / 3.2, 0.0, −6.5 %, −6.5 % / 5.4, 0.0, −10.7 %, −10.7 %; x1 g1.5: 1.4, 0.0, −2.8 %, −2.8 % / 4.2, 0.0, −8.5 %, −8.5 % / 7.3, 0.0, −13.9 %, −13.9 %; x1 g2: 1.6, 0.0, −3.4 %, −3.4 % / 5.0, 0.0, −10.0 %, −10.0 %; x1.1 g0: 0.0, 0.0, 0.0 %, 0.0 % / 0.0, 0.0, 0.0 %, 0.0 % / 0.0, 0.0, 0.0 %, 0.0 %; x1.1 g1: 0.2, 0.0, −1.4 %, −1.4 % / 0.6, 0.0, −4.2 %, −4.2 % / 1.0, 0.0, −7.1 %, −7.1 %; x1.1 g1.5: 0.2, 0.0, −1.8 %, −1.8 % / 0.8, 0.0, −5.5 %, −5.5 % / 1.3, 0.0, −9.3 %, −9.3 %; x1.1 g2: 0.3, 0.0, −2.1 %, −2.1 % / 0.9, 0.0, −6.5 %, −6.5 %.

*72f* — ΔD, Δ déficit, costo de aporte, costo de gasto:

| demanda | g 0 | g 0.25 | g 0.5 | g 1 | g 1.5 | g 2 |
|---|---|---|---|---|---|---|
| 1 | 0.0 [0.0–0.0]; 0.0 [0.0–0.0]; 0.0 % [0.0–0.0]; 0.0 % [0.0–0.0] | 1.7 [1.3–1.7]; 0.0 [0.0–0.0]; −2.2 % [−2.2–−1.5]; −2.2 % [−2.2–−1.5] | 3.3 [2.6–3.4]; 0.0 [0.0–0.0]; −4.2 % [−4.4–−3.0]; −4.2 % [−4.4–−3.0] | 6.6 [5.3–6.7]; 0.0 [0.0–0.0]; −8.1 % [−8.3–−5.9]; −8.1 % [−8.3–−5.9] | 9.7 [7.9–9.9]; 0.1 [0.1–0.1]; −11.6 % [−11.9–−8.7]; −11.6 % [−11.9–−8.7] | 12.7 [10.5–12.9]; 0.1 [0.1–0.1]; −14.7 % [−15.1–−11.3]; −14.7 % [−15.1–−11.3] |
| 1.1 | 0.0 [0.0–0.0]; 0.0 [0.0–0.0]; 0.0 % [0.0–0.0]; 0.0 % [0.0–0.0] | 0.4 [0.3–0.4]; 0.0 [0.0–0.0]; −1.9 % [−2.0–−1.4]; −1.9 % [−2.0–−1.4] | 0.7 [0.6–0.7]; 0.0 [0.0–0.0]; −3.7 % [−3.8–−2.6]; −3.7 % [−3.8–−2.6] | 1.3 [1.1–1.4]; 0.0 [0.0–0.0]; −6.8 % [−7.0–−5.0]; −6.8 % [−7.0–−5.0] | 1.9 [1.6–2.0]; 0.1 [0.0–0.1]; −9.5 % [−9.8–−7.1]; −9.5 % [−9.8–−7.1] | 2.4 [2.0–2.5]; 0.1 [0.1–0.1]; −11.8 % [−12.2–−8.9]; −11.8 % [−12.2–−8.9] |

Sensibilidad a a (muestra, medianas a = 0,1 / 0,3 / 0,5): x1 g0: 0.0, 0.0, 0.0 %, 0.0 % / 0.0, 0.0, 0.0 %, 0.0 % / 0.0, 0.0, 0.0 %, 0.0 %; x1 g1: 2.0, 0.0, −2.6 %, −2.6 % / 6.6, 0.0, −8.1 %, −8.1 % / 11.9, 0.1, −13.8 %, −13.8 %; x1 g1.5: 2.9, 0.0, −3.7 %, −3.7 % / 9.7, 0.1, −11.6 %, −11.6 % / 18.0, 0.1, −19.7 %, −19.7 %; x1 g2: 3.7, 0.0, −4.7 %, −4.7 % / 12.7, 0.1, −14.7 %, −14.7 %; x1.1 g0: 0.0, 0.0, 0.0 %, 0.0 % / 0.0, 0.0, 0.0 %, 0.0 % / 0.0, 0.0, 0.0 %, 0.0 %; x1.1 g1: 0.3, 0.0, −1.6 %, −1.6 % / 1.1, 0.0, −5.0 %, −5.0 % / 2.0, 0.1, −8.9 %, −8.9 %; x1.1 g1.5: 0.5, 0.0, −2.2 %, −2.2 % / 1.6, 0.0, −7.2 %, −7.2 % / 3.0, 0.1, −12.8 %, −12.8 %; x1.1 g2: 0.6, 0.0, −2.7 %, −2.7 % / 2.0, 0.1, −9.0 %, −9.0 %.
<!-- /generado:envolventes -->

## 17. Identificabilidad (generado)

<!-- generado:identificabilidad -->
| magnitud | clase | por qué |
|---|---|---|
| trayectoria de T | NON_IDENTIFIABLE | T nunca se observa; dada g, su forma la fija la señal certificada (aporte y demanda) |
| poscarga a | NON_IDENTIFIABLE | llega a la presión y al gasto sólo con T ≠ 1, y no se observa gasto ni resistencia; con tono dinámico a y g actúan juntos, así que una envolvente de presión acotaría el par, no a |
| compuesto presión / gasto | POORLY_IDENTIFIED | PAM = PAM de llegada × Q × T: en la llegada, bien acotada por anclaje (exacta por construcción); después, nada observado; el gasto lo fija la fisiología sanguínea certificada con T = 1 y sólo se mueve con el tono a través de a |
| ganancia de tono | NON_IDENTIFIABLE | no hay presión, gasto ni resistencia registrados después de la llegada, y la presión de llegada es exacta por construcción con cualquier ganancia (T = 1 allí): nada observado alcanza g. Sólo está acotada por estructura (g a < 1, 1 + g ≤ 3); las envolventes A, B y F la harían PARTIALLY_CONSTRAINED |

Amplitud de las medianas entre ganancias (lo que una envolvente podría acotar, mmHg): A gi_bleed_57m map x1: 7.6; A gi_bleed_57m map x1.1: 6.5; A gi_bleed_57m sbp x1: 10.2; A gi_bleed_57m sbp x1.1: 8.7; B gi_bleed_72f map x1: 16.8; B gi_bleed_72f map x1.1: 13.5; B gi_bleed_72f sbp x1: 22.3; B gi_bleed_72f sbp x1.1: 17.8; F gi_bleed_57m dbp x1: 29.9; F gi_bleed_57m dbp x1.1: 32.4; F gi_bleed_57m map x1: 36.1; F gi_bleed_57m map x1.1: 39.1; F gi_bleed_57m sbp x1: 48.7; F gi_bleed_57m sbp x1.1: 52.7; F gi_bleed_72f dbp x1: 14.6; F gi_bleed_72f dbp x1.1: 20.4; F gi_bleed_72f map x1: 17.5; F gi_bleed_72f map x1.1: 24.3; F gi_bleed_72f sbp x1: 23.1; F gi_bleed_72f sbp x1.1: 32.2.
<!-- /generado:identificabilidad -->

La tabla congelada no tiene fila para s0, y la revisión adversarial lo señaló. s0 y g son conjuntamente no
identificables: el nivel de aporte de llegada fija s0, no está aprobado, y su efecto sobre T se confunde con el de g,
porque T a los 120 tras la reanimación es 1 / (1 + g·s0).

## 18. Barorreflejo: plan actualizado (generado)

<!-- generado:barorreflejo -->
- **doble conteo**: the acute signal drives both tone and the sympathetic drive; a pressure deficit falls with output and rises less once tone supports it, so the baroreflex term reads MAP after tone; their shared variance on the arrival surface is reported before any value
- **requiere**: faculty pressure envelopes (A, B, F) and a tone decision first; then a MAP set point and a baroreflex gain range authorized before any value; then the P2I-2AK A-F rules repeated
- **señal**: the absolute MAP the pressure domain now derives with dynamic tone (mmHg, anchored on the authored arrival), against a faculty set point: max(0, MAP_set - MAP) / MAP_set, never the arrival-relative 1 - p
- **estado**: DEFERRED: pressure -> HR stays PRESSURE_TERM_DIAGNOSTIC_ONLY (0 in the primary HR profile); not reconnected in P2J-2
- **interacción con el tono**: tone already answers the acute deficit and supports pressure; a baroreflex acting on HR must not also act on T through the same deficit (one tone writer only: the core fails closed on a second one), and its gain is explored jointly with the acute HR gain and the tone gain
<!-- /generado:barorreflejo -->

## 19. Decisiones que se piden a la docencia

1. **Normalización del tono a la llegada (§3):**
   - El canal T vale (1 + g·s) / (1 + g·s0), así que la llegada ya contiene la vasoconstricción de su propio déficit.
   - En consecuencia:
     - el apoyo sin tratamiento es moderado (57m);
     - tras la reanimación, el tono baja por debajo del de llegada;
     - el paciente tratado puede caer bajo PAS 80 antes que el no tratado (57m, g = 2);
     - y, en la práctica, s0 actúa como un desplazamiento propio de cada caso, ligado a un nivel de aporte de llegada
       sin aprobar.
   - ¿Es la lectura buscada, o se prefiere otra referencia del tono, como un s0 docente o común?
2. **Ganancia de tono:**
   - El rango congelado es 0,25–2; 0 es la referencia T = 1.
   - Con a = 0,3, g ≥ 0,5 pierde candidatos de lactato a demanda 1,0 (FD-LAC-06 de 72f), y g ≥ 1,5 hace que la PAM
     baje durante la primera unidad de GR en 57m.
   - ¿Qué rango es aceptable?
3. **Retirada del tono:**
   - ¿Se acepta que T siga al déficit sin retraso?
   - ¿O se autoriza un término de memoria o una constante de tiempo? Si se autoriza, falta su rango.
   - Ninguna de las dos opciones cambia el nivel final, que depende del punto 1.
4. **Envolventes de presión A, B y F** (sin tratamiento a los 120 y tras la reanimación definitiva), y las respuestas
   a cristaloide y a la primera y la segunda unidad de GR (C–E).
5. **Rango de T aceptable** en shock (G) y tras la adecuación (H), y **costo de aporte aceptable** del tono (I).
6. **El gasto tras la reanimación** (1,4–1,8 veces el de llegada a los 120): sostiene la sobrepresión que queda con
   g ≤ 1. Pertenece a la fisiología sanguínea y de precarga certificada, que P2J-2 no reabre.
7. **Después:** el punto de ajuste y la ganancia del barorreflejo, y la reconexión presión → FC (§18).

## 20. Validación, veredicto y eficiencia (generado)

<!-- generado:validacion -->
Reconstrucción contra el núcleo: 816 corridas completas en 48 filas de la muestra, todas iguales: sí (máxima diferencia 0.0). Repetición idéntica: sí. Referencia g = 0 igual a la presión de P2J-1: sí. Unidades de lactato de P2I-2AK reproducidas: sí (1.0: `06f6d5c82fa3…`, 1.1: `515a157e2118…`; 18 y 37 unidades). Prueba AST de lo que P2J-2 cambió fuera de su módulo: `clinical_core/derived.py` sí; `clinical_core/integration.py` sí.
<!-- /generado:validacion -->

<!-- generado:veredicto -->
**DYNAMIC_TONE_DECISION_SURFACE_READY**

- distribuciones de P1–P4 para ambos casos, ambas demandas y cada ganancia: sí
- retroalimentación determinista y estable (sonda 5, sin rechazo de simulación, repeticiones idénticas): sí
- restricciones de lactato satisfacibles por alguna ganancia > 0 en cada demanda: sí
- sin lazo patológico presión / gasto (ningún UNSTABLE_FEEDBACK): sí
- nada aprobado: sí
- presión continua y no negativa: sí
- presión → FC aplazada (0 en el perfil primario): sí
- reconstrucción igual al núcleo en la muestra: sí
- semántica del tono coherente (sondas 1, 2 y 6; T = 1 en los minutos 0 y 1; la ganancia 0 reproduce P2J-1): sí
- unidades de P2I-2AK reproducidas y referencia de lactato intacta a ganancia 0: sí
- gasto cero y paro coherentes: sí
- Parámetros aprobados: 0.
<!-- /generado:veredicto -->

<!-- generado:eficiencia -->
Trayectorias hemodinámicas para reproducir las unidades: 3178; trayectorias de sangre en caché (una por conjunto y escenario): 1326; reconstrucciones por ganancia con a = 0,3: 11196 y de la muestra con a = 0,1 / 0,3 / 0,5: 816 (corridas del núcleo que habrían hecho falta sin reconstrucción: 11724); unidades releídas por FD-LAC: 55 por ganancia; corridas completas de validación: 816; corridas completas para la FC: 288; rechazos analíticos: 1; barrido cartesiano: no; presión heredada leída: no.
<!-- /generado:eficiencia -->

## 21. Limitaciones

- **La sensibilidad a a** se lee en la muestra (3 unidades por demanda), no en todas las unidades. Lo mismo ocurre con
  FD-LAC para a = 0,1 y 0,5 y con la FC.
- **Antes del congelamiento** se miró una corrida técnica: P1, 57m, un conjunto de sangre, tres niveles de aporte,
  ganancias 0 y 1, con
  T, PAM, déficit, D y lactato en algunos minutos. Servía para comprobar la implementación. La lista de ganancias ya
  estaba fijada y no cambió.
- **El congelamiento se enmendó una vez** (`a034aef` → `b3b63b1`; `a034aef` queda sólo en el reflog, nunca se subió).
  - El primer intento de evaluación se detuvo en la primera tarea de trayectorias, sin escribir resultados: la
    adecuación L3 vale `None` donde no hay hemostasia.
  - Después, una prueba de humo sobre dos unidades sintéticas hizo fallar `envelopes()` al leer un par rechazado con
    a = 0,5. Esa prueba sólo imprimió booleanos y el nombre de la comprobación que no pasaba (la de lactato, esperable
    en unidades no retenidas), ningún valor de presión.
  - La enmienda tiene tres cambios de código (`NOT_ASSESSED`, saltar los pares rechazados en la sensibilidad a a y la
    comprobación de que la ganancia 0 reproduce la referencia de lactato) más el texto de `VERDICT_RULE`. No se tocaron
    ganancias, poscargas ni reglas.
- **Dos comprobaciones del veredicto no pueden fallar en la práctica:**
  - `reference_equals_p2j1` compara la reconstrucción con g = 0 contra la salida en caché × la PAM de llegada, no
    contra el registro de P2J-1;
  - `pressure_to_hr_deferred` compara una constante.
- **El mecanismo exacto de la pérdida de FD-LAC-06** (§13) no se descompuso, y ese diagnóstico no está en el registro.
- **El registro** se escribe en JSON compacto (4 MB) para no duplicar su tamaño con sangría.
