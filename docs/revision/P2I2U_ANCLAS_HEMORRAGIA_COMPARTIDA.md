# P2I-2U · Arnés de calibración alineado y anclas docentes del estado hemorrágico compartido

Este paquete funciona sólo en sombra:
- no integra nada en tiempo de ejecución ni cambia lo que ve el residente;
- no migra GI ni otra familia;
- no refiltra el lactato (P2I-2R sigue PENDIENTE DE REFILTRADO);
- no calibra la presión ni la FC, ni aprueba ningún número;
- no se ajusta al motor heredado.

**Sustituido en parte por P2I-2V (2026-10-27).** Este documento registra P2I-2U tal como se cerró.
- La docencia aprobó después FD-BLD-01 a 09 y las anclas sin tratar A y B. Su estado aparece en la hoja de §6 A.6
  (FACULTY_APPROVED: conducta clínica / envolvente aprobada; parámetros ocultos sin aprobar).
- También aprobó la categoría `CASE_OVERRIDES_FAMILY_DEFAULT` para la tasa de sangrado, sin aprobar ninguna tasa.
- Por eso el recuento de §3 («57 abiertas») ya no rige: quedan las 48 de P2G.
- Fuente: `docs/revision/P2I2V_ANCLAS_APROBADAS_FILTRO.md`.

**Decisiones docentes que aplica (2026-10-27).**
1. SHARED_HAEMORRHAGE_STATE_NEEDED fue la decisión de arquitectura correcta (P2I-2T queda aceptado y cerrado).
2. La decisión sobre una tasa independiente de pérdida de Hb es obsoleta.
3. FD-23, si representa una deriva o tasa independiente de Hb, queda RETIRADA.
4. La sonda congelada de nivel 2 «GI bleed / trauma» no puede conservar la fisiología obsoleta de derivas independientes
   de V y Hb.

Sondas y superficies: `clinical_core/blood_anchors.py`. Números: `docs/revision/P2I2U_blood_anchors.json`.

## 1. La sonda F5, reemplazada (P2I-2U-1)

| | Antes (hasta `94501f5`) | Ahora |
|---|---|---|
| Mecanismo | dos derivas declaradas e independientes: V −10 mL/min y Hb −0,02 g/dL/min durante 60 min | un flujo sintético de sangre total, 10 mL-eq/min durante 60 min (`bands.BloodLoss`), a través de `BloodState` |
| Etiqueta | «GI bleed / trauma» | «GI bleed / trauma», rotulada **SYNTHETIC_CROSS_FAMILY_HAEMORRHAGE_PROBE** (`bands.PROBE_KINDS`); su tasa es sintética, no una tasa GI ni de trauma |
| V y Hb | escritas directamente por la sonda | derivadas del estado compartido: la pérdida de sangre total da la consecuencia de volumen y la de contenido de GR, y el relleno diluye. Ninguna escritura directa de V ni de Hb, ni deriva propia de Hb |
| Lectura a 30′ | V −300 (escrita por la sonda), Hb 12,4 (13 − 0,6 por la deriva), PAM 76 | C −283 mL-eq (el relleno devuelve 17 mL-eq; V = κ·C, con κ = 1), Hb 12,94 (sólo dilución), PAM 77 |
| Lectura a 60′ | la corrida se detenía en el minuto 58 (gasto 0 con pulso) | C −537 mL-eq, Hb 12,78, PAM 14, gasto 0,10: sigue perfundiendo, al borde |

**Por qué la semántica anterior quedó inválida.** P2I-2T decidió que la Hb no tiene una deriva propia del sangrado: resulta
del contenido de GR sobre el volumen circulante. Una sonda que baja la Hb a tasa fija, sin perder GR ni volumen, describe
una fisiología que el núcleo ya no tiene y que la docencia rechazó.

**Qué se conserva.** El concepto de la sonda (la hemorragia como familia transversal de nivel 2), su llegada neutra, sus
minutos y su banda, que sigue TBD.

**Pruebas.** Una prueba exige:
- que la sonda sea sólo flujos `BloodLoss`;
- que nada mueva V ni Hb fuera del estado (`outside_v` y `outside_hb` en 0);
- que su texto diga que la tasa es sintética;
- que la tabla de `bands.report()` marque con «†» la Hb de las sondas que siguen escribiendo V directamente.

**Auditoría de las demás sondas de calibración** que mueven V o Hb directamente. Ninguna sonda viva conserva la
fisiología de dos derivas; sólo la conserva un registro histórico de P2I-2S.

| Sonda | Qué mueve | Clasificación |
|---|---|---|
| reglas congeladas HR1–HR4, RR1, PL4 (`calibration.py`) | V sola (−8 mL/min, reposición) | sondas de deterioro de la coordenada de precarga, no de hemorragia; sin Hb; cambiarlas cambia las reglas congeladas |
| DM1 (`calibration.py`) | Hb sola (−30 %) | anemia aislada para la regla de demanda; no es un sangrado |
| borde de precarga de P2G §11 (`decision_pack.py`) | V sola (8 y 4 mL/min) | igual que HR1, rotulada como «sólo V» en el documento P2G desde P2I-2T |
| demás sondas de nivel 2 (`bands.py`) | T, P, W; V sola, en mL y por fuera de `BloodState` (fuga de −5 mL/min, bolo de 500 mL, −200 / +250 mL, +20 mL/min durante 100 min) | no son hemorragias. Su Hb no sigue a ese volumen (ni diluye ni concentra): la tabla la marca con «†». Si deben pasar por `BloodState` queda abierto: cambiaría `harness_sources` |
| sondas de P2I-2P y P2I-2Q (`oxygen_probes.py`, `hemodynamic_probes.py`) | Hb o V solas | registros históricos anteriores a P2I-2T; no se regeneran |
| `haemorrhage_probes.static_row` (P2I-2S) | V y Hb a la vez, con la tasa heredada `LEGACY_HB_PER_MIN` | registro histórico con su resumen fijado (`760627b3…`); no se regenera. Es la fisiología de dos derivas que P2I-2T y P2I-2U retiraron |

## 2. Recongelamiento (P2I-2U-2)

**Qué cambió.** De los diez componentes del congelamiento de calibración cambia uno, `harness_sources`, porque cambian
dos archivos:
- `bands.py`: la sonda, y la marca «†» en la Hb de las sondas que escriben V directamente;
- `calibration.py`, las razones del registro:
  - ninguna constante del estado sanguíneo se decide por separado;
  - κ es sólo contabilidad;
  - `preload_curve_scale_ml` sólo se decide como λ/κ;
  - la Hb de la unidad la acota sólo FD-BLD-01.

**Qué no cambió.** Los otros nueve componentes, entre ellos `rules` (las reglas congeladas, sus umbrales y sus sondas) y
`bands`. El nuevo resumen y los componentes
quedan registrados con su motivo en `test_clinical_core_calibration_framework.py`.

**Por qué es una actualización autorizada de la arquitectura y no un ajuste a posteriori:**
- la causa es una decisión docente explícita (P2I-2T, confirmada en P2I-2U), no un resultado que se quisiera obtener;
- la sonda cambia de mecanismo, no de números elegidos: la tasa sintética, los minutos y la llegada son los mismos;
- ninguna regla, umbral ni banda cambia, y el golden directo no cambia;
- conservar el resumen anterior habría dejado congelada una fisiología que la docencia retiró.

**Artefactos que cambian por los resúmenes** (las cifras no cambian, salvo donde se dice):
- el paquete P2G y el corte P2I-1, regenerados: sólo cambian sus resúmenes. En P2G cambian además, escritas a mano,
  las filas FD-08, FD-14 y FD-15 (§4) y el párrafo de FD-23 (§3);
- el JSON de sondas de P2I-2T, regenerado con las mismas cifras;
- P2I-2R conserva su congelamiento (`152abc6c…`) y sigue PENDIENTE DE REFILTRADO;
- P2I-2P, P2I-2Q y P2I-2S siguen como registros históricos.

## 3. FD-23 (P2I-2U-3)

**Significado exacto.**
- `hb_loss_g_dl_per_min`, registro `gi_hb_loss_g_dl_per_min`.
- Era la caída de Hb por minuto de sangrado GI sin tratar: el literal del motor 0,009 g/dL/min (`family_engine.py:2170`).
- Las opciones eran «0,009 de familia / coherente con FD-22». Afectaba a la Hb, y se recomendaba como valor de familia
  para que la Hb siguiera la aritmética del motor.
- Era exactamente la tasa de Hb, calibrada aparte, que la docencia retiró.

**Estado: RETIRED — INVALIDATED BY SHARED HAEMORRHAGE STATE.**
- La Hb ahora resulta del contenido de GR y del volumen circulante.
- No queda ninguna deriva de Hb del sangrado, fisiológicamente independiente, que aprobar.
- No se reemplaza por otra decisión de Hb por minuto. Su id no se reutiliza.

**Decisiones abiertas.**
- Tabla maestra de P2G: 48 abiertas (FD-01 a FD-50, menos FD-23, retirada, y FD-49, resuelta).
- Más las 9 FD-BLD de este documento, todas ABIERTAS.
- Total: 57 decisiones docentes abiertas.
- Las anclas sin tratar A–D quedan como preguntas para fijar envolventes de paciente más adelante; no son decisiones
  numeradas.

## 4. Lo que no se pide a la docencia (P2I-2U-4)

**No se aprueban por separado** B0, κ, λ, la τ, la meta y la capacidad del relleno, el contenido y el volumen de la
unidad de GR, ni la cinética del cristaloide:
- las razones del registro lo dicen para B0, κ, λ (sólo como λ/κ), el relleno y la Hb de la unidad;
- el volumen de la unidad y la cinética del cristaloide no tienen entrada en el registro: son parámetros provisionales
  de los contribuyentes, y tampoco se piden;
- la docencia fija envolventes de paciente (FD-BLD, anclas A–D), y esas envolventes acotan, a la vez, las combinaciones
  de parámetros que las mueven (§6 A.5).

**κ y λ** se mantienen separados sólo para la implementación:
- se explora λ/κ, con κ = 1;
- la prueba estructural de §6 A.5 muestra que (κ, λ) y (2κ, 2λ) dan exactamente las mismas anclas.

**λ en P2G.** FD-08, FD-14 y FD-15 de la tabla maestra de P2G ofrecen `preload_curve_scale_ml` 600–833–1500.
- Con κ = 1, esos valores son λ/κ: la misma razón que acotan FD-BLD-02 a 04 (§6 A.5).
- Las respuestas se concilian entre sí; ninguna fija λ por sí sola.
- Esas tres filas de P2G lo dicen ahora; no cambian sus opciones ni su estado.

## 5. Superficies y anclas (P2I-2U-5 a P2I-2U-11)

Las tablas están en §6, generadas. Salvo donde se dice, las cifras de este resumen son de la referencia; las medianas y
los rangos son de la cuadrícula sintética, no bandas.

- **Sin tratar (A.1).** Lo que mueve la Hb es el relleno, no el sangrado.
  - Con el sangrado de referencia, la Hb apenas cae en 2 h: 6,70 → 6,60 en 57m y 6,40 → 6,31 en 72f.
  - El gasto de la referencia cae a 0,36 (57m) y 0,58 (72f) a los 120 min.
  - En la cuadrícula, 78 de 243 corridas de 57m y 42 de 243 de 72f dejan de perfundir antes de los 120 min. Las
    detienen sobre todo la tasa alta, la posición baja y λ/κ corta.
  - Las tablas cuentan las corridas que siguen perfundiendo (n) y las resumen también con las detenidas incluidas. A
    los 120 min, la mediana del gasto es 0,62 entre las que siguen y 0,37 con las detenidas en 0 (57m); en 72f, 0,69 y
    0,59.
  - Con la banda de entrega en su punto medio, la llegada ya está en déficit crítico. El ancla C no puede leerse como
    «cuándo entra en crítico», sino como cuánto se agrava.
- **Una unidad de GR (A.2).**
  - ΔHb mediana de 0,91 g/dL en 57m y 0,93 en 72f, con un rango de 0,54 a 1,63 según B0 y la unidad. No se ajustó al
    +0,85 heredado.
  - El efecto sobre el gasto depende de la respuesta a la precarga: con la posición inferior llega hasta +1,77 (57m).
  - Una unidad alcanza la referencia euvolémica inferior en el 33 % (57m) y el 56 % (72f) de la cuadrícula.
- **Dos unidades (A.2).** La segunda unidad da menos gasto que la primera en toda la cuadrícula, pero eso es
  estructural, no un hallazgo.
  - Con la curva de precarga exponencial, Δgasto de la 2.ª / Δgasto de la 1.ª = exp(−volumen de la unidad / (λ/κ)). En
    la referencia vale 0,70, sea cual sea la posición, B0 o la Hb de la unidad.
  - Una prueba lo fija como identidad.
  - La segunda unidad también da menos ΔHb en el 100 % de la cuadrícula.
- **Cristaloide durante el sangrado (A.3).**
  - El efecto intravascular es transitorio: en la referencia queda el 85 %, el 62 % y el 50 % del pico a los 30, 60 y
    120 min.
  - La dilución se revierte en un 42–53 % entre los 60 y los 120 min con 1 L, y en un 44–54 % con 2 L.
  - El Δgasto al terminar 1 L depende sobre todo de la posición de llegada:
    - en 57m es 0,23 en la referencia;
    - las medianas son 0,68, 0,31 y 0,17 con la posición inferior, media y superior;
    - la retención y λ/κ lo modulan.
  - En 57m, 162 de 729 corridas sin cristaloide y 84 con 1 L se detienen antes de los 120 min. Cada fila resume sólo los
    pares que siguen perfundiendo los dos (columna n).
  - El efecto neto sobre C es algo menor que el retenido, porque mientras la circulación está sobre la llegada el
    relleno espera.
- **Relleno (A.4).**
  - En la referencia repone el 18 % de una pérdida aguda a los 60 min y el 31 % a los 120. En la cuadrícula, las
    medianas son 15 % y 28 %, con rangos de 5–45 % y 9–64 % según la meta y la τ.
  - Diluye la Hb: 0,11 g/dL a los 120 min en la referencia de 57m (0,10 en 72f; mediana de la cuadrícula, 0,09).
  - Sigue después de la hemostasia mientras quede déficit: 45 mL-eq en la referencia y una mediana de 44 (17–68).
  - Con la pérdida explorada (200 mL-eq), la capacidad limita sólo con su valor más bajo (100 mL-eq, el 11 % de la
    cuadrícula).
  - El relleno se acerca a la meta en primer orden y no llega al 99 % de ella en 4 h.
- **Identificabilidad (A.5).**
  - Bien acotables:
    - λ/κ, que domina sólo la razón de la segunda unidad; en el gasto y el déficit sin tratar pesa 0,53–0,77, detrás
      de la tasa de sangrado y de la posición;
    - la posición de llegada, que domina el Δgasto de una unidad y el del cristaloide;
    - la retención del cristaloide, que domina su efecto pico y la dilución;
    - la fracción transitoria del cristaloide, que domina retenido / pico. Es un ancla añadida tras la revisión para que
      FD-BLD-05 tenga la suya; antes esta fracción quedaba como parcial.
  - Parcialmente acotables:
    - la tasa de sangrado, que es el mayor motor del gasto y del déficit sin tratar pero comparte con la posición
      (0,82–0,95) y λ/κ (0,53–0,77);
    - B0;
    - la meta y la τ del relleno;
    - la Hb y el volumen de la unidad;
    - la τ de redistribución del cristaloide.
  - Mal identificada: la capacidad del relleno, que no se distingue sin pérdidas mayores.
  - No identificables por separado: κ y λ (sólo λ/κ) y ρ (sólo ρ × la entrega de llegada).
- **Autoridad de la tasa de sangrado (A.7).** El encargo pide evaluar CASE_OVERRIDES_FAMILY_DEFAULT como preferida; no
  se adopta.
  - Permite casos con sangrados distintos donde el autor lo diga.
  - Su riesgo es que el valor de familia gobierna en silencio a los casos sin declaración.
  - Se añade FAMILY_ALLOWED_RANGE, que P2G lista para esta tasa (FD-50).
  - Los registros de autoridad de producción siguen vacíos.

**Sin lactato (P2I-2U-12).** No se volvió a correr ningún filtro FD-LAC. El lactato aparece sólo como contexto, con la
cinética del punto medio de P2F.

## 6. Tablas (generado)

<!-- generado:anclas-hemorragia -->
Generado desde las anclas `54ad30f9e4851e3127fc1ab227fcb27a6c34eb9d07e62a699d595a9ea74cd943` (`python -m clinical_core.blood_anchors`). Llegada: cada caso GI con sus bandas en el punto medio (posición de precarga: la que indique la tabla), cinética del lactato del punto medio de P2F (sólo contexto), ρ 2,5 con la banda de entrega de llegada re-anclada. κ = 1: la escala se explora como λ/κ. **Todos los rangos son exploraciones SINTÉTICAS, no valores aprobados ni bandas nuevas:** λ/κ reutiliza los tres puntos candidatos del registro de `preload_curve_scale_ml` y la posición recorre la banda del caso; el resto no es una banda candidata. Cada celda: referencia (mínimo–máximo en la cuadrícula).

| Parámetro | Referencia (provisional) | Exploración sintética |
|---|---|---|
| tasa de sangrado (mL-eq/min) | 2,5 | 1,25 / 2,5 / 5 |
| B0 (mL-eq) | 4000 | 3000 / 4000 / 5000 |
| λ/κ (mL-eq) | 833 | 600 / 833 / 1500 |
| posición de precarga de llegada | punto medio de la banda del caso | inf. / medio / sup. |
| meta del relleno (fracción de lo perdido) | 0,5 | 0,25 / 0,5 / 0,75 |
| τ del relleno (min) | 120 | 60 / 120 / 240 |
| capacidad del relleno (mL-eq) | 1000 | 100 / 500 / 1000 |
| Hb de la unidad de GR (g/dL) | 20 | 18 / 20 / 22 |
| volumen de la unidad (mL-eq) | 300 | 250 / 300 / 350 |
| retención intravascular del cristaloide | 0,125 | 0,125 / 0,2 / 0,3 |
| τ de redistribución del cristaloide (min) | 30 | 15 / 30 / 60 |
| fracción transitoria del cristaloide | 0,6 | 0,4 / 0,6 / 0,8 |
| ρ (reserva de extracción) | 2,5 | 1 / 2,5 / 3 |

### A.1 Sangrado sin tratar (P2I-2U-5)

**gi_bleed_57m** — 243 combinaciones de la cuadrícula (tasa de sangrado (mL-eq/min), B0 (mL-eq), λ/κ (mL-eq), posición de precarga de llegada, meta del relleno (fracción de lo perdido)); 78 se detienen antes de los 120 min (el gasto llega a 0 con pulso; colapso apagado). Referencia: sigue perfundiendo a los 120 min.

| Magnitud | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| corridas que siguen perfundiendo | 243 de 243 | 234 de 243 | 213 de 243 | 165 de 243 |
| sangre total perdida (mL-eq) | 0 (0–0) | 75 (38–150) | 150 (75–300) | 300 (150–600) |
| desviación circulante C (mL-eq) | 0 (0–0) | -71 (-146–-34) | -134 (-284–-63) | -245 (-545–-109) |
| cambio del contenido de GR | 0,000 (0,000–0,000) | -0,019 (-0,050–-0,007) | -0,037 (-0,100–-0,015) | -0,075 (-0,199–-0,030) |
| Hb (g/dL) | 6,70 (6,70–6,70) | 6,69 (6,67–6,70) | 6,67 (6,59–6,69) | 6,60 (6,30–6,68) |
| precarga efectiva (posición 0–1) | 0,35 (0,20–0,50) | 0,29 (0,05–0,49) | 0,24 (0,01–0,48) | 0,13 (0,02–0,46) |
| gasto relativo | 1,00 (1,00–1,00) | 0,84 (0,24–0,98) | 0,68 (0,03–0,96) | 0,36 (0,06–0,92) |
| índice de DO2 | 0,34 (0,34–0,34) | 0,28 (0,08–0,33) | 0,23 (0,01–0,32) | 0,12 (0,02–0,31) |
| déficit efectivo | 0,15 (0,15–0,15) | 0,29 (0,17–0,80) | 0,43 (0,19–0,98) | 0,69 (0,22–0,95) |
| PAS (contexto) | 88 (88–88) | 81 (31–87) | 73 (4–86) | 48 (8–85) |
| PAM (contexto) | 65 (65–65) | 60 (23–65) | 55 (3–64) | 36 (6–63) |
| lactato (contexto) | 4,4 (4,4–4,4) | 4,0 (4,0–4,1) | 3,8 (3,7–4,0) | 3,6 (3,1–3,9) |
| gasto relativo, con las detenidas en 0 | 1,00 (1,00–1,00) | 0,84 (0,00–0,98) | 0,68 (0,00–0,96) | 0,36 (0,00–0,92) |
| déficit efectivo, con las detenidas en su valor al detenerse | 0,15 (0,15–0,15) | 0,29 (0,17–1,00) | 0,43 (0,19–1,00) | 0,69 (0,22–1,00) |

El mínimo–máximo de cada fila resume sólo las corridas que siguen perfundiendo en ese minuto (primera fila); las dos últimas filas incluyen las detenidas: gasto 0 y el déficit con que se detuvieron, que es un piso (sin tratamiento no mejora). Una corrida detenida no tiene Hb.

Estado del O2 en la cuadrícula (corridas que siguen perfundiendo): 0′ crítica 243; 30′ crítica 234; 60′ crítica 213; 120′ crítica 165. Con la banda de entrega de llegada en su punto medio, la llegada ya está en déficit crítico.

Proporción de corridas que se detienen antes de los 120 min, por valor de cada dimensión: tasa de sangrado (mL-eq/min): 1,25 4 %, 2,5 26 %, 5 67 %; B0 (mL-eq): 3000 32 %, 4000 32 %, 5000 32 %; λ/κ (mL-eq): 600 52 %, 833 33 %, 1500 11 %; posición de precarga de llegada: inf. 59 %, medio 26 %, sup. 11 %; meta del relleno (fracción de lo perdido): 0,25 37 %, 0,5 30 %, 0,75 30 %.

**gi_bleed_72f** — 243 combinaciones de la cuadrícula (tasa de sangrado (mL-eq/min), B0 (mL-eq), λ/κ (mL-eq), posición de precarga de llegada, meta del relleno (fracción de lo perdido)); 42 se detienen antes de los 120 min (el gasto llega a 0 con pulso; colapso apagado). Referencia: sigue perfundiendo a los 120 min.

| Magnitud | 0′ | 30′ | 60′ | 120′ |
|---|---|---|---|---|
| corridas que siguen perfundiendo | 243 de 243 | 243 de 243 | 234 de 243 | 201 de 243 |
| sangre total perdida (mL-eq) | 0 (0–0) | 75 (38–150) | 150 (75–300) | 300 (150–600) |
| desviación circulante C (mL-eq) | 0 (0–0) | -71 (-146–-34) | -134 (-284–-63) | -245 (-545–-109) |
| cambio del contenido de GR | 0,000 (0,000–0,000) | -0,019 (-0,050–-0,007) | -0,037 (-0,100–-0,015) | -0,075 (-0,199–-0,030) |
| Hb (g/dL) | 6,40 (6,40–6,40) | 6,39 (6,37–6,40) | 6,37 (6,29–6,39) | 6,31 (6,02–6,38) |
| precarga efectiva (posición 0–1) | 0,45 (0,30–0,60) | 0,40 (0,11–0,59) | 0,35 (0,02–0,58) | 0,26 (0,01–0,57) |
| gasto relativo | 1,00 (1,00–1,00) | 0,89 (0,36–0,98) | 0,79 (0,05–0,97) | 0,58 (0,01–0,95) |
| índice de DO2 | 0,34 (0,34–0,34) | 0,30 (0,12–0,33) | 0,27 (0,02–0,33) | 0,20 (0,00–0,32) |
| déficit efectivo | 0,15 (0,15–0,15) | 0,24 (0,16–0,70) | 0,33 (0,18–0,96) | 0,51 (0,20–0,99) |
| PAS (contexto) | 98 (98–98) | 93 (54–97) | 88 (8–97) | 79 (2–96) |
| PAM (contexto) | 74 (74–74) | 71 (42–74) | 67 (6–73) | 61 (1–72) |
| lactato (contexto) | 3,4 (3,4–3,4) | 3,3 (3,3–3,3) | 3,1 (3,1–3,3) | 3,1 (2,8–3,5) |
| gasto relativo, con las detenidas en 0 | 1,00 (1,00–1,00) | 0,89 (0,36–0,98) | 0,79 (0,00–0,97) | 0,58 (0,00–0,95) |
| déficit efectivo, con las detenidas en su valor al detenerse | 0,15 (0,15–0,15) | 0,24 (0,16–0,70) | 0,33 (0,18–0,99) | 0,51 (0,20–1,00) |

El mínimo–máximo de cada fila resume sólo las corridas que siguen perfundiendo en ese minuto (primera fila); las dos últimas filas incluyen las detenidas: gasto 0 y el déficit con que se detuvieron, que es un piso (sin tratamiento no mejora). Una corrida detenida no tiene Hb.

Estado del O2 en la cuadrícula (corridas que siguen perfundiendo): 0′ crítica 243; 30′ crítica 243; 60′ crítica 234; 120′ crítica 201. Con la banda de entrega de llegada en su punto medio, la llegada ya está en déficit crítico.

Proporción de corridas que se detienen antes de los 120 min, por valor de cada dimensión: tasa de sangrado (mL-eq/min): 1,25 0 %, 2,5 11 %, 5 41 %; B0 (mL-eq): 3000 17 %, 4000 17 %, 5000 17 %; λ/κ (mL-eq): 600 33 %, 833 15 %, 1500 4 %; posición de precarga de llegada: inf. 37 %, medio 15 %, sup. 0 %; meta del relleno (fracción de lo perdido): 0,25 22 %, 0,5 15 %, 0,75 15 %.

### A.2 Una y dos unidades de GR, con el sangrado controlado (P2I-2U-6 y 7)

**gi_bleed_57m** — 243 combinaciones (Hb de la unidad de GR (g/dL), volumen de la unidad (mL-eq), λ/κ (mL-eq), posición de precarga de llegada, B0 (mL-eq)); unidad 1 en 0–30 min, unidad 2 en 30–60 min.

| Magnitud | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| Hb (g/dL) | 6,70 (6,70–6,70) | 7,63 (7,24–8,30) | 8,43 (7,73–9,59) |
| desviación circulante C (mL-eq) | 0 (0–0) | 300 (250–350) | 600 (500–700) |
| precarga efectiva (posición) | 0,35 (0,20–0,50) | 0,55 (0,32–0,72) | 0,68 (0,43–0,84) |
| gasto relativo | 1,00 (1,00–1,00) | 1,56 (1,15–2,77) | 1,95 (1,28–3,75) |
| respuesta a +100 mL-eq (Δgasto) | 0,210 (0,064–0,614) | 0,147 (0,051–0,405) | 0,102 (0,040–0,267) |
| índice de DO2 | 0,34 (0,34–0,34) | 0,60 (0,42–1,17) | 0,84 (0,50–1,83) |
| déficit efectivo | 0,15 (0,15–0,15) | 0,00 (0,00–0,00) | 0,00 (0,00–0,00) |
| PAS (contexto) | 88 (88–88) | 113 (95–168) | 131 (101–212) |

| Incremento | unidad 1 | unidad 2 |
|---|---|---|
| ΔHb (g/dL) | 0,91 (0,54–1,60) | 0,80 (0,49–1,30) |
| Δgasto | 0,561 (0,154–1,768) | 0,392 (0,130–0,987) |
| ΔDO2 | 0,260 (0,084–0,826) | 0,226 (0,080–0,662) |
| respuesta a la precarga antes de la unidad | 0,210 (0,064–0,614) | 0,147 (0,051–0,405) |

- Rendimiento decreciente del gasto (Δ de la 2.ª < Δ de la 1.ª): 100 % de la cuadrícula. Es estructural, no un hallazgo: con la curva de precarga exponencial, Δgasto de la 2.ª / Δgasto de la 1.ª = exp(−volumen de la unidad / (λ/κ)) en toda la cuadrícula; la posición, B0 y la Hb de la unidad no entran. ΔHb de la 2.ª menor que la de la 1.ª: 100 %.
- Posición tras 1 U en la referencia euvolémica del caso (banda 0,60–0,80): ≥ 0,60 en 33 %, ≥ 0,70 en 4 %; tras 2 U: 74 % y 44 %.
- Por posición de llegada (respuesta a la precarga): inf.: posición 0,20 (0,20–0,20) → 0,44 (0,32–0,55), Δgasto 1.ª 1,209 (0,614–1,768), 2.ª 0,844 (0,520–0,987); medio: posición 0,35 (0,35–0,35) → 0,55 (0,45–0,64), Δgasto 1.ª 0,561 (0,285–0,821), 2.ª 0,392 (0,241–0,458); sup.: posición 0,50 (0,50–0,50) → 0,65 (0,58–0,72), Δgasto 1.ª 0,302 (0,154–0,442), 2.ª 0,211 (0,130–0,247).

**gi_bleed_72f** — 243 combinaciones (Hb de la unidad de GR (g/dL), volumen de la unidad (mL-eq), λ/κ (mL-eq), posición de precarga de llegada, B0 (mL-eq)); unidad 1 en 0–30 min, unidad 2 en 30–60 min.

| Magnitud | antes | tras 1 U | tras 2 U |
|---|---|---|---|
| Hb (g/dL) | 6,40 (6,40–6,40) | 7,35 (6,95–8,03) | 8,17 (7,45–9,35) |
| desviación circulante C (mL-eq) | 0 (0–0) | 300 (250–350) | 600 (500–700) |
| precarga efectiva (posición) | 0,45 (0,30–0,60) | 0,62 (0,41–0,78) | 0,73 (0,50–0,88) |
| gasto relativo | 1,00 (1,00–1,00) | 1,37 (1,10–2,03) | 1,63 (1,19–2,61) |
| respuesta a +100 mL-eq (Δgasto) | 0,138 (0,043–0,358) | 0,096 (0,034–0,236) | 0,067 (0,027–0,156) |
| índice de DO2 | 0,34 (0,34–0,34) | 0,53 (0,41–0,87) | 0,71 (0,47–1,29) |
| déficit efectivo | 0,15 (0,15–0,15) | 0,00 (0,00–0,00) | 0,00 (0,00–0,00) |
| PAS (contexto) | 98 (98–98) | 115 (103–144) | 126 (107–170) |

| Incremento | unidad 1 | unidad 2 |
|---|---|---|
| ΔHb (g/dL) | 0,93 (0,55–1,63) | 0,82 (0,50–1,32) |
| Δgasto | 0,358 (0,102–1,031) | 0,258 (0,087–0,575) |
| ΔDO2 | 0,186 (0,067–0,527) | 0,165 (0,064–0,428) |
| respuesta a la precarga antes de la unidad | 0,138 (0,043–0,358) | 0,096 (0,034–0,236) |

- Rendimiento decreciente del gasto (Δ de la 2.ª < Δ de la 1.ª): 100 % de la cuadrícula. Es estructural, no un hallazgo: con la curva de precarga exponencial, Δgasto de la 2.ª / Δgasto de la 1.ª = exp(−volumen de la unidad / (λ/κ)) en toda la cuadrícula; la posición, B0 y la Hb de la unidad no entran. ΔHb de la 2.ª menor que la de la 1.ª: 100 %.
- Posición tras 1 U en la referencia euvolémica del caso (banda 0,60–0,80): ≥ 0,60 en 56 %, ≥ 0,70 en 22 %; tras 2 U: 89 % y 59 %.
- Por posición de llegada (respuesta a la precarga): inf.: posición 0,30 (0,30–0,30) → 0,51 (0,41–0,61), Δgasto 1.ª 0,705 (0,358–1,031), 2.ª 0,492 (0,303–0,575); medio: posición 0,45 (0,45–0,45) → 0,62 (0,53–0,69), Δgasto 1.ª 0,370 (0,188–0,540), 2.ª 0,258 (0,159–0,301); sup.: posición 0,60 (0,60–0,60) → 0,72 (0,66–0,78), Δgasto 1.ª 0,202 (0,102–0,295), 2.ª 0,141 (0,087–0,164).

### A.3 Cristaloide durante sangrado continuo (P2I-2U-8)

**gi_bleed_57m, 1 L en 20 min** — 729 combinaciones (retención intravascular del cristaloide, τ de redistribución del cristaloide (min), fracción transitoria del cristaloide, λ/κ (mL-eq), B0 (mL-eq), posición de precarga de llegada); comparado con el mismo sangrado sin cristaloide; antes de los 120 min se detienen 84 corridas con cristaloide y 162 sin él, y cada fila resume sólo los pares que siguen perfundiendo los dos (columna n). Efecto pico en C 102 (77–279) mL-eq (minuto 20 en la referencia); cristaloide retenido pico 104 (78–281) mL-eq; dilución pico de Hb 0,17 (0,10–0,57) g/dL. Δgasto al terminar, por posición de llegada: inf. 0,68 (0,21–1,61), medio 0,31 (0,10–0,75), sup. 0,17 (0,05–0,40).

| Minuto | n | retenido (mL-eq) | retenido / pico | efecto neto en C | dilución de Hb | reversión | gasto | Δgasto | DO2 | déficit | PAS (contexto) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 729 | 104 (78–281) | 1,00 (1,00–1,00) | 102 (77–279) | 0,17 (0,10–0,57) | 0,00 (0,00–0,00) | 1,12 (1,02–2,28) | 0,23 (0,05–1,61) | 0,37 (0,34–0,73) | 0,08 (0,00–0,16) | 93 (89–146) |
| 30 | 729 | 89 (52–266) | 0,85 (0,67–0,94) | 84 (49–261) | 0,14 (0,07–0,54) | 0,17 (0,06–0,35) | 1,03 (0,85–2,09) | 0,19 (0,03–1,59) | 0,34 (0,29–0,67) | 0,14 (0,00–0,29) | 89 (81–137) |
| 60 | 648 | 64 (29–232) | 0,62 (0,37–0,82) | 60 (26–216) | 0,10 (0,03–0,45) | 0,42 (0,22–0,67) | 0,83 (0,45–1,37) | 0,15 (0,02–1,07) | 0,28 (0,15–0,45) | 0,31 (0,00–0,63) | 80 (59–105) |
| 120 | 567 | 52 (25–199) | 0,50 (0,28–0,74) | 49 (24–176) | 0,08 (0,03–0,35) | 0,53 (0,29–0,76) | 0,51 (0,17–0,95) | 0,14 (0,02–0,71) | 0,17 (0,06–0,31) | 0,58 (0,23–0,86) | 66 (22–86) |

**gi_bleed_57m, 2 L en 20 min** — 729 combinaciones (retención intravascular del cristaloide, τ de redistribución del cristaloide (min), fracción transitoria del cristaloide, λ/κ (mL-eq), B0 (mL-eq), posición de precarga de llegada); comparado con el mismo sangrado sin cristaloide; antes de los 120 min se detienen 27 corridas con cristaloide y 162 sin él, y cada fila resume sólo los pares que siguen perfundiendo los dos (columna n). Efecto pico en C 206 (155–561) mL-eq (minuto 20 en la referencia); cristaloide retenido pico 208 (157–562) mL-eq; dilución pico de Hb 0,33 (0,20–1,06) g/dL. Δgasto al terminar, por posición de llegada: inf. 1,25 (0,41–2,63), medio 0,58 (0,19–1,22), sup. 0,31 (0,10–0,66).

| Minuto | n | retenido (mL-eq) | retenido / pico | efecto neto en C | dilución de Hb | reversión | gasto | Δgasto | DO2 | déficit | PAS (contexto) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 729 | 208 (157–562) | 1,00 (1,00–1,00) | 206 (155–561) | 0,33 (0,20–1,06) | 0,00 (0,00–0,00) | 1,32 (1,07–3,30) | 0,43 (0,10–2,63) | 0,43 (0,35–1,01) | 0,00 (0,00–0,14) | 102 (91–191) |
| 30 | 729 | 177 (105–531) | 0,85 (0,67–0,94) | 173 (101–527) | 0,28 (0,13–1,01) | 0,16 (0,05–0,35) | 1,21 (1,02–3,13) | 0,38 (0,07–2,63) | 0,40 (0,33–0,96) | 0,01 (0,00–0,16) | 98 (89–184) |
| 60 | 648 | 128 (57–464) | 0,62 (0,37–0,82) | 116 (53–448) | 0,19 (0,07–0,86) | 0,44 (0,19–0,67) | 0,96 (0,59–2,26) | 0,28 (0,04–1,95) | 0,32 (0,20–0,70) | 0,21 (0,00–0,51) | 86 (69–144) |
| 120 | 567 | 104 (50–398) | 0,50 (0,28–0,74) | 96 (47–343) | 0,15 (0,06–0,65) | 0,54 (0,32–0,76) | 0,64 (0,27–1,28) | 0,27 (0,04–1,22) | 0,21 (0,09–0,40) | 0,48 (0,00–0,78) | 72 (36–101) |

**gi_bleed_72f, 1 L en 20 min** — 729 combinaciones (retención intravascular del cristaloide, τ de redistribución del cristaloide (min), fracción transitoria del cristaloide, λ/κ (mL-eq), B0 (mL-eq), posición de precarga de llegada); comparado con el mismo sangrado sin cristaloide; antes de los 120 min se detienen 6 corridas con cristaloide y 81 sin él, y cada fila resume sólo los pares que siguen perfundiendo los dos (columna n). Efecto pico en C 102 (77–279) mL-eq (minuto 20 en la referencia); cristaloide retenido pico 104 (78–281) mL-eq; dilución pico de Hb 0,16 (0,10–0,55) g/dL. Δgasto al terminar, por posición de llegada: inf. 0,40 (0,12–0,94), medio 0,21 (0,06–0,49), sup. 0,11 (0,03–0,27).

| Minuto | n | retenido (mL-eq) | retenido / pico | efecto neto en C | dilución de Hb | reversión | gasto | Δgasto | DO2 | déficit | PAS (contexto) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 729 | 104 (78–281) | 1,00 (1,00–1,00) | 102 (77–279) | 0,16 (0,10–0,55) | 0,00 (0,00–0,00) | 1,08 (1,01–1,75) | 0,15 (0,03–0,94) | 0,36 (0,34–0,56) | 0,11 (0,00–0,16) | 101 (99–132) |
| 30 | 729 | 89 (52–266) | 0,85 (0,67–0,94) | 84 (49–261) | 0,13 (0,06–0,52) | 0,17 (0,06–0,35) | 1,02 (0,92–1,64) | 0,13 (0,02–0,93) | 0,34 (0,31–0,53) | 0,15 (0,00–0,24) | 99 (94–127) |
| 60 | 729 | 64 (29–232) | 0,62 (0,37–0,82) | 60 (26–216) | 0,09 (0,03–0,43) | 0,42 (0,22–0,67) | 0,89 (0,54–1,30) | 0,10 (0,01–0,88) | 0,30 (0,18–0,42) | 0,26 (0,00–0,55) | 93 (77–111) |
| 120 | 648 | 52 (25–199) | 0,50 (0,28–0,74) | 49 (24–176) | 0,07 (0,03–0,34) | 0,53 (0,29–0,76) | 0,68 (0,29–0,97) | 0,09 (0,01–0,60) | 0,22 (0,10–0,31) | 0,44 (0,21–0,76) | 83 (44–97) |

**gi_bleed_72f, 2 L en 20 min** — 729 combinaciones (retención intravascular del cristaloide, τ de redistribución del cristaloide (min), fracción transitoria del cristaloide, λ/κ (mL-eq), B0 (mL-eq), posición de precarga de llegada); comparado con el mismo sangrado sin cristaloide; antes de los 120 min se detienen 0 corridas con cristaloide y 81 sin él, y cada fila resume sólo los pares que siguen perfundiendo los dos (columna n). Efecto pico en C 206 (155–561) mL-eq (minuto 20 en la referencia); cristaloide retenido pico 208 (157–562) mL-eq; dilución pico de Hb 0,31 (0,19–1,01) g/dL. Δgasto al terminar, por posición de llegada: inf. 0,73 (0,24–1,53), medio 0,38 (0,12–0,80), sup. 0,21 (0,07–0,44).

| Minuto | n | retenido (mL-eq) | retenido / pico | efecto neto en C | dilución de Hb | reversión | gasto | Δgasto | DO2 | déficit | PAS (contexto) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 729 | 208 (157–562) | 1,00 (1,00–1,00) | 206 (155–561) | 0,31 (0,19–1,01) | 0,00 (0,00–0,00) | 1,21 (1,05–2,34) | 0,28 (0,07–1,53) | 0,39 (0,34–0,71) | 0,02 (0,00–0,16) | 107 (100–158) |
| 30 | 729 | 177 (105–531) | 0,85 (0,67–0,94) | 173 (101–527) | 0,27 (0,13–0,96) | 0,16 (0,05–0,35) | 1,14 (1,01–2,24) | 0,25 (0,05–1,54) | 0,37 (0,33–0,69) | 0,07 (0,00–0,17) | 104 (99–154) |
| 60 | 729 | 128 (57–464) | 0,62 (0,37–0,82) | 116 (53–448) | 0,18 (0,06–0,83) | 0,44 (0,19–0,67) | 0,97 (0,66–1,95) | 0,19 (0,03–1,54) | 0,32 (0,22–0,61) | 0,20 (0,00–0,45) | 97 (83–141) |
| 120 | 648 | 104 (50–398) | 0,50 (0,28–0,74) | 96 (47–343) | 0,14 (0,06–0,62) | 0,54 (0,32–0,76) | 0,76 (0,37–1,26) | 0,18 (0,02–1,06) | 0,25 (0,12–0,40) | 0,38 (0,01–0,69) | 87 (56–110) |

«Retenido» es el cristaloide que sigue en la circulación (estado sanguíneo); «efecto neto en C» lo compara con el mismo sangrado sin cristaloide, y es menor porque mientras la circulación está sobre la llegada el relleno espera.

### A.4 Relleno plasmático (P2I-2U-9)

**gi_bleed_57m, pérdida aguda sintética de 200 mL-eq en 10 min (no es una tasa GI)** — 81 combinaciones (meta del relleno (fracción de lo perdido), τ del relleno (min), capacidad del relleno (mL-eq), B0 (mL-eq)).

| Minuto | relleno (mL-eq) | fracción de lo perdido repuesta | dilución de Hb por el relleno | C (mL-eq) | meta alcanzada | la capacidad limita |
|---|---|---|---|---|---|---|
| 30 | 18 (5–50) | 0,09 (0,02–0,25) | 0,032 (0,007–0,117) | -182 (-195–-150) | 0 % | 11 % |
| 60 | 36 (10–89) | 0,18 (0,05–0,45) | 0,064 (0,014–0,207) | -164 (-190–-111) | 0 % | 11 % |
| 120 | 61 (19–128) | 0,31 (0,09–0,64) | 0,107 (0,026–0,292) | -139 (-181–-72) | 0 % | 11 % |
| 240 | 86 (31–147) | 0,43 (0,16–0,73) | 0,148 (0,043–0,334) | -114 (-169–-53) | 0 % | 11 % |

**gi_bleed_57m, sangrado GI de referencia detenido por completo a los 60 min** — 81 combinaciones (meta del relleno (fracción de lo perdido), τ del relleno (min), capacidad del relleno (mL-eq), B0 (mL-eq)).

| Minuto | relleno (mL-eq) | fracción de lo perdido repuesta | dilución de Hb por el relleno | C (mL-eq) | meta alcanzada | la capacidad limita |
|---|---|---|---|---|---|---|
| 30 | 4 (1–12) | 0,06 (0,01–0,15) | 0,007 (0,001–0,026) | -71 (-74–-63) | 0 % | 0 % |
| 60 | 16 (4–41) | 0,11 (0,03–0,28) | 0,027 (0,006–0,093) | -132 (-143–-107) | 0 % | 11 % |
| 120 | 39 (11–85) | 0,26 (0,08–0,58) | 0,066 (0,016–0,192) | -109 (-136–-63) | 0 % | 11 % |
| 240 | 61 (21–107) | 0,41 (0,15–0,73) | 0,104 (0,029–0,241) | -87 (-126–-40) | 0 % | 11 % |

Relleno después de la hemostasia (minutos 60–240): 45 (17–68) mL-eq; en el modelo actual el relleno sigue mientras quede déficit y distancia a la meta.

**gi_bleed_72f, pérdida aguda sintética de 200 mL-eq en 10 min (no es una tasa GI)** — 81 combinaciones (meta del relleno (fracción de lo perdido), τ del relleno (min), capacidad del relleno (mL-eq), B0 (mL-eq)).

| Minuto | relleno (mL-eq) | fracción de lo perdido repuesta | dilución de Hb por el relleno | C (mL-eq) | meta alcanzada | la capacidad limita |
|---|---|---|---|---|---|---|
| 30 | 18 (5–50) | 0,09 (0,02–0,25) | 0,031 (0,006–0,112) | -182 (-195–-150) | 0 % | 11 % |
| 60 | 36 (10–89) | 0,18 (0,05–0,45) | 0,061 (0,013–0,198) | -164 (-190–-111) | 0 % | 11 % |
| 120 | 61 (19–128) | 0,31 (0,09–0,64) | 0,102 (0,025–0,279) | -139 (-181–-72) | 0 % | 11 % |
| 240 | 86 (31–147) | 0,43 (0,16–0,73) | 0,141 (0,041–0,319) | -114 (-169–-53) | 0 % | 11 % |

**gi_bleed_72f, sangrado GI de referencia detenido por completo a los 60 min** — 81 combinaciones (meta del relleno (fracción de lo perdido), τ del relleno (min), capacidad del relleno (mL-eq), B0 (mL-eq)).

| Minuto | relleno (mL-eq) | fracción de lo perdido repuesta | dilución de Hb por el relleno | C (mL-eq) | meta alcanzada | la capacidad limita |
|---|---|---|---|---|---|---|
| 30 | 4 (1–12) | 0,06 (0,01–0,15) | 0,007 (0,001–0,025) | -71 (-74–-63) | 0 % | 0 % |
| 60 | 16 (4–41) | 0,11 (0,03–0,28) | 0,026 (0,006–0,089) | -132 (-143–-107) | 0 % | 11 % |
| 120 | 39 (11–85) | 0,26 (0,08–0,58) | 0,063 (0,015–0,184) | -109 (-136–-63) | 0 % | 11 % |
| 240 | 61 (21–107) | 0,41 (0,15–0,73) | 0,099 (0,028–0,230) | -87 (-126–-40) | 0 % | 11 % |

Relleno después de la hemostasia (minutos 60–240): 45 (17–68) mL-eq; en el modelo actual el relleno sigue mientras quede déficit y distancia a la meta.

### A.5 Identificabilidad (P2I-2U-11)

Efecto de cada parámetro sobre cada ancla, variándolo solo en su rango sintético (el resto en la referencia), como fracción del mayor efecto sobre esa ancla (máximo de los dos casos). Criterio de la sonda, no clínico: bien acotable si es el mayor motor de un ancla y ningún otro llega a 0,50 de su efecto; parcialmente si llega a 0,25 en alguna; mal identificado si no.

| Ancla | tasa de sangrado (mL-eq/min) | B0 (mL-eq) | λ/κ (mL-eq) | posición de precarga de llegada | meta del relleno (fracción de lo perdido) | τ del relleno (min) | capacidad del relleno (mL-eq) | Hb de la unidad de GR (g/dL) | volumen de la unidad (mL-eq) | retención intravascular del cristaloide | τ de redistribución del cristaloide (min) | fracción transitoria del cristaloide | ρ (reserva de extracción) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sin tratar: cambio de Hb a 120′ | 1,00 | 0,37 | 0,00 | 0,00 | 0,65 | 0,63 | 0,09 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| sin tratar: gasto a 60′ | 1,00 | 0,00 | 0,53 | 0,95 | 0,07 | 0,09 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| sin tratar: gasto a 120′ | 1,00 | 0,00 | 0,77 | 0,84 | 0,21 | 0,20 | 0,03 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| sin tratar: déficit efectivo a 120′ | 1,00 | 0,01 | 0,77 | 0,82 | 0,20 | 0,19 | 0,03 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| 1 U: ΔHb | 0,00 | 1,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,60 | 0,63 | 0,00 | 0,00 | 0,00 | 0,00 |
| 1 U: Δgasto | 0,00 | 0,00 | 0,43 | 1,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,17 | 0,00 | 0,00 | 0,00 | 0,00 |
| 2.ª U: Δgasto / Δgasto de la 1.ª | 0,00 | 0,00 | 1,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,39 | 0,00 | 0,00 | 0,00 | 0,00 |
| 1 L: efecto pico en C | 0,02 | 0,00 | 0,00 | 0,00 | 0,01 | 0,02 | 0,00 | 0,00 | 0,00 | 1,00 | 0,16 | 0,10 | 0,00 |
| 1 L: Δgasto al terminar (20′) | 0,04 | 0,00 | 0,51 | 1,00 | 0,01 | 0,02 | 0,00 | 0,00 | 0,00 | 0,76 | 0,13 | 0,08 | 0,00 |
| 1 L: cristaloide retenido a 60′ | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 1,00 | 0,33 | 0,45 | 0,00 |
| 1 L: retenido / pico a 60′ | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,46 | 1,00 | 0,00 |
| 2 L: dilución pico | 0,00 | 0,40 | 0,00 | 0,00 | 0,01 | 0,01 | 0,00 | 0,00 | 0,00 | 1,00 | 0,17 | 0,10 | 0,00 |
| relleno: fracción repuesta a 120′ | 0,00 | 0,00 | 0,00 | 0,00 | 1,00 | 0,77 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| relleno: dilución a 120′ | 0,00 | 0,56 | 0,00 | 0,00 | 1,00 | 0,77 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |

| Parámetro | Clase | Anclas que mueve (≥ 0,25) |
|---|---|---|
| tasa de sangrado (mL-eq/min) | PARTIALLY_CONSTRAINABLE (parcialmente) | sin tratar: cambio de Hb a 120′; sin tratar: gasto a 60′; sin tratar: gasto a 120′; sin tratar: déficit efectivo a 120′ |
| B0 (mL-eq) | PARTIALLY_CONSTRAINABLE (parcialmente) | sin tratar: cambio de Hb a 120′; 1 U: ΔHb; 2 L: dilución pico; relleno: dilución a 120′ |
| λ/κ (mL-eq) | WELL_CONSTRAINABLE (bien acotable) | sin tratar: gasto a 60′; sin tratar: gasto a 120′; sin tratar: déficit efectivo a 120′; 1 U: Δgasto; 2.ª U: Δgasto / Δgasto de la 1.ª; 1 L: Δgasto al terminar (20′) |
| posición de precarga de llegada | WELL_CONSTRAINABLE (bien acotable) | sin tratar: gasto a 60′; sin tratar: gasto a 120′; sin tratar: déficit efectivo a 120′; 1 U: Δgasto; 1 L: Δgasto al terminar (20′) |
| meta del relleno (fracción de lo perdido) | PARTIALLY_CONSTRAINABLE (parcialmente) | sin tratar: cambio de Hb a 120′; relleno: fracción repuesta a 120′; relleno: dilución a 120′ |
| τ del relleno (min) | PARTIALLY_CONSTRAINABLE (parcialmente) | sin tratar: cambio de Hb a 120′; relleno: fracción repuesta a 120′; relleno: dilución a 120′ |
| capacidad del relleno (mL-eq) | POORLY_IDENTIFIED (mal identificado) | — |
| Hb de la unidad de GR (g/dL) | PARTIALLY_CONSTRAINABLE (parcialmente) | 1 U: ΔHb |
| volumen de la unidad (mL-eq) | PARTIALLY_CONSTRAINABLE (parcialmente) | 1 U: ΔHb; 2.ª U: Δgasto / Δgasto de la 1.ª |
| retención intravascular del cristaloide | WELL_CONSTRAINABLE (bien acotable) | 1 L: efecto pico en C; 1 L: Δgasto al terminar (20′); 1 L: cristaloide retenido a 60′; 2 L: dilución pico |
| τ de redistribución del cristaloide (min) | PARTIALLY_CONSTRAINABLE (parcialmente) | 1 L: cristaloide retenido a 60′; 1 L: retenido / pico a 60′ |
| fracción transitoria del cristaloide | WELL_CONSTRAINABLE (bien acotable) | 1 L: cristaloide retenido a 60′; 1 L: retenido / pico a 60′ |
| ρ (reserva de extracción) | NON_IDENTIFIABLE_SEPARATELY (sólo en combinación) | con la banda de entrega de llegada re-anclada, sólo ρ × arrival_delivery_ratio llega a D y al déficit (P2I-2P); sola, sólo cambia la etiqueta adecuada / compensada |
| κ (por separado) | NON_IDENTIFIABLE_SEPARATELY (sólo en combinación) | sólo λ/κ llega al gasto, la presión y la entrega (V entra sólo como V/λ); la Hb nunca lee κ |
| λ (por separado) | NON_IDENTIFIABLE_SEPARATELY (sólo en combinación) | lo mismo: λ sólo es identificable como λ/κ |

Comprobaciones estructurales: con (κ, λ) y (2κ, 2λ) el mayor cambio de cualquier ancla es gi_bleed_57m 0,000000000000, gi_bleed_72f 0,000000000000; con ρ 1 / 2,5 / 3 y la banda re-anclada, gi_bleed_57m 0,000000000000, gi_bleed_72f 0,000000000000.

Combinaciones que mueven cada ancla (en orden de efecto): sin tratar: cambio de Hb a 120′: tasa de sangrado (mL-eq/min), meta del relleno (fracción de lo perdido), τ del relleno (min), B0 (mL-eq); sin tratar: gasto a 60′: tasa de sangrado (mL-eq/min), posición de precarga de llegada, λ/κ (mL-eq); sin tratar: gasto a 120′: tasa de sangrado (mL-eq/min), posición de precarga de llegada, λ/κ (mL-eq); sin tratar: déficit efectivo a 120′: tasa de sangrado (mL-eq/min), posición de precarga de llegada, λ/κ (mL-eq); 1 U: ΔHb: B0 (mL-eq), volumen de la unidad (mL-eq), Hb de la unidad de GR (g/dL); 1 U: Δgasto: posición de precarga de llegada, λ/κ (mL-eq); 2.ª U: Δgasto / Δgasto de la 1.ª: λ/κ (mL-eq), volumen de la unidad (mL-eq); 1 L: efecto pico en C: retención intravascular del cristaloide; 1 L: Δgasto al terminar (20′): posición de precarga de llegada, retención intravascular del cristaloide, λ/κ (mL-eq); 1 L: cristaloide retenido a 60′: retención intravascular del cristaloide, fracción transitoria del cristaloide, τ de redistribución del cristaloide (min); 1 L: retenido / pico a 60′: fracción transitoria del cristaloide, τ de redistribución del cristaloide (min); 2 L: dilución pico: retención intravascular del cristaloide, B0 (mL-eq); relleno: fracción repuesta a 120′: meta del relleno (fracción de lo perdido), τ del relleno (min); relleno: dilución a 120′: meta del relleno (fracción de lo perdido), τ del relleno (min), B0 (mL-eq).

### A.6 Hoja de trabajo FD-BLD (P2I-2U-6, 8 y 9)

En esta hoja cada cifra es la mediana (mínimo–máximo) de la cuadrícula de su superficie, no la referencia; las de A.1 y A.3 resumen sólo las corridas que siguen perfundiendo (n en sus tablas), salvo donde se dice. «Qué acotaría» son los parámetros internos que mueven las anclas de la evidencia mostrada (A.5), en orden de efecto; ninguno se decide por separado.

**Estado (P2I-2V, 2026-10-27).** La docencia aprobó FD-BLD-01 a 09 y las anclas sin tratar A y B. FACULTY_APPROVED quiere decir: conducta clínica / envolvente aprobada; los parámetros ocultos del modelo siguen sin aprobar. Las envolventes son envolventes clínicas, no objetivos exactos. Cómo se leen y qué región dejan: `docs/revision/P2I2V_ANCLAS_APROBADAS_FILTRO.md`. **P2I-2V-R:** A pasa a v2, sin caída mínima de Hb; FD-BLD-03 queda FACULTY_APPROVED_QUALITATIVE / NOT_YET_HARD_FILTER (se informa, no filtra): `docs/revision/P2I2VR_RESTRICCIONES_REVISADAS_FILTRO.md`.

| ID | Pregunta | Lo que muestra el modelo (sólo modelo) | Qué acotaría | Selección docente | Estado |
|---|---|---|---|---|---|
| FD-BLD-01 | ¿Qué aumento de Hb por una unidad debería ser aceptable en estos adultos modelados? | gi_bleed_57m: ΔHb 0,91 (0,54–1,60) g/dL; gi_bleed_72f: ΔHb 0,93 (0,55–1,63) g/dL | B0 (mL-eq), volumen de la unidad (mL-eq), Hb de la unidad de GR (g/dL) | ≈ 0,7–1,2 g/dL por unidad; no es una regla fija de +1 g/dL; tras mezcla razonable y sin una pérdida simultánea abrumadora | FACULTY_APPROVED |
| FD-BLD-02 | ¿Cuánto debería poder mejorar el gasto efectivo una unidad cuando el paciente responde a la precarga? | gi_bleed_57m: Δgasto 0,56 (0,15–1,77) (posición inf. 1,21 (0,61–1,77)); gi_bleed_72f: Δgasto 0,36 (0,10–1,03) (posición inf. 0,71 (0,36–1,03)) | posición de precarga de llegada, λ/κ (mL-eq) | con respuesta a la precarga y llenado bajo: gi_bleed_57m ≈ 15–40 %; gi_bleed_72f ≈ 10–30 % de aumento del gasto efectivo; envolventes de techo / conducta, no respuestas obligatorias | FACULTY_APPROVED |
| FD-BLD-03 | ¿Una unidad sola debería poder normalizar el gasto en alguno de los dos casos GI? | gi_bleed_57m: llega a la referencia euvolémica inferior en 33 % de la cuadrícula; gi_bleed_72f: llega a la referencia euvolémica inferior en 56 % de la cuadrícula | posición de precarga de llegada, λ/κ (mL-eq) | una unidad no debe normalizar de forma fiable el gasto efectivo en ninguno de los dos casos; 72f puede acercarse a un estado adecuado si responde a la precarga; 57m no pasa de fisiología hemorrágica grave a gasto normalizado / euvolémico con una sola unidad. Segunda unidad: beneficio ≤ el de la primera (la razón ~0,70 no se aprueba) | FACULTY_APPROVED_QUALITATIVE / NOT_YET_HARD_FILTER |
| FD-BLD-04 | ¿Qué tamaño debería tener la respuesta hemodinámica transitoria a 1 L de cristaloide? | gi_bleed_57m: Δgasto al terminar 1 L 0,31 (0,05–1,61) (posición de llegada inf. 0,68 (0,21–1,61), medio 0,31 (0,10–0,75), sup. 0,17 (0,05–0,40)); efecto pico en C 164 (77–279) mL-eq; gi_bleed_72f: Δgasto al terminar 1 L 0,20 (0,03–0,94) (posición de llegada inf. 0,40 (0,12–0,94), medio 0,21 (0,06–0,49), sup. 0,11 (0,03–0,27)); efecto pico en C 164 (77–279) mL-eq | posición de precarga de llegada, retención intravascular del cristaloide, λ/κ (mL-eq) | ≈ 15–30 % del volumen infundido (≈ 150–300 mL por litro); envolvente clínica, no una conversión exacta | FACULTY_APPROVED |
| FD-BLD-05 | ¿Cuánto efecto intravascular efectivo del cristaloide debería quedar a los 30 y 60 min? | gi_bleed_57m: retenido a 30′ 142 (52–266) y a 60′ 103 (29–232) mL-eq; retenido / pico a 30′ 0,87 (0,67–0,94), a 60′ 0,62 (0,37–0,82); gi_bleed_72f: retenido a 30′ 142 (52–266) y a 60′ 103 (29–232) mL-eq; retenido / pico a 30′ 0,87 (0,67–0,94), a 60′ 0,62 (0,37–0,82) | retención intravascular del cristaloide, fracción transitoria del cristaloide, τ de redistribución del cristaloide (min) | ≈ 15–25 % a los ~30 min; ≈ 10–20 % a los ~60 min; ≈ 5–15 % a los ~120 min | FACULTY_APPROVED |
| FD-BLD-06 | ¿Cuánta dilución de la Hb debería ser aceptable con 1–2 L de cristaloide? | gi_bleed_57m: dilución pico 1 L 0,26 (0,10–0,57), 2 L 0,50 (0,20–1,06) g/dL; gi_bleed_72f: dilución pico 1 L 0,25 (0,10–0,55), 2 L 0,48 (0,19–1,01) g/dL | retención intravascular del cristaloide, B0 (mL-eq) | 1 L: descenso transitorio de ≈ 0,2–0,5 g/dL; 2 L: descenso transitorio de ≈ 0,4–0,8 g/dL; con reversión parcial | FACULTY_APPROVED |
| FD-BLD-07 | ¿Qué fracción de un déficit agudo de volumen circulante debería poder reponer el relleno endógeno en ~1–2 h? | gi_bleed_57m: repuesto a 60′ 0,15 (0,05–0,45), a 120′ 0,28 (0,09–0,64); gi_bleed_72f: repuesto a 60′ 0,15 (0,05–0,45), a 120′ 0,28 (0,09–0,64) | meta del relleno (fracción de lo perdido), τ del relleno (min) | ≈ 10–25 % a los ~60 min; ≈ 20–45 % a los ~120 min; ≈ 30–60 % a los ~240 min | FACULTY_APPROVED |
| FD-BLD-08 | ¿El relleno debería seguir activo después de la hemostasia mientras quede déficit? | gi_bleed_57m: relleno tras la hemostasia 44 (17–68) mL-eq (hoy sigue mientras quede déficit); gi_bleed_72f: relleno tras la hemostasia 44 (17–68) mL-eq (hoy sigue mientras quede déficit) | meta del relleno (fracción de lo perdido), τ del relleno (min) | sí: sigue después de la hemostasia mientras quede déficit circulante y capacidad de relleno | FACULTY_APPROVED |
| FD-BLD-09 | ¿Qué efecto cualitativo sobre la Hb debería producir el relleno en 1–2 h? | gi_bleed_57m: dilución por relleno a 120′ 0,09 (0,03–0,29) g/dL (baja la Hb; no crea GR); gi_bleed_72f: dilución por relleno a 120′ 0,09 (0,03–0,28) g/dL (baja la Hb; no crea GR) | meta del relleno (fracción de lo perdido), τ del relleno (min), B0 (mL-eq) | aumenta el volumen plasmático / circulante, no la masa de GR, y diluye la Hb progresivamente; ningún decremento fijo en g/dL: la magnitud sale del estado sanguíneo compartido | FACULTY_APPROVED |

| Ancla sin tratar | Pregunta | Lo que muestra el modelo | Qué acotaría | Selección docente | Estado |
|---|---|---|---|---|---|
| A | cambio de Hb aceptable a los 60 / 120 min | gi_bleed_57m: ΔHb a 60′ -0,02 (-0,11–-0,01), a 120′ -0,07 (-0,40–-0,02); gi_bleed_72f: ΔHb a 60′ -0,03 (-0,11–-0,01), a 120′ -0,07 (-0,38–-0,02) | tasa de sangrado (mL-eq/min), meta del relleno (fracción de lo perdido), τ del relleno (min), B0 (mL-eq) | v2 (P2I-2V-R), sin caída mínima: caída de Hb gi_bleed_57m 0,0–0,5 g/dL a los 60 min, 0,0–0,9 g/dL a los 120 min; gi_bleed_72f 0,0–0,4 g/dL a los 60 min, 0,0–0,7 g/dL a los 120 min; con hemorragia en curso y sin fuente de GR, la Hb no sube por la hemorragia misma | FACULTY_APPROVED v2 |
| B | deterioro del gasto aceptable a los 60 / 120 min | gi_bleed_57m: gasto a 60′ 0,73 (0,03–0,96) (n = 213), a 120′ 0,62 (0,06–0,92) (n = 165 de 243 que siguen perfundiendo); con las detenidas en 0: 60′ 0,66 (0,00–0,96), 120′ 0,37 (0,00–0,92); gi_bleed_72f: gasto a 60′ 0,80 (0,05–0,97) (n = 234), a 120′ 0,69 (0,01–0,95) (n = 201 de 243 que siguen perfundiendo); con las detenidas en 0: 60′ 0,79 (0,00–0,97), 120′ 0,59 (0,00–0,95) | tasa de sangrado (mL-eq/min), posición de precarga de llegada, λ/κ (mL-eq) | gasto efectivo relativo a la llegada: gi_bleed_57m 0,85–0,95 a los 30 min, 0,70–0,85 a los 60 min, 0,45–0,65 a los 120 min; gi_bleed_72f 0,90–0,98 a los 30 min, 0,80–0,92 a los 60 min, 0,60–0,78 a los 120 min | FACULTY_APPROVED |
| C | transición aceptable a disponibilidad de O2 compensada / crítica | gi_bleed_57m: déficit a 120′ 0,48 (0,22–0,95) (n = 165 que siguen perfundiendo); con las detenidas en su déficit al detenerse: 0,69 (0,22–1,00); la llegada ya está en déficit crítico con la banda de entrega en su punto medio; gi_bleed_72f: déficit a 120′ 0,42 (0,20–0,99) (n = 201 que siguen perfundiendo); con las detenidas en su déficit al detenerse: 0,50 (0,20–1,00); la llegada ya está en déficit crítico con la banda de entrega en su punto medio | tasa de sangrado (mL-eq/min), posición de precarga de llegada, λ/κ (mL-eq) |  | ABIERTA |
| D | si cada caso debe seguir perfundiendo a los 120 min sin tratamiento | gi_bleed_57m: 78 de 243 se detienen antes de 120′; gi_bleed_72f: 42 de 243 se detienen antes de 120′ | tasa de sangrado (mL-eq/min), posición de precarga de llegada, λ/κ (mL-eq) |  | ABIERTA |

C y D no se decidieron. D queda implícita en la envolvente de B a los 120 min (un gasto de 0,45–0,65 o 0,60–0,78 exige seguir perfundiendo), pero no se decidió por separado.

### A.7 Autoridad de la tasa de sangrado (P2I-2U-10)

`FAMILY_ALLOWED_RANGE` no está entre las tres que pide el encargo; se añade porque P2G la lista para `blood_loss_ml_per_min` (FD-50). En P2I-2U no se adoptó ninguna. **P2I-2V (2026-10-27):** la docencia aprobó la categoría `CASE_OVERRIDES_FAMILY_DEFAULT` para esta tasa, sin aprobar ningún valor numérico.

| Política | Significado | Autoría | Consecuencia clínica | Riesgo | Puerta de migración |
|---|---|---|---|---|---|
| `CASE_OVERRIDES_FAMILY_DEFAULT` (la que el encargo pide evaluar como preferida; no adoptada) | el caso puede declarar una tasa o gravedad verificada; el valor de familia GI aprobado es sólo respaldo | opcional por caso: un campo de autoría nuevo (tasa o grado de gravedad) y un mapeo registrado de gravedad a tasa; el valor de familia se aprueba una vez | los casos pueden diferir (sangrado rápido o lento) donde su autor lo dice; los que no declaran sangran al valor de familia | el valor de familia gobierna en silencio cada caso sin declaración, así que su valor pesa tanto como el de cualquier caso; el mapeo gravedad → tasa es a su vez una decisión docente | migrable con el valor de familia aprobado; una declaración del caso necesita procedencia de confianza |
| `CASE_REQUIRED` | cada caso GI debe declarar su propia tasa verificada; sin respaldo | un campo nuevo obligatorio en cada caso GI antes de migrar | la hemorragia de cada caso es explícita; ningún caso hereda una tasa para la que no se escribió | hoy ningún caso del banco declara una tasa (melena desde ayer; tres días y otro episodio hoy): los dos quedan bloqueados hasta que se escriba | falla cerrado para todo caso sin el campo |
| `FAMILY_ALLOWED_RANGE` | la familia aprueba un rango como envoltura de autorización, no como fuente del valor: la tasa es la verificada del caso y debe caer dentro | el mismo campo nuevo por caso que `CASE_OVERRIDES_FAMILY_DEFAULT`, más los límites del rango | el sangrado rápido y el lento pueden diferir dentro de límites aprobados | sin tasa del caso sólo corre con un respaldo del rango aprobado explícitamente; si no, cierra, como `CASE_REQUIRED` hoy para los dos casos del banco; los dos límites son decisiones docentes | falla cerrado sin tasa del caso verificada, salvo que la aprobación defina un respaldo |
| `FAMILY_FIXED_VALUE` | una tasa de familia GI aprobada para todos los casos; ningún caso la cambia | ninguna por caso | todo paciente GI sangra igual; no se distingue un sangrado rápido de uno lento | una constante GI se vuelve verdad universal de la familia (la docencia ya rechazó tratar así el literal heredado) | migrable con el valor aprobado |
<!-- /generado:anclas-hemorragia -->

## 7. Qué no hace

- No responde ninguna FD-BLD ni las anclas A–D: las selecciones quedan en blanco.
- No aprueba ningún valor: todos siguen CANDIDATE / PROVISIONAL / SYNTHETIC.
- No calibra la hemorragia, la presión ni la FC; no refiltra el lactato.
- No migra GI ni otra familia, no puebla los registros de autoridad y no integra nada en tiempo de ejecución.
