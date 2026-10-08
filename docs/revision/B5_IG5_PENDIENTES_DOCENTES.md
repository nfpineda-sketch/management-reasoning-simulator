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

## 1. Lo que el centinela ve en la sala (30 casos)

| Ítem | Texto en inglés | Dónde | Fuente | Casos | Propuesta en español (a decidir) |
|---|---|---|---|---|---|
| ES-P1 | Presentation only. Orders are read in Spanish and English either way. | Ayuda del selector de idioma, en el panel de inicio | `app.py:10192` | 30 | «Sólo cambia la presentación. Las órdenes se leen igual en español y en inglés.» El selector mismo es bilingüe a propósito (`BILINGUAL`); su ayuda no lo es |
| ES-P2 | Ask about {tema} | Entrada «TÚ» del tema de la historia y su leyenda | `app.py:11009` | 30 | «Preguntar por: {tema}», con el tema en español (I-5), como «Examen: {región}» (L-11) |
| ES-P3 | Latest response | Desplegable después de «Finalizar ahora» | `app.py:10779` | 30 | «Última respuesta» |
| ES-P4 | Clinical chart · examination · results · treatment record | Desplegable después del cierre | `app.py:10934` | 30 | «Ficha clínica · examen · resultados · registro de tratamientos» |
| ES-P5 | Gastroenterology is at the bedside but defers endoscopy until the patient is resuscitated (hemoglobin {n} g/dL without blood running); they will re-check every 15 minutes. | Sala, tras la interconsulta en la hemorragia digestiva | `family_engine.py:2003` | `gi_bleed_72f` | «Gastroenterología está al lado de la cama, pero difiere la endoscopía hasta que el paciente esté reanimado (hemoglobina {n} g/dL sin sangre en curso); volverá a evaluar cada 15 minutos.» |
| ES-P6 | heparina 4000 **units** IV | Panel de tratamientos, línea después de la orden, «Acción:» y resumen al cierre | dosis de heparina (`dose` con `units`) | 6 SCA y 2 TEP | «unidades» o «UI». X1-0 deja la dosis «como se escribió» y fija las unidades que no cambian (mL, mg, mcg…); «units» no está entre ellas |
| ES-P7 | Hemorrhage control + **Blood** + … | Resumen de la decisión al cierre, cuando la acción no trae su etiqueta del registro | `report_presentation.action_phrase` (nombre del tipo como respaldo) | `trauma_limb_hemorrhage_27m` | «Control de la hemorragia» y «Glóbulos rojos» (V-9 ya dice «glóbulos rojos» para *packed red cells*). Con la etiqueta del registro la sala ya dice «Torniquete aplicado…» y «Glóbulos rojos 2 unidades iniciadas» |

## 2. Lo que la sala puede mostrar y el recorrido del centinela no alcanzó

Hallado por la cosecha a nivel del motor (todas las órdenes de una batería de aclaraciones, en los 30 casos). Sólo
aparece si el residente escribe esa orden.

| Ítem | Texto | Fuente | Propuesta (a decidir) |
|---|---|---|---|
| ES-P8 | No active {kind} infusion is recorded. Specify a starting rate and units. · No matching administered treatment is recorded. Specify the treatment, dose and route. · No infusion is running. Name the drug and its starting rate. · No active conventional oxygen is recorded. Specify the starting device and flow. · No continuous nebulization is running. Specify the rate in mg/h to start it. · No active NIV is recorded. Specify the starting mode, pressures and FiO2. · No active ventilator or NIV settings are recorded. Specify the support to start. | `active_order_context.py:37–155`, **lector congelado** (su inglés no cambia). Hoy salen mezcladas: «No active infusión de noradrenalina is recorded. Indica starting rate and units.» | Frases enteras en `language.py` (que no es el lector), con el estilo de X1-C: «No hay registro de una infusión activa de {fármaco}. Indica la velocidad inicial y sus unidades.», etc. |
| ES-P9 | (no dose written; 1 g is the standard fixed loading dose the simulator applies) | `family_engine.py:732`, base de la dosis del ácido tranexámico sin dosis escrita | «(sin dosis escrita; 1 g es la dosis de carga fija estándar que aplica el simulador)», como la del bolo sin velocidad («sin velocidad escrita; velocidad estándar del simulador…», ya activa) |
| ES-P10 | Ventricular fibrillation, precipitated by an exercise stress test on an unstable occlusion. The pulse is lost and organized reassessment is paused: this is the outcome the pathway exists to prevent. | `acs_reperfusion.py:316`; hoy sale mezclada («Fibrilación ventricular, precipitated by…») | «Fibrilación ventricular, precipitada por una prueba de esfuerzo con una oclusión inestable. Se pierde el pulso y la reevaluación organizada se detiene: es el desenlace que la vía busca evitar.» |
| ES-P11 | endoscopy performed | `event_provenance.py:151`, etiqueta del evento en la hemorragia digestiva | «endoscopía realizada» |

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
- En el detector, no en la sala: «interconsulta» y «dada» son español y ya no cuentan como inglés; IPAP y EPAP se
  clasificaron como códigos, como CPAP y BiPAP (X1-0, punto 2). **Esta última es una clasificación técnica de esta
  ronda, no una decisión docente:** si la docencia prefiere otra cosa, se cambia.
