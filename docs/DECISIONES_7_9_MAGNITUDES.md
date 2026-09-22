# Derivadas adicionales y trabajo respiratorio — magnitudes implementadas

> **Estado: IMPLEMENTADO** el 2026-09-21 en `acs_reperfusion.py`, `clinical_cases.py` y
> `work_of_breathing.py`, con las decisiones docentes 7 y 9 de la revisión del banco.

## Decisión 7 · Derivadas derechas y posteriores

Antes: "Pide un electrocardiograma con derivadas derechas" entregaba **un ECG de 12 estándar**,
sin avisar, y "derivaciones posteriores V7 V8 V9" no se reconocía. El residente que hacía lo
correcto recibía lo mismo que el que no.

### Cómo se piden

| Estudio | Se reconoce |
|---|---|
| **Derechas** | derivadas/derivaciones derechas · ECG derecho · electrocardiograma derecho · V3R · V4R · right-sided ECG/leads · right precordial leads |
| **Posteriores** | derivadas/derivaciones posteriores · ECG posterior · V7 V8 V9 · V7–V9 · posterior ECG/leads |

- Pedir las dos en una orden entrega **las dos**.
- El estudio específico **gana** sobre el ECG de 12 que va escrito en la misma frase: pedir
  "un electrocardiograma con derivadas derechas" es **un** estudio, no dos.
- `electrocardiograma` y `repite el ECG` siguen siendo el de 12 derivaciones, sin cambios.

### Qué muestran

Los hallazgos salen de la declaración coronaria del caso y de **dónde está la arteria ahora**.
Pedir el estudio nunca garantiza un resultado positivo.

| Caso | Derechas (V3R–V4R) | Posteriores (V7–V9) |
|---|---|---|
| **54m inferior con VD**, ocluida | **SDST 1.5 mm en V4R**, 1 mm en V3R | sin SDST |
| **61m posterior**, ocluida | sin SDST | **SDST 1 mm en V7–V9**, concordante con la depresión anterior |
| cualquiera, **arteria abierta** | "el SDST de V4R se resolvió" | "el SDST posterior se resolvió" |
| de Winter, Wellens, tronco, NSTEMI | sin SDST | sin SDST |

### Disponibilidad y honestidad del resultado

- Solo los casos con declaración coronaria tienen estos estudios. En la neumonía el motor
  responde **"Requested study 'ecg_right' is unavailable"** con la lista de lo que sí existe:
  nunca entrega un ECG de 12 haciéndolo pasar por derivadas derechas.
- Mientras no exista el trazado dibujado, el informe **se identifica como sustituto textual**:
  *"Textual report: this encounter records the additional leads in words; the rendered tracing
  shows the standard twelve."*
- El encabezado del resultado dice **"Right-sided ECG (V3R-V4R)"** o **"Posterior ECG (V7-V9)"**
  y **"Performed at minute N"**, no "Investigation · Sample obtained".

## Decisión 9 · El trabajo respiratorio se recalcula en todas las familias

Antes la escala proporcional era solo de la neumonía. El TEP trombolizado bajaba la frecuencia
de 32 a 29, subía la saturación a 95 y seguía diciendo **"Markedly increased"**, que es la
palabra con que el caso fue escrito.

Ahora hay **una escala común** y **determinantes propios de cada fisiopatología**. La palabra
del caso se conserva solo mientras el paciente está donde el caso lo dejó.

### La carga de cada familia

| Familia | De qué se calcula la carga |
|---|---|
| Neumonía | pulmón efectivo (condensación menos reclutamiento) |
| Edema pulmonar | drive congestivo + exceso de pulmón |
| Asma | obstrucción |
| **TEP** | circulación + sobrecarga del VD + carga pulmonar de la obstrucción |
| **Hemorragia digestiva** | circulación |
| **SCA, hipoglicemia** | circulación (o 1.0 si no hay carga respiratoria) |
| Opioides | mantiene su propia regla: es el **drive**, no la carga |
| Ventilación invasiva | mantiene su propia regla: sincronía o disincronía |

### Niveles por unidad de carga

| Familia | Niveles por unidad |
|---|---|
| **Neumonía** | **6.0** (la decisión del 2026-09-21, sin cambios) |
| TEP | 4.0 |
| Edema pulmonar, asma, SCA, hemorragia, hipoglicemia | 3.0 |

### El agotamiento

| Mecanismo | Magnitud |
|---|---|
| Carga que no se puede sostener | **1.25** |
| Tiempo cargándola | **25 minutos** seguidos |
| Soporte (VMNI, invasiva, bolsa) | **reinicia el reloj**: el ventilador descarga los músculos |
| Cómo se informa | **"Exhausted: shallow and ineffective effort"** |

Ese texto **no pertenece a la escala ascendente**: es un sexto estado. Un esfuerzo visible que
baja mientras la carga sube no puede leerse como mejoría.

### Trayectorias del motor

**TEP 61m, trombolizado por hipotensión sostenida** (antes: "Markedly increased" en las cinco filas)

| Momento | FR | SpO₂ | Llene | Trabajo |
|---|---|---|---|---|
| 25 min | 32 | 93 | 5.1 | Markedly increased |
| 85 min (post trombolisis) | 30 | 94 | 4.3 | **Moderately increased** |
| 145 min | 29 | 95 | 3.7 | Moderately increased |

**Asma 24f sin tratamiento**

| Momento | FR | SpO₂ | Carga | Trabajo |
|---|---|---|---|---|
| 20 min | 35 | 89 | 1.04 | Markedly increased |
| 80 min | 38 | 87 | 1.23 | **Severe** |
| 100 min | 39 | 86 | 1.30 | Severe *(12 min de carga alta)* |
| **120 min** | 41 | 85 | 1.37 | **Exhausted: shallow and ineffective effort** |
| 140 min | 42 | 84 | 1.44 | Exhausted |

## Fuera de este cambio

- **El trazado dibujado** de V3R–V4R y V7–V9: el renderizador sigue mostrando las doce
  estándar. El informe lo declara.
- **La interpretación** sigue siendo trabajo del residente: el informe describe el ST y no
  nombra el diagnóstico.
- **Los casos generados por IA** no tienen estos estudios ni esta escala: declaran los suyos.
- **La eficacia ventilatoria** (gases, mecánica) sigue donde estaba; esta decisión separa la
  carga del esfuerzo visible, no reescribe la ventilación.
