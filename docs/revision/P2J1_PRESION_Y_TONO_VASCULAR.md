# P2J-1 · Presión y tono vascular: auditoría estructural y superficie de calibración

- **Fecha:** 2026-10-30. Sólo en sombra. No se integra nada, y ningún parámetro se aprueba ni se selecciona. El golden
  registra P2J-1 con la dirección estructural que pidió la docencia (§10); la forma proporcional queda por confirmar
  (§18).
- **Base:** `052d816` (P2I-2AK, cerrado). Congelamiento: `31a74ef`, antes de leer ninguna trayectoria sobre la
  fisiología conservada (digest `92aa42cb…`).
- **Números:** `docs/revision/P2J1_pressure_tone.json`. Las secciones marcadas «generado» las escribe
  `python -m clinical_core.pressure_tone_report` desde ese registro.

## Resumen

- **Hallazgo:** la relación de presión que leía el núcleo hasta P2I-2AK era continua, pero tenía una rodilla con quiebre de
  pendiente (CONTINUOUS_WITH_KNEE) en `pressure_rel` 0,5. Sobre la rodilla, la recta heredada (llegada − 45 y − 25 mmHg
  por unidad de 1 − p) llevaba una resistencia propia que T no representaba: un tono oculto que cambia con el flujo.
  Valía 1,52–1,65 veces la de llegada en la rodilla y menos de 1 sobre la llegada.
- **Corrección mínima (sin parámetros nuevos):** PAS y PAD son las de llegada × p, con p = gasto × T, en todo el
  rango. Desaparecen la rodilla, el piso y el tono oculto. Las dos ganancias y la rodilla quedan en el perfil sin leerse.
- **Qué cambia y qué no:**
  - Cambian sólo PAS, PAD, PAM, la presión de pulso y la conciencia por umbrales de PAS.
  - Gasto, T, p, BloodState, déficit, D, lactato, FR y FC son idénticos. El golden lo muestra columna por columna, y
    las unidades de lactato de P2I-2AJ y P2I-2AK se reproducen byte a byte.
- **T** es la resistencia vascular sistémica relativa a la llegada, y ahora es la única resistencia. No hay doble
  conteo, pero ningún mecanismo clínico la escribe: en los casos GI vale 1 siempre. **El modelo no tiene, por lo tanto,
  ninguna respuesta del tono que compense o relaje la presión.** Esa respuesta pide parámetros nuevos: es decisión
  docente.
- **Trayectorias sobre la fisiología conservada:**
  - Sin tratamiento, la PAM de 57m cae de 65 a 33 mmHg (PAS 44) en 120 min, y la de 72f de 74 a 49.
  - Con 2 U de GR y hemostasia, sube a 101 mmHg en ambos (PAS 136 y 133).
  - La relación previa daba 49 y 63, y 82 y 85.
- **Veredicto:** PRESSURE_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION. La estructura es coherente, pero la relación
  ya no tiene parámetros propios en los casos GI: la calibración numérica de la presión depende de envolventes docentes
  y de autorizar, o no, una respuesta del tono (§17).

## 1. Decisiones docentes registradas (generado)

<!-- generado:decisiones -->
- **corrección:** the minimum common-physiology correction of a clear structural defect; no fit to the two GI pressures, no GI-specific term, no unnecessary change to output, no new parameter unless structurally required (then stop for authorization before any range)
- **fecha:** 2026-10-30
- **demanda:** 1.0 and 1.1 stay CURRENTLY_COMPATIBLE uncertainty states; robustness across them is not required; pressure is simulated once if it is invariant to demand
- **FC:** P2I-2AK accepted (HR_OBSERVABLE_FILTER_SATISFIED); the HR region is carried as uncertainty: no intrinsic rate, acute-deficit gain, debt gain or sinus ceiling is selected or approved
- **presión → FC:** PRESSURE_TERM_DIAGNOSTIC_ONLY: the pressure contribution to the sympathetic drive stays 0 in the primary HR profile until pressure is structurally coherent and a later package reconnects it
- **alcance:** shadow only; no runtime integration, GI or second-family migration, final pressure parameter, hard pressure envelope, pressure -> HR reconnection, RR calibration, collapse, legacy fitting or HR latent selection
- **estructura esperada:** pressure continuous in output; never decreasing with output at a fixed tone or with tone at a fixed output; approaching zero with output; no arbitrary positive floor without output; consistent with pulse, rhythm and arrest. A smooth nonlinear mapping is acceptable; a physiologically meaningful knee may be later; an arbitrary implementation discontinuity is not
<!-- /generado:decisiones -->

## 2. Derivación actual, término por término (generado)

Antes de P2J-1 las ecuaciones de PAS y PAD eran las de la columna «antes»; desde P2J-1 son las de la llegada × p. La
PAM no se modela aparte: es (PAS + 2 PAD) / 3. La presión de pulso tampoco: es PAS − PAD. La presión relativa p que lee
la FC es gasto × T.

Fuera del núcleo, la comparación con el motor heredado (`comparison.py`) proyecta las presiones a la pantalla con la
convención del motor (PAS acotada a 50–240, PAD con mínimo 25). Es un piso sólo de pantalla: no actúa en el golden (PAS
mínima 73), pero las trayectorias de §12 llegan a PAS cruda 42–44.

<!-- generado:ecuaciones -->
| Término | Ecuación | Parámetros | Procedencia | Valor | Estado | Alcance |
|---|---|---|---|---|---|---|
| output | Q = P x (R.output_factor / arrival output_factor) x preload_rel x 1 / (1 + a (T - 1)) | P, rhythm output factor, preload curve (scale, arrival position, c), afterload_sensitivity a | KD-S4, P2D-5 (derived._perfusion) | a = 0.3 | candidata provisional | common (arrival position per case) |
| preload_rel | position(V) / position(0) on 1 - exp(-x / (scale x P^c)), x = arrival filling + V | preload_curve_scale_ml, arrival_preload_fraction / case position, pump_preload_coupling | KD-S4, P2D-5, P2I-2T (V from the shared blood state) | scale 833.3 mL-eq, c = 1 | candidata provisional | common (position per case) |
| vascular tone T | a channel: multiplier, 1 at arrival; changed only by contributions (none in the GI cases) | channel guard [0.1, 3.0] | proposal §7.2, §7.4 (anchoring) | 1 | estructural | common |
| relative pressure | p = Q x T (relative to arrival: 1 there) | none | KD-S4 (derived._perfusion) | — | estructural | common |
| SBP | SBP = SBP_arrival x max(0, p) (P2J-1; before: SBP_a - 45 (1 - p) above the knee, the knee value x p / knee below it) | authored arrival SBP | P2J-1 (derived.arterial_pressures) | — | estructural | scale per case (authored) |
| DBP | DBP = DBP_arrival x max(0, p) (P2J-1; before: DBP_a - 25 (1 - p) above the knee, ramp below) | authored arrival DBP | P2J-1 | — | estructural | scale per case (authored) |
| MAP | MAP = (SBP + 2 DBP) / 3, so MAP = MAP_arrival x p since P2J-1 | none | derived.derive | — | estructural | common |
| pulse pressure | PP = SBP - DBP = PP_arrival x p since P2J-1 (not modelled on its own) | none | derived | — | estructural | common |
| HR pressure term | sympathetic_per_pressure_deficit x (1 - p) in the drive target; 0 in the primary HR profile | sympathetic_per_pressure_deficit | KD-S2, P2I-2AG (PRESSURE_TERM_DIAGNOSTIC_ONLY) | 1.0 (default profile), 0.0 (primary HR profile) | candidata provisional | common |
| sbp_per_pressure_deficit | read until P2I-2AK above the knee | 45 mmHg per unit | family_engine._surface | 45 | no se lee desde P2J-1 | common |
| dbp_per_pressure_deficit | read until P2I-2AK above the knee | 25 mmHg per unit | family_engine._surface | 25 | no se lee desde P2J-1 | common |
| low_output_pressure_knee | read until P2I-2AK: the splice point | 0.5 of p | P2E-4 | 0.5 | no se lee desde P2J-1 | common |
| arrival anchors | SBP 88 / DBP 54 (57m), 98 / 62 (72f) | case bank | clinical_cases.py:881, :910 | — | registrada en el caso | per case |
| consciousness by pressure | level 1 below SBP 80, 2 below 65 (raw SBP) | pressure_levels | family_engine._PRESSURE_LEVELS | (80, 1), (65, 2) | magnitud heredada adoptada (no aprobada) | common |
| zero output | Q <= 1e-9 with a pulse: UnresolvedBoundary (the run stops); no pulse: SBP, DBP, MAP not measurable (None) | OUTPUT_EPSILON (numerical, not clinical) | P2D-2 | 1e-9 | estructural | common |
<!-- /generado:ecuaciones -->

<!-- generado:topes -->
**Antes de P2J-1:**
- knee at p = 0.5 (low_output_pressure_knee, provisional): the slope of SBP and DBP changes there
- max(0, .) on the linear branch (inactive for any arrival above 22.5 / 12.5 mmHg)
- max(0, p) below the knee (p is never negative)
- no cap: linear above arrival, unbounded
- T guard [0.1, 3.0] (a bound, recorded as a clamp when it acts)

**Desde P2J-1:**
- max(0, p) only (p is never negative: Q and T are)
- no knee, no floor, no cap
- T guard [0.1, 3.0] (unchanged)
- afterload a < 1 (profile check): Q stays positive at any tone and p rises with T
- Q <= 1e-9 with a pulse stops the run (unchanged)
<!-- /generado:topes -->

## 3. La rodilla, en estados fijos (generado)

Clasificación de la relación previa: **CONTINUOUS_WITH_KNEE**.
- No hay salto de valor ni piso: vale 0 en p = 0.
- La pendiente cambia sólo en p = 0,5, y el salto depende de la presión de llegada de cada caso: es un artefacto de
  implementación, no fisiología.
- La resistencia implícita (PAM / (PAM de llegada × p)) muestra el tono oculto.

Desde P2J-1: **CONTINUOUS_AND_SMOOTH**, con resistencia implícita 1 en todo el rango.

Alcance del clasificador: lee la cuadrícula de 0,002 y el punto 0,5, no todo el intervalo. Un quiebre o un salto entre
puntos de la cuadrícula se le escaparía. La relación actual está fijada aparte, exactamente: una prueba la compara en 301
puntos y en puntos fuera de la cuadrícula, y la dirección 8 comprueba la identidad en cada minuto de cada trayectoria.

<!-- generado:rodilla -->
| Llegada | Antes de P2J-1 | Pendiente de PAS bajo / sobre la rodilla (×) | Pendiente de PAD (×) | Resistencia implícita con p 0,5 · 1,5 · 2 | Desde P2J-1 |
|---|---|---|---|---|---|
| GI 57m | CONTINUOUS_WITH_KNEE | 131,0 / 45,0 (2,91) | 83,0 / 25,0 (3,32) | 1,52 · 0,83 · 0,74 | CONTINUOUS_AND_SMOOTH, resistencia 1,00 |
| GI 72f | CONTINUOUS_WITH_KNEE | 151,0 / 45,0 (3,36) | 99,0 / 25,0 (3,96) | 1,57 · 0,81 · 0,71 | CONTINUOUS_AND_SMOOTH, resistencia 1,00 |
| neutral arrival | CONTINUOUS_WITH_KNEE | 195,0 / 45,0 (4,33) | 125,0 / 25,0 (5,00) | 1,65 · 0,78 · 0,68 | CONTINUOUS_AND_SMOOTH, resistencia 1,00 |

La réplica de la relación previa reproduce el registro de P2I-2Q, calculado por el núcleo de entonces (diferencia máxima 0).
<!-- /generado:rodilla -->

## 4. Gasto cero y paro, P7 (generado)

<!-- generado:cero -->
- **Cero numérico con pulso:** UNRESOLVED_BOUNDARY (la corrida se detiene; nunca hay pulso ni presión sin gasto).
- **Gasto pequeño:** PAM 6,53e-05 y 0,000122 mmHg con P 1e-6 y T 1 o 3; 0,122 mmHg con P 0,001 y T 3.
- **Sin pulso (AESP, asistolia, FV):** gasto 0 y PAS, PAD y PAM no medibles en los tres: sí.
- **Cumple:** sí.
<!-- /generado:cero -->

## 5. Tono T: qué representa y por dónde pasa (generado)

- **Antes de P2J-1:** MIXED_CONSTRUCT. T era la resistencia relativa, pero la relación de presión sumaba una
  resistencia propia.
- **Desde P2J-1:** resistencia vascular sistémica relativa a la llegada, la única que lee la presión.
- **Entra en dos ecuaciones:**
  - el gasto: la poscarga baja el gasto, 1 / (1 + a (T − 1));
  - la presión: p = gasto × T.
- **No es doble conteo:** son los dos efectos físicos de la resistencia sobre el flujo y sobre la presión.
- **No hay circularidad:** nada escribe T. El impulso simpático sólo mueve la FC.

<!-- generado:tono -->
- **Lecturas:** `clinical_core/blood_fluid_readiness.py` · _haemodynamics (.T); `clinical_core/derived.py` · _perfusion (.T); `clinical_core/hemodynamic_probes.py` · _row (.T); `clinical_core/integration.py` · <module> (Channel.T); `clinical_core/pressure_tone.py` · _rows (.T); `clinical_core/state.py` · <module> (Channel.T); `clinical_core/state.py` · CoreState (.T).
- **Escrituras:** `clinical_core/bands.py` · <module> (drift on "T"); `clinical_core/hemodynamic_probes.py` · pressure_as_perfusion (T=); `clinical_core/pressure_tone.py` · coupling_probes (T=); `clinical_core/pressure_tone.py` · zero_output_probe (T=); `clinical_core/state.py` · anchored_state (T=).
- **Escritores clínicos:** 0. Sólo escriben T las sondas sintéticas y el valor 1 de la llegada (anclaje).
<!-- /generado:tono -->

## 6. Bomba, tono, gasto y presión: P5 y P6 (generado)

Con precarga, bomba y ritmo fijos (llegada canónica de 57m):
- subir T baja el gasto y sube la presión;
- bajar T hace lo contrario;
- subir P con T fijo sube ambos.

El acoplamiento de poscarga es coherente en los tres puntos de a.

<!-- generado:acoplamiento -->
- **Más tono (T 1 → 2):** el gasto baja: sí; la presión sube: sí.
- **Menos tono (T 1 → 0,5):** el gasto sube: sí; la presión baja: sí.
- **Más bomba (P 1 → 1,5) con T fijo:** el gasto sube: sí; la presión sube: sí.
- **Techo del tono:** con P y precarga fijos y T sin cota, p no supera 3,33 veces el gasto base (1 / a); dentro de la guarda de T (≤ 3) el máximo es 3 / (1 + 2a), 1,875 con a = 0,3.

| a | PAM con bomba fija, T 0,5 · 1 · 2 · 3 | Gasto con bomba fija, T 0,5 · 1 · 2 · 3 | PAM con gasto fijo, T 0,5 · 1 · 2 · 3 |
|---|---|---|---|
| 0,1 | 34,4 · 65,3 · 118,8 · 163,3 | 1,053 · 1,000 · 0,909 · 0,833 | 32,7 · 65,3 · 130,7 · 196,0 |
| 0,3 | 38,4 · 65,3 · 100,5 · 122,5 | 1,176 · 1,000 · 0,769 · 0,625 | 32,7 · 65,3 · 130,7 · 196,0 |
| 0,5 | 43,6 · 65,3 · 87,1 · 98,0 | 1,333 · 1,000 · 0,667 · 0,500 | 32,7 · 65,3 · 130,7 · 196,0 |

| T | PAM con P 0,1 · 0,25 · 0,5 · 0,75 · 1 · 1,5 |
|---|---|
| 1 | 6,5 · 16,3 · 32,7 · 49,0 · 65,3 · 98,0 |
| 2 | 10,1 · 25,1 · 50,3 · 75,4 · 100,5 · 150,8 |
| 1 (V −75 %, −50 %, 0, +50 %, +100 % del llenado de llegada) | 20,8 · 38,3 · 65,3 · 84,5 · 98,0 |
<!-- /generado:acoplamiento -->

## 7. Presiones registradas (generado)

<!-- generado:registradas -->
- **57m:** PAS 88 y PAD 54 mmHg (`clinical_cases.py:881`, AUTHORED_OBSERVATION); PAM 65.3 (derived, not authored) (MODEL_DERIVED, (SBP + 2 DBP) / 3). Observaciones posteriores de presión registradas: 0. El motor heredado tiene trayectorias de presión: LEGACY_REFERENCE, nunca leídas.
- **72f:** PAS 98 y PAD 62 mmHg (`clinical_cases.py:910`, AUTHORED_OBSERVATION); PAM 74.0 (derived, not authored) (MODEL_DERIVED, (SBP + 2 DBP) / 3). Observaciones posteriores de presión registradas: 0. El motor heredado tiene trayectorias de presión: LEGACY_REFERENCE, nunca leídas.
<!-- /generado:registradas -->

## 8. Presión de llegada reconstruida (generado)

- Con la severidad de llegada conservada (57m D0 60 y entrega 0,24; 72f D0 20 y entrega 0,34), la llegada modelada
  reproduce exactamente la registrada.
- **Es por construcción:** p vale 1 en la llegada y la escala es la presión registrada. El desajuste 0 no prueba nada,
  y la severidad de llegada no tiene ningún camino hacia la presión de llegada.

<!-- generado:llegada -->
| Caso · demanda | Par (D0, entrega) | Gasto | T | PAS / PAD / PAM modeladas | Registradas | Desajuste |
|---|---|---|---|---|---|---|
| 57m · 1,0 | D0 60, 0,24 | 1,00 | 1 | 88,0 / 54,0 / 65,3 | 88 / 54 / 65,3 | 0,0 / 0,0 / 0,0 |
| 57m · 1,1 | D0 60, 0,24 | 1,00 | 1 | 88,0 / 54,0 / 65,3 | 88 / 54 / 65,3 | 0,0 / 0,0 / 0,0 |
| 72f · 1,0 | D0 20, 0,34 | 1,00 | 1 | 98,0 / 62,0 / 74,0 | 98 / 62 / 74,0 | 0,0 / 0,0 / 0,0 |
| 72f · 1,1 | D0 20, 0,34 | 1,00 | 1 | 98,0 / 62,0 / 74,0 | 98 / 62 / 74,0 | 0,0 / 0,0 / 0,0 |
<!-- /generado:llegada -->

## 9. Normalización

- **Antes de P2J-1: mixta.** PAS y PAD estaban en mmHg absolutos, anclados en la llegada registrada con ganancias
  absolutas heredadas, mientras que p y el término de la FC eran relativos a la llegada. Además, 1 − p no era el déficit
  relativo de la PAM: la recta movía la PAM 31,7 mmHg por unidad de p, casi la mitad de la PAM de llegada.
- **Desde P2J-1: ABSOLUTE_MMHG_ANCHORED_ON_AUTHORED_ARRIVAL.** PAS, PAD y PAM son mmHg absolutos y clínicamente
  interpretables, con escala en la presión registrada de llegada, y PAM / PAM de llegada = p exactamente.
- **Sin referencia inventada:** ningún caso declara una presión normal (euvolémica). El punto de ajuste de un
  barorreflejo será un número docente (§16).
- **No es un bloqueo estructural:** la arquitectura ya produce una PAM absoluta interpretable.

## 10. La corrección estructural y lo que cambió (generado)

- **Qué se corrigió, en `derived.arterial_pressures`:** el empalme en la rodilla (el quiebre) y la resistencia propia
  de la recta (el tono oculto, que habría contado dos veces con cualquier respuesta explícita del tono).
- **Por qué esta forma es la mínima:**
  - no añade ningún parámetro;
  - extiende a todo el rango la regla que P2E-4 ya usaba bajo la rodilla (presión proporcional a flujo × resistencia),
    a la resistencia de llegada;
  - por debajo de la llegada coincide con la familia previa con rodilla 1; por encima, reemplaza la recta heredada, que
    ningún valor de la rodilla convierte en proporcional.
- **Alternativas descartadas:**
  - Suavizar la rodilla conservando las ganancias heredadas exige elegir una forma funcional nueva (potencia,
    hipérbola) y conserva el tono oculto.
  - Una respuesta explícita del tono exige parámetros nuevos.
  - Ninguna se toma sin autorización docente.
- **Golden:** sólo cambian PAS, PAD, PAM y la conciencia; quedan registrados como P2J-1.
  - `shadow.DECISIONS` marca P2J-1 como «approved»: sólo la dirección que pidió la docencia en el encargo (continua,
    monótona con el gasto y con el tono, 0 sin gasto). De esa entrada depende que el golden clasifique esas diferencias
    como APPROVED_DIRECTION_MAGNITUDE_TBD y no como UNRESOLVED.
  - La forma proporcional, que fija cuánto difiere el núcleo del motor heredado, está por confirmar (§18.1). En la hora sin tratamiento de
  57m, la PAS del núcleo baja de 80 mmHg desde el minuto 31, y KD-S3 vuelve a actuar. Contracts v2 reproduce el nuevo
  golden.

<!-- generado:cambio -->
- **Cambia:** SBP, DBP, MAP, pulse pressure, consciousness (SBP thresholds 80 / 65).
- **No cambia:** output, T, p, BloodState, V, Hb, delivery, deficit, D, lactate, RR, HR (the drive reads p, not SBP), CRT.
- **Mayor cambio en las trayectorias de decisión** (160446 minutos con pulso): PAS 25,7, PAD 17,3, PAM 20,1 mmHg. En la llegada no cambia: sí.
<!-- /generado:cambio -->

## 11. Superficie candidata, congelada antes de las trayectorias (generado)

<!-- generado:superficie -->
- **Relación:** `SBP = SBP_arrival x p, DBP = DBP_arrival x p, p = output x T`; parámetros libres: 0. Es estructural (la corrección de P2J-1): no es candidata.
- **Sensibilidad a la poscarga a:** 0,1, 0,3, 0,5, la banda registrada en `calibration.REGISTRY` (P2G, provisional); una dimensión, sólo en las sondas sintéticas P5, porque sólo actúa con T ≠ 1.
- **Referencia del tono:** 1, por la regla de anclaje (§7.4 de la propuesta); no es candidata.
- **Respuesta del tono:** `NOT_AUTHORIZED`. Ningún mecanismo escribe T; una respuesta del tono pide parámetros nuevos (ganancia, punto de ajuste, constante de tiempo) cuyos rangos debe autorizar la docencia.
- **Bomba:** 1; ningún mecanismo GI escribe P.
- **Fisiología previa:** la sangre y los líquidos conservados (las unidades de lactato de P2I-2AJ y P2I-2AK con demanda 1,0 y 1,1) se arrastran como incertidumbre; no se reabren ni se refiltran.

**Cómo se construyó, antes de cualquier trayectoria:** la banda registrada del único parámetro de presión que queda, su límite dimensional (a < 1, para que el gasto siga positivo y la presión suba con el tono), las presiones registradas de llegada como escala y las sondas sintéticas. No se leyó ninguna trayectoria GI ni presión heredada. No hay envolventes de presión más allá de la llegada, así que no se aplica ningún filtro.
<!-- /generado:superficie -->

## 12. Trayectorias de decisión P1–P4 sobre la fisiología conservada (generado)

- **Cómo se leen:** BAJO / mediana / ALTO sobre los conjuntos de sangre que usan las unidades de lactato conservadas
  con demanda 1,0 o 1,1. La presión no depende de la demanda ni del lado del lactato, así que cada trayectoria se
  simula una vez por conjunto.
- **Lo que muestran:**
  - Sin tratamiento (P1), la presión cae con el gasto y nada la compensa.
  - El cristaloide (P2) la sube rápido, con una mediana de 118/72 mmHg en 57m a los 30 min (hasta 123/75), y la pierde a
    medida que se redistribuye.
  - Los GR (P3, P4) la llevan por encima de la llegada; la hemostasia la sostiene.
- **La columna «PAM antes de P2J-1»** es la misma salida de gasto leída con la relación previa: muestra cuánto
  amortiguaba el tono oculto.

<!-- generado:trayectorias -->
**P1 · sin tratamiento (L1)**

| Caso | Min | Gasto | PAS | PAD | PAM | PP | PAM antes de P2J-1 | Sangrado (mL/min) | Cristaloide | GR (U) |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m | 0 | 1,00 | 88,0 | 54,0 | 65,3 | 34,0 | 65,3 | 2,50 | 0 | 0,00 |
| 57m | 15 | 0,94 / 0,94 / 0,96 | 82,4 / 82,7 / 84,1 | 50,6 / 50,7 / 51,6 | 61,2 / 61,4 / 62,4 | 31,9 / 31,9 / 32,5 | 63,3 / 63,4 / 63,9 | 2,50 | 0 | 0,00 |
| 57m | 30 | 0,87 / 0,88 / 0,91 | 76,8 / 77,7 / 80,2 | 47,1 / 47,7 / 49,2 | 57,0 / 57,7 / 59,5 | 29,7 / 30,0 / 31,0 | 61,3 / 61,6 / 62,5 | 2,50 | 0 | 0,00 |
| 57m | 60 | 0,74 / 0,77 / 0,83 | 65,4 / 68,1 / 72,6 | 40,1 / 41,8 / 44,6 | 48,5 / 50,6 / 53,9 | 25,3 / 26,3 / 28,1 | 57,2 / 58,2 / 59,8 | 2,50 | 0 | 0,00 |
| 57m | 90 | 0,61 / 0,65 / 0,74 | 53,7 / 57,0 / 65,1 | 33,0 / 34,9 / 40,0 | 39,9 / 42,3 / 48,4 | 20,8 / 22,0 / 25,2 | 53,0 / 54,2 / 57,1 | 2,50 | 0 | 0,00 |
| 57m | 120 | 0,48 / 0,50 / 0,65 | 42,0 / 43,9 / 56,9 | 25,7 / 26,9 / 34,9 | 31,1 / 32,6 / 42,2 | 16,2 / 17,0 / 22,0 | 47,2 / 49,4 / 54,1 | 2,50 | 0 | 0,00 |
| 72f | 0 | 1,00 | 98,0 | 62,0 | 74,0 | 36,0 | 74,0 | 2,50 | 0 | 0,00 |
| 72f | 15 | 0,96 / 0,96 / 0,97 | 93,9 / 94,0 / 95,1 | 59,4 / 59,5 / 60,2 | 70,9 / 71,0 / 71,8 | 34,5 / 34,5 / 34,9 | 72,7 / 72,7 / 73,1 | 2,50 | 0 | 0,00 |
| 72f | 30 | 0,92 / 0,92 / 0,94 | 89,7 / 90,3 / 92,2 | 56,8 / 57,1 / 58,3 | 67,7 / 68,2 / 69,6 | 33,0 / 33,2 / 33,9 | 71,3 / 71,5 / 72,1 | 2,50 | 0 | 0,00 |
| 72f | 60 | 0,83 / 0,85 / 0,88 | 81,2 / 83,2 / 86,6 | 51,4 / 52,7 / 54,8 | 61,3 / 62,8 / 65,4 | 29,8 / 30,6 / 31,8 | 68,6 / 69,2 / 70,3 | 2,50 | 0 | 0,00 |
| 72f | 90 | 0,74 / 0,76 / 0,83 | 72,6 / 75,0 / 81,0 | 45,9 / 47,4 / 51,3 | 54,8 / 56,6 / 61,2 | 26,7 / 27,5 / 29,8 | 65,8 / 66,6 / 68,5 | 2,50 | 0 | 0,00 |
| 72f | 120 | 0,65 / 0,67 / 0,76 | 63,8 / 65,2 / 74,9 | 40,4 / 41,3 / 47,4 | 48,2 / 49,3 / 56,5 | 23,4 / 24,0 / 27,5 | 63,0 / 63,4 / 66,5 | 2,50 | 0 | 0,00 |

Conjuntos de sangre: 37 (57m) y 37 (72f). T vale 1 en todos los minutos.

**P2 · 2 L de cristaloide en 20 min, sangrado activo (L2)**

| Caso | Min | Gasto | PAS | PAD | PAM | PP | PAM antes de P2J-1 | Sangrado (mL/min) | Cristaloide | GR (U) |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m | 0 | 1,00 | 88,0 | 54,0 | 65,3 | 34,0 | 65,3 | 2,50 | 0 | 0,00 |
| 57m | 15 | 1,24 / 1,32 / 1,35 | 109,1 / 116,5 / 118,5 | 67,0 / 71,5 / 72,7 | 81,0 / 86,5 / 88,0 | 42,2 / 45,0 / 45,8 | 72,9 / 75,6 / 76,3 | 2,50 | 300 | 0,00 |
| 57m | 30 | 1,24 / 1,34 / 1,39 | 109,1 / 117,6 / 122,7 | 66,9 / 72,2 / 75,3 | 81,0 / 87,3 / 91,1 | 42,1 / 45,4 / 47,4 | 72,9 / 76,0 / 77,8 | 2,50 | 400 | 0,00 |
| 57m | 60 | 1,09 / 1,20 / 1,28 | 96,0 / 105,9 / 112,2 | 58,9 / 65,0 / 68,9 | 71,3 / 78,6 / 83,3 | 37,1 / 40,9 / 43,4 | 68,2 / 71,8 / 74,0 | 2,50 | 400 | 0,00 |
| 57m | 90 | 0,93 / 1,08 / 1,14 | 82,1 / 94,8 / 100,5 | 50,4 / 58,2 / 61,7 | 60,9 / 70,4 / 74,6 | 31,7 / 36,6 / 38,8 | 63,2 / 67,8 / 69,8 | 2,50 | 400 | 0,00 |
| 57m | 120 | 0,77 / 0,95 / 1,00 | 67,9 / 83,2 / 87,7 | 41,7 / 51,1 / 53,8 | 50,4 / 61,8 / 65,1 | 26,2 / 32,2 / 33,9 | 58,1 / 63,6 / 65,2 | 2,50 | 400 | 0,00 |
| 72f | 0 | 1,00 | 98,0 | 62,0 | 74,0 | 36,0 | 74,0 | 2,50 | 0 | 0,00 |
| 72f | 15 | 1,16 / 1,22 / 1,23 | 113,7 / 119,2 / 120,6 | 71,9 / 75,4 / 76,3 | 85,8 / 90,0 / 91,1 | 41,8 / 43,8 / 44,3 | 79,1 / 80,8 / 81,3 | 2,50 | 300 | 0,00 |
| 72f | 30 | 1,16 / 1,22 / 1,26 | 113,6 / 119,7 / 123,7 | 71,9 / 75,7 / 78,3 | 85,8 / 90,4 / 93,4 | 41,7 / 44,0 / 45,5 | 79,1 / 81,0 / 82,3 | 2,50 | 400 | 0,00 |
| 72f | 60 | 1,06 / 1,14 / 1,18 | 104,0 / 111,3 / 116,0 | 65,8 / 70,4 / 73,4 | 78,5 / 84,0 / 87,6 | 38,2 / 40,9 / 42,6 | 75,9 / 78,3 / 79,8 | 2,50 | 400 | 0,00 |
| 72f | 90 | 0,96 / 1,05 / 1,09 | 93,6 / 103,0 / 107,3 | 59,2 / 65,2 / 67,9 | 70,7 / 77,8 / 81,0 | 34,4 / 37,9 / 39,4 | 72,6 / 75,6 / 77,0 | 2,50 | 400 | 0,00 |
| 72f | 120 | 0,85 / 0,96 / 1,00 | 83,1 / 94,4 / 97,7 | 52,6 / 59,8 / 61,8 | 62,7 / 71,3 / 73,8 | 30,5 / 34,7 / 35,9 | 69,2 / 72,9 / 73,9 | 2,50 | 400 | 0,00 |

Conjuntos de sangre: 444 (57m) y 444 (72f). T vale 1 en todos los minutos.

**P3 · IBP y 2 U de GR sin hemostasia (L3 sin la endoscopia)**

| Caso | Min | Gasto | PAS | PAD | PAM | PP | PAM antes de P2J-1 | Sangrado (mL/min) | Cristaloide | GR (U) |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m | 0 | 1,00 | 88,0 | 54,0 | 65,3 | 34,0 | 65,3 | 2,00 | 0 | 0,00 |
| 57m | 15 | 1,11 / 1,17 / 1,18 | 98,0 / 103,1 / 104,0 | 60,2 / 63,2 / 63,8 | 72,8 / 76,5 / 77,2 | 37,9 / 39,8 / 40,2 | 68,9 / 70,8 / 71,1 | 2,00 | 0 | 0,50 |
| 57m | 30 | 1,22 / 1,33 / 1,33 | 107,4 / 116,7 / 117,0 | 65,9 / 71,6 / 71,8 | 79,8 / 86,7 / 86,9 | 41,5 / 45,1 / 45,2 | 72,3 / 75,7 / 75,8 | 2,00 | 0 | 1,00 |
| 57m | 60 | 1,42 / 1,55 / 1,60 | 124,6 / 136,5 / 140,4 | 76,4 / 83,7 / 86,2 | 92,5 / 101,3 / 104,2 | 48,1 / 52,7 / 54,2 | 78,5 / 82,8 / 84,2 | 2,00 | 0 | 2,00 |
| 57m | 90 | 1,36 / 1,50 / 1,54 | 119,4 / 132,3 / 135,9 | 73,3 / 81,2 / 83,4 | 88,6 / 98,2 / 100,9 | 46,1 / 51,1 / 52,5 | 76,6 / 81,3 / 82,6 | 2,00 | 0 | 2,00 |
| 57m | 120 | 1,30 / 1,45 / 1,49 | 114,0 / 127,7 / 131,2 | 70,0 / 78,4 / 80,5 | 84,6 / 94,8 / 97,4 | 44,0 / 49,3 / 50,7 | 74,7 / 79,6 / 80,9 | 2,00 | 0 | 2,00 |
| 72f | 0 | 1,00 | 98,0 | 62,0 | 74,0 | 36,0 | 74,0 | 2,00 | 0 | 0,00 |
| 72f | 15 | 1,08 / 1,11 / 1,12 | 105,4 / 109,0 / 109,8 | 66,7 / 69,0 / 69,5 | 79,6 / 82,3 / 82,9 | 38,7 / 40,1 / 40,4 | 76,4 / 77,6 / 77,8 | 2,00 | 0 | 0,50 |
| 72f | 30 | 1,15 / 1,21 / 1,22 | 112,3 / 119,1 / 119,5 | 71,0 / 75,3 / 75,6 | 84,8 / 89,9 / 90,3 | 41,2 / 43,7 / 43,9 | 78,6 / 80,8 / 81,0 | 2,00 | 0 | 1,00 |
| 72f | 60 | 1,27 / 1,37 / 1,39 | 124,8 / 134,0 / 136,4 | 79,0 / 84,8 / 86,3 | 94,2 / 101,2 / 103,0 | 45,8 / 49,2 / 50,1 | 82,7 / 85,6 / 86,4 | 2,00 | 0 | 2,00 |
| 72f | 90 | 1,23 / 1,34 / 1,36 | 121,0 / 130,9 / 133,1 | 76,6 / 82,8 / 84,2 | 91,4 / 98,8 / 100,5 | 44,5 / 48,1 / 48,9 | 81,4 / 84,6 / 85,3 | 2,00 | 0 | 2,00 |
| 72f | 120 | 1,19 / 1,30 / 1,32 | 117,1 / 127,5 / 129,6 | 74,1 / 80,6 / 82,0 | 88,4 / 96,3 / 97,9 | 43,0 / 46,8 / 47,6 | 80,2 / 83,5 / 84,2 | 2,00 | 0 | 2,00 |

Conjuntos de sangre: 91 (57m) y 91 (72f). T vale 1 en todos los minutos.

**P4 · manejo definitivo: IBP, 2 U de GR y hemostasia a los 60 (L3)**

| Caso | Min | Gasto | PAS | PAD | PAM | PP | PAM antes de P2J-1 | Sangrado (mL/min) | Cristaloide | GR (U) |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m | 0 | 1,00 | 88,0 | 54,0 | 65,3 | 34,0 | 65,3 | 2,00 | 0 | 0,00 |
| 57m | 15 | 1,11 / 1,17 / 1,18 | 98,0 / 103,1 / 104,0 | 60,2 / 63,2 / 63,8 | 72,8 / 76,5 / 77,2 | 37,9 / 39,8 / 40,2 | 68,9 / 70,8 / 71,1 | 2,00 | 0 | 0,50 |
| 57m | 30 | 1,22 / 1,33 / 1,33 | 107,4 / 116,7 / 117,0 | 65,9 / 71,6 / 71,8 | 79,8 / 86,7 / 86,9 | 41,5 / 45,1 / 45,2 | 72,3 / 75,7 / 75,8 | 2,00 | 0 | 1,00 |
| 57m | 60 | 1,42 / 1,55 / 1,60 | 124,7 / 136,6 / 140,5 | 76,5 / 83,8 / 86,2 | 92,6 / 101,4 / 104,3 | 48,2 / 52,8 / 54,3 | 78,5 / 82,8 / 84,2 | 0,25 | 0 | 2,00 |
| 57m | 90 | 1,41 / 1,55 / 1,59 | 124,1 / 136,1 / 140,0 | 76,1 / 83,5 / 85,9 | 92,1 / 101,0 / 103,9 | 47,9 / 52,6 / 54,1 | 78,3 / 82,6 / 84,0 | 0,25 | 0 | 2,00 |
| 57m | 120 | 1,40 / 1,54 / 1,58 | 123,4 / 135,6 / 139,4 | 75,8 / 83,2 / 85,6 | 91,7 / 100,7 / 103,5 | 47,7 / 52,4 / 53,9 | 78,1 / 82,5 / 83,8 | 0,25 | 0 | 2,00 |
| 72f | 0 | 1,00 | 98,0 | 62,0 | 74,0 | 36,0 | 74,0 | 2,00 | 0 | 0,00 |
| 72f | 15 | 1,08 / 1,11 / 1,12 | 105,4 / 109,0 / 109,8 | 66,7 / 69,0 / 69,5 | 79,6 / 82,3 / 82,9 | 38,7 / 40,1 / 40,4 | 76,4 / 77,6 / 77,8 | 2,00 | 0 | 0,50 |
| 72f | 30 | 1,15 / 1,21 / 1,22 | 112,3 / 119,1 / 119,5 | 71,0 / 75,3 / 75,6 | 84,8 / 89,9 / 90,3 | 41,2 / 43,7 / 43,9 | 78,6 / 80,8 / 81,0 | 2,00 | 0 | 1,00 |
| 72f | 60 | 1,27 / 1,37 / 1,39 | 124,9 / 134,1 / 136,5 | 79,0 / 84,8 / 86,4 | 94,3 / 101,2 / 103,1 | 45,9 / 49,2 / 50,1 | 82,7 / 85,7 / 86,4 | 0,25 | 0 | 2,00 |
| 72f | 90 | 1,27 / 1,36 / 1,39 | 124,4 / 133,7 / 136,1 | 78,7 / 84,6 / 86,1 | 94,0 / 101,0 / 102,8 | 45,7 / 49,1 / 50,0 | 82,5 / 85,5 / 86,3 | 0,25 | 0 | 2,00 |
| 72f | 120 | 1,27 / 1,36 / 1,38 | 124,0 / 133,3 / 135,7 | 78,4 / 84,3 / 85,8 | 93,6 / 100,7 / 102,5 | 45,5 / 49,0 / 49,8 | 82,4 / 85,4 / 86,2 | 0,25 | 0 | 2,00 |

Conjuntos de sangre: 91 (57m) y 91 (72f). T vale 1 en todos los minutos.
<!-- /generado:trayectorias -->

Contexto de oxígeno: el déficit efectivo y D dependen del lado del lactato y de la demanda. Vienen de las corridas
completas de la muestra de validación (tres unidades por demanda) y son sólo contexto.

<!-- generado:contexto -->
| Escenario · caso · demanda | Déficit efectivo a 0 · 30 · 60 · 120 | D a 0 · 30 · 60 · 120 |
|---|---|---|
| P1 · 57m · 1,0 | 0,400 · 0,456 / 0,476 / 0,476 · 0,511 / 0,552 / 0,553 · 0,619 / 0,707 / 0,719 | 60,0 · 85,6 / 86,2 / 86,2 · 114,6 / 117,0 / 117,0 · 182,3 / 192,3 / 192,7 |
| P1 · 57m · 1,1 | 0,500 · 0,554 / 0,556 / 0,576 · 0,609 / 0,611 / 0,653 · 0,717 / 0,719 / 0,819 | 60,0 · 67,9 / 67,9 / 68,0 · 76,6 / 76,6 / 77,2 · 96,5 / 96,6 / 99,2 |
| P1 · 72f · 1,0 | 0,150 · 0,202 / 0,222 / 0,222 · 0,254 / 0,295 / 0,296 · 0,356 / 0,444 / 0,456 | 20,0 · 30,5 / 31,1 / 31,1 · 44,1 / 46,5 / 46,5 · 80,6 / 90,7 / 91,1 |
| P1 · 72f · 1,1 | 0,250 · 0,302 / 0,302 / 0,322 · 0,354 / 0,354 / 0,396 · 0,456 / 0,459 / 0,556 | 20,0 · 24,1 / 24,1 / 24,3 · 29,0 / 29,0 / 29,6 · 41,2 / 41,2 / 43,8 |
| P2 · 57m · 1,0 | 0,400 · 0,261 / 0,279 / 0,281 · 0,362 / 0,371 / 0,373 · 0,518 / 0,548 / 0,562 | 60,0 · 77,0 / 77,8 / 78,1 · 95,5 / 97,2 / 97,6 · 150,6 / 151,3 / 153,4 |
| P2 · 57m · 1,1 | 0,500 · 0,379 / 0,381 / 0,405 · 0,471 / 0,473 / 0,481 · 0,616 / 0,618 / 0,662 | 60,0 · 65,9 / 66,0 / 66,3 · 72,3 / 72,4 / 72,9 · 88,8 / 89,3 / 89,4 |
| P2 · 72f · 1,0 | 0,150 · 0,040 / 0,056 / 0,063 · 0,129 / 0,136 / 0,145 · 0,270 / 0,302 / 0,318 | 20,0 · 23,3 / 24,2 / 24,3 · 28,2 / 29,9 / 30,4 · 54,4 / 54,5 / 58,2 |
| P2 · 72f · 1,1 | 0,250 · 0,156 / 0,163 / 0,181 · 0,236 / 0,245 / 0,247 · 0,370 / 0,372 / 0,418 | 20,0 · 22,6 / 22,6 / 22,8 · 25,5 / 25,6 / 26,0 · 34,6 / 35,4 / 35,5 |
| P3 · 57m · 1,0 | 0,400 · 0,074 / 0,079 / 0,085 · 0,000 · 0,000 | 60,0 · 74,4 / 74,5 / 74,9 · 35,6 / 36,9 / 37,1 · 4,7 / 4,8 / 4,9 |
| P3 · 57m · 1,1 | 0,500 · 0,179 / 0,216 / 0,218 · 0,000 · 0,000 / 0,019 / 0,028 | 60,0 · 65,1 / 65,4 / 65,4 · 45,4 / 54,5 / 60,4 · 5,9 / 11,9 / 20,6 |
| P3 · 72f · 1,0 | 0,150 · 0,000 · 0,000 · 0,000 | 20,0 · 11,9 / 12,3 / 12,4 · 4,3 / 4,5 / 4,5 · 0,6 |
| P3 · 72f · 1,1 | 0,250 · 0,000 · 0,000 · 0,000 | 20,0 · 15,7 / 17,6 / 18,2 · 5,7 / 6,3 / 6,6 · 0,7 / 0,8 / 0,9 |
| P4 · 57m · 1,0 | 0,400 · 0,074 / 0,079 / 0,085 · 0,000 · 0,000 | 60,0 · 74,4 / 74,5 / 74,9 · 35,6 / 36,9 / 37,1 · 4,7 / 4,8 / 4,9 |
| P4 · 57m · 1,1 | 0,500 · 0,179 / 0,216 / 0,218 · 0,000 · 0,000 | 60,0 · 65,1 / 65,4 / 65,4 · 45,4 / 54,5 / 60,4 · 5,9 / 7,1 / 7,9 |
| P4 · 72f · 1,0 | 0,150 · 0,000 · 0,000 · 0,000 | 20,0 · 11,9 / 12,3 / 12,4 · 4,3 / 4,5 / 4,5 · 0,6 |
| P4 · 72f · 1,1 | 0,250 · 0,000 · 0,000 · 0,000 | 20,0 · 15,7 / 17,6 / 18,2 · 5,7 / 6,3 / 6,6 · 0,7 / 0,8 / 0,9 |
<!-- /generado:contexto -->

## 13. Invariantes direccionales (generado)

<!-- generado:direcciones -->
1. si el gasto baja con T fijo, la PAM no sube (P6 y cada par de minutos consecutivos de cada trayectoria, T = 1) — **cumple: sí**.
2. si el gasto sube con T fijo, la PAM no baja (los mismos pares) — **cumple: sí**.
3. más tono con gasto fijo no baja la PAM (P5 con gasto fijo, en cada punto de poscarga) — **cumple: sí**.
4. sin gasto no se conserva una presión normal (P7) — **cumple: sí**.
5. la hemorragia sin tratamiento no normaliza sola la presión: en P1 la PAM nunca supera la de llegada en los minutos 1–120, en cada conjunto de sangre — **cumple: sí**. Conjuntos: 74; fallan: 0.
6. la reanimación eficaz puede mejorar la presión: en P4, PAM a los 120 sobre la de llegada en al menos un conjunto (alcanzabilidad, contada) — **alcanzable: sí (182 de 182)**.
7. la hemostasia sola no normaliza al instante: P4 es igual a P3 antes del minuto de hemostasia h, y el paso de la PAM hacia h no supera el mayor paso de un minuto anterior, en cada conjunto — **cumple: sí**. Minuto de hemostasia: 60; efecto propio sobre la PAM en ese minuto: 0,05 / 0,08 / 0,11 mmHg.
8. la respuesta de la presión a líquidos o sangre pasa por la fisiología, no por la identidad del tratamiento: en cada minuto PAM = PAM de llegada × gasto × T exactamente, y `arterial_pressures` sólo lee p y la llegada — **cumple: sí**.
<!-- /generado:direcciones -->

## 14. Identificabilidad (generado)

<!-- generado:identificabilidad -->
| Latente | Clase | Por qué |
|---|---|---|
| sensibilidad a la poscarga | NON_IDENTIFIABLE | sólo llega al gasto y a la presión con T ≠ 1, y T vale 1 en todos los escenarios GI |
| parámetro de gasto bajo | NON_IDENTIFIABLE | no queda ninguno: OUTPUT_EPSILON es numérico y la regla de colapso está apagada |
| forma no lineal / rodilla | NON_IDENTIFIABLE | antes de P2J-1, la rodilla y las dos ganancias no tenían ninguna presión registrada fuera de la llegada que las acotara; desde P2J-1 no hay parámetro de forma |
| escala de la relación | WELL_CONSTRAINED | sólo por anclaje: la PAS y la PAD registradas de llegada de cada caso, exactas; la reconstrucción de la llegada es exacta por construcción y no hay ninguna presión registrada posterior, así que la forma fuera de la llegada no está probada |
| interacción bomba / tono | NON_IDENTIFIABLE | P y T valen 1 en todos los escenarios GI; sólo las sondas sintéticas P5 y P6 los mueven |
| nivel de referencia del tono | NON_IDENTIFIABLE | T vale 1 en la llegada por la regla de anclaje y ningún mecanismo GI lo mueve: cualquier referencia queda absorbida por la presión registrada de llegada |

Las únicas observaciones de presión son dos, una por caso y en la llegada, donde el modelo las reproduce por construcción. No se elige ningún conjunto.
<!-- /generado:identificabilidad -->

## 15. Propagación de la FC y de la demanda (generado)

<!-- generado:dependencia -->
- **Código:** la ruta de la presión (_perfusion, preload_position, arrival_filling, arrival_preload, arterial_pressures) lee 39 nombres y ninguno prohibido (0); contribuyentes que leen derivados: 0.
- **Números:** 240 corridas completas de la muestra dan exactamente el gasto, p, PAS, PAD y PAM de la corrida sólo de sangre: demandas 1,0 y 1,1, otro punto de lactato y dos variantes de FC (el perfil primario con las ganancias más altas, techo 150 e intrínseca superior; y la intrínseca inferior con el término de presión diagnóstico del perfil por defecto, el mismo que ya usan las corridas base): sí; D cambia con la demanda: sí.
- **Consecuencia:** la presión no depende de la región de FC ni de la demanda; se simula una vez por conjunto de sangre.
<!-- /generado:dependencia -->

## 16. Plan de reconexión barorrefleja: sólo plan (generado)

<!-- generado:barorreflejo -->
- **Estado:** `PLAN_ONLY`: en P2J-1 la presión → FC sigue PRESSURE_TERM_DIAGNOSTIC_ONLY.
- **Señal:** la PAM absoluta que ahora deriva el dominio de la presión (mmHg, anclada en la llegada registrada) frente a un punto de ajuste que fija la docencia, max(0, PAM_ajuste − PAM) / PAM_ajuste; no el 1 − p relativo a la llegada.
- **Signo:** el impulso sube cuando la PAM cae bajo el punto de ajuste y vale 0 en él o por encima; nunca es negativo (P2D-3), así que no hay bradicardia barorrefleja sin una fuente explícita que cambie R.
- **El término actual 1 − p no debe quedar como está:** relativo a la llegada, vale 0 en una llegada hipotensa (88/54 es su cero), se vuelve negativo sobre la llegada y descuenta los otros estímulos de la suma, y hasta P2J-1 discrepaba de la PAM mostrada por un factor de casi dos (desde P2J-1 es exactamente el déficit relativo de la PAM mostrada respecto de la llegada).
- **Doble conteo:** la señal aguda del déficit de oxígeno y un déficit de presión caen ambos con el gasto (correlación 0,75, P2I-2AF). El término de presión lee la presión (PAM) y el agudo la disponibilidad de oxígeno; la ganancia aguda se vuelve a explorar junto con la barorrefleja sobre la misma superficie de llegada y se informa la varianza compartida; el término nunca se suma encima de la región aguda actual.
- **Pruebas que se repiten:** la ventana de FC de llegada ±5 lpm (P2I-2AI, P2I-2AJ) y las envolventes A–F de P2I-2AK (6).
- **Requiere:** primero las envolventes docentes de presión; después un punto de ajuste y un rango de ganancia autorizados antes de cualquier valor.
<!-- /generado:barorreflejo -->

## 17. Veredicto (generado)

<!-- generado:veredicto -->
**PRESSURE_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION**

- reconstrucción de la llegada para ambos casos y demandas: sí
- superficie candidata congelada y admisible en P5: sí
- direcciones 1–5, 7 y 8: sí
- retroalimentación presión → FC aplazada: sí
- relación continua, suave, monótona, 0 en 0 y sin resistencia oculta: sí
- sin piso ni rodilla: sí
- rutas de T enumeradas, sin escritor clínico: sí
- fisiología previa sin cambios: sí
- gasto cero y paro coherentes (P7): sí
- Parámetros aprobados: 0.
<!-- /generado:veredicto -->

- **Qué quiere decir el veredicto:** la estructura está lista para la calibración numérica docente. Pero en los casos
  GI la relación ya no tiene ningún parámetro propio:
  - la escala es la presión registrada;
  - T y P valen 1;
  - a sólo actúa con T ≠ 1.
- **Consecuencia:** cualquier envolvente docente de presión pondría a prueba la salida de gasto ya certificada, salvo
  que la docencia autorice una respuesta del tono. Eso es lo primero que se pide decidir (§18).

## 18. Decisiones docentes que se piden

1. **Confirmar o reemplazar la relación proporcional.** Deja sin leer las ganancias heredadas (45 y 25 mmHg) y la
   rodilla, y duplica, cerca de la llegada, la sensibilidad de la presión al gasto. Hay que decidir también si la entrada
   «approved» de P2J-1 en `shadow.DECISIONS`, que cubre sólo la dirección, puede seguir así hasta esa confirmación.
2. **Decidir si la presión necesita una respuesta explícita del tono.** Sería una vasoconstricción barorrefleja o
   simpática que escriba T al caer la presión, y que lo relaje cuando el gasto se recupere.
   - Sin ella: 57m llega a PAS 44 a los 120 min sin tratamiento y a 136/83 tras la reanimación; 72f, a 65 y a 133/84.
   - Con ella hay parámetros nuevos (ganancia, punto de ajuste, constante de tiempo, límites de T), cuyos rangos debe
     autorizar la docencia antes de cualquier valor.
3. **Envolventes de presión más allá de la llegada.** Ningún caso registra una presión posterior. Harían falta, por
   ejemplo: la PAM sin tratamiento a los 60 y a los 120, el rango tras la reanimación, y la respuesta y su caída tras
   2 L de cristaloide.
4. **Umbrales de conciencia por PAS** (80 y 65, heredados): ahora leen una PAS que baja más rápido.
5. **Después, la reconexión presión → FC** (§16), con su punto de ajuste y su ganancia, repitiendo A–F de P2I-2AK.

## 19. Eficiencia (generado)

<!-- generado:eficiencia -->
Trayectorias hemodinámicas para reproducir las unidades de lactato: 3178; corridas de presión, una por conjunto de sangre y escenario: 1326 (un diseño por candidato y demanda habría pedido 10464); corridas completas de validación: 240; barrido cartesiano: no; presión heredada leída: no.
<!-- /generado:eficiencia -->

- **Sobre el congelamiento:** antes de él se vieron presiones GI con la relación corregida, cuando la corrección ya estaba
  decidida e implementada:
  - una sonda de tiempo imprimió dos valores de PAM en L3 de un conjunto de sangre;
  - la regeneración del propio congelamiento (golden, P2I-2T, P2I-2U) mostró las presiones nuevas, PAS de hasta 330 en
    extremos de la exploración sintética de P2I-2U.

  No se fijó ninguna regla ni rango después de verlas. Entre `31a74ef` y `e11d6d1`, en `clinical_core` sólo se añadió
  el módulo del informe, y la banda de poscarga 0,1/0,3/0,5 es anterior a P2J-1.
