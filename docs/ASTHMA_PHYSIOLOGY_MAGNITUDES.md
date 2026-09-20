# Fisiología del asma grave — magnitudes implementadas

> **Estado: IMPLEMENTADO y REVISADO** en `family_engine.py` (rama `asthma`), `asthma_ventilation.py` y `asthma_complications.py`, con las decisiones docentes del 2026-09-19 y la revisión de magnitudes del 2026-09-20 (inicio del broncodilatador, decaimiento más rápido, magnesio más modesto y objetivo de pH). Son parámetros docentes, no un modelo predictivo. Las trayectorias de abajo salen del motor ya implementado. Las demás familias del banco, PS001 y los casos generados dan exactamente lo mismo que antes.

Aplica a `asthma_24f` (138/84, FC 126, SpO₂ 90%, FR 34, trabajo marcadamente aumentado, alerta) y `asthma_49m` (142/86, FC 132, SpO₂ 89%, FR 30, trabajo severo, somnoliento, con ingreso previo a UCI).

## Decisiones docentes

Indicación de la facultad: todo asmático grave, antes de ser intubado, debería recibir beta-agonistas inhalados continuos, corticoides endovenosos, sulfato de magnesio y adrenalina diluida en goteo o en bolos. Si se intuba, la ketamina es el inductor y el sedante de mantención de elección. El paciente no debe intubarse muy precoz, pero tampoco tarde: es un equilibrio difícil. Una vez intubado, lo que importa es el seteo: tiempo espiratorio prolongado, volúmenes más bajos e hipercapnia permisiva. La alarma de presión siempre se va a encender, porque la presión en la vía aérea está aumentada; lo que importa no es la presión máxima sino la meseta, que es la que llega al alvéolo.

| # | Pieza | Decisión |
|---|---|---|
| 1 | Beta-agonista continuo | Mantiene el efecto en vez de dejarlo decaer dosis a dosis |
| 2 | Magnesio IV | Suma broncodilatación sobre el beta-agonista |
| 3 | Adrenalina diluida | Goteo o bolos de 50–150 mcg, antes de considerar la intubación |
| 4 | Ketamina | Inductor y mantención preferidos; broncodilata |
| 5 | Ventana de intubación | Precoz y tardía tienen precio; a tiempo no |
| 6 | Seteo del ventilador | El tiempo espiratorio define el atrapamiento; la meseta es lo que importa |
| 7 | Alarma de presión | Se enciende siempre; el pico refleja resistencia, no alvéolo |
| 8 | Volumen | La precarga está agotada: el volumen paga parte del costo de la presión positiva |
| 9 | Potasio y lactato | Efectos beta reversibles, visibles en el laboratorio |

## Magnitudes implementadas

Variable interna `obstruction`: 1.0 al llegar, piso 0.2 en superficie. El flujo efectivo es `obstruction − bronchodilation − relajación (adrenalina + ketamina)`.

### Tratamiento

| Mecanismo | Magnitud |
|---|---|
| Progresión sin tratamiento | +0.002/min |
| Salbutamol nebulizado, dosis puntual | 5 mg entregan +0.8, **liberado con constante de 7 min**, y decae **2.5%/min** (vida media ≈ 27 min). El pico real de una dosis es 0.55 |
| **Nebulización continua** | Sostiene 0.09 por mg/h (10 mg/h → 0.90), con constante de 10 min |
| Corticoide IV | Desde los 60 min, −0.004/min × exposición (125 mg de metilprednisolona = 1.0) |
| **Magnesio IV** | +0.05 por gramo, tope **+0.12**, aparición en 10 min. Rango 0.5–4 g. Ayuda, y menos que las otras intervenciones |
| **Adrenalina** | +0.035 por mcg/min equivalente, tope +0.45. PAS hasta +30, FC hasta +25 |
| **Bolo de adrenalina** | 10–500 mcg IV; equivale a un tercio de su dosis en mcg/min y decae con constante de 3 min |
| **Ketamina** | +0.0015 por mg, tope +0.25, constante de 45 min |
| Propofol y midazolam | PAS −0.12 y −0.8 mmHg por mg, constante de 15 min. Ketamina y etomidato no bajan la PA |
| **Potasio** | −0.012 mmol/L por minuto y por unidad de efecto beta; vuelve al basal con constante de 120 min; piso 2.6 |
| **Lactato beta** | +0.02 mmol/L por minuto y por unidad de efecto beta; aclaramiento con constante de 60 min; techo 6.0 |

### Superficie

| Signo | Magnitud |
|---|---|
| SpO₂ | −14 puntos por unidad de obstrucción sobre 1.0; ganancia por FiO₂ |
| FR | +18 por unidad de obstrucción |
| **FC** | +25 por unidad de obstrucción, **+0.3 por minuto de agotamiento acumulado (tope 15)**, y +12 por el beta-agonista |
| PaO₂ | Sube con la FiO₂ atenuada por el cortocircuito de la familia (asma 0.30) |
| pCO₂ | Sigue a la obstrucción; intubado, sigue a la ventilación minuto |

### Agotamiento y fatiga

| Mecanismo | Magnitud |
|---|---|
| Cuenta como agotamiento | Esfuerzo marcado o severo con SpO₂ < 90, o estado mental no alerta |
| Recuperación del reloj | −0.5 min por minuto de alivio |
| Fatiga | Pasados 20 min acumulados, la obstrucción empeora +0.0015/min extra |

### Ventilador

```
τ = resistencia × distensibilidad          resistencia = 10 + 30 × obstrucción
aire atrapado = Vt · e^(−Te/τ) / (1 − e^(−Te/τ))   distensibilidad = 0.05 L/cmH₂O
auto-PEEP = aire atrapado / distensibilidad
meseta = PEEP + auto-PEEP + Vt/distensibilidad
pico = meseta + resistencia × flujo
```

| Parámetro | Valor |
|---|---|
| Por defecto si no se indica | Vt 8 mL/kg, FR 14/min, flujo 60 L/min |
| Costo hemodinámico del auto-PEEP | −2.0 mmHg de PAS por cmH₂O |
| Desconexión del circuito | Vacía la trampa; vuelve con constante de 3 min |
| Alarma de presión | Pico ≥ 40 cmH₂O |
| Límite de meseta | 30 cmH₂O |
| Sedación | Dura 45 min; sin ella el paciente gatilla y la FR entregada sube 35% |
| Hipercapnia permisiva | pCO₂ = 40 × VE requerida / VE entregada; VE requerida = 0.10 L/min/kg × (1 + 0.25 × obstrucción) |
| **Objetivo de pH** | 7.20 como objetivo práctico, no frontera de seguridad. Bajo eso, el registro pide reevaluar tolerancia, tendencia y otras causas de acidosis, y aclara que **no significa subir la ventilación minuto**. La PaCO₂ de 90 mmHg es referencia clásica, no límite rígido |

### Complicaciones y volumen

| Mecanismo | Magnitud |
|---|---|
| **Barotrauma** | Exposición +0.1 por cmH₂O de meseta sobre 30, por minuto; a las 10 unidades se rompe el pulmón |
| Neumotórax a tensión | PAS −35, SpO₂ −12, pico +15, y la ganancia de oxígeno cae 70% |
| Descompresión | Aguja o tubo; recuperación con constante de 2 min. Lado equivocado: sin efecto |
| **Volumen** | Recupera hasta 55% del costo de la presión positiva, proporcional a lo dado, completo con 1500 mL |
| Intubación precoz | PAS −12 |
| Intubación tardía | PAS −25 y lactato +2.0; ambas se disipan con constante de 20 min |

## Trayectorias del motor

Anotaciones: PA · FC · SpO₂ · FR · trabajo respiratorio · K · lactato. **Continua** = salbutamol 10 mg/h más ipratropio y metilprednisolona 125 mg IV.

### 24f

| Escenario | 20 min | 60 min | 90 min |
|---|---|---|---|
| Sin tratamiento | 30′: 138/84 · 131 · 89 · 35 · marcado | 138/84 · 142 · 88 · 37 · marcado | 138/84 · **147 · 86 · 39 · severo** |
| Dosis puntuales | 138/84 · 119 · 98 · 24 · leve | 138/84 · 121 · **96 · 26 · moderado** · K 3.7 | 138/84 · 124 · **93 · 30 · moderado** · K 3.6 |
| Nebulización continua | 138/84 · 118 · 99 · 22 · leve | 138/84 · 120 · 98 · 23 · leve · K 3.7 | 138/84 · 118 · **99 · 22 · leve** · K 3.6 |
| Continua + magnesio | 138/84 · 118 · 99 · 22 · leve | 138/84 · 120 · 98 · 23 · leve | 138/84 · 118 · 99 · 22 · leve |
| Continua + magnesio + adrenalina | 138/84 · 118 · 99 · 22 · leve | **144/88** · 123 · 99 · **20** · leve · K 3.6 | 144/88 · 122 · 99 · 20 · leve · K 3.5 |

Con el inicio gradual y el decaimiento más rápido de la revisión del 2026-09-20, la diferencia entre dosis puntuales y nebulización continua aparece **a los 60 min**, no a los 90: la dosis puntual ya cedió y la paciente vuelve a SpO₂ 96 y FR 26, mientras la continua se mantiene en 98 y 23. El magnesio agregado a la continua casi no se ve, porque la broncodilatación está cerca de su techo; se mide solo, sin nebulización continua.

### 49m

| Escenario | 20 min | 60 min | 90 min |
|---|---|---|---|
| Sin tratamiento | 30′: 142/86 · 143 · 88 · 31 · severo | 142/86 · 152 · 86 · 33 · severo | 142/86 · **154 · 85 · 35** · severo |
| Dosis puntuales | 142/86 · 124 · 98 · 19 · moderado | 142/86 · 125 · 98 · 19 · moderado | 142/86 · 136 · **95 · 23 · marcado** |
| Nebulización continua | 142/86 · 126 · 99 · 18 · moderado | 142/86 · 125 · 98 · 18 · moderado | 142/86 · 123 · 99 · **17** · moderado |
| Continua + magnesio + adrenalina | 142/86 · 125 · 99 · 17 · moderado | 148/90 · 129 · 99 · 16 · moderado | 148/90 · 129 · 99 · 16 · moderado · K 3.4 · 3.5 |

### Seteo del ventilador

Sobre la 24f sin broncodilatar, es decir con obstrucción 1.0 y resistencia 40 cmH₂O/L/s. Ketamina 100 mg como inductor.

| Seteo | Te | auto-PEEP | Meseta | Pico | PA | VE | Gases |
|---|---|---|---|---|---|---|---|
| Vt 750, FR 30, PEEP 5 | 1.25 s | **15.1** | **35.1** | 71.4 | **108/66** | 22.5 | pH 7.46 · pCO₂ 30 |
| Vt 700, FR 28, PEEP 5 | 1.44 s | 11.5 | 30.5 | 66.8 | 115/70 | 19.6 | pH 7.46 · pCO₂ 30 |
| Vt 450, FR 12, PEEP 0, flujo 80 | 4.66 s | 0.7 | **9.7** | 58.1 | **137/83** | 5.4 | pH 7.14 · pCO₂ 63 |
| Vt 450, FR 10, PEEP 0, flujo 80 | 5.66 s | 0.4 | 9.4 | 57.8 | 137/84 | 4.5 | pH **7.06** · pCO₂ 76 |

El pico se mantiene entre 58 y 71 en los cuatro seteos, y la alarma suena en todos: lo que cambia con el seteo es la meseta, de 35 a 9. La PaO₂ con FiO₂ 100% es 271 en los cuatro. El costo del tiempo espiratorio largo es el pH: bajar de FR 12 a 10 cuesta 0.08 de pH.

### Barotrauma y volumen

Seteo Vt 750, FR 30, PEEP 5 sobre la 24f sin broncodilatar.

| | Tras intubar | Neumotórax | Tras descomprimir |
|---|---|---|---|
| Sin volumen | 108/66 | min 20: **70/43** · SpO₂ 86 · pico 89.6 | 102/62 · SpO₂ 99 |
| 1000 mL antes | **118/72** | min 31: **95/58** · SpO₂ 86 · pico 90.8 | 115/70 · SpO₂ 99 |

El volumen no evita el neumotórax, pero cambia la tolerancia: 70/43 contra 95/58 con el mismo neumotórax. El pulmón se rompe más tarde con volumen porque la trampa tarda más en subir la meseta.

### Ventana de intubación

Con ajuste protector (Vt 450, FR 10, PEEP 0, flujo 80) sobre la 24f.

| Momento | Estado previo | Clasificación | PA tras inducción | Lactato |
|---|---|---|---|---|
| Tras nebulizar | SpO₂ 99, alerta, sin agotamiento | **precoz** | 129/78 | 2.4 |
| 25 min sin tratar | SpO₂ 89, alerta, 7 min de agotamiento | **a tiempo** | 137/84 | 2.1 |
| 80 min sin tratar | SpO₂ 87, alerta, 62 min de agotamiento | **tardía** | **117/71** | **4.0** |

La ventana es estrecha a propósito: una paciente que ya mejoró se clasifica precoz, y basta una hora de agotamiento para que sea tardía.

## Qué más cambió

- **Intubación con comas:** "Intubate with VC/AC at FiO2 100% and PEEP 5" antes se partía en dos órdenes incompletas.
- **Ajustar el ventilador** ya no exige un caso generado.
- **Desconectar el circuito** es una maniobra ejecutable, en español e inglés.
- **La sedación de procedimiento** es ejecutable en los casos del banco, no solo en los generados.
- **PaO₂ con oxígeno:** antes informaba PaO₂ 77 y P/F 77 con SpO₂ 99% y FiO₂ 100%, en todas las familias del banco.
- **Historia:** el intérprete reconoce inhalador, rescate, mantención y exposiciones.

## Fuera de este cambio

- **Heliox, ECMO y ventilación con anestésicos inhalados.**
- **Neumotórax espontáneo** o como causa de la presentación inicial: solo existe como barotrauma del ventilado.
- **Paro cardiorrespiratorio** por intubación demasiado tardía: el precio se paga como hipotensión y lactato, no como paro.
- **Extubación y destete.**
- **Los casos generados por IA** no tienen nada de este bloque: el magnesio es la única pieza disponible ahí.
