# P2I-2V · Anclas docentes aprobadas del estado sanguíneo compartido y filtro de la región candidata

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución ni cambia lo que ve el residente;
- no migra GI ni otra familia;
- no refiltra el lactato (P2I-2R sigue en pausa, PENDIENTE DE REFILTRADO);
- no calibra la presión ni la FC, ni activa el colapso canónico;
- no se ajusta al motor heredado;
- no elige ningún conjunto final de parámetros ocultos.

Código: `clinical_core/blood_constraints.py` (decisiones, lecturas, variantes y filtro; congelado) y
`clinical_core/blood_filter_report.py` (este informe y el diagnóstico de §5.7). Números:
- `docs/revision/P2I2V_blood_sensitivity.json`: antes del congelamiento;
- `docs/revision/P2I2V_blood_filter.json`: el filtro, con `python -m clinical_core.blood_constraints --filter`;
- `docs/revision/P2I2V_blood_diagnostic.json`: el diagnóstico, con
  `python -m clinical_core.blood_filter_report --diagnostic-out`.

El documento se escribe con `python -m clinical_core.blood_filter_report --write … --sensitivity … --filter …
--diagnostic …`.

**Sustituido en parte por P2I-2V-R (2026-10-27).** Este documento es el registro histórico de P2I-2V, tal como
corrió con el congelamiento `cfb8e508…`, y ya no se regenera. Después, la docencia:
- retiró la caída mínima de Hb sin tratar (U-HB v2);
- dejó FD-BLD-03 como cualitativa, sin filtrar;
- pidió implementar V5 y usar como lectura primaria una tasa de sangrado común.

Además, las cuatro sondas de nivel 2 que escribían V directamente pasaron a `HISTORICAL_PROBE`. Fuente:
`docs/revision/P2I2VR_RESTRICCIONES_REVISADAS_FILTRO.md`.

## 1. Decisiones docentes que aplica (2026-10-27)

- **Envolventes sin tratar** (gasto relativo a la llegada de cada caso y caída de Hb): envolventes clínicas de
  calibración, no objetivos heredados. La PAS y la PAM siguen siendo sólo contexto. La caída de Hb es un cambio de
  concentración que sale del estado sanguíneo compartido: no se recrea ninguna deriva directa de Hb por minuto.
- **FD-BLD-01 a FD-BLD-09:** FACULTY_APPROVED. Conducta clínica / envolvente aprobada; los parámetros ocultos del
  modelo siguen sin aprobar.
- **Segunda unidad:** el beneficio hemodinámico de la unidad 2 es ≤ el de la unidad 1 a medida que se agota la
  respuesta a la precarga. La razón estructural ~0,70 no se aprueba como constante fisiológica.
- **FD-23:** sigue RETIRED — INVALIDATED BY SHARED HAEMORRHAGE STATE.
- **Autoridad de la tasa de sangrado:** se aprueba la categoría `CASE_OVERRIDES_FAMILY_DEFAULT`: gana la tasa o
  gravedad verificada del caso; el valor de familia GI aprobado sólo es respaldo; sin ninguno de los dos, la migración
  cierra. Sólo la política: no se aprueba ninguna tasa. Queda declarada en `migration_authority.AUTHORITY_POLICIES`;
  `APPROVED_FAMILY_DEFAULTS` sigue vacío, así que la tasa sigue bloqueando la migración.

## 2. Definiciones operativas (P2I-2V-1)

<!-- generado:definiciones -->
Congelamiento de las decisiones y de su lectura: `cfb8e508fbf3fe9c94b33ec141eee20c56edf188222e2a73a65cc9444486fd26` (`python -m clinical_core.blood_constraints --digest`). Lo fijan las decisiones transcritas, las lecturas, las variantes y todas las fuentes de `clinical_core` salvo este informe.

| Restricción | Envolvente 57m | Envolvente 72f | Lectura operativa |
|---|---|---|---|
| U-OUT: gasto sin tratar (envolventes por caso a 30, 60 y 120 min) | 30′ 0,85–0,95, 60′ 0,70–0,85, 120′ 0,45–0,65 | 30′ 0,90–0,98, 60′ 0,80–0,92, 120′ 0,60–0,78 | Sangrado GI del caso a la tasa del candidato desde el minuto 0, sin tratamiento y con la hemodinámica propia del candidato. Gasto relativo a la llegada en los minutos 30, 60 y 120. Una corrida cuyo gasto llega a 0 con pulso se detiene y lee gasto 0 desde entonces: no cumple la envolvente. |
| U-HB: caída de Hb sin tratar (envolventes por caso a 60 y 120 min) | 60′ 0,2–0,5 g/dL, 120′ 0,4–0,9 g/dL | 60′ 0,1–0,4 g/dL, 120′ 0,3–0,7 g/dL | Caída de Hb = Hb de llegada del caso − Hb a los 60 y 120 min, leída del estado sanguíneo compartido. Ninguna deriva directa de Hb. |
| FD-BLD-01: ΔHb de una unidad de GR | 0,7–1,2 g/dL | 0,7–1,2 g/dL | Sangrado controlado; unidad 1 en 0–30 min. Hb a los 30 min − Hb a los 0, en cada caso. El modelo mezcla al instante: leerla a los 45 o 60 min da lo mismo (sensibilidad). |
| FD-BLD-02: aumento relativo del gasto con una unidad (techo) | ≤ 0,40 (piso 0,15, no exigido) | ≤ 0,30 (piso 0,10, no exigido) | (gasto a los 30 − gasto a los 0) / gasto a los 0 no supera el techo del caso. El piso no se exige (la docencia: no son respuestas obligatorias); V4 lo exige donde el estado responde a la precarga. Todas las posiciones de la cuadrícula están bajo el punto medio euvolémico (0,7); la superior de 72f (0,6) coincide con el límite inferior de esa banda, así que «con llenado bajo» es dudoso en ese punto. |
| FD-BLD-03: una unidad no normaliza el gasto | posición < 0,6 | posición < 0,7 | «Normalizado» = posición de precarga tras una unidad en o sobre la referencia euvolémica del caso (banda 0,6–0,7–0,8). 57m debe quedar bajo su límite inferior (no entra en el rango euvolémico); 72f bajo su punto medio (puede acercarse, no llegar). Una corrida determinista por candidato: «de forma fiable» se lee por candidato. Esa banda es CANDIDATA y era «sólo diagnóstica» (gi_reference): aquí se usa como umbral operativo sin estar aprobada. |
| SECOND-UNIT: beneficio de la 2.ª unidad ≤ el de la 1.ª | Δ2 ≤ Δ1 | Δ2 ≤ Δ1 | Δgasto de la unidad 2 (30 → 60 min) ≤ Δgasto de la unidad 1 (0 → 30 min), en cada caso. |
| FD-BLD-04: efecto circulante inicial de 1 L de cristaloide | 0,15–0,30 | 0,15–0,30 | Sangrado del caso en curso; 1 L en 20 min desde el minuto 0. Contribución inicial = el mayor cristaloide intravascular retenido (entrado − salido) en 0–30 min, sobre el volumen infundido: lo que aporta la bolsa, no el cambio neto de C (eso iba a ser V5, que no quedó implementada). |
| FD-BLD-05: cristaloide retenido a 30, 60 y 120 min | 30′ 0,15–0,25, 60′ 0,10–0,20, 120′ 0,05–0,15 | 30′ 0,15–0,25, 60′ 0,10–0,20, 120′ 0,05–0,15 | Cristaloide intravascular retenido a los 30, 60 y 120 min desde el inicio de la infusión, sobre el volumen infundido (1 L). |
| FD-BLD-06: dilución de Hb con 1 y 2 L, con reversión parcial | 1 L 0,2–0,5 g/dL, 2 L 0,4–0,8 g/dL; 0 < dilución(120′) < pico | 1 L 0,2–0,5 g/dL, 2 L 0,4–0,8 g/dL; 0 < dilución(120′) < pico | Dilución = Hb sin la bolsa − Hb con ella, mismo sangrado. Su pico en 0–120 min dentro de la envolvente de cada volumen (1 y 2 L); reversión parcial: 0 < dilución a los 120 < pico. |
| FD-BLD-07: fracción del déficit agudo repuesta por el relleno | 60′ 0,10–0,25, 120′ 0,20–0,45, 240′ 0,30–0,60 | 60′ 0,10–0,25, 120′ 0,20–0,45, 240′ 0,30–0,60 | Pérdida aguda sintética de 200 mL-eq en 10 min (la superficie de P2I-2U que vio la docencia). Fracción repuesta = relleno acumulado / volumen perdido a los 60, 120 y 240 min. |
| FD-BLD-08: el relleno sigue tras la hemostasia | sigue tras la hemostasia mientras quede déficit y brecha a la meta / capacidad | sigue tras la hemostasia mientras quede déficit y brecha a la meta / capacidad | Sangrado GI del caso detenido por completo a los 60 min. Si a los 60 queda déficit (C < 0) y el relleno está bajo min(capacidad, meta × perdido), el relleno debe ser positivo en cada minuto 61–70 y mayor a los 240 que a los 60; nunca supera la capacidad. La docencia dice «capacidad»; el código mira también la meta. No cambia nada: la condición se aplica en todas las filas. |
| FD-BLD-09: el relleno diluye la Hb y no añade GR | Hb con relleno < sin relleno; ningún GR añadido | Hb con relleno < sin relleno; ningún GR añadido | Pérdida aguda con y sin relleno: donde el relleno es > 0 a los 60, 120 y 240 min, la Hb con relleno es menor; ningún cambio de relleno lleva GR y el contenido de GR nunca sube. |

**Estructura de la región.** Los parámetros del modelo son comunes a los dos casos; la tasa de sangrado y la posición de llegada son de cada caso. La posición es una banda del caso; una tasa propia del caso es admisible con `CASE_OVERRIDES_FAMILY_DEFAULT`, pero hoy ningún caso la declara: V8 exige una tasa común. Se informan también los sobrevivientes de cada caso por separado (todo libre por caso). Ninguna restricción lee ρ: queda en la región y sólo cambia la etiqueta del estado de extracción.

**Lectura de la sangre.** Hb, volumen circulante, relleno y cristaloide no dependen de λ/κ, de la posición ni de ρ. Verificado en los puntos de prueba (Hb, volumen y relleno, cuatro superficies) y, en el filtro, en la Hb a los 60 y 120 min de cada candidato sin tratar que no se detiene. Se leen con λ/κ 1500 y la posición superior del caso, donde ninguna superficie de la cuadrícula se detiene: ningún candidato sale de una restricción de sangre porque su circulación se detuvo; eso lo juzgan las envolventes de gasto. Fuera de la cuadrícula (tasas más altas) esa lectura sí puede detenerse, y el código falla a la vista.

**Plantillas de los contribuyentes.** El sangrado, la bolsa y la unidad se construyen desde las entradas materializadas del camino del motor de familias (`blood_anchors._templates`). Cada campo numérico que actúa se sobrescribe con el valor del candidato; los demás no actúan. `family_engine.py` y `clinical_cases.py` no están en este congelamiento: los fija el de calibración (`scenario_inputs`, `input_path_sources`). Ninguna trayectoria heredada entra en una restricción.

**Variantes declaradas antes del filtro.** Cada una cambia una sola lectura y se informa junto a la primaria, nunca en su lugar.

| Variante | Qué cambia |
|---|---|
| `V1_envelope_tolerance` | cada envolvente numérica, ensanchada un 10 % de su ancho en cada extremo |
| `V2_fd03_both_midpoint` | FD-BLD-03: los dos casos bajo el punto medio euvolémico |
| `V3_fd03_both_lower` | FD-BLD-03: los dos casos bajo el límite inferior euvolémico |
| `V4_fd02_lower_bound_when_responsive` | FD-BLD-02: también el piso, donde un reto de +250 mL-eq a la llegada sube el gasto ≥ 10 % (el reto es una lectura contrafáctica de la curva en V + κ·250, no una trayectoria ni una escritura en el estado) |
| `V5_fd04_net_effect` | FD-BLD-04: efecto neto sobre C (con − sin bolsa) en vez del retenido. **Declarada pero no implementada** en el código congelado: su recuento es el de la lectura primaria |
| `V6_fd06_from_arrival_hb` | FD-BLD-06: dilución = Hb de llegada − Hb con la bolsa |
| `V7_fd07_500_ml` | FD-BLD-07: pérdida aguda de 500 mL-eq en 10 min |
| `V8_common_bleed_rate` | una sola tasa de sangrado para los dos casos (camino del valor de familia) |
| `V9_fd05_from_end_of_infusion` | FD-BLD-05 a los 30, 60 y 120 min desde el fin de la infusión (minutos 50, 80 y 140) |
| `V10_fd07_from_end_of_loss` | FD-BLD-07 a los 60, 120 y 240 min desde el fin de la pérdida (minutos 70, 130 y 250) |

Nota posterior al congelamiento (revisión adversarial): V5 quedó declarada, pero `passes()` no tiene su rama, así que su recuento es el de la lectura primaria. Se informa así; implementarla exigiría recongelar y volver a filtrar.

**Identificabilidad tras el filtro** (regla congelada, a la resolución de la cuadrícula): un solo valor explorado entre los sobrevivientes = WELL_CONSTRAINED; alguno excluido = PARTIALLY_CONSTRAINED; ninguno excluido = POORLY_IDENTIFIED; κ, λ y ρ = NON_IDENTIFIABLE_SEPARATELY (estructural). Sobre los sobrevivientes conjuntos; si no hay, sobre los de cada caso. Ningún valor se elige por su frecuencia.

**Candidatos representativos** (regla congelada): ρ en su referencia; ordenados por el gasto de 57m a los 120 min, luego el de 72f, luego los valores; bajo / medio / alto = el primero, el ⌊n/2⌋-ésimo y el último. Sin sobrevivientes conjuntos, los de cada caso del mismo modo; sin ninguno, no hay representativo.

Texto congelado de cada lectura, tal como lo fija el código (`IMPLEMENTATION`):

- `envelopes`: inclusive, compared on the unrounded model value; nothing is fitted to a midpoint
- `untreated`: the case's GI bleed at the candidate's rate from minute 0, no treatment, the candidate's own haemodynamics; output relative to arrival read at minutes 30, 60 and 120; a run whose output reached zero with a pulse stops there and reads output 0 afterwards, which fails the envelope
- `untreated_hb`: Hb fall = authored arrival Hb - Hb at minutes 60 and 120, read from the shared blood state
- `blood_reading`: every Hb, circulating-volume, refill and crystalloid quantity is read from the shared blood state with lambda / kappa 1500 and the case's upper position, where no surface stops: blood quantities do not depend on lambda / kappa, position or rho (verified on off-grid points, and on every untreated candidate that does not stop)
- `red_cells`: bleeding controlled (no simultaneous loss); unit 1 over minutes 0-30, unit 2 over 30-60 (P2I-2U); unit 1 read at minute 30 (end of its infusion; the model mixes at once), unit 2 at minute 60
- `FD-BLD-01`: Hb at 30 - Hb at 0 inside the envelope, in each case
- `FD-BLD-02`: (output at 30 - output at 0) / output at 0 must not exceed the case's upper bound; the lower bound is not enforced (the faculty: not mandatory; a less preload-responsive state may respond less); every grid position lies in the case band below the euvolaemic reference (underfilled)
- `FD-BLD-03`: normalized = preload position after one unit at or above the case's euvolaemic reference point (reference_preload_fraction band 0.6-0.7-0.8): 57m must stay below its lower bound (no entry into the euvolaemic range), 72f below its midpoint (it may approach, not reach, the euvolaemic reference); one deterministic run per candidate, so 'reliably' is read per candidate
- `second_unit`: output gain of unit 2 (30 to 60) <= output gain of unit 1 (0 to 30), in each case
- `crystalloid`: the case's GI bleed continues at the candidate's rate; the bag runs over 20 min from minute 0 (P2I-2U); compared with the same run without it
- `FD-BLD-04`: early contribution = the largest retained intravascular crystalloid (in - out) over minutes 0-30, over the volume infused (1 L)
- `FD-BLD-05`: retained intravascular crystalloid at minutes 30, 60 and 120 from the start of the infusion, over the volume infused (1 L)
- `FD-BLD-06`: dilution = Hb without the bag - Hb with it, same bleeding; its peak over minutes 0-120 inside the volume's envelope (1 L and 2 L); partial reversal: 0 < dilution at 120 < peak
- `FD-BLD-07`: a synthetic acute loss of 200 mL-eq over 10 min from minute 0 (the P2I-2U surface faculty saw); restored share = cumulative refill / volume shed at minutes 60, 120 and 240
- `FD-BLD-08`: the case's GI bleed stopped completely at minute 60; where at minute 60 a deficit remains (C < 0) and refill is below min(capacity, target share x shed), refill must be positive in every minute 61-70 and larger at 240 than at 60; refill never exceeds the capacity
- `FD-BLD-09`: the acute loss with and without refill: wherever refill > 0 at 60, 120 and 240, Hb with refill < Hb without; no refill change carries red cells; red-cell content never rises
- `joint`: the shared model parameters are common to both cases; the bleed rate and the arrival position are per case (the position is a case band; a case-specific rate is admissible under the approved CASE_OVERRIDES_FAMILY_DEFAULT, but no case declares one today, so V8 requires one common rate)
- `rho`: no constraint reads rho: it stays in the region and only changes the extraction-state label
- `region`: the P2I-2U exploration grid, three values per parameter (blood_anchors.EXPLORATION); feasibility between grid points is not assessed
<!-- /generado:definiciones -->

## 3. Sensibilidad previa al congelamiento (P2I-2V-1)

<!-- generado:sensibilidad -->
Calculada antes del congelamiento, con el código congelado `cfb8e508fbf3fe9c94b33ec141eee20c56edf188222e2a73a65cc9444486fd26`, sólo en dos puntos de prueba fuera de la cuadrícula en todos sus parámetros (P1, P2): ningún candidato de la región se evaluó antes del commit de congelamiento. Muestra cuánto mueve la métrica cada lectura que la docencia no fijó; no dice nada de cuántos candidatos sobreviven.

| Punto | `bleed_ml_per_min` | `arrival_circulating_volume_ml` | `preload_scale_over_kappa_ml` | `preload_fraction` | `plasma_refill_target_share` | `plasma_refill_tau_min` | `plasma_refill_capacity_ml` | `red_cell_unit_hb_g_dl` | `red_cell_unit_volume_ml` | `crystalloid_effective_ml_per_ml` | `crystalloid_leak_tau_min` | `crystalloid_transient_share` | `reserve` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 3 | 4500 | 1000 | 0,4 | 0,6 | 90 | 750 | 21 | 320 | 0,25 | 45 | 0,7 | 2 |
| P2 | 2 | 3500 | 700 | 0,48 | 0,4 | 150 | 300 | 19 | 280 | 0,15 | 20 | 0,5 | 2,75 |

Premisa de la lectura de la sangre: cambiar λ/κ, la posición o ρ mueve la sangre como máximo 0,000000000000 (Hb, volumen circulante, relleno; cuatro superficies, dos puntos, dos casos).

| Lectura | Qué se varió | P1|gi_bleed_57m | P1|gi_bleed_72f | P2|gi_bleed_57m | P2|gi_bleed_72f |
|---|---|---|---|---|---|
| gasto sin tratar | minuto 25 / 30 / 35 | 0,89 / 0,87 / 0,85 | 0,89 / 0,87 / 0,85 | 0,92 / 0,91 / 0,89 | 0,92 / 0,91 / 0,89 |
| gasto sin tratar | minuto 115 / 120 / 125 | 0,56 / 0,55 / 0,53 | 0,56 / 0,55 / 0,53 | 0,64 / 0,62 / 0,60 | 0,64 / 0,62 / 0,60 |
| caída de Hb | minuto 55 / 60 / 65 | 0,037 / 0,044 / 0,051 | 0,036 / 0,042 / 0,048 | 0,014 / 0,016 / 0,019 | 0,013 / 0,016 / 0,018 |
| caída de Hb | minuto 115 / 120 / 125 | 0,137 / 0,147 / 0,158 | 0,131 / 0,141 / 0,151 | 0,055 / 0,059 / 0,063 | 0,052 / 0,056 / 0,061 |
| ΔHb de una unidad (mezcla) | minuto 30 / 45 / 60 | 0,949 / 0,949 / 0,949 | 0,969 / 0,969 / 0,969 | 0,911 / 0,911 / 0,911 | 0,933 / 0,933 / 0,933 |
| aumento del gasto con una unidad | minuto 30 / 60 | 0,411 / 0,411 | 0,411 / 0,411 | 0,357 / 0,357 | 0,357 / 0,357 |
| posición tras una unidad | frente a 0,6 / 0,7 / 0,8 | 0,564 | 0,564 | 0,651 | 0,651 |
| respuesta a la precarga | reto de 100 / 250 / 500 mL-eq | 0,143 / 0,332 / 0,590 | 0,143 / 0,332 / 0,590 | 0,144 / 0,325 / 0,553 | 0,144 / 0,325 / 0,553 |
| FD-BLD-04 | retenido / efecto neto | 0,215 / 0,211 | 0,215 / 0,211 | 0,121 / 0,120 | 0,121 / 0,120 |
| FD-BLD-05 | desde el inicio: 30 / 60 / 120 | 0,187 / 0,132 / 0,090 | 0,187 / 0,132 / 0,090 | 0,103 / 0,081 / 0,075 | 0,103 / 0,081 / 0,075 |
| FD-BLD-05 | desde el fin: 50 / 80 / 140 | 0,147 / 0,112 / 0,085 | 0,147 / 0,112 / 0,085 | 0,085 / 0,077 / 0,075 | 0,085 / 0,077 / 0,075 |
| FD-BLD-06 (1 L) | pico y 120′: contrafáctico / desde la llegada | 0,302, 0,109 / 0,307, 0,256 | 0,288, 0,104 / 0,293, 0,245 | 0,224, 0,133 / 0,226, 0,192 | 0,214, 0,127 / 0,215, 0,183 |
| FD-BLD-06 (2 L) | pico con infusión de 20 / 40 min | 0,582 / 0,506 | 0,556 / 0,484 | 0,434 / 0,381 | 0,415 / 0,364 |
| FD-BLD-07 (200 mL-eq) | 60 / 120 / 240 desde el inicio | 0,272 / 0,432 / 0,556 | 0,272 / 0,432 / 0,556 | 0,122 / 0,214 / 0,316 | 0,122 / 0,214 / 0,316 |
| FD-BLD-07 (200 mL-eq) | 70 / 130 / 250 (desde el fin) | 0,307 / 0,449 / 0,560 | 0,307 / 0,449 / 0,560 | 0,140 / 0,226 / 0,322 | 0,140 / 0,226 / 0,322 |
| FD-BLD-07 (500 mL-eq) | 60 / 120 / 240 | 0,272 / 0,432 / 0,556 | 0,272 / 0,432 / 0,556 | 0,122 / 0,214 / 0,316 | 0,122 / 0,214 / 0,316 |
| FD-BLD-08 | relleno 60 → 240 (mL-eq); sigue en 61–70 | 67; sí | 67; sí | 27; sí | 27; sí |

Lectura de la tabla: el minuto exacto mueve el gasto unos 0,02 por cada 5 min y la caída de Hb menos de 0,01 g/dL; la mezcla no importa (el modelo mezcla al instante). Cambian la métrica de forma material: el reloj de FD-BLD-05 (desde el inicio o desde el fin de la infusión), la línea de base de la reversión en FD-BLD-06, la velocidad de la infusión de 2 L, el reloj de FD-BLD-07 y el umbral de FD-BLD-03. Cada uno tiene su variante declarada antes del filtro (V9, V6, V10, V2/V3), salvo la velocidad de 2 L, que se deja como la de P2I-2U (20 min) y se señala como limitación.
<!-- /generado:sensibilidad -->

## 4. Congelamiento antes del filtro (P2I-2V-1)

Orden seguido:
1. Las definiciones de §2 y las variantes se escribieron sin evaluar ningún candidato de la región.
2. Las pruebas de humo del filtro y la sensibilidad usaron sólo puntos fuera de la cuadrícula en todos sus parámetros.
   El conteo se verificó contra fuerza bruta en una región de humo hecha de esos valores.
3. Las decisiones, las lecturas, las variantes y todas las fuentes de `clinical_core` (salvo el informe) quedaron
   fijadas en un resumen. `test_clinical_core_blood_constraints.py` lo exige, y exige que el filtro informado haya
   corrido con él.
4. Se hizo commit del congelamiento.
5. Sólo entonces corrió el filtro sobre la región.

## 5. Filtro de la región candidata (P2I-2V-2 a P2I-2V-5)

<!-- generado:filtro -->
Filtro corrido con el congelamiento `cfb8e508fbf3fe9c94b33ec141eee20c56edf188222e2a73a65cc9444486fd26`, el mismo que fija la prueba. Región: la cuadrícula de P2I-2U, tres valores por parámetro. Candidatos antes del filtro: 14348907 conjuntos (parámetros comunes, tasa y posición por caso), 4782969 con una tasa común (V8) y 1594323 por caso solo.

### 5.1 Sobrevivientes por restricción

«Sola»: sólo esa restricción. «Todas menos ésta»: el resto, sin ella; muestra qué restricción decide el resultado. Las cifras cuentan candidatos de la cuadrícula, no pacientes.

| Restricción | sola: 57m | sola: 72f | sola: conjunto | todas menos ésta: 57m | todas menos ésta: 72f | todas menos ésta: conjunto |
|---|---|---|---|---|---|---|
| U-OUT: gasto sin tratar (envolventes por caso a 30, 60 y 120 min) | 225261 | 282123 | 441774 | 0 | 0 | 0 |
| U-HB: caída de Hb sin tratar (envolventes por caso a 60 y 120 min) | 0 | 65610 | 0 | 1494 | 3591 | 2241 |
| FD-BLD-01: ΔHb de una unidad de GR | 1062882 | 1003833 | 9034497 | 0 | 0 | 0 |
| FD-BLD-02: aumento relativo del gasto con una unidad (techo) | 649539 | 708588 | 3011499 | 0 | 0 | 0 |
| FD-BLD-03: una unidad no normaliza el gasto | 1062882 | 1240029 | 7794468 | 0 | 0 | 0 |
| SECOND-UNIT: beneficio de la 2.ª unidad ≤ el de la 1.ª | 1594323 | 1594323 | 14348907 | 0 | 0 | 0 |
| FD-BLD-04: efecto circulante inicial de 1 L de cristaloide | 944784 | 944784 | 8503056 | 0 | 0 | 0 |
| FD-BLD-05: cristaloide retenido a 30, 60 y 120 min | 531441 | 531441 | 4782969 | 0 | 0 | 0 |
| FD-BLD-06: dilución de Hb con 1 y 2 L, con reversión parcial | 924372 | 906147 | 7818525 | 0 | 0 | 0 |
| FD-BLD-07: fracción del déficit agudo repuesta por el relleno | 354294 | 354294 | 3188646 | 0 | 192 | 0 |
| FD-BLD-08: el relleno sigue tras la hemostasia | 1594323 | 1594323 | 14348907 | 0 | 0 | 0 |
| FD-BLD-09: el relleno diluye la Hb y no añade GR | 1594323 | 1594323 | 14348907 | 0 | 0 | 0 |
| **Todas** | 0 | 0 | 0 | | | |

### 5.2 Variantes declaradas antes del filtro

| Variante | 57m | 72f | conjunto |
|---|---|---|---|
| primaria | 0 | 0 | 0 |
| `V1_envelope_tolerance`: cada envolvente numérica, ensanchada un 10 % de su ancho en cada extremo | 0 | 0 | 0 |
| `V2_fd03_both_midpoint`: FD-BLD-03: los dos casos bajo el punto medio euvolémico | 0 | 0 | 0 |
| `V3_fd03_both_lower`: FD-BLD-03: los dos casos bajo el límite inferior euvolémico | 0 | 0 | 0 |
| `V4_fd02_lower_bound_when_responsive`: FD-BLD-02: también el piso, donde un reto de +250 mL-eq a la llegada sube el gasto ≥ 10 % (el reto es una lectura contrafáctica de la curva en V + κ·250, no una trayectoria ni una escritura en el estado) | 0 | 0 | 0 |
| `V5_fd04_net_effect`: FD-BLD-04: efecto neto sobre C (con − sin bolsa) en vez del retenido. **Declarada pero no implementada** en el código congelado: su recuento es el de la lectura primaria | 0 | 0 | 0 |
| `V6_fd06_from_arrival_hb`: FD-BLD-06: dilución = Hb de llegada − Hb con la bolsa | 0 | 0 | 0 |
| `V7_fd07_500_ml`: FD-BLD-07: pérdida aguda de 500 mL-eq en 10 min | 0 | 0 | 0 |
| `V8_common_bleed_rate`: una sola tasa de sangrado para los dos casos (camino del valor de familia) | 0 | 0 | 0 |
| `V9_fd05_from_end_of_infusion`: FD-BLD-05 a los 30, 60 y 120 min desde el fin de la infusión (minutos 50, 80 y 140) | 0 | 0 | 0 |
| `V10_fd07_from_end_of_loss`: FD-BLD-07 a los 60, 120 y 240 min desde el fin de la pérdida (minutos 70, 130 y 250) | 0 | 0 | 0 |

V5 no se evaluó: su fila repite la lectura primaria. No puede cambiar el resultado: U-HB sola vacía 57m, y U-HB con FD-BLD-07 vacía 72f; ninguna de las dos lee FD-BLD-04. Quedan evaluadas nueve variantes.

### 5.3 Región candidata restringida por la docencia (FACULTY-CONSTRAINED SHARED-BLOOD CANDIDATE REGION)

No son valores aprobados ni se elige ninguno por su frecuencia: cada celda dice cuántos sobrevivientes tienen ese valor explorado.

**Ningún candidato cumple todas las restricciones, ni en el conjunto ni en ninguno de los dos casos por separado, ni en ninguna de las nueve variantes evaluadas.** La región candidata restringida por la docencia está vacía dentro de la cuadrícula explorada. Qué restricción lo decide: §5.1 y el diagnóstico de §5.7.

### 5.4 Identificabilidad tras el filtro (P2I-2V-4)

Base: los sobrevivientes de cada caso (no hay conjuntos).

No evaluable con la regla congelada: no hay sobrevivientes en ningún caso, así que ningún parámetro queda acotado por la región filtrada (ninguna clase WELL / PARTIALLY / POORLY se puede asignar). Siguen NON_IDENTIFIABLE_SEPARATELY por estructura: κ y λ (sólo λ/κ) y ρ (sólo ρ × la entrega de llegada; ninguna ancla de este paquete la lee). Las nuevas restricciones no rompen la simetría κ/λ: ninguna lee V fuera de V/λ ni la Hb lee κ. El diagnóstico de §5.7 aplica la misma regla, sólo como diagnóstico, al conjunto que cumple todo salvo U-HB.


### 5.5 Candidatos representativos (P2I-2V-5)

No hay sobreviviente del que mostrar trayectorias.

### 5.6 Lo que leen las restricciones, en toda su tabla (contexto)

Mediana (mínimo–máximo) de cada lectura sobre la cuadrícula de su superficie, junto a la envolvente docente. No se ajusta nada a estas cifras.

| Lectura | Envolvente docente | gi_bleed_57m | gi_bleed_72f |
|---|---|---|---|
| gasto sin tratar a 30′ | 0,85–0,95 / 0,90–0,98 | 0,83 (0,00–0,98) | 0,89 (0,35–0,99) |
| gasto sin tratar a 60′ | 0,70–0,85 / 0,80–0,92 | 0,66 (0,00–0,96) | 0,79 (0,00–0,98) |
| gasto sin tratar a 120′ | 0,45–0,65 / 0,60–0,78 | 0,36 (0,00–0,94) | 0,60 (0,00–0,96) |
| corridas sin tratar que se detienen antes de 120′ | — | 2061 de 6561 | 1269 de 6561 |
| caída de Hb sin tratar a 60′ | 0,2–0,5 / 0,1–0,4 | 0,024 (0,003–0,189) | 0,023 (0,003–0,181) |
| caída de Hb sin tratar a 120′ | 0,4–0,9 / 0,3–0,7 | 0,079 (0,011–0,591) | 0,075 (0,010–0,564) |
| ΔHb de una unidad | 0,7–1,2 | 0,91 (0,54–1,60) | 0,93 (0,55–1,63) |
| aumento relativo del gasto con una unidad | techo 0,40 / 0,30 | 0,56 (0,15–1,77) | 0,36 (0,10–1,03) |
| posición tras una unidad | < 0,6 / 0,7 | 0,55 (0,32–0,72) | 0,62 (0,41–0,78) |
| Δgasto 2.ª / 1.ª unidad | ≤ 1 | 0,70 (0,56–0,85) | 0,70 (0,56–0,85) |
| 1 L: contribución inicial | 0,15–0,30 | 0,166 (0,078–0,281) | 0,166 (0,078–0,281) |
| 1 L: retenido a 30′ | 0,15–0,25 | 0,142 (0,052–0,266) | 0,142 (0,052–0,266) |
| 1 L: retenido a 60′ | 0,10–0,20 | 0,103 (0,029–0,232) | 0,103 (0,029–0,232) |
| 1 L: retenido a 120′ | 0,05–0,15 | 0,080 (0,025–0,199) | 0,080 (0,025–0,199) |
| 1 L: dilución pico (g/dL) | 0,2–0,5 | 0,259 (0,097–0,581) | 0,247 (0,092–0,555) |
| 2 L: dilución pico (g/dL) | 0,4–0,8 | 0,504 (0,191–1,070) | 0,481 (0,182–1,022) |
| relleno: fracción repuesta a 60′ | 0,10–0,25 | 0,152 (0,051–0,447) | 0,152 (0,051–0,447) |
| relleno: fracción repuesta a 120′ | 0,20–0,45 | 0,285 (0,095–0,639) | 0,285 (0,095–0,639) |
| relleno: fracción repuesta a 240′ | 0,30–0,60 | 0,429 (0,156–0,735) | 0,429 (0,156–0,735) |
| relleno tras la hemostasia, 60 → 240′ (mL-eq) | > 0 | 34 (9–135) | 34 (9–135) |

### 5.7 Diagnóstico: el conjunto que cumple todo salvo U-HB (NO es un resultado del filtro)

Calculado después del filtro con el mismo congelamiento (`cfb8e508fbf3fe9c94b33ec141eee20c56edf188222e2a73a65cc9444486fd26`) y sólo con funciones congeladas: no cambia ninguna regla ni ninguna lectura. Su conjunto es el «todas menos ésta» de §5.1, que el filtro ya contó; aquí se describe para que la docencia vea qué exige la restricción que vacía la región.

**Mayor caída de Hb sin tratar que alcanza la región** (g/dL):

| Caso | Envolvente docente 60′ / 120′ | Mayor caída en toda la cuadrícula 60′ / 120′ | Mayor caída donde el relleno cumple FD-BLD-07, 60′ / 120′ | Dónde se alcanza (con FD-BLD-07, a los 60′) |
|---|---|---|---|---|
| gi_bleed_57m | 0,2–0,5 / 0,4–0,9 | 0,189 / 0,591 | 0,075 / 0,270 | B0 (mL-eq) 3000; tasa de sangrado (mL-eq/min) 5; capacidad del relleno (mL-eq) 100; meta del relleno (fracción de lo perdido) 0,75; τ del relleno (min) 120 |
| gi_bleed_72f | 0,1–0,4 / 0,3–0,7 | 0,181 / 0,564 | 0,071 / 0,258 | B0 (mL-eq) 3000; tasa de sangrado (mL-eq/min) 5; capacidad del relleno (mL-eq) 100; meta del relleno (fracción de lo perdido) 0,75; τ del relleno (min) 120 |

**El conjunto.** 2241 candidatos conjuntos (gi_bleed_57m: 1494 por caso solo, gi_bleed_72f: 3591 por caso solo). Sobrevivientes por valor:

| Parámetro | Por valor | Clase (regla congelada, sólo diagnóstico) |
|---|---|---|
| tasa de sangrado (mL-eq/min) (gi_bleed_57m) | 1,25: 0 · 2,5: 0 · 5: 2241 | WELL_CONSTRAINED (borde de la cuadrícula: no lo identifica) |
| tasa de sangrado (mL-eq/min) (gi_bleed_72f) | 1,25: 0 · 2,5: 747 · 5: 1494 | PARTIALLY_CONSTRAINED |
| B0 (mL-eq) | 3000: 432 · 4000: 1080 · 5000: 729 | POORLY_IDENTIFIED |
| λ/κ (mL-eq) | 600: 0 · 833: 0 · 1500: 2241 | WELL_CONSTRAINED (borde de la cuadrícula: no lo identifica) |
| posición de precarga de llegada (gi_bleed_57m) | inf.: 0 · medio: 0 · sup.: 2241 | WELL_CONSTRAINED (borde de la cuadrícula: no lo identifica) |
| posición de precarga de llegada (gi_bleed_72f) | inf.: 0 · medio: 747 · sup.: 1494 | PARTIALLY_CONSTRAINED |
| meta del relleno (fracción de lo perdido) | 0,25: 0 · 0,5: 996 · 0,75: 1245 | PARTIALLY_CONSTRAINED |
| τ del relleno (min) | 60: 0 · 120: 1245 · 240: 996 | PARTIALLY_CONSTRAINED |
| capacidad del relleno (mL-eq) | 100: 747 · 500: 747 · 1000: 747 | POORLY_IDENTIFIED |
| contenido de GR de la unidad (Hb, g/dL) | 18: 432 · 20: 783 · 22: 1026 | POORLY_IDENTIFIED |
| volumen de la unidad (mL-eq) | 250: 999 · 300: 1242 · 350: 0 | PARTIALLY_CONSTRAINED |
| fracción retenida del cristaloide | 0,125: 0 · 0,2: 1296 · 0,3: 945 | PARTIALLY_CONSTRAINED |
| τ de redistribución del cristaloide (min) | 15: 216 · 30: 756 · 60: 1269 | POORLY_IDENTIFIED |
| fracción transitoria del cristaloide | 0,4: 648 · 0,6: 837 · 0,8: 756 | POORLY_IDENTIFIED |
| ρ (reserva de extracción) | 1: 747 · 2,5: 747 · 3: 747 | NON_IDENTIFIABLE_SEPARATELY |

**Sus representativos** (la regla congelada de §2 aplicada a este conjunto). Cumplen todas las restricciones salvo U-HB; su caída de Hb sin tratar frente a la envolvente:

| Representativo | gi_bleed_57m: caída 60′ / 120′ (envolvente) | gi_bleed_72f: caída 60′ / 120′ (envolvente) | Restricciones que no cumple |
|---|---|---|---|
| Bajo | 0,065 / 0,138 (0,2–0,5 / 0,4–0,9) | 0,063 / 0,131 (0,1–0,4 / 0,3–0,7) | U-HB (gi_bleed_57m), U-HB (gi_bleed_72f) |
| Medio | 0,035 / 0,136 (0,2–0,5 / 0,4–0,9) | 0,034 / 0,130 (0,1–0,4 / 0,3–0,7) | U-HB (gi_bleed_57m), U-HB (gi_bleed_72f) |
| Alto | 0,044 / 0,156 (0,2–0,5 / 0,4–0,9) | 0,042 / 0,149 (0,1–0,4 / 0,3–0,7) | U-HB (gi_bleed_57m), U-HB (gi_bleed_72f) |

En estas trayectorias el lactato (sólo contexto) baja mientras el déficit crítico crece: con la cinética del punto medio de P2F la depuración domina. No es coherente clínicamente y no se corrige aquí: P2I-2R sigue en pausa.

**Diagnóstico, bajo — gi_bleed_57m.** tasa de sangrado (mL-eq/min) 5; B0 (mL-eq) 3000; λ/κ (mL-eq) 1500; posición de precarga de llegada sup.; meta del relleno (fracción de lo perdido) 0,5; τ del relleno (min) 120; capacidad del relleno (mL-eq) 100; contenido de GR de la unidad (Hb, g/dL) 18; volumen de la unidad (mL-eq) 250; fracción retenida del cristaloide 0,2; τ de redistribución del cristaloide (min) 30; fracción transitoria del cristaloide 0,4; ρ (reserva de extracción) 2,5.

| Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| Hb (g/dL) | 6,70 | 6,68 | 6,63 | 6,56 |
| volumen circulante C (mL-eq) | 0 | -142 | -272 | -544 |
| precarga (posición) | 0,50 | 0,45 | 0,40 | 0,28 |
| gasto relativo | 1,00 | 0,90 | 0,80 | 0,56 |
| DO2 | 0,34 | 0,31 | 0,27 | 0,19 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,24 | 0,33 | 0,53 |
| relleno acumulado (mL-eq) | 0 | 8 | 28 | 56 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,7 | 3,4 |

| GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| Hb (g/dL) | 6,70 | 7,57 | 8,31 |
| volumen circulante C (mL-eq) | 0 | 250 | 500 |
| precarga (posición) | 0,50 | 0,58 | 0,64 |
| gasto relativo | 1,00 | 1,15 | 1,28 |
| DO2 | 0,34 | 0,44 | 0,54 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,6 |

| 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| Hb (g/dL) | 6,70 | 6,32 | 6,35 | 6,37 | 6,32 |
| volumen circulante C (mL-eq) | 0 | 77 | 11 | -145 | -426 |
| precarga (posición) | 0,50 | 0,53 | 0,50 | 0,45 | 0,34 |
| gasto relativo | 1,00 | 1,05 | 1,01 | 0,90 | 0,67 |
| DO2 | 0,34 | 0,34 | 0,32 | 0,29 | 0,22 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,16 | 0,19 | 0,27 | 0,46 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 20 | 52 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,7 | 3,3 |

| 2 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| Hb (g/dL) | 6,70 | 5,98 | 6,04 | 6,14 | 6,11 |
| volumen circulante C (mL-eq) | 0 | 255 | 172 | -26 | -315 |
| precarga (posición) | 0,50 | 0,58 | 0,55 | 0,49 | 0,38 |
| gasto relativo | 1,00 | 1,16 | 1,11 | 0,98 | 0,77 |
| DO2 | 0,34 | 0,35 | 0,34 | 0,31 | 0,24 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,12 | 0,15 | 0,24 | 0,41 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 3 | 41 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,7 | 3,2 |

| Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| Hb (g/dL) | 6,70 | 6,63 | 6,57 | 6,50 |
| volumen circulante C (mL-eq) | 0 | -267 | -239 | -211 |
| precarga (posición) | 0,50 | 0,40 | 0,41 | 0,42 |
| gasto relativo | 1,00 | 0,80 | 0,83 | 0,85 |
| DO2 | 0,34 | 0,27 | 0,28 | 0,28 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,32 | 0,31 | 0,30 |
| relleno acumulado (mL-eq) | 0 | 28 | 56 | 84 |
| lactato (sólo contexto) | 4,4 | 3,7 | 3,4 | 3,0 |

**Diagnóstico, bajo — gi_bleed_72f.** tasa de sangrado (mL-eq/min) 5; B0 (mL-eq) 3000; λ/κ (mL-eq) 1500; posición de precarga de llegada sup.; meta del relleno (fracción de lo perdido) 0,5; τ del relleno (min) 120; capacidad del relleno (mL-eq) 100; contenido de GR de la unidad (Hb, g/dL) 18; volumen de la unidad (mL-eq) 250; fracción retenida del cristaloide 0,2; τ de redistribución del cristaloide (min) 30; fracción transitoria del cristaloide 0,4; ρ (reserva de extracción) 2,5.

| Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| Hb (g/dL) | 6,40 | 6,38 | 6,34 | 6,27 |
| volumen circulante C (mL-eq) | 0 | -142 | -272 | -544 |
| precarga (posición) | 0,60 | 0,56 | 0,52 | 0,43 |
| gasto relativo | 1,00 | 0,93 | 0,87 | 0,71 |
| DO2 | 0,34 | 0,32 | 0,29 | 0,24 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,21 | 0,27 | 0,41 |
| relleno acumulado (mL-eq) | 0 | 8 | 28 | 56 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,1 | 2,9 |

| GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| Hb (g/dL) | 6,40 | 7,29 | 8,06 |
| volumen circulante C (mL-eq) | 0 | 250 | 500 |
| precarga (posición) | 0,60 | 0,66 | 0,71 |
| gasto relativo | 1,00 | 1,10 | 1,19 |
| DO2 | 0,34 | 0,43 | 0,51 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| lactato (sólo contexto) | 3,4 | 3,2 | 3,0 |

| 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| Hb (g/dL) | 6,40 | 6,04 | 6,07 | 6,08 | 6,04 |
| volumen circulante C (mL-eq) | 0 | 77 | 11 | -145 | -426 |
| precarga (posición) | 0,60 | 0,62 | 0,60 | 0,56 | 0,47 |
| gasto relativo | 1,00 | 1,03 | 1,00 | 0,93 | 0,78 |
| DO2 | 0,34 | 0,33 | 0,32 | 0,30 | 0,25 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,17 | 0,19 | 0,25 | 0,37 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 20 | 52 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,9 |

| 2 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| Hb (g/dL) | 6,40 | 5,71 | 5,77 | 5,86 | 5,84 |
| volumen circulante C (mL-eq) | 0 | 255 | 172 | -26 | -315 |
| precarga (posición) | 0,60 | 0,66 | 0,64 | 0,59 | 0,51 |
| gasto relativo | 1,00 | 1,10 | 1,07 | 0,99 | 0,84 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,31 | 0,26 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,16 | 0,18 | 0,23 | 0,35 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 3 | 41 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,9 |

| Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| Hb (g/dL) | 6,40 | 6,34 | 6,27 | 6,21 |
| volumen circulante C (mL-eq) | 0 | -267 | -239 | -211 |
| precarga (posición) | 0,60 | 0,52 | 0,53 | 0,54 |
| gasto relativo | 1,00 | 0,87 | 0,88 | 0,90 |
| DO2 | 0,34 | 0,29 | 0,29 | 0,30 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,27 | 0,26 | 0,26 |
| relleno acumulado (mL-eq) | 0 | 28 | 56 | 84 |
| lactato (sólo contexto) | 3,4 | 3,1 | 2,9 | 2,7 |

**Diagnóstico, medio — gi_bleed_57m.** tasa de sangrado (mL-eq/min) 5; B0 (mL-eq) 5000; λ/κ (mL-eq) 1500; posición de precarga de llegada sup.; meta del relleno (fracción de lo perdido) 0,75; τ del relleno (min) 240; capacidad del relleno (mL-eq) 1000; contenido de GR de la unidad (Hb, g/dL) 20; volumen de la unidad (mL-eq) 300; fracción retenida del cristaloide 0,2; τ de redistribución del cristaloide (min) 60; fracción transitoria del cristaloide 0,6; ρ (reserva de extracción) 2,5.

| Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| Hb (g/dL) | 6,70 | 6,69 | 6,66 | 6,56 |
| volumen circulante C (mL-eq) | 0 | -143 | -274 | -505 |
| precarga (posición) | 0,50 | 0,45 | 0,40 | 0,30 |
| gasto relativo | 1,00 | 0,90 | 0,80 | 0,60 |
| DO2 | 0,34 | 0,31 | 0,27 | 0,20 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,24 | 0,32 | 0,50 |
| relleno acumulado (mL-eq) | 0 | 7 | 26 | 95 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,7 | 3,4 |

| GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| Hb (g/dL) | 6,70 | 7,45 | 8,13 |
| volumen circulante C (mL-eq) | 0 | 300 | 600 |
| precarga (posición) | 0,50 | 0,59 | 0,66 |
| gasto relativo | 1,00 | 1,18 | 1,33 |
| DO2 | 0,34 | 0,45 | 0,55 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,6 |

| 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| Hb (g/dL) | 6,70 | 6,46 | 6,48 | 6,50 | 6,45 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -150 | -411 |
| precarga (posición) | 0,50 | 0,53 | 0,51 | 0,45 | 0,34 |
| gasto relativo | 1,00 | 1,05 | 1,01 | 0,90 | 0,68 |
| DO2 | 0,34 | 0,35 | 0,33 | 0,30 | 0,22 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,14 | 0,17 | 0,26 | 0,44 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 18 | 90 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,7 | 3,3 |

| 2 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| Hb (g/dL) | 6,70 | 6,24 | 6,28 | 6,36 | 6,35 |
| volumen circulante C (mL-eq) | 0 | 262 | 181 | -32 | -323 |
| precarga (posición) | 0,50 | 0,58 | 0,56 | 0,49 | 0,38 |
| gasto relativo | 1,00 | 1,16 | 1,11 | 0,98 | 0,76 |
| DO2 | 0,34 | 0,37 | 0,35 | 0,32 | 0,24 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,08 | 0,11 | 0,21 | 0,39 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 4 | 79 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,6 | 3,2 |

| Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| Hb (g/dL) | 6,70 | 6,66 | 6,60 | 6,52 |
| volumen circulante C (mL-eq) | 0 | -269 | -226 | -166 |
| precarga (posición) | 0,50 | 0,40 | 0,42 | 0,44 |
| gasto relativo | 1,00 | 0,80 | 0,84 | 0,88 |
| DO2 | 0,34 | 0,27 | 0,28 | 0,29 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,32 | 0,30 | 0,27 |
| relleno acumulado (mL-eq) | 0 | 26 | 69 | 129 |
| lactato (sólo contexto) | 4,4 | 3,7 | 3,3 | 3,0 |

**Diagnóstico, medio — gi_bleed_72f.** tasa de sangrado (mL-eq/min) 5; B0 (mL-eq) 5000; λ/κ (mL-eq) 1500; posición de precarga de llegada sup.; meta del relleno (fracción de lo perdido) 0,75; τ del relleno (min) 240; capacidad del relleno (mL-eq) 1000; contenido de GR de la unidad (Hb, g/dL) 20; volumen de la unidad (mL-eq) 300; fracción retenida del cristaloide 0,2; τ de redistribución del cristaloide (min) 60; fracción transitoria del cristaloide 0,6; ρ (reserva de extracción) 2,5.

| Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| Hb (g/dL) | 6,40 | 6,39 | 6,37 | 6,27 |
| volumen circulante C (mL-eq) | 0 | -143 | -274 | -505 |
| precarga (posición) | 0,60 | 0,56 | 0,52 | 0,44 |
| gasto relativo | 1,00 | 0,93 | 0,87 | 0,73 |
| DO2 | 0,34 | 0,32 | 0,29 | 0,24 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,21 | 0,27 | 0,39 |
| relleno acumulado (mL-eq) | 0 | 7 | 26 | 95 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,1 | 2,9 |

| GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| Hb (g/dL) | 6,40 | 7,17 | 7,86 |
| volumen circulante C (mL-eq) | 0 | 300 | 600 |
| precarga (posición) | 0,60 | 0,67 | 0,73 |
| gasto relativo | 1,00 | 1,12 | 1,22 |
| DO2 | 0,34 | 0,43 | 0,51 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| lactato (sólo contexto) | 3,4 | 3,2 | 3,0 |

| 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| Hb (g/dL) | 6,40 | 6,17 | 6,19 | 6,21 | 6,16 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -150 | -411 |
| precarga (posición) | 0,60 | 0,62 | 0,60 | 0,56 | 0,47 |
| gasto relativo | 1,00 | 1,04 | 1,01 | 0,93 | 0,79 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,31 | 0,26 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,15 | 0,17 | 0,23 | 0,35 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 18 | 90 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,9 |

| 2 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| Hb (g/dL) | 6,40 | 5,96 | 6,00 | 6,07 | 6,06 |
| volumen circulante C (mL-eq) | 0 | 262 | 181 | -32 | -323 |
| precarga (posición) | 0,60 | 0,66 | 0,65 | 0,59 | 0,50 |
| gasto relativo | 1,00 | 1,11 | 1,08 | 0,99 | 0,84 |
| DO2 | 0,34 | 0,35 | 0,34 | 0,32 | 0,27 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,12 | 0,14 | 0,20 | 0,32 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 4 | 79 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,8 |

| Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| Hb (g/dL) | 6,40 | 6,37 | 6,31 | 6,23 |
| volumen circulante C (mL-eq) | 0 | -269 | -226 | -166 |
| precarga (posición) | 0,60 | 0,52 | 0,53 | 0,55 |
| gasto relativo | 1,00 | 0,87 | 0,89 | 0,92 |
| DO2 | 0,34 | 0,29 | 0,30 | 0,31 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,27 | 0,25 | 0,24 |
| relleno acumulado (mL-eq) | 0 | 26 | 69 | 129 |
| lactato (sólo contexto) | 3,4 | 3,1 | 2,9 | 2,6 |

**Diagnóstico, alto — gi_bleed_57m.** tasa de sangrado (mL-eq/min) 5; B0 (mL-eq) 5000; λ/κ (mL-eq) 1500; posición de precarga de llegada sup.; meta del relleno (fracción de lo perdido) 0,5; τ del relleno (min) 120; capacidad del relleno (mL-eq) 500; contenido de GR de la unidad (Hb, g/dL) 22; volumen de la unidad (mL-eq) 300; fracción retenida del cristaloide 0,3; τ de redistribución del cristaloide (min) 60; fracción transitoria del cristaloide 0,8; ρ (reserva de extracción) 2,5.

| Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| Hb (g/dL) | 6,70 | 6,69 | 6,66 | 6,54 |
| volumen circulante C (mL-eq) | 0 | -142 | -269 | -490 |
| precarga (posición) | 0,50 | 0,45 | 0,40 | 0,31 |
| gasto relativo | 1,00 | 0,90 | 0,80 | 0,61 |
| DO2 | 0,34 | 0,31 | 0,27 | 0,20 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,24 | 0,32 | 0,49 |
| relleno acumulado (mL-eq) | 0 | 8 | 31 | 110 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,7 | 3,4 |

| GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| Hb (g/dL) | 6,70 | 7,57 | 8,34 |
| volumen circulante C (mL-eq) | 0 | 300 | 600 |
| precarga (posición) | 0,50 | 0,59 | 0,66 |
| gasto relativo | 1,00 | 1,18 | 1,33 |
| DO2 | 0,34 | 0,45 | 0,56 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,6 |

| 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| Hb (g/dL) | 6,70 | 6,36 | 6,40 | 6,46 | 6,44 |
| volumen circulante C (mL-eq) | 0 | 162 | 81 | -118 | -400 |
| precarga (posición) | 0,50 | 0,55 | 0,53 | 0,46 | 0,35 |
| gasto relativo | 1,00 | 1,10 | 1,05 | 0,92 | 0,69 |
| DO2 | 0,34 | 0,36 | 0,34 | 0,30 | 0,23 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,11 | 0,15 | 0,25 | 0,43 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 18 | 102 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,7 | 3,2 |

| 2 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| Hb (g/dL) | 6,70 | 6,06 | 6,13 | 6,29 | 6,35 |
| volumen circulante C (mL-eq) | 0 | 425 | 313 | 28 | -316 |
| precarga (posición) | 0,50 | 0,62 | 0,59 | 0,51 | 0,38 |
| gasto relativo | 1,00 | 1,25 | 1,19 | 1,02 | 0,77 |
| DO2 | 0,34 | 0,38 | 0,37 | 0,33 | 0,25 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,04 | 0,08 | 0,19 | 0,38 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 0 | 87 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,6 | 3,1 |

| Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| Hb (g/dL) | 6,70 | 6,66 | 6,59 | 6,53 |
| volumen circulante C (mL-eq) | 0 | -264 | -218 | -173 |
| precarga (posición) | 0,50 | 0,40 | 0,42 | 0,44 |
| gasto relativo | 1,00 | 0,81 | 0,84 | 0,88 |
| DO2 | 0,34 | 0,27 | 0,28 | 0,29 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,32 | 0,29 | 0,27 |
| relleno acumulado (mL-eq) | 0 | 31 | 77 | 122 |
| lactato (sólo contexto) | 4,4 | 3,7 | 3,3 | 3,0 |

**Diagnóstico, alto — gi_bleed_72f.** tasa de sangrado (mL-eq/min) 5; B0 (mL-eq) 5000; λ/κ (mL-eq) 1500; posición de precarga de llegada sup.; meta del relleno (fracción de lo perdido) 0,5; τ del relleno (min) 120; capacidad del relleno (mL-eq) 500; contenido de GR de la unidad (Hb, g/dL) 22; volumen de la unidad (mL-eq) 300; fracción retenida del cristaloide 0,3; τ de redistribución del cristaloide (min) 60; fracción transitoria del cristaloide 0,8; ρ (reserva de extracción) 2,5.

| Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| Hb (g/dL) | 6,40 | 6,39 | 6,36 | 6,25 |
| volumen circulante C (mL-eq) | 0 | -142 | -269 | -490 |
| precarga (posición) | 0,60 | 0,56 | 0,52 | 0,45 |
| gasto relativo | 1,00 | 0,93 | 0,87 | 0,74 |
| DO2 | 0,34 | 0,32 | 0,29 | 0,25 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,21 | 0,27 | 0,38 |
| relleno acumulado (mL-eq) | 0 | 8 | 31 | 110 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,1 | 2,9 |

| GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| Hb (g/dL) | 6,40 | 7,28 | 8,07 |
| volumen circulante C (mL-eq) | 0 | 300 | 600 |
| precarga (posición) | 0,60 | 0,67 | 0,73 |
| gasto relativo | 1,00 | 1,12 | 1,22 |
| DO2 | 0,34 | 0,43 | 0,52 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| lactato (sólo contexto) | 3,4 | 3,2 | 3,0 |

| 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| Hb (g/dL) | 6,40 | 6,08 | 6,11 | 6,18 | 6,15 |
| volumen circulante C (mL-eq) | 0 | 162 | 81 | -118 | -400 |
| precarga (posición) | 0,60 | 0,64 | 0,62 | 0,57 | 0,48 |
| gasto relativo | 1,00 | 1,07 | 1,04 | 0,95 | 0,80 |
| DO2 | 0,34 | 0,34 | 0,34 | 0,31 | 0,26 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,14 | 0,16 | 0,22 | 0,35 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 18 | 102 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,8 |

| 2 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| Hb (g/dL) | 6,40 | 5,79 | 5,85 | 6,01 | 6,06 |
| volumen circulante C (mL-eq) | 0 | 425 | 313 | 28 | -316 |
| precarga (posición) | 0,60 | 0,70 | 0,68 | 0,61 | 0,51 |
| gasto relativo | 1,00 | 1,16 | 1,13 | 1,01 | 0,84 |
| DO2 | 0,34 | 0,36 | 0,35 | 0,32 | 0,27 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,11 | 0,12 | 0,19 | 0,32 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 0 | 87 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,8 |

| Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| Hb (g/dL) | 6,40 | 6,36 | 6,30 | 6,24 |
| volumen circulante C (mL-eq) | 0 | -264 | -218 | -173 |
| precarga (posición) | 0,60 | 0,52 | 0,54 | 0,55 |
| gasto relativo | 1,00 | 0,87 | 0,90 | 0,92 |
| DO2 | 0,34 | 0,29 | 0,30 | 0,30 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,26 | 0,25 | 0,24 |
| relleno acumulado (mL-eq) | 0 | 31 | 77 | 122 |
| lactato (sólo contexto) | 3,4 | 3,1 | 2,9 | 2,6 |

<!-- /generado:filtro -->

### 5.8 Lectura del resultado

**La región candidata restringida por la docencia está vacía dentro de la cuadrícula explorada.**
- No sobrevive ningún candidato: ni en el conjunto, ni en cada caso por separado, ni en ninguna de las nueve variantes
  evaluadas. Tampoco con las envolventes ensanchadas un 10 % (V1). V5 no quedó implementada (§5.2), pero su recuento
  sería 0 igualmente.
- Lo decide una sola restricción, la caída de Hb sin tratar (U-HB). Sin ella sobreviven 2241 candidatos conjuntos;
  sin cualquier otra, ninguno.
- No se cambió ninguna regla después de ver los recuentos: las lecturas y las variantes son las congeladas en
  `3f86464`.

**Por qué.** En el estado sanguíneo compartido, perder sangre total no cambia la concentración de Hb: sólo el
relleno (y los líquidos) la bajan. Sin tratamiento, Hb / Hb de llegada ≈ (B0 − perdido) / (B0 − perdido + relleno).
Es una aproximación que da una cota superior de la caída: el modelo la integra minuto a minuto y da algo menos.
- Una caída de 0,2 g/dL a los 60 min en 57m (Hb 6,7) exige un relleno de alrededor del 3 % del volumen que queda:
  unos 85 mL-eq con B0 3000 y 300 mL-eq perdidos.
- En toda la cuadrícula, 57m llega como máximo a 0,189 g/dL a los 60 min. Cuando el relleno cumple su propia
  envolvente aprobada (FD-BLD-07), llega a 0,075 a los 60 min y 0,270 a los 120.
- En 72f, la caída aislada sí cabe: 65 610 candidatos por caso solo, todos con 5 mL-eq/min, meta ≥ 0,5 y τ de 60 o
  120 min. Pero con el relleno dentro de FD-BLD-07, 72f llega como máximo a 0,071 g/dL a los 60 min (la envolvente
  pide 0,1–0,4). Sin FD-BLD-07 quedan 192 candidatos de 72f por caso solo.
- **En este modelo y esta región, la envolvente de Hb sin tratar y la de relleno no se cumplen a la vez.**

**57m y 72f no están en la misma situación.** Se comprobó con una exploración de revisión fuera de la cuadrícula,
con la hemodinámica propia de cada punto. No forma parte del filtro ni es una regla:
- En 72f, con tasas de 7,5–10 mL-eq/min y λ/κ 2500, U-HB, U-OUT y FD-BLD-07 se cumplen a la vez (8 combinaciones con
  el relleno de la cuadrícula). El conflicto de 72f se debe al rango explorado.
- En 57m, hasta 10 mL-eq/min, con B0 ≥ 3000 y el relleno dentro de FD-BLD-07, la caída a los 60 min llega como máximo
  a 0,159 g/dL. El conflicto de 57m es estructural: el relleno que permite FD-BLD-07 no baja la Hb lo bastante pronto.

**Lo que muestra el resto.** En el conjunto que cumple todo salvo U-HB (§5.7, diagnóstico), entre los valores
explorados sólo quedan:
- λ/κ 1500;
- en 57m, la posición superior y la tasa de 5 mL-eq/min;
- una unidad de 250–300 mL-eq;
- una retención del cristaloide de 0,2–0,3;
- un relleno con τ de 120–240 min y meta ≥ 0,5.

- λ/κ, la tasa de 57m y la posición de 57m quedan en el borde de lo explorado, así que no se identifican: el valor
  admisible puede estar más allá.
- No es una región aprobada ni candidata: sólo dice qué piden las demás anclas.

**Qué haría falta.** Son decisiones pendientes; ninguna se tomó aquí:
1. Explorar fuera de la cuadrícula:
   - B0 por debajo de 3000 mL-eq. B0 es una normalización, no un volumen medido.
   - Tasas de sangrado por encima de 5 mL-eq/min con el gasto aún dentro de su envolvente; esto bastaría en 72f, no
     en 57m.
   - Si esos valores son clínicamente admisibles lo decide la docencia.
   - Exigiría otra lectura de la sangre, registrada y recongelada: la congelada se detiene con tasas altas en 57m.
2. Cambiar la estructura del relleno, de modo que en un sangrado continuo siga al déficit más deprisa que en la
   pérdida aguda de FD-BLD-07. Es un cambio del modelo, fuera de este paquete.
3. Revisar alguna de las envolventes en conflicto: U-HB a los 60 y 120 min, o FD-BLD-07.

Mientras no se decida, no hay región candidata que validar como paciente (§5.5 vacío) ni identificabilidad
evaluable (§5.4).

## 6. Sondas de nivel 2 de líquidos y fugas que siguen fuera de BloodState (P2I-2V-7)

**Alcance:** las sondas de nivel 2, todas en `clinical_core/bands.py`.

Fuera del nivel 2 siguen otras escrituras directas de V o de Hb. Ya las auditó P2I-2U (§1 de su informe) y ninguna
la lee P2I-2V:
- las reglas congeladas RR1, HR1, HR2 y PL4 (`calibration.py`): V sola. Cambiarlas cambia las reglas congeladas;
- DM1 (`calibration.py`): Hb −30 %, anemia aislada;
- el borde de precarga de P2G §11 (`decision_pack.py`): V sola;
- las sondas históricas de P2I-2Q (`hemodynamic_probes.py`).

Auditoría de `clinical_core/bands.py`. Sólo la sonda de hemorragia pasa por el estado sanguíneo compartido (P2I-2U).
Otras cuatro escriben V directamente, como sonda guionada. Desde P2I-2U, su Hb lleva la marca «†» en la tabla:

| Sonda | Qué escribe | Fisiología que prueba | ¿La gobierna hoy BloodState? | Conversión |
|---|---|---|---|---|
| `vasodilation_with_preload_loss` (sepsis) | V −5 mL/min durante 40 min | tono bajo más «secuestro venoso, fuga» | en parte: la fuga capilar sería plasma que sale (concentraría la Hb), pero BloodState no tiene un proceso de fuga plasmática; el secuestro venoso es un cambio de precarga efectiva, no volumen perdido | no trivial: exige un proceso nuevo en el núcleo o separar la sonda en dos mecanismos |
| `pump_failure_then_bolus` (SCA) | V +500 mL en el minuto 40 | respuesta de una bomba débil a un bolo | sí: el líquido administrado lo gobierna BloodState (`Crystalloid`) | no trivial: hay que elegir el tipo de líquido y su fracción efectiva. 500 mL-eq efectivos equivalen, por FD-BLD-04, a unos 1,7–3,3 L de cristaloide; un cristaloide con parámetros FD-BLD exige elegir parámetros ocultos, y eso no está autorizado |
| `preload_dependent` (IAM del VD / TEP) | V −200 mL en el minuto 1; +250 mL en el 20 | dependencia de la precarga | la pérdida de 200 mL es pérdida de precarga efectiva (no es sangre: no la gobierna BloodState); el bolo de 250 mL sí | no trivial, por la misma elección del tipo de líquido |
| `overload` (edema pulmonar) | V +20 mL/min durante 100 min | congestión con una bomba débil | sí: líquido administrado | no trivial, por la misma elección |

**Decisión: se informan y no se cambian.**
- Convertirlas ampliaría el alcance: haría falta un proceso nuevo en el núcleo, o elegir el tipo y la fracción
  efectiva del líquido, que es un parámetro oculto que este paquete no puede elegir.
- No gobiernan nada aprobado. Ninguna restricción, filtro ni decisión de P2I-2V las lee: el filtro sólo toma de
  `bands.py` el flujo de sangre total `BloodLoss`.
- Siguen activas en el arnés de nivel 2, con bandas TBD y la Hb marcada «†».
- Opciones para decidir:
  - los líquidos administrados, como flujos sin GR a través de BloodState;
  - la fuga capilar, como un proceso nuevo de salida de plasma;
  - el secuestro venoso y la pérdida de precarga del VD, como desplazamientos de precarga efectiva, que no son
    volumen sanguíneo, con esa etiqueta explícita.

## 7. Qué no hace

- No elige ningún conjunto final de parámetros ocultos: la región que queda no es una aprobación.
- No usa lactato, trayectorias heredadas, PAS ni PAM para filtrar.
- No refiltra el lactato (P2I-2R sigue en pausa), no calibra la presión ni la FC, no activa el colapso canónico.
- No migra GI ni otra familia y no integra nada en tiempo de ejecución.
- No puebla ningún valor de familia (`APPROVED_FAMILY_DEFAULTS` sigue vacío).
