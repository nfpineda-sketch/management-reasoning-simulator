# Fisiología de la hemorragia digestiva — magnitudes implementadas

> **Estado: IMPLEMENTADO y REVISADO** en `family_engine.py` (bloque `GI_BLEED` y rama `gi_bleed`), con las decisiones docentes del 2026-09-18 y 2026-09-19, y la revisión de magnitudes del 2026-09-20 (alivio tras la hemostasia más rápido). Son parámetros docentes, no un modelo predictivo. Las trayectorias de abajo salen del motor ya implementado. Las demás familias del banco, PS001 y los casos generados dan exactamente lo mismo que antes.

Aplica a `gi_bleed_57m` (88/54, FC 124, FR 26, llene 5 s, Hb 6.7, lactato 4.4, melena por AINE) y `gi_bleed_72f` (98/62, FC 112, FR 24, llene 4 s, Hb 6.4, lactato 3.4, úlcera previa y naproxeno).

## Decisiones docentes

| # | Pregunta | Decisión |
|---|---|---|
| 1 | Cristaloide contra sangre | "Haz que el volumen solo rinda menos en hemorragia activa". Antes 2 L de suero restauraban la presión casi como una transfusión, con una caída de hemoglobina de solo 0.2 g/dL |
| 2 | Taquipnea | Sigue a la circulación: baja con la sangre y sube sin tratamiento |
| 3 | Hemostasia | La interconsulta lleva a una endoscopia real, pero solo si el paciente está reanimado |
| 4 | Pantoprazol | Reduce algo el sangrado, y solo antes de la endoscopia |
| 5 | Recuperación | Con el sangrado controlado y la anemia corregida, la taquicardia compensatoria cede |
| 6 | Heparina | Se elimina: un bolo dado por error deja de importar, y suspender una infusión cuenta |

## Magnitudes implementadas

Variable interna `circulation`: 1.0 al llegar; **bajar** es mejorar, subir es empeorar. Piso 0.25.

| Mecanismo | Magnitud |
|---|---|
| Sangrado activo | Circulación +0.003/min; hemoglobina −0.009 g/dL/min (0.54 g/dL por hora) |
| Con heparina | +0.002/min y −0.006 g/dL/min extra, proporcional a la exposición |
| Eliminación de heparina | Constante de 60 min |
| **Cristaloide** | Circulación −0.00015 por mL, contra −0.00025 en las otras familias |
| **Fuga del cristaloide** | 60% de esa ganancia se redistribuye con constante de 30 min |
| **Hemodilución** | −0.0006 g/dL por mL: 1 L baja la hemoglobina 0.6 g/dL |
| Sangre | Circulación −0.36 por unidad; hemoglobina +0.85 g/dL por unidad; se entrega en 30 min por unidad si no se indica tiempo |
| **Pantoprazol** | Deja el sangrado en 80%, solo antes de la endoscopia |
| **Endoscopia** | 60 min después de la interconsulta, si PAS ≥ 90 y Hb ≥ 7 o hay sangre corriendo. Reintenta cada 15 min. Deja el sangrado en 10% |
| **Alivio tras hemostasia** | Con endoscopia hecha y Hb ≥ 7: hasta −20 latidos, con constante de **45 min** (revisión del 2026-09-20; antes 90). Reversible si la anemia vuelve |

### Transfundir sin anemia

Aplica a **todas las familias del banco**, no solo a esta (pregunta docente del 2026-09-20). Una unidad son unos 300 mL que entran rápido y se quedan en el intravascular, así que en un paciente sin déficit de transporte el volumen va al pulmón.

| Mecanismo | Magnitud |
|---|---|
| Umbral | Hemoglobina ≥ 10 g/dL **antes** de la unidad |
| Aparición | 30 min |
| Por unidad | SpO₂ −4, FR +4 |
| Pulmón ya congestivo | × 1.6 |
| Tope | 4 unidades |
| Furosemida | 0.012 unidades por mg: 40 mg deshacen media unidad |

En el hombre de 54 años del SCA, con hemoglobina 14.1, dos unidades en 30 min lo llevan de SpO₂ 96 y FR 22 a **88 y 30**; con 40 mg de furosemida vuelve a 90 y 28. En la mujer del edema pulmonar, **una sola unidad** la lleva de SpO₂ 84 a 76 y la FR a 40.

El examen respiratorio pasa a describir crépitos bibasales nuevos desde la transfusión, y el registro lo nombra una vez. El umbral es la hemoglobina y no el diagnóstico: una anemia a medio corregir no tiene castigo, y un paciente ya normalizado sí.

No se modelan la reacción febril no hemolítica, frecuente pero aleatoria en un motor determinista, ni la reacción hemolítica, que exige un error de identificación que el simulador no representa.

### Superficie

| Signo | Magnitud |
|---|---|
| PAS y PAD | −45 y −25 por unidad de circulación sobre 1.0 |
| FC | +25 por unidad de circulación, menos el alivio de la hemostasia |
| **FR** | +15 por unidad de circulación, con piso de 14 |
| Llene capilar | +4 s por unidad de circulación, entre 2 y 8 s |
| Lactato | Basal más 2 por unidad de circulación |
| SpO₂ | No cambia: el oxímetro sigue normal pese a la anemia. Es deliberado |

## Trayectorias del motor

Anotaciones: PA · FC · FR · llene capilar · estado mental · Hb · lactato.

### 57m (Hb 6.7 al llegar)

| Escenario | 30 min | 60 min | 120 min |
|---|---|---|---|
| Sin tratamiento | 84/52 · 126 · 27 · 5.4 s · Hb 6.4 | 80/50 · 128 · 29 · 5.7 s · Hb 6.2 | 72/45 · 133 · 31 · 6.4 s · **somnoliento** · Hb 5.6 |
| Solo cristaloide 2 L | 89/55 · 123 · 26 · 4.9 s · Hb 5.8 | 89/54 · 124 · 26 · 4.9 s · **Hb 5.0** | 78/48 · 130 · 29 · 5.9 s · **somnoliento · Hb 4.4** |
| Solo sangre | 100/61 · 117 · 22 · 3.9 s · Hb 7.3 | 112/68 · 110 · 18 · 2.8 s · Hb 7.9 | 104/63 · 115 · 21 · 3.6 s · Hb 7.3 (**recae**) |
| Sangre + pantoprazol + endoscopia | 101/61 · 117 · 22 · 3.8 s · Hb 7.3 | 114/68 · 109 · 17 · 2.7 s · Hb 8.0 · **endoscopia** | 113/68 · **100** · 18 · 2.8 s · Hb 7.9 (**estable**) |
| Heparina por error | 82/51 · 127 · 28 · 5.6 s · Hb 6.3 | 76/48 · 130 · 30 · 6.0 s · **somnoliento** | 67/42 · 136 · 33 · 6.9 s · Hb 5.3 |

### 72f (Hb 6.4 al llegar)

| Escenario | 30 min | 60 min | 120 min |
|---|---|---|---|
| Sin tratamiento | 94/60 · 114 · 25 · 4.4 s · Hb 6.1 | 90/58 · 116 · 27 · 4.7 s · Hb 5.9 | 82/53 · 121 · 29 · 5.4 s · Hb 5.3 |
| Solo cristaloide 2 L | 99/63 · 111 · 24 · 3.9 s · Hb 5.5 | 99/62 · 112 · 24 · 3.9 s · **Hb 4.7** | 88/56 · 118 · 27 · 4.9 s · **Hb 4.1** |
| Solo sangre | 110/69 · 105 · 20 · 2.9 s · Hb 7.0 | 122/76 · 98 · 16 · 2 s · Hb 7.6 | 114/71 · 103 · 19 · 2.6 s (**recae**) |
| Sangre + pantoprazol + endoscopia | 111/69 · 105 · 20 · 2.8 s · Hb 7.0 | 124/76 · 97 · 15 · 2 s · **endoscopia** | 123/76 · **88** · 16 · 2 s · Hb 7.6 |
| Heparina por error | 92/59 · 115 · 26 · 4.6 s · Hb 6.0 | 86/56 · 118 · 28 · 5.0 s · Hb 5.6 | 77/50 · 124 · 31 · 5.9 s · **somnoliento** |

El contraste docente está en las dos primeras columnas del cristaloide: la presión mejora algo y el llene también, pero la hemoglobina cae más rápido que sin tratamiento, por dilución sobre un sangrado que sigue. A los 120 min el paciente está peor que si no se hubiera hecho nada, y con la mitad de la hemoglobina.

### Endoscopia diferida (57m, interconsulta a los 0 min sin transfundir)

| min | PA | FC | Hb | Evento |
|---|---|---|---|---|
| 60 | 80/50 | 128 | 6.2 | **Se posterga:** "defers endoscopy until the patient is resuscitated" |
| 90 | 76/47 | 131 | 5.9 | Se posterga otra vez, un aviso por orden |
| 150 | 102/62 | 115 | 7.2 | **Endoscopia hecha**, 60 min después de empezar la transfusión |
| 180 | 102/62 | 110 | 7.2 | Estable |

### Recuperación tras la hemostasia (57m, sangre + pantoprazol + interconsulta, y una unidad más a los 60 min)

| min | PA | FC | FR | Llene | Hb | Alivio |
|---|---|---|---|---|---|---|
| 60 | 114/68 | 109 | 17 | 2.7 s | 8.0 | 0.02 |
| 120 | 121/73 | **91** | 15 | 2.0 s | 8.8 | 0.75 |
| 180 | 121/72 | 87 | 15 | 2.1 s | 8.7 | 0.93 |
| 240 | 120/72 | 87 | 15 | 2.2 s | 8.7 | 0.98 |

Con la constante de 45 minutos la FC llega a menos de 100 en dos horas, no en cuatro. Sin este alivio, se quedaba pegada en 105 para siempre, porque el piso de la variable de circulación (0.25) fija la FC mínima del 57m en ese valor.

## Qué más cambió

- **Interconsulta repetida:** "gastroenterology already contacted at minute N; not repeated".
- **Etiqueta de la transfusión:** "Packed red cells 2 units started over 60 min", sin decimales.
- **Órdenes con tiempo de infusión** en todas las familias: volumen, dosis, tiempo y vía.
- **La endoscopia** aparece en el registro como entrada **PROCEDURE**, con su hora, ordenada junto a los resultados de exámenes.
- **El laboratorio básico** ya no imprime la línea "Other measured values are shown below".

## Fuera de este cambio

- **Resangrado.** Tras la endoscopia queda el 10% del sangrado, siempre igual. El mensaje dice que el resangrado es posible, pero no ocurre.
- **Otras terapias:** ácido tranexámico, reversión de anticoagulación, octreótido, ligadura de várices. La hemorragia variceal no es un caso del banco.
- **Sonda nasogástrica, grupo y pruebas cruzadas, plaquetas y plasma.**
- **Los casos generados por IA** no tienen nada de este bloque.
