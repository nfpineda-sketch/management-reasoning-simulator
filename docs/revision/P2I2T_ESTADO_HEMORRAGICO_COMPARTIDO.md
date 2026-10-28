# P2I-2T · Estado hemorrágico compartido

Este paquete corrige la estructura del núcleo en sombra:
- funciona sólo en sombra, sin integración en tiempo de ejecución ni cambio en lo que ve el residente;
- no migra GI ni otra familia;
- no vuelve a filtrar el lactato (P2I-2R sigue PENDIENTE DE REFILTRADO);
- no calibra la presión ni la FC, no activa el colapso canónico y no aprueba ningún número.

**Decisión docente que implementa (2026-10-27).** Dos derivas independientes (`V -= fijo`, `Hb -= fijo`) no son
aceptables. Se implementa el estado hemorrágico compartido mínimo, sin un modelo de compartimentos de alta fidelidad:
- una sola fuente hemorrágica quita volumen circulante y masa de glóbulos rojos;
- la Hb resulta de la masa de glóbulos rojos y del volumen circulante, que mueven el cristaloide, los glóbulos rojos
  transfundidos y el relleno plasmático.

**Sustituido en parte por P2I-2U (2026-10-27).** Este documento registra P2I-2T tal como se cerró.
- F5 (§7) y la sonda de banda pendiente de §8 se resolvieron en P2I-2U: la sonda es ahora un flujo sintético de sangre
  total a través del estado compartido.
- Los valores provisionales de §8 (B0, κ con λ, el relleno, la unidad de GR, la retención del cristaloide) ya no se
  deciden por separado: los acotan las anclas de paciente FD-BLD-01 a 09.
- FD-23 quedó RETIRED — INVALIDATED BY SHARED HAEMORRHAGE STATE.
- Fuente: `docs/revision/P2I2U_ANCLAS_HEMORRAGIA_COMPARTIDA.md`.

**Valores.** Todos los valores nuevos son PROVISIONALES (SYNTHETIC/CANDIDATE, TBD) y ninguno está aprobado. Las cifras
de este documento salen del perfil canónico con esos valores. Los volúmenes son mL-eq de volumen circulante normalizado,
no litros medidos.

## 1. Diseño (P2I-2T-1 a P2I-2T-8)

### 1.1 Estado tipado (`state.BloodState`, campo `CoreState.blood`)

Siete acumulados desde la llegada, todos no negativos y que nunca bajan (`BLOOD_FIELDS`):

| Campo | Qué acumula |
|---|---|
| `shed_ml` | sangre total perdida, de toda fuente hemorrágica |
| `shed_red_cells` | contenido de glóbulos rojos que salió con ella, con la composición que tenía al salir |
| `crystalloid_in_ml` / `crystalloid_out_ml` | cristaloide que entró a la circulación (la parte intravascular de cada orden) y el que se redistribuyó fuera |
| `transfused_ml` / `transfused_red_cells` | volumen y contenido que aportaron los glóbulos rojos transfundidos |
| `refill_ml` | plasma que volvió del intersticio (sin glóbulos rojos) |

De ellos se derivan:
- **C**, la desviación del volumen circulante: −perdido + cristaloide neto + transfundido + relleno;
- el **contenido de glóbulos rojos**, en unidades del contenido de llegada (llegada = 1): 1 − perdido + transfundido;
- la **desviación plasmática**, sólo para informes: C menos el cambio de volumen eritrocitario, leído con una
  concentración corpuscular media de 33 g/dL (`derived.RED_CELL_HB_G_DL`). Ningún mecanismo la lee.

La normalización es el volumen circulante de llegada `arrival_circulating_volume_ml` (B0, provisional 4000 mL-eq).

Dos campos más (`BLOOD_OFFSETS`: `outside_v`, `outside_hb`) contabilizan lo que movieron V y Hb las sondas declaradas y
los límites, fuera del estado. Son 0 en toda corrida sin sondas ni límites.

El estado se serializa en el JSON canónico del estado, entra en su resumen, se reproduce y se copia en profundidad.
Un estado posterior a la llegada sin `blood` se rechaza.

### 1.2 Flujos y registro

- **Contribuyentes.** Ningún contribuyente escribe V ni Hb. Cada uno declara flujos (`provenance.BloodFlow`) con un
  proceso y un volumen:
  - `whole_blood_loss` (módulo de enfermedad);
  - `crystalloid_in` / `crystalloid_out` (orden);
  - `red_cell_transfusion` (orden, con la Hb de su unidad).
- **Relleno.** `plasma_refill` es un acoplamiento propio del núcleo; ningún contribuyente puede declararlo.
- **Una sonda declarada** (`scripted_event`) es la única fuente que todavía puede mover V o Hb directamente.
- **Integrador.** Lee la composición al comienzo del minuto y resuelve los glóbulos rojos de cada flujo:
  - la sangre total sale con la composición actual;
  - la unidad entra con la suya;
  - el cristaloide y el relleno no traen ninguno.
- **Registro.** Cada flujo aplicado queda como `BloodChange` en `MinuteRecord.blood`.

### 1.3 Hb y V

- **Hb = Hb de llegada × contenido × B0 / (B0 + C).** La pérdida aguda de sangre total no la cambia de inmediato; el
  relleno y el cristaloide la diluyen; los glóbulos rojos la suben.
  - Es el acoplamiento `core_coupling:blood_composition`, modulado por las fuentes que movieron el estado ese minuto.
  - No queda ningún `Hb += 0,85` ni `Hb -= 0,009`.
- **V = κ × C** («Effective circulating volume / preload coordinate (V)», `CHANNEL_DEFINITIONS`), con κ =
  `volume_preload_kappa`, provisional 1.
  - Es la única conversión: cada cambio mueve V una vez, en κ × su volumen, atribuido a su fuente.
  - V sigue siendo una coordenada interna de precarga, no un volumen de sangre medido.
- **Identificabilidad de κ y λ.**
  - El gasto lee V sólo como V/λ, con λ la escala de la curva. Entonces sólo κ/λ es identificable desde la
    hemodinámica: (κ, λ) y (2κ, 2λ) dan el mismo paciente (§4.2).
  - La Hb lee C/B0 y nunca κ.
  - No se aprueba λ por separado; κ = 1 sólo fija que V se cuente en mL-eq de volumen circulante.
- **Curva de precarga:** la saturante se mantiene; no apareció ninguna contradicción nueva.

### 1.4 Procesos

- **Sangrado (P2I-2T-2).** El módulo GI declara un único flujo de sangre total, `blood_loss_ml_per_min` × fracción.
  - El IBP (0,8) y la hemostasia (0,1) actúan sobre ese flujo y figuran como moduladores.
  - El campo `hb_loss_g_dl_per_min` desapareció y `volume_loss_ml_per_min` pasó a `blood_loss_ml_per_min`.
- **Relleno plasmático (P2I-2T-4).** Tiende, en primer orden, a una meta:
  - la meta es `plasma_refill_target_share` × lo perdido (provisional 0,5);
  - con un tope de `plasma_refill_capacity_ml` (provisional 1000) y τ `plasma_refill_tau_min` (provisional 120 min);
  - sólo restaura un déficit: actúa mientras la circulación está por debajo de la llegada (C < 0), y el relleno de un
    minuto nunca supera ese déficit. Con líquidos o GR por encima de la llegada, espera;
  - es gradual, no pasa su meta, no se revierte, no trae glóbulos rojos (diluye) y sigue tras detenerse el sangrado
    mientras quede déficit;
  - el modelo mínimo no modela cuánto frenan los líquidos al relleno por debajo de la llegada.
- **Cristaloide (P2I-2T-5).** Usa la cinética de fuga existente (12,5 % intravascular, 60 % transitorio, τ 30 min),
  ahora como flujos de entrada y salida.
  - Diluye sin glóbulos rojos.
  - La dilución se revierte en la medida en que el volumen se va: queda la parte retenida.
- **Glóbulos rojos (P2I-2T-6).** Una sola representación de la unidad: `volume_ml_per_unit` (300, el literal) a
  `unit_hb_g_dl`.
  - `unit_hb_g_dl` vale provisionalmente 20 g/dL: una unidad típica, con hematocrito de alrededor de 0,6. No se ajustó al
    0,85 heredado.
  - La subida de la Hb depende de la circulación a la que entra la unidad.

### 1.5 Llegada (P2I-2T-10) y autoridad de la tasa (P2I-2T-9)

- **Llegada.** No se infiere ninguna pérdida previa desde la Hb.
  - El estado sanguíneo de llegada es cero: la Hb de llegada fija la composición, con contenido 1 en B0.
  - La posición en la curva y D / lactato siguen siendo los declarados.
  - El estado compartido gobierna sólo la evolución desde la llegada.
- **Tasa del sangrado.** La política probable es CASE_OVERRIDES_FAMILY_DEFAULT: la declara el caso, con un respaldo de
  familia.
  - No está aprobada, y `AUTHORITY_POLICIES` sigue vacío.
  - Un literal GI no es una verdad universal. Es FD-22.

## 2. Conservación y contabilidad (P2I-2T-12)

El integrador comprueba cada minuto, y falla cerrado si no se cumple (`integration._check_blood`):
- **cada campo del estado** cambia exactamente en los cambios de su proceso, y ninguno baja;
- **V:** fuera de las sondas y de los límites, los deltas de V suman κ × el volumen que esas fuentes movieron. Ningún
  sangrado, líquido ni relleno mueve V fuera del estado, ni lo mueve dos veces;
- **Hb:** fuera de las sondas y de los límites, sólo la composición mueve la Hb, y en exactamente el cambio de
  contenido / volumen.

Además:
- **Escrituras directas.** Un módulo, una orden o un proceso logístico que escriba V o Hb directamente se rechaza
  (`ProvenanceError`).
- **Composición.** Cada registro debe llevar los glóbulos rojos que da la composición: la Hb actual para la sangre
  total, la de la unidad para una transfusión, ninguna para el cristaloide y el relleno.
- **Relleno.** Debe ser el que da el estado al comienzo del minuto.
- **Sondas y límites.** Lo que movieron fuera del estado queda contabilizado (`outside_v`, `outside_hb`). Entonces
  V = κ × C + `outside_v` y Hb = composición + `outside_hb` se comprueban al entrar y al salir de cada minuto y al
  comenzar una corrida (`check_blood_identity`).
- **Estado inexplicable.** Un estado armado o editado a mano, o reanudado con otro κ o con otro B0, se rechaza.
- **Guardas de V y Hb.** Son guardas, no fisiología. Si el estado sanguíneo las alcanza, la corrida se detiene
  (`UnresolvedBoundary`) en vez de separar el canal del estado. La de V se expresa en volumen circulante (±3000 mL-eq,
  aplicada a V escalada por κ), así que no separa κ de λ.
- **Traza de Contracts v2.** Lleva el estado sanguíneo de llegada y final (`core_blood_state`, nunca autoritativo),
  además de los cambios de cada minuto.

Las pruebas (`test_clinical_core_shared_haemorrhage.py`) fijan, con una corrida que ejerce todos los procesos:
- los glóbulos rojos sólo cambian con la pérdida o la transfusión;
- el volumen sólo cambia con el sangrado, los líquidos, el relleno o la redistribución;
- la Hb no cambia sin un cambio de contenido o de volumen que la explique, y coincide cada minuto con la de la
  composición;
- V = κ × C cada minuto, con κ 0,5, 1 y 2, y con sondas que mueven V o Hb directamente (contabilizadas);
- detener el sangrado detiene las pérdidas nuevas;
- el relleno y el salino no crean glóbulos rojos;
- los glóbulos rojos no son cristaloide;
- no queda ninguna deriva heredada activa en paralelo;
- la persistencia y la reanudación se conservan, y un estado inexplicable se rechaza;
- el relleno nunca lleva la circulación por encima de la llegada;
- una guarda nunca recorta lo que movió el estado sanguíneo.

## 3. Sondas A–K (P2I-2T-11)

Corren con la llegada GI 72f del golden y el perfil canónico (reserva de extracción 1). La tabla de cada sonda está en
§4.1.

| Sonda | Qué muestra |
|---|---|
| A · pérdida aguda de 300 mL, sin relleno | la Hb sigue en 6,40: la pérdida aguda de sangre total no la baja; V −300 y gasto 0,57 |
| B · la misma pérdida, con relleno | la Hb baja despacio por dilución, 6,31 a los 60 min y 6,19 a los 240 min; el relleno devuelve 129 mL-eq y V se recupera hasta −171 |
| C · sangrado GI continuo | 600 mL-eq perdidos en 4 h; la Hb baja a 6,11; el relleno, 170 mL-eq; V −430 y gasto 0,32 |
| D · sangrado detenido a los 120 min | lo perdido se congela en 297,5; el relleno sigue de 55 a 114 mL-eq; la Hb sigue bajando, de 6,31 a 6,21, mientras V se recupera |
| E · 1 L de cristaloide | C llega a +104 al terminar la bolsa y queda en +50; la Hb baja hasta 6,24 y vuelve a 6,32 |
| F · 2 L de cristaloide | C llega a +208 y queda en +100; la Hb baja hasta 6,08 y vuelve a 6,24 |
| G · 1 unidad de GR | la Hb sube de 6,40 a 7,35 (+0,95) y V +300; gasto 1,30, DO2 1,50 |
| H · 2 unidades | la Hb llega a 8,17 y V a +600; gasto 1,51, DO2 1,93 |
| I · 2 unidades con sangrado continuo | la Hb llega a 8,20 a los 60 min y se mantiene: el sangrado sigue (V de +450 a 0 a los 240 min), pero la pérdida de sangre total no cambia la Hb y el relleno espera a que haya déficit |
| J · 2 L de cristaloide con sangrado continuo | a los 240 min, Hb 5,98 frente a 6,11 sin cristaloide, y V −333 frente a −430; el relleno empieza cuando la circulación baja de la llegada |
| K · hemostasia a los 120 min (residual 10 %) | el sangrado cae a 0,25 mL-eq/min; el relleno lleva V de −243 a −208, y la Hb baja de 6,31 a 6,20 |

**Lectura fisiológica (sin aprobar nada).** Las cuatro observaciones dependen de valores TBD. No se corrigieron hacia
el motor heredado.
- **Caída de la Hb.** Con una sola fuente a 2,5 mL-eq/min, la Hb cae 0,09 g/dL en 2 h; la deriva heredada caía 1,08.
  - P2I-2S ya mostró que la deriva heredada equivale a varias veces la pérdida de V. La tasa del sangrado, B0 y la meta
    del relleno son TBD (FD-22, §5).
- **Cristaloide.** Diluye mucho menos que la deriva heredada (2 L: −0,32 g/dL en el pico, frente a −1,2 permanente)
  porque retiene el 12,5 % intravascular heredado; la retención es TBD.
- **Unidad de GR.** Su efecto en el gasto no cambia (+30 % por unidad en una llegada en 0,5): sigue siendo la razón
  unidad/λ de P2I-2S, pendiente.
- **Relleno.** Recupera parte de V mientras hay déficit, así que la PA cae más despacio que antes sin tratamiento.

## 4. Tablas (generado)

<!-- generado:estado-sanguineo -->
Generado desde las sondas `f1608b49a37d07b4726545764a1d00a9ed890465dd968b811bd13226652d4e7e` (`python -m clinical_core.blood_probes`). Llegada GI `gi_bleed_72f` del golden (anclas canónicas, parámetros de caso sin declarar) y perfil canónico: volumen circulante de llegada 4000 mL-eq, κ 1,0, escala de la curva 833 mL-eq, relleno: meta 50 % de lo perdido, τ 120 min, capacidad 1000 mL-eq; unidad de GR 300 mL-eq a 20 g/dL; reserva de extracción 1 (canónica). **Todos son valores PROVISIONALES (SYNTHETIC/CANDIDATE, TBD); ninguno está aprobado.** Los volúmenes son mL-eq de volumen circulante normalizado, no litros medidos; los GR, en unidades del contenido de llegada (llegada = 1).

### 4.1 Sondas A–K

Columnas: perdido (mL-eq) · GR (contenido) · desviación circulante C · desviación plasmática · relleno · cristaloide neto · GR transfundidos (mL-eq) · Hb (g/dL) · V · gasto relativo · índice de DO2 · estado de extracción · déficit efectivo.

**A · pérdida aguda de 300 mL en 10 min, sin relleno.** Hb mínima 6,40, máxima 6,40; V mínima -300, máxima 0.

| min | perdido | GR | C | plasma | relleno | cristaloide | GR transf. | Hb | V | gasto | DO2 | estado | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 1,000 | 0 | 0 | 0 | 0 | 0 | 6,40 | 0 | 1,00 | 1,00 | adecuada | 0,000 |
| 10 | 300 | 0,925 | -300 | -242 | 0 | 0 | 0 | 6,40 | -300 | 0,57 | 0,57 | crítica | 0,433 |
| 20 | 300 | 0,925 | -300 | -242 | 0 | 0 | 0 | 6,40 | -300 | 0,57 | 0,57 | crítica | 0,433 |
| 30 | 300 | 0,925 | -300 | -242 | 0 | 0 | 0 | 6,40 | -300 | 0,57 | 0,57 | crítica | 0,433 |
| 60 | 300 | 0,925 | -300 | -242 | 0 | 0 | 0 | 6,40 | -300 | 0,57 | 0,57 | crítica | 0,433 |
| 90 | 300 | 0,925 | -300 | -242 | 0 | 0 | 0 | 6,40 | -300 | 0,57 | 0,57 | crítica | 0,433 |
| 120 | 300 | 0,925 | -300 | -242 | 0 | 0 | 0 | 6,40 | -300 | 0,57 | 0,57 | crítica | 0,433 |
| 180 | 300 | 0,925 | -300 | -242 | 0 | 0 | 0 | 6,40 | -300 | 0,57 | 0,57 | crítica | 0,433 |
| 240 | 300 | 0,925 | -300 | -242 | 0 | 0 | 0 | 6,40 | -300 | 0,57 | 0,57 | crítica | 0,433 |

**B · pérdida aguda de 300 mL en 10 min, con relleno.** Hb mínima 6,18, máxima 6,40; V mínima -295, máxima 0.

| min | perdido | GR | C | plasma | relleno | cristaloide | GR transf. | Hb | V | gasto | DO2 | estado | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 1,000 | 0 | 0 | 0 | 0 | 0 | 6,40 | 0 | 1,00 | 1,00 | adecuada | 0,000 |
| 10 | 300 | 0,925 | -295 | -236 | 5 | 0 | 0 | 6,39 | -295 | 0,58 | 0,58 | crítica | 0,425 |
| 20 | 300 | 0,925 | -283 | -225 | 17 | 0 | 0 | 6,37 | -283 | 0,60 | 0,59 | crítica | 0,407 |
| 30 | 300 | 0,925 | -272 | -214 | 28 | 0 | 0 | 6,35 | -272 | 0,61 | 0,61 | crítica | 0,391 |
| 60 | 300 | 0,925 | -245 | -187 | 55 | 0 | 0 | 6,31 | -245 | 0,66 | 0,65 | crítica | 0,352 |
| 90 | 300 | 0,925 | -224 | -166 | 76 | 0 | 0 | 6,27 | -224 | 0,69 | 0,68 | crítica | 0,323 |
| 120 | 300 | 0,925 | -208 | -150 | 92 | 0 | 0 | 6,24 | -208 | 0,72 | 0,70 | crítica | 0,301 |
| 180 | 300 | 0,925 | -185 | -127 | 115 | 0 | 0 | 6,21 | -185 | 0,75 | 0,73 | crítica | 0,271 |
| 240 | 300 | 0,925 | -171 | -113 | 129 | 0 | 0 | 6,18 | -171 | 0,77 | 0,75 | crítica | 0,254 |

**C · sangrado GI continuo (sin tratar) con relleno.** Hb mínima 6,11, máxima 6,40; V mínima -430, máxima 0.

| min | perdido | GR | C | plasma | relleno | cristaloide | GR transf. | Hb | V | gasto | DO2 | estado | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 1,000 | 0 | 0 | 0 | 0 | 0 | 6,40 | 0 | 1,00 | 1,00 | adecuada | 0,000 |
| 10 | 25 | 0,994 | -25 | -20 | 0 | 0 | 0 | 6,40 | -25 | 0,97 | 0,97 | crítica | 0,030 |
| 20 | 50 | 0,988 | -48 | -38 | 2 | 0 | 0 | 6,40 | -48 | 0,94 | 0,94 | crítica | 0,060 |
| 30 | 75 | 0,981 | -71 | -56 | 4 | 0 | 0 | 6,39 | -71 | 0,91 | 0,91 | crítica | 0,090 |
| 60 | 150 | 0,963 | -134 | -105 | 16 | 0 | 0 | 6,37 | -134 | 0,83 | 0,82 | crítica | 0,178 |
| 90 | 225 | 0,944 | -192 | -148 | 33 | 0 | 0 | 6,35 | -192 | 0,74 | 0,73 | crítica | 0,265 |
| 120 | 300 | 0,925 | -245 | -187 | 55 | 0 | 0 | 6,31 | -245 | 0,66 | 0,65 | crítica | 0,351 |
| 180 | 450 | 0,889 | -342 | -256 | 108 | 0 | 0 | 6,22 | -342 | 0,49 | 0,48 | crítica | 0,521 |
| 240 | 600 | 0,853 | -430 | -316 | 170 | 0 | 0 | 6,11 | -430 | 0,32 | 0,31 | crítica | 0,690 |

**D · sangrado GI detenido a los 120 min; el relleno continúa.** Hb mínima 6,21, máxima 6,40; V mínima -244, máxima 0.

| min | perdido | GR | C | plasma | relleno | cristaloide | GR transf. | Hb | V | gasto | DO2 | estado | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 1,000 | 0 | 0 | 0 | 0 | 0 | 6,40 | 0 | 1,00 | 1,00 | adecuada | 0,000 |
| 10 | 25 | 0,994 | -25 | -20 | 0 | 0 | 0 | 6,40 | -25 | 0,97 | 0,97 | crítica | 0,030 |
| 20 | 50 | 0,988 | -48 | -38 | 2 | 0 | 0 | 6,40 | -48 | 0,94 | 0,94 | crítica | 0,060 |
| 30 | 75 | 0,981 | -71 | -56 | 4 | 0 | 0 | 6,39 | -71 | 0,91 | 0,91 | crítica | 0,090 |
| 60 | 150 | 0,963 | -134 | -105 | 16 | 0 | 0 | 6,37 | -134 | 0,83 | 0,82 | crítica | 0,178 |
| 90 | 225 | 0,944 | -192 | -148 | 33 | 0 | 0 | 6,35 | -192 | 0,74 | 0,73 | crítica | 0,265 |
| 120 | 298 | 0,926 | -243 | -185 | 55 | 0 | 0 | 6,31 | -243 | 0,66 | 0,65 | crítica | 0,348 |
| 180 | 298 | 0,926 | -206 | -148 | 92 | 0 | 0 | 6,25 | -206 | 0,72 | 0,70 | crítica | 0,297 |
| 240 | 298 | 0,926 | -183 | -126 | 114 | 0 | 0 | 6,21 | -183 | 0,75 | 0,73 | crítica | 0,268 |

**E · 1 L de cristaloide en 20 min, sin sangrado.** Hb mínima 6,24, máxima 6,40; V mínima 0, máxima 104.

| min | perdido | GR | C | plasma | relleno | cristaloide | GR transf. | Hb | V | gasto | DO2 | estado | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 1,000 | 0 | 0 | 0 | 0 | 0 | 6,40 | 0 | 1,00 | 1,00 | adecuada | 0,000 |
| 10 | 0 | 1,000 | 56 | 56 | 0 | 56 | 0 | 6,31 | 56 | 1,07 | 1,05 | adecuada | 0,000 |
| 20 | 0 | 1,000 | 104 | 104 | 0 | 104 | 0 | 6,24 | 104 | 1,12 | 1,09 | adecuada | 0,000 |
| 30 | 0 | 1,000 | 89 | 89 | 0 | 89 | 0 | 6,26 | 89 | 1,10 | 1,08 | adecuada | 0,000 |
| 60 | 0 | 1,000 | 64 | 64 | 0 | 64 | 0 | 6,30 | 64 | 1,07 | 1,06 | adecuada | 0,000 |
| 90 | 0 | 1,000 | 55 | 55 | 0 | 55 | 0 | 6,31 | 55 | 1,06 | 1,05 | adecuada | 0,000 |
| 120 | 0 | 1,000 | 52 | 52 | 0 | 52 | 0 | 6,32 | 52 | 1,06 | 1,05 | adecuada | 0,000 |
| 180 | 0 | 1,000 | 50 | 50 | 0 | 50 | 0 | 6,32 | 50 | 1,06 | 1,05 | adecuada | 0,000 |
| 240 | 0 | 1,000 | 50 | 50 | 0 | 50 | 0 | 6,32 | 50 | 1,06 | 1,05 | adecuada | 0,000 |

**F · 2 L de cristaloide en 20 min, sin sangrado.** Hb mínima 6,08, máxima 6,40; V mínima 0, máxima 208.

| min | perdido | GR | C | plasma | relleno | cristaloide | GR transf. | Hb | V | gasto | DO2 | estado | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 1,000 | 0 | 0 | 0 | 0 | 0 | 6,40 | 0 | 1,00 | 1,00 | adecuada | 0,000 |
| 10 | 0 | 1,000 | 113 | 113 | 0 | 113 | 0 | 6,22 | 113 | 1,13 | 1,10 | adecuada | 0,000 |
| 20 | 0 | 1,000 | 208 | 208 | 0 | 208 | 0 | 6,08 | 208 | 1,22 | 1,16 | adecuada | 0,000 |
| 30 | 0 | 1,000 | 177 | 177 | 0 | 177 | 0 | 6,13 | 177 | 1,19 | 1,14 | adecuada | 0,000 |
| 60 | 0 | 1,000 | 128 | 128 | 0 | 128 | 0 | 6,20 | 128 | 1,14 | 1,11 | adecuada | 0,000 |
| 90 | 0 | 1,000 | 110 | 110 | 0 | 110 | 0 | 6,23 | 110 | 1,12 | 1,09 | adecuada | 0,000 |
| 120 | 0 | 1,000 | 104 | 104 | 0 | 104 | 0 | 6,24 | 104 | 1,12 | 1,09 | adecuada | 0,000 |
| 180 | 0 | 1,000 | 101 | 101 | 0 | 101 | 0 | 6,24 | 101 | 1,11 | 1,09 | adecuada | 0,000 |
| 240 | 0 | 1,000 | 100 | 100 | 0 | 100 | 0 | 6,24 | 100 | 1,11 | 1,09 | adecuada | 0,000 |

**G · 1 unidad de GR en 30 min, sin sangrado.** Hb mínima 6,40, máxima 7,35; V mínima 0, máxima 300.

| min | perdido | GR | C | plasma | relleno | cristaloide | GR transf. | Hb | V | gasto | DO2 | estado | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 1,000 | 0 | 0 | 0 | 0 | 0 | 6,40 | 0 | 1,00 | 1,00 | adecuada | 0,000 |
| 10 | 0 | 1,078 | 100 | 39 | 0 | 0 | 100 | 6,73 | 100 | 1,11 | 1,17 | adecuada | 0,000 |
| 20 | 0 | 1,156 | 200 | 79 | 0 | 0 | 200 | 7,05 | 200 | 1,21 | 1,34 | adecuada | 0,000 |
| 30 | 0 | 1,234 | 300 | 118 | 0 | 0 | 300 | 7,35 | 300 | 1,30 | 1,50 | adecuada | 0,000 |
| 60 | 0 | 1,234 | 300 | 118 | 0 | 0 | 300 | 7,35 | 300 | 1,30 | 1,50 | adecuada | 0,000 |
| 90 | 0 | 1,234 | 300 | 118 | 0 | 0 | 300 | 7,35 | 300 | 1,30 | 1,50 | adecuada | 0,000 |
| 120 | 0 | 1,234 | 300 | 118 | 0 | 0 | 300 | 7,35 | 300 | 1,30 | 1,50 | adecuada | 0,000 |
| 180 | 0 | 1,234 | 300 | 118 | 0 | 0 | 300 | 7,35 | 300 | 1,30 | 1,50 | adecuada | 0,000 |
| 240 | 0 | 1,234 | 300 | 118 | 0 | 0 | 300 | 7,35 | 300 | 1,30 | 1,50 | adecuada | 0,000 |

**H · 2 unidades de GR en 60 min, sin sangrado.** Hb mínima 6,40, máxima 8,17; V mínima 0, máxima 600.

| min | perdido | GR | C | plasma | relleno | cristaloide | GR transf. | Hb | V | gasto | DO2 | estado | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 1,000 | 0 | 0 | 0 | 0 | 0 | 6,40 | 0 | 1,00 | 1,00 | adecuada | 0,000 |
| 10 | 0 | 1,078 | 100 | 39 | 0 | 0 | 100 | 6,73 | 100 | 1,11 | 1,17 | adecuada | 0,000 |
| 20 | 0 | 1,156 | 200 | 79 | 0 | 0 | 200 | 7,05 | 200 | 1,21 | 1,34 | adecuada | 0,000 |
| 30 | 0 | 1,234 | 300 | 118 | 0 | 0 | 300 | 7,35 | 300 | 1,30 | 1,50 | adecuada | 0,000 |
| 60 | 0 | 1,469 | 600 | 236 | 0 | 0 | 600 | 8,17 | 600 | 1,51 | 1,93 | adecuada | 0,000 |
| 90 | 0 | 1,469 | 600 | 236 | 0 | 0 | 600 | 8,17 | 600 | 1,51 | 1,93 | adecuada | 0,000 |
| 120 | 0 | 1,469 | 600 | 236 | 0 | 0 | 600 | 8,17 | 600 | 1,51 | 1,93 | adecuada | 0,000 |
| 180 | 0 | 1,469 | 600 | 236 | 0 | 0 | 600 | 8,17 | 600 | 1,51 | 1,93 | adecuada | 0,000 |
| 240 | 0 | 1,469 | 600 | 236 | 0 | 0 | 600 | 8,17 | 600 | 1,51 | 1,93 | adecuada | 0,000 |

**I · 2 unidades en 60 min durante sangrado GI continuo.** Hb mínima 6,40, máxima 8,20; V mínima 0, máxima 450.

| min | perdido | GR | C | plasma | relleno | cristaloide | GR transf. | Hb | V | gasto | DO2 | estado | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 1,000 | 0 | 0 | 0 | 0 | 0 | 6,40 | 0 | 1,00 | 1,00 | adecuada | 0,000 |
| 10 | 25 | 1,072 | 75 | 19 | 0 | 0 | 100 | 6,73 | 75 | 1,09 | 1,14 | adecuada | 0,000 |
| 20 | 50 | 1,143 | 150 | 39 | 0 | 0 | 200 | 7,05 | 150 | 1,16 | 1,28 | adecuada | 0,000 |
| 30 | 75 | 1,214 | 225 | 59 | 0 | 0 | 300 | 7,36 | 225 | 1,24 | 1,42 | adecuada | 0,000 |
| 60 | 150 | 1,426 | 450 | 120 | 0 | 0 | 600 | 8,20 | 450 | 1,42 | 1,82 | adecuada | 0,000 |
| 90 | 225 | 1,402 | 375 | 63 | 0 | 0 | 600 | 8,20 | 375 | 1,36 | 1,75 | adecuada | 0,000 |
| 120 | 300 | 1,378 | 300 | 7 | 0 | 0 | 600 | 8,20 | 300 | 1,30 | 1,67 | adecuada | 0,000 |
| 180 | 450 | 1,330 | 150 | -106 | 0 | 0 | 600 | 8,20 | 150 | 1,16 | 1,49 | adecuada | 0,000 |
| 240 | 600 | 1,282 | 0 | -218 | 0 | 0 | 600 | 8,20 | 0 | 1,00 | 1,28 | adecuada | 0,000 |

**J · 2 L de cristaloide en 20 min durante sangrado GI continuo.** Hb mínima 5,98, máxima 6,40; V mínima -333, máxima 158.

| min | perdido | GR | C | plasma | relleno | cristaloide | GR transf. | Hb | V | gasto | DO2 | estado | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 1,000 | 0 | 0 | 0 | 0 | 0 | 6,40 | 0 | 1,00 | 1,00 | adecuada | 0,000 |
| 10 | 25 | 0,994 | 88 | 93 | 0 | 113 | 0 | 6,22 | 88 | 1,10 | 1,07 | adecuada | 0,000 |
| 20 | 50 | 0,988 | 158 | 167 | 0 | 208 | 0 | 6,08 | 158 | 1,17 | 1,11 | adecuada | 0,000 |
| 30 | 75 | 0,982 | 102 | 116 | 0 | 177 | 0 | 6,13 | 102 | 1,12 | 1,07 | adecuada | 0,000 |
| 60 | 150 | 0,964 | -18 | 10 | 3 | 128 | 0 | 6,20 | -18 | 0,98 | 0,95 | crítica | 0,053 |
| 90 | 225 | 0,946 | -91 | -49 | 23 | 110 | 0 | 6,19 | -91 | 0,88 | 0,86 | crítica | 0,144 |
| 120 | 300 | 0,928 | -149 | -93 | 47 | 104 | 0 | 6,17 | -149 | 0,80 | 0,77 | crítica | 0,225 |
| 180 | 450 | 0,892 | -246 | -162 | 103 | 101 | 0 | 6,08 | -246 | 0,66 | 0,62 | crítica | 0,376 |
| 240 | 600 | 0,856 | -333 | -221 | 167 | 100 | 0 | 5,98 | -333 | 0,51 | 0,48 | crítica | 0,525 |

**K · hemostasia endoscópica a los 120 min tras pérdida acumulada (residual 10 %).** Hb mínima 6,20, máxima 6,40; V mínima -244, máxima 0.

| min | perdido | GR | C | plasma | relleno | cristaloide | GR transf. | Hb | V | gasto | DO2 | estado | déficit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 1,000 | 0 | 0 | 0 | 0 | 0 | 6,40 | 0 | 1,00 | 1,00 | adecuada | 0,000 |
| 10 | 25 | 0,994 | -25 | -20 | 0 | 0 | 0 | 6,40 | -25 | 0,97 | 0,97 | crítica | 0,030 |
| 20 | 50 | 0,988 | -48 | -38 | 2 | 0 | 0 | 6,40 | -48 | 0,94 | 0,94 | crítica | 0,060 |
| 30 | 75 | 0,981 | -71 | -56 | 4 | 0 | 0 | 6,39 | -71 | 0,91 | 0,91 | crítica | 0,090 |
| 60 | 150 | 0,963 | -134 | -105 | 16 | 0 | 0 | 6,37 | -134 | 0,83 | 0,82 | crítica | 0,178 |
| 90 | 225 | 0,944 | -192 | -148 | 33 | 0 | 0 | 6,35 | -192 | 0,74 | 0,73 | crítica | 0,265 |
| 120 | 298 | 0,926 | -243 | -186 | 55 | 0 | 0 | 6,31 | -243 | 0,66 | 0,65 | crítica | 0,348 |
| 180 | 313 | 0,922 | -219 | -159 | 93 | 0 | 0 | 6,24 | -219 | 0,70 | 0,68 | crítica | 0,318 |
| 240 | 328 | 0,919 | -208 | -145 | 120 | 0 | 0 | 6,20 | -208 | 0,72 | 0,69 | crítica | 0,306 |

### 4.2 Identificabilidad de κ y λ, y normalización del volumen

| κ / escala λ (mL-eq) | V a 120 min | C a 120 min | gasto a 120 min | Hb a 120 min |
|---|---|---|---|---|
| 0.5/416.667 | -123 | -245 | 0,6579 | 6,309 |
| 1/833.333 | -245 | -245 | 0,6579 | 6,309 |
| 2/1666.67 | -490 | -245 | 0,6579 | 6,309 |

| Volumen circulante de llegada (mL-eq) | V a 120 min | gasto a 120 min | Hb a 120 min |
|---|---|---|---|
| 3000 | -245 | 0,6579 | 6,277 |
| 4000 | -245 | 0,6579 | 6,309 |
| 5000 | -245 | 0,6579 | 6,328 |

### 4.3 Golden GI: antes / después

Antes: `d087bde147a1254c6d81c883dbea09670dd97b0316d1e26e93e3364bde822833`; después: `b7e6a03915b3a6907b5fc73e9827c5784dc42697ea5823231a693433919b399d` (sha256 de `clinical_core/golden/gi_bleed_shadow.json`). Cada celda: motor heredado · núcleo antes → núcleo después, en el último minuto de la corrida.

| Corrida | min | V | Hb | PAS | FC | lactato | FR | llenado capilar | Variables distintas del heredado: antes → después |
|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m/aggressive_volume | 90 | 528 · 1088 → 1088 | 8,09 · 8,09 → 9,60 | 117,0 · 121,0 → 121,0 | 108,0 · 124,0 → 124,0 | 3,10 · 4,40 → 4,40 | 16,0 · 26,0 → 26,0 | 2,50 · 2,10 → 2,10 | +Hb |
| gi_bleed_57m/definitive_management | 120 | 467 · 467 → 467 | 7,92 · 7,92 → 8,46 | 113,0 · 107,0 → 107,0 | 95,0 · 124,0 → 124,0 | 3,30 · 4,40 → 4,40 | 18,0 · 26,0 → 26,0 | 2,80 · 3,30 → 3,30 | +Hb |
| gi_bleed_57m/oxygen_non_rebreather | 20 | -50 · -50 → -48 | 6,52 · 6,52 → 6,70 | 85,0 · 85,0 → 85,0 | 125,0 · 126,0 → 126,0 | 4,50 · 4,40 → 4,40 | 27,0 · 26,0 → 26,0 | 5,20 · 5,20 → 5,20 | +V, +Hb, −PAD, −PAM, −PAS |
| gi_bleed_57m/prbc_2u_over_60 | 90 | 375 · 375 → 375 | 7,59 · 7,59 → 8,46 | 108,0 · 104,0 → 104,0 | 113,0 · 124,0 → 124,0 | 3,50 · 4,40 → 4,40 | 19,0 · 26,0 → 26,0 | 3,20 · 3,60 → 3,60 | +Hb |
| gi_bleed_57m/queued_timed_bags | 45 | 44 · 44 → 44 | 5,09 · 5,09 → 6,45 | 90,0 · 90,0 → 90,0 | 123,0 · 124,0 → 124,0 | 4,30 · 4,40 → 4,40 | 25,0 · 26,0 → 26,0 | 4,80 · 4,80 → 4,80 | +Hb |
| gi_bleed_57m/saline_2l_over_20 | 60 | -22 · -22 → -18 | 4,96 · 4,96 → 6,49 | 87,0 · 87,0 → 87,0 | 125,0 · 126,0 → 125,0 | 4,50 · 4,40 → 4,40 | 26,0 · 26,0 → 26,0 | 5,10 · 5,10 → 5,10 | +V, +Hb |
| gi_bleed_57m/saline_then_blood | 120 | 397 · 397 → 397 | 6,88 · 6,88 → 8,39 | 109,0 · 105,0 → 105,0 | 112,0 · 124,0 → 124,0 | 3,40 · 4,40 → 4,40 | 19,0 · 26,0 → 26,0 | 3,10 · 3,50 → 3,50 | +Hb |
| gi_bleed_57m/stop_fluids | 60 | -43 · -43 → -37 | 5,16 · 5,16 → 6,52 | 86,0 · 86,0 → 86,0 | 125,0 · 126,0 → 125,0 | 4,50 · 4,40 → 4,40 | 27,0 · 26,0 → 26,0 | 5,20 · 5,20 → 5,20 | +V, +Hb |
| gi_bleed_57m/untimed_shared_line | 90 | 490 · 490 → 490 | 6,39 · 6,39 → 8,27 | 114,0 · 108,0 → 108,0 | 109,0 · 124,0 → 124,0 | 3,20 · 4,40 → 4,40 | 17,0 · 26,0 → 26,0 | 2,60 · 3,20 → 3,20 | +Hb |
| gi_bleed_57m/untreated_60 | 60 | -150 · -150 → -134 | 6,16 · 6,16 → 6,67 | 80,0 · 79,0 → 80,0 | 128,0 · 130,0 → 129,0 | 4,80 · 4,50 → 4,40 | 29,0 · 26,0 → 26,0 | 5,70 · 5,80 → 5,70 | +V, +Hb, −conciencia |
| gi_bleed_72f/aggressive_volume | 90 | 528 · 1088 → 1088 | 7,79 · 7,79 → 9,38 | 127,0 · 131,0 → 131,0 | 96,0 · 112,0 → 112,0 | 2,10 · 3,40 → 3,40 | 14,0 · 24,0 → 24,0 | 2,00 · 2,00 → 2,00 | +Hb |
| gi_bleed_72f/definitive_management | 120 | 467 · 467 → 467 | 7,62 · 7,62 → 8,20 | 123,0 · 117,0 → 117,0 | 83,0 · 112,0 → 112,0 | 2,30 · 3,40 → 3,40 | 16,0 · 24,0 → 24,0 | 2,00 · 2,30 → 2,30 | +Hb |
| gi_bleed_72f/oxygen_non_rebreather | 20 | -50 · -50 → -48 | 6,22 · 6,22 → 6,40 | 95,0 · 95,0 → 95,0 | 113,0 · 114,0 → 113,0 | 3,50 · 3,40 → 3,40 | 25,0 · 24,0 → 24,0 | 4,20 · 4,20 → 4,20 | +V, +Hb, −PAD, −FC, −PAS |
| gi_bleed_72f/prbc_2u_over_60 | 90 | 375 · 375 → 375 | 7,29 · 7,29 → 8,20 | 118,0 · 114,0 → 114,0 | 101,0 · 112,0 → 112,0 | 2,50 · 3,40 → 3,40 | 17,0 · 24,0 → 24,0 | 2,20 · 2,60 → 2,60 | +Hb |
| gi_bleed_72f/queued_timed_bags | 45 | 44 · 44 → 44 | 4,79 · 4,79 → 6,16 | 100,0 · 100,0 → 100,0 | 111,0 · 112,0 → 112,0 | 3,30 · 3,40 → 3,40 | 23,0 · 24,0 → 24,0 | 3,80 · 3,80 → 3,80 | +Hb |
| gi_bleed_72f/saline_2l_over_20 | 60 | -22 · -22 → -18 | 4,66 · 4,66 → 6,20 | 97,0 · 97,0 → 97,0 | 113,0 · 114,0 → 113,0 | 3,50 · 3,50 → 3,40 | 24,0 · 24,0 → 24,0 | 4,10 · 4,10 → 4,10 | +V, +Hb |
| gi_bleed_72f/saline_then_blood | 120 | 397 · 397 → 397 | 6,58 · 6,58 → 8,14 | 119,0 · 115,0 → 115,0 | 100,0 · 112,0 → 112,0 | 2,40 · 3,40 → 3,40 | 17,0 · 24,0 → 24,0 | 2,10 · 2,50 → 2,50 | +Hb |
| gi_bleed_72f/stop_fluids | 60 | -43 · -43 → -37 | 4,86 · 4,86 → 6,22 | 96,0 · 96,0 → 96,0 | 113,0 · 115,0 → 113,0 | 3,50 · 3,40 → 3,40 | 25,0 · 24,0 → 24,0 | 4,20 · 4,20 → 4,20 | +V, +Hb |
| gi_bleed_72f/untimed_shared_line | 90 | 490 · 490 → 490 | 6,09 · 6,09 → 8,01 | 124,0 · 118,0 → 118,0 | 97,0 · 112,0 → 112,0 | 2,20 · 3,40 → 3,40 | 15,0 · 24,0 → 24,0 | 2,00 · 2,20 → 2,20 | +Hb |
| gi_bleed_72f/untreated_60 | 60 | -150 · -150 → -134 | 5,86 · 5,86 → 6,37 | 90,0 · 89,0 → 90,0 | 116,0 · 118,0 → 117,0 | 3,80 · 3,50 → 3,40 | 27,0 · 24,0 → 24,0 | 4,70 · 4,80 → 4,70 | +V, +Hb |

<!-- /generado:estado-sanguineo -->

## 5. Parámetros TBD (P2I-2T-14)

| Parámetro | Valor provisional | Dónde |
|---|---|---|
| tasa del sangrado | 2,5 mL-eq/min (literal GI, sólo para la comparación) | `GIHaemorrhage.blood_loss_ml_per_min`; FD-22 |
| normalización del volumen circulante (B0) | 4000 mL-eq | `arrival_circulating_volume_ml` |
| κ (y λ, sólo como razón) | 1 (λ 833) | `volume_preload_kappa`, `preload_curve_scale_ml` |
| meta del relleno, capacidad y τ | 0,5 de lo perdido, 1000 mL-eq, 120 min | `plasma_refill_target_share`, `plasma_refill_capacity_ml`, `plasma_refill_tau_min` |
| contenido y volumen efectivo de la unidad de GR | 20 g/dL, 300 mL-eq | `legacy_adapter.PROVISIONAL_RED_CELL_UNIT_HB_G_DL`, `volume_ml_per_unit` |
| retención del cristaloide y τ de redistribución | 12,5 %, 60 % transitorio, 30 min | `GI_BLEED` del motor, vía el adaptador |
| posición de precarga de llegada | 0,5 (sin declarar) | `preload_fraction` |
| ρ (reserva de extracción) | 1 canónica; banda candidata 2,0–3,0 | `oxygen_extraction_reserve` |

Los cinco del estado compartido y la unidad están en el registro de calibración como CANDIDATE sin banda. El documento
P2G los lista fuera de su tabla maestra con el motivo, y FD-23 (la tasa de Hb) quedó retirada.

## 6. Efectos sobre los artefactos

- **Golden GI.** Cambió (§4.3). La Hb ya no coincide con el motor en ninguna corrida. V difiere donde el relleno actúa:
  - difiere sin tratamiento, con oxígeno y con salino solo o detenido;
  - coincide donde las órdenes mantienen la circulación sobre la llegada desde el comienzo;
  - difiere también, como antes, fuera de la pinza del motor (KD-S4).
  - La Hb del núcleo queda ahora muy por encima de la del motor: 6,67 frente a 6,16 en la hora sin tratamiento de 57m, y
    6,49 frente a 4,96 tras 2 L de salino. Con 2,5 mL-eq/min de sangre total y un relleno parcial, la Hb apenas cae; la
    deriva heredada describía una pérdida de sangre varias veces mayor (P2I-2S). Es una consecuencia de valores TBD (la
    tasa, B0, la meta del relleno y la retención del cristaloide), no un ajuste.
  - Las variables aguas abajo cambian de tamaño.
  - En las corridas de oxígeno de 20 min, la PA mostrada vuelve a coincidir con la del motor.
  - En la hora sin tratamiento de 57m, la PAS cruda ya no llega al umbral de 80 mmHg: KD-S3 queda registrada pero
    `DORMANT`.
  - Se registró la diferencia conocida P2I-2T («approved» en estructura, magnitud TBD). No queda ninguna diferencia
    UNRESOLVED.
- **Contracts v2.** La sombra directa y la de Contracts v2 siguen idénticas entre sí.
- **Congelamiento de calibración.** Cambiaron bandas, `harness_sources`, `migration_sources`, `input_adapter_sources` y
  `scenario_inputs`; las reglas no cambiaron. El motivo está en la prueba.
- **Puerta de migración.** Los dos casos GI siguen bloqueados, con 11 bloqueos (12 antes: se fue la tasa de Hb).
- **Paquete P2G y corte P2I-1.** Se regeneraron con el núcleo nuevo. La región admisible sigue siendo de 1054 conjuntos
  y las cifras de lactato y FC cambian poco.
  - En el documento P2G, FD-22 pasó a la tasa de sangre total y FD-23 se retiró (48 decisiones abiertas).
- **P2I-2R.** Sigue PENDIENTE DE REFILTRADO y conserva su congelamiento (`152abc6c…`).
- **P2I-2P, P2I-2Q y P2I-2S.** Quedan como registros históricos anteriores a P2I-2T (`HISTORICAL`): sus documentos y JSON
  no se regeneran, y sus comandos lo rehúsan.

## 7. Revisión adversarial (subagente independiente, de sólo lectura)

Cada hallazgo se confirmó con una sonda antes de corregirlo.

| # | Hallazgo | Resultado |
|---|---|---|
| F1 | el relleno seguía añadiendo volumen con la circulación ya sobre la llegada (GR, cristaloide) | corregido: el relleno sólo restaura un déficit (§1.4) |
| F2 | las guardas de V y Hb separaban el canal del estado sin que nada lo notara | corregido: falla cerrado si recortan lo que movió el estado; lo que mueven sondas y límites se contabiliza y se comprueba cada minuto |
| F3 | la guarda de V, en unidades de V, rompía la equivalencia (κ, λ) | corregido: guarda en volumen circulante |
| F4 | un estado inicial o reanudado no se contrastaba con su estado sanguíneo | corregido: `check_blood_identity` al comenzar la corrida y cada minuto |
| F5 | la sonda de banda de nivel 2 «GI bleed / trauma» (`bands.py`) sigue con dos derivas | **pendiente:** está en el arnés congelado; cambiarla necesita autorización (§8) |
| F6 | prosa del documento P2G con cifras anteriores a la regeneración | corregido, cifra por cifra contra sus tablas; las sondas de V sola de §11, rotuladas |
| F7 | los requisitos 5 y 6 de P2I-2S ya no se probaban en el núcleo vigente | corregido: prueba viva nueva, además de la del registro |
| F8 | `crystalloid_out` se comprueba en total, no por fuente | limitación registrada: cada bolsa lleva su propio depósito, pero el núcleo no verifica que una fuente no saque más de lo que dio |
| F9 | los registros no se contrastaban con la composición | corregido |
| F10 | la comparación lee V como volumen del motor; sólo vale con κ = 1 | limitación registrada: el golden usa el perfil canónico (κ 1) |
| F11 | la traza de Contracts v2 no tenía el bloque del estado sanguíneo | corregido (`core_blood_state`) |
| F12 | restos menores (`REFERENCE_ONLY` sin uso, un comentario de «volumen intravascular») | corregidos: una prueba exige que ningún constructor lea esos literales |

## 8. Decisiones pendientes

- **Valores provisionales:** la tasa del sangrado (FD-22), B0, κ (con λ), la meta, la capacidad y la τ del relleno, la
  unidad de GR y la retención del cristaloide (§5).
- **Sonda de banda «GI bleed / trauma»** (`bands.py`, en el arnés congelado). Sigue moviendo V y Hb con dos derivas
  declaradas, ahora contabilizadas. Retirarla o pasarla a un flujo de sangre total cambia el congelamiento: necesita
  autorización.
- **Freno del relleno por los líquidos por debajo de la llegada:** no se modela; sería otra decisión.

## 9. Qué no hace

- No calibra el sangrado, la presión ni la FC.
- No refiltra el lactato.
- No activa el colapso canónico.
- No migra GI ni otra familia.
- No integra nada en tiempo de ejecución ni cambia lo que ve el residente.
- No aprueba ningún valor: todos siguen CANDIDATE / PROVISIONAL.
