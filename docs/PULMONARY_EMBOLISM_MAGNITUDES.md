# Embolia pulmonar — magnitudes implementadas

> **Estado: IMPLEMENTADO** en `pe_obstruction.py` y la rama `pulmonary_embolism` de `family_engine.py`, con las decisiones docentes del 2026-09-20. Son parámetros docentes, no un modelo predictivo. Las trayectorias de abajo salen del motor ya implementado. Las demás familias del banco, PS001 y los casos generados dan exactamente lo mismo que antes.

Aplica a `pulmonary_embolism_33f` (110/70, FC 124, SpO₂ 90%, FR 30, cirugía de tobillo hace 12 días, anticonceptivo con estrógeno) y `pulmonary_embolism_61m` (86/54, FC 132, SpO₂ 88%, FR 32, sobrecarga derecha en el ECG, cáncer de colon en quimioterapia).

## Criterio revisado (2026-09-29, posterior a V3)

Decisión docente del 2026-09-29 («D revisada»). V3 (`3d942ee`) conserva el criterio anterior; los
encuentros jugados antes de este cambio se leen con la regla de su tiempo.

| Qué | Regla actual |
|---|---|
| Shock obstructivo atribuible al TEP | PAS < 90, o un vasopresor que la necesita para sostener ≥ 90, **con** al menos un signo de hipoperfusión. Cumple el criterio desde la llegada o cuando aparece, sin esperar |
| Hipotensión sin hipoperfusión | 15 minutos **completos y consecutivos**. Un minuto que el TEP deja en 90 o más, sin un vasopresor que necesite, reinicia la cuenta (antes: un minuto de recuperación descontaba uno) |
| Noradrenalina | Iniciarla no crea la indicación. Cuenta sólo cuando la presión que deja el TEP estaría bajo 90 sin ella (antes: cualquier minuto con noradrenalina contaba) |
| Signos de hipoperfusión (basta uno) | Conciencia alterada por la presión (PAS atribuible < 80) o escrita al llegar; periferia con llene de 3,5 s o más (frías o «cool» dentro de la categoría «impaired» o peor); lactato interno > 2,0 mmol/L. **Parámetros docentes** del simulador. La somnolencia por sedación no cuenta. No hace falta pedir el lactato para que la fisiología reconozca un shock manifiesto; y un dato interno no demuestra que el residente lo obtuvo |
| Atribución | La presión se calcula antes de redondear, con lo que hacen la obstrucción, la distensión del VD y la presión positiva. El apoyo de vasopresores o inotrópicos, las caídas por sedación, opioide o nitrato y el sangrado tras la lisis conservan su efecto en el paciente, pero no son el shock del TEP |
| Cada orden | Se juzga con el estado de su minuto. Haber cumplido el criterio queda como antecedente (`obstructive_shock_from_min`, `persistent_hypotension_from_min`), no como permiso |
| Segunda dosis | Un shock que persiste no la indica por sí solo: se registra como repetición, la primera dosis sigue actuando y la repetida no tiene efecto propio en el simulador |
| Registro | Cada trombolítico lleva `thrombolysis_indication` (versión 2): motivo (`obstructive_shock`, `persistent_hypotension` o ninguno), minuto y datos internos. El tamizaje de `pe_unindicated_thrombolysis` lo lee; un registro sin ese campo se lee con la regla de su tiempo, nunca como «sin indicación» |
| Texto | «sustained hypotension» sólo se escribe cuando ocurrieron 15 minutos consecutivos. El shock obstructivo no se anuncia en la sala, para no nombrar el diagnóstico |
| Casos generados | Misma regla. El núcleo compartido no separa el efecto de un vasopresor ni las caídas por fármacos: el vasopresor cuenta sólo si se inició con una PAS bajo 90, y la sedación nunca cuenta como conciencia alterada (aproximación documentada) |

**Fuente clínica y parámetros docentes.** La guía ESC 2019 de embolia pulmonar aguda (Konstantinides et
al., *Eur Heart J* 2020;41:543–603, doi:10.1093/eurheartj/ehz405, tabla 4) define la inestabilidad
hemodinámica del TEP de alto riesgo como paro cardíaco, shock obstructivo (hipotensión o vasopresor necesario,
con hipoperfusión de órganos) o hipotensión persistente (más de 15 minutos). El docente consultó la copia
íntegra; esta sesión no pudo abrirla porque la red del entorno la bloquea, y la verificó sólo en resúmenes
secundarios. Los 15 minutos completos, el corte de lactato de 2,0 mmol/L y el llene de 3,5 s son
**aproximaciones docentes de este simulador**, no una reproducción literal de la guía.

**Qué quedó aparte (no resuelto):** la farmacología de una lisis no indicada (hoy no disuelve nada), la
seguridad de las dosis repetidas y la redacción «sustained hypotension» de las declaraciones D3 y C1 y de TDFC.

### Trayectorias de 61m con el criterio revisado

| Trombólisis ordenada en el minuto | Antes (V3) | Ahora |
|---|---|---|
| 0, 5, 10, 14 | Sin indicación; la obstrucción no cambia (84/53 a los 45 min) | Indicada por shock obstructivo: 98/61, FC 125 a los 45 min |
| 15, 16, 20 | Indicada | Indicada (shock obstructivo): 98/61 a los 45 min |
| Sin lisis | 83/52, FC 134 a los 65 min | Igual |

`pulmonary_embolism_33f` con noradrenalina sin hipotensión: antes, a los 15 min el motor anunciaba una
«hipotensión sostenida» que no ocurrió y la lisis quedaba «indicada»; ahora no hay anuncio, la lisis no está
indicada y el tamizaje propone el evento.

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
| Hipotensión sostenida | PAS < 90 durante 15 min. Un minuto de recuperación devuelve un minuto del reloj (hasta V3; ver el criterio revisado) |
| Presión sostenida por vasopresor | **Cuenta como hipotensión**: poner noradrenalina no borra la indicación (hasta V3; ahora sólo si el vasopresor es necesario) |
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
