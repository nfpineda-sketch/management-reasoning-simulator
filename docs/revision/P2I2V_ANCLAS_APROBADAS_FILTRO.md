# P2I-2V · Anclas docentes aprobadas del estado sanguíneo compartido y filtro de la región candidata

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución ni cambia lo que ve el residente;
- no migra GI ni otra familia;
- no refiltra el lactato (P2I-2R sigue en pausa, PENDIENTE DE REFILTRADO);
- no calibra la presión ni la FC, ni activa el colapso canónico;
- no se ajusta al motor heredado;
- no elige ningún conjunto final de parámetros ocultos.

Código: `clinical_core/blood_constraints.py` (decisiones, lecturas, variantes y filtro; congelado) y
`clinical_core/blood_filter_report.py` (sólo este informe). Números: `docs/revision/P2I2V_blood_sensitivity.json`
(antes del congelamiento) y `docs/revision/P2I2V_blood_filter.json` (el filtro).

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
| FD-BLD-02: aumento relativo del gasto con una unidad (techo) | ≤ 0,40 (piso 0,15, no exigido) | ≤ 0,30 (piso 0,10, no exigido) | (gasto a los 30 − gasto a los 0) / gasto a los 0 no supera el techo del caso. El piso no se exige (la docencia: no son respuestas obligatorias); V4 lo exige donde el estado responde a la precarga. Todas las posiciones de la cuadrícula están bajo la referencia euvolémica. |
| FD-BLD-03: una unidad no normaliza el gasto | posición < 0,6 | posición < 0,7 | «Normalizado» = posición de precarga tras una unidad en o sobre la referencia euvolémica del caso (banda 0,6–0,7–0,8). 57m debe quedar bajo su límite inferior (no entra en el rango euvolémico); 72f bajo su punto medio (puede acercarse, no llegar). Una corrida determinista por candidato: «de forma fiable» se lee por candidato. |
| SECOND-UNIT: beneficio de la 2.ª unidad ≤ el de la 1.ª | Δ2 ≤ Δ1 | Δ2 ≤ Δ1 | Δgasto de la unidad 2 (30 → 60 min) ≤ Δgasto de la unidad 1 (0 → 30 min), en cada caso. |
| FD-BLD-04: efecto circulante inicial de 1 L de cristaloide | 0,15–0,30 | 0,15–0,30 | Sangrado del caso en curso; 1 L en 20 min desde el minuto 0. Contribución inicial = el mayor cristaloide intravascular retenido (entrado − salido) en 0–30 min, sobre el volumen infundido. |
| FD-BLD-05: cristaloide retenido a 30, 60 y 120 min | 30′ 0,15–0,25, 60′ 0,10–0,20, 120′ 0,05–0,15 | 30′ 0,15–0,25, 60′ 0,10–0,20, 120′ 0,05–0,15 | Cristaloide intravascular retenido a los 30, 60 y 120 min desde el inicio de la infusión, sobre el volumen infundido (1 L). |
| FD-BLD-06: dilución de Hb con 1 y 2 L, con reversión parcial | 1 L 0,2–0,5 g/dL, 2 L 0,4–0,8 g/dL; 0 < dilución(120′) < pico | 1 L 0,2–0,5 g/dL, 2 L 0,4–0,8 g/dL; 0 < dilución(120′) < pico | Dilución = Hb sin la bolsa − Hb con ella, mismo sangrado. Su pico en 0–120 min dentro de la envolvente de cada volumen (1 y 2 L); reversión parcial: 0 < dilución a los 120 < pico. |
| FD-BLD-07: fracción del déficit agudo repuesta por el relleno | 60′ 0,10–0,25, 120′ 0,20–0,45, 240′ 0,30–0,60 | 60′ 0,10–0,25, 120′ 0,20–0,45, 240′ 0,30–0,60 | Pérdida aguda sintética de 200 mL-eq en 10 min (la superficie de P2I-2U que vio la docencia). Fracción repuesta = relleno acumulado / volumen perdido a los 60, 120 y 240 min. |
| FD-BLD-08: el relleno sigue tras la hemostasia | sigue tras la hemostasia mientras quede déficit y brecha a la meta / capacidad | sigue tras la hemostasia mientras quede déficit y brecha a la meta / capacidad | Sangrado GI del caso detenido por completo a los 60 min. Si a los 60 queda déficit (C < 0) y el relleno está bajo min(capacidad, meta × perdido), el relleno debe ser positivo en cada minuto 61–70 y mayor a los 240 que a los 60; nunca supera la capacidad. |
| FD-BLD-09: el relleno diluye la Hb y no añade GR | Hb con relleno < sin relleno; ningún GR añadido | Hb con relleno < sin relleno; ningún GR añadido | Pérdida aguda con y sin relleno: donde el relleno es > 0 a los 60, 120 y 240 min, la Hb con relleno es menor; ningún cambio de relleno lleva GR y el contenido de GR nunca sube. |

**Estructura de la región.** Los parámetros del modelo son comunes a los dos casos; la tasa de sangrado y la posición de llegada son de cada caso. La posición es una banda del caso; una tasa propia del caso es admisible con `CASE_OVERRIDES_FAMILY_DEFAULT`, pero hoy ningún caso la declara: V8 exige una tasa común. Se informan también los sobrevivientes de cada caso por separado (todo libre por caso). Ninguna restricción lee ρ: queda en la región y sólo cambia la etiqueta del estado de extracción.

**Lectura de la sangre.** Hb, volumen circulante, relleno y cristaloide no dependen de λ/κ, de la posición ni de ρ (verificado en los puntos de prueba y, en el filtro, en cada candidato sin tratar que no se detiene). Se leen con λ/κ 1500 y la posición superior del caso, donde ninguna superficie se detiene: ningún candidato sale de una restricción de sangre porque su circulación se detuvo; eso lo juzgan las envolventes de gasto.

**Variantes declaradas antes del filtro.** Cada una cambia una sola lectura y se informa junto a la primaria, nunca en su lugar.

| Variante | Qué cambia |
|---|---|
| `V1_envelope_tolerance` | cada envolvente numérica, ensanchada un 10 % de su ancho en cada extremo |
| `V2_fd03_both_midpoint` | FD-BLD-03: los dos casos bajo el punto medio euvolémico |
| `V3_fd03_both_lower` | FD-BLD-03: los dos casos bajo el límite inferior euvolémico |
| `V4_fd02_lower_bound_when_responsive` | FD-BLD-02: también el piso, donde un reto de +250 mL-eq a la llegada sube el gasto ≥ 10 % |
| `V5_fd04_net_effect` | FD-BLD-04: efecto neto sobre C (con − sin bolsa) en vez del retenido |
| `V6_fd06_from_arrival_hb` | FD-BLD-06: dilución = Hb de llegada − Hb con la bolsa |
| `V7_fd07_500_ml` | FD-BLD-07: pérdida aguda de 500 mL-eq en 10 min |
| `V8_common_bleed_rate` | una sola tasa de sangrado para los dos casos (camino del valor de familia) |
| `V9_fd05_from_end_of_infusion` | FD-BLD-05 a los 30, 60 y 120 min desde el fin de la infusión (minutos 50, 80 y 140) |
| `V10_fd07_from_end_of_loss` | FD-BLD-07 a los 60, 120 y 240 min desde el fin de la pérdida (minutos 70, 130 y 250) |

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
Pendiente: el filtro corre después del commit de congelamiento.
<!-- /generado:filtro -->
