# Fase 3 · Ratificación de la instantánea de desarrollo de la vía común de tono vascular (P3-415 a P3-423)

Encargo del 2026-11-18. Rama `phase-3-runtime-integration`; linaje `PHASE2_AMENDMENT_3` (certificado, digesto `867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c`); conjunto revisado `COMMON_TONE_V1_MULTIFAMILY_FACULTY_REVIEW`; testigo revisado `CENTER_REFERENCE`.

**Esto es un registro de decisión. No cambia fisiología, parámetros, trayectorias, acoplamiento con la poscarga, autoridad, puntuación ni el primer piloto, y no es una validación clínica.** Convierte la revisión docente humana de las cinco trayectorias de presión ante una orden de norepinefrina en una ratificación de desarrollo, duradera y trazable. La instantánea es un **registro que nada ejecutable lee**.

## 0 · Qué se decidió (decisión docente del 2026-11-18; FD-TONE-RATIFY-01 a FD-TONE-RATIFY-09)

| Decisión | Contenido |
|---|---|
| **FD-TONE-RATIFY-01** | Totales de la revisión: `ACCEPT` 1, `ACCEPT_WITH_LIMITATION` 3, `RECALIBRATE` 0, `REJECT` 1. El único `REJECT` es un vasopresor clínicamente inapropiado en un paciente con edema pulmonar ya gravemente hipertenso: **no** se lee como fallo del mecanismo común de tono. |
| **FD-TONE-RATIFY-02** | La vía común de tono vascular es **aceptable para desarrollo** en contextos de vasopresor de soporte bien seleccionados. |
| **FD-TONE-RATIFY-03** | `CENTER_REFERENCE` se promueve a **`COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1`**: instantánea **de desarrollo**, no calibración clínica, ni validación de producción, ni aprobación para residentes. |
| **FD-TONE-RATIFY-04** | `LOW` y `HIGH` siguen siendo `TEST_WITNESS_ONLY`; sin otro ciclo de calibración salvo que lo exija evidencia futura. |
| **FD-TONE-RATIFY-05** | `COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED` persiste como **limitación de desarrollo monitoreada**: bloquea la promoción educativa del comportamiento del vasopresor en familias limitadas por la bomba; **no** bloquea el desarrollo del mecanismo común. |
| **FD-TONE-RATIFY-06** | El escenario de edema pulmonar hipertenso se clasifica `INAPPROPRIATE_INTERVENTION_CONTEXT` y, opcionalmente, `NEGATIVE_CONTROL_CANDIDATE` para trabajo futuro de razonamiento de manejo. **No** se altera su fisiología para que la intervención parezca beneficiosa. |
| **FD-TONE-RATIFY-07** | `CONSCIOUSNESS_UNDER_TONE_UNRESOLVED` persiste: sigue bloqueada la interpretación de consciencia derivada de la presión bajo soporte de tono activo. |
| **FD-TONE-RATIFY-08** | `TITRATION_AND_STOP_NOT_SUPPORTED` persiste como la **siguiente brecha de manejo de alta prioridad**; el siguiente objetivo de implementación es la semántica de cambio de tasa, titulación y suspensión de norepinefrina. **No se implementa** en este paquete. |
| **FD-TONE-RATIFY-09** | No se requiere revisión de sensibilidad para la decisión actual; la revisión opcional LOW/HIGH queda como trabajo futuro y no retrasa la ratificación. |

## 1 · P3-415 · La evidencia humana, tal como se reportó

Registro: `docs/revision/PHASE3_HUMAN_COMMON_TONE_MULTIFAMILY_REVIEW.json` (versionado, sellado, indexado; digesto `50807dfc418226aed48826864abf6ac14c8d5d785f9e1f2ed68207091afe0804`). Es evidencia **humana**, separada del análisis del modelo (clases `HUMAN_FACULTY_REVIEW`, `MODEL_ANALYSIS` y `TEST_RESULT`). Los juicios y las interpretaciones se transcribieron una sola vez desde el reporte, sin cambiar una palabra.

| Escenario | Global | Q1 dirección | Q2 tiempo | Q3 magnitud | Q4 respuesta al manejo | Q5 riesgo educativo |
|---|---|---|---|---|---|---|
| Hemorragia digestiva (FR-F) | `ACCEPT_WITH_LIMITATION` | Expected | Plausible | Plausible | Coherent | Maybe |
| Sonda sintética de bajo tono (SYNTH) | `ACCEPT` | Expected | Plausible | Plausible | Coherent | No |
| ACS / limitado por la bomba | `ACCEPT_WITH_LIMITATION` | Expected | Plausible | Plausible | Uncertain | Yes |
| Edema pulmonar hipertenso | `REJECT` | Expected | Plausible | Too large | Incoherent | Yes |
| Embolia pulmonar de alto riesgo (PE) | `ACCEPT_WITH_LIMITATION` | Expected | Plausible | Plausible | Coherent | Maybe |

**Procedencia: `HUMAN_FACULTY_REVIEW_REPORTED_NOT_STORE_VERIFIED`.** El almacén persistido de esa revisión (los registros por evento de la propia persona revisora) **no está** en el repositorio ni en este contenedor; el encargo pedía leerlo si estaba disponible y, si no, usar lo reportado y marcarlo. Por eso el registro **no verifica** las respuestas contra el almacén, ni el orden de los escenarios tal como se persistió, ni el estado de finalización, ni los eventos de bloqueo y envío, ni la apertura del chequeo opcional de sensibilidad. **No se inventó** ningún comentario libre (`NONE_REPORTED`), ni evento, ni respuesta de sensibilidad, y **no se registra el nombre** de la persona revisora. Cada escenario queda atado al conjunto fijado por el digesto de su ítem (`FR-F d8ca8ea38d43`, `SYNTH 92728a6fa840`, `ACS c1e87b70f49b`, `PULM-EDEMA 6709f611aa8b`, `PE eb8970436cfb`) y por el de su trayectoria. Las revisiones anteriores (primera revisión humana, re-revisión humana, conjunto de esta revisión y su punto de control, sondas y candidato FR-F) se **preservan**: sus archivos son los que fija el índice y el registro las nombra por digesto y huella.

## 2 · P3-416 · Clasificación escenario por escenario

Vocabulario: `MECHANISM_FAILURE`, `INAPPROPRIATE_INTERVENTION_CONTEXT`, `EDUCATIONAL_LIMITATION` (más `DEVELOPMENT_POSITIVE_CONTROL` para el control positivo). **Regla: un escenario es un `MECHANISM_FAILURE` sólo si el juicio humano registrado lo dice; ninguno lo dice.** La clasificación **no la deriva el modelo de los números**: cada entrada cita el texto humano registrado en el que se apoya (`human_basis`) y una prueba rechaza una cita que no esté en el registro humano.

| Escenario | Clasificación | Limitación asociada | Qué significa |
|---|---|---|---|
| Hemorragia digestiva | `EDUCATIONAL_LIMITATION` | `COMMON_TONE_PRESSURE_BENEFIT_MUST_NOT_IMPLY_VOLUME_CORRECTION` | La respuesta temprana es apropiada; el beneficio es incompleto y se atenúa mientras la hemorragia sigue sin tratar; no se lee como corrección de la pérdida de volumen. |
| Sonda sintética de bajo tono | `DEVELOPMENT_POSITIVE_CONTROL` | — | El mecanismo hace lo que debe en el único estado construido para probarlo y no devuelve el sistema a su línea de base. |
| ACS / limitado por la bomba | `EDUCATIONAL_LIMITATION` | `COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED` | Dirección y tiempo defendibles; paciente no hipotenso, limitado por la bomba, y la norepinefrina no corrige la falla de bomba. **No** se recalibra globalmente desde este escenario. |
| Edema pulmonar hipertenso | `INAPPROPRIATE_INTERVENTION_CONTEXT` (+ `NEGATIVE_CONTROL_CANDIDATE`) | — | La docencia rechazó dar este vasopresor a este paciente; **no** la forma en que el mecanismo común responde. |
| Embolia pulmonar de alto riesgo | `EDUCATIONAL_LIMITATION` | `COMMON_TONE_PRESSURE_BENEFIT_MUST_NOT_IMPLY_OBSTRUCTION_CORRECTION` | Soporte hemodinámico temporal defendible en choque obstructivo; no implica corregir la obstrucción vascular pulmonar. |

### Auditoría del `REJECT` del edema pulmonar

- **Lo registrado:** Q1 Expected y Q2 Plausible (dirección y tiempo correctos); Q3 Too large, Q4 Incoherent y Q5 Yes, **con la explicación de la propia docencia**: el paciente ya está profundamente hipertenso con edema pulmonar cardiogénico agudo, la norepinefrina es clínicamente inapropiada y lleva la presión a un rango extremo. El `REJECT` es **principalmente un juicio del contexto de manejo y del uso educativo**; **no** es, por sí solo, evidencia de que el mecanismo común requiera recalibración global; **no** se reajusta `T` para que la norepinefrina parezca aceptable en un paciente que no debe recibirla.
- **¿El juicio registrado sostiene un fallo del mecanismo?** No. Ningún escenario fue `RECALIBRATE`.
- **Análisis del modelo (no juzga; `MODEL_ANALYSIS`)**, leído del registro certificado de sondas, minuto 30: la **misma** respuesta relativa (razón de presión 1,192661) en edema pulmonar, hemorragia digestiva, asma y opioide, y algo mayor en ACS (1,217297) y embolia pulmonar (1,215861). La ganancia absoluta es la mayor en el edema (28,9 mmHg de PAM, de 150 a 178,9 mmHg) porque su línea de base es la más alta, no porque el mecanismo actúe distinto ahí. Cambiar `T` para reducir ese aumento cambiaría todas las familias, para que se vea mejor en un paciente que no debe recibir el fármaco. **No se cambió nada.**
- **Se conserva la acción disponible** (`norepinephrine_made_unavailable = false`): la acción es inapropiada en ese contexto, no en general, y el mecanismo común debe seguir representándola para que la orden inapropiada tenga una consecuencia que se pueda juzgar.

## 3 · P3-417 · Ratificación para desarrollo

Registro: `docs/revision/COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json` (digesto `a5a8f4370e240a07406111e0fedf40884e7e382dbd08643949bc82201452bab2`). **Se ratifica** la vía común de tono vascular (soporte vasoconstrictor de la Enmienda 3, con la norepinefrina a tasa fija como primer escritor) **para experimentos de desarrollo** en contextos de vasopresor de soporte bien seleccionados. **Es:** una ratificación de desarrollo. **No es:** una calibración clínica, una validación de producción, una aprobación para residentes, una afirmación de validación clínica, una aprobación de la norepinefrina en ningún paciente ni una promoción educativa del comportamiento del vasopresor. **No amplía ninguna autoridad:** `COMMON_CORE_RUNTIME_AUTHORITY = False`; la concesión viva sigue siendo `GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3` (sólo presión de GI; la norepinefrina **sigue no concedida**).

## 4 · P3-418 · `COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1`

Registro: `docs/revision/COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1.json` (digesto `ee1740ca77173ce0797268f8327f21fc29304c5c54ff2c642c1f2bdfb3270356`). Es **exactamente** el `CENTER_REFERENCE` que la docencia revisó, **copiado y no recalculado**, ni optimizado, ni sustituido por el valor de otro testigo:

| Parámetro | Valor | Unidad |
|---|---|---|
| `tone_gain` | 0,6 | fracción del tono de llegada (lo que toma el campo de perfil `vasoconstrictor_support_to_tone_gain`) |
| `half_effect_rate_mcg_min` | 10,0 | mcg/min |
| `onset_tau_min` | 1,5 | min |
| `offset_tau_min` | 2,5 | min |

Los cuatro valores son **un solo punto** de la región de desarrollo; ninguno se sustituye por el de otro testigo y ninguno es un rango aparte. El registro prueba que son **iguales** en el núcleo certificado (`clinical_core.vascular_support.witness('CENTER_REFERENCE')`), en el registro certificado de sondas y en el candidato certificado de FR-F (con las huellas de archivo de ambos), y ata las trayectorias revisadas por su digesto. Dentro de la región (`tone_gain` 0,3–0,9; `half_effect_rate_mcg_min` 5–20; `onset_tau_min` 0,5–3,0; `offset_tau_min` 1,0–5,0), **todas las confianzas siguen por debajo de 0,80**: no se adopta una región estrecha y el punto **no es una calibración** (FD-TONE-06).

**`LOW` y `HIGH` siguen siendo `TEST_WITNESS_ONLY`** (no se promueven; se reabren sólo si evidencia futura exige otro ciclo). **Los registros certificados anteriores** (`PHASE3_COMMON_TONE_PROBES.json`, `PHASE3_FRF_TONE_V1_CANDIDATE.json`) **siguen diciendo `chosen_witness: null`**: son historia inmutable (FD-RECORD-01) y no se editan; la ratificación es el registro que ahora dice cuál testigo se revisó y se aceptó para desarrollo.

**Es un registro que nada ejecutable lee.** `runtime_tone_support.py` sigue tomando un **nombre** de testigo para una copia de desarrollo en la sombra, ningún adaptador registrado declara el lector y la autoridad viva de presión de GI **sigue deteniéndose** ante una orden de norepinefrina. Vincular algo a esta instantánea sería un paso **ejecutable** aparte, con su propia autorización y recertificación; una prueba asegura que ningún módulo de la raíz ni del núcleo menciona los registros nuevos.

## 5 · P3-419 y P3-420 · Limitaciones y control negativo (persistidos en la ratificación)

| Identificador | Estado | Bloquea | No bloquea |
|---|---|---|---|
| `COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED` | `MONITORED_DEVELOPMENT_LIMITATION` | la promoción educativa del comportamiento del vasopresor en familias limitadas por la bomba | el desarrollo continuado del mecanismo común; esta ratificación |
| `CONSCIOUSNESS_UNDER_TONE_UNRESOLVED` | `OPEN_DEVELOPMENT_LIMITATION` | la interpretación de consciencia derivada de la presión bajo soporte activo; cualquier autoridad de consciencia o interpretación visible al residente bajo ese soporte | el desarrollo continuado del mecanismo común |
| `TITRATION_AND_STOP_NOT_SUPPORTED` | `NEXT_HIGH_PRIORITY_MANAGEMENT_GAP` | afirmar que se representa un cambio de tasa o una suspensión | esta ratificación |

- **Dependencia de la bomba:** el costo de salida del tono es **una** sensibilidad para toda bomba y volumen (limitación certificada de la vía); cómo debe depender la respuesta de presión del estado de la bomba **no** está validado, y la revisión de ACS (no hipotenso, limitado por la bomba) es donde se hizo visible. **No se hace ahora:** una sensibilidad de poscarga específica de la bomba ni una recalibración global. Se reabre sólo si una revisión docente futura la pide, otra familia limitada por la bomba muestra el mismo déficit, o se propone un uso educativo del vasopresor en una de ellas.
- **Consciencia bajo tono:** las lecturas de consciencia salen de la presión, de modo que con soporte se leen **mejor** mientras el gasto y la entrega son menores (limitación certificada); el mapeo de desarrollo rechaza el soporte sobre un testigo de consciencia de la Enmienda 2.
- **Control negativo:** `HYPERTENSIVE_PULMONARY_EDEMA_NOREPI` (`pulmonary_edema_58m`) = `INAPPROPRIATE_INTERVENTION_CONTEXT`, candidato opcional a escenario de manejo de control negativo (un vasopresor ordenado a un paciente profundamente hipertenso con edema pulmonar cardiogénico agudo). **No se construyó**, no se alteró su fisiología y la norepinefrina **no** se hizo indisponible.

## 6 · P3-421 · Siguiente prioridad de implementación: `NOREPINEPHRINE_TITRATION_AND_STOP_SEMANTICS` (sin implementar)

Hoy `runtime_tone_support.py` mapea **sólo** el primer inicio de norepinefrina a tasa fija en mcg/min; un ajuste, una suspensión, una dosis por peso y cualquier inicio posterior son brechas declaradas. **Comportamiento futuro deseado:** iniciar, aumentar, disminuir y suspender, **por el mismo escritor común** del soporte vasoconstrictor, **sin** atajos fármaco → mmHg, **sin** varios escritores de tono en competencia y **sin** ramas por caso.

**Primer paso cuando se autorice (no ahora):** una auditoría de lo que el motor refleja ante un cambio de tasa y una suspensión, de cómo el escritor representa una tasa que cambia en el tiempo y de qué significa cada orden para el soporte que la constante de cese ya decae. **Nada de esto está implementado ni autorizado a implementarse.** Es una decisión docente autorizar su inicio.

## 7 · Frontera: lo que NO cambió

Sin recalibración del tono; sin modificación del acoplamiento con la poscarga; `CENTER_REFERENCE` sin alterar; `LOW`/`HIGH` sin promover; sin ampliación de autoridad (norepinefrina sigue no concedida); sin recalibración de GI; sin cambio de control de fuente; sin autoridad de consciencia ni terminal; sin despliegue a residentes; sin afirmación de validación clínica; sin titulación ni suspensión; sin tocar `clinical_core/` (digesto `867bac09…`), `family_engine.py`, la instantánea de presión de GI, las concesiones, la página del encuentro, la puntuación, el primer piloto, el lector, el corpus de validación, V3 ni los baselines. Ni respuestas externas, ni IA de la app, ni correo.

## 8 · P3-422 · Validación

Análisis de dependencias: no se añadió ni cambió ningún módulo ejecutable de la raíz ni del núcleo; los archivos nuevos son tres registros versionados, el arnés constructor (con nombre de prueba, que ninguna página importa), dos archivos de pruebas, este documento, filas de decisión y deuda y una nota en `CLAUDE.md`; el índice de registros crece en tres entradas más la del punto de control. Por eso la validación es **focalizada** (ver el punto de control, `docs/revision/PHASE3_COMMON_TONE_RATIFICATION_CHECKPOINT.json`, para las cifras exactas sobre la huella certificada).

Pruebas: `test_phase3_tone_ratification.py` (registros: evidencia humana igual a la reportada, respuestas válidas, totales, ligadura al conjunto fijado, preservación de lo anterior, clasificación, mutantes —un `REJECT` clasificado como fallo del mecanismo, una recalibración que la docencia no pidió, una cita ausente, una respuesta que no es una opción—, instantánea igual en el núcleo y en los registros certificados, `LOW`/`HIGH` de prueba, limitaciones, siguiente prioridad no implementada, nada ejecutable cambiado ni autoridad ampliada, regeneración bajo el mismo código) y `test_phase3_tone_ratification_records.py` (decisiones, deuda, documento, `CLAUDE.md` y punto de control dicen lo mismo). El arnés constructor es `test_tone_ratification_analysis.py`.

## 9 · P3-423 · Punto de control: **A · `COMMON_TONE_DEVELOPMENT_SNAPSHOT_RATIFIED`**

Las opciones eran A `COMMON_TONE_DEVELOPMENT_SNAPSHOT_RATIFIED`, B `HUMAN_REVIEW_RECORD_MISMATCH`, C `PULMONARY_EDEMA_REJECT_IMPLIES_MECHANISM_FAILURE`, D `SNAPSHOT_BINDING_MISMATCH`, E `RATIFICATION_REQUIRES_PHYSIOLOGY_CHANGE`. Resultó **A**: los totales reportados son la tabulación de los juicios y las respuestas son opciones válidas de las preguntas reales (no B; el registro queda marcado `REPORTED_NOT_STORE_VERIFIED`); el juicio humano registrado dice que el `REJECT` es de contexto de manejo (no C); la ligadura es igual en el núcleo, en las sondas y en el candidato de FR-F (no D); ningún paso toca la fisiología (no E).

## 10 · Lo que queda abierto a decisión docente

1. Si y cuándo autorizar la semántica de titulación y suspensión (FD-TONE-RATIFY-08), cuyo primer paso es una auditoría.
2. Si la limitación de dependencia de la bomba exige trabajo antes de cualquier uso educativo de un vasopresor en una familia limitada por la bomba.
3. Si el edema pulmonar hipertenso se convierte en un escenario de manejo de control negativo.
4. Si se aporta el almacén persistido de esta revisión para **verificar** el registro humano (hoy reportado, no verificado).
5. Si alguna vez se quiere la revisión opcional de sensibilidad LOW/HIGH (FD-TONE-RATIFY-09).
6. Vincular la instantánea a algo ejecutable (por ejemplo, que el mapeo de desarrollo la lea) es un paso ejecutable aparte que exige autorización y recertificación.
