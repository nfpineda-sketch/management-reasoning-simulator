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

**Ampliado por P2I-2W (2026-10-27).** P2I-2V-R quedó aceptado y cerrado. Este documento es su registro, tal como
corrió con el congelamiento `a9ab10d8…`, y ya no se regenera. P2I-2W extiende los bordes abiertos de la cuadrícula
con las mismas restricciones: `docs/revision/P2I2W_EXTENSION_BORDES_AUDITORIA.md`.

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

Lectura de la tabla: el minuto exacto mueve el gasto unos 0,02 por cada 5 min y la caída de Hb menos de 0,01 g/dL; la mezcla no importa (el modelo mezcla al instante). Cambian la métrica de forma material: el reloj de FD-BLD-05 (desde el inicio o desde el fin de la infusión), la línea de base de la reversión en FD-BLD-06, la velocidad de la infusión de 2 L y el reloj de FD-BLD-07. Cada uno tiene su variante declarada antes del filtro (V9, V6, V10), salvo la velocidad de 2 L, que se deja como la de P2I-2U (20 min) y se señala como limitación. En los puntos de prueba, el efecto neto (V5) difiere del retenido en menos de 0,01. La Hb sin tratar no sube en ningún minuto (U-HB v2).
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
Filtro corrido con el congelamiento `a9ab10d8d809070e5e76bcb4557525924dcb918fbd86d9b2a62393687d53c893`, el mismo que fija la prueba. Región: la cuadrícula de P2I-2U, sin cambios (tres valores por parámetro). Lectura primaria: una tasa de sangrado común. Candidatos antes del filtro: 4782969 conjuntos con tasa común (primaria), 14348907 con tasa por caso (V8) y 1594323 por caso solo.

### 5.1 Sobrevivientes por restricción

«Sola»: sólo esa restricción. «Todas menos ésta»: el resto, sin ella. Conjunto = los dos casos con la tasa común. Las cifras cuentan candidatos de la cuadrícula, no pacientes.

| Restricción | sola: 57m | sola: 72f | sola: conjunto | todas menos ésta: 57m | todas menos ésta: 72f | todas menos ésta: conjunto |
|---|---|---|---|---|---|---|
| U-OUT: gasto sin tratar (envolventes por caso a 30, 60 y 120 min) | 225261 | 282123 | 205578 | 25542 | 28728 | 38502 |
| U-HB: caída de Hb sin tratar (envolventes por caso a 60 y 120 min) | 1594323 | 1594323 | 4782969 | 5004 | 8379 | 4896 |
| FD-BLD-01: ΔHb de una unidad de GR | 1062882 | 1003833 | 3011499 | 7371 | 12474 | 7371 |
| FD-BLD-02: aumento relativo del gasto con una unidad (techo) | 649539 | 708588 | 1003833 | 8970 | 11172 | 7938 |
| SECOND-UNIT: beneficio de la 2.ª unidad ≤ el de la 1.ª | 1594323 | 1594323 | 4782969 | 5004 | 8379 | 4896 |
| FD-BLD-04: efecto circulante inicial de 1 L de cristaloide | 944784 | 944784 | 2834352 | 5004 | 8379 | 4896 |
| FD-BLD-05: cristaloide retenido a 30, 60 y 120 min | 531441 | 531441 | 1594323 | 8802 | 13986 | 8154 |
| FD-BLD-06: dilución de Hb con 1 y 2 L, con reversión parcial | 924372 | 906147 | 2606904 | 6318 | 9639 | 6075 |
| FD-BLD-07: fracción del déficit agudo repuesta por el relleno | 354294 | 354294 | 1062882 | 22167 | 33564 | 21603 |
| FD-BLD-08: el relleno sigue tras la hemostasia | 1594323 | 1594323 | 4782969 | 5004 | 8379 | 4896 |
| FD-BLD-09: el relleno diluye la Hb y no añade GR | 1594323 | 1594323 | 4782969 | 5004 | 8379 | 4896 |
| **Todas (las que filtran)** | 5004 | 8379 | 4896 | | | |

FD-BLD-03 no filtra (FACULTY_APPROVED_QUALITATIVE / NOT_YET_HARD_FILTER); su diagnóstico está en §5.3.

### 5.2 Lectura primaria y variantes declaradas antes del filtro

| Lectura | 57m | 72f | conjunto |
|---|---|---|---|
| **primaria: tasa común** | 5004 | 8379 | 4896 |
| `V1_envelope_tolerance`: cada envolvente numérica, ensanchada un 10 % de su ancho en cada extremo | 20367 | 25425 | 19443 |
| `V2_fd03_both_midpoint`: diagnóstico de FD-BLD-03 con los dos casos bajo el punto medio euvolémico (no filtra) — sólo cambia el diagnóstico de FD-BLD-03 | 5004 | 8379 | 4896 |
| `V3_fd03_both_lower`: diagnóstico de FD-BLD-03 con los dos casos bajo el límite inferior euvolémico (no filtra) — sólo cambia el diagnóstico de FD-BLD-03 | 5004 | 8379 | 4896 |
| `V4_fd02_lower_bound_when_responsive`: FD-BLD-02: también el piso, donde un reto de +250 mL-eq a la llegada sube el gasto ≥ 10 % (el reto es una lectura contrafáctica de la curva en V + κ·250, no una trayectoria ni una escritura en el estado) | 5004 | 8379 | 4896 |
| `V5_fd04_net_effect`: FD-BLD-04: efecto neto sobre C (con − sin bolsa) en vez del retenido (implementada en P2I-2V-R tal como se declaró en P2I-2V) | 5004 | 8379 | 4896 |
| `V6_fd06_from_arrival_hb`: FD-BLD-06: dilución = Hb de llegada − Hb con la bolsa | 4248 | 7665 | 4182 |
| `V7_fd07_500_ml`: FD-BLD-07: pérdida aguda de 500 mL-eq en 10 min | 3336 | 5586 | 3264 |
| `V8_case_specific_bleed_rate`: la tasa de sangrado puede diferir por caso (la lectura primaria de P2I-2V; en P2I-2V-R la primaria es la tasa común) | 5004 | 8379 | 6030 |
| `V9_fd05_from_end_of_infusion`: FD-BLD-05 a los 30, 60 y 120 min desde el fin de la infusión (minutos 50, 80 y 140) | 1908 | 3528 | 1881 |
| `V10_fd07_from_end_of_loss`: FD-BLD-07 a los 60, 120 y 240 min desde el fin de la pérdida (minutos 70, 130 y 250) | 9684 | 14763 | 9432 |

### 5.3 FD-BLD-03, sólo diagnóstico

Cuántos sobrevivientes no llegarían a la referencia euvolémica tras una unidad, con cada lectura (la diferencia con el total son los que sí llegarían). Nadie se rechaza por esto.

| Lectura de «normalizado» | 57m | 72f | conjunto |
|---|---|---|---|
| ambos ≥ 0,7 | 5004 | 3591 | 2268 |
| ambos ≥ 0,6 | 1494 | 1197 | 0 |
| 57m ≥ 0,6, 72f ≥ 0,7 | 1494 | 3591 | 1494 |
| de un total de | 5004 | 8379 | 4896 |

En el conjunto, un candidato «llega» si llega en al menos uno de los dos casos. La lectura «ambos ≥ 0,6» es degenerada en 72f: su posición de llegada superior (0,6) ya está en ese límite antes de la unidad.

### 5.4 Región candidata restringida por la docencia (FACULTY-CONSTRAINED SHARED-BLOOD CANDIDATE REGION)

No son valores aprobados ni se elige ninguno por su frecuencia: cada celda dice cuántos sobrevivientes conjuntos (tasa común) tienen ese valor explorado.

| Parámetro | Sobrevivientes por valor | Rango que sobrevive |
|---|---|---|
| tasa de sangrado común (mL-eq/min) | 1,25: 0 · 2,5: 2628 · 5: 2268 | 2,5 – 5 |
| posición de precarga de llegada (gi_bleed_57m) | inf.: 0 · medio: 0 · sup.: 4896 | sup. |
| posición de precarga de llegada (gi_bleed_72f) | inf.: 0 · medio: 0 · sup.: 4896 | sup. |
| B0 (mL-eq) | 3000: 720 · 4000: 2232 · 5000: 1944 | 3000 – 5000 |
| λ/κ (mL-eq) | 600: 1494 · 833: 1134 · 1500: 2268 | 600 – 1500 |
| meta del relleno (fracción de lo perdido) | 0,25: 0 · 0,5: 2259 · 0,75: 2637 | 0,5 – 0,75 |
| τ del relleno (min) | 60: 0 · 120: 2886 · 240: 2010 | 120 – 240 |
| capacidad del relleno (mL-eq) | 100: 1632 · 500: 1632 · 1000: 1632 | 100 – 1000 |
| contenido de GR de la unidad (Hb, g/dL) | 18: 1179 · 20: 1764 · 22: 1953 | 18 – 22 |
| volumen de la unidad (mL-eq) | 250: 1665 · 300: 2070 · 350: 1161 | 250 – 350 |
| fracción retenida del cristaloide | 0,125: 0 · 0,2: 2700 · 0,3: 2196 | 0,2 – 0,3 |
| τ de redistribución del cristaloide (min) | 15: 495 · 30: 1665 · 60: 2736 | 15 – 60 |
| fracción transitoria del cristaloide | 0,4: 1350 · 0,6: 1881 · 0,8: 1665 | 0,4 – 0,8 |
| ρ (reserva de extracción) | 1: 1632 · 2,5: 1632 · 3: 1632 | 1 – 3 |

### 5.5 Identificabilidad tras el filtro

Base: los sobrevivientes conjuntos con la tasa común. A la resolución de la cuadrícula.

| Parámetro | Clase | Valores que quedan |
|---|---|---|
| tasa de sangrado común (mL-eq/min) | PARTIALLY_CONSTRAINED (abierto en el borde de la cuadrícula: ese lado lo acota la cuadrícula, no las restricciones) | 2,5, 5 |
| posición de precarga de llegada (gi_bleed_57m) | WELL_CONSTRAINED (borde de la cuadrícula: la acota, no la identifica) | sup. |
| posición de precarga de llegada (gi_bleed_72f) | WELL_CONSTRAINED (borde de la cuadrícula: la acota, no la identifica) | sup. |
| B0 (mL-eq) | POORLY_IDENTIFIED | 3000, 4000, 5000 |
| λ/κ (mL-eq) | POORLY_IDENTIFIED | 600, 833, 1500 |
| meta del relleno (fracción de lo perdido) | PARTIALLY_CONSTRAINED (abierto en el borde de la cuadrícula: ese lado lo acota la cuadrícula, no las restricciones) | 0,5, 0,75 |
| τ del relleno (min) | PARTIALLY_CONSTRAINED (abierto en el borde de la cuadrícula: ese lado lo acota la cuadrícula, no las restricciones) | 120, 240 |
| capacidad del relleno (mL-eq) | POORLY_IDENTIFIED | 100, 500, 1000 |
| contenido de GR de la unidad (Hb, g/dL) | POORLY_IDENTIFIED | 18, 20, 22 |
| volumen de la unidad (mL-eq) | POORLY_IDENTIFIED | 250, 300, 350 |
| fracción retenida del cristaloide | PARTIALLY_CONSTRAINED (abierto en el borde de la cuadrícula: ese lado lo acota la cuadrícula, no las restricciones) | 0,2, 0,3 |
| τ de redistribución del cristaloide (min) | POORLY_IDENTIFIED | 15, 30, 60 |
| fracción transitoria del cristaloide | POORLY_IDENTIFIED | 0,4, 0,6, 0,8 |
| ρ (reserva de extracción) | NON_IDENTIFIABLE_SEPARATELY | 1, 2,5, 3; only rho x the arrival delivery ratio reaches D and the deficit; no constraint reads it |
| λ (por separado) | NON_IDENTIFIABLE_SEPARATELY | only lambda / kappa reaches any anchor |
| κ (por separado) | NON_IDENTIFIABLE_SEPARATELY | only lambda / kappa reaches any anchor; Hb never reads kappa |

### 5.6 Candidatos representativos

Regla congelada: ρ en su referencia; ordenados por el gasto de 57m a los 120 min, luego el de 72f, luego los valores; bajo / medio / alto = el primero, el ⌊n/2⌋-ésimo y el último. La PAS y el lactato son sólo contexto. No son una selección: son tres puntos de la región.

**Bajo — gi_bleed_57m.** tasa de sangrado (mL-eq/min) 2,5; B0 (mL-eq) 3000; λ/κ (mL-eq) 600; posición de precarga de llegada sup.; meta del relleno (fracción de lo perdido) 0,5; τ del relleno (min) 120; capacidad del relleno (mL-eq) 100; contenido de GR de la unidad (Hb, g/dL) 18; volumen de la unidad (mL-eq) 250; fracción retenida del cristaloide 0,2; τ de redistribución del cristaloide (min) 30; fracción transitoria del cristaloide 0,4; ρ (reserva de extracción) 2,5.

| Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,025 | -0,050 | -0,099 |
| Hb (g/dL) | 6,70 | 6,69 | 6,66 | 6,59 |
| volumen circulante C (mL-eq) | 0 | -71 | -134 | -253 |
| precarga (posición) | 0,50 | 0,44 | 0,37 | 0,24 |
| gasto relativo | 1,00 | 0,87 | 0,75 | 0,48 |
| DO2 | 0,34 | 0,30 | 0,25 | 0,16 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,26 | 0,37 | 0,60 |
| relleno acumulado (mL-eq) | 0 | 4 | 16 | 47 |
| PAS (sólo contexto) | 88 | 82 | 77 | 62 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,8 | 3,5 |

| GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | 0,224 | 0,448 |
| Hb (g/dL) | 6,70 | 7,57 | 8,31 |
| volumen circulante C (mL-eq) | 0 | 250 | 500 |
| precarga (posición) | 0,50 | 0,67 | 0,78 |
| gasto relativo | 1,00 | 1,34 | 1,57 |
| DO2 | 0,34 | 0,51 | 0,66 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| PAS (sólo contexto) | 88 | 103 | 113 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,6 |

| 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,016 | -0,024 | -0,048 | -0,096 |
| Hb (g/dL) | 6,70 | 6,32 | 6,36 | 6,41 | 6,35 |
| volumen circulante C (mL-eq) | 0 | 127 | 86 | -13 | -139 |
| precarga (posición) | 0,50 | 0,60 | 0,57 | 0,49 | 0,37 |
| gasto relativo | 1,00 | 1,19 | 1,13 | 0,98 | 0,74 |
| DO2 | 0,34 | 0,38 | 0,37 | 0,32 | 0,24 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,04 | 0,09 | 0,20 | 0,40 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 2 | 39 |
| PAS (sólo contexto) | 88 | 97 | 94 | 87 | 76 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,6 | 3,1 |

| 2 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,016 | -0,023 | -0,046 | -0,092 |
| Hb (g/dL) | 6,70 | 5,99 | 6,05 | 6,15 | 6,17 |
| volumen circulante C (mL-eq) | 0 | 305 | 247 | 120 | -41 |
| precarga (posición) | 0,50 | 0,70 | 0,67 | 0,59 | 0,47 |
| gasto relativo | 1,00 | 1,40 | 1,34 | 1,18 | 0,93 |
| DO2 | 0,34 | 0,42 | 0,41 | 0,37 | 0,29 |
| estado de extracción | crítica | compensada | compensada | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 | 0,08 | 0,27 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 0 | 15 |
| PAS (sólo contexto) | 88 | 106 | 103 | 96 | 85 |
| lactato (sólo contexto) | 4,4 | 4,1 | 4,0 | 3,6 | 2,9 |

| Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,049 | -0,049 | -0,049 |
| Hb (g/dL) | 6,70 | 6,66 | 6,61 | 6,56 |
| volumen circulante C (mL-eq) | 0 | -132 | -109 | -87 |
| precarga (posición) | 0,50 | 0,38 | 0,40 | 0,42 |
| gasto relativo | 1,00 | 0,75 | 0,80 | 0,84 |
| DO2 | 0,34 | 0,26 | 0,27 | 0,28 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,36 | 0,33 | 0,30 |
| relleno acumulado (mL-eq) | 0 | 16 | 39 | 61 |
| PAS (sólo contexto) | 88 | 77 | 79 | 81 |
| lactato (sólo contexto) | 4,4 | 3,8 | 3,4 | 3,1 |

**Bajo — gi_bleed_72f.** tasa de sangrado (mL-eq/min) 2,5; B0 (mL-eq) 3000; λ/κ (mL-eq) 600; posición de precarga de llegada sup.; meta del relleno (fracción de lo perdido) 0,5; τ del relleno (min) 120; capacidad del relleno (mL-eq) 100; contenido de GR de la unidad (Hb, g/dL) 18; volumen de la unidad (mL-eq) 250; fracción retenida del cristaloide 0,2; τ de redistribución del cristaloide (min) 30; fracción transitoria del cristaloide 0,4; ρ (reserva de extracción) 2,5.

| Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,025 | -0,050 | -0,099 |
| Hb (g/dL) | 6,40 | 6,39 | 6,37 | 6,29 |
| volumen circulante C (mL-eq) | 0 | -71 | -134 | -253 |
| precarga (posición) | 0,60 | 0,55 | 0,50 | 0,39 |
| gasto relativo | 1,00 | 0,92 | 0,83 | 0,65 |
| DO2 | 0,34 | 0,31 | 0,28 | 0,22 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,22 | 0,30 | 0,46 |
| relleno acumulado (mL-eq) | 0 | 4 | 16 | 47 |
| PAS (sólo contexto) | 98 | 94 | 90 | 82 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,1 | 3,0 |

| GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | 0,234 | 0,469 |
| Hb (g/dL) | 6,40 | 7,29 | 8,06 |
| volumen circulante C (mL-eq) | 0 | 250 | 500 |
| precarga (posición) | 0,60 | 0,74 | 0,83 |
| gasto relativo | 1,00 | 1,23 | 1,38 |
| DO2 | 0,34 | 0,48 | 0,59 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| PAS (sólo contexto) | 98 | 108 | 115 |
| lactato (sólo contexto) | 3,4 | 3,2 | 3,0 |

| 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,016 | -0,024 | -0,048 | -0,096 |
| Hb (g/dL) | 6,40 | 6,04 | 6,07 | 6,12 | 6,07 |
| volumen circulante C (mL-eq) | 0 | 127 | 86 | -13 | -139 |
| precarga (posición) | 0,60 | 0,68 | 0,65 | 0,59 | 0,50 |
| gasto relativo | 1,00 | 1,13 | 1,09 | 0,99 | 0,83 |
| DO2 | 0,34 | 0,36 | 0,35 | 0,32 | 0,27 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,10 | 0,12 | 0,20 | 0,33 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 2 | 39 |
| PAS (sólo contexto) | 98 | 104 | 102 | 97 | 90 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,8 |

| 2 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,016 | -0,023 | -0,046 | -0,092 |
| Hb (g/dL) | 6,40 | 5,72 | 5,78 | 5,87 | 5,89 |
| volumen circulante C (mL-eq) | 0 | 305 | 247 | 120 | -41 |
| precarga (posición) | 0,60 | 0,76 | 0,74 | 0,67 | 0,57 |
| gasto relativo | 1,00 | 1,27 | 1,23 | 1,12 | 0,95 |
| DO2 | 0,34 | 0,38 | 0,38 | 0,35 | 0,30 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,04 | 0,06 | 0,13 | 0,25 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 0 | 15 |
| PAS (sólo contexto) | 98 | 110 | 108 | 103 | 96 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,2 | 3,0 | 2,6 |

| Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,049 | -0,049 | -0,049 |
| Hb (g/dL) | 6,40 | 6,37 | 6,32 | 6,27 |
| volumen circulante C (mL-eq) | 0 | -132 | -109 | -87 |
| precarga (posición) | 0,60 | 0,50 | 0,52 | 0,54 |
| gasto relativo | 1,00 | 0,84 | 0,87 | 0,90 |
| DO2 | 0,34 | 0,28 | 0,29 | 0,30 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,29 | 0,27 | 0,25 |
| relleno acumulado (mL-eq) | 0 | 16 | 39 | 61 |
| PAS (sólo contexto) | 98 | 91 | 92 | 93 |
| lactato (sólo contexto) | 3,4 | 3,1 | 2,9 | 2,7 |

**Medio — gi_bleed_57m.** tasa de sangrado (mL-eq/min) 5; B0 (mL-eq) 4000; λ/κ (mL-eq) 1500; posición de precarga de llegada sup.; meta del relleno (fracción de lo perdido) 0,75; τ del relleno (min) 240; capacidad del relleno (mL-eq) 1000; contenido de GR de la unidad (Hb, g/dL) 22; volumen de la unidad (mL-eq) 300; fracción retenida del cristaloide 0,2; τ de redistribución del cristaloide (min) 60; fracción transitoria del cristaloide 0,6; ρ (reserva de extracción) 2,5.

| Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,037 | -0,075 | -0,149 |
| Hb (g/dL) | 6,70 | 6,69 | 6,66 | 6,53 |
| volumen circulante C (mL-eq) | 0 | -143 | -274 | -505 |
| precarga (posición) | 0,50 | 0,45 | 0,40 | 0,30 |
| gasto relativo | 1,00 | 0,90 | 0,80 | 0,60 |
| DO2 | 0,34 | 0,31 | 0,27 | 0,20 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,24 | 0,33 | 0,50 |
| relleno acumulado (mL-eq) | 0 | 7 | 26 | 95 |
| PAS (sólo contexto) | 88 | 83 | 79 | 70 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,7 | 3,4 |

| GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | 0,246 | 0,493 |
| Hb (g/dL) | 6,70 | 7,77 | 8,70 |
| volumen circulante C (mL-eq) | 0 | 300 | 600 |
| precarga (posición) | 0,50 | 0,59 | 0,66 |
| gasto relativo | 1,00 | 1,18 | 1,33 |
| DO2 | 0,34 | 0,47 | 0,59 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| PAS (sólo contexto) | 88 | 96 | 103 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,6 |

| 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,036 | -0,073 | -0,145 |
| Hb (g/dL) | 6,70 | 6,41 | 6,43 | 6,46 | 6,39 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -150 | -411 |
| precarga (posición) | 0,50 | 0,53 | 0,51 | 0,45 | 0,34 |
| gasto relativo | 1,00 | 1,05 | 1,01 | 0,90 | 0,68 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,29 | 0,22 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,14 | 0,18 | 0,27 | 0,45 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 18 | 90 |
| PAS (sólo contexto) | 88 | 90 | 88 | 83 | 74 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,7 | 3,3 |

| 2 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,035 | -0,070 | -0,141 |
| Hb (g/dL) | 6,70 | 6,14 | 6,18 | 6,28 | 6,26 |
| volumen circulante C (mL-eq) | 0 | 262 | 181 | -32 | -323 |
| precarga (posición) | 0,50 | 0,58 | 0,56 | 0,49 | 0,38 |
| gasto relativo | 1,00 | 1,16 | 1,11 | 0,98 | 0,76 |
| DO2 | 0,34 | 0,36 | 0,35 | 0,31 | 0,24 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,10 | 0,13 | 0,22 | 0,40 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 4 | 79 |
| PAS (sólo contexto) | 88 | 95 | 93 | 87 | 77 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,7 | 3,2 |

| Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,074 | -0,074 | -0,074 |
| Hb (g/dL) | 6,70 | 6,66 | 6,58 | 6,48 |
| volumen circulante C (mL-eq) | 0 | -269 | -226 | -166 |
| precarga (posición) | 0,50 | 0,40 | 0,42 | 0,44 |
| gasto relativo | 1,00 | 0,80 | 0,84 | 0,88 |
| DO2 | 0,34 | 0,27 | 0,28 | 0,29 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,32 | 0,30 | 0,27 |
| relleno acumulado (mL-eq) | 0 | 26 | 69 | 129 |
| PAS (sólo contexto) | 88 | 79 | 81 | 83 |
| lactato (sólo contexto) | 4,4 | 3,7 | 3,4 | 3,0 |

**Medio — gi_bleed_72f.** tasa de sangrado (mL-eq/min) 5; B0 (mL-eq) 4000; λ/κ (mL-eq) 1500; posición de precarga de llegada sup.; meta del relleno (fracción de lo perdido) 0,75; τ del relleno (min) 240; capacidad del relleno (mL-eq) 1000; contenido de GR de la unidad (Hb, g/dL) 22; volumen de la unidad (mL-eq) 300; fracción retenida del cristaloide 0,2; τ de redistribución del cristaloide (min) 60; fracción transitoria del cristaloide 0,6; ρ (reserva de extracción) 2,5.

| Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,037 | -0,075 | -0,149 |
| Hb (g/dL) | 6,40 | 6,39 | 6,36 | 6,24 |
| volumen circulante C (mL-eq) | 0 | -143 | -274 | -505 |
| precarga (posición) | 0,60 | 0,56 | 0,52 | 0,44 |
| gasto relativo | 1,00 | 0,93 | 0,87 | 0,73 |
| DO2 | 0,34 | 0,32 | 0,29 | 0,24 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,21 | 0,27 | 0,39 |
| relleno acumulado (mL-eq) | 0 | 7 | 26 | 95 |
| PAS (sólo contexto) | 98 | 95 | 92 | 86 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,1 | 2,9 |

| GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | 0,258 | 0,516 |
| Hb (g/dL) | 6,40 | 7,49 | 8,43 |
| volumen circulante C (mL-eq) | 0 | 300 | 600 |
| precarga (posición) | 0,60 | 0,67 | 0,73 |
| gasto relativo | 1,00 | 1,12 | 1,22 |
| DO2 | 0,34 | 0,45 | 0,55 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| PAS (sólo contexto) | 98 | 103 | 108 |
| lactato (sólo contexto) | 3,4 | 3,2 | 3,0 |

| 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,036 | -0,073 | -0,145 |
| Hb (g/dL) | 6,40 | 6,12 | 6,14 | 6,17 | 6,10 |
| volumen circulante C (mL-eq) | 0 | 81 | 16 | -150 | -411 |
| precarga (posición) | 0,60 | 0,62 | 0,60 | 0,56 | 0,47 |
| gasto relativo | 1,00 | 1,04 | 1,01 | 0,93 | 0,79 |
| DO2 | 0,34 | 0,34 | 0,33 | 0,30 | 0,26 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,16 | 0,18 | 0,24 | 0,36 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 18 | 90 |
| PAS (sólo contexto) | 98 | 100 | 98 | 95 | 89 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,9 |

| 2 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,024 | -0,035 | -0,070 | -0,141 |
| Hb (g/dL) | 6,40 | 5,86 | 5,91 | 6,00 | 5,98 |
| volumen circulante C (mL-eq) | 0 | 262 | 181 | -32 | -323 |
| precarga (posición) | 0,60 | 0,66 | 0,65 | 0,59 | 0,50 |
| gasto relativo | 1,00 | 1,11 | 1,08 | 0,99 | 0,84 |
| DO2 | 0,34 | 0,34 | 0,34 | 0,31 | 0,27 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,14 | 0,16 | 0,21 | 0,33 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 4 | 79 |
| PAS (sólo contexto) | 98 | 103 | 101 | 97 | 91 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,3 | 3,1 | 2,8 |

| Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,074 | -0,074 | -0,074 |
| Hb (g/dL) | 6,40 | 6,36 | 6,28 | 6,19 |
| volumen circulante C (mL-eq) | 0 | -269 | -226 | -166 |
| precarga (posición) | 0,60 | 0,52 | 0,53 | 0,55 |
| gasto relativo | 1,00 | 0,87 | 0,89 | 0,92 |
| DO2 | 0,34 | 0,29 | 0,30 | 0,30 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,27 | 0,26 | 0,24 |
| relleno acumulado (mL-eq) | 0 | 26 | 69 | 129 |
| PAS (sólo contexto) | 98 | 92 | 93 | 94 |
| lactato (sólo contexto) | 3,4 | 3,1 | 2,9 | 2,7 |

**Alto — gi_bleed_57m.** tasa de sangrado (mL-eq/min) 2,5; B0 (mL-eq) 5000; λ/κ (mL-eq) 833; posición de precarga de llegada sup.; meta del relleno (fracción de lo perdido) 0,75; τ del relleno (min) 240; capacidad del relleno (mL-eq) 500; contenido de GR de la unidad (Hb, g/dL) 22; volumen de la unidad (mL-eq) 350; fracción retenida del cristaloide 0,3; τ de redistribución del cristaloide (min) 60; fracción transitoria del cristaloide 0,8; ρ (reserva de extracción) 2,5.

| Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,015 | -0,030 | -0,060 |
| Hb (g/dL) | 6,70 | 6,70 | 6,68 | 6,63 |
| volumen circulante C (mL-eq) | 0 | -72 | -137 | -252 |
| precarga (posición) | 0,50 | 0,46 | 0,41 | 0,32 |
| gasto relativo | 1,00 | 0,91 | 0,82 | 0,65 |
| DO2 | 0,34 | 0,31 | 0,28 | 0,22 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,23 | 0,30 | 0,46 |
| relleno acumulado (mL-eq) | 0 | 3 | 13 | 48 |
| PAS (sólo contexto) | 88 | 84 | 80 | 72 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,7 | 3,4 |

| GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | 0,230 | 0,460 |
| Hb (g/dL) | 6,70 | 7,70 | 8,58 |
| volumen circulante C (mL-eq) | 0 | 350 | 700 |
| precarga (posición) | 0,50 | 0,67 | 0,78 |
| gasto relativo | 1,00 | 1,34 | 1,57 |
| DO2 | 0,34 | 0,52 | 0,68 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| PAS (sólo contexto) | 88 | 103 | 114 |
| lactato (sólo contexto) | 4,4 | 4,0 | 3,6 |

| 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,010 | -0,015 | -0,029 | -0,058 |
| Hb (g/dL) | 6,70 | 6,36 | 6,40 | 6,49 | 6,53 |
| volumen circulante C (mL-eq) | 0 | 212 | 156 | 14 | -166 |
| precarga (posición) | 0,50 | 0,61 | 0,59 | 0,51 | 0,39 |
| gasto relativo | 1,00 | 1,22 | 1,17 | 1,02 | 0,78 |
| DO2 | 0,34 | 0,40 | 0,38 | 0,33 | 0,26 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,01 | 0,05 | 0,16 | 0,35 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 0 | 36 |
| PAS (sólo contexto) | 88 | 98 | 96 | 89 | 78 |
| lactato (sólo contexto) | 4,4 | 4,2 | 4,0 | 3,6 | 3,1 |

| 2 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,010 | -0,014 | -0,028 | -0,057 |
| Hb (g/dL) | 6,70 | 6,06 | 6,13 | 6,29 | 6,43 |
| volumen circulante C (mL-eq) | 0 | 475 | 388 | 178 | -84 |
| precarga (posición) | 0,50 | 0,72 | 0,69 | 0,60 | 0,45 |
| gasto relativo | 1,00 | 1,43 | 1,37 | 1,19 | 0,89 |
| DO2 | 0,34 | 0,44 | 0,43 | 0,38 | 0,29 |
| estado de extracción | crítica | compensada | compensada | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 | 0,05 | 0,27 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 0 | 20 |
| PAS (sólo contexto) | 88 | 108 | 105 | 97 | 83 |
| lactato (sólo contexto) | 4,4 | 4,1 | 4,0 | 3,6 | 2,9 |

| Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,029 | -0,029 | -0,029 |
| Hb (g/dL) | 6,70 | 6,68 | 6,65 | 6,61 |
| volumen circulante C (mL-eq) | 0 | -135 | -113 | -83 |
| precarga (posición) | 0,50 | 0,41 | 0,43 | 0,45 |
| gasto relativo | 1,00 | 0,82 | 0,85 | 0,90 |
| DO2 | 0,34 | 0,28 | 0,29 | 0,30 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,30 | 0,28 | 0,25 |
| relleno acumulado (mL-eq) | 0 | 13 | 34 | 64 |
| PAS (sólo contexto) | 88 | 80 | 81 | 83 |
| lactato (sólo contexto) | 4,4 | 3,7 | 3,3 | 2,9 |

**Alto — gi_bleed_72f.** tasa de sangrado (mL-eq/min) 2,5; B0 (mL-eq) 5000; λ/κ (mL-eq) 833; posición de precarga de llegada sup.; meta del relleno (fracción de lo perdido) 0,75; τ del relleno (min) 240; capacidad del relleno (mL-eq) 500; contenido de GR de la unidad (Hb, g/dL) 22; volumen de la unidad (mL-eq) 350; fracción retenida del cristaloide 0,3; τ de redistribución del cristaloide (min) 60; fracción transitoria del cristaloide 0,8; ρ (reserva de extracción) 2,5.

| Sin tratar | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,015 | -0,030 | -0,060 |
| Hb (g/dL) | 6,40 | 6,40 | 6,38 | 6,34 |
| volumen circulante C (mL-eq) | 0 | -72 | -137 | -252 |
| precarga (posición) | 0,60 | 0,56 | 0,53 | 0,46 |
| gasto relativo | 1,00 | 0,94 | 0,88 | 0,76 |
| DO2 | 0,34 | 0,32 | 0,30 | 0,26 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,20 | 0,25 | 0,36 |
| relleno acumulado (mL-eq) | 0 | 3 | 13 | 48 |
| PAS (sólo contexto) | 98 | 95 | 93 | 87 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,1 | 2,9 |

| GR, sangrado controlado | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | 0,241 | 0,481 |
| Hb (g/dL) | 6,40 | 7,42 | 8,32 |
| volumen circulante C (mL-eq) | 0 | 350 | 700 |
| precarga (posición) | 0,60 | 0,74 | 0,83 |
| gasto relativo | 1,00 | 1,23 | 1,38 |
| DO2 | 0,34 | 0,48 | 0,61 |
| estado de extracción | crítica | compensada | compensada |
| déficit crítico efectivo | 0,15 | 0,00 | 0,00 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 |
| PAS (sólo contexto) | 98 | 108 | 115 |
| lactato (sólo contexto) | 3,4 | 3,2 | 3,0 |

| 1 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,010 | -0,015 | -0,029 | -0,058 |
| Hb (g/dL) | 6,40 | 6,08 | 6,12 | 6,20 | 6,23 |
| volumen circulante C (mL-eq) | 0 | 212 | 156 | 14 | -166 |
| precarga (posición) | 0,60 | 0,69 | 0,67 | 0,61 | 0,51 |
| gasto relativo | 1,00 | 1,15 | 1,11 | 1,01 | 0,85 |
| DO2 | 0,34 | 0,37 | 0,36 | 0,33 | 0,28 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,07 | 0,10 | 0,17 | 0,29 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 0 | 36 |
| PAS (sólo contexto) | 98 | 105 | 103 | 98 | 91 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,2 | 3,0 | 2,7 |

| 2 L en 20 min con sangrado | 0′ | 20′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,010 | -0,014 | -0,028 | -0,057 |
| Hb (g/dL) | 6,40 | 5,79 | 5,86 | 6,01 | 6,14 |
| volumen circulante C (mL-eq) | 0 | 475 | 388 | 178 | -84 |
| precarga (posición) | 0,60 | 0,77 | 0,75 | 0,68 | 0,56 |
| gasto relativo | 1,00 | 1,29 | 1,25 | 1,13 | 0,93 |
| DO2 | 0,34 | 0,40 | 0,39 | 0,36 | 0,30 |
| estado de extracción | crítica | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,01 | 0,03 | 0,10 | 0,24 |
| relleno acumulado (mL-eq) | 0 | 0 | 0 | 0 | 20 |
| PAS (sólo contexto) | 98 | 111 | 109 | 104 | 95 |
| lactato (sólo contexto) | 3,4 | 3,3 | 3,2 | 3,0 | 2,6 |

| Hemostasia a los 60 min | 0′ | 60′ | 120′ | 240′ |
|---|---|---|---|---|
| contenido de GR (cambio relativo) | 0,000 | -0,029 | -0,029 | -0,029 |
| Hb (g/dL) | 6,40 | 6,38 | 6,36 | 6,32 |
| volumen circulante C (mL-eq) | 0 | -135 | -113 | -83 |
| precarga (posición) | 0,60 | 0,53 | 0,54 | 0,56 |
| gasto relativo | 1,00 | 0,88 | 0,90 | 0,93 |
| DO2 | 0,34 | 0,30 | 0,30 | 0,31 |
| estado de extracción | crítica | crítica | crítica | crítica |
| déficit crítico efectivo | 0,15 | 0,25 | 0,24 | 0,22 |
| relleno acumulado (mL-eq) | 0 | 13 | 34 | 64 |
| PAS (sólo contexto) | 98 | 93 | 94 | 95 |
| lactato (sólo contexto) | 3,4 | 3,1 | 2,9 | 2,6 |

### 5.7 Lo que leen las restricciones, en toda su tabla (contexto)

Mediana (mínimo–máximo) de cada lectura sobre la cuadrícula de su superficie, junto a la envolvente docente. No se ajusta nada a estas cifras.

| Lectura | Envolvente docente | gi_bleed_57m | gi_bleed_72f |
|---|---|---|---|
| gasto sin tratar a 30′ | 0,85–0,95 / 0,90–0,98 | 0,83 (0,00–0,98) | 0,89 (0,35–0,99) |
| gasto sin tratar a 60′ | 0,70–0,85 / 0,80–0,92 | 0,66 (0,00–0,96) | 0,79 (0,00–0,98) |
| gasto sin tratar a 120′ | 0,45–0,65 / 0,60–0,78 | 0,36 (0,00–0,94) | 0,60 (0,00–0,96) |
| corridas sin tratar que se detienen antes de 120′ | — | 2061 de 6561 | 1269 de 6561 |
| caída de Hb sin tratar a 60′ (v2) | 0,0–0,5 / 0,0–0,4 | 0,024 (0,003–0,189) | 0,023 (0,003–0,181) |
| caída de Hb sin tratar a 120′ (v2) | 0,0–0,9 / 0,0–0,7 | 0,079 (0,011–0,591) | 0,075 (0,010–0,564) |
| mayor subida de Hb sin tratar, minuto a minuto | ≤ 1e-9 | 0,000000000000 (0,000000000000–0,000000000000) | 0,000000000000 (0,000000000000–0,000000000000) |
| ΔHb de una unidad | 0,7–1,2 | 0,91 (0,54–1,60) | 0,93 (0,55–1,63) |
| aumento relativo del gasto con una unidad | techo 0,40 / 0,30 | 0,56 (0,15–1,77) | 0,36 (0,10–1,03) |
| posición tras una unidad (FD-BLD-03, diagnóstico) | — | 0,55 (0,32–0,72) | 0,62 (0,41–0,78) |
| Δgasto 2.ª / 1.ª unidad | ≤ 1 | 0,70 (0,56–0,85) | 0,70 (0,56–0,85) |
| 1 L: contribución inicial (retenido) | 0,15–0,30 | 0,166 (0,078–0,281) | 0,166 (0,078–0,281) |
| 1 L: efecto neto inicial sobre C (V5) | 0,15–0,30 | 0,164 (0,073–0,281) | 0,164 (0,073–0,281) |
| 1 L: retenido a 30′ | 0,15–0,25 | 0,142 (0,052–0,266) | 0,142 (0,052–0,266) |
| 1 L: retenido a 60′ | 0,10–0,20 | 0,103 (0,029–0,232) | 0,103 (0,029–0,232) |
| 1 L: retenido a 120′ | 0,05–0,15 | 0,080 (0,025–0,199) | 0,080 (0,025–0,199) |
| 1 L: dilución pico (g/dL) | 0,2–0,5 | 0,259 (0,097–0,581) | 0,247 (0,092–0,555) |
| 2 L: dilución pico (g/dL) | 0,4–0,8 | 0,504 (0,191–1,070) | 0,481 (0,182–1,022) |
| relleno: fracción repuesta a 60′ | 0,10–0,25 | 0,152 (0,051–0,447) | 0,152 (0,051–0,447) |
| relleno: fracción repuesta a 120′ | 0,20–0,45 | 0,285 (0,095–0,639) | 0,285 (0,095–0,639) |
| relleno: fracción repuesta a 240′ | 0,30–0,60 | 0,429 (0,156–0,735) | 0,429 (0,156–0,735) |
| relleno tras la hemostasia, 60 → 240′ (mL-eq) | > 0 | 34 (9–135) | 34 (9–135) |
<!-- /generado:filtro -->

### 5.8 Lectura del resultado

**La región ya no está vacía.**
- Con la tasa común, 4896 de 4 782 969 candidatos cumplen todas las restricciones que filtran. Con tasas por caso
  (V8), 6030 de 14 348 907. Por caso solo, 5004 en 57m y 8379 en 72f.
- No se cambió ninguna regla después de ver los recuentos, y la cuadrícula es la de P2I-2U (una prueba lo exige).
- Es una región candidata restringida por la docencia, no un conjunto aprobado: no se elige ningún valor.

**U-HB v2 ya no acota nada.**
- Todos los candidatos la cumplen: la caída queda dentro de [0, techo], y la Hb sin tratar no sube en ningún minuto
  (la mayor subida en toda la cuadrícula es 9e-16, ruido numérico).
- En los sobrevivientes, la Hb sin tratar cae poco. En los representativos de 57m: 0,02–0,04 g/dL a los 60 min y
  0,07–0,17 a los 120. Es lo que la docencia admite ahora: sin caída mínima.
- El relleno no se debilitó. FD-BLD-07 sigue acotando: sobreviven sólo τ de 120–240 min y metas de 0,5–0,75. Sin
  FD-BLD-07, sobrevivirían 21 603 candidatos.

**Qué acota la región** (lo que sobrevive sin cada restricción, frente a 4896):

| Sin… | Sobrevivientes |
|---|---|
| U-OUT | 38 502 |
| FD-BLD-07 | 21 603 |
| FD-BLD-05 | 8154 |
| FD-BLD-02 | 7938 |
| FD-BLD-01 | 7371 |
| FD-BLD-06 | 6075 |
| U-HB, FD-BLD-04, la segunda unidad, FD-BLD-08 y FD-BLD-09 | 4896 (no acotan, dado el resto) |

**Variantes:**
- V1 (envolventes ensanchadas un 10 %): 19 443.
- V10 (FD-BLD-07 desde el fin de la pérdida): 9432.
- V6 (dilución desde la Hb de llegada): 4182.
- V7 (pérdida aguda de 500 mL-eq): 3264.
- V9 (FD-BLD-05 desde el fin de la infusión): 1881.
- V4 y V5: igual que la primaria.
  - V5 está implementada y es siempre más estricta: en las 6561 filas del cristaloide de cada caso, el efecto neto
    queda entre 0,0002 y 0,011 por debajo del retenido. Cambia el veredicto de FD-BLD-04 en 36 filas de cada caso,
    siempre de «cumple» a «no cumple».
  - Esas filas no sobreviven a las demás restricciones; FD-BLD-04 no acota, dado el resto. Por eso el recuento no
    cambia.
- V2 y V3: igual que la primaria, porque sólo mueven el diagnóstico de FD-BLD-03.

**Posición de llegada.**
- Todos los sobrevivientes llegan en la posición superior de su banda: 0,5 en 57m y 0,6 en 72f. Es el borde de la
  cuadrícula, así que la acota la cuadrícula: no queda identificada.
- La posición 0,6 de 72f coincide con el límite inferior de la banda euvolémica candidata. La premisa de FD-BLD-02
  («con llenado bajo») es dudosa en ese punto.

**FD-BLD-03, sólo diagnóstico.**
- Con la lectura anterior (57m ≥ 0,6, 72f ≥ 0,7), 3402 de los 4896 sobrevivientes llegarían a la referencia
  euvolémica con una unidad, en al menos uno de los dos casos. Con «ambos ≥ 0,7» (V2) serían 2628, y con «ambos ≥
  0,6» (V3), los 4896.
- V3 es degenerada en 72f: su posición de llegada (0,6) ya está en ese límite antes de la unidad.
- En los representativos, una unidad sube el gasto de 57m entre un 18 y un 34 % (el techo de FD-BLD-02 es 40 %) y el
  estado de extracción pasa de crítico a compensado.
- Nada de esto rechaza candidatos. Queda para la calibración de PA, FC y gasto de referencia que definirá la
  normalización.

**Estado de oxígeno.** Todos los sobrevivientes llegan en déficit crítico, con la banda de entrega en su punto medio,
como ya se vio en P2I-2U.

**Identificabilidad** (a la resolución de la cuadrícula):
- acotadas en parte: la tasa común (2,5 y 5), la meta y la τ del relleno, y la fracción retenida del cristaloide. Las
  cuatro conservan el valor más alto explorado: las restricciones las acotan por abajo y, por arriba, las acota la
  cuadrícula;
- la posición de cada caso queda sólo en el borde;
- quedan con todos sus valores: B0, λ/κ, la capacidad del relleno, la unidad de GR y la cinética del cristaloide;
- κ, λ y ρ siguen sin poder separarse.
- λ/κ ya no queda fijada en 1500, como pasaba cuando FD-BLD-03 filtraba.

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
- Ninguna sonda activa de nivel 2 escribe V ni Hb fuera de BloodState; una prueba lo exige.
- Las comprobaciones de nivel 1 de `calibration.py` (RR1, HR1 a HR4, PL4) siguen escribiendo V, como reglas
  congeladas. Las auditó P2I-2U y quedan fuera de este encargo.
- Dos pruebas siguen ejecutando sondas históricas, como registro y no como validación de la fisiología circulante
  actual: `test_historical_probe_record_overload` y `test_historical_probe_record_p2d7_sepsis_with_preload_loss`.
- Una tercera las ejecuta sólo para comprobar que escriben V fuera de BloodState.
- `bands.DIAGNOSTICS` conserva la clasificación P2D-7 de esa sonda, con su estado `HISTORICAL_PROBE`.
- Cambia el componente `harness_sources` del congelamiento de calibración (sólo `bands.py`), con el motivo registrado.

## 7. Qué no hace

- No elige ningún conjunto final de parámetros ocultos: la región que quede no es una aprobación.
- No usa lactato, trayectorias heredadas, PAS ni PAM para filtrar, ni la posición de precarga (FD-BLD-03 no filtra).
- No amplía, no densifica ni cambia la cuadrícula.
- No migra, no integra y no puebla ningún valor de familia.
