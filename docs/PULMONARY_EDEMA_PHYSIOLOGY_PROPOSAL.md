# Fisiología del edema pulmonar — propuesta de magnitudes

> **Estado: PROPUESTA, no implementada.** Nada de esto cambia la app todavía. Las cifras de las tablas salen de un prototipo que aplica estas fórmulas sobre el motor actual (`family_engine.py`) en las dos variantes del banco. Son parámetros docentes para revisión clínica, no un modelo predictivo.

Aplica a la familia `pulmonary_edema`: `pulmonary_edema_58m` (hipertensivo, 218/116, SpO₂ 81%, FR 38) y `pulmonary_edema_75f` (IC con FE reducida y ERC, 164/92, SpO₂ 84%, FR 32).

## Por qué cambiar: lo que vimos en la corrida del 58m

| # | Qué pasó | Causa en el modelo actual |
|---|---|---|
| 1 | 500 mL de suero no empeoraron nada | El suero empeora el pulmón 0.00015 por mL (500 mL = +0.075). La nitroglicerina a 200 mcg/min lo mejora 0.009 por minuto y lo tapa |
| 2 | La PA es una escalera: 183/99 con 100 mcg/min y 153/85 con 200, siempre idéntica | La PAS es la basal − 0.35 × la dosis, con un tope de 65 mmHg. No depende del tiempo, del pulmón ni del diurético |
| 3 | Subir la BiPAP de 10/5 a 14/8 no hizo nada | El reclutamiento es 0.35 fijo con cualquier VMNI; IPAP y EPAP no se usan |
| 4 | SpO₂ 99% con FiO₂ 40% y con 80% | La ganancia por oxígeno es (FiO₂ − 0.21) × 30, sin efecto de shunt, y el pulmón se recupera demasiado rápido |
| 5 | Desde los 70 min: FR 24, trabajo "moderado" y SpO₂ 99%, haga lo que haga el residente | El pulmón llega a su valor mínimo (0.25) en ~60 min. La FR solo puede bajar 13.5 desde la basal, así que en el 58m nunca baja de 24 |

Hay otro hallazgo que conviene decidir junto con esto. En la 75f, la nitroglicerina a 200 mcg/min baja la PAS de 164 a **99**, porque el tope de 65 mmHg es igual para los dos pacientes.

## Propuesta

La variable interna `lung` se mantiene (1.0 al llegar, sube si empeora, baja si mejora). Solo cambian sus fuentes y cómo se traduce en signos vitales.

### P1. El volumen empeora el pulmón de forma visible

| Parámetro | Actual | Propuesto |
|---|---|---|
| Efecto del cristaloide sobre `lung` | +0.00015 por mL | **+0.0006 por mL** (4×) |
| Sensibilidad por variante | — | **58m × 1.0 · 75f × 1.5** (IC con FE reducida) |

500 mL suman +0.30 en el 58m y +0.45 en la 75f. El efecto no lo compensa la nitroglicerina, que solo frena la progresión espontánea de la enfermedad.

### P2. La presión de la VMNI importa

| Parámetro | Actual | Propuesto |
|---|---|---|
| Reclutamiento | 0.35 con cualquier VMNI | **0.20 + 0.03 × EPAP**, máximo 0.50 (EPAP 5 → 0.35, igual que hoy; EPAP 8 → 0.44; EPAP 10 → 0.50) |
| Presión de soporte (IPAP − EPAP) | sin efecto | **FR −1 por cada cmH₂O sobre 5**, entre −5 y +3 |
| EPAP sobre la PAS | sin efecto | **−1.5 mmHg por cada cmH₂O de EPAP sobre 5** |

Con EPAP 5 el reclutamiento no cambia: una BiPAP 10/5 recluta lo mismo que hoy. Su oxigenación sí cambia por P4.

### P3. La presión arterial deja de ser una escalera

| Parámetro | Actual | Propuesto |
|---|---|---|
| Efecto de la nitroglicerina | instantáneo: 0.35 × dosis | Mismo objetivo, alcanzado **con constante de tiempo de 3 min** |
| Tope del efecto | 65 mmHg para todos | **30% de la PAS basal** (58m: 65 mmHg; 75f: 49 mmHg) |
| Alivio de la congestión | — | **Hasta −10% de la PAS basal** a medida que el pulmón mejora (menos descarga simpática) |
| Diurético | solo mejora el pulmón | Igual, y baja la PA a través del alivio de la congestión |

Al bajar la nitroglicerina con el pulmón mejor, la PA sube, pero no vuelve al mismo valor exacto.

### P4. Oxigenación con shunt y recuperación más lenta

| Parámetro | Actual | Propuesto |
|---|---|---|
| Ganancia por FiO₂ | (FiO₂ − 0.21) × 30 | **× (1 − 0.6 × congestión)**: con el pulmón congestivo, subir la FiO₂ rinde menos |
| SpO₂ con el pulmón recuperado, sin oxígeno | basal + 13.5 | **97%** |
| FR con el pulmón recuperado | basal − 13.5 (58m: 24) | **16/min** en ambas variantes |
| Trabajo respiratorio | según el pulmón, con un mínimo alto | Baja nivel por nivel hasta **Normal** con el pulmón recuperado |
| FC | −15 × mejoría | **−20 × mejoría** |
| Nitroglicerina sobre `lung` | hasta −0.012/min | **hasta −0.006/min** (0.00006 por mcg/min) |
| Furosemida sobre `lung` | desde los 20 min, hasta −0.006/min | **desde los 30 min, hasta −0.004/min** (0.00005 por mg) |
| Empeoramiento más allá de la llegada | pendiente actual | **Se mantiene igual** |

`congestión` es 1 al llegar y 0 con el pulmón recuperado, contando el reclutamiento de la VMNI.

## Qué cambiaría: trayectorias del prototipo

Órdenes comunes: **inicio** = BiPAP 10/5 FiO₂ 60% + nitroglicerina 100 mcg/min; a los 10 min **titulación** = nitroglicerina 200 + furosemida 40 mg IV.

### 58m (edema hipertensivo)

**Manejo estándar (inicio → titulación → observar)**

| min | Actual | Propuesto |
|---|---|---|
| 10 | 183/99 · FC 119 · SpO₂ 99 · FR 30 · marcado | 173/94 · FC 116 · SpO₂ 97 · FR 27 · marcado |
| 25 | 153/85 · FC 117 · SpO₂ 99 · FR 28 · moderado | 140/79 · FC 115 · SpO₂ 99 · FR 26 · marcado |
| 55 | 153/85 · FC 115 · SpO₂ 99 · FR 24 · moderado | 137/77 · FC 111 · SpO₂ 99 · FR 22 · moderado |
| 85 | 153/85 · FC 115 · SpO₂ 99 · FR 24 · moderado | 132/75 · FC 107 · SpO₂ 99 · FR 18 · leve |

**500 mL de suero en 15 min a los 35 min** (sobre el manejo estándar)

| min | Actual | Propuesto |
|---|---|---|
| 35 (antes) | 153/85 · SpO₂ 99 · FR 26 · moderado | 139/78 · SpO₂ 99 · FR 25 · marcado |
| 50 | 153/85 · SpO₂ 99 · FR 24 · moderado | **146/82 · FC 120 · SpO₂ 92 · FR 31 · severo** |
| 65 | 153/85 · SpO₂ 99 · FR 24 · moderado | 144/80 · FC 118 · SpO₂ 95 · FR 29 · marcado |

**BiPAP 14/8 en vez de 10/5 desde los 10 min**

| min | Actual (10/5 o 14/8, idénticos) | Propuesto 10/5 | Propuesto 14/8 |
|---|---|---|---|
| 25 | 153/85 · FR 28 · moderado | 140/79 · FR 26 · marcado | 133/77 · FR 22 · moderado |
| 55 | 153/85 · FR 24 · moderado | 137/77 · FR 22 · moderado | 130/76 · FR 18 · moderado |
| 85 | 153/85 · FR 24 · moderado | 132/75 · FR 18 · leve | 126/74 · FR 15 · normal |

**Bajar la FiO₂ a 40% a los 25 min y volver a 80% a los 35 min**

| min | Actual | Propuesto |
|---|---|---|
| 35 (FiO₂ 40%) | SpO₂ 99 | **SpO₂ 95** |
| 45 (FiO₂ 80%) | SpO₂ 99 | SpO₂ 99 |

**Desescalar a los 55 min** (nitroglicerina 100, FiO₂ 40%): a los 75 min, actual **183/99** (el mismo valor de los 10 min); propuesto **164/90**.

**Sin tratamiento:** igual que hoy en ambos modelos (a los 60 min 218/116, SpO₂ 78, FR 41, obnubilado).

### 75f (IC con FE reducida, ERC)

| Escenario | min | Actual | Propuesto |
|---|---|---|---|
| Manejo estándar | 25 | **99/61** · SpO₂ 99 · FR 22 | 106/64 · SpO₂ 99 · FR 23 |
| Manejo estándar | 85 | 99/61 · SpO₂ 99 · FR 18 | 100/61 · SpO₂ 99 · FR 17 |
| 500 mL a los 35 min | 50 | 99/61 · SpO₂ 99 · FR 18 · leve | **113/68 · FC 112 · SpO₂ 91 · FR 30 · marcado** |
| 500 mL a los 35 min | 65 | 99/61 · SpO₂ 99 · FR 18 | 112/67 · SpO₂ 93 · FR 29 |
| BiPAP 14/8 | 85 | 99/61 · FR 18 · leve | **94/61** · FR 15 · normal |
| FiO₂ 40% a los 25 min | 35 | SpO₂ 99 | **SpO₂ 96** |
| Desescalar a los 55 min | 75 | 129/75 | 115/68 |

## Decisiones clínicas que necesito de ti

1. **Daño por volumen.** ¿Te parece suficiente una caída de SpO₂ de 99 a 92% con FR 31 y trabajo severo tras 500 mL, en paciente con BiPAP? ¿La 75f debería ser 1.5× más sensible, o más?
2. **Nitroglicerina en la 75f.** Con 200 mcg/min la PAS queda en torno a 100, y con BiPAP 14/8 baja a 94. ¿Es la señal docente que quieres ("titula según la PA"), o el tope del 30% es demasiado?
3. **Efecto de la EPAP.** ¿Reclutamiento de 0.20 + 0.03 × EPAP y −1.5 mmHg de PAS por cmH₂O sobre 5 te parecen razonables? ¿Debería una EPAP alta en la 75f bajar más la PA?
4. **Ritmo de recuperación.** Con el manejo estándar, el 58m llega a FR 18 y trabajo leve a los 85 min, cuando hoy se queda en FR 24 y trabajo moderado. ¿Es un ritmo creíble?
5. **Diurético.** Inicio a los 30 min y hasta −0.004/min. ¿Quieres además un indicador visible, como diuresis horaria o balance?
6. **Techo de SpO₂.** Hoy el máximo mostrado es 99%. ¿Mostrar 100% con FiO₂ alta, como señal de hiperoxia al desescalar?

## Fuera de esta propuesta

- **Gases venosos dinámicos** (pH y pCO₂ que sigan a la FR y al pulmón). Afecta a todas las familias; conviene un documento aparte.
- **Salbutamol en edema** (sin beneficio, con taquicardia). Es una extensión menor que se puede agregar después.
- **PS001 y casos generados** usan otro motor y no cambian con esto.

## Cómo se implementaría

- Cambios solo en la rama `pulmonary_edema` de `_minute` y `_surface` en `family_engine.py`, y la sensibilidad al volumen como dato de cada variante en `clinical_cases.py`.
- Las otras familias no cambian; se verificaría con la misma comparación contra HEAD que hicimos para el tiempo de infusión.
- Pruebas por escenario: el volumen empeora, la EPAP ayuda, la PA no vuelve en escalera y una FiO₂ baja se nota con el pulmón congestivo.
