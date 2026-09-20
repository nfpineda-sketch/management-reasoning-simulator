# Mecanismos clínicos en los casos generados por IA

> **Estado: IMPLEMENTADO** el 2026-09-20. Siete mecanismos compartidos entre el banco y los casos generados, con compuertas obligatorias. Las magnitudes viven en los módulos del banco y están documentadas en los siete documentos de magnitudes; aquí se documenta **la arquitectura, las declaraciones, las compuertas y lo que cambia en un caso generado**.

## El problema que resuelve

Los casos generados ya ejecutaban las órdenes del banco: `coupled_encounter.execute` llama a `family_engine._order`, el mismo que activa hemodinamia, da trombolisis, descomprime un tórax o administra octreótido. Lo que faltaba es que **alguien leyera sus efectos**. El motor generado tiene su propio estado y su propia superficie, así que cuando `_order` marcaba "arteria abierta al minuto 110", nada lo miraba.

El resultado era una brecha creciente: el banco tenía barotrauma, ventanas de reperfusión, antídotos y ventilador; un caso generado de la misma enfermedad no tenía nada de eso.

## El patrón

Cada mecanismo tiene tres partes, y el precedente es `nitrate_hazard`, que ya funcionaba así desde el 2026-09-18.

1. **Declaración en el contrato.** Un campo en `engine`, obligatorio en el esquema y nulo cuando no aplica.
2. **Compuerta de coherencia.** Corre en `collect_clinical_issues`, antes de la revisión, y **obliga**: si el caso describe el hallazgo, debe declarar el mecanismo; si lo declara sin que el residente pueda descubrirlo, se rechaza.
3. **Efectos como deltas observables.** El mecanismo no toca las variables internas del banco: devuelve caídas de presión, cambios de frecuencia, saturación o laboratorio, y el adaptador los suma a `physiology_inputs`. El núcleo compartido sigue siendo el dueño de la fisiología.

Declarar un mecanismo también **autoriza sus órdenes** sin que el autor escriba reglas de respuesta.

## Los siete mecanismos

| Declaración | Campos | Qué obliga a declararla |
|---|---|---|
| `engine.coronary` | `omi`, `active_occlusion`, `territory`, `rv_involvement`, `pci_capable`, `symptom_onset_min` | Un `ecg_profile` de oclusión |
| `engine.airway_obstruction` | `severity` (0.3 a 1.3) | Sibilancias, espiración prolongada o entrada de aire reducida en el examen o la historia |
| `engine.pulmonary_obstruction` | `bleeding_risk` (nulo, `recent_surgery` o `severe_hypertension`) | Ventrículo derecho dilatado o con D-sign o McConnell en el POCUS, o defectos de llene en el angioTAC |
| `engine.glucose_failure` | `sulfonylurea`, `thiamine_deficient` | Glucosa de llegada bajo 70 mg/dL |
| `engine.opioid_toxidrome` | `long_acting` | Un opioide o pupilas puntiformes en la historia **y** FR bajo 12 |
| `engine.active_bleeding` | `established` | Melena, hematemesis, deposiciones negras o sangrado descrito |
| `engine.pulmonary_congestion` | `cardiogenic` | Líneas B difusas, crépitos bilaterales o edema pulmonar descrito |

Más `engine.nitrate_hazard`, que ya existía.

### Códigos de rechazo

`CORONARY_UNDECLARED`, `CORONARY_ECG_MISMATCH`, `CORONARY_UNDISCOVERABLE`, `AIRWAY_OBSTRUCTION_UNDECLARED`, `AIRWAY_OBSTRUCTION_UNDISCOVERABLE`, `PULMONARY_OBSTRUCTION_UNDECLARED`, `PULMONARY_OBSTRUCTION_UNDISCOVERABLE`, `GLUCOSE_FAILURE_UNDECLARED`, `GLUCOSE_FAILURE_UNDISCOVERABLE`, `OPIOID_TOXIDROME_UNDECLARED`, `OPIOID_TOXIDROME_UNDISCOVERABLE`, `ACTIVE_BLEEDING_UNDECLARED`, `ACTIVE_BLEEDING_UNDISCOVERABLE`, `PULMONARY_CONGESTION_UNDECLARED`, `PULMONARY_CONGESTION_UNDISCOVERABLE`.

Todas las compuertas ignoran menciones negadas, oración por oración, como ya hacía el riesgo de nitratos: "no wheeze" no obliga a declarar broncoespasmo.

### Exigencias de descubribilidad

| Declaración | Además exige |
|---|---|
| Coronaria | Territorio coherente con el patrón; Wellens con `active_occlusion` falso; compromiso derecho solo en SDST inferior; troponina numérica |
| Obstrucción pulmonar | Un riesgo de sangrado declarado debe aparecer en la historia: "operado hace doce días" |
| Glucosa | La sulfonilurea debe estar nombrada en los medicamentos; la depleción de tiamina debe explicarse por alcohol o ayuno |
| Opioides | La exposición y la FR baja, las dos |
| Sangrado | Una hemorragia `established` debe llegar anémica: hemoglobina de 10 g/dL o menos |

## Órdenes que autoriza cada declaración

| Mecanismo | Órdenes |
|---|---|
| Coronario | trombolisis, test de esfuerzo |
| Vía aérea | desconexión del circuito, descompresión torácica, magnesio, nebulización continua, adrenalina en goteo y en bolo, broncodilatador, corticoide, sedación de procedimiento |
| Obstrucción pulmonar | trombolisis |
| Glucosa | dextrosa, infusión de glucosado, octreótido, glucagón, tiamina, carbohidrato oral |
| Opioides | naloxona, infusión de naloxona, bolsa-mascarilla |
| Sangrado | sangre, inhibidor de bomba de protones |
| Congestión | bolo IV de nitroglicerina |

Sin la declaración, esas órdenes siguen respondiendo "outside the main/IA core and has no declared disease-specific response".

## Calibración: el núcleo amplifica

Tres ajustes que hubo que hacer porque el núcleo compartido reacciona con fuerza a lo que recibe:

| Ajuste | Banco | Caso generado | Por qué |
|---|---|---|---|
| Bloqueo AV completo | FC impuesta en 42 | −12 latidos y −6 mmHg, con rampa de 5 min | Imponer la frecuencia como delta colapsaba al paciente en trece minutos |
| Auto-PEEP | −2.0 mmHg por cmH₂O | −1.2 | La misma razón |
| Tope del mecanismo | sin tope | −30 mmHg | El mecanismo empuja, no gobierna |

Y dos hallazgos de integración:

- **El núcleo ya modela la dextrosa**, así que sumar el delta del mecanismo la contaba dos veces: el monitor marcaba 230 en un paciente que estaba en 130. Con la declaración presente, **el mecanismo es el dueño** de la glucosa que se muestra y del estado mental que explica.
- **El decaimiento de la naloxona vivía en el minuto del banco**, que no corre para casos generados, así que el antídoto no se iba nunca. Ahora vive en `opioid_reversal.step`, que llaman los dos motores. El banco quedó idéntico.

## Comportamiento verificado en casos generados

| Mecanismo | Verificado |
|---|---|
| Coronario | Activación con su nota y puerta-balón de 90 min; bloqueo AV a los 45; arteria abierta al minuto 90; ECG que resuelve a basal; troponina de 90 a 3690 |
| Vía aérea | Obstrucción que progresa y responde al salbutamol; Vt 750 y FR 30 dan auto-PEEP 15.7, meseta 35.7 y pico 88; neumotórax a tensión con −30 mmHg; descompresión y ajuste protector que lo revierten; presiones en el update |
| Obstrucción pulmonar | 1000 mL en 10 min cuestan 13 mmHg, 250 mL en 30 no cuestan nada; el reloj de hipotensión corre bajo vasopresor; la trombolisis indicada disuelve; el sangrado declarado baja la hemoglobina informada 0.84 g/dL |
| Glucosa | Glucosa que cae y monitor que lo muestra; ampolla que despierta; sulfonilurea que la vuelve a llevar; octreótido que la corta; convulsión a los 20 min |
| Opioides | 0.4 mg con bolsa-mascarilla lleva la FR a 12; a los 45 min el antídoto se fue; la infusión sostiene al de acción prolongada; 2 mg dan FC 128 y agitación; 20 min de apnea terminan en asistolia |
| Sangrado | La hemoglobina cae sin tratamiento; dos unidades la suben; un litro de suero la deja más de un punto por debajo; el pantoprazol la frena; la endoscopia se posterga mientras el paciente no esté reanimado |
| Congestión | 2000 mcg de bolo bajan la PA 11 mmHg al tercer minuto, el efecto se disipa a los 15, y lo descargado queda como mejor saturación y menor frecuencia |

Sin declaración, las trayectorias del banco, de los casos generados y de PS001 son **idénticas byte a byte**.

## Por qué la congestión es el mecanismo más delgado

El núcleo compartido **ya modela la congestión**: tiene `pulmonary_congestion` como variable, el volumen la empeora, y el oxígeno, la ventilación no invasiva, la nitroglicerina en infusión y la furosemida son acciones nativas que el núcleo responde. Construir un segundo modelo encima habría duplicado el cálculo, que es el error que cometió la primera versión del mecanismo de glucosa: el monitor marcaba 230 en un paciente que estaba en 130.

Por eso este mecanismo agrega solo lo que el núcleo no cubre —el bolo IV de nitroglicerina, que el banco inventó para esta enseñanza— y deja el resto donde está. La declaración, además, autoriza el bolo y declara la intención del caso.

El de hemorragia, en cambio, es completo: el núcleo modela volumen, pero **no modela perder sangre**. Sin este mecanismo, un caso generado sobre un paciente que sangra no sangraba en absoluto.

## Fuera de este cambio

- **Ninguna corrida pagada** se ejecutó para verificar esto. Lo que falta saber es si el autor de IA **declara el mecanismo cuando corresponde**; si no lo hace, la compuerta rechaza el caso y la generación reintenta, con el costo que eso implica.
- **Las instrucciones al autor** describen el mecanismo coronario en detalle; los otros seis se validan por compuerta pero no se explican en el prompt.
- **Las magnitudes específicas del edema pulmonar del banco** —reclutamiento de la VMNI, tope del 30% de la PAS para la nitroglicerina, la furosemida que casi no sirve antes de resolver— siguen siendo solo del banco.
