# B-5 · IG-5 · Textos de la sala en español fuera del inventario de X-1 (TD-86)

> **Ronda de implementación local del 2026-10-08.** Las 105 decisiones de X-1 están implementadas en inglés y en
> español (`test_b5_x1_spanish.py`). El centinela del español (`tools_spanish_sentinel.py`, 30 casos) y una cosecha a
> nivel del motor hallaron, además, textos **fuera del inventario de X-1** que la sala muestra en inglés.
> **ES-P1 a ES-P13:** decididos por la docencia el 2026-10-08 e implementados en local (§1 y §2). No queda ningún
> texto de la sala a la espera de redacción docente; ninguno se resolvió como excepción del centinela.

## 1. ES-P1 a ES-P7: decididos por la docencia e implementados en local (2026-10-08)

Decisión «FACULTY DECISIONS — ES-P1 TO ES-P7»; implementados en local (C-2026-10-08-08,
`test_b5_x1_spanish.py`). El inglés, el disparador, el momento y los valores no cambian.

| Ítem | Inglés | Español aprobado | Fuente |
|---|---|---|---|
| ES-P1 | Presentation only. Orders are read in Spanish and English either way. | Sólo cambia la presentación. Las órdenes se leen igual en español y en inglés. | `app.py`, `_language_selector` (catálogo `report_language`) |
| ES-P2 | Ask about {topic} | Preguntar por: {tema en español}, con el nombre que ya da `history_topics.topic_label` (p. ej., «Preguntar por: Motivo de consulta») | `app.py`, `_room_you_words` |
| ES-P3 | Latest response | Última respuesta | `app.py`, `_render_closed_bedside` |
| ES-P4 | Clinical chart · examination · results · treatment record | Ficha clínica · examen · resultados · registro de tratamientos | `app.py`, desplegable tras el cierre |
| ES-P5 | Gastroenterology is at the bedside but defers endoscopy until the patient is resuscitated (hemoglobin {n} g/dL without blood running); they will re-check every 15 minutes. | El equipo de Gastroenterología está a pie de cama, pero difiere la endoscopía hasta lograr una reanimación adecuada (hemoglobina {n} g/dL sin transfusión en curso); reevaluará cada 15 minutos. | `language.py` (frase entera) |
| ES-P6 | heparina 4000 units IV | heparina 4000 unidades IV («unidades», nunca «UI») | `report_presentation._dose_unit`, `family_reports.format_administration`, `language.py` |
| ES-P7 | Hemorrhage control + Blood + … | Control de la hemorragia · Glóbulos rojos | `report_presentation.action_phrase` (`_FALLBACK_NAMES_ES`) |

## 2. ES-P8 a ES-P13: decididos por la docencia e implementados en local (2026-10-08)

Decisión «Faculty now resolves ES-P8 through ES-P13»; implementados en local como frases enteras en `language.py`
(C-2026-10-08-09, `test_b5_x1_spanish.py`). El lector congelado (`active_order_context.py`) no se tocó: su inglés,
sus disparadores y su ejecución son los mismos. `PENDING_OUTSIDE_THE_WALK` queda vacía. La propuesta anterior
de cada ítem está en el historial de git de este archivo.

### ES-P8 · Aclaraciones del lector congelado (`active_order_context.py`, `complete_active_order`)

| # | Inglés exacto (sin cambio) | Español aprobado e implementado |
|---|---|---|
| 8a | No matching administered treatment is recorded. Specify the treatment, dose and route. | No hay registro de un tratamiento administrado que coincida. Indica el tratamiento, la dosis y la vía. |
| 8b | Which previous treatment should be repeated? Specify the drug or fluid. | ¿Qué tratamiento anterior quieres repetir? Indica el fármaco o el fluido. |
| 8c | Specify compatible units for the treatment being repeated. | Indica unidades compatibles con el tratamiento que se repite. |
| 8d | The patient is not receiving invasive ventilation. | El paciente no está con ventilación invasiva. |
| 8e | Specify an airway transition; stopping a ventilator is not an extubation order. | Indica un cambio de la vía aérea; detener el ventilador no es una orden de extubación. |
| 8f | No infusion is running. Name the drug and its starting rate. | No hay ninguna infusión en curso. Indica el fármaco y su velocidad inicial. |
| 8g | More than one infusion is running ({lista}). Name the one to change. | Hay más de una infusión en curso ({lista}). Indica cuál quieres cambiar. |
| 8h | Nitroglycerin is ordered in mcg/min in this encounter. | En este encuentro, la nitroglicerina se indica en mcg/min. |
| 8i | Specify the new {fármaco} rate. | Indica la nueva velocidad de {fármaco}. |
| 8j | No active {fármaco} infusion is recorded. Specify a starting rate and units. | No hay registro de una infusión activa de {fármaco}. Indica la velocidad inicial y sus unidades. |
| 8k | Specify the rate in the new infusion units. | Indica la velocidad en las nuevas unidades de la infusión. |
| 8l | No active conventional oxygen is recorded. Specify the starting device and flow. | No hay registro de oxígeno convencional activo. Indica el dispositivo inicial y el flujo. |
| 8m | Specify the flow for the new oxygen device. | Indica el flujo para el nuevo dispositivo de oxígeno. |
| 8n | No continuous nebulization is running. Specify the rate in mg/h to start it. | No hay nebulización continua en curso. Indica la velocidad en mg/h para iniciarla. |
| 8o | No active NIV is recorded. Specify the starting mode, pressures and FiO2. | No hay registro de VMNI activa. Indica el modo inicial, las presiones y la FiO₂. |

{fármaco} (8i, 8j) sólo puede ser norepinephrine, nitroglycerin o dobutamine, y se dice con su nombre V-9
(noradrenalina, nitroglicerina, dobutamina).

**8g, confirmado por la docencia el 2026-10-08 (APPROVE de la implementación).** La {lista} de 8g no la escribe el
residente: la arma el motor con los nombres ordenados de las infusiones en curso. En la sala en español se dice con
los nombres V-9 ya aprobados («dobutamina, noradrenalina»), igual que {fármaco}; los identificadores canónicos e
internos de los fármacos no cambian. No queda ninguna decisión pendiente sobre 8g.

### ES-P9 a ES-P13

| ID | Fuente (sin cambio) | Español aprobado e implementado | Lo que no cambia |
|---|---|---|---|
| ES-P9 | `family_engine.py:736` (`dose_basis`), unida a la etiqueta en `family_engine.py:1856–1859` | (sin dosis escrita; 1 g es la dosis de carga fija estándar que aplica el simulador) | 1 g, la dosis de carga fija, la ejecución y la trayectoria |
| ES-P10a | `acs_reperfusion.ventricular_fibrillation`, desde `family_engine.py:1721` | Fibrilación ventricular desencadenada por una prueba de esfuerzo con una oclusión inestable. Se pierde el pulso y se suspende la reevaluación organizada: este es el desenlace que esta vía clínica busca prevenir. | Disparador, momento, fisiología del paro, interrupción y procedencia |
| ES-P10b | `acs_reperfusion.py:288`, misma función | Fibrilación ventricular desencadenada por una arteria que ha permanecido ocluida durante dos horas. Se pierde el pulso y se suspende la reevaluación organizada: este es el desenlace que esta vía clínica busca prevenir. | Igual que ES-P10a |
| ES-P11 | `event_provenance.py:151` | **Queda canónico «endoscopy performed».** Ninguna pantalla localizada lo muestra (es dato del registro y del tamizaje docente), así que no se creó una ruta nueva para «endoscopía realizada» | `event_provenance.py`, `rubric_screening` y el almacenamiento del Trace |
| ES-P12 | `unexecuted_items.py:167`, `held_messages` | También se reconoció lo siguiente, pero no puede ejecutarse en esta versión: {lista}. | {lista} es lo que escribió el residente: no se traduce, normaliza, sustituye ni pasa a minúsculas (se resguarda antes de las reglas) |
| ES-P13 v1 | `family_engine.py:2001–2007` | El equipo de Gastroenterología está a pie de cama, pero difiere la endoscopía hasta lograr una reanimación adecuada (presión sistólica de {pas} mmHg); reevaluará cada 15 minutos. | Disparador, momento, valores, estado de la transfusión, 15 minutos, interconsulta y fisiología |
| ES-P13 v2 | Igual | … (presión sistólica de {pas} mmHg, hemoglobina {n} g/dL sin transfusión en curso); reevaluará cada 15 minutos. | Igual |

## 3. Observaciones, sin cambio

- Concordancia de género en el recibo: «Aspirina 300 mg PO administrado» (el participio sigue a la orden, no al
  fármaco). La regla V-9 no tocó la concordancia.
- Etiquetas compuestas por palabras: «Adrenalina suspensión», «Nitroglicerina inicio a 100 mcg/min» (anteriores a
  esta ronda; en español, sin inglés).
- TD-85: el inglés del paro de la bradicardia y de la reacción bifásica dice más que el español aprobado
  («Paro circulatorio por bradicardia profunda.», «La reacción anafiláctica vuelve.»), por decisión docente.
- TD-84: en `bradycardia_ccb_68m` el examen inglés omite «no focal deficit»; no fue parte de la decisión.
- `pelvic_binder` no es ejecutable en `trauma_limb_hemorrhage_27m`: la pregunta lo dice en los dos idiomas
  («faja pélvica», C27e).
- Los rótulos de rol «Faculty» y «Admin» siguen en inglés en el portal de cuentas: son del personal, fuera de la
  sala del residente.

## 4. Lo que se corrigió con palabras ya aprobadas (no son pendientes)

El centinela del 2026-10-08 halló también inglés que tenía ya su español aprobado en otra parte; se aplicó sin
redacción nueva (`test_b5_x1_spanish.py`, última sección):

- «Examine: Abdomen» → «Examen: Abdomen» (L-11; el nombre de la región se escribe igual).
- La frase del TEP «The systolic pressure has stayed below 90 mmHg…» ya tenía su español entero; una regla de la
  Fase 0 traducía antes la etiqueta del evento dentro de ella y la frase quedaba mezclada. Ahora la frase entera se
  reconoce con la etiqueta en cualquiera de los dos idiomas.
- «esfuerzo respiratorio increased» → «aumentado» (`OBSERVED_VALUES_ES`: «Aumentado»).
- «nebulized» → «nebulizado» (la vía del registro, `report_presentation._ROUTES_ES`), en el panel de tratamientos y
  en la línea después de la orden.
- «Glucose 25 g IV» → «Glucosa 25 g IV» (V-9: *dextrose* → glucosa; es el bolo de glucosa).
- «NIV inicio» → «VMNI inicio» (X1-0, punto 3).
- El resumen del estado en español nombraba «Norepinephrine», «Dobutamine» y «Nitroglycerin»: ahora V-9.
- Revisión adversarial del 2026-10-08 (C-2026-10-08-07): la pregunta de la vía vuelve a su redacción, con la clase por
  su etiqueta («Please specify a supported route for antibiotic.» · «Indica una vía soportada para antibiótico.»), y se
  dice entera en español aunque el fármaco tenga dos palabras; lo que escribió el residente («avoid aspirin»,
  «albuterol 5 mg nebulized», la lista de X1-C29) ya no se traduce a medias; el centinela vuelve a marcar las palabras
  que sólo eran nombres de ranuras de plantilla («given», «drug»…) y ES-P2 reconoce sólo los temas de la historia.
- Mini-pase adversarial del 2026-10-08, tras ES-P8 a ES-P13 (C-2026-10-08-09): lo que escribió el residente se aparta
  antes de decir en español cualquier frase de la sala (si escribe «Finish now» dentro de una orden, queda «Finish
  now», no «Finalizar ahora»), sin tope de largo; y «unidades» (ES-P6) también en la dosis por kilo y por boca: «80
  units/kg × 50 kg» → «80 unidades/kg × 50 kg», «heparin 5000 units PO» → «heparina 5000 unidades PO». No es redacción
  nueva: es la palabra que la docencia ya aprobó en ES-P6.
- En el detector, no en la sala: «interconsulta» y «dada» son español y ya no cuentan como inglés; IPAP y EPAP se
  clasificaron como códigos, como CPAP y BiPAP (X1-0, punto 2). **Esta última es una clasificación técnica de esta
  ronda, no una decisión docente:** si la docencia prefiere otra cosa, se cambia.
