# B-5 · Mapa de preparación para la implementación

> **Ejecutado en local el 2026-10-08** con la autorización «FINAL FACULTY DECISIONS + LOCAL IMPLEMENTATION
> AUTHORIZATION»: IG-0 a IG-7 en este orden, con commits locales y sin push. El estado de cada grupo, el SHA del
> candidato local y lo que quedó detenido para decisión docente están en `docs/revision/B5_CANDIDATO_LOCAL.md` y en
> `docs/revision/B5_IG5_PENDIENTES_DOCENTES.md`. Lo que sigue es el plan tal como se escribió antes de ejecutarlo.

> **Documento de planificación. Nada implementado.** Sesión autónoma del 2026-10-08, rama `clinical-encounter-v0.13`.
> Prepara la ronda de implementación para que corra en **una sola pasada controlada** cuando la docencia apruebe los 9
> relatos pendientes, decida TD-84 y TD-85 y autorice implementar. No cambia código, `case_text/es`,
> `rubric_text/es`, el corpus ni las pruebas.
>
> **Base del runtime:** `8ff41a45a6ce60dfc652149b2ef774424304e49a` (B-1). Desde ese commit sólo cambió `docs/`:
> `git diff 8ff41a4 -- . ':(exclude)docs'` sale vacío (verificado el 2026-10-08). Cada línea de código citada aquí vale
> para ese runtime.
>
> **Etiquetas de evidencia:** VERIFICADO EN EL CÓDIGO (lectura del archivo y la línea) · VERIFICADO CON EL MOTOR (sonda
> de sólo lectura que ejecuta el código) · VERIFICADO POR SCRIPT (cálculo determinista) · APROBADO POR LA DOCENCIA ·
> PROPUESTO · SUPUESTO / POR DEFINIR.

## 0. En una mirada

- **Decidido y sin implementar:** 21 ítems de implementación (§1), agrupados en 8 grupos atómicos (IG-0 a IG-7, §6).
- **Propuesto, a decisión docente:** 2 ítems nuevos de esta sesión (§3):
  - **TD-84:** el examen neurológico inglés de los opioides pierde «small reactive pupils»;
  - **TD-85:** dos frases del motor llegan en inglés a la sala en español, sin borrador ni inventario: el paro de la
    bradicardia y la reacción bifásica de la anafilaxia.
- **Activación del relato y de la rúbrica:** el mecanismo existe y es seguro por versión (§4 y §5). Las 30 versiones
  objetivo del relato y las 5 de la rúbrica se reproducen hoy desde el repositorio más los cambios decididos (VERIFICADO
  POR SCRIPT). Faltan la herramienta de exportación, 6 pruebas y los dos `approvals.json`, que se generan sólo con
  los 30 casos aprobados.
- **Reglas duras de la implementación:**
  - el lector queda congelado: `family_parser.py`, `shared_order_language.py`, `shared_order_quantities.py`,
    `active_order_context.py` y `weight_based_doses.py` son idénticos a V3 (`3d942ee`; VERIFICADO POR SCRIPT) y
    deben seguir así. Todo el español de los mensajes que nacen en el lector va por `language.py`;
  - no se tocan el corpus ni los baselines;
  - cada hash aprobado debe reproducirse exacto; si no, se detiene y vuelve a la docencia.
- **Secuencia recomendada (§7):** IG-0 (instrumentos) → IG-1 y IG-2 (datos del relato y de la rúbrica) → IG-3 (eventos
  y frases de paro) → IG-4 (hallazgos del examen) → IG-5 (capa de presentación en español, X-1) → IG-6 (documentos) →
  IG-7 (congelamiento) → recertificación final una sola vez (§9).

## 1. Inventario de todo lo decidido que falta implementar antes del candidato final

| N.º | Ítem | Decisión docente | TD | Estado |
|---|---|---|---|---|
| 1 | A-2: examen del edema pulmonar durante el agotamiento | REVISE, 2026-10-07 | TD-51 | APROBADO; sin implementar |
| 2 | A-6 + A-6a, A-6b, A-7-49m, A-8a: examen del asma grave de la 49m según el estado del motor | A-6 REVISE; las otras cuatro APPROVE, 2026-10-07 | TD-83 | APROBADO; sin implementar |
| 3 | A-9 (inglés) y «{n}/min» en A-9, A-10 y A-11 | A-9 REVISE; A-10 y A-11 APPROVE con nota cosmética | TD-52 (a) | APROBADO; sin implementar |
| 4 | D-42: el límite de evaluación del POCUS en la neumonía, en la guía docente | REVISE (sólo documentación) | TD-54 | APROBADO; sin implementar |
| 5 | K-18: la frase del paro de la anafilaxia tras una dosis | REVISE | TD-82 | APROBADO; sin implementar |
| 6 | K-E5: la etiqueta del paro de la anafilaxia | REVISE | TD-82 | APROBADO; sin implementar |
| 7 | K-E6: la etiqueta del paro de la bradicardia | REVISE | TD-67 | APROBADO; sin implementar |
| 8 | K-E16: «84 %» → «84%» (cosmético) | APPROVE con nota cosmética | TD-67 | APROBADO; sin implementar |
| 9 | J: la nota de la foto fija en español | APPROVE (redacción docente) | — | APROBADO; sin implementar |
| 10 | K-5, K-6, K-13, K-14: el fármaco en español en los recibos y en la tarjeta (regla X1-0) | APPROVE con la regla X1-0 | TD-80 | APROBADO; sin implementar |
| 11 | X-1: la capa de presentación en español (100 formulaciones; I-1 a I-11; V-1 a V-7) | 105 de 105, XR-01 a XR-28 | TD-79, TD-80 | APROBADO; sin implementar |
| 12 | V-9: los nombres de fármacos en español en los 6 puntos donde se muestran | XR-06 | TD-80 | APROBADO; sin implementar |
| 13 | Limpieza de claves internas a la vista (TD-80 a) | XR-05 (b), L-17, L-18, X1-C27e, X1-C28 | TD-80 | APROBADO; sin implementar |
| 14 | Activación de los 18 borradores del motor (`spanish_drafts.ENGINE`, A-1 a A-18) | S-B: «mostrarlo es activarlo (X-1)» | TD-79 | APROBADO; sin implementar |
| 15 | XR-18: la aclaración del carbohidrato oral, con su entrada en el registro de correcciones | XR-18 REVISE | — | APROBADO; sin implementar |
| 16 | Relato: T-1 (7 pasajes), T-2 (2), T-3 (1) y P-1 (1): 11 pasajes en 10 casos | Lote 0, R1–R4A, 2026-10-07/08 | TD-81 | APROBADO (21 de 30); 9 casos pendientes de decisión |
| 17 | Rúbrica: D4 con R-1 (3 cadenas) y D5 (b) (1 cadena) | RUB, 2026-10-07 | TD-81 | APROBADO; sin implementar |
| 18 | `case_text/es/approvals.json` (30 filas) y `rubric_text/es/approvals.json` (5 filas), con sus pruebas | Camino (a), 2026-10-07 | TD-81 | APROBADO; se genera con los 30 aprobados |
| 19 | Centinela del español (prueba nueva) | X-1, §10 | TD-79 | APROBADO como requisito; sin construir |
| 20 | Guías H-62 e I-63: actualizar al comportamiento final y firmar | DEFER hasta el candidato implementado | — | Pendiente a propósito |
| 21 | Documentos que siguen a lo anterior: `F0_11_FRASES_ES.md` (filas de K-18, K-E5, K-E6), `GUIA_DOCENTE_PILOTO.md` (D-42; TD-51), `RUNBOOK_PILOTO.md` (desactualizado frente a §16) y la línea de la rama de desarrollo (§15 de readiness) | Consecuencia de 1–20 | — | Sin hacer |

Propuestos en esta sesión, **no** se implementan sin decisión docente: **TD-84** y **TD-85** (§3).

## 2. Mapa decisión → código

Todo de sólo lectura sobre el runtime `8ff41a4`: VERIFICADO EN EL CÓDIGO, salvo donde dice otra cosa.

| Decisión | TD | Archivos | Función / estructura | Comportamiento actual | Objetivo aprobado | Tipo de cambio | Pruebas que existen | Pruebas a agregar o actualizar | Capa compartida |
|---|---|---|---|---|---|---|---|---|---|
| A-2 | TD-51 | `family_engine.py`, `work_of_breathing.py`, `spanish_drafts.py`, `language.py` | `current_findings`, rama del edema pulmonar (`family_engine.py:3236–3237`); criterio `work_of_breathing.exhausted()` (`work_of_breathing.py:54–55`) | Con `lung ≥ 0.7` dice «Bilateral inspiratory crackles with increased respiratory effort.», también cuando el esfuerzo ya es «Exhausted»; en español sale en inglés | EN «Bilateral inspiratory crackles; respiratory effort is now shallow and ineffective, consistent with exhaustion.» · ES «Crépitos inspiratorios bilaterales; el esfuerzo respiratorio ahora es superficial e ineficaz, compatible con agotamiento.», sólo con el criterio de agotamiento | ENGINE FINDING + DISPLAY LANGUAGE | `test_td47_and_r4_engine_findings.py:65–97` (A-3 nunca junto al agotamiento) | Prueba hermana para A-2 (con agotamiento → A-2 nueva; sin → la actual); borrador de A-2 en `spanish_drafts.ENGINE` | La misma línea produce A-3 |
| A-6, A-6a, A-6b, A-7-49m, A-8a | TD-83 | `family_engine.py`, `language.py`, `spanish_drafts.py` | Rama del asma de `current_findings` (`family_engine.py:3227–3235`); índice de obstrucción `:3228`; `_airway_relaxation` `:2329–2334` | Desde la primera orden, la 49m muestra A-6 aunque la obstrucción no haya bajado; A-7 dice «wheeze on the other side» | La 49m conserva su gravedad por estado: A-6a al respirar sola (y con VNI), A-6b intubada, A-7-49m con neumotórax a tensión, A-8a tras descomprimir, mientras el índice no baje de su valor de llegada; A-5, A-6 y A-8 rigen con mejoría real (redacción: paquete, bloque A) | ENGINE FINDING | `test_family_engine.py:110–118`; `test_asthma_complications.py:46–52`; `test_examination_orders.py:70–74` | Pruebas por estado de la 49m: oxígeno solo → A-6a; etomidato y rocuronio → A-6b; ketamina → A-6; neumotórax → A-7-49m; descomprimido → A-8a; broncodilatador → A-5 y A-8. Español de A-6b, A-7-49m y A-8a (A-6a sale por el relato aprobado) | Las 8 frases del asma salen del mismo bloque |
| A-9 (+ A-10, A-11 cosmético) | TD-52 (a) | `family_engine.py`, `spanish_drafts.py` | f-string de la rama de opioides (`family_engine.py:3247`) | «Respiratory rate {n} /min; assisted ventilation is in progress.» | EN «Respiratory rate {n}/min, provided by the assisted ventilation currently in progress.»; ES como el borrador; «{n}/min» en las tres | TEXT ONLY | Ninguna fija el texto; `test_spanish_drafts.py:58` exige plantilla = inglés | Prueba de las tres frases en EN y ES; actualizar las filas 9–11 de `spanish_drafts.ENGINE` | A-9, A-10 y A-11 comparten la línea; TD-84 está 30 líneas antes |
| D-42 | TD-54 | `docs/GUIA_DOCENTE_PILOTO.md` | Párrafo de las líneas 156–159 | La guía junta trauma y neumonía en un párrafo con otra redacción | La redacción docente del paquete (fila D-42) para la parte de la neumonía; la frase del trauma queda | DOCUMENTATION | — | — | El texto inglés de `case_assessment_bank.py:1797–1802` no cambia |
| K-18 | TD-82 | `anaphylaxis_reaction.py`, `language.py` | `ARREST_AFTER_DOSE_TEXT` (`anaphylaxis_reaction.py:145–151`); regla en `_PHASE0_RULES` (`language.py:467–470`) | «…the adrenaline given earlier had worn off and the reaction had come back…» | EN «…the adrenaline given earlier did not keep the reaction under control…» · ES «…la adrenalina administrada antes no logró mantener la reacción bajo control…» | TEXT ONLY | `test_phase0_spanish.py:124–127` (fija el español actual); `test_phase0_acceptance_findings.py:235–244` | Actualizar las dos; renombrar la prueba «…wore_off_says_so» | Junto a K-21; aparece en la misma entrada que K-E5 |
| K-E5 | TD-82 | `event_provenance.py`, `language.py` | `FLAG_EVENTS["arrested"]["label"]` (`event_provenance.py:67–72`); regla `language.py:429` | «circulatory arrest from untreated anaphylaxis», también tras una dosis | EN «circulatory arrest from anaphylaxis without effective adrenaline» · ES «paro circulatorio por anafilaxia sin adrenalina eficaz» | ENGINE EVENT LABEL | Ninguna fija la etiqueta; `test_phase0_observation_and_provenance.py:72` sólo exige que no diga «resuscitation» | Prueba de la etiqueta EN/ES con y sin adrenalina dada | Misma tabla y mismo bloque de reglas que K-E6 |
| K-E6 | TD-67 | `event_provenance.py`, `language.py` | `FLAG_EVENTS["bradycardia_arrest"]["label"]` (`:73–78`); regla `language.py:430` | «loss of circulation from the falling rate» | EN «circulatory arrest from profound bradycardia» · ES «paro circulatorio por bradicardia profunda» | ENGINE EVENT LABEL | Ninguna | Prueba de la etiqueta EN/ES | Igual que K-E5; TD-85 (a) es la frase de procedimiento del mismo paro |
| K-E16 | TD-67 | `event_provenance.py`, `language.py` | `event_provenance.py:298` («saturation {spo2} % and falling»); regla `language.py:440` | «84 %» | «84%» | TEXT ONLY | — | La regla española debe aceptar la forma nueva | Igual que K-E5 |
| J | — | `clinical_scene.py` | `STILL_VIEW_NOTE` (`clinical_scene.py:207–208`) | Sólo inglés | ES «Una fotografía fija no muestra todos los signos clínicos; examina al paciente para evaluar lo que no puede mostrar.» | DISPLAY LANGUAGE | `test_scene_correction.py:122,125`; `test_the_room_shows_the_bank.py:409,416` | Prueba de la nota en ES | Catálogo de pantalla de X-1 |
| K-5, K-6, K-13, K-14 | TD-80 | `time_semantics.py`, `order_pipeline.py`, `app.py`, `language.py` | Etiquetas del motor llevadas a la tarjeta y al recibo (`time_semantics.py:263–295`; `order_pipeline.held_message` `:364–383`; reglas `language.py:397–403`) | El fármaco sale en inglés dentro del español | El fármaco con V-9 | DISPLAY LANGUAGE | `test_phase0_spanish.py:94–107` fija «aspirin» y «norepinephrine» en español | Actualizar a V-9 | V-9 (fila 12) |
| X-1 (100 formulaciones) | TD-79, TD-80 | `app.py` (55 ítems), `family_engine.py` (25), `family_parser.py` (9, **sólo su español, por `language.py`**), `resuscitation_room.py` (8), `clinical_scene.py` (2), `family_reports.py` (2), `reasoning_questions.py`, `account_portal.py`, `ecg12.py`, `clinical_physiology.py` (1 cada uno); I-1 a I-11 (9 en `app.py`, 1 en `language.py`, 1 en `resuscitation_room.py`) | Fuentes con línea en `docs/revision/X1_ESPANOL_PROPUESTO.md` (§4–§8): las 67 referencias `APP:` y las 69 `FE:`/`FP:` coinciden hoy con su texto (0 desajustes) | Español ausente o mezclado en esas pantallas | El español aprobado (105 de 105; XR-01 a XR-28) | DISPLAY LANGUAGE (TEXT ONLY en las REVISE de XR) | `test_room_labels_in_spanish.py`, `test_screens_speak_the_readers_language.py`, `test_document_language.py`, `test_presentation_language.py`, `test_orders_read_the_same_in_both_languages.py` | Centinela (fila 19); actualizar `regression_v06030_diagnostic_information_layer.py:13` y `regression_v089_reasoning_gate_action_transparency.py:19` (fijan literales que cambian) | `language.py` (sala), `report_language.py` + `screen_language.py` (pantallas y documentos), `history_topics.py` |
| V-9 | TD-80 | `report_presentation.py`, `app.py`, `family_reports.py`, `resuscitation_room.py`, `time_semantics.py`, `order_pipeline.py`, `portfolio.py` | Seis puntos de presentación: etiquetas del motor en la tarjeta y el recibo; vista de órdenes y documentos (`report_presentation.action_phrase`, `:235`; el agente en `:329–345` y `:355–365`); panel de tratamientos (`app.py:10400–10456`; `family_reports.format_administration` `:91–106`); línea de soporte (`resuscitation_room.device_labels` `:6–19`); preguntas de aclaración (`family_engine.py:472, 568, 640–656, 767`); documentos en español (`app.py:3985–4013`; `portfolio.py:210`) | Nombres canónicos en inglés; sólo los trombolíticos tienen tabla (`language._THROMBOLYTICS_ES`, `language.py:1263–1269`) | La tabla V-9 (X-1 §12.2), sólo para mostrar; el identificador guardado no cambia | DISPLAY LANGUAGE | `test_room_labels_in_spanish.py:71–76` y `test_document_language.py:335–336` esperan el fármaco en inglés | Actualizar esas dos a V-9; prueba de que el identificador canónico guardado no cambia | Una función de presentación aplicada en los 6 puntos; lee `family_parser._AGENTS` sin modificarlo |
| Limpieza de claves | TD-80 (a) | `family_engine.py`, `app.py` | `{kind}` en las preguntas (`family_engine.py:640, 645, 654, 656, 767, 472`), `{agent or kind}` (`:568`), `({kind})` (`:855`), `{key!r}` y la lista de estudios (`:611–612`); `render_event` y la evolución (`app.py:10118`, `:10753`) con «ORDER_CANCELLED» y «DIAGNOSTIC» fuera de `_EVENT_LABELS` | Claves internas a la vista | Columna inglesa de presentación de X-1; «ORDER CANCELLED» / «ORDEN CANCELADA»; «ECG» | DISPLAY LANGUAGE | `test_encounter_screen.py:249–345` (fija el tipo de cada evento, no su etiqueta) | Prueba de que ninguna clave cruda llega a la pantalla | Capa X-1 |
| Borradores del motor (18) | TD-79 | `spanish_drafts.py`, `language.py`, `test_spanish_drafts.py` | `spanish_drafts.ENGINE` (filas 1–18), hoy prohibido en el runtime (`test_spanish_drafts.py:31–34`) | Las frases A-1 a A-11 salen en inglés en la sala en español; A-12 a A-18, en inglés en el panel del examen | Activos (S-B) | DISPLAY LANGUAGE | `test_spanish_drafts.py:31–34, 49–59, 62–67`; `test_review_sheets_are_current.py` | Cambiar el contrato de `test_spanish_drafts.py` (de borrador a activo); regenerar `ES_BORRADORES.md` y `R4_FRASES_MOTOR.md` | Capa X-1; depende de IG-4 (el inglés final de A-2, A-6, A-9) |
| XR-18 | — | `family_engine.py`, `corrections_registry.py` | `family_engine.py:769–772` (carbohidrato oral; estados seguros en `glucose_rescue.ORAL_SAFE_MENTAL`) | EN «…until the airway is protected.»; ES mezclado | EN «…until oral administration is safe.» · ES «…hasta que sea seguro administrar por vía oral.» (V-5 para el estado) | TEXT ONLY | `test_hypoglycemia_preservation.py:47–53, 70–80` | Una entrada nueva en `corrections_registry.CORRECTIONS` con `"preservation": {"variants": [los 3 de hipoglicemia], "scripts": ["oral_while_not_alert"]}`; no regenerar el archivo dorado | — |
| Relato T-1/T-2/T-3/P-1 | TD-81 | `case_text/es/acs.json`, `pneumonia.json`, `pulmonary_edema.json`, `asthma.json`, `hypoglycemia.json` | 11 pasajes en 10 casos (`docs/revision/B5_RELATO_INTEGRIDAD_30.md`) | Texto anterior | Las versiones objetivo aprobadas | TEXT ONLY (datos) | `test_case_text.py` (48, 55, 88, 119, 148) | §4.5 | — |
| Rúbrica D4/D5 | TD-81 | `rubric_text/es/descriptors.json` | D4: «qué evalúa», nivel 0 y nivel 2; D5: nivel 3 | Borrador anterior (`8591b254…`, `a87a1655…`) | `041597d9…` y `52958f1c…` | TEXT ONLY (datos) | `test_rubric_text.py` | §5.4 | — |
| Aprobaciones | TD-81 | `case_text/es/approvals.json`, `rubric_text/es/approvals.json` (nuevos) | `case_text.pack_approvals`/`status` (`case_text.py:149–166`); `rubric_text.pack_approvals`/`status` (`rubric_text.py:125–142`) | No existen; con base vacía todo queda en inglés | 30 filas `{variant_id, version, decision}` y 5 `{domain_id, version, decision}` | APPROVAL ACTIVATION | `test_case_text.py:148`; `test_rubric_text.py:140, 151` | §4.5 y §5.4 | — |
| Centinela del español | TD-79 | Prueba nueva | Recorre los 30 casos en español con una batería de órdenes que dispare cada pregunta y falla ante cualquier línea visible con inglés fuera de los nombres canónicos y los códigos (X-1 §10) | No existe | Con las aprobaciones del candidato, cero inglés no declarado | TEST HARNESS | Lo más cercano: `test_phase0_spanish.py`, `tools_engine_spanish.residue` | La prueba entera (§9 A-3) | Debe incluir el paro de la bradicardia y la reacción bifásica (TD-85) |

**Capas compartidas, comprobadas en el código:**
- `current_findings` (`family_engine.py:3197–3255`): A-2, A-3, A-5 a A-11, A-6a, A-6b, A-7-49m, A-8a y TD-84 → un
  solo grupo (IG-4).
- `event_provenance.FLAG_EVENTS` y el bloque de reglas de eventos de `language.py` (`:424–441`): K-E5, K-E6, K-E16 →
  un grupo con K-18 (IG-3).
- La capa de presentación (`language.py`, `report_language.py`, `screen_language.py`, `app.py`): X-1, V-9, claves,
  borradores, J, K-5/6/13/14 → un grupo (IG-5).

## 3. Propuestas nuevas de esta sesión (requieren decisión docente; no se implementan sin ella)

### TD-84 · El examen neurológico inglés de los opioides pierde la miosis

- **Qué:** la sala no muestra el pasaje neurológico del relato. El motor compone «Current mental status: …» y le
  agrega las pupilas y la lateralización que extrae del relato **en inglés** con expresiones regulares
  (`family_engine.py:3210–3218`). La de las pupilas, `\bpupils?[^.!?;]*`, empieza en la palabra «pupils» y pierde
  los adjetivos que la preceden. El español (`language._neurological_tail`, `language.py:1379–1398`) toma la frase
  entera de la traducción aprobada.
- **VERIFICADO CON EL MOTOR** (sonda de sólo lectura, examen de llegada de los 30 casos, relato instalado):
  - `opioid_35m`: EN «pupils and brief bilateral withdrawal to firm stimulation»; ES «Pupilas pequeñas y reactivas, y
    retiro bilateral breve ante un estímulo firme.».
  - `opioid_67f`: EN «pupils, briefly withdrawing both arms to a firm stimulus.»; ES «Pupilas pequeñas y reactivas,
    retira brevemente ambos brazos ante un estímulo firme.».
  - Menor: `bradycardia_ccb_68m`, EN «moving all limbs» (omite «no focal deficit»); ES «Moviliza todas las
    extremidades. Sin déficit focal.».
  - Los otros 27 casos: sin diferencia.
- **Impacto:** en inglés, la miosis (la pista del toxíndrome opioide) no aparece en el examen de la sala; en español
  sí. Los dos idiomas dicen cosas distintas sobre el mismo hallazgo.
- **Propuesta (para decidir):** capturar la cláusula entera que nombra las pupilas (desde el signo de puntuación
  anterior), de modo que el inglés diga «with small reactive pupils and brief bilateral withdrawal…» y quede a la par
  del español; prueba EN/ES de paridad en los 30 casos. Cambio del motor (ENGINE FINDING), dentro de IG-4.
- **Clasificación propuesta:** bloquea el GO del piloto bilingüe (validez de la evaluación en inglés). Decisión
  docente.

### TD-85 · Dos frases del motor llegan en inglés a la sala en español

- **VERIFICADO CON EL MOTOR:** `language.say(texto, "es")` las devuelve sin cambio. Ninguna está en `spanish_drafts`,
  en el inventario de X-1, en R-4 ni en F0-11, y ningún documento las nombra (búsqueda en `docs/`: 0).
- **(a) Paro de la bradicardia** (`bradycardia_toxicology.ARREST_TEXT`, `bradycardia_toxicology.py:145–148`; entra a
  la sala como procedimiento, `family_engine.py:2617–2621`; los 4 casos de bradicardia):
  - EN: «The rate has fallen away and the circulation with it. Nothing given so far reached the cause, and the rate
    was the only thing holding the output up.»
  - **ES propuesto:** «La frecuencia se desplomó y, con ella, la circulación. Nada de lo administrado hasta ahora
    actuó sobre la causa, y la frecuencia era lo único que sostenía el gasto cardíaco.»
- **(b) Reacción bifásica de la anafilaxia** (`anaphylaxis_reaction.BIPHASIC_TEXT`, `anaphylaxis_reaction.py:133–137`;
  entra como procedimiento, `family_engine.py:2187–2190`; sólo `anaphylaxis_29f`, el único caso con `"biphasic":
  True`, `clinical_cases.py:1081`, y es del corpus):
  - EN: «The reaction returns: the wheeze and the flushing are back and the pressure is falling again, more than an
    hour after it first settled. The adrenaline that treated the first reaction has long since worn off.»
  - **ES propuesto:** «La reacción vuelve: reaparecen las sibilancias y el enrojecimiento, y la presión vuelve a caer,
    más de una hora después de que se controló por primera vez. La adrenalina que trató la primera reacción perdió su
    efecto hace rato.»
- **Cambio:** sólo dos reglas en `language.py` (DISPLAY LANGUAGE), dentro de IG-3; el inglés no cambia.
- **Lo que muestra sobre el inventario:** el inventario de X-1 no era exhaustivo. Un barrido de las constantes de
  texto de 17 módulos del motor halló sólo estas dos sin español y sin documento. Las demás candidatas tienen
  documento o se traducen por otra vía. El barrido no cubre el texto compuesto en el momento: por eso el centinela
  (§9 A-3) es obligatorio, no opcional.
- **Clasificación propuesta:** bloquea el GO del piloto bilingüe (inglés en la sala española). Decisión docente
  sobre la redacción.

### Otras diferencias halladas (no clínicas; las decide el responsable técnico, no la docencia)

- **El preflight acepta una clave del proveedor presente pero retenida** (`tools_pilot_preflight.py:217–218`); §16.11
  exige que no esté. El runbook la agrega como comprobación manual (sin cambio de código).
- **`docs/RUNBOOK_PILOTO.md` está desactualizado frente a §16:** rama, prueba del paso 0 y `MRS_FREE_GENERATION`.
  Lo reemplaza `docs/revision/PILOT_PROMOTION_DEPLOYMENT_RUNBOOK.md`; se actualiza o se marca como superado en IG-6.
- **La rama de desarrollo después del piloto:** readiness §15 dice que la Fase 1 va en `clinical-encounter-v0.13`;
  esta sesión propone `phase-1-contracts-v2`. Es una contradicción que la docencia o el responsable debe decidir; ver
  `docs/revision/PHASE_1_KICKOFF_PACKAGE.md`, §1.
- **`F0_11_FRASES_ES.md` no lo comprueba ninguna prueba,** aunque el paquete (línea 803) dice que sí: sus filas de
  K-18, K-E5 y K-E6 se editan a mano en IG-6.

## 4. Activación de las aprobaciones del relato

### 4.1 Cómo funciona hoy (VERIFICADO EN EL CÓDIGO)

- **Esquema que se lee:** `case_text/es/approvals.json`, una lista de objetos. `pack_approvals` (`case_text.py:149–155`)
  descarta todo lo que no sea un objeto con `decision == "approved"`. `status` usa sólo `variant_id` y `version`.
  El archivo hoy no existe.
- **Versión:** `case_text.version(rows)` (`case_text.py:73–77`) es el sha256 de `json.dumps(sorted((ruta, en, es)))`
  de todos los pasajes del caso. El `variant_id` no entra en el hash.
- **Estado de un caso** (`status`, `case_text.py:158–166`):
  1. una revisión en la base a la versión actual → manda esa revisión (también `changes_requested`);
  2. si no, una fila del paquete con el mismo `variant_id` y la misma versión → `approved`;
  3. si no → `outdated` (había una aprobación vieja en la base) o `pending`.
- **Activación:** `approved_table` (`:169–187`) arma `{inglés: español}` sólo para los casos `approved`, y dentro de
  cada uno sólo con los pasajes cuyo inglés coincide con el de hoy (`usable_rows`, `:87–91`). `install`
  (`:193–207`) lo entrega a `language.set_narrative` cada 120 s como máximo. Lo llama `app.py:10157–10177` en
  cada ejecución; los documentos usan `language.narrating(caso)`.

### 4.2 Respuestas

| Pregunta | Respuesta | Evidencia |
|---|---|---|
| Esquema esperado | `[{"variant_id": …, "version": …, "decision": "approved"}, …]`; otros campos se ignoran | `case_text.py:149–166` |
| Dónde se lee | `case_text.install` → `pack_approvals("es")`, en la sala y en los documentos | `case_text.py:193–207`; `app.py:10157–10177` |
| Cómo se empareja el caso | Por `variant_id` exacto | `case_text.py:164` |
| Cómo se calcula la versión | sha256 del JSON de las tuplas ordenadas (ruta, en, es) | `case_text.py:73–77` |
| `decision = "approved"` | Única que cuenta; las demás filas se descartan al leer | `case_text.py:155` |
| Falta la fila | El caso queda `pending`: entero en inglés | `case_text.py:166` |
| Hash viejo o distinto | No empareja: `pending` (u `outdated`), entero en inglés | `case_text.py:164–166`; `test_case_text.py:88` (desde la base) |
| Decisión distinta de `approved` | Descartada al leer: como si faltara | `case_text.py:155` |
| ¿Puede quedar activo un español cambiado bajo una aprobación vieja? | **No.** Cualquier cambio del español cambia la versión y el caso vuelve al inglés. Lo único que puede activarse a medias es un caso aprobado cuyo **inglés** cambió: ese pasaje cae al inglés y el resto sigue en español (mezcla dentro del caso). Lo impide `test_case_text.py:48`, que falla si un borrador no traduce el inglés de hoy | `case_text.py:87–91, 158–166` |

**Riesgos que la implementación debe cubrir:**
- **Una revisión en la base manda sobre el paquete.** En una base nueva no hay ninguna, pero si alguien registra
  `changes_requested` en la versión aprobada, el caso vuelve al inglés sin que el paquete cambie. Es el sentido seguro;
  queda declarado.
- **Un `approvals.json` mal formado:** la sala lo absorbe (`app.py:10169–10174` captura todo y queda en inglés), pero
  el panel docente (`case_text_portal._render`) sólo captura `AccountError` y fallaría. Lo cubre la prueba de forma
  (§4.5, prueba 6).
- **Filas duplicadas o `variant_id` desconocidos:** se toleran en silencio (`any`). El exportador debe impedirlos.

### 4.3 Flujo de exportación y verificación (diseño; no implementado)

- **Herramienta propuesta:** `tools_case_text_approvals.py`, sin red y sin base.
  - **`--check`:** calcula la versión de cada caso desde `case_text/es` y la compara con las 30 versiones aprobadas.
    Imprime CASO · VERSIÓN · APROBADA · RESULTADO y termina con código 0 sólo si las 30 coinciden.
  - **`--write`:** hace lo mismo y, sólo si todo coincide, escribe `case_text/es/approvals.json`:
    - exactamente 30 filas `{variant_id, version, decision: "approved"}`, en el orden de `pilot_freeze.CASES`;
    - JSON con `ensure_ascii=False`, sangría fija y salto de línea final, para que el archivo sea determinista;
    - sin nombres, revisores ni identificadores de personas.
- **De dónde salen las 30 versiones aprobadas:** de los documentos de lote, transcritas una sola vez en la herramienta
  como una constante. Una prueba las compara con `docs/revision/B5_RELATO_INTEGRIDAD_30.md` (columna «Versión
  objetivo»), para que el documento y el código no diverjan.
- **Se niega a escribir** si: falta un caso de `pilot_freeze.accepted_variants()`; sobra uno (p. ej.
  `trauma_hemothorax_41m`); hay un duplicado; alguna versión no coincide (y nombra el caso: «se detiene y vuelve a la
  docencia»); el inglés de un pasaje no coincide con el de hoy.

### 4.4 Orden en la implementación

1. Aplicar los 11 cambios de texto (T-1, T-2, T-3, P-1) en `case_text/es`.
2. Correr `--check`: 30 de 30 coinciden. Si no, se detiene.
3. Correr `--write`.
4. Correr las pruebas de §4.5 y la de plantillas del corpus (que debe seguir pasando: ningún cambio toca los 18
   pasajes fijos, VERIFICADO POR SCRIPT).

### 4.5 Pruebas a agregar (en `test_case_text.py` o en un archivo nuevo)

1. **Completitud:** con una base vacía, los 30 casos del piloto quedan `approved` sólo por el archivo, y la sala y los
   documentos los muestran en español. Es la prueba de TD-81.
2. **Exactamente 30:** el archivo tiene 30 filas, una por caso del piloto, sin `trauma_hemothorax_41m`.
3. **Hash viejo:** una fila con una versión anterior deja ese caso en inglés.
4. **Duplicados y desconocidos:** el exportador se niega; además, la prueba de forma falla si el archivo los tiene.
5. **Decisión no aprobada:** una fila con `decision` distinta deja el caso en inglés.
6. **Forma:** el archivo es una lista de objetos con exactamente esas tres claves. Un archivo mal formado no tumba el
   panel docente (o la prueba fija el comportamiento declarado).
7. **Coherencia con los documentos:** las 30 versiones de la herramienta coinciden con
   `B5_RELATO_INTEGRIDAD_30.md`.

## 5. Activación de las aprobaciones de la rúbrica

### 5.1 Cómo funciona hoy (VERIFICADO EN EL CÓDIGO)

- **Archivo:** `rubric_text/es/approvals.json` (no existe); `pack_approvals` (`rubric_text.py:125–131`) con el mismo
  filtro `decision == "approved"`.
- **Clave:** `domain_id` (no `domain`). Estado: `status` (`rubric_text.py:134–142`), con la misma precedencia que el
  relato (la base primero).
- **Versión:** `rubric_text.version(domain, rows)` (`:51–55`), sha256 de `[domain] + sorted([clave, en, es])`. El
  dominio sí entra en el hash.
- **Además,** `approved_table` (`:145–154`) exige `current()` (`:58–64`): las mismas claves, el inglés igual al de
  `rubric.DOMAINS` y un español no vacío. Si el inglés de la rúbrica cambia, el dominio vuelve al inglés y la base
  rechaza aprobarlo (`record`, `:100–102`).
- **Quién ve qué:**
  - sólo la docencia ve los descriptores (`rubric_portal.render_rubric_assessment`, puerta `STAFF`). Con un dominio sin
    aprobar, en español aparece la nota «Descriptors a faculty member has not yet approved in Spanish are shown in
    English.» (`rubric_portal.py:125–127`);
  - el residente ve sólo los títulos de los dominios (`title_es`, activos sin aprobación);
  - el puntaje y el criterio de la IA quedan en inglés por diseño (`rubric_analysis.py:81–82`).

### 5.2 Reproducibilidad (VERIFICADO POR SCRIPT, 2026-10-08)

| Dominio | Versión del repositorio hoy | Versión aprobada | Cambios | ¿Se reproduce? |
|---|---|---|---|---|
| D1 | `552618f3085a42ae3d6e13d8be3338a60ce3fb713f1a223eb74825e505fe1369` | la misma | — | sí |
| D2 | `0393ca0dd6717a6a54b649541e7f140c1d0dd822cbf8e98e205f8456df6763c4` | la misma | — | sí |
| D3 | `bf7395c34d28bce676adfc5bad71f5a6d4a1dbdced9952c64dda64f52284a191` | la misma | — | sí |
| D4 | `8591b254c11b5afe993b2a99ad37d83be5765cdf4bb82c06b7d8519ca0d1b764` | `041597d975468e31bdf8d6c1d1ddd35e289b98fa05b5e8d3b9106db0c36e2dad` | R-1: «se comprobaron» → «se revisaron» (qué evalúa); «No comprueba» → «No revisa» (0); «Comprueba» → «Revisa» (2) | sí |
| D5 | `a87a1655f6611fbc3c55ee298447710c8343a3e0f42d2019d27539b99b989137` | `52958f1cdcd83dc9e7f4535c9ae65862f0f4ab829d230ac4bd8eff617abbdac4` | (b): «un seguimiento que explicite» → «un control posterior que explicite» (3) | sí |

### 5.3 Flujo (diseño)

- **Herramienta:** la misma de §4.3 con `--rubric` (o una hermana, `tools_rubric_text_approvals.py`).
  - Escribe 5 filas `{domain_id, version, decision: "approved"}` en el orden D1–D5.
  - Se niega a escribir si falta, sobra o se repite un dominio, si una versión no coincide o si `current()` es falso.
- **Prueba determinista de que el español aprobado está activo:** con una base vacía,
  `rubric_text.descriptors(d, "es")["language"] == "es"` para los 5 dominios, y el texto es el aprobado.

### 5.4 Pruebas a agregar (en `test_rubric_text.py`)

1. Con una base vacía, D1–D5 quedan aprobados sólo por el archivo y el panel los muestra en español, sin la nota de
   «no aprobados».
2. Exactamente 5 filas, una por dominio.
3. Un hash viejo deja ese dominio en inglés.
4. Duplicados y decisiones no aprobadas: rechazados por el exportador e ignorados al leer.
5. La forma del archivo.

## 6. Grafo de dependencias y grupos atómicos

Derivado de las dependencias del código (§2), no de la lista de decisiones:
- `spanish_drafts.ENGINE` exige que la plantilla sea igual al inglés del motor (`test_spanish_drafts.py:58`). Por
  eso el inglés final de A-2, A-6 y sus variantes, y A-9 (IG-4) tiene que estar antes de activar los borradores (IG-5).
- K-18 y K-E5 aparecen en la misma entrada de la sala. Cambiar uno sin el otro deja la entrada contradictoria:
  «untreated» junto a «given earlier».
- La capa de presentación es una sola: activarla por partes deja pantallas mixtas.

| Orden | Grupo | Archivos | Por qué juntos | Pruebas | Condición de parada |
|---|---|---|---|---|---|
| 0 | **IG-0 · Instrumentos** (TEST HARNESS) | Herramientas nuevas: exportador del relato y de la rúbrica (§4.3, §5.3); centinela del español (esqueleto); pruebas de §4.5 y §5.4, marcadas como esperables de fallar hasta IG-1 e IG-2 si hace falta | Medir antes de cambiar; no toca nada que vea el residente | Las herramientas corren sobre los datos de hoy: `--check` informa 21 coincidencias y 9 en espera; el centinela lista hoy sus fallas conocidas | Si una herramienta no reproduce los hashes de §4 y §5 tal como se calcularon el 2026-10-08, se detiene |
| 1 | **IG-1 · Relato** (TEXT ONLY, datos) | `case_text/es/{acs,pneumonia,pulmonary_edema,asthma,hypoglycemia}.json`; `case_text/es/approvals.json` (nuevo) | Los 11 pasajes y sus 30 versiones se aprueban juntos; el archivo sólo vale con las 30 | §4.5; `test_case_text.py`; plantillas del corpus | Una versión distinta de la aprobada → se detiene y vuelve a la docencia. **Requisito previo:** los 30 casos aprobados |
| 2 | **IG-2 · Rúbrica** (TEXT ONLY, datos) | `rubric_text/es/descriptors.json`; `rubric_text/es/approvals.json` (nuevo) | Mismo principio | §5.4; `test_rubric_text.py` | Una versión distinta → se detiene |
| 3 | **IG-3 · Eventos y frases de paro** (ENGINE EVENT LABEL + TEXT ONLY) | `event_provenance.py` (K-E5, K-E6, K-E16); `anaphylaxis_reaction.py` (K-18); `language.py` (sus reglas; TD-85 si se aprueba) | K-18 y K-E5 juntos; K-E5, K-E6 y K-E16 en la misma tabla y el mismo bloque de reglas | Actualizar `test_phase0_spanish.py:124–127` y `test_phase0_acceptance_findings.py:235–244`; nuevas: etiquetas EN/ES, con y sin adrenalina; TD-85 en ES | Las etiquetas en el Trace siguen siendo las de la tabla; `test_phase0_observation_and_provenance.py` en verde |
| 4 | **IG-4 · Hallazgos del examen** (ENGINE FINDING) | `family_engine.py` (`current_findings` `:3197–3255`); `work_of_breathing.py` (sólo lectura del criterio) | A-2, A-6 y sus variantes, A-9 a A-11 y TD-84 están en la misma función; un solo cambio y una sola batería por estado | Las de §2 (A-2, asma por estado, opioides, paridad de pupilas de TD-84); `test_family_engine.py`; batería de aceptación (categoría `observation_consistency`) | Cualquier cambio fuera de los casos y estados decididos (p. ej. la 24f) → se detiene |
| 5 | **IG-5 · Capa de presentación en español** (DISPLAY LANGUAGE) | `language.py`, `report_language.py`, `screen_language.py`, `history_topics.py`, `app.py`, `report_presentation.py`, `family_reports.py`, `resuscitation_room.py`, `clinical_scene.py`, `spanish_drafts.py` (activación), `family_engine.py` (claves crudas, XR-07, XR-18), `corrections_registry.py` (XR-18); **no** `family_parser.py` | X-1 entero, V-9, la limpieza de claves, los 18 borradores (+ los nuevos de IG-4), J y K-5/6/13/14 en una pasada, para no dejar pantallas mixtas | Centinela en verde; actualizar `test_spanish_drafts.py`, `test_phase0_spanish.py:94–107`, `test_room_labels_in_spanish.py:71–76`, `test_document_language.py:335–336`, `test_presentation_language.py:30–35`, las regresiones v06030 y v089; `test_hypoglycemia_preservation.py` con la corrección de XR-18 | `family_parser.py` cambió (`git diff 3d942ee -- family_parser.py` no vacío) → se detiene; el centinela halla inglés no declarado → se corrige dentro de IG-5 o se detiene si exige otra decisión docente |
| 6 | **IG-6 · Documentos** (DOCUMENTATION) | `docs/GUIA_DOCENTE_PILOTO.md` (D-42; TD-51), `docs/revision/F0_11_FRASES_ES.md`, `docs/RUNBOOK_PILOTO.md`, guías H-62 e I-63 (a la firma), readiness §15 (rama) | Describen el comportamiento final | `test_review_sheets_are_current.py` y las pruebas de documentos | — |
| 7 | **IG-7 · Congelamiento** | `corrections_registry.py` (una corrección por cada cambio de comportamiento: A-2, TD-83, A-9, K-18, K-E5, K-E6, TD-84, TD-85, XR-18), `pilot_freeze.py` / `docs/revision/PILOT_FREEZE_MANIFEST.md` (regenerado), `MRS_CODE_VERSION` del candidato | Fija el candidato final | `test_phase0_pilot_freeze.py`; `test_corrections_registry.py`; `test_debt_register_cites_its_corrections.py` | Árbol limpio y SHA exacto; si falla, no hay candidato |

## 7. Secuencia consolidada recomendada

1. **Antes de escribir código:**
   - la docencia aprueba R4B, R5 y R6 (9 casos);
   - decide TD-84 y TD-85;
   - autoriza la ronda de implementación;
   - el responsable decide la rama de la Fase 1 (no bloquea esta ronda).
2. **Ronda única de implementación** en `clinical-encounter-v0.13`, commits locales por grupo y en este orden:
   IG-0 → IG-1 → IG-2 → IG-3 → IG-4 → IG-5 → IG-6 → IG-7.
   - IG-1 e IG-2 pueden ir antes que IG-0 si la docencia ya aprobó los 30 y el exportador está listo.
   - IG-3 e IG-4 van antes de IG-5, porque IG-5 activa borradores que deben coincidir con el inglés final.
3. **Pruebas focalizadas** al cerrar cada grupo: las de su fila. **No** se corre la suite entera entre grupos.
4. **Una sola recertificación final** sobre el SHA del candidato (§9 A): suite completa, 56 regresiones, centinela,
   preflight, B-1 en el proveedor y freeze. Así hay un solo SHA nuevo y una sola recertificación.

## 8. Archivos del runtime y de datos que cambiarán (previstos)

- **Código:** `family_engine.py`, `event_provenance.py`, `anaphylaxis_reaction.py`, `language.py`,
  `report_language.py`, `screen_language.py`, `history_topics.py`, `app.py`, `report_presentation.py`,
  `family_reports.py`, `resuscitation_room.py`, `clinical_scene.py`, `spanish_drafts.py`, `corrections_registry.py`,
  `pilot_freeze.py`; y, sólo si lo exige la redacción de X-1, `portfolio.py`, `reasoning_questions.py`,
  `account_portal.py`, `ecg12.py` y `clinical_physiology.py` (uno o dos ítems cada uno).
- **Datos:** `case_text/es/{acs,pneumonia,pulmonary_edema,asthma,hypoglycemia}.json`,
  `rubric_text/es/descriptors.json`, `case_text/es/approvals.json` (nuevo), `rubric_text/es/approvals.json` (nuevo).
- **Herramientas nuevas:** el exportador (§4.3) y el centinela (prueba).
- **Pruebas:** las listadas en §2 y §6.
- **Documentos:** §6, IG-6.
- **No cambian:**
  - `family_parser.py`, `shared_order_language.py`, `shared_order_quantities.py`, `active_order_context.py` y
    `weight_based_doses.py` (lector V3);
  - el corpus de validación, `validation/`, los baselines y `test_data/hypoglycemia_preservation_2026-09-25.json`;
  - `case_assessment_bank.py` (D-42 es sólo de la guía).

## 9. Matriz de recertificación final

### A. Obligatorio antes de fijar el SHA final

| N.º | Qué | Cómo | Aprueba si |
|---|---|---|---|
| A-1 | Pruebas focalizadas de cada cambio | Las de §2 y §6, por grupo | 0 fallas |
| A-2 | Hashes del relato y de la rúbrica | `tools_case_text_approvals.py --check` (30) y `--rubric --check` (5) | 30 de 30 y 5 de 5 iguales a lo aprobado |
| A-3 | **Centinela del español** | Los 30 casos del piloto en español, con las aprobaciones del candidato. Una batería que dispare: historia, examen (todas las regiones), estudios, tratamientos, aclaraciones, compuerta de razonamiento, espera y reevaluación, interrupción crítica, paro (incluidos el de la bradicardia y la reacción bifásica de la 29f), recibos, panel de tratamientos, línea de soporte y documentos descargables en español | 0 líneas visibles con inglés fuera de las excepciones canónicas declaradas (nombres canónicos guardados, códigos, unidades) |
| A-4 | Lector congelado | `git diff 3d942ee -- family_parser.py shared_order_language.py shared_order_quantities.py active_order_context.py weight_based_doses.py` | Vacío |
| A-5 | Corpus intacto | `test_validation_corpus.py::test_the_committed_blank_templates_are_what_the_generator_writes`; huella de los 18 pasajes (`6d10a034…`, `B5_RELATO_INTEGRIDAD_30.md`) | Pasa; huella igual |
| A-6 | Regresiones | `python3 run_regressions.py` | `PASS: 56/56` |
| A-7 | Suite completa | `python3 .claude/skills/verificar-y-entregar/scripts/suite_particionada.py --salida <dir nuevo fuera del repo>` (Python 3.11, Streamlit 1.64.0) | 0 FAILED; árbol sin cambios antes y después |
| A-8 | Invariantes de la Fase 0 | Dentro de A-7: `test_phase0_order_ledger.py` (ninguna orden se pierde; cada orden con destino y recibo), `test_phase0_submission_guard.py` (idempotencia; escritura previa), `test_phase0_time_and_events.py` (tiempo, espera, interrupción), `test_phase0_observation_and_provenance.py` (paro, procedencia), `test_phase0_guards.py`, `test_phase0_acceptance_battery.py` (31 × 19) y `test_phase0_acceptance_page.py` (31) | Todas en verde |
| A-9 | Preservación de la hipoglicemia | `test_hypoglycemia_preservation.py` con la corrección de XR-18 declarada | Sólo cambia `oral_while_not_alert` en los 3 casos |
| A-10 | Freeze | `python3 tools_pilot_freeze.py --write`; `test_phase0_pilot_freeze.py` | Sin deriva |
| A-11 | Proveedor (B-1 en el SHA final) | Los 4 archivos de B-1 en una corrida limpia sobre el SHA exacto: PostgreSQL 17, endpoint *pooled*, TLS, `TARGET OK` antes y después (procedimiento de readiness §18.6 y §18.10) | 23 passed, 0 skipped |
| A-12 | Preflight | `python3 tools_pilot_preflight.py --secrets <archivo> --commit <SHA> --connect` | «LISTA», 0 FALLA, sin AVISO de `no_batch_settings`; y, a mano, que `OPENAI_API_KEY` no esté |
| A-13 | Base vacía | Base de prueba vacía: arranque del esquema (`check_database.py --create`), primer encuentro, primer envío, recarga y reanudación (`test_phase0_acceptance_page.py` lo cubre con SQLite; en PostgreSQL, A-11) | Pasa |
| A-14 | Árbol limpio y SHA exacto | `git status --short` vacío; SHA de 40 caracteres anotado; `MRS_CODE_VERSION` igual a ese SHA | — |

### B. Obligatorio después del despliegue y antes del GO

El detalle está en `docs/revision/PILOT_PROMOTION_DEPLOYMENT_RUNBOOK.md`, §6E y §6F:
- identidad de la base (`mrs_pilot`) y del código (SHA);
- prueba de humo desplegada;
- fotos (TD-56): `check_database.py --photo-approvals` debe terminar en «All 117 approvals…»;
- inspección visual del español;
- activación del relato y de la rúbrica;
- enlaces a las guías;
- GO explícito.

### C. Opcional o deuda técnica (no bloquea)

- TD-76: respaldo de PostgreSQL 17 sin probar. Se recomienda un simulacro en `mrs_pilot` antes de que entren los
  residentes; queda declarado.
- TD-77: aislamiento de `HOME`.
- TD-78.
- TD-70: G-ANSWER-ORDER.
- TD-65: programador de órdenes.
- TD-62 y TD-64: con la fisiología común, después del piloto.
- Las decisiones abiertas de `trauma_hemothorax_41m` (C-34, D-44, F-59).

## 10. Comprobación interna de este mapa

- **Cada REVISE aparece una sola vez:** A-2 (fila 1), A-6 (2), A-9 (3), D-42 (4), K-18 (5), K-E5 (6) y K-E6 (7). Son
  las 7 del paquete (`FACULTY_SIGNOFF_PACKET_PREPILOT.md:155`).
- **Los estados límite del asma** (A-6a, A-6b, A-7-49m y A-8a) están en la fila 2, con A-6.
- **Las familias de X-1:** formulaciones G, L, M, E, T, P, X1-C, X1-R y A-2; implementación I-1 a I-11; vocabularios
  V-1 a V-7 y V-9; XR-01 a XR-28. Todas en las filas 11–15.
- **Las dependencias del relato y de la rúbrica:** filas 16–18 y §4–§5.
- **Decisiones sin lugar:** ninguna conocida. La única que no pide código son las firmas de H-62 e I-63 (fila 20).
- **Propuestas nuevas:** TD-84 y TD-85, fuera de las 21 y marcadas como pendientes de decisión.
