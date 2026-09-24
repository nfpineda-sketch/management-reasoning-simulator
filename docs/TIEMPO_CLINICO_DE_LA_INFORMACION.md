# Obtener información cuesta tiempo clínico

> Auditoría y corrección del 2026-09-23. Todo medido con el motor real, sin una
> sola llamada pagada.

## 1 · Qué encontró la auditoría

Medí cada tipo de interacción sobre el mismo paciente inestable, una a la vez
desde el mismo punto de partida.

### Lo que ya funcionaba

| | |
|---|---|
| **Los estudios tienen duraciones diferenciadas** | ECG 1, POCUS 2, lactato 5, radiografía 8, laboratorio 10 — declaradas por caso |
| **Varios estudios juntos no se suman** | se procesan en paralelo, el turno cuesta el mayor |
| **Un resultado no aparece antes de su tiempo** | y la muestra congela al paciente en el momento de la toma, así que tratar durante el procesamiento no cambia el resultado retrospectivamente |
| **Cada minuto de reloj corre fisiología** | `_minute()` y `_surface()` por minuto, no un contador |
| **Una entrada con varias órdenes no duplica** | una sola administración por orden |
| **El portón no se abre para pedir estudios** | ni antes ni después de esta corrección |

### Lo que estaba roto

| Hallazgo | Medición |
|---|---|
| **Una pregunta de anamnesis costaba cero minutos** | el panel «Talk» no pasa por el motor: `add_event` y `rerun_app`, sin reloj |
| **Un examen físico costaba cero minutos** | `duration = 0` en el motor; tres exploraciones seguidas dejaban el reloj en 0 |
| **Pedir un estudio congelaba al residente** | `elapsed = max(diagnostic_delay, …)`: pedir un laboratorio costaba **10 minutos muertos** en los que no se podía tratar |
| **Consultar un resultado disponible no se podía decir** | «Revisa el lactato» se rechazaba; la única forma de ver un resultado era volver a pedir el examen |
| **Un examen de varias regiones se retenía** | «Examino la respiración, el abdomen y el corazón» devolvía tres «orden no reconocida» |

El primero y el segundo son el problema que planteaste: **el paciente quedaba
congelado mientras el residente investigaba.** Un paciente inestable y sin
tratar seguía exactamente igual después de cinco interacciones de información.

## 2 · La tabla de tiempos

En `clinical_time.py`, en un solo lugar, y **documentada como supuestos del
simulador pendientes de calibración clínica**.

| Actividad | Tiempo activo | Supuesto |
|---|---|---|
| Consultar un resultado ya disponible | **1 min** | leer algo que ya está |
| Pregunta dirigida al paciente o al acompañante | **2 min** | una pregunta |
| Examen físico de una región | **2 min** | |
| Cada región adicional del mismo examen | **+1 min** | las manos ya están sobre el paciente |
| Examen extenso | **tope de 8 min** | por muchas regiones que se nombren |
| Solicitar un estudio que hace otro | **1 min** | escribir la solicitud |
| Realizar un estudio de cabecera | **su propia duración** | ECG, POCUS, E-FAST, HGT, temperatura |

### Los dos relojes

Lo que estaba fundido en un número ahora son dos cosas distintas:

- **Tiempo activo** — los minutos del residente. Avanzan el reloj y el paciente
  los vive.
- **Tiempo de resultado** — la espera hasta que un estudio vuelve. **No ocupa al
  residente.** Pedir un laboratorio cuesta un minuto y el resultado llega diez
  minutos después, durante los cuales se puede tratar, preguntar, examinar o
  reevaluar.

```
t=  1   pido un panel de laboratorio          pendiente: basic_labs a los 10 min
t=  6   doy ceftriaxona 2 g EV                pendiente: basic_labs a los 10 min
t= 11   reevalúo                              ← el resultado llega en el minuto 10
```

Un estudio de cabecera vuelve cuando el residente deja de mirar, porque era él
quien miraba.

## 3 · Los dos recorridos comparables

El mismo caso de anafilaxia, la misma cantidad de información obtenida.

### Sin tratamiento: la enfermedad no espera

```
llegada                                           84/46  FC 126  SpO2 91  Alert
t=  4  examino respiración, abdomen y general      80/44  FC 129  SpO2 84  Drowsy
t=  5  pido laboratorio y gases venosos            79/43  FC 130  SpO2 84  Drowsy
t=  7  examino el corazón                          77/42  FC 131  SpO2 84  Drowsy
t= 12  reevalúo                                    71/39  FC 136  SpO2 83  Drowsy
```

### Con tratamiento oportuno: el tratamiento sigue actuando mientras investiga

```
llegada                                           84/46  FC 126  SpO2 91  Alert
t=  5  adrenalina 0,5 mg IM                        88/48  FC 123  SpO2 86  Drowsy
t=  9  examino respiración, abdomen y general      93/51  FC 119  SpO2 93  Alert
t= 10  pido laboratorio y gases venosos            95/52  FC 118  SpO2 93  Alert
t= 12  examino el corazón                          97/53  FC 116  SpO2 93  Alert
t= 17  reevalúo                                   101/56  FC 113  SpO2 94  Alert
```

Misma información obtenida, mismos minutos gastados en obtenerla. Lo que
cambió es si el proceso patológico estaba tratado mientras pasaban.

Y un tercer recorrido que importa tanto como los dos anteriores: **el cólico
renal no complicado**, 24 minutos de información, `142/84 · FC 94 · SpO2 98` al
principio y exactamente lo mismo al final. **Nada empeora por preguntar.**

## 4 · La invariancia

Llegar al mismo minuto con las mismas intervenciones da el mismo paciente,
divida como se divida el intervalo:

| | reloj | resultado |
|---|---|---|
| un solo mensaje de 12 minutos | t=12 | 71/39 · FC 136 · SpO2 83 |
| seis exploraciones | t=12 | 71/39 · FC 136 · SpO2 83 |
| tres exploraciones y una espera | t=12 | 71/39 · FC 136 · SpO2 83 |

**El número de mensajes no decide el deterioro.** Lo decide el reloj.

## 5 · Lo que no cuesta tiempo clínico

Por diseño, y con prueba:

- Un turno **rechazado** por una limitación del simulador: 0 minutos.
- Abrir y completar el **formulario de las cuatro categorías**: 0 minutos, y la
  orden se ejecuta una sola vez después.
- Re-renderizar la pantalla o volver a mostrar la misma respuesta: no pasa por
  el motor temporal.

## 6 · En el Management Trace

Cada actividad de información entra al trace con `execution_status:
"information"` — **nunca numerada como decisión**, porque no lo es — y lleva:
la solicitud original, el tipo de actividad, el minuto de inicio, la duración y
el de término, el estado antes y después, **qué resultados seguían pendientes y
a qué minuto llegarían**, y los tratamientos concurrentes.

Las dos lecturas docentes (`management_trace_analysis` y `faculty_analysis`)
aceptan el estado nuevo y lo exponen. Nada aquí etiqueta un intervalo dedicado a
obtener información como un error: registra el hecho, y la pertinencia se valora
con lo que se sabía en ese momento.

## 7 · La evidencia

`test_information_costs_clinical_time.py`, 40 pruebas, cubre las nueve
verificaciones que pediste más la invariancia:

| Verificación | Cómo se comprueba |
|---|---|
| 1 · inestable sin tratar | anafilaxia: 84/46 a 71/39 durante cuatro interacciones de información |
| 2 · con tratamiento oportuno | mismo caso: llega a 101/56 y Alert obteniendo la misma información |
| 3 · paciente estable | cólico renal: 24 minutos y los tres signos idénticos |
| 4 · examen nuevo | pendiente visible, se trata durante la espera, llega al minuto 10 |
| 5 · resultado disponible | revisarlo cuesta 1 min y `diagnostic_history` tiene **una** entrada |
| 6 · órdenes agrupadas | cuatro estudios juntos cuestan un acto de solicitar; un antibiótico administrado una vez |
| 7 · pregunta o examen focalizado | el portón devuelve vacío para examen, estudio y revisión |
| 8 · follow-up y rechazo | ambos 0 minutos; la orden se ejecuta una sola vez después |
| 9 · espera que cruza un evento | el paro de la anafilaxia aparece en el turno que lo cruza |
| **invariancia** | tres formas de llegar al minuto 12 dan el mismo paciente exacto |

Y cuatro más sobre la interfaz, conducida como la conduce un residente:
preguntar cobra 2 minutos, examinar cobra 2, **cambiar de pantalla y
re-renderizar cobran 0**, y el intervalo queda en el trace con su tipo, su
duración y el estado antes y después.

## 8 · La deriva de las doce familias

Pediste revisar si alguna avanza demasiado lento. Medí las 31 casos sin tratar a
los 10, 30 y 60 minutos.

**Una sola estaba genuinamente congelada: la bradicardia.** Un hombre a 74/44 con
frecuencia 38 seguía exactamente igual una hora después, en las cuatro
variantes. Eso enseña que una bradicardia inestable no es urgente.

Ahora cada causa progresa por su propia razón, y ninguna por el hecho de que
pase el tiempo:

| Variante | Por qué avanza | A los 60 min sin tratar |
|---|---|---|
| Bloqueador de calcio | el comprimido sigue absorbiéndose | 74/44 FC 38 → **57/35 FC 20**, y el motor declara el fin |
| Betabloqueo | lo mismo | 80/48 FC 40 → **62/38 FC 23** |
| BAV completo | un ritmo de escape que nadie sostiene no es de fiar | 78/46 FC 32 → **68/41 FC 21** |
| Hiperkalemia | un paciente anúrico sigue fabricando potasio | 84/50 FC 38 K 7,6 → **72/43 FC 26 K 8,2** |

La presión ahora **sigue a la frecuencia**: antes se medía la recuperación contra
el escape actual, así que sólo podía ser cero y la presión nunca se movía.

### Las que quedan en cero, y por qué está bien

| Caso | |
|---|---|
| `acs_48m_wellens` | un patrón de estenosis crítica **sin** oclusión actual; el paciente se ve bien y ésa es la enseñanza |
| `hypoglycemia_*` (3) | **no están congeladas**: la glicemia cae 34→29, la conciencia va de Drowsy a Unresponsive y la convulsión se dispara. Mi métrica sólo miraba presión y saturación |
| `renal_colic_34m` | no debe deteriorarse: la decisión es **no** hospitalizar, y fabricar un declive para que el caso se sienta urgente sería inventar |

### Las lentas que dejé como están

`pneumonia`, `gi_bleed` y la pielonefritis pierden ~9 puntos en una hora. Son
procesos subagudos y la cifra es defendible. El edema pulmonar mantiene la
presión fija —es hipertensivo— pero la conciencia va de Alert a Obtunded, así
que el paciente sí se agota. El asma mueve la frecuencia de 132 a 152 por la vía
del agotamiento, que ya estaba modelada.

## 9 · La dependencia explícita entre órdenes

«Primero espera el resultado y después trata» ahora se respeta.

```
t= 1   pido un panel de laboratorio y espero el resultado, luego ceftriaxona 2 g EV
       → Held as instructed until basic labs is back: ceftriaxone; expected at 10 min
t= 6   reevalúo                        → sigue en espera
t=14   reevalúo                        → el resultado llegó al minuto 10, y el
                                          antibiótico se administró entonces
```

El disparador es **deliberadamente estrecho**: tiene que nombrar la espera
—«espero el resultado», «cuando llegue», «tras el resultado», «wait for the
result», «once it is back»— y no basta con encadenar dos órdenes. «Doy oxígeno y
luego reevalúo» se sigue leyendo exactamente como antes.

Y una orden en espera **sigue respondiendo por su razonamiento**: esperar un
resultado no exime a una orden de manejo de las cuatro categorías.

## 10 · Lo que queda pendiente

- **Los tiempos son supuestos**, centralizados y documentados, sin calibración
  clínica. Cambiar cualquiera es cambiar un número en `clinical_time.py`.
- **La deriva se revisó entera** (sección 8). Las cifras de cada familia siguen
  siendo supuestos: la bradicardia está calibrada contra un solo punto —peri-paro
  a los 60 minutos sin tratar— y los demás no se tocaron.
- **La dependencia sólo entiende una espera por entrada.** «Espera el lactato y
  después trata, y cuando llegue la radiografía hospitaliza» reconoce la primera
  y no la segunda.
- **El panel «Talk» y el botón «Examine»** ahora cobran tiempo; el resto de la
  interfaz no pasa por el reloj y no debe hacerlo.
