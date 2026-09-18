# Fisiología del edema pulmonar — magnitudes decididas

> **Estado: IMPLEMENTADO** en `family_engine.py` (bloque `EDEMA` y rama `pulmonary_edema`) con las decisiones docentes del 2026-09-18. Son parámetros docentes, no un modelo predictivo. Las trayectorias de abajo salen del motor ya implementado. Las demás familias del banco, PS001 y el SCA con nitroglicerina dan exactamente lo mismo que antes.

Aplica a `pulmonary_edema_58m` (hipertensivo, 218/116, SpO₂ 81%, FR 38) y `pulmonary_edema_75f` (IC con FE reducida y ERC, 164/92, SpO₂ 84%, FR 32).

## Por qué se cambió

En una corrida del 58m: 500 mL de suero no cambiaron nada; la PA era una escalera según la dosis de nitroglicerina (183/99 ↔ 153/85); subir la BiPAP de 10/5 a 14/8 no hizo nada; y desde los 70 min el pulmón llegaba a su valor mínimo (0.25), con FR fija en 24, trabajo "moderado" y SpO₂ 99%, hiciera lo que hiciera el residente.

## Decisiones docentes

| # | Pregunta | Decisión |
|---|---|---|
| 1 | Daño por volumen | El beneficio de la VMNI es mayor que el daño de 500 mL y se mantiene aunque se dé volumen al mismo tiempo. Sin presión positiva, el daño sí debe verse |
| 2 | Nitroglicerina | El tope del 30% de la PAS basal está bien. Se puede dar en infusión, en bolos IV de 1000–2000 mcg, o infusión más bolos pequeños |
| 3 | EPAP | Reclutamiento 0.20 + 0.03 × EPAP y −1.5 mmHg por cmH₂O sobre 5: aprobado |
| 4 | Recuperación | Con VMNI y bolos de nitroglicerina, la mejoría es mucho más rápida |
| 5 | Diurético | Antes de resolver el edema, poco o ningún efecto. Sirve más tarde, ya resuelto, en pacientes con volumen circulante efectivo aumentado |
| 6 | Techo de SpO₂ | Se queda en 99% |

## Magnitudes implementadas

Variable interna `lung`: 1.0 al llegar, sube si empeora y 0.25 es el edema resuelto. "Resuelto" para el diurético y la recurrencia es `lung` ≤ 0.65.

| Mecanismo | Magnitud |
|---|---|
| Progresión sin tratamiento | +0.003/min. Ya resuelto y sin exceso de volumen (58m): +0.001/min |
| Cristaloide | +0.0004 por mL × sensibilidad de la variante (58m 1.0, 75f 1.5). **× 0.4 con VMNI o ventilación invasiva** |
| VMNI, efecto curativo | −0.006/min con EPAP 5, y −0.0006/min más por cada cmH₂O sobre 5 |
| VMNI, reclutamiento | 0.20 + 0.03 × EPAP, máximo 0.50 |
| VMNI, presión de soporte | FR −1 por cada cmH₂O de (IPAP − EPAP) sobre 5, entre −5 y +3 |
| VMNI, PA | −1.5 mmHg de PAS por cada cmH₂O de EPAP sobre 5 |
| Nitroglicerina | Equivalente = infusión (mcg/min) + reserva de bolos ÷ 4. Pulmón −0.00008 por mcg/min equivalente, hasta −0.02/min |
| Bolo IV de nitroglicerina | 50–3000 mcg; su efecto decae con constante de 4 min |
| Nitroglicerina sobre la PA | Objetivo 0.35 × equivalente, tope **30% de la PAS basal**, alcanzado con constante de 3 min |
| Alivio de la congestión sobre la PA | Hasta −10% de la PAS basal a medida que se resuelve |
| Furosemida | Desde los 30 min, −0.00005 por mg, hasta −0.004/min. **× 0.1 si se da antes de resolver el edema; × 0.25 sin exceso de volumen (58m)** |
| Oxigenación | Ganancia por FiO₂ × (1 − 0.6 × congestión). Resuelto sin oxígeno: 97%. Techo 99% |
| FR, FC, trabajo | Resuelto: FR 16; FC −20 × mejoría; el trabajo respiratorio baja en proporción hasta Normal |

## Trayectorias del motor

Las anotaciones son PA · FC · SpO₂ · FR · trabajo respiratorio. **VMNI** = BiPAP 10/5 FiO₂ 60%.

### 58m (edema hipertensivo)

| Escenario | 5–10 min | 15–30 min | 60 min |
|---|---|---|---|
| Sin tratamiento | — | 30′: 218/116 · 126 · 79 · 40 · severo | 218/116 · 78 · 41 · severo |
| Solo VMNI | 10′: 207/111 · 116 · 97 · 27 · moderado | 30′: 205/110 · 99 · 25 · moderado | 203/109 · 99 · 22 · leve |
| VMNI + infusión 100 → 200 | 10′: 170/93 · 114 · 99 · 25 · moderado | 30′: 131/74 · 106 · 99 · 16 · normal | 131/74 · 16 · normal |
| VMNI + bolo 2000 → bolo 1000 + infusión 100 | 5′: 148/83 · 114 · 99 · 25 · moderado | 15′: 143/80 · 108 · 99 · 19 · normal | 161/89 · 16 · normal |
| Lo anterior + 500 mL a los 10 min | 10′: 143/80 · 99 · 22 · leve | 25′: 163/90 · 99 · **19** · normal (sigue mejorando) | — |
| **500 mL sin VMNI** (mascarilla con reservorio) | 5′: 218/116 · 88 · 38 · severo | 20′: 218/116 · **84 · 43** · severo | — |
| BiPAP **14/8** + infusión 100 | 10′: 163/92 · 99 · 20 · leve | 30′: 157/89 · 99 · 15 · normal | 157/89 · 15 · normal |

### 75f (IC con FE reducida)

| Escenario | 5–10 min | 15–30 min | 60 min |
|---|---|---|---|
| Sin tratamiento | — | 30′: 164/92 · 114 · 82 · 34 · marcado | 164/92 · 81 · 35 · severo |
| Solo VMNI | 10′: 156/88 · 104 · 99 · 24 · leve | 30′: 154/87 · 99 · 23 · leve | 152/86 · 99 · 21 · leve |
| VMNI + infusión 100 → 200 | 10′: 120/71 · 102 · 99 · 22 · leve | 30′: **98/61** · 94 · 99 · 16 · normal | 98/61 · 16 · normal |
| VMNI + bolos + infusión 100 | 5′: 111/67 · 102 · 99 · 22 · leve | 15′: 101/62 · 96 · 99 · 18 · normal | 113/67 · 16 · normal |
| Lo anterior + 500 mL a los 10 min | 10′: 103/63 · 99 · 20 · leve | 25′: 115/68 · 99 · 19 · leve (sigue mejorando) | — |
| **500 mL sin VMNI** | 5′: 164/92 · 91 · 32 · marcado | 20′: 164/92 · **85 · 38** · severo | — |

### Furosemida y retiro del tratamiento

Pauta: VMNI + bolo 2000 + infusión 100 durante 45 min. Luego se suspende la nitroglicerina y se pasa a naricera 4 L/min. Valores a los 135 min:

| Variante | Sin furosemida | Furosemida al inicio (edema sin resolver) | Furosemida al retirar (edema resuelto) |
|---|---|---|---|
| 75f (exceso de volumen) | 157/88 · SpO₂ 93 · FR 25 · moderado (recae) | 156/88 · SpO₂ 94 · FR 24 (casi sin efecto) | 151/86 · **SpO₂ 98 · FR 20** · leve |
| 58m (sin exceso de volumen) | 202/108 · SpO₂ 97 · FR 21 · leve | 201/108 · FR 21 | 200/107 · FR 20 |

En el 58m, al suspender la nitroglicerina la PA vuelve a ~200. Sigue siendo el paciente hipertenso que dejó su tratamiento, y el caso aún no permite indicar antihipertensivos orales.

## Qué más cambió

- **Bolo IV de nitroglicerina** en español e inglés: "Give nitroglycerin 2000 mcg IV bolus", "Nitroglycerin 1 mg IV push", "Administra bolo de nitroglicerina 1000 mcg IV". La nitroglicerina sublingual y el bolo de noradrenalina siguen pidiendo aclaración.
- El bolo tiene efecto en todas las familias del banco. Fuera del edema solo baja la PA, igual que la infusión.
- Los casos generados por IA y PS001 no tienen bolo de nitroglicerina; esa orden pide aclaración.

## Fuera de este cambio

- **Gases venosos dinámicos:** pH y pCO₂ siguen fijos en todas las familias.
- **Salbutamol en edema:** sin efecto modelado.
- **Diuresis o balance visible.**
