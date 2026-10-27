# P2I-2Q · Plausibilidad hemodinámica antes del refiltrado del lactato

Este paquete es una auditoría en sombra **de sólo lectura**:
- no cambia la fisiología, ningún valor por defecto, banda, registro, golden ni regla;
- no vuelve a filtrar el lactato (P2I-2R sigue en pausa) ni activa el colapso canónico en GI;
- no aprueba ningún valor.

Las sondas viven en `clinical_core/hemodynamic_probes.py` y sus resultados en `docs/revision/P2I2Q_hemodynamic_probes.json`.
- **Oxígeno:** se lee con la semántica aceptada en P2I-2P, con la reserva de extracción candidata 2,5 (banda 2,0–3,0) y la
  banda de llegada GI re-anclada (relación / ρ).
- **Representante:** el miembro con todos los niveles en el punto medio de la región restringida de P2I-2R, tal como se
  comprometió (leída, no refiltrada).
  - La hemodinámica es la misma para todos los candidatos admisibles: 1053 de los 1054 están en la precarga media.

## 0. Decisiones docentes sobre P2I-2P (registradas el 2026-10-27)

La docencia aceptó P2I-2P y su corrección estructural, y decidió:
1. **Semántica del oxígeno:**
   - entrega relativa = DO2 / DO2 normal en reposo;
   - demanda relativa = VO2 demandado / VO2 normal en reposo;
   - frontera crítica = demanda / `oxygen_extraction_reserve`;
   - déficit efectivo = máx(0, demanda − reserva × entrega);
   - D se acumula desde el déficit efectivo, no por estar el DO2 bajo lo normal.
2. **Estados:**
   - ADEQUATE: sin déficit crítico;
   - COMPENSATED: DO2 bajo lo normal, con una reserva de extracción suficiente (déficit efectivo 0);
   - CRITICAL: la reserva no alcanza (déficit efectivo > 0).
   - Para FD-LAC, «entrega inadecuada» significa CRITICAL, y «entrega adecuada restituida» (FD-LAC-04/05) significa
     ausencia sostenida de déficit crítico.
3. **FD-LAC-06:** por intervalo de reevaluación clínicamente significativo:
   - PERSISTENT/WORSENING_CRITICAL: déficit > 0 con trayectoria neta estable o en empeoramiento;
   - RECOVERING_CRITICAL: déficit > 0 que baja a lo largo del intervalo; el lactato puede bajar;
   - no se exige mejoría monótona minuto a minuto: cuenta la trayectoria neta entre puntos de reevaluación;
   - no se exige una orden de reanimación activa: la respuesta fisiológica dice si la reanimación es eficaz.
4. **Reserva de extracción:**
   - no se estima ajustando el lactato GI: es un parámetro fisiológico común;
   - banda candidata 2,0–3,0 y punto medio representativo 2,5, sin aprobación final;
   - D y lactato no separan la reserva de `arrival_delivery_ratio`, porque dependen de su producto. Con ρ ≠ 1 se usa
     la banda re-anclada, nunca la banda antigua en unidades incompatibles.

Estas decisiones guían la lectura de las sondas. No se volvió a filtrar ni se codificaron en `faculty_constraints.py`:
eso queda para el refiltrado, cuando la docencia lo autorice, con una nueva congelación de definiciones.

## 1. Qué es V (P2I-2Q-2)

Exactamente:
- **Unidad:** V está en «mL-eq». La equivalencia sale de una sola conversión heredada: 300 mL de glóbulos rojos movían en 0,36
  la variable «circulación» del motor de familias, así que 1 unidad equivale a 833,3 mL-eq.
- **Entradas en GI:**
  - el sangrado resta 2,5 mL-eq/min (el literal heredado 0,003 × 833; ×0,8 con IBP; ×0,1 tras la hemostasia);
  - los glóbulos rojos suman 300 mL-eq por unidad;
  - el salino suma 0,125 mL-eq por mL infundido, con un 60 % transitorio que se fuga con τ 30 min.
- **Lectura:** V entra **1:1 en el llenado efectivo**: x = x₀ + V, con x₀ la distancia de la llegada al punto de gasto
  cero.
  - No hay partición en volumen tensionado y no tensionado, ni reclutamiento venoso, ni relleno transcapilar.
  - El salino es la única entrada con una retención intravascular propia.

**Conclusión:** V no se comporta como volumen intravascular real. Es un **desplazamiento de la precarga efectiva**,
equivalente al volumen tensionado, con una etiqueta en mL cuya escala viene de la conversión heredada.
- **La escala de la curva** (λ = 833,3 mL-eq) sólo se ancló a la pendiente del motor heredado en la posición 0,5, que
  ningún caso GI usa.
  - En la posición 0,35 de 57m, la pendiente es 1,86 veces la heredada.
  - La λ que conservaría la pendiente heredada ahí sería 1548 mL-eq.
- **Ni λ ni los literales se contrastaron con volúmenes fisiológicos:** es una herencia del motor antiguo, no un ajuste
  deliberado.
- **Los literales de entrada no comparten una unidad física.** En 2 h de sangrado, V baja 300 mL-eq, y la Hb del mismo
  sangrado baja 1,08 g/dL (16 %). Con un volumen sanguíneo de unos 5 L y relleno completo (orientación, no un dato del caso),
  esa caída de Hb correspondería a unos 800 mL perdidos, 2,7 veces lo que pierde V.

## 2. El mapeo exacto y el paso responsable (P2I-2Q-1)

- **V → llenado efectivo:** x = x₀ + V, con x₀ = −λ·ln(1 − p₀) y p₀ la posición de llegada en la curva (banda POCUS GI: 57m
  0,2–0,35–0,5; 72f 0,3–0,45–0,6).
- **Llenado → respuesta de precarga:** p(x) = 1 − e^(−x/(λ·P^c)); respuesta = p(x) / p(x₀). Es saturable, casi lineal cerca
  del flujo cero, y 0 bajo x = 0.
- **Respuesta → gasto:** gasto = P × factor de ritmo × respuesta × 1/(1 + 0,3·(T − 1)).
  - La FC no entra: el factor de ritmo sinusal es constante.
  - El impulso simpático sólo mueve la FC: no el tono, la contractilidad ni el reclutamiento venoso.
- **Gasto → presión:** presión_rel = gasto × T.
  - Sobre la rodilla 0,5: PAS = PAS_llegada − 45·(1 − presión_rel) y PAD = PAD_llegada − 25·(1 − presión_rel).
  - Bajo la rodilla, ambas son proporcionales a presión_rel.

**El paso responsable es V → llenado efectivo, por la distancia x₀ al flujo cero.**
- Con λ = 833 mL-eq, la llegada de 57m (p₀ 0,35) queda a 359 mL-eq del gasto cero, y la de 72f (0,45) a 498 mL-eq.
- El sangrado sin tratar consume 300 mL-eq en 120 min, el 84 % y el 60 % de esa distancia. A los 120 min, en 57m:
  - el gasto = respuesta de precarga = 0,20, con P, ritmo y poscarga en 1;
  - la Hb aporta 0,84 a la entrega; la caída de la entrega es casi toda de gasto.
- Ni la forma de la curva (cerca del flujo cero es lineal, como el retorno venoso) ni la presión (que sigue al gasto) son
  la causa.
- Incluso en la referencia euvolémica (0,70) el flujo llega a cero tras perder 1003 mL-eq, y la frontera crítica (ρ 2,5)
  tras 730 mL-eq. Como la transfusión ancla el mL-eq a mL reales, eso sería un 15–20 % del volumen sanguíneo. Clínicamente,
  la hemorragia de clase II (15–30 %) suele conservar la presión. La escala es demasiado corta, aproximadamente a la mitad.
- **Huella previa:** P2F rechazó el único punto de diseño con precarga baja (57m, 0,2) porque la sonda vacía el ventrículo:
  x₀ = 186 mL-eq son 74 min de sangrado. La restricción de la región admisible a la precarga media es en parte un efecto
  de esta escala.

## 3. Requisitos de forma (P2I-2Q-3)

| Requisito | ¿Lo cumple la forma actual? | Evidencia (§4.3) |
|---|---|---|
| Una pérdida modesta no produce un colapso discontinuo | Sí en forma, no en magnitud | Continua (ningún paso de 5 mL-eq mueve el gasto un 5 %), pero −24 % por los primeros 100 mL-eq en la posición 0,35 |
| El gasto baja progresivamente al volverse críticamente insuficiente la precarga | Sí | Lineal hacia el flujo cero |
| La relación es no lineal y saturable | Sí | Pasos crecientes a medida que baja el llenado |
| Una depleción grave produce una falla profunda del gasto | Sí | Gasto 0 en x = 0; la corrida se detiene (colapso apagado) |
| Una P reducida empeora la tolerancia a la pérdida | Sólo en términos absolutos | Hasta la frontera crítica: 233 → 181 mL-eq (c = 1) o 173 (c = 0) con P 0,7. Relativa a su propio gasto, mejora un poco con c = 1 (hasta el 50 %: 199 → 207 → 226 con P 1 / 0,7 / 0,4), porque la curva se aplana. P no mueve el punto de flujo cero |
| La respuesta a fluidos depende del estado | Sí | Primeros 100 mL-eq: −24 % en 0,35 frente a −5 % en 0,70 |

Nota sobre P:
- en el modelo de Guyton, una bomba débil, con presión auricular alta, llegaría antes al flujo cero;
- en el núcleo, P no desplaza ese punto;
- es una simplificación estructural que se anota, no la causa de la implausibilidad actual.

## 4. Tablas (generado)

<!-- generado:hemodinamica -->
Generado desde las sondas `760627b365b161b166872b932b2bd5cf4fdba6b3507ad17a28215dfb2a8f1357` (`python -m clinical_core.hemodynamic_probes`). Oxígeno con la reserva candidata 2,5 (banda 2,0–3,0, no aprobada) y la banda de llegada re-anclada. Representante: `debt_clearance_tau_min=60,lactate_clearance_tau_min=120,lactate_per_output_deficit=12;excess=midpoint;intrinsic=midpoint;preload=midpoint;debt=midpoint;delivery=midpoint`, miembro de la región restringida comprometida de P2I-2R (leída, no refiltrada). Cargas de colapso sintéticas con los valores candidatos del registro: umbral de gasto 0,3, 1,0 por minuto a severidad plena, límites 5 / 15 / 30, repago τ 60 min; umbral de déficit profundo 0,5. La regla del núcleo sigue apagada.

### 4.1 Qué mueve V (mL-eq) en los escenarios GI

| Entrada | Valor |
|---|---|
| mL-eq por unidad de «circulación» heredada (300 mL de GR = 0,36) | 833,3333 |
| sangrado activo, mL-eq/min (literal heredado 0,003 × 833) | 2,5000 |
| fracción del sangrado con IBP / tras la hemostasia | 0,80 / 0,10 |
| Hb perdida por minuto de sangrado, g/dL | 0,0090 |
| glóbulos rojos, mL-eq por unidad / Hb por unidad | 300 / 0,85 |
| salino, mL-eq por mL infundido; fracción transitoria; τ de fuga (min) | 0,125; 0,60; 30 |
| escala de la curva de precarga λ, mL-eq (banda del registro) | 833,3 (600 / 833 / 1500) |

### 4.2 Auditoría GI sin tratar (L1)

**gi_bleed_57m** — hemodinámica:

| Min | Perdido (mL-eq) | V | Llenado efectivo x (mL-eq) | Posición | Respuesta de precarga | P | Ritmo, FC | Gasto rel. | T | PAS / PAD / PAM |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 359 | 0,350 | 1,00 | 1,00 | sinusal, 124 | 1,00 | 1,00 | 88 / 54 / 65 |
| 15 | 38 | -38 | 321 | 0,320 | 0,91 | 1,00 | sinusal, 126 | 0,91 | 1,00 | 84 / 52 / 63 |
| 30 | 75 | -75 | 284 | 0,289 | 0,83 | 1,00 | sinusal, 128 | 0,83 | 1,00 | 80 / 50 / 60 |
| 45 | 112 | -112 | 246 | 0,256 | 0,73 | 1,00 | sinusal, 130 | 0,73 | 1,00 | 76 / 47 / 57 |
| 60 | 150 | -150 | 209 | 0,222 | 0,63 | 1,00 | sinusal, 133 | 0,63 | 1,00 | 72 / 45 / 54 |
| 90 | 225 | -225 | 134 | 0,149 | 0,42 | 1,00 | sinusal, 140 | 0,42 | 1,00 | 56 / 35 / 42 |
| 120 | 300 | -300 | 59 | 0,068 | 0,20 | 1,00 | sinusal, 147 | 0,20 | 1,00 | 26 / 16 / 19 |

**gi_bleed_57m** — oxígeno, deuda y colapso sintético:

| Min | Hb | DO2 / normal | Demanda | Estado | Déficit efectivo | D | Lactato | Conciencia | Carga A (gasto) | Carga B (déficit) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 6,70 | 0,34 | 1,00 | crítica | 0,15 | 20,0 | 4,40 | 0 | 0,0 | 0,0 |
| 15 | 6,56 | 0,30 | 1,00 | crítica | 0,24 | 18,1 | 4,45 | 0 | 0,0 | 2,9 |
| 30 | 6,43 | 0,27 | 1,00 | crítica | 0,33 | 17,8 | 4,46 | 0 | 0,0 | 7,1 |
| 45 | 6,29 | 0,23 | 1,00 | crítica | 0,42 | 18,8 | 4,48 | 1 | 0,0 | 12,6 |
| 60 | 6,16 | 0,20 | 1,00 | crítica | 0,50 | 20,8 | 4,54 | 1 | 0,0 | 19,4 |
| 90 | 5,89 | 0,13 | 1,00 | crítica | 0,68 | 26,8 | 4,80 | 2 | 0,0 | 37,2 |
| 120 | 5,62 | 0,06 | 1,00 | crítica | 0,86 | 34,6 | 5,31 | 2 | 2,1 | 60,2 |

Al final: gasto 0,20 = P 1,00 × ritmo 1,00 × respuesta de precarga 0,20 × poscarga 1,00; la entrega suma Hb 0,84 y SpO2 1,00 de la llegada. Distancia al flujo cero en la llegada (mL-eq, y minutos a 2,5 mL-eq/min): posición 0,20 (inferior): 186 (74 min); posición 0,35 (media): 359 (144 min); posición 0,50 (superior): 578 (231 min).

**gi_bleed_72f** — hemodinámica:

| Min | Perdido (mL-eq) | V | Llenado efectivo x (mL-eq) | Posición | Respuesta de precarga | P | Ritmo, FC | Gasto rel. | T | PAS / PAD / PAM |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 498 | 0,450 | 1,00 | 1,00 | sinusal, 112 | 1,00 | 1,00 | 98 / 62 / 74 |
| 15 | 38 | -38 | 461 | 0,425 | 0,94 | 1,00 | sinusal, 113 | 0,94 | 1,00 | 95 / 61 / 72 |
| 30 | 75 | -75 | 423 | 0,398 | 0,88 | 1,00 | sinusal, 114 | 0,88 | 1,00 | 93 / 59 / 70 |
| 45 | 112 | -112 | 386 | 0,371 | 0,82 | 1,00 | sinusal, 116 | 0,82 | 1,00 | 90 / 58 / 68 |
| 60 | 150 | -150 | 348 | 0,342 | 0,76 | 1,00 | sinusal, 118 | 0,76 | 1,00 | 87 / 56 / 66 |
| 90 | 225 | -225 | 273 | 0,280 | 0,62 | 1,00 | sinusal, 122 | 0,62 | 1,00 | 81 / 53 / 62 |
| 120 | 300 | -300 | 198 | 0,212 | 0,47 | 1,00 | sinusal, 127 | 0,47 | 1,00 | 71 / 47 / 55 |

**gi_bleed_72f** — oxígeno, deuda y colapso sintético:

| Min | Hb | DO2 / normal | Demanda | Estado | Déficit efectivo | D | Lactato | Conciencia | Carga A (gasto) | Carga B (déficit) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 6,40 | 0,34 | 1,00 | crítica | 0,15 | 20,0 | 3,40 | 0 | 0,0 | 0,0 |
| 15 | 6,26 | 0,31 | 1,00 | crítica | 0,21 | 18,0 | 3,56 | 0 | 0,0 | 2,7 |
| 30 | 6,13 | 0,29 | 1,00 | crítica | 0,28 | 17,3 | 3,67 | 0 | 0,0 | 6,4 |
| 45 | 5,99 | 0,26 | 1,00 | crítica | 0,34 | 17,6 | 3,77 | 0 | 0,0 | 11,0 |
| 60 | 5,86 | 0,24 | 1,00 | crítica | 0,41 | 18,7 | 3,87 | 0 | 0,0 | 16,6 |
| 90 | 5,59 | 0,18 | 1,00 | crítica | 0,54 | 22,6 | 4,14 | 0 | 0,0 | 30,8 |
| 120 | 5,32 | 0,13 | 1,00 | crítica | 0,67 | 28,1 | 4,57 | 1 | 0,0 | 48,8 |

Al final: gasto 0,47 = P 1,00 × ritmo 1,00 × respuesta de precarga 0,47 × poscarga 1,00; la entrega suma Hb 0,83 y SpO2 1,00 de la llegada. Distancia al flujo cero en la llegada (mL-eq, y minutos a 2,5 mL-eq/min): posición 0,30 (inferior): 297 (119 min); posición 0,45 (media): 498 (199 min); posición 0,60 (superior): 764 (305 min).

### 4.3 Pérdida incremental sintética (estados por lo demás idénticos)

Llegada neutra sana colocada en cada posición, Hb y SpO2 sin cambio, tono 1; el índice DO2 supone una entrega normal en esa llegada, así que la frontera crítica es un gasto de 0,40.

| Llegada; bomba | −0 mL-eq | −100 mL-eq | −200 mL-eq | −300 mL-eq | −400 mL-eq | −500 mL-eq | −750 mL-eq | −1000 mL-eq |
|---|---|---|---|---|---|---|---|---|
| llegada GI 57m (0,35); P 1 | 1,00 · PAS 120 · adecuada | 0,76 · PAS 109 · compensada | 0,50 · PAS 97 · compensada | 0,20 · PAS 38 · crítica | sin gasto | sin gasto | sin gasto | sin gasto |
| llegada GI 57m (0,35); P 0,7 | 0,70 · PAS 106 · compensada | 0,55 · PAS 100 · compensada | 0,36 · PAS 71 · crítica | 0,15 · PAS 29 · crítica | sin gasto | sin gasto | sin gasto | sin gasto |
| llegada GI 72f (0,45); P 1 | 1,00 · PAS 120 · adecuada | 0,84 · PAS 113 · compensada | 0,67 · PAS 105 · compensada | 0,47 · PAS 92 · compensada | 0,25 · PAS 48 · crítica | sin gasto | sin gasto | sin gasto |
| llegada GI 72f (0,45); P 0,7 | 0,70 · PAS 106 · compensada | 0,60 · PAS 102 · compensada | 0,49 · PAS 95 · compensada | 0,35 · PAS 68 · crítica | 0,19 · PAS 37 · crítica | sin gasto | sin gasto | sin gasto |
| referencia euvolémica (0,70); P 1 | 1,00 · PAS 120 · adecuada | 0,95 · PAS 118 · compensada | 0,88 · PAS 115 · compensada | 0,81 · PAS 112 · compensada | 0,74 · PAS 108 · compensada | 0,65 · PAS 104 · compensada | 0,37 · PAS 73 · crítica | 0,01 · PAS 1 · crítica |
| referencia euvolémica (0,70); P 0,7 | 0,70 · PAS 106 · compensada | 0,67 · PAS 105 · compensada | 0,64 · PAS 104 · compensada | 0,60 · PAS 102 · compensada | 0,55 · PAS 100 · compensada | 0,49 · PAS 96 · compensada | 0,30 · PAS 59 · crítica | 0,00 · PAS 1 · crítica |

| Llegada; bomba | Pérdida hasta 75 % / 50 % de su propio gasto | Pérdida hasta la frontera crítica | Distancia al flujo cero |
|---|---|---|---|
| llegada GI 57m (0,35); P 1 | 105 / 199 | 233 | 359 |
| llegada GI 57m (0,35); P 0,7 | 112 / 207 | 181 | 359 |
| llegada GI 72f (0,45); P 1 | 155 / 286 | 333 | 498 |
| llegada GI 72f (0,45); P 0,7 | 170 / 301 | 266 | 498 |
| referencia euvolémica (0,70); P 1 | 383 / 644 | 730 | 1003 |
| referencia euvolémica (0,70); P 0,7 | 445 / 695 | 634 | 1003 |

Escala λ en la posición 0,35 (bomba normal), gasto por pérdida:

| λ (mL-eq) | −0 | −100 | −200 | −300 | −400 | −500 | −750 | −1000 | Pérdida hasta la frontera crítica | Flujo cero |
|---|---|---|---|---|---|---|---|---|---|---|
| 600 | 1,00 | 0,66 | 0,27 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 168 | 258 |
| 833 | 1,00 | 0,76 | 0,50 | 0,20 | 0,00 | 0,00 | 0,00 | 0,00 | 233 | 359 |
| 1500 | 1,00 | 0,87 | 0,74 | 0,59 | 0,43 | 0,27 | 0,00 | 0,00 | 420 | 646 |

Acoplamiento bomba–precarga c en la posición 0,35:

| c | P | −0 | −100 | −200 | −300 | −400 | −500 | −750 | −1000 | Pérdida hasta la frontera crítica |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0,7 | 0,70 | 0,53 | 0,35 | 0,14 | 0,00 | 0,00 | 0,00 | 0,00 | 173 |
| 0 | 1 | 1,00 | 0,76 | 0,50 | 0,20 | 0,00 | 0,00 | 0,00 | 0,00 | 233 |
| 1 | 0,7 | 0,70 | 0,55 | 0,36 | 0,15 | 0,00 | 0,00 | 0,00 | 0,00 | 181 |
| 1 | 1 | 1,00 | 0,76 | 0,50 | 0,20 | 0,00 | 0,00 | 0,00 | 0,00 | 233 |

### 4.4 DO2 corregido y déficit crítico en L1, L2 y L3 (representante)

| Escenario y caso | Min | Perdido | V | Gasto | PAS | Hb | DO2 / normal | Estado | Déficit efectivo | D | Lactato |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L1 gi_bleed_57m | 0 | 0 | 0 | 1,00 | 88 | 6,70 | 0,34 | crítica | 0,15 | 20,0 | 4,40 |
| L1 gi_bleed_57m | 15 | 38 | -38 | 0,91 | 84 | 6,56 | 0,30 | crítica | 0,24 | 18,1 | 4,45 |
| L1 gi_bleed_57m | 30 | 75 | -75 | 0,83 | 80 | 6,43 | 0,27 | crítica | 0,33 | 17,8 | 4,46 |
| L1 gi_bleed_57m | 45 | 112 | -112 | 0,73 | 76 | 6,29 | 0,23 | crítica | 0,42 | 18,8 | 4,48 |
| L1 gi_bleed_57m | 60 | 150 | -150 | 0,63 | 72 | 6,16 | 0,20 | crítica | 0,50 | 20,8 | 4,54 |
| L1 gi_bleed_57m | 90 | 225 | -225 | 0,42 | 56 | 5,89 | 0,13 | crítica | 0,68 | 26,8 | 4,80 |
| L1 gi_bleed_57m | 120 | 300 | -300 | 0,20 | 26 | 5,62 | 0,06 | crítica | 0,86 | 34,6 | 5,31 |
| L1 gi_bleed_72f | 0 | 0 | 0 | 1,00 | 98 | 6,40 | 0,34 | crítica | 0,15 | 20,0 | 3,40 |
| L1 gi_bleed_72f | 15 | 38 | -38 | 0,94 | 95 | 6,26 | 0,31 | crítica | 0,21 | 18,0 | 3,56 |
| L1 gi_bleed_72f | 30 | 75 | -75 | 0,88 | 93 | 6,13 | 0,29 | crítica | 0,28 | 17,3 | 3,67 |
| L1 gi_bleed_72f | 45 | 112 | -112 | 0,82 | 90 | 5,99 | 0,26 | crítica | 0,34 | 17,6 | 3,77 |
| L1 gi_bleed_72f | 60 | 150 | -150 | 0,76 | 87 | 5,86 | 0,24 | crítica | 0,41 | 18,7 | 3,87 |
| L1 gi_bleed_72f | 90 | 225 | -225 | 0,62 | 81 | 5,59 | 0,18 | crítica | 0,54 | 22,6 | 4,14 |
| L1 gi_bleed_72f | 120 | 300 | -300 | 0,47 | 71 | 5,32 | 0,13 | crítica | 0,67 | 28,1 | 4,57 |
| L2 gi_bleed_57m | 0 | 0 | 0 | 1,00 | 88 | 6,70 | 0,34 | crítica | 0,15 | 20,0 | 4,40 |
| L2 gi_bleed_57m | 15 | 38 | 125 | 1,26 | 100 | 5,67 | 0,36 | crítica | 0,10 | 17,0 | 4,44 |
| L2 gi_bleed_57m | 30 | 75 | 102 | 1,21 | 98 | 5,23 | 0,32 | crítica | 0,19 | 15,0 | 4,41 |
| L2 gi_bleed_57m | 45 | 112 | 34 | 1,07 | 91 | 5,09 | 0,28 | crítica | 0,31 | 15,0 | 4,36 |
| L2 gi_bleed_57m | 60 | 150 | -22 | 0,95 | 86 | 4,96 | 0,24 | crítica | 0,40 | 16,4 | 4,33 |
| L2 gi_bleed_57m | 90 | 225 | -115 | 0,73 | 76 | 4,69 | 0,17 | crítica | 0,57 | 21,6 | 4,42 |
| L2 gi_bleed_57m | 120 | 300 | -196 | 0,51 | 66 | 4,42 | 0,11 | crítica | 0,72 | 28,4 | 4,77 |
| L2 gi_bleed_72f | 0 | 0 | 0 | 1,00 | 98 | 6,40 | 0,34 | crítica | 0,15 | 20,0 | 3,40 |
| L2 gi_bleed_72f | 15 | 38 | 125 | 1,17 | 106 | 5,37 | 0,33 | crítica | 0,17 | 17,5 | 3,56 |
| L2 gi_bleed_72f | 30 | 75 | 102 | 1,14 | 104 | 4,93 | 0,30 | crítica | 0,25 | 16,4 | 3,66 |
| L2 gi_bleed_72f | 45 | 112 | 34 | 1,05 | 100 | 4,79 | 0,27 | crítica | 0,33 | 16,7 | 3,73 |
| L2 gi_bleed_72f | 60 | 150 | -22 | 0,97 | 97 | 4,66 | 0,24 | crítica | 0,40 | 17,8 | 3,81 |
| L2 gi_bleed_72f | 90 | 225 | -115 | 0,82 | 90 | 4,39 | 0,19 | crítica | 0,52 | 21,8 | 4,06 |
| L2 gi_bleed_72f | 120 | 300 | -196 | 0,68 | 83 | 4,12 | 0,15 | crítica | 0,63 | 27,0 | 4,47 |
| L3 gi_bleed_57m | 0 | 0 | 0 | 1,00 | 88 | 6,70 | 0,34 | crítica | 0,15 | 20,0 | 4,40 |
| L3 gi_bleed_57m | 15 | 30 | 120 | 1,25 | 99 | 7,02 | 0,44 | compensada | 0,00 | 16,1 | 4,43 |
| L3 gi_bleed_57m | 30 | 60 | 240 | 1,46 | 109 | 7,33 | 0,55 | compensada | 0,00 | 12,5 | 4,36 |
| L3 gi_bleed_57m | 45 | 90 | 360 | 1,65 | 117 | 7,65 | 0,64 | compensada | 0,00 | 9,7 | 4,23 |
| L3 gi_bleed_57m | 60 | 118 | 482 | 1,82 | 125 | 7,97 | 0,73 | compensada | 0,00 | 7,6 | 4,05 |
| L3 gi_bleed_57m | 90 | 126 | 474 | 1,81 | 124 | 7,95 | 0,73 | compensada | 0,00 | 4,6 | 3,64 |
| L3 gi_bleed_57m | 120 | 133 | 467 | 1,80 | 124 | 7,92 | 0,72 | compensada | 0,00 | 2,8 | 3,21 |
| L3 gi_bleed_72f | 0 | 0 | 0 | 1,00 | 98 | 6,40 | 0,34 | crítica | 0,15 | 20,0 | 3,40 |
| L3 gi_bleed_72f | 15 | 30 | 120 | 1,16 | 105 | 6,72 | 0,42 | compensada | 0,00 | 16,4 | 3,55 |
| L3 gi_bleed_72f | 30 | 60 | 240 | 1,31 | 112 | 7,03 | 0,49 | compensada | 0,00 | 12,7 | 3,59 |
| L3 gi_bleed_72f | 45 | 90 | 360 | 1,43 | 117 | 7,35 | 0,56 | compensada | 0,00 | 9,9 | 3,55 |
| L3 gi_bleed_72f | 60 | 118 | 482 | 1,54 | 122 | 7,67 | 0,63 | compensada | 0,00 | 7,7 | 3,46 |
| L3 gi_bleed_72f | 90 | 126 | 474 | 1,53 | 122 | 7,65 | 0,62 | compensada | 0,00 | 4,6 | 3,18 |
| L3 gi_bleed_72f | 120 | 133 | 467 | 1,52 | 122 | 7,62 | 0,62 | compensada | 0,00 | 2,8 | 2,86 |

### 4.5 Transfusión de 2 unidades (L3) en unidades corregidas

| Caso | Min | V | Hb | Gasto | PAS / PAM | FC | Demanda | DO2 / normal con ρ 2 · 2,5 · 3 | Estado con ρ 2 · 2,5 · 3 | Déficit efectivo |
|---|---|---|---|---|---|---|---|---|---|---|
| gi_bleed_57m relación de llegada superior | 0 | 0 | 6,70 | 1,00 | 88 / 65 | 124 | 1,00 | 0,50 · 0,40 · 0,33 | compensada · compensada · compensada | 0,00 |
| gi_bleed_57m relación de llegada superior | 15 | 120 | 7,02 | 1,25 | 99 / 73 | 119 | 1,00 | 0,65 · 0,52 · 0,44 | compensada · compensada · compensada | 0,00 |
| gi_bleed_57m relación de llegada superior | 30 | 240 | 7,33 | 1,46 | 109 / 80 | 113 | 1,00 | 0,80 · 0,64 · 0,53 | compensada · compensada · compensada | 0,00 |
| gi_bleed_57m relación de llegada superior | 45 | 360 | 7,65 | 1,65 | 117 / 86 | 107 | 1,00 | 0,94 · 0,75 · 0,63 | compensada · compensada · compensada | 0,00 |
| gi_bleed_57m relación de llegada superior | 60 | 482 | 7,97 | 1,82 | 125 / 91 | 102 | 1,00 | 1,08 · 0,86 · 0,72 | adecuada · compensada · compensada | 0,00 |
| gi_bleed_57m relación de llegada superior | 90 | 474 | 7,95 | 1,81 | 124 / 91 | 101 | 1,00 | 1,07 · 0,86 · 0,71 | adecuada · compensada · compensada | 0,00 |
| gi_bleed_57m relación de llegada superior | 120 | 467 | 7,92 | 1,80 | 124 / 91 | 100 | 1,00 | 1,06 · 0,85 · 0,71 | adecuada · compensada · compensada | 0,00 |
| gi_bleed_57m representante | 0 | 0 | 6,70 | 1,00 | 88 / 65 | 124 | 1,00 | 0,42 · 0,34 · 0,28 | crítica · crítica · crítica | 0,15 |
| gi_bleed_57m representante | 15 | 120 | 7,02 | 1,25 | 99 / 73 | 119 | 1,00 | 0,56 · 0,44 · 0,37 | compensada · compensada · compensada | 0,00 |
| gi_bleed_57m representante | 30 | 240 | 7,33 | 1,46 | 109 / 80 | 113 | 1,00 | 0,68 · 0,55 · 0,45 | compensada · compensada · compensada | 0,00 |
| gi_bleed_57m representante | 45 | 360 | 7,65 | 1,65 | 117 / 86 | 107 | 1,00 | 0,80 · 0,64 · 0,53 | compensada · compensada · compensada | 0,00 |
| gi_bleed_57m representante | 60 | 482 | 7,97 | 1,82 | 125 / 91 | 102 | 1,00 | 0,92 · 0,73 · 0,61 | compensada · compensada · compensada | 0,00 |
| gi_bleed_57m representante | 90 | 474 | 7,95 | 1,81 | 124 / 91 | 101 | 1,00 | 0,91 · 0,73 · 0,61 | compensada · compensada · compensada | 0,00 |
| gi_bleed_57m representante | 120 | 467 | 7,92 | 1,80 | 124 / 91 | 101 | 1,00 | 0,90 · 0,72 · 0,60 | compensada · compensada · compensada | 0,00 |
| gi_bleed_72f relación de llegada superior | 0 | 0 | 6,40 | 1,00 | 98 / 74 | 112 | 1,00 | 0,50 · 0,40 · 0,33 | compensada · compensada · compensada | 0,00 |
| gi_bleed_72f relación de llegada superior | 15 | 120 | 6,72 | 1,16 | 105 / 79 | 108 | 1,00 | 0,61 · 0,49 · 0,41 | compensada · compensada · compensada | 0,00 |
| gi_bleed_72f relación de llegada superior | 30 | 240 | 7,03 | 1,31 | 112 / 84 | 104 | 1,00 | 0,72 · 0,57 · 0,48 | compensada · compensada · compensada | 0,00 |
| gi_bleed_72f relación de llegada superior | 45 | 360 | 7,35 | 1,43 | 117 / 88 | 100 | 1,00 | 0,82 · 0,66 · 0,55 | compensada · compensada · compensada | 0,00 |
| gi_bleed_72f relación de llegada superior | 60 | 482 | 7,67 | 1,54 | 122 / 91 | 97 | 1,00 | 0,92 · 0,74 · 0,61 | compensada · compensada · compensada | 0,00 |
| gi_bleed_72f relación de llegada superior | 90 | 474 | 7,65 | 1,53 | 122 / 91 | 96 | 1,00 | 0,91 · 0,73 · 0,61 | compensada · compensada · compensada | 0,00 |
| gi_bleed_72f relación de llegada superior | 120 | 467 | 7,62 | 1,52 | 122 / 91 | 95 | 1,00 | 0,91 · 0,73 · 0,60 | compensada · compensada · compensada | 0,00 |
| gi_bleed_72f representante | 0 | 0 | 6,40 | 1,00 | 98 / 74 | 112 | 1,00 | 0,42 · 0,34 · 0,28 | crítica · crítica · crítica | 0,15 |
| gi_bleed_72f representante | 15 | 120 | 6,72 | 1,16 | 105 / 79 | 109 | 1,00 | 0,52 · 0,42 · 0,35 | compensada · compensada · compensada | 0,00 |
| gi_bleed_72f representante | 30 | 240 | 7,03 | 1,31 | 112 / 84 | 104 | 1,00 | 0,61 · 0,49 · 0,41 | compensada · compensada · compensada | 0,00 |
| gi_bleed_72f representante | 45 | 360 | 7,35 | 1,43 | 117 / 88 | 100 | 1,00 | 0,70 · 0,56 · 0,46 | compensada · compensada · compensada | 0,00 |
| gi_bleed_72f representante | 60 | 482 | 7,67 | 1,54 | 122 / 91 | 97 | 1,00 | 0,78 · 0,63 · 0,52 | compensada · compensada · compensada | 0,00 |
| gi_bleed_72f representante | 90 | 474 | 7,65 | 1,53 | 122 / 91 | 96 | 1,00 | 0,78 · 0,62 · 0,52 | compensada · compensada · compensada | 0,00 |
| gi_bleed_72f representante | 120 | 467 | 7,62 | 1,52 | 122 / 91 | 95 | 1,00 | 0,77 · 0,62 · 0,51 | compensada · compensada · compensada | 0,00 |

### 4.6 Señales de colapso y estado mental

| Escenario | Primer minuto crítico | Señal | Alcanza 5 / 15 / 30 | Carga máxima | Carga al final |
|---|---|---|---|---|---|
| hemorragia grave: GI 57m sin tratar | min 0 | A · gasto | — / — / — | 2,1 | 2,1 |
| hemorragia grave: GI 57m sin tratar | min 0 | B · déficit crítico | min 24 / min 51 / min 79 | 60,2 | 60,2 |
| hemorragia grave: GI 57m sin tratar | min 0 | B' · déficit crítico profundo | min 89 / min 110 / — | 21,6 | 21,6 |
| hemorragia grave: GI 57m sin tratar | min 0 | C · combinada (máx. de A y B) | min 24 / min 51 / min 79 | 60,2 | 60,2 |
| hemorragia grave: GI 72f sin tratar | min 0 | A · gasto | — / — / — | 0,0 | 0,0 |
| hemorragia grave: GI 72f sin tratar | min 0 | B · déficit crítico | min 25 / min 56 / min 89 | 48,8 | 48,8 |
| hemorragia grave: GI 72f sin tratar | min 0 | B' · déficit crítico profundo | min 116 / — / — | 6,4 | 6,4 |
| hemorragia grave: GI 72f sin tratar | min 0 | C · combinada (máx. de A y B) | min 25 / min 56 / min 89 | 48,8 | 48,8 |
| GI 57m mantenido en la llegada, sin sangrado | min 0 | A · gasto | — / — / — | 0,0 | 0,0 |
| GI 57m mantenido en la llegada, sin sangrado | min 0 | B · déficit crítico | min 34 / min 100 / — | 18,0 | 18,0 |
| GI 57m mantenido en la llegada, sin sangrado | min 0 | B' · déficit crítico profundo | — / — / — | 0,0 | 0,0 |
| GI 57m mantenido en la llegada, sin sangrado | min 0 | C · combinada (máx. de A y B) | min 34 / min 100 / — | 18,0 | 18,0 |
| hemorragia masiva: llegada sana, V −10 mL-eq/min | min 73 | A · gasto | min 96 / — / — | 8,6 | 8,6 |
| hemorragia masiva: llegada sana, V −10 mL-eq/min | min 73 | B · déficit crítico | min 91 / — / — | 12,1 | 12,1 |
| hemorragia masiva: llegada sana, V −10 mL-eq/min | min 73 | B' · déficit crítico profundo | min 100 / — / — | 5,3 | 5,3 |
| hemorragia masiva: llegada sana, V −10 mL-eq/min | min 73 | C · combinada (máx. de A y B) | min 91 / — / — | 12,1 | 12,1 |
| anemia grave con gasto conservado: Hb de 13 a 3 g/dL | min 87 | A · gasto | — / — / — | 0,0 | 0,0 |
| anemia grave con gasto conservado: Hb de 13 a 3 g/dL | min 87 | B · déficit crítico | min 112 / — / — | 8,7 | 8,7 |
| anemia grave con gasto conservado: Hb de 13 a 3 g/dL | min 87 | B' · déficit crítico profundo | — / — / — | 0,0 | 0,0 |
| anemia grave con gasto conservado: Hb de 13 a 3 g/dL | min 87 | C · combinada (máx. de A y B) | min 112 / — / — | 8,7 | 8,7 |
| hipoxemia grave con gasto y Hb conservados: SpO2 de 97 a 45 % (fuera del núcleo) | — | A · gasto | — / — / — | 0,0 | 0,0 |
| hipoxemia grave con gasto y Hb conservados: SpO2 de 97 a 45 % (fuera del núcleo) | — | B · déficit crítico | — / — / — | 0,0 | 0,0 |
| hipoxemia grave con gasto y Hb conservados: SpO2 de 97 a 45 % (fuera del núcleo) | — | B' · déficit crítico profundo | — / — / — | 0,0 | 0,0 |
| hipoxemia grave con gasto y Hb conservados: SpO2 de 97 a 45 % (fuera del núcleo) | — | C · combinada (máx. de A y B) | — / — / — | 0,0 | 0,0 |
| hipoxemia extrema con gasto y Hb conservados: SpO2 de 97 a 30 % (fuera del núcleo) | min 27 | A · gasto | — / — / — | 0,0 | 0,0 |
| hipoxemia extrema con gasto y Hb conservados: SpO2 de 97 a 30 % (fuera del núcleo) | min 27 | B · déficit crítico | min 51 / min 95 / — | 20,7 | 20,7 |
| hipoxemia extrema con gasto y Hb conservados: SpO2 de 97 a 30 % (fuera del núcleo) | min 27 | B' · déficit crítico profundo | — / — / — | 0,0 | 0,0 |
| hipoxemia extrema con gasto y Hb conservados: SpO2 de 97 a 30 % (fuera del núcleo) | min 27 | C · combinada (máx. de A y B) | min 51 / min 95 / — | 20,7 | 20,7 |
| recuperación: bomba a 0,25 hasta el min 30, restituida al 60 | min 24 | A · gasto | — / — / — | 0,3 | 0,1 |
| recuperación: bomba a 0,25 hasta el min 30, restituida al 60 | min 24 | B · déficit crítico | — / — / — | 2,3 | 0,6 |
| recuperación: bomba a 0,25 hasta el min 30, restituida al 60 | min 24 | B' · déficit crítico profundo | — / — / — | 0,0 | 0,0 |
| recuperación: bomba a 0,25 hasta el min 30, restituida al 60 | min 24 | C · combinada (máx. de A y B) | — / — / — | 2,3 | 0,6 |
| recuperación: GI 57m con manejo definitivo | min 0 | A · gasto | — / — / — | 0,0 | 0,0 |
| recuperación: GI 57m con manejo definitivo | min 0 | B · déficit crítico | — / — / — | 0,7 | 0,1 |
| recuperación: GI 57m con manejo definitivo | min 0 | B' · déficit crítico profundo | — / — / — | 0,0 | 0,0 |
| recuperación: GI 57m con manejo definitivo | min 0 | C · combinada (máx. de A y B) | — / — / — | 0,7 | 0,1 |
| tratamiento parcial: GI 57m sólo con salino | min 0 | A · gasto | — / — / — | 0,0 | 0,0 |
| tratamiento parcial: GI 57m sólo con salino | min 0 | B · déficit crítico | min 37 / min 66 / min 95 | 46,4 | 46,4 |
| tratamiento parcial: GI 57m sólo con salino | min 0 | B' · déficit crítico profundo | min 109 / — / — | 9,2 | 9,2 |
| tratamiento parcial: GI 57m sólo con salino | min 0 | C · combinada (máx. de A y B) | min 37 / min 66 / min 95 | 46,4 | 46,4 |

| Escenario | Min | Gasto | DO2 / normal | Estado | Fracción de déficit | D | Conciencia del núcleo | PAS | SpO2 |
|---|---|---|---|---|---|---|---|---|---|
| hemorragia grave: GI 57m sin tratar | 0 | 1,00 | 0,34 | crítica | 0,15 | 20,0 | 0 | 88 | 97 |
| hemorragia grave: GI 57m sin tratar | 30 | 0,83 | 0,27 | crítica | 0,33 | 17,8 | 0 | 80 | 97 |
| hemorragia grave: GI 57m sin tratar | 60 | 0,63 | 0,20 | crítica | 0,50 | 20,8 | 1 | 72 | 97 |
| hemorragia grave: GI 57m sin tratar | 90 | 0,42 | 0,13 | crítica | 0,68 | 26,8 | 2 | 56 | 97 |
| hemorragia grave: GI 57m sin tratar | 120 | 0,20 | 0,06 | crítica | 0,86 | 34,6 | 2 | 26 | 97 |
| hemorragia grave: GI 72f sin tratar | 0 | 1,00 | 0,34 | crítica | 0,15 | 20,0 | 0 | 98 | 96 |
| hemorragia grave: GI 72f sin tratar | 30 | 0,88 | 0,29 | crítica | 0,28 | 17,3 | 0 | 93 | 96 |
| hemorragia grave: GI 72f sin tratar | 60 | 0,76 | 0,24 | crítica | 0,41 | 18,7 | 0 | 87 | 96 |
| hemorragia grave: GI 72f sin tratar | 90 | 0,62 | 0,18 | crítica | 0,54 | 22,6 | 0 | 81 | 96 |
| hemorragia grave: GI 72f sin tratar | 120 | 0,47 | 0,13 | crítica | 0,67 | 28,1 | 1 | 71 | 96 |
| GI 57m mantenido en la llegada, sin sangrado | 0 | 1,00 | 0,34 | crítica | 0,15 | 20,0 | 0 | 88 | 97 |
| GI 57m mantenido en la llegada, sin sangrado | 30 | 1,00 | 0,34 | crítica | 0,15 | 15,6 | 0 | 88 | 97 |
| GI 57m mantenido en la llegada, sin sangrado | 60 | 1,00 | 0,34 | crítica | 0,15 | 13,0 | 0 | 88 | 97 |
| GI 57m mantenido en la llegada, sin sangrado | 90 | 1,00 | 0,34 | crítica | 0,15 | 11,4 | 0 | 88 | 97 |
| GI 57m mantenido en la llegada, sin sangrado | 120 | 1,00 | 0,34 | crítica | 0,15 | 10,5 | 0 | 88 | 97 |
| hemorragia masiva: llegada sana, V −10 mL-eq/min | 0 | 1,00 | 1,00 | adecuada | 0,00 | 0,0 | 0 | 120 | 97 |
| hemorragia masiva: llegada sana, V −10 mL-eq/min | 30 | 0,81 | 0,81 | compensada | 0,00 | 0,0 | 0 | 112 | 97 |
| hemorragia masiva: llegada sana, V −10 mL-eq/min | 60 | 0,55 | 0,55 | compensada | 0,00 | 0,0 | 0 | 100 | 97 |
| hemorragia masiva: llegada sana, V −10 mL-eq/min | 90 | 0,17 | 0,17 | crítica | 0,58 | 4,2 | 2 | 32 | 97 |
| anemia grave con gasto conservado: Hb de 13 a 3 g/dL | 0 | 1,00 | 1,00 | adecuada | 0,00 | 0,0 | 0 | 120 | 97 |
| anemia grave con gasto conservado: Hb de 13 a 3 g/dL | 30 | 1,00 | 0,79 | compensada | 0,00 | 0,0 | 0 | 120 | 97 |
| anemia grave con gasto conservado: Hb de 13 a 3 g/dL | 60 | 1,00 | 0,58 | compensada | 0,00 | 0,0 | 0 | 120 | 97 |
| anemia grave con gasto conservado: Hb de 13 a 3 g/dL | 90 | 1,00 | 0,38 | crítica | 0,06 | 0,1 | 0 | 120 | 97 |
| anemia grave con gasto conservado: Hb de 13 a 3 g/dL | 120 | 1,00 | 0,23 | crítica | 0,42 | 7,3 | 0 | 120 | 97 |
| hipoxemia grave con gasto y Hb conservados: SpO2 de 97 a 45 % (fuera del núcleo) | 0 | 1,00 | 1,00 | adecuada | 0,00 | — | — | — | 97 |
| hipoxemia grave con gasto y Hb conservados: SpO2 de 97 a 45 % (fuera del núcleo) | 30 | 1,00 | 0,46 | compensada | 0,00 | — | — | — | 45 |
| hipoxemia grave con gasto y Hb conservados: SpO2 de 97 a 45 % (fuera del núcleo) | 60 | 1,00 | 0,46 | compensada | 0,00 | — | — | — | 45 |
| hipoxemia grave con gasto y Hb conservados: SpO2 de 97 a 45 % (fuera del núcleo) | 90 | 1,00 | 0,46 | compensada | 0,00 | — | — | — | 45 |
| hipoxemia grave con gasto y Hb conservados: SpO2 de 97 a 45 % (fuera del núcleo) | 120 | 1,00 | 0,46 | compensada | 0,00 | — | — | — | 45 |
| hipoxemia extrema con gasto y Hb conservados: SpO2 de 97 a 30 % (fuera del núcleo) | 0 | 1,00 | 1,00 | adecuada | 0,00 | — | — | — | 97 |
| hipoxemia extrema con gasto y Hb conservados: SpO2 de 97 a 30 % (fuera del núcleo) | 30 | 1,00 | 0,31 | crítica | 0,23 | — | — | — | 30 |
| hipoxemia extrema con gasto y Hb conservados: SpO2 de 97 a 30 % (fuera del núcleo) | 60 | 1,00 | 0,31 | crítica | 0,23 | — | — | — | 30 |
| hipoxemia extrema con gasto y Hb conservados: SpO2 de 97 a 30 % (fuera del núcleo) | 90 | 1,00 | 0,31 | crítica | 0,23 | — | — | — | 30 |
| hipoxemia extrema con gasto y Hb conservados: SpO2 de 97 a 30 % (fuera del núcleo) | 120 | 1,00 | 0,31 | crítica | 0,23 | — | — | — | 30 |
| recuperación: bomba a 0,25 hasta el min 30, restituida al 60 | 0 | 1,00 | 1,00 | adecuada | 0,00 | 0,0 | 0 | 120 | 97 |
| recuperación: bomba a 0,25 hasta el min 30, restituida al 60 | 30 | 0,25 | 0,25 | crítica | 0,38 | 0,9 | 2 | 49 | 97 |
| recuperación: bomba a 0,25 hasta el min 30, restituida al 60 | 60 | 1,00 | 1,00 | adecuada | 0,00 | 1,4 | 0 | 120 | 97 |
| recuperación: bomba a 0,25 hasta el min 30, restituida al 60 | 90 | 1,00 | 1,00 | adecuada | 0,00 | 0,8 | 0 | 120 | 97 |
| recuperación: bomba a 0,25 hasta el min 30, restituida al 60 | 120 | 1,00 | 1,00 | adecuada | 0,00 | 0,5 | 0 | 120 | 97 |
| recuperación: GI 57m con manejo definitivo | 0 | 1,00 | 0,34 | crítica | 0,15 | 20,0 | 0 | 88 | 97 |
| recuperación: GI 57m con manejo definitivo | 30 | 1,46 | 0,55 | compensada | 0,00 | 12,5 | 0 | 109 | 97 |
| recuperación: GI 57m con manejo definitivo | 60 | 1,82 | 0,73 | compensada | 0,00 | 7,6 | 0 | 125 | 97 |
| recuperación: GI 57m con manejo definitivo | 90 | 1,81 | 0,73 | compensada | 0,00 | 4,6 | 0 | 124 | 97 |
| recuperación: GI 57m con manejo definitivo | 120 | 1,80 | 0,72 | compensada | 0,00 | 2,8 | 0 | 124 | 97 |
| tratamiento parcial: GI 57m sólo con salino | 0 | 1,00 | 0,34 | crítica | 0,15 | 20,0 | 0 | 88 | 97 |
| tratamiento parcial: GI 57m sólo con salino | 30 | 1,21 | 0,32 | crítica | 0,19 | 15,0 | 0 | 98 | 97 |
| tratamiento parcial: GI 57m sólo con salino | 60 | 0,95 | 0,24 | crítica | 0,40 | 16,4 | 0 | 86 | 97 |
| tratamiento parcial: GI 57m sólo con salino | 90 | 0,73 | 0,17 | crítica | 0,57 | 21,6 | 1 | 76 | 97 |
| tratamiento parcial: GI 57m sólo con salino | 120 | 0,51 | 0,11 | crítica | 0,72 | 28,4 | 1 | 66 | 97 |

### 4.7 Forma de la presión a tono fijo

Resistencia implícita (PAM / gasto, relativa a la de llegada) y salto de la pendiente de la PAS en la rodilla (0,5 de presión relativa).

| Llegada | Resistencia implícita con gasto 1 · 0,75 · 0,5 · 0,3 · 0,2 | Pendiente de la PAS sobre / bajo la rodilla (mmHg por unidad) | Salto |
|---|---|---|---|
| GI 57m | 1,00 · 1,17 · 1,52 · 1,52 · 1,52 | 45 / 131 | ×2,9 |
| GI 72f | 1,00 · 1,19 · 1,57 · 1,57 · 1,57 | 45 / 151 | ×3,4 |
| neutral arrival | 1,00 · 1,22 · 1,65 · 1,65 · 1,65 | 45 / 195 | ×4,3 |

La presión como sustituto de la perfusión (llegada neutra):

| P | T | Gasto | PAS / PAM | DO2 / normal | Estado | Conciencia del núcleo |
|---|---|---|---|---|---|---|
| 1,00 | 1,00 | 1,00 | 120 / 90 | 1,00 | adecuada | 0 |
| 0,35 | 1,00 | 0,35 | 68 / 52 | 0,35 | crítica | 1 |
| 0,25 | 3,00 | 0,16 | 91 / 70 | 0,16 | crítica | 0 |

### 4.8 Escalas candidatas de la curva (para revisión docente; nada cambia en lo canónico)

| λ (mL-eq) | Euvolemia: flujo cero / frontera crítica / mitad del gasto (mL-eq perdidos) | Caso | Flujo cero en la llegada | L1 a los 60 min: gasto, PAS, DO2, fracción de déficit | L1 a los 120 min | L1: gasto ≤ 0,5 desde | L3: gasto y PAS máximos |
|---|---|---|---|---|---|---|---|
| 833 | 1003 / 730 / 644 | gi_bleed_57m | 359 | 0,63, 72, 0,20, 0,50 | 0,20, 26, 0,06, 0,86 | min 80 | 1,82, 125 |
| 833 | 1003 / 730 / 644 | gi_bleed_72f | 498 | 0,76, 87, 0,24, 0,41 | 0,47, 71, 0,13, 0,67 | min 115 | 1,54, 122 |
| 1500 | 1806 / 1313 / 1160 | gi_bleed_57m | 646 | 0,80, 79, 0,25, 0,37 | 0,59, 69, 0,17, 0,58 | — | 1,51, 111 |
| 1500 | 1806 / 1313 / 1160 | gi_bleed_72f | 897 | 0,87, 92, 0,27, 0,32 | 0,73, 86, 0,21, 0,48 | — | 1,34, 113 |
| 2000 | 2408 / 1751 / 1546 | gi_bleed_57m | 862 | 0,86, 81, 0,27, 0,33 | 0,70, 74, 0,20, 0,50 | — | 1,40, 106 |
| 2000 | 2408 / 1751 / 1546 | gi_bleed_72f | 1196 | 0,90, 94, 0,28, 0,30 | 0,80, 89, 0,23, 0,43 | — | 1,26, 110 |

<!-- /generado:hemodinamica -->

## 5. Presión y gasto (P2I-2Q-4)

- **Monotonía:** a tono fijo, menos gasto da siempre menos PAS, PAD y PAM, continuas y monótonas.
- **Bajo la rodilla:** son proporcionales al gasto: con resistencia fija, presión = flujo × resistencia.
- **El origen principal de la brusquedad (PAS 88 → 72 → 26 a los 0, 60 y 120 min en 57m) es el gasto.** Con λ 1500, la
  misma relación de presión da 79 y 69 mmHg a los 60 y 120 min (§4.8).
- **La forma de la presión aporta un quiebre** (§4.7):
  - sobre la rodilla, la recta adoptada implica una resistencia que sube a medida que cae el gasto: 1,52 veces la de
    llegada en la rodilla en 57m, 1,57 en 72f y 1,65 en la llegada neutra. Es un tono implícito con T = 1;
  - bajo la rodilla esa resistencia queda fija;
  - la pendiente de la PAS se multiplica por 2,9 (57m), 3,4 (72f) y 4,3 (neutra) al cruzarla, así que la caída de presión
    se acelera bruscamente cuando el gasto baja de 0,5 de la llegada;
  - con la resistencia de llegada fija, la PAS sería todavía menor (≈ 17 con gasto 0,195), así que la presión no cae más que
    la física. El defecto es el quiebre y el tono escondido.
- **Faltas estructurales, no tocadas:**
  - no hay respuesta barorrefleja del tono: el impulso simpático no escribe T ni P;
  - la FC no entra en el gasto: sube de 124 a 147 lpm sin efecto.

  Pertenecen a la calibración de PA y FC, fuera de este paquete.
- **La presión se usa como perfusión en un lugar:** el nivel de conciencia, que lee la PAS por bandas (§9). Con P 0,25 y
  T 3, el gasto es 0,16 y el estado CRÍTICO, pero la PAS es 91 y el paciente sale «alerta» (§4.7). En el núcleo, el gasto,
  la entrega, D y el TLC leen el gasto.

## 6. DO2 corregido y déficit crítico (§4.4)

Con ρ 2,5 y la banda re-anclada, ambas llegadas son CRÍTICAS: DO2 0,34 de lo normal, déficit efectivo 0,15.
- **L1 sin tratar:** críticas todo el tiempo. El DO2 baja a 0,06 (57m) y 0,13 (72f) a los 120 min, y la fracción de déficit
  sube a 0,86 y 0,67.
- **L2, salino:** el gasto sube de forma transitoria (1,26 a los 15 min en 57m), pero la dilución baja la Hb (6,7 → 5,7). La
  entrega apenas cambia y vuelve a caer: crítica todo el tiempo, con DO2 0,11 a los 120 min.
- **L3, manejo definitivo:** compensada desde el minuto 15. El déficit efectivo es 0 de ahí en adelante, y D y el lactato
  bajan.

## 7. Transfusión en unidades corregidas (P2I-2Q-7)

- **57m, representante:**
  - antes: Hb 6,7, gasto 1,00, DO2 0,34 (ρ 2,5), crítica, déficit 0,15;
  - a los 15 min: compensada (DO2 0,44);
  - a los 60 min: Hb 8,0, gasto 1,82, PAS 125, FC 102, DO2 0,73 (0,92 con ρ 2; 0,61 con ρ 3), compensada.
- **72f:** gasto máximo 1,54, PAS 122, DO2 0,63.
- **Variante con la relación de llegada superior:** DO2 1,08 con ρ 2 (adecuada, apenas sobre lo normal), 0,86 con ρ 2,5.
- **Sin problema de DO2:** el DO2 corregido no supera lo normal salvo en ese 1,08, que es plausible tras la reanimación y no
  se marca como patológico.
- **La presión y la FC son plausibles.** Lo que sí hereda el problema de §2 es la magnitud de la respuesta del gasto:
  +82 % sobre la llegada con +482 mL-eq. Es el reflejo de la misma escala corta: con λ 1500 sería +51 %, con PAS 111.

## 8. Colapso (P2I-2Q-5)

Comparación sintética (§4.6; registro: umbral de gasto 0,3, límites 5/15/30, repago τ 60):

| Situación | A · gasto | B · déficit crítico | B′ · sólo el déficit profundo (> 0,5) |
|---|---|---|---|
| Hemorragia grave GI sin tratar | Nunca llega al límite (umbral relativo a la llegada) | Llega pronto: límite 15 a los 51 min en 57m, todavía con PAS ≈ 74 | Límite 15 a los 110 min en 57m (PAS ≈ 36) |
| Paciente estable en la llegada GI de 57m, sin sangrado (gasto 1, fracción 0,15) | 0 | **Llega al límite 15 a los 100 min**: colapsaría un paciente estable | 0 |
| Hemorragia masiva (llegada sana, V −10 mL-eq/min) | Límite 5 a los 96 min. El gasto llega a 0 en el min 101 y la corrida se detiene antes de cualquier límite mayor | Límite 5 a los 91 min | Límite 5 a los 100 min |
| Anemia grave con gasto conservado (Hb 13 → 3) | Ciega: 0 | Límite 5 a los 112 min | No llega (fracción máxima 0,42) |
| Hipoxemia grave (SpO2 45 %) | Ciega | Ciega: DO2 0,46, compensada con ρ 2,5 | Ciega |
| Hipoxemia extrema (SpO2 30 %) | Ciega | Límite 15 a los 95 min | No llega (fracción 0,23) |
| Recuperación (bomba restituida; GI L3) | Sin colapso; se repaga | Sin colapso; se repaga (pico 2,3 → 0,6) | Sin colapso |
| Tratamiento parcial (GI 57m, sólo salino) | 0 | Límite 5 a los 37 min, con gasto 1,15, PAS 95 y paciente alerta | Límite 5 a los 109 min |

La carga sintética sigue el esquema del núcleo (P2E-3): el minuto m suma la severidad leída al inicio del minuto. Con la
señal de gasto coincide, minuto a minuto, con la carga del propio núcleo (prueba).

**Recomendación (sin umbrales finales; el colapso canónico GI sigue apagado):**
1. **La familia B, el déficit crítico normalizado, es la única que maneja estructuralmente las cuatro situaciones.** La
   señal A es ciega a la anemia y a la hipoxemia, y no ve la gravedad de la llegada porque su umbral es relativo a la
   llegada.
2. **El gasto no es requisito previo.** Sigue siendo un criterio independiente de falta de pulso: el gasto cero ya detiene la
   corrida.
3. **D no alimenta la carga.**
4. **C (combinada) no aporta:** en todas las sondas, donde A acumula, B también acumula, y antes. Como máximo, C no cuenta
   dos veces; una suma de A y B sí contaría dos veces el bajo gasto, porque el DO2 es proporcional al gasto.
5. **B cruda no sirve tal cual.** Integra el mismo déficit que D, sin aclaramiento mientras dura, y acumula desde la llegada:
   - un paciente estable en la llegada de 57m colapsaría a los 100 min;
   - el salino parcial alcanza el límite 5 con PAS 95 y el paciente alerta.

   La señal debe responder a la parte **profunda** del déficit. B′ lo hace: es 0 en el paciente estable y en las
   recuperaciones, y alcanza los límites sólo en estados profundos. Así se distingue de D.
6. **La dosis de B′ necesita sus propios valores.** Con el umbral sintético 0,5, B′ tarda o no llega en la anemia Hb 3 y en
   la hipoxemia SpO2 30 %. El umbral, la forma (umbral o peso convexo), el límite y el repago son decisión docente. Los
   límites del registro se pensaron para la severidad del gasto.
7. **Límite del modelo:**
   - el DO2 corporal total con una reserva fija subestima la letalidad de la hipoxemia, que daña antes el cerebro y el
     miocardio;
   - el núcleo no produce hipoxemia: la SpO2 sólo se mueve con la FiO2;
   - la vía del paro hipóxico requeriría un acoplamiento O2 miocárdico → P, que no existe.
8. **Orden:** el momento del colapso depende de la escala hemodinámica. Primero se fija λ (§10), después la dosis de B′.
   La señal A, además, puede quedar adelantada por el gasto cero: el núcleo detiene la corrida antes de llegar a su
   límite.

## 9. Estado mental (P2I-2Q-6)

- **Hoy:** el nivel de conciencia es el máximo entre el de llegada, el de las bandas de PAS (< 80 → 1; < 65 → 2) y el de las
  de SpO2 (< 87 → 1; < 80 → 2). No lee el déficit crítico ni D.
- **En GI:** la PAS acompaña al déficit; 57m pasa a 1 a los 45 min y a 2 a los 90. No hay contradicción estructural en las
  corridas canónicas, así que **no se cambió**.
- **Brechas:**
  - la anemia grave con déficit crítico (Hb 3, fracción 0,42) deja al paciente alerta;
  - un estado vasoconstreñido de gasto bajo (P 0,25, T 3: gasto 0,16, CRÍTICO, PAS 91) también deja al paciente alerta. La
    PAS hace de sustituto de la perfusión;
  - la recuperación es instantánea: nivel 2 a los 30 min y 0 a los 60 al restituir la PAS, sin retraso;
  - D sola tampoco sirve: el paciente de 57m llega con D 20 y está alerta.
- **Por qué no se cambió:** ningún módulo ni intervención del núcleo escribe T (sólo las sondas), así que la contradicción no
  aparece en ninguna corrida canónica.
  Corregirla es calibración del estado mental: decisión docente.
- **Recomendación:**
  - la entrada aguda debe ser el **déficit crítico actual** (fracción efectiva / demanda), para que una falta aguda muy
    grave de O2 altere la conciencia antes de que se acumule una D grande;
  - la **deuda acumulada D** (o una memoria lenta) debe dar persistencia y retraso de recuperación;
  - es decir, ambas, con papeles distintos;
  - la hipoxemia mantiene su vía directa por la SpO2;
  - los umbrales son TBD.

## 10. Clasificación del problema V → gasto (P2I-2Q-8)

**B · PARAMETER_SCALE_CALIBRATION_ERROR.**
- **La forma no es el problema:** cumple los seis requisitos (§3). Su núcleo lineal cerca del flujo cero coincide con el
  retorno venoso proporcional al volumen tensionado.
- **La implausibilidad está en la escala o posición:** la distancia al flujo cero (x₀ = −λ·ln(1 − p₀)) es corta en toda la
  curva. Ya lo es en la euvolemia, y lo es en las llegadas GI con las bandas POCUS.
- **Origen:** λ y la tasa de sangrado vienen de literales heredados.
- **Con la misma forma y otra escala, la trayectoria se vuelve plausible.** Con λ 1500–2000, el L1 sin tratar de 57m queda a
  los 120 min con gasto 0,59–0,70, PAS 69–74 y todavía CRÍTICO.
- **No se elige por parecido al motor heredado:** precisamente, la escala actual es la herencia.
- **No es D:** la transfusión ancla el mL-eq a mL reales (300 por unidad), así que el flujo cero tras ~1 L desde la
  euvolemia no se arregla reinterpretando.
- **Ausencias estructurales (anotadas, no propuestas como corrección ahora):**
  - el reclutamiento venoso, el relleno transcapilar, el tono barorreflejo y la FC en el gasto;
  - que P no mueva el punto de flujo cero.

  Si la docencia quiere compensación y descompensación dependientes del tiempo, eso sería trabajo estructural aparte. Para
  corregir la implausibilidad actual no hace falta.
- **Aparte de V → gasto, la relación de presión tiene un defecto de forma propio** (§5): el tono implícito y el quiebre de
  pendiente en la rodilla.
  - No causa la caída del gasto, pero acelera la de la presión bajo 0,5.
  - Corrección mínima propuesta, no implementada: una relación presión–flujo con una resistencia implícita continua (sin
    quiebre) o un tono barorreflejo explícito.
  - Pertenece a la calibración de PA, que este paquete no hace.

**Rangos candidatos para revisión docente** (orientación fisiológica, no aprobación):
- **Referencias de orientación:** la hemorragia de clase III (30–40 %, unos 1,5–2 L en un adulto de 5 L) suele traer
  hipotensión, y la de clase IV (> 40 %) amenaza la vida. Un objetivo coherente es que la frontera crítica esté cerca de
  1,3–1,8 L perdidos desde la euvolemia y el flujo cero cerca de 1,8–2,5 L.
- **Valores candidatos** (§4.8, con la referencia euvolémica 0,70 y ρ 2,5):
  - λ 1500 da 1313 / 1806 mL-eq (frontera crítica / flujo cero);
  - λ 2000 da 1751 / 2408 mL-eq.
- **Rango candidato:** λ ≈ 1500–2000 mL-eq. El techo de la banda del registro es 1500, así que habría que ampliarla.
  - Coincide con la λ de 1548 que conservaría la pendiente heredada en la posición GI real.
- **Posiciones p₀:** se mantienen las bandas POCUS.
- **Tasa de sangrado:** se mantiene en 2,5 mL-eq/min, un literal heredado que el caso no declara. Se señala como
  pendiente de revisión.

**Efecto en lo que sigue:**
- cambiar λ cambia el gasto, D y el lactato en L1 y L2, y la respuesta de L3;
- también puede readmitir posiciones de precarga que P2F rechazó;
- por eso λ debe decidirse **antes** del refiltrado del lactato.

## 11. Parámetros que requieren calibración docente

- **Escala de la curva:** `preload_curve_scale_ml` (λ), con una banda del registro a ampliar.
- **Llegada:** las posiciones de llegada `preload_fraction` (bandas POCUS) y la posición euvolémica de referencia.
- **Volumen:** la tasa de sangrado y la conversión de mL derramados o transfundidos a precarga efectiva; la caída de Hb por
  sangrado, coherente con esa pérdida; la retención del salino.
- **Bomba y presión:** el acoplamiento bomba–precarga c y la rodilla y pendientes de la presión. La calibración de PA
  queda fuera de este paquete.
- **Colapso:** la señal, la forma de su severidad, el límite, el repago y el ritmo terminal.
- **Estado mental:** las entradas y los umbrales.
- **Reserva de extracción:** ρ, dentro de la banda candidata 2,0–3,0.

## 12. Limitaciones

- Las sondas sintéticas usan la llegada neutra sana con Hb y SpO2 sin cambio. El índice DO2 de §4.3 supone una entrega
  normal en esa llegada.
- La hipoxemia se calculó fuera del núcleo, que no puede producirla.
- Las cargas de colapso son cálculos sobre las trayectorias, con los valores candidatos del registro. La regla del núcleo
  sigue apagada.
- Las orientaciones de volumen (clases de hemorragia, volumen sanguíneo de unos 5 L, relleno) son aproximadas y sirven
  para ordenar la discusión docente. No son parámetros aprobados.
- **Textos congelados:** `gi_reference.py` todavía describe la unidad de la demanda y de la banda de llegada con la redacción
  anterior a P2I-2P («delivery that meets the reference demand»).
  - Forma parte del congelamiento de calibración y no se tocó.
  - La lectura vigente es la de §0.
