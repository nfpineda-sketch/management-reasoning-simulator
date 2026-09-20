# Síndrome coronario agudo — magnitudes implementadas

> **Estado: IMPLEMENTADO** en `ecg12.py` (morfologías), `acs_reperfusion.py`, `clinical_cases.py` (seis variantes) y la rama `acs` de `family_engine.py`, con las decisiones docentes del 2026-09-19. Son parámetros docentes, no un modelo predictivo. Las trayectorias de abajo salen del motor ya implementado. Las demás familias del banco, PS001 y los casos generados dan exactamente lo mismo que antes.

## Decisión docente

Indicación de la facultad: la conducta y el manejo cambian según el ECG. Hay SCA con SDST, donde se debe activar hemodinamia para ir a abrir la arteria, y SCA sin SDST, donde el manejo es diferente y no se requiere hemodinamia de inmediato. Hay también equivalentes electrocardiográficos que, sin SDST, deben estudiarse agresivamente con coronariografía: el infarto aislado de pared posterior, las T de de Winter, el IDST difuso con SDST en aVR y el síndrome de Wellens, en el que se debe programar coronariografía y nunca hacer un test de esfuerzo. La nomenclatura está cambiando a OMI precisamente para no dejar fuera estos casos, que sin SDST en el ECG de 12 derivadas igual tienen una arteria grande tapada que hay que destapar.

| # | Pregunta | Decisión |
|---|---|---|
| 1 | Puerta-balón | Menos de 90 min en centro con hemodinamia; 120 con traslado; si se anticipa más de 120, trombolisis |
| 2 | Costo de la demora | Troponina, motilidad segmentaria, arritmias (bloqueo AV completo en el inferior, FV tardía), hipotensión y shock: todos plausibles |
| 3 | No-OMI | Antiagregación, anticoagulación y cama monitorizada, con coronariografía diferida y sin castigo por no pedirla de inmediato |
| 4 | Test de esfuerzo en Wellens | Se ejecuta, y el paciente presenta fibrilación ventricular |
| 5 | Nitroglicerina en infarto con riesgo de compromiso derecho | Sí, con la misma mecánica de los casos generados |

## Las seis variantes del banco

| Caso | Llegada | ECG | Troponina | Declaración |
|---|---|---|---|---|
| **54m inferior** | 100/64 · 58 · SpO₂ 96 · FR 22 | `st_elevation_inferior` | 95 | OMI activo, inferior, **compromiso derecho** |
| **66f no-OMI** | 146/86 · 102 · SpO₂ 95 · FR 24 | `st_depression` | 180 | sin oclusión |
| **61m posterior** | 132/80 · 88 · SpO₂ 96 · FR 20 | `posterior_infarct` | 140 | OMI activo, posterior |
| **52m de Winter** | 128/78 · 96 · SpO₂ 95 · FR 24 | `de_winter` | 60 | OMI activo, anterior |
| **48m Wellens** | 138/84 · 76 · SpO₂ 97 · FR 18 | `wellens` | 42 | OMI **sin oclusión activa** |
| **70f tronco** | 104/66 · 112 · SpO₂ 94 · FR 26 | `diffuse_st_depression_avr` | 260 | OMI activo, tronco |

El ECG **no trae interpretación**: el residente lee el trazado. Ninguna presentación nombra el patrón.

## Morfologías

Amplitudes que genera el modelo de onda, medidas derivación por derivación en `test_ecg_omi_morphologies.py`.

| Patrón | ST en el punto J | Onda T | Otros |
|---|---|---|---|
| Posterior aislado | V1 −0.12, V2 −0.22, V3 −0.18 | positiva 0.18 a 0.20 | R/S > 1 en V2–V3 (R 1.15 sobre S −0.40) |
| De Winter | V2–V4 entre −0.14 y −0.16 | 0.79 a 0.89 mV, simétricas | aVR +0.08 |
| IDST difuso con aVR | I −0.12, II −0.20, V3–V6 −0.14 a −0.20 | negativas | **aVR +0.16** |
| Wellens | sin desviación (< 0.03) | V2 −0.28, V3 −0.45, V4 −0.40 | R conservadas |

## Magnitudes del camino

| Mecanismo | Magnitud |
|---|---|
| Puerta-balón, centro con hemodinamia | 90 min desde la activación |
| Puerta-balón con traslado | 120 min |
| Trombolisis | Abre a los 60 min de administrada |
| Troponina | +25 ng/L por minuto de oclusión; **× 1.6** al abrir, por lavado |
| Función regional | Parte en 0.82 y cae 0.0025/min; piso 0.45; recupera 0.0015/min hasta 0.85 |
| Grados de motilidad | ≥ 0.85 normal, ≥ 0.70 leve, ≥ 0.58 moderada, bajo eso acinesia |
| Circulación | +0.0012/min; **+0.0018/min con compromiso derecho** |
| Bloqueo AV completo | A los 45 min de oclusión, solo territorio inferior, FC 42 |
| Fibrilación ventricular | A los 120 min de oclusión, o con test de esfuerzo sobre oclusión inestable |
| Shock | Función regional ≤ 0.55 con arteria cerrada |
| Nitroglicerina con compromiso derecho | Constantes de `nitrate_hazard`: tope 45% de la PAS, mitad del efecto a 15 mcg/min, aparición 2 min, recuperación 12 min, rescate 0.06 mmHg por mL |

**Estado terminal:** en fibrilación ventricular el monitor marca 0, sin pulso, y la reevaluación ordinaria se detiene, igual que en PS001. El manejo del paro está fuera de este build.

## Trayectorias del motor

Anotaciones: PA · FC · ritmo · minutos de isquemia · función regional · troponina.

### 54m inferior, activación a los 20 min

| min | PA | FC | Ritmo | Isquemia | Función | Troponina |
|---|---|---|---|---|---|---|
| 20 | 97/63 | 59 | bradicardia sinusal | 20 | 0.77 | — |
| 65 | 92/59 | **42** | **bloqueo AV completo** | 65 | 0.66 | — |
| 75 | 91/59 | 42 | bloqueo AV completo | 75 | 0.63 | 1720 |
| 110 | — | — | **arteria abierta, ECG basal** | 109 | — | — |
| 130 | 85/56 | 66 | sinusal | 109 | 0.58 | **4455** |
| 190 | 83/54 | 68 | sinusal | 109 | **0.67** | — |

### 54m inferior, sin activar

| min | PA | FC | Ritmo | Función | Troponina |
|---|---|---|---|---|---|
| 45 | 94/61 | 42 | bloqueo AV completo | 0.71 | — |
| 55 | 93/60 | 42 | bloqueo AV completo | 0.68 | 1220 |
| 105 | 87/57 | 42 | bloqueo AV completo | 0.56 | 2470 |
| 140 | **0/0** | 0 | **FV** | 0.47 | — |

### 54m inferior, trombolisis a los 10 min

| min | PA | FC | Ritmo | Isquemia | Función | Troponina |
|---|---|---|---|---|---|---|
| 10 | 99/63 | 59 | bradicardia sinusal | 10 | 0.80 | — |
| 60 | — | — | **arteria abierta, ECG basal** | 59 | — | — |
| 75 | 92/59 | 63 | sinusal | 59 | 0.70 | 2455 |
| 135 | 89/58 | 64 | sinusal | 59 | **0.78** | — |

La trombolisis a los 10 min deja una función de 0.78 a las dos horas; la angioplastia activada a los 20 min deja 0.67, porque tarda 90 min en abrir. Es el contenido docente de la regla de los 120 minutos.

### 52m de Winter

| Escenario | Resultado |
|---|---|
| Activación inmediata | Arteria abierta al minuto 90; a los 105 min, 118/73 · FC 101 · función 0.62 · troponina 3620 |
| Sin activar | A los 70 min, función 0.65 y troponina 1560; **FV a los 130 min** |

**No hace bloqueo AV**, porque el bloqueo solo ocurre en territorio inferior.

### 48m Wellens

| min | PA | FC | Isquemia | Función | Evento |
|---|---|---|---|---|---|
| 60 | 138/84 | 76 | — | 1.00 | nada cambia |
| 120 | 138/84 | 76 | — | 1.00 | nada cambia |
| 210 | 138/84 | 76 | — | 0.85 | **"critical proximal stenosis, stented before it occluded"**, ECG basal |
| 225 | 138/84 | 76 | — | 0.85 | troponina **42**, motilidad normal |

Con la arteria abierta no se infarta nada, la troponina no se mueve y el POCUS sigue normal. El test de esfuerzo, en cambio, fibrila a los 10 min.

### 70f tronco, sin activar

A los 65 min: 98/62 · FC 116 · función 0.66 · troponina 1635 · contracción globalmente reducida. **FV a los 130 min.**

### 66f no-OMI

A las dos horas: 140/83 · FC 105 · troponina **180**, sin cambios, con su motilidad autorizada intacta. Activar hemodinamia responde que la angiografía inmediata no es necesaria y que el camino es antiagregación, anticoagulación y cama monitorizada.

### Nitroglicerina 20 mcg/min en el 54m

| min | PA | Estado |
|---|---|---|
| 5 | **68/46** | somnoliento |
| 15 | 66/45 | somnoliento |
| 27 | 97/62 | alerta, tras suspenderla y dar 500 mL |

## Qué más cambió

- **Órdenes nuevas:** `Activate the cath lab`, `Give tenecteplase 40 mg IV` (también alteplasa y estreptoquinasa, en los dos idiomas) y `Order a stress test` / `test de esfuerzo`.
- **ECG dinámico:** el perfil cambia con la reperfusión, así que repetir el ECG informa. Antes era fijo para todo el encuentro.
- **El camino se informa como entrada propia** del registro, con su hora.
- **La trombolisis sin oclusión** queda registrada como riesgo de sangrado sin arteria que abrir.
- **El magnesio y la trombolisis** quedaron disponibles también para los casos generados, porque el contrato de capacidades exige que todo medicamento del motor exista ahí.

## Fuera de este cambio

- **Traslado:** los 120 min están implementados, pero los seis casos son centros con hemodinamia, así que ningún caso fuerza todavía la decisión de trombolisis por demora.
- **Antiagregación dual y anticoagulación:** el motor acepta las órdenes pero no las modela.
- **Manejo del paro:** desfibrilación, compresiones y adrenalina en FV no son ejecutables.
- **Complicaciones mecánicas:** insuficiencia mitral aguda, rotura septal, taponamiento.
- **Derivaciones posteriores o V7–V9**, ECG seriado automático, y monitorización continua del ST.
- **Los casos generados por IA** no tienen nada de este bloque.
