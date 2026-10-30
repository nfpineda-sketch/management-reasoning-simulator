# P2J-3 · Filtro docente de envolventes observables de presión y tono

- **Fecha:** 2026-10-30. Sólo en sombra. No se aprueba ninguna ganancia, poscarga ni envolvente; la FC es un
  diagnóstico, y la presión no alimenta la FC.
- **Base:** `51bc0ca` (P2J-2, cerrado: su módulo y su registro quedan fijados byte a byte, y su congelamiento se
  recalcula con los archivos de tuplas en sus hashes de P2J-2). Congelamiento de P2J-3: `3d558fd` (digest
  `611e1702…`), antes de contar los supervivientes de la fisiología retenida; la prueba de humo previa se declara en
  §16.
- **Números:** `docs/revision/P2J3_pressure_tone_filter.json`. Las secciones marcadas «generado» las escribe
  `python -m clinical_core.pressure_tone_filter_report` desde ese registro.
- **Sin cambios en el núcleo:** las trayectorias son la reconstrucción exacta de P2J-2 desde las trayectorias de sangre
  en caché. Los comparadores de cristaloide y de GR son contrafactuales emparejados.

## Resumen

- **Qué es un candidato:** un punto de presión y tono (g, a) a una demanda, multiplicado por un candidato fisiológico
  retenido de P2I-2AK (conjunto P3 × punto de cristaloide × base de lactato). Entran 216 candidatos por punto con
  demanda 1,0 y 1092 con 1,1.
- **Filtro primario** (g = 0,25 / 0,5 / 1; a = 0,3):
  - Ninguna envolvente de presión ni de tono rechaza un candidato. A, B, F, C, D, E, G y H se cumplen en todos, y no
    hay rechazo estructural.
  - **Las envolventes tampoco distinguen entre haber respuesta de tono y no haberla.** La referencia sin respuesta
    (g = 0) cumple A, B y F en todas las claves y en ambas demandas. En F, la PAS de 57m queda a 0,6 mmHg del techo
    de 140. C, D y E no se calcularon para g = 0.
  - Sólo FD-LAC (I) recorta, y sólo a demanda 1,0: g = 0,5 deja 181 de 216 y g = 1 deja 134. A demanda 1,1 sobreviven
    los 1092 en las tres ganancias.
  - Las tres ganancias son ROBUST_ACROSS_DEMAND.
- **Sin tratamiento (P1, 120 min, demanda 1,0, medianas por caso):**
  - **57m:** PAS / PAM 45,7 / 33,9 (g = 0,25), 47,4 / 35,2 (g = 0,5) y 50,2 / 37,2 (g = 1); con T = 1, 43,6 / 32,4.
  - **72f:** 68,3 / 51,6, 71,4 / 53,9 y 77,3 / 58,3; con T = 1, 65,0 / 49,1.
  - Todos los valores quedan dentro de A y B.
- **Manejo definitivo (P4, 120 min, demanda 1,0, medianas):**
  - **57m:** 126,7 / 94,1, 118,9 / 88,3 y 105,9 / 78,6.
  - **72f:** 129,9 / 98,1, 126,7 / 95,6 y 120,7 / 91,1.
  - Todos dentro de F. T_abs vale 1 a los 120 tras la adecuación (H).
- **Contrafactuales:** el cristaloide (frente a L1 en el mismo minuto) y la 1.ª y la 2.ª unidad de GR (frente a L3
  sin esa unidad) dan, en todas las trayectorias de los supervivientes y en cada minuto de comparación,
  PRESSURE_AND_PERFUSION_IMPROVE. Ninguna regla C, D ni E rechazó a ningún candidato primario.
  - Bajo el comparador emparejado desaparece la caída de la PAM durante la 1.ª unidad que se veía en P2J-2 con la
    ventana antes/después.
  - Con g = 1, la 1.ª unidad todavía sube la PAM de 57m +7,3 mmHg a los 30 min (demanda 1,0).
- **Tono en shock:** T_abs máximo en P1 de 1,18 (g = 0,25), 1,36 (g = 0,5) y 1,73 (g = 1), en 57m con demanda
  1,0 (1,76 con 1,1). Todos quedan dentro de G, que para g ≤ 1 se cumple por construcción.
- **Costo:** el gasto y el aporte caen −2 % (g = 0,25), −4 % (g = 0,5) y −6 a −8 % (g = 1) a los 120 sin tratamiento.
  No hay umbral: la docencia lo remite a FD-LAC.
- **FC (diagnóstico):** en 2616 corridas completas del núcleo, ninguna regla A–F de P2I-2AK fallaría en ningún
  candidato superviviente.
- **Sensibilidad (después, sin rescatar nada):**
  - **a = 0,1:** sobreviven todos, salvo 24 candidatos de g = 1 a demanda 1,1, que F rechaza.
  - **a = 0,5:** FD-LAC recorta más; con g = 1 quedan 20 de 216 a demanda 1,0.
  - **g = 1,5:** G (T_abs > 2) y FD-LAC lo restringen a 18 candidatos a demanda 1,0 (F no rechaza ninguno ahí). A
    1,1 lo eliminan G y F.
  - **g = 2:** queda incompatible con ambas demandas por G, F, FD-LAC y, a 1,0, también B (48).
  - Las conclusiones primarias son cualitativamente estables con a = 0,1 y 0,5: sobreviven las tres ganancias
    primarias. Con a = 0,5 el recorte es de FD-LAC; con a = 0,1 el único recorte es F (24 candidatos de g = 1 a
    1,1).
- **Identificabilidad:**
  - La ganancia de tono sigue NON_IDENTIFIABLE: las envolventes no distinguen entre 0,25, 0,5 y 1.
  - La poscarga queda POORLY_IDENTIFIED: sólo F con a = 0,1 la distingue.
- **Veredicto: PRESSURE_TONE_OBSERVABLE_FILTER_SATISFIED.**

## 1. Decisiones docentes registradas (generado)

<!-- generado:decisiones -->
- **poscarga**: PRIMARY a = 0.3, the provisional reference, not approved; a = 0.1 and 0.5 SENSITIVITY_ONLY, reported after the primary filter for the qualitative stability of its conclusions
- **fecha**: 2026-10-30
- **demanda**: 1.0 and 1.1 carried separately; robustness across them is not a hard criterion; neither is approved
- **envolventes**: A-I as frozen in ENVELOPES: case / scenario educational calibration envelopes, not universal thresholds; no DBP envelope; pressures above arrival are not pathological by themselves
- **ganancia**: g = 0 DIAGNOSTIC_NO_RESPONSE_REFERENCE; PRIMARY g = 0.25, 0.5, 1.0; SENSITIVITY_ONLY g = 1.5, 2.0, never rescuing a primary region; no g FACULTY_APPROVED (g > 1 is not declared impossible)
- **FC**: HR is a diagnostic in P2J-3 (P2I-2AK A-F under the changed DO2 / D); never a pressure filter unless a structural contradiction appears; pressure -> HR stays deferred
- **normalización**: ACCEPTED: T_abs = 1 + g s, T = (1 + g s) / (1 + g s0), s0 the patient's modelled arrival acute signal; T = 1 means tone relative to that patient's arrival state; T_abs is an internal modelled vasoconstrictor coordinate, not a measured absolute SVR; no universal normal s0 or premorbid SVR
- **gasto tras la reanimación**: post-resuscitation Q about 1.4-1.8 x arrival is not rejected for being above 1: Q = 1 is the shocked arrival, not a normal resting output; BloodState and pump calibration are not reopened for it
- **alcance**: shadow only; no final tone or afterload approval, pressure -> HR reconnection, RR calibration, consciousness recalibration, collapse activation, GI or second-family migration, runtime integration or legacy fitting; BloodState, D, lactate constraints, RR, the P2J-1 mapping and the HR latent ranges unchanged
- **temporalidad**: ACCEPTED: the instantaneous target with the explicit one-step lag; no tone memory, no D-driven vascular memory, no tone time constant (reconsidered only if later cross-domain behaviour requires it)
<!-- /generado:decisiones -->

## 2. Soporte primario y de sensibilidad (generado)

<!-- generado:soporte -->
| ganancia g | estado |
|---|---|
| 0 | DIAGNOSTIC_NO_RESPONSE_REFERENCE |
| 0.25 | PRIMARY |
| 0.5 | PRIMARY |
| 1 | PRIMARY |
| 1.5 | SENSITIVITY_ONLY |
| 2 | SENSITIVITY_ONLY |

| poscarga a | estado |
|---|---|
| 0.1 | SENSITIVITY_ONLY |
| 0.3 | PRIMARY_PROVISIONAL_REFERENCE |
| 0.5 | SENSITIVITY_ONLY |

Pares primarios: (g 0.25, a 0.3), (g 0.5, a 0.3), (g 1, a 0.3). Pares de sensibilidad: (g 0.25, a 0.1), (g 0.5, a 0.1), (g 1, a 0.1), (g 0.25, a 0.5), (g 0.5, a 0.5), (g 1, a 0.5), (g 1.5, a 0.3), (g 2, a 0.3). Los demás pares explorados en P2J-2 cuentan como PRIMARY_RANGE_REJECTION: demanda 1: 3024 candidatos; demanda 1.1: 15288 candidatos.
<!-- /generado:soporte -->

## 3. Envolventes A–I, minutos y clases de comparación (generado)

H se lee con el retraso de un paso que la docencia aceptó: un minuto sin déficit deja T_abs = 1 en el minuto
siguiente. En el mismo minuto, T_abs todavía refleja el minuto anterior (§13).

<!-- generado:envolventes -->
- **A**: untreated 57m at 120: 40 <= SBP <= 70 and 30 <= MAP <= 50 mmHg.
- **B**: untreated 72f at 120: 60 <= SBP <= 95 and 45 <= MAP <= 70 mmHg.
- **C**: crystalloid against its matched same-time untreated counterfactual: no PRESSURE_AND_PERFUSION_WORSEN at the comparison times; a zero or negative pressure change with improving perfusion is kept.
- **D**: first PRBC unit against L3 without it: no PRBC_CAUSES_PRESSURE_AND_PERFUSION_WORSENING at the comparison times.
- **E**: second PRBC unit against L3 without it: the same rule; no size relation to unit 1 is required.
- **F**: definitive management (haemostasis, sustained adequacy), both cases, at 120: 90 <= SBP <= 140 and 65 <= MAP <= 105 mmHg; no DBP envelope.
- **G**: T_abs within [1.0, 2.0] at every minute of the clinical haemorrhage scenarios (a broad physiological exploration envelope, not an SVR range); synthetic probes reported separately.
- **H**: when the effective deficit is zero the acute tone resolves: with the accepted one-step lag, every minute m with deficit(m) = 0 gives T_abs(m + 1) = 1 to numerical precision; no time constant or memory tolerance.
- **I**: the candidate keeps FD-LAC and L3 adequacy (P2I-2AD's rules, unchanged) under its own tone; a pressure / tone point with zero FD-LAC-compatible candidates at a compatible demand is CROSS_DOMAIN_INCOMPATIBLE there; no minimum retained share.

Minutos de comparación (congelados): C: crystalloid volume complete, 120; D: unit 1 complete, 120; E: unit 2 complete, 120.

At each comparison minute: delta = intervention - matched counterfactual for MAP, SBP, output Q, delivery and the effective deficit. Pressure improves when delta MAP > 0, worsens when < 0; perfusion improves when delta delivery > 0, worsens when < 0 (at equal demand the effective deficit then moves the other way or stays 0); a delta within 1e-9 of its scale is no change. Classes: PRESSURE_AND_PERFUSION_IMPROVE; PRESSURE_NONIMPROVING_WITH_PERFUSION_IMPROVEMENT; PRESSURE_IMPROVING_WITH_PERFUSION_WORSENING; PRESSURE_UNCHANGED_WITH_PERFUSION_WORSENING; NO_PERFUSION_CHANGE; PRESSURE_AND_PERFUSION_WORSEN. Only the last rejects (for the red cells named PRBC_CAUSES_PRESSURE_AND_PERFUSION_WORSENING); a pressure fall alone never does.
<!-- /generado:envolventes -->

## 4. Orden congelado del filtro (generado)

<!-- generado:orden -->
SUPPORT → SIMULATION → G → H → A → B → F → C → D → E → I

Fixed before any count, cheapest first: the support (a table lookup), a structural guard (a run that stops or meets T's guard), G and H (read on every minute already rebuilt; G holds analytically for g <= 1 since T_abs = 1 + g s <= 1 + g), A and B (one P1 trajectory per case), F (P4), C (a P2 / P1 pair per crystalloid point, the most trajectories), D and E (P4 against its counterfactuals), I last (FD-LAC re-read: the most expensive). Every rule is evaluated for every candidate; the first failure in ORDER is the counted one, every failure and every pair of failures is reported too.
<!-- /generado:orden -->

## 5. Filtro primario (generado)

<!-- generado:primario -->
| ganancia (a = 0,3) | demanda | entran | sobreviven | primera falla | toda falla | superposiciones | FD-LAC sola | envolventes solas |
|---|---|---|---|---|---|---|---|---|
| g 0.25 | 1 | 216 | **216** | ninguna | ninguna | ninguna | 216 | 216 |
| g 0.25 | 1.1 | 1092 | **1092** | ninguna | ninguna | ninguna | 1092 | 1092 |
| g 0.5 | 1 | 216 | **181** | I · FD-LAC y adecuación L3: 35 | I: 35 | ninguna | 181 | 216 |
| g 0.5 | 1.1 | 1092 | **1092** | ninguna | ninguna | ninguna | 1092 | 1092 |
| g 1 | 1 | 216 | **134** | I · FD-LAC y adecuación L3: 82 | I: 82 | ninguna | 134 | 216 |
| g 1 | 1.1 | 1092 | **1092** | ninguna | ninguna | ninguna | 1092 | 1092 |
<!-- /generado:primario -->

## 6. Demanda (generado)

<!-- generado:demanda -->
| ganancia (a = 0,3) | clase |
|---|---|
| 0.25 | robusto en ambas demandas |
| 0.5 | robusto en ambas demandas |
| 1 | robusto en ambas demandas |
<!-- /generado:demanda -->

## 7. Observables de los supervivientes primarios (generado)

<!-- generado:observables -->
Sobre las trayectorias únicas de los supervivientes primarios (mediana [rango]); entre paréntesis, la referencia T = 1 en las mismas claves.

| punto | caso | PAS / PAM sin tratamiento a los 120 | PAS / PAM definitivo a los 120 | T_abs máx. (P1) | T_abs a los 120 tras la adecuación |
|---|---|---|---|---|---|
| g0.25 x1 | 57m | 45.7 [44.0–58.3] / 33.9 [32.7–43.3] (43.6 / 32.4) | 126.7 [126.7–130.3] / 94.1 [94.1–96.7] (135.6 / 100.7) | 1.18 [1.16–1.18] | 1.000 [1.000–1.000] |
| g0.25 x1 | 72f | 68.3 [67.1–77.5] / 51.6 [50.7–58.5] (65.0 / 49.1) | 129.9 [129.9–132.2] / 98.1 [98.1–99.8] (133.3 / 100.7) | 1.11 [1.09–1.12] | 1.000 [1.000–1.000] |
| g0.25 x1.1 | 57m | 45.8 [43.8–58.6] / 34.0 [32.5–43.5] (43.9 / 32.6) | 125.6 [114.4–129.2] / 93.2 [84.9–95.9] (135.6 / 100.7) | 1.18 [1.16–1.19] | 1.000 [1.000–1.000] |
| g0.25 x1.1 | 72f | 68.1 [66.7–77.3] / 51.4 [50.4–58.4] (65.2 / 49.3) | 128.2 [119.2–130.5] / 96.8 [90.0–98.5] (133.3 / 100.7) | 1.13 [1.11–1.13] | 1.000 [1.000–1.000] |
| g0.5 x1 | 57m | 47.4 [45.8–60.0] / 35.2 [34.0–44.5] (43.6 / 32.4) | 118.9 [118.9–122.3] / 88.3 [88.3–90.8] (135.6 / 100.7) | 1.36 [1.31–1.36] | 1.000 [1.000–1.000] |
| g0.5 x1 | 72f | 71.4 [70.3–80.1] / 53.9 [53.0–60.5] (65.0 / 49.1) | 126.7 [126.7–128.9] / 95.6 [95.6–97.3] (133.3 / 100.7) | 1.23 [1.19–1.24] | 1.000 [1.000–1.000] |
| g0.5 x1.1 | 57m | 47.3 [45.3–60.1] / 35.1 [33.7–44.6] (43.9 / 32.6) | 117.0 [106.5–120.3] / 86.8 [79.1–89.3] (135.6 / 100.7) | 1.37 [1.33–1.38] | 1.000 [1.000–1.000] |
| g0.5 x1.1 | 72f | 70.8 [69.4–79.5] / 53.4 [52.4–60.1] (65.2 / 49.3) | 123.5 [114.8–125.7] / 93.3 [86.7–94.9] (133.3 / 100.7) | 1.25 [1.21–1.26] | 1.000 [1.000–1.000] |
| g1 x1 | 57m | 50.2 [48.5–62.7] / 37.2 [36.0–46.5] (43.6 / 32.4) | 105.9 [105.9–108.9] / 78.6 [78.6–80.9] (135.6 / 100.7) | 1.72 [1.64–1.73] | 1.000 [1.000–1.000] |
| g1 x1 | 72f | 77.3 [76.1–85.2] / 58.3 [57.5–64.3] (65.0 / 49.1) | 120.7 [120.7–122.8] / 91.1 [91.1–92.7] (133.3 / 100.7) | 1.49 [1.39–1.50] | 1.000 [1.000–1.000] |
| g1 x1.1 | 57m | 49.6 [47.7–62.4] / 36.8 [35.4–46.3] (43.9 / 32.6) | 102.9 [93.7–105.8] / 76.4 [69.5–78.5] (135.6 / 100.7) | 1.75 [1.66–1.76] | 1.000 [1.000–1.000] |
| g1 x1.1 | 72f | 75.5 [74.2–83.7] / 57.0 [56.0–63.2] (65.2 / 49.3) | 115.0 [107.0–117.1] / 86.9 [80.8–88.4] (133.3 / 100.7) | 1.53 [1.44–1.54] | 1.000 [1.000–1.000] |

Contrafactuales emparejados (intervención − comparador): clases y ΔPAM / Δaporte en cada minuto de comparación.

| punto | caso | contraste | clases | minuto: ΔPAM; Δaporte; ΔQ; Δdéficit |
|---|---|---|---|---|
| g0.25 x1 | 57m | cristaloide | presión y perfusión mejoran: 432 | 120: 26.9 [11.9–32.8]; 0.374 [0.165–0.462]; 0.429 [0.192–0.525]; −0.224 [−0.277–−0.099]; 20: 29.6 [23.2–30.7]; 0.365 [0.300–0.408]; 0.521 [0.407–0.536]; −0.219 [−0.245–−0.180] |
| g0.25 x1 | 57m | 1.ª unidad | presión y perfusión mejoran: 36 | 120: 16.3 [15.9–18.8]; 0.582 [0.559–0.631]; 0.310 [0.303–0.352]; −0.113 [−0.118–−0.109]; 30: 22.7 [21.0–22.8]; 0.676 [0.637–0.684]; 0.463 [0.433–0.465]; −0.405 [−0.410–−0.382] |
| g0.25 x1 | 57m | 2.ª unidad | presión y perfusión mejoran: 36 | 120: 16.6 [16.5–18.9]; 0.591 [0.574–0.636]; 0.317 [0.317–0.355]; −0.118 [−0.122–−0.112]; 60: 16.3 [16.3–18.8]; 0.583 [0.565–0.633]; 0.309 [0.308–0.350]; −0.104 [−0.109–−0.100] |
| g0.25 x1 | 72f | cristaloide | presión y perfusión mejoran: 432 | 120: 19.6 [8.6–24.0]; 0.236 [0.100–0.295]; 0.290 [0.128–0.355]; −0.200 [−0.250–−0.085]; 20: 21.9 [16.8–22.8]; 0.208 [0.172–0.245]; 0.349 [0.270–0.360]; −0.177 [−0.201–−0.146] |
| g0.25 x1 | 72f | 1.ª unidad | presión y perfusión mejoran: 36 | 120: 14.0 [13.7–15.7]; 0.436 [0.418–0.464]; 0.197 [0.192–0.221]; 0.000 [0.000–0.000]; 30: 18.2 [16.7–18.2]; 0.510 [0.477–0.516]; 0.303 [0.279–0.304]; −0.210 [−0.211–−0.194] |
| g0.25 x1 | 72f | 2.ª unidad | presión y perfusión mejoran: 36 | 120: 14.3 [14.3–15.9]; 0.443 [0.428–0.468]; 0.201 [0.201–0.223]; 0.000 [0.000–0.000]; 60: 14.0 [14.0–15.7]; 0.438 [0.423–0.467]; 0.196 [0.196–0.220]; 0.000 [0.000–0.000] |
| g0.25 x1.1 | 57m | cristaloide | presión y perfusión mejoran: 888 | 120: 23.2 [12.0–32.9]; 0.324 [0.157–0.474]; 0.366 [0.191–0.525]; −0.193 [−0.284–−0.094]; 20: 28.7 [21.4–31.0]; 0.358 [0.264–0.430]; 0.497 [0.368–0.535]; −0.214 [−0.258–−0.159] |
| g0.25 x1.1 | 57m | 1.ª unidad | presión y perfusión mejoran: 182 | 120: 14.6 [12.6–17.5]; 0.552 [0.507–0.641]; 0.318 [0.286–0.362]; −0.240 [−0.280–−0.211]; 30: 21.9 [15.8–23.9]; 0.613 [0.538–0.680]; 0.429 [0.317–0.461]; −0.368 [−0.408–−0.323] |
| g0.25 x1.1 | 57m | 2.ª unidad | presión y perfusión mejoran: 182 | 120: 15.0 [12.8–17.6]; 0.567 [0.514–0.647]; 0.326 [0.291–0.365]; −0.244 [−0.285–−0.214]; 60: 14.7 [12.7–17.5]; 0.559 [0.509–0.644]; 0.318 [0.285–0.361]; −0.230 [−0.272–−0.202] |
| g0.25 x1.1 | 72f | cristaloide | presión y perfusión mejoran: 888 | 120: 16.9 [8.6–24.2]; 0.205 [0.091–0.305]; 0.248 [0.127–0.355]; −0.174 [−0.260–−0.077]; 20: 21.2 [15.8–23.1]; 0.205 [0.140–0.266]; 0.334 [0.247–0.360]; −0.174 [−0.226–−0.119] |
| g0.25 x1.1 | 72f | 1.ª unidad | presión y perfusión mejoran: 182 | 120: 13.8 [12.2–15.5]; 0.406 [0.369–0.467]; 0.198 [0.174–0.222]; 0.000 [0.000–0.000]; 30: 15.6 [10.7–17.2]; 0.470 [0.418–0.523]; 0.286 [0.215–0.310]; −0.308 [−0.311–−0.293] |
| g0.25 x1.1 | 72f | 2.ª unidad | presión y perfusión mejoran: 182 | 120: 14.1 [12.4–15.7]; 0.412 [0.376–0.471]; 0.202 [0.176–0.224]; 0.000 [0.000–0.000]; 60: 13.8 [12.2–15.5]; 0.408 [0.372–0.470]; 0.197 [0.175–0.222]; 0.000 [0.000–0.000] |
| g0.5 x1 | 57m | cristaloide | presión y perfusión mejoran: 362 | 120: 25.0 [11.6–32.1]; 0.358 [0.167–0.448]; 0.405 [0.194–0.529]; −0.215 [−0.269–−0.100]; 20: 26.4 [20.9–27.9]; 0.378 [0.313–0.421]; 0.532 [0.420–0.551]; −0.227 [−0.253–−0.188] |
| g0.5 x1 | 57m | 1.ª unidad | presión y perfusión mejoran: 36 | 120: 14.2 [13.8–16.6]; 0.603 [0.579–0.652]; 0.324 [0.316–0.366]; −0.096 [−0.101–−0.091]; 30: 17.5 [16.0–17.7]; 0.714 [0.673–0.723]; 0.497 [0.465–0.499]; −0.428 [−0.434–−0.404] |
| g0.5 x1 | 57m | 2.ª unidad | presión y perfusión mejoran: 36 | 120: 14.5 [14.3–16.7]; 0.613 [0.595–0.659]; 0.332 [0.331–0.370]; −0.101 [−0.106–−0.095]; 60: 14.4 [14.3–16.8]; 0.603 [0.585–0.654]; 0.322 [0.321–0.364]; −0.086 [−0.091–−0.082] |
| g0.5 x1 | 72f | cristaloide | presión y perfusión mejoran: 362 | 120: 17.5 [8.0–22.7]; 0.231 [0.103–0.284]; 0.277 [0.131–0.362]; −0.196 [−0.241–−0.088]; 20: 18.8 [14.3–20.0]; 0.222 [0.184–0.258]; 0.361 [0.282–0.374]; −0.188 [−0.204–−0.157] |
| g0.5 x1 | 72f | 1.ª unidad | presión y perfusión mejoran: 36 | 120: 13.7 [13.4–15.4]; 0.441 [0.423–0.469]; 0.199 [0.194–0.223]; 0.000 [0.000–0.000]; 30: 15.3 [14.0–15.3]; 0.529 [0.494–0.535]; 0.320 [0.295–0.321]; −0.214 [−0.214–−0.196] |
| g0.5 x1 | 72f | 2.ª unidad | presión y perfusión mejoran: 36 | 120: 14.0 [14.0–15.5]; 0.447 [0.432–0.473]; 0.203 [0.203–0.225]; 0.000 [0.000–0.000]; 60: 13.6 [13.6–15.3]; 0.442 [0.427–0.472]; 0.198 [0.198–0.223]; 0.000 [0.000–0.000] |
| g0.5 x1.1 | 57m | cristaloide | presión y perfusión mejoran: 888 | 120: 22.6 [11.7–32.3]; 0.327 [0.158–0.479]; 0.369 [0.193–0.530]; −0.196 [−0.288–−0.095]; 20: 26.2 [19.7–28.6]; 0.371 [0.274–0.448]; 0.512 [0.378–0.553]; −0.223 [−0.269–−0.164] |
| g0.5 x1.1 | 57m | 1.ª unidad | presión y perfusión mejoran: 182 | 120: 11.0 [9.0–14.2]; 0.585 [0.538–0.673]; 0.340 [0.307–0.388]; −0.227 [−0.270–−0.196]; 30: 17.9 [12.5–19.9]; 0.643 [0.562–0.713]; 0.457 [0.338–0.490]; −0.386 [−0.428–−0.337] |
| g0.5 x1.1 | 57m | 2.ª unidad | presión y perfusión mejoran: 182 | 120: 11.3 [9.1–14.2]; 0.598 [0.544–0.679]; 0.349 [0.312–0.391]; −0.232 [−0.275–−0.199]; 60: 11.1 [9.2–14.3]; 0.589 [0.538–0.675]; 0.340 [0.306–0.386]; −0.217 [−0.261–−0.186] |
| g0.5 x1.1 | 72f | cristaloide | presión y perfusión mejoran: 888 | 120: 16.1 [8.1–23.0]; 0.212 [0.093–0.314]; 0.252 [0.129–0.363]; −0.178 [−0.267–−0.079]; 20: 18.6 [14.0–20.8]; 0.217 [0.148–0.283]; 0.350 [0.256–0.378]; −0.184 [−0.241–−0.126] |
| g0.5 x1.1 | 72f | 1.ª unidad | presión y perfusión mejoran: 182 | 120: 13.3 [11.7–15.0]; 0.412 [0.374–0.474]; 0.201 [0.177–0.225]; 0.000 [0.000–0.000]; 30: 12.0 [7.2–13.4]; 0.494 [0.441–0.548]; 0.307 [0.235–0.332]; −0.311 [−0.313–−0.295] |
| g0.5 x1.1 | 72f | 2.ª unidad | presión y perfusión mejoran: 182 | 120: 13.6 [11.9–15.1]; 0.418 [0.382–0.478]; 0.205 [0.179–0.227]; 0.000 [0.000–0.000]; 60: 13.3 [11.8–14.9]; 0.414 [0.378–0.477]; 0.200 [0.177–0.225]; 0.000 [0.000–0.000] |
| g1 x1 | 57m | cristaloide | presión y perfusión mejoran: 268 | 120: 24.3 [11.1–30.9]; 0.356 [0.171–0.456]; 0.407 [0.197–0.537]; −0.213 [−0.274–−0.102]; 20: 22.1 [16.8–23.0]; 0.405 [0.336–0.434]; 0.560 [0.445–0.584]; −0.242 [−0.261–−0.202] |
| g1 x1 | 57m | 1.ª unidad | presión y perfusión mejoran: 36 | 120: 11.9 [11.5–14.2]; 0.629 [0.605–0.680]; 0.340 [0.330–0.384]; −0.063 [−0.068–−0.057]; 30: 7.3 [6.1–7.6]; 0.790 [0.745–0.800]; 0.563 [0.528–0.566]; −0.467 [−0.468–−0.447] |
| g1 x1 | 57m | 2.ª unidad | presión y perfusión mejoran: 36 | 120: 11.9 [11.7–14.1]; 0.641 [0.624–0.687]; 0.349 [0.347–0.389]; −0.069 [−0.074–−0.061]; 60: 12.4 [12.1–14.7]; 0.627 [0.610–0.679]; 0.336 [0.334–0.380]; −0.051 [−0.057–−0.046] |
| g1 x1 | 72f | cristaloide | presión y perfusión mejoran: 268 | 120: 15.9 [6.9–20.3]; 0.236 [0.109–0.298]; 0.285 [0.137–0.375]; −0.199 [−0.253–−0.093]; 20: 13.1 [8.8–13.9]; 0.251 [0.211–0.279]; 0.395 [0.311–0.409]; −0.209 [−0.210–−0.180] |
| g1 x1 | 72f | 1.ª unidad | presión y perfusión mejoran: 36 | 120: 13.0 [12.7–14.6]; 0.449 [0.431–0.478]; 0.202 [0.198–0.227]; 0.000 [0.000–0.000]; 30: 9.7 [8.8–9.8]; 0.565 [0.528–0.571]; 0.352 [0.325–0.353]; −0.221 [−0.222–−0.202] |
| g1 x1 | 72f | 2.ª unidad | presión y perfusión mejoran: 36 | 120: 13.3 [13.3–14.7]; 0.456 [0.440–0.482]; 0.207 [0.207–0.229]; 0.000 [0.000–0.000]; 60: 13.0 [13.0–14.6]; 0.451 [0.436–0.481]; 0.202 [0.202–0.227]; 0.000 [0.000–0.000] |
| g1 x1.1 | 57m | cristaloide | presión y perfusión mejoran: 888 | 120: 21.9 [11.2–31.3]; 0.333 [0.161–0.488]; 0.374 [0.195–0.538]; −0.198 [−0.293–−0.097]; 20: 22.0 [16.8–24.6]; 0.395 [0.290–0.478]; 0.541 [0.395–0.586]; −0.237 [−0.287–−0.174] |
| g1 x1.1 | 57m | 1.ª unidad | presión y perfusión mejoran: 182 | 120: 5.6 [3.4–9.4]; 0.635 [0.583–0.719]; 0.371 [0.337–0.426]; −0.204 [−0.252–−0.168]; 30: 10.4 [6.8–12.8]; 0.698 [0.606–0.774]; 0.507 [0.376–0.544]; −0.419 [−0.465–−0.364] |
| g1 x1.1 | 57m | 2.ª unidad | presión y perfusión mejoran: 182 | 120: 5.7 [3.4–9.3]; 0.645 [0.591–0.726]; 0.383 [0.343–0.429]; −0.209 [−0.257–−0.172]; 60: 5.9 [3.7–9.7]; 0.634 [0.583–0.719]; 0.371 [0.335–0.423]; −0.192 [−0.242–−0.158] |
| g1 x1.1 | 72f | cristaloide | presión y perfusión mejoran: 888 | 120: 14.6 [7.2–21.1]; 0.220 [0.098–0.329]; 0.261 [0.133–0.378]; −0.187 [−0.279–−0.083]; 20: 12.6 [10.2–15.9]; 0.242 [0.164–0.319]; 0.380 [0.275–0.416]; −0.206 [−0.271–−0.139] |
| g1 x1.1 | 72f | 1.ª unidad | presión y perfusión mejoran: 182 | 120: 12.4 [10.9–13.9]; 0.422 [0.384–0.486]; 0.206 [0.181–0.231]; 0.000 [0.000–0.000]; 30: 5.4 [1.0–6.5]; 0.538 [0.482–0.594]; 0.345 [0.271–0.372]; −0.317 [−0.319–−0.299] |
| g1 x1.1 | 72f | 2.ª unidad | presión y perfusión mejoran: 182 | 120: 12.7 [11.1–14.1]; 0.429 [0.392–0.491]; 0.210 [0.184–0.233]; 0.000 [0.000–0.000]; 60: 12.4 [11.0–13.9]; 0.425 [0.388–0.489]; 0.205 [0.182–0.231]; 0.000 [0.000–0.000] |
<!-- /generado:observables -->

## 8. Presión frente a perfusión (generado)

<!-- generado:intercambio -->
Sin tratamiento (P1) a los 120, contra T = 1 en la misma clave; sin umbral (la docencia lo remite a FD-LAC).

| punto | caso | cambio del gasto | cambio del aporte |
|---|---|---|---|
| g0.25 x1 | 57m | −2.1 % [−2.1–−1.5] | −2.1 % [−2.1–−1.5] |
| g0.25 x1 | 72f | −2.2 % [−2.2–−1.5] | −2.2 % [−2.2–−1.5] |
| g0.25 x1.1 | 57m | −1.9 % [−1.9–−1.3] | −1.9 % [−1.9–−1.3] |
| g0.25 x1.1 | 72f | −1.9 % [−2.0–−1.4] | −1.9 % [−2.0–−1.4] |
| g0.5 x1 | 57m | −3.8 % [−3.9–−2.8] | −3.8 % [−3.9–−2.8] |
| g0.5 x1 | 72f | −4.2 % [−4.4–−3.0] | −4.2 % [−4.4–−3.0] |
| g0.5 x1.1 | 57m | −3.4 % [−3.5–−2.4] | −3.4 % [−3.5–−2.4] |
| g0.5 x1.1 | 72f | −3.7 % [−3.8–−2.6] | −3.7 % [−3.8–−2.6] |
| g1 x1 | 57m | −6.5 % [−6.7–−4.8] | −6.5 % [−6.7–−4.8] |
| g1 x1 | 72f | −8.1 % [−8.3–−5.9] | −8.1 % [−8.3–−5.9] |
| g1 x1.1 | 57m | −5.7 % [−5.9–−4.1] | −5.7 % [−5.9–−4.1] |
| g1 x1.1 | 72f | −6.8 % [−7.0–−5.0] | −6.8 % [−7.0–−5.0] |
<!-- /generado:intercambio -->

## 9. FC: diagnóstico (generado)

<!-- generado:fc -->
Diagnóstico, nunca filtro: corridas completas del núcleo (L1, L3 y los dos contrafactuales) con el tono de cada punto, bajo las combinaciones latentes primarias de P2I-2AK; reglas A–F que fallarían, contadas sobre los candidatos supervivientes × combinaciones latentes.

| punto | unidades fisiológicas | filas (candidato × combinación) | A–F que fallan |
|---|---|---|---|
| g0.25 x1 | 18 | 432 | ninguna |
| g0.25 x1.1 | 91 | 9828 | ninguna |
| g0.5 x1 | 18 | 362 | ninguna |
| g0.5 x1.1 | 91 | 9828 | ninguna |
| g1 x1 | 18 | 268 | ninguna |
| g1 x1.1 | 91 | 9828 | ninguna |
<!-- /generado:fc -->

## 10. Conciencia: tiempo bajo los umbrales (generado)

<!-- generado:conciencia -->
Umbrales vigentes de PAS, sin recalibrar: minutos con PAS < 80 y < 65 por trayectoria (mediana [rango]) de los supervivientes primarios.

| punto | caso | P1 <80 | P1 <65 | P2 <80 | P2 <65 | P3 <80 | P4 <80 |
|---|---|---|---|---|---|---|---|
| g0.25 x1 | 57m | 97 [88–97] | 53 [28–55] | 0 [0–24] | 0 [0–0] | 0 [0–0] | 0 [0–0] |
| g0.25 x1 | 72f | 46 [15–48] | 0 [0–0] | 0 [0–0] | 0 [0–0] | 0 [0–0] | 0 [0–0] |
| g0.25 x1.1 | 57m | 96 [87–97] | 47 [24–56] | 0 [0–24] | 0 [0–0] | 0 [0–0] | 0 [0–0] |
| g0.25 x1.1 | 72f | 40 [14–49] | 0 [0–0] | 0 [0–0] | 0 [0–0] | 0 [0–0] | 0 [0–0] |
| g0.5 x1 | 57m | 95 [85–95] | 49 [21–51] | 0 [0–22] | 0 [0–0] | 0 [0–0] | 0 [0–0] |
| g0.5 x1 | 72f | 35 [0–38] | 0 [0–0] | 0 [0–0] | 0 [0–0] | 0 [0–0] | 0 [0–0] |
| g0.5 x1.1 | 57m | 94 [84–95] | 44 [19–52] | 0 [0–23] | 0 [0–0] | 0 [0–0] | 0 [0–0] |
| g0.5 x1.1 | 72f | 32 [3–41] | 0 [0–0] | 0 [0–0] | 0 [0–0] | 0 [0–0] | 0 [0–0] |
| g1 x1 | 57m | 90 [79–91] | 41 [11–44] | 0 [0–17] | 0 [0–0] | 0 [0–0] | 0 [0–0] |
| g1 x1 | 72f | 12 [0–16] | 0 [0–0] | 0 [0–0] | 0 [0–0] | 0 [0–0] | 0 [0–0] |
| g1 x1.1 | 57m | 90 [79–92] | 38 [10–46] | 0 [0–19] | 0 [0–0] | 0 [0–0] | 0 [0–0] |
| g1 x1.1 | 72f | 16 [0–24] | 0 [0–0] | 0 [0–0] | 0 [0–0] | 0 [0–0] | 0 [0–0] |
<!-- /generado:conciencia -->

## 11. Sensibilidad (generado)

<!-- generado:sensibilidad -->
| par de sensibilidad | demanda | entran | sobreviven | primera falla | toda falla | superposiciones | FD-LAC sola | envolventes solas |
|---|---|---|---|---|---|---|---|---|
| g0.25 a0.1 | 1 | 216 | **216** | ninguna | ninguna | ninguna | 216 | 216 |
| g0.25 a0.1 | 1.1 | 1092 | **1092** | ninguna | ninguna | ninguna | 1092 | 1092 |
| g0.25 a0.5 | 1 | 216 | **188** | I · FD-LAC y adecuación L3: 28 | I: 28 | ninguna | 188 | 216 |
| g0.25 a0.5 | 1.1 | 1092 | **1092** | ninguna | ninguna | ninguna | 1092 | 1092 |
| g0.5 a0.1 | 1 | 216 | **216** | ninguna | ninguna | ninguna | 216 | 216 |
| g0.5 a0.1 | 1.1 | 1092 | **1092** | ninguna | ninguna | ninguna | 1092 | 1092 |
| g0.5 a0.5 | 1 | 216 | **140** | I · FD-LAC y adecuación L3: 76 | I: 76 | ninguna | 140 | 216 |
| g0.5 a0.5 | 1.1 | 1092 | **1092** | ninguna | ninguna | ninguna | 1092 | 1092 |
| g1 a0.1 | 1 | 216 | **216** | ninguna | ninguna | ninguna | 216 | 216 |
| g1 a0.1 | 1.1 | 1092 | **1068** | F · manejo definitivo: 24 | F: 24 | ninguna | 1092 | 1068 |
| g1 a0.5 | 1 | 216 | **20** | I · FD-LAC y adecuación L3: 196 | I: 196 | ninguna | 20 | 216 |
| g1 a0.5 | 1.1 | 1092 | **994** | I · FD-LAC y adecuación L3: 98 | I: 98 | ninguna | 994 | 1092 |
| g1.5 a0.3 | 1 | 216 | **18** | G · T_abs en [1, 2]: 168, I · FD-LAC y adecuación L3: 30 | G: 168, I: 177 | G+I: 147 | 39 | 48 |
| g1.5 a0.3 | 1.1 | 1092 | **0** | G · T_abs en [1, 2]: 1092 | F: 468, G: 1092 | F+G: 468 | 1092 | 0 |
| g2 a0.3 | 1 | 216 | **0** | G · T_abs en [1, 2]: 216 | B: 48, F: 216, G: 216, I: 212 | B+F: 48, B+G: 48, B+I: 44, F+G: 216, F+I: 212, G+I: 212 | 4 | 0 |
| g2 a0.3 | 1.1 | 1092 | **0** | G · T_abs en [1, 2]: 1092 | F: 1092, G: 1092, I: 112 | F+G: 1092, F+I: 112, G+I: 112 | 980 | 0 |

Clase por demanda: g0.25 a0.1: robusto en ambas demandas; g0.25 a0.5: robusto en ambas demandas; g0.5 a0.1: robusto en ambas demandas; g0.5 a0.5: robusto en ambas demandas; g1 a0.1: robusto en ambas demandas; g1 a0.5: robusto en ambas demandas; g1.5 a0.3: sólo demanda 1,0; g2 a0.3: incompatible con ambas. Ningún punto de sensibilidad rescata un candidato primario: se evalúan después y aparte.
<!-- /generado:sensibilidad -->

## 12. Identificabilidad (generado)

<!-- generado:identificabilidad -->
| magnitud | clase | detalle |
|---|---|---|
| ganancia de tono | NON_IDENTIFIABLE | {"1": "NON_IDENTIFIABLE", "1.1": "NON_IDENTIFIABLE"} |
| poscarga a | POORLY_IDENTIFIED | {"x1 g0.25": "NON_IDENTIFIABLE", "x1 g0.5": "NON_IDENTIFIABLE", "x1 g1": "NON_IDENTIFIABLE", "x1.1 g0.25": "NON_IDENTIFIABLE", "x1.1 g0.5": "NON_IDENTIFIABLE", "x1.1 g1": "POORLY_IDENTIFIED"} |
| trayectoria de T_abs | NON_IDENTIFIABLE | T_abs = 1 + g s with s the certified signal: it is constrained exactly as far as g is |
| compuesto presión / gasto | POORLY_IDENTIFIED | A, B and F bound MAP and SBP at 120 (faculty envelopes, not observations); output is never observed and enters only through MAP = arrival MAP x Q x T |

Computed on the primary filter, never from the faculty's support decisions: a quantity is WELL_CONSTRAINED only with an authored observation fixing it (none exists after arrival); PARTIALLY_CONSTRAINED when the faculty pressure envelopes alone (A-F, before I) leave one primary gain without survivors at a demand while another keeps some; POORLY_IDENTIFIED when the envelopes remove candidates differently across gains without emptying one; NON_IDENTIFIABLE when they remove the same candidates at every gain. The afterload point reads the same rule across a = 0.1 / 0.3 / 0.5 at the primary gains (sensitivity). The T_abs trajectory follows the gain; the pressure / output composite is bounded at 120 by A, B and F while output is never observed.
<!-- /generado:identificabilidad -->

## 13. Comparadores y validación (generado)

<!-- generado:comparadores -->
Válidos: sí.

| caso | comprobación | resultado |
|---|---|---|
| 57m | C_bag_does_not_reach_L1 | True |
| 57m | C_items_differ_by_crystalloid_only | True |
| 57m | D_E_items_differ_in_the_red_cells_only | True |
| 57m | D_unit_minutes | [True, True] |
| 57m | E_prefix_equal_until_unit_2 | True |
| 57m | E_unit_2_never | True |
| 57m | elapsed_same | True |
| 57m | haemostasis_same | True |
| 57m | unit_minutes | [30, 60] |
| 72f | C_bag_does_not_reach_L1 | True |
| 72f | C_items_differ_by_crystalloid_only | True |
| 72f | D_E_items_differ_in_the_red_cells_only | True |
| 72f | D_unit_minutes | [True, True] |
| 72f | E_prefix_equal_until_unit_2 | True |
| 72f | E_unit_2_never | True |
| 72f | elapsed_same | True |
| 72f | haemostasis_same | True |
| 72f | unit_minutes | [30, 60] |
<!-- /generado:comparadores -->

<!-- generado:validacion -->
Unidades de P2I-2AK reproducidas: sí (1.0: `06f6d5c82fa3…`, 1.1: `515a157e2118…`; 18 y 37 unidades; 216 y 1092 candidatos por punto). Tablas de trayectorias de P2J-2 reproducidas para g = 0, 0,25, 0,5 y 1: sí. Reconstrucción de P4 y de los contrafactuales contra el núcleo: 1962 trayectorias, iguales: sí (2616 corridas completas). Minutos con déficit 0 y T_abs ≠ 1 en el mismo minuto (el retraso aceptado de un paso; H se lee en el minuto siguiente): g 0.25: 506; g 0.5: 532; g 1: 628.
<!-- /generado:validacion -->

## 14. Veredicto y eficiencia (generado)

<!-- generado:veredicto -->
**PRESSURE_TONE_OBSERVABLE_FILTER_SATISFIED**

- los comparadores cambian sólo su intervención: sí
- queda región FD-LAC no vacía: sí
- retroalimentación estable (sin rechazo estructural): sí
- G y H se cumplen en todos los candidatos primarios: sí
- nada aprobado: sí
- presión → FC aplazada (0 en el perfil primario de FC): sí
- sobrevive algún candidato primario: sí
- reconstrucción igual al núcleo (P4 y contrafactuales): sí
- unidades de P2I-2AK y tablas de P2J-2 reproducidas: sí
- Parámetros aprobados: 0.
<!-- /generado:veredicto -->

<!-- generado:eficiencia -->
Trayectorias de sangre en caché: 1326, contrafactuales: 364; grupos de reglas: 1648; puntos (g, a) evaluados: 11; corridas completas del núcleo (FC y validación): 2616; corridas del núcleo que habrían hecho falta sin reconstrucción: 54384; barrido cartesiano: no; presión heredada leída: no.
<!-- /generado:eficiencia -->

## 15. Recomendación: barorreflejo a continuación

Se puede pasar al barorreflejo (presión → FC) llevando como incertidumbre los tres puntos primarios, g = 0,25 / 0,5 / 1
con a = 0,3, todos robustos en ambas demandas. No hace falta otra decisión de presión antes de ese paso:

- En este núcleo la FC no alimenta el gasto ni la presión. La presión es igual con cualquier perfil de FC (P2J-1), así
  que reconectar presión → FC no puede mover la región de presión y tono filtrada aquí.
- Los supervivientes cumplen A–I. I recorta 35 y 82 candidatos a demanda 1,0 con g = 0,5 y 1.
- Lo que sigue sin identificar es la ganancia dentro de [0,25, 1]. Las envolventes por extremos no la distinguen y
  tampoco distinguen la ausencia de respuesta (g = 0). La región la acotan las decisiones de soporte de la docencia
  y FD-LAC, no las envolventes A–H.
- Eso no impide fijar un punto de ajuste y un rango de ganancia del barorreflejo; sólo obliga a llevar las tres
  ganancias.
- El texto congelado `BAROREFLEX_NEXT` pide una región acotada en ambas demandas o una declaración docente. Aquí las
  tres ganancias son robustas en ambas demandas, así que la condición se cumple sin pedir robustez como criterio.

Lo que sí hará falta para el barorreflejo:

- un punto de ajuste de PAM y un rango de ganancia autorizados antes de cualquier valor;
- la comprobación de doble conteo frente al déficit agudo, que también impulsa el tono;
- repetir las reglas A–F de P2I-2AK (recertificación de la FC, que cambia de forma indirecta con el tono).

Si la docencia quisiera identificar la ganancia, haría falta una observación que la distinga. Una envolvente de curso
temporal serviría, por ejemplo la PAM a los 30 o 60 min sin tratamiento. Sería una decisión opcional, no un bloqueo.

## 16. Limitaciones

- **La prueba de humo previa al congelamiento** (dos unidades sintéticas) imprimió un booleano: algún candidato de ese
  subconjunto sobrevivía. No se leyó ningún recuento ni valor de presión, y ninguna envolvente es mía: todas las
  fijó la docencia.
- **La regla de identificabilidad** cuenta como «envolventes» todas las reglas salvo I (también G, H y la
  estructural), y compara recuentos, no conjuntos de candidatos.
  - La clase global elige el caso más favorable: «poscarga POORLY_IDENTIFIED» sale de 1 de 6 puntos.
  - El «compuesto presión / gasto» se asignó a mano (POORLY_IDENTIFIED); con la regla, sin eliminaciones, saldría
    NON_IDENTIFIABLE.
- **Seis de las nueve comprobaciones del veredicto no pueden fallar en la rama READY:**
  - `nothing_approved` y `pressure_to_hr_deferred` son constantes;
  - `upstream_reproduced` lleva `units_equal` literal (el control real es la excepción previa);
  - `fd_lac_region_nonempty` se deduce de que haya supervivientes;
  - `g_h_hold`: G se cumple por construcción para g ≤ 1, y H es exacta por la fórmula del objetivo;
  - `feedback_stable`: el guardia de T es inalcanzable para g ≤ 1.
  - Sólo informan de verdad `primary_survivors`, los comparadores, la reconstrucción y la reproducción de P2J-2.
- **Una corrida detenida o una fila sin pulso** haría caer la evaluación (índice 120) en vez de contarse como
  SIMULATION. No ocurre en el registro.
- **El texto de G** menciona «sondas sintéticas aparte», pero P2J-3 no tiene sondas.
- **La regla del veredicto** dice «trayectorias de los supervivientes»; el código comprueba G y H en todos los
  candidatos primarios, que es más estricto.
- **Cómputo de sobra:** cada pasada de poscarga recalcula g = 0 y su FD-LAC (unas 27 % de las evaluaciones FD-LAC),
  que no se leen. No hay barrido cartesiano.
- **La FC** se lee sobre las unidades fisiológicas de los supervivientes (L1, L3 y contrafactuales). L2 y los
  observables de la FC con cristaloide de P2I-2AK no se repiten.
- **Los minutos de comparación** son la finalización de cada intervención (cristaloide a los 20, unidades a los 30 y
  60) y el 120. Otros minutos no se juzgan.
