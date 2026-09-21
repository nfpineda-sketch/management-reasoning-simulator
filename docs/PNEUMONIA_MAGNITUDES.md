# Neumonía — magnitudes implementadas

> **Estado: IMPLEMENTADO** en `family_engine.py` (rama `pneumonia`) y `clinical_cases.py` (dos variantes), con las decisiones docentes del 2026-09-21. Son parámetros docentes, no un modelo predictivo. Las trayectorias de abajo salen del motor ya implementado. Las demás familias del banco, PS001 y los casos generados dan exactamente lo mismo que antes.

Es la última familia del banco que quedaba sin documento. El modelo ya existía; lo que se agregó el 2026-09-21 es que el paciente pueda **mostrar** que fue tratado.

## Las dos variantes

| Caso | Llegada | Estado mental | Foco | Laboratorio |
|---|---|---|---|---|
| **46f, artritis reumatoide** | 92/58 · FC 118 · SpO₂ 89 · FR 30 · T 39.1 · llene 4 s | alerta | condensación basal **derecha** | lactato 3.8 · GB 19.4 · creatinina 1.4 |
| **83m, hipertenso** | 96/60 · FC 108 · SpO₂ 91 · FR 28 · T 37.8 · llene 4 s | **somnoliento** | condensación basal **izquierda** | lactato 3.1 · GB 15.6 · creatinina 1.6 |

El de 83 años es el caso difícil: lo trae la hija porque está "inusualmente somnoliento", la nota de derivación sugiere deshidratación, la fiebre es 37.8 y el diagnóstico no viene dado. Normalmente camina solo y conversa bien, así que la somnolencia es aguda.

## Decisiones docentes del 2026-09-21

Origen: una corrida del 83m en que, a las dos horas y media, la presión, el llene, la saturación y el lactato estaban recuperados y el paciente seguía descrito igual que al llegar — somnoliento y con el mismo trabajo respiratorio. Los dos signos sobre los que está construido el caso no podían responder al tratamiento.

| # | Pregunta | Decisión |
|---|---|---|
| 1 | ¿Cuándo despierta? | Con la **perfusión recuperada**, no con uno solo de los parámetros |
| 2 | ¿Con cuánto retraso? | **30 minutos**: el cerebro va detrás de la hemodinamia |
| 3 | ¿Cuánto despierta? | **Un escalón**, desde el valor con que el caso fue escrito, y no más |
| 4 | Cerebro sin azúcar | **Nunca despierta**, aunque todos los demás parámetros estén resueltos |
| 5 | Trabajo respiratorio | Que siga al pulmón en vez de quedarse pegado en un nivel |

## Magnitudes implementadas

Variables internas `lung` y `circulation`: 1.0 al llegar; **subir** es empeorar. La superficie se calcula contra el estado de llegada que el caso escribió, así que en el minuto cero el motor reproduce exactamente lo autorizado.

| Mecanismo | Magnitud |
|---|---|
| Progresión sin tratamiento | Pulmón **+0.002/min** y circulación **+0.002/min** |
| **Antibiótico** | Nada antes de **60 min**; después **−0.003/min × exposición**, sobre el pulmón y la circulación |
| Exposición del antibiótico | Dosis ÷ dosis de referencia, tope 1.0: ceftriaxona 1000 mg, azitromicina 500, piperacilina-tazobactam 4500, vancomicina 1000 |
| Cristaloide | Circulación **−0.00025 por mL**: 1 L es −0.25 |
| Sangre | Circulación −0.36 por unidad; hemoglobina +0.85 g/dL |
| Noradrenalina | **1.5 mmHg de PAS por mcg/min**, con techo de **+35 mmHg**. En 70 kg, 0.05 mcg/kg/min son 3.5 mcg/min y +5 mmHg; el techo llega cerca de 0.33 mcg/kg/min |
| Oxígeno sobre la SpO₂ | Ganancia de **30 puntos × (FiO₂ − 0.21)**, con techo de 99% |
| **Cortocircuito** | 0.60: la PaO₂ sube `(FiO₂ − 0.21) × 350 × 0.40`. Es la familia con el segundo cortocircuito más alto, después del edema |
| Reclutamiento | **0.35 con VMNI**, 0.48 con ventilación invasiva, restados del pulmón |

### Superficie

| Signo | Magnitud |
|---|---|
| PAS y PAD | −45 y −25 por unidad de circulación sobre 1.0 |
| FC | +25 por unidad de circulación |
| SpO₂ | −18 por unidad de pulmón efectivo sobre 1.0 |
| FR | +18 por unidad de pulmón efectivo sobre 1.0 |
| Llene capilar | Basal +4 s por unidad de circulación, entre 2 y 8 s |
| Lactato | Basal + 2 por unidad de circulación, piso 0.8 |
| **Trabajo respiratorio** | **6 niveles por unidad de pulmón efectivo** (decisión 5): un nivel por cada ~8% de carga. Mientras el paciente está donde el caso lo dejó, se conserva la palabra que el caso escribió |
| **Estado mental** | Ver abajo |

### El estado mental

Antes solo podía **empeorar**: bajo SpO₂ 80 o PAS 65 pasa a obnubilado, y bajo SpO₂ 87 o PAS 80 a somnoliento si venía alerta. No había camino de vuelta, así que un paciente que llegaba somnoliento por hipoperfusión no despertaba nunca.

| Mecanismo | Magnitud |
|---|---|
| Perfusión recuperada | SpO₂ ≥ **92**, PAS ≥ **100** y llene < **3.5 s**, las tres juntas |
| Retraso | **30 minutos** de perfusión recuperada |
| Contador | Cada minuto bueno **suma uno**, cada minuto malo **resta uno**, con piso en cero: un bamboleo de 1 mmHg alrededor del umbral no reinicia la media hora |
| Recuperación | **Un escalón** en la escala sin respuesta → obnubilado → somnoliento → alerta, desde el valor de llegada |
| Una vez despierto | Queda despierto. Si se deteriora de verdad, las reglas de empeoramiento lo vuelven a bajar |
| **Hipoglicemia y opioides** | **Quedan fuera**: esas familias escriben su propio estado mental. Un cerebro sin azúcar no despierta porque la presión esté bien, y el encefalópata de Wernicke sigue confuso con la glicemia normal (decisión 4) |

Vale para todas las familias del banco que no escriben su propio estado mental, no solo para la neumonía.

## Trayectorias del motor

Anotaciones: PA · FC · SpO₂ · FR · llene · estado mental · trabajo respiratorio · lactato.

### 46f (alerta al llegar, SpO₂ 89)

| Escenario | 30 min | 60 min | 120 min | 240 min |
|---|---|---|---|---|
| Sin tratamiento | 89/56 · 120 · 88 · 31 · 4.2 | 87/55 · 121 · 87 · 32 · **muy aumentado** | 81/52 · 124 · 85 · 34 · 5.0 · **somnolienta** | 70/46 · 130 · **80** · 39 · 5.9 · **severo** · lact 4.8 |
| Solo oxígeno | 89/56 · 120 · **99** · 31 | 87/55 · 121 · 99 · 32 | 81/52 · 124 · 99 · 34 · 5.0 | 70/46 · 130 · 99 · 39 · 5.9 · **somnolienta** |
| Oxígeno + antibiótico | 89/56 · 120 · 99 · 31 | 87/55 · 121 · 99 · 32 · muy aumentado | 89/57 · 119 · 99 · 31 · aumentado | 95/60 · 116 · 99 · 29 · 3.7 |
| Oxígeno + antibiótico + 1 L | 101/63 · 113 · 99 · 31 · **3.2** | 98/61 · 115 · 99 · 32 · 3.5 | 101/63 · 113 · 99 · 31 · 3.2 | 106/66 · 110 · 99 · 29 · **2.7** · lact 3.2 |
| Todo + noradrenalina | 101/63 · 113 · 99 · 31 | 103/65 · 115 · 99 · 32 | 106/66 · 113 · 99 · 31 | 111/69 · 110 · 99 · 29 · 2.7 |

**El oxígeno solo corrige el oxímetro y nada más.** A las cuatro horas la paciente está en 70/46 con llene de 5.9 y somnolienta, con una saturación de 99%. Es deliberado: el número que el residente mira con más frecuencia es el que menos informa aquí.

### 83m (somnoliento al llegar)

| Escenario | 30 min | 60 min | 120 min | 240 min |
|---|---|---|---|---|
| Sin tratamiento | 93/58 · 110 · 90 · 29 · 4.2 · somnoliento | 91/57 · 111 · 89 · 30 · **muy aumentado** | 85/54 · 114 · 87 · 32 · 5.0 | 74/48 · 120 · **82** · 37 · 5.9 · **severo** |
| Solo oxígeno | 93/58 · 110 · 99 · 29 · somnoliento | 91/57 · 111 · 99 · 30 | 85/54 · 114 · 99 · 32 · 5.0 · **somnoliento** | 74/48 · 120 · 99 · 37 · 5.9 · somnoliento |
| Oxígeno + antibiótico | 93/58 · 110 · 99 · 29 · somnoliento | 91/57 · 111 · 99 · 30 | 93/59 · 109 · 99 · 29 · 4.2 · **somnoliento** | 99/62 · 106 · 99 · 27 · 3.7 · **somnoliento** |
| **Oxígeno + antibiótico + 1 L** | 105/65 · 103 · 99 · 29 · **3.2** · somnoliento | 102/63 · 105 · 99 · 30 · **alerta** | 105/65 · 103 · 99 · 29 · alerta | 110/68 · 100 · 99 · 27 · **2.7** · alerta · lact 2.5 |
| Todo + noradrenalina | 105/65 · 103 · 99 · 29 · somnoliento | 107/67 · 105 · 99 · 30 · **alerta** | 110/68 · 103 · 99 · 29 · alerta | 115/71 · 100 · 99 · 27 · 2.7 · alerta |

**El contenido docente está en las dos últimas filas contra la tercera.** Con oxígeno y antibiótico pero sin volumen, el hombre sigue somnoliento a las cuatro horas: la perfusión nunca cruza el umbral. Con el litro despierta a los 60 minutos, y se queda despierto. El residente que solo mira la saturación ve 99% en las tres filas.

### El trabajo respiratorio a lo largo del antibiótico (46f, tratada)

| min | FR | Trabajo |
|---|---|---|
| 0 | 30 | aumentado *(la palabra del caso)* |
| 75 | 32 | **muy aumentado** — el antibiótico todavía no rinde |
| 120 | 31 | aumentado |
| 300 | 28 | **levemente aumentado** |
| 390 | 26 | levemente aumentado |

Empeorar antes de mejorar es correcto: el antibiótico entra a los 60 minutos y recién entonces gana la carrera contra la progresión.

## Qué más cambió

- **La recuperación del estado mental vale para todo el banco**, no solo para la neumonía: cualquier caso escrito con un estado mental alterado por hipoperfusión puede recobrar un escalón. Hipoglicemia y opioides quedan fuera por decisión docente.
- **El trabajo respiratorio proporcional es solo de la neumonía.** El edema pulmonar ya tenía su propia regla y no se tocó; el asma conserva la suya.

## Fuera de este cambio

- **El techo de SpO₂ 99% con reservorio.** Con cortocircuito 0.60 la saturación se satura y deja de informar aunque el pulmón empeore. Es deliberado, pero significa que la oximetría no distingue una condensación que progresa. La gasometría sí, a través de la PaO₂.
- **La elección del antibiótico no importa**: cualquiera de los cuatro, a dosis de referencia, rinde lo mismo. No hay cobertura acertada ni equivocada, ni resistencia.
- **Los hemocultivos nunca informan** un germen: quedan pendientes durante todo el encuentro.
- **La fiebre no responde** al antipirético ni al antibiótico; la temperatura es fija.
- **No se modelan** derrame paraneumónico, empiema, ventilación no invasiva fallida con indicación de intubar por fatiga, ni neumonía aspirativa.
- **Los casos generados por IA** no tienen esta rama; tienen sus propios mecanismos declarados.
