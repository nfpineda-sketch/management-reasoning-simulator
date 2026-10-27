# P2I-2S · Restricciones de calibración de la escala hemorragia / precarga

> **REGISTRO HISTÓRICO, anterior a P2I-2T (2026-10-27).** Esta auditoría describe el núcleo en sombra antes de que el
> estado hemorrágico compartido (P2I-2T, `docs/revision/P2I2T_ESTADO_HEMORRAGICO_COMPARTIDO.md`) reemplazara las derivas
> independientes de V y Hb del sangrado GI. Sus cifras y su JSON (sondas
> `760627b365b161b166872b932b2bd5cf4fdba6b3507ad17a28215dfb2a8f1357`) quedan tal como se aceptaron y no se regeneran; las
> trayectorias GI actuales son otras.

Este paquete es una auditoría en sombra **de sólo lectura**:
- no cambia la fisiología, ningún valor por defecto, banda, registro, golden ni regla;
- no aprueba ningún valor de λ ni de posición;
- no vuelve a filtrar el lactato (P2I-2R sigue en pausa).

Las sondas están en `clinical_core/haemorrhage_probes.py` y los resultados en `docs/revision/P2I2S_haemorrhage_probes.json`.
- **V** sigue siendo una coordenada interna de precarga efectiva en mL-eq, no volumen de sangre literal. Los «análogos de
  discusión» en mL sólo sirven para conversar.
- **Oxígeno:** reserva candidata 2,5 y banda de llegada re-anclada.
- **Representante:** el mismo de P2I-2Q.
- **Nada se ordenó por parecido al motor heredado.** Tampoco por evitar una PAS de 26 ni por la similitud con el golden.

## 0. Interpretación docente vigente (registrada el 2026-10-27)

- **Conclusión de P2I-2Q aceptada:** el problema V → gasto es de escala o calibración (PARAMETER_SCALE_CALIBRATION_ERROR), no
  de forma.
- **V:** coordenada interna en mL-eq, que no se reinterpreta como volumen de sangre.
- **Coherencia exigida:** pérdida de sangre, pérdida de V, pérdida de Hb, precarga y gasto, y DO2 deben salir de un proceso
  hemorrágico coherente. V y Hb no necesitan las mismas unidades.
- **λ 1500–2000 no está aprobado.**
  - No se elige por la PA heredada, por evitar una PAS de 26 ni por parecerse al golden.
  - Se calibra con respuestas de paciente.
- **Presión y FC quedan fuera:** el quiebre de la rodilla, el tono, la FC en el gasto y los efectos simpáticos son de un paquete
  posterior.

## 1. Representación actual de la hemorragia (P2I-2S-1)

| Proceso | Efecto en V | Efecto en Hb | ¿De dónde sale? |
|---|---|---|---|
| Sangrado GI | −2,5 mL-eq/min × fracción (1 sin tratar; 0,8 con IBP; 0,1 tras la hemostasia) | −0,009 g/dL/min × la misma fracción, constante, sea cual sea la Hb, el volumen o los fluidos | Dos literales heredados independientes: 0,003 «circulación»/min y 0,009 g/dL/min |
| Glóbulos rojos | +300 mL-eq por unidad | +0,85 g/dL por unidad, constante | Dos literales heredados: 0,36 de «circulación» y 0,85 g/dL |
| Salino | +0,125 mL-eq por mL infundido; el 60 % se fuga con τ 30 min | −0,0006 g/dL por mL infundido, al infundir. No se revierte cuando el volumen se fuga | Literales del motor de la familia |
| Llegada | V = 0 por definición; posición en la curva = banda POCUS (57m 0,2–0,35–0,5; 72f 0,3–0,45–0,6) | Hb del caso | `reference_preload_fraction` (0,6–0,8) es sólo diagnóstica: ningún mecanismo la lee |

**Respuesta: B · dos derivas ajustadas por separado.**
- Sólo comparten la fracción de actividad del sangrado.
- No hay una cantidad de hemorragia subyacente: lo mismo ocurre con la transfusión y el cristaloide, cada uno con dos
  constantes propias.
- **Se informa como problema estructural de calibración.** No se las forzó a coincidir.

**Incoherencias concretas** (§4.1 y §4.7; mezcla de 3–5 L sólo como análogo de discusión):
- **Sangrado:** en 2 h, V −300 mL-eq y Hb −1,08 g/dL (16 %).
  - **Sin suponer nada sobre V:** una caída de Hb del 16 % en 2 h exige al menos 484 / 645 / 806 mL de sangre perdida (mezcla
    de 3 / 4 / 5 L, con relleno completo). Con menos relleno, más.
  - **Sólo si se supusiera que V cuenta el volumen circulante 1:1 (κ = 1):**
    - leído así, la sangre perdida no bajaría la Hb, porque sale entera a su propia concentración (§4.7, sin relleno);
    - para que un solo sangrado diera ambas cifras harían falta 735–1058 mL, con un 59–72 % ya rellenado por plasma en las
      mismas 2 h: 2,5–3,5 veces la pérdida de V;
    - ese relleno implícito no aparece en ningún otro lugar del modelo: no hay recuperación de V ni dilución tras la
      hemostasia.
- **Hb constante:** la caída de Hb es la misma en g/dL con Hb 3 que con Hb 13. La dilución debería ser proporcional a la Hb.
- **Glóbulos rojos:** el efecto en la Hb es compatible con una unidad de 16–22 g/dL en la mezcla. Los 300 mL-eq de V no
  prueban nada: el mL-eq se definió justamente como 300 mL / 0,36, así que la coincidencia es circular. Ambos efectos son
  constantes que no dependen del estado.
- **Salino 2 L:**
  - V gana 250 mL-eq brutos, alcanza un pico real de 208 (infusión de 20 min con fuga) y retiene 100;
  - la dilución de −1,2 g/dL implicaría 655–1091 mL retenidos. V cuenta sólo 0,09–0,15 mL-eq por mL retenido implícito,
    frente a 1,0 por mL de glóbulos rojos (7 a 11 veces menos);
  - la dilución persiste cuando el 60 % del volumen se fuga (prueba).

## 2. Semántica (P2I-2S-1, puntos 6–8)

- **Pérdida de V:** desplazamiento de la precarga efectiva, en la misma unidad interna que la escala de la curva λ y que la
  unidad de glóbulos rojos.
- **λ es una convención de unidades (§4.8, prueba):** V entra en la fisiología sólo como V/λ.
  - Si se duplican λ y todas las entradas de V, ninguna corrida cambia (diferencia 0,0 en gasto, DO2 y D).
  - Lo fisiológico son las razones adimensionales, junto con la posición p₀:
    - sangrado/λ: 0,003 por min;
    - unidad/λ: 0,36;
    - salino/λ: 0,00015 por mL.
  - Con la λ actual, esas razones son exactamente los literales del motor heredado: la calibración actual es la heredada,
    escrita en otras unidades.
  - Elegir λ con las entradas fijas equivale a elegir esas razones. No es un parámetro fisiológico propio.
- **Pérdida de Hb:** una deriva de concentración propia. Codifica a la vez la pérdida y la dilución por relleno, sin
  representarlas.
- **¿Comparten un estado de sangrado? No.** Sólo comparten la fracción de actividad.

## 3. Anclas clínicas de pérdida incremental (P2I-2S-2)

- **Las anclas:** se definen por el proceso, como minutos del sangrado GI no tratado tras la llegada:
  - pequeña: 30 min;
  - moderada: 60 min;
  - grave continua: 120 min;
  - muy grave o prolongada: 240 min.
- **Qué aplican:** a V y a la Hb exactamente lo que aplica el módulo. No se infiere la pérdida previa a la llegada desde la
  Hb, y no se afirma que un mL-eq sea un mL.
- **Resultados (§4.2, 57m; con las entradas actuales, λ 833 / 1500 / 2000 equivalen a sangrado/λ 0,0030 / 0,0017 / 0,0013
  por min):**
  - con λ 833: pequeña 0,83, moderada 0,63, grave 0,20 y muy grave sin gasto;
  - con λ 1500: 0,90 · 0,80 · 0,59 · 0,09;
  - con λ 2000: 0,93 · 0,86 · 0,70 · 0,35.
  
  Todas quedan críticas (la llegada ya lo es, con DO2 0,34), con la fracción de déficit creciendo.

## 4. Tablas (generado)

<!-- generado:hemorragia -->
Generado desde las sondas `760627b365b161b166872b932b2bd5cf4fdba6b3507ad17a28215dfb2a8f1357` (`python -m clinical_core.haemorrhage_probes`). Oxígeno con la reserva candidata 2,5 y la banda de llegada re-anclada; representante `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=midpoint;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint`. Anclas de pérdida incremental = minutos del sangrado no tratado del módulo GI: pequeña 30 min, moderada 60 min, grave continua 120 min, muy grave o prolongada 240 min. V es una coordenada interna (mL-eq), no volumen de sangre.

### 4.1 Auditoría del estado de hemorragia

| Caso | Llegada: V, Hb, banda de posición (ref. euvolémica) | Sangrado: V/min, Hb/min (g/dL), Hb por mL-eq | 2 h de sangrado: ΔV, ΔHb (relativa) | Análogo, sin suponer nada sobre V (mezcla 3 / 4 / 5 L): sangre mínima que explica la caída de Hb | Análogo SUPONIENDO V = volumen circulante (κ = 1): sangre que daría ambas, fracción rellenada, sangre / ΔV | GR por unidad: V, Hb; Hb de la unidad implícita | Salino 2 L: ganancia bruta / pico real / retenido en V, ΔHb; retenido implícito por la dilución; V por mL retenido implícito |
|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 0, 6,7, 0,20 / 0,35 / 0,50 (0,60 / 0,70 / 0,80) | 2,5, 0,009, 0,0036 | −300, −1,08 (16 %) | 484 / 645 / 806 mL | 735 mL, 0,59, ×2,5; 896 mL, 0,67, ×3,0; 1058 mL, 0,72, ×3,5 | +300, +0,85; 16,1 / 18,9 / 21,7 g/dL | +250 / +208 / +100, −1,2; 655 / 873 / 1091 mL; 0,15 / 0,11 / 0,09 |
| gi_bleed_72f | 0, 6,4, 0,30 / 0,45 / 0,60 (0,60 / 0,70 / 0,80) | 2,5, 0,009, 0,0036 | −300, −1,08 (17 %) | 506 / 675 / 844 mL | 756 mL, 0,60, ×2,5; 924 mL, 0,68, ×3,1; 1093 mL, 0,73, ×3,6 | +300, +0,85; 15,8 / 18,6 / 21,4 g/dL | +250 / +208 / +100, −1,2; 692 / 923 / 1154 mL; 0,14 / 0,11 / 0,09 |

### 4.2 Anclas clínicas de pérdida incremental tras la llegada

| Caso; λ | Ancla | ΔV (mL-eq) | Hb | Llenado efectivo | Gasto | PAS / PAM | DO2 / normal | Estado | Fracción de déficit |
|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m; 833 | pequeña | -75 | 6,43 | 284 | 0,83 | 80 / 60 | 0,27 | crítica | 0,33 |
| gi_bleed_57m; 833 | moderada | -150 | 6,16 | 209 | 0,63 | 72 / 54 | 0,20 | crítica | 0,50 |
| gi_bleed_57m; 833 | grave continua | -300 | 5,62 | 59 | 0,20 | 26 / 19 | 0,06 | crítica | 0,86 |
| gi_bleed_57m; 833 | muy grave o prolongada | -600 | 4,54 | — | 0,00 | — / — | 0,00 | crítica | 1,00 |
| gi_bleed_57m; 1500 | pequeña | -75 | 6,43 | 571 | 0,90 | 84 / 62 | 0,30 | crítica | 0,26 |
| gi_bleed_57m; 1500 | moderada | -150 | 6,16 | 496 | 0,80 | 79 / 59 | 0,25 | crítica | 0,37 |
| gi_bleed_57m; 1500 | grave continua | -300 | 5,62 | 346 | 0,59 | 69 / 52 | 0,17 | crítica | 0,58 |
| gi_bleed_57m; 1500 | muy grave o prolongada | -600 | 4,54 | 46 | 0,09 | 11 / 9 | 0,02 | crítica | 0,95 |
| gi_bleed_57m; 2000 | pequeña | -75 | 6,43 | 787 | 0,93 | 85 / 63 | 0,30 | crítica | 0,24 |
| gi_bleed_57m; 2000 | moderada | -150 | 6,16 | 712 | 0,86 | 81 / 61 | 0,27 | crítica | 0,33 |
| gi_bleed_57m; 2000 | grave continua | -300 | 5,62 | 562 | 0,70 | 74 / 56 | 0,20 | crítica | 0,50 |
| gi_bleed_57m; 2000 | muy grave o prolongada | -600 | 4,54 | 262 | 0,35 | 46 / 35 | 0,08 | crítica | 0,80 |
| gi_bleed_72f; 833 | pequeña | -75 | 6,13 | 423 | 0,88 | 93 / 70 | 0,29 | crítica | 0,28 |
| gi_bleed_72f; 833 | moderada | -150 | 5,86 | 348 | 0,76 | 87 / 66 | 0,24 | crítica | 0,41 |
| gi_bleed_72f; 833 | grave continua | -300 | 5,32 | 198 | 0,47 | 71 / 55 | 0,13 | crítica | 0,67 |
| gi_bleed_72f; 833 | muy grave o prolongada | -600 | 4,24 | — | 0,00 | — / — | 0,00 | crítica | 1,00 |
| gi_bleed_72f; 1500 | pequeña | -75 | 6,13 | 822 | 0,94 | 95 / 72 | 0,31 | crítica | 0,24 |
| gi_bleed_72f; 1500 | moderada | -150 | 5,86 | 747 | 0,87 | 92 / 70 | 0,27 | crítica | 0,32 |
| gi_bleed_72f; 1500 | grave continua | -300 | 5,32 | 597 | 0,73 | 86 / 65 | 0,21 | crítica | 0,48 |
| gi_bleed_72f; 1500 | muy grave o prolongada | -600 | 4,24 | 297 | 0,40 | 60 / 46 | 0,09 | crítica | 0,78 |
| gi_bleed_72f; 2000 | pequeña | -75 | 6,13 | 1121 | 0,95 | 96 / 73 | 0,31 | crítica | 0,22 |
| gi_bleed_72f; 2000 | moderada | -150 | 5,86 | 1046 | 0,90 | 94 / 71 | 0,28 | crítica | 0,30 |
| gi_bleed_72f; 2000 | grave continua | -300 | 5,32 | 896 | 0,80 | 89 / 68 | 0,23 | crítica | 0,43 |
| gi_bleed_72f; 2000 | muy grave o prolongada | -600 | 4,24 | 596 | 0,57 | 79 / 60 | 0,13 | crítica | 0,68 |

### 4.3 Cuadrícula λ × posición de llegada (desde la llegada de 57m)

λ es una convención de unidades (§4.8): con las entradas fijas, cada fila es una razón sangrado/λ y unidad/λ, indicadas junto a λ. Cada celda: minutos de este sangrado hasta perder la mitad del gasto / hasta el flujo cero; gasto tras 1 unidad de GR; región. Criterio DE LA SONDA (minutos del literal heredado de sangrado; no son números docentes): demasiado sensible si el ancla pequeña (30 min) quita más de un cuarto del gasto o el flujo cero llega antes del ancla grave (120 min); demasiado insensible si el gasto sigue > 0,9 tras el ancla muy grave (240 min). Ventana de EJEMPLO, no propuesta: mitad del gasto en 120–240 min.

| λ \ posición | 0,20 | 0,25 | 0,30 | 0,35 | 0,40 | 0,45 | 0,50 | 0,60 | 0,70 |
|---|---|---|---|---|---|---|---|---|---|
| 833 (0,0030/min; 0,36) | 39 / 74; 2,21; S< | 51 / 96; 1,91; S< | 65 / 119; 1,71; S< | 79 / 144; 1,56; ·< | 96 / 170; 1,45; ·< | 114 / 199; 1,37; ·< | 135 / 231; 1,30; ·= | 187 / 305; 1,20; ·= | 258 / 401; 1,13; ·> |
| 1000 (0,0025/min; 0,30) | 47 / 89; 2,04; S< | 62 / 115; 1,78; S< | 78 / 143; 1,60; ·< | 95 / 172; 1,48; ·< | 115 / 204; 1,39; ·< | 137 / 239; 1,32; ·= | 162 / 277; 1,26; ·= | 224 / 367; 1,17; ·= | 309 / 482; 1,11; ·> |
| 1250 (0,0020/min; 0,24) | 59 / 112; 1,85; S< | 77 / 144; 1,64; ·< | 97 / 178; 1,50; ·< | 119 / 215; 1,40; ·< | 144 / 255; 1,32; ·= | 171 / 299; 1,26; ·= | 203 / 347; 1,21; ·= | 280 / 458; 1,14; ·> | 387 / 602; 1,09; ·> |
| 1500 (0,0017/min; 0,20) | 71 / 134; 1,73; ·< | 92 / 173; 1,54; ·< | 116 / 214; 1,42; ·< | 143 / 258; 1,34; ·= | 173 / 306; 1,27; ·= | 206 / 359; 1,22; ·= | 243 / 416; 1,18; ·> | 336 / 550; 1,12; ·> | 464 / 722; 1,08; ·> |
| 1750 (0,0014/min; 0,17) | 82 / 156; 1,63; ·< | 108 / 201; 1,47; ·< | 136 / 250; 1,37; ·= | 167 / 302; 1,29; ·= | 201 / 358; 1,24; ·= | 240 / 418; 1,19; ·> | 284 / 485; 1,16; ·> | 392 / 641; 1,11; ·> | 541 / 843; 1,07; ·> |
| 2000 (0,0013/min; 0,15) | 94 / 179; 1,56; ·< | 123 / 230; 1,42; ·= | 155 / 285; 1,33; ·= | 191 / 345; 1,26; ·= | 230 / 409; 1,21; ·= | 274 / 478; 1,17; ·> | 324 / 555; 1,14; ·> | 448 / 733; 1,09; ·> | 619 / 963; 1,06; ·> |
| 2500 (0,0010/min; 0,12) | 118 / 223; 1,45; ·< | 154 / 288; 1,34; ·= | 194 / 357; 1,26; ·= | 238 / 431; 1,21; ·= | 288 / 511; 1,17; ·> | 343 / 598; 1,14; ·> | 405 / 693; 1,11; ·> | 560 / 916; 1,08; ·> | 773 / 1204; 1,05; ·> |
| 3000 (0,0008/min; 0,10) | 141 / 268; 1,38; ·= | 185 / 345; 1,29; ·= | 233 / 428; 1,22; ·= | 286 / 517; 1,18; ·> | 345 / 613; 1,14; ·> | 412 / 717; 1,12; ·> | 487 / 832; 1,10; ·> | 672 / 1100; 1,06; ·> | 928 / 1445; 1,04; I> |

Claves: S demasiado sensible y I demasiado insensible según el criterio de la sonda, · requiere un ancla docente; < más rápida, = dentro, > más lenta que la ventana de ejemplo.

| λ \ posición (gasto tras las anclas pequeña · moderada · grave · muy grave; DO2 tras la grave) | 0,20 | 0,25 | 0,30 | 0,35 | 0,40 | 0,45 | 0,50 | 0,60 | 0,70 |
|---|---|---|---|---|---|---|---|---|---|
| 833 | 0,62 · 0,21 · 0,00 · 0,00; 0,00 | 0,72 · 0,41 · 0,00 · 0,00; 0,00 | 0,78 · 0,54 · 0,00 · 0,00; 0,00 | 0,83 · 0,63 · 0,20 · 0,00; 0,06 | 0,86 · 0,70 · 0,35 · 0,00; 0,10 | 0,88 · 0,76 · 0,47 · 0,00; 0,13 | 0,91 · 0,80 · 0,57 · 0,00; 0,16 | 0,94 · 0,87 · 0,71 · 0,30; 0,20 | 0,96 · 0,92 · 0,81 · 0,55; 0,23 |
| 1000 | 0,69 · 0,35 · 0,00 · 0,00; 0,00 | 0,77 · 0,51 · 0,00 · 0,00; 0,00 | 0,82 · 0,62 · 0,18 · 0,00; 0,05 | 0,86 · 0,70 · 0,35 · 0,00; 0,10 | 0,88 · 0,76 · 0,48 · 0,00; 0,14 | 0,90 · 0,80 · 0,57 · 0,00; 0,16 | 0,92 · 0,84 · 0,65 · 0,18; 0,19 | 0,95 · 0,89 · 0,77 · 0,45; 0,22 | 0,97 · 0,93 · 0,85 · 0,65; 0,24 |
| 1250 | 0,75 · 0,49 · 0,00 · 0,00; 0,00 | 0,81 · 0,62 · 0,19 · 0,00; 0,05 | 0,86 · 0,70 · 0,37 · 0,00; 0,10 | 0,89 · 0,76 · 0,50 · 0,00; 0,14 | 0,91 · 0,81 · 0,59 · 0,08; 0,17 | 0,92 · 0,84 · 0,67 · 0,25; 0,19 | 0,94 · 0,87 · 0,73 · 0,38; 0,21 | 0,96 · 0,92 · 0,82 · 0,59; 0,23 | 0,97 · 0,95 · 0,88 · 0,74; 0,25 |
| 1500 | 0,79 · 0,58 · 0,11 · 0,00; 0,03 | 0,85 · 0,68 · 0,34 · 0,00; 0,10 | 0,88 · 0,75 · 0,48 · 0,00; 0,14 | 0,90 · 0,80 · 0,59 · 0,09; 0,17 | 0,92 · 0,84 · 0,67 · 0,26; 0,19 | 0,94 · 0,87 · 0,73 · 0,40; 0,21 | 0,95 · 0,89 · 0,78 · 0,51; 0,22 | 0,97 · 0,93 · 0,85 · 0,67; 0,24 | 0,98 · 0,95 · 0,91 · 0,79; 0,26 |
| 1750 | 0,82 · 0,64 · 0,25 · 0,00; 0,07 | 0,87 · 0,73 · 0,44 · 0,00; 0,13 | 0,90 · 0,79 · 0,56 · 0,05; 0,16 | 0,92 · 0,83 · 0,65 · 0,24; 0,19 | 0,93 · 0,87 · 0,72 · 0,39; 0,21 | 0,95 · 0,89 · 0,77 · 0,50; 0,22 | 0,96 · 0,91 · 0,81 · 0,59; 0,23 | 0,97 · 0,94 · 0,88 · 0,73; 0,25 | 0,98 · 0,96 · 0,92 · 0,82; 0,26 |
| 2000 | 0,85 · 0,69 · 0,35 · 0,00; 0,10 | 0,89 · 0,77 · 0,51 · 0,00; 0,15 | 0,91 · 0,82 · 0,62 · 0,18; 0,18 | 0,93 · 0,86 · 0,70 · 0,35; 0,20 | 0,94 · 0,88 · 0,76 · 0,48; 0,22 | 0,95 · 0,90 · 0,80 · 0,57; 0,23 | 0,96 · 0,92 · 0,84 · 0,65; 0,24 | 0,97 · 0,95 · 0,89 · 0,77; 0,25 | 0,98 · 0,97 · 0,93 · 0,85; 0,27 |
| 2500 | 0,88 · 0,75 · 0,49 · 0,00; 0,14 | 0,91 · 0,81 · 0,62 · 0,19; 0,18 | 0,93 · 0,86 · 0,70 · 0,37; 0,20 | 0,94 · 0,89 · 0,76 · 0,50; 0,22 | 0,95 · 0,91 · 0,81 · 0,59; 0,23 | 0,96 · 0,92 · 0,84 · 0,67; 0,24 | 0,97 · 0,94 · 0,87 · 0,73; 0,25 | 0,98 · 0,96 · 0,92 · 0,82; 0,26 | 0,99 · 0,97 · 0,95 · 0,88; 0,27 |
| 3000 | 0,90 · 0,79 · 0,58 · 0,11; 0,17 | 0,92 · 0,85 · 0,68 · 0,34; 0,20 | 0,94 · 0,88 · 0,75 · 0,48; 0,22 | 0,95 · 0,90 · 0,80 · 0,59; 0,23 | 0,96 · 0,92 · 0,84 · 0,67; 0,24 | 0,97 · 0,94 · 0,87 · 0,73; 0,25 | 0,97 · 0,95 · 0,89 · 0,78; 0,26 | 0,98 · 0,97 · 0,93 · 0,85; 0,27 | 0,99 · 0,98 · 0,95 · 0,91; 0,27 |

### 4.4 Trayectorias con el sangrado GI desde llegadas sintéticas (llegada sana, DO2 normal)

| Llegada; λ | 0 min: gasto, DO2, estado | 60 min: gasto, DO2, estado | 120 min: gasto, DO2, estado | 180 min: gasto, DO2, estado | 240 min: gasto, DO2, estado | Primer min crítico | Gasto ≤ 0,5 desde | Flujo cero |
|---|---|---|---|---|---|---|---|---|
| precarga normal (0,70); 833 | 1,00, 1,00, adecuada | 0,92, 0,88, compensada | 0,81, 0,75, compensada | 0,69, 0,61, compensada | 0,55, 0,46, compensada | — | — | — |
| precarga normal (0,70); 1500 | 1,00, 1,00, adecuada | 0,95, 0,92, compensada | 0,91, 0,83, compensada | 0,85, 0,74, compensada | 0,79, 0,66, compensada | — | — | — |
| precarga normal (0,70); 2000 | 1,00, 1,00, adecuada | 0,97, 0,93, compensada | 0,93, 0,85, compensada | 0,89, 0,78, compensada | 0,85, 0,71, compensada | — | — | — |
| infrallenado (0,35); 833 | 1,00, 1,00, adecuada | 0,63, 0,61, compensada | 0,20, 0,18, crítica | — | — | min 90 | min 80 | min 144 |
| infrallenado (0,35); 1500 | 1,00, 1,00, adecuada | 0,80, 0,77, compensada | 0,59, 0,54, compensada | 0,35, 0,31, crítica | 0,09, 0,07, crítica | min 157 | min 144 | — |
| infrallenado (0,35); 2000 | 1,00, 1,00, adecuada | 0,86, 0,82, compensada | 0,70, 0,64, compensada | 0,53, 0,47, compensada | 0,35, 0,29, crítica | min 203 | min 191 | — |
| infrallenado grave (0,20); 833 | 1,00, 1,00, adecuada | 0,21, 0,20, crítica | — | — | — | min 46 | min 40 | min 75 |
| infrallenado grave (0,20); 1500 | 1,00, 1,00, adecuada | 0,58, 0,56, compensada | 0,11, 0,10, crítica | — | — | min 81 | min 71 | min 134 |
| infrallenado grave (0,20); 2000 | 1,00, 1,00, adecuada | 0,69, 0,66, compensada | 0,35, 0,32, crítica | — | — | min 107 | min 95 | min 179 |
| bomba deprimida (0,35; P a 0,7 en 10 min); 833 | 1,00, 1,00, adecuada | 0,46, 0,44, compensada | 0,15, 0,13, crítica | — | — | min 69 | min 51 | min 144 |
| bomba deprimida (0,35; P a 0,7 en 10 min); 1500 | 1,00, 1,00, adecuada | 0,57, 0,55, compensada | 0,43, 0,39, crítica | 0,26, 0,23, crítica | 0,07, 0,05, crítica | min 118 | min 92 | — |
| bomba deprimida (0,35; P a 0,7 en 10 min); 2000 | 1,00, 1,00, adecuada | 0,61, 0,58, compensada | 0,50, 0,46, compensada | 0,39, 0,34, crítica | 0,26, 0,22, crítica | min 151 | min 122 | — |

### 4.5 Transfusión sin sangrado (1 unidad en 30 min, 2 en 60), por λ y volumen por unidad

| Caso | Unidades | λ | mL-eq por unidad | V | Hb | Gasto | PAS | DO2 (antes → después) | Estado |
|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m | 1 | 833 | 300 | +300 | 6,70 → 7,55 | 1,56 | 113 | 0,34 → 0,60 | compensada |
| gi_bleed_57m | 1 | 833 | 200 | +200 | 6,70 → 7,55 | 1,40 | 106 | 0,34 → 0,53 | compensada |
| gi_bleed_57m | 1 | 833 | 120 | +120 | 6,70 → 7,55 | 1,25 | 99 | 0,34 → 0,48 | compensada |
| gi_bleed_57m | 1 | 1500 | 300 | +300 | 6,70 → 7,55 | 1,34 | 103 | 0,34 → 0,51 | compensada |
| gi_bleed_57m | 1 | 1500 | 200 | +200 | 6,70 → 7,55 | 1,23 | 98 | 0,34 → 0,47 | compensada |
| gi_bleed_57m | 1 | 1500 | 120 | +120 | 6,70 → 7,55 | 1,14 | 94 | 0,34 → 0,44 | compensada |
| gi_bleed_57m | 1 | 2000 | 300 | +300 | 6,70 → 7,55 | 1,26 | 100 | 0,34 → 0,48 | compensada |
| gi_bleed_57m | 1 | 2000 | 200 | +200 | 6,70 → 7,55 | 1,18 | 96 | 0,34 → 0,45 | compensada |
| gi_bleed_57m | 1 | 2000 | 120 | +120 | 6,70 → 7,55 | 1,11 | 93 | 0,34 → 0,42 | compensada |
| gi_bleed_57m | 2 | 833 | 300 | +600 | 6,70 → 8,40 | 1,95 | 131 | 0,34 → 0,83 | compensada |
| gi_bleed_57m | 2 | 833 | 200 | +400 | 6,70 → 8,40 | 1,71 | 120 | 0,34 → 0,73 | compensada |
| gi_bleed_57m | 2 | 833 | 120 | +240 | 6,70 → 8,40 | 1,46 | 109 | 0,34 → 0,62 | compensada |
| gi_bleed_57m | 2 | 1500 | 300 | +600 | 6,70 → 8,40 | 1,61 | 116 | 0,34 → 0,69 | compensada |
| gi_bleed_57m | 2 | 1500 | 200 | +400 | 6,70 → 8,40 | 1,43 | 108 | 0,34 → 0,61 | compensada |
| gi_bleed_57m | 2 | 1500 | 120 | +240 | 6,70 → 8,40 | 1,27 | 100 | 0,34 → 0,54 | compensada |
| gi_bleed_57m | 2 | 2000 | 300 | +600 | 6,70 → 8,40 | 1,48 | 110 | 0,34 → 0,63 | compensada |
| gi_bleed_57m | 2 | 2000 | 200 | +400 | 6,70 → 8,40 | 1,34 | 103 | 0,34 → 0,57 | compensada |
| gi_bleed_57m | 2 | 2000 | 120 | +240 | 6,70 → 8,40 | 1,21 | 97 | 0,34 → 0,52 | compensada |
| gi_bleed_72f | 1 | 833 | 300 | +300 | 6,40 → 7,25 | 1,37 | 115 | 0,34 → 0,53 | compensada |
| gi_bleed_72f | 1 | 833 | 200 | +200 | 6,40 → 7,25 | 1,26 | 110 | 0,34 → 0,49 | compensada |
| gi_bleed_72f | 1 | 833 | 120 | +120 | 6,40 → 7,25 | 1,16 | 105 | 0,34 → 0,45 | compensada |
| gi_bleed_72f | 1 | 1500 | 300 | +300 | 6,40 → 7,25 | 1,22 | 108 | 0,34 → 0,47 | compensada |
| gi_bleed_72f | 1 | 1500 | 200 | +200 | 6,40 → 7,25 | 1,15 | 105 | 0,34 → 0,44 | compensada |
| gi_bleed_72f | 1 | 1500 | 120 | +120 | 6,40 → 7,25 | 1,09 | 102 | 0,34 → 0,42 | compensada |
| gi_bleed_72f | 1 | 2000 | 300 | +300 | 6,40 → 7,25 | 1,17 | 106 | 0,34 → 0,45 | compensada |
| gi_bleed_72f | 1 | 2000 | 200 | +200 | 6,40 → 7,25 | 1,12 | 103 | 0,34 → 0,43 | compensada |
| gi_bleed_72f | 1 | 2000 | 120 | +120 | 6,40 → 7,25 | 1,07 | 101 | 0,34 → 0,41 | compensada |
| gi_bleed_72f | 2 | 833 | 300 | +600 | 6,40 → 8,10 | 1,63 | 126 | 0,34 → 0,70 | compensada |
| gi_bleed_72f | 2 | 833 | 200 | +400 | 6,40 → 8,10 | 1,47 | 119 | 0,34 → 0,63 | compensada |
| gi_bleed_72f | 2 | 833 | 120 | +240 | 6,40 → 8,10 | 1,31 | 112 | 0,34 → 0,56 | compensada |
| gi_bleed_72f | 2 | 1500 | 300 | +600 | 6,40 → 8,10 | 1,40 | 116 | 0,34 → 0,60 | compensada |
| gi_bleed_72f | 2 | 1500 | 200 | +400 | 6,40 → 8,10 | 1,29 | 111 | 0,34 → 0,55 | compensada |
| gi_bleed_72f | 2 | 1500 | 120 | +240 | 6,40 → 8,10 | 1,18 | 106 | 0,34 → 0,51 | compensada |
| gi_bleed_72f | 2 | 2000 | 300 | +600 | 6,40 → 8,10 | 1,32 | 112 | 0,34 → 0,57 | compensada |
| gi_bleed_72f | 2 | 2000 | 200 | +400 | 6,40 → 8,10 | 1,22 | 108 | 0,34 → 0,53 | compensada |
| gi_bleed_72f | 2 | 2000 | 120 | +240 | 6,40 → 8,10 | 1,14 | 104 | 0,34 → 0,49 | compensada |

Atribución del aumento de gasto en L3 (2 unidades, IBP, hemostasia a los 60 min): gasto máximo por λ y volumen por unidad; y, con λ 833, moviendo sólo la razón unidad/λ, sólo la razón sangrado/λ o ambas al valor que daría otra λ.

| Caso | λ | 300 mL-eq | 200 mL-eq | 120 mL-eq |
|---|---|---|---|---|
| gi_bleed_57m | 833 | 1,82 | 1,53 | 1,25 |
| gi_bleed_57m | 1500 | 1,51 | 1,32 | 1,14 |
| gi_bleed_57m | 2000 | 1,40 | 1,24 | 1,11 |
| gi_bleed_72f | 833 | 1,54 | 1,35 | 1,17 |
| gi_bleed_72f | 1500 | 1,34 | 1,21 | 1,10 |
| gi_bleed_72f | 2000 | 1,26 | 1,16 | 1,07 |

| Caso | Razones de la λ | Sólo unidad/λ | Sólo sangrado/λ | Ambas |
|---|---|---|---|---|
| gi_bleed_57m | 1500 | 1,42 | 1,88 | 1,51 |
| gi_bleed_57m | 2000 | 1,27 | 1,90 | 1,40 |
| gi_bleed_72f | 1500 | 1,28 | 1,58 | 1,34 |
| gi_bleed_72f | 2000 | 1,18 | 1,59 | 1,26 |

### 4.6 Cristaloide solo (en 20 min), con y sin sangrado

| Caso; volumen; sangrado; λ | Pico de gasto (min) | 0 min: gasto, Hb, DO2 | 20 min: gasto, Hb, DO2 | 60 min: gasto, Hb, DO2 | 120 min: gasto, Hb, DO2 |
|---|---|---|---|---|---|
| gi_bleed_57m; 1000 mL; sin sangrado; 833 | 1,22 (20) | 1,00, 6,70, 0,34 | 1,22, 6,10, 0,38 | 1,14, 6,10, 0,35 | 1,11, 6,10, 0,34 |
| gi_bleed_57m; 1000 mL; sin sangrado; 1500 | 1,12 (20) | 1,00, 6,70, 0,34 | 1,12, 6,10, 0,35 | 1,08, 6,10, 0,33 | 1,06, 6,10, 0,33 |
| gi_bleed_57m; 1000 mL; sin sangrado; 2000 | 1,09 (20) | 1,00, 6,70, 0,34 | 1,09, 6,10, 0,34 | 1,06, 6,10, 0,33 | 1,05, 6,10, 0,32 |
| gi_bleed_57m; 1000 mL; con sangrado; 833 | 1,12 (20) | 1,00, 6,70, 0,34 | 1,12, 5,92, 0,34 | 0,80, 5,56, 0,23 | 0,36, 5,02, 0,09 |
| gi_bleed_57m; 1000 mL; con sangrado; 1500 | 1,07 (20) | 1,00, 6,70, 0,34 | 1,07, 5,92, 0,32 | 0,89, 5,56, 0,25 | 0,67, 5,02, 0,17 |
| gi_bleed_57m; 1000 mL; con sangrado; 2000 | 1,05 (20) | 1,00, 6,70, 0,34 | 1,05, 5,92, 0,32 | 0,92, 5,56, 0,26 | 0,75, 5,02, 0,19 |
| gi_bleed_57m; 2000 mL; sin sangrado; 833 | 1,41 (20) | 1,00, 6,70, 0,34 | 1,41, 5,50, 0,39 | 1,27, 5,50, 0,35 | 1,22, 5,50, 0,34 |
| gi_bleed_57m; 2000 mL; sin sangrado; 1500 | 1,24 (20) | 1,00, 6,70, 0,34 | 1,24, 5,50, 0,35 | 1,15, 5,50, 0,32 | 1,12, 5,50, 0,31 |
| gi_bleed_57m; 2000 mL; sin sangrado; 2000 | 1,18 (20) | 1,00, 6,70, 0,34 | 1,18, 5,50, 0,33 | 1,12, 5,50, 0,31 | 1,09, 5,50, 0,31 |
| gi_bleed_57m; 2000 mL; con sangrado; 833 | 1,32 (20) | 1,00, 6,70, 0,34 | 1,32, 5,32, 0,36 | 0,95, 4,96, 0,24 | 0,51, 4,42, 0,11 |
| gi_bleed_57m; 2000 mL; con sangrado; 1500 | 1,19 (20) | 1,00, 6,70, 0,34 | 1,19, 5,32, 0,32 | 0,97, 4,96, 0,24 | 0,74, 4,42, 0,17 |
| gi_bleed_57m; 2000 mL; con sangrado; 2000 | 1,14 (20) | 1,00, 6,70, 0,34 | 1,14, 5,32, 0,31 | 0,98, 4,96, 0,25 | 0,81, 4,42, 0,18 |
| gi_bleed_72f; 1000 mL; sin sangrado; 833 | 1,14 (20) | 1,00, 6,40, 0,34 | 1,14, 5,80, 0,35 | 1,09, 5,80, 0,34 | 1,07, 5,80, 0,33 |
| gi_bleed_72f; 1000 mL; sin sangrado; 1500 | 1,08 (20) | 1,00, 6,40, 0,34 | 1,08, 5,80, 0,33 | 1,05, 5,80, 0,32 | 1,04, 5,80, 0,32 |
| gi_bleed_72f; 1000 mL; sin sangrado; 2000 | 1,06 (20) | 1,00, 6,40, 0,34 | 1,06, 5,80, 0,33 | 1,04, 5,80, 0,32 | 1,03, 5,80, 0,32 |
| gi_bleed_72f; 1000 mL; con sangrado; 833 | 1,08 (20) | 1,00, 6,40, 0,34 | 1,08, 5,62, 0,32 | 0,87, 5,26, 0,24 | 0,58, 4,72, 0,14 |
| gi_bleed_72f; 1000 mL; con sangrado; 1500 | 1,04 (20) | 1,00, 6,40, 0,34 | 1,04, 5,62, 0,31 | 0,93, 5,26, 0,26 | 0,78, 4,72, 0,20 |
| gi_bleed_72f; 1000 mL; con sangrado; 2000 | 1,03 (20) | 1,00, 6,40, 0,34 | 1,03, 5,62, 0,31 | 0,95, 5,26, 0,26 | 0,84, 4,72, 0,21 |
| gi_bleed_72f; 2000 mL; sin sangrado; 833 | 1,27 (20) | 1,00, 6,40, 0,34 | 1,27, 5,20, 0,35 | 1,17, 5,20, 0,32 | 1,14, 5,20, 0,32 |
| gi_bleed_72f; 2000 mL; sin sangrado; 1500 | 1,16 (20) | 1,00, 6,40, 0,34 | 1,16, 5,20, 0,32 | 1,10, 5,20, 0,30 | 1,08, 5,20, 0,30 |
| gi_bleed_72f; 2000 mL; sin sangrado; 2000 | 1,12 (20) | 1,00, 6,40, 0,34 | 1,12, 5,20, 0,31 | 1,08, 5,20, 0,30 | 1,06, 5,20, 0,29 |
| gi_bleed_72f; 2000 mL; con sangrado; 833 | 1,21 (20) | 1,00, 6,40, 0,34 | 1,21, 5,02, 0,32 | 0,97, 4,66, 0,24 | 0,68, 4,12, 0,15 |
| gi_bleed_72f; 2000 mL; con sangrado; 1500 | 1,12 (20) | 1,00, 6,40, 0,34 | 1,12, 5,02, 0,30 | 0,98, 4,66, 0,24 | 0,83, 4,12, 0,18 |
| gi_bleed_72f; 2000 mL; con sangrado; 2000 | 1,09 (20) | 1,00, 6,40, 0,34 | 1,09, 5,02, 0,29 | 0,99, 4,66, 0,24 | 0,87, 4,12, 0,19 |

### 4.7 Prototipo de un solo sangrado (FUERA del núcleo; ilustración, mezcla 4 L, sangrado hasta el min 120)

| Prototipo | 0 min: V, Hb | 60 min: V, Hb | 120 min: V, Hb | 180 min: V, Hb | 240 min: V, Hb |
|---|---|---|---|---|---|
| pérdida de sangre = literal de V, sin relleno | 0, 6,70 | -150, 6,70 | -300, 6,70 | -300, 6,70 | -300, 6,70 |
| pérdida de sangre = literal de V, relleno τ 60 | 0, 6,70 | -94, 6,61 | -129, 6,41 | -47, 6,28 | -17, 6,23 |
| pérdida coherente con la Hb (8 mL/min), relleno τ 60 | 0, 6,70 | -301, 6,39 | -412, 5,77 | -151, 5,38 | -56, 5,25 |

### 4.8 λ es una convención de unidades

Con λ y todas las entradas de V duplicadas, L1, L2 y L3 de ambos casos no cambian: diferencia máxima de gasto, DO2 o D = 0,000. Con la λ actual, las razones son exactamente los literales heredados: sangrado/λ 0,0030 por min, unidad/λ 0,36, salino/λ 0,00015 por mL.

Distancia al flujo cero fija en 359 mL-eq (la de 57m hoy), con λ y la posición cambiando juntas:

| λ | Posición | Gasto tras las anclas pequeña · moderada · grave · muy grave | Mitad del gasto (min) | Gasto tras 2 unidades |
|---|---|---|---|---|
| 600 | 0,450 | 0,84 · 0,65 · 0,21 · 0,00 | 82 | 1,77 |
| 833 | 0,350 | 0,83 · 0,63 · 0,20 · 0,00 | 79 | 1,95 |
| 1500 | 0,213 | 0,81 · 0,61 · 0,18 · 0,00 | 76 | 2,22 |
| 3000 | 0,113 | 0,80 · 0,60 · 0,17 · 0,00 | 74 | 2,43 |

### 4.9 Envolventes GI para la docencia (por λ y posición de llegada)

| Caso; λ; posición | Flujo cero | Sin tratar 30 · 60 · 120 min: gasto (PAS/PAM) DO2 déficit | Manejo definitivo 60 · 120 min: gasto, Hb, DO2, déficit |
|---|---|---|---|
| gi_bleed_57m; 833; 0,20 (inferior) | 186 | 0,62 (71/53) 0,20 0,49 · 0,21 (28/21) 0,07 0,84 · — | 2,76, 7,97, 1,12, 0,00 · 2,72, 7,92, 1,09, 0,00 |
| gi_bleed_57m; 833; 0,35 (media) | 359 | 0,83 (80/60) 0,27 0,33 · 0,63 (72/54) 0,20 0,50 · 0,20 (26/19) 0,06 0,86 | 1,82, 7,97, 0,73, 0,00 · 1,80, 7,92, 0,72, 0,00 |
| gi_bleed_57m; 833; 0,50 (superior) | 578 | 0,91 (84/62) 0,30 0,26 · 0,80 (79/59) 0,25 0,37 · 0,57 (69/52) 0,16 0,60 | 1,44, 7,97, 0,58, 0,00 · 1,43, 7,92, 0,57, 0,00 |
| gi_bleed_57m; 1250; 0,20 (inferior) | 279 | 0,75 (77/58) 0,25 0,39 · 0,49 (64/49) 0,15 0,62 · — | 2,28, 7,97, 0,92, 0,00 · 2,25, 7,92, 0,90, 0,00 |
| gi_bleed_57m; 1250; 0,35 (media) | 538 | 0,89 (83/62) 0,29 0,28 · 0,76 (77/58) 0,24 0,40 · 0,50 (65/49) 0,14 0,65 | 1,59, 7,97, 0,65, 0,00 · 1,58, 7,92, 0,63, 0,00 |
| gi_bleed_57m; 1250; 0,50 (superior) | 866 | 0,94 (85/63) 0,31 0,23 · 0,87 (82/61) 0,27 0,32 · 0,73 (76/57) 0,21 0,48 | 1,32, 7,97, 0,53, 0,00 · 1,31, 7,92, 0,53, 0,00 |
| gi_bleed_57m; 1500; 0,20 (inferior) | 335 | 0,79 (79/59) 0,26 0,35 · 0,58 (69/52) 0,18 0,55 · 0,11 (15/11) 0,03 0,92 | 2,10, 7,97, 0,85, 0,00 · 2,07, 7,92, 0,83, 0,00 |
| gi_bleed_57m; 1500; 0,35 (media) | 646 | 0,90 (84/62) 0,30 0,26 · 0,80 (79/59) 0,25 0,37 · 0,59 (69/52) 0,17 0,58 | 1,51, 7,97, 0,61, 0,00 · 1,50, 7,92, 0,60, 0,00 |
| gi_bleed_57m; 1500; 0,50 (superior) | 1040 | 0,95 (86/64) 0,31 0,23 · 0,89 (83/62) 0,28 0,30 · 0,78 (78/58) 0,22 0,44 | 1,27, 7,97, 0,52, 0,00 · 1,27, 7,92, 0,51, 0,00 |
| gi_bleed_57m; 2000; 0,20 (inferior) | 446 | 0,85 (81/60) 0,28 0,31 · 0,69 (74/55) 0,22 0,46 · 0,35 (46/35) 0,10 0,75 | 1,86, 7,97, 0,75, 0,00 · 1,83, 7,92, 0,74, 0,00 |
| gi_bleed_57m; 2000; 0,35 (media) | 862 | 0,93 (85/63) 0,30 0,24 · 0,86 (81/61) 0,27 0,33 · 0,70 (74/56) 0,20 0,50 | 1,40, 7,97, 0,57, 0,00 · 1,39, 7,92, 0,56, 0,00 |
| gi_bleed_57m; 2000; 0,50 (superior) | 1386 | 0,96 (86/64) 0,31 0,22 · 0,92 (84/63) 0,29 0,28 · 0,84 (81/60) 0,24 0,40 | 1,21, 7,97, 0,49, 0,00 · 1,21, 7,92, 0,49, 0,00 |
| gi_bleed_57m; 2500; 0,20 (inferior) | 558 | 0,88 (83/61) 0,29 0,28 · 0,75 (77/58) 0,24 0,41 · 0,49 (64/49) 0,14 0,65 | 1,70, 7,97, 0,69, 0,00 · 1,68, 7,92, 0,68, 0,00 |
| gi_bleed_57m; 2500; 0,35 (media) | 1077 | 0,94 (85/64) 0,31 0,23 · 0,89 (83/62) 0,28 0,31 · 0,76 (77/58) 0,22 0,46 | 1,33, 7,97, 0,54, 0,00 · 1,32, 7,92, 0,53, 0,00 |
| gi_bleed_57m; 2500; 0,50 (superior) | 1733 | 0,97 (87/64) 0,32 0,21 · 0,94 (85/63) 0,29 0,27 · 0,87 (82/61) 0,25 0,38 | 1,18, 7,97, 0,48, 0,00 · 1,17, 7,92, 0,47, 0,00 |
| gi_bleed_72f; 833; 0,30 (inferior) | 297 | 0,78 (88/67) 0,25 0,36 · 0,54 (77/59) 0,17 0,58 · — | 2,02, 7,67, 0,83, 0,00 · 2,00, 7,62, 0,81, 0,00 |
| gi_bleed_72f; 833; 0,45 (media) | 498 | 0,88 (93/70) 0,29 0,28 · 0,76 (87/66) 0,24 0,41 · 0,47 (71/55) 0,13 0,67 | 1,54, 7,67, 0,63, 0,00 · 1,52, 7,62, 0,62, 0,00 |
| gi_bleed_72f; 833; 0,60 (superior) | 764 | 0,94 (95/72) 0,31 0,24 · 0,87 (92/70) 0,27 0,32 · 0,71 (85/65) 0,20 0,50 | 1,29, 7,67, 0,53, 0,00 · 1,29, 7,62, 0,52, 0,00 |
| gi_bleed_72f; 1250; 0,30 (inferior) | 446 | 0,86 (92/69) 0,28 0,30 · 0,70 (85/65) 0,22 0,45 · 0,37 (55/43) 0,10 0,74 | 1,75, 7,67, 0,71, 0,00 · 1,73, 7,62, 0,70, 0,00 |
| gi_bleed_72f; 1250; 0,45 (media) | 747 | 0,92 (95/72) 0,30 0,25 · 0,84 (91/69) 0,26 0,34 · 0,67 (83/64) 0,19 0,53 | 1,39, 7,67, 0,57, 0,00 · 1,38, 7,62, 0,56, 0,00 |
| gi_bleed_72f; 1250; 0,60 (superior) | 1145 | 0,96 (96/73) 0,31 0,22 · 0,92 (94/71) 0,28 0,29 · 0,82 (90/68) 0,23 0,42 | 1,21, 7,67, 0,49, 0,00 · 1,21, 7,62, 0,49, 0,00 |
| gi_bleed_72f; 1500; 0,30 (inferior) | 535 | 0,88 (93/70) 0,29 0,28 · 0,75 (87/66) 0,23 0,41 · 0,48 (73/56) 0,14 0,66 | 1,64, 7,67, 0,67, 0,00 · 1,62, 7,62, 0,66, 0,00 |
| gi_bleed_72f; 1500; 0,45 (media) | 897 | 0,94 (95/72) 0,31 0,24 · 0,87 (92/70) 0,27 0,32 · 0,73 (86/65) 0,21 0,48 | 1,34, 7,67, 0,54, 0,00 · 1,33, 7,62, 0,54, 0,00 |
| gi_bleed_72f; 1500; 0,60 (superior) | 1374 | 0,97 (96/73) 0,31 0,21 · 0,93 (95/72) 0,29 0,28 · 0,85 (91/69) 0,24 0,40 | 1,18, 7,67, 0,48, 0,00 · 1,18, 7,62, 0,48, 0,00 |
| gi_bleed_72f; 2000; 0,30 (inferior) | 713 | 0,91 (94/71) 0,30 0,26 · 0,82 (90/68) 0,25 0,36 · 0,62 (81/62) 0,18 0,56 | 1,50, 7,67, 0,61, 0,00 · 1,49, 7,62, 0,60, 0,00 |
| gi_bleed_72f; 2000; 0,45 (media) | 1196 | 0,95 (96/73) 0,31 0,22 · 0,90 (94/71) 0,28 0,30 · 0,80 (89/68) 0,23 0,43 | 1,26, 7,67, 0,51, 0,00 · 1,25, 7,62, 0,51, 0,00 |
| gi_bleed_72f; 2000; 0,60 (superior) | 1833 | 0,97 (97/73) 0,32 0,21 · 0,95 (96/72) 0,30 0,26 · 0,89 (93/71) 0,25 0,37 | 1,14, 7,67, 0,47, 0,00 · 1,14, 7,62, 0,46, 0,00 |
| gi_bleed_72f; 2500; 0,30 (inferior) | 892 | 0,93 (95/72) 0,30 0,24 · 0,86 (92/69) 0,27 0,33 · 0,70 (85/65) 0,20 0,50 | 1,41, 7,67, 0,57, 0,00 · 1,40, 7,62, 0,57, 0,00 |
| gi_bleed_72f; 2500; 0,45 (media) | 1495 | 0,96 (96/73) 0,31 0,22 · 0,92 (95/72) 0,29 0,28 · 0,84 (91/69) 0,24 0,40 | 1,21, 7,67, 0,50, 0,00 · 1,21, 7,62, 0,49, 0,00 |
| gi_bleed_72f; 2500; 0,60 (superior) | 2291 | 0,98 (97/73) 0,32 0,20 · 0,96 (96/73) 0,30 0,25 · 0,92 (94/71) 0,26 0,35 | 1,12, 7,67, 0,46, 0,00 · 1,11, 7,62, 0,45, 0,00 |

<!-- /generado:hemorragia -->

## 5. Requisitos de respuesta (P2I-2S-3)

| Requisito docente | Resultado |
|---|---|
| 1. Una pérdida pequeña o modesta no colapsa el gasto de forma desproporcionada | Depende de la distancia al flujo cero x₀ = −λ·ln(1 − p₀). Con λ 833 y p₀ 0,2, el ancla pequeña ya quita el 38 % (claramente demasiado sensible). Con λ 833 y 0,35 quita el 17 %, y la moderada el 37 % |
| 2. La pérdida progresiva empeora progresivamente | Sí, en toda la cuadrícula (gasto monótono) |
| 3. El sangrado grave continuo puede producir shock profundo | Sí, desde llegadas infrallenadas. Desde la precarga normal (0,70), 240 min de este sangrado dejan un gasto de 0,55–0,85 según λ: el sangrado del módulo es moderado para un paciente euvolémico |
| 4. Aceleración al agotarse la reserva, sin un precipicio por una pérdida modesta | La forma acelera hacia el flujo cero. El «precipicio» sólo aparece donde x₀ es chico (λ ≤ 1250 con posiciones bajas) |
| 5. El infrallenado se deteriora antes | Sí: con λ 833, el gasto queda a la mitad a los 80 min (0,35) y no en 4 h (0,70; 258 min en la cuadrícula); con λ 1500, a los 144 min frente a ninguna en 4 h (§4.4) |
| 6. La bomba deprimida tolera menos | Sí, en términos absolutos: llega a crítica a los 118 min frente a 157 (λ 1500), y a los 69 frente a 90 (λ 833) |
| 7. La transfusión mejora el contenido de O2 y la precarga, sin una respuesta de PA fija | Mejora ambos (Hb +0,85/unidad y V +300). La PA sigue al gasto, no a un valor fijo. La magnitud depende de λ y del mapeo de volumen (§8) |
| 8. El cristaloide mejora la precarga sin restituir la Hb y puede diluirla | Sí: mejora transitoria del gasto (pico 1,12–1,41 con 2 L sin sangrado) con DO2 que no se restituye, por la Hb diluida. Pero la dilución no se revierte cuando el volumen se fuga (§1) |

## 6. Cuadrícula λ × posición (P2I-2S-4)

- **Métrica:** se informan en minutos de este sangrado (hasta la mitad del gasto y hasta el flujo cero), el gasto y el DO2 tras
  cada ancla, si sigue perfundiendo, y una segunda ancla: el gasto tras una unidad de glóbulos rojos.
- **Lectura de la cuadrícula:** con las entradas fijas, cada fila de λ es una pareja de razones (sangrado/λ, unidad/λ),
  indicada en la tabla. La cuadrícula es, en rigor, una cuadrícula de razones × posición.
- **Regiones, según el criterio de la sonda** (no son números docentes):
  - el criterio está en minutos del literal heredado de sangrado, así que restringe sangrado/λ y p₀, no λ;
  - además tiene bordes de filo: λ 833 con p₀ 0,30 cae «sensible» (flujo cero a los 119 min) y con 0,35 no (144 min);
  - **demasiado sensible:** el ancla pequeña quita más de un cuarto del gasto, o el flujo cero llega antes de las 2 h. Ocurre
    con sangrado/λ 0,003 (λ 833) y p₀ ≤ 0,30, con 0,0025 (λ 1000) y p₀ ≤ 0,25, y con 0,002 (λ 1250) y p₀ 0,20;
  - **demasiado insensible:** gasto > 0,9 tras 4 h sin tratar. Sólo con sangrado/λ 0,00083 (λ 3000) y p₀ 0,70;
  - **el resto requiere un ancla docente numérica.** Con los requisitos cualitativos no se puede trazar una región plausible
    más estrecha, ni siquiera para un paciente que ya llega en shock.
  - La ventana de **ejemplo** (mitad del gasto en 2–4 h desde la llegada de 57m) muestra cómo actuaría un ancla: una banda
    diagonal.
- **Identificabilidad (§4.8, distancia al flujo cero fija):**
  - la **pérdida** identifica la reserva de llegada en minutos de sangrado, x₀/sangrado. Con x₀ fijo, el gasto tras cada
    ancla cambia ≤ 0,04 y la mitad del gasto llega a los 74–82 min con cualquier λ (600–3000);
  - la **transfusión** sí distingue la curvatura, es decir la posición: con x₀ fijo, dos unidades dan un gasto de 1,77 a 2,43.
    Esa ancla funciona sólo si se conoce la razón unidad/sangrado;
  - ningún dato fija x₀ en mL-eq: sólo existen x₀/sangrado y x₀/unidad.
- **Decisión docente en dos anclas, ambas en términos de paciente:**
  1. cuánto tolera cada caso este sangrado: el tiempo hasta perder la mitad del gasto, o hasta un shock profundo;
  2. cuánto responde a una unidad de glóbulos rojos o a un volumen estándar.

  Con eso, junto con las posiciones POCUS, quedan fijadas las razones. Si se corrige el mapeo de la hemorragia (§11),
  cambian las entradas y, con ellas, las razones que cumplen las mismas anclas. **Decidir C antes que A.**

## 7. Trayectorias (P2I-2S-3, puntos 13–15; §4.4)

Las tres parten de la llegada sana con el sangrado GI del módulo:
- **Precarga normal (0,70):** compensada hasta las 4 h con todas las λ. El gasto queda en 0,55 (λ 833), 0,79 (1500) y 0,85
  (2000).
- **Infrallenado (0,35):** crítica a los 90 / 157 / 203 min (λ 833 / 1500 / 2000).
  - El flujo cero llega en el min 144 sólo con λ 833.
  - Con 0,20, la crítica llega a los 46 / 81 / 107 min, y el flujo cero a los 75 / 134 / 179 min.
- **Bomba deprimida (0,35, P a 0,7):** crítica a los 69 / 118 / 151 min, siempre antes que con la bomba normal.

## 8. Transfusión (P2I-2S-6; §4.5)

- **Sin sangrado, desde la llegada de 57m:**
  - 1 unidad: gasto 1,56 / 1,34 / 1,26 (λ 833 / 1500 / 2000), Hb 6,7 → 7,55, DO2 0,34 → 0,60 / 0,51 / 0,48, compensada;
  - 2 unidades: gasto 1,95 / 1,61 / 1,48, Hb 8,4, DO2 0,83 / 0,69 / 0,63.
- **Atribución del +82 % de L3 (57m): es una sola palanca, la razón unidad/λ = 0,36**, el literal heredado.
  - Con λ 833, llevar sólo unidad/λ al valor de λ 1500 baja el pico de 1,82 a 1,42.
  - Llevar sólo sangrado/λ lo sube a 1,88.
  - Llevar ambas da 1,51, igual que λ 1500.
- **Por qué pesa tanto:** en p₀ 0,35, dos unidades (600 mL-eq) cubren el 93 % de la distancia entre la llegada y la posición
  euvolémica de referencia (644 mL-eq).
- **Respuesta a la pregunta P2I-2S-6:** el +82 % viene de la sensibilidad de escala de la precarga a través de la razón de
  volumen de la transfusión. Con las entradas fijas, «λ» y «mapeo de volumen de la transfusión» son la misma cosa.
- **Recomendación:** no corregir la transfusión por separado. Derivar su efecto en V y en la Hb del volumen y del contenido de
  Hb de la unidad, dentro del mapeo común (§11), con el mismo factor que el sangrado.

## 9. Cristaloide (P2I-2S-7; §4.6)

- **Sin sangrado (57m):**
  - con 2 L, el gasto sube a 1,41 / 1,24 / 1,18 (λ 833 / 1500 / 2000) y baja hacia 1,22 / 1,12 / 1,09 a los 120 min;
  - la Hb cae a 5,5 y el DO2 no se restituye: con λ 833 pasa de 0,34 a 0,39 en el pico y vuelve a 0,34 a los 120 min; con
    λ 1500 y 2000 termina por debajo de la llegada (0,31);
  - es la mejora hemodinámica transitoria sin restitución de la capacidad de O2 que se esperaba.
- **Con sangrado continuo:** la mejora dura menos de una hora. A los 120 min el DO2 cae a 0,09–0,21, según el caso, el
  volumen y λ.
- **Defecto de mapeo, no de calibración:** la dilución no se revierte con la fuga.

## 10. Envolventes GI (P2I-2S-8; §4.9)

- **Sin tratar, 57m** (posición media; gasto a 30 · 60 · 120 min):
  - λ 833: 0,83 · 0,63 · 0,20;
  - λ 1500: 0,90 · 0,80 · 0,59;
  - λ 2000: 0,93 · 0,86 · 0,70.
  
  El DO2 a los 120 min va de 0,06 a 0,20, siempre crítico.
- **Sin tratar, 72f:** λ 833: 0,88 · 0,76 · 0,47; λ 1500: 0,94 · 0,87 · 0,73.
- **Manejo definitivo:** compensado a los 60 y 120 min en toda la cuadrícula.
  - El gasto va de 1,11 (72f superior, λ 2500) a 2,76 (57m inferior, λ 833), y el DO2 de 0,45 a 1,12.
  - Las combinaciones con x₀ chico dan las respuestas de transfusión más exageradas.
- **La PA sólo se muestra como contexto:** no fue objetivo de calibración.

## 11. Clasificación del mapeo de la hemorragia (P2I-2S-5)

**SHARED_HAEMORRHAGE_STATE_NEEDED.**

**Por qué no basta una corrección menor:**
- la coherencia exige que la Hb dependa del volumen y de su propia concentración, y que el relleno siga después de la
  hemostasia: la Hb baja con retraso;
- la dilución del cristaloide debe seguir al volumen que queda.

Todo eso requiere un estado de balance de volumen, no sólo otra constante.

**Estructura mínima propuesta (no implementada; se detiene aquí para la decisión docente):**
1. **Un solo sangrado:** pérdida de sangre entera b(t) = tasa × fracción de actividad, con la tasa del caso o de la familia (§12 D).
2. **Balance de volumen circulante relativo a la llegada:** C(t), que resta el sangrado y suma el volumen de las unidades, el
   cristaloide que queda (con la fuga actual) y el relleno.
3. **Hb por mezcla:**
   - masa de Hb / (volumen de mezcla de llegada + C);
   - el sangrado se lleva masa a la Hb actual, la unidad aporta su masa y el cristaloide no aporta;
   - así la dilución sigue al volumen que queda.
4. **Relleno de plasma** hacia un objetivo, con τ propio: la Hb sigue bajando tras la hemostasia y V se recupera en parte.
   El objetivo es una decisión docente: el volumen de llegada (que ya es hipovolémico, como en el prototipo) o uno euvolémico.
   Decide cuánto se «devuelve» una transfusión.
5. **V = κ × C, un único mapeo para todas las fuentes.** V sigue siendo la coordenada interna de precarga efectiva. Como λ es
   una convención de unidades, el único parámetro fisiológico del mapeo es κ/λ: la fracción de la escala de precarga que mueve
   cada mL de volumen circulante.

**Alternativa interina** (MINOR_MAPPING_CORRECTION, no recomendada como definitiva): derivar los cambios de Hb de los mismos
eventos de volumen, con un volumen de mezcla y una fracción de relleno instantánea.
- Es coherente en el punto de operación.
- No tiene retraso ni recuperación tras la hemostasia.

## 12. Opciones para la docencia (P2I-2S-10)

**A. «Región de λ»: no se propone ninguna.**
- λ es una convención de unidades. Lo que hay que decidir son las razones sangrado/λ, unidad/λ y salino/λ, junto con p₀.
  Hoy son los literales heredados.
- Se ofrece a la docencia:
  - **la cuadrícula** (§4.3), con las razones indicadas;
  - **las regiones excluidas según el criterio de la sonda**, condicionadas al literal de sangrado;
  - **las dos anclas en términos de paciente que las fijarían** (§6): la tolerancia de cada caso a este sangrado y la respuesta
    a una unidad o a un volumen.
- **Ventana de ejemplo, no propuesta:** si la docencia dijera «mitad del gasto en 2–4 h desde la llegada de 57m», con las
  entradas actuales quedaría sangrado/λ entre ~0,0010 y ~0,0017 por min (λ 1500–2500).
- Ese ejemplo no sostiene ningún valor: depende del literal de sangrado y de la decisión C.

**B. Región de posición de llegada:**
- se mantienen las bandas POCUS (57m 0,2–0,5; 72f 0,3–0,6);
- con λ ≥ 1500, la posición inferior de 57m deja de vaciar el ventrículo antes de las 2 h (flujo cero a los 134 min). P2F
  podría readmitirla, así que la admisibilidad debe reevaluarse después de fijar λ.

**C. Arquitectura del mapeo V/Hb:** estado de hemorragia compartido (§11), con κ, la mezcla y el relleno como parámetros
nuevos TBD. La alternativa interina sólo si la docencia no quiere cinética.

**D. Tasa de sangrado:** hoy es un literal heredado de la familia, igual para los dos casos y en dos derivas. Opciones:
1. mantenerla como valor por defecto de la familia, marcada como heredada;
2. una banda declarada por el caso, con el valor de la familia como respaldo;
3. con el estado compartido, una tasa de pérdida de sangre declarada por el caso que mueva V y la Hb a través del modelo.

Se recomienda la opción 3, con la 2 como transición. En ningún caso se infiere desde la Hb previa a la llegada.

**E. Mapeo de la transfusión:** no corregirlo por separado.
- El +82 % es la razón unidad/λ (0,36, heredada) actuando en una llegada infrallenada.
- Dentro del estado compartido, la unidad aporta su volumen y su masa de Hb, y su efecto en V usa el mismo κ/λ que el
  sangrado. Una ancla docente de respuesta a una unidad fijaría esa razón.

## 13. Parámetros que siguen TBD

- **Curva:** las razones de entrada / λ (λ es una convención); las posiciones p₀ y la de referencia euvolémica.
- **Sangrado:** la tasa (familia o caso) y su forma en el estado compartido.
- **Estado compartido:** κ/λ, el volumen de mezcla, el τ y el objetivo del relleno, y la Hb de la unidad.
- **Cristaloide:** su retención y la fuga.
- **Oxígeno:** ρ (candidata 2,0–3,0).
- **Fuera de este paquete:** la presión, el tono, la FC y el colapso, todos para paquetes posteriores.

## 14. Limitaciones

- Las anclas son minutos del sangrado del propio módulo. Su equivalencia física depende de la decisión C y de anclas docentes.
- Los análogos en mL (mezcla de 3–5 L, relleno, Hb de la unidad) son orientación para la discusión, no parámetros.
- El prototipo de un solo sangrado (§4.7) se calcula fuera del núcleo con valores ilustrativos: 4 L de mezcla, relleno τ 60
  hacia el volumen de llegada, 8 mL/min. No es una propuesta de valores.
- Las evaluaciones de la cuadrícula y de las anclas son estáticas: la llegada con V y la Hb desplazadas. Coinciden con la
  corrida dinámica (gasto 0,825 / 0,634 / 0,195 a los 30 / 60 / 120 min en 57m). Las trayectorias, la transfusión, el
  cristaloide y las envolventes son corridas del núcleo.
- La cuadrícula y las envolventes mueven p₀ con el DO2 de llegada fijo (0,34 re-anclado).
  - Si el gasto de llegada guardara relación con la posición (gasto / gasto normal ≈ p₀ / p_ref) y con una Hb normal de
    13,5–15, p₀ y el DO2 de llegada no serían independientes.
  - Es una sospecha no verificada, que depende de la Hb habitual, del tono y de la FC.
  - Por eso no se usó como restricción. Algunos extremos (57m inferior con λ 833 tras el manejo definitivo: DO2 1,12) quedan
    sobre lo normal por esa independencia.
- **Texto no tocado:** `state.py` todavía rotula V como «Intravascular volume», en contra de la regla docente. Corregirlo
  cambia los metadatos del núcleo y se deja para cuando se toque el núcleo.
