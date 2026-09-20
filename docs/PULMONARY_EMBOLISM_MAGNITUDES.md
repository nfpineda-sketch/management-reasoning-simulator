# Embolia pulmonar — magnitudes implementadas

> **Estado: IMPLEMENTADO** en `pe_obstruction.py` y la rama `pulmonary_embolism` de `family_engine.py`, con las decisiones docentes del 2026-09-20. Son parámetros docentes, no un modelo predictivo. Las trayectorias de abajo salen del motor ya implementado. Las demás familias del banco, PS001 y los casos generados dan exactamente lo mismo que antes.

Aplica a `pulmonary_embolism_33f` (110/70, FC 124, SpO₂ 90%, FR 30, cirugía de tobillo hace 12 días, anticonceptivo con estrógeno) y `pulmonary_embolism_61m` (86/54, FC 132, SpO₂ 88%, FR 32, sobrecarga derecha en el ECG, cáncer de colon en quimioterapia).

## Decisiones docentes

| # | Pregunta | Decisión |
|---|---|---|
| 1 | Trombolisis sistémica | Solo con **hipotensión sostenida** |
| 2 | Volumen | **Castigar el volumen a chorro**: el ventrículo obstruido no lo acepta |
| 3 | Sangrado de la trombolisis | Sí, con consecuencia |
| 4 | Intubación precoz en shock obstructivo | Sí, con consecuencia |

## Magnitudes implementadas

| Mecanismo | Magnitud |
|---|---|
| Hipotensión sostenida | PAS < 90 durante 15 min. Un minuto de recuperación devuelve un minuto del reloj |
| Presión sostenida por vasopresor | **Cuenta como hipotensión**: poner noradrenalina no borra la indicación |
| La indicación | No expira una vez alcanzada |
| Volumen tolerado | Hasta 10 mL/min, unos 600 mL/h |
| Exceso de velocidad | +0.0006 de obstrucción por mL por minuto sobre lo tolerado |
| Recuperación del ventrículo distendido | Constante de 45 min |
| Reparto del daño del volumen | 65% como caída de gasto, 35% como peor oxigenación |
| Trombolisis | Empieza a los 5 min; la obstrucción cae hacia 0.62 con constante de 30 min; el espacio muerto hacia 0.80 |
| Sangrado oculto | −0.006 g/dL por minuto en todo paciente trombolisado |
| Sangrado mayor | Con riesgo declarado, desde los 20 min: −0.03 g/dL y +0.0015 de obstrucción por minuto |
| Presión positiva | −0.40 de circulación, más 0.03 por cmH₂O de PEEP sobre 5 |
| Desvanecimiento del costo del tubo | Proporcional a lo disuelto: con la obstrucción resuelta, el tubo no cuesta |

La mujer de 33 años declara `lysis_bleeding_risk="recent_surgery"`: es la razón para sangrar que el caso pone a la vista en la historia.

## Trayectorias del motor

Anotaciones: PA · FC · SpO₂ · FR · estado mental · obstrucción interna · Hb.

### 61m, alto riesgo

| Escenario | 20–30 min | 60–90 min | 120 min |
|---|---|---|---|
| Sin tratamiento | 85/53 · 133 · 88 · 32 | 82/52 · 134 · 87 · 33 | — |
| Oxígeno y heparina | 85/54 · 132 · **99** · 32 | 83/53 · 133 · 99 · 33 | 81/51 · 135 · 99 · 33 (sigue cayendo) |
| **Trombolisis indicada** | 95/59 · 127 · 99 · 30 · obstr 0.81 | 99/61 · 125 · 99 · 29 · obstr 0.71 | **101/62** · 124 · obstr 0.66 |
| Trombolisis al minuto 0 | 84/53 · 133 · 88 · 32 · **sin efecto** | — | — |
| **1000 mL en 10 min** | 12′: **72/46** · 140 · 87 · 34 · **somnoliento** | 32′: 76/48 · 138 | 77′: 79/50 · 136 |
| 250 mL en 30 min | 85/53 · 133 · 88 · 32 · **idéntico a no dar nada** | — | — |
| Intubación precoz, PEEP 5 | 10′: **68/44** · 142 | — | — |
| Intubación, PEEP 12 | 10′: **58/39** · 147 | — | — |
| Intubar después de lisar | 90′: 100/62 · 124 | 100′: **99/61** · 125 (el tubo no cuesta) | — |

El oxígeno corrige la saturación y no cambia nada más: a las dos horas el paciente está peor que al llegar. La anticoagulación tampoco alivia la obstrucción, que es lo que se quiere enseñar.

### 33f, submasiva

| Escenario | 25 min | 65 min | 105–120 min |
|---|---|---|---|
| Oxígeno y heparina | — | 107/69 · 125 · 94 · 31 | 105/67 · 127 · 94 · 31 |
| **Trombolisis sin indicación** | 108/69 · 125 · 90 · Hb **12.3** | 104/67 · 127 · 89 · Hb **10.8** | 99/64 · 130 · 88 · Hb **9.4** |

Dos avisos aparecen en el registro: que la trombolisis se dio antes de que la hipotensión fuera sostenida, con los minutos exactos, y que hay sangrado del sitio quirúrgico operado hace doce días. A las dos horas está peor que la misma paciente sin tratar.

## Qué más cambió

- **Órdenes nuevas:** la trombolisis ya existía por el SCA y aquí tiene su propia rama; el resto son las órdenes del banco.
- **El volumen del TEP dejó de valer por su total** y pasó a valer por su velocidad. Antes cada mL sumaba 0.00005 de obstrucción sin importar en cuánto tiempo entrara.
- **El paro respiratorio de los opioides y la fibrilación del SCA** comparten ahora el mismo estado terminal del motor.

## Fuera de este cambio

- **Trombolisis dirigida por catéter, embolectomía y ECMO.**
- **Hemorragia intracraneal** como forma del sangrado: solo está el sangrado del sitio declarado y el oculto.
- **Dosis reducida de trombolítico** y contraindicaciones absolutas que rechacen la orden.
- **Filtro de vena cava**, y anticoagulación con consecuencias medibles dentro del encuentro.
- **Los casos generados por IA** no tienen nada de este bloque.
