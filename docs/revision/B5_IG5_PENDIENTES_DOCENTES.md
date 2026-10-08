# B-5 · IG-5 · Textos de la sala en español fuera del inventario de X-1 (TD-86)

> **Ronda de implementación local del 2026-10-08.** Las 105 decisiones de X-1 están implementadas en inglés y en
> español (`test_b5_x1_spanish.py`). El centinela del español (`tools_spanish_sentinel.py`, 30 casos) y una cosecha a
> nivel del motor hallaron, además, textos **fuera del inventario de X-1** que la sala muestra en inglés.
> **ES-P1 a ES-P7:** decididos por la docencia el 2026-10-08 e implementados en local (§1). **ES-P8 a ES-P13:** sin
> redacción docente; no se tradujeron (§2). No son excepciones: el centinela no se da por completo mientras alguno
> siga abierto.

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

## 2. ES-P8 a ES-P13: sin redacción docente, sin implementar

Ninguno se tradujo. El centinela los declara aparte (`PENDING_OUTSIDE_THE_WALK`): su recorrido no los alcanza, y no
se da por completo mientras alguno siga abierto. Lo que hoy se ve en español es el resultado de `language.say`
sobre el texto inglés.

### ES-P8 · Aclaraciones del lector congelado sobre lo que no está activo

- **Fuente:** `active_order_context.py`, función `complete_active_order` (lector congelado: su inglés no cambia). El español iría
  en `language.py`, como frase entera.
- **Dónde lo ve el residente:** la entrada «ACLARACIÓN», al escribir una orden que ajusta, mantiene, detiene o
  repite algo que no está activo, o que es ambigua.
- **Clínico o de presentación:** presentación. Es una pregunta de aclaración: no cambia el motor ni la conducta.
- **Por qué X-1 no lo cubrió:** el inventario de X-1 se leyó de `app.py` y `family_engine.py`. El lector congelado
  quedó fuera.

Cada plantilla va por separado. {fármaco} es norepinephrine, nitroglycerin o dobutamine, en español por V-9.

| # | Inglés exacto | Hoy, en la sala en español | Disparador | Español propuesto | Recomendación |
|---|---|---|---|---|---|
| 8a | No matching administered treatment is recorded. Specify the treatment, dose and route. | No matching administrado treatment is recorded. Indica treatment, dose and route. | Repetir un tratamiento que no se dio | No hay registro de un tratamiento administrado que coincida. Indica el tratamiento, la dosis y la vía. | APPROVE |
| 8b | Which previous treatment should be repeated? Specify the drug or fluid. | Which previous treatment should be repeated? Indica drug or fluid. | «Repetir» sin decir qué | ¿Qué tratamiento anterior quieres repetir? Indica el fármaco o el fluido. | APPROVE |
| 8c | Specify compatible units for the treatment being repeated. | (todo en inglés) | Repetir con otras unidades | Indica unidades compatibles con el tratamiento que se repite. | APPROVE |
| 8d | The patient is not receiving invasive ventilation. | (todo en inglés) | Ajustar el ventilador sin intubación | El paciente no está con ventilación invasiva. | APPROVE |
| 8e | Specify an airway transition; stopping a ventilator is not an extubation order. | Indica airway transition; stopping a ventilator is not an extubation order. | «Detener el ventilador» | Indica un cambio de la vía aérea; detener el ventilador no es una orden de extubación. | APPROVE |
| 8f | No infusion is running. Name the drug and its starting rate. | Infusión de No is running. Name the drug and its starting rate. | Ajustar «la infusión» sin ninguna en curso | No hay ninguna infusión en curso. Indica el fármaco y su velocidad inicial. | APPROVE |
| 8g | More than one infusion is running ({lista}). Name the one to change. | More than infusión de one is running (dobutamina, noradrenalina). Name the one to change. | Ajustar «la infusión» con dos o más en curso | Hay más de una infusión en curso ({lista}). Indica cuál quieres cambiar. | APPROVE |
| 8h | Nitroglycerin is ordered in mcg/min in this encounter. | Nitroglicerina is ordered in mcg/min in this encounter. | Nitroglicerina en mcg/kg/min | En este encuentro, la nitroglicerina se indica en mcg/min. | APPROVE |
| 8i | Specify the new {fármaco} rate. | Indica new noradrenalina rate. | Ajustar sin la nueva velocidad | Indica la nueva velocidad de {fármaco}. | APPROVE |
| 8j | No active {fármaco} infusion is recorded. Specify a starting rate and units. | No active infusión de noradrenalina is recorded. Indica starting rate and units. | Ajustar una infusión que no corre | No hay registro de una infusión activa de {fármaco}. Indica la velocidad inicial y sus unidades. | APPROVE |
| 8k | Specify the rate in the new infusion units. | Indica rate in the infusión de new units. | Cambiar las unidades sin la velocidad | Indica la velocidad en las nuevas unidades de la infusión. | APPROVE |
| 8l | No active conventional oxygen is recorded. Specify the starting device and flow. | No active conventional oxygen is recorded. Indica starting device and flow. | Ajustar oxígeno que no está | No hay registro de oxígeno convencional activo. Indica el dispositivo inicial y el flujo. | APPROVE |
| 8m | Specify the flow for the new oxygen device. | Indica flow for the new oxygen device. | Cambiar de dispositivo sin el flujo | Indica el flujo para el nuevo dispositivo de oxígeno. | APPROVE |
| 8n | No continuous nebulization is running. Specify the rate in mg/h to start it. | No nebulización continua is running. Indica rate in mg/h to inicio it. | Ajustar una nebulización continua que no corre | No hay nebulización continua en curso. Indica la velocidad en mg/h para iniciarla. | APPROVE |
| 8o | No active NIV is recorded. Specify the starting mode, pressures and FiO2. | No active NIV is recorded. Indica starting mode, pressures and FiO2. | Ajustar una VMNI que no está | No hay registro de VMNI activa. Indica el modo inicial, las presiones y la FiO₂. | APPROVE |

«No active ventilator or NIV settings are recorded. Specify the support to start.» ya tiene su español
(«No hay parámetros de ventilador ni de VMNI registrados. Indica qué soporte iniciar.») y no está pendiente.

### ES-P9 a ES-P13

| ID | Inglés exacto | Fuente | Dónde lo ve el residente | Caso o disparador | Clínico o presentación | Por qué X-1 no lo cubrió | Español propuesto | Recomendación |
|---|---|---|---|---|---|---|---|---|
| ES-P9 | `{Etiqueta} (no dose written; 1 g is the standard fixed loading dose the simulator applies)`; p. ej. «Tranexamic acid 1 g IV administered (no dose written; 1 g is the standard fixed loading dose the simulator applies)», también dentro de «After …, BP …» | `family_engine.py:736`, `_validate` (`dose_basis`), unida a la etiqueta en `family_engine.py:1856–1859` | Línea después de la orden y actualización clínica «Tras …» | Ácido tranexámico sin dosis escrita, en cualquier caso que lo acepte (la cosecha lo halló en `acs_48m_wellens`) | Clínico: dice qué dosis aplicó el simulador; la dosis (1 g IV) no cambia | `dose_basis` se agrega al ejecutar; el inventario leyó los literales de las preguntas, no las bases de dosis | (sin dosis escrita; 1 g es la dosis de carga fija estándar que aplica el simulador) | APPROVE |
| ES-P10a | Ventricular fibrillation, precipitated by an exercise stress test on an unstable occlusion. The pulse is lost and organized reassessment is paused: this is the outcome the pathway exists to prevent. | `acs_reperfusion.ventricular_fibrillation`, llamada desde `family_engine.py:1721` | Línea del evento en la sala; hoy «Fibrilación ventricular, precipitated by …» | Prueba de esfuerzo con una oclusión inestable (SCA) | Clínico: un evento crítico; no cambia el motor | Frase compuesta por el motor; X-1 no la alcanzó | Fibrilación ventricular desencadenada por una prueba de esfuerzo con una oclusión inestable. Se pierde el pulso y se suspende la reevaluación organizada: es el desenlace que la vía busca evitar. | REVISE si la docencia prefiere otro verbo («precipitada», «desencadenada») |
| ES-P10b | Ventricular fibrillation, precipitated by an artery that has stayed closed for two hours. The pulse is lost and organized reassessment is paused: this is the outcome the pathway exists to prevent. | `acs_reperfusion.py:288`, misma función | Igual que ES-P10a | Arteria ocluida dos horas sin reperfusión (SCA con oclusión) | Clínico, igual que ES-P10a | Igual que ES-P10a | Fibrilación ventricular desencadenada por una arteria que ha permanecido ocluida durante dos horas. Se pierde el pulso y se suspende la reevaluación organizada: es el desenlace que la vía busca evitar. | Igual que ES-P10a |
| ES-P11 | endoscopy performed (etiqueta del evento `endoscopy_at`; contexto: `{"kind": "endoscopy", "label": "endoscopy performed", "cause_class": "LOGISTIC", "interrupt": False}`) | `event_provenance.py:151`, `FLAG_EVENTS` | **No se halló en la sala.** No interrumpe la espera, así que no es una línea del encuentro. Queda en el registro del Trace (`event["events"]`, canónico en inglés por diseño, TD-80) y lo lee el tamizaje docente (`rubric_screening._course`). En la sala, la endoscopía se dice con su frase ya traducida («Gastroenterology performed upper endoscopy…») | Endoscopía realizada en la hemorragia digestiva | Registro y tamizaje, no la sala | Etiqueta interna del registro de eventos | «endoscopía realizada», sólo si la docencia quiere verla en sus vistas | NO CAMBIAR el registro canónico. Decidir sólo si las vistas docentes la muestran |
| ES-P12 | Also recognized but not executable in this build: {lista}. (`{lista}` = lo que escribió el residente, unido con «, ») | `unexecuted_items.py:167`, `held_messages`; se muestra desde `app.py:8325` y `app.py:11103` | Panel de la orden retenida (compuerta del razonamiento), última línea de lo que la orden también trae | Una orden retenida que trae ítems reconocidos sin categoría ejecutable | Presentación; la lista no se traduce (C-2026-10-08-07) | Las demás líneas de la orden retenida sí estaban en X-1; ésta, la de ítems sin categoría, no | También en esta orden, reconocido pero no ejecutable en esta versión: «{lista}». (como las demás líneas, con la lista entre «» y tal como se escribió) | APPROVE |
| ES-P13 | Gastroenterology is at the bedside but defers endoscopy until the patient is resuscitated (SBP {pas} mmHg); they will re-check every 15 minutes. · … (SBP {pas} mmHg, hemoglobin {n} g/dL without blood running); they will re-check every 15 minutes. | `family_engine.py:2001–2007`, `_endoscopy_minute` | Sala, tras la interconsulta, igual que ES-P5 | Hemorragia digestiva con la presión sistólica bajo el umbral de la endoscopía | Contenido clínico; no cambia el motor | Hallado al implementar ES-P5: la decisión cubrió sólo la variante de la hemoglobina | El equipo de Gastroenterología está a pie de cama, pero difiere la endoscopía hasta lograr una reanimación adecuada (presión sistólica de {pas} mmHg); reevaluará cada 15 minutos. · … (presión sistólica de {pas} mmHg, hemoglobina {n} g/dL sin transfusión en curso); reevaluará cada 15 minutos. («presión sistólica de {n} mmHg» ya es español aprobado en la sala) | APPROVE |

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
- En el detector, no en la sala: «interconsulta» y «dada» son español y ya no cuentan como inglés; IPAP y EPAP se
  clasificaron como códigos, como CPAP y BiPAP (X1-0, punto 2). **Esta última es una clasificación técnica de esta
  ronda, no una decisión docente:** si la docencia prefiere otra cosa, se cambia.
