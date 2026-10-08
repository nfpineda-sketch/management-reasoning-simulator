# B-5 · IG-5 · Lo que sigue en inglés en la sala en español: pendiente de redacción docente

> **Ronda de implementación local del 2026-10-08** («FINAL FACULTY DECISIONS + LOCAL IMPLEMENTATION
> AUTHORIZATION»). Las 105 decisiones de X-1 están implementadas en inglés y en español
> (`test_b5_x1_spanish.py`). El centinela del español (`tools_spanish_sentinel.py`, 30 casos) y una cosecha a nivel
> del motor hallaron, además, textos **fuera del inventario de X-1** que la sala muestra en inglés. Ninguno tiene
> redacción docente en español. Según la autorización («si implementar una decisión aprobada exige una decisión
> nueva de redacción que la docencia no tomó: detener ese ítem e informarlo»), **no se tradujeron**: quedan aquí,
> con una propuesta, a decisión docente. Es TD-86 del registro de deuda.
>
> **No son excepciones.** El centinela los reconoce uno por uno (`PENDING_FACULTY_WORDING`) y los informa como
> pendientes, aparte del inglés no intencional; su prueba (`test_spanish_sentinel.py`) falla ante cualquier otra
> línea en inglés y marca como «xfail» el caso que todavía muestra uno de estos, nombrándolo. El centinela **no está
> limpio** mientras estos ítems sigan abiertos.

## 1. Lo que el centinela ve en la sala (30 casos): paquete para la decisión docente

Recorrido del 2026-10-08 sobre `ef1051c` (30 casos, 156 apariciones, todas de estos siete ítems; 0 de inglés no
intencional). La recomendación es una propuesta: **la decisión es docente** y ninguno se tradujo.

| Ítem | Inglés exacto | Español propuesto | Dónde aparece | Casos · apariciones | Por qué no estaba en X-1 | Efecto | Recomendación | Fuente |
|---|---|---|---|---|---|---|---|---|
| ES-P1 | Presentation only. Orders are read in Spanish and English either way. | «Sólo cambia la presentación. Las órdenes se leen igual en español y en inglés.» | Ayuda (?) del selector de idioma, panel de inicio | 30 · 30 | El selector es bilingüe a propósito (`BILINGUAL`); su ayuda no entró al inventario | Sólo presentación | APPROVE | `app.py:10192`, `_language_selector` |
| ES-P2 | Ask about {tema} (p. ej., «Ask about presenting symptoms») | «Preguntar por: {tema}», con el tema en español (I-5): «Preguntar por: motivo de consulta» | Entrada «TÚ» de la conversación y su leyenda, al elegir un tema de la historia | 30 · 30 | X-1 cubrió «Examen: {región}» (L-11), no la entrada del tema | Sólo presentación (el evento guardado no cambia) | APPROVE | `app.py:11007` y `:11012`, `_render_staff_tools` |
| ES-P3 | Latest response | «Última respuesta» | Desplegable después de «Finalizar ahora» | 30 · 30 | Pantalla posterior al cierre fuera de P-02 a P-07 | Sólo presentación | APPROVE | `app.py:10779`, `_render_closed_bedside` |
| ES-P4 | Clinical chart · examination · results · treatment record | «Ficha clínica · examen · resultados · registro de tratamientos» | Desplegable después de «Finalizar ahora» | 30 · 30 | Igual que ES-P3 | Sólo presentación | APPROVE | `app.py:10934`, `_render_staff_tools` |
| ES-P5 | Gastroenterology is at the bedside but defers endoscopy until the patient is resuscitated (hemoglobin {n} g/dL without blood running); they will re-check every 15 minutes. | Propuesta inicial: «Gastroenterología está al lado de la cama, pero difiere la endoscopía hasta que el paciente esté reanimado (hemoglobina {n} g/dL sin sangre en curso); volverá a evaluar cada 15 minutos.» Variante recomendada, neutra en género (el caso es una paciente) y sin «sangre en curso»: «Gastroenterología está junto a la cama, pero difiere la endoscopía hasta completar la reanimación (hemoglobina {n} g/dL sin transfusión en curso); volverá a evaluar cada 15 minutos.» | Sala, tras la interconsulta, cuando la endoscopía se difiere | 1 (`gi_bleed_72f`) · 3 | Frase del motor de la hemorragia digestiva que las sondas del inventario no alcanzaron | Contenido clínico (traducción de una frase del curso clínico); no cambia el motor ni la conducta | REVISE (variante neutra) | `family_engine.py:2003`, `_endoscopy_minute` |
| ES-P6 | heparina 4000 **units** IV | «unidades»: «heparina 4000 unidades IV» | Panel de tratamientos, línea después de la orden, «Acción:» y resumen al cierre | 8 (6 SCA y 2 TEP) · 32 | X1-0 deja la dosis «como se escribió» y fija las unidades que no cambian (mL, mg, mcg…); «units» no está entre ellas | Notación de la unidad de dosis; la dosis no cambia. Sensible: se recomienda la palabra entera y no «UI», que puede leerse como «IV» | APPROVE con «unidades» | `report_presentation.action_phrase` (`_amount`, :346) y `family_reports.format_administration` (:105) |
| ES-P7 | Hemorrhage control + **Blood** + … | «Control de la hemorragia» y «Glóbulos rojos» (V-9 ya dice «glóbulos rojos» para *packed red cells*; el tipo `blood` es sólo glóbulos rojos, 1 a 4 unidades, `family_engine.py:692`) | Resumen de la decisión al cierre, cuando la acción no trae su etiqueta del registro | 1 (`trauma_limb_hemorrhage_27m`) · 1 | X-1 cubrió las etiquetas del registro (I-10), no el nombre de respaldo del tipo | Sólo presentación | APPROVE | `report_presentation.action_phrase` (nombre del tipo como respaldo, ≈:360) |

## 2. Lo que la sala puede mostrar y el recorrido del centinela no alcanzó

Hallado por la cosecha a nivel del motor (todas las órdenes de una batería de aclaraciones, en los 30 casos). Sólo
aparece si el residente escribe esa orden.

| Ítem | Texto | Fuente | Propuesta (a decidir) |
|---|---|---|---|
| ES-P8 | No active {kind} infusion is recorded. Specify a starting rate and units. · No matching administered treatment is recorded. Specify the treatment, dose and route. · No infusion is running. Name the drug and its starting rate. · No active conventional oxygen is recorded. Specify the starting device and flow. · No continuous nebulization is running. Specify the rate in mg/h to start it. · No active NIV is recorded. Specify the starting mode, pressures and FiO2. · No active ventilator or NIV settings are recorded. Specify the support to start. | `active_order_context.py:37–155`, **lector congelado** (su inglés no cambia). Hoy salen mezcladas: «No active infusión de noradrenalina is recorded. Indica starting rate and units.» | Frases enteras en `language.py` (que no es el lector), con el estilo de X1-C: «No hay registro de una infusión activa de {fármaco}. Indica la velocidad inicial y sus unidades.», etc. |
| ES-P9 | (no dose written; 1 g is the standard fixed loading dose the simulator applies) | `family_engine.py:732`, base de la dosis del ácido tranexámico sin dosis escrita | «(sin dosis escrita; 1 g es la dosis de carga fija estándar que aplica el simulador)», como la del bolo sin velocidad («sin velocidad escrita; velocidad estándar del simulador…», ya activa) |
| ES-P10 | Ventricular fibrillation, precipitated by an exercise stress test on an unstable occlusion. The pulse is lost and organized reassessment is paused: this is the outcome the pathway exists to prevent. | `acs_reperfusion.py:316`; hoy sale mezclada («Fibrilación ventricular, precipitated by…») | «Fibrilación ventricular, precipitada por una prueba de esfuerzo con una oclusión inestable. Se pierde el pulso y la reevaluación organizada se detiene: es el desenlace que la vía busca evitar.» |
| ES-P11 | endoscopy performed | `event_provenance.py:151`, etiqueta del evento en la hemorragia digestiva | «endoscopía realizada» |
| ES-P12 | Also recognized but not executable in this build: {lista}. | `unexecuted_items.held_messages` (última línea de una orden retenida); hallado por la revisión adversarial del 2026-10-08. La lista es lo que escribió el residente: desde C-2026-10-08-07 ninguna regla la traduce a medias | «También en esta orden, reconocido pero no ejecutable en esta versión: «{lista}».», como las demás líneas de la orden retenida (X1-C29 dice «Esta versión reconoce, pero no ejecuta: {lista}.») |

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
