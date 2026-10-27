# P2I-2V-R · Restricciones del estado sanguíneo compartido revisadas por la docencia y nuevo filtro

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución, no migra GI ni otra familia, no refiltra el lactato (P2I-2R sigue en pausa);
- no calibra la presión ni la FC, ni activa el colapso;
- no se ajusta al motor heredado y no elige ningún conjunto final de parámetros ocultos;
- no amplía la cuadrícula: el filtro corre sobre la misma cuadrícula de P2I-2U.

Código: `clinical_core/blood_constraints.py` (decisiones, lecturas, variantes y filtro; recongelado) y
`clinical_core/blood_filter_report.py` (sólo este informe). Números: `docs/revision/P2I2VR_blood_sensitivity.json`
(antes del congelamiento) y `docs/revision/P2I2VR_blood_filter.json` (el filtro). P2I-2V queda como registro
histórico (`docs/revision/P2I2V_ANCLAS_APROBADAS_FILTRO.md`, congelamiento `cfb8e508…`).

## 1. Revisiones docentes que aplica (2026-10-27)

- **U-HB: FACULTY_APPROVED v2.**
  - Se retira la caída mínima de Hb sin tratar. La Hb es una concentración: en la hemorragia de sangre total se
    pierden juntos los GR y el plasma.
  - Nuevas envolventes, inclusivas: 57m 0,0–0,5 g/dL a los 60 min y 0,0–0,9 a los 120; 72f 0,0–0,4 y 0,0–0,7.
  - Invariante: con hemorragia en curso y sin fuente de GR, la Hb no sube por la hemorragia misma.
  - No se reintroduce ninguna deriva de Hb por minuto.
- **FD-BLD-07: sin cambios.** El relleno no se debilita para cumplir la Hb.
- **FD-BLD-03: FACULTY_APPROVED_QUALITATIVE / NOT_YET_HARD_FILTER.**
  - La decisión clínica sigue: una unidad no debe normalizar de forma fiable el estado hemodinámico.
  - Las posiciones 0,6 / 0,7 vienen de bandas internas candidatas, no de una definición aprobada de normalización:
    se informan como diagnóstico y no rechazan candidatos.
  - FD-BLD-02 sigue siendo el límite cuantitativo de la respuesta a una unidad.
- **V5 implementada** exactamente como se declaró en P2I-2V: «FD-BLD-04: contribución inicial leída como el efecto
  neto de la bolsa sobre C (con − sin)».
- **Tasa de sangrado en el análisis:**
  - primaria: una tasa candidata común de familia GI para los dos casos;
  - sensibilidad (V8): tasas por caso;
  - la política de producción sigue siendo `CASE_OVERRIDES_FAMILY_DEFAULT`, sin tasa aprobada ni valor de familia.
- **FD-BLD-01, 02, 04, 05, 06, 07, 08 y 09:** sin cambios. **FD-23:** sigue retirada. Los parámetros ocultos siguen
  sin aprobar.

## 2. Definiciones operativas

<!-- generado:definiciones -->
Congelamiento de las decisiones y de su lectura: `a9ab10d8d809070e5e76bcb4557525924dcb918fbd86d9b2a62393687d53c893` (`python -m clinical_core.blood_constraints --digest`). Lo fijan las decisiones transcritas, las lecturas, las variantes y todas las fuentes de `clinical_core` salvo este informe.

| Restricción | Envolvente 57m | Envolvente 72f | Lectura operativa |
|---|---|---|---|
| U-OUT: gasto sin tratar (envolventes por caso a 30, 60 y 120 min) | 30′ 0,85–0,95, 60′ 0,70–0,85, 120′ 0,45–0,65 | 30′ 0,90–0,98, 60′ 0,80–0,92, 120′ 0,60–0,78 | Sangrado GI del caso a la tasa del candidato desde el minuto 0, sin tratamiento y con la hemodinámica propia del candidato. Gasto relativo a la llegada en los minutos 30, 60 y 120. Una corrida cuyo gasto llega a 0 con pulso se detiene y lee gasto 0 desde entonces: no cumple la envolvente. |
| U-HB: caída de Hb sin tratar (envolventes por caso a 60 y 120 min) | 60′ 0,0–0,5 g/dL, 120′ 0,0–0,9 g/dL; la Hb no sube sin tratar | 60′ 0,0–0,4 g/dL, 120′ 0,0–0,7 g/dL; la Hb no sube sin tratar | v2 (P2I-2V-R): caída de Hb = Hb de llegada del caso − Hb a los 60 y 120 min, leída del estado sanguíneo compartido, dentro de [0, techo del caso]: no se exige caída mínima. Además, en la corrida sin tratar (hemorragia en curso, sin fuente de GR ni líquidos) la Hb no sube de un minuto al siguiente en 0–120 min (tolerancia numérica de 1e-9 g/dL). Ninguna deriva directa de Hb. |
| FD-BLD-01: ΔHb de una unidad de GR | 0,7–1,2 g/dL | 0,7–1,2 g/dL | Sangrado controlado; unidad 1 en 0–30 min. Hb a los 30 min − Hb a los 0, en cada caso. El modelo mezcla al instante: leerla a los 45 o 60 min da lo mismo (sensibilidad). |
| FD-BLD-02: aumento relativo del gasto con una unidad (techo) | ≤ 0,40 (piso 0,15, no exigido) | ≤ 0,30 (piso 0,10, no exigido) | (gasto a los 30 − gasto a los 0) / gasto a los 0 no supera el techo del caso. El piso no se exige (la docencia: no son respuestas obligatorias); V4 lo exige donde el estado responde a la precarga. Todas las posiciones de la cuadrícula están bajo el punto medio euvolémico (0,7); la superior de 72f (0,6) coincide con el límite inferior de esa banda, así que «con llenado bajo» es dudoso en ese punto. |
| SECOND-UNIT: beneficio de la 2.ª unidad ≤ el de la 1.ª | Δ2 ≤ Δ1 | Δ2 ≤ Δ1 | Δgasto de la unidad 2 (30 → 60 min) ≤ Δgasto de la unidad 1 (0 → 30 min), en cada caso. |
| FD-BLD-04: efecto circulante inicial de 1 L de cristaloide | 0,15–0,30 | 0,15–0,30 | Sangrado del caso en curso; 1 L en 20 min desde el minuto 0. Contribución inicial = el mayor cristaloide intravascular retenido (entrado − salido) en 0–30 min, sobre el volumen infundido: lo que aporta la bolsa. V5 (implementada en P2I-2V-R tal como se declaró) lee en su lugar el mayor efecto neto sobre C en 0–30 min: C con la bolsa − C sin ella, mismo sangrado, sobre el volumen infundido. |
| FD-BLD-05: cristaloide retenido a 30, 60 y 120 min | 30′ 0,15–0,25, 60′ 0,10–0,20, 120′ 0,05–0,15 | 30′ 0,15–0,25, 60′ 0,10–0,20, 120′ 0,05–0,15 | Cristaloide intravascular retenido a los 30, 60 y 120 min desde el inicio de la infusión, sobre el volumen infundido (1 L). |
| FD-BLD-06: dilución de Hb con 1 y 2 L, con reversión parcial | 1 L 0,2–0,5 g/dL, 2 L 0,4–0,8 g/dL; 0 < dilución(120′) < pico | 1 L 0,2–0,5 g/dL, 2 L 0,4–0,8 g/dL; 0 < dilución(120′) < pico | Dilución = Hb sin la bolsa − Hb con ella, mismo sangrado. Su pico en 0–120 min dentro de la envolvente de cada volumen (1 y 2 L); reversión parcial: 0 < dilución a los 120 < pico. |
| FD-BLD-07: fracción del déficit agudo repuesta por el relleno | 60′ 0,10–0,25, 120′ 0,20–0,45, 240′ 0,30–0,60 | 60′ 0,10–0,25, 120′ 0,20–0,45, 240′ 0,30–0,60 | Pérdida aguda sintética de 200 mL-eq en 10 min (la superficie de P2I-2U que vio la docencia). Fracción repuesta = relleno acumulado / volumen perdido a los 60, 120 y 240 min. |
| FD-BLD-08: el relleno sigue tras la hemostasia | sigue tras la hemostasia mientras quede déficit y brecha a la meta / capacidad | sigue tras la hemostasia mientras quede déficit y brecha a la meta / capacidad | Sangrado GI del caso detenido por completo a los 60 min. Si a los 60 queda déficit (C < 0) y el relleno está bajo min(capacidad, meta × perdido), el relleno debe ser positivo en cada minuto 61–70 y mayor a los 240 que a los 60; nunca supera la capacidad. La docencia dice «capacidad»; el código mira también la meta. No cambia nada: la condición se aplica en todas las filas. |
| FD-BLD-09: el relleno diluye la Hb y no añade GR | Hb con relleno < sin relleno; ningún GR añadido | Hb con relleno < sin relleno; ningún GR añadido | Pérdida aguda con y sin relleno: donde el relleno es > 0 a los 60, 120 y 240 min, la Hb con relleno es menor; ningún cambio de relleno lleva GR y el contenido de GR nunca sube. |
| FD-BLD-03: una unidad no normaliza el gasto | diagnóstico: posición ≥ 0,6 se informa (no filtra) | diagnóstico: posición ≥ 0,7 se informa (no filtra) | **Sólo diagnóstico desde P2I-2V-R: no rechaza ningún candidato.** Se informa cuántos sobrevivientes llegarían a la referencia euvolémica tras una unidad, leída como posición de precarga en o sobre un punto de la banda candidata `reference_preload_fraction` (0,6–0,7–0,8): 57m su límite inferior y 72f su punto medio, y las lecturas V2 (ambos el medio) y V3 (ambos el inferior). Esa banda es CANDIDATA, no una definición aprobada de normalización. |

**Estructura de la región (P2I-2V-R).** La lectura primaria usa una sola tasa de sangrado candidata de familia GI para los dos casos: ningún caso declara una tasa verificada, y las diferencias entre casos no se explican antes de tiempo ajustando tasas separadas. La variante V8 deja que la tasa difiera por caso. Los demás parámetros del modelo son comunes; la posición de llegada es de cada caso (una banda del caso). Se informan también los sobrevivientes de cada caso por separado (todo libre por caso). Ninguna restricción lee ρ: queda en la región y sólo cambia la etiqueta del estado de extracción. La política de autoridad de producción no cambia (`CASE_OVERRIDES_FAMILY_DEFAULT`) y no se puebla ningún valor de familia.

**Lectura de la sangre.** Hb, volumen circulante, relleno y cristaloide no dependen de λ/κ, de la posición ni de ρ. Verificado en los puntos de prueba (Hb, volumen y relleno, cuatro superficies) y, en el filtro, en la Hb a los 60 y 120 min de cada candidato sin tratar que no se detiene. Se leen con λ/κ 1500 y la posición superior del caso, donde ninguna superficie de la cuadrícula se detiene: ningún candidato sale de una restricción de sangre porque su circulación se detuvo; eso lo juzgan las envolventes de gasto. Fuera de la cuadrícula (tasas más altas) esa lectura sí puede detenerse, y el código falla a la vista.

**Plantillas de los contribuyentes.** El sangrado, la bolsa y la unidad se construyen desde las entradas materializadas del camino del motor de familias (`blood_anchors._templates`). Cada campo numérico que actúa se sobrescribe con el valor del candidato; los demás no actúan. `family_engine.py` y `clinical_cases.py` no están en este congelamiento: los fija el de calibración (`scenario_inputs`, `input_path_sources`). Ninguna trayectoria heredada entra en una restricción.

**Variantes declaradas antes del filtro.** Cada una cambia una sola lectura y se informa junto a la primaria, nunca en su lugar.

| Variante | Qué cambia |
|---|---|
| `V1_envelope_tolerance` | cada envolvente numérica, ensanchada un 10 % de su ancho en cada extremo |
| `V2_fd03_both_midpoint` | diagnóstico de FD-BLD-03 con los dos casos bajo el punto medio euvolémico (no filtra) |
| `V3_fd03_both_lower` | diagnóstico de FD-BLD-03 con los dos casos bajo el límite inferior euvolémico (no filtra) |
| `V4_fd02_lower_bound_when_responsive` | FD-BLD-02: también el piso, donde un reto de +250 mL-eq a la llegada sube el gasto ≥ 10 % (el reto es una lectura contrafáctica de la curva en V + κ·250, no una trayectoria ni una escritura en el estado) |
| `V5_fd04_net_effect` | FD-BLD-04: efecto neto sobre C (con − sin bolsa) en vez del retenido (implementada en P2I-2V-R tal como se declaró en P2I-2V) |
| `V6_fd06_from_arrival_hb` | FD-BLD-06: dilución = Hb de llegada − Hb con la bolsa |
| `V7_fd07_500_ml` | FD-BLD-07: pérdida aguda de 500 mL-eq en 10 min |
| `V8_case_specific_bleed_rate` | la tasa de sangrado puede diferir por caso (la lectura primaria de P2I-2V; en P2I-2V-R la primaria es la tasa común) |
| `V9_fd05_from_end_of_infusion` | FD-BLD-05 a los 30, 60 y 120 min desde el fin de la infusión (minutos 50, 80 y 140) |
| `V10_fd07_from_end_of_loss` | FD-BLD-07 a los 60, 120 y 240 min desde el fin de la pérdida (minutos 70, 130 y 250) |

V2 y V3 sólo cambian el diagnóstico de FD-BLD-03, que ya no filtra: su recuento de sobrevivientes es el de la lectura primaria. Con la región vacía, se buscan los conjuntos mínimos de restricciones sin sobreviviente conjunto, hasta 3 restricciones.

**Identificabilidad tras el filtro** (regla congelada, a la resolución de la cuadrícula): un solo valor explorado entre los sobrevivientes = WELL_CONSTRAINED; alguno excluido = PARTIALLY_CONSTRAINED; ninguno excluido = POORLY_IDENTIFIED; κ, λ y ρ = NON_IDENTIFIABLE_SEPARATELY (estructural). Un único valor en el borde de la cuadrícula se marca: lo acota la cuadrícula, no lo identifica. Sobre los sobrevivientes conjuntos; si no hay, sobre los de cada caso. Ningún valor se elige por su frecuencia.

**Candidatos representativos** (regla congelada): ρ en su referencia; ordenados por el gasto de 57m a los 120 min, luego el de 72f, luego los valores; bajo / medio / alto = el primero, el ⌊n/2⌋-ésimo y el último. Sin sobrevivientes conjuntos, los de cada caso del mismo modo; sin ninguno, no hay representativo.

Texto congelado de cada lectura, tal como lo fija el código (`IMPLEMENTATION`):

- `envelopes`: inclusive, compared on the unrounded model value; nothing is fitted to a midpoint
- `untreated`: the case's GI bleed at the candidate's rate from minute 0, no treatment, the candidate's own haemodynamics; output relative to arrival read at minutes 30, 60 and 120; a run whose output reached zero with a pulse stops there and reads output 0 afterwards, which fails the envelope
- `untreated_hb`: U-HB v2: Hb fall = authored arrival Hb - Hb at minutes 60 and 120, read from the shared blood state, inside [0, the case's upper bound]: no minimum decline; and in the untreated run (ongoing haemorrhage, no red-cell source, no fluid) Hb never rises from one minute to the next over minutes 0-120 by more than a numerical 1e-9 g/dL
- `blood_reading`: every Hb, circulating-volume, refill and crystalloid quantity is read from the shared blood state with lambda / kappa 1500 and the case's upper position, where no surface stops: blood quantities do not depend on lambda / kappa, position or rho (verified on off-grid points, and on every untreated candidate that does not stop)
- `red_cells`: bleeding controlled (no simultaneous loss); unit 1 over minutes 0-30, unit 2 over 30-60 (P2I-2U); unit 1 read at minute 30 (end of its infusion; the model mixes at once), unit 2 at minute 60
- `FD-BLD-01`: Hb at 30 - Hb at 0 inside the envelope, in each case
- `FD-BLD-02`: (output at 30 - output at 0) / output at 0 must not exceed the case's upper bound; the lower bound is not enforced (the faculty: not mandatory; a less preload-responsive state may respond less); every grid position lies in the case band below the euvolaemic reference (underfilled)
- `FD-BLD-03`: DIAGNOSTIC ONLY since P2I-2V-R (never filters): how many survivors would reach the case's euvolaemic reference after one unit, read as preload position at or above a point of the candidate reference_preload_fraction band (0.6-0.7-0.8): 57m its lower bound and 72f its midpoint, and the readings V2 (both midpoint) and V3 (both lower)
- `second_unit`: output gain of unit 2 (30 to 60) <= output gain of unit 1 (0 to 30), in each case
- `crystalloid`: the case's GI bleed continues at the candidate's rate; the bag runs over 20 min from minute 0 (P2I-2U); compared with the same run without it
- `FD-BLD-04`: early contribution = the largest retained intravascular crystalloid (in - out) over minutes 0-30, over the volume infused (1 L); V5 reads instead the largest net effect on C over minutes 0-30 (C with the bag - C without it, same bleeding), over the volume infused
- `FD-BLD-05`: retained intravascular crystalloid at minutes 30, 60 and 120 from the start of the infusion, over the volume infused (1 L)
- `FD-BLD-06`: dilution = Hb without the bag - Hb with it, same bleeding; its peak over minutes 0-120 inside the volume's envelope (1 L and 2 L); partial reversal: 0 < dilution at 120 < peak
- `FD-BLD-07`: a synthetic acute loss of 200 mL-eq over 10 min from minute 0 (the P2I-2U surface faculty saw); restored share = cumulative refill / volume shed at minutes 60, 120 and 240
- `FD-BLD-08`: the case's GI bleed stopped completely at minute 60; where at minute 60 a deficit remains (C < 0) and refill is below min(capacity, target share x shed), refill must be positive in every minute 61-70 and larger at 240 than at 60; refill never exceeds the capacity
- `FD-BLD-09`: the acute loss with and without refill: wherever refill > 0 at 60, 120 and 240, Hb with refill < Hb without; no refill change carries red cells; red-cell content never rises
- `joint`: P2I-2V-R primary: every model parameter and the bleed rate are common to both cases (one GI-family candidate rate); the arrival position is per case (a case band). V8 lets the rate differ by case
- `rho`: no constraint reads rho: it stays in the region and only changes the extraction-state label
- `region`: the P2I-2U exploration grid, three values per parameter (blood_anchors.EXPLORATION); feasibility between grid points is not assessed
<!-- /generado:definiciones -->

## 3. Sensibilidad previa al congelamiento

<!-- generado:sensibilidad -->
Calculada antes del congelamiento, con el código congelado `a9ab10d8d809070e5e76bcb4557525924dcb918fbd86d9b2a62393687d53c893`, sólo en dos puntos de prueba fuera de la cuadrícula en todos sus parámetros (P1, P2): ningún candidato de la región se evaluó antes del commit de congelamiento. Muestra cuánto mueve la métrica cada lectura que la docencia no fijó; no dice nada de cuántos candidatos sobreviven.

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
| U-HB v2: mayor subida de Hb sin tratar | minuto a minuto, 0–120 | 0,000000000000 | -0,000000000000 | -0,000000000000 | 0,000000000000 |
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

Lectura de la tabla: el minuto exacto mueve el gasto unos 0,02 por cada 5 min y la caída de Hb menos de 0,01 g/dL; la mezcla no importa (el modelo mezcla al instante). Cambian la métrica de forma material: el reloj de FD-BLD-05 (desde el inicio o desde el fin de la infusión), la línea de base de la reversión en FD-BLD-06, la velocidad de la infusión de 2 L y el reloj de FD-BLD-07. Cada uno tiene su variante declarada antes del filtro (V9, V6, V10), salvo la velocidad de 2 L, que se deja como la de P2I-2U (20 min) y se señala como limitación. El efecto neto (V5) apenas difiere del retenido. La Hb sin tratar no sube en ningún minuto (U-HB v2).
<!-- /generado:sensibilidad -->

## 4. Congelamiento antes del nuevo filtro

Orden seguido:
1. Se aplicaron las revisiones: U-HB v2, FD-BLD-03 como diagnóstico, V5 implementada, tasa común primaria.
2. Las cuatro sondas de nivel 2 que escribían V directamente quedaron como `HISTORICAL_PROBE` (§6).
3. La cuadrícula no cambió.
4. Las pruebas de humo y la sensibilidad usaron sólo puntos fuera de la cuadrícula.
5. Las decisiones, las lecturas, las variantes y todas las fuentes de `clinical_core` (salvo el informe) quedaron
   fijadas en un resumen nuevo, que exige `test_clinical_core_blood_constraints.py`.
6. Se hizo commit del congelamiento.
7. Sólo entonces corrió el filtro.

## 5. Filtro sobre la misma cuadrícula

<!-- generado:filtro -->
Pendiente: el filtro corre después del commit de congelamiento.
<!-- /generado:filtro -->

## 6. Sondas de nivel 2 que escribían V directamente

Ninguna de las cuatro se puede expresar con un mecanismo existente de BloodState sin física nueva, parámetros
ocultos nuevos o supuestos numéricos nuevos. Por eso salieron del arnés activo y quedan sólo como `HISTORICAL_PROBE`
(`bands.HISTORICAL_PROBES`, con su motivo en `bands.HISTORICAL_REASONS`):

| Sonda | Qué escribía | Por qué no se convierte |
|---|---|---|
| `vasodilation_with_preload_loss` (sepsis) | V −5 mL/min durante 40 min | el secuestro venoso es un cambio de precarga efectiva, no volumen perdido, y BloodState no tiene fuga plasmática: haría falta física nueva |
| `pump_failure_then_bolus` (SCA) | V +500 mL en el minuto 40 | el líquido administrado lo gobierna `Crystalloid`, pero sólo con fracción efectiva, τ y fracción transitoria: elegirlos es un supuesto numérico nuevo, y mantener 500 mL-eq plenamente efectivos contradiría FD-BLD-04 y 05 |
| `preload_dependent` (IAM del VD / TEP) | V −200 mL en el minuto 1; +250 mL en el 20 | la «pérdida» es pérdida de precarga del VD, no sangre (física nueva); el bolo necesita las mismas elecciones de cristaloide |
| `overload` (edema pulmonar) | V +20 mL/min durante 100 min | líquido administrado: las mismas elecciones de cristaloide |

- Siguen ejecutables como registro (`bands.probe`), pero ninguna está en `bands.PROBES`, ni tiene banda, ni aparece en
  la tabla del informe del arnés.
- Ninguna sonda activa escribe V ni Hb fuera de BloodState; una prueba lo exige.
- Cambia el componente `harness_sources` del congelamiento de calibración (sólo `bands.py`), con el motivo registrado.

## 7. Qué no hace

- No elige ningún conjunto final de parámetros ocultos: la región que quede no es una aprobación.
- No usa lactato, trayectorias heredadas, PAS ni PAM para filtrar, ni la posición de precarga (FD-BLD-03 no filtra).
- No amplía, no densifica ni cambia la cuadrícula.
- No migra, no integra y no puebla ningún valor de familia.
