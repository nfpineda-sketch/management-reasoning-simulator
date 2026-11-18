# Fase 3 · Revisión docente multiescenario de la vía común de tono vascular / norepinefrina (P3-402 a P3-414)

Encargo del 2026-11-18. Rama `phase-3-runtime-integration`; linaje `PHASE2_AMENDMENT_3` (certificado, digesto `867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c`); sin autoridad de norepinefrina; ningún testigo ratificado; la instantánea de presión de GI no cambió; sin despliegue a residentes.
**Esto es capa de revisión (UX y plomería de persistencia). No cambia fisiología, parámetros, trayectorias, autoridad, puntuación ni el primer piloto, y no es una validación clínica.** La revisión humana **no se hizo**: este documento y el entorno la dejan lista.

## 0 · Qué es y para qué sirve

Una revisión docente **simple, intuitiva y clínica** de **cinco** trayectorias de presión (PAS/PAD/PAM) ante **una** orden de norepinefrina (10 mcg/min, iniciada una vez y nunca cambiada), en una sola sesión, con la misma experiencia de la *Faculty Trajectory Review* anterior: una pantalla por escenario, cinco preguntas (Q1 a Q5), comentario opcional, **LOCK FIRST IMPRESSION** (las respuestas quedan inmutables), juicio global con comentario opcional, **SUBMIT & NEXT** y un resumen final.

**No es una calibración fina.** Pregunta si cada trayectoria es direccionalmente plausible, temporalmente plausible, de magnitud defendible y educativamente segura **para desarrollo**. `RECALIBRATE` sólo para un problema material de dirección, tiempo, magnitud, orden de las intervenciones o seguridad educativa. Los cuatro veredictos son `ACCEPT`, `ACCEPT_WITH_LIMITATION`, `RECALIBRATE` y `REJECT`.

Conjunto versionado: **`COMMON_TONE_V1_MULTIFAMILY_FACULTY_REVIEW`** (`docs/revision/PHASE3_COMMON_TONE_V1_MULTIFAMILY_REVIEW_SET.json`, registro histórico versionado, sellado e indexado; su digesto está fijado en el código, `faculty_tone_review.PINNED_SET_DIGEST`). No sobrescribe ninguna revisión anterior: sus registros viven en `tone_review/`, `tone_reviews/` y `tone_sensitivity/`, aparte de los de la primera revisión (`trajectory/`, `trajectory_reviews/`) y de la re-revisión (`trajectory_rereview/`, `trajectory_rereviews/`).

## 1 · P3-402 · Auditoría de fuentes (cada trayectoria es lo ya certificado)

Regla: **ninguna trayectoria se calcula con otro parámetro, ni se afina, ni se sustituye un testigo.** `CENTER_REFERENCE` es el único testigo de la primera pasada, con los valores exactos certificados (`PHASE3_COMMON_TONE_PROBES.json` y `PHASE3_FRF_TONE_V1_CANDIDATE.json`, ambos intactos: sus bytes son los fijados por el índice de registros históricos).

| Escenario | Fuente | Cómo se obtuvo | Prueba de igualdad |
|---|---|---|---|
| **FR-F** (hemorragia digestiva, `gi_bleed_57m`, orden en el minuto 2) | `PHASE3_FRF_TONE_V1_CANDIDATE.json`, `witnesses.CENTER_REFERENCE.per_minute` (minutos 0 a 32) | Tomada **sin recalcular** | La presión mostrada en los cuatro minutos de reevaluación (2, 7, 17, 32) es la guardada en el registro; el primer punto es la llegada autoral |
| **SYNTH** (sonda fisiológica sintética de bajo tono) | `PHASE3_COMMON_TONE_PROBES.json`, `core_probes.distributive` | La misma construcción de `core_distributive` (anclas y carga sintética del núcleo, norepinefrina 10 mcg/min desde el minuto 10, hasta el 40) | La sonda guardada completa se reproduce; la PAM de llegada, antes de la orden, sin soporte y con soporte coinciden con lo guardado |
| **ACS** (`acs_70f_left_main`, orden en el minuto 5) | `…PROBES.json`, `family_probes.acs` | La llamada certificada del arnés (`test_tone_pathway_analysis.shadow_run`: mapeo registrado de la familia más el lector declarado, testigo `CENTER_REFERENCE`, 10 mcg/min en el minuto 5, hasta el 30) | Valores observados, hechos causales y referencia sin mapeo **iguales** a los guardados; reproducción exacta; sin huecos ni fallos; la orden se construye (`BUILT`) |
| **PULM-EDEMA** (`pulmonary_edema_58m`) | `…PROBES.json`, `family_probes.pulmonary_edema` | Ídem | Ídem |
| **PE** (`pulmonary_embolism_61m`) | `…PROBES.json`, `family_probes.pulmonary_embolism` | Ídem | Ídem |

La auditoría completa (huellas de archivo y de registro, banderas de igualdad por escenario) queda **dentro del registro** (`audit.sources`), apartada de lo que ve la persona revisora, y la repite una prueba que **regenera** el contenido con las llamadas certificadas y lo compara con lo guardado (`test_phase3_tone_review_records.py`, c3), con independencia del código que generó la procedencia. Una segunda prueba ata cada escenario al registro certificado **sin pasar por el constructor** (c6 a c8).

Huella del código generador: el núcleo certificado (`867bac09…`), todos los módulos de aplicación **salvo los dos módulos de revisión** (el que carga el conjunto guarda su propio digesto, y un digesto fijado no puede formar parte de lo que fija) y los dos arneses. Un cambio posterior en cualquier módulo de aplicación exige regenerar el registro (todavía no está publicado) y volver a fijar el digesto; después de publicarlo es inmutable (FD-RECORD-01).

## 2 · P3-403 · Conjunto máximo con sentido (REQUIRED / OPTIONAL / EXCLUDED)

| # | Escenario | Estado | Motivo |
|---|---|---|---|
| 1 | FR-F | **REQUIRED, incluido** | Choque hemorrágico con sangrado en curso; la orden se acepta y se reproduce |
| 2 | SYNTH | **REQUIRED, incluido** | Sonda sintética ya certificada; rotulada «SYNTHETIC DEVELOPMENT PHYSIOLOGY PROBE · This is a synthetic development physiology probe, not a clinical case.» |
| 3 | ACS | **REQUIRED, incluido** | Limitado por la bomba (certificado) |
| 4 | PULM-EDEMA | **REQUIRED, incluido** | Congestivo, limitado por la bomba (certificado) |
| 5 | PE | **REQUIRED, incluido** | Obstructivo de bajo flujo: la trayectoria determinista completa se reproduce **exactamente** con la fisiología certificada, sin supuestos nuevos |
| — | opioide (`opioid_35m`) | **EXCLUDED** | La trayectoria certificada exacta se puede generar (igual a la guardada), pero **no tiene sentido clínico** para esta pregunta: el caso autoral es normotenso (llegada 106/64 mmHg) y de fisiología de depresión respiratoria; un vasopresor no tiene indicación y juzgar su respuesta de presión preguntaría por una respuesta que nadie provocaría |
| — | asma (`asthma_49m`) | **EXCLUDED** | Igual: la trayectoria exacta existe, pero el caso es hipertenso (llegada 142/86 mmHg) y de falla respiratoria; sin indicación |

Ninguno se añadió «para subir la cuenta». Orden de pantalla exactamente el de la tabla; no se le dice a la persona revisora que el orden tenga estructura de control positivo o negativo.

## 3 · P3-404 y P3-405 · Identidad y datos

Cada escenario guarda sólo lo que la pantalla dibuja: rótulo, título, contexto clínico **autoral** (la presentación y el diagnóstico del caso), hallazgos de base **autorales** citados literalmente (examen, ecografía, hemoglobina), llegada (PA, SpO₂, FR), la intervención, los puntos por minuto (PAS/PAD/PAM enteros, PAM = (PAS + 2 × PAD)/3) y los minutos de la tabla. **No guarda** FC ni relleno capilar (no se recalcularon para estas trayectorias), ni estado de tono, flujo, entrega o deuda de oxígeno, consciencia, estado de colapso, parámetros, otro testigo, comparador, trayectoria anterior ni juicio anterior. El cargador exige las claves exactas, rechaza cualquier palabra de mecanismo en un campo visible y **nunca lanza excepción**; un conjunto editado, re-firmado, ampliado, reordenado o que filtra es rechazado aunque el digesto recalcule y esté fijado.

## 4 · P3-406 · Pantalla (reutiliza la existente)

`faculty_tone_review_ui.py` reutiliza el gráfico, la tabla de intervenciones, los widgets y los *callbacks* de autoguardado de la *Faculty Trajectory Review*; mismo diseño visual; sin tablero técnico ni archivos que la persona abra. Una pantalla por escenario: rótulo (sólo la sonda lleva el aviso amarillo), título, **What you are judging** (la pregunta específica del escenario, con la redacción del encargo), contexto y hallazgos de base, tabla de la intervención, gráfico PAS/PAD/PAM con el marcador de la orden, tabla de valores en minutos clave, Q1 a Q5, comentario opcional, **LOCK FIRST IMPRESSION**, juicio global, comentario opcional, **SUBMIT & NEXT** (**SUBMIT & FINISH** en el quinto) y avance automático.

Cambios compartidos, mínimos y declarados:

* `faculty_trajectory_review_ui.pressure_chart` ganó dos parámetros opcionales, `y_max` (140 por omisión) y `x_title` (el título anterior por omisión): el edema pulmonar llega a 260 mmHg y el eje fijo en 140 lo habría recortado. Las revisiones anteriores dibujan exactamente lo mismo (prueba t18).
* `faculty_review_ui.launcher` ganó el modo `TONE_MODE` («Norepinephrine review (vascular tone)»), un aviso propio para ese modo (el aviso del entorno habla del alcance de la autoridad viva de GI, que esta revisión no usa) y un **bloqueo propio** (hallazgo 1 de la revisión adversarial): mientras la persona revisora no tenga sus cinco escenarios enviados **y verificados**, el lanzador no ofrece nada más (ni la primera revisión, ni la re-revisión, ni el encuentro en vivo: dibujan trayectorias anteriores, el comparador legado, FC y relleno capilar y juicios anteriores). Falla cerrado; el interruptor del operador `MRS_FACULTY_TONE_GATE=off` lo suelta (para el operador y para las pruebas de los otros modos); el bloqueo de la re-revisión (FD-REREVIEW-21) conserva su precedencia. Sin página de tono entregada, el lanzador es exactamente el anterior.
* `app.py`: dos líneas (importación y entrega de la página); el modo de aterrizaje es ahora el de tono.

Las pantallas de revisión no importan nada de la capa de Fase 3, el motor, el núcleo ni la autoridad (prueba t16).

## 5 · P3-407 · Persistencia

El registro de eventos de la revisión anterior (`ReviewLog`: añadir sólo, encadenado por hash, bajo `flock` y `fsync`) en archivos propios. Autoguardado por *callbacks*; un refresco restaura respuestas, comentario, bloqueo, juicio global y avance; **el bloqueo es irreversible** (una respuesta ciega posterior se ignora al leer y se rechaza al escribir); un segundo envío no crea un segundo registro; un registro forjado o alterado no cuenta y deja el registro ilegible; un bloqueo no fija lo que la pantalla no muestra (dos ventanas de una misma cuenta). Un registro por escenario, con el digesto del conjunto, el del escenario y los de la fuente certificada.

## 6 · P3-408 · Sensibilidad (opcional, después de todos los juicios)

**No** se muestran LOW ni HIGH escenario por escenario. Sólo tras el quinto envío, aparece junto a **Summary** el botón **Sensitivity (optional)**. Por escenario en que la sensibilidad cambia materialmente el cuadro, se dibujan LOW / CENTER / HIGH **en los mismos ejes** (PAM; la tabla da PAS/PAD (PAM) de los tres), **sin valores de parámetros**, con **una** pregunta («Does the sensitivity range remain within a clinically defensible development envelope?», YES / BORDERLINE / NO) y comentario opcional. Autoguardado en su propio registro (`tone_sensitivity/`), sin bloqueo ni envío ni registro: la revisión principal se completa sin él, y no se elige ningún testigo preferido.

Regla de materialidad (**fijada antes de mirar ninguna trayectoria**; `MATERIAL_MAP_SPAN`, `MATERIAL_SBP_SPAN`): se ofrece un escenario sólo si la PAM del último minuto, o la PAS máxima, difiere al menos 10 mmHg (PAM) o 15 mmHg (PAS) entre el ajuste débil y el fuerte; el cargador **recalcula** la regla y rechaza una bandera guardada que no la cumpla. Resultado: los cinco escenarios la cumplen (ninguno se omitió). Las otras posiciones sólo salen del cargador mediante `sensitivity_view`, que lanza `Locked` mientras falte un envío.

## 7 · P3-409 · Resumen final

**REVIEW COMPLETE · 5 / 5**; recuento de `ACCEPT` / `ACCEPT_WITH_LIMITATION` / `RECALIBRATE` / `REJECT`; tabla (escenario, juicio global, Q1 a Q5) apta para captura; comentarios; las respuestas opcionales de sensibilidad si existen; y, **sólo aquí**, **DEVELOPMENT LIMITATIONS TO FOLLOW UP**:

* `COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED` — la revisión de ACS y edema informa si la vía es aceptable **para desarrollo**, no respalda su promoción educativa.
* `CONSCIOUSNESS_UNDER_TONE_UNRESOLVED` — la consciencia bajo soporte de tono no se mostró ni se juzgó.
* `TITRATION_AND_STOP_NOT_SUPPORTED` — sólo se representa un inicio a tasa fija; titulación, cambios de tasa y suspensión no están soportados.

Se guardan en el conjunto, aparte de los escenarios, y también en el resumen técnico de la sesión (`tone_review/session_summary_<ref>.json`).

**Guía de interpretación posterior (sólo guía docente; no es aprobación automática):** si FR-F y la sonda de bajo tono quedan `ACCEPT` / `ACCEPT_WITH_LIMITATION` y ningún escenario requerido queda `REJECT`, la vía puede avanzar; un `RECALIBRATE` en un escenario limitado por la bomba apunta a trabajo **dirigido** en el acoplamiento con la bomba, no a una recalibración global; el mismo problema material de magnitud en varias familias no relacionadas obliga a reconsiderar la región común de tono.

## 8 · P3-410 · Auditoría de ciego

Sobre las pantallas reales (AppTest sobre `app.py` y navegador real) se escanearon texto visible, texto propio de cada elemento (etiquetas, ayudas, opciones, expansores, barra lateral), especificaciones de gráfico, claves de sesión, enlaces y descargas, en **cada etapa de cada escenario**: sin `CENTER_REFERENCE`, sin LOW/HIGH, sin parámetros, sin trayectoria anterior ni juicio anterior, sin comparador legado, sin FC ni relleno capilar, sin estado de tono/flujo/entrega/deuda/consciencia/colapso, sin archivo técnico, y **sin las limitaciones antes del resumen**. Los detectores se prueban a sí mismos (inyectan fugas y exigen que las vean). La primera pasada **no lee** ningún archivo de otro conjunto, de las revisiones anteriores ni de las fuentes certificadas (gancho de auditoría de `open`).

La ruta forzada a la sensibilidad o al resumen antes del quinto envío (clave de sesión) no muestra nada de ellos, y una clave forzada de otro modo no abre nada mientras dura el bloqueo. La sección opcional y las limitaciones esperan registros **verificados** (no sólo el estado de los registros de eventos): un registro faltante, forjado o malformado deja la revisión incompleta, sin pantalla de error.

## 9 · P3-411 · Capturas

Navegador real (Chromium), ventanas de portátil de 1366 × 768 y 1440 × 900: sin desplazamiento horizontal (`scrollWidth == clientWidth`); la persona revisora desplaza la pantalla y obtiene, por escenario, el contexto, el gráfico con su tabla y las preguntas; el resumen cabe en una captura. Los nombres de los escenarios son cortos («GI hemorrhage», «Low-tone probe», «ACS», «Pulm. edema», «Pulm. embolism») para que los botones no se trunquen. No hay botón de exportación: la captura es el medio.

## 10 · Cómo se lanza y qué clics hace la persona revisora

**Operador** (el mismo entorno de un solo proceso de la re-revisión; las mismas variables):

```bash
export MRS_FACULTY_DEVELOPMENT_REVIEW=faculty_development_review MRS_PHASE3_SHADOW=shadow_compare MRS_PHASE3_AUTHORITY=limited_common_authority \
       MRS_PHASE3_AUTHORITY_SNAPSHOT=GI_JOINT_PRESSURE_DEVELOPMENT_SNAPSHOT_V1 MRS_PHASE3_AUTHORITY_ENVIRONMENT=development MRS_OFFLINE_CASES=1 \
       MRS_PHASE3_AUTHORITY_STORE="$HOME/faculty_review/R1/store" MRS_AUTH_MODE=accounts MRS_ALLOW_LOCAL_SQLITE=true \
       MRS_DATABASE_URL="sqlite:///$HOME/faculty_review/R1/accounts/accounts.sqlite3"
streamlit run app.py
```

Si el almacén de esa persona **no** contiene la re-revisión completada, el bloqueo FD-REREVIEW-21 sigue vigente (sin cambios): sólo se ofrece la re-revisión. El operador, que sabe que esa re-revisión ya se hizo, añade `MRS_FACULTY_REREVIEW_GATE=off` (el interruptor del operador de FD-REREVIEW-22); la persona revisora no ve nada de eso.

**Persona revisora:** (1) abre la dirección que imprime Streamlit; (2) inicia sesión con su cuenta docente; (3) **ya está en la revisión** (escenario 1 de 5): no hay nada que elegir ni nada más que abrir hasta el quinto envío; (4) por escenario: Q1 a Q5 → comentario opcional → **LOCK FIRST IMPRESSION** → **Overall judgment** → comentario opcional → **SUBMIT & NEXT** (en el quinto, **SUBMIT & FINISH**); (5) ve **REVIEW COMPLETE · 5 / 5**, el recuento, la tabla y las limitaciones; (6) opcional: **Sensitivity (optional)** → una respuesta por escenario.

## 11 · Revisión adversarial, pruebas y certificación

**Revisión adversarial independiente** (una; de sólo lectura; confirmó cada hallazgo con una sonda antes de reportarlo; ninguna fuga dentro de la propia página de tono):

| # | Sev. | Hallazgo (confirmado) | Disposición |
|---|---|---|---|
| 1 | Alta | Con la revisión a 0/5, la primera revisión, la re-revisión y el modo en vivo seguían seleccionables: dibujan trayectorias anteriores, el comparador legado, FC y relleno capilar y juicios anteriores | **Corregido**: bloqueo propio del lanzador (§ 4) |
| 2 | Media-alta | La sección opcional (LOW/HIGH) se abría con el estado de los registros de eventos, no con registros verificados | **Corregido**: espera `summary.complete` verificado |
| 3 | Media | Un archivo de registro malformado (`[]`, `"x"`, `7`, claves de tipo equivocado) tumbaba la pantalla de resumen con la traza | **Corregido**: es un problema técnico, nunca una excepción |
| 4 | Media-baja | La identidad de los registros no ligaba el digesto del conjunto: otro conjunto reutilizaría respuestas | **Corregido**: el digesto forma parte del nombre del registro |
| 5 | Baja | Un comentario global rechazado se perdía en silencio al enviar | **Corregido**: el envío espera a que lo escrito esté guardado |
| 6 | Baja | `load_set` podía lanzar con una sección malformada de un conjunto re-firmado y fijado | **Corregido** |
| 7 | Baja | El filtro de fugas no cubría las formas de texto de FC, relleno capilar, lactato, estado mental, índice cardiaco, estado de tono | **Corregido** (defensa en profundidad: el digesto fijado es la defensa real) |
| 8 | Baja | `SensitivityLog` escribe antes del quinto envío si se le llama a mano | **Declarado**: sólo la página lo condiciona; no hay ruta desde el navegador |
| 9 | Baja | Con el interruptor del operador de la re-revisión, se aterriza en la revisión de tono, no en la re-revisión pendiente | **Aceptado** (es lo previsto); comentarios del lanzador corregidos |

Cada corrección tiene una prueba que falla sin ella (`test_phase3_tone_review.py` t19 a t22 y `test_phase3_tone_review_page.py` p20 a p24).

**Pruebas focalizadas de este ciclo:** `test_phase3_tone_review.py` (módulo: conjunto, cargador, registros, sensibilidad, resumen, aislamiento), `test_phase3_tone_review_page.py` (página real, AppTest sobre `app.py`) y `test_phase3_tone_review_records.py` (registro, fuentes, igualdad con lo certificado). **Pruebas anteriores adaptadas** (declaradas): `test_phase3_trajectory_rereview.py` r12 y `test_phase3_trajectory_rereview_page.py` p15c, p15e y p15f (el aterrizaje tras liberar el bloqueo es ahora la revisión de tono y los modos son cuatro; lo que protegen sigue protegido), y `test_phase3_faculty_review_page.py` (el fixture abre también el bloqueo de tono para las pruebas de los otros modos).

**Certificación:** ver el § 12 (cifras sobre el candidato congelado).

## 12 · Certificación y punto de control

**Certificación (candidato C1, antes de este registro, estas filas y las cifras):** rama `phase-3-runtime-integration`, base `deb9726`, huella `f5579ea52c10b7e7384c1995b5da86f11bbfe8d6a34e496f337f996d9f215c97` (idéntica al inicio y al final, 0 reanudaciones); **suite completa 13 390 pruebas, 0 fallas, 0 errores, 97 omitidas, 1 xfail**; **regresiones 56/56 activas**, 10 retiradas (las declara el propio ejecutor). Una sola corrida sobre una huella congelada. **Análisis de dependencias:** la suite completa era obligatoria porque varias guardas recorren todos los módulos de la raíz (`ROOT.glob("*.py")`: límites de contrato, linaje de las enmiendas, guardas dormidas, índice de registros) y el cambio añade dos módulos de raíz, toca el lanzador y `app.py` y agrega registros indexados.

**Árbol publicado (C2):** C1 más el registro del punto de control, su entrada del índice (y el digesto fijado en la prueba del índice), las filas de decisión FD-P3-265 a FD-P3-268 y las cifras de este documento. Esas piezas y las pruebas que las leen se corrieron de nuevo sobre el árbol final (cifras en el informe de entrega).

**Punto de control: B · `CORE_SCENARIOS_READY_BUT_OPTIONAL_SCENARIOS_EXCLUDED`** (`docs/revision/PHASE3_COMMON_TONE_V1_MULTIFAMILY_REVIEW_CHECKPOINT.json`). No es A porque los dos escenarios opcionales no forman parte del conjunto (su trayectoria exacta existe, pero un vasopresor no tiene indicación en ellos); no es C, D ni E: la persistencia está certificada, no se encontró fuga de ciego tras las correcciones y cada escenario es igual a su fuente certificada.

## 13 · Limitaciones y decisiones pendientes

1. **La revisión humana no se hizo** y nada aquí la sustituye. Lo que diga la persona revisora son juicios suyos, tabulados; no son una puntuación ni una validación.
2. **Edema pulmonar hipertenso (hallazgo a vigilar, no corregido).** El caso autoral llega con 218/116 mmHg (PAM 150) y, ante la orden, el modelo lo lleva a 260/138 (PAM 179). Un vasopresor **no tiene indicación** en un paciente hipertenso con edema pulmonar cardiogénico: se incluyó porque el encargo lo exige, y se espera que la persona revisora marque el riesgo educativo (Q5) o la magnitud (Q3). Esa respuesta es la evidencia que se busca; no se tocó nada.
3. **FC y relleno capilar no se muestran** (no se recalcularon para estas trayectorias); tampoco consciencia, flujo, entrega ni colapso.
4. **Los bloqueos del lanzador.** Persiste el de la re-revisión (FD-REREVIEW-21): mientras la re-revisión de esa cuenta no esté completa en su almacén, el modo de tono no se ofrece (ver § 10). Y hay uno nuevo, el de esta revisión: hasta el quinto envío verificado no se ofrece nada más. Después reaparecen los cuatro modos y se aterriza en el resumen.
5. **El registro del conjunto no tiene firma**: el sello y el digesto fijado en el código detectan una edición descuidada, no una reescritura coherente de contenido, sello e índice a la vez (el mismo límite que `TD-153` ítem 7). Aceptado para esta revisión de un solo proceso.
6. **Presiones en mmHg enteros**, con el criterio de pantalla de las revisiones anteriores (PAS y PAD redondeadas; PAM = (PAS + 2 × PAD)/3); la PAM sin redondear del modelo difiere hasta ~1 mmHg.
7. **Opioide y asma excluidos** por falta de sentido clínico, no por imposibilidad técnica.
8. **Sin exportación**: la captura de pantalla es el único medio de compartir; el resumen técnico de la sesión se escribe solo y no se muestra.
9. **Sin cambios fuera de lo declarado:** no se tocó el núcleo (`clinical_core/`, digesto fijado), la fisiología de tono, el acoplamiento con la poscarga, la calibración de GI, la sensibilidad a la bomba, el volumen, la entrega, la consciencia, la dosis-respuesta ni el inicio/fin de la norepinefrina; sin parámetro elegido, sin autoridad de norepinefrina ampliada, sin control de fuente, sin autoridad de consciencia ni terminal, sin despliegue a residentes ni validación clínica; `COMMON_CORE_RUNTIME_AUTHORITY = False`.
10. **Pendiente (decisión docente):** el resultado de la revisión humana y, según la guía del § 7, si la vía avanza, si hay trabajo dirigido de acoplamiento con la bomba o si se reconsidera la región común.
